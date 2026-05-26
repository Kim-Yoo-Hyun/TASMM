#!/usr/bin/env python3
"""Launch an E005-M80 confidence-log-depth targeted detector rerun batch."""

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


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M79_DIR = EXP_ROOT / "artifacts" / "E005-M79_runner_insertion_targeted_rerun_plan_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M80_confidence_log_depth_detector_launch_v0"
VERSION = "e005_m80_confidence_log_depth_detector_launch_v0"
DEFAULT_MIN_GPU_FREE_MIB = 24000


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def gpu_free_mib() -> int | None:
    proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    values: list[int] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(int(line))
        except ValueError:
            continue
    return max(values) if values else None


def write_fifo_once(path: Path, payload: str, timeout_s: float = 20.0) -> dict[str, Any]:
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
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
        return {"ok": True, "error": ""}
    return {"ok": False, "error": last_error or "fifo_writer_timeout"}


def build_run_script(path: Path, command: list[str]) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shlex.quote(str(ROOT))}",
        f"exec {shlex.join(command)}",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def get_arg_value(command: list[str], name: str) -> str | None:
    try:
        index = command.index(name)
    except ValueError:
        return None
    if index + 1 >= len(command):
        return None
    return command[index + 1]


def select_batch(command_plan: dict[str, Any], batch_id: str) -> dict[str, Any]:
    for batch in command_plan.get("batches", []):
        if batch.get("batch_id") == batch_id:
            return batch
    raise RuntimeError(f"batch not found in M79 command plan: {batch_id}")


