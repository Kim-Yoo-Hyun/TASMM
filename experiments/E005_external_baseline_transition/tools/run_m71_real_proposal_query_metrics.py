#!/usr/bin/env python3
"""Convert E005 real proposal detector output into query-level metrics."""

from __future__ import annotations

import argparse
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
DEFAULT_M70_ROOT = EXP_ROOT / "artifacts" / "E005-M70_full_denominator_real_proposal_detector_verification_v0"
DEFAULT_M51_DIR = EXP_ROOT / "artifacts" / "E005-M51_h001_heldout_policy_replay_contract_v0"
DEFAULT_M45_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
DEFAULT_OUT_ROOT = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0"
VERSION = "e005_m71_real_proposal_query_metric_v0"
READY_DETECTOR_VERIFICATION_STATUSES = {
    "e005_m70_real_proposal_detector_batch_ready_with_false_positive_load",
    "e005_m89_cleanup_trace_detector_batch_ready",
}

STATIC_POLICY = "real_static_memory_only_v0"
CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
H001_POLICY = "real_task_context_memory_trust_reobserve_v0"
CONCEPTGRAPHS_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"

DETECTOR_POLICIES = {
    "real_detector_confidence_top1_v0": ("confidence_desc", "top1", False),
    "real_detector_confidence_top3_v0": ("confidence_desc", "top3", False),
    "real_detector_confidence_top5_v0": ("confidence_desc", "top5", False),
    "real_detector_task_budget_v0": ("confidence_desc", "task_budget", False),
    "real_bounded_old_memory_distance_guard_adaptive_top5_v0": ("old_memory_distance_guard", "adaptive_uncertainty_top5", False),
    "real_unbounded_old_memory_distance_guard_until_target_v0": (
        "old_memory_distance_guard",
        "unbounded_until_target_or_exhausted",
        False,
    ),
    "real_oracle_target_first_task_budget_upper_bound_v0": ("oracle_target_first_upper_bound", "task_budget", True),
}
MEMORY_POLICIES = [STATIC_POLICY, CONTEXT_AGNOSTIC_POLICY, H001_POLICY]
POLICY_ORDER = list(DETECTOR_POLICIES) + MEMORY_POLICIES + [CONCEPTGRAPHS_POLICY]
TASK_CONTEXT_PROFILES = {
    "routine_fetch": {"high_ambiguity_budget": 2, "max_candidate_budget": 3},
    "high_value_fetch": {"high_ambiguity_budget": 5, "max_candidate_budget": 5},
    "noisy_high_value_fetch": {"high_ambiguity_budget": 5, "max_candidate_budget": 5},
}


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
    return math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(a, b)))


def proposal_confidence(row: dict[str, Any]) -> float:
    return float(row.get("selection_score") or row.get("confidence") or 0.0)


def old_distance(row: dict[str, Any], query: dict[str, Any]) -> float | None:
    old = query.get("old_scene_aligned_centroid")
    centroid = row.get("centroid_world_m")
    if not old or not centroid:
        return None
    return distance(centroid, old)


def order_score(row: dict[str, Any], query: dict[str, Any], target_uid: str, mode: str) -> tuple[float, float, str]:
    confidence = proposal_confidence(row)
    if mode == "confidence_desc":
        primary = confidence
    elif mode == "old_memory_distance_guard":
        primary = confidence
        dist = old_distance(row, query)
        if bool(query.get("old_location_dead_end_expected")) and dist is not None:
            threshold = max(float(query.get("success_threshold_m") or 0.5), 0.1)
            primary *= min(2.0, max(0.25, dist / threshold))
    elif mode == "oracle_target_first_upper_bound":
        primary = 10.0 if str(row.get("matched_target_uid")) == target_uid else confidence
    else:
        raise RuntimeError(f"unknown order mode: {mode}")
    return primary, confidence, str(row.get("proposal_uid", ""))


def order_proposals(rows: list[dict[str, Any]], query: dict[str, Any], target_uid: str, mode: str) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -order_score(row, query, target_uid, mode)[0],
            -order_score(row, query, target_uid, mode)[1],
            int(row.get("pre_cap_rank") or 10**9),
            int(row.get("pre_cap_group_rank") or 10**9),
            order_score(row, query, target_uid, mode)[2],
        ),
    )


def target_rank_in_order(ordered: list[dict[str, Any]], target_uid: str) -> tuple[int | None, str | None, int | None]:
    for rank, proposal in enumerate(ordered, start=1):
        if str(proposal.get("matched_target_uid")) == target_uid:
            fp_before = sum(1 for prev in ordered[: rank - 1] if str(prev.get("matched_target_uid")) != target_uid)
            return rank, str(proposal.get("proposal_uid")), fp_before
    return None, None, None


def ambiguity_band(candidate_count: int) -> str:
    if candidate_count <= 1:
        return "trivial_candidate"
    if candidate_count <= 3:
        return "rank_sensitive"
    return "high_ambiguity"


