#!/usr/bin/env python3
"""Build the M204 additive source-pool candidate-union trajectory contract."""

from __future__ import annotations

import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m204_additive_source_pool_candidate_union_docker_trajectory_contract_v0"
READY_STATUS = "e008_m204_additive_source_pool_candidate_union_docker_trajectory_contract_ready_runner_next"
NEEDS_RUNTIME_STATUS = "e008_m204_additive_source_pool_candidate_union_docker_trajectory_contract_ready_needs_runtime"
BLOCKED_STATUS = "e008_m204_additive_source_pool_candidate_union_docker_trajectory_contract_blocked"
NEXT_UNIT = "E008-M205 additive source-pool candidate-union Docker trajectory execution"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M204_additive_source_pool_candidate_union_docker_trajectory_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M204_additive_source_pool_candidate_union_docker_trajectory_contract_v0"
)

M64_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M68_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M195_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
M197_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
)
M201_DIR = EXP_ROOT / "artifacts" / "E008-M201_additive_source_pool_candidate_union_row_materialization_v0"
M202_DIR = EXP_ROOT / "artifacts" / "E008-M202_additive_source_pool_candidate_union_goal_evaluation_proxy_v0"
M203_DIR = EXP_ROOT / "artifacts" / "E008-M203_additive_source_pool_candidate_union_proxy_result_interpretation_v0"

M37_RUNNER = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M205_RUNNER = EXP_ROOT / "tools" / "run_m205_additive_source_pool_candidate_union_docker_trajectory_execution.py"
M205_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0"
)
M205_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0"
)

HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH2_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)

SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
BASELINE_POLICY = "no_source_pool_detector_confidence_reachable_subset_v0"
REPLACEMENT_POLICY = "source_pool_replacement_detector_confidence_reachable_subset_v0"
UNGUARDED_POLICY = "additive_union_unguarded_confidence_sort_v0"
POLICIES = [SELECTED_POLICY, BASELINE_POLICY, REPLACEMENT_POLICY, UNGUARDED_POLICY]
EXPECTED_DENOMINATOR_ROWS = 30
EXPECTED_POLICY_COUNT = 4
EXPECTED_PLAN_ROWS = EXPECTED_DENOMINATOR_ROWS * EXPECTED_POLICY_COUNT

POLICY_ROLES = {
    SELECTED_POLICY: "method_additive_union_source_gap_guard",
    BASELINE_POLICY: "protected_no_source_detector_confidence_baseline",
    REPLACEMENT_POLICY: "negative_source_pool_replacement_ablation",
    UNGUARDED_POLICY: "additive_union_unguarded_confidence_sort_ablation",
}

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "eval_all_viewpoint_count_loaded",
    "eval_geodesic_distance",
    "eval_euclidean_distance",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_first_viewpoint_3d_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    path.write_text(
        "".join(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def command_status(cmd: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s, check=False)
    except FileNotFoundError as exc:
        return {"available": False, "ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc)}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "available": True,
            "ok": False,
            "returncode": None,
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
            "timeout_s": timeout_s,
        }
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-500:],
    }


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m204::{adapter_episode_id.replace('::', '__')}::{policy_id}"


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m204::{adapter_episode_id.replace('::', '__')}"


def nav_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("proposal_uid")): row for row in rows if row.get("proposal_uid")}


