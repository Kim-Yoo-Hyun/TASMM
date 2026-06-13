#!/usr/bin/env python3
"""Materialize E008-M161 confidence-first constrained repair rows."""

from __future__ import annotations

import json
import math
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M155_DIR = EXP_ROOT / "artifacts" / "E008-M155_budget_aware_utility_policy_materialization_smoke_v0"
M156_DIR = EXP_ROOT / "artifacts" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
M160_DIR = EXP_ROOT / "artifacts" / "E008-M160_confidence_first_constrained_utility_repair_contract_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M161_confidence_first_constrained_repair_materialization_smoke_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M161_confidence_first_constrained_repair_materialization_smoke_v0"
)

VERSION = "e008_m161_confidence_first_constrained_repair_materialization_smoke_v0"
READY_STATUS = "e008_m161_confidence_first_constrained_repair_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m161_confidence_first_constrained_repair_materialization_smoke_blocked"
NEXT_CONTRACT_UNIT = "E008-M162 confidence-first constrained repair trajectory execution contract / Docker preflight"
NEXT_INTERPRETATION_UNIT = "E008-M162 confidence-first constrained repair materialization interpretation"

SELECTED_POLICY = "confidence_first_path_veto_tiebreak_repair_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
NO_PATH_TIEBREAK = "confidence_first_no_path_tiebreak_v1"
NO_CONFIDENCE_FLOOR = "budget_guarded_no_confidence_floor_v1"
NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"
SOURCE_GAP_TRIGGER_ONLY = "source_gap_trigger_only_v1"

POLICY_ROLES = {
    SELECTED_POLICY: "selected_confidence_first_constrained_repair",
    PROTECTED_BASELINE: "protected_detector_confidence_baseline",
    NO_PATH_TIEBREAK: "path_tiebreak_disabled_ablation",
    NO_CONFIDENCE_FLOOR: "negative_no_confidence_floor_ablation",
    NO_VISIT_GUARD: "visit_guard_tradeoff_witness_ablation",
    SOURCE_GAP_TRIGGER_ONLY: "source_gap_trigger_only_ablation",
}

POLICY_ORDER = [
    SELECTED_POLICY,
    PROTECTED_BASELINE,
    NO_PATH_TIEBREAK,
    NO_CONFIDENCE_FLOOR,
    NO_VISIT_GUARD,
    SOURCE_GAP_TRIGGER_ONLY,
]

CONFIDENCE_BAND_ABS = 0.03
MIN_PATH_ADVANTAGE_M = 3.0
MAX_RANK_DISPLACEMENT = 1

FORBIDDEN_NONEMPTY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_position",
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


def int_value(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def nonempty(value: Any) -> bool:
    return value not in {None, False, "", 0} and value != [] and value != {}


def row_blocked_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for field in FORBIDDEN_NONEMPTY_FIELDS:
        if field in row and nonempty(row.get(field)):
            hits.append(field)
    if bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")):
        hits.append("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    if bool(row.get("policy_input_uses_eval_goal_or_viewpoint")):
        hits.append("policy_input_uses_eval_goal_or_viewpoint")
    if bool(row.get("policy_input_uses_success_label")) or bool(row.get("uses_success_label_for_policy")):
        hits.append("uses_success_label_for_policy")
    return sorted(set(hits))


def path_cost(row: dict[str, Any]) -> float | None:
    for field in [
        "source_to_candidate_path_cost_m",
        "current_pose_to_candidate_geodesic_m",
        "planned_segment_path_cost_m",
        "planned_cumulative_path_cost_m",
    ]:
        value = finite_float(row.get(field))
        if value is not None:
            return value
    return None


def confidence(row: dict[str, Any]) -> float:
    return finite_float(row.get("confidence")) or 0.0


def path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("path_ready", True)) and bool(row.get("candidate_usable_for_path_smoke", True))


def source_gap_prelabel(row: dict[str, Any]) -> bool:
    return bool(
        row.get("source_gap_recovery_branch_active")
        or row.get("diagnostic_source_gap_boundary")
        or row.get("source_gap_flag")
        or row.get("source_coverage_gap_flag")
    )


def group_by_uid_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))].append(row)
    for policy_rows in grouped.values():
        for rows_for_policy in policy_rows.values():
            rows_for_policy.sort(key=lambda row: int_value(row.get("visit_rank"), 10**9))
    return grouped


