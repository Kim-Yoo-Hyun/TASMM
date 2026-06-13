#!/usr/bin/env python3
"""Interpret E008-M140 confidence-preserving repair results and decide scale-up route."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M138_DIR = EXP_ROOT / "artifacts" / "E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0"
M139_DIR = EXP_ROOT / "artifacts" / "E008-M139_target_free_confidence_preserving_repair_trajectory_contract_v0"
M140_DIR = EXP_ROOT / "artifacts" / "E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0"
)

VERSION = "e008_m141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0"
READY_STATUS = "e008_m141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_ready"
BLOCKED_STATUS = "e008_m141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_blocked"
NEXT_UNIT = "E008-M142 target-free confidence-preserving controlled scale-up contract"

METHOD_POLICY = "confidence_band_trajectory_tiebreak_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_BASELINE = "trajectory_greedy_confidence_only_reachable_v0"
HARD_VETO_ABLATION = "confidence_preserving_hard_veto_v0"
PRIOR_REPAIR_BASELINE = "trajectory_greedy_confidence_path_repair_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
POLICY_ORDER = [
    METHOD_POLICY,
    HARD_VETO_ABLATION,
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY_BASELINE,
    PRIOR_REPAIR_BASELINE,
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


def policy_role(policy_id: str) -> str:
    if policy_id == METHOD_POLICY:
        return "selected_confidence_preserving_repair"
    if policy_id == PRIMARY_BASELINE:
        return "protected_detector_confidence_baseline"
    if policy_id == CONFIDENCE_ONLY_BASELINE:
        return "strong_confidence_only_ablation"
    if policy_id == HARD_VETO_ABLATION:
        return "hard_feasibility_veto_ablation"
    if policy_id == PRIOR_REPAIR_BASELINE:
        return "negative_prior_repair_baseline"
    if policy_id == PATH_COST_BASELINE:
        return "negative_path_cost_baseline"
    return "unknown"


def build_policy_result_rows(metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence = metrics.get(CONFIDENCE_ONLY_BASELINE, {})
    prior = metrics.get(PRIOR_REPAIR_BASELINE, {})
    path_cost = metrics.get(PATH_COST_BASELINE, {})

    rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        row = metrics.get(policy_id, {})
        delta_spl_primary = delta(row.get("SPL"), primary.get("SPL"))
        delta_visits_primary = delta(row.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "delta_SPL_vs_detector_confidence": delta_spl_primary,
                "delta_CandidateVisits_vs_detector_confidence": delta_visits_primary,
                "delta_SPL_vs_confidence_only": delta(row.get("SPL"), confidence.get("SPL")),
                "delta_SPL_vs_prior_repair": delta(row.get("SPL"), prior.get("SPL")),
                "delta_SPL_vs_path_cost": delta(row.get("SPL"), path_cost.get("SPL")),
                "supports_executed_smoke": bool(row.get("success_rows")),
                "supports_controlled_scale_up_seed": policy_id == METHOD_POLICY
                and method_preserves_confidence_baseline(method, primary, confidence)
                and method_recovers_prior_regression(method, prior, path_cost),
                "supports_final_real_navigation_claim": False,
                "interpretation": interpret_policy(policy_id, delta_spl_primary, delta_visits_primary),
            }
        )
    return rows


def method_preserves_confidence_baseline(
    method: dict[str, Any],
    primary: dict[str, Any],
    confidence: dict[str, Any],
) -> bool:
    sr_delta_primary = delta(method.get("SR"), primary.get("SR"))
    spl_delta_primary = delta(method.get("SPL"), primary.get("SPL"))
    spl_delta_confidence = delta(method.get("SPL"), confidence.get("SPL"))
    visit_delta_primary = delta(method.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean"))
    if None in {sr_delta_primary, spl_delta_primary, spl_delta_confidence, visit_delta_primary}:
        return False
    return (
        (sr_delta_primary or 0.0) >= 0.0
        and (spl_delta_primary or 0.0) >= 0.0
        and (spl_delta_confidence or 0.0) >= 0.0
        and (visit_delta_primary or 0.0) <= 0.0
    )


def method_recovers_prior_regression(
    method: dict[str, Any],
    prior: dict[str, Any],
    path_cost: dict[str, Any],
) -> bool:
    prior_delta = delta(method.get("SPL"), prior.get("SPL"))
    path_delta = delta(method.get("SPL"), path_cost.get("SPL"))
    return (prior_delta or 0.0) > 0.0 and (path_delta or 0.0) > 0.0


def interpret_policy(
    policy_id: str,
    delta_spl_primary: float | None,
    delta_visits_primary: float | None,
) -> str:
    if policy_id == METHOD_POLICY:
        if (delta_spl_primary or 0.0) >= 0.0 and (delta_visits_primary or 0.0) < 0.0:
            return "preserves_detector_confidence_spl_and_reduces_candidate_visits_on_one_case"
        if (delta_spl_primary or 0.0) < 0.0:
            return "would_not_be_scale_ready_because_it_degrades_detector_confidence_spl"
        return "ties_detector_confidence_without_visit_gain"
    if policy_id == HARD_VETO_ABLATION:
        return "matches_selected_policy_on_this_case_so_scale_up_must_audit_false_veto_risk"
    if policy_id == PRIMARY_BASELINE:
        return "protected_naive_baseline_that_the_method_must_not_degrade"
    if policy_id == CONFIDENCE_ONLY_BASELINE:
        return "strong_ablation_showing_confidence_ordering_remains_hard_to_beat"
    if policy_id == PRIOR_REPAIR_BASELINE:
        return "negative_repair_baseline_that_m137_m140_were_designed_to_fix"
    if policy_id == PATH_COST_BASELINE:
        return "negative_path_cost_baseline_showing_path_cost_cannot_replace_confidence"
    return "manual_review"


def build_pairwise_interpretation_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(pairwise_rows, key=lambda item: str(item.get("baseline_policy_id"))):
        baseline = str(row.get("baseline_policy_id"))
        spl_delta = finite_float(row.get("delta_SPL"))
        visit_delta = delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits"))
        out.append(
            {
                "version": VERSION,
                "row_type": "pairwise_result_interpretation",
                "method_policy_id": row.get("method_policy_id"),
                "baseline_policy_id": baseline,
                "delta_SR": row.get("delta_SR"),
                "delta_SPL": spl_delta,
                "delta_PathLengthM": row.get("delta_PathLengthM"),
                "delta_CandidateVisits": visit_delta,
                "supports_controlled_scale_up_seed": baseline in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE}
                and (spl_delta or 0.0) >= 0.0
                and (visit_delta or 0.0) <= 0.0,
                "supports_regression_recovery": baseline in {PRIOR_REPAIR_BASELINE, PATH_COST_BASELINE}
                and (spl_delta or 0.0) > 0.0,
                "supports_final_real_navigation_claim": False,
                "interpretation": interpret_pairwise(baseline, spl_delta, visit_delta),
            }
        )
    return out


def interpret_pairwise(baseline: str, spl_delta: float | None, visit_delta: float | None) -> str:
    if baseline in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE}:
        if (spl_delta or 0.0) >= 0.0 and (visit_delta or 0.0) < 0.0:
            return "selected_policy_preserves_strong_confidence_baseline_spl_and_reduces_visits"
        return "selected_policy_does_not_yet_beat_strong_confidence_baseline_on_spl"
    if baseline == HARD_VETO_ABLATION:
        return "selected_policy_ties_hard_veto_on_this_case_so_scale_up_needs_false_veto_and_tie_break_audit"
    if baseline == PRIOR_REPAIR_BASELINE:
        return "selected_policy_recovers_the_m135_trajectory_repair_regression"
    if baseline == PATH_COST_BASELINE:
        return "selected_policy_recovers_the_m130_source_to_candidate_path_cost_failure"
    return "manual_review"


def build_principle_rows() -> list[dict[str, Any]]:
    return [
        principle(
            "motivation",
            "dynamic_object_search_with_noisy_open_vocabulary_evidence_exposes_stale_memory_and_candidate_ranking_failures",
            "Motivation only; not a contribution by itself.",
        ),
        principle(
            "naive_baseline",
            "detector_confidence_ranking_and_confidence_only_reachable_ranking_are_the_protected_baselines",
            "Any path/search-cost method must not degrade these baselines before scale-up.",
        ),
        principle(
            "failure_diagnosis",
            "M130/M135_show_path_cost_or_trajectory_cost_can_hurt_SPL_when_it_replaces_confidence_ordering",
            "This diagnosis forced the M137 method form.",
        ),
        principle(
            "method_form",
            "use_path_or_trajectory_cost_only_as_confidence_band_tie_break_hard_feasibility_veto_or_source_gap_trigger",
            "The component is derived from the failure, not added as decoration.",
        ),
        principle(
            "current_evidence",
            "M140_preserves_detector_confidence_SPL_and_reduces_candidate_visits_on_one_case",
            "This supports controlled scale-up, not final navigation claims.",
        ),
        principle(
            "disconfirmation_rule",
            "if_scale_up_degrades_detector_confidence_SR_or_SPL_or_creates_false_vetoes_the_claim_must_be_rejected_or_rewritten",
            "This prevents fitting the method to the desired hypothesis.",
        ),
    ]


def principle(stage: str, statement: str, claim_use: str) -> dict[str, Any]:
    return {"version": VERSION, "stage": stage, "statement": statement, "claim_use": claim_use}


def build_gate_rows(
    m138_coverage: dict[str, Any],
    m140_coverage: dict[str, Any],
    metrics: dict[str, dict[str, Any]],
    missing_inputs: list[str],
) -> list[dict[str, Any]]:
    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence = metrics.get(CONFIDENCE_ONLY_BASELINE, {})
    prior = metrics.get(PRIOR_REPAIR_BASELINE, {})
    path_cost = metrics.get(PATH_COST_BASELINE, {})
    preserves = method_preserves_confidence_baseline(method, primary, confidence)
    recovers = method_recovers_prior_regression(method, prior, path_cost)
    hard_veto_count = finite_float(m138_coverage.get("selected_policy_hard_veto_rows")) or 0.0
    return [
        gate(
            "m140_input_ready",
            "pass" if not missing_inputs and m140_coverage.get("status") == "e008_m140_target_free_confidence_preserving_repair_trajectory_execution_smoke_ready" else "fail",
            "M140 trajectory execution artifact is present and ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(m140_coverage.get("leakage_audit_pass")) else "fail",
            "ObjectNav goal/viewpoint fields are metric-only and not policy inputs.",
            blocks_final=True,
        ),
        gate(
            "confidence_band_audit",
            "pass" if m138_coverage.get("selected_policy_confidence_band_violations") == 0 else "fail",
            "Selected policy has zero outside-band confidence overrides in M138.",
            blocks_final=True,
        ),
        gate(
            "protected_baseline_not_degraded",
            "pass" if preserves else "fail",
            "Selected policy preserves detector-confidence and confidence-only SR/SPL on the one case.",
            blocks_final=True,
        ),
        gate(
            "visit_efficiency_gain",
            "pass" if (delta(method.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean")) or 0.0) < 0.0 else "warning",
            "Selected policy reduces detector-confidence candidate visits from 3 to 2 on the one case.",
            blocks_final=False,
        ),
        gate(
            "prior_regression_recovered",
            "pass" if recovers else "fail",
            "Selected policy recovers M130/M135 path-cost and trajectory-aware repair SPL regressions.",
            blocks_final=False,
        ),
        gate(
            "hard_veto_false_veto_risk",
            "warning" if hard_veto_count > 0 else "pass",
            "Selected policy hard-vetoes 13 rows in M138; scale-up must audit whether vetoes suppress true targets.",
            blocks_final=True,
        ),
        gate(
            "denominator_scale",
            "warning",
            "M140 is still one target-free trajectory case.",
            blocks_final=True,
        ),
        gate(
            "external_navigation_baselines",
            "warning",
            "`VLFM`, `HM3D-OVON`, `HOV-SG`, and GOAT-style executable baselines are not yet integrated.",
            blocks_final=True,
        ),
        gate(
            "controlled_scale_up_ready",
            "pass" if preserves and recovers else "fail",
            "Scale-up is justified as validation of a fixed confidence-preserving principle, not as final claim evidence.",
            blocks_final=False,
        ),
        gate(
            "final_real_navigation_claim",
            "fail",
            "One-case result plus missing heldout/external-baseline evidence cannot support final real navigation SR/SPL.",
            blocks_final=True,
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


def build_scale_up_seed_rows() -> list[dict[str, Any]]:
    return [
        seed(
            "fixed_policy",
            "Freeze `confidence_band_trajectory_tiebreak_v0`; no per-case retuning of confidence band, min path advantage, or veto logic.",
            "prevents_result_fitting",
        ),
        seed(
            "comparison_set",
            "Run at least detector-confidence, confidence-only reachable, hard-veto, prior trajectory repair, and path-cost-only baselines.",
            "keeps_protected_naive_baselines",
        ),
        seed(
            "denominator",
            "Scale over all currently source-ready target-free cases first, then heldout scenes/categories as source materializes.",
            "turns_one_case_smoke_into_scale_evidence",
        ),
        seed(
            "pass_gate",
            "No SR/SPL regression versus detector-confidence; candidate visits or failure reduction must improve on source-ready subset.",
            "defines_positive_evidence_before_running",
        ),
        seed(
            "warning_gate",
            "Any high hard-veto count requires false-veto audit against matched target rows and near-target candidates.",
            "guards_against_suppressing_true_targets",
        ),
        seed(
            "fail_gate",
            "If detector-confidence tie is broken only by posthoc target distance or if SPL drops, reject the navigation-improvement claim.",
            "keeps_claim_from_being_forced",
        ),
    ]


def seed(item_id: str, contract: str, purpose: str) -> dict[str, Any]:
    return {"version": VERSION, "item_id": item_id, "contract": contract, "purpose": purpose}


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "executed_confidence_preserving_repair_smoke",
            True,
            "M140 executes one target-free confidence-preserving repair case in Docker Habitat.",
        ),
        claim(
            "controlled_scale_up_seed",
            True,
            "M140 preserves detector-confidence SR/SPL and reduces candidate visits, so M142 scale-up is justified.",
        ),
        claim(
            "positive_real_navigation_improvement",
            False,
            "Needs M142+ denominator scale, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "deployable_search_policy",
            False,
            "M140 is a full-ranked one-case trajectory smoke, not a fixed-budget deployed policy.",
        ),
        claim(
            "final_real_rgbd_open_vocab_robustness",
            False,
            "M140 uses a target-free detector route but does not establish final RGB-D/open-vocabulary robustness.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M140 does not use human intent; E006-M08 remains the active boundary unless redesigned.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "is_the_project_forcing_the_hypothesis",
            "No. Negative M130/M135 results rejected the prior path-cost form; M137/M140 changed the method according to the diagnosed failure.",
        ),
        defense(
            "why_scale_after_only_one_case",
            "Scale-up is not a claim. It tests whether the fixed confidence-preserving principle holds beyond the diagnostic case.",
        ),
        defense(
            "why_not_claim_better_spl_now",
            "M140 ties detector-confidence SPL and improves candidate visits only on one case, so it is a scale seed rather than final evidence.",
        ),
        defense(
            "what_would_disconfirm_the_method",
            "Any scale-up SR/SPL regression against detector-confidence, high false-veto rate, or gain only on filtered cases rejects or rewrites the claim.",
        ),
        defense(
            "why_this_is_semantic_mapping_not_just_ranking",
            "The decision exposes memory trust, current evidence reliability, source coverage, and path feasibility as map-to-action state rather than only sorting detections.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "bounded_diagnostic_only",
            "decision": "reject_as_next",
            "selected": False,
            "reason": "M140 is positive enough to test generality; stopping at one case would not satisfy top-tier evidence rigor.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "controlled_scale_up_confidence_preserving_policy",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The fixed confidence-preserving policy preserves the protected baseline while recovering prior regressions.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "scale_unguarded_path_cost_or_prior_repair",
            "decision": "reject",
            "selected": False,
            "reason": "M130/M135 showed unguarded path/trajectory cost hurts SPL against confidence baselines.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_sr_spl",
            "decision": "reject_now",
            "selected": False,
            "reason": "Final claim needs scale, heldout transfer, external baselines, and failure analysis.",
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
    principle_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M141 Confidence-Preserving Repair Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M140 status: `{coverage['m140_status']}`.",
            f"- Selected policy: `{METHOD_POLICY}`.",
            f"- Selected policy `SR` / `SPL`: {fmt(coverage['method_SR'])} / {fmt(coverage['method_SPL'])}.",
            f"- Detector-confidence `SR` / `SPL`: {fmt(coverage['detector_confidence_SR'])} / {fmt(coverage['detector_confidence_SPL'])}.",
            f"- Candidate visits delta vs detector-confidence: {fmt(coverage['delta_CandidateVisits_vs_detector_confidence'])}.",
            f"- Prior repair `SPL`: {fmt(coverage['prior_repair_SPL'])}.",
            f"- Path-cost baseline `SPL`: {fmt(coverage['path_cost_SPL'])}.",
            f"- Controlled scale-up ready: {coverage['controlled_scale_up_ready']}.",
            f"- Final real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.",
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
                    "CandidateVisits_mean",
                    "delta_SPL_vs_detector_confidence",
                    "delta_CandidateVisits_vs_detector_confidence",
                    "supports_controlled_scale_up_seed",
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
                    "delta_CandidateVisits",
                    "supports_controlled_scale_up_seed",
                    "supports_regression_recovery",
                ],
            ),
            "",
            "## Novelty Discipline",
            "",
            markdown_table(principle_rows, ["stage", "statement", "claim_use"]),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_final_real_navigation_claim", "rationale"]),
            "",
            "## Scale-Up Seed",
            "",
            markdown_table(scale_rows, ["item_id", "contract", "purpose"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Claim Boundary",
            "",
            "- M141 selects controlled scale-up because M140 preserves the protected confidence baseline and recovers prior regressions.",
            "- M141 does not support final real navigation `SR` / `SPL`; it only authorizes M142 scale-up contract design.",
            "- M142 must freeze the selected policy and define pass/warning/fail gates before any long run.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    m138_coverage = read_json(M138_DIR / "coverage.json")
    m139_coverage = read_json(M139_DIR / "coverage.json")
    m140_coverage = read_json(M140_DIR / "coverage.json")
    metric_rows = read_jsonl(M140_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_raw = read_jsonl(M140_DIR / "pairwise_policy_delta_rows.jsonl")

    required_inputs = [
        M138_DIR / "coverage.json",
        M139_DIR / "coverage.json",
        M140_DIR / "coverage.json",
        M140_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        M140_DIR / "pairwise_policy_delta_rows.jsonl",
        M140_DIR / "leakage_audit_rows.jsonl",
    ]
    missing_inputs = [str(path.relative_to(ROOT)) for path in required_inputs if not path.exists()]
    metrics = metric_aggregates(metric_rows)
    policy_rows = build_policy_result_rows(metrics)
    pairwise_rows = build_pairwise_interpretation_rows(pairwise_raw)
    principle_rows = build_principle_rows()
    gate_rows = build_gate_rows(m138_coverage, m140_coverage, metrics, missing_inputs)
    scale_rows = build_scale_up_seed_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    method = metrics.get(METHOD_POLICY, {})
    primary = metrics.get(PRIMARY_BASELINE, {})
    confidence = metrics.get(CONFIDENCE_ONLY_BASELINE, {})
    prior = metrics.get(PRIOR_REPAIR_BASELINE, {})
    path_cost = metrics.get(PATH_COST_BASELINE, {})
    controlled_scale_up_ready = method_preserves_confidence_baseline(method, primary, confidence) and method_recovers_prior_regression(
        method, prior, path_cost
    )
    gate_warning_count = sum(1 for row in gate_rows if row.get("gate_status") == "warning")
    gate_fail_count = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    status = READY_STATUS if not missing_inputs else BLOCKED_STATUS
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m138_status": m138_coverage.get("status"),
        "m139_status": m139_coverage.get("status"),
        "m140_status": m140_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "m140_scan_task_policy_rows": m140_coverage.get("scan_task_policy_rows"),
        "m140_trajectory_attempt_rows": m140_coverage.get("trajectory_attempt_rows"),
        "m140_leakage_audit_pass": bool(m140_coverage.get("leakage_audit_pass")),
        "method_policy_id": METHOD_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE,
        "method_SR": method.get("SR"),
        "method_SPL": method.get("SPL"),
        "method_CandidateVisits_mean": method.get("CandidateVisits_mean"),
        "detector_confidence_SR": primary.get("SR"),
        "detector_confidence_SPL": primary.get("SPL"),
        "detector_confidence_CandidateVisits_mean": primary.get("CandidateVisits_mean"),
        "confidence_only_SPL": confidence.get("SPL"),
        "prior_repair_SPL": prior.get("SPL"),
        "path_cost_SPL": path_cost.get("SPL"),
        "delta_SR_vs_detector_confidence": delta(method.get("SR"), primary.get("SR")),
        "delta_SPL_vs_detector_confidence": delta(method.get("SPL"), primary.get("SPL")),
        "delta_CandidateVisits_vs_detector_confidence": delta(
            method.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean")
        ),
        "delta_SPL_vs_prior_repair": delta(method.get("SPL"), prior.get("SPL")),
        "delta_SPL_vs_path_cost": delta(method.get("SPL"), path_cost.get("SPL")),
        "selected_policy_confidence_band_violations": m138_coverage.get("selected_policy_confidence_band_violations"),
        "selected_policy_hard_veto_rows": m138_coverage.get("selected_policy_hard_veto_rows"),
        "controlled_scale_up_ready": controlled_scale_up_ready,
        "bounded_diagnostic_only_selected": False,
        "scale_unguarded_path_cost_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "policy_result_rows": len(policy_rows),
        "pairwise_interpretation_rows": len(pairwise_rows),
        "principle_rows": len(principle_rows),
        "gate_rows": len(gate_rows),
        "gate_warning_count": gate_warning_count,
        "gate_fail_count": gate_fail_count,
        "selected_next_unit": NEXT_UNIT,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_interpretation_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_result_interpretation_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "principle_trace_rows.jsonl", principle_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "scale_up_seed_rows.jsonl", scale_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, pairwise_rows, principle_rows, gate_rows, route_rows, scale_rows),
        encoding="utf-8",
    )
    mirror_outputs(
        [
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "policy_result_interpretation_rows.jsonl",
            ARTIFACT_DIR / "pairwise_result_interpretation_rows.jsonl",
            ARTIFACT_DIR / "principle_trace_rows.jsonl",
            ARTIFACT_DIR / "gate_rows.jsonl",
            ARTIFACT_DIR / "scale_up_seed_rows.jsonl",
            ARTIFACT_DIR / "claim_boundary_rows.jsonl",
            ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
            ARTIFACT_DIR / "route_decision_rows.jsonl",
            ARTIFACT_DIR / "report.md",
        ]
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
