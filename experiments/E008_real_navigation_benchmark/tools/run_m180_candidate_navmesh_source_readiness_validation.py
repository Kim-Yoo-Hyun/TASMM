#!/usr/bin/env python3
"""Validate M179 source-pool detector candidates against HM3D navmeshes."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M125_TOOL = EXP_ROOT / "tools" / "run_m125_target_free_detector_candidate_navmesh_validation.py"

VERSION = "e008_m180_candidate_navmesh_source_readiness_validation_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"

M178_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
M178_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
M179_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M179_bounded_render_detector_execution_verification_v0"


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
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def copy_if_needed(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def build_compat_inputs() -> tuple[Path, Path]:
    compat_root = ARTIFACT_DIR / "_compat_inputs"
    compat_m124 = compat_root / "m124_detector"
    compat_m122 = compat_root / "m122_launcher"

    proposal_src = M179_ARTIFACT_DIR / "detector" / "container_output" / "real_proposals.jsonl"
    copy_if_needed(proposal_src, compat_m124 / "container_output" / "real_proposals.jsonl")

    m179_cov = read_json(M179_ARTIFACT_DIR / "coverage.json")
    detector_cov = read_json(M179_ARTIFACT_DIR / "detector" / "e008_m16_verification_coverage.json")
    write_json(
        compat_m124 / "e008_m124_verification_coverage.json",
        {
            **detector_cov,
            "version": VERSION,
            "status": "e008_m124_target_free_detector_candidate_source_ready",
            "m179_status": m179_cov.get("status"),
            "compatibility_role": "M180 wrapper input for M125 navmesh validator",
            "coordinate_candidate_rows": m179_cov.get("coordinate_candidate_rows"),
            "prediction_rows": m179_cov.get("prediction_rows"),
        },
    )

    manifest_src = M178_ARTIFACT_DIR / "source_pool_detector_manifest_rows.jsonl"
    copy_if_needed(manifest_src, compat_m122 / "target_free_detector_manifest_rows.jsonl")
    return compat_m124, compat_m122


def patch_outputs() -> dict[str, Any]:
    coverage = read_json(ARTIFACT_DIR / "coverage.json")
    original_status = coverage.get("status")
    status_map = {
        "e008_m125_target_free_detector_candidate_navmesh_validation_ready": (
            "e008_m180_candidate_navmesh_source_readiness_validation_ready"
        ),
        "e008_m125_target_free_detector_candidate_navmesh_validation_ready_with_source_warnings": (
            "e008_m180_candidate_navmesh_source_readiness_validation_ready_with_source_warnings"
        ),
        "e008_m125_target_free_detector_candidate_navmesh_validation_blocked": (
            "e008_m180_candidate_navmesh_source_readiness_validation_blocked"
        ),
    }
    coverage["version"] = VERSION
    coverage["status"] = status_map.get(str(original_status), str(original_status))
    coverage["m125_compat_status"] = original_status
    coverage["m179_status"] = read_json(M179_ARTIFACT_DIR / "coverage.json").get("status")
    coverage["selected_next_unit"] = (
        "E008-M181 expanded candidate visit-order/path materialization"
        if coverage["status"]
        in {
            "e008_m180_candidate_navmesh_source_readiness_validation_ready",
            "e008_m180_candidate_navmesh_source_readiness_validation_ready_with_source_warnings",
        }
        else "repair E008-M180 candidate navmesh/source-readiness validation"
    )
    coverage["candidate_navmesh_validation_ready"] = coverage["status"] in {
        "e008_m180_candidate_navmesh_source_readiness_validation_ready",
        "e008_m180_candidate_navmesh_source_readiness_validation_ready_with_source_warnings",
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)

    route_rows = read_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl")
    for row in route_rows:
        if row.get("selected"):
            row["next_unit"] = coverage["selected_next_unit"]
            row["route_id"] = "e008_m181_expanded_candidate_visit_order_path_materialization"
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    report_path = ARTIFACT_DIR / "report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "# E008-M125 Target-Free Detector Candidate Navmesh Validation",
            "# E008-M180 Candidate Navmesh Source-Readiness Validation",
        )
        report = report.replace("M125", "M180")
        report = report.replace("M124", "M179")
        report_path.write_text(report, encoding="utf-8")
    return coverage


def main() -> None:
    m125 = load_module(M125_TOOL, "e008_m125_navmesh_wrapper")
    compat_m124, compat_m122 = build_compat_inputs()
    m125.ARTIFACT_DIR = ARTIFACT_DIR
    m125.DATA_OUT_DIR = DATA_OUT_DIR
    m125.M121_DATA_DIR = M178_DATA_DIR
    m125.M122_ARTIFACT_DIR = compat_m122
    m125.M124_ARTIFACT_DIR = compat_m124
    m125.VERSION = VERSION
    m125.main()
    coverage = patch_outputs()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if coverage.get("status") == "e008_m180_candidate_navmesh_source_readiness_validation_blocked":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
