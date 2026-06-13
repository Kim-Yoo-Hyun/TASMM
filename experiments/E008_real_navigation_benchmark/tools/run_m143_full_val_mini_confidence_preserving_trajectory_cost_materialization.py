#!/usr/bin/env python3
"""Materialize E008-M143 full-val-mini confidence-preserving trajectory costs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M37_PATH = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"

VERSION = "e008_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0"
READY_STATUS = "e008_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization_ready"
BLOCKED_STATUS = "e008_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization_blocked"
NEXT_UNIT = "E008-M144 full-val-mini confidence-preserving trajectory execution contract / Docker preflight"

DEFAULT_M68_ROOT = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
DEFAULT_M69_ROOT = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
DEFAULT_M72_ROOT = EXP_ROOT / "artifacts" / "E008-M72_full_val_mini_detector_policy_trajectory_contract_v0"
DEFAULT_M142_ROOT = EXP_ROOT / "artifacts" / "E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0"
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M143_full_val_mini_confidence_preserving_trajectory_cost_materialization_v0"
)

MATRIX_ID = "full_val_mini_candidate_to_candidate_geodesic_matrix_v0"
SELECTED_POLICY = "confidence_band_trajectory_tiebreak_v0"
HARD_VETO_POLICY = "confidence_preserving_hard_veto_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY = "trajectory_greedy_confidence_only_reachable_v0"
FAILED_REPAIR = "trajectory_greedy_confidence_path_repair_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
POLICY_ORDER = [
    SELECTED_POLICY,
    HARD_VETO_POLICY,
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY,
    FAILED_REPAIR,
    PATH_COST_BASELINE,
]
POLICY_ROLES = {
    SELECTED_POLICY: "selected_confidence_preserving_method",
    HARD_VETO_POLICY: "hard_feasibility_veto_ablation",
    PRIMARY_BASELINE: "protected_detector_confidence_baseline",
    CONFIDENCE_ONLY: "strong_confidence_only_baseline",
    FAILED_REPAIR: "negative_prior_repair_baseline",
    PATH_COST_BASELINE: "negative_path_cost_baseline",
}
CONFIDENCE_BAND_ABS = 0.03
MIN_PATH_ADVANTAGE_M = 1.0

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
    parser.add_argument("--m68-root", default=str(DEFAULT_M68_ROOT))
    parser.add_argument("--m69-root", default=str(DEFAULT_M69_ROOT))
    parser.add_argument("--m72-root", default=str(DEFAULT_M72_ROOT))
    parser.add_argument("--m142-root", default=str(DEFAULT_M142_ROOT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    parser.add_argument("--limit-episodes", type=int, default=None)
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


def as_vec3(value: object) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    out = [finite_float(part) for part in value]
    if any(part is None for part in out):
        return None
    return [float(part) for part in out]


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
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
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


def adapter_token(adapter_episode_id: str) -> str:
    return adapter_episode_id.replace("::", "__")


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m143::{adapter_token(adapter_episode_id)}::{policy_id}"


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m143::{adapter_token(adapter_episode_id)}"


def start_node_uid(adapter_episode_id: str) -> str:
    return f"episode_start::{adapter_episode_id}"


def candidate_node_uid(row: dict[str, Any]) -> str:
    return f"candidate::{row.get('proposal_uid')}"


def candidate_position(row: dict[str, Any]) -> list[float] | None:
    return as_vec3(
        row.get("execution_stop_position_m")
        or row.get("candidate_stop_position_m")
        or row.get("snapped_position_m")
    )


def confidence_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    return (
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or row.get("candidate_rank") or 10**9),
        str(row.get("proposal_uid")),
    )


def source_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    return (
        finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or row.get("candidate_rank") or 10**9),
        str(row.get("proposal_uid")),
    )


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def is_path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) or row.get("navmesh_validation_status") == "candidate_path_ready"


def build_visit_index(visit_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    primary_rows = [row for row in visit_rows if row.get("policy_id") == PRIMARY_BASELINE]
    for row in sorted(primary_rows, key=lambda item: (str(item.get("adapter_episode_id")), int(item.get("visit_rank") or 10**9))):
        index.setdefault(str(row.get("proposal_uid")), row)
    return index


def build_base_candidate_rows(
    nav_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    limit_episodes: int | None,
) -> list[dict[str, Any]]:
    visit_index = build_visit_index(visit_rows)
    goal_episode_ids = {str(row.get("adapter_episode_id")) for row in goal_rows}
    ready_nav_rows = [
        row
        for row in nav_rows
        if is_path_ready(row)
        and str(row.get("adapter_episode_id")) in goal_episode_ids
        and str(row.get("proposal_uid")) in visit_index
    ]
    selected_episode_ids = sorted({str(row.get("adapter_episode_id")) for row in ready_nav_rows})
    if limit_episodes is not None:
        selected_episode_ids = selected_episode_ids[:limit_episodes]
    selected_episode_set = set(selected_episode_ids)

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(ready_nav_rows, key=lambda item: (str(item.get("adapter_episode_id")), confidence_sort_key(item))):
        adapter_episode_id = str(row.get("adapter_episode_id"))
        if adapter_episode_id not in selected_episode_set:
            continue
        proposal_uid = str(row.get("proposal_uid"))
        if proposal_uid in seen:
            continue
        visit = visit_index[proposal_uid]
        stop = as_vec3(row.get("snapped_position_m"))
        clean = dict(row)
        for field in BLOCKED_POLICY_FIELDS:
            clean.pop(field, None)
        clean.update(
            {
                "version": VERSION,
                "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
                "candidate_rank_m09": int(visit.get("candidate_rank_m09") or row.get("candidate_rank") or 10**9),
                "candidate_position_m": as_vec3(row.get("centroid_world_m")),
                "candidate_stop_position_m": stop,
                "execution_stop_position_m": stop,
                "source_to_candidate_path_cost_m": finite_float(visit.get("source_to_candidate_path_cost_m"))
                if finite_float(visit.get("source_to_candidate_path_cost_m")) is not None
                else finite_float(row.get("source_to_snapped_geodesic_m")),
                "cumulative_known_path_cost_m": finite_float(visit.get("cumulative_known_path_cost_m")),
                "path_ready": True,
                "candidate_usable_for_path_smoke": True,
                "blocked_candidate_for_path_policy": False,
                "query_label_compatible": True,
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "primary_budget_cap": "full_ranked",
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M143 base candidate row from M68/M69; ObjectNav goal/viewpoint fields are excluded from policy input.",
            }
        )
        out.append(clean)
        seen.add(proposal_uid)
    return out


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


def build_cost_matrix_rows(
    m37: Any,
    goal_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    goal_index = {str(row.get("adapter_episode_id")): row for row in goal_rows}
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_episode[str(row.get("adapter_episode_id"))].append(row)

    rows: list[dict[str, Any]] = []
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    scene_errors: list[dict[str, Any]] = []
    sim_by_scene: dict[str, Any] = {}

    def add_path(
        sim: Any,
        adapter_episode_id: str,
        first: dict[str, Any],
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
            "scan_id": first.get("scan_id"),
            "scene_key": first.get("scene_key"),
            "object_category": first.get("object_category"),
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
            "claim_boundary": "M143 cost matrix uses episode start and candidate stop positions only; ObjectNav goal/viewpoints remain metric-only.",
        }
        rows.append(row)
        lookup[(from_uid, to_uid)] = row

    try:
        for adapter_episode_id, episode_candidates in sorted(by_episode.items()):
            episode_candidates = sorted(episode_candidates, key=confidence_sort_key)
            first = episode_candidates[0]
            goal = goal_index.get(adapter_episode_id, {})
            start_pos = as_vec3(goal.get("start_position"))
            scene_path = str(first.get("scene_docker_path") or "")
            if start_pos is None or not scene_path:
                scene_errors.append(
                    {
                        "adapter_episode_id": adapter_episode_id,
                        "scene_path": scene_path,
                        "error": "missing start_position or scene_docker_path",
                    }
                )
                continue
            if scene_path not in sim_by_scene:
                sim_by_scene[scene_path] = m37.make_sim(scene_path)
            sim = sim_by_scene[scene_path]
            start_uid = start_node_uid(adapter_episode_id)
            for candidate in episode_candidates:
                pos = candidate_position(candidate)
                if pos is None:
                    continue
                add_path(
                    sim,
                    adapter_episode_id,
                    first,
                    start_uid,
                    "episode_start",
                    start_pos,
                    candidate_node_uid(candidate),
                    "candidate",
                    pos,
                    to_proposal_uid=str(candidate.get("proposal_uid")),
                )
            for src in episode_candidates:
                src_pos = candidate_position(src)
                if src_pos is None:
                    continue
                for dst in episode_candidates:
                    if src.get("proposal_uid") == dst.get("proposal_uid"):
                        continue
                    dst_pos = candidate_position(dst)
                    if dst_pos is None:
                        continue
                    add_path(
                        sim,
                        adapter_episode_id,
                        first,
                        candidate_node_uid(src),
                        "candidate",
                        src_pos,
                        candidate_node_uid(dst),
                        "candidate",
                        dst_pos,
                        from_proposal_uid=str(src.get("proposal_uid")),
                        to_proposal_uid=str(dst.get("proposal_uid")),
                    )
    finally:
        for sim in sim_by_scene.values():
            sim.close()
    return rows, lookup, scene_errors


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


def greedy_confidence_path_repair_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(candidates)
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
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
                    score,
                )
            )
        selected_item = sorted(scored)[0]
        selected = selected_item[-2]
        found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        events.append(
            {
                "reason": "prior_trajectory_greedy_confidence_path_repair",
                "selected_current_path_found": found,
                "selected_current_path_cost_m": cost,
                "trajectory_repair_score": selected_item[-1],
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if found:
            current_uid = candidate_node_uid(selected)
        step_idx += 1
    return ordered, events


def confidence_band_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
    confidence_band_abs: float,
    min_path_advantage_m: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(sorted(candidates, key=confidence_sort_key))
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []
    while remaining:
        detector_top = sorted(remaining, key=confidence_sort_key)[0]
        top_conf = finite_float(detector_top.get("confidence")) or 0.0
        band = [
            row
            for row in sorted(remaining, key=confidence_sort_key)
            if top_conf - (finite_float(row.get("confidence")) or -math.inf) <= confidence_band_abs
        ]
        feasible_band: list[tuple[dict[str, Any], float | None]] = []
        for row in band:
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
            if found and not blocked:
                feasible_band.append((row, cost))
        selected = detector_top
        reason = "detector_confidence_preserved"
        hard_veto = False
        path_advantage = 0.0
        if feasible_band:
            detector_found, detector_cost, _, _ = matrix_cost(
                cost_lookup,
                current_uid,
                candidate_node_uid(detector_top),
            )
            best_path_row, best_path_cost = sorted(
                feasible_band,
                key=lambda item: (
                    item[1] if item[1] is not None else math.inf,
                    -(finite_float(item[0].get("confidence")) or -math.inf),
                    int(item[0].get("candidate_rank_m09") or 10**9),
                    str(item[0].get("proposal_uid")),
                ),
            )[0]
            if not detector_found or detector_top.get("blocked_candidate_for_path_policy"):
                selected = best_path_row
                reason = "hard_feasibility_veto_on_detector_top"
                hard_veto = selected.get("proposal_uid") != detector_top.get("proposal_uid")
            elif detector_cost is not None and best_path_cost is not None:
                path_advantage = detector_cost - best_path_cost
                if (
                    best_path_row.get("proposal_uid") != detector_top.get("proposal_uid")
                    and path_advantage >= min_path_advantage_m
                ):
                    selected = best_path_row
                    reason = "within_band_path_tiebreak"
        else:
            feasible_remaining = []
            for row in sorted(remaining, key=confidence_sort_key):
                found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
                blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
                if found and not blocked:
                    feasible_remaining.append((row, cost))
            if feasible_remaining:
                selected, _ = sorted(
                    feasible_remaining,
                    key=lambda item: (
                        -(finite_float(item[0].get("confidence")) or -math.inf),
                        item[1] if item[1] is not None else math.inf,
                        int(item[0].get("candidate_rank_m09") or 10**9),
                        str(item[0].get("proposal_uid")),
                    ),
                )[0]
                reason = "hard_feasibility_veto_on_infeasible_band"
                hard_veto = selected.get("proposal_uid") != detector_top.get("proposal_uid")
        selected_found, selected_cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        audit_events.append(
            {
                "detector_top_proposal_uid": detector_top.get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence": top_conf,
                "selected_confidence": finite_float(selected.get("confidence")),
                "confidence_delta_from_top": top_conf - (finite_float(selected.get("confidence")) or 0.0),
                "selected_current_path_found": selected_found,
                "selected_current_path_cost_m": selected_cost,
                "reason": reason,
                "hard_feasibility_veto_applied": hard_veto,
                "confidence_band_abs": confidence_band_abs,
                "min_path_advantage_m": min_path_advantage_m,
                "path_advantage_m": path_advantage,
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if selected_found:
            current_uid = candidate_node_uid(selected)
    return ordered, audit_events


def hard_veto_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(sorted(candidates, key=confidence_sort_key))
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []
    while remaining:
        detector_top = sorted(remaining, key=confidence_sort_key)[0]
        feasible_remaining = []
        for row in sorted(remaining, key=confidence_sort_key):
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            blocked = bool(row.get("blocked_candidate_for_path_policy")) or not bool(row.get("path_ready"))
            if found and not blocked:
                feasible_remaining.append((row, cost))
        selected = detector_top
        reason = "detector_confidence_preserved"
        if feasible_remaining:
            detector_found, _, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(detector_top))
            if not detector_found or detector_top.get("blocked_candidate_for_path_policy"):
                selected = feasible_remaining[0][0]
                reason = "hard_feasibility_veto_on_detector_top"
        found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        audit_events.append(
            {
                "detector_top_proposal_uid": detector_top.get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence": finite_float(detector_top.get("confidence")),
                "selected_confidence": finite_float(selected.get("confidence")),
                "confidence_delta_from_top": (finite_float(detector_top.get("confidence")) or 0.0)
                - (finite_float(selected.get("confidence")) or 0.0),
                "selected_current_path_found": found,
                "selected_current_path_cost_m": cost,
                "reason": reason,
                "hard_feasibility_veto_applied": selected.get("proposal_uid") != detector_top.get("proposal_uid"),
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if found:
            current_uid = candidate_node_uid(selected)
    return ordered, audit_events


def order_candidates_for_episode(
    policy_id: str,
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
    if policy_id == SELECTED_POLICY:
        return confidence_band_order(
            candidates,
            cost_lookup,
            adapter_episode_id,
            CONFIDENCE_BAND_ABS,
            MIN_PATH_ADVANTAGE_M,
        )
    if policy_id == HARD_VETO_POLICY:
        return hard_veto_order(candidates, cost_lookup, adapter_episode_id)
    if policy_id in {PRIMARY_BASELINE, CONFIDENCE_ONLY}:
        return sorted(candidates, key=confidence_sort_key), None
    if policy_id == FAILED_REPAIR:
        return greedy_confidence_path_repair_order(candidates, cost_lookup, adapter_episode_id)
    if policy_id == PATH_COST_BASELINE:
        return sorted(candidates, key=source_cost_sort_key), None
    raise ValueError(f"unknown policy_id: {policy_id}")


def materialize_policy_rows(
    policy_id: str,
    ordered_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
    audit_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    benchmark_uid = build_benchmark_uid(adapter_episode_id)
    current_uid = start_node_uid(adapter_episode_id)
    cumulative = 0.0
    event_by_rank = {idx + 1: event for idx, event in enumerate(audit_events or [])}
    out: list[dict[str, Any]] = []
    for rank, source in enumerate(ordered_candidates, start=1):
        to_uid = candidate_node_uid(source)
        found, cost, point_count, path_error = matrix_cost(cost_lookup, current_uid, to_uid)
        if found and cost is not None:
            cumulative += cost
        confidence = finite_float(source.get("confidence")) or 0.0
        source_cost = finite_float(source.get("source_to_candidate_path_cost_m"))
        event = event_by_rank.get(rank, {})
        if policy_id in {SELECTED_POLICY, HARD_VETO_POLICY, PRIMARY_BASELINE, CONFIDENCE_ONLY}:
            score = confidence
            if policy_id == SELECTED_POLICY and event.get("reason") == "within_band_path_tiebreak":
                score += 0.0001
        elif policy_id == PATH_COST_BASELINE:
            score = -1.0 * (source_cost if source_cost is not None else math.inf)
        else:
            score = event.get("trajectory_repair_score")
            if score is None:
                score = confidence - (cost if cost is not None else 1e6)
        row = dict(source)
        for field in BLOCKED_POLICY_FIELDS:
            row.pop(field, None)
        row.update(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": benchmark_uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE,
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_visit_uid": f"{plan_uid}::{rank:04d}",
                "visit_rank": rank,
                "ranking_score": score,
                "candidate_order_component": policy_id,
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "primary_budget_cap": "full_ranked",
                "trajectory_cost_matrix_id": MATRIX_ID,
                "confidence_preserving_repair_materialized": policy_id == SELECTED_POLICY,
                "trajectory_repair_materialized": policy_id == FAILED_REPAIR,
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
                "confidence_band_reason": event.get("reason") if event else None,
                "hard_feasibility_veto_applied": bool(event.get("hard_feasibility_veto_applied")) if event else False,
                "confidence_delta_from_top": event.get("confidence_delta_from_top") if event else 0.0,
                "confidence_order_override_allowed": bool(
                    event
                    and event.get("reason") in {"within_band_path_tiebreak", "hard_feasibility_veto_on_detector_top"}
                ),
                "uses_trajectory_cost_matrix_for_policy": policy_id
                in {SELECTED_POLICY, HARD_VETO_POLICY, FAILED_REPAIR},
                "uses_task_context_for_decision": False,
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M143 materializes full-val-mini confidence-preserving rows only; SR/SPL requires M144/M145 execution.",
            }
        )
        out.append(row)
        if found:
            current_uid = to_uid
    return out


def build_all_policy_rows(
    base_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in base_candidates:
        by_episode[str(row.get("adapter_episode_id"))].append(row)
    out: list[dict[str, Any]] = []
    for adapter_episode_id, candidates in sorted(by_episode.items()):
        candidates = sorted(candidates, key=confidence_sort_key)
        for policy_id in POLICY_ORDER:
            ordered, events = order_candidates_for_episode(policy_id, candidates, cost_lookup, adapter_episode_id)
            out.extend(materialize_policy_rows(policy_id, ordered, cost_lookup, adapter_episode_id, events))
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
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE,
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
                "planned_cumulative_path_cost_m": rows[-1].get("planned_cumulative_path_cost_m"),
                "first_proposal_uid": first.get("proposal_uid"),
                "first_confidence": first.get("confidence"),
                "first_current_pose_to_candidate_geodesic_m": first.get("current_pose_to_candidate_geodesic_m"),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "confidence_preserving_candidate_file": "confidence_preserving_candidate_rows.jsonl",
                "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m145_full_val_mini_confidence_preserving_trajectory_execution.py",
                "runner_input_ready": bool(path_ready_rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": True,
                "start_state_source": "ObjectNav episode start state from M72 episode_goal_eval_rows; goal/viewpoints are metric-only",
                "uses_trajectory_cost_matrix_for_policy": policy_id in {SELECTED_POLICY, HARD_VETO_POLICY, FAILED_REPAIR},
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
                "claim_boundary": "M143 fixes full-val-mini trajectory inputs only; final SR/SPL requires M144/M145.",
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


def build_policy_order_audit_rows(
    candidate_rows: list[dict[str, Any]],
    base_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in base_candidates:
        base_by_episode[str(row.get("adapter_episode_id"))].append(row)
    for row in candidate_rows:
        rows_by_key[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)

    out: list[dict[str, Any]] = []
    for adapter_episode_id, base_rows in sorted(base_by_episode.items()):
        detector_order = [str(row.get("proposal_uid")) for row in sorted(base_rows, key=confidence_sort_key)]
        detector_rank = {proposal_uid: idx + 1 for idx, proposal_uid in enumerate(detector_order)}
        detector_conf = {
            str(row.get("proposal_uid")): finite_float(row.get("confidence")) or 0.0 for row in base_rows
        }
        for policy_id in POLICY_ORDER:
            policy_rows = sorted(
                rows_by_key.get((adapter_episode_id, policy_id), []),
                key=lambda row: int(row.get("visit_rank") or 10**9),
            )
            outside_band_overrides = 0
            hard_veto_count = 0
            first_rank_flip = None
            for idx, row in enumerate(policy_rows, start=1):
                proposal_uid = str(row.get("proposal_uid"))
                expected_uid = detector_order[idx - 1] if idx <= len(detector_order) else None
                if expected_uid != proposal_uid and first_rank_flip is None:
                    first_rank_flip = {
                        "visit_rank": idx,
                        "expected_detector_proposal_uid": expected_uid,
                        "selected_proposal_uid": proposal_uid,
                    }
                stronger_remaining = [
                    other_uid
                    for other_uid in detector_order
                    if detector_rank[other_uid] > idx
                    and detector_conf[other_uid] > detector_conf.get(proposal_uid, 0.0) + CONFIDENCE_BAND_ABS
                ]
                if policy_id == SELECTED_POLICY and stronger_remaining and not row.get("hard_feasibility_veto_applied"):
                    outside_band_overrides += 1
                if row.get("hard_feasibility_veto_applied"):
                    hard_veto_count += 1
            out.append(
                {
                    "version": VERSION,
                    "row_type": "policy_order_audit",
                    "adapter_episode_id": adapter_episode_id,
                    "policy_id": policy_id,
                    "policy_role": POLICY_ROLES.get(policy_id),
                    "candidate_rows": len(policy_rows),
                    "detector_order_identical": [str(row.get("proposal_uid")) for row in policy_rows] == detector_order,
                    "first_rank_flip": first_rank_flip,
                    "hard_feasibility_veto_count": hard_veto_count,
                    "outside_confidence_band_override_count": outside_band_overrides,
                    "confidence_band_violation_count": outside_band_overrides,
                    "confidence_band_abs": CONFIDENCE_BAND_ABS,
                    "audit_pass": policy_id != SELECTED_POLICY or outside_band_overrides == 0,
                }
            )
    return out


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads = [
        ("confidence_preserving_candidate_rows", candidate_rows),
        ("confidence_preserving_execution_plan_rows", plan_rows),
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
    base_candidates: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    scene_errors: list[dict[str, Any]],
    limit_episodes: int | None,
) -> list[dict[str, Any]]:
    by_episode = Counter(str(row.get("adapter_episode_id")) for row in base_candidates)
    expected_matrix_rows = sum(count * count for count in by_episode.values())
    expected_candidate_rows = len(base_candidates) * len(POLICY_ORDER)
    expected_plan_rows = len(by_episode) * len(POLICY_ORDER)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            f"missing={missing_inputs}",
            True,
        ),
        (
            "full_scale_not_episode_limited",
            limit_episodes is None,
            f"limit_episodes={limit_episodes}",
            True,
        ),
        (
            "source_ready_denominator_preserved",
            len(by_episode) == 30 and len(base_candidates) == 900,
            f"episodes={len(by_episode)}; base_candidates={len(base_candidates)}; expected=30/900",
            True,
        ),
        (
            "trajectory_cost_matrix_materialized",
            len(matrix_rows) == expected_matrix_rows,
            f"matrix rows={len(matrix_rows)}; expected={expected_matrix_rows}",
            True,
        ),
        (
            "candidate_policy_rows_materialized",
            len(candidate_rows) == expected_candidate_rows,
            f"candidate rows={len(candidate_rows)}; expected={expected_candidate_rows}",
            True,
        ),
        (
            "same_candidate_count_per_policy",
            set(candidate_counts.values()) == {len(base_candidates)} and len(candidate_counts) == len(POLICY_ORDER),
            f"counts={dict(sorted(candidate_counts.items()))}",
            True,
        ),
        (
            "execution_plans_materialized",
            len(plan_rows) == expected_plan_rows,
            f"plan rows={len(plan_rows)}; expected={expected_plan_rows}",
            True,
        ),
        (
            "confidence_band_audit_pass",
            all(row.get("audit_pass") for row in audit_rows if row.get("policy_id") == SELECTED_POLICY),
            f"selected violations={sum(int(row.get('confidence_band_violation_count') or 0) for row in audit_rows if row.get('policy_id') == SELECTED_POLICY)}",
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
            "M143 materializes trajectory-cost and runner-compatible rows only; M144/M145 should execute.",
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
            "blocks_m144": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "full_val_mini_confidence_preserving_rows_materialized",
            "supported": ready,
            "claim_boundary": "M143 materializes the frozen M142 confidence-preserving policy suite over 30 full-val-mini episodes and 900 path-ready candidates.",
        },
        {
            "version": VERSION,
            "claim_id": "principle_driven_not_conclusion_fitted",
            "supported": ready,
            "claim_boundary": "M143 follows the M130/M135 failure diagnosis: trajectory cost is only a confidence-band tie-break / feasibility guard, not a replacement for detector confidence.",
        },
        {
            "version": VERSION,
            "claim_id": "executed_navigation_improvement",
            "supported": False,
            "claim_boundary": "M143 does not execute Habitat trajectories; M144/M145 are required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final navigation claim still needs execution, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M143 is target-free and does not change the E006-M08 human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m143_selected_next",
            "decision": "prepare_m144_docker_execution_contract" if ready else "repair_m143_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M143 materialization",
            "launch_long_job_now": False,
            "reason": "M143 has runner-compatible full-val-mini confidence-preserving rows; M144 should preflight Docker execution."
            if ready
            else "One or more materialization gates failed.",
        }
    ]


def build_policy_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for policy_id, policy_rows in sorted(by_policy.items()):
        ordered = sorted(
            policy_rows,
            key=lambda row: (str(row.get("adapter_episode_id")), int(row.get("visit_rank") or 10**9)),
        )
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id),
                "episode_rows": len({str(row.get("adapter_episode_id")) for row in ordered}),
                "candidate_rows": len(ordered),
                "path_ready_rows": sum(1 for row in ordered if row.get("path_ready")),
                "planned_cumulative_path_cost_m_mean": mean(
                    [
                        row.get("planned_cumulative_path_cost_m")
                        for row in ordered
                        if int(row.get("visit_rank") or 0)
                        == max(
                            int(other.get("visit_rank") or 0)
                            for other in ordered
                            if other.get("policy_plan_uid") == row.get("policy_plan_uid")
                        )
                    ]
                ),
                "hard_feasibility_veto_rows": sum(1 for row in ordered if row.get("hard_feasibility_veto_applied")),
                "confidence_band_override_rows": sum(
                    1 for row in ordered if row.get("confidence_band_reason") == "within_band_path_tiebreak"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "M143 policy summary over materialized rows; not executed trajectory evidence.",
            }
        )
    return rows


def copy_metric_only_rows(m72_root: Path, out_root: Path, derived_out_root: Path) -> tuple[int, int]:
    episode_rows = read_jsonl(m72_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m72_root / "oracle_path_rows.jsonl")
    for output_dir in (out_root, derived_out_root):
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
    return len(episode_rows), len(oracle_rows)


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    audit_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M143 Full-Val-Mini Confidence-Preserving Trajectory-Cost Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Base path-ready candidate rows: {coverage['base_path_ready_candidate_rows']}.",
            f"- Episode rows: {coverage['episode_rows']}.",
            f"- Cost matrix rows: {coverage['trajectory_cost_matrix_rows']} "
            f"(expected {coverage['expected_trajectory_cost_matrix_rows']}).",
            f"- Candidate-policy rows: {coverage['confidence_preserving_candidate_rows']}.",
            f"- Execution plan rows: {coverage['confidence_preserving_execution_plan_rows']}.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Selected policy confidence-band violations: {coverage['selected_policy_confidence_band_violations']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "candidate_rows",
                    "planned_cumulative_path_cost_m_mean",
                    "hard_feasibility_veto_rows",
                    "confidence_band_override_rows",
                ],
            ),
            "",
            "## Order Audit Summary",
            "",
            markdown_table(
                audit_summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "detector_order_identical_rows",
                    "hard_feasibility_veto_count",
                    "confidence_band_violation_count",
                    "audit_pass",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m144", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M143 supports full-val-mini row/materialization readiness only.",
            "- M143 does not execute trajectories or support final real navigation `SR` / `SPL`.",
            "- The selected policy keeps detector confidence protected and only uses trajectory cost as a bounded tie-break / feasibility guard.",
            "",
        ]
    )


def summarize_audit_rows(audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(by_policy.items()):
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "episode_rows": len(rows),
                "detector_order_identical_rows": sum(1 for row in rows if row.get("detector_order_identical")),
                "hard_feasibility_veto_count": sum(int(row.get("hard_feasibility_veto_count") or 0) for row in rows),
                "confidence_band_violation_count": sum(
                    int(row.get("confidence_band_violation_count") or 0) for row in rows
                ),
                "audit_pass": all(row.get("audit_pass") for row in rows),
            }
        )
    return out


def main() -> None:
    args = parse_args()
    m68_root = resolve_path(args.m68_root)
    m69_root = resolve_path(args.m69_root)
    m72_root = resolve_path(args.m72_root)
    m142_root = resolve_path(args.m142_root)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m37 = load_m37_module()
    m68_cov = read_json(m68_root / "coverage.json")
    m69_cov = read_json(m69_root / "coverage.json")
    m72_cov = read_json(m72_root / "coverage.json")
    m142_cov = read_json(m142_root / "coverage.json")
    nav_rows = read_jsonl(m68_root / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(m69_root / "candidate_visit_order_rows.jsonl")
    goal_rows = read_jsonl(m72_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m72_root / "oracle_path_rows.jsonl")

    missing_inputs = [
        str(path.relative_to(ROOT))
        for path, rows in [
            (m68_root / "coverage.json", [m68_cov] if m68_cov else []),
            (m69_root / "coverage.json", [m69_cov] if m69_cov else []),
            (m72_root / "coverage.json", [m72_cov] if m72_cov else []),
            (m142_root / "coverage.json", [m142_cov] if m142_cov else []),
            (m68_root / "candidate_navmesh_validation_rows.jsonl", nav_rows),
            (m69_root / "candidate_visit_order_rows.jsonl", visit_rows),
            (m72_root / "episode_goal_eval_rows.jsonl", goal_rows),
            (m72_root / "oracle_path_rows.jsonl", oracle_rows),
        ]
        if not rows
    ]
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    base_candidates = build_base_candidate_rows(nav_rows, visit_rows, goal_rows, args.limit_episodes)
    matrix_rows, cost_lookup, scene_errors = build_cost_matrix_rows(m37, goal_rows, base_candidates)
    candidate_rows = build_all_policy_rows(base_candidates, cost_lookup)
    plan_rows = build_plan_rows(candidate_rows)
    input_contract_rows = build_input_contract_rows()
    audit_rows = build_policy_order_audit_rows(candidate_rows, base_candidates)
    audit_summary_rows = summarize_audit_rows(audit_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, matrix_rows)
    gate_rows = build_readiness_gate_rows(
        missing_inputs,
        base_candidates,
        matrix_rows,
        candidate_rows,
        plan_rows,
        leakage_rows,
        audit_rows,
        scene_errors,
        args.limit_episodes,
    )
    ready = not any(row.get("blocks_m144") for row in gate_rows)
    claim_rows = build_claim_boundary_rows(ready)
    route_rows = build_route_decision_rows(ready)
    summary_rows = build_policy_summary_rows(candidate_rows)

    episode_count = len({str(row.get("adapter_episode_id")) for row in base_candidates})
    expected_matrix_rows = sum(
        count * count for count in Counter(str(row.get("adapter_episode_id")) for row in base_candidates).values()
    )
    path_found_count = sum(1 for row in matrix_rows if row.get("path_found"))
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    selected_audit_rows = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m68_status": m68_cov.get("status"),
        "m69_status": m69_cov.get("status"),
        "m72_status": m72_cov.get("status"),
        "m142_status": m142_cov.get("status"),
        "episode_rows": episode_count,
        "scene_count": len({str(row.get("scene_key")) for row in base_candidates}),
        "category_count": len({str(row.get("object_category")) for row in base_candidates}),
        "base_path_ready_candidate_rows": len(base_candidates),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "expected_trajectory_cost_matrix_rows": expected_matrix_rows,
        "trajectory_cost_matrix_path_found_rows": path_found_count,
        "trajectory_cost_matrix_path_missing_rows": len(matrix_rows) - path_found_count,
        "confidence_preserving_candidate_rows": len(candidate_rows),
        "confidence_preserving_execution_plan_rows": len(plan_rows),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "policy_ids": POLICY_ORDER,
        "selected_policy_id": SELECTED_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE,
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "min_path_advantage_m": MIN_PATH_ADVANTAGE_M,
        "selected_policy_hard_veto_rows": sum(
            int(row.get("hard_feasibility_veto_count") or 0) for row in selected_audit_rows
        ),
        "selected_policy_confidence_band_violations": sum(
            int(row.get("confidence_band_violation_count") or 0) for row in selected_audit_rows
        ),
        "policy_order_audit_rows": len(audit_rows),
        "policy_order_audit_pass": all(row.get("audit_pass") for row in audit_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "scene_error_rows": len(scene_errors),
        "episode_goal_eval_rows_copied_for_metric": len(goal_rows),
        "oracle_path_rows_copied_for_metric": len(oracle_rows),
        "runner_alias_candidate_file_ready": True,
        "runner_alias_plan_file_ready": True,
        "materialization_ready": ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "limit_episodes": args.limit_episodes,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "base_candidate_rows.jsonl", base_candidates)
        write_jsonl(output_dir / "trajectory_cost_matrix_rows.jsonl", matrix_rows)
        write_jsonl(output_dir / "confidence_preserving_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "confidence_preserving_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "policy_order_audit_rows.jsonl", audit_rows)
        write_jsonl(output_dir / "policy_order_audit_summary_rows.jsonl", audit_summary_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", summary_rows)
        write_json(output_dir / "scene_materialization_meta.json", {"scene_errors": scene_errors})
    copy_metric_only_rows(m72_root, out_root, derived_out_root)
    (out_root / "report.md").write_text(
        build_report(coverage, summary_rows, audit_summary_rows, gate_rows),
        encoding="utf-8",
    )
    shutil.copy2(out_root / "report.md", derived_out_root / "report.md")

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
