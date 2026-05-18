#!/usr/bin/env python3
"""Evaluate E003-M75 expanded direct bridge query-level metrics."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M73_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
DEFAULT_M74_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M74_direct_bridge_denominator_detector_run_v0"
DEFAULT_E001_DIR = REPO_ROOT / "experiments" / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
M75_VERSION = "e003_m75_expanded_direct_query_bridge_v0"
POLICIES = {
    "detector_top1_v0": ("confidence_desc", "top1"),
    "detector_top3_v0": ("confidence_desc", "top3"),
    "detector_top5_v0": ("confidence_desc", "top5"),
    "detector_task_budget_v0": ("confidence_desc", "task_budget"),
    "bounded_old_memory_distance_guard_adaptive_top5_v0": ("old_memory_distance_guard", "adaptive_uncertainty_top5"),
    "unbounded_old_memory_distance_guard_until_target_v0": ("old_memory_distance_guard", "unbounded_until_target_or_exhausted"),
    "oracle_target_first_task_budget_upper_bound_v0": ("oracle_target_first_upper_bound", "task_budget"),
}
NON_DEPLOYABLE_POLICIES = {"oracle_target_first_task_budget_upper_bound_v0"}


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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


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


def task_conditioned_budget(query: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_detector_candidate"
    if query["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"

    max_budget = int(query["max_candidate_budget"])
    high_ambiguity_budget = int(query["high_ambiguity_budget"])
    if query["task_context_id"] == "routine_fetch":
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "routine_trivial_candidate"
        if query["ambiguity_band"] == "high_ambiguity":
            return min(candidate_count, max_budget, high_ambiguity_budget), "routine_high_ambiguity_bounded"
        return min(candidate_count, max_budget, 3), "routine_rank_sensitive_budget"

    if query["task_context_id"] in {"high_value_fetch", "noisy_high_value_fetch"}:
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "high_value_trivial_candidate"
        return min(candidate_count, max_budget), "high_value_expand_budget"

    raise RuntimeError(f"unknown task_context_id: {query['task_context_id']}")


def policy_budget(mode: str, query: dict[str, Any], candidate_count: int, target_rank: int | None) -> tuple[int, str]:
    if mode == "top1":
        return min(candidate_count, 1), "detector_confidence_top1"
    if mode == "top3":
        return min(candidate_count, 3), "detector_confidence_top3"
    if mode == "top5":
        return min(candidate_count, 5), "detector_confidence_top5"
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
        return candidate_count, "exhaust_detector_candidates"
    raise RuntimeError(f"unknown budget mode: {mode}")


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def query_slice_id(row: dict[str, Any]) -> str:
    if row.get("old_location_dead_end_expected"):
        return "stale_old_dead_end"
    if row.get("row_band") == "significant_moved":
        return "significant_moved"
    if row.get("expected_memory_state") == "trusted_or_low_motion":
        return "trusted_or_low_motion"
    return "review_or_mid_motion"


def build_query_rows(
    direct_rows: list[dict[str, Any]],
    e001_by_row_uid: dict[str, dict[str, Any]],
    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    target_recall_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for direct in direct_rows:
        e001 = e001_by_row_uid[str(direct["row_uid"])]
        target_uid = str(direct["target_uid"])
        same_label = proposals_by_scan_label.get((direct["current_rescan_id"], direct["label_canonical"]), [])
        confidence_ordered = order_proposals(same_label, e001, target_uid, "confidence_desc")
        target_rank = None
        target_proposal = None
        for rank, proposal in enumerate(confidence_ordered, start=1):
            if str(proposal.get("matched_target_uid")) == target_uid:
                target_rank = rank
                target_proposal = proposal
                break

        target_recall = target_recall_by_uid.get(target_uid, {})
        query_target_detected = bool(target_recall.get("matched")) and target_rank is not None
        fp_before = None
        if query_target_detected and target_rank is not None:
            fp_before = sum(1 for proposal in confidence_ordered[: target_rank - 1] if str(proposal.get("matched_target_uid")) != target_uid)

        static_success = float(e001["scene_aligned_static_error_m"]) <= float(e001["success_threshold_m"])
        e001_target_success = float(e001["row_geometry_error_m"]) <= float(e001["success_threshold_m"])
        old_dead_end = bool(e001.get("old_location_dead_end_expected")) or bool(e001.get("old_memory_is_stale") and not static_success)
        row = {
            "m75_version": M75_VERSION,
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
            "query_slice_id": None,
            "ambiguity_band": e001["ambiguity_band"],
            "expected_memory_state": e001["expected_memory_state"],
            "old_memory_is_stale": bool(e001["old_memory_is_stale"]),
            "old_location_dead_end_expected": old_dead_end,
            "scene_aligned_static_error_m": e001["scene_aligned_static_error_m"],
            "row_geometry_error_m": e001["row_geometry_error_m"],
            "success_threshold_m": e001["success_threshold_m"],
            "e001_annotation_target_success": e001_target_success,
            "query_target_detected": query_target_detected,
            "query_target_rank_by_detector_score": target_rank,
            "query_target_best_proposal_uid": target_proposal.get("proposal_uid") if target_proposal else None,
            "query_target_best_match_distance_m": target_proposal.get("match_distance_m") if target_proposal else None,
            "query_target_best_confidence": target_proposal.get("confidence") if target_proposal else None,
            "same_label_detector_proposal_count": len(confidence_ordered),
            "same_label_false_positive_count": sum(1 for proposal in confidence_ordered if str(proposal.get("matched_target_uid")) != target_uid),
            "same_label_matched_other_target_count": sum(
                1
                for proposal in confidence_ordered
                if proposal.get("match_status") == "matched" and str(proposal.get("matched_target_uid")) != target_uid
            ),
            "same_label_unmatched_false_positive_count": sum(1 for proposal in confidence_ordered if proposal.get("match_status") != "matched"),
            "false_positive_before_target_count": fp_before,
            "target_recall_best_proposal_uid": target_recall.get("best_proposal_uid"),
            "target_recall_best_match_distance_m": target_recall.get("best_match_distance_m"),
            "allowed_policy_inputs": [
                "current_rescan_id",
                "label_canonical",
                "detector proposal confidence/centroid",
                "task_context_id",
                "pre-evaluation staleness metadata",
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


def target_rank_in_order(ordered: list[dict[str, Any]], target_uid: str) -> tuple[int | None, str | None, int | None]:
    for rank, proposal in enumerate(ordered, start=1):
        if str(proposal.get("matched_target_uid")) == target_uid:
            fp_before = sum(1 for prev in ordered[: rank - 1] if str(prev.get("matched_target_uid")) != target_uid)
            return rank, str(proposal.get("proposal_uid")), fp_before
    return None, None, None


def build_policy_rows(
    query_rows: list[dict[str, Any]],
    e001_by_row_uid: dict[str, dict[str, Any]],
    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for query_row in query_rows:
        e001 = e001_by_row_uid[str(query_row["row_uid"])]
        target_uid = str(query_row["target_uid"])
        same_label = proposals_by_scan_label.get((query_row["current_rescan_id"], query_row["label_canonical"]), [])
        for policy, (order_mode, budget_mode) in POLICIES.items():
            ordered = order_proposals(same_label, e001, target_uid, order_mode)
            target_rank, target_proposal_uid, fp_before = target_rank_in_order(ordered, target_uid)
            returned_k, reason = policy_budget(budget_mode, e001, len(ordered), target_rank)
            success = bool(target_rank is not None and target_rank <= returned_k)
            expected_cost = int(target_rank) if success and target_rank is not None else int(returned_k) + 1
            rows.append(
                {
                    "m75_version": M75_VERSION,
                    "row_uid": query_row["row_uid"],
                    "base_row_uid": query_row["base_row_uid"],
                    "pair_uid": query_row["pair_uid"],
                    "target_uid": target_uid,
                    "current_rescan_id": query_row["current_rescan_id"],
                    "label_canonical": query_row["label_canonical"],
                    "task_context_id": query_row["task_context_id"],
                    "row_band": query_row["row_band"],
                    "query_slice_id": query_row["query_slice_id"],
                    "policy": policy,
                    "order_mode": order_mode,
                    "budget_mode": budget_mode,
                    "deployable_policy": policy not in NON_DEPLOYABLE_POLICIES,
                    "decision_reason": reason,
                    "target_detected": target_rank is not None,
                    "target_rank": target_rank,
                    "target_proposal_uid": target_proposal_uid,
                    "false_positive_before_target_count": fp_before,
                    "candidate_count": len(ordered),
                    "returned_location_count": returned_k,
                    "query_bridge_success": success,
                    "expected_search_cost": expected_cost,
                    "attempt_spl_proxy": attempt_spl(success, expected_cost),
                    "old_location_dead_end_expected": query_row["old_location_dead_end_expected"],
                    "old_location_dead_end_avoided": bool(query_row["old_location_dead_end_expected"] and success),
                    "real_navigation_sr_spl_ready": False,
                    "real_rgbd_open_vocab_query_claim_ready": False,
                }
            )
    return rows


def summarize_query_detection(query_rows: list[dict[str, Any]]) -> dict[str, Any]:
    detected = [row for row in query_rows if row["query_target_detected"]]
    unique_targets = sorted({row["target_uid"] for row in query_rows})
    detected_targets = sorted({row["target_uid"] for row in detected})
    false_before = [
        int(row["false_positive_before_target_count"])
        for row in detected
        if row["false_positive_before_target_count"] is not None
    ]
    return {
        "query_rows": len(query_rows),
        "unique_target_uids": len(unique_targets),
        "query_target_detected_rows": len(detected),
        "query_target_detected_rate": safe_rate(len(detected), len(query_rows)),
        "unique_target_detected_uids": len(detected_targets),
        "unique_target_detected_rate": safe_rate(len(detected_targets), len(unique_targets)),
        "mean_target_rank_when_detected": safe_mean(
            [int(row["query_target_rank_by_detector_score"]) for row in detected if row["query_target_rank_by_detector_score"]]
        ),
        "mean_false_positive_before_target_when_detected": safe_mean(false_before),
        "mean_same_label_detector_proposals_per_query": safe_mean(
            [int(row["same_label_detector_proposal_count"]) for row in query_rows]
        ),
        "query_rows_by_slice": dict(Counter(row["query_slice_id"] for row in query_rows)),
        "query_rows_by_task_context": dict(Counter(row["task_context_id"] for row in query_rows)),
        "query_rows_by_label": dict(Counter(row["label_canonical"] for row in query_rows)),
    }


def summarize_policy_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    stale = [row for row in rows if row["old_location_dead_end_expected"]]
    detected = [row for row in rows if row["target_detected"]]
    return {
        "rows": len(rows),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "mean_target_rank_if_detected": safe_mean([int(row["target_rank"]) for row in detected if row["target_rank"] is not None]),
        "mean_false_positive_before_target_if_detected": safe_mean(
            [
                int(row["false_positive_before_target_count"])
                for row in detected
                if row["false_positive_before_target_count"] is not None
            ]
        ),
        "mean_returned_location_count": safe_mean([int(row["returned_location_count"]) for row in rows]),
        "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_avoided_rows": sum(1 for row in stale if row["old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(sum(1 for row in stale if row["old_location_dead_end_avoided"]), len(stale)),
    }


def summarize_policies(policy_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_metrics: dict[str, Any] = {}
    summary_rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        rows = [row for row in policy_rows if row["policy"] == policy]
        policy_metrics[policy] = summarize_policy_group(rows)
        summary_rows.append({"group_type": "policy", "group_value": policy, "policy": policy, **policy_metrics[policy]})
        for task_context, task_rows in sorted(group_by(rows, "task_context_id").items()):
            summary_rows.append(
                {"group_type": "task_context", "group_value": task_context, "policy": policy, **summarize_policy_group(task_rows)}
            )
        for slice_id, slice_rows in sorted(group_by(rows, "query_slice_id").items()):
            summary_rows.append(
                {"group_type": "query_slice", "group_value": slice_id, "policy": policy, **summarize_policy_group(slice_rows)}
            )
    return policy_metrics, summary_rows


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key))].append(row)
    return grouped


def build_failure_rows(query_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["row_uid"], row["policy"]): row for row in policy_rows}
    failures = []
    for query in query_rows:
        task = by_key[(query["row_uid"], "detector_task_budget_v0")]
        bounded = by_key[(query["row_uid"], "bounded_old_memory_distance_guard_adaptive_top5_v0")]
        unbounded = by_key[(query["row_uid"], "unbounded_old_memory_distance_guard_until_target_v0")]
        if not task["target_detected"]:
            failure_class = "detector_recall_miss"
        elif task["query_bridge_success"]:
            failure_class = "task_budget_success"
        elif bounded["query_bridge_success"]:
            failure_class = "bounded_repair_success"
        elif unbounded["query_bridge_success"]:
            failure_class = "unbounded_high_cost_repair_only"
        else:
            failure_class = "detected_but_not_recovered"
        failures.append(
            {
                "m75_version": M75_VERSION,
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "target_uid": query["target_uid"],
                "current_rescan_id": query["current_rescan_id"],
                "label_canonical": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "query_slice_id": query["query_slice_id"],
                "failure_class": failure_class,
                "target_detected": task["target_detected"],
                "task_budget_success": task["query_bridge_success"],
                "bounded_repair_success": bounded["query_bridge_success"],
                "unbounded_success": unbounded["query_bridge_success"],
                "task_target_rank": task["target_rank"],
                "bounded_target_rank": bounded["target_rank"],
                "task_expected_search_cost": task["expected_search_cost"],
                "bounded_expected_search_cost": bounded["expected_search_cost"],
                "unbounded_expected_search_cost": unbounded["expected_search_cost"],
                "task_false_positive_before_target_count": task["false_positive_before_target_count"],
                "bounded_false_positive_before_target_count": bounded["false_positive_before_target_count"],
            }
        )
    return failures


def route_decision(metrics: dict[str, Any], failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    task = metrics["policy_metrics"]["detector_task_budget_v0"]
    bounded = metrics["policy_metrics"]["bounded_old_memory_distance_guard_adaptive_top5_v0"]
    unbounded = metrics["policy_metrics"]["unbounded_old_memory_distance_guard_until_target_v0"]
    failure_counts = Counter(row["failure_class"] for row in failure_rows)
    if int(bounded["query_bridge_success_rows"]) > int(task["query_bridge_success_rows"]):
        selected = "expanded_bridge_bounded_repair_positive_e004_gate_next"
        rationale = "Bounded repair improves query-level success over the original task-budget policy on the expanded denominator."
    elif int(unbounded["query_bridge_success_rows"]) > int(task["query_bridge_success_rows"]):
        selected = "expanded_bridge_high_cost_upper_bound_e004_gate_next"
        rationale = "The expanded denominator has an unbounded upper-bound gain, but bounded repair does not improve the task-budget policy."
    elif failure_counts.get("detector_recall_miss", 0) > 0:
        selected = "proposal_recall_or_external_baseline_before_e004"
        rationale = "Target recall miss remains the dominant blocker before claiming a robust real proposal/search bridge."
    else:
        selected = "e004_transition_gate_next"
        rationale = "Detector outputs are query-level evaluated, but claim boundary must still be reviewed before E004."
    return {
        "bounded_success_delta_vs_task": int(bounded["query_bridge_success_rows"]) - int(task["query_bridge_success_rows"]),
        "failure_class_counts": dict(failure_counts),
        "rationale": rationale,
        "selected_next_route": selected,
        "task_budget_success_rows": task["query_bridge_success_rows"],
        "unbounded_success_delta_vs_task": int(unbounded["query_bridge_success_rows"]) - int(task["query_bridge_success_rows"]),
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], route: dict[str, Any]) -> str:
    task = metrics["policy_metrics"]["detector_task_budget_v0"]
    bounded = metrics["policy_metrics"]["bounded_old_memory_distance_guard_adaptive_top5_v0"]
    unbounded = metrics["policy_metrics"]["unbounded_old_memory_distance_guard_until_target_v0"]
    return "\n".join(
        [
            "# E003-M75 Expanded Direct Query Bridge",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {metrics['query_rows']}",
            f"- Unique targets: {metrics['unique_target_uids']}",
            f"- Query target detected rows/rate: {metrics['query_target_detected_rows']} / {metrics['query_target_detected_rate']}",
            f"- Unique target detected rows/rate: {metrics['unique_target_detected_uids']} / {metrics['unique_target_detected_rate']}",
            f"- Mean target rank when detected: {metrics['mean_target_rank_when_detected']}",
            f"- Mean false positives before target when detected: {metrics['mean_false_positive_before_target_when_detected']}",
            f"- `detector_task_budget_v0` success rows/rate: {task['query_bridge_success_rows']} / {task['query_bridge_success_rate']}",
            f"- `detector_task_budget_v0` mean expected search cost / `AttemptSPL` proxy: {task['mean_expected_search_cost']} / {task['mean_attempt_spl_proxy']}",
            f"- `bounded_old_memory_distance_guard_adaptive_top5_v0` success rows/rate: {bounded['query_bridge_success_rows']} / {bounded['query_bridge_success_rate']}",
            f"- `bounded_old_memory_distance_guard_adaptive_top5_v0` mean expected search cost / `AttemptSPL` proxy: {bounded['mean_expected_search_cost']} / {bounded['mean_attempt_spl_proxy']}",
            f"- `unbounded_old_memory_distance_guard_until_target_v0` success rows/rate: {unbounded['query_bridge_success_rows']} / {unbounded['query_bridge_success_rate']}",
            f"- `unbounded_old_memory_distance_guard_until_target_v0` mean expected search cost / `AttemptSPL` proxy: {unbounded['mean_expected_search_cost']} / {unbounded['mean_attempt_spl_proxy']}",
            f"- M74 proposal rows: {coverage['m74_prediction_rows']}",
            f"- M74 proposal precision smoke: {coverage['m74_proposal_precision_smoke']}",
            f"- M74 scan target recall smoke: {coverage['m74_scan_target_recall_smoke']}",
            f"- Failure class counts: {route['failure_class_counts']}",
            f"- Selected next route: `{route['selected_next_route']}`",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M75 supports an expanded direct query-level bridge diagnostic over E003-M74 detector outputs.",
            "- E003-M75 can be used to report proposal-to-query rank, budget, and cost behavior for the current `GroundingDINO` RGB-D backprojection route.",
            "- E003-M75 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
            "",
            "## 에이전트 추론",
            "",
            f"- {route['rationale']}",
            "- Proposal recall and query-level budget success must remain separate in reviewer-facing claims.",
            "- The bounded repair gain is useful for the E004 gate, but it is not yet a final policy claim because it increases average search cost and relaxes the original memory-trust behavior.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before the E004 transition gate.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m73-dir", default=DEFAULT_M73_DIR, type=Path)
    parser.add_argument("--m74-dir", default=DEFAULT_M74_DIR, type=Path)
    parser.add_argument("--e001-dir", default=DEFAULT_E001_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    direct_rows = load_jsonl(args.m73_dir / "direct_bridge_query_rows.jsonl")
    e001_rows = load_jsonl(args.e001_dir / "query_rows.jsonl")
    proposals = load_jsonl(args.m74_dir / "matching" / "matched_proposals.jsonl")
    target_recall_rows = load_jsonl(args.m74_dir / "matching" / "target_recall_rows.jsonl")
    m73_coverage = load_json(args.m73_dir / "coverage.json")
    m74_coverage = load_json(args.m74_dir / "coverage.json")
    m74_matching = load_json(args.m74_dir / "matching" / "coverage.json")

    e001_by_row_uid = {str(row["row_uid"]): row for row in e001_rows}
    missing = sorted(row["row_uid"] for row in direct_rows if str(row["row_uid"]) not in e001_by_row_uid)
    if missing:
        raise RuntimeError(f"missing E001 query rows: {missing[:5]}")

    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in proposals:
        proposals_by_scan_label[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    target_recall_by_uid = {str(row["target_uid"]): row for row in target_recall_rows}

    query_rows = build_query_rows(
        direct_rows=direct_rows,
        e001_by_row_uid=e001_by_row_uid,
        proposals_by_scan_label=proposals_by_scan_label,
        target_recall_by_uid=target_recall_by_uid,
    )
    policy_rows = build_policy_rows(query_rows, e001_by_row_uid, proposals_by_scan_label)
    query_metrics = summarize_query_detection(query_rows)
    policy_metrics, policy_summary_rows = summarize_policies(policy_rows)
    metrics = {**query_metrics, "policy_metrics": policy_metrics}
    failure_rows = build_failure_rows(query_rows, policy_rows)
    route = route_decision(metrics, failure_rows)

    bounded_delta = int(route["bounded_success_delta_vs_task"])
    status = "expanded_direct_query_bridge_ready"
    if metrics["query_target_detected_rows"] == 0:
        status = "expanded_direct_query_bridge_detector_target_miss"
    elif bounded_delta <= 0:
        status = "expanded_direct_query_bridge_no_bounded_gain"

    coverage = {
        "detector_budget_policy_success_rows": policy_metrics["detector_task_budget_v0"]["query_bridge_success_rows"],
        "direct_bridge_query_rows": len(query_rows),
        "m73_detector_ready_query_rows": m73_coverage.get("detector_ready_query_rows"),
        "m73_dir": str(args.m73_dir),
        "m74_dir": str(args.m74_dir),
        "m74_matching_status": m74_matching.get("status"),
        "m74_prediction_rows": m74_coverage.get("prediction_rows"),
        "m74_proposal_precision_smoke": m74_matching.get("proposal_precision_smoke"),
        "m74_scan_target_recall_smoke": m74_matching.get("scan_target_recall_smoke"),
        "m74_validator_error_rows": m74_coverage.get("validator_error_rows"),
        "m74_validator_warning_rows": m74_coverage.get("validator_warning_rows"),
        "m75_version": M75_VERSION,
        "next_recommended_unit": "E004 transition gate after reviewing M75 claim boundary",
        "paper_table_command_ready": False,
        "policy_rows": len(policy_rows),
        "query_target_detected_rows": metrics["query_target_detected_rows"],
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "selected_next_route": route["selected_next_route"],
        "status": status,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "query_bridge_rows.jsonl", query_rows)
    write_jsonl(args.out_dir / "policy_rows.jsonl", policy_rows)
    write_jsonl(args.out_dir / "policy_summary_rows.jsonl", policy_summary_rows)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "route_decision.json", route)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, metrics, route))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status in {"expanded_direct_query_bridge_ready", "expanded_direct_query_bridge_no_bounded_gain"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
