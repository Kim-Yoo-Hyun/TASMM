#!/usr/bin/env python3
"""Run E003-M28 cap-aware label-balanced detector policy replay smoke."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
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
DEFAULT_M26_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M26_prompt_expanded_multiscan_docker_rerun_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M28_cap_aware_label_balanced_policy_v0"
M28_VERSION = "e003_m28_cap_aware_label_balanced_policy_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("label_canonical"))
        for row in prompt_payload.get("labels", [])
        if row.get("detector_prompt_enabled") and row.get("label_canonical")
    }


def prompt_labels_by_scan(prompt_payload: dict[str, Any]) -> dict[str, set[str]]:
    by_scan: dict[str, set[str]] = defaultdict(set)
    for row in prompt_payload.get("labels", []):
        if not row.get("detector_prompt_enabled") or not row.get("label_canonical"):
            continue
        label = str(row["label_canonical"])
        for scan_id in row.get("scan_ids", []):
            by_scan[str(scan_id)].add(label)
    return by_scan


def label_mapping_cleanup(
    proposals: list[dict[str, Any]],
    enabled_labels: set[str],
    scan_labels: dict[str, set[str]],
    require_scan_label: bool,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    kept = []
    dropped_non_prompt = 0
    dropped_not_scan_prompt = 0
    for row in proposals:
        label = str(row.get("label_canonical"))
        scan_id = str(row.get("scan_id"))
        if label not in enabled_labels:
            dropped_non_prompt += 1
            continue
        if require_scan_label and label not in scan_labels.get(scan_id, set()):
            dropped_not_scan_prompt += 1
            continue
        kept.append(row)
    return kept, {
        "dropped_non_prompt_label_rows": dropped_non_prompt,
        "dropped_not_scan_prompt_label_rows": dropped_not_scan_prompt,
    }


def spatial_consolidate(
    proposals: list[dict[str, Any]],
    score_mode: str,
    radius_m: float,
) -> list[dict[str, Any]]:
    if radius_m <= 0:
        return sorted(proposals, key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))))

    kept: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in proposals:
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)

    for _, rows in sorted(grouped.items()):
        local_kept: list[dict[str, Any]] = []
        ranked = sorted(rows, key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))))
        for row in ranked:
            if all(distance_m(row["centroid_world_m"], kept_row["centroid_world_m"]) > radius_m for kept_row in local_kept):
                local_kept.append(row)
        kept.extend(local_kept)
    return sorted(kept, key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))))


def apply_per_label_cap(
    proposals: list[dict[str, Any]],
    score_mode: str,
    per_scan_label_cap: int,
    global_cap: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in proposals:
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)

    retained = []
    for _, rows in sorted(grouped.items()):
        ranked = sorted(rows, key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))))
        retained.extend(ranked[:per_scan_label_cap])

    retained = sorted(retained, key=lambda row: (-score_proposal(row, score_mode), str(row.get("proposal_uid", ""))))
    return retained[:global_cap]


def evaluate_policy(
    proposals: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    label_overlap_targets: list[dict[str, Any]],
    match_threshold_m: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    proposal_rows, target_rows, matched_targets = match_proposals(
        proposals=proposals,
        eval_targets=eval_targets,
        threshold_m=match_threshold_m,
    )
    matched_rows = [row for row in proposal_rows if row["match_status"] == "matched"]
    false_positive_rows = [
        row
        for row in proposal_rows
        if row["match_status"] in {"unmatched_false_positive", "unmatched_no_same_label_target"}
    ]
    overlap_labels = {str(row["label_canonical"]) for row in label_overlap_targets}
    label_overlap_matched = sum(
        1 for row in target_rows if row["matched"] and str(row["label_canonical"]) in overlap_labels
    )
    row = {
        "false_positive_proposal_rate": safe_rate(len(false_positive_rows), len(proposal_rows)),
        "false_positive_proposal_rows": len(false_positive_rows),
        "label_overlap_target_recall": safe_rate(label_overlap_matched, len(label_overlap_targets)),
        "label_overlap_target_rows": len(label_overlap_targets),
        "matched_centroid_error_m": numeric_summary(
            [float(row["match_distance_m"]) for row in matched_rows if row.get("match_distance_m") is not None]
        ),
        "matched_proposal_rows": len(matched_rows),
        "matched_target_rows": len(matched_targets),
        "proposal_precision": safe_rate(len(matched_rows), len(proposal_rows)),
        "proposal_rows": len(proposal_rows),
        "scan_target_recall": safe_rate(len(matched_targets), len(eval_targets)),
        "scan_target_rows": len(eval_targets),
    }
    return row, proposal_rows, target_rows, build_label_metrics(target_rows, proposal_rows)


def select_policy(rows: list[dict[str, Any]], baseline_matched: int) -> dict[str, Any]:
    min_matched = max(1, math.ceil(baseline_matched * 0.80))
    eligible = [row for row in rows if int(row["matched_target_rows"]) >= min_matched]
    if not eligible:
        eligible = rows
    return sorted(
        eligible,
        key=lambda row: (
            -(row["proposal_precision"] if row["proposal_precision"] is not None else -1.0),
            -float(row["scan_target_recall"] or 0.0),
            int(row["false_positive_proposal_rows"]),
            int(row["proposal_rows"]),
        ),
    )[0]


def confidence_summary(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [float(row.get("confidence", 0.0) or 0.0) for row in rows]
    if not values:
        return {"max": None, "mean": None, "median": None, "min": None}
    return {"max": max(values), "mean": mean(values), "median": median(values), "min": min(values)}


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_policy"]
    baseline = coverage["baseline_policy"]
    return "\n".join(
        [
            "# E003-M28 Cap Aware Label Balanced Policy",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Input proposal rows: {coverage['input_proposal_rows']}",
            f"- Enabled prompt labels: {coverage['enabled_prompt_label_count']}",
            f"- Label-cleaned proposal rows: {coverage['label_cleaned_proposal_rows']}",
            f"- Dropped non-prompt label rows: {coverage['label_cleanup']['dropped_non_prompt_label_rows']}",
            f"- Dropped not-scan-prompt label rows: {coverage['label_cleanup']['dropped_not_scan_prompt_label_rows']}",
            f"- Baseline proposal rows: {baseline['proposal_rows']}",
            f"- Baseline matched target rows: {baseline['matched_target_rows']}",
            f"- Baseline false-positive rows: {baseline['false_positive_proposal_rows']}",
            f"- Baseline precision: {baseline['proposal_precision']}",
            f"- Selected score mode: `{selected['score_mode']}`",
            f"- Selected per-scan-label cap: {selected['per_scan_label_cap']}",
            f"- Selected spatial consolidation radius m: {selected['spatial_consolidation_radius_m']}",
            f"- Selected proposal rows: {selected['proposal_rows']}",
            f"- Selected matched target rows: {selected['matched_target_rows']}",
            f"- Selected false-positive rows: {selected['false_positive_proposal_rows']}",
            f"- Selected precision: {selected['proposal_precision']}",
            f"- Selected scan target recall: {selected['scan_target_recall']}",
            f"- Precision delta vs baseline: {coverage['selected_precision_delta_vs_baseline']}",
            f"- False-positive reduction vs baseline: {coverage['selected_false_positive_reduction_vs_baseline']}",
            f"- Matched target delta vs baseline: {coverage['selected_matched_target_delta_vs_baseline']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M28 supports an artifact-replay diagnostic that label-balanced cap-aware ranking can reduce written-proposal false positives under the M26 denominator.",
            "- E003-M28 does not support a final real RGB-D/open-vocabulary robustness claim because the policy is replayed after M26's detector cap, not inside the detector before cap.",
            "",
            "## 에이전트 추론",
            "",
            "- The selected replay policy should be treated as a pre-cap Docker integration candidate only if the recall loss is explicitly reported.",
            "- The next Docker run should apply this policy before the per-frame/global cap so raw detector candidates are ranked before truncation.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M28. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m26-dir", default=DEFAULT_M26_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    parser.add_argument("--global-cap", default=1440, type=int)
    args = parser.parse_args()

    proposals = load_jsonl(args.m26_dir / "detector_rerun" / "container_output" / "real_proposals.jsonl")
    targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    prompt_payload = load_json(args.m17_dir / "prompt_set.json")
    enabled_labels = detector_prompt_labels(prompt_payload)
    scan_labels = prompt_labels_by_scan(prompt_payload)
    evaluated_scans = sorted({str(row["scan_id"]) for row in proposals})
    eval_targets = [
        row
        for row in targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]
    baseline_labels = sorted({str(row["label_canonical"]) for row in proposals})
    label_overlap_targets = [row for row in eval_targets if str(row["label_canonical"]) in baseline_labels]

    baseline_policy, baseline_matched, baseline_targets, baseline_label_metrics = evaluate_policy(
        proposals=proposals,
        eval_targets=eval_targets,
        label_overlap_targets=label_overlap_targets,
        match_threshold_m=args.match_distance_threshold_m,
    )
    cleaned, cleanup = label_mapping_cleanup(
        proposals=proposals,
        enabled_labels=enabled_labels,
        scan_labels=scan_labels,
        require_scan_label=True,
    )

    policy_rows: list[dict[str, Any]] = []
    artifacts_by_key: dict[tuple[str, int, float], tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    score_modes = ["confidence", "confidence_log_depth", "confidence_sqrt_depth"]
    per_label_caps = [2, 3, 5, 8, 12, 16, 24, 32]
    consolidation_radii = [0.0, 0.25, 0.5, 0.75, 1.0]
    for score_mode in score_modes:
        for radius_m in consolidation_radii:
            consolidated = spatial_consolidate(cleaned, score_mode=score_mode, radius_m=radius_m)
            for per_label_cap in per_label_caps:
                retained = apply_per_label_cap(
                    consolidated,
                    score_mode=score_mode,
                    per_scan_label_cap=per_label_cap,
                    global_cap=args.global_cap,
                )
                policy, matched, target_rows, label_metrics = evaluate_policy(
                    proposals=retained,
                    eval_targets=eval_targets,
                    label_overlap_targets=label_overlap_targets,
                    match_threshold_m=args.match_distance_threshold_m,
                )
                policy.update(
                    {
                        "global_cap": args.global_cap,
                        "per_scan_label_cap": per_label_cap,
                        "score_mode": score_mode,
                        "spatial_consolidation_radius_m": radius_m,
                    }
                )
                key = (score_mode, per_label_cap, radius_m)
                policy_rows.append(policy)
                artifacts_by_key[key] = (retained, matched, target_rows, label_metrics)

    selected = select_policy(policy_rows, int(baseline_policy["matched_target_rows"]))
    selected_key = (
        str(selected["score_mode"]),
        int(selected["per_scan_label_cap"]),
        float(selected["spatial_consolidation_radius_m"]),
    )
    selected_retained, selected_matched, selected_targets, selected_label_metrics = artifacts_by_key[selected_key]
    selected_matches = [row for row in selected_matched if row["match_status"] == "matched"]

    coverage = {
        "baseline_confidence_summary": confidence_summary(proposals),
        "baseline_policy": baseline_policy,
        "enabled_prompt_label_count": len(enabled_labels),
        "evaluated_scan_count": len(evaluated_scans),
        "evaluated_scans": evaluated_scans,
        "global_cap": args.global_cap,
        "input_proposal_rows": len(proposals),
        "label_cleaned_confidence_summary": confidence_summary(cleaned),
        "label_cleaned_proposal_rows": len(cleaned),
        "label_cleanup": cleanup,
        "m28_version": M28_VERSION,
        "next_policy_id": "cap_aware_label_balanced_ranking_v0",
        "next_recommended_unit": "E003-M29 Docker pre-cap policy integration rerun gate",
        "paper_table_command_ready": False,
        "policy_sweep_rows": len(policy_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "replay_after_detector_cap": True,
        "recall_floor_fraction_for_selection": 0.80,
        "selected_false_positive_reduction_vs_baseline": int(baseline_policy["false_positive_proposal_rows"])
        - int(selected["false_positive_proposal_rows"]),
        "selected_matched_labels": dict(Counter(row["label_canonical"] for row in selected_matches)),
        "selected_matched_target_delta_vs_baseline": int(selected["matched_target_rows"])
        - int(baseline_policy["matched_target_rows"]),
        "selected_policy": selected,
        "selected_precision_delta_vs_baseline": (
            selected["proposal_precision"] - baseline_policy["proposal_precision"]
            if selected["proposal_precision"] is not None and baseline_policy["proposal_precision"] is not None
            else None
        ),
        "status": "cap_aware_label_balanced_policy_smoke_ready",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "policy_sweep_rows.jsonl", policy_rows)
    write_jsonl(args.out_dir / "selected_proposals.jsonl", selected_retained)
    write_jsonl(args.out_dir / "selected_matched_proposals.jsonl", selected_matched)
    write_jsonl(args.out_dir / "selected_target_recall_rows.jsonl", selected_targets)
    write_jsonl(args.out_dir / "selected_label_metrics.jsonl", selected_label_metrics)
    write_jsonl(args.out_dir / "baseline_matched_proposals.jsonl", baseline_matched)
    write_jsonl(args.out_dir / "baseline_label_metrics.jsonl", baseline_label_metrics)
    write_json(args.out_dir / "selected_policy.json", selected)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
