#!/usr/bin/env python3
"""Run E003-M37 suppression split validation gate."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from run_m36_recall_preserving_suppression_sweep import (
    clean_proposal,
    evaluate_policy,
    rank,
    safe_rate,
    select_best,
    slim_policy,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M34_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M34_scaled_pre_cap_failure_analysis_v0"
DEFAULT_M36_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M36_recall_preserving_suppression_sweep_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M37_suppression_split_validation_v0"
M37_VERSION = "e003_m37_suppression_split_validation_v0"


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


def policy_id_float(value: float) -> str:
    return str(value).replace(".", "p")


def rows_for_scans(rows: list[dict[str, Any]], scans: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("scan_id")) in scans]


def scan_stats(
    clean_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scans = sorted({str(row["scan_id"]) for row in clean_rows})
    proposal_count = Counter(str(row["scan_id"]) for row in clean_rows)
    matched_count = Counter(str(row["scan_id"]) for row in matched_rows if row.get("match_status") == "matched")
    target_count = Counter(
        str(row["scan_id"])
        for row in targets
        if row.get("evaluation_target_enabled")
    )
    visible_count = Counter(
        str(row["scan_id"])
        for row in visibility_rows
        if row.get("depth_consistent_visible_proxy")
    )
    label_count: dict[str, set[str]] = defaultdict(set)
    matched_label_count: dict[str, set[str]] = defaultdict(set)
    for row in clean_rows:
        label_count[str(row["scan_id"])].add(str(row["label_canonical"]))
    for row in matched_rows:
        if row.get("match_status") == "matched":
            matched_label_count[str(row["scan_id"])].add(str(row["label_canonical"]))
    return [
        {
            "evaluation_target_rows": int(target_count[scan]),
            "matched_label_count": len(matched_label_count[scan]),
            "matched_proposal_rows": int(matched_count[scan]),
            "proposal_label_count": len(label_count[scan]),
            "proposal_rows": int(proposal_count[scan]),
            "scan_id": scan,
            "visible_proxy_target_rows": int(visible_count[scan]),
        }
        for scan in scans
    ]


def choose_balanced_scan_split(stats: list[dict[str, Any]], dev_scan_count: int) -> tuple[set[str], set[str], dict[str, Any]]:
    totals = {
        "evaluation_target_rows": sum(int(row["evaluation_target_rows"]) for row in stats),
        "matched_proposal_rows": sum(int(row["matched_proposal_rows"]) for row in stats),
        "proposal_rows": sum(int(row["proposal_rows"]) for row in stats),
        "visible_proxy_target_rows": sum(int(row["visible_proxy_target_rows"]) for row in stats),
    }
    scans = [str(row["scan_id"]) for row in stats]
    stats_by_scan = {str(row["scan_id"]): row for row in stats}
    best = None
    for combo in itertools.combinations(scans, dev_scan_count):
        dev = set(combo)
        score = 0.0
        dev_totals = {}
        for key, total in totals.items():
            dev_value = sum(int(stats_by_scan[scan][key]) for scan in dev)
            dev_totals[key] = dev_value
            score += abs((safe_rate(dev_value, total) or 0.0) - 0.5)
        candidate = (score, sorted(dev), dev_totals)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    dev_scans = set(best[1])
    heldout_scans = set(scans) - dev_scans
    return dev_scans, heldout_scans, {
        "balance_score": best[0],
        "dev_totals": best[2],
        "heldout_totals": {key: totals[key] - best[2][key] for key in totals},
        "totals": totals,
    }


def matched_rank_caps(
    train_matched_rows: list[dict[str, Any]],
    train_visibility_rows: list[dict[str, Any]],
    *,
    retain_fraction: float,
    visible_miss_guard: bool,
    fallback_cap: int,
) -> dict[str, int]:
    matched_ranks_by_label: dict[str, list[int]] = defaultdict(list)
    all_labels = sorted({str(row["label_canonical"]) for row in train_matched_rows})
    for row in train_matched_rows:
        if row.get("match_status") == "matched":
            matched_ranks_by_label[str(row["label_canonical"])].append(rank(row))

    visible_miss = Counter()
    for row in train_visibility_rows:
        if row.get("depth_consistent_visible_proxy") and not row.get("m23_selected_matched"):
            visible_miss[str(row["label_canonical"])] += 1

    caps = {}
    for label in all_labels:
        if visible_miss_guard and visible_miss[label] > 0:
            caps[label] = fallback_cap
            continue
        ranks = sorted(matched_ranks_by_label[label])
        if not ranks:
            caps[label] = fallback_cap
            continue
        keep_count = max(1, math.ceil(len(ranks) * retain_fraction))
        caps[label] = ranks[keep_count - 1]
    return caps


def apply_caps(clean_rows: list[dict[str, Any]], caps: dict[str, int], fallback_cap: int) -> list[dict[str, Any]]:
    return [row for row in clean_rows if rank(row) <= caps.get(str(row["label_canonical"]), fallback_cap)]


def label_coverage_rows(
    train_rows: list[dict[str, Any]],
    heldout_rows: list[dict[str, Any]],
    heldout_targets: list[dict[str, Any]],
    caps: dict[str, int],
    fallback_cap: int,
) -> list[dict[str, Any]]:
    train_matched = Counter(str(row["label_canonical"]) for row in train_rows if row.get("match_status") == "matched")
    train_prop = Counter(str(row["label_canonical"]) for row in train_rows)
    heldout_prop = Counter(str(row["label_canonical"]) for row in heldout_rows)
    heldout_target = Counter(str(row["label_canonical"]) for row in heldout_targets)
    labels = sorted(set(train_prop) | set(heldout_prop) | set(heldout_target))
    rows = []
    for label in labels:
        cap = caps.get(label, fallback_cap)
        if train_matched[label] == 0 and heldout_target[label] > 0:
            risk = "heldout_target_without_dev_match"
        elif train_matched[label] == 0 and heldout_prop[label] > 0:
            risk = "heldout_proposal_without_dev_match"
        else:
            risk = "covered"
        rows.append(
            {
                "cap": cap,
                "heldout_proposal_rows": int(heldout_prop[label]),
                "heldout_target_rows": int(heldout_target[label]),
                "label_canonical": label,
                "risk": risk,
                "train_matched_rows": int(train_matched[label]),
                "train_proposal_rows": int(train_prop[label]),
                "uses_fallback_cap": label not in caps,
            }
        )
    return rows


def evaluate_split_policy(
    *,
    clean_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    baseline_metrics: dict[str, Any],
    threshold_m: float,
    policy_id: str,
    policy_family: str,
    deployability: str,
    description: str,
    policy_params: dict[str, Any],
) -> dict[str, Any]:
    row, _, _, _ = evaluate_policy(
        clean_rows=clean_rows,
        eval_targets=eval_targets,
        visibility_rows=visibility_rows,
        threshold_m=threshold_m,
        policy_id=policy_id,
        policy_family=policy_family,
        deployability=deployability,
        description=description,
        baseline_metrics=baseline_metrics,
        policy_params=policy_params,
    )
    return row


def select_best_dev_policy(rows: list[dict[str, Any]], min_retention: float) -> dict[str, Any] | None:
    return select_best(rows, min_retention=min_retention)


def build_split_results(
    *,
    train_scans: set[str],
    heldout_scans: set[str],
    clean_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    threshold_m: float,
    split_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    train_clean = rows_for_scans(clean_rows, train_scans)
    train_matched = rows_for_scans(matched_rows, train_scans)
    train_targets = rows_for_scans(eval_targets, train_scans)
    train_visibility = rows_for_scans(visibility_rows, train_scans)
    heldout_clean = rows_for_scans(clean_rows, heldout_scans)
    heldout_matched = rows_for_scans(matched_rows, heldout_scans)
    heldout_targets = rows_for_scans(eval_targets, heldout_scans)
    heldout_visibility = rows_for_scans(visibility_rows, heldout_scans)

    train_baseline, _, _, _ = evaluate_policy(
        clean_rows=train_clean,
        eval_targets=train_targets,
        visibility_rows=train_visibility,
        threshold_m=threshold_m,
        policy_id=f"{split_name}_train_baseline",
        policy_family="baseline",
        deployability="baseline",
        description="Train/dev split baseline without suppression.",
        baseline_metrics=None,
    )
    train_baseline["false_positive_reduction_vs_m33"] = 0
    train_baseline["matched_target_delta_vs_m33"] = 0
    train_baseline["matched_target_retention_vs_m33"] = 1.0
    train_baseline["precision_delta_vs_m33"] = 0.0
    train_baseline["visible_proxy_recall_delta_vs_m33"] = 0.0

    heldout_baseline, _, _, _ = evaluate_policy(
        clean_rows=heldout_clean,
        eval_targets=heldout_targets,
        visibility_rows=heldout_visibility,
        threshold_m=threshold_m,
        policy_id=f"{split_name}_heldout_baseline",
        policy_family="baseline",
        deployability="baseline",
        description="Held-out split baseline without suppression.",
        baseline_metrics=None,
    )
    heldout_baseline["false_positive_reduction_vs_m33"] = 0
    heldout_baseline["matched_target_delta_vs_m33"] = 0
    heldout_baseline["matched_target_retention_vs_m33"] = 1.0
    heldout_baseline["precision_delta_vs_m33"] = 0.0
    heldout_baseline["visible_proxy_recall_delta_vs_m33"] = 0.0

    train_rows = [dict(train_baseline, split=split_name, phase="train")]
    heldout_rows = [dict(heldout_baseline, split=split_name, phase="heldout")]

    # Select fixed hyperparameters on the train split.
    train_candidates: list[dict[str, Any]] = []
    candidate_payloads: list[dict[str, Any]] = []
    for cap in [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]:
        filtered = [row for row in train_clean if rank(row) <= cap]
        candidate = evaluate_split_policy(
            clean_rows=filtered,
            eval_targets=train_targets,
            visibility_rows=train_visibility,
            baseline_metrics=train_baseline,
            threshold_m=threshold_m,
            policy_id=f"global_rank_cap_le_{cap}",
            policy_family="global_rank_cap",
            deployability="deployable_fixed_hyperparameter_selected_on_train",
            description=f"Keep proposals with per-scan-label rank <= {cap}.",
            policy_params={"global_rank_cap": cap},
        )
        candidate["split"] = split_name
        candidate["phase"] = "train"
        train_candidates.append(candidate)
        candidate_payloads.append({"family": "global_rank_cap", "params": {"global_rank_cap": cap}})

    for confidence in [0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40]:
        for min_depth in [0, 250, 500, 1000, 2000]:
            filtered = [
                row
                for row in train_clean
                if float(row.get("confidence", 0.0) or 0.0) >= confidence
                and int(row.get("depth_valid_pixel_count", 0) or 0) >= min_depth
            ]
            candidate = evaluate_split_policy(
                clean_rows=filtered,
                eval_targets=train_targets,
                visibility_rows=train_visibility,
                baseline_metrics=train_baseline,
                threshold_m=threshold_m,
                policy_id=f"confidence_ge_{policy_id_float(confidence)}_depth_ge_{min_depth}",
                policy_family="confidence_depth_filter",
                deployability="deployable_fixed_hyperparameter_selected_on_train",
                description=f"Keep confidence >= {confidence} and depth pixels >= {min_depth}.",
                policy_params={"confidence_threshold": confidence, "min_depth_pixels": min_depth},
            )
            candidate["split"] = split_name
            candidate["phase"] = "train"
            train_candidates.append(candidate)
            candidate_payloads.append(
                {
                    "family": "confidence_depth_filter",
                    "params": {"confidence_threshold": confidence, "min_depth_pixels": min_depth},
                }
            )

    best_fixed = select_best_dev_policy(train_candidates, min_retention=0.95)
    if best_fixed is not None:
        train_rows.append(best_fixed)
        params = best_fixed["policy_params"]
        if best_fixed["policy_family"] == "global_rank_cap":
            heldout_filtered = [row for row in heldout_clean if rank(row) <= int(params["global_rank_cap"])]
        else:
            heldout_filtered = [
                row
                for row in heldout_clean
                if float(row.get("confidence", 0.0) or 0.0) >= float(params["confidence_threshold"])
                and int(row.get("depth_valid_pixel_count", 0) or 0) >= int(params["min_depth_pixels"])
            ]
        heldout = evaluate_split_policy(
            clean_rows=heldout_filtered,
            eval_targets=heldout_targets,
            visibility_rows=heldout_visibility,
            baseline_metrics=heldout_baseline,
            threshold_m=threshold_m,
            policy_id=f"{best_fixed['policy_id']}_selected_on_train",
            policy_family=str(best_fixed["policy_family"]),
            deployability="deployable_fixed_hyperparameter_selected_on_train",
            description="Best fixed policy selected on train and applied to heldout.",
            policy_params=params,
        )
        heldout["split"] = split_name
        heldout["phase"] = "heldout"
        heldout_rows.append(heldout)

    fallback_cap = 24
    caps = matched_rank_caps(
        train_matched,
        train_visibility,
        retain_fraction=1.0,
        visible_miss_guard=True,
        fallback_cap=fallback_cap,
    )
    train_labelwise = evaluate_split_policy(
        clean_rows=apply_caps(train_clean, caps, fallback_cap),
        eval_targets=train_targets,
        visibility_rows=train_visibility,
        baseline_metrics=train_baseline,
        threshold_m=threshold_m,
        policy_id="dev_selected_visible_miss_guarded_labelwise_rank_cap_v0",
        policy_family="visible_miss_guarded_labelwise_rank_cap",
        deployability="candidate_policy_selected_on_train",
        description="Labelwise caps selected on train and protected by train visible-miss guard.",
        policy_params={"fallback_cap": fallback_cap, "label_caps": caps, "visible_miss_guard": True},
    )
    train_labelwise["split"] = split_name
    train_labelwise["phase"] = "train"
    train_rows.append(train_labelwise)

    heldout_labelwise = evaluate_split_policy(
        clean_rows=apply_caps(heldout_clean, caps, fallback_cap),
        eval_targets=heldout_targets,
        visibility_rows=heldout_visibility,
        baseline_metrics=heldout_baseline,
        threshold_m=threshold_m,
        policy_id="dev_selected_visible_miss_guarded_labelwise_rank_cap_v0",
        policy_family="visible_miss_guarded_labelwise_rank_cap",
        deployability="candidate_policy_selected_on_train",
        description="Labelwise caps selected on train and applied to heldout.",
        policy_params={"fallback_cap": fallback_cap, "label_caps": caps, "visible_miss_guard": True},
    )
    heldout_labelwise["split"] = split_name
    heldout_labelwise["phase"] = "heldout"
    heldout_rows.append(heldout_labelwise)

    oracle_caps = matched_rank_caps(
        heldout_matched,
        heldout_visibility,
        retain_fraction=1.0,
        visible_miss_guard=True,
        fallback_cap=fallback_cap,
    )
    heldout_oracle = evaluate_split_policy(
        clean_rows=apply_caps(heldout_clean, oracle_caps, fallback_cap),
        eval_targets=heldout_targets,
        visibility_rows=heldout_visibility,
        baseline_metrics=heldout_baseline,
        threshold_m=threshold_m,
        policy_id="heldout_oracle_visible_miss_guarded_labelwise_rank_cap_v0",
        policy_family="heldout_oracle_labelwise_rank_cap",
        deployability="diagnostic_oracle_not_deployable",
        description="Heldout oracle labelwise cap for ceiling only.",
        policy_params={"fallback_cap": fallback_cap, "label_caps": oracle_caps, "visible_miss_guard": True},
    )
    heldout_oracle["split"] = split_name
    heldout_oracle["phase"] = "heldout"
    heldout_rows.append(heldout_oracle)

    coverage_rows = label_coverage_rows(train_matched, heldout_matched, heldout_targets, caps, fallback_cap)
    split_summary = {
        "dev_scan_count": len(train_scans),
        "dev_scans": sorted(train_scans),
        "fallback_cap": fallback_cap,
        "heldout_scan_count": len(heldout_scans),
        "heldout_scans": sorted(heldout_scans),
        "heldout_target_without_dev_match_labels": sum(
            1 for row in coverage_rows if row["risk"] == "heldout_target_without_dev_match"
        ),
        "split": split_name,
    }
    return train_rows + heldout_rows, coverage_rows, split_summary


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_candidate_policy"]
    fixed = coverage["selected_fixed_policy"]
    oracle = coverage["heldout_oracle_policy"]
    return "\n".join(
        [
            "# E003-M37 Suppression Split Validation Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Split protocol: `{coverage['selected_split_protocol']}`",
            f"- Dev scans: {coverage['dev_scan_count']}",
            f"- Heldout scans: {coverage['heldout_scan_count']}",
            f"- Heldout baseline matched targets: {coverage['heldout_baseline_policy']['matched_target_rows']}",
            f"- Heldout baseline false-positive rows: {coverage['heldout_baseline_policy']['false_positive_proposal_rows']}",
            f"- Heldout target labels without dev matched example: {coverage['heldout_target_without_dev_match_labels']}",
            f"- Selected candidate policy: `{selected['policy_id'] if selected else None}`",
            f"- Selected candidate heldout matched targets: {selected['matched_target_rows'] if selected else None}",
            f"- Selected candidate heldout false-positive rows: {selected['false_positive_proposal_rows'] if selected else None}",
            f"- Selected candidate heldout precision: {selected['proposal_precision'] if selected else None}",
            f"- Selected candidate heldout retention: {selected['matched_target_retention_vs_m33'] if selected else None}",
            f"- Selected fixed policy: `{fixed['policy_id'] if fixed else None}`",
            f"- Heldout oracle policy: `{oracle['policy_id'] if oracle else None}`",
            f"- Heldout oracle false-positive rows: {oracle['false_positive_proposal_rows'] if oracle else None}",
            f"- Runner integration recommended: {coverage['runner_integration_recommended']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M37 supports a split-validation gate for suppression policies over M33 real-proposal artifacts.",
            "- E003-M37 does not support Docker runner integration if heldout recall-preserving false-positive reduction is weak.",
            "- E003-M37 does not support a final real RGB-D/open-vocabulary robustness claim.",
            "",
            "## 에이전트 추론",
            "",
            "- The diagnostic labelwise ceiling should not be promoted unless dev-selected caps transfer to heldout scans.",
            "- If heldout gains are weak, the next step should be stronger split design or temporal/spatial evidence rather than runner integration.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M37. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m34-dir", default=DEFAULT_M34_DIR, type=Path)
    parser.add_argument("--m36-dir", default=DEFAULT_M36_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    parser.add_argument("--dev-scan-count", default=4, type=int)
    args = parser.parse_args()

    matched_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_matched_proposals.jsonl")
    clean_rows = [clean_proposal(row) for row in matched_rows]
    all_targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    visibility_rows = load_jsonl(args.m33_dir / "visibility_denominator" / "target_denominator_rows.jsonl")
    m36_coverage = load_json(args.m36_dir / "coverage.json")
    eval_targets = [
        row
        for row in all_targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in {str(item["scan_id"]) for item in clean_rows}
    ]
    stats = scan_stats(clean_rows, matched_rows, all_targets, visibility_rows)
    dev_scans, heldout_scans, split_balance = choose_balanced_scan_split(stats, args.dev_scan_count)
    validation_rows, label_coverage, split_summary = build_split_results(
        train_scans=dev_scans,
        heldout_scans=heldout_scans,
        clean_rows=clean_rows,
        matched_rows=matched_rows,
        eval_targets=eval_targets,
        visibility_rows=visibility_rows,
        threshold_m=args.match_distance_threshold_m,
        split_name="balanced_scan_4_4_v0",
    )
    heldout_rows = [row for row in validation_rows if row["phase"] == "heldout"]
    heldout_baseline = next(row for row in heldout_rows if row["policy_family"] == "baseline")
    selected_candidate = next(
        row for row in heldout_rows if row["policy_family"] == "visible_miss_guarded_labelwise_rank_cap"
    )
    selected_fixed = next(
        (row for row in heldout_rows if row["deployability"] == "deployable_fixed_hyperparameter_selected_on_train"),
        None,
    )
    heldout_oracle = next(row for row in heldout_rows if row["policy_family"] == "heldout_oracle_labelwise_rank_cap")

    candidate_retention = float(selected_candidate.get("matched_target_retention_vs_m33") or 0.0)
    candidate_fp_reduction_rate = safe_rate(
        int(selected_candidate.get("false_positive_reduction_vs_m33", 0) or 0),
        int(heldout_baseline.get("false_positive_proposal_rows", 0) or 0),
    ) or 0.0
    runner_integration_recommended = candidate_retention >= 0.95 and candidate_fp_reduction_rate >= 0.10
    next_unit = (
        "E003-M38 suppression runner integration gate"
        if runner_integration_recommended
        else "E003-M38 stronger split or temporal-spatial suppression gate"
    )
    coverage = {
        "dev_scan_count": len(dev_scans),
        "dev_scans": sorted(dev_scans),
        "heldout_baseline_policy": slim_policy(heldout_baseline),
        "heldout_oracle_policy": slim_policy(heldout_oracle),
        "heldout_scan_count": len(heldout_scans),
        "heldout_scans": sorted(heldout_scans),
        "label_coverage_rows": len(label_coverage),
        "label_coverage_risk_counts": dict(Counter(str(row["risk"]) for row in label_coverage)),
        "label_stratified_validation_feasible": split_summary["heldout_target_without_dev_match_labels"] == 0,
        "heldout_target_without_dev_match_labels": split_summary["heldout_target_without_dev_match_labels"],
        "m36_selected_diagnostic_policy": m36_coverage.get("selected_diagnostic_policy"),
        "m37_version": M37_VERSION,
        "next_recommended_unit": next_unit,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "runner_integration_recommended": runner_integration_recommended,
        "selected_candidate_fp_reduction_rate": candidate_fp_reduction_rate,
        "selected_candidate_policy": slim_policy(selected_candidate),
        "selected_fixed_policy": slim_policy(selected_fixed),
        "selected_split_protocol": "balanced_scan_4_4_v0",
        "split_balance": split_balance,
        "split_summary": split_summary,
        "status": "suppression_split_validation_gate_ready",
        "validation_rows": len(validation_rows),
    }

    write_jsonl(args.out_dir / "scan_split_rows.jsonl", stats)
    write_jsonl(args.out_dir / "validation_rows.jsonl", validation_rows)
    write_jsonl(args.out_dir / "label_coverage_rows.jsonl", label_coverage)
    write_json(args.out_dir / "split_plan.json", {"split_balance": split_balance, "split_summary": split_summary})
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
