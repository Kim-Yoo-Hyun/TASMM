#!/usr/bin/env python3
"""Interpret E008-M151 full-val-mini budget-guarded trajectory results."""

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
M150_DIR = EXP_ROOT / "artifacts" / "E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0"
M151_DIR = EXP_ROOT / "artifacts" / "E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0"
)

VERSION = "e008_m152_full_val_mini_budget_guarded_confidence_path_result_interpretation_v0"
READY_STATUS = "e008_m152_full_val_mini_budget_guarded_confidence_path_result_interpretation_ready"
BLOCKED_STATUS = "e008_m152_full_val_mini_budget_guarded_confidence_path_result_interpretation_blocked"
NEXT_UNIT = "E008-M153 full-val-mini budget/SPL Pareto failure decomposition / next-route decision"

METHOD_POLICY = "budget_guarded_confidence_path_repair_v1"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_BASELINE = "budget_guarded_confidence_only_v1"
SOURCE_GAP_ONLY_BASELINE = "budget_guarded_source_gap_only_v1"
NO_VISIT_GUARD_ABLATION = "budget_guarded_no_visit_guard_v1"
NO_CONFIDENCE_FLOOR_ABLATION = "budget_guarded_no_confidence_floor_v1"
POLICY_ORDER = [
    METHOD_POLICY,
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY_BASELINE,
    SOURCE_GAP_ONLY_BASELINE,
    NO_VISIT_GUARD_ABLATION,
    NO_CONFIDENCE_FLOOR_ABLATION,
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


def metric_aggregates(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def scan_metric_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]


def policy_role(policy_id: str) -> str:
    return {
        METHOD_POLICY: "selected_budget_guarded_method",
        PRIMARY_BASELINE: "protected_detector_confidence_baseline",
        CONFIDENCE_ONLY_BASELINE: "confidence_floor_ablation",
        SOURCE_GAP_ONLY_BASELINE: "source_gap_trigger_ablation",
        NO_VISIT_GUARD_ABLATION: "visit_guard_ablation",
        NO_CONFIDENCE_FLOOR_ABLATION: "negative_no_confidence_floor_ablation",
    }.get(policy_id, "unknown")


def interpret_policy(
    policy_id: str,
    spl_delta: float | None,
    visit_delta: float | None,
    path_delta: float | None,
    is_best_spl: bool,
) -> str:
    if policy_id == METHOD_POLICY:
        if (spl_delta or 0.0) < 0.0 and (visit_delta or 0.0) > 0.0:
            return "selected_policy_reduces_path_length_but_loses_spl_and_visit_efficiency_to_detector_confidence"
        if (spl_delta or 0.0) < 0.0:
            return "selected_policy_loses_spl_to_detector_confidence"
        return "selected_policy_requires_manual_review"
    if policy_id == PRIMARY_BASELINE:
        return "protected_naive_baseline_remains_stronger_than_selected_policy_on_spl_and_visits"
    if policy_id == CONFIDENCE_ONLY_BASELINE:
        return "confidence_only_matches_detector_confidence; selected_path_repair_adds_no_positive_aggregate_spl"
    if policy_id == SOURCE_GAP_ONLY_BASELINE:
        return "source_gap_only_matches_detector_confidence; source_gap_trigger_does_not_explain_selected_policy_gain"
    if policy_id == NO_VISIT_GUARD_ABLATION:
        return (
            "no_visit_guard_has_best_spl_but_more_candidate_visits; metric_tradeoff_requires_pareto_failure_analysis"
            if is_best_spl
            else "no_visit_guard_requires_manual_review"
        )
    if policy_id == NO_CONFIDENCE_FLOOR_ABLATION:
        return "removing_confidence_floor_is_strongly_negative; confidence_floor_is_necessary"
    if path_delta is not None:
        return "manual_review"
    return "missing_policy_metric"


def build_policy_result_rows(metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    primary = metrics.get(PRIMARY_BASELINE, {})
    best_spl = max(
        [finite_float(row.get("SPL")) for row in metrics.values() if finite_float(row.get("SPL")) is not None],
        default=None,
    )
    rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        row = metrics.get(policy_id, {})
        sr_delta = delta(row.get("SR"), primary.get("SR"))
        spl_delta = delta(row.get("SPL"), primary.get("SPL"))
        visit_delta = delta(row.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean"))
        path_delta = delta(row.get("PathLengthM_mean"), primary.get("PathLengthM_mean"))
        is_best_spl = best_spl is not None and finite_float(row.get("SPL")) == best_spl
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "success_rows": row.get("success_rows"),
                "scan_task_policy_rows": row.get("scan_task_policy_rows"),
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "StopRank_mean_over_success": row.get("StopRank_mean_over_success"),
                "delta_SR_vs_detector_confidence": sr_delta,
                "delta_SPL_vs_detector_confidence": spl_delta,
                "delta_PathLengthM_mean_vs_detector_confidence": path_delta,
                "delta_CandidateVisits_mean_vs_detector_confidence": visit_delta,
                "is_best_spl_policy": is_best_spl,
                "supports_positive_navigation_improvement": bool(
                    policy_id == METHOD_POLICY
                    and sr_delta is not None
                    and spl_delta is not None
                    and visit_delta is not None
                    and sr_delta >= 0.0
                    and spl_delta > 0.0
                    and visit_delta <= 0.0
                ),
                "supports_final_real_navigation_claim": False,
                "interpretation": interpret_policy(policy_id, spl_delta, visit_delta, path_delta, is_best_spl),
            }
        )
    return rows


def interpret_pairwise_summary(baseline_id: str, spl_delta: float | None, visit_delta: float | None) -> str:
    if baseline_id in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE, SOURCE_GAP_ONLY_BASELINE}:
        if (spl_delta or 0.0) < 0.0 and (visit_delta or 0.0) > 0.0:
            return "selected_method_loses_mean_spl_and_visit_efficiency_to_confidence_family_baseline"
        return "selected_method_does_not_show_required_gain_over_confidence_family"
    if baseline_id == NO_VISIT_GUARD_ABLATION:
        return "no_visit_guard_beats_selected_on_spl_but_uses_more_visits; Pareto tradeoff unresolved"
    if baseline_id == NO_CONFIDENCE_FLOOR_ABLATION:
        return "selected_method_beats_no_confidence_floor_negative_control; confidence_floor_needed"
    return "manual_review"


