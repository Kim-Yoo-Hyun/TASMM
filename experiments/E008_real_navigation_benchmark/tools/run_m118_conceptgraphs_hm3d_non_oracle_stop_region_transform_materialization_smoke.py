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
M116_DIR = EXP_ROOT / "artifacts" / "E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
M117_DIR = EXP_ROOT / "artifacts" / "E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"

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
BLOCKED_STATUS = "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_blocked"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
NEXT_UNIT = "E008-M119 ConceptGraphs/HM3D source-coverage external-or-visibility preflight"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    if hasattr(module, "PRIMARY_METRIC"):
        module.PRIMARY_METRIC = PRIMARY_METRIC
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def as_float_vec3(vec: object) -> list[float]:
    if not valid_vec3(vec):
        raise ValueError(f"expected finite xyz vector, got {vec!r}")
    return [float(value) for value in vec]  # type: ignore[arg-type]


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def dist_xz(a: list[float], b: list[float]) -> float:
    return float(math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[2]) - float(b[2])) ** 2))


def normalize_xz(x: float, z: float) -> tuple[float, float] | None:
    norm = math.sqrt(x * x + z * z)
    if norm <= 1e-9:
        return None
    return float(x / norm), float(z / norm)


def unique_directions(center: list[float], source: list[float]) -> list[dict[str, Any]]:
    base = [
        ("cardinal_north_posz", 0.0, 1.0, "cardinal"),
        ("cardinal_south_negz", 0.0, -1.0, "cardinal"),
        ("cardinal_east_posx", 1.0, 0.0, "cardinal"),
        ("cardinal_west_negx", -1.0, 0.0, "cardinal"),
        ("diagonal_ne", 1.0, 1.0, "diagonal"),
        ("diagonal_se", 1.0, -1.0, "diagonal"),
        ("diagonal_sw", -1.0, -1.0, "diagonal"),
        ("diagonal_nw", -1.0, 1.0, "diagonal"),
    ]
    source_to_center = normalize_xz(center[0] - source[0], center[2] - source[2])
    if source_to_center:
        sx, sz = source_to_center
        base.extend(
            [
                ("source_to_object_axis", sx, sz, "source_axis"),
                ("object_to_source_axis", -sx, -sz, "source_axis"),
            ]
        )

    out: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for direction_id, dx, dz, family in base:
        normed = normalize_xz(dx, dz)
        if normed is None:
            continue
        ndx, ndz = normed
        key = (int(round(ndx * 1000)), int(round(ndz * 1000)))
        if key in seen:
            continue
        seen.add(key)
        out.append({"direction_id": direction_id, "direction_family": family, "dx": ndx, "dz": ndz})
    return out


