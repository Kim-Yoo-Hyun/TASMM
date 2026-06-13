#!/usr/bin/env python3
"""Freeze the E008-M154 budget-aware utility objective and policy-selection contract."""

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
M148_DIR = EXP_ROOT / "artifacts" / "E008-M148_full_val_mini_budget_guarded_confidence_path_redesign_contract_v0"
M149_DIR = EXP_ROOT / "artifacts" / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
M153_DIR = EXP_ROOT / "artifacts" / "E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M154_budget_aware_utility_objective_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M154_budget_aware_utility_objective_contract_v0"

VERSION = "e008_m154_budget_aware_utility_objective_contract_v0"
READY_STATUS = "e008_m154_budget_aware_utility_objective_contract_ready"
BLOCKED_STATUS = "e008_m154_budget_aware_utility_objective_contract_blocked"
NEXT_UNIT = "E008-M155 budget-aware utility policy materialization smoke"

METHOD_POLICY = "budget_aware_confidence_path_utility_v0"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR = "budget_guarded_no_confidence_floor_v1"
M153_SELECTED = "budget_guarded_confidence_path_repair_v1"


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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def summarize_m149_budget_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, policy_rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "row_type": "prior_policy_audit_summary",
                "source_version": "e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0",
                "policy_id": policy_id,
                "episode_policy_rows": len(policy_rows),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in policy_rows]),
                "mean_path_repair_trigger_rows": mean(
                    [finite_float(row.get("path_repair_trigger_rows")) for row in policy_rows]
                ),
                "max_rank_displacement_abs_from_detector": max(
                    [int(row.get("max_rank_displacement_abs_from_detector") or 0) for row in policy_rows],
                    default=0,
                ),
                "mean_candidate_row_delta_vs_detector": mean(
                    [finite_float(row.get("planned_candidate_row_delta_vs_detector")) for row in policy_rows]
                ),
                "all_guard_pass": all(bool(row.get("guard_pass")) for row in policy_rows),
            }
        )
    return out


def build_utility_objective_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "utility_objective",
            "objective_id": METHOD_POLICY,
            "objective_role": "selected_next_method_contract",
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "formula_scope": "pre_execution_candidate_and_prefix_ranking_only",
            "formula_expression": (
                "utility_delta = "
                "0.040*clip(local_path_advantage_m/10,0,1) "
                "+ 0.020*source_gap_prelabel "
                "- 0.060*planned_extra_visit_norm "
                "- 0.040*clip(confidence_loss/0.03,0,1) "
                "- 0.030*rank_displacement_abs"
            ),
            "selection_rule": "promote_candidate_only_if_utility_delta_gt_0_and_all_guards_pass",
            "confidence_band_abs": 0.02,
            "min_local_path_advantage_m": 3.0,
            "max_rank_displacement_abs": 1,
            "max_planned_extra_visit_norm": 0.0,
            "path_cost_use": "bounded_repair_signal_not_primary_ordering",
            "visit_budget_use": "explicit_penalty_and_prefix_guard",
            "source_gap_use": "small_bonus_only_when_pre_labeled_before_eval",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "M153 shows path length reduction alone is not enough; the objective must charge planned visit cost and confidence loss before execution.",
        },
        {
            "version": VERSION,
            "row_type": "utility_objective",
            "objective_id": "detector_confidence_default_v0",
            "objective_role": "fallback_when_utility_margin_not_positive",
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "formula_scope": "pre_execution_candidate_ranking_only",
            "formula_expression": "score = detector_confidence_order",
            "selection_rule": "use_default_order_when_any_guard_fails_or_utility_delta_le_0",
            "confidence_band_abs": 0.0,
            "min_local_path_advantage_m": None,
            "max_rank_displacement_abs": 0,
            "max_planned_extra_visit_norm": 0.0,
            "path_cost_use": "none",
            "visit_budget_use": "protected_baseline",
            "source_gap_use": "none",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "Detector-confidence remains the protected naive baseline and default fallback.",
        },
    ]


