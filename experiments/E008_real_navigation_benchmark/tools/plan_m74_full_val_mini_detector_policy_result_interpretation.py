#!/usr/bin/env python3
"""Interpret E008-M73 full-val-mini detector-policy trajectory results."""

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
M72_DIR = EXP_ROOT / "artifacts" / "E008-M72_full_val_mini_detector_policy_trajectory_contract_v0"
M73_DIR = EXP_ROOT / "artifacts" / "E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M74_full_val_mini_detector_policy_result_interpretation_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M74_full_val_mini_detector_policy_result_interpretation_v0"
)

VERSION = "e008_m74_full_val_mini_detector_policy_result_interpretation_v0"
READY_STATUS = "e008_m74_full_val_mini_detector_policy_result_interpretation_ready"
BLOCKED_STATUS = "e008_m74_full_val_mini_detector_policy_result_interpretation_blocked"
NEXT_UNIT = "E008-M75 full-val-mini source-gap/SPL repair contract"

ALL_CANDIDATE_POLICY = "detector_confidence_all_candidates_v0"
PRIMARY_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
PATH_COST_POLICY = "path_cost_ascending_reachable_subset_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"

POLICY_ORDER = [
    ALL_CANDIDATE_POLICY,
    PRIMARY_DETECTOR_POLICY,
    PATH_COST_POLICY,
    TRADEOFF_POLICY,
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


def metric_rows_by_scope(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == scope]


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
        "StopRank_mean_over_success": mean(
            [finite_float(row.get("StopRank")) for row in rows if is_success(row)]
        ),
        "OldLocationDeadEndCostM_mean": mean(
            [finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]
        ),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
    }


def build_policy_interpretation_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = {
        str(row.get("policy_id")): row
        for row in metric_rows_by_scope(metric_rows, "policy_aggregate")
    }
    primary = aggregates.get(PRIMARY_DETECTOR_POLICY, {})
    rows = []
    for policy_id in POLICY_ORDER:
        row = dict(aggregates.get(policy_id, {}))
        sr_delta = delta(row.get("SR"), primary.get("SR"))
        spl_delta = delta(row.get("SPL"), primary.get("SPL"))
        path_delta = delta(row.get("PathLengthM_mean"), primary.get("PathLengthM_mean"))
        visits_delta = delta(row.get("CandidateVisits_mean"), primary.get("CandidateVisits_mean"))
        row.update(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": policy_id,
                "delta_SR_vs_primary_detector": sr_delta,
                "delta_SPL_vs_primary_detector": spl_delta,
                "delta_PathLengthM_mean_vs_primary_detector": path_delta,
                "delta_CandidateVisits_mean_vs_primary_detector": visits_delta,
                "supports_positive_policy_success_claim": bool(sr_delta is not None and sr_delta > 0),
                "supports_positive_spl_claim": bool(
                    sr_delta is not None
                    and spl_delta is not None
                    and sr_delta >= 0
                    and spl_delta > 0
                ),
                "supports_path_length_diagnostic": bool(path_delta is not None and path_delta < 0),
                "supports_final_navigation_claim": False,
                "interpretation": interpret_policy(policy_id, sr_delta, spl_delta, path_delta, visits_delta),
            }
        )
        rows.append(row)
    return rows


def interpret_policy(
    policy_id: str,
    sr_delta: float | None,
    spl_delta: float | None,
    path_delta: float | None,
    visits_delta: float | None,
) -> str:
    if policy_id == PRIMARY_DETECTOR_POLICY:
        return "primary_detector_confidence_baseline_has_best_spl_and_lowest_candidate_visits"
    if policy_id == ALL_CANDIDATE_POLICY:
        return "all_candidate_detector_baseline_matches_primary_spl_but_keeps_unreachable_candidate_accounting"
    if policy_id == PATH_COST_POLICY:
        if (path_delta or 0.0) < 0 and (spl_delta or 0.0) < 0 and (visits_delta or 0.0) > 0:
            return "path_cost_policy_shortens_mean_path_but_loses_spl_and_visit_efficiency"
        return "path_cost_policy_requires_manual_review"
    if policy_id == TRADEOFF_POLICY:
        return "confidence_path_cost_tradeoff_does_not_beat_detector_confidence_on_sr_or_spl"
    return "requires_manual_review"


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        grouped[(str(row.get("policy_id")), bool(row.get("diagnostic_source_gap_boundary")))].append(row)

    rows = []
    for policy_id in POLICY_ORDER:
        for source_gap in [False, True]:
            current = aggregate(
                grouped.get((policy_id, source_gap), []),
                {
                    "version": VERSION,
                    "row_type": "policy_source_boundary",
                    "policy_id": policy_id,
                    "diagnostic_source_gap_boundary": source_gap,
                    "source_boundary": "source_gap" if source_gap else "source_ready",
                },
            )
            current["supports_final_navigation_claim"] = False
            current["interpretation"] = interpret_source_boundary(source_gap, current)
            rows.append(current)
    return rows


