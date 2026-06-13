#!/usr/bin/env python3
"""Decompose E008-M145/M146 policy-family failures and freeze the next redesign contract."""

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
M145_DIR = EXP_ROOT / "artifacts" / "E008-M145_full_val_mini_confidence_preserving_trajectory_execution_v0"
M146_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M146_full_val_mini_confidence_preserving_trajectory_result_interpretation_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M147_full_val_mini_policy_family_failure_decomposition_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M147_full_val_mini_policy_family_failure_decomposition_v0"
)

VERSION = "e008_m147_full_val_mini_policy_family_failure_decomposition_v0"
READY_STATUS = "e008_m147_full_val_mini_policy_family_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m147_full_val_mini_policy_family_failure_decomposition_blocked"
NEXT_UNIT = "E008-M148 full-val-mini budget-guarded confidence/path redesign contract"

METHOD_POLICY = "confidence_band_trajectory_tiebreak_v0"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_POLICY = "trajectory_greedy_confidence_only_reachable_v0"
HARD_VETO_POLICY = "confidence_preserving_hard_veto_v0"
PRIOR_REPAIR_POLICY = "trajectory_greedy_confidence_path_repair_v0"
PATH_COST_POLICY = "path_cost_ascending_reachable_subset_v0"


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


def metric_rows_by_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id")): row
        for row in rows
        if row.get("row_type") == "policy_result_interpretation"
    }


def scan_rows_by_uid(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("benchmark_row_uid")), str(row.get("policy_id"))): row
        for row in rows
        if row.get("metric_scope") == "scan_task_policy"
    }


def classify_method_vs_detector(method: dict[str, Any], detector: dict[str, Any]) -> str:
    spl_delta = delta(method.get("SPL"), detector.get("SPL"))
    visit_delta = delta(method.get("CandidateVisits"), detector.get("CandidateVisits"))
    sr_delta = delta(method.get("SR"), detector.get("SR"))
    eps = 1e-9
    if sr_delta is not None and sr_delta < -eps:
        return "sr_regression"
    if spl_delta is not None and spl_delta < -eps and visit_delta is not None and visit_delta > eps:
        return "spl_loss_and_more_visits"
    if spl_delta is not None and spl_delta < -eps:
        return "spl_loss_without_more_visits"
    if spl_delta is not None and spl_delta > eps and visit_delta is not None and visit_delta <= eps:
        return "clean_spl_gain"
    if spl_delta is not None and spl_delta > eps and visit_delta is not None and visit_delta > eps:
        return "spl_gain_with_visit_cost"
    if abs(spl_delta or 0.0) <= eps and visit_delta is not None and visit_delta > eps:
        return "visit_regression_only"
    if abs(spl_delta or 0.0) <= eps and visit_delta is not None and visit_delta < -eps:
        return "visit_reduction_without_spl_change"
    return "neutral_or_tie"


