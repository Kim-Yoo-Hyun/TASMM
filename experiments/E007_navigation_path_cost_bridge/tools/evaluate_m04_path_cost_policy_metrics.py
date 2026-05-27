#!/usr/bin/env python3
"""Evaluate E007 path-cost policy metrics with source-limited accounting."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
M03_DIR = EXP_ROOT / "artifacts" / "E007-M03_external_candidate_grid_projection_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M04_path_cost_policy_metrics_v0"
VERSION = "e007_m04_path_cost_policy_metrics_v0"

METHOD_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"
BASELINE_POLICIES = [
    "real_static_memory_only_v0",
    "real_detector_confidence_top5_v0",
    "conceptgraphs_only_strict_top5_v0",
    "real_context_agnostic_memory_trust_reobserve_v0",
    "h001_real_task_context_memory_trust_v0",
]
POLICIES = BASELINE_POLICIES + [METHOD_POLICY]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def round6(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    if not valid:
        return None
    return round(mean(valid), 6)


def group_by_query_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["query_uid"], row["policy"])].append(row)
    return grouped


def attempt_spl(success: bool, actual_cost_m: float | None, optimal_cost_m: float | None) -> float | None:
    if actual_cost_m is None or optimal_cost_m is None:
        return None
    if not success:
        return 0.0
    if optimal_cost_m <= 1e-9 and actual_cost_m <= 1e-9:
        return 1.0
    return round(optimal_cost_m / max(actual_cost_m, optimal_cost_m, 1e-9), 6)


def first_target_index(route_rows: list[dict[str, Any]]) -> int | None:
    for row in sorted(route_rows, key=lambda item: int(item["route_index"])):
        if row.get("candidate_is_target_eval_only"):
            return int(row["route_index"])
    return None


def expected_stop_index(query_row: dict[str, Any], route_count: int) -> tuple[int | None, str]:
    if not query_row.get("query_bridge_success_eval_only"):
        return route_count if route_count else None, "failure_visit_all_routes"
    direct = query_row.get("direct_target_route_index")
    if direct is not None:
        return int(direct), "direct_target_route"
    expected = query_row.get("expected_search_cost_eval_only")
    if isinstance(expected, (int, float)) and int(expected) > 0 and int(expected) <= route_count:
        return int(expected), "eval_expected_search_cost_rank"
    return None, "success_stop_route_missing"


def source_limited_reason(
    *,
    query_row: dict[str, Any],
    visited_rows: list[dict[str, Any]],
    stop_index: int | None,
) -> str | None:
    if query_row.get("route_rows") == 0:
        return "no_candidate_route"
    if stop_index is None:
        return "success_stop_route_missing"
    bad_status = [row.get("path_source_status") for row in visited_rows if not row.get("candidate_grid_path_ready")]
    if bad_status:
        return "visited_route_" + str(Counter(bad_status).most_common(1)[0][0])
    if not query_row.get("target_grid_path_ready"):
        return "target_path_source_limited"
    return None


def route_cost_at_stop(visited_rows: list[dict[str, Any]]) -> float | None:
    if not visited_rows:
        return None
    value = visited_rows[-1].get("candidate_path_cumulative_cost_m")
    return float(value) if value is not None else None


def old_location_dead_end_rows(visited_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in visited_rows
        if row.get("candidate_source") == "old_memory" and not row.get("candidate_is_target_eval_only")
    ]


def build_metric_rows(
    query_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    routes_by_query_policy = group_by_query_policy(route_rows)
    metric_rows: list[dict[str, Any]] = []

    for query in sorted(query_rows, key=lambda row: (row["query_uid"], row["policy"])):
        routes = sorted(
            routes_by_query_policy.get((query["query_uid"], query["policy"]), []),
            key=lambda row: int(row["route_index"]),
        )
        direct_target = first_target_index(routes)
        query = {**query, "direct_target_route_index": direct_target}
        stop_index, stop_source = expected_stop_index(query, len(routes))
        visited = [row for row in routes if stop_index is not None and int(row["route_index"]) <= stop_index]
        limited_reason = source_limited_reason(query_row=query, visited_rows=visited, stop_index=stop_index)
        source_ready = limited_reason is None
        success = bool(query.get("query_bridge_success_eval_only"))
        actual_cost = route_cost_at_stop(visited) if source_ready else None
        target_cost = float(query["target_path_cost_m"]) if query.get("target_path_cost_m") is not None else None
        spl = attempt_spl(success, actual_cost, target_cost) if source_ready else None
        old_dead_rows = old_location_dead_end_rows(visited)
        old_dead_cost = sum(float(row.get("candidate_path_step_cost_m") or 0.0) for row in old_dead_rows)

        metric_rows.append(
            {
                "m04_version": VERSION,
                "query_uid": query["query_uid"],
                "row_uid": query["row_uid"],
                "base_row_uid": query.get("base_row_uid"),
                "policy": query["policy"],
                "row_band": query.get("row_band"),
                "task_context_id": query.get("task_context_id"),
                "route_rows": len(routes),
                "visited_route_rows": len(visited),
                "stop_route_index": stop_index,
                "stop_route_source": stop_source,
                "direct_target_route_index": direct_target,
                "expected_search_cost_eval_only": query.get("expected_search_cost_eval_only"),
                "query_bridge_success_eval_only": success,
                "success_source_eval_only": query.get("success_source_eval_only"),
                "path_source_ready": source_ready,
                "path_source_limited_reason": limited_reason,
                "target_grid_path_ready": bool(query.get("target_grid_path_ready")),
                "target_path_cost_m": round6(target_cost),
                "path_expected_search_cost_m": round6(actual_cost),
                "path_attempt_spl_proxy": spl,
                "old_location_dead_end_visit_count": len(old_dead_rows),
                "old_location_dead_end_cost_m_lower_bound": round6(old_dead_cost) if source_ready else None,
                "old_location_dead_end_cost_boundary": "lower_bound_path_starts_at_old_memory",
                "full_denominator_row": True,
                "source_ready_subset_row": source_ready,
                "real_navigation_sr_spl_ready": False,
            }
        )
    return metric_rows


def summarize_policy(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    ready_rows = [row for row in rows if row["path_source_ready"]]
    source_rows = ready_rows if subset == "source_ready" else rows
    source_ready_success = [row for row in ready_rows if row["query_bridge_success_eval_only"]]
    return {
        "subset": subset,
        "policy": rows[0]["policy"] if rows else None,
        "query_policy_rows": len(rows),
        "metric_rows": len(source_rows),
        "path_source_ready_rows": len(ready_rows),
        "path_source_limited_rows": len(rows) - len(ready_rows),
        "path_source_limited_rate": safe_rate(len(rows) - len(ready_rows), len(rows)),
        "query_bridge_success_rows_full_denominator": sum(1 for row in rows if row["query_bridge_success_eval_only"]),
        "query_bridge_success_rate_full_denominator": safe_rate(
            sum(1 for row in rows if row["query_bridge_success_eval_only"]),
            len(rows),
        ),
        "path_success_rows_source_ready": len(source_ready_success),
        "path_success_rate_source_ready": safe_rate(len(source_ready_success), len(ready_rows)),
        "path_success_lower_bound_rate_full_denominator": safe_rate(len(source_ready_success), len(rows)),
        "mean_path_expected_search_cost_m_source_ready": safe_mean(
            [row["path_expected_search_cost_m"] for row in ready_rows]
        ),
        "mean_path_attempt_spl_proxy_source_ready": safe_mean(
            [row["path_attempt_spl_proxy"] for row in ready_rows]
        ),
        "old_location_dead_end_visit_rows_source_ready": sum(
            1 for row in ready_rows if row["old_location_dead_end_visit_count"] > 0
        ),
        "old_location_dead_end_visit_rate_source_ready": safe_rate(
            sum(1 for row in ready_rows if row["old_location_dead_end_visit_count"] > 0),
            len(ready_rows),
        ),
        "mean_old_location_dead_end_cost_m_lower_bound_source_ready": safe_mean(
            [row["old_location_dead_end_cost_m_lower_bound"] for row in ready_rows]
        ),
        "source_limited_reason_counts": dict(Counter(row["path_source_limited_reason"] for row in rows if not row["path_source_ready"])),
    }


def build_policy_summary_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        rows_by_policy[row["policy"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        rows = rows_by_policy.get(policy, [])
        if not rows:
            continue
        summary_rows.append(summarize_policy(rows, "full_denominator"))
        summary_rows.append(summarize_policy(rows, "source_ready"))
    return summary_rows


def build_paired_delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy_query = {(row["policy"], row["query_uid"]): row for row in metric_rows}
    method_rows = [row for row in metric_rows if row["policy"] == METHOD_POLICY]
    deltas: list[dict[str, Any]] = []
    for baseline in BASELINE_POLICIES:
        paired: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for method in method_rows:
            base = by_policy_query.get((baseline, method["query_uid"]))
            if base and method["path_source_ready"] and base["path_source_ready"]:
                paired.append((method, base))
        method_success = sum(1 for method, _ in paired if method["query_bridge_success_eval_only"])
        base_success = sum(1 for _, base in paired if base["query_bridge_success_eval_only"])
        deltas.append(
            {
                "method_policy": METHOD_POLICY,
                "baseline_policy": baseline,
                "paired_source_ready_rows": len(paired),
                "method_success_rows": method_success,
                "baseline_success_rows": base_success,
                "method_success_rate": safe_rate(method_success, len(paired)),
                "baseline_success_rate": safe_rate(base_success, len(paired)),
                "success_rate_delta": None
                if not paired
                else round((method_success - base_success) / len(paired), 6),
                "method_mean_path_expected_search_cost_m": safe_mean(
                    [method["path_expected_search_cost_m"] for method, _ in paired]
                ),
                "baseline_mean_path_expected_search_cost_m": safe_mean(
                    [base["path_expected_search_cost_m"] for _, base in paired]
                ),
                "mean_path_cost_delta_m": None
                if not paired
                else round(
                    safe_mean([method["path_expected_search_cost_m"] for method, _ in paired])
                    - safe_mean([base["path_expected_search_cost_m"] for _, base in paired]),
                    6,
                ),
                "method_mean_path_attempt_spl_proxy": safe_mean(
                    [method["path_attempt_spl_proxy"] for method, _ in paired]
                ),
                "baseline_mean_path_attempt_spl_proxy": safe_mean(
                    [base["path_attempt_spl_proxy"] for _, base in paired]
                ),
                "mean_path_attempt_spl_delta": None
                if not paired
                else round(
                    safe_mean([method["path_attempt_spl_proxy"] for method, _ in paired])
                    - safe_mean([base["path_attempt_spl_proxy"] for _, base in paired]),
                    6,
                ),
            }
        )
    return deltas


def build_context_summary_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[(row["policy"], row.get("row_band") or "unknown", row.get("task_context_id") or "unknown")].append(row)
    return [
        {
            **summarize_policy(rows, "source_ready"),
            "row_band": row_band,
            "task_context_id": task_context_id,
        }
        for (policy, row_band, task_context_id), rows in sorted(grouped.items())
    ]


def build_claim_rows(coverage: dict[str, Any], paired_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    method_vs_static = next(row for row in paired_rows if row["baseline_policy"] == "real_static_memory_only_v0")
    method_vs_cg = next(row for row in paired_rows if row["baseline_policy"] == "conceptgraphs_only_strict_top5_v0")
    method_vs_h001 = next(row for row in paired_rows if row["baseline_policy"] == "h001_real_task_context_memory_trust_v0")
    return [
        {
            "claim_id": "C-E007-M04-001",
            "claim": "Path-cost policy metrics can be computed on a source-ready subset while preserving the full 195-row denominator.",
            "status": "supported_with_source_limits",
            "evidence": (
                f"{coverage['query_policy_rows']} full query-policy rows; "
                f"{coverage['path_source_ready_query_policy_rows']} source-ready rows; "
                f"{coverage['source_limited_query_policy_rows']} source-limited rows."
            ),
            "boundary": "Report full denominator and source-ready subset separately.",
        },
        {
            "claim_id": "C-E007-M04-002",
            "claim": "H001 + ConceptGraphs fallback remains stronger than static stale memory and ConceptGraphs-only on paired source-ready rows.",
            "status": "supported_as_proxy_path_metric"
            if (method_vs_static["success_rate_delta"] or 0) > 0 and (method_vs_cg["success_rate_delta"] or 0) > 0
            else "mixed",
            "evidence": (
                f"vs static success delta {method_vs_static['success_rate_delta']}; "
                f"vs ConceptGraphs success delta {method_vs_cg['success_rate_delta']}."
            ),
            "boundary": "This is an occupancy-grid proxy, not real navigation execution.",
        },
        {
            "claim_id": "C-E007-M04-003",
            "claim": "Map-assisted fallback improves over H001-only only if the path-cost and SPL tradeoff remains favorable.",
            "status": "needs_reviewer_caution"
            if (method_vs_h001["success_rate_delta"] or 0) <= 0
            else "supported_with_cost_tradeoff",
            "evidence": (
                f"vs H001-only success delta {method_vs_h001['success_rate_delta']}; "
                f"path cost delta {method_vs_h001['mean_path_cost_delta_m']}; "
                f"AttemptSPL delta {method_vs_h001['mean_path_attempt_spl_delta']}."
            ),
            "boundary": "If success gain is small or cost rises, frame as repair tradeoff, not unconditional policy dominance.",
        },
        {
            "claim_id": "C-E007-M04-004",
            "claim": "Rows without direct route-level target flags are handled through the upstream expected-search-cost stop rank.",
            "status": "source_boundary_recorded",
            "evidence": f"{coverage['eval_expected_search_cost_stop_rows']} / {coverage['query_policy_rows']} query-policy rows use `eval_expected_search_cost_rank`.",
            "boundary": "These rows support path-cost accounting from upstream rank evidence, not direct route-target localization evidence.",
        },
        {
            "claim_id": "C-E007-M04-005",
            "claim": "Real navigation SR/SPL remains unsupported.",
            "status": "blocked",
            "evidence": "No simulator, navmesh, controller, or trajectory execution is integrated.",
            "boundary": "Use `PathAttemptSPLProxy`, not real `SPL`.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    paired_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    full_rows = [row for row in policy_rows if row["subset"] == "full_denominator"]
    table = [
        "| Policy | Success Full | Source Ready | Success Lower Full | Mean Path Cost | Mean Path `AttemptSPL` | Source-Limited |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in full_rows:
        table.append(
            f"| `{row['policy']}` | {row['query_bridge_success_rate_full_denominator']} | "
            f"{row['path_source_ready_rows']} / {row['query_policy_rows']} | "
            f"{row['path_success_lower_bound_rate_full_denominator']} | "
            f"{row['mean_path_expected_search_cost_m_source_ready']} | "
            f"{row['mean_path_attempt_spl_proxy_source_ready']} | "
            f"{row['path_source_limited_rate']} |"
        )

    delta_table = [
        "| Baseline | Paired Ready | Success Delta | Path Cost Delta | `AttemptSPL` Delta |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in paired_rows:
        delta_table.append(
            f"| `{row['baseline_policy']}` | {row['paired_source_ready_rows']} | "
            f"{row['success_rate_delta']} | {row['mean_path_cost_delta_m']} | "
            f"{row['mean_path_attempt_spl_delta']} |"
        )

    claim_table = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_table.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    return f"""# E007-M04 Path-Cost Policy Metrics

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- Query-policy rows: {coverage["query_policy_rows"]}.
- Path source-ready query-policy rows: {coverage["path_source_ready_query_policy_rows"]}.
- Source-limited query-policy rows: {coverage["source_limited_query_policy_rows"]}.
- Stop-route source counts: `{coverage["stop_route_source_counts"]}`.
- Method policy: `{METHOD_POLICY}`.
- Real navigation `SR` / `SPL` ready: false.

