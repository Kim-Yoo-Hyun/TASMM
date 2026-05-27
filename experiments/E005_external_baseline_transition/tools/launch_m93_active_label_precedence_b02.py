#!/usr/bin/env python3
"""Launch E005-M93 bounded heldout_b02 active-label precedence rerun."""

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
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M92_DIR = EXP_ROOT / "artifacts" / "E005-M92_active_label_precedence_next_step_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_detector_launch_v0"
RUN_ROOT = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_detector_run_v0"
VERIFY_ROOT = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_detector_verification_v0"
QUERY_ROOT = EXP_ROOT / "artifacts" / "E005-M93_active_label_precedence_query_metric_v0"
VERSION = "e005_m93_active_label_precedence_detector_launch_v0"
DEFAULT_MIN_GPU_FREE_MIB = 24000
BATCH_ID = "heldout_b02"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
        try:
            values.append(int(line.strip()))
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


def set_arg(command: list[str], name: str, value: str) -> list[str]:
    out = list(command)
    try:
        index = out.index(name)
    except ValueError as exc:
        raise RuntimeError(f"missing command argument: {name}") from exc
    if index + 1 >= len(out):
        raise RuntimeError(f"argument has no value: {name}")
    out[index + 1] = value
    return out


def ensure_flag(command: list[str], flag: str) -> list[str]:
    return list(command) if flag in command else [*command, flag]


def build_exact_command(run_dir: Path) -> list[str]:
    command_plan = read_json(M68_DIR / "batches" / BATCH_ID / "detector_run_command_plan.json")
    if not command_plan:
        raise RuntimeError("missing E005-M68 heldout_b02 command plan")
    command = [str(part) for part in command_plan["exact_command"]]
    command = set_arg(command, "--out-dir", str(run_dir))
    command = set_arg(command, "--selection-score-mode", "confidence_log_depth")
    command = ensure_flag(command, "--export-cleanup-trace")
    return command


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


def expected_files(run_dir: Path) -> list[str]:
    return [
        str(run_dir / "coverage.json"),
        str(run_dir / "container_output" / "real_proposals.jsonl"),
        str(run_dir / "container_output" / "pre_cap_candidate_pool.jsonl"),
        str(run_dir / "container_output" / "cleanup_trace.jsonl"),
        str(run_dir / "container_output" / "pre_cap_policy_summary.json"),
        str(run_dir / "matching" / "coverage.json"),
        str(run_dir / "validator" / "coverage.json"),
    ]


