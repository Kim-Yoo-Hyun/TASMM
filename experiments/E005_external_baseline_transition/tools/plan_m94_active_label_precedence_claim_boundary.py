#!/usr/bin/env python3
"""Fix the E005-M94 claim boundary after the M93 bounded b02 rerun."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M94_active_label_precedence_claim_boundary_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M71_B02_DIR = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0" / "heldout_b02"
M82_DIR = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0" / "heldout_b02"
M93_QUERY_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_query_metric_v0" / "heldout_b02"
M93_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_result_analysis_v0"
VERSION = "e005_m94_active_label_precedence_claim_boundary_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rate(num: int | float, den: int | float) -> float | None:
    return round(float(num) / float(den), 6) if den else None


def build_summary() -> dict[str, Any]:
    m75 = read_json(M75_DIR / "coverage.json")
    m71_b02 = read_json(M71_B02_DIR / "coverage.json")
    m82 = read_json(M82_DIR / "coverage.json")
    m93_query = read_json(M93_QUERY_DIR / "coverage.json")
    m93 = read_json(M93_DIR / "coverage.json")

    query_rows = int(m75.get("query_rows", 195))
    b02_rows = int(m82.get("query_rows", 69))

    # M93 reruns b02 with the confidence-log-depth runner plus active-label
    # precedence. Keep this projection diagnostic because b01/b03 did not run
    # the same active-label runner and H001 does not gain on b02.
    projected = {
        "query_rows": query_rows,
        "query_target_detected_rows": int(m75["query_target_detected_rows"])
        - int(m71_b02["query_target_detected_rows"])
        + int(m93["m93_query_target_detected_rows"]),
        "real_detector_top5_success_rows": int(m75["real_detector_top5_success_rows"])
        - int(m71_b02["real_detector_top5_success_rows"])
        + int(m93["m93_detector_top5_success_rows"]),
        "real_detector_task_budget_success_rows": int(m75["real_detector_task_budget_success_rows"])
        - int(m71_b02["real_detector_task_budget_success_rows"])
        + int(m93["m93_detector_task_budget_success_rows"]),
        "h001_success_rows": int(m75["h001_success_rows"])
        - int(m71_b02["real_h001_success_rows"])
        + int(m93["m93_h001_success_rows"]),
        "context_agnostic_success_rows": int(m75["context_agnostic_success_rows"])
        - int(m71_b02["real_context_agnostic_success_rows"])
        + int(m93_query["real_context_agnostic_success_rows"]),
    }
    projected["query_target_detected_rate"] = rate(projected["query_target_detected_rows"], query_rows)
    projected["detector_top5_rate"] = rate(projected["real_detector_top5_success_rows"], query_rows)
    projected["detector_task_budget_rate"] = rate(projected["real_detector_task_budget_success_rows"], query_rows)
    projected["h001_success_rate"] = rate(projected["h001_success_rows"], query_rows)

    h001_gain = int(m93["m93_h001_success_rows"]) - int(m82["real_h001_success_rows"])
    task_budget_gain = int(m93["m93_detector_task_budget_success_rows"]) - int(m82["real_detector_task_budget_success_rows"])
    target_detection_gain = int(m93["target_detection_gain_rows"])
    side_effect_loss = int(m93["side_effect_detection_loss_rows"])

    selected_route = "stop_and_record_m93_as_batch_level_repair_diagnostic"
    if h001_gain > 0 and task_budget_gain > 0 and side_effect_loss == 0:
        selected_route = "consider_b01_b03_extension_after_claim_update"

    summary = {
        "b02_query_rows": b02_rows,
        "broader_b01_b03_rerun_now": selected_route != "stop_and_record_m93_as_batch_level_repair_diagnostic",
        "deployable_search_policy_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_b02_gain_rows": h001_gain,
        "m75_baseline_aggregate": {
            "context_agnostic_success_rows": m75.get("context_agnostic_success_rows"),
            "h001_success_rows": m75.get("h001_success_rows"),
            "query_rows": m75.get("query_rows"),
            "query_target_detected_rows": m75.get("query_target_detected_rows"),
            "real_detector_task_budget_success_rows": m75.get("real_detector_task_budget_success_rows"),
            "real_detector_top5_success_rows": m75.get("real_detector_top5_success_rows"),
        },
        "m93_batch_result": {
            "detector_task_budget_success_rows_original_m75": m71_b02.get("real_detector_task_budget_success_rows"),
            "detector_task_budget_success_rows_after": m93.get("m93_detector_task_budget_success_rows"),
            "detector_task_budget_success_rows_before": m82.get("real_detector_task_budget_success_rows"),
            "detector_top5_success_rows_original_m75": m71_b02.get("real_detector_top5_success_rows"),
            "detector_top5_success_rows_after": m93.get("m93_detector_top5_success_rows"),
            "detector_top5_success_rows_before": m82.get("real_detector_top5_success_rows"),
            "h001_success_rows_original_m75": m71_b02.get("real_h001_success_rows"),
            "h001_success_rows_after": m93.get("m93_h001_success_rows"),
            "h001_success_rows_before": m82.get("real_h001_success_rows"),
            "proposal_precision": m93.get("m93_proposal_precision"),
            "scan_target_recall": m93.get("m93_scan_target_recall"),
            "side_effect_loss_rows": side_effect_loss,
            "target_detection_rows_original_m75": m71_b02.get("query_target_detected_rows"),
            "target_detection_rows_after": m93.get("m93_query_target_detected_rows"),
            "target_detection_rows_before": m82.get("query_target_detected_rows"),
            "target_detection_gain_rows": target_detection_gain,
        },
        "next_recommended_unit": "E005-M95 paper-facing real-proposal diagnostic table and final E005 boundary refresh",
        "projected_aggregate_if_b02_replaced_by_m93": projected,
        "real_navigation_sr_spl_ready": False,
        "selected_next_route": selected_route,
        "status": "e005_m94_active_label_precedence_claim_boundary_ready",
        "task_budget_b02_gain_rows": task_budget_gain,
        "version": VERSION,
    }
    return summary


def report(summary: dict[str, Any]) -> str:
    projected = summary["projected_aggregate_if_b02_replaced_by_m93"]
    return f"""# E005-M94 Active-Label Precedence Claim Boundary

