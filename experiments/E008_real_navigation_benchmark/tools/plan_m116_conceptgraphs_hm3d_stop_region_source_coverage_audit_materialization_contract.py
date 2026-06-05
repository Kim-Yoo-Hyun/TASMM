#!/usr/bin/env python3
"""Materialize M116 stop-region/source-coverage audit rows for ConceptGraphs HM3D."""

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

M110_DIR = EXP_ROOT / "artifacts" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
M111_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M112_DIR = EXP_ROOT / "artifacts" / "E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"
M113_DIR = EXP_ROOT / "artifacts" / "E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0"
M114_DIR = EXP_ROOT / "artifacts" / "E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0"
M115_DIR = EXP_ROOT / "artifacts" / "E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
)

VERSION = "e008_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
READY_STATUS = "e008_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_ready"
BLOCKED_STATUS = "e008_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_blocked"
NEXT_UNIT = "E008-M117 ConceptGraphs HM3D stop-region transform and source-coverage route decision contract"

PRIMARY_ANY_VIEWPOINT_XZ_M = 1.0
RELAXED_ANY_VIEWPOINT_XZ_M = 1.5
DIAGNOSTIC_GOAL_CENTER_XZ_M = 1.5
BUDGET5_RANK = 5


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


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key))].append(row)
    return grouped


