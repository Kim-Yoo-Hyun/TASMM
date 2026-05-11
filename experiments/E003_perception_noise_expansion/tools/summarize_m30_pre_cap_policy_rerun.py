#!/usr/bin/env python3
"""Summarize E003-M30 pre-cap policy Docker rerun pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M26_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M26_prompt_expanded_multiscan_docker_rerun_v0"
DEFAULT_M28_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M28_cap_aware_label_balanced_policy_v0"
DEFAULT_M30_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M30_pre_cap_policy_docker_rerun_v0"
M30_VERSION = "e003_m30_pre_cap_policy_docker_rerun_v0"


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


def ready(payload: dict[str, Any], status: str) -> bool:
    return payload.get("status") == status


def build_coverage(
    detector: dict[str, Any],
    calibration: dict[str, Any],
    visibility: dict[str, Any],
    m26: dict[str, Any],
    m28: dict[str, Any],
    m30_dir: Path,
) -> dict[str, Any]:
    frame = detector.get("frame_diagnostics", {})
    matching = detector.get("matching_coverage", {})
    run_config = detector.get("run_config", {})
    pre_cap = detector.get("pre_cap_policy_summary", {})
    selected = calibration.get("selected_config", {})
    baseline = calibration.get("baseline_config", {})
    m28_selected = m28.get("selected_policy", {})

    matched = int(matching.get("matched_target_rows", 0) or 0)
    m26_matched = int(m26.get("matching_matched_target_rows", 0) or 0)
    false_positive = int(matching.get("false_positive_proposal_rows", 0) or 0)
    m26_false_positive = int(m26.get("matching_false_positive_proposal_rows", 0) or 0)
    precision = matching.get("proposal_precision_smoke")
    m26_precision = m26.get("matching_proposal_precision_smoke")

    coverage: dict[str, Any] = {
        "artifact_root": str(m30_dir),
        "backend_contract_ready": bool(detector.get("backend_contract_ready")),
        "calibration_ready": ready(calibration, "proposal_calibration_diagnostic_ready"),
        "candidate_selection_policy": run_config.get("candidate_selection_policy"),
        "detector_rerun_ready": ready(detector, "frame_scaling_projection_diagnostic_ready"),
        "docker_build_executed": bool(detector.get("docker_build_executed")),
        "docker_run_executed": bool(detector.get("docker_run_executed")),
        "evaluated_frame_count": visibility.get("evaluated_frame_count"),
        "evaluated_scan_count": visibility.get("evaluated_scan_count"),
        "frame_raw_prediction_rows": frame.get("raw_prediction_count"),
        "frame_written_prediction_rows": frame.get("written_prediction_count"),
        "m26_baseline": {
            "false_positive_proposal_rows": m26_false_positive,
            "matched_target_rows": m26_matched,
            "proposal_precision_smoke": m26_precision,
            "written_prediction_rows": m26.get("frame_written_prediction_rows"),
        },
        "m28_replay_selected_policy": {
            "false_positive_proposal_rows": m28_selected.get("false_positive_proposal_rows"),
            "matched_target_rows": m28_selected.get("matched_target_rows"),
            "proposal_precision": m28_selected.get("proposal_precision"),
            "proposal_rows": m28_selected.get("proposal_rows"),
        },
        "m30_version": M30_VERSION,
        "matched_target_delta_vs_m26": matched - m26_matched,
        "matching_false_positive_proposal_rows": false_positive,
        "matching_label_overlap_target_recall_smoke": matching.get("label_overlap_target_recall_smoke"),
        "matching_matched_target_rows": matched,
        "matching_proposal_precision_smoke": precision,
        "matching_scan_target_recall_smoke": matching.get("scan_target_recall_smoke"),
        "max_predictions_reached_after_policy": pre_cap.get("max_predictions_reached_after_policy"),
        "next_recommended_unit": "E003-M31 pre-cap policy failure/recall tradeoff analysis",
        "paper_table_command_ready": False,
        "pre_cap_policy_applied": bool(detector.get("pre_cap_policy_applied")),
        "pre_cap_policy_summary": pre_cap,
        "precision_delta_vs_m26": (
            float(precision) - float(m26_precision)
            if precision is not None and m26_precision is not None
            else None
        ),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_config": run_config,
        "selected_calibration_false_positive_proposal_rows": selected.get("false_positive_proposal_rows"),
        "selected_calibration_matched_target_rows": selected.get("matched_target_rows"),
        "selected_calibration_precision": selected.get("proposal_precision"),
        "selected_calibration_retained_proposal_rows": selected.get("retained_proposal_rows"),
        "status": "pre_cap_policy_docker_rerun_pilot_ready",
        "validator_error_rows": detector.get("validator_error_rows"),
        "validator_warning_rows": detector.get("validator_warning_rows"),
        "visibility_depth_consistent_visible_proxy_target_rows": visibility.get(
            "depth_consistent_visible_proxy_target_rows"
        ),
        "visibility_prompt_not_active_target_rows": visibility.get("prompt_not_active_target_rows"),
        "visibility_recall_over_depth_consistent_visible_proxy_denominator": visibility.get(
            "m23_recall_over_depth_consistent_visible_proxy_denominator"
        ),
    }
    coverage["false_positive_delta_vs_m26"] = false_positive - m26_false_positive
    coverage["selected_calibration_delta_vs_detector_precision"] = (
        float(selected["proposal_precision"]) - float(baseline["proposal_precision"])
        if selected.get("proposal_precision") is not None and baseline.get("proposal_precision") is not None
        else None
    )
    coverage["claim_blockers"] = [
        blocker
        for blocker, blocked in [
            ("paper_table_visibility_benchmark_not_ready", True),
            ("real_rgbd_open_vocab_claim_not_ready", True),
            ("pre_cap_policy_recall_tradeoff_needs_analysis", True),
            ("detector_result_is_two_scan_pilot_only", True),
        ]
        if blocked
    ]
    return coverage


def build_report(coverage: dict[str, Any]) -> str:
    pre_cap = coverage["pre_cap_policy_summary"]
    return "\n".join(
        [
            "# E003-M30 Pre Cap Policy Docker Rerun",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker run executed: {coverage['docker_run_executed']}",
            f"- Candidate selection policy: `{coverage['candidate_selection_policy']}`",
            f"- Pre-cap policy applied: {coverage['pre_cap_policy_applied']}",
            f"- Raw predictions: {coverage['frame_raw_prediction_rows']}",
            f"- Projected candidates: {pre_cap.get('projected_candidate_count')}",
            f"- Policy input candidates: {pre_cap.get('policy_input_candidate_count')}",
            f"- Spatial consolidated candidates: {pre_cap.get('spatial_consolidated_candidate_count')}",
            f"- Final written predictions: {coverage['frame_written_prediction_rows']}",
            f"- Max predictions reached after policy: {coverage['max_predictions_reached_after_policy']}",
            f"- Validator error / warning rows: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- M26 matched target rows: {coverage['m26_baseline']['matched_target_rows']}",
            f"- M30 matched target rows: {coverage['matching_matched_target_rows']}",
            f"- Matched target delta vs M26: {coverage['matched_target_delta_vs_m26']}",
            f"- M26 false-positive rows: {coverage['m26_baseline']['false_positive_proposal_rows']}",
            f"- M30 false-positive rows: {coverage['matching_false_positive_proposal_rows']}",
            f"- False-positive delta vs M26: {coverage['false_positive_delta_vs_m26']}",
            f"- M26 proposal precision: {fmt(coverage['m26_baseline']['proposal_precision_smoke'])}",
            f"- M30 proposal precision: {fmt(coverage['matching_proposal_precision_smoke'])}",
            f"- Precision delta vs M26: {fmt(coverage['precision_delta_vs_m26'])}",
            f"- Selected calibration retained / matched / false-positive rows: {coverage['selected_calibration_retained_proposal_rows']} / {coverage['selected_calibration_matched_target_rows']} / {coverage['selected_calibration_false_positive_proposal_rows']}",
            f"- Selected calibration precision: {fmt(coverage['selected_calibration_precision'])}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M30 supports saying the pre-cap policy can be executed inside the Docker detector runner under the fixed M26 pilot conditions.",
            "- E003-M30 does not support a final real RGB-D/open-vocabulary robustness claim because this is still a two-scan pilot and needs failure/recall tradeoff analysis.",
            "",
            "## 에이전트 추론",
            "",
            "- The key comparison is M30 vs M26, not M30 alone, because M26 fixed prompt coverage but was cap/false-positive dominated.",
            "- If M30 reduces false positives while preserving most M26 matches, the next unit should analyze which labels/frames/targets account for the remaining recall loss.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M30. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m26-dir", default=DEFAULT_M26_DIR, type=Path)
    parser.add_argument("--m28-dir", default=DEFAULT_M28_DIR, type=Path)
    parser.add_argument("--m30-dir", default=DEFAULT_M30_DIR, type=Path)
    args = parser.parse_args()

    detector = load_json(args.m30_dir / "detector_rerun" / "coverage.json")
    calibration = load_json(args.m30_dir / "match_preserving_calibration" / "coverage.json")
    visibility = load_json(args.m30_dir / "visibility_denominator" / "coverage.json")
    m26 = load_json(args.m26_dir / "coverage.json")
    m28 = load_json(args.m28_dir / "coverage.json")
    coverage = build_coverage(detector, calibration, visibility, m26, m28, args.m30_dir)

    write_json(args.m30_dir / "coverage.json", coverage)
    write_json(
        args.m30_dir / "claim_boundary.json",
        {
            "paper_table_command_ready": coverage["paper_table_command_ready"],
            "real_rgbd_or_open_vocab_claim_ready": coverage["real_rgbd_or_open_vocab_claim_ready"],
            "supported_claims": [
                "pre-cap policy executes inside Docker detector runner under fixed M26 pilot conditions",
                "schema-valid pre-cap policy outputs can be matched against the M17 target denominator",
            ],
            "unsupported_claims": [
                "real RGB-D perception robustness",
                "open-vocabulary perception robustness",
                "deployable search policy",
                "paper-table detector benchmark result",
            ],
            "claim_blockers": coverage["claim_blockers"],
            "next_recommended_unit": coverage["next_recommended_unit"],
        },
    )
    (args.m30_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
