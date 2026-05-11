#!/usr/bin/env python3
"""Plan E003-M32 scaled pre-cap policy rerun gate."""

from __future__ import annotations

import argparse
import json
import math
import shlex
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M30_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M30_pre_cap_policy_docker_rerun_v0"
DEFAULT_M31_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M31_pre_cap_policy_tradeoff_analysis_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M32_scaled_pre_cap_rerun_gate_v0"
M32_VERSION = "e003_m32_scaled_pre_cap_rerun_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def command_payload(command: list[str]) -> dict[str, Any]:
    return {
        "argv": command,
        "shell": shlex.join(command),
    }


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def build_scope_rows(manifest_rows: list[dict[str, Any]], max_scans: int, max_frames_per_scan: int) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(manifest_rows[:max_scans], start=1):
        sampled = int(row.get("sampled_frame_count", 0) or 0)
        selected = min(sampled, max_frames_per_scan)
        rows.append(
            {
                "detector_target_count": int(row.get("detector_target_count", 0) or 0),
                "evaluation_target_count": int(row.get("evaluation_target_count", 0) or 0),
                "full_sampled_frame_count": sampled,
                "scope_index": idx,
                "scan_id": str(row["scan_id"]),
                "selected_frame_count": selected,
                "selected_frame_rate": safe_rate(selected, sampled),
                "target_label_count": int(row.get("target_label_count", 0) or 0),
            }
        )
    return rows