def interpret_source_boundary(source_gap: bool, row: dict[str, Any]) -> str:
    sr = finite_float(row.get("SR")) or 0.0
    if source_gap and sr == 0.0:
        return "source_gap_not_recovered_by_detector_policy_rows"
    if source_gap:
        return "source_gap_partial_recovery_requires_manual_review"
    if sr < 1.0:
        return "source_ready_policy_still_has_failures"
    return "source_ready_success_pass"


def build_pairwise_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        grouped[str(row.get("baseline_policy_id"))].append(row)

    out = []
    for baseline_id in [ALL_CANDIDATE_POLICY, PRIMARY_DETECTOR_POLICY, TRADEOFF_POLICY]:
        rows = grouped.get(baseline_id, [])
        delta_sr = [finite_float(row.get("delta_SR")) for row in rows]
        delta_spl = [finite_float(row.get("delta_SPL")) for row in rows]
        delta_path = [finite_float(row.get("delta_PathLengthM")) for row in rows]
        delta_visits = [
            delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits"))
            for row in rows
        ]
        current = {
            "version": VERSION,
            "row_type": "pairwise_path_cost_vs_baseline",
            "method_policy_id": PATH_COST_POLICY,
            "baseline_policy_id": baseline_id,
            "rows": len(rows),
            "delta_SR_mean": mean(delta_sr),
            "delta_SPL_mean": mean(delta_spl),
            "delta_PathLengthM_mean": mean(delta_path),
            "delta_CandidateVisits_mean": mean(delta_visits),
            "sr_win_rows": sum(1 for value in delta_sr if value is not None and value > 0),
            "sr_tie_rows": sum(1 for value in delta_sr if value == 0),
            "sr_loss_rows": sum(1 for value in delta_sr if value is not None and value < 0),
            "spl_win_rows": sum(1 for value in delta_spl if value is not None and value > 0),
            "spl_loss_rows": sum(1 for value in delta_spl if value is not None and value < 0),
            "path_length_win_rows": sum(1 for value in delta_path if value is not None and value < 0),
            "candidate_visit_regression_rows": sum(1 for value in delta_visits if value is not None and value > 0),
            "supports_positive_policy_claim": False,
            "supports_final_navigation_claim": False,
        }
        current["interpretation"] = interpret_pairwise(current)
        out.append(current)
    return out


def interpret_pairwise(row: dict[str, Any]) -> str:
    if row["baseline_policy_id"] in {ALL_CANDIDATE_POLICY, PRIMARY_DETECTOR_POLICY}:
        return "path_cost_has_no_sr_gain_and_negative_mean_spl_against_detector_confidence"
    if row["baseline_policy_id"] == TRADEOFF_POLICY:
        return "path_cost_is_not_a_stable_improvement_over_confidence_path_cost_tradeoff"
    return "requires_manual_review"


