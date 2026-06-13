#!/usr/bin/env python3
"""Decompose E008-M164 confidence-first constrained repair failures."""

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
M161_DIR = EXP_ROOT / "artifacts" / "E008-M161_confidence_first_constrained_repair_materialization_smoke_v0"
M163_DIR = EXP_ROOT / "artifacts" / "E008-M163_confidence_first_constrained_repair_trajectory_execution_v0"
M164_DIR = EXP_ROOT / "artifacts" / "E008-M164_confidence_first_constrained_repair_result_interpretation_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M165_confidence_first_repair_failure_decomposition_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M165_confidence_first_repair_failure_decomposition_v0"
)

VERSION = "e008_m165_confidence_first_repair_failure_decomposition_v0"
READY_STATUS = "e008_m165_confidence_first_repair_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m165_confidence_first_repair_failure_decomposition_blocked"
NEXT_UNIT = "E008-M166 navigation failure-boundary package and method-pivot contract"

METHOD_POLICY = "confidence_first_path_veto_tiebreak_repair_v1"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
NO_PATH_TIEBREAK = "confidence_first_no_path_tiebreak_v1"
SOURCE_GAP_ONLY = "source_gap_trigger_only_v1"
NO_VISIT_GUARD = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR = "budget_guarded_no_confidence_floor_v1"


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


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def metric_rows_by_episode(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row.get("metric_scope") == "scan_task_policy":
            grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row
    return grouped


def policy_aggregates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def method_order_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("benchmark_row_uid")): row
        for row in rows
        if row.get("policy_id") == METHOD_POLICY
    }


