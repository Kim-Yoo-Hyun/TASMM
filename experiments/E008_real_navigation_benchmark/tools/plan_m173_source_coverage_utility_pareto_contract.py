#!/usr/bin/env python3
"""Freeze E008-M173 source-coverage utility/Pareto contract."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
M172_DIR = EXP_ROOT / "artifacts" / "E008-M172_source_coverage_ablation_tradeoff_decomposition_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M173_source_coverage_utility_pareto_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M173_source_coverage_utility_pareto_contract_v0"

VERSION = "e008_m173_source_coverage_utility_pareto_contract_v0"
READY_STATUS = "e008_m173_source_coverage_utility_pareto_contract_ready"
BLOCKED_STATUS = "e008_m173_source_coverage_utility_pareto_contract_blocked"
NEXT_UNIT = "E008-M174 source-coverage utility/Pareto row materialization smoke"

SELECTED_POLICY = "source_coverage_budgeted_utility_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_WITNESS = "source_coverage_only_task_agnostic_v1"
PREVIOUS_SELECTED = "source_coverage_memory_interface_policy_v1"
CONFIDENCE_ONLY = "confidence_floor_only_v1"
PATH_ONLY = "path_cost_only_reachable_subset_v1"

REQUIRED_MATERIALIZATION_FIELDS = [
    "benchmark_row_uid",
    "policy_id",
    "candidate_visit_uid",
    "proposal_uid",
    "confidence",
    "m168_coverage_key",
    "m168_detector_visit_rank",
    "m168_rank_displacement_abs_from_detector",
    "m168_source_gap_prelabel",
    "source_to_candidate_path_cost_m",
    "m168_planned_cumulative_path_cost_proxy_m",
    "path_ready",
    "policy_input_uses_eval_goal_or_viewpoint",
    "uses_success_label_for_policy",
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def build_field_availability_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(candidate_rows)
    rows: list[dict[str, Any]] = []
    for field in REQUIRED_MATERIALIZATION_FIELDS:
        present = sum(field in row and row.get(field) is not None for row in candidate_rows)
        rows.append(
            {
                "version": VERSION,
                "row_type": "field_availability",
                "field": field,
                "present_rows": present,
                "total_rows": total,
                "all_rows_ready": total > 0 and present == total,
                "required_for_m174": True,
            }
        )
    return rows


def build_method_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_next_policy_contract",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "source coverage can be used only as a budget-aware semantic-map interface decision under detector-confidence guard",
            "method_form": "start from detector-confidence order, add bounded source-coverage utility, fall back to detector order unless utility and guards pass",
            "why_this_form": "M172 shows source coverage can change successful proposals but is unstable and visit-expensive without an explicit utility/Pareto objective.",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "materialize_before_execution": True,
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": PROTECTED_BASELINE,
            "policy_role": "protected_naive_baseline",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "detector-confidence remains the default current-evidence reliability order",
            "method_form": "no source coverage utility; no path utility",
            "why_this_form": "M172 shows the previous selected policy is dominated by detector-confidence/confidence-floor.",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "materialize_before_execution": True,
        },
    ]


def build_utility_objective_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "utility_objective",
            "objective_id": SELECTED_POLICY,
            "objective_role": "selected_next_objective",
            "formula_scope": "pre_execution_candidate_ranking_only",
            "formula_expression": (
                "utility_delta = "
                "0.050*coverage_novelty_norm "
                "+ 0.030*prefix_path_saving_norm "
                "+ 0.020*source_gap_prelabel "
                "- 0.080*expected_extra_visit_norm "
                "- 0.060*confidence_loss_norm "
                "- 0.040*rank_displacement_norm"
            ),
            "selection_rule": "promote candidate only when utility_delta > 0 and every required guard passes; otherwise keep detector-confidence order",
            "coverage_novelty_norm": "new unique m168_coverage_key in top-10 prefix divided by 10",
            "prefix_path_saving_norm": "clip((detector_prefix_path_m - method_prefix_path_m)/20,0,1)",
            "expected_extra_visit_norm": "clip((method_prefix_len - detector_prefix_len)/10,0,1); selected method target is zero on non-source-gap rows",
            "confidence_loss_norm": "clip((detector_candidate_confidence - promoted_candidate_confidence)/0.05,0,1)",
            "rank_displacement_norm": "clip(abs(rank_displacement_from_detector)/5,0,1)",
            "primary_objective_type": "bounded_fixed_budget_pareto_utility",
            "why_this_objective": "M172 makes source coverage useful only as a tradeoff; this formula charges the exact failure terms: visits, confidence loss, and rank displacement.",
        },
        {
            "version": VERSION,
            "row_type": "utility_objective",
            "objective_id": "detector_confidence_fallback_v1",
            "objective_role": "fallback_and_protected_baseline",
            "formula_scope": "pre_execution_candidate_ranking_only",
            "formula_expression": "utility_delta = 0; order = detector_confidence_reachable_subset_v0",
            "selection_rule": "fallback whenever selected objective has utility_delta <= 0 or a required guard fails",
            "coverage_novelty_norm": "not used",
            "prefix_path_saving_norm": "not used",
            "expected_extra_visit_norm": "not used",
            "confidence_loss_norm": "not used",
            "rank_displacement_norm": "not used",
            "primary_objective_type": "protected_default_order",
            "why_this_objective": "Detector-confidence is the simplest defended baseline after M171/M172.",
        },
    ]


def build_guard_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "eval_leakage_guard",
            "required": True,
            "pass_condition": "policy rows must not use ObjectNav eval goal/viewpoint, trajectory_success, SR, SPL, StopRank, success_proposal_uid, or nearest eval-viewpoint distance",
            "failure_action": "block_m174_materialization",
            "reason": "M173 is a pre-execution method contract.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "detector_confidence_protection_guard",
            "required": True,
            "pass_condition": "candidate confidence must remain within 0.05 of the detector-prefix candidate it displaces",
            "failure_action": "fallback_to_detector_order",
            "reason": "M172 shows detector-confidence dominates the previous selected method.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "fixed_budget_visit_guard",
            "required": True,
            "pass_condition": "non-source-gap rows may not increase planned top-10 candidate count or expected extra visit norm",
            "failure_action": "reject_promotion",
            "reason": "Source-coverage-only gained mean SPL with more visits, so visit cost must be charged before execution.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "prefix_path_saving_guard",
            "required": True,
            "pass_condition": "promoted source-coverage candidate must not increase top-10 planned cumulative path cost; path-only cannot become primary order",
            "failure_action": "reject_promotion",
            "reason": "M172 shows path-cost-only lowers path length but loses SPL/visits.",
        },
        {
            "version": VERSION,
            "row_type": "guard_contract",
            "guard_id": "source_gap_prelabel_guard",
            "required": True,
            "pass_condition": "source_gap_prelabel can relax visit guard only if computed before evaluation without target/viewpoint leakage",
            "failure_action": "treat_source_gap_bonus_as_zero",
            "reason": "M172 source-gap prelabel rows are zero; source-gap claims remain restricted.",
        },
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("confidence", "current detector/proposal reliability"),
        ("candidate_rank", "pre-execution detector rank"),
        ("m168_detector_visit_rank", "protected baseline visit rank"),
        ("m168_coverage_key", "source-coverage identity"),
        ("frame_pose_role", "source pose role"),
        ("observation_pose_id", "source observation identity"),
        ("bearing_relative_deg", "source coverage direction"),
        ("shell_radius_m", "source coverage radius"),
        ("source_to_candidate_path_cost_m", "pre-execution path cost"),
        ("m168_planned_cumulative_path_cost_proxy_m", "planned prefix path proxy"),
        ("path_ready", "hard feasibility guard"),
        ("m168_rank_displacement_abs_from_detector", "bounded displacement guard"),
        ("m168_source_gap_prelabel", "pre-execution source-gap state"),
    ]
    blocked = [
        ("ObjectNav eval goal", "metric-only target"),
        ("ObjectNav eval viewpoint", "metric-only viewpoint"),
        ("trajectory_success", "post-execution label"),
        ("SR", "post-execution metric"),
        ("SPL", "post-execution metric"),
        ("StopRank", "post-execution success rank"),
        ("success_proposal_uid", "post-execution winning candidate"),
        ("success_candidate_to_nearest_eval_viewpoint_xz_m", "metric-only target distance"),
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


def build_metric_target_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "clean_navigation_improvement_gate",
            "claim_role": "required_for_positive_navigation_claim",
            "comparison_policy_id": PROTECTED_BASELINE,
            "pass_condition": "SR >= detector and SPL > detector and CandidateVisits_mean <= detector",
            "disconfirmation_action": "reject_positive_navigation_claim_and_run_failure_decomposition",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "precommitted_pareto_utility_gate",
            "claim_role": "diagnostic_or_secondary_claim_only",
            "comparison_policy_id": PROTECTED_BASELINE,
            "pass_condition": "precommitted utility improves while clean_navigation_improvement_gate may still fail",
            "disconfirmation_action": "do_not_claim_real_navigation_sr_spl; keep as tradeoff evidence only",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "source_coverage_ablation_explanation_gate",
            "claim_role": "required_for_method_component_claim",
            "comparison_policy_id": SOURCE_COVERAGE_WITNESS,
            "pass_condition": "selected method matches or improves source-coverage-only utility while reducing visits or preserving SPL",
            "disconfirmation_action": "source coverage is useful but not integrated by H001 method form",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "heldout_external_baseline_gate",
            "claim_role": "required_for_final_top_tier_claim",
            "comparison_policy_id": "external_navigation_or_map_baselines",
            "pass_condition": "heldout transfer and at least one stronger navigation/search baseline route are evaluated",
            "disconfirmation_action": "keep result as internal diagnostic table",
        },
    ]


def build_ablation_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": PROTECTED_BASELINE,
            "role": "protected_naive_baseline",
            "required_for_m174": True,
            "expected_pressure": "must remain unbeaten fallback unless selected utility genuinely improves budgeted navigation.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": SOURCE_COVERAGE_WITNESS,
            "role": "tradeoff_witness_not_main_method",
            "required_for_m174": True,
            "expected_pressure": "tests whether source coverage alone explains any gains and whether visit cost remains visible.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "source_coverage_utility_without_visit_penalty_v1",
            "role": "visit_penalty_ablation",
            "required_for_m174": True,
            "expected_pressure": "should reproduce source-coverage-only visit-expensive behavior if visit penalty is necessary.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "source_coverage_utility_without_path_term_v1",
            "role": "path_term_ablation",
            "required_for_m174": True,
            "expected_pressure": "tests whether path savings are useful beyond coverage novelty and confidence.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "source_coverage_utility_without_coverage_term_v1",
            "role": "coverage_term_ablation",
            "required_for_m174": True,
            "expected_pressure": "tests whether source coverage is necessary or only decorative.",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": "source_coverage_utility_without_confidence_guard_v1",
            "role": "negative_control",
            "required_for_m174": True,
            "expected_pressure": "should expose detector-confidence degradation if the confidence guard is necessary.",
        },
    ]


def build_disconfirmation_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "disconfirmation_rule",
            "rule_id": "no_materialized_policy_change",
            "condition": "M174 selected policy changes fewer than 5/30 episode orders",
            "interpretation": "utility contract is too conservative to be a method contribution",
            "next_action": "record as diagnostic; do not execute trajectories without a new failure-derived principle",
        },
        {
            "version": VERSION,
            "row_type": "disconfirmation_rule",
            "rule_id": "selected_repeats_m171_failure",
            "condition": "future execution has SR tie/loss, SPL <= detector, and visits > detector",
            "interpretation": "source coverage integration still fails the protected baseline",
            "next_action": "reject positive navigation claim and inspect candidate-source rather than threshold tuning",
        },
        {
            "version": VERSION,
            "row_type": "disconfirmation_rule",
            "rule_id": "utility_only_gain",
            "condition": "future execution improves precommitted utility but not clean SR/SPL/visit gate",
            "interpretation": "claim can only be Pareto/diagnostic, not final real navigation SR/SPL",
            "next_action": "keep claim boundary and require external baseline pressure before paper claim",
        },
    ]


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "selected_next_unit": NEXT_UNIT,
            "input_candidate_rows": "experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/source_coverage_candidate_rows.jsonl",
            "input_policy_plan_rows": "experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/policy_plan_rows.jsonl",
            "input_component_rows": "experiments/E008_real_navigation_benchmark/artifacts/E008-M168_source_coverage_memory_interface_materialization_v0/source_coverage_component_rows.jsonl",
            "policies_to_materialize": [
                SELECTED_POLICY,
                PROTECTED_BASELINE,
                SOURCE_COVERAGE_WITNESS,
                "source_coverage_utility_without_visit_penalty_v1",
                "source_coverage_utility_without_path_term_v1",
                "source_coverage_utility_without_coverage_term_v1",
                "source_coverage_utility_without_confidence_guard_v1",
            ],
            "required_outputs": [
                "source_coverage_utility_candidate_rows.jsonl",
                "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "policy_plan_rows.jsonl",
                "utility_component_rows.jsonl",
                "policy_order_audit_rows.jsonl",
                "leakage_audit_rows.jsonl",
                "report.md",
            ],
            "must_not_run_habitat": True,
            "reason": "M174 must prove the new objective is materializable and leakage-safe before Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "selected_next_unit": "E008-M175 source-coverage utility/Pareto trajectory contract / Docker preflight",
            "input_candidate_rows": "E008-M174 materialized rows if ready",
            "input_policy_plan_rows": "E008-M174 policy plans if leakage/order gates pass",
            "input_component_rows": "E008-M174 utility component rows",
            "policies_to_materialize": [],
            "required_outputs": [
                "trajectory_candidate_rows.jsonl",
                "trajectory_execution_plan_rows.jsonl",
                "docker_preflight_rows.jsonl",
                "m176_command_rows.jsonl",
            ],
            "must_not_run_habitat": True,
            "reason": "Trajectory execution waits until the selected utility policy passes row-level gates.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_coverage_utility_contract_ready",
            "supported": True,
            "claim_boundary": "M173 supports a pre-execution method/utility contract only.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_policy_improves_real_navigation",
            "supported": False,
            "claim_boundary": "Requires M174 materialization, M175 Docker preflight, M176 execution, and protected-baseline interpretation.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_only_main_method",
            "supported": False,
            "claim_boundary": "Still blocked; source-coverage-only remains a task-agnostic tradeoff witness.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M173 is target-free and does not change E006-M08.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still requires selected method success, heldout transfer, and external navigation/search baselines.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "is_m173_cherry_picking_source_coverage",
            "reviewer_response": "No. M172 explicitly rejects source-coverage-only as a main method; M173 precommits the utility and guards before materialization/execution.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_claim_pareto_frontier_now",
            "reviewer_response": "M172 shows a Pareto witness, but top-tier claim needs a selected method and precommitted objective, not a posthoc ablation.",
        },
        {
            "version": VERSION,
            "issue_id": "why_detector_confidence_remains_protected",
            "reviewer_response": "The previous selected policy is dominated by detector-confidence/confidence-floor; any new method must keep detector-confidence as fallback and baseline.",
        },
        {
            "version": VERSION,
            "issue_id": "what_would_falsify_m173",
            "reviewer_response": "If M174 cannot materialize rows without leakage, or future execution repeats SPL/visit regression, the method contract is diagnostic only.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "materialize_source_coverage_utility_policy",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The objective is fixed; next step is row materialization and leakage/order audit.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "run_habitat_trajectory_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "M173 is contract-only; Docker execution waits for M174/M175.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "promote_source_coverage_only_main_method",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "M172 labels it as task-agnostic tradeoff witness with extra visits.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    utility_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M173 Source-Coverage Utility/Pareto Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M172 status: `{coverage['m172_status']}`.",
            f"- Selected next policy: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Required fields ready: {coverage['required_fields_ready']}.",
            f"- Candidate rows audited: {coverage['candidate_rows_audited']}.",
            f"- Performance claim ready: {coverage['performance_claim_ready']}.",
            f"- Trajectory execution ready: {coverage['trajectory_execution_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Method Contract",
            "",
            table(method_rows, ["policy_id", "policy_role", "principle", "materialize_before_execution"]),
            "",
            "## Utility Objective",
            "",
            table(utility_rows, ["objective_id", "objective_role", "primary_objective_type", "selection_rule"]),
            "",
            "## Guards",
            "",
            table(guard_rows, ["guard_id", "required", "pass_condition", "failure_action"]),
            "",
            "## Metric Targets",
            "",
            table(metric_rows, ["metric_target_id", "claim_role", "comparison_policy_id", "pass_condition"]),
            "",
            "## Route Decision",
            "",
            table(route_rows, ["route_id", "decision", "selected", "reason", "selected_next_unit"]),
            "",
            "## Claim Boundary",
            "",
            "- M173 is a contract/design artifact, not performance evidence.",
            "- Source-coverage-only remains a Pareto witness, not the selected method.",
            "- M174 must materialize rows and run leakage/order audits before any Docker trajectory execution.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m168 = read_json(M168_DIR / "coverage.json")
    m172 = read_json(M172_DIR / "coverage.json")
    candidate_rows = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")
    field_rows = build_field_availability_rows(candidate_rows)
    method_rows = build_method_contract_rows()
    utility_rows = build_utility_objective_rows()
    guard_rows = build_guard_contract_rows()
    input_rows = build_input_contract_rows()
    metric_rows = build_metric_target_rows()
    ablation_rows = build_ablation_contract_rows()
    disconfirmation_rows = build_disconfirmation_rows()
    materialization_rows = build_materialization_plan_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    missing_inputs: list[str] = []
    if m168.get("status") != "e008_m168_source_coverage_memory_interface_materialization_ready":
        missing_inputs.append("M168 ready coverage")
    if m172.get("status") != "e008_m172_source_coverage_ablation_tradeoff_decomposition_ready":
        missing_inputs.append("M172 ready coverage")
    if not candidate_rows:
        missing_inputs.append("M168 source_coverage_candidate_rows")
    missing_fields = [row["field"] for row in field_rows if not row["all_rows_ready"]]
    if missing_fields:
        missing_inputs.append("required fields: " + ",".join(missing_fields))

    ready = not missing_inputs
    selected_route = next(row for row in route_rows if row["selected"])
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing_inputs,
        "m168_status": m168.get("status"),
        "m172_status": m172.get("status"),
        "candidate_rows_audited": len(candidate_rows),
        "required_field_rows": len(field_rows),
        "required_fields_ready": all(row["all_rows_ready"] for row in field_rows),
        "method_contract_rows": len(method_rows),
        "utility_objective_rows": len(utility_rows),
        "guard_contract_rows": len(guard_rows),
        "input_contract_rows": len(input_rows),
        "metric_target_rows": len(metric_rows),
        "ablation_contract_rows": len(ablation_rows),
        "disconfirmation_rows": len(disconfirmation_rows),
        "materialization_plan_rows": len(materialization_rows),
        "claim_boundary_rows": len(claim_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "route_decision_rows": len(route_rows),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "source_coverage_witness_policy_id": SOURCE_COVERAGE_WITNESS,
        "previous_selected_policy_id": PREVIOUS_SELECTED,
        "source_coverage_only_delta_SPL_vs_detector": m172.get("source_coverage_only_delta_SPL_vs_detector"),
        "source_coverage_only_delta_CandidateVisits_vs_detector": m172.get("source_coverage_only_delta_CandidateVisits_vs_detector"),
        "source_coverage_only_tradeoff_witness": m172.get("source_coverage_only_tradeoff_witness"),
        "promote_source_coverage_only_as_main_method_now": False,
        "performance_claim_ready": False,
        "trajectory_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_route["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "field_availability_rows.jsonl", field_rows)
    write_jsonl(ARTIFACT_DIR / "method_contract_rows.jsonl", method_rows)
    write_jsonl(ARTIFACT_DIR / "utility_objective_rows.jsonl", utility_rows)
    write_jsonl(ARTIFACT_DIR / "guard_contract_rows.jsonl", guard_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "metric_target_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "ablation_contract_rows.jsonl", ablation_rows)
    write_jsonl(ARTIFACT_DIR / "disconfirmation_rows.jsonl", disconfirmation_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_plan_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, method_rows, utility_rows, guard_rows, metric_rows, route_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