## Facts

- Status: `{summary["status"]}`.
- M93 b02 target detected rows: {summary["m93_batch_result"]["target_detection_rows_before"]} -> {summary["m93_batch_result"]["target_detection_rows_after"]}.
- M93 b02 detector top5 rows: {summary["m93_batch_result"]["detector_top5_success_rows_before"]} -> {summary["m93_batch_result"]["detector_top5_success_rows_after"]}.
- M93 b02 detector task-budget rows: {summary["m93_batch_result"]["detector_task_budget_success_rows_before"]} -> {summary["m93_batch_result"]["detector_task_budget_success_rows_after"]}.
- M93 b02 H001 rows: {summary["m93_batch_result"]["h001_success_rows_before"]} -> {summary["m93_batch_result"]["h001_success_rows_after"]}.
- M93 side-effect loss rows: {summary["m93_batch_result"]["side_effect_loss_rows"]}.
- Projected diagnostic aggregate if b02 is replaced by M93: target detected {projected["query_target_detected_rows"]} / {projected["query_rows"]}, detector top5 {projected["real_detector_top5_success_rows"]} / {projected["query_rows"]}, detector task-budget {projected["real_detector_task_budget_success_rows"]} / {projected["query_rows"]}, H001 {projected["h001_success_rows"]} / {projected["query_rows"]}.
- Selected next route: `{summary["selected_next_route"]}`.
- Next recommended unit: `{summary["next_recommended_unit"]}`.

## Claim Boundary

- M93 is valid batch-level repair evidence for target-detection recovery in one diagnosed cleanup failure mode.
- M93 is not a main H001 semantic-memory gain because H001 success remains unchanged on b02.
- M93 is not a final real RGB-D/open-vocabulary robustness result because the repair was not tested across b01/b03 and detector precision remains weak.
- Real navigation `SR` / `SPL` and deployable search policy claims remain unsupported.

## Agent Inference

- The rational next step is to record M93 as diagnostic evidence, refresh the paper-facing real-proposal table/boundary, and avoid b01/b03 active-label reruns unless a complete detector-repair appendix is explicitly needed.
- Further top-tier progress should come from stronger external proposal/mapping baselines or navigation/search execution evidence, not from more local label-cleanup tuning.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    write_json(OUT_DIR / "coverage.json", summary)
    write_json(OUT_DIR / "summary.json", summary)
    write_text(OUT_DIR / "report.md", report(summary))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
