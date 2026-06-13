#!/usr/bin/env python3
"""Decompose E008-M158 budget-aware utility component failures."""

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
M157_DIR = EXP_ROOT / "artifacts" / "E008-M157_budget_aware_utility_trajectory_execution_v0"
M158_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M158_budget_aware_utility_trajectory_result_interpretation_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M159_budget_aware_utility_component_failure_decomposition_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M159_budget_aware_utility_component_failure_decomposition_v0"
)

VERSION = "e008_m159_budget_aware_utility_component_failure_decomposition_v0"
READY_STATUS = "e008_m159_budget_aware_utility_component_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m159_budget_aware_utility_component_failure_decomposition_blocked"
NEXT_UNIT = "E008-M160 confidence-first constrained utility repair contract / metric target decision"

METHOD_POLICY = "budget_aware_confidence_path_utility_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
NO_PATH_GAIN_ABLATION = "budget_aware_utility_without_path_gain_v0"
NO_SOURCE_GAP_ABLATION = "budget_aware_utility_without_source_gap_bonus_v0"
NO_VISIT_PENALTY_ABLATION = "budget_aware_utility_without_visit_penalty_v0"
NO_VISIT_GUARD_ABLATION = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR_ABLATION = "budget_guarded_no_confidence_floor_v1"


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
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def policy_rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in rows}


def summary_rows_by_baseline(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("baseline_policy_id")): row for row in rows}