def build_case_delta_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = scan_rows_by_uid(scan_rows)
    uids = sorted({uid for uid, _policy_id in indexed})
    out: list[dict[str, Any]] = []
    for uid in uids:
        method = indexed.get((uid, METHOD_POLICY))
        detector = indexed.get((uid, DETECTOR_POLICY))
        prior = indexed.get((uid, PRIOR_REPAIR_POLICY))
        path_cost = indexed.get((uid, PATH_COST_POLICY))
        if not method or not detector:
            continue
        row = {
            "version": VERSION,
            "row_type": "case_delta",
            "benchmark_row_uid": uid,
            "scan_id": method.get("scan_id"),
            "scene_key": method.get("scene_key"),
            "adapter_episode_id": method.get("adapter_episode_id"),
            "object_category": method.get("object_category"),
            "task_context_id": method.get("task_context_id"),
            "profile_vs_detector": classify_method_vs_detector(method, detector),
            "method_SR": method.get("SR"),
            "detector_SR": detector.get("SR"),
            "method_SPL": method.get("SPL"),
            "detector_SPL": detector.get("SPL"),
            "delta_SPL_vs_detector": delta(method.get("SPL"), detector.get("SPL")),
            "method_CandidateVisits": method.get("CandidateVisits"),
            "detector_CandidateVisits": detector.get("CandidateVisits"),
            "delta_CandidateVisits_vs_detector": delta(
                method.get("CandidateVisits"), detector.get("CandidateVisits")
            ),
            "method_PathLengthM": method.get("PathLengthM"),
            "detector_PathLengthM": detector.get("PathLengthM"),
            "delta_PathLengthM_vs_detector": delta(method.get("PathLengthM"), detector.get("PathLengthM")),
            "method_success_source_role": method.get("success_source_role"),
            "detector_success_source_role": detector.get("success_source_role"),
            "method_success_candidate_to_nearest_eval_viewpoint_xz_m": method.get(
                "success_candidate_to_nearest_eval_viewpoint_xz_m"
            ),
            "detector_success_candidate_to_nearest_eval_viewpoint_xz_m": detector.get(
                "success_candidate_to_nearest_eval_viewpoint_xz_m"
            ),
        }
        if prior:
            row.update(
                {
                    "prior_repair_SPL": prior.get("SPL"),
                    "prior_repair_CandidateVisits": prior.get("CandidateVisits"),
                    "delta_SPL_vs_prior_repair": delta(method.get("SPL"), prior.get("SPL")),
                    "delta_CandidateVisits_vs_prior_repair": delta(
                        method.get("CandidateVisits"), prior.get("CandidateVisits")
                    ),
                }
            )
        if path_cost:
            row.update(
                {
                    "path_cost_SPL": path_cost.get("SPL"),
                    "path_cost_CandidateVisits": path_cost.get("CandidateVisits"),
                    "delta_SPL_vs_path_cost": delta(method.get("SPL"), path_cost.get("SPL")),
                    "delta_CandidateVisits_vs_path_cost": delta(
                        method.get("CandidateVisits"), path_cost.get("CandidateVisits")
                    ),
                }
            )
        out.append(row)
    return out


def summarize_group(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key) or "unknown")].append(row)
    out: list[dict[str, Any]] = []
    for group_id, group_rows in sorted(grouped.items()):
        spl_delta = [finite_float(row.get("delta_SPL_vs_detector")) for row in group_rows]
        visit_delta = [finite_float(row.get("delta_CandidateVisits_vs_detector")) for row in group_rows]
        out.append(
            {
                "version": VERSION,
                "row_type": f"{group_key}_profile_decomposition",
                group_key: group_id,
                "rows": len(group_rows),
                "mean_delta_SPL_vs_detector": mean(spl_delta),
                "mean_delta_CandidateVisits_vs_detector": mean(visit_delta),
                "clean_spl_gain_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "clean_spl_gain"
                ),
                "spl_gain_with_visit_cost_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "spl_gain_with_visit_cost"
                ),
                "spl_loss_and_more_visits_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "spl_loss_and_more_visits"
                ),
                "spl_loss_without_more_visits_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "spl_loss_without_more_visits"
                ),
                "visit_regression_only_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "visit_regression_only"
                ),
                "neutral_or_tie_rows": sum(
                    1 for row in group_rows if row.get("profile_vs_detector") == "neutral_or_tie"
                ),
            }
        )
    return out