def host_path_from_docker(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        rel = path.relative_to(DOCKER_DATA_ROOT)
    except ValueError:
        return None
    return RESEARCH2_DATA_ROOT / rel


def build_episode_goal_rows(
    goal_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    episode_index = {str(row.get("adapter_episode_id")): row for row in episode_rows}
    out = []
    for row in goal_rows:
        adapter_episode_id = str(row.get("adapter_episode_id"))
        episode = episode_index.get(adapter_episode_id, {})
        out.append(
            {
                **row,
                "version": VERSION,
                "scan_id": episode.get("scan_id") or f"hm3dnav_{row.get('scene_key')}_ep{row.get('source_episode_id')}",
                "scene_docker_path": episode.get("scene_docker_path"),
                "navmesh_docker_path": episode.get("navmesh_docker_path"),
                "policy_input_allowed": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M204 copies ObjectNav goal/viewpoint fields for evaluation-only trajectory metrics.",
            }
        )
    return sorted(out, key=lambda row: str(row.get("adapter_episode_id")))


def build_oracle_path_rows(goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in goal_rows:
        geodesic = finite_float(row.get("eval_geodesic_distance"))
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "viewpoint_path_found": geodesic is not None,
                "viewpoint_path_geodesic_distance": geodesic,
                "goal_snapped_path_found": False,
                "goal_snapped_path_geodesic_distance": None,
                "goal_snapped_path_point_count": 0,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M204 maps ObjectNav episode geodesic distance into the runner oracle-path contract.",
            }
        )
    return rows


def build_candidate_row(
    policy_row: dict[str, Any],
    nav: dict[str, Any],
    episode: dict[str, Any],
    placeholder: bool = False,
) -> dict[str, Any]:
    policy_id = str(policy_row.get("policy_id"))
    adapter_episode_id = str(policy_row.get("adapter_episode_id"))
    visit_rank = int(policy_row.get("visit_rank") or 1)
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    proposal_uid = str(policy_row.get("proposal_uid") or f"m204-placeholder::{adapter_episode_id}::{policy_id}")
    path_ready = (
        bool(policy_row.get("path_ready"))
        and bool(nav.get("candidate_usable_for_path_smoke", True))
        and not placeholder
    )
    snapped = nav.get("snapped_position_m") or policy_row.get("candidate_snapped_position_m")
    return {
        "version": VERSION,
        "policy_plan_uid": plan_uid,
        "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
        "policy_id": policy_id,
        "policy_role": POLICY_ROLES.get(policy_id, "additive_source_pool_policy"),
        "scan_id": policy_row.get("scan_id") or episode.get("scan_id"),
        "adapter_episode_id": adapter_episode_id,
        "scene_key": policy_row.get("scene_key") or episode.get("scene_key"),
        "object_category": policy_row.get("object_category") or episode.get("object_category"),
        "task_context_id": "open_vocabulary_object_search_additive_source_pool",
        "candidate_visit_uid": f"{plan_uid}::{visit_rank:04d}",
        "proposal_uid": proposal_uid,
        "raw_candidate_uid": policy_row.get("raw_candidate_uid"),
        "label_canonical": policy_row.get("label_canonical"),
        "visit_rank": visit_rank,
        "union_rank": policy_row.get("union_rank"),
        "base_candidate_rank": policy_row.get("base_candidate_rank"),
        "source_pool_candidate_rank": policy_row.get("source_pool_candidate_rank"),
        "confidence": policy_row.get("confidence") if policy_row.get("confidence") is not None else nav.get("confidence"),
        "selection_score": policy_row.get("selection_score")
        if policy_row.get("selection_score") is not None
        else nav.get("selection_score"),
        "ranking_score": policy_row.get("selection_score")
        if policy_row.get("selection_score") is not None
        else nav.get("selection_score"),
        "candidate_source_role": "current_observation",
        "candidate_source_family": policy_row.get("candidate_source_family"),
        "dynamic_stale_overlay_role": "additive_source_pool_candidate_union",
        "candidate_order_component": policy_id,
        "candidate_position_m": nav.get("centroid_world_m"),
        "candidate_stop_position_m": snapped,
        "execution_stop_position_m": snapped,
        "snapped_position_m": snapped,
        "target_free_observation_source_position_m": nav.get("source_position"),
        "source_to_candidate_path_cost_m": policy_row.get("source_to_candidate_path_cost_m")
        if policy_row.get("source_to_candidate_path_cost_m") is not None
        else nav.get("source_to_snapped_geodesic_m"),
        "cumulative_known_path_cost_m": policy_row.get("cumulative_known_path_cost_m"),
        "path_ready": path_ready,
        "candidate_usable_for_path_smoke": path_ready,
        "blocked_candidate_for_path_policy": bool(policy_row.get("blocked_candidate_for_path_policy")) or placeholder,
        "navmesh_validation_status": nav.get("navmesh_validation_status") or policy_row.get("navmesh_validation_status"),
        "scene_docker_path": nav.get("scene_docker_path") or episode.get("scene_docker_path"),
        "navmesh_docker_path": nav.get("navmesh_docker_path") or episode.get("navmesh_docker_path"),
        "frame_id": nav.get("frame_id"),
        "observation_pose_id": nav.get("observation_pose_id"),
        "target_free_route_id": nav.get("route_id"),
        "pose_family": nav.get("pose_family") or nav.get("frame_pose_role"),
        "candidate_scope": "additive_candidate_union",
        "union_action": policy_row.get("union_action"),
        "source_boundary_status": policy_row.get("source_boundary_status"),
        "source_ready_after_m195": bool(policy_row.get("source_ready_after_m195")),
        "source_gap_after_m195": bool(policy_row.get("source_gap_after_m195")),
        "m202_eval_source": policy_row.get("m202_eval_source"),
        "primary_budget_cap": "full_ranked",
        "policy_input_allowed": bool(policy_row.get("policy_input_allowed", True)),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "no_candidate_placeholder": placeholder,
        "claim_boundary": "M204 materializes runner-compatible additive candidate-union rows; no trajectory metric has been computed.",
    }


def build_trajectory_candidate_rows(
    union_policy_rows: list[dict[str, Any]],
    episode_goal_rows: list[dict[str, Any]],
    baseline_nav_rows: list[dict[str, Any]],
    source_pool_nav_rows: list[dict[str, Any]],
    scan_policy_metric_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_nav = nav_index(baseline_nav_rows)
    source_nav = nav_index(source_pool_nav_rows)
    episode_index = {str(row.get("adapter_episode_id")): row for row in episode_goal_rows}
    metric_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in scan_policy_metric_rows
        if row.get("metric_scope") == "m202_scan_policy_goal_eval"
    }
    rows = []
    join_rows = []
    observed_plan_keys = set()
    for policy_row in sorted(
        union_policy_rows,
        key=lambda row: (
            str(row.get("policy_id")),
            str(row.get("adapter_episode_id")),
            int(row.get("visit_rank") or 10**9),
        ),
    ):
        eval_source = str(policy_row.get("m202_eval_source"))
        nav = source_nav.get(str(policy_row.get("proposal_uid"))) if eval_source == "M197" else baseline_nav.get(str(policy_row.get("proposal_uid")))
        nav = nav or {}
        adapter_episode_id = str(policy_row.get("adapter_episode_id"))
        episode = episode_index.get(adapter_episode_id, {})
        policy_id = str(policy_row.get("policy_id"))
        observed_plan_keys.add((policy_id, adapter_episode_id))
        rows.append(build_candidate_row(policy_row, nav, episode))
        join_rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "adapter_episode_id": adapter_episode_id,
                "proposal_uid": policy_row.get("proposal_uid"),
                "m202_eval_source": eval_source,
                "nav_joined": bool(nav),
                "episode_joined": bool(episode),
                "scene_path_joined": bool(nav.get("scene_docker_path") or episode.get("scene_docker_path")),
                "candidate_stop_joined": bool(nav.get("snapped_position_m") or policy_row.get("candidate_snapped_position_m")),
            }
        )

    for policy_id in POLICIES:
        for episode in episode_goal_rows:
            adapter_episode_id = str(episode.get("adapter_episode_id"))
            if (policy_id, adapter_episode_id) in observed_plan_keys:
                continue
            metric = metric_index.get((policy_id, adapter_episode_id), {})
            placeholder = {
                "policy_id": policy_id,
                "adapter_episode_id": adapter_episode_id,
                "scan_id": episode.get("scan_id"),
                "scene_key": episode.get("scene_key"),
                "object_category": episode.get("object_category"),
                "visit_rank": 1,
                "proposal_uid": f"m204-placeholder::{adapter_episode_id}::{policy_id}",
                "candidate_source_family": "no_candidate",
                "union_action": "no_candidate_placeholder",
                "source_boundary_status": "no_candidate_for_policy",
                "source_ready_after_m195": False,
                "source_gap_after_m195": True,
                "path_ready": False,
                "policy_input_allowed": True,
                "m202_eval_source": "none",
            }
            rows.append(build_candidate_row(placeholder, {}, episode, placeholder=True))
            join_rows.append(
                {
                    "version": VERSION,
                    "policy_id": policy_id,
                    "adapter_episode_id": adapter_episode_id,
                    "proposal_uid": placeholder["proposal_uid"],
                    "m202_eval_source": "none",
                    "nav_joined": False,
                    "episode_joined": True,
                    "scene_path_joined": bool(episode.get("scene_docker_path")),
                    "candidate_stop_joined": False,
                    "placeholder_reason": f"M202 scan-policy candidate_rows={metric.get('candidate_rows')}",
                }
            )
    return rows, join_rows