def build_blocker_response_rows(blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping = {
        "two_scan_pilot_only": {
            "m32_response": "scale from 2 scans to all 8 M17 staged scans",
            "tracked_in_scaled_rerun": True,
        },
        "remaining_scan_level_misses": {
            "m32_response": "require post-rerun visibility denominator and target-transition rows",
            "tracked_in_scaled_rerun": True,
        },
        "remaining_false_positive_load": {
            "m32_response": "require label-level false-positive ranking after scaled rerun",
            "tracked_in_scaled_rerun": True,
        },
        "visibility_proxy_not_true_visibility": {
            "m32_response": "keep true visibility as non-claim; report depth-consistent visible proxy only",
            "tracked_in_scaled_rerun": True,
        },
        "top_visible_miss_labels": {
            "m32_response": "carry visible-miss label list as required post-analysis field",
            "tracked_in_scaled_rerun": True,
        },
        "top_recall_loss_labels": {
            "m32_response": "track `plant` recall loss explicitly before accepting policy as default",
            "tracked_in_scaled_rerun": True,
        },
        "top_false_positive_labels": {
            "m32_response": "track table/chair/box/light/plant false positives explicitly before paper-table scaling",
            "tracked_in_scaled_rerun": True,
        },
    }
    rows = []
    for row in blocker_rows:
        item = dict(row)
        item.update(mapping.get(str(row["blocker_id"]), {"m32_response": "record as unresolved", "tracked_in_scaled_rerun": True}))
        rows.append(item)
    return rows


def build_commands(args: argparse.Namespace) -> dict[str, Any]:
    root = REPO_ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
    detector_dir = root / "detector_rerun"
    calibration_dir = root / "match_preserving_calibration"
    visibility_dir = root / "visibility_denominator"
    detector_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--out-dir",
        str(detector_dir),
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
        "--max-scans",
        str(args.scaled_max_scans),
        "--max-frames-per-scan",
        str(args.scaled_max_frames_per_scan),
        "--max-labels",
        str(args.max_labels),
        "--max-predictions",
        str(args.max_predictions),
        "--max-predictions-per-frame",
        str(args.max_predictions_per_frame),
        "--threshold",
        str(args.threshold),
        "--text-threshold",
        str(args.text_threshold),
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        args.selection_score_mode,
        "--pre-cap-per-scan-label-cap",
        str(args.pre_cap_per_scan_label_cap),
        "--pre-cap-spatial-consolidation-radius-m",
        str(args.pre_cap_spatial_consolidation_radius_m),
        "--raw-candidate-collection-cap",
        str(args.raw_candidate_collection_cap),
    ]
    calibration_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py",
        "--m22-dir",
        str(detector_dir),
        "--out-dir",
        str(calibration_dir),
        "--selection-policy",
        "full_match_preserving",
    ]
    visibility_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py",
        "--m22-dir",
        str(detector_dir),
        "--m23-dir",
        str(calibration_dir),
        "--out-dir",
        str(visibility_dir),
        "--max-labels",
        str(args.max_labels),
    ]
    return {
        "calibration_command": command_payload(calibration_command),
        "detector_command": command_payload(detector_command),
        "docker_password_policy": "stdin_required_not_stored",
        "expected_output_root": str(root),
        "visibility_command": command_payload(visibility_command),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M32 Scaled Pre Cap Rerun Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Staged scans: {coverage['staged_scan_count']}",
            f"- Selected scans: {coverage['selected_scan_count']}",
            f"- Selected frame budget: {coverage['selected_frame_count']} / {coverage['available_sampled_frame_count']}",
            f"- Evaluation target rows in selected scope: {coverage['selected_evaluation_target_rows']}",
            f"- Max labels: {coverage['run_config']['max_labels']}",
            f"- Max predictions: {coverage['run_config']['max_predictions']}",
            f"- Candidate selection policy: `{coverage['run_config']['candidate_selection_policy']}`",
            f"- Per-scan-label cap: {coverage['run_config']['pre_cap_per_scan_label_cap']}",
            f"- Spatial consolidation radius m: {coverage['run_config']['pre_cap_spatial_consolidation_radius_m']}",
            f"- Estimated raw predictions: {coverage['estimated_raw_predictions']}",
            f"- Estimated final prediction rows: {coverage['estimated_final_prediction_rows']}",
            f"- M31 blockers tracked: {coverage['m31_blocker_rows']}",
            f"- Docker command ready: {coverage['docker_command_ready']}",
            f"- Docker run executed: {coverage['docker_run_executed']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M32 supports fixing a scaled rerun contract for the pre-cap policy.",
            "- E003-M32 does not support a detector-result claim because it does not execute Docker inference.",
            "",
            "## 에이전트 추론",
            "",
            "- The next Docker run should scale across all 8 staged scans but keep a 24-frame-per-scan budget to control CPU cost before full-frame evaluation.",
            "- M31 blockers should be treated as required post-rerun diagnostics, especially `plant` recall loss and table/chair/box/light/plant false positives.",
            "- A paper-table claim remains blocked until the scaled rerun and its failure analysis are complete.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M32. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m30-dir", default=DEFAULT_M30_DIR, type=Path)
    parser.add_argument("--m31-dir", default=DEFAULT_M31_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--scaled-max-scans", default=8, type=int)
    parser.add_argument("--scaled-max-frames-per-scan", default=24, type=int)
    parser.add_argument("--max-labels", default=32, type=int)
    parser.add_argument("--max-predictions", default=10000, type=int)
    parser.add_argument("--max-predictions-per-frame", default=60, type=int)
    parser.add_argument("--pre-cap-per-scan-label-cap", default=24, type=int)
    parser.add_argument("--pre-cap-spatial-consolidation-radius-m", default=0.5, type=float)
    parser.add_argument("--raw-candidate-collection-cap", default=200000, type=int)
    parser.add_argument("--selection-score-mode", default="confidence")
    parser.add_argument("--threshold", default=0.08, type=float)
    parser.add_argument("--text-threshold", default=0.08, type=float)
    args = parser.parse_args()

    manifest_rows = load_jsonl(args.m17_dir / "real_proposal_query_manifest.jsonl")
    m30_coverage = load_json(args.m30_dir / "coverage.json")
    m31_coverage = load_json(args.m31_dir / "coverage.json")
    blocker_rows = load_jsonl(args.m31_dir / "scaling_blocker_rows.jsonl")
    scope_rows = build_scope_rows(
        manifest_rows=manifest_rows,
        max_scans=args.scaled_max_scans,
        max_frames_per_scan=args.scaled_max_frames_per_scan,
    )
    blocker_response_rows = build_blocker_response_rows(blocker_rows)

    selected_frames = sum(row["selected_frame_count"] for row in scope_rows)
    available_frames = sum(row["full_sampled_frame_count"] for row in scope_rows)
    eval_targets = sum(row["evaluation_target_count"] for row in scope_rows)
    m30_frames = int(m30_coverage.get("evaluated_frame_count", 0) or 0)
    raw_per_frame = float(m30_coverage.get("frame_raw_prediction_rows", 0) or 0) / max(m30_frames, 1)
    final_rows = int(
        m30_coverage.get(
            "m30_written_predictions",
            m30_coverage.get("frame_written_prediction_rows", 0),
        )
        or 0
    )
    final_per_frame = float(final_rows) / max(m30_frames, 1)
    estimated_raw = int(math.ceil(raw_per_frame * selected_frames))
    estimated_final = int(math.ceil(final_per_frame * selected_frames))
    commands = build_commands(args)

    coverage = {
        "available_sampled_frame_count": available_frames,
        "docker_command_ready": True,
        "docker_run_executed": False,
        "estimated_final_prediction_rows": estimated_final,
        "estimated_raw_predictions": estimated_raw,
        "m31_blocker_rows": len(blocker_response_rows),
        "m31_reference": {
            "m30_gain_targets_vs_m26": m31_coverage.get("m30_gain_targets_vs_m26"),
            "m30_loss_targets_vs_m26": m31_coverage.get("m30_loss_targets_vs_m26"),
            "top_false_positive_labels": m31_coverage.get("top_false_positive_labels"),
            "top_loss_labels": m31_coverage.get("top_loss_labels"),
        },
        "m32_version": M32_VERSION,
        "next_recommended_unit": "E003-M33 scaled pre-cap policy Docker rerun",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_config": {
            "candidate_selection_policy": "cap_aware_label_balanced_ranking_v0",
            "max_frames_per_scan": args.scaled_max_frames_per_scan,
            "max_labels": args.max_labels,
            "max_predictions": args.max_predictions,
            "max_predictions_per_frame": args.max_predictions_per_frame,
            "max_scans": args.scaled_max_scans,
            "pre_cap_per_scan_label_cap": args.pre_cap_per_scan_label_cap,
            "pre_cap_spatial_consolidation_radius_m": args.pre_cap_spatial_consolidation_radius_m,
            "raw_candidate_collection_cap": args.raw_candidate_collection_cap,
            "selection_score_mode": args.selection_score_mode,
            "text_threshold": args.text_threshold,
            "threshold": args.threshold,
        },
        "selected_evaluation_target_rows": eval_targets,
        "selected_frame_count": selected_frames,
        "selected_route": "staged_8scan_24frame_pre_cap_scaled_pilot",
        "selected_scan_count": len(scope_rows),
        "staged_scan_count": len(manifest_rows),
        "status": "scaled_pre_cap_rerun_gate_ready",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "scaled_scope_rows.jsonl", scope_rows)
    write_jsonl(args.out_dir / "blocker_response_rows.jsonl", blocker_response_rows)
    write_json(args.out_dir / "scaled_rerun_plan.json", commands)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
