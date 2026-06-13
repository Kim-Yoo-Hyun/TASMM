#!/usr/bin/env python3
"""Materialize E008-M154 budget-aware utility policy rows without trajectory execution."""

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
M149_DIR = EXP_ROOT / "artifacts" / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
M154_DIR = EXP_ROOT / "artifacts" / "E008-M154_budget_aware_utility_objective_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M155_budget_aware_utility_policy_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M155_budget_aware_utility_policy_materialization_smoke_v0"

VERSION = "e008_m155_budget_aware_utility_policy_materialization_smoke_v0"
READY_STATUS = "e008_m155_budget_aware_utility_policy_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m155_budget_aware_utility_policy_materialization_smoke_blocked"
NEXT_EXECUTION_CONTRACT = "E008-M156 budget-aware utility trajectory execution contract / Docker preflight"
NEXT_INTERPRETATION = "E008-M156 budget-aware utility materialization result interpretation / objective relaxation decision"

M149_SELECTED_POLICY = "budget_guarded_confidence_path_repair_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR = "budget_guarded_no_confidence_floor_v1"

SELECTED_POLICY = "budget_aware_confidence_path_utility_v0"
WITHOUT_PATH = "budget_aware_utility_without_path_gain_v0"
WITHOUT_VISIT = "budget_aware_utility_without_visit_penalty_v0"
WITHOUT_SOURCE_GAP = "budget_aware_utility_without_source_gap_bonus_v0"

DERIVED_POLICY_CONFIGS = [
    {
        "policy_id": SELECTED_POLICY,
        "policy_role": "selected_budget_aware_method",
        "path_weight": 0.040,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.060,
        "confidence_penalty_weight": 0.040,
        "rank_penalty_weight": 0.030,
    },
    {
        "policy_id": WITHOUT_PATH,
        "policy_role": "path_component_ablation",
        "path_weight": 0.0,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.060,
        "confidence_penalty_weight": 0.040,
        "rank_penalty_weight": 0.030,
    },
    {
        "policy_id": WITHOUT_VISIT,
        "policy_role": "visit_penalty_ablation",
        "path_weight": 0.040,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.0,
        "confidence_penalty_weight": 0.040,
        "rank_penalty_weight": 0.030,
    },
    {
        "policy_id": WITHOUT_SOURCE_GAP,
        "policy_role": "source_gap_component_ablation",
        "path_weight": 0.040,
        "source_gap_weight": 0.0,
        "visit_penalty_weight": 0.060,
        "confidence_penalty_weight": 0.040,
        "rank_penalty_weight": 0.030,
    },
]

REFERENCE_POLICIES = [
    PROTECTED_BASELINE,
    NO_VISIT_GUARD,
    NO_CONFIDENCE_FLOOR,
]

FORBIDDEN_NONEMPTY_FIELDS = {
    "trajectory_success",
    "SPL",
    "SR",
    "StopRank",
    "success_proposal_uid",
    "success_candidate_to_eval_goal_xz_m",
    "success_candidate_to_nearest_eval_viewpoint_xz_m",
    "nearest_eval_viewpoint_distance_m",
    "eval_goal_position",
    "eval_viewpoint_position",
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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def group_by_uid_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))].append(row)
    for policy_rows in grouped.values():
        for rows_for_policy in policy_rows.values():
            rows_for_policy.sort(key=lambda row: int_value(row.get("visit_rank"), 10**9))
    return grouped


def proposal_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("proposal_uid")): row for row in rows}


def nonempty(value: Any) -> bool:
    return value not in {None, False, "", 0} and value != [] and value != {}


