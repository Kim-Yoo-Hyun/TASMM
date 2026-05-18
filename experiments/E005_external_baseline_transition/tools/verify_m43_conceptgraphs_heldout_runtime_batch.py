#!/usr/bin/env python3
"""Verify a launched E005-M43 ConceptGraphs heldout runtime batch."""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "E005_external_baseline_transition"
M43_DIR = EXP_DIR / "artifacts" / "E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout)
        return {
            "cmd": cmd,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "ok": False, "returncode": None, "stderr": repr(exc), "stdout": ""}


def tmux_running(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session], timeout=10)["ok"]


def tail_log(path: str, lines: int = 80) -> dict[str, Any]:
    if not path:
        return {"exists": False, "tail": ""}
    log_path = Path(path)
    if not log_path.exists():
        return {"exists": False, "tail": ""}
    result = run(["tail", "-n", str(lines), str(log_path)], timeout=10)
    return {"exists": True, "tail": result["stdout"] if result["ok"] else result["stderr"]}


def inventory_row(expected: dict[str, Any]) -> dict[str, Any]:
    gsa_files = sorted(glob.glob(str(expected.get("gsa_detection_pattern", ""))))
    full_pcd = Path(str(expected.get("full_pcd", "")))
    full_pcd_post = Path(str(expected.get("full_pcd_post", "")))
    return {
        "full_pcd_exists": full_pcd.exists(),
        "full_pcd_post_exists": full_pcd_post.exists(),
        "full_pcd_post_size_bytes": full_pcd_post.stat().st_size if full_pcd_post.exists() else 0,
        "full_pcd_size_bytes": full_pcd.stat().st_size if full_pcd.exists() else 0,
        "gsa_detection_count": len(gsa_files),
        "sample_gsa_detection": gsa_files[0] if gsa_files else "",
        "scan_id": expected.get("scan_id"),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M43 ConceptGraphs Heldout Runtime Batch Verification",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Batch id: `{coverage['batch_id']}`.",
            f"- tmux running: {str(coverage['tmux_running']).lower()}.",
            f"- Background status: `{coverage['background_status'].get('status', 'missing')}`.",
            f"- Ready scans: {coverage['ready_scan_count']} / {coverage['expected_scan_count']}.",
            f"- Log path: `{coverage['log_path']}`.",
            "",
            "## Claim Boundary",
            "",
            "- E005-M43 verifies runtime output availability for one heldout batch only.",
            "- Query-level metric conversion remains a separate gate.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    launch = read_json(M43_DIR / "coverage.json")
    batch_id = args.batch_id or launch.get("batch_id", "")
    expected = read_jsonl(M43_DIR / f"expected_outputs_{batch_id}.jsonl")
    background = read_json(Path(launch.get("background_status_path", "")))
    running = tmux_running(str(launch.get("tmux_session", "")))
    inventory = [inventory_row(row) for row in expected]
    ready_count = sum(
        1 for row in inventory if row["gsa_detection_count"] > 0 and row["full_pcd_exists"] and row["full_pcd_post_exists"]
    )
    if launch.get("status", "").endswith("blocked_preflight"):
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_blocked_preflight"
    elif running:
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_running"
    elif background.get("status") == "completed" and ready_count == len(expected):
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_outputs_ready"
    elif background.get("status") == "failed":
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_failed"
    else:
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_needs_verification"

    out_dir = M43_DIR / "verification" / batch_id
    if status == "e005_m43_conceptgraphs_heldout_runtime_batch_blocked_preflight":
        next_unit = "E005-M43 relaunch when GPU memory is available"
    elif status == "e005_m43_conceptgraphs_heldout_runtime_batch_running":
        next_unit = "E005-M44 ConceptGraphs heldout runtime batch completion verification"
    else:
        next_unit = "E005-M45 heldout ConceptGraphs output-to-query metric conversion"

    coverage = {
        "background_status": background,
        "batch_id": batch_id,
        "expected_scan_count": len(expected),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "inventory": inventory,
        "launch_status": launch.get("status"),
        "log_path": launch.get("log_path"),
        "log_tail": tail_log(str(launch.get("log_path", "")), 80),
        "next_recommended_unit": next_unit,
        "ready_scan_count": ready_count,
        "status": status,
        "tmux_running": running,
    }
    write_json(out_dir / "coverage.json", coverage)
    write_text(out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
