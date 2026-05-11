#!/usr/bin/env python3
"""Plan E003-M35 false-positive suppression route."""

from __future__ import annotations

import argparse
import json
import math
import shlex
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M34_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M34_scaled_pre_cap_failure_analysis_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M35_false_positive_suppression_route_v0"
M35_VERSION = "e003_m35_false_positive_suppression_route_v0"


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


def rank(row: dict[str, Any]) -> int:
    return int(row.get("pre_cap_group_rank", 999999) or 999999)


def is_matched(row: dict[str, Any]) -> bool:
    return row.get("match_status") == "matched"


def metric_row(
    rows: list[dict[str, Any]],
    *,
    policy_id: str,
    baseline: dict[str, Any],
    description: str,
) -> dict[str, Any]:
    matched_rows = [row for row in rows if is_matched(row)]
    matched_target_uids = {str(row.get("matched_target_uid")) for row in matched_rows if row.get("matched_target_uid")}
    matched_target_count = len(matched_target_uids) if matched_target_uids else len(matched_rows)
    false_positive_rows = len(rows) - len(matched_rows)
    return {
        "description": description,
        "false_positive_proposal_rows": false_positive_rows,
        "false_positive_reduction_vs_m33": int(baseline["false_positive_proposal_rows"]) - false_positive_rows,
        "matched_target_delta_vs_m33": matched_target_count - int(baseline["matched_target_rows"]),
        "matched_target_retention": safe_rate(matched_target_count, int(baseline["matched_target_rows"])),
        "matched_target_rows": matched_target_count,
        "policy_id": policy_id,
        "proposal_precision": safe_rate(len(matched_rows), len(rows)),
        "proposal_rows": len(rows),
        "proposal_row_reduction_vs_m33": int(baseline["proposal_rows"]) - len(rows),
    }


def build_global_rank_probe_rows(
    rows: list[dict[str, Any]],
    baseline: dict[str, Any],
    caps: list[int],
) -> list[dict[str, Any]]:
    probe_rows = []
    for cap in caps:
        kept = [row for row in rows if rank(row) <= cap]
        probe = metric_row(
            kept,
            policy_id=f"global_pre_cap_group_rank_le_{cap}",
            baseline=baseline,
            description=f"Keep proposals whose per-scan-label rank is <= {cap}.",
        )
        probe["global_rank_cap"] = cap
        probe["deployability"] = "deployable_fixed_hyperparameter_if_selected_on_dev_split"
        probe_rows.append(probe)
    return probe_rows


def label_caps(
    rows: list[dict[str, Any]],
    label_failure_rows: list[dict[str, Any]],
    *,
    visible_miss_guard: bool,
) -> dict[str, int]:
    visible_miss_by_label = {
        str(row["label_canonical"]): int(row.get("visible_proxy_missed_target_rows", 0) or 0)
        for row in label_failure_rows
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["label_canonical"])].append(row)

    caps = {}
    for label, local_rows in grouped.items():
        if visible_miss_guard and visible_miss_by_label.get(label, 0) > 0:
            caps[label] = max(rank(row) for row in local_rows)
            continue
        matched_ranks = [rank(row) for row in local_rows if is_matched(row)]
        if matched_ranks:
            caps[label] = max(matched_ranks)
        else:
            caps[label] = 0
    return caps


