#!/usr/bin/env python3
"""Build the E005-M95 paper-facing real-proposal diagnostic boundary."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M95_real_proposal_paper_boundary_v0"
VERSION = "e005_m95_real_proposal_paper_boundary_v0"

M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M76_DIR = EXP_ROOT / "artifacts" / "E005-M76_real_proposal_claim_boundary_v0"
M82_DIR = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0" / "heldout_b02"
M93_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_result_analysis_v0"
M94_DIR = EXP_ROOT / "artifacts" / "E005-M94_active_label_precedence_claim_boundary_v0"

H001 = "real_task_context_memory_trust_reobserve_v0"
CONTEXT = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC = "real_static_memory_only_v0"
DETECTOR_TASK = "real_detector_task_budget_v0"
DETECTOR_TOP5 = "real_detector_confidence_top5_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
UNBOUNDED = "real_unbounded_old_memory_distance_guard_until_target_v0"

POLICY_LABELS = {
    STATIC: "Static stale memory",
    DETECTOR_TASK: "Real detector task-budget",
    DETECTOR_TOP5: "Real detector confidence top-5",
    CONCEPTGRAPHS: "ConceptGraphs same-batch map retrieval",
    CONTEXT: "Context-agnostic memory trust + re-observation",
    H001: "H001 task-conditioned memory trust + re-observation",
    UNBOUNDED: "Real detector unbounded target upper bound",
}

MAIN_POLICIES = [
    DETECTOR_TASK,
    DETECTOR_TOP5,
    CONCEPTGRAPHS,
    STATIC,
    CONTEXT,
    H001,
    UNBOUNDED,
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float | None, den: int | float | None) -> float | None:
    if num is None or not den:
        return None
    return round(float(num) / float(den), 6)


def delta(value: int | float | None, base: int | float | None) -> int | float | None:
    if value is None or base is None:
        return None
    if isinstance(value, int) and isinstance(base, int):
        return value - base
    return round(float(value) - float(base), 6)


def claim_role(policy: str) -> str:
    if policy == H001:
        return "main_method_diagnostic_row"
    if policy in {CONTEXT, STATIC}:
        return "memory_ablation"
    if policy in {DETECTOR_TASK, DETECTOR_TOP5, CONCEPTGRAPHS}:
        return "baseline"
    if policy == UNBOUNDED:
        return "diagnostic_upper_bound"
    return "diagnostic"


def build_main_table(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    policy_metrics = metrics["policy_metrics"]
    h001 = policy_metrics[H001]
    rows: list[dict[str, Any]] = []
    for policy in MAIN_POLICIES:
        metric = policy_metrics[policy]
        rows.append(
            {
                "table_id": "M95-A_full_real_proposal_diagnostic",
                "source_artifact": "E005-M75_real_proposal_aggregate_route_v0",
                "policy": policy,
                "paper_label": POLICY_LABELS[policy],
                "claim_role": claim_role(policy),
                "query_rows": metric["rows"],
                "success_rows": metric["query_bridge_success_rows"],
                "success_rate": metric["query_bridge_success_rate"],
                "target_detected_rows": metric["target_detected_rows"],
                "target_detected_rate": metric["target_detected_rate"],
                "mean_expected_search_cost": metric["mean_expected_search_cost"],
                "mean_attempt_spl_proxy": metric["mean_attempt_spl_proxy"],
                "old_location_dead_end_avoided_rows": metric.get("old_location_dead_end_avoided_rows"),
                "delta_success_rows_vs_h001": delta(metric["query_bridge_success_rows"], h001["query_bridge_success_rows"]),
                "delta_expected_search_cost_vs_h001": delta(metric["mean_expected_search_cost"], h001["mean_expected_search_cost"]),
                "paper_use": "diagnostic_main_table" if policy != UNBOUNDED else "upper_bound_appendix",
            }
        )
    return rows


def build_repair_table(
    m75: dict[str, Any],
    m82: dict[str, Any],
    m93: dict[str, Any],
    m94: dict[str, Any],
    detector_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    projected = m94["projected_aggregate_if_b02_replaced_by_m93"]
    return [
        {
            "table_id": "M95-B_repair_diagnostic",
            "row_id": "original_m75_aggregate",
            "paper_label": "Original full real-proposal aggregate",
            "scope": "195 query rows / b01+b02+b03",
            "source_artifact": "E005-M75_real_proposal_aggregate_route_v0",
            "target_detected_rows": m75["query_target_detected_rows"],
            "query_rows": m75["query_rows"],
            "target_detected_rate": m75["query_target_detected_rate"],
            "detector_top5_success_rows": m75["real_detector_top5_success_rows"],
            "detector_task_budget_success_rows": m75["real_detector_task_budget_success_rows"],
            "h001_success_rows": m75["h001_success_rows"],
            "proposal_precision": detector_summary["proposal_precision"],
            "scan_target_recall": detector_summary["scan_target_recall"],
            "claim_role": "baseline_diagnostic_aggregate",
            "paper_use": "diagnostic_table",
        },
        {
            "table_id": "M95-B_repair_diagnostic",
            "row_id": "m82_confidence_log_depth_b02",
            "paper_label": "Confidence-log-depth b02 rerun",
            "scope": "69 query rows / b02 only",
            "source_artifact": "E005-M82_confidence_log_depth_query_metric_v0",
            "target_detected_rows": m82["query_target_detected_rows"],
            "query_rows": m82["query_rows"],
            "target_detected_rate": m82["query_target_detected_rate"],
            "detector_top5_success_rows": m82["real_detector_top5_success_rows"],
            "detector_task_budget_success_rows": m82["real_detector_task_budget_success_rows"],
            "h001_success_rows": m82["real_h001_success_rows"],
            "proposal_precision": 0.05303,
            "scan_target_recall": 0.823529,
            "claim_role": "ranking_repair_diagnostic",
            "paper_use": "appendix_or_failure_analysis",
        },
        {
            "table_id": "M95-B_repair_diagnostic",
            "row_id": "m93_active_label_precedence_b02",
            "paper_label": "Active-label precedence b02 rerun",
            "scope": "69 query rows / b02 only",
            "source_artifact": "E005-M93_active_label_precedence_result_analysis_v0",
            "target_detected_rows": m93["m93_query_target_detected_rows"],
            "query_rows": m94["b02_query_rows"],
            "target_detected_rate": safe_rate(m93["m93_query_target_detected_rows"], m94["b02_query_rows"]),
            "detector_top5_success_rows": m93["m93_detector_top5_success_rows"],
            "detector_task_budget_success_rows": m93["m93_detector_task_budget_success_rows"],
            "h001_success_rows": m93["m93_h001_success_rows"],
            "proposal_precision": m93["m93_proposal_precision"],
            "scan_target_recall": m93["m93_scan_target_recall"],
            "target_detection_gain_rows_vs_m82": m93["target_detection_gain_rows"],
            "detector_top5_gain_rows_vs_m82": int(m93["m93_detector_top5_success_rows"]) - int(m82["real_detector_top5_success_rows"]),
            "detector_task_budget_gain_rows_vs_m82": int(m93["m93_detector_task_budget_success_rows"]) - int(m82["real_detector_task_budget_success_rows"]),
            "h001_gain_rows_vs_m82": int(m93["m93_h001_success_rows"]) - int(m82["real_h001_success_rows"]),
            "side_effect_loss_rows": m93["side_effect_detection_loss_rows"],
            "claim_role": "batch_repair_diagnostic",
            "paper_use": "failure_analysis_not_main_result",
        },
        {
            "table_id": "M95-B_repair_diagnostic",
            "row_id": "m94_b02_replaced_projection",
            "paper_label": "Projected aggregate if b02 is replaced by M93",
            "scope": "195 query rows / projection, not a full rerun",
            "source_artifact": "E005-M94_active_label_precedence_claim_boundary_v0",
            "target_detected_rows": projected["query_target_detected_rows"],
            "query_rows": projected["query_rows"],
            "target_detected_rate": projected["query_target_detected_rate"],
            "detector_top5_success_rows": projected["real_detector_top5_success_rows"],
            "detector_task_budget_success_rows": projected["real_detector_task_budget_success_rows"],
            "h001_success_rows": projected["h001_success_rows"],
            "proposal_precision": None,
            "scan_target_recall": None,
            "claim_role": "diagnostic_projection",
            "paper_use": "claim_boundary_only_not_main_table",
        },
    ]


def build_claim_boundary_rows(
    m75: dict[str, Any],
    m82: dict[str, Any],
    m93: dict[str, Any],
    m94: dict[str, Any],
    detector_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    projected = m94["projected_aggregate_if_b02_replaced_by_m93"]
    return [
        {
            "claim_id": "C-M95-001",
            "claim_type": "allowed_diagnostic",
            "claim": "H001 can be reported on the full real-proposal diagnostic denominator against detector-only and ConceptGraphs same-batch baselines.",
            "status": "ready_with_boundary",
            "evidence": {
                "query_rows": m75["query_rows"],
                "h001_success_rows": m75["h001_success_rows"],
                "context_agnostic_success_rows": m75["context_agnostic_success_rows"],
                "conceptgraphs_success_rows": m75["conceptgraphs_same_batch_success_rows"],
                "detector_top5_success_rows": m75["real_detector_top5_success_rows"],
                "detector_task_budget_success_rows": m75["real_detector_task_budget_success_rows"],
            },
            "allowed_wording": "On a full real-proposal diagnostic denominator, H001 outperforms detector-only and ConceptGraphs same-batch retrieval while remaining near context-agnostic memory trust.",
            "forbidden_wording": "H001 proves final real RGB-D/open-vocabulary robustness.",
            "next_validation_requirement": "Add stronger external proposal/mapping baselines or navigation/search execution evidence before expanding the claim.",
        },
        {
            "claim_id": "C-M95-002",
            "claim_type": "allowed_diagnostic",
            "claim": "Active-label precedence repairs one diagnosed b02 cleanup failure mode.",
            "status": "ready_batch_diagnostic",
            "evidence": {
                "b02_query_rows": m94["b02_query_rows"],
                "target_detected_before": m82["query_target_detected_rows"],
                "target_detected_after": m93["m93_query_target_detected_rows"],
                "detector_top5_before": m82["real_detector_top5_success_rows"],
                "detector_top5_after": m93["m93_detector_top5_success_rows"],
                "h001_before": m82["real_h001_success_rows"],
                "h001_after": m93["m93_h001_success_rows"],
                "side_effect_loss_rows": m93["side_effect_detection_loss_rows"],
            },
            "allowed_wording": "The active-label precedence repair recovers target detection for the diagnosed b02 zero-written cluster without observed side-effect loss.",
            "forbidden_wording": "The repair improves the main H001 method or solves real proposal robustness.",
            "next_validation_requirement": "Run b01/b03 only if a complete detector-repair appendix is needed.",
        },
        {
            "claim_id": "C-M95-003",
            "claim_type": "blocked",
            "claim": "Final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "evidence": {
                "m75_target_detected_rows": m75["query_target_detected_rows"],
                "m75_query_rows": m75["query_rows"],
                "m75_proposal_precision": detector_summary["proposal_precision"],
                "m93_proposal_precision": m93["m93_proposal_precision"],
                "m94_projected_target_detected_rows": projected["query_target_detected_rows"],
                "b01_b03_active_label_rerun_done": False,
            },
            "allowed_wording": "Current real-proposal results are diagnostic and expose detector/prompt failure modes.",
            "forbidden_wording": "The method is robust to real RGB-D/open-vocabulary perception.",
            "next_validation_requirement": "Heldout label/scene transfer with stronger proposal baselines and a visibility-aware denominator.",
        },
        {
            "claim_id": "C-M95-004",
            "claim_type": "blocked",
            "claim": "Deployable search policy.",
            "status": "blocked",
            "evidence": {
                "m93_detector_task_budget_gain_rows_vs_m82": int(m93["m93_detector_task_budget_success_rows"]) - int(m82["real_detector_task_budget_success_rows"]),
                "m93_h001_gain_rows_vs_m82": int(m93["m93_h001_success_rows"]) - int(m82["real_h001_success_rows"]),
                "trajectory_execution_ready": False,
            },
            "allowed_wording": "The current evidence supports a query-level search diagnostic and policy boundary.",
            "forbidden_wording": "The current policy is deployable for real robot search.",
            "next_validation_requirement": "Fixed execution environment, candidate visit execution, cost model validation, and ablations under stronger baselines.",
        },
        {
            "claim_id": "C-M95-005",
            "claim_type": "blocked",
            "claim": "Real navigation SR/SPL improvement.",
            "status": "blocked",
            "evidence": {
                "metrics_available": ["ExpectedSearchCost", "AttemptSPL"],
                "simulator_or_navmesh_ready": False,
                "trajectory_execution_ready": False,
            },
            "allowed_wording": "Navigation is currently represented by proxy search metrics.",
            "forbidden_wording": "The method improves real navigation SR/SPL.",
            "next_validation_requirement": "Simulator/navmesh episodes and navigation/search baselines such as VLFM, HM3D-OVON, or GOAT-Bench modular baselines.",
        },
        {
            "claim_id": "C-M95-006",
            "claim_type": "blocked",
            "claim": "Human intent as a main contribution.",
            "status": "blocked",
            "evidence": {
                "h001_minus_context_agnostic_success_rows_m75": int(m75["h001_success_rows"]) - int(m75["context_agnostic_success_rows"]),
                "human_intent_main_claim_ready": False,
            },
            "allowed_wording": "Structured task context remains a controlled secondary condition.",
            "forbidden_wording": "The main contribution is human intent understanding.",
            "next_validation_requirement": "Optional E006 context-sensitive utility benchmark with stronger context-agnostic baselines.",
        },
    ]


def markdown_main_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Row | Role | Success | Target Detected | ExpectedSearchCost | AttemptSPL | Use |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["paper_label"]),
                    str(row["claim_role"]),
                    f"{row['success_rows']} / {row['query_rows']} ({float(row['success_rate']):.6f})",
                    f"{row['target_detected_rows']} / {row['query_rows']} ({float(row['target_detected_rate']):.6f})",
                    f"{float(row['mean_expected_search_cost']):.6f}",
                    f"{float(row['mean_attempt_spl_proxy']):.6f}",
                    str(row["paper_use"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def markdown_repair_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Row | Scope | Target Detected | Detector Top5 | Detector Task-Budget | H001 | Claim Role |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["paper_label"]),
                    str(row["scope"]),
                    f"{row['target_detected_rows']} / {row['query_rows']} ({float(row['target_detected_rate']):.6f})",
                    f"{row['detector_top5_success_rows']} / {row['query_rows']}",
                    f"{row['detector_task_budget_success_rows']} / {row['query_rows']}",
                    f"{row['h001_success_rows']} / {row['query_rows']}",
                    str(row["claim_role"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_report(
    main_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> str:
    return f"""# E005-M95 Real-Proposal Paper Boundary

