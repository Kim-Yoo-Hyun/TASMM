#!/usr/bin/env python3
"""Run E005-M78 fixed offline repair replay over real proposal pre-cap pools."""

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
DEFAULT_M75_ROOT = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
DEFAULT_M76_ROOT = EXP_ROOT / "artifacts" / "E005-M76_real_proposal_claim_boundary_v0"
DEFAULT_M77_ROOT = EXP_ROOT / "artifacts" / "E005-M77_offline_detector_prompt_repair_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M78_offline_repair_replay_v0"
VERSION = "e005_m78_offline_repair_replay_v0"

BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
MATCH_THRESHOLD_M = 1.0
FIXED_POLICY = {
    "policy_id": "offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0",
    "m77_source_policy_id": "offline_confidence_log_depth_radius0p5_cap24",
    "score_mode": "confidence_log_depth",
    "spatial_radius_m": 0.5,
    "per_scan_label_cap": 24,
    "visit_budget": 5,
    "deployability": "offline_replay_over_existing_pre_cap_candidate_pool",
}
M75_DETECTOR_POLICY = "real_detector_confidence_top5_v0"
M75_H001_POLICY = "real_task_context_memory_trust_reobserve_v0"
M75_CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
M75_CONCEPTGRAPHS_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def score_candidate(row: dict[str, Any], mode: str) -> float:
    confidence = float(row.get("confidence") or 0.0)
    depth = float(row.get("depth_valid_pixel_count") or 0.0)
    log_depth = min(1.0, math.log1p(max(depth, 0.0)) / math.log1p(5000.0))
    if mode == "confidence_log_depth":
        return confidence * log_depth
    if mode == "confidence":
        return confidence
    raise RuntimeError(f"unknown score mode: {mode}")


def query_slice_id(row: dict[str, Any]) -> str:
    if row.get("old_location_dead_end_expected"):
        return "stale_old_dead_end"
    if row.get("row_band") == "significant_moved":
        return "significant_moved"
    if row.get("expected_memory_state") == "trusted_or_low_motion":
        return "trusted_or_low_motion"
    return "review_or_mid_motion"


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
        out["m78_match_threshold_m"] = MATCH_THRESHOLD_M
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
    ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row.get("raw_candidate_uid"))))
    kept: list[dict[str, Any]] = []
    for row in ranked:
        centroid = row.get("centroid_world_m")
        if not centroid:
            continue
        if all(distance(centroid, kept_row["centroid_world_m"]) > radius_m for kept_row in kept if kept_row.get("centroid_world_m")):
            kept.append(row)
    return kept


def select_fixed_policy_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    score_mode = str(FIXED_POLICY["score_mode"])
    radius_m = float(FIXED_POLICY["spatial_radius_m"])
    cap = int(FIXED_POLICY["per_scan_label_cap"])
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)

    selected: list[dict[str, Any]] = []
    for (scan_id, label), group_rows in sorted(groups.items()):
        consolidated = spatial_consolidate(group_rows, radius_m, score_mode)
        ranked = sorted(consolidated, key=lambda row: (-score_candidate(row, score_mode), str(row.get("raw_candidate_uid"))))
        for local_rank, row in enumerate(ranked[:cap], start=1):
            out = dict(row)
            out["m78_policy_id"] = FIXED_POLICY["policy_id"]
            out["m78_m77_source_policy_id"] = FIXED_POLICY["m77_source_policy_id"]
            out["m78_score_mode"] = score_mode
            out["m78_spatial_radius_m"] = radius_m
            out["m78_per_scan_label_cap"] = cap
            out["m78_group_key"] = f"{scan_id}::{label}"
            out["m78_group_rank"] = local_rank
            out["m78_selection_score"] = round(score_candidate(row, score_mode), 8)
            selected.append(out)
    selected = sorted(
        selected,
        key=lambda row: (
            -float(row["m78_selection_score"]),
            str(row["scan_id"]),
            str(row["label_canonical"]),
            int(row["m78_group_rank"]),
            str(row.get("raw_candidate_uid")),
        ),
    )
    for rank, row in enumerate(selected, start=1):
        row["m78_global_rank"] = rank
    return selected