def expected_files_ready(paths: list[str]) -> bool:
    return bool(paths) and all(Path(path).exists() for path in paths)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M93 Active-Label Precedence Detector Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Batch: `{coverage['batch_id']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Background job status: `{coverage['background_job_status']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Input dir: `{coverage['input_dir']}`.",
            f"- Output dir: `{coverage['output_dir']}`.",
            f"- Expected files ready before launch: `{coverage['expected_files_ready_before_launch']}`.",
            f"- Selection score mode: `{coverage['selection_score_mode']}`.",
            f"- Cleanup trace requested: `{coverage['cleanup_trace_requested']}`.",
            f"- Verification command: `{coverage['verification_command']}`.",
            f"- Query metric command: `{coverage['query_metric_command']}`.",
            "",
            "## Claim Boundary",
            "",
            "- This launch is not a final robustness result.",
            "- M93 tests whether the M91 active-label repair has net positive batch-level effect and whether `chair` / `stool` side effects occur.",
            "- Real navigation `SR` / `SPL` remains unsupported.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=OUT_DIR, type=Path)
    parser.add_argument("--run-root", default=RUN_ROOT, type=Path)
    parser.add_argument("--verify-root", default=VERIFY_ROOT, type=Path)
    parser.add_argument("--query-root", default=QUERY_ROOT, type=Path)
    parser.add_argument("--min-gpu-free-mib", default=DEFAULT_MIN_GPU_FREE_MIB, type=int)
    parser.add_argument("--ignore-gpu-memory", action="store_true")
    parser.add_argument("--sudo-password-env", default="E005_M93_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m92 = read_json(M92_DIR / "coverage.json")
    if m92.get("status") != "e005_m92_active_label_precedence_next_step_decision_ready":
        raise RuntimeError(f"M92 is not ready: {m92.get('status')}")
    if m92.get("selected_next_route") != "bounded_heldout_b02_rerun_before_full_query_claim":
        raise RuntimeError(f"M92 selected unexpected route: {m92.get('selected_next_route')}")

    launch_dir = args.out_dir.resolve() / BATCH_ID
    run_dir = args.run_root.resolve() / BATCH_ID
    launch_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    exact_command = build_exact_command(run_dir)
    expected = expected_files(run_dir)
    ready_before_launch = expected_files_ready(expected)
    tmux_session = "e005_m93_active_label_b02"
    needs_sudo_password = "--sudo-password-stdin" in exact_command
    sudo_password = (
        read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
        if needs_sudo_password
        else None
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m93_active_label_b02.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_script = launch_dir / "run_m93_heldout_b02.sh"
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
        status = "e005_m93_active_label_precedence_outputs_exist_needs_verification"
        background_status = "needs_verification"
    elif not tmux_path:
        status = "e005_m93_active_label_precedence_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m93_active_label_precedence_already_running"
        background_status = "running"
    elif not args.ignore_gpu_memory and current_gpu_free is not None and current_gpu_free < args.min_gpu_free_mib:
        status = "e005_m93_active_label_precedence_blocked_preflight"
        background_status = "blocked_preflight"
        launch_stderr = f"gpu_free_below_threshold:{current_gpu_free}<{args.min_gpu_free_mib}"
    elif needs_sudo_password and sudo_password is None:
        status = "e005_m93_active_label_precedence_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e005_m93_sudo_{os.getpid()}_{timestamp}.fifo"
        if needs_sudo_password:
            os.mkfifo(fifo_path, 0o600)
        command_inner = (
            f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; "
            f"cd {shlex.quote(str(ROOT))}; "
            f"{shlex.quote(str(run_script))} "
            f"{('< ' + shlex.quote(str(fifo_path))) if needs_sudo_password else ''} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        launch_command = ["tmux", "new-session", "-d", "-s", tmux_session, "bash", "-lc", command_inner]
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
            status = "e005_m93_active_label_precedence_job_launched"
            background_status = "running"
        elif proc.returncode == 0 and password_delivery["ok"] and not after_running:
            status = "e005_m93_active_label_precedence_job_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "e005_m93_active_label_precedence_launch_failed"
            background_status = "failed"

    verification_command = [
        "python",
        "experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py",
        "--batch-id",
        BATCH_ID,
        "--launch-root",
        str(args.out_dir.resolve()),
        "--run-root",
        str(args.run_root.resolve()),
        "--out-root",
        str(args.verify_root.resolve()),
        "--require-ready",
    ]
    query_metric_command = [
        "python",
        "experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py",
        "--batch-id",
        BATCH_ID,
        "--m69-root",
        str(args.run_root.resolve()),
        "--m70-root",
        str(args.verify_root.resolve()),
        "--out-root",
        str(args.query_root.resolve()),
    ]

    coverage: dict[str, Any] = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_id": BATCH_ID,
        "background_job_status": background_status,
        "cleanup_trace_requested": True,
        "current_gpu_free_mib": current_gpu_free,
        "expected_files": expected,
        "expected_files_ready_before_launch": ready_before_launch,
        "input_dir": str(M68_DIR / "batches" / BATCH_ID),
        "launch_command_file": str(launch_command_file),
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "log_path": str(log_path),
        "output_dir": str(run_dir),
        "password_delivery": password_delivery,
        "query_metric_command": " ".join(shlex.quote(part) for part in query_metric_command),
        "run_script": str(run_script),
        "selection_score_mode": "confidence_log_depth",
        "tmux_session": tmux_session,
        "verification_command": " ".join(shlex.quote(part) for part in verification_command),
        "working_directory": str(ROOT),
    }
    write_json(launch_dir / "coverage.json", coverage)
    write_text(launch_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
