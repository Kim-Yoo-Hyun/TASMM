#!/usr/bin/env python3
"""Materialize E008-M133 target-free trajectory-aware repair rows."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M37_PATH = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"

VERSION = "e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
READY_STATUS = "e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_blocked"
NEXT_UNIT = "E008-M134 target-free trajectory-aware repair trajectory execution contract and Docker preflight"

DEFAULT_M129_CONTRACT = EXP_ROOT / "artifacts" / "E008-M129_target_free_detector_policy_trajectory_contract_v0"
DEFAULT_M132_CONTRACT = EXP_ROOT / "artifacts" / "E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0"
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
)

MATRIX_ID = "candidate_to_candidate_geodesic_matrix_v0"
PRIMARY_BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
HISTORICAL_PATH_POLICY = "path_cost_ascending_reachable_subset_v0"
SELECTED_REPAIR_POLICY = "trajectory_greedy_confidence_path_repair_v0"

POLICY_ORDER = [
    SELECTED_REPAIR_POLICY,
    "trajectory_greedy_confidence_only_reachable_v0",
    "trajectory_greedy_path_only_reachable_v0",
    PRIMARY_BASELINE_POLICY,
    HISTORICAL_PATH_POLICY,
]

POLICY_ROLES = {
    SELECTED_REPAIR_POLICY: "selected_repair_policy",
    "trajectory_greedy_confidence_only_reachable_v0": "trajectory_repair_ablation_confidence_only",
    "trajectory_greedy_path_only_reachable_v0": "trajectory_repair_ablation_path_only",
    PRIMARY_BASELINE_POLICY: "primary_detector_confidence_baseline",
    HISTORICAL_PATH_POLICY: "negative_historical_path_cost_baseline",
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
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
}


def load_m37_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m37_runner", M37_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load M37 runner from {M37_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m129-contract", default=str(DEFAULT_M129_CONTRACT))
    parser.add_argument("--m132-contract", default=str(DEFAULT_M132_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


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
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def valid_vec3(value: object) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(finite_float(part) is not None for part in value)


def as_vec3(value: object) -> list[float] | None:
    if not valid_vec3(value):
        return None
    return [float(part) for part in value]  # type: ignore[arg-type]


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
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


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def adapter_token(adapter_episode_id: str) -> str:
    return adapter_episode_id.replace("::", "__")


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m133::{adapter_token(adapter_episode_id)}::{policy_id}"


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m133::{adapter_token(adapter_episode_id)}"


def candidate_node_uid(row: dict[str, Any]) -> str:
    return f"candidate::{row.get('proposal_uid')}"


def start_node_uid(adapter_episode_id: str) -> str:
    return f"episode_start::{adapter_episode_id}"


def candidate_position(row: dict[str, Any]) -> list[float] | None:
    return as_vec3(row.get("execution_stop_position_m") or row.get("snapped_position_m") or row.get("candidate_stop_position_m"))


def candidate_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    return (
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or 10**9),
        str(row.get("proposal_uid")),
    )


def source_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    return (
        finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or 10**9),
        str(row.get("proposal_uid")),
    )


def normalize(value: float | None, values: list[float | None], missing_value: float) -> float:
    clean = [float(item) for item in values if item is not None and math.isfinite(float(item))]
    if value is None or not math.isfinite(value):
        return missing_value
    if not clean:
        return missing_value
    min_v = min(clean)
    max_v = max(clean)
    if math.isclose(max_v, min_v):
        return 0.5
    return float((value - min_v) / (max_v - min_v))


def matrix_cost(
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    from_uid: str,
    to_uid: str,
) -> tuple[bool, float | None, int, str]:
    row = cost_lookup.get((from_uid, to_uid), {})
    return (
        bool(row.get("path_found")),
        finite_float(row.get("geodesic_distance_m")),
        int(row.get("point_count") or 0),
        str(row.get("path_error") or ""),
    )


def build_base_candidate_rows(m129_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in m129_candidates
        if row.get("policy_id") == PRIMARY_BASELINE_POLICY
        and row.get("path_ready")
        and row.get("candidate_usable_for_path_smoke", True)
        and not row.get("policy_input_uses_eval_goal_or_viewpoint")
        and not row.get("policy_input_uses_success_label")
    ]
    dedup: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=candidate_sort_key):
        dedup.setdefault(str(row.get("proposal_uid")), row)
    return list(dedup.values())


def build_cost_matrix_rows(
    sim: Any,
    m37: Any,
    start_pos: list[float],
    candidates: list[dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    start_uid = start_node_uid(adapter_episode_id)

    def add_path(
        from_uid: str,
        from_type: str,
        from_pos: list[float],
        to_uid: str,
        to_type: str,
        to_pos: list[float],
        from_proposal_uid: str | None = None,
        to_proposal_uid: str | None = None,
    ) -> None:
        path = m37.find_path(sim, from_pos, to_pos)
        row = {
            "version": VERSION,
            "row_type": "trajectory_cost_matrix",
            "matrix_id": MATRIX_ID,
            "adapter_episode_id": adapter_episode_id,
            "scan_id": candidates[0].get("scan_id") if candidates else None,
            "scene_key": candidates[0].get("scene_key") if candidates else None,
            "object_category": candidates[0].get("object_category") if candidates else None,
            "from_node_uid": from_uid,
            "from_node_type": from_type,
            "from_proposal_uid": from_proposal_uid,
            "to_node_uid": to_uid,
            "to_node_type": to_type,
            "to_proposal_uid": to_proposal_uid,
            "from_position_m": from_pos,
            "to_position_m": to_pos,
            "path_found": bool(path.get("path_found")),
            "geodesic_distance_m": finite_float(path.get("geodesic_distance")),
            "point_count": int(path.get("point_count") or 0),
            "path_error": str(path.get("error") or ""),
            "cost_source": "Habitat pathfinder geodesic distance on HM3D navmesh",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "claim_boundary": "M133 cost matrix uses episode start/candidate stops only; ObjectNav goal/viewpoints are not policy inputs.",
        }
        rows.append(row)
        lookup[(from_uid, to_uid)] = row

    for cand in candidates:
        pos = candidate_position(cand)
        if pos is None:
            continue
        add_path(
            start_uid,
            "episode_start",
            start_pos,
            candidate_node_uid(cand),
            "candidate",
            pos,
            to_proposal_uid=str(cand.get("proposal_uid")),
        )

    for src in candidates:
        src_pos = candidate_position(src)
        if src_pos is None:
            continue
        for dst in candidates:
            if src.get("proposal_uid") == dst.get("proposal_uid"):
                continue
            dst_pos = candidate_position(dst)
            if dst_pos is None:
                continue
            add_path(
                candidate_node_uid(src),
                "candidate",
                src_pos,
                candidate_node_uid(dst),
                "candidate",
                dst_pos,
                from_proposal_uid=str(src.get("proposal_uid")),
                to_proposal_uid=str(dst.get("proposal_uid")),
            )
    return rows, lookup


def greedy_path_only_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> list[dict[str, Any]]:
    remaining = list(candidates)
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    while remaining:
        scored = []
        for row in remaining:
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            scored.append(
                (
                    not found,
                    cost if cost is not None else math.inf,
                    -(finite_float(row.get("confidence")) or -math.inf),
                    int(row.get("candidate_rank_m09") or 10**9),
                    str(row.get("proposal_uid")),
                    row,
                )
            )
        selected = sorted(scored)[0][-1]
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        found, _, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        if found:
            current_uid = candidate_node_uid(selected)
    return ordered


def greedy_confidence_path_repair_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> list[dict[str, Any]]:
    remaining = list(candidates)
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    step_idx = 0
    while remaining:
        conf_values = [finite_float(row.get("confidence")) for row in remaining]
        source_values = [finite_float(row.get("source_to_candidate_path_cost_m")) for row in remaining]
        current_values = [
            matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))[1]
            if matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))[0]
            else None
            for row in remaining
        ]
        scored = []
        for row in remaining:
            found, current_cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            conf = finite_float(row.get("confidence"))
            source_cost = finite_float(row.get("source_to_candidate_path_cost_m"))
            conf_norm = normalize(conf, conf_values, 0.0)
            current_norm = normalize(current_cost if found else None, current_values, 1.0)
            source_norm = normalize(source_cost, source_values, 1.0)
            score = conf_norm - current_norm
            if step_idx == 0:
                score -= 0.10 * source_norm
            scored.append(
                (
                    -score,
                    not found,
                    current_norm,
                    source_norm,
                    int(row.get("candidate_rank_m09") or 10**9),
                    str(row.get("proposal_uid")),
                    row,
                )
            )
        selected = sorted(scored)[0][-1]
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        found, _, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        if found:
            current_uid = candidate_node_uid(selected)
        step_idx += 1
    return ordered


def ordered_candidates_for_policy(
    policy_id: str,
    base_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> list[dict[str, Any]]:
    if policy_id == PRIMARY_BASELINE_POLICY or policy_id == "trajectory_greedy_confidence_only_reachable_v0":
        return sorted(base_candidates, key=candidate_sort_key)
    if policy_id == HISTORICAL_PATH_POLICY:
        return sorted(base_candidates, key=source_cost_sort_key)
    if policy_id == "trajectory_greedy_path_only_reachable_v0":
        return greedy_path_only_order(base_candidates, cost_lookup, adapter_episode_id)
    if policy_id == SELECTED_REPAIR_POLICY:
        return greedy_confidence_path_repair_order(base_candidates, cost_lookup, adapter_episode_id)
    raise ValueError(f"unknown policy_id: {policy_id}")


def materialize_policy_candidate_rows(
    policy_id: str,
    ordered_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    benchmark_uid = build_benchmark_uid(adapter_episode_id)
    current_uid = start_node_uid(adapter_episode_id)
    cumulative = 0.0
    for rank, source in enumerate(ordered_candidates, start=1):
        to_uid = candidate_node_uid(source)
        found, cost, point_count, path_error = matrix_cost(cost_lookup, current_uid, to_uid)
        if found and cost is not None:
            cumulative += cost
        confidence = finite_float(source.get("confidence")) or 0.0
        source_cost = finite_float(source.get("source_to_candidate_path_cost_m"))
        if policy_id == HISTORICAL_PATH_POLICY:
            repair_score = -1.0 * (source_cost if source_cost is not None else math.inf)
        elif policy_id == "trajectory_greedy_path_only_reachable_v0":
            repair_score = -1.0 * (cost if cost is not None else math.inf)
        elif policy_id in {PRIMARY_BASELINE_POLICY, "trajectory_greedy_confidence_only_reachable_v0"}:
            repair_score = confidence
        else:
            # The exact online score is recomputed during ordering; this row records a local diagnostic score.
            repair_score = confidence - (cost if cost is not None else 1e6)

        row = dict(source)
        row.update(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": benchmark_uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_visit_uid": f"{plan_uid}::{rank:04d}",
                "visit_rank": rank,
                "ranking_score": repair_score,
                "candidate_order_component": policy_id,
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "primary_budget_cap": "full_ranked",
                "trajectory_cost_matrix_id": MATRIX_ID,
                "trajectory_repair_score": repair_score,
                "trajectory_repair_step_source": current_uid,
                "trajectory_repair_materialized": True,
                "trajectory_aware_repair_materialized": True,
                "current_pose_to_candidate_geodesic_m": cost,
                "current_pose_to_candidate_path_found": found,
                "current_pose_to_candidate_path_point_count": point_count,
                "current_pose_to_candidate_path_error": path_error,
                "planned_segment_path_found": found,
                "planned_cumulative_path_cost_m": cumulative,
                "selected_from_remaining_rows": len(ordered_candidates) - rank + 1,
                "path_ready": bool(source.get("path_ready")),
                "candidate_usable_for_path_smoke": bool(source.get("candidate_usable_for_path_smoke", True)),
                "blocked_candidate_for_path_policy": bool(source.get("blocked_candidate_for_path_policy")),
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M133 materializes repaired visit-order rows only; executed SR/SPL remains blocked until M134.",
            }
        )
        for field in BLOCKED_POLICY_FIELDS:
            row.pop(field, None)
        out.append(row)
        if found:
            current_uid = to_uid
    return out


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)

    plan_rows: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        policy_id = str(first.get("policy_id"))
        path_ready_rows = [row for row in rows if row.get("path_ready")]
        blocked_rows = [row for row in rows if not row.get("path_ready")]
        plan_rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": policy_id,
                "policy_role": first.get("policy_role"),
                "scan_id": first.get("scan_id"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_budget": len(rows),
                "primary_budget_cap": "full_ranked",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": len(path_ready_rows),
                "blocked_candidate_rows": len(blocked_rows),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "repair_candidate_file": "trajectory_repair_candidate_rows.jsonl",
                "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m130_target_free_detector_policy_trajectory_execution_smoke.py",
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start_position only; goal/viewpoints are metric-only",
                "uses_trajectory_cost_matrix_for_policy": True,
                "uses_task_context_for_decision": False,
                "uses_m127_proxy_success_for_filtering": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "diagnostic_source_gap_boundary_for_reporting": False,
                "stale_visit_first": False,
                "current_observation_first": True,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "claim_boundary": "M133 fixes target-free repair trajectory inputs only; final SR/SPL requires M134 execution and scale.",
            }
        )
    return plan_rows


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join start state"),
        ("scene_key", "scene identity"),
        ("object_category", "query category and label compatibility"),
        ("scene_docker_path", "Habitat scene path"),
        ("navmesh_docker_path", "Habitat navmesh path"),
        ("candidate_position_m", "detector-derived candidate centroid"),
        ("candidate_stop_position_m", "candidate stop on navmesh"),
        ("execution_stop_position_m", "candidate execution stop"),
        ("snapped_position_m", "navmesh-snapped candidate point"),
        ("confidence", "detector confidence score"),
        ("source_to_candidate_path_cost_m", "source-to-candidate path prior"),
        ("current_pose_to_candidate_geodesic_m", "trajectory-aware current-pose geodesic cost"),
        ("trajectory_cost_matrix_id", "cost matrix identifier"),
        ("candidate_rank_m09", "detector rank tie-breaker"),
        ("path_ready", "candidate path usability flag"),
        ("candidate_usable_for_path_smoke", "runner usability flag"),
    ]
    rows = [
        {
            "version": VERSION,
            "contract_group": "allowed_policy_input",
            "field": field,
            "allowed_for_policy": True,
            "allowed_for_metric": True,
            "reason": reason,
        }
        for field, reason in allowed
    ]
    rows.extend(
        {
            "version": VERSION,
            "contract_group": "blocked_policy_input",
            "field": field,
            "allowed_for_policy": False,
            "allowed_for_metric": True,
            "reason": "ObjectNav goal/viewpoint, success label, or posthoc metric-only field.",
        }
        for field in sorted(BLOCKED_POLICY_FIELDS)
    )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads = [
        ("trajectory_repair_candidate_rows", candidate_rows),
        ("trajectory_repair_execution_plan_rows", plan_rows),
        ("trajectory_cost_matrix_rows", matrix_rows),
    ]
    out: list[dict[str, Any]] = []
    for payload, rows in payloads:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get(
                "policy_input_uses_eval_goal_or_viewpoint"
            ) or row.get("policy_input_uses_success_label"):
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


def build_readiness_gate_rows(
    missing_inputs: list[str],
    base_candidate_count: int,
    matrix_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    scene_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_matrix_rows = base_candidate_count + base_candidate_count * max(base_candidate_count - 1, 0)
    expected_candidate_rows = base_candidate_count * len(POLICY_ORDER)
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            f"missing={missing_inputs}",
            True,
        ),
        (
            "path_ready_candidate_universe_preserved",
            base_candidate_count > 0 and len(candidate_rows) == expected_candidate_rows,
            f"base={base_candidate_count}; materialized={len(candidate_rows)}; expected={expected_candidate_rows}",
            True,
        ),
        (
            "trajectory_cost_matrix_materialized",
            len(matrix_rows) == expected_matrix_rows,
            f"matrix rows={len(matrix_rows)}; expected={expected_matrix_rows}",
            True,
        ),
        (
            "repair_execution_plans_materialized",
            len(plan_rows) == len(POLICY_ORDER),
            f"plan rows={len(plan_rows)}; expected={len(POLICY_ORDER)}",
            True,
        ),
        (
            "leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in leakage_rows),
            f"failed={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}",
            True,
        ),
        (
            "scene_runtime_errors_absent",
            not scene_errors,
            f"scene_errors={len(scene_errors)}",
            True,
        ),
        (
            "execute_trajectories_now",
            False,
            "M133 materializes repair rows only; M134 should execute.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m134": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "trajectory_aware_repair_rows_materialized",
            "supported": ready,
            "claim_boundary": "M133 materializes trajectory-aware repair rows and cost matrix for the target-free case.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repaired_navigation_improvement",
            "supported": False,
            "claim_boundary": "M133 does not execute repaired trajectories; SR/SPL comparison requires M134.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final navigation claim requires execution, scale, heldout transfer, and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M133 is target-free and does not change the E006 human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision": "select_m134_trajectory_repair_execution_preflight" if ready else "repair_m133_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M133 materialization",
            "launch_long_job_now": False,
            "trajectory_repair_rows_ready": ready,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "human_intent_main_claim_ready": False,
        }
    ]


def build_policy_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": ordered[0].get("policy_role") if ordered else None,
                "candidate_rows": len(ordered),
                "path_ready_rows": sum(1 for row in ordered if row.get("path_ready")),
                "first_proposal_uid": ordered[0].get("proposal_uid") if ordered else None,
                "first_confidence": ordered[0].get("confidence") if ordered else None,
                "first_current_pose_to_candidate_geodesic_m": ordered[0].get("current_pose_to_candidate_geodesic_m")
                if ordered
                else None,
                "planned_cumulative_path_cost_m": ordered[-1].get("planned_cumulative_path_cost_m") if ordered else None,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "policy summary over materialized M133 rows; not executed trajectory evidence",
            }
        )
    return out


def build_report(
    coverage: dict[str, Any],
    policy_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M133 Target-Free Trajectory-Aware Visit-Order Repair Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Path-ready candidate universe rows: {coverage['base_path_ready_candidate_rows']}.",
            f"- Cost matrix rows: {coverage['trajectory_cost_matrix_rows']} "
            f"(expected {coverage['expected_trajectory_cost_matrix_rows']}).",
            f"- Repair candidate rows: {coverage['trajectory_repair_candidate_rows']}.",
            f"- Repair execution plan rows: {coverage['trajectory_repair_execution_plan_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Materialization",
            "",
            markdown_table(
                policy_summary_rows,
                [
                    "policy_id",
                    "candidate_rows",
                    "path_ready_rows",
                    "first_proposal_uid",
                    "first_confidence",
                    "first_current_pose_to_candidate_geodesic_m",
                    "planned_cumulative_path_cost_m",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m134", "evidence"]),
            "",
            "## Decision",
            "",
            *[f"- {row['decision']}: {row['selected_next_unit']}" for row in route_rows],
            "",
            "## Claim Boundary",
            "",
            "- M133 is a materialization smoke only.",
            "- `ObjectNav` goal/viewpoint fields remain metric-only and are not used in policy rows.",
            "- Repaired `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked.",
            "",
        ]
    )


def copy_metric_only_inputs(m129_contract: Path, output_dir: Path) -> None:
    for filename in ("episode_goal_eval_rows.jsonl", "oracle_path_rows.jsonl"):
        rows = read_jsonl(m129_contract / filename)
        write_jsonl(output_dir / filename, rows)


def write_all_outputs(
    output_dir: Path,
    coverage: dict[str, Any],
    matrix_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    input_contract_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    policy_summary_rows: list[dict[str, Any]],
    m129_contract: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "coverage.json", coverage)
    write_jsonl(output_dir / "trajectory_cost_matrix_rows.jsonl", matrix_rows)
    write_jsonl(output_dir / "trajectory_repair_candidate_rows.jsonl", candidate_rows)
    write_jsonl(output_dir / "trajectory_repair_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
    write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    write_jsonl(output_dir / "policy_summary_rows.jsonl", policy_summary_rows)

    # Alias files keep the artifact directly consumable by the M37/M130 runner family.
    write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
    copy_metric_only_inputs(m129_contract, output_dir)

    (output_dir / "report.md").write_text(
        build_report(coverage, policy_summary_rows, gate_rows, route_rows),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    m129_contract = resolve_path(args.m129_contract)
    m132_contract = resolve_path(args.m132_contract)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)

    m37 = load_m37_module()
    m129_cov = read_json(m129_contract / "coverage.json")
    m132_cov = read_json(m132_contract / "coverage.json")
    m129_candidates = read_jsonl(m129_contract / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    episode_rows = read_jsonl(m129_contract / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m129_contract / "oracle_path_rows.jsonl")
    repair_contract_rows = read_jsonl(m132_contract / "policy_repair_contract_rows.jsonl")

    missing_inputs = []
    for name, value in [
        ("m129_coverage", m129_cov),
        ("m132_coverage", m132_cov),
        ("m129_candidates", m129_candidates),
        ("episode_goal_eval_rows", episode_rows),
        ("oracle_path_rows", oracle_rows),
        ("m132_policy_repair_contract_rows", repair_contract_rows),
    ]:
        if not value:
            missing_inputs.append(name)
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    base_candidates = build_base_candidate_rows(m129_candidates)
    if not base_candidates:
        raise SystemExit("no path-ready detector-confidence candidate rows available for M133")
    adapter_episode_id = str(base_candidates[0].get("adapter_episode_id"))
    eval_row = next((row for row in episode_rows if str(row.get("adapter_episode_id")) == adapter_episode_id), {})
    start_pos = as_vec3(eval_row.get("start_position"))
    if start_pos is None:
        raise SystemExit(f"missing start_position for adapter_episode_id={adapter_episode_id}")
    scene_path = str(base_candidates[0].get("scene_docker_path") or "")
    if not scene_path:
        raise SystemExit("missing scene_docker_path in base candidates")

    scene_errors: list[dict[str, Any]] = []
    sim = None
    matrix_rows: list[dict[str, Any]] = []
    cost_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        sim = m37.make_sim(scene_path)
        matrix_rows, cost_lookup = build_cost_matrix_rows(sim, m37, start_pos, base_candidates, adapter_episode_id)
    except Exception as exc:  # pragma: no cover - Docker runtime guard
        scene_errors.append({"scene_path": scene_path, "error": repr(exc)})
    finally:
        if sim is not None:
            sim.close()

    candidate_rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        ordered = ordered_candidates_for_policy(policy_id, base_candidates, cost_lookup, adapter_episode_id)
        candidate_rows.extend(materialize_policy_candidate_rows(policy_id, ordered, cost_lookup, adapter_episode_id))

    plan_rows = build_plan_rows(candidate_rows)
    input_contract_rows = build_input_contract_rows()
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, matrix_rows)
    gate_rows = build_readiness_gate_rows(
        missing_inputs,
        len(base_candidates),
        matrix_rows,
        candidate_rows,
        plan_rows,
        leakage_rows,
        scene_errors,
    )
    ready = not any(row.get("blocks_m134") for row in gate_rows)
    claim_rows = build_claim_boundary_rows(ready)
    route_rows = build_route_decision_rows(ready)
    policy_summary_rows = build_policy_summary_rows(candidate_rows)

    expected_matrix_rows = len(base_candidates) + len(base_candidates) * max(len(base_candidates) - 1, 0)
    path_found_count = sum(1 for row in matrix_rows if row.get("path_found"))
    policy_counter = Counter(str(row.get("policy_id")) for row in candidate_rows)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m129_status": m129_cov.get("status"),
        "m132_status": m132_cov.get("status"),
        "base_path_ready_candidate_rows": len(base_candidates),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "expected_trajectory_cost_matrix_rows": expected_matrix_rows,
        "trajectory_cost_matrix_path_found_rows": path_found_count,
        "trajectory_cost_matrix_path_missing_rows": len(matrix_rows) - path_found_count,
        "trajectory_repair_candidate_rows": len(candidate_rows),
        "trajectory_repair_execution_plan_rows": len(plan_rows),
        "candidate_rows_by_policy": dict(sorted(policy_counter.items())),
        "policy_ids": POLICY_ORDER,
        "selected_repair_policy": SELECTED_REPAIR_POLICY,
        "primary_strong_baseline_policy": PRIMARY_BASELINE_POLICY,
        "historical_negative_path_policy": HISTORICAL_PATH_POLICY,
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "scene_error_rows": len(scene_errors),
        "runner_alias_candidate_file_ready": True,
        "runner_alias_plan_file_ready": True,
        "episode_goal_eval_rows_copied_for_metric": len(episode_rows),
        "oracle_path_rows_copied_for_metric": len(oracle_rows),
        "trajectory_repair_rows_ready": ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M133 materialization",
    }

    for output_dir in (out_root, derived_out_root):
        write_all_outputs(
            output_dir,
            coverage,
            matrix_rows,
            candidate_rows,
            plan_rows,
            input_contract_rows,
            leakage_rows,
            gate_rows,
            claim_rows,
            route_rows,
            policy_summary_rows,
            m129_contract,
        )

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
