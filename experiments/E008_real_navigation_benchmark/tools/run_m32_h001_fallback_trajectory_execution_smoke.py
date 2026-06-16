#!/usr/bin/env python3
"""Execute E008-M31 H001 fallback visit orders as a Habitat trajectory smoke."""

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
VERSION = "e008_m32_h001_fallback_trajectory_execution_smoke_v0"

DEFAULT_M31_CONTRACT = EXP_ROOT / "artifacts" / "E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M30_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M30_h001_current_observation_fallback_replay_smoke_v0"

HOST_RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
POLICY_ID = "h001_current_observation_backstop_top5_v0"


def data_root() -> Path:
    if DOCKER_DATA_ROOT.exists():
        return DOCKER_DATA_ROOT
    return HOST_RESEARCH2_DATA_ROOT


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


def valid_vec3(vec: object) -> bool:
    if not isinstance(vec, list) or len(vec) != 3:
        return False
    return all(finite_float(value) is not None for value in vec)


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


def group_plan_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(plan_rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, plan_rows in grouped.items()
    }


def source_gap_index(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(str(row.get("adapter_episode_id")), str(row.get("task_context_id"))) for row in rows}


def scene_for_group(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        scene_path = row.get("scene_docker_path")
        if scene_path:
            return str(scene_path)
    return ""


def execute_policy_plan(
    sim: Any,
    policy_plan_uid: str,
    rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
    m30_index: dict[str, dict[str, Any]],
    source_gap_keys: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    first = rows[0]
    adapter_episode_id = str(first.get("adapter_episode_id"))
    task_context_id = str(first.get("task_context_id"))
    eval_goal = eval_index.get(adapter_episode_id, {})
    oracle = oracle_index.get(adapter_episode_id, {})
    m30 = m30_index.get(policy_plan_uid, {})
    current = as_vec3(eval_goal.get("start_position"))
    attempt_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    cumulative_path = 0.0
    candidate_visits = 0
    executed_stops = 0
    success = False
    stop_rank: int | None = None
    success_attempt: dict[str, Any] | None = None

    for row in rows:
        rank = int(row.get("visit_rank") or len(attempt_rows) + 1)
        proposal_uid = str(row.get("proposal_uid"))
        path_ready = bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))
        candidate_pos = as_vec3(row.get("execution_stop_position_m") or row.get("snapped_position_m") or row.get("candidate_stop_position_m"))
        counted_visit = True
        attempt_status = "not_started"
        path_found = False
        segment_m = None
        path_point_count = 0
        path_error = ""
        stop_position = None
        eval_result: dict[str, Any] = eval_stop(None, eval_goal)

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
                current = candidate_pos
                stop_position = candidate_pos
                executed_stops += 1
                eval_result = eval_stop(stop_position, eval_goal)
                attempt_status = "executed_success" if eval_result["primary_eval_hit"] else "executed_no_success"
            else:
                attempt_status = "path_not_found"

        if counted_visit:
            candidate_visits += 1

        attempt = {
            "version": VERSION,
            "policy_id": POLICY_ID,
            "policy_plan_uid": policy_plan_uid,
            "scan_id": first.get("scan_id"),
            "adapter_episode_id": adapter_episode_id,
            "scene_key": first.get("scene_key"),
            "object_category": first.get("object_category"),
            "task_context_id": task_context_id,
            "visit_rank": rank,
            "proposal_uid": proposal_uid,
            "raw_candidate_uid": row.get("raw_candidate_uid"),
            "candidate_visit_uid": row.get("candidate_visit_uid"),
            "source_role": row.get("source_role"),
            "repair_replay_segment": row.get("repair_replay_segment"),
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
            "counted_as_candidate_visit": counted_visit,
            "navmesh_validation_status": row.get("navmesh_validation_status"),
            "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
            "ranking_cost_m": row.get("ranking_cost_m"),
            "m31_source_gap_boundary": (adapter_episode_id, task_context_id) in source_gap_keys,
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
                    "policy_id": POLICY_ID,
                    "policy_plan_uid": policy_plan_uid,
                    "scan_id": first.get("scan_id"),
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
                "policy_id": POLICY_ID,
                "policy_plan_uid": policy_plan_uid,
                "scan_id": first.get("scan_id"),
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
        "policy_id": POLICY_ID,
        "policy_plan_uid": policy_plan_uid,
        "scan_id": first.get("scan_id"),
        "adapter_episode_id": adapter_episode_id,
        "scene_key": first.get("scene_key"),
        "object_category": first.get("object_category"),
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
        "success_source_role": success_attempt.get("source_role") if success_attempt else None,
        "success_candidate_to_nearest_eval_viewpoint_xz_m": success_attempt.get("candidate_to_nearest_eval_viewpoint_xz_m") if success_attempt else None,
        "success_candidate_to_eval_goal_xz_m": success_attempt.get("candidate_to_eval_goal_xz_m") if success_attempt else None,
        "m30_primary_hit": m30.get("primary_hit"),
        "m30_primary_first_hit_rank": m30.get("primary_first_hit_rank"),
        "m30_primary_first_hit_cost_m": m30.get("primary_first_hit_cost_m"),
        "m30_primary_spl_proxy": m30.get("primary_spl_proxy"),
        "m30_candidate_rows": m30.get("candidate_rows"),
        "m31_source_gap_boundary": (adapter_episode_id, task_context_id) in source_gap_keys,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "claim_boundary": "trajectory_smoke_metric_not_final_navigation_claim",
    }
    return attempt_rows, metric, failure_rows