def build_pairwise_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        grouped[str(row.get("baseline_policy_id"))].append(row)

    out: list[dict[str, Any]] = []
    for baseline_id in sorted(grouped):
        rows = grouped[baseline_id]
        spl_deltas = [finite_float(row.get("delta_SPL")) for row in rows]
        sr_deltas = [finite_float(row.get("delta_SR")) for row in rows]
        path_deltas = [finite_float(row.get("delta_PathLengthM")) for row in rows]
        visit_deltas = [
            delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits")) for row in rows
        ]
        out.append(
            {
                "version": VERSION,
                "row_type": "pairwise_delta_summary",
                "method_policy_id": METHOD_POLICY,
                "baseline_policy_id": baseline_id,
                "rows": len(rows),
                "delta_SR_mean": mean(sr_deltas),
                "delta_SPL_mean": mean(spl_deltas),
                "delta_PathLengthM_mean": mean(path_deltas),
                "delta_CandidateVisits_mean": mean(visit_deltas),
                "method_better_spl_rows": sum(1 for value in spl_deltas if value is not None and value > 1e-9),
                "method_tie_spl_rows": sum(1 for value in spl_deltas if value is not None and abs(value) <= 1e-9),
                "method_worse_spl_rows": sum(1 for value in spl_deltas if value is not None and value < -1e-9),
                "method_fewer_visit_rows": sum(1 for value in visit_deltas if value is not None and value < -1e-9),
                "method_tie_visit_rows": sum(1 for value in visit_deltas if value is not None and abs(value) <= 1e-9),
                "method_more_visit_rows": sum(1 for value in visit_deltas if value is not None and value > 1e-9),
                "supports_positive_navigation_improvement": False,
                "interpretation": interpret_pairwise_summary(baseline_id, mean(spl_deltas), mean(visit_deltas)),
            }
        )
    return out


