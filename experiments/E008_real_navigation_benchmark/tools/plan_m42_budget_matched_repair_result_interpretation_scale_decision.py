#!/usr/bin/env python3
"""Interpret M41 budget-matched repair results and decide whether to scale."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0"
)
M41_DIR = EXP_ROOT / "artifacts" / "E008-M41_budget_matched_repair_trajectory_execution_smoke_v0"

VERSION = "e008_m42_budget_matched_repair_result_interpretation_scale_decision_v0"
STATUS = "e008_m42_budget_matched_repair_result_interpretation_scale_decision_ready"
NEXT_UNIT = "E008-M43 dynamic-stale navigation policy redesign contract"

H001_POLICY = "h001_dead_end_penalized_budget5_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_TOPK_POLICY = "fixed_topk_current_observation_budget5_v0"
STATIC_POLICY = "static_stale_memory_top1_v0"
TASK_AGNOSTIC_POLICY = "task_agnostic_dead_end_penalized_budget5_v0"

POLICY_ORDER = [
    DETECTOR_POLICY,
    FIXED_TOPK_POLICY,
    H001_POLICY,
    STATIC_POLICY,
    TASK_AGNOSTIC_POLICY,
]


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
    except (TypeError, ValueError):
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


def scan_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def policy_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def index_policy_aggregates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in policy_aggregate_rows(rows)}


def aggregate_rows(rows: list[dict[str, Any]], group: dict[str, Any]) -> dict[str, Any]:
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
    scan_rows = scan_task_rows(all_rows)
    out = []
    for policy_id in POLICY_ORDER:
        aggregate = dict(aggregates.get(policy_id, {}))
        rows = [row for row in scan_rows if row.get("policy_id") == policy_id]
        interpretation = interpret_policy(policy_id, aggregate)
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_task_policy_rows": aggregate.get("scan_task_policy_rows", len(rows)),
                "success_rows": aggregate.get("success_rows"),
                "SR": aggregate.get("SR"),
                "SPL": aggregate.get("SPL"),
                "PathLengthM_mean": aggregate.get("PathLengthM_mean"),
                "CandidateVisits_mean": aggregate.get("CandidateVisits_mean"),
                "OldLocationDeadEndCostM_mean": aggregate.get("OldLocationDeadEndCostM_mean"),
                "stale_visit_first_rows": sum(1 for row in rows if bool(row.get("stale_visit_first"))),
                "current_observation_first_rows": sum(1 for row in rows if bool(row.get("current_observation_first"))),
                "interpretation": interpretation,
                "claim_ready": policy_claim_ready(policy_id, aggregate),
            }
        )
    return out


def interpret_policy(policy_id: str, row: dict[str, Any]) -> str:
    sr = finite_float(row.get("SR"))
    spl = finite_float(row.get("SPL"))
    if policy_id == STATIC_POLICY:
        return "static_stale_memory_lower_bound_fails_all_rows"
    if policy_id == H001_POLICY and sr == 0.5 and spl is not None:
        return "h001_recovers_static_failures_but_ties_current_and_task_agnostic_sr_spl"
    if policy_id == DETECTOR_POLICY:
        return "detector_confidence_current_observation_matches_h001_success_and_spl"
    if policy_id == FIXED_TOPK_POLICY:
        return "fixed_current_topk_matches_h001_success_and_spl"
    if policy_id == TASK_AGNOSTIC_POLICY:
        return "task_agnostic_dead_end_penalty_matches_h001_success_and_spl"
    return "requires_manual_review"


def policy_claim_ready(policy_id: str, row: dict[str, Any]) -> bool:
    sr = finite_float(row.get("SR"))
    if policy_id == H001_POLICY:
        return bool(sr is not None and sr > 0)
    if policy_id == STATIC_POLICY:
        return False
    return bool(sr is not None and sr >= 0)


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for boundary_value, boundary_name in [(False, "source_ready"), (True, "source_gap")]:
        boundary_rows = [row for row in scan_rows if bool(row.get("diagnostic_source_gap_boundary")) is boundary_value]
        for policy_id in POLICY_ORDER:
            rows = [row for row in boundary_rows if row.get("policy_id") == policy_id]
            aggregate = aggregate_rows(
                rows,
                {
                    "version": VERSION,
                    "boundary": boundary_name,
                    "diagnostic_source_gap_boundary": boundary_value,
                    "policy_id": policy_id,
                },
            )
            aggregate["interpretation"] = interpret_boundary(policy_id, boundary_name, aggregate)
            out.append(aggregate)
    return out


def interpret_boundary(policy_id: str, boundary_name: str, row: dict[str, Any]) -> str:
    sr = finite_float(row.get("SR"))
    if boundary_name == "source_ready":
        if policy_id in {H001_POLICY, DETECTOR_POLICY, FIXED_TOPK_POLICY, TASK_AGNOSTIC_POLICY} and sr == 1.0:
            return "all_current_evidence_policies_succeed;_h001_not_distinct"
        if policy_id == STATIC_POLICY and sr == 0.0:
            return "static_stale_memory_fails_even_when_current_source_exists"
    if boundary_name == "source_gap":
        if sr == 0.0:
            return "source_gap_unsolved_by_ranking_or_dead_end_penalty"
    return "requires_manual_review"


def build_pairwise_decision_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_baseline[str(row.get("baseline_policy_id"))].append(row)

    out = []
    for baseline_id in [STATIC_POLICY, DETECTOR_POLICY, FIXED_TOPK_POLICY, TASK_AGNOSTIC_POLICY]:
        rows = by_baseline.get(baseline_id, [])
        delta_sr = [finite_float(row.get("delta_SR")) for row in rows]
        delta_spl = [finite_float(row.get("delta_SPL")) for row in rows]
        delta_path = [finite_float(row.get("delta_PathLengthM")) for row in rows]
        delta_old_cost = [finite_float(row.get("method_OldLocationDeadEndCostM")) - finite_float(row.get("baseline_OldLocationDeadEndCostM")) for row in rows]
        row = {
            "version": VERSION,
            "method_policy_id": H001_POLICY,
            "baseline_policy_id": baseline_id,
            "rows": len(rows),
            "delta_SR_mean": mean(delta_sr),
            "delta_SPL_mean": mean(delta_spl),
            "delta_PathLengthM_mean": mean(delta_path),
            "delta_OldLocationDeadEndCostM_mean": mean(delta_old_cost),
            "sr_win_rows": sum(1 for value in delta_sr if value is not None and value > 0),
            "sr_tie_rows": sum(1 for value in delta_sr if value == 0),
            "sr_loss_rows": sum(1 for value in delta_sr if value is not None and value < 0),
            "spl_win_rows": sum(1 for value in delta_spl if value is not None and value > 0),
            "spl_tie_rows": sum(1 for value in delta_spl if value == 0),
            "spl_loss_rows": sum(1 for value in delta_spl if value is not None and value < 0),
        }
        row["interpretation"] = interpret_pairwise(row)
        row["supports_navigation_improvement_claim"] = supports_navigation_improvement(row)
        out.append(row)
    return out


def interpret_pairwise(row: dict[str, Any]) -> str:
    baseline_id = row["baseline_policy_id"]
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    delta_path = finite_float(row.get("delta_PathLengthM_mean"))
    if baseline_id == STATIC_POLICY and delta_sr is not None and delta_sr > 0:
        return "h001_beats_static_stale_memory_lower_bound_only"
    if baseline_id in {DETECTOR_POLICY, FIXED_TOPK_POLICY} and delta_sr == 0 and delta_spl == 0:
        return "h001_ties_current_observation_baseline_on_sr_spl"
    if baseline_id == TASK_AGNOSTIC_POLICY and delta_sr == 0 and delta_spl == 0:
        return "task_context_main_effect_not_supported"
    if delta_path is not None and delta_path < 0:
        return "efficiency_gain_without_sr_spl_gain;_insufficient_for_main_claim"
    return "requires_manual_review"


def supports_navigation_improvement(row: dict[str, Any]) -> bool:
    baseline_id = row["baseline_policy_id"]
    delta_sr = finite_float(row.get("delta_SR_mean"))
    delta_spl = finite_float(row.get("delta_SPL_mean"))
    if baseline_id == STATIC_POLICY:
        return bool(delta_sr is not None and delta_sr > 0)
    return bool(delta_sr is not None and delta_spl is not None and delta_sr > 0 and delta_spl >= 0)


def build_task_context_effect_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_context: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in scan_rows:
        by_context[str(row.get("task_context_id"))][str(row.get("policy_id"))].append(row)

    out = []
    for context_id in sorted(by_context):
        h001 = aggregate_rows(
            by_context[context_id].get(H001_POLICY, []),
            {"version": VERSION, "task_context_id": context_id, "policy_id": H001_POLICY},
        )
        task_agnostic = aggregate_rows(
            by_context[context_id].get(TASK_AGNOSTIC_POLICY, []),
            {"version": VERSION, "task_context_id": context_id, "policy_id": TASK_AGNOSTIC_POLICY},
        )
        fixed = aggregate_rows(
            by_context[context_id].get(FIXED_TOPK_POLICY, []),
            {"version": VERSION, "task_context_id": context_id, "policy_id": FIXED_TOPK_POLICY},
        )
        out.append(
            {
                "version": VERSION,
                "task_context_id": context_id,
                "h001_rows": h001["rows"],
                "h001_SR": h001["SR"],
                "h001_SPL": h001["SPL"],
                "h001_PathLengthM_mean": h001["PathLengthM_mean"],
                "h001_OldLocationDeadEndCostM_mean": h001["OldLocationDeadEndCostM_mean"],
                "task_agnostic_SR": task_agnostic["SR"],
                "task_agnostic_SPL": task_agnostic["SPL"],
                "fixed_topk_SR": fixed["SR"],
                "fixed_topk_SPL": fixed["SPL"],
                "h001_minus_task_agnostic_SR": nullable_sub(h001["SR"], task_agnostic["SR"]),
                "h001_minus_task_agnostic_SPL": nullable_sub(h001["SPL"], task_agnostic["SPL"]),
                "h001_minus_fixed_topk_SR": nullable_sub(h001["SR"], fixed["SR"]),
                "h001_minus_fixed_topk_SPL": nullable_sub(h001["SPL"], fixed["SPL"]),
                "interpretation": interpret_task_context(h001, task_agnostic, fixed),
                "supports_human_intent_main_claim": False,
            }
        )
    return out


def nullable_sub(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def interpret_task_context(h001: dict[str, Any], task_agnostic: dict[str, Any], fixed: dict[str, Any]) -> str:
    if nullable_sub(h001["SR"], task_agnostic["SR"]) == 0 and nullable_sub(h001["SPL"], task_agnostic["SPL"]) == 0:
        return "structured_task_context_does_not_improve_sr_spl_over_task_agnostic_in_m41"
    if nullable_sub(h001["SR"], fixed["SR"]) == 0 and nullable_sub(h001["SPL"], fixed["SPL"]) == 0:
        return "task_context_collapses_to_current_observation_baseline_in_m41"
    return "requires_manual_review"


def build_scale_gate_rows(
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    h001 = next(row for row in policy_rows if row["policy_id"] == H001_POLICY)
    detector_pair = next(row for row in pairwise_rows if row["baseline_policy_id"] == DETECTOR_POLICY)
    fixed_pair = next(row for row in pairwise_rows if row["baseline_policy_id"] == FIXED_TOPK_POLICY)
    task_pair = next(row for row in pairwise_rows if row["baseline_policy_id"] == TASK_AGNOSTIC_POLICY)
    source_gap_h001 = next(
        row for row in source_rows if row["policy_id"] == H001_POLICY and row["boundary"] == "source_gap"
    )
    source_ready_h001 = next(
        row for row in source_rows if row["policy_id"] == H001_POLICY and row["boundary"] == "source_ready"
    )
    task_context_ready = any(bool(row.get("supports_human_intent_main_claim")) for row in task_rows)

    gates = [
        {
            "version": VERSION,
            "gate_id": "beats_static_stale_memory",
            "passed": finite_float(h001.get("SR")) is not None and finite_float(h001.get("SR")) > 0,
            "evidence": "H001 has positive SR while static stale memory has SR 0.",
            "implication": "lower_bound_recovery_only",
        },
        {
            "version": VERSION,
            "gate_id": "beats_detector_confidence_budget_matched",
            "passed": bool(detector_pair.get("supports_navigation_improvement_claim")),
            "evidence": f"delta SR {fmt(detector_pair.get('delta_SR_mean'))}, delta SPL {fmt(detector_pair.get('delta_SPL_mean'))}.",
            "implication": "required_for_navigation_improvement_claim",
        },
        {
            "version": VERSION,
            "gate_id": "beats_fixed_current_topk_budget_matched",
            "passed": bool(fixed_pair.get("supports_navigation_improvement_claim")),
            "evidence": f"delta SR {fmt(fixed_pair.get('delta_SR_mean'))}, delta SPL {fmt(fixed_pair.get('delta_SPL_mean'))}.",
            "implication": "required_to_show_not_just_current_observation_cap",
        },
        {
            "version": VERSION,
            "gate_id": "beats_task_agnostic_memory_trust",
            "passed": bool(task_pair.get("supports_navigation_improvement_claim")),
            "evidence": f"delta SR {fmt(task_pair.get('delta_SR_mean'))}, delta SPL {fmt(task_pair.get('delta_SPL_mean'))}.",
            "implication": "required_for_task_conditioning_claim",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_solved",
            "passed": finite_float(source_gap_h001.get("SR")) is not None and finite_float(source_gap_h001.get("SR")) > 0,
            "evidence": f"source-gap H001 SR {fmt(source_gap_h001.get('SR'))}; source-ready H001 SR {fmt(source_ready_h001.get('SR'))}.",
            "implication": "ranking_only_policy_cannot_be_scaled_as_source_recovery_claim",
        },
        {
            "version": VERSION,
            "gate_id": "task_context_main_effect",
            "passed": task_context_ready,
            "evidence": "No task context group improves over task-agnostic SR/SPL.",
            "implication": "human_intent_remains_conditioning_variable_not_main_contribution",
        },
    ]
    return gates


def build_claim_boundary_rows(scale_gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_pass = {row["gate_id"]: bool(row["passed"]) for row in scale_gate_rows}
    return [
        {
            "version": VERSION,
            "claim_id": "budget_matched_repair_smoke_result",
            "supported": True,
            "claim_boundary": "M41 is a Docker Habitat smoke test over 90 scan-task-policy rows; M42 interprets it as source-ready repair evidence only.",
        },
        {
            "version": VERSION,
            "claim_id": "static_stale_memory_lower_bound_failure",
            "supported": gate_pass["beats_static_stale_memory"],
            "claim_boundary": "Static stale memory is a weak lower bound and fails all M41 rows.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_navigation_improvement_over_current_observation",
            "supported": False,
            "claim_boundary": "H001 ties detector confidence and fixed current top-k on SR/SPL; do not claim navigation improvement over current observation.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_or_human_intent_main_effect",
            "supported": False,
            "claim_boundary": "H001 does not beat task-agnostic dead-end penalty on SR/SPL; structured task context remains a conditioning variable.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_recovery",
            "supported": False,
            "claim_boundary": "Source-gap rows remain unsolved by budget-matched ranking/penalty; they require candidate-source expansion or source repair.",
        },
        {
            "version": VERSION,
            "claim_id": "scale_to_full_navigation_benchmark_now",
            "supported": False,
            "claim_boundary": "Scale-up is blocked until H001 beats detector/fixed/task-agnostic under a budget-matched protocol or the method is redesigned.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M42 does not support final real navigation SR/SPL; it only selects the next redesign route.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack_id": "h001_only_beats_static_lower_bound",
            "risk": "A reviewer can argue the positive result is only against a deliberately weak static stale-memory baseline.",
            "defense_or_fix": "Keep the static result as failure diagnosis, not as the main novelty evidence; require detector/fixed/task-agnostic deltas before scale.",
        },
        {
            "version": VERSION,
            "attack_id": "task_context_not_causal",
            "risk": "H001 and task-agnostic policies have identical SR/SPL in M41.",
            "defense_or_fix": "Do not claim human intent as a main contribution; redesign should create task-dependent decisions that change visit order or source expansion.",
        },
        {
            "version": VERSION,
            "attack_id": "source_gap_confounds_policy",
            "risk": "Half of the denominator is source-gap; ranking cannot succeed when no candidate source covers the target.",
            "defense_or_fix": "Separate source-ready and source-gap rows; add candidate-source expansion before any final navigation claim.",
        },
        {
            "version": VERSION,
            "attack_id": "efficiency_metric_not_primary",
            "risk": "Small path-length differences without SR/SPL gain are not enough for top-tier navigation novelty.",
            "defense_or_fix": "Use path/search cost as an auxiliary metric unless the redesign yields consistent budget-matched SR/SPL or ExpectedSearchCost gains.",
        },
    ]


def build_route_decision_rows(scale_gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed_required = [
        row["gate_id"]
        for row in scale_gate_rows
        if not row["passed"] and row["gate_id"] != "beats_static_stale_memory"
    ]
    return [
        {
            "version": VERSION,
            "route_id": "scale_full_navigation_benchmark_now",
            "selected": False,
            "reason": "Required budget-matched current-observation and task-agnostic gates failed.",
            "failed_required_gates": failed_required,
        },
        {
            "version": VERSION,
            "route_id": "policy_redesign_before_scale",
            "selected": True,
            "reason": "H001 needs a source-expansion or task-dependent re-observation decision before scale.",
            "selected_next_unit": NEXT_UNIT,
        },
    ]


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M42 Budget-Matched Repair Result Interpretation",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- M41 status: `{coverage['m41_status']}`",
        f"- Scale-up recommended now: `{str(coverage['scale_up_recommended_now']).lower()}`",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Final real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        "",
        "## Policy Result",
        "",
        "| Policy | SR | SPL | PathLengthM | OldDeadEndM | Interpretation |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in policy_rows:
        lines.append(
            "| "
            f"`{row['policy_id']}` | {fmt(row.get('SR'))} | {fmt(row.get('SPL'))} | "
            f"{fmt(row.get('PathLengthM_mean'))} | {fmt(row.get('OldLocationDeadEndCostM_mean'))} | "
            f"{row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Source Boundary",
            "",
            "| Boundary | Policy | Rows | SR | SPL | Interpretation |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in source_rows:
        lines.append(
            "| "
            f"`{row['boundary']}` | `{row['policy_id']}` | {row['rows']} | {fmt(row.get('SR'))} | "
            f"{fmt(row.get('SPL'))} | {row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Decision",
            "",
            "| Baseline | Delta SR | Delta SPL | Supports Improvement | Interpretation |",
            "|---|---:|---:|---|---|",
        ]
    )
    for row in pairwise_rows:
        lines.append(
            "| "
            f"`{row['baseline_policy_id']}` | {fmt(row.get('delta_SR_mean'))} | "
            f"{fmt(row.get('delta_SPL_mean'))} | `{str(row['supports_navigation_improvement_claim']).lower()}` | "
            f"{row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Task Context",
            "",
            "| Task Context | H001 SR | Task-Agnostic SR | Delta SR | H001 SPL | Task-Agnostic SPL | Delta SPL |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in task_rows:
        lines.append(
            "| "
            f"`{row['task_context_id']}` | {fmt(row.get('h001_SR'))} | {fmt(row.get('task_agnostic_SR'))} | "
            f"{fmt(row.get('h001_minus_task_agnostic_SR'))} | {fmt(row.get('h001_SPL'))} | "
            f"{fmt(row.get('task_agnostic_SPL'))} | {fmt(row.get('h001_minus_task_agnostic_SPL'))} |"
        )

    lines.extend(
        [
            "",
            "## Scale Gate",
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
            "- Do not scale M41 as a final navigation result.",
            "- Keep the static stale-memory result as a lower-bound failure diagnosis.",
            "- Redesign H001 before scale so it changes source expansion, re-observation, or task-dependent visit order beyond current-observation ranking.",
            f"- Next unit: `{NEXT_UNIT}`.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m41_coverage = read_json(M41_DIR / "coverage.json")
    all_rows = read_jsonl(M41_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_source_rows = read_jsonl(M41_DIR / "pairwise_policy_delta_rows.jsonl")
    scan_rows = scan_task_rows(all_rows)

    policy_rows = build_policy_result_rows(all_rows)
    source_rows = build_source_boundary_rows(scan_rows)
    pairwise_rows = build_pairwise_decision_rows(pairwise_source_rows)
    task_rows = build_task_context_effect_rows(scan_rows)
    scale_rows = build_scale_gate_rows(policy_rows, source_rows, pairwise_rows, task_rows)
    claim_rows = build_claim_boundary_rows(scale_rows)
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows(scale_rows)

    failed_scale_gates = [row["gate_id"] for row in scale_rows if not row["passed"]]
    source_gap_h001 = next(
        row for row in source_rows if row["policy_id"] == H001_POLICY and row["boundary"] == "source_gap"
    )
    source_ready_h001 = next(
        row for row in source_rows if row["policy_id"] == H001_POLICY and row["boundary"] == "source_ready"
    )

    coverage = {
        "version": VERSION,
        "status": STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m41_status": m41_coverage.get("status"),
        "m41_scan_task_policy_rows": m41_coverage.get("scan_task_policy_rows"),
        "policy_result_rows": len(policy_rows),
        "source_boundary_rows": len(source_rows),
        "pairwise_decision_rows": len(pairwise_rows),
        "task_context_effect_rows": len(task_rows),
        "scale_gate_rows": len(scale_rows),
        "claim_boundary_rows": len(claim_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "route_decision_rows": len(route_rows),
        "h001_source_ready_SR": source_ready_h001.get("SR"),
        "h001_source_gap_SR": source_gap_h001.get("SR"),
        "static_baseline_only_positive": True,
        "source_ready_policy_tie": True,
        "source_gap_unsolved": finite_float(source_gap_h001.get("SR")) == 0.0,
        "task_context_main_effect_ready": False,
        "budget_matched_repair_positive_claim_ready": False,
        "scale_up_recommended_now": False,
        "dynamic_stale_navigation_result_ready": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_route": "policy_redesign_before_scale",
        "selected_next_unit": NEXT_UNIT,
        "failed_scale_gates": failed_scale_gates,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_decision_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "task_context_effect_rows.jsonl", task_rows)
    write_jsonl(ARTIFACT_DIR / "scale_gate_rows.jsonl", scale_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    write_report(coverage, policy_rows, source_rows, pairwise_rows, task_rows, scale_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
