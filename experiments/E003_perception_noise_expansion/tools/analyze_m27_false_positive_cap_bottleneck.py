#!/usr/bin/env python3
"""Analyze E003-M26 false-positive and cap bottlenecks for the next detector policy."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M26_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M26_prompt_expanded_multiscan_docker_rerun_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M27_false_positive_cap_bottleneck_v0"
M27_VERSION = "e003_m27_false_positive_cap_bottleneck_v0"
FALSE_POSITIVE_STATUSES = {"unmatched_false_positive", "unmatched_no_same_label_target"}


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


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def numeric_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"max": None, "mean": None, "median": None, "min": None}
    return {
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
    }


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "None"
    return str(value)


def build_frame_cap_rows(frame_rows: list[dict[str, Any]], max_predictions_per_frame: int) -> list[dict[str, Any]]:
    rows = []
    for row in frame_rows:
        raw = int(row.get("raw_prediction_count", 0) or 0)
        skipped = int(row.get("skipped_no_depth_prediction_count", 0) or 0)
        written = int(row.get("written_prediction_count", 0) or 0)
        after_depth = max(0, raw - skipped)
        cap_or_post_depth_rejected = max(0, after_depth - written)
        rows.append(
            {
                "cap_or_post_depth_rejected_rows": cap_or_post_depth_rejected,
                "cap_pressure_rate": safe_rate(cap_or_post_depth_rejected, after_depth),
                "frame_id": str(row.get("frame_id")),
                "label_count": int(row.get("label_count", 0) or 0),
                "raw_prediction_count": raw,
                "scan_id": str(row.get("scan_id")),
                "skipped_no_depth_prediction_count": skipped,
                "saturated_by_per_frame_cap": written >= max_predictions_per_frame and after_depth > written,
                "written_prediction_count": written,
            }
        )
    return rows


def summarize_match_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in rows if row.get("match_status") == "matched"]
    false_positive = [row for row in rows if row.get("match_status") in FALSE_POSITIVE_STATUSES]
    no_same_label = [row for row in rows if row.get("match_status") == "unmatched_no_same_label_target"]
    same_label_over_threshold = [row for row in rows if row.get("match_status") == "unmatched_false_positive"]
    return {
        "confidence_by_matched": numeric_summary([float(row.get("confidence", 0.0) or 0.0) for row in matched]),
        "confidence_by_false_positive": numeric_summary(
            [float(row.get("confidence", 0.0) or 0.0) for row in false_positive]
        ),
        "depth_pixels_by_matched": numeric_summary([float(row.get("depth_valid_pixel_count", 0) or 0) for row in matched]),
        "depth_pixels_by_false_positive": numeric_summary(
            [float(row.get("depth_valid_pixel_count", 0) or 0) for row in false_positive]
        ),
        "false_positive_proposal_rate": safe_rate(len(false_positive), len(rows)),
        "false_positive_proposal_rows": len(false_positive),
        "matched_proposal_rows": len(matched),
        "no_same_label_false_positive_rows": len(no_same_label),
        "proposal_precision": safe_rate(len(matched), len(rows)),
        "proposal_rows": len(rows),
        "same_label_over_threshold_false_positive_rows": len(same_label_over_threshold),
    }


def build_label_rows(
    baseline_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    baseline_label_metrics: list[dict[str, Any]],
    selected_label_metrics: list[dict[str, Any]],
    visibility_label_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    label_metrics = {str(row["label_canonical"]): row for row in baseline_label_metrics}
    selected_metrics = {str(row["label_canonical"]): row for row in selected_label_metrics}
    visibility_metrics = {str(row["label_canonical"]): row for row in visibility_label_rows}
    labels = sorted(
        set(label_metrics)
        | set(selected_metrics)
        | {str(row.get("label_canonical")) for row in baseline_rows}
        | {str(row.get("label_canonical")) for row in selected_rows}
    )
    baseline_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    selected_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in baseline_rows:
        baseline_by_label[str(row.get("label_canonical"))].append(row)
    for row in selected_rows:
        selected_by_label[str(row.get("label_canonical"))].append(row)

    rows = []
    for label in labels:
        baseline_group = baseline_by_label.get(label, [])
        selected_group = selected_by_label.get(label, [])
        baseline_fp = [row for row in baseline_group if row.get("match_status") in FALSE_POSITIVE_STATUSES]
        selected_fp = [row for row in selected_group if row.get("match_status") in FALSE_POSITIVE_STATUSES]
        baseline_matched = [row for row in baseline_group if row.get("match_status") == "matched"]
        selected_matched = [row for row in selected_group if row.get("match_status") == "matched"]
        metric = label_metrics.get(label, {})
        selected_metric = selected_metrics.get(label, {})
        visibility = visibility_metrics.get(label, {})
        bottleneck_counts = visibility.get("bottleneck_counts", {})
        rows.append(
            {
                "active_prompt_target_rows": visibility.get("active_prompt_target_rows", 0),
                "baseline_false_positive_rows": len(baseline_fp),
                "baseline_matched_rows": len(baseline_matched),
                "baseline_precision": safe_rate(len(baseline_matched), len(baseline_group)),
                "baseline_proposal_rows": len(baseline_group),
                "bottleneck_counts": bottleneck_counts,
                "depth_consistent_visible_rows": visibility.get("depth_consistent_visible_rows", 0),
                "detector_or_threshold_missed_visible_target_rows": int(
                    bottleneck_counts.get("detector_or_threshold_missed_visible_target", 0) or 0
                ),
                "evaluation_target_rows": visibility.get("evaluation_target_rows", metric.get("target_rows", 0)),
                "false_positive_share_of_selected": safe_rate(len(selected_fp), len(selected_rows)),
                "label_canonical": label,
                "no_target_label_with_predictions": int(metric.get("target_rows", 0) or 0) == 0
                and len(baseline_group) > 0,
                "selected_false_positive_rows": len(selected_fp),
                "selected_matched_rows": len(selected_matched),
                "selected_precision": safe_rate(len(selected_matched), len(selected_group)),
                "selected_proposal_rows": len(selected_group),
                "selected_target_recall": selected_metric.get("target_recall"),
                "target_rows": metric.get("target_rows", 0),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -int(row["selected_false_positive_rows"]),
            -int(row["baseline_false_positive_rows"]),
            str(row["label_canonical"]),
        ),
    )


def aggregate_bottleneck_counts(visibility_label_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in visibility_label_rows:
        counts.update({str(key): int(value) for key, value in row.get("bottleneck_counts", {}).items()})
    return dict(sorted(counts.items()))


def build_policy_decision(coverage: dict[str, Any], label_rows: list[dict[str, Any]]) -> dict[str, Any]:
    no_target_rows = [row for row in label_rows if row["no_target_label_with_predictions"]]
    high_fp_labels = [
        row["label_canonical"]
        for row in label_rows
        if int(row["selected_false_positive_rows"]) >= 25 and int(row["selected_matched_rows"]) == 0
    ][:10]
    return {
        "do_not_scale_to_paper_table": True,
        "next_policy_id": "cap_aware_label_balanced_ranking_v0",
        "next_recommended_unit": "E003-M28 cap-aware label-balanced detector policy smoke",
        "policy_requirements": [
            "filter output labels not mapped to the prompt-set canonical labels",
            "rank before the per-frame/global cap using confidence and depth support",
            "use per-label or label-balanced caps so high-volume labels do not dominate written proposals",
            "apply same-label spatial consolidation before evaluating wider scan scaling",
            "keep match-preserving recall constraints during calibration",
        ],
        "rejected_next_steps": [
            {
                "reason": "all sampled frames already saturate the per-frame cap and false-positive rate is above 0.9",
                "step": "wider scan/frame scaling immediately",
            },
            {
                "reason": "M26 selected calibration reduces only 92 false positives while preserving 39 matches",
                "step": "threshold/depth/NMS-only calibration as final policy",
            },
            {
                "reason": "raising caps will likely increase false positives unless ranking is fixed first",
                "step": "increase max_predictions as the first response",
            },
        ],
        "supporting_facts": {
            "frames_saturated_by_per_frame_cap": coverage["frames_saturated_by_per_frame_cap"],
            "no_target_label_count_with_predictions": len(no_target_rows),
            "selected_false_positive_rate": coverage["selected_false_positive_rate"],
            "selected_precision": coverage["selected_precision"],
            "top_high_fp_zero_match_labels": high_fp_labels,
            "written_prediction_rows": coverage["written_prediction_rows"],
        },
    }


def build_report(coverage: dict[str, Any], policy_decision: dict[str, Any]) -> str:
    top_fp = coverage["top_selected_false_positive_labels"][:8]
    top_fp_text = ", ".join(f"{row['label_canonical']}={row['selected_false_positive_rows']}" for row in top_fp)
    return "\n".join(
        [
            "# E003-M27 False Positive Cap Bottleneck",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Input unit: `E003-M26_prompt_expanded_multiscan_docker_rerun_v0`",
            f"- Evaluated scans / frames: {coverage['evaluated_scan_count']} / {coverage['evaluated_frame_count']}",
            f"- Raw / written predictions: {coverage['raw_prediction_rows']} / {coverage['written_prediction_rows']}",
            f"- Skipped no-depth predictions: {coverage['skipped_no_depth_prediction_rows']}",
            f"- Lower-bound cap/post-depth rejected rows: {coverage['lower_bound_cap_or_post_depth_rejected_rows']}",
            f"- Frames saturated by per-frame cap: {coverage['frames_saturated_by_per_frame_cap']} / {coverage['evaluated_frame_count']}",
            f"- Baseline proposal precision: {fmt(coverage['baseline_precision'])}",
            f"- Selected match-preserving precision: {fmt(coverage['selected_precision'])}",
            f"- Baseline / selected matched target rows: {coverage['baseline_matched_rows']} / {coverage['selected_matched_rows']}",
            f"- Baseline / selected false-positive rows: {coverage['baseline_false_positive_rows']} / {coverage['selected_false_positive_rows']}",
            f"- Calibration false-positive reduction: {coverage['calibration_false_positive_reduction_rows']}",
            f"- Same-label over-threshold false-positive rows after selected calibration: {coverage['selected_same_label_over_threshold_false_positive_rows']}",
            f"- No-same-label false-positive rows after selected calibration: {coverage['selected_no_same_label_false_positive_rows']}",
            f"- No-target labels with detector predictions: {coverage['no_target_label_count_with_predictions']}",
            f"- Top selected false-positive labels: {top_fp_text}",
            f"- Visibility bottleneck counts: {coverage['visibility_bottleneck_counts']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M27 supports a diagnostic claim that the current real-detector pilot is blocked by cap pressure and false-positive domination, not by prompt coverage.",
            "- E003-M27 does not support real RGB-D/open-vocabulary robustness or a paper-table detector benchmark result.",
            "",
            "## 에이전트 추론",
            "",
            "- Wider scaling should wait because every sampled frame saturates the per-frame cap and selected precision remains near 0.03.",
            "- Threshold/depth/NMS calibration alone is insufficient because it preserves recall but barely changes precision.",
            f"- Next detector policy should be `{policy_decision['next_policy_id']}`: label mapping cleanup, pre-cap ranking, label-balanced caps, and same-label spatial consolidation.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M27. Next recommended unit: `{policy_decision['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m26-dir", default=DEFAULT_M26_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    detector_coverage = load_json(args.m26_dir / "detector_rerun" / "coverage.json")
    calibration_coverage = load_json(args.m26_dir / "match_preserving_calibration" / "coverage.json")
    visibility_coverage = load_json(args.m26_dir / "visibility_denominator" / "coverage.json")
    frame_rows = load_jsonl(args.m26_dir / "detector_rerun" / "frame_diagnostics.jsonl")
    baseline_rows = load_jsonl(args.m26_dir / "detector_rerun" / "matching" / "matched_proposals.jsonl")
    baseline_label_metrics = load_jsonl(args.m26_dir / "detector_rerun" / "matching" / "label_metrics.jsonl")
    selected_rows = load_jsonl(args.m26_dir / "match_preserving_calibration" / "selected_matched_proposals.jsonl")
    selected_label_metrics = load_jsonl(args.m26_dir / "match_preserving_calibration" / "selected_label_metrics.jsonl")
    visibility_label_rows = load_jsonl(args.m26_dir / "visibility_denominator" / "label_bottleneck_rows.jsonl")

    max_predictions_per_frame = int(detector_coverage.get("run_config", {}).get("max_predictions_per_frame", 0) or 0)
    cap_rows = build_frame_cap_rows(frame_rows, max_predictions_per_frame)
    label_rows = build_label_rows(
        baseline_rows=baseline_rows,
        selected_rows=selected_rows,
        baseline_label_metrics=baseline_label_metrics,
        selected_label_metrics=selected_label_metrics,
        visibility_label_rows=visibility_label_rows,
    )
    baseline_summary = summarize_match_rows(baseline_rows)
    selected_summary = summarize_match_rows(selected_rows)
    visibility_counts = aggregate_bottleneck_counts(visibility_label_rows)

    saturated_frames = sum(1 for row in cap_rows if row["saturated_by_per_frame_cap"])
    lower_bound_cap_rejected = sum(int(row["cap_or_post_depth_rejected_rows"]) for row in cap_rows)
    no_target_label_count = sum(1 for row in label_rows if row["no_target_label_with_predictions"])
    top_selected_fp = sorted(label_rows, key=lambda row: -int(row["selected_false_positive_rows"]))[:12]

    coverage: dict[str, Any] = {
        "baseline_false_positive_rate": baseline_summary["false_positive_proposal_rate"],
        "baseline_false_positive_rows": baseline_summary["false_positive_proposal_rows"],
        "baseline_matched_rows": baseline_summary["matched_proposal_rows"],
        "baseline_precision": baseline_summary["proposal_precision"],
        "baseline_proposal_rows": baseline_summary["proposal_rows"],
        "calibration_false_positive_reduction_rows": int(baseline_summary["false_positive_proposal_rows"])
        - int(selected_summary["false_positive_proposal_rows"]),
        "calibration_matched_delta_rows": int(selected_summary["matched_proposal_rows"])
        - int(baseline_summary["matched_proposal_rows"]),
        "evaluated_frame_count": visibility_coverage.get("evaluated_frame_count"),
        "evaluated_scan_count": visibility_coverage.get("evaluated_scan_count"),
        "frame_cap_pressure_rate": safe_rate(lower_bound_cap_rejected, sum(int(row["raw_prediction_count"]) for row in cap_rows)),
        "frames_saturated_by_per_frame_cap": saturated_frames,
        "lower_bound_cap_or_post_depth_rejected_rows": lower_bound_cap_rejected,
        "m27_version": M27_VERSION,
        "max_predictions_reached": detector_coverage.get("model_status", {}).get("max_predictions_reached"),
        "no_target_label_count_with_predictions": no_target_label_count,
        "paper_table_command_ready": False,
        "raw_prediction_rows": sum(int(row["raw_prediction_count"]) for row in cap_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "selected_false_positive_rate": selected_summary["false_positive_proposal_rate"],
        "selected_false_positive_rows": selected_summary["false_positive_proposal_rows"],
        "selected_matched_rows": selected_summary["matched_proposal_rows"],
        "selected_no_same_label_false_positive_rows": selected_summary["no_same_label_false_positive_rows"],
        "selected_precision": selected_summary["proposal_precision"],
        "selected_proposal_rows": selected_summary["proposal_rows"],
        "selected_same_label_over_threshold_false_positive_rows": selected_summary[
            "same_label_over_threshold_false_positive_rows"
        ],
        "skipped_no_depth_prediction_rows": sum(int(row["skipped_no_depth_prediction_count"]) for row in cap_rows),
        "status": "false_positive_cap_bottleneck_ready",
        "top_selected_false_positive_labels": top_selected_fp,
        "visibility_bottleneck_counts": visibility_counts,
        "written_prediction_rows": sum(int(row["written_prediction_count"]) for row in cap_rows),
    }
    coverage["confidence_depth_summary"] = {
        "baseline": baseline_summary,
        "selected_match_preserving": selected_summary,
    }
    coverage["dominant_blockers"] = [
        "per_frame_and_global_prediction_cap_saturated",
        "same_label_over_threshold_false_positive_domination",
        "match_preserving_calibration_insufficient",
    ]
    policy_decision = build_policy_decision(coverage, label_rows)
    coverage["next_policy_id"] = policy_decision["next_policy_id"]
    coverage["next_recommended_unit"] = policy_decision["next_recommended_unit"]

    write_jsonl(args.out_dir / "frame_cap_rows.jsonl", cap_rows)
    write_jsonl(args.out_dir / "false_positive_label_rows.jsonl", label_rows)
    write_json(args.out_dir / "policy_decision.json", policy_decision)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, policy_decision), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
