#!/usr/bin/env python3
"""Interpret M61 high-path tail-slot trajectory results and decide scale route."""

from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0"
)
M61_DIR = EXP_ROOT / "artifacts" / "E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0"

VERSION = "e008_m62_high_path_tail_slot_result_interpretation_scale_decision_v0"
READY_STATUS = "e008_m62_high_path_tail_slot_result_interpretation_scale_decision_ready"
BLOCKED_STATUS = "e008_m62_high_path_tail_slot_result_interpretation_scale_decision_blocked"
NEXT_UNIT = "E008-M63 high-path tail-slot scale-up contract and source-boundary baseline plan"

H001_POLICY = "h001_task_conditioned_high_path_tail_slot_budget5_v3"
H001_BASE_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
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
    H001_BASE_POLICY,
    H001_PREV_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    STATIC_POLICY,
    TASK_AGNOSTIC_POLICY,
]

PAIRWISE_BASELINES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    H001_BASE_POLICY,
    H001_PREV_POLICY,
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: sanitize_json(row.get(key)) for key in fieldnames})


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


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def scan_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def policy_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def is_success(row: dict[str, Any]) -> bool:
    return bool(row.get("trajectory_success")) or finite_float(row.get("SR")) == 1.0


def aggregate(rows: list[dict[str, Any]], group: dict[str, Any]) -> dict[str, Any]:
    success_rows = sum(1 for row in rows if is_success(row))
    return {
        **group,
        "rows": len(rows),
        "success_rows": success_rows,
        "SR": safe_ratio(success_rows, len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]),
        "StopRank_mean_over_success": mean(
            [finite_float(row.get("StopRank")) for row in rows if is_success(row)]
        ),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
    }


def interpret_policy(policy_id: str) -> str:
    if policy_id == H001_POLICY:
        return "positive_controlled_smoke_recovers_source_gap_but_source_ready_efficiency_guard_required"
    if policy_id == H001_BASE_POLICY:
        return "base_h001_v2_is_strong_but_fails_two_source_gap_episodes_across_task_contexts"
    if policy_id == H001_PREV_POLICY:
        return "previous_h001_is_weaker_than_high_path_tail_slot_policy"
    if policy_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY}:
        return "current_observation_baseline_is_source_ready_efficient_but_source_gap_brittle"
    if policy_id == SOURCE_DIVERSE_CURRENT_POLICY:
        return "current_observation_source_diverse_baseline_fails_source_gap_rows"
    if policy_id == TASK_AGNOSTIC_POLICY:
        return "task_agnostic_source_diverse_ties_base_h001_v2_and_is_a_required_baseline"
    if policy_id == STATIC_POLICY:
        return "static_stale_memory_lower_bound_fails_all_rows"
    return "requires_manual_review"


def build_policy_result_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = {str(row.get("policy_id")): row for row in policy_aggregate_rows(metric_rows)}
    out = []
    for policy_id in POLICY_ORDER:
        row = dict(aggregates.get(policy_id, {}))
        row.update(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "row_type": "policy_aggregate_interpretation",
                "interpretation": interpret_policy(policy_id),
                "supports_controlled_navigation_smoke": policy_id == H001_POLICY,
                "supports_final_real_navigation_claim": False,
            }
        )
        out.append(row)
    return out


