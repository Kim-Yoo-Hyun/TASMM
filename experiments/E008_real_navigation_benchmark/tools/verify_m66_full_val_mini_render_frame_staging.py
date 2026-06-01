#!/usr/bin/env python3
"""Verify E008-M66 full-val-mini render frame staging."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M65_full_val_mini_render_detector_contract_v0"
M15_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m15_non_oracle_observation_expansion_frame_staging.py"
VERSION = "e008_m66_full_val_mini_render_frame_staging_verifier_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_m15_verifier():
    spec = importlib.util.spec_from_file_location("e008_m15_verify_tool", M15_VERIFY_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 verifier: {M15_VERIFY_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rewrite_status(old_status: str) -> str:
    if old_status == "e008_m15_non_oracle_observation_expansion_frame_staging_verified":
        return "e008_m66_full_val_mini_render_frame_staging_verified"
    if old_status == "e008_m15_non_oracle_observation_expansion_frame_staging_verified_with_snap_warnings":
        return "e008_m66_full_val_mini_render_frame_staging_verified_with_snap_warnings"
    return "e008_m66_full_val_mini_render_frame_staging_verification_failed"


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M66 Full-Val-Mini Render Frame Staging Verification",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Expected frames: {coverage['expected_frame_rows']}.",
            f"- Ready frames: {coverage['ready_frame_rows']}.",
            f"- Ready scans: {coverage['ready_scan_rows']} / {coverage['scan_rows']}.",
            f"- Snap validation rows: {coverage['snap_validation_rows']}.",
            f"- Snap-ready rows: {coverage['snap_ready_rows']}.",
            f"- Large snap warning rows: {coverage['large_snap_warning_rows']}.",
            f"- Detector input files ready: {coverage['detector_input_files_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## 논문 주장",
            "",
            "- M66 verifies rendered RGB-D frame staging only.",
            "- M66 does not support detector candidate quality, real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.",
            "",
            "## 에이전트 추론",
            "",
            "- If M66 is verified, M67 can run open-vocabulary detector candidate-source generation on the staged frames.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--data-out-dir", type=Path, default=DATA_OUT_DIR)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    module = load_m15_verifier()
    module.ARTIFACT_DIR = args.artifact_dir
    module.DATA_OUT_DIR = args.data_out_dir
    module.VERSION = VERSION
    coverage = module.run()
    old_status = str(coverage.get("status"))
    ready = old_status.startswith("e008_m15_non_oracle_observation_expansion_frame_staging_verified")
    coverage.update(
        {
            "version": VERSION,
            "status": rewrite_status(old_status),
            "artifact_output_root": str(args.artifact_dir),
            "derived_output_root": str(args.data_out_dir),
            "selected_next_unit": "E008-M67 full-val-mini detector candidate-source background launch"
            if ready
            else "repair E008-M66 render frame staging",
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    )
    write_json(args.artifact_dir / "verification_coverage.json", coverage)
    write_text(args.artifact_dir / "verification_report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
