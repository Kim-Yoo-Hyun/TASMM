#!/usr/bin/env python3
"""Decompose E008-M171 source-coverage ablation tradeoffs."""

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
M170_DIR = EXP_ROOT / "artifacts" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"
M171_DIR = EXP_ROOT / "artifacts" / "E008-M171_source_coverage_memory_interface_result_interpretation_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M172_source_coverage_ablation_tradeoff_decomposition_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M172_source_coverage_ablation_tradeoff_decomposition_v0"

VERSION = "e008_m172_source_coverage_ablation_tradeoff_decomposition_v0"
READY_STATUS = "e008_m172_source_coverage_ablation_tradeoff_decomposition_ready"
BLOCKED_STATUS = "e008_m172_source_coverage_ablation_tradeoff_decomposition_blocked"
NEXT_UNIT = "E008-M173 source-coverage utility/Pareto contract and bounded method redesign"

SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_ONLY = "source_coverage_only_task_agnostic_v1"
CONFIDENCE_ONLY = "confidence_floor_only_v1"
PATH_ONLY = "path_cost_only_reachable_subset_v1"

POLICIES = [
    SELECTED_POLICY,
    DETECTOR_POLICY,
    SOURCE_COVERAGE_ONLY,
    CONFIDENCE_ONLY,
    PATH_ONLY,
]