def build_label_cap_rows(
    rows: list[dict[str, Any]],
    label_failure_rows: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    policy_specs = [
        {
            "policy_id": "labelwise_full_recall_rank_cap_oracle_v0",
            "description": "Set each label cap to the max matched proposal rank on M33; labels with no matched proposal get cap 0.",
            "deployability": "diagnostic_upper_bound_not_final_method",
            "visible_miss_guard": False,
        },
        {
            "policy_id": "visible_miss_guarded_labelwise_rank_cap_v0",
            "description": "Use labelwise max matched rank, but keep current cap for labels with visible-proxy misses.",
            "deployability": "candidate_policy_after_dev_split_selection",
            "visible_miss_guard": True,
        },
    ]
    output_rows = []
    for spec in policy_specs:
        caps = label_caps(
            rows=rows,
            label_failure_rows=label_failure_rows,
            visible_miss_guard=bool(spec["visible_miss_guard"]),
        )
        kept = [row for row in rows if rank(row) <= caps.get(str(row["label_canonical"]), 0)]
        row = metric_row(
            kept,
            policy_id=str(spec["policy_id"]),
            baseline=baseline,
            description=str(spec["description"]),
        )
        cap_counts = Counter(caps.values())
        row.update(
            {
                "deployability": spec["deployability"],
                "labels_with_cap_zero": sum(1 for value in caps.values() if value == 0),
                "labels_with_current_cap_24": sum(1 for value in caps.values() if value >= 24),
                "max_label_cap": max(caps.values()) if caps else None,
                "min_nonzero_label_cap": min((value for value in caps.values() if value > 0), default=None),
                "visible_miss_guard": bool(spec["visible_miss_guard"]),
                "cap_histogram": {str(key): value for key, value in sorted(cap_counts.items())},
            }
        )
        output_rows.append(row)
    return output_rows


def build_label_priority_rows(
    label_failure_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matched_ranks_by_label: dict[str, list[int]] = defaultdict(list)
    for row in matched_rows:
        if is_matched(row):
            matched_ranks_by_label[str(row["label_canonical"])].append(rank(row))

    priority_rows = []
    for row in label_failure_rows:
        label = str(row["label_canonical"])
        fp = int(row.get("false_positive_proposal_rows", 0) or 0)
        matched = int(row.get("matched_target_rows", 0) or 0)
        visible_miss = int(row.get("visible_proxy_missed_target_rows", 0) or 0)
        precision = row.get("proposal_precision")
        target_recall = row.get("target_recall")
        matched_ranks = matched_ranks_by_label.get(label, [])
        if visible_miss:
            route_hint = "guard_recall_before_suppressing"
        elif fp >= 100 and (precision is None or float(precision) < 0.12):
            route_hint = "priority_for_rank_cap_suppression"
        elif matched == 0 and fp > 0:
            route_hint = "diagnostic_drop_candidate_only"
        else:
            route_hint = "secondary"
        priority_score = fp + (50 if route_hint == "priority_for_rank_cap_suppression" else 0) - (40 * visible_miss)
        priority_rows.append(
            {
                "failure_mode": row.get("failure_mode"),
                "false_positive_proposal_rows": fp,
                "label_canonical": label,
                "matched_rank_max": max(matched_ranks) if matched_ranks else None,
                "matched_rank_min": min(matched_ranks) if matched_ranks else None,
                "matched_target_rows": matched,
                "priority_score": priority_score,
                "proposal_precision": precision,
                "route_hint": route_hint,
                "target_recall": target_recall,
                "target_rows": int(row.get("target_rows", 0) or 0),
                "visible_proxy_missed_target_rows": visible_miss,
                "visible_proxy_recall": row.get("visible_proxy_recall"),
            }
        )
    return sorted(priority_rows, key=lambda item: (-float(item["priority_score"]), str(item["label_canonical"])))


def build_route_candidate_rows(
    global_rows: list[dict[str, Any]],
    label_cap_rows: list[dict[str, Any]],
    m34_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    best_global_95 = next(
        (
            row
            for row in sorted(global_rows, key=lambda item: -int(item["false_positive_reduction_vs_m33"]))
            if float(row.get("matched_target_retention") or 0.0) >= 0.95
        ),
        None,
    )
    label_full = next(row for row in label_cap_rows if row["policy_id"] == "labelwise_full_recall_rank_cap_oracle_v0")
    label_guarded = next(row for row in label_cap_rows if row["policy_id"] == "visible_miss_guarded_labelwise_rank_cap_v0")
    return [
        {
            "candidate_route": "recall_preserving_rank_cap_sweep_v0",
            "decision": "selected",
            "evidence": {
                "best_global_95pct_retention_probe": best_global_95,
                "labelwise_full_recall_probe": label_full,
                "visible_miss_guarded_probe": label_guarded,
            },
            "expected_burden": "low",
            "next_action": "Implement M36 offline sweep over M33 proposals; report deployable fixed caps separately from diagnostic oracle caps.",
            "reason": "Uses existing proposal fields and can quantify false-positive reduction before any expensive Docker rerun.",
            "risk": "If caps are selected on the same 8 scans, they are diagnostic only; paper claim needs dev/held-out split.",
        },
        {
            "candidate_route": "confidence_depth_threshold_only_v0",
            "decision": "deprioritized",
            "evidence": {
                "m33_match_preserving_calibration_changed_selected_proposals": False,
                "m34_false_positive_suppression_required": bool(m34_coverage.get("false_positive_suppression_required")),
            },
            "expected_burden": "low",
            "next_action": "Include as a baseline arm in M36, but do not make it the primary route.",
            "reason": "M23/M33 match-preserving calibration already selected the baseline-like no-filter config.",
            "risk": "Likely improves precision only by dropping matched targets.",
        },
        {
            "candidate_route": "prompt_label_canonicalization_audit_v0",
            "decision": "deferred_supporting_analysis",
            "evidence": {
                "top_false_positive_labels": m34_coverage.get("top_false_positive_labels", [])[:8],
                "top_visible_miss_labels": m34_coverage.get("top_visible_miss_labels", [])[:8],
            },
            "expected_burden": "medium",
            "next_action": "Run only after M36 identifies labels whose errors look like prompt/canonicalization failures.",
            "reason": "Can reduce systematic label confusion but may change denominator semantics.",
            "risk": "Manual prompt cleanup can look ad hoc without a clean dev/held-out protocol.",
        },
        {
            "candidate_route": "temporal_spatial_consistency_filter_v0",
            "decision": "second_priority",
            "evidence": {
                "m33_final_rows": m34_coverage.get("m33_false_positive_proposal_rows", 0)
                + m34_coverage.get("m33_matched_target_rows", 0),
                "visibility_proxy_is_true_visibility": m34_coverage.get("visibility_proxy_is_true_visibility"),
            },
            "expected_burden": "medium",
            "next_action": "Consider after rank-cap sweep; may require runner changes to retain cluster/frame support.",
            "reason": "A deployable temporal consistency rule is methodologically cleaner, but current final rows do not preserve enough raw cluster support.",
            "risk": "May suppress objects visible in only one or two sampled frames.",
        },
        {
            "candidate_route": "stronger_detector_or_segmentation_backend_v0",
            "decision": "deferred_heavy_route",
            "evidence": {
                "current_detector": "IDEA-Research/grounding-dino-tiny",
                "current_precision": m34_coverage.get("m33_proposal_precision"),
            },
            "expected_burden": "high",
            "next_action": "Treat as top-tier expansion after artifact-level suppression gives a measurable ceiling.",
            "reason": "A stronger detector or mask backend can improve real perception quality but requires new Docker/model/runtime validation.",
            "risk": "Could turn the work into detector engineering before the semantic memory claim is isolated.",
        },
    ]


def build_route_plan(out_dir: Path) -> dict[str, Any]:
    m36_out = (
        REPO_ROOT
        / "experiments"
        / "E003_perception_noise_expansion"
        / "artifacts"
        / "E003-M36_recall_preserving_suppression_sweep_v0"
    )
    command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m36_recall_preserving_suppression_sweep.py",
        "--out-dir",
        str(m36_out),
    ]
    return {
        "allowed_inference_fields": [
            "scan_id",
            "label_canonical",
            "confidence",
            "depth_valid_pixel_count",
            "pre_cap_group_rank",
            "centroid_world_m",
            "frame_ids",
        ],
        "blocked_inference_fields": [
            "match_status",
            "matched_target_uid",
            "matched_3dssg_instance_id",
            "nearest_same_label_target_uid",
            "3DSSG object instance ids",
        ],
        "diagnostic_fields_allowed_for_evaluation_only": [
            "match_status",
            "matched_target_uid",
            "matched_3dssg_instance_id",
            "nearest_same_label_distance_m",
        ],
        "m35_output_dir": str(out_dir),
        "next_command_plan": command_payload(command),
        "next_unit": "E003-M36 recall-preserving suppression sweep smoke",
        "recall_preservation_gate": {
            "conservative_matched_target_retention_min": 0.95,
            "exploratory_matched_target_retention_min": 0.90,
            "must_report_depth_consistent_visible_proxy_recall": True,
            "must_report_scan_target_recall": True,
        },
        "selected_route": "recall_preserving_rank_cap_sweep_v0",
    }


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_probe"]
    top_labels = ", ".join(
        f"{row['label']} {row['false_positive_rows']}"
        for row in coverage["top_false_positive_labels"]
    )
    priority_labels = ", ".join(
        f"{row['label']} {row['route_hint']}"
        for row in coverage["suppression_priority_labels"][:6]
    )
    return "\n".join(
        [
            "# E003-M35 False Positive Suppression Route",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Baseline proposal rows: {coverage['baseline']['proposal_rows']}",
            f"- Baseline matched targets: {coverage['baseline']['matched_target_rows']}",
            f"- Baseline false-positive rows: {coverage['baseline']['false_positive_proposal_rows']}",
            f"- Baseline precision: {coverage['baseline']['proposal_precision']}",
            f"- Top false-positive labels: {top_labels}",
            f"- Suppression priority labels: {priority_labels}",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Selected probe policy: `{selected['policy_id']}`",
            f"- Selected probe proposal rows: {selected['proposal_rows']}",
            f"- Selected probe matched targets: {selected['matched_target_rows']}",
            f"- Selected probe false-positive rows: {selected['false_positive_proposal_rows']}",
            f"- Selected probe precision: {selected['proposal_precision']}",
            f"- Selected probe false-positive reduction vs M33: {selected['false_positive_reduction_vs_m33']}",
            f"- Selected probe matched target retention: {selected['matched_target_retention']}",
            f"- Docker run executed: {coverage['docker_run_executed']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M35 supports selecting a recall-preserving suppression sweep route for the M33 real-proposal artifacts.",
            "- E003-M35 does not support a final suppression method claim because it does not execute the selected M36 sweep or a held-out validation.",
            "- E003-M35 does not support a paper-table real RGB-D/open-vocabulary robustness claim.",
            "",
            "## 에이전트 추론",
            "",
            "- Rank-cap suppression is the first route because it uses fields already present in M33 outputs and can be tested without another long Docker run.",
            "- The selected probe is promising as a ceiling, but any cap selected using M33 match labels is diagnostic until validated on a split that did not choose the caps.",
            "- Confidence/depth-only filtering should stay as a baseline arm, not the primary route.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M35. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m34-dir", default=DEFAULT_M34_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    m33_coverage = load_json(args.m33_dir / "coverage.json")
    m34_coverage = load_json(args.m34_dir / "coverage.json")
    label_failure_rows = load_jsonl(args.m34_dir / "label_failure_rows.jsonl")
    matched_proposal_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_matched_proposals.jsonl")

    baseline = {
        "false_positive_proposal_rows": int(m33_coverage.get("false_positive_proposal_rows", 0) or 0),
        "matched_target_rows": int(m33_coverage.get("matched_target_rows", 0) or 0),
        "proposal_precision": m33_coverage.get("proposal_precision"),
        "proposal_rows": len(matched_proposal_rows),
    }
    global_probe_rows = build_global_rank_probe_rows(
        rows=matched_proposal_rows,
        baseline=baseline,
        caps=[4, 6, 8, 10, 12, 16, 20, 24],
    )
    label_cap_probe_rows = build_label_cap_rows(
        rows=matched_proposal_rows,
        label_failure_rows=label_failure_rows,
        baseline=baseline,
    )
    label_priority_rows = build_label_priority_rows(label_failure_rows, matched_proposal_rows)
    route_candidate_rows = build_route_candidate_rows(global_probe_rows, label_cap_probe_rows, m34_coverage)
    route_plan = build_route_plan(args.out_dir)

    selected_probe = next(
        row for row in label_cap_probe_rows if row["policy_id"] == "visible_miss_guarded_labelwise_rank_cap_v0"
    )
    best_global_95 = next(
        (
            row
            for row in sorted(global_probe_rows, key=lambda item: -int(item["false_positive_reduction_vs_m33"]))
            if float(row.get("matched_target_retention") or 0.0) >= 0.95
        ),
        None,
    )
    coverage = {
        "baseline": baseline,
        "best_global_95pct_retention_probe": best_global_95,
        "docker_run_executed": False,
        "global_rank_probe_rows": len(global_probe_rows),
        "label_cap_probe_rows": len(label_cap_probe_rows),
        "label_priority_rows": len(label_priority_rows),
        "m33_status": m33_coverage.get("status"),
        "m34_status": m34_coverage.get("status"),
        "m35_version": M35_VERSION,
        "next_recommended_unit": route_plan["next_unit"],
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "route_candidate_rows": len(route_candidate_rows),
        "selected_probe": selected_probe,
        "selected_route": route_plan["selected_route"],
        "status": "false_positive_suppression_route_ready",
        "top_false_positive_labels": [
            {
                "false_positive_rows": int(row["false_positive_proposal_rows"]),
                "label": row["label_canonical"],
                "matched_target_rows": int(row["matched_target_rows"]),
            }
            for row in sorted(
                label_priority_rows,
                key=lambda item: (-int(item["false_positive_proposal_rows"]), str(item["label_canonical"])),
            )[:8]
        ],
        "suppression_priority_labels": [
            {
                "false_positive_rows": int(row["false_positive_proposal_rows"]),
                "label": row["label_canonical"],
                "matched_target_rows": int(row["matched_target_rows"]),
                "route_hint": row["route_hint"],
            }
            for row in label_priority_rows[:8]
        ],
    }

    write_jsonl(args.out_dir / "global_rank_probe_rows.jsonl", global_probe_rows)
    write_jsonl(args.out_dir / "label_cap_probe_rows.jsonl", label_cap_probe_rows)
    write_jsonl(args.out_dir / "label_priority_rows.jsonl", label_priority_rows)
    write_jsonl(args.out_dir / "route_candidate_rows.jsonl", route_candidate_rows)
    write_json(args.out_dir / "suppression_route_plan.json", route_plan)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
