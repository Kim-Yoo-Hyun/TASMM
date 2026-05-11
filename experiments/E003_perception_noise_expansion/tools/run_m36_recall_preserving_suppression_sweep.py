#!/usr/bin/env python3
"""Run E003-M36 recall-preserving suppression sweep over M33 proposals."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from evaluate_m21_detector_matching import build_label_metrics, match_proposals


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M34_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M34_scaled_pre_cap_failure_analysis_v0"
DEFAULT_M35_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M35_false_positive_suppression_route_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M36_recall_preserving_suppression_sweep_v0"
M36_VERSION = "e003_m36_recall_preserving_suppression_sweep_v0"


MATCH_FIELDS = {
    "match_distance_m",
    "match_iou_3d",
    "match_status",
    "matched_3dssg_instance_id",
    "matched_target_uid",
    "nearest_same_label_distance_m",
    "nearest_same_label_target_uid",
}


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
    return {"max": max(values), "mean": mean(values), "median": median(values), "min": min(values)}


def rank(row: dict[str, Any]) -> int:
    return int(row.get("pre_cap_group_rank", 999999) or 999999)


def clean_proposal(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in MATCH_FIELDS}


def matched_target_set(target_rows: list[dict[str, Any]]) -> set[str]:
    return {str(row["target_uid"]) for row in target_rows if row.get("matched")}


def visible_proxy_metrics(target_rows: list[dict[str, Any]], visibility_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = matched_target_set(target_rows)
    visible_targets = [row for row in visibility_rows if row.get("depth_consistent_visible_proxy")]
    matched_visible = [row for row in visible_targets if str(row["target_uid"]) in matched]
    return {
        "depth_consistent_visible_proxy_matched_rows": len(matched_visible),
        "depth_consistent_visible_proxy_missed_rows": len(visible_targets) - len(matched_visible),
        "depth_consistent_visible_proxy_recall": safe_rate(len(matched_visible), len(visible_targets)),
        "depth_consistent_visible_proxy_target_rows": len(visible_targets),
    }


def evaluate_policy(
    *,
    clean_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    threshold_m: float,
    policy_id: str,
    policy_family: str,
    deployability: str,
    description: str,
    baseline_metrics: dict[str, Any] | None,
    policy_params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    proposal_rows, target_rows, _ = match_proposals(clean_rows, eval_targets, threshold_m)
    matched_proposals = [row for row in proposal_rows if row["match_status"] == "matched"]
    false_positive_rows = [
        row
        for row in proposal_rows
        if row["match_status"] in {"unmatched_false_positive", "unmatched_no_same_label_target"}
    ]
    matched_distances = [
        float(row["match_distance_m"])
        for row in matched_proposals
        if row.get("match_distance_m") is not None
    ]
    visible = visible_proxy_metrics(target_rows, visibility_rows)
    matched_targets = sum(1 for row in target_rows if row.get("matched"))
    row = {
        "deployability": deployability,
        "description": description,
        "false_positive_proposal_rows": len(false_positive_rows),
        "matched_centroid_error_m": numeric_summary(matched_distances),
        "matched_proposal_rows": len(matched_proposals),
        "matched_target_rows": matched_targets,
        "policy_family": policy_family,
        "policy_id": policy_id,
        "policy_params": policy_params or {},
        "proposal_precision": safe_rate(len(matched_proposals), len(proposal_rows)),
        "proposal_rows": len(proposal_rows),
        "scan_target_recall": safe_rate(matched_targets, len(eval_targets)),
        "scan_target_rows": len(eval_targets),
    }
    row.update(visible)
    if baseline_metrics:
        row["false_positive_reduction_vs_m33"] = int(baseline_metrics["false_positive_proposal_rows"]) - len(false_positive_rows)
        row["matched_target_delta_vs_m33"] = matched_targets - int(baseline_metrics["matched_target_rows"])
        row["matched_target_retention_vs_m33"] = safe_rate(matched_targets, int(baseline_metrics["matched_target_rows"]))
        row["precision_delta_vs_m33"] = (
            None
            if baseline_metrics.get("proposal_precision") is None or row["proposal_precision"] is None
            else float(row["proposal_precision"]) - float(baseline_metrics["proposal_precision"])
        )
        row["visible_proxy_recall_delta_vs_m33"] = (
            None
            if baseline_metrics.get("depth_consistent_visible_proxy_recall") is None
            or row.get("depth_consistent_visible_proxy_recall") is None
            else float(row["depth_consistent_visible_proxy_recall"])
            - float(baseline_metrics["depth_consistent_visible_proxy_recall"])
        )
    label_rows = build_label_metrics(target_rows, proposal_rows)
    for item in label_rows:
        item["policy_id"] = policy_id
        item["policy_family"] = policy_family
    return row, proposal_rows, target_rows, label_rows


def label_caps_from_baseline(
    matched_rows: list[dict[str, Any]],
    label_failure_rows: list[dict[str, Any]],
    *,
    retain_fraction: float,
    visible_miss_guard: bool,
) -> dict[str, int]:
    visible_miss_by_label = {
        str(row["label_canonical"]): int(row.get("visible_proxy_missed_target_rows", 0) or 0)
        for row in label_failure_rows
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matched_rows:
        grouped[str(row["label_canonical"])].append(row)

    caps = {}
    for label, rows in grouped.items():
        if visible_miss_guard and visible_miss_by_label.get(label, 0) > 0:
            caps[label] = max(rank(row) for row in rows)
            continue
        matched_ranks = sorted(rank(row) for row in rows if row.get("match_status") == "matched")
        if not matched_ranks:
            caps[label] = 0
            continue
        keep_count = max(1, math.ceil(len(matched_ranks) * retain_fraction))
        caps[label] = matched_ranks[keep_count - 1]
    return caps


def apply_label_caps(clean_rows: list[dict[str, Any]], caps: dict[str, int]) -> list[dict[str, Any]]:
    return [row for row in clean_rows if rank(row) <= caps.get(str(row["label_canonical"]), 0)]


def policy_id_float(value: float) -> str:
    return str(value).replace(".", "p")


def build_policies(
    clean_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    label_failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = [
        {
            "clean_rows": clean_rows,
            "deployability": "baseline",
            "description": "M33 proposals without additional suppression.",
            "family": "baseline",
            "id": "m33_no_suppression",
            "params": {},
        }
    ]

    for cap in [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]:
        policies.append(
            {
                "clean_rows": [row for row in clean_rows if rank(row) <= cap],
                "deployability": "deployable_fixed_hyperparameter_if_selected_on_dev_split",
                "description": f"Keep proposals with per-scan-label rank <= {cap}.",
                "family": "global_rank_cap",
                "id": f"global_rank_cap_le_{cap}",
                "params": {"global_rank_cap": cap},
            }
        )

    for threshold in [0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40]:
        for min_depth in [0, 250, 500, 1000, 2000]:
            policies.append(
                {
                    "clean_rows": [
                        row
                        for row in clean_rows
                        if float(row.get("confidence", 0.0) or 0.0) >= threshold
                        and int(row.get("depth_valid_pixel_count", 0) or 0) >= min_depth
                    ],
                    "deployability": "deployable_fixed_hyperparameter_if_selected_on_dev_split",
                    "description": f"Keep proposals with confidence >= {threshold} and depth pixels >= {min_depth}.",
                    "family": "confidence_depth_filter",
                    "id": f"confidence_ge_{policy_id_float(threshold)}_depth_ge_{min_depth}",
                    "params": {"confidence_threshold": threshold, "min_depth_pixels": min_depth},
                }
            )

    for retain_fraction in [1.0, 0.95, 0.90]:
        caps = label_caps_from_baseline(
            matched_rows,
            label_failure_rows,
            retain_fraction=retain_fraction,
            visible_miss_guard=False,
        )
        policies.append(
            {
                "cap_histogram": dict(Counter(caps.values())),
                "clean_rows": apply_label_caps(clean_rows, caps),
                "deployability": "diagnostic_oracle_not_deployable",
                "description": f"Set per-label rank caps from M33 matched ranks at retain_fraction={retain_fraction}.",
                "family": "labelwise_rank_cap_diagnostic",
                "id": f"labelwise_rank_cap_oracle_retain_{policy_id_float(retain_fraction)}",
                "params": {
                    "label_caps": caps,
                    "retain_fraction": retain_fraction,
                    "visible_miss_guard": False,
                },
            }
        )

    caps = label_caps_from_baseline(
        matched_rows,
        label_failure_rows,
        retain_fraction=1.0,
        visible_miss_guard=True,
    )
    policies.append(
        {
            "cap_histogram": dict(Counter(caps.values())),
            "clean_rows": apply_label_caps(clean_rows, caps),
            "deployability": "candidate_policy_after_dev_split_selection",
            "description": "Use labelwise full-retention rank caps, but keep current cap for labels with visible-proxy misses.",
            "family": "visible_miss_guarded_labelwise_rank_cap",
            "id": "visible_miss_guarded_labelwise_rank_cap_v0",
            "params": {
                "label_caps": caps,
                "retain_fraction": 1.0,
                "visible_miss_guard": True,
            },
        }
    )
    return policies


def summarize_family(sweep_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sweep_rows:
        by_family[str(row["policy_family"])].append(row)
    for family, items in sorted(by_family.items()):
        best_95 = select_best(items, min_retention=0.95)
        best_100 = select_best(items, min_retention=1.0)
        rows.append(
            {
                "best_100pct_policy_id": best_100.get("policy_id") if best_100 else None,
                "best_100pct_false_positive_reduction_vs_m33": best_100.get("false_positive_reduction_vs_m33") if best_100 else None,
                "best_95pct_policy_id": best_95.get("policy_id") if best_95 else None,
                "best_95pct_false_positive_reduction_vs_m33": best_95.get("false_positive_reduction_vs_m33") if best_95 else None,
                "family": family,
                "policy_rows": len(items),
            }
        )
    return rows


def select_best(rows: list[dict[str, Any]], min_retention: float) -> dict[str, Any] | None:
    eligible = [
        row
        for row in rows
        if row.get("matched_target_retention_vs_m33") is not None
        and float(row["matched_target_retention_vs_m33"]) >= min_retention
    ]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda row: (
            -int(row.get("false_positive_reduction_vs_m33", 0) or 0),
            -(float(row.get("proposal_precision") or 0.0)),
            -float(row.get("depth_consistent_visible_proxy_recall") or 0.0),
            int(row.get("proposal_rows", 0) or 0),
            str(row["policy_id"]),
        ),
    )[0]


def slim_policy(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    keep = [
        "deployability",
        "depth_consistent_visible_proxy_recall",
        "false_positive_proposal_rows",
        "false_positive_reduction_vs_m33",
        "matched_target_delta_vs_m33",
        "matched_target_retention_vs_m33",
        "matched_target_rows",
        "policy_family",
        "policy_id",
        "proposal_precision",
        "proposal_rows",
        "scan_target_recall",
    ]
    return {key: row.get(key) for key in keep}


def build_report(coverage: dict[str, Any]) -> str:
    deployable = coverage["selected_deployable_95pct_policy"]
    diagnostic = coverage["selected_diagnostic_policy"]
    m35 = coverage["m35_selected_probe_policy"]
    return "\n".join(
        [
            "# E003-M36 Recall Preserving Suppression Sweep",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Input proposal rows: {coverage['input_proposal_rows']}",
            f"- Evaluation target rows: {coverage['scan_target_rows']}",
            f"- Sweep policy rows: {coverage['sweep_rows']}",
            f"- Baseline matched targets: {coverage['baseline_policy']['matched_target_rows']}",
            f"- Baseline false-positive rows: {coverage['baseline_policy']['false_positive_proposal_rows']}",
            f"- Baseline precision: {coverage['baseline_policy']['proposal_precision']}",
            f"- Baseline visible-proxy recall: {coverage['baseline_policy']['depth_consistent_visible_proxy_recall']}",
            f"- Selected deployable 95pct policy: `{deployable['policy_id'] if deployable else None}`",
            f"- Selected deployable 95pct matched targets: {deployable['matched_target_rows'] if deployable else None}",
            f"- Selected deployable 95pct false-positive rows: {deployable['false_positive_proposal_rows'] if deployable else None}",
            f"- Selected deployable 95pct precision: {deployable['proposal_precision'] if deployable else None}",
            f"- Selected diagnostic policy: `{diagnostic['policy_id'] if diagnostic else None}`",
            f"- Selected diagnostic matched targets: {diagnostic['matched_target_rows'] if diagnostic else None}",
            f"- Selected diagnostic false-positive rows: {diagnostic['false_positive_proposal_rows'] if diagnostic else None}",
            f"- Selected diagnostic precision: {diagnostic['proposal_precision'] if diagnostic else None}",
            f"- M35 selected probe after rematching: `{m35['policy_id'] if m35 else None}`",
            f"- M35 selected probe matched targets / false positives: {m35['matched_target_rows'] if m35 else None} / {m35['false_positive_proposal_rows'] if m35 else None}",
            f"- Split validation required: {coverage['split_validation_required']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M36 supports an offline suppression sweep over the M33 real-proposal artifacts.",
            "- E003-M36 supports a diagnostic ceiling for labelwise rank-cap suppression, not a final method claim.",
            "- E003-M36 does not support a paper-table real RGB-D/open-vocabulary robustness claim because policy selection still needs split validation.",
            "",
            "## 에이전트 추론",
            "",
            "- Deployable fixed hyperparameters give a modest recall-preserving gain, while labelwise diagnostic caps show a much larger ceiling.",
            "- The next step should validate cap selection on a dev/held-out split before adding the policy to the Docker runner.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M36. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m34-dir", default=DEFAULT_M34_DIR, type=Path)
    parser.add_argument("--m35-dir", default=DEFAULT_M35_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    args = parser.parse_args()

    matched_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_matched_proposals.jsonl")
    clean_rows = [clean_proposal(row) for row in matched_rows]
    all_targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    visibility_rows = load_jsonl(args.m33_dir / "visibility_denominator" / "target_denominator_rows.jsonl")
    label_failure_rows = load_jsonl(args.m34_dir / "label_failure_rows.jsonl")
    m33_coverage = load_json(args.m33_dir / "coverage.json")
    m35_coverage = load_json(args.m35_dir / "coverage.json")

    evaluated_scans = sorted({str(row["scan_id"]) for row in clean_rows})
    eval_targets = [
        row
        for row in all_targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]

    baseline_policy, baseline_proposals, baseline_targets, baseline_labels = evaluate_policy(
        clean_rows=clean_rows,
        eval_targets=eval_targets,
        visibility_rows=visibility_rows,
        threshold_m=args.match_distance_threshold_m,
        policy_id="m33_no_suppression",
        policy_family="baseline",
        deployability="baseline",
        description="M33 proposals without additional suppression.",
        baseline_metrics=None,
    )
    baseline_policy["false_positive_reduction_vs_m33"] = 0
    baseline_policy["matched_target_delta_vs_m33"] = 0
    baseline_policy["matched_target_retention_vs_m33"] = 1.0
    baseline_policy["precision_delta_vs_m33"] = 0.0
    baseline_policy["visible_proxy_recall_delta_vs_m33"] = 0.0

    policies = build_policies(clean_rows, baseline_proposals, label_failure_rows)
    sweep_rows: list[dict[str, Any]] = []
    selected_policy_payloads: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    label_rows_output: list[dict[str, Any]] = []

    for policy in policies:
        row, proposal_rows, target_rows, label_rows = evaluate_policy(
            clean_rows=policy["clean_rows"],
            eval_targets=eval_targets,
            visibility_rows=visibility_rows,
            threshold_m=args.match_distance_threshold_m,
            policy_id=str(policy["id"]),
            policy_family=str(policy["family"]),
            deployability=str(policy["deployability"]),
            description=str(policy["description"]),
            baseline_metrics=baseline_policy,
            policy_params=policy.get("params", {}),
        )
        if policy.get("cap_histogram") is not None:
            row["cap_histogram"] = {str(k): v for k, v in sorted(policy["cap_histogram"].items())}
        sweep_rows.append(row)
        if policy["id"] in {
            "m33_no_suppression",
            "visible_miss_guarded_labelwise_rank_cap_v0",
            "labelwise_rank_cap_oracle_retain_1p0",
        }:
            selected_policy_payloads[str(policy["id"])] = (proposal_rows, target_rows, label_rows)
            label_rows_output.extend(label_rows)

    family_rows = summarize_family(sweep_rows)
    deployable_rows = [
        row
        for row in sweep_rows
        if row["deployability"] == "deployable_fixed_hyperparameter_if_selected_on_dev_split"
    ]
    diagnostic_rows = [
        row
        for row in sweep_rows
        if row["deployability"] in {"diagnostic_oracle_not_deployable", "candidate_policy_after_dev_split_selection"}
    ]
    selected_deployable = select_best(deployable_rows, min_retention=0.95)
    selected_diagnostic = select_best(diagnostic_rows, min_retention=1.0)
    selected_m35 = next(
        (row for row in sweep_rows if row["policy_id"] == "visible_miss_guarded_labelwise_rank_cap_v0"),
        None,
    )

    coverage = {
        "baseline_policy": slim_policy(baseline_policy),
        "expected_m33_false_positive_rows": m33_coverage.get("false_positive_proposal_rows"),
        "expected_m33_matched_target_rows": m33_coverage.get("matched_target_rows"),
        "input_proposal_rows": len(clean_rows),
        "m35_selected_probe_expected": m35_coverage.get("selected_probe"),
        "m35_selected_probe_policy": slim_policy(selected_m35),
        "m36_version": M36_VERSION,
        "match_distance_threshold_m": args.match_distance_threshold_m,
        "next_recommended_unit": "E003-M37 suppression split validation gate",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "scan_target_rows": len(eval_targets),
        "selected_deployable_95pct_policy": slim_policy(selected_deployable),
        "selected_diagnostic_policy": slim_policy(selected_diagnostic),
        "split_validation_required": True,
        "status": "recall_preserving_suppression_sweep_ready",
        "sweep_family_rows": len(family_rows),
        "sweep_rows": len(sweep_rows),
        "visibility_proxy_is_true_visibility": False,
    }

    write_jsonl(args.out_dir / "sweep_rows.jsonl", sweep_rows)
    write_jsonl(args.out_dir / "family_summary_rows.jsonl", family_rows)
    write_jsonl(args.out_dir / "selected_policy_label_rows.jsonl", label_rows_output)
    if selected_m35 and selected_m35["policy_id"] in selected_policy_payloads:
        proposal_rows, target_rows, _ = selected_policy_payloads[str(selected_m35["policy_id"])]
        write_jsonl(args.out_dir / "selected_policy_proposals.jsonl", proposal_rows)
        write_jsonl(args.out_dir / "selected_policy_target_rows.jsonl", target_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
