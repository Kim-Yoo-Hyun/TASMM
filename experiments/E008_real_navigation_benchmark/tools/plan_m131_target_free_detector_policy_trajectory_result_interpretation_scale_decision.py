#!/usr/bin/env python3
"""Interpret E008-M130 target-free detector-policy trajectory results and decide scale route."""

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
M129_DIR = EXP_ROOT / "artifacts" / "E008-M129_target_free_detector_policy_trajectory_contract_v0"
M130_DIR = EXP_ROOT / "artifacts" / "E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0"
)

VERSION = "e008_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0"
READY_STATUS = "e008_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_ready"
BLOCKED_STATUS = "e008_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_blocked"
NEXT_UNIT = "E008-M132 target-free trajectory-aware visit-order repair contract"

METHOD_POLICY = "path_cost_ascending_reachable_subset_v0"
PRIMARY_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
ALL_CANDIDATE_POLICY = "detector_confidence_all_candidates_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"
POLICY_ORDER = [
    ALL_CANDIDATE_POLICY,
    PRIMARY_DETECTOR_POLICY,
    METHOD_POLICY,
    TRADEOFF_POLICY,
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


def finite_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def rows_by_scope(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == scope]


def policy_id(row: dict[str, Any]) -> str:
    return str(row.get("policy_id") or row.get("group_id"))


def build_policy_result_rows(
    plan_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plans = {policy_id(row): row for row in plan_rows}
    budget_full = {
        str(row.get("policy_id")): row
        for row in budget_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    }
    budget5 = {
        str(row.get("policy_id")): row
        for row in budget_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == 5
    }
    aggregates = {policy_id(row): row for row in rows_by_scope(metric_rows, "policy_aggregate")}
    detector = aggregates.get(PRIMARY_DETECTOR_POLICY, {})

    out: list[dict[str, Any]] = []
    for pid in POLICY_ORDER:
        plan = plans.get(pid, {})
        full = budget_full.get(pid, {})
        b5 = budget5.get(pid, {})
        metric = aggregates.get(pid, {})
        spl_delta = delta(metric.get("SPL"), detector.get("SPL"))
        path_delta = delta(metric.get("PathLengthM_mean"), detector.get("PathLengthM_mean"))
        visit_delta = delta(metric.get("CandidateVisits_mean"), detector.get("CandidateVisits_mean"))
        proxy_spl_delta = delta(metric.get("SPL"), full.get("GoalEvalProxySPL"))
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": pid,
                "m129_candidate_rows": plan.get("candidate_rows"),
                "m129_path_ready_candidate_rows": plan.get("path_ready_candidate_rows"),
                "m129_budget5_proxy_sr": b5.get("GoalEvalProxySR"),
                "m129_full_proxy_sr": full.get("GoalEvalProxySR"),
                "m129_full_proxy_spl": full.get("GoalEvalProxySPL"),
                "m129_proxy_first_hit_rank": full.get("primary_first_hit_rank_mean_over_success"),
                "m129_proxy_first_hit_cost_m": full.get("primary_first_hit_cost_m_mean_over_success"),
                "m130_success_rows": metric.get("success_rows"),
                "m130_scan_task_policy_rows": metric.get("scan_task_policy_rows"),
                "m130_SR": metric.get("SR"),
                "m130_SPL": metric.get("SPL"),
                "m130_PathLengthM_mean": metric.get("PathLengthM_mean"),
                "m130_CandidateVisits_mean": metric.get("CandidateVisits_mean"),
                "m130_StopRank_mean_over_success": metric.get("StopRank_mean_over_success"),
                "delta_SPL_vs_detector_confidence_reachable": spl_delta,
                "delta_PathLengthM_vs_detector_confidence_reachable": path_delta,
                "delta_CandidateVisits_vs_detector_confidence_reachable": visit_delta,
                "trajectory_minus_proxy_SPL": proxy_spl_delta,
                "supports_executed_smoke": bool(metric.get("success_rows")),
                "supports_positive_navigation_policy_claim": supports_positive_policy(pid, metric, detector),
                "supports_final_real_navigation_claim": False,
                "interpretation": interpret_policy(pid, spl_delta, path_delta, visit_delta, proxy_spl_delta),
            }
        )
    return out


def supports_positive_policy(pid: str, metric: dict[str, Any], detector: dict[str, Any]) -> bool:
    if pid != METHOD_POLICY:
        return False
    sr_delta = delta(metric.get("SR"), detector.get("SR"))
    spl_delta = delta(metric.get("SPL"), detector.get("SPL"))
    if sr_delta is None or spl_delta is None:
        return False
    return sr_delta > 0 or (sr_delta == 0 and spl_delta > 0)


