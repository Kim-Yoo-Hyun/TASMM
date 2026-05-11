#!/usr/bin/env python3
"""Analyze E003-M31 pre-cap policy recall/precision tradeoffs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M26_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M26_prompt_expanded_multiscan_docker_rerun_v0"
DEFAULT_M28_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M28_cap_aware_label_balanced_policy_v0"
DEFAULT_M30_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M30_pre_cap_policy_docker_rerun_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M31_pre_cap_policy_tradeoff_analysis_v0"
M31_VERSION = "e003_m31_pre_cap_policy_tradeoff_analysis_v0"


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


def target_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["target_uid"]): row for row in rows}


def proposal_status_counts(rows: list[dict[str, Any]]) -> dict[str, Counter]:
    by_label: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        label = str(row.get("label_canonical"))
        by_label[label][str(row.get("match_status"))] += 1
    return by_label


def proposal_frame_counts(rows: list[dict[str, Any]]) -> dict[tuple[str, str], Counter]:
    counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in rows:
        scan_id = str(row.get("scan_id"))
        frame_ids = row.get("frame_ids") or ["unknown_frame"]
        frame_id = str(frame_ids[0])
        counts[(scan_id, frame_id)]["proposal_rows"] += 1
        counts[(scan_id, frame_id)][str(row.get("match_status"))] += 1
    return counts


def matched(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("matched"))


def build_target_transition_rows(
    m26_targets: list[dict[str, Any]],
    m28_targets: list[dict[str, Any]],
    m30_targets: list[dict[str, Any]],
    m26_visibility: dict[str, dict[str, Any]],
    m30_visibility: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    m26 = target_map(m26_targets)
    m28 = target_map(m28_targets)
    m30 = target_map(m30_targets)
    target_uids = sorted(set(m26) | set(m28) | set(m30))
    rows = []
    for target_uid in target_uids:
        source = m30.get(target_uid) or m26.get(target_uid) or m28.get(target_uid) or {}
        m26_hit = matched(m26.get(target_uid))
        m28_hit = matched(m28.get(target_uid))
        m30_hit = matched(m30.get(target_uid))
        if m26_hit and m30_hit:
            transition = "stable_matched"
        elif not m26_hit and m30_hit:
            transition = "m30_gain"
        elif m26_hit and not m30_hit:
            transition = "m30_loss"
        else:
            transition = "stable_missed"
        vis30 = m30_visibility.get(target_uid, {})
        vis26 = m26_visibility.get(target_uid, {})
        rows.append(
            {
                "active_prompt_label": bool(vis30.get("active_prompt_label", vis26.get("active_prompt_label", False))),
                "bottleneck_category_m26": vis26.get("bottleneck_category"),
                "bottleneck_category_m30": vis30.get("bottleneck_category"),
                "depth_consistent_visible_proxy": bool(
                    vis30.get("depth_consistent_visible_proxy", vis26.get("depth_consistent_visible_proxy", False))
                ),
                "label_canonical": str(source.get("label_canonical")),
                "m26_best_match_distance_m": (m26.get(target_uid) or {}).get("best_match_distance_m"),
                "m26_matched": m26_hit,
                "m28_best_match_distance_m": (m28.get(target_uid) or {}).get("best_match_distance_m"),
                "m28_matched": m28_hit,
                "m30_best_match_distance_m": (m30.get(target_uid) or {}).get("best_match_distance_m"),
                "m30_matched": m30_hit,
                "object_instance_id": str(source.get("object_instance_id")),
                "scan_id": str(source.get("scan_id")),
                "target_uid": target_uid,
                "transition_m26_to_m30": transition,
            }
        )
    return rows


def build_label_tradeoff_rows(
    target_rows: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    m26_proposals: list[dict[str, Any]],
    m28_proposals: list[dict[str, Any]],
    m30_proposals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_labels = sorted({str(row["label_canonical"]) for row in target_rows})
    m26_counts = proposal_status_counts(m26_proposals)
    m28_counts = proposal_status_counts(m28_proposals)
    m30_counts = proposal_status_counts(m30_proposals)
    rows = []
    for label in target_labels:
        targets = [row for row in transition_rows if row["label_canonical"] == label]
        visible = [row for row in targets if row["depth_consistent_visible_proxy"]]
        m26_prop = m26_counts[label]
        m28_prop = m28_counts[label]
        m30_prop = m30_counts[label]
        m26_proposal_rows = sum(m26_prop.values())
        m28_proposal_rows = sum(m28_prop.values())
        m30_proposal_rows = sum(m30_prop.values())
        row = {
            "depth_consistent_visible_proxy_rows": len(visible),
            "label_canonical": label,
            "m26_false_positive_rows": m26_prop.get("unmatched_false_positive", 0)
            + m26_prop.get("unmatched_no_same_label_target", 0),
            "m26_matched_targets": sum(1 for item in targets if item["m26_matched"]),
            "m26_precision_by_label": safe_rate(m26_prop.get("matched", 0), m26_proposal_rows),
            "m26_proposal_rows": m26_proposal_rows,
            "m28_false_positive_rows": m28_prop.get("unmatched_false_positive", 0)
            + m28_prop.get("unmatched_no_same_label_target", 0),
            "m28_matched_targets": sum(1 for item in targets if item["m28_matched"]),
            "m28_precision_by_label": safe_rate(m28_prop.get("matched", 0), m28_proposal_rows),
            "m28_proposal_rows": m28_proposal_rows,
            "m30_false_positive_rows": m30_prop.get("unmatched_false_positive", 0)
            + m30_prop.get("unmatched_no_same_label_target", 0),
            "m30_gain_targets_vs_m26": sum(1 for item in targets if item["transition_m26_to_m30"] == "m30_gain"),
            "m30_loss_targets_vs_m26": sum(1 for item in targets if item["transition_m26_to_m30"] == "m30_loss"),
            "m30_matched_targets": sum(1 for item in targets if item["m30_matched"]),
            "m30_missed_visible_targets": sum(1 for item in visible if not item["m30_matched"]),
            "m30_precision_by_label": safe_rate(m30_prop.get("matched", 0), m30_proposal_rows),
            "m30_proposal_rows": m30_proposal_rows,
            "target_rows": len(targets),
        }
        row["m30_matched_delta_vs_m26"] = row["m30_matched_targets"] - row["m26_matched_targets"]
        row["m30_false_positive_delta_vs_m26"] = row["m30_false_positive_rows"] - row["m26_false_positive_rows"]
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            -abs(int(row["m30_matched_delta_vs_m26"])),
            -abs(int(row["m30_false_positive_delta_vs_m26"])),
            str(row["label_canonical"]),
        ),
    )


def frame_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row["scan_id"]), str(row["frame_id"]))


def build_frame_tradeoff_rows(
    m26_frames: list[dict[str, Any]],
    m30_frames: list[dict[str, Any]],
    m26_proposals: list[dict[str, Any]],
    m28_proposals: list[dict[str, Any]],
    m30_proposals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m26 = {frame_key(row): row for row in m26_frames}
    m30 = {frame_key(row): row for row in m30_frames}
    m26_counts = proposal_frame_counts(m26_proposals)
    m28_counts = proposal_frame_counts(m28_proposals)
    m30_counts = proposal_frame_counts(m30_proposals)
    rows = []
    for key in sorted(set(m26) | set(m30)):
        row26 = m26.get(key, {})
        row30 = m30.get(key, {})
        c26 = m26_counts[key]
        c28 = m28_counts[key]
        c30 = m30_counts[key]
        rows.append(
            {
                "frame_id": key[1],
                "m26_false_positive_rows": c26.get("unmatched_false_positive", 0)
                + c26.get("unmatched_no_same_label_target", 0),
                "m26_matched_proposal_rows": c26.get("matched", 0),
                "m26_raw_prediction_count": int(row26.get("raw_prediction_count", 0) or 0),
                "m26_written_prediction_count": int(row26.get("written_prediction_count", 0) or 0),
                "m28_false_positive_rows": c28.get("unmatched_false_positive", 0)
                + c28.get("unmatched_no_same_label_target", 0),
                "m28_matched_proposal_rows": c28.get("matched", 0),
                "m28_selected_proposal_rows": sum(c28.values()),
                "m30_false_positive_rows": c30.get("unmatched_false_positive", 0)
                + c30.get("unmatched_no_same_label_target", 0),
                "m30_matched_proposal_rows": c30.get("matched", 0),
                "m30_projected_candidate_count": int(row30.get("projected_candidate_count", 0) or 0),
                "m30_raw_prediction_count": int(row30.get("raw_prediction_count", 0) or 0),
                "m30_written_prediction_count": int(row30.get("written_prediction_count", 0) or 0),
                "scan_id": key[0],
            }
        )
    for row in rows:
        row["m30_false_positive_delta_vs_m26"] = row["m30_false_positive_rows"] - row["m26_false_positive_rows"]
        row["m30_matched_delta_vs_m26"] = row["m30_matched_proposal_rows"] - row["m26_matched_proposal_rows"]
        row["m30_written_delta_vs_m26"] = row["m30_written_prediction_count"] - row["m26_written_prediction_count"]
    return sorted(
        rows,
        key=lambda row: (
            -abs(int(row["m30_false_positive_delta_vs_m26"])),
            -abs(int(row["m30_matched_delta_vs_m26"])),
            str(row["scan_id"]),
            str(row["frame_id"]),
        ),
    )


def top_labels(rows: list[dict[str, Any]], key: str, limit: int = 8) -> list[dict[str, Any]]:
    return [row for row in sorted(rows, key=lambda item: (-int(item.get(key, 0) or 0), str(item["label_canonical"]))) if row.get(key, 0)][:limit]


def top_loss_labels(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return [
        row
        for row in sorted(
            rows,
            key=lambda item: (int(item.get("m30_matched_delta_vs_m26", 0) or 0), str(item["label_canonical"])),
        )
        if int(row.get("m30_matched_delta_vs_m26", 0) or 0) < 0
    ][:limit]


def build_blocker_rows(
    coverage: dict[str, Any],
    label_rows: list[dict[str, Any]],
    transition_counts: Counter,
    m17_manifest_rows: int,
) -> list[dict[str, Any]]:
    m30_missed = transition_counts.get("stable_missed", 0) + transition_counts.get("m30_loss", 0)
    top_missed_visible = top_labels(label_rows, "m30_missed_visible_targets", limit=5)
    top_losses = top_loss_labels(label_rows, limit=5)
    top_false_positive = top_labels(label_rows, "m30_false_positive_rows", limit=5)
    rows = [
        {
            "blocker_id": "two_scan_pilot_only",
            "evidence": f"evaluated_scan_count={coverage['evaluated_scan_count']} / staged_scan_count={m17_manifest_rows}",
            "next_action": "scale pre-cap policy to the remaining staged scans after M31 tradeoff review",
            "severity": "blocking_paper_table_claim",
        },
        {
            "blocker_id": "remaining_scan_level_misses",
            "evidence": f"m30_missed_targets={m30_missed} / scan_eval_targets={coverage['scan_eval_target_rows']}",
            "next_action": "separate not-visible proxy targets from detector/threshold missed visible targets",
            "severity": "blocking_real_perception_claim",
        },
        {
            "blocker_id": "remaining_false_positive_load",
            "evidence": f"m30_false_positive_rows={coverage['m30_false_positive_rows']}, m30_precision={coverage['m30_precision']}",
            "next_action": "inspect top false-positive labels and consider label-specific prompt/calibration rules",
            "severity": "blocking_deployable_policy_claim",
        },
        {
            "blocker_id": "visibility_proxy_not_true_visibility",
            "evidence": f"depth_consistent_visible_proxy_targets={coverage['depth_consistent_visible_proxy_targets']}",
            "next_action": "do not claim true visible-object recall until mask/frustum/object visibility is implemented",
            "severity": "claim_boundary",
        },
        {
            "blocker_id": "top_visible_miss_labels",
            "evidence": json.dumps(
                [
                    {
                        "label": row["label_canonical"],
                        "missed_visible": row["m30_missed_visible_targets"],
                        "target_rows": row["target_rows"],
                    }
                    for row in top_missed_visible
                ],
                sort_keys=True,
            ),
            "next_action": "inspect visible-proxy misses before scaling detector claims",
            "severity": "analysis_required",
        },
        {
            "blocker_id": "top_recall_loss_labels",
            "evidence": json.dumps(
                [
                    {
                        "label": row["label_canonical"],
                        "loss_targets": abs(int(row["m30_matched_delta_vs_m26"])),
                        "m26_matched": row["m26_matched_targets"],
                        "m30_matched": row["m30_matched_targets"],
                    }
                    for row in top_losses
                ],
                sort_keys=True,
            ),
            "next_action": "inspect labels where pre-cap consolidation lost M26 matches before scaling",
            "severity": "analysis_required",
        },
        {
            "blocker_id": "top_false_positive_labels",
            "evidence": json.dumps(
                [
                    {
                        "false_positive_rows": row["m30_false_positive_rows"],
                        "label": row["label_canonical"],
                        "proposal_rows": row["m30_proposal_rows"],
                    }
                    for row in top_false_positive
                ],
                sort_keys=True,
            ),
            "next_action": "use label-level false-positive rows to choose prompt cleanup or per-label caps",
            "severity": "analysis_required",
        },
    ]
    return rows


def build_report(coverage: dict[str, Any], top_gain_labels: list[dict[str, Any]], top_fp_labels: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E003-M31 Pre Cap Policy Tradeoff Analysis",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Evaluated scans: {coverage['evaluated_scan_count']}",
            f"- Scan eval target rows: {coverage['scan_eval_target_rows']}",
            f"- M26 / M28 / M30 matched target rows: {coverage['m26_matched_targets']} / {coverage['m28_matched_targets']} / {coverage['m30_matched_targets']}",
            f"- M30 gains/losses vs M26: {coverage['m30_gain_targets_vs_m26']} / {coverage['m30_loss_targets_vs_m26']}",
            f"- Stable matched / stable missed: {coverage['stable_matched_targets']} / {coverage['stable_missed_targets']}",
            f"- M26 / M28 / M30 false-positive rows: {coverage['m26_false_positive_rows']} / {coverage['m28_false_positive_rows']} / {coverage['m30_false_positive_rows']}",
            f"- M26 / M28 / M30 proposal precision: {coverage['m26_precision']} / {coverage['m28_precision']} / {coverage['m30_precision']}",
            f"- M30 written proposals: {coverage['m30_written_predictions']}",
            f"- M30 depth-consistent visible-proxy target rows: {coverage['depth_consistent_visible_proxy_targets']}",
            f"- M30 missed visible-proxy target rows: {coverage['m30_missed_visible_proxy_targets']}",
            f"- Top gain labels: {', '.join(f'{row['label_canonical']}:+{row['m30_gain_targets_vs_m26']}' for row in top_gain_labels)}",
            f"- Top loss labels: {', '.join(f'{row['label_canonical']}:{row['m30_matched_delta_vs_m26']}' for row in coverage['top_loss_label_rows'])}",
            f"- Top false-positive labels: {', '.join(f'{row['label_canonical']}:{row['m30_false_positive_rows']}' for row in top_fp_labels)}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M31 supports a two-scan diagnostic claim that the pre-cap policy improves the M26 detector pilot's recall/precision tradeoff.",
            "- E003-M31 does not support a final real RGB-D/open-vocabulary robustness claim because scale, true visibility, and remaining false positives are unresolved.",
            "",
            "## 에이전트 추론",
            "",
            "- M30 is better than M26 on matched targets and false positives, while M28 remains a high-precision post-hoc replay with lower matched-target count.",
            "- The next scaling step is reasonable only after visible-proxy misses and top false-positive labels are reviewed, because the remaining error is label- and visibility-structured.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M31. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m26-dir", default=DEFAULT_M26_DIR, type=Path)
    parser.add_argument("--m28-dir", default=DEFAULT_M28_DIR, type=Path)
    parser.add_argument("--m30-dir", default=DEFAULT_M30_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    m17_manifest = load_jsonl(args.m17_dir / "real_proposal_query_manifest.jsonl")
    m26_cov = load_json(args.m26_dir / "coverage.json")
    m28_cov = load_json(args.m28_dir / "coverage.json")
    m30_cov = load_json(args.m30_dir / "coverage.json")

    m26_targets = load_jsonl(args.m26_dir / "detector_rerun" / "matching" / "target_recall_rows.jsonl")
    m28_targets = load_jsonl(args.m28_dir / "selected_target_recall_rows.jsonl")
    m30_targets = load_jsonl(args.m30_dir / "detector_rerun" / "matching" / "target_recall_rows.jsonl")
    m26_proposals = load_jsonl(args.m26_dir / "detector_rerun" / "matching" / "matched_proposals.jsonl")
    m28_proposals = load_jsonl(args.m28_dir / "selected_matched_proposals.jsonl")
    m30_proposals = load_jsonl(args.m30_dir / "detector_rerun" / "matching" / "matched_proposals.jsonl")
    m26_frames = load_jsonl(args.m26_dir / "detector_rerun" / "frame_diagnostics.jsonl")
    m30_frames = load_jsonl(args.m30_dir / "detector_rerun" / "frame_diagnostics.jsonl")
    m26_visibility = target_map(load_jsonl(args.m26_dir / "visibility_denominator" / "target_denominator_rows.jsonl"))
    m30_visibility = target_map(load_jsonl(args.m30_dir / "visibility_denominator" / "target_denominator_rows.jsonl"))

    transition_rows = build_target_transition_rows(
        m26_targets=m26_targets,
        m28_targets=m28_targets,
        m30_targets=m30_targets,
        m26_visibility=m26_visibility,
        m30_visibility=m30_visibility,
    )
    label_rows = build_label_tradeoff_rows(
        target_rows=m30_targets,
        transition_rows=transition_rows,
        m26_proposals=m26_proposals,
        m28_proposals=m28_proposals,
        m30_proposals=m30_proposals,
    )
    frame_rows = build_frame_tradeoff_rows(
        m26_frames=m26_frames,
        m30_frames=m30_frames,
        m26_proposals=m26_proposals,
        m28_proposals=m28_proposals,
        m30_proposals=m30_proposals,
    )

    transition_counts = Counter(row["transition_m26_to_m30"] for row in transition_rows)
    m30_visible = [row for row in transition_rows if row["depth_consistent_visible_proxy"]]
    m30_missed_visible = [row for row in m30_visible if not row["m30_matched"]]
    m30_status = Counter(str(row.get("match_status")) for row in m30_proposals)
    top_gain_labels = top_labels(label_rows, "m30_gain_targets_vs_m26")
    top_losses = top_loss_labels(label_rows)
    top_fp_labels = top_labels(label_rows, "m30_false_positive_rows")

    coverage = {
        "depth_consistent_visible_proxy_targets": len(m30_visible),
        "evaluated_scan_count": int(m30_cov.get("evaluated_scan_count", 0) or 0),
        "m26_false_positive_rows": int(m26_cov["matching_false_positive_proposal_rows"]),
        "m26_matched_targets": int(m26_cov["matching_matched_target_rows"]),
        "m26_precision": m26_cov["matching_proposal_precision_smoke"],
        "m28_false_positive_rows": int(m28_cov["selected_policy"]["false_positive_proposal_rows"]),
        "m28_matched_targets": int(m28_cov["selected_policy"]["matched_target_rows"]),
        "m28_precision": m28_cov["selected_policy"]["proposal_precision"],
        "m30_false_positive_rows": int(m30_cov["matching_false_positive_proposal_rows"]),
        "m30_gain_targets_vs_m26": transition_counts.get("m30_gain", 0),
        "m30_loss_targets_vs_m26": transition_counts.get("m30_loss", 0),
        "m30_matched_targets": int(m30_cov["matching_matched_target_rows"]),
        "m30_missed_visible_proxy_targets": len(m30_missed_visible),
        "m30_precision": m30_cov["matching_proposal_precision_smoke"],
        "m30_proposal_status_counts": dict(sorted(m30_status.items())),
        "m30_version": m30_cov.get("m30_version"),
        "m30_written_predictions": int(m30_cov["frame_written_prediction_rows"]),
        "m31_version": M31_VERSION,
        "next_recommended_unit": "E003-M32 scaled pre-cap policy rerun gate",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "scan_eval_target_rows": len(m30_targets),
        "stable_matched_targets": transition_counts.get("stable_matched", 0),
        "stable_missed_targets": transition_counts.get("stable_missed", 0),
        "status": "pre_cap_policy_tradeoff_analysis_ready",
        "target_transition_counts": dict(sorted(transition_counts.items())),
        "total_label_rows": len(label_rows),
        "total_frame_rows": len(frame_rows),
    }
    blocker_rows = build_blocker_rows(
        coverage=coverage,
        label_rows=label_rows,
        transition_counts=transition_counts,
        m17_manifest_rows=len(m17_manifest),
    )
    coverage["scaling_blocker_rows"] = len(blocker_rows)
    coverage["top_gain_labels"] = [
        {"gain": row["m30_gain_targets_vs_m26"], "label": row["label_canonical"]}
        for row in top_gain_labels[:5]
    ]
    coverage["top_loss_labels"] = [
        {"label": row["label_canonical"], "loss": abs(int(row["m30_matched_delta_vs_m26"]))}
        for row in top_losses[:5]
    ]
    coverage["top_loss_label_rows"] = top_losses[:5]
    coverage["top_false_positive_labels"] = [
        {"false_positive_rows": row["m30_false_positive_rows"], "label": row["label_canonical"]}
        for row in top_fp_labels[:5]
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "target_transition_rows.jsonl", transition_rows)
    write_jsonl(args.out_dir / "label_tradeoff_rows.jsonl", label_rows)
    write_jsonl(args.out_dir / "frame_tradeoff_rows.jsonl", frame_rows)
    write_jsonl(args.out_dir / "scaling_blocker_rows.jsonl", blocker_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, top_gain_labels[:5], top_fp_labels[:5]), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
