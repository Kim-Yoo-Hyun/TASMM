#!/usr/bin/env python3
"""Verify E008-M123 target-free render frame staging."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M15_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m15_non_oracle_observation_expansion_frame_staging.py"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
M123_LAUNCH_DIR = ARTIFACT_DIR
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
VERSION = "e008_m123_target_free_render_frame_staging_verifier_v0"
TMUX_SESSION = "e008_m123_target_free_render"


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


def load_m15_verifier():
    spec = importlib.util.spec_from_file_location("e008_m15_verify_tool", M15_VERIFY_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 verifier: {M15_VERIFY_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command_row() -> dict[str, Any]:
    rows = read_jsonl(M123_LAUNCH_DIR / "long_job_command_rows.jsonl")
    for row in rows:
        if row.get("job_id") == "E008-M123":
            return row
    return {}


def rewrite_status(old_status: str) -> str:
    if old_status == "e008_m15_non_oracle_observation_expansion_frame_staging_verified":
        return "e008_m123_target_free_render_frame_staging_verified"
    if old_status == "e008_m15_non_oracle_observation_expansion_frame_staging_verified_with_snap_warnings":
        return "e008_m123_target_free_render_frame_staging_verified_with_snap_warnings"
    return "e008_m123_target_free_render_frame_staging_verification_failed"


def frame_index(frame_id: str) -> int:
    return int(str(frame_id).replace("frame-", ""))


def detector_manifest_frame_status(data_out_dir: Path, frame_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_rows = read_jsonl(data_out_dir / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    ready_by_index: dict[int, bool] = {
        frame_index(str(row.get("frame_id"))): bool(row.get("frame_ready")) for row in frame_rows
    }
    invalid_rows: list[dict[str, Any]] = []
    total = 0
    ready = 0
    repaired_rows = 0
    for manifest in manifest_rows:
        repaired_rows += 1 if manifest.get("m123_depth_validity_repaired") else 0
        for index in [int(item) for item in manifest.get("sampled_frame_indices", [])]:
            total += 1
            if ready_by_index.get(index, False):
                ready += 1
            else:
                invalid_rows.append(
                    {
                        "frame_id": f"frame-{index:06d}",
                        "frame_index": index,
                        "manifest_route_id": manifest.get("route_id"),
                        "scan_id": manifest.get("scan_id"),
                    }
                )
    return {
        "detector_manifest_rows": len(manifest_rows),
        "detector_manifest_repaired_rows": repaired_rows,
        "detector_sampled_frame_rows": total,
        "detector_sampled_ready_frame_rows": ready,
        "detector_sampled_invalid_frame_rows": len(invalid_rows),
        "detector_sampled_invalid_rows": invalid_rows,
        "depth_filtered_detector_manifest_ready": bool(
            manifest_rows and total > 0 and repaired_rows == len(manifest_rows) and not invalid_rows
        ),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M123 Target-Free Render Frame Staging Verification",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Log path: `{coverage.get('log_path')}`.",
            f"- Output path: `{coverage['derived_output_root']}`.",
            f"- Expected frames: {coverage['expected_frame_rows']}.",
            f"- Ready frames: {coverage['ready_frame_rows']}.",
            f"- Detector sampled ready frames: {coverage['detector_sampled_ready_frame_rows']} / {coverage['detector_sampled_frame_rows']}.",
            f"- Depth-filtered detector manifest ready: {coverage['depth_filtered_detector_manifest_ready']}.",
            f"- Ready scans: {coverage['ready_scan_rows']} / {coverage['scan_rows']}.",
            f"- Snap validation rows: {coverage['snap_validation_rows']}.",
            f"- Snap-ready rows: {coverage['snap_ready_rows']}.",
            f"- Large snap warning rows: {coverage['large_snap_warning_rows']}.",
            f"- Detector input files ready: {coverage['detector_input_files_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M123 is the target-free rendered RGB-D frame staging gate.",
            "- If M123 fails, it does not support rendered-frame readiness.",
            "- If M123 passes only via depth-filtered detector manifest readiness, it supports detector-input readiness but not all-frame render validity.",
            "- M123 does not run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "",
            "## Next",
            "",
            "- If verified, launch E008-M124 detector candidate-source generation on the staged target-free frames.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--data-out-dir", type=Path, default=DATA_OUT_DIR)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    command = command_row()
    module = load_m15_verifier()
    module.ARTIFACT_DIR = args.artifact_dir
    module.DATA_OUT_DIR = args.data_out_dir
    module.VERSION = VERSION
    coverage = module.run()
    old_status = str(coverage.get("status"))
    frame_rows = read_jsonl(args.artifact_dir / "verification_frame_rows.jsonl")
    detector_status = detector_manifest_frame_status(args.data_out_dir, frame_rows)
    full_render_ready = old_status.startswith("e008_m15_non_oracle_observation_expansion_frame_staging_verified")
    depth_filtered_ready = bool(detector_status["depth_filtered_detector_manifest_ready"])
    ready = bool(full_render_ready or depth_filtered_ready)
    status = rewrite_status(old_status)
    if depth_filtered_ready and not full_render_ready:
        status = "e008_m123_target_free_render_frame_staging_verified_with_depth_filtered_frames"
    coverage.update(
        {
            "version": VERSION,
            "status": status,
            "artifact_output_root": str(args.artifact_dir),
            "derived_output_root": str(args.data_out_dir),
            "tmux_session": TMUX_SESSION,
            "tmux_running_after_verification": tmux_running(TMUX_SESSION),
            "log_path": command.get("log_path"),
            "launch_command": command.get("command"),
            "verification_command": command.get("verification_command"),
            "full_render_frame_staging_ready": full_render_ready,
            **{key: value for key, value in detector_status.items() if key != "detector_sampled_invalid_rows"},
            "selected_next_unit": "E008-M124 target-free source-coverage detector candidate-source background launch"
            if ready
            else "repair E008-M123 target-free render frame staging",
            "detector_candidate_rows_ready": False,
            "source_gap_recovery_evaluated": False,
            "trajectory_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "deployable_search_policy_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "human_intent_main_claim_ready": False,
        }
    )
    command_status_rows = [
        {
            "job_id": "E008-M123",
            "job_status": "completed_needs_downstream_detector" if ready else "failed_needs_repair",
            "completion_mode": "full_render_ready"
            if full_render_ready
            else "depth_filtered_detector_manifest_ready"
            if depth_filtered_ready
            else "not_ready",
            "tmux_session": TMUX_SESSION,
            "tmux_running_after_verification": tmux_running(TMUX_SESSION),
            "log_path": command.get("log_path"),
            "output_path": str(args.data_out_dir),
            "verification_command": command.get("verification_command"),
        }
    ]
    write_json(args.artifact_dir / "coverage.json", coverage)
    write_jsonl(args.artifact_dir / "job_status_rows.jsonl", command_status_rows)
    write_jsonl(args.artifact_dir / "detector_sampled_invalid_frame_rows.jsonl", detector_status["detector_sampled_invalid_rows"])
    write_text(args.artifact_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