def row_blocked_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for field in FORBIDDEN_NONEMPTY_FIELDS:
        if field in row and nonempty(row.get(field)):
            hits.append(field)
    if bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")):
        hits.append("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    if bool(row.get("policy_input_uses_success_label")) or bool(row.get("uses_success_label_for_policy")):
        hits.append("uses_success_label_for_policy")
    return sorted(set(hits))


def compute_components(
    *,
    detector_row: dict[str, Any],
    selected_row: dict[str, Any],
    detector_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rank_displacement = int_value(selected_row.get("rank_displacement_from_detector"), 0)
    rank_displacement_abs = abs(rank_displacement)
    confidence_loss = max(0.0, finite_float(selected_row.get("confidence_delta_from_detector_predecessor")) or 0.0)
    local_path_advantage = max(0.0, finite_float(selected_row.get("local_path_advantage_m")) or 0.0)
    source_gap_prelabel = bool(
        selected_row.get("source_gap_recovery_branch_active")
        or selected_row.get("diagnostic_source_gap_boundary")
        or detector_row.get("source_gap_recovery_branch_active")
        or detector_row.get("diagnostic_source_gap_boundary")
    )
    planned_extra_visit_norm = max(0, len(selected_rows) - len(detector_rows)) / max(1, len(detector_rows))

    method_rank = int_value(selected_row.get("visit_rank"), int_value(detector_row.get("visit_rank"), 1))
    detector_prefix_row = detector_rows[min(max(method_rank - 1, 0), max(len(detector_rows) - 1, 0))]
    detector_prefix_cost = finite_float(detector_prefix_row.get("planned_cumulative_path_cost_m"))
    method_prefix_cost = finite_float(selected_row.get("planned_cumulative_path_cost_m"))
    prefix_path_delta = (
        method_prefix_cost - detector_prefix_cost
        if method_prefix_cost is not None and detector_prefix_cost is not None
        else None
    )

    confidence_guard_pass = confidence_loss <= 0.02 or source_gap_prelabel
    prefix_path_guard_pass = (
        rank_displacement == 0
        or (prefix_path_delta is not None and prefix_path_delta <= -1.0)
        or local_path_advantage >= 3.0
    )
    visit_budget_guard_pass = planned_extra_visit_norm <= 0.0 or source_gap_prelabel
    rank_displacement_guard_pass = rank_displacement_abs <= 1
    source_gap_prelabel_guard_pass = True
    missing_component_fields = [
        field
        for field, value in {
            "confidence_loss": confidence_loss,
            "local_path_advantage_m": local_path_advantage,
            "planned_extra_visit_norm": planned_extra_visit_norm,
            "rank_displacement_abs_from_detector": rank_displacement_abs,
        }.items()
        if value is None
    ]
    return {
        "confidence_loss": confidence_loss,
        "local_path_advantage_m": local_path_advantage,
        "planned_extra_visit_norm": planned_extra_visit_norm,
        "rank_displacement_from_detector": rank_displacement,
        "rank_displacement_abs_from_detector": rank_displacement_abs,
        "source_gap_prelabel": source_gap_prelabel,
        "detector_prefix_cumulative_path_m": detector_prefix_cost,
        "method_prefix_cumulative_path_m": method_prefix_cost,
        "prefix_path_delta_m": prefix_path_delta,
        "confidence_floor_guard_pass": confidence_guard_pass,
        "prefix_path_dominance_guard_pass": prefix_path_guard_pass,
        "visit_budget_guard_strict_pass": visit_budget_guard_pass,
        "source_gap_prelabel_guard_pass": source_gap_prelabel_guard_pass,
        "rank_displacement_guard_pass": rank_displacement_guard_pass,
        "missing_component_fields": missing_component_fields,
        "component_ready": len(missing_component_fields) == 0,
    }


def utility_delta(components: dict[str, Any], config: dict[str, Any]) -> float:
    path_component = float(config["path_weight"]) * clip(float(components["local_path_advantage_m"]) / 10.0, 0.0, 1.0)
    source_gap_component = float(config["source_gap_weight"]) * (1.0 if components["source_gap_prelabel"] else 0.0)
    visit_penalty = float(config["visit_penalty_weight"]) * float(components["planned_extra_visit_norm"])
    confidence_penalty = float(config["confidence_penalty_weight"]) * clip(
        float(components["confidence_loss"]) / 0.03,
        0.0,
        1.0,
    )
    rank_penalty = float(config["rank_penalty_weight"]) * float(components["rank_displacement_abs_from_detector"])
    return path_component + source_gap_component - visit_penalty - confidence_penalty - rank_penalty


def materialize_derived_policy(
    *,
    uid: str,
    config: dict[str, Any],
    detector_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected_by_proposal = proposal_map(selected_rows)
    detector_by_proposal = proposal_map(detector_rows)
    detector_order = [str(row.get("proposal_uid")) for row in detector_rows]
    component_rows: list[dict[str, Any]] = []
    order_entries: list[tuple[float, int, int, str]] = []
    allowed_promotions: set[str] = set()

    for detector_index, detector_row in enumerate(detector_rows, start=1):
        proposal_uid = str(detector_row.get("proposal_uid"))
        selected_row = selected_by_proposal.get(proposal_uid, detector_row)
        components = compute_components(
            detector_row=detector_row,
            selected_row=selected_row,
            detector_rows=detector_rows,
            selected_rows=selected_rows,
        )
        utility = utility_delta(components, config)
        is_promotion_candidate = components["rank_displacement_from_detector"] < 0
        guard_pass = all(
            [
                components["component_ready"],
                components["confidence_floor_guard_pass"],
                components["prefix_path_dominance_guard_pass"],
                components["visit_budget_guard_strict_pass"],
                components["source_gap_prelabel_guard_pass"],
                components["rank_displacement_guard_pass"],
            ]
        )
        promotion_allowed = bool(is_promotion_candidate and guard_pass and utility > 0.0)
        if promotion_allowed:
            allowed_promotions.add(proposal_uid)
        fallback_reason = "promotion_allowed" if promotion_allowed else "detector_confidence_default"
        if is_promotion_candidate and not promotion_allowed:
            failed_guards = [
                key
                for key in [
                    "component_ready",
                    "confidence_floor_guard_pass",
                    "prefix_path_dominance_guard_pass",
                    "visit_budget_guard_strict_pass",
                    "source_gap_prelabel_guard_pass",
                    "rank_displacement_guard_pass",
                ]
                if not components[key]
            ]
            if utility <= 0.0:
                failed_guards.append("utility_delta_not_positive")
            fallback_reason = ",".join(failed_guards) if failed_guards else "promotion_not_candidate"
        sort_key = detector_index + (components["rank_displacement_from_detector"] if promotion_allowed else 0)
        tie_break = 0 if promotion_allowed else 1
        order_entries.append((float(sort_key), tie_break, detector_index, proposal_uid))
        component_rows.append(
            {
                "version": VERSION,
                "row_type": "utility_component",
                "benchmark_row_uid": uid,
                "policy_id": str(config["policy_id"]),
                "proposal_uid": proposal_uid,
                "detector_visit_rank": detector_index,
                "m149_selected_visit_rank": int_value(selected_row.get("visit_rank"), detector_index),
                "utility_delta": utility,
                "utility_promote_candidate": is_promotion_candidate,
                "utility_promotion_allowed": promotion_allowed,
                "utility_fallback_reason": fallback_reason,
                **components,
            }
        )

    ordered_proposals = [proposal_uid for _key, _tie, _detector_index, proposal_uid in sorted(order_entries)]
    policy_rows: list[dict[str, Any]] = []
    for visit_rank, proposal_uid in enumerate(ordered_proposals, start=1):
        detector_row = detector_by_proposal[proposal_uid]
        selected_row = selected_by_proposal.get(proposal_uid, detector_row)
        use_selected_source = proposal_uid in allowed_promotions
        source_row = selected_row if use_selected_source else detector_row
        component = next(row for row in component_rows if row["proposal_uid"] == proposal_uid)
        out = dict(source_row)
        out.update(
            {
                "version": VERSION,
                "claim_boundary": "M155 materializes budget-aware utility rows only; no Habitat trajectory is executed.",
                "policy_id": str(config["policy_id"]),
                "policy_role": str(config["policy_role"]),
                "candidate_order_component": str(config["policy_id"]),
                "policy_plan_uid": f"m155::{uid}::{config['policy_id']}",
                "candidate_visit_uid": f"m155::{uid}::{config['policy_id']}::{visit_rank:04d}",
                "visit_rank": visit_rank,
                "m155_source_policy_id": M149_SELECTED_POLICY if use_selected_source else PROTECTED_BASELINE,
                "m155_detector_visit_rank": component["detector_visit_rank"],
                "m155_utility_delta": component["utility_delta"],
                "m155_utility_promotion_allowed": component["utility_promotion_allowed"],
                "m155_utility_fallback_reason": component["utility_fallback_reason"],
                "m155_planned_cost_needs_recompute_for_execution": ordered_proposals != detector_order,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
            }
        )
        policy_rows.append(out)

    changed_order = ordered_proposals != detector_order
    audit = {
        "version": VERSION,
        "row_type": "policy_order_audit",
        "benchmark_row_uid": uid,
        "policy_id": str(config["policy_id"]),
        "candidate_rows": len(policy_rows),
        "detector_candidate_rows": len(detector_rows),
        "candidate_set_matches_detector": set(ordered_proposals) == set(detector_order),
        "order_changed_vs_detector": changed_order,
        "utility_positive_rows": sum(1 for row in component_rows if finite_float(row.get("utility_delta")) and row["utility_delta"] > 0),
        "utility_promotion_allowed_rows": len(allowed_promotions),
        "promotion_candidate_rows": sum(1 for row in component_rows if row["utility_promote_candidate"]),
        "component_missing_rows": sum(1 for row in component_rows if row["missing_component_fields"]),
        "max_rank_displacement_abs_from_detector": max(
            [int_value(row.get("rank_displacement_abs_from_detector")) for row in component_rows],
            default=0,
        ),
        "blocked_field_hits": sum(len(row_blocked_hits(row)) for row in policy_rows),
        "audit_pass": set(ordered_proposals) == set(detector_order)
        and len(policy_rows) == len(detector_rows)
        and all(len(row_blocked_hits(row)) == 0 for row in policy_rows),
    }
    return policy_rows, component_rows, audit


def copy_reference_policy_rows(
    *,
    uid: str,
    policy_id: str,
    source_rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    detector_order = [str(row.get("proposal_uid")) for row in detector_rows]
    policy_order = [str(row.get("proposal_uid")) for row in source_rows]
    for visit_rank, row in enumerate(source_rows, start=1):
        out = dict(row)
        out.update(
            {
                "version": VERSION,
                "claim_boundary": "M155 carries required reference policy rows forward for later comparison; no Habitat trajectory is executed.",
                "m155_reference_policy": True,
                "m155_source_policy_id": policy_id,
                "policy_plan_uid": f"m155::{uid}::{policy_id}",
                "candidate_visit_uid": f"m155::{uid}::{policy_id}::{visit_rank:04d}",
                "visit_rank": visit_rank,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
            }
        )
        rows.append(out)
    audit = {
        "version": VERSION,
        "row_type": "policy_order_audit",
        "benchmark_row_uid": uid,
        "policy_id": policy_id,
        "candidate_rows": len(rows),
        "detector_candidate_rows": len(detector_rows),
        "candidate_set_matches_detector": set(policy_order) == set(detector_order),
        "order_changed_vs_detector": policy_order != detector_order,
        "utility_positive_rows": None,
        "utility_promotion_allowed_rows": None,
        "promotion_candidate_rows": None,
        "component_missing_rows": 0,
        "max_rank_displacement_abs_from_detector": max(
            [abs(int_value(row.get("rank_displacement_from_detector"))) for row in rows],
            default=0,
        ),
        "blocked_field_hits": sum(len(row_blocked_hits(row)) for row in rows),
        "audit_pass": set(policy_order) == set(detector_order)
        and len(rows) == len(detector_rows)
        and all(len(row_blocked_hits(row)) == 0 for row in rows),
    }
    return rows, audit


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    plan_rows: list[dict[str, Any]] = []
    for (uid, policy_id), rows in sorted(grouped.items()):
        first = rows[0]
        rows_sorted = sorted(rows, key=lambda row: int_value(row.get("visit_rank"), 10**9))
        plan_rows.append(
            {
                "version": VERSION,
                "row_type": "policy_plan",
                "benchmark_row_uid": uid,
                "policy_id": policy_id,
                "policy_plan_uid": f"m155::{uid}::{policy_id}",
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_rows": len(rows_sorted),
                "first_proposal_uid": rows_sorted[0].get("proposal_uid") if rows_sorted else None,
                "last_proposal_uid": rows_sorted[-1].get("proposal_uid") if rows_sorted else None,
                "requires_cumulative_path_recompute_for_execution": any(
                    bool(row.get("m155_planned_cost_needs_recompute_for_execution")) for row in rows_sorted
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
            }
        )
    return plan_rows


def build_leakage_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for policy_id, policy_rows in sorted(grouped.items()):
        blocked_hits: dict[str, int] = defaultdict(int)
        for row in policy_rows:
            for hit in row_blocked_hits(row):
                blocked_hits[hit] += 1
        rows.append(
            {
                "version": VERSION,
                "row_type": "leakage_audit",
                "policy_id": policy_id,
                "candidate_rows": len(policy_rows),
                "blocked_field_hits": sum(blocked_hits.values()),
                "blocked_field_hit_counts": dict(sorted(blocked_hits.items())),
                "leakage_audit_pass": sum(blocked_hits.values()) == 0,
            }
        )
    return rows


def build_materialization_gate_rows(
    *,
    missing_inputs: list[str],
    candidate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    selected_changed_episodes: int,
) -> list[dict[str, Any]]:
    all_audits_pass = all(bool(row.get("audit_pass")) for row in audit_rows)
    leakage_pass = all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    return [
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "required_inputs_present",
            "gate_status": "pass" if not missing_inputs else "fail",
            "rationale": f"missing_inputs={len(missing_inputs)}",
            "blocks_execution": bool(missing_inputs),
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "candidate_rows_written",
            "gate_status": "pass" if candidate_rows else "fail",
            "rationale": f"candidate_rows={len(candidate_rows)}",
            "blocks_execution": not candidate_rows,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "policy_order_audit",
            "gate_status": "pass" if all_audits_pass else "fail",
            "rationale": f"audit_rows={len(audit_rows)} all_pass={all_audits_pass}",
            "blocks_execution": not all_audits_pass,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "leakage_audit",
            "gate_status": "pass" if leakage_pass else "fail",
            "rationale": f"leakage_rows={len(leakage_rows)} all_pass={leakage_pass}",
            "blocks_execution": not leakage_pass,
        },
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": "selected_policy_changes_order",
            "gate_status": "pass" if selected_changed_episodes > 0 else "warning",
            "rationale": f"selected_changed_episodes={selected_changed_episodes}",
            "blocks_execution": selected_changed_episodes == 0,
        },
    ]


def build_claim_boundary_rows(selected_changed_episodes: int) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_aware_policy_materialized",
            "supported": True,
            "claim_boundary": "M155 supports row materialization and leakage audit only.",
        },
        {
            "version": VERSION,
            "claim_id": "budget_aware_policy_navigation_improvement",
            "supported": False,
            "claim_boundary": "Requires Docker trajectory execution and protected-baseline metric gate.",
        },
        {
            "version": VERSION,
            "claim_id": "budget_aware_policy_changes_decisions",
            "supported": selected_changed_episodes > 0,
            "claim_boundary": "Supported only as pre-execution visit-order materialization, not performance.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M155 remains target-free and does not change E006-M08.",
        },
    ]


def build_reviewer_defense_rows(selected_changed_episodes: int) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "does_m155_prove_navigation_improvement",
            "reviewer_response": "No. It only checks that the M154 utility policy can be materialized without eval leakage.",
        },
        {
            "version": VERSION,
            "issue_id": "what_if_selected_order_does_not_change",
            "reviewer_response": "Then the objective is too conservative for this denominator and should be interpreted before any trajectory run.",
        },
        {
            "version": VERSION,
            "issue_id": "why_materialize_references",
            "reviewer_response": "Detector-confidence, no-visit-guard, and no-confidence-floor rows remain required to preserve the M153 reviewer-defense comparisons.",
        },
        {
            "version": VERSION,
            "issue_id": "selected_order_change_status",
            "reviewer_response": f"The selected budget-aware policy changes {selected_changed_episodes} episode orders before execution.",
        },
    ]


