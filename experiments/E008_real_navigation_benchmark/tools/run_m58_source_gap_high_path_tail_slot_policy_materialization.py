#!/usr/bin/env python3
"""Materialize E008-M58 high-path tail-slot policy rows."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M17_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M49_DIR = EXP_ROOT / "artifacts" / "E008-M49_routine_fetch_repair_row_materialization_smoke_v0"
M56_DIR = EXP_ROOT / "artifacts" / "E008-M56_source_gap_candidate_source_expansion_contract_v0"
M57_DIR = EXP_ROOT / "artifacts" / "E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0"
)

VERSION = "e008_m58_source_gap_high_path_tail_slot_policy_materialization_v0"
READY_STATUS = "e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready"
BLOCKED_STATUS = "e008_m58_source_gap_high_path_tail_slot_policy_materialization_blocked"
NEXT_UNIT = "E008-M59 high-path tail-slot leakage-safe goal-evaluation smoke"

PRIMARY_BUDGET = 5
M49_REPAIR_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
M58_POLICY = "h001_task_conditioned_high_path_tail_slot_budget5_v3"
SELECTED_ROUTE = "h001_safe_top4_plus_high_path_tail_slot_v0"

EXPECTED_M49_CANDIDATE_ROWS = 558
EXPECTED_M49_PLAN_ROWS = 126
EXPECTED_NEW_PLAN_ROWS = 18
EXPECTED_NEW_CANDIDATE_ROWS = 90
EXPECTED_TOTAL_PLAN_ROWS = EXPECTED_M49_PLAN_ROWS + EXPECTED_NEW_PLAN_ROWS
EXPECTED_TOTAL_CANDIDATE_ROWS = EXPECTED_M49_CANDIDATE_ROWS + EXPECTED_NEW_CANDIDATE_ROWS

REPORTING_ONLY_FIELDS = {
    "diagnostic_source_gap_boundary_for_reporting",
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
    "diagnostic_primary_eval_hit",
    "diagnostic_hit_any_viewpoint_xz_1p0",
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
    "diagnostic_source_gap_boundary_for_reporting",
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


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    return [float(value) for value in vec]  # type: ignore[arg-type]


def source_diversity_key(row: dict[str, Any]) -> str:
    pos = as_vec3(row.get("snapped_position_m") or row.get("execution_stop_position_m"))
    spatial = "missing" if pos is None else f"{round(pos[0])}:{round(pos[2])}"
    return f"{row.get('frame_id')}::{spatial}"


def policy_order(rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(row.get("proposal_uid"))
        for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9))
    ]


def group_by_scan_task_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("adapter_episode_id")),
                str(row.get("task_context_id")),
                str(row.get("policy_id")),
            )
        ].append(row)
    return {
        key: sorted(value, key=lambda item: int(item.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def group_by_plan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(value, key=lambda item: int(item.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def m58_plan_uid(adapter_episode_id: str, task_context_id: str) -> str:
    return f"m58::{adapter_episode_id}::{task_context_id}::{M58_POLICY}"


def clone_m49_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["version"] = VERSION
    out["source_version"] = row.get("version")
    out["m58_materialization_kind"] = "m49_policy_order_reuse"
    out["m58_selected_route"] = SELECTED_ROUTE
    out["claim_boundary"] = "M58 reuses M49 baseline rows; no trajectory metric has been computed."
    return out


def clone_base_candidate(source: dict[str, Any], visit_rank: int, plan_uid: str) -> dict[str, Any]:
    row = dict(source)
    row.update(
        {
            "version": VERSION,
            "source_version": source.get("version"),
            "selected_route": SELECTED_ROUTE,
            "m58_plan_uid": plan_uid,
            "source_m49_policy_plan_uid": source.get("policy_plan_uid"),
            "source_m49_candidate_visit_uid": source.get("candidate_visit_uid"),
            "m58_materialization_kind": "h001_safe_top4_reuse",
            "overlay_policy_plan_uid": plan_uid,
            "policy_plan_uid": plan_uid,
            "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
            "candidate_visit_uid": f"{plan_uid}::{visit_rank:03d}",
            "policy_id": M58_POLICY,
            "policy_role": "test_method_h001_safe_high_path_tail_slot",
            "visit_rank": visit_rank,
            "candidate_order_component": "m58_h001_safe_top4_reuse",
            "primary_budget_cap": PRIMARY_BUDGET,
            "candidate_visit_order_contract": SELECTED_ROUTE,
            "use_diagnostic_source_gap_boundary_for_policy": False,
            "policy_input_allowed": True,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "uses_m57_diagnostic_hit_for_policy": False,
            "uses_task_context_for_decision": True,
            "diagnostic_not_policy_input": True,
            "claim_boundary": "M58 materializes high-path tail-slot policy rows only; no trajectory metric has been computed.",
        }
    )
    return row


def build_full_pool_indices(
    visit_rows: list[dict[str, Any]],
    navmesh_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    nav_index = {
        (str(row.get("adapter_episode_id")), str(row.get("proposal_uid"))): row
        for row in navmesh_rows
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in visit_rows:
        if row.get("policy_id") != "detector_confidence_all_candidates_v0":
            continue
        if not row.get("path_ready"):
            continue
        path_cost = finite_float(row.get("source_to_candidate_path_cost_m"))
        if path_cost is None:
            continue
        nav = nav_index.get((str(row.get("adapter_episode_id")), str(row.get("proposal_uid"))), {})
        if not nav or not valid_vec3(nav.get("snapped_position_m")):
            continue
        merged = dict(row)
        merged.update(
            {
                "frame_id": nav.get("frame_id"),
                "candidate_position_m": nav.get("centroid_world_m"),
                "snapped_position_m": nav.get("snapped_position_m"),
                "candidate_stop_position_m": nav.get("snapped_position_m"),
                "execution_stop_position_m": nav.get("snapped_position_m"),
                "source_position_m": nav.get("source_position"),
                "scene_docker_path": nav.get("scene_docker_path"),
                "navmesh_docker_path": nav.get("navmesh_docker_path"),
                "candidate_usable_for_path_smoke": bool(nav.get("candidate_usable_for_path_smoke", True)),
                "source_to_candidate_path_cost_m": path_cost,
                "source_diversity_key": source_diversity_key({**row, **nav}),
            }
        )
        grouped[str(row.get("adapter_episode_id"))].append(merged)
    for episode_id in list(grouped):
        grouped[episode_id] = sorted(
            grouped[episode_id],
            key=lambda item: (
                -(finite_float(item.get("source_to_candidate_path_cost_m")) or -1.0),
                -(finite_float(item.get("confidence")) or -1.0),
                str(item.get("proposal_uid")),
            ),
        )
    return grouped


def clone_high_path_candidate(source: dict[str, Any], base: dict[str, Any], visit_rank: int, plan_uid: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": source.get("version"),
        "selected_route": SELECTED_ROUTE,
        "m58_plan_uid": plan_uid,
        "source_m49_policy_plan_uid": base.get("policy_plan_uid"),
        "source_m49_candidate_visit_uid": None,
        "source_m18_policy_id": source.get("policy_id"),
        "source_m18_detector_rank": source.get("visit_rank"),
        "m58_materialization_kind": "m18_full_pool_high_path_tail_slot",
        "overlay_policy_plan_uid": plan_uid,
        "policy_plan_uid": plan_uid,
        "overlay_candidate_uid": f"{plan_uid}::{visit_rank:03d}",
        "candidate_visit_uid": f"{plan_uid}::{visit_rank:03d}",
        "policy_id": M58_POLICY,
        "policy_role": "test_method_h001_safe_high_path_tail_slot",
        "adapter_episode_id": base.get("adapter_episode_id"),
        "scan_id": base.get("scan_id"),
        "scene_key": base.get("scene_key"),
        "object_category": base.get("object_category"),
        "task_context_id": base.get("task_context_id"),
        "benchmark_row_uid": base.get("benchmark_row_uid"),
        "visit_rank": visit_rank,
        "candidate_order_component": "m58_high_path_tail_slot",
        "candidate_visit_order_contract": SELECTED_ROUTE,
        "primary_budget_cap": PRIMARY_BUDGET,
        "candidate_source_role": "current_observation",
        "source_role": "current_observation",
        "dynamic_stale_overlay_role": "current_evidence",
        "proposal_uid": source.get("proposal_uid"),
        "raw_candidate_uid": source.get("raw_candidate_uid"),
        "frame_id": source.get("frame_id"),
        "label_canonical": source.get("label_canonical"),
        "confidence": source.get("confidence"),
        "ranking_score": source.get("confidence"),
        "selection_score": source.get("selection_score"),
        "candidate_rank_m09": source.get("candidate_rank_m09"),
        "candidate_position_m": source.get("candidate_position_m"),
        "snapped_position_m": source.get("snapped_position_m"),
        "candidate_stop_position_m": source.get("candidate_stop_position_m"),
        "execution_stop_position_m": source.get("execution_stop_position_m"),
        "source_position_m": source.get("source_position_m"),
        "source_to_candidate_path_cost_m": source.get("source_to_candidate_path_cost_m"),
        "cumulative_known_path_cost_m": source.get("source_to_candidate_path_cost_m"),
        "snap_distance_m": source.get("snap_distance_m"),
        "navmesh_validation_status": source.get("navmesh_validation_status"),
        "scene_docker_path": source.get("scene_docker_path"),
        "navmesh_docker_path": source.get("navmesh_docker_path"),
        "path_ready": True,
        "candidate_usable_for_path_smoke": bool(source.get("candidate_usable_for_path_smoke", True)),
        "policy_input_allowed": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "uses_m57_diagnostic_hit_for_policy": False,
        "uses_task_context_for_decision": True,
        "diagnostic_source_gap_boundary_for_reporting": bool(base.get("diagnostic_source_gap_boundary_for_reporting")),
        "use_diagnostic_source_gap_boundary_for_policy": False,
        "diagnostic_not_policy_input": True,
        "source_diversity_key": source.get("source_diversity_key"),
        "source_expansion_route": "m58_high_path_tail_slot_from_m18_full_pool",
        "source_gap_handling": "policy_visible_high_path_tail_slot_applied_to_all_scan_task_rows",
        "claim_boundary": "M58 materializes high-path tail-slot policy rows only; no trajectory metric has been computed.",
    }


def materialize_m58_policy(
    m49_candidate_rows: list[dict[str, Any]],
    full_pool_by_episode: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = group_by_scan_task_policy(m49_candidate_rows)
    keys = sorted(key for key in by_key if key[2] == M49_REPAIR_POLICY)
    new_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for adapter_episode_id, task_context_id, _ in keys:
        base_rows = by_key[(adapter_episode_id, task_context_id, M49_REPAIR_POLICY)]
        plan_uid = m58_plan_uid(adapter_episode_id, task_context_id)
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()
        for source in base_rows[: PRIMARY_BUDGET - 1]:
            row = clone_base_candidate(source, len(selected) + 1, plan_uid)
            selected.append(row)
            seen.add(str(row.get("proposal_uid")))

        tail_source = next(
            (
                row
                for row in full_pool_by_episode.get(adapter_episode_id, [])
                if str(row.get("proposal_uid")) not in seen
            ),
            None,
        )
        tail_from = "m18_full_pool_high_path"
        if tail_source is None:
            tail_source = next((row for row in base_rows if str(row.get("proposal_uid")) not in seen), None)
            tail_from = "m49_h001_v2_fallback"
        if tail_source is not None:
            if tail_from == "m18_full_pool_high_path":
                tail_row = clone_high_path_candidate(tail_source, base_rows[0], len(selected) + 1, plan_uid)
            else:
                tail_row = clone_base_candidate(tail_source, len(selected) + 1, plan_uid)
                tail_row["candidate_order_component"] = "m58_tail_slot_m49_fallback"
                tail_row["m58_materialization_kind"] = "m49_h001_v2_fallback_tail"
            selected.append(tail_row)
            seen.add(str(tail_row.get("proposal_uid")))

        for source in base_rows:
            if len(selected) >= PRIMARY_BUDGET:
                break
            if str(source.get("proposal_uid")) in seen:
                continue
            row = clone_base_candidate(source, len(selected) + 1, plan_uid)
            row["candidate_order_component"] = "m58_fill_from_h001_v2"
            selected.append(row)
            seen.add(str(row.get("proposal_uid")))

        new_rows.extend(selected)
        audit_rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "task_context_id": task_context_id,
                "object_category": base_rows[0].get("object_category") if base_rows else None,
                "policy_id": M58_POLICY,
                "source_policy_id": M49_REPAIR_POLICY,
                "candidate_rows": len(selected),
                "tail_slot_from": tail_from,
                "tail_slot_proposal_uid": selected[-1].get("proposal_uid") if selected else None,
                "tail_slot_visit_rank": selected[-1].get("visit_rank") if selected else None,
                "tail_slot_source_to_candidate_path_cost_m": selected[-1].get("source_to_candidate_path_cost_m") if selected else None,
                "same_top4_as_h001_v2": policy_order(selected[:4]) == policy_order(base_rows[:4]),
                "same_top5_as_h001_v2": policy_order(selected) == policy_order(base_rows[:5]),
                "uses_source_gap_label_for_selection": False,
                "uses_m57_diagnostic_hit_for_selection": False,
                "claim_boundary": "Tail-slot audit is materialization-only; diagnostic labels are evaluated in separate audit rows.",
            }
        )
    return new_rows, audit_rows


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
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(group_by_plan(candidate_rows).items()):
        first = rows[0]
        stale_rows = [row for row in rows if row.get("candidate_source_role") == "stale_old_memory"]
        current_rows = [row for row in rows if row.get("candidate_source_role") == "current_observation"]
        unique_frames = {str(row.get("frame_id")) for row in rows if row.get("frame_id")}
        unique_keys = {str(row.get("source_diversity_key")) for row in rows if row.get("source_diversity_key")}
        cap = int(first.get("primary_budget_cap") or PRIMARY_BUDGET)
        out.append(
            {
                "version": VERSION,
                "selected_route": first.get("selected_route") or SELECTED_ROUTE,
                "m58_plan_uid": first.get("m58_plan_uid"),
                "source_m49_policy_plan_uid": first.get("source_m49_policy_plan_uid") or first.get("policy_plan_uid"),
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
                "old_location_dead_end_cost_proxy_m": old_location_dead_end_proxy(rows),
                "stale_visit_rate_proxy": len(stale_rows) / len(rows) if rows else 0.0,
                "reobservation_rate_proxy": len(current_rows) / len(rows) if rows else 0.0,
                "unique_frame_ids": len(unique_frames),
                "unique_source_diversity_keys": len(unique_keys),
                "duplicate_frame_rows": max(0, len(rows) - len(unique_frames)),
                "source_role_counts": dict(sorted(Counter(str(row.get("candidate_source_role")) for row in rows).items())),
                "diagnostic_source_gap_boundary_for_reporting": bool(first.get("diagnostic_source_gap_boundary_for_reporting")),
                "use_diagnostic_source_gap_boundary_for_policy": False,
                "uses_m57_diagnostic_hit_for_policy": False,
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
                "claim_boundary": "M58 materializes high-path tail-slot trajectory inputs; no trajectory metric has been computed yet.",
            }
        )
    return out


def build_policy_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id in sorted(by_policy):
        rows = by_policy[policy_id]
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_plan_rows": len(rows),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "source_gap_plan_rows": sum(1 for row in rows if row.get("diagnostic_source_gap_boundary_for_reporting")),
                "stale_first_plan_rows": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first_plan_rows": sum(1 for row in rows if row.get("current_observation_first")),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in rows]),
                "mean_old_location_dead_end_cost_proxy_m": mean(
                    [finite_float(row.get("old_location_dead_end_cost_proxy_m")) for row in rows]
                ),
                "runner_input_ready_rows": sum(1 for row in rows if row.get("runner_input_ready")),
                "claim_boundary": "M58 summary is pre-execution materialization only.",
            }
        )
    return out


def build_m49_preservation_rows(m49_candidate_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m49_by_plan = group_by_plan(m49_candidate_rows)
    m58_by_plan = group_by_plan(candidate_rows)
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(m49_by_plan.items()):
        copied_rows = m58_by_plan.get(plan_uid, [])
        out.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "policy_id": rows[0].get("policy_id") if rows else None,
                "adapter_episode_id": rows[0].get("adapter_episode_id") if rows else None,
                "task_context_id": rows[0].get("task_context_id") if rows else None,
                "m49_candidate_rows": len(rows),
                "m58_copied_candidate_rows": len(copied_rows),
                "proposal_order_preserved": policy_order(rows) == policy_order(copied_rows),
                "preservation_pass": len(rows) == len(copied_rows) and policy_order(rows) == policy_order(copied_rows),
            }
        )
    return out


def build_diagnostic_hit_sets(m57_feature_rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for row in m57_feature_rows:
        if row.get("diagnostic_primary_eval_hit"):
            out[str(row.get("adapter_episode_id"))].add(str(row.get("proposal_uid")))
    return out


def rank_for_hit(rows: list[dict[str, Any]], hit_uids: set[str]) -> int | None:
    ranks = [
        int(row.get("visit_rank") or 10**9)
        for row in rows
        if str(row.get("proposal_uid")) in hit_uids
    ]
    return min(ranks) if ranks else None


def build_source_gap_recovery_rows(
    m49_candidate_rows: list[dict[str, Any]],
    m58_candidate_rows: list[dict[str, Any]],
    m56_case_rows: list[dict[str, Any]],
    m57_feature_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hit_sets = build_diagnostic_hit_sets(m57_feature_rows)
    m49_by_key = group_by_scan_task_policy(m49_candidate_rows)
    m58_by_key = group_by_scan_task_policy(m58_candidate_rows)
    source_gap_type = {str(row.get("adapter_episode_id")): str(row.get("source_gap_type")) for row in m56_case_rows}
    audit_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key in sorted(k for k in m58_by_key if k[2] == M58_POLICY):
        adapter_episode_id, task_context_id, _ = key
        hits = hit_sets.get(adapter_episode_id, set())
        base_rows = m49_by_key.get((adapter_episode_id, task_context_id, M49_REPAIR_POLICY), [])
        new_rows = m58_by_key.get(key, [])
        base_rank = rank_for_hit(base_rows, hits)
        new_rank = rank_for_hit(new_rows, hits)
        row = {
            "version": VERSION,
            "adapter_episode_id": adapter_episode_id,
            "task_context_id": task_context_id,
            "object_category": new_rows[0].get("object_category") if new_rows else None,
            "source_gap_type": source_gap_type.get(adapter_episode_id),
            "diagnostic_hit_uids": sorted(hits),
            "diagnostic_hit_uids_allowed_for_policy": False,
            "base_h001_v2_hit_rank": base_rank,
            "m58_high_path_tail_hit_rank": new_rank,
            "base_h001_v2_hit_in_budget": base_rank is not None and base_rank <= PRIMARY_BUDGET,
            "m58_high_path_tail_hit_in_budget": new_rank is not None and new_rank <= PRIMARY_BUDGET,
            "recovered_by_m58": base_rank is None and new_rank is not None and new_rank <= PRIMARY_BUDGET,
            "preserved_base_success": base_rank is not None and new_rank is not None,
            "uses_diagnostic_hit_for_policy": False,
            "claim_boundary": "Diagnostic hit rank is audit-only; M58 policy order uses no eval labels.",
        }
        audit_rows.append(row)
        by_episode[adapter_episode_id].append(row)
    for episode_id, rows in sorted(by_episode.items()):
        unrecovered = source_gap_type.get(episode_id) == "full_pool_hit_budget5_surfacing_failure"
        episode_rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "object_category": rows[0].get("object_category") if rows else None,
                "source_gap_type": source_gap_type.get(episode_id),
                "task_context_rows": len(rows),
                "base_hit_context_rows": sum(1 for row in rows if row.get("base_h001_v2_hit_in_budget")),
                "m58_hit_context_rows": sum(1 for row in rows if row.get("m58_high_path_tail_hit_in_budget")),
                "m58_recovered_context_rows": sum(1 for row in rows if row.get("recovered_by_m58")),
                "unrecovered_budget_surfacing_episode": unrecovered,
                "unrecovered_episode_recovered_by_m58": bool(
                    unrecovered and all(row.get("m58_high_path_tail_hit_in_budget") for row in rows)
                ),
                "claim_boundary": "Episode recovery is diagnostic goal-hit audit, not trajectory SR/SPL.",
            }
        )
    return audit_rows, episode_rows


def build_input_contract_rows(m49_input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in m49_input_rows:
        current = dict(row)
        current["version"] = VERSION
        current["policy_use"] = "M58 row materialization and later leakage audit."
        rows.append(current)
        seen.add(str(current.get("field")))
    extra_rows = [
        ("path_cost_descending_rank", True, "Allowed derived rank from policy-visible source-to-candidate path cost."),
        ("diagnostic_primary_eval_hit", False, "Audit-only M57/M59 label; never used for policy ordering."),
        ("diagnostic_hit_any_viewpoint_xz_1p0", False, "Audit-only M57/M59 label; never used for policy ordering."),
        ("diagnostic_hit_uids", False, "Audit-only target ids; never used for policy ordering."),
    ]
    for field, allowed, use in extra_rows:
        if field not in seen:
            rows.append(
                {
                    "version": VERSION,
                    "field": field,
                    "allowed_for_policy": allowed,
                    "policy_use": use,
                }
            )
    return rows


def build_leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]], input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        source_gap_policy_hits = 0
        m57_policy_hits = 0
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
            if row.get("use_diagnostic_source_gap_boundary_for_policy"):
                source_gap_policy_hits += 1
            if row.get("uses_m57_diagnostic_hit_for_policy"):
                m57_policy_hits += 1
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
                "source_gap_boundary_policy_use_hits": source_gap_policy_hits,
                "m57_diagnostic_hit_policy_use_hits": m57_policy_hits,
                "over_budget_candidate_hits": over_budget_hits,
                "leakage_pass": sum(field_hits.values()) == 0
                and flag_hits == 0
                and source_gap_policy_hits == 0
                and m57_policy_hits == 0,
                "budget_cap_compliance_pass": over_budget_hits == 0,
            }
        )
    return out


def build_readiness_gate_rows(
    m57_coverage: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    new_candidate_rows: list[dict[str, Any]],
    new_plan_rows: list[dict[str, Any]],
    preservation_rows: list[dict[str, Any]],
    episode_recovery_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unrecovered_rows = [row for row in episode_recovery_rows if row.get("unrecovered_budget_surfacing_episode")]
    return [
        {
            "version": VERSION,
            "gate_id": "m57_ready",
            "status": "pass"
            if m57_coverage.get("status") == "e008_m57_source_gap_full_pool_candidate_source_feature_audit_ready"
            else "fail",
            "evidence": f"M57 status `{m57_coverage.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_rows_materialized",
            "status": "pass" if len(candidate_rows) == EXPECTED_TOTAL_CANDIDATE_ROWS else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; expected={EXPECTED_TOTAL_CANDIDATE_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "execution_plan_rows_materialized",
            "status": "pass" if len(plan_rows) == EXPECTED_TOTAL_PLAN_ROWS else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected={EXPECTED_TOTAL_PLAN_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "new_policy_full_denominator_materialized",
            "status": "pass"
            if len(new_plan_rows) == EXPECTED_NEW_PLAN_ROWS and len(new_candidate_rows) == EXPECTED_NEW_CANDIDATE_ROWS
            else "fail",
            "evidence": f"new policy plan rows={len(new_plan_rows)}, candidate rows={len(new_candidate_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_policy_orders_preserved",
            "status": "pass" if preservation_rows and all(row.get("preservation_pass") for row in preservation_rows) else "fail",
            "evidence": f"preserved rows={sum(1 for row in preservation_rows if row.get('preservation_pass'))}/{len(preservation_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "unrecovered_source_gap_recovered_in_audit",
            "status": "pass"
            if unrecovered_rows and all(row.get("unrecovered_episode_recovered_by_m58") for row in unrecovered_rows)
            else "fail",
            "evidence": f"unrecovered recovered episodes={sum(1 for row in unrecovered_rows if row.get('unrecovered_episode_recovered_by_m58'))}/{len(unrecovered_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_input_ready",
            "status": "pass" if plan_rows and all(row.get("runner_input_ready") for row in plan_rows) else "fail",
            "evidence": f"runner-ready rows={sum(1 for row in plan_rows if row.get('runner_input_ready'))}/{len(plan_rows)}.",
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
            "evidence": "M58 only materializes JSONL rows and does not execute Habitat trajectories.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "high_path_tail_slot_policy_materialized",
            "status": "supported_materialization_only",
            "claim_boundary": "M58 materializes a budget-5 H001-compatible high-path tail-slot policy over all scan-task rows.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_budget_surfacing_recovered",
            "status": "diagnostic_only",
            "claim_boundary": "Diagnostic hit-rank audit shows recovery, but M58 does not compute trajectory SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "high_path_tail_slot_improves_navigation",
            "status": "not_ready",
            "claim_boundary": "M59 goal evaluation and later Docker trajectory execution are required before navigation claims.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "claim_boundary": "M58 does not create task-context-specific wins; task context remains secondary.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "claim_boundary": "M58 is materialization only and does not support final real navigation SR/SPL.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "run_high_path_tail_goal_evaluation" if ready else "repair_m58_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M58 source-gap high-path tail-slot policy materialization",
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "requires_docker_next": False,
            "requires_docker_after_goal_eval": True,
            "real_navigation_sr_spl_ready": False,
            "deployable_search_policy_ready": False,
        }
    ]


def build_command_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "command_id": "m59_goal_eval_next",
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/run_m59_high_path_tail_slot_goal_evaluation_smoke.py",
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/coverage.json",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0/report.md",
            ],
            "claim_boundary": "M59 is the next planned unit; M58 does not create this script or execute it.",
        }
    ]


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


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def write_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    tail_audit_rows: list[dict[str, Any]],
    episode_recovery_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    selected_tail_rows = [
        row
        for row in tail_audit_rows
        if row.get("policy_id") == M58_POLICY and row.get("task_context_id") == "high_value_fetch"
    ]
    lines = [
        "# E008-M58 Source-Gap High-Path Tail-Slot Policy Materialization",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Candidate rows: {coverage['candidate_rows']}.",
        f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
        f"- New policy: `{M58_POLICY}`.",
        f"- New policy plan rows: {coverage['new_policy_plan_rows']}.",
        f"- New policy candidate rows: {coverage['new_policy_candidate_rows']}.",
        f"- Unrecovered source-gap episodes recovered in diagnostic audit: {coverage['unrecovered_source_gap_recovered_episode_rows']} / {coverage['unrecovered_source_gap_episode_rows']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Policy Materialization",
        "",
        markdown_table(
            policy_rows,
            [
                "policy_id",
                "policy_plan_rows",
                "candidate_rows",
                "source_gap_plan_rows",
                "runner_input_ready_rows",
            ],
        ),
        "",
        "## Tail-Slot Audit",
        "",
        markdown_table(
            selected_tail_rows,
            [
                "adapter_episode_id",
                "task_context_id",
                "object_category",
                "tail_slot_from",
                "tail_slot_visit_rank",
                "tail_slot_source_to_candidate_path_cost_m",
                "same_top4_as_h001_v2",
                "same_top5_as_h001_v2",
            ],
        ),
        "",
        "## Source-Gap Diagnostic Recovery",
        "",
        markdown_table(
            episode_recovery_rows,
            [
                "adapter_episode_id",
                "object_category",
                "source_gap_type",
                "base_hit_context_rows",
                "m58_hit_context_rows",
                "m58_recovered_context_rows",
                "unrecovered_episode_recovered_by_m58",
            ],
        ),
        "",
        "## Readiness Gates",
        "",
        markdown_table(gate_rows, ["gate_id", "status", "evidence"]),
        "",
        "## Claim Boundary",
        "",
        "- M58 materializes policy rows only; it does not execute trajectories.",
        "- The high-path tail-slot rule is applied to all scan-task rows, not only diagnostic source-gap rows.",
        "- Diagnostic hit labels are used only in audit outputs, not in policy ordering.",
        "- Final real navigation `SR` / `SPL`, deployable policy, and human-intent main claims remain blocked.",
        "",
        "## Next",
        "",
        f"- {coverage['selected_next_unit']}: evaluate the materialized policy with leakage-safe goal labels before Docker trajectory execution.",
        "",
    ]
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m49_coverage = read_json(M49_DIR / "coverage.json")
    m57_coverage = read_json(M57_DIR / "coverage.json")
    m49_candidate_rows = read_jsonl(M49_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    m49_input_rows = read_jsonl(M49_DIR / "input_contract_rows.jsonl")
    m56_case_rows = read_jsonl(M56_DIR / "source_gap_case_rows.jsonl")
    m57_feature_rows = read_jsonl(M57_DIR / "source_gap_full_pool_candidate_feature_rows.jsonl")
    visit_rows = read_jsonl(M18_DIR / "candidate_visit_order_rows.jsonl")
    navmesh_rows = read_jsonl(M17_DIR / "candidate_navmesh_rows.jsonl")

    if not m49_coverage or not m57_coverage:
        raise SystemExit("missing M49/M57 coverage")
    if not m49_candidate_rows or not m49_input_rows or not visit_rows or not navmesh_rows:
        raise SystemExit("missing required row inputs")

    full_pool_by_episode = build_full_pool_indices(visit_rows, navmesh_rows)
    copied_m49_candidate_rows = [clone_m49_row(row) for row in m49_candidate_rows]
    new_candidate_rows, tail_slot_audit_rows = materialize_m58_policy(m49_candidate_rows, full_pool_by_episode)
    candidate_rows = sorted(
        copied_m49_candidate_rows + new_candidate_rows,
        key=lambda row: (
            str(row.get("adapter_episode_id")),
            str(row.get("task_context_id")),
            str(row.get("policy_id")),
            int(row.get("visit_rank") or 10**9),
        ),
    )
    plan_rows = build_execution_plan_rows(candidate_rows)
    new_plan_rows = [row for row in plan_rows if row.get("policy_id") == M58_POLICY]
    policy_rows = build_policy_summary_rows(plan_rows)
    preservation_rows = build_m49_preservation_rows(m49_candidate_rows, candidate_rows)
    source_gap_audit_rows, episode_recovery_rows = build_source_gap_recovery_rows(
        m49_candidate_rows,
        new_candidate_rows,
        m56_case_rows,
        m57_feature_rows,
    )
    input_rows = build_input_contract_rows(m49_input_rows)
    leakage_rows = build_leakage_rows(candidate_rows, plan_rows, input_rows)
    gate_rows = build_readiness_gate_rows(
        m57_coverage,
        candidate_rows,
        plan_rows,
        new_candidate_rows,
        new_plan_rows,
        preservation_rows,
        episode_recovery_rows,
        leakage_rows,
    )
    ready = all(row.get("status") == "pass" for row in gate_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(ready)
    command_rows = build_command_rows()
    unrecovered_episode_rows = [
        row for row in episode_recovery_rows if row.get("unrecovered_budget_surfacing_episode")
    ]

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m49_status": m49_coverage.get("status"),
        "m57_status": m57_coverage.get("status"),
        "candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "expected_candidate_rows": EXPECTED_TOTAL_CANDIDATE_ROWS,
        "expected_trajectory_execution_plan_rows": EXPECTED_TOTAL_PLAN_ROWS,
        "new_policy_id": M58_POLICY,
        "new_policy_plan_rows": len(new_plan_rows),
        "new_policy_candidate_rows": len(new_candidate_rows),
        "policy_count": len({row.get("policy_id") for row in plan_rows}),
        "m49_preservation_audit_rows": len(preservation_rows),
        "m49_preservation_pass_rows": sum(1 for row in preservation_rows if row.get("preservation_pass")),
        "tail_slot_policy_audit_rows": len(tail_slot_audit_rows),
        "source_gap_recovery_audit_rows": len(source_gap_audit_rows),
        "source_gap_episode_recovery_rows": len(episode_recovery_rows),
        "unrecovered_source_gap_episode_rows": len(unrecovered_episode_rows),
        "unrecovered_source_gap_recovered_episode_rows": sum(
            1 for row in unrecovered_episode_rows if row.get("unrecovered_episode_recovered_by_m58")
        ),
        "unrecovered_source_gap_context_rows": sum(int(row.get("task_context_rows") or 0) for row in unrecovered_episode_rows),
        "unrecovered_source_gap_recovered_context_rows": sum(
            int(row.get("m58_recovered_context_rows") or 0) for row in unrecovered_episode_rows
        ),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_pass") for row in leakage_rows),
        "budget_cap_compliance_pass": all(row.get("budget_cap_compliance_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "readiness_gate_pass_rows": sum(1 for row in gate_rows if row.get("status") == "pass"),
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M58 source-gap high-path tail-slot policy materialization",
        "launch_long_job_now": False,
        "requires_docker_now": False,
        "m59_requires_docker": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "high_path_tail_candidate_rows.jsonl", new_candidate_rows)
    write_jsonl(ARTIFACT_DIR / "high_path_tail_execution_plan_rows.jsonl", new_plan_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_summary_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "m49_order_preservation_audit_rows.jsonl", preservation_rows)
    write_jsonl(ARTIFACT_DIR / "tail_slot_policy_audit_rows.jsonl", tail_slot_audit_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_recovery_audit_rows.jsonl", source_gap_audit_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_episode_recovery_rows.jsonl", episode_recovery_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m59_command_rows.jsonl", command_rows)
    write_report(coverage, policy_rows, tail_slot_audit_rows, episode_recovery_rows, gate_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(DATA_OUT_DIR / "high_path_tail_candidate_rows.jsonl", new_candidate_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
