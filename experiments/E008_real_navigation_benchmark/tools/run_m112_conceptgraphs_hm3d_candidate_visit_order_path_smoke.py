#!/usr/bin/env python3
"""Materialize ConceptGraphs HM3D candidate visit-order/path rows after E008-M111."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"
)
M111_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
)
VERSION = "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"

POLICIES = [
    {
        "policy_id": "conceptgraphs_semantic_all_candidates_v0",
        "candidate_scope": "all_label_compatible_conceptgraphs_candidates",
        "description": "Sort all query-compatible ConceptGraphs candidates by CLIP text semantic score; retain non-path-ready rows as policy failures.",
    },
    {
        "policy_id": "conceptgraphs_semantic_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_conceptgraphs_candidates",
        "description": "Sort only M111 path-ready ConceptGraphs candidates by CLIP text semantic score.",
    },
    {
        "policy_id": "path_cost_ascending_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_conceptgraphs_candidates",
        "description": "Sort only M111 path-ready ConceptGraphs candidates by source-to-candidate geodesic path cost.",
    },
    {
        "policy_id": "semantic_path_cost_tradeoff_reachable_subset_v0",
        "candidate_scope": "path_ready_label_compatible_conceptgraphs_candidates",
        "description": "Sort only M111 path-ready ConceptGraphs candidates by semantic score divided by one plus source-to-candidate geodesic path cost.",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def is_path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) and finite_float(row.get("source_to_snapped_geodesic_m")) is not None


def semantic_score(row: dict[str, Any]) -> float:
    return finite_float(row.get("semantic_score")) or -math.inf


def path_cost(row: dict[str, Any]) -> float | None:
    return finite_float(row.get("source_to_snapped_geodesic_m")) if is_path_ready(row) else None


def semantic_path_cost_tradeoff_score(row: dict[str, Any]) -> float:
    sem = finite_float(row.get("semantic_score")) or 0.0
    cost = path_cost(row)
    if cost is None:
        return -math.inf
    return float(sem / (1.0 + cost))


def sort_rows(policy_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if policy_id == "conceptgraphs_semantic_all_candidates_v0":
        return sorted(
            rows,
            key=lambda row: (
                -semantic_score(row),
                int(row.get("rank") or row.get("candidate_rank") or 10**9),
                str(row.get("proposal_uid")),
            ),
        )
    path_ready_rows = [row for row in rows if is_path_ready(row)]
    if policy_id == "conceptgraphs_semantic_reachable_subset_v0":
        return sorted(
            path_ready_rows,
            key=lambda row: (
                -semantic_score(row),
                int(row.get("rank") or row.get("candidate_rank") or 10**9),
                str(row.get("proposal_uid")),
            ),
        )
    if policy_id == "path_cost_ascending_reachable_subset_v0":
        return sorted(
            path_ready_rows,
            key=lambda row: (
                path_cost(row) or math.inf,
                -semantic_score(row),
                int(row.get("rank") or row.get("candidate_rank") or 10**9),
                str(row.get("proposal_uid")),
            ),
        )
    if policy_id == "semantic_path_cost_tradeoff_reachable_subset_v0":
        return sorted(
            path_ready_rows,
            key=lambda row: (
                -semantic_path_cost_tradeoff_score(row),
                path_cost(row) or math.inf,
                int(row.get("rank") or row.get("candidate_rank") or 10**9),
                str(row.get("proposal_uid")),
            ),
        )
    raise ValueError(f"unknown policy: {policy_id}")


def build_visit_order_rows(
    rows_by_query: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    visit_rows: list[dict[str, Any]] = []
    query_policy_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []

    for policy in POLICIES:
        policy_id = policy["policy_id"]
        per_query_metrics: list[dict[str, Any]] = []
        for query_uid in sorted(rows_by_query):
            query_rows = rows_by_query[query_uid]
            ranked_rows = sort_rows(policy_id, query_rows)
            cumulative_known_cost = 0.0
            first_ready_rank: int | None = None
            first_ready_cost: float | None = None
            first_ready_uid: str | None = None
            for rank, row in enumerate(ranked_rows, start=1):
                ready = is_path_ready(row)
                cost = path_cost(row)
                if cost is not None:
                    cumulative_known_cost += cost
                if ready and first_ready_rank is None:
                    first_ready_rank = rank
                    first_ready_cost = cost
                    first_ready_uid = str(row.get("proposal_uid"))
                visit_rows.append(
                    {
                        "version": VERSION,
                        "policy_id": policy_id,
                        "candidate_scope": policy["candidate_scope"],
                        "query_uid": query_uid,
                        "scan_id": row.get("scan_id"),
                        "adapter_episode_id": row.get("adapter_episode_id"),
                        "scene_key": row.get("scene_key"),
                        "object_category": row.get("object_category"),
                        "task_context_id": row.get("task_context_id"),
                        "visit_rank": rank,
                        "proposal_uid": row.get("proposal_uid"),
                        "candidate_uid": row.get("candidate_uid"),
                        "raw_candidate_uid": row.get("raw_candidate_uid"),
                        "label_canonical": row.get("label_canonical"),
                        "conceptgraphs_semantic_rank": row.get("rank"),
                        "candidate_rank": row.get("candidate_rank"),
                        "semantic_score": row.get("semantic_score"),
                        "selection_score": row.get("selection_score"),
                        "candidate_confidence_mean": row.get("candidate_confidence_mean"),
                        "candidate_point_count": row.get("candidate_point_count"),
                        "candidate_num_detections": row.get("candidate_num_detections"),
                        "source_to_candidate_path_cost_m": cost,
                        "snap_distance_m": row.get("snap_distance_m"),
                        "path_ready": ready,
                        "navmesh_validation_status": row.get("navmesh_validation_status"),
                        "blocked_candidate_for_path_policy": not ready,
                        "cumulative_known_path_cost_m": cumulative_known_cost,
                        "semantic_path_cost_tradeoff_score": semantic_path_cost_tradeoff_score(row) if ready else None,
                        "query_label_compatible": query_label_compatible(row.get("object_category"), row.get("label_canonical")),
                        "policy_input_allowed": bool(row.get("policy_input_allowed")),
                        "uses_objectnav_eval_goal": bool(row.get("uses_objectnav_eval_goal")),
                        "uses_objectnav_eval_viewpoint": bool(row.get("uses_objectnav_eval_viewpoint")),
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                        ),
                        "source_class_name_boundary": "generic_item_class_names_clip_text_score_only",
                    }
                )
            metric = summarize_query_policy(
                policy_id,
                policy["candidate_scope"],
                query_uid,
                query_rows,
                ranked_rows,
                first_ready_rank,
                first_ready_cost,
                first_ready_uid,
            )
            query_policy_rows.append(metric)
            per_query_metrics.append(metric)
        aggregate_rows.append(summarize_policy_aggregate(policy_id, policy["candidate_scope"], per_query_metrics))
    return visit_rows, query_policy_rows, aggregate_rows


def summarize_query_policy(
    policy_id: str,
    scope: str,
    query_uid: str,
    query_rows: list[dict[str, Any]],
    ranked_rows: list[dict[str, Any]],
    first_ready_rank: int | None,
    first_ready_cost: float | None,
    first_ready_uid: str | None,
) -> dict[str, Any]:
    top1 = ranked_rows[:1]
    top3 = ranked_rows[:3]
    top5 = ranked_rows[:5]
    top1_costs = [path_cost(row) for row in top1 if is_path_ready(row)]
    top3_costs = [path_cost(row) for row in top3 if is_path_ready(row)]
    top5_costs = [path_cost(row) for row in top5 if is_path_ready(row)]
    top1_costs_f = [value for value in top1_costs if value is not None]
    top3_costs_f = [value for value in top3_costs if value is not None]
    top5_costs_f = [value for value in top5_costs if value is not None]
    first = query_rows[0] if query_rows else {}
    return {
        "version": VERSION,
        "metric_scope": "query_policy",
        "policy_id": policy_id,
        "candidate_scope": scope,
        "query_uid": query_uid,
        "scan_id": first.get("scan_id"),
        "adapter_episode_id": first.get("adapter_episode_id"),
        "scene_key": first.get("scene_key"),
        "object_category": first.get("object_category"),
        "label_canonical": first.get("label_canonical"),
        "task_context_id": first.get("task_context_id"),
        "input_candidate_rows": len(query_rows),
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
            bool(row.get("uses_objectnav_eval_goal"))
            or bool(row.get("uses_objectnav_eval_viewpoint"))
            or bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
            for row in ranked_rows
        ),
        "source_class_name_boundary": "generic_item_class_names_clip_text_score_only",
    }


def summarize_policy_aggregate(policy_id: str, scope: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_ready_ranks = [
        finite_float(row.get("first_path_ready_rank")) for row in rows if row.get("first_path_ready_rank") is not None
    ]
    first_ready_costs = [
        finite_float(row.get("first_path_ready_cost_m")) for row in rows if row.get("first_path_ready_cost_m") is not None
    ]
    top1_costs = [
        finite_float(row.get("top1_known_path_cost_m")) for row in rows if row.get("top1_known_path_cost_m") is not None
    ]
    top3_costs = [
        finite_float(row.get("top3_cumulative_known_path_cost_m"))
        for row in rows
        if row.get("top3_cumulative_known_path_cost_m") is not None
    ]
    top5_costs = [
        finite_float(row.get("top5_cumulative_known_path_cost_m"))
        for row in rows
        if row.get("top5_cumulative_known_path_cost_m") is not None
    ]
    first_ready_ranks_f = [value for value in first_ready_ranks if value is not None]
    first_ready_costs_f = [value for value in first_ready_costs if value is not None]
    top1_costs_f = [value for value in top1_costs if value is not None]
    top3_costs_f = [value for value in top3_costs if value is not None]
    top5_costs_f = [value for value in top5_costs if value is not None]
    return {
        "version": VERSION,
        "metric_scope": "policy_aggregate",
        "policy_id": policy_id,
        "candidate_scope": scope,
        "query_policy_rows": len(rows),
        "ranked_candidate_rows": sum(int(row.get("ranked_candidate_rows") or 0) for row in rows),
        "path_ready_ranked_rows": sum(int(row.get("path_ready_ranked_rows") or 0) for row in rows),
        "blocked_ranked_rows": sum(int(row.get("blocked_ranked_rows") or 0) for row in rows),
        "top1_path_ready_query_rows": sum(1 for row in rows if row.get("top1_path_ready")),
        "top5_blocked_rows": sum(int(row.get("top5_blocked_rows") or 0) for row in rows),
        "mean_first_path_ready_rank": mean(first_ready_ranks_f),
        "mean_first_path_ready_cost_m": mean(first_ready_costs_f),
        "p90_first_path_ready_cost_m": percentile(first_ready_costs_f, 90),
        "mean_top1_known_path_cost_m": mean(top1_costs_f),
        "mean_top3_cumulative_known_path_cost_m": mean(top3_costs_f),
        "mean_top5_cumulative_known_path_cost_m": mean(top5_costs_f),
        "candidate_visit_order_path_smoke_ready": all(row.get("candidate_visit_order_path_smoke_ready") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows
        ),
        "source_class_name_boundary": "generic_item_class_names_clip_text_score_only",
    }


def build_query_source_policy_rows(
    query_policy_rows: list[dict[str, Any]],
    query_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundary_by_query = {str(row.get("query_uid")): row for row in query_source_rows}
    out: list[dict[str, Any]] = []
    for metric in query_policy_rows:
        boundary = boundary_by_query.get(str(metric.get("query_uid")), {})
        out.append(
            {
                "version": VERSION,
                "metric_scope": "conceptgraphs_query_source_policy",
                "policy_id": metric.get("policy_id"),
                "candidate_scope": metric.get("candidate_scope"),
                "query_uid": metric.get("query_uid"),
                "scan_id": metric.get("scan_id"),
                "adapter_episode_id": metric.get("adapter_episode_id"),
                "scene_key": metric.get("scene_key"),
                "object_category": boundary.get("label_canonical") or metric.get("object_category"),
                "m102_branch": boundary.get("m102_branch"),
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m111": bool(boundary.get("source_ready")),
                "source_gap_after_m111": bool(boundary.get("source_gap")),
                "input_candidate_rows": metric.get("input_candidate_rows"),
                "ranked_candidate_rows": metric.get("ranked_candidate_rows"),
                "path_ready_ranked_rows": metric.get("path_ready_ranked_rows"),
                "blocked_ranked_rows": metric.get("blocked_ranked_rows"),
                "first_path_ready_rank": metric.get("first_path_ready_rank"),
                "first_path_ready_cost_m": metric.get("first_path_ready_cost_m"),
                "top1_path_ready": metric.get("top1_path_ready"),
                "top5_path_ready_rows": metric.get("top5_path_ready_rows"),
                "top5_blocked_rows": metric.get("top5_blocked_rows"),
                "top5_cumulative_known_path_cost_m": metric.get("top5_cumulative_known_path_cost_m"),
                "candidate_visit_order_path_smoke_ready": bool(metric.get("candidate_visit_order_path_smoke_ready"))
                and bool(boundary.get("source_ready")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "real_navigation_sr_spl_ready": False,
                "source_gap_recovery_evaluated": False,
                "claim_boundary": "M112 evaluates ConceptGraphs candidate visit order and source-to-candidate path costs only; it does not score eval goals or execute trajectories.",
            }
        )
    return out


def build_failure_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in candidate_rows:
        if is_path_ready(row):
            continue
        out.append(
            {
                "version": VERSION,
                "query_uid": row.get("query_uid"),
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "proposal_uid": row.get("proposal_uid"),
                "candidate_uid": row.get("candidate_uid"),
                "label_canonical": row.get("label_canonical"),
                "conceptgraphs_semantic_rank": row.get("rank"),
                "semantic_score": row.get("semantic_score"),
                "candidate_confidence_mean": row.get("candidate_confidence_mean"),
                "navmesh_validation_status": row.get("navmesh_validation_status"),
                "source_to_snapped_path_error": row.get("source_to_snapped_path_error"),
                "snap_distance_m": row.get("snap_distance_m"),
                "snapped_navigable": row.get("snapped_navigable"),
                "source_to_snapped_path_found": row.get("source_to_snapped_path_found"),
                "claim_boundary_use": "policy_failure_accounting_only",
            }
        )
    return sorted(
        out,
        key=lambda row: (
            str(row.get("scan_id")),
            str(row.get("navmesh_validation_status")),
            int(row.get("conceptgraphs_semantic_rank") or 10**9),
        ),
    )


def build_leakage_audit_rows(
    visit_rows: list[dict[str, Any]],
    query_policy_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        {
            "check_id": "visit_rows_do_not_use_eval_goal_or_viewpoint",
            "passed": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in visit_rows),
            "row_count": len(visit_rows),
        },
        {
            "check_id": "query_policy_rows_do_not_use_eval_goal_or_viewpoint",
            "passed": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in query_policy_rows),
            "row_count": len(query_policy_rows),
        },
        {
            "check_id": "aggregate_rows_do_not_use_eval_goal_or_viewpoint",
            "passed": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows),
            "row_count": len(aggregate_rows),
        },
        {
            "check_id": "policy_rows_do_not_contain_goal_distance_or_success_fields",
            "passed": not any(
                key in row
                for row in visit_rows
                for key in ("eval_success", "distance_to_goal", "success_label", "objectnav_goal_distance_m")
            ),
            "row_count": len(visit_rows),
        },
    ]
    return [{"version": VERSION, **row} for row in checks]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_conceptgraphs_visit_order_path_materialization",
            "supported": True,
            "claim_boundary": "M112 materializes ConceptGraphs HM3D candidate visit-order and source-to-candidate path-cost rows without eval-goal/viewpoint policy leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M112 does not compare candidates against eval-only ObjectNav goals or viewpoints, so it cannot claim source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M112 does not execute Habitat trajectories, so it cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M112 covers two source-gap ConceptGraphs cases only and lacks heldout transfer plus external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_conceptgraphs_class_name_recognition",
            "supported": False,
            "claim_boundary": "The current ConceptGraphs source class names are generic item labels; M112 uses CLIP feature/text semantic scores, not class-name recognition.",
        },
    ]


def build_route_decision_rows(ready: bool, leakage_pass: bool) -> list[dict[str, Any]]:
    if ready and leakage_pass:
        return [
            {
                "version": VERSION,
                "decision": "proceed_after_conceptgraphs_visit_order_path_smoke",
                "selected_next_unit": "E008-M113 ConceptGraphs HM3D leakage-safe candidate goal-evaluation smoke",
                "reason": "M112 materializes ConceptGraphs semantic/path-cost visit-order rows without eval-goal leakage; next step is leakage-safe eval-only target scoring for source-gap recovery.",
                "launch_long_job_now": False,
                "source_gap_recovery_evaluated": False,
                "real_navigation_sr_spl_ready": False,
                "final_real_rgbd_open_vocab_robustness_ready": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "repair_m112_conceptgraphs_visit_order_path_smoke",
            "selected_next_unit": "repair E008-M112 ConceptGraphs candidate visit-order/path smoke",
            "reason": "Visit-order/path rows are incomplete or leakage audit failed.",
            "launch_long_job_now": False,
            "source_gap_recovery_evaluated": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    query_source_policy_rows: list[dict[str, Any]],
    failure_counts: Counter[str],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_query_rows} | {mean_first_path_ready_rank} | {mean_first_path_ready_cost_m} | "
            "{mean_top5_cumulative_known_path_cost_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    query_lines = []
    for row in query_source_policy_rows:
        query_lines.append(
            "| {scan_id} | {object_category} | {policy_id} | {ranked_candidate_rows} | "
            "{path_ready_ranked_rows} | {first_path_ready_rank} | {first_path_ready_cost_m} | "
            "{top5_path_ready_rows} | {source_boundary_status} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M112 ConceptGraphs HM3D Candidate Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M111 status: `{coverage['m111_status']}`.
- Input candidate rows: {coverage['input_candidate_rows']}.
- Query-compatible candidate rows: {coverage['query_compatible_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']} / {coverage['query_compatible_candidate_rows']}.
- Failure rows retained for policy accounting: {coverage['failure_rows']} ({failure_line}).
- Visit-order rows: {coverage['visit_order_rows']}.
- Query-source policy metric rows: {coverage['query_source_policy_metric_rows']}.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready queries | mean first-ready rank | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Query-Source Policy Rows

| scan_id | category | policy_id | ranked | path-ready | first-ready rank | first-ready cost m | top5 path-ready | boundary |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(query_lines)}

## Claim Boundary

- M112 is a `ConceptGraphs` candidate visit-order/path-cost smoke, not an executed navigation benchmark.
- M112 does not claim source-gap recovery because eval-only goal/viewpoint matching is not run here.
- M112 does not claim real navigation `SR` / `SPL`.
- M112 does not claim final real RGB-D/open-vocabulary robustness.
- M112 does not claim class-name recognition because the current `ConceptGraphs` source class names are generic `item`; it uses CLIP feature/text scores for query ranking.
- Non-path-ready rows remain explicit failure/accounting rows rather than being silently removed.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m111_coverage = read_json(M111_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M111_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    query_source_rows = read_jsonl(M111_ARTIFACT_DIR / "query_source_boundary_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing E008-M111 candidate_navmesh_validation_rows.jsonl")
    if not query_source_rows:
        raise SystemExit("missing E008-M111 query_source_boundary_rows.jsonl")

    query_compatible_rows = [
        row for row in candidate_rows if query_label_compatible(row.get("object_category"), row.get("label_canonical"))
    ]
    rows_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_query[str(row.get("query_uid"))].append(row)

    visit_rows, query_policy_rows, aggregate_rows = build_visit_order_rows(rows_by_query)
    query_source_policy_rows = build_query_source_policy_rows(query_policy_rows, query_source_rows)
    policy_metric_rows = query_policy_rows + aggregate_rows
    failure_rows = build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)
    leakage_audit_rows = build_leakage_audit_rows(visit_rows, query_policy_rows, aggregate_rows)
    leakage_pass = all(row.get("passed") for row in leakage_audit_rows)
    ready = bool(aggregate_rows) and all(row.get("candidate_visit_order_path_smoke_ready") for row in aggregate_rows)
    source_ready = all(row.get("source_ready") for row in query_source_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows)
    route_decision_rows = build_route_decision_rows(ready and source_ready and not uses_eval_policy, leakage_pass)
    claim_boundary_rows = build_claim_boundary_rows()

    coverage = {
        "version": VERSION,
        "status": "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_ready"
        if ready and source_ready and not uses_eval_policy and leakage_pass
        else "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m111_status": m111_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "input_candidate_rows": len(candidate_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "query_rows": len(rows_by_query),
        "source_ready_query_rows": sum(1 for row in query_source_rows if row.get("source_ready")),
        "path_ready_candidate_rows": sum(1 for row in query_compatible_rows if is_path_ready(row)),
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "policy_count": len(POLICIES),
        "visit_order_rows": len(visit_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "query_policy_metric_rows": len(query_policy_rows),
        "query_source_policy_metric_rows": len(query_source_policy_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "leakage_audit_pass": leakage_pass,
        "candidate_visit_order_path_smoke_ready": ready and source_ready and not uses_eval_policy and leakage_pass,
        "source_gap_recovery_evaluated": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "source_class_name_boundary": "generic_item_class_names_clip_text_score_only",
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(ARTIFACT_DIR / "query_policy_metric_rows.jsonl", query_policy_rows)
    write_jsonl(ARTIFACT_DIR / "query_source_policy_metric_rows.jsonl", query_source_policy_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, query_source_policy_rows, failure_counts))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(DATA_OUT_DIR / "query_policy_metric_rows.jsonl", query_policy_rows)
    write_jsonl(DATA_OUT_DIR / "query_source_policy_metric_rows.jsonl", query_source_policy_rows)
    write_jsonl(DATA_OUT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(DATA_OUT_DIR / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_decision_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