def build_pairwise_decision_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        if row.get("method_policy_id") == H001_POLICY:
            by_baseline[str(row.get("baseline_policy_id"))].append(row)

    out = []
    for baseline_id in PAIRWISE_BASELINES:
        rows = by_baseline.get(baseline_id, [])
        delta_sr = [finite_float(row.get("delta_SR")) for row in rows]
        delta_spl = [finite_float(row.get("delta_SPL")) for row in rows]
        delta_path = [finite_float(row.get("delta_PathLengthM")) for row in rows]
        current = {
            "version": VERSION,
            "row_type": "h001_pairwise_delta_interpretation",
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
        current["supports_controlled_navigation_smoke"] = supports_pairwise_smoke(current)
        current["margin_level"] = classify_margin(current)
        current["interpretation"] = interpret_pairwise(current)
        current["supports_final_real_navigation_claim"] = False
        out.append(current)
    return out


def supports_pairwise_smoke(row: dict[str, Any]) -> bool:
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    if row["baseline_policy_id"] == STATIC_POLICY:
        return bool(delta_sr is not None and delta_sr > 0)
    return bool(delta_sr is not None and delta_spl is not None and delta_sr > 0 and delta_spl >= 0)


def classify_margin(row: dict[str, Any]) -> str:
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    if delta_sr is None or delta_spl is None:
        return "missing"
    if delta_sr <= 0 or delta_spl < 0:
        return "not_supported"
    if delta_sr >= 0.3 and delta_spl >= 0.05:
        return "strong_controlled_smoke_margin"
    if delta_sr > 0 and delta_spl >= 0:
        return "thin_spl_margin"
    return "manual_review"


def interpret_pairwise(row: dict[str, Any]) -> str:
    baseline_id = str(row["baseline_policy_id"])
    margin = str(row["margin_level"])
    if baseline_id == STATIC_POLICY:
        return "h001_high_path_rejects_static_stale_memory_lower_bound"
    if baseline_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY} and margin == "thin_spl_margin":
        return "h001_high_path_wins_sr_but_spl_margin_is_thin_and_needs_source_ready_guard"
    if baseline_id == TASK_AGNOSTIC_POLICY:
        return "h001_high_path_beats_task_agnostic_source_diverse_in_this_controlled_smoke_but_not_human_intent_main_claim"
    if baseline_id == H001_BASE_POLICY:
        return "tail_slot_policy_improves_over_base_h001_v2_by_recovering_source_gap_rows"
    if baseline_id == H001_PREV_POLICY:
        return "tail_slot_policy_improves_over_previous_h001_source_diverse_policy"
    if baseline_id == SOURCE_DIVERSE_CURRENT_POLICY:
        return "tail_slot_policy_beats_current_only_source_diverse_by_using_stale_memory_plus_current_sources"
    return "requires_manual_review"


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        grouped[(str(row.get("policy_id")), bool(row.get("diagnostic_source_gap_boundary")))].append(row)

    rows: list[dict[str, Any]] = []
    aggregate_index: dict[tuple[str, bool], dict[str, Any]] = {}
    for policy_id in POLICY_ORDER:
        for source_gap in [False, True]:
            current = aggregate(
                grouped.get((policy_id, source_gap), []),
                {
                    "version": VERSION,
                    "row_type": "policy_source_boundary_aggregate",
                    "policy_id": policy_id,
                    "diagnostic_source_gap_boundary": source_gap,
                    "source_boundary": "source_gap" if source_gap else "source_ready",
                },
            )
            current["interpretation"] = interpret_source_boundary(policy_id, source_gap, current)
            current["supports_final_real_navigation_claim"] = False
            aggregate_index[(policy_id, source_gap)] = current
            rows.append(current)

    for baseline_id in [DETECTOR_POLICY, FIXED_CURRENT_POLICY, H001_BASE_POLICY, TASK_AGNOSTIC_POLICY, SOURCE_DIVERSE_CURRENT_POLICY]:
        for source_gap in [False, True]:
            method = aggregate_index[(H001_POLICY, source_gap)]
            baseline = aggregate_index[(baseline_id, source_gap)]
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "h001_source_boundary_delta",
                    "method_policy_id": H001_POLICY,
                    "baseline_policy_id": baseline_id,
                    "diagnostic_source_gap_boundary": source_gap,
                    "source_boundary": "source_gap" if source_gap else "source_ready",
                    "rows": method["rows"],
                    "baseline_rows": baseline["rows"],
                    "delta_SR": delta(method.get("SR"), baseline.get("SR")),
                    "delta_SPL": delta(method.get("SPL"), baseline.get("SPL")),
                    "delta_PathLengthM_mean": delta(method.get("PathLengthM_mean"), baseline.get("PathLengthM_mean")),
                    "supports_source_gap_recovery": bool(
                        source_gap
                        and finite_float(method.get("SR")) is not None
                        and finite_float(baseline.get("SR")) is not None
                        and finite_float(method.get("SR")) > finite_float(baseline.get("SR"))
                    ),
                    "source_ready_efficiency_regression": bool(
                        not source_gap
                        and baseline_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY}
                        and finite_float(method.get("SPL")) is not None
                        and finite_float(baseline.get("SPL")) is not None
                        and finite_float(method.get("SPL")) < finite_float(baseline.get("SPL"))
                    ),
                    "supports_final_real_navigation_claim": False,
                }
            )
    return rows


