#!/usr/bin/env python3
"""Validate M194 source-pool scale detector candidates against HM3D navmeshes."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M125_TOOL = EXP_ROOT / "tools" / "run_m125_target_free_detector_candidate_navmesh_validation.py"

VERSION = "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
)

M193_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
M193_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
)
M194_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M194_source_pool_scale_render_detector_execution_v0"

READY_STATUSES = {
    "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_ready",
    "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_ready_with_source_warnings",
}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def copy_required(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def build_compat_inputs() -> tuple[Path, Path]:
    compat_root = ARTIFACT_DIR / "_compat_inputs"
    compat_m124 = compat_root / "m124_detector"
    compat_m122 = compat_root / "m122_launcher"

    proposal_src = M194_ARTIFACT_DIR / "detector" / "container_output" / "real_proposals.jsonl"
    copy_required(proposal_src, compat_m124 / "container_output" / "real_proposals.jsonl")

    m194_cov = read_json(M194_ARTIFACT_DIR / "coverage.json")
    detector_cov = read_json(M194_ARTIFACT_DIR / "detector" / "e008_m16_verification_coverage.json")
    write_json(
        compat_m124 / "e008_m124_verification_coverage.json",
        {
            **detector_cov,
            "version": VERSION,
            "status": "e008_m124_target_free_detector_candidate_source_ready",
            "m194_status": m194_cov.get("status"),
            "compatibility_role": "M195 wrapper input for M125 navmesh validator",
            "coordinate_candidate_rows": m194_cov.get("coordinate_candidate_rows"),
            "prediction_rows": m194_cov.get("prediction_rows"),
            "pre_cap_candidate_rows": m194_cov.get("pre_cap_candidate_rows"),
            "render_ready_frame_rows": m194_cov.get("render_ready_frame_rows"),
        },
    )

    manifest_src = M193_ARTIFACT_DIR / "source_pool_detector_manifest_rows.jsonl"
    copy_required(manifest_src, compat_m122 / "target_free_detector_manifest_rows.jsonl")
    return compat_m124, compat_m122


def patch_outputs() -> dict[str, Any]:
    coverage = read_json(ARTIFACT_DIR / "coverage.json")
    original_status = str(coverage.get("status"))
    status_map = {
        "e008_m125_target_free_detector_candidate_navmesh_validation_ready": (
            "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_ready"
        ),
        "e008_m125_target_free_detector_candidate_navmesh_validation_ready_with_source_warnings": (
            "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_ready_with_source_warnings"
        ),
        "e008_m125_target_free_detector_candidate_navmesh_validation_blocked": (
            "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_blocked"
        ),
    }
    coverage["version"] = VERSION
    coverage["status"] = status_map.get(original_status, original_status)
    coverage["m125_compat_status"] = original_status
    coverage["m194_status"] = read_json(M194_ARTIFACT_DIR / "coverage.json").get("status")
    coverage["candidate_navmesh_validation_ready"] = coverage["status"] in READY_STATUSES
    coverage["selected_next_unit"] = (
        "E008-M196 source-pool scale candidate visit-order/path materialization"
        if coverage["candidate_navmesh_validation_ready"]
        else "repair E008-M195 source-pool scale candidate navmesh/source-readiness validation"
    )

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)

    route_rows = read_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl")
    for row in route_rows:
        if row.get("selected"):
            row["next_unit"] = coverage["selected_next_unit"]
            row["route_id"] = "e008_m196_source_pool_scale_candidate_visit_order_path_materialization"
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    report_path = ARTIFACT_DIR / "report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "# E008-M125 Target-Free Detector Candidate Navmesh Validation",
            "# E008-M195 Source-Pool Scale Candidate Navmesh Source-Readiness Validation",
        )
        report = report.replace("M125", "M195")
        report = report.replace("M124", "M194")
        report = report.replace("M121", "M193")
        report = report.replace("target-free detector", "source-pool scale detector")
        report = report.replace("Target-Free Detector", "Source-Pool Scale Detector")
        report = report.replace("target-free source", "source-pool scale source")
        report_path.write_text(report, encoding="utf-8")
    return coverage


def main() -> None:
    m125 = load_module(M125_TOOL, "e008_m125_navmesh_wrapper_for_m195")
    compat_m124, compat_m122 = build_compat_inputs()
    m125.ARTIFACT_DIR = ARTIFACT_DIR
    m125.DATA_OUT_DIR = DATA_OUT_DIR
    m125.M121_DATA_DIR = M193_DATA_DIR
    m125.M122_ARTIFACT_DIR = compat_m122
    m125.M124_ARTIFACT_DIR = compat_m124
    m125.VERSION = VERSION
    m125.main()
    coverage = patch_outputs()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if coverage.get("status") == "e008_m195_source_pool_scale_candidate_navmesh_source_readiness_validation_blocked":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
