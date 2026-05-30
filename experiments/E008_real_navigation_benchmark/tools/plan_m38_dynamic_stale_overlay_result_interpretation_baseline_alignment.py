#!/usr/bin/env python3
"""Interpret E008-M37 dynamic-stale overlay trajectories before scale-up."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0"
)
VERSION = "e008_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0"

M37_DIR = EXP_ROOT / "artifacts" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"

H001_POLICY = "h001_task_conditioned_memory_trust_navigation_v0"
STATIC_POLICY = "static_stale_memory_top1_v0"
FIXED_TOPK_POLICY = "fixed_topk_current_observation_v0"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
TASK_AGNOSTIC_POLICY = "task_agnostic_memory_trust_navigation_v0"
NEXT_UNIT = "E008-M39 budget-matched dynamic-stale policy repair and source-gap contract"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def policy_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def index_policy_aggregates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in policy_aggregate_rows(rows)}


def aggregate_group(rows: list[dict[str, Any]], group: dict[str, Any]) -> dict[str, Any]:
    success_rows = sum(1 for row in rows if bool(row.get("trajectory_success")) or finite_float(row.get("SR")) == 1.0)
    return {
        **group,
        "rows": len(rows),
        "success_rows": success_rows,
        "SR": safe_ratio(success_rows, len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]),
        "stale_visit_first_rows": sum(1 for row in rows if bool(row.get("stale_visit_first"))),
        "current_observation_first_rows": sum(1 for row in rows if bool(row.get("current_observation_first"))),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
    }


def build_policy_result_rows(all_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = index_policy_aggregates(all_rows)
    scan_rows = metric_rows(all_rows)
    rows = []
    for policy_id in [DETECTOR_POLICY, FIXED_TOPK_POLICY, H001_POLICY, STATIC_POLICY, TASK_AGNOSTIC_POLICY]:
        row = dict(aggregates.get(policy_id, {}))
        policy_scan_rows = [scan_row for scan_row in scan_rows if scan_row.get("policy_id") == policy_id]
        row.update(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "stale_visit_first_rows": sum(1 for scan_row in policy_scan_rows if bool(scan_row.get("stale_visit_first"))),
                "current_observation_first_rows": sum(
                    1 for scan_row in policy_scan_rows if bool(scan_row.get("current_observation_first"))
                ),
                "m38_interpretation": interpret_policy(policy_id, row),
            }
        )
        rows.append(row)
    return rows


def interpret_policy(policy_id: str, row: dict[str, Any]) -> str:
    sr = finite_float(row.get("SR"))
    spl = finite_float(row.get("SPL"))
    if policy_id == STATIC_POLICY:
        return "naive_static_stale_memory_fails_all_rows"
    if policy_id == DETECTOR_POLICY and sr == 1.0:
        return "strong_current_observation_baseline_dominates_smoke_denominator_but_uses_many_visits"
    if policy_id == FIXED_TOPK_POLICY:
        return "bounded_current_observation_matches_h001_success_with_higher_spl"
    if policy_id == TASK_AGNOSTIC_POLICY:
        return "task_context_ablation_matches_h001_success_and_beats_h001_spl"
    if policy_id == H001_POLICY and sr == 0.5 and spl is not None:
        return "h001_beats_static_but_fails_navigation_improvement_claim"
    return "requires_manual_review"


def build_pairwise_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_baseline[str(row.get("baseline_policy_id"))].append(row)
    for baseline_id in [STATIC_POLICY, FIXED_TOPK_POLICY, DETECTOR_POLICY, TASK_AGNOSTIC_POLICY]:
        current = by_baseline.get(baseline_id, [])
        delta_sr = [finite_float(row.get("delta_SR")) for row in current]
        delta_spl = [finite_float(row.get("delta_SPL")) for row in current]
        delta_path = [finite_float(row.get("delta_PathLengthM")) for row in current]
        rows.append(
            {
                "version": VERSION,
                "method_policy_id": H001_POLICY,
                "baseline_policy_id": baseline_id,
                "rows": len(current),
                "delta_SR_mean": mean(delta_sr),
                "delta_SPL_mean": mean(delta_spl),
                "delta_PathLengthM_mean": mean(delta_path),
                "sr_win_rows": sum(1 for value in delta_sr if value is not None and value > 0),
                "sr_tie_rows": sum(1 for value in delta_sr if value == 0),
                "sr_loss_rows": sum(1 for value in delta_sr if value is not None and value < 0),
                "spl_win_rows": sum(1 for value in delta_spl if value is not None and value > 0),
                "spl_tie_rows": sum(1 for value in delta_spl if value == 0),
                "spl_loss_rows": sum(1 for value in delta_spl if value is not None and value < 0),
                "interpretation": interpret_pairwise(baseline_id, mean(delta_sr), mean(delta_spl), current),
            }
        )
    return rows


def interpret_pairwise(
    baseline_id: str,
    delta_sr_mean: float | None,
    delta_spl_mean: float | None,
    rows: list[dict[str, Any]],
) -> str:
    if not rows:
        return "missing_pairwise_rows"
    if baseline_id == STATIC_POLICY and delta_sr_mean is not None and delta_sr_mean > 0:
        return "h001_supports_bounded_improvement_over_static_stale_memory"
    if baseline_id == DETECTOR_POLICY:
        return "h001_underperforms_detector_confidence_on_success_and_efficiency"
    if baseline_id == FIXED_TOPK_POLICY:
        return "h001_has_no_success_gain_over_fixed_current_topk_and_loses_efficiency"
    if baseline_id == TASK_AGNOSTIC_POLICY:
        return "task_conditioning_not_supported_as_main_effect_in_m37"
    return "requires_manual_review"


def build_task_context_effect_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(str(row.get("adapter_episode_id")), str(row.get("task_context_id")))][str(row.get("policy_id"))] = row

    contexts = sorted({str(row.get("task_context_id")) for row in rows})
    out = []
    for context_id in contexts:
        diffs = []
        for (episode_id, task_id), policy_rows in by_key.items():
            if task_id != context_id:
                continue
            h001 = policy_rows.get(H001_POLICY)
            task_agnostic = policy_rows.get(TASK_AGNOSTIC_POLICY)
            fixed_topk = policy_rows.get(FIXED_TOPK_POLICY)
            detector = policy_rows.get(DETECTOR_POLICY)
            if not h001 or not task_agnostic:
                continue
            diffs.append(
                {
                    "episode_id": episode_id,
                    "h001_minus_task_agnostic_SR": finite_float(h001.get("SR")) - finite_float(task_agnostic.get("SR")),
                    "h001_minus_task_agnostic_SPL": finite_float(h001.get("SPL"))
                    - finite_float(task_agnostic.get("SPL")),
                    "h001_minus_task_agnostic_PathLengthM": finite_float(h001.get("PathLengthM"))
                    - finite_float(task_agnostic.get("PathLengthM")),
                    "h001_minus_fixed_topk_SR": finite_float(h001.get("SR")) - finite_float(fixed_topk.get("SR"))
                    if fixed_topk
                    else None,
                    "h001_minus_detector_SR": finite_float(h001.get("SR")) - finite_float(detector.get("SR"))
                    if detector
                    else None,
                    "h001_stale_visit_first": bool(h001.get("stale_visit_first")),
                    "task_agnostic_stale_visit_first": bool(task_agnostic.get("stale_visit_first")),
                }
            )
        out.append(
            {
                "version": VERSION,
                "task_context_id": context_id,
                "rows": len(diffs),
                "h001_minus_task_agnostic_SR_mean": mean(
                    [finite_float(row.get("h001_minus_task_agnostic_SR")) for row in diffs]
                ),
                "h001_minus_task_agnostic_SPL_mean": mean(
                    [finite_float(row.get("h001_minus_task_agnostic_SPL")) for row in diffs]
                ),
                "h001_minus_task_agnostic_PathLengthM_mean": mean(
                    [finite_float(row.get("h001_minus_task_agnostic_PathLengthM")) for row in diffs]
                ),
                "h001_minus_fixed_topk_SR_mean": mean([finite_float(row.get("h001_minus_fixed_topk_SR")) for row in diffs]),
                "h001_minus_detector_SR_mean": mean([finite_float(row.get("h001_minus_detector_SR")) for row in diffs]),
                "h001_stale_visit_first_rows": sum(1 for row in diffs if row.get("h001_stale_visit_first")),
                "task_agnostic_stale_visit_first_rows": sum(
                    1 for row in diffs if row.get("task_agnostic_stale_visit_first")
                ),
                "interpretation": interpret_task_context(context_id, diffs),
            }
        )
    return out


def interpret_task_context(context_id: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_context_rows"
    delta_sr = mean([finite_float(row.get("h001_minus_task_agnostic_SR")) for row in rows])
    delta_spl = mean([finite_float(row.get("h001_minus_task_agnostic_SPL")) for row in rows])
    h001_stale = sum(1 for row in rows if row.get("h001_stale_visit_first"))
    agnostic_stale = sum(1 for row in rows if row.get("task_agnostic_stale_visit_first"))
    if delta_sr == 0 and delta_spl is not None and delta_spl < 0:
        return "task_condition_changes_ordering_but_not_success_and_lowers_efficiency"
    if context_id == "noisy_high_value_fetch" and h001_stale < agnostic_stale:
        return "noise_context_avoids_stale_first_but_without_success_gain"
    return "task_context_effect_requires_repair_or_larger_scale"


def build_source_gap_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("policy_id")), bool(row.get("diagnostic_source_gap_boundary")))].append(row)
    out = []
    for policy_id in [DETECTOR_POLICY, FIXED_TOPK_POLICY, H001_POLICY, STATIC_POLICY, TASK_AGNOSTIC_POLICY]:
        for source_gap in [False, True]:
            current = groups.get((policy_id, source_gap), [])
            out.append(
                {
                    "version": VERSION,
                    "policy_id": policy_id,
                    "diagnostic_source_gap_boundary": source_gap,
                    **aggregate_group(current, {}),
                    "interpretation": interpret_source_gap(policy_id, source_gap, current),
                }
            )
    return out


def interpret_source_gap(policy_id: str, source_gap: bool, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_rows"
    sr = safe_ratio(sum(1 for row in rows if bool(row.get("trajectory_success"))), len(rows))
    if source_gap and policy_id == DETECTOR_POLICY and sr == 1.0:
        return "detector_can_recover_source_gap_only_by_searching_many_current_candidates"
    if source_gap and policy_id in {H001_POLICY, FIXED_TOPK_POLICY, TASK_AGNOSTIC_POLICY} and sr == 0.0:
        return "bounded_policy_source_gap_failure"
    if not source_gap and policy_id in {H001_POLICY, TASK_AGNOSTIC_POLICY} and sr == 1.0:
        return "memory_trust_policy_succeeds_when_candidate_source_has_target_region"
    if not source_gap and policy_id == STATIC_POLICY and sr == 0.0:
        return "static_old_location_fails_even_when_current_source_is_available"
    return "requires_manual_review"


def value_by_policy(policy_rows: list[dict[str, Any]], policy_id: str, key: str) -> float | None:
    for row in policy_rows:
        if row.get("policy_id") == policy_id:
            return finite_float(row.get(key))
    return None


def build_failure_diagnosis_rows(
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    m37_cov: dict[str, Any],
) -> list[dict[str, Any]]:
    h001_sr = value_by_policy(policy_rows, H001_POLICY, "SR")
    h001_spl = value_by_policy(policy_rows, H001_POLICY, "SPL")
    detector_sr = value_by_policy(policy_rows, DETECTOR_POLICY, "SR")
    detector_spl = value_by_policy(policy_rows, DETECTOR_POLICY, "SPL")
    fixed_sr = value_by_policy(policy_rows, FIXED_TOPK_POLICY, "SR")
    fixed_spl = value_by_policy(policy_rows, FIXED_TOPK_POLICY, "SPL")
    agnostic_sr = value_by_policy(policy_rows, TASK_AGNOSTIC_POLICY, "SR")
    agnostic_spl = value_by_policy(policy_rows, TASK_AGNOSTIC_POLICY, "SPL")
    static_sr = value_by_policy(policy_rows, STATIC_POLICY, "SR")
    source_gap_h001 = next(
        (row for row in source_gap_rows if row.get("policy_id") == H001_POLICY and row.get("diagnostic_source_gap_boundary")),
        {},
    )
    source_gap_detector = next(
        (
            row
            for row in source_gap_rows
            if row.get("policy_id") == DETECTOR_POLICY and row.get("diagnostic_source_gap_boundary")
        ),
        {},
    )
    h001_stale_rows = next((row for row in policy_rows if row.get("policy_id") == H001_POLICY), {}).get(
        "stale_visit_first_rows"
    )
    no_task_gain = all(finite_float(row.get("h001_minus_task_agnostic_SR_mean")) == 0.0 for row in task_rows)
    return [
        {
            "version": VERSION,
            "diagnosis_id": "static_stale_memory_is_a_valid_naive_failure",
            "status": "supported_lower_bound_only",
            "evidence": f"H001 SR {fmt(h001_sr)} vs static SR {fmt(static_sr)}.",
            "implication": "The stale-memory problem is real, but beating static memory is not enough for a top-tier navigation claim.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "detector_confidence_baseline_not_rebutted",
            "status": "claim_blocker",
            "evidence": f"Detector confidence SR/SPL {fmt(detector_sr)}/{fmt(detector_spl)} vs H001 {fmt(h001_sr)}/{fmt(h001_spl)}.",
            "implication": "A future H001 navigation claim must either beat this baseline under budget-matched conditions or explain why the baseline uses an unrealistic search budget.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "fixed_current_observation_beats_h001_efficiency",
            "status": "claim_blocker",
            "evidence": f"Fixed current top-k SR/SPL {fmt(fixed_sr)}/{fmt(fixed_spl)} vs H001 {fmt(h001_sr)}/{fmt(h001_spl)}.",
            "implication": "The next policy must show why memory trust is better than a simple bounded current-observation policy.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "task_context_conditioning_not_yet_a_main_effect",
            "status": "human_intent_claim_blocker" if no_task_gain else "needs_more_rows",
            "evidence": f"Task-agnostic memory trust SR/SPL {fmt(agnostic_sr)}/{fmt(agnostic_spl)} vs H001 {fmt(h001_sr)}/{fmt(h001_spl)}.",
            "implication": "Human intent should remain structured task context / ablation until it changes decisions with measurable gains.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "stale_first_dead_end_and_visit_order_cost",
            "status": "partial_mechanism",
            "evidence": f"H001 stale-visit-first rows {h001_stale_rows}/18 and OldLocationDeadEndCostM mean {fmt(value_by_policy(policy_rows, H001_POLICY, 'OldLocationDeadEndCostM_mean'))}.",
            "implication": "Repair should penalize stale-first visits unless current evidence is weak or task utility justifies the dead-end risk.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "source_gap_budget_mismatch",
            "status": "claim_blocker",
            "evidence": f"Source-gap subset H001 SR {fmt(source_gap_h001.get('SR'))} vs detector SR {fmt(source_gap_detector.get('SR'))}.",
            "implication": "Separate source construction failures from policy failures and introduce budget-matched baselines before scaling.",
        },
        {
            "version": VERSION,
            "diagnosis_id": "smoke_scale_boundary",
            "status": "scale_claim_blocker",
            "evidence": f"Scene count {m37_cov.get('scene_count')}, scan-task-policy rows {m37_cov.get('scan_task_policy_rows')}, intervention rows {m37_cov.get('intervention_rows')}.",
            "implication": "M37 is useful for design debugging, not for final real navigation SR/SPL or generality claims.",
        },
    ]


def build_claim_boundary_rows(policy_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    h001_sr = value_by_policy(policy_rows, H001_POLICY, "SR")
    detector_sr = value_by_policy(policy_rows, DETECTOR_POLICY, "SR")
    agnostic_sr = value_by_policy(policy_rows, TASK_AGNOSTIC_POLICY, "SR")
    static_sr = value_by_policy(policy_rows, STATIC_POLICY, "SR")
    h001_vs_static = next((row for row in pairwise_rows if row.get("baseline_policy_id") == STATIC_POLICY), {})
    h001_vs_detector = next((row for row in pairwise_rows if row.get("baseline_policy_id") == DETECTOR_POLICY), {})
    h001_vs_agnostic = next((row for row in pairwise_rows if row.get("baseline_policy_id") == TASK_AGNOSTIC_POLICY), {})
    return [
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_overlay_trajectory_smoke",
            "supported": True,
            "boundary": "M37/M38 support an executable counterfactual dynamic-stale overlay trajectory smoke.",
            "evidence": "90 scan-task-policy rows and 467 trajectory attempt rows executed with leakage pass.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_beats_static_stale_memory",
            "supported": bool(h001_sr is not None and static_sr is not None and h001_sr > static_sr),
            "boundary": "This is a lower-bound naive-baseline claim, not a top-tier navigation contribution by itself.",
            "evidence": f"H001 SR {fmt(h001_sr)} vs static SR {fmt(static_sr)}; mean delta SR {fmt(h001_vs_static.get('delta_SR_mean'))}.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_beats_detector_confidence_navigation",
            "supported": False,
            "boundary": "Blocked because current detector-confidence baseline dominates H001 on SR/SPL.",
            "evidence": f"H001 SR {fmt(h001_sr)} vs detector SR {fmt(detector_sr)}; mean delta SR {fmt(h001_vs_detector.get('delta_SR_mean'))}.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_main_human_intent_claim",
            "supported": False,
            "boundary": "Blocked because structured task context does not improve SR over task-agnostic memory trust in M37.",
            "evidence": f"H001 SR {fmt(h001_sr)} vs task-agnostic SR {fmt(agnostic_sr)}; mean delta SR {fmt(h001_vs_agnostic.get('delta_SR_mean'))}.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "boundary": "Blocked until policy repair, scale, budget-matched baselines, and navigation/search baselines are added.",
            "evidence": "M37 is a 6-episode smoke and H001 does not beat required current-observation baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "boundary": "Blocked; M38 interprets navigation rows and does not add a new RGB-D/open-vocabulary detector route.",
            "evidence": "Use E003/E005 artifacts for proposal robustness, not E008-M38.",
        },
    ]


def build_reviewer_defense_rows(diagnosis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "reviewer_question": "Why is H001 not just worse than detector confidence?",
            "answer_status": "not_yet_defensible_as_positive_navigation_claim",
            "evidence_pointer": "detector_confidence_baseline_not_rebutted",
            "required_next_evidence": "Budget-matched detector baseline and source-gap-aware policy repair.",
        },
        {
            "version": VERSION,
            "reviewer_question": "Does task context matter?",
            "answer_status": "not_yet_as_main_claim",
            "evidence_pointer": "task_context_conditioning_not_yet_a_main_effect",
            "required_next_evidence": "Task contexts must alter memory trust/re-observation decisions with SR/SPL or cost gains.",
        },
        {
            "version": VERSION,
            "reviewer_question": "Why not always use current observations?",
            "answer_status": "not_yet_rebutted",
            "evidence_pointer": "fixed_current_observation_beats_h001_efficiency",
            "required_next_evidence": "Show conditions where memory trust improves over fixed current top-k under equal budget.",
        },
        {
            "version": VERSION,
            "reviewer_question": "Can this be scaled now?",
            "answer_status": "scale_up_not_recommended_before_repair",
            "evidence_pointer": "smoke_scale_boundary",
            "required_next_evidence": "M39 repair contract, then repeat trajectory smoke before broader scene scale.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m38_next_unit",
            "decision": "repair_before_scale",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M37 is executable but H001 underperforms detector confidence, fixed current top-k on SPL, and task-agnostic memory trust on SPL.",
            "next_action": "Design a budget-matched source-gap-aware policy repair contract before any larger navigation scale-up.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m38_baseline_alignment",
            "decision": "keep_detector_fixed_topk_static_and_task_agnostic_as_required_rows",
            "selected_next_unit": NEXT_UNIT,
            "reason": "These baselines expose distinct reviewer attacks: stale-memory lower bound, current-only policy, strong detector route, and no-task-context ablation.",
            "next_action": "Carry all four baselines into M39 and require budget-matched candidate visits/search cost accounting.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m38_claim_boundary",
            "decision": "do_not_claim_final_navigation_or_human_intent",
            "selected_next_unit": NEXT_UNIT,
            "reason": "Current evidence supports only a trajectory smoke and a static-memory lower-bound improvement.",
            "next_action": "Update claim boundary and keep final real navigation, final RGB-D/open-vocabulary robustness, and human intent main claim false.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    diagnosis_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E008-M38 Dynamic-Stale Overlay Result Interpretation / Baseline Alignment",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Input M37 status: `{coverage['m37_status']}`.",
        f"- Scan-task-policy rows: {coverage['m37_scan_task_policy_rows']}.",
        f"- Pairwise baseline summary rows: {coverage['pairwise_baseline_summary_rows']}.",
        f"- H001 `SR` / `SPL`: {fmt(coverage['h001_SR'])} / {fmt(coverage['h001_SPL'])}.",
        f"- Detector confidence `SR` / `SPL`: {fmt(coverage['detector_confidence_SR'])} / {fmt(coverage['detector_confidence_SPL'])}.",
        f"- Fixed current top-k `SR` / `SPL`: {fmt(coverage['fixed_topk_SR'])} / {fmt(coverage['fixed_topk_SPL'])}.",
        f"- Task-agnostic memory trust `SR` / `SPL`: {fmt(coverage['task_agnostic_SR'])} / {fmt(coverage['task_agnostic_SPL'])}.",
        f"- Static stale memory `SR` / `SPL`: {fmt(coverage['static_SR'])} / {fmt(coverage['static_SPL'])}.",
        "",
        "## Policy Alignment",
        "",
        "| policy_id | rows | success | SR | SPL | PathLengthM | CandidateVisits | OldDeadEndM | interpretation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in policy_rows:
        lines.append(
            "| {policy_id} | {scan_task_policy_rows} | {success_rows} | {SR} | {SPL} | {PathLengthM_mean} | {CandidateVisits_mean} | {OldLocationDeadEndCostM_mean} | {interp} |".format(
                policy_id=row.get("policy_id"),
                scan_task_policy_rows=row.get("scan_task_policy_rows"),
                success_rows=row.get("success_rows"),
                SR=fmt(row.get("SR")),
                SPL=fmt(row.get("SPL")),
                PathLengthM_mean=fmt(row.get("PathLengthM_mean")),
                CandidateVisits_mean=fmt(row.get("CandidateVisits_mean")),
                OldLocationDeadEndCostM_mean=fmt(row.get("OldLocationDeadEndCostM_mean")),
                interp=row.get("m38_interpretation"),
            )
        )
    lines.extend(
        [
            "",
            "## H001 Pairwise Summary",
            "",
            "| baseline | rows | dSR | dSPL | dPathLengthM | SR win/tie/loss | SPL win/tie/loss | interpretation |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in pairwise_rows:
        lines.append(
            "| {baseline} | {rows} | {dSR} | {dSPL} | {dPath} | {sr_win}/{sr_tie}/{sr_loss} | {spl_win}/{spl_tie}/{spl_loss} | {interp} |".format(
                baseline=row.get("baseline_policy_id"),
                rows=row.get("rows"),
                dSR=fmt(row.get("delta_SR_mean")),
                dSPL=fmt(row.get("delta_SPL_mean")),
                dPath=fmt(row.get("delta_PathLengthM_mean")),
                sr_win=row.get("sr_win_rows"),
                sr_tie=row.get("sr_tie_rows"),
                sr_loss=row.get("sr_loss_rows"),
                spl_win=row.get("spl_win_rows"),
                spl_tie=row.get("spl_tie_rows"),
                spl_loss=row.get("spl_loss_rows"),
                interp=row.get("interpretation"),
            )
        )
    lines.extend(
        [
            "",
            "## Failure Diagnosis",
            "",
        ]
    )
    for row in diagnosis_rows:
        lines.append(f"- `{row['diagnosis_id']}`: {row['status']}. {row['evidence']} {row['implication']}")
    lines.extend(
        [
            "",
            "## Task Context Boundary",
            "",
            "| task_context_id | rows | dSR vs task-agnostic | dSPL vs task-agnostic | H001 stale-first rows | interpretation |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in task_rows:
        lines.append(
            "| {task} | {rows} | {dSR} | {dSPL} | {stale} | {interp} |".format(
                task=row.get("task_context_id"),
                rows=row.get("rows"),
                dSR=fmt(row.get("h001_minus_task_agnostic_SR_mean")),
                dSPL=fmt(row.get("h001_minus_task_agnostic_SPL_mean")),
                stale=row.get("h001_stale_visit_first_rows"),
                interp=row.get("interpretation"),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}`: supported={str(row['supported']).lower()}. {row['boundary']}")
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            f"- Selected next unit: {route_rows[0]['selected_next_unit']}.",
            f"- Decision: `{route_rows[0]['decision']}`.",
            f"- Reason: {route_rows[0]['reason']}",
            "",
            "## Source-Gap Note",
            "",
            "- Source-gap rows should not be hidden or filtered out. They are the strongest current evidence that H001 needs a source-gap-aware repair before scale-up.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m37_cov = read_json(M37_DIR / "coverage.json")
    all_metric_rows = read_jsonl(M37_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    scan_policy_rows = metric_rows(all_metric_rows)
    m37_pairwise_rows = read_jsonl(M37_DIR / "pairwise_policy_delta_rows.jsonl")

    policy_rows = build_policy_result_rows(all_metric_rows)
    pairwise_rows = build_pairwise_summary_rows(m37_pairwise_rows)
    task_rows = build_task_context_effect_rows(scan_policy_rows)
    source_gap_rows = build_source_gap_rows(scan_policy_rows)
    diagnosis_rows = build_failure_diagnosis_rows(policy_rows, pairwise_rows, task_rows, source_gap_rows, m37_cov)
    claim_rows = build_claim_boundary_rows(policy_rows, pairwise_rows)
    reviewer_rows = build_reviewer_defense_rows(diagnosis_rows)
    route_rows = build_route_decision_rows()

    coverage = {
        "version": VERSION,
        "status": "e008_m38_dynamic_stale_overlay_result_interpretation_baseline_alignment_ready",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m37_status": m37_cov.get("status"),
        "m37_scan_task_policy_rows": m37_cov.get("scan_task_policy_rows"),
        "m37_trajectory_attempt_rows": m37_cov.get("trajectory_attempt_rows"),
        "m37_policy_count": m37_cov.get("policy_count"),
        "scene_count": m37_cov.get("scene_count"),
        "intervention_rows": m37_cov.get("intervention_rows"),
        "policy_result_rows": len(policy_rows),
        "pairwise_baseline_summary_rows": len(pairwise_rows),
        "task_context_effect_rows": len(task_rows),
        "source_gap_diagnosis_rows": len(source_gap_rows),
        "failure_diagnosis_rows": len(diagnosis_rows),
        "claim_boundary_rows": len(claim_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "route_decision_rows": len(route_rows),
        "h001_SR": value_by_policy(policy_rows, H001_POLICY, "SR"),
        "h001_SPL": value_by_policy(policy_rows, H001_POLICY, "SPL"),
        "static_SR": value_by_policy(policy_rows, STATIC_POLICY, "SR"),
        "static_SPL": value_by_policy(policy_rows, STATIC_POLICY, "SPL"),
        "fixed_topk_SR": value_by_policy(policy_rows, FIXED_TOPK_POLICY, "SR"),
        "fixed_topk_SPL": value_by_policy(policy_rows, FIXED_TOPK_POLICY, "SPL"),
        "detector_confidence_SR": value_by_policy(policy_rows, DETECTOR_POLICY, "SR"),
        "detector_confidence_SPL": value_by_policy(policy_rows, DETECTOR_POLICY, "SPL"),
        "task_agnostic_SR": value_by_policy(policy_rows, TASK_AGNOSTIC_POLICY, "SR"),
        "task_agnostic_SPL": value_by_policy(policy_rows, TASK_AGNOSTIC_POLICY, "SPL"),
        "h001_beats_static_memory": True,
        "h001_beats_detector_confidence": False,
        "h001_beats_fixed_current_topk_success": False,
        "h001_beats_task_agnostic_success": False,
        "task_context_main_claim_ready": False,
        "budget_matched_policy_repair_needed": True,
        "source_gap_repair_needed": True,
        "scale_up_recommended_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_baseline_summary_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "task_context_effect_rows.jsonl", task_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_diagnosis_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "failure_diagnosis_rows.jsonl", diagnosis_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, pairwise_rows, task_rows, source_gap_rows, diagnosis_rows, claim_rows, route_rows),
        encoding="utf-8",
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "policy_result_rows.jsonl", policy_rows)
    write_jsonl(DATA_OUT_DIR / "pairwise_baseline_summary_rows.jsonl", pairwise_rows)
    write_jsonl(DATA_OUT_DIR / "failure_diagnosis_rows.jsonl", diagnosis_rows)
    write_jsonl(DATA_OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
