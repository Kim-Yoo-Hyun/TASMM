#!/usr/bin/env python3
"""Plan the E004 transition gate from E003-M75 to task-context memory trust."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M75_DIR = REPO_ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M01_transition_gate_v0"
M01_VERSION = "e004_m01_transition_gate_v0"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def policy(metrics: dict[str, Any], name: str) -> dict[str, Any]:
    return metrics["policy_metrics"][name]


def task_context_variation(summary_rows: list[dict[str, Any]], policy_name: str) -> dict[str, Any]:
    rows = [
        row
        for row in summary_rows
        if row.get("policy") == policy_name and row.get("group_type") == "task_context"
    ]
    success_rates = {
        row["group_value"]: row.get("query_bridge_success_rate")
        for row in rows
    }
    concrete_rates = [float(rate) for rate in success_rates.values() if rate is not None]
    spread = round(max(concrete_rates) - min(concrete_rates), 6) if concrete_rates else None
    return {
        "success_rate_by_task_context": success_rates,
        "success_rate_spread": spread,
        "task_context_specific_effect_ready": bool(spread is not None and spread >= 0.05),
    }


def build_report(coverage: dict[str, Any], decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E004-M01 Transition Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Source artifact: `{coverage['m75_dir']}`.",
            f"- M75 query rows: {coverage['m75_query_rows']}.",
            f"- M75 target detected rows/rate: {coverage['m75_target_detected_rows']} / {coverage['m75_target_detected_rate']}.",
            f"- Task-budget success rows/rate: {coverage['task_budget_success_rows']} / {coverage['task_budget_success_rate']}.",
            f"- Bounded repair success rows/rate: {coverage['bounded_success_rows']} / {coverage['bounded_success_rate']}.",
            f"- Bounded success delta vs task budget: {coverage['bounded_success_delta_vs_task']}.",
            f"- Task-budget mean `ExpectedSearchCost`: {coverage['task_budget_mean_expected_search_cost']}.",
            f"- Bounded mean `ExpectedSearchCost`: {coverage['bounded_mean_expected_search_cost']}.",
            f"- Unbounded mean `ExpectedSearchCost`: {coverage['unbounded_mean_expected_search_cost']}.",
            f"- Task-context-specific effect ready: {coverage['task_context_specific_effect_ready']}.",
            "",
            "## 논문 주장",
            "",
            "- E004-M01 supports starting an E004 task-context memory trust / re-observation decision experiment.",
            "- E004-M01 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            f"- {decision['rationale']}",
            "- E004 must convert bounded repair into a task-conditioned memory-trust decision, not a generic expansion of top-k search.",
            "- E004 must avoid using target identity, matched proposal labels, or post-hoc success labels as policy inputs.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E004-M02 implementation planning.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m75-dir", default=DEFAULT_M75_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    m75_metrics = load_json(args.m75_dir / "metrics.json")
    m75_route = load_json(args.m75_dir / "route_decision.json")
    summary_rows = load_jsonl(args.m75_dir / "policy_summary_rows.jsonl")

    task = policy(m75_metrics, "detector_task_budget_v0")
    bounded = policy(m75_metrics, "bounded_old_memory_distance_guard_adaptive_top5_v0")
    unbounded = policy(m75_metrics, "unbounded_old_memory_distance_guard_until_target_v0")
    variation = task_context_variation(summary_rows, "bounded_old_memory_distance_guard_adaptive_top5_v0")

    bounded_delta = int(bounded["query_bridge_success_rows"]) - int(task["query_bridge_success_rows"])
    cost_increase = float(bounded["mean_expected_search_cost"]) - float(task["mean_expected_search_cost"])
    checks = {
        "bounded_gain_positive": bounded_delta > 0,
        "bounded_gain_large_enough_for_next_gate": bounded_delta >= 10,
        "bounded_cost_below_unbounded": float(bounded["mean_expected_search_cost"]) < float(unbounded["mean_expected_search_cost"]),
        "detector_bridge_large_enough_for_gate": int(m75_metrics["query_rows"]) >= 50,
        "target_detection_high_enough_for_gate": float(m75_metrics["query_target_detected_rate"]) >= 0.75,
        "task_context_specific_effect_ready": variation["task_context_specific_effect_ready"],
    }

    hard_pass = (
        checks["bounded_gain_positive"]
        and checks["bounded_gain_large_enough_for_next_gate"]
        and checks["bounded_cost_below_unbounded"]
        and checks["detector_bridge_large_enough_for_gate"]
        and checks["target_detection_high_enough_for_gate"]
    )
    status = "e004_transition_ready_with_constraints" if hard_pass else "e004_transition_not_ready"
    selected_next = "E004-M02 implementation plan" if hard_pass else "repair E003 bridge before E004"
    rationale = (
        "M75 gives a real-proposal query-level signal: bounded repair improves success by "
        f"{bounded_delta} rows over task budget, but it increases mean search cost by {cost_increase:.6f} "
        "and does not yet show a task-context-specific effect."
    )
    decision = {
        "checks": checks,
        "claim_boundary": {
            "deployable_search_policy_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "e004_required_contract": {
            "allowed_inputs": [
                "task_context_id",
                "staleness/motion metadata available before evaluation",
                "old memory centroid",
                "current detector proposal confidence/centroid/count",
                "path/search-cost proxy if available",
            ],
            "blocked_inputs": [
                "target_uid",
                "matched_3dssg_instance_id",
                "match_distance_m",
                "query success/failure label",
                "post-hoc target rank",
            ],
            "required_metrics": [
                "ExpectedSearchCost",
                "budgeted query success",
                "old-location dead-end avoidance",
                "AttemptSPL proxy",
                "over-search rate",
                "task-context ablation delta",
            ],
        },
        "m75_selected_next_route": m75_route.get("selected_next_route"),
        "rationale": rationale,
        "selected_next_unit": selected_next,
    }

    coverage = {
        "bounded_mean_expected_search_cost": bounded["mean_expected_search_cost"],
        "bounded_success_delta_vs_task": bounded_delta,
        "bounded_success_rate": bounded["query_bridge_success_rate"],
        "bounded_success_rows": bounded["query_bridge_success_rows"],
        "cost_increase_vs_task_budget": round(cost_increase, 6),
        "m01_version": M01_VERSION,
        "m75_dir": str(args.m75_dir),
        "m75_query_rows": m75_metrics["query_rows"],
        "m75_target_detected_rate": m75_metrics["query_target_detected_rate"],
        "m75_target_detected_rows": m75_metrics["query_target_detected_rows"],
        "next_recommended_unit": selected_next,
        "real_navigation_sr_spl_claim_ready": False,
        "real_rgbd_open_vocab_robustness_claim_ready": False,
        "selected_next_route": decision["selected_next_unit"],
        "status": status,
        "task_budget_mean_expected_search_cost": task["mean_expected_search_cost"],
        "task_budget_success_rate": task["query_bridge_success_rate"],
        "task_budget_success_rows": task["query_bridge_success_rows"],
        "task_context_specific_effect_ready": variation["task_context_specific_effect_ready"],
        "task_context_variation": variation,
        "unbounded_mean_expected_search_cost": unbounded["mean_expected_search_cost"],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "decision.json", decision)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, decision))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if hard_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
