#!/usr/bin/env python3
"""Audit E007 path-start and source-limit sensitivity for reviewer defense."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
M03_DIR = EXP_ROOT / "artifacts" / "E007-M03_external_candidate_grid_projection_v0"
M04_DIR = EXP_ROOT / "artifacts" / "E007-M04_path_cost_policy_metrics_v0"
M05_DIR = EXP_ROOT / "artifacts" / "E007-M05_path_cost_result_interpretation_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M06_path_start_source_limit_sensitivity_v0"
VERSION = "e007_m06_path_start_source_limit_sensitivity_v0"

METHOD_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"
POLICIES = [
    "real_static_memory_only_v0",
    "real_detector_confidence_top5_v0",
    "conceptgraphs_only_strict_top5_v0",
    "real_context_agnostic_memory_trust_reobserve_v0",
    "h001_real_task_context_memory_trust_v0",
    METHOD_POLICY,
]
BASELINES = [policy for policy in POLICIES if policy != METHOD_POLICY]


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


def safe_rate(num: int, den: int) -> float | None:
    return None if den == 0 else round(num / den, 6)


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return None if not valid else round(mean(valid), 6)


def round6(value: float | int | None) -> float | None:
    return None if value is None else round(float(value), 6)


def metric_subset(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    return [row for row in rows if predicate(row)]


def summarize_rows(rows: list[dict[str, Any]], *, denominator_rows: int | None = None) -> dict[str, Any]:
    den = len(rows) if denominator_rows is None else denominator_rows
    success_rows = sum(1 for row in rows if row["query_bridge_success_eval_only"])
    source_ready_rows = sum(1 for row in rows if row["path_source_ready"])
    return {
        "rows": len(rows),
        "denominator_rows": den,
        "success_rows": success_rows,
        "success_rate": safe_rate(success_rows, den),
        "source_ready_rows": source_ready_rows,
        "source_ready_rate": safe_rate(source_ready_rows, den),
        "mean_path_cost_m": safe_mean([row["path_expected_search_cost_m"] for row in rows]),
        "mean_path_attempt_spl_proxy": safe_mean([row["path_attempt_spl_proxy"] for row in rows]),
        "stop_route_source_counts": dict(Counter(row["stop_route_source"] for row in rows)),
    }


def build_policy_sensitivity_rows(
    metric_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_old_start_risk: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in route_rows:
        if row.get("candidate_source") != "old_memory" or int(row.get("route_index") or 0) != 1:
            continue
        policy = row["policy"]
        route_old_start_risk[policy]["old_first_rows"] += 1
        if not row.get("candidate_is_target_eval_only"):
            route_old_start_risk[policy]["old_first_non_target_rows"] += 1
        if (row.get("candidate_path_step_cost_m") or 0.0) == 0.0:
            route_old_start_risk[policy]["old_first_zero_step_rows"] += 1
        if not row.get("candidate_is_target_eval_only") and (row.get("candidate_path_step_cost_m") or 0.0) == 0.0:
            route_old_start_risk[policy]["old_first_non_target_zero_step_rows"] += 1

    rows_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        rows_by_policy[row["policy"]].append(row)

    output: list[dict[str, Any]] = []
    for policy in POLICIES:
        rows = rows_by_policy[policy]
        full = summarize_rows(rows)
        source_ready = summarize_rows(metric_subset(rows, lambda row: row["path_source_ready"]), denominator_rows=len(rows))
        direct_or_failure = summarize_rows(
            metric_subset(rows, lambda row: row["stop_route_source"] != "eval_expected_search_cost_rank"),
            denominator_rows=len(rows),
        )
        source_ready_direct = summarize_rows(
            metric_subset(
                rows,
                lambda row: row["path_source_ready"] and row["stop_route_source"] != "eval_expected_search_cost_rank",
            ),
            denominator_rows=len(rows),
        )
        stale_zero_cost_failures = [
            row
            for row in rows
            if not row["query_bridge_success_eval_only"]
            and row["path_source_ready"]
            and row["old_location_dead_end_visit_count"] > 0
            and (row["old_location_dead_end_cost_m_lower_bound"] or 0.0) == 0.0
        ]
        output.append(
            {
                "policy": policy,
                "full_success_rows": full["success_rows"],
                "full_success_rate": full["success_rate"],
                "source_ready_rows": source_ready["rows"],
                "source_ready_success_rows": source_ready["success_rows"],
                "source_ready_lower_bound_success_rate": source_ready["success_rate"],
                "source_limited_rows": len(rows) - source_ready["rows"],
                "source_limit_success_gap_rate": None
                if full["success_rate"] is None or source_ready["success_rate"] is None
                else round(full["success_rate"] - source_ready["success_rate"], 6),
                "eval_expected_search_cost_rank_rows": full["stop_route_source_counts"].get(
                    "eval_expected_search_cost_rank", 0
                ),
                "direct_or_failure_rows": direct_or_failure["rows"],
                "direct_or_failure_success_rows": direct_or_failure["success_rows"],
                "direct_or_failure_success_rate_full_denominator": direct_or_failure["success_rate"],
                "source_ready_direct_or_failure_rows": source_ready_direct["rows"],
                "source_ready_direct_or_failure_success_rows": source_ready_direct["success_rows"],
                "source_ready_direct_or_failure_success_rate_full_denominator": source_ready_direct["success_rate"],
                "mean_path_cost_m_source_ready_direct_or_failure": source_ready_direct["mean_path_cost_m"],
                "mean_path_attempt_spl_source_ready_direct_or_failure": source_ready_direct[
                    "mean_path_attempt_spl_proxy"
                ],
                "old_first_rows": route_old_start_risk[policy].get("old_first_rows", 0),
                "old_first_non_target_rows": route_old_start_risk[policy].get("old_first_non_target_rows", 0),
                "old_first_zero_step_rows": route_old_start_risk[policy].get("old_first_zero_step_rows", 0),
                "old_first_non_target_zero_step_rows": route_old_start_risk[policy].get(
                    "old_first_non_target_zero_step_rows", 0
                ),
                "zero_cost_stale_failure_rows": len(stale_zero_cost_failures),
                "path_start_bias_boundary": "old_memory_centroid_start_underestimates_old_location_dead_end_cost"
                if route_old_start_risk[policy].get("old_first_non_target_zero_step_rows", 0)
                else "no_old_first_non_target_zero_step_rows",
            }
        )
    return output


def paired_delta(
    metric_rows: list[dict[str, Any]],
    *,
    subset_id: str,
    subset_predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    by_policy_query = {(row["policy"], row["query_uid"]): row for row in metric_rows}
    method_rows = [row for row in metric_rows if row["policy"] == METHOD_POLICY]
    output: list[dict[str, Any]] = []
    for baseline in BASELINES:
        pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for method in method_rows:
            base = by_policy_query.get((baseline, method["query_uid"]))
            if base and subset_predicate(method) and subset_predicate(base):
                pairs.append((method, base))
        method_success = sum(1 for method, _ in pairs if method["query_bridge_success_eval_only"])
        base_success = sum(1 for _, base in pairs if base["query_bridge_success_eval_only"])
        output.append(
            {
                "subset_id": subset_id,
                "method_policy": METHOD_POLICY,
                "baseline_policy": baseline,
                "paired_rows": len(pairs),
                "method_success_rows": method_success,
                "baseline_success_rows": base_success,
                "method_success_rate": safe_rate(method_success, len(pairs)),
                "baseline_success_rate": safe_rate(base_success, len(pairs)),
                "success_rate_delta": None if not pairs else round((method_success - base_success) / len(pairs), 6),
                "method_mean_path_cost_m": safe_mean([method["path_expected_search_cost_m"] for method, _ in pairs]),
                "baseline_mean_path_cost_m": safe_mean([base["path_expected_search_cost_m"] for _, base in pairs]),
                "path_cost_delta_m": None
                if not pairs
                else round(
                    (safe_mean([method["path_expected_search_cost_m"] for method, _ in pairs]) or 0.0)
                    - (safe_mean([base["path_expected_search_cost_m"] for _, base in pairs]) or 0.0),
                    6,
                ),
                "method_mean_path_attempt_spl_proxy": safe_mean(
                    [method["path_attempt_spl_proxy"] for method, _ in pairs]
                ),
                "baseline_mean_path_attempt_spl_proxy": safe_mean(
                    [base["path_attempt_spl_proxy"] for _, base in pairs]
                ),
                "path_attempt_spl_delta": None
                if not pairs
                else round(
                    (safe_mean([method["path_attempt_spl_proxy"] for method, _ in pairs]) or 0.0)
                    - (safe_mean([base["path_attempt_spl_proxy"] for _, base in pairs]) or 0.0),
                    6,
                ),
            }
        )
    return output


def build_paired_delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subsets: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("full_query_success_only", lambda row: True),
        ("source_ready_only", lambda row: bool(row["path_source_ready"])),
        (
            "source_ready_direct_or_failure_only",
            lambda row: bool(row["path_source_ready"]) and row["stop_route_source"] != "eval_expected_search_cost_rank",
        ),
    ]
    output: list[dict[str, Any]] = []
    for subset_id, predicate in subsets:
        output.extend(paired_delta(metric_rows, subset_id=subset_id, subset_predicate=predicate))
    return output


def find_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    for row in rows:
        if row["policy"] == policy:
            return row
    raise RuntimeError(f"Missing policy sensitivity row: {policy}")


def find_delta(rows: list[dict[str, Any]], subset_id: str, baseline: str) -> dict[str, Any]:
    for row in rows:
        if row["subset_id"] == subset_id and row["baseline_policy"] == baseline:
            return row
    raise RuntimeError(f"Missing paired delta row: {subset_id}/{baseline}")


def build_reviewer_defense_rows(
    policy_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    method = find_policy(policy_rows, METHOD_POLICY)
    static = find_policy(policy_rows, "real_static_memory_only_v0")
    direct_static = find_delta(delta_rows, "source_ready_direct_or_failure_only", "real_static_memory_only_v0")
    direct_cg = find_delta(delta_rows, "source_ready_direct_or_failure_only", "conceptgraphs_only_strict_top5_v0")
    direct_h001 = find_delta(delta_rows, "source_ready_direct_or_failure_only", "h001_real_task_context_memory_trust_v0")
    return [
        {
            "attack_id": "R-E007-M06-001",
            "reviewer_attack": "Source-ready subset hides failures.",
            "risk": "medium",
            "sensitivity_result": (
                f"Method full success {method['full_success_rows']}/195; source-ready lower bound "
                f"{method['source_ready_success_rows']}/195; source-limited rows {method['source_limited_rows']}/195."
            ),
            "defense": "Report full success, source-ready lower bound, and source-limited rate together.",
            "claim_boundary": "Do not present source-ready metrics alone.",
        },
        {
            "attack_id": "R-E007-M06-002",
            "reviewer_attack": "Expected-search-cost stop-rank rows are not direct route-localization evidence.",
            "risk": "medium",
            "sensitivity_result": (
                f"Method has {method['eval_expected_search_cost_rank_rows']} stop-rank rows; direct/failure source-ready paired deltas remain "
                f"+{direct_static['success_rate_delta']} vs static and +{direct_cg['success_rate_delta']} vs ConceptGraphs."
            ),
            "defense": "Use direct/failure-only sensitivity as the stricter reviewer-facing check.",
            "claim_boundary": "Stop-rank rows support upstream rank-cost accounting only.",
        },
        {
            "attack_id": "R-E007-M06-003",
            "reviewer_attack": "Old-location dead-end cost is biased because paths start from old memory.",
            "risk": "high",
            "sensitivity_result": (
                f"Static memory has {static['zero_cost_stale_failure_rows']} zero-cost stale failures; all policies have "
                f"{sum(row['old_first_non_target_zero_step_rows'] for row in policy_rows)} old-first non-target zero-step rows."
            ),
            "defense": "Block `OldLocationDeadEndCostM` as a primary metric until robot/start-pose or executed navigation is added.",
            "claim_boundary": "E007 can claim path-cost bridge evidence, not old-location dead-end cost reduction.",
        },
        {
            "attack_id": "R-E007-M06-004",
            "reviewer_attack": "H001 + ConceptGraphs is not strictly better than H001-only.",
            "risk": "medium",
            "sensitivity_result": (
                f"Direct/failure source-ready delta vs H001-only is +{direct_h001['success_rate_delta']} success, "
                f"{direct_h001['path_attempt_spl_delta']} `PathAttemptSPLProxy`, and "
                f"{direct_h001['path_cost_delta_m']}m path cost."
            ),
            "defense": "Frame as map-assisted repair tradeoff, not path-cost optimality.",
            "claim_boundary": "No unconditional dominance over H001-only.",
        },
    ]


def build_claim_rows(
    policy_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    method = find_policy(policy_rows, METHOD_POLICY)
    direct_static = find_delta(delta_rows, "source_ready_direct_or_failure_only", "real_static_memory_only_v0")
    direct_cg = find_delta(delta_rows, "source_ready_direct_or_failure_only", "conceptgraphs_only_strict_top5_v0")
    direct_h001 = find_delta(delta_rows, "source_ready_direct_or_failure_only", "h001_real_task_context_memory_trust_v0")
    old_non_target_zero = sum(row["old_first_non_target_zero_step_rows"] for row in policy_rows)
    return [
        {
            "claim_id": "C-E007-M06-001",
            "claim": "E007 bridge table survives source-limit sensitivity for major baseline comparisons.",
            "status": "supported_with_proxy_boundary",
            "evidence": (
                f"Method lower-bound source-ready success is {method['source_ready_success_rows']}/195; "
                f"direct/failure-only paired deltas remain +{direct_static['success_rate_delta']} vs static and "
                f"+{direct_cg['success_rate_delta']} vs ConceptGraphs."
            ),
            "boundary": "Still report source-limited rows and do not call it real navigation.",
        },
        {
            "claim_id": "C-E007-M06-002",
            "claim": "Method-vs-H001 remains a repair tradeoff under stricter direct/failure-only sensitivity.",
            "status": "supported_with_tradeoff",
            "evidence": (
                f"Direct/failure source-ready paired delta vs H001-only: success +{direct_h001['success_rate_delta']}, "
                f"`PathAttemptSPLProxy` {direct_h001['path_attempt_spl_delta']}, path cost {direct_h001['path_cost_delta_m']}m."
            ),
            "boundary": "Do not claim path-cost optimality over H001-only.",
        },
        {
            "claim_id": "C-E007-M06-003",
            "claim": "Old-location dead-end cost is blocked as a primary paper metric.",
            "status": "blocked_as_primary_metric",
            "evidence": f"{old_non_target_zero} old-first non-target route rows have zero first-step cost.",
            "boundary": "Needs robot/start-pose, spawn sensitivity, or executed navigation.",
        },
    ]


def build_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e007_m07_bridge_table_package_and_navigation_expansion_decision",
            "selected": True,
            "decision": "selected",
            "next_unit": "E007-M07 bridge-table package and navigation-expansion decision",
            "reason": [
                "E007-M06 makes the current bridge table reviewer-defensible with explicit source-limit and path-start boundaries.",
                "The next step should package the table/claim ledger before deciding whether to launch real navigation infrastructure.",
            ],
        },
        {
            "rank": 2,
            "route_id": "real_navigation_sr_spl_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "Simulator/navmesh/trajectory execution integration",
            "reason": [
                "Real navigation remains a separate infrastructure step.",
                "E007-M06 still blocks `OldLocationDeadEndCostM` without a robot/start-pose source.",
            ],
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    reviewer_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    policy_table = [
        "| Policy | Full Success | Source-Ready LB | Direct/Failure LB | Stop-Rank Rows | Source-Limited | Old-Start Non-Target Zero |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in policy_rows:
        policy_table.append(
            f"| `{row['policy']}` | {row['full_success_rows']} / 195 | "
            f"{row['source_ready_success_rows']} / 195 | "
            f"{row['source_ready_direct_or_failure_success_rows']} / 195 | "
            f"{row['eval_expected_search_cost_rank_rows']} | {row['source_limited_rows']} | "
            f"{row['old_first_non_target_zero_step_rows']} |"
        )

    delta_table = [
        "| Subset | Baseline | Paired Rows | Success Delta | Path Cost Delta | `PathAttemptSPLProxy` Delta |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in delta_rows:
        delta_table.append(
            f"| `{row['subset_id']}` | `{row['baseline_policy']}` | {row['paired_rows']} | "
            f"{row['success_rate_delta']} | {row['path_cost_delta_m']} | {row['path_attempt_spl_delta']} |"
        )

    reviewer_table = ["| Attack | Risk | Defense |", "| --- | --- | --- |"]
    for row in reviewer_rows:
        reviewer_table.append(f"| {row['reviewer_attack']} | `{row['risk']}` | {row['defense']} |")

    claim_table = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_table.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    route_table = ["| Rank | Route | Decision | Next Unit |", "| ---: | --- | --- | --- |"]
    for row in route_rows:
        route_table.append(f"| {row['rank']} | `{row['route_id']}` | `{row['decision']}` | {row['next_unit']} |")

    return f"""# E007-M06 Path-Start / Source-Limit Sensitivity

