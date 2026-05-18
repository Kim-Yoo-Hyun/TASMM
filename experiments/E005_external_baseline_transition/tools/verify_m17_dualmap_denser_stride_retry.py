#!/usr/bin/env python3
"""Verify the E005-M17 DualMap denser-stride object-output retry."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M17_dualmap_denser_stride_retry_v0"
TMUX_SESSION = "e005_m17_dualmap_denser_stride_retry"
VERIFY_VERSION = "e005_m17_dualmap_denser_stride_retry_verifier_v0"


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


def run(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def int_from_regex(text: str, pattern: str, default: int = 0) -> int:
    match = re.search(pattern, text)
    if not match:
        return default
    return int(match.group(1))


def local_object_counts(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"Local Objects num: (\d+)", text)]


def output_inventory(output_path: Path) -> dict[str, Any]:
    pkl_files = sorted(output_path.glob("*/map/*.pkl")) if output_path.exists() else []
    layout_files = sorted(output_path.glob("*/map/layout.pcd")) if output_path.exists() else []
    system_time_files = sorted(output_path.glob("*/system_time.csv")) if output_path.exists() else []
    detector_time_files = sorted(output_path.glob("*/detector_time.csv")) if output_path.exists() else []
    log_files = sorted(output_path.glob("log/*.log")) if output_path.exists() else []
    return {
        "output_path_exists": output_path.exists(),
        "pkl_count": len(pkl_files),
        "layout_pcd_count": len(layout_files),
        "system_time_count": len(system_time_files),
        "detector_time_count": len(detector_time_files),
        "dualmap_log_count": len(log_files),
        "sample_pkl": str(pkl_files[0]) if pkl_files else "",
        "sample_layout_pcd": str(layout_files[0]) if layout_files else "",
        "sample_system_time": str(system_time_files[0]) if system_time_files else "",
        "sample_detector_time": str(detector_time_files[0]) if detector_time_files else "",
        "sample_dualmap_log": str(log_files[-1]) if log_files else "",
    }


def detect_failure_signals(log_tail: str, dualmap_log_text: str, background_status: dict[str, Any]) -> list[str]:
    combined = f"{log_tail}\n{dualmap_log_text[-8000:]}"
    signals: list[str] = []
    if background_status.get("status") == "failed":
        signals.append(f"background_status_failed_returncode_{background_status.get('returncode')}")
    if "CUDA out of memory" in combined:
        signals.append("cuda_out_of_memory")
    if "Error loading YOLO model" in combined:
        signals.append("yolo_model_init_failed")
    if "Error loading SAM model" in combined:
        signals.append("sam_model_init_failed")
    if "Error loading FASTSAM model" in combined:
        signals.append("fastsam_model_init_failed")
    if "Permission denied" in combined:
        signals.append("permission_denied")
    if "Detector' object has no attribute" in combined:
        signals.append("detector_attribute_missing_after_init_failure")
    if "Error executing job with overrides" in combined:
        signals.append("hydra_job_error")
    if "Failed to download" in combined or "MaxRetryError" in combined:
        signals.append("model_download_failed")
    return signals


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
    dualmap_log_path = Path(inventory.get("sample_dualmap_log", ""))
    dualmap_log_text = read_text(dualmap_log_path)
    counts = local_object_counts(dualmap_log_text)
    processed_keyframes = len(re.findall(r"\[Main\] Keyframe idx:", dualmap_log_text))
    configured_stride = int_from_regex(dualmap_log_text, r"stride: (\d+)", default=0)
    configured_stable_num = int_from_regex(dualmap_log_text, r"stable_num: (\d+)", default=0)
    failure_signals = detect_failure_signals(log_tail, dualmap_log_text, background_status)
    if running:
        status = "e005_m17_dualmap_denser_stride_retry_running"
    elif inventory["pkl_count"] > 0 and inventory["layout_pcd_count"] > 0 and inventory["system_time_count"] > 0:
        status = "e005_m17_dualmap_denser_stride_retry_outputs_ready"
    elif background_status.get("status") == "failed" or failure_signals:
        status = "e005_m17_dualmap_denser_stride_retry_failed"
    elif background_status.get("status") == "completed":
        status = "e005_m17_dualmap_denser_stride_retry_completed_missing_expected_outputs"
    else:
        status = "e005_m17_dualmap_denser_stride_retry_needs_verification"
    coverage = {
        "background_status": background_status,
        "configured_stable_num": configured_stable_num,
        "configured_stride": configured_stride,
        "failure_signals": failure_signals,
        "final_local_object_count": counts[-1] if counts else 0,
        "first_local_object_count": counts[0] if counts else 0,
        "launch_coverage": str(args.out_dir / "coverage.json"),
        "log_exists": log_exists,
        "log_path": str(log_path),
        "log_size_bytes": log_size,
        "log_tail": log_tail,
        "max_local_object_count": max(counts) if counts else 0,
        "output_inventory": inventory,
        "output_path": str(output_path),
        "processed_keyframes": processed_keyframes,
        "status": status,
        "tmux_session": launch.get("tmux_session", TMUX_SESSION),
        "tmux_session_running": running,
        "verify_version": VERIFY_VERSION,
    }
    verify_dir = args.out_dir / "verification"
    write_json(verify_dir / "coverage.json", coverage)
    write_text(verify_dir / "report.md", json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status in {"e005_m17_dualmap_denser_stride_retry_running", "e005_m17_dualmap_denser_stride_retry_outputs_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