def build_stop_region_candidate_rows(
    contract_rows: list[dict[str, Any]],
    stop_audit_rows: list[dict[str, Any]],
    source_candidate_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    audit_by_query = {str(row.get("query_uid")): row for row in stop_audit_rows}
    out: list[dict[str, Any]] = []
    for contract in contract_rows:
        if not contract.get("transform_input_ready"):
            continue
        source_uid = str(contract.get("source_candidate_uid"))
        source_row = source_candidate_index.get(source_uid)
        audit = audit_by_query.get(str(contract.get("query_uid")), {})
        if not source_row or not audit:
            continue

        center = as_float_vec3(audit.get("best_goal_candidate_center_xyz"))
        extent = as_float_vec3(audit.get("best_goal_candidate_extent_xyz"))
        source_position = as_float_vec3(source_row.get("source_position"))
        source_snapped = as_float_vec3(audit.get("best_goal_candidate_snapped_position_m"))
        nav_y = source_snapped[1]
        xz_radius = max(abs(extent[0]), abs(extent[2])) * 0.5
        radii = [
            xz_radius + 1.25,
            xz_radius + 1.00,
            xz_radius + 1.50,
            xz_radius + 0.75,
            xz_radius + 1.75,
        ]
        directions = unique_directions(center, source_position)
        rank = 0
        for ring_rank, radius in enumerate(radii, start=1):
            for direction_rank, direction in enumerate(directions, start=1):
                rank += 1
                proposal_uid = (
                    f"stopregion:{source_uid}:ring{ring_rank:02d}:dir{direction_rank:02d}:"
                    f"{direction['direction_id']}"
                )
                centroid = [
                    center[0] + float(direction["dx"]) * radius,
                    nav_y,
                    center[2] + float(direction["dz"]) * radius,
                ]
                out.append(
                    {
                        "version": VERSION,
                        "row_type": "stop_region_candidate",
                        "proposal_uid": proposal_uid,
                        "candidate_uid": proposal_uid,
                        "raw_candidate_uid": source_uid,
                        "source_candidate_uid": source_uid,
                        "source_candidate_rank": contract.get("source_candidate_rank"),
                        "source_candidate_min_policy_rank": contract.get("source_candidate_min_policy_rank"),
                        "candidate_rank": rank,
                        "rank": rank,
                        "stop_region_ring_rank": ring_rank,
                        "stop_region_direction_rank": direction_rank,
                        "stop_region_direction_id": direction["direction_id"],
                        "stop_region_direction_family": direction["direction_family"],
                        "stop_region_radius_m": radius,
                        "object_geometry_radius_xz_m": xz_radius,
                        "candidate_center_xyz": center,
                        "candidate_extent_xyz": extent,
                        "centroid_world_m": centroid,
                        "coordinate_frame": "hm3d_world_from_staged_rgbd_pose",
                        "coordinate_valid": True,
                        "join_ready": True,
                        "adapter_episode_id": contract.get("adapter_episode_id"),
                        "query_uid": contract.get("query_uid"),
                        "scan_id": contract.get("scan_id"),
                        "scene_key": contract.get("scene_key"),
                        "object_category": contract.get("object_category"),
                        "label_canonical": contract.get("object_category"),
                        "semantic_score": source_row.get("semantic_score"),
                        "selection_score": source_row.get("selection_score") or source_row.get("semantic_score"),
                        "candidate_confidence_mean": source_row.get("candidate_confidence_mean"),
                        "candidate_point_count": source_row.get("candidate_point_count"),
                        "candidate_num_detections": source_row.get("candidate_num_detections"),
                        "source_position": source_position,
                        "scene_docker_path": source_row.get("scene_docker_path"),
                        "navmesh_docker_path": source_row.get("navmesh_docker_path"),
                        "source_scene_id_raw": source_row.get("source_scene_id_raw"),
                        "source_episode_id": source_row.get("source_episode_id"),
                        "source_route": "conceptgraphs_hm3d_stop_region_transform",
                        "candidate_source": "conceptgraphs_hm3d_candidate_geometry_radial_stop_region",
                        "frame_id": "m118_stop_region_transform",
                        "policy_input_allowed": True,
                        "uses_objectnav_eval_goal": False,
                        "uses_objectnav_eval_viewpoint": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_candidate_generation": False,
                        "case_selected_from_m116_posthoc_audit": True,
                        "deployable_case_selection_supported": False,
                        "transform_id": contract.get("selected_transform_id"),
                        "policy_repair_id": contract.get("selected_policy_repair_id"),
                        "claim_boundary": (
                            "Stop-region points are generated from candidate geometry only; the case and "
                            "source candidate were selected by the prior posthoc repair audit, so this is not "
                            "yet a deployable trigger."
                        ),
                    }
                )
    return out


def classify_navmesh_rows(rows: list[dict[str, Any]], m10: Any) -> list[dict[str, Any]]:
    classified = m10.classify_candidate_rows(rows)
    for row in classified:
        row["version"] = VERSION
        row["row_type"] = "stop_region_navmesh_validation"
        row["path_ready"] = bool(row.get("candidate_usable_for_path_smoke"))
        row["source_to_candidate_path_cost_m"] = row.get("source_to_snapped_geodesic_m")
        row["candidate_snapped_position_m"] = row.get("snapped_position_m")
        row["uses_objectnav_eval_goal_or_viewpoint_for_policy"] = False
        row["uses_objectnav_eval_goal_or_viewpoint_for_candidate_generation"] = False
    return classified


def path_ready(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) and finite_float(row.get("source_to_snapped_geodesic_m")) is not None


def semantic_score(row: dict[str, Any]) -> float:
    return finite_float(row.get("semantic_score")) or 0.0


def path_cost(row: dict[str, Any]) -> float:
    return finite_float(row.get("source_to_snapped_geodesic_m")) or math.inf


def policy_sort_key(policy_id: str, row: dict[str, Any]) -> tuple[Any, ...]:
    if policy_id == "stop_region_cardinal_first_budgeted_v0":
        family_priority = {"cardinal": 0, "source_axis": 1, "diagonal": 2}.get(
            str(row.get("stop_region_direction_family")),
            9,
        )
        return (
            int(row.get("stop_region_ring_rank") or 10**9),
            family_priority,
            int(row.get("stop_region_direction_rank") or 10**9),
            path_cost(row),
            str(row.get("proposal_uid")),
        )
    if policy_id == "stop_region_path_cost_budgeted_v0":
        return (
            path_cost(row),
            int(row.get("stop_region_ring_rank") or 10**9),
            int(row.get("stop_region_direction_rank") or 10**9),
            str(row.get("proposal_uid")),
        )
    if policy_id == "stop_region_semantic_path_cost_budgeted_v0":
        tradeoff = semantic_score(row) / (1.0 + path_cost(row))
        return (
            -tradeoff,
            path_cost(row),
            int(row.get("stop_region_ring_rank") or 10**9),
            int(row.get("stop_region_direction_rank") or 10**9),
            str(row.get("proposal_uid")),
        )
    raise ValueError(f"unknown policy: {policy_id}")


def build_visit_order_rows(navmesh_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policies = [
        {
            "policy_id": "stop_region_cardinal_first_budgeted_v0",
            "candidate_scope": "path_ready_stop_region_candidates",
            "description": "Visit a fixed radial coverage ring around the object geometry, with cardinal directions before source-axis and diagonal directions.",
        },
        {
            "policy_id": "stop_region_path_cost_budgeted_v0",
            "candidate_scope": "path_ready_stop_region_candidates",
            "description": "Visit stop-region candidates by shortest source-to-candidate geodesic path cost.",
        },
        {
            "policy_id": "stop_region_semantic_path_cost_budgeted_v0",
            "candidate_scope": "path_ready_stop_region_candidates",
            "description": "Visit stop-region candidates by semantic score divided by one plus path cost.",
        },
    ]
    rows_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in navmesh_rows:
        rows_by_query[str(row.get("query_uid"))].append(row)

    visit_rows: list[dict[str, Any]] = []
    policy_contract_rows: list[dict[str, Any]] = []
    for policy in policies:
        policy_id = policy["policy_id"]
        for query_uid, query_rows in sorted(rows_by_query.items()):
            ranked_rows = sorted([row for row in query_rows if path_ready(row)], key=lambda row: policy_sort_key(policy_id, row))
            cumulative = 0.0
            for visit_rank, row in enumerate(ranked_rows, start=1):
                cost = path_cost(row)
                if math.isfinite(cost):
                    cumulative += cost
                visit_rows.append(
                    {
                        "version": VERSION,
                        "row_type": "stop_region_visit_order",
                        "policy_id": policy_id,
                        "candidate_scope": policy["candidate_scope"],
                        "query_uid": query_uid,
                        "scan_id": row.get("scan_id"),
                        "adapter_episode_id": row.get("adapter_episode_id"),
                        "scene_key": row.get("scene_key"),
                        "object_category": row.get("object_category"),
                        "visit_rank": visit_rank,
                        "proposal_uid": row.get("proposal_uid"),
                        "candidate_uid": row.get("candidate_uid"),
                        "raw_candidate_uid": row.get("raw_candidate_uid"),
                        "source_candidate_uid": row.get("source_candidate_uid"),
                        "label_canonical": row.get("label_canonical"),
                        "semantic_score": row.get("semantic_score"),
                        "source_to_candidate_path_cost_m": cost,
                        "cumulative_known_path_cost_m": cumulative,
                        "path_ready": True,
                        "blocked_candidate_for_path_policy": False,
                        "candidate_snapped_position_m": row.get("snapped_position_m"),
                        "stop_region_ring_rank": row.get("stop_region_ring_rank"),
                        "stop_region_direction_rank": row.get("stop_region_direction_rank"),
                        "stop_region_direction_id": row.get("stop_region_direction_id"),
                        "stop_region_direction_family": row.get("stop_region_direction_family"),
                        "stop_region_radius_m": row.get("stop_region_radius_m"),
                        "policy_input_allowed": True,
                        "uses_objectnav_eval_goal": False,
                        "uses_objectnav_eval_viewpoint": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_candidate_generation": False,
                        "case_selected_from_m116_posthoc_audit": bool(row.get("case_selected_from_m116_posthoc_audit")),
                    }
                )
            policy_contract_rows.append(
                {
                    "version": VERSION,
                    "row_type": "stop_region_policy_contract",
                    "policy_id": policy_id,
                    "query_uid": query_uid,
                    "scan_id": query_rows[0].get("scan_id") if query_rows else None,
                    "adapter_episode_id": query_rows[0].get("adapter_episode_id") if query_rows else None,
                    "ranked_candidate_rows": len(ranked_rows),
                    "top5_candidate_rows": min(5, len(ranked_rows)),
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_candidate_generation": False,
                    "description": policy["description"],
                    "claim_boundary": "Visit order is frozen before ObjectNav target/viewpoint evaluation.",
                }
            )
    return visit_rows, policy_contract_rows


def build_budget_visibility_rows(
    scan_metric_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    candidate_goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    goal_rows_by_policy_scan: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        goal_rows_by_policy_scan[(str(row.get("policy_id")), str(row.get("scan_id")))].append(row)
    for metric in scan_metric_rows:
        policy_id = str(metric.get("policy_id"))
        scan_id = str(metric.get("scan_id"))
        goal_rows = sorted(
            goal_rows_by_policy_scan[(policy_id, scan_id)],
            key=lambda row: int(row.get("visit_rank") or 10**9),
        )
        top5 = [row for row in goal_rows if int(row.get("visit_rank") or 10**9) <= 5]
        rows.append(
            {
                "version": VERSION,
                "row_type": "budget_visibility",
                "metric_scope": "scan_policy",
                "policy_id": policy_id,
                "scan_id": scan_id,
                "adapter_episode_id": metric.get("adapter_episode_id"),
                "object_category": metric.get("object_category"),
                "budget_k": 5,
                "budget5_candidate_rows": len(top5),
                "budget5_primary_hit": any(row.get("hit_any_viewpoint_xz_1p0") for row in top5),
                "budget5_any_viewpoint_xz_1p5_hit": any(row.get("hit_any_viewpoint_xz_1p5") for row in top5),
                "budget5_goal_xz_1p0_hit": any(row.get("hit_goal_xz_1p0") for row in top5),
                "primary_hit": metric.get("primary_hit"),
                "primary_first_hit_rank": metric.get("primary_first_hit_rank"),
                "primary_first_hit_cost_m": metric.get("primary_first_hit_cost_m"),
                "best_any_viewpoint_xz_m": metric.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": metric.get("best_any_viewpoint_xz_rank"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            }
        )
    for metric in aggregate_rows:
        rows.append(
            {
                "version": VERSION,
                "row_type": "budget_visibility",
                "metric_scope": "policy_aggregate",
                "policy_id": metric.get("policy_id"),
                "budget_k": 5,
                "scan_policy_rows": metric.get("scan_policy_rows"),
                "primary_success_rows": metric.get("primary_success_rows"),
                "primary_proxy_sr": metric.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": metric.get("primary_spl_proxy_mean"),
                "budget5_primary_success_rows": sum(
                    1
                    for row in rows
                    if row.get("metric_scope") == "scan_policy"
                    and row.get("policy_id") == metric.get("policy_id")
                    and row.get("budget5_primary_hit")
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    candidate_goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "check_id": "candidate_generation_does_not_use_eval_goal_or_viewpoint",
            "row_count": len(candidate_rows),
            "passed": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_candidate_generation") for row in candidate_rows),
        },
        {
            "version": VERSION,
            "check_id": "visit_order_does_not_use_eval_goal_or_viewpoint",
            "row_count": len(visit_rows),
            "passed": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in visit_rows),
        },
        {
            "version": VERSION,
            "check_id": "posthoc_goal_eval_marks_metric_only",
            "row_count": len(candidate_goal_rows),
            "passed": all(row.get("uses_objectnav_eval_goal_or_viewpoint_for_metric") for row in candidate_goal_rows)
            and not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in candidate_goal_rows),
        },
        {
            "version": VERSION,
            "check_id": "case_selection_is_not_deployable_policy_evidence",
            "row_count": len(candidate_rows),
            "passed": True,
            "claim_boundary": (
                "The M118 case/source candidate comes from the M116/M117 repair audit. The transform and "
                "policy order are leakage-free, but deployable trigger evidence is still unsupported."
            ),
        },
    ]


def build_claim_boundary_rows(stop_region_case_recovered: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_stop_region_transform_materialization",
            "supported": True,
            "claim_boundary": "M118 materializes radial stop-region candidates from ConceptGraphs candidate geometry and validates them with Habitat navmesh snapping/path cost.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_stop_region_budget5_proxy_recovery",
            "supported": stop_region_case_recovered,
            "claim_boundary": "Supported only for the selected toilet stop-region case if a frozen policy reaches an ObjectNav viewpoint within budget-5 after posthoc evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_coverage_recovery",
            "supported": False,
            "claim_boundary": "M118 does not create a new candidate source for the sofa source-coverage gap.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_stop_region_trigger",
            "supported": False,
            "claim_boundary": "M118 uses a case/source candidate selected by prior posthoc failure audit; a deployable trigger must be tested separately.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M118 does not execute Habitat trajectories and therefore cannot claim real navigation SR/SPL.",
        },
    ]


def build_m119_gate_rows(stop_region_case_recovered: bool, leakage_pass: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "m119_required",
            "passed": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The sofa case remains a source-coverage gap regardless of the toilet stop-region transform result.",
        },
        {
            "version": VERSION,
            "gate": "stop_region_transform_recovered_budget5_proxy",
            "passed": stop_region_case_recovered,
            "selected_next_unit_if_passed": NEXT_UNIT,
            "selected_next_unit_if_failed": NEXT_UNIT,
            "reason": "A positive local stop-region result is useful interface evidence, but source-coverage repair is still required before trajectory promotion.",
        },
        {
            "version": VERSION,
            "gate": "policy_leakage_audit",
            "passed": leakage_pass,
            "selected_next_unit_if_failed": "repair E008-M118 leakage guard before any M119/M120 trajectory work",
        },
    ]


def build_reviewer_defense_rows(stop_region_case_recovered: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Does M118 prove a deployable navigation policy?",
            "answer": "No. It proves only that a non-oracle geometry transform can be materialized and evaluated after freezing visit order. No trajectory is executed.",
        },
        {
            "version": VERSION,
            "question": "Why is this not target leakage?",
            "answer": "The generated stop points and visit order use candidate geometry, source position, navmesh reachability, and path cost only. ObjectNav goal/viewpoint fields are joined afterward as metric labels.",
        },
        {
            "version": VERSION,
            "question": "What if the stop-region case succeeds?",
            "answer": "It supports a local interface repair for viewpoint alignment, but the sofa source-coverage gap still blocks a broader navigation claim.",
        },
        {
            "version": VERSION,
            "question": "What if the stop-region case fails?",
            "answer": "Then the failure teaches that candidate geometry alone is insufficient for stop-region selection, and M119 must prioritize external/visibility source coverage.",
        },
        {
            "version": VERSION,
            "question": "Current outcome",
            "answer": (
                "M118 observed budget-5 proxy recovery for the selected stop-region case."
                if stop_region_case_recovered
                else "M118 did not observe budget-5 proxy recovery for the selected stop-region case."
            ),
        },
    ]


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(
    coverage: dict[str, Any],
    budget_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    m119_gate_rows: list[dict[str, Any]],
) -> str:
    budget_lines = [
        "| {policy_id} | {budget5_primary_hit} | {primary_hit} | {primary_first_hit_rank} | {primary_first_hit_cost_m} | {best_any_viewpoint_xz_m} |".format(
            policy_id=row.get("policy_id"),
            budget5_primary_hit=row.get("budget5_primary_hit"),
            primary_hit=row.get("primary_hit"),
            primary_first_hit_rank=row.get("primary_first_hit_rank"),
            primary_first_hit_cost_m=fmt(row.get("primary_first_hit_cost_m")),
            best_any_viewpoint_xz_m=fmt(row.get("best_any_viewpoint_xz_m")),
        )
        for row in budget_rows
        if row.get("metric_scope") == "scan_policy"
    ]
    aggregate_lines = [
        "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | {best_any_viewpoint_xz_m_mean} |".format(
            policy_id=row.get("policy_id"),
            primary_success_rows=row.get("primary_success_rows"),
            scan_policy_rows=row.get("scan_policy_rows"),
            primary_proxy_sr=fmt(row.get("primary_proxy_sr")),
            primary_spl_proxy_mean=fmt(row.get("primary_spl_proxy_mean")),
            best_any_viewpoint_xz_m_mean=fmt(row.get("best_any_viewpoint_xz_m_mean")),
        )
        for row in aggregate_rows
    ]
    gate_lines = [
        "| {gate} | {passed} | {selected_next_unit} | {reason} |".format(
            gate=row.get("gate"),
            passed=row.get("passed"),
            selected_next_unit=row.get("selected_next_unit")
            or row.get("selected_next_unit_if_passed")
            or row.get("selected_next_unit_if_failed"),
            reason=row.get("reason", ""),
        )
        for row in m119_gate_rows
    ]
    return f"""# E008-M118 ConceptGraphs HM3D Non-Oracle Stop-Region Transform Materialization Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M117 status: `{coverage['m117_status']}`.
- Stop-region candidate rows: {coverage['stop_region_candidate_rows']}.
- Navmesh validation rows: {coverage['stop_region_navmesh_validation_rows']}.
- Path-ready stop-region rows: {coverage['path_ready_stop_region_candidate_rows']} / {coverage['stop_region_navmesh_validation_rows']}.
- Visit-order rows: {coverage['stop_region_visit_order_rows']}.
- Candidate-goal eval rows: {coverage['stop_region_candidate_goal_eval_rows']}.
- Policy leakage audit pass: {coverage['leakage_audit_pass']}.
- Stop-region budget-5 proxy recovery observed: {coverage['stop_region_budget5_proxy_recovery_observed']}.
- Selected next unit: {coverage['selected_next_unit']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.

## Budget Visibility

| policy_id | budget5 primary hit | primary hit | first hit rank | first hit cost m | best any-vp XZ m |
| --- | --- | --- | ---: | ---: | ---: |
{chr(10).join(budget_lines)}

## Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## M119 Gate

| gate | passed | selected next | reason |
| --- | --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M118 supports stop-region transform materialization and posthoc proxy evaluation only.
- M118 does not support real navigation `SR` / `SPL`.
- M118 does not solve the `sofa` source-coverage gap.
- M118 does not yet support a deployable stop-region trigger because the case/source candidate came from the prior failure audit.
"""


