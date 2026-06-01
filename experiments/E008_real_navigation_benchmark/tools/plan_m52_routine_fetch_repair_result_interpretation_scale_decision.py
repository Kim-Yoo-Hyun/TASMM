#!/usr/bin/env python3
"""Interpret M51 routine-fetch repair results and decide scale-up route."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0"
)
M51_DIR = EXP_ROOT / "artifacts" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"

VERSION = "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_v0"
READY_STATUS = "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready"
BLOCKED_STATUS = "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_blocked"
NEXT_UNIT = "E008-M53 routine-fetch task-context specificity boundary and next-route decision"

H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
H001_PREV_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_CURRENT_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_DIVERSE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"

POLICY_ORDER = [
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    H001_POLICY,
    H001_PREV_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    STATIC_POLICY,
    TASK_AGNOSTIC_POLICY,
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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def nullable_sub(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def gt(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and left_f > right_f)


def ge(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and left_f >= right_f)


def eq(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and abs(left_f - right_f) < 1e-12)


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def scan_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def policy_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def aggregate_rows(rows: list[dict[str, Any]], group: dict[str, Any]) -> dict[str, Any]:
    success_rows = sum(
        1 for row in rows if bool(row.get("trajectory_success")) or finite_float(row.get("SR")) == 1.0
    )
    return {
        **group,
        "rows": len(rows),
        "success_rows": success_rows,
        "SR": safe_ratio(success_rows, len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
        "stale_visit_first_rows": sum(1 for row in rows if bool(row.get("stale_visit_first"))),
        "current_observation_first_rows": sum(1 for row in rows if bool(row.get("current_observation_first"))),
    }


def build_policy_result_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = {str(row.get("policy_id")): row for row in policy_aggregate_rows(metric_rows)}
    out = []
    for policy_id in POLICY_ORDER:
        row = dict(aggregates.get(policy_id, {}))
        row.update(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "interpretation": interpret_policy(policy_id, row),
                "supports_final_navigation_claim": False,
            }
        )
        out.append(row)
    return out


def interpret_policy(policy_id: str, row: dict[str, Any]) -> str:
    if policy_id == H001_POLICY:
        return "repaired_h001_improves_sr_over_current_observation_and_previous_h001_but_ties_task_agnostic_and_loses_detector_spl"
    if policy_id == H001_PREV_POLICY:
        return "previous_h001_is_lower_than_repaired_h001_after_routine_fetch_safety_rule"
    if policy_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY}:
        return "current_observation_baseline_has_lower_sr_but_higher_spl_than_repaired_h001"
    if policy_id == SOURCE_DIVERSE_CURRENT_POLICY:
        return "source_diverse_current_observation_has_lower_sr_and_lower_spl_than_repaired_h001"
    if policy_id == STATIC_POLICY:
        return "static_stale_memory_lower_bound_fails_all_rows"
    if policy_id == TASK_AGNOSTIC_POLICY:
        return "task_agnostic_source_diverse_ties_repaired_h001_sr_spl_path_and_visits"
    return "requires_manual_review"


def build_pairwise_decision_rows(pairwise_input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_input_rows:
        if row.get("method_policy_id") == H001_POLICY:
            by_baseline[str(row.get("baseline_policy_id"))].append(row)

    out = []
    for baseline_id in [
        STATIC_POLICY,
        DETECTOR_POLICY,
        FIXED_CURRENT_POLICY,
        SOURCE_DIVERSE_CURRENT_POLICY,
        H001_PREV_POLICY,
        TASK_AGNOSTIC_POLICY,
    ]:
        rows = by_baseline.get(baseline_id, [])
        delta_sr = [finite_float(row.get("delta_SR")) for row in rows]
        delta_spl = [finite_float(row.get("delta_SPL")) for row in rows]
        delta_path = [finite_float(row.get("delta_PathLengthM")) for row in rows]
        current = {
            "version": VERSION,
            "method_policy_id": H001_POLICY,
            "baseline_policy_id": baseline_id,
            "rows": len(rows),
            "delta_SR_mean": mean(delta_sr),
            "delta_SPL_mean": mean(delta_spl),
            "delta_PathLengthM_mean": mean(delta_path),
            "sr_win_rows": sum(1 for value in delta_sr if value is not None and value > 0),
            "sr_tie_rows": sum(1 for value in delta_sr if value == 0),
            "sr_loss_rows": sum(1 for value in delta_sr if value is not None and value < 0),
            "spl_win_rows": sum(1 for value in delta_spl if value is not None and value > 0),
            "spl_tie_rows": sum(1 for value in delta_spl if value == 0),
            "spl_loss_rows": sum(1 for value in delta_spl if value is not None and value < 0),
        }
        current["interpretation"] = interpret_pairwise(current)
        current["supports_navigation_improvement_claim"] = supports_navigation_improvement(current)
        out.append(current)
    return out


def supports_navigation_improvement(row: dict[str, Any]) -> bool:
    baseline_id = row["baseline_policy_id"]
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    if baseline_id == STATIC_POLICY:
        return bool(delta_sr is not None and delta_sr > 0)
    return bool(delta_sr is not None and delta_spl is not None and delta_sr > 0 and delta_spl >= 0)


def interpret_pairwise(row: dict[str, Any]) -> str:
    baseline_id = row["baseline_policy_id"]
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    if baseline_id == STATIC_POLICY:
        return "repaired_h001_beats_static_lower_bound_only"
    if baseline_id == H001_PREV_POLICY:
        return "routine_fetch_safety_repair_improves_previous_h001_sr_spl_and_path"
    if baseline_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY}:
        if delta_sr is not None and delta_sr > 0 and delta_spl is not None and delta_spl < 0:
            return "repaired_h001_recovers_more_successes_but_loses_efficiency"
    if baseline_id == SOURCE_DIVERSE_CURRENT_POLICY:
        return "repaired_h001_beats_source_diverse_current_observation_but_this_does_not_isolate_task_context"
    if baseline_id == TASK_AGNOSTIC_POLICY:
        if delta_sr == 0 and delta_spl == 0:
            return "task_conditioning_has_no_observable_effect_against_task_agnostic_source_diverse"
    return "requires_manual_review"


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for boundary_value, boundary_name in [(False, "source_ready"), (True, "source_gap")]:
        for policy_id in POLICY_ORDER:
            rows = [
                row
                for row in scan_rows
                if row.get("policy_id") == policy_id and bool(row.get("diagnostic_source_gap_boundary")) is boundary_value
            ]
            aggregate = aggregate_rows(
                rows,
                {
                    "version": VERSION,
                    "boundary": boundary_name,
                    "diagnostic_source_gap_boundary": boundary_value,
                    "policy_id": policy_id,
                },
            )
            aggregate["interpretation"] = interpret_source_boundary(policy_id, boundary_name, aggregate)
            out.append(aggregate)
    return out


def interpret_source_boundary(policy_id: str, boundary_name: str, row: dict[str, Any]) -> str:
    if boundary_name == "source_ready":
        if policy_id in {H001_POLICY, H001_PREV_POLICY, DETECTOR_POLICY, FIXED_CURRENT_POLICY, SOURCE_DIVERSE_CURRENT_POLICY, TASK_AGNOSTIC_POLICY}:
            return "source_available_rows_are_easy_for_current_or_diverse_sources"
        if policy_id == STATIC_POLICY:
            return "static_stale_memory_still_fails_without_current_source_use"
    if boundary_name == "source_gap":
        if policy_id == H001_POLICY:
            return "repaired_h001_partially_recovers_source_gap_but_absolute_sr_is_low"
        if policy_id == TASK_AGNOSTIC_POLICY:
            return "task_agnostic_matches_repaired_h001_on_source_gap"
        if policy_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY, SOURCE_DIVERSE_CURRENT_POLICY}:
            return "current_observation_only_policy_largely_fails_source_gap"
        if policy_id == H001_PREV_POLICY:
            return "previous_h001_has_lower_source_gap_recovery_than_repaired_h001"
    return "requires_manual_review"


def build_task_context_effect_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_context: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in scan_rows:
        by_context[str(row.get("task_context_id"))][str(row.get("policy_id"))].append(row)

    out = []
    for context_id in sorted(by_context):
        h001 = aggregate_rows(by_context[context_id].get(H001_POLICY, []), {"policy_id": H001_POLICY})
        previous = aggregate_rows(by_context[context_id].get(H001_PREV_POLICY, []), {"policy_id": H001_PREV_POLICY})
        task_agnostic = aggregate_rows(
            by_context[context_id].get(TASK_AGNOSTIC_POLICY, []),
            {"policy_id": TASK_AGNOSTIC_POLICY},
        )
        detector = aggregate_rows(by_context[context_id].get(DETECTOR_POLICY, []), {"policy_id": DETECTOR_POLICY})
        row = {
            "version": VERSION,
            "task_context_id": context_id,
            "h001_rows": h001["rows"],
            "h001_SR": h001["SR"],
            "h001_SPL": h001["SPL"],
            "previous_h001_SR": previous["SR"],
            "previous_h001_SPL": previous["SPL"],
            "task_agnostic_SR": task_agnostic["SR"],
            "task_agnostic_SPL": task_agnostic["SPL"],
            "detector_SR": detector["SR"],
            "detector_SPL": detector["SPL"],
            "h001_minus_previous_SR": nullable_sub(h001["SR"], previous["SR"]),
            "h001_minus_previous_SPL": nullable_sub(h001["SPL"], previous["SPL"]),
            "h001_minus_task_agnostic_SR": nullable_sub(h001["SR"], task_agnostic["SR"]),
            "h001_minus_task_agnostic_SPL": nullable_sub(h001["SPL"], task_agnostic["SPL"]),
            "h001_minus_detector_SR": nullable_sub(h001["SR"], detector["SR"]),
            "h001_minus_detector_SPL": nullable_sub(h001["SPL"], detector["SPL"]),
        }
        row["interpretation"] = interpret_task_context(row)
        row["supports_human_intent_main_claim"] = False
        out.append(row)
    return out


def interpret_task_context(row: dict[str, Any]) -> str:
    delta_task_sr = finite_float(row.get("h001_minus_task_agnostic_SR"))
    delta_task_spl = finite_float(row.get("h001_minus_task_agnostic_SPL"))
    delta_prev_sr = finite_float(row.get("h001_minus_previous_SR"))
    if delta_task_sr == 0 and delta_task_spl == 0 and delta_prev_sr is not None and delta_prev_sr >= 0:
        return "repair_preserves_or_improves_previous_h001_but_task_context_has_no_effect_vs_task_agnostic"
    if delta_task_sr is not None and delta_task_sr < 0:
        return "task_conditioning_regresses_against_task_agnostic"
    if delta_task_sr is not None and delta_task_sr >= 0 and delta_task_spl is not None and delta_task_spl < 0:
        return "task_conditioning_keeps_success_but_adds_path_cost"
    return "requires_manual_review"


def build_regression_case_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, bool], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_rows:
        key = (
            str(row.get("adapter_episode_id")),
            str(row.get("task_context_id")),
            str(row.get("object_category")),
            bool(row.get("diagnostic_source_gap_boundary")),
        )
        by_key[key][str(row.get("policy_id"))] = row

    out = []
    for (episode_id, task_context_id, object_category, source_gap), policy_rows in sorted(by_key.items()):
        h001 = policy_rows.get(H001_POLICY)
        previous = policy_rows.get(H001_PREV_POLICY)
        task_agnostic = policy_rows.get(TASK_AGNOSTIC_POLICY)
        detector = policy_rows.get(DETECTOR_POLICY)
        if not h001 or not task_agnostic:
            continue
        task_delta_sr = nullable_sub(h001.get("SR"), task_agnostic.get("SR"))
        task_delta_spl = nullable_sub(h001.get("SPL"), task_agnostic.get("SPL"))
        detector_delta_spl = nullable_sub(h001.get("SPL"), detector.get("SPL") if detector else None)
        if not (
            (task_delta_sr is not None and task_delta_sr < 0)
            or (task_delta_spl is not None and task_delta_spl < 0)
            or (detector_delta_spl is not None and detector_delta_spl < 0 and finite_float(h001.get("SR")) == 1.0)
        ):
            continue
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "task_context_id": task_context_id,
                "object_category": object_category,
                "diagnostic_source_gap_boundary": source_gap,
                "h001_SR": h001.get("SR"),
                "h001_SPL": h001.get("SPL"),
                "previous_h001_SR": previous.get("SR") if previous else None,
                "previous_h001_SPL": previous.get("SPL") if previous else None,
                "task_agnostic_SR": task_agnostic.get("SR"),
                "task_agnostic_SPL": task_agnostic.get("SPL"),
                "detector_SR": detector.get("SR") if detector else None,
                "detector_SPL": detector.get("SPL") if detector else None,
                "h001_minus_task_agnostic_SR": task_delta_sr,
                "h001_minus_task_agnostic_SPL": task_delta_spl,
                "h001_minus_detector_SPL": detector_delta_spl,
                "suspected_cause": classify_regression(h001, task_agnostic, detector, source_gap),
            }
        )
    return out


def classify_regression(
    h001: dict[str, Any],
    task_agnostic: dict[str, Any],
    detector: dict[str, Any] | None,
    source_gap: bool,
) -> str:
    if eq(h001.get("SR"), task_agnostic.get("SR")) and eq(h001.get("SPL"), task_agnostic.get("SPL")):
        if detector and finite_float(h001.get("SPL")) is not None and finite_float(detector.get("SPL")) is not None:
            if finite_float(h001.get("SPL")) < finite_float(detector.get("SPL")) and not source_gap:
                return "source_diverse_visit_order_preserves_success_but_is_less_efficient_than_detector_confidence"
        return "task_conditioning_no_distinct_effect_vs_task_agnostic_source_diverse"
    if finite_float(h001.get("SR")) == 0.0 and finite_float(task_agnostic.get("SR")) == 1.0:
        return "task_conditioning_or_safety_rule_misses_candidate_reached_by_task_agnostic"
    return "requires_manual_review"


def build_scale_gate_rows(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy = {row["policy_id"]: row for row in policy_rows}
    pair = {row["baseline_policy_id"]: row for row in pairwise_rows}
    source = {(row["policy_id"], row["boundary"]): row for row in source_rows}

    h001 = policy[H001_POLICY]
    previous = policy[H001_PREV_POLICY]
    task_agnostic = policy[TASK_AGNOSTIC_POLICY]
    source_gap = source[(H001_POLICY, "source_gap")]
    task_source_gap = source[(TASK_AGNOSTIC_POLICY, "source_gap")]

    return [
        {
            "version": VERSION,
            "gate_id": "m51_execution_ready",
            "passed": coverage.get("status") == "e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready",
            "evidence": f"M51 status `{coverage.get('status')}` with {coverage.get('scan_task_policy_rows')} scan-task-policy rows.",
            "implication": "required_input_gate",
        },
        {
            "version": VERSION,
            "gate_id": "leakage_safe_execution",
            "passed": bool(coverage.get("leakage_audit_pass")) and not bool(coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
            "evidence": "M51 leakage audit passed and ObjectNav goal/viewpoint is not used for policy input.",
            "implication": "required_input_gate",
        },
        {
            "version": VERSION,
            "gate_id": "beats_static_stale_memory",
            "passed": gt(h001.get("SR"), policy[STATIC_POLICY].get("SR")),
            "evidence": f"H001 v2 SR {fmt(h001.get('SR'))} vs static SR {fmt(policy[STATIC_POLICY].get('SR'))}.",
            "implication": "lower_bound_recovery_only",
        },
        {
            "version": VERSION,
            "gate_id": "improves_previous_h001",
            "passed": gt(h001.get("SR"), previous.get("SR")) and ge(h001.get("SPL"), previous.get("SPL")),
            "evidence": f"H001 v2 SR/SPL {fmt(h001.get('SR'))}/{fmt(h001.get('SPL'))}; previous H001 {fmt(previous.get('SR'))}/{fmt(previous.get('SPL'))}.",
            "implication": "repair_positive_within_h001_family",
        },
        {
            "version": VERSION,
            "gate_id": "beats_current_observation_sr",
            "passed": gt(h001.get("SR"), policy[DETECTOR_POLICY].get("SR"))
            and gt(h001.get("SR"), policy[FIXED_CURRENT_POLICY].get("SR")),
            "evidence": f"H001 v2 SR {fmt(h001.get('SR'))}; detector/fixed SR {fmt(policy[DETECTOR_POLICY].get('SR'))}/{fmt(policy[FIXED_CURRENT_POLICY].get('SR'))}.",
            "implication": "smoke_positive_for_recovery",
        },
        {
            "version": VERSION,
            "gate_id": "beats_current_observation_spl",
            "passed": ge(pair[DETECTOR_POLICY].get("delta_SPL_mean"), 0.0)
            and ge(pair[FIXED_CURRENT_POLICY].get("delta_SPL_mean"), 0.0),
            "evidence": f"delta SPL vs detector {fmt(pair[DETECTOR_POLICY].get('delta_SPL_mean'))}; vs fixed {fmt(pair[FIXED_CURRENT_POLICY].get('delta_SPL_mean'))}.",
            "implication": "required_for_efficiency_claim",
        },
        {
            "version": VERSION,
            "gate_id": "beats_task_agnostic_source_diverse",
            "passed": gt(h001.get("SR"), task_agnostic.get("SR")) and ge(h001.get("SPL"), task_agnostic.get("SPL")),
            "evidence": f"H001 v2 SR/SPL {fmt(h001.get('SR'))}/{fmt(h001.get('SPL'))}; task-agnostic {fmt(task_agnostic.get('SR'))}/{fmt(task_agnostic.get('SPL'))}.",
            "implication": "required_for_task_conditioning_or_human_context_claim",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_absolute_recovery",
            "passed": ge(source_gap.get("SR"), 0.5),
            "evidence": f"H001 v2 source-gap SR {fmt(source_gap.get('SR'))}; source-gap success must be non-trivial before scale-up.",
            "implication": "required_for_dynamic_stale_memory_claim",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_beats_task_agnostic",
            "passed": gt(source_gap.get("SR"), task_source_gap.get("SR")),
            "evidence": f"H001 v2 source-gap SR {fmt(source_gap.get('SR'))}; task-agnostic source-gap SR {fmt(task_source_gap.get('SR'))}.",
            "implication": "required_for_task_conditioning_source_gap_claim",
        },
        {
            "version": VERSION,
            "gate_id": "all_task_contexts_have_distinct_effect",
            "passed": all(
                gt(row.get("h001_minus_task_agnostic_SR"), 0.0)
                or (eq(row.get("h001_minus_task_agnostic_SR"), 0.0) and gt(row.get("h001_minus_task_agnostic_SPL"), 0.0))
                for row in task_rows
            ),
            "evidence": "Each structured task context must improve SR or SPL over task-agnostic source-diverse.",
            "implication": "required_for_human_intent_main_claim",
        },
    ]


def build_claim_boundary_rows(scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_pass = {row["gate_id"]: bool(row["passed"]) for row in scale_rows}
    return [
        {
            "version": VERSION,
            "claim_id": "routine_fetch_repair_trajectory_smoke_ready",
            "supported": gate_pass["m51_execution_ready"] and gate_pass["leakage_safe_execution"],
            "claim_boundary": "M51 is a leakage-safe Docker Habitat trajectory smoke over 126 scan-task-policy rows.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_repair_improves_previous_h001",
            "supported": gate_pass["improves_previous_h001"],
            "claim_boundary": "The routine_fetch safety repair improves the previous H001 source-diverse policy within the same smoke denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_sr_gain_over_current_observation",
            "supported": gate_pass["beats_current_observation_sr"],
            "claim_boundary": "H001 v2 has a smoke-level SR gain over detector/fixed/current-observation baselines, but this is not sufficient for final navigation improvement.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_navigation_efficiency_gain",
            "supported": False,
            "claim_boundary": "H001 v2 loses SPL to detector/fixed current-observation baselines despite higher SR.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_or_human_intent_main_effect",
            "supported": False,
            "claim_boundary": "H001 v2 ties the task-agnostic source-diverse policy exactly, so structured task context is not supported as a main effect.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_recovery_ready_for_scale",
            "supported": False,
            "claim_boundary": "Source-gap SR remains low and does not beat the task-agnostic source-diverse policy.",
        },
        {
            "version": VERSION,
            "claim_id": "scale_to_broader_navigation_now",
            "supported": False,
            "claim_boundary": "Scale-up is blocked until task-context specificity and source-gap recovery are either repaired or removed from the main claim.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M52 is an interpretation gate, not a final real navigation benchmark.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack_id": "task_agnostic_tie",
            "risk": "A reviewer can remove structured task context and obtain the same SR/SPL/path result.",
            "defense_or_fix": "Do not claim human/task-context contribution yet; M53 must decide whether to repair task specificity or demote it to a condition.",
        },
        {
            "version": VERSION,
            "attack_id": "sr_spl_tradeoff_against_detector",
            "risk": "H001 v2 improves SR over detector/fixed baselines but is less efficient in SPL.",
            "defense_or_fix": "Report this as a recovery/coverage tradeoff; require efficiency repair before deployable navigation claim.",
        },
        {
            "version": VERSION,
            "attack_id": "source_gap_still_hard",
            "risk": "The dynamic stale-memory setting is most important under source gap, but source-gap SR remains low.",
            "defense_or_fix": "Separate source-ready and source-gap rows; require a source-gap-specific candidate-generation or memory-trust repair before scale.",
        },
        {
            "version": VERSION,
            "attack_id": "tiny_smoke_denominator",
            "risk": "The result is still a small controlled HM3D ObjectNav smoke.",
            "defense_or_fix": "Use M52 only as a go/no-go gate; broader benchmark execution waits for a policy that beats strong baselines.",
        },
    ]


def build_route_decision_rows(scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed = [row["gate_id"] for row in scale_rows if not row["passed"]]
    return [
        {
            "version": VERSION,
            "route_id": "scale_navigation_benchmark_now",
            "selected": False,
            "reason": "H001 v2 ties task-agnostic source-diverse, loses SPL to detector/fixed baselines, and has weak source-gap recovery.",
            "failed_gates": failed,
        },
        {
            "version": VERSION,
            "route_id": "repair_or_demote_task_context_before_scale",
            "selected": True,
            "reason": "The immediate novelty blocker is task-context indistinguishability, not Docker/Habitat execution readiness.",
            "selected_next_unit": NEXT_UNIT,
        },
    ]


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    regression_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M52 Routine-Fetch Repair Interpretation",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- M51 status: `{coverage['m51_status']}`",
        f"- Scale-up recommended now: `{str(coverage['scale_up_recommended_now']).lower()}`",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Final real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        f"- Human intent main claim ready: `{str(coverage['human_intent_main_claim_ready']).lower()}`",
        "",
        "## Policy Result",
        "",
        "| Policy | SR | SPL | PathLengthM | CandidateVisits | Interpretation |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in policy_rows:
        lines.append(
            "| "
            f"`{row['policy_id']}` | {fmt(row.get('SR'))} | {fmt(row.get('SPL'))} | "
            f"{fmt(row.get('PathLengthM_mean'))} | {fmt(row.get('CandidateVisits_mean'))} | "
            f"{row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Gate",
            "",
            "| Baseline | Delta SR | Delta SPL | Delta PathLengthM | SR W/T/L | SPL W/T/L | Interpretation |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in pairwise_rows:
        lines.append(
            "| "
            f"`{row['baseline_policy_id']}` | {fmt(row.get('delta_SR_mean'))} | "
            f"{fmt(row.get('delta_SPL_mean'))} | {fmt(row.get('delta_PathLengthM_mean'))} | "
            f"{row['sr_win_rows']}/{row['sr_tie_rows']}/{row['sr_loss_rows']} | "
            f"{row['spl_win_rows']}/{row['spl_tie_rows']}/{row['spl_loss_rows']} | "
            f"{row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Source Boundary",
            "",
            "| Boundary | Policy | Rows | SR | SPL | PathLengthM | Interpretation |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in source_rows:
        lines.append(
            "| "
            f"`{row['boundary']}` | `{row['policy_id']}` | {row['rows']} | {fmt(row.get('SR'))} | "
            f"{fmt(row.get('SPL'))} | {fmt(row.get('PathLengthM_mean'))} | {row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Task Context",
            "",
            "| Context | H001 v2 SR | Previous H001 SR | Task-Agnostic SR | H001-TaskAgnostic SR | H001 v2 SPL | Task-Agnostic SPL | H001-TaskAgnostic SPL | Interpretation |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in task_rows:
        lines.append(
            "| "
            f"`{row['task_context_id']}` | {fmt(row.get('h001_SR'))} | {fmt(row.get('previous_h001_SR'))} | "
            f"{fmt(row.get('task_agnostic_SR'))} | {fmt(row.get('h001_minus_task_agnostic_SR'))} | "
            f"{fmt(row.get('h001_SPL'))} | {fmt(row.get('task_agnostic_SPL'))} | "
            f"{fmt(row.get('h001_minus_task_agnostic_SPL'))} | {row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Regression / Weakness Cases",
            "",
            "| Episode | Context | Object | Source Gap | H001-TaskAgnostic SR | H001-TaskAgnostic SPL | H001-Detector SPL | Cause |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in regression_rows[:40]:
        lines.append(
            "| "
            f"`{row['adapter_episode_id']}` | `{row['task_context_id']}` | `{row['object_category']}` | "
            f"`{str(row['diagnostic_source_gap_boundary']).lower()}` | "
            f"{fmt(row.get('h001_minus_task_agnostic_SR'))} | {fmt(row.get('h001_minus_task_agnostic_SPL'))} | "
            f"{fmt(row.get('h001_minus_detector_SPL'))} | {row['suspected_cause']} |"
        )

    lines.extend(
        [
            "",
            "## Scale Decision",
            "",
            "| Gate | Passed | Evidence |",
            "|---|---|---|",
        ]
    )
    for row in scale_rows:
        lines.append(f"| `{row['gate_id']}` | `{str(row['passed']).lower()}` | {row['evidence']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not scale this policy to a broader navigation benchmark now.",
            "- Keep M51 as evidence that the repaired H001 policy improves the previous H001 policy and static/current-observation SR on this smoke denominator.",
            "- Do not claim human intent or task-context main contribution: task-agnostic source-diverse matches H001 v2 exactly.",
            "- Do not claim deployable navigation improvement: H001 v2 loses SPL to detector/fixed baselines.",
            f"- Next unit: `{NEXT_UNIT}`.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m51_coverage = read_json(M51_DIR / "coverage.json")
    metric_rows = read_jsonl(M51_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_input_rows = read_jsonl(M51_DIR / "pairwise_policy_delta_rows.jsonl")
    scan_rows = scan_task_rows(metric_rows)

    if not m51_coverage:
        raise SystemExit("missing M51 coverage")
    if not metric_rows or not pairwise_input_rows or not scan_rows:
        raise SystemExit("missing M51 metric inputs")

    policy_rows = build_policy_result_rows(metric_rows)
    pairwise_rows = build_pairwise_decision_rows(pairwise_input_rows)
    source_rows = build_source_boundary_rows(scan_rows)
    task_rows = build_task_context_effect_rows(scan_rows)
    regression_rows = build_regression_case_rows(scan_rows)
    scale_rows = build_scale_gate_rows(m51_coverage, policy_rows, pairwise_rows, source_rows, task_rows)
    claim_rows = build_claim_boundary_rows(scale_rows)
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows(scale_rows)

    m51_ready = m51_coverage.get("status") == "e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready"
    scale_up = False
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if m51_ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m51_status": m51_coverage.get("status"),
        "m51_scan_task_policy_rows": m51_coverage.get("scan_task_policy_rows"),
        "m51_trajectory_attempt_rows": m51_coverage.get("trajectory_attempt_rows"),
        "m51_leakage_audit_pass": m51_coverage.get("leakage_audit_pass"),
        "policy_result_rows": len(policy_rows),
        "pairwise_decision_rows": len(pairwise_rows),
        "source_boundary_rows": len(source_rows),
        "task_context_effect_rows": len(task_rows),
        "regression_or_weakness_case_rows": len(regression_rows),
        "scale_gate_rows": len(scale_rows),
        "scale_gate_pass_rows": sum(1 for row in scale_rows if row["passed"]),
        "scale_up_recommended_now": scale_up,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_decision_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "task_context_effect_rows.jsonl", task_rows)
    write_jsonl(ARTIFACT_DIR / "regression_or_weakness_case_rows.jsonl", regression_rows)
    write_jsonl(ARTIFACT_DIR / "scale_gate_rows.jsonl", scale_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_report(coverage, policy_rows, pairwise_rows, source_rows, task_rows, regression_rows, scale_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