def summarize_repair_components(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failed_guards: Counter[str] = Counter()
    for row in rows:
        for guard in row.get("failed_guards") or []:
            failed_guards[str(guard)] += 1
    return {
        "repair_component_rows": len(rows),
        "promotion_allowed_rows": sum(bool(row.get("promotion_allowed")) for row in rows),
        "source_gap_prelabel_rows": sum(bool(row.get("source_gap_prelabel")) for row in rows),
        "path_tiebreak_guard_pass_rows": sum(bool(row.get("path_tiebreak_guard_pass")) for row in rows),
        "confidence_floor_guard_pass_rows": sum(bool(row.get("confidence_floor_guard_pass")) for row in rows),
        "hard_feasibility_veto_pass_rows": sum(bool(row.get("hard_feasibility_veto_pass")) for row in rows),
        "failed_guard_counts": dict(sorted(failed_guards.items())),
    }


def classify_episode(delta_spl: float | None, delta_visits: float | None, order_changed: bool) -> str:
    spl = delta_spl or 0.0
    visits = delta_visits or 0.0
    if not order_changed:
        return "order_unchanged_control"
    if spl < -1e-9 and visits > 1e-9:
        return "harmful_extra_pre_success_visits"
    if spl < -1e-9:
        return "harmful_spl_regression"
    if spl > 1e-9 and visits <= 1e-9:
        return "local_swap_useful_but_sparse"
    if spl > 1e-9 and visits > 1e-9:
        return "spl_gain_with_visit_cost"
    if visits > 1e-9:
        return "visit_regression_without_spl_gain"
    return "neutral_tie"


def build_episode_failure_profile_rows(
    metric_by_episode: dict[str, dict[str, dict[str, Any]]],
    order_by_episode: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for uid in sorted(metric_by_episode):
        policies = metric_by_episode[uid]
        method = policies.get(METHOD_POLICY, {})
        detector = policies.get(PRIMARY_BASELINE, {})
        no_visit = policies.get(NO_VISIT_GUARD, {})
        order = order_by_episode.get(uid, {})
        delta_spl = delta(method.get("SPL"), detector.get("SPL"))
        delta_visits = delta(method.get("CandidateVisits"), detector.get("CandidateVisits"))
        delta_path = delta(method.get("PathLengthM"), detector.get("PathLengthM"))
        no_visit_delta_spl = delta(no_visit.get("SPL"), detector.get("SPL"))
        no_visit_delta_visits = delta(no_visit.get("CandidateVisits"), detector.get("CandidateVisits"))
        order_changed = bool(order.get("order_changed_vs_detector"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "episode_failure_profile",
                "benchmark_row_uid": uid,
                "scan_id": method.get("scan_id") or detector.get("scan_id"),
                "scene_key": method.get("scene_key") or detector.get("scene_key"),
                "object_category": method.get("object_category") or detector.get("object_category"),
                "order_changed_vs_detector": order_changed,
                "local_swap_promoted_rows": order.get("local_swap_promoted_rows", 0),
                "local_swap_demoted_rows": order.get("local_swap_demoted_rows", 0),
                "max_rank_displacement_abs_from_detector": order.get("max_rank_displacement_abs_from_detector", 0),
                "selected_SR": method.get("SR"),
                "detector_SR": detector.get("SR"),
                "selected_SPL": method.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "selected_CandidateVisits": method.get("CandidateVisits"),
                "detector_CandidateVisits": detector.get("CandidateVisits"),
                "selected_PathLengthM": method.get("PathLengthM"),
                "detector_PathLengthM": detector.get("PathLengthM"),
                "delta_SR_vs_detector": delta(method.get("SR"), detector.get("SR")),
                "delta_SPL_vs_detector": delta_spl,
                "delta_CandidateVisits_vs_detector": delta_visits,
                "delta_PathLengthM_vs_detector": delta_path,
                "selected_success_proposal_changed_vs_detector": method.get("success_proposal_uid")
                != detector.get("success_proposal_uid"),
                "selected_failure_type_changed_vs_detector": method.get("FailureType")
                != detector.get("FailureType"),
                "no_visit_guard_delta_SPL_vs_detector": no_visit_delta_spl,
                "no_visit_guard_delta_CandidateVisits_vs_detector": no_visit_delta_visits,
                "no_visit_guard_success_proposal_changed_vs_detector": no_visit.get("success_proposal_uid")
                != detector.get("success_proposal_uid"),
                "classification": classify_episode(delta_spl, delta_visits, order_changed),
            }
        )
    return rows


def summarize_episode_profiles(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classifications = Counter(str(row.get("classification")) for row in rows)
    changed = [row for row in rows if row.get("order_changed_vs_detector")]
    unchanged = [row for row in rows if not row.get("order_changed_vs_detector")]
    return {
        "episode_rows": len(rows),
        "changed_episode_rows": len(changed),
        "unchanged_episode_rows": len(unchanged),
        "classification_counts": dict(sorted(classifications.items())),
        "selected_success_proposal_changed_rows": sum(
            bool(row.get("selected_success_proposal_changed_vs_detector")) for row in rows
        ),
        "selected_failure_type_changed_rows": sum(
            bool(row.get("selected_failure_type_changed_vs_detector")) for row in rows
        ),
        "selected_better_spl_rows": sum((finite_float(row.get("delta_SPL_vs_detector")) or 0.0) > 1e-9 for row in rows),
        "selected_worse_spl_rows": sum((finite_float(row.get("delta_SPL_vs_detector")) or 0.0) < -1e-9 for row in rows),
        "selected_tie_spl_rows": sum(
            abs(finite_float(row.get("delta_SPL_vs_detector")) or 0.0) <= 1e-9 for row in rows
        ),
        "selected_more_visit_rows": sum(
            (finite_float(row.get("delta_CandidateVisits_vs_detector")) or 0.0) > 1e-9 for row in rows
        ),
        "selected_fewer_visit_rows": sum(
            (finite_float(row.get("delta_CandidateVisits_vs_detector")) or 0.0) < -1e-9 for row in rows
        ),
        "selected_delta_SPL_mean": mean([finite_float(row.get("delta_SPL_vs_detector")) for row in rows]),
        "selected_delta_CandidateVisits_mean": mean(
            [finite_float(row.get("delta_CandidateVisits_vs_detector")) for row in rows]
        ),
        "selected_delta_PathLengthM_mean": mean([finite_float(row.get("delta_PathLengthM_vs_detector")) for row in rows]),
        "changed_delta_SPL_mean": mean([finite_float(row.get("delta_SPL_vs_detector")) for row in changed]),
        "changed_delta_CandidateVisits_mean": mean(
            [finite_float(row.get("delta_CandidateVisits_vs_detector")) for row in changed]
        ),
        "no_visit_guard_success_proposal_changed_rows": sum(
            bool(row.get("no_visit_guard_success_proposal_changed_vs_detector")) for row in rows
        ),
    }


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
    m161: dict[str, Any],
    m164: dict[str, Any],
    repair_summary: dict[str, Any],
    episode_summary: dict[str, Any],
    aggregates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    method = aggregates.get(METHOD_POLICY, {})
    detector = aggregates.get(PRIMARY_BASELINE, {})
    no_path = aggregates.get(NO_PATH_TIEBREAK, {})
    source_gap = aggregates.get(SOURCE_GAP_ONLY, {})
    no_visit = aggregates.get(NO_VISIT_GUARD, {})
    no_conf = aggregates.get(NO_CONFIDENCE_FLOOR, {})
    return [
        component_row(
            "protected_detector_confidence_base",
            "supported_as_required_baseline",
            "protected_baseline_not_beaten",
            "keep_as_primary_naive_baseline",
            {
                "base_detector_candidate_rows": m161.get("base_detector_candidate_rows"),
                "selected_changed_episode_rows": m161.get("selected_changed_episode_rows"),
                "selected_local_swap_promoted_rows": m161.get("selected_local_swap_promoted_rows"),
            },
            {
                "method_SR": method.get("SR"),
                "detector_SR": detector.get("SR"),
                "method_SPL": method.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "method_delta_SPL_vs_detector": m164.get("method_delta_SPL_vs_detector_confidence"),
                "method_delta_CandidateVisits_vs_detector": m164.get(
                    "method_delta_CandidateVisits_vs_detector_confidence"
                ),
            },
            "The selected repair does not beat the simplest reachable detector-confidence order.",
            "Keep detector-confidence as the protected baseline for any later route.",
        ),
        component_row(
            "confidence_floor_guard",
            "supported_diagnostic",
            "negative_control_pass",
            "keep_as_guard_not_standalone_contribution",
            {
                "confidence_floor_guard_pass_rows": repair_summary.get("confidence_floor_guard_pass_rows"),
                "hard_feasibility_veto_pass_rows": repair_summary.get("hard_feasibility_veto_pass_rows"),
            },
            {
                "no_confidence_floor_SPL": no_conf.get("SPL"),
                "no_confidence_floor_CandidateVisits_mean": no_conf.get("CandidateVisits_mean"),
                "selected_delta_SPL_vs_no_confidence_floor": (
                    (method.get("SPL") or 0.0) - (no_conf.get("SPL") or 0.0)
                ),
            },
            "Removing confidence floor sharply degrades SPL and visits, so reliability guard is necessary.",
            "Retain confidence floor in future policy, but do not claim it alone solves navigation.",
        ),
        component_row(
            "local_path_tiebreak_repair",
            "rejected_current_form",
            "component_value_fail",
            "do_not_scale",
            {
                "changed_episode_rows": episode_summary.get("changed_episode_rows"),
                "local_swap_promoted_rows": m161.get("selected_local_swap_promoted_rows"),
                "promotion_allowed_rows": repair_summary.get("promotion_allowed_rows"),
                "failed_guard_counts": repair_summary.get("failed_guard_counts"),
            },
            {
                "selected_delta_SPL_mean": episode_summary.get("selected_delta_SPL_mean"),
                "selected_delta_CandidateVisits_mean": episode_summary.get(
                    "selected_delta_CandidateVisits_mean"
                ),
                "selected_success_proposal_changed_rows": episode_summary.get(
                    "selected_success_proposal_changed_rows"
                ),
                "selected_failure_type_changed_rows": episode_summary.get("selected_failure_type_changed_rows"),
                "no_path_tiebreak_SPL": no_path.get("SPL"),
            },
            "Local swaps changed orders but did not change any selected successful proposal; they mostly perturb pre-success route cost.",
            "Stop local-rerank scale-up; next route must change candidate-source/semantic-memory interface or freeze as diagnostic.",
        ),
        component_row(
            "source_gap_trigger",
            "absent_or_inert",
            "component_value_fail",
            "use_only_for_source_gap_rows",
            {
                "source_gap_prelabel_rows": repair_summary.get("source_gap_prelabel_rows"),
                "source_gap_only_SPL": source_gap.get("SPL"),
                "detector_SPL": detector.get("SPL"),
            },
            {
                "source_gap_only_equals_detector": source_gap.get("SPL") == detector.get("SPL"),
                "source_gap_only_CandidateVisits_mean": source_gap.get("CandidateVisits_mean"),
            },
            "The current full-val-mini target-free denominator contains no activated source-gap trigger.",
            "Source-gap logic should be evaluated only on source-gap/source-coverage rows or external proposal-source routes.",
        ),
        component_row(
            "no_visit_guard_route",
            "tradeoff_witness",
            "warning_not_selectable_posthoc",
            "do_not_promote_without_precommitted_budget_metric",
            {
                "best_SPL_policy_id": m164.get("best_SPL_policy_id"),
                "no_visit_guard_success_proposal_changed_rows": episode_summary.get(
                    "no_visit_guard_success_proposal_changed_rows"
                ),
            },
            {
                "no_visit_guard_SPL": no_visit.get("SPL"),
                "detector_SPL": detector.get("SPL"),
                "no_visit_guard_delta_SPL_vs_detector": (no_visit.get("SPL") or 0.0) - (detector.get("SPL") or 0.0),
                "no_visit_guard_delta_visits_vs_detector": (no_visit.get("CandidateVisits_mean") or 0.0)
                - (detector.get("CandidateVisits_mean") or 0.0),
            },
            "The no-visit-guard ablation gets best SPL but buys it with more visits and was not the selected method.",
            "Treat it as Pareto evidence; only promote after precommitting a utility/Pareto metric.",
        ),
        component_row(
            "ranking_only_navigation_repair",
            "exhausted_current_denominator",
            "method_form_fail",
            "pivot_method_form",
            {
                "candidate_set_matches_detector": True,
                "selected_success_proposal_changed_rows": episode_summary.get(
                    "selected_success_proposal_changed_rows"
                ),
            },
            {
                "positive_navigation_improvement_ready": m164.get("positive_navigation_improvement_ready"),
                "final_real_navigation_sr_spl_ready": m164.get("real_navigation_sr_spl_ready"),
            },
            "On this denominator, changing only visit order does not recover different target candidates or failures.",
            "M166 should package the boundary and decide between candidate-source/memory-interface pivot and external navigation baseline contract.",
        ),
    ]


def build_failure_mechanism_rows(episode_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "local_swaps_do_not_change_success_target",
            "severity": "high",
            "fact": f"Selected repair changed {episode_summary.get('changed_episode_rows')} episodes but changed 0 successful proposals vs detector-confidence.",
            "agent_inference": "The method cannot improve SR on this denominator because it reaches the same successful target candidates.",
            "next_validation_requirement": "Do not scale local swap reranking; require a candidate-source or memory-interface change that can alter target recovery.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "pre_success_route_cost_regression",
            "severity": "high",
            "fact": f"Mean delta SPL is {fmt(episode_summary.get('selected_delta_SPL_mean'))} and mean delta candidate visits is {fmt(episode_summary.get('selected_delta_CandidateVisits_mean'))}.",
            "agent_inference": "The selected path tie-break adds route/search cost before reaching the same success.",
            "next_validation_requirement": "Any future path-cost rule must reduce pre-success cost without extra visits or change successful target recovery.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "source_gap_trigger_absent",
            "severity": "medium",
            "fact": "Source-gap prelabel rows are zero and source-gap-only equals detector-confidence.",
            "agent_inference": "The current denominator cannot validate a source-gap-triggered semantic memory claim.",
            "next_validation_requirement": "Evaluate source-gap trigger only on source-gap/source-coverage rows or external proposal-source routes.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "confidence_floor_is_necessary_but_not_sufficient",
            "severity": "medium",
            "fact": "No-confidence-floor ablation is much worse, but the selected confidence-first repair still loses to detector-confidence.",
            "agent_inference": "Confidence is a guardrail, not the full contribution.",
            "next_validation_requirement": "Keep confidence floor while revising the method form around candidate-source or policy-level evidence.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "no_visit_guard_is_pareto_not_method",
            "severity": "medium",
            "fact": "No-visit-guard has best SPL but uses more visits than detector-confidence.",
            "agent_inference": "SPL gains can be bought by extra search effort, so top-tier claim needs a precommitted budget/Pareto metric.",
            "next_validation_requirement": "Do not pick no-visit-guard posthoc; record it as Pareto evidence for M166.",
        },
    ]


def build_principle_revision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "ranking_only_is_insufficient",
            "revised_principle": "A semantic memory policy must change either target recovery, source coverage, or task-level search cost; changing order around the same success candidate is not enough.",
            "method_form_implication": "Move beyond local reranking unless the rule demonstrably changes successful target recovery or reduces pre-success route cost.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "path_cost_must_be_outcome_linked",
            "revised_principle": "Path cost should be used only when it changes the outcome being claimed: fewer visits, shorter executed route, or different recovered target.",
            "method_form_implication": "Future path/search-cost terms need episode-level outcome guards, not just local pairwise rank swaps.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "source_gap_requires_source_gap_evidence",
            "revised_principle": "Source-gap behavior is a source-selection problem, not a universal ranking bonus.",
            "method_form_implication": "Evaluate it on source-gap/source-coverage rows or external mapping/proposal-source baselines.",
        },
        {
            "version": VERSION,
            "row_type": "principle_revision",
            "principle_id": "budget_is_claim_defining",
            "revised_principle": "A navigation/search claim must specify whether improvement is fixed-budget, SPL-maximizing, or Pareto/utility-based before selecting the method.",
            "method_form_implication": "M166 should freeze the metric target before any no-visit-guard or external-baseline comparison.",
        },
    ]


