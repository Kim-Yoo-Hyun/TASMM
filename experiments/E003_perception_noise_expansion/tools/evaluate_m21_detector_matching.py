#!/usr/bin/env python3
"""Evaluate E003-M20 detector proposal rows against the M17 target denominator."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M20_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M20_detector_model_smoke_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M21_detector_proposal_matching_v0"
M21_VERSION = "e003_m21_detector_proposal_matching_v0"


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


def distance_m(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def numeric_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
    }


def nearest_same_label_targets(
    proposal: dict[str, Any],
    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    candidates = targets_by_scan_label.get((str(proposal["scan_id"]), str(proposal["label_canonical"])), [])
    distances = []
    for target in candidates:
        distances.append(
            {
                "distance_m": distance_m(proposal["centroid_world_m"], target["centroid_world_m"]),
                "label_canonical": target["label_canonical"],
                "object_instance_id": target["object_instance_id"],
                "scan_id": target["scan_id"],
                "target_uid": target["target_uid"],
            }
        )
    return sorted(distances, key=lambda row: row["distance_m"])


def match_proposals(
    proposals: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    threshold_m: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    target_by_uid = {}
    for target in eval_targets:
        targets_by_scan_label[(str(target["scan_id"]), str(target["label_canonical"]))].append(target)
        target_by_uid[str(target["target_uid"])] = target

    matched_targets: set[str] = set()
    proposal_rows: list[dict[str, Any]] = []
    ranked = sorted(
        enumerate(proposals),
        key=lambda item: (-float(item[1].get("confidence", 0.0)), str(item[1].get("proposal_uid", ""))),
    )
    match_by_index: dict[int, dict[str, Any]] = {}

    for original_index, proposal in ranked:
        nearest = nearest_same_label_targets(proposal, targets_by_scan_label)
        nearest_available = [row for row in nearest if row["target_uid"] not in matched_targets]
        best_available = nearest_available[0] if nearest_available else None
        best_any = nearest[0] if nearest else None
        if best_available and best_available["distance_m"] <= threshold_m:
            matched_targets.add(str(best_available["target_uid"]))
            match_by_index[original_index] = {
                "matched_distance_m": best_available["distance_m"],
                "matched_target_uid": best_available["target_uid"],
                "nearest_same_label_distance_m": best_any["distance_m"] if best_any else None,
                "nearest_same_label_target_uid": best_any["target_uid"] if best_any else None,
                "status": "matched",
            }
        else:
            match_by_index[original_index] = {
                "matched_distance_m": None,
                "matched_target_uid": None,
                "nearest_same_label_distance_m": best_any["distance_m"] if best_any else None,
                "nearest_same_label_target_uid": best_any["target_uid"] if best_any else None,
                "status": "unmatched_false_positive" if nearest else "unmatched_no_same_label_target",
            }

    for original_index, proposal in enumerate(proposals):
        match = match_by_index[original_index]
        target = target_by_uid.get(str(match["matched_target_uid"])) if match["matched_target_uid"] else None
        row = dict(proposal)
        row["match_distance_m"] = (
            round(float(match["matched_distance_m"]), 6) if match["matched_distance_m"] is not None else None
        )
        row["match_iou_3d"] = None
        row["match_status"] = match["status"]
        row["matched_3dssg_instance_id"] = target.get("object_instance_id") if target else None
        row["matched_target_uid"] = match["matched_target_uid"]
        row["nearest_same_label_distance_m"] = (
            round(float(match["nearest_same_label_distance_m"]), 6)
            if match["nearest_same_label_distance_m"] is not None
            else None
        )
        row["nearest_same_label_target_uid"] = match["nearest_same_label_target_uid"]
        proposal_rows.append(row)

    target_rows = []
    proposals_by_target = defaultdict(list)
    for row in proposal_rows:
        if row.get("matched_target_uid"):
            proposals_by_target[str(row["matched_target_uid"])].append(row)
    for target in eval_targets:
        matched = str(target["target_uid"]) in matched_targets
        matched_props = proposals_by_target.get(str(target["target_uid"]), [])
        best_prop = matched_props[0] if matched_props else None
        target_rows.append(
            {
                "best_match_distance_m": best_prop.get("match_distance_m") if best_prop else None,
                "best_proposal_uid": best_prop.get("proposal_uid") if best_prop else None,
                "evaluation_target_enabled": bool(target.get("evaluation_target_enabled")),
                "label_canonical": target["label_canonical"],
                "matched": matched,
                "object_instance_id": target["object_instance_id"],
                "scan_id": target["scan_id"],
                "target_uid": target["target_uid"],
            }
        )
    return proposal_rows, target_rows, matched_targets


def build_label_metrics(target_rows: list[dict[str, Any]], proposal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = sorted({row["label_canonical"] for row in target_rows} | {row["label_canonical"] for row in proposal_rows})
    target_count = Counter(row["label_canonical"] for row in target_rows)
    matched_target_count = Counter(row["label_canonical"] for row in target_rows if row["matched"])
    proposal_count = Counter(row["label_canonical"] for row in proposal_rows)
    matched_proposal_count = Counter(row["label_canonical"] for row in proposal_rows if row["match_status"] == "matched")
    rows = []
    for label in labels:
        rows.append(
            {
                "detector_proposal_rows": proposal_count[label],
                "label_canonical": label,
                "matched_proposal_rows": matched_proposal_count[label],
                "matched_target_rows": matched_target_count[label],
                "proposal_precision": safe_rate(matched_proposal_count[label], proposal_count[label]),
                "target_recall": safe_rate(matched_target_count[label], target_count[label]),
                "target_rows": target_count[label],
            }
        )
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M21 Detector Proposal Matching",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Input prediction rows: {coverage['input_prediction_rows']}",
            f"- Evaluated scans: {coverage['evaluated_scan_count']} / {coverage['m17_scan_count']}",
            f"- Scan-level evaluation target rows: {coverage['scan_eval_target_rows']}",
            f"- Label-overlap target rows: {coverage['label_overlap_target_rows']}",
            f"- Matched proposal rows: {coverage['matched_proposal_rows']}",
            f"- Matched target rows: {coverage['matched_target_rows']}",
            f"- Proposal precision smoke: {coverage['proposal_precision_smoke']}",
            f"- Scan target recall smoke: {coverage['scan_target_recall_smoke']}",
            f"- Label-overlap target recall smoke: {coverage['label_overlap_target_recall_smoke']}",
            f"- False-positive proposal rows: {coverage['false_positive_proposal_rows']}",
            f"- Mean matched centroid error m: {coverage['matched_centroid_error_m']['mean']}",
            f"- Matching threshold m: {coverage['match_distance_threshold_m']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M21 supports a first detector-to-denominator matching gate for M20 proposal rows.",
            "- E003-M21 does not support real RGB-D/open-vocabulary robustness because M20 only covers one sampled frame from one scan.",
            "- E003-M21 can identify whether the current RGB-D backprojection and label mapping are plausible enough to scale.",
            "",
            "## 에이전트 추론",
            "",
            "- Low scan-level recall is expected at this stage because the M20 denominator is not visibility-filtered and only one frame was evaluated.",
            "- The current useful signal is whether same-label proposals can be matched with reasonable centroid error and whether false positives dominate.",
            "- The next unit should scale the detector run over more frames/scans or fix RGB-D projection before using this path in paper tables.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M21 smoke. The next step should be selected from scaling M20 inference or improving projection/matching quality.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m20-dir", default=DEFAULT_M20_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    args = parser.parse_args()

    proposals = load_jsonl(args.m20_dir / "container_output" / "real_proposals.jsonl")
    targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    manifest_rows = load_jsonl(args.m17_dir / "real_proposal_query_manifest.jsonl")

    evaluated_scans = sorted({str(row["scan_id"]) for row in proposals})
    proposal_labels = sorted({str(row["label_canonical"]) for row in proposals})
    eval_targets = [
        row
        for row in targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]
    label_overlap_targets = [row for row in eval_targets if str(row["label_canonical"]) in proposal_labels]

    proposal_rows, target_rows, matched_targets = match_proposals(
        proposals=proposals,
        eval_targets=eval_targets,
        threshold_m=args.match_distance_threshold_m,
    )
    matched_proposals = [row for row in proposal_rows if row["match_status"] == "matched"]
    false_positive_rows = [
        row
        for row in proposal_rows
        if row["match_status"] in {"unmatched_false_positive", "unmatched_no_same_label_target"}
    ]
    matched_errors = [float(row["match_distance_m"]) for row in matched_proposals if row.get("match_distance_m") is not None]
    nearest_same_label_distances = [
        float(row["nearest_same_label_distance_m"])
        for row in proposal_rows
        if row.get("nearest_same_label_distance_m") is not None
    ]
    label_metrics = build_label_metrics(target_rows, proposal_rows)
    label_overlap_matched = sum(1 for row in target_rows if row["matched"] and row["label_canonical"] in proposal_labels)

    paper_table_ready = False
    real_claim_ready = False
    status = "detector_matching_smoke_ready"
    if not proposals:
        status = "detector_matching_no_predictions"
    elif not evaluated_scans:
        status = "detector_matching_no_evaluated_scan"

    coverage = {
        "evaluated_scan_count": len(evaluated_scans),
        "evaluated_scans": evaluated_scans,
        "false_positive_proposal_rate_smoke": safe_rate(len(false_positive_rows), len(proposal_rows)),
        "false_positive_proposal_rows": len(false_positive_rows),
        "input_prediction_rows": len(proposals),
        "label_metric_rows": len(label_metrics),
        "label_overlap_target_recall_smoke": safe_rate(label_overlap_matched, len(label_overlap_targets)),
        "label_overlap_target_rows": len(label_overlap_targets),
        "m17_scan_count": len({str(row["scan_id"]) for row in manifest_rows}),
        "m21_version": M21_VERSION,
        "match_distance_threshold_m": args.match_distance_threshold_m,
        "matched_centroid_error_m": numeric_summary(matched_errors),
        "matched_proposal_rows": len(matched_proposals),
        "matched_target_rows": len(matched_targets),
        "nearest_same_label_distance_m": numeric_summary(nearest_same_label_distances),
        "paper_table_command_ready": paper_table_ready,
        "proposal_precision_smoke": safe_rate(len(matched_proposals), len(proposal_rows)),
        "proposal_rows": len(proposal_rows),
        "real_rgbd_or_open_vocab_claim_ready": real_claim_ready,
        "scan_eval_target_rows": len(eval_targets),
        "scan_target_recall_smoke": safe_rate(len(matched_targets), len(eval_targets)),
        "status": status,
        "target_rows": len(target_rows),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "matched_proposals.jsonl", proposal_rows)
    write_jsonl(args.out_dir / "target_recall_rows.jsonl", target_rows)
    write_jsonl(args.out_dir / "label_metrics.jsonl", label_metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0 if status == "detector_matching_smoke_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
