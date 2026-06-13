#!/usr/bin/env python3
"""Materialize E008-M149 budget-guarded confidence/path rows."""

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

VERSION = "e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
READY_STATUS = "e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_ready"
BLOCKED_STATUS = "e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_blocked"
NEXT_UNIT = "E008-M150 full-val-mini budget-guarded confidence/path trajectory execution contract / Docker preflight"

DEFAULT_M143_ROOT = (
    EXP_ROOT
    / "artifacts"
    / "E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0"
)
DEFAULT_M148_CONTRACT = (
    EXP_ROOT / "artifacts" / "E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0"
)
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
)

SELECTED_POLICY = "budget_guarded_confidence_path_repair_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY = "budget_guarded_confidence_only_v1"
NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR = "budget_guarded_no_confidence_floor_v1"
SOURCE_GAP_ONLY = "budget_guarded_source_gap_only_v1"

SOURCE_M143_SELECTED = "confidence_band_trajectory_tiebreak_v0"
SOURCE_M143_FAILED_REPAIR = "trajectory_greedy_confidence_path_repair_v0"
SOURCE_M143_PATH_COST = "path_cost_ascending_reachable_subset_v0"

POLICY_ORDER = [
    SELECTED_POLICY,
    PROTECTED_BASELINE,
    CONFIDENCE_ONLY,
    NO_VISIT_GUARD,
    NO_CONFIDENCE_FLOOR,
    SOURCE_GAP_ONLY,
]
POLICY_ROLES = {
    SELECTED_POLICY: "selected_budget_guarded_method",
    PROTECTED_BASELINE: "protected_detector_confidence_baseline",
    CONFIDENCE_ONLY: "confidence_floor_ablation",
    NO_VISIT_GUARD: "visit_guard_ablation",
    NO_CONFIDENCE_FLOOR: "negative_path_priority_ablation",
    SOURCE_GAP_ONLY: "source_gap_trigger_ablation",
}

CONFIDENCE_BAND_ABS = 0.03
MAX_RANK_DISPLACEMENT = 1
MIN_LOCAL_PATH_ADVANTAGE_M = 1.0
MATRIX_ID = "full_val_mini_candidate_to_candidate_geodesic_matrix_v0"

METRIC_ONLY_BLOCKED_FIELDS = {
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
    "hit_any_viewpoint_xz_0p5",
    "hit_any_viewpoint_xz_1p0",
    "hit_any_viewpoint_xz_1p5",
    "hit_goal_xz_1p0",
    "hit_goal_xz_1p5",
    "eval_success",
    "success_label",
    "trajectory_success",
    "SR",
    "SPL",
    "StopRank",
    "success_candidate_to_eval_goal_xz_m",
    "success_candidate_to_nearest_eval_viewpoint_xz_m",
    "success_proposal_uid",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
    "uses_objectnav_eval_goal",
    "uses_objectnav_eval_viewpoint",
}
POLICY_FLAG_FIELDS = {
    "uses_objectnav_eval_goal_or_viewpoint_for_policy",
    "policy_input_uses_eval_goal_or_viewpoint",
    "policy_input_uses_success_label",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m143-root", default=str(DEFAULT_M143_ROOT))
    parser.add_argument("--m148-contract", default=str(DEFAULT_M148_CONTRACT))
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


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
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
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def adapter_token(adapter_episode_id: str) -> str:
    return adapter_episode_id.replace("::", "__")


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m149::{adapter_token(adapter_episode_id)}"


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m149::{adapter_token(adapter_episode_id)}::{policy_id}"


def start_node_uid(adapter_episode_id: str) -> str:
    return f"episode_start::{adapter_episode_id}"


def candidate_node_uid(row: dict[str, Any]) -> str:
    return f"candidate::{row.get('proposal_uid')}"


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


def load_cost_lookup(matrix_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("from_node_uid")), str(row.get("to_node_uid"))): row
        for row in matrix_rows
    }


def group_rows_by_policy_episode(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("policy_id")), str(row.get("adapter_episode_id")))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def strip_policy_and_metric_fields(row: dict[str, Any]) -> dict[str, Any]:
    clean = dict(row)
    for field in METRIC_ONLY_BLOCKED_FIELDS:
        clean.pop(field, None)
    for field in [
        "policy_id",
        "policy_role",
        "policy_plan_uid",
        "candidate_visit_uid",
        "visit_rank",
        "ranking_score",
        "candidate_order_component",
        "method_policy",
        "primary_baseline_policy",
        "confidence_band_reason",
        "hard_feasibility_veto_applied",
        "confidence_delta_from_top",
        "confidence_order_override_allowed",
        "confidence_preserving_repair_materialized",
        "trajectory_repair_materialized",
        "planned_cumulative_path_cost_m",
        "current_pose_to_candidate_geodesic_m",
        "current_pose_to_candidate_path_found",
        "current_pose_to_candidate_path_point_count",
        "current_pose_to_candidate_path_error",
        "planned_segment_path_found",
        "selected_from_remaining_rows",
        "claim_boundary",
        "version",
    ]:
        clean.pop(field, None)
    return clean


