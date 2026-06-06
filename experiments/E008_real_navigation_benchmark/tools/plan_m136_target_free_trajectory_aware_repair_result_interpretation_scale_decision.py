#!/usr/bin/env python3
"""Interpret E008-M135 trajectory-aware repair results and decide scale route."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M134_DIR = EXP_ROOT / "artifacts" / "E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0"
M135_DIR = EXP_ROOT / "artifacts" / "E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0"
)

VERSION = "e008_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0"
READY_STATUS = "e008_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_ready"
BLOCKED_STATUS = "e008_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_blocked"
NEXT_UNIT = "E008-M137 target-free confidence-preserving trajectory-aware repair contract"

METHOD_POLICY = "trajectory_greedy_confidence_path_repair_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_BASELINE = "trajectory_greedy_confidence_only_reachable_v0"
PATH_ONLY_BASELINE = "trajectory_greedy_path_only_reachable_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
POLICY_ORDER = [
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY_BASELINE,
    METHOD_POLICY,
    PATH_ONLY_BASELINE,
    PATH_COST_BASELINE,
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


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def metric_aggregates(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def build_policy_result_rows(metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence_only = metrics.get(CONFIDENCE_ONLY_BASELINE, primary)
    method = metrics.get(METHOD_POLICY, {})
    out: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        row = metrics.get(policy_id, {})
        delta_spl_primary = delta(row.get("SPL"), primary.get("SPL"))
        delta_spl_confidence = delta(row.get("SPL"), confidence_only.get("SPL"))
        delta_visits_primary = delta(row.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean"))
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "StopRank_mean_over_success": row.get("StopRank_mean_over_success"),
                "delta_SPL_vs_detector_confidence": delta_spl_primary,
                "delta_SPL_vs_confidence_only": delta_spl_confidence,
                "delta_CandidateVisits_vs_detector_confidence": delta_visits_primary,
                "supports_executed_smoke": bool(row.get("success_rows")),
                "supports_positive_navigation_policy_claim": policy_id == METHOD_POLICY
                and supports_positive_method(method, primary, confidence_only),
                "supports_failure_diagnosis": policy_id == METHOD_POLICY,
                "interpretation": interpret_policy(policy_id, delta_spl_primary, delta_spl_confidence, delta_visits_primary),
            }
        )
    return out


def policy_role(policy_id: str) -> str:
    if policy_id == METHOD_POLICY:
        return "selected_repair_policy"
    if policy_id == PRIMARY_BASELINE:
        return "primary_detector_confidence_baseline"
    if policy_id == CONFIDENCE_ONLY_BASELINE:
        return "strong_confidence_only_ablation"
    if policy_id == PATH_ONLY_BASELINE:
        return "path_only_ablation"
    if policy_id == PATH_COST_BASELINE:
        return "source_to_candidate_path_cost_baseline"
    return "unknown"


def supports_positive_method(
    method: dict[str, Any],
    primary: dict[str, Any],
    confidence_only: dict[str, Any],
) -> bool:
    sr_delta_primary = delta(method.get("SR"), primary.get("SR"))
    spl_delta_primary = delta(method.get("SPL"), primary.get("SPL"))
    spl_delta_conf = delta(method.get("SPL"), confidence_only.get("SPL"))
    if sr_delta_primary is None or spl_delta_primary is None or spl_delta_conf is None:
        return False
    return sr_delta_primary > 0 or (sr_delta_primary == 0 and spl_delta_primary > 0 and spl_delta_conf > 0)


def interpret_policy(
    policy_id: str,
    delta_spl_primary: float | None,
    delta_spl_confidence: float | None,
    delta_visits_primary: float | None,
) -> str:
    if policy_id == PRIMARY_BASELINE:
        return "detector_confidence_remains_the_strongest_executed_baseline_on_the_one_target_free_case"
    if policy_id == CONFIDENCE_ONLY_BASELINE:
        return "confidence_only_ties_detector_confidence_and_exposes_that_m135_repair_added_path_cost_without_needed_gain"
    if policy_id == METHOD_POLICY:
        if (delta_spl_primary or 0.0) < 0 and (delta_spl_confidence or 0.0) < 0:
            return "repair_improves_path_cost_family_but_breaks_confidence_efficiency_against_strong_baselines"
        if (delta_visits_primary or 0.0) > 0:
            return "repair_requires_more_candidate_visits_than_detector_confidence"
        return "method_requires_manual_review"
    if policy_id == PATH_ONLY_BASELINE:
        return "path_only_ablation_is_weaker_than_confidence_preserving_repair_but_not_a_strong_baseline"
    if policy_id == PATH_COST_BASELINE:
        return "source_to_candidate_path_cost_baseline_remains_diagnostic_negative_after_m131"
    return "manual_review"


def build_pairwise_interpretation_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(pairwise_rows, key=lambda item: str(item.get("baseline_policy_id"))):
        baseline = str(row.get("baseline_policy_id"))
        spl_delta = finite_float(row.get("delta_SPL"))
        path_delta = finite_float(row.get("delta_PathLengthM"))
        visit_delta = delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits"))
        out.append(
            {
                "version": VERSION,
                "row_type": "repair_pairwise_interpretation",
                "method_policy_id": row.get("method_policy_id"),
                "baseline_policy_id": baseline,
                "delta_SR": row.get("delta_SR"),
                "delta_SPL": spl_delta,
                "delta_PathLengthM": path_delta,
                "delta_CandidateVisits": visit_delta,
                "supports_positive_navigation_policy_claim": baseline in {PATH_ONLY_BASELINE, PATH_COST_BASELINE}
                and (spl_delta or 0.0) > 0,
                "blocks_positive_navigation_policy_claim": baseline in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE}
                and (spl_delta is None or spl_delta <= 0),
                "interpretation": interpret_pairwise(baseline, spl_delta, path_delta, visit_delta),
            }
        )
    return out


def interpret_pairwise(
    baseline: str,
    spl_delta: float | None,
    path_delta: float | None,
    visit_delta: float | None,
) -> str:
    if baseline in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE}:
        return "selected_repair_ties_sr_but_loses_spl_path_length_and_visit_efficiency_to_confidence_baseline"
    if baseline == PATH_ONLY_BASELINE:
        return "selected_repair_beats_path_only_spl_with_fewer_visits_but_this_is_not_the_strong_baseline"
    if baseline == PATH_COST_BASELINE:
        return "selected_repair_corrects_source_to_candidate_path_cost_failure_but_only_against_a_known_negative_baseline"
    if visit_delta is not None and visit_delta > 0:
        return "selected_repair_increases_visit_count"
    if path_delta is not None and path_delta < 0:
        return "selected_repair_shortens_path_relative_to_this_baseline"
    return "manual_review"


def build_repair_diagnosis_rows(metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence = metrics.get(CONFIDENCE_ONLY_BASELINE, primary)
    path_only = metrics.get(PATH_ONLY_BASELINE, {})
    path_cost = metrics.get(PATH_COST_BASELINE, {})
    return [
        {
            "version": VERSION,
            "diagnosis_id": "what_m135_fixed",
            "diagnosis": "candidate_to_candidate_trajectory_cost_repair_reduces_the_extreme_path_cost_failure",
            "evidence": (
                f"repair SPL {fmt(method.get('SPL'))} > path-only SPL {fmt(path_only.get('SPL'))} "
                f"and path-cost SPL {fmt(path_cost.get('SPL'))}"
            ),
            "claim_use": "failure_diagnosis_only",
        },
        {
            "version": VERSION,
            "diagnosis_id": "what_m135_broke",
            "diagnosis": "trajectory_repair_overrides_or_dilutes_confidence_efficiency",
            "evidence": (
                f"repair SPL {fmt(method.get('SPL'))} < detector-confidence SPL {fmt(primary.get('SPL'))} "
                f"and confidence-only SPL {fmt(confidence.get('SPL'))}"
            ),
            "claim_use": "blocks_positive_navigation_policy_claim",
        },
        {
            "version": VERSION,
            "diagnosis_id": "next_design_principle",
            "diagnosis": "trajectory_cost_should_be_confidence_preserving_or_guarded_not_a_replacement_for_confidence_ordering",
            "evidence": "M135 confidence-only and detector-confidence baselines succeed earlier with shorter executed paths.",
            "claim_use": "input_to_m137_contract",
        },
    ]


def build_gate_rows(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> list[dict[str, Any]]:
    method = next((row for row in policy_rows if row.get("policy_id") == METHOD_POLICY), {})
    loses_to_confidence = any(
        row.get("baseline_policy_id") in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE}
        and (finite_float(row.get("delta_SPL")) is None or (finite_float(row.get("delta_SPL")) or 0.0) <= 0)
        for row in pairwise_rows
    )
    beats_path_family = all(
        (finite_float(row.get("delta_SPL")) or 0.0) > 0
        for row in pairwise_rows
        if row.get("baseline_policy_id") in {PATH_ONLY_BASELINE, PATH_COST_BASELINE}
    )
    return [
        gate(
            "m135_input_ready",
            "pass" if not missing_inputs and coverage.get("status") == "e008_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke_ready" else "fail",
            "M135 trajectory execution artifact is present and ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(coverage.get("leakage_audit_pass")) else "fail",
            "ObjectNav goal/viewpoint fields are metric-only and not policy inputs.",
            blocks_final=True,
        ),
        gate(
            "trajectory_execution_plumbing",
            "pass" if finite_float(coverage.get("trajectory_SR")) == 1.0 else "warning",
            "M135 executes one target-free repair case and all five policies reach the eval viewpoint.",
            blocks_final=False,
        ),
        gate(
            "path_family_repair_diagnostic",
            "pass" if beats_path_family else "warning",
            "Selected repair improves over path-only and source-to-candidate path-cost baselines.",
            blocks_final=False,
        ),
        gate(
            "strong_confidence_baseline_spl",
            "fail" if loses_to_confidence else "pass",
            "Selected repair loses SPL to detector-confidence and confidence-only baselines.",
            blocks_final=True,
        ),
        gate(
            "visit_efficiency",
            "fail" if (finite_float(method.get("delta_CandidateVisits_vs_detector_confidence")) or 0.0) > 0 else "pass",
            "Selected repair visits more candidates than detector confidence before success.",
            blocks_final=True,
        ),
        gate(
            "positive_navigation_improvement",
            "fail" if not bool(method.get("supports_positive_navigation_policy_claim")) else "pass",
            "No positive SR/SPL gain over the strongest confidence baselines.",
            blocks_final=True,
        ),
        gate(
            "scale_current_repair",
            "fail",
            "Scaling the current selected repair would scale a negative strong-baseline result.",
            blocks_final=True,
        ),
        gate(
            "denominator_scale",
            "fail",
            "M135 is a one-case target-free trajectory smoke.",
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
            "M135 can be recorded as a trajectory-cost repair diagnostic.",
            blocks_final=False,
        ),
        gate(
            "confidence_preserving_repair_next",
            "pass",
            "Next design should preserve confidence ordering and use trajectory cost only as a guarded/tie-break signal.",
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
            "executed_target_free_repair_trajectory_smoke",
            True,
            "M135 executes one target-free trajectory-aware repair case in Docker Habitat.",
        ),
        claim(
            "trajectory_cost_failure_diagnosis",
            True,
            "M135 shows candidate-to-candidate trajectory cost helps relative to path-only/source-to-candidate path-cost baselines.",
        ),
        claim(
            "positive_navigation_improvement",
            False,
            "Selected repair loses `SPL` to detector-confidence and confidence-only baselines.",
        ),
        claim(
            "deployable_search_policy",
            False,
            "M135 is full-ranked one-case execution and does not establish a deployable fixed-budget policy.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Needs a confidence-preserving repair, scale, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "final_real_rgbd_open_vocab_robustness",
            False,
            "M135 tests trajectory execution over an existing detector route only; it does not establish final perception robustness.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M135 does not use human intent; E006-M08 remains the active human-intent boundary.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "does_m135_prove_navigation_improvement",
            "No. It proves executable repair plumbing and a path-family diagnostic, but the selected repair loses `SPL` to confidence baselines.",
        ),
        defense(
            "why_did_repair_fail_against_confidence",
            "The repair reduces trajectory path-cost failures but still visits lower-confidence/less efficient stops before the high-confidence target-near stop.",
        ),
        defense(
            "why_not_scale_current_repair",
            "A one-case negative result against the strongest baseline is not a defensible scale-up seed for a top-tier navigation claim.",
        ),
        defense(
            "what_principle_should_m137_test",
            "Trajectory cost should be a confidence-preserving guard or tie-breaker, not a replacement for detector-confidence ordering.",
        ),
        defense(
            "is_human_intent_changed_by_m135",
            "No. E006-M08 remains the human-intent boundary; M135 only tests trajectory execution.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_current_trajectory_greedy_confidence_path_repair",
            "decision": "reject_now",
            "selected": False,
            "reason": "Selected repair loses `SPL` and visit efficiency to detector-confidence / confidence-only baselines.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "record_m135_as_diagnostic_execution_table",
            "decision": "select",
            "selected": True,
            "reason": "M135 is useful as executed evidence that trajectory-cost repair helps only against weaker path-family baselines.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "confidence_preserving_trajectory_repair_contract",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "Next policy must preserve confidence efficiency and add trajectory cost as a guarded/tie-break signal.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_sr_spl",
            "decision": "reject_now",
            "selected": False,
            "reason": "One-case diagnostic with negative strong-baseline `SPL` does not support final navigation claim.",
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
    diagnosis_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M136 Target-Free Trajectory-Aware Repair Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M135 status: `{coverage['m135_status']}`.",
            f"- M135 scan-policy rows: {coverage['m135_scan_task_policy_rows']}.",
            f"- M135 trajectory attempts: {coverage['m135_trajectory_attempt_rows']}.",
            f"- M135 leakage audit pass: {coverage['m135_leakage_audit_pass']}.",
            f"- Selected repair policy: `{METHOD_POLICY}`.",
            f"- Selected repair `SPL`: {fmt(coverage['method_SPL'])}.",
            f"- Detector-confidence `SPL`: {fmt(coverage['detector_confidence_SPL'])}.",
            f"- Confidence-only `SPL`: {fmt(coverage['confidence_only_SPL'])}.",
            f"- Scale current repair: {coverage['scale_current_repair_ready']}.",
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
                    "supports_positive_navigation_policy_claim",
                ],
            ),
            "",
            "## Pairwise Interpretation",
            "",
            markdown_table(
                pairwise_rows,
                [
                    "baseline_policy_id",
                    "delta_SR",
                    "delta_SPL",
                    "delta_PathLengthM",
                    "delta_CandidateVisits",
                    "blocks_positive_navigation_policy_claim",
                ],
            ),
            "",
            "## Diagnosis",
            "",
            markdown_table(diagnosis_rows, ["diagnosis_id", "diagnosis", "claim_use"]),
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
            "- M136 supports an executed repair diagnostic, not a positive navigation-improvement claim.",
            "- Current repair should not be scaled as a main result because it loses `SPL` to confidence baselines.",
            "- Next route is a confidence-preserving trajectory repair contract before any scale-up.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    m134_coverage = read_json(M134_DIR / "coverage.json")
    m135_coverage = read_json(M135_DIR / "coverage.json")
    metric_rows = read_jsonl(M135_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_raw = read_jsonl(M135_DIR / "pairwise_policy_delta_rows.jsonl")

    required_inputs = [
        M134_DIR / "coverage.json",
        M135_DIR / "coverage.json",
        M135_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        M135_DIR / "pairwise_policy_delta_rows.jsonl",
        M135_DIR / "leakage_audit_rows.jsonl",
    ]
    missing_inputs = [str(path.relative_to(ROOT)) for path in required_inputs if not path.exists()]
    metrics = metric_aggregates(metric_rows)
    policy_rows = build_policy_result_rows(metrics)
    pairwise_rows = build_pairwise_interpretation_rows(pairwise_raw)
    diagnosis_rows = build_repair_diagnosis_rows(metrics)
    gate_rows = build_gate_rows(m135_coverage, policy_rows, pairwise_raw, missing_inputs)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence = metrics.get(CONFIDENCE_ONLY_BASELINE, primary)
    gate_fail_count = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    scale_current_repair_ready = False
    status = READY_STATUS if not missing_inputs else BLOCKED_STATUS
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m134_status": m134_coverage.get("status"),
        "m135_status": m135_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "m135_scan_task_policy_rows": m135_coverage.get("scan_task_policy_rows"),
        "m135_trajectory_attempt_rows": m135_coverage.get("trajectory_attempt_rows"),
        "m135_leakage_audit_pass": bool(m135_coverage.get("leakage_audit_pass")),
        "policy_result_rows": len(policy_rows),
        "pairwise_interpretation_rows": len(pairwise_rows),
        "diagnosis_rows": len(diagnosis_rows),
        "gate_rows": len(gate_rows),
        "gate_fail_count": gate_fail_count,
        "method_policy_id": METHOD_POLICY,
        "method_SR": method.get("SR"),
        "method_SPL": method.get("SPL"),
        "detector_confidence_SPL": primary.get("SPL"),
        "confidence_only_SPL": confidence.get("SPL"),
        "delta_SPL_vs_detector_confidence": delta(method.get("SPL"), primary.get("SPL")),
        "delta_SPL_vs_confidence_only": delta(method.get("SPL"), confidence.get("SPL")),
        "path_family_repair_diagnostic_ready": True,
        "scale_current_repair_ready": scale_current_repair_ready,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_interpretation_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_result_interpretation_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "repair_diagnosis_rows.jsonl", diagnosis_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, pairwise_rows, diagnosis_rows, gate_rows, route_rows),
        encoding="utf-8",
    )
    mirror_outputs(
        [
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "policy_result_interpretation_rows.jsonl",
            ARTIFACT_DIR / "pairwise_result_interpretation_rows.jsonl",
            ARTIFACT_DIR / "repair_diagnosis_rows.jsonl",
            ARTIFACT_DIR / "gate_rows.jsonl",
            ARTIFACT_DIR / "claim_boundary_rows.jsonl",
            ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
            ARTIFACT_DIR / "route_decision_rows.jsonl",
            ARTIFACT_DIR / "report.md",
        ]
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
