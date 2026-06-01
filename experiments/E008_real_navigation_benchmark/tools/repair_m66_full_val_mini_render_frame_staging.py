#!/usr/bin/env python3
"""Repair and relaunch E008-M66 full-val-mini render frame staging."""

from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M65_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
M65_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M65_full_val_mini_render_detector_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M66_full_val_mini_render_frame_staging_repair_v0"
LOG_DIR = ROOT / "logs"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
TMUX_SESSION = "e008_m66_full_val_mini_render_repair"
VERSION = "e008_m66_full_val_mini_render_frame_staging_repair_v0"
VERIFY_COMMAND = "python experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py --require-ready"


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


def distance(a: list[Any], b: list[Any]) -> float:
    try:
        return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))
    except Exception:
        return float("inf")


def build_ready_rows(plan_rows: list[dict[str, Any]], snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan_by_key = {(str(row["scan_id"]), str(row["frame_id"])): row for row in plan_rows}
    ready = []
    for snap in snap_rows:
        if not snap.get("snap_validation_ready"):
            continue
        plan = plan_by_key.get((str(snap.get("scan_id")), str(snap.get("frame_id"))))
        if not plan:
            continue
        ready.append({"plan": plan, "snap": snap})
    return ready


def choose_fallback(failed_snap: dict[str, Any], ready_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    scan_id = str(failed_snap.get("scan_id"))
    yaw = failed_snap.get("yaw_offset_deg")
    bearing = failed_snap.get("bearing_relative_deg")
    radius = float(failed_snap.get("shell_radius_m") or 0.0)
    planned = failed_snap.get("planned_position_m") or []

    candidates = [
        row
        for row in ready_rows
        if str(row["plan"].get("scan_id")) == scan_id
        and row["snap"].get("yaw_offset_deg") == yaw
        and row["snap"].get("bearing_relative_deg") == bearing
        and float(row["snap"].get("shell_radius_m") or 0.0) < radius
    ]
    if not candidates:
        candidates = [
            row
            for row in ready_rows
            if str(row["plan"].get("scan_id")) == scan_id and row["snap"].get("yaw_offset_deg") == yaw
        ]
    if not candidates:
        candidates = [row for row in ready_rows if str(row["plan"].get("scan_id")) == scan_id]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda row: (
            abs(float(row["snap"].get("shell_radius_m") or 0.0) - min(radius, 1.5)),
            distance(planned, row["snap"].get("render_position_m") or row["plan"].get("source_position") or []),
        ),
    )


def patch_render_plan() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    plan_path = M65_DATA_DIR / "render_inputs" / "render_plan_rows.jsonl"
    plan_rows = read_jsonl(plan_path)
    issue_rows = read_jsonl(M65_ARTIFACT_DIR / "verification_issue_rows.jsonl")
    snap_rows = read_jsonl(M65_DATA_DIR / "snap_validation_rows.jsonl")
    failed_snaps = {
        (str(row.get("scan_id")), str(row.get("frame_id"))): row
        for row in snap_rows
        if not row.get("snap_validation_ready")
    }
    ready_rows = build_ready_rows(plan_rows, snap_rows)
    fallback_rows = []
    blockers = []
    patched_plan_rows = []
    for row in plan_rows:
        key = (str(row.get("scan_id")), str(row.get("frame_id")))
        failed_snap = failed_snaps.get(key)
        if not failed_snap:
            patched_plan_rows.append(row)
            continue
        fallback = choose_fallback(failed_snap, ready_rows)
        if fallback is None:
            blockers.append(f"no_fallback:{key[0]}:{key[1]}")
            patched_plan_rows.append(row)
            continue
        fallback_plan = fallback["plan"]
        patched = dict(row)
        for field in [
            "source_position",
            "source_rotation",
            "requires_navmesh_snap_validation",
            "bearing_relative_deg",
            "shell_radius_m",
            "pose_role",
            "route_id",
        ]:
            patched[field] = fallback_plan.get(field)
        patched.update(
            {
                "m66_repair_applied": True,
                "m66_repair_policy": "fallback_to_same_scan_yaw_ready_shell_pose_v0",
                "m66_repair_source_frame_id": fallback_plan.get("frame_id"),
                "m66_repair_source_observation_pose_id": fallback_plan.get("observation_pose_id"),
                "m66_original_observation_pose_id": row.get("observation_pose_id"),
                "m66_original_source_position": row.get("source_position"),
                "m66_original_shell_radius_m": row.get("shell_radius_m"),
                "position_status": "m66_repaired_with_ready_shell_fallback",
                "version": VERSION,
            }
        )
        fallback_rows.append(
            {
                "scan_id": key[0],
                "frame_id": key[1],
                "original_observation_pose_id": row.get("observation_pose_id"),
                "fallback_frame_id": fallback_plan.get("frame_id"),
                "fallback_observation_pose_id": fallback_plan.get("observation_pose_id"),
                "original_shell_radius_m": row.get("shell_radius_m"),
                "fallback_shell_radius_m": fallback_plan.get("shell_radius_m"),
                "yaw_offset_deg": row.get("yaw_offset_deg"),
                "repair_policy": patched["m66_repair_policy"],
            }
        )
        patched_plan_rows.append(patched)

    write_jsonl(ARTIFACT_DIR / "original_issue_rows.jsonl", issue_rows)
    write_jsonl(ARTIFACT_DIR / "fallback_repair_rows.jsonl", fallback_rows)
    write_jsonl(ARTIFACT_DIR / "patched_render_plan_rows.jsonl", patched_plan_rows)
    write_jsonl(plan_path, patched_plan_rows)
    return patched_plan_rows, fallback_rows, blockers


def build_render_command(prefix: list[str], log_path: Path) -> tuple[list[str], str]:
    render_input_dir = M65_DATA_DIR / "render_inputs"
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
        f"{RESEARCH3_DATA_ROOT}:/data:ro",
        "-v",
        f"{render_input_dir}:/inputs:ro",
        "-v",
        f"{M65_DATA_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m65.py",
    ]
    shell_command = f"cd {shlex.quote(str(ROOT))} && {shell_join(docker_command)} > {shlex.quote(str(log_path))} 2>&1"
    return ["tmux", "new-session", "-d", "-s", TMUX_SESSION, shell_command], shell_command


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M66 Full-Val-Mini Render Frame Staging Repair",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Previous M66 status: `{coverage['previous_m66_status']}`.",
            f"- Patched render plan rows: {coverage['patched_render_plan_rows']}.",
            f"- Fallback repair rows: {coverage['fallback_repair_rows']}.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Launch executed: {str(coverage['launch_executed']).lower()}.",
            f"- Verification command: `{coverage['verification_command']}`.",
            "",
            "## 논문 주장",
            "",
            "- This repair is an input-staging repair only.",
            "- It does not support detector robustness, deployable search, or real navigation `SR` / `SPL`.",
            "",
            "## 에이전트 추론",
            "",
            "- The failure mode is invalid radius-3.0 shell viewpoints, not a detector or policy result.",
            "- M67 detector inference should still wait until repaired M66 verification passes.",
            "",
        ]
    )


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    previous = read_json(M65_ARTIFACT_DIR / "verification_coverage.json")
    prefix, docker = docker_prefix()
    patched_plan_rows, fallback_rows, repair_blockers = patch_render_plan()
    image = command_status([*prefix, "image", "inspect", HABITAT_IMAGE, "--format", "{{.Id}}"]) if docker["available"] else {"available": False}
    blockers = list(repair_blockers)
    if previous.get("status") != "e008_m66_full_val_mini_render_frame_staging_verification_failed":
        blockers.append("previous_m66_not_failed")
    if len(patched_plan_rows) != 1080:
        blockers.append("patched_plan_row_count_mismatch")
    if len(fallback_rows) != int(previous.get("frame_issue_rows", 0) or 0):
        blockers.append("fallback_row_count_mismatch")
    if not docker["available"]:
        blockers.append("docker_unavailable")
    if not image.get("available"):
        blockers.append("habitat_image_unavailable")
    if tmux_running(TMUX_SESSION):
        blockers.append("tmux_session_already_running")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e008_m66_full_val_mini_render_repair.log"
    tmux_command, shell_command = build_render_command(prefix, log_path)
    launch_result: dict[str, Any] = {"available": False, "returncode": None, "stdout": "", "stderr": ""}
    launch_executed = False
    if not blockers:
        launch_result = command_status(tmux_command)
        launch_executed = bool(launch_result["available"])
    status = (
        "e008_m66_full_val_mini_render_frame_staging_repair_launched"
        if launch_executed
        else "e008_m66_full_val_mini_render_frame_staging_repair_blocked"
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "previous_m66_status": previous.get("status"),
        "blockers": blockers,
        "patched_render_plan_rows": len(patched_plan_rows),
        "fallback_repair_rows": len(fallback_rows),
        "launch_executed": launch_executed,
        "tmux_session": TMUX_SESSION,
        "tmux_running_after_launch": tmux_running(TMUX_SESSION),
        "working_directory": str(ROOT),
        "output_path": str(M65_DATA_DIR),
        "log_path": str(log_path),
        "verification_command": VERIFY_COMMAND,
        "docker_status": docker,
        "tmux_command": tmux_command,
        "shell_command": shell_command,
        "launch_result": launch_result,
        "render_frames_ready": False,
        "detector_candidate_rows_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E008-M66 repaired completion verification",
    }
    command_rows = [
        {
            "job_id": "E008-M66-repair",
            "job_status": "launched" if launch_executed else status,
            "command": shell_command,
            "tmux_command": shell_join(tmux_command),
            "working_directory": str(ROOT),
            "output_path": str(M65_DATA_DIR),
            "log_path": str(log_path),
            "verification_command": VERIFY_COMMAND,
        }
    ]
    write_json(ARTIFACT_DIR / "repair_coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed else 2


if __name__ == "__main__":
    raise SystemExit(main())