def classify_plan_failure(attempt_rows: list[dict[str, Any]]) -> str:
    statuses = Counter(str(row.get("attempt_status")) for row in attempt_rows)
    if statuses.get("executed_no_success"):
        return "no_eval_success_after_executed_stops"
    if statuses.get("path_not_found"):
        return "path_not_found_before_success"
    if statuses.get("blocked_candidate_unusable"):
        return "all_candidates_blocked_or_unusable"
    return "budget_exhausted_no_eval_success"


def aggregate_metric_rows(scan_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metrics:
        by_policy[str(row["policy_id"])].append(row)
        by_task_context[str(row["task_context_id"])].append(row)
    for policy_id, rows in sorted(by_policy.items()):
        out.append(build_aggregate_row("policy_aggregate", policy_id, rows))
    for task_context_id, rows in sorted(by_task_context.items()):
        out.append(build_aggregate_row("task_context_aggregate", task_context_id, rows))
    source_gap_rows = [row for row in scan_metrics if row.get("m31_source_gap_boundary")]
    non_source_gap_rows = [row for row in scan_metrics if not row.get("m31_source_gap_boundary")]
    out.append(build_aggregate_row("source_gap_aggregate", "source_gap_boundary_true", source_gap_rows))
    out.append(build_aggregate_row("source_gap_aggregate", "source_gap_boundary_false", non_source_gap_rows))
    return out


def build_aggregate_row(scope: str, group_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row.get("trajectory_success")]
    return {
        "version": VERSION,
        "metric_scope": scope,
        "group_id": group_id,
        "policy_id": POLICY_ID,
        "scan_task_policy_rows": len(rows),
        "success_rows": len(successes),
        "SR": safe_ratio(len(successes), len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "ExecutedStops_mean": mean([finite_float(row.get("ExecutedStops")) for row in rows]),
        "StopRank_mean_over_success": mean([finite_float(row.get("StopRank")) for row in successes]),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "claim_boundary": "trajectory_smoke_aggregate_not_final_navigation_claim",
    }


def build_proxy_delta_rows(scan_metric_rows: list[dict[str, Any]], m30_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for metric in sorted(scan_metric_rows, key=lambda row: str(row.get("policy_plan_uid"))):
        policy_plan_uid = str(metric.get("policy_plan_uid"))
        proxy = m30_index.get(policy_plan_uid, {})
        proxy_hit = bool(proxy.get("primary_hit"))
        trajectory_hit = bool(metric.get("trajectory_success"))
        proxy_spl = finite_float(proxy.get("primary_spl_proxy"))
        trajectory_spl = finite_float(metric.get("SPL"))
        rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": policy_plan_uid,
                "adapter_episode_id": metric.get("adapter_episode_id"),
                "scan_id": metric.get("scan_id"),
                "scene_key": metric.get("scene_key"),
                "object_category": metric.get("object_category"),
                "task_context_id": metric.get("task_context_id"),
                "m30_proxy_primary_hit": proxy_hit,
                "trajectory_success": trajectory_hit,
                "success_agreement": proxy_hit == trajectory_hit,
                "m30_proxy_first_hit_rank": proxy.get("primary_first_hit_rank"),
                "trajectory_stop_rank": metric.get("StopRank"),
                "m30_proxy_spl": proxy_spl,
                "trajectory_spl": trajectory_spl,
                "trajectory_minus_proxy_spl": (trajectory_spl - proxy_spl) if trajectory_spl is not None and proxy_spl is not None else None,
                "m31_source_gap_boundary": metric.get("m31_source_gap_boundary"),
            }
        )
    return rows


def build_source_gap_outcome_rows(
    source_gap_rows: list[dict[str, Any]],
    scan_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_index = {
        (str(row.get("adapter_episode_id")), str(row.get("task_context_id"))): row
        for row in scan_metric_rows
    }
    out = []
    for row in source_gap_rows:
        key = (str(row.get("adapter_episode_id")), str(row.get("task_context_id")))
        metric = metric_index.get(key, {})
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "m31_transition_type": row.get("transition_type"),
                "m28_failure_type": row.get("m28_failure_type"),
                "trajectory_success": metric.get("trajectory_success", False),
                "SR": metric.get("SR", 0.0),
                "SPL": metric.get("SPL", 0.0),
                "PathLengthM": metric.get("PathLengthM"),
                "CandidateVisits": metric.get("CandidateVisits"),
                "FailureType": metric.get("FailureType", "missing_metric_row"),
                "diagnostic_uses_eval_goal_or_viewpoint": True,
                "policy_input_uses_eval_goal_or_viewpoint": False,
            }
        )
    return out


