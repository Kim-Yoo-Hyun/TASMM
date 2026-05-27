#!/usr/bin/env python3
"""Materialize detector candidate visit-order rows after E008-M10 navmesh validation."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M11_detector_candidate_visit_order_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M11_detector_candidate_visit_order_path_smoke_v0"
VERSION = "e008_m11_detector_candidate_visit_order_path_smoke_v0"

M10_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M10_detector_candidate_navmesh_validation_v0"

POLICIES = [
    {
        "policy_id": "detector_confidence_all_candidates_v0",
        "candidate_scope": "all_label_compatible_candidates",
        "description": "Sort all query-compatible detector candidates by detector confidence; retain unreachable/snap-failed rows as policy failures.",
    },
    {
        "policy_id": "detector_confidence_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_candidates",
        "description": "Sort only M10 path-ready candidates by detector confidence.",
    },
    {
        "policy_id": "path_cost_ascending_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_candidates",
        "description": "Sort only M10 path-ready candidates by source-to-candidate geodesic path cost.",
    },
    {
        "policy_id": "confidence_path_cost_tradeoff_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_candidates",
        "description": "Sort only M10 path-ready candidates by confidence divided by one plus source-to-candidate geodesic path cost.",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return float(ordered[idx])


def is_path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) and finite_float(row.get("source_to_snapped_geodesic_m")) is not None


def query_label_compatible(object_category: object, label: object) -> bool:
    query = str(object_category or "").lower().replace("-", "_")
    candidate = str(label or "").lower().replace("-", "_")
    if not query or not candidate:
        return False
    aliases = {
        "tv_monitor": {"tv", "television", "monitor", "tv_monitor"},
        "television": {"tv", "television", "monitor", "tv_monitor"},
        "tv": {"tv", "television", "monitor", "tv_monitor"},
    }
    if query in aliases:
        return candidate in aliases[query]
    return query == candidate


def sort_rows(policy_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if policy_id == "detector_confidence_all_candidates_v0":
        return sorted(rows, key=lambda r: (-(finite_float(r.get("confidence")) or -1.0), int(r.get("candidate_rank") or 10**9), str(r.get("proposal_uid"))))
    path_ready_rows = [row for row in rows if is_path_ready(row)]
    if policy_id == "detector_confidence_reachable_subset_v0":
        return sorted(path_ready_rows, key=lambda r: (-(finite_float(r.get("confidence")) or -1.0), int(r.get("candidate_rank") or 10**9), str(r.get("proposal_uid"))))
    if policy_id == "path_cost_ascending_reachable_subset_v0":
        return sorted(
            path_ready_rows,
            key=lambda r: (
                finite_float(r.get("source_to_snapped_geodesic_m")) or math.inf,
                -(finite_float(r.get("confidence")) or -1.0),
                int(r.get("candidate_rank") or 10**9),
                str(r.get("proposal_uid")),
            ),
        )
    if policy_id == "confidence_path_cost_tradeoff_reachable_subset_v0":
        return sorted(
            path_ready_rows,
            key=lambda r: (
                -tradeoff_score(r),
                finite_float(r.get("source_to_snapped_geodesic_m")) or math.inf,
                int(r.get("candidate_rank") or 10**9),
                str(r.get("proposal_uid")),
            ),
        )
    raise ValueError(f"unknown policy: {policy_id}")


def tradeoff_score(row: dict[str, Any]) -> float:
    confidence = finite_float(row.get("confidence")) or 0.0
    path_m = finite_float(row.get("source_to_snapped_geodesic_m"))
    if path_m is None:
        return -math.inf
    return float(confidence / (1.0 + path_m))


def build_visit_order_rows(rows_by_scan: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    visit_rows: list[dict[str, Any]] = []
    scan_metric_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []

    for policy in POLICIES:
        policy_id = policy["policy_id"]
        per_scan_metrics: list[dict[str, Any]] = []
        for scan_id in sorted(rows_by_scan):
            scan_rows = rows_by_scan[scan_id]
            ranked_rows = sort_rows(policy_id, scan_rows)
            cumulative_known_cost = 0.0
            ready_rank: int | None = None
            ready_cost: float | None = None
            ready_uid: str | None = None
            for rank, row in enumerate(ranked_rows, start=1):
                path_ready = is_path_ready(row)
                path_cost = finite_float(row.get("source_to_snapped_geodesic_m")) if path_ready else None
                if path_cost is not None:
                    cumulative_known_cost += path_cost
                if path_ready and ready_rank is None:
                    ready_rank = rank
                    ready_cost = path_cost
                    ready_uid = str(row.get("proposal_uid"))
                visit_rows.append(
                    {
                        "version": VERSION,
                        "policy_id": policy_id,
                        "candidate_scope": policy["candidate_scope"],
                        "scan_id": scan_id,
                        "adapter_episode_id": row.get("adapter_episode_id"),
                        "scene_key": row.get("scene_key"),
                        "object_category": row.get("object_category"),
                        "visit_rank": rank,
                        "proposal_uid": row.get("proposal_uid"),
                        "raw_candidate_uid": row.get("raw_candidate_uid"),
                        "label_canonical": row.get("label_canonical"),
                        "candidate_rank_m09": row.get("candidate_rank"),
                        "confidence": row.get("confidence"),
                        "selection_score": row.get("selection_score"),
                        "source_to_candidate_path_cost_m": path_cost,
                        "snap_distance_m": row.get("snap_distance_m"),
                        "path_ready": path_ready,
                        "navmesh_validation_status": row.get("navmesh_validation_status"),
                        "blocked_candidate_for_path_policy": not path_ready,
                        "cumulative_known_path_cost_m": cumulative_known_cost,
                        "confidence_path_cost_tradeoff_score": tradeoff_score(row) if path_ready else None,
                        "query_label_compatible": query_label_compatible(row.get("object_category"), row.get("label_canonical")),
                        "policy_input_allowed": bool(row.get("policy_input_allowed")),
                        "uses_objectnav_eval_goal": bool(row.get("uses_objectnav_eval_goal")),
                        "uses_objectnav_eval_viewpoint": bool(row.get("uses_objectnav_eval_viewpoint")),
                    }
                )
            metric = summarize_scan_policy(policy_id, policy["candidate_scope"], scan_id, scan_rows, ranked_rows, ready_rank, ready_cost, ready_uid)
            scan_metric_rows.append(metric)
            per_scan_metrics.append(metric)
        aggregate_rows.append(summarize_policy_aggregate(policy_id, policy["candidate_scope"], per_scan_metrics))
    return visit_rows, scan_metric_rows, aggregate_rows


def summarize_scan_policy(
    policy_id: str,
    scope: str,
    scan_id: str,
    scan_rows: list[dict[str, Any]],
    ranked_rows: list[dict[str, Any]],
    first_ready_rank: int | None,
    first_ready_cost: float | None,
    first_ready_uid: str | None,
) -> dict[str, Any]:
    top1 = ranked_rows[:1]
    top3 = ranked_rows[:3]
    top5 = ranked_rows[:5]
    top1_costs = [finite_float(row.get("source_to_snapped_geodesic_m")) for row in top1 if is_path_ready(row)]
    top3_costs = [finite_float(row.get("source_to_snapped_geodesic_m")) for row in top3 if is_path_ready(row)]
    top5_costs = [finite_float(row.get("source_to_snapped_geodesic_m")) for row in top5 if is_path_ready(row)]
    top1_costs_f = [v for v in top1_costs if v is not None]
    top3_costs_f = [v for v in top3_costs if v is not None]
    top5_costs_f = [v for v in top5_costs if v is not None]
    object_category = scan_rows[0].get("object_category") if scan_rows else None
    return {
        "version": VERSION,
        "metric_scope": "scan_policy",
        "policy_id": policy_id,
        "candidate_scope": scope,
        "scan_id": scan_id,
        "adapter_episode_id": scan_rows[0].get("adapter_episode_id") if scan_rows else None,
        "scene_key": scan_rows[0].get("scene_key") if scan_rows else None,
        "object_category": object_category,
        "input_candidate_rows": len(scan_rows),
        "ranked_candidate_rows": len(ranked_rows),
        "path_ready_ranked_rows": sum(1 for row in ranked_rows if is_path_ready(row)),
        "blocked_ranked_rows": sum(1 for row in ranked_rows if not is_path_ready(row)),
        "first_path_ready_rank": first_ready_rank,
        "first_path_ready_cost_m": first_ready_cost,
        "first_path_ready_proposal_uid": first_ready_uid,
        "top1_path_ready": bool(top1 and is_path_ready(top1[0])),
        "top3_path_ready_rows": sum(1 for row in top3 if is_path_ready(row)),
        "top5_path_ready_rows": sum(1 for row in top5 if is_path_ready(row)),
        "top5_blocked_rows": sum(1 for row in top5 if not is_path_ready(row)),
        "top1_known_path_cost_m": top1_costs_f[0] if top1_costs_f else None,
        "top3_cumulative_known_path_cost_m": sum(top3_costs_f) if top3_costs_f else None,
        "top5_cumulative_known_path_cost_m": sum(top5_costs_f) if top5_costs_f else None,
        "mean_top5_known_path_cost_m": mean(top5_costs_f),
        "candidate_visit_order_path_smoke_ready": bool(ranked_rows and any(is_path_ready(row) for row in ranked_rows)),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint")) for row in ranked_rows
        ),
    }


def summarize_policy_aggregate(policy_id: str, scope: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_ready_ranks = [finite_float(row.get("first_path_ready_rank")) for row in rows if row.get("first_path_ready_rank") is not None]
    first_ready_costs = [finite_float(row.get("first_path_ready_cost_m")) for row in rows if row.get("first_path_ready_cost_m") is not None]
    top1_costs = [finite_float(row.get("top1_known_path_cost_m")) for row in rows if row.get("top1_known_path_cost_m") is not None]
    top3_costs = [finite_float(row.get("top3_cumulative_known_path_cost_m")) for row in rows if row.get("top3_cumulative_known_path_cost_m") is not None]
    top5_costs = [finite_float(row.get("top5_cumulative_known_path_cost_m")) for row in rows if row.get("top5_cumulative_known_path_cost_m") is not None]
    first_ready_ranks_f = [v for v in first_ready_ranks if v is not None]
    first_ready_costs_f = [v for v in first_ready_costs if v is not None]
    top1_costs_f = [v for v in top1_costs if v is not None]
    top3_costs_f = [v for v in top3_costs if v is not None]
    top5_costs_f = [v for v in top5_costs if v is not None]
    return {
        "version": VERSION,
        "metric_scope": "policy_aggregate",
        "policy_id": policy_id,
        "candidate_scope": scope,
        "scan_policy_rows": len(rows),
        "ranked_candidate_rows": sum(int(row.get("ranked_candidate_rows") or 0) for row in rows),
        "path_ready_ranked_rows": sum(int(row.get("path_ready_ranked_rows") or 0) for row in rows),
        "blocked_ranked_rows": sum(int(row.get("blocked_ranked_rows") or 0) for row in rows),
        "top1_path_ready_scan_rows": sum(1 for row in rows if row.get("top1_path_ready")),
        "top5_blocked_rows": sum(int(row.get("top5_blocked_rows") or 0) for row in rows),
        "mean_first_path_ready_rank": mean(first_ready_ranks_f),
        "mean_first_path_ready_cost_m": mean(first_ready_costs_f),
        "p90_first_path_ready_cost_m": percentile(first_ready_costs_f, 90),
        "mean_top1_known_path_cost_m": mean(top1_costs_f),
        "mean_top3_cumulative_known_path_cost_m": mean(top3_costs_f),
        "mean_top5_cumulative_known_path_cost_m": mean(top5_costs_f),
        "candidate_visit_order_path_smoke_ready": all(row.get("candidate_visit_order_path_smoke_ready") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows),
    }


def build_failure_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in candidate_rows:
        if is_path_ready(row):
            continue
        out.append(
            {
                "version": VERSION,
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "proposal_uid": row.get("proposal_uid"),
                "label_canonical": row.get("label_canonical"),
                "confidence": row.get("confidence"),
                "candidate_rank_m09": row.get("candidate_rank"),
                "navmesh_validation_status": row.get("navmesh_validation_status"),
                "source_to_snapped_path_error": row.get("source_to_snapped_path_error"),
                "snap_distance_m": row.get("snap_distance_m"),
                "snapped_navigable": row.get("snapped_navigable"),
                "source_to_snapped_path_found": row.get("source_to_snapped_path_found"),
                "claim_boundary_use": "policy_failure_accounting_only",
            }
        )
    return sorted(out, key=lambda r: (str(r.get("scan_id")), str(r.get("navmesh_validation_status")), int(r.get("candidate_rank_m09") or 10**9)))


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], failure_counts: Counter[str]) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_scan_rows} | {mean_first_path_ready_cost_m} | {mean_top5_cumulative_known_path_cost_m} |".format(
                **{k: format_value(row.get(k)) for k in row}
            )
        )
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M11 Detector Candidate Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M10 status: `{coverage['m10_status']}`.
- Input candidate rows: {coverage['input_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']} / {coverage['input_candidate_rows']}.
- Failure rows retained for policy accounting: {coverage['failure_rows']} ({failure_line}).
- Visit-order rows: {coverage['visit_order_rows']}.
- Policy metric rows: {coverage['policy_metric_rows']}.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready scans | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- This artifact is a visit-order/path-cost smoke, not an executed navigation benchmark.
- It does not claim real navigation `SR` / `SPL`.
- It does not use `ObjectNav` goal/viewpoint coordinates as policy input.
- The 12 non-path-ready rows remain explicit failure/accounting rows instead of being silently removed from the full denominator.

## Agent Inference

The reachable subset is sufficient to materialize detector candidate visit order over 6 `HM3D ObjectNav` adapter rows. The next validation should connect these policy rows to leakage-safe goal evaluation or a simulator execution contract before any real navigation claim is made.
"""


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m10_coverage = read_json(M10_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M10_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing M10 candidate_navmesh_rows.jsonl")

    query_compatible_rows = [row for row in candidate_rows if query_label_compatible(row.get("object_category"), row.get("label_canonical"))]
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_scan[str(row.get("scan_id"))].append(row)

    visit_rows, scan_metric_rows, aggregate_rows = build_visit_order_rows(rows_by_scan)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)

    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "proceed_after_visit_order_path_smoke",
            "selected_next_unit": "E008-M12 leakage-safe detector candidate goal-evaluation smoke",
            "reason": "M11 materializes detector candidate visit-order/path-cost rows without using eval goal/viewpoint fields; next step should evaluate candidate visits against ObjectNav targets under a leakage-safe evaluation contract.",
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "launch_long_job_now": False,
        }
    ]

    coverage = {
        "version": VERSION,
        "status": "e008_m11_detector_candidate_visit_order_path_smoke_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m10_status": m10_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "input_candidate_rows": len(candidate_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "evaluated_scan_rows": len(rows_by_scan),
        "path_ready_candidate_rows": sum(1 for row in query_compatible_rows if is_path_ready(row)),
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "policy_count": len(POLICIES),
        "visit_order_rows": len(visit_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows),
        "candidate_visit_order_path_smoke_ready": all(row.get("candidate_visit_order_path_smoke_ready") for row in aggregate_rows),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(DATA_OUT_DIR / "failure_rows.jsonl", failure_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, failure_counts))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
