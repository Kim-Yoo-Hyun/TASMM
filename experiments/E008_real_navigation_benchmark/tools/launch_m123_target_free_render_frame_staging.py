#!/usr/bin/env python3
"""Launch E008-M123 target-free render frame staging in tmux."""

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
M121_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
M122_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0"
M121_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
LOG_DIR = ROOT / "logs"
RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
TMUX_SESSION = "e008_m123_target_free_render"
VERSION = "e008_m123_target_free_source_coverage_render_frame_staging_launch_v0"
VERIFY_COMMAND = (
    "python experiments/E008_real_navigation_benchmark/tools/verify_m123_target_free_render_frame_staging.py "
    "--require-ready"
)


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


def docker_prefix() -> tuple[list[str], dict[str, Any]]:
    direct = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    sudo_n = command_status(["sudo", "-n", "docker", "info", "--format", "{{.ServerVersion}}"])
    if direct["available"]:
        return ["docker"], {"available": True, "mode": "direct", "direct": direct, "sudo_n": sudo_n}
    if sudo_n["available"]:
        return ["sudo", "-n", "docker"], {"available": True, "mode": "sudo_n", "direct": direct, "sudo_n": sudo_n}
    return ["docker"], {"available": False, "mode": "unavailable", "direct": direct, "sudo_n": sudo_n}


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


def count_existing_render_files() -> dict[str, int]:
    scan_root = M121_DATA_DIR / "3RScan" / "scans"
    return {
        "color": len(list(scan_root.glob("*/sequence/frame-*.color.jpg"))) if scan_root.exists() else 0,
        "depth": len(list(scan_root.glob("*/sequence/frame-*.depth.pgm"))) if scan_root.exists() else 0,
        "pose": len(list(scan_root.glob("*/sequence/frame-*.pose.txt"))) if scan_root.exists() else 0,
        "info": len(list(scan_root.glob("*/sequence/_info.txt"))) if scan_root.exists() else 0,
    }


def build_render_command(prefix: list[str], log_path: Path) -> tuple[list[str], str, str]:
    render_input_dir = M121_DATA_DIR / "render_inputs"
    docker_command = [
        *prefix,
        "run",
        "--rm",
        "--gpus",
        "all",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "HOME=/tmp",
        "-e",
        "XDG_CACHE_HOME=/tmp/.cache",
        "-v",
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "-v",
        f"{render_input_dir}:/inputs:ro",
        "-v",
        f"{M121_DATA_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m122_target_free.py",
    ]
    shell_command = f"cd {shlex.quote(str(ROOT))} && {shell_join(docker_command)} > {shlex.quote(str(log_path))} 2>&1"
    tmux_command = ["tmux", "new-session", "-d", "-s", TMUX_SESSION, shell_command]
    return tmux_command, shell_command, shell_join(docker_command)


