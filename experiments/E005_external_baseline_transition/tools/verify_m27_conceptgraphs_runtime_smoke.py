#!/usr/bin/env python3
"""Verify E005-M27 ConceptGraphs one-scan runtime smoke."""

from __future__ import annotations

import glob
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LAUNCH_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
OUT_DIR = LAUNCH_DIR / "verification"
SESSION = "e005_m27_conceptgraphs_runtime_smoke"


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


def tail_log(path: str, lines: int = 120) -> dict[str, Any]:
    if not path:
        return {"exists": False, "tail": ""}
    log_path = Path(path)
    if not log_path.exists():
        return {"exists": False, "tail": ""}
    result = run(["tail", "-n", str(lines), str(log_path)], timeout=10)
    return {"exists": True, "tail": result["stdout"] if result["ok"] else result["stderr"]}


def output_inventory(expected: dict[str, str]) -> dict[str, Any]:
    gsa_files = sorted(glob.glob(expected.get("gsa_detection_pattern", "")))
    full_pcd = Path(expected.get("full_pcd", ""))
    full_pcd_post = Path(expected.get("full_pcd_post", ""))
    return {
        "gsa_detection_count": len(gsa_files),
        "sample_gsa_detection": gsa_files[0] if gsa_files else "",
        "full_pcd_exists": full_pcd.exists(),
        "full_pcd_size_bytes": full_pcd.stat().st_size if full_pcd.exists() else 0,
        "full_pcd_post_exists": full_pcd_post.exists(),
        "full_pcd_post_size_bytes": full_pcd_post.stat().st_size if full_pcd_post.exists() else 0,
    }


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M27 ConceptGraphs Runtime Smoke Verification",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux running: {str(coverage['tmux_running']).lower()}.",
        f"- background status: `{coverage['background_status'].get('status', 'missing')}`.",
        f"- GSA detections: {coverage['output_inventory']['gsa_detection_count']}.",
        f"- full pcd exists: {str(coverage['output_inventory']['full_pcd_exists']).lower()}.",
        f"- post pcd exists: {str(coverage['output_inventory']['full_pcd_post_exists']).lower()}.",
        f"- log path: `{coverage['log_path']}`.",
        "",
        "## Claim Boundary",
        "",
        "- Runtime smoke readiness is not a paper-result baseline comparison.",
        "- Query-level conversion and metric evaluation remain separate gates.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    launch = read_json(LAUNCH_DIR / "coverage.json")
    background_status = read_json(Path(launch.get("background_status_path", "")))
    running = tmux_running()
    inventory = output_inventory(launch.get("expected_outputs", {}))
    if running:
        status = "e005_m27_conceptgraphs_runtime_smoke_running"
    elif background_status.get("status") == "completed" and inventory["gsa_detection_count"] > 0 and inventory["full_pcd_exists"]:
        status = "e005_m27_conceptgraphs_runtime_smoke_outputs_ready"
    elif background_status.get("status") == "failed":
        status = "e005_m27_conceptgraphs_runtime_smoke_failed"
    elif launch.get("status") == "e005_m27_conceptgraphs_runtime_smoke_blocked_preflight":
        status = "e005_m27_conceptgraphs_runtime_smoke_blocked_preflight"
    else:
        status = "e005_m27_conceptgraphs_runtime_smoke_needs_verification"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_running": running,
        "background_status": background_status,
        "launch_status": launch.get("status"),
        "blockers": launch.get("blockers", []),
        "output_inventory": inventory,
        "log_path": launch.get("log_path"),
        "log_tail": tail_log(launch.get("log_path", ""), 120),
        "next_recommended_unit": "E005-M27 runtime smoke completion verification"
        if status == "e005_m27_conceptgraphs_runtime_smoke_running"
        else "E005-M28 ConceptGraphs output schema inspection"
        if status == "e005_m27_conceptgraphs_runtime_smoke_outputs_ready"
        else "E005-M26 Docker build completion verification"
        if status == "e005_m27_conceptgraphs_runtime_smoke_blocked_preflight"
        else "Inspect E005-M27 runtime log tail",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
