#!/usr/bin/env python3
"""Verify sequence payload readiness for E003-M56 target scans."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "E003-M56_current_rescan_sequence_staging_plan_v0"
    / "download_manifest.jsonl"
)
DEFAULT_OUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "E003-M56_current_rescan_sequence_staging_plan_v0"
    / "verification"
)


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


def verify_row(row: dict[str, Any]) -> dict[str, Any]:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless every manifest row is sequence-ready.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_rows = load_jsonl(args.manifest)
    rows = [verify_row(row) for row in manifest_rows]
    ready_rows = sum(1 for row in rows if row["ready"])
    coverage = {
        "manifest_rows": len(manifest_rows),
        "ready_rows": ready_rows,
        "require_ready": bool(args.require_ready),
        "status": "sequence_payloads_ready" if ready_rows == len(rows) else "sequence_payloads_not_ready",
        "target_scan_ids": [row["scan_id"] for row in rows],
        "verification_version": "e003_m56_sequence_payload_verifier_v0",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_jsonl(args.out_dir / "verification_rows.jsonl", rows)
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and ready_rows != len(rows):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
