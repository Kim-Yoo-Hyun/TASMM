#!/usr/bin/env python3
"""Launch E008-M16 non-oracle observation expansion detector candidate smoke."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M15_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
M15_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
M16_DIR = EXP_ROOT / "artifacts" / "E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0"
RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
TMUX_SESSION = "e008_m16_hm3d_expanded_detector"
LOG_DIR = ROOT / "logs"
VERSION = "e008_m16_non_oracle_observation_expansion_detector_launcher_v0"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def materialize_detector_inputs(m15_data_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Create an E008-M16 detector input directory with explicit frame indices."""
    source_input_dir = m15_data_dir / "detector_inputs"
    input_dir = out_dir / "detector_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)

    source_manifest_rows = read_jsonl(source_input_dir / "real_proposal_query_manifest.jsonl")
    source_target_rows = read_jsonl(source_input_dir / "real_proposal_object_targets.jsonl")
    render_rows = read_jsonl(m15_data_dir / "render_inputs" / "render_plan_rows.jsonl")
    frame_indices_by_scan: dict[str, list[int]] = {}
    for row in render_rows:
        scan_id = str(row.get("scan_id"))
        frame_index = row.get("frame_index")
        if frame_index is None:
            frame_id = str(row.get("frame_id", ""))
            try:
                frame_index = int(frame_id.replace("frame-", ""))
            except ValueError:
                continue
        frame_indices_by_scan.setdefault(scan_id, []).append(int(frame_index))

    manifest_rows = []
    for row in source_manifest_rows:
        scan_id = str(row.get("scan_id"))
        frame_indices = sorted(set(frame_indices_by_scan.get(scan_id, [])))
        target_labels = [str(label) for label in row.get("target_labels", []) if str(label)]
        patched = dict(row)
        patched["detector_config_id"] = "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0"
        patched["detector_target_count"] = len(target_labels)
        patched["evaluation_target_count"] = 0
        patched["frame_id_format"] = "frame-{index:06d}"
        patched["max_frames"] = len(frame_indices)
        patched["object_target_path"] = str(input_dir / "real_proposal_object_targets.jsonl")
        patched["prompt_set_path"] = str(input_dir / "prompt_set.json")
        patched["proposal_output_schema_path"] = str(input_dir / "proposal_output_schema.json")
        patched["sampled_frame_count"] = len(frame_indices)
        patched["sampled_frame_indices"] = frame_indices
        patched["version"] = "e008_m16_non_oracle_observation_expansion_detector_input_v0"
        manifest_rows.append(patched)

    target_rows = []
    for row in source_target_rows:
        patched = dict(row)
        patched.setdefault("detector_prompt_enabled", True)
        patched.setdefault("evaluation_target_enabled", False)
        patched.setdefault(
            "target_uid",
            f"e008-m16:{patched.get('scan_id')}:{patched.get('label_canonical')}",
        )
        patched["version"] = "e008_m16_non_oracle_observation_expansion_detector_input_v0"
        target_rows.append(patched)

    write_jsonl(input_dir / "real_proposal_query_manifest.jsonl", manifest_rows)
    write_jsonl(input_dir / "real_proposal_object_targets.jsonl", target_rows)
    for name in ["prompt_set.json", "proposal_output_schema.json"]:
        shutil.copy2(source_input_dir / name, input_dir / name)

    return {
        "detector_input_dir": str(input_dir),
        "manifest_rows": len(manifest_rows),
        "render_rows": len(render_rows),
        "target_rows": len(target_rows),
        "total_sampled_frame_indices": sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows),
    }


def command_status(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stderr": str(exc),
            "stdout": "",
        }
    return {
        "available": result.returncode == 0,
        "command": command,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "stdout": result.stdout.strip(),
    }


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(item) for item in command)