def build_plan_rows(
    candidate_rows: list[dict[str, Any]],
    scan_policy_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in scan_policy_metric_rows
        if row.get("metric_scope") == "m202_scan_policy_goal_eval"
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)

    out = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        policy_id = str(first.get("policy_id"))
        adapter_episode_id = str(first.get("adapter_episode_id"))
        metric = metric_index.get((policy_id, adapter_episode_id), {})
        path_ready_rows = [row for row in rows if row.get("path_ready")]
        placeholders = [row for row in rows if row.get("no_candidate_placeholder")]
        source_counts = Counter(str(row.get("candidate_source_family")) for row in rows)
        out.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id, "additive_source_pool_policy"),
                "scan_id": first.get("scan_id"),
                "adapter_episode_id": adapter_episode_id,
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_budget": len(rows),
                "primary_budget_cap": "full_ranked",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": len(path_ready_rows),
                "blocked_candidate_rows": len(rows) - len(path_ready_rows),
                "no_candidate_placeholder_rows": len(placeholders),
                "candidate_source_family_counts": dict(sorted(source_counts.items())),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": str(M205_RUNNER.relative_to(ROOT)),
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start state from M197 source_pool_scale_eval_goal_rows and M64 scene path rows",
                "m202_proxy_primary_hit_for_reporting": metric.get("primary_hit"),
                "m202_proxy_primary_first_hit_rank_for_reporting": metric.get("primary_first_hit_rank"),
                "m202_proxy_primary_first_hit_cost_m_for_reporting": metric.get("primary_first_hit_cost_m"),
                "m202_proxy_spl_for_reporting": metric.get("primary_spl_proxy"),
                "m202_candidate_rows_for_reporting": metric.get("candidate_rows"),
                "diagnostic_source_gap_boundary_for_reporting": any(row.get("source_gap_after_m195") for row in rows),
                "stale_visit_first": False,
                "current_observation_first": True,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "uses_task_context_for_decision": False,
                "uses_m202_proxy_success_for_filtering": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M204 fixes additive candidate-union trajectory input; final SR/SPL is blocked until M205 execution.",
            }
        )
    return out