def expected_files_ready(expected_files: list[str]) -> bool:
    return bool(expected_files) and all(Path(path).exists() for path in expected_files)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M80 Confidence-Log-Depth Detector Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Batch: `{coverage['batch_id']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Background job status: `{coverage['background_job_status']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Working directory: `{coverage['working_directory']}`.",
            f"- Input dir: `{coverage['input_dir']}`.",
            f"- Output dir: `{coverage['output_dir']}`.",
            f"- Expected files ready before launch: `{coverage['expected_files_ready_before_launch']}`.",
            f"- Verification command: `{coverage['verification_command']}`.",
            f"- Query metric command: `{coverage['query_metric_command']}`.",
            "",
            "## Claim Boundary",
            "",
            "- This launch is not a paper-result claim.",
            "- Final real RGB-D/open-vocabulary robustness remains blocked until completion verification and query-level conversion.",
            "- Real navigation `SR` / `SPL` remains unsupported by this detector rerun.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--m79-dir", default=M79_DIR, type=Path)
    parser.add_argument("--out-dir", default=OUT_DIR, type=Path)
    parser.add_argument("--min-gpu-free-mib", default=DEFAULT_MIN_GPU_FREE_MIB, type=int)
    parser.add_argument("--ignore-gpu-memory", action="store_true")
    parser.add_argument("--sudo-password-env", default="E005_M80_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m79_dir = args.m79_dir.resolve()

    m79_coverage = read_json(args.m79_dir / "coverage.json")
    if m79_coverage.get("status") != "e005_m79_runner_insertion_targeted_rerun_plan_ready":
        raise RuntimeError(f"M79 is not ready: {m79_coverage.get('status')}")
    batch_id = args.batch_id or str(m79_coverage.get("first_rerun_batch") or "heldout_b02")

    command_plan_path = args.m79_dir / "targeted_rerun_command_plan.json"
    command_plan = read_json(command_plan_path)
    if not command_plan:
        raise RuntimeError(f"missing command plan: {command_plan_path}")
    batch_plan = select_batch(command_plan, batch_id)

    launch_dir = args.out_dir.resolve() / batch_id
    launch_dir.mkdir(parents=True, exist_ok=True)

    exact_command = [str(part) for part in batch_plan["exact_command"]]
    tmux_session = str(batch_plan["tmux_session"])
    expected_files = [str(path) for path in batch_plan.get("expected_files", [])]
    ready_before_launch = expected_files_ready(expected_files)
    input_dir = get_arg_value(exact_command, "--m17-dir")
    output_dir = str(batch_plan.get("output_dir") or get_arg_value(exact_command, "--out-dir") or "")
    needs_sudo_password = "--sudo-password-stdin" in exact_command
    sudo_password = (
        read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
        if needs_sudo_password
        else None
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m80_confidence_log_depth_{batch_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_script = launch_dir / f"run_m80_{batch_id}.sh"
    launch_command_file = launch_dir / "launch_command.txt"
    build_run_script(run_script, exact_command)

    tmux_path = shutil.which("tmux")
    current_gpu_free = gpu_free_mib()
    before_running = bool(tmux_path and tmux_has_session(tmux_session))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    password_delivery = {"ok": not needs_sudo_password, "error": ""}
    fifo_path: Path | None = None

    if ready_before_launch:
        status = "e005_m80_confidence_log_depth_detector_outputs_exist_needs_verification"
        background_status = "needs_verification"
    elif not tmux_path:
        status = "e005_m80_confidence_log_depth_detector_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m80_confidence_log_depth_detector_already_running"
        background_status = "running"
    elif not args.ignore_gpu_memory and current_gpu_free is not None and current_gpu_free < args.min_gpu_free_mib:
        status = "e005_m80_confidence_log_depth_detector_blocked_preflight"
        background_status = "blocked_preflight"
        launch_stderr = f"gpu_free_below_threshold:{current_gpu_free}<{args.min_gpu_free_mib}"
    elif needs_sudo_password and sudo_password is None:
        status = "e005_m80_confidence_log_depth_detector_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e005_m80_sudo_{batch_id}_{os.getpid()}_{timestamp}.fifo"
        if needs_sudo_password:
            os.mkfifo(fifo_path, 0o600)
        command_inner = (
            f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; "
            f"cd {shlex.quote(str(ROOT))}; "
            f"{shlex.quote(str(run_script))} "
            f"{('< ' + shlex.quote(str(fifo_path))) if needs_sudo_password else ''} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        launch_command = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            tmux_session,
            "bash",
            "-lc",
            command_inner,
        ]
        write_text(launch_command_file, shlex.join(launch_command) + "\n")
        proc = subprocess.run(
            launch_command,
            cwd=str(ROOT),
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
        after_running = tmux_has_session(tmux_session)
        if proc.returncode == 0 and password_delivery["ok"] and after_running:
            status = "e005_m80_confidence_log_depth_detector_job_launched"
            background_status = "running"
        elif proc.returncode == 0 and password_delivery["ok"] and not after_running:
            status = "e005_m80_confidence_log_depth_detector_job_exited_needs_verification"
            background_status = "needs_verification"
        else:
            if after_running:
                subprocess.run(["tmux", "kill-session", "-t", tmux_session], check=False)
            if fifo_path is not None and fifo_path.exists():
                fifo_path.unlink()
            status = "e005_m80_confidence_log_depth_detector_launch_failed"
            background_status = "failed"

    coverage = {
        "background_job_status": background_status,
        "batch_id": batch_id,
        "command_plan": str(command_plan_path),
        "current_gpu_free_mib": current_gpu_free,
        "e005_m80_version": VERSION,
        "exact_command": exact_command,
        "expected_files": expected_files,
        "expected_files_ready_before_launch": ready_before_launch,
        "fixed_policy_id": m79_coverage.get("fixed_policy_id"),
        "fixed_score_mode": m79_coverage.get("fixed_score_mode"),
        "input_dir": input_dir,
        "launch_command_file": str(launch_command_file),
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "log_path": str(log_path),
        "min_gpu_free_mib": args.min_gpu_free_mib,
        "next_recommended_unit": "E005-M81 confidence-log-depth detector completion verification for heldout_b02",
        "output_dir": output_dir,
        "password_delivery": password_delivery,
        "query_metric_command": batch_plan.get("query_metric_command"),
        "real_navigation_sr_spl_claim_ready": False,
        "real_rgbd_open_vocab_robustness_claim_ready": False,
        "run_script": str(run_script),
        "status": status,
        "sudo_password_supplied": sudo_password is not None,
        "tmux_session": tmux_session,
        "verification_command": batch_plan.get("verification_command"),
        "working_directory": str(ROOT),
    }
    write_json(launch_dir / "coverage.json", coverage)
    write_text(launch_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