def build_base_rows(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for (policy_id, adapter_episode_id), rows in grouped.items():
        if policy_id != PROTECTED_BASELINE:
            continue
        detector_rank = {
            str(row.get("proposal_uid")): int(row.get("visit_rank") or idx + 1)
            for idx, row in enumerate(rows)
        }
        episode_rows: list[dict[str, Any]] = []
        for row in rows:
            clean = strip_policy_and_metric_fields(row)
            proposal_uid = str(row.get("proposal_uid"))
            clean.update(
                {
                    "m143_policy_id": row.get("policy_id"),
                    "m143_policy_plan_uid": row.get("policy_plan_uid"),
                    "m143_candidate_visit_uid": row.get("candidate_visit_uid"),
                    "m143_detector_visit_rank": detector_rank[proposal_uid],
                    "m143_detector_candidate_rank": row.get("candidate_rank_m09") or row.get("candidate_rank"),
                    "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
                    "policy_input_uses_eval_goal_or_viewpoint": False,
                    "policy_input_uses_success_label": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                }
            )
            episode_rows.append(clean)
        out[adapter_episode_id] = sorted(episode_rows, key=lambda row: int(row.get("m143_detector_visit_rank") or 10**9))
    return out


def order_from_source_policy(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    base_by_episode: dict[str, list[dict[str, Any]]],
    adapter_episode_id: str,
    source_policy_id: str,
) -> list[dict[str, Any]]:
    base_by_proposal = {
        str(row.get("proposal_uid")): row
        for row in base_by_episode[adapter_episode_id]
    }
    source_rows = grouped.get((source_policy_id, adapter_episode_id), [])
    ordered = [
        base_by_proposal[str(row.get("proposal_uid"))]
        for row in source_rows
        if str(row.get("proposal_uid")) in base_by_proposal
    ]
    if len(ordered) == len(base_by_proposal):
        return ordered
    missing = [
        row
        for row in base_by_episode[adapter_episode_id]
        if str(row.get("proposal_uid")) not in {str(item.get("proposal_uid")) for item in ordered}
    ]
    return ordered + missing


def confidence(row: dict[str, Any]) -> float:
    return finite_float(row.get("confidence")) or 0.0


def build_selected_budget_guarded_order(
    detector_rows: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    ordered: list[dict[str, Any]] = []
    event_by_proposal: dict[str, dict[str, Any]] = {}
    current_uid = start_node_uid(adapter_episode_id)
    i = 0
    while i < len(detector_rows):
        current_row = detector_rows[i]
        current_proposal = str(current_row.get("proposal_uid"))
        next_row = detector_rows[i + 1] if i + 1 < len(detector_rows) else None
        selected_pair_swapped = False
        if next_row is not None:
            next_proposal = str(next_row.get("proposal_uid"))
            current_found, current_cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(current_row))
            next_found, next_cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(next_row))
            conf_delta = confidence(current_row) - confidence(next_row)
            path_advantage = None
            if current_cost is not None and next_cost is not None:
                path_advantage = current_cost - next_cost
            hard_veto = (not current_found) and next_found
            local_repair = (
                current_found
                and next_found
                and path_advantage is not None
                and path_advantage >= MIN_LOCAL_PATH_ADVANTAGE_M
                and conf_delta <= CONFIDENCE_BAND_ABS
            )
            if hard_veto or local_repair:
                trigger_id = "hard_feasibility_veto" if hard_veto else "confidence_ambiguous_local_path_repair"
                event_by_proposal[next_proposal] = {
                    "budget_repair_trigger_id": trigger_id,
                    "budget_repair_reason": "adjacent_candidate_promoted_before_detector_predecessor",
                    "detector_predecessor_proposal_uid": current_proposal,
                    "confidence_delta_from_detector_predecessor": conf_delta,
                    "local_path_advantage_m": path_advantage,
                    "current_node_uid_at_decision": current_uid,
                    "rank_displacement_guard_applies": True,
                    "source_gap_recovery_branch_active": False,
                    "path_repair_applied": True,
                    "hard_feasibility_veto_applied": hard_veto,
                }
                event_by_proposal[current_proposal] = {
                    "budget_repair_trigger_id": f"paired_after_{trigger_id}",
                    "budget_repair_reason": "detector_predecessor_demoted_by_adjacent_budget_guarded_repair",
                    "detector_predecessor_proposal_uid": current_proposal,
                    "confidence_delta_from_detector_predecessor": 0.0,
                    "local_path_advantage_m": path_advantage,
                    "current_node_uid_at_decision": current_uid,
                    "rank_displacement_guard_applies": True,
                    "source_gap_recovery_branch_active": False,
                    "path_repair_applied": True,
                    "hard_feasibility_veto_applied": hard_veto,
                }
                ordered.extend([next_row, current_row])
                next_to_current_found, _, _, _ = matrix_cost(
                    cost_lookup,
                    candidate_node_uid(next_row),
                    candidate_node_uid(current_row),
                )
                current_uid = candidate_node_uid(current_row) if next_to_current_found else candidate_node_uid(next_row)
                selected_pair_swapped = True
                i += 2
        if selected_pair_swapped:
            continue
        event_by_proposal[current_proposal] = {
            "budget_repair_trigger_id": "detector_confidence_preserved",
            "budget_repair_reason": "no_budget_guarded_path_repair_trigger",
            "detector_predecessor_proposal_uid": None,
            "confidence_delta_from_detector_predecessor": 0.0,
            "local_path_advantage_m": None,
            "current_node_uid_at_decision": current_uid,
            "rank_displacement_guard_applies": True,
            "source_gap_recovery_branch_active": False,
            "path_repair_applied": False,
            "hard_feasibility_veto_applied": False,
        }
        ordered.append(current_row)
        found, _, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(current_row))
        if found:
            current_uid = candidate_node_uid(current_row)
        i += 1
    return ordered, event_by_proposal