## Facts

- Status: `{coverage["status"]}`.
- Main diagnostic denominator: {coverage["query_rows"]} query rows.
- M75 target detected: {coverage["m75_target_detected_rows"]} / {coverage["query_rows"]}.
- M75 H001 / context-agnostic / ConceptGraphs / detector top5: {coverage["m75_h001_success_rows"]} / {coverage["m75_context_agnostic_success_rows"]} / {coverage["m75_conceptgraphs_success_rows"]} / {coverage["m75_detector_top5_success_rows"]}.
- M94 projected aggregate after b02 replacement: target detected {coverage["m94_projected_target_detected_rows"]} / {coverage["query_rows"]}, detector top5 {coverage["m94_projected_detector_top5_success_rows"]} / {coverage["query_rows"]}, detector task-budget {coverage["m94_projected_detector_task_budget_success_rows"]} / {coverage["query_rows"]}, H001 {coverage["m94_projected_h001_success_rows"]} / {coverage["query_rows"]}.
- Selected next route: `{coverage["selected_next_route"]}`.
- Next recommended unit: `{coverage["next_recommended_unit"]}`.

## Paper-Facing Diagnostic Table

{markdown_main_table(main_rows)}
## Repair Diagnostic Table

{markdown_repair_table(repair_rows)}
## Claim Boundary

