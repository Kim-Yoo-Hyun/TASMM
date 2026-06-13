#!/usr/bin/env python3
"""Run leakage-safe ObjectNav goal-evaluation proxy for M181 rows."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M127_TOOL = EXP_ROOT / "tools" / "run_m127_target_free_detector_candidate_goal_evaluation_smoke.py"

VERSION = "e008_m182_leakage_safe_goal_evaluation_proxy_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M182_leakage_safe_goal_evaluation_proxy_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M182_leakage_safe_goal_evaluation_proxy_v0"
M180_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"
M181_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M181_expanded_candidate_visit_order_path_materialization_v0"


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
    m127 = load_module(M127_TOOL, "e008_m127_goal_wrapper")
    m127.ARTIFACT_DIR = ARTIFACT_DIR
    m127.DATA_OUT_DIR = DATA_OUT_DIR
    m127.M125_ARTIFACT_DIR = M180_ARTIFACT_DIR
    m127.M126_ARTIFACT_DIR = M181_ARTIFACT_DIR
    m127.VERSION = VERSION
    m127.main()

    coverage = read_json(ARTIFACT_DIR / "coverage.json")
    original_status = coverage.get("status")
    ready = original_status == "e008_m127_target_free_detector_candidate_goal_evaluation_smoke_ready"
    proxy_recovery = bool(coverage.get("target_free_proxy_recovery_observed"))
    coverage["version"] = VERSION
    coverage["status"] = (
        "e008_m182_leakage_safe_goal_evaluation_proxy_ready"
        if ready
        else "e008_m182_leakage_safe_goal_evaluation_proxy_blocked"
    )
    coverage["m127_compat_status"] = original_status
    coverage["m180_status"] = read_json(M180_ARTIFACT_DIR / "coverage.json").get("status")
    coverage["m181_status"] = read_json(M181_ARTIFACT_DIR / "coverage.json").get("status")
    coverage["selected_next_unit"] = (
        "E008-M183 Docker trajectory execution contract/preflight"
        if ready and proxy_recovery
        else "repair E008-M182 proxy recovery before trajectory execution"
    )
    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)

    report_path = ARTIFACT_DIR / "report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "# E008-M127 Target-Free Detector Candidate Goal-Evaluation Smoke",
            "# E008-M182 Leakage-Safe Goal-Evaluation Proxy",
        )
        report = report.replace("M127", "M182")
        report_path.write_text(report, encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready or not proxy_recovery:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
