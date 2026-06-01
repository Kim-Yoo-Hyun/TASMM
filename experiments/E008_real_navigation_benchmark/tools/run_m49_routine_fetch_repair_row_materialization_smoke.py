#!/usr/bin/env python3
"""Materialize E008-M49 routine-fetch repair rows for the next trajectory gate."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M49_routine_fetch_repair_row_materialization_smoke_v0"
)
DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M49_routine_fetch_repair_row_materialization_smoke_v0"
)

M44_DIR = EXP_ROOT / "artifacts" / "E008-M44_source_diverse_redesign_row_materialization_smoke_v0"
M48_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0"
)

VERSION = "e008_m49_routine_fetch_repair_row_materialization_smoke_v0"
READY_STATUS = "e008_m49_routine_fetch_repair_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m49_routine_fetch_repair_row_materialization_smoke_blocked"
NEXT_UNIT = "E008-M50 routine-fetch repair trajectory execution contract and Docker preflight"

STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_CURRENT_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_DIVERSE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
H001_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
REPAIR_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"

BASELINE_POLICIES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]
M49_POLICIES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
    REPAIR_POLICY,
]

PRIMARY_BUDGET = 5
EXPECTED_SCAN_TASK_ROWS = 18
EXPECTED_PLAN_ROWS = 126
EXPECTED_CANDIDATE_ROWS = 558

SELECTED_ROUTE = "routine_fetch_safe_source_diverse_repair_v2"
REPORTING_ONLY_FIELDS = {"diagnostic_source_gap_boundary_for_reporting"}
BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "eval_success",
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
    "diagnostic_source_gap_boundary",
}

POLICY_ROLES = {
    STATIC_POLICY: "naive_lower_bound",
    DETECTOR_POLICY: "budget_matched_detector_baseline",
    FIXED_CURRENT_POLICY: "budget_matched_fixed_current_baseline",
    SOURCE_DIVERSE_CURRENT_POLICY: "source_diversity_current_observation_baseline",
    TASK_AGNOSTIC_POLICY: "task_context_ablation",
    H001_POLICY: "previous_h001_task_conditioned_source_diverse",
    REPAIR_POLICY: "repaired_h001_task_conditioned_safe_source_diverse",
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
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def candidate_identity(row: dict[str, Any]) -> str:
    for key in ("proposal_uid", "source_candidate_identity", "raw_candidate_uid", "candidate_visit_uid"):
        value = row.get(key)
        if value:
            return str(value)
    return json.dumps(row.get("execution_stop_position_m") or row.get("candidate_position_m"), sort_keys=True)


def group_by_plan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {key: sorted(value, key=lambda item: int(item.get("visit_rank") or 10**9)) for key, value in grouped.items()}


def group_by_scan_task_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row.get("adapter_episode_id")), str(row.get("task_context_id")), str(row.get("policy_id")))
        grouped[key].append(row)
    return {key: sorted(value, key=lambda item: int(item.get("visit_rank") or 10**9)) for key, value in grouped.items()}


def m49_plan_uid(adapter_episode_id: str, task_context_id: str, policy_id: str) -> str:
    return f"m49::{adapter_episode_id}::{task_context_id}::{policy_id}"


def proposal_order(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("proposal_uid")) for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9))]


def source_role_order(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("candidate_source_role")) for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9))]


def strip_blocked_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in BLOCKED_POLICY_FIELDS}


def clone_candidate(
    source: dict[str, Any],
    policy_id: str,
    visit_rank: int,
    component: str,
    source_m44_policy_plan_uid: str,
    source_kind: str,
) -> dict[str, Any]:
    plan_uid = m49_plan_uid(str(source.get("adapter_episode_id")), str(source.get("task_context_id")), policy_id)
    row = strip_blocked_fields(source)
    row.update(
        {
            "version": VERSION,
            "source_version": source.get("version"),
            "selected_route": SELECTED_ROUTE,
            "m49_plan_uid": plan_uid,
            "source_m44_policy_plan_uid": source_m44_policy_plan_uid,
            "source_m44_candidate_visit_uid": source.get("candidate_visit_uid"),
            "source_m44_policy_id": source.get("policy_id"),
            "source_m49_materialization_kind": source_kind,
            "source_candidate_identity": candidate_identity(source),
            "overlay_policy_plan_uid": plan_uid,
            "policy_plan_uid": plan_uid,
            "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
            "candidate_visit_uid": f"{plan_uid}::{visit_rank:03d}",
            "policy_id": policy_id,
            "policy_role": POLICY_ROLES[policy_id],
            "visit_rank": visit_rank,
            "candidate_order_component": component,
            "primary_budget_cap": 1 if policy_id == STATIC_POLICY else PRIMARY_BUDGET,
            "candidate_visit_order_contract": "routine_fetch_safe_source_diverse_v2"
            if policy_id == REPAIR_POLICY
            else "m44_order_preserved_v1",
            "use_diagnostic_source_gap_boundary_for_policy": False,
            "policy_input_allowed": True,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "uses_task_context_for_decision": True
            if policy_id == REPAIR_POLICY
            else bool(source.get("uses_task_context_for_decision")),
            "diagnostic_not_policy_input": True,
            "claim_boundary": "M49 materializes candidate rows only; no trajectory metric has been computed.",
        }
    )
    if "candidate_source_role" not in row:
        row["candidate_source_role"] = row.get("source_role")
    if "source_role" not in row:
        row["source_role"] = row.get("candidate_source_role")
    return row


def clone_baseline_rows(m44_candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cloned: list[dict[str, Any]] = []
    for source in sorted(m44_candidate_rows, key=lambda row: (str(row.get("policy_plan_uid")), int(row.get("visit_rank") or 10**9))):
        policy_id = str(source.get("policy_id"))
        if policy_id not in BASELINE_POLICIES:
            continue
        cloned.append(
            clone_candidate(
                source,
                policy_id,
                int(source.get("visit_rank") or 1),
                str(source.get("candidate_order_component")),
                str(source.get("policy_plan_uid")),
                "m44_baseline_order_reuse",
            )
        )
    return cloned


def materialize_repair_policy(m44_candidate_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = group_by_scan_task_policy(m44_candidate_rows)
    scan_task_keys = sorted({(key[0], key[1]) for key in by_key if key[2] == H001_POLICY})
    repair_rows: list[dict[str, Any]] = []
    repair_audit_rows: list[dict[str, Any]] = []

    for adapter_episode_id, task_context_id in scan_task_keys:
        h001_rows = by_key.get((adapter_episode_id, task_context_id, H001_POLICY), [])
        task_rows = by_key.get((adapter_episode_id, task_context_id, TASK_AGNOSTIC_POLICY), [])
        if task_context_id == "routine_fetch" and task_rows:
            source_rows = task_rows
            source_kind = "routine_fetch_task_agnostic_source_diverse_current_guard"
            component_prefix = "m49_repair_routine_fetch_source_diverse_current_guard"
        else:
            source_rows = h001_rows
            source_kind = "non_routine_h001_v1_passthrough"
            component_prefix = "m49_repair_non_routine_h001_v1_passthrough"
        source_plan_uid = str(source_rows[0].get("policy_plan_uid")) if source_rows else ""
        current_repair = [
            clone_candidate(
                source,
                REPAIR_POLICY,
                rank,
                f"{component_prefix}::{source.get('candidate_order_component')}",
                source_plan_uid,
                source_kind,
            )
            for rank, source in enumerate(source_rows[:PRIMARY_BUDGET], start=1)
        ]
        repair_rows.extend(current_repair)
        repair_audit_rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "task_context_id": task_context_id,
                "object_category": current_repair[0].get("object_category") if current_repair else None,
                "source_kind": source_kind,
                "repair_policy_id": REPAIR_POLICY,
                "source_policy_id": TASK_AGNOSTIC_POLICY if source_kind.startswith("routine_fetch") else H001_POLICY,
                "candidate_rows": len(current_repair),
                "same_order_as_h001_v1": proposal_order(current_repair) == proposal_order(h001_rows),
                "same_order_as_task_agnostic": proposal_order(current_repair) == proposal_order(task_rows),
                "stale_visit_first": bool(current_repair and current_repair[0].get("candidate_source_role") == "stale_old_memory"),
                "current_observation_candidate_rows": sum(1 for row in current_repair if row.get("candidate_source_role") == "current_observation"),
                "stale_old_memory_candidate_rows": sum(1 for row in current_repair if row.get("candidate_source_role") == "stale_old_memory"),
                "policy_uses_task_context_for_decision": True,
                "claim_boundary": "Repair audit is materialization-only and does not use trajectory success for policy ordering.",
            }
        )
    return repair_rows, repair_audit_rows


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


def build_execution_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = group_by_plan(candidate_rows)
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        first = rows[0]
        stale_rows = [row for row in rows if row.get("candidate_source_role") == "stale_old_memory"]
        current_rows = [row for row in rows if row.get("candidate_source_role") == "current_observation"]
        unique_frames = {str(row.get("frame_id")) for row in rows if row.get("frame_id")}
        unique_keys = {str(row.get("source_diversity_key")) for row in rows if row.get("source_diversity_key")}
        first_current_rank = min([int(row.get("visit_rank") or 10**9) for row in current_rows], default=None)
        stale_before_current = [
            row
            for row in stale_rows
            if first_current_rank is None or int(row.get("visit_rank") or 10**9) < first_current_rank
        ]
        cap = int(first.get("primary_budget_cap") or PRIMARY_BUDGET)
        out.append(
            {
                "version": VERSION,
                "selected_route": SELECTED_ROUTE,
                "m49_plan_uid": plan_uid,
                "source_m44_policy_plan_uid": first.get("source_m44_policy_plan_uid"),
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
                "primary_budget_cap": cap,
                "candidate_budget": cap,
                "candidate_visit_order_contract": first.get("candidate_visit_order_contract"),
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
                "unique_frame_ids": len(unique_frames),
                "unique_source_diversity_keys": len(unique_keys),
                "duplicate_frame_rows": max(0, len(rows) - len(unique_frames)),
                "source_role_counts": dict(sorted(Counter(str(row.get("candidate_source_role")) for row in rows).items())),
                "diagnostic_source_gap_boundary_for_reporting": bool(first.get("diagnostic_source_gap_boundary_for_reporting")),
                "use_diagnostic_source_gap_boundary_for_policy": False,
                "uses_task_context_for_decision": bool(first.get("uses_task_context_for_decision")),
                "diagnostic_not_policy_input": True,
                "runner_input_ready": bool(rows) and all(valid_vec3(row.get("execution_stop_position_m")) for row in rows),
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
                "claim_boundary": "M49 materializes repaired trajectory inputs; no trajectory metric has been computed yet.",
            }
        )
    return out


def build_policy_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id in M49_POLICIES:
        rows = by_policy.get(policy_id, [])
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_plan_rows": len(rows),
                "source_ready_plan_rows": sum(1 for row in rows if not row.get("diagnostic_source_gap_boundary_for_reporting")),
                "source_gap_plan_rows": sum(1 for row in rows if row.get("diagnostic_source_gap_boundary_for_reporting")),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in rows]),
                "stale_first_plan_rows": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first_plan_rows": sum(1 for row in rows if row.get("current_observation_first")),
                "mean_old_location_dead_end_cost_proxy_m": mean(
                    [finite_float(row.get("old_location_dead_end_cost_proxy_m")) for row in rows]
                ),
                "runner_input_ready_rows": sum(1 for row in rows if row.get("runner_input_ready")),
                "claim_boundary": "M49 summary is pre-execution materialization only.",
            }
        )
    return out


def build_baseline_preservation_rows(
    m44_candidate_rows: list[dict[str, Any]],
    m49_candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m44_by_key = group_by_scan_task_policy(m44_candidate_rows)
    m49_by_key = group_by_scan_task_policy(m49_candidate_rows)
    out: list[dict[str, Any]] = []
    for key in sorted(m44_by_key):
        adapter_episode_id, task_context_id, policy_id = key
        if policy_id not in BASELINE_POLICIES:
            continue
        m44_rows = m44_by_key[key]
        m49_rows = m49_by_key.get(key, [])
        proposal_pass = proposal_order(m44_rows) == proposal_order(m49_rows)
        source_pass = source_role_order(m44_rows) == source_role_order(m49_rows)
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "task_context_id": task_context_id,
                "object_category": m44_rows[0].get("object_category") if m44_rows else None,
                "policy_id": policy_id,
                "m44_candidate_rows": len(m44_rows),
                "m49_candidate_rows": len(m49_rows),
                "proposal_order_preserved": proposal_pass,
                "source_role_order_preserved": source_pass,
                "preservation_pass": len(m44_rows) == len(m49_rows) and proposal_pass and source_pass,
            }
        )
    return out


def build_repair_target_audit_rows(
    target_rows: list[dict[str, Any]],
    m49_candidate_rows: list[dict[str, Any]],
    m44_candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m49_by_key = group_by_scan_task_policy(m49_candidate_rows)
    m44_by_key = group_by_scan_task_policy(m44_candidate_rows)
    out: list[dict[str, Any]] = []
    for target in target_rows:
        adapter_episode_id = str(target.get("adapter_episode_id"))
        task_context_id = str(target.get("task_context_id"))
        target_uid = str(target.get("target_proposal_uid_for_audit_only"))
        repair_rows = m49_by_key.get((adapter_episode_id, task_context_id, REPAIR_POLICY), [])
        h001_rows = m44_by_key.get((adapter_episode_id, task_context_id, H001_POLICY), [])
        task_rows = m44_by_key.get((adapter_episode_id, task_context_id, TASK_AGNOSTIC_POLICY), [])
        repair_rank = rank_for_proposal(repair_rows, target_uid)
        h001_rank = rank_for_proposal(h001_rows, target_uid)
        task_rank = rank_for_proposal(task_rows, target_uid)
        source_gap = bool(target.get("diagnostic_source_gap_boundary_for_reporting"))
        stale_first = bool(repair_rows and repair_rows[0].get("candidate_source_role") == "stale_old_memory")
        if source_gap:
            passed = repair_rank is not None and not stale_first
        else:
            reference_ranks = [rank for rank in (task_rank, h001_rank) if rank is not None]
            passed = repair_rank is not None and bool(reference_ranks) and repair_rank <= min(reference_ranks)
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "task_context_id": task_context_id,
                "object_category": target.get("object_category"),
                "diagnostic_source_gap_boundary_for_reporting": source_gap,
                "target_proposal_uid_for_audit_only": target_uid,
                "target_allowed_for_policy_input": False,
                "repair_rank": repair_rank,
                "h001_v1_rank": h001_rank,
                "task_agnostic_rank": task_rank,
                "repair_stale_visit_first": stale_first,
                "audit_pass": passed,
                "claim_boundary": "Target proposal uid is used after materialization for audit only, not for policy ordering.",
            }
        )
    return out


def rank_for_proposal(rows: list[dict[str, Any]], proposal_uid: str) -> int | None:
    for row in rows:
        if str(row.get("proposal_uid")) == proposal_uid:
            return int(row.get("visit_rank") or 0)
    return None


def build_input_contract_rows(m48_input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in m48_input_rows:
        current = dict(row)
        current["version"] = VERSION
        current["policy_use"] = "M49 row materialization and M50 trajectory runner leakage audit."
        out.append(current)
    if not any(row.get("field") == "diagnostic_source_gap_boundary_for_reporting" for row in out):
        out.append(
            {
                "version": VERSION,
                "field": "diagnostic_source_gap_boundary_for_reporting",
                "allowed_for_policy": False,
                "policy_use": "Reporting-only split after materialization/execution; never used for ordering.",
            }
        )
    return out


def build_leakage_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked_fields = {str(row.get("field")) for row in input_rows if row.get("allowed_for_policy") is False}
    out: list[dict[str, Any]] = []
    for payload_name, rows in [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        reporting_hits = Counter()
        flag_hits = 0
        over_budget_hits = 0
        for row in rows:
            for field in blocked_fields:
                if field not in row:
                    continue
                if field in REPORTING_ONLY_FIELDS:
                    reporting_hits[field] += 1
                else:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
            if payload_name.startswith("dynamic"):
                cap = int(row.get("primary_budget_cap") or PRIMARY_BUDGET)
                if int(row.get("visit_rank") or 0) > cap:
                    over_budget_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload_name,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "reporting_only_field_hits": dict(sorted(reporting_hits.items())),
                "reporting_only_field_hit_count": sum(reporting_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "over_budget_candidate_hits": over_budget_hits,
                "leakage_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
                "budget_cap_compliance_pass": over_budget_hits == 0,
            }
        )
    return out


def build_readiness_gate_rows(
    m48_coverage: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    repair_target_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policies = {str(row.get("policy_id")) for row in plan_rows}
    return [
        {
            "version": VERSION,
            "gate_id": "m48_contract_ready",
            "status": "pass"
            if m48_coverage.get("status") == "e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_ready"
            else "fail",
            "evidence": f"M48 status `{m48_coverage.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_rows_materialized",
            "status": "pass" if len(candidate_rows) == EXPECTED_CANDIDATE_ROWS else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; expected={EXPECTED_CANDIDATE_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "execution_plan_rows_materialized",
            "status": "pass" if len(plan_rows) == EXPECTED_PLAN_ROWS else "fail",
            "evidence": f"execution plan rows={len(plan_rows)}; expected={EXPECTED_PLAN_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "all_policies_materialized",
            "status": "pass" if set(M49_POLICIES) == policies else "fail",
            "evidence": f"policies={sorted(policies)}.",
        },
        {
            "version": VERSION,
            "gate_id": "baseline_order_preserved",
            "status": "pass" if baseline_rows and all(row.get("preservation_pass") for row in baseline_rows) else "fail",
            "evidence": f"baseline preservation pass rows={sum(1 for row in baseline_rows if row.get('preservation_pass'))}/{len(baseline_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "repair_targets_materialized",
            "status": "pass" if repair_target_rows and all(row.get("audit_pass") for row in repair_target_rows) else "fail",
            "evidence": f"repair target pass rows={sum(1 for row in repair_target_rows if row.get('audit_pass'))}/{len(repair_target_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_input_ready",
            "status": "pass" if plan_rows and all(row.get("runner_input_ready") for row in plan_rows) else "fail",
            "evidence": f"runner-ready plan rows={sum(1 for row in plan_rows if row.get('runner_input_ready'))}/{len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if leakage_rows and all(row.get("leakage_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked field hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "budget_cap_compliance",
            "status": "pass" if leakage_rows and all(row.get("budget_cap_compliance_pass") for row in leakage_rows) else "fail",
            "evidence": f"over-budget hits={sum(int(row.get('over_budget_candidate_hits') or 0) for row in leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "no_trajectory_execution_claim",
            "status": "pass",
            "evidence": "M49 only materializes JSONL rows and does not execute Habitat trajectories.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "repair_rows_materialized",
            "status": "supported_materialization_only",
            "claim_boundary": "M49 supports leakage-safe row materialization for the repaired routine-fetch policy.",
        },
        {
            "version": VERSION,
            "claim_id": "baseline_comparison_preserved",
            "status": "supported_materialization_only",
            "claim_boundary": "M49 preserves all M44 baseline proposal orders for the next paired trajectory comparison.",
        },
        {
            "version": VERSION,
            "claim_id": "repaired_navigation_improvement",
            "status": "not_ready",
            "claim_boundary": "No repaired navigation improvement can be claimed until Docker Habitat execution is run.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "claim_boundary": "M49 does not execute trajectories and does not support final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "claim_boundary": "Structured task context remains a condition on memory trust and visit order, not a natural-language intent claim.",
        },
    ]


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "prepare_repaired_trajectory_execution_contract" if ready else "repair_m49_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M49 routine-fetch repair row materialization",
            "launch_long_job_now": False,
            "requires_docker_next": True,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_m50_command_rows() -> list[dict[str, Any]]:
    command = (
        "python experiments/E008_real_navigation_benchmark/tools/plan_m50_routine_fetch_repair_trajectory_contract.py"
    )
    docker_command_template = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research3/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        "research3/habitat-h001:20260508-calib-artifacts "
        "bash -lc \"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m50_routine_fetch_repair_trajectory_execution_smoke.py\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "m50_contract_next",
            "working_directory": str(ROOT),
            "command": command,
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/coverage.json",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M50_routine_fetch_repair_trajectory_contract_v0/report.md",
            ],
        },
        {
            "version": VERSION,
            "command_id": "m51_or_later_docker_execution_template",
            "working_directory": str(ROOT),
            "command": docker_command_template,
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json"
            ],
            "claim_boundary": "Recorded as a template only; M49 does not launch Docker trajectory execution.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M49 Routine-Fetch Repair Row Materialization",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- M48 status: `{coverage['m48_status']}`",
        f"- Candidate rows: `{coverage['candidate_rows']}`",
        f"- Execution plan rows: `{coverage['trajectory_execution_plan_rows']}`",
        f"- Selected repair policy: `{REPAIR_POLICY}`",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Final real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        "",
        "## Policy Materialization",
        "",
        markdown_table(
            policy_rows,
            [
                "policy_id",
                "policy_plan_rows",
                "candidate_rows",
                "stale_first_plan_rows",
                "current_first_plan_rows",
                "runner_input_ready_rows",
            ],
        ),
        "",
        "## Repair Policy Audit",
        "",
        markdown_table(
            repair_rows,
            [
                "adapter_episode_id",
                "task_context_id",
                "object_category",
                "source_kind",
                "same_order_as_h001_v1",
                "same_order_as_task_agnostic",
                "stale_visit_first",
            ],
        ),
        "",
        "## Regression Target Audit",
        "",
        markdown_table(
            target_rows,
            [
                "adapter_episode_id",
                "object_category",
                "diagnostic_source_gap_boundary_for_reporting",
                "repair_rank",
                "h001_v1_rank",
                "task_agnostic_rank",
                "repair_stale_visit_first",
                "audit_pass",
            ],
        ),
        "",
        "## Readiness Gates",
        "",
        markdown_table(gate_rows, ["gate_id", "status", "evidence"]),
        "",
        "## Decision",
        "",
        "- M49 is materialization only; no trajectory result is claimed.",
        "- Preserve all M44 baseline visit orders for paired comparison.",
        f"- Send `{REPAIR_POLICY}` to the next Docker trajectory contract/preflight gate.",
        "",
    ]
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m44_coverage = read_json(M44_DIR / "coverage.json")
    m48_coverage = read_json(M48_DIR / "coverage.json")
    m44_candidate_rows = read_jsonl(M44_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    m48_input_rows = read_jsonl(M48_DIR / "input_contract_rows.jsonl")
    m48_target_rows = read_jsonl(M48_DIR / "regression_repair_target_rows.jsonl")

    if not m44_coverage or not m48_coverage:
        raise SystemExit("missing M44/M48 coverage")
    if not m44_candidate_rows or not m48_input_rows or not m48_target_rows:
        raise SystemExit("missing M44/M48 row inputs")

    baseline_candidate_rows = clone_baseline_rows(m44_candidate_rows)
    repair_candidate_rows, repair_audit_rows = materialize_repair_policy(m44_candidate_rows)
    candidate_rows = sorted(
        baseline_candidate_rows + repair_candidate_rows,
        key=lambda row: (
            str(row.get("adapter_episode_id")),
            str(row.get("task_context_id")),
            M49_POLICIES.index(str(row.get("policy_id"))) if str(row.get("policy_id")) in M49_POLICIES else 99,
            int(row.get("visit_rank") or 10**9),
        ),
    )
    plan_rows = build_execution_plan_rows(candidate_rows)
    policy_rows = build_policy_summary_rows(plan_rows)
    baseline_rows = build_baseline_preservation_rows(m44_candidate_rows, candidate_rows)
    target_audit_rows = build_repair_target_audit_rows(m48_target_rows, candidate_rows, m44_candidate_rows)
    input_rows = build_input_contract_rows(m48_input_rows)
    leakage_rows = build_leakage_rows(candidate_rows, plan_rows, input_rows)
    gate_rows = build_readiness_gate_rows(m48_coverage, candidate_rows, plan_rows, baseline_rows, target_audit_rows, leakage_rows)
    ready = all(row.get("status") == "pass" for row in gate_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_rows(ready)
    command_rows = build_m50_command_rows()

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m44_status": m44_coverage.get("status"),
        "m48_status": m48_coverage.get("status"),
        "candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "expected_candidate_rows": EXPECTED_CANDIDATE_ROWS,
        "expected_trajectory_execution_plan_rows": EXPECTED_PLAN_ROWS,
        "policy_count": len({row.get("policy_id") for row in plan_rows}),
        "policy_materialization_summary_rows": len(policy_rows),
        "baseline_preservation_audit_rows": len(baseline_rows),
        "baseline_preservation_pass_rows": sum(1 for row in baseline_rows if row.get("preservation_pass")),
        "repair_policy_audit_rows": len(repair_audit_rows),
        "routine_fetch_repair_rows": sum(1 for row in repair_audit_rows if row.get("task_context_id") == "routine_fetch"),
        "regression_repair_target_audit_rows": len(target_audit_rows),
        "regression_repair_target_pass_rows": sum(1 for row in target_audit_rows if row.get("audit_pass")),
        "input_contract_rows": len(input_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_pass") for row in leakage_rows),
        "budget_cap_compliance_pass": all(row.get("budget_cap_compliance_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "readiness_gate_pass_rows": sum(1 for row in gate_rows if row.get("status") == "pass"),
        "selected_repair_policy": REPAIR_POLICY,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M49 routine-fetch repair row materialization",
        "launch_long_job_now": False,
        "requires_docker_now": False,
        "m50_requires_docker": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "routine_fetch_repair_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "routine_fetch_repair_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_summary_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "baseline_preservation_audit_rows.jsonl", baseline_rows)
    write_jsonl(ARTIFACT_DIR / "repair_policy_audit_rows.jsonl", repair_audit_rows)
    write_jsonl(ARTIFACT_DIR / "regression_repair_target_audit_rows.jsonl", target_audit_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m50_command_rows.jsonl", command_rows)
    write_report(coverage, policy_rows, repair_audit_rows, target_audit_rows, gate_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
