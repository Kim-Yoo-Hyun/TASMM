#!/usr/bin/env python3
"""Verify the E005-M06 DualMap bootstrap background job."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M06_dualmap_bootstrap_launch_v0"
DUALMAP_REPO = REPO_ROOT / "local_dataset" / "external_repos" / "DualMap"
IMAGE_NAME = "research2/dualmap-smoke:latest"
TMUX_SESSION = "e005_m06_dualmap_bootstrap"
VERIFY_VERSION = "e005_m06_dualmap_bootstrap_verifier_v0"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def run(command: list[str], cwd: Path | None = None, input_text: str | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
    }


def tmux_has_session(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session])["ok"]


def read_tail(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - max_chars), 0)
        return handle.read().decode("utf-8", errors="replace")


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M06 DualMap Bootstrap Verification",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session running: {str(coverage['tmux_session_running']).lower()}.",
        f"- background status: `{coverage['background_status'].get('status')}`.",
        f"- local `mobileclip` submodule ready: {str(coverage['local_mobileclip_ready']).lower()}.",
        f"- Docker image ready: {str(coverage['image_ready']).lower()}.",
        f"- Docker image id: `{coverage.get('image_id') or ''}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- log exists: {str(coverage['log_exists']).lower()}.",
        f"- log size bytes: {coverage['log_size_bytes']}.",
        "",
        "## Paper Claim Boundary",
        "",
        "- E005-M06 verification only supports environment/bootstrap readiness or failure diagnosis.",
        "- It does not support `DualMap` baseline performance, final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
        "",
        "## Agent Inference",
        "",
        "- If status remains running, do not monitor continuously.",
        "- If image readiness passes, the next unit can run a one-scan `DualMap` runtime smoke on the materialized staged root.",
        "- If image build fails, inspect only targeted log tail and decide whether to repair `DualMap` or switch to `ConceptGraphs`.",
        "",
        "## User Decision Needed",
        "",
        "- None while the bootstrap job is still running.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--sudo-password-env", default="E005_M06_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    launch = read_json(args.out_dir / "coverage.json")
    background_status_path = Path(launch.get("background_status_path", args.out_dir / "background_status.json"))
    background_status = read_json(background_status_path)
    log_path = Path(launch.get("log_path", ""))
    sudo_password = read_sudo_password(
        env_name=args.sudo_password_env,
        use_stdin=args.sudo_password_stdin,
    )

    submodule_probe = run(["git", "submodule", "status", "--recursive"], cwd=DUALMAP_REPO)
    local_mobileclip_ready = (
        (DUALMAP_REPO / "3rdparty" / "mobileclip" / "setup.py").exists()
        and submodule_probe["ok"]
        and not any(line.startswith("-") for line in submodule_probe["stdout_tail"].splitlines())
    )

    image_probe = {"ok": False, "stdout_tail": "", "stderr_tail": "", "returncode": None}
    if sudo_password:
        image_probe = run(
            ["sudo", "-S", "docker", "image", "inspect", IMAGE_NAME, "--format", "{{.Id}} {{.Size}}"],
            input_text=sudo_password,
        )
    image_ready = image_probe.get("ok", False) and bool(image_probe.get("stdout_tail", "").strip())
    image_id = ""
    image_size_bytes: int | None = None
    if image_ready:
        parts = image_probe["stdout_tail"].strip().split()
        image_id = parts[0] if parts else ""
        if len(parts) > 1:
            try:
                image_size_bytes = int(parts[1])
            except ValueError:
                image_size_bytes = None

    running = tmux_has_session(launch.get("tmux_session", TMUX_SESSION))
    log_exists = log_path.exists()
    log_size = log_path.stat().st_size if log_exists else 0
    log_tail = read_tail(log_path)

    if running:
        status = "e005_m06_dualmap_bootstrap_running"
    elif local_mobileclip_ready and image_ready:
        status = "e005_m06_dualmap_bootstrap_ready"
    elif background_status.get("status") == "failed":
        status = "e005_m06_dualmap_bootstrap_failed"
    else:
        status = "e005_m06_dualmap_bootstrap_needs_verification"

    coverage = {
        "background_status": background_status,
        "image_id": image_id,
        "image_name": IMAGE_NAME,
        "image_probe": image_probe,
        "image_ready": image_ready,
        "image_size_bytes": image_size_bytes,
        "launch_coverage": str(args.out_dir / "coverage.json"),
        "local_mobileclip_ready": local_mobileclip_ready,
        "log_exists": log_exists,
        "log_path": str(log_path),
        "log_size_bytes": log_size,
        "log_tail": log_tail,
        "status": status,
        "submodule_probe": submodule_probe,
        "tmux_session": launch.get("tmux_session", TMUX_SESSION),
        "tmux_session_running": running,
        "verify_version": VERIFY_VERSION,
    }
    verify_dir = args.out_dir / "verification"
    write_json(verify_dir / "coverage.json", coverage)
    write_text(verify_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status in {"e005_m06_dualmap_bootstrap_running", "e005_m06_dualmap_bootstrap_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
