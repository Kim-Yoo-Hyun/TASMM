#!/usr/bin/env python3
"""Freeze the M148 budget-guarded confidence/path redesign contract."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M143_DIR = EXP_ROOT / "artifacts" / "E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0"
M147_DIR = EXP_ROOT / "artifacts" / "E008-M147_full_val_mini_policy_family_failure_decomposition_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0"

VERSION = "e008_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0"
READY_STATUS = "e008_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract_ready"
BLOCKED_STATUS = "e008_m148_full_val_mini_budget_guarded_confidence_path_redesign_contract_blocked"
NEXT_UNIT = "E008-M149 full-val-mini budget-guarded confidence/path row materialization smoke"

SELECTED_POLICY = "budget_guarded_confidence_path_repair_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_BAND = 0.03
MAX_RANK_DISPLACEMENT = 1
MAX_MEAN_VISIT_DELTA_FOR_PASS = 0.0


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


def bool_count(rows: list[dict[str, Any]], field: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[str(bool(row.get(field)))] += 1
    return counter


def field_present_count(rows: list[dict[str, Any]], field: str) -> int:
    return sum(1 for row in rows if row.get(field) is not None)


def build_policy_contract_rows() -> list[dict[str, Any]]:
    common = {
        "version": VERSION,
        "row_type": "policy_contract",
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "confidence_band": CONFIDENCE_BAND,
        "max_rank_displacement": MAX_RANK_DISPLACEMENT,
        "max_mean_visit_delta_for_pass": MAX_MEAN_VISIT_DELTA_FOR_PASS,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_success_label_for_policy": False,
    }
    return [
        {
            **common,
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_budget_guarded_method",
            "description": "Detector-confidence order is the default; path repair can fire only under a precommitted trigger and visit-budget guard.",
            "confidence_floor": "preserve_detector_confidence_order_outside_repair_trigger",
            "path_cost_use": "local_repair_signal_only",
            "visit_budget_guard": "required",
            "expected_failure_if_removed": "path repair can increase candidate visits and lose to detector-confidence as in M146/M147.",
        },
        {
            **common,
            "policy_id": "budget_guarded_confidence_only_v1",
            "policy_role": "confidence_floor_ablation",
            "description": "Same protected confidence floor and visit budget, but no path repair.",
            "confidence_floor": "preserve_detector_confidence_order",
            "path_cost_use": "none",
            "visit_budget_guard": "required",
            "expected_failure_if_removed": "tests whether the redesign contributes beyond protected confidence ordering.",
        },
        {
            **common,
            "policy_id": "budget_guarded_no_visit_guard_v1",
            "policy_role": "visit_guard_ablation",
            "description": "Allows the same path repair triggers but removes visit-budget protection.",
            "confidence_floor": "preserve_detector_confidence_order_outside_repair_trigger",
            "path_cost_use": "local_repair_signal_only",
            "visit_budget_guard": "removed",
            "expected_failure_if_removed": "should reproduce the M147 gain-with-visit-cost failure family.",
        },
        {
            **common,
            "policy_id": "budget_guarded_no_confidence_floor_v1",
            "policy_role": "negative_path_priority_ablation",
            "description": "Lets path/search cost dominate confidence within a larger candidate window.",
            "confidence_floor": "removed",
            "path_cost_use": "primary_ordering_signal",
            "visit_budget_guard": "optional",
            "expected_failure_if_removed": "should remain close to path-cost-first negative baseline behavior.",
        },
        {
            **common,
            "policy_id": "budget_guarded_source_gap_only_v1",
            "policy_role": "source_gap_trigger_ablation",
            "description": "Uses repair only for source-gap/source-coverage cases and otherwise keeps confidence order.",
            "confidence_floor": "preserve_detector_confidence_order",
            "path_cost_use": "source_gap_repair_signal",
            "visit_budget_guard": "required",
            "expected_failure_if_removed": "tests whether non-source-gap confidence-band repairs caused unnecessary visit cost.",
        },
    ]


def build_trigger_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "hard_feasibility_veto",
            "enabled_for_selected_policy": True,
            "allowed_inputs": "path_ready, candidate_usable_for_path_smoke, current_pose_to_candidate_path_found, source_to_snapped_path_found",
            "blocked_inputs": "success label, eval goal, eval viewpoint, nearest eval-viewpoint distance",
            "rule": "Unreachable or path-invalid candidates may be demoted before confidence ordering is applied.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "confidence_ambiguous_local_path_repair",
            "enabled_for_selected_policy": True,
            "allowed_inputs": "confidence, confidence_delta_from_top, candidate_rank, trajectory cost matrix, source role",
            "blocked_inputs": "per-episode SPL, trajectory_success, StopRank, success candidate id",
            "rule": f"Path repair can reorder only within confidence_delta_from_top <= {CONFIDENCE_BAND} and rank displacement <= {MAX_RANK_DISPLACEMENT}.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "visit_budget_guard",
            "enabled_for_selected_policy": True,
            "allowed_inputs": "candidate rank, protected baseline prefix, planned policy prefix, path-ready count",
            "blocked_inputs": "actual success rank, eval-goal distance, final CandidateVisits",
            "rule": "The selected policy must not plan a longer protected-prefix visit sequence than detector-confidence unless source-gap branch is active.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "source_gap_recovery_branch",
            "enabled_for_selected_policy": True,
            "allowed_inputs": "source-gap/source-coverage diagnostic produced before evaluation, source role, observation coverage state",
            "blocked_inputs": "ObjectNav target/viewpoint placement, posthoc success/failure labels",
            "rule": "Source-gap branch may spend extra visits only when the case was pre-labeled source-gap before trajectory execution.",
        },
    ]


def build_allowed_input_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "confidence",
        "confidence_delta_from_top",
        "candidate_rank",
        "visit_rank",
        "path_ready",
        "candidate_usable_for_path_smoke",
        "current_pose_to_candidate_geodesic_m",
        "planned_cumulative_path_cost_m",
        "source_to_candidate_path_cost_m",
        "candidate_source_role",
        "dynamic_stale_overlay_role",
        "task_context_id",
        "hard_feasibility_veto_applied",
        "confidence_order_override_allowed",
    ]
    return [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "present_rows": field_present_count(candidate_rows, field),
            "total_rows": len(candidate_rows),
            "allowed_reason": "available before policy execution and not derived from ObjectNav eval target or success label",
        }
        for field in fields
    ]


def build_blocked_input_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "uses_objectnav_eval_goal",
        "uses_objectnav_eval_viewpoint",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy",
        "policy_input_uses_eval_goal_or_viewpoint",
        "policy_input_uses_success_label",
        "trajectory_success",
        "SPL",
        "SR",
        "StopRank",
        "success_candidate_to_eval_goal_xz_m",
        "success_candidate_to_nearest_eval_viewpoint_xz_m",
        "success_proposal_uid",
    ]
    return [
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "observed_rows_in_m143_candidate_table": field_present_count(candidate_rows, field),
            "blocked_reason": "must not be used by M149 policy materialization; allowed only for later metric interpretation if present in execution output",
        }
        for field in fields
    ]


def build_budget_guard_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    override_counts = bool_count(candidate_rows, "confidence_order_override_allowed")
    hard_veto_counts = bool_count(candidate_rows, "hard_feasibility_veto_applied")
    return [
        {
            "version": VERSION,
            "row_type": "budget_guard",
            "guard_id": "protected_prefix_length_guard",
            "rule": "M149 selected policy must preserve the detector-confidence planned prefix length unless source_gap_recovery_branch is active.",
            "pass_condition_for_m150_execution": "mean CandidateVisits delta vs detector-confidence <= 0.0 and SR delta >= 0.0",
            "warning_condition_for_m150_execution": "SPL improves but CandidateVisits mean increases; record as diagnostic, not positive claim",
        },
        {
            "version": VERSION,
            "row_type": "budget_guard",
            "guard_id": "rank_displacement_guard",
            "rule": f"Path repair may move a candidate by at most {MAX_RANK_DISPLACEMENT} rank within the protected confidence band.",
            "m143_override_true_rows": override_counts.get("True", 0),
            "m143_override_false_rows": override_counts.get("False", 0),
        },
        {
            "version": VERSION,
            "row_type": "budget_guard",
            "guard_id": "hard_veto_guard",
            "rule": "Hard feasibility veto can demote path-invalid candidates before confidence ordering.",
            "m143_hard_veto_true_rows": hard_veto_counts.get("True", 0),
            "m143_hard_veto_false_rows": hard_veto_counts.get("False", 0),
        },
        {
            "version": VERSION,
            "row_type": "budget_guard",
            "guard_id": "m149_expected_policy_rows",
            "rule": "M149 should materialize selected policy plus ablation rows on the same 30-episode denominator.",
            "m143_policy_count_rows": dict(sorted(policy_counts.items())),
            "expected_selected_policy_rows": policy_counts.get(PROTECTED_BASELINE, 0),
        },
    ]


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    out_root = EXP_ROOT / "artifacts" / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
    derived_root = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
    command = (
        "python experiments/E008_real_navigation_benchmark/tools/"
        "run_m149_full_val_mini_budget_guarded_confidence_path_materialization.py "
        "--m143-root experiments/E008_real_navigation_benchmark/artifacts/"
        "E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0 "
        "--m148-contract experiments/E008_real_navigation_benchmark/artifacts/"
        "E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0 "
        f"--out-root {out_root} --derived-out-root {derived_root}"
    )
    return [
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "target_unit": NEXT_UNIT,
            "command": command,
            "working_directory": str(ROOT),
            "output_path": str(out_root),
            "derived_output_path": str(derived_root),
            "expected_files": [
                "coverage.json",
                "budget_guarded_candidate_rows.jsonl",
                "budget_guarded_execution_plan_rows.jsonl",
                "policy_order_audit_rows.jsonl",
                "budget_guard_audit_rows.jsonl",
                "leakage_audit_rows.jsonl",
                "report.md",
            ],
            "verification_command": (
                "python -m py_compile experiments/E008_real_navigation_benchmark/tools/"
                "run_m149_full_val_mini_budget_guarded_confidence_path_materialization.py"
            ),
            "long_job": False,
        }
    ]


def build_readiness_gate_rows(
    m143_cov: dict[str, Any],
    m147_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_count = len(candidate_rows)
    policy_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    blocked_policy_uses = sum(
        1
        for row in candidate_rows
        if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
        or row.get("policy_input_uses_eval_goal_or_viewpoint")
        or row.get("policy_input_uses_success_label")
    )
    missing_allowed = [row["field"] for row in allowed_rows if row["present_rows"] == 0]
    metric_only_present = [
        row["field"]
        for row in blocked_rows
        if row["observed_rows_in_m143_candidate_table"] > 0
        and row["field"]
        not in {
            "uses_objectnav_eval_goal",
            "uses_objectnav_eval_viewpoint",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy",
            "policy_input_uses_eval_goal_or_viewpoint",
            "policy_input_uses_success_label",
        }
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m143_candidate_rows_ready",
            "gate_status": "pass" if candidate_count == 5400 else "fail",
            "blocks_m149": candidate_count != 5400,
            "rationale": f"Expected 5,400 M143 candidate-policy rows; found {candidate_count}.",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m143_policy_denominator_ready",
            "gate_status": "pass" if len(policy_counts) == 6 and min(policy_counts.values() or [0]) == 900 else "fail",
            "blocks_m149": not (len(policy_counts) == 6 and min(policy_counts.values() or [0]) == 900),
            "rationale": f"Policy counts: {dict(sorted(policy_counts.items()))}",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m147_redesign_premise_ready",
            "gate_status": "pass" if m147_cov.get("redesign_contract_ready") is True else "fail",
            "blocks_m149": m147_cov.get("redesign_contract_ready") is not True,
            "rationale": "M148 depends on M147 failure decomposition and redesign contract.",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "allowed_inputs_available",
            "gate_status": "pass" if not missing_allowed else "fail",
            "blocks_m149": bool(missing_allowed),
            "rationale": f"Missing allowed fields: {missing_allowed}",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "blocked_policy_input_audit",
            "gate_status": "pass" if blocked_policy_uses == 0 else "fail",
            "blocks_m149": blocked_policy_uses != 0,
            "rationale": f"Rows with blocked policy input flags: {blocked_policy_uses}; metric-only blocked fields present: {metric_only_present}",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m143_source_status",
            "gate_status": "pass" if str(m143_cov.get("status", "")).endswith("_ready") else "warning",
            "blocks_m149": False,
            "rationale": f"M143 status: {m143_cov.get('status')}",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "positive_navigation_claim",
            "gate_status": "fail",
            "blocks_m149": False,
            "rationale": "M148 is only a redesign contract; it does not support positive navigation claims.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "budget_guarded_redesign_contract",
            "supported": True,
            "claim_boundary": "M148 freezes a pre-execution policy form, allowed inputs, guard rules, and M149 materialization route.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "positive_navigation_improvement",
            "supported": False,
            "claim_boundary": "No positive navigation claim until the M148-selected policy is materialized, executed, and beats protected baselines.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Requires M149 materialization, trajectory execution, heldout transfer, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M148 target-free navigation route does not alter E006-M08's human-intent boundary.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "materialize_budget_guarded_policy",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The method form is precommitted and uses only allowed M143/M147 fields.",
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "rerun_trajectory_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Policy rows and execution plans must be materialized and audited before Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required after the internal selected policy is stable.",
        },
    ]


def render_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    trigger_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E008-M148 Budget-Guarded Confidence/Path Redesign Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected policy: `{coverage['selected_policy_id']}`.",
        f"- M143 candidate rows: {coverage['m143_candidate_rows']}.",
        f"- Confidence band: {coverage['confidence_band']}.",
        f"- Max rank displacement: {coverage['max_rank_displacement']}.",
        f"- Redesign contract ready: {coverage['redesign_contract_ready']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Policy Contracts",
        "",
        "| policy_id | role | confidence_floor | path_cost_use | visit_guard |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in policy_rows:
        lines.append(
            f"| {row['policy_id']} | {row['policy_role']} | {row['confidence_floor']} | {row['path_cost_use']} | {row['visit_budget_guard']} |"
        )

    lines.extend(["", "## Trigger Contracts", "", "| trigger_id | enabled | rule |", "| --- | --- | --- |"])
    for row in trigger_rows:
        lines.append(f"| {row['trigger_id']} | {row['enabled_for_selected_policy']} | {row['rule']} |")

    lines.extend(["", "## Readiness Gates", "", "| gate_id | status | blocks_m149 | rationale |", "| --- | --- | --- | --- |"])
    for row in gate_rows:
        lines.append(f"| {row['gate_id']} | {row['gate_status']} | {row['blocks_m149']} | {row['rationale']} |")

    lines.extend(["", "## M149 Plan", ""])
    for row in materialization_rows:
        lines.append(f"- Command: `{row['command']}`")
        lines.append(f"- Output path: `{row['output_path']}`")

    lines.extend(["", "## Route Decision", "", "| route_id | decision | selected | selected_next_unit |", "| --- | --- | --- | --- |"])
    for row in route_rows:
        lines.append(f"| {row['route_id']} | {row['decision']} | {row['selected']} | {row.get('selected_next_unit')} |")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M148 does not claim navigation improvement.",
            "- M148 prevents posthoc policy selection by freezing the selected policy and ablations before M149.",
            "- M149 must materialize rows and audit leakage/budget guards before any Docker trajectory execution.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    m143_cov = read_json(M143_DIR / "coverage.json")
    m147_cov = read_json(M147_DIR / "coverage.json")
    candidate_rows = read_jsonl(M143_DIR / "confidence_preserving_candidate_rows.jsonl")

    required_inputs = [
        M143_DIR / "coverage.json",
        M143_DIR / "confidence_preserving_candidate_rows.jsonl",
        M147_DIR / "coverage.json",
        M147_DIR / "redesign_contract_rows.jsonl",
    ]
    missing_inputs = [str(path) for path in required_inputs if not path.exists()]
    if missing_inputs:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        coverage = {
            "version": VERSION,
            "status": BLOCKED_STATUS,
            "generated_at": generated_at,
            "missing_inputs": missing_inputs,
            "selected_next_unit": None,
        }
        write_json(ARTIFACT_DIR / "coverage.json", coverage)
        return 1

    policy_rows = build_policy_contract_rows()
    trigger_rows = build_trigger_contract_rows()
    allowed_rows = build_allowed_input_rows(candidate_rows)
    blocked_rows = build_blocked_input_rows(candidate_rows)
    budget_rows = build_budget_guard_rows(candidate_rows)
    materialization_rows = build_materialization_plan_rows()
    gate_rows = build_readiness_gate_rows(m143_cov, m147_cov, candidate_rows, allowed_rows, blocked_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    blocking_fail_count = sum(
        1 for row in gate_rows if row.get("gate_status") == "fail" and row.get("blocks_m149")
    )
    gate_fail_count = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    gate_warning_count = sum(1 for row in gate_rows if row.get("gate_status") == "warning")
    policy_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    override_counts = bool_count(candidate_rows, "confidence_order_override_allowed")
    hard_veto_counts = bool_count(candidate_rows, "hard_feasibility_veto_applied")

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if blocking_fail_count == 0 else BLOCKED_STATUS,
        "generated_at": generated_at,
        "missing_inputs": [],
        "m143_status": m143_cov.get("status"),
        "m147_status": m147_cov.get("status"),
        "m143_candidate_rows": len(candidate_rows),
        "m143_policy_counts": dict(sorted(policy_counts.items())),
        "confidence_override_true_rows": override_counts.get("True", 0),
        "hard_feasibility_veto_true_rows": hard_veto_counts.get("True", 0),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "confidence_band": CONFIDENCE_BAND,
        "max_rank_displacement": MAX_RANK_DISPLACEMENT,
        "max_mean_visit_delta_for_pass": MAX_MEAN_VISIT_DELTA_FOR_PASS,
        "policy_contract_rows": len(policy_rows),
        "trigger_contract_rows": len(trigger_rows),
        "allowed_input_rows": len(allowed_rows),
        "blocked_input_rows": len(blocked_rows),
        "budget_guard_rows": len(budget_rows),
        "materialization_plan_rows": len(materialization_rows),
        "gate_fail_count": gate_fail_count,
        "gate_warning_count": gate_warning_count,
        "blocking_gate_fail_count": blocking_fail_count,
        "redesign_contract_ready": blocking_fail_count == 0,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if blocking_fail_count == 0 else None,
    }

    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "trigger_contract_rows.jsonl", trigger_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_rows.jsonl", allowed_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "budget_guard_rows.jsonl", budget_rows)
    write_jsonl(ARTIFACT_DIR / "m149_materialization_plan_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        render_report(coverage, policy_rows, trigger_rows, gate_rows, materialization_rows, route_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
