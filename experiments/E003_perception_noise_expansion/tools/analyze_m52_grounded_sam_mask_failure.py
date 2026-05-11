#!/usr/bin/env python3
"""Analyze why the E003-M49 Grounded-SAM mask route failed M50."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M49_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M49_grounded_sam_smoke_v0"
DEFAULT_M50_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M50_same_subset_bbox_vs_mask_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M52_grounded_sam_mask_failure_v0"
M52_VERSION = "e003_m52_grounded_sam_mask_failure_v0"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def distance_m(a: list[float] | None, b: list[float] | None) -> float | None:
    if not a or not b:
        return None
    if len(a) != len(b):
        return None
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def frame_id(row: dict[str, Any]) -> str:
    frame_ids = row.get("frame_ids") or []
    if frame_ids:
        return str(frame_ids[0])
    bbox = row.get("bbox_2d") or {}
    if bbox:
        return str(sorted(bbox)[0])
    return "unknown"


def candidate_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(row.get("scan_id")),
        frame_id(row),
        int(row.get("raw_frame_local_index")),
    )


def target_key(row: dict[str, Any]) -> str:
    return str(row.get("target_uid"))


def compact_proposal(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "bbox_2d": row.get("bbox_2d"),
        "centroid_world_m": row.get("centroid_world_m"),
        "confidence": row.get("confidence"),
        "depth_valid_pixel_count": row.get("depth_valid_pixel_count"),
        "frame_id": frame_id(row),
        "label_canonical": row.get("label_canonical"),
        "match_distance_m": row.get("match_distance_m"),
        "match_status": row.get("match_status"),
        "matched_target_uid": row.get("matched_target_uid"),
        "nearest_same_label_distance_m": row.get("nearest_same_label_distance_m"),
        "nearest_same_label_target_uid": row.get("nearest_same_label_target_uid"),
        "proposal_uid": row.get("proposal_uid"),
        "raw_frame_local_index": row.get("raw_frame_local_index"),
        "scan_id": row.get("scan_id"),
    }


def build_candidate_rows(
    bbox_rows: list[dict[str, Any]],
    mask_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bbox_by_key = {candidate_key(row): row for row in bbox_rows}
    mask_by_key = {candidate_key(row): row for row in mask_rows}
    all_keys = sorted(set(bbox_by_key) | set(mask_by_key))
    rows: list[dict[str, Any]] = []
    common_same_target_deltas = []
    common_centroid_shifts = []
    common_bbox_diag_shifts = []
    bbox_matched_mask_missing = 0
    bbox_matched_mask_common_unmatched = 0
    label_mismatch_count = 0

    for key in all_keys:
        bbox = bbox_by_key.get(key)
        mask = mask_by_key.get(key)
        status = "common"
        if bbox and not mask:
            status = "bbox_only"
        elif mask and not bbox:
            status = "mask_only"

        bbox_match_distance = bbox.get("match_distance_m") if bbox else None
        mask_match_distance = mask.get("match_distance_m") if mask else None
        bbox_target = bbox.get("matched_target_uid") if bbox else None
        mask_target = mask.get("matched_target_uid") if mask else None
        same_matched_target = bool(bbox_target and mask_target and bbox_target == mask_target)
        match_distance_delta = None
        if same_matched_target and bbox_match_distance is not None and mask_match_distance is not None:
            match_distance_delta = round(float(mask_match_distance) - float(bbox_match_distance), 6)
            common_same_target_deltas.append(float(match_distance_delta))

        centroid_shift = None
        if bbox and mask:
            centroid_shift = distance_m(bbox.get("centroid_world_m"), mask.get("centroid_world_m"))
            if centroid_shift is not None:
                common_centroid_shifts.append(centroid_shift)
            if bbox.get("label_canonical") != mask.get("label_canonical"):
                label_mismatch_count += 1
        bbox_diag_shift = None
        if mask:
            bbox_diag_shift = distance_m(mask.get("bbox_centroid_world_m"), mask.get("centroid_world_m"))
            if bbox_diag_shift is not None:
                common_bbox_diag_shifts.append(bbox_diag_shift)

        if bbox and bbox.get("match_status") == "matched" and not mask:
            bbox_matched_mask_missing += 1
        if bbox and mask and bbox.get("match_status") == "matched" and mask.get("match_status") != "matched":
            bbox_matched_mask_common_unmatched += 1

        rows.append(
            {
                "bbox": compact_proposal(bbox) if bbox else None,
                "bbox_match_distance_m": bbox_match_distance,
                "bbox_matched_target_uid": bbox_target,
                "candidate_key": {
                    "frame_id": key[1],
                    "raw_frame_local_index": key[2],
                    "scan_id": key[0],
                },
                "common_bbox_to_mask_centroid_shift_m": round(centroid_shift, 6) if centroid_shift is not None else None,
                "label_mismatch": bool(bbox and mask and bbox.get("label_canonical") != mask.get("label_canonical")),
                "mask": compact_proposal(mask) if mask else None,
                "mask_bbox_diagnostic_to_mask_centroid_shift_m": (
                    round(bbox_diag_shift, 6) if bbox_diag_shift is not None else None
                ),
                "mask_match_distance_m": mask_match_distance,
                "mask_matched_target_uid": mask_target,
                "match_distance_delta_mask_minus_bbox_m": match_distance_delta,
                "same_matched_target": same_matched_target,
                "status": status,
            }
        )

    common = sum(1 for row in rows if row["status"] == "common")
    bbox_only = sum(1 for row in rows if row["status"] == "bbox_only")
    mask_only = sum(1 for row in rows if row["status"] == "mask_only")
    summary = {
        "bbox_matched_mask_common_unmatched": bbox_matched_mask_common_unmatched,
        "bbox_matched_mask_missing": bbox_matched_mask_missing,
        "bbox_only_candidate_rows": bbox_only,
        "candidate_pairing_rows": len(rows),
        "common_bbox_to_mask_centroid_shift_m": numeric_summary(common_centroid_shifts),
        "common_candidate_rows": common,
        "common_same_target_match_distance_delta_mask_minus_bbox_m": numeric_summary(common_same_target_deltas),
        "label_mismatch_count": label_mismatch_count,
        "mask_bbox_diagnostic_to_mask_centroid_shift_m": numeric_summary(common_bbox_diag_shifts),
        "mask_only_candidate_rows": mask_only,
    }
    return rows, summary


def build_target_rows(
    bbox_targets: list[dict[str, Any]],
    mask_targets: list[dict[str, Any]],
    bbox_proposals_by_uid: dict[str, dict[str, Any]],
    mask_proposals_by_uid: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bbox_by_target = {target_key(row): row for row in bbox_targets}
    mask_by_target = {target_key(row): row for row in mask_targets}
    rows: list[dict[str, Any]] = []
    for uid in sorted(set(bbox_by_target) | set(mask_by_target)):
        bbox = bbox_by_target.get(uid)
        mask = mask_by_target.get(uid)
        bbox_prop = bbox_proposals_by_uid.get(str(bbox.get("best_proposal_uid"))) if bbox else None
        mask_prop = mask_proposals_by_uid.get(str(mask.get("best_proposal_uid"))) if mask else None
        bbox_candidate_key = candidate_key(bbox_prop) if bbox_prop else None
        mask_candidate_key = candidate_key(mask_prop) if mask_prop else None
        if bbox and bbox.get("matched") and mask and mask.get("matched"):
            transition = "matched_by_both"
        elif bbox and bbox.get("matched") and (not mask or not mask.get("matched")):
            transition = "lost_by_mask"
        elif mask and mask.get("matched") and (not bbox or not bbox.get("matched")):
            transition = "gained_by_mask"
        else:
            transition = "missed_by_both"
        rows.append(
            {
                "bbox_best_match_distance_m": bbox.get("best_match_distance_m") if bbox else None,
                "bbox_best_proposal_uid": bbox.get("best_proposal_uid") if bbox else None,
                "bbox_candidate_key": (
                    {
                        "frame_id": bbox_candidate_key[1],
                        "raw_frame_local_index": bbox_candidate_key[2],
                        "scan_id": bbox_candidate_key[0],
                    }
                    if bbox_candidate_key
                    else None
                ),
                "bbox_matched": bool(bbox and bbox.get("matched")),
                "label_canonical": (bbox or mask).get("label_canonical"),
                "mask_best_match_distance_m": mask.get("best_match_distance_m") if mask else None,
                "mask_best_proposal_uid": mask.get("best_proposal_uid") if mask else None,
                "mask_candidate_key": (
                    {
                        "frame_id": mask_candidate_key[1],
                        "raw_frame_local_index": mask_candidate_key[2],
                        "scan_id": mask_candidate_key[0],
                    }
                    if mask_candidate_key
                    else None
                ),
                "mask_matched": bool(mask and mask.get("matched")),
                "object_instance_id": (bbox or mask).get("object_instance_id"),
                "scan_id": (bbox or mask).get("scan_id"),
                "target_uid": uid,
                "transition": transition,
            }
        )
    lost = [row for row in rows if row["transition"] == "lost_by_mask"]
    gained = [row for row in rows if row["transition"] == "gained_by_mask"]
    both = [row for row in rows if row["transition"] == "matched_by_both"]
    summary = {
        "gained_by_mask_targets": len(gained),
        "lost_by_mask_labels": dict(Counter(row["label_canonical"] for row in lost)),
        "lost_by_mask_targets": len(lost),
        "matched_by_both_targets": len(both),
        "missed_by_both_targets": sum(1 for row in rows if row["transition"] == "missed_by_both"),
        "target_rows": len(rows),
    }
    return rows, summary


def build_diagnosis(
    m49_model: dict[str, Any],
    m50_coverage: dict[str, Any],
    candidate_summary: dict[str, Any],
    target_summary: dict[str, Any],
) -> dict[str, Any]:
    aggregate_delta = (m50_coverage.get("comparison") or {}).get("delta_mask_minus_bbox") or {}
    common_delta_mean = (
        candidate_summary.get("common_same_target_match_distance_delta_mask_minus_bbox_m") or {}
    ).get("mean")
    lost_targets = int(target_summary["lost_by_mask_targets"])
    bbox_matched_mask_missing = int(candidate_summary["bbox_matched_mask_missing"])
    skipped_mask_projection = int(m49_model.get("skipped_mask_projection_count") or 0)

    target_loss_primary_cause = "not_determined"
    if lost_targets and bbox_matched_mask_missing == lost_targets:
        target_loss_primary_cause = "mask_projection_candidate_dropout_before_matching"
    elif lost_targets:
        target_loss_primary_cause = "mask_geometry_or_ranking_match_loss"

    centroid_worsening_primary_cause = "not_determined"
    if (
        aggregate_delta.get("matched_centroid_error_mean_m") is not None
        and float(aggregate_delta["matched_centroid_error_mean_m"]) > 0
        and common_delta_mean is not None
        and float(common_delta_mean) <= 0
    ):
        centroid_worsening_primary_cause = "match_set_composition_after_easy_target_dropout"
    elif aggregate_delta.get("matched_centroid_error_mean_m") is not None:
        centroid_worsening_primary_cause = "common_mask_centroid_shift_or_match_loss"

    false_positive_interpretation = "not_determined"
    if (
        aggregate_delta.get("false_positive_proposal_rows") is not None
        and aggregate_delta.get("input_prediction_rows") is not None
        and float(aggregate_delta["false_positive_proposal_rows"]) < 0
        and float(aggregate_delta["input_prediction_rows"]) < 0
        and aggregate_delta.get("proposal_precision_smoke") is not None
        and float(aggregate_delta["proposal_precision_smoke"]) < 0
    ):
        false_positive_interpretation = "fewer_rows_without_precision_gain"

    exact_skip_reason_observable = False
    return {
        "centroid_worsening_primary_cause": centroid_worsening_primary_cause,
        "exact_mask_skip_reason_observable_from_current_artifacts": exact_skip_reason_observable,
        "false_positive_interpretation": false_positive_interpretation,
        "mask_projection_skipped_rows": skipped_mask_projection,
        "next_recommended_unit": "E003-M53 bbox-depth continuation and failure-boundary repair gate",
        "openmask3d_feasibility_next_now": False,
        "scaled_grounded_sam_recommended": False,
        "target_loss_primary_cause": target_loss_primary_cause,
    }


def build_report(coverage: dict[str, Any]) -> str:
    c = coverage["candidate_pairing_summary"]
    t = coverage["target_transition_summary"]
    d = coverage["diagnosis"]
    m50 = coverage["m50_summary"]
    lines = [
        "# E003-M52 Grounded-SAM Mask Failure Analysis",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Bbox-depth proposal rows: {m50['bbox_prediction_rows']}.",
        f"- Mask-depth proposal rows: {m50['mask_prediction_rows']}.",
        f"- Common candidate rows by scan/frame/raw index: {c['common_candidate_rows']}.",
        f"- Bbox-only candidate rows: {c['bbox_only_candidate_rows']}.",
        f"- Mask-only candidate rows: {c['mask_only_candidate_rows']}.",
        f"- `Grounded-SAM` skipped mask projection rows: {d['mask_projection_skipped_rows']}.",
        f"- Bbox matched targets: {m50['bbox_matched_target_rows']}.",
        f"- Mask matched targets: {m50['mask_matched_target_rows']}.",
        f"- Lost-by-mask targets: {t['lost_by_mask_targets']}, labels {t['lost_by_mask_labels']}.",
        f"- Matched-by-both targets: {t['matched_by_both_targets']}.",
        f"- Common same-target match-distance delta mask minus bbox: {c['common_same_target_match_distance_delta_mask_minus_bbox_m']}.",
        f"- Aggregate M50 mean centroid error delta mask minus bbox: {m50['aggregate_centroid_error_delta_mask_minus_bbox_m']}.",
        f"- Exact per-skipped mask reason observable from current artifacts: {d['exact_mask_skip_reason_observable_from_current_artifacts']}.",
        "",
        "## 논문 주장",
        "",
        "- E003-M52 does not create a final paper claim.",
        "- E003-M52 supports a route decision: the current `Grounded-SAM` mask-depth path should not be scaled as-is.",
        "- Real RGB-D/open-vocabulary robustness remains unsupported.",
        "",
        "## 에이전트 추론",
        "",
        f"- Target loss primary cause: `{d['target_loss_primary_cause']}`.",
        f"- Centroid worsening primary cause: `{d['centroid_worsening_primary_cause']}`.",
        f"- False-positive interpretation: `{d['false_positive_interpretation']}`.",
        "- The M50 centroid degradation is not evidence that the common matched target became worse under mask-depth; the common matched target is slightly better under mask-depth, but the easy bbox-depth `plant` match was dropped before matching.",
        "- Because the exact skipped-mask reason is not recorded, the current artifact can defend stopping the scaled `Grounded-SAM` route but cannot prove whether the failure is SAM mask absence, low valid mask depth, or another per-candidate projection condition.",
        f"- Next recommended unit: `{d['next_recommended_unit']}`.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None if bbox-depth continuation is accepted as the next immediate route. `OpenMask3D` remains the next external 3D instance baseline candidate after the current bbox-depth route is stabilized.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m49-dir", default=DEFAULT_M49_DIR, type=Path)
    parser.add_argument("--m50-dir", default=DEFAULT_M50_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m49_dir = args.m49_dir.resolve()
    m50_dir = args.m50_dir.resolve()
    out_dir = args.out_dir.resolve()

    m49_model = load_json(m49_dir / "container_output" / "model_smoke.json")
    m49_matching = load_json(m49_dir / "matching" / "coverage.json")
    m50_coverage = load_json(m50_dir / "coverage.json")
    bbox_matching = load_json(m50_dir / "bbox_depth_baseline" / "matching" / "coverage.json")

    bbox_rows = load_jsonl(m50_dir / "bbox_depth_baseline" / "matching" / "matched_proposals.jsonl")
    mask_rows = load_jsonl(m49_dir / "matching" / "matched_proposals.jsonl")
    bbox_target_rows = load_jsonl(m50_dir / "bbox_depth_baseline" / "matching" / "target_recall_rows.jsonl")
    mask_target_rows = load_jsonl(m49_dir / "matching" / "target_recall_rows.jsonl")
    bbox_proposals_by_uid = {str(row.get("proposal_uid")): row for row in bbox_rows}
    mask_proposals_by_uid = {str(row.get("proposal_uid")): row for row in mask_rows}

    candidate_rows, candidate_summary = build_candidate_rows(bbox_rows=bbox_rows, mask_rows=mask_rows)
    target_rows, target_summary = build_target_rows(
        bbox_targets=bbox_target_rows,
        mask_targets=mask_target_rows,
        bbox_proposals_by_uid=bbox_proposals_by_uid,
        mask_proposals_by_uid=mask_proposals_by_uid,
    )
    diagnosis = build_diagnosis(
        m49_model=m49_model,
        m50_coverage=m50_coverage,
        candidate_summary=candidate_summary,
        target_summary=target_summary,
    )

    bbox_metrics = m50_coverage["bbox_depth_metrics"]
    mask_metrics = m50_coverage["mask_depth_metrics"]
    aggregate_delta = (m50_coverage.get("comparison") or {}).get("delta_mask_minus_bbox") or {}
    coverage = {
        "candidate_pairing_summary": candidate_summary,
        "diagnosis": diagnosis,
        "m49_mask_model_summary": {
            "inference_rows": m49_model.get("inference_rows"),
            "mask_depth_filter": m49_model.get("mask_depth_filter"),
            "mask_min_depth_valid_pixels": m49_model.get("mask_min_depth_valid_pixels"),
            "mask_point_sample_cap": m49_model.get("mask_point_sample_cap"),
            "mask_projected_candidate_count": m49_model.get("mask_projected_candidate_count"),
            "prediction_rows": m49_model.get("prediction_rows"),
            "skipped_mask_projection_count": m49_model.get("skipped_mask_projection_count"),
        },
        "m50_summary": {
            "aggregate_centroid_error_delta_mask_minus_bbox_m": aggregate_delta.get("matched_centroid_error_mean_m"),
            "bbox_false_positive_rows": bbox_metrics.get("false_positive_proposal_rows"),
            "bbox_matched_target_rows": bbox_metrics.get("matched_target_rows"),
            "bbox_prediction_rows": bbox_metrics.get("input_prediction_rows"),
            "bbox_precision": bbox_metrics.get("proposal_precision_smoke"),
            "mask_false_positive_rows": mask_metrics.get("false_positive_proposal_rows"),
            "mask_matched_target_rows": mask_metrics.get("matched_target_rows"),
            "mask_prediction_rows": mask_metrics.get("input_prediction_rows"),
            "mask_precision": mask_metrics.get("proposal_precision_smoke"),
        },
        "m52_version": M52_VERSION,
        "matching_threshold_m": bbox_matching.get("match_distance_threshold_m") or m49_matching.get("match_distance_threshold_m"),
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "status": "grounded_sam_mask_failure_analysis_ready",
        "target_transition_summary": target_summary,
    }

    write_json(out_dir / "coverage.json", coverage)
    write_jsonl(out_dir / "candidate_pairing_rows.jsonl", candidate_rows)
    write_jsonl(out_dir / "target_transition_rows.jsonl", target_rows)
    write_json(out_dir / "diagnosis.json", diagnosis)
    write_text(out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