def interpret_source_boundary(policy_id: str, source_gap: bool, row: dict[str, Any]) -> str:
    if policy_id == H001_POLICY and source_gap:
        return "h001_high_path_recovers_all_source_gap_rows_in_m61"
    if policy_id == H001_POLICY and not source_gap:
        return "h001_high_path_keeps_source_ready_success_but_is_less_spl_efficient_than_detector_topk"
    if policy_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY} and source_gap:
        return "current_observation_policy_has_no_source_gap_recovery"
    if policy_id in {DETECTOR_POLICY, FIXED_CURRENT_POLICY} and not source_gap:
        return "current_observation_policy_is_strong_source_ready_efficiency_baseline"
    if policy_id == STATIC_POLICY:
        return "static_stale_memory_fails_boundary_subset"
    return "source_boundary_context_for_scale_decision"


def build_task_context_effect_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        grouped[(str(row.get("task_context_id")), str(row.get("policy_id")))].append(row)

    contexts = sorted({str(row.get("task_context_id")) for row in scan_rows})
    out: list[dict[str, Any]] = []
    for context_id in contexts:
        policy_stats = {
            policy_id: aggregate(
                grouped.get((context_id, policy_id), []),
                {"task_context_id": context_id, "policy_id": policy_id},
            )
            for policy_id in [H001_POLICY, H001_BASE_POLICY, TASK_AGNOSTIC_POLICY, DETECTOR_POLICY, STATIC_POLICY]
        }
        h001 = policy_stats[H001_POLICY]
        task_agnostic = policy_stats[TASK_AGNOSTIC_POLICY]
        detector = policy_stats[DETECTOR_POLICY]
        base = policy_stats[H001_BASE_POLICY]
        out.append(
            {
                "version": VERSION,
                "row_type": "task_context_policy_delta",
                "task_context_id": context_id,
                "rows": h001["rows"],
                "h001_SR": h001.get("SR"),
                "h001_SPL": h001.get("SPL"),
                "base_h001_SR": base.get("SR"),
                "base_h001_SPL": base.get("SPL"),
                "task_agnostic_SR": task_agnostic.get("SR"),
                "task_agnostic_SPL": task_agnostic.get("SPL"),
                "detector_SR": detector.get("SR"),
                "detector_SPL": detector.get("SPL"),
                "h001_minus_task_agnostic_SR": delta(h001.get("SR"), task_agnostic.get("SR")),
                "h001_minus_task_agnostic_SPL": delta(h001.get("SPL"), task_agnostic.get("SPL")),
                "h001_minus_detector_SR": delta(h001.get("SR"), detector.get("SR")),
                "h001_minus_detector_SPL": delta(h001.get("SPL"), detector.get("SPL")),
                "supports_conditioned_memory_trust_smoke": bool(
                    finite_float(delta(h001.get("SR"), task_agnostic.get("SR"))) is not None
                    and finite_float(delta(h001.get("SR"), task_agnostic.get("SR"))) > 0
                ),
                "supports_human_intent_main_claim": False,
                "human_intent_boundary": "structured_task_context_conditions_memory_trust_only_not_natural_language_intent_understanding",
            }
        )
    return out