## Facts

- Status: `{coverage["status"]}`.
- Query-policy rows: {coverage["query_policy_rows"]}.
- Source-limited query-policy rows: {coverage["source_limited_query_policy_rows"]}.
- Stop-rank query-policy rows: {coverage["eval_expected_search_cost_rank_rows"]}.
- Old-first non-target zero-step route rows: {coverage["old_first_non_target_zero_step_rows"]}.
- Selected next unit: {coverage["selected_next_unit"]}.
- Real navigation `SR` / `SPL` ready: false.

## Sensitivity Table

{chr(10).join(policy_table)}

## Paired Delta Sensitivity

{chr(10).join(delta_table)}

## Reviewer Defense

{chr(10).join(reviewer_table)}

## Claim Boundary

{chr(10).join(claim_table)}

## Route Decision

{chr(10).join(route_table)}

## Agent Inference

- The E007 bridge table is defensible as an occupancy-grid path-cost proxy table if full denominator, source-ready lower bound, and direct/failure-only sensitivity are reported together.
- The result remains strongest against static memory, detector-confidence ranking, and `ConceptGraphs`-only.
- The method-vs-H001 result remains a repair tradeoff rather than path-cost optimality.
- `OldLocationDeadEndCostM` should stay blocked until a robot/start-pose or executed navigation source exists.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m04 = read_json(M04_DIR / "coverage.json")
    m05 = read_json(M05_DIR / "coverage.json")
    metric_rows = read_jsonl(M04_DIR / "query_policy_metric_rows.jsonl")
    route_rows = read_jsonl(M03_DIR / "projected_route_rows.jsonl")
    if not metric_rows:
        raise RuntimeError("Missing E007-M04 query policy metric rows.")
    if not route_rows:
        raise RuntimeError("Missing E007-M03 projected route rows.")

    policy_rows = build_policy_sensitivity_rows(metric_rows, route_rows)
    delta_rows = build_paired_delta_rows(metric_rows)
    reviewer_rows = build_reviewer_defense_rows(policy_rows, delta_rows)
    claim_rows = build_claim_rows(policy_rows, delta_rows)
    route_decision_rows = build_route_rows()

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m06_path_start_source_limit_sensitivity_ready",
        "version": VERSION,
        "m04_status": m04.get("status"),
        "m05_status": m05.get("status"),
        "query_policy_rows": len(metric_rows),
        "source_limited_query_policy_rows": sum(1 for row in metric_rows if not row["path_source_ready"]),
        "eval_expected_search_cost_rank_rows": sum(
            1 for row in metric_rows if row["stop_route_source"] == "eval_expected_search_cost_rank"
        ),
        "old_first_non_target_zero_step_rows": sum(
            1
            for row in route_rows
            if row.get("candidate_source") == "old_memory"
            and int(row.get("route_index") or 0) == 1
            and not row.get("candidate_is_target_eval_only")
            and (row.get("candidate_path_step_cost_m") or 0.0) == 0.0
        ),
        "bridge_table_defensible_with_proxy_boundary": True,
        "real_navigation_sr_spl_ready": False,
        "old_location_dead_end_cost_primary_ready": False,
        "selected_next_unit": "E007-M07 bridge-table package and navigation-expansion decision",
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "policy_sensitivity_rows.jsonl", policy_rows)
    write_jsonl(OUT_DIR / "paired_delta_sensitivity_rows.jsonl", delta_rows)
    write_jsonl(OUT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(OUT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "policy_sensitivity_rows": policy_rows,
            "paired_delta_sensitivity_rows": delta_rows,
            "reviewer_defense_rows": reviewer_rows,
            "claim_boundary_rows": claim_rows,
            "route_decision_rows": route_decision_rows,
        },
    )
    write_text(
        OUT_DIR / "report.md",
        build_report(coverage, policy_rows, delta_rows, reviewer_rows, claim_rows, route_decision_rows),
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
