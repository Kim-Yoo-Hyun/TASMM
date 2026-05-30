#!/usr/bin/env python3
"""Materialize H001 visit-order/path rows from E008-M25 source rows."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M26_h001_visit_order_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M26_h001_visit_order_path_smoke_v0"
M25_DIR = EXP_ROOT / "artifacts" / "E008-M25_h001_candidate_source_materialization_smoke_v0"
VERSION = "e008_m26_h001_visit_order_path_smoke_v0"

BLOCKED_RUNTIME_ROLES = {"external_map", "runtime_event"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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


def valid_vec3(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(finite_float(component) is not None for component in value)
    )


def safe_mean(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def safe_rate(num: int, den: int) -> float | None:
    return round(float(num) / float(den), 6) if den else None


def is_path_ready(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("path_ready"))
        and row.get("navmesh_validation_status") == "candidate_path_ready"
        and finite_float(row.get("source_to_candidate_path_cost_m")) is not None
        and valid_vec3(row.get("candidate_stop_position_m"))
    )


def confidence_sort_key(row: dict[str, Any]) -> tuple[float, float, float, int, str]:
    confidence = finite_float(row.get("candidate_confidence")) or 0.0
    reliability = finite_float(row.get("proposal_reliability_score")) or 0.0
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m")) or 1e9
    rank = int(row.get("candidate_rank") or 10**9)
    return (-confidence, -reliability, path_cost, rank, str(row.get("source_row_uid")))


def reliability_sort_key(row: dict[str, Any]) -> tuple[float, float, float, int, str]:
    reliability = finite_float(row.get("proposal_reliability_score")) or 0.0
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m")) or 1e9
    confidence = finite_float(row.get("candidate_confidence")) or 0.0
    rank = int(row.get("candidate_rank") or 10**9)
    return (-reliability, path_cost, -confidence, rank, str(row.get("source_row_uid")))


def path_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, float, int, str]:
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m")) or 1e9
    reliability = finite_float(row.get("proposal_reliability_score")) or 0.0
    confidence = finite_float(row.get("candidate_confidence")) or 0.0
    rank = int(row.get("candidate_rank") or 10**9)
    return (path_cost, -reliability, -confidence, rank, str(row.get("source_row_uid")))


def source_key(plan: dict[str, Any], role: str) -> tuple[str, str, str]:
    return (str(plan.get("adapter_episode_id")), str(plan.get("task_context_id")), role)


def source_accounting_row(
    plan: dict[str, Any],
    role: str,
    source_rows: list[dict[str, Any]],
    path_ready_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "policy_plan_uid": plan.get("policy_plan_uid"),
        "policy_id": plan.get("policy_id"),
        "policy_family": plan.get("policy_family"),
        "adapter_episode_id": plan.get("adapter_episode_id"),
        "scan_id": plan.get("scan_id"),
        "scene_key": plan.get("scene_key"),
        "object_category": plan.get("object_category"),
        "task_context_id": plan.get("task_context_id"),
        "source_role": role,
        "source_role_required": True,
        "source_rows": len(source_rows),
        "path_ready_rows": len(path_ready_rows),
        "non_path_ready_rows": max(0, len(source_rows) - len(path_ready_rows)),
        "selected_visit_rows": len(selected_rows),
        "role_path_ready": bool(path_ready_rows) if role not in BLOCKED_RUNTIME_ROLES else False,
        "filter_reason": "path_ready_only_for_execution_smoke",
    }


def select_rows_for_plan(
    plan: dict[str, Any],
    grouped_source_rows: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    policy_id = str(plan.get("policy_id"))
    required_roles = [str(role) for role in plan.get("required_source_roles", [])]
    source_filter_rows: list[dict[str, Any]] = []
    blocked = any(role in BLOCKED_RUNTIME_ROLES for role in required_roles)

    role_rows: dict[str, list[dict[str, Any]]] = {}
    role_path_ready_rows: dict[str, list[dict[str, Any]]] = {}
    for role in required_roles:
        source_rows = grouped_source_rows.get(source_key(plan, role), [])
        path_ready_rows = [row for row in source_rows if is_path_ready(row)]
        role_rows[role] = source_rows
        role_path_ready_rows[role] = path_ready_rows

    selections: list[tuple[str, list[dict[str, Any]], str]] = []
    if not blocked:
        initial = role_path_ready_rows.get("initial_memory_proxy", [])
        current = role_path_ready_rows.get("current_observation", [])
        initial_budget = int(plan.get("h001_initial_memory_budget") or 0)
        current_budget = int(plan.get("h001_current_observation_budget") or 0)

        if policy_id == "real_static_memory_proxy_v0":
            selections.append(
                (
                    "initial_memory_proxy",
                    sorted(initial, key=confidence_sort_key)[:initial_budget],
                    "static_memory_proxy_confidence_desc_top1",
                )
            )
        elif policy_id == "real_detector_confidence_expanded_v0":
            selections.append(
                (
                    "current_observation",
                    sorted(current, key=confidence_sort_key)[:current_budget],
                    "current_observation_confidence_desc_top5",
                )
            )
        elif policy_id == "real_context_agnostic_memory_trust_reobserve_v0":
            selections.append(
                (
                    "initial_memory_proxy",
                    sorted(initial, key=confidence_sort_key)[:initial_budget],
                    "context_agnostic_initial_proxy_top1",
                )
            )
            selections.append(
                (
                    "current_observation",
                    sorted(current, key=confidence_sort_key)[:current_budget],
                    "context_agnostic_current_observation_top3",
                )
            )
        elif policy_id == "h001_real_task_context_memory_trust_v0":
            task_context_id = str(plan.get("task_context_id"))
            if task_context_id == "noisy_high_value_fetch":
                selections.append(
                    (
                        "current_observation",
                        sorted(current, key=reliability_sort_key)[:current_budget],
                        "h001_noisy_high_value_current_reobserve_reliability_first",
                    )
                )
                selections.append(
                    (
                        "initial_memory_proxy",
                        sorted(initial, key=reliability_sort_key)[:initial_budget],
                        "h001_noisy_high_value_initial_memory_guard",
                    )
                )
            else:
                selections.append(
                    (
                        "initial_memory_proxy",
                        sorted(initial, key=reliability_sort_key)[:initial_budget],
                        f"h001_{task_context_id}_trusted_initial_memory_top1",
                    )
                )
                selections.append(
                    (
                        "current_observation",
                        sorted(current, key=path_cost_sort_key)[:current_budget],
                        f"h001_{task_context_id}_bounded_reobservation_path_cost",
                    )
                )

    selected_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    selected_rows: list[dict[str, Any]] = []
    visit_index = 0
    cumulative_known_path_cost = 0.0
    for role, rows, reason in selections:
        for row in rows:
            visit_index += 1
            path_cost = finite_float(row.get("source_to_candidate_path_cost_m")) or 0.0
            cumulative_known_path_cost += path_cost
            visit_row = {
                "version": VERSION,
                "candidate_visit_uid": f"m26::{plan.get('policy_plan_uid')}::{visit_index:03d}",
                "policy_plan_uid": plan.get("policy_plan_uid"),
                "policy_id": plan.get("policy_id"),
                "policy_family": plan.get("policy_family"),
                "adapter_episode_id": plan.get("adapter_episode_id"),
                "scan_id": plan.get("scan_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "task_context_id": plan.get("task_context_id"),
                "candidate_visit_order_contract": plan.get("candidate_visit_order_contract"),
                "candidate_order_component": reason,
                "visit_order_index": visit_index,
                "source_role": role,
                "source_row_uid": row.get("source_row_uid"),
                "proposal_uid": row.get("proposal_uid"),
                "raw_candidate_uid": row.get("raw_candidate_uid"),
                "frame_id": row.get("frame_id"),
                "label_canonical": row.get("label_canonical"),
                "candidate_rank": row.get("candidate_rank"),
                "candidate_confidence": row.get("candidate_confidence"),
                "proposal_reliability_score": row.get("proposal_reliability_score"),
                "staleness_proxy_score": row.get("staleness_proxy_score"),
                "selection_score": row.get("selection_score"),
                "snap_distance_m": row.get("snap_distance_m"),
                "candidate_position_m": row.get("candidate_position_m"),
                "candidate_stop_position_m": row.get("candidate_stop_position_m"),
                "candidate_source_position_m": row.get("candidate_source_position_m"),
                "source_to_candidate_path_cost_m": path_cost,
                "cumulative_known_path_cost_m": round(cumulative_known_path_cost, 6),
                "path_ready": True,
                "navmesh_validation_status": row.get("navmesh_validation_status"),
                "policy_input_allowed": bool(row.get("policy_input_allowed", True)),
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M26 materializes H001 visit order and known source-to-candidate path-cost proxy only; no executed SR/SPL claim.",
            }
            selected_rows.append(visit_row)
            selected_by_role[role].append(visit_row)

    for role in required_roles:
        source_filter_rows.append(
            source_accounting_row(
                plan,
                role,
                role_rows.get(role, []),
                role_path_ready_rows.get(role, []),
                selected_by_role.get(role, []),
            )
        )
    return selected_rows, source_filter_rows, blocked


def build_scan_metric_row(plan: dict[str, Any], visit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    costs = [finite_float(row.get("source_to_candidate_path_cost_m")) for row in visit_rows]
    cost_values = [cost for cost in costs if cost is not None]
    initial_budget = int(plan.get("h001_initial_memory_budget") or 0)
    current_budget = int(plan.get("h001_current_observation_budget") or 0)
    effective_budget = initial_budget + current_budget
    budget_fulfilled = len(visit_rows) == effective_budget
    return {
        "version": VERSION,
        "metric_scope": "scan_policy",
        "scan_policy_metric_uid": f"m26::{plan.get('policy_plan_uid')}::metric",
        "policy_plan_uid": plan.get("policy_plan_uid"),
        "policy_id": plan.get("policy_id"),
        "policy_family": plan.get("policy_family"),
        "adapter_episode_id": plan.get("adapter_episode_id"),
        "scan_id": plan.get("scan_id"),
        "scene_key": plan.get("scene_key"),
        "object_category": plan.get("object_category"),
        "task_context_id": plan.get("task_context_id"),
        "required_source_roles": plan.get("required_source_roles"),
        "candidate_visit_order_contract": plan.get("candidate_visit_order_contract"),
        "max_candidate_budget": plan.get("max_candidate_budget"),
        "effective_candidate_budget": effective_budget,
        "h001_initial_memory_budget": initial_budget,
        "h001_current_observation_budget": current_budget,
        "selected_visit_rows": len(visit_rows),
        "selected_path_ready_rows": sum(1 for row in visit_rows if row.get("path_ready")),
        "selected_non_path_ready_rows": sum(1 for row in visit_rows if not row.get("path_ready")),
        "candidate_budget_fulfilled": budget_fulfilled,
        "first_candidate_path_cost_m": cost_values[0] if cost_values else None,
        "known_path_cost_proxy_sum_m": round(sum(cost_values), 6) if cost_values else None,
        "mean_candidate_path_cost_m": safe_mean(cost_values),
        "max_candidate_path_cost_m": max(cost_values) if cost_values else None,
        "candidate_visit_order_path_smoke_ready": bool(visit_rows) and budget_fulfilled,
        "trajectory_execution_input_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "real_navigation_sr_spl_ready": False,
        "status": "ready_for_goal_evaluation_smoke" if bool(visit_rows) and budget_fulfilled else "blocked_incomplete_visit_order",
        "claim_boundary": "M26 path cost is a known source-to-candidate proxy; inter-candidate trajectory execution and SR/SPL are deferred.",
    }


def aggregate_metric_rows(scan_metric_rows: list[dict[str, Any]], blocked_plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metric_rows:
        grouped[str(row.get("policy_id"))].append(row)
    for policy_id, policy_rows in sorted(grouped.items()):
        first_costs = [
            finite_float(row.get("first_candidate_path_cost_m"))
            for row in policy_rows
            if finite_float(row.get("first_candidate_path_cost_m")) is not None
        ]
        sum_costs = [
            finite_float(row.get("known_path_cost_proxy_sum_m"))
            for row in policy_rows
            if finite_float(row.get("known_path_cost_proxy_sum_m")) is not None
        ]
        rows.append(
            {
                "version": VERSION,
                "metric_scope": "aggregate_policy",
                "policy_id": policy_id,
                "policy_family": policy_rows[0].get("policy_family"),
                "scan_policy_rows": len(policy_rows),
                "ready_scan_policy_rows": sum(
                    1 for row in policy_rows if row.get("candidate_visit_order_path_smoke_ready")
                ),
                "candidate_budget_fulfilled_rows": sum(1 for row in policy_rows if row.get("candidate_budget_fulfilled")),
                "selected_visit_rows": sum(int(row.get("selected_visit_rows") or 0) for row in policy_rows),
                "selected_path_ready_rows": sum(int(row.get("selected_path_ready_rows") or 0) for row in policy_rows),
                "mean_first_candidate_path_cost_m": safe_mean(first_costs),
                "mean_known_path_cost_proxy_sum_m": safe_mean(sum_costs),
                "ready_rate": safe_rate(
                    sum(1 for row in policy_rows if row.get("candidate_visit_order_path_smoke_ready")),
                    len(policy_rows),
                ),
                "trajectory_execution_input_ready": False,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "Aggregate path metrics are visit-order/path-cost smoke metrics, not executed navigation results.",
            }
        )
    blocked_by_policy = Counter(str(row.get("policy_id")) for row in blocked_plan_rows)
    for policy_id, count in sorted(blocked_by_policy.items()):
        rows.append(
            {
                "version": VERSION,
                "metric_scope": "aggregate_policy",
                "policy_id": policy_id,
                "policy_family": blocked_plan_rows[0].get("policy_family") if blocked_plan_rows else None,
                "scan_policy_rows": 0,
                "blocked_policy_plan_rows": count,
                "ready_scan_policy_rows": 0,
                "candidate_budget_fulfilled_rows": 0,
                "selected_visit_rows": 0,
                "selected_path_ready_rows": 0,
                "ready_rate": 0.0,
                "trajectory_execution_input_ready": False,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "External-map fallback is blocked until external map candidates and runtime miss events are materialized.",
            }
        )
    return rows


def build_blocked_policy_row(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "policy_plan_uid": plan.get("policy_plan_uid"),
        "policy_id": plan.get("policy_id"),
        "policy_family": plan.get("policy_family"),
        "adapter_episode_id": plan.get("adapter_episode_id"),
        "scan_id": plan.get("scan_id"),
        "scene_key": plan.get("scene_key"),
        "object_category": plan.get("object_category"),
        "task_context_id": plan.get("task_context_id"),
        "required_source_roles": plan.get("required_source_roles"),
        "blocked_reason": "missing_external_map_or_runtime_event_source_for_h001_fallback",
        "selected_visit_rows": 0,
        "real_navigation_sr_spl_ready": False,
        "claim_boundary": "M26 does not execute external-map fallback without materialized external-map source rows and observed-miss runtime events.",
    }


def build_leakage_audit_rows(
    source_rows: list[dict[str, Any]],
    query_context_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "check_id": "m25_source_rows_no_eval_goal_or_viewpoint_policy_input",
            "rows_checked": len(source_rows),
            "passed": not any(row.get("uses_objectnav_eval_goal") or row.get("uses_objectnav_eval_viewpoint") for row in source_rows),
        },
        {
            "version": VERSION,
            "check_id": "m25_query_context_rows_no_eval_goal_or_viewpoint_policy_input",
            "rows_checked": len(query_context_rows),
            "passed": not any(row.get("uses_objectnav_eval_goal") or row.get("uses_objectnav_eval_viewpoint") for row in query_context_rows),
        },
        {
            "version": VERSION,
            "check_id": "m26_visit_rows_no_eval_goal_or_viewpoint_policy_input",
            "rows_checked": len(visit_rows),
            "passed": not any(row.get("uses_objectnav_eval_goal") or row.get("uses_objectnav_eval_viewpoint") for row in visit_rows),
        },
        {
            "version": VERSION,
            "check_id": "m26_metric_rows_do_not_claim_real_sr_spl",
            "rows_checked": len(metric_rows),
            "passed": not any(row.get("real_navigation_sr_spl_ready") for row in metric_rows),
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_h001_visit_order_materialization",
            "supported": True,
            "claim_boundary": "H001 policy plans can be converted into candidate visit-order rows using non-oracle source rows and precomputed navmesh reachability.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_h001_path_cost_proxy",
            "supported": True,
            "claim_boundary": "M26 provides source-to-candidate path-cost proxy rows for candidate ranking/accounting.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M26 does not execute a navigation agent and does not compute final SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_true_dynamic_stale_memory_on_hm3d",
            "supported": False,
            "claim_boundary": "The initial memory source is an HM3D static-memory proxy, not a true dynamic stale-memory event stream.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_natural_language_human_intent",
            "supported": False,
            "claim_boundary": "Task context is structured and changes memory trust/re-observation budget; natural-language intent parsing is not tested here.",
        },
    ]


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    source_filter_counts: Counter[str],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {scan_policy_rows} | {ready_scan_policy_rows} | {selected_visit_rows} | "
            "{mean_first_candidate_path_cost_m} | {mean_known_path_cost_proxy_sum_m} | {ready_rate} |".format(
                **{
                    "policy_id": row.get("policy_id"),
                    "scan_policy_rows": row.get("scan_policy_rows", 0),
                    "ready_scan_policy_rows": row.get("ready_scan_policy_rows", 0),
                    "selected_visit_rows": row.get("selected_visit_rows", 0),
                    "mean_first_candidate_path_cost_m": format_value(row.get("mean_first_candidate_path_cost_m")),
                    "mean_known_path_cost_proxy_sum_m": format_value(row.get("mean_known_path_cost_proxy_sum_m")),
                    "ready_rate": format_value(row.get("ready_rate")),
                }
            )
        )
    source_filter_line = ", ".join(f"`{key}` {value}" for key, value in sorted(source_filter_counts.items())) or "none"
    return f"""# E008-M26 H001 Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M25 status: `{coverage['m25_status']}`.
