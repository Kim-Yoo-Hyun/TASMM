#!/usr/bin/env python3
"""Verify E008-M15 non-oracle observation expansion frame staging."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
VERSION = "e008_m15_non_oracle_observation_expansion_frame_staging_verifier_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
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


def file_stats(path: Path) -> dict[str, Any]:
    return {
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def pgm_depth_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "height": 0, "nonzero_count": 0, "size_bytes": 0, "width": 0}
    data = path.read_bytes()
    try:
        if not data.startswith(b"P5"):
            raise ValueError("not binary PGM")
        offset = 2
        tokens: list[bytes] = []
        while len(tokens) < 3:
            while offset < len(data) and chr(data[offset]).isspace():
                offset += 1
            if offset < len(data) and data[offset:offset + 1] == b"#":
                while offset < len(data) and data[offset:offset + 1] not in {b"\n", b"\r"}:
                    offset += 1
                continue
            start = offset
            while offset < len(data) and not chr(data[offset]).isspace():
                offset += 1
            tokens.append(data[start:offset])
        while offset < len(data) and chr(data[offset]).isspace():
            offset += 1
        width = int(tokens[0])
        height = int(tokens[1])
        max_value = int(tokens[2])
        pixel_bytes = data[offset:]
        if max_value > 255:
            nonzero = 0
            for idx in range(0, len(pixel_bytes) - 1, 2):
                if pixel_bytes[idx] or pixel_bytes[idx + 1]:
                    nonzero += 1
        else:
            nonzero = sum(1 for value in pixel_bytes if value)
        return {
            "exists": True,
            "height": height,
            "max_value": max_value,
            "nonzero_count": nonzero,
            "size_bytes": len(data),
            "width": width,
        }
    except Exception as exc:
        return {
            "error": repr(exc),
            "exists": True,
            "height": 0,
            "nonzero_count": 0,
            "size_bytes": len(data),
            "width": 0,
        }


def pose_valid(path: Path) -> bool:
    if not path.exists():
        return False
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append([float(item) for item in line.split()])
            except ValueError:
                return False
    return len(rows) == 4 and all(len(row) == 4 for row in rows) and all(
        math.isfinite(value) for row in rows for value in row
    )


def info_ready(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    required = [
        "m_colorWidth",
        "m_colorHeight",
        "m_depthWidth",
        "m_depthHeight",
        "m_depthShift",
        "m_calibrationDepthIntrinsic",
        "m_frames.size",
    ]
    return all(item in text for item in required)


def build_frame_rows(render_plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    issues = []
    for plan in render_plan_rows:
        color = Path(str(plan["expected_color"]))
        depth = Path(str(plan["expected_depth"]))
        pose = Path(str(plan["expected_pose"]))
        sequence = color.parent
        info = sequence / "_info.txt"
        color_stats = file_stats(color)
        depth_stats = pgm_depth_stats(depth)
        row = {
            "adapter_episode_id": plan["adapter_episode_id"],
            "color_exists": color.exists(),
            "color_nonblank": bool(int(color_stats.get("size_bytes", 0) or 0) > 1024),
            "color_path": str(color),
            "color_size_bytes": color_stats.get("size_bytes"),
            "depth_exists": depth.exists(),
            "depth_nonzero_count": depth_stats.get("nonzero_count", 0),
            "depth_path": str(depth),
            "depth_positive": bool(int(depth_stats.get("nonzero_count", 0) or 0) > 0),
            "frame_id": plan["frame_id"],
            "info_exists": info.exists(),
            "info_ready": info_ready(info),
            "observation_pose_id": plan.get("observation_pose_id"),
            "pose_exists": pose.exists(),
            "pose_path": str(pose),
            "pose_role": plan.get("pose_role"),
            "pose_valid": pose_valid(pose),
            "requires_navmesh_snap_validation": bool(plan.get("requires_navmesh_snap_validation")),
            "scan_id": plan["scan_id"],
            "sequence_dir": str(sequence),
            "uses_objectnav_eval_goal": bool(plan.get("uses_objectnav_eval_goal")),
            "uses_objectnav_eval_viewpoint": bool(plan.get("uses_objectnav_eval_viewpoint")),
        }
        row["frame_ready"] = all(
            [
                row["color_exists"],
                row["color_nonblank"],
                row["depth_exists"],
                row["depth_positive"],
                row["pose_exists"],
                row["pose_valid"],
                row["info_ready"],
            ]
        )
        rows.append(row)
        if not row["frame_ready"]:
            issues.append(
                {
                    k: row[k]
                    for k in [
                        "scan_id",
                        "frame_id",
                        "observation_pose_id",
                        "color_exists",
                        "color_nonblank",
                        "depth_exists",
                        "depth_positive",
                        "pose_valid",
                        "info_ready",
                    ]
                }
            )
    return rows, issues


def build_scan_rows(frame_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in frame_rows:
        grouped.setdefault(str(row["scan_id"]), []).append(row)
    out = []
    for scan_id, rows in sorted(grouped.items()):
        sequence = Path(str(rows[0]["sequence_dir"]))
        out.append(
            {
                "scan_id": scan_id,
                "sequence_dir": str(sequence),
                "color_frames": sum(1 for row in rows if row["color_exists"]),
                "depth_frames": sum(1 for row in rows if row["depth_exists"]),
                "pose_frames": sum(1 for row in rows if row["pose_exists"]),
                "ready_frames": sum(1 for row in rows if row["frame_ready"]),
                "expected_frames": len(rows),
                "info_ready": info_ready(sequence / "_info.txt"),
                "scan_ready": len(rows) > 0 and all(row["frame_ready"] for row in rows),
            }
        )
    return out


def mean(values: list[Any]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def build_report(coverage: dict[str, Any], scan_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E008-M15 Non-Oracle Observation Expansion Frame Staging Verification",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Expected frames: {coverage['expected_frame_rows']}.",
        f"- Ready frames: {coverage['ready_frame_rows']}.",
        f"- Ready scans: {coverage['ready_scan_rows']} / {coverage['scan_rows']}.",
        f"- Snap validation rows: {coverage['snap_validation_rows']}.",
        f"- Snap-ready rows: {coverage['snap_ready_rows']}.",
        f"- Large snap warning rows: {coverage['large_snap_warning_rows']}.",
        f"- Detector input files ready: {coverage['detector_input_files_ready']}.",
        f"- `ObjectNav` eval fields used for policy: {str(coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']).lower()}.",
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.",
        f"- Final real RGB-D/open-vocabulary robustness ready: {str(coverage['final_real_rgbd_open_vocab_robustness_ready']).lower()}.",
        "",
        "## Scan Rows",
        "",
        "| scan_id | ready_frames | expected_frames | info_ready |",
        "| --- | --- | --- | --- |",
    ]
    for row in scan_rows:
        lines.append(
            f"| {row['scan_id']} | {row['ready_frames']} | {row['expected_frames']} | {row['info_ready']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E008-M15 verifies expanded frame staging and navmesh snap readiness only.",
            "- It does not run detector inference, H001 navigation execution, or `SR` / `SPL` evaluation.",
            "- Detector rerun and candidate-to-goal evaluation remain required before any navigation evidence claim.",
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    render_plan_rows = read_jsonl(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl")
    manifest_rows = read_jsonl(DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    snap_rows = read_jsonl(DATA_OUT_DIR / "snap_validation_rows.jsonl")
    frame_rows, issue_rows = build_frame_rows(render_plan_rows)
    scan_rows = build_scan_rows(frame_rows)
    detector_inputs = [
        DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl",
        DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl",
        DATA_OUT_DIR / "detector_inputs" / "prompt_set.json",
        DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json",
    ]
    ready_frames = sum(1 for row in frame_rows if row["frame_ready"])
    ready_scans = sum(1 for row in scan_rows if row["scan_ready"])
    detector_input_files_ready = all(path.exists() and path.stat().st_size > 0 for path in detector_inputs)
    category_counts = Counter(str(row.get("object_category")) for row in manifest_rows)
    snap_ready_rows = sum(1 for row in snap_rows if row.get("snap_validation_ready"))
    snap_required_rows = sum(1 for row in snap_rows if row.get("requires_navmesh_snap_validation"))
    snap_large_rows = sum(1 for row in snap_rows if row.get("snap_warning_large_move"))
    uses_eval_policy = any(
        bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint"))
        for row in render_plan_rows
    )
    ready = (
        bool(render_plan_rows)
        and ready_frames == len(render_plan_rows)
        and ready_scans == len(scan_rows)
        and detector_input_files_ready
        and len(snap_rows) == len(render_plan_rows)
        and snap_ready_rows == len(snap_rows)
        and not uses_eval_policy
    )
    status = (
        "e008_m15_non_oracle_observation_expansion_frame_staging_verified"
        if ready and snap_large_rows == 0
        else "e008_m15_non_oracle_observation_expansion_frame_staging_verified_with_snap_warnings"
        if ready
        else "e008_m15_non_oracle_observation_expansion_frame_staging_verification_failed"
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "expected_frame_rows": len(render_plan_rows),
        "ready_frame_rows": ready_frames,
        "scan_rows": len(scan_rows),
        "ready_scan_rows": ready_scans,
        "detector_input_files_ready": detector_input_files_ready,
        "detector_manifest_rows": len(manifest_rows),
        "object_category_counts": dict(sorted(category_counts.items())),
        "frame_issue_rows": len(issue_rows),
        "snap_validation_rows": len(snap_rows),
        "snap_required_rows": snap_required_rows,
        "snap_ready_rows": snap_ready_rows,
        "large_snap_warning_rows": snap_large_rows,
        "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in snap_rows]),
        "max_snap_distance_m": max(
            [float(row["snap_distance_m"]) for row in snap_rows if row.get("snap_distance_m") is not None],
            default=None,
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E008-M16 non-oracle observation expansion detector candidate smoke"
        if ready
        else "repair E008-M15 frame staging",
    }

    write_jsonl(ARTIFACT_DIR / "verification_frame_rows.jsonl", frame_rows)
    write_jsonl(ARTIFACT_DIR / "verification_scan_rows.jsonl", scan_rows)
    write_jsonl(ARTIFACT_DIR / "verification_issue_rows.jsonl", issue_rows)
    write_json(ARTIFACT_DIR / "verification_coverage.json", coverage)
    write_text(ARTIFACT_DIR / "verification_report.md", build_report(coverage, scan_rows))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"].startswith("e008_m15_non_oracle_observation_expansion_frame_staging_verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())
