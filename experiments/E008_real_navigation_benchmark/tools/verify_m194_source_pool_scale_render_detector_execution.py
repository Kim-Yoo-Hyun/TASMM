#!/usr/bin/env python3
"""Verify E008-M194 source-pool scale render/detector execution."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M179_TOOL = EXP_ROOT / "tools" / "verify_m179_bounded_render_detector_execution.py"
M193_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M194_source_pool_scale_render_detector_execution_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
)
DETECTOR_DIR = ARTIFACT_DIR / "detector"
RENDER_SESSION = "e008_m194_source_pool_scale_render"
DETECTOR_SESSION = "e008_m194_source_pool_scale_detector"
VERSION = "e008_m194_source_pool_scale_render_detector_verifier_v0"
NEXT_UNIT = "E008-M195 source-pool scale candidate navmesh/source-readiness validation"


def load_m179() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m179_verifier_reused", M179_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M179_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.M178_ARTIFACT_DIR = M193_ARTIFACT_DIR
    module.ARTIFACT_DIR = ARTIFACT_DIR
    module.DATA_OUT_DIR = DATA_OUT_DIR
    module.DETECTOR_DIR = DETECTOR_DIR
    module.RENDER_SESSION = RENDER_SESSION
    module.DETECTOR_SESSION = DETECTOR_SESSION
    module.VERSION = VERSION
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def patch_status(value: Any) -> Any:
    if isinstance(value, str):
        return (
            value.replace("E008-M180 candidate navmesh/source-readiness validation", NEXT_UNIT)
            .replace("E008-M179 detector launch", "E008-M194 detector launch")
            .replace("E008-M179", "E008-M194")
            .replace("e008_m179", "e008_m194")
            .replace("m179", "m194")
        )
    if isinstance(value, dict):
        return {key: patch_status(item) for key, item in value.items()}
    if isinstance(value, list):
        return [patch_status(item) for item in value]
    return value


def build_summary_coverage(render: dict[str, Any], detector: dict[str, Any]) -> dict[str, Any]:
    ready = detector.get("status") == "e008_m194_detector_candidate_source_ready"
    running = render.get("status") == "e008_m194_render_running" or detector.get("status") == (
        "e008_m194_detector_candidate_source_running"
    )
    status = (
        "e008_m194_source_pool_scale_render_detector_execution_ready"
        if ready
        else "e008_m194_source_pool_scale_render_detector_execution_running"
        if running
        else "e008_m194_source_pool_scale_render_detector_execution_needs_next_step"
    )
    return {
        "version": VERSION,
        "status": status,
        "render_status": render.get("status"),
        "detector_status": detector.get("status"),
        "render_ready_frame_rows": render.get("ready_frame_rows", 0),
        "render_plan_rows": render.get("render_plan_rows", 0),
        "detector_manifest_ready_rows": render.get("detector_manifest_ready_rows", 0),
        "detector_manifest_invalid_rows": render.get("detector_manifest_invalid_rows", 0),
        "prediction_rows": detector.get("prediction_rows", 0),
        "coordinate_candidate_rows": detector.get("coordinate_candidate_rows", 0),
        "pre_cap_candidate_rows": detector.get("pre_cap_candidate_rows", 0),
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": NEXT_UNIT
        if ready
        else detector.get("selected_next_unit") or render.get("selected_next_unit"),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M194 Source-Pool Scale Render/Detector Verification",
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
            "- M194 verifies source-pool scale render/detector execution only.",
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
    m179 = load_m179()
    render = patch_status(m179.verify_render())
    raw_detector = m179.verify_detector() if render.get("depth_filtered_detector_manifest_ready") else {}
    detector = patch_status(raw_detector)
    write_json(ARTIFACT_DIR / "render_verification_coverage.json", render)
    if detector:
        write_json(ARTIFACT_DIR / "detector_verification_coverage.json", detector)
    coverage = build_summary_coverage(render, detector)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_render_ready and not render.get("depth_filtered_detector_manifest_ready"):
        return 2
    if args.require_ready and coverage.get("status") != "e008_m194_source_pool_scale_render_detector_execution_ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