COMPARISONS = [
    (SELECTED_POLICY, DETECTOR_POLICY, "selected_vs_detector_confidence"),
    (SOURCE_COVERAGE_ONLY, DETECTOR_POLICY, "source_coverage_only_vs_detector_confidence"),
    (SELECTED_POLICY, SOURCE_COVERAGE_ONLY, "selected_vs_source_coverage_only"),
    (PATH_ONLY, DETECTOR_POLICY, "path_cost_only_vs_detector_confidence"),
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


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


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


def aggregate_rows(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def scan_rows_by_episode(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in metric_rows:
        if row.get("metric_scope") == "scan_task_policy":
            grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row
    return grouped


def policy_role(policy_id: str) -> str:
    return {
        SELECTED_POLICY: "selected_memory_interface_policy",
        DETECTOR_POLICY: "protected_detector_confidence_baseline",
        SOURCE_COVERAGE_ONLY: "task_agnostic_source_coverage_ablation",
        CONFIDENCE_ONLY: "confidence_floor_ablation",
        PATH_ONLY: "path_cost_only_ablation",
    }.get(policy_id, "unknown")


def metric_values(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "SR": finite_float(row.get("SR")),
        "SPL": finite_float(row.get("SPL")),
        "CandidateVisits_mean": finite_float(row.get("CandidateVisits_mean")),
        "PathLengthM_mean": finite_float(row.get("PathLengthM_mean")),
    }


def dominates(left: dict[str, Any], right: dict[str, Any], *, include_path_length: bool) -> bool:
    left_m = metric_values(left)
    right_m = metric_values(right)
    keys = ["SR", "SPL", "CandidateVisits_mean"]
    if include_path_length:
        keys.append("PathLengthM_mean")
    if any(left_m[key] is None or right_m[key] is None for key in keys):
        return False
    non_worse = [
        left_m["SR"] >= right_m["SR"],
        left_m["SPL"] >= right_m["SPL"],
        left_m["CandidateVisits_mean"] <= right_m["CandidateVisits_mean"],
    ]
    strict = [
        left_m["SR"] > right_m["SR"],
        left_m["SPL"] > right_m["SPL"],
        left_m["CandidateVisits_mean"] < right_m["CandidateVisits_mean"],
    ]
    if include_path_length:
        non_worse.append(left_m["PathLengthM_mean"] <= right_m["PathLengthM_mean"])
        strict.append(left_m["PathLengthM_mean"] < right_m["PathLengthM_mean"])
    return all(non_worse) and any(strict)


def build_policy_pareto_rows(aggregates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    detector = aggregates.get(DETECTOR_POLICY, {})
    best_spl = max(
        [finite_float(row.get("SPL")) for row in aggregates.values() if finite_float(row.get("SPL")) is not None],
        default=None,
    )
    for policy_id in POLICIES:
        policy = aggregates.get(policy_id, {})
        primary_dominators = [
            other_id
            for other_id, other in aggregates.items()
            if other_id != policy_id and dominates(other, policy, include_path_length=False)
        ]
        expanded_dominators = [
            other_id
            for other_id, other in aggregates.items()
            if other_id != policy_id and dominates(other, policy, include_path_length=True)
        ]
        interpretation = "manual_review"
        if policy_id == SELECTED_POLICY:
            interpretation = "reject_selected_policy_positive_claim"
        elif policy_id == SOURCE_COVERAGE_ONLY:
            interpretation = "pareto_tradeoff_witness_not_selected_method"
        elif policy_id == DETECTOR_POLICY:
            interpretation = "protected_baseline_still_required"
        elif policy_id == CONFIDENCE_ONLY:
            interpretation = "equivalent_to_detector_on_this_denominator"
        elif policy_id == PATH_ONLY:
            interpretation = "path_cost_alone_is_misaligned"
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_pareto",
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "SR": policy.get("SR"),
                "SPL": policy.get("SPL"),
                "CandidateVisits_mean": policy.get("CandidateVisits_mean"),
                "PathLengthM_mean": policy.get("PathLengthM_mean"),
                "success_rows": policy.get("success_rows"),
                "scan_task_policy_rows": policy.get("scan_task_policy_rows"),
                "delta_SR_vs_detector": delta(policy.get("SR"), detector.get("SR")),
                "delta_SPL_vs_detector": delta(policy.get("SPL"), detector.get("SPL")),
                "delta_CandidateVisits_vs_detector": delta(
                    policy.get("CandidateVisits_mean"), detector.get("CandidateVisits_mean")
                ),
                "delta_PathLengthM_vs_detector": delta(policy.get("PathLengthM_mean"), detector.get("PathLengthM_mean")),
                "primary_space": "maximize_SR,maximize_SPL,minimize_CandidateVisits",
                "primary_dominated_by": primary_dominators,
                "primary_pareto_member": not primary_dominators,
                "expanded_space": "maximize_SR,maximize_SPL,minimize_CandidateVisits,minimize_PathLengthM",
                "expanded_dominated_by": expanded_dominators,
                "expanded_pareto_member": not expanded_dominators,
                "is_best_spl_policy": best_spl is not None and finite_float(policy.get("SPL")) == best_spl,
                "supports_positive_navigation_improvement": False,
                "supports_final_navigation_claim": False,
                "interpretation": interpretation,
            }
        )
    return rows


def classify_tradeoff(method: dict[str, Any], baseline: dict[str, Any]) -> str:
    eps = 1e-9
    delta_sr = delta(method.get("SR"), baseline.get("SR"))
    delta_spl = delta(method.get("SPL"), baseline.get("SPL"))
    delta_visits = delta(method.get("CandidateVisits"), baseline.get("CandidateVisits"))
    delta_path = delta(method.get("PathLengthM"), baseline.get("PathLengthM"))
    if delta_sr is not None and delta_sr < -eps:
        return "sr_regression"
    if delta_spl is None or delta_visits is None:
        return "missing_metric"
    if delta_spl > eps and delta_visits <= eps:
        return "clean_spl_gain"
    if delta_spl > eps and delta_visits > eps:
        return "spl_gain_with_visit_cost"
    if delta_spl < -eps and delta_visits > eps:
        return "spl_loss_and_more_visits"
    if delta_spl < -eps and delta_visits <= eps:
        return "spl_loss_without_more_visits"
    if abs(delta_spl) <= eps and delta_visits < -eps:
        return "visit_saving_spl_tie"
    if abs(delta_spl) <= eps and delta_visits > eps:
        return "visit_regression_spl_tie"
    if delta_path is not None and delta_path < -eps:
        return "path_gain_only"
    return "neutral_or_tie"


def build_episode_tradeoff_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = scan_rows_by_episode(metric_rows)
    rows: list[dict[str, Any]] = []
    for uid, policies in sorted(grouped.items()):
        for method_id, baseline_id, comparison_id in COMPARISONS:
            method = policies.get(method_id)
            baseline = policies.get(baseline_id)
            if not method or not baseline:
                continue
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "episode_tradeoff",
                    "comparison_id": comparison_id,
                    "method_policy_id": method_id,
                    "baseline_policy_id": baseline_id,
                    "benchmark_row_uid": uid,
                    "scan_id": method.get("scan_id"),
                    "scene_key": method.get("scene_key"),
                    "adapter_episode_id": method.get("adapter_episode_id"),
                    "object_category": method.get("object_category"),
                    "task_context_id": method.get("task_context_id"),
                    "method_SR": method.get("SR"),
                    "baseline_SR": baseline.get("SR"),
                    "delta_SR": delta(method.get("SR"), baseline.get("SR")),
                    "method_SPL": method.get("SPL"),
                    "baseline_SPL": baseline.get("SPL"),
                    "delta_SPL": delta(method.get("SPL"), baseline.get("SPL")),
                    "method_CandidateVisits": method.get("CandidateVisits"),
                    "baseline_CandidateVisits": baseline.get("CandidateVisits"),
                    "delta_CandidateVisits": delta(method.get("CandidateVisits"), baseline.get("CandidateVisits")),
                    "method_PathLengthM": method.get("PathLengthM"),
                    "baseline_PathLengthM": baseline.get("PathLengthM"),
                    "delta_PathLengthM": delta(method.get("PathLengthM"), baseline.get("PathLengthM")),
                    "method_success_proposal_uid": method.get("success_proposal_uid"),
                    "baseline_success_proposal_uid": baseline.get("success_proposal_uid"),
                    "success_proposal_changed": method.get("success_proposal_uid") != baseline.get("success_proposal_uid"),
                    "method_success_source_role": method.get("success_source_role"),
                    "baseline_success_source_role": baseline.get("success_source_role"),
                    "success_source_role_changed": method.get("success_source_role") != baseline.get("success_source_role"),
                    "tradeoff_class": classify_tradeoff(method, baseline),
                }
            )
    return rows


