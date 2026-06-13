#!/usr/bin/env python3
"""Decompose E008-M151/M152 budget/SPL Pareto failures and select the next route."""

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
M151_DIR = EXP_ROOT / "artifacts" / "E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
M152_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M153_full_val_mini_budget_spl_pareto_failure_decomposition_v0"
)

VERSION = "e008_m153_full_val_mini_budget_spl_pareto_failure_decomposition_v0"
READY_STATUS = "e008_m153_full_val_mini_budget_spl_pareto_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m153_full_val_mini_budget_spl_pareto_failure_decomposition_blocked"
NEXT_UNIT = "E008-M154 budget-aware utility objective contract / policy-selection rule"

METHOD_POLICY = "budget_guarded_confidence_path_repair_v1"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_POLICY = "budget_guarded_confidence_only_v1"
SOURCE_GAP_ONLY_POLICY = "budget_guarded_source_gap_only_v1"
NO_VISIT_GUARD_POLICY = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR_POLICY = "budget_guarded_no_confidence_floor_v1"

POLICY_ORDER = [
    METHOD_POLICY,
    DETECTOR_POLICY,
    CONFIDENCE_ONLY_POLICY,
    SOURCE_GAP_ONLY_POLICY,
    NO_VISIT_GUARD_POLICY,
    NO_CONFIDENCE_FLOOR_POLICY,
]