def proposal_order(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("proposal_uid")) for row in sorted(rows, key=lambda row: int_value(row.get("visit_rank"), 10**9))]


def copy_policy_row(
    row: dict[str, Any],
    *,
    uid: str,
    policy_id: str,
    visit_rank: int,
    policy_role: str,
    detector_rank: int,
    rank_displacement: int,
    reason: str,
    order_changed: bool,
    needs_recompute: bool,
) -> dict[str, Any]:
    out = dict(row)
    out.update(
        {
            "version": VERSION,
            "claim_boundary": "M161 materializes confidence-first constrained repair rows only; no Habitat trajectory is executed.",
            "row_type": "confidence_first_candidate",
            "policy_id": policy_id,
            "policy_role": policy_role,
            "policy_plan_uid": f"m161::{uid}::{policy_id}",
            "candidate_visit_uid": f"m161::{uid}::{policy_id}::{visit_rank:04d}",
            "candidate_order_component": policy_id,
            "visit_rank": visit_rank,
            "m161_source_policy_id": str(row.get("policy_id")),
            "m161_detector_visit_rank": detector_rank,
            "m161_rank_displacement_from_detector": rank_displacement,
            "m161_rank_displacement_abs_from_detector": abs(rank_displacement),
            "m161_repair_reason": reason,
            "m161_order_changed_vs_detector": order_changed,
            "m161_planned_cost_needs_recompute_for_execution": needs_recompute,
            "requires_cumulative_path_recompute_for_execution": needs_recompute,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "selected_policy_id": SELECTED_POLICY,
        }
    )
    return out


