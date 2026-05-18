#!/usr/bin/env python3
"""Verify E005-M39 heldout sequence staging completion for ConceptGraphs."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "E005_external_baseline_transition"
M38_DIR = EXP_DIR / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
M39_DIR = EXP_DIR / "artifacts" / "E005-M39_conceptgraphs_heldout_sequence_launch_v0"
DEFAULT_OUT_DIR = EXP_DIR / "artifacts" / "E005-M40_heldout_sequence_staging_verification_v0"
TMUX_SESSION = "e005_m39_conceptgraphs_heldout_sequence"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def count_sequence_files(sequence_dir: Path) -> dict[str, int]:
    if not sequence_dir.exists():
        return {
            "color_frames": 0,
            "depth_frames": 0,
            "pose_frames": 0,
            "frame_triplet_lower_bound": 0,
        }
    color_frames = len(list(sequence_dir.glob("*.color.jpg")))
    depth_frames = len(list(sequence_dir.glob("*.depth.pgm")))
    pose_frames = len(list(sequence_dir.glob("*.pose.txt")))
    return {
        "color_frames": color_frames,
        "depth_frames": depth_frames,
        "pose_frames": pose_frames,
        "frame_triplet_lower_bound": min(color_frames, depth_frames, pose_frames),
    }


def zip_status(path: Path) -> tuple[bool, int | None, str | None]:
    if not path.exists():
        return False, None, "missing_zip"
    try:
        with zipfile.ZipFile(path) as zf:
            bad_member = zf.testzip()
            if bad_member:
                return False, len(zf.namelist()), f"bad_zip_member:{bad_member}"
            return True, len(zf.namelist()), None
    except zipfile.BadZipFile:
        return False, None, "bad_zip_file"


def verify_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    scan_id = str(row["scan_id"])
    scan_dir = Path(str(row["scan_dir"]))
    zip_path = Path(str(row["sequence_zip_path"]))
    sequence_dir = Path(str(row["sequence_dir"]))
    valid_zip, zip_entries, zip_error = zip_status(zip_path)
    counts = count_sequence_files(sequence_dir)
    ready = bool(valid_zip and sequence_dir.exists() and counts["frame_triplet_lower_bound"] > 0)
    return {
        **counts,
        "has_info": (sequence_dir / "_info.txt").exists(),
        "ready": ready,
        "scan_dir": str(scan_dir),
        "scan_dir_ready": scan_dir.exists(),
        "scan_id": scan_id,
        "sequence_dir": str(sequence_dir),
        "sequence_dir_ready": sequence_dir.exists(),
        "sequence_zip_path": str(zip_path),
        "sequence_zip_ready": zip_path.exists(),
        "sequence_zip_valid": valid_zip,
        "zip_entries": zip_entries,
        "zip_error": zip_error,
    }


def tmux_session_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def tail_text(path: Path, max_bytes: int = 65536) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - max_bytes), 0)
        return f.read().decode("utf-8", errors="replace")


def write_report(path: Path, coverage: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    lines = [
        "# E005-M40 Heldout Sequence Staging Verification",
        "",
        "## Status",
        "",
        str(coverage["status"]),
        "",
        "## Facts",
        "",
        f"- Manifest rows: {coverage['manifest_rows']}.",
        f"- Ready rows: {coverage['ready_rows']}.",
        f"- tmux session stopped: {str(coverage['tmux_session_stopped']).lower()}.",
        f"- Total frame triplet lower bound: {coverage['total_frame_triplet_lower_bound']}.",
        f"- Minimum frame triplet lower bound: {coverage['min_frame_triplet_lower_bound']}.",
        f"- Sequence zip valid rows: {coverage['sequence_zip_valid_rows']}.",
        f"- Heldout query rows after exclusion: {coverage['heldout_query_rows_after_exclusion']}.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Target Scans",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}`: ready {ready}, triplets {triplets}, zip valid {zip_valid}, zip entries {zip_entries}.".format(
                scan_id=row["scan_id"],
                ready=str(row["ready"]).lower(),
                triplets=row["frame_triplet_lower_bound"],
                zip_valid=str(row["sequence_zip_valid"]).lower(),
                zip_entries=row["zip_entries"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M40 verifies heldout sequence staging only.",
            "- E005-M40 does not support `ConceptGraphs` heldout runtime performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.",
            "",
            "## Agent Inference",
            "",
            "- Heldout runtime can be planned next because all 9 heldout scans have valid `sequence.zip` files and extracted color/depth/pose triplets.",
            "- The next bottleneck moves from data acquisition to `ConceptGraphs` staging materialization/runtime over the 9 heldout scans.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=M39_DIR / "download_manifest.jsonl", type=Path)
    parser.add_argument("--m39-coverage", default=M39_DIR / "coverage.json", type=Path)
    parser.add_argument("--heldout-contract", default=M38_DIR / "heldout_contract.json", type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_rows = load_jsonl(args.manifest)
    m39_coverage = load_json(args.m39_coverage)
    heldout_contract = load_json(args.heldout_contract)
    rows = [verify_manifest_row(row) for row in manifest_rows]

    ready_rows = sum(1 for row in rows if row["ready"])
    valid_zip_rows = sum(1 for row in rows if row["sequence_zip_valid"])
    triplets = [int(row["frame_triplet_lower_bound"]) for row in rows]
    target_scan_ids = [row["scan_id"] for row in rows]
    expected_scan_ids = heldout_contract["next_execution_requirements"]["missing_sequence_scan_ids"]
    expected_scan_set_match = sorted(target_scan_ids) == sorted(expected_scan_ids)
    session_running = tmux_session_running(TMUX_SESSION)
    log_path = Path(str(m39_coverage["log_path"]))
    log_tail = tail_text(log_path)
    log_has_ready_status = '"status": "sequence_payloads_ready"' in log_tail
    all_ready = (
        ready_rows == len(rows)
        and valid_zip_rows == len(rows)
        and expected_scan_set_match
        and not session_running
    )
    coverage = {
        "all_target_scans_ready": ready_rows == len(rows),
        "expected_scan_set_match": expected_scan_set_match,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "heldout_query_rows_after_exclusion": heldout_contract["next_execution_requirements"][
            "heldout_query_rows_after_exclusion"
        ],
        "log_has_ready_status_in_tail": log_has_ready_status,
        "log_path": str(log_path),
        "m39_status_at_launch": m39_coverage["status"],
        "m40_version": "e005_m40_heldout_sequence_staging_verification_v0",
        "manifest_rows": len(rows),
        "max_frame_triplet_lower_bound": max(triplets) if triplets else 0,
        "min_frame_triplet_lower_bound": min(triplets) if triplets else 0,
        "next_recommended_unit": "E005-M41 ConceptGraphs heldout runtime preflight / launch plan",
        "paper_table_claim_ready": False,
        "ready_rows": ready_rows,
        "real_navigation_claim_ready": False,
        "require_ready": bool(args.require_ready),
        "sequence_zip_valid_rows": valid_zip_rows,
        "status": "e005_m40_heldout_sequence_staging_ready" if all_ready else "e005_m40_heldout_sequence_staging_not_ready",
        "target_scan_ids": target_scan_ids,
        "tmux_session": TMUX_SESSION,
        "tmux_session_running": session_running,
        "tmux_session_stopped": not session_running,
        "total_frame_triplet_lower_bound": sum(triplets),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_jsonl(args.out_dir / "sequence_rows.jsonl", rows)
    write_report(args.out_dir / "report.md", coverage, rows)
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and not all_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
