#!/usr/bin/env python3
"""Analyze E005-M93 batch-level active-label precedence effect."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M82_DIR = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0" / "heldout_b02"
M92_DIR = EXP_ROOT / "artifacts" / "E005-M92_active_label_precedence_next_step_v0"
M93_VERIFY_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_detector_verification_v0" / "heldout_b02"
M93_QUERY_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_query_metric_v0" / "heldout_b02"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_result_analysis_v0"
VERSION = "e005_m93_active_label_precedence_result_analysis_v0"
POLICIES = [
    "real_detector_confidence_top5_v0",
    "real_detector_task_budget_v0",
    "real_task_context_memory_trust_reobserve_v0",
    "real_context_agnostic_memory_trust_reobserve_v0",
    "real_static_memory_only_v0",
]
CONFLICT_SCAN_ID = "74ef846e-9dce-2d66-83d5-294aac7b1b0f"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def by_uid(rows: list[dict[str, Any]], key: str = "query_uid") -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows}


def policy_rows_by_uid(root: Path, policy: str) -> dict[str, dict[str, Any]]:
    return {
        str(row["query_uid"]): row
        for row in read_jsonl(root / "policy_rows.jsonl")
        if row.get("policy") == policy
    }


def counter_dict(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def build_delta_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    q82 = by_uid(read_jsonl(M82_DIR / "query_bridge_rows.jsonl"))
    q93 = by_uid(read_jsonl(M93_QUERY_DIR / "query_bridge_rows.jsonl"))
    missing = sorted(set(q82) ^ set(q93))
    if missing:
        raise RuntimeError(f"M82/M93 query uid mismatch: {missing[:5]}")

    policy82 = {policy: policy_rows_by_uid(M82_DIR, policy) for policy in POLICIES}
    policy93 = {policy: policy_rows_by_uid(M93_QUERY_DIR, policy) for policy in POLICIES}
    rows: list[dict[str, Any]] = []
    for query_uid in sorted(q82):
        before = q82[query_uid]
        after = q93[query_uid]
        row: dict[str, Any] = {
            "current_rescan_id": after["current_rescan_id"],
            "detection_gain": bool(not before["query_target_detected"] and after["query_target_detected"]),
            "detection_loss": bool(before["query_target_detected"] and not after["query_target_detected"]),
            "label_canonical": after["label_canonical"],
            "m82_target_detected": bool(before["query_target_detected"]),
            "m93_target_detected": bool(after["query_target_detected"]),
            "m93_target_rank": after.get("query_target_rank_by_real_detector_confidence"),
            "query_uid": query_uid,
            "row_band": after["row_band"],
            "target_uid": after["target_uid"],
            "task_context_id": after["task_context_id"],
        }
        for policy in POLICIES:
            b = policy82[policy][query_uid]
            a = policy93[policy][query_uid]
            row[f"{policy}_before"] = bool(b["query_bridge_success"])
            row[f"{policy}_after"] = bool(a["query_bridge_success"])
            row[f"{policy}_gain"] = bool(not b["query_bridge_success"] and a["query_bridge_success"])
            row[f"{policy}_loss"] = bool(b["query_bridge_success"] and not a["query_bridge_success"])
        rows.append(row)

    detection_gains = [row for row in rows if row["detection_gain"]]
    detection_losses = [row for row in rows if row["detection_loss"]]
    summary: dict[str, Any] = {
        "query_rows": len(rows),
        "detection_gain_rows": len(detection_gains),
        "detection_loss_rows": len(detection_losses),
        "detection_gain_by_scan": counter_dict(detection_gains, "current_rescan_id"),
        "detection_gain_by_label": counter_dict(detection_gains, "label_canonical"),
        "detection_gain_by_task_context": counter_dict(detection_gains, "task_context_id"),
        "detection_gain_by_row_band": counter_dict(detection_gains, "row_band"),
    }
    for policy in POLICIES:
        gains = [row for row in rows if row[f"{policy}_gain"]]
        losses = [row for row in rows if row[f"{policy}_loss"]]
        summary[f"{policy}_success_before"] = sum(1 for row in rows if row[f"{policy}_before"])
        summary[f"{policy}_success_after"] = sum(1 for row in rows if row[f"{policy}_after"])
        summary[f"{policy}_gain_rows"] = len(gains)
        summary[f"{policy}_loss_rows"] = len(losses)
        summary[f"{policy}_gain_by_label"] = counter_dict(gains, "label_canonical")
        summary[f"{policy}_loss_by_label"] = counter_dict(losses, "label_canonical")
    return rows, summary


def build_side_effect_rows(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for label in ("chair", "stool"):
        label_rows = [
            row
            for row in delta_rows
            if row["current_rescan_id"] == CONFLICT_SCAN_ID and row["label_canonical"] == label
        ]
        if not label_rows:
            continue
        rows.append(
            {
                "conflict_label": label,
                "current_rescan_id": CONFLICT_SCAN_ID,
                "detection_after": sum(1 for row in label_rows if row["m93_target_detected"]),
                "detection_before": sum(1 for row in label_rows if row["m82_target_detected"]),
                "detection_gain_rows": sum(1 for row in label_rows if row["detection_gain"]),
                "detection_loss_rows": sum(1 for row in label_rows if row["detection_loss"]),
                "h001_success_after": sum(
                    1 for row in label_rows if row["real_task_context_memory_trust_reobserve_v0_after"]
                ),
                "h001_success_before": sum(
                    1 for row in label_rows if row["real_task_context_memory_trust_reobserve_v0_before"]
                ),
                "query_rows": len(label_rows),
                "top5_success_after": sum(1 for row in label_rows if row["real_detector_confidence_top5_v0_after"]),
                "top5_success_before": sum(1 for row in label_rows if row["real_detector_confidence_top5_v0_before"]),
            }
        )
    return rows


def build_coverage(summary: dict[str, Any], side_effect_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m82_cov = read_json(M82_DIR / "coverage.json")
    m92_cov = read_json(M92_DIR / "coverage.json")
    m93_cov = read_json(M93_QUERY_DIR / "coverage.json")
    m93_verify = read_json(M93_VERIFY_DIR / "coverage.json")
    side_effect_detection_losses = sum(row["detection_loss_rows"] for row in side_effect_rows)
    side_effect_h001_losses = sum(
        max(0, int(row["h001_success_before"]) - int(row["h001_success_after"])) for row in side_effect_rows
    )
    return {
        "status": "e005_m93_active_label_precedence_result_analysis_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m82_query_target_detected_rows": m82_cov.get("query_target_detected_rows"),
        "m93_query_target_detected_rows": m93_cov.get("query_target_detected_rows"),
        "target_detection_gain_rows": summary["detection_gain_rows"],
        "target_detection_loss_rows": summary["detection_loss_rows"],
        "m82_detector_top5_success_rows": m82_cov.get("real_detector_top5_success_rows"),
        "m93_detector_top5_success_rows": m93_cov.get("real_detector_top5_success_rows"),
        "m82_detector_task_budget_success_rows": m82_cov.get("real_detector_task_budget_success_rows"),
        "m93_detector_task_budget_success_rows": m93_cov.get("real_detector_task_budget_success_rows"),
        "m82_h001_success_rows": m82_cov.get("real_h001_success_rows"),
        "m93_h001_success_rows": m93_cov.get("real_h001_success_rows"),
        "m93_verification_status": m93_verify.get("status"),
        "m93_query_metric_status": m93_cov.get("status"),
        "m93_prediction_rows": m93_verify.get("line_counts", {}).get("prediction_rows"),
        "m93_pre_cap_candidate_rows": m93_verify.get("line_counts", {}).get("pre_cap_candidate_rows"),
        "m93_cleanup_trace_rows": m93_verify.get("line_counts", {}).get("cleanup_trace_rows"),
        "m93_matched_target_rows": m93_verify.get("matching", {}).get("matched_target_rows"),
        "m93_scan_target_recall": m93_verify.get("matching", {}).get("scan_target_recall_smoke"),
        "m93_proposal_precision": m93_verify.get("matching", {}).get("proposal_precision_smoke"),
        "m92_side_effect_risk_query_rows": m92_cov.get("side_effect_risk_query_rows"),
        "side_effect_detection_loss_rows": side_effect_detection_losses,
        "side_effect_h001_loss_rows": side_effect_h001_losses,
        "side_effect_observed": bool(side_effect_detection_losses or side_effect_h001_losses),
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_route": "record_m93_as_batch_level_repair_diagnostic_no_final_robustness_claim",
        "next_recommended_unit": "E005-M94 claim-boundary update or broader repair decision",
    }


def build_report(coverage: dict[str, Any], summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M93 Active-Label Precedence Result Analysis",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Target detected rows: {coverage['m82_query_target_detected_rows']} -> {coverage['m93_query_target_detected_rows']}.",
            f"- Target detection gain/loss rows: {coverage['target_detection_gain_rows']} / {coverage['target_detection_loss_rows']}.",
            f"- Detector top5 success rows: {coverage['m82_detector_top5_success_rows']} -> {coverage['m93_detector_top5_success_rows']}.",
            f"- Detector task-budget success rows: {coverage['m82_detector_task_budget_success_rows']} -> {coverage['m93_detector_task_budget_success_rows']}.",
            f"- H001 success rows: {coverage['m82_h001_success_rows']} -> {coverage['m93_h001_success_rows']}.",
            f"- M93 matched targets / precision / recall: {coverage['m93_matched_target_rows']} / {coverage['m93_proposal_precision']} / {coverage['m93_scan_target_recall']}.",
            f"- Detection gain by scan: `{summary['detection_gain_by_scan']}`.",
            f"- Detection gain by label: `{summary['detection_gain_by_label']}`.",
            f"- Side-effect observed: {coverage['side_effect_observed']}.",
            f"- Selected next route: `{coverage['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M93 supports batch-level target-detection repair evidence for the active-label precedence fix.",
            "- M93 does not improve H001 memory-decision success on b02, so it should not be presented as the main method gain.",
            "- Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain unsupported.",
            "",
            "## Agent Inference",
            "",
            "- The repair is useful as a robustness and failure-boundary artifact: it recovers all 15 missed query rows from the zero-written scan without observed side-effect losses.",
            "- Since H001 success is unchanged, the paper story should keep this as detector/prompt bridge evidence, not a new semantic memory contribution.",
            "",
        ]
    )


def main() -> int:
    m93_cov = read_json(M93_QUERY_DIR / "coverage.json")
    if m93_cov.get("status") not in {
        "e005_m71_real_proposal_query_metric_ready_with_false_positive_boundary",
        "e005_m71_real_proposal_query_metric_ready_target_detection_weak",
    }:
        raise RuntimeError(f"M93 query metric is not ready: {m93_cov.get('status')}")
    delta_rows, summary = build_delta_rows()
    side_effect_rows = build_side_effect_rows(delta_rows)
    coverage = build_coverage(summary, side_effect_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "delta_rows.jsonl", delta_rows)
    write_jsonl(OUT_DIR / "side_effect_rows.jsonl", side_effect_rows)
    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, summary))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
