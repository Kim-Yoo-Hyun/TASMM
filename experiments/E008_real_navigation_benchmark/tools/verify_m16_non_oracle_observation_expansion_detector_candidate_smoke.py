#!/usr/bin/env python3
"""Verify E008-M16 non-oracle observation expansion detector candidate smoke."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M15_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
M15_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
M16_DIR = EXP_ROOT / "artifacts" / "E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0"
TMUX_SESSION = "e008_m16_hm3d_expanded_detector"
VERSION = "e008_m16_non_oracle_observation_expansion_detector_candidate_verifier_v0"
READY_E003_STATUSES = {
    "frame_scaling_projection_diagnostic_ready",
    "temporal_spatial_support_runner_smoke_ready",
    "support_aware_selection_runner_smoke_ready",
    "pre_cap_candidate_pool_export_smoke_ready",
    "cleanup_trace_diagnostic_ready",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def has_valid_centroid(row: dict[str, Any]) -> bool:
    value = row.get("centroid_world_m")
    if not isinstance(value, list) or len(value) != 3:
        return False
    try:
        return all(math.isfinite(float(item)) for item in value)
    except (TypeError, ValueError):
        return False


def build_candidate_summary_rows(
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    pre_cap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_scans = {str(row.get("scan_id")) for row in manifest_rows}
    by_scan = Counter(str(row.get("scan_id")) for row in predictions)
    by_scan_coord = Counter(str(row.get("scan_id")) for row in predictions if has_valid_centroid(row))
    by_scan_precap = Counter(str(row.get("scan_id")) for row in pre_cap_rows)
    by_scan_labels: dict[str, Counter[str]] = {scan_id: Counter() for scan_id in expected_scans}
    for row in predictions:
        by_scan_labels.setdefault(str(row.get("scan_id")), Counter())[str(row.get("label_canonical"))] += 1

    rows = []
    for scan_id in sorted(expected_scans | set(by_scan) | set(by_scan_precap)):
        rows.append(
            {
                "coordinate_candidate_rows": int(by_scan_coord.get(scan_id, 0)),
                "detector_candidate_rows": int(by_scan.get(scan_id, 0)),
                "label_counts": dict(sorted(by_scan_labels.get(scan_id, Counter()).items())),
                "pre_cap_candidate_rows": int(by_scan_precap.get(scan_id, 0)),
                "scan_id": scan_id,
                "sequence_candidate_source": "E008-M15 non-oracle expanded rendered RGB-D frames",
            }
        )
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M16 Non-Oracle Observation Expansion Detector Candidate Smoke",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`",
            f"- tmux running: {coverage['tmux_running']}",
            f"- M15 status: `{coverage.get('m15_status')}`",
            f"- E003 detector status: `{coverage.get('e003_detector_status')}`",
            f"- Manifest rows: {coverage['manifest_rows']}",
            f"- Frame rows: {coverage['frame_rows']}",
            f"- Frames with written predictions: {coverage['frames_with_written_predictions']}",
            f"- Raw / written predictions: {coverage['raw_prediction_count']} / {coverage['written_prediction_count']}",
            f"- Prediction rows: {coverage['prediction_rows']}",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}",
            f"- Pre-cap candidate rows: {coverage['pre_cap_candidate_rows']}",
            f"- Validator errors / warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matching target rows: {coverage['matching_target_rows']}",
            f"- Matching status: `{coverage.get('matching_status')}`",
            f"- `ObjectNav` eval fields used for policy: {str(coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']).lower()}",
            f"- Selected next unit: {coverage['selected_next_unit']}",
            "",
            "## 논문 주장",
            "",
            "- E008-M16 supports whether the leakage-safe expanded observation set can produce detector candidate coordinates.",
            "- E008-M16 does not support real navigation `SR` / `SPL` because it does not execute navigation trajectories.",
            "- E008-M16 does not support final real RGB-D/open-vocabulary robustness by itself because candidate-goal and policy evaluation remain separate gates.",
            "",
            "## 에이전트 추론",
            "",
            "- If detector candidates with valid coordinates exist, the next gate should validate snap-to-navmesh and source-to-candidate paths on the expanded candidate set.",
            "- If candidate rows are empty or dominated by invalid coordinates, the bottleneck is detector/prompt/projection rather than navigation policy.",
            "- The M15 large snap warnings must stay visible in the next navmesh/path accounting.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for this verifier.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m15-artifact-dir", type=Path, default=M15_ARTIFACT_DIR)
    parser.add_argument("--m15-data-dir", type=Path, default=M15_DATA_DIR)
    parser.add_argument("--m16-dir", type=Path, default=M16_DIR)
    parser.add_argument("--tmux-session", default=TMUX_SESSION)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    detector_inputs = args.m16_dir / "detector_inputs"
    if not detector_inputs.exists():
        detector_inputs = args.m15_data_dir / "detector_inputs"
    manifest_rows = read_jsonl(detector_inputs / "real_proposal_query_manifest.jsonl")
    m15_coverage = read_json(args.m15_artifact_dir / "verification_coverage.json")
    e003_coverage = read_json(args.m16_dir / "coverage.json")
    launch_coverage = read_json(args.m16_dir / "e008_m16_launch_coverage.json")
    validator_coverage = read_json(args.m16_dir / "validator" / "coverage.json")
    matching_coverage = read_json(args.m16_dir / "matching" / "coverage.json")
    model_status = read_json(args.m16_dir / "container_output" / "model_smoke.json")
    predictions = read_jsonl(args.m16_dir / "container_output" / "real_proposals.jsonl")
    pre_cap_rows = read_jsonl(args.m16_dir / "container_output" / "pre_cap_candidate_pool.jsonl")

    candidate_summary_rows = build_candidate_summary_rows(predictions, manifest_rows, pre_cap_rows)
    coordinate_rows = sum(1 for row in predictions if has_valid_centroid(row))
    e003_status = e003_coverage.get("status")
    detector_ready = bool(e003_status in READY_E003_STATUSES and predictions)
    validator_errors = int(validator_coverage.get("error_rows", 0) or 0)
    validator_warnings = int(validator_coverage.get("warning_rows", 0) or 0)
    frame_diag = e003_coverage.get("frame_diagnostics", {}) if e003_coverage else {}
    tmux_is_running = tmux_running(args.tmux_session)
    uses_eval_policy = bool(m15_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
    matching_target_rows = int(matching_coverage.get("target_rows", 0) or 0)

    if tmux_is_running and not (detector_ready and coordinate_rows):
        status = "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_running"
        selected_next = "Wait for E008-M16 completion verification"
    elif detector_ready and coordinate_rows:
        status = "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready"
        selected_next = "E008-M17 expanded detector candidate navmesh validation"
    elif e003_status in READY_E003_STATUSES:
        status = "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready_empty_or_no_coordinates"
        selected_next = "E008-M17 detector candidate failure diagnosis before navigation execution"
    elif not e003_coverage:
        status = "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_missing_coverage"
        selected_next = "Inspect E008-M16 log and rerun or repair detector command"
    else:
        status = "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_failed_or_needs_review"
        selected_next = "Inspect E008-M16 detector coverage/log before navigation execution"

    coverage = {
        "version": VERSION,
        "status": status,
        "m15_status": m15_coverage.get("status"),
        "m16_dir": str(args.m16_dir),
        "launch_status": launch_coverage.get("status"),
        "log_path": launch_coverage.get("log_path"),
        "tmux_running": tmux_is_running,
        "manifest_rows": len(manifest_rows),
        "e003_detector_status": e003_status,
        "frame_rows": int(frame_diag.get("frame_rows", 0) or 0),
        "frames_with_written_predictions": int(frame_diag.get("frames_with_written_predictions", 0) or 0),
        "raw_prediction_count": int(frame_diag.get("raw_prediction_count", 0) or 0),
        "written_prediction_count": int(frame_diag.get("written_prediction_count", 0) or 0),
        "prediction_rows": len(predictions),
        "coordinate_candidate_rows": coordinate_rows,
        "pre_cap_candidate_rows": len(pre_cap_rows),
        "detector_candidate_rows_by_scan": {
            row["scan_id"]: row["detector_candidate_rows"] for row in candidate_summary_rows
        },
        "pre_cap_candidate_rows_by_scan": {
            row["scan_id"]: row["pre_cap_candidate_rows"] for row in candidate_summary_rows
        },
        "validator_status": validator_coverage.get("status"),
        "validator_error_rows": validator_errors,
        "validator_warning_rows": validator_warnings,
        "matching_status": matching_coverage.get("status"),
        "matching_target_rows": matching_target_rows,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": selected_next,
    }
    route_rows = [
        {
            "claim": "expanded_detector_coordinate_candidate_source",
            "ready": bool(detector_ready and coordinate_rows),
            "reason": "Requires non-empty expanded detector rows with valid centroid_world_m.",
        },
        {
            "claim": "real_navigation_sr_spl",
            "ready": False,
            "reason": "Detector candidate smoke is not navigation trajectory execution.",
        },
        {
            "claim": "final_real_rgbd_open_vocab_robustness",
            "ready": False,
            "reason": "Requires candidate-goal evaluation, policy comparison, and scale/heldout checks.",
        },
    ]

    args.m16_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.m16_dir / "e008_m16_verification_coverage.json", coverage)
    write_jsonl(args.m16_dir / "e008_m16_candidate_summary_rows.jsonl", candidate_summary_rows)
    write_jsonl(args.m16_dir / "e008_m16_route_decision_rows.jsonl", route_rows)
    (args.m16_dir / "e008_m16_verification_report.md").write_text(build_report(coverage), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))
    ready = status == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready"
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