def compare_episode_profile(
    grouped: dict[str, dict[str, dict[str, Any]]],
    baseline_policy_id: str,
    interpretation: str,
) -> dict[str, Any]:
    better_spl = tie_spl = worse_spl = 0
    fewer_visit = tie_visit = more_visit = 0
    for rows in grouped.values():
        method = rows.get(METHOD_POLICY, {})
        baseline = rows.get(baseline_policy_id, {})
        spl_delta = delta(method.get("SPL"), baseline.get("SPL"))
        visit_delta = delta(method.get("CandidateVisits"), baseline.get("CandidateVisits"))
        if spl_delta is not None:
            if spl_delta > 1e-9:
                better_spl += 1
            elif spl_delta < -1e-9:
                worse_spl += 1
            else:
                tie_spl += 1
        if visit_delta is not None:
            if visit_delta < -1e-9:
                fewer_visit += 1
            elif visit_delta > 1e-9:
                more_visit += 1
            else:
                tie_visit += 1
    return {
        "version": VERSION,
        "row_type": "episode_delta_profile",
        "profile_id": f"method_vs_{baseline_policy_id}",
        "baseline_policy_id": baseline_policy_id,
        "episode_rows": len(grouped),
        "method_better_spl_rows": better_spl,
        "method_tie_spl_rows": tie_spl,
        "method_worse_spl_rows": worse_spl,
        "method_fewer_visit_rows": fewer_visit,
        "method_tie_visit_rows": tie_visit,
        "method_more_visit_rows": more_visit,
        "interpretation": interpretation,
    }


def build_episode_delta_profile_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row

    return [
        compare_episode_profile(
            grouped,
            PRIMARY_BASELINE,
            "selected_method_has_mixed_episode_spl_changes_and_more_visit_rows_than_fewer_visit_rows",
        ),
        compare_episode_profile(
            grouped,
            CONFIDENCE_ONLY_BASELINE,
            "confidence_only_is_equivalent_to_detector_confidence_for_this_policy_family",
        ),
        compare_episode_profile(
            grouped,
            SOURCE_GAP_ONLY_BASELINE,
            "source_gap_only_is_equivalent_to_detector_confidence_for_this_denominator",
        ),
        compare_episode_profile(
            grouped,
            NO_VISIT_GUARD_ABLATION,
            "no_visit_guard_wins_more_spl_rows_but_spends_more_candidate_visits",
        ),
        compare_episode_profile(
            grouped,
            NO_CONFIDENCE_FLOOR_ABLATION,
            "selected_method_recovers_the_no_confidence_floor_negative_control",
        ),
    ]


def gate(gate_id: str, status: str, rationale: str, *, blocks_final: bool) -> dict[str, Any]:
    return {
        "version": VERSION,
        "gate_id": gate_id,
        "gate_status": status,
        "rationale": rationale,
        "blocks_final_real_navigation_claim": blocks_final and status in {"fail", "warning"},
    }