def policy_order_for_episode(
    policy_id: str,
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    base_by_episode: dict[str, list[dict[str, Any]]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    detector_rows = base_by_episode[adapter_episode_id]
    if policy_id == SELECTED_POLICY:
        return build_selected_budget_guarded_order(detector_rows, cost_lookup, adapter_episode_id)
    if policy_id in {PROTECTED_BASELINE, CONFIDENCE_ONLY, SOURCE_GAP_ONLY}:
        return detector_rows, {
            str(row.get("proposal_uid")): {
                "budget_repair_trigger_id": "source_gap_branch_inactive"
                if policy_id == SOURCE_GAP_ONLY
                else "detector_confidence_preserved",
                "budget_repair_reason": "detector_confidence_order_used",
                "detector_predecessor_proposal_uid": None,
                "confidence_delta_from_detector_predecessor": 0.0,
                "local_path_advantage_m": None,
                "current_node_uid_at_decision": None,
                "rank_displacement_guard_applies": policy_id != PROTECTED_BASELINE,
                "source_gap_recovery_branch_active": False,
                "path_repair_applied": False,
                "hard_feasibility_veto_applied": False,
            }
            for row in detector_rows
        }
    if policy_id == NO_VISIT_GUARD:
        ordered = order_from_source_policy(grouped, base_by_episode, adapter_episode_id, SOURCE_M143_FAILED_REPAIR)
        return ordered, {
            str(row.get("proposal_uid")): {
                "budget_repair_trigger_id": "visit_guard_removed_prior_path_repair_order",
                "budget_repair_reason": "negative_ablation_reuses_M143_trajectory_greedy_repair_order",
                "detector_predecessor_proposal_uid": None,
                "confidence_delta_from_detector_predecessor": None,
                "local_path_advantage_m": None,
                "current_node_uid_at_decision": None,
                "rank_displacement_guard_applies": False,
                "source_gap_recovery_branch_active": False,
                "path_repair_applied": True,
                "hard_feasibility_veto_applied": False,
            }
            for row in ordered
        }
    if policy_id == NO_CONFIDENCE_FLOOR:
        ordered = order_from_source_policy(grouped, base_by_episode, adapter_episode_id, SOURCE_M143_PATH_COST)
        return ordered, {
            str(row.get("proposal_uid")): {
                "budget_repair_trigger_id": "confidence_floor_removed_path_cost_priority",
                "budget_repair_reason": "negative_ablation_reuses_M143_path_cost_first_order",
                "detector_predecessor_proposal_uid": None,
                "confidence_delta_from_detector_predecessor": None,
                "local_path_advantage_m": None,
                "current_node_uid_at_decision": None,
                "rank_displacement_guard_applies": False,
                "source_gap_recovery_branch_active": False,
                "path_repair_applied": True,
                "hard_feasibility_veto_applied": False,
            }
            for row in ordered
        }
    raise ValueError(f"unknown policy_id: {policy_id}")


def materialize_rows_for_order(
    policy_id: str,
    ordered_rows: list[dict[str, Any]],
    events: dict[str, dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> list[dict[str, Any]]:
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    benchmark_uid = build_benchmark_uid(adapter_episode_id)
    detector_rank = {
        str(row.get("proposal_uid")): int(row.get("m143_detector_visit_rank") or idx + 1)
        for idx, row in enumerate(sorted(ordered_rows, key=lambda item: int(item.get("m143_detector_visit_rank") or 10**9)))
    }
    current_uid = start_node_uid(adapter_episode_id)
    cumulative = 0.0
    out: list[dict[str, Any]] = []
    for visit_rank, source in enumerate(ordered_rows, start=1):
        proposal_uid = str(source.get("proposal_uid"))
        found, cost, point_count, path_error = matrix_cost(cost_lookup, current_uid, candidate_node_uid(source))
        if found and cost is not None:
            cumulative += cost
        source_cost = finite_float(source.get("source_to_candidate_path_cost_m"))
        if policy_id == NO_CONFIDENCE_FLOOR:
            ranking_score = -1.0 * (source_cost if source_cost is not None else math.inf)
        elif policy_id == NO_VISIT_GUARD:
            ranking_score = confidence(source) - 0.001 * (cost if cost is not None else 1e6)
        else:
            ranking_score = confidence(source)
        event = events.get(proposal_uid, {})
        rank_displacement = visit_rank - detector_rank.get(proposal_uid, visit_rank)
        row = strip_policy_and_metric_fields(source)
        row.update(
            {
                "version": VERSION,
                "benchmark_row_uid": benchmark_uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "policy_plan_uid": plan_uid,
                "candidate_visit_uid": f"{plan_uid}::{visit_rank:04d}",
                "visit_rank": visit_rank,
                "ranking_score": ranking_score,
                "candidate_order_component": policy_id,
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
                "protected_baseline_policy_id": PROTECTED_BASELINE,
                "source_m143_policy_id": source.get("m143_policy_id"),
                "m143_detector_visit_rank": detector_rank.get(proposal_uid),
                "rank_displacement_from_detector": rank_displacement,
                "rank_displacement_abs_from_detector": abs(rank_displacement),
                "within_rank_displacement_guard": abs(rank_displacement) <= MAX_RANK_DISPLACEMENT,
                "confidence_band_abs": CONFIDENCE_BAND_ABS,
                "max_rank_displacement": MAX_RANK_DISPLACEMENT,
                "min_local_path_advantage_m": MIN_LOCAL_PATH_ADVANTAGE_M,
                "budget_guarded_materialized": True,
                "budget_guard_applied": policy_id in {SELECTED_POLICY, CONFIDENCE_ONLY, SOURCE_GAP_ONLY},
                "visit_budget_guard_active": policy_id in {SELECTED_POLICY, CONFIDENCE_ONLY, SOURCE_GAP_ONLY},
                "confidence_floor_active": policy_id != NO_CONFIDENCE_FLOOR,
                "budget_repair_trigger_id": event.get("budget_repair_trigger_id"),
                "budget_repair_reason": event.get("budget_repair_reason"),
                "path_repair_applied": bool(event.get("path_repair_applied")),
                "source_gap_recovery_branch_active": bool(event.get("source_gap_recovery_branch_active")),
                "hard_feasibility_veto_applied": bool(event.get("hard_feasibility_veto_applied")),
                "confidence_delta_from_detector_predecessor": event.get("confidence_delta_from_detector_predecessor"),
                "local_path_advantage_m": event.get("local_path_advantage_m"),
                "trajectory_cost_matrix_id": MATRIX_ID,
                "uses_trajectory_cost_matrix_for_policy": policy_id
                in {SELECTED_POLICY, NO_VISIT_GUARD, NO_CONFIDENCE_FLOOR},
                "uses_task_context_for_decision": False,
                "current_pose_to_candidate_geodesic_m": cost,
                "current_pose_to_candidate_path_found": found,
                "current_pose_to_candidate_path_point_count": point_count,
                "current_pose_to_candidate_path_error": path_error,
                "planned_segment_path_found": found,
                "planned_cumulative_path_cost_m": cumulative,
                "selected_from_remaining_rows": len(ordered_rows) - visit_rank + 1,
                "policy_input_allowed": True,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "claim_boundary": "M149 materializes budget-guarded rows only; SR/SPL requires M150/M151 trajectory execution.",
            }
        )
        out.append(row)
        if found:
            current_uid = candidate_node_uid(source)
    return out


def build_all_candidate_rows(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    base_by_episode: dict[str, list[dict[str, Any]]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for adapter_episode_id in sorted(base_by_episode):
        for policy_id in POLICY_ORDER:
            ordered, events = policy_order_for_episode(
                policy_id,
                grouped,
                base_by_episode,
                cost_lookup,
                adapter_episode_id,
            )
            out.extend(materialize_rows_for_order(policy_id, ordered, events, cost_lookup, adapter_episode_id))
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
        detector_identical = all(int(row.get("rank_displacement_from_detector") or 0) == 0 for row in rows)
        plan_rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": policy_id,
                "policy_role": first.get("policy_role"),
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
                "protected_baseline_policy_id": PROTECTED_BASELINE,
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
                "detector_order_identical": detector_identical,
                "max_rank_displacement_abs_from_detector": max(
                    int(row.get("rank_displacement_abs_from_detector") or 0) for row in rows
                ),
                "budget_repair_trigger_rows": sum(1 for row in rows if row.get("path_repair_applied")),
                "hard_feasibility_veto_rows": sum(1 for row in rows if row.get("hard_feasibility_veto_applied")),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "budget_guarded_candidate_file": "budget_guarded_candidate_rows.jsonl",
                "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m151_full_val_mini_budget_guarded_confidence_path_execution.py",
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start state from M72/M143 episode_goal_eval_rows; goal/viewpoints are metric-only",
                "uses_trajectory_cost_matrix_for_policy": policy_id
                in {SELECTED_POLICY, NO_VISIT_GUARD, NO_CONFIDENCE_FLOOR},
                "uses_task_context_for_decision": False,
                "uses_m127_proxy_success_for_filtering": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "diagnostic_source_gap_boundary_for_reporting": False,
                "stale_visit_first": False,
                "current_observation_first": True,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "claim_boundary": "M149 fixes budget-guarded full-val-mini trajectory inputs only; final SR/SPL requires trajectory execution.",
            }
        )
    return plan_rows


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join start state"),
        ("scene_key", "scene identity"),
        ("object_category", "query category and label compatibility"),
        ("scene_docker_path", "Habitat scene path"),
        ("navmesh_docker_path", "Habitat navmesh path"),
        ("candidate_position_m", "detector-derived candidate centroid"),
        ("candidate_stop_position_m", "candidate stop on navmesh"),
        ("execution_stop_position_m", "candidate execution stop"),
        ("snapped_position_m", "navmesh-snapped candidate point"),
        ("confidence", "detector confidence score"),
        ("candidate_rank_m09", "detector rank tie-breaker"),
        ("m143_detector_visit_rank", "protected detector visit rank"),
        ("source_to_candidate_path_cost_m", "source-to-candidate path prior"),
        ("current_pose_to_candidate_geodesic_m", "trajectory-aware current-pose geodesic cost"),
        ("trajectory_cost_matrix_id", "cost matrix identifier"),
        ("path_ready", "candidate path usability flag"),
        ("candidate_usable_for_path_smoke", "runner usability flag"),
        ("rank_displacement_from_detector", "budget-guard audit field"),
        ("budget_repair_trigger_id", "precommitted trigger id"),
        ("path_repair_applied", "precommitted repair flag"),
    ]
    rows = [
        {
            "version": VERSION,
            "contract_group": "allowed_policy_input",
            "field": field,
            "allowed_for_policy": True,
            "allowed_for_metric": True,
            "reason": reason,
        }
        for field, reason in allowed
    ]
    rows.extend(
        {
            "version": VERSION,
            "contract_group": "blocked_policy_input",
            "field": field,
            "allowed_for_policy": False,
            "allowed_for_metric": True,
            "reason": "ObjectNav goal/viewpoint, success label, or posthoc metric-only field.",
        }
        for field in sorted(METRIC_ONLY_BLOCKED_FIELDS - {"uses_objectnav_eval_goal", "uses_objectnav_eval_viewpoint"})
    )
    return rows


def build_policy_order_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_plan[str(row.get("policy_plan_uid"))].append(row)
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(by_plan.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        policy_id = str(first.get("policy_id"))
        detector_order_identical = all(int(row.get("rank_displacement_from_detector") or 0) == 0 for row in rows)
        first_rank_flip = None
        for row in rows:
            if int(row.get("rank_displacement_from_detector") or 0) != 0:
                first_rank_flip = {
                    "visit_rank": row.get("visit_rank"),
                    "proposal_uid": row.get("proposal_uid"),
                    "detector_visit_rank": row.get("m143_detector_visit_rank"),
                    "rank_displacement_from_detector": row.get("rank_displacement_from_detector"),
                }
                break
        selected_confidence_band_violations = sum(
            1
            for row in rows
            if policy_id == SELECTED_POLICY
            and row.get("budget_repair_trigger_id") == "confidence_ambiguous_local_path_repair"
            and (
                finite_float(row.get("confidence_delta_from_detector_predecessor")) is None
                or float(row.get("confidence_delta_from_detector_predecessor")) > CONFIDENCE_BAND_ABS
            )
        )
        rank_displacement_violations = sum(
            1
            for row in rows
            if policy_id == SELECTED_POLICY
            and int(row.get("rank_displacement_abs_from_detector") or 0) > MAX_RANK_DISPLACEMENT
        )
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_order_audit",
                "adapter_episode_id": first.get("adapter_episode_id"),
                "policy_plan_uid": plan_uid,
                "policy_id": policy_id,
                "policy_role": first.get("policy_role"),
                "candidate_rows": len(rows),
                "detector_order_identical": detector_order_identical,
                "first_rank_flip": first_rank_flip,
                "max_rank_displacement_abs_from_detector": max(
                    int(row.get("rank_displacement_abs_from_detector") or 0) for row in rows
                ),
                "rank_displacement_violation_count": rank_displacement_violations,
                "confidence_band_violation_count": selected_confidence_band_violations,
                "budget_repair_trigger_rows": sum(1 for row in rows if row.get("path_repair_applied")),
                "hard_feasibility_veto_count": sum(1 for row in rows if row.get("hard_feasibility_veto_applied")),
                "audit_pass": policy_id != SELECTED_POLICY
                or (rank_displacement_violations == 0 and selected_confidence_band_violations == 0),
            }
        )
    return out


def build_budget_guard_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_episode_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_episode_policy[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)
    out: list[dict[str, Any]] = []
    for (adapter_episode_id, policy_id), rows in sorted(by_episode_policy.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        detector_rows = by_episode_policy.get((adapter_episode_id, PROTECTED_BASELINE), [])
        detector_count = len(detector_rows)
        selected_rank_violations = sum(
            1
            for row in rows
            if policy_id == SELECTED_POLICY
            and int(row.get("rank_displacement_abs_from_detector") or 0) > MAX_RANK_DISPLACEMENT
        )
        selected_confidence_violations = sum(
            1
            for row in rows
            if policy_id == SELECTED_POLICY
            and row.get("budget_repair_trigger_id") == "confidence_ambiguous_local_path_repair"
            and (
                finite_float(row.get("confidence_delta_from_detector_predecessor")) is None
                or float(row.get("confidence_delta_from_detector_predecessor")) > CONFIDENCE_BAND_ABS
            )
        )
        planned_delta = len(rows) - detector_count
        guard_applies = policy_id in {SELECTED_POLICY, CONFIDENCE_ONLY, SOURCE_GAP_ONLY}
        out.append(
            {
                "version": VERSION,
                "row_type": "budget_guard_audit",
                "adapter_episode_id": adapter_episode_id,
                "policy_id": policy_id,
                "candidate_rows": len(rows),
                "protected_baseline_candidate_rows": detector_count,
                "planned_candidate_row_delta_vs_detector": planned_delta,
                "max_rank_displacement_abs_from_detector": max(
                    int(row.get("rank_displacement_abs_from_detector") or 0) for row in rows
                ),
                "path_repair_trigger_rows": sum(1 for row in rows if row.get("path_repair_applied")),
                "source_gap_recovery_branch_rows": sum(1 for row in rows if row.get("source_gap_recovery_branch_active")),
                "visit_budget_guard_active": guard_applies,
                "selected_rank_displacement_violation_count": selected_rank_violations,
                "selected_confidence_band_violation_count": selected_confidence_violations,
                "guard_pass": not guard_applies
                or (planned_delta == 0 and selected_rank_violations == 0 and selected_confidence_violations == 0),
            }
        )
    return out


def build_leakage_audit_rows(
    m148_blocked_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked_fields = {
        str(row.get("field"))
        for row in m148_blocked_rows
        if row.get("field") not in POLICY_FLAG_FIELDS
    }
    out: list[dict[str, Any]] = []
    for payload, rows in [
        ("budget_guarded_candidate_rows", candidate_rows),
        ("budget_guarded_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        true_flag_hits = Counter()
        for row in rows:
            for field in blocked_fields:
                if field in row:
                    field_hits[field] += 1
            for field in POLICY_FLAG_FIELDS:
                if row.get(field):
                    true_flag_hits[field] += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_true_policy_flag_hits": dict(sorted(true_flag_hits.items())),
                "blocked_true_policy_flag_hit_count": sum(true_flag_hits.values()),
                "leakage_audit_pass": sum(field_hits.values()) == 0 and sum(true_flag_hits.values()) == 0,
            }
        )
    return out


def build_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for policy_id, policy_rows in sorted(by_policy.items()):
        final_rows = []
        by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in policy_rows:
            by_plan[str(row.get("policy_plan_uid"))].append(row)
        for plan_rows in by_plan.values():
            final_rows.append(max(plan_rows, key=lambda row: int(row.get("visit_rank") or 0)))
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id),
                "episode_rows": len(by_plan),
                "candidate_rows": len(policy_rows),
                "detector_order_identical_rows": sum(
                    1
                    for plan_rows in by_plan.values()
                    if all(int(row.get("rank_displacement_from_detector") or 0) == 0 for row in plan_rows)
                ),
                "path_repair_trigger_rows": sum(1 for row in policy_rows if row.get("path_repair_applied")),
                "hard_feasibility_veto_rows": sum(1 for row in policy_rows if row.get("hard_feasibility_veto_applied")),
                "max_rank_displacement_abs_from_detector": max(
                    int(row.get("rank_displacement_abs_from_detector") or 0) for row in policy_rows
                ),
                "planned_cumulative_path_cost_m_mean": mean(
                    [row.get("planned_cumulative_path_cost_m") for row in final_rows]
                ),
                "claim_boundary": "M149 summary over materialized rows; not executed trajectory evidence.",
            }
        )
    return rows


def build_readiness_gate_rows(
    missing_inputs: list[str],
    m143_cov: dict[str, Any],
    m148_cov: dict[str, Any],
    base_by_episode: dict[str, list[dict[str, Any]]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    order_audit_rows: list[dict[str, Any]],
    budget_audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base_count = sum(len(rows) for rows in base_by_episode.values())
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    expected_candidate_rows = base_count * len(POLICY_ORDER)
    expected_plan_rows = len(base_by_episode) * len(POLICY_ORDER)
    selected_rows = [row for row in candidate_rows if row.get("policy_id") == SELECTED_POLICY]
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            f"missing={missing_inputs}",
            True,
        ),
        (
            "m143_materialization_ready",
            m143_cov.get("status") == "e008_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization_ready",
            f"m143_status={m143_cov.get('status')}",
            True,
        ),
        (
            "m148_contract_ready",
            m148_cov.get("status") == "e008_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract_ready",
            f"m148_status={m148_cov.get('status')}",
            True,
        ),
        (
            "source_ready_denominator_preserved",
            len(base_by_episode) == 30 and base_count == 900,
            f"episodes={len(base_by_episode)}; base_candidates={base_count}; expected=30/900",
            True,
        ),
        (
            "candidate_policy_rows_materialized",
            len(candidate_rows) == expected_candidate_rows,
            f"candidate rows={len(candidate_rows)}; expected={expected_candidate_rows}",
            True,
        ),
        (
            "same_candidate_count_per_policy",
            set(candidate_counts.values()) == {base_count} and set(candidate_counts) == set(POLICY_ORDER),
            f"counts={dict(sorted(candidate_counts.items()))}",
            True,
        ),
        (
            "execution_plans_materialized",
            len(plan_rows) == expected_plan_rows,
            f"plan rows={len(plan_rows)}; expected={expected_plan_rows}",
            True,
        ),
        (
            "selected_policy_budget_guard_pass",
            all(row.get("guard_pass") for row in budget_audit_rows if row.get("policy_id") == SELECTED_POLICY),
            "selected policy planned row delta, confidence band, and rank displacement guards",
            True,
        ),
        (
            "selected_policy_order_audit_pass",
            all(row.get("audit_pass") for row in order_audit_rows if row.get("policy_id") == SELECTED_POLICY),
            f"selected rows={len(selected_rows)}",
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
            "M149 materializes runner-compatible rows only; M150 should preflight Docker execution.",
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
            "blocks_m150": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "budget_guarded_rows_materialized",
            "supported": ready,
            "claim_boundary": "M149 materializes the precommitted M148 budget-guarded policy family over the same full-val-mini denominator.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "principle_driven_policy_form",
            "supported": ready,
            "claim_boundary": "The selected policy keeps detector confidence as the default and allows only local path repair under confidence/rank/visit guards.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "executed_navigation_improvement",
            "supported": False,
            "claim_boundary": "M149 does not execute Habitat trajectories; M150/M151 are required for SR/SPL.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final navigation claim still requires execution, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M149 is target-free and does not change the E006-M08 human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m149_selected_next",
            "decision": "prepare_m150_docker_execution_contract" if ready else "repair_m149_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M149 materialization",
            "launch_long_job_now": False,
            "reason": "M149 has runner-compatible budget-guarded full-val-mini rows; M150 should preflight Docker execution."
            if ready
            else "One or more materialization gates failed.",
        }
    ]


def copy_metric_only_rows(m143_root: Path, out_root: Path, derived_out_root: Path) -> tuple[int, int]:
    episode_rows = read_jsonl(m143_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m143_root / "oracle_path_rows.jsonl")
    for output_dir in (out_root, derived_out_root):
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
    return len(episode_rows), len(oracle_rows)


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M149 Full-Val-Mini Budget-Guarded Confidence/Path Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Episode rows: {coverage['episode_rows']}.",
            f"- Base path-ready candidate rows: {coverage['base_path_ready_candidate_rows']}.",
            f"- Budget-guarded candidate rows: {coverage['budget_guarded_candidate_rows']}.",
            f"- Execution plan rows: {coverage['budget_guarded_execution_plan_rows']}.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Selected policy repair-trigger rows: {coverage['selected_policy_path_repair_trigger_rows']}.",
            f"- Selected policy max rank displacement: {coverage['selected_policy_max_rank_displacement_abs']} "
            f"(limit {coverage['max_rank_displacement']}).",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "candidate_rows",
                    "detector_order_identical_rows",
                    "path_repair_trigger_rows",
                    "max_rank_displacement_abs_from_detector",
                    "planned_cumulative_path_cost_m_mean",
                ],
            ),
            "",
            "## Budget Guard Summary",
            "",
            markdown_table(
                budget_summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "guard_pass_rows",
                    "planned_candidate_row_delta_vs_detector_sum",
                    "max_rank_displacement_abs_from_detector",
                    "path_repair_trigger_rows",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m150", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M149 supports row/materialization readiness only.",
            "- M149 does not execute trajectories or support final real navigation `SR` / `SPL`.",
            "- Positive navigation-improvement remains blocked until the budget-guarded rows are executed and interpreted.",
            "",
        ]
    )


