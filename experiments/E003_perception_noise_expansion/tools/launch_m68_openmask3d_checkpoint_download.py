#!/usr/bin/env python3
"""Launch the E003-M68 OpenMask3D checkpoint download job in tmux."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M67_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M67_openmask3d_checkpoint_env_route_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M68_openmask3d_checkpoint_download_launch_v0"
LAUNCH_VERSION = "e003_m68_openmask3d_checkpoint_download_launch_v0"
TMUX_SESSION = "e003_m68_openmask3d_checkpoints"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M68 OpenMask3D Checkpoint Download Launch",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- background job status: `{coverage['background_job_status']}`.",
            f"- launch executed: {coverage['launch_executed']}.",
            f"- working directory: `{coverage['working_directory']}`.",
            f"- log path: `{coverage['log_path']}`.",
            f"- download script: `{coverage['download_script']}`.",
            f"- output cache dir: `{coverage['cache_dir']}`.",
            f"- expected files: {coverage['expected_files']}.",
            f"- verification command: `{coverage['verification_command']}`.",
            "",
            "## 논문 주장",
            "",
            "- E003-M68 launch does not create an `OpenMask3D` proposal-quality claim.",
            "- It only starts checkpoint acquisition needed before Docker/model smoke can be retried.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not monitor the download continuously.",
            "- Check progress only when the user requests it or when E003-M69 needs the checkpoints.",
            "- If the job fails, inspect only the log tail or targeted error lines.",
            "- Completion should be verified with file size/layout checks and the recorded verification command.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the background job is running.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m67-dir", default=DEFAULT_M67_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m67_dir = args.m67_dir.resolve()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    command_plan = load_json(args.m67_dir / "download_command_plan.json")
    manifest = load_json(args.m67_dir / "checkpoint_manifest.json")
    verification_plan = load_json(args.m67_dir / "verification_command.json")
    expected_files = [
        {
            "key": row["key"],
            "cache_path": row["cache"]["path"],
            "resource_path": row["resource"]["path"],
            "min_size_bytes": row["min_size_bytes"],
        }
        for row in manifest["checkpoints"]
    ]
    cache_dir = str(Path(expected_files[0]["cache_path"]).parent) if expected_files else ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e003_m68_openmask3d_checkpoints.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    download_script = Path(command_plan["download_script"]).resolve()
    working_directory = Path(command_plan["working_directory"]).resolve()
    launch_command_file = args.out_dir / "launch_command.txt"

    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""

    if not tmux_path:
        status = "openmask3d_checkpoint_download_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
        launch_command = []
    elif before_running:
        status = "openmask3d_checkpoint_download_already_running"
        background_status = "running"
        launch_command = []
    elif not download_script.exists():
        status = "openmask3d_checkpoint_download_launch_failed"
        background_status = "failed"
        launch_stderr = f"download_script_missing: {download_script}"
        launch_command = []
    else:
        command_inner = (
            f"cd {shlex.quote(str(working_directory))} && "
            f"bash {shlex.quote(str(download_script))} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        launch_command = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            TMUX_SESSION,
            "bash",
            "-lc",
            command_inner,
        ]
        write_text(launch_command_file, shlex.join(launch_command) + "\n")
        proc = subprocess.run(
            launch_command,
            cwd=str(working_directory),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout
        launch_stderr = proc.stderr
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and after_running:
            status = "openmask3d_checkpoint_download_job_launched"
            background_status = "running"
        elif proc.returncode == 0:
            status = "openmask3d_checkpoint_download_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "openmask3d_checkpoint_download_launch_failed"
            background_status = "failed"

    coverage = {
        "background_job_status": background_status,
        "cache_dir": cache_dir,
        "download_script": str(download_script),
        "expected_files": expected_files,
        "launch_command": shlex.join(launch_command) if launch_command else "",
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": LAUNCH_VERSION,
        "log_exists_at_launch": log_path.exists(),
        "log_path": str(log_path),
        "next_recommended_unit": "E003-M69 OpenMask3D checkpoint completion verification",
        "status": status,
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "verification_command": verification_plan.get("verification_command") or verification_plan.get("command"),
        "working_directory": str(working_directory),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
