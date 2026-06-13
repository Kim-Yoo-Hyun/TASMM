#!/usr/bin/env python3
"""Materialize E008-M138 confidence-preserving trajectory repair rows."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m138_target_free_confidence_preserving_repair_materialization_smoke_v0"
READY_STATUS = "e008_m138_target_free_confidence_preserving_repair_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m138_target_free_confidence_preserving_repair_materialization_smoke_blocked"
NEXT_UNIT = "E008-M139 target-free confidence-preserving repair trajectory execution contract / Docker preflight"

DEFAULT_M133_ROOT = (
    EXP_ROOT / "artifacts" / "E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
)
DEFAULT_M137_CONTRACT = (
    EXP_ROOT / "artifacts" / "E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0"
)
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0"
)

MATRIX_ID = "candidate_to_candidate_geodesic_matrix_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY = "trajectory_greedy_confidence_only_reachable_v0"
FAILED_REPAIR = "trajectory_greedy_confidence_path_repair_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
SELECTED_POLICY = "confidence_band_trajectory_tiebreak_v0"
HARD_VETO_POLICY = "confidence_preserving_hard_veto_v0"

POLICY_ORDER = [
    SELECTED_POLICY,
    HARD_VETO_POLICY,
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY,
    FAILED_REPAIR,
    PATH_COST_BASELINE,
]

POLICY_ROLES = {
    SELECTED_POLICY: "selected_confidence_preserving_repair",
    HARD_VETO_POLICY: "hard_feasibility_veto_ablation",
    PRIMARY_BASELINE: "protected_detector_confidence_baseline",
    CONFIDENCE_ONLY: "strong_confidence_only_ablation",
    FAILED_REPAIR: "negative_prior_repair_baseline",
    PATH_COST_BASELINE: "negative_source_to_candidate_path_baseline",
}

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "eval_all_viewpoint_count_loaded",
    "eval_geodesic_distance",
    "eval_euclidean_distance",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_first_viewpoint_3d_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m133-root", default=str(DEFAULT_M133_ROOT))
    parser.add_argument("--m137-contract", default=str(DEFAULT_M137_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def adapter_token(adapter_episode_id: str) -> str:
    return adapter_episode_id.replace("::", "__")


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m138::{adapter_token(adapter_episode_id)}::{policy_id}"


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m138::{adapter_token(adapter_episode_id)}"


def start_node_uid(adapter_episode_id: str) -> str:
    return f"episode_start::{adapter_episode_id}"


def candidate_node_uid(row: dict[str, Any]) -> str:
    return f"candidate::{row.get('proposal_uid')}"


def confidence_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    return (
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or 10**9),
        str(row.get("proposal_uid")),
    )


def source_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    return (
        finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or 10**9),
        str(row.get("proposal_uid")),
    )


def matrix_cost(
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    from_uid: str,
    to_uid: str,
) -> tuple[bool, float | None, int, str]:
    row = cost_lookup.get((from_uid, to_uid), {})
    return (
        bool(row.get("path_found")),
        finite_float(row.get("geodesic_distance_m")),
        int(row.get("point_count") or 0),
        str(row.get("path_error") or ""),
    )


def build_cost_lookup(matrix_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("from_node_uid")), str(row.get("to_node_uid"))): row
        for row in matrix_rows
        if row.get("from_node_uid") and row.get("to_node_uid")
    }


def base_candidate_rows(m133_candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in m133_candidate_rows
        if row.get("policy_id") == PRIMARY_BASELINE
        and row.get("path_ready")
        and row.get("candidate_usable_for_path_smoke", True)
        and not row.get("policy_input_uses_eval_goal_or_viewpoint")
        and not row.get("policy_input_uses_success_label")
    ]
    dedup: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=confidence_sort_key):
        clean = dict(row)
        for field in BLOCKED_POLICY_FIELDS:
            clean.pop(field, None)
        dedup.setdefault(str(clean.get("proposal_uid")), clean)
    return list(dedup.values())


def m133_policy_order(m133_candidate_rows: list[dict[str, Any]], policy_id: str) -> list[str]:
    rows = [row for row in m133_candidate_rows if row.get("policy_id") == policy_id]
    rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
    return [str(row.get("proposal_uid")) for row in rows]


def order_from_proposal_ids(base_rows: list[dict[str, Any]], proposal_ids: list[str]) -> list[dict[str, Any]]:
    index = {str(row.get("proposal_uid")): row for row in base_rows}
    ordered = [index[proposal_id] for proposal_id in proposal_ids if proposal_id in index]
    missing = [row for row in base_rows if str(row.get("proposal_uid")) not in set(proposal_ids)]
    return ordered + sorted(missing, key=confidence_sort_key)


def confidence_band_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
    confidence_band_abs: float,
    min_path_advantage_m: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(sorted(candidates, key=confidence_sort_key))
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []
    while remaining:
        detector_top = sorted(remaining, key=confidence_sort_key)[0]
        top_conf = finite_float(detector_top.get("confidence")) or 0.0
        band = [
            row
            for row in sorted(remaining, key=confidence_sort_key)
            if top_conf - (finite_float(row.get("confidence")) or -math.inf) <= confidence_band_abs
        ]
        feasible_band: list[tuple[dict[str, Any], float | None, bool]] = []
        for row in band:
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
            if found and not blocked:
                feasible_band.append((row, cost, row.get("proposal_uid") == detector_top.get("proposal_uid")))
        selected = detector_top
        reason = "detector_confidence_preserved"
        hard_veto = False
        path_advantage = 0.0
        if feasible_band:
            detector_found, detector_cost, _, _ = matrix_cost(
                cost_lookup, current_uid, candidate_node_uid(detector_top)
            )
            best_path_row, best_path_cost, _ = sorted(
                feasible_band,
                key=lambda item: (
                    item[1] if item[1] is not None else math.inf,
                    -(finite_float(item[0].get("confidence")) or -math.inf),
                    int(item[0].get("candidate_rank_m09") or 10**9),
                    str(item[0].get("proposal_uid")),
                ),
            )[0]
            if not detector_found or detector_top.get("blocked_candidate_for_path_policy"):
                selected = best_path_row
                reason = "hard_feasibility_veto_on_detector_top"
                hard_veto = selected.get("proposal_uid") != detector_top.get("proposal_uid")
            elif detector_cost is not None and best_path_cost is not None:
                path_advantage = detector_cost - best_path_cost
                if (
                    best_path_row.get("proposal_uid") != detector_top.get("proposal_uid")
                    and path_advantage >= min_path_advantage_m
                ):
                    selected = best_path_row
                    reason = "within_band_path_tiebreak"
        else:
            feasible_remaining = []
            for row in sorted(remaining, key=confidence_sort_key):
                found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
                blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
                if found and not blocked:
                    feasible_remaining.append((row, cost))
            if feasible_remaining:
                selected, _ = sorted(
                    feasible_remaining,
                    key=lambda item: (
                        -(finite_float(item[0].get("confidence")) or -math.inf),
                        item[1] if item[1] is not None else math.inf,
                        int(item[0].get("candidate_rank_m09") or 10**9),
                        str(item[0].get("proposal_uid")),
                    ),
                )[0]
                reason = "hard_feasibility_veto_on_infeasible_band"
                hard_veto = selected.get("proposal_uid") != detector_top.get("proposal_uid")
        selected_found, selected_cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        audit_events.append(
            {
                "detector_top_proposal_uid": detector_top.get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence": top_conf,
                "selected_confidence": finite_float(selected.get("confidence")),
                "confidence_delta_from_top": top_conf - (finite_float(selected.get("confidence")) or 0.0),
                "selected_current_path_found": selected_found,
                "selected_current_path_cost_m": selected_cost,
                "reason": reason,
                "hard_feasibility_veto_applied": hard_veto,
                "confidence_band_abs": confidence_band_abs,
                "min_path_advantage_m": min_path_advantage_m,
                "path_advantage_m": path_advantage,
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if selected_found:
            current_uid = candidate_node_uid(selected)
    return ordered, audit_events


def hard_veto_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(sorted(candidates, key=confidence_sort_key))
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []
    while remaining:
        detector_top = sorted(remaining, key=confidence_sort_key)[0]
        feasible_remaining = []
        for row in sorted(remaining, key=confidence_sort_key):
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
            if found and not blocked:
                feasible_remaining.append((row, cost))
        selected = detector_top
        reason = "detector_confidence_preserved"
        if feasible_remaining:
            detector_found, _, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(detector_top))
            if not detector_found or detector_top.get("blocked_candidate_for_path_policy"):
                selected = feasible_remaining[0][0]
                reason = "hard_feasibility_veto_on_detector_top"
        found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        audit_events.append(
            {
                "detector_top_proposal_uid": detector_top.get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence": finite_float(detector_top.get("confidence")),
                "selected_confidence": finite_float(selected.get("confidence")),
                "confidence_delta_from_top": (finite_float(detector_top.get("confidence")) or 0.0)
                - (finite_float(selected.get("confidence")) or 0.0),
                "selected_current_path_found": found,
                "selected_current_path_cost_m": cost,
                "reason": reason,
                "hard_feasibility_veto_applied": selected.get("proposal_uid") != detector_top.get("proposal_uid"),
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if found:
            current_uid = candidate_node_uid(selected)
    return ordered, audit_events


def materialize_policy_rows(
    policy_id: str,
    ordered_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
    audit_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    benchmark_uid = build_benchmark_uid(adapter_episode_id)
    current_uid = start_node_uid(adapter_episode_id)
    cumulative = 0.0
    event_by_rank = {idx + 1: event for idx, event in enumerate(audit_events or [])}
    out: list[dict[str, Any]] = []
    for rank, source in enumerate(ordered_candidates, start=1):
        to_uid = candidate_node_uid(source)
        found, cost, point_count, path_error = matrix_cost(cost_lookup, current_uid, to_uid)
        if found and cost is not None:
            cumulative += cost
        confidence = finite_float(source.get("confidence")) or 0.0
        source_cost = finite_float(source.get("source_to_candidate_path_cost_m"))
        event = event_by_rank.get(rank, {})
        if policy_id in {PRIMARY_BASELINE, CONFIDENCE_ONLY, HARD_VETO_POLICY}:
            score = confidence
        elif policy_id == PATH_COST_BASELINE:
            score = -1.0 * (source_cost if source_cost is not None else math.inf)
        elif policy_id == SELECTED_POLICY:
            score = confidence
            if event.get("reason") == "within_band_path_tiebreak":
                score += 0.0001
        else:
            score = confidence - (cost if cost is not None else 1e6)
        row = dict(source)
        for field in BLOCKED_POLICY_FIELDS:
            row.pop(field, None)
        row.update(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": benchmark_uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_visit_uid": f"{plan_uid}::{rank:04d}",
                "visit_rank": rank,
                "ranking_score": score,
                "candidate_order_component": policy_id,
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "primary_budget_cap": "full_ranked",
                "trajectory_cost_matrix_id": MATRIX_ID,
                "confidence_preserving_repair_materialized": True,
                "trajectory_repair_materialized": policy_id == FAILED_REPAIR,
                "current_pose_to_candidate_geodesic_m": cost,
                "current_pose_to_candidate_path_found": found,
                "current_pose_to_candidate_path_point_count": point_count,
                "current_pose_to_candidate_path_error": path_error,
                "planned_segment_path_found": found,
                "planned_cumulative_path_cost_m": cumulative,
                "selected_from_remaining_rows": len(ordered_candidates) - rank + 1,
                "path_ready": bool(source.get("path_ready")),
                "candidate_usable_for_path_smoke": bool(source.get("candidate_usable_for_path_smoke", True)),
                "blocked_candidate_for_path_policy": bool(source.get("blocked_candidate_for_path_policy")),
                "confidence_band_reason": event.get("reason") if event else None,
                "hard_feasibility_veto_applied": bool(event.get("hard_feasibility_veto_applied")) if event else False,
                "confidence_delta_from_top": event.get("confidence_delta_from_top") if event else 0.0,
                "confidence_order_override_allowed": bool(
                    event
                    and event.get("reason") in {"within_band_path_tiebreak", "hard_feasibility_veto_on_detector_top"}
                ),
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M138 materializes confidence-preserving visit-order rows only; executed SR/SPL remains blocked until M139.",
            }
        )
        out.append(row)
        if found:
            current_uid = to_uid
    return out


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    plan_rows: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        policy_id = str(first.get("policy_id"))
        path_ready_rows = [row for row in rows if row.get("path_ready")]
        blocked_rows = [row for row in rows if not row.get("path_ready")]
        plan_rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": policy_id,
                "policy_role": first.get("policy_role"),
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE,
                "scan_id": first.get("scan_id"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_budget": len(rows),
                "primary_budget_cap": "full_ranked",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": len(path_ready_rows),
                "blocked_candidate_rows": len(blocked_rows),
                "planned_cumulative_path_cost_m": rows[-1].get("planned_cumulative_path_cost_m"),
                "first_proposal_uid": first.get("proposal_uid"),
                "first_confidence": first.get("confidence"),
                "first_current_pose_to_candidate_geodesic_m": first.get("current_pose_to_candidate_geodesic_m"),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "confidence_preserving_candidate_file": "confidence_preserving_candidate_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m139_target_free_confidence_preserving_repair_trajectory_execution_smoke.py",
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start_position only; goal/viewpoints are metric-only",
                "uses_trajectory_cost_matrix_for_policy": True,
                "uses_task_context_for_decision": False,
                "uses_m127_proxy_success_for_filtering": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M138 fixes confidence-preserving repair trajectory inputs only; final SR/SPL requires M139 execution and scale.",
            }
        )
    return plan_rows


def build_policy_order_audit_rows(
    candidate_rows: list[dict[str, Any]],
    base_candidates: list[dict[str, Any]],
    confidence_band_abs: float,
) -> list[dict[str, Any]]:
    detector_order = [str(row.get("proposal_uid")) for row in sorted(base_candidates, key=confidence_sort_key)]
    detector_rank = {proposal_uid: idx + 1 for idx, proposal_uid in enumerate(detector_order)}
    detector_conf = {
        str(row.get("proposal_uid")): finite_float(row.get("confidence")) or 0.0 for row in base_candidates
    }
    rows: list[dict[str, Any]] = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for policy_id, policy_rows in sorted(by_policy.items()):
        ordered = sorted(policy_rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        outside_band_overrides = 0
        hard_veto_count = 0
        first_rank_flip = None
        for idx, row in enumerate(ordered, start=1):
            proposal_uid = str(row.get("proposal_uid"))
            expected_uid = detector_order[idx - 1] if idx <= len(detector_order) else None
            if expected_uid != proposal_uid and first_rank_flip is None:
                first_rank_flip = {
                    "visit_rank": idx,
                    "expected_detector_proposal_uid": expected_uid,
                    "selected_proposal_uid": proposal_uid,
                }
            stronger_remaining = [
                other_uid
                for other_uid in detector_order
                if detector_rank[other_uid] > idx
                and detector_conf[other_uid] > detector_conf.get(proposal_uid, 0.0) + confidence_band_abs
            ]
            if policy_id == SELECTED_POLICY and stronger_remaining and not row.get("hard_feasibility_veto_applied"):
                outside_band_overrides += 1
            if row.get("hard_feasibility_veto_applied"):
                hard_veto_count += 1
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_order_audit",
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id),
                "candidate_rows": len(ordered),
                "detector_order_identical": [str(row.get("proposal_uid")) for row in ordered] == detector_order,
                "first_rank_flip": first_rank_flip,
                "hard_feasibility_veto_count": hard_veto_count,
                "outside_confidence_band_override_count": outside_band_overrides,
                "confidence_band_violation_count": outside_band_overrides,
                "confidence_band_abs": confidence_band_abs,
                "audit_pass": policy_id != SELECTED_POLICY or outside_band_overrides == 0,
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads = [
        ("confidence_preserving_candidate_rows", candidate_rows),
        ("confidence_preserving_execution_plan_rows", plan_rows),
        ("trajectory_cost_matrix_rows", matrix_rows),
    ]
    out: list[dict[str, Any]] = []
    for payload, rows in payloads:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get(
                "policy_input_uses_eval_goal_or_viewpoint"
            ) or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def build_readiness_gate_rows(
    missing_inputs: list[str],
    base_candidate_count: int,
    matrix_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_candidate_rows = base_candidate_count * len(POLICY_ORDER)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            f"missing={missing_inputs}",
            True,
        ),
        (
            "candidate_universe_preserved",
            base_candidate_count > 0 and len(candidate_rows) == expected_candidate_rows,
            f"base={base_candidate_count}; materialized={len(candidate_rows)}; expected={expected_candidate_rows}",
            True,
        ),
        (
            "same_candidate_count_per_policy",
            set(candidate_counts.values()) == {base_candidate_count} and len(candidate_counts) == len(POLICY_ORDER),
            f"counts={dict(sorted(candidate_counts.items()))}",
            True,
        ),
        (
            "execution_plans_materialized",
            len(plan_rows) == len(POLICY_ORDER),
            f"plan rows={len(plan_rows)}; expected={len(POLICY_ORDER)}",
            True,
        ),
        (
            "trajectory_cost_matrix_reused",
            bool(matrix_rows),
            f"matrix rows={len(matrix_rows)}",
            True,
        ),
        (
            "selected_policy_present",
            SELECTED_POLICY in candidate_counts and PRIMARY_BASELINE in candidate_counts,
            f"selected={SELECTED_POLICY in candidate_counts}; primary_baseline={PRIMARY_BASELINE in candidate_counts}",
            True,
        ),
        (
            "confidence_band_audit_pass",
            all(row.get("audit_pass") for row in audit_rows if row.get("policy_id") == SELECTED_POLICY),
            f"selected violations={sum(int(row.get('confidence_band_violation_count') or 0) for row in audit_rows if row.get('policy_id') == SELECTED_POLICY)}",
            True,
        ),
        (
            "leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in leakage_rows),
            f"failed={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}",
            True,
        ),
        (
            "execute_trajectories_now",
            False,
            "M138 materializes rows only; M139 should handle Docker execution contract/preflight.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m139": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "confidence_preserving_rows_materialized",
            "supported": ready,
            "claim_boundary": "M138 materializes confidence-preserving trajectory repair rows for the target-free case.",
        },
        {
            "version": VERSION,
            "claim_id": "executed_navigation_improvement",
            "supported": False,
            "claim_boundary": "M138 does not execute Habitat trajectories; M139 is required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final real navigation claim still needs execution, scale, heldout transfer, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M138 is target-free and does not change the E006-M08 human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m138_selected_next",
            "decision": "prepare_m139_docker_execution_contract" if ready else "repair_m138_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M138 materialization",
            "launch_long_job_now": False,
            "reason": "M138 has runner-compatible confidence-preserving rows; M139 should preflight Docker execution."
            if ready
            else "One or more materialization gates failed.",
        }
    ]


def build_policy_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for policy_id, policy_rows in sorted(by_policy.items()):
        ordered = sorted(policy_rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = ordered[0]
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": first.get("policy_role"),
                "candidate_rows": len(ordered),
                "path_ready_rows": sum(1 for row in ordered if row.get("path_ready")),
                "first_proposal_uid": first.get("proposal_uid"),
                "first_confidence": first.get("confidence"),
                "first_current_pose_to_candidate_geodesic_m": first.get("current_pose_to_candidate_geodesic_m"),
                "planned_cumulative_path_cost_m": ordered[-1].get("planned_cumulative_path_cost_m"),
                "hard_feasibility_veto_rows": sum(1 for row in ordered if row.get("hard_feasibility_veto_applied")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "M138 policy summary over materialized rows; not executed trajectory evidence.",
            }
        )
    return rows


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M138 Target-Free Confidence-Preserving Repair Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Base candidate rows: {coverage['base_candidate_rows']}.",
            f"- Materialized candidate rows: {coverage['confidence_preserving_candidate_rows']}.",
            f"- Execution plan rows: {coverage['confidence_preserving_execution_plan_rows']}.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['primary_baseline_policy_id']}`.",
            f"- Confidence band abs: {fmt(coverage['confidence_band_abs'])}.",
            f"- Min path advantage: {fmt(coverage['min_path_advantage_m'])}.",
            f"- Selected policy hard-veto rows: {coverage['selected_policy_hard_veto_rows']}.",
            f"- Selected policy confidence-band violations: {coverage['selected_policy_confidence_band_violations']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                summary_rows,
                [
                    "policy_id",
                    "policy_role",
                    "candidate_rows",
                    "first_proposal_uid",
                    "first_confidence",
                    "first_current_pose_to_candidate_geodesic_m",
                    "planned_cumulative_path_cost_m",
                    "hard_feasibility_veto_rows",
                ],
            ),
            "",
            "## Order Audit",
            "",
            markdown_table(
                audit_rows,
                [
                    "policy_id",
                    "detector_order_identical",
                    "hard_feasibility_veto_count",
                    "outside_confidence_band_override_count",
                    "confidence_band_violation_count",
                    "audit_pass",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m139", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M138 supports row materialization only.",
            "- M138 does not execute `Habitat` trajectories or support final real navigation `SR` / `SPL`.",
            "- The selected policy protects detector-confidence ordering except for hard feasibility vetoes and confidence-band tie-breaks.",
            "",
        ]
    )


def copy_aux_files(src_root: Path, dst_root: Path) -> None:
    for filename in [
        "episode_goal_eval_rows.jsonl",
        "oracle_path_rows.jsonl",
        "trajectory_cost_matrix_rows.jsonl",
    ]:
        src = src_root / filename
        if src.exists():
            shutil.copy2(src, dst_root / filename)


def main() -> None:
    args = parse_args()
    m133_root = resolve_path(args.m133_root)
    m137_contract = resolve_path(args.m137_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m133_cov = read_json(m133_root / "coverage.json")
    m137_cov = read_json(m137_contract / "coverage.json")
    m133_candidate_rows = read_jsonl(m133_root / "trajectory_repair_candidate_rows.jsonl")
    matrix_rows = read_jsonl(m133_root / "trajectory_cost_matrix_rows.jsonl")
    policy_contract_rows = read_jsonl(m137_contract / "policy_contract_rows.jsonl")
    band_rows = read_jsonl(m137_contract / "confidence_band_contract_rows.jsonl")

    missing_inputs = [
        str(path)
        for path, rows in [
            (m133_root / "coverage.json", [m133_cov] if m133_cov else []),
            (m137_contract / "coverage.json", [m137_cov] if m137_cov else []),
            (m133_root / "trajectory_repair_candidate_rows.jsonl", m133_candidate_rows),
            (m133_root / "trajectory_cost_matrix_rows.jsonl", matrix_rows),
            (m137_contract / "policy_contract_rows.jsonl", policy_contract_rows),
            (m137_contract / "confidence_band_contract_rows.jsonl", band_rows),
        ]
        if not rows
    ]

    selected_contract = next(
        (row for row in policy_contract_rows if row.get("policy_id") == SELECTED_POLICY),
        {},
    )
    confidence_band_abs = finite_float(selected_contract.get("confidence_band_abs")) or 0.03
    min_path_advantage_m = finite_float(selected_contract.get("min_path_advantage_m")) or 1.0
    base_candidates = base_candidate_rows(m133_candidate_rows)
    if not base_candidates:
        raise SystemExit("no base candidates from M133 detector-confidence baseline")
    adapter_episode_id = str(base_candidates[0].get("adapter_episode_id"))
    cost_lookup = build_cost_lookup(matrix_rows)

    selected_order, selected_events = confidence_band_order(
        base_candidates,
        cost_lookup,
        adapter_episode_id,
        confidence_band_abs,
        min_path_advantage_m,
    )
    hard_veto, hard_veto_events = hard_veto_order(base_candidates, cost_lookup, adapter_episode_id)

    orders: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]] | None]] = {
        SELECTED_POLICY: (selected_order, selected_events),
        HARD_VETO_POLICY: (hard_veto, hard_veto_events),
        PRIMARY_BASELINE: (sorted(base_candidates, key=confidence_sort_key), None),
        CONFIDENCE_ONLY: (sorted(base_candidates, key=confidence_sort_key), None),
        FAILED_REPAIR: (
            order_from_proposal_ids(base_candidates, m133_policy_order(m133_candidate_rows, FAILED_REPAIR)),
            None,
        ),
        PATH_COST_BASELINE: (sorted(base_candidates, key=source_cost_sort_key), None),
    }

    candidate_rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        ordered, events = orders[policy_id]
        candidate_rows.extend(materialize_policy_rows(policy_id, ordered, cost_lookup, adapter_episode_id, events))
    plan_rows = build_plan_rows(candidate_rows)
    summary_rows = build_policy_summary_rows(candidate_rows)
    audit_rows = build_policy_order_audit_rows(candidate_rows, base_candidates, confidence_band_abs)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, matrix_rows)
    gate_rows = build_readiness_gate_rows(
        missing_inputs,
        len(base_candidates),
        matrix_rows,
        candidate_rows,
        plan_rows,
        leakage_rows,
        audit_rows,
    )
    ready = not any(row.get("blocks_m139") for row in gate_rows)
    route_rows = build_route_decision_rows(ready)
    claim_rows = build_claim_boundary_rows(ready)

    selected_audit = next((row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY), {})
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m133_status": m133_cov.get("status"),
        "m137_status": m137_cov.get("status"),
        "base_candidate_rows": len(base_candidates),
        "confidence_preserving_candidate_rows": len(candidate_rows),
        "confidence_preserving_execution_plan_rows": len(plan_rows),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "selected_policy_id": SELECTED_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE,
        "confidence_band_abs": confidence_band_abs,
        "min_path_advantage_m": min_path_advantage_m,
        "selected_policy_hard_veto_rows": selected_audit.get("hard_feasibility_veto_count", 0),
        "selected_policy_confidence_band_violations": selected_audit.get("confidence_band_violation_count", 0),
        "policy_order_audit_pass": all(row.get("audit_pass") for row in audit_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "materialization_ready": ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        output_dir.mkdir(parents=True, exist_ok=True)
        copy_aux_files(m133_root, output_dir)
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "confidence_preserving_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "confidence_preserving_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", summary_rows)
        write_jsonl(output_dir / "policy_order_audit_rows.jsonl", audit_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    (out_root / "report.md").write_text(
        build_report(coverage, summary_rows, audit_rows, gate_rows),
        encoding="utf-8",
    )
    shutil.copy2(out_root / "report.md", derived_out_root / "report.md")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