def build_detector_command(args: argparse.Namespace) -> list[str]:
    detector_input_dir = args.out_dir / "detector_inputs"
    return [
        "python",
        str(RUNNER),
        "--dataset-root",
        str(args.m15_data_dir),
        "--m17-dir",
        str(detector_input_dir),
        "--out-dir",
        str(args.out_dir),
        "--max-scans",
        str(args.max_scans),
        "--max-frames-per-scan",
        str(args.max_frames_per_scan),
        "--max-labels",
        str(args.max_labels),
        "--max-predictions",
        str(args.max_predictions),
        "--max-predictions-per-frame",
        str(args.max_predictions_per_frame),
        "--threshold",
        str(args.threshold),
        "--text-threshold",
        str(args.text_threshold),
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence_log_depth",
        "--pre-cap-per-scan-label-cap",
        str(args.pre_cap_per_scan_label_cap),
        "--pre-cap-spatial-consolidation-radius-m",
        str(args.pre_cap_spatial_consolidation_radius_m),
        "--raw-candidate-collection-cap",
        str(args.raw_candidate_collection_cap),
        "--export-pre-cap-candidate-pool",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m15-artifact-dir", type=Path, default=M15_ARTIFACT_DIR)
    parser.add_argument("--m15-data-dir", type=Path, default=M15_DATA_DIR)
    parser.add_argument("--out-dir", type=Path, default=M16_DIR)
    parser.add_argument("--tmux-session", default=TMUX_SESSION)
    parser.add_argument("--max-scans", type=int, default=6)
    parser.add_argument("--max-frames-per-scan", type=int, default=36)
    parser.add_argument("--max-labels", type=int, default=5)
    parser.add_argument("--max-predictions", type=int, default=12000)
    parser.add_argument("--max-predictions-per-frame", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.08)
    parser.add_argument("--text-threshold", type=float, default=0.08)
    parser.add_argument("--pre-cap-per-scan-label-cap", type=int, default=24)
    parser.add_argument("--pre-cap-spatial-consolidation-radius-m", type=float, default=0.5)
    parser.add_argument("--raw-candidate-collection-cap", type=int, default=100000)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    args.m15_artifact_dir = args.m15_artifact_dir.resolve()
    args.m15_data_dir = args.m15_data_dir.resolve()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    m15_coverage = read_json(args.m15_artifact_dir / "verification_coverage.json")
    detector_input_meta = materialize_detector_inputs(args.m15_data_dir, args.out_dir)
    detector_input_dir = args.out_dir / "detector_inputs"
    manifest_rows = read_jsonl(detector_input_dir / "real_proposal_query_manifest.jsonl")
    render_rows = read_jsonl(args.m15_data_dir / "render_inputs" / "render_plan_rows.jsonl")
    existing_coverage = read_json(args.out_dir / "coverage.json")
    docker_status = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    image_status = command_status(["docker", "image", "inspect", "research2/real-smoke:latest", "--format", "{{.Id}}"])
    tmux_is_running = tmux_running(args.tmux_session)

    blockers = []
    if not str(m15_coverage.get("status", "")).startswith(
        "e008_m15_non_oracle_observation_expansion_frame_staging_verified"
    ):
        blockers.append("m15_verification_not_ready")
    if len(manifest_rows) != args.max_scans:
        blockers.append(f"manifest_rows_mismatch:{len(manifest_rows)}!={args.max_scans}")
    if len(render_rows) < args.max_scans * args.max_frames_per_scan:
        blockers.append(f"render_rows_too_small:{len(render_rows)}")
    if not docker_status["available"]:
        blockers.append("docker_unavailable")
    if not image_status["available"]:
        blockers.append("research2_real_smoke_image_missing")
    if tmux_is_running and not args.force:
        blockers.append("tmux_session_already_running")
    if existing_coverage and existing_coverage.get("status") and not args.force:
        blockers.append("m16_existing_coverage_present_use_force_to_rerun")

    detector_command = build_detector_command(args)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e008_m16_hm3d_expanded_detector.log"
    shell_command = f"cd {shlex.quote(str(ROOT))} && {shell_join(detector_command)} > {shlex.quote(str(log_path))} 2>&1"
    tmux_command = ["tmux", "new-session", "-d", "-s", args.tmux_session, shell_command]

    launch_executed = False
    launch_result: dict[str, Any] = {"available": False, "returncode": None, "stderr": "", "stdout": ""}
    if not blockers:
        launch_result = command_status(tmux_command)
        launch_executed = bool(launch_result["available"])

    status = "e008_m16_detector_candidate_smoke_launched" if launch_executed else "e008_m16_detector_candidate_smoke_launch_blocked"
    if tmux_is_running and "tmux_session_already_running" in blockers:
        status = "e008_m16_detector_candidate_smoke_already_running"

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "launch_executed": launch_executed,
        "tmux_session": args.tmux_session,
        "tmux_running_before_launch": tmux_is_running,
        "log_path": str(log_path),
        "working_directory": str(ROOT),
        "output_path": str(args.out_dir),
        "detector_input_meta": detector_input_meta,
        "detector_input_path": str(detector_input_dir),
        "expected_files": [
            "coverage.json",
            "container_output/real_proposals.jsonl",
            "container_output/pre_cap_candidate_pool.jsonl",
            "validator/coverage.json",
            "matching/coverage.json",
        ],
        "verification_command": (
            "python experiments/E008_real_navigation_benchmark/tools/"
            "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py --require-ready"
        ),
        "detector_command": detector_command,
        "tmux_command": tmux_command,
        "docker_status": docker_status,
        "image_status": image_status,
        "launch_result": launch_result,
        "manifest_rows": len(manifest_rows),
        "render_plan_rows": len(render_rows),
        "m15_status": m15_coverage.get("status"),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
            m15_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
        ),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }

    command_rows = [
        {
            "job_id": "E008-M16",
            "status": status,
            "command": shell_command,
            "working_directory": str(ROOT),
            "output_path": str(args.out_dir),
            "log_path": str(log_path),
            "verification_command": coverage["verification_command"],
        }
    ]
    write_json(args.out_dir / "e008_m16_launch_coverage.json", coverage)
    write_jsonl(args.out_dir / "long_job_command_rows.jsonl", command_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed or status == "e008_m16_detector_candidate_smoke_already_running" else 2


if __name__ == "__main__":
    raise SystemExit(main())
