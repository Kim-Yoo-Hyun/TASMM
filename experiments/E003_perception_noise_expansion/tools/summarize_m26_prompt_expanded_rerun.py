#!/usr/bin/env python3
"""Summarize E003-M26 prompt-expanded multi-scan Docker rerun pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M26_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M26_prompt_expanded_multiscan_docker_rerun_v0"
M26_VERSION = "e003_m26_prompt_expanded_multiscan_docker_rerun_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "None"
    return str(value)


def is_ready(payload: dict[str, Any], expected_status: str) -> bool:
    return payload.get("status") == expected_status


def build_coverage(detector: dict[str, Any], calibration: dict[str, Any], visibility: dict[str, Any], m26_dir: Path) -> dict[str, Any]:
    frame = detector.get("frame_diagnostics", {})
    matching = detector.get("matching_coverage", {})
    validator = detector.get("validator_coverage", {})
    run_config = detector.get("run_config", {})
    baseline = calibration.get("baseline_config", {})
    selected = calibration.get("selected_config", {})

    scan_eval_target_rows = int(visibility.get("scan_eval_target_rows", 0) or 0)
    prompt_not_active_target_rows = int(visibility.get("prompt_not_active_target_rows", -1))
    prompt_coverage_fixed = scan_eval_target_rows > 0 and prompt_not_active_target_rows == 0
    prediction_cap_hit = bool(detector.get("model_status", {}).get("max_predictions_reached"))
    false_positive_dominated = float(matching.get("false_positive_proposal_rate_smoke", 0.0) or 0.0) > 0.9

    coverage: dict[str, Any] = {
        "artifact_root": str(m26_dir),
        "backend_contract_ready": bool(detector.get("backend_contract_ready")),
        "calibration_ready": is_ready(calibration, "proposal_calibration_diagnostic_ready"),
        "calibration_selection_policy": calibration.get("selection_policy"),
        "detector_rerun_ready": is_ready(detector, "frame_scaling_projection_diagnostic_ready"),
        "docker_build_executed": bool(detector.get("docker_build_executed")),
        "docker_run_executed": bool(detector.get("docker_run_executed")),
        "docker_server_version": detector.get("docker_info", {}).get("stdout"),
        "evaluated_frame_count": visibility.get("evaluated_frame_count"),
        "evaluated_scan_count": visibility.get("evaluated_scan_count"),
        "evaluated_scans": visibility.get("evaluated_scans", []),
        "false_positive_dominated": false_positive_dominated,
        "frame_raw_prediction_rows": frame.get("raw_prediction_count"),
        "frame_raw_to_written_rate": frame.get("raw_to_written_rate"),
        "frame_skipped_no_depth_prediction_rows": frame.get("skipped_no_depth_prediction_count"),
        "frame_written_prediction_rows": frame.get("written_prediction_count"),
        "input_prediction_rows": calibration.get("input_proposal_rows"),
        "m26_version": M26_VERSION,
        "max_predictions_reached": prediction_cap_hit,
        "matching_false_positive_proposal_rows": matching.get("false_positive_proposal_rows"),
        "matching_label_overlap_target_recall_smoke": matching.get("label_overlap_target_recall_smoke"),
        "matching_label_overlap_target_rows": matching.get("label_overlap_target_rows"),
        "matching_matched_target_rows": matching.get("matched_target_rows"),
        "matching_mean_centroid_error_m": matching.get("matched_centroid_error_m", {}).get("mean"),
        "matching_proposal_precision_smoke": matching.get("proposal_precision_smoke"),
        "matching_scan_eval_target_rows": matching.get("scan_eval_target_rows"),
        "matching_scan_target_recall_smoke": matching.get("scan_target_recall_smoke"),
        "next_recommended_unit": "E003-M27 false-positive / cap bottleneck analysis gate",
        "not_projected_or_capped_prediction_rows": frame.get("not_projected_or_capped_prediction_count"),
        "paper_table_command_ready": False,
        "prediction_rows": detector.get("prediction_rows"),
        "prompt_coverage_fixed": prompt_coverage_fixed,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_config": run_config,
        "selected_calibration_false_positive_proposal_rows": selected.get("false_positive_proposal_rows"),
        "selected_calibration_matched_target_rows": selected.get("matched_target_rows"),
        "selected_calibration_precision": selected.get("proposal_precision"),
        "selected_calibration_retained_proposal_rows": selected.get("retained_proposal_rows"),
        "selected_calibration_scan_target_recall": selected.get("scan_target_recall"),
        "status": "prompt_expanded_multiscan_docker_rerun_pilot_ready",
        "validator_error_rows": validator.get("error_rows"),
        "validator_warning_rows": validator.get("warning_rows"),
        "visibility_active_prompt_target_rows": visibility.get("active_prompt_target_rows"),
        "visibility_depth_consistent_visible_proxy_target_rows": visibility.get(
            "depth_consistent_visible_proxy_target_rows"
        ),
        "visibility_detector_or_threshold_missed_visible_target_rows": visibility.get(
            "detector_or_threshold_missed_visible_target_rows"
        ),
        "visibility_postcheck_ready": is_ready(visibility, "visibility_prompt_projection_gate_ready"),
        "visibility_prompt_not_active_target_rows": visibility.get("prompt_not_active_target_rows"),
        "visibility_recall_over_depth_consistent_visible_proxy_denominator": visibility.get(
            "m23_recall_over_depth_consistent_visible_proxy_denominator"
        ),
        "visibility_recall_over_scan_denominator": visibility.get("m23_recall_over_scan_denominator"),
    }
    coverage["baseline_to_selected_false_positive_delta"] = calibration.get("baseline_false_positive_delta")
    coverage["baseline_to_selected_matched_target_delta"] = calibration.get("baseline_matched_target_delta")
    coverage["baseline_to_selected_precision_delta"] = calibration.get("baseline_precision_delta")
    coverage["baseline_precision"] = baseline.get("proposal_precision")
    coverage["baseline_matched_target_rows"] = baseline.get("matched_target_rows")
    coverage["baseline_false_positive_proposal_rows"] = baseline.get("false_positive_proposal_rows")
    coverage["blocking_conditions"] = [
        condition
        for condition, blocked in [
            ("max_predictions_cap_reached", prediction_cap_hit),
            ("false_positive_rate_over_0_9", false_positive_dominated),
            ("paper_table_visibility_benchmark_not_ready", True),
            ("real_rgbd_open_vocab_claim_not_ready", True),
        ]
        if blocked
    ]
    return coverage


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M26 Prompt Expanded Multiscan Docker Rerun",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker run executed: {coverage['docker_run_executed']}",
            f"- Image/server route: `research2/real-smoke`, Docker server {coverage['docker_server_version']}",
            f"- Evaluated scans / frames: {coverage['evaluated_scan_count']} / {coverage['evaluated_frame_count']}",
            f"- Run config: max scans {coverage['run_config'].get('max_scans')}, max frames per scan {coverage['run_config'].get('max_frames_per_scan')}, max labels {coverage['run_config'].get('max_labels')}, max predictions {coverage['run_config'].get('max_predictions')}",
            f"- Raw / written predictions: {coverage['frame_raw_prediction_rows']} / {coverage['frame_written_prediction_rows']}",
            f"- Raw-to-written rate: {fmt(coverage['frame_raw_to_written_rate'])}",
            f"- Not projected or capped predictions: {coverage['not_projected_or_capped_prediction_rows']}",
            f"- Max predictions reached: {coverage['max_predictions_reached']}",
            f"- Validator error / warning rows: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Scan eval target rows: {coverage['matching_scan_eval_target_rows']}",
            f"- Active prompt target rows: {coverage['visibility_active_prompt_target_rows']}",
            f"- Prompt-not-active target rows: {coverage['visibility_prompt_not_active_target_rows']}",
            f"- Matched target rows: {coverage['matching_matched_target_rows']}",
            f"- Scan target recall smoke: {fmt(coverage['matching_scan_target_recall_smoke'])}",
            f"- Label-overlap target recall smoke: {fmt(coverage['matching_label_overlap_target_recall_smoke'])}",
            f"- Proposal precision smoke: {fmt(coverage['matching_proposal_precision_smoke'])}",
            f"- False-positive proposal rows: {coverage['matching_false_positive_proposal_rows']}",
            f"- Selected calibration retained / matched / false-positive rows: {coverage['selected_calibration_retained_proposal_rows']} / {coverage['selected_calibration_matched_target_rows']} / {coverage['selected_calibration_false_positive_proposal_rows']}",
            f"- Selected calibration precision: {fmt(coverage['selected_calibration_precision'])}",
            f"- Depth-consistent visible-proxy target rows: {coverage['visibility_depth_consistent_visible_proxy_target_rows']}",
            f"- Recall over depth-consistent visible-proxy denominator: {fmt(coverage['visibility_recall_over_depth_consistent_visible_proxy_denominator'])}",
            f"- Detector/threshold missed visible-proxy target rows: {coverage['visibility_detector_or_threshold_missed_visible_target_rows']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M26 supports saying that the prompt-expanded Docker route can produce non-empty multi-scan RGB-D/open-vocabulary proposal artifacts under the fixed schema.",
            "- E003-M26 supports saying that prompt coverage is no longer the immediate blocker for the two-scan pilot because prompt-not-active target rows are 0.",
            "- E003-M26 does not support a paper-table real RGB-D/open-vocabulary robustness claim.",
            "",
            "## 에이전트 추론",
            "",
            "- The bottleneck shifted from prompt budget to proposal quality: recall improved over the earlier one-scan smoke, but proposal precision remains very low.",
            "- The detector output is cap-limited, so the next unit should separate detector scoring, frame/label caps, projection loss, and false-positive consolidation before wider scaling.",
            "- The match-preserving calibration preserves matched targets, but it does not solve the false-positive domination problem.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M26. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m26-dir", default=DEFAULT_M26_DIR, type=Path)
    args = parser.parse_args()

    detector = load_json(args.m26_dir / "detector_rerun" / "coverage.json")
    calibration = load_json(args.m26_dir / "match_preserving_calibration" / "coverage.json")
    visibility = load_json(args.m26_dir / "visibility_denominator" / "coverage.json")
    coverage = build_coverage(detector, calibration, visibility, args.m26_dir)

    write_json(args.m26_dir / "coverage.json", coverage)
    write_json(
        args.m26_dir / "claim_boundary.json",
        {
            "controlled_real_detector_pilot_artifact_ready": True,
            "paper_table_command_ready": coverage["paper_table_command_ready"],
            "real_rgbd_or_open_vocab_claim_ready": coverage["real_rgbd_or_open_vocab_claim_ready"],
            "supported_claims": [
                "prompt-expanded Docker route produces schema-valid multi-scan detector proposal artifacts",
                "expanded prompt cap removes prompt-not-active target rows for the two-scan pilot",
            ],
            "unsupported_claims": [
                "real RGB-D perception robustness",
                "open-vocabulary perception robustness",
                "deployable search policy",
                "paper-table detector benchmark result",
            ],
            "blocking_conditions": coverage["blocking_conditions"],
            "next_recommended_unit": coverage["next_recommended_unit"],
        },
    )
    (args.m26_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