def build_budget_summary_rows(candidate_goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        grouped[(str(row.get("policy_id")), str(row.get("adapter_episode_id")))].append(row)
    scan_rows = []
    for (policy_id, adapter_episode_id), rows in sorted(grouped.items()):
        sorted_rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = sorted_rows[0] if sorted_rows else {}
        for budget in [1, 3, 5, 10, 20, "full"]:
            budget_rows = sorted_rows if budget == "full" else [
                row for row in sorted_rows if int(row.get("visit_rank") or 10**9) <= int(budget)
            ]
            hit_rows = [row for row in budget_rows if row.get("primary_eval_hit")]
            hit_row = hit_rows[0] if hit_rows else None
            oracle = finite_float(hit_row.get("episode_eval_geodesic_distance_m")) if hit_row else None
            cost = finite_float(hit_row.get("cumulative_known_path_cost_m")) if hit_row else None
            spl = float(oracle / max(oracle, cost)) if hit_row and oracle is not None and cost is not None and cost > 0 else 0.0
            scan_rows.append(
                {
                    "version": VERSION,
                    "metric_scope": "scan_policy_budget",
                    "policy_id": policy_id,
                    "adapter_episode_id": adapter_episode_id,
                    "scan_id": first.get("scan_id"),
                    "scene_key": first.get("scene_key"),
                    "object_category": first.get("object_category"),
                    "budget": budget,
                    "candidate_rows_considered": len(budget_rows),
                    "primary_hit": hit_row is not None,
                    "primary_first_hit_rank": hit_row.get("visit_rank") if hit_row else None,
                    "primary_first_hit_cost_m": cost,
                    "primary_spl_proxy": spl,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                    "claim_boundary": "Budget proxy sensitivity; not executed navigation.",
                }
            )
    aggregate_rows = []
    by_policy_budget: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        by_policy_budget[(str(row.get("policy_id")), str(row.get("budget")))].append(row)
    for (policy_id, budget), rows in sorted(by_policy_budget.items()):
        success_rows = [row for row in rows if row.get("primary_hit")]
        aggregate_rows.append(
            {
                "version": VERSION,
                "metric_scope": "policy_budget_aggregate",
                "policy_id": policy_id,
                "budget": int(budget) if str(budget).isdigit() else budget,
                "scan_policy_rows": len(rows),
                "success_rows": len(success_rows),
                "GoalEvalProxySR": safe_ratio(len(success_rows), len(rows)),
                "GoalEvalProxySPL": mean([row.get("primary_spl_proxy") for row in rows]),
                "primary_first_hit_rank_mean_over_success": mean([row.get("primary_first_hit_rank") for row in success_rows]),
                "primary_first_hit_cost_m_mean_over_success": mean([row.get("primary_first_hit_cost_m") for row in success_rows]),
                "claim_boundary": "Budget proxy sensitivity; not executed navigation.",
            }
        )
    return scan_rows + aggregate_rows


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join policy rows to ObjectNav execution state"),
        ("scene_key", "scene identity and navmesh lookup"),
        ("object_category", "query category used for detector prompt and label compatibility"),
        ("scene_docker_path", "Habitat scene path inside the read-only data mount"),
        ("navmesh_docker_path", "Habitat navmesh path inside the read-only data mount"),
        ("proposal_uid", "candidate identity"),
        ("raw_candidate_uid", "dedup candidate identity"),
        ("label_canonical", "candidate label after canonicalization"),
        ("confidence", "detector score for confidence-rank baselines"),
        ("selection_score", "detector score after pre-cap ranking"),
        ("candidate_source_family", "no-source detector vs source-pool detector provenance"),
        ("union_action", "additive union action used for audit"),
        ("snapped_position_m", "candidate stop position snapped to navmesh"),
        ("source_to_candidate_path_cost_m", "source-to-candidate path cost computed without target labels"),
        ("visit_rank", "policy visit order from M201"),
        ("path_ready", "navmesh source-readiness flag"),
    ]
    rows = []
    for field, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "contract_group": "allowed_policy_input",
                "allowed_for_policy": True,
                "allowed_for_metric": True,
                "reason": reason,
            }
        )
    for field in sorted(BLOCKED_POLICY_FIELDS):
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "contract_group": "blocked_policy_input",
                "allowed_for_policy": False,
                "allowed_for_metric": True,
                "reason": "ObjectNav goal/viewpoint/success/oracle fields are evaluation-only and must not enter trajectory policy input.",
            }
        )
    return rows