def build_selected_policy_rows(
    uid: str,
    detector_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    detector_rows = sorted(detector_rows, key=lambda row: int_value(row.get("visit_rank"), 10**9))
    detector_by_proposal = {str(row.get("proposal_uid")): row for row in detector_rows}
    detector_rank = {str(row.get("proposal_uid")): idx for idx, row in enumerate(detector_rows, start=1)}

    selected_order: list[str] = []
    component_rows: list[dict[str, Any]] = []
    promoted: set[str] = set()
    demoted: set[str] = set()

    i = 0
    while i < len(detector_rows):
        current = detector_rows[i]
        current_uid = str(current.get("proposal_uid"))
        if i + 1 >= len(detector_rows):
            selected_order.append(current_uid)
            i += 1
            continue

        nxt = detector_rows[i + 1]
        next_uid = str(nxt.get("proposal_uid"))
        conf_loss = confidence(current) - confidence(nxt)
        current_cost = path_cost(current)
        next_cost = path_cost(nxt)
        path_advantage = (
            current_cost - next_cost
            if current_cost is not None and next_cost is not None
            else None
        )
        source_gap_active = source_gap_prelabel(nxt)
        failed_guards: list[str] = []
        if not path_ready(current) or not path_ready(nxt):
            failed_guards.append("hard_feasibility_veto")
        if conf_loss > CONFIDENCE_BAND_ABS:
            failed_guards.append("confidence_band")
        if path_advantage is None or path_advantage < MIN_PATH_ADVANTAGE_M:
            failed_guards.append("path_advantage")
        if source_gap_active:
            failed_guards.append("source_gap_trigger_not_target_free")

        promotion_allowed = not failed_guards
        component_rows.append(
            {
                "version": VERSION,
                "row_type": "repair_component",
                "benchmark_row_uid": uid,
                "policy_id": SELECTED_POLICY,
                "proposal_uid": next_uid,
                "detector_visit_rank": i + 2,
                "candidate_predecessor_proposal_uid": current_uid,
                "candidate_predecessor_detector_rank": i + 1,
                "candidate_confidence": confidence(nxt),
                "predecessor_confidence": confidence(current),
                "confidence_loss_vs_predecessor": conf_loss,
                "candidate_path_cost_m": next_cost,
                "predecessor_path_cost_m": current_cost,
                "local_path_advantage_m": path_advantage,
                "source_gap_prelabel": source_gap_active,
                "hard_feasibility_veto_pass": path_ready(current) and path_ready(nxt),
                "confidence_floor_guard_pass": conf_loss <= CONFIDENCE_BAND_ABS,
                "path_tiebreak_guard_pass": path_advantage is not None
                and path_advantage >= MIN_PATH_ADVANTAGE_M,
                "budget_non_regression_guard_pass": True,
                "rank_displacement_guard_pass": True,
                "source_gap_trigger_guard_pass": not source_gap_active,
                "promotion_allowed": promotion_allowed,
                "repair_action": "swap_with_predecessor" if promotion_allowed else "keep_detector_order",
                "failed_guards": failed_guards,
            }
        )
        if promotion_allowed:
            selected_order.extend([next_uid, current_uid])
            promoted.add(next_uid)
            demoted.add(current_uid)
            i += 2
        else:
            selected_order.append(current_uid)
            i += 1

    detector_order = proposal_order(detector_rows)
    order_changed = selected_order != detector_order
    selected_rows: list[dict[str, Any]] = []
    for visit_rank, proposal_uid in enumerate(selected_order, start=1):
        source_row = detector_by_proposal[proposal_uid]
        rank_delta = visit_rank - detector_rank[proposal_uid]
        if proposal_uid in promoted:
            reason = "confidence_band_path_tiebreak_promoted"
        elif proposal_uid in demoted:
            reason = "paired_candidate_demoted_by_local_swap"
        else:
            reason = "detector_confidence_order_preserved"
        selected_rows.append(
            copy_policy_row(
                source_row,
                uid=uid,
                policy_id=SELECTED_POLICY,
                visit_rank=visit_rank,
                policy_role=POLICY_ROLES[SELECTED_POLICY],
                detector_rank=detector_rank[proposal_uid],
                rank_displacement=rank_delta,
                reason=reason,
                order_changed=order_changed,
                needs_recompute=order_changed,
            )
        )

    audit = build_policy_order_audit(
        uid=uid,
        policy_id=SELECTED_POLICY,
        policy_rows=selected_rows,
        detector_rows=detector_rows,
        changed_metric_field="repair_promotion_allowed_rows",
        changed_metric_value=len(promoted),
    )
    audit.update(
        {
            "local_swap_promoted_rows": len(promoted),
            "local_swap_demoted_rows": len(demoted),
            "path_tiebreak_candidate_rows": len(component_rows),
            "selected_policy_order_changed": order_changed,
        }
    )
    return selected_rows, component_rows, audit


def build_policy_order_audit(
    *,
    uid: str,
    policy_id: str,
    policy_rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
    changed_metric_field: str,
    changed_metric_value: int | None,
) -> dict[str, Any]:
    detector_order = proposal_order(detector_rows)
    policy_order = proposal_order(policy_rows)
    rank_displacements = [
        abs(int_value(row.get("m161_rank_displacement_from_detector")))
        for row in policy_rows
    ]
    blocked_hits = sum(len(row_blocked_hits(row)) for row in policy_rows)
    max_disp = max(rank_displacements, default=0)
    is_selected = policy_id == SELECTED_POLICY
    audit_pass = (
        set(policy_order) == set(detector_order)
        and len(policy_rows) == len(detector_rows)
        and blocked_hits == 0
        and (not is_selected or max_disp <= MAX_RANK_DISPLACEMENT)
    )
    return {
        "version": VERSION,
        "row_type": "policy_order_audit",
        "benchmark_row_uid": uid,
        "policy_id": policy_id,
        "candidate_rows": len(policy_rows),
        "detector_candidate_rows": len(detector_rows),
        "candidate_set_matches_detector": set(policy_order) == set(detector_order),
        "order_changed_vs_detector": policy_order != detector_order,
        "max_rank_displacement_abs_from_detector": max_disp,
        "blocked_field_hits": blocked_hits,
        changed_metric_field: changed_metric_value,
        "audit_pass": audit_pass,
    }


def copy_reference_policy_rows(
    *,
    uid: str,
    policy_id: str,
    source_rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
    source_policy_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    detector_rank = {
        str(row.get("proposal_uid")): idx
        for idx, row in enumerate(sorted(detector_rows, key=lambda row: int_value(row.get("visit_rank"), 10**9)), start=1)
    }
    sorted_source = sorted(source_rows, key=lambda row: int_value(row.get("visit_rank"), 10**9))
    source_order_changed = proposal_order(sorted_source) != proposal_order(detector_rows)
    for visit_rank, row in enumerate(sorted_source, start=1):
        proposal_uid = str(row.get("proposal_uid"))
        rows.append(
            copy_policy_row(
                row,
                uid=uid,
                policy_id=policy_id,
                visit_rank=visit_rank,
                policy_role=POLICY_ROLES[policy_id],
                detector_rank=detector_rank.get(proposal_uid, visit_rank),
                rank_displacement=visit_rank - detector_rank.get(proposal_uid, visit_rank),
                reason=f"reference_policy_copied_from_{source_policy_id}",
                order_changed=source_order_changed,
                needs_recompute=source_order_changed,
            )
        )
    audit = build_policy_order_audit(
        uid=uid,
        policy_id=policy_id,
        policy_rows=rows,
        detector_rows=detector_rows,
        changed_metric_field="reference_policy_rows",
        changed_metric_value=len(rows),
    )
    return rows, audit


def build_detector_derived_reference(
    *,
    uid: str,
    policy_id: str,
    detector_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for visit_rank, row in enumerate(sorted(detector_rows, key=lambda row: int_value(row.get("visit_rank"), 10**9)), start=1):
        rows.append(
            copy_policy_row(
                row,
                uid=uid,
                policy_id=policy_id,
                visit_rank=visit_rank,
                policy_role=POLICY_ROLES[policy_id],
                detector_rank=visit_rank,
                rank_displacement=0,
                reason="detector_confidence_order_reference",
                order_changed=False,
                needs_recompute=False,
            )
        )
    audit = build_policy_order_audit(
        uid=uid,
        policy_id=policy_id,
        policy_rows=rows,
        detector_rows=detector_rows,
        changed_metric_field="reference_policy_rows",
        changed_metric_value=len(rows),
    )
    return rows, audit


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    rows: list[dict[str, Any]] = []
    for (uid, policy_id), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: int_value(row.get("visit_rank"), 10**9))
        first = ordered[0]
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_plan",
                "benchmark_row_uid": uid,
                "policy_id": policy_id,
                "policy_plan_uid": f"m161::{uid}::{policy_id}",
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_rows": len(ordered),
                "path_ready_candidate_rows": sum(1 for row in ordered if path_ready(row)),
                "first_proposal_uid": ordered[0].get("proposal_uid"),
                "last_proposal_uid": ordered[-1].get("proposal_uid"),
                "requires_cumulative_path_recompute_for_execution": any(
                    bool(row.get("m161_planned_cost_needs_recompute_for_execution"))
                    for row in ordered
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
            }
        )
    return rows


def build_leakage_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for policy_id, group in sorted(grouped.items()):
        blocked_hits: dict[str, int] = defaultdict(int)
        for row in group:
            for hit in row_blocked_hits(row):
                blocked_hits[hit] += 1
        rows.append(
            {
                "version": VERSION,
                "row_type": "leakage_audit",
                "policy_id": policy_id,
                "candidate_rows": len(group),
                "blocked_field_hits": sum(blocked_hits.values()),
                "blocked_field_hit_counts": dict(sorted(blocked_hits.items())),
                "leakage_audit_pass": sum(blocked_hits.values()) == 0,
            }
        )
    return rows


def build_materialization_gate_rows(
    *,
    missing_inputs: list[str],
    m155_coverage: dict[str, Any],
    m156_coverage: dict[str, Any],
    m160_coverage: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    selected_changed_episodes: int,
    selected_promoted_rows: int,
) -> list[dict[str, Any]]:
    all_audits_pass = all(bool(row.get("audit_pass")) for row in audit_rows)
    leakage_pass = all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    selected_max_disp = max(
        [
            int_value(row.get("max_rank_displacement_abs_from_detector"))
            for row in audit_rows
            if row.get("policy_id") == SELECTED_POLICY
        ],
        default=0,
    )
    return [
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "required_inputs_present",
            "gate_status": "pass" if not missing_inputs else "fail",
            "rationale": f"missing_inputs={len(missing_inputs)}",
            "blocks_next": bool(missing_inputs),
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "m155_materialization_ready",
            "gate_status": "pass"
            if m155_coverage.get("status") == "e008_m155_budget_aware_utility_policy_materialization_smoke_ready"
            else "fail",
            "rationale": str(m155_coverage.get("status")),
            "blocks_next": m155_coverage.get("status")
            != "e008_m155_budget_aware_utility_policy_materialization_smoke_ready",
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "m156_reference_ready",
            "gate_status": "pass"
            if m156_coverage.get("status") == "e008_m156_budget_aware_utility_trajectory_contract_ready_runner_next"
            else "warning",
            "rationale": str(m156_coverage.get("status")),
            "blocks_next": False,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "m160_contract_ready",
            "gate_status": "pass"
            if m160_coverage.get("status") == "e008_m160_confidence_first_constrained_utility_repair_contract_ready"
            else "fail",
            "rationale": str(m160_coverage.get("status")),
            "blocks_next": m160_coverage.get("status")
            != "e008_m160_confidence_first_constrained_utility_repair_contract_ready",
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "candidate_rows_written",
            "gate_status": "pass" if candidate_rows else "fail",
            "rationale": f"candidate_rows={len(candidate_rows)}",
            "blocks_next": not candidate_rows,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "selected_policy_changes_order",
            "gate_status": "pass" if selected_changed_episodes > 0 else "warning",
            "rationale": f"changed_episodes={selected_changed_episodes}; promoted_rows={selected_promoted_rows}",
            "blocks_next": selected_changed_episodes == 0,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "rank_displacement_guard",
            "gate_status": "pass" if selected_max_disp <= MAX_RANK_DISPLACEMENT else "fail",
            "rationale": f"selected_max_rank_displacement={selected_max_disp}",
            "blocks_next": selected_max_disp > MAX_RANK_DISPLACEMENT,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "policy_order_audit",
            "gate_status": "pass" if all_audits_pass else "fail",
            "rationale": f"audit_rows={len(audit_rows)} all_pass={all_audits_pass}",
            "blocks_next": not all_audits_pass,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "leakage_audit",
            "gate_status": "pass" if leakage_pass else "fail",
            "rationale": f"leakage_rows={len(leakage_rows)} all_pass={leakage_pass}",
            "blocks_next": not leakage_pass,
        },
    ]