def build_preflight_rows(prefix: list[str], docker: dict[str, Any], render_plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m121 = read_json(M121_ARTIFACT_DIR / "coverage.json")
    m122 = read_json(M122_ARTIFACT_DIR / "coverage.json")
    image = command_status([*prefix, "image", "inspect", HABITAT_IMAGE, "--format", "{{.Id}}"]) if docker["available"] else {"available": False}
    return [
        {
            "gate_id": "m121_materialization_ready",
            "gate_status": "pass"
            if str(m121.get("status", "")).startswith("e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready")
            else "fail",
            "details": m121.get("status"),
        },
        {
            "gate_id": "m122_launcher_contract_ready",
            "gate_status": "pass"
            if str(m122.get("status", "")).startswith("e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_ready")
            else "fail",
            "details": m122.get("status"),
        },
        {
            "gate_id": "render_plan_rows_ready",
            "gate_status": "pass" if len(render_plan_rows) == 320 else "fail",
            "details": len(render_plan_rows),
        },
        {
            "gate_id": "render_script_ready",
            "gate_status": "pass" if (M121_DATA_DIR / "render_inputs" / "render_m122_target_free.py").exists() else "fail",
            "details": str(M121_DATA_DIR / "render_inputs" / "render_m122_target_free.py"),
        },
        {
            "gate_id": "external_hm3d_data_readonly_source_ready",
            "gate_status": "pass" if RESEARCH2_DATA_ROOT.exists() else "fail",
            "details": str(RESEARCH2_DATA_ROOT),
        },
        {
            "gate_id": "docker_available",
            "gate_status": "pass" if docker["available"] else "fail",
            "details": docker["mode"],
        },
        {
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if image.get("available") else "fail",
            "details": HABITAT_IMAGE,
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
            "# E008-M123 Target-Free Render Frame Staging Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Output path: `{coverage['output_path']}`.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
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
            "- M123 is a background render-frame staging launch only.",
            "- M123 does not run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "",
            "## Next",
            "",
            "- Verify E008-M123 completion before launching E008-M124 detector candidate-source generation.",
            "",
        ]
    )


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    prefix, docker = docker_prefix()
    render_plan_rows = read_jsonl(M121_DATA_DIR / "render_inputs" / "render_plan_rows.jsonl")
    preflight_rows = build_preflight_rows(prefix, docker, render_plan_rows)
    blockers = [row["gate_id"] for row in preflight_rows if row["gate_status"] == "fail"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e008_m123_target_free_render.log"
    tmux_command, shell_command, docker_command = build_render_command(prefix, log_path)
    existing_files = count_existing_render_files()
    launch_result: dict[str, Any] = {"available": False, "returncode": None, "stdout": "", "stderr": ""}
    launch_executed = False
    status = "e008_m123_target_free_render_frame_staging_launch_blocked"
    if not blockers:
        launch_result = command_status(tmux_command)
        launch_executed = bool(launch_result["available"])
        status = (
            "e008_m123_target_free_render_frame_staging_launched"
            if launch_executed
            else "e008_m123_target_free_render_frame_staging_launch_failed"
        )
    elif tmux_running(TMUX_SESSION) and blockers == ["tmux_session_free"]:
        status = "e008_m123_target_free_render_frame_staging_already_running"

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "launch_executed": launch_executed,
        "tmux_session": TMUX_SESSION,
        "tmux_running_after_launch": tmux_running(TMUX_SESSION),
        "working_directory": str(ROOT),
        "output_path": str(M121_DATA_DIR),
        "log_path": str(log_path),
        "render_plan_rows": len(render_plan_rows),
        "expected_frame_rows": len(render_plan_rows),
        "existing_render_files_before_launch": existing_files,
        "verification_command": VERIFY_COMMAND,
        "docker_status": docker,
        "tmux_command": tmux_command,
        "shell_command": shell_command,
        "docker_command": docker_command,
        "launch_result": launch_result,
        "render_frames_ready": False,
        "detector_candidate_rows_ready": False,
        "source_gap_recovery_evaluated": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": "E008-M123 completion verification",
    }
    command_rows = [
        {
            "job_id": "E008-M123",
            "job_status": "launched" if launch_executed else status,
            "command": shell_command,
            "tmux_command": shell_join(tmux_command),
            "working_directory": str(ROOT),
            "output_path": str(M121_DATA_DIR),
            "log_path": str(log_path),
            "expected_files": [
                "rendered_frame_rows.jsonl",
                "snap_validation_rows.jsonl",
                "render_summary.json",
                "3RScan/scans/<scan_id>/sequence/frame-*.color.jpg",
                "3RScan/scans/<scan_id>/sequence/frame-*.depth.pgm",
                "3RScan/scans/<scan_id>/sequence/frame-*.pose.txt",
            ],
            "verification_command": VERIFY_COMMAND,
        }
    ]
    write_json(ARTIFACT_DIR / "launch_coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "preflight_rows.jsonl", preflight_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, preflight_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed or status.endswith("already_running") else 2


if __name__ == "__main__":
    raise SystemExit(main())
