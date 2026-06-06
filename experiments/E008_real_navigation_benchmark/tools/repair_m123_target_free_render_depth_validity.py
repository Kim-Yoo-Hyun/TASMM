#!/usr/bin/env python3
"""Repair E008-M123 detector manifest by filtering zero-depth rendered frames."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)
DETECTOR_INPUT_DIR = DATA_OUT_DIR / "detector_inputs"
MANIFEST_PATH = DETECTOR_INPUT_DIR / "real_proposal_query_manifest.jsonl"
BACKUP_MANIFEST_PATH = DETECTOR_INPUT_DIR / "real_proposal_query_manifest.m122_pre_m123_depth_repair.jsonl"
VERSION = "e008_m123_target_free_render_depth_validity_repair_v0"


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M123 Depth-Validity Repair",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Original detector manifest rows: {coverage['original_manifest_rows']}.",
            f"- Repaired detector manifest rows: {coverage['repaired_manifest_rows']}.",
            f"- Original sampled frames: {coverage['original_sampled_frame_count']}.",
            f"- Repaired sampled frames: {coverage['repaired_sampled_frame_count']}.",
            f"- Dropped invalid depth frames: {coverage['dropped_invalid_depth_frame_count']}.",
            f"- Detector sampled invalid frames after repair: {coverage['detector_sampled_invalid_frame_count_after_repair']}.",
            f"- Backup manifest: `{coverage['backup_manifest_path']}`.",
            f"- Patched manifest: `{coverage['patched_manifest_path']}`.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- This repair makes the detector manifest use only frames that passed M123 color/depth/pose validation.",
            "- It does not claim all 320 target-free render frames are valid.",
            "- It does not run detector inference, recover source-gap rows, execute trajectories, or support final navigation claims.",
            "",
        ]
    )


def main() -> int:
    verification_coverage = read_json(ARTIFACT_DIR / "coverage.json") or read_json(ARTIFACT_DIR / "verification_coverage.json")
    frame_rows = read_jsonl(ARTIFACT_DIR / "verification_frame_rows.jsonl")
    manifest_rows = read_jsonl(MANIFEST_PATH)

    if not frame_rows:
        raise RuntimeError(f"missing verification frame rows: {ARTIFACT_DIR / 'verification_frame_rows.jsonl'}")
    if not manifest_rows:
        raise RuntimeError(f"missing detector manifest rows: {MANIFEST_PATH}")

    frame_ready_by_index: dict[int, bool] = {}
    frame_info_by_index: dict[int, dict[str, Any]] = {}
    for row in frame_rows:
        frame_id = str(row.get("frame_id"))
        try:
            frame_index = int(frame_id.replace("frame-", ""))
        except ValueError as exc:
            raise RuntimeError(f"invalid frame_id in verification rows: {frame_id}") from exc
        frame_ready_by_index[frame_index] = bool(row.get("frame_ready"))
        frame_info_by_index[frame_index] = row

    if not BACKUP_MANIFEST_PATH.exists():
        write_jsonl(BACKUP_MANIFEST_PATH, manifest_rows)

    repaired_manifest_rows: list[dict[str, Any]] = []
    dropped_rows: list[dict[str, Any]] = []
    per_manifest_rows: list[dict[str, Any]] = []
    invalid_after_repair = 0

    for row in manifest_rows:
        original_indices = [int(index) for index in row.get("sampled_frame_indices", [])]
        valid_indices: list[int] = []
        invalid_indices: list[int] = []
        for frame_index in original_indices:
            if frame_ready_by_index.get(frame_index, False):
                valid_indices.append(frame_index)
            else:
                invalid_indices.append(frame_index)
                info = frame_info_by_index.get(frame_index, {})
                dropped_rows.append(
                    {
                        "frame_id": f"frame-{frame_index:06d}",
                        "frame_index": frame_index,
                        "manifest_route_id": row.get("route_id"),
                        "observation_pose_id": info.get("observation_pose_id"),
                        "reason": "m123_frame_not_ready_for_detector_depth_positive_filter",
                        "scan_id": row.get("scan_id"),
                        "depth_positive": info.get("depth_positive"),
                        "color_nonblank": info.get("color_nonblank"),
                        "pose_valid": info.get("pose_valid"),
                        "info_ready": info.get("info_ready"),
                    }
                )

        repaired = dict(row)
        repaired["source_version"] = repaired.get("version")
        repaired["version"] = VERSION
        repaired["m123_depth_validity_repaired"] = True
        repaired["frame_sampling_strategy"] = (
            f"{row.get('frame_sampling_strategy', 'unknown')}_depth_positive_subset"
        )
        repaired["pre_repair_sampled_frame_count"] = len(original_indices)
        repaired["pre_repair_sampled_frame_indices"] = original_indices
        repaired["sampled_frame_indices"] = valid_indices
        repaired["sampled_frame_count"] = len(valid_indices)
        repaired["max_frames"] = min(int(row.get("max_frames") or len(valid_indices)), len(valid_indices))
        repaired["dropped_invalid_depth_frame_indices"] = invalid_indices
        repaired["dropped_invalid_depth_frame_count"] = len(invalid_indices)
        repaired["claim_boundary"] = (
            "M123 depth-validity repair filters zero-depth rendered frames from detector input; "
            "this does not claim all target-free render frames are valid."
        )
        repaired_manifest_rows.append(repaired)
        invalid_after_repair += sum(1 for index in valid_indices if not frame_ready_by_index.get(index, False))
        per_manifest_rows.append(
            {
                "route_id": row.get("route_id"),
                "scan_id": row.get("scan_id"),
                "original_sampled_frame_count": len(original_indices),
                "repaired_sampled_frame_count": len(valid_indices),
                "dropped_invalid_depth_frame_count": len(invalid_indices),
                "detector_sampled_invalid_frame_count_after_repair": sum(
                    1 for index in valid_indices if not frame_ready_by_index.get(index, False)
                ),
            }
        )

    original_total = sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows)
    repaired_total = sum(len(row.get("sampled_frame_indices", [])) for row in repaired_manifest_rows)
    dropped_total = len(dropped_rows)
    status = (
        "e008_m123_target_free_render_depth_validity_repair_ready"
        if repaired_manifest_rows and repaired_total > 0 and invalid_after_repair == 0 and dropped_total > 0
        else "e008_m123_target_free_render_depth_validity_repair_failed"
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "data_bearing_output_root": str(DATA_OUT_DIR),
        "verification_status_before_repair": verification_coverage.get("status"),
        "verification_ready_frame_rows_before_repair": verification_coverage.get("ready_frame_rows"),
        "verification_expected_frame_rows": verification_coverage.get("expected_frame_rows"),
        "original_manifest_rows": len(manifest_rows),
        "repaired_manifest_rows": len(repaired_manifest_rows),
        "original_sampled_frame_count": original_total,
        "repaired_sampled_frame_count": repaired_total,
        "dropped_invalid_depth_frame_count": dropped_total,
        "detector_sampled_invalid_frame_count_after_repair": invalid_after_repair,
        "patched_manifest_path": str(MANIFEST_PATH),
        "backup_manifest_path": str(BACKUP_MANIFEST_PATH),
        "source_gap_recovery_evaluated": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E008-M123 completion verification after depth filtering"
        if status.endswith("_ready")
        else "repair E008-M123 detector manifest filtering",
    }

    write_jsonl(MANIFEST_PATH, repaired_manifest_rows)
    write_jsonl(ARTIFACT_DIR / "depth_repair_manifest_rows.jsonl", repaired_manifest_rows)
    write_jsonl(ARTIFACT_DIR / "depth_repair_dropped_frame_rows.jsonl", dropped_rows)
    write_jsonl(ARTIFACT_DIR / "depth_repair_per_manifest_rows.jsonl", per_manifest_rows)
    write_json(ARTIFACT_DIR / "depth_repair_coverage.json", coverage)
    write_text(ARTIFACT_DIR / "depth_repair_report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status.endswith("_ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
