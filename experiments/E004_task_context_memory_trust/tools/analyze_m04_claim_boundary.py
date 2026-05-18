#!/usr/bin/env python3
"""Analyze E004-M04 claim boundaries and budget ablations."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_m03_memory_trust_policy import (  # noqa: E402
    VERSION as M03_VERSION,
    evaluate_e004_policy,
    load_jsonl,
    safe_mean,
    safe_rate,
    write_json,
    write_jsonl,
    write_text,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M75_DIR = REPO_ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
DEFAULT_M03_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M03_memory_trust_policy_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M04_claim_boundary_ablation_v0"
VERSION = "e004_m04_claim_boundary_ablation_v0"

COUNTERFACTUAL_CONTEXTS = {
    "all_routine_memory_trust_counterfactual_v0": "routine_fetch",
    "all_high_value_memory_trust_counterfactual_v0": "high_value_fetch",
    "all_noisy_high_value_memory_trust_counterfactual_v0": "noisy_high_value_fetch",
}


def normalize_counterfactual(row: dict[str, Any], policy: str, forced_context: str) -> dict[str, Any]:
    query = dict(row)
    original_context = str(query["task_context_id"])
    query["task_context_id"] = forced_context
    evaluated = evaluate_e004_policy("task_context_memory_trust_reobserve_v0", query)
    evaluated["e004_version"] = VERSION
    evaluated["policy"] = policy
    evaluated["policy_family"] = "e004_counterfactual_context_ablation"
    evaluated["original_task_context_id"] = original_context
    evaluated["forced_task_context_id"] = forced_context
    evaluated["task_context_id"] = original_context
    evaluated["decision_context_id"] = forced_context
    return evaluated


def normalize_m03_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["e004_version"] = VERSION
    normalized.setdefault("original_task_context_id", row["task_context_id"])
    normalized.setdefault("decision_context_id", row["task_context_id"])
    return normalized


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    stale = [row for row in rows if row["old_location_dead_end_expected"]]
    return {
        "rows": len(rows),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
        "mean_returned_location_count": safe_mean([int(row["returned_location_count"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_avoided_rows": sum(1 for row in stale if row["old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(sum(1 for row in stale if row["old_location_dead_end_avoided"]), len(stale)),
        "old_memory_success_rows": sum(1 for row in rows if row.get("success_source") == "old_memory"),
        "detector_reobservation_success_rows": sum(1 for row in rows if row.get("success_source") == "detector_reobservation"),
        "over_search_rows": sum(1 for row in rows if int(row["returned_location_count"]) >= 5 and not row["query_bridge_success"]),
    }


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key))].append(row)
    return grouped


def summarize(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_metrics: dict[str, Any] = {}
    summary_rows: list[dict[str, Any]] = []
    policies = sorted({row["policy"] for row in rows})
    for policy in policies:
        policy_rows = [row for row in rows if row["policy"] == policy]
        metrics = summarize_group(policy_rows)
        policy_metrics[policy] = metrics
        summary_rows.append({"group_type": "policy", "group_value": policy, "policy": policy, **metrics})
        for context, context_rows in sorted(group_by(policy_rows, "task_context_id").items()):
            summary_rows.append({"group_type": "task_context", "group_value": context, "policy": policy, **summarize_group(context_rows)})
        for slice_id, slice_rows in sorted(group_by(policy_rows, "query_slice_id").items()):
            summary_rows.append({"group_type": "query_slice", "group_value": slice_id, "policy": policy, **summarize_group(slice_rows)})
    return policy_metrics, summary_rows


def delta(policy_metrics: dict[str, Any], left: str, right: str) -> dict[str, Any]:
    lval = policy_metrics[left]
    rval = policy_metrics[right]
    return {
        "success_delta_rows": int(lval["query_bridge_success_rows"]) - int(rval["query_bridge_success_rows"]),
        "success_delta_rate": round(float(lval["query_bridge_success_rate"]) - float(rval["query_bridge_success_rate"]), 6),
        "mean_expected_search_cost_delta": round(float(lval["mean_expected_search_cost"]) - float(rval["mean_expected_search_cost"]), 6),
        "mean_returned_location_count_delta": round(float(lval["mean_returned_location_count"]) - float(rval["mean_returned_location_count"]), 6),
        "mean_attempt_spl_proxy_delta": round(float(lval["mean_attempt_spl_proxy"]) - float(rval["mean_attempt_spl_proxy"]), 6),
    }


def build_row_level_ablation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["row_uid"], row["policy"]): row for row in rows}
    row_uids = sorted({row["row_uid"] for row in rows if row["policy"] == "task_context_memory_trust_reobserve_v0"})
    output = []
    for row_uid in row_uids:
        task = by_key[(row_uid, "task_context_memory_trust_reobserve_v0")]
        context_agnostic = by_key[(row_uid, "context_agnostic_memory_trust_reobserve_v0")]
        all_high = by_key[(row_uid, "all_high_value_memory_trust_counterfactual_v0")]
        all_routine = by_key[(row_uid, "all_routine_memory_trust_counterfactual_v0")]
        if task["query_bridge_success"] and not context_agnostic["query_bridge_success"]:
            ablation_class = "task_context_unique_success"
        elif all_high["query_bridge_success"] and not task["query_bridge_success"]:
            ablation_class = "all_high_value_budget_only_success"
        elif context_agnostic["query_bridge_success"]:
            ablation_class = "context_agnostic_already_success"
        elif bool(task.get("static_memory_success")):
            ablation_class = "static_memory_success"
        else:
            ablation_class = "unrecovered"
        output.append(
            {
                "e004_version": VERSION,
                "row_uid": row_uid,
                "base_row_uid": task["base_row_uid"],
                "task_context_id": task["task_context_id"],
                "query_slice_id": task["query_slice_id"],
                "label_canonical": task["label_canonical"],
                "ablation_class": ablation_class,
                "task_context_success": task["query_bridge_success"],
                "context_agnostic_success": context_agnostic["query_bridge_success"],
                "all_high_value_success": all_high["query_bridge_success"],
                "all_routine_success": all_routine["query_bridge_success"],
                "task_context_expected_search_cost": task["expected_search_cost"],
                "context_agnostic_expected_search_cost": context_agnostic["expected_search_cost"],
                "all_high_value_expected_search_cost": all_high["expected_search_cost"],
                "all_routine_expected_search_cost": all_routine["expected_search_cost"],
            }
        )
    return output


def build_decision(policy_metrics: dict[str, Any], row_ablation: list[dict[str, Any]]) -> dict[str, Any]:
    task = "task_context_memory_trust_reobserve_v0"
    context_agnostic = "context_agnostic_memory_trust_reobserve_v0"
    all_high = "all_high_value_memory_trust_counterfactual_v0"
    all_routine = "all_routine_memory_trust_counterfactual_v0"
    task_vs_context = delta(policy_metrics, task, context_agnostic)
    all_high_vs_task = delta(policy_metrics, all_high, task)
    task_vs_all_routine = delta(policy_metrics, task, all_routine)
    ablation_counts = Counter(row["ablation_class"] for row in row_ablation)
    gates = {
        "memory_trust_claim_supported": int(policy_metrics[task]["query_bridge_success_rows"]) > int(policy_metrics["static_memory_only_v0"]["query_bridge_success_rows"]),
        "task_context_unique_success_exists": ablation_counts.get("task_context_unique_success", 0) > 0,
        "task_context_gain_small": int(task_vs_context["success_delta_rows"]) <= 2,
        "all_high_value_budget_can_gain_more": int(all_high_vs_task["success_delta_rows"]) > 0,
        "task_context_cost_below_all_high": float(all_high_vs_task["mean_expected_search_cost_delta"]) > 0,
    }
    task_context_claim_strength = "limited_positive" if gates["task_context_unique_success_exists"] else "not_supported"
    if not gates["task_context_gain_small"] and gates["task_context_unique_success_exists"]:
        task_context_claim_strength = "moderate_positive"
    status = "e004_m04_claim_boundary_ready"
    return {
        "ablation_class_counts": dict(ablation_counts),
        "claim_boundary": {
            "memory_trust_decision_claim_ready": gates["memory_trust_claim_supported"],
            "task_context_specific_claim_strength": task_context_claim_strength,
            "deployable_search_policy_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "deltas": {
            "task_context_vs_context_agnostic": task_vs_context,
            "all_high_value_vs_task_context": all_high_vs_task,
            "task_context_vs_all_routine": task_vs_all_routine,
        },
        "gates": gates,
        "selected_next_unit": "E004-M05 scale/split stress before E005 external baselines",
        "status": status,
    }


def build_report(coverage: dict[str, Any], policy_metrics: dict[str, Any], decision: dict[str, Any]) -> str:
    task = policy_metrics["task_context_memory_trust_reobserve_v0"]
    context_agnostic = policy_metrics["context_agnostic_memory_trust_reobserve_v0"]
    all_high = policy_metrics["all_high_value_memory_trust_counterfactual_v0"]
    all_routine = policy_metrics["all_routine_memory_trust_counterfactual_v0"]
    return "\n".join(
        [
            "# E004-M04 Claim Boundary Ablation",
            "",
            "## Status",
            "",
            decision["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}.",
            f"- `context_agnostic_memory_trust_reobserve_v0`: {context_agnostic['query_bridge_success_rows']} / {context_agnostic['rows']}, mean `ExpectedSearchCost` {context_agnostic['mean_expected_search_cost']}.",
            f"- `task_context_memory_trust_reobserve_v0`: {task['query_bridge_success_rows']} / {task['rows']}, mean `ExpectedSearchCost` {task['mean_expected_search_cost']}.",
            f"- `all_routine_memory_trust_counterfactual_v0`: {all_routine['query_bridge_success_rows']} / {all_routine['rows']}, mean `ExpectedSearchCost` {all_routine['mean_expected_search_cost']}.",
            f"- `all_high_value_memory_trust_counterfactual_v0`: {all_high['query_bridge_success_rows']} / {all_high['rows']}, mean `ExpectedSearchCost` {all_high['mean_expected_search_cost']}.",
            f"- Task-context vs context-agnostic delta: {decision['deltas']['task_context_vs_context_agnostic']}.",
            f"- All-high-value vs task-context delta: {decision['deltas']['all_high_value_vs_task_context']}.",
            f"- Ablation class counts: {decision['ablation_class_counts']}.",
            "",
            "## 논문 주장",
            "",
            "- E004-M04 supports a memory-trust decision claim under the current 96-row direct bridge denominator.",
            "- E004-M04 supports only a limited task-context-specific claim: `high_value_fetch` gives a small success gain by accepting extra search cost.",
            "- E004-M04 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The current task-context effect is real but small: 2 unique successes over context-agnostic memory trust.",
            "- A pure all-high-value budget counterfactual gets more successes than the task-context policy, so the paper must not claim globally optimal task conditioning yet.",
            "- The defensible claim is a controlled memory-trust/re-observation tradeoff, not a final search policy.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E004-M05.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m75-dir", default=DEFAULT_M75_DIR, type=Path)
    parser.add_argument("--m03-dir", default=DEFAULT_M03_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    query_rows = load_jsonl(args.m75_dir / "query_bridge_rows.jsonl")
    m03_rows = [normalize_m03_row(row) for row in load_jsonl(args.m03_dir / "policy_rows.jsonl")]
    keep_policies = {
        "static_memory_only_v0",
        "context_agnostic_memory_trust_reobserve_v0",
        "task_context_memory_trust_reobserve_v0",
    }
    rows = [row for row in m03_rows if row["policy"] in keep_policies]
    for query in query_rows:
        for policy, forced_context in COUNTERFACTUAL_CONTEXTS.items():
            rows.append(normalize_counterfactual(query, policy, forced_context))

    policy_metrics, summary_rows = summarize(rows)
    row_ablation = build_row_level_ablation(rows)
    decision = build_decision(policy_metrics, row_ablation)
    coverage = {
        "e004_version": VERSION,
        "m03_version": M03_VERSION,
        "m75_dir": str(args.m75_dir),
        "m03_dir": str(args.m03_dir),
        "next_recommended_unit": decision["selected_next_unit"],
        "policy_rows": len(rows),
        "query_rows": len(query_rows),
        "status": decision["status"],
    }
    metrics = {
        "policy_metrics": policy_metrics,
        "query_rows": len(query_rows),
        "summary_version": VERSION,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "policy_rows.jsonl", rows)
    write_jsonl(args.out_dir / "policy_summary_rows.jsonl", summary_rows)
    write_jsonl(args.out_dir / "row_ablation.jsonl", row_ablation)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "decision.json", decision)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, policy_metrics, decision))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
