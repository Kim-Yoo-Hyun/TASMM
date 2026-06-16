#!/usr/bin/env python3
"""Materialize E008-M44 source-diverse redesign rows for the next trajectory smoke."""

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
VERSION = "e008_m44_source_diverse_redesign_row_materialization_smoke_v0"
READY_STATUS = "e008_m44_source_diverse_redesign_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m44_source_diverse_redesign_row_materialization_smoke_blocked"

M36_DIR = EXP_ROOT / "artifacts" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
M40_DIR = EXP_ROOT / "artifacts" / "E008-M40_budget_matched_repair_row_materialization_smoke_v0"
M43_DIR = EXP_ROOT / "artifacts" / "E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M44_source_diverse_redesign_row_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M44_source_diverse_redesign_row_materialization_smoke_v0"

NEXT_UNIT = "E008-M45 source-diverse redesign trajectory execution contract and Docker preflight"
SELECTED_ROUTE = "source_diverse_current_candidate_pool_rerank_v1"
PRIMARY_BUDGET = 5
SOURCE_DIVERSITY_RADIUS_M = 1.0
LOW_DEAD_END_COST_M = 1.5

STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_BUDGET5_POLICY = "detector_confidence_budget5_v0"
FIXED_TOPK_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_DIVERSE_POLICY = "source_diverse_current_observation_budget5_v1"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
H001_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"

MATERIALIZED_POLICIES = [
    STATIC_POLICY,
    DETECTOR_BUDGET5_POLICY,
    FIXED_TOPK_POLICY,
    SOURCE_DIVERSE_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]

M36_STATIC_POLICY = "static_stale_memory_top1_v0"
M36_DETECTOR_FULL_POLICY = "detector_confidence_reachable_subset_v0"

