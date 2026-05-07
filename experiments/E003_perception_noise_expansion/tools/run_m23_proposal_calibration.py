#!/usr/bin/env python3
"""Run E003-M23 detector proposal consolidation/calibration sweep."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

from evaluate_m21_detector_matching import (
    build_label_metrics,
    distance_m,
    load_jsonl,
    match_proposals,
    numeric_summary,
    safe_rate,
    write_json,
    write_jsonl,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M22_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M22_frame_scaling_projection_diagnostic_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M23_proposal_consolidation_calibration_v0"
M23_VERSION = "e003_m23_proposal_consolidation_calibration_v0"


def score_proposal(row: dict[str, Any], score_mode: str) -> float:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    depth_pixels = float(row.get("depth_valid_pixel_count", 0.0) or 0.0)
    if score_mode == "confidence":
        return confidence
    if score_mode == "confidence_log_depth":
        return confidence * min(1.0, math.log1p(depth_pixels) / math.log1p(5000.0))
    if score_mode == "confidence_sqrt_depth":
        return confidence * min(1.0, math.sqrt(depth_pixels) / math.sqrt(5000.0))
    raise ValueError(f"unknown score mode: {score_mode}")


def filter_proposals(
    proposals: list[dict[str, Any]],
    confidence_threshold: float,
    min_depth_pixels: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in proposals
        if float(row.get("confidence", 0.0) or 0.0) >= confidence_threshold
        and int(row.get("depth_valid_pixel_count", 0) or 0) >= min_depth_pixels
    ]


def spatial_nms(
    proposals: list[dict[str, Any]],
    radius_m: float,
    score_mode: str,
) -> list[dict[str, Any]]:
    if radius_m <= 0:
        return sorted(
            proposals,
            key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))),
        )

    kept: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in proposals:
        grouped.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(row)

    for _, rows in sorted(grouped.items()):
        ranked = sorted(
            rows,
            key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))),
        )
        local_kept: list[dict[str, Any]] = []
        for row in ranked:
            if all(distance_m(row["centroid_world_m"], kept_row["centroid_world_m"]) > radius_m for kept_row in local_kept):
                local_kept.append(row)
        kept.extend(local_kept)
    return sorted(kept, key=lambda row: str(row.get("proposal_uid", "")))


def f1_score(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def evaluate_config(
    proposals: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    fixed_label_overlap_targets: list[dict[str, Any]],
    confidence_threshold: float,
    min_depth_pixels: int,
    nms_radius_m: float,
    score_mode: str,
    match_threshold_m: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    filtered = filter_proposals(proposals, confidence_threshold, min_depth_pixels)
    retained = spatial_nms(filtered, nms_radius_m, score_mode)
    matched_proposals, target_rows, matched_targets = match_proposals(
        proposals=retained,
        eval_targets=eval_targets,
        threshold_m=match_threshold_m,
    )
    matched_rows = [row for row in matched_proposals if row["match_status"] == "matched"]
    false_positive_rows = [
        row
        for row in matched_proposals
        if row["match_status"] in {"unmatched_false_positive", "unmatched_no_same_label_target"}
    ]
    fixed_label_set = {str(row["label_canonical"]) for row in fixed_label_overlap_targets}
    fixed_label_matched = sum(1 for row in target_rows if row["matched"] and row["label_canonical"] in fixed_label_set)
    proposal_precision = safe_rate(len(matched_rows), len(matched_proposals))
    scan_recall = safe_rate(len(matched_targets), len(eval_targets))
    fixed_label_recall = safe_rate(fixed_label_matched, len(fixed_label_overlap_targets))
    row = {
        "calibration_f1": f1_score(proposal_precision, fixed_label_recall),
        "confidence_threshold": confidence_threshold,
        "false_positive_proposal_rate": safe_rate(len(false_positive_rows), len(matched_proposals)),
        "false_positive_proposal_rows": len(false_positive_rows),
        "filtered_proposal_rows": len(filtered),
        "fixed_label_overlap_target_recall": fixed_label_recall,
        "fixed_label_overlap_target_rows": len(fixed_label_overlap_targets),
        "match_distance_threshold_m": match_threshold_m,
        "matched_centroid_error_m": numeric_summary(
            [float(row["match_distance_m"]) for row in matched_rows if row.get("match_distance_m") is not None]
        ),
        "matched_proposal_rows": len(matched_rows),
        "matched_target_rows": len(matched_targets),
        "min_depth_pixels": min_depth_pixels,
        "nms_radius_m": nms_radius_m,
        "proposal_precision": proposal_precision,
        "retained_proposal_rows": len(retained),
        "scan_target_recall": scan_recall,
        "score_mode": score_mode,
    }
    return row, retained, matched_proposals, target_rows


def select_config(sweep_rows: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_matched = int(baseline["matched_target_rows"])
    min_matched = max(1, math.ceil(baseline_matched * 0.5))
    eligible = [row for row in sweep_rows if int(row["matched_target_rows"]) >= min_matched]
    if not eligible:
        eligible = sweep_rows
    return sorted(
        eligible,
        key=lambda row: (
            -(row["calibration_f1"] if row["calibration_f1"] is not None else -1.0),
            -(row["proposal_precision"] if row["proposal_precision"] is not None else -1.0),
            -float(row["fixed_label_overlap_target_recall"] or 0.0),
            int(row["false_positive_proposal_rows"]),
            int(row["retained_proposal_rows"]),
        ),
    )[0]


def best_with_min_matched(sweep_rows: list[dict[str, Any]], min_matched: int) -> dict[str, Any] | None:
    eligible = [row for row in sweep_rows if int(row["matched_target_rows"]) >= min_matched]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda row: (
            -(row["proposal_precision"] if row["proposal_precision"] is not None else -1.0),
            int(row["false_positive_proposal_rows"]),
            int(row["retained_proposal_rows"]),
            -float(row["fixed_label_overlap_target_recall"] or 0.0),
        ),
    )[0]


def summarize_confidence(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [float(row.get("confidence", 0.0) or 0.0) for row in rows]
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {"max": max(values), "mean": mean(values), "median": median(values), "min": min(values)}


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_config"]
    baseline = coverage["baseline_config"]
    return "\n".join(
        [
            "# E003-M23 Proposal Consolidation Calibration",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Input proposal rows: {coverage['input_proposal_rows']}",
            f"- Sweep rows: {coverage['sweep_rows']}",
            f"- Baseline retained proposal rows: {baseline['retained_proposal_rows']}",
            f"- Baseline matched target rows: {baseline['matched_target_rows']}",
            f"- Baseline proposal precision: {baseline['proposal_precision']}",
            f"- Baseline fixed label-overlap target recall: {baseline['fixed_label_overlap_target_recall']}",
            f"- Best full-match-preserving proposal precision: {coverage['full_match_preserving_config']['proposal_precision'] if coverage['full_match_preserving_config'] else None}",
            f"- Best full-match-preserving false-positive rows: {coverage['full_match_preserving_config']['false_positive_proposal_rows'] if coverage['full_match_preserving_config'] else None}",
            f"- Selected confidence threshold: {selected['confidence_threshold']}",
            f"- Selected min depth pixels: {selected['min_depth_pixels']}",
            f"- Selected NMS radius m: {selected['nms_radius_m']}",
            f"- Selected score mode: `{selected['score_mode']}`",
            f"- Selected retained proposal rows: {selected['retained_proposal_rows']}",
            f"- Selected matched target rows: {selected['matched_target_rows']}",
            f"- Selected false-positive proposal rows: {selected['false_positive_proposal_rows']}",
            f"- Selected proposal precision: {selected['proposal_precision']}",
            f"- Selected scan target recall: {selected['scan_target_recall']}",
            f"- Selected fixed label-overlap target recall: {selected['fixed_label_overlap_target_recall']}",
            f"- Selected calibration F1: {selected['calibration_f1']}",
            f"- Selection policy: `{coverage['selection_policy']}`",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M23 supports a calibration/consolidation diagnostic over M22 detector proposals.",
            "- E003-M23 does not support real perception robustness because the sweep is tuned on one scan and uses 3DSSG matching only for evaluation.",
            "",
            "## 에이전트 추론",
            "",
            "- A useful calibration gate should improve precision or false-positive count without collapsing matched target coverage.",
            "- If the selected config mainly trades recall for precision, the next step should not scale to paper tables before a visibility-aware denominator or better detector prompts/NMS.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M23 diagnostic.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m22-dir", default=DEFAULT_M22_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    parser.add_argument(
        "--selection-policy",
        choices=["balanced_f1", "full_match_preserving", "near_match_preserving"],
        default="balanced_f1",
    )
    args = parser.parse_args()

    proposals = load_jsonl(args.m22_dir / "container_output" / "real_proposals.jsonl")
    targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    evaluated_scans = sorted({str(row["scan_id"]) for row in proposals})
    baseline_labels = sorted({str(row["label_canonical"]) for row in proposals})
    eval_targets = [
        row
        for row in targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]
    fixed_label_overlap_targets = [row for row in eval_targets if str(row["label_canonical"]) in baseline_labels]

    confidence_thresholds = [0.0, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    min_depth_thresholds = [0, 100, 250, 500, 1000, 2000]
    nms_radii = [0.0, 0.25, 0.50, 0.75, 1.00, 1.50]
    score_modes = ["confidence", "confidence_log_depth", "confidence_sqrt_depth"]

    baseline_row, baseline_retained, baseline_matched, baseline_targets = evaluate_config(
        proposals=proposals,
        eval_targets=eval_targets,
        fixed_label_overlap_targets=fixed_label_overlap_targets,
        confidence_threshold=0.0,
        min_depth_pixels=0,
        nms_radius_m=0.0,
        score_mode="confidence",
        match_threshold_m=args.match_distance_threshold_m,
    )

    sweep_rows: list[dict[str, Any]] = []
    artifacts_by_key: dict[tuple[float, int, float, str], tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for confidence_threshold in confidence_thresholds:
        for min_depth_pixels in min_depth_thresholds:
            for nms_radius_m in nms_radii:
                for score_mode in score_modes:
                    row, retained, matched, target_rows = evaluate_config(
                        proposals=proposals,
                        eval_targets=eval_targets,
                        fixed_label_overlap_targets=fixed_label_overlap_targets,
                        confidence_threshold=confidence_threshold,
                        min_depth_pixels=min_depth_pixels,
                        nms_radius_m=nms_radius_m,
                        score_mode=score_mode,
                        match_threshold_m=args.match_distance_threshold_m,
                    )
                    sweep_rows.append(row)
                    artifacts_by_key[(confidence_threshold, min_depth_pixels, nms_radius_m, score_mode)] = (
                        retained,
                        matched,
                        target_rows,
                    )

    full_match_preserving = best_with_min_matched(sweep_rows, int(baseline_row["matched_target_rows"]))
    near_match_preserving = best_with_min_matched(sweep_rows, max(1, int(baseline_row["matched_target_rows"]) - 1))
    if args.selection_policy == "full_match_preserving" and full_match_preserving:
        selected = full_match_preserving
    elif args.selection_policy == "near_match_preserving" and near_match_preserving:
        selected = near_match_preserving
    else:
        selected = select_config(sweep_rows, baseline_row)
    selected_key = (
        float(selected["confidence_threshold"]),
        int(selected["min_depth_pixels"]),
        float(selected["nms_radius_m"]),
        str(selected["score_mode"]),
    )
    selected_retained, selected_matched, selected_targets = artifacts_by_key[selected_key]
    selected_label_metrics = build_label_metrics(selected_targets, selected_matched)
    selected_matches = [row for row in selected_matched if row["match_status"] == "matched"]

    status = "proposal_calibration_diagnostic_ready"
    if not proposals:
        status = "proposal_calibration_no_input"
    elif not selected_retained:
        status = "proposal_calibration_selected_empty"

    coverage = {
        "baseline_config": baseline_row,
        "baseline_false_positive_delta": selected["false_positive_proposal_rows"] - baseline_row["false_positive_proposal_rows"],
        "baseline_matched_target_delta": selected["matched_target_rows"] - baseline_row["matched_target_rows"],
        "baseline_precision_delta": (
            selected["proposal_precision"] - baseline_row["proposal_precision"]
            if selected["proposal_precision"] is not None and baseline_row["proposal_precision"] is not None
            else None
        ),
        "confidence_summary_input": summarize_confidence(proposals),
        "confidence_summary_selected": summarize_confidence(selected_retained),
        "evaluated_scan_count": len(evaluated_scans),
        "evaluated_scans": evaluated_scans,
        "fixed_label_overlap_target_rows": len(fixed_label_overlap_targets),
        "full_match_preserving_config": full_match_preserving,
        "input_proposal_rows": len(proposals),
        "m23_version": M23_VERSION,
        "near_match_preserving_config": near_match_preserving,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "selected_config": selected,
        "selected_label_metrics_rows": len(selected_label_metrics),
        "selected_match_labels": dict(Counter(row["label_canonical"] for row in selected_matches)),
        "selection_policy": args.selection_policy,
        "status": status,
        "sweep_rows": len(sweep_rows),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "sweep_rows.jsonl", sweep_rows)
    write_jsonl(args.out_dir / "selected_proposals.jsonl", selected_retained)
    write_jsonl(args.out_dir / "selected_matched_proposals.jsonl", selected_matched)
    write_jsonl(args.out_dir / "selected_target_recall_rows.jsonl", selected_targets)
    write_jsonl(args.out_dir / "selected_label_metrics.jsonl", selected_label_metrics)
    write_json(args.out_dir / "selected_config.json", selected)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0 if status == "proposal_calibration_diagnostic_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