COMPARISONS = [
    (METHOD_POLICY, DETECTOR_POLICY, "selected_vs_detector_confidence"),
    (METHOD_POLICY, CONFIDENCE_ONLY_POLICY, "selected_vs_confidence_only"),
    (METHOD_POLICY, SOURCE_GAP_ONLY_POLICY, "selected_vs_source_gap_only"),
    (METHOD_POLICY, NO_VISIT_GUARD_POLICY, "selected_vs_no_visit_guard"),
    (METHOD_POLICY, NO_CONFIDENCE_FLOOR_POLICY, "selected_vs_no_confidence_floor"),
    (NO_VISIT_GUARD_POLICY, DETECTOR_POLICY, "no_visit_guard_vs_detector_confidence"),
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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def metric_aggregate_rows(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def scan_policy_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]


def policy_role(policy_id: str) -> str:
    return {
        METHOD_POLICY: "selected_budget_guarded_method",
        DETECTOR_POLICY: "protected_detector_confidence_baseline",
        CONFIDENCE_ONLY_POLICY: "confidence_floor_ablation",
        SOURCE_GAP_ONLY_POLICY: "source_gap_trigger_ablation",
        NO_VISIT_GUARD_POLICY: "visit_guard_ablation",
        NO_CONFIDENCE_FLOOR_POLICY: "negative_no_confidence_floor_ablation",
    }.get(policy_id, "unknown")


def policy_metrics(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "SR": finite_float(row.get("SR")),
        "SPL": finite_float(row.get("SPL")),
        "CandidateVisits_mean": finite_float(row.get("CandidateVisits_mean")),
        "PathLengthM_mean": finite_float(row.get("PathLengthM_mean")),
    }


def dominates(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    include_path_length: bool,
) -> bool:
    a_m = policy_metrics(a)
    b_m = policy_metrics(b)
    keys = ["SR", "SPL", "CandidateVisits_mean"]
    if include_path_length:
        keys.append("PathLengthM_mean")
    if any(a_m[key] is None or b_m[key] is None for key in keys):
        return False

    non_worse = [
        a_m["SR"] >= b_m["SR"],
        a_m["SPL"] >= b_m["SPL"],
        a_m["CandidateVisits_mean"] <= b_m["CandidateVisits_mean"],
    ]
    strict = [
        a_m["SR"] > b_m["SR"],
        a_m["SPL"] > b_m["SPL"],
        a_m["CandidateVisits_mean"] < b_m["CandidateVisits_mean"],
    ]
    if include_path_length:
        non_worse.append(a_m["PathLengthM_mean"] <= b_m["PathLengthM_mean"])
        strict.append(a_m["PathLengthM_mean"] < b_m["PathLengthM_mean"])
    return all(non_worse) and any(strict)


def build_pareto_policy_rows(aggregates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
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
        best_spl = max(
            [finite_float(row.get("SPL")) for row in aggregates.values() if finite_float(row.get("SPL")) is not None],
            default=None,
        )
        interpretation = "manual_review"
        if policy_id == METHOD_POLICY:
            if primary_dominators:
                interpretation = "selected_policy_is_dominated_in_primary_sr_spl_visit_space"
            elif expanded_dominators:
                interpretation = "selected_policy_is_dominated_even_when_path_length_is_counted"
            else:
                interpretation = "selected_policy_only_survives_when_path_length_tradeoff_is_counted"
        elif policy_id == NO_VISIT_GUARD_POLICY:
            interpretation = "best_spl_policy_but_visit_expensive_not_posthoc_selectable"
        elif policy_id == NO_CONFIDENCE_FLOOR_POLICY:
            interpretation = "negative_control_dominated_confidence_floor_is_needed"
        elif policy_id in {DETECTOR_POLICY, CONFIDENCE_ONLY_POLICY, SOURCE_GAP_ONLY_POLICY}:
            interpretation = "confidence_family_protected_frontier_baseline"
        rows.append(
            {
                "version": VERSION,
                "row_type": "pareto_policy",
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "SR": policy.get("SR"),
                "SPL": policy.get("SPL"),
                "CandidateVisits_mean": policy.get("CandidateVisits_mean"),
                "PathLengthM_mean": policy.get("PathLengthM_mean"),
                "success_rows": policy.get("success_rows"),
                "scan_task_policy_rows": policy.get("scan_task_policy_rows"),
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
    spl_delta = delta(method.get("SPL"), baseline.get("SPL"))
    visit_delta = delta(method.get("CandidateVisits"), baseline.get("CandidateVisits"))
    path_delta = delta(method.get("PathLengthM"), baseline.get("PathLengthM"))
    sr_delta = delta(method.get("SR"), baseline.get("SR"))
    eps = 1e-9
    if sr_delta is not None and sr_delta < -eps:
        return "sr_regression"
    if spl_delta is None or visit_delta is None:
        return "missing_metric"
    if spl_delta > eps and visit_delta <= eps:
        return "clean_spl_gain"
    if spl_delta > eps and visit_delta > eps:
        return "spl_gain_with_visit_cost"
    if spl_delta < -eps and visit_delta > eps:
        return "spl_loss_and_more_visits"
    if spl_delta < -eps and visit_delta <= eps:
        return "spl_loss_without_more_visits"
    if abs(spl_delta) <= eps and visit_delta < -eps:
        return "visit_saving_spl_tie"
    if abs(spl_delta) <= eps and visit_delta > eps:
        return "visit_regression_spl_tie"
    if path_delta is not None and path_delta < -eps:
        return "path_gain_only"
    return "neutral_or_tie"


def indexed_scan_rows(scan_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row
    return grouped


def build_episode_tradeoff_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = indexed_scan_rows(scan_rows)
    out: list[dict[str, Any]] = []
    for uid, rows in sorted(grouped.items()):
        for method_id, baseline_id, comparison_id in COMPARISONS:
            method = rows.get(method_id)
            baseline = rows.get(baseline_id)
            if not method or not baseline:
                continue
            out.append(
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
                    "method_success_source_role": method.get("success_source_role"),
                    "baseline_success_source_role": baseline.get("success_source_role"),
                    "tradeoff_class": classify_tradeoff(method, baseline),
                }
            )
    return out


def summarize_tradeoffs(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        grouped[(str(row.get("comparison_id")), str(row.get("tradeoff_class")))].append(row)
    out: list[dict[str, Any]] = []
    for (comparison_id, tradeoff_class), rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "row_type": "pareto_case_profile",
                "comparison_id": comparison_id,
                "tradeoff_class": tradeoff_class,
                "rows": len(rows),
                "mean_delta_SR": mean([finite_float(row.get("delta_SR")) for row in rows]),
                "mean_delta_SPL": mean([finite_float(row.get("delta_SPL")) for row in rows]),
                "mean_delta_CandidateVisits": mean(
                    [finite_float(row.get("delta_CandidateVisits")) for row in rows]
                ),
                "mean_delta_PathLengthM": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
            }
        )
    return out


def build_failure_diagnosis_rows(
    pareto_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    selected = next(row for row in pareto_rows if row["policy_id"] == METHOD_POLICY)
    no_visit = next(row for row in pareto_rows if row["policy_id"] == NO_VISIT_GUARD_POLICY)
    no_conf = next(row for row in pareto_rows if row["policy_id"] == NO_CONFIDENCE_FLOOR_POLICY)

    selected_vs_detector = [row for row in profile_rows if row["comparison_id"] == "selected_vs_detector_confidence"]
    more_visit_losses = sum(row["rows"] for row in selected_vs_detector if row["tradeoff_class"] == "spl_loss_and_more_visits")
    clean_gains = sum(row["rows"] for row in selected_vs_detector if row["tradeoff_class"] == "clean_spl_gain")
    path_gain_only = sum(row["rows"] for row in selected_vs_detector if row["tradeoff_class"] == "path_gain_only")

    return [
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "primary_policy_dominance_failure",
            "severity": "high",
            "fact": "The selected policy is dominated in primary SR/SPL/CandidateVisits space.",
            "evidence": f"primary_dominated_by={selected['primary_dominated_by']}",
            "agent_inference": "The current selected policy cannot be defended as a navigation-improving method.",
            "next_requirement": "Do not scale or claim this policy; convert the failure into an explicit utility/Pareto contract.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "path_length_gain_not_spl_gain",
            "severity": "high",
            "fact": "Selected policy reduces mean path length but loses mean SPL and uses more candidate visits than detector-confidence.",
            "evidence": f"clean_spl_gain_rows={clean_gains}, spl_loss_and_more_visits_rows={more_visit_losses}, path_gain_only_rows={path_gain_only}",
            "agent_inference": "Path cost is not useless, but path-length minimization alone is misaligned with the SR/SPL/search-budget objective.",
            "next_requirement": "Define a precommitted utility that trades off SPL, candidate visits, and path length before new execution.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "visit_guard_tradeoff",
            "severity": "medium",
            "fact": "`budget_guarded_no_visit_guard_v1` has the best SPL but higher candidate visits.",
            "evidence": f"SPL={fmt(no_visit['SPL'])}, CandidateVisits_mean={fmt(no_visit['CandidateVisits_mean'])}",
            "agent_inference": "The visit guard likely suppresses useful path repairs; removing it posthoc is not enough because search effort rises.",
            "next_requirement": "Use no-visit-guard only as a tradeoff witness, not as a selected method.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "confidence_floor_necessity",
            "severity": "low",
            "fact": "No-confidence-floor ablation is much worse.",
            "evidence": f"SPL={fmt(no_conf['SPL'])}, CandidateVisits_mean={fmt(no_conf['CandidateVisits_mean'])}",
            "agent_inference": "Current evidence supports confidence as a necessary reliability guard.",
            "next_requirement": "Keep confidence floor in the next method contract.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "source_gap_trigger_not_enough",
            "severity": "medium",
            "fact": "Source-gap-only matches detector-confidence, while selected source/path repair does not add positive aggregate evidence.",
            "evidence": "M152 pairwise summaries show confidence/source-gap family baselines remain protected.",
            "agent_inference": "The source-gap trigger is not yet a sufficient decision principle without budget-aware utility.",
            "next_requirement": "Treat source-gap as one feature in a utility objective rather than the main trigger.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_spl_pareto_failure_diagnostic",
            "supported": True,
            "claim_boundary": "M153 supports a diagnostic statement about why the selected policy fails and what tradeoff the next policy must resolve.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_budget_guarded_navigation_improvement",
            "supported": False,
            "claim_boundary": "Blocked because selected policy is dominated in primary SR/SPL/CandidateVisits space.",
        },
        {
            "version": VERSION,
            "claim_id": "no_visit_guard_as_selected_method",
            "supported": False,
            "claim_boundary": "Blocked because it is a posthoc ablation with higher candidate-visit cost.",
        },
        {
            "version": VERSION,
            "claim_id": "confidence_floor_needed",
            "supported": True,
            "claim_boundary": "Supported within the full-val-mini diagnostic table by the no-confidence-floor negative control.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still requires a precommitted method that beats protected baselines plus heldout transfer and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M153 is target-free and does not upgrade E006-M08's human-intent boundary.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "are_you_cherry_picking_no_visit_guard",
            "reviewer_response": "No. M153 records it as a Pareto witness because it improves SPL at higher visit cost; it is not selected as the method.",
        },
        {
            "version": VERSION,
            "issue_id": "why_not_call_path_repair_successful",
            "reviewer_response": "Path length decreases, but the precommitted paper-facing criteria include SR, SPL, and candidate visits. The selected policy fails those criteria.",
        },
        {
            "version": VERSION,
            "issue_id": "what_principle_follows_from_failure",
            "reviewer_response": "A semantic memory search policy should expose a budget-aware utility over confidence, stale-memory trust/source gap, path length, and candidate visits rather than optimizing any one signal alone.",
        },
        {
            "version": VERSION,
            "issue_id": "does_this_support_final_navigation",
            "reviewer_response": "No. It supports a failure diagnosis and next method contract only; final SR/SPL claims need heldout and external baseline evidence.",
        },
        {
            "version": VERSION,
            "issue_id": "is_this_forcing_the_hypothesis",
            "reviewer_response": "The positive claim is explicitly rejected when gates fail. The next route is a principle derived from the observed conflict, not a threshold adjustment.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "claim_selected_budget_guarded_policy",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Selected policy is dominated in primary SR/SPL/CandidateVisits space.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "promote_no_visit_guard_policy",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "No-visit-guard is posthoc and visit-expensive even though it has best SPL.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but the internal utility/Pareto contract should be fixed before another heavy run.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "budget_aware_utility_contract",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The failure diagnosis points to an explicit utility over confidence, path length, candidate visits, and source-gap/trust signals.",
            "launch_long_job_now": False,
        },
    ]


def build_coverage(
    m151_coverage: dict[str, Any],
    m152_coverage: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    pareto_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    diagnosis_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    selected = next(row for row in pareto_rows if row["policy_id"] == METHOD_POLICY)
    no_visit = next(row for row in pareto_rows if row["policy_id"] == NO_VISIT_GUARD_POLICY)
    primary_frontier = [row["policy_id"] for row in pareto_rows if row["primary_pareto_member"]]
    expanded_frontier = [row["policy_id"] for row in pareto_rows if row["expanded_pareto_member"]]
    status = READY_STATUS if not missing_inputs and selected["primary_dominated_by"] else BLOCKED_STATUS
    positive_ready = False
    return {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m151_status": m151_coverage.get("status"),
        "m152_status": m152_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "metric_rows": len(metric_rows),
        "scan_task_policy_rows": len(scan_rows),
        "episode_tradeoff_rows": len(episode_rows),
        "pareto_policy_rows": len(pareto_rows),
        "pareto_case_profile_rows": len(profile_rows),
        "failure_diagnosis_rows": len(diagnosis_rows),
        "primary_frontier_policy_ids": primary_frontier,
        "expanded_frontier_policy_ids": expanded_frontier,
        "selected_policy_id": METHOD_POLICY,
        "selected_primary_dominated_by": selected["primary_dominated_by"],
        "selected_expanded_dominated_by": selected["expanded_dominated_by"],
        "no_visit_guard_best_spl": bool(no_visit["is_best_spl_policy"]),
        "positive_navigation_improvement_ready": positive_ready,
        "final_real_navigation_claim_ready": False,
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


def profile_count(profile_rows: list[dict[str, Any]], comparison_id: str, tradeoff_class: str) -> int:
    return sum(
        int(row.get("rows") or 0)
        for row in profile_rows
        if row.get("comparison_id") == comparison_id and row.get("tradeoff_class") == tradeoff_class
    )


def build_report(
    coverage: dict[str, Any],
    pareto_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    diagnosis_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected = next(row for row in pareto_rows if row["policy_id"] == METHOD_POLICY)
    detector = next(row for row in pareto_rows if row["policy_id"] == DETECTOR_POLICY)
    no_visit = next(row for row in pareto_rows if row["policy_id"] == NO_VISIT_GUARD_POLICY)
    no_conf = next(row for row in pareto_rows if row["policy_id"] == NO_CONFIDENCE_FLOOR_POLICY)
    selected_vs_detector_loss_more = profile_count(
        profile_rows, "selected_vs_detector_confidence", "spl_loss_and_more_visits"
    )
    selected_vs_detector_clean_gain = profile_count(
        profile_rows, "selected_vs_detector_confidence", "clean_spl_gain"
    )
    no_visit_vs_detector_gain_cost = profile_count(
        profile_rows, "no_visit_guard_vs_detector_confidence", "spl_gain_with_visit_cost"
    )
    selected_route = next(row for row in route_rows if row["selected"])

    return "\n".join(
        [
            "# E008-M153 Budget/SPL Pareto Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Input M151 status: `{coverage['m151_status']}`.",
            f"- Input M152 status: `{coverage['m152_status']}`.",
            f"- Scan-task-policy rows: {coverage['scan_task_policy_rows']}.",
            f"- Selected policy `{METHOD_POLICY}`: `SR` {fmt(selected['SR'])}, `SPL` {fmt(selected['SPL'])}, `CandidateVisits` {fmt(selected['CandidateVisits_mean'])}, `PathLengthM` {fmt(selected['PathLengthM_mean'])}.",
            f"- Protected detector-confidence `{DETECTOR_POLICY}`: `SR` {fmt(detector['SR'])}, `SPL` {fmt(detector['SPL'])}, `CandidateVisits` {fmt(detector['CandidateVisits_mean'])}, `PathLengthM` {fmt(detector['PathLengthM_mean'])}.",
            f"- Best-SPL ablation `{NO_VISIT_GUARD_POLICY}`: `SPL` {fmt(no_visit['SPL'])}, `CandidateVisits` {fmt(no_visit['CandidateVisits_mean'])}.",
            f"- Negative control `{NO_CONFIDENCE_FLOOR_POLICY}`: `SPL` {fmt(no_conf['SPL'])}, `CandidateVisits` {fmt(no_conf['CandidateVisits_mean'])}.",
            "",
            "## Pareto Result",
            "",
            markdown_table(
                pareto_rows,
                [
                    "policy_id",
                    "SR",
                    "SPL",
                    "CandidateVisits_mean",
                    "PathLengthM_mean",
                    "primary_pareto_member",
                    "primary_dominated_by",
                    "expanded_pareto_member",
                ],
            ),
            "",
            "## Failure Decomposition",
            "",
            f"- Selected-vs-detector clean SPL gain rows: {selected_vs_detector_clean_gain}.",
            f"- Selected-vs-detector SPL-loss-and-more-visits rows: {selected_vs_detector_loss_more}.",
            f"- No-visit-guard-vs-detector SPL-gain-with-visit-cost rows: {no_visit_vs_detector_gain_cost}.",
            "",
            markdown_table(
                diagnosis_rows,
                ["diagnosis_id", "severity", "fact", "agent_inference", "next_requirement"],
            ),
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
            "- Fact: the selected budget-guarded policy cannot support positive navigation improvement because it is dominated in the primary `SR`/`SPL`/candidate-visit space.",
            "- Fact: adding `PathLengthM` makes the tradeoff visible, but lower path length alone is not enough for the paper-facing navigation claim.",
            "- Agent inference: the next method should not simply pick the best observed ablation; it should precommit a budget-aware utility objective that explains when path repair is worth extra visits.",
            f"- Selected next unit: {selected_route['selected_next_unit']}.",
            "",
        ]
    )


def copy_artifacts_to_data_dir(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    metric_path = M151_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl"
    m151_coverage_path = M151_DIR / "coverage.json"
    m152_coverage_path = M152_DIR / "coverage.json"
    m152_policy_path = M152_DIR / "policy_result_interpretation_rows.jsonl"

    missing_inputs = [
        str(path)
        for path in [metric_path, m151_coverage_path, m152_coverage_path, m152_policy_path]
        if not path.exists()
    ]
    metric_rows = read_jsonl(metric_path)
    m151_coverage = read_json(m151_coverage_path)
    m152_coverage = read_json(m152_coverage_path)

    aggregates = metric_aggregate_rows(metric_rows)
    scan_rows = scan_policy_rows(metric_rows)
    pareto_rows = build_pareto_policy_rows(aggregates)
    episode_rows = build_episode_tradeoff_rows(scan_rows)
    profile_rows = summarize_tradeoffs(episode_rows)
    diagnosis_rows = build_failure_diagnosis_rows(pareto_rows, profile_rows)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()
    coverage = build_coverage(
        m151_coverage,
        m152_coverage,
        metric_rows,
        scan_rows,
        pareto_rows,
        episode_rows,
        profile_rows,
        diagnosis_rows,
        route_rows,
        missing_inputs,
    )

    outputs = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "pareto_policy_rows.jsonl",
        ARTIFACT_DIR / "episode_tradeoff_rows.jsonl",
        ARTIFACT_DIR / "pareto_case_profile_rows.jsonl",
        ARTIFACT_DIR / "failure_diagnosis_rows.jsonl",
        ARTIFACT_DIR / "claim_boundary_rows.jsonl",
        ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
        ARTIFACT_DIR / "route_decision_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]

    write_json(outputs[0], coverage)
    write_jsonl(outputs[1], pareto_rows)
    write_jsonl(outputs[2], episode_rows)
    write_jsonl(outputs[3], profile_rows)
    write_jsonl(outputs[4], diagnosis_rows)
    write_jsonl(outputs[5], claim_rows)
    write_jsonl(outputs[6], reviewer_rows)
    write_jsonl(outputs[7], route_rows)
    outputs[8].write_text(
        build_report(coverage, pareto_rows, profile_rows, diagnosis_rows, claim_rows, route_rows),
        encoding="utf-8",
    )
    copy_artifacts_to_data_dir(outputs)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