def build_leakage_audit_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    input_keys = set()
    for row in candidate_rows + plan_rows:
        input_keys.update(row.keys())
    rows = []
    for field in sorted(BLOCKED_POLICY_FIELDS):
        observed = field in input_keys
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": False,
                "observed_in_policy_input": observed,
                "leakage_audit_pass": not observed,
            }
        )
    flag_hits = sum(
        1
        for row in candidate_rows + plan_rows
        if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_success_label")
    )
    rows.append(
        {
            "version": VERSION,
            "field": "policy_input_flags",
            "allowed_for_policy": False,
            "observed_in_policy_input": flag_hits > 0,
            "flag_hit_count": flag_hits,
            "leakage_audit_pass": flag_hits == 0,
        }
    )
    return rows


def build_policy_contract_rows(
    plan_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    comparison_index = {str(row.get("policy_id")): row for row in comparison_rows}
    full_budget_index = {
        str(row.get("policy_id")): row
        for row in budget_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    }
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out = []
    for policy_id in POLICIES:
        rows = by_policy.get(policy_id, [])
        comparison = comparison_index.get(policy_id, {})
        full_budget = full_budget_index.get(policy_id, {})
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id),
                "trajectory_role": "method_candidate" if policy_id == SELECTED_POLICY else "baseline_or_ablation",
                "execution_mode": "full_ranked_until_success_or_exhausted",
                "candidate_budget": "full_ranked",
                "plan_rows": len(rows),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "path_ready_candidate_rows": sum(int(row.get("path_ready_candidate_rows") or 0) for row in rows),
                "placeholder_rows": sum(int(row.get("no_candidate_placeholder_rows") or 0) for row in rows),
                "m202_primary_proxy_sr": comparison.get("primary_proxy_sr")
                if comparison
                else full_budget.get("GoalEvalProxySR"),
                "m202_primary_spl_proxy_mean": comparison.get("primary_spl_proxy_mean")
                if comparison
                else full_budget.get("GoalEvalProxySPL"),
                "m202_delta_primary_proxy_sr": comparison.get("delta_primary_proxy_sr"),
                "m202_delta_primary_spl_proxy_mean": comparison.get("delta_primary_spl_proxy_mean"),
                "runner_required": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "Policy contract supports M205 trajectory execution input only; M204 is not a navigation result.",
            }
        )
    return out


