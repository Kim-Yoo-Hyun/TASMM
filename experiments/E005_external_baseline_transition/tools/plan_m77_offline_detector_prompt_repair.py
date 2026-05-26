#!/usr/bin/env python3
"""Design E005-M77 offline detector/prompt repair over pre-cap candidate pools."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
DEFAULT_M68_ROOT = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
DEFAULT_M69_ROOT = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
DEFAULT_M71_ROOT = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0"
DEFAULT_M75_ROOT = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
DEFAULT_M76_ROOT = EXP_ROOT / "artifacts" / "E005-M76_real_proposal_claim_boundary_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M77_offline_detector_prompt_repair_v0"
VERSION = "e005_m77_offline_detector_prompt_repair_v0"

BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
MATCH_THRESHOLD_M = 1.0
CURRENT_POLICY_ID = "current_runner_confidence_radius0p5_cap24"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def score_candidate(row: dict[str, Any], mode: str) -> float:
    confidence = float(row.get("confidence") or 0.0)
    depth = float(row.get("depth_valid_pixel_count") or 0.0)
    sqrt_depth = min(1.0, math.sqrt(max(depth, 0.0)) / math.sqrt(5000.0))
    log_depth = min(1.0, math.log1p(max(depth, 0.0)) / math.log1p(5000.0))
    if mode == "confidence":
        return confidence
    if mode == "confidence_sqrt_depth":
        return confidence * sqrt_depth
    if mode == "confidence_log_depth":
        return confidence * log_depth
    if mode == "confidence_depth_floor_500":
        return confidence if depth >= 500 else confidence * 0.25
    raise RuntimeError(f"unknown score mode: {mode}")


def target_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["scan_id"]), str(row["label_canonical"])


def match_candidates_to_targets(
    candidate_rows: list[dict[str, Any]],
    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    matched_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        targets = targets_by_scan_label.get((str(row["scan_id"]), str(row["label_canonical"])), [])
        centroid = row.get("centroid_world_m")
        nearest_target = None
        nearest_distance = None
        if centroid:
            for target in targets:
                dist = distance(centroid, target["centroid_world_m"])
                if nearest_distance is None or dist < nearest_distance:
                    nearest_distance = dist
                    nearest_target = target
        out = dict(row)
        out["m77_match_threshold_m"] = MATCH_THRESHOLD_M
        out["nearest_same_label_distance_m"] = round(nearest_distance, 6) if nearest_distance is not None else None
        out["nearest_same_label_target_uid"] = nearest_target.get("target_uid") if nearest_target else None
        if nearest_target and nearest_distance is not None and nearest_distance <= MATCH_THRESHOLD_M:
            out["match_status"] = "matched"
            out["matched_target_uid"] = nearest_target["target_uid"]
            out["matched_3dssg_instance_id"] = nearest_target["object_instance_id"]
            out["match_distance_m"] = round(nearest_distance, 6)
        elif targets:
            out["match_status"] = "unmatched_false_positive"
            out["matched_target_uid"] = None
            out["matched_3dssg_instance_id"] = None
            out["match_distance_m"] = None
        else:
            out["match_status"] = "unmatched_no_same_label_target"
            out["matched_target_uid"] = None
            out["matched_3dssg_instance_id"] = None
            out["match_distance_m"] = None
        out["proposal_uid"] = out.get("proposal_uid") or out.get("pre_cap_candidate_pool_uid") or out.get("raw_candidate_uid")
        matched_rows.append(out)
    return matched_rows


def spatial_consolidate(rows: list[dict[str, Any]], radius_m: float, score_mode: str) -> list[dict[str, Any]]:
    if radius_m <= 0:
        return list(rows)
    ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row.get("raw_candidate_uid"))))
    kept: list[dict[str, Any]] = []
    for row in ranked:
        centroid = row.get("centroid_world_m")
        if not centroid:
            continue
        if all(distance(centroid, kept_row["centroid_world_m"]) > radius_m for kept_row in kept if kept_row.get("centroid_world_m")):
            kept.append(row)
    return kept


def select_policy_candidates(rows: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    score_mode = str(policy["score_mode"])
    radius_m = float(policy["spatial_radius_m"])
    cap = int(policy["per_scan_label_cap"])
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)

    selected: list[dict[str, Any]] = []
    for (scan_id, label), group_rows in sorted(groups.items()):
        consolidated = spatial_consolidate(group_rows, radius_m, score_mode)
        ranked = sorted(consolidated, key=lambda row: (-score_candidate(row, score_mode), str(row.get("raw_candidate_uid"))))
        for local_rank, row in enumerate(ranked[:cap], start=1):
            out = dict(row)
            out["m77_policy_id"] = policy["policy_id"]
            out["m77_score_mode"] = score_mode
            out["m77_spatial_radius_m"] = radius_m
            out["m77_per_scan_label_cap"] = cap
            out["m77_group_key"] = f"{scan_id}::{label}"
            out["m77_group_rank"] = local_rank
            out["m77_selection_score"] = round(score_candidate(row, score_mode), 8)
            selected.append(out)
    selected = sorted(
        selected,
        key=lambda row: (
            -float(row["m77_selection_score"]),
            str(row["scan_id"]),
            str(row["label_canonical"]),
            int(row["m77_group_rank"]),
            str(row.get("raw_candidate_uid")),
        ),
    )
    for rank, row in enumerate(selected, start=1):
        row["m77_global_rank"] = rank
    return selected


def target_rank(rows: list[dict[str, Any]], query: dict[str, Any]) -> tuple[int | None, int | None, str | None]:
    same_label = [
        row
        for row in rows
        if str(row["scan_id"]) == str(query["current_rescan_id"])
        and str(row["label_canonical"]) == str(query["label_canonical"])
    ]
    same_label = sorted(
        same_label,
        key=lambda row: (
            -float(row.get("m77_selection_score") or score_candidate(row, "confidence")),
            int(row.get("m77_group_rank") or row.get("pre_cap_group_rank") or 10**9),
            str(row.get("proposal_uid")),
        ),
    )
    target_uid = str(query["target_uid"])
    for rank, row in enumerate(same_label, start=1):
        if str(row.get("matched_target_uid")) == target_uid:
            return rank, rank - 1, str(row.get("proposal_uid"))
    return None, None, None


def build_policies() -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = [
        {
            "policy_id": CURRENT_POLICY_ID,
            "score_mode": "confidence",
            "spatial_radius_m": 0.5,
            "per_scan_label_cap": 24,
            "deployability": "current_runner_replay",
        },
        {
            "policy_id": "offline_confidence_sqrt_depth_radius0p5_cap24",
            "score_mode": "confidence_sqrt_depth",
            "spatial_radius_m": 0.5,
            "per_scan_label_cap": 24,
            "deployability": "offline_replay_candidate",
        },
        {
            "policy_id": "offline_confidence_log_depth_radius0p5_cap24",
            "score_mode": "confidence_log_depth",
            "spatial_radius_m": 0.5,
            "per_scan_label_cap": 24,
            "deployability": "offline_replay_candidate",
        },
        {
            "policy_id": "offline_confidence_depth_floor500_radius0p5_cap24",
            "score_mode": "confidence_depth_floor_500",
            "spatial_radius_m": 0.5,
            "per_scan_label_cap": 24,
            "deployability": "offline_replay_candidate",
        },
    ]
    for cap in [8, 12, 16]:
        policies.append(
            {
                "policy_id": f"offline_confidence_radius0p5_cap{cap}",
                "score_mode": "confidence",
                "spatial_radius_m": 0.5,
                "per_scan_label_cap": cap,
                "deployability": "offline_replay_candidate",
            }
        )
    for radius in [0.25, 0.75, 1.0]:
        policies.append(
            {
                "policy_id": f"offline_confidence_radius{str(radius).replace('.', 'p')}_cap24",
                "score_mode": "confidence",
                "spatial_radius_m": radius,
                "per_scan_label_cap": 24,
                "deployability": "offline_replay_candidate",
            }
        )
    return policies


def summarize_policy(policy_id: str, selected_rows: list[dict[str, Any]], query_eval_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched_proposals = [row for row in selected_rows if row.get("match_status") == "matched"]
    matched_targets = {str(row["matched_target_uid"]) for row in matched_proposals if row.get("matched_target_uid")}
    query_success_top5 = sum(1 for row in query_eval_rows if row["target_rank"] is not None and int(row["target_rank"]) <= 5)
    query_success_top10 = sum(1 for row in query_eval_rows if row["target_rank"] is not None and int(row["target_rank"]) <= 10)
    target_detected = sum(1 for row in query_eval_rows if row["target_rank"] is not None)
    fp_before_values = [int(row["false_positive_before_target_count"]) for row in query_eval_rows if row["false_positive_before_target_count"] is not None]
    return {
        "policy_id": policy_id,
        "selected_rows": len(selected_rows),
        "matched_proposal_rows": len(matched_proposals),
        "matched_target_uids": len(matched_targets),
        "target_rows": len(target_rows),
        "scan_target_recall": safe_rate(len(matched_targets), len(target_rows)),
        "proposal_precision": safe_rate(len(matched_proposals), len(selected_rows)),
        "query_rows": len(query_eval_rows),
        "query_target_detected_rows": target_detected,
        "query_target_detected_rate": safe_rate(target_detected, len(query_eval_rows)),
        "query_top5_success_rows": query_success_top5,
        "query_top5_success_rate": safe_rate(query_success_top5, len(query_eval_rows)),
        "query_top10_success_rows": query_success_top10,
        "query_top10_success_rate": safe_rate(query_success_top10, len(query_eval_rows)),
        "mean_false_positive_before_target": safe_mean(fp_before_values),
    }


def build_target_boundary_rows(
    *,
    target_rows: list[dict[str, Any]],
    pre_cap_matched_rows: list[dict[str, Any]],
    current_target_recall: dict[str, dict[str, Any]],
    current_query_rows: list[dict[str, Any]],
    current_policy_eval: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pre_cap_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    current_eval_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    current_query_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pre_cap_matched_rows:
        if row.get("matched_target_uid"):
            pre_cap_by_target[str(row["matched_target_uid"])].append(row)
    for row in current_policy_eval:
        current_eval_by_target[str(row["target_uid"])].append(row)
    for row in current_query_rows:
        current_query_by_target[str(row["target_uid"])].append(row)

    rows: list[dict[str, Any]] = []
    for target in sorted(target_rows, key=lambda row: str(row["target_uid"])):
        target_uid = str(target["target_uid"])
        pre_cap_hits = pre_cap_by_target.get(target_uid, [])
        recall = current_target_recall.get(target_uid, {})
        current_eval = current_eval_by_target.get(target_uid, [])
        current_queries = current_query_by_target.get(target_uid, [])
        current_ranks = [row["target_rank"] for row in current_eval if row.get("target_rank") is not None]
        current_query_ranks = [
            row.get("query_target_rank_by_real_detector_confidence")
            for row in current_queries
            if row.get("query_target_rank_by_real_detector_confidence") is not None
        ]
        pre_cap_detected = bool(pre_cap_hits)
        current_detected = bool(recall.get("matched"))
        best_current_rank = min(current_ranks) if current_ranks else None
        if not pre_cap_detected:
            repair_class = "prompt_or_detector_recall_miss"
        elif not current_detected:
            repair_class = "selection_or_cap_lost_target"
        elif best_current_rank is not None and best_current_rank > 5:
            repair_class = "rank_or_false_positive_budget_gap"
        else:
            repair_class = "already_top5_or_memory_recovered"
        rows.append(
            {
                "record_type": "e005_m77_target_repair_boundary",
                "target_uid": target_uid,
                "batch_id": target.get("m68_batch_id"),
                "scan_id": target.get("scan_id"),
                "label_canonical": target.get("label_canonical"),
                "pre_cap_detected": pre_cap_detected,
                "pre_cap_matched_candidate_rows": len(pre_cap_hits),
                "current_selected_detected": current_detected,
                "current_best_match_distance_m": recall.get("best_match_distance_m"),
                "current_query_best_rank": min(current_query_ranks) if current_query_ranks else None,
                "current_replay_best_rank": best_current_rank,
                "repair_class": repair_class,
            }
        )
    return rows


def summarize_target_boundaries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row["repair_class"]) for row in rows)
    return {
        "target_rows": len(rows),
        "repair_class_counts": dict(counts),
        "pre_cap_detected_targets": sum(1 for row in rows if row["pre_cap_detected"]),
        "current_selected_detected_targets": sum(1 for row in rows if row["current_selected_detected"]),
        "pre_cap_detected_target_rate": safe_rate(sum(1 for row in rows if row["pre_cap_detected"]), len(rows)),
        "current_selected_detected_target_rate": safe_rate(sum(1 for row in rows if row["current_selected_detected"]), len(rows)),
    }


def build_decision(
    *,
    target_summary: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    m76: dict[str, Any],
) -> dict[str, Any]:
    by_policy = {row["policy_id"]: row for row in policy_rows}
    current = by_policy[CURRENT_POLICY_ID]
    best_top5 = max(policy_rows, key=lambda row: (int(row["query_top5_success_rows"]), -float(row["mean_false_positive_before_target"] or 9999)))
    best_precision = max(policy_rows, key=lambda row: (float(row["proposal_precision"] or 0.0), int(row["query_top5_success_rows"])))
    current_top5 = int(current["query_top5_success_rows"])
    best_top5_delta = int(best_top5["query_top5_success_rows"]) - current_top5
    prompt_miss = int(target_summary["repair_class_counts"].get("prompt_or_detector_recall_miss", 0))
    selection_lost = int(target_summary["repair_class_counts"].get("selection_or_cap_lost_target", 0))
    rank_gap = int(target_summary["repair_class_counts"].get("rank_or_false_positive_budget_gap", 0))

    offline_repair_promising = bool(best_top5_delta >= 5 or selection_lost >= 5)
    prompt_repair_needed = bool(prompt_miss >= 10)
    if offline_repair_promising:
        selected = "offline_replay_repair_candidate_then_targeted_detector_rerun"
        next_unit = "E005-M78 offline repair replay implementation"
        rationale = "Pre-cap pools contain enough recoverable targets or policy delta to justify an offline replay repair before detector rerun."
    elif prompt_repair_needed:
        selected = "prompt_label_or_external_detector_repair_needed"
        next_unit = "E005-M78 prompt/label recall repair plan"
        rationale = "Most missing targets are absent even from the pre-cap pool, so ranking alone cannot create final robustness."
    else:
        selected = "diagnostic_table_only_no_local_repair_gain"
        next_unit = "E006/E007 or external proposal baseline decision"
        rationale = "Offline replay does not show enough gain; use M75/M76 as diagnostic evidence and move to external baselines or navigation."

    return {
        "selected_next_route": selected,
        "next_recommended_unit": next_unit,
        "rationale": rationale,
        "m76_selected_route": m76.get("selected_next_route"),
        "offline_repair_promising": offline_repair_promising,
        "prompt_repair_needed": prompt_repair_needed,
        "current_policy_id": CURRENT_POLICY_ID,
        "best_top5_policy_id": best_top5["policy_id"],
        "best_top5_delta_vs_current": best_top5_delta,
        "best_precision_policy_id": best_precision["policy_id"],
        "target_repair_summary": target_summary,
        "claim_boundary": {
            "m77_is_offline_design_not_new_detector_result": True,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
            "human_intent_main_claim_ready": False,
        },
    }


def build_report(
    coverage: dict[str, Any],
    target_summary: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    decision: dict[str, Any],
) -> str:
    top_rows = sorted(policy_rows, key=lambda row: (-int(row["query_top5_success_rows"]), float(row["mean_false_positive_before_target"] or 9999)))[:5]
    lines = [
        "# E005-M77 Offline Detector / Prompt Repair",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Pre-cap candidate rows: {coverage['pre_cap_candidate_rows']}.",
        f"- Target rows: {coverage['target_rows']}.",
        f"- Query rows: {coverage['query_rows']}.",
        f"- M75 detector top5 query success: {coverage['m75_detector_top5_success_rows']} / {coverage['query_rows']}.",
        f"- Current replay top5 query success: {coverage['current_policy_top5_success_rows']} / {coverage['query_rows']}."
        f" Match with M75 top5: {coverage['current_replay_top5_matches_m75_detector_top5']}.",
        f"- Pre-cap detected targets: {target_summary['pre_cap_detected_targets']} / {target_summary['target_rows']} = {target_summary['pre_cap_detected_target_rate']}.",
        f"- Current selected detected targets: {target_summary['current_selected_detected_targets']} / {target_summary['target_rows']} = {target_summary['current_selected_detected_target_rate']}.",
        f"- Repair class counts: {target_summary['repair_class_counts']}.",
        "",
        "## Policy Sweep",
        "",
        "| Policy | Top5 | Target Detected | Precision | Mean FP Before Target |",
        "| --- | ---: | ---: | ---: | ---: |",
        *[
            f"| `{row['policy_id']}` | {row['query_top5_success_rows']} / {row['query_rows']} | {row['query_target_detected_rows']} / {row['query_rows']} | {row['proposal_precision']} | {row['mean_false_positive_before_target']} |"
            for row in top_rows
        ],
        "",
        "## Decision",
        "",
        f"- Selected route: `{decision['selected_next_route']}`.",
        f"- Next unit: {decision['next_recommended_unit']}.",
        f"- Rationale: {decision['rationale']}",
        "",
        "## Claim Boundary",
        "",
        "- M77 is an offline design artifact over existing candidate pools, not a new detector result.",
        "- M77 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, real navigation `SR` / `SPL`, or human intent as a main claim.",
        "- Any policy selected here must be validated by a fixed replay/rerun protocol before entering a paper main table.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    m68_root = DEFAULT_M68_ROOT
    m69_root = DEFAULT_M69_ROOT
    m71_root = DEFAULT_M71_ROOT
    out_dir = DEFAULT_OUT_DIR
    m75_coverage = read_json(DEFAULT_M75_ROOT / "coverage.json")

    target_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    current_query_rows: list[dict[str, Any]] = []
    current_target_recall: dict[str, dict[str, Any]] = {}
    pre_cap_rows: list[dict[str, Any]] = []
    for batch in BATCHES:
        batch_targets = read_jsonl(m68_root / "batches" / batch / "real_proposal_object_targets.jsonl")
        batch_queries = read_jsonl(m68_root / "batches" / batch / "direct_bridge_query_rows.jsonl")
        batch_pre_cap = read_jsonl(m69_root / batch / "container_output" / "pre_cap_candidate_pool.jsonl")
        batch_current_queries = read_jsonl(m71_root / batch / "query_bridge_rows.jsonl")
        batch_recall = read_jsonl(m69_root / batch / "matching" / "target_recall_rows.jsonl")
        target_rows.extend(batch_targets)
        query_rows.extend(batch_queries)
        current_query_rows.extend(batch_current_queries)
        pre_cap_rows.extend(batch_pre_cap)
        for row in batch_recall:
            current_target_recall[str(row["target_uid"])] = row

    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        targets_by_scan_label[target_key(row)].append(row)

    pre_cap_matched_rows = match_candidates_to_targets(pre_cap_rows, targets_by_scan_label)
    policies = build_policies()
    policy_rows: list[dict[str, Any]] = []
    query_eval_rows: list[dict[str, Any]] = []
    selected_by_policy: dict[str, list[dict[str, Any]]] = {}
    for policy in policies:
        selected = select_policy_candidates(pre_cap_matched_rows, policy)
        selected_by_policy[str(policy["policy_id"])] = selected
        eval_rows: list[dict[str, Any]] = []
        for query in query_rows:
            rank, fp_before, proposal_uid = target_rank(selected, query)
            eval_rows.append(
                {
                    "record_type": "e005_m77_query_policy_eval",
                    "policy_id": policy["policy_id"],
                    "query_uid": query["bridge_query_uid"],
                    "row_uid": query["row_uid"],
                    "target_uid": query["target_uid"],
                    "batch_id": query["m68_batch_id"],
                    "scan_id": query["current_rescan_id"],
                    "label_canonical": query["label_canonical"],
                    "task_context_id": query["task_context_id"],
                    "query_slice_id": "stale_old_dead_end"
                    if query.get("old_location_dead_end_expected")
                    else str(query.get("expected_memory_state")),
                    "target_rank": rank,
                    "target_proposal_uid": proposal_uid,
                    "false_positive_before_target_count": fp_before,
                    "top5_success": rank is not None and rank <= 5,
                    "top10_success": rank is not None and rank <= 10,
                    "target_detected": rank is not None,
                }
            )
        query_eval_rows.extend(eval_rows)
        policy_rows.append(summarize_policy(str(policy["policy_id"]), selected, eval_rows, target_rows))

    current_eval = [row for row in query_eval_rows if row["policy_id"] == CURRENT_POLICY_ID]
    target_boundary_rows = build_target_boundary_rows(
        target_rows=target_rows,
        pre_cap_matched_rows=pre_cap_matched_rows,
        current_target_recall=current_target_recall,
        current_query_rows=current_query_rows,
        current_policy_eval=current_eval,
    )
    target_summary = summarize_target_boundaries(target_boundary_rows)
    m76 = read_json(DEFAULT_M76_ROOT / "route_decision.json")
    decision = build_decision(target_summary=target_summary, policy_rows=policy_rows, m76=m76)

    best = {row["policy_id"]: row for row in policy_rows}[decision["best_top5_policy_id"]]
    coverage = {
        "status": "e005_m77_offline_detector_prompt_repair_design_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pre_cap_candidate_rows": len(pre_cap_rows),
        "target_rows": len(target_rows),
        "query_rows": len(query_rows),
        "policies_evaluated": len(policy_rows),
        "current_policy_id": CURRENT_POLICY_ID,
        "current_policy_top5_success_rows": {row["policy_id"]: row for row in policy_rows}[CURRENT_POLICY_ID][
            "query_top5_success_rows"
        ],
        "m75_query_target_detected_rows": m75_coverage.get("query_target_detected_rows"),
        "m75_detector_top5_success_rows": m75_coverage.get("real_detector_top5_success_rows"),
        "current_replay_top5_matches_m75_detector_top5": {row["policy_id"]: row for row in policy_rows}[CURRENT_POLICY_ID][
            "query_top5_success_rows"
        ]
        == m75_coverage.get("real_detector_top5_success_rows"),
        "best_top5_policy_id": decision["best_top5_policy_id"],
        "best_top5_success_rows": best["query_top5_success_rows"],
        "best_top5_delta_vs_current": decision["best_top5_delta_vs_current"],
        "pre_cap_detected_targets": target_summary["pre_cap_detected_targets"],
        "current_selected_detected_targets": target_summary["current_selected_detected_targets"],
        "target_repair_class_counts": target_summary["repair_class_counts"],
        "offline_repair_promising": decision["offline_repair_promising"],
        "prompt_repair_needed": decision["prompt_repair_needed"],
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "coverage.json", coverage)
    write_json(out_dir / "route_decision.json", decision)
    write_jsonl(out_dir / "policy_summary_rows.jsonl", policy_rows)
    write_csv(out_dir / "policy_summary_rows.csv", policy_rows)
    write_jsonl(out_dir / "query_policy_eval_rows.jsonl", query_eval_rows)
    write_jsonl(out_dir / "target_repair_boundary_rows.jsonl", target_boundary_rows)
    write_jsonl(out_dir / "pre_cap_matched_sample_rows.jsonl", pre_cap_matched_rows[:1000])
    write_text(out_dir / "report.md", build_report(coverage, target_summary, policy_rows, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