def summarize_policy_order(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_id"))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for policy_id, group in grouped.items():
        out[policy_id] = {
            "policy_id": policy_id,
            "rows": len(group),
            "order_changed_rows": sum(bool(row.get("order_changed_vs_detector")) for row in group),
            "utility_positive_rows": sum(int(row.get("utility_positive_rows") or 0) for row in group),
            "utility_promotion_allowed_rows": sum(
                int(row.get("utility_promotion_allowed_rows") or 0) for row in group
            ),
            "max_rank_displacement_abs_from_detector": max(
                [int(row.get("max_rank_displacement_abs_from_detector") or 0) for row in group],
                default=0,
            ),
            "audit_pass_rows": sum(bool(row.get("audit_pass")) for row in group),
        }
    return out


def summarize_utility_components(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_id"))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for policy_id, group in grouped.items():
        out[policy_id] = {
            "policy_id": policy_id,
            "rows": len(group),
            "utility_promote_candidate_rows": sum(bool(row.get("utility_promote_candidate")) for row in group),
            "utility_promotion_allowed_rows": sum(bool(row.get("utility_promotion_allowed")) for row in group),
            "source_gap_prelabel_rows": sum(bool(row.get("source_gap_prelabel")) for row in group),
            "path_advantage_nonzero_rows": sum(
                abs(finite_float(row.get("local_path_advantage_m")) or 0.0) > 1e-9 for row in group
            ),
            "planned_extra_visit_nonzero_rows": sum(
                abs(finite_float(row.get("planned_extra_visit_norm")) or 0.0) > 1e-9 for row in group
            ),
        }
    return out


def summarize_candidates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_id"))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for policy_id, group in grouped.items():
        out[policy_id] = {
            "policy_id": policy_id,
            "rows": len(group),
            "path_repair_applied_rows": sum(bool(row.get("path_repair_applied")) for row in group),
            "source_gap_branch_rows": sum(bool(row.get("source_gap_recovery_branch_active")) for row in group),
            "visit_budget_guard_active_rows": sum(bool(row.get("visit_budget_guard_active")) for row in group),
            "rank_displacement_nonzero_rows": sum(
                abs(int(row.get("rank_displacement_from_detector") or 0)) > 0 for row in group
            ),
            "method_policy_rows": sum(bool(row.get("method_policy")) for row in group),
        }
    return out


def component_row(
    component_id: str,
    component_status: str,
    evidence_status: str,
    paper_decision: str,
    materialization: dict[str, Any],
    execution: dict[str, Any],
    diagnosis: str,
    next_requirement: str,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "row_type": "component_failure",
        "component_id": component_id,
        "component_status": component_status,
        "evidence_status": evidence_status,
        "paper_decision": paper_decision,
        "materialization": materialization,
        "execution": execution,
        "failure_diagnosis": diagnosis,
        "next_method_requirement": next_requirement,
        "supports_positive_navigation_improvement": False,
        "supports_final_navigation_claim": False,
    }


def build_component_failure_rows(
    policy: dict[str, dict[str, Any]],
    pairwise: dict[str, dict[str, Any]],
    order: dict[str, dict[str, Any]],
    components: dict[str, dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    method = policy.get(METHOD_POLICY, {})
    detector = policy.get(PRIMARY_BASELINE, {})
    no_path = policy.get(NO_PATH_GAIN_ABLATION, {})
    no_source = policy.get(NO_SOURCE_GAP_ABLATION, {})
    no_visit_penalty = policy.get(NO_VISIT_PENALTY_ABLATION, {})
    no_visit_guard = policy.get(NO_VISIT_GUARD_ABLATION, {})
    no_conf = policy.get(NO_CONFIDENCE_FLOOR_ABLATION, {})

    return [
        component_row(
            "protected_detector_confidence_base",
            "supported_as_naive_baseline",
            "protected_baseline_not_beaten",
            "keep_as_required_baseline_and_starting_order",
            {
                "detector_order_changed_rows": order.get(PRIMARY_BASELINE, {}).get("order_changed_rows"),
                "selected_order_changed_rows": order.get(METHOD_POLICY, {}).get("order_changed_rows"),
            },
            {
                "method_SR": method.get("SR"),
                "detector_SR": detector.get("SR"),
                "method_SPL": method.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "delta_SPL_vs_detector": method.get("delta_SPL_vs_detector_confidence"),
            },
            "The selected utility does not beat the simplest reachable detector-confidence policy.",
            "M160 must preserve detector confidence as the protected base order and only allow constrained repairs.",
        ),
        component_row(
            "confidence_floor_guard",
            "supported",
            "negative_control_pass",
            "keep",
            {
                "no_confidence_floor_order_changed_rows": order.get(NO_CONFIDENCE_FLOOR_ABLATION, {}).get(
                    "order_changed_rows"
                ),
                "no_confidence_floor_max_rank_displacement": order.get(NO_CONFIDENCE_FLOOR_ABLATION, {}).get(
                    "max_rank_displacement_abs_from_detector"
                ),
            },
            {
                "no_confidence_floor_SPL": no_conf.get("SPL"),
                "no_confidence_floor_CandidateVisits_mean": no_conf.get("CandidateVisits_mean"),
                "delta_SPL_selected_vs_no_confidence_floor": pairwise.get(NO_CONFIDENCE_FLOOR_ABLATION, {}).get(
                    "delta_SPL_mean"
                ),
                "delta_CandidateVisits_selected_vs_no_confidence_floor": pairwise.get(
                    NO_CONFIDENCE_FLOOR_ABLATION, {}
                ).get("delta_CandidateVisits_mean"),
            },
            "Removing the confidence floor sharply reduces SPL and increases candidate visits.",
            "M160 must keep a confidence floor or confidence band before any path/search-cost intervention.",
        ),
        component_row(
            "scalar_path_gain",
            "harmful_in_current_form",
            "component_value_fail",
            "demote_to_guarded_veto_or_tie_break_only",
            {
                "selected_order_changed_rows": order.get(METHOD_POLICY, {}).get("order_changed_rows"),
                "selected_utility_promotion_allowed_rows": order.get(METHOD_POLICY, {}).get(
                    "utility_promotion_allowed_rows"
                ),
                "without_path_gain_order_changed_rows": order.get(NO_PATH_GAIN_ABLATION, {}).get(
                    "order_changed_rows"
                ),
                "selected_path_repair_applied_rows": candidates.get(METHOD_POLICY, {}).get(
                    "path_repair_applied_rows"
                ),
                "without_path_gain_path_repair_applied_rows": candidates.get(NO_PATH_GAIN_ABLATION, {}).get(
                    "path_repair_applied_rows"
                ),
                "path_advantage_nonzero_rows": components.get(METHOD_POLICY, {}).get("path_advantage_nonzero_rows"),
            },
            {
                "method_SPL": method.get("SPL"),
                "without_path_gain_SPL": no_path.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "delta_SPL_selected_vs_without_path_gain": pairwise.get(NO_PATH_GAIN_ABLATION, {}).get(
                    "delta_SPL_mean"
                ),
                "delta_CandidateVisits_selected_vs_without_path_gain": pairwise.get(
                    NO_PATH_GAIN_ABLATION, {}
                ).get("delta_CandidateVisits_mean"),
            },
            "Path-gain promotions changed 17 rows, but removing path gain matches detector-confidence and improves the selected utility on aggregate.",
            "M160 may use path cost only as a hard feasibility veto, confidence-band tie-break, or bounded repair condition; not as a global additive bonus.",
        ),
        component_row(
            "source_gap_bonus",
            "inert_on_current_denominator",
            "component_value_fail",
            "replace_global_bonus_with_source_gap_trigger",
            {
                "source_gap_prelabel_rows": components.get(METHOD_POLICY, {}).get("source_gap_prelabel_rows"),
                "selected_source_gap_branch_rows": candidates.get(METHOD_POLICY, {}).get("source_gap_branch_rows"),
                "without_source_gap_order_changed_rows": order.get(NO_SOURCE_GAP_ABLATION, {}).get(
                    "order_changed_rows"
                ),
            },
            {
                "method_SPL": method.get("SPL"),
                "without_source_gap_bonus_SPL": no_source.get("SPL"),
                "delta_SPL_selected_vs_without_source_gap": pairwise.get(NO_SOURCE_GAP_ABLATION, {}).get(
                    "delta_SPL_mean"
                ),
                "delta_CandidateVisits_selected_vs_without_source_gap": pairwise.get(
                    NO_SOURCE_GAP_ABLATION, {}
                ).get("delta_CandidateVisits_mean"),
            },
            "No source-gap prelabel or source-gap branch is activated in the current materialized denominator, and removing the bonus is exactly equivalent.",
            "M160 should treat source gap as a trigger for re-observation/source expansion only when source-gap evidence exists.",
        ),
        component_row(
            "visit_penalty_scalar",
            "inert_on_current_denominator",
            "component_value_fail",
            "replace_with_explicit_budget_constraint_or_pareto_metric",
            {
                "planned_extra_visit_nonzero_rows": components.get(METHOD_POLICY, {}).get(
                    "planned_extra_visit_nonzero_rows"
                ),
                "without_visit_penalty_order_changed_rows": order.get(NO_VISIT_PENALTY_ABLATION, {}).get(
                    "order_changed_rows"
                ),
                "selected_visit_budget_guard_active_rows": candidates.get(METHOD_POLICY, {}).get(
                    "visit_budget_guard_active_rows"
                ),
            },
            {
                "method_SPL": method.get("SPL"),
                "without_visit_penalty_SPL": no_visit_penalty.get("SPL"),
                "delta_SPL_selected_vs_without_visit_penalty": pairwise.get(NO_VISIT_PENALTY_ABLATION, {}).get(
                    "delta_SPL_mean"
                ),
                "delta_CandidateVisits_selected_vs_without_visit_penalty": pairwise.get(
                    NO_VISIT_PENALTY_ABLATION, {}
                ).get("delta_CandidateVisits_mean"),
            },
            "The scalar visit penalty does not change the selected policy relative to its ablation.",
            "M160 must precommit budget either as a hard visit cap or as an explicit reported Pareto/utility target.",
        ),
        component_row(
            "visit_guard",
            "tradeoff_witness",
            "warning_not_selectable_posthoc",
            "keep_as_ablation_not_method",
            {
                "no_visit_guard_order_changed_rows": order.get(NO_VISIT_GUARD_ABLATION, {}).get(
                    "order_changed_rows"
                ),
                "no_visit_guard_rank_displacement_nonzero_rows": candidates.get(NO_VISIT_GUARD_ABLATION, {}).get(
                    "rank_displacement_nonzero_rows"
                ),
                "no_visit_guard_max_rank_displacement": order.get(NO_VISIT_GUARD_ABLATION, {}).get(
                    "max_rank_displacement_abs_from_detector"
                ),
            },
            {
                "no_visit_guard_SPL": no_visit_guard.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "no_visit_guard_delta_SPL_vs_detector": no_visit_guard.get("delta_SPL_vs_detector_confidence"),
                "no_visit_guard_delta_CandidateVisits_vs_detector": no_visit_guard.get(
                    "delta_CandidateVisits_mean_vs_detector_confidence"
                ),
                "selected_delta_SPL_vs_no_visit_guard": pairwise.get(NO_VISIT_GUARD_ABLATION, {}).get(
                    "delta_SPL_mean"
                ),
                "selected_delta_CandidateVisits_vs_no_visit_guard": pairwise.get(NO_VISIT_GUARD_ABLATION, {}).get(
                    "delta_CandidateVisits_mean"
                ),
            },
            "Removing the visit guard gives the best SPL but spends more visits, so it exposes the budget/SPL conflict rather than a selectable method.",
            "M160 must define whether the target is protected SPL at no extra visits, or a precommitted utility/Pareto frontier with a budget cost.",
        ),
    ]


def build_failure_mechanism_rows(component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "protected_detector_confidence_not_beaten",
            "severity": "high",
            "fact": "The selected utility ties detector-confidence on SR but loses SPL, path length, and candidate visits.",
            "agent_inference": "The method form is not yet a navigation-improving semantic-memory policy.",
            "next_validation_requirement": "Keep detector-confidence as the protected baseline in M160 and require non-negative protected-baseline deltas.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "path_gain_promotes_wrong_tradeoff",
            "severity": "high",
            "fact": "Removing path gain matches detector-confidence, while selected path-gain utility is worse on aggregate.",
            "agent_inference": "Path/search cost is useful only under a constrained confidence-first interface, not as a global score bonus.",
            "next_validation_requirement": "Convert path cost to veto/tie-break/repair trigger and audit the rows it changes before execution.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "source_gap_bonus_not_activated",
            "severity": "medium",
            "fact": "Source-gap bonus has zero observed effect on the M155/M157 denominator.",
            "agent_inference": "The current denominator tests target-free detector candidates, not a source-gap-triggered re-observation policy.",
            "next_validation_requirement": "Use source-gap only when the row is labeled as source-gap or when a source-coverage expansion route is selected.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "visit_penalty_not_binding",
            "severity": "medium",
            "fact": "The visit-penalty ablation is identical to the selected utility.",
            "agent_inference": "A weak scalar penalty cannot resolve the SPL/search-budget conflict.",
            "next_validation_requirement": "Use a hard visit budget or precommitted utility/Pareto objective before another execution run.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "confidence_floor_survives",
            "severity": "low",
            "fact": "The no-confidence-floor ablation sharply worsens SPL.",
            "agent_inference": "Confidence remains a necessary reliability guard for open-vocabulary proposal noise.",
            "next_validation_requirement": "Do not remove confidence floor in repaired policies.",
        },
    ]


def build_principle_revision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "confidence_first_constrained_repair",
            "revised_principle": "Dynamic semantic memory should start from current-evidence confidence and permit path/search-cost interventions only when they are confidence-preserving and budget-bounded.",
            "method_form_implication": "Use detector-confidence as the base order, keep confidence floor, then apply local veto/tie-break/repair rules.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "path_cost_not_global_score",
            "revised_principle": "Path/search cost should explain reachability or local order ties, not override proposal reliability globally.",
            "method_form_implication": "Path cost may be a hard feasibility veto, confidence-band tie-break, or bounded local repair only.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "source_gap_as_trigger",
            "revised_principle": "Source-gap evidence should trigger re-observation or source expansion, not add a universal ranking bonus.",
            "method_form_implication": "Use source-gap labels only for source-gap rows and keep target-free rows confidence-first.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "budget_as_constraint",
            "revised_principle": "Search effort must be constrained or explicitly traded off; otherwise an SPL gain can be bought by more visits.",
            "method_form_implication": "M160 must define a protected SR/SPL gate and a separate visit/path-cost utility or Pareto frontier.",
        },
    ]


def build_m160_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "base_order",
            "decision": "detector_confidence_first",
            "requirement": "The repaired policy starts from `detector_confidence_reachable_subset_v0` and may change order only under explicit guards.",
        },
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "confidence_guard",
            "decision": "mandatory",
            "requirement": "Keep confidence floor / confidence band because the no-confidence-floor ablation fails.",
        },
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "path_cost",
            "decision": "veto_or_tie_break_only",
            "requirement": "Do not use scalar path gain as a global additive bonus; use it only as hard feasibility veto, confidence-band tie-break, or bounded local repair.",
        },
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "source_gap",
            "decision": "trigger_only",
            "requirement": "No global source-gap bonus on target-free rows; use source-gap only for rows with source-gap evidence or source-coverage expansion.",
        },
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "budget_metric",
            "decision": "precommit_metric_target",
            "requirement": "Before execution, choose whether the target is protected SPL with no extra visits or a reported utility/Pareto tradeoff.",
        },
        {
            "version": VERSION,
            "row_type": "m160_contract_seed",
            "contract_item": "positive_claim_gate",
            "decision": "strict",
            "requirement": "A repaired policy cannot support a positive claim unless it beats or ties detector-confidence on SR/SPL and does not worsen the precommitted budget target.",
        },
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "budget_aware_utility_component_diagnostic",
            True,
            "M159 decomposes which M154/M155/M157 utility components are supported, harmful, inert, or tradeoff-only.",
        ),
        claim(
            "confidence_floor_needed",
            True,
            "Supported within the M157/M158 diagnostic table by the no-confidence-floor negative control.",
        ),
        claim(
            "selected_budget_aware_utility_navigation_improvement",
            False,
            "Blocked because selected utility loses protected SPL and visit efficiency to detector-confidence.",
        ),
        claim(
            "scalar_path_gain_component_supported",
            False,
            "Blocked because no-path-gain matches detector-confidence and is better than selected utility.",
        ),
        claim(
            "source_gap_bonus_component_supported",
            False,
            "Blocked on the current denominator because source-gap bonus has no observed effect.",
        ),
        claim(
            "visit_penalty_component_supported",
            False,
            "Blocked on the current denominator because the visit-penalty ablation is equivalent.",
        ),
        claim(
            "no_visit_guard_as_selected_method",
            False,
            "Blocked because it is a posthoc tradeoff witness with higher candidate visits.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Still requires a repaired selected method, heldout transfer, external navigation/search baselines, and failure analysis.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M159 is target-free and does not change the E006-M08 human-intent boundary.",
        ),
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "are_you_fitting_to_negative_results",
            "reviewer_response": "No. The positive selected-policy claim is rejected, and M159 records component failures before any repair contract.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_use_path_gain_anyway",
            "reviewer_response": "Because the path-gain term changed order but worsened the protected baseline comparison. It can only return as a constrained veto/tie-break/repair signal.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_pick_no_visit_guard",
            "reviewer_response": "It has the best SPL but higher visits, so it is a Pareto witness rather than a precommitted method.",
        },
        {
            "version": VERSION,
            "issue_id": "why_is_source_gap_not_the_main_fix",
            "reviewer_response": "The current denominator contains no activated source-gap branch for this utility, so global source-gap bonus evidence is absent.",
        },
        {
            "version": VERSION,
            "issue_id": "what_survives_as_novelty_principle",
            "reviewer_response": "The supported principle is narrower: confidence-first semantic memory with constrained re-observation/path-cost repair, not a free-form additive utility.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "claim_selected_budget_aware_utility",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Selected utility loses protected SPL and visit efficiency to detector-confidence.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "scale_selected_budget_aware_utility",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Scaling a component-failing policy would violate the novelty discipline.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "promote_no_visit_guard_as_method",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "No-visit-guard is posthoc and visit-expensive despite best SPL.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but the internal repair contract should be narrowed first.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "confidence_first_constrained_utility_repair_contract",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "M159 shows the next method must be confidence-first, path-cost-constrained, source-gap-triggered, and budget-precommitted.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    m155_coverage: dict[str, Any],
    m157_coverage: dict[str, Any],
    m158_coverage: dict[str, Any],
    component_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    principle_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    supported = [row["component_id"] for row in component_rows if row["component_status"] == "supported"]
    harmful = [
        row["component_id"]
        for row in component_rows
        if row["component_status"] in {"harmful_in_current_form", "inert_on_current_denominator"}
    ]
    tradeoff = [row["component_id"] for row in component_rows if row["component_status"] == "tradeoff_witness"]
    status = READY_STATUS if not missing_inputs else BLOCKED_STATUS
    return {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m155_status": m155_coverage.get("status"),
        "m157_status": m157_coverage.get("status"),
        "m158_status": m158_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "component_failure_rows": len(component_rows),
        "failure_mechanism_rows": len(mechanism_rows),
        "principle_revision_rows": len(principle_rows),
        "m160_contract_seed_rows": len(contract_rows),
        "supported_component_ids": supported,
        "rejected_or_inert_component_ids": harmful,
        "tradeoff_component_ids": tradeoff,
        "positive_navigation_improvement_ready": False,
        "component_repair_contract_required": True,
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
            elif isinstance(value, dict):
                value = "; ".join(f"{key}={value[key]}" for key in sorted(value))
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(
    coverage: dict[str, Any],
    component_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    principle_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected_route = next(row for row in route_rows if row["selected"])
    return "\n".join(
        [
            "# E008-M159 Budget-Aware Utility Component Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Input M155 status: `{coverage['m155_status']}`.",
            f"- Input M157 status: `{coverage['m157_status']}`.",
            f"- Input M158 status: `{coverage['m158_status']}`.",
            f"- Component rows: {coverage['component_failure_rows']}.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            f"- Final real navigation `SR` / `SPL` ready: {coverage['final_real_navigation_sr_spl_ready']}.",
            "",
            "## Component Decomposition",
            "",
            markdown_table(
                component_rows,
                ["component_id", "component_status", "evidence_status", "paper_decision"],
            ),
            "",
            "## Failure Mechanisms",
            "",
            markdown_table(
                mechanism_rows,
                ["mechanism_id", "severity", "fact", "next_validation_requirement"],
            ),
            "",
            "## Principle Revision",
            "",
            markdown_table(
                principle_rows,
                ["principle_id", "revised_principle", "method_form_implication"],
            ),
            "",
            "## M160 Contract Seed",
            "",
            markdown_table(contract_rows, ["contract_item", "decision", "requirement"]),
            "",
            "## Paper Claims",
            "",
            markdown_table(claim_rows, ["claim_id", "supported", "claim_boundary"]),
            "",
            "## Agent Inference",
            "",
            "- The current failure does not mean path/search cost is irrelevant. It means the additive path-gain utility is mis-specified for `SR` / `SPL` and search budget.",
            "- The next method form should be narrower: confidence-first ordering, confidence floor, path cost only as veto/tie-break/repair, source-gap only as trigger, and explicit budget target.",
            "- No positive navigation claim should be made before M160 fixes the contract and a later execution beats the protected detector-confidence baseline.",
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
        "m155_coverage": M155_DIR / "coverage.json",
        "m155_policy_order_audit": M155_DIR / "policy_order_audit_rows.jsonl",
        "m155_utility_components": M155_DIR / "utility_component_rows.jsonl",
        "m155_candidate_rows": M155_DIR / "budget_aware_candidate_rows.jsonl",
        "m157_coverage": M157_DIR / "coverage.json",
        "m158_coverage": M158_DIR / "coverage.json",
        "m158_policy_results": M158_DIR / "policy_result_interpretation_rows.jsonl",
        "m158_pairwise_summary": M158_DIR / "pairwise_delta_summary_rows.jsonl",
    }
    missing_inputs = [key for key, path in required.items() if not path.exists()]

    m155_coverage = read_json(required["m155_coverage"])
    m157_coverage = read_json(required["m157_coverage"])
    m158_coverage = read_json(required["m158_coverage"])
    policy_results = read_jsonl(required["m158_policy_results"])
    pairwise_summary = read_jsonl(required["m158_pairwise_summary"])
    policy_order = read_jsonl(required["m155_policy_order_audit"])
    utility_components = read_jsonl(required["m155_utility_components"])
    candidate_rows = read_jsonl(required["m155_candidate_rows"])

    policy = policy_rows_by_id(policy_results)
    pairwise = summary_rows_by_baseline(pairwise_summary)
    order_summary = summarize_policy_order(policy_order)
    component_summary = summarize_utility_components(utility_components)
    candidate_summary = summarize_candidates(candidate_rows)

    component_rows = build_component_failure_rows(
        policy, pairwise, order_summary, component_summary, candidate_summary
    )
    mechanism_rows = build_failure_mechanism_rows(component_rows)
    principle_rows = build_principle_revision_rows()
    contract_rows = build_m160_contract_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()
    coverage = build_coverage(
        m155_coverage,
        m157_coverage,
        m158_coverage,
        component_rows,
        mechanism_rows,
        principle_rows,
        contract_rows,
        route_rows,
        missing_inputs,
    )
    report = build_report(
        coverage,
        component_rows,
        mechanism_rows,
        principle_rows,
        contract_rows,
        claim_rows,
        route_rows,
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "component_failure_rows.jsonl", component_rows)
    write_jsonl(ARTIFACT_DIR / "failure_mechanism_rows.jsonl", mechanism_rows)
    write_jsonl(ARTIFACT_DIR / "principle_revision_rows.jsonl", principle_rows)
    write_jsonl(ARTIFACT_DIR / "m160_contract_seed_rows.jsonl", contract_rows)
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