def build_route_decision_rows(materialization_ready: bool, selected_changed_episodes: int) -> list[dict[str, Any]]:
    execution_ready = materialization_ready and selected_changed_episodes > 0
    selected_next = NEXT_EXECUTION_CONTRACT if execution_ready else NEXT_INTERPRETATION
    return [
        {
            "version": VERSION,
            "route_id": "trajectory_execution_contract",
            "decision": "select_next" if execution_ready else "defer",
            "selected": execution_ready,
            "selected_next_unit": NEXT_EXECUTION_CONTRACT if execution_ready else None,
            "reason": "Selected utility policy materialized at least one changed episode and passed audits." if execution_ready else "Materialization did not produce a changed selected policy or audits are not ready.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "materialization_result_interpretation",
            "decision": "defer" if execution_ready else "select_next",
            "selected": not execution_ready,
            "selected_next_unit": NEXT_INTERPRETATION if not execution_ready else None,
            "reason": "Use this route if the utility objective is too conservative or materialization gates block execution.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baseline work waits until the internal utility policy has execution evidence or a recorded negative interpretation.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "selected_next_unit",
            "decision": "record",
            "selected": True,
            "selected_next_unit": selected_next,
            "reason": "Canonical next action selected by M155 gates.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    *,
    missing_inputs: list[str],
    source_candidate_rows: list[dict[str, Any]],
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
        and all(bool(row.get("audit_pass")) for row in audit_rows)
        and all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    )
    selected_audits = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_changed_episodes = sum(1 for row in selected_audits if bool(row.get("order_changed_vs_detector")))
    selected_promoted_rows = sum(int(row.get("utility_promotion_allowed_rows") or 0) for row in selected_audits)
    selected_next = next(row["selected_next_unit"] for row in route_rows if row["route_id"] == "selected_next_unit")
    return {
        "version": VERSION,
        "status": READY_STATUS if materialization_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "missing_inputs": missing_inputs,
        "source_candidate_rows": len(source_candidate_rows),
        "materialized_candidate_rows": len(candidate_rows),
        "utility_component_rows": len(component_rows),
        "policy_plan_rows": len(plan_rows),
        "policy_order_audit_rows": len(audit_rows),
        "leakage_audit_rows": len(leakage_rows),
        "materialization_gate_rows": len(gate_rows),
        "materialization_ready": materialization_ready,
        "selected_policy_id": SELECTED_POLICY,
        "selected_changed_episode_rows": selected_changed_episodes,
        "selected_utility_promoted_rows": selected_promoted_rows,
        "trajectory_execution_ready": materialization_ready and selected_changed_episodes > 0,
        "performance_claim_ready": False,
        "selected_next_unit": selected_next,
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        cells: list[str] = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                value = fmt(value)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def summarize_policy_audit(audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        grouped[str(row.get("policy_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for policy_id, policy_rows in sorted(grouped.items()):
        rows.append(
            {
                "policy_id": policy_id,
                "episode_rows": len(policy_rows),
                "changed_episode_rows": sum(1 for row in policy_rows if bool(row.get("order_changed_vs_detector"))),
                "promotion_allowed_rows": sum(int(row.get("utility_promotion_allowed_rows") or 0) for row in policy_rows),
                "blocked_field_hits": sum(int(row.get("blocked_field_hits") or 0) for row in policy_rows),
                "all_audit_pass": all(bool(row.get("audit_pass")) for row in policy_rows),
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
    policy_summary = summarize_policy_audit(audit_rows)
    selected_route = next(row for row in route_rows if row.get("route_id") == "selected_next_unit")
    return "\n".join(
        [
            "# E008-M155 Budget-Aware Utility Policy Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Source candidate rows: {coverage['source_candidate_rows']}.",
            f"- Materialized candidate rows: {coverage['materialized_candidate_rows']}.",
            f"- Utility component rows: {coverage['utility_component_rows']}.",
            f"- Selected changed episode rows: {coverage['selected_changed_episode_rows']}.",
            f"- Selected utility promoted rows: {coverage['selected_utility_promoted_rows']}.",
            f"- Materialization ready: {coverage['materialization_ready']}.",
            f"- Trajectory execution ready: {coverage['trajectory_execution_ready']}.",
            "",
            "## Policy Audit",
            "",
            markdown_table(
                policy_summary,
                ["policy_id", "episode_rows", "changed_episode_rows", "promotion_allowed_rows", "blocked_field_hits", "all_audit_pass"],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "rationale", "blocks_execution"]),
            "",
            "## Claim Boundary",
            "",
            markdown_table(claim_rows, ["claim_id", "supported", "claim_boundary"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Interpretation",
            "",
            "- Fact: M155 materializes policy rows only and does not execute `Habitat` trajectories.",
            "- Agent inference: if selected changed rows are positive and audits pass, the next safe step is Docker preflight for trajectory execution.",
            "- Paper claim boundary: M155 supports method materialization, not navigation improvement.",
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

    candidate_path = M149_DIR / "budget_guarded_candidate_rows.jsonl"
    m154_coverage_path = M154_DIR / "coverage.json"
    utility_path = M154_DIR / "utility_objective_rows.jsonl"
    guard_path = M154_DIR / "guard_contract_rows.jsonl"
    required = [candidate_path, m154_coverage_path, utility_path, guard_path]
    missing_inputs = [str(path) for path in required if not path.exists()]

    source_rows = read_jsonl(candidate_path)
    grouped = group_by_uid_policy(source_rows)

    candidate_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []

    for uid, policy_groups in sorted(grouped.items()):
        detector_rows = policy_groups.get(PROTECTED_BASELINE, [])
        selected_rows = policy_groups.get(M149_SELECTED_POLICY, [])
        if not detector_rows or not selected_rows:
            continue
        for config in DERIVED_POLICY_CONFIGS:
            rows, components, audit = materialize_derived_policy(
                uid=uid,
                config=config,
                detector_rows=detector_rows,
                selected_rows=selected_rows,
            )
            candidate_rows.extend(rows)
            component_rows.extend(components)
            audit_rows.append(audit)
        for policy_id in REFERENCE_POLICIES:
            ref_rows = policy_groups.get(policy_id, [])
            if not ref_rows:
                continue
            rows, audit = copy_reference_policy_rows(
                uid=uid,
                policy_id=policy_id,
                source_rows=ref_rows,
                detector_rows=detector_rows,
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
    gate_rows = build_materialization_gate_rows(
        missing_inputs=missing_inputs,
        candidate_rows=candidate_rows,
        audit_rows=audit_rows,
        leakage_rows=leakage_rows,
        selected_changed_episodes=selected_changed,
    )
    materialization_ready = (
        not missing_inputs
        and bool(candidate_rows)
        and all(bool(row.get("audit_pass")) for row in audit_rows)
        and all(bool(row.get("leakage_audit_pass")) for row in leakage_rows)
    )
    claim_rows = build_claim_boundary_rows(selected_changed)
    reviewer_rows = build_reviewer_defense_rows(selected_changed)
    route_rows = build_route_decision_rows(materialization_ready, selected_changed)
    coverage = build_coverage(
        missing_inputs=missing_inputs,
        source_candidate_rows=source_rows,
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
        ARTIFACT_DIR / "budget_aware_candidate_rows.jsonl",
        ARTIFACT_DIR / "utility_component_rows.jsonl",
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
    write_jsonl(outputs[2], component_rows)
    write_jsonl(outputs[3], plan_rows)
    write_jsonl(outputs[4], audit_rows)
    write_jsonl(outputs[5], leakage_rows)
    write_jsonl(outputs[6], gate_rows)
    write_jsonl(outputs[7], claim_rows)
    write_jsonl(outputs[8], reviewer_rows)
    write_jsonl(outputs[9], route_rows)
    outputs[10].write_text(
        build_report(coverage, audit_rows, gate_rows, route_rows, claim_rows),
        encoding="utf-8",
    )
    copy_artifacts(outputs)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