def build_budget_boundary_rows(budget_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = [
        row for row in budget_rows if row.get("metric_scope") == "policy_budget_aggregate"
    ]
    out = []
    for row in aggregates:
        budget = row.get("budget")
        sr = finite_float(row.get("GoalEvalProxySR")) or 0.0
        spl = finite_float(row.get("GoalEvalProxySPL")) or 0.0
        current = {
            "version": VERSION,
            "row_type": "budget_proxy_boundary",
            "policy_id": row.get("policy_id"),
            "budget": budget,
            "success_rows": row.get("success_rows"),
            "scan_policy_rows": row.get("scan_policy_rows"),
            "GoalEvalProxySR": row.get("GoalEvalProxySR"),
            "GoalEvalProxySPL": row.get("GoalEvalProxySPL"),
            "deployable_fixed_budget_ready": bool(budget == 5 and sr >= 0.8 and spl > 0.5),
            "supports_final_navigation_claim": False,
            "interpretation": interpret_budget(budget, sr),
        }
        out.append(current)
    return sorted(out, key=lambda r: (str(r["policy_id"]), str(r["budget"])))


def interpret_budget(budget: object, sr: float) -> str:
    if budget == "full":
        return "full_rank_proxy_available_not_deployable_budget"
    if budget == 5 and sr < 0.8:
        return "budget5_proxy_success_too_low_for_deployable_search_claim"
    if isinstance(budget, int) and budget < 5:
        return "low_budget_diagnostic_only"
    return "budget_sensitivity_context"


def build_gate_rows(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> list[dict[str, Any]]:
    by_policy = {str(row.get("policy_id")): row for row in policy_rows}
    primary = by_policy.get(PRIMARY_DETECTOR_POLICY, {})
    path = by_policy.get(PATH_COST_POLICY, {})
    source_gap_rows = [row for row in source_rows if row.get("source_boundary") == "source_gap"]
    budget5_rows = [row for row in budget_rows if row.get("budget") == 5]
    budget5_min_sr = min(
        [finite_float(row.get("GoalEvalProxySR")) or 0.0 for row in budget5_rows],
        default=0.0,
    )
    path_sr_delta = delta(path.get("SR"), primary.get("SR")) or 0.0
    path_spl_delta = delta(path.get("SPL"), primary.get("SPL")) or 0.0
    path_length_delta = delta(path.get("PathLengthM_mean"), primary.get("PathLengthM_mean")) or 0.0

    return [
        gate(
            "m73_input_ready",
            "pass" if not missing_inputs and coverage.get("status") == "e008_m73_full_val_mini_detector_policy_trajectory_execution_smoke_ready" else "fail",
            "M73 trajectory execution artifact is present and ready.",
            blocks_final=True,
        ),
        gate(
            "leakage_audit_pass",
            "pass" if bool(coverage.get("leakage_audit_pass")) else "fail",
            "ObjectNav goal/viewpoint fields are metric-only and not policy inputs.",
            blocks_final=True,
        ),
        gate(
            "proxy_to_trajectory_success_consistency",
            "pass" if finite_float(coverage.get("trajectory_SR")) == 0.8 else "warning",
            "Executed trajectory SR matches the M72/M70 full-ranked proxy success floor of 24/30.",
            blocks_final=False,
        ),
        gate(
            "positive_policy_success_gain",
            "fail" if path_sr_delta <= 0 else "pass",
            "All detector policies tie at SR 0.8; path-cost ordering does not improve success.",
            blocks_final=True,
        ),
        gate(
            "positive_spl_gain",
            "fail" if path_spl_delta <= 0 else "pass",
            "Path-cost ordering loses SPL against detector-confidence baselines.",
            blocks_final=True,
        ),
        gate(
            "path_length_gain_only",
            "warning" if path_length_delta < 0 else "fail",
            "Path-cost ordering lowers mean path length, but this alone is insufficient because SPL and visits regress.",
            blocks_final=True,
        ),
        gate(
            "source_gap_recovery",
            "fail" if all((finite_float(row.get("SR")) or 0.0) == 0.0 for row in source_gap_rows) else "warning",
            "Source-gap rows have zero trajectory success in M73.",
            blocks_final=True,
        ),
        gate(
            "budget5_deployability",
            "fail" if budget5_min_sr < 0.8 else "warning",
            f"Minimum budget-5 proxy SR is {budget5_min_sr:.4f}, below deployable search requirements.",
            blocks_final=True,
        ),
        gate(
            "external_navigation_baselines",
            "fail",
            "VLFM / HM3D-OVON / GOAT-Bench-style baselines are not integrated.",
            blocks_final=True,
        ),
        gate(
            "diagnostic_table_ready",
            "pass",
            "M73 is usable as a diagnostic trajectory table with explicit negative boundary.",
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
            "executed_full_val_mini_detector_policy_trajectory_smoke",
            True,
            "M73 executes the full-val-mini detector-policy rows in Habitat and can be reported as diagnostic trajectory evidence.",
        ),
        claim(
            "proxy_to_trajectory_consistency",
            True,
            "M73 preserves the full-ranked 24/30 success level from M70/M72 in executed trajectories.",
        ),
        claim(
            "path_cost_policy_improves_navigation",
            False,
            "Path-cost ordering has no SR gain and lower SPL than detector-confidence baselines.",
        ),
        claim(
            "deployable_fixed_budget_search_policy",
            False,
            "M72 budget-5 success is too low and M73 is a full-ranked execution smoke.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Requires source-gap repair, SPL/visit efficiency repair, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "h001_stale_memory_navigation_claim",
            False,
            "M73 is detector-policy-only and does not test H001 stale-memory update.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M73 uses `open_vocabulary_object_search` as a structured context only and does not test human intent.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "claim_id": claim_id,
        "supported": supported,
        "claim_boundary": boundary,
    }


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "repair_before_positive_navigation_claim",
            "selected_next_unit": NEXT_UNIT,
            "selected_route": "source_gap_and_spl_regression_repair_contract",
            "rationale": "M73 is executed and useful diagnostically, but path-cost policy has no SR gain, lower SPL, more visits, source-gap failure, and budget-5 weakness.",
            "launch_long_job_now": False,
            "final_real_navigation_sr_spl_ready": False,
            "deployable_search_policy_ready": False,
            "diagnostic_table_ready": True,
        }
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
        for col in columns:
            value = row.get(col)
            if isinstance(value, float):
                value = fmt(value)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    selected_route = route_rows[0] if route_rows else {}
    report = "\n".join(
        [
            "# E008-M74 Full-Val-Mini Detector-Policy Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M73 status: `{coverage.get('m73_status')}`.",
            f"- M73 trajectory SR / SPL: {fmt(coverage.get('m73_trajectory_SR'))} / {fmt(coverage.get('m73_trajectory_SPL_mean'))}.",
            f"- Scan-task-policy rows: {coverage.get('m73_scan_task_policy_rows')}.",
            f"- Path-cost vs detector SPL delta: {fmt(coverage.get('path_cost_delta_SPL_vs_primary_detector'))}.",
            f"- Path-cost vs detector path-length delta: {fmt(coverage.get('path_cost_delta_PathLengthM_vs_primary_detector'))}.",
            f"- Source-gap trajectory SR: {fmt(coverage.get('source_gap_SR'))}.",
            f"- Minimum budget-5 proxy SR: {fmt(coverage.get('budget5_min_GoalEvalProxySR'))}.",
            "",
            "## Policy Interpretation",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "success_rows",
                    "scan_task_policy_rows",
                    "SR",
                    "SPL",
                    "PathLengthM_mean",
                    "CandidateVisits_mean",
                    "interpretation",
                ],
            ),
            "",
            "## Pairwise Path-Cost Deltas",
            "",
            markdown_table(
                pairwise_rows,
                [
                    "baseline_policy_id",
                    "delta_SR_mean",
                    "delta_SPL_mean",
                    "delta_PathLengthM_mean",
                    "delta_CandidateVisits_mean",
                    "interpretation",
                ],
            ),
            "",
            "## Source Boundary",
            "",
            markdown_table(
                source_rows,
                ["policy_id", "source_boundary", "rows", "success_rows", "SR", "SPL", "interpretation"],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_final_real_navigation_claim", "rationale"]),
            "",
            "## Decision",
            "",
            f"- Selected route: `{selected_route.get('selected_route')}`.",
            f"- Selected next unit: {selected_route.get('selected_next_unit')}.",
            "- M73 should be treated as diagnostic executed trajectory evidence, not as positive final navigation evidence.",
            "- The next step should repair source-gap failure and SPL/candidate-visit regression before any broader navigation claim.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    coverage_m73 = read_json(M73_DIR / "coverage.json")
    metric_rows = read_jsonl(M73_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_input_rows = read_jsonl(M73_DIR / "pairwise_policy_delta_rows.jsonl")
    leakage_rows = read_jsonl(M73_DIR / "leakage_audit_rows.jsonl")
    budget_input_rows = read_jsonl(M72_DIR / "budget_proxy_summary_rows.jsonl")

    missing_inputs = [
        str(path)
        for path in [
            M73_DIR / "coverage.json",
            M73_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
            M73_DIR / "pairwise_policy_delta_rows.jsonl",
            M73_DIR / "leakage_audit_rows.jsonl",
            M72_DIR / "budget_proxy_summary_rows.jsonl",
        ]
        if not path.exists()
    ]

    scan_rows = metric_rows_by_scope(metric_rows, "scan_task_policy")
    policy_rows = build_policy_interpretation_rows(metric_rows)
    source_rows = build_source_boundary_rows(scan_rows)
    pairwise_rows = build_pairwise_summary_rows(pairwise_input_rows)
    budget_rows = build_budget_boundary_rows(budget_input_rows)
    gate_rows = build_gate_rows(coverage_m73, policy_rows, source_rows, budget_rows, missing_inputs)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    by_policy = {str(row.get("policy_id")): row for row in policy_rows}
    path = by_policy.get(PATH_COST_POLICY, {})
    source_gap_all = [row for row in source_rows if row.get("source_boundary") == "source_gap"]
    budget5 = [row for row in budget_rows if row.get("budget") == 5]
    input_ready = (
        not missing_inputs
        and coverage_m73.get("status") == "e008_m73_full_val_mini_detector_policy_trajectory_execution_smoke_ready"
    )
    leakage_pass = bool(coverage_m73.get("leakage_audit_pass")) and all(
        bool(row.get("leakage_audit_pass")) for row in leakage_rows
    )
    status = READY_STATUS if input_ready and leakage_pass else BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m73_status": coverage_m73.get("status"),
        "missing_inputs": missing_inputs,
        "leakage_audit_pass": leakage_pass,
        "m73_trajectory_candidate_rows": coverage_m73.get("trajectory_candidate_rows"),
        "m73_trajectory_attempt_rows": coverage_m73.get("trajectory_attempt_rows"),
        "m73_scan_task_policy_rows": coverage_m73.get("scan_task_policy_rows"),
        "m73_trajectory_success_rows": coverage_m73.get("trajectory_success_rows"),
        "m73_trajectory_failure_rows": coverage_m73.get("trajectory_failure_rows"),
        "m73_trajectory_SR": coverage_m73.get("trajectory_SR"),
        "m73_trajectory_SPL_mean": coverage_m73.get("trajectory_SPL_mean"),
        "path_cost_delta_SR_vs_primary_detector": path.get("delta_SR_vs_primary_detector"),
        "path_cost_delta_SPL_vs_primary_detector": path.get("delta_SPL_vs_primary_detector"),
        "path_cost_delta_PathLengthM_vs_primary_detector": path.get(
            "delta_PathLengthM_mean_vs_primary_detector"
        ),
        "path_cost_delta_CandidateVisits_vs_primary_detector": path.get(
            "delta_CandidateVisits_mean_vs_primary_detector"
        ),
        "source_gap_SR": mean([finite_float(row.get("SR")) for row in source_gap_all]),
        "source_gap_success_rows": sum(int(row.get("success_rows") or 0) for row in source_gap_all),
        "source_gap_rows": sum(int(row.get("rows") or 0) for row in source_gap_all),
        "budget5_min_GoalEvalProxySR": min(
            [finite_float(row.get("GoalEvalProxySR")) or 0.0 for row in budget5],
            default=0.0,
        ),
        "policy_interpretation_rows": len(policy_rows),
        "source_boundary_rows": len(source_rows),
        "pairwise_summary_rows": len(pairwise_rows),
        "budget_boundary_rows": len(budget_rows),
        "gate_rows": len(gate_rows),
        "gate_pass_rows": sum(1 for row in gate_rows if row["gate_status"] == "pass"),
        "gate_warning_rows": sum(1 for row in gate_rows if row["gate_status"] == "warning"),
        "gate_fail_rows": sum(1 for row in gate_rows if row["gate_status"] == "fail"),
        "diagnostic_table_ready": status == READY_STATUS,
        "positive_navigation_policy_claim_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else None,
        "launch_long_job_now": False,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_interpretation_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_summary_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "budget_boundary_rows.jsonl", budget_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_csv(
        ARTIFACT_DIR / "diagnostic_policy_table.csv",
        policy_rows,
        [
            "policy_id",
            "success_rows",
            "scan_task_policy_rows",
            "SR",
            "SPL",
            "PathLengthM_mean",
            "CandidateVisits_mean",
            "delta_SR_vs_primary_detector",
            "delta_SPL_vs_primary_detector",
            "delta_PathLengthM_mean_vs_primary_detector",
            "interpretation",
        ],
    )
    write_report(coverage, policy_rows, source_rows, pairwise_rows, gate_rows, route_rows)

    for filename in [
        "coverage.json",
        "policy_interpretation_rows.jsonl",
        "source_boundary_rows.jsonl",
        "pairwise_summary_rows.jsonl",
        "budget_boundary_rows.jsonl",
        "gate_rows.jsonl",
        "claim_boundary_rows.jsonl",
        "route_decision_rows.jsonl",
        "diagnostic_policy_table.csv",
        "report.md",
    ]:
        shutil.copy2(ARTIFACT_DIR / filename, DATA_OUT_DIR / filename)

    print(json.dumps({"status": status, "selected_next_unit": coverage["selected_next_unit"]}, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