def summarize_tradeoffs(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        grouped[(str(row.get("comparison_id")), str(row.get("tradeoff_class")))].append(row)
    rows: list[dict[str, Any]] = []
    for (comparison_id, tradeoff_class), group in sorted(grouped.items()):
        rows.append(
            {
                "version": VERSION,
                "row_type": "tradeoff_summary",
                "comparison_id": comparison_id,
                "tradeoff_class": tradeoff_class,
                "rows": len(group),
                "mean_delta_SR": mean([finite_float(row.get("delta_SR")) for row in group]),
                "mean_delta_SPL": mean([finite_float(row.get("delta_SPL")) for row in group]),
                "mean_delta_CandidateVisits": mean([finite_float(row.get("delta_CandidateVisits")) for row in group]),
                "mean_delta_PathLengthM": mean([finite_float(row.get("delta_PathLengthM")) for row in group]),
                "success_proposal_changed_rows": sum(bool(row.get("success_proposal_changed")) for row in group),
                "success_source_role_changed_rows": sum(bool(row.get("success_source_role_changed")) for row in group),
            }
        )
    return rows


def comparison_summary(episode_rows: list[dict[str, Any]], comparison_id: str) -> dict[str, Any]:
    rows = [row for row in episode_rows if row.get("comparison_id") == comparison_id]
    classes = Counter(str(row.get("tradeoff_class")) for row in rows)
    return {
        "comparison_id": comparison_id,
        "rows": len(rows),
        "class_counts": dict(sorted(classes.items())),
        "mean_delta_SR": mean([finite_float(row.get("delta_SR")) for row in rows]),
        "mean_delta_SPL": mean([finite_float(row.get("delta_SPL")) for row in rows]),
        "mean_delta_CandidateVisits": mean([finite_float(row.get("delta_CandidateVisits")) for row in rows]),
        "mean_delta_PathLengthM": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
        "better_SPL_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) > 1e-9 for row in rows),
        "worse_SPL_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) < -1e-9 for row in rows),
        "tie_SPL_rows": sum(abs(finite_float(row.get("delta_SPL")) or 0.0) <= 1e-9 for row in rows),
        "more_visit_rows": sum((finite_float(row.get("delta_CandidateVisits")) or 0.0) > 1e-9 for row in rows),
        "fewer_visit_rows": sum((finite_float(row.get("delta_CandidateVisits")) or 0.0) < -1e-9 for row in rows),
        "tie_visit_rows": sum(abs(finite_float(row.get("delta_CandidateVisits")) or 0.0) <= 1e-9 for row in rows),
        "success_proposal_changed_rows": sum(bool(row.get("success_proposal_changed")) for row in rows),
    }


def build_failure_diagnosis_rows(
    policy_rows: list[dict[str, Any]],
    source_coverage_summary: dict[str, Any],
    selected_summary: dict[str, Any],
    path_summary: dict[str, Any],
    m168: dict[str, Any],
) -> list[dict[str, Any]]:
    selected = next(row for row in policy_rows if row["policy_id"] == SELECTED_POLICY)
    source_cov = next(row for row in policy_rows if row["policy_id"] == SOURCE_COVERAGE_ONLY)
    path_only = next(row for row in policy_rows if row["policy_id"] == PATH_ONLY)
    return [
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "selected_policy_is_dominated",
            "severity": "high",
            "fact": "The selected memory-interface policy is dominated by detector-confidence in SR/SPL/CandidateVisits space.",
            "evidence": f"primary_dominated_by={selected['primary_dominated_by']}; delta_SPL={fmt(selected['delta_SPL_vs_detector'])}; delta_visits={fmt(selected['delta_CandidateVisits_vs_detector'])}.",
            "agent_inference": "The current memory-interface guard overconstrains useful source coverage without improving executed navigation.",
            "next_requirement": "Do not scale or claim the selected policy; revise the objective before new execution.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "source_coverage_only_is_pareto_tradeoff",
            "severity": "high",
            "fact": "Source-coverage-only is a Pareto witness, not a clean improvement over detector-confidence.",
            "evidence": f"delta_SPL={fmt(source_cov['delta_SPL_vs_detector'])}; delta_visits={fmt(source_cov['delta_CandidateVisits_vs_detector'])}; win/loss/tie={source_coverage_summary['better_SPL_rows']}/{source_coverage_summary['worse_SPL_rows']}/{source_coverage_summary['tie_SPL_rows']}.",
            "agent_inference": "Source coverage can change useful targets, but its effect is unstable and budget-dependent.",
            "next_requirement": "Precommit a utility/Pareto objective before promoting source coverage to the method.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "source_coverage_is_task_agnostic_in_m170",
            "severity": "medium",
            "fact": "The strongest source-coverage row is task-agnostic and does not use human intent or stale-memory trust as the main decision.",
            "evidence": f"policy_id={SOURCE_COVERAGE_ONLY}; success_proposal_changed_rows={source_coverage_summary['success_proposal_changed_rows']}.",
            "agent_inference": "This result pressures H001 to explain why memory trust/re-observation is needed beyond source diversity.",
            "next_requirement": "Treat source coverage as a necessary interface component, not as the paper contribution by itself.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "source_gap_trigger_absent",
            "severity": "medium",
            "fact": "M168 source-gap prelabel rows remain zero.",
            "evidence": f"source_gap_prelabel_rows={m168.get('source_gap_prelabel_rows')}.",
            "agent_inference": "M170/M171 cannot validate source-gap-trigger behavior on this denominator.",
            "next_requirement": "Keep source-gap claims limited to source-gap/source-coverage denominators or external proposal-source routes.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "path_cost_only_is_misaligned",
            "severity": "medium",
            "fact": "Path-cost-only has lower mean path length but much lower SPL and more visits than detector-confidence.",
            "evidence": f"path_only_delta_SPL={fmt(path_only['delta_SPL_vs_detector'])}; path_only_delta_visits={fmt(path_only['delta_CandidateVisits_vs_detector'])}; path_only_delta_path={fmt(path_only['delta_PathLengthM_vs_detector'])}.",
            "agent_inference": "Path cost should be a feasibility/budget term, not the primary ordering rule.",
            "next_requirement": "The next contract should protect detector confidence while using source coverage only under a budget-aware utility.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "selected_vs_source_coverage_only_tradeoff",
            "severity": "high",
            "fact": "The selected policy uses fewer visits than source-coverage-only but loses SPL.",
            "evidence": f"selected_vs_source_coverage_only mean_delta_SPL={fmt(selected_summary.get('mean_delta_SPL'))}; mean_delta_visits={fmt(selected_summary.get('mean_delta_CandidateVisits'))}.",
            "agent_inference": "The current guard acts like a budget constraint but lacks a precommitted utility target.",
            "next_requirement": "Define whether the paper optimizes fixed-budget SPL, expected search cost, or a Pareto frontier before redesign.",
        },
    ]