POLICY_ROLES = {
    STATIC_POLICY: "naive_lower_bound",
    DETECTOR_BUDGET5_POLICY: "budget_matched_detector_baseline",
    FIXED_TOPK_POLICY: "budget_matched_fixed_current_baseline",
    SOURCE_DIVERSE_POLICY: "source_diversity_baseline",
    TASK_AGNOSTIC_POLICY: "task_context_ablation",
    H001_POLICY: "test_method_task_conditioned_source_diverse_memory_trust",
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
    "diagnostic_source_gap_boundary",
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


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    return [float(value) for value in vec]  # type: ignore[arg-type]


def dist_xz(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None:
        return None
    return float(math.sqrt((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2))


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def group_by_plan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def source_plan_uid(prefix: str, plan: dict[str, Any], policy_id: str) -> str:
    return f"{prefix}::{plan.get('adapter_episode_id')}::{plan.get('task_context_id')}::{policy_id}"


def m40_plan_uid(plan: dict[str, Any]) -> str:
    return source_plan_uid("m40", plan, str(plan.get("policy_id")))


def candidate_identity(row: dict[str, Any]) -> str:
    for key in ("proposal_uid", "candidate_visit_uid", "raw_candidate_uid", "overlay_candidate_uid"):
        value = row.get(key)
        if value:
            return str(value)
    return json.dumps(row.get("execution_stop_position_m") or row.get("candidate_position_m"), sort_keys=True)


def candidate_position(row: dict[str, Any]) -> list[float] | None:
    return as_vec3(row.get("execution_stop_position_m") or row.get("snapped_position_m") or row.get("candidate_stop_position_m"))


def diversity_key(row: dict[str, Any]) -> str:
    pos = candidate_position(row)
    if pos is None:
        spatial = "missing"
    else:
        spatial = f"{round(pos[0] / SOURCE_DIVERSITY_RADIUS_M)}:{round(pos[2] / SOURCE_DIVERSITY_RADIUS_M)}"
    return f"{row.get('frame_id')}::{spatial}"


def frame_index(row: dict[str, Any]) -> int:
    text = str(row.get("frame_id") or "")
    if "-" in text:
        text = text.rsplit("-", 1)[-1]
    try:
        return int(text)
    except ValueError:
        return 10**9


def detector_sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
    path_ready = bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))
    score = finite_float(row.get("ranking_score")) or finite_float(row.get("confidence")) or -1.0
    cost = finite_float(row.get("source_to_candidate_path_cost_m"))
    return (0 if path_ready else 1, -score, cost if cost is not None else float("inf"), candidate_identity(row))


def confidence_sorted(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=detector_sort_key)


def path_ready_current_candidates(plan: dict[str, Any], rows_by_plan: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    source_uid = source_plan_uid("m35", plan, M36_DETECTOR_FULL_POLICY)
    return confidence_sorted(
        [
            row
            for row in rows_by_plan.get(source_uid, [])
            if row.get("candidate_source_role") == "current_observation"
            and bool(row.get("path_ready"))
            and bool(row.get("candidate_usable_for_path_smoke", True))
        ]
    )


def stale_candidate(plan: dict[str, Any], rows_by_plan: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    source_uid = source_plan_uid("m35", plan, M36_STATIC_POLICY)
    rows = rows_by_plan.get(source_uid, [])
    return rows[0] if rows else None


def source_diverse_take(
    candidates: list[dict[str, Any]],
    slots: int,
    used_ids: set[str],
    used_frames: set[str],
    selected_positions: list[list[float]],
) -> list[tuple[dict[str, Any], str]]:
    selected: list[tuple[dict[str, Any], str]] = []
    if slots <= 0:
        return selected

    def can_take(row: dict[str, Any], require_frame_unique: bool, require_spatial_unique: bool) -> bool:
        if candidate_identity(row) in used_ids:
            return False
        frame = str(row.get("frame_id"))
        if require_frame_unique and frame in used_frames:
            return False
        pos = candidate_position(row)
        if require_spatial_unique and selected_positions:
            dists = [dist_xz(pos, existing) for existing in selected_positions]
            clean = [value for value in dists if value is not None]
            if clean and min(clean) < SOURCE_DIVERSITY_RADIUS_M:
                return False
        return True

    def take(row: dict[str, Any], component: str) -> None:
        used_ids.add(candidate_identity(row))
        used_frames.add(str(row.get("frame_id")))
        pos = candidate_position(row)
        if pos is not None:
            selected_positions.append(pos)
        selected.append((row, component))

    unique_frames = sorted({str(row.get("frame_id")) for row in candidates if row.get("frame_id")}, key=lambda item: frame_index({"frame_id": item}))
    if unique_frames and slots > 1:
        for slot_idx in range(slots):
            if len(selected) >= slots:
                return selected
            start = math.floor(slot_idx * len(unique_frames) / slots)
            end = math.floor((slot_idx + 1) * len(unique_frames) / slots)
            frame_band = set(unique_frames[start:end] or unique_frames[start : start + 1])
            band_rows = [row for row in candidates if str(row.get("frame_id")) in frame_band]
            for row in band_rows:
                if not can_take(row, require_frame_unique=True, require_spatial_unique=True):
                    continue
                take(row, f"source_diverse_current_frame_band_{slot_idx + 1:02d}_spatial")
                break

    passes = [
        (True, True, "source_diverse_current_unique_frame_spatial"),
        (True, False, "source_diverse_current_unique_frame"),
        (False, False, "source_diverse_current_budget_fill"),
    ]
    for require_frame_unique, require_spatial_unique, component in passes:
        for row in candidates:
            if len(selected) >= slots:
                return selected
            if not can_take(row, require_frame_unique, require_spatial_unique):
                continue
            take(row, component)
    return selected


def confidence_fill_take(
    candidates: list[dict[str, Any]],
    slots: int,
    used_ids: set[str],
    used_frames: set[str],
    selected_positions: list[list[float]],
    component: str,
) -> list[tuple[dict[str, Any], str]]:
    selected: list[tuple[dict[str, Any], str]] = []
    if slots <= 0:
        return selected
    for row in candidates:
        if len(selected) >= slots:
            break
        if candidate_identity(row) in used_ids:
            continue
        used_ids.add(candidate_identity(row))
        used_frames.add(str(row.get("frame_id")))
        pos = candidate_position(row)
        if pos is not None:
            selected_positions.append(pos)
        selected.append((row, component))
    return selected


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
    plan_uid = str(plan.get("m44_plan_uid"))
    row = strip_blocked_fields(source)
    row.update(
        {
            "version": VERSION,
            "source_version": source.get("version"),
            "selected_route": SELECTED_ROUTE,
            "m44_plan_uid": plan_uid,
            "source_m36_policy_plan_uid": source_policy_plan_uid,
            "source_candidate_visit_uid": source.get("candidate_visit_uid"),
            "source_candidate_identity": candidate_identity(source),
            "benchmark_row_uid": plan.get("benchmark_row_uid"),
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
            "source_diversity_key": diversity_key(source),
            "source_expansion_route": plan.get("source_expansion_route") or "none",
            "diagnostic_source_gap_boundary_for_reporting": bool(
                plan.get("diagnostic_source_gap_boundary_for_reporting")
            ),
            "use_diagnostic_source_gap_boundary_for_policy": False,
            "uses_task_context_for_decision": bool(plan.get("uses_task_context_for_decision")),
            "primary_budget_cap": int(plan.get("primary_budget_cap") or PRIMARY_BUDGET),
            "policy_input_allowed": True,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "diagnostic_not_policy_input": True,
            "claim_boundary": "M44 materializes source-diverse redesign trajectory input rows; no trajectory result is produced.",
        }
    )
    if "candidate_source_role" not in row:
        row["candidate_source_role"] = row.get("source_role")
    if "source_role" not in row:
        row["source_role"] = row.get("candidate_source_role")
    return row


def materialize_baseline_from_m40(
    plan: dict[str, Any],
    m40_rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    source_uid = m40_plan_uid(plan)
    source_rows = m40_rows_by_plan.get(source_uid, [])
    cap = int(plan.get("primary_budget_cap") or PRIMARY_BUDGET)
    return [
        clone_candidate(row, plan, rank, "m40_budget_matched_replay", source_uid)
        for rank, row in enumerate(source_rows[:cap], start=1)
    ]


def h001_slot_plan(task_context_id: str, stale_low_dead_end: bool) -> tuple[int, int, bool, str]:
    if task_context_id in {"high_value_fetch", "noisy_high_value_fetch"}:
        return 4, 1, False, "high_value_stale_suppressed"
    if task_context_id == "routine_fetch" and stale_low_dead_end:
        return 3, 1, True, "routine_low_dead_end_stale_allowed"
    if task_context_id == "routine_fetch":
        return 3, 2, False, "routine_stale_suppressed_confidence_fill"
    return 4, 1, False, "default_task_context_source_diverse"


def materialize_source_diverse(
    plan: dict[str, Any],
    m36_rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    policy_id = str(plan.get("policy_id"))
    current = path_ready_current_candidates(plan, m36_rows_by_plan)
    stale = stale_candidate(plan, m36_rows_by_plan)
    source_uid = source_plan_uid("m35", plan, M36_DETECTOR_FULL_POLICY)

    selected: list[tuple[dict[str, Any], str]] = []
    used_ids: set[str] = set()
    used_frames: set[str] = set()
    selected_positions: list[list[float]] = []
    stale_cost = finite_float(stale.get("source_to_candidate_path_cost_m")) if stale else None
    stale_low_dead_end = stale_cost is not None and stale_cost <= LOW_DEAD_END_COST_M

    if policy_id == SOURCE_DIVERSE_POLICY:
        selected.extend(source_diverse_take(current, PRIMARY_BUDGET, used_ids, used_frames, selected_positions))
    elif policy_id == TASK_AGNOSTIC_POLICY:
        selected.extend(source_diverse_take(current, 4, used_ids, used_frames, selected_positions))
        selected.extend(
            confidence_fill_take(
                current,
                PRIMARY_BUDGET - len(selected),
                used_ids,
                used_frames,
                selected_positions,
                "task_agnostic_confidence_fill",
            )
        )
    elif policy_id == H001_POLICY:
        diversity_slots, confidence_slots, use_stale, component_prefix = h001_slot_plan(
            str(plan.get("task_context_id")),
            stale_low_dead_end,
        )
        if use_stale and stale is not None:
            selected.append((stale, f"h001_{component_prefix}"))
            used_ids.add(candidate_identity(stale))
            used_frames.add(str(stale.get("frame_id")))
            pos = candidate_position(stale)
            if pos is not None:
                selected_positions.append(pos)
        selected.extend(source_diverse_take(current, diversity_slots, used_ids, used_frames, selected_positions))
        selected.extend(
            confidence_fill_take(
                current,
                confidence_slots,
                used_ids,
                used_frames,
                selected_positions,
                f"h001_{component_prefix}_confidence_fill",
            )
        )
        selected.extend(
            confidence_fill_take(
                current,
                PRIMARY_BUDGET - len(selected),
                used_ids,
                used_frames,
                selected_positions,
                f"h001_{component_prefix}_budget_fill",
            )
        )
    else:
        raise ValueError(f"unsupported source-diverse policy: {policy_id}")

    return [
        clone_candidate(row, plan, rank, component, source_uid)
        for rank, (row, component) in enumerate(selected[:PRIMARY_BUDGET], start=1)
    ]


def materialize_plan_candidates(
    plan: dict[str, Any],
    m36_rows_by_plan: dict[str, list[dict[str, Any]]],
    m40_rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    policy_id = str(plan.get("policy_id"))
    if policy_id in {STATIC_POLICY, DETECTOR_BUDGET5_POLICY, FIXED_TOPK_POLICY}:
        return materialize_baseline_from_m40(plan, m40_rows_by_plan)
    return materialize_source_diverse(plan, m36_rows_by_plan)


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
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
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
                "m44_plan_uid": plan_uid,
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
                "primary_budget_cap": cap,
                "candidate_budget": cap,
                "candidate_visit_order_contract": "source_diverse_redesign_v1",
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
                "diagnostic_source_gap_boundary_for_reporting": bool(
                    first.get("diagnostic_source_gap_boundary_for_reporting")
                ),
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
                "claim_boundary": "M44 materializes source-diverse execution plans; no trajectory metric has been computed yet.",
            }
        )
    return out


def build_policy_summary_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                "source_ready_plan_rows": sum(
                    1 for row in rows if not row.get("diagnostic_source_gap_boundary_for_reporting")
                ),
                "source_gap_plan_rows": sum(
                    1 for row in rows if row.get("diagnostic_source_gap_boundary_for_reporting")
                ),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "mean_candidate_rows": mean([finite_float(row.get("candidate_rows")) for row in rows]),
                "mean_unique_frame_ids": mean([finite_float(row.get("unique_frame_ids")) for row in rows]),
                "stale_first_plan_rows": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first_plan_rows": sum(1 for row in rows if row.get("current_observation_first")),
                "mean_old_location_dead_end_cost_proxy_m": mean(
                    [finite_float(row.get("old_location_dead_end_cost_proxy_m")) for row in rows]
                ),
                "runner_input_ready_rows": sum(1 for row in rows if row.get("runner_input_ready")),
                "claim_boundary": "M44 summary is pre-execution materialization only.",
            }
        )
    return out


def build_candidate_pool_summary_rows(
    plan_rows: list[dict[str, Any]],
    m36_rows_by_plan: dict[str, list[dict[str, Any]]],
    m40_rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    by_scan_task: dict[tuple[str, str], dict[str, Any]] = {}
    for plan in plan_rows:
        key = (str(plan.get("adapter_episode_id")), str(plan.get("task_context_id")))
        if key in by_scan_task:
            continue
        full_candidates = path_ready_current_candidates(plan, m36_rows_by_plan)
        stale = stale_candidate(plan, m36_rows_by_plan)
        m40_detector_rows = m40_rows_by_plan.get(source_plan_uid("m40", plan, DETECTOR_BUDGET5_POLICY), [])
        by_scan_task[key] = {
            "version": VERSION,
            "adapter_episode_id": plan.get("adapter_episode_id"),
            "scan_id": plan.get("scan_id"),
            "scene_key": plan.get("scene_key"),
            "object_category": plan.get("object_category"),
            "task_context_id": plan.get("task_context_id"),
            "diagnostic_source_gap_boundary_for_reporting": bool(
                plan.get("diagnostic_source_gap_boundary_for_reporting")
            ),
            "m36_full_current_candidate_rows": len(full_candidates),
            "m36_full_current_unique_frame_ids": len({str(row.get("frame_id")) for row in full_candidates}),
            "m36_full_current_unique_diversity_keys": len({diversity_key(row) for row in full_candidates}),
            "m40_detector_budget5_rows": len(m40_detector_rows),
            "stale_candidate_ready": stale is not None,
            "stale_old_memory_path_cost_m": finite_float(stale.get("source_to_candidate_path_cost_m")) if stale else None,
            "claim_boundary": "Candidate-pool counts are policy-visible source diagnostics, not eval success labels.",
        }
    return [by_scan_task[key] for key in sorted(by_scan_task)]


def build_source_diversity_audit_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in plan_rows:
        candidate_rows = int(row.get("candidate_rows") or 0)
        out.append(
            {
                "version": VERSION,
                "m44_plan_uid": row.get("m44_plan_uid"),
                "policy_id": row.get("policy_id"),
                "task_context_id": row.get("task_context_id"),
                "candidate_rows": candidate_rows,
                "primary_budget_cap": row.get("primary_budget_cap"),
                "unique_frame_ids": row.get("unique_frame_ids"),
                "unique_source_diversity_keys": row.get("unique_source_diversity_keys"),
                "duplicate_frame_rows": row.get("duplicate_frame_rows"),
                "current_observation_candidate_rows": row.get("current_observation_candidate_rows"),
                "stale_old_memory_candidate_rows": row.get("stale_old_memory_candidate_rows"),
                "source_role_counts": row.get("source_role_counts"),
                "budget_cap_compliance_pass": candidate_rows <= int(row.get("primary_budget_cap") or PRIMARY_BUDGET),
                "runner_input_ready": row.get("runner_input_ready"),
                "uses_task_context_for_decision": row.get("uses_task_context_for_decision"),
            }
        )
    return out


def build_policy_distinctness_audit_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        key = (str(row.get("adapter_episode_id")), str(row.get("task_context_id")), str(row.get("policy_id")))
        grouped[key].append(row)

    out: list[dict[str, Any]] = []
    scan_task_keys = sorted({(key[0], key[1]) for key in grouped})
    compared_policies = [
        FIXED_TOPK_POLICY,
        SOURCE_DIVERSE_POLICY,
        TASK_AGNOSTIC_POLICY,
        H001_POLICY,
    ]
    for adapter_episode_id, task_context_id in scan_task_keys:
        detector_rows = sorted(
            grouped.get((adapter_episode_id, task_context_id, DETECTOR_BUDGET5_POLICY), []),
            key=lambda row: int(row.get("visit_rank") or 10**9),
        )
        detector_ids = [str(row.get("source_candidate_identity")) for row in detector_rows]
        detector_set = set(detector_ids)
        for policy_id in compared_policies:
            rows = sorted(
                grouped.get((adapter_episode_id, task_context_id, policy_id), []),
                key=lambda row: int(row.get("visit_rank") or 10**9),
            )
            ids = [str(row.get("source_candidate_identity")) for row in rows]
            row_set = set(ids)
            first = rows[0] if rows else {}
            out.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": adapter_episode_id,
                    "scan_id": first.get("scan_id"),
                    "scene_key": first.get("scene_key"),
                    "task_context_id": task_context_id,
                    "policy_id": policy_id,
                    "reference_policy_id": DETECTOR_BUDGET5_POLICY,
                    "candidate_rows": len(rows),
                    "same_order_as_detector": ids == detector_ids,
                    "same_set_as_detector": row_set == detector_set,
                    "candidate_set_overlap_count": len(row_set & detector_set),
                    "new_candidate_count_vs_detector": len(row_set - detector_set),
                    "diagnostic_source_gap_boundary_for_reporting": bool(
                        first.get("diagnostic_source_gap_boundary_for_reporting")
                    ),
                    "claim_boundary": "Policy distinctness is a pre-execution audit; it does not use eval success labels.",
                }
            )
    return out


def build_input_contract_rows(m43_input_guard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed_fields: list[str] = []
    for row in m43_input_guard_rows:
        if row.get("field_group") == "allowed_policy_inputs":
            allowed_fields = [str(field) for field in row.get("fields", [])]
            break
    for field in allowed_fields:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": True,
                "policy_use": "M44 source-diverse materialization and M45 trajectory execution.",
            }
        )
    for field in sorted(BLOCKED_POLICY_FIELDS):
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": False,
                "policy_use": "Metric or diagnostic-only after execution; never used for M44 policy ordering.",
            }
        )
    rows.append(
        {
            "version": VERSION,
            "field": "diagnostic_source_gap_boundary_for_reporting",
            "allowed_for_policy": False,
            "policy_use": "Stored only to split analysis after execution; not used to rank candidates.",
        }
    )
    return rows


