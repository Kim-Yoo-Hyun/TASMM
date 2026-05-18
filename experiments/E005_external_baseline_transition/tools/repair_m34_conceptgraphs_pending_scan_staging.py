#!/usr/bin/env python3
"""Repair M33 pending ConceptGraphs staging for Docker-visible file reads."""

from __future__ import annotations

import json
import shutil
import stat
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M33_conceptgraphs_pending_scan_runtime_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M34_conceptgraphs_pending_scan_staging_repair_v0"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
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


def copy_symlink_target(path: Path) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return {"path": str(path), "status": "missing"}
    if not path.is_symlink():
        return {"path": str(path), "status": "already_regular", "size_bytes": path.stat().st_size}

    try:
        target = path.resolve(strict=True)
    except FileNotFoundError:
        return {"path": str(path), "status": "broken_symlink", "link_target": str(path.readlink())}

    tmp = path.with_name(f".{path.name}.tmp-copy")
    shutil.copyfile(target, tmp)
    shutil.copystat(target, tmp, follow_symlinks=True)
    path.unlink()
    tmp.replace(path)
    return {
        "path": str(path),
        "status": "materialized",
        "source": str(target),
        "size_bytes": path.stat().st_size,
    }


def chmod_for_container_write(scan_root: Path) -> dict[str, Any]:
    changed_dirs = 0
    changed_files = 0
    if not scan_root.exists():
        return {"changed_dirs": 0, "changed_files": 0, "status": "missing_scan_root"}

    for path in [scan_root, *scan_root.rglob("*")]:
        try:
            current_mode = stat.S_IMODE(path.stat().st_mode)
            desired_mode = 0o777 if path.is_dir() else 0o666
            if current_mode != desired_mode:
                path.chmod(desired_mode)
                if path.is_dir():
                    changed_dirs += 1
                else:
                    changed_files += 1
        except FileNotFoundError:
            continue
    return {
        "changed_dirs": changed_dirs,
        "changed_files": changed_files,
        "status": "permission_repaired",
    }


def scan_rows() -> list[dict[str, Any]]:
    expected_rows = read_jsonl(M33_DIR / "expected_outputs.jsonl")
    scan_ids = [str(row["scan_id"]) for row in expected_rows if row.get("scan_id")]
    rows: list[dict[str, Any]] = []
    for scan_id in scan_ids:
        scan_root = STAGED_ROOT / scan_id
        depth_files = sorted((scan_root / "depth").glob("*.png"))
        pose_files = sorted((scan_root / "pose").glob("*.txt"))
        color_files = sorted((scan_root / "color").glob("*.jpg"))

        materialized = []
        for path in depth_files + pose_files:
            result = copy_symlink_target(path)
            if result["status"] != "already_regular":
                materialized.append(result)
        permission_result = chmod_for_container_write(scan_root)

        depth_after = sorted((scan_root / "depth").glob("*.png"))
        pose_after = sorted((scan_root / "pose").glob("*.txt"))
        color_after = sorted((scan_root / "color").glob("*.jpg"))
        depth_regular = sum(1 for path in depth_after if path.exists() and not path.is_symlink())
        pose_regular = sum(1 for path in pose_after if path.exists() and not path.is_symlink())
        writable_dirs = sum(1 for path in [scan_root, *scan_root.rglob("*")] if path.is_dir() and path.stat().st_mode & stat.S_IWOTH)
        total_dirs = sum(1 for path in [scan_root, *scan_root.rglob("*")] if path.is_dir())
        ready = (
            scan_root.exists()
            and len(color_after) > 0
            and len(color_after) == len(depth_after) == len(pose_after)
            and depth_regular == len(depth_after)
            and pose_regular == len(pose_after)
            and writable_dirs == total_dirs
        )
        rows.append(
            {
                "scan_id": scan_id,
                "scan_root": str(scan_root),
                "color_count": len(color_after),
                "depth_count": len(depth_after),
                "pose_count": len(pose_after),
                "depth_regular_count": depth_regular,
                "pose_regular_count": pose_regular,
                "materialized_file_count": len(materialized),
                "permission_result": permission_result,
                "container_writable_dir_count": writable_dirs,
                "total_dir_count": total_dirs,
                "sample_materialized": materialized[:5],
                "container_visible_payload_ready": ready,
            }
        )
    return rows


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M34 ConceptGraphs Pending Scan Staging Repair",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Pending scans: {coverage['scan_count']}.",
        f"- Ready scans after repair: {coverage['ready_scan_count']} / {coverage['scan_count']}.",
        f"- Materialized files: {coverage['materialized_file_count']}.",
        f"- Permission-changed dirs/files: {coverage['permission_changed_dir_count']} / {coverage['permission_changed_file_count']}.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}`: ready {ready}, color/depth/pose {color}/{depth}/{pose}, "
            "regular depth/pose {depth_regular}/{pose_regular}, writable dirs {writable_dirs}/{total_dirs}, materialized {materialized}".format(
                scan_id=row["scan_id"],
                ready=str(row["container_visible_payload_ready"]).lower(),
                color=row["color_count"],
                depth=row["depth_count"],
                pose=row["pose_count"],
                depth_regular=row["depth_regular_count"],
                pose_regular=row["pose_regular_count"],
                writable_dirs=row["container_writable_dir_count"],
                total_dirs=row["total_dir_count"],
                materialized=row["materialized_file_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This repair only fixes Docker container visibility for staged `ConceptGraphs` inputs.",
            "- It also makes pending scan staging folders writable to the container runtime user.",
            "- It does not change `ConceptGraphs` outputs, query metrics, or final baseline claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = scan_rows()
    ready_count = sum(1 for row in rows if row["container_visible_payload_ready"])
    materialized_count = sum(row["materialized_file_count"] for row in rows)
    permission_changed_dir_count = sum(row["permission_result"]["changed_dirs"] for row in rows)
    permission_changed_file_count = sum(row["permission_result"]["changed_files"] for row in rows)
    status = (
        "e005_m34_conceptgraphs_pending_scan_staging_repair_ready"
        if rows and ready_count == len(rows)
        else "e005_m34_conceptgraphs_pending_scan_staging_repair_incomplete"
    )
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scan_count": len(rows),
        "ready_scan_count": ready_count,
        "materialized_file_count": materialized_count,
        "permission_changed_dir_count": permission_changed_dir_count,
        "permission_changed_file_count": permission_changed_file_count,
        "staged_root": str(STAGED_ROOT),
        "previous_failure": "M33 first failed because staged depth/pose files were host-absolute symlinks; relaunch then failed because pending scan roots were not writable to the Docker runtime user.",
        "next_recommended_unit": "E005-M33 pending scan runtime relaunch",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "scan_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