def build_guard_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "no_eval_leakage_guard",
            "required": True,
            "pass_condition": "policy rows must not use ObjectNav eval goal, eval viewpoint, success candidate id, trajectory_success, SPL, StopRank, or nearest eval-viewpoint distance",
            "failure_action": "block_m155_materialization",
            "reason": "Navigation labels are metric-only fields.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "confidence_floor_guard",
            "required": True,
            "pass_condition": "candidate promotion is allowed only when confidence_loss <= 0.02 unless source_gap_prelabel is true",
            "failure_action": "fall_back_to_detector_confidence_order",
            "reason": "M153/M152 show no-confidence-floor is strongly negative.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "prefix_path_dominance_guard",
            "required": True,
            "pass_condition": "affected top-B prefixes must reduce planned cumulative path cost by at least 1.0m or keep detector order",
            "failure_action": "reject_candidate_promotion",
            "reason": "Path repair must pay for itself before execution; path length alone cannot be claimed after the fact.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "visit_budget_guard_strict",
            "required": True,
            "pass_condition": "planned_extra_visit_norm must equal 0.0 for non-source-gap rows; source-gap rows may spend extra visits only under prelabel",
            "failure_action": "fall_back_to_detector_confidence_order",
            "reason": "M153 shows no-visit-guard improves SPL only as a visit-expensive tradeoff witness.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "source_gap_prelabel_guard",
            "required": True,
            "pass_condition": "source_gap_prelabel must be created before trajectory execution and cannot use ObjectNav target/viewpoint placement",
            "failure_action": "treat_source_gap_bonus_as_zero",
            "reason": "Source-gap trigger is useful only as a pre-execution semantic-map state.",
        },
    ]


def build_policy_selection_rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "policy_selection_rule",
            "rule_id": "default_detector_confidence_first",
            "order": 1,
            "condition": "always_available",
            "action": "initialize_visit_order_from_detector_confidence_reachable_subset_v0",
            "selected_method": False,
            "claim_role": "protected_naive_baseline",
        },
        {
            "version": VERSION,
            "row_type": "policy_selection_rule",
            "rule_id": "hard_feasibility_veto_before_utility",
            "order": 2,
            "condition": "candidate path invalid, source snap invalid, or path_ready false",
            "action": "demote_or_drop_before_utility_scoring",
            "selected_method": True,
            "claim_role": "safety_guard",
        },
        {
            "version": VERSION,
            "row_type": "policy_selection_rule",
            "rule_id": "budget_aware_utility_promotion",
            "order": 3,
            "condition": "confidence_floor_guard, prefix_path_dominance_guard, visit_budget_guard_strict, and utility_delta > 0",
            "action": "promote_candidate_within_max_rank_displacement_abs_1",
            "selected_method": True,
            "claim_role": "selected_next_method_form",
        },
        {
            "version": VERSION,
            "row_type": "policy_selection_rule",
            "rule_id": "no_visit_guard_not_selectable",
            "order": 4,
            "condition": "policy resembles no_visit_guard by allowing visit-expensive displacement without strict guard",
            "action": "allow_only_as_ablation_not_selected_method",
            "selected_method": False,
            "claim_role": "tradeoff_witness_ablation",
        },
        {
            "version": VERSION,
            "row_type": "policy_selection_rule",
            "rule_id": "fallback_on_failed_margin",
            "order": 5,
            "condition": "utility_delta <= 0 or any required guard fails",
            "action": "keep_detector_confidence_order",
            "selected_method": True,
            "claim_role": "anti_regression_guard",
        },
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("confidence", "detector/proposal confidence visible before evaluation"),
        ("candidate_rank", "detector-confidence rank visible before evaluation"),
        ("rank_displacement_abs_from_detector", "planned rank displacement relative to protected baseline"),
        ("confidence_loss", "derived confidence drop from detector-confidence predecessor, computed before evaluation"),
        ("planned_extra_visit_norm", "derived planned visit-budget penalty, computed from candidate order before execution"),
        ("local_path_advantage_m", "pre-execution path cost advantage from trajectory cost matrix"),
        ("planned_cumulative_path_cost_m", "planned path prefix cost, not executed success path"),
        ("detector_prefix_cumulative_path_m", "protected detector-confidence prefix path cost for the same prefix size"),
        ("method_prefix_cumulative_path_m", "candidate method prefix path cost for the same prefix size"),
        ("prefix_path_delta_m", "method prefix path cost minus detector prefix path cost"),
        ("source_gap_prelabel", "pre-execution source-gap/source-coverage state"),
        ("path_ready", "navmesh/path readiness"),
        ("candidate_source_role", "current/stale/proposal source role"),
    ]
    blocked = [
        ("trajectory_success", "post-execution success label"),
        ("SPL", "post-execution metric"),
        ("StopRank", "post-execution success rank"),
        ("success_proposal_uid", "post-execution winning candidate id"),
        ("ObjectNav eval goal", "metric-only target field"),
        ("ObjectNav eval viewpoint", "metric-only target-view field"),
        ("nearest eval-viewpoint distance", "metric-only distance to evaluation target"),
    ]
    rows: list[dict[str, Any]] = []
    for field, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "row_type": "input_contract",
                "field": field,
                "input_status": "allowed",
                "reason": reason,
            }
        )
    for field, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "row_type": "input_contract",
                "field": field,
                "input_status": "blocked",
                "reason": reason,
            }
        )
    return rows