- Candidate source rows: {coverage['h001_candidate_source_rows']}.
- Policy execution plan rows: {coverage['h001_policy_execution_plan_rows']}.
- Evaluated ready policy plans: {coverage['evaluated_policy_plan_rows']}.
- Blocked policy plans retained: {coverage['blocked_policy_plan_rows']}.
- H001 candidate visit-order rows: {coverage['h001_candidate_visit_order_rows']}.
- Policy path metric rows: {coverage['h001_policy_path_metric_rows']}.
- Source filter accounting rows: {coverage['source_filter_accounting_rows']} ({source_filter_line}).
- Source input leakage pass: {coverage['source_input_leakage_pass']}.

## Policy Aggregate

| policy_id | scan rows | ready rows | visit rows | mean first path m | mean known path sum m | ready rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- E008-M26 is a visit-order/path-cost smoke for H001 policy rows, not an executed `Habitat` navigation benchmark.
- E008-M26 does not compute final real navigation `SR` / `SPL`.
- Path cost is the known source-to-candidate path proxy from M25, not an inter-candidate trajectory execution cost.
- `initial_memory_proxy` is still an HM3D static-memory proxy, not a true dynamic stale-memory stream.
- Structured `task_context_id` controls memory trust/re-observation budget; natural-language human intent is not tested here.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m25_coverage = read_json(M25_DIR / "coverage.json")
    source_rows = read_jsonl(M25_DIR / "h001_candidate_source_rows.jsonl")
    query_context_rows = read_jsonl(M25_DIR / "h001_query_context_rows.jsonl")
    policy_plan_rows = read_jsonl(M25_DIR / "h001_policy_execution_plan_rows.jsonl")
    if not source_rows or not policy_plan_rows:
        raise SystemExit("missing M25 source rows or policy plan rows")

    grouped_source_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        grouped_source_rows[(str(row.get("adapter_episode_id")), str(row.get("task_context_id")), str(row.get("source_role")))].append(row)

    visit_rows: list[dict[str, Any]] = []
    source_filter_rows: list[dict[str, Any]] = []
    scan_metric_rows: list[dict[str, Any]] = []
    blocked_policy_rows: list[dict[str, Any]] = []

    for plan in policy_plan_rows:
        selected_rows, filter_rows, blocked = select_rows_for_plan(plan, grouped_source_rows)
        source_filter_rows.extend(filter_rows)
        if blocked:
            blocked_policy_rows.append(build_blocked_policy_row(plan))
            continue
        visit_rows.extend(selected_rows)
        scan_metric_rows.append(build_scan_metric_row(plan, selected_rows))

    aggregate_rows = aggregate_metric_rows(scan_metric_rows, blocked_policy_rows)
    metric_rows = scan_metric_rows + aggregate_rows
    leakage_audit_rows = build_leakage_audit_rows(source_rows, query_context_rows, visit_rows, metric_rows)
    claim_boundary_rows = build_claim_boundary_rows()

    source_input_leakage_pass = all(row.get("passed") for row in leakage_audit_rows)
    ready_scan_metric_rows = sum(1 for row in scan_metric_rows if row.get("candidate_visit_order_path_smoke_ready"))
    evaluated_policy_plan_rows = len(scan_metric_rows)
    materialized_ready_policy_plan_rows = sum(1 for row in policy_plan_rows if row.get("materialized_for_next_runner"))
    blocked_policy_plan_rows = len(blocked_policy_rows)
    all_selected_path_ready = all(row.get("path_ready") for row in visit_rows)
    h001_visit_order_path_smoke_ready = (
        bool(visit_rows)
        and ready_scan_metric_rows == evaluated_policy_plan_rows
        and evaluated_policy_plan_rows == materialized_ready_policy_plan_rows
        and blocked_policy_plan_rows == len(policy_plan_rows) - materialized_ready_policy_plan_rows
        and all_selected_path_ready
        and source_input_leakage_pass
    )

    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "proceed_to_leakage_safe_goal_evaluation_smoke" if h001_visit_order_path_smoke_ready else "repair_m26_visit_order_path_smoke",
            "selected_next_unit": "E008-M27 H001 leakage-safe goal-evaluation smoke"
            if h001_visit_order_path_smoke_ready
            else "repair E008-M26 H001 visit-order/path smoke",
            "reason": "H001 policy plans now have path-ready visit-order rows without eval-goal leakage; next step is eval-only goal hit scoring."
            if h001_visit_order_path_smoke_ready
            else "H001 visit-order/path rows are incomplete or leakage audit failed.",
            "launch_long_job_now": False,
            "h001_visit_order_path_smoke_ready": h001_visit_order_path_smoke_ready,
            "h001_navigation_policy_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]

    status = (
        "e008_m26_h001_visit_order_path_smoke_ready_goal_eval_next"
        if h001_visit_order_path_smoke_ready
        else "e008_m26_h001_visit_order_path_smoke_blocked"
    )
    source_filter_counts = Counter(str(row.get("source_role")) for row in source_filter_rows)
    source_role_selected_counts = Counter(str(row.get("source_role")) for row in visit_rows)
    policy_visit_counts = Counter(str(row.get("policy_id")) for row in visit_rows)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m25_status": m25_coverage.get("status"),
        "h001_candidate_source_rows": len(source_rows),
        "h001_query_context_rows": len(query_context_rows),
        "h001_policy_execution_plan_rows": len(policy_plan_rows),
        "materialized_ready_policy_plan_rows": materialized_ready_policy_plan_rows,
        "evaluated_policy_plan_rows": evaluated_policy_plan_rows,
        "blocked_policy_plan_rows": blocked_policy_plan_rows,
        "h001_candidate_visit_order_rows": len(visit_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_metric_rows": len(aggregate_rows),
        "h001_policy_path_metric_rows": len(metric_rows),
        "source_filter_accounting_rows": len(source_filter_rows),
        "source_filter_rows_by_role": dict(sorted(source_filter_counts.items())),
        "selected_visit_rows_by_role": dict(sorted(source_role_selected_counts.items())),
        "selected_visit_rows_by_policy": dict(sorted(policy_visit_counts.items())),
        "selected_visit_rows_path_ready": sum(1 for row in visit_rows if row.get("path_ready")),
        "source_input_leakage_pass": source_input_leakage_pass,
        "leakage_audit_rows": len(leakage_audit_rows),
        "claim_boundary_rows": len(claim_boundary_rows),
        "route_decision_rows": len(route_decision_rows),
        "h001_visit_order_path_smoke_ready": h001_visit_order_path_smoke_ready,
        "trajectory_execution_input_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "h001_initial_memory_proxy_not_true_dynamic_stale_memory": True,
        "structured_task_context_not_natural_language_intent": True,
        "dynamic_stale_memory_claim_ready_on_hm3d": False,
        "real_navigation_sr_spl_ready": False,
        "real_navigation_sr_spl_smoke_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "h001_candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "h001_policy_path_metric_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "source_filter_accounting_rows.jsonl", source_filter_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_policy_plan_rows.jsonl", blocked_policy_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, aggregate_rows, source_filter_counts),
        encoding="utf-8",
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "h001_candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "h001_policy_path_metric_rows.jsonl", metric_rows)
    write_jsonl(DATA_OUT_DIR / "source_filter_accounting_rows.jsonl", source_filter_rows)
    write_jsonl(DATA_OUT_DIR / "blocked_policy_plan_rows.jsonl", blocked_policy_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
