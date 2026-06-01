#!/usr/bin/env python3
"""Verify E008-M86 source-gap detector candidate-source output.

This wrapper reuses the generic E008-M16 detector-candidate verifier and
rewrites the status/route names for the E008-M86 source-gap chain.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M84_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
M84_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
M86_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"
M16_VERIFIER = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
TMUX_SESSION = "e008_m86_source_gap_detector"
VERSION = "e008_m86_source_gap_detector_candidate_source_verifier_v0"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M86 Source-Gap Detector Candidate-Source Verification",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`",
            f"- Generic verifier status: `{coverage.get('generic_verifier_status')}`",
            f"- tmux running: {coverage['tmux_running']}",
            f"- Manifest rows: {coverage['manifest_rows']}",
            f"- Frame rows: {coverage['frame_rows']}",
            f"- Frames with written predictions: {coverage['frames_with_written_predictions']}",
            f"- Raw / written predictions: {coverage['raw_prediction_count']} / {coverage['written_prediction_count']}",
            f"- Final / pre-cap candidate rows: {coverage['prediction_rows']} / {coverage['pre_cap_candidate_rows']}",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}",
            f"- Validator errors / warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matching target rows: {coverage['matching_target_rows']}",
            f"- Selected next unit: {coverage['selected_next_unit']}",
            "",
            "## Claim Boundary",
            "",
            "- E008-M86 supports source-gap detector candidate-source availability and schema/coordinate readiness.",
            "- E008-M86 does not support real navigation `SR` / `SPL` because it does not validate navmesh paths or execute trajectories.",
            "- E008-M86 does not support final real RGB-D/open-vocabulary robustness because matching targets are absent and downstream recovery evaluation remains future work.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m84-artifact-dir", type=Path, default=M84_ARTIFACT_DIR)
    parser.add_argument("--m84-data-dir", type=Path, default=M84_DATA_DIR)
    parser.add_argument("--m86-dir", type=Path, default=M86_DIR)
    parser.add_argument("--tmux-session", default=TMUX_SESSION)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    command = [
        sys.executable,
        str(M16_VERIFIER),
        "--m15-artifact-dir",
        str(args.m84_artifact_dir),
        "--m15-data-dir",
        str(args.m84_data_dir),
        "--m16-dir",
        str(args.m86_dir),
        "--tmux-session",
        args.tmux_session,
    ]
    if args.require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        if result.stdout:
            sys.stderr.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.returncode

    generic = read_json(args.m86_dir / "e008_m16_verification_coverage.json")
    generic_status = str(generic.get("status"))
    ready = generic_status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready"
    status = (
        "e008_m86_source_gap_detector_candidate_source_verified"
        if ready
        else "e008_m86_source_gap_detector_candidate_source_needs_review"
    )
    selected_next = (
        "E008-M87 source-gap detector candidate navmesh/source-readiness validation"
        if ready
        else "repair E008-M86 source-gap detector candidate-source output"
    )

    coverage = dict(generic)
    coverage.update(
        {
            "version": VERSION,
            "status": status,
            "generic_verifier_status": generic_status,
            "generic_selected_next_unit": generic.get("selected_next_unit"),
            "m86_dir": str(args.m86_dir),
            "source_gap_detector_candidate_source_ready": bool(ready),
            "h001_navigation_policy_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "selected_next_unit": selected_next,
        }
    )
    route_rows = [
        {
            "decision": "selected_next" if ready else "repair",
            "launch_long_job_now": False,
            "next_unit": selected_next,
            "reason": "M86 generated source-gap detector candidates with valid coordinates."
            if ready
            else "M86 output is not ready for navmesh/source-readiness validation.",
            "route_id": "e008_m87_source_gap_detector_candidate_navmesh_validation",
            "selected": bool(ready),
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later trajectory/source-gap recovery evaluation",
            "reason": "M86 is a candidate-source gate only; navigation execution must wait for M87+ validation.",
            "route_id": "e008_real_navigation_sr_spl_now",
            "selected": False,
        },
    ]

    summary_rows = read_jsonl(args.m86_dir / "e008_m16_candidate_summary_rows.jsonl")
    write_json(args.m86_dir / "e008_m86_verification_coverage.json", coverage)
    write_jsonl(args.m86_dir / "e008_m86_candidate_summary_rows.jsonl", summary_rows)
    write_jsonl(args.m86_dir / "e008_m86_route_decision_rows.jsonl", route_rows)
    (args.m86_dir / "e008_m86_verification_report.md").write_text(build_report(coverage), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
