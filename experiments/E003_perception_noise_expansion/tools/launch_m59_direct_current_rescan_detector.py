#!/usr/bin/env python3
"""Launch the E003-M59 direct current-rescan detector run in tmux."""

from __future__ import annotations

import argparse
import errno
import getpass
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M58_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M58_direct_current_rescan_bridge_design_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M59_direct_current_rescan_detector_launch_v0"
M59_VERSION = "e003_m59_direct_current_rescan_detector_launch_v0"
TMUX_SESSION = "e003_m59_direct_bridge"


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


def read_sudo_password(*, env_name: str, use_stdin: bool) -> str | None:
    value = os.environ.get(env_name)
    if value:
        return value if value.endswith("\n") else value + "\n"
    if not use_stdin:
        return None
    if sys.stdin.isatty():
        value = getpass.getpass("")
    else:
        value = sys.stdin.readline()
    if not value:
        return None
    return value if value.endswith("\n") else value + "\n"


def write_fifo_once(path: Path, payload: str, timeout_s: float = 10.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as exc:
            last_error = str(exc)
            if exc.errno == errno.ENXIO:
                time.sleep(0.1)
                continue
            return {"ok": False, "error": last_error}
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
        return {"ok": True, "error": ""}
    return {"ok": False, "error": last_error or "fifo_writer_timeout"}


def build_run_script(path: Path, command: list[str], working_directory: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shlex.quote(str(working_directory))}",
        f"exec {shlex.join(command)}",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M59 Direct Current-Rescan Detector Launch",
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
            f"- output path: `{coverage['output_dir']}`.",
            f"- working directory: `{coverage['working_directory']}`.",
            f"- target scans: {coverage['target_scan_count']} / {coverage['target_scan_ids']}.",
            f"- bridge query rows: {coverage['bridge_query_rows']}.",
            f"- verification command: `{coverage['verification_command']}`.",
            f"- expected files: {coverage['expected_files']}.",
            f"- password value recorded: {coverage['sudo_password_recorded']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M59 launch does not create a paper result claim.",
            "- It only starts the Docker detector run required before query-level direct current-rescan bridge evaluation.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not monitor the detector job continuously.",
            "- Verify completion with the recorded verification command and expected files before E003-M60.",
            "- If the job fails, inspect only the log tail or targeted error lines.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the background job is running.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m58-dir", default=DEFAULT_M58_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--sudo-password-env", default="E003_M59_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m58_dir = args.m58_dir.resolve()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    command_plan = load_json(args.m58_dir / "detector_run_command_plan.json")
    m58_coverage = load_json(args.m58_dir / "coverage.json")
    target_scan_ids = [str(row["scan_id"]) for row in m58_coverage.get("scan_summary", []) if row.get("scan_id")]
    exact_command = [str(part) for part in command_plan["exact_command"]]
    needs_sudo_password = "--sudo-password-stdin" in exact_command
    sudo_password = (
        read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
        if needs_sudo_password
        else None
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e003_m59_direct_current_rescan_detector_run.log"
    run_script = args.out_dir / "run_m59_detector.sh"
    launch_command_file = args.out_dir / "launch_command.txt"
    working_directory = Path(command_plan["working_directory"]).resolve()
    build_run_script(run_script, exact_command, working_directory)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    password_delivery = {"ok": not needs_sudo_password, "error": ""}
    fifo_path: Path | None = None

    if not tmux_path:
        status = "direct_current_rescan_detector_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "direct_current_rescan_detector_job_already_running"
        background_status = "running"
    elif needs_sudo_password and sudo_password is None:
        status = "direct_current_rescan_detector_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e003_m59_sudo_{os.getpid()}_{timestamp}.fifo"
        if needs_sudo_password:
            os.mkfifo(fifo_path, 0o600)
        command_inner = (
            f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; "
            f"cd {shlex.quote(str(working_directory))}; "
            f"{shlex.quote(str(run_script))} "
            f"{('< ' + shlex.quote(str(fifo_path))) if needs_sudo_password else ''} "
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
        if proc.returncode == 0 and needs_sudo_password and sudo_password is not None:
            password_delivery = write_fifo_once(fifo_path, sudo_password)
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and password_delivery["ok"] and after_running:
            status = "direct_current_rescan_detector_job_launched"
            background_status = "running"
        elif proc.returncode == 0 and password_delivery["ok"] and not after_running:
            status = "direct_current_rescan_detector_job_exited_needs_verification"
            background_status = "needs_verification"
        else:
            if after_running:
                subprocess.run(["tmux", "kill-session", "-t", TMUX_SESSION], check=False)
            status = "direct_current_rescan_detector_launch_failed"
            background_status = "failed"

    coverage = {
        "background_job_status": background_status,
        "bridge_query_rows": m58_coverage.get("direct_bridge_query_rows"),
        "command_plan": str(args.m58_dir / "detector_run_command_plan.json"),
        "expected_files": command_plan.get("expected_files"),
        "exact_command": exact_command,
        "launch_command_file": str(launch_command_file),
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "log_exists_at_launch": log_path.exists(),
        "log_path": str(log_path),
        "m59_version": M59_VERSION,
        "next_recommended_unit": "E003-M60 direct current-rescan query-level bridge evaluation after detector output verification",
        "output_dir": command_plan.get("output_dir"),
        "password_delivery": password_delivery,
        "run_script": str(run_script),
        "status": status,
        "sudo_password_recorded": False,
        "target_scan_count": m58_coverage.get("direct_bridge_scan_rows"),
        "target_scan_ids": target_scan_ids,
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "verification_command": shlex.join([str(part) for part in command_plan["verification_command"]]),
        "working_directory": command_plan.get("working_directory"),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
