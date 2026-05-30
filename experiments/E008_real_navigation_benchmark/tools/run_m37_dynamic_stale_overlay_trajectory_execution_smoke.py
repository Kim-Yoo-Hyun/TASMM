#!/usr/bin/env python3
"""Execute E008-M36 dynamic-stale overlay rows as a Habitat trajectory smoke."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
READY_STATUS = "e008_m37_dynamic_stale_overlay_trajectory_execution_smoke_ready"
BLOCKED_STATUS = "e008_m37_dynamic_stale_overlay_trajectory_execution_smoke_blocked"

DEFAULT_M36_CONTRACT = EXP_ROOT / "artifacts" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"

HOST_RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
H001_POLICY = "h001_task_conditioned_memory_trust_navigation_v0"
BASELINE_POLICIES = [
    "static_stale_memory_top1_v0",
    "fixed_topk_current_observation_v0",
    "detector_confidence_reachable_subset_v0",
    "task_agnostic_memory_trust_navigation_v0",
]


def data_root() -> Path:
    if DOCKER_DATA_ROOT.exists():
        return DOCKER_DATA_ROOT
    return HOST_RESEARCH3_DATA_ROOT


def objectnav_content_root() -> Path:
    return (
        data_root()
        / "datasets"
        / "objectnav"
        / "hm3d"
        / "v2"
        / "objectnav_hm3d_v2"
        / "val_mini"
        / "content"
    )


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


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


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    return [float(value) for value in vec]  # type: ignore[arg-type]


def dist3(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def dist_xz(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[2]) - float(b[2])) ** 2))


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def load_goal_index() -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for content_file in sorted(objectnav_content_root().glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        goals_by_category = payload.get("goals_by_category", {})
        for key, goals in goals_by_category.items():
            if "_" not in key or not isinstance(goals, list):
                continue
            scene_file, category = key.split("_", 1)
            index[(scene_file, category)] = goals
    return index


def build_eval_goal_index(goal_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    goal_index = load_goal_index()
    out: dict[str, dict[str, Any]] = {}
    for row in goal_rows:
        scene_file = Path(str(row.get("scene_id_raw", ""))).name
        category = str(row.get("object_category", ""))
        goals = goal_index.get((scene_file, category), [])
        selected_goal = None
        closest_id = row.get("eval_goal_object_id")
        for goal in goals:
            if goal.get("object_id") == closest_id:
                selected_goal = goal
                break
        if selected_goal is None and goals:
            selected_goal = goals[0]
        all_viewpoint_positions = []
        if isinstance(selected_goal, dict):
            for viewpoint in selected_goal.get("view_points", []):
                agent_state = viewpoint.get("agent_state", {}) if isinstance(viewpoint, dict) else {}
                position = as_vec3(agent_state.get("position"))
                if position is not None:
                    all_viewpoint_positions.append(position)
        out[str(row["adapter_episode_id"])] = {
            **row,
            "eval_all_viewpoint_positions": all_viewpoint_positions,
            "eval_all_viewpoint_count_loaded": len(all_viewpoint_positions),
            "eval_goals_by_category_loaded": bool(goals),
            "eval_selected_goal_loaded": selected_goal is not None,
        }
    return out


def nearest_viewpoint_distances(candidate_pos: list[float] | None, viewpoints: list[list[float]]) -> tuple[float | None, float | None]:
    if not valid_vec3(candidate_pos) or not viewpoints:
        return None, None
    xz = [dist_xz(candidate_pos, viewpoint) for viewpoint in viewpoints]
    xyz = [dist3(candidate_pos, viewpoint) for viewpoint in viewpoints]
    clean_xz = [value for value in xz if value is not None]
    clean_xyz = [value for value in xyz if value is not None]
    return (min(clean_xz) if clean_xz else None, min(clean_xyz) if clean_xyz else None)


def hit(distance: float | None, threshold: float) -> bool:
    return distance is not None and distance <= threshold


def source_gap_for_reporting(row: dict[str, Any]) -> bool:
    return bool(row.get("diagnostic_source_gap_boundary") or row.get("diagnostic_source_gap_boundary_for_reporting"))


def find_path(sim: Any, start: list[float], end: list[float]) -> dict[str, Any]:
    import habitat_sim

    out = {"path_found": False, "geodesic_distance": None, "point_count": 0, "error": ""}
    try:
        path = habitat_sim.ShortestPath()
        path.requested_start = start
        path.requested_end = end
        found = bool(sim.pathfinder.find_path(path))
        out["path_found"] = found
        out["geodesic_distance"] = float(path.geodesic_distance) if found else None
        out["point_count"] = len(path.points) if found else 0
    except Exception as exc:  # pragma: no cover - docker runtime guard
        out["error"] = repr(exc)
    return out


def make_sim(scene_path: str) -> Any:
    import habitat_sim

    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = scene_path
    sim_cfg.scene_dataset_config_file = SCENE_DATASET_CONFIG
    return habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.AgentConfiguration()]))


def eval_stop(stop_position: list[float] | None, eval_goal: dict[str, Any]) -> dict[str, Any]:
    viewpoints = eval_goal.get("eval_all_viewpoint_positions", [])
    goal_pos = as_vec3(eval_goal.get("eval_goal_position"))
    first_viewpoint = as_vec3(eval_goal.get("eval_first_viewpoint_position"))
    nearest_vp_xz, nearest_vp_3d = nearest_viewpoint_distances(stop_position, viewpoints)
    goal_xz = dist_xz(stop_position, goal_pos)
    goal_3d = dist3(stop_position, goal_pos)
    first_vp_xz = dist_xz(stop_position, first_viewpoint)
    first_vp_3d = dist3(stop_position, first_viewpoint)
    return {
        "candidate_to_nearest_eval_viewpoint_xz_m": nearest_vp_xz,
        "candidate_to_nearest_eval_viewpoint_3d_m": nearest_vp_3d,
        "candidate_to_eval_goal_xz_m": goal_xz,
        "candidate_to_eval_goal_3d_m": goal_3d,
        "candidate_to_eval_first_viewpoint_xz_m": first_vp_xz,
        "candidate_to_eval_first_viewpoint_3d_m": first_vp_3d,
        "hit_any_viewpoint_xz_0p5": hit(nearest_vp_xz, 0.5),
        "hit_any_viewpoint_xz_1p0": hit(nearest_vp_xz, 1.0),
        "hit_any_viewpoint_xz_1p5": hit(nearest_vp_xz, 1.5),
        "hit_goal_xz_1p0": hit(goal_xz, 1.0),
        "hit_goal_xz_1p5": hit(goal_xz, 1.5),
        "primary_eval_metric": PRIMARY_METRIC,
        "primary_eval_hit": hit(nearest_vp_xz, 1.0),
    }


def group_candidate_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def classify_plan_failure(attempt_rows: list[dict[str, Any]]) -> str:
    statuses = Counter(str(row.get("attempt_status")) for row in attempt_rows)
    if statuses.get("executed_no_success"):
        return "no_eval_success_after_executed_stops"
    if statuses.get("path_not_found"):
        return "path_not_found_before_success"
    if statuses.get("blocked_candidate_unusable"):
        return "all_candidates_blocked_or_unusable"
    return "budget_exhausted_no_eval_success"


def scene_for_group(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        scene_path = row.get("scene_docker_path")
        if scene_path:
            return str(scene_path)
    return ""


def execute_policy_plan(
    sim: Any,
    plan: dict[str, Any],
    rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    first = rows[0]
    policy_plan_uid = str(plan.get("policy_plan_uid"))
    policy_id = str(plan.get("policy_id"))
    adapter_episode_id = str(plan.get("adapter_episode_id"))
    task_context_id = str(plan.get("task_context_id"))
    eval_goal = eval_index.get(adapter_episode_id, {})
    oracle = oracle_index.get(adapter_episode_id, {})
    current = as_vec3(eval_goal.get("start_position"))
    attempt_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    cumulative_path = 0.0
    candidate_visits = 0
    executed_stops = 0
    stale_executed_path_before_current = 0.0
    current_seen = False
    success = False
    stop_rank: int | None = None
    success_attempt: dict[str, Any] | None = None

    for row in rows:
        rank = int(row.get("visit_rank") or len(attempt_rows) + 1)
        proposal_uid = str(row.get("proposal_uid"))
        source_role = str(row.get("candidate_source_role"))
        path_ready = bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))
        candidate_pos = as_vec3(row.get("execution_stop_position_m") or row.get("snapped_position_m") or row.get("candidate_stop_position_m"))
        candidate_visits += 1
        attempt_status = "not_started"
        path_found = False
        segment_m = None
        path_point_count = 0
        path_error = ""
        stop_position = None
        eval_result: dict[str, Any] = eval_stop(None, eval_goal)

        if source_role == "current_observation":
            current_seen = True
        if current is None:
            attempt_status = "blocked_missing_start_position"
        elif not path_ready or candidate_pos is None:
            attempt_status = "blocked_candidate_unusable"
        else:
            path = find_path(sim, current, candidate_pos)
            path_found = bool(path.get("path_found"))
            segment_m = finite_float(path.get("geodesic_distance"))
            path_point_count = int(path.get("point_count") or 0)
            path_error = str(path.get("error") or "")
            if path_found and segment_m is not None:
                cumulative_path += segment_m
                if source_role == "stale_old_memory" and not current_seen:
                    stale_executed_path_before_current += segment_m
                current = candidate_pos
                stop_position = candidate_pos
                executed_stops += 1
                eval_result = eval_stop(stop_position, eval_goal)
                attempt_status = "executed_success" if eval_result["primary_eval_hit"] else "executed_no_success"
            else:
                attempt_status = "path_not_found"

        attempt = {
            "version": VERSION,
            "policy_id": policy_id,
            "policy_role": plan.get("policy_role"),
            "policy_plan_uid": policy_plan_uid,
            "benchmark_row_uid": plan.get("benchmark_row_uid"),
            "scan_id": plan.get("scan_id"),
            "adapter_episode_id": adapter_episode_id,
            "scene_key": plan.get("scene_key"),
            "object_category": plan.get("object_category"),
            "task_context_id": task_context_id,
            "visit_rank": rank,
            "proposal_uid": proposal_uid,
            "raw_candidate_uid": row.get("raw_candidate_uid"),
            "candidate_visit_uid": row.get("candidate_visit_uid"),
            "candidate_source_role": source_role,
            "dynamic_stale_overlay_role": row.get("dynamic_stale_overlay_role"),
            "candidate_order_component": row.get("candidate_order_component"),
            "label_canonical": row.get("label_canonical"),
            "attempt_status": attempt_status,
            "path_found": path_found,
            "segment_geodesic_m": segment_m,
            "path_point_count": path_point_count,
            "path_error": path_error,
            "cumulative_path_length_m": cumulative_path,
            "candidate_visits_so_far": candidate_visits,
            "executed_stops_so_far": executed_stops,
            "start_position_m": eval_goal.get("start_position"),
            "candidate_stop_position_m": candidate_pos,
            "stop_position_m": stop_position,
            "eval_success": bool(eval_result["primary_eval_hit"]),
            "eval_goal_xz_1p0_success": bool(eval_result["hit_goal_xz_1p0"]),
            "counted_as_candidate_visit": True,
            "navmesh_validation_status": row.get("navmesh_validation_status"),
            "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
            "m35_old_location_dead_end_cost_proxy_m": plan.get("old_location_dead_end_cost_proxy_m"),
            "diagnostic_source_gap_boundary": source_gap_for_reporting(plan),
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            **eval_result,
        }
        attempt_rows.append(attempt)

        if attempt_status in {"blocked_missing_start_position", "blocked_candidate_unusable", "path_not_found"}:
            failure_rows.append(
                {
                    "version": VERSION,
                    "failure_scope": "candidate_attempt",
                    "policy_id": policy_id,
                    "policy_plan_uid": policy_plan_uid,
                    "scan_id": plan.get("scan_id"),
                    "adapter_episode_id": adapter_episode_id,
                    "task_context_id": task_context_id,
                    "failure_type": attempt_status,
                    "proposal_uid": proposal_uid,
                    "visit_rank": rank,
                    "reason": path_error or str(row.get("navmesh_validation_status") or attempt_status),
                }
            )

        if eval_result["primary_eval_hit"]:
            success = True
            stop_rank = rank
            success_attempt = attempt
            break

    oracle_path_m = finite_float(oracle.get("viewpoint_path_geodesic_distance"))
    spl = 0.0
    if success and oracle_path_m is not None and oracle_path_m > 0:
        spl = float(oracle_path_m / max(oracle_path_m, cumulative_path))
    failure_type = "success" if success else classify_plan_failure(attempt_rows)
    if not success:
        failure_rows.append(
            {
                "version": VERSION,
                "failure_scope": "scan_task_policy",
                "policy_id": policy_id,
                "policy_plan_uid": policy_plan_uid,
                "scan_id": plan.get("scan_id"),
                "adapter_episode_id": adapter_episode_id,
                "task_context_id": task_context_id,
                "failure_type": failure_type,
                "proposal_uid": None,
                "visit_rank": None,
                "reason": "trajectory_exhausted_without_primary_eval_success",
            }
        )

    metric = {
        "version": VERSION,
        "metric_scope": "scan_task_policy",
        "policy_id": policy_id,
        "policy_role": plan.get("policy_role"),
        "policy_plan_uid": policy_plan_uid,
        "benchmark_row_uid": plan.get("benchmark_row_uid"),
        "scan_id": plan.get("scan_id"),
        "adapter_episode_id": adapter_episode_id,
        "scene_key": plan.get("scene_key"),
        "object_category": plan.get("object_category"),
        "task_context_id": task_context_id,
        "SR": 1.0 if success else 0.0,
        "SPL": spl,
        "PathLengthM": cumulative_path,
        "CandidateVisits": candidate_visits,
        "ExecutedStops": executed_stops,
        "StopRank": stop_rank,
        "FailureType": failure_type,
        "oracle_viewpoint_path_m": oracle_path_m,
        "trajectory_success": success,
        "success_proposal_uid": success_attempt.get("proposal_uid") if success_attempt else None,
        "success_source_role": success_attempt.get("candidate_source_role") if success_attempt else None,
        "success_dynamic_stale_overlay_role": success_attempt.get("dynamic_stale_overlay_role") if success_attempt else None,
        "success_candidate_to_nearest_eval_viewpoint_xz_m": success_attempt.get("candidate_to_nearest_eval_viewpoint_xz_m")
        if success_attempt
        else None,
        "success_candidate_to_eval_goal_xz_m": success_attempt.get("candidate_to_eval_goal_xz_m") if success_attempt else None,
        "stale_visit_first": bool(plan.get("stale_visit_first")),
        "current_observation_first": bool(plan.get("current_observation_first")),
        "stale_before_current_rows": plan.get("stale_before_current_rows"),
        "old_location_dead_end_cost_proxy_m": plan.get("old_location_dead_end_cost_proxy_m"),
        "OldLocationDeadEndCostM": stale_executed_path_before_current,
        "diagnostic_source_gap_boundary": source_gap_for_reporting(plan),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "claim_boundary": "dynamic_stale_overlay_trajectory_smoke_metric_not_final_navigation_claim",
    }
    return attempt_rows, metric, failure_rows


def build_aggregate_row(scope: str, group_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row.get("trajectory_success")]
    return {
        "version": VERSION,
        "metric_scope": scope,
        "group_id": group_id,
        "scan_task_policy_rows": len(rows),
        "success_rows": len(successes),
        "SR": safe_ratio(len(successes), len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "ExecutedStops_mean": mean([finite_float(row.get("ExecutedStops")) for row in rows]),
        "StopRank_mean_over_success": mean([finite_float(row.get("StopRank")) for row in successes]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "claim_boundary": "trajectory_smoke_aggregate_not_final_navigation_claim",
    }


def aggregate_metric_rows(scan_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source_gap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metrics:
        by_policy[str(row["policy_id"])].append(row)
        by_task_context[str(row["task_context_id"])].append(row)
        by_source_gap[str(bool(row.get("diagnostic_source_gap_boundary"))).lower()].append(row)
    for policy_id, rows in sorted(by_policy.items()):
        aggregate = build_aggregate_row("policy_aggregate", policy_id, rows)
        aggregate["policy_id"] = policy_id
        out.append(aggregate)
    for task_context_id, rows in sorted(by_task_context.items()):
        out.append(build_aggregate_row("task_context_aggregate", task_context_id, rows))
    for source_gap_id, rows in sorted(by_source_gap.items()):
        out.append(build_aggregate_row("source_gap_aggregate", f"source_gap_{source_gap_id}", rows))
    return out


def build_pairwise_delta_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_benchmark: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_metric_rows:
        by_benchmark[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row
    out = []
    for benchmark_uid, policy_rows in sorted(by_benchmark.items()):
        h001 = policy_rows.get(H001_POLICY)
        if not h001:
            continue
        for baseline_id in BASELINE_POLICIES:
            baseline = policy_rows.get(baseline_id)
            if not baseline:
                continue
            out.append(
                {
                    "version": VERSION,
                    "benchmark_row_uid": benchmark_uid,
                    "adapter_episode_id": h001.get("adapter_episode_id"),
                    "scan_id": h001.get("scan_id"),
                    "object_category": h001.get("object_category"),
                    "task_context_id": h001.get("task_context_id"),
                    "method_policy_id": H001_POLICY,
                    "baseline_policy_id": baseline_id,
                    "method_SR": h001.get("SR"),
                    "baseline_SR": baseline.get("SR"),
                    "delta_SR": (finite_float(h001.get("SR")) or 0.0) - (finite_float(baseline.get("SR")) or 0.0),
                    "method_SPL": h001.get("SPL"),
                    "baseline_SPL": baseline.get("SPL"),
                    "delta_SPL": (finite_float(h001.get("SPL")) or 0.0) - (finite_float(baseline.get("SPL")) or 0.0),
                    "method_PathLengthM": h001.get("PathLengthM"),
                    "baseline_PathLengthM": baseline.get("PathLengthM"),
                    "delta_PathLengthM": (finite_float(h001.get("PathLengthM")) or 0.0)
                    - (finite_float(baseline.get("PathLengthM")) or 0.0),
                    "method_CandidateVisits": h001.get("CandidateVisits"),
                    "baseline_CandidateVisits": baseline.get("CandidateVisits"),
                    "method_OldLocationDeadEndCostM": h001.get("OldLocationDeadEndCostM"),
                    "baseline_OldLocationDeadEndCostM": baseline.get("OldLocationDeadEndCostM"),
                    "diagnostic_source_gap_boundary": bool(h001.get("diagnostic_source_gap_boundary")),
                    "claim_boundary": "pairwise delta over M37 smoke rows only; not final navigation claim",
                }
            )
    return out


def build_old_location_outcome_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": row.get("policy_id"),
            "policy_plan_uid": row.get("policy_plan_uid"),
            "benchmark_row_uid": row.get("benchmark_row_uid"),
            "adapter_episode_id": row.get("adapter_episode_id"),
            "task_context_id": row.get("task_context_id"),
            "stale_visit_first": row.get("stale_visit_first"),
            "old_location_dead_end_cost_proxy_m": row.get("old_location_dead_end_cost_proxy_m"),
            "OldLocationDeadEndCostM": row.get("OldLocationDeadEndCostM"),
            "trajectory_success": row.get("trajectory_success"),
            "success_source_role": row.get("success_source_role"),
            "FailureType": row.get("FailureType"),
        }
        for row in scan_metric_rows
        if row.get("stale_visit_first") or row.get("old_location_dead_end_cost_proxy_m")
    ]


def build_leakage_audit_rows(contract_dir: Path, candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contract_rows = read_jsonl(contract_dir / "input_contract_rows.jsonl")
    blocked_fields = {str(row.get("field")) for row in contract_rows if row.get("allowed_for_policy") is False}
    out = []
    for payload, rows in [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in blocked_fields:
                if field in row:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def execute_all(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    oracle_index = {str(row.get("adapter_episode_id")): row for row in oracle_rows}
    plan_index = {str(row.get("policy_plan_uid")): row for row in plan_rows if row.get("execute_in_next_runner")}
    grouped = {key: rows for key, rows in group_candidate_rows(candidate_rows).items() if key in plan_index}
    scene_groups: dict[str, list[str]] = defaultdict(list)
    for policy_plan_uid, rows in grouped.items():
        scene_groups[scene_for_group(rows)].append(policy_plan_uid)

    attempt_rows: list[dict[str, Any]] = []
    scan_metric_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    scene_meta = {"scene_count": len(scene_groups), "scene_errors": []}

    for scene_path, plan_uids in sorted(scene_groups.items()):
        if not scene_path:
            scene_meta["scene_errors"].append({"scene_path": scene_path, "error": "missing_scene_path"})
            continue
        sim = None
        try:
            sim = make_sim(scene_path)
            for policy_plan_uid in sorted(plan_uids):
                plan = plan_index[policy_plan_uid]
                rows = grouped[policy_plan_uid]
                attempts, metric, failures = execute_policy_plan(sim, plan, rows, eval_index, oracle_index)
                attempt_rows.extend(attempts)
                scan_metric_rows.append(metric)
                failure_rows.extend(failures)
        except Exception as exc:  # pragma: no cover - docker runtime guard
            scene_meta["scene_errors"].append({"scene_path": scene_path, "error": repr(exc)})
        finally:
            if sim is not None:
                sim.close()

    aggregate_rows = aggregate_metric_rows(scan_metric_rows)
    return attempt_rows, scan_metric_rows + aggregate_rows, failure_rows, scene_meta


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_overlay_trajectory_smoke",
            "supported": ready,
            "claim_boundary": "M37 executes the M35/M36 counterfactual stale overlay rows in Habitat as a smoke test.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M37 is still a 6-episode smoke; final navigation claim requires scale and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "true_temporal_dynamic_navigation",
            "supported": False,
            "claim_boundary": "The HM3D overlay is counterfactual, not true temporal object movement.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context remains a condition/ablation, not a natural-language human-intent claim.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_dynamic_stale_overlay_navigation_result" if ready else "repair_m37_runner",
            "selected_next_unit": "E008-M38 dynamic-stale overlay result interpretation and baseline alignment"
            if ready
            else "repair E008-M37 dynamic-stale overlay trajectory execution smoke",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "dynamic_stale_navigation_result_ready": ready,
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
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> str:
    policy_rows = [row for row in aggregate_rows if row.get("metric_scope") == "policy_aggregate"]
    pairwise_summary: list[dict[str, Any]] = []
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_baseline[str(row.get("baseline_policy_id"))].append(row)
    for baseline_id, rows in sorted(by_baseline.items()):
        pairwise_summary.append(
            {
                "baseline_policy_id": baseline_id,
                "rows": len(rows),
                "delta_SR_mean": mean([finite_float(row.get("delta_SR")) for row in rows]),
                "delta_SPL_mean": mean([finite_float(row.get("delta_SPL")) for row in rows]),
                "delta_PathLengthM_mean": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
            }
        )
    return "\n".join(
        [
            "# E008-M37 Dynamic-Stale Overlay Trajectory Execution Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Inside Docker: {coverage['inside_docker']}.",
            f"- Trajectory attempt rows: {coverage['trajectory_attempt_rows']}.",
            f"- Scan-task-policy metric rows: {coverage['scan_task_policy_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Dynamic-stale overlay trajectory smoke ready: {coverage['dynamic_stale_overlay_trajectory_smoke_ready']}.",
            f"- Final real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.",
            "",
            "## Policy Aggregates",
            "",
            markdown_table(policy_rows, ["group_id", "success_rows", "scan_task_policy_rows", "SR", "SPL", "PathLengthM_mean", "OldLocationDeadEndCostM_mean"]),
            "",
            "## H001 Pairwise Delta Summary",
            "",
            markdown_table(pairwise_summary, ["baseline_policy_id", "rows", "delta_SR_mean", "delta_SPL_mean", "delta_PathLengthM_mean"]),
            "",
            "## Claim Boundary",
            "",
            "- M37 is a dynamic-stale overlay trajectory smoke, not a final navigation benchmark.",
            "- `ObjectNav` goal/viewpoints are used only after stops for metric computation.",
            "- The HM3D overlay is counterfactual and must not be described as true temporal dynamic object motion.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m36-contract", default=str(DEFAULT_M36_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    m36_contract = resolve_path(args.m36_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m36_cov = read_json(m36_contract / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    candidate_rows = read_jsonl(m36_contract / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(m36_contract / "trajectory_execution_plan_rows.jsonl")

    if not m36_cov:
        raise SystemExit("missing M36 coverage.json")
    if not goal_rows or not oracle_rows or not candidate_rows or not plan_rows:
        raise SystemExit("missing one or more E008 input artifacts for M37")

    eval_index = build_eval_goal_index(goal_rows)
    attempt_rows, metric_rows, failure_rows, scene_meta = execute_all(candidate_rows, plan_rows, eval_index, oracle_rows)
    scan_metric_rows = [row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]
    aggregate_rows = [row for row in metric_rows if row.get("metric_scope") != "scan_task_policy"]
    pairwise_rows = build_pairwise_delta_rows(scan_metric_rows)
    old_location_rows = build_old_location_outcome_rows(scan_metric_rows)
    leakage_rows = build_leakage_audit_rows(m36_contract, candidate_rows, plan_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_rows)

    success_rows = sum(1 for row in scan_metric_rows if row.get("trajectory_success"))
    ready = (
        len(scan_metric_rows) == 90
        and bool(attempt_rows)
        and leakage_pass
        and len(scene_meta.get("scene_errors", [])) == 0
        and not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in attempt_rows + scan_metric_rows)
    )
    claim_rows = build_claim_boundary_rows(ready)
    route_rows = build_route_decision_rows(ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m36_status": m36_cov.get("status"),
        "runtime_data_root": str(data_root()),
        "inside_docker": Path("/.dockerenv").exists() or os.environ.get("container") is not None,
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "trajectory_attempt_rows": len(attempt_rows),
        "scan_task_policy_rows": len(scan_metric_rows),
        "aggregate_metric_rows": len(aggregate_rows),
        "trajectory_failure_rows": len(failure_rows),
        "pairwise_policy_delta_rows": len(pairwise_rows),
        "old_location_outcome_rows": len(old_location_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": leakage_pass,
        "scene_count": scene_meta.get("scene_count"),
        "scene_error_rows": len(scene_meta.get("scene_errors", [])),
        "policy_count": len({row.get("policy_id") for row in scan_metric_rows}),
        "intervention_rows": len({row.get("benchmark_row_uid") for row in scan_metric_rows}),
        "trajectory_success_rows": success_rows,
        "trajectory_SR": safe_ratio(success_rows, len(scan_metric_rows)),
        "trajectory_SPL_mean": mean([finite_float(row.get("SPL")) for row in scan_metric_rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in scan_metric_rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in scan_metric_rows]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in scan_metric_rows]),
        "dynamic_stale_overlay_trajectory_smoke_ready": ready,
        "dynamic_stale_navigation_result_ready": ready,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in attempt_rows + scan_metric_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "dynamic_stale_trajectory_attempt_rows.jsonl", attempt_rows)
        write_jsonl(output_dir / "dynamic_stale_trajectory_policy_metric_rows.jsonl", metric_rows)
        write_jsonl(output_dir / "dynamic_stale_trajectory_failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "pairwise_policy_delta_rows.jsonl", pairwise_rows)
        write_jsonl(output_dir / "old_location_dead_end_outcome_rows.jsonl", old_location_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_json(output_dir / "scene_execution_meta.json", scene_meta)
    (out_root / "report.md").write_text(build_report(coverage, aggregate_rows, pairwise_rows), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
