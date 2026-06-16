#!/usr/bin/env python3
"""Execute E008-M21 detector-policy visit orders as a small Habitat trajectory smoke."""

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
VERSION = "e008_m22_expanded_detector_policy_trajectory_execution_smoke_v0"

DEFAULT_M21_CONTRACT = EXP_ROOT / "artifacts" / "E008-M21_expanded_detector_policy_trajectory_execution_contract_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M19_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"

HOST_RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"


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


def policy_counts_blocked(policy_id: str) -> bool:
    return policy_id == "detector_confidence_all_candidates_v0"


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


def group_visit_rows(visit_rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in visit_rows:
        grouped[(str(row.get("policy_id")), str(row.get("scan_id")))].append(row)
    return {
        key: sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, rows in grouped.items()
    }


def scene_for_group(rows: list[dict[str, Any]], candidate_index: dict[str, dict[str, Any]]) -> str:
    for row in rows:
        candidate = candidate_index.get(str(row.get("proposal_uid")), {})
        scene_path = candidate.get("scene_docker_path")
        if scene_path:
            return str(scene_path)
    return ""


def execute_policy_scan(
    sim: Any,
    policy_id: str,
    scan_id: str,
    rows: list[dict[str, Any]],
    candidate_index: dict[str, dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
    m19_index: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    first = rows[0]
    adapter_episode_id = str(first.get("adapter_episode_id"))
    eval_goal = eval_index.get(adapter_episode_id, {})
    oracle = oracle_index.get(adapter_episode_id, {})
    m19 = m19_index.get((policy_id, scan_id), {})
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
        candidate = candidate_index.get(proposal_uid, {})
        path_ready = bool(row.get("path_ready")) and bool(candidate.get("candidate_usable_for_path_smoke"))
        candidate_pos = as_vec3(candidate.get("snapped_position_m"))
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
            if policy_counts_blocked(policy_id):
                attempt_status = "blocked_candidate_counted"
                counted_visit = True
            else:
                attempt_status = "blocked_candidate_skipped"
                counted_visit = False
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
            "policy_id": policy_id,
            "scan_id": scan_id,
            "adapter_episode_id": adapter_episode_id,
            "scene_key": first.get("scene_key"),
            "object_category": first.get("object_category"),
            "visit_rank": rank,
            "proposal_uid": proposal_uid,
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
            "candidate_snapped_position_m": candidate_pos,
            "stop_position_m": stop_position,
            "eval_success": bool(eval_result["primary_eval_hit"]),
            "eval_goal_xz_1p0_success": bool(eval_result["hit_goal_xz_1p0"]),
            "counted_as_candidate_visit": counted_visit,
            "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
            "navmesh_validation_status": row.get("navmesh_validation_status"),
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            **eval_result,
        }
        attempt_rows.append(attempt)

        if attempt_status in {"blocked_missing_start_position", "blocked_candidate_counted", "path_not_found"}:
            failure_rows.append(
                {
                    "version": VERSION,
                    "failure_scope": "candidate_attempt",
                    "policy_id": policy_id,
                    "scan_id": scan_id,
                    "adapter_episode_id": adapter_episode_id,
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
    failure_type = "success" if success else classify_scan_failure(attempt_rows)
    if not success:
        failure_rows.append(
            {
                "version": VERSION,
                "failure_scope": "scan_policy",
                "policy_id": policy_id,
                "scan_id": scan_id,
                "adapter_episode_id": adapter_episode_id,
                "failure_type": failure_type,
                "proposal_uid": None,
                "visit_rank": None,
                "reason": "trajectory_exhausted_without_primary_eval_success",
            }
        )

    metric = {
        "version": VERSION,
        "metric_scope": "scan_policy",
        "policy_id": policy_id,
        "scan_id": scan_id,
        "adapter_episode_id": adapter_episode_id,
        "scene_key": first.get("scene_key"),
        "object_category": first.get("object_category"),
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
        "success_candidate_to_nearest_eval_viewpoint_xz_m": success_attempt.get("candidate_to_nearest_eval_viewpoint_xz_m") if success_attempt else None,
        "success_candidate_to_eval_goal_xz_m": success_attempt.get("candidate_to_eval_goal_xz_m") if success_attempt else None,
        "m19_primary_hit": m19.get("primary_hit"),
        "m19_primary_first_hit_rank": m19.get("primary_first_hit_rank"),
        "m19_primary_first_hit_cost_m": m19.get("primary_first_hit_cost_m"),
        "m19_primary_spl_proxy": m19.get("primary_spl_proxy"),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "claim_boundary": "trajectory_smoke_metric_not_final_h001_navigation_claim",
    }
    return attempt_rows, metric, failure_rows


def classify_scan_failure(attempt_rows: list[dict[str, Any]]) -> str:
    statuses = Counter(str(row.get("attempt_status")) for row in attempt_rows)
    if statuses.get("executed_no_success"):
        return "no_eval_success_after_executed_stops"
    if statuses.get("path_not_found"):
        return "path_not_found_before_success"
    if statuses.get("blocked_candidate_counted") and not statuses.get("executed_no_success"):
        return "all_candidates_blocked_or_unreachable"
    return "budget_exhausted_no_eval_success"


def aggregate_policy_metrics(scan_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metrics:
        by_policy[str(row["policy_id"])].append(row)
    aggregates = []
    for policy_id, rows in sorted(by_policy.items()):
        successes = [row for row in rows if row.get("trajectory_success")]
        aggregates.append(
            {
                "version": VERSION,
                "metric_scope": "policy_aggregate",
                "policy_id": policy_id,
                "scan_policy_rows": len(rows),
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
                "claim_boundary": "trajectory_smoke_metric_not_final_h001_navigation_claim",
            }
        )
    return aggregates


def build_leakage_audit_rows(
    m21_contract_dir: Path,
    visit_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    input_keys = set()
    for row in visit_rows:
        input_keys.update(row.keys())
    for row in candidate_rows:
        input_keys.update(key for key in row.keys() if not key.startswith("candidate_to_eval"))
    blocked_rows = read_jsonl(m21_contract_dir / "blocked_eval_field_rows.jsonl")
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
    rows.append(
        {
            "version": VERSION,
            "field": "uses_objectnav_eval_goal_or_viewpoint_for_policy",
            "allowed_for_policy": False,
            "observed_in_policy_input": any(
                bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint"))
                for row in visit_rows
            ),
            "leakage_audit_pass": not any(
                bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint"))
                for row in visit_rows
            ),
            "reason": "ObjectNav eval goal/viewpoint flags must stay false in policy visit rows.",
        }
    )
    return rows


def execute_all(
    visit_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    m19_metric_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidate_index = {str(row.get("proposal_uid")): row for row in candidate_rows}
    oracle_index = {str(row.get("adapter_episode_id")): row for row in oracle_rows}
    m19_index = {
        (str(row.get("policy_id")), str(row.get("scan_id"))): row
        for row in m19_metric_rows
        if row.get("metric_scope") == "scan_policy"
    }
    grouped = group_visit_rows(visit_rows)
    scene_groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key, rows in grouped.items():
        scene_groups[scene_for_group(rows, candidate_index)].append(key)

    attempt_rows: list[dict[str, Any]] = []
    scan_metric_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    scene_meta = {"scene_count": len(scene_groups), "scene_errors": []}

    for scene_path, keys in sorted(scene_groups.items()):
        if not scene_path:
            scene_meta["scene_errors"].append({"scene_path": scene_path, "error": "missing_scene_path"})
            continue
        sim = None
        try:
            sim = make_sim(scene_path)
            for policy_id, scan_id in sorted(keys):
                rows = grouped[(policy_id, scan_id)]
                attempts, metric, failures = execute_policy_scan(
                    sim,
                    policy_id,
                    scan_id,
                    rows,
                    candidate_index,
                    eval_index,
                    oracle_index,
                    m19_index,
                )
                attempt_rows.extend(attempts)
                scan_metric_rows.append(metric)
                failure_rows.extend(failures)
        except Exception as exc:  # pragma: no cover - docker runtime guard
            scene_meta["scene_errors"].append({"scene_path": scene_path, "error": repr(exc)})
        finally:
            if sim is not None:
                sim.close()

    aggregate_rows = aggregate_policy_metrics(scan_metric_rows)
    return attempt_rows, scan_metric_rows + aggregate_rows, failure_rows, scene_meta


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join([header, sep] + body)


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


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]]) -> str:
    table = markdown_table(
        aggregate_rows,
        [
            "policy_id",
            "success_rows",
            "scan_policy_rows",
            "SR",
            "SPL",
            "PathLengthM_mean",
            "CandidateVisits_mean",
            "ExecutedStops_mean",
            "StopRank_mean_over_success",
        ],
    )
    return f"""# E008-M22 Expanded Detector-Policy Trajectory Execution Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Trajectory execution rows: {coverage['trajectory_execution_rows']}.
- Scan-policy metric rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy metric rows: {coverage['aggregate_policy_metric_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Real navigation `SR` / `SPL` smoke rows ready: {coverage['real_navigation_sr_spl_smoke_ready']}.
- Final real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.
- H001 navigation policy execution ready: {coverage['h001_navigation_policy_execution_ready']}.

## Aggregate Metrics

{table}

## Claim Boundary

- E008-M22 executes detector-policy candidate orders in `Habitat`, but it is still a 6-episode smoke set.
- The rows are trajectory `SR` / `SPL` smoke evidence for detector policies, not final H001 navigation evidence.
- `ObjectNav` goal/viewpoints are used only after each stop for metrics.
- H001 real navigation remains blocked until stale-memory/current-observation candidate-source rows are instantiated for `HM3D ObjectNav`.

## Agent Inference

This runner turns the M19 `GoalEvalProxy` into executed trajectory rows. The next defensible step is to compare M19 proxy metrics against M22 trajectory metrics and decide whether to instantiate H001 candidate sources or scale the detector-policy runner first.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m21-contract", default=str(DEFAULT_M21_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    m21_contract = resolve_path(args.m21_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m21_coverage = read_json(m21_contract / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    candidate_rows = read_jsonl(M17_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    visit_rows = read_jsonl(M18_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")
    m19_metric_rows = read_jsonl(M19_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")

    if not m21_coverage:
        raise SystemExit("missing M21 coverage.json")
    if not goal_rows or not oracle_rows or not candidate_rows or not visit_rows or not m19_metric_rows:
        raise SystemExit("missing one or more E008 input artifacts for M22")

    eval_index = build_eval_goal_index(goal_rows)
    attempt_rows, metric_rows, failure_rows, scene_meta = execute_all(
        visit_rows,
        candidate_rows,
        eval_index,
        oracle_rows,
        m19_metric_rows,
    )
    leakage_audit_rows = build_leakage_audit_rows(m21_contract, visit_rows, candidate_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    scan_metric_rows = [row for row in metric_rows if row.get("metric_scope") == "scan_policy"]
    aggregate_rows = [row for row in metric_rows if row.get("metric_scope") == "policy_aggregate"]
    success_counts = [int(row.get("success_rows") or 0) for row in aggregate_rows]
    ready = bool(attempt_rows) and len(scan_metric_rows) == 24 and len(aggregate_rows) == 4 and leakage_pass
    selected_next = (
        "E008-M23 trajectory-vs-proxy consistency and H001 candidate-source decision"
        if ready
        else "repair E008-M22 trajectory execution runner scaffold"
    )

    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "trajectory_execution_smoke_ready_h001_claim_blocked" if ready else "blocked",
            "reason": "Detector-policy trajectory rows and leakage-audited SR/SPL smoke metrics are ready; H001 candidate-source rows remain absent."
            if ready
            else "Trajectory execution rows or leakage audit are incomplete.",
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "real_navigation_sr_spl_smoke_ready": ready,
            "h001_navigation_policy_execution_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m22_expanded_detector_policy_trajectory_execution_smoke_ready_h001_blocked"
        if ready
        else "e008_m22_expanded_detector_policy_trajectory_execution_smoke_blocked",
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m21_status": m21_coverage.get("status"),
        "runtime_data_root": str(data_root()),
        "inside_docker": Path("/.dockerenv").exists() or os.environ.get("container") is not None,
        "candidate_visit_order_rows": len(visit_rows),
        "candidate_navmesh_rows": len(candidate_rows),
        "trajectory_execution_rows": len(attempt_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_metric_rows": len(aggregate_rows),
        "trajectory_failure_rows": len(failure_rows),
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "scene_count": scene_meta.get("scene_count"),
        "scene_error_rows": len(scene_meta.get("scene_errors", [])),
        "policy_count": len(aggregate_rows),
        "episode_rows": len(goal_rows),
        "success_count_min": min(success_counts) if success_counts else 0,
        "success_count_max": max(success_counts) if success_counts else 0,
        "real_navigation_sr_spl_smoke_ready": ready,
        "real_navigation_sr_spl_ready": False,
        "h001_candidate_source_rows_ready": 0,
        "h001_navigation_policy_execution_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in attempt_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "trajectory_attempt_rows.jsonl", attempt_rows)
        write_jsonl(output_dir / "trajectory_policy_metric_rows.jsonl", metric_rows)
        write_jsonl(output_dir / "trajectory_failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_json(output_dir / "scene_execution_meta.json", scene_meta)
    (out_root / "report.md").write_text(build_report(coverage, aggregate_rows), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
