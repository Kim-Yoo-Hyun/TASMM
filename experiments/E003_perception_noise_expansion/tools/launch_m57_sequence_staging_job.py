#!/usr/bin/env python3
"""Launch the E003-M57 current-rescan sequence staging job in tmux."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M56_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M56_current_rescan_sequence_staging_plan_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M57_sequence_staging_job_launch_v0"
M57_VERSION = "e003_m57_sequence_staging_job_launch_v0"
TMUX_SESSION = "e003_m56_sequence_stage"


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
            "# E003-M57 Sequence Staging Job Launch",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- job status: `{coverage['background_job_status']}`.",
            f"- launched: {coverage['launch_executed']}.",
            f"- log path: `{coverage['log_path']}`.",
            f"- run script: `{coverage['run_script']}`.",
            f"- verification command: `{coverage['verification_command']}`.",
            f"- target scans: {coverage['target_scan_ids']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M57 does not create a paper result claim.",
            "- It only launches the long-running staging job needed before direct current-rescan detector evaluation.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not monitor the job continuously.",
            "- Check progress only when the user requests it or when the next dependent task needs the sequence payloads.",
            "- Verify completion with the recorded verification command rather than reading full logs.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the background job is running.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m56-dir", default=DEFAULT_M56_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command_plan = load_json(args.m56_dir / "command_plan.json")
    m56_coverage = load_json(args.m56_dir / "coverage.json")
    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    if not tmux_path:
        status = "sequence_staging_job_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "sequence_staging_job_already_running"
        background_status = "running"
    else:
        proc = subprocess.run(
            command_plan["launch_command"],
            shell=True,
            cwd=command_plan["working_directory"],
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
            status = "sequence_staging_job_launched"
            background_status = "running"
        else:
            status = "sequence_staging_job_launch_failed"
            background_status = "failed"

    log_path = Path(command_plan["log_path"])
    coverage = {
        "background_job_status": background_status,
        "expected_files": m56_coverage.get("expected_files"),
        "launch_command": command_plan["launch_command"],
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "log_exists_at_launch": log_path.exists(),
        "log_path": str(log_path),
        "m57_version": M57_VERSION,
        "next_recommended_unit": "Wait for staging completion, then verify sequence payloads",
        "run_script": command_plan["run_script"],
        "status": status,
        "target_scan_ids": m56_coverage.get("target_scan_ids"),
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "verification_command": command_plan["verification_command"],
        "working_directory": command_plan["working_directory"],
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
