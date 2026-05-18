#!/usr/bin/env python3
"""Verify E003-M70 OpenMask3D Docker build preflight status."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M70_openmask3d_docker_env_build_preflight_v0"
VERIFY_VERSION = "e003_m70_openmask3d_docker_build_verifier_v0"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def run_command(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-4000:],
        "stdout_tail": proc.stdout[-4000:],
    }


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def read_tail(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - max_chars), 0)
        return f.read().decode("utf-8", errors="replace")


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M70 OpenMask3D Docker Build Verification",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- tmux session running: {coverage['tmux_session_running']}.",
            f"- background status: `{coverage['background_status'].get('status')}`.",
            f"- image inspect ready: {coverage['image_ready']}.",
            f"- image id: `{coverage.get('image_id') or ''}`.",
            f"- log path: `{coverage['log_path']}`.",
            f"- log exists: {coverage['log_exists']}.",
            f"- log size bytes: {coverage['log_size_bytes']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M70 verification only supports Docker environment readiness or failure diagnosis.",
            "- It does not support `OpenMask3D` proposal-quality, real RGB-D robustness, or search-improvement claims.",
            "",
            "## 에이전트 추론",
            "",
            "- If status remains running, do not monitor continuously.",
            "- If build fails, inspect the recorded log tail and decide whether to fall back rather than repairing the environment indefinitely.",
            "- If image readiness passes, the next unit can be a minimal container import/GPU smoke before model inference.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the Docker build is still running.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    launch = load_json(args.out_dir / "coverage.json")
    background_status_path = Path(launch.get("background_status_path", args.out_dir / "background_status.json"))
    background_status = load_json(background_status_path)
    tmux_session = launch.get("tmux_session", "e003_m70_openmask3d_docker_build")
    running = tmux_has_session(tmux_session)
    image_name = launch.get("image_name", "research2/openmask3d-smoke:latest")
    image_probe = run_command(
        [
            "bash",
            "-lc",
            f"printf 'a\\n' | sudo -S docker image inspect {image_name!r} --format '{{{{.Id}}}} {{{{.Size}}}}' 2>/dev/null",
        ]
    )
    image_ready = image_probe["returncode"] == 0 and bool(image_probe["stdout_tail"].strip())
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

    log_path = Path(launch.get("log_path", ""))
    log_exists = log_path.exists()
    log_size = log_path.stat().st_size if log_exists else 0
    log_tail = read_tail(log_path)

    if running:
        status = "openmask3d_docker_build_running"
    elif image_ready:
        status = "openmask3d_docker_image_ready"
    elif background_status.get("status") == "failed":
        status = "openmask3d_docker_build_failed"
    else:
        status = "openmask3d_docker_build_not_ready"

    coverage = {
        "background_status": background_status,
        "image_id": image_id,
        "image_name": image_name,
        "image_probe": image_probe,
        "image_ready": image_ready,
        "image_size_bytes": image_size_bytes,
        "launch_coverage": str(args.out_dir / "coverage.json"),
        "log_exists": log_exists,
        "log_path": str(log_path),
        "log_size_bytes": log_size,
        "log_tail": log_tail,
        "status": status,
        "tmux_session": tmux_session,
        "tmux_session_running": running,
        "verify_version": VERIFY_VERSION,
    }
    verify_dir = args.out_dir / "verification"
    write_json(verify_dir / "coverage.json", coverage)
    write_text(verify_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status in {"openmask3d_docker_build_running", "openmask3d_docker_image_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
