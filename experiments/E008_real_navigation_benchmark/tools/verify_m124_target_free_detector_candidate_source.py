#!/usr/bin/env python3
"""Verify E008-M124 target-free detector candidate-source generation."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
GENERIC_VERIFIER = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
M123_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
M121_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M124_target_free_source_coverage_detector_candidate_source_v0"
TMUX_SESSION = "e008_m124_target_free_detector"
VERSION = "e008_m124_target_free_detector_candidate_source_verifier_v0"


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def rewrite_status(generic_status: str, tmux_is_running: bool) -> str:
    if generic_status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready":
        return "e008_m124_target_free_detector_candidate_source_ready"
    if generic_status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_running" or tmux_is_running:
        return "e008_m124_target_free_detector_candidate_source_running"
    if generic_status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready_empty_or_no_coordinates":
        return "e008_m124_target_free_detector_candidate_source_ready_empty_or_no_coordinates"
    if not generic_status:
        return "e008_m124_target_free_detector_candidate_source_waiting_for_output"
    return "e008_m124_target_free_detector_candidate_source_failed_or_needs_review"


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M124 Target-Free Detector Candidate-Source Verification",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- tmux running: {coverage['tmux_running']}.",
            f"- Generic detector status: `{coverage.get('generic_detector_status')}`.",
            f"- Manifest rows: {coverage['manifest_rows']}.",
            f"- Detector sampled frames: {coverage['detector_sampled_frame_rows']}.",
            f"- Frames with written predictions: {coverage['frames_with_written_predictions']}.",
            f"- Raw / written predictions: {coverage['raw_prediction_count']} / {coverage['written_prediction_count']}.",
            f"- Prediction rows: {coverage['prediction_rows']}.",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}.",
            f"- Pre-cap candidate rows: {coverage['pre_cap_candidate_rows']}.",
            f"- Validator errors / warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M124 verifies detector candidate-source generation only.",
            "- M124 does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "- M124 uses the M123 depth-filtered 295-frame detector manifest; it does not claim full 320-frame render validity.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    generic_command = [
        "python",
        str(GENERIC_VERIFIER),
        "--m15-artifact-dir",
        str(M123_ARTIFACT_DIR),
        "--m15-data-dir",
        str(M121_DATA_DIR),
        "--m16-dir",
        str(args.artifact_dir),
        "--tmux-session",
        TMUX_SESSION,
    ]
    result = subprocess.run(generic_command, check=False, text=True, capture_output=True)
    generic = read_json(args.artifact_dir / "e008_m16_verification_coverage.json")
    manifest_rows = read_jsonl(M121_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    tmux_is_running = tmux_running(TMUX_SESSION)
    status = rewrite_status(str(generic.get("status", "")), tmux_is_running)
    ready = status == "e008_m124_target_free_detector_candidate_source_ready"
    coverage = {
        "version": VERSION,
        "status": status,
        "generic_detector_status": generic.get("status"),
        "generic_verifier_returncode": result.returncode,
        "generic_verifier_stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "generic_verifier_stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
        "artifact_output_root": str(args.artifact_dir),
        "data_input_root": str(M121_DATA_DIR),
        "tmux_session": TMUX_SESSION,
        "tmux_running": tmux_is_running,
        "manifest_rows": len(manifest_rows),
        "detector_sampled_frame_rows": sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows),
        "m123_status": read_json(M123_ARTIFACT_DIR / "coverage.json").get("status"),
        "m123_depth_filtered_detector_manifest_ready": read_json(M123_ARTIFACT_DIR / "coverage.json").get(
            "depth_filtered_detector_manifest_ready"
        ),
        "launch_status": read_json(args.artifact_dir / "e008_m124_launch_coverage.json").get("status"),
        "log_path": read_json(args.artifact_dir / "e008_m124_launch_coverage.json").get("log_path"),
        "frame_rows": int(generic.get("frame_rows", 0) or 0),
        "frames_with_written_predictions": int(generic.get("frames_with_written_predictions", 0) or 0),
        "raw_prediction_count": int(generic.get("raw_prediction_count", 0) or 0),
        "written_prediction_count": int(generic.get("written_prediction_count", 0) or 0),
        "prediction_rows": int(generic.get("prediction_rows", 0) or 0),
        "coordinate_candidate_rows": int(generic.get("coordinate_candidate_rows", 0) or 0),
        "pre_cap_candidate_rows": int(generic.get("pre_cap_candidate_rows", 0) or 0),
        "validator_error_rows": int(generic.get("validator_error_rows", 0) or 0),
        "validator_warning_rows": int(generic.get("validator_warning_rows", 0) or 0),
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E008-M125 target-free detector candidate navmesh/source-readiness validation"
        if ready
        else "wait for E008-M124 completion"
        if tmux_is_running
        else "inspect or repair E008-M124 detector candidate-source output",
    }
    route_rows = [
        {
            "claim": "target_free_detector_candidate_source",
            "ready": ready,
            "support_status": "supported" if ready else "not_supported",
            "reason": "Requires non-empty detector rows with valid centroid_world_m.",
        },
        {
            "claim": "real_navigation_sr_spl",
            "ready": False,
            "support_status": "blocked",
            "reason": "M124 is detector candidate generation only.",
        },
    ]
    write_json(args.artifact_dir / "e008_m124_verification_coverage.json", coverage)
    write_jsonl(args.artifact_dir / "e008_m124_route_decision_rows.jsonl", route_rows)
    write_text(args.artifact_dir / "e008_m124_verification_report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