def build_policy_family_rows(policy_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    def policy_metric(policy_id: str, field: str) -> Any:
        return policy_rows.get(policy_id, {}).get(field)

    families = [
        {
            "policy_family_id": "confidence_only_protected_family",
            "member_policy_ids": [DETECTOR_POLICY, CONFIDENCE_ONLY_POLICY, HARD_VETO_POLICY],
            "representative_policy_id": DETECTOR_POLICY,
            "family_status": "protected_baseline_family",
            "failure_or_strength": "confidence_ordering_remains_hard_to_beat_on_full_val_mini",
            "method_implication": "Any redesign must beat or preserve this family before claiming navigation improvement.",
        },
        {
            "policy_family_id": "confidence_band_tiebreak_family",
            "member_policy_ids": [METHOD_POLICY],
            "representative_policy_id": METHOD_POLICY,
            "family_status": "rejected_as_positive_method",
            "failure_or_strength": "band-level path tiebreak perturbs ordering without improving aggregate SPL or visits",
            "method_implication": "A confidence band alone is too weak; it needs a stricter trigger and visit-budget guard.",
        },
        {
            "policy_family_id": "trajectory_path_repair_family",
            "member_policy_ids": [PRIOR_REPAIR_POLICY],
            "representative_policy_id": PRIOR_REPAIR_POLICY,
            "family_status": "diagnostic_candidate_not_claimable_posthoc",
            "failure_or_strength": "best observed SPL but higher candidate visits than detector-confidence",
            "method_implication": "Potential next method only if precommitted with budget guard and case-level trigger.",
        },
        {
            "policy_family_id": "path_cost_first_family",
            "member_policy_ids": [PATH_COST_POLICY],
            "representative_policy_id": PATH_COST_POLICY,
            "family_status": "negative_baseline",
            "failure_or_strength": "path cost as primary ordering destroys SPL and visit efficiency",
            "method_implication": "Path/search cost cannot replace detector confidence; it can only gate or repair selected cases.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for family in families:
        policy_id = str(family["representative_policy_id"])
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_family_decomposition",
                **family,
                "representative_SR": policy_metric(policy_id, "SR"),
                "representative_SPL": policy_metric(policy_id, "SPL"),
                "representative_CandidateVisits_mean": policy_metric(policy_id, "CandidateVisits_mean"),
                "representative_delta_SPL_vs_detector": policy_metric(
                    policy_id, "delta_SPL_vs_detector_confidence"
                ),
                "representative_delta_CandidateVisits_vs_detector": policy_metric(
                    policy_id, "delta_CandidateVisits_mean_vs_detector_confidence"
                ),
            }
        )
    return rows


def build_failure_diagnosis_rows(case_rows: list[dict[str, Any]], policy_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    profile_counts = defaultdict(int)
    for row in case_rows:
        profile_counts[str(row.get("profile_vs_detector"))] += 1

    method = policy_rows.get(METHOD_POLICY, {})
    prior = policy_rows.get(PRIOR_REPAIR_POLICY, {})
    path = policy_rows.get(PATH_COST_POLICY, {})
    return [
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "protected_confidence_baseline_not_beaten",
            "evidence": (
                f"selected delta SPL {fmt(method.get('delta_SPL_vs_detector_confidence'))}, "
                f"delta visits {fmt(method.get('delta_CandidateVisits_mean_vs_detector_confidence'))}"
            ),
            "principle": "Do not claim navigation improvement unless the method beats the simplest confidence-ranking baseline.",
            "redesign_requirement": "Keep detector-confidence as protected ordering outside explicitly justified repair cases.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "confidence_band_not_selective_enough",
            "evidence": (
                f"profiles clean_gain {profile_counts['clean_spl_gain']}, "
                f"gain_with_visit_cost {profile_counts['spl_gain_with_visit_cost']}, "
                f"loss_more_visits {profile_counts['spl_loss_and_more_visits']}, "
                f"visit_regression_only {profile_counts['visit_regression_only']}"
            ),
            "principle": "A band tiebreak helps only in a subset; it must not globally perturb visit order.",
            "redesign_requirement": "Add case-level trigger and visit-budget guard before path repair is allowed.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "path_cost_first_is_negative_baseline",
            "evidence": (
                f"path-cost SPL {fmt(path.get('SPL'))}, "
                f"delta SPL {fmt(path.get('delta_SPL_vs_detector_confidence'))}, "
                f"delta visits {fmt(path.get('delta_CandidateVisits_mean_vs_detector_confidence'))}"
            ),
            "principle": "Search/path cost cannot replace visual-semantic confidence.",
            "redesign_requirement": "Use path cost as hard infeasibility veto, local tie-break, or source-gap trigger only.",
        },
        {
            "version": VERSION,
            "row_type": "failure_diagnosis",
            "diagnosis_id": "prior_path_repair_is_promising_but_not_free",
            "evidence": (
                f"prior repair SPL {fmt(prior.get('SPL'))}, "
                f"delta SPL {fmt(prior.get('delta_SPL_vs_detector_confidence'))}, "
                f"delta visits {fmt(prior.get('delta_CandidateVisits_mean_vs_detector_confidence'))}"
            ),
            "principle": "The best observed SPL row is not automatically a contribution if it increases visit cost and was not precommitted.",
            "redesign_requirement": "Precommit a budget-guarded repair policy and rerun before any positive claim.",
        },
    ]


def build_redesign_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "redesign_contract",
            "contract_id": "protected_confidence_floor",
            "required": True,
            "allowed_inputs": "candidate confidence, source role, reachability/path cost, source-gap flag, task context already available before evaluation",
            "blocked_inputs": "ObjectNav eval goal/viewpoint, success candidate, nearest eval viewpoint distance, posthoc per-episode winner",
            "rule": "Default order remains detector-confidence / confidence-only unless a precommitted repair trigger fires.",
        },
        {
            "version": VERSION,
            "row_type": "redesign_contract",
            "contract_id": "visit_budget_guard",
            "required": True,
            "allowed_inputs": "candidate rank, planned candidate visit count, path-ready count, budget cap",
            "blocked_inputs": "final success rank or eval-goal distance",
            "rule": "A path repair cannot increase planned candidate visits beyond the protected baseline unless it is a declared source-gap recovery branch.",
        },
        {
            "version": VERSION,
            "row_type": "redesign_contract",
            "contract_id": "case_level_repair_trigger",
            "required": True,
            "allowed_inputs": "confidence tie band, hard reachability failure, source-gap/source-coverage diagnostic, stale/current source role",
            "blocked_inputs": "episode-level oracle success/failure labels",
            "rule": "Path cost can reorder only when confidence evidence is ambiguous or the confidence candidate is unreachable/source-gap limited.",
        },
        {
            "version": VERSION,
            "row_type": "redesign_contract",
            "contract_id": "precommit_before_execution",
            "required": True,
            "allowed_inputs": "M145/M146 aggregate diagnostics and allowed-input schema",
            "blocked_inputs": "choosing the M145 best policy after seeing per-episode eval outcomes",
            "rule": "M148 must freeze the policy family before any rerun or further scale-up.",
        },
    ]