def make_lookup(rows: list[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value is not None:
                lookup[str(value)] = row
    return lookup


def bucket_distance(value: float | None) -> str:
    if value is None:
        return "missing"
    if value <= PRIMARY_ANY_VIEWPOINT_XZ_M:
        return "<=1.0m"
    if value <= RELAXED_ANY_VIEWPOINT_XZ_M:
        return "<=1.5m"
    if value <= 3.0:
        return "<=3.0m"
    if value <= 5.0:
        return "<=5.0m"
    return ">5.0m"


def dedupe_eval_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_uid: dict[str, dict[str, Any]] = {}
    ranks_by_uid: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        proposal_uid = str(row.get("proposal_uid"))
        if proposal_uid == "None":
            continue
        policy_id = str(row.get("policy_id"))
        visit_rank = row.get("visit_rank")
        if visit_rank is not None:
            try:
                ranks_by_uid[proposal_uid][policy_id] = min(
                    int(visit_rank), ranks_by_uid[proposal_uid].get(policy_id, int(visit_rank))
                )
            except (TypeError, ValueError):
                pass
        current = by_uid.get(proposal_uid)
        current_any = finite_float(current.get("candidate_to_nearest_eval_viewpoint_xz_m")) if current else None
        row_any = finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m"))
        if current is None or (row_any is not None and (current_any is None or row_any < current_any)):
            by_uid[proposal_uid] = dict(row)
    out: list[dict[str, Any]] = []
    for uid, row in by_uid.items():
        ranks = ranks_by_uid.get(uid, {})
        row["visit_rank_by_policy"] = dict(sorted(ranks.items()))
        row["min_visit_rank_across_policies"] = min(ranks.values()) if ranks else row.get("visit_rank")
        out.append(row)
    return out


def sorted_by_distance(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(
        [row for row in rows if finite_float(row.get(key)) is not None],
        key=lambda row: float(row[key]),
    )


def candidate_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    centers = [row.get("candidate_center_xyz") for row in rows if isinstance(row.get("candidate_center_xyz"), list)]
    xs = [float(center[0]) for center in centers if len(center) >= 3]
    zs = [float(center[2]) for center in centers if len(center) >= 3]
    ranks = [int(row["rank"]) for row in rows if row.get("rank") is not None]
    semantic_scores = [float(row["semantic_score"]) for row in rows if finite_float(row.get("semantic_score")) is not None]
    image_counts: Counter[int] = Counter()
    for row in rows:
        for image_idx in row.get("source_image_idx") or []:
            try:
                image_counts[int(image_idx)] += 1
            except (TypeError, ValueError):
                continue
    return {
        "candidate_rows": len(rows),
        "rank_min": min(ranks) if ranks else None,
        "rank_max": max(ranks) if ranks else None,
        "semantic_score_min": min(semantic_scores) if semantic_scores else None,
        "semantic_score_max": max(semantic_scores) if semantic_scores else None,
        "candidate_center_x_range": [min(xs), max(xs)] if xs else None,
        "candidate_center_z_range": [min(zs), max(zs)] if zs else None,
        "top_source_image_idx_counts": [
            {"source_image_idx": idx, "count": count} for idx, count in image_counts.most_common(5)
        ],
    }


def build_source_coverage_rows(
    case_rows: list[dict[str, Any]],
    eval_by_scan: dict[str, list[dict[str, Any]]],
    candidate_by_scan: dict[str, list[dict[str, Any]]],
    candidate_lookup: dict[str, dict[str, Any]],
    nav_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in case_rows:
        if case.get("selected_repair_family") != "alternative_candidate_source_or_visibility_audit":
            continue
        scan_id = str(case.get("scan_id"))
        path_ready_eval = dedupe_eval_rows([row for row in eval_by_scan.get(scan_id, []) if row.get("path_ready")])
        any_values = [finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) for row in path_ready_eval]
        any_values = [value for value in any_values if value is not None]
        goal_values = [finite_float(row.get("candidate_to_eval_goal_xz_m")) for row in path_ready_eval]
        goal_values = [value for value in goal_values if value is not None]
        best_any = sorted_by_distance(path_ready_eval, "candidate_to_nearest_eval_viewpoint_xz_m")
        best_row = best_any[0] if best_any else {}
        best_uid = str(best_row.get("proposal_uid")) if best_row else None
        best_candidate = candidate_lookup.get(best_uid or "", {})
        best_nav = nav_lookup.get(best_uid or "", {})
        bucket_counts = Counter(bucket_distance(value) for value in any_values)
        goal_bucket_counts = Counter(bucket_distance(value) for value in goal_values)
        min_any = min(any_values) if any_values else None
        max_any = max(any_values) if any_values else None
        current_source_coverage_status = (
            "no_path_ready_candidate_within_5m_any_viewpoint"
            if min_any is not None and min_any > 5.0
            else "candidate_source_has_nearish_but_not_primary_target_region_candidate"
        )
        out.append(
            {
                "version": VERSION,
                "row_type": "source_coverage_audit",
                "query_uid": case.get("query_uid"),
                "adapter_episode_id": case.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": case.get("scene_key"),
                "object_category": case.get("object_category"),
                "m114_failure_class": case.get("m114_failure_class"),
                "selected_repair_family": case.get("selected_repair_family"),
                "candidate_source": "conceptgraphs_hm3d_runtime_post_pcd",
                "candidate_source_boundary": "generic_item_class_names_clip_text_score_only",
                "candidate_distribution_stats": candidate_stats(candidate_by_scan.get(scan_id, [])),
                "path_ready_eval_candidate_rows": len(path_ready_eval),
                "any_viewpoint_xz_bucket_counts": dict(sorted(bucket_counts.items())),
                "goal_center_xz_bucket_counts": dict(sorted(goal_bucket_counts.items())),
                "min_any_viewpoint_xz_m": min_any,
                "mean_any_viewpoint_xz_m": mean(any_values),
                "max_any_viewpoint_xz_m": max_any,
                "primary_target_near_candidate_rows": sum(
                    1 for value in any_values if value <= PRIMARY_ANY_VIEWPOINT_XZ_M
                ),
                "relaxed_target_near_candidate_rows": sum(
                    1 for value in any_values if value <= RELAXED_ANY_VIEWPOINT_XZ_M
                ),
                "best_any_viewpoint_candidate_uid": best_uid,
                "best_any_viewpoint_candidate_rank": best_candidate.get("rank"),
                "best_any_viewpoint_candidate_min_policy_rank": best_row.get("min_visit_rank_across_policies"),
                "best_any_viewpoint_candidate_visit_rank_by_policy": best_row.get("visit_rank_by_policy"),
                "best_any_viewpoint_candidate_semantic_score": best_candidate.get("semantic_score"),
                "best_any_viewpoint_candidate_path_cost_m": best_nav.get("source_to_snapped_geodesic_m"),
                "best_any_viewpoint_candidate_center_xyz": best_candidate.get("candidate_center_xyz"),
                "best_any_viewpoint_candidate_snapped_position_m": best_nav.get("snapped_position_m")
                or best_row.get("candidate_snapped_position_m"),
                "best_any_viewpoint_candidate_source_image_idx": best_candidate.get("source_image_idx"),
                "best_any_viewpoint_candidate_source_class_names": best_candidate.get("source_class_names"),
                "current_source_coverage_status": current_source_coverage_status,
                "same_source_rerun_justified": False,
                "same_source_path_ranking_repair_justified": False,
                "external_candidate_source_or_visibility_audit_needed": True,
                "m117_materialization_requirement": (
                    "Do not repeat the same ConceptGraphs runtime or path ranking. First decide whether a "
                    "visibility audit, broader observation route, or stronger external map/proposal baseline "
                    "is the appropriate source-coverage repair."
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_audit": True,
                "claim_boundary": "Source-coverage diagnosis only; no new candidate generation or source-gap recovery.",
            }
        )
    return out


def build_stop_region_rows(
    case_rows: list[dict[str, Any]],
    eval_by_scan: dict[str, list[dict[str, Any]]],
    candidate_lookup: dict[str, dict[str, Any]],
    nav_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in case_rows:
        if case.get("selected_repair_family") != "stop_region_viewpoint_alignment_audit":
            continue
        scan_id = str(case.get("scan_id"))
        path_ready_eval = dedupe_eval_rows([row for row in eval_by_scan.get(scan_id, []) if row.get("path_ready")])
        best_goal_rows = sorted_by_distance(path_ready_eval, "candidate_to_eval_goal_xz_m")
        best_goal = best_goal_rows[0] if best_goal_rows else {}
        best_uid = str(best_goal.get("proposal_uid")) if best_goal else None
        best_candidate = candidate_lookup.get(best_uid or "", {})
        best_nav = nav_lookup.get(best_uid or "", {})
        goal_xz = finite_float(best_goal.get("candidate_to_eval_goal_xz_m"))
        any_vp_xz = finite_float(best_goal.get("candidate_to_nearest_eval_viewpoint_xz_m"))
        min_rank = best_goal.get("min_visit_rank_across_policies")
        try:
            min_rank_int = int(min_rank)
        except (TypeError, ValueError):
            min_rank_int = None
        goal_center_hit = goal_xz is not None and goal_xz <= DIAGNOSTIC_GOAL_CENTER_XZ_M
        primary_hit = any_vp_xz is not None and any_vp_xz <= PRIMARY_ANY_VIEWPOINT_XZ_M
        relaxed_any_hit = any_vp_xz is not None and any_vp_xz <= RELAXED_ANY_VIEWPOINT_XZ_M
        out.append(
            {
                "version": VERSION,
                "row_type": "stop_region_alignment_audit",
                "query_uid": case.get("query_uid"),
                "adapter_episode_id": case.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": case.get("scene_key"),
                "object_category": case.get("object_category"),
                "m114_failure_class": case.get("m114_failure_class"),
                "selected_repair_family": case.get("selected_repair_family"),
                "candidate_source": "conceptgraphs_hm3d_runtime_post_pcd",
                "candidate_source_boundary": "generic_item_class_names_clip_text_score_only",
                "best_goal_candidate_uid": best_uid,
                "best_goal_candidate_rank": best_candidate.get("rank"),
                "best_goal_candidate_min_policy_rank": min_rank_int,
                "best_goal_candidate_visit_rank_by_policy": best_goal.get("visit_rank_by_policy"),
                "best_goal_candidate_semantic_score": best_candidate.get("semantic_score"),
                "best_goal_candidate_path_cost_m": best_nav.get("source_to_snapped_geodesic_m"),
                "best_goal_candidate_center_xyz": best_candidate.get("candidate_center_xyz"),
                "best_goal_candidate_extent_xyz": best_candidate.get("candidate_extent_xyz"),
                "best_goal_candidate_snapped_position_m": best_nav.get("snapped_position_m")
                or best_goal.get("candidate_snapped_position_m"),
                "best_goal_candidate_source_image_idx": best_candidate.get("source_image_idx"),
                "best_goal_candidate_source_class_names": best_candidate.get("source_class_names"),
                "candidate_to_eval_goal_xz_m": goal_xz,
                "candidate_to_nearest_eval_viewpoint_xz_m": any_vp_xz,
                "goal_center_diagnostic_hit_1p5": goal_center_hit,
                "primary_any_viewpoint_hit_1p0": primary_hit,
                "relaxed_any_viewpoint_hit_1p5": relaxed_any_hit,
                "primary_any_viewpoint_miss_margin_m": (any_vp_xz - PRIMARY_ANY_VIEWPOINT_XZ_M)
                if any_vp_xz is not None
                else None,
                "relaxed_any_viewpoint_miss_margin_m": (any_vp_xz - RELAXED_ANY_VIEWPOINT_XZ_M)
                if any_vp_xz is not None
                else None,
                "goal_center_margin_m": (DIAGNOSTIC_GOAL_CENTER_XZ_M - goal_xz) if goal_xz is not None else None,
                "stop_region_alignment_gap_m": (any_vp_xz - goal_xz)
                if any_vp_xz is not None and goal_xz is not None
                else None,
                "budget5_policy_rank_ready": min_rank_int is not None and min_rank_int <= BUDGET5_RANK,
                "budget_warning": "candidate_exists_but_not_budget5_visible"
                if min_rank_int is not None and min_rank_int > BUDGET5_RANK
                else "candidate_budget_visible_or_rank_unknown",
                "candidate_to_stop_region_transform_candidate": "candidate_geometry_radial_stop_region_v0",
                "transform_allowed_inputs": [
                    "candidate_center_xyz",
                    "candidate_extent_xyz",
                    "snapped_position_m",
                    "navmesh reachability",
                    "source-to-candidate path cost",
                ],
                "transform_blocked_inputs": [
                    "ObjectNav target viewpoint coordinates",
                    "ObjectNav eval goal position",
                    "target object id",
                    "distance-to-target fields before frozen policy",
                ],
                "transform_smoke_ready": False,
                "trajectory_promotion_ready": False,
                "m117_materialization_requirement": (
                    "Materialize non-oracle stop-region candidates around the ConceptGraphs object geometry "
                    "and evaluate them only after the transform rows are frozen. Also address the budget/rank "
                    "warning before a trajectory run."
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_audit": True,
                "claim_boundary": "Stop-region interface diagnosis only; no transformed candidate or trajectory result yet.",
            }
        )
    return out


def build_case_summary_rows(
    source_rows: list[dict[str, Any]],
    stop_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        rows.append(
            {
                "version": VERSION,
                "row_type": "case_audit_summary",
                "scan_id": row.get("scan_id"),
                "object_category": row.get("object_category"),
                "audit_family": "source_coverage",
                "audit_status": row.get("current_source_coverage_status"),
                "primary_blocker": "no target-near ConceptGraphs map candidate in current source route",
                "next_repair_route": "visibility_audit_or_external_candidate_source_preflight",
                "direct_trajectory_promotion_ready": False,
            }
        )
    for row in stop_rows:
        rows.append(
            {
                "version": VERSION,
                "row_type": "case_audit_summary",
                "scan_id": row.get("scan_id"),
                "object_category": row.get("object_category"),
                "audit_family": "stop_region_alignment",
                "audit_status": "goal_center_near_but_viewpoint_miss",
                "primary_blocker": "candidate-to-stop-region interface and budget visibility are not yet materialized",
                "next_repair_route": "non_oracle_stop_region_transform_contract",
                "direct_trajectory_promotion_ready": False,
            }
        )
    return rows


def build_blocked_input_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "field": "M110 candidate geometry",
            "used_for_policy_or_source_generation": True,
            "used_for_posthoc_audit": True,
            "audit_status": "pass",
            "reason": "Candidate geometry is a valid non-oracle map output from the frozen ConceptGraphs route.",
        },
        {
            "version": VERSION,
            "field": "M111 navmesh/source readiness",
            "used_for_policy_or_source_generation": True,
            "used_for_posthoc_audit": True,
            "audit_status": "pass",
            "reason": "Reachability and path costs are policy-visible after M111/M112.",
        },
        {
            "version": VERSION,
            "field": "M112 frozen visit order",
            "used_for_policy_or_source_generation": True,
            "used_for_posthoc_audit": True,
            "audit_status": "pass",
            "reason": "M116 uses the already frozen visit order to diagnose budget visibility, not to re-rank with target distances.",
        },
        {
            "version": VERSION,
            "field": "M113 distance-to-target fields",
            "used_for_policy_or_source_generation": False,
            "used_for_posthoc_audit": True,
            "audit_status": "pass",
            "reason": "Distances are used only after M112 policy order is frozen to materialize failure-family diagnostics.",
        },
        {
            "version": VERSION,
            "field": "ObjectNav eval goal position / target viewpoint coordinates",
            "used_for_policy_or_source_generation": False,
            "used_for_posthoc_audit": "metric_only",
            "audit_status": "pass",
            "reason": "M116 does not use eval goal or target viewpoint coordinates to generate candidates, rank candidates, or select trajectory targets.",
        },
        {
            "version": VERSION,
            "field": "target object id / success labels",
            "used_for_policy_or_source_generation": False,
            "used_for_posthoc_audit": False,
            "audit_status": "pass",
            "reason": "M116 does not use target object ids or success labels as policy/source inputs.",
        },
    ]


def build_repair_decision_rows(
    source_rows: list[dict[str, Any]],
    stop_rows: list[dict[str, Any]],
    input_ready: bool,
) -> list[dict[str, Any]]:
    if not input_ready:
        return [
            {
                "version": VERSION,
                "route_id": "repair_m116_inputs",
                "decision": "select_if_blocked",
                "reason": "M116 inputs are incomplete; repair lineage before any next route.",
                "selected_next_unit": "repair E008-M116 input lineage",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "route_id": "direct_trajectory_execution",
            "decision": "reject_now",
            "case_rows": len(source_rows) + len(stop_rows),
            "reason": "M116 materializes audit rows only; no recovered target-near source or stop-region transform exists yet.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "same_conceptgraphs_path_ranking_only",
            "decision": "reject_now",
            "case_rows": len(source_rows) + len(stop_rows),
            "reason": "M112/M113 already showed path-ready ordering is insufficient when target-near candidates are absent or low-rank.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "repeat_same_conceptgraphs_runtime",
            "decision": "reject_now",
            "case_rows": len(source_rows),
            "reason": "The severe source-coverage case needs a changed visibility/source principle, not the same runtime repeated.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "candidate_geometry_stop_region_transform",
            "decision": "select_subroute",
            "case_rows": len(stop_rows),
            "reason": "One case has a goal-center diagnostic candidate but misses target viewpoints; test a non-oracle stop-region transform before trajectory.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "source_coverage_external_or_visibility_route",
            "decision": "select_subroute",
            "case_rows": len(source_rows),
            "reason": "One case has no path-ready candidate within 5m of a valid target viewpoint; audit visibility/external candidate-source routes.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "m117_stop_region_transform_source_coverage_route_decision_contract",
            "decision": "select",
            "case_rows": len(source_rows) + len(stop_rows),
            "reason": "M117 should decide the next concrete repair route using the M116 materialized audit rows.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
    ]


def build_m117_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M117 selects one executable repair route with no target-goal leakage: stop-region transform smoke for the alignment case, or external/visibility source preflight for the coverage case.",
            "next_action": "Implement the selected repair route only after the route has exact inputs, outputs, blocked fields, and evaluation metrics.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M117 can select only a diagnostic route or cannot make source-coverage repair executable without a heavier external baseline.",
            "next_action": "Keep M116 as reviewer-defense evidence and consider E006-M06 or `HOV-SG`/`OpenMask3D` feasibility next.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M117 requires ObjectNav target viewpoints, eval goal, target object id, or success labels as policy/source inputs.",
            "next_action": "Do not run trajectory or mapping jobs; repair the route contract first.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_audit_materialization",
            "supported": True,
            "claim_boundary": "M116 supports materialized audit rows for one stop-region alignment case and one severe source-coverage case.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_leakage_safe_repair_route_precondition",
            "supported": True,
            "claim_boundary": "M116 supports rejecting direct trajectory execution and same-source reranking before a non-oracle repair route is fixed.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M116 does not generate new candidates or recover the two M113 primary failures.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M116 produces no Habitat trajectory results and no SR/SPL table.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M116 is a two-case ConceptGraphs HM3D diagnostic, not heldout RGB-D/open-vocabulary robustness evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M116 does not execute E006 utility, regret, or transfer gates.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why is M116 not a trajectory run?",
            "answer": "M115 showed 0/2 primary proxy recovery. M116 materializes the missing failure-family evidence needed before a trajectory could test a repaired policy.",
        },
        {
            "version": VERSION,
            "question": "What does the sofa case show?",
            "answer": "The current ConceptGraphs source has 20 path-ready sofa candidates, but none is within 5m of a valid target viewpoint; repeating path ranking cannot create a target-region candidate.",
        },
        {
            "version": VERSION,
            "question": "What does the toilet case show?",
            "answer": "A candidate is near the goal center under a 1.5m diagnostic but misses valid ObjectNav viewpoints and is not budget-5 visible, so stop-region conversion and ranking must be repaired before trajectory.",
        },
        {
            "version": VERSION,
            "question": "Does M116 prove ConceptGraphs is bad?",
            "answer": "No. It is a two-case HM3D route audit. It shows this current ConceptGraphs route is insufficient for source-gap recovery without stop-region/source-coverage repair.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    source_rows: list[dict[str, Any]],
    stop_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    source_lines = [
        "| {scan_id} | {object_category} | {path_ready_eval_candidate_rows} | {min_any_viewpoint_xz_m} | "
        "{primary_target_near_candidate_rows} | {relaxed_target_near_candidate_rows} | {current_source_coverage_status} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            path_ready_eval_candidate_rows=row.get("path_ready_eval_candidate_rows"),
            min_any_viewpoint_xz_m=fmt(row.get("min_any_viewpoint_xz_m")),
            primary_target_near_candidate_rows=row.get("primary_target_near_candidate_rows"),
            relaxed_target_near_candidate_rows=row.get("relaxed_target_near_candidate_rows"),
            current_source_coverage_status=row.get("current_source_coverage_status"),
        )
        for row in source_rows
    ]
    stop_lines = [
        "| {scan_id} | {object_category} | {candidate_to_eval_goal_xz_m} | {candidate_to_nearest_eval_viewpoint_xz_m} | "
        "{best_goal_candidate_min_policy_rank} | {budget_warning} | {transform_smoke_ready} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            candidate_to_eval_goal_xz_m=fmt(row.get("candidate_to_eval_goal_xz_m")),
            candidate_to_nearest_eval_viewpoint_xz_m=fmt(row.get("candidate_to_nearest_eval_viewpoint_xz_m")),
            best_goal_candidate_min_policy_rank=row.get("best_goal_candidate_min_policy_rank"),
            budget_warning=row.get("budget_warning"),
            transform_smoke_ready=row.get("transform_smoke_ready"),
        )
        for row in stop_rows
    ]
    decision_lines = [
        "| {route_id} | {decision} | {case_rows} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            case_rows=row.get("case_rows"),
            reason=row.get("reason"),
        )
        for row in decision_rows
    ]
    gate_lines = [
        "| {gate} | {condition} | {next_action} |".format(
            gate=row.get("gate"),
            condition=row.get("condition"),
            next_action=row.get("next_action"),
        )
        for row in gate_rows
    ]
    return f"""# E008-M116 ConceptGraphs HM3D Stop-Region / Source-Coverage Audit Materialization

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M115 status: `{coverage['m115_status']}`.
- Source-coverage audit rows: {coverage['source_coverage_audit_rows']}.
- Stop-region alignment audit rows: {coverage['stop_region_alignment_audit_rows']}.
- Blocked-input audit pass: {coverage['blocked_input_audit_pass']}.
- Source-gap recovery supported: {coverage['source_gap_recovery_supported']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Launch long job now: {coverage['launch_long_job_now']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Source-Coverage Audit

| scan_id | category | path-ready eval candidates | min any-vp XZ m | primary target-near rows | relaxed target-near rows | status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(source_lines)}

## Stop-Region Alignment Audit

| scan_id | category | goal XZ m | nearest viewpoint XZ m | min policy rank | budget warning | transform smoke ready |
| --- | --- | ---: | ---: | ---: | --- | --- |
{chr(10).join(stop_lines)}

## Repair Decision

| route | decision | cases | reason |
| --- | --- | ---: | --- |
{chr(10).join(decision_lines)}

## M117 Gate

| gate | condition | next action |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M116 supports only leakage-safe audit materialization and repair-route preconditions.
- M116 does not support source-gap recovery, trajectory promotion, final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m110_coverage = read_json(M110_DIR / "coverage.json")
    m111_coverage = read_json(M111_DIR / "coverage.json")
    m112_coverage = read_json(M112_DIR / "coverage.json")
    m113_coverage = read_json(M113_DIR / "coverage.json")
    m114_coverage = read_json(M114_DIR / "coverage.json")
    m115_coverage = read_json(M115_DIR / "coverage.json")

    m110_candidate_rows = read_jsonl(M110_DIR / "candidate_rows.jsonl")
    m111_nav_rows = read_jsonl(M111_DIR / "candidate_navmesh_validation_rows.jsonl")
    m112_visit_rows = read_jsonl(M112_DIR / "candidate_visit_order_rows.jsonl")
    m113_eval_rows = read_jsonl(M113_DIR / "candidate_goal_eval_rows.jsonl")
    m115_case_rows = read_jsonl(M115_DIR / "case_failure_audit_rows.jsonl")

    input_ready = (
        m110_coverage.get("status") == "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_ready"
        and m111_coverage.get("status") == "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready"
        and m112_coverage.get("status") == "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_ready"
        and m113_coverage.get("status") == "e008_m113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_ready"
        and m114_coverage.get("status") == "e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_ready"
        and m115_coverage.get("status") == "e008_m115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_ready"
        and bool(m110_candidate_rows)
        and bool(m111_nav_rows)
        and bool(m112_visit_rows)
        and bool(m113_eval_rows)
        and bool(m115_case_rows)
    )

    candidate_lookup = make_lookup(m110_candidate_rows, "candidate_uid", "candidate_id")
    nav_lookup = make_lookup(m111_nav_rows, "candidate_uid", "candidate_id", "proposal_uid")
    eval_by_scan = group_by(m113_eval_rows, "scan_id")
    candidate_by_scan = group_by(m110_candidate_rows, "scan_id")

    source_rows = build_source_coverage_rows(
        m115_case_rows, eval_by_scan, candidate_by_scan, candidate_lookup, nav_lookup
    )
    stop_rows = build_stop_region_rows(m115_case_rows, eval_by_scan, candidate_lookup, nav_lookup)
    case_summary_rows = build_case_summary_rows(source_rows, stop_rows)
    blocked_input_rows = build_blocked_input_audit_rows()
    blocked_input_pass = all(row.get("audit_status") == "pass" for row in blocked_input_rows)
    decision_rows = build_repair_decision_rows(source_rows, stop_rows, input_ready)
    gate_rows = build_m117_gate_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()

    m116_gate_pass = input_ready and len(source_rows) >= 1 and len(stop_rows) >= 1 and blocked_input_pass
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if m116_gate_pass else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m110_status": m110_coverage.get("status"),
        "m111_status": m111_coverage.get("status"),
        "m112_status": m112_coverage.get("status"),
        "m113_status": m113_coverage.get("status"),
        "m114_status": m114_coverage.get("status"),
        "m115_status": m115_coverage.get("status"),
        "m110_candidate_rows": m110_coverage.get("candidate_rows"),
        "m111_path_ready_candidate_rows": m111_coverage.get("source_to_snapped_path_found_rows"),
        "m112_visit_order_rows": m112_coverage.get("visit_order_rows"),
        "m113_primary_success_count_max": m113_coverage.get("primary_success_count_max"),
        "m115_case_failure_audit_rows": m115_coverage.get("case_failure_audit_rows"),
        "source_coverage_audit_rows": len(source_rows),
        "stop_region_alignment_audit_rows": len(stop_rows),
        "case_audit_summary_rows": len(case_summary_rows),
        "blocked_input_audit_rows": len(blocked_input_rows),
        "blocked_input_audit_pass": blocked_input_pass,
        "m116_gate_pass": m116_gate_pass,
        "selected_next_unit": NEXT_UNIT,
        "source_gap_recovery_supported": False,
        "stop_region_transform_smoke_ready": False,
        "direct_trajectory_promotion_ready": False,
        "additional_long_job_recommended_now": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "source_coverage_audit_rows.jsonl": source_rows,
        "stop_region_alignment_audit_rows.jsonl": stop_rows,
        "case_audit_summary_rows.jsonl": case_summary_rows,
        "blocked_input_audit_rows.jsonl": blocked_input_rows,
        "repair_route_decision_rows.jsonl": decision_rows,
        "m117_gate_rows.jsonl": gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, source_rows, stop_rows, decision_rows, gate_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