## Policy Summary

{chr(10).join(table)}

## Paired Source-Ready Delta

{chr(10).join(delta_table)}

## Claim Boundary

{chr(10).join(claim_table)}

## Agent Inference

- E007-M04 upgrades E007 from route-field readiness to policy-level path-cost proxy metrics.
- The result should be reported as an occupancy-grid proxy search/navigation bridge, not real navigation.
- Source-limited rows are substantial enough that full-denominator and source-ready subset metrics must both appear in paper tables.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m03 = read_json(M03_DIR / "coverage.json")
    query_rows = read_jsonl(M03_DIR / "query_path_readiness_rows.jsonl")
    route_rows = read_jsonl(M03_DIR / "projected_route_rows.jsonl")
    if not query_rows:
        raise RuntimeError("Missing E007-M03 query path readiness rows.")
    if not route_rows:
        raise RuntimeError("Missing E007-M03 projected route rows.")

    metric_rows = build_metric_rows(query_rows, route_rows)
    policy_rows = build_policy_summary_rows(metric_rows)
    paired_rows = build_paired_delta_rows(metric_rows)
    context_rows = build_context_summary_rows(metric_rows)

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m04_path_cost_policy_metrics_ready_with_source_limits",
        "version": VERSION,
        "m03_status": m03.get("status"),
        "query_rows": len({row["row_uid"] for row in metric_rows}),
        "query_policy_rows": len(metric_rows),
        "path_source_ready_query_policy_rows": sum(1 for row in metric_rows if row["path_source_ready"]),
        "source_limited_query_policy_rows": sum(1 for row in metric_rows if not row["path_source_ready"]),
        "policies": POLICIES,
        "method_policy": METHOD_POLICY,
        "path_policy_metric_ready": True,
        "full_denominator_preserved": len(metric_rows) == 1170,
        "real_navigation_sr_spl_ready": False,
        "source_limited_reason_counts": dict(Counter(row["path_source_limited_reason"] for row in metric_rows if not row["path_source_ready"])),
        "stop_route_source_counts": dict(Counter(row["stop_route_source"] for row in metric_rows)),
        "eval_expected_search_cost_stop_rows": sum(
            1 for row in metric_rows if row["stop_route_source"] == "eval_expected_search_cost_rank"
        ),
        "selected_next_unit": "E007-M05 path-cost result interpretation and paper-table boundary decision",
    }
    claim_rows = build_claim_rows(coverage, paired_rows)

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "query_policy_metric_rows.jsonl", metric_rows)
    write_jsonl(OUT_DIR / "policy_metric_summary_rows.jsonl", policy_rows)
    write_jsonl(OUT_DIR / "paired_policy_delta_rows.jsonl", paired_rows)
    write_jsonl(OUT_DIR / "context_metric_summary_rows.jsonl", context_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "policy_metric_summary_rows": policy_rows,
            "paired_policy_delta_rows": paired_rows,
            "claim_boundary_rows": claim_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, policy_rows, paired_rows, claim_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
