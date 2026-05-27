#!/usr/bin/env python3
"""Verify E008-M09 HM3D rendered RGB-D detector candidate smoke."""

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
DEFAULT_M08_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
DEFAULT_M08_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
)
DEFAULT_M09_DIR = EXP_ROOT / "artifacts" / "E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0"
VERSION = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_verifier_v0"
TMUX_SESSION = "e008_m09_hm3d_rgbd_detector"
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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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
        return all(math.isfinite(float(v)) for v in value)
    except (TypeError, ValueError):
        return False


def build_candidate_summary_rows(predictions: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_scans = {str(row.get("scan_id")) for row in manifest_rows}
    rows: list[dict[str, Any]] = []
    by_scan = Counter(str(row.get("scan_id")) for row in predictions)
    by_scan_coord = Counter(str(row.get("scan_id")) for row in predictions if has_valid_centroid(row))
    by_scan_labels: dict[str, Counter[str]] = {scan_id: Counter() for scan_id in expected_scans}
    for row in predictions:
        scan_id = str(row.get("scan_id"))
        by_scan_labels.setdefault(scan_id, Counter())[str(row.get("label_canonical"))] += 1
    for scan_id in sorted(expected_scans | set(by_scan)):
        rows.append(
            {
                "coordinate_candidate_rows": int(by_scan_coord.get(scan_id, 0)),
                "detector_candidate_rows": int(by_scan.get(scan_id, 0)),
                "label_counts": dict(sorted(by_scan_labels.get(scan_id, Counter()).items())),
                "scan_id": scan_id,
                "sequence_candidate_source": "E008-M08 rendered RGB-D frames",
            }
        )
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M09 HM3D Rendered RGB-D Detector Candidate Smoke Verification",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`",
            f"- E003 detector status: `{coverage.get('e003_detector_status')}`",
            f"- tmux running: {coverage['tmux_running']}",
            f"- Manifest rows: {coverage['manifest_rows']}",
            f"- Prediction rows: {coverage['prediction_rows']}",
            f"- Coordinate candidate rows: {coverage['coordinate_candidate_rows']}",
            f"- Validator status: `{coverage.get('validator_status')}`",
            f"- Validator errors / warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matching status: `{coverage.get('matching_status')}`",
            f"- Evaluated scans: {coverage['evaluated_scan_count']}",
            f"- Frame rows: {coverage['frame_rows']}",
            f"- Raw / written predictions: {coverage['raw_prediction_count']} / {coverage['written_prediction_count']}",
            f"- Selected next unit: {coverage['selected_next_unit']}",
            "",
            "## 논문 주장",
            "",
            "- E008-M09 is a detector-candidate source gate for real navigation expansion.",
            "- E008-M09 does not support real navigation `SR` / `SPL` by itself.",
            "- E008-M09 does not support final real RGB-D/open-vocabulary robustness by itself.",
            "",
            "## 에이전트 추론",
            "",
            "- If coordinate candidates exist, the next necessary gate is coordinate-frame and snap-to-navmesh validation.",
            "- If candidates are empty or detector execution fails, the next necessary gate is detector/prompt/runtime failure diagnosis.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m08-artifact-dir", type=Path, default=DEFAULT_M08_ARTIFACT_DIR)
    parser.add_argument("--m08-data-dir", type=Path, default=DEFAULT_M08_DATA_DIR)
    parser.add_argument("--m09-dir", type=Path, default=DEFAULT_M09_DIR)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    detector_inputs = args.m08_data_dir / "detector_inputs"
    manifest_rows = read_jsonl(detector_inputs / "real_proposal_query_manifest.jsonl")
    m08_coverage = read_json(args.m08_artifact_dir / "coverage.json")
    e003_coverage = read_json(args.m09_dir / "coverage.json")
    validator_coverage = read_json(args.m09_dir / "validator" / "coverage.json")
    matching_coverage = read_json(args.m09_dir / "matching" / "coverage.json")
    model_status = read_json(args.m09_dir / "container_output" / "model_smoke.json")
    predictions = read_jsonl(args.m09_dir / "container_output" / "real_proposals.jsonl")
    pre_cap_rows = read_jsonl(args.m09_dir / "container_output" / "pre_cap_candidate_pool.jsonl")

    candidate_summary_rows = build_candidate_summary_rows(predictions, manifest_rows)
    coordinate_rows = sum(1 for row in predictions if has_valid_centroid(row))
    e003_status = e003_coverage.get("status")
    detector_ready = bool(e003_status in READY_E003_STATUSES and predictions)
    validator_errors = int(validator_coverage.get("error_rows", 0) or 0)
    validator_warnings = int(validator_coverage.get("warning_rows", 0) or 0)
    frame_diag = e003_coverage.get("frame_diagnostics", {}) if e003_coverage else {}
    tmux_is_running = tmux_running(TMUX_SESSION)

    if detector_ready and coordinate_rows:
        status = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_ready"
        selected_next = "E008-M10 detector candidate coordinate-frame and snap-to-navmesh validation"
    elif e003_status in READY_E003_STATUSES:
        status = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_ready_empty_or_no_coordinates"
        selected_next = "E008-M10 detector candidate failure diagnosis before navigation execution"
    elif tmux_is_running and not e003_coverage:
        status = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_running"
        selected_next = "Wait for E008-M09 completion verification"
    elif not e003_coverage:
        status = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_missing_coverage"
        selected_next = "Inspect E008-M09 log and rerun or repair detector command"
    else:
        status = "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_failed_or_needs_review"
        selected_next = "Inspect E008-M09 detector coverage/log before navigation execution"

    coverage = {
        "coordinate_candidate_rows": coordinate_rows,
        "detector_candidate_rows_by_scan": {row["scan_id"]: row["detector_candidate_rows"] for row in candidate_summary_rows},
        "e003_detector_status": e003_status,
        "evaluated_scan_count": int(matching_coverage.get("evaluated_scan_count", 0) or 0),
        "frame_rows": int(frame_diag.get("frame_rows", 0) or 0),
        "h001_navigation_policy_execution_ready": False,
        "m08_ready": m08_coverage.get("status") == "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_ready",
        "manifest_rows": len(manifest_rows),
        "matching_status": matching_coverage.get("status"),
        "m09_dir": str(args.m09_dir),
        "prediction_rows": len(predictions),
        "pre_cap_candidate_rows": len(pre_cap_rows),
        "raw_prediction_count": int(frame_diag.get("raw_prediction_count", 0) or 0),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": selected_next,
        "status": status,
        "tmux_running": tmux_is_running,
        "validator_error_rows": validator_errors,
        "validator_status": validator_coverage.get("status"),
        "validator_warning_rows": validator_warnings,
        "version": VERSION,
        "written_prediction_count": int(frame_diag.get("written_prediction_count", 0) or 0),
    }

    route_rows = [
        {
            "claim": "real_navigation_sr_spl",
            "ready": False,
            "reason": "Detector candidate smoke is not trajectory execution.",
        },
        {
            "claim": "coordinate_candidate_source",
            "ready": bool(detector_ready and coordinate_rows),
            "reason": "Requires non-empty detector rows with valid centroid_world_m.",
        },
        {
            "claim": "next_gate",
            "ready": bool(detector_ready and coordinate_rows),
            "selected_next_unit": selected_next,
        },
    ]

    args.m09_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.m09_dir / "e008_m09_verification_coverage.json", coverage)
    write_jsonl(args.m09_dir / "e008_m09_candidate_summary_rows.jsonl", candidate_summary_rows)
    write_jsonl(args.m09_dir / "e008_m09_route_decision_rows.jsonl", route_rows)
    (args.m09_dir / "e008_m09_verification_report.md").write_text(build_report(coverage), encoding="utf-8")

    ready = status == "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_ready"
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
