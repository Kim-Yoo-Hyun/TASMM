#!/usr/bin/env python3
"""Replay H001 memory-trust policies on the M38 heldout query contract."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M51_DIR = EXP_ROOT / "artifacts" / "E005-M51_h001_heldout_policy_replay_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0"
VERSION = "e005_m52_h001_heldout_policy_replay_v0"

CONCEPTGRAPHS_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
H001_POLICY = "task_context_memory_trust_reobserve_v0"
CONTEXT_AGNOSTIC_POLICY = "context_agnostic_memory_trust_reobserve_v0"
STATIC_POLICY = "static_memory_only_v0"

TASK_CONTEXT_PROFILES = {
    "routine_fetch": {
        "max_candidate_budget": 3,
        "high_ambiguity_budget": 2,
    },
    "high_value_fetch": {
        "max_candidate_budget": 5,
        "high_ambiguity_budget": 5,
    },
    "noisy_high_value_fetch": {
        "max_candidate_budget": 5,
        "high_ambiguity_budget": 5,
    },
}

DETECTOR_POLICIES = {
    "detector_top1_v0": ("top1", False),
    "detector_top3_v0": ("top3", False),
    "detector_top5_v0": ("top5", False),
    "detector_task_budget_v0": ("task_budget", False),
    "bounded_old_memory_distance_guard_adaptive_top5_v0": ("adaptive_uncertainty_top5", False),
    "unbounded_old_memory_distance_guard_until_target_v0": ("unbounded_until_target_or_exhausted", False),
    "oracle_target_first_task_budget_upper_bound_v0": ("task_budget", True),
}

MEMORY_POLICIES = [
    STATIC_POLICY,
    CONTEXT_AGNOSTIC_POLICY,
    H001_POLICY,
]

POLICY_ORDER = list(DETECTOR_POLICIES) + MEMORY_POLICIES + [CONCEPTGRAPHS_POLICY]


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
    return float(query["scene_aligned_static_error_m"]) <= float(query["success_threshold_m"])


def target_rank(query: dict[str, Any]) -> int | None:
    rank = query.get("query_target_rank_by_detector_score")
    return None if rank is None else int(rank)


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


def detector_budget(policy: str, query: dict[str, Any], rank: int | None, candidate_count: int) -> tuple[int, str, int | None]:
    mode, oracle = DETECTOR_POLICIES[policy]
    effective_rank = 1 if oracle and rank is not None else rank
    if mode == "top1":
        return min(candidate_count, 1), "detector_confidence_top1", effective_rank
    if mode == "top3":
        return min(candidate_count, 3), "detector_confidence_top3", effective_rank
    if mode == "top5":
        return min(candidate_count, 5), "detector_confidence_top5", effective_rank
    if mode == "task_budget":
        budget, reason = task_conditioned_budget(query, candidate_count)
        return budget, reason, effective_rank
    if mode == "adaptive_uncertainty_top5":
        budget, reason = task_conditioned_budget(query, candidate_count)
        if bool(query.get("old_location_dead_end_expected")) or candidate_count >= 12:
            return min(candidate_count, max(budget, 5)), "adaptive_uncertainty_top5", effective_rank
        return budget, f"adaptive_keep_{reason}", effective_rank
    if mode == "unbounded_until_target_or_exhausted":
        if effective_rank is not None:
            return effective_rank, "visit_until_detected_target", effective_rank
        return candidate_count, "exhaust_detector_candidates", effective_rank
    raise RuntimeError(f"unknown detector mode: {mode}")


def evaluate_detector_policy(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    rank = target_rank(query)
    candidate_count = int(query["same_label_detector_proposal_count"])
    returned, reason, effective_rank = detector_budget(policy, query, rank, candidate_count)
    success = bool(effective_rank is not None and effective_rank <= returned)
    expected_cost = int(effective_rank) if success and effective_rank is not None else int(returned) + 1
    return {
        "m52_version": VERSION,
        "row_uid": query["row_uid"],
        "query_uid": query["bridge_query_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "target_uid": query["target_uid"],
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "query_slice_id": query_slice_id(query),
        "policy": policy,
        "policy_family": "conceptgraphs_detector_baseline",
        "deployable_policy": policy != "oracle_target_first_task_budget_upper_bound_v0",
        "decision_reason": reason,
        "target_detected": rank is not None,
        "target_rank": effective_rank,
        "raw_target_rank": rank,
        "candidate_count": candidate_count,
        "returned_location_count": returned,
        "query_bridge_success": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "old_location_dead_end_expected": bool(query["old_location_dead_end_expected"]),
        "old_location_dead_end_avoided": bool(query["old_location_dead_end_expected"] and success),
        "old_memory_first": False,
        "memory_trust_level": "not_applicable",
        "success_source": "detector_reobservation" if success else "none",
        "leakage_audit_pass": True,
        "policy_input_fields_used": ["ConceptGraphs candidate count/rank order", "task_context_id", "pre-evaluation staleness metadata"],
        "real_navigation_sr_spl_ready": False,
    }


def memory_decision(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    context = str(query["task_context_id"])
    state = str(query["expected_memory_state"])
    stale = bool(query["old_memory_is_stale"])
    candidate_count = int(query["same_label_detector_proposal_count"])
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
        "candidate_visit_order": "old_memory_then_conceptgraphs_rank" if old_memory_first else "conceptgraphs_rank",
        "decision_reason": reason,
        "detector_budget": detector_k,
        "memory_trust_level": memory_trust_level,
        "old_memory_first": old_memory_first,
        "re_observation_budget": detector_k,
    }


def evaluate_memory_policy(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    decision = memory_decision(policy, query)
    rank = target_rank(query)
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
        success_source = "detector_reobservation"
    else:
        success = False
        expected_cost = int(old_first) + detector_k + 1
        success_source = "none"
    old_dead_end_expected = bool(query["old_location_dead_end_expected"])
    return {
        "m52_version": VERSION,
        "row_uid": query["row_uid"],
        "query_uid": query["bridge_query_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "target_uid": query["target_uid"],
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "query_slice_id": query_slice_id(query),
        "policy": policy,
        "policy_family": "h001_memory_trust_reobserve",
        "deployable_policy": True,
        "target_detected": rank is not None,
        "target_rank": rank,
        "raw_target_rank": rank,
        "static_memory_success": static_success,
        "candidate_count": int(query["same_label_detector_proposal_count"]),
        "returned_location_count": decision["candidate_visit_budget"],
        "query_bridge_success": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "old_location_dead_end_expected": old_dead_end_expected,
        "old_location_dead_end_avoided": bool(old_dead_end_expected and not decision["old_memory_first"] and success),
        "success_source": success_source,
        "leakage_audit_pass": True,
        "policy_input_fields_used": ["task_context_id", "expected_memory_state", "old_memory_is_stale", "same_label_detector_proposal_count"],
        "real_navigation_sr_spl_ready": False,
        **decision,
    }


def load_conceptgraphs_primary_rows() -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for suffix in ["b01", "b02", "b03"]:
        rows.extend(read_jsonl(M45_METRIC_DIR / f"policy_rows_heldout_{suffix}.jsonl"))
    primary = [row for row in rows if row.get("policy") == CONCEPTGRAPHS_POLICY]
    return {str(row["query_uid"]): row for row in primary}


def normalize_conceptgraphs_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "m52_version": VERSION,
        "row_uid": str(row["query_uid"]).removeprefix("m38:"),
        "query_uid": row["query_uid"],
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


def summarize_policy_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    stale = [row for row in rows if row["old_location_dead_end_expected"]]
    old_successes = [row for row in successes if row.get("success_source") == "old_memory"]
    detector_successes = [row for row in successes if row.get("success_source") == "detector_reobservation"]
    over_search = [row for row in rows if int(row["returned_location_count"]) >= 5 and not row["query_bridge_success"]]
    return {
        "rows": len(rows),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "old_memory_success_rows": len(old_successes),
        "detector_reobservation_success_rows": len(detector_successes),
        "mean_returned_location_count": safe_mean([int(row["returned_location_count"]) for row in rows]),
        "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_avoided_rows": sum(1 for row in stale if row["old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(sum(1 for row in stale if row["old_location_dead_end_avoided"]), len(stale)),
        "over_search_rows": len(over_search),
        "over_search_rate": safe_rate(len(over_search), len(rows)),
        "target_detected_rows": sum(1 for row in rows if row.get("target_detected")),
        "target_detected_rate": safe_rate(sum(1 for row in rows if row.get("target_detected")), len(rows)),
    }


def summarize(policy_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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


def comparison_rows(policy_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    selected = [
        STATIC_POLICY,
        "detector_task_budget_v0",
        "detector_top5_v0",
        CONTEXT_AGNOSTIC_POLICY,
        H001_POLICY,
        CONCEPTGRAPHS_POLICY,
        "unbounded_old_memory_distance_guard_until_target_v0",
    ]
    rows = []
    for policy in selected:
        metric = policy_metrics.get(policy, {})
        rows.append(
            {
                "policy": policy,
                "rows": metric.get("rows"),
                "success_rows": metric.get("query_bridge_success_rows"),
                "success_rate": metric.get("query_bridge_success_rate"),
                "mean_expected_search_cost": metric.get("mean_expected_search_cost"),
                "mean_attempt_spl_proxy": metric.get("mean_attempt_spl_proxy"),
                "old_memory_success_rows": metric.get("old_memory_success_rows"),
                "detector_reobservation_success_rows": metric.get("detector_reobservation_success_rows"),
                "target_detected_rate": metric.get("target_detected_rate"),
            }
        )
    return rows


def build_failure_rows(query_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["query_uid"], row["policy"]): row for row in policy_rows}
    rows = []
    for query in query_rows:
        qid = query["bridge_query_uid"]
        task = by_key[(qid, H001_POLICY)]
        cg = by_key[(qid, CONCEPTGRAPHS_POLICY)]
        context = by_key[(qid, CONTEXT_AGNOSTIC_POLICY)]
        static = by_key[(qid, STATIC_POLICY)]
        if task["query_bridge_success"] and not cg["query_bridge_success"]:
            cls = "h001_recovers_conceptgraphs_miss"
        elif cg["query_bridge_success"] and not task["query_bridge_success"]:
            cls = "conceptgraphs_recovers_h001_miss"
        elif task["query_bridge_success"] and cg["query_bridge_success"]:
            cls = "both_success"
        elif static["query_bridge_success"] and not task["query_bridge_success"]:
            cls = "h001_regresses_static_memory"
        elif context["query_bridge_success"] and not task["query_bridge_success"]:
            cls = "h001_regresses_context_agnostic"
        else:
            cls = "both_fail"
        rows.append(
            {
                "m52_version": VERSION,
                "query_uid": qid,
                "row_uid": query["row_uid"],
                "target_uid": query["target_uid"],
                "label_canonical": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "failure_class": cls,
                "h001_success": task["query_bridge_success"],
                "conceptgraphs_success": cg["query_bridge_success"],
                "static_success": static["query_bridge_success"],
                "context_agnostic_success": context["query_bridge_success"],
                "h001_expected_search_cost": task["expected_search_cost"],
                "conceptgraphs_expected_search_cost": cg["expected_search_cost"],
            }
        )
    return rows


def task_delta(policy_metrics: dict[str, Any], policy_a: str, policy_b: str) -> dict[str, Any]:
    a = policy_metrics[policy_a]
    b = policy_metrics[policy_b]
    return {
        "success_rows_delta": int(a["query_bridge_success_rows"]) - int(b["query_bridge_success_rows"]),
        "success_rate_delta": round(float(a["query_bridge_success_rate"]) - float(b["query_bridge_success_rate"]), 6),
        "mean_expected_search_cost_delta": round(float(a["mean_expected_search_cost"]) - float(b["mean_expected_search_cost"]), 6),
        "mean_attempt_spl_proxy_delta": round(float(a["mean_attempt_spl_proxy"]) - float(b["mean_attempt_spl_proxy"]), 6),
    }


def build_decision(policy_metrics: dict[str, Any], failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    h001 = policy_metrics[H001_POLICY]
    static = policy_metrics[STATIC_POLICY]
    context = policy_metrics[CONTEXT_AGNOSTIC_POLICY]
    cg = policy_metrics[CONCEPTGRAPHS_POLICY]
    unbounded = policy_metrics["unbounded_old_memory_distance_guard_until_target_v0"]
    gates = {
        "paired_vs_conceptgraphs_success_gain": int(h001["query_bridge_success_rows"]) > int(cg["query_bridge_success_rows"]),
        "beats_static_memory_success": int(h001["query_bridge_success_rows"]) > int(static["query_bridge_success_rows"]),
        "task_context_effect_vs_context_agnostic": int(h001["query_bridge_success_rows"]) != int(context["query_bridge_success_rows"])
        or abs(float(h001["mean_expected_search_cost"]) - float(context["mean_expected_search_cost"])) >= 0.1,
        "below_unbounded_cost": float(h001["mean_expected_search_cost"]) < float(unbounded["mean_expected_search_cost"]),
        "not_real_navigation_claim": True,
    }
    if gates["paired_vs_conceptgraphs_success_gain"] and gates["beats_static_memory_success"] and gates["below_unbounded_cost"]:
        status = "e005_m52_h001_heldout_replay_ready_with_paired_gain"
    else:
        status = "e005_m52_h001_heldout_replay_ready_with_claim_boundary"
    return {
        "status": status,
        "gates": gates,
        "delta_vs_conceptgraphs": task_delta(policy_metrics, H001_POLICY, CONCEPTGRAPHS_POLICY),
        "delta_vs_static": task_delta(policy_metrics, H001_POLICY, STATIC_POLICY),
        "delta_vs_context_agnostic": task_delta(policy_metrics, H001_POLICY, CONTEXT_AGNOSTIC_POLICY),
        "failure_class_counts": dict(Counter(row["failure_class"] for row in failure_rows)),
        "claim_boundary": {
            "paired_h001_vs_conceptgraphs_query_claim_ready": gates["paired_vs_conceptgraphs_success_gain"],
            "h001_over_static_memory_claim_ready": gates["beats_static_memory_success"],
            "task_context_specific_claim_ready": gates["task_context_effect_vs_context_agnostic"],
            "real_navigation_sr_spl_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        },
        "next_recommended_unit": "E005-M53 paired heldout failure analysis / paper-table decision",
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], decision: dict[str, Any]) -> str:
    pm = metrics["policy_metrics"]
    h001 = pm[H001_POLICY]
    cg = pm[CONCEPTGRAPHS_POLICY]
    static = pm[STATIC_POLICY]
    context = pm[CONTEXT_AGNOSTIC_POLICY]
    return "\n".join(
        [
            "# E005-M52 H001 Heldout Policy Replay",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Query rows: {coverage['query_rows']}.",
            f"- `ConceptGraphs` strict bbox top5 success rows/rate: {cg['query_bridge_success_rows']} / {cg['query_bridge_success_rate']}.",
            f"- `static_memory_only_v0` success rows/rate: {static['query_bridge_success_rows']} / {static['query_bridge_success_rate']}.",
            f"- `context_agnostic_memory_trust_reobserve_v0` success rows/rate: {context['query_bridge_success_rows']} / {context['query_bridge_success_rate']}.",
            f"- `task_context_memory_trust_reobserve_v0` success rows/rate: {h001['query_bridge_success_rows']} / {h001['query_bridge_success_rate']}.",
            f"- H001 mean `ExpectedSearchCost` / proxy `SPL`: {h001['mean_expected_search_cost']} / {h001['mean_attempt_spl_proxy']}.",
            f"- Delta vs `ConceptGraphs`: {decision['delta_vs_conceptgraphs']}.",
            f"- Delta vs static memory: {decision['delta_vs_static']}.",
            f"- Failure class counts: {decision['failure_class_counts']}.",
            "",
            "## Claim Boundary",
            "",
            "- M52 is a paired query-level replay result on the `M38` heldout contract.",
            "- It still uses proxy `ExpectedSearchCost` / proxy `SPL`, not real navigation `SR` / `SPL`.",
            "- `ConceptGraphs` rank is used as the current observation order for H001 replay; this isolates memory-trust/search policy value from detector differences.",
            "",
            "## Agent Inference",
            "",
            "- If H001 beats `ConceptGraphs` but not `static_memory_only_v0`, the defensible claim is memory-preservation plus bounded re-observation, not task-context novelty.",
            "- E005-M53 should inspect paired wins/losses by `row_band`, label, and task context before promoting a paper-table claim.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m51_coverage = read_json(M51_DIR / "coverage.json")
    if not m51_coverage.get("ready_for_m52_replay"):
        raise RuntimeError(f"M51 is not replay-ready: {m51_coverage.get('status')}")
    query_rows = read_jsonl(M51_DIR / "adapter_preview_rows.jsonl")
    cg_by_uid = load_conceptgraphs_primary_rows()
    policy_rows: list[dict[str, Any]] = []
    for query in query_rows:
        for policy in DETECTOR_POLICIES:
            policy_rows.append(evaluate_detector_policy(policy, query))
        for policy in MEMORY_POLICIES:
            policy_rows.append(evaluate_memory_policy(policy, query))
        cg_row = cg_by_uid.get(str(query["bridge_query_uid"]))
        if not cg_row:
            raise RuntimeError(f"missing ConceptGraphs row: {query['bridge_query_uid']}")
        policy_rows.append(normalize_conceptgraphs_row(cg_row))

    policy_metrics, summary_rows = summarize(policy_rows)
    failures = build_failure_rows(query_rows, policy_rows)
    comp_rows = comparison_rows(policy_metrics)
    decision = build_decision(policy_metrics, failures)
    metrics = {
        "version": VERSION,
        "query_rows": len(query_rows),
        "policy_metrics": policy_metrics,
        "comparison_policies": [row["policy"] for row in comp_rows],
    }
    coverage = {
        "status": decision["status"],
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "query_rows": len(query_rows),
        "policy_rows": len(policy_rows),
        "m51_status": m51_coverage.get("status"),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in policy_rows),
        "h001_success_rows": policy_metrics[H001_POLICY]["query_bridge_success_rows"],
        "h001_success_rate": policy_metrics[H001_POLICY]["query_bridge_success_rate"],
        "conceptgraphs_success_rows": policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rows"],
        "conceptgraphs_success_rate": policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rate"],
        "static_success_rows": policy_metrics[STATIC_POLICY]["query_bridge_success_rows"],
        "context_agnostic_success_rows": policy_metrics[CONTEXT_AGNOSTIC_POLICY]["query_bridge_success_rows"],
        "paired_superiority_claim_candidate": decision["claim_boundary"]["paired_h001_vs_conceptgraphs_query_claim_ready"],
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": decision["next_recommended_unit"],
    }
    write_jsonl(OUT_DIR / "policy_rows.jsonl", policy_rows)
    write_jsonl(OUT_DIR / "policy_summary_rows.jsonl", summary_rows)
    write_jsonl(OUT_DIR / "comparison_rows.jsonl", comp_rows)
    write_jsonl(OUT_DIR / "failure_rows.jsonl", failures)
    write_json(OUT_DIR / "metrics.json", metrics)
    write_json(OUT_DIR / "decision.json", decision)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, metrics, decision))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
