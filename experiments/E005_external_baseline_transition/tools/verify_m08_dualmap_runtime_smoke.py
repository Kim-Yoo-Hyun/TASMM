#!/usr/bin/env python3
"""Verify the E005-M08 DualMap one-scan runtime smoke background job."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M08_dualmap_one_scan_runtime_smoke_v0"
TMUX_SESSION = "e005_m08_dualmap_runtime"
VERIFY_VERSION = "e005_m08_dualmap_runtime_smoke_verifier_v0"


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


def run(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
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


def read_tail(path: Path, max_chars: int = 8000) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - max_chars), 0)
        return handle.read().decode("utf-8", errors="replace")


def output_inventory(output_path: Path) -> dict[str, Any]:
    pkl_files = sorted(output_path.glob("*/map/*.pkl")) if output_path.exists() else []
    layout_files = sorted(output_path.glob("*/map/layout.pcd")) if output_path.exists() else []
    system_time_files = sorted(output_path.glob("*/system_time.csv")) if output_path.exists() else []
    log_files = sorted(output_path.glob("log/*.log")) if output_path.exists() else []
    return {
        "output_path_exists": output_path.exists(),
        "pkl_count": len(pkl_files),
        "layout_pcd_count": len(layout_files),
        "system_time_count": len(system_time_files),
        "dualmap_log_count": len(log_files),
        "sample_pkl": str(pkl_files[0]) if pkl_files else "",
        "sample_layout_pcd": str(layout_files[0]) if layout_files else "",
        "sample_system_time": str(system_time_files[0]) if system_time_files else "",
        "sample_dualmap_log": str(log_files[-1]) if log_files else "",
    }


def detect_failure_signals(log_tail: str, background_status: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    if background_status.get("status") == "failed":
        signals.append(f"background_status_failed_returncode_{background_status.get('returncode')}")
    if "CUDA out of memory" in log_tail:
        signals.append("cuda_out_of_memory")
    if "Detector][Init] Error loading CLIP model" in log_tail:
        signals.append("clip_model_init_failed")
    if "Detector' object has no attribute 'yolo'" in log_tail:
        signals.append("yolo_not_initialized_after_detector_init_failure")
    if "Detector' object has no attribute 'fastsam'" in log_tail:
        signals.append("fastsam_not_initialized_after_detector_init_failure")
    if "Error executing job with overrides" in log_tail:
        signals.append("hydra_job_error")
    return signals


def build_report(coverage: dict[str, Any]) -> str:
    inv = coverage["output_inventory"]
    failure_signals = coverage.get("failure_signals", [])
    lines = [
        "# E005-M08 DualMap One-Scan Runtime Smoke Verification",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session running: {str(coverage['tmux_session_running']).lower()}.",
        f"- background status: `{coverage['background_status'].get('status')}`.",
        f"- output path: `{coverage['output_path']}`.",
        f"- output path exists: {str(inv['output_path_exists']).lower()}.",
        f"- runtime object `*.pkl` count: {inv['pkl_count']}.",
        f"- `layout.pcd` count: {inv['layout_pcd_count']}.",
        f"- `system_time.csv` count: {inv['system_time_count']}.",
        f"- DualMap log count: {inv['dualmap_log_count']}.",
        f"- launch log path: `{coverage['log_path']}`.",
        f"- launch log exists: {str(coverage['log_exists']).lower()}.",
        f"- launch log size bytes: {coverage['log_size_bytes']}.",
        f"- failure signals: {', '.join(failure_signals) if failure_signals else 'none'}.",
        "",
        "## Paper Claim Boundary",
        "",
        "- E005-M08 verification only supports runtime-smoke readiness or failure diagnosis.",
        "- Runtime file presence alone does not support `DualMap` baseline performance.",
        "- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
        "## Agent Inference",
        "",
        "- If status remains running, do not monitor continuously.",
        "- If runtime outputs are ready, inspect runtime object `*.pkl` schema before building an E004/E005 adapter.",
        "- If runtime failed, record the blocker before relaunching; current failure signals are not map-quality evidence.",
        "",
        "## User Decision Needed",
        "",
        "- None before the next bounded repair/relaunch route decision.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    launch = read_json(args.out_dir / "coverage.json")
    background_status_path = Path(launch.get("background_status_path", args.out_dir / "background_status.json"))
    background_status = read_json(background_status_path)
    log_path = Path(launch.get("log_path", ""))
    output_path = Path(launch.get("output_path", ""))
    running = tmux_has_session(launch.get("tmux_session", TMUX_SESSION))
    inventory = output_inventory(output_path)
    log_exists = log_path.exists()
    log_size = log_path.stat().st_size if log_exists else 0
    log_tail = read_tail(log_path)
    failure_signals = detect_failure_signals(log_tail, background_status)

    if running:
        status = "e005_m08_dualmap_runtime_running"
    elif inventory["pkl_count"] > 0 and inventory["layout_pcd_count"] > 0 and inventory["system_time_count"] > 0:
        status = "e005_m08_dualmap_runtime_outputs_ready"
    elif background_status.get("status") == "failed":
        status = "e005_m08_dualmap_runtime_failed"
    elif background_status.get("status") == "completed":
        status = "e005_m08_dualmap_runtime_completed_missing_expected_outputs"
    else:
        status = "e005_m08_dualmap_runtime_needs_verification"

    coverage = {
        "background_status": background_status,
        "launch_coverage": str(args.out_dir / "coverage.json"),
        "log_exists": log_exists,
        "log_path": str(log_path),
        "log_size_bytes": log_size,
        "log_tail": log_tail,
        "failure_signals": failure_signals,
        "output_inventory": inventory,
        "output_path": str(output_path),
        "status": status,
        "tmux_session": launch.get("tmux_session", TMUX_SESSION),
        "tmux_session_running": running,
        "verify_version": VERIFY_VERSION,
    }
    verify_dir = args.out_dir / "verification"
    write_json(verify_dir / "coverage.json", coverage)
    write_text(verify_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status in {"e005_m08_dualmap_runtime_running", "e005_m08_dualmap_runtime_outputs_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