def build_gate_rows(
    m151_coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> list[dict[str, Any]]:
    method = next(row for row in policy_rows if row["policy_id"] == METHOD_POLICY)
    detector_summary = next(row for row in pairwise_rows if row["baseline_policy_id"] == PRIMARY_BASELINE)
    no_visit_guard = next(row for row in policy_rows if row["policy_id"] == NO_VISIT_GUARD_ABLATION)
    no_conf_floor_summary = next(row for row in pairwise_rows if row["baseline_policy_id"] == NO_CONFIDENCE_FLOOR_ABLATION)
    source_gap_summary = next(row for row in pairwise_rows if row["baseline_policy_id"] == SOURCE_GAP_ONLY_BASELINE)
    best_policy = next((row for row in policy_rows if row["is_best_spl_policy"]), {})
    return [
        gate(
            "m151_input_ready",
            "pass" if not missing_inputs and m151_coverage.get("status") == "e008_m151_full_val_mini_budget_guarded_confidence_path_execution_ready" else "fail",
            "M151 full-val-mini execution artifact is present and ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(m151_coverage.get("leakage_audit_pass")) else "fail",
            "ObjectNav goal/viewpoint fields are metric-only and not policy inputs.",
            blocks_final=True,
        ),
        gate(
            "denominator_execution",
            "pass" if m151_coverage.get("scan_task_policy_rows") == 180 else "fail",
            "M151 executed the frozen 30 episode x 6 policy full-val-mini suite.",
            blocks_final=True,
        ),
        gate(
            "protected_baseline_sr",
            "pass" if (finite_float(method.get("delta_SR_vs_detector_confidence")) or 0.0) >= 0.0 else "fail",
            "Selected policy ties detector-confidence SR.",
            blocks_final=True,
        ),
        gate(
            "protected_baseline_spl",
            "fail" if (finite_float(method.get("delta_SPL_vs_detector_confidence")) or 0.0) < 0.0 else "pass",
            "Selected policy loses mean SPL to the protected detector-confidence baseline.",
            blocks_final=True,
        ),
        gate(
            "visit_efficiency",
            "fail" if (finite_float(method.get("delta_CandidateVisits_mean_vs_detector_confidence")) or 0.0) > 0.0 else "pass",
            "Selected policy visits more candidates on average than detector-confidence.",
            blocks_final=True,
        ),
        gate(
            "path_length_reduction",
            "warning" if (finite_float(method.get("delta_PathLengthM_mean_vs_detector_confidence")) or 0.0) < 0.0 else "fail",
            "Selected policy reduces mean path length, but this does not offset SPL and visit-efficiency regressions.",
            blocks_final=True,
        ),
        gate(
            "selected_policy_is_best_spl",
            "fail" if best_policy.get("policy_id") != METHOD_POLICY else "pass",
            f"Best observed SPL policy is `{best_policy.get('policy_id')}`.",
            blocks_final=True,
        ),
        gate(
            "confidence_floor_necessity",
            "pass" if (finite_float(no_conf_floor_summary.get("delta_SPL_mean")) or 0.0) > 0.0 else "fail",
            "Selected policy beats the no-confidence-floor negative control, so confidence floor remains necessary.",
            blocks_final=False,
        ),
        gate(
            "source_gap_trigger_value",
            "fail" if (finite_float(source_gap_summary.get("delta_SPL_mean")) or 0.0) < 0.0 else "warning",
            "Source-gap-only ablation matches detector-confidence; selected source/path repair does not add positive aggregate evidence.",
            blocks_final=True,
        ),
        gate(
            "visit_guard_tradeoff",
            "warning" if bool(no_visit_guard.get("is_best_spl_policy")) else "pass",
            "No-visit-guard ablation has best SPL but more candidate visits, so the metric tradeoff must be decomposed before redesign.",
            blocks_final=True,
        ),
        gate(
            "episode_level_consistency",
            "warning",
            f"Selected policy beats detector SPL in {detector_summary.get('method_better_spl_rows')} / {detector_summary.get('rows')} rows, loses in {detector_summary.get('method_worse_spl_rows')} rows, and has more-visit rows {detector_summary.get('method_more_visit_rows')}.",
            blocks_final=True,
        ),
        gate(
            "positive_navigation_improvement",
            "fail",
            "Do not claim positive navigation improvement because protected SPL and visit-efficiency gates fail.",
            blocks_final=True,
        ),
        gate(
            "diagnostic_table_ready",
            "pass",
            "M151 is useful as a full-val-mini budget/path tradeoff diagnostic table.",
            blocks_final=False,
        ),
        gate(
            "final_real_navigation_claim",
            "fail",
            "Final SR/SPL claim still needs a selected method that beats protected baselines plus heldout/external navigation-search evidence.",
            blocks_final=True,
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "full_val_mini_budget_guarded_execution_table",
            True,
            "M151 executes the fixed 30-episode, 6-policy budget-guarded trajectory suite in Docker Habitat.",
        ),
        claim(
            "selected_budget_guarded_positive_navigation_improvement",
            False,
            "Selected policy ties SR but loses mean SPL and candidate-visit efficiency to detector-confidence.",
        ),
        claim(
            "confidence_floor_needed",
            True,
            "No-confidence-floor ablation is much worse, supporting confidence as a necessary guard.",
        ),
        claim(
            "path_repair_needed_as_current_form",
            False,
            "Selected path repair reduces mean path length but does not improve SPL or candidate visits over detector-confidence.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Requires a selected method that beats protected baselines, heldout transfer, external navigation/search baselines, and failure analysis.",
        ),
        claim(
            "deployable_search_policy",
            False,
            "M151 does not yet establish a fixed-budget deployed policy; it exposes a budget/SPL Pareto conflict.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M151 target-free rows do not use human intent; E006-M08 remains the active boundary.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "does_m151_prove_navigation_improvement",
            "No. It proves full-val-mini budget-guarded execution works, but selected policy loses mean SPL and visit efficiency to detector-confidence.",
        ),
        defense(
            "why_not_claim_path_length_improvement",
            "The selected policy reduces mean path length but still has lower SPL and more candidate visits; a path-length-only claim would be weaker than the predefined SR/SPL/search-efficiency gate.",
        ),
        defense(
            "why_not_pick_no_visit_guard_posthoc",
            "`budget_guarded_no_visit_guard_v1` has the best SPL but spends more candidate visits. It must be treated as a failure diagnosis / Pareto tradeoff, not a posthoc selected method.",
        ),
        defense(
            "what_did_m151_teach",
            "Confidence is necessary, but the current visit guard and path repair do not produce a protected-baseline improvement. The next method form must resolve SPL vs visit-budget tradeoff explicitly.",
        ),
        defense(
            "is_this_hypothesis_fitting",
            "No. The predefined protected-baseline gate fails, so M152 rejects the positive claim and routes to failure decomposition instead of changing thresholds.",
        ),
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "claim_selected_budget_guarded_navigation_improvement",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Selected policy loses mean SPL and visit efficiency to detector-confidence on full-val-mini.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "scale_selected_budget_guarded_policy",
            "decision": "reject_now",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Scaling a policy that fails the protected-baseline gate would violate the novelty discipline.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "record_m151_as_full_val_mini_diagnostic_table",
            "decision": "select",
            "selected": True,
            "selected_next_unit": None,
            "reason": "M151 is useful as a budget/path tradeoff diagnostic execution table.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "budget_spl_pareto_failure_decomposition",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "M153 should diagnose why no-visit-guard wins SPL, why selected policy reduces path length but loses SPL, and what claim/metric is defensible.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External baselines remain required, but the internal policy/metric tradeoff should be settled before another heavy integration.",
            "launch_long_job_now": False,
        },
    ]


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
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M152 Full-Val-Mini Budget-Guarded Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M151 status: `{coverage['m151_status']}`.",
            f"- Selected policy: `{METHOD_POLICY}`.",
            f"- Selected policy `SR` / `SPL`: {fmt(coverage['method_SR'])} / {fmt(coverage['method_SPL'])}.",
            f"- Detector-confidence `SR` / `SPL`: {fmt(coverage['detector_confidence_SR'])} / {fmt(coverage['detector_confidence_SPL'])}.",
            f"- Selected policy delta `SPL` / candidate visits / path length vs detector-confidence: {fmt(coverage['method_delta_SPL_vs_detector_confidence'])} / {fmt(coverage['method_delta_CandidateVisits_vs_detector_confidence'])} / {fmt(coverage['method_delta_PathLengthM_vs_detector_confidence'])}.",
            f"- Best SPL policy: `{coverage['best_SPL_policy_id']}` with `SPL` {fmt(coverage['best_SPL'])}.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            f"- Diagnostic table ready: {coverage['diagnostic_table_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Interpretation",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "policy_role",
                    "SR",
                    "SPL",
                    "PathLengthM_mean",
                    "CandidateVisits_mean",
                    "delta_SPL_vs_detector_confidence",
                    "delta_CandidateVisits_mean_vs_detector_confidence",
                    "is_best_spl_policy",
                    "supports_positive_navigation_improvement",
                ],
            ),
            "",
            "## Pairwise Summary",
            "",
            markdown_table(
                pairwise_rows,
                [
                    "baseline_policy_id",
                    "rows",
                    "delta_SR_mean",
                    "delta_SPL_mean",
                    "delta_PathLengthM_mean",
                    "delta_CandidateVisits_mean",
                    "method_better_spl_rows",
                    "method_worse_spl_rows",
                    "method_more_visit_rows",
                ],
            ),
            "",
            "## Episode Delta Profile",
            "",
            markdown_table(
                episode_rows,
                [
                    "profile_id",
                    "episode_rows",
                    "method_better_spl_rows",
                    "method_tie_spl_rows",
                    "method_worse_spl_rows",
                    "method_fewer_visit_rows",
                    "method_more_visit_rows",
                    "interpretation",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_final_real_navigation_claim", "rationale"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Claim Boundary",
            "",
            "- M152 rejects a positive navigation-improvement claim for the selected budget-guarded policy.",
            "- M151 remains a full-val-mini diagnostic execution table.",
            "- M153 should decompose the budget/SPL Pareto failure before any new scale-up or external-baseline push.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    m150_coverage = read_json(M150_DIR / "coverage.json")
    m151_coverage = read_json(M151_DIR / "coverage.json")
    metric_rows = read_jsonl(M151_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_raw = read_jsonl(M151_DIR / "pairwise_policy_delta_rows.jsonl")
    scan_rows = scan_metric_rows(metric_rows)

    required_inputs = [
        M150_DIR / "coverage.json",
        M151_DIR / "coverage.json",
        M151_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        M151_DIR / "pairwise_policy_delta_rows.jsonl",
        M151_DIR / "claim_boundary_rows.jsonl",
    ]
    missing_inputs = [str(path.relative_to(ROOT)) for path in required_inputs if not path.exists()]
    metrics = metric_aggregates(metric_rows)
    policy_rows = build_policy_result_rows(metrics)
    pairwise_rows = build_pairwise_summary_rows(pairwise_raw)
    episode_rows = build_episode_delta_profile_rows(scan_rows)
    gate_rows = build_gate_rows(m151_coverage, policy_rows, pairwise_rows, missing_inputs)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    best_policy = max(
        policy_rows,
        key=lambda row: finite_float(row.get("SPL")) if finite_float(row.get("SPL")) is not None else -1.0,
    )
    positive_ready = bool(method.get("SR") == primary.get("SR")) and (
        (delta(method.get("SPL"), primary.get("SPL")) or 0.0) > 0.0
    ) and ((delta(method.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean")) or 0.0) <= 0.0)
    missing_blocked = bool(missing_inputs)
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": BLOCKED_STATUS if missing_blocked else READY_STATUS,
        "missing_inputs": missing_inputs,
        "m150_status": m150_coverage.get("status"),
        "m151_status": m151_coverage.get("status"),
        "m151_scan_task_policy_rows": m151_coverage.get("scan_task_policy_rows"),
        "m151_trajectory_attempt_rows": m151_coverage.get("trajectory_attempt_rows"),
        "m151_leakage_audit_pass": m151_coverage.get("leakage_audit_pass"),
        "method_policy_id": METHOD_POLICY,
        "method_SR": method.get("SR"),
        "method_SPL": method.get("SPL"),
        "method_PathLengthM_mean": method.get("PathLengthM_mean"),
        "method_CandidateVisits_mean": method.get("CandidateVisits_mean"),
        "detector_confidence_SR": primary.get("SR"),
        "detector_confidence_SPL": primary.get("SPL"),
        "detector_confidence_PathLengthM_mean": primary.get("PathLengthM_mean"),
        "detector_confidence_CandidateVisits_mean": primary.get("CandidateVisits_mean"),
        "method_delta_SPL_vs_detector_confidence": delta(method.get("SPL"), primary.get("SPL")),
        "method_delta_PathLengthM_vs_detector_confidence": delta(
            method.get("PathLengthM_mean"), primary.get("PathLengthM_mean")
        ),
        "method_delta_CandidateVisits_vs_detector_confidence": delta(
            method.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean")
        ),
        "best_SPL_policy_id": best_policy.get("policy_id"),
        "best_SPL": best_policy.get("SPL"),
        "positive_navigation_improvement_ready": positive_ready,
        "scale_selected_policy_ready": False,
        "diagnostic_table_ready": not missing_blocked,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "gate_pass_count": sum(1 for row in gate_rows if row["gate_status"] == "pass"),
        "gate_warning_count": sum(1 for row in gate_rows if row["gate_status"] == "warning"),
        "gate_fail_count": sum(1 for row in gate_rows if row["gate_status"] == "fail"),
        "selected_next_unit": NEXT_UNIT,
        "launch_long_job_now": False,
    }

    report = build_report(coverage, policy_rows, pairwise_rows, episode_rows, gate_rows, route_rows)
    outputs = {
        "coverage.json": coverage,
        "policy_result_interpretation_rows.jsonl": policy_rows,
        "pairwise_delta_summary_rows.jsonl": pairwise_rows,
        "episode_delta_profile_rows.jsonl": episode_rows,
        "gate_rows.jsonl": gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
        "route_decision_rows.jsonl": route_rows,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
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