def build_leakage_audit_rows(
    m31_contract_dir: Path,
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    input_keys = set()
    for row in candidate_rows + plan_rows:
        input_keys.update(row.keys())
    blocked_rows = read_jsonl(m31_contract_dir / "blocked_input_rows.jsonl")
    rows = []
    for blocked in blocked_rows:
        field = str(blocked.get("field"))
        observed = field in input_keys
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": False,
                "observed_in_policy_input": observed,
                "leakage_audit_pass": not observed,
                "reason": blocked.get("reason"),
            }
        )
    flag_hits = any(
        bool(row.get("policy_input_uses_eval_goal_or_viewpoint")) or bool(row.get("policy_input_uses_failure_label"))
        for row in candidate_rows + plan_rows
    )
    rows.append(
        {
            "version": VERSION,
            "field": "policy_input_eval_or_failure_flags",
            "allowed_for_policy": False,
            "observed_in_policy_input": flag_hits,
            "leakage_audit_pass": not flag_hits,
            "reason": "M31 policy inputs must not carry eval-goal or failure-label usage flags set to true.",
        }
    )
    return rows


def execute_all(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    m30_metric_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    oracle_index = {str(row.get("adapter_episode_id")): row for row in oracle_rows}
    m30_index = {
        str(row.get("policy_plan_uid")): row
        for row in m30_metric_rows
        if row.get("metric_scope") == "scan_policy"
    }
    source_gap_keys = source_gap_index(source_gap_rows)
    plan_uid_set = {str(row.get("policy_plan_uid")) for row in plan_rows if row.get("execute_in_next_runner")}
    grouped = {
        key: rows
        for key, rows in group_plan_rows(candidate_rows).items()
        if key in plan_uid_set
    }
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
                rows = grouped[policy_plan_uid]
                attempts, metric, failures = execute_policy_plan(
                    sim,
                    policy_plan_uid,
                    rows,
                    eval_index,
                    oracle_index,
                    m30_index,
                    source_gap_keys,
                )
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


def build_claim_boundary_rows(ready: bool, scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_h001_fallback_trajectory_smoke",
            "supported": ready,
            "claim_boundary": "M32 executes all 18 H001 fallback episode-task rows in Habitat without eval-goal policy inputs.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M32 is a 6-episode smoke over HM3D ObjectNav transfer rows; final navigation claim still needs scale and baseline alignment.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_dynamic_stale_memory_navigation",
            "supported": False,
            "claim_boundary": "`initial_memory_proxy` is not true dynamic stale memory state injection in HM3D.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M32 executes existing M31 rows and does not expand real RGB-D/open-vocabulary robustness.",
        },
    ]


def build_route_decision_rows(ready: bool, coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_h001_fallback_trajectory_and_align_baselines" if ready else "repair_m32_runner",
            "reason": "H001 fallback trajectory smoke rows are ready; next step is to compare against detector trajectory rows and decide scale/baseline alignment."
            if ready
            else "H001 fallback trajectory execution did not produce a complete leakage-safe smoke artifact.",
            "selected_next_unit": coverage["selected_next_unit"],
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "real_navigation_sr_spl_smoke_ready": ready,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "human_intent_main_claim_ready": False,
        }
    ]


