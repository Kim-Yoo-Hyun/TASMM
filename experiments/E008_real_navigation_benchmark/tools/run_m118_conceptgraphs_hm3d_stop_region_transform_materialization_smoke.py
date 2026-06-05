#!/usr/bin/env python3
"""Materialize non-oracle stop-region candidates for the M117 ConceptGraphs HM3D route."""

from __future__ import annotations

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

M10_TOOL = EXP_ROOT / "tools" / "run_m10_detector_candidate_navmesh_validation.py"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M111_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M113_DIR = EXP_ROOT / "artifacts" / "E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0"
M117_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"
)

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0"
)

VERSION = "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0"
READY_STATUS = "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_ready"
WARNING_STATUS = "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_ready_with_budget_warning"
BLOCKED_STATUS = "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_blocked"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

POLICY_ID = "stop_region_path_cost_budget5_v0"
BASELINE_POLICY_ID = "source_candidate_only_frozen_rank_v0"
NEXT_INTERPRET_UNIT = "E008-M119 stop-region transform result interpretation and source-coverage route decision"
NEXT_SOURCE_COVERAGE_UNIT = "E008-M119 ConceptGraphs/HM3D source-coverage external-or-visibility preflight"

BASE_STANDOFF_M = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50]
DIRECTIONS_XZ = [
    (1.0, 0.0, "east"),
    (-1.0, 0.0, "west"),
    (0.0, 1.0, "north"),
    (0.0, -1.0, "south"),
    (1.0, 1.0, "north_east"),
    (1.0, -1.0, "south_east"),
    (-1.0, 1.0, "north_west"),
    (-1.0, -1.0, "south_west"),
]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) >= 3 and all(finite_float(value) is not None for value in vec[:3])


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    assert isinstance(vec, list)
    return [float(vec[0]), float(vec[1]), float(vec[2])]


