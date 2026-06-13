#!/usr/bin/env python3
"""Execute M183 source-pool detector policy rows as a Docker Habitat trajectory smoke."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M130_TOOL = EXP_ROOT / "tools" / "run_m130_target_free_detector_policy_trajectory_execution_smoke.py"

VERSION = "e008_m184_docker_trajectory_execution_sr_spl_v0"
READY_STATUS = "e008_m184_docker_trajectory_execution_sr_spl_ready"
BLOCKED_STATUS = "e008_m184_docker_trajectory_execution_sr_spl_blocked"
NEXT_UNIT = "E008-M185 protected detector-confidence interpretation and scale decision"

DEFAULT_M183_CONTRACT = EXP_ROOT / "artifacts" / "E008-M183_docker_trajectory_execution_contract_preflight_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M184_docker_trajectory_execution_sr_spl_v0"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    m130 = load_module(M130_TOOL, "e008_m130_trajectory_wrapper")
    m130.VERSION = VERSION
    m130.READY_STATUS = READY_STATUS
    m130.BLOCKED_STATUS = BLOCKED_STATUS
    m130.NEXT_UNIT = NEXT_UNIT
    m130.DEFAULT_M129_CONTRACT = DEFAULT_M183_CONTRACT
    m130.DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR
    m130.DEFAULT_DATA_OUT_DIR = DEFAULT_DATA_OUT_DIR

    original_argv = sys.argv[:]
    try:
        if len(sys.argv) == 1:
            sys.argv = [
                sys.argv[0],
                "--m129-contract",
                str(DEFAULT_M183_CONTRACT),
                "--out-root",
                str(DEFAULT_ARTIFACT_DIR),
                "--derived-out-root",
                str(DEFAULT_DATA_OUT_DIR),
            ]
        m130.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
