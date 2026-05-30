#!/usr/bin/env python3
"""Materialize the E008-M34 counterfactual stale-memory overlay rows."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M35_dynamic_stale_overlay_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M35_dynamic_stale_overlay_materialization_smoke_v0"
VERSION = "e008_m35_dynamic_stale_overlay_materialization_smoke_v0"

M17_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M31_DIR = EXP_ROOT / "artifacts" / "E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0"
M34_DIR = EXP_ROOT / "artifacts" / "E008-M34_dynamic_stale_navigation_contract_v0"

SELECTED_ROUTE = "hm3d_counterfactual_stale_overlay_v0"
NEXT_UNIT = "E008-M36 dynamic-stale overlay trajectory execution contract and runner adaptation"

STATIC_POLICY = "static_stale_memory_top1_v0"
FIXED_CURRENT_POLICY = "fixed_topk_current_observation_v0"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
TASK_AGNOSTIC_POLICY = "task_agnostic_memory_trust_navigation_v0"
H001_POLICY = "h001_task_conditioned_memory_trust_navigation_v0"
ORACLE_POLICY = "oracle_current_target_upper_bound_v0"

MATERIALIZED_POLICIES = [
    STATIC_POLICY,
    FIXED_CURRENT_POLICY,
    DETECTOR_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]

POLICY_ROLES = {
    STATIC_POLICY: "naive_stale_memory",
    FIXED_CURRENT_POLICY: "naive_current_observation",
    DETECTOR_POLICY: "required_navigation_baseline",
    TASK_AGNOSTIC_POLICY: "ablation",
    H001_POLICY: "test_method",
}

BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "m32_trajectory_success",
    "m33_source_gap_label",
    "detector_success_delta",
    "primary_eval_hit",
    "trajectory_success",
    "success_proposal_uid",
    "success_source_role",
}


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def policy_plan_uid(intervention: dict[str, Any], policy_id: str) -> str:
    return (
        f"m35::{intervention.get('adapter_episode_id')}::"
        f"{intervention.get('task_context_id')}::{policy_id}"
    )


def source_plan_uid(intervention: dict[str, Any]) -> str:
    row_uid = str(intervention.get("benchmark_row_uid") or "")
    return row_uid.removeprefix("m34::")


def detector_sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
    path_ready = bool(row.get("path_ready")) or bool(row.get("candidate_usable_for_path_smoke"))
    score = finite_float(row.get("selection_score")) or finite_float(row.get("confidence")) or -1.0
    cost = finite_float(row.get("source_to_snapped_geodesic_m"))
    if cost is None:
        cost = float("inf")
    return (0 if path_ready else 1, -score, cost, str(row.get("proposal_uid")))


def h001_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    rank = int(row.get("visit_rank") or row.get("original_visit_rank") or 10**9)
    return (rank, str(row.get("proposal_uid")))


def index_h001_candidates(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get("policy_plan_uid"))].append(row)
    return {key: sorted(value, key=h001_sort_key) for key, value in out.items()}


def index_current_candidates(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("policy_input_allowed") is False:
            continue
        key = (str(row.get("adapter_episode_id")), str(row.get("object_category")))
        out[key].append(row)
    return {key: sorted(value, key=detector_sort_key) for key, value in out.items()}


def stale_rows_for_plan(h001_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stale = [row for row in h001_rows if row.get("source_role") == "initial_memory_proxy"]
    return sorted(stale, key=h001_sort_key)[:1]


def current_rows_for_plan(h001_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = [row for row in h001_rows if row.get("source_role") == "current_observation"]
    return sorted(current, key=h001_sort_key)


def materialize_from_h001_row(
    row: dict[str, Any],
    intervention: dict[str, Any],
    policy_id: str,
    visit_rank: int,
    role: str,
    component: str,
) -> dict[str, Any]:
    plan_uid = policy_plan_uid(intervention, policy_id)
    stop = row.get("execution_stop_position_m") or row.get("candidate_stop_position_m") or row.get("snapped_position_m")
    path_ready = bool(row.get("path_ready")) and row.get("policy_input_allowed", True) is not False
    return {
        "version": VERSION,
        "selected_route": SELECTED_ROUTE,
        "benchmark_row_uid": intervention.get("benchmark_row_uid"),
        "m34_source_policy_plan_uid": source_plan_uid(intervention),
        "overlay_policy_plan_uid": plan_uid,
        "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
        "policy_id": policy_id,
        "policy_role": POLICY_ROLES[policy_id],
        "adapter_episode_id": intervention.get("adapter_episode_id"),
        "scan_id": intervention.get("scan_id"),
        "scene_key": intervention.get("scene_key"),
        "object_category": intervention.get("object_category"),
        "task_context_id": intervention.get("task_context_id"),
        "visit_rank": visit_rank,
        "candidate_source_role": role,
        "dynamic_stale_overlay_role": "stale_old_memory_overlay" if role == "stale_old_memory" else "current_evidence",
        "candidate_order_component": component,
        "proposal_uid": row.get("proposal_uid"),
        "raw_candidate_uid": row.get("raw_candidate_uid"),
        "frame_id": row.get("frame_id"),
        "label_canonical": row.get("label_canonical"),
        "candidate_position_m": row.get("candidate_position_m"),
        "candidate_stop_position_m": stop,
        "execution_stop_position_m": stop,
        "snapped_position_m": row.get("snapped_position_m") or stop,
        "source_position_m": row.get("source_position") or row.get("candidate_source_position_m"),
        "scene_docker_path": row.get("scene_docker_path"),
        "navmesh_docker_path": row.get("navmesh_docker_path"),
        "path_ready": path_ready,
        "candidate_usable_for_path_smoke": bool(row.get("candidate_usable_for_path_smoke", path_ready)),
        "navmesh_validation_status": row.get("navmesh_validation_status"),
        "ranking_score": finite_float(row.get("selection_score")) or finite_float(row.get("confidence")),
        "confidence": finite_float(row.get("confidence")),
        "source_to_candidate_path_cost_m": finite_float(row.get("source_to_candidate_path_cost_m")),
        "cumulative_known_path_cost_m": finite_float(row.get("cumulative_known_path_cost_m")),
        "policy_input_allowed": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "diagnostic_source_gap_boundary": bool(intervention.get("source_gap_boundary")),
        "diagnostic_not_policy_input": True,
        "claim_boundary": "M35 materialized policy input row; eval goal/viewpoint and trajectory success labels are excluded.",
    }


def materialize_from_detector_row(
    row: dict[str, Any],
    intervention: dict[str, Any],
    policy_id: str,
    visit_rank: int,
    component: str,
) -> dict[str, Any]:
    plan_uid = policy_plan_uid(intervention, policy_id)
    stop = row.get("snapped_position_m")
    path_ready = bool(row.get("candidate_usable_for_path_smoke")) and bool(row.get("source_to_snapped_path_found"))
    return {
        "version": VERSION,
        "selected_route": SELECTED_ROUTE,
        "benchmark_row_uid": intervention.get("benchmark_row_uid"),
        "m34_source_policy_plan_uid": source_plan_uid(intervention),
        "overlay_policy_plan_uid": plan_uid,
        "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
        "policy_id": policy_id,
        "policy_role": POLICY_ROLES[policy_id],
        "adapter_episode_id": intervention.get("adapter_episode_id"),
        "scan_id": intervention.get("scan_id"),
        "scene_key": intervention.get("scene_key"),
        "object_category": intervention.get("object_category"),
        "task_context_id": intervention.get("task_context_id"),
        "visit_rank": visit_rank,
        "candidate_source_role": "current_observation",
        "dynamic_stale_overlay_role": "current_evidence",
        "candidate_order_component": component,
        "proposal_uid": row.get("proposal_uid"),
        "raw_candidate_uid": row.get("raw_candidate_uid"),
        "frame_id": row.get("frame_id"),
        "label_canonical": row.get("label_canonical"),
        "candidate_position_m": row.get("centroid_world_m"),
        "candidate_stop_position_m": stop,
        "execution_stop_position_m": stop,
        "snapped_position_m": stop,
        "source_position_m": row.get("source_position"),
        "scene_docker_path": row.get("scene_docker_path"),
        "navmesh_docker_path": row.get("navmesh_docker_path"),
        "path_ready": path_ready,
        "candidate_usable_for_path_smoke": bool(row.get("candidate_usable_for_path_smoke")),
        "navmesh_validation_status": row.get("navmesh_validation_status"),
        "ranking_score": finite_float(row.get("selection_score")) or finite_float(row.get("confidence")),
        "confidence": finite_float(row.get("confidence")),
        "source_to_candidate_path_cost_m": finite_float(row.get("source_to_snapped_geodesic_m")),
        "cumulative_known_path_cost_m": finite_float(row.get("source_to_snapped_geodesic_m")),
        "policy_input_allowed": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "diagnostic_source_gap_boundary": bool(intervention.get("source_gap_boundary")),
        "diagnostic_not_policy_input": True,
        "claim_boundary": "M35 materialized detector/current-observation input row; eval goal/viewpoint and trajectory success labels are excluded.",
    }


def materialize_policy_rows(
    intervention: dict[str, Any],
    h001_by_plan: dict[str, list[dict[str, Any]]],
    current_by_episode: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    source_uid = source_plan_uid(intervention)
    h001_rows = h001_by_plan.get(source_uid, [])
    stale = stale_rows_for_plan(h001_rows)
    h001_current = current_rows_for_plan(h001_rows)
    current_key = (str(intervention.get("adapter_episode_id")), str(intervention.get("object_category")))
    detector_current = [
        row for row in current_by_episode.get(current_key, []) if bool(row.get("candidate_usable_for_path_smoke"))
    ]

    rows: list[dict[str, Any]] = []
    if stale:
        rows.append(
            materialize_from_h001_row(
                stale[0],
                intervention,
                STATIC_POLICY,
                1,
                "stale_old_memory",
                "static_stale_memory_top1",
            )
        )

    for rank, row in enumerate(detector_current[:5], start=1):
        rows.append(
            materialize_from_detector_row(
                row,
                intervention,
                FIXED_CURRENT_POLICY,
                rank,
                "fixed_top5_current_observation_confidence",
            )
        )

    for rank, row in enumerate(detector_current, start=1):
        rows.append(
            materialize_from_detector_row(
                row,
                intervention,
                DETECTOR_POLICY,
                rank,
                "detector_confidence_reachable_subset",
            )
        )

    agnostic_rows = []
    if stale:
        agnostic_rows.append(
            materialize_from_h001_row(
                stale[0],
                intervention,
                TASK_AGNOSTIC_POLICY,
                1,
                "stale_old_memory",
                "task_agnostic_memory_first",
            )
        )
    for rank, row in enumerate(detector_current[:5], start=len(agnostic_rows) + 1):
        agnostic_rows.append(
            materialize_from_detector_row(
                row,
                intervention,
                TASK_AGNOSTIC_POLICY,
                rank,
                "task_agnostic_current_observation_top5",
            )
        )
    rows.extend(agnostic_rows)

    for rank, row in enumerate(h001_rows, start=1):
        role = "stale_old_memory" if row.get("source_role") == "initial_memory_proxy" else "current_observation"
        rows.append(
            materialize_from_h001_row(
                row,
                intervention,
                H001_POLICY,
                rank,
                role,
                str(row.get("candidate_order_component") or "h001_task_conditioned_order"),
            )
        )
    return rows


def old_location_dead_end_proxy(rows: list[dict[str, Any]]) -> float | None:
    total = 0.0
    seen = False
    for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9)):
        if row.get("candidate_source_role") == "current_observation":
            break
        if row.get("candidate_source_role") == "stale_old_memory":
            seen = True
            value = finite_float(row.get("source_to_candidate_path_cost_m"))
            if value is not None:
                total += value
    return total if seen else 0.0


def build_execution_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("overlay_policy_plan_uid"))].append(row)

    out = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        stale_rows = [row for row in rows if row.get("candidate_source_role") == "stale_old_memory"]
        current_rows = [row for row in rows if row.get("candidate_source_role") == "current_observation"]
        first_current_rank = min([int(row.get("visit_rank") or 10**9) for row in current_rows], default=None)
        stale_before_current = [
            row
            for row in stale_rows
            if first_current_rank is None or int(row.get("visit_rank") or 10**9) < first_current_rank
        ]
        out.append(
            {
                "version": VERSION,
                "selected_route": SELECTED_ROUTE,
                "overlay_policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "m34_source_policy_plan_uid": first.get("m34_source_policy_plan_uid"),
                "policy_id": first.get("policy_id"),
                "policy_role": first.get("policy_role"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": sum(1 for row in rows if row.get("path_ready")),
                "stale_old_memory_candidate_rows": len(stale_rows),
                "current_observation_candidate_rows": len(current_rows),
                "first_candidate_source_role": first.get("candidate_source_role"),
                "stale_visit_first": first.get("candidate_source_role") == "stale_old_memory",
                "current_observation_first": first.get("candidate_source_role") == "current_observation",
                "stale_before_current_rows": len(stale_before_current),
                "old_location_dead_end_cost_proxy_m": old_location_dead_end_proxy(rows),
                "stale_visit_rate_proxy": safe_ratio(len(stale_rows), len(rows)),
                "reobservation_rate_proxy": safe_ratio(len(current_rows), len(rows)),
                "diagnostic_source_gap_boundary": bool(first.get("diagnostic_source_gap_boundary")),
                "diagnostic_not_policy_input": True,
                "runner_input_ready": all(valid_vec3(row.get("execution_stop_position_m")) for row in rows),
                "requires_generalized_runner": True,
                "execution_candidate_file": "dynamic_stale_overlay_policy_candidate_rows.jsonl",
                "termination_rule": "terminate on first eval-only success after a stop or after candidate budget is exhausted",
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "M35 materialized execution plan; no trajectory result is produced.",
            }
        )
    return out


def build_policy_materialization_status_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)

    rows = []
    for policy_id in MATERIALIZED_POLICIES + [ORACLE_POLICY]:
        policy_plans = by_policy.get(policy_id, [])
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "materialized": policy_id in MATERIALIZED_POLICIES,
                "policy_plan_rows": len(policy_plans),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in policy_plans),
                "runner_input_ready_rows": sum(1 for row in policy_plans if row.get("runner_input_ready")),
                "role": POLICY_ROLES.get(policy_id, "upper_bound_not_method"),
                "reason": (
                    "oracle is metric-only and blocked from policy materialization"
                    if policy_id == ORACLE_POLICY
                    else "materialized from M34 intervention contract without eval-goal policy input"
                ),
            }
        )
    return rows


def build_materialization_audit_rows(
    interventions: list[dict[str, Any]],
    h001_by_plan: dict[str, list[dict[str, Any]]],
    current_by_episode: dict[tuple[str, str], list[dict[str, Any]]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_by_benchmark = defaultdict(list)
    for row in plan_rows:
        plan_by_benchmark[str(row.get("benchmark_row_uid"))].append(row)

    out = []
    for intervention in interventions:
        source_uid = source_plan_uid(intervention)
        h001_rows = h001_by_plan.get(source_uid, [])
        current_key = (str(intervention.get("adapter_episode_id")), str(intervention.get("object_category")))
        current_rows = [
            row for row in current_by_episode.get(current_key, []) if bool(row.get("candidate_usable_for_path_smoke"))
        ]
        plans = plan_by_benchmark[str(intervention.get("benchmark_row_uid"))]
        out.append(
            {
                "version": VERSION,
                "benchmark_row_uid": intervention.get("benchmark_row_uid"),
                "adapter_episode_id": intervention.get("adapter_episode_id"),
                "scan_id": intervention.get("scan_id"),
                "object_category": intervention.get("object_category"),
                "task_context_id": intervention.get("task_context_id"),
                "h001_source_plan_uid": source_uid,
                "h001_candidate_rows": len(h001_rows),
                "h001_stale_candidate_rows": sum(1 for row in h001_rows if row.get("source_role") == "initial_memory_proxy"),
                "detector_current_candidate_rows": len(current_rows),
                "materialized_policy_plan_rows": len(plans),
                "all_required_policies_materialized": len(plans) == len(MATERIALIZED_POLICIES),
                "source_gap_boundary": bool(intervention.get("source_gap_boundary")),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "status": "ready" if len(plans) == len(MATERIALIZED_POLICIES) and h001_rows and current_rows else "needs_review",
            }
        )
    return out


def build_policy_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)

    out = []
    for policy_id, rows in sorted(by_policy.items()):
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_plan_rows": len(rows),
                "source_gap_plan_rows": sum(1 for row in rows if row.get("diagnostic_source_gap_boundary")),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in rows]),
                "stale_first_plan_rows": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first_plan_rows": sum(1 for row in rows if row.get("current_observation_first")),
                "mean_old_location_dead_end_cost_proxy_m": mean(
                    [finite_float(row.get("old_location_dead_end_cost_proxy_m")) for row in rows]
                ),
                "mean_stale_visit_rate_proxy": mean([finite_float(row.get("stale_visit_rate_proxy")) for row in rows]),
                "mean_reobservation_rate_proxy": mean([finite_float(row.get("reobservation_rate_proxy")) for row in rows]),
                "runner_input_ready_rows": sum(1 for row in rows if row.get("runner_input_ready")),
                "policy_input_uses_eval_goal_or_viewpoint": any(
                    bool(row.get("policy_input_uses_eval_goal_or_viewpoint")) for row in rows
                ),
                "claim_boundary": "M35 policy summary is pre-execution materialization only.",
            }
        )
    return out


def build_leakage_audit_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for payload_name, payload_rows in [
        ("dynamic_stale_overlay_policy_candidate_rows", candidate_rows),
        ("dynamic_stale_overlay_policy_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        for row in payload_rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        rows.append(
            {
                "version": VERSION,
                "payload": payload_name,
                "row_count": len(payload_rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
                "claim_boundary": "Eval goal/viewpoint and success labels are allowed only in later metric computation, not M35 policy input rows.",
            }
        )
    return rows


def build_readiness_gate_rows(
    m34_cov: dict[str, Any],
    interventions: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    required_policy_plan_rows = len(interventions) * len(MATERIALIZED_POLICIES)
    return [
        {
            "version": VERSION,
            "gate_id": "m34_contract_ready",
            "status": "pass" if m34_cov.get("contract_ready") else "fail",
            "evidence": f"M34 status={m34_cov.get('status')}; selected_route={m34_cov.get('selected_route')}.",
        },
        {
            "version": VERSION,
            "gate_id": "intervention_denominator_preserved",
            "status": "pass" if len(interventions) == 18 else "fail",
            "evidence": f"intervention rows={len(interventions)}.",
        },
        {
            "version": VERSION,
            "gate_id": "required_policy_plans_materialized",
            "status": "pass" if len(plan_rows) == required_policy_plan_rows else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected={required_policy_plan_rows}.",
        },
        {
            "version": VERSION,
            "gate_id": "required_candidate_rows_materialized",
            "status": "pass" if candidate_rows else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "per_intervention_materialization",
            "status": "pass" if all(row.get("status") == "ready" for row in audit_rows) else "fail",
            "evidence": f"ready intervention rows={sum(1 for row in audit_rows if row.get('status') == 'ready')}/{len(audit_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked field hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_execution_after_m35",
            "status": "needs_runner",
            "evidence": "M35 materializes multi-policy rows; the M32 runner is H001-specific and should be generalized before execution.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_overlay_materialized",
            "status": "supported_materialization_only",
            "safe_claim": "M35 materializes a leakage-safe counterfactual stale-memory overlay denominator and policy input rows.",
        },
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_navigation_result",
            "status": "not_ready",
            "safe_claim": "Do not claim dynamic-stale navigation improvement until the materialized rows are executed and evaluated.",
        },
        {
            "version": VERSION,
            "claim_id": "true_temporal_dynamic_navigation",
            "status": "not_ready",
            "safe_claim": "The HM3D overlay is counterfactual; true temporal movement still requires 3RScan/3DSSG navigation execution or an equivalent validated route.",
        },
        {
            "version": VERSION,
            "claim_id": "real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "M35 produces no trajectory SR/SPL result.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m35_selected_next",
            "selected_route": SELECTED_ROUTE,
            "selected_next_unit": NEXT_UNIT,
            "decision": "generalize_trajectory_runner_for_materialized_overlay_rows",
            "reason": "M35 creates multi-policy execution inputs; the next step is a runner contract/adaptation before any trajectory result claim.",
            "launch_long_job_now": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E008-M35 Dynamic-Stale Overlay Materialization Smoke",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected route: `{coverage['selected_route']}`.",
        f"- Intervention rows: {coverage['intervention_rows']}.",
        f"- Materialized policy plan rows: {coverage['policy_execution_plan_rows']}.",
        f"- Materialized candidate rows: {coverage['policy_candidate_rows']}.",
        f"- Required policy ids: {', '.join(coverage['materialized_policy_ids'])}.",
        f"- Source-gap plan rows: {coverage['source_gap_policy_plan_rows']}.",
        f"- Blocked field hits: {coverage['blocked_field_hit_count']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Policy Materialization Summary",
        "",
        "| policy | plans | candidates | stale-first plans | current-first plans | mean old dead-end proxy m |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| `{policy_id}` | {plans} | {candidates} | {stale_first} | {current_first} | {cost:.6f} |".format(
                policy_id=row["policy_id"],
                plans=row["policy_plan_rows"],
                candidates=row["candidate_rows"],
                stale_first=row["stale_first_plan_rows"],
                current_first=row["current_first_plan_rows"],
                cost=row["mean_old_location_dead_end_cost_proxy_m"] or 0.0,
            )
        )
    lines.extend(["", "## Gates", ""])
    for row in gate_rows:
        lines.append(f"- `{row['gate_id']}`: {row['status']} - {row['evidence']}")
    lines.extend(["", "## Claim Boundary", ""])
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}`: {row['status']} - {row['safe_claim']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            f"- {coverage['selected_next_unit']}.",
            "- Do not report M35 as `SR` / `SPL`; it is an input materialization gate.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m34_cov = read_json(M34_DIR / "coverage.json")
    interventions = read_jsonl(M34_DIR / "dynamic_stale_intervention_plan_rows.jsonl")
    m34_policy_contract = read_jsonl(M34_DIR / "policy_baseline_contract_rows.jsonl")
    h001_candidates = read_jsonl(M31_DIR / "h001_fallback_candidate_visit_order_rows.jsonl")
    detector_candidates = read_jsonl(M17_DIR / "candidate_navmesh_rows.jsonl")

    h001_by_plan = index_h001_candidates(h001_candidates)
    current_by_episode = index_current_candidates(detector_candidates)

    candidate_rows: list[dict[str, Any]] = []
    for intervention in sorted(interventions, key=lambda row: str(row.get("benchmark_row_uid"))):
        candidate_rows.extend(materialize_policy_rows(intervention, h001_by_plan, current_by_episode))

    plan_rows = build_execution_plan_rows(candidate_rows)
    materialization_status_rows = build_policy_materialization_status_rows(plan_rows)
    materialization_audit_rows = build_materialization_audit_rows(
        interventions,
        h001_by_plan,
        current_by_episode,
        plan_rows,
    )
    summary_rows = build_policy_summary_rows(plan_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows)
    gate_rows = build_readiness_gate_rows(
        m34_cov,
        interventions,
        candidate_rows,
        plan_rows,
        materialization_audit_rows,
        leakage_rows,
    )
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    policy_candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    policy_plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    source_role_counts = Counter(str(row.get("candidate_source_role")) for row in candidate_rows)
    blocked_field_hit_count = sum(int(row.get("blocked_field_hit_count") or 0) for row in leakage_rows)
    blocked_flag_hit_count = sum(int(row.get("blocked_flag_hit_count") or 0) for row in leakage_rows)
    required_plan_rows = len(interventions) * len(MATERIALIZED_POLICIES)
    ready_interventions = sum(1 for row in materialization_audit_rows if row.get("status") == "ready")

    coverage = {
        "version": VERSION,
        "status": "e008_m35_dynamic_stale_overlay_materialization_smoke_ready_runner_next",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m34_status": m34_cov.get("status"),
        "selected_route": SELECTED_ROUTE,
        "selected_next_unit": NEXT_UNIT,
        "intervention_rows": len(interventions),
        "required_policy_ids": MATERIALIZED_POLICIES,
        "materialized_policy_ids": sorted(policy_plan_counts),
        "m34_policy_contract_rows": len(m34_policy_contract),
        "policy_execution_plan_rows": len(plan_rows),
        "expected_policy_execution_plan_rows": required_plan_rows,
        "policy_candidate_rows": len(candidate_rows),
        "policy_plan_counts": dict(sorted(policy_plan_counts.items())),
        "policy_candidate_counts": dict(sorted(policy_candidate_counts.items())),
        "candidate_source_role_counts": dict(sorted(source_role_counts.items())),
        "source_gap_intervention_rows": sum(1 for row in interventions if row.get("source_gap_boundary")),
        "source_gap_policy_plan_rows": sum(1 for row in plan_rows if row.get("diagnostic_source_gap_boundary")),
        "ready_intervention_rows": ready_interventions,
        "all_interventions_ready": ready_interventions == len(interventions),
        "all_required_policy_plans_materialized": len(plan_rows) == required_plan_rows,
        "all_policy_plan_rows_have_candidates": all(int(row.get("candidate_rows") or 0) > 0 for row in plan_rows),
        "all_candidate_rows_have_execution_stop": all(valid_vec3(row.get("execution_stop_position_m")) for row in candidate_rows),
        "blocked_field_hit_count": blocked_field_hit_count,
        "blocked_flag_hit_count": blocked_flag_hit_count,
        "policy_input_leakage_pass": blocked_field_hit_count == 0 and blocked_flag_hit_count == 0,
        "dynamic_stale_overlay_materialized": True,
        "trajectory_execution_ready": False,
        "generalized_runner_required": True,
        "dynamic_stale_navigation_result_ready": False,
        "true_temporal_dynamic_navigation_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_policy_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_policy_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_status_rows.jsonl", materialization_status_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_audit_rows.jsonl", materialization_audit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_summary_rows.jsonl", summary_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_overlay_policy_candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_overlay_policy_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(DATA_OUT_DIR / "policy_materialization_summary_rows.jsonl", summary_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, summary_rows, gate_rows, claim_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
