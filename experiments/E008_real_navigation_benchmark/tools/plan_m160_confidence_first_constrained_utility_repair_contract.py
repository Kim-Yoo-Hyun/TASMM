#!/usr/bin/env python3
"""Freeze the E008-M160 confidence-first constrained utility repair contract."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M159_DIR = EXP_ROOT / "artifacts" / "E008-M159_budget_aware_utility_component_failure_decomposition_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M160_confidence_first_constrained_utility_repair_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M160_confidence_first_constrained_utility_repair_contract_v0"
)

VERSION = "e008_m160_confidence_first_constrained_utility_repair_contract_v0"
READY_STATUS = "e008_m160_confidence_first_constrained_utility_repair_contract_ready"
BLOCKED_STATUS = "e008_m160_confidence_first_constrained_utility_repair_contract_blocked"
NEXT_UNIT = "E008-M161 confidence-first constrained repair row materialization smoke"

SELECTED_POLICY = "confidence_first_path_veto_tiebreak_repair_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
NEGATIVE_NO_CONFIDENCE = "budget_guarded_no_confidence_floor_v1"
TRADEOFF_NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"


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


def fmt(value: object) -> str:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{out:.6f}" if math.isfinite(out) else "NA"


def build_method_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_next_repair_contract",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "confidence_first_constrained_repair",
            "confidence_band_abs": 0.03,
            "max_rank_displacement_abs": 1,
            "min_path_advantage_m": 3.0,
            "visit_budget_delta_allowed": 0,
            "source_gap_trigger_scope": "prelabeled_source_gap_or_source_coverage_rows_only",
            "path_cost_scope": "hard_feasibility_veto_then_confidence_band_tiebreak_then_bounded_local_repair",
            "formula": "base=detector_confidence_order; demote no-path candidates; within confidence band and rank displacement <=1, promote only if path advantage >=3m and candidate-visit delta <=0; source-gap trigger may activate only on pre-labeled source-gap rows",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "M159 shows confidence floor survives, scalar path gain is harmful, source-gap/visit penalty are inert globally, and no-visit-guard is a visit-expensive tradeoff witness.",
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": PROTECTED_BASELINE,
            "policy_role": "protected_naive_baseline",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "detector_confidence_first",
            "confidence_band_abs": 0.0,
            "max_rank_displacement_abs": 0,
            "min_path_advantage_m": None,
            "visit_budget_delta_allowed": 0,
            "source_gap_trigger_scope": "none",
            "path_cost_scope": "none",
            "formula": "rank candidates by current evidence confidence after reachability filtering",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "This is the simplest current-evidence policy that M158/M159 failed to beat.",
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": NEGATIVE_NO_CONFIDENCE,
            "policy_role": "negative_control_ablation",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "remove_confidence_floor",
            "confidence_band_abs": None,
            "max_rank_displacement_abs": None,
            "min_path_advantage_m": None,
            "visit_budget_delta_allowed": None,
            "source_gap_trigger_scope": "not_selected",
            "path_cost_scope": "unprotected_path_priority",
            "formula": "ablation only; allow path priority without confidence floor",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "M159 uses this as evidence that confidence guard is necessary.",
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": TRADEOFF_NO_VISIT_GUARD,
            "policy_role": "tradeoff_witness_ablation",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "show_spl_visit_tradeoff",
            "confidence_band_abs": 0.03,
            "max_rank_displacement_abs": None,
            "min_path_advantage_m": None,
            "visit_budget_delta_allowed": None,
            "source_gap_trigger_scope": "diagnostic_only",
            "path_cost_scope": "diagnostic_unbounded_repair",
            "formula": "ablation only; remove visit guard to expose upper SPL tradeoff",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "M159 treats no-visit-guard as a Pareto witness, not a selectable method.",
        },
    ]


def build_repair_rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "base_order_initialization",
            "order": 1,
            "required": True,
            "condition": "always",
            "action": f"initialize order from `{PROTECTED_BASELINE}`",
            "blocked_if_missing": True,
        },
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "hard_feasibility_veto",
            "order": 2,
            "required": True,
            "condition": "candidate is not coordinate-valid, snapped navigable, source-ready, or path-ready",
            "action": "demote candidate below path-ready candidates before any utility repair",
            "blocked_if_missing": False,
        },
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "confidence_floor_guard",
            "order": 3,
            "required": True,
            "condition": "candidate confidence is outside confidence band relative to protected predecessor",
            "action": "block promotion over the higher-confidence candidate",
            "blocked_if_missing": True,
        },
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "path_tiebreak_only_inside_confidence_band",
            "order": 4,
            "required": True,
            "condition": "confidence difference <= 0.03 and local path advantage >= 3.0m",
            "action": "allow at most rank-displacement-1 local swap if candidate visits do not increase",
            "blocked_if_missing": True,
        },
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "source_gap_trigger",
            "order": 5,
            "required": True,
            "condition": "source_gap_flag is precomputed before evaluation and source-coverage expansion route is active",
            "action": "allow source-gap repair branch; otherwise source-gap bonus is zero",
            "blocked_if_missing": False,
        },
        {
            "version": VERSION,
            "row_type": "repair_rule",
            "rule_id": "budget_non_regression_guard",
            "order": 6,
            "required": True,
            "condition": "candidate visit count would exceed protected baseline visit count",
            "action": "block promotion for primary selected method; record only in tradeoff/Pareto ablation",
            "blocked_if_missing": True,
        },
    ]


def build_metric_target_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "protected_spl_no_extra_visits_v0",
            "target_role": "primary_positive_claim_gate",
            "comparison_policy_id": PROTECTED_BASELINE,
            "required_for_positive_claim": True,
            "pass_condition": "delta_SR >= 0 and delta_SPL > 0 and delta_CandidateVisits <= 0",
            "path_condition": "delta_PathLengthM <= 0 is preferred but not sufficient without SPL/visit gate",
            "why": "M158/M159 show a policy can manipulate path terms without improving protected SPL or visit efficiency.",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "component_value_gate_v0",
            "target_role": "ablation_gate",
            "comparison_policy_id": "ablation_without_each_component",
            "required_for_positive_claim": True,
            "pass_condition": "removing confidence guard must hurt; removing path repair/source-gap/budget guard must hurt the selected method on the precommitted target",
            "path_condition": "component rows must identify which cases are changed before execution",
            "why": "M159 shows path/source/visit components can be harmful or inert unless their case-level effect is audited.",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "pareto_tradeoff_report_v0",
            "target_role": "secondary_diagnostic",
            "comparison_policy_id": TRADEOFF_NO_VISIT_GUARD,
            "required_for_positive_claim": False,
            "pass_condition": "report SPL gain with candidate-visit cost, but do not use it as selected method unless user explicitly changes target",
            "path_condition": "show SR/SPL/visits/path length frontier",
            "why": "No-visit-guard is informative but not selectable as a posthoc method.",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "source_gap_trigger_audit_v0",
            "target_role": "diagnostic_gate",
            "comparison_policy_id": "source_gap_rows_only",
            "required_for_positive_claim": False,
            "pass_condition": "source-gap repair may be evaluated only on rows with precomputed source-gap or source-coverage flags",
            "path_condition": "target-free rows must not receive a global source-gap bonus",
            "why": "M159 found source-gap bonus inert on the current target-free denominator.",
        },
    ]


def build_allowed_input_rows() -> list[dict[str, Any]]:
    allowed = [
        ("candidate_confidence", "current proposal reliability"),
        ("candidate_position_m", "candidate geometry"),
        ("source_position_m", "current source/start pose"),
        ("path_ready", "precomputed navmesh/source-to-candidate reachability"),
        ("source_to_candidate_path_cost_m", "precomputed path cost from source to candidate"),
        ("protected_detector_rank", "base detector-confidence rank"),
        ("source_gap_flag", "precomputed source-gap/source-coverage state"),
        ("task_context_id", "structured task context only if policy contract enables it"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "reason": reason,
            "must_be_available_before_execution": True,
        }
        for field, reason in allowed
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    blocked = [
        ("ObjectNav eval goal position", "metric-only target label"),
        ("ObjectNav eval viewpoint position", "metric-only target label"),
        ("ObjectNav target object position", "metric-only target label"),
        ("trajectory_success", "post-execution outcome"),
        ("SPL", "post-execution metric"),
        ("StopRank", "post-execution metric"),
        ("success_candidate_to_eval_goal_xz_m", "posthoc target distance"),
        ("success_candidate_to_nearest_eval_viewpoint_xz_m", "posthoc target distance"),
        ("oracle_viewpoint_path_m", "metric upper-bound only"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "reason": reason,
            "failure_action": "fail_leakage_audit",
        }
        for field, reason in blocked
    ]


def build_ablation_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "ablation_id": "no_confidence_floor",
            "policy_id": NEGATIVE_NO_CONFIDENCE,
            "expected_failure": "SPL and candidate visits worsen because path/search cost overrides proposal reliability",
            "claim_role": "necessary_guard_negative_control",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "ablation_id": "path_cost_disabled",
            "policy_id": PROTECTED_BASELINE,
            "expected_failure": "selected repair should reduce to detector-confidence if no legitimate local path repair exists",
            "claim_role": "protected_baseline_comparison",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "ablation_id": "unbounded_path_repair_no_visit_guard",
            "policy_id": TRADEOFF_NO_VISIT_GUARD,
            "expected_failure": "may improve SPL by spending more candidate visits, therefore not selected",
            "claim_role": "pareto_tradeoff_witness",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "ablation_id": "global_source_gap_bonus_disabled",
            "policy_id": "source_gap_trigger_only_v1",
            "expected_failure": "global source-gap bonus should be inert or blocked on target-free rows",
            "claim_role": "source_gap_trigger_boundary",
        },
    ]


def build_readiness_gate_rows(m159_coverage: dict[str, Any], missing_inputs: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m159_ready",
            "gate_status": "pass"
            if m159_coverage.get("status") == "e008_m159_budget_aware_utility_component_failure_decomposition_ready"
            else "fail",
            "blocks_next": m159_coverage.get("status")
            != "e008_m159_budget_aware_utility_component_failure_decomposition_ready",
            "rationale": "M160 must start from M159 component failure diagnosis.",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "required_inputs_present",
            "gate_status": "pass" if not missing_inputs else "fail",
            "blocks_next": bool(missing_inputs),
            "rationale": f"missing_inputs={len(missing_inputs)}",
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "execution_needed_now",
            "gate_status": "pass",
            "blocks_next": False,
            "rationale": "M160 is a contract-only unit; no Docker or long job is launched.",
        },
    ]


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "next_unit": NEXT_UNIT,
            "input_root_candidates": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M155_budget_aware_utility_policy_materialization_smoke_v0/",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0/",
            ],
            "output_root": "experiments/E008_real_navigation_benchmark/artifacts/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/",
            "derived_output_root": "local_dataset/HM3D_navigation_bridge/E008-M161_confidence_first_constrained_repair_materialization_smoke_v0/",
            "required_outputs": [
                "confidence_first_candidate_rows.jsonl",
                "repair_component_rows.jsonl",
                "policy_order_audit_rows.jsonl",
                "leakage_audit_rows.jsonl",
                "claim_boundary_rows.jsonl",
                "report.md",
            ],
            "verification_command": "python -m py_compile experiments/E008_real_navigation_benchmark/tools/run_m161_confidence_first_constrained_repair_materialization.py && python experiments/E008_real_navigation_benchmark/tools/run_m161_confidence_first_constrained_repair_materialization.py",
            "launch_long_job_now": False,
        }
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "confidence_first_repair_contract_ready",
            "supported": True,
            "claim_boundary": "M160 fixes a pre-execution method/metric contract derived from M159 component failures.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_repair_navigation_improvement",
            "supported": False,
            "claim_boundary": "No repaired rows or trajectories have been materialized or executed yet.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Requires M161 materialization, trajectory execution, protected-baseline improvement, heldout transfer, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M160 is target-free and does not change the E006-M08 human-intent boundary.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "why_not_scale_m158_policy",
            "reviewer_response": "M159 shows the selected utility fails protected SPL/visit gates and has harmful or inert components, so scaling it would be conclusion-fitting.",
        },
        {
            "version": VERSION,
            "issue_id": "why_detector_confidence_first",
            "reviewer_response": "Detector-confidence is the strongest protected naive baseline in M158/M159; the repair must earn any deviation through constrained local evidence.",
        },
        {
            "version": VERSION,
            "issue_id": "why_path_cost_is_still_used",
            "reviewer_response": "Path cost is not used as a global additive score. It is restricted to feasibility veto, confidence-band tie-break, or bounded local repair.",
        },
        {
            "version": VERSION,
            "issue_id": "why_no_positive_claim_yet",
            "reviewer_response": "M160 is a contract-only unit. Positive navigation claims need materialized rows and Docker-executed trajectories against protected baselines.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_m158_selected_utility",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "M159 component failures block scaling the additive utility.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "select_no_visit_guard_as_method",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "No-visit-guard is a visit-expensive Pareto witness, not a precommitted selected method.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "confidence_first_constrained_repair_materialization",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The next executable step is row materialization under this fixed confidence-first repair contract.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but the internal selected method must first be materialized under a non-posthoc contract.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    m159_coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    ablation_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    status = READY_STATUS if not missing_inputs and all(not row["blocks_next"] for row in readiness_rows) else BLOCKED_STATUS
    return {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m159_status": m159_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "metric_target_id": "protected_spl_no_extra_visits_v0",
        "method_contract_rows": len(method_rows),
        "repair_rule_rows": len(repair_rows),
        "metric_target_rows": len(metric_rows),
        "allowed_input_rows": len(allowed_rows),
        "blocked_input_rows": len(blocked_rows),
        "ablation_contract_rows": len(ablation_rows),
        "readiness_gate_rows": len(readiness_rows),
        "positive_navigation_improvement_ready": False,
        "row_materialization_ready": status == READY_STATUS,
        "materialization_ready_next": status == READY_STATUS,
        "trajectory_execution_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": next(row["selected_next_unit"] for row in route_rows if row["selected"]),
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
            elif isinstance(value, list):
                value = ", ".join(str(item) for item in value) if value else "none"
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(
    coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected_route = next(row for row in route_rows if row["selected"])
    return "\n".join(
        [
            "# E008-M160 Confidence-First Constrained Utility Repair Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Input M159 status: `{coverage['m159_status']}`.",
            f"- Selected policy contract: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            f"- Row materialization ready: {coverage['row_materialization_ready']}.",
            f"- Trajectory execution ready: {coverage['trajectory_execution_ready']}.",
            "",
            "## Method Contract",
            "",
            markdown_table(
                method_rows,
                ["policy_id", "policy_role", "base_order_policy_id", "path_cost_scope", "visit_budget_delta_allowed"],
            ),
            "",
            "## Repair Rules",
            "",
            markdown_table(repair_rows, ["rule_id", "order", "condition", "action"]),
            "",
            "## Metric Targets",
            "",
            markdown_table(metric_rows, ["metric_target_id", "target_role", "pass_condition"]),
            "",
            "## Paper Claims",
            "",
            markdown_table(claim_rows, ["claim_id", "supported", "claim_boundary"]),
            "",
            "## Agent Inference",
            "",
            "- M160 converts the M159 negative result into a non-posthoc method contract.",
            "- The selected repair is narrower than the failed additive utility: detector-confidence first, confidence floor mandatory, path cost only as constrained repair, source gap only as trigger, and budget as a hard non-regression gate.",
            "- The next unit should materialize rows before any Docker trajectory execution.",
            "",
            "## Route Decision",
            "",
            f"- Selected route: `{selected_route['route_id']}`.",
            f"- Selected next unit: {selected_route['selected_next_unit']}.",
            f"- Reason: {selected_route['reason']}",
            "",
        ]
    )


def main() -> None:
    required = {
        "m159_coverage": M159_DIR / "coverage.json",
        "m159_component_rows": M159_DIR / "component_failure_rows.jsonl",
        "m159_contract_seed_rows": M159_DIR / "m160_contract_seed_rows.jsonl",
        "m159_principle_rows": M159_DIR / "principle_revision_rows.jsonl",
    }
    missing_inputs = [key for key, path in required.items() if not path.exists()]

    m159_coverage = read_json(required["m159_coverage"])
    method_rows = build_method_contract_rows()
    repair_rows = build_repair_rule_rows()
    metric_rows = build_metric_target_rows()
    allowed_rows = build_allowed_input_rows()
    blocked_rows = build_blocked_input_rows()
    ablation_rows = build_ablation_contract_rows()
    readiness_rows = build_readiness_gate_rows(m159_coverage, missing_inputs)
    materialization_rows = build_materialization_plan_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()
    coverage = build_coverage(
        m159_coverage,
        method_rows,
        repair_rows,
        metric_rows,
        allowed_rows,
        blocked_rows,
        ablation_rows,
        readiness_rows,
        route_rows,
        missing_inputs,
    )
    report = build_report(coverage, method_rows, repair_rows, metric_rows, claim_rows, route_rows)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "method_contract_rows.jsonl", method_rows)
    write_jsonl(ARTIFACT_DIR / "repair_rule_rows.jsonl", repair_rows)
    write_jsonl(ARTIFACT_DIR / "metric_target_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_rows.jsonl", allowed_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "ablation_contract_rows.jsonl", ablation_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_plan_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