def interpret_policy(
    pid: str,
    spl_delta: float | None,
    path_delta: float | None,
    visit_delta: float | None,
    proxy_spl_delta: float | None,
) -> str:
    if pid == PRIMARY_DETECTOR_POLICY:
        return "primary_detector_confidence_baseline_is_best_executed_spl_and_visit_efficiency_on_m130"
    if pid == ALL_CANDIDATE_POLICY:
        return "all_candidate_detector_baseline_matches_primary_detector_spl_but_counts_extra_unreachable_candidates"
    if pid == METHOD_POLICY:
        if (spl_delta or 0.0) < 0 and (path_delta or 0.0) > 0:
            return "source_to_candidate_path_cost_ordering_fails_as_trajectory_policy_due_myopic_tour_cost_mismatch"
        if (proxy_spl_delta or 0.0) < 0:
            return "proxy_spl_overestimates_path_cost_policy_execution_efficiency"
        return "path_cost_policy_requires_manual_review"
    if pid == TRADEOFF_POLICY:
        return "confidence_path_cost_tradeoff_also_loses_spl_to_detector_confidence_in_execution"
    return "requires_manual_review"


def build_proxy_trajectory_consistency_rows(
    plan_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plans = {policy_id(row): row for row in plan_rows}
    budget_full = {
        str(row.get("policy_id")): row
        for row in budget_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    }
    metrics = {policy_id(row): row for row in rows_by_scope(metric_rows, "policy_aggregate")}
    rows: list[dict[str, Any]] = []
    for pid in POLICY_ORDER:
        plan = plans.get(pid, {})
        proxy = budget_full.get(pid, {})
        metric = metrics.get(pid, {})
        proxy_spl = finite_float(proxy.get("GoalEvalProxySPL"))
        trajectory_spl = finite_float(metric.get("SPL"))
        proxy_rank = finite_float(proxy.get("primary_first_hit_rank_mean_over_success"))
        trajectory_rank = finite_float(metric.get("StopRank_mean_over_success"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "proxy_to_trajectory_consistency",
                "policy_id": pid,
                "proxy_SR": proxy.get("GoalEvalProxySR"),
                "trajectory_SR": metric.get("SR"),
                "proxy_SPL": proxy_spl,
                "trajectory_SPL": trajectory_spl,
                "delta_trajectory_minus_proxy_SPL": delta(trajectory_spl, proxy_spl),
                "proxy_first_hit_rank": proxy_rank,
                "trajectory_stop_rank": trajectory_rank,
                "delta_trajectory_minus_proxy_hit_rank": delta(trajectory_rank, proxy_rank),
                "proxy_first_hit_cost_m": proxy.get("primary_first_hit_cost_m_mean_over_success"),
                "trajectory_path_length_m": metric.get("PathLengthM_mean"),
                "m127_proxy_spl_for_reporting": plan.get("m127_proxy_spl_for_reporting"),
                "consistency_status": classify_proxy_consistency(pid, proxy_spl, trajectory_spl),
                "interpretation": interpret_proxy_consistency(pid, proxy_spl, trajectory_spl),
            }
        )
    return rows


def classify_proxy_consistency(pid: str, proxy_spl: float | None, trajectory_spl: float | None) -> str:
    if proxy_spl is None or trajectory_spl is None:
        return "missing"
    if pid in {METHOD_POLICY, TRADEOFF_POLICY} and proxy_spl > 0.7 and trajectory_spl < 0.2:
        return "proxy_execution_spl_flip"
    if trajectory_spl >= proxy_spl:
        return "trajectory_at_least_proxy_spl"
    return "trajectory_lower_than_proxy_spl"


def interpret_proxy_consistency(pid: str, proxy_spl: float | None, trajectory_spl: float | None) -> str:
    status = classify_proxy_consistency(pid, proxy_spl, trajectory_spl)
    if status == "proxy_execution_spl_flip":
        return "M129 proxy used source-to-candidate cumulative cost; M130 execution accumulates candidate-to-candidate path, exposing tour-cost mismatch."
    if pid == PRIMARY_DETECTOR_POLICY:
        return "Detector-confidence ordering finds the successful stop early in actual execution despite lower proxy SPL."
    return "Proxy and trajectory metrics should be interpreted separately."


def build_failure_diagnosis_rows(
    attempt_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attempts_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempt_rows:
        attempts_by_policy[str(row.get("policy_id"))].append(row)
    metrics = {policy_id(row): row for row in rows_by_scope(metric_rows, "policy_aggregate")}

    out: list[dict[str, Any]] = []
    for pid in POLICY_ORDER:
        rows = sorted(attempts_by_policy.get(pid, []), key=lambda row: finite_int(row.get("visit_rank")) or 10**9)
        success_rank = next((finite_int(row.get("visit_rank")) for row in rows if row.get("eval_success")), None)
        before_success = [row for row in rows if success_rank is None or (finite_int(row.get("visit_rank")) or 0) < success_rank]
        executed_before = [row for row in before_success if row.get("attempt_status") == "executed_no_success"]
        path_not_found_before = [row for row in before_success if row.get("attempt_status") == "path_not_found"]
        wasted_path = sum(finite_float(row.get("segment_geodesic_m")) or 0.0 for row in executed_before)
        mean_target_gap = mean([finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) for row in executed_before])
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_failure_diagnosis",
                "policy_id": pid,
                "attempt_rows": len(rows),
                "success_rank": success_rank,
                "executed_no_success_before_success": len(executed_before),
                "path_not_found_before_success": len(path_not_found_before),
                "wasted_path_before_success_m": wasted_path,
                "mean_unsuccessful_stop_to_nearest_eval_viewpoint_xz_m": mean_target_gap,
                "final_PathLengthM_mean": metrics.get(pid, {}).get("PathLengthM_mean"),
                "final_SPL": metrics.get(pid, {}).get("SPL"),
                "failure_mechanism": classify_failure_mechanism(pid, len(executed_before), wasted_path, mean_target_gap),
                "next_validation_requirement": next_validation_requirement(pid),
            }
        )
    return out