def format_value(value: object) -> str:
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
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join([header, sep] + body)


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    proxy_delta_rows: list[dict[str, Any]],
    source_gap_outcome_rows: list[dict[str, Any]],
) -> str:
    aggregate_table = markdown_table(
        aggregate_rows,
        [
            "metric_scope",
            "group_id",
            "success_rows",
            "scan_task_policy_rows",
            "SR",
            "SPL",
            "PathLengthM_mean",
            "CandidateVisits_mean",
        ],
    )
    proxy_table = markdown_table(
        [
            {
                "row_group": "all_rows",
                "success_agreement_rows": sum(1 for row in proxy_delta_rows if row.get("success_agreement")),
                "proxy_success_trajectory_failure_rows": sum(
                    1 for row in proxy_delta_rows if row.get("m30_proxy_primary_hit") and not row.get("trajectory_success")
                ),
                "proxy_failure_trajectory_success_rows": sum(
                    1 for row in proxy_delta_rows if not row.get("m30_proxy_primary_hit") and row.get("trajectory_success")
                ),
            }
        ],
        ["row_group", "success_agreement_rows", "proxy_success_trajectory_failure_rows", "proxy_failure_trajectory_success_rows"],
    )
    source_gap_table = markdown_table(
        source_gap_outcome_rows,
        ["adapter_episode_id", "task_context_id", "object_category", "trajectory_success", "SPL", "FailureType"],
    )
    return f"""# E008-M32 H001 Fallback Trajectory Execution Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Inside Docker: {coverage['inside_docker']}.
- Trajectory attempt rows: {coverage['trajectory_attempt_rows']}.
- Scan-task metric rows: {coverage['scan_task_metric_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- H001 fallback trajectory smoke ready: {coverage['h001_fallback_trajectory_smoke_ready']}.
- Trajectory success rows: {coverage['trajectory_success_rows']} / {coverage['scan_task_metric_rows']}.
- Trajectory `SR`: {format_value(coverage['trajectory_SR'])}.
- Trajectory `SPL`: {format_value(coverage['trajectory_SPL_mean'])}.
- Real navigation `SR` / `SPL` final ready: {coverage['real_navigation_sr_spl_ready']}.

## Aggregate Metrics

{aggregate_table}

## Proxy vs Trajectory

{proxy_table}

## Source-Gap Outcomes

{source_gap_table}

## Claim Boundary

- M32 is an H001 fallback trajectory smoke, not a final navigation benchmark.
- `ObjectNav` goal/viewpoints are used only after stops for metrics.
- The 9 source-gap rows remain post-hoc diagnostics.
- Final real navigation `SR` / `SPL` needs scale, baseline alignment, and search/navigation baselines.

## Agent Inference

The next step is E008-M33: interpret the M32 H001 trajectory result against M22 detector-policy trajectory rows and decide whether to scale, align baselines, or repair candidate sources before making any navigation claim.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m31-contract", default=str(DEFAULT_M31_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    m31_contract = resolve_path(args.m31_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m31_coverage = read_json(m31_contract / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    m31_candidate_rows = read_jsonl(m31_contract / "h001_fallback_candidate_visit_order_rows.jsonl")
    m31_plan_rows = read_jsonl(m31_contract / "trajectory_execution_plan_rows.jsonl")
    source_gap_rows = read_jsonl(m31_contract / "source_gap_boundary_rows.jsonl")
    m30_metric_rows = read_jsonl(M30_ARTIFACT_DIR / "fallback_replay_policy_goal_metric_rows.jsonl")

    if not m31_coverage:
        raise SystemExit("missing M31 coverage.json")
    if not goal_rows or not oracle_rows or not m31_candidate_rows or not m31_plan_rows or not m30_metric_rows:
        raise SystemExit("missing one or more E008 input artifacts for M32")

    eval_index = build_eval_goal_index(goal_rows)
    attempt_rows, metric_rows, failure_rows, scene_meta = execute_all(
        m31_candidate_rows,
        m31_plan_rows,
        eval_index,
        oracle_rows,
        m30_metric_rows,
        source_gap_rows,
    )
    leakage_audit_rows = build_leakage_audit_rows(m31_contract, m31_candidate_rows, m31_plan_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    scan_metric_rows = [row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]
    aggregate_rows = [row for row in metric_rows if row.get("metric_scope") != "scan_task_policy"]
    m30_index = {
        str(row.get("policy_plan_uid")): row
        for row in m30_metric_rows
        if row.get("metric_scope") == "scan_policy"
    }
    proxy_delta_rows = build_proxy_delta_rows(scan_metric_rows, m30_index)
    source_gap_outcome_rows = build_source_gap_outcome_rows(source_gap_rows, scan_metric_rows)

    trajectory_success_rows = sum(1 for row in scan_metric_rows if row.get("trajectory_success"))
    ready = (
        bool(attempt_rows)
        and len(scan_metric_rows) == 18
        and leakage_pass
        and len(scene_meta.get("scene_errors", [])) == 0
        and not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in attempt_rows + scan_metric_rows)
    )
    selected_next = (
        "E008-M33 H001 trajectory result interpretation and baseline alignment decision"
        if ready
        else "repair E008-M32 H001 fallback trajectory runner scaffold"
    )

    proxy_success_trajectory_failure_rows = sum(
        1 for row in proxy_delta_rows if row.get("m30_proxy_primary_hit") and not row.get("trajectory_success")
    )
    proxy_failure_trajectory_success_rows = sum(
        1 for row in proxy_delta_rows if not row.get("m30_proxy_primary_hit") and row.get("trajectory_success")
    )
    success_agreement_rows = sum(1 for row in proxy_delta_rows if row.get("success_agreement"))
    source_gap_trajectory_success_rows = sum(1 for row in source_gap_outcome_rows if row.get("trajectory_success"))

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m32_h001_fallback_trajectory_execution_smoke_ready"
        if ready
        else "e008_m32_h001_fallback_trajectory_execution_smoke_blocked",
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m31_status": m31_coverage.get("status"),
        "runtime_data_root": str(data_root()),
        "inside_docker": Path("/.dockerenv").exists() or os.environ.get("container") is not None,
        "m31_candidate_visit_rows": len(m31_candidate_rows),
        "m31_execution_plan_rows": len(m31_plan_rows),
        "trajectory_attempt_rows": len(attempt_rows),
        "scan_task_metric_rows": len(scan_metric_rows),
        "aggregate_metric_rows": len(aggregate_rows),
        "trajectory_failure_rows": len(failure_rows),
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "scene_count": scene_meta.get("scene_count"),
        "scene_error_rows": len(scene_meta.get("scene_errors", [])),
        "episode_count": len({row.get("adapter_episode_id") for row in scan_metric_rows}),
        "task_context_count": len({row.get("task_context_id") for row in scan_metric_rows}),
        "trajectory_success_rows": trajectory_success_rows,
        "trajectory_SR": safe_ratio(trajectory_success_rows, len(scan_metric_rows)),
        "trajectory_SPL_mean": mean([finite_float(row.get("SPL")) for row in scan_metric_rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in scan_metric_rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in scan_metric_rows]),
        "m30_proxy_success_rows": sum(1 for row in m30_index.values() if row.get("primary_hit")),
        "proxy_trajectory_success_agreement_rows": success_agreement_rows,
        "proxy_trajectory_success_agreement_rate": safe_ratio(success_agreement_rows, len(proxy_delta_rows)),
        "proxy_success_trajectory_failure_rows": proxy_success_trajectory_failure_rows,
        "proxy_failure_trajectory_success_rows": proxy_failure_trajectory_success_rows,
        "source_gap_boundary_rows": len(source_gap_rows),
        "source_gap_trajectory_success_rows": source_gap_trajectory_success_rows,
        "h001_fallback_trajectory_smoke_ready": ready,
        "real_navigation_sr_spl_smoke_ready": ready,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in attempt_rows + scan_metric_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    claim_boundary_rows = build_claim_boundary_rows(ready, scan_metric_rows)
    route_decision_rows = build_route_decision_rows(ready, coverage)

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "trajectory_attempt_rows.jsonl", attempt_rows)
        write_jsonl(output_dir / "trajectory_policy_metric_rows.jsonl", metric_rows)
        write_jsonl(output_dir / "trajectory_failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "proxy_trajectory_delta_rows.jsonl", proxy_delta_rows)
        write_jsonl(output_dir / "source_gap_outcome_rows.jsonl", source_gap_outcome_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_json(output_dir / "scene_execution_meta.json", scene_meta)
    (out_root / "report.md").write_text(build_report(coverage, aggregate_rows, proxy_delta_rows, source_gap_outcome_rows), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