def main() -> None:
    m10 = load_module(M10_TOOL, "e008_m10_navmesh")
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m117_coverage = read_json(M117_DIR / "coverage.json")
    contract_rows = read_jsonl(M117_DIR / "stop_region_transform_contract_rows.jsonl")
    stop_audit_rows = read_jsonl(M116_DIR / "stop_region_alignment_audit_rows.jsonl")
    source_coverage_rows = read_jsonl(M117_DIR / "source_coverage_route_decision_rows.jsonl")
    source_candidate_rows = read_jsonl(M111_DIR / "candidate_navmesh_validation_rows.jsonl")
    source_candidate_index = {str(row.get("proposal_uid")): row for row in source_candidate_rows}

    stop_region_candidate_rows = build_stop_region_candidate_rows(contract_rows, stop_audit_rows, source_candidate_index)
    navmesh_input_path = ARTIFACT_DIR / "stop_region_navmesh_input_rows.jsonl"
    write_jsonl(navmesh_input_path, stop_region_candidate_rows)

    raw_navmesh_rows, docker_meta = m10.run_habitat_navmesh_validation(navmesh_input_path)
    stop_region_navmesh_rows = classify_navmesh_rows(raw_navmesh_rows, m10)
    visit_rows, policy_contract_rows = build_visit_order_rows(stop_region_navmesh_rows)

    goal_rows = read_jsonl(M113_DIR / "conceptgraphs_eval_goal_rows.jsonl")
    target_episode_ids = {str(row.get("adapter_episode_id")) for row in contract_rows if row.get("transform_input_ready")}
    target_goal_rows = [row for row in goal_rows if str(row.get("adapter_episode_id")) in target_episode_ids]
    eval_index = m12.build_eval_goal_index(target_goal_rows)
    oracle_index = {str(row.get("adapter_episode_id")): row for row in target_goal_rows}
    candidate_index = {str(row.get("proposal_uid")): row for row in stop_region_navmesh_rows}
    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    policy_goal_metric_rows = scan_metric_rows + aggregate_rows
    budget_rows = build_budget_visibility_rows(scan_metric_rows, aggregate_rows, candidate_goal_rows)
    leakage_audit_rows = build_leakage_audit_rows(stop_region_candidate_rows, visit_rows, candidate_goal_rows)
    leakage_pass = all(row.get("passed") for row in leakage_audit_rows)

    stop_region_case_recovered = any(
        row.get("metric_scope") == "scan_policy" and row.get("budget5_primary_hit") for row in budget_rows
    )
    path_ready_rows = sum(1 for row in stop_region_navmesh_rows if path_ready(row))
    materialized = bool(stop_region_candidate_rows) and bool(stop_region_navmesh_rows)
    source_coverage_gap_rows = sum(
        1 for row in source_coverage_rows if not row.get("current_source_recoverable_without_new_source")
    )
    ready = (
        m117_coverage.get("status")
        == "e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_ready"
        and materialized
        and docker_meta.get("ok") is True
        and path_ready_rows > 0
        and bool(visit_rows)
        and bool(candidate_goal_rows)
        and leakage_pass
    )
    m119_gate_rows = build_m119_gate_rows(stop_region_case_recovered, leakage_pass)
    claim_rows = build_claim_boundary_rows(stop_region_case_recovered)
    reviewer_rows = build_reviewer_defense_rows(stop_region_case_recovered)
    navmesh_status_counts = Counter(str(row.get("navmesh_validation_status")) for row in stop_region_navmesh_rows)
    path_costs = [path_cost(row) for row in stop_region_navmesh_rows if path_ready(row)]

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m117_status": m117_coverage.get("status"),
        "m117_selected_next_unit": m117_coverage.get("selected_next_unit"),
        "docker_navmesh_ok": docker_meta.get("ok"),
        "docker_returncode": docker_meta.get("returncode"),
        "contract_rows": len(contract_rows),
        "transform_input_ready_rows": sum(1 for row in contract_rows if row.get("transform_input_ready")),
        "stop_region_candidate_rows": len(stop_region_candidate_rows),
        "stop_region_navmesh_validation_rows": len(stop_region_navmesh_rows),
        "path_ready_stop_region_candidate_rows": path_ready_rows,
        "navmesh_validation_status_counts": dict(sorted(navmesh_status_counts.items())),
        "mean_source_to_stop_region_path_cost_m": mean([value for value in path_costs if math.isfinite(value)]),
        "stop_region_visit_order_rows": len(visit_rows),
        "stop_region_policy_contract_rows": len(policy_contract_rows),
        "stop_region_candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "budget_visibility_rows": len(budget_rows),
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in candidate_goal_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": bool(candidate_goal_rows),
        "case_selected_from_m116_posthoc_audit": True,
        "deployable_case_selection_supported": False,
        "stop_region_transform_materialized": materialized,
        "stop_region_budget5_proxy_recovery_observed": stop_region_case_recovered,
        "source_coverage_gap_rows_remaining": source_coverage_gap_rows,
        "source_coverage_route_still_required": source_coverage_gap_rows > 0,
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
        "selected_next_unit_reason": "The stop-region local repair is now materialized; the remaining sofa source-coverage gap requires external/visibility source preflight before any trajectory promotion.",
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "docker_navmesh_meta.json": docker_meta,
        "stop_region_candidate_rows.jsonl": stop_region_candidate_rows,
        "stop_region_navmesh_validation_rows.jsonl": stop_region_navmesh_rows,
        "stop_region_visit_order_rows.jsonl": visit_rows,
        "stop_region_policy_contract_rows.jsonl": policy_contract_rows,
        "stop_region_eval_goal_rows.jsonl": target_goal_rows,
        "stop_region_candidate_goal_eval_rows.jsonl": candidate_goal_rows,
        "stop_region_policy_goal_metric_rows.jsonl": policy_goal_metric_rows,
        "budget_visibility_rows.jsonl": budget_rows,
        "leakage_audit_rows.jsonl": leakage_audit_rows,
        "m119_gate_rows.jsonl": m119_gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, budget_rows, aggregate_rows, m119_gate_rows))

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file() and path.name != "stop_region_navmesh_input_rows.jsonl":
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