def build_gate_rows(m145_cov: dict[str, Any], m146_cov: dict[str, Any], case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": "m145_execution_ready",
            "gate_status": "pass" if m145_cov.get("status") == "e008_m145_full_val_mini_confidence_preserving_trajectory_execution_ready" else "fail",
            "blocks_next": m145_cov.get("status") != "e008_m145_full_val_mini_confidence_preserving_trajectory_execution_ready",
            "rationale": "M147 needs full-val-mini trajectory metrics.",
        },
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": "m146_interpretation_ready",
            "gate_status": "pass" if m146_cov.get("status") == "e008_m146_full_val_mini_confidence_preserving_trajectory_result_interpretation_ready" else "fail",
            "blocks_next": m146_cov.get("status") != "e008_m146_full_val_mini_confidence_preserving_trajectory_result_interpretation_ready",
            "rationale": "M147 uses M146's protected-baseline decision as its premise.",
        },
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": "case_delta_decomposition_ready",
            "gate_status": "pass" if len(case_rows) == 30 else "warning",
            "blocks_next": len(case_rows) == 0,
            "rationale": f"Expected 30 full-val-mini episode deltas; found {len(case_rows)}.",
        },
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": "positive_navigation_claim",
            "gate_status": "fail",
            "blocks_next": False,
            "rationale": "M146 shows selected policy loses SPL and visit efficiency to detector-confidence.",
        },
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": "redesign_contract_ready",
            "gate_status": "pass",
            "blocks_next": False,
            "rationale": "M147 freezes the requirements for a budget-guarded confidence/path redesign before execution.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "claim_current_confidence_band_policy",
            "decision": "reject",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Current selected policy fails protected detector-confidence SPL and visit-efficiency gates.",
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "promote_prior_repair_policy_directly",
            "decision": "reject_posthoc",
            "selected": False,
            "selected_next_unit": None,
            "reason": "Prior repair has best SPL but was not the selected precommitted policy and increases visits.",
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "freeze_budget_guarded_confidence_path_redesign",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The next defensible method form must preserve confidence ranking, limit visit cost, and trigger path repair only in diagnosed cases.",
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "external_navigation_baseline_now",
            "decision": "defer",
            "selected": False,
            "selected_next_unit": None,
            "reason": "External navigation/search baselines remain required, but the internal method form is not stable enough for a fair main comparison.",
        },
    ]