def summarize_budget_guard_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, policy_rows in sorted(by_policy.items()):
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "episode_rows": len(policy_rows),
                "guard_pass_rows": sum(1 for row in policy_rows if row.get("guard_pass")),
                "planned_candidate_row_delta_vs_detector_sum": sum(
                    int(row.get("planned_candidate_row_delta_vs_detector") or 0) for row in policy_rows
                ),
                "max_rank_displacement_abs_from_detector": max(
                    int(row.get("max_rank_displacement_abs_from_detector") or 0) for row in policy_rows
                ),
                "path_repair_trigger_rows": sum(int(row.get("path_repair_trigger_rows") or 0) for row in policy_rows),
            }
        )
    return out


def main() -> None:
    args = parse_args()
    m143_root = resolve_path(args.m143_root)
    m148_contract = resolve_path(args.m148_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m143_cov = read_json(m143_root / "coverage.json")
    m148_cov = read_json(m148_contract / "coverage.json")
    m143_candidate_rows = read_jsonl(m143_root / "confidence_preserving_candidate_rows.jsonl")
    matrix_rows = read_jsonl(m143_root / "trajectory_cost_matrix_rows.jsonl")
    policy_contract_rows = read_jsonl(m148_contract / "policy_contract_rows.jsonl")
    trigger_contract_rows = read_jsonl(m148_contract / "trigger_contract_rows.jsonl")
    m148_allowed_rows = read_jsonl(m148_contract / "allowed_input_rows.jsonl")
    m148_blocked_rows = read_jsonl(m148_contract / "blocked_input_rows.jsonl")
    missing_inputs = [
        str(path.relative_to(ROOT))
        for path, rows in [
            (m143_root / "coverage.json", [m143_cov] if m143_cov else []),
            (m148_contract / "coverage.json", [m148_cov] if m148_cov else []),
            (m143_root / "confidence_preserving_candidate_rows.jsonl", m143_candidate_rows),
            (m143_root / "trajectory_cost_matrix_rows.jsonl", matrix_rows),
            (m148_contract / "policy_contract_rows.jsonl", policy_contract_rows),
            (m148_contract / "trigger_contract_rows.jsonl", trigger_contract_rows),
            (m148_contract / "allowed_input_rows.jsonl", m148_allowed_rows),
            (m148_contract / "blocked_input_rows.jsonl", m148_blocked_rows),
        ]
        if not rows
    ]
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    grouped = group_rows_by_policy_episode(m143_candidate_rows)
    base_by_episode = build_base_rows(grouped)
    cost_lookup = load_cost_lookup(matrix_rows)
    candidate_rows = build_all_candidate_rows(grouped, base_by_episode, cost_lookup)
    plan_rows = build_plan_rows(candidate_rows)
    input_contract_rows = build_input_contract_rows()
    order_audit_rows = build_policy_order_audit_rows(candidate_rows)
    budget_audit_rows = build_budget_guard_audit_rows(candidate_rows)
    leakage_rows = build_leakage_audit_rows(m148_blocked_rows, candidate_rows, plan_rows)
    gate_rows = build_readiness_gate_rows(
        missing_inputs,
        m143_cov,
        m148_cov,
        base_by_episode,
        candidate_rows,
        plan_rows,
        order_audit_rows,
        budget_audit_rows,
        leakage_rows,
    )
    ready = not any(row.get("blocks_m150") for row in gate_rows)
    claim_rows = build_claim_boundary_rows(ready)
    route_rows = build_route_decision_rows(ready)
    summary_rows = build_summary_rows(candidate_rows)
    budget_summary_rows = summarize_budget_guard_rows(budget_audit_rows)
    episode_goal_count, oracle_count = copy_metric_only_rows(m143_root, out_root, derived_out_root)

    base_count = sum(len(rows) for rows in base_by_episode.values())
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    selected_rows = [row for row in candidate_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_order_audits = [row for row in order_audit_rows if row.get("policy_id") == SELECTED_POLICY]
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m143_status": m143_cov.get("status"),
        "m148_status": m148_cov.get("status"),
        "episode_rows": len(base_by_episode),
        "scene_count": len({str(row.get("scene_key")) for rows in base_by_episode.values() for row in rows}),
        "category_count": len({str(row.get("object_category")) for rows in base_by_episode.values() for row in rows}),
        "base_path_ready_candidate_rows": base_count,
        "m143_candidate_rows": len(m143_candidate_rows),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "budget_guarded_candidate_rows": len(candidate_rows),
        "budget_guarded_execution_plan_rows": len(plan_rows),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "policy_ids": POLICY_ORDER,
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "policy_contract_rows": len(policy_contract_rows),
        "trigger_contract_rows": len(trigger_contract_rows),
        "m148_allowed_input_rows": len(m148_allowed_rows),
        "m148_blocked_input_rows": len(m148_blocked_rows),
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "max_rank_displacement": MAX_RANK_DISPLACEMENT,
        "min_local_path_advantage_m": MIN_LOCAL_PATH_ADVANTAGE_M,
        "selected_policy_rows": len(selected_rows),
        "selected_policy_path_repair_trigger_rows": sum(1 for row in selected_rows if row.get("path_repair_applied")),
        "selected_policy_hard_feasibility_veto_rows": sum(
            1 for row in selected_rows if row.get("hard_feasibility_veto_applied")
        ),
        "selected_policy_max_rank_displacement_abs": max(
            [int(row.get("rank_displacement_abs_from_detector") or 0) for row in selected_rows] or [0]
        ),
        "selected_policy_confidence_band_violations": sum(
            int(row.get("confidence_band_violation_count") or 0) for row in selected_order_audits
        ),
        "selected_policy_rank_displacement_violations": sum(
            int(row.get("rank_displacement_violation_count") or 0) for row in selected_order_audits
        ),
        "policy_order_audit_rows": len(order_audit_rows),
        "policy_order_audit_pass": all(row.get("audit_pass") for row in order_audit_rows),
        "budget_guard_audit_rows": len(budget_audit_rows),
        "budget_guard_audit_pass": all(
            row.get("guard_pass") for row in budget_audit_rows if row.get("policy_id") == SELECTED_POLICY
        ),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "episode_goal_eval_rows_copied_for_metric": episode_goal_count,
        "oracle_path_rows_copied_for_metric": oracle_count,
        "runner_alias_candidate_file_ready": True,
        "runner_alias_plan_file_ready": True,
        "materialization_ready": ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "base_candidate_rows.jsonl", [row for rows in base_by_episode.values() for row in rows])
        write_jsonl(output_dir / "trajectory_cost_matrix_rows.jsonl", matrix_rows)
        write_jsonl(output_dir / "budget_guarded_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "budget_guarded_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "m148_policy_contract_rows.jsonl", policy_contract_rows)
        write_jsonl(output_dir / "m148_trigger_contract_rows.jsonl", trigger_contract_rows)
        write_jsonl(output_dir / "policy_order_audit_rows.jsonl", order_audit_rows)
        write_jsonl(output_dir / "budget_guard_audit_rows.jsonl", budget_audit_rows)
        write_jsonl(output_dir / "budget_guard_audit_summary_rows.jsonl", budget_summary_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", summary_rows)
    (out_root / "report.md").write_text(
        build_report(coverage, summary_rows, gate_rows, budget_summary_rows),
        encoding="utf-8",
    )
    shutil.copy2(out_root / "report.md", derived_out_root / "report.md")

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
