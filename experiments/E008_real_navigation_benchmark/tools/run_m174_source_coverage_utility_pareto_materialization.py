#!/usr/bin/env python3
"""Materialize E008-M174 source-coverage utility/Pareto rows."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
M173_DIR = EXP_ROOT / "artifacts" / "E008-M173_source_coverage_utility_pareto_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M174_source_coverage_utility_pareto_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M174_source_coverage_utility_pareto_materialization_smoke_v0"

VERSION = "e008_m174_source_coverage_utility_pareto_materialization_smoke_v0"
READY_STATUS = "e008_m174_source_coverage_utility_pareto_materialization_ready_for_m175"
BLOCKED_STATUS = "e008_m174_source_coverage_utility_pareto_materialization_blocked"
NEXT_UNIT = "E008-M175 source-coverage utility/Pareto Docker trajectory execution contract / preflight"
FAILURE_NEXT_UNIT = "E008-M174b source-coverage utility conservatism failure decomposition"

SELECTED_POLICY = "source_coverage_budgeted_utility_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_WITNESS = "source_coverage_only_task_agnostic_v1"
WITHOUT_VISIT = "source_coverage_utility_without_visit_penalty_v1"
WITHOUT_PATH = "source_coverage_utility_without_path_term_v1"
WITHOUT_COVERAGE = "source_coverage_utility_without_coverage_term_v1"
WITHOUT_CONFIDENCE_GUARD = "source_coverage_utility_without_confidence_guard_v1"

POLICY_ROLES = {
    SELECTED_POLICY: "selected_source_coverage_budgeted_utility_policy",
    PROTECTED_BASELINE: "protected_detector_confidence_baseline",
    SOURCE_COVERAGE_WITNESS: "task_agnostic_source_coverage_pareto_witness",
    WITHOUT_VISIT: "visit_penalty_ablation",
    WITHOUT_PATH: "path_term_ablation",
    WITHOUT_COVERAGE: "coverage_term_ablation",
    WITHOUT_CONFIDENCE_GUARD: "confidence_guard_negative_control",
}

POLICY_ORDER = [
    SELECTED_POLICY,
    PROTECTED_BASELINE,
    SOURCE_COVERAGE_WITNESS,
    WITHOUT_VISIT,
    WITHOUT_PATH,
    WITHOUT_COVERAGE,
    WITHOUT_CONFIDENCE_GUARD,
]

UTILITY_CONFIGS = {
    SELECTED_POLICY: {
        "coverage_weight": 0.050,
        "path_weight": 0.030,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.080,
        "confidence_penalty_weight": 0.060,
        "rank_penalty_weight": 0.040,
        "require_confidence_guard": True,
        "require_prefix_path_guard": True,
    },
    WITHOUT_VISIT: {
        "coverage_weight": 0.050,
        "path_weight": 0.030,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.0,
        "confidence_penalty_weight": 0.060,
        "rank_penalty_weight": 0.040,
        "require_confidence_guard": True,
        "require_prefix_path_guard": True,
    },
    WITHOUT_PATH: {
        "coverage_weight": 0.050,
        "path_weight": 0.0,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.080,
        "confidence_penalty_weight": 0.060,
        "rank_penalty_weight": 0.040,
        "require_confidence_guard": True,
        "require_prefix_path_guard": True,
    },
    WITHOUT_COVERAGE: {
        "coverage_weight": 0.0,
        "path_weight": 0.030,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.080,
        "confidence_penalty_weight": 0.060,
        "rank_penalty_weight": 0.040,
        "require_confidence_guard": True,
        "require_prefix_path_guard": True,
    },
    WITHOUT_CONFIDENCE_GUARD: {
        "coverage_weight": 0.050,
        "path_weight": 0.030,
        "source_gap_weight": 0.020,
        "visit_penalty_weight": 0.080,
        "confidence_penalty_weight": 0.0,
        "rank_penalty_weight": 0.040,
        "require_confidence_guard": False,
        "require_prefix_path_guard": True,
    },
}

FORBIDDEN_NONEMPTY_FIELDS = {
    "trajectory_success",
    "SR",
    "SPL",
    "StopRank",
    "success_proposal_uid",
    "success_candidate_to_eval_goal_xz_m",
    "success_candidate_to_nearest_eval_viewpoint_xz_m",
    "nearest_eval_viewpoint_distance_m",
    "eval_goal_position",
    "eval_viewpoint_position",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "primary_eval_hit",
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def finite_float(value: object, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def int_value(value: object, default: int = 10**9) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def nonempty(value: Any) -> bool:
    return value not in {None, False, "", 0} and value != [] and value != {}


def path_cost(row: dict[str, Any]) -> float:
    for field in ["source_to_candidate_path_cost_m", "current_pose_to_candidate_geodesic_m", "cumulative_known_path_cost_m"]:
        value = finite_float(row.get(field))
        if value is not None:
            return value
    return 10**9


def confidence(row: dict[str, Any]) -> float:
    return finite_float(row.get("confidence"), 0.0) or 0.0


def coverage_key(row: dict[str, Any]) -> str:
    return str(row.get("m168_coverage_key") or row.get("proposal_uid") or "unknown")


def row_blocked_hits(row: dict[str, Any]) -> list[str]:
    hits = [field for field in FORBIDDEN_NONEMPTY_FIELDS if field in row and nonempty(row.get(field))]
    if bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) or bool(row.get("policy_input_uses_eval_goal_or_viewpoint")):
        hits.append("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    if bool(row.get("uses_success_label_for_policy")) or bool(row.get("policy_input_uses_success_label")):
        hits.append("uses_success_label_for_policy")
    return sorted(set(hits))


def group_by_uid_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))].append(row)
    for policy_rows in grouped.values():
        for rows_for_policy in policy_rows.values():
            rows_for_policy.sort(key=lambda row: int_value(row.get("visit_rank")))
    return grouped


def move_candidate(order: list[dict[str, Any]], proposal_uid: str, target_idx: int) -> list[dict[str, Any]]:
    row = next(row for row in order if str(row.get("proposal_uid")) == proposal_uid)
    out = [row for row in order if str(row.get("proposal_uid")) != proposal_uid]
    out.insert(target_idx, row)
    return out


def compute_candidate_components(
    *,
    uid: str,
    policy_id: str,
    current_order: list[dict[str, Any]],
    witness_row: dict[str, Any],
    witness_rank: int,
    detector_rank_index: dict[str, int],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    proposal_uid = str(witness_row.get("proposal_uid"))
    current_idx = next((idx for idx, row in enumerate(current_order) if str(row.get("proposal_uid")) == proposal_uid), None)
    detector_rank = detector_rank_index.get(proposal_uid, witness_rank)
    target_idx = max(0, min(witness_rank - 1, len(current_order) - 1))
    if current_idx is None or target_idx >= current_idx:
        after_order = current_order
    else:
        after_order = move_candidate(current_order, proposal_uid, target_idx)

    before_top10 = current_order[:10]
    after_top10 = after_order[:10]
    before_unique = len({coverage_key(row) for row in before_top10})
    after_unique = len({coverage_key(row) for row in after_top10})
    coverage_novelty_norm = max(0.0, float(after_unique - before_unique) / 10.0)
    detector_prefix_path_m = sum(path_cost(row) for row in before_top10)
    method_prefix_path_m = sum(path_cost(row) for row in after_top10)
    prefix_path_saving_norm = clip((detector_prefix_path_m - method_prefix_path_m) / 20.0, 0.0, 1.0)
    displaced_row = current_order[target_idx] if current_order else witness_row
    confidence_loss = max(0.0, confidence(displaced_row) - confidence(witness_row))
    confidence_loss_norm = clip(confidence_loss / 0.05, 0.0, 1.0)
    rank_displacement_abs = abs(detector_rank - witness_rank)
    rank_displacement_norm = clip(float(rank_displacement_abs) / 5.0, 0.0, 1.0)
    expected_extra_visit_norm = 0.0
    source_gap_prelabel = bool(witness_row.get("m168_source_gap_prelabel"))

    utility_delta = (
        float(config["coverage_weight"]) * coverage_novelty_norm
        + float(config["path_weight"]) * prefix_path_saving_norm
        + float(config["source_gap_weight"]) * (1.0 if source_gap_prelabel else 0.0)
        - float(config["visit_penalty_weight"]) * expected_extra_visit_norm
        - float(config["confidence_penalty_weight"]) * confidence_loss_norm
        - float(config["rank_penalty_weight"]) * rank_displacement_norm
    )

    confidence_guard_pass = (not bool(config["require_confidence_guard"])) or confidence_loss <= 0.05
    fixed_budget_visit_guard_pass = expected_extra_visit_norm <= 0.0
    prefix_path_saving_guard_pass = (not bool(config["require_prefix_path_guard"])) or method_prefix_path_m <= detector_prefix_path_m + 1e-9
    source_gap_prelabel_guard_pass = True
    eval_leakage_guard_pass = len(row_blocked_hits(witness_row)) == 0
    promotion_candidate = current_idx is not None and target_idx < current_idx
    promotion_allowed = bool(
        promotion_candidate
        and utility_delta > 0.0
        and eval_leakage_guard_pass
        and confidence_guard_pass
        and fixed_budget_visit_guard_pass
        and prefix_path_saving_guard_pass
        and source_gap_prelabel_guard_pass
    )
    failed_guards = [
        guard
        for guard, passed in [
            ("eval_leakage_guard", eval_leakage_guard_pass),
            ("detector_confidence_protection_guard", confidence_guard_pass),
            ("fixed_budget_visit_guard", fixed_budget_visit_guard_pass),
            ("prefix_path_saving_guard", prefix_path_saving_guard_pass),
            ("source_gap_prelabel_guard", source_gap_prelabel_guard_pass),
            ("utility_delta_positive", utility_delta > 0.0),
        ]
        if not passed
    ]
    component = {
        "version": VERSION,
        "row_type": "utility_component",
        "benchmark_row_uid": uid,
        "policy_id": policy_id,
        "proposal_uid": proposal_uid,
        "detector_rank": detector_rank,
        "source_coverage_witness_rank": witness_rank,
        "target_rank": target_idx + 1,
        "promotion_candidate": promotion_candidate,
        "promotion_allowed": promotion_allowed,
        "fallback_reason": "promotion_allowed" if promotion_allowed else ",".join(failed_guards or ["not_a_promotion_candidate"]),
        "coverage_novelty_norm": coverage_novelty_norm,
        "prefix_path_saving_norm": prefix_path_saving_norm,
        "expected_extra_visit_norm": expected_extra_visit_norm,
        "confidence_loss_norm": confidence_loss_norm,
        "rank_displacement_norm": rank_displacement_norm,
        "source_gap_prelabel": source_gap_prelabel,
        "detector_prefix_path_m": detector_prefix_path_m,
        "method_prefix_path_m": method_prefix_path_m,
        "confidence_loss": confidence_loss,
        "rank_displacement_abs_from_detector": rank_displacement_abs,
        "utility_delta": utility_delta,
        "eval_leakage_guard_pass": eval_leakage_guard_pass,
        "detector_confidence_protection_guard_pass": confidence_guard_pass,
        "fixed_budget_visit_guard_pass": fixed_budget_visit_guard_pass,
        "prefix_path_saving_guard_pass": prefix_path_saving_guard_pass,
        "source_gap_prelabel_guard_pass": source_gap_prelabel_guard_pass,
        "all_required_guards_pass": not failed_guards,
    }
    return component, after_order, promotion_allowed


def copy_candidate_row(row: dict[str, Any], uid: str, policy_id: str, visit_rank: int, detector_rank_index: dict[str, int], component_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    proposal_uid = str(row.get("proposal_uid"))
    detector_rank = detector_rank_index.get(proposal_uid, visit_rank)
    displacement = visit_rank - detector_rank
    component = component_index.get(proposal_uid, {})
    out = dict(row)
    out.update(
        {
            "version": VERSION,
            "row_type": "source_coverage_utility_candidate",
            "m168_source_version": row.get("version"),
            "m174_materialization_version": VERSION,
            "claim_boundary": "M174 materializes source-coverage utility/Pareto rows only; no Habitat trajectory is executed.",
            "policy_id": policy_id,
            "policy_role": POLICY_ROLES[policy_id],
            "policy_plan_uid": f"m174::{uid}::{policy_id}",
            "candidate_visit_uid": f"m174::{uid}::{policy_id}::{visit_rank:04d}",
            "candidate_order_component": policy_id,
            "visit_rank": visit_rank,
            "m174_detector_visit_rank": detector_rank,
            "m174_rank_displacement_from_detector": displacement,
            "m174_rank_displacement_abs_from_detector": abs(displacement),
            "m174_selected_policy_id": SELECTED_POLICY,
            "m174_protected_baseline_policy_id": PROTECTED_BASELINE,
            "m174_source_coverage_witness_policy_id": SOURCE_COVERAGE_WITNESS,
            "m174_utility_delta": component.get("utility_delta", 0.0),
            "m174_promotion_candidate": bool(component.get("promotion_candidate", False)),
            "m174_promotion_allowed": bool(component.get("promotion_allowed", False)),
            "m174_fallback_reason": component.get("fallback_reason", "detector_confidence_default"),
            "m174_coverage_novelty_norm": component.get("coverage_novelty_norm", 0.0),
            "m174_prefix_path_saving_norm": component.get("prefix_path_saving_norm", 0.0),
            "m174_expected_extra_visit_norm": component.get("expected_extra_visit_norm", 0.0),
            "m174_confidence_loss_norm": component.get("confidence_loss_norm", 0.0),
            "m174_rank_displacement_norm": component.get("rank_displacement_norm", 0.0),
            "m174_policy_uses_source_coverage_utility": policy_id in UTILITY_CONFIGS,
            "m174_policy_is_reference_only": policy_id in {PROTECTED_BASELINE, SOURCE_COVERAGE_WITNESS},
            "requires_cumulative_path_recompute_for_execution": policy_id not in {PROTECTED_BASELINE},
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
        }
    )
    return out


def materialize_policy_rows(uid: str, policy_id: str, detector_rows: list[dict[str, Any]], witness_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    detector_rank_index = {str(row.get("proposal_uid")): idx for idx, row in enumerate(detector_rows, start=1)}
    if policy_id == PROTECTED_BASELINE:
        ordered = list(detector_rows)
        components: list[dict[str, Any]] = []
    elif policy_id == SOURCE_COVERAGE_WITNESS:
        ordered = list(witness_rows)
        components = []
    else:
        ordered = list(detector_rows)
        components = []
        config = UTILITY_CONFIGS[policy_id]
        for witness_rank, witness_row in enumerate(witness_rows, start=1):
            component, candidate_order, allowed = compute_candidate_components(
                uid=uid,
                policy_id=policy_id,
                current_order=ordered,
                witness_row=witness_row,
                witness_rank=witness_rank,
                detector_rank_index=detector_rank_index,
                config=config,
            )
            if component["promotion_candidate"]:
                components.append(component)
            if allowed:
                ordered = candidate_order
    component_index = {str(row.get("proposal_uid")): row for row in components if row.get("promotion_allowed")}
    policy_rows = [
        copy_candidate_row(row, uid=uid, policy_id=policy_id, visit_rank=rank, detector_rank_index=detector_rank_index, component_index=component_index)
        for rank, row in enumerate(ordered, start=1)
    ]
    cumulative = 0.0
    for row in policy_rows:
        cumulative += path_cost(row)
        row["m174_planned_cumulative_path_cost_proxy_m"] = cumulative
    return policy_rows, components


def build_policy_plan_rows(candidate_rows: list[dict[str, Any]], audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    audit_index = {(str(row.get("benchmark_row_uid")), str(row.get("policy_id"))): row for row in audit_rows}
    plan_rows: list[dict[str, Any]] = []
    for (uid, policy_id), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: int_value(row.get("visit_rank")))
        first = ordered[0]
        last = ordered[-1]
        audit = audit_index.get((uid, policy_id), {})
        plan_rows.append(
            {
                "version": VERSION,
                "row_type": "policy_plan",
                "benchmark_row_uid": uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "policy_plan_uid": f"m174::{uid}::{policy_id}",
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_rows": len(ordered),
                "path_ready_candidate_rows": sum(bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True)) for row in ordered),
                "first_proposal_uid": first.get("proposal_uid"),
                "last_proposal_uid": last.get("proposal_uid"),
                "planned_cumulative_path_cost_proxy_m": last.get("m174_planned_cumulative_path_cost_proxy_m"),
                "order_changed_vs_detector": bool(audit.get("order_changed_vs_detector")),
                "promoted_rows": audit.get("promoted_rows"),
                "demoted_rows": audit.get("demoted_rows"),
                "max_rank_displacement_abs_from_detector": audit.get("max_rank_displacement_abs_from_detector"),
                "requires_cumulative_path_recompute_for_execution": any(bool(row.get("requires_cumulative_path_recompute_for_execution")) for row in ordered),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
            }
        )
    return plan_rows


def build_order_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in candidate_rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))].append(row)
    audit_rows: list[dict[str, Any]] = []
    for uid, policy_map in sorted(grouped.items()):
        detector_rows = sorted(policy_map[PROTECTED_BASELINE], key=lambda row: int_value(row.get("visit_rank")))
        detector_order = [str(row.get("proposal_uid")) for row in detector_rows]
        detector_top10_coverage = len({coverage_key(row) for row in detector_rows[:10]})
        detector_top10_path = sum(path_cost(row) for row in detector_rows[:10])
        for policy_id, rows in sorted(policy_map.items()):
            ordered = sorted(rows, key=lambda row: int_value(row.get("visit_rank")))
            policy_order = [str(row.get("proposal_uid")) for row in ordered]
            displacements = [abs(int_value(row.get("m174_rank_displacement_from_detector"), 0)) for row in ordered]
            blocked_hits = sum(len(row_blocked_hits(row)) for row in ordered)
            audit_rows.append(
                {
                    "version": VERSION,
                    "row_type": "policy_order_audit",
                    "benchmark_row_uid": uid,
                    "policy_id": policy_id,
                    "candidate_rows": len(ordered),
                    "detector_candidate_rows": len(detector_rows),
                    "candidate_set_matches_detector": set(policy_order) == set(detector_order),
                    "order_changed_vs_detector": policy_order != detector_order,
                    "promoted_rows": sum(int_value(row.get("m174_rank_displacement_from_detector"), 0) < 0 for row in ordered),
                    "demoted_rows": sum(int_value(row.get("m174_rank_displacement_from_detector"), 0) > 0 for row in ordered),
                    "max_rank_displacement_abs_from_detector": max(displacements, default=0),
                    "unique_coverage_keys_first10": len({coverage_key(row) for row in ordered[:10]}),
                    "detector_unique_coverage_keys_first10": detector_top10_coverage,
                    "top10_path_cost_m": sum(path_cost(row) for row in ordered[:10]),
                    "detector_top10_path_cost_m": detector_top10_path,
                    "blocked_field_hits": blocked_hits,
                    "order_audit_pass": set(policy_order) == set(detector_order) and len(ordered) == len(detector_rows) and blocked_hits == 0,
                }
            )
    return audit_rows


def build_guard_audit_rows(candidate_rows: list[dict[str, Any]], component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    by_policy = defaultdict(list)
    by_policy_components = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for row in component_rows:
        by_policy_components[str(row.get("policy_id"))].append(row)
    for policy_id in POLICY_ORDER:
        rows = by_policy[policy_id]
        components = by_policy_components[policy_id]
        accepted = [row for row in components if row.get("promotion_allowed")]
        out.extend(
            [
                {
                    "version": VERSION,
                    "row_type": "guard_audit",
                    "policy_id": policy_id,
                    "guard_id": "eval_leakage_guard",
                    "checked_rows": len(rows),
                    "violation_rows": sum(1 for row in rows if row_blocked_hits(row)),
                    "guard_pass": all(not row_blocked_hits(row) for row in rows),
                },
                {
                    "version": VERSION,
                    "row_type": "guard_audit",
                    "policy_id": policy_id,
                    "guard_id": "detector_confidence_protection_guard",
                    "checked_rows": len(accepted),
                    "violation_rows": sum(1 for row in accepted if not row.get("detector_confidence_protection_guard_pass")),
                    "guard_pass": all(row.get("detector_confidence_protection_guard_pass") for row in accepted),
                    "required_for_policy": policy_id != WITHOUT_CONFIDENCE_GUARD,
                },
                {
                    "version": VERSION,
                    "row_type": "guard_audit",
                    "policy_id": policy_id,
                    "guard_id": "fixed_budget_visit_guard",
                    "checked_rows": len(rows),
                    "violation_rows": 0 if len(rows) % 30 == 0 else len(rows),
                    "guard_pass": len(rows) % 30 == 0,
                },
                {
                    "version": VERSION,
                    "row_type": "guard_audit",
                    "policy_id": policy_id,
                    "guard_id": "prefix_path_saving_guard",
                    "checked_rows": len(accepted),
                    "violation_rows": sum(1 for row in accepted if not row.get("prefix_path_saving_guard_pass")),
                    "guard_pass": all(row.get("prefix_path_saving_guard_pass") for row in accepted),
                },
                {
                    "version": VERSION,
                    "row_type": "guard_audit",
                    "policy_id": policy_id,
                    "guard_id": "source_gap_prelabel_guard",
                    "checked_rows": len(accepted),
                    "violation_rows": sum(1 for row in accepted if not row.get("source_gap_prelabel_guard_pass")),
                    "guard_pass": all(row.get("source_gap_prelabel_guard_pass") for row in accepted),
                },
            ]
        )
    return out


def build_leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for payload_name, rows in [("source_coverage_utility_candidate_rows", candidate_rows), ("policy_plan_rows", plan_rows)]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in row_blocked_hits(row):
                field_hits[field] += 1
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload_name,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def build_materialization_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    gates = [
        ("m173_contract_ready", coverage["m173_status"] == "e008_m173_source_coverage_utility_pareto_contract_ready", f"M173 status={coverage['m173_status']}.", True),
        ("required_rows_written", coverage["source_coverage_utility_candidate_rows"] == 6300 and coverage["policy_plan_rows"] == 210, f"candidate={coverage['source_coverage_utility_candidate_rows']}; plans={coverage['policy_plan_rows']}.", True),
        ("leakage_audit_pass", coverage["leakage_audit_pass"], f"failed leakage rows={coverage['leakage_audit_failed_rows']}.", True),
        ("order_audit_pass", coverage["order_audit_pass"], f"failed order rows={coverage['order_audit_failed_rows']}.", True),
        ("guard_audit_pass", coverage["guard_audit_pass"], f"failed guard rows={coverage['guard_audit_failed_rows']}.", True),
        ("selected_policy_activity_gate", coverage["selected_changed_episode_rows"] >= 5, f"selected changed episode rows={coverage['selected_changed_episode_rows']}; threshold=5.", True),
        ("execute_trajectories_now", False, "M174 is row materialization only; M175/M176 are required for Docker execution.", False),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "materialization_gate",
            "gate_id": gate_id,
            "status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m175": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_coverage_utility_rows_materialized",
            "supported": True,
            "claim_boundary": "M174 writes fixed utility/Pareto policy rows and audits them; it does not execute Habitat trajectories.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_utility_ready_for_trajectory_execution",
            "supported": ready,
            "claim_boundary": "Requires leakage/order/guard audits and selected policy activity gate before M175/M176.",
        },
        {
            "version": VERSION,
            "claim_id": "positive_navigation_improvement",
            "supported": False,
            "claim_boundary": "Requires Docker execution and protected-baseline interpretation after M174.",
        },
    ]


def build_route_rows(ready: bool, selected_changed: int) -> list[dict[str, Any]]:
    if ready:
        return [
            {
                "version": VERSION,
                "decision": "proceed_to_m175_trajectory_contract",
                "selected_next_unit": NEXT_UNIT,
                "launch_long_job_now": False,
                "reason": "M174 materialization, leakage/order/guard audits, and selected policy activity gate passed.",
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "block_docker_execution_and_run_failure_decomposition",
            "selected_next_unit": FAILURE_NEXT_UNIT,
            "launch_long_job_now": False,
            "reason": f"Selected policy changed {selected_changed}/30 episode orders; M173 disconfirmation rule requires at least 5 changed episodes before execution.",
        }
    ]


def build_report(coverage: dict[str, Any], audit_rows: list[dict[str, Any]], guard_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> str:
    selected_audits = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    policy_summary = []
    for policy_id in POLICY_ORDER:
        rows = [row for row in audit_rows if row.get("policy_id") == policy_id]
        policy_summary.append(
            {
                "policy_id": policy_id,
                "changed_episode_rows": sum(bool(row.get("order_changed_vs_detector")) for row in rows),
                "promoted_rows": sum(int(row.get("promoted_rows") or 0) for row in rows),
                "max_rank_displacement": max([int(row.get("max_rank_displacement_abs_from_detector") or 0) for row in rows], default=0),
                "order_audit_pass": all(row.get("order_audit_pass") for row in rows),
            }
        )
    return "\n".join(
        [
            "# E008-M174 Source-Coverage Utility/Pareto Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M173 status: `{coverage['m173_status']}`.",
            f"- Candidate rows: {coverage['source_coverage_utility_candidate_rows']}.",
            f"- Policy plan rows: {coverage['policy_plan_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Order audit pass: {coverage['order_audit_pass']}.",
            f"- Guard audit pass: {coverage['guard_audit_pass']}.",
            f"- Selected policy changed episode rows: {coverage['selected_changed_episode_rows']}.",
            f"- Trajectory contract ready next: {coverage['trajectory_contract_ready_next']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Summary",
            "",
            table(policy_summary, ["policy_id", "changed_episode_rows", "promoted_rows", "max_rank_displacement", "order_audit_pass"]),
            "",
            "## Selected Audit Sample",
            "",
            table(selected_audits[:10], ["benchmark_row_uid", "order_changed_vs_detector", "promoted_rows", "top10_path_cost_m", "detector_top10_path_cost_m", "order_audit_pass"]),
            "",
            "## Guard Audit",
            "",
            table(guard_rows, ["policy_id", "guard_id", "checked_rows", "violation_rows", "guard_pass"]),
            "",
            "## Gates",
            "",
            table(gate_rows, ["gate_id", "status", "blocks_m175", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M174 does not execute `Habitat` trajectories.",
            "- Docker execution is allowed only if selected policy activity and audit gates pass.",
            "- If selected policy activity fails, the next step is failure decomposition rather than threshold tuning.",
            "",
        ]
    )


def materialize_all(base_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = group_by_uid_policy(base_rows)
    candidate_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    for uid, policy_map in sorted(grouped.items()):
        detector_rows = policy_map.get(PROTECTED_BASELINE, [])
        witness_rows = policy_map.get(SOURCE_COVERAGE_WITNESS, [])
        if not detector_rows or not witness_rows:
            continue
        for policy_id in POLICY_ORDER:
            rows, components = materialize_policy_rows(uid, policy_id, detector_rows, witness_rows)
            candidate_rows.extend(rows)
            component_rows.extend(components)
    return candidate_rows, component_rows


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m173 = read_json(M173_DIR / "coverage.json")
    m168 = read_json(M168_DIR / "coverage.json")
    base_rows = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")
    missing = []
    if m173.get("status") != "e008_m173_source_coverage_utility_pareto_contract_ready":
        missing.append("M173 ready coverage")
    if m168.get("status") != "e008_m168_source_coverage_memory_interface_materialization_ready":
        missing.append("M168 ready coverage")
    if not base_rows:
        missing.append("M168 source coverage candidate rows")

    candidate_rows, component_rows = materialize_all(base_rows) if not missing else ([], [])
    audit_rows = build_order_audit_rows(candidate_rows)
    plan_rows = build_policy_plan_rows(candidate_rows, audit_rows)
    guard_rows = build_guard_audit_rows(candidate_rows, component_rows)
    leakage_rows = build_leakage_rows(candidate_rows, plan_rows)

    counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    selected_audits = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_changed = sum(bool(row.get("order_changed_vs_detector")) for row in selected_audits)
    selected_promoted = sum(int(row.get("promoted_rows") or 0) for row in selected_audits)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_rows)
    order_pass = all(row.get("order_audit_pass") for row in audit_rows)
    guard_pass = all(row.get("guard_pass") for row in guard_rows)
    required_rows_ready = len(candidate_rows) == 6300 and set(counts.values()) == {900} and len(plan_rows) == 210 and set(plan_counts.values()) == {30}

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "missing_inputs": missing,
        "m168_status": m168.get("status"),
        "m173_status": m173.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "source_coverage_witness_policy_id": SOURCE_COVERAGE_WITNESS,
        "policy_ids": POLICY_ORDER,
        "policy_count": len(POLICY_ORDER),
        "source_coverage_utility_candidate_rows": len(candidate_rows),
        "candidate_rows_by_policy": dict(sorted(counts.items())),
        "policy_plan_rows": len(plan_rows),
        "policy_plan_counts": dict(sorted(plan_counts.items())),
        "utility_component_rows": len(component_rows),
        "policy_order_audit_rows": len(audit_rows),
        "guard_audit_rows": len(guard_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_failed_rows": sum(1 for row in leakage_rows if not row.get("leakage_audit_pass")),
        "order_audit_failed_rows": sum(1 for row in audit_rows if not row.get("order_audit_pass")),
        "guard_audit_failed_rows": sum(1 for row in guard_rows if not row.get("guard_pass")),
        "required_rows_ready": required_rows_ready,
        "leakage_audit_pass": leakage_pass,
        "order_audit_pass": order_pass,
        "guard_audit_pass": guard_pass,
        "selected_changed_episode_rows": selected_changed,
        "selected_promoted_rows": selected_promoted,
        "selected_policy_activity_gate_pass": selected_changed >= 5,
        "source_coverage_witness_changed_episode_rows": sum(bool(row.get("order_changed_vs_detector")) for row in audit_rows if row.get("policy_id") == SOURCE_COVERAGE_WITNESS),
        "trajectory_contract_ready_next": False,
        "trajectory_execution_ready": False,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
    }
    ready = not missing and required_rows_ready and leakage_pass and order_pass and guard_pass and selected_changed >= 5
    coverage["status"] = READY_STATUS if ready else BLOCKED_STATUS
    coverage["trajectory_contract_ready_next"] = ready
    coverage["selected_next_unit"] = NEXT_UNIT if ready else FAILURE_NEXT_UNIT

    gate_rows = build_materialization_gate_rows(coverage)
    claim_rows = build_claim_rows(ready)
    route_rows = build_route_rows(ready, selected_changed)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_coverage_utility_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "policy_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "utility_component_rows.jsonl", component_rows)
    write_jsonl(ARTIFACT_DIR / "policy_order_audit_rows.jsonl", audit_rows)
    write_jsonl(ARTIFACT_DIR / "guard_audit_rows.jsonl", guard_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, audit_rows, guard_rows, gate_rows), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
