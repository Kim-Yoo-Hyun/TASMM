#!/usr/bin/env python3
"""Analyze E003-M34 scaled pre-cap failure and label blockers."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M31_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M31_pre_cap_policy_tradeoff_analysis_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M34_scaled_pre_cap_failure_analysis_v0"
M34_VERSION = "e003_m34_scaled_pre_cap_failure_analysis_v0"


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


def false_positive_count(row: dict[str, Any]) -> int:
    if "false_positive_proposal_rows" in row:
        return int(row.get("false_positive_proposal_rows", 0) or 0)
    return max(
        0,
        int(row.get("detector_proposal_rows", 0) or 0)
        - int(row.get("matched_proposal_rows", 0) or 0),
    )


def build_visible_miss_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in target_rows:
        if not bool(row.get("depth_consistent_visible_proxy")):
            continue
        if bool(row.get("m23_selected_matched")):
            continue
        rows.append(
            {
                "active_prompt_label": bool(row.get("active_prompt_label")),
                "bottleneck_category": row.get("bottleneck_category"),
                "centroid_in_color_bounds_frame_count": int(row.get("centroid_in_color_bounds_frame_count", 0) or 0),
                "depth_consistent_frame_count": int(row.get("depth_consistent_frame_count", 0) or 0),
                "depth_valid_frame_count": int(row.get("depth_valid_frame_count", 0) or 0),
                "frame_count": int(row.get("frame_count", 0) or 0),
                "label_canonical": str(row.get("label_canonical")),
                "m22_best_match_distance_m": row.get("m22_best_match_distance_m"),
                "m22_matched": bool(row.get("m22_matched")),
                "m23_selected_best_match_distance_m": row.get("m23_selected_best_match_distance_m"),
                "m23_selected_matched": bool(row.get("m23_selected_matched")),
                "object_instance_id": str(row.get("object_instance_id")),
                "scan_id": str(row.get("scan_id")),
                "target_uid": str(row.get("target_uid")),
            }
        )
    return sorted(rows, key=lambda item: (str(item["label_canonical"]), str(item["scan_id"]), str(item["target_uid"])))


def build_visible_label_rows(target_rows: list[dict[str, Any]], visible_miss_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = sorted({str(row.get("label_canonical")) for row in target_rows})
    miss_counts = Counter(str(row["label_canonical"]) for row in visible_miss_rows)
    rows = []
    for label in labels:
        visible = [
            row
            for row in target_rows
            if str(row.get("label_canonical")) == label and bool(row.get("depth_consistent_visible_proxy"))
        ]
        if not visible and not miss_counts[label]:
            continue
        matched = sum(1 for row in visible if bool(row.get("m23_selected_matched")))
        rows.append(
            {
                "label_canonical": label,
                "visible_proxy_matched_target_rows": matched,
                "visible_proxy_missed_target_rows": int(miss_counts[label]),
                "visible_proxy_recall": safe_rate(matched, len(visible)),
                "visible_proxy_target_rows": len(visible),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item["visible_proxy_missed_target_rows"]),
            str(item["label_canonical"]),
        ),
    )


def build_label_failure_rows(
    label_metric_rows: list[dict[str, Any]],
    visible_label_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    visible_by_label = {str(row["label_canonical"]): row for row in visible_label_rows}
    rows = []
    for row in label_metric_rows:
        label = str(row.get("label_canonical", row.get("label")))
        detector_rows = int(row.get("detector_proposal_rows", 0) or 0)
        matched_rows = int(row.get("matched_proposal_rows", 0) or 0)
        matched_targets = int(row.get("matched_target_rows", 0) or 0)
        target_rows = int(row.get("target_rows", 0) or 0)
        fp_rows = false_positive_count(row)
        visible = visible_by_label.get(label, {})
        visible_miss = int(visible.get("visible_proxy_missed_target_rows", 0) or 0)
        precision = row.get("proposal_precision")
        if precision is None:
            precision = safe_rate(matched_rows, detector_rows)
        target_recall = row.get("target_recall")
        if target_recall is None:
            target_recall = safe_rate(matched_targets, target_rows)
        if fp_rows >= 100 and (precision is None or precision < 0.1):
            failure_mode = "high_false_positive_low_precision"
        elif visible_miss:
            failure_mode = "visible_proxy_miss"
        elif target_rows and (target_recall is None or target_recall < 0.5):
            failure_mode = "low_target_recall"
        elif fp_rows:
            failure_mode = "residual_false_positive"
        else:
            failure_mode = "no_primary_label_failure"
        rows.append(
            {
                "detector_proposal_rows": detector_rows,
                "failure_mode": failure_mode,
                "false_positive_proposal_rows": fp_rows,
                "false_positive_rate": safe_rate(fp_rows, detector_rows),
                "label_canonical": label,
                "matched_proposal_rows": matched_rows,
                "matched_target_rows": matched_targets,
                "proposal_precision": precision,
                "target_recall": target_recall,
                "target_rows": target_rows,
                "unmatched_target_rows": max(0, target_rows - matched_targets),
                "visible_proxy_missed_target_rows": visible_miss,
                "visible_proxy_recall": visible.get("visible_proxy_recall"),
                "visible_proxy_target_rows": int(visible.get("visible_proxy_target_rows", 0) or 0),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item["false_positive_proposal_rows"]),
            -int(item["visible_proxy_missed_target_rows"]),
            str(item["label_canonical"]),
        ),
    )


def parse_evidence_labels(evidence: str) -> list[str]:
    try:
        payload = json.loads(evidence)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    labels = []
    for item in payload:
        if isinstance(item, dict) and item.get("label") is not None:
            labels.append(str(item["label"]))
    return labels


def label_row(label_failure_rows: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    for row in label_failure_rows:
        if row["label_canonical"] == label:
            return row
    return None


def build_blocker_resolution_rows(
    m31_blockers: list[dict[str, Any]],
    m31_coverage: dict[str, Any],
    m33_coverage: dict[str, Any],
    visibility_coverage: dict[str, Any],
    label_failure_rows: list[dict[str, Any]],
    visible_label_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    top_m33_fp = [
        {
            "false_positive_rows": int(row["false_positive_proposal_rows"]),
            "label": row["label_canonical"],
            "proposal_precision": row["proposal_precision"],
        }
        for row in label_failure_rows[:8]
    ]
    top_visible_miss = [
        {
            "label": row["label_canonical"],
            "missed_visible": int(row["visible_proxy_missed_target_rows"]),
            "visible_proxy_target_rows": int(row["visible_proxy_target_rows"]),
        }
        for row in visible_label_rows
        if int(row["visible_proxy_missed_target_rows"]) > 0
    ][:8]
    blocker_rows = []
    for blocker in m31_blockers:
        blocker_id = str(blocker["blocker_id"])
        m31_evidence = str(blocker.get("evidence", ""))
        if blocker_id == "two_scan_pilot_only":
            resolved = int(m33_coverage.get("evaluated_scan_count", 0) or 0) >= 8
            status = "resolved" if resolved else "unresolved"
            evidence = (
                f"m33_evaluated_scan_count={m33_coverage.get('evaluated_scan_count')}, "
                f"m33_evaluated_frame_count={m33_coverage.get('evaluated_frame_count')}"
            )
            next_action = "remove scale-count blocker; keep paper-table claim blocked by quality blockers"
            impact = "8-scan diagnostic analysis is supported; final detector benchmark claim is not."
        elif blocker_id == "remaining_scan_level_misses":
            missed = int(m33_coverage.get("scan_eval_target_rows", 0) or 0) - int(m33_coverage.get("matched_target_rows", 0) or 0)
            visible_missed = int(visibility_coverage.get("detector_or_threshold_missed_visible_target_rows", 0) or 0)
            non_visible_or_proxy_blocked = missed - visible_missed
            status = "partially_resolved_by_visibility_separation"
            evidence = (
                f"m33_missed_scan_targets={missed}, "
                f"visible_proxy_missed_targets={visible_missed}, "
                f"not_visible_or_proxy_blocked_targets={non_visible_or_proxy_blocked}"
            )
            next_action = "report scan-level recall and depth-consistent visible-proxy recall separately"
            impact = "Real perception recall can be reported only with an explicit visibility-proxy boundary."
        elif blocker_id == "remaining_false_positive_load":
            status = "unresolved"
            evidence = (
                f"m33_false_positive_rows={m33_coverage.get('false_positive_proposal_rows')}, "
                f"m33_precision={m33_coverage.get('proposal_precision')}, "
                f"top_false_positive_labels={top_m33_fp[:5]}"
            )
            next_action = "design false-positive suppression route before promoting real proposal output to search-policy tables"
            impact = "Deployable search-policy claim remains blocked."
        elif blocker_id == "visibility_proxy_not_true_visibility":
            status = "unresolved_claim_boundary"
            evidence = (
                f"visibility_proxy_is_true_visibility={m33_coverage.get('visibility_proxy_is_true_visibility')}, "
                f"depth_consistent_visible_proxy_targets={visibility_coverage.get('depth_consistent_visible_proxy_target_rows')}"
            )
            next_action = "keep visibility as centroid/depth proxy or implement mask/object visibility before stronger claim"
            impact = "True visible-object recall claim remains unsupported."
        elif blocker_id == "top_visible_miss_labels":
            visible_miss_total = int(visibility_coverage.get("detector_or_threshold_missed_visible_target_rows", 0) or 0)
            status = "analyzed_not_resolved" if visible_miss_total else "resolved"
            evidence = f"m33_visible_miss_labels={top_visible_miss}"
            next_action = "use visible-miss label list for prompt/detector inspection"
            impact = "Visible-proxy misses are small but still prevent a clean recall-saturation claim."
        elif blocker_id == "top_recall_loss_labels":
            plant = label_row(label_failure_rows, "plant") or {}
            status = "reframed_after_scaling"
            evidence = (
                "M31 plant loss is not directly comparable after 8-scan rerun; "
                f"M33 plant false_positive_rows={plant.get('false_positive_proposal_rows')}, "
                f"matched_target_rows={plant.get('matched_target_rows')}, "
                f"target_rows={plant.get('target_rows')}, "
                f"visible_proxy_missed_target_rows={plant.get('visible_proxy_missed_target_rows')}"
            )
            next_action = "treat plant as a high-risk false-positive label rather than only a recall-loss label"
            impact = "Per-label ablation should include plant if proposal filtering is changed."
        elif blocker_id == "top_false_positive_labels":
            m31_labels = parse_evidence_labels(m31_evidence)
            m33_labels = [str(row["label"]) for row in top_m33_fp]
            overlap = sorted(set(m31_labels) & set(m33_labels))
            status = "unresolved"
            evidence = f"m31_m33_top_false_positive_label_overlap={overlap}, m33_top_false_positive_labels={top_m33_fp}"
            next_action = "prioritize labels that persist across two-scan and 8-scan diagnostics"
            impact = "False-positive suppression is the next gate for real-proposal search integration."
        else:
            status = "carried_forward"
            evidence = "No M34-specific rule."
            next_action = str(blocker.get("next_action", "review manually"))
            impact = "No direct claim update."
        blocker_rows.append(
            {
                "blocker_id": blocker_id,
                "m31_evidence": m31_evidence,
                "m31_next_action": blocker.get("next_action"),
                "m31_severity": blocker.get("severity"),
                "m34_evidence": evidence,
                "m34_status": status,
                "next_action": next_action,
                "paper_claim_impact": impact,
                "source_m31_evaluated_scan_count": m31_coverage.get("evaluated_scan_count"),
                "source_m33_evaluated_scan_count": m33_coverage.get("evaluated_scan_count"),
            }
        )
    return blocker_rows


def build_report(coverage: dict[str, Any]) -> str:
    top_fp = ", ".join(
        f"{row['label']} {row['false_positive_rows']}"
        for row in coverage["top_false_positive_labels"]
    )
    top_visible = ", ".join(
        f"{row['label']} {row['missed_visible']}"
        for row in coverage["top_visible_miss_labels"]
    )
    blocker_text = ", ".join(f"{k} {v}" for k, v in sorted(coverage["blocker_status_counts"].items()))
    return "\n".join(
        [
            "# E003-M34 Scaled Failure Analysis",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- M33 evaluated scans / frames: {coverage['m33_evaluated_scan_count']} / {coverage['m33_evaluated_frame_count']}",
            f"- M33 matched targets / scan targets: {coverage['m33_matched_target_rows']} / {coverage['m33_scan_eval_target_rows']}",
            f"- M33 false-positive proposal rows: {coverage['m33_false_positive_proposal_rows']}",
            f"- M33 proposal precision: {coverage['m33_proposal_precision']}",
            f"- M33 scan target recall: {coverage['m33_scan_target_recall']}",
            f"- Depth-consistent visible-proxy target rows: {coverage['visible_proxy_target_rows']}",
            f"- Visible-proxy missed target rows: {coverage['visible_proxy_missed_target_rows']}",
            f"- Visible-proxy recall: {coverage['visible_proxy_recall']}",
            f"- Top false-positive labels: {top_fp}",
            f"- Top visible-miss labels: {top_visible}",
            f"- M31 blocker status counts after M34: {blocker_text}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M34 supports a scaled diagnostic failure analysis for the 8-scan real RGB-D/open-vocabulary proposal route.",
            "- E003-M34 does not support a final real RGB-D/open-vocabulary robustness claim because false-positive load remains unresolved and visibility remains a proxy.",
            "- E003-M34 does not support a deployable search-policy claim from real detector proposals yet.",
            "",
            "## 에이전트 추론",
            "",
            "- The previous scale-count blocker is resolved, but the main technical blocker moved to false-positive suppression.",
            "- Scan-level missed targets are mostly not visible under the current sampled-frame proxy; visible-proxy misses are much smaller and should be reported separately.",
            "- The next useful unit is a false-positive suppression route decision before connecting M33 proposals into E001/E002 search-policy tables.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for M34. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m31-dir", default=DEFAULT_M31_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    calibration_dir = args.m33_dir / "match_preserving_calibration"
    visibility_dir = args.m33_dir / "visibility_denominator"

    m31_coverage = load_json(args.m31_dir / "coverage.json")
    m31_blockers = load_jsonl(args.m31_dir / "scaling_blocker_rows.jsonl")
    m33_coverage = load_json(args.m33_dir / "coverage.json")
    visibility_coverage = load_json(visibility_dir / "coverage.json")
    label_metric_rows = load_jsonl(calibration_dir / "selected_label_metrics.jsonl")
    target_rows = load_jsonl(visibility_dir / "target_denominator_rows.jsonl")

    visible_miss_rows = build_visible_miss_rows(target_rows)
    visible_label_rows = build_visible_label_rows(target_rows, visible_miss_rows)
    label_failure_rows = build_label_failure_rows(label_metric_rows, visible_label_rows)
    blocker_rows = build_blocker_resolution_rows(
        m31_blockers=m31_blockers,
        m31_coverage=m31_coverage,
        m33_coverage=m33_coverage,
        visibility_coverage=visibility_coverage,
        label_failure_rows=label_failure_rows,
        visible_label_rows=visible_label_rows,
    )

    blocker_status_counts = Counter(str(row["m34_status"]) for row in blocker_rows)
    top_false_positive = [
        {
            "false_positive_rows": int(row["false_positive_proposal_rows"]),
            "label": row["label_canonical"],
            "matched_target_rows": int(row["matched_target_rows"]),
            "proposal_precision": row["proposal_precision"],
            "target_rows": int(row["target_rows"]),
            "visible_proxy_missed_target_rows": int(row["visible_proxy_missed_target_rows"]),
        }
        for row in label_failure_rows[:8]
    ]
    top_visible_miss = [
        {
            "label": row["label_canonical"],
            "missed_visible": int(row["visible_proxy_missed_target_rows"]),
            "visible_proxy_recall": row["visible_proxy_recall"],
            "visible_proxy_target_rows": int(row["visible_proxy_target_rows"]),
        }
        for row in visible_label_rows
        if int(row["visible_proxy_missed_target_rows"]) > 0
    ][:8]

    coverage = {
        "all_m31_blockers_analyzed": len(blocker_rows) == len(m31_blockers),
        "blocker_resolution_rows": len(blocker_rows),
        "blocker_status_counts": dict(sorted(blocker_status_counts.items())),
        "default_real_proposal_policy_ready": False,
        "false_positive_suppression_required": int(m33_coverage.get("false_positive_proposal_rows", 0) or 0) > 0,
        "label_failure_rows": len(label_failure_rows),
        "m31_evaluated_scan_count": int(m31_coverage.get("evaluated_scan_count", 0) or 0),
        "m33_evaluated_frame_count": int(m33_coverage.get("evaluated_frame_count", 0) or 0),
        "m33_evaluated_scan_count": int(m33_coverage.get("evaluated_scan_count", 0) or 0),
        "m33_false_positive_proposal_rows": int(m33_coverage.get("false_positive_proposal_rows", 0) or 0),
        "m33_matched_target_rows": int(m33_coverage.get("matched_target_rows", 0) or 0),
        "m33_proposal_precision": m33_coverage.get("proposal_precision"),
        "m33_scan_eval_target_rows": int(m33_coverage.get("scan_eval_target_rows", 0) or 0),
        "m33_scan_target_recall": m33_coverage.get("scan_target_recall"),
        "m34_version": M34_VERSION,
        "next_recommended_unit": "E003-M35 false-positive suppression route decision",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "scale_count_blocker_resolved": any(
            row["blocker_id"] == "two_scan_pilot_only" and row["m34_status"] == "resolved"
            for row in blocker_rows
        ),
        "status": "scaled_pre_cap_failure_analysis_ready",
        "top_false_positive_labels": top_false_positive,
        "top_visible_miss_labels": top_visible_miss,
        "visible_proxy_missed_target_rows": len(visible_miss_rows),
        "visible_proxy_recall": visibility_coverage.get("m23_recall_over_depth_consistent_visible_proxy_denominator"),
        "visible_proxy_target_rows": int(visibility_coverage.get("depth_consistent_visible_proxy_target_rows", 0) or 0),
        "visibility_proxy_is_true_visibility": bool(visibility_coverage.get("visibility_proxy_is_true_visibility")),
    }

    write_jsonl(args.out_dir / "label_failure_rows.jsonl", label_failure_rows)
    write_jsonl(args.out_dir / "visible_miss_rows.jsonl", visible_miss_rows)
    write_jsonl(args.out_dir / "visible_label_rows.jsonl", visible_label_rows)
    write_jsonl(args.out_dir / "blocker_resolution_rows.jsonl", blocker_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