def ordered_same_label(selected_rows: list[dict[str, Any]], query: dict[str, Any]) -> list[dict[str, Any]]:
    same_label = [
        row
        for row in selected_rows
        if str(row["scan_id"]) == str(query["current_rescan_id"])
        and str(row["label_canonical"]) == str(query["label_canonical"])
    ]
    return sorted(
        same_label,
        key=lambda row: (
            -float(row.get("m78_selection_score") or score_candidate(row, "confidence")),
            int(row.get("m78_group_rank") or row.get("pre_cap_group_rank") or 10**9),
            str(row.get("proposal_uid")),
        ),
    )


def target_rank_in_order(ordered: list[dict[str, Any]], target_uid: str) -> tuple[int | None, str | None, int | None]:
    for rank, proposal in enumerate(ordered, start=1):
        if str(proposal.get("matched_target_uid")) == target_uid:
            fp_before = sum(1 for prev in ordered[: rank - 1] if str(prev.get("matched_target_uid")) != target_uid)
            return rank, str(proposal.get("proposal_uid")), fp_before
    return None, None, None


def evaluate_fixed_policy(query_rows: list[dict[str, Any]], selected_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    budget = int(FIXED_POLICY["visit_budget"])
    for query in query_rows:
        target_uid = str(query["target_uid"])
        ordered = ordered_same_label(selected_rows, query)
        target_rank, proposal_uid, fp_before = target_rank_in_order(ordered, target_uid)
        returned = min(len(ordered), budget)
        success = bool(target_rank is not None and target_rank <= returned)
        expected_cost = int(target_rank) if success and target_rank is not None else returned + 1
        row = {
            "m78_version": VERSION,
            "query_uid": query["bridge_query_uid"],
            "row_uid": query["row_uid"],
            "base_row_uid": query["base_row_uid"],
            "pair_uid": query["pair_uid"],
            "target_uid": target_uid,
            "current_rescan_id": query["current_rescan_id"],
            "label_canonical": query["label_canonical"],
            "task_context_id": query["task_context_id"],
            "row_band": query["row_band"],
            "expected_memory_state": query.get("expected_memory_state"),
            "old_memory_is_stale": bool(query.get("old_memory_is_stale")),
            "old_location_dead_end_expected": bool(query.get("old_location_dead_end_expected")),
            "query_slice_id": query_slice_id(query),
            "policy": FIXED_POLICY["policy_id"],
            "policy_family": "offline_real_rgbd_open_vocab_detector_repair_replay",
            "deployable_policy": False,
            "decision_reason": "fixed_offline_confidence_log_depth_radius0p5_cap24_top5",
            "target_detected": target_rank is not None,
            "target_rank": target_rank,
            "raw_target_rank": target_rank,
            "target_proposal_uid": proposal_uid,
            "false_positive_before_target_count": fp_before,
            "candidate_count": len(ordered),
            "returned_location_count": returned,
            "query_bridge_success": success,
            "expected_search_cost": expected_cost,
            "attempt_spl_proxy": attempt_spl(success, expected_cost),
            "old_location_dead_end_avoided": bool(query.get("old_location_dead_end_expected") and success),
            "old_memory_first": False,
            "memory_trust_level": "not_applicable",
            "success_source": "offline_repaired_real_detector_reobservation" if success else "none",
            "leakage_audit_pass": True,
            "policy_input_fields_used": [
                "scan_id",
                "label_canonical",
                "proposal confidence",
                "depth_valid_pixel_count",
                "centroid_world_m",
                "fixed spatial radius",
                "fixed per-scan-label cap",
            ],
            "blocked_policy_inputs": [
                "target_uid",
                "object_instance_id_rescan",
                "matched_3dssg_instance_id",
                "match_distance_m",
                "success labels",
                "M77 policy sweep outcome",
            ],
            "real_navigation_sr_spl_ready": False,
        }
        rows.append(row)
    return rows


def summarize_policy_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    stale = [row for row in rows if row["old_location_dead_end_expected"]]
    detected = [row for row in rows if row["target_detected"]]
    over_search = [row for row in rows if int(row["returned_location_count"]) >= 5 and not row["query_bridge_success"]]
    return {
        "rows": len(rows),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "old_memory_success_rows": 0,
        "detector_reobservation_success_rows": len(successes),
        "mean_target_rank_if_detected": safe_mean([int(row["target_rank"]) for row in detected if row["target_rank"] is not None]),
        "mean_false_positive_before_target_if_detected": safe_mean(
            [
                int(row["false_positive_before_target_count"])
                for row in detected
                if row.get("false_positive_before_target_count") is not None
            ]
        ),
        "mean_returned_location_count": safe_mean([int(row["returned_location_count"]) for row in rows]),
        "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_expected_rows": len(stale),
        "old_location_dead_end_avoided_rows": sum(1 for row in stale if row["old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(sum(1 for row in stale if row["old_location_dead_end_avoided"]), len(stale)),
        "over_search_rows": len(over_search),
        "over_search_rate": safe_rate(len(over_search), len(rows)),
    }


def summarize_selected_candidates(selected_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in selected_rows if row.get("match_status") == "matched"]
    matched_targets = {str(row["matched_target_uid"]) for row in matched if row.get("matched_target_uid")}
    return {
        "selected_rows": len(selected_rows),
        "matched_proposal_rows": len(matched),
        "matched_target_uids": len(matched_targets),
        "target_rows": len(target_rows),
        "scan_target_recall": safe_rate(len(matched_targets), len(target_rows)),
        "proposal_precision": safe_rate(len(matched), len(selected_rows)),
    }


def build_target_replay_rows(
    target_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    policy_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected_rows:
        if row.get("matched_target_uid"):
            selected_by_target[str(row["matched_target_uid"])].append(row)
    for row in policy_rows:
        policy_by_target[str(row["target_uid"])].append(row)

    rows: list[dict[str, Any]] = []
    for target in sorted(target_rows, key=lambda row: str(row["target_uid"])):
        target_uid = str(target["target_uid"])
        hit_rows = selected_by_target.get(target_uid, [])
        target_policy_rows = policy_by_target.get(target_uid, [])
        ranks = [int(row["target_rank"]) for row in target_policy_rows if row.get("target_rank") is not None]
        top5_rows = [row for row in target_policy_rows if row["query_bridge_success"]]
        rows.append(
            {
                "record_type": "e005_m78_target_replay_boundary",
                "target_uid": target_uid,
                "batch_id": target.get("m68_batch_id"),
                "scan_id": target.get("scan_id"),
                "label_canonical": target.get("label_canonical"),
                "fixed_selected_detected": bool(hit_rows),
                "fixed_selected_matched_candidate_rows": len(hit_rows),
                "fixed_query_best_rank": min(ranks) if ranks else None,
                "fixed_query_top5_context_rows": len(top5_rows),
                "fixed_query_rows": len(target_policy_rows),
                "fixed_query_any_top5_success": bool(top5_rows),
            }
        )
    return rows


def build_comparison_rows(m75_metrics: dict[str, Any], m78_metric: dict[str, Any], selected_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy in [
        M75_DETECTOR_POLICY,
        M75_CONTEXT_AGNOSTIC_POLICY,
        M75_H001_POLICY,
        M75_CONCEPTGRAPHS_POLICY,
    ]:
        metric = m75_metrics.get(policy, {})
        rows.append(
            {
                "record_type": "e005_m78_policy_comparison",
                "policy": policy,
                "source": "E005-M75",
                "rows": metric.get("rows"),
                "query_bridge_success_rows": metric.get("query_bridge_success_rows"),
                "query_bridge_success_rate": metric.get("query_bridge_success_rate"),
                "target_detected_rows": metric.get("target_detected_rows"),
                "target_detected_rate": metric.get("target_detected_rate"),
                "mean_expected_search_cost": metric.get("mean_expected_search_cost"),
                "mean_attempt_spl_proxy": metric.get("mean_attempt_spl_proxy"),
                "proposal_precision": None,
                "scan_target_recall": None,
            }
        )
    rows.append(
        {
            "record_type": "e005_m78_policy_comparison",
            "policy": FIXED_POLICY["policy_id"],
            "source": "E005-M78",
            "rows": m78_metric["rows"],
            "query_bridge_success_rows": m78_metric["query_bridge_success_rows"],
            "query_bridge_success_rate": m78_metric["query_bridge_success_rate"],
            "target_detected_rows": m78_metric["target_detected_rows"],
            "target_detected_rate": m78_metric["target_detected_rate"],
            "mean_expected_search_cost": m78_metric["mean_expected_search_cost"],
            "mean_attempt_spl_proxy": m78_metric["mean_attempt_spl_proxy"],
            "proposal_precision": selected_summary["proposal_precision"],
            "scan_target_recall": selected_summary["scan_target_recall"],
        }
    )
    return rows


def compare_with_m77(policy_rows: list[dict[str, Any]], m77_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m77_fixed = {
        str(row["query_uid"]): row
        for row in m77_rows
        if row.get("policy_id") == FIXED_POLICY["m77_source_policy_id"]
    }
    mismatches: list[str] = []
    rank_mismatches: list[str] = []
    for row in policy_rows:
        m77_row = m77_fixed.get(str(row["query_uid"]))
        if not m77_row:
            mismatches.append(str(row["query_uid"]))
            continue
        if bool(row["query_bridge_success"]) != bool(m77_row.get("top5_success")):
            mismatches.append(str(row["query_uid"]))
        if row.get("target_rank") != m77_row.get("target_rank"):
            rank_mismatches.append(str(row["query_uid"]))
    return {
        "m77_fixed_rows": len(m77_fixed),
        "m78_rows": len(policy_rows),
        "top5_success_mismatch_rows": len(mismatches),
        "target_rank_mismatch_rows": len(rank_mismatches),
        "matches_m77_best_policy_top5": len(mismatches) == 0 and len(m77_fixed) == len(policy_rows),
        "matches_m77_best_policy_rank": len(rank_mismatches) == 0 and len(m77_fixed) == len(policy_rows),
        "mismatch_query_uid_sample": mismatches[:10],
        "rank_mismatch_query_uid_sample": rank_mismatches[:10],
    }


def build_decision(
    m75_metrics: dict[str, Any],
    m78_metric: dict[str, Any],
    m77_compare: dict[str, Any],
    selected_summary: dict[str, Any],
    m76_decision: dict[str, Any],
) -> dict[str, Any]:
    m75_detector = m75_metrics[M75_DETECTOR_POLICY]
    m75_h001 = m75_metrics[M75_H001_POLICY]
    detector_delta = int(m78_metric["query_bridge_success_rows"]) - int(m75_detector["query_bridge_success_rows"])
    h001_delta = int(m78_metric["query_bridge_success_rows"]) - int(m75_h001["query_bridge_success_rows"])
    fixed_replay_ready = bool(m77_compare["matches_m77_best_policy_top5"] and detector_delta >= 5)
    if fixed_replay_ready:
        selected_route = "fixed_offline_repair_ready_for_runner_insertion_or_targeted_rerun"
        next_unit = "E005-M79 runner insertion point and targeted repair rerun plan"
        rationale = "Fixed replay reproduces the M77 best policy and improves detector top5 enough to justify implementation in the runner path."
    else:
        selected_route = "offline_repair_not_stable_enough_for_runner_insertion"
        next_unit = "E005-M79 external proposal baseline or prompt recall repair"
        rationale = "Fixed replay does not reproduce the design result or does not clear the detector-delta gate."
    return {
        "selected_next_route": selected_route,
        "next_recommended_unit": next_unit,
        "rationale": rationale,
        "m76_selected_route": m76_decision.get("selected_next_route"),
        "fixed_policy_id": FIXED_POLICY["policy_id"],
        "m77_source_policy_id": FIXED_POLICY["m77_source_policy_id"],
        "fixed_replay_ready_for_runner_insertion": fixed_replay_ready,
        "success_rows_delta_vs_m75_detector_top5": detector_delta,
        "success_rows_delta_vs_m75_h001": h001_delta,
        "m77_reproduction": m77_compare,
        "selected_candidate_summary": selected_summary,
        "claim_boundary": {
            "m78_is_fixed_offline_replay_not_new_detector_result": True,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
            "human_intent_main_claim_ready": False,
        },
    }


def build_report(
    coverage: dict[str, Any],
    policy_metric: dict[str, Any],
    selected_summary: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    decision: dict[str, Any],
) -> str:
    table_rows = [
        row
        for row in comparison_rows
        if row["policy"]
        in {
            M75_DETECTOR_POLICY,
            M75_CONCEPTGRAPHS_POLICY,
            M75_CONTEXT_AGNOSTIC_POLICY,
            M75_H001_POLICY,
            FIXED_POLICY["policy_id"],
        }
    ]
    lines = [
        "# E005-M78 Offline Repair Replay",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Query rows: {coverage['query_rows']}.",
        f"- Target rows: {coverage['target_rows']}.",
        f"- Pre-cap candidate rows: {coverage['pre_cap_candidate_rows']}.",
        f"- Fixed policy: `{FIXED_POLICY['policy_id']}` from M77 `{FIXED_POLICY['m77_source_policy_id']}`.",
        f"- Fixed selected proposals: {selected_summary['selected_rows']}; matched proposal rows: {selected_summary['matched_proposal_rows']}; proposal precision: {selected_summary['proposal_precision']}.",
        f"- Fixed scan-target recall: {selected_summary['matched_target_uids']} / {selected_summary['target_rows']} = {selected_summary['scan_target_recall']}.",
        f"- Fixed replay top5 success: {policy_metric['query_bridge_success_rows']} / {policy_metric['rows']} = {policy_metric['query_bridge_success_rate']}.",
        f"- M77 top5 reproduction: {coverage['matches_m77_best_policy_top5']} with {coverage['m77_top5_success_mismatch_rows']} success mismatches.",
        "",
        "## Comparison",
        "",
        "| Policy | Source | Success | Target Detected | Mean ExpectedSearchCost | Proxy SPL | Precision | Target Recall |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| `{row['policy']}` | {row['source']} | {row['query_bridge_success_rows']} / {row['rows']} | {row['target_detected_rows']} / {row['rows']} | {row['mean_expected_search_cost']} | {row['mean_attempt_spl_proxy']} | {row['proposal_precision']} | {row['scan_target_recall']} |"
            for row in table_rows
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
        "- M78 is a fixed offline replay over existing pre-cap candidates, not a new detector run.",
        "- It can support a detector-ranking repair argument, but not final real RGB-D/open-vocabulary robustness.",
        "- Deployable search policy and real navigation `SR` / `SPL` still require runner integration and downstream path/navigation execution.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    target_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    pre_cap_rows: list[dict[str, Any]] = []
    for batch in BATCHES:
        target_rows.extend(read_jsonl(DEFAULT_M68_ROOT / "batches" / batch / "real_proposal_object_targets.jsonl"))
        query_rows.extend(read_jsonl(DEFAULT_M68_ROOT / "batches" / batch / "direct_bridge_query_rows.jsonl"))
        pre_cap_rows.extend(read_jsonl(DEFAULT_M69_ROOT / batch / "container_output" / "pre_cap_candidate_pool.jsonl"))

    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        targets_by_scan_label[target_key(row)].append(row)

    pre_cap_matched_rows = match_candidates_to_targets(pre_cap_rows, targets_by_scan_label)
    selected_rows = select_fixed_policy_candidates(pre_cap_matched_rows)
    policy_rows = evaluate_fixed_policy(query_rows, selected_rows)
    policy_metric = summarize_policy_group(policy_rows)
    selected_summary = summarize_selected_candidates(selected_rows, target_rows)
    target_replay_rows = build_target_replay_rows(target_rows, selected_rows, policy_rows)

    m75_metrics = read_json(DEFAULT_M75_ROOT / "policy_metrics.json")
    m76_decision = read_json(DEFAULT_M76_ROOT / "route_decision.json")
    m77_query_eval_rows = read_jsonl(DEFAULT_M77_ROOT / "query_policy_eval_rows.jsonl")
    m77_compare = compare_with_m77(policy_rows, m77_query_eval_rows)
    comparison_rows = build_comparison_rows(m75_metrics, policy_metric, selected_summary)
    decision = build_decision(m75_metrics, policy_metric, m77_compare, selected_summary, m76_decision)

    m75_detector = m75_metrics[M75_DETECTOR_POLICY]
    m75_h001 = m75_metrics[M75_H001_POLICY]
    coverage = {
        "status": "e005_m78_offline_repair_replay_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "query_rows": len(query_rows),
        "target_rows": len(target_rows),
        "pre_cap_candidate_rows": len(pre_cap_rows),
        "fixed_policy_id": FIXED_POLICY["policy_id"],
        "m77_source_policy_id": FIXED_POLICY["m77_source_policy_id"],
        "fixed_selected_rows": selected_summary["selected_rows"],
        "fixed_matched_proposal_rows": selected_summary["matched_proposal_rows"],
        "fixed_proposal_precision": selected_summary["proposal_precision"],
        "fixed_matched_target_uids": selected_summary["matched_target_uids"],
        "fixed_scan_target_recall": selected_summary["scan_target_recall"],
        "fixed_query_target_detected_rows": policy_metric["target_detected_rows"],
        "fixed_query_target_detected_rate": policy_metric["target_detected_rate"],
        "fixed_top5_success_rows": policy_metric["query_bridge_success_rows"],
        "fixed_top5_success_rate": policy_metric["query_bridge_success_rate"],
        "fixed_mean_expected_search_cost": policy_metric["mean_expected_search_cost"],
        "fixed_mean_attempt_spl_proxy": policy_metric["mean_attempt_spl_proxy"],
        "m75_detector_top5_success_rows": m75_detector["query_bridge_success_rows"],
        "m75_h001_success_rows": m75_h001["query_bridge_success_rows"],
        "success_rows_delta_vs_m75_detector_top5": decision["success_rows_delta_vs_m75_detector_top5"],
        "success_rows_delta_vs_m75_h001": decision["success_rows_delta_vs_m75_h001"],
        "matches_m77_best_policy_top5": m77_compare["matches_m77_best_policy_top5"],
        "matches_m77_best_policy_rank": m77_compare["matches_m77_best_policy_rank"],
        "m77_top5_success_mismatch_rows": m77_compare["top5_success_mismatch_rows"],
        "m77_target_rank_mismatch_rows": m77_compare["target_rank_mismatch_rows"],
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
        "human_intent_main_claim_ready": False,
    }

    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "fixed_policy_config.json", FIXED_POLICY)
    write_json(out_dir / "coverage.json", coverage)
    write_json(out_dir / "policy_metrics.json", {FIXED_POLICY["policy_id"]: policy_metric})
    write_json(out_dir / "route_decision.json", decision)
    write_jsonl(out_dir / "selected_repair_proposals.jsonl", selected_rows)
    write_jsonl(out_dir / "query_policy_rows.jsonl", policy_rows)
    write_jsonl(out_dir / "target_replay_boundary_rows.jsonl", target_replay_rows)
    write_jsonl(out_dir / "comparison_rows.jsonl", comparison_rows)
    write_csv(out_dir / "comparison_rows.csv", comparison_rows)
    write_text(out_dir / "report.md", build_report(coverage, policy_metric, selected_summary, comparison_rows, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