def classify_failure_mechanism(pid: str, executed_no_success: int, wasted_path: float, mean_target_gap: float | None) -> str:
    if pid == METHOD_POLICY and executed_no_success >= 8 and wasted_path > 80:
        return "myopic_source_to_candidate_cost_visits_many_target_far_stops_before_success"
    if pid == TRADEOFF_POLICY and executed_no_success >= 8:
        return "confidence_path_tradeoff_still_prioritizes_target_far_low_source_cost_stops"
    if pid == PRIMARY_DETECTOR_POLICY:
        return "detector_confidence_finds_target_near_stop_early_despite_one_path_not_found_candidate"
    if pid == ALL_CANDIDATE_POLICY:
        return "all_candidate_baseline_extra_blocked_candidates_increase_visit_accounting"
    if mean_target_gap is not None and mean_target_gap > 5:
        return "candidate_order_visits_target_far_stops"
    return "manual_review"


def next_validation_requirement(pid: str) -> str:
    if pid in {METHOD_POLICY, TRADEOFF_POLICY}:
        return "repair_policy_with_candidate_to_candidate_or_online_current_pose_path_cost_before_scale"
    if pid in {PRIMARY_DETECTOR_POLICY, ALL_CANDIDATE_POLICY}:
        return "keep_as_strong_baseline_for_m132_repair_comparison"
    return "manual_review"


def build_pairwise_interpretation_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(pairwise_rows, key=lambda item: str(item.get("baseline_policy_id"))):
        spl_delta = finite_float(row.get("delta_SPL"))
        path_delta = finite_float(row.get("delta_PathLengthM"))
        visit_delta = delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits"))
        out.append(
            {
                "version": VERSION,
                "row_type": "path_cost_pairwise_interpretation",
                "method_policy_id": row.get("method_policy_id"),
                "baseline_policy_id": row.get("baseline_policy_id"),
                "delta_SR": row.get("delta_SR"),
                "delta_SPL": spl_delta,
                "delta_PathLengthM": path_delta,
                "delta_CandidateVisits": visit_delta,
                "supports_positive_navigation_policy_claim": bool(
                    finite_float(row.get("delta_SR")) is not None
                    and spl_delta is not None
                    and (finite_float(row.get("delta_SR")) or 0.0) >= 0
                    and spl_delta > 0
                ),
                "interpretation": interpret_pairwise(row.get("baseline_policy_id"), spl_delta, path_delta, visit_delta),
            }
        )
    return out


