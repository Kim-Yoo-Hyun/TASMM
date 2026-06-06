#!/usr/bin/env python3
"""Launch E008-M124 target-free detector candidate-source generation in tmux."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M123_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
M121_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)
DETECTOR_INPUT_DIR = M121_DATA_DIR / "detector_inputs"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M124_target_free_source_coverage_detector_candidate_source_v0"
LOG_DIR = ROOT / "logs"
HF_CACHE = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "model_cache" / "huggingface"
RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
VERIFY_COMMAND = (
    "python experiments/E008_real_navigation_benchmark/tools/verify_m124_target_free_detector_candidate_source.py "
    "--require-ready"
)
TMUX_SESSION = "e008_m124_target_free_detector"
IMAGE_TAG = "research2/real-smoke"
VERSION = "e008_m124_target_free_detector_candidate_source_launch_v0"


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


def command_status(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return {"available": False, "command": command, "returncode": None, "stderr": str(exc), "stdout": ""}
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
    return " ".join(shlex.quote(str(item)) for item in command)


def detector_command() -> list[str]:
    return [
        "python",
        str(RUNNER),
        "--dataset-root",
        str(M121_DATA_DIR),
        "--m17-dir",
        str(DETECTOR_INPUT_DIR),
        "--out-dir",
        str(ARTIFACT_DIR),
        "--hf-cache",
        str(HF_CACHE),
        "--max-scans",
        "2",
        "--max-frames-per-scan",
        "192",
        "--max-labels",
        "1",
        "--max-predictions",
        "12000",
        "--max-predictions-per-frame",
        "100",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence_log_depth",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "100000",
        "--export-pre-cap-candidate-pool",
    ]


def build_preflight_rows() -> list[dict[str, Any]]:
    m123 = read_json(M123_ARTIFACT_DIR / "coverage.json")
    manifest_rows = read_jsonl(DETECTOR_INPUT_DIR / "real_proposal_query_manifest.jsonl")
    repaired_manifest_rows = [row for row in manifest_rows if row.get("m123_depth_validity_repaired")]
    docker_info = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    image = command_status(["docker", "image", "inspect", IMAGE_TAG, "--format", "{{.Id}}"])
    return [
        {
            "gate_id": "m123_depth_filtered_frame_staging_ready",
            "gate_status": "pass"
            if m123.get("status") == "e008_m123_target_free_render_frame_staging_verified_with_depth_filtered_frames"
            else "fail",
            "details": m123.get("status"),
        },
        {
            "gate_id": "detector_manifest_repaired",
            "gate_status": "pass" if manifest_rows and len(repaired_manifest_rows) == len(manifest_rows) else "fail",
            "details": {
                "manifest_rows": len(manifest_rows),
                "repaired_manifest_rows": len(repaired_manifest_rows),
                "sampled_frame_rows": sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows),
            },
        },
        {
            "gate_id": "detector_input_files_ready",
            "gate_status": "pass"
            if all(
                (DETECTOR_INPUT_DIR / name).exists() and (DETECTOR_INPUT_DIR / name).stat().st_size > 0
                for name in [
                    "real_proposal_query_manifest.jsonl",
                    "real_proposal_object_targets.jsonl",
                    "prompt_set.json",
                    "proposal_output_schema.json",
                ]
            )
            else "fail",
            "details": str(DETECTOR_INPUT_DIR),
        },
        {
            "gate_id": "docker_available",
            "gate_status": "pass" if docker_info["available"] else "fail",
            "details": docker_info.get("stdout") or docker_info.get("stderr"),
        },
        {
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if image["available"] else "fail",
            "details": IMAGE_TAG,
        },
        {
            "gate_id": "hf_cache_writable",
            "gate_status": "pass" if HF_CACHE.exists() and os.access(HF_CACHE, os.W_OK) else "fail",
            "details": str(HF_CACHE),
        },
        {
            "gate_id": "tmux_session_free",
            "gate_status": "pass" if not tmux_running(TMUX_SESSION) else "fail",
            "details": TMUX_SESSION,
        },
    ]


def build_report(coverage: dict[str, Any], preflight_rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M124 Target-Free Detector Candidate-Source Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Output path: `{coverage['output_path']}`.",
            f"- Detector sampled frames: {coverage['detector_sampled_frame_rows']}.",
            f"- Launch executed: {str(coverage['launch_executed']).lower()}.",
            f"- Verification command: `{coverage['verification_command']}`.",
            "",
            "## Preflight",
            "",
            "| gate_id | gate_status | details |",
            "| --- | --- | --- |",
            *[
                f"| {row['gate_id']} | {row['gate_status']} | {row.get('details', '')} |"
                for row in preflight_rows
            ],
            "",
            "## Claim Boundary",
            "",
            "- M124 launches target-free detector candidate-source generation on the M123 depth-filtered frame subset.",
            "- M124 does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "",
            "## Next",
            "",
            "- Verify E008-M124 completion before E008-M125 candidate navmesh/source-readiness validation.",
            "",
        ]
    )


def main() -> int:
    generated_at = datetime.now().isoformat(timespec="seconds")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    HF_CACHE.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{timestamp}_{TMUX_SESSION}.log"
    command = detector_command()
    shell_command = f"cd {shlex.quote(str(ROOT))} && {shell_join(command)} > {shlex.quote(str(log_path))} 2>&1"
    tmux_command = ["tmux", "new-session", "-d", "-s", TMUX_SESSION, shell_command]
    preflight_rows = build_preflight_rows()
    blockers = [row for row in preflight_rows if row["gate_status"] == "fail"]
    manifest_rows = read_jsonl(DETECTOR_INPUT_DIR / "real_proposal_query_manifest.jsonl")
    launch_result = None
    launch_executed = False
    if not blockers:
        launch_result = command_status(tmux_command)
        launch_executed = bool(launch_result["available"])
    coverage = {
        "version": VERSION,
        "generated_at": generated_at,
        "status": "e008_m124_target_free_detector_candidate_source_launched"
        if launch_executed
        else "e008_m124_target_free_detector_candidate_source_launch_blocked",
        "artifact_output_root": str(ARTIFACT_DIR),
        "data_input_root": str(M121_DATA_DIR),
        "detector_input_dir": str(DETECTOR_INPUT_DIR),
        "hf_cache": str(HF_CACHE),
        "tmux_session": TMUX_SESSION,
        "tmux_running_after_launch": tmux_running(TMUX_SESSION),
        "log_path": str(log_path),
        "output_path": str(ARTIFACT_DIR),
        "working_directory": str(ROOT),
        "command": shell_command,
        "detector_command": shell_join(command),
        "tmux_command": tmux_command,
        "launch_result": launch_result,
        "launch_executed": launch_executed,
        "detector_manifest_rows": len(manifest_rows),
        "detector_sampled_frame_rows": sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows),
        "verification_command": VERIFY_COMMAND,
        "selected_next_unit": "E008-M124 completion verification"
        if launch_executed
        else "repair E008-M124 launch blockers",
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }
    long_job_rows = [
        {
            "job_id": "E008-M124",
            "job_status": "launched" if launch_executed else "blocked",
            "job_type": "target_free_source_coverage_open_vocabulary_detector",
            "tmux_session": TMUX_SESSION,
            "log_path": str(log_path),
            "working_directory": str(ROOT),
            "command": shell_command,
            "output_path": str(ARTIFACT_DIR),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
            ],
            "verification_command": VERIFY_COMMAND,
            "next_if_verified": "E008-M125 target-free detector candidate navmesh/source-readiness validation",
            "version": VERSION,
        }
    ]
    write_json(ARTIFACT_DIR / "e008_m124_launch_coverage.json", coverage)
    write_json(ARTIFACT_DIR / "e008_m16_launch_coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "preflight_rows.jsonl", preflight_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_command_rows.jsonl", long_job_rows)
    write_text(ARTIFACT_DIR / "launch_report.md", build_report(coverage, preflight_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed else 2


if __name__ == "__main__":
    raise SystemExit(main())