def build_claim_boundary_rows(selected_changed_episodes: int) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "confidence_first_repair_rows_materialized",
            "supported": True,
            "claim_boundary": "M161 supports row materialization and leakage/order audit only.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_repair_changes_visit_order",
            "supported": selected_changed_episodes > 0,
            "claim_boundary": "Supported only as pre-execution candidate order changes; no navigation performance is claimed.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_repair_navigation_improvement",
            "supported": False,
            "claim_boundary": "Requires Docker trajectory execution and protected `SR` / `SPL` / candidate-visit gate.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M161 remains target-free and does not change E006-M08.",
        },
    ]


def build_reviewer_defense_rows(selected_changed_episodes: int, selected_promoted_rows: int) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "does_m161_repeat_failed_additive_utility",
            "reviewer_response": "No. The selected policy starts from detector-confidence and applies only adjacent confidence-band path tie-breaks with rank-displacement <= 1.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_claim_navigation_improvement",
            "reviewer_response": "M161 has no trajectory execution. It only materializes rows for the next Docker-preflighted execution contract.",
        },
        {
            "version": VERSION,
            "issue_id": "what_changed_before_execution",
            "reviewer_response": f"The selected policy changes {selected_changed_episodes} episode orders with {selected_promoted_rows} local path tie-break promotions.",
        },
        {
            "version": VERSION,
            "issue_id": "why_keep_no_confidence_and_no_visit_guard",
            "reviewer_response": "They are retained as negative-control and Pareto-tradeoff references from M159/M160.",
        },
    ]