def build_policy_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "policy_decision",
            "route_id": "claim_selected_memory_interface_policy",
            "decision": "reject_now",
            "selected": False,
            "reason": "Selected policy loses SPL and visit-efficiency to detector-confidence.",
            "launch_long_job_now": False,
            "selected_next_unit": None,
        },
        {
            "version": VERSION,
            "row_type": "policy_decision",
            "route_id": "promote_source_coverage_only",
            "decision": "reject_as_main_method_now",
            "selected": False,
            "reason": "It is task-agnostic, not preselected as the method, and improves mean SPL only as a budget/Pareto tradeoff.",
            "launch_long_job_now": False,
            "selected_next_unit": None,
        },
        {
            "version": VERSION,
            "row_type": "policy_decision",
            "route_id": "keep_detector_confidence_protected_baseline",
            "decision": "select_guard",
            "selected": True,
            "reason": "Detector-confidence remains the simplest protected baseline and dominates the selected policy.",
            "launch_long_job_now": False,
            "selected_next_unit": None,
        },
        {
            "version": VERSION,
            "row_type": "policy_decision",
            "route_id": "source_coverage_utility_pareto_contract",
            "decision": "select_next",
            "selected": True,
            "reason": "M172 shows source coverage is useful only under an explicit SPL/visit/path tradeoff objective.",
            "launch_long_job_now": False,
            "selected_next_unit": NEXT_UNIT,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "m172_source_coverage_tradeoff_diagnostic",
            "supported": True,
            "claim_boundary": "M172 supports a diagnostic statement that source coverage creates a Pareto tradeoff but not a clean method win.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_source_coverage_memory_interface_navigation_improvement",
            "supported": False,
            "claim_boundary": "Blocked because selected policy loses SPL and visits to detector-confidence.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_only_as_main_method",
            "supported": False,
            "claim_boundary": "Blocked because it is task-agnostic, not the preselected method, and requires a budget/Pareto objective before promotion.",
        },
        {
            "version": VERSION,
            "claim_id": "path_cost_only_as_main_method",
            "supported": False,
            "claim_boundary": "Blocked because path-cost-only lowers path length but loses SPL and visits.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M172 is target-free and does not upgrade E006-M08's human-intent boundary.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still requires a precommitted method that beats protected baselines, heldout transfer, and external navigation/search baselines.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "why_not_claim_source_coverage_only",
            "reviewer_response": "Because it was an ablation, not the selected method; its mean SPL gain is small, episode-level wins/losses are balanced, and it spends more candidate visits.",
        },
        {
            "version": VERSION,
            "issue_id": "why_is_m172_still_useful",
            "reviewer_response": "It identifies that source coverage is a real decision variable, but only under a precommitted SPL/visit/path tradeoff objective.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_tune_thresholds_after_m171",
            "reviewer_response": "Changing thresholds after a failed protected-baseline gate would be conclusion-fitting; M172 instead records the failure mechanism and next contract.",
        },
        {
            "version": VERSION,
            "issue_id": "what_is_the_next_principle",
            "reviewer_response": "The next method should make source coverage a budget-aware semantic memory interface decision while keeping detector confidence protected.",
        },
        {
            "version": VERSION,
            "issue_id": "does_this_support_human_intent",
            "reviewer_response": "No. Human intent remains secondary under current evidence; M172 is about source coverage and search-budget tradeoffs.",
        },
    ]