def build_docker_preflight_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docker_version_status = command_status(["docker", "--version"])
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE])
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader"])
    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)])
    m205_compile = command_status(["python", "-m", "py_compile", str(M205_RUNNER)])

    scene_paths = sorted({str(row.get("scene_docker_path")) for row in candidate_rows if row.get("scene_docker_path")})
    navmesh_paths = sorted({str(row.get("navmesh_docker_path")) for row in candidate_rows if row.get("navmesh_docker_path")})
    scene_host_paths = [host_path_from_docker(path) for path in scene_paths]
    navmesh_host_paths = [host_path_from_docker(path) for path in navmesh_paths]
    scene_ready = sum(1 for path in scene_host_paths if path is not None and path.exists())
    navmesh_ready = sum(1 for path in navmesh_host_paths if path is not None and path.exists())
    content_files = list(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")) if OBJECTNAV_CONTENT_ROOT.exists() else []
    return [
        {
            "version": VERSION,
            "check_id": "docker_cli",
            "status": "pass" if docker_version_status.get("ok") else "fail",
            "evidence": f"returncode={docker_version_status.get('returncode')}; stderr_tail={docker_version_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "habitat_docker_image",
            "status": "pass" if docker_image_status.get("ok") else "fail",
            "evidence": f"image={HABITAT_IMAGE}; returncode={docker_image_status.get('returncode')}; stderr_tail={docker_image_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "nvidia_smi",
            "status": "pass" if nvidia_status.get("ok") else "warning",
            "evidence": f"returncode={nvidia_status.get('returncode')}; stdout_tail={nvidia_status.get('stdout_tail')!r}; stderr_tail={nvidia_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "read_only_hm3d_data_root",
            "status": "pass" if RESEARCH2_DATA_ROOT.exists() else "fail",
            "evidence": f"path={RESEARCH2_DATA_ROOT}; exists={RESEARCH2_DATA_ROOT.exists()}.",
        },
        {
            "version": VERSION,
            "check_id": "scene_files",
            "status": "pass" if scene_ready == len(scene_paths) and bool(scene_paths) else "fail",
            "evidence": f"ready={scene_ready}/{len(scene_paths)}.",
        },
        {
            "version": VERSION,
            "check_id": "navmesh_files",
            "status": "pass" if navmesh_ready == len(navmesh_paths) and bool(navmesh_paths) else "fail",
            "evidence": f"ready={navmesh_ready}/{len(navmesh_paths)}.",
        },
        {
            "version": VERSION,
            "check_id": "objectnav_content_files",
            "status": "pass" if content_files else "fail",
            "evidence": f"path={OBJECTNAV_CONTENT_ROOT}; json_gz_files={len(content_files)}.",
        },
        {
            "version": VERSION,
            "check_id": "m37_generalized_runner_available",
            "status": "pass" if M37_RUNNER.exists() and m37_compile.get("ok") else "fail",
            "evidence": f"runner={M37_RUNNER.relative_to(ROOT)}; py_compile={bool(m37_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "m205_policy_wrapper_available",
            "status": "pass" if M205_RUNNER.exists() and m205_compile.get("ok") else "fail",
            "evidence": f"runner={M205_RUNNER.relative_to(ROOT)}; py_compile={bool(m205_compile.get('ok'))}.",
        },
    ]


def build_readiness_gate_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    episode_goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    join_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    m203_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    fail_docker = sum(1 for row in docker_rows if row.get("status") == "fail")
    return [
        {
            "version": VERSION,
            "gate_id": "m203_contract_promotion_ready",
            "status": "pass" if m203_coverage.get("m204_contract_ready") else "fail",
            "evidence": f"M203 m204_contract_ready={m203_coverage.get('m204_contract_ready')}.",
        },
        {
            "version": VERSION,
            "gate_id": "fixed_denominator_goal_rows",
            "status": "pass" if len(episode_goal_rows) == EXPECTED_DENOMINATOR_ROWS else "fail",
            "evidence": f"episode_goal_rows={len(episode_goal_rows)}; expected={EXPECTED_DENOMINATOR_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "oracle_path_rows",
            "status": "pass" if len(oracle_rows) == EXPECTED_DENOMINATOR_ROWS else "fail",
            "evidence": f"oracle_path_rows={len(oracle_rows)}; expected={EXPECTED_DENOMINATOR_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_plan_rows",
            "status": "pass" if len(plan_rows) == EXPECTED_PLAN_ROWS and all(plan_counts.get(policy) == 30 for policy in POLICIES) else "fail",
            "evidence": f"plan_rows={len(plan_rows)}; policy_counts={dict(sorted(plan_counts.items()))}.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_scene_join",
            "status": "pass" if all(row.get("scene_path_joined") for row in join_rows) else "fail",
            "evidence": f"scene_join_fail={sum(1 for row in join_rows if not row.get('scene_path_joined'))}/{len(join_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_position_join",
            "status": "pass" if all(row.get("candidate_stop_joined") or row.get("placeholder_reason") for row in join_rows) else "fail",
            "evidence": f"position_join_fail={sum(1 for row in join_rows if not row.get('candidate_stop_joined') and not row.get('placeholder_reason'))}/{len(join_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_audit_pass") for row in leakage_rows) else "fail",
            "evidence": f"leakage_fail={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}/{len(leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_candidate_rows_materialized",
            "status": "pass" if candidate_rows and len(plan_rows) == EXPECTED_PLAN_ROWS else "fail",
            "evidence": f"candidate_rows={len(candidate_rows)}; plan_rows={len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "docker_runtime_preflight",
            "status": "pass" if fail_docker == 0 else "fail",
            "evidence": f"docker/runtime fail checks={fail_docker}/{len(docker_rows)}.",
        },
    ]


