#!/usr/bin/env python3
"""Verify E008-M107 ConceptGraphs HM3D source-gap runtime outputs."""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M106_ROOT = (
    ROOT
    / "experiments"
    / "E008_real_navigation_benchmark"
    / "artifacts"
    / "E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


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
    except Exception as exc:  # noqa: BLE001 - verifier records local command failures.
        return {"cmd": cmd, "ok": False, "returncode": None, "stderr": repr(exc), "stdout": ""}


def tmux_running(session: str) -> bool:
    if not session:
        return False
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
        "scan_id": expected.get("scan_id"),
        "gsa_detection_count": len(gsa_files),
        "sample_gsa_detection": gsa_files[0] if gsa_files else "",
        "full_pcd_exists": full_pcd.exists(),
        "full_pcd_size_bytes": full_pcd.stat().st_size if full_pcd.exists() else 0,
        "full_pcd_post_exists": full_pcd_post.exists(),
        "full_pcd_post_size_bytes": full_pcd_post.stat().st_size if full_pcd_post.exists() else 0,
        "runtime_output_ready": len(gsa_files) > 0 and full_pcd.exists() and full_pcd_post.exists(),
    }


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E008-M108 ConceptGraphs HM3D Source-Gap Runtime Verification",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M106 status: `{coverage['m106_status']}`.",
        f"- tmux running: {str(coverage['tmux_running']).lower()}.",
        f"- Background status: `{coverage['background_status'].get('status', 'missing')}`.",
        f"- Ready scans: {coverage['ready_scan_count']} / {coverage['expected_scan_count']}.",
        f"- Log path: `{coverage['log_path']}`.",
        "",
        "## Claim Boundary",
        "",
        "- M108 verifies runtime output availability only.",
        "- Candidate export, coordinate validation, source-gap recovery, trajectory execution, and final navigation claims remain separate gates.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m106-root", default=str(DEFAULT_M106_ROOT))
    parser.add_argument("--out-root", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m106_root = Path(args.m106_root)
    out_root = Path(args.out_root) if args.out_root else m106_root / "verification" / "m108"
    m106 = read_json(m106_root / "coverage.json")
    expected_rows = read_jsonl(m106_root / "expected_output_rows.jsonl")
    background_status = read_json(Path(str(m106.get("background_status_path", ""))))
    running = tmux_running(str(m106.get("tmux_session", "")))
    inventory = [inventory_row(row) for row in expected_rows]
    ready_count = sum(1 for row in inventory if row["runtime_output_ready"])
    background_state = background_status.get("status")
    runtime_outputs_ready = len(expected_rows) > 0 and ready_count == len(expected_rows)
    if background_state == "completed" and runtime_outputs_ready:
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_outputs_ready"
    elif background_state == "failed":
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_failed"
    elif running:
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_running"
    elif m106.get("status", "").endswith("waiting_gpu") and ready_count == 0 and not background_status:
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_waiting_gpu"
    elif not background_status and ready_count == 0:
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_not_launched"
    else:
        status = "e008_m108_conceptgraphs_hm3d_source_gap_runtime_needs_verification"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m106_root": str(m106_root),
        "m106_status": m106.get("status"),
        "tmux_session": m106.get("tmux_session"),
        "tmux_running": running,
        "background_status": background_status,
        "expected_scan_count": len(expected_rows),
        "ready_scan_count": ready_count,
        "runtime_outputs_ready": runtime_outputs_ready,
        "inventory": inventory,
        "log_path": m106.get("log_path"),
        "log_tail": tail_log(str(m106.get("log_path", "")), 80),
        "candidate_rows_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": {
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_outputs_ready": (
                "E008-M109 ConceptGraphs HM3D candidate export adapter contract"
            ),
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_running": (
                "E008-M108 completion verification after background job finishes"
            ),
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_waiting_gpu": (
                "E008-M107 launch when GPU memory is available"
            ),
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_not_launched": (
                "E008-M107 launch when GPU memory is available"
            ),
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_failed": (
                "Inspect E008-M107 log and repair runtime inputs"
            ),
            "e008_m108_conceptgraphs_hm3d_source_gap_runtime_needs_verification": (
                "Inspect M107 status/output mismatch"
            ),
        }[status],
    }
    write_json(out_root / "coverage.json", coverage)
    write_jsonl(out_root / "runtime_inventory_rows.jsonl", inventory)
    write_text(out_root / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