def build_ablation_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": PROTECTED_BASELINE,
            "role": "protected_naive_baseline",
            "required_for_m155": True,
            "expected_pressure": "selected method must beat or tie SR, improve SPL, and not increase candidate visits.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "budget_aware_utility_without_path_gain_v0",
            "role": "path_component_ablation",
            "required_for_m155": True,
            "expected_pressure": "tests whether path term adds anything beyond confidence floor and guards.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "budget_aware_utility_without_visit_penalty_v0",
            "role": "visit_penalty_ablation",
            "required_for_m155": True,
            "expected_pressure": "should reproduce M153 no-visit-guard tradeoff if visit cost is truly necessary.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "budget_aware_utility_without_source_gap_bonus_v0",
            "role": "source_gap_component_ablation",
            "required_for_m155": True,
            "expected_pressure": "tests whether source-gap/trust signal is useful or just decorative.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": NO_VISIT_GUARD,
            "role": "tradeoff_witness_not_selectable",
            "required_for_m155": True,
            "expected_pressure": "best-SPL but visit-expensive behavior should remain visible as reviewer defense.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": NO_CONFIDENCE_FLOOR,
            "role": "negative_control",
            "required_for_m155": True,
            "expected_pressure": "confidence floor must remain necessary.",
        },
    ]