def render_report(
    coverage: dict[str, Any],
    family_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E008-M147 Policy-Family Failure Decomposition",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Case delta rows: {coverage['case_delta_rows']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
        f"- Redesign contract ready: {coverage['redesign_contract_ready']}.",
        "",
        "## Policy Families",
        "",
        "| family | status | representative | SR | SPL | visits | implication |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in family_rows:
        lines.append(
            "| {family} | {status} | {policy} | {sr} | {spl} | {visits} | {implication} |".format(
                family=row["policy_family_id"],
                status=row["family_status"],
                policy=row["representative_policy_id"],
                sr=fmt(row.get("representative_SR")),
                spl=fmt(row.get("representative_SPL")),
                visits=fmt(row.get("representative_CandidateVisits_mean")),
                implication=row["method_implication"],
            )
        )

    lines.extend(
        [
            "",
            "## Case Profiles",
            "",
            "| profile | rows | mean_delta_SPL | mean_delta_visits | clean_gain | gain_with_visit_cost | loss_more_visits | visit_regression_only |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in [r for r in profile_rows if r.get("row_type") == "profile_vs_detector_profile_decomposition"]:
        lines.append(
            "| {profile} | {rows} | {spl} | {visits} | {clean} | {gain_cost} | {loss_more} | {visit_reg} |".format(
                profile=row["profile_vs_detector"],
                rows=row["rows"],
                spl=fmt(row.get("mean_delta_SPL_vs_detector")),
                visits=fmt(row.get("mean_delta_CandidateVisits_vs_detector")),
                clean=row["clean_spl_gain_rows"],
                gain_cost=row["spl_gain_with_visit_cost_rows"],
                loss_more=row["spl_loss_and_more_visits_rows"],
                visit_reg=row["visit_regression_only_rows"],
            )
        )

    lines.extend(["", "## Failure Diagnoses", ""])
    for row in failure_rows:
        lines.append(f"- `{row['diagnosis_id']}`: {row['principle']} Evidence: {row['evidence']}")

    lines.extend(
        [
            "",
            "## Redesign Contract",
            "",
            "| contract_id | required | rule |",
            "| --- | --- | --- |",
        ]
    )
    for row in contract_rows:
        lines.append(f"| {row['contract_id']} | {row['required']} | {row['rule']} |")

    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| route_id | decision | selected | selected_next_unit | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in route_rows:
        lines.append(
            f"| {row['route_id']} | {row['decision']} | {row['selected']} | {row.get('selected_next_unit')} | {row['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M147 does not claim real navigation improvement.",
            "- M147 explains why the current selected policy is not paper-facing as a positive method.",
            "- M148 must freeze a budget-guarded confidence/path policy before any new execution.",
            "- External navigation/search baselines remain required after the internal policy form is stable.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    m145_cov = read_json(M145_DIR / "coverage.json")
    m146_cov = read_json(M146_DIR / "coverage.json")
    policy_rows_raw = read_jsonl(M146_DIR / "policy_result_interpretation_rows.jsonl")
    scan_rows = read_jsonl(M145_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")

    missing_inputs = [
        str(path)
        for path in [
            M145_DIR / "coverage.json",
            M145_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
            M146_DIR / "coverage.json",
            M146_DIR / "policy_result_interpretation_rows.jsonl",
        ]
        if not path.exists()
    ]

    if missing_inputs:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        coverage = {
            "version": VERSION,
            "status": BLOCKED_STATUS,
            "generated_at": generated_at,
            "missing_inputs": missing_inputs,
            "selected_next_unit": None,
        }
        write_json(ARTIFACT_DIR / "coverage.json", coverage)
        return 1

    policy_rows = metric_rows_by_policy(policy_rows_raw)
    case_rows = build_case_delta_rows(scan_rows)
    profile_rows = (
        summarize_group(case_rows, "profile_vs_detector")
        + summarize_group(case_rows, "object_category")
        + summarize_group(case_rows, "scene_key")
    )
    family_rows = build_policy_family_rows(policy_rows)
    failure_rows = build_failure_diagnosis_rows(case_rows, policy_rows)
    contract_rows = build_redesign_contract_rows()
    gate_rows = build_gate_rows(m145_cov, m146_cov, case_rows)
    route_rows = build_route_decision_rows()

    gate_fail_count = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    blocking_gate_fail_count = sum(
        1 for row in gate_rows if row.get("gate_status") == "fail" and row.get("blocks_next")
    )
    method = policy_rows.get(METHOD_POLICY, {})
    prior = policy_rows.get(PRIOR_REPAIR_POLICY, {})
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if blocking_gate_fail_count == 0 else BLOCKED_STATUS,
        "generated_at": generated_at,
        "m145_status": m145_cov.get("status"),
        "m146_status": m146_cov.get("status"),
        "missing_inputs": [],
        "case_delta_rows": len(case_rows),
        "profile_decomposition_rows": len(profile_rows),
        "policy_family_rows": len(family_rows),
        "failure_diagnosis_rows": len(failure_rows),
        "redesign_contract_rows": len(contract_rows),
        "gate_fail_count": gate_fail_count,
        "blocking_gate_fail_count": blocking_gate_fail_count,
        "method_policy_id": METHOD_POLICY,
        "method_SPL": method.get("SPL"),
        "method_delta_SPL_vs_detector_confidence": method.get("delta_SPL_vs_detector_confidence"),
        "method_delta_CandidateVisits_vs_detector_confidence": method.get(
            "delta_CandidateVisits_mean_vs_detector_confidence"
        ),
        "best_observed_policy_id": PRIOR_REPAIR_POLICY,
        "best_observed_policy_SPL": prior.get("SPL"),
        "best_observed_policy_delta_visits_vs_detector": prior.get(
            "delta_CandidateVisits_mean_vs_detector_confidence"
        ),
        "positive_navigation_improvement_ready": False,
        "redesign_contract_ready": blocking_gate_fail_count == 0,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_redesign_family": "budget_guarded_confidence_path_repair_v1",
        "selected_next_unit": NEXT_UNIT if blocking_gate_fail_count == 0 else None,
    }

    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_family_rows.jsonl", family_rows)
    write_jsonl(ARTIFACT_DIR / "case_delta_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "profile_decomposition_rows.jsonl", profile_rows)
    write_jsonl(ARTIFACT_DIR / "failure_diagnosis_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "redesign_contract_rows.jsonl", contract_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        render_report(coverage, family_rows, profile_rows, failure_rows, contract_rows, route_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
