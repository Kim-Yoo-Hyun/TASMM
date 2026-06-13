#!/usr/bin/env python3
"""Materialize M180 source-pool detector candidate visit-order/path rows."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M126_TOOL = EXP_ROOT / "tools" / "run_m126_target_free_detector_candidate_visit_order_path_smoke.py"

VERSION = "e008_m181_expanded_candidate_visit_order_path_materialization_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M181_expanded_candidate_visit_order_path_materialization_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M181_expanded_candidate_visit_order_path_materialization_v0"
M180_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"


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


def main() -> None:
    m126 = load_module(M126_TOOL, "e008_m126_visit_wrapper")
    m126.ARTIFACT_DIR = ARTIFACT_DIR
    m126.DATA_OUT_DIR = DATA_OUT_DIR
    m126.M125_ARTIFACT_DIR = M180_ARTIFACT_DIR
    m126.VERSION = VERSION
    m126.main()

    coverage = read_json(ARTIFACT_DIR / "coverage.json")
    original_status = coverage.get("status")
    ready = original_status == "e008_m126_target_free_detector_candidate_visit_order_path_smoke_ready"
    coverage["version"] = VERSION
    coverage["status"] = (
        "e008_m181_expanded_candidate_visit_order_path_materialization_ready"
        if ready
        else "e008_m181_expanded_candidate_visit_order_path_materialization_blocked"
    )
    coverage["m126_compat_status"] = original_status
    coverage["m180_status"] = read_json(M180_ARTIFACT_DIR / "coverage.json").get("status")
    coverage["selected_next_unit"] = (
        "E008-M182 leakage-safe goal-evaluation proxy"
        if ready
        else "repair E008-M181 expanded candidate visit-order/path materialization"
    )
    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)

    report_path = ARTIFACT_DIR / "report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "# E008-M126 Target-Free Detector Candidate Visit-Order Path Smoke",
            "# E008-M181 Expanded Candidate Visit-Order Path Materialization",
        )
        report = report.replace("M126", "M181")
        report_path.write_text(report, encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
