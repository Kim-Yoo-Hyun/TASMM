#!/usr/bin/env python3
"""Interpret E005-M80/M82 and decide whether to rerun remaining batches."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M83_confidence_log_depth_rerun_decision_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M71_DIR = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M78_DIR = EXP_ROOT / "artifacts" / "E005-M78_offline_repair_replay_v0"
M82_DIR = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0"
VERSION = "e005_m83_confidence_log_depth_rerun_decision_v0"
BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def batch_row_uids() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for batch_id in BATCHES:
        path = M68_DIR / "batches" / batch_id / "direct_bridge_query_rows.jsonl"
        for row in iter_jsonl(path):
            row_uid = row.get("row_uid")
            if row_uid:
                mapping[str(row_uid)] = batch_id
    return mapping


def m78_batch_metrics(row_to_batch: dict[str, str]) -> dict[str, dict[str, int]]:
    metrics: dict[str, dict[str, int]] = {
        batch: {"query_rows": 0, "top5_success_rows": 0, "target_detected_rows": 0}
        for batch in BATCHES
    }
    for row in iter_jsonl(M78_DIR / "query_policy_rows.jsonl"):
        batch_id = row_to_batch.get(str(row.get("row_uid")))
        if batch_id is None:
            continue
        metrics[batch_id]["query_rows"] += 1
        metrics[batch_id]["top5_success_rows"] += int(bool(row.get("query_bridge_success")))
        metrics[batch_id]["target_detected_rows"] += int(bool(row.get("target_detected")))
    return metrics


def build_batch_rows() -> list[dict[str, Any]]:
    row_to_batch = batch_row_uids()
    m78_by_batch = m78_batch_metrics(row_to_batch)
    rows: list[dict[str, Any]] = []
    for batch_id in BATCHES:
        original = read_json(M71_DIR / batch_id / "coverage.json")
        m82 = read_json(M82_DIR / batch_id / "coverage.json")
        fixed = m78_by_batch[batch_id]
        actual_available = bool(m82)
        actual_top5 = m82.get("real_detector_top5_success_rows") if actual_available else None
        actual_task_budget = m82.get("real_detector_task_budget_success_rows") if actual_available else None
        actual_target_detected = m82.get("query_target_detected_rows") if actual_available else None
        original_top5 = int(original.get("real_detector_top5_success_rows", 0))
        original_task_budget = int(original.get("real_detector_task_budget_success_rows", 0))
        original_target_detected = int(original.get("query_target_detected_rows", 0))
        expected_top5 = fixed["top5_success_rows"]
        expected_target_detected = fixed["target_detected_rows"]
        row: dict[str, Any] = {
            "actual_available": actual_available,
            "actual_target_detected_rows": actual_target_detected,
            "actual_task_budget_success_rows": actual_task_budget,
            "actual_top5_success_rows": actual_top5,
            "batch_id": batch_id,
            "expected_m78_target_detected_delta_vs_original": expected_target_detected - original_target_detected,
            "expected_m78_target_detected_rows": expected_target_detected,
            "expected_m78_top5_delta_vs_original": expected_top5 - original_top5,
            "expected_m78_top5_success_rows": expected_top5,
            "original_target_detected_rows": original_target_detected,
            "original_task_budget_success_rows": original_task_budget,
            "original_top5_success_rows": original_top5,
            "query_rows": int(original.get("query_rows", fixed["query_rows"])),
        }
        if actual_available:
            row.update(
                {
                    "actual_target_detected_delta_vs_original": int(actual_target_detected) - original_target_detected,
                    "actual_task_budget_delta_vs_original": int(actual_task_budget) - original_task_budget,
                    "actual_top5_delta_vs_original": int(actual_top5) - original_top5,
                    "actual_top5_matches_m78_expected": int(actual_top5) == expected_top5,
                }
            )
        if batch_id == "heldout_b01":
            row["remaining_batch_decision"] = "do_not_rerun_now_zero_top5_gain_expected"
        elif batch_id == "heldout_b03":
            row["remaining_batch_decision"] = "do_not_rerun_now_small_gain_only_if_diagnostic_table_needed"
        else:
            row["remaining_batch_decision"] = "completed_rerun_reproduced_expected_ranking_gain"
        rows.append(row)
    return rows


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    batch_lines = [
        "| Batch | Original Top5 | M78 Expected Top5 | Actual Top5 | Original Target Detected | Actual Target Detected | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        actual_top5 = "-" if row["actual_top5_success_rows"] is None else str(row["actual_top5_success_rows"])
        actual_target = "-" if row["actual_target_detected_rows"] is None else str(row["actual_target_detected_rows"])
        batch_lines.append(
            "| `{batch}` | {orig_top5}/{q} | {exp_top5}/{q} | {actual_top5}/{q} | "
            "{orig_target}/{q} | {actual_target}/{q} | `{decision}` |".format(
                batch=row["batch_id"],
                q=row["query_rows"],
                orig_top5=row["original_top5_success_rows"],
                exp_top5=row["expected_m78_top5_success_rows"],
                actual_top5=actual_top5,
                orig_target=row["original_target_detected_rows"],
                actual_target=actual_target,
                decision=row["remaining_batch_decision"],
            )
        )
    return "\n".join(
        [
            "# E005-M83 Confidence-Log-Depth Rerun Decision",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Selected route: `{coverage['selected_next_route']}`.",
            f"- Actual b02 top5 gain: {coverage['b02_actual_top5_delta_vs_original']} rows.",
            f"- Actual b02 target-detection gain: {coverage['b02_actual_target_detected_delta_vs_original']} rows.",
            f"- Expected aggregate detector top5 if all remaining fixed-policy gains are realized: {coverage['expected_all_batch_top5_success_rows']} / {coverage['query_rows']}.",
            f"- H001 real memory-trust policy: {coverage['h001_success_rows']} / {coverage['query_rows']}.",
            "",
            "## Batch Decision",
            "",
            *batch_lines,
            "",
            "## Claim Boundary",
            "",
            "- E005-M83 supports a limited detector-ranking repair diagnostic.",
            "- It does not support final real RGB-D/open-vocabulary robustness because target detection does not improve and detector-only performance remains far below H001.",
            "- Remaining detector reruns should not be launched before deciding whether a complete diagnostic row is worth the compute.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_batch_rows()
    original_total_top5 = sum(row["original_top5_success_rows"] for row in rows)
    expected_total_top5 = sum(row["expected_m78_top5_success_rows"] for row in rows)
    actual_b02 = next(row for row in rows if row["batch_id"] == "heldout_b02")
    partial_actual_top5 = sum(
        row["actual_top5_success_rows"]
        if row["actual_top5_success_rows"] is not None
        else row["original_top5_success_rows"]
        for row in rows
    )
    m75 = read_json(M75_DIR / "coverage.json")
    m78 = read_json(M78_DIR / "coverage.json")

    coverage = {
        "b02_actual_target_detected_delta_vs_original": actual_b02["actual_target_detected_delta_vs_original"],
        "b02_actual_top5_delta_vs_original": actual_b02["actual_top5_delta_vs_original"],
        "b02_actual_top5_matches_m78_expected": actual_b02["actual_top5_matches_m78_expected"],
        "deployable_search_policy_claim_ready": False,
        "expected_all_batch_top5_delta_vs_m75": expected_total_top5 - original_total_top5,
        "expected_all_batch_top5_success_rows": expected_total_top5,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_success_rows": int(m75.get("h001_success_rows", 0)),
        "m78_fixed_top5_success_rows": int(m78.get("fixed_top5_success_rows", expected_total_top5)),
        "next_recommended_unit": "E005-M84 prompt/label recall repair or external proposal baseline route decision",
        "partial_actual_top5_with_b02_rerun_only": partial_actual_top5,
        "query_rows": int(m75.get("query_rows", 195)),
        "real_navigation_sr_spl_claim_ready": False,
        "remaining_rerun_recommendation": {
            "heldout_b01": "skip_now_zero_top5_gain_expected",
            "heldout_b03": "skip_now_small_gain_only_if_complete_diagnostic_table_is_needed",
        },
        "selected_next_route": "stop_remaining_reruns_record_diagnostic_boundary_then_repair_recall_or_external_proposal",
        "status": "e005_m83_confidence_log_depth_rerun_decision_ready_limited_detector_ranking_gain",
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "batch_decision_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
