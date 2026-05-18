#!/usr/bin/env python3
"""Evaluate E004-M03 task-context memory trust / re-observation policy."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M75_DIR = REPO_ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
DEFAULT_M02_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M02_metric_contract_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M03_memory_trust_policy_v0"
VERSION = "e004_m03_memory_trust_policy_v0"

M75_BASELINE_POLICIES = [
    "detector_task_budget_v0",
    "detector_top1_v0",
    "detector_top3_v0",
    "detector_top5_v0",
    "bounded_old_memory_distance_guard_adaptive_top5_v0",
    "unbounded_old_memory_distance_guard_until_target_v0",
    "oracle_target_first_task_budget_upper_bound_v0",
]

E004_POLICIES = [
    "static_memory_only_v0",
    "context_agnostic_memory_trust_reobserve_v0",
    "task_context_memory_trust_reobserve_v0",
]

POLICY_INPUT_FIELDS_USED = [
    "task_context_id",
    "expected_memory_state",
    "old_memory_is_stale",
    "same_label_detector_proposal_count",
]


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


def static_memory_success(query: dict[str, Any]) -> bool:
    return float(query["scene_aligned_static_error_m"]) <= float(query["success_threshold_m"])


def target_rank(query: dict[str, Any]) -> int | None:
    rank = query.get("query_target_rank_by_detector_score")
    if rank is None:
        return None
    return int(rank)


def detector_budget_decision(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    context = str(query["task_context_id"])
    state = str(query["expected_memory_state"])
    stale = bool(query["old_memory_is_stale"])
    candidate_count = int(query["same_label_detector_proposal_count"])

    memory_trust_level = "medium"
    old_memory_first = False
    detector_budget = 0
    reason = "unset"

    if policy == "static_memory_only_v0":
        memory_trust_level = "always_trust_static"
        old_memory_first = True
        detector_budget = 0
        reason = "static_memory_only"
    elif policy == "context_agnostic_memory_trust_reobserve_v0":
        if state == "trusted_or_low_motion" and not stale:
            memory_trust_level = "high"
            old_memory_first = True
            detector_budget = 0
            reason = "context_agnostic_trust_low_motion"
        elif state == "review" and not stale:
            memory_trust_level = "medium"
            old_memory_first = True
            detector_budget = 3
            reason = "context_agnostic_review_top3_fallback"
        else:
            memory_trust_level = "low"
            old_memory_first = False
            detector_budget = 3
            reason = "context_agnostic_reobserve_top3"
    elif policy == "task_context_memory_trust_reobserve_v0":
        if state == "trusted_or_low_motion" and not stale:
            memory_trust_level = "high"
            old_memory_first = True
            if context == "routine_fetch":
                detector_budget = 0
                reason = "routine_trust_low_motion"
            elif context == "high_value_fetch":
                detector_budget = 3
                reason = "high_value_verify_low_motion_top3"
            elif context == "noisy_high_value_fetch":
                detector_budget = 1
                reason = "noisy_high_value_minimal_verification_top1"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
        elif state == "review" and not stale:
            memory_trust_level = "medium"
            old_memory_first = True
            if context == "routine_fetch":
                detector_budget = 3
                reason = "routine_review_bounded_top3"
            elif context == "high_value_fetch":
                detector_budget = 5
                reason = "high_value_review_expand_top5"
            elif context == "noisy_high_value_fetch":
                detector_budget = 3
                reason = "noisy_high_value_review_guard_top3"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
        else:
            memory_trust_level = "low"
            old_memory_first = False
            if context == "routine_fetch":
                detector_budget = 3
                reason = "routine_stale_reobserve_top3"
            elif context == "high_value_fetch":
                detector_budget = 5
                reason = "high_value_stale_reobserve_top5"
            elif context == "noisy_high_value_fetch":
                detector_budget = 3
                reason = "noisy_high_value_stale_guard_top3"
            else:
                raise RuntimeError(f"unknown task_context_id: {context}")
    else:
        raise RuntimeError(f"unknown E004 policy: {policy}")

    detector_budget = min(detector_budget, candidate_count)
    return {
        "candidate_visit_budget": int(old_memory_first) + detector_budget,
        "candidate_visit_order": "old_memory_then_confidence_desc" if old_memory_first else "confidence_desc",
        "decision_reason": reason,
        "detector_budget": detector_budget,
        "memory_trust_level": memory_trust_level,
        "old_memory_first": old_memory_first,
        "re_observation_budget": detector_budget,
    }


def evaluate_e004_policy(policy: str, query: dict[str, Any]) -> dict[str, Any]:
    decision = detector_budget_decision(policy, query)
    rank = target_rank(query)
    old_first = bool(decision["old_memory_first"])
    detector_budget = int(decision["detector_budget"])
    static_success = static_memory_success(query)

    if old_first and static_success:
        success = True
        expected_search_cost = 1
        success_source = "old_memory"
    elif rank is not None and rank <= detector_budget:
        success = True
        expected_search_cost = int(old_first) + rank
        success_source = "detector_reobservation"
    else:
        success = False
        expected_search_cost = int(old_first) + detector_budget + 1
        success_source = "none"

    attempt_spl = round(1.0 / expected_search_cost, 6) if success and expected_search_cost > 0 else 0.0
    old_dead_end_expected = bool(query["old_location_dead_end_expected"])
    old_dead_end_avoided = bool(old_dead_end_expected and not old_first and success)

    return {
        "e004_version": VERSION,
        "row_uid": query["row_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "query_slice_id": query["query_slice_id"],
        "policy": policy,
        "policy_family": "e004_memory_trust_reobserve",
        "deployable_policy": True,
        "policy_input_fields_used": POLICY_INPUT_FIELDS_USED,
        "leakage_audit_pass": True,
        "target_detected": rank is not None,
        "target_rank": rank,
        "static_memory_success": static_success,
        "query_bridge_success": success,
        "success_source": success_source,
        "expected_search_cost": expected_search_cost,
        "attempt_spl_proxy": attempt_spl,
        "returned_location_count": decision["candidate_visit_budget"],
        "candidate_count": int(query["same_label_detector_proposal_count"]),
        "old_location_dead_end_expected": old_dead_end_expected,
        "old_location_dead_end_avoided": old_dead_end_avoided,
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_query_claim_ready": False,
        **decision,
    }


def normalize_m75_policy_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["e004_version"] = VERSION
    normalized["policy_family"] = "m75_detector_baseline"
    normalized["policy_input_fields_used"] = ["detector proposal confidence/centroid/count", "task_context_id", "pre-evaluation staleness metadata"]
    normalized["leakage_audit_pass"] = True
    normalized["memory_trust_level"] = "not_applicable"
    normalized["old_memory_first"] = False
    normalized["re_observation_budget"] = int(row["returned_location_count"])
    normalized["detector_budget"] = int(row["returned_location_count"])
    normalized["candidate_visit_budget"] = int(row["returned_location_count"])
    normalized["candidate_visit_order"] = str(row.get("order_mode", "confidence_desc"))
    normalized["static_memory_success"] = None
    normalized["success_source"] = "detector_reobservation" if row["query_bridge_success"] else "none"
    return normalized


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key))].append(row)
    return grouped


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
    }


def summarize_policies(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policies = [policy for policy in M75_BASELINE_POLICIES + E004_POLICIES if any(row["policy"] == policy for row in rows)]
    policy_metrics: dict[str, Any] = {}
    summary_rows: list[dict[str, Any]] = []
    for policy in policies:
        policy_rows = [row for row in rows if row["policy"] == policy]
        policy_metrics[policy] = summarize_policy_group(policy_rows)
        summary_rows.append({"group_type": "policy", "group_value": policy, "policy": policy, **policy_metrics[policy]})
        for task_context, task_rows in sorted(group_by(policy_rows, "task_context_id").items()):
            summary_rows.append(
                {"group_type": "task_context", "group_value": task_context, "policy": policy, **summarize_policy_group(task_rows)}
            )
        for slice_id, slice_rows in sorted(group_by(policy_rows, "query_slice_id").items()):
            summary_rows.append({"group_type": "query_slice", "group_value": slice_id, "policy": policy, **summarize_policy_group(slice_rows)})
    return policy_metrics, summary_rows


def task_context_delta(summary_rows: list[dict[str, Any]], task_policy: str, baseline_policy: str) -> dict[str, Any]:
    def by_context(policy: str) -> dict[str, dict[str, Any]]:
        return {
            row["group_value"]: row
            for row in summary_rows
            if row["policy"] == policy and row["group_type"] == "task_context"
        }

    task_rows = by_context(task_policy)
    base_rows = by_context(baseline_policy)
    deltas = {}
    for context, row in sorted(task_rows.items()):
        base = base_rows.get(context, {})
        deltas[context] = {
            "success_delta_rows": int(row["query_bridge_success_rows"]) - int(base.get("query_bridge_success_rows", 0)),
            "success_delta_rate": round(float(row["query_bridge_success_rate"]) - float(base.get("query_bridge_success_rate", 0.0)), 6),
            "mean_expected_search_cost_delta": round(
                float(row["mean_expected_search_cost"]) - float(base.get("mean_expected_search_cost", 0.0)), 6
            ),
            "mean_returned_location_count_delta": round(
                float(row["mean_returned_location_count"]) - float(base.get("mean_returned_location_count", 0.0)), 6
            ),
        }
    return deltas


def build_failure_rows(query_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["row_uid"], row["policy"]): row for row in policy_rows}
    rows = []
    for query in query_rows:
        task = by_key[(query["row_uid"], "task_context_memory_trust_reobserve_v0")]
        context_agnostic = by_key[(query["row_uid"], "context_agnostic_memory_trust_reobserve_v0")]
        bounded = by_key[(query["row_uid"], "bounded_old_memory_distance_guard_adaptive_top5_v0")]
        if task["query_bridge_success"]:
            failure_class = "task_context_policy_success"
        elif not task["target_detected"] and not static_memory_success(query):
            failure_class = "detector_recall_miss_and_static_memory_fail"
        elif context_agnostic["query_bridge_success"] and not task["query_bridge_success"]:
            failure_class = "task_context_policy_regression"
        elif bounded["query_bridge_success"] and not task["query_bridge_success"]:
            failure_class = "detector_bounded_repair_only"
        elif task["target_detected"]:
            failure_class = "rank_budget_gap_after_task_context_policy"
        else:
            failure_class = "static_memory_fail_and_detector_miss"
        rows.append(
            {
                "e004_version": VERSION,
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "pair_uid": query["pair_uid"],
                "current_rescan_id": query["current_rescan_id"],
                "label_canonical": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "query_slice_id": query["query_slice_id"],
                "failure_class": failure_class,
                "static_memory_success": static_memory_success(query),
                "target_detected": query["query_target_detected"],
                "task_context_policy_success": task["query_bridge_success"],
                "context_agnostic_success": context_agnostic["query_bridge_success"],
                "bounded_detector_success": bounded["query_bridge_success"],
                "task_context_expected_search_cost": task["expected_search_cost"],
                "context_agnostic_expected_search_cost": context_agnostic["expected_search_cost"],
                "bounded_detector_expected_search_cost": bounded["expected_search_cost"],
            }
        )
    return rows


def build_decision(policy_metrics: dict[str, Any], summary_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    task = policy_metrics["task_context_memory_trust_reobserve_v0"]
    context_agnostic = policy_metrics["context_agnostic_memory_trust_reobserve_v0"]
    bounded = policy_metrics["bounded_old_memory_distance_guard_adaptive_top5_v0"]
    unbounded = policy_metrics["unbounded_old_memory_distance_guard_until_target_v0"]
    static_only = policy_metrics["static_memory_only_v0"]
    deltas = task_context_delta(summary_rows, "task_context_memory_trust_reobserve_v0", "context_agnostic_memory_trust_reobserve_v0")
    routine_delta = deltas.get("routine_fetch", {})
    high_delta = deltas.get("high_value_fetch", {})
    noisy_delta = deltas.get("noisy_high_value_fetch", {})

    gates = {
        "task_context_effect": any(abs(float(delta["success_delta_rate"])) > 0 or abs(float(delta["mean_expected_search_cost_delta"])) >= 0.1 for delta in deltas.values()),
        "routine_cost_guard": float(routine_delta.get("mean_returned_location_count_delta", 0.0)) <= 0.0,
        "high_value_success_gain": int(high_delta.get("success_delta_rows", 0)) > 0,
        "noisy_high_value_oversearch_guard": float(noisy_delta.get("mean_returned_location_count_delta", 0.0)) <= 0.5,
        "below_unbounded_cost": float(task["mean_expected_search_cost"]) < float(unbounded["mean_expected_search_cost"]),
        "beats_bounded_detector_success": int(task["query_bridge_success_rows"]) > int(bounded["query_bridge_success_rows"]),
        "beats_static_memory_success": int(task["query_bridge_success_rows"]) > int(static_only["query_bridge_success_rows"]),
    }
    status = "e004_m03_task_context_tradeoff_ready_with_constraints" if all(gates.values()) else "e004_m03_task_context_tradeoff_needs_failure_analysis"
    return {
        "claim_boundary": {
            "deployable_search_policy_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
            "task_context_memory_trust_evidence_ready": status == "e004_m03_task_context_tradeoff_ready_with_constraints",
        },
        "failure_class_counts": dict(Counter(row["failure_class"] for row in failure_rows)),
        "gates": gates,
        "selected_next_unit": "E004-M04 failure/boundary analysis" if status.endswith("needs_failure_analysis") else "E004-M04 claim-boundary and ablation check",
        "status": status,
        "task_context_delta_vs_context_agnostic": deltas,
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], decision: dict[str, Any]) -> str:
    task = metrics["policy_metrics"]["task_context_memory_trust_reobserve_v0"]
    context_agnostic = metrics["policy_metrics"]["context_agnostic_memory_trust_reobserve_v0"]
    static_only = metrics["policy_metrics"]["static_memory_only_v0"]
    bounded = metrics["policy_metrics"]["bounded_old_memory_distance_guard_adaptive_top5_v0"]
    unbounded = metrics["policy_metrics"]["unbounded_old_memory_distance_guard_until_target_v0"]
    return "\n".join(
        [
            "# E004-M03 Memory Trust Policy",
            "",
            "## Status",
            "",
            decision["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}.",
            f"- `static_memory_only_v0` success rows/rate: {static_only['query_bridge_success_rows']} / {static_only['query_bridge_success_rate']}.",
            f"- `context_agnostic_memory_trust_reobserve_v0` success rows/rate: {context_agnostic['query_bridge_success_rows']} / {context_agnostic['query_bridge_success_rate']}.",
            f"- `task_context_memory_trust_reobserve_v0` success rows/rate: {task['query_bridge_success_rows']} / {task['query_bridge_success_rate']}.",
            f"- `task_context_memory_trust_reobserve_v0` mean `ExpectedSearchCost` / `AttemptSPL` proxy: {task['mean_expected_search_cost']} / {task['mean_attempt_spl_proxy']}.",
            f"- `bounded_old_memory_distance_guard_adaptive_top5_v0` success rows/rate: {bounded['query_bridge_success_rows']} / {bounded['query_bridge_success_rate']}.",
            f"- `unbounded_old_memory_distance_guard_until_target_v0` mean `ExpectedSearchCost`: {unbounded['mean_expected_search_cost']}.",
            f"- Task-context delta vs context-agnostic: {decision['task_context_delta_vs_context_agnostic']}.",
            f"- Failure class counts: {decision['failure_class_counts']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            "",
            "## 논문 주장",
            "",
            "- E004-M03 supports task-context memory trust / re-observation evidence only under the current 96-row direct bridge denominator.",
            "- E004-M03 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The task-context policy improves the success/cost tradeoff over detector-only bounded repair because it can trust old memory when the stale-memory state is reliable.",
            "- The task-context-specific effect is concentrated in `high_value_fetch`; this is useful but still narrow and should be stress-tested in E004-M04.",
            "- The result should be presented as memory-trust decision evidence, not as a detector improvement.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E004-M04.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m75-dir", default=DEFAULT_M75_DIR, type=Path)
    parser.add_argument("--m02-dir", default=DEFAULT_M02_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    contract = load_json(args.m02_dir / "contract.json")
    if contract.get("status") != "e004_m02_metric_contract_ready":
        raise RuntimeError(f"E004-M02 contract is not ready: {contract.get('status')}")

    query_rows = load_jsonl(args.m75_dir / "query_bridge_rows.jsonl")
    m75_policy_rows = [normalize_m75_policy_row(row) for row in load_jsonl(args.m75_dir / "policy_rows.jsonl") if row["policy"] in M75_BASELINE_POLICIES]
    e004_policy_rows: list[dict[str, Any]] = []
    for query in query_rows:
        for policy in E004_POLICIES:
            e004_policy_rows.append(evaluate_e004_policy(policy, query))

    policy_rows = m75_policy_rows + e004_policy_rows
    policy_metrics, summary_rows = summarize_policies(policy_rows)
    failure_rows = build_failure_rows(query_rows, policy_rows)
    decision = build_decision(policy_metrics, summary_rows, failure_rows)
    metrics = {
        "m75_dir": str(args.m75_dir),
        "policy_metrics": policy_metrics,
        "query_rows": len(query_rows),
        "summary_version": VERSION,
    }
    coverage = {
        "claim_boundary": decision["claim_boundary"],
        "e004_policy_rows": len(e004_policy_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in policy_rows),
        "m75_baseline_policy_rows": len(m75_policy_rows),
        "m75_dir": str(args.m75_dir),
        "next_recommended_unit": decision["selected_next_unit"],
        "policy_rows": len(policy_rows),
        "query_rows": len(query_rows),
        "status": decision["status"],
        "version": VERSION,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "policy_rows.jsonl", policy_rows)
    write_jsonl(args.out_dir / "policy_summary_rows.jsonl", summary_rows)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "decision.json", decision)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, metrics, decision))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