def build_evaluation_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "evaluation_gate",
            "gate_id": "m155_materialization_readiness",
            "metric_or_check": "all required fields can be computed without eval leakage",
            "pass_condition": "missing required fields = 0 and blocked-field hits = 0",
            "blocks_final_claim": True,
        },
        {
            "version": VERSION,
            "row_type": "evaluation_gate",
            "gate_id": "m156_execution_promotion",
            "metric_or_check": "selected utility rows preserve denominator and Docker runner contract",
            "pass_condition": "candidate rows, execution plans, eval-goal rows, and oracle rows match M151 denominator",
            "blocks_final_claim": True,
        },
        {
            "version": VERSION,
            "row_type": "evaluation_gate",
            "gate_id": "protected_baseline_navigation_gate",
            "metric_or_check": "SR/SPL/CandidateVisits vs detector confidence",
            "pass_condition": "SR >= detector, SPL > detector, CandidateVisits_mean <= detector",
            "blocks_final_claim": True,
        },
        {
            "version": VERSION,
            "row_type": "evaluation_gate",
            "gate_id": "ablation_explanation_gate",
            "metric_or_check": "component ablations",
            "pass_condition": "visit penalty, path gain, confidence floor, and source-gap/trust ablations explain the observed gains or failures",
            "blocks_final_claim": True,
        },
        {
            "version": VERSION,
            "row_type": "evaluation_gate",
            "gate_id": "heldout_external_baseline_gate",
            "metric_or_check": "heldout transfer and external navigation/search baselines",
            "pass_condition": "pass only after M155/M156 selected method survives full-val-mini and later baseline route",
            "blocks_final_claim": True,
        },
    ]


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "next_unit": NEXT_UNIT,
            "input_source": "M149 candidate rows + M153 failure diagnosis",
            "output_rows": "budget-aware candidate rows, utility component rows, policy order audit rows, leakage audit rows",
            "must_not_run_habitat": True,
            "reason": "M155 should first prove that the utility contract is materializable before any Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "next_unit": "E008-M156 budget-aware utility trajectory execution contract / Docker preflight",
            "input_source": "M155 materialized rows if all guards pass",
            "output_rows": "runner candidate rows, execution plan rows, Docker command rows",
            "must_not_run_habitat": True,
            "reason": "Trajectory execution should wait until row-level leakage and denominator checks pass.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_aware_utility_contract_ready",
            "supported": True,
            "claim_boundary": "M154 supports a pre-execution method contract, not a performance claim.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_budget_aware_policy_improves_navigation",
            "supported": False,
            "claim_boundary": "Requires M155 materialization, M156/M157 execution, and protected-baseline gate.",
        },
        {
            "version": VERSION,
            "claim_id": "no_visit_guard_selected_method",
            "supported": False,
            "claim_boundary": "Still blocked; no-visit-guard remains a tradeoff witness ablation.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M154 remains target-free and does not change the E006-M08 human-intent boundary.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "is_m154_moving_the_goalposts",
            "reviewer_response": "No. M153 rejects the positive claim first; M154 precommits a new objective before any new materialization or trajectory execution.",
        },
        {
            "version": VERSION,
            "issue_id": "why_utility_instead_of_best_ablation",
            "reviewer_response": "`budget_guarded_no_visit_guard_v1` is best SPL but visit-expensive, so selecting it posthoc would not explain the search-budget failure.",
        },
        {
            "version": VERSION,
            "issue_id": "why_keep_detector_confidence",
            "reviewer_response": "Detector-confidence is the protected naive baseline and default fallback; path/search cost is only a bounded repair signal.",
        },
        {
            "version": VERSION,
            "issue_id": "what_would_falsify_the_new_contract",
            "reviewer_response": "If M155 cannot materialize required fields without leakage, or M157 fails SR/SPL/visit gates against detector-confidence, the contract is diagnostic only.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "materialize_budget_aware_utility_policy",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The objective is now fixed and must be materialized without eval leakage before trajectory execution.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "run_habitat_trajectory_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "M154 is contract-only; Docker execution waits until M155/M156 row and preflight gates pass.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required after the internal selected policy has a defensible utility form.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    m153_coverage: dict[str, Any],
    prior_audit_rows: list[dict[str, Any]],
    utility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    blocked_fields = [row for row in input_rows if row["input_status"] == "blocked"]
    selected_prior = next(
        (row for row in prior_audit_rows if row["policy_id"] == M153_SELECTED),
        {},
    )
    no_visit_prior = next(
        (row for row in prior_audit_rows if row["policy_id"] == NO_VISIT_GUARD),
        {},
    )
    ready = not missing_inputs and m153_coverage.get("status") == "e008_m153_full_val_mini_budget_spl_pareto_failure_decomposition_ready"
    return {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m153_status": m153_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "prior_policy_audit_rows": len(prior_audit_rows),
        "utility_objective_rows": len(utility_rows),
        "guard_contract_rows": len(guard_rows),
        "input_contract_rows": len(input_rows),
        "blocked_input_fields": len(blocked_fields),
        "selected_objective_id": METHOD_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "m153_selected_prior_max_rank_displacement": selected_prior.get("max_rank_displacement_abs_from_detector"),
        "m153_no_visit_guard_prior_max_rank_displacement": no_visit_prior.get("max_rank_displacement_abs_from_detector"),
        "performance_claim_ready": False,
        "trajectory_execution_ready": False,
        "selected_next_unit": NEXT_UNIT,
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


def build_report(
    coverage: dict[str, Any],
    utility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    ablation_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected_route = next(row for row in route_rows if row["selected"])
    return "\n".join(
        [
            "# E008-M154 Budget-Aware Utility Objective Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Input M153 status: `{coverage['m153_status']}`.",
            f"- Selected objective: `{coverage['selected_objective_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Performance claim ready: {coverage['performance_claim_ready']}.",
            f"- Trajectory execution ready: {coverage['trajectory_execution_ready']}.",
            "",
            "## Utility Objective",
            "",
            markdown_table(
                utility_rows,
                [
                    "objective_id",
                    "objective_role",
                    "formula_expression",
                    "selection_rule",
                    "confidence_band_abs",
                    "min_local_path_advantage_m",
                ],
            ),
            "",
            "## Required Guards",
            "",
            markdown_table(guard_rows, ["guard_id", "required", "pass_condition", "failure_action"]),
            "",
            "## Ablations",
            "",
            markdown_table(ablation_rows, ["policy_id", "role", "required_for_m155", "expected_pressure"]),
            "",
            "## Evaluation Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "metric_or_check", "pass_condition", "blocks_final_claim"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Interpretation",
            "",
            "- Fact: M154 fixes a contract only; it does not execute `Habitat` trajectories.",
            "- Agent inference: the next policy must charge path repair for confidence loss and planned visit cost before execution.",
            "- Paper claim boundary: M154 can be cited as method precommitment / reviewer defense, not as navigation performance evidence.",
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

    m153_coverage_path = M153_DIR / "coverage.json"
    m153_failure_path = M153_DIR / "failure_diagnosis_rows.jsonl"
    m148_policy_path = M148_DIR / "policy_contract_rows.jsonl"
    m149_budget_audit_path = M149_DIR / "budget_guard_audit_rows.jsonl"
    required = [m153_coverage_path, m153_failure_path, m148_policy_path, m149_budget_audit_path]
    missing = [str(path) for path in required if not path.exists()]

    m153_coverage = read_json(m153_coverage_path)
    m149_budget_audit_rows = read_jsonl(m149_budget_audit_path)

    prior_audit_rows = summarize_m149_budget_audit(m149_budget_audit_rows)
    utility_rows = build_utility_objective_rows()
    guard_rows = build_guard_contract_rows()
    selection_rows = build_policy_selection_rule_rows()
    input_rows = build_input_contract_rows()
    ablation_rows = build_ablation_contract_rows()
    gate_rows = build_evaluation_gate_rows()
    materialization_rows = build_materialization_plan_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()
    coverage = build_coverage(m153_coverage, prior_audit_rows, utility_rows, guard_rows, input_rows, missing)

    outputs = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "prior_policy_audit_summary_rows.jsonl",
        ARTIFACT_DIR / "utility_objective_rows.jsonl",
        ARTIFACT_DIR / "guard_contract_rows.jsonl",
        ARTIFACT_DIR / "policy_selection_rule_rows.jsonl",
        ARTIFACT_DIR / "input_contract_rows.jsonl",
        ARTIFACT_DIR / "ablation_contract_rows.jsonl",
        ARTIFACT_DIR / "evaluation_gate_rows.jsonl",
        ARTIFACT_DIR / "materialization_plan_rows.jsonl",
        ARTIFACT_DIR / "claim_boundary_rows.jsonl",
        ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
        ARTIFACT_DIR / "route_decision_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]

    write_json(outputs[0], coverage)
    write_jsonl(outputs[1], prior_audit_rows)
    write_jsonl(outputs[2], utility_rows)
    write_jsonl(outputs[3], guard_rows)
    write_jsonl(outputs[4], selection_rows)
    write_jsonl(outputs[5], input_rows)
    write_jsonl(outputs[6], ablation_rows)
    write_jsonl(outputs[7], gate_rows)
    write_jsonl(outputs[8], materialization_rows)
    write_jsonl(outputs[9], claim_rows)
    write_jsonl(outputs[10], reviewer_rows)
    write_jsonl(outputs[11], route_rows)
    outputs[12].write_text(
        build_report(coverage, utility_rows, guard_rows, ablation_rows, gate_rows, route_rows),
        encoding="utf-8",
    )
    copy_artifacts(outputs)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
