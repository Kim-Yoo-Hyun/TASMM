#!/usr/bin/env python3
"""Verify the E005-M25 ConceptGraphs Docker build background job."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LAUNCH_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M25_conceptgraphs_docker_build_preflight_v0"
OUT_DIR = LAUNCH_DIR / "verification"
SESSION = "e005_m25_conceptgraphs_docker_build"
IMAGE = "research2/conceptgraphs-smoke:latest"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001 - verifier should record failures.
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def tmux_running() -> bool:
    return run(["tmux", "has-session", "-t", SESSION], timeout=10)["ok"]


def image_state(image: str) -> dict[str, Any]:
    result = run(["docker", "image", "inspect", image, "--format", "{{.Id}} {{.Size}}"], timeout=20)
    if not result["ok"] or not result["stdout"]:
        return {"exists": False, "image": image, "image_id": None, "size_bytes": 0, "inspect": result}
    parts = result["stdout"].split()
    size = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return {"exists": True, "image": image, "image_id": parts[0], "size_bytes": size, "inspect": result}


def run_import_smoke(image: str) -> dict[str, Any]:
    return run(["docker", "run", "--rm", image, "python", "/opt/research2/import_smoke.py"], timeout=120)


def tail_log(log_path: str, lines: int = 80) -> dict[str, Any]:
    if not log_path:
        return {"exists": False, "tail": ""}
    path = Path(log_path)
    if not path.exists():
        return {"exists": False, "tail": ""}
    result = run(["tail", "-n", str(lines), str(path)], timeout=10)
    return {"exists": True, "tail": result["stdout"] if result["ok"] else result["stderr"]}


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M25 ConceptGraphs Docker Build Verification",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux running: {str(coverage['tmux_running']).lower()}.",
        f"- background status: `{coverage['background_status'].get('status', 'missing')}`.",
        f"- image exists: {str(coverage['image_state']['exists']).lower()}.",
        f"- image id: `{coverage['image_state'].get('image_id')}`.",
        f"- image size bytes: {coverage['image_state'].get('size_bytes', 0)}.",
        f"- import smoke executed: {str(coverage['import_smoke_executed']).lower()}.",
        f"- import smoke ok: {str(coverage['import_smoke_ok']).lower()}.",
        f"- log path: `{coverage['log_path']}`.",
        "",
        "## Claim Boundary",
        "",
        "- This verification checks container build/import readiness only.",
        "- One-scan `ConceptGraphs` runtime output and baseline comparison remain unsupported before E005-M26/M27.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    launch = read_json(LAUNCH_DIR / "coverage.json")
    background_status = read_json(Path(launch.get("background_status_path", "")))
    running = tmux_running()
    image = image_state(IMAGE)
    import_smoke = {"ok": False, "stdout": "", "stderr": "not_executed"}
    import_executed = False
    if image["exists"] and not running:
        import_smoke = run_import_smoke(IMAGE)
        import_executed = True

    if running:
        status = "e005_m25_conceptgraphs_docker_build_running"
    elif background_status.get("status") == "completed" and image["exists"] and import_smoke["ok"]:
        status = "e005_m25_conceptgraphs_docker_build_ready"
    elif background_status.get("status") == "failed":
        status = "e005_m25_conceptgraphs_docker_build_failed"
    elif image["exists"] and not import_smoke["ok"]:
        status = "e005_m25_conceptgraphs_import_smoke_failed"
    else:
        status = "e005_m25_conceptgraphs_docker_build_needs_verification"

    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_running": running,
        "background_status": background_status,
        "image_state": image,
        "import_smoke_executed": import_executed,
        "import_smoke_ok": bool(import_smoke["ok"]),
        "import_smoke_stdout_head": "\n".join(import_smoke.get("stdout", "").splitlines()[:80]),
        "import_smoke_stderr_tail": "\n".join(import_smoke.get("stderr", "").splitlines()[-80:]),
        "log_path": launch.get("log_path"),
        "log_tail": tail_log(launch.get("log_path", ""), 80),
        "next_recommended_unit": "E005-M26 ConceptGraphs Docker build completion verification"
        if status == "e005_m25_conceptgraphs_docker_build_running"
        else "E005-M26 ConceptGraphs import/runtime preflight"
        if status == "e005_m25_conceptgraphs_docker_build_ready"
        else "Inspect E005-M25 Docker build log tail",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