def build_m205_command_rows(runtime_ready: bool) -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m205_additive_source_pool_candidate_union_docker_trajectory_execution.py "
        "--m204-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M204_additive_source_pool_candidate_union_docker_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m205_additive_source_pool_candidate_union_docker_trajectory_execution",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M205_RUNNER.relative_to(ROOT)),
            "runner_implemented": M205_RUNNER.exists(),
            "output_path": str(M205_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M205_DATA_OUT_DIR.relative_to(ROOT)),
            "command": command,
            "launch_now": False,
            "runtime_preflight_ready": runtime_ready,
            "expected_files": [
                "coverage.json",
                "dynamic_stale_trajectory_attempt_rows.jsonl",
                "dynamic_stale_trajectory_policy_metric_rows.jsonl",
                "pairwise_policy_delta_rows.jsonl",
                "claim_boundary_rows.jsonl",
                "report.md",
            ],
            "verification_command": (
                "python - <<'PY'\n"
                "import json\n"
                "from pathlib import Path\n"
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m205_additive_source_pool_candidate_union_docker_trajectory_execution_ready'\n"
                "assert c['scan_task_policy_rows'] == 120\n"
                "print('m205 ready')\n"
                "PY"
            ),
        }
    ]


def build_claim_boundary_rows(runtime_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "additive_candidate_union_trajectory_contract",
            "supported": True,
            "claim_boundary": "M204 supports only runner-compatible contract materialization and Docker/data preflight for M205.",
        },
        {
            "version": VERSION,
            "claim_id": "m205_runtime_launch_ready",
            "supported": runtime_ready,
            "claim_boundary": "M205 launch is allowed only when Docker image, HM3D/ObjectNav data mount, scene files, navmesh files, and runner compile checks pass.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M204 does not execute trajectories and does not support final real navigation SR/SPL.",
        },
    ]


