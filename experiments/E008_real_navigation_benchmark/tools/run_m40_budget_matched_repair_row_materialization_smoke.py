#!/usr/bin/env python3
"""Materialize E008-M40 budget-matched repair rows for the next trajectory smoke."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m40_budget_matched_repair_row_materialization_smoke_v0"

M36_DIR = EXP_ROOT / "artifacts" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
M39_DIR = EXP_ROOT / "artifacts" / "E008-M39_budget_matched_policy_repair_source_gap_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M40_budget_matched_repair_row_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M40_budget_matched_repair_row_materialization_smoke_v0"

NEXT_UNIT = "E008-M41 budget-matched repair trajectory execution smoke"
SELECTED_ROUTE = "hm3d_counterfactual_stale_overlay_budget_matched_repair_v0"
PRIMARY_BUDGET = 5

STATIC_POLICY = "static_stale_memory_top1_v0"
FIXED_POLICY = "fixed_topk_current_observation_budget5_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
TASK_AGNOSTIC_POLICY = "task_agnostic_dead_end_penalized_budget5_v0"
H001_POLICY = "h001_dead_end_penalized_budget5_v0"

SOURCE_STATIC_POLICY = "static_stale_memory_top1_v0"
SOURCE_FIXED_POLICY = "fixed_topk_current_observation_v0"
SOURCE_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"

MATERIALIZED_POLICIES = [
    STATIC_POLICY,
    FIXED_POLICY,
    DETECTOR_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]

POLICY_ROLES = {
    STATIC_POLICY: "naive_lower_bound",
    FIXED_POLICY: "budget_matched_current_only_baseline",
    DETECTOR_POLICY: "budget_matched_detector_baseline",
    TASK_AGNOSTIC_POLICY: "ablation_no_task_context",
    H001_POLICY: "test_method_task_conditioned_memory_trust",
}

BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "trajectory_success",
    "m32_trajectory_success",
    "success_proposal_uid",
    "success_source_role",
    "success_dynamic_stale_overlay_role",
    "FailureType",
    "SR",
    "SPL",
    "StopRank",
    "PathLengthM",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def policy_plan_uid(plan: dict[str, Any]) -> str:
    return str(plan.get("m40_plan_uid"))


def source_plan_uid(plan: dict[str, Any], policy_id: str) -> str:
    source_h001 = str(plan.get("source_m36_policy_plan_uid"))
    prefix = source_h001.rsplit("::", 1)[0]
    if policy_id == STATIC_POLICY:
        return f"{prefix}::{SOURCE_STATIC_POLICY}"
    if policy_id == FIXED_POLICY:
        return f"{prefix}::{SOURCE_FIXED_POLICY}"
    return f"{prefix}::{SOURCE_DETECTOR_POLICY}"


def group_by_plan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def detector_sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
    path_ready = bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))
    score = finite_float(row.get("ranking_score")) or finite_float(row.get("confidence")) or -1.0
    cost = finite_float(row.get("source_to_candidate_path_cost_m"))
    return (0 if path_ready else 1, -score, cost if cost is not None else float("inf"), str(row.get("proposal_uid")))


def strip_blocked_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in BLOCKED_POLICY_FIELDS}


def clone_candidate(
    source: dict[str, Any],
    plan: dict[str, Any],
    visit_rank: int,
    component: str,
    source_policy_plan_uid: str,
) -> dict[str, Any]:
    policy_id = str(plan.get("policy_id"))
    plan_uid = policy_plan_uid(plan)
    row = strip_blocked_fields(source)
    row.update(
        {
            "version": VERSION,
            "source_version": str(source.get("version")),
            "selected_route": SELECTED_ROUTE,
            "m40_plan_uid": plan_uid,
            "source_m36_policy_plan_uid": source_policy_plan_uid,
            "benchmark_row_uid": source.get("benchmark_row_uid"),
            "overlay_policy_plan_uid": plan_uid,
            "policy_plan_uid": plan_uid,
            "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
            "candidate_visit_uid": f"{plan_uid}::{visit_rank:03d}",
            "policy_id": policy_id,
            "policy_role": POLICY_ROLES[policy_id],
            "adapter_episode_id": plan.get("adapter_episode_id"),
            "scan_id": plan.get("scan_id"),
            "scene_key": plan.get("scene_key"),
            "object_category": plan.get("object_category"),
            "task_context_id": plan.get("task_context_id"),
            "visit_rank": visit_rank,
            "candidate_order_component": component,
            "diagnostic_source_gap_boundary": bool(plan.get("diagnostic_source_gap_boundary")),
            "source_gap_handling": plan.get("source_gap_handling"),
            "primary_budget_cap": int(plan.get("primary_budget_cap") or PRIMARY_BUDGET),
            "policy_input_allowed": True,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "diagnostic_not_policy_input": True,
            "claim_boundary": "M40 materializes budget-matched repair trajectory input rows; no trajectory result is produced.",
        }
    )
    if "source_role" not in row:
        row["source_role"] = row.get("candidate_source_role")
    return row


def stale_candidate(plan: dict[str, Any], rows_by_plan: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    rows = rows_by_plan.get(source_plan_uid(plan, STATIC_POLICY), [])
    return rows[0] if rows else None


def current_candidates(plan: dict[str, Any], rows_by_plan: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = rows_by_plan.get(source_plan_uid(plan, DETECTOR_POLICY), [])
    return sorted(
        [
            row
            for row in rows
            if row.get("candidate_source_role") == "current_observation"
            and bool(row.get("candidate_usable_for_path_smoke", True))
        ],
        key=detector_sort_key,
    )


def stale_trusted_task_agnostic(stale: dict[str, Any] | None, current_top: list[dict[str, Any]]) -> bool:
    if stale is None:
        return False
    stale_cost = finite_float(stale.get("source_to_candidate_path_cost_m"))
    best_conf = max([finite_float(row.get("confidence")) or 0.0 for row in current_top], default=0.0)
    return stale_cost is not None and stale_cost <= 1.5 and best_conf < 0.7


def stale_trusted_h001(plan: dict[str, Any], stale: dict[str, Any] | None, current_top: list[dict[str, Any]]) -> bool:
    if stale is None:
        return False
    stale_cost = finite_float(stale.get("source_to_candidate_path_cost_m"))
    best_conf = max([finite_float(row.get("confidence")) or 0.0 for row in current_top], default=0.0)
    if stale_cost is None:
        return False
    task_context = str(plan.get("task_context_id"))
    thresholds = {
        "high_value_fetch": {"cost": 1.0, "confidence": 0.5},
        "noisy_high_value_fetch": {"cost": 0.75, "confidence": 0.4},
        "routine_fetch": {"cost": 1.5, "confidence": 0.75},
    }
    threshold = thresholds.get(task_context, {"cost": 1.0, "confidence": 0.5})
    return stale_cost <= threshold["cost"] and best_conf < threshold["confidence"]


def materialize_plan_candidates(
    plan: dict[str, Any],
    rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    policy_id = str(plan.get("policy_id"))
    plan_uid = policy_plan_uid(plan)
    stale = stale_candidate(plan, rows_by_plan)
    current_top = current_candidates(plan, rows_by_plan)[:PRIMARY_BUDGET]
    rows: list[dict[str, Any]] = []

    if policy_id == STATIC_POLICY:
        if stale is not None:
            rows.append(clone_candidate(stale, plan, 1, "static_stale_memory_top1", source_plan_uid(plan, STATIC_POLICY)))
        return rows

    if policy_id == FIXED_POLICY:
        source_uid = source_plan_uid(plan, FIXED_POLICY)
        source_rows = rows_by_plan.get(source_uid, [])[:PRIMARY_BUDGET]
        return [
            clone_candidate(row, plan, rank, "fixed_top5_current_observation_budget5", source_uid)
            for rank, row in enumerate(source_rows, start=1)
        ]

    if policy_id == DETECTOR_POLICY:
        source_uid = source_plan_uid(plan, DETECTOR_POLICY)
        return [
            clone_candidate(row, plan, rank, "detector_confidence_budget5", source_uid)
            for rank, row in enumerate(current_top, start=1)
        ]

    if policy_id == TASK_AGNOSTIC_POLICY:
        source_uid = source_plan_uid(plan, DETECTOR_POLICY)
        selected: list[tuple[dict[str, Any], str]] = []
        if stale_trusted_task_agnostic(stale, current_top):
            selected.append((stale, "task_agnostic_stale_if_low_dead_end_and_weak_current"))  # type: ignore[arg-type]
            selected.extend((row, "task_agnostic_current_observation_budget_remainder") for row in current_top[:4])
        else:
            selected.extend((row, "task_agnostic_stale_suppressed_current_top5") for row in current_top)
        return [clone_candidate(row, plan, rank, component, source_uid) for rank, (row, component) in enumerate(selected, start=1)]

    if policy_id == H001_POLICY:
        source_uid = source_plan_uid(plan, DETECTOR_POLICY)
        selected = []
        if stale_trusted_h001(plan, stale, current_top):
            selected.append((stale, "h001_task_conditioned_stale_trusted"))  # type: ignore[arg-type]
            selected.extend((row, "h001_task_conditioned_current_budget_remainder") for row in current_top[:4])
        else:
            selected.extend((row, "h001_task_conditioned_stale_suppressed_current_top5") for row in current_top)
        return [clone_candidate(row, plan, rank, component, source_uid) for rank, (row, component) in enumerate(selected, start=1)]

    raise ValueError(f"unsupported M40 policy: {policy_id}")


def old_location_dead_end_proxy(rows: list[dict[str, Any]]) -> float:
    total = 0.0
    seen = False
    for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9)):
        if row.get("candidate_source_role") == "current_observation":
            break
        if row.get("candidate_source_role") == "stale_old_memory":
            seen = True
            value = finite_float(row.get("source_to_candidate_path_cost_m"))
            if value is not None:
                total += value
    return total if seen else 0.0


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = group_by_plan(candidate_rows)
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        stale_rows = [row for row in rows if row.get("candidate_source_role") == "stale_old_memory"]
        current_rows = [row for row in rows if row.get("candidate_source_role") == "current_observation"]
        first_current_rank = min([int(row.get("visit_rank") or 10**9) for row in current_rows], default=None)
        stale_before_current = [
            row
            for row in stale_rows
            if first_current_rank is None or int(row.get("visit_rank") or 10**9) < first_current_rank
        ]
        out.append(
            {
                "version": VERSION,
                "selected_route": SELECTED_ROUTE,
                "m40_plan_uid": plan_uid,
                "source_m36_policy_plan_uid": first.get("source_m36_policy_plan_uid"),
                "overlay_policy_plan_uid": plan_uid,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": first.get("policy_id"),
                "policy_role": first.get("policy_role"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "primary_budget_cap": int(first.get("primary_budget_cap") or PRIMARY_BUDGET),
                "candidate_budget": int(first.get("primary_budget_cap") or PRIMARY_BUDGET),
                "candidate_visit_order_contract": "budget_matched_repair_v0",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": sum(1 for row in rows if row.get("path_ready")),
                "stale_old_memory_candidate_rows": len(stale_rows),
                "current_observation_candidate_rows": len(current_rows),
                "first_candidate_source_role": first.get("candidate_source_role"),
                "stale_visit_first": first.get("candidate_source_role") == "stale_old_memory",
                "current_observation_first": first.get("candidate_source_role") == "current_observation",
                "stale_before_current_rows": len(stale_before_current),
                "old_location_dead_end_cost_proxy_m": old_location_dead_end_proxy(rows),
                "stale_visit_rate_proxy": len(stale_rows) / len(rows) if rows else 0.0,
                "reobservation_rate_proxy": len(current_rows) / len(rows) if rows else 0.0,
                "source_role_counts": dict(sorted(Counter(str(row.get("candidate_source_role")) for row in rows).items())),
                "diagnostic_source_gap_boundary": bool(first.get("diagnostic_source_gap_boundary")),
                "source_gap_handling": first.get("source_gap_handling"),
                "diagnostic_not_policy_input": True,
                "runner_input_ready": all(valid_vec3(row.get("execution_stop_position_m")) for row in rows),
                "execute_in_next_runner": True,
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py",
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_semantics": "start at episode start and visit execution_stop_position_m in visit_rank order",
                "start_state_source": "ObjectNav episode start state from E008-M03/E008-M22 runner input",
                "termination_rule": "terminate on first eval-only success after a stop or after candidate budget is exhausted",
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_m35_proxy_success_for_filtering": False,
                "claim_boundary": "M40 materializes repaired budget-matched execution plans; no trajectory metric has been computed yet.",
            }
        )
    return out


def build_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id in MATERIALIZED_POLICIES:
        rows = by_policy.get(policy_id, [])
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_plan_rows": len(rows),
                "source_ready_plan_rows": sum(1 for row in rows if not row.get("diagnostic_source_gap_boundary")),
                "source_gap_plan_rows": sum(1 for row in rows if row.get("diagnostic_source_gap_boundary")),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in rows]),
                "stale_first_plan_rows": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first_plan_rows": sum(1 for row in rows if row.get("current_observation_first")),
                "mean_old_location_dead_end_cost_proxy_m": mean(
                    [finite_float(row.get("old_location_dead_end_cost_proxy_m")) for row in rows]
                ),
                "runner_input_ready_rows": sum(1 for row in rows if row.get("runner_input_ready")),
                "claim_boundary": "M40 summary is pre-execution materialization only.",
            }
        )
    return out


def build_source_gap_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        grouped[str(row.get("source_gap_handling"))].append(row)
    return [
        {
            "version": VERSION,
            "source_gap_handling": key,
            "policy_plan_rows": len(rows),
            "unique_scan_task_rows": len({(row.get("adapter_episode_id"), row.get("task_context_id")) for row in rows}),
            "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
            "claim_boundary": "Source-gap rows remain separated from source-ready primary policy comparison.",
        }
        for key, rows in sorted(grouped.items())
    ]


def build_policy_design_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": STATIC_POLICY,
            "design": "visit stale old-memory location only",
            "task_context_used": False,
            "primary_budget_cap": 1,
        },
        {
            "version": VERSION,
            "policy_id": FIXED_POLICY,
            "design": "visit the first five current-observation candidates from the existing fixed top-k source",
            "task_context_used": False,
            "primary_budget_cap": PRIMARY_BUDGET,
        },
        {
            "version": VERSION,
            "policy_id": DETECTOR_POLICY,
            "design": "visit top-five detector-confidence current-observation candidates",
            "task_context_used": False,
            "primary_budget_cap": PRIMARY_BUDGET,
        },
        {
            "version": VERSION,
            "policy_id": TASK_AGNOSTIC_POLICY,
            "design": "trust stale only when old-location cost <=1.5m and current confidence <0.7; otherwise current top-five",
            "task_context_used": False,
            "primary_budget_cap": PRIMARY_BUDGET,
        },
        {
            "version": VERSION,
            "policy_id": H001_POLICY,
            "design": "condition stale trust on task context, old-location dead-end cost, and current proposal confidence",
            "task_context_used": True,
            "primary_budget_cap": PRIMARY_BUDGET,
        },
    ]


def build_leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload_name, payload_rows in [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        over_budget_hits = 0
        for row in payload_rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
            if payload_name.endswith("candidate_rows") and row.get("policy_id") != STATIC_POLICY:
                if int(row.get("visit_rank") or 0) > PRIMARY_BUDGET:
                    over_budget_hits += 1
        rows.append(
            {
                "version": VERSION,
                "payload": payload_name,
                "row_count": len(payload_rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "over_budget_candidate_hits": over_budget_hits,
                "leakage_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
                "budget_cap_compliance_pass": over_budget_hits == 0,
            }
        )
    return rows


def build_readiness_gate_rows(plan_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]], leakage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_plan_rows = 18 * len(MATERIALIZED_POLICIES)
    return [
        {
            "version": VERSION,
            "gate_id": "m40_plan_rows_preserved",
            "status": "pass" if len(plan_rows) == expected_plan_rows else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected={expected_plan_rows}.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_rows_materialized",
            "status": "pass" if candidate_rows else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_input_ready",
            "status": "pass" if all(row.get("runner_input_ready") for row in plan_rows) else "fail",
            "evidence": f"runner-ready plan rows={sum(1 for row in plan_rows if row.get('runner_input_ready'))}/{len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked field hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "budget_cap_compliance",
            "status": "pass" if all(row.get("budget_cap_compliance_pass") for row in leakage_rows) else "fail",
            "evidence": f"over-budget hits={sum(int(row.get('over_budget_candidate_hits') or 0) for row in leakage_rows)}.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_matched_repair_rows_materialized",
            "status": "supported_materialization_only",
            "claim_boundary": "M40 supports only leakage-safe row materialization for repaired budget-matched policies.",
        },
        {
            "version": VERSION,
            "claim_id": "budget_matched_repair_trajectory_result",
            "status": "not_ready",
            "claim_boundary": "No trajectory metric is produced until M41 executes these rows in Docker Habitat.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "claim_boundary": "M40 does not execute trajectories and does not support final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "claim_boundary": "Structured task context is a memory-trust condition in M40, not a natural-language human-intent claim.",
        },
    ]


def build_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "execute_budget_matched_repair_trajectory_smoke",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
            "requires_docker": True,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_m41_command_rows() -> list[dict[str, Any]]:
    command = (
        'docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp '
        '-v /home/yoohyun/research2/local_dataset/data:/data:ro '
        '-v /home/yoohyun/research2:/work -w /work '
        'research2/habitat-h001:20260508-calib-artifacts '
        'bash -lc "micromamba run -n base python '
        'experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py '
        '--m36-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M40_budget_matched_repair_row_materialization_smoke_v0 '
        '--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0 '
        '--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0"'
    )
    return [
        {
            "version": VERSION,
            "command_id": "m41_docker_runner_command",
            "working_directory": str(ROOT),
            "command": command,
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/coverage.json",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M41_budget_matched_repair_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl",
            ],
            "verification_command": "python - <<'PY' ... assert coverage status and scan_task_policy_rows ... PY",
            "launch_now": False,
        }
    ]


def build_report(coverage: dict[str, Any], summary_rows: list[dict[str, Any]], source_gap_rows: list[dict[str, Any]]) -> str:
    def fmt(value: object) -> str:
        if isinstance(value, float):
            return f"{value:.6f}"
        if value is None:
            return "null"
        return str(value)

    def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        for row in rows:
            lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
        return "\n".join(lines)

    return "\n".join(
        [
            "# E008-M40 Budget-Matched Repair Row Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M40 plan rows: {coverage['m40_plan_rows']}.",
            f"- Trajectory candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Source-ready plan rows: {coverage['source_ready_plan_rows']}.",
            f"- Source-gap plan rows: {coverage['source_gap_plan_rows']}.",
            f"- Policy input leakage pass: {coverage['policy_input_leakage_pass']}.",
            f"- Budget cap compliance pass: {coverage['budget_cap_compliance_pass']}.",
            f"- Trajectory execution launched: {coverage['trajectory_execution_launched']}.",
            "",
            "## Policy Summary",
            "",
            table(
                summary_rows,
                [
                    "policy_id",
                    "policy_plan_rows",
                    "candidate_rows",
                    "source_ready_plan_rows",
                    "source_gap_plan_rows",
                    "stale_first_plan_rows",
                    "current_first_plan_rows",
                    "mean_old_location_dead_end_cost_proxy_m",
                ],
            ),
            "",
            "## Source-Gap Handling",
            "",
            table(source_gap_rows, ["source_gap_handling", "policy_plan_rows", "unique_scan_task_rows", "candidate_rows"]),
            "",
            "## Claim Boundary",
            "",
            "- M40 is materialization only; it does not produce trajectory `SR` / `SPL`.",
            "- Source-gap rows remain a separate boundary and should not be used as a pure policy-failure claim.",
            "- Structured task context is used only to condition memory trust and re-observation ordering.",
            "",
            "## Next",
            "",
            f"- {NEXT_UNIT}.",
            "",
        ]
    )


def copy_core_outputs(out_root: Path, derived_out_root: Path, filenames: list[str]) -> None:
    derived_out_root.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        src = out_root / name
        if src.exists():
            shutil.copy2(src, derived_out_root / name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m36_cov = read_json(M36_DIR / "coverage.json")
    m39_cov = read_json(M39_DIR / "coverage.json")
    m40_plan_rows = read_jsonl(M39_DIR / "m40_materialization_plan_rows.jsonl")
    m36_candidate_rows = read_jsonl(M36_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    input_contract_rows = read_jsonl(M36_DIR / "input_contract_rows.jsonl")

    if not m36_cov or not m39_cov or not m40_plan_rows or not m36_candidate_rows:
        raise SystemExit("missing required M36/M39 input artifacts")

    rows_by_plan = group_by_plan(m36_candidate_rows)
    candidate_rows: list[dict[str, Any]] = []
    for plan in m40_plan_rows:
        candidate_rows.extend(materialize_plan_candidates(plan, rows_by_plan))
    plan_rows = build_plan_rows(candidate_rows)
    summary_rows = build_summary_rows(plan_rows)
    source_gap_rows = build_source_gap_summary_rows(plan_rows)
    policy_design_rows = build_policy_design_rows()
    leakage_rows = build_leakage_rows(candidate_rows, plan_rows)
    readiness_rows = build_readiness_gate_rows(plan_rows, candidate_rows, leakage_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_rows()
    command_rows = build_m41_command_rows()

    policy_ids = sorted({str(row.get("policy_id")) for row in plan_rows})
    leakage_pass = all(row.get("leakage_pass") for row in leakage_rows)
    budget_pass = all(row.get("budget_cap_compliance_pass") for row in leakage_rows)
    runner_ready = all(row.get("runner_input_ready") for row in plan_rows)
    ready = (
        len(m40_plan_rows) == 90
        and len(plan_rows) == 90
        and len(policy_ids) == len(MATERIALIZED_POLICIES)
        and bool(candidate_rows)
        and leakage_pass
        and budget_pass
        and runner_ready
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m40_budget_matched_repair_row_materialization_smoke_ready"
        if ready
        else "e008_m40_budget_matched_repair_row_materialization_smoke_blocked",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m36_status": m36_cov.get("status"),
        "m39_status": m39_cov.get("status"),
        "m40_plan_rows": len(m40_plan_rows),
        "materialized_policy_plan_rows": len(plan_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "trajectory_candidate_rows": len(candidate_rows),
        "policy_count": len(policy_ids),
        "policy_ids": policy_ids,
        "intervention_rows": len({(row.get("adapter_episode_id"), row.get("task_context_id")) for row in plan_rows}),
        "source_ready_plan_rows": sum(1 for row in plan_rows if not row.get("diagnostic_source_gap_boundary")),
        "source_gap_plan_rows": sum(1 for row in plan_rows if row.get("diagnostic_source_gap_boundary")),
        "source_ready_scan_task_rows": len(
            {
                (row.get("adapter_episode_id"), row.get("task_context_id"))
                for row in plan_rows
                if not row.get("diagnostic_source_gap_boundary")
            }
        ),
        "source_gap_scan_task_rows": len(
            {
                (row.get("adapter_episode_id"), row.get("task_context_id"))
                for row in plan_rows
                if row.get("diagnostic_source_gap_boundary")
            }
        ),
        "policy_design_rows": len(policy_design_rows),
        "repair_policy_materialization_summary_rows": len(summary_rows),
        "source_gap_materialization_summary_rows": len(source_gap_rows),
        "leakage_audit_rows": len(leakage_rows),
        "readiness_gate_rows": len(readiness_rows),
        "policy_input_leakage_pass": leakage_pass,
        "budget_cap_compliance_pass": budget_pass,
        "runner_input_ready": runner_ready,
        "m41_runner_input_ready": ready,
        "trajectory_execution_launched": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    patched_input_contract_rows = [
        {**row, "version": VERSION, "source_version": row.get("version")}
        for row in input_contract_rows
    ]

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "repair_policy_materialization_summary_rows.jsonl", summary_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_materialization_summary_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "policy_design_rows.jsonl", policy_design_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", patched_input_contract_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m41_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, summary_rows, source_gap_rows), encoding="utf-8")

    copy_core_outputs(
        ARTIFACT_DIR,
        DATA_OUT_DIR,
        [
            "coverage.json",
            "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
            "trajectory_execution_plan_rows.jsonl",
            "input_contract_rows.jsonl",
            "m41_command_rows.jsonl",
        ],
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
