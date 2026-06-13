#!/usr/bin/env python3
"""Verify E008-M179 bounded render/detector execution."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
GENERIC_DETECTOR_VERIFIER = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
M178_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M179_bounded_render_detector_execution_verification_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
)
DETECTOR_DIR = ARTIFACT_DIR / "detector"
RENDER_SESSION = "e008_m179_source_pool_render"
DETECTOR_SESSION = "e008_m179_source_pool_detector"
VERSION = "e008_m179_bounded_render_detector_verifier_v0"


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


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def frame_ready_rows(render_plan_rows: list[dict[str, Any]], rendered_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rendered_by_key = {
        (str(row.get("scan_id")), str(row.get("frame_id"))): row for row in rendered_rows
    }
    out: list[dict[str, Any]] = []
    for plan in render_plan_rows:
        key = (str(plan.get("scan_id")), str(plan.get("frame_id")))
        rendered = rendered_by_key.get(key, {})
        color = Path(str(plan.get("expected_color")))
        depth = Path(str(plan.get("expected_depth")))
        pose = Path(str(plan.get("expected_pose")))
        positive_depth = int(rendered.get("depth_positive_pixels", 0) or 0)
        ready = bool(
            rendered
            and color.exists()
            and color.stat().st_size > 0
            and depth.exists()
            and depth.stat().st_size > 0
            and pose.exists()
            and pose.stat().st_size > 0
            and positive_depth > 0
        )
        out.append(
            {
                "version": VERSION,
                "row_type": "render_frame_verification",
                "scan_id": key[0],
                "frame_id": key[1],
                "frame_index": plan.get("frame_index"),
                "adapter_episode_id": plan.get("adapter_episode_id"),
                "object_category": plan.get("object_category"),
                "render_ready": ready,
                "rendered_row_present": bool(rendered),
                "color_ready": color.exists() and color.stat().st_size > 0 if color.exists() else False,
                "depth_ready": depth.exists() and depth.stat().st_size > 0 if depth.exists() else False,
                "pose_ready": pose.exists() and pose.stat().st_size > 0 if pose.exists() else False,
                "depth_positive_pixels": positive_depth,
                "expected_color": str(color),
                "expected_depth": str(depth),
                "expected_pose": str(pose),
            }
        )
    return out


def repair_detector_manifest(frame_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_path = DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl"
    source_manifest_path = M178_ARTIFACT_DIR / "source_pool_detector_manifest_rows.jsonl"
    manifest_rows = read_jsonl(source_manifest_path)
    if not manifest_rows:
        manifest_rows = read_jsonl(manifest_path)
    ready_by_scan: dict[str, set[int]] = {}
    for row in frame_rows:
        if row.get("render_ready"):
            ready_by_scan.setdefault(str(row.get("scan_id")), set()).add(int(row.get("frame_index") or 0))
    repaired: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        scan_id = str(manifest.get("scan_id"))
        original_indices = [int(index) for index in manifest.get("sampled_frame_indices", [])]
        ready_indices = sorted(index for index in original_indices if index in ready_by_scan.get(scan_id, set()))
        next_row = dict(manifest)
        next_row["m179_depth_validity_repaired"] = True
        next_row["m179_original_sampled_frame_count"] = len(original_indices)
        next_row["m179_ready_sampled_frame_count"] = len(ready_indices)
        next_row["sampled_frame_indices"] = ready_indices
        next_row["sampled_frame_count"] = len(ready_indices)
        next_row["max_frames"] = len(ready_indices)
        repaired.append(next_row)
        repair_rows.append(
            {
                "version": VERSION,
                "row_type": "detector_manifest_depth_repair",
                "scan_id": scan_id,
                "adapter_episode_id": manifest.get("adapter_episode_id"),
                "object_category": manifest.get("object_category"),
                "original_sampled_frame_count": len(original_indices),
                "ready_sampled_frame_count": len(ready_indices),
                "dropped_frame_count": len(original_indices) - len(ready_indices),
                "manifest_ready_for_detector": bool(ready_indices),
            }
        )
        if not ready_indices:
            invalid_rows.append(
                {
                    "scan_id": scan_id,
                    "adapter_episode_id": manifest.get("adapter_episode_id"),
                    "reason": "no_depth_positive_render_frames",
                }
            )
    if manifest_rows and any(row.get("manifest_ready_for_detector") for row in repair_rows):
        write_jsonl(manifest_path, repaired)
    return {
        "manifest_rows": manifest_rows,
        "repaired_manifest_rows": repaired,
        "repair_rows": repair_rows,
        "invalid_rows": invalid_rows,
    }


def verify_render() -> dict[str, Any]:
    render_plan_rows = read_jsonl(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl")
    rendered_rows = read_jsonl(DATA_OUT_DIR / "rendered_frame_rows.jsonl")
    render_summary = read_json(DATA_OUT_DIR / "render_summary.json")
    frame_rows = frame_ready_rows(render_plan_rows, rendered_rows)
    repair = repair_detector_manifest(frame_rows)
    ready_rows = [row for row in frame_rows if row.get("render_ready")]
    all_frames_ready = bool(render_plan_rows and len(ready_rows) == len(render_plan_rows))
    depth_filtered_ready = bool(repair["repair_rows"] and not repair["invalid_rows"])
    status = (
        "e008_m179_render_ready"
        if all_frames_ready
        else "e008_m179_render_ready_with_depth_filtered_frames"
        if depth_filtered_ready
        else "e008_m179_render_running"
        if tmux_running(RENDER_SESSION)
        else "e008_m179_render_failed_or_needs_repair"
    )
    coverage = {
        "version": VERSION,
        "status": status,
        "tmux_session": RENDER_SESSION,
        "tmux_running": tmux_running(RENDER_SESSION),
        "render_plan_rows": len(render_plan_rows),
        "rendered_frame_rows": len(rendered_rows),
        "ready_frame_rows": len(ready_rows),
        "render_summary_status": render_summary.get("ok"),
        "render_summary_frame_rows": render_summary.get("frame_rows"),
        "detector_manifest_rows": len(repair["manifest_rows"]),
        "detector_manifest_repaired_rows": len(repair["repaired_manifest_rows"]),
        "detector_manifest_ready_rows": sum(1 for row in repair["repair_rows"] if row.get("manifest_ready_for_detector")),
        "detector_manifest_invalid_rows": len(repair["invalid_rows"]),
        "depth_filtered_detector_manifest_ready": depth_filtered_ready,
        "selected_next_unit": "E008-M179 detector launch" if depth_filtered_ready else "repair E008-M179 render output",
    }
    write_json(ARTIFACT_DIR / "render_verification_coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "render_verification_frame_rows.jsonl", frame_rows)
    write_jsonl(ARTIFACT_DIR / "detector_manifest_repair_rows.jsonl", repair["repair_rows"])
    write_jsonl(ARTIFACT_DIR / "detector_manifest_invalid_rows.jsonl", repair["invalid_rows"])
    return coverage


def verify_detector() -> dict[str, Any]:
    generic_command = [
        "python",
        str(GENERIC_DETECTOR_VERIFIER),
        "--m15-artifact-dir",
        str(ARTIFACT_DIR),
        "--m15-data-dir",
        str(DATA_OUT_DIR),
        "--m16-dir",
        str(DETECTOR_DIR),
        "--tmux-session",
        DETECTOR_SESSION,
    ]
    result = subprocess.run(generic_command, check=False, text=True, capture_output=True)
    generic = read_json(DETECTOR_DIR / "e008_m16_verification_coverage.json")
    manifest_rows = read_jsonl(DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    status = str(generic.get("status", ""))
    tmux_is_running = tmux_running(DETECTOR_SESSION)
    if status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready":
        mapped_status = "e008_m179_detector_candidate_source_ready"
    elif tmux_is_running or status.endswith("_running"):
        mapped_status = "e008_m179_detector_candidate_source_running"
    elif not generic:
        mapped_status = "e008_m179_detector_candidate_source_waiting_for_output"
    else:
        mapped_status = "e008_m179_detector_candidate_source_failed_or_needs_review"
    coverage = {
        "version": VERSION,
        "status": mapped_status,
        "generic_detector_status": status,
        "generic_verifier_returncode": result.returncode,
        "generic_verifier_stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "generic_verifier_stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
        "tmux_session": DETECTOR_SESSION,
        "tmux_running": tmux_is_running,
        "detector_dir": str(DETECTOR_DIR),
        "manifest_rows": len(manifest_rows),
        "detector_sampled_frame_rows": sum(len(row.get("sampled_frame_indices", [])) for row in manifest_rows),
        "prediction_rows": int(generic.get("prediction_rows", 0) or 0),
        "coordinate_candidate_rows": int(generic.get("coordinate_candidate_rows", 0) or 0),
        "pre_cap_candidate_rows": int(generic.get("pre_cap_candidate_rows", 0) or 0),
        "validator_error_rows": int(generic.get("validator_error_rows", 0) or 0),
        "validator_warning_rows": int(generic.get("validator_warning_rows", 0) or 0),
        "selected_next_unit": "E008-M180 candidate navmesh/source-readiness validation"
        if mapped_status == "e008_m179_detector_candidate_source_ready"
        else "wait for or repair E008-M179 detector output",
    }
    write_json(ARTIFACT_DIR / "detector_verification_coverage.json", coverage)
    return coverage


def build_summary_coverage(render: dict[str, Any], detector: dict[str, Any]) -> dict[str, Any]:
    ready = detector.get("status") == "e008_m179_detector_candidate_source_ready"
    status = (
        "e008_m179_bounded_render_detector_execution_ready"
        if ready
        else "e008_m179_bounded_render_detector_execution_running"
        if render.get("status") == "e008_m179_render_running"
        or detector.get("status") == "e008_m179_detector_candidate_source_running"
        else "e008_m179_bounded_render_detector_execution_needs_next_step"
    )
    return {
        "version": VERSION,
        "status": status,
        "render_status": render.get("status"),
        "detector_status": detector.get("status"),
        "render_ready_frame_rows": render.get("ready_frame_rows", 0),
        "render_plan_rows": render.get("render_plan_rows", 0),
        "detector_manifest_ready_rows": render.get("detector_manifest_ready_rows", 0),
        "prediction_rows": detector.get("prediction_rows", 0),
        "coordinate_candidate_rows": detector.get("coordinate_candidate_rows", 0),
        "pre_cap_candidate_rows": detector.get("pre_cap_candidate_rows", 0),
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": "E008-M180 candidate navmesh/source-readiness validation"
        if ready
        else detector.get("selected_next_unit") or render.get("selected_next_unit"),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M179 Bounded Render/Detector Verification",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Render status: `{coverage['render_status']}`.",
            f"- Detector status: `{coverage['detector_status']}`.",
            f"- Ready render frames: {coverage['render_ready_frame_rows']} / {coverage['render_plan_rows']}.",
            f"- Detector manifest ready rows: {coverage['detector_manifest_ready_rows']}.",
            f"- Prediction rows: {coverage['prediction_rows']}.",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}.",
            f"- Pre-cap candidate rows: {coverage['pre_cap_candidate_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M179 verifies bounded render/detector execution only.",
            "- It does not validate candidate reachability, evaluate ObjectNav goals, execute trajectories, or support real navigation `SR` / `SPL`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-render-ready", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    render = verify_render()
    detector = verify_detector() if render.get("depth_filtered_detector_manifest_ready") else {}
    coverage = build_summary_coverage(render, detector)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_render_ready and not render.get("depth_filtered_detector_manifest_ready"):
        return 2
    if args.require_ready and coverage.get("status") != "e008_m179_bounded_render_detector_execution_ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