def build_m166_route_seed_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "m166_route_seed",
            "route_id": "freeze_m163_m164_as_negative_diagnostic",
            "decision": "select",
            "requirement": "Record M163/M164 as diagnostic execution evidence, not a positive result.",
        },
        {
            "version": VERSION,
            "row_type": "m166_route_seed",
            "route_id": "reject_local_swap_scaleup",
            "decision": "select",
            "requirement": "Do not run a larger local-swap reranker because the current run changes order without changing successful target candidates.",
        },
        {
            "version": VERSION,
            "row_type": "m166_route_seed",
            "route_id": "candidate_source_or_memory_interface_pivot",
            "decision": "select_next",
            "requirement": "Define whether the next method form changes source coverage, candidate generation, memory trust state, or external map proposal interface.",
        },
        {
            "version": VERSION,
            "row_type": "m166_route_seed",
            "route_id": "external_navigation_baseline_contract",
            "decision": "prepare_after_boundary",
            "requirement": "External navigation/search baselines remain required, but only after M166 fixes the claim boundary and shared input interface.",
        },
        {
            "version": VERSION,
            "row_type": "m166_route_seed",
            "route_id": "no_visit_guard_pareto_table",
            "decision": "defer",
            "requirement": "Use no-visit-guard only as a Pareto witness unless a utility metric is precommitted.",
        },
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "confidence_first_failure_decomposition",
            True,
            "M165 decomposes why M163/M164 fail protected navigation-improvement gates.",
        ),
        claim(
            "confidence_floor_needed",
            True,
            "Supported diagnostically by no-confidence-floor negative control, but not sufficient for a positive navigation claim.",
        ),
        claim(
            "selected_confidence_first_repair_navigation_improvement",
            False,
            "Blocked because selected repair loses SPL and candidate-visit efficiency to detector-confidence.",
        ),
        claim(
            "local_path_tiebreak_component_supported",
            False,
            "Blocked because local swaps do not change successful target proposals and regress aggregate SPL/visits.",
        ),
        claim(
            "source_gap_trigger_component_supported",
            False,
            "Blocked on this denominator because source-gap trigger has no activated source-gap evidence.",
        ),
        claim(
            "no_visit_guard_as_selected_method",
            False,
            "Blocked because it is a posthoc Pareto witness with extra visits.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Still requires a selected method that beats protected baselines, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M165 is target-free and does not change the E006-M08 human-intent boundary.",
        ),
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "why_not_continue_threshold_tuning",
            "reviewer_response": "M165 shows the selected local swaps do not change successful target candidates; tuning thresholds would be conclusion-fitting without a new failure-derived principle.",
        },
        {
            "version": VERSION,
            "issue_id": "why_is_path_cost_not_the_contribution",
            "reviewer_response": "Path cost is not rejected wholesale, but current local tie-breaks worsen SPL/visits. A future path-cost claim must change target recovery or reduce pre-success route cost.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_pick_no_visit_guard",
            "reviewer_response": "No-visit-guard is a posthoc tradeoff witness: it has best SPL but spends more visits than detector-confidence.",
        },
        {
            "version": VERSION,
            "issue_id": "what_remains_supported",
            "reviewer_response": "The confidence floor remains necessary under open-vocabulary proposal noise; the rest of the current reranker is diagnostic-negative.",
        },
        {
            "version": VERSION,
            "issue_id": "what_is_the_next_principled_step",
            "reviewer_response": "M166 should package the failure boundary and pivot from local ranking repair to candidate-source/memory-interface or external-baseline contract.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "claim_selected_confidence_first_navigation_improvement",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "M165 confirms selected repair changes order but not successful target recovery, while SPL/visit gates fail.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "scale_local_path_tiebreak_repair",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Local swap scale-up would scale a mechanism that currently perturbs pre-success route cost without changing successful proposals.",
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
            "route_id": "freeze_failure_boundary_and_pivot_contract",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The next unit should freeze the navigation failure boundary and decide whether to pivot to candidate-source/memory-interface or external navigation baseline contract.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but M166 should first define the shared interface and claim boundary after the internal repair failure.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    m161_coverage: dict[str, Any],
    m163_coverage: dict[str, Any],
    m164_coverage: dict[str, Any],
    repair_summary: dict[str, Any],
    episode_summary: dict[str, Any],
    component_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    principle_rows: list[dict[str, Any]],
    route_seed_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    supported = [
        row["component_id"]
        for row in component_rows
        if row["component_status"] in {"supported_diagnostic", "supported_as_required_baseline"}
    ]
    rejected = [
        row["component_id"]
        for row in component_rows
        if row["component_status"] in {"rejected_current_form", "absent_or_inert", "exhausted_current_denominator"}
    ]
    tradeoff = [row["component_id"] for row in component_rows if row["component_status"] == "tradeoff_witness"]
    selected_route = next(row for row in route_rows if row["selected"])
    return {
        "version": VERSION,
        "status": READY_STATUS if not missing_inputs else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m161_status": m161_coverage.get("status"),
        "m163_status": m163_coverage.get("status"),
        "m164_status": m164_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "repair_component_rows": repair_summary.get("repair_component_rows"),
        "promotion_allowed_rows": repair_summary.get("promotion_allowed_rows"),
        "source_gap_prelabel_rows": repair_summary.get("source_gap_prelabel_rows"),
        "episode_failure_profile_rows": episode_summary.get("episode_rows"),
        "changed_episode_rows": episode_summary.get("changed_episode_rows"),
        "selected_success_proposal_changed_rows": episode_summary.get("selected_success_proposal_changed_rows"),
        "selected_failure_type_changed_rows": episode_summary.get("selected_failure_type_changed_rows"),
        "selected_better_spl_rows": episode_summary.get("selected_better_spl_rows"),
        "selected_worse_spl_rows": episode_summary.get("selected_worse_spl_rows"),
        "selected_tie_spl_rows": episode_summary.get("selected_tie_spl_rows"),
        "selected_more_visit_rows": episode_summary.get("selected_more_visit_rows"),
        "selected_fewer_visit_rows": episode_summary.get("selected_fewer_visit_rows"),
        "selected_delta_SPL_mean": episode_summary.get("selected_delta_SPL_mean"),
        "selected_delta_CandidateVisits_mean": episode_summary.get("selected_delta_CandidateVisits_mean"),
        "selected_delta_PathLengthM_mean": episode_summary.get("selected_delta_PathLengthM_mean"),
        "component_failure_rows": len(component_rows),
        "failure_mechanism_rows": len(mechanism_rows),
        "principle_revision_rows": len(principle_rows),
        "m166_route_seed_rows": len(route_seed_rows),
        "supported_component_ids": supported,
        "rejected_or_exhausted_component_ids": rejected,
        "tradeoff_component_ids": tradeoff,
        "positive_navigation_improvement_ready": False,
        "local_rerank_scaleup_ready": False,
        "method_pivot_contract_required": True,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_route["selected_next_unit"],
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
    episode_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    principle_rows: list[dict[str, Any]],
    route_seed_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected_route = next(row for row in route_rows if row["selected"])
    episode_summary_rows = [
        {
            "summary_id": "selected_vs_detector",
            "episode_rows": coverage["episode_failure_profile_rows"],
            "changed_episode_rows": coverage["changed_episode_rows"],
            "success_proposal_changed_rows": coverage["selected_success_proposal_changed_rows"],
            "mean_delta_SPL": coverage["selected_delta_SPL_mean"],
            "mean_delta_CandidateVisits": coverage["selected_delta_CandidateVisits_mean"],
            "better_spl_rows": coverage["selected_better_spl_rows"],
            "worse_spl_rows": coverage["selected_worse_spl_rows"],
        }
    ]
    return "\n".join(
        [
            "# E008-M165 Confidence-First Repair Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Input M161 status: `{coverage['m161_status']}`.",
            f"- Input M163 status: `{coverage['m163_status']}`.",
            f"- Input M164 status: `{coverage['m164_status']}`.",
            f"- Changed episodes: {coverage['changed_episode_rows']} / {coverage['episode_failure_profile_rows']}.",
            f"- Selected success proposal changes vs detector-confidence: {coverage['selected_success_proposal_changed_rows']}.",
            f"- Mean delta `SPL` / candidate visits / path length: {fmt(coverage['selected_delta_SPL_mean'])} / {fmt(coverage['selected_delta_CandidateVisits_mean'])} / {fmt(coverage['selected_delta_PathLengthM_mean'])}.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Episode Summary",
            "",
            markdown_table(
                episode_summary_rows,
                [
                    "summary_id",
                    "episode_rows",
                    "changed_episode_rows",
                    "success_proposal_changed_rows",
                    "mean_delta_SPL",
                    "mean_delta_CandidateVisits",
                    "better_spl_rows",
                    "worse_spl_rows",
                ],
            ),
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
            "## M166 Route Seed",
            "",
            markdown_table(route_seed_rows, ["route_id", "decision", "requirement"]),
            "",
            "## Paper Claims",
            "",
            markdown_table(claim_rows, ["claim_id", "supported", "claim_boundary"]),
            "",
            "## Agent Inference",
            "",
            "- The selected repair changes order, but not the successful target proposal. Therefore the current failure is not a lack of path-cost tuning; it is a method-form mismatch.",
            "- Continuing local rerank scale-up would test a mechanism that already fails the protected gate and does not affect target recovery.",
            "- The next principled step is to freeze this failure boundary, then decide whether the paper pivots toward candidate-source / memory-interface changes or external navigation baseline contracts.",
            "",
            "## Route Decision",
            "",
            f"- Selected route: `{selected_route['route_id']}`.",
            f"- Selected next unit: {selected_route['selected_next_unit']}.",
            f"- Reason: {selected_route['reason']}",
            "",
            "## Episode Rows",
            "",
            "Detailed rows are stored in `episode_failure_profile_rows.jsonl`.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    required = {
        "m161_coverage": M161_DIR / "coverage.json",
        "m161_policy_order_audit": M161_DIR / "policy_order_audit_rows.jsonl",
        "m161_repair_components": M161_DIR / "repair_component_rows.jsonl",
        "m163_coverage": M163_DIR / "coverage.json",
        "m163_policy_metrics": M163_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        "m164_coverage": M164_DIR / "coverage.json",
        "m164_component_interpretation": M164_DIR / "component_interpretation_rows.jsonl",
    }
    missing_inputs = [key for key, path in required.items() if not path.exists()]

    m161_coverage = read_json(required["m161_coverage"])
    m163_coverage = read_json(required["m163_coverage"])
    m164_coverage = read_json(required["m164_coverage"])
    order_rows = read_jsonl(required["m161_policy_order_audit"])
    repair_rows = read_jsonl(required["m161_repair_components"])
    metric_rows = read_jsonl(required["m163_policy_metrics"])

    metric_by_episode = metric_rows_by_episode(metric_rows)
    aggregates = policy_aggregates(metric_rows)
    order_by_episode = method_order_rows(order_rows)
    repair_summary = summarize_repair_components(repair_rows)
    episode_rows = build_episode_failure_profile_rows(metric_by_episode, order_by_episode)
    episode_summary = summarize_episode_profiles(episode_rows)
    component_rows = build_component_failure_rows(
        m161_coverage, m164_coverage, repair_summary, episode_summary, aggregates
    )
    mechanism_rows = build_failure_mechanism_rows(episode_summary)
    principle_rows = build_principle_revision_rows()
    route_seed_rows = build_m166_route_seed_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()
    coverage = build_coverage(
        m161_coverage,
        m163_coverage,
        m164_coverage,
        repair_summary,
        episode_summary,
        component_rows,
        mechanism_rows,
        principle_rows,
        route_seed_rows,
        route_rows,
        missing_inputs,
    )
    report = build_report(
        coverage,
        episode_rows,
        component_rows,
        mechanism_rows,
        principle_rows,
        route_seed_rows,
        claim_rows,
        route_rows,
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "coverage.json": coverage,
        "episode_failure_profile_rows.jsonl": episode_rows,
        "component_failure_rows.jsonl": component_rows,
        "failure_mechanism_rows.jsonl": mechanism_rows,
        "principle_revision_rows.jsonl": principle_rows,
        "m166_route_seed_rows.jsonl": route_seed_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
        "route_decision_rows.jsonl": route_rows,
    }

    written: list[Path] = []
    for name, payload in outputs.items():
        path = ARTIFACT_DIR / name
        if name.endswith(".jsonl"):
            write_jsonl(path, payload)  # type: ignore[arg-type]
        else:
            write_json(path, payload)
        written.append(path)
    report_path = ARTIFACT_DIR / "report.md"
    report_path.write_text(report, encoding="utf-8")
    written.append(report_path)
    mirror_outputs(written)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
