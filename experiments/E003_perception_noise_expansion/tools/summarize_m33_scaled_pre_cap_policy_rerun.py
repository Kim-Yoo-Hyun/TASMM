#!/usr/bin/env python3
"""Summarize E003-M33 scaled pre-cap policy Docker rerun."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M32_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M32_scaled_pre_cap_rerun_gate_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
M33_VERSION = "e003_m33_scaled_pre_cap_policy_docker_rerun_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def mtime_runtime_seconds(start_path: Path, end_path: Path) -> int | None:
    if not start_path.exists() or not end_path.exists():
        return None
    return max(0, int(round(end_path.stat().st_mtime - start_path.stat().st_mtime)))


def iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def top_label_counts(label_rows_path: Path, limit: int = 8) -> list[dict[str, Any]]:
    rows = load_jsonl(label_rows_path) if label_rows_path.exists() else []
    normalized = []
    for row in rows:
        label = row.get("label", row.get("label_canonical"))
        if "false_positive_proposal_rows" in row:
            false_positive_rows = row.get("false_positive_proposal_rows", 0)
        elif "false_positive_rows" in row:
            false_positive_rows = row.get("false_positive_rows", 0)
        else:
            false_positive_rows = int(row.get("detector_proposal_rows", 0) or 0) - int(row.get("matched_proposal_rows", 0) or 0)
        matched_target_rows = row.get("matched_target_rows", 0)
        if label is None:
            continue
        normalized.append(
            {
                "false_positive_proposal_rows": int(false_positive_rows or 0),
                "label": str(label),
                "matched_target_rows": int(matched_target_rows or 0),
            }
        )
    return sorted(normalized, key=lambda item: (-item["false_positive_proposal_rows"], item["label"]))[:limit]


def build_report(coverage: dict[str, Any]) -> str:
    top_false_positive_text = ", ".join(
        f"{row['label']} {row['false_positive_proposal_rows']}"
        for row in coverage["top_false_positive_labels"]
    )
    return "\n".join(
        [
            "# E003-M33 Scaled Pre Cap Policy Docker Rerun",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker run executed: {coverage['docker_run_executed']}",
            f"- Estimated detector wall time seconds: {coverage['estimated_detector_wall_time_seconds']}",
            f"- Evaluated scans / frames: {coverage['evaluated_scan_count']} / {coverage['evaluated_frame_count']}",
            f"- Evaluation target rows: {coverage['scan_eval_target_rows']}",
            f"- Raw predictions: {coverage['raw_prediction_count']}",
            f"- Projected candidates: {coverage['projected_candidate_count']}",
            f"- Policy input candidates: {coverage['policy_input_candidate_count']}",
            f"- Spatial consolidated candidates: {coverage['spatial_consolidated_candidate_count']}",
            f"- Final prediction rows: {coverage['final_prediction_rows']}",
            f"- Raw candidate cap reached: {coverage['raw_candidate_collection_cap_reached']}",
            f"- Max predictions reached after policy: {coverage['max_predictions_reached_after_policy']}",
            f"- Validator errors/warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matched target rows: {coverage['matched_target_rows']}",
            f"- False-positive proposal rows: {coverage['false_positive_proposal_rows']}",
            f"- Proposal precision: {coverage['proposal_precision']}",
            f"- Scan target recall: {coverage['scan_target_recall']}",
            f"- Depth-consistent visible-proxy target rows: {coverage['depth_consistent_visible_proxy_target_rows']}",
            f"- Recall over depth-consistent visible-proxy denominator: {coverage['recall_over_depth_consistent_visible_proxy_denominator']}",
            f"- Detector/threshold missed visible-proxy target rows: {coverage['detector_or_threshold_missed_visible_target_rows']}",
            f"- Calibration changed selected proposals: {coverage['calibration_changed_selected_proposals']}",
            f"- Top false-positive labels: {top_false_positive_text}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M33 supports that the Dockerized `cap_aware_label_balanced_ranking_v0` route can scale from the two-scan pilot to 8 staged `3RScan` scans under a fixed output schema.",
            "- E003-M33 supports a scaled diagnostic result, not a final real RGB-D/open-vocabulary robustness claim.",
            "- E003-M33 does not support a deployable perception/search claim because false-positive load remains high and visibility is still a centroid/depth proxy.",
            "",
            "## 에이전트 추론",
            "",
            "- The scaled run improves the denominator size enough for label-level failure analysis, but proposal precision remains low.",
            "- Match-preserving calibration selected the baseline-like config, so simple confidence/depth/NMS filtering did not reduce false positives without risking matched target loss.",
            "- The next unit should analyze M33 false-positive labels, visible-proxy misses, and M31 blocker resolution before any paper-table claim.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M33. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m32-dir", default=DEFAULT_M32_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    args = parser.parse_args()

    detector_dir = args.m33_dir / "detector_rerun"
    calibration_dir = args.m33_dir / "match_preserving_calibration"
    visibility_dir = args.m33_dir / "visibility_denominator"
    detector_coverage = load_json(detector_dir / "coverage.json")
    calibration_coverage = load_json(calibration_dir / "coverage.json")
    visibility_coverage = load_json(visibility_dir / "coverage.json")
    m32_coverage = load_json(args.m32_dir / "coverage.json")

    frame = detector_coverage.get("frame_diagnostics", {})
    matching = detector_coverage.get("matching_coverage", {})
    pre_cap = detector_coverage.get("pre_cap_policy_summary", {})
    selected_config = calibration_coverage.get("selected_config", {})
    baseline_config = calibration_coverage.get("baseline_config", {})
    runtime_seconds = mtime_runtime_seconds(
        detector_dir / "container_output" / "backend_contract.json",
        detector_dir / "coverage.json",
    )

    final_prediction_rows = int(pre_cap.get("final_prediction_rows", detector_coverage.get("prediction_rows", 0)) or 0)
    selected_retained = int(selected_config.get("retained_proposal_rows", 0) or 0)
    baseline_retained = int(baseline_config.get("retained_proposal_rows", 0) or 0)
    coverage = {
        "backend_contract_ready": bool(detector_coverage.get("backend_contract_ready")),
        "calibration_changed_selected_proposals": selected_retained != baseline_retained,
        "calibration_selected_confidence_threshold": selected_config.get("confidence_threshold"),
        "calibration_selected_min_depth_pixels": selected_config.get("min_depth_pixels"),
        "calibration_selected_nms_radius_m": selected_config.get("nms_radius_m"),
        "detector_end_time": iso_mtime(detector_dir / "coverage.json"),
        "detector_or_threshold_missed_visible_target_rows": visibility_coverage.get("detector_or_threshold_missed_visible_target_rows"),
        "detector_start_proxy_time": iso_mtime(detector_dir / "container_output" / "backend_contract.json"),
        "docker_build_executed": bool(detector_coverage.get("docker_build_executed")),
        "docker_run_executed": bool(detector_coverage.get("docker_run_executed")),
        "estimated_detector_wall_time_seconds": runtime_seconds,
        "evaluated_frame_count": int(visibility_coverage.get("evaluated_frame_count", frame.get("scanned_frame_count", 0)) or 0),
        "evaluated_scan_count": int(visibility_coverage.get("evaluated_scan_count", 0) or 0),
        "false_positive_proposal_rows": int(matching.get("false_positive_proposal_rows", 0) or 0),
        "final_prediction_rows": final_prediction_rows,
        "final_to_raw_rate": safe_rate(final_prediction_rows, int(pre_cap.get("raw_prediction_count", frame.get("raw_prediction_count", 0)) or 0)),
        "m32_estimated_final_prediction_rows": m32_coverage.get("estimated_final_prediction_rows"),
        "m32_estimated_raw_predictions": m32_coverage.get("estimated_raw_predictions"),
        "m33_version": M33_VERSION,
        "matched_target_rows": int(matching.get("matched_target_rows", 0) or 0),
        "max_predictions_reached_after_policy": bool(pre_cap.get("max_predictions_reached_after_policy")),
        "next_recommended_unit": "E003-M34 scaled pre-cap failure and label analysis",
        "paper_table_command_ready": False,
        "policy_input_candidate_count": int(pre_cap.get("policy_input_candidate_count", 0) or 0),
        "projected_candidate_count": int(pre_cap.get("projected_candidate_count", 0) or 0),
        "proposal_precision": matching.get("proposal_precision_smoke"),
        "raw_candidate_collection_cap_reached": bool(pre_cap.get("raw_candidate_collection_cap_reached")),
        "raw_prediction_count": int(pre_cap.get("raw_prediction_count", frame.get("raw_prediction_count", 0)) or 0),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "recall_over_depth_consistent_visible_proxy_denominator": visibility_coverage.get("m22_recall_over_depth_consistent_visible_proxy_denominator"),
        "run_config": detector_coverage.get("run_config", {}),
        "scan_eval_target_rows": int(visibility_coverage.get("scan_eval_target_rows", 0) or 0),
        "scan_target_recall": matching.get("scan_target_recall_smoke"),
        "selected_route": m32_coverage.get("selected_route"),
        "skipped_no_depth_prediction_count": int(pre_cap.get("skipped_no_depth_prediction_count", frame.get("skipped_no_depth_prediction_count", 0)) or 0),
        "spatial_consolidated_candidate_count": int(pre_cap.get("spatial_consolidated_candidate_count", 0) or 0),
        "status": "scaled_pre_cap_policy_docker_rerun_ready",
        "top_false_positive_labels": top_label_counts(calibration_dir / "selected_label_metrics.jsonl"),
        "validator_error_rows": int(detector_coverage.get("validator_error_rows", 0) or 0),
        "validator_warning_rows": int(detector_coverage.get("validator_warning_rows", 0) or 0),
        "visibility_proxy_is_true_visibility": bool(visibility_coverage.get("visibility_proxy_is_true_visibility")),
        "depth_consistent_visible_proxy_target_rows": int(visibility_coverage.get("depth_consistent_visible_proxy_target_rows", 0) or 0),
    }

    write_json(args.m33_dir / "coverage.json", coverage)
    (args.m33_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