def build_route_decision_rows(runtime_ready: bool) -> list[dict[str, Any]]:
    if runtime_ready:
        return [
            {
                "version": VERSION,
                "decision": "proceed_to_m205_docker_trajectory_execution",
                "selected_next_unit": NEXT_UNIT,
                "launch_long_job_now": False,
                "runtime_preflight_ready": True,
                "real_navigation_sr_spl_ready": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "block_m205_launch_until_runtime_preflight_passes",
            "selected_next_unit": "restore/repoint HM3D ObjectNav data mount and Habitat Docker image, then run E008-M205",
            "launch_long_job_now": False,
            "runtime_preflight_ready": False,
            "real_navigation_sr_spl_ready": False,
            "reason": "M204 contract rows are materialized, but runtime preflight detects missing Habitat image and/or read-only HM3D/ObjectNav data root.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return f"""# E008-M204 Additive Source-Pool Candidate-Union Docker Trajectory Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Trajectory candidate rows: {coverage['trajectory_candidate_rows']}.
- Trajectory plan rows: {coverage['trajectory_execution_plan_rows']}.
- Episode goal rows: {coverage['episode_goal_eval_rows']}.
- Oracle path rows: {coverage['oracle_path_rows']}.
- Placeholder rows: {coverage['no_candidate_placeholder_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Runtime preflight pass: {coverage['runtime_preflight_pass']}.
- M205 execution ready: {coverage['m205_execution_ready']}.
- Selected next unit: `{coverage['selected_next_unit']}`.

## Policy Contract

{markdown_table(policy_rows, ['policy_id', 'policy_role', 'plan_rows', 'candidate_rows', 'path_ready_candidate_rows', 'placeholder_rows', 'm202_primary_proxy_sr', 'm202_primary_spl_proxy_mean'])}

## Gates

{markdown_table(gate_rows, ['gate_id', 'status', 'evidence'])}

## Docker/Data Preflight

{markdown_table(docker_rows, ['check_id', 'status', 'evidence'])}

## Route Decision

{markdown_table(route_rows, ['decision', 'runtime_preflight_ready', 'selected_next_unit', 'reason'])}

## Interpretation

M204 fixes the trajectory contract for the selected additive source-pool candidate-union method and the required baselines. It does not launch M205 because the current runtime preflight is not ready on this machine.
"""


def main() -> None:
    m201_cov = read_json(M201_DIR / "coverage.json")
    m202_cov = read_json(M202_DIR / "coverage.json")
    m203_cov = read_json(M203_DIR / "coverage.json")
    if not m201_cov or not m202_cov or not m203_cov:
        raise SystemExit("missing M201/M202/M203 coverage inputs")

    episode_rows = read_jsonl(M64_DIR / "val_mini_episode_rows.jsonl")
    goal_source_rows = read_jsonl(M197_DIR / "source_pool_scale_eval_goal_rows.jsonl")
    baseline_nav_rows = read_jsonl(M68_DIR / "candidate_navmesh_validation_rows.jsonl")
    source_pool_nav_rows = read_jsonl(M195_DIR / "candidate_navmesh_validation_rows.jsonl")
    union_policy_rows = read_jsonl(M201_DIR / "union_policy_rows.jsonl")
    candidate_goal_rows = read_jsonl(M202_DIR / "candidate_goal_eval_rows.jsonl")
    policy_goal_rows = read_jsonl(M202_DIR / "policy_goal_metric_rows.jsonl")
    policy_comparison_rows = read_jsonl(M202_DIR / "policy_comparison_rows.jsonl")
    if not all([episode_rows, goal_source_rows, baseline_nav_rows, source_pool_nav_rows, union_policy_rows, candidate_goal_rows, policy_goal_rows]):
        raise SystemExit("missing one or more row inputs for M204")

    episode_goal_rows = build_episode_goal_rows(goal_source_rows, episode_rows)
    oracle_rows = build_oracle_path_rows(episode_goal_rows)
    candidate_rows, join_rows = build_trajectory_candidate_rows(
        union_policy_rows,
        episode_goal_rows,
        baseline_nav_rows,
        source_pool_nav_rows,
        policy_goal_rows,
    )
    plan_rows = build_plan_rows(candidate_rows, policy_goal_rows)
    budget_rows = build_budget_summary_rows(candidate_goal_rows)
    input_contract_rows = build_input_contract_rows()
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows)
    policy_contract_rows = build_policy_contract_rows(plan_rows, policy_comparison_rows, budget_rows)
    docker_rows = build_docker_preflight_rows(candidate_rows)
    gate_rows = build_readiness_gate_rows(
        candidate_rows,
        plan_rows,
        episode_goal_rows,
        oracle_rows,
        join_rows,
        leakage_rows,
        docker_rows,
        m203_cov,
    )
    runtime_preflight_pass = all(row.get("status") != "fail" for row in docker_rows)
    contract_materialized = (
        len(plan_rows) == EXPECTED_PLAN_ROWS
        and len(episode_goal_rows) == EXPECTED_DENOMINATOR_ROWS
        and len(oracle_rows) == EXPECTED_DENOMINATOR_ROWS
        and all(row.get("leakage_audit_pass") for row in leakage_rows)
        and all(row.get("status") != "fail" for row in gate_rows if row.get("gate_id") != "docker_runtime_preflight")
    )
    status = READY_STATUS if contract_materialized and runtime_preflight_pass else NEEDS_RUNTIME_STATUS if contract_materialized else BLOCKED_STATUS
    command_rows = build_m205_command_rows(runtime_preflight_pass)
    claim_rows = build_claim_boundary_rows(runtime_preflight_pass)
    route_rows = build_route_decision_rows(runtime_preflight_pass)

    policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    source_counts = Counter(str(row.get("candidate_source_family")) for row in candidate_rows)
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m201_status": m201_cov.get("status"),
        "m202_status": m202_cov.get("status"),
        "m203_status": m203_cov.get("status"),
        "episode_goal_eval_rows": len(episode_goal_rows),
        "oracle_path_rows": len(oracle_rows),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "expected_trajectory_execution_plan_rows": EXPECTED_PLAN_ROWS,
        "policy_plan_counts": dict(sorted(policy_counts.items())),
        "candidate_source_family_counts": dict(sorted(source_counts.items())),
        "no_candidate_placeholder_rows": sum(1 for row in candidate_rows if row.get("no_candidate_placeholder")),
        "candidate_nav_join_rows": len(join_rows),
        "candidate_nav_join_fail_rows": sum(1 for row in join_rows if not row.get("nav_joined") and not row.get("placeholder_reason")),
        "candidate_scene_join_fail_rows": sum(1 for row in join_rows if not row.get("scene_path_joined")),
        "candidate_position_join_fail_rows": sum(
            1 for row in join_rows if not row.get("candidate_stop_joined") and not row.get("placeholder_reason")
        ),
        "policy_contract_rows": len(policy_contract_rows),
        "input_contract_rows": len(input_contract_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "docker_preflight_rows": len(docker_rows),
        "docker_preflight_fail_rows": sum(1 for row in docker_rows if row.get("status") == "fail"),
        "runtime_preflight_pass": runtime_preflight_pass,
        "contract_materialized": contract_materialized,
        "m205_runner_implemented": M205_RUNNER.exists(),
        "m205_execution_ready": runtime_preflight_pass and contract_materialized,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", episode_goal_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "candidate_join_audit_rows.jsonl", join_rows)
        write_jsonl(output_dir / "policy_contract_rows.jsonl", policy_contract_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "budget_proxy_summary_rows.jsonl", budget_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "m205_command_rows.jsonl", command_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_contract_rows, gate_rows, docker_rows, route_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