def report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    diagnosis_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M172 Source-Coverage Ablation Tradeoff Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M171 status: `{coverage['m171_status']}`.",
            f"- Selected positive navigation-improvement ready: {coverage['selected_positive_navigation_improvement_ready']}.",
            f"- Source-coverage-only Pareto frontier: {coverage['source_coverage_only_primary_pareto_member']}.",
            f"- Source-coverage-only delta `SPL` / visits vs detector: {fmt(coverage['source_coverage_only_delta_SPL_vs_detector'])} / {fmt(coverage['source_coverage_only_delta_CandidateVisits_vs_detector'])}.",
            f"- Source-coverage-only win/loss/tie vs detector: {coverage['source_coverage_only_better_SPL_rows']} / {coverage['source_coverage_only_worse_SPL_rows']} / {coverage['source_coverage_only_tie_SPL_rows']}.",
            f"- Promote source-coverage-only as main method now: {coverage['promote_source_coverage_only_as_main_method_now']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Pareto Rows",
            "",
            table(
                policy_rows,
                [
                    "policy_id",
                    "SR",
                    "SPL",
                    "CandidateVisits_mean",
                    "PathLengthM_mean",
                    "primary_pareto_member",
                    "primary_dominated_by",
                    "interpretation",
                ],
            ),
            "",
            "## Comparison Summaries",
            "",
            table(
                comparison_rows,
                [
                    "comparison_id",
                    "rows",
                    "mean_delta_SPL",
                    "mean_delta_CandidateVisits",
                    "better_SPL_rows",
                    "worse_SPL_rows",
                    "tie_SPL_rows",
                    "success_proposal_changed_rows",
                ],
            ),
            "",
            "## Failure Diagnosis",
            "",
            table(diagnosis_rows, ["diagnosis_id", "severity", "fact", "next_requirement"]),
            "",
            "## Policy Decision",
            "",
            table(decision_rows, ["route_id", "decision", "selected", "reason", "selected_next_unit"]),
            "",
            "## Claim Boundary",
            "",
            "- M172 does not upgrade real navigation `SR` / `SPL` to a final claim.",
            "- `source_coverage_only_task_agnostic_v1` is retained as a tradeoff witness, not a main method.",
            "- M173 should precommit the source-coverage utility/Pareto objective before another long trajectory run.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m168 = read_json(M168_DIR / "coverage.json")
    m170 = read_json(M170_DIR / "coverage.json")
    m171 = read_json(M171_DIR / "coverage.json")
    metric_rows = read_jsonl(M170_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    missing = []
    if m168.get("status") != "e008_m168_source_coverage_memory_interface_materialization_ready":
        missing.append("M168 ready coverage")
    if m170.get("status") != "e008_m170_source_coverage_memory_interface_trajectory_execution_ready":
        missing.append("M170 ready coverage")
    if m171.get("status") != "e008_m171_source_coverage_memory_interface_result_interpretation_ready":
        missing.append("M171 ready coverage")
    if len([row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]) != 150:
        missing.append("M170 scan-task-policy rows")

    aggregates = aggregate_rows(metric_rows)
    policy_rows = build_policy_pareto_rows(aggregates)
    episode_rows = build_episode_tradeoff_rows(metric_rows)
    tradeoff_summary_rows = summarize_tradeoffs(episode_rows)
    comparison_rows = [
        comparison_summary(episode_rows, comparison_id)
        for _, _, comparison_id in COMPARISONS
    ]
    comparison_by_id = {row["comparison_id"]: row for row in comparison_rows}
    diagnosis_rows = build_failure_diagnosis_rows(
        policy_rows,
        comparison_by_id["source_coverage_only_vs_detector_confidence"],
        comparison_by_id["selected_vs_source_coverage_only"],
        comparison_by_id["path_cost_only_vs_detector_confidence"],
        m168,
    )
    decision_rows = build_policy_decision_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()

    selected_policy = next(row for row in policy_rows if row["policy_id"] == SELECTED_POLICY)
    source_cov = next(row for row in policy_rows if row["policy_id"] == SOURCE_COVERAGE_ONLY)
    source_cov_summary = comparison_by_id["source_coverage_only_vs_detector_confidence"]
    ready = not missing
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m168_status": m168.get("status"),
        "m170_status": m170.get("status"),
        "m171_status": m171.get("status"),
        "policy_pareto_rows": len(policy_rows),
        "episode_tradeoff_rows": len(episode_rows),
        "tradeoff_summary_rows": len(tradeoff_summary_rows),
        "comparison_summary_rows": len(comparison_rows),
        "failure_diagnosis_rows": len(diagnosis_rows),
        "policy_decision_rows": len(decision_rows),
        "selected_policy_id": SELECTED_POLICY,
        "selected_policy_primary_pareto_member": selected_policy["primary_pareto_member"],
        "selected_policy_primary_dominated_by": selected_policy["primary_dominated_by"],
        "selected_positive_navigation_improvement_ready": False,
        "source_coverage_only_policy_id": SOURCE_COVERAGE_ONLY,
        "source_coverage_only_primary_pareto_member": source_cov["primary_pareto_member"],
        "source_coverage_only_delta_SPL_vs_detector": source_cov["delta_SPL_vs_detector"],
        "source_coverage_only_delta_CandidateVisits_vs_detector": source_cov["delta_CandidateVisits_vs_detector"],
        "source_coverage_only_delta_PathLengthM_vs_detector": source_cov["delta_PathLengthM_vs_detector"],
        "source_coverage_only_better_SPL_rows": source_cov_summary["better_SPL_rows"],
        "source_coverage_only_worse_SPL_rows": source_cov_summary["worse_SPL_rows"],
        "source_coverage_only_tie_SPL_rows": source_cov_summary["tie_SPL_rows"],
        "source_coverage_only_more_visit_rows": source_cov_summary["more_visit_rows"],
        "source_coverage_only_fewer_visit_rows": source_cov_summary["fewer_visit_rows"],
        "source_coverage_only_success_proposal_changed_rows": source_cov_summary["success_proposal_changed_rows"],
        "source_coverage_only_tradeoff_witness": True,
        "promote_source_coverage_only_as_main_method_now": False,
        "source_gap_prelabel_rows": m168.get("source_gap_prelabel_rows"),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_pareto_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "episode_tradeoff_rows.jsonl", episode_rows)
    write_jsonl(ARTIFACT_DIR / "tradeoff_summary_rows.jsonl", tradeoff_summary_rows)
    write_jsonl(ARTIFACT_DIR / "comparison_summary_rows.jsonl", comparison_rows)
    write_jsonl(ARTIFACT_DIR / "failure_diagnosis_rows.jsonl", diagnosis_rows)
    write_jsonl(ARTIFACT_DIR / "policy_decision_rows.jsonl", decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        report(coverage, policy_rows, comparison_rows, diagnosis_rows, decision_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
