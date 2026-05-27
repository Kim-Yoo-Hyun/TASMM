#!/usr/bin/env python3
"""Launch E005-M89 target-independent cleanup trace rerun."""

from __future__ import annotations

import argparse
import errno
import getpass
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M68_BATCH_ROOT = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0" / "batches"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_launch_v0"
RUN_ROOT = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_run_v0"
VERIFY_ROOT = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_verification_v0"
VERSION = "e005_m89_cleanup_trace_detector_launch_v0"
DEFAULT_SCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"


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


def expected_files(output_dir: Path) -> list[str]:
    return [
        str(output_dir / "coverage.json"),
        str(output_dir / "container_output" / "backend_contract.json"),
        str(output_dir / "container_output" / "cleanup_trace.jsonl"),
        str(output_dir / "container_output" / "model_smoke.json"),
        str(output_dir / "container_output" / "pre_cap_policy_summary.json"),
        str(output_dir / "container_output" / "run_metadata.json"),
        str(output_dir / "frame_diagnostics.jsonl"),
        str(output_dir / "report.md"),
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M89 Cleanup Trace Detector Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Batch: `{coverage['batch_id']}`.",
            f"- Scan id: `{coverage['scan_id']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Background job status: `{coverage['background_job_status']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Output dir: `{coverage['output_dir']}`.",
            f"- Expected files ready before launch: `{coverage['expected_files_ready_before_launch']}`.",
            f"- Verification command: `{coverage['verification_command']}`.",
            "",
            "## Claim Boundary",
            "",
            "- This launch is instrumentation, not a prompt repair or detector repair result.",
            "- The trace must not use target ids, candidate-is-target labels, matched target ids, or query success labels.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default="heldout_b02")
    parser.add_argument("--scan-id", default=DEFAULT_SCAN_ID)
    parser.add_argument("--out-dir", default=OUT_DIR, type=Path)
    parser.add_argument("--run-root", default=RUN_ROOT, type=Path)
    parser.add_argument("--sudo-password-env", default="E005_M89_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    batch_id = str(args.batch_id)
    scan_id = str(args.scan_id)
    input_dir = (M68_BATCH_ROOT / batch_id).resolve()
    output_dir = (args.run_root.resolve() / batch_id)
    launch_dir = args.out_dir.resolve() / batch_id
    launch_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    exact_command = [
        sys.executable,
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--m17-dir",
        str(input_dir),
        "--out-dir",
        str(output_dir),
        "--max-scans",
        "1",
        "--scan-id",
        scan_id,
        "--max-frames-per-scan",
        "24",
        "--max-labels",
        "9",
        "--max-predictions",
        "64800",
        "--max-predictions-per-frame",
        "100",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "400000",
        "--export-pre-cap-candidate-pool",
        "--export-cleanup-trace",
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
    ]
    tmux_session = f"e005_m89_cleanup_trace_{batch_id}_{scan_id[:8]}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"{timestamp}_{tmux_session}.log"
    run_script = launch_dir / f"run_m89_{batch_id}_{scan_id[:8]}.sh"
    fifo_path = launch_dir / f"{tmux_session}.fifo"
    password_path = Path("/tmp") / f"{tmux_session}_sudo_input"
    build_run_script(run_script, exact_command)

    expected = expected_files(output_dir)
    ready_before = bool(expected) and all(Path(path).exists() for path in expected)
    sudo_password = read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
    launch_error = ""
    fifo_status: dict[str, Any] | None = None
    launch_executed = False
    if tmux_has_session(tmux_session):
        background_status = "running"
        status = "e005_m89_cleanup_trace_detector_job_already_running"
    elif ready_before:
        background_status = "needs_verification"
        status = "e005_m89_cleanup_trace_detector_outputs_already_present"
    elif not sudo_password:
        background_status = "failed"
        status = "e005_m89_cleanup_trace_detector_launch_blocked_missing_sudo_password"
    else:
        password_path.write_text(sudo_password, encoding="utf-8")
        password_path.chmod(0o600)
        tmux_command = (
            "set -euo pipefail; "
            f"cd {shlex.quote(str(ROOT))} && "
            f"sudo_payload=$(cat {shlex.quote(str(password_path))}) && "
            f"rm -f {shlex.quote(str(password_path))} && "
            f"printf '%s\\n' \"$sudo_payload\" | {shlex.quote(str(run_script))} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        proc = subprocess.run(
            ["tmux", "new-session", "-d", "-s", tmux_session, tmux_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        launch_executed = proc.returncode == 0
        if launch_executed:
            background_status = "running"
            status = "e005_m89_cleanup_trace_detector_job_launched"
        else:
            if password_path.exists():
                password_path.unlink()
            background_status = "failed"
            launch_error = proc.stderr.strip()
            status = "e005_m89_cleanup_trace_detector_launch_failed_tmux"

    verification_command = [
        sys.executable,
        "experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py",
        "--batch-id",
        batch_id,
        "--launch-root",
        str(args.out_dir.resolve()),
        "--run-root",
        str(args.run_root.resolve()),
        "--out-root",
        str(VERIFY_ROOT),
        "--require-ready",
    ]
    coverage = {
        "background_job_status": background_status,
        "batch_id": batch_id,
        "blocked_fields": [
            "target_uid",
            "candidate_is_target",
            "matched_3dssg_instance_id",
            "nearest_target_distance",
            "query_success_label",
        ],
        "command": exact_command,
        "expected_files": expected,
        "expected_files_ready_before_launch": ready_before,
        "fifo_status": fifo_status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_dir": str(input_dir),
        "launch_error": launch_error,
        "launch_executed": launch_executed,
        "log_path": str(log_path),
        "output_dir": str(output_dir),
        "password_input_method": "temporary_file_removed_inside_tmux_command",
        "scan_id": scan_id,
        "status": status,
        "tmux_session": tmux_session,
        "version": VERSION,
        "verification_command": " ".join(shlex.quote(part) for part in verification_command),
        "working_directory": str(ROOT),
    }
    write_json(launch_dir / "coverage.json", coverage)
    write_text(launch_dir / "launch_command.txt", " ".join(shlex.quote(part) for part in exact_command) + "\n")
    write_text(launch_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