def interpret_pairwise(
    baseline_id: object,
    spl_delta: float | None,
    path_delta: float | None,
    visit_delta: float | None,
) -> str:
    baseline = str(baseline_id)
    if baseline in {ALL_CANDIDATE_POLICY, PRIMARY_DETECTOR_POLICY}:
        return "path_cost_ties_sr_but_loses_spl_path_length_and_visit_efficiency_to_detector_confidence"
    if baseline == TRADEOFF_POLICY and spl_delta is not None and spl_delta < 0:
        return "path_cost_does_not_improve_over_confidence_path_cost_tradeoff"
    if visit_delta is not None and visit_delta > 0:
        return "path_cost_requires_visit_efficiency_repair"
    return "manual_review"


def build_gate_rows(
    coverage_m130: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    proxy_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> list[dict[str, Any]]:
    policy = {str(row.get("policy_id")): row for row in policy_rows}
    method = policy.get(METHOD_POLICY, {})
    detector = policy.get(PRIMARY_DETECTOR_POLICY, {})
    proxy_flip = any(
        row.get("policy_id") in {METHOD_POLICY, TRADEOFF_POLICY}
        and row.get("consistency_status") == "proxy_execution_spl_flip"
        for row in proxy_rows
    )
    return [
        gate(
            "m130_input_ready",
            "pass" if not missing_inputs and coverage_m130.get("status") == "e008_m130_target_free_detector_policy_trajectory_execution_smoke_ready" else "fail",
            "M130 trajectory execution artifact is present and ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(coverage_m130.get("leakage_audit_pass")) else "fail",
            "ObjectNav goal/viewpoint fields are metric-only and not policy inputs.",
            blocks_final=True,
        ),
        gate(
            "trajectory_execution_plumbing",
            "pass" if finite_float(coverage_m130.get("trajectory_SR")) == 1.0 else "warning",
            "M130 executes one target-free case and all four policies reach the eval viewpoint.",
            blocks_final=False,
        ),
        gate(
            "positive_sr_gain",
            "fail" if (delta(method.get("m130_SR"), detector.get("m130_SR")) or 0.0) <= 0 else "pass",
            "All policies tie on SR in the one-case execution.",
            blocks_final=True,
        ),
        gate(
            "positive_spl_gain",
            "fail" if (delta(method.get("m130_SPL"), detector.get("m130_SPL")) or 0.0) <= 0 else "pass",
            "Path-cost policy loses SPL to detector-confidence baselines.",
            blocks_final=True,
        ),
        gate(
            "visit_efficiency",
            "fail" if (delta(method.get("m130_CandidateVisits_mean"), detector.get("m130_CandidateVisits_mean")) or 0.0) > 0 else "pass",
            "Path-cost policy visits more candidates before success than detector confidence.",
            blocks_final=True,
        ),
        gate(
            "proxy_to_trajectory_consistency",
            "fail" if proxy_flip else "pass",
            "M129 proxy SPL ranks path-cost high, but M130 execution shows a large SPL collapse.",
            blocks_final=True,
        ),
        gate(
            "denominator_scale",
            "fail",
            "M130 is one target-free case; no generality claim is possible.",
            blocks_final=True,
        ),
        gate(
            "external_navigation_baselines",
            "fail",
            "`VLFM`, `HM3D-OVON`, and GOAT-style baselines are not integrated for this route.",
            blocks_final=True,
        ),
        gate(
            "diagnostic_table_ready",
            "pass",
            "M130 is useful as an executed diagnostic showing a proxy-to-trajectory mismatch.",
            blocks_final=False,
        ),
        gate(
            "repair_before_scale",
            "pass",
            "Next step should repair trajectory visit ordering before scale-up.",
            blocks_final=False,
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


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "executed_target_free_trajectory_smoke",
            True,
            "M130 executes one target-free detector-policy trajectory case in Docker Habitat.",
        ),
        claim(
            "proxy_to_trajectory_failure_diagnosis",
            True,
            "M131 identifies that source-to-candidate path-cost proxy can invert under candidate-to-candidate trajectory execution.",
        ),
        claim(
            "path_cost_navigation_improvement",
            False,
            "Path-cost policy ties SR but loses SPL, path length, and visit efficiency to detector-confidence baselines.",
        ),
        claim(
            "deployable_search_policy",
            False,
            "Budget-5 proxy fails for path-cost policies and M130 is full-ranked one-case execution.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Needs trajectory-aware repair, scale, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M130/M131 use a structured target-free search context only and do not test human intent.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "claim_id": claim_id,
        "supported": supported,
        "claim_boundary": boundary,
    }


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "does_m130_prove_navigation_improvement",
            "No. M130 proves executable metric plumbing, but the path-cost method loses SPL to detector-confidence baselines.",
        ),
        defense(
            "why_did_path_cost_fail",
            "The policy ranks candidates by source-to-candidate cost, while executed navigation accumulates candidate-to-candidate path length after each stop.",
        ),
        defense(
            "why_not_scale_now",
            "Scaling a policy with negative one-case SPL evidence would make a weak paper table; repair the visit-order principle first.",
        ),
        defense(
            "why_keep_detector_confidence_baseline",
            "Detector-confidence reachable subset is the strongest executed baseline in M130 and must remain in all future comparisons.",
        ),
        defense(
            "is_human_intent_supported",
            "No. E006-M08 remains the active human-intent boundary; M130/M131 do not change that.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_current_path_cost_policy",
            "decision": "reject_now",
            "selected": False,
            "reason": "M130 path-cost policy loses SPL and path length to detector-confidence baselines.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "record_m130_as_diagnostic_execution_table",
            "decision": "select",
            "selected": True,
            "reason": "M130 is useful as executable evidence and a proxy-to-trajectory failure diagnosis.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "trajectory_aware_visit_order_repair_contract",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "Next policy must use online/current-pose or candidate-to-candidate path cost, not only source-to-candidate cost.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_sr_spl",
            "decision": "reject_now",
            "selected": False,
            "reason": "One-case diagnostic and negative method SPL do not support final navigation claim.",
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
        cells = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                value = fmt(value)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    proxy_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    selected_next = next((row for row in route_rows if row.get("selected_next_unit")), {})
    report = "\n".join(
        [
            "# E008-M131 Target-Free Detector-Policy Trajectory Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M130 status: `{coverage.get('m130_status')}`.",
            f"- M130 trajectory SR / SPL: {fmt(coverage.get('m130_trajectory_SR'))} / {fmt(coverage.get('m130_trajectory_SPL_mean'))}.",
            f"- Method policy SPL: {fmt(coverage.get('method_SPL'))}.",
            f"- Detector-confidence reachable SPL: {fmt(coverage.get('primary_detector_SPL'))}.",
            f"- Method delta SPL vs detector-confidence: {fmt(coverage.get('method_delta_SPL_vs_primary_detector'))}.",
            f"- Method delta path length vs detector-confidence: {fmt(coverage.get('method_delta_PathLengthM_vs_primary_detector'))}.",
            f"- Proxy-to-trajectory flip detected: {coverage.get('proxy_to_trajectory_flip_detected')}.",
            "",
            "## Policy Results",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "m130_SR",
                    "m130_SPL",
                    "m130_PathLengthM_mean",
                    "m130_CandidateVisits_mean",
                    "delta_SPL_vs_detector_confidence_reachable",
                    "interpretation",
                ],
            ),
            "",
            "## Proxy-To-Trajectory Consistency",
            "",
            markdown_table(
                proxy_rows,
                [
                    "policy_id",
                    "proxy_SPL",
                    "trajectory_SPL",
                    "delta_trajectory_minus_proxy_SPL",
                    "consistency_status",
                    "interpretation",
                ],
            ),
            "",
            "## Failure Diagnosis",
            "",
            markdown_table(
                failure_rows,
                [
                    "policy_id",
                    "success_rank",
                    "executed_no_success_before_success",
                    "wasted_path_before_success_m",
                    "failure_mechanism",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_final_real_navigation_claim", "rationale"]),
            "",
            "## Decision",
            "",
            "- Do not scale the current path-cost policy as a positive navigation result.",
            "- Keep M130 as a diagnostic execution table and failure case.",
            f"- Selected next unit: {selected_next.get('selected_next_unit')}.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m129_coverage = read_json(M129_DIR / "coverage.json")
    m130_coverage = read_json(M130_DIR / "coverage.json")
    plan_rows = read_jsonl(M129_DIR / "trajectory_execution_plan_rows.jsonl")
    budget_rows = read_jsonl(M129_DIR / "budget_proxy_summary_rows.jsonl")
    metric_rows = read_jsonl(M130_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    attempt_rows = read_jsonl(M130_DIR / "dynamic_stale_trajectory_attempt_rows.jsonl")
    pairwise_input_rows = read_jsonl(M130_DIR / "pairwise_policy_delta_rows.jsonl")
    leakage_rows = read_jsonl(M130_DIR / "leakage_audit_rows.jsonl")

    required_paths = [
        M129_DIR / "coverage.json",
        M129_DIR / "trajectory_execution_plan_rows.jsonl",
        M129_DIR / "budget_proxy_summary_rows.jsonl",
        M130_DIR / "coverage.json",
        M130_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        M130_DIR / "dynamic_stale_trajectory_attempt_rows.jsonl",
        M130_DIR / "pairwise_policy_delta_rows.jsonl",
        M130_DIR / "leakage_audit_rows.jsonl",
    ]
    missing_inputs = [str(path) for path in required_paths if not path.exists()]

    policy_rows = build_policy_result_rows(plan_rows, budget_rows, metric_rows)
    proxy_rows = build_proxy_trajectory_consistency_rows(plan_rows, budget_rows, metric_rows)
    failure_rows = build_failure_diagnosis_rows(attempt_rows, metric_rows)
    pairwise_rows = build_pairwise_interpretation_rows(pairwise_input_rows)
    gate_rows = build_gate_rows(m130_coverage, policy_rows, proxy_rows, missing_inputs)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    by_policy = {str(row.get("policy_id")): row for row in policy_rows}
    method = by_policy.get(METHOD_POLICY, {})
    detector = by_policy.get(PRIMARY_DETECTOR_POLICY, {})
    status = READY_STATUS if not missing_inputs and m130_coverage.get("status") == "e008_m130_target_free_detector_policy_trajectory_execution_smoke_ready" else BLOCKED_STATUS
    proxy_flip = any(row.get("consistency_status") == "proxy_execution_spl_flip" for row in proxy_rows)
    final_blockers = [
        row["gate_id"]
        for row in gate_rows
        if row.get("blocks_final_real_navigation_claim")
    ]

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m129_status": m129_coverage.get("status"),
        "m130_status": m130_coverage.get("status"),
        "m130_scan_task_policy_rows": m130_coverage.get("scan_task_policy_rows"),
        "m130_trajectory_attempt_rows": m130_coverage.get("trajectory_attempt_rows"),
        "m130_trajectory_success_rows": m130_coverage.get("trajectory_success_rows"),
        "m130_trajectory_SR": m130_coverage.get("trajectory_SR"),
        "m130_trajectory_SPL_mean": m130_coverage.get("trajectory_SPL_mean"),
        "method_policy_id": METHOD_POLICY,
        "primary_detector_policy_id": PRIMARY_DETECTOR_POLICY,
        "method_SR": method.get("m130_SR"),
        "method_SPL": method.get("m130_SPL"),
        "primary_detector_SR": detector.get("m130_SR"),
        "primary_detector_SPL": detector.get("m130_SPL"),
        "method_delta_SPL_vs_primary_detector": method.get("delta_SPL_vs_detector_confidence_reachable"),
        "method_delta_PathLengthM_vs_primary_detector": method.get("delta_PathLengthM_vs_detector_confidence_reachable"),
        "method_delta_CandidateVisits_vs_primary_detector": method.get("delta_CandidateVisits_vs_detector_confidence_reachable"),
        "proxy_to_trajectory_flip_detected": proxy_flip,
        "policy_result_rows": len(policy_rows),
        "proxy_consistency_rows": len(proxy_rows),
        "failure_diagnosis_rows": len(failure_rows),
        "pairwise_interpretation_rows": len(pairwise_rows),
        "gate_rows": len(gate_rows),
        "final_real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "diagnostic_execution_table_ready": status == READY_STATUS,
        "scale_current_path_cost_policy_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "final_navigation_blockers": final_blockers,
        "missing_inputs": missing_inputs,
    }

    output_names = [
        ("coverage.json", coverage),
        ("policy_result_interpretation_rows.jsonl", policy_rows),
        ("proxy_trajectory_consistency_rows.jsonl", proxy_rows),
        ("failure_diagnosis_rows.jsonl", failure_rows),
        ("pairwise_interpretation_rows.jsonl", pairwise_rows),
        ("gate_rows.jsonl", gate_rows),
        ("claim_boundary_rows.jsonl", claim_rows),
        ("reviewer_defense_rows.jsonl", reviewer_rows),
        ("route_decision_rows.jsonl", route_rows),
    ]
    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        for name, payload in output_names:
            path = output_dir / name
            if name.endswith(".jsonl"):
                write_jsonl(path, payload)  # type: ignore[arg-type]
            else:
                write_json(path, payload)

    write_report(coverage, policy_rows, proxy_rows, failure_rows, gate_rows, route_rows)
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
