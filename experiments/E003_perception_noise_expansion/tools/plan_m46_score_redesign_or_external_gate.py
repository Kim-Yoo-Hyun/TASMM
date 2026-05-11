#!/usr/bin/env python3
"""Plan E003-M46 after M45 support-aware score failure."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from evaluate_m21_detector_matching import build_label_metrics, match_proposals


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M45_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M45_scaled_candidate_pool_export_replay_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M46_score_redesign_or_external_gate_v0"
M46_VERSION = "e003_m46_score_redesign_or_external_gate_v0"
M33_MATCHED = 204
M33_FP = 3210
M33_PRECISION = 0.05975395430579965
WEAK_MATCHED_FLOOR = 194
WEAK_FP_CEILING = 3049


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
    return {"max": max(values), "mean": mean(values), "median": median(values), "min": min(values)}


def distance_m(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def sqrt_depth_score(row: dict[str, Any]) -> float:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    depth_pixels = float(row.get("depth_valid_pixel_count", 0.0) or 0.0)
    return confidence * min(1.0, math.sqrt(depth_pixels) / math.sqrt(5000.0))


def support_features(row: dict[str, Any]) -> dict[str, float]:
    temporal = float(row.get("support_temporal_neighbor_frame_count_r2p0m", 0) or 0)
    spatial = float(row.get("support_spatial_neighbor_count_r1p0m", 0) or 0)
    group_count = float(row.get("support_group_candidate_count", 0) or 0)
    group_frames = max(1.0, float(row.get("support_group_frame_count", 0) or 0))
    return {
        "density": group_count / group_frames,
        "spatial_factor": min(1.0, max(0.0, spatial) / 8.0),
        "temporal_factor": min(1.0, max(0.0, temporal) / 2.0),
    }


def build_base_group_rank(candidate_rows: list[dict[str, Any]]) -> dict[str, int]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    rank_by_uid = {}
    for rows in grouped.values():
        ranked = sorted(rows, key=lambda row: (-sqrt_depth_score(row), str(row["raw_candidate_uid"])))
        for rank, row in enumerate(ranked, start=1):
            rank_by_uid[str(row["raw_candidate_uid"])] = rank
    return rank_by_uid


def score_candidate(row: dict[str, Any], policy_id: str, base_rank_by_uid: dict[str, int]) -> float:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    sqrt_score = sqrt_depth_score(row)
    features = support_features(row)
    temporal = features["temporal_factor"]
    spatial = features["spatial_factor"]
    density = features["density"]
    base_rank = base_rank_by_uid.get(str(row["raw_candidate_uid"]), 999999)

    if policy_id == "confidence":
        return confidence
    if policy_id == "confidence_sqrt_depth":
        return sqrt_score
    if policy_id == "current_support_boost":
        return sqrt_score * (1.0 + 0.25 * temporal + 0.10 * spatial)
    if policy_id == "support_tiebreak_eps":
        return sqrt_score + 0.0001 * (temporal + 0.5 * spatial)
    if policy_id == "temporal_boost_0p05":
        return sqrt_score * (1.0 + 0.05 * temporal)
    if policy_id == "temporal_boost_0p10":
        return sqrt_score * (1.0 + 0.10 * temporal)
    if policy_id == "weak_support_boost":
        return sqrt_score * (1.0 + 0.05 * temporal + 0.02 * spatial)
    if policy_id == "spatial_penalty_temporal_boost":
        return sqrt_score * max(0.0, 1.0 + 0.05 * temporal - 0.05 * spatial)
    if policy_id == "density_penalty_0p01":
        return sqrt_score / (1.0 + 0.01 * density)
    if policy_id == "density_penalty_0p03":
        return sqrt_score / (1.0 + 0.03 * density)
    if policy_id == "rank_guard_12_weak_support":
        if base_rank <= 12:
            return sqrt_score * (1.0 + 0.05 * temporal + 0.02 * spatial)
        return sqrt_score
    if policy_id == "rank_guard_24_weak_support":
        if base_rank <= 24:
            return sqrt_score * (1.0 + 0.05 * temporal + 0.02 * spatial)
        return sqrt_score
    raise ValueError(f"unknown policy_id: {policy_id}")


def select_from_candidate_pool(
    candidate_rows: list[dict[str, Any]],
    *,
    max_predictions: int,
    per_scan_label_cap: int,
    policy_id: str,
    spatial_consolidation_radius_m: float,
    base_rank_by_uid: dict[str, int],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(dict(row))

    consolidated = []
    for _, rows in sorted(grouped.items()):
        ranked = sorted(
            rows,
            key=lambda row: (-score_candidate(row, policy_id, base_rank_by_uid), str(row["raw_candidate_uid"])),
        )
        local_kept: list[dict[str, Any]] = []
        for row in ranked:
            if spatial_consolidation_radius_m <= 0 or all(
                distance_m(row["centroid_world_m"], kept["centroid_world_m"]) > spatial_consolidation_radius_m
                for kept in local_kept
            ):
                local_kept.append(row)
        consolidated.extend(local_kept)

    balanced = []
    balanced_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in consolidated:
        balanced_groups[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    for key, rows in sorted(balanced_groups.items()):
        ranked = sorted(
            rows,
            key=lambda row: (-score_candidate(row, policy_id, base_rank_by_uid), str(row["raw_candidate_uid"])),
        )
        for rank, row in enumerate(ranked[:per_scan_label_cap], start=1):
            row = dict(row)
            row["candidate_selection_policy"] = "cap_aware_label_balanced_ranking_v0"
            row["offline_replay_score_mode"] = policy_id
            row["pre_cap_group_key"] = f"{key[0]}::{key[1]}"
            row["pre_cap_group_rank"] = rank
            row["selection_score"] = round(score_candidate(row, policy_id, base_rank_by_uid), 8)
            balanced.append(row)

    ranked_final = sorted(balanced, key=lambda row: (-float(row["selection_score"]), str(row["raw_candidate_uid"])))
    selected = ranked_final[:max_predictions]
    for rank, row in enumerate(selected, start=1):
        row["pre_cap_rank"] = rank
        frame_id = str((row.get("frame_ids") or ["frame-unknown"])[0])
        scan_id = str(row.get("scan_id"))
        row["proposal_uid"] = f"m46-{policy_id}:{scan_id}:{frame_id}:{rank:05d}"
    return selected


def evaluate_policy(
    *,
    policy_id: str,
    selected_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    threshold_m: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    proposal_rows, target_rows, _ = match_proposals(selected_rows, eval_targets, threshold_m)
    matched_rows = [row for row in proposal_rows if row["match_status"] == "matched"]
    fp_rows = [
        row
        for row in proposal_rows
        if row["match_status"] in {"unmatched_false_positive", "unmatched_no_same_label_target"}
    ]
    matched_distances = [
        float(row["match_distance_m"]) for row in matched_rows if row.get("match_distance_m") is not None
    ]
    matched_target_rows = sum(1 for row in target_rows if row.get("matched"))
    precision = safe_rate(len(matched_rows), len(proposal_rows))
    hard_pass = (
        matched_target_rows >= M33_MATCHED
        and len(fp_rows) < M33_FP
        and precision is not None
        and precision > M33_PRECISION
    )
    weak_positive = (
        matched_target_rows >= WEAK_MATCHED_FLOOR
        and len(fp_rows) <= WEAK_FP_CEILING
        and precision is not None
        and precision > M33_PRECISION
    )
    row = {
        "false_positive_delta_vs_m33": len(fp_rows) - M33_FP,
        "false_positive_proposal_rows": len(fp_rows),
        "hard_pass_vs_m45_contract": hard_pass,
        "matched_centroid_error_m": numeric_summary(matched_distances),
        "matched_target_delta_vs_m33": matched_target_rows - M33_MATCHED,
        "matched_target_rows": matched_target_rows,
        "policy_id": policy_id,
        "proposal_precision": precision,
        "proposal_precision_delta_vs_m33": None if precision is None else precision - M33_PRECISION,
        "proposal_rows": len(proposal_rows),
        "scan_target_recall": safe_rate(matched_target_rows, len(eval_targets)),
        "weak_positive_vs_m45_contract": weak_positive,
    }
    return row, proposal_rows, target_rows, build_label_metrics(target_rows, proposal_rows)


def support_summary_by_match_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = {
        "matched": [row for row in rows if row.get("match_status") == "matched"],
        "false_positive": [
            row
            for row in rows
            if row.get("match_status") in {"unmatched_false_positive", "unmatched_no_same_label_target"}
        ],
    }
    summary = {}
    for name, group in grouped.items():
        values = {
            "confidence": [float(row.get("confidence", 0.0) or 0.0) for row in group],
            "density": [support_features(row)["density"] for row in group],
            "spatial_factor": [support_features(row)["spatial_factor"] for row in group],
            "temporal_factor": [support_features(row)["temporal_factor"] for row in group],
        }
        summary[name] = {
            key: {
                "mean": mean(vals) if vals else None,
                "median": median(vals) if vals else None,
            }
            for key, vals in values.items()
        }
        summary[name]["rows"] = len(group)
    return summary


def matched_target_uids(target_rows: list[dict[str, Any]]) -> set[str]:
    return {str(row["target_uid"]) for row in target_rows if row.get("matched")}


def build_route_decision(policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    hard_passes = [row for row in policy_rows if row["hard_pass_vs_m45_contract"]]
    weak_positives = [row for row in policy_rows if row["weak_positive_vs_m45_contract"]]
    best = sorted(
        policy_rows,
        key=lambda row: (
            int(row["matched_target_rows"]),
            -int(row["false_positive_proposal_rows"]),
            float(row["proposal_precision"] or 0.0),
        ),
        reverse=True,
    )[0]
    if hard_passes or weak_positives:
        selected_route = "score_redesign_followup_first"
        next_unit = "E003-M47 support-aware redesigned score heldout/split validation"
    else:
        selected_route = "external_proposal_baseline_gate_first"
        next_unit = "E003-M47 external proposal/mapping baseline feasibility gate"
    return {
        "best_policy_by_matched_fp_precision": best,
        "hard_pass_policy_count": len(hard_passes),
        "m46_version": M46_VERSION,
        "next_recommended_unit": next_unit,
        "selected_route": selected_route,
        "weak_positive_policy_count": len(weak_positives),
    }


def build_report(coverage: dict[str, Any]) -> str:
    top_rows = coverage["top_policy_rows"]
    top_lines = [
        (
            f"- `{row['policy_id']}`: matched {row['matched_target_rows']}, "
            f"FP {row['false_positive_proposal_rows']}, precision {row['proposal_precision']}, "
            f"hard {row['hard_pass_vs_m45_contract']}, weak {row['weak_positive_vs_m45_contract']}."
        )
        for row in top_rows
    ]
    return "\n".join(
        [
            "# E003-M46 Score Redesign Or External Baseline Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Candidate pool rows: {coverage['candidate_pool_rows']}.",
            f"- Swept policy rows: {coverage['policy_count']}.",
            f"- Hard pass policy count: {coverage['route_decision']['hard_pass_policy_count']}.",
            f"- Weak positive policy count: {coverage['route_decision']['weak_positive_policy_count']}.",
            f"- Selected route: `{coverage['route_decision']['selected_route']}`.",
            f"- Next recommended unit: `{coverage['route_decision']['next_recommended_unit']}`.",
            "",
            "## Top Policies",
            "",
            *top_lines,
            "",
            "## Paper Claim",
            "",
            "- E003-M46 does not create a new paper claim.",
            "- It decides whether M45 failure is repairable by a local score redesign before moving to external baselines.",
            "",
            "## Agent Inference",
            "",
            "- If no hard/weak positive policy appears in this bounded sweep, the current support evidence is not discriminative enough as a main score signal.",
            "- In that case, top-tier progress should shift toward external proposal/mapping baselines or richer support evidence, not a stale-memory bridge claim.",
            "",
            "## User Decision Needed",
            "",
            "- None for this gate; the next unit follows the selected route.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m45-dir", default=DEFAULT_M45_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m45_coverage = load_json(args.m45_dir / "coverage.json")
    docker_coverage = load_json(args.m45_dir / "docker_coverage.json")
    candidate_rows = load_jsonl(args.m45_dir / "container_output" / "pre_cap_candidate_pool.jsonl")
    targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    run_config = m45_coverage.get("run_config") or docker_coverage.get("run_config") or {}
    max_predictions = int(run_config.get("max_predictions", 10000) or 10000)
    per_scan_label_cap = int(run_config.get("pre_cap_per_scan_label_cap", 24) or 24)
    spatial_radius_m = float(run_config.get("pre_cap_spatial_consolidation_radius_m", 0.5) or 0.5)
    evaluated_scans = sorted({str(row["scan_id"]) for row in candidate_rows})
    eval_targets = [
        row
        for row in targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]
    base_rank_by_uid = build_base_group_rank(candidate_rows)
    policies = [
        "confidence",
        "confidence_sqrt_depth",
        "support_tiebreak_eps",
        "temporal_boost_0p05",
        "temporal_boost_0p10",
        "weak_support_boost",
        "rank_guard_12_weak_support",
        "rank_guard_24_weak_support",
        "spatial_penalty_temporal_boost",
        "density_penalty_0p01",
        "density_penalty_0p03",
        "current_support_boost",
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    policy_rows = []
    policy_target_sets = {}
    current_support_matched_rows = []
    for policy_id in policies:
        selected = select_from_candidate_pool(
            candidate_rows,
            max_predictions=max_predictions,
            per_scan_label_cap=per_scan_label_cap,
            policy_id=policy_id,
            spatial_consolidation_radius_m=spatial_radius_m,
            base_rank_by_uid=base_rank_by_uid,
        )
        row, proposal_rows, target_rows, label_rows = evaluate_policy(
            policy_id=policy_id,
            selected_rows=selected,
            eval_targets=eval_targets,
            threshold_m=args.match_distance_threshold_m,
        )
        policy_rows.append(row)
        policy_target_sets[policy_id] = matched_target_uids(target_rows)
        policy_dir = args.out_dir / "policies" / policy_id
        write_jsonl(policy_dir / "matched_proposals.jsonl", proposal_rows)
        write_jsonl(policy_dir / "target_recall_rows.jsonl", target_rows)
        write_jsonl(policy_dir / "label_metrics.jsonl", label_rows)
        if policy_id == "current_support_boost":
            current_support_matched_rows = proposal_rows

    policy_rows = sorted(
        policy_rows,
        key=lambda row: (
            int(row["matched_target_rows"]),
            -int(row["false_positive_proposal_rows"]),
            float(row["proposal_precision"] or 0.0),
        ),
        reverse=True,
    )
    route_decision = build_route_decision(policy_rows)
    sqrt_targets = policy_target_sets.get("confidence_sqrt_depth", set())
    support_targets = policy_target_sets.get("current_support_boost", set())
    failure_delta = {
        "support_gained_target_rows_vs_sqrt_depth": len(support_targets - sqrt_targets),
        "support_lost_target_rows_vs_sqrt_depth": len(sqrt_targets - support_targets),
        "support_lost_target_uid_examples": sorted(sqrt_targets - support_targets)[:12],
    }
    coverage = {
        "candidate_pool_rows": len(candidate_rows),
        "evaluated_scan_count": len(evaluated_scans),
        "eval_target_rows": len(eval_targets),
        "failure_delta_vs_confidence_sqrt_depth": failure_delta,
        "m45_frozen_verdict": (m45_coverage.get("frozen_interpretation_contract_verdict") or {}).get("verdict"),
        "m46_version": M46_VERSION,
        "policy_count": len(policy_rows),
        "route_decision": route_decision,
        "run_config": run_config,
        "status": "score_redesign_or_external_gate_ready",
        "support_summary_by_match_status_current_support": support_summary_by_match_status(
            current_support_matched_rows
        ),
        "top_policy_rows": policy_rows[:8],
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", route_decision)
    write_jsonl(args.out_dir / "policy_sweep.jsonl", policy_rows)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
