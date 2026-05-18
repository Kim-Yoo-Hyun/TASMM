#!/usr/bin/env python3
"""Write the E004-M02 metric contract for task-context memory trust."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M75_DIR = REPO_ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
DEFAULT_M01_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M01_transition_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M02_metric_contract_v0"
VERSION = "e004_m02_metric_contract_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_first_jsonl(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def present_keys(row: dict[str, Any], keys: list[str]) -> dict[str, bool]:
    return {key: key in row for key in keys}


def build_contract(m75_dir: Path, m01_dir: Path) -> dict[str, Any]:
    metrics = load_json(m75_dir / "metrics.json")
    m01_decision = load_json(m01_dir / "decision.json")
    sample_query = load_first_jsonl(m75_dir / "query_bridge_rows.jsonl")
    sample_policy = load_first_jsonl(m75_dir / "policy_rows.jsonl")

    required_query_fields = [
        "bridge_query_uid",
        "row_uid",
        "base_row_uid",
        "task_context_id",
        "label_canonical",
        "current_rescan_id",
        "pair_uid",
        "query_slice_id",
        "row_band",
        "old_memory_is_stale",
        "expected_memory_state",
        "same_label_detector_proposal_count",
        "old_location_dead_end_expected",
    ]
    required_policy_fields = [
        "row_uid",
        "policy",
        "query_bridge_success",
        "expected_search_cost",
        "attempt_spl_proxy",
        "returned_location_count",
        "old_location_dead_end_avoided",
        "deployable_policy",
    ]

    input_readiness = {
        "m75_query_rows": metrics.get("query_rows"),
        "m75_target_detected_rows": metrics.get("query_target_detected_rows"),
        "required_query_fields_present": present_keys(sample_query, required_query_fields),
        "required_policy_fields_present": present_keys(sample_policy, required_policy_fields),
    }
    input_readiness["query_contract_ready"] = all(input_readiness["required_query_fields_present"].values())
    input_readiness["policy_metric_contract_ready"] = all(input_readiness["required_policy_fields_present"].values())

    contract = {
        "version": VERSION,
        "source_artifacts": {
            "e003_m75": str(m75_dir),
            "e004_m01": str(m01_dir),
        },
        "status": "e004_m02_metric_contract_ready"
        if input_readiness["query_contract_ready"] and input_readiness["policy_metric_contract_ready"]
        else "e004_m02_metric_contract_needs_input_repair",
        "input_readiness": input_readiness,
        "task_contexts": {
            "routine_fetch": {
                "memory_trust_mode": "conservative",
                "re_observation_mode": "low_budget",
                "objective": "avoid over-search while suppressing clear stale old-location dead ends",
                "expected_budget_behavior": "prefer top1/top3 unless stale/dead-end evidence is present",
            },
            "high_value_fetch": {
                "memory_trust_mode": "recall_oriented",
                "re_observation_mode": "expanded_budget",
                "objective": "accept higher search cost when stale memory or detector ambiguity makes target loss costly",
                "expected_budget_behavior": "allow top5-style expansion under stale/review states",
            },
            "noisy_high_value_fetch": {
                "memory_trust_mode": "uncertainty_aware",
                "re_observation_mode": "bounded_verification",
                "objective": "avoid both stale old-location failure and unbounded false-positive chasing",
                "expected_budget_behavior": "expand only when detector ambiguity or stale evidence passes a fixed gate",
            },
        },
        "allowed_policy_inputs": [
            "task_context_id",
            "label_canonical",
            "current_rescan_id",
            "pair_uid",
            "query_slice_id or row_band when derived before target matching",
            "old_memory_is_stale",
            "expected_memory_state",
            "same_label_detector_proposal_count",
            "detector proposal confidence/centroid/count fields before target matching",
            "path/search-cost proxy fields when available",
        ],
        "blocked_policy_inputs": [
            "target_uid",
            "object_instance_id_rescan",
            "query_target_best_proposal_uid",
            "query_target_best_match_distance_m",
            "query_target_rank_by_detector_score",
            "target_recall_best_match_distance_m",
            "false_positive_before_target_count",
            "query_bridge_success",
            "success/failure class labels",
        ],
        "evaluation_only_fields": [
            "old_location_dead_end_expected",
            "query_bridge_success",
            "expected_search_cost",
            "attempt_spl_proxy",
            "old_location_dead_end_avoided",
        ],
        "policy_family_to_implement_next": {
            "id": "task_context_memory_trust_reobserve_v0",
            "decision_outputs": [
                "memory_trust_level",
                "re_observation_budget",
                "candidate_visit_budget",
                "candidate_visit_order",
                "old_location_dead_end_guard",
            ],
            "must_compare_against": [
                "detector_task_budget_v0",
                "detector_top1_v0",
                "detector_top3_v0",
                "detector_top5_v0",
                "bounded_old_memory_distance_guard_adaptive_top5_v0",
                "oracle_target_first_task_budget_upper_bound_v0",
            ],
            "non_goal": "do not optimize a task-agnostic top-k expansion",
        },
        "metrics": {
            "primary": [
                "budgeted query success",
                "ExpectedSearchCost",
                "AttemptSPL proxy",
                "old-location dead-end avoided rate",
            ],
            "task_context_specific": [
                "routine_fetch cost increase vs detector_task_budget_v0",
                "high_value_fetch success gain vs routine-conservative budget",
                "noisy_high_value_fetch false-positive over-search control",
                "task-context ablation delta against context-agnostic thresholds",
            ],
            "diagnostic": [
                "target_detected_rate",
                "same_label_detector_proposal_count",
                "returned_location_count",
                "failure class split: detector recall miss / rank-budget gap / over-search",
            ],
        },
        "success_gates_for_e004_m03": {
            "gate_1_task_context_effect": "at least one task-context-specific policy decision changes success/cost tradeoff vs context-agnostic bounded repair",
            "gate_2_cost_guard": "routine_fetch must not simply inherit high_value top5 expansion when no stale/dead-end evidence exists",
            "gate_3_bounded_repair_guard": "high_value/noisy_high_value may improve success, but mean ExpectedSearchCost must stay below unbounded repair",
            "gate_4_claim_boundary": "no real navigation SR/SPL or final real RGB-D/open-vocabulary robustness claim from E004-M03 alone",
        },
        "next_unit": {
            "id": "E004-M03",
            "name": "implement and evaluate task_context_memory_trust_reobserve_v0",
            "expected_command": "python experiments/E004_task_context_memory_trust/tools/evaluate_m03_memory_trust_policy.py",
        },
        "inherits_claim_boundary_from_m01": m01_decision.get("claim_boundary", {}),
    }
    return contract


def build_report(contract: dict[str, Any]) -> str:
    ready = contract["input_readiness"]
    return "\n".join(
        [
            "# E004-M02 Metric Contract",
            "",
            "## Status",
            "",
            contract["status"],
            "",
            "## 사실",
            "",
            f"- Source E003-M75 query rows: {ready['m75_query_rows']}.",
            f"- Source E003-M75 target detected rows: {ready['m75_target_detected_rows']}.",
            f"- Query contract ready: {ready['query_contract_ready']}.",
            f"- Policy metric contract ready: {ready['policy_metric_contract_ready']}.",
            "",
            "## 논문 주장",
            "",
            "- E004-M02 fixes the evaluation contract for task-context memory trust and re-observation decisions.",
            "- E004-M02 is not a method result and does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The next method unit should implement `task_context_memory_trust_reobserve_v0` and compare it against detector top-k, task-budget, bounded repair, and oracle policies.",
            "- The central risk is leakage: E004 must not use target rank, target match distance, false positives before target, success labels, or evaluation-only dead-end labels as policy inputs.",
            "- A positive E004 result must show task-context-specific tradeoffs, not merely higher top-k search.",
            "",
            "## Next",
            "",
            f"- {contract['next_unit']['id']}: {contract['next_unit']['name']}.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m75-dir", default=DEFAULT_M75_DIR, type=Path)
    parser.add_argument("--m01-dir", default=DEFAULT_M01_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    contract = build_contract(args.m75_dir, args.m01_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "contract.json", contract)
    write_text(args.out_dir / "report.md", build_report(contract))
    print(json.dumps({"status": contract["status"], "next_unit": contract["next_unit"]}, ensure_ascii=False, indent=2))
    return 0 if contract["status"] == "e004_m02_metric_contract_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
