#!/usr/bin/env python3
"""Materialize E006-M07 utility metric rows after frozen policy outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
M05_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M05_schema_pair_materialization_smoke_v0"
)
M06_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M06_baseline_policy_materialization_smoke_v0"
)
DEFAULT_OUT_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M07_utility_metric_materialization_smoke_v0"
)
E007_M04_ROWS = (
    REPO_ROOT
    / "experiments/E007_navigation_path_cost_bridge/artifacts/"
    / "E007-M04_path_cost_policy_metrics_v0/query_policy_metric_rows.jsonl"
)

VERSION = "e006_m07_utility_metric_materialization_smoke_v0"
PATH_UNIT_M = 5.0
BUDGET_OVERRUN_PENALTY = 10.0
PRIMARY_POLICY = "h001_task_conditioned_memory_trust_v0"

BLOCKED_TERMS = [
    "target_uid",
    "target_object_instance_id",
    "eval_goal_coordinate",
    "oracle_viewpoint",
    "success_label",
    "target_rank",
    "target_distance",
]

TASK_PROXY_BY_PROFILE = {
    "routine_fetch_v0": "routine_fetch",
    "high_value_fetch_v0": "high_value_fetch",
    "urgent_fetch_v0": "routine_fetch",
    "inspection_v0": "high_value_fetch",
    "avoid_false_alarm_v0": "routine_fetch",
    "low_value_fast_v0": "routine_fetch",
    "high_value_slow_v0": "high_value_fetch",
}

EVAL_POLICY_BY_POLICY_ID = {
    "static_stale_memory_v0": "real_static_memory_only_v0",
    "detector_confidence_topk_v0": "real_detector_confidence_top5_v0",
    "fixed_topk_always5_v0": "real_detector_confidence_top5_v0",
    "context_agnostic_memory_trust_reobserve_v0": "real_context_agnostic_memory_trust_reobserve_v0",
    "all_high_value_memory_trust_counterfactual_v0": "h001_real_task_context_memory_trust_v0",
    "all_reobserve_budget5_v0": "real_detector_confidence_top5_v0",
    "risk_threshold_only_v0": "real_static_memory_only_v0",
    "path_cost_only_reachable_first_v0": "real_context_agnostic_memory_trust_reobserve_v0",
    "proposal_reliability_only_v0": "real_detector_confidence_top5_v0",
    "dev_best_global_mixture_v0": "real_context_agnostic_memory_trust_reobserve_v0",
    "conceptgraphs_only_open_vocab_map_v0": "conceptgraphs_only_strict_top5_v0",
    "open3dsg_vocab_only_scene_graph_v0": "conceptgraphs_only_strict_top5_v0",
    "no_task_context_v0": "real_context_agnostic_memory_trust_reobserve_v0",
    "no_staleness_memory_trust_v0": "real_detector_confidence_top5_v0",
    "no_reobserve_budget_v0": "real_static_memory_only_v0",
    "no_path_search_cost_v0": "h001_real_task_context_memory_trust_v0",
    "task_context_only_v0": "real_detector_confidence_top5_v0",
    "h001_task_conditioned_memory_trust_v0": "h001_then_conceptgraphs_top5_on_observed_miss_v0",
}

ORACLE_POLICIES = {
    "oracle_target_available_v0",
    "oracle_context_utility_v0",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stable_hash(raw: str, length: int = 12) -> str:
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_profiles() -> dict[str, dict[str, Any]]:
    schema = read_json(M05_ROOT / "task_context_schema.json")
    return {row["utility_profile_id"]: row for row in schema.get("profiles", [])}


def index_eval_rows() -> tuple[
    dict[str, str],
    dict[tuple[str, str, str], dict[str, Any]],
]:
    hash_to_base: dict[str, str] = {}
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in read_jsonl(E007_M04_ROWS):
        base = str(row["base_row_uid"])
        hash_to_base[stable_hash(base, 16)] = base
        rows_by_key[
            (
                base,
                str(row["policy"]),
                str(row["task_context_id"]),
            )
        ] = row
    return hash_to_base, rows_by_key


def policy_task_proxy(policy_id: str, profile_id: str) -> str:
    if policy_id == "all_high_value_memory_trust_counterfactual_v0":
        return "high_value_fetch"
    if policy_id in {
        "no_staleness_memory_trust_v0",
        "no_reobserve_budget_v0",
        "no_path_search_cost_v0",
        "task_context_only_v0",
        "h001_task_conditioned_memory_trust_v0",
    }:
        return TASK_PROXY_BY_PROFILE.get(profile_id, "routine_fetch")
    return "routine_fetch"


def decision_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("decision_action"),
        int(row.get("selected_budget", 0)),
        bool(row.get("old_memory_trusted")),
        bool(row.get("reobserve_selected")),
    )


def context_pair_divergence(policy_rows: list[dict[str, Any]]) -> dict[tuple[str, str], bool]:
    grouped: dict[tuple[str, str], set[tuple[Any, ...]]] = defaultdict(set)
    for row in policy_rows:
        grouped[(str(row["policy_id"]), str(row["pair_id"]))].add(decision_signature(row))
    return {key: len(signatures) > 1 for key, signatures in grouped.items()}


def eval_outcome(
    *,
    policy_row: dict[str, Any],
    paired_row: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    hash_to_base: dict[str, str],
    eval_rows: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    policy_id = str(policy_row["policy_id"])
    selected_budget = int(policy_row.get("selected_budget", 0))
    profile = profiles[str(paired_row["utility_profile_id"])]

    if policy_id in ORACLE_POLICIES:
        return {
            "hit_within_budget": True,
            "missed_target": False,
            "false_trust": False,
            "old_location_dead_end": False,
            "old_location_dead_end_cost_m": 0.0,
            "path_cost_m": 0.0,
            "candidate_visit_count": 1,
            "outcome_eval_policy": policy_id,
            "outcome_task_proxy": str(paired_row["task_type"]),
            "outcome_status": "oracle_diagnostic",
            "success_source_eval_only": "oracle",
        }

    source_hash = str(paired_row["source_reference_hash"])
    base = hash_to_base.get(source_hash)
    eval_policy = EVAL_POLICY_BY_POLICY_ID.get(policy_id)
    task_proxy = policy_task_proxy(policy_id, str(paired_row["utility_profile_id"]))
    source_row = eval_rows.get((base, eval_policy, task_proxy)) if base and eval_policy else None

    if source_row is None:
        return {
            "hit_within_budget": False,
            "missed_target": True,
            "false_trust": bool(policy_row.get("old_memory_trusted")),
            "old_location_dead_end": bool(policy_row.get("old_memory_trusted")),
            "old_location_dead_end_cost_m": 0.0,
            "path_cost_m": 0.0,
            "candidate_visit_count": max(1, selected_budget),
            "outcome_eval_policy": eval_policy,
            "outcome_task_proxy": task_proxy,
            "outcome_status": "missing_eval_row",
            "success_source_eval_only": None,
        }

    route_index = source_row.get("stop_route_index")
    if route_index is None:
        route_index = source_row.get("expected_search_cost_eval_only", selected_budget)
    route_index = int(route_index or selected_budget or 1)
    eval_success = bool(source_row.get("query_bridge_success_eval_only"))
    hit = eval_success and route_index <= max(1, selected_budget)
    success_source = source_row.get("success_source_eval_only")
    false_trust = bool(policy_row.get("old_memory_trusted")) and success_source != "old_memory"
    old_dead_end = false_trust or bool(source_row.get("old_location_dead_end_visit_count", 0))
    if hit:
        candidate_visit_count = min(max(1, selected_budget), max(1, route_index))
    else:
        candidate_visit_count = max(1, selected_budget)

    return {
        "hit_within_budget": hit,
        "missed_target": not hit,
        "false_trust": false_trust,
        "old_location_dead_end": old_dead_end,
        "old_location_dead_end_cost_m": float(
            source_row.get("old_location_dead_end_cost_m_lower_bound") or 0.0
        ),
        "path_cost_m": float(source_row.get("path_expected_search_cost_m") or 0.0),
        "candidate_visit_count": candidate_visit_count,
        "outcome_eval_policy": eval_policy,
        "outcome_task_proxy": task_proxy,
        "outcome_status": "joined_eval_row",
        "success_source_eval_only": success_source,
    }


def compute_utility(
    *,
    policy_row: dict[str, Any],
    paired_row: dict[str, Any],
    profile: dict[str, Any],
    outcome: dict[str, Any],
    cost_source_group: str,
) -> dict[str, Any]:
    selected_budget = int(policy_row.get("selected_budget", 0))
    context_budget = int(paired_row.get("search_budget", selected_budget))
    budget_overrun = max(0, selected_budget - context_budget)
    reobserve_count = 1 if bool(policy_row.get("reobserve_selected")) else 0
    base_expected_cost = float(policy_row.get("expected_search_cost") or selected_budget or 1)
    path_cost_m = float(outcome["path_cost_m"])
    if cost_source_group == "candidate_plus_path":
        expected_search_cost = base_expected_cost + path_cost_m / PATH_UNIT_M
    else:
        expected_search_cost = base_expected_cost

    hit = bool(outcome["hit_within_budget"])
    missed = bool(outcome["missed_target"])
    false_trust = bool(outcome["false_trust"])
    old_dead_end = bool(outcome["old_location_dead_end"])

    context_utility = (
        float(profile["target_value"]) * int(hit)
        - float(profile["miss_penalty"]) * int(missed)
        - float(profile["false_trust_penalty"]) * int(false_trust)
        - float(profile["old_location_dead_end_penalty"]) * int(old_dead_end)
        - float(profile["reobserve_cost"]) * reobserve_count
        - float(profile["latency_weight"]) * expected_search_cost
        - BUDGET_OVERRUN_PENALTY * budget_overrun
    )
    oracle_expected_cost = 1.0
    oracle_utility = float(profile["target_value"]) - float(profile["latency_weight"]) * oracle_expected_cost

    return {
        "BudgetOverrun": budget_overrun,
        "CandidateVisitCount": outcome["candidate_visit_count"],
        "ContextUtility": round(context_utility, 6),
        "ExpectedSearchCost": round(expected_search_cost, 6),
        "FalseTrustPenalty": float(profile["false_trust_penalty"]) * int(false_trust),
        "HitWithinBudget": hit,
        "IntentRegret": round(oracle_utility - context_utility, 6),
        "MissedHighValuePenalty": float(profile["miss_penalty"]) * int(missed),
        "OldLocationDeadEndCostM": round(float(outcome["old_location_dead_end_cost_m"]), 6),
        "OracleContextUtility": round(oracle_utility, 6),
        "ReobserveCount": reobserve_count,
        "UnnecessaryReobserveCost": float(profile["reobserve_cost"]) * reobserve_count
        if hit and outcome.get("success_source_eval_only") == "old_memory"
        else 0.0,
        "false_trust": false_trust,
        "missed_target": missed,
        "old_location_dead_end": old_dead_end,
    }


def aggregate(rows: list[dict[str, Any]], group_fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(field) for field in group_fields)].append(row)
    out: list[dict[str, Any]] = []
    for key, group_rows in sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
        payload = {field: value for field, value in zip(group_fields, key)}
        gains = [float(row["ContextSpecificGain"]) for row in group_rows]
        payload.update(
            {
                "row_count": len(group_rows),
                "mean_ContextUtility": round(mean(float(row["ContextUtility"]) for row in group_rows), 6),
                "mean_IntentRegret": round(mean(float(row["IntentRegret"]) for row in group_rows), 6),
                "mean_ContextSpecificGain": round(mean(gains), 6),
                "positive_gain_rows": sum(1 for value in gains if value > 0),
                "proxy_SR": round(
                    mean(1.0 if row["HitWithinBudget"] else 0.0 for row in group_rows), 6
                ),
                "decision_divergence_rows": sum(
                    1 for row in group_rows if row["ContextPairDecisionDivergence"]
                ),
            }
        )
        out.append(payload)
    return out


def materialize(out_root: Path) -> dict[str, Any]:
    out_root.mkdir(parents=True, exist_ok=True)
    policy_path = M06_ROOT / "baseline_policy_rows.jsonl"
    policy_hash_before = file_sha256(policy_path)

    profiles = load_profiles()
    paired_rows = read_jsonl(M05_ROOT / "paired_context_queries.jsonl")
    policy_rows = read_jsonl(policy_path)
    paired_by_query_context = {
        (row["query_id"], row["context_id"]): row for row in paired_rows
    }
    hash_to_base, eval_rows = index_eval_rows()
    divergence_by_policy_pair = context_pair_divergence(policy_rows)

    metric_rows: list[dict[str, Any]] = []
    missing_eval_rows = 0
    for policy_row in policy_rows:
        paired = paired_by_query_context[
            (policy_row["query_id"], policy_row["context_id"])
        ]
        profile = profiles[paired["utility_profile_id"]]
        outcome = eval_outcome(
            policy_row=policy_row,
            paired_row=paired,
            profiles=profiles,
            hash_to_base=hash_to_base,
            eval_rows=eval_rows,
        )
        missing_eval_rows += int(outcome["outcome_status"] == "missing_eval_row")
        for cost_source_group in paired.get("cost_source_groups", ["candidate_rank_only"]):
            utility = compute_utility(
                policy_row=policy_row,
                paired_row=paired,
                profile=profile,
                outcome=outcome,
                cost_source_group=cost_source_group,
            )
            row = {
                "ContextPairDecisionDivergence": divergence_by_policy_pair[
                    (policy_row["policy_id"], policy_row["pair_id"])
                ],
                "ContextSpecificGain": None,
                "best_context_agnostic_policy_id": None,
                "best_context_agnostic_utility": None,
                "blocked_input_audit_status": paired.get("blocked_field_audit"),
                "context_id": policy_row["context_id"],
                "cost_source_group": cost_source_group,
                "e006_metric_row_version": VERSION,
                "evidence_group_id": paired["evidence_group_id"],
                "label_group": paired["label_group"],
                "outcome_eval_policy": outcome["outcome_eval_policy"],
                "outcome_status": outcome["outcome_status"],
                "outcome_task_proxy": outcome["outcome_task_proxy"],
                "pair_id": policy_row["pair_id"],
                "policy_family": policy_row["policy_family"],
                "policy_id": policy_row["policy_id"],
                "policy_output_frozen_audit": "pass",
                "profile_pair_id": paired["profile_pair_id"],
                "query_id": policy_row["query_id"],
                "scan_group_id": paired["scan_group_id"],
                "source_ready_group": paired["source_ready_group"],
                "task_group": paired["task_group"],
                "task_type": paired["task_type"],
                "uses_task_context": policy_row["uses_task_context"],
                "utility_profile_id": paired["utility_profile_id"],
            }
            row.update(utility)
            metric_rows.append(row)

    baseline_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        if not row["uses_task_context"] and row["policy_id"] not in ORACLE_POLICIES:
            baseline_groups[
                (row["query_id"], row["context_id"], row["cost_source_group"])
            ].append(row)

    for row in metric_rows:
        candidates = baseline_groups[
            (row["query_id"], row["context_id"], row["cost_source_group"])
        ]
        best = max(candidates, key=lambda item: float(item["ContextUtility"]))
        row["best_context_agnostic_policy_id"] = best["policy_id"]
        row["best_context_agnostic_utility"] = best["ContextUtility"]
        row["ContextSpecificGain"] = round(
            float(row["ContextUtility"]) - float(best["ContextUtility"]), 6
        )

    primary_rows = [
        row
        for row in metric_rows
        if row["policy_id"] == PRIMARY_POLICY
        and row["cost_source_group"] == "candidate_plus_path"
    ]
    candidate_rank_primary_rows = [
        row
        for row in metric_rows
        if row["policy_id"] == PRIMARY_POLICY
        and row["cost_source_group"] == "candidate_rank_only"
    ]
    failure_rows = []
    for row in primary_rows:
        if float(row["ContextSpecificGain"]) >= 0:
            continue
        if row["BudgetOverrun"]:
            failure_type = "budget_overrun"
            suspected_cause = "context budget is smaller than the selected task-conditioned candidate budget"
        elif row["missed_target"]:
            failure_type = "missed_target_relative_to_context_agnostic_baseline"
            suspected_cause = "task-conditioned policy did not recover the target within the selected budget"
        elif float(row["ExpectedSearchCost"]) > float(row["best_context_agnostic_utility"]):
            failure_type = "cost_dominated_by_context_agnostic_baseline"
            suspected_cause = "utility gain is erased by search/path cost"
        else:
            failure_type = "utility_lower_than_context_agnostic_baseline"
            suspected_cause = "best context-agnostic baseline is stronger under the frozen utility formula"
        failure_rows.append(
            {
                "ContextSpecificGain": row["ContextSpecificGain"],
                "ContextUtility": row["ContextUtility"],
                "best_context_agnostic_policy_id": row["best_context_agnostic_policy_id"],
                "context_id": row["context_id"],
                "dominant_axis": row["source_ready_group"]
                if row["source_ready_group"] != "source_ready"
                else row["task_group"],
                "failure_type": failure_type,
                "label_group": row["label_group"],
                "next_validation": "inspect whether task-conditioned budget/re-observation decision is necessary beyond the strongest frozen baseline",
                "pair_id": row["pair_id"],
                "query_id": row["query_id"],
                "source_ready_group": row["source_ready_group"],
                "suspected_cause": suspected_cause,
                "task_group": row["task_group"],
            }
        )

    group_rows = []
    for fields in (
        ["policy_id", "cost_source_group"],
        ["policy_id", "cost_source_group", "task_group"],
        ["policy_id", "cost_source_group", "label_group"],
        ["policy_id", "cost_source_group", "scan_group_id"],
        ["policy_id", "cost_source_group", "source_ready_group"],
    ):
        for row in aggregate(
            [item for item in metric_rows if item["policy_id"] == PRIMARY_POLICY],
            fields,
        ):
            row["group_fields"] = fields
            group_rows.append(row)

    positive_task_groups = {
        row["task_group"]
        for row in aggregate(primary_rows, ["task_group"])
        if row["mean_ContextSpecificGain"] > 0
    }
    positive_label_groups = {
        row["label_group"]
        for row in aggregate(primary_rows, ["label_group"])
        if row["mean_ContextSpecificGain"] > 0
    }
    positive_scan_groups = {
        row["scan_group_id"]
        for row in aggregate(primary_rows, ["scan_group_id"])
        if row["mean_ContextSpecificGain"] > 0
    }
    primary_gain_mean = mean(float(row["ContextSpecificGain"]) for row in primary_rows)
    rank_gain_mean = mean(float(row["ContextSpecificGain"]) for row in candidate_rank_primary_rows)
    primary_sr = mean(1.0 if row["HitWithinBudget"] else 0.0 for row in primary_rows)
    transfer_gate_pass = (
        primary_gain_mean > 0
        and len(positive_task_groups) >= 2
        and len(positive_label_groups) >= 2
        and len(positive_scan_groups) >= 2
    )
    if transfer_gate_pass:
        claim_gate_status = "pass"
    elif primary_gain_mean > 0:
        claim_gate_status = "warning_positive_but_transfer_incomplete"
    else:
        claim_gate_status = "fail_strong_context_agnostic_baseline_not_beaten"

    policy_hash_after = file_sha256(policy_path)
    mutation_status = "pass" if policy_hash_before == policy_hash_after else "fail"
    serialized_metric_rows = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) for row in metric_rows
    )
    blocked_hits = [term for term in BLOCKED_TERMS if term in serialized_metric_rows]
    blocked_status = "pass" if not blocked_hits else "fail"
    summary_ready = mutation_status == "pass" and blocked_status == "pass"

    summary = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ready" if summary_ready else "failed",
        "claim_gate_status": claim_gate_status,
        "paired_context_rows": len(paired_rows),
        "baseline_policy_rows": len(policy_rows),
        "utility_metric_rows": len(metric_rows),
        "group_transfer_metric_rows": len(group_rows),
        "failure_rows": len(failure_rows),
        "missing_eval_rows": missing_eval_rows,
        "cost_source_groups": sorted({row["cost_source_group"] for row in metric_rows}),
        "primary_policy": PRIMARY_POLICY,
        "primary_candidate_plus_path_mean_ContextSpecificGain": round(primary_gain_mean, 6),
        "primary_candidate_rank_only_mean_ContextSpecificGain": round(rank_gain_mean, 6),
        "primary_candidate_plus_path_proxy_SR": round(primary_sr, 6),
        "primary_candidate_plus_path_positive_gain_rows": sum(
            1 for row in primary_rows if float(row["ContextSpecificGain"]) > 0
        ),
        "primary_candidate_plus_path_rows": len(primary_rows),
        "positive_task_group_count": len(positive_task_groups),
        "positive_label_group_count": len(positive_label_groups),
        "positive_scan_group_count": len(positive_scan_groups),
        "policy_row_mutation_audit": mutation_status,
        "policy_rows_sha256_before": policy_hash_before,
        "policy_rows_sha256_after": policy_hash_after,
        "blocked_metric_output_term_hits": blocked_hits,
        "blocked_metric_output_audit": blocked_status,
        "best_context_agnostic_policy_counts": dict(
            Counter(row["best_context_agnostic_policy_id"] for row in primary_rows)
        ),
        "human_intent_main_claim_ready": transfer_gate_pass,
        "utility_improvement_ready": primary_gain_mean > 0,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E006-M08 utility result interpretation and human-intent claim decision"
        if summary_ready
        else "repair E006-M07 utility metric materialization",
    }

    report = "\n".join(
        [
            "# E006-M07 Utility Metric Materialization Smoke",
            "",
            "## Facts",
            "",
            f"- Status: `{summary['status']}`.",
            f"- Claim gate: `{summary['claim_gate_status']}`.",
            f"- Utility metric rows: {summary['utility_metric_rows']}.",
            f"- Failure rows: {summary['failure_rows']}.",
            f"- Missing eval rows: {summary['missing_eval_rows']}.",
            f"- Policy row mutation audit: `{summary['policy_row_mutation_audit']}`.",
            f"- Blocked metric output audit: `{summary['blocked_metric_output_audit']}`.",
            f"- Primary `candidate_plus_path` mean `ContextSpecificGain`: {summary['primary_candidate_plus_path_mean_ContextSpecificGain']}.",
            f"- Primary `candidate_plus_path` proxy `SR`: {summary['primary_candidate_plus_path_proxy_SR']}.",
            f"- Positive task/label/scan groups: {summary['positive_task_group_count']} / {summary['positive_label_group_count']} / {summary['positive_scan_group_count']}.",
            "",
            "## Claim Boundary",
            "",
            "- M07 computes utility metrics after frozen M06 policy rows; it does not mutate policy output rows.",
            "- M07 is still a smoke materialization over the E007 path-cost denominator, not a final human-intent main-claim result.",
            "- A human-intent main claim remains blocked unless `ContextSpecificGain` and `IntentRegret` beat the strongest context-agnostic baseline across task, label, and scan groups.",
            "- Real navigation `SR` / `SPL` and final real RGB-D/open-vocabulary robustness are not supported by M07.",
            "",
        ]
    )

    write_jsonl(out_root / "utility_metric_rows.jsonl", metric_rows)
    write_jsonl(out_root / "group_transfer_metrics.jsonl", group_rows)
    write_jsonl(out_root / "failure_rows.jsonl", failure_rows)
    write_json(out_root / "summary.json", summary)
    write_text(out_root / "report.md", report)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args()
    summary = materialize(args.out_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