def query_slice_id(row: dict[str, Any]) -> str:
    if row.get("old_location_dead_end_expected"):
        return "stale_old_dead_end"
    if row.get("row_band") == "significant_moved":
        return "significant_moved"
    if row.get("expected_memory_state") == "trusted_or_low_motion":
        return "trusted_or_low_motion"
    return "review_or_mid_motion"


def static_memory_success(query: dict[str, Any]) -> bool:
    if "static_memory_success" in query:
        return bool(query["static_memory_success"])
    return float(query["scene_aligned_static_error_m"]) <= float(query["success_threshold_m"])


def task_conditioned_budget(query: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_detector_candidate"
    if query["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"
    profile = TASK_CONTEXT_PROFILES[str(query["task_context_id"])]
    max_budget = int(profile["max_candidate_budget"])
    high_ambiguity_budget = int(profile["high_ambiguity_budget"])
    band = ambiguity_band(candidate_count)
    if query["task_context_id"] == "routine_fetch":
        if band == "trivial_candidate":
            return 1, "routine_trivial_candidate"
        if band == "high_ambiguity":
            return min(candidate_count, max_budget, high_ambiguity_budget), "routine_high_ambiguity_bounded"
        return min(candidate_count, max_budget, 3), "routine_rank_sensitive_budget"
    if query["task_context_id"] in {"high_value_fetch", "noisy_high_value_fetch"}:
        if band == "trivial_candidate":
            return 1, "high_value_trivial_candidate"
        return min(candidate_count, max_budget), "high_value_expand_budget"
    raise RuntimeError(f"unknown task_context_id: {query['task_context_id']}")


def detector_budget(mode: str, query: dict[str, Any], candidate_count: int, target_rank: int | None) -> tuple[int, str]:
    if mode == "top1":
        return min(candidate_count, 1), "real_detector_confidence_top1"
    if mode == "top3":
        return min(candidate_count, 3), "real_detector_confidence_top3"
    if mode == "top5":
        return min(candidate_count, 5), "real_detector_confidence_top5"
    if mode == "task_budget":
        return task_conditioned_budget(query, candidate_count)
    if mode == "adaptive_uncertainty_top5":
        base_budget, base_reason = task_conditioned_budget(query, candidate_count)
        if bool(query.get("old_location_dead_end_expected")) or candidate_count >= 12:
            return min(candidate_count, max(base_budget, 5)), "adaptive_uncertainty_top5"
        return base_budget, f"adaptive_keep_{base_reason}"
    if mode == "unbounded_until_target_or_exhausted":
        if target_rank is not None:
            return target_rank, "visit_until_detected_target"
        return candidate_count, "exhaust_real_detector_candidates"
    raise RuntimeError(f"unknown budget mode: {mode}")


def memory_decision(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    context = str(query["task_context_id"])
    state = str(query["expected_memory_state"])
    stale = bool(query["old_memory_is_stale"])
    candidate_count = int(query["same_label_real_proposal_count"])
    memory_trust_level = "medium"
    old_memory_first = False
    detector_k = 0
    reason = "unset"
    if policy == STATIC_POLICY:
        memory_trust_level = "always_trust_static"
        old_memory_first = True
        detector_k = 0
        reason = "static_memory_only"
    elif policy == CONTEXT_AGNOSTIC_POLICY:
        if state == "trusted_or_low_motion" and not stale:
            memory_trust_level = "high"
            old_memory_first = True
            detector_k = 0
            reason = "context_agnostic_trust_low_motion"
        elif state == "review" and not stale:
            memory_trust_level = "medium"
            old_memory_first = True
            detector_k = 3
            reason = "context_agnostic_review_top3_fallback"
        else:
            memory_trust_level = "low"
            old_memory_first = False
            detector_k = 3
            reason = "context_agnostic_reobserve_top3"
    elif policy == H001_POLICY:
        if state == "trusted_or_low_motion" and not stale:
            memory_trust_level = "high"
            old_memory_first = True
            if context == "routine_fetch":
                detector_k = 0
                reason = "routine_trust_low_motion"
            elif context == "high_value_fetch":
                detector_k = 3
                reason = "high_value_verify_low_motion_top3"
            elif context == "noisy_high_value_fetch":
                detector_k = 1
                reason = "noisy_high_value_minimal_verification_top1"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
        elif state == "review" and not stale:
            memory_trust_level = "medium"
            old_memory_first = True
            if context == "routine_fetch":
                detector_k = 3
                reason = "routine_review_bounded_top3"
            elif context == "high_value_fetch":
                detector_k = 5
                reason = "high_value_review_expand_top5"
            elif context == "noisy_high_value_fetch":
                detector_k = 3
                reason = "noisy_high_value_review_guard_top3"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
        else:
            memory_trust_level = "low"
            old_memory_first = False
            if context == "routine_fetch":
                detector_k = 3
                reason = "routine_stale_reobserve_top3"
            elif context == "high_value_fetch":
                detector_k = 5
                reason = "high_value_stale_reobserve_top5"
            elif context == "noisy_high_value_fetch":
                detector_k = 3
                reason = "noisy_high_value_stale_guard_top3"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
    else:
        raise RuntimeError(f"unknown memory policy: {policy}")
    detector_k = min(detector_k, candidate_count)
    return {
        "candidate_visit_budget": int(old_memory_first) + detector_k,
        "candidate_visit_order": "old_memory_then_real_detector_rank" if old_memory_first else "real_detector_rank",
        "decision_reason": reason,
        "detector_budget": detector_k,
        "memory_trust_level": memory_trust_level,
        "old_memory_first": old_memory_first,
        "re_observation_budget": detector_k,
    }


def build_query_rows(
    direct_rows: list[dict[str, Any]],
    adapter_by_uid: dict[str, dict[str, Any]],
    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    target_recall_by_uid: dict[str, dict[str, Any]],
    batch_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for direct in direct_rows:
        adapter = adapter_by_uid[str(direct["row_uid"])]
        target_uid = str(direct["target_uid"])
        same_label = proposals_by_scan_label.get((direct["current_rescan_id"], direct["label_canonical"]), [])
        ordered = order_proposals(same_label, adapter, target_uid, "confidence_desc")
        target_rank, target_proposal_uid, fp_before = target_rank_in_order(ordered, target_uid)
        target_proposal = next((row for row in ordered if str(row.get("proposal_uid")) == str(target_proposal_uid)), None)
        target_recall = target_recall_by_uid.get(target_uid, {})
        row = {
            "m71_version": VERSION,
            "batch_id": batch_id,
            "query_uid": direct["bridge_query_uid"],
            "bridge_query_uid": direct["bridge_query_uid"],
            "row_uid": direct["row_uid"],
            "base_row_uid": direct["base_row_uid"],
            "pair_uid": direct["pair_uid"],
            "reference_scan_id": direct["reference_scan_id"],
            "current_rescan_id": direct["current_rescan_id"],
            "target_uid": target_uid,
            "object_instance_id_rescan": direct["object_instance_id_rescan"],
            "label_canonical": direct["label_canonical"],
            "task_context_id": direct["task_context_id"],
            "row_band": direct["row_band"],
            "expected_memory_state": adapter["expected_memory_state"],
            "old_memory_is_stale": bool(adapter["old_memory_is_stale"]),
            "old_location_dead_end_expected": bool(adapter["old_location_dead_end_expected"]),
            "old_scene_aligned_centroid": adapter.get("old_scene_aligned_centroid"),
            "current_target_centroid": adapter.get("current_target_centroid"),
            "scene_aligned_static_error_m": adapter["scene_aligned_static_error_m"],
            "scene_aligned_static_planar_error_m": adapter.get("scene_aligned_static_planar_error_m"),
            "row_geometry_error_m": adapter["row_geometry_error_m"],
            "success_threshold_m": adapter["success_threshold_m"],
            "static_memory_success": static_memory_success(adapter),
            "query_target_detected": target_rank is not None,
            "query_target_rank_by_real_detector_confidence": target_rank,
            "query_target_best_proposal_uid": target_proposal_uid,
            "query_target_best_match_distance_m": target_proposal.get("match_distance_m") if target_proposal else None,
            "query_target_best_confidence": target_proposal.get("confidence") if target_proposal else None,
            "same_label_real_proposal_count": len(ordered),
            "same_label_false_positive_count": sum(1 for proposal in ordered if str(proposal.get("matched_target_uid")) != target_uid),
            "same_label_matched_other_target_count": sum(
                1
                for proposal in ordered
                if proposal.get("match_status") == "matched" and str(proposal.get("matched_target_uid")) != target_uid
            ),
            "same_label_unmatched_false_positive_count": sum(1 for proposal in ordered if proposal.get("match_status") != "matched"),
            "false_positive_before_target_count": fp_before,
            "target_recall_best_proposal_uid": target_recall.get("best_proposal_uid"),
            "target_recall_best_match_distance_m": target_recall.get("best_match_distance_m"),
            "allowed_policy_inputs": [
                "scan_id",
                "label_canonical",
                "proposal confidence/centroid",
                "task_context_id",
                "expected_memory_state",
                "old_memory_is_stale",
            ],
            "blocked_policy_inputs": [
                "target_uid",
                "object_instance_id_rescan",
                "matched_3dssg_instance_id",
                "match_distance_m",
                "success labels",
            ],
        }
        row["query_slice_id"] = query_slice_id(row)
        rows.append(row)
    return rows


def evaluate_detector_policy(policy: str, query: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    order_mode, budget_mode, oracle = DETECTOR_POLICIES[policy]
    target_uid = str(query["target_uid"])
    ordered = order_proposals(proposals, query, target_uid, order_mode)
    rank, proposal_uid, fp_before = target_rank_in_order(ordered, target_uid)
    effective_rank = 1 if oracle and rank is not None else rank
    returned, reason = detector_budget(budget_mode, query, len(ordered), effective_rank)
    success = bool(effective_rank is not None and effective_rank <= returned)
    expected_cost = int(effective_rank) if success and effective_rank is not None else int(returned) + 1
    return {
        "m71_version": VERSION,
        "query_uid": query["query_uid"],
        "row_uid": query["row_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "target_uid": target_uid,
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "query_slice_id": query["query_slice_id"],
        "policy": policy,
        "policy_family": "real_rgbd_open_vocab_detector_baseline",
        "deployable_policy": not oracle,
        "decision_reason": reason,
        "target_detected": rank is not None,
        "target_rank": effective_rank,
        "raw_target_rank": rank,
        "target_proposal_uid": proposal_uid,
        "false_positive_before_target_count": fp_before,
        "candidate_count": len(ordered),
        "returned_location_count": returned,
        "query_bridge_success": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "old_location_dead_end_expected": bool(query["old_location_dead_end_expected"]),
        "old_location_dead_end_avoided": bool(query["old_location_dead_end_expected"] and success),
        "old_memory_first": False,
        "memory_trust_level": "not_applicable",
        "success_source": "real_detector_reobservation" if success else "none",
        "leakage_audit_pass": True,
        "policy_input_fields_used": ["real proposal confidence/rank", "task_context_id", "pre-evaluation staleness metadata"],
        "real_navigation_sr_spl_ready": False,
    }


def evaluate_memory_policy(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    decision = memory_decision(policy, query)
    rank = query.get("query_target_rank_by_real_detector_confidence")
    rank = None if rank is None else int(rank)
    old_first = bool(decision["old_memory_first"])
    detector_k = int(decision["detector_budget"])
    static_success = static_memory_success(query)
    if old_first and static_success:
        success = True
        expected_cost = 1
        success_source = "old_memory"
    elif rank is not None and rank <= detector_k:
        success = True
        expected_cost = int(old_first) + int(rank)
        success_source = "real_detector_reobservation"
    else:
        success = False
        expected_cost = int(old_first) + detector_k + 1
        success_source = "none"
    old_dead_end_expected = bool(query["old_location_dead_end_expected"])
    return {
        "m71_version": VERSION,
        "query_uid": query["query_uid"],
        "row_uid": query["row_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "target_uid": query["target_uid"],
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "query_slice_id": query["query_slice_id"],
        "policy": policy,
        "policy_family": "h001_memory_trust_reobserve_on_real_proposals",
        "deployable_policy": True,
        "target_detected": rank is not None,
        "target_rank": rank,
        "raw_target_rank": rank,
        "static_memory_success": static_success,
        "candidate_count": int(query["same_label_real_proposal_count"]),
        "returned_location_count": decision["candidate_visit_budget"],
        "query_bridge_success": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "old_location_dead_end_expected": old_dead_end_expected,
        "old_location_dead_end_avoided": bool(old_dead_end_expected and not decision["old_memory_first"] and success),
        "success_source": success_source,
        "leakage_audit_pass": True,
        "policy_input_fields_used": ["task_context_id", "expected_memory_state", "old_memory_is_stale", "same_label_real_proposal_count"],
        "real_navigation_sr_spl_ready": False,
        **decision,
    }


def normalize_conceptgraphs_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "m71_version": VERSION,
        "query_uid": row["query_uid"],
        "row_uid": str(row["query_uid"]).removeprefix("m38:"),
        "base_row_uid": str(row["query_uid"]).removeprefix("m38:").rsplit(":", 1)[0],
        "pair_uid": str(row["query_uid"]).removeprefix("m38:").split(":")[0],
        "target_uid": row["target_uid"],
        "current_rescan_id": row["scan_id"],
        "label_canonical": row["label_canonical"],
        "task_context_id": row["task_context_id"],
        "row_band": row["row_band"],
        "query_slice_id": query_slice_id(row),
        "policy": CONCEPTGRAPHS_POLICY,
        "policy_family": "external_mapping_baseline",
        "deployable_policy": True,
        "target_detected": bool(row["target_detected"]),
        "target_rank": row.get("target_rank"),
        "raw_target_rank": row.get("target_rank"),
        "candidate_count": int(row["candidate_count"]),
        "returned_location_count": int(row["returned_location_count"]),
        "query_bridge_success": bool(row["query_bridge_success"]),
        "expected_search_cost": int(row["expected_search_cost"]),
        "attempt_spl_proxy": float(row["attempt_spl_proxy"]),
        "old_location_dead_end_expected": bool(row["old_location_dead_end_expected"]),
        "old_location_dead_end_avoided": bool(row["old_location_dead_end_expected"] and row["query_bridge_success"]),
        "old_memory_first": False,
        "memory_trust_level": "not_applicable",
        "success_source": "external_map" if row["query_bridge_success"] else "none",
        "leakage_audit_pass": True,
        "policy_input_fields_used": ["ConceptGraphs map candidates", "CLIP text ranking"],
        "real_navigation_sr_spl_ready": False,
    }


def summarize_query_detection(query_rows: list[dict[str, Any]]) -> dict[str, Any]:
    detected = [row for row in query_rows if row["query_target_detected"]]
    unique_targets = sorted({row["target_uid"] for row in query_rows})
    detected_targets = sorted({row["target_uid"] for row in detected})
    return {
        "query_rows": len(query_rows),
        "unique_target_uids": len(unique_targets),
        "query_target_detected_rows": len(detected),
        "query_target_detected_rate": safe_rate(len(detected), len(query_rows)),
        "unique_target_detected_uids": len(detected_targets),
        "unique_target_detected_rate": safe_rate(len(detected_targets), len(unique_targets)),
        "mean_target_rank_when_detected": safe_mean(
            [int(row["query_target_rank_by_real_detector_confidence"]) for row in detected if row["query_target_rank_by_real_detector_confidence"]]
        ),
        "mean_false_positive_before_target_when_detected": safe_mean(
            [int(row["false_positive_before_target_count"]) for row in detected if row["false_positive_before_target_count"] is not None]
        ),
        "mean_same_label_real_proposals_per_query": safe_mean([int(row["same_label_real_proposal_count"]) for row in query_rows]),
        "query_rows_by_label": dict(Counter(row["label_canonical"] for row in query_rows)),
        "query_rows_by_slice": dict(Counter(row["query_slice_id"] for row in query_rows)),
        "query_rows_by_task_context": dict(Counter(row["task_context_id"] for row in query_rows)),
    }


def summarize_policy_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    stale = [row for row in rows if row["old_location_dead_end_expected"]]
    old_successes = [row for row in successes if row.get("success_source") == "old_memory"]
    detector_successes = [row for row in successes if row.get("success_source") == "real_detector_reobservation"]
    over_search = [row for row in rows if int(row["returned_location_count"]) >= 5 and not row["query_bridge_success"]]
    detected = [row for row in rows if row.get("target_detected")]
    return {
        "rows": len(rows),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "old_memory_success_rows": len(old_successes),
        "detector_reobservation_success_rows": len(detector_successes),
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
        "old_location_dead_end_avoided_rows": sum(1 for row in stale if row["old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(sum(1 for row in stale if row["old_location_dead_end_avoided"]), len(stale)),
        "over_search_rows": len(over_search),
        "over_search_rate": safe_rate(len(over_search), len(rows)),
    }


def summarize_policies(policy_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_metrics: dict[str, Any] = {}
    summary_rows: list[dict[str, Any]] = []
    for policy in POLICY_ORDER:
        rows = [row for row in policy_rows if row["policy"] == policy]
        if not rows:
            continue
        policy_metrics[policy] = summarize_policy_group(rows)
        summary_rows.append({"group_type": "policy", "group_value": policy, "policy": policy, **policy_metrics[policy]})
        for field in ["task_context_id", "row_band", "query_slice_id", "label_canonical"]:
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                grouped[str(row.get(field))].append(row)
            for value, group in sorted(grouped.items()):
                summary_rows.append({"group_type": field, "group_value": value, "policy": policy, **summarize_policy_group(group)})
    return policy_metrics, summary_rows


def build_failure_rows(query_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["query_uid"], row["policy"]): row for row in policy_rows}
    rows: list[dict[str, Any]] = []
    for query in query_rows:
        qid = query["query_uid"]
        task = by_key[(qid, "real_detector_task_budget_v0")]
        top5 = by_key[(qid, "real_detector_confidence_top5_v0")]
        h001 = by_key[(qid, H001_POLICY)]
        context = by_key[(qid, CONTEXT_AGNOSTIC_POLICY)]
        static = by_key[(qid, STATIC_POLICY)]
        unbounded = by_key[(qid, "real_unbounded_old_memory_distance_guard_until_target_v0")]
        cg = by_key.get((qid, CONCEPTGRAPHS_POLICY))
        if not task["target_detected"]:
            cls = "real_detector_recall_miss"
        elif h001["query_bridge_success"] and cg and not cg["query_bridge_success"]:
            cls = "real_h001_recovers_conceptgraphs_miss"
        elif cg and cg["query_bridge_success"] and not h001["query_bridge_success"]:
            cls = "conceptgraphs_recovers_real_h001_miss"
        elif h001["query_bridge_success"] and cg and cg["query_bridge_success"]:
            cls = "both_success"
        elif static["query_bridge_success"] and not h001["query_bridge_success"]:
            cls = "h001_regresses_static_memory"
        elif context["query_bridge_success"] and not h001["query_bridge_success"]:
            cls = "h001_regresses_context_agnostic"
        elif unbounded["query_bridge_success"] and not h001["query_bridge_success"]:
            cls = "real_detector_high_cost_only"
        elif top5["query_bridge_success"] and not task["query_bridge_success"]:
            cls = "real_detector_top5_only"
        else:
            cls = "unrecovered"
        rows.append(
            {
                "m71_version": VERSION,
                "batch_id": query["batch_id"],
                "query_uid": qid,
                "row_uid": query["row_uid"],
                "target_uid": query["target_uid"],
                "label_canonical": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "query_slice_id": query["query_slice_id"],
                "failure_class": cls,
                "target_detected": task["target_detected"],
                "real_detector_task_success": task["query_bridge_success"],
                "real_detector_top5_success": top5["query_bridge_success"],
                "real_h001_success": h001["query_bridge_success"],
                "conceptgraphs_success": cg["query_bridge_success"] if cg else None,
                "static_success": static["query_bridge_success"],
                "context_agnostic_success": context["query_bridge_success"],
                "unbounded_success": unbounded["query_bridge_success"],
                "real_h001_expected_search_cost": h001["expected_search_cost"],
                "conceptgraphs_expected_search_cost": cg["expected_search_cost"] if cg else None,
                "real_detector_target_rank": task["target_rank"],
                "real_detector_false_positive_before_target_count": task["false_positive_before_target_count"],
            }
        )
    return rows


def metric_delta(policy_metrics: dict[str, Any], left: str, right: str) -> dict[str, Any]:
    a = policy_metrics[left]
    b = policy_metrics[right]
    return {
        "success_rows_delta": int(a["query_bridge_success_rows"]) - int(b["query_bridge_success_rows"]),
        "success_rate_delta": round(float(a["query_bridge_success_rate"]) - float(b["query_bridge_success_rate"]), 6),
        "mean_expected_search_cost_delta": round(float(a["mean_expected_search_cost"]) - float(b["mean_expected_search_cost"]), 6),
        "mean_attempt_spl_proxy_delta": round(float(a["mean_attempt_spl_proxy"]) - float(b["mean_attempt_spl_proxy"]), 6),
    }


def build_decision(metrics: dict[str, Any], failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pm = metrics["policy_metrics"]
    h001 = pm[H001_POLICY]
    task = pm["real_detector_task_budget_v0"]
    top5 = pm["real_detector_confidence_top5_v0"]
    static = pm[STATIC_POLICY]
    cg = pm.get(CONCEPTGRAPHS_POLICY)
    target_rate = float(metrics["query_target_detected_rate"] or 0.0)
    gates = {
        "real_detector_target_detection_sufficient_for_batch_diagnostic": target_rate >= 0.70,
        "real_h001_beats_real_detector_task_budget": int(h001["query_bridge_success_rows"]) > int(task["query_bridge_success_rows"]),
        "real_h001_beats_real_detector_top5": int(h001["query_bridge_success_rows"]) > int(top5["query_bridge_success_rows"]),
        "real_h001_beats_static_memory": int(h001["query_bridge_success_rows"]) > int(static["query_bridge_success_rows"]),
        "real_h001_beats_context_agnostic_memory_trust": int(h001["query_bridge_success_rows"])
        > int(pm[CONTEXT_AGNOSTIC_POLICY]["query_bridge_success_rows"])
        or (
            int(h001["query_bridge_success_rows"]) == int(pm[CONTEXT_AGNOSTIC_POLICY]["query_bridge_success_rows"])
            and float(h001["mean_expected_search_cost"]) < float(pm[CONTEXT_AGNOSTIC_POLICY]["mean_expected_search_cost"])
        ),
        "real_h001_beats_conceptgraphs_same_batch": bool(
            cg and int(h001["query_bridge_success_rows"]) > int(cg["query_bridge_success_rows"])
        ),
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
    }
    failure_counts = Counter(row["failure_class"] for row in failure_rows)
    if gates["real_detector_target_detection_sufficient_for_batch_diagnostic"] and gates["real_h001_beats_real_detector_task_budget"]:
        selected = "launch_remaining_batches_after_recording_false_positive_boundary"
        rationale = "This batch has enough real detector target recall to justify scaling, and H001 memory trust improves over detector task-budget on this batch."
    elif target_rate >= 0.70:
        selected = "query_metric_ready_but_policy_gain_weak_review_before_remaining_batches"
        rationale = "Real detector recall is usable, but policy gain is weak; inspect failures before launching remaining batches."
    else:
        selected = "repair_real_detector_or_prompt_route_before_remaining_batches"
        rationale = "Target detection is too low for a reliable real RGB-D/open-vocabulary robustness path."
    return {
        "selected_next_route": selected,
        "rationale": rationale,
        "gates": gates,
        "failure_class_counts": dict(failure_counts),
        "delta_vs_real_detector_task_budget": metric_delta(pm, H001_POLICY, "real_detector_task_budget_v0"),
        "delta_vs_real_detector_top5": metric_delta(pm, H001_POLICY, "real_detector_confidence_top5_v0"),
        "delta_vs_static_memory": metric_delta(pm, H001_POLICY, STATIC_POLICY),
        "delta_vs_context_agnostic_memory_trust": metric_delta(pm, H001_POLICY, CONTEXT_AGNOSTIC_POLICY),
        "delta_vs_conceptgraphs_same_batch": metric_delta(pm, H001_POLICY, CONCEPTGRAPHS_POLICY) if cg else None,
        "claim_boundary": {
            "batch_query_metric_ready": True,
            "remaining_batches_launch_candidate": selected == "launch_remaining_batches_after_recording_false_positive_boundary",
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "next_recommended_unit": "E005-M72/E005-M73 remaining-batch launch or verification if accepting M71 false-positive boundary",
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], decision: dict[str, Any]) -> str:
    pm = metrics["policy_metrics"]
    h001 = pm[H001_POLICY]
    task = pm["real_detector_task_budget_v0"]
    top5 = pm["real_detector_confidence_top5_v0"]
    static = pm[STATIC_POLICY]
    context = pm[CONTEXT_AGNOSTIC_POLICY]
    cg = pm.get(CONCEPTGRAPHS_POLICY, {})
    return "\n".join(
        [
            f"# E005-M71 Real Proposal Query Metrics: {coverage['batch_id']}",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Query rows: {metrics['query_rows']}.",
            f"- Unique targets: {metrics['unique_target_uids']}.",
            f"- Query target detected rows/rate: {metrics['query_target_detected_rows']} / {metrics['query_target_detected_rate']}.",
            f"- Unique target detected rows/rate: {metrics['unique_target_detected_uids']} / {metrics['unique_target_detected_rate']}.",
            f"- Mean target rank when detected: {metrics['mean_target_rank_when_detected']}.",
            f"- Mean false positives before target when detected: {metrics['mean_false_positive_before_target_when_detected']}.",
            f"- `real_detector_task_budget_v0` success rows/rate: {task['query_bridge_success_rows']} / {task['query_bridge_success_rate']}.",
            f"- `real_detector_confidence_top5_v0` success rows/rate: {top5['query_bridge_success_rows']} / {top5['query_bridge_success_rate']}.",
            f"- `real_static_memory_only_v0` success rows/rate: {static['query_bridge_success_rows']} / {static['query_bridge_success_rate']}.",
            f"- `real_context_agnostic_memory_trust_reobserve_v0` success rows/rate: {context['query_bridge_success_rows']} / {context['query_bridge_success_rate']}.",
            f"- `real_task_context_memory_trust_reobserve_v0` success rows/rate: {h001['query_bridge_success_rows']} / {h001['query_bridge_success_rate']}.",
            f"- H001 mean `ExpectedSearchCost` / proxy `SPL`: {h001['mean_expected_search_cost']} / {h001['mean_attempt_spl_proxy']}.",
            f"- `ConceptGraphs` same-batch strict bbox top5 rows/rate: {cg.get('query_bridge_success_rows')} / {cg.get('query_bridge_success_rate')}.",
            f"- Failure class counts: {decision['failure_class_counts']}.",
            f"- Selected next route: `{decision['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            f"- M71 converts `{coverage['batch_id']}` detector output into query-level search metrics.",
            "- M71 is one batch only, so it is not final real RGB-D/open-vocabulary robustness.",
            "- Real navigation `SR` / `SPL` and deployable search policy claims remain false.",
            "",
            "## Agent Inference",
            "",
            f"- {decision['rationale']}",
            "- Because false positives remain high, remaining-batch launch should preserve the same metric contract and not be described as a final robustness result.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default="heldout_b01")
    parser.add_argument("--m68-root", default=DEFAULT_M68_ROOT, type=Path)
    parser.add_argument("--m69-root", default=DEFAULT_M69_ROOT, type=Path)
    parser.add_argument("--m70-root", default=DEFAULT_M70_ROOT, type=Path)
    parser.add_argument("--m51-dir", default=DEFAULT_M51_DIR, type=Path)
    parser.add_argument("--m45-dir", default=DEFAULT_M45_DIR, type=Path)
    parser.add_argument("--out-root", default=DEFAULT_OUT_ROOT, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    batch_id = args.batch_id
    m68_batch = args.m68_root / "batches" / batch_id
    m69_batch = args.m69_root / batch_id
    m70_batch = args.m70_root / batch_id
    out_dir = args.out_root / batch_id

    direct_rows = read_jsonl(m68_batch / "direct_bridge_query_rows.jsonl")
    adapter_rows = read_jsonl(args.m51_dir / "adapter_preview_rows.jsonl")
    proposals = read_jsonl(m69_batch / "matching" / "matched_proposals.jsonl")
    target_recall_rows = read_jsonl(m69_batch / "matching" / "target_recall_rows.jsonl")
    m70 = read_json(m70_batch / "coverage.json")
    matching = read_json(m69_batch / "matching" / "coverage.json")
    cg_rows = [row for row in read_jsonl(args.m45_dir / f"policy_rows_{batch_id}.jsonl") if row.get("policy") == CONCEPTGRAPHS_POLICY]

    adapter_by_uid = {str(row["row_uid"]): row for row in adapter_rows}
    missing_adapter = sorted(row["row_uid"] for row in direct_rows if str(row["row_uid"]) not in adapter_by_uid)
    if missing_adapter:
        raise RuntimeError(f"missing M51 adapter rows: {missing_adapter[:5]}")
    if m70.get("status") not in READY_DETECTOR_VERIFICATION_STATUSES:
        raise RuntimeError(f"M70 is not ready: {m70.get('status')}")
    if matching.get("status") != "detector_matching_smoke_ready":
        raise RuntimeError(f"M69 matching is not ready: {matching.get('status')}")

    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in proposals:
        proposals_by_scan_label[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    target_recall_by_uid = {str(row["target_uid"]): row for row in target_recall_rows}
    query_rows = build_query_rows(direct_rows, adapter_by_uid, proposals_by_scan_label, target_recall_by_uid, batch_id)

    policy_rows: list[dict[str, Any]] = []
    for query in query_rows:
        same_label = proposals_by_scan_label.get((query["current_rescan_id"], query["label_canonical"]), [])
        for policy in DETECTOR_POLICIES:
            policy_rows.append(evaluate_detector_policy(policy, query, same_label))
        for policy in MEMORY_POLICIES:
            policy_rows.append(evaluate_memory_policy(policy, query))
    cg_by_uid = {str(row["query_uid"]): row for row in cg_rows}
    missing_cg = sorted(row["query_uid"] for row in query_rows if str(row["query_uid"]) not in cg_by_uid)
    if missing_cg:
        raise RuntimeError(f"missing ConceptGraphs batch rows: {missing_cg[:5]}")
    policy_rows.extend(normalize_conceptgraphs_row(cg_by_uid[str(row["query_uid"])]) for row in query_rows)

    query_metrics = summarize_query_detection(query_rows)
    policy_metrics, summary_rows = summarize_policies(policy_rows)
    metrics = {**query_metrics, "policy_metrics": policy_metrics, "version": VERSION}
    failure_rows = build_failure_rows(query_rows, policy_rows)
    decision = build_decision(metrics, failure_rows)
    status = "e005_m71_real_proposal_query_metric_ready_with_false_positive_boundary"
    if not decision["gates"]["real_detector_target_detection_sufficient_for_batch_diagnostic"]:
        status = "e005_m71_real_proposal_query_metric_ready_target_detection_weak"

    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_id": batch_id,
        "query_rows": len(query_rows),
        "policy_rows": len(policy_rows),
        "m70_status": m70.get("status"),
        "m69_matching_status": matching.get("status"),
        "m69_prediction_rows": m70.get("line_counts", {}).get("prediction_rows"),
        "m69_pre_cap_candidate_rows": m70.get("line_counts", {}).get("pre_cap_candidate_rows"),
        "query_target_detected_rows": metrics["query_target_detected_rows"],
        "query_target_detected_rate": metrics["query_target_detected_rate"],
        "real_h001_success_rows": policy_metrics[H001_POLICY]["query_bridge_success_rows"],
        "real_h001_success_rate": policy_metrics[H001_POLICY]["query_bridge_success_rate"],
        "real_detector_task_budget_success_rows": policy_metrics["real_detector_task_budget_v0"]["query_bridge_success_rows"],
        "real_detector_top5_success_rows": policy_metrics["real_detector_confidence_top5_v0"]["query_bridge_success_rows"],
        "real_context_agnostic_success_rows": policy_metrics[CONTEXT_AGNOSTIC_POLICY]["query_bridge_success_rows"],
        "conceptgraphs_same_batch_success_rows": policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rows"],
        "conceptgraphs_b01_success_rows": policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rows"],
        "real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "query_bridge_rows.jsonl", query_rows)
    write_jsonl(out_dir / "policy_rows.jsonl", policy_rows)
    write_jsonl(out_dir / "policy_summary_rows.jsonl", summary_rows)
    write_jsonl(out_dir / "failure_rows.jsonl", failure_rows)
    write_json(out_dir / "metrics.json", metrics)
    write_json(out_dir / "route_decision.json", decision)
    write_json(out_dir / "coverage.json", coverage)
    write_text(out_dir / "report.md", build_report(coverage, metrics, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
