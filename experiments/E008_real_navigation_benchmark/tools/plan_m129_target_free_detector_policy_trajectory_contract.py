#!/usr/bin/env python3
"""Build the E008-M129 target-free detector-policy trajectory contract and Docker preflight."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m129_target_free_detector_policy_trajectory_contract_v0"
READY_STATUS = "e008_m129_target_free_detector_policy_trajectory_contract_ready_runner_next"
READY_RUNNER_MISSING_STATUS = "e008_m129_target_free_detector_policy_trajectory_contract_ready_runner_missing"
BLOCKED_STATUS = "e008_m129_target_free_detector_policy_trajectory_contract_blocked"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M129_target_free_detector_policy_trajectory_contract_v0"
DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M129_target_free_detector_policy_trajectory_contract_v0"
)

M125_DIR = EXP_ROOT / "artifacts" / "E008-M125_target_free_detector_candidate_navmesh_validation_v0"
M126_DIR = EXP_ROOT / "artifacts" / "E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0"
M127_DIR = EXP_ROOT / "artifacts" / "E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0"
M128_DIR = EXP_ROOT / "artifacts" / "E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0"

HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH3_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)

M37_RUNNER = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M130_RUNNER = EXP_ROOT / "tools" / "run_m130_target_free_detector_policy_trajectory_execution_smoke.py"
M130_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0"
M130_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0"
)
NEXT_UNIT = "E008-M130 target-free detector-policy trajectory execution smoke"

POLICY_ROLES = {
    "detector_confidence_all_candidates_v0": "blocked_candidate_accounting_baseline",
    "detector_confidence_reachable_subset_v0": "primary_detector_confidence_baseline",
    "path_cost_ascending_reachable_subset_v0": "path_efficiency_candidate_policy",
    "confidence_path_cost_tradeoff_reachable_subset_v0": "confidence_path_cost_tradeoff_candidate_policy",
}
METHOD_POLICY = "path_cost_ascending_reachable_subset_v0"
EXPECTED_SCAN_ROWS = 1
EXPECTED_POLICY_COUNT = 4
EXPECTED_PLAN_ROWS = EXPECTED_SCAN_ROWS * EXPECTED_POLICY_COUNT
PRIMARY_EXECUTION_MODE = "full_ranked_until_success_or_exhausted"
BUDGETS: list[int | str] = [1, 3, 5, 10, 20, "full"]

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


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return round(sum(clean) / len(clean), 6) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def command_status(cmd: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s, check=False)
    except FileNotFoundError as exc:
        return {"available": False, "ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "available": True,
            "ok": False,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "",
            "timeout_s": timeout_s,
        }
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-500:],
    }


def host_path_from_docker(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        rel = path.relative_to(DOCKER_DATA_ROOT)
    except ValueError:
        return None
    return RESEARCH3_DATA_ROOT / rel


def adapter_episode_id_from_goal(row: dict[str, Any]) -> str:
    existing = row.get("adapter_episode_id")
    if existing:
        return str(existing)
    return f"{row.get('scene_key')}::{row.get('source_episode_id')}"


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m129::{adapter_episode_id.replace('::', '__')}::{policy_id}"


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m129::{adapter_episode_id.replace('::', '__')}"


def build_episode_goal_rows(raw_goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in raw_goal_rows:
        out.append(
            {
                **row,
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id_from_goal(row),
                "policy_input_allowed": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M129 copies target-free ObjectNav goal/viewpoint fields for evaluation-only trajectory metrics.",
            }
        )
    return out


def build_oracle_path_rows(goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in goal_rows:
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": f"hm3dnav_{row.get('scene_key').replace('-', '_')}_ep{row.get('source_episode_id')}",
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "viewpoint_path_found": finite_float(row.get("eval_geodesic_distance")) is not None,
                "viewpoint_path_geodesic_distance": row.get("eval_geodesic_distance"),
                "goal_snapped_path_found": False,
                "goal_snapped_path_geodesic_distance": None,
                "goal_snapped_path_point_count": 0,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M129 maps ObjectNav episode info.geodesic_distance into the runner oracle-path contract.",
            }
        )
    return rows


def build_trajectory_candidate_rows(
    visit_rows: list[dict[str, Any]],
    nav_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    nav_index = {str(row.get("proposal_uid")): row for row in nav_rows}
    out: list[dict[str, Any]] = []
    for visit in sorted(
        visit_rows,
        key=lambda row: (
            str(row.get("policy_id")),
            str(row.get("adapter_episode_id")),
            int(row.get("visit_rank") or 10**9),
        ),
    ):
        policy_id = str(visit.get("policy_id"))
        adapter_episode_id = str(visit.get("adapter_episode_id"))
        proposal_uid = str(visit.get("proposal_uid"))
        nav = nav_index.get(proposal_uid, {})
        path_ready = bool(visit.get("path_ready")) and bool(nav.get("candidate_usable_for_path_smoke"))
        out.append(
            {
                "version": VERSION,
                "policy_plan_uid": build_policy_plan_uid(adapter_episode_id, policy_id),
                "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id, "target_free_detector_policy"),
                "scan_id": visit.get("scan_id") or nav.get("scan_id"),
                "adapter_episode_id": adapter_episode_id,
                "scene_key": visit.get("scene_key") or nav.get("scene_key"),
                "object_category": visit.get("object_category") or nav.get("object_category"),
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_visit_uid": f"{build_policy_plan_uid(adapter_episode_id, policy_id)}::{int(visit.get('visit_rank') or 0):04d}",
                "proposal_uid": proposal_uid,
                "raw_candidate_uid": visit.get("raw_candidate_uid") or nav.get("raw_candidate_uid"),
                "label_canonical": visit.get("label_canonical") or nav.get("label_canonical"),
                "visit_rank": visit.get("visit_rank"),
                "candidate_rank_m09": visit.get("candidate_rank_m09") or nav.get("candidate_rank"),
                "confidence": visit.get("confidence") if visit.get("confidence") is not None else nav.get("confidence"),
                "selection_score": visit.get("selection_score") if visit.get("selection_score") is not None else nav.get("selection_score"),
                "ranking_score": visit.get("selection_score") if visit.get("selection_score") is not None else nav.get("selection_score"),
                "confidence_path_cost_tradeoff_score": visit.get("confidence_path_cost_tradeoff_score"),
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "candidate_order_component": policy_id,
                "candidate_position_m": nav.get("centroid_world_m"),
                "candidate_stop_position_m": nav.get("snapped_position_m"),
                "execution_stop_position_m": nav.get("snapped_position_m"),
                "snapped_position_m": nav.get("snapped_position_m"),
                "target_free_observation_source_position_m": nav.get("source_position"),
                "source_to_candidate_path_cost_m": nav.get("source_to_snapped_geodesic_m")
                if nav.get("source_to_snapped_geodesic_m") is not None
                else visit.get("source_to_candidate_path_cost_m"),
                "cumulative_known_path_cost_m": visit.get("cumulative_known_path_cost_m"),
                "path_ready": path_ready,
                "candidate_usable_for_path_smoke": path_ready,
                "blocked_candidate_for_path_policy": bool(visit.get("blocked_candidate_for_path_policy")),
                "navmesh_validation_status": nav.get("navmesh_validation_status") or visit.get("navmesh_validation_status"),
                "scene_docker_path": nav.get("scene_docker_path"),
                "navmesh_docker_path": nav.get("navmesh_docker_path"),
                "frame_id": nav.get("frame_id"),
                "observation_pose_id": nav.get("observation_pose_id"),
                "target_free_route_id": nav.get("route_id"),
                "pose_family": nav.get("pose_family"),
                "candidate_scope": visit.get("candidate_scope"),
                "primary_budget_cap": "full_ranked",
                "policy_input_allowed": bool(visit.get("policy_input_allowed", True)) and bool(nav.get("policy_input_allowed", True)),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M129 materializes runner-compatible target-free detector-policy candidates; no trajectory metric has been computed.",
            }
        )
    return out


def build_plan_rows(
    candidate_rows: list[dict[str, Any]],
    path_metric_rows: list[dict[str, Any]],
    goal_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    path_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in path_metric_rows
        if row.get("metric_scope") == "scan_policy"
    }
    goal_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in goal_metric_rows
        if row.get("metric_scope") == "target_free_scan_policy_goal_eval"
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)

    plan_rows: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        policy_id = str(first.get("policy_id"))
        adapter_episode_id = str(first.get("adapter_episode_id"))
        path = path_index.get((policy_id, adapter_episode_id), {})
        goal = goal_index.get((policy_id, adapter_episode_id), {})
        path_ready_rows = [row for row in rows if row.get("path_ready")]
        blocked_rows = [row for row in rows if not row.get("path_ready")]
        plan_rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id, "target_free_detector_policy"),
                "scan_id": first.get("scan_id"),
                "adapter_episode_id": adapter_episode_id,
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_budget": len(rows),
                "primary_budget_cap": "full_ranked",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": len(path_ready_rows),
                "blocked_candidate_rows": len(blocked_rows),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": str(M130_RUNNER.relative_to(ROOT)),
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start state from M127 target_free_eval_goal_rows",
                "m126_ranked_candidate_rows": path.get("ranked_candidate_rows"),
                "m126_path_ready_ranked_rows": path.get("path_ready_ranked_rows"),
                "m126_first_path_ready_rank": path.get("first_path_ready_rank"),
                "m126_first_path_ready_cost_m": path.get("first_path_ready_cost_m"),
                "m127_proxy_primary_hit_for_reporting": goal.get("primary_hit"),
                "m127_proxy_primary_first_hit_rank_for_reporting": goal.get("primary_first_hit_rank"),
                "m127_proxy_primary_first_hit_cost_m_for_reporting": goal.get("primary_first_hit_cost_m"),
                "m127_proxy_spl_for_reporting": goal.get("primary_spl_proxy"),
                "m127_goal_xz_1p0_hit_for_reporting": goal.get("goal_xz_1p0_hit"),
                "diagnostic_source_gap_boundary_for_reporting": False,
                "stale_visit_first": False,
                "current_observation_first": True,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "uses_task_context_for_decision": False,
                "uses_m127_proxy_success_for_filtering": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M129 fixes a target-free detector-policy trajectory input; final SR/SPL is blocked until M130 execution.",
            }
        )
    return plan_rows


def build_budget_summary_rows(candidate_goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        grouped[(str(row.get("policy_id")), str(row.get("adapter_episode_id")))].append(row)
    scan_rows: list[dict[str, Any]] = []
    for (policy_id, adapter_episode_id), rows in sorted(grouped.items()):
        sorted_rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = sorted_rows[0] if sorted_rows else {}
        for budget in BUDGETS:
            if budget == "full":
                budget_rows = sorted_rows
                budget_value: int | str = "full"
            else:
                budget_rows = [row for row in sorted_rows if int(row.get("visit_rank") or 10**9) <= int(budget)]
                budget_value = int(budget)
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
                    "budget": budget_value,
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

    aggregate_rows: list[dict[str, Any]] = []
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
                "budget": int(budget) if budget.isdigit() else budget,
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


def build_policy_contract_rows(
    policy_goal_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate_goal = {
        str(row.get("policy_id")): row
        for row in policy_goal_rows
        if row.get("metric_scope") == "policy_aggregate"
    }
    budget5 = {
        str(row.get("policy_id")): row
        for row in budget_summary_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == 5
    }
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = defaultdict(int)
    path_ready_counts = defaultdict(int)
    for row in plan_rows:
        policy_id = str(row.get("policy_id"))
        candidate_counts[policy_id] += int(row.get("candidate_rows") or 0)
        path_ready_counts[policy_id] += int(row.get("path_ready_candidate_rows") or 0)
    rows: list[dict[str, Any]] = []
    for policy_id in sorted(aggregate_goal):
        goal = aggregate_goal[policy_id]
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": "method_candidate" if policy_id == METHOD_POLICY else "baseline_or_ablation",
                "trajectory_role": POLICY_ROLES.get(policy_id, "target_free_detector_policy"),
                "execution_mode": PRIMARY_EXECUTION_MODE,
                "candidate_budget": "full_ranked",
                "plan_rows": plan_counts.get(policy_id, 0),
                "candidate_rows": candidate_counts.get(policy_id, 0),
                "path_ready_candidate_rows": path_ready_counts.get(policy_id, 0),
                "m127_primary_proxy_sr": goal.get("primary_proxy_sr"),
                "m127_primary_spl_proxy_mean": goal.get("primary_spl_proxy_mean"),
                "m127_primary_first_hit_rank_mean_over_success": goal.get("primary_first_hit_rank_mean_over_success"),
                "m127_goal_xz_1p0_proxy_sr": goal.get("goal_xz_1p0_proxy_sr"),
                "budget5_GoalEvalProxySR": budget5.get(policy_id, {}).get("GoalEvalProxySR"),
                "budget5_GoalEvalProxySPL": budget5.get(policy_id, {}).get("GoalEvalProxySPL"),
                "runner_required": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "Policy contract supports target-free trajectory execution input only; M129 is not a navigation result.",
            }
        )
    return rows


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join policy rows to ObjectNav execution state"),
        ("scene_key", "scene identity and navmesh lookup"),
        ("object_category", "query category used for detector prompt and label compatibility"),
        ("scene_docker_path", "Habitat scene path inside the read-only data mount"),
        ("navmesh_docker_path", "Habitat navmesh path inside the read-only data mount"),
        ("proposal_uid", "detector candidate identity"),
        ("label_canonical", "detector label after canonicalization"),
        ("confidence", "detector score for confidence-rank baselines"),
        ("selection_score", "detector score after pre-cap ranking"),
        ("snapped_position_m", "candidate stop position snapped to navmesh"),
        ("source_to_candidate_path_cost_m", "target-free source-to-candidate path cost computed without target labels"),
        ("visit_rank", "policy visit order from M126"),
        ("path_ready", "navmesh source-readiness flag from M125/M126"),
    ]
    rows: list[dict[str, Any]] = []
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
    rows: list[dict[str, Any]] = []
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
    flag_hits = sum(1 for row in candidate_rows + plan_rows if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
    rows.append(
        {
            "version": VERSION,
            "field": "uses_objectnav_eval_goal_or_viewpoint_for_policy",
            "allowed_for_policy": False,
            "observed_in_policy_input": flag_hits > 0,
            "flag_hit_count": flag_hits,
            "leakage_audit_pass": flag_hits == 0,
        }
    )
    return rows


def build_docker_preflight_rows(
    candidate_rows: list[dict[str, Any]],
    docker_version_status: dict[str, Any],
    docker_image_status: dict[str, Any],
    nvidia_status: dict[str, Any],
    m37_compile: dict[str, Any],
    m130_compile: dict[str, Any] | None,
) -> list[dict[str, Any]]:
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
            "status": "pass" if RESEARCH3_DATA_ROOT.exists() else "fail",
            "evidence": f"path={RESEARCH3_DATA_ROOT}; exists={RESEARCH3_DATA_ROOT.exists()}.",
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
            "check_id": "m130_policy_wrapper_available",
            "status": "pass" if M130_RUNNER.exists() and m130_compile and m130_compile.get("ok") else "warning",
            "evidence": f"runner={M130_RUNNER.relative_to(ROOT)}; exists={M130_RUNNER.exists()}; py_compile={bool(m130_compile and m130_compile.get('ok'))}.",
        },
    ]


def build_m130_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research3/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m130_target_free_detector_policy_trajectory_execution_smoke.py "
        "--m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m130_target_free_detector_policy_trajectory_execution_smoke",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research3/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M130_RUNNER.relative_to(ROOT)),
            "runner_implemented": M130_RUNNER.exists(),
            "output_path": str(M130_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M130_DATA_OUT_DIR.relative_to(ROOT)),
            "command": command,
            "launch_now": False,
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m130_target_free_detector_policy_trajectory_execution_smoke_ready'\n"
                "assert c['scan_task_policy_rows'] == 4\n"
                "print('m130 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    m125_cov: dict[str, Any],
    m126_cov: dict[str, Any],
    m127_cov: dict[str, Any],
    m128_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policies = Counter(str(row.get("policy_id")) for row in plan_rows)
    full_rows = [
        row
        for row in budget_summary_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    ]
    return [
        {
            "version": VERSION,
            "gate_id": "target_free_navmesh_validation_ready",
            "status": "pass" if m125_cov.get("status") == "e008_m125_target_free_detector_candidate_navmesh_validation_ready" else "fail",
            "evidence": f"M125 status={m125_cov.get('status')}; path_ready={m125_cov.get('source_to_snapped_path_found_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "target_free_visit_order_ready",
            "status": "pass" if m126_cov.get("candidate_visit_order_path_smoke_ready") else "fail",
            "evidence": f"M126 status={m126_cov.get('status')}; visit_order_rows={m126_cov.get('visit_order_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "leakage_safe_goal_eval_ready",
            "status": "pass" if m127_cov.get("leakage_audit_pass") else "fail",
            "evidence": f"M127 status={m127_cov.get('status')}; leakage={m127_cov.get('leakage_audit_pass')}.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_contract_promotion_ready",
            "status": "pass" if m128_cov.get("trajectory_contract_promotion_ready") else "fail",
            "evidence": f"M128 status={m128_cov.get('status')}; promotion={m128_cov.get('trajectory_contract_promotion_ready')}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_candidate_rows_materialized",
            "status": "pass" if len(candidate_rows) == int(m126_cov.get("visit_order_rows") or -1) else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; M126 visit_order_rows={m126_cov.get('visit_order_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_plan_rows_materialized",
            "status": "pass" if len(plan_rows) == EXPECTED_PLAN_ROWS and len(policies) == EXPECTED_POLICY_COUNT else "fail",
            "evidence": f"plan rows={len(plan_rows)}; policies={dict(sorted(policies.items()))}.",
        },
        {
            "version": VERSION,
            "gate_id": "goal_and_oracle_rows_ready",
            "status": "pass" if len(goal_rows) == EXPECTED_SCAN_ROWS and len(oracle_rows) == EXPECTED_SCAN_ROWS else "fail",
            "evidence": f"goal rows={len(goal_rows)}; oracle rows={len(oracle_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_audit_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked hits={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}.",
        },
        {
            "version": VERSION,
            "gate_id": "full_ranked_proxy_success_floor",
            "status": "pass"
            if full_rows and min(float(row.get("GoalEvalProxySR") or 0.0) for row in full_rows) >= 1.0
            else "fail",
            "evidence": f"full-budget min proxy SR={min([float(row.get('GoalEvalProxySR') or 0.0) for row in full_rows], default=0.0):.6f}.",
        },
        {
            "version": VERSION,
            "gate_id": "docker_preflight",
            "status": "pass"
            if all(row.get("status") in {"pass", "warning"} for row in docker_rows)
            and not any(row.get("status") == "fail" for row in docker_rows)
            else "fail",
            "evidence": f"fail={sum(1 for row in docker_rows if row.get('status') == 'fail')}; warning={sum(1 for row in docker_rows if row.get('status') == 'warning')}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_wrapper",
            "status": "pass" if M130_RUNNER.exists() else "warning",
            "evidence": f"M130 runner exists={M130_RUNNER.exists()}; warning means next unit should scaffold the wrapper before Docker execution.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "trajectory_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M129 provides a Docker-preflighted, runner-compatible one-case target-free detector-policy trajectory input contract.",
        },
        {
            "version": VERSION,
            "claim_id": "target_free_detector_policy_execution",
            "status": "not_executed",
            "safe_claim": "M129 does not execute Habitat trajectories; M130 is required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "deployable_fixed_budget_policy",
            "status": "blocked",
            "safe_claim": "M129 primary mode is full-ranked proxy-to-trajectory consistency execution; fixed-budget deployability remains later evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M130 execution, result interpretation, larger scale, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "M129 detector-policy contract does not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(contract_ready: bool, runner_ready: bool) -> list[dict[str, Any]]:
    if contract_ready and runner_ready:
        selected_next = NEXT_UNIT
        decision = "run_m130_target_free_detector_policy_trajectory_smoke"
    elif contract_ready:
        selected_next = "E008-M130 target-free detector-policy trajectory execution runner scaffold"
        decision = "scaffold_m130_runner_before_docker_execution"
    else:
        selected_next = "repair E008-M129 target-free detector-policy trajectory contract"
        decision = "repair_m129_contract_or_preflight"
    return [
        {
            "version": VERSION,
            "decision_id": "m129_selected_next",
            "decision": decision,
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "reason": "M129 fixes the target-free detector-policy trajectory input contract and Docker/data preflight; M130 should execute the bounded one-case trajectory smoke."
            if contract_ready
            else "One or more M129 contract/preflight gates failed.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> str:
    budget_summary = [
        row
        for row in budget_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") in {5, "full"}
    ]
    return "\n".join(
        [
            "# E008-M129 Target-Free Detector-Policy Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Eval goal rows: {coverage['target_free_eval_goal_rows']}.",
            f"- Oracle path rows: {coverage['oracle_path_rows']}.",
            f"- Docker preflight pass: {coverage['docker_preflight_pass']}.",
            f"- Runner implemented: {coverage['runner_implemented']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "trajectory_role",
                    "plan_rows",
                    "candidate_rows",
                    "path_ready_candidate_rows",
                    "m127_primary_proxy_sr",
                    "m127_primary_spl_proxy_mean",
                    "budget5_GoalEvalProxySR",
                ],
            ),
            "",
            "## Budget Sensitivity",
            "",
            markdown_table(
                budget_summary,
                ["policy_id", "budget", "success_rows", "scan_policy_rows", "GoalEvalProxySR", "GoalEvalProxySPL"],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            markdown_table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Paper Claim Boundary",
            "",
            "- M129 supports only the trajectory execution contract and Docker/data preflight.",
            "- M129 intentionally does not claim final real navigation `SR` / `SPL`, deployable fixed-budget search policy, or final real RGB-D/open-vocabulary robustness.",
            "- The full-ranked execution mode tests proxy-to-trajectory consistency for one target-free case.",
            "",
        ]
    )


def copy_core_outputs(filenames: list[str]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        src = ARTIFACT_DIR / name
        if src.exists():
            shutil.copy2(src, DATA_OUT_DIR / name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m125_cov = read_json(M125_DIR / "coverage.json")
    m126_cov = read_json(M126_DIR / "coverage.json")
    m127_cov = read_json(M127_DIR / "coverage.json")
    m128_cov = read_json(M128_DIR / "coverage.json")
    nav_rows = read_jsonl(M125_DIR / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(M126_DIR / "candidate_visit_order_rows.jsonl")
    m126_metric_rows = read_jsonl(M126_DIR / "policy_metric_rows.jsonl")
    raw_goal_rows = read_jsonl(M127_DIR / "target_free_eval_goal_rows.jsonl")
    candidate_goal_rows = read_jsonl(M127_DIR / "candidate_goal_eval_rows.jsonl")
    scan_goal_rows = read_jsonl(M127_DIR / "target_free_scan_goal_metric_rows.jsonl")
    policy_goal_rows = read_jsonl(M127_DIR / "policy_goal_metric_rows.jsonl")

    if not all([m125_cov, m126_cov, m127_cov, m128_cov]):
        raise SystemExit("missing one or more required E008-M125/M126/M127/M128 coverage files")
    if not all([nav_rows, visit_rows, raw_goal_rows, candidate_goal_rows, scan_goal_rows, policy_goal_rows]):
        raise SystemExit("missing one or more required E008-M125/M126/M127 row files")

    goal_rows = build_episode_goal_rows(raw_goal_rows)
    oracle_rows = build_oracle_path_rows(goal_rows)
    candidate_rows = build_trajectory_candidate_rows(visit_rows, nav_rows)
    plan_rows = build_plan_rows(candidate_rows, m126_metric_rows, scan_goal_rows)
    budget_summary_rows = build_budget_summary_rows(candidate_goal_rows)
    policy_rows = build_policy_contract_rows(policy_goal_rows, plan_rows, budget_summary_rows)
    input_rows = build_input_contract_rows()
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows)

    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)
    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m130_compile = command_status(["python", "-m", "py_compile", str(M130_RUNNER)], timeout_s=30) if M130_RUNNER.exists() else None
    docker_rows = build_docker_preflight_rows(
        candidate_rows,
        docker_version_status,
        docker_image_status,
        nvidia_status,
        m37_compile,
        m130_compile,
    )
    gate_rows = build_readiness_gate_rows(
        m125_cov,
        m126_cov,
        m127_cov,
        m128_cov,
        candidate_rows,
        plan_rows,
        goal_rows,
        oracle_rows,
        leakage_rows,
        docker_rows,
        budget_summary_rows,
    )
    contract_ready = not any(row.get("status") == "fail" for row in gate_rows)
    runner_ready = M130_RUNNER.exists() and bool(m130_compile and m130_compile.get("ok"))
    route_rows = build_route_decision_rows(contract_ready, runner_ready)
    command_rows = build_m130_command_rows()
    claim_rows = build_claim_boundary_rows()

    policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    budget5_summary = [
        row
        for row in budget_summary_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == 5
    ]
    full_budget_summary = [
        row
        for row in budget_summary_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    ]
    docker_preflight_pass = all(row.get("status") in {"pass", "warning"} for row in docker_rows) and not any(
        row.get("status") == "fail" for row in docker_rows
    )
    if not contract_ready:
        status = BLOCKED_STATUS
    elif runner_ready:
        status = READY_STATUS
    else:
        status = READY_RUNNER_MISSING_STATUS

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m125_status": m125_cov.get("status"),
        "m126_status": m126_cov.get("status"),
        "m127_status": m127_cov.get("status"),
        "m128_status": m128_cov.get("status"),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "policy_count": len(policy_counts),
        "policy_ids": sorted(policy_counts),
        "policy_plan_counts": dict(sorted(policy_counts.items())),
        "target_free_eval_goal_rows": len(goal_rows),
        "oracle_path_rows": len(oracle_rows),
        "primary_execution_mode": PRIMARY_EXECUTION_MODE,
        "method_policy_id": METHOD_POLICY,
        "budget5_min_GoalEvalProxySR": min([float(row.get("GoalEvalProxySR") or 0.0) for row in budget5_summary], default=0.0),
        "full_ranked_min_GoalEvalProxySR": min([float(row.get("GoalEvalProxySR") or 0.0) for row in full_budget_summary], default=0.0),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "docker_preflight_pass": docker_preflight_pass,
        "docker_cli_ok": bool(docker_version_status.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "nvidia_smi_ok": bool(nvidia_status.get("ok")),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "runner_script": str(M130_RUNNER.relative_to(ROOT)),
        "runner_implemented": M130_RUNNER.exists(),
        "runner_py_compile_pass": runner_ready,
        "trajectory_execution_contract_ready": contract_ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "detector_target_recall_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", goal_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
        write_jsonl(output_dir / "trajectory_execution_contract_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "budget_proxy_summary_rows.jsonl", budget_summary_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "m130_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, budget_summary_rows, gate_rows, docker_rows),
        encoding="utf-8",
    )
    copy_core_outputs(
        [
            "coverage.json",
            "trajectory_execution_contract_rows.jsonl",
            "budget_proxy_summary_rows.jsonl",
            "docker_preflight_rows.jsonl",
            "readiness_gate_rows.jsonl",
            "m130_command_rows.jsonl",
        ]
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