def build_scale_gate_rows(
    coverage_m61: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy = {str(row["policy_id"]): row for row in policy_rows}

    def p(policy_id: str, metric: str) -> float | None:
        return finite_float(policy.get(policy_id, {}).get(metric))

    source_delta_rows = [row for row in source_rows if row.get("row_type") == "h001_source_boundary_delta"]
    source_gap_deltas = [row for row in source_delta_rows if row.get("diagnostic_source_gap_boundary") is True]
    source_ready_detector_regression = any(
        row.get("source_ready_efficiency_regression") for row in source_delta_rows
    )
    pairwise_by_base = {str(row["baseline_policy_id"]): row for row in pairwise_rows}

    gates = [
        gate(
            "m61_input_ready",
            "pass"
            if coverage_m61.get("status") == "e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready"
            else "fail",
            "M61 trajectory artifact is available and marked ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(coverage_m61.get("leakage_audit_pass")) else "fail",
            "Policy rows do not use ObjectNav goal/viewpoints before metric-time evaluation.",
            blocks_final=True,
        ),
        gate(
            "controlled_smoke_rows_present",
            "pass" if int(coverage_m61.get("scan_task_policy_rows", 0)) == 144 else "fail",
            "M61 has 144 scan-task-policy rows over 8 policies and 18 scan-task contexts.",
            blocks_final=True,
        ),
        gate(
            "beats_static_stale_memory",
            "pass" if (p(H001_POLICY, "SR") or 0.0) > (p(STATIC_POLICY, "SR") or 0.0) else "fail",
            "H001 high-path rejects the static stale-memory lower bound.",
            blocks_final=True,
        ),
        gate(
            "beats_base_h001_v2_full_aggregate",
            "pass"
            if (p(H001_POLICY, "SR") or 0.0) > (p(H001_BASE_POLICY, "SR") or 0.0)
            and (p(H001_POLICY, "SPL") or 0.0) > (p(H001_BASE_POLICY, "SPL") or 0.0)
            else "fail",
            "Tail-slot policy improves over base H001 v2 on full aggregate SR and SPL.",
            blocks_final=True,
        ),
        gate(
            "beats_task_agnostic_full_aggregate",
            "pass"
            if (p(H001_POLICY, "SR") or 0.0) > (p(TASK_AGNOSTIC_POLICY, "SR") or 0.0)
            and (p(H001_POLICY, "SPL") or 0.0) > (p(TASK_AGNOSTIC_POLICY, "SPL") or 0.0)
            else "fail",
            "H001 high-path beats task-agnostic source-diverse in this controlled smoke.",
            blocks_final=True,
        ),
        gate(
            "beats_detector_full_aggregate",
            "pass"
            if (p(H001_POLICY, "SR") or 0.0) > (p(DETECTOR_POLICY, "SR") or 0.0)
            and (p(H001_POLICY, "SPL") or 0.0) > (p(DETECTOR_POLICY, "SPL") or 0.0)
            else "fail",
            "H001 high-path beats detector-confidence top-5 on full aggregate, with a thin SPL margin.",
            blocks_final=True,
        ),
        gate(
            "source_gap_recovery_supported",
            "pass" if all(bool(row.get("supports_source_gap_recovery")) for row in source_gap_deltas) else "fail",
            "H001 high-path recovers source-gap rows that current-only policies miss.",
            blocks_final=True,
        ),
        gate(
            "source_ready_efficiency_guard",
            "warning" if source_ready_detector_regression else "pass",
            "H001 high-path is less SPL-efficient than detector/fixed on source-ready rows; M63 must keep a source-ready no-regression guard.",
            blocks_final=True,
        ),
        gate(
            "denominator_scale_sufficient",
            "fail",
            "M61 has only 18 scan-task contexts over 2 scenes; this is not enough for a final navigation claim.",
            blocks_final=True,
        ),
        gate(
            "heldout_transfer_ready",
            "fail",
            "No heldout scene/category transfer table exists for the high-path policy yet.",
            blocks_final=True,
        ),
        gate(
            "stronger_navigation_search_baselines_ready",
            "fail",
            "VLFM, HM3D-OVON, GOAT-Bench style modular baselines are not integrated.",
            blocks_final=True,
        ),
        gate(
            "final_real_rgbd_open_vocab_robustness_ready",
            "fail",
            "M61 uses the staged rendered RGB-D proposal bridge but is not a final robustness study.",
            blocks_final=True,
        ),
        gate(
            "human_intent_main_claim_ready",
            "fail",
            "Structured task context conditions memory trust; it does not yet demonstrate natural-language human intent understanding.",
            blocks_final=True,
        ),
        gate(
            "diagnostic_navigation_table_ready",
            "pass" if pairwise_by_base.get(DETECTOR_POLICY, {}).get("supports_controlled_navigation_smoke") else "fail",
            "A diagnostic paper-facing navigation smoke table is defensible with explicit boundaries.",
            blocks_final=False,
        ),
        gate(
            "scale_up_contract_ready",
            "pass",
            "Next step should scale the controlled result with source-boundary guards and stronger baselines.",
            blocks_final=False,
        ),
    ]
    return gates


def gate(gate_id: str, status: str, rationale: str, *, blocks_final: bool) -> dict[str, Any]:
    return {
        "version": VERSION,
        "gate_id": gate_id,
        "gate_status": status,
        "rationale": rationale,
        "blocks_diagnostic_table": False if status in {"pass", "warning"} else gate_id in {"m61_input_ready", "leakage_audit_pass"},
        "blocks_final_real_navigation_claim": blocks_final and status in {"fail", "warning"},
    }


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim("controlled_high_path_tail_slot_trajectory_smoke", True, "M61 executes H001 high-path tail-slot rows in Habitat and M62 verifies aggregate/source-boundary gains."),
        claim("source_gap_recovery_smoke", True, "H001 high-path recovers source-gap rows in the 18-context controlled smoke."),
        claim("diagnostic_navigation_table", True, "A bounded diagnostic table is usable if marked as small-scale controlled evidence."),
        claim("final_real_navigation_sr_spl", False, "Needs scale-up, heldout transfer, and stronger navigation/search baselines."),
        claim("final_real_rgbd_open_vocab_robustness", False, "Needs detector/proposal robustness and external open-vocabulary mapping baselines beyond current smoke."),
        claim("deployable_search_policy", False, "Needs broader scenes, failure recovery behavior, compute budget, and non-oracle deployment protocol."),
        claim("human_intent_main_claim", False, "Current evidence supports structured task context as memory-trust condition only."),
        claim("generality_across_scenes_categories", False, "Two scenes and limited object categories are insufficient for generality."),
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
            "is_this_final_navigation",
            "No. M62 treats M61 as controlled trajectory smoke; final claim needs M63 scale contract, heldout transfer, and external baselines.",
        ),
        defense(
            "is_high_path_tail_slot_leaking_goal",
            "No. M61 leakage audit passes; ObjectNav goal/viewpoints are metric-only after stops, not policy inputs.",
        ),
        defense(
            "why_not_detector_confidence_only",
            "Detector/fixed policies are efficient on source-ready rows but have zero source-gap recovery in M61.",
        ),
        defense(
            "why_not_task_agnostic_memory_trust",
            "Task-agnostic source-diverse ties base H001 v2 but misses the recovered source-gap rows surfaced by the high-path tail slot.",
        ),
        defense(
            "h001_source_ready_spl_regression",
            "Valid attack. H001 high-path loses source-ready SPL to detector/fixed; next scale contract must report source-ready and source-gap separately and include a no-regression guard.",
        ),
        defense(
            "is_human_intent_the_main_claim",
            "No. Human/task context remains a structured condition for memory trust and re-observation, not the main natural-language intent contribution.",
        ),
        defense(
            "is_the_sample_large_enough",
            "No. The result has 18 scan-task contexts over 2 scenes; it is a positive smoke result, not a benchmark-scale result.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_route_decision_rows(scale_gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostic_ready = not any(row.get("blocks_diagnostic_table") for row in scale_gates)
    return [
        {
            "version": VERSION,
            "route_id": "paper_diagnostic_navigation_table_v0",
            "selected": diagnostic_ready,
            "rationale": "Use M61/M62 as bounded diagnostic evidence with explicit small-scale and source-boundary caveats.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "scale_up_contract_with_source_boundary_guard",
            "selected": diagnostic_ready,
            "rationale": "Scale only after fixing source-ready no-regression reporting, heldout split, and stronger baseline plan.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_now",
            "selected": False,
            "rationale": "Blocked by scale, heldout transfer, external baseline, and source-ready efficiency gates.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "repair_policy_before_any_scale",
            "selected": False,
            "rationale": "M61 is positive enough to scale, but M63 must preserve source-ready efficiency as a guardrail.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
    ]


def report_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            cells.append(fmt(value) if isinstance(value, float) else str(value))
        body.append("| " + " | ".join(cells) + " |")
    return [header, sep, *body]


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    scale_gates: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    source_aggregates = [
        row
        for row in source_rows
        if row.get("row_type") == "policy_source_boundary_aggregate"
        and row.get("policy_id") in {H001_POLICY, DETECTOR_POLICY, H001_BASE_POLICY, TASK_AGNOSTIC_POLICY, STATIC_POLICY}
    ]
    lines = [
        "# E008-M62 High-Path Tail-Slot Result Interpretation and Scale Decision",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M61 status: `{coverage['m61_status']}`.",
        f"- M61 scan-task-policy rows: {coverage['m61_scan_task_policy_rows']}.",
        f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
        f"- H001 high-path `SR` / `SPL`: {fmt(coverage['h001_SR'])} / {fmt(coverage['h001_SPL'])}.",
        f"- Detector `SR` / `SPL`: {fmt(coverage['detector_SR'])} / {fmt(coverage['detector_SPL'])}.",
        f"- Task-agnostic `SR` / `SPL`: {fmt(coverage['task_agnostic_SR'])} / {fmt(coverage['task_agnostic_SPL'])}.",
        f"- Source-ready efficiency warning: {coverage['source_ready_efficiency_warning']}.",
        f"- Final real navigation `SR` / `SPL` ready: {coverage['final_real_navigation_sr_spl_ready']}.",
        "",
        "## Policy Aggregates",
        "",
        *report_table(
            policy_rows,
            [
                "policy_id",
                "success_rows",
                "scan_task_policy_rows",
                "SR",
                "SPL",
                "PathLengthM_mean",
                "CandidateVisits_mean",
            ],
        ),
        "",
        "## H001 Pairwise Deltas",
        "",
        *report_table(
            pairwise_rows,
            ["baseline_policy_id", "rows", "delta_SR_mean", "delta_SPL_mean", "delta_PathLengthM_mean", "margin_level"],
        ),
        "",
        "## Source Boundary",
        "",
        *report_table(
            source_aggregates,
            ["policy_id", "source_boundary", "success_rows", "rows", "SR", "SPL", "PathLengthM_mean"],
        ),
        "",
        "## Scale Gates",
        "",
        *report_table(scale_gates, ["gate_id", "gate_status", "blocks_final_real_navigation_claim"]),
        "",
        "## Decision",
        "",
    ]
    for row in route_rows:
        lines.append(f"- `{row['route_id']}` selected={row['selected']}: {row['rationale']}")
    lines.extend(
        [
            "",
            "M62 promotes M61 only to a bounded diagnostic navigation table and a scale-up contract. It does not promote final real navigation, final RGB-D/open-vocabulary robustness, deployable search policy, or human-intent main claims.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    coverage_m61 = read_json(M61_DIR / "coverage.json")
    metric_rows = read_jsonl(M61_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_input_rows = read_jsonl(M61_DIR / "pairwise_policy_delta_rows.jsonl")
    leakage_rows = read_jsonl(M61_DIR / "leakage_audit_rows.jsonl")
    scan_rows = scan_task_rows(metric_rows)

    missing_inputs = [
        str(path)
        for path in [
            M61_DIR / "coverage.json",
            M61_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
            M61_DIR / "pairwise_policy_delta_rows.jsonl",
            M61_DIR / "leakage_audit_rows.jsonl",
        ]
        if not path.exists()
    ]

    policy_rows = build_policy_result_rows(metric_rows)
    source_rows = build_source_boundary_rows(scan_rows)
    task_context_rows = build_task_context_effect_rows(scan_rows)
    pairwise_rows = build_pairwise_decision_rows(pairwise_input_rows)
    scale_gates = build_scale_gate_rows(coverage_m61, policy_rows, source_rows, pairwise_rows)
    claim_rows = build_claim_boundary_rows()
    defense_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows(scale_gates)

    policy_by_id = {str(row.get("policy_id")): row for row in policy_rows}
    source_ready_detector_regression = any(
        row.get("source_ready_efficiency_regression")
        for row in source_rows
        if row.get("row_type") == "h001_source_boundary_delta"
    )
    source_gap_all_recovered = all(
        row.get("supports_source_gap_recovery")
        for row in source_rows
        if row.get("row_type") == "h001_source_boundary_delta"
        and row.get("diagnostic_source_gap_boundary") is True
    )
    input_ready = not missing_inputs and coverage_m61.get("status") == "e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready"
    leakage_pass = bool(coverage_m61.get("leakage_audit_pass")) and all(
        bool(row.get("leakage_audit_pass")) for row in leakage_rows
    )
    status = READY_STATUS if input_ready and leakage_pass else BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m61_status": coverage_m61.get("status"),
        "missing_inputs": missing_inputs,
        "m61_scan_task_policy_rows": coverage_m61.get("scan_task_policy_rows"),
        "m61_policy_count": coverage_m61.get("policy_count"),
        "m61_scene_count": coverage_m61.get("scene_count"),
        "m61_trajectory_attempt_rows": coverage_m61.get("trajectory_attempt_rows"),
        "leakage_audit_pass": leakage_pass,
        "policy_result_rows": len(policy_rows),
        "source_boundary_rows": len(source_rows),
        "task_context_effect_rows": len(task_context_rows),
        "pairwise_decision_rows": len(pairwise_rows),
        "scale_gate_rows": len(scale_gates),
        "scale_gate_pass_rows": sum(1 for row in scale_gates if row["gate_status"] == "pass"),
        "scale_gate_warning_rows": sum(1 for row in scale_gates if row["gate_status"] == "warning"),
        "scale_gate_fail_rows": sum(1 for row in scale_gates if row["gate_status"] == "fail"),
        "h001_policy_id": H001_POLICY,
        "h001_SR": policy_by_id.get(H001_POLICY, {}).get("SR"),
        "h001_SPL": policy_by_id.get(H001_POLICY, {}).get("SPL"),
        "detector_SR": policy_by_id.get(DETECTOR_POLICY, {}).get("SR"),
        "detector_SPL": policy_by_id.get(DETECTOR_POLICY, {}).get("SPL"),
        "task_agnostic_SR": policy_by_id.get(TASK_AGNOSTIC_POLICY, {}).get("SR"),
        "task_agnostic_SPL": policy_by_id.get(TASK_AGNOSTIC_POLICY, {}).get("SPL"),
        "base_h001_SR": policy_by_id.get(H001_BASE_POLICY, {}).get("SR"),
        "base_h001_SPL": policy_by_id.get(H001_BASE_POLICY, {}).get("SPL"),
        "positive_controlled_smoke_ready": status == READY_STATUS and bool(policy_by_id.get(H001_POLICY, {}).get("supports_controlled_navigation_smoke")),
        "source_gap_recovery_supported": source_gap_all_recovered,
        "source_ready_efficiency_warning": source_ready_detector_regression,
        "diagnostic_navigation_table_ready": status == READY_STATUS and not any(row.get("blocks_diagnostic_table") for row in scale_gates),
        "scale_up_contract_ready": status == READY_STATUS,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else None,
        "launch_long_job_now": False,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_decision_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "task_context_effect_rows.jsonl", task_context_rows)
    write_jsonl(ARTIFACT_DIR / "scale_gate_rows.jsonl", scale_gates)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", defense_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_csv(
        ARTIFACT_DIR / "paper_navigation_table_rows.csv",
        policy_rows,
        [
            "policy_id",
            "success_rows",
            "scan_task_policy_rows",
            "SR",
            "SPL",
            "PathLengthM_mean",
            "CandidateVisits_mean",
            "OldLocationDeadEndCostM_mean",
            "interpretation",
        ],
    )
    write_report(coverage, policy_rows, source_rows, pairwise_rows, scale_gates, route_rows)

    for filename in [
        "coverage.json",
        "policy_result_rows.jsonl",
        "pairwise_decision_rows.jsonl",
        "source_boundary_rows.jsonl",
        "task_context_effect_rows.jsonl",
        "scale_gate_rows.jsonl",
        "claim_boundary_rows.jsonl",
        "reviewer_defense_rows.jsonl",
        "route_decision_rows.jsonl",
        "paper_navigation_table_rows.csv",
        "report.md",
    ]:
        shutil.copy2(ARTIFACT_DIR / filename, DATA_OUT_DIR / filename)

    print(json.dumps({"status": status, "selected_next_unit": coverage["selected_next_unit"]}, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