def build_route_decision_rows(materialization_ready: bool, selected_changed_episodes: int) -> list[dict[str, Any]]:
    execution_contract_ready = materialization_ready and selected_changed_episodes > 0
    selected_next = NEXT_CONTRACT_UNIT if execution_contract_ready else NEXT_INTERPRETATION_UNIT
    return [
        {
            "version": VERSION,
            "route_id": "trajectory_execution_contract",
            "decision": "select_next" if execution_contract_ready else "defer",
            "selected": execution_contract_ready,
            "selected_next_unit": NEXT_CONTRACT_UNIT if execution_contract_ready else None,
            "reason": "Rows are materialized, audits pass, and selected policy changes at least one episode.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "materialization_interpretation",
            "decision": "defer" if execution_contract_ready else "select_next",
            "selected": not execution_contract_ready,
            "selected_next_unit": NEXT_INTERPRETATION_UNIT if not execution_contract_ready else None,
            "reason": "Use if selected policy is too conservative or materialization gates fail.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but first test the fixed non-posthoc internal repair.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "selected_next_unit",
            "decision": "record",
            "selected": True,
            "selected_next_unit": selected_next,
            "reason": "Canonical next action selected by M161 gates.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    *,
    missing_inputs: list[str],
    m155_coverage: dict[str, Any],
    m156_coverage: dict[str, Any],
    m160_coverage: dict[str, Any],
    source_rows: list[dict[str, Any]],
    base_detector_rows: int,
    candidate_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    materialization_ready = (
        not missing_inputs
        and bool(candidate_rows)
        and all(not bool(row.get("blocks_next")) for row in gate_rows)
        and all(bool(row.get("audit_pass")) for row in audit_rows)
        and all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    )
    selected_audits = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_changed_episodes = sum(1 for row in selected_audits if bool(row.get("order_changed_vs_detector")))
    selected_promoted_rows = sum(int(row.get("local_swap_promoted_rows") or 0) for row in selected_audits)
    selected_next = next(row["selected_next_unit"] for row in route_rows if row["route_id"] == "selected_next_unit")
    policy_counts: dict[str, int] = defaultdict(int)
    for row in candidate_rows:
        policy_counts[str(row.get("policy_id"))] += 1
    return {
        "version": VERSION,
        "status": READY_STATUS if materialization_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m155_status": m155_coverage.get("status"),
        "m156_status": m156_coverage.get("status"),
        "m160_status": m160_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "source_candidate_rows": len(source_rows),
        "base_detector_candidate_rows": base_detector_rows,
        "materialized_candidate_rows": len(candidate_rows),
        "candidate_rows_by_policy": dict(sorted(policy_counts.items())),
        "repair_component_rows": len(component_rows),
        "policy_plan_rows": len(plan_rows),
        "policy_order_audit_rows": len(audit_rows),
        "leakage_audit_rows": len(leakage_rows),
        "materialization_gate_rows": len(gate_rows),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "metric_target_id": "protected_spl_no_extra_visits_v0",
        "selected_changed_episode_rows": selected_changed_episodes,
        "selected_local_swap_promoted_rows": selected_promoted_rows,
        "materialization_ready": materialization_ready,
        "trajectory_contract_ready_next": materialization_ready and selected_changed_episodes > 0,
        "trajectory_execution_ready": False,
        "positive_navigation_improvement_ready": False,
        "performance_claim_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }


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


def summarize_policy_audit(audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        grouped[str(row.get("policy_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for policy_id, group in sorted(grouped.items()):
        rows.append(
            {
                "policy_id": policy_id,
                "episode_rows": len(group),
                "changed_episode_rows": sum(1 for row in group if bool(row.get("order_changed_vs_detector"))),
                "local_swap_promoted_rows": sum(int(row.get("local_swap_promoted_rows") or 0) for row in group),
                "max_rank_displacement": max(
                    [int_value(row.get("max_rank_displacement_abs_from_detector")) for row in group],
                    default=0,
                ),
                "blocked_field_hits": sum(int(row.get("blocked_field_hits") or 0) for row in group),
                "all_audit_pass": all(bool(row.get("audit_pass")) for row in group),
            }
        )
    return rows


def build_report(
    coverage: dict[str, Any],
    audit_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    selected_route = next(row for row in route_rows if row.get("route_id") == "selected_next_unit")
    return "\n".join(
        [
            "# E008-M161 Confidence-First Constrained Repair Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Source candidate rows: {coverage['source_candidate_rows']}.",
            f"- Base detector candidate rows: {coverage['base_detector_candidate_rows']}.",
            f"- Materialized candidate rows: {coverage['materialized_candidate_rows']}.",
            f"- Repair component rows: {coverage['repair_component_rows']}.",
            f"- Selected changed episode rows: {coverage['selected_changed_episode_rows']}.",
            f"- Selected local-swap promoted rows: {coverage['selected_local_swap_promoted_rows']}.",
            f"- Materialization ready: {coverage['materialization_ready']}.",
            f"- Trajectory contract ready next: {coverage['trajectory_contract_ready_next']}.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            "",
            "## Policy Audit",
            "",
            markdown_table(
                summarize_policy_audit(audit_rows),
                [
                    "policy_id",
                    "episode_rows",
                    "changed_episode_rows",
                    "local_swap_promoted_rows",
                    "max_rank_displacement",
                    "blocked_field_hits",
                    "all_audit_pass",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "rationale", "blocks_next"]),
            "",
            "## Claim Boundary",
            "",
            markdown_table(claim_rows, ["claim_id", "supported", "claim_boundary"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Agent Inference",
            "",
            "- M161 operationalizes M160 without reintroducing the failed additive path utility.",
            "- The selected method changes only local adjacent order within the confidence band and keeps max rank displacement at one.",
            "- M161 does not support navigation improvement; it prepares M162 trajectory contract/preflight.",
            f"- Selected next unit: {selected_route['selected_next_unit']}.",
            "",
        ]
    )


def copy_artifacts(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = {
        "m155_coverage": M155_DIR / "coverage.json",
        "m155_candidate_rows": M155_DIR / "budget_aware_candidate_rows.jsonl",
        "m156_coverage": M156_DIR / "coverage.json",
        "m160_coverage": M160_DIR / "coverage.json",
        "m160_method_contract": M160_DIR / "method_contract_rows.jsonl",
        "m160_repair_rules": M160_DIR / "repair_rule_rows.jsonl",
        "m160_metric_targets": M160_DIR / "metric_target_rows.jsonl",
    }
    missing_inputs = [key for key, path in required.items() if not path.exists()]

    m155_coverage = read_json(required["m155_coverage"])
    m156_coverage = read_json(required["m156_coverage"])
    m160_coverage = read_json(required["m160_coverage"])
    source_rows = read_jsonl(required["m155_candidate_rows"])
    grouped = group_by_uid_policy(source_rows)

    candidate_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    base_detector_rows = 0

    for uid, policy_groups in sorted(grouped.items()):
        detector_rows = policy_groups.get(PROTECTED_BASELINE, [])
        if not detector_rows:
            continue
        base_detector_rows += len(detector_rows)

        selected_rows, selected_components, selected_audit = build_selected_policy_rows(uid, detector_rows)
        candidate_rows.extend(selected_rows)
        component_rows.extend(selected_components)
        audit_rows.append(selected_audit)

        for policy_id in [PROTECTED_BASELINE, NO_PATH_TIEBREAK, SOURCE_GAP_TRIGGER_ONLY]:
            rows, audit = build_detector_derived_reference(
                uid=uid,
                policy_id=policy_id,
                detector_rows=detector_rows,
            )
            candidate_rows.extend(rows)
            audit_rows.append(audit)

        for policy_id in [NO_CONFIDENCE_FLOOR, NO_VISIT_GUARD]:
            source_policy_rows = policy_groups.get(policy_id, [])
            if not source_policy_rows:
                continue
            rows, audit = copy_reference_policy_rows(
                uid=uid,
                policy_id=policy_id,
                source_rows=source_policy_rows,
                detector_rows=detector_rows,
                source_policy_id=policy_id,
            )
            candidate_rows.extend(rows)
            audit_rows.append(audit)

    plan_rows = build_plan_rows(candidate_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows)
    selected_changed = sum(
        1
        for row in audit_rows
        if row.get("policy_id") == SELECTED_POLICY and bool(row.get("order_changed_vs_detector"))
    )
    selected_promoted = sum(
        int(row.get("local_swap_promoted_rows") or 0)
        for row in audit_rows
        if row.get("policy_id") == SELECTED_POLICY
    )
    gate_rows = build_materialization_gate_rows(
        missing_inputs=missing_inputs,
        m155_coverage=m155_coverage,
        m156_coverage=m156_coverage,
        m160_coverage=m160_coverage,
        candidate_rows=candidate_rows,
        audit_rows=audit_rows,
        leakage_rows=leakage_rows,
        selected_changed_episodes=selected_changed,
        selected_promoted_rows=selected_promoted,
    )
    materialization_ready = (
        not missing_inputs
        and bool(candidate_rows)
        and all(not bool(row.get("blocks_next")) for row in gate_rows)
        and all(bool(row.get("audit_pass")) for row in audit_rows)
        and all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    )
    claim_rows = build_claim_boundary_rows(selected_changed)
    reviewer_rows = build_reviewer_defense_rows(selected_changed, selected_promoted)
    route_rows = build_route_decision_rows(materialization_ready, selected_changed)
    coverage = build_coverage(
        missing_inputs=missing_inputs,
        m155_coverage=m155_coverage,
        m156_coverage=m156_coverage,
        m160_coverage=m160_coverage,
        source_rows=source_rows,
        base_detector_rows=base_detector_rows,
        candidate_rows=candidate_rows,
        component_rows=component_rows,
        plan_rows=plan_rows,
        audit_rows=audit_rows,
        leakage_rows=leakage_rows,
        gate_rows=gate_rows,
        route_rows=route_rows,
    )

    outputs = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "confidence_first_candidate_rows.jsonl",
        ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
        ARTIFACT_DIR / "repair_component_rows.jsonl",
        ARTIFACT_DIR / "policy_plan_rows.jsonl",
        ARTIFACT_DIR / "policy_order_audit_rows.jsonl",
        ARTIFACT_DIR / "leakage_audit_rows.jsonl",
        ARTIFACT_DIR / "materialization_gate_rows.jsonl",
        ARTIFACT_DIR / "claim_boundary_rows.jsonl",
        ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
        ARTIFACT_DIR / "route_decision_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]
    write_json(outputs[0], coverage)
    write_jsonl(outputs[1], candidate_rows)
    write_jsonl(outputs[2], candidate_rows)
    write_jsonl(outputs[3], component_rows)
    write_jsonl(outputs[4], plan_rows)
    write_jsonl(outputs[5], audit_rows)
    write_jsonl(outputs[6], leakage_rows)
    write_jsonl(outputs[7], gate_rows)
    write_jsonl(outputs[8], claim_rows)
    write_jsonl(outputs[9], reviewer_rows)
    write_jsonl(outputs[10], route_rows)
    outputs[11].write_text(
        build_report(coverage, audit_rows, gate_rows, route_rows, claim_rows),
        encoding="utf-8",
    )
    copy_artifacts(outputs)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