def build_leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for payload_name, rows in [
        ("source_diverse_redesign_candidate_rows", candidate_rows),
        ("source_diverse_redesign_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        over_budget_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
            if payload_name.endswith("candidate_rows"):
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
                "blocked_flag_hit_count": flag_hits,
                "over_budget_candidate_hits": over_budget_hits,
                "leakage_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
                "budget_cap_compliance_pass": over_budget_hits == 0,
            }
        )
    return out


def build_readiness_gate_rows(
    m44_plan_rows: list[dict[str, Any]],
    execution_plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_rows = 18 * len(MATERIALIZED_POLICIES)
    return [
        {
            "version": VERSION,
            "gate_id": "m43_plan_rows_preserved",
            "status": "pass" if len(m44_plan_rows) == expected_rows else "fail",
            "evidence": f"M43 M44 plan rows={len(m44_plan_rows)}; expected={expected_rows}.",
        },
        {
            "version": VERSION,
            "gate_id": "execution_plan_rows_materialized",
            "status": "pass" if len(execution_plan_rows) == expected_rows else "fail",
            "evidence": f"execution plan rows={len(execution_plan_rows)}; expected={expected_rows}.",
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
            "status": "pass" if all(row.get("runner_input_ready") for row in execution_plan_rows) else "fail",
            "evidence": (
                f"runner-ready plan rows={sum(1 for row in execution_plan_rows if row.get('runner_input_ready'))}"
                f"/{len(execution_plan_rows)}."
            ),
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
            "claim_id": "source_diverse_redesign_rows_materialized",
            "status": "supported_materialization_only",
            "claim_boundary": "M44 supports leakage-safe row materialization for source-diverse redesign policies.",
        },
        {
            "version": VERSION,
            "claim_id": "source_diverse_navigation_improvement",
            "status": "not_ready",
            "claim_boundary": "No navigation improvement can be claimed until M45 executes these rows in Docker Habitat.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "claim_boundary": "M44 does not execute trajectories and does not support final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "claim_boundary": "Structured task context is a memory-trust/re-observation condition, not natural-language intent understanding.",
        },
    ]


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "execute_source_diverse_trajectory_preflight" if ready else "repair_m44_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M44 source-diverse row materialization",
            "launch_long_job_now": False,
            "requires_docker": True,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_m45_command_rows() -> list[dict[str, Any]]:
    command = (
        'docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp '
        '-v /home/yoohyun/research2/local_dataset/data:/data:ro '
        '-v /home/yoohyun/research2:/work -w /work '
        'research2/habitat-h001:20260508-calib-artifacts '
        'bash -lc "micromamba run -n base python '
        'experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py '
        '--m36-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M44_source_diverse_redesign_row_materialization_smoke_v0 '
        '--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_execution_smoke_v0 '
        '--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M45_source_diverse_redesign_trajectory_execution_smoke_v0"'
    )
    return [
        {
            "version": VERSION,
            "command_id": "m45_docker_runner_command",
            "working_directory": str(ROOT),
            "command": command,
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_execution_smoke_v0/coverage.json",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M45_source_diverse_redesign_trajectory_execution_smoke_v0/dynamic_stale_trajectory_policy_metric_rows.jsonl",
            ],
            "verification_command": "python - <<'PY' ... assert coverage status and scan_task_policy_rows ... PY",
            "launch_now": False,
            "claim_boundary": "M45 command is recorded for the next Docker step; M44 does not launch it.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    distinctness_rows: list[dict[str, Any]],
) -> str:
    source_gap_pool_rows = [row for row in pool_rows if row.get("diagnostic_source_gap_boundary_for_reporting")]
    distinctness_summary: list[dict[str, Any]] = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in distinctness_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for policy_id, rows in sorted(by_policy.items()):
        distinctness_summary.append(
            {
                "policy_id": policy_id,
                "audit_rows": len(rows),
                "same_order_rows": sum(1 for row in rows if row.get("same_order_as_detector")),
                "same_set_rows": sum(1 for row in rows if row.get("same_set_as_detector")),
                "mean_new_candidate_count_vs_detector": mean(
                    [finite_float(row.get("new_candidate_count_vs_detector")) for row in rows]
                ),
            }
        )
    return "\n".join(
        [
            "# E008-M44 Source-Diverse Redesign Row Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M43 materialization plan rows: {coverage['m43_m44_plan_rows']}.",
            f"- Execution plan rows: {coverage['source_diverse_execution_plan_rows']}.",
            f"- Candidate rows: {coverage['source_diverse_candidate_rows']}.",
            f"- Source-ready/source-gap plan rows: {coverage['source_ready_plan_rows']} / {coverage['source_gap_plan_rows']}.",
            f"- Policy input leakage pass: {coverage['policy_input_leakage_pass']}.",
            f"- Budget cap compliance pass: {coverage['budget_cap_compliance_pass']}.",
            f"- M45 runner input ready: {coverage['m45_runner_input_ready']}.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                summary_rows,
                [
                    "policy_id",
                    "policy_plan_rows",
                    "candidate_rows",
                    "source_ready_plan_rows",
                    "source_gap_plan_rows",
                    "mean_candidate_rows",
                    "mean_unique_frame_ids",
                    "current_first_plan_rows",
                    "stale_first_plan_rows",
                ],
            ),
            "",
            "## Candidate Pool Summary",
            "",
            markdown_table(
                source_gap_pool_rows[:6],
                [
                    "scan_id",
                    "task_context_id",
                    "m36_full_current_candidate_rows",
                    "m36_full_current_unique_frame_ids",
                    "m40_detector_budget5_rows",
                    "stale_old_memory_path_cost_m",
                ],
            ),
            "",
            "## Policy Distinctness Audit",
            "",
            markdown_table(
                distinctness_summary,
                [
                    "policy_id",
                    "audit_rows",
                    "same_order_rows",
                    "same_set_rows",
                    "mean_new_candidate_count_vs_detector",
                ],
            ),
            "",
            "## Leakage Audit",
            "",
            markdown_table(
                leakage_rows,
                [
                    "payload",
                    "row_count",
                    "blocked_field_hit_count",
                    "blocked_flag_hit_count",
                    "over_budget_candidate_hits",
                    "leakage_pass",
                    "budget_cap_compliance_pass",
                ],
            ),
            "",
            "## 논문 주장",
            "",
            "- M44 can only claim that source-diverse redesign rows are materialized under the same top-5 budget without policy leakage.",
            "- M44 cannot claim navigation improvement, final real navigation `SR` / `SPL`, or final real RGB-D/open-vocabulary robustness.",
            "",
            "## 에이전트 추론",
            "",
            "- M43 diagnosed that confidence top-5 drops recoverable source-gap candidates; M44 therefore tests visit-order redesign, not a new detector or extra observation budget.",
            "- Keeping detector-confidence, fixed top-k, source-diverse, task-agnostic, and H001 rows in the same materialization package preserves the ablation ladder required by the novelty contract.",
            "",
            "## 사용자 판단 필요",
            "",
            "- M45 should execute these rows in Docker before any broader scale-up decision.",
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
    m40_cov = read_json(M40_DIR / "coverage.json")
    m43_cov = read_json(M43_DIR / "coverage.json")
    m44_plan_rows = read_jsonl(M43_DIR / "m44_materialization_plan_rows.jsonl")
    m43_input_guard_rows = read_jsonl(M43_DIR / "input_guard_rows.jsonl")
    m36_candidate_rows = read_jsonl(M36_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    m40_candidate_rows = read_jsonl(M40_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")

    if not m36_cov or not m40_cov or not m43_cov or not m44_plan_rows or not m36_candidate_rows or not m40_candidate_rows:
        raise SystemExit("missing required M36/M40/M43 input artifacts")

    m36_rows_by_plan = group_by_plan(m36_candidate_rows)
    m40_rows_by_plan = group_by_plan(m40_candidate_rows)

    candidate_rows: list[dict[str, Any]] = []
    for plan in m44_plan_rows:
        candidate_rows.extend(materialize_plan_candidates(plan, m36_rows_by_plan, m40_rows_by_plan))

    execution_plan_rows = build_execution_plan_rows(candidate_rows)
    summary_rows = build_policy_summary_rows(execution_plan_rows)
    pool_rows = build_candidate_pool_summary_rows(m44_plan_rows, m36_rows_by_plan, m40_rows_by_plan)
    diversity_rows = build_source_diversity_audit_rows(execution_plan_rows)
    distinctness_rows = build_policy_distinctness_audit_rows(candidate_rows)
    input_contract_rows = build_input_contract_rows(m43_input_guard_rows)
    leakage_rows = build_leakage_rows(candidate_rows, execution_plan_rows)
    readiness_rows = build_readiness_gate_rows(m44_plan_rows, execution_plan_rows, candidate_rows, leakage_rows)
    claim_rows = build_claim_boundary_rows()

    policy_ids = sorted({str(row.get("policy_id")) for row in execution_plan_rows})
    expected_plan_rows = 18 * len(MATERIALIZED_POLICIES)
    leakage_pass = all(row.get("leakage_pass") for row in leakage_rows)
    budget_pass = all(row.get("budget_cap_compliance_pass") for row in leakage_rows)
    runner_ready = all(row.get("runner_input_ready") for row in execution_plan_rows)
    ready = (
        len(m44_plan_rows) == expected_plan_rows
        and len(execution_plan_rows) == expected_plan_rows
        and len(policy_ids) == len(MATERIALIZED_POLICIES)
        and bool(candidate_rows)
        and leakage_pass
        and budget_pass
        and runner_ready
    )

    route_rows = build_route_rows(ready)
    command_rows = build_m45_command_rows()
    source_ready_plan_rows = sum(1 for row in execution_plan_rows if not row.get("diagnostic_source_gap_boundary_for_reporting"))
    source_gap_plan_rows = sum(1 for row in execution_plan_rows if row.get("diagnostic_source_gap_boundary_for_reporting"))

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m36_status": m36_cov.get("status"),
        "m40_status": m40_cov.get("status"),
        "m43_status": m43_cov.get("status"),
        "m43_m44_plan_rows": len(m44_plan_rows),
        "source_diverse_execution_plan_rows": len(execution_plan_rows),
        "trajectory_execution_plan_rows": len(execution_plan_rows),
        "source_diverse_candidate_rows": len(candidate_rows),
        "trajectory_candidate_rows": len(candidate_rows),
        "policy_count": len(policy_ids),
        "policy_ids": policy_ids,
        "intervention_rows": len({(row.get("adapter_episode_id"), row.get("task_context_id")) for row in execution_plan_rows}),
        "source_ready_plan_rows": source_ready_plan_rows,
        "source_gap_plan_rows": source_gap_plan_rows,
        "source_ready_scan_task_rows": len(
            {
                (row.get("adapter_episode_id"), row.get("task_context_id"))
                for row in execution_plan_rows
                if not row.get("diagnostic_source_gap_boundary_for_reporting")
            }
        ),
        "source_gap_scan_task_rows": len(
            {
                (row.get("adapter_episode_id"), row.get("task_context_id"))
                for row in execution_plan_rows
                if row.get("diagnostic_source_gap_boundary_for_reporting")
            }
        ),
        "candidate_pool_summary_rows": len(pool_rows),
        "policy_materialization_summary_rows": len(summary_rows),
        "source_diversity_audit_rows": len(diversity_rows),
        "policy_distinctness_audit_rows": len(distinctness_rows),
        "leakage_audit_rows": len(leakage_rows),
        "readiness_gate_rows": len(readiness_rows),
        "policy_input_leakage_pass": leakage_pass,
        "budget_cap_compliance_pass": budget_pass,
        "runner_input_ready": runner_ready,
        "m45_runner_input_ready": ready,
        "trajectory_execution_launched": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_diverse_redesign_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "source_diverse_redesign_execution_plan_rows.jsonl", execution_plan_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", execution_plan_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_summary_rows.jsonl", summary_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_pool_summary_rows.jsonl", pool_rows)
    write_jsonl(ARTIFACT_DIR / "source_diversity_audit_rows.jsonl", diversity_rows)
    write_jsonl(ARTIFACT_DIR / "policy_distinctness_audit_rows.jsonl", distinctness_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_contract_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m45_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, summary_rows, pool_rows, leakage_rows, distinctness_rows),
        encoding="utf-8",
    )

    copy_core_outputs(
        ARTIFACT_DIR,
        DATA_OUT_DIR,
        [
            "coverage.json",
            "source_diverse_redesign_candidate_rows.jsonl",
            "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
            "source_diverse_redesign_execution_plan_rows.jsonl",
            "trajectory_execution_plan_rows.jsonl",
            "input_contract_rows.jsonl",
            "m45_command_rows.jsonl",
        ],
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