- Allowed diagnostic claims: {coverage["allowed_diagnostic_claim_count"]}.
- Blocked claims: {coverage["blocked_claim_count"]}.
- Final real RGB-D/open-vocabulary robustness: false.
- Deployable search policy: false.
- Real navigation `SR` / `SPL`: false.
- Human intent main contribution: false.

## Agent Inference

- The paper-facing E005 result should use M75 as the full-denominator real-proposal diagnostic table.
- M93/M94 should be reported as repair/failure-analysis evidence, not as a main method result.
- The next useful work is not another local cleanup rerun unless a complete appendix is required; it is choosing the next expansion route toward stronger external proposal/mapping evidence or navigation/search execution.
"""


def build_outputs() -> dict[str, Any]:
    m75 = read_json(M75_DIR / "coverage.json")
    m75_metrics = read_json(M75_DIR / "policy_metrics.json")
    m75_query = read_json(M75_DIR / "query_summary.json")
    detector_summary = read_json(M76_DIR / "detector_summary.json")
    m82 = read_json(M82_DIR / "coverage.json")
    m93 = read_json(M93_DIR / "coverage.json")
    m94 = read_json(M94_DIR / "coverage.json")

    main_rows = build_main_table({"policy_metrics": m75_metrics})
    repair_rows = build_repair_table(m75, m82, m93, m94, detector_summary)
    claim_rows = build_claim_boundary_rows(m75, m82, m93, m94, detector_summary)

    coverage = {
        "allowed_diagnostic_claim_count": sum(1 for row in claim_rows if row["claim_type"] == "allowed_diagnostic"),
        "blocked_claim_count": sum(1 for row in claim_rows if row["claim_type"] == "blocked"),
        "deployable_search_policy_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "human_intent_main_claim_ready": False,
        "m75_conceptgraphs_success_rows": m75["conceptgraphs_same_batch_success_rows"],
        "m75_context_agnostic_success_rows": m75["context_agnostic_success_rows"],
        "m75_detector_task_budget_success_rows": m75["real_detector_task_budget_success_rows"],
        "m75_detector_top5_success_rows": m75["real_detector_top5_success_rows"],
        "m75_h001_success_rows": m75["h001_success_rows"],
        "m75_proposal_precision": detector_summary["proposal_precision"],
        "m75_query_target_detected_rate": m75["query_target_detected_rate"],
        "m75_scan_target_recall": detector_summary["scan_target_recall"],
        "m75_target_detected_rows": m75["query_target_detected_rows"],
        "m93_h001_gain_rows_vs_m82": int(m93["m93_h001_success_rows"]) - int(m82["real_h001_success_rows"]),
        "m93_target_detection_gain_rows": m93["target_detection_gain_rows"],
        "m94_projected_detector_task_budget_success_rows": m94["projected_aggregate_if_b02_replaced_by_m93"]["real_detector_task_budget_success_rows"],
        "m94_projected_detector_top5_success_rows": m94["projected_aggregate_if_b02_replaced_by_m93"]["real_detector_top5_success_rows"],
        "m94_projected_h001_success_rows": m94["projected_aggregate_if_b02_replaced_by_m93"]["h001_success_rows"],
        "m94_projected_target_detected_rows": m94["projected_aggregate_if_b02_replaced_by_m93"]["query_target_detected_rows"],
        "main_table_row_count": len(main_rows),
        "next_recommended_unit": "E005-M96 next expansion route decision: external proposal baseline vs navigation bridge",
        "query_rows": m75["query_rows"],
        "query_rows_by_batch": m75_query["query_rows_by_batch"],
        "real_navigation_sr_spl_ready": False,
        "repair_table_row_count": len(repair_rows),
        "selected_next_route": "close_current_e005_boundary_and_choose_next_expansion_route",
        "status": "e005_m95_real_proposal_paper_boundary_ready",
        "version": VERSION,
    }
    return {
        "claim_rows": claim_rows,
        "coverage": coverage,
        "main_rows": main_rows,
        "repair_rows": repair_rows,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = build_outputs()
    main_rows = outputs["main_rows"]
    repair_rows = outputs["repair_rows"]
    claim_rows = outputs["claim_rows"]
    coverage = outputs["coverage"]

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", outputs)
    write_jsonl(OUT_DIR / "paper_real_proposal_table_rows.jsonl", main_rows)
    write_csv(OUT_DIR / "paper_real_proposal_table_rows.csv", main_rows)
    write_jsonl(OUT_DIR / "repair_diagnostic_rows.jsonl", repair_rows)
    write_csv(OUT_DIR / "repair_diagnostic_rows.csv", repair_rows)
    write_jsonl(OUT_DIR / "final_claim_boundary_rows.jsonl", claim_rows)
    write_text(
        OUT_DIR / "paper_real_proposal_tables.md",
        "# E005-M95 Paper-Facing Tables\n\n"
        "## Full Real-Proposal Diagnostic Table\n\n"
        + markdown_main_table(main_rows)
        + "\n## Repair Diagnostic Table\n\n"
        + markdown_repair_table(repair_rows),
    )
    write_text(OUT_DIR / "report.md", build_report(main_rows, repair_rows, claim_rows, coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