def dist_xz(a: list[float], b: list[float]) -> float:
    return float(math.sqrt((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2))


def normalize_xz(dx: float, dz: float) -> tuple[float, float]:
    norm = math.sqrt(dx * dx + dz * dz)
    if norm <= 1e-9:
        return 0.0, 0.0
    return dx / norm, dz / norm


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def build_source_candidate_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in ("proposal_uid", "candidate_uid", "raw_candidate_uid"):
            value = row.get(key)
            if value is not None:
                out[str(value)] = row
    return out


def build_stop_region_candidate_rows(
    contract_rows: list[dict[str, Any]],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contract in contract_rows:
        source_uid = str(contract.get("source_candidate_uid"))
        source = source_lookup.get(source_uid, {})
        center = as_vec3(source.get("candidate_center_xyz"))
        extent = as_vec3(source.get("candidate_extent_xyz")) or as_vec3(contract.get("candidate_extent_xyz"))
        snapped = as_vec3(source.get("snapped_position_m"))
        source_position = as_vec3(source.get("source_position"))
        if center is None:
            center = as_vec3(contract.get("best_goal_candidate_center_xyz"))
        if extent is None:
            extent = [0.5, 0.5, 0.5]
        if snapped is None:
            snapped = as_vec3(contract.get("best_goal_candidate_snapped_position_m"))
        floor_y = snapped[1] if snapped else (source_position[1] if source_position else center[1])
        object_radius_xz = max(abs(extent[0]), abs(extent[2])) * 0.5

        directions = list(DIRECTIONS_XZ)
        if source_position is not None:
            sx, sz = normalize_xz(source_position[0] - center[0], source_position[2] - center[2])
            if sx != 0.0 or sz != 0.0:
                directions.append((sx, sz, "source_facing"))

        rank = 0
        seen_positions: set[tuple[int, int]] = set()
        for dx, dz, direction_name in directions:
            ux, uz = normalize_xz(dx, dz)
            if ux == 0.0 and uz == 0.0:
                continue
            for standoff_m in BASE_STANDOFF_M:
                radius_m = object_radius_xz + standoff_m
                x = center[0] + ux * radius_m
                z = center[2] + uz * radius_m
                key = (round(x * 1000), round(z * 1000))
                if key in seen_positions:
                    continue
                seen_positions.add(key)
                rank += 1
                rows.append(
                    {
                        "version": VERSION,
                        "row_type": "stop_region_candidate",
                        "query_uid": contract.get("query_uid"),
                        "adapter_episode_id": contract.get("adapter_episode_id"),
                        "scan_id": contract.get("scan_id"),
                        "scene_key": contract.get("scene_key"),
                        "object_category": contract.get("object_category"),
                        "label_canonical": contract.get("object_category"),
                        "source_candidate_uid": source_uid,
                        "proposal_uid": (
                            f"{source_uid}:stop_region:{direction_name}:r{radius_m:.2f}".replace(" ", "_")
                        ),
                        "candidate_uid": (
                            f"{source_uid}:stop_region:{direction_name}:r{radius_m:.2f}".replace(" ", "_")
                        ),
                        "raw_candidate_uid": source_uid,
                        "candidate_rank": rank,
                        "rank": rank,
                        "candidate_scope": "candidate_geometry_radial_stop_region_v0",
                        "transform_id": "candidate_geometry_radial_stop_region_v0",
                        "direction_name": direction_name,
                        "unit_direction_xz": [ux, uz],
                        "standoff_m": standoff_m,
                        "object_radius_xz_m": object_radius_xz,
                        "radial_distance_from_object_center_xz_m": radius_m,
                        "candidate_center_xyz": [x, floor_y, z],
                        "centroid_world_m": [x, floor_y, z],
                        "source_object_center_xyz": center,
                        "source_object_extent_xyz": extent,
                        "source_object_snapped_position_m": snapped,
                        "source_candidate_rank": contract.get("source_candidate_rank"),
                        "source_candidate_min_policy_rank": contract.get("source_candidate_min_policy_rank"),
                        "source_candidate_semantic_score": source.get("semantic_score"),
                        "semantic_score": source.get("semantic_score"),
                        "selection_score": source.get("semantic_score"),
                        "candidate_confidence_mean": source.get("candidate_confidence_mean"),
                        "candidate_point_count": source.get("candidate_point_count"),
                        "candidate_num_detections": source.get("candidate_num_detections"),
                        "source_image_idx": source.get("source_image_idx"),
                        "source_class_names": source.get("source_class_names"),
                        "candidate_source": "conceptgraphs_hm3d_runtime_post_pcd_stop_region_transform",
                        "source_route": "candidate_geometry_radial_stop_region_v0",
                        "coordinate_frame": "hm3d_world_from_conceptgraphs_candidate_geometry",
                        "coordinate_valid": True,
                        "join_ready": bool(source.get("scene_docker_path")),
                        "scene_docker_path": source.get("scene_docker_path"),
                        "navmesh_docker_path": source.get("navmesh_docker_path"),
                        "source_position": source.get("source_position"),
                        "source_scene_id_raw": source.get("source_scene_id_raw"),
                        "source_episode_id": source.get("source_episode_id"),
                        "task_context_id": source.get("task_context_id") or "source_gap_recovery_probe_v0",
                        "policy_input_allowed": True,
                        "uses_objectnav_eval_goal": False,
                        "uses_objectnav_eval_viewpoint": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "transform_input_allowed": True,
                        "claim_boundary": "Generated from non-oracle ConceptGraphs candidate geometry before target evaluation.",
                    }
                )
    return rows


def classify_stop_region_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m10 = load_module(M10_TOOL, "e008_m10_navmesh")
    return m10.classify_candidate_rows(rows)


def run_navmesh_validation(candidate_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    m10 = load_module(M10_TOOL, "e008_m10_navmesh")
    docker_input_path = ARTIFACT_DIR / "stop_region_navmesh_input_rows.jsonl"
    write_jsonl(docker_input_path, candidate_rows)
    rows, meta = m10.run_habitat_navmesh_validation(docker_input_path)
    rows = classify_stop_region_rows(rows)
    return rows, meta


def is_path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) and finite_float(row.get("source_to_snapped_geodesic_m")) is not None


def build_visit_order_rows(nav_rows: list[dict[str, Any]], source_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in nav_rows:
        by_query[str(row.get("query_uid"))].append(row)

    for query_uid, candidates in sorted(by_query.items()):
        path_ready = [row for row in candidates if is_path_ready(row)]
        ranked = sorted(
            path_ready,
            key=lambda row: (
                finite_float(row.get("source_to_snapped_geodesic_m")) or math.inf,
                dist_xz(as_vec3(row.get("candidate_center_xyz")) or [0, 0, 0], as_vec3(row.get("source_object_center_xyz")) or [0, 0, 0]),
                int(row.get("rank") or 10**9),
            ),
        )
        cumulative_cost = 0.0
        for visit_rank, row in enumerate(ranked, start=1):
            cost = finite_float(row.get("source_to_snapped_geodesic_m")) or 0.0
            cumulative_cost += cost
            rows.append(
                {
                    "version": VERSION,
                    "policy_id": POLICY_ID,
                    "candidate_scope": "path_ready_stop_region_candidates",
                    "query_uid": query_uid,
                    "scan_id": row.get("scan_id"),
                    "adapter_episode_id": row.get("adapter_episode_id"),
                    "scene_key": row.get("scene_key"),
                    "object_category": row.get("object_category"),
                    "task_context_id": row.get("task_context_id"),
                    "visit_rank": visit_rank,
                    "proposal_uid": row.get("proposal_uid"),
                    "candidate_uid": row.get("candidate_uid"),
                    "raw_candidate_uid": row.get("raw_candidate_uid"),
                    "label_canonical": row.get("label_canonical"),
                    "source_candidate_uid": row.get("source_candidate_uid"),
                    "source_candidate_min_policy_rank": row.get("source_candidate_min_policy_rank"),
                    "transform_id": row.get("transform_id"),
                    "direction_name": row.get("direction_name"),
                    "standoff_m": row.get("standoff_m"),
                    "semantic_score": row.get("semantic_score"),
                    "selection_score": row.get("selection_score"),
                    "source_to_candidate_path_cost_m": cost,
                    "cumulative_known_path_cost_m": cumulative_cost,
                    "snap_distance_m": row.get("snap_distance_m"),
                    "path_ready": True,
                    "blocked_candidate_for_path_policy": False,
                    "navmesh_validation_status": row.get("navmesh_validation_status"),
                    "candidate_snapped_position_m": row.get("snapped_position_m"),
                    "policy_input_allowed": bool(row.get("policy_input_allowed")),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "budget5_visible": visit_rank <= 5,
                    "claim_boundary": "Stop-region policy order is frozen before ObjectNav target evaluation.",
                }
            )

        source_uid = str(candidates[0].get("source_candidate_uid")) if candidates else ""
        source = source_lookup.get(source_uid)
        if source is not None:
            rows.append(
                {
                    "version": VERSION,
                    "policy_id": BASELINE_POLICY_ID,
                    "candidate_scope": "original_source_candidate_only",
                    "query_uid": query_uid,
                    "scan_id": source.get("scan_id"),
                    "adapter_episode_id": source.get("adapter_episode_id"),
                    "scene_key": source.get("scene_key"),
                    "object_category": source.get("object_category"),
                    "task_context_id": source.get("task_context_id"),
                    "visit_rank": 1,
                    "proposal_uid": source.get("proposal_uid"),
                    "candidate_uid": source.get("candidate_uid"),
                    "raw_candidate_uid": source.get("raw_candidate_uid"),
                    "label_canonical": source.get("label_canonical"),
                    "source_candidate_uid": source_uid,
                    "source_candidate_min_policy_rank": candidates[0].get("source_candidate_min_policy_rank") if candidates else None,
                    "transform_id": "none_source_candidate_baseline",
                    "direction_name": None,
                    "standoff_m": None,
                    "semantic_score": source.get("semantic_score"),
                    "selection_score": source.get("selection_score"),
                    "source_to_candidate_path_cost_m": source.get("source_to_snapped_geodesic_m"),
                    "cumulative_known_path_cost_m": source.get("source_to_snapped_geodesic_m"),
                    "snap_distance_m": source.get("snap_distance_m"),
                    "path_ready": is_path_ready(source),
                    "blocked_candidate_for_path_policy": not is_path_ready(source),
                    "navmesh_validation_status": source.get("navmesh_validation_status"),
                    "candidate_snapped_position_m": source.get("snapped_position_m"),
                    "policy_input_allowed": bool(source.get("policy_input_allowed")),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "budget5_visible": False,
                    "claim_boundary": "Frozen source candidate baseline retained for M118 delta interpretation.",
                }
            )
    return rows


def build_candidate_index(nav_rows: list[dict[str, Any]], source_lookup: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in nav_rows:
        out[str(row.get("proposal_uid"))] = row
    for key, row in source_lookup.items():
        out[key] = row
    return out


def build_posthoc_goal_rows(
    visit_rows: list[dict[str, Any]],
    candidate_index: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    m12.VERSION = VERSION
    m12.PRIMARY_METRIC = PRIMARY_METRIC
    goal_rows = read_jsonl(M113_DIR / "conceptgraphs_eval_goal_rows.jsonl")
    eval_index = m12.build_eval_goal_index(goal_rows)
    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, {})
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    leakage_audit_rows = m12.build_leakage_audit_rows(candidate_goal_rows, eval_index)
    return goal_rows, candidate_goal_rows, scan_metric_rows, aggregate_rows, leakage_audit_rows


def build_budget_visibility_rows(
    candidate_goal_rows: list[dict[str, Any]],
    scan_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best_by_policy = {(str(row.get("policy_id")), str(row.get("scan_id"))): row for row in scan_metric_rows}
    rows: list[dict[str, Any]] = []
    for (policy_id, scan_id), metric in sorted(best_by_policy.items()):
        policy_rows = [
            row
            for row in candidate_goal_rows
            if str(row.get("policy_id")) == policy_id and str(row.get("scan_id")) == scan_id
        ]
        budget_rows = [row for row in policy_rows if int(row.get("visit_rank") or 10**9) <= 5]
        rows.append(
            {
                "version": VERSION,
                "row_type": "budget_visibility",
                "policy_id": policy_id,
                "scan_id": scan_id,
                "adapter_episode_id": metric.get("adapter_episode_id"),
                "object_category": metric.get("object_category"),
                "budget_k": 5,
                "candidate_rows": metric.get("candidate_rows"),
                "path_ready_rows": metric.get("path_ready_rows"),
                "budget_rows": len(budget_rows),
                "budget_path_ready_rows": sum(1 for row in budget_rows if row.get("path_ready")),
                "budget_any_viewpoint_xz_1p0_hit": any(row.get("hit_any_viewpoint_xz_1p0") for row in budget_rows),
                "budget_any_viewpoint_xz_1p5_hit": any(row.get("hit_any_viewpoint_xz_1p5") for row in budget_rows),
                "budget_goal_xz_1p0_hit": any(row.get("hit_goal_xz_1p0") for row in budget_rows),
                "primary_hit": metric.get("primary_hit"),
                "primary_first_hit_rank": metric.get("primary_first_hit_rank"),
                "primary_first_hit_cost_m": metric.get("primary_first_hit_cost_m"),
                "best_any_viewpoint_xz_m": metric.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": metric.get("best_any_viewpoint_xz_rank"),
                "best_goal_xz_m": metric.get("best_goal_xz_m"),
                "best_goal_xz_rank": metric.get("best_goal_xz_rank"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            }
        )
    return rows


def build_route_decision_rows(
    coverage: dict[str, Any],
    budget_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stop_primary = any(
        row.get("policy_id") == POLICY_ID and row.get("budget_any_viewpoint_xz_1p0_hit")
        for row in budget_rows
    )
    stop_relaxed = any(
        row.get("policy_id") == POLICY_ID and row.get("budget_any_viewpoint_xz_1p5_hit")
        for row in budget_rows
    )
    if stop_primary:
        selected = NEXT_INTERPRET_UNIT
        decision = "select_m119_result_interpretation_before_trajectory"
        reason = "M118 materializes at least one budget-5 transformed stop-region candidate that hits the primary ObjectNav viewpoint proxy after frozen policy order."
    elif stop_relaxed:
        selected = NEXT_INTERPRET_UNIT
        decision = "select_m119_result_interpretation_with_relaxed_warning"
        reason = "M118 materializes a relaxed target-region candidate but not a primary 1.0m hit; interpret before trajectory."
    else:
        selected = NEXT_SOURCE_COVERAGE_UNIT
        decision = "select_source_coverage_external_or_visibility_preflight"
        reason = "M118 materializes stop-region candidates but does not create a budget-visible target-region hit."
    return [
        {
            "version": VERSION,
            "route_id": "direct_trajectory_execution",
            "decision": "reject_now",
            "selected": False,
            "reason": "M118 is materialization and posthoc proxy evaluation only; no trajectory contract is fixed yet.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "m119_after_m118",
            "decision": decision,
            "selected": True,
            "selected_next_unit": selected,
            "reason": reason,
            "launch_long_job_now": False,
            "stop_region_primary_budget5_hit": stop_primary,
            "stop_region_relaxed_budget5_hit": stop_relaxed,
            "source_coverage_route_still_required": True,
        },
    ]


def build_m119_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M118 has frozen stop-region candidate rows, navmesh validation rows, visit order rows, leakage audit pass, and budget-5 primary posthoc hit.",
            "gate_status": "pass" if coverage.get("stop_region_primary_budget5_hit") else "not_met",
            "next_action": NEXT_INTERPRET_UNIT,
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M118 has reachable transformed candidates but no budget-5 primary hit.",
            "gate_status": "pass" if coverage.get("stop_region_candidate_path_ready_rows") and not coverage.get("stop_region_primary_budget5_hit") else "not_met",
            "next_action": NEXT_SOURCE_COVERAGE_UNIT,
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M118 uses ObjectNav target fields to choose or rank transformed candidates.",
            "gate_status": "fail" if coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") else "pass",
            "next_action": "Repair M118 leakage contract before any further navigation step.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_stop_region_materialization",
            "supported": True,
            "claim_boundary": "M118 materializes non-oracle stop-region candidates from frozen ConceptGraphs object geometry.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_posthoc_goal_eval_after_freeze",
            "supported": True,
            "claim_boundary": "M118 evaluates ObjectNav target proximity only after candidate generation and visit order are frozen.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M118 does not execute Habitat trajectories and cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_coverage_recovery",
            "supported": False,
            "claim_boundary": "M118 does not repair the sofa source-coverage gap; that remains an external/visibility source route.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    budget_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    budget_lines = [
        "| {policy_id} | {budget_rows} | {budget_path_ready_rows} | {budget_any_viewpoint_xz_1p0_hit} | "
        "{primary_first_hit_rank} | {best_any_viewpoint_xz_m} | {best_goal_xz_m} |".format(
            policy_id=row.get("policy_id"),
            budget_rows=row.get("budget_rows"),
            budget_path_ready_rows=row.get("budget_path_ready_rows"),
            budget_any_viewpoint_xz_1p0_hit=row.get("budget_any_viewpoint_xz_1p0_hit"),
            primary_first_hit_rank=row.get("primary_first_hit_rank"),
            best_any_viewpoint_xz_m=fmt(row.get("best_any_viewpoint_xz_m")),
            best_goal_xz_m=fmt(row.get("best_goal_xz_m")),
        )
        for row in budget_rows
    ]
    route_lines = [
        "| {route_id} | {decision} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            reason=row.get("reason"),
        )
        for row in route_rows
    ]
    return f"""# E008-M118 ConceptGraphs HM3D Non-Oracle Stop-Region Transform Materialization Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M117 status: `{coverage['m117_status']}`.
- Stop-region candidate rows: {coverage['stop_region_candidate_rows']}.
- Navmesh path-ready rows: {coverage['stop_region_candidate_path_ready_rows']}.
- Visit-order rows: {coverage['stop_region_visit_order_rows']}.
- Posthoc goal-eval rows: {coverage['stop_region_posthoc_goal_eval_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Stop-region primary budget-5 hit: {coverage['stop_region_primary_budget5_hit']}.
- Stop-region relaxed budget-5 hit: {coverage['stop_region_relaxed_budget5_hit']}.
- Source-coverage route still required: {coverage['source_coverage_route_still_required']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Budget Visibility

| policy | budget rows | budget path-ready | budget primary hit | first hit rank | best any-vp XZ m | best goal XZ m |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
{chr(10).join(budget_lines)}

## Route Decision

| route | decision | reason |
| --- | --- | --- |
{chr(10).join(route_lines)}

## Claim Boundary

- M118 supports non-oracle stop-region candidate materialization and posthoc proxy evaluation after frozen candidate order.
- M118 does not execute trajectories, does not repair the sofa source-coverage gap, and does not support final real navigation `SR` / `SPL`.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m117_coverage = read_json(M117_DIR / "coverage.json")
    contract_rows = read_jsonl(M117_DIR / "stop_region_transform_contract_rows.jsonl")
    source_nav_rows = read_jsonl(M111_DIR / "candidate_navmesh_validation_rows.jsonl")
    source_lookup = build_source_candidate_lookup(source_nav_rows)

    candidate_rows = build_stop_region_candidate_rows(contract_rows, source_lookup)
    nav_rows, docker_meta = run_navmesh_validation(candidate_rows)
    visit_rows = build_visit_order_rows(nav_rows, source_lookup)
    candidate_index = build_candidate_index(nav_rows, source_lookup)
    goal_rows, posthoc_rows, scan_metric_rows, aggregate_rows, leakage_rows = build_posthoc_goal_rows(
        visit_rows,
        candidate_index,
    )
    budget_rows = build_budget_visibility_rows(posthoc_rows, scan_metric_rows)

    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_rows)
    leakage_pass = bool(leakage_rows) and not uses_eval_policy
    path_ready_rows = sum(1 for row in nav_rows if row.get("candidate_usable_for_path_smoke"))
    primary_budget_hit = any(
        row.get("policy_id") == POLICY_ID and row.get("budget_any_viewpoint_xz_1p0_hit")
        for row in budget_rows
    )
    relaxed_budget_hit = any(
        row.get("policy_id") == POLICY_ID and row.get("budget_any_viewpoint_xz_1p5_hit")
        for row in budget_rows
    )

    ready = (
        m117_coverage.get("status")
        == "e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_ready"
        and bool(candidate_rows)
        and bool(nav_rows)
        and path_ready_rows > 0
        and bool(visit_rows)
        and bool(posthoc_rows)
        and leakage_pass
    )
    if not ready:
        status = BLOCKED_STATUS
    elif primary_budget_hit:
        status = READY_STATUS
    else:
        status = WARNING_STATUS

    coverage: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m117_status": m117_coverage.get("status"),
        "m117_selected_next_unit": m117_coverage.get("selected_next_unit"),
        "stop_region_candidate_rows": len(candidate_rows),
        "stop_region_navmesh_validation_rows": len(nav_rows),
        "stop_region_candidate_path_ready_rows": path_ready_rows,
        "stop_region_visit_order_rows": len(visit_rows),
        "stop_region_posthoc_goal_eval_rows": len(posthoc_rows),
        "stop_region_scan_metric_rows": len(scan_metric_rows),
        "stop_region_aggregate_rows": len(aggregate_rows),
        "budget_visibility_rows": len(budget_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "stop_region_primary_budget5_hit": primary_budget_hit,
        "stop_region_relaxed_budget5_hit": relaxed_budget_hit,
        "source_coverage_route_still_required": True,
        "source_gap_recovery_supported": primary_budget_hit,
        "direct_trajectory_promotion_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "additional_long_job_recommended_now": False,
        "navmesh_validation_status_counts": dict(
            sorted(Counter(str(row.get("navmesh_validation_status")) for row in nav_rows).items())
        ),
        "docker_returncode": docker_meta.get("returncode"),
    }

    route_rows = build_route_decision_rows(coverage, budget_rows)
    selected_next = next((row.get("selected_next_unit") for row in route_rows if row.get("selected")), NEXT_SOURCE_COVERAGE_UNIT)
    coverage["selected_next_unit"] = selected_next
    m119_gate_rows = build_m119_gate_rows(coverage)
    claim_rows = build_claim_boundary_rows()

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "docker_navmesh_meta.json": docker_meta,
        "stop_region_candidate_rows.jsonl": candidate_rows,
        "stop_region_navmesh_validation_rows.jsonl": nav_rows,
        "stop_region_visit_order_rows.jsonl": visit_rows,
        "conceptgraphs_eval_goal_rows.jsonl": goal_rows,
        "stop_region_posthoc_goal_eval_rows.jsonl": posthoc_rows,
        "stop_region_scan_metric_rows.jsonl": scan_metric_rows,
        "stop_region_aggregate_rows.jsonl": aggregate_rows,
        "budget_visibility_rows.jsonl": budget_rows,
        "leakage_audit_rows.jsonl": leakage_rows,
        "route_decision_rows.jsonl": route_rows,
        "m119_gate_rows.jsonl": m119_gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, budget_rows, route_rows), encoding="utf-8")

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
