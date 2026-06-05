#!/usr/bin/env python3
"""Verify E008-M97 coverage-expansion detector candidate-source output."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M16_VERIFIER = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
M95_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0"
M96_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M96_coverage_expansion_render_frame_staging_launch_v0"
M93_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
M97_DIR = EXP_ROOT / "artifacts" / "E008-M97_coverage_expansion_detector_candidate_source_v0"
TMUX_SESSION = "e008_m97_coverage_detector"
VERSION = "e008_m97_coverage_expansion_detector_candidate_source_verifier_v0"


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M97 Coverage-Expansion Detector Candidate-Source Verification",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Generic verifier status: `{coverage.get('generic_verifier_status')}`.",
            f"- tmux running: {coverage['tmux_running']}.",
            f"- Log path: `{coverage.get('log_path')}`.",
            f"- Manifest rows: {coverage['manifest_rows']}.",
            f"- Frame rows: {coverage['frame_rows']}.",
            f"- Frames with written predictions: {coverage['frames_with_written_predictions']}.",
            f"- Raw / written predictions: {coverage['raw_prediction_count']} / {coverage['written_prediction_count']}.",
            f"- Final / pre-cap candidate rows: {coverage['prediction_rows']} / {coverage['pre_cap_candidate_rows']}.",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}.",
            f"- Validator errors / warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}.",
            f"- Matching target rows: {coverage['matching_target_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- E008-M97 supports coverage-expansion detector candidate-source availability and schema/coordinate readiness.",
            "- E008-M97 does not support source-gap recovery because goal/viewpoint recovery scoring has not run yet.",
            "- E008-M97 does not support real navigation `SR` / `SPL` because it does not validate navmesh paths or execute trajectories.",
            "",
        ]
    )


def m97_command_row() -> dict[str, Any]:
    rows = read_jsonl(M95_ARTIFACT_DIR / "long_job_command_rows.jsonl")
    for row in rows:
        if row.get("job_id") == "E008-M97":
            return row
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m96-artifact-dir", type=Path, default=M96_ARTIFACT_DIR)
    parser.add_argument("--m93-data-dir", type=Path, default=M93_DATA_DIR)
    parser.add_argument("--m97-dir", type=Path, default=M97_DIR)
    parser.add_argument("--tmux-session", default=TMUX_SESSION)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    command = [
        sys.executable,
        str(M16_VERIFIER),
        "--m15-artifact-dir",
        str(args.m96_artifact_dir),
        "--m15-data-dir",
        str(args.m93_data_dir),
        "--m16-dir",
        str(args.m97_dir),
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

    generic = read_json(args.m97_dir / "e008_m16_verification_coverage.json")
    m96 = read_json(args.m96_artifact_dir / "coverage.json")
    command_row = m97_command_row()
    generic_status = str(generic.get("status"))
    ready = generic_status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready"
    status = (
        "e008_m97_coverage_expansion_detector_candidate_source_verified"
        if ready
        else "e008_m97_coverage_expansion_detector_candidate_source_needs_review"
    )
    selected_next = (
        "E008-M98 coverage-expansion detector candidate navmesh/source-readiness validation"
        if ready
        else "repair E008-M97 coverage-expansion detector candidate-source output"
    )

    coverage = dict(generic)
    coverage.update(
        {
            "version": VERSION,
            "status": status,
            "generic_verifier_status": generic_status,
            "generic_selected_next_unit": generic.get("selected_next_unit"),
            "m96_status": m96.get("status"),
            "m96_artifact_root": str(args.m96_artifact_dir),
            "m93_data_root": str(args.m93_data_dir),
            "m97_dir": str(args.m97_dir),
            "log_path": command_row.get("log_path") or generic.get("log_path"),
            "launch_command": command_row.get("command"),
            "verification_command": command_row.get("verification_command"),
            "coverage_expansion_detector_candidate_source_ready": bool(ready),
            "source_gap_recovery_evaluated": False,
            "trajectory_execution_ready": False,
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
            "reason": "M97 generated coverage-expansion detector candidates with valid coordinates."
            if ready
            else "M97 output is not ready for navmesh/source-readiness validation.",
            "route_id": "e008_m98_coverage_expansion_detector_candidate_navmesh_validation",
            "selected": bool(ready),
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later source-gap recovery and trajectory evaluation",
            "reason": "M97 is a candidate-source gate only; source-gap recovery must wait for M98+ validation/evaluation.",
            "route_id": "e008_source_gap_recovery_or_navigation_sr_spl_now",
            "selected": False,
        },
    ]

    summary_rows = read_jsonl(args.m97_dir / "e008_m16_candidate_summary_rows.jsonl")
    write_json(args.m97_dir / "e008_m97_verification_coverage.json", coverage)
    write_jsonl(args.m97_dir / "e008_m97_candidate_summary_rows.jsonl", summary_rows)
    write_jsonl(args.m97_dir / "e008_m97_route_decision_rows.jsonl", route_rows)
    (args.m97_dir / "e008_m97_verification_report.md").write_text(build_report(coverage), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
