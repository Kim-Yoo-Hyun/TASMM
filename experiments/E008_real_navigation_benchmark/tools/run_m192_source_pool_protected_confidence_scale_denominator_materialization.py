#!/usr/bin/env python3
"""Materialize the E008-M192 source-pool scale denominator rows."""

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
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
M191_DIR = EXP_ROOT / "artifacts" / "E008-M191_source_pool_protected_confidence_scaleup_contract_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0"
)

VERSION = "e008_m192_source_pool_protected_confidence_scale_denominator_materialization_v0"
READY_STATUS = "e008_m192_source_pool_protected_confidence_scale_denominator_materialization_ready"
BLOCKED_STATUS = "e008_m192_source_pool_protected_confidence_scale_denominator_materialization_blocked"
NEXT_UNIT = "E008-M193 source-pool scale navmesh/snap validation and render/detector launcher contract"

SELECTED_DENOMINATOR = "hm3d_val_mini_all_triggered_source_pool_scale_v1"
SELECTED_METHOD = "source_pool_plus_detector_confidence_reachable_subset_v1"
PRIMARY_ABLATION = "no_source_pool_detector_confidence_reachable_subset_v0"
PROTECTED_DEFAULT = "detector_confidence_reachable_subset_v0"
SOURCE_POOL_COMPONENT = "fixed_budget_source_pool_candidate_generation"
ROUTE_ID = "source_pool_scale_full_triggered_expansion_v1"
POSE_FAMILY = "source_anchor_radial_coverage_pool"
MAX_SOURCE_POSES_PER_REQUEST = 8
SOURCE_BEARINGS_DEG = [0.0, 90.0, 180.0, 270.0]
SOURCE_RADII_M = [2.0, 4.0]
YAW_OFFSETS_DEG = [0, 90, 180, 270]
RENDER_WIDTH = 640
RENDER_HEIGHT = 480
DEFAULT_ROTATION_XYZW = [0.0, 0.0, 0.0, 1.0]


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


def sanitize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_vec(vec: object, n: int = 3) -> bool:
    if not isinstance(vec, list) or len(vec) != n:
        return False
    try:
        return all(math.isfinite(float(value)) for value in vec)
    except Exception:
        return False


def as_float_vec(vec: object) -> list[float]:
    if not finite_vec(vec):
        return []
    return [float(value) for value in vec]  # type: ignore[arg-type]


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def planned_position(anchor: list[float], radius_m: float, bearing_deg: float) -> list[float]:
    angle = math.radians(float(bearing_deg))
    return [
        float(anchor[0]) + radius_m * math.sin(angle),
        float(anchor[1]),
        float(anchor[2]) + radius_m * math.cos(angle),
    ]


def int_or_default(value: object, default: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def target_leakage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    forbidden_truthy_keys = [
        "uses_objectnav_eval_goal",
        "uses_objectnav_eval_viewpoint",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy",
        "uses_objectnav_eval_goal_or_viewpoint_for_source_placement",
        "uses_success_label_for_policy",
        "uses_target_object_id_or_success_label",
    ]
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        hit_keys = [key for key in forbidden_truthy_keys if bool(row.get(key))]
        if hit_keys:
            out.append(
                {
                    "version": VERSION,
                    "row_type": "blocked_input_audit",
                    "row_index": index,
                    "row_type_hit": row.get("row_type"),
                    "benchmark_row_uid": row.get("benchmark_row_uid"),
                    "hit_keys": hit_keys,
                }
            )
    return out


def anchors_by_benchmark(candidate_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if not finite_vec(row.get("source_position")):
            continue
        if not row.get("scene_docker_path") or not row.get("navmesh_docker_path"):
            continue
        grouped[str(row.get("benchmark_row_uid"))].append(row)

    for key, rows in grouped.items():
        seen_positions: set[tuple[float, float, float]] = set()
        unique_rows: list[dict[str, Any]] = []
        for row in sorted(
            rows,
            key=lambda item: (
                0 if str(item.get("frame_pose_role")) == "start_pose" else 1,
                int_or_default(item.get("visit_rank") or item.get("m168_detector_visit_rank"), 10_000),
                -float(item.get("confidence") or 0.0),
            ),
        ):
            pos = as_float_vec(row.get("source_position"))
            rounded = tuple(round(value, 2) for value in pos)
            if rounded in seen_positions:
                continue
            seen_positions.add(rounded)
            unique_rows.append(row)
        grouped[key] = unique_rows
    return grouped


def anchor_plan(anchors: list[dict[str, Any]], pose_budget: int) -> list[tuple[dict[str, Any], float, float]]:
    plan: list[tuple[dict[str, Any], float, float]] = []
    if len(anchors) >= 2:
        for anchor in anchors[: math.ceil(pose_budget / len(SOURCE_BEARINGS_DEG))]:
            for bearing in SOURCE_BEARINGS_DEG:
                plan.append((anchor, 2.0, bearing))
    elif anchors:
        for radius in SOURCE_RADII_M:
            for bearing in SOURCE_BEARINGS_DEG:
                plan.append((anchors[0], radius, bearing))
    return plan[:pose_budget]


def build_pose_rows(
    seed_rows: list[dict[str, Any]],
    grouped_anchors: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pose_rows: list[dict[str, Any]] = []
    missing_anchor_rows: list[dict[str, Any]] = []
    anchor_audit_rows: list[dict[str, Any]] = []
    request_rows: list[dict[str, Any]] = []

    for request in seed_rows:
        uid = str(request.get("benchmark_row_uid"))
        anchors = grouped_anchors.get(uid, [])
        pose_budget = min(
            MAX_SOURCE_POSES_PER_REQUEST,
            int_or_default(request.get("planned_source_pose_rows"), MAX_SOURCE_POSES_PER_REQUEST),
        )
        plan = anchor_plan(anchors, pose_budget)
        if not plan:
            missing_anchor_rows.append(
                {
                    "version": VERSION,
                    "row_type": "m192_missing_source_anchor",
                    "scale_request_uid": request.get("scale_request_uid"),
                    "benchmark_row_uid": uid,
                    "adapter_episode_id": request.get("adapter_episode_id"),
                    "scan_id": request.get("scan_id"),
                    "scene_key": request.get("scene_key"),
                    "object_category": request.get("object_category"),
                    "reason": "No policy-visible M168 source_position with scene/navmesh path was available.",
                }
            )

        for anchor_rank, anchor in enumerate(anchors[:4], start=1):
            anchor_audit_rows.append(
                {
                    "version": VERSION,
                    "row_type": "m192_source_anchor_audit",
                    "scale_request_uid": request.get("scale_request_uid"),
                    "benchmark_row_uid": uid,
                    "adapter_episode_id": request.get("adapter_episode_id"),
                    "scan_id": request.get("scan_id"),
                    "scene_key": request.get("scene_key"),
                    "object_category": request.get("object_category"),
                    "source_anchor_rank": anchor_rank,
                    "source_anchor_observation_pose_id": anchor.get("observation_pose_id"),
                    "source_anchor_candidate_visit_uid": anchor.get("candidate_visit_uid"),
                    "source_anchor_frame_pose_role": anchor.get("frame_pose_role"),
                    "source_anchor_position_m": anchor.get("source_position"),
                    "source_anchor_confidence": anchor.get("confidence"),
                    "source_anchor_visit_rank": anchor.get("visit_rank") or anchor.get("m168_detector_visit_rank"),
                    "hm3d_scene_docker_path": anchor.get("scene_docker_path"),
                    "hm3d_navmesh_docker_path": anchor.get("navmesh_docker_path"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_success_label_for_policy": False,
                }
            )

        materialized_for_request = 0
        for pose_index, (anchor, radius, bearing) in enumerate(plan):
            anchor_position = as_float_vec(anchor.get("source_position"))
            source_position = planned_position(anchor_position, radius, bearing)
            materialized_for_request += 1
            pose_rows.append(
                {
                    "version": VERSION,
                    "row_type": "source_pool_observation_pose",
                    "scale_denominator_id": SELECTED_DENOMINATOR,
                    "scale_request_uid": request.get("scale_request_uid"),
                    "scale_batch_id": request.get("scale_batch_id"),
                    "adapter_episode_id": request.get("adapter_episode_id"),
                    "benchmark_row_uid": uid,
                    "trigger_row_uid": request.get("source_trigger_row_uid"),
                    "scan_id": request.get("scan_id"),
                    "scene_key": request.get("scene_key"),
                    "object_category": request.get("object_category"),
                    "selected_method_id": SELECTED_METHOD,
                    "primary_ablation_id": PRIMARY_ABLATION,
                    "protected_default_policy_id": PROTECTED_DEFAULT,
                    "kept_method_component": SOURCE_POOL_COMPONENT,
                    "route_id": ROUTE_ID,
                    "observation_pose_id": f"{uid}:m192:pose-{pose_index:03d}",
                    "observation_pose_index": pose_index,
                    "pose_family": POSE_FAMILY,
                    "pose_role": "source_pool_candidate_observation_pose",
                    "source_anchor_observation_pose_id": anchor.get("observation_pose_id"),
                    "source_anchor_candidate_visit_uid": anchor.get("candidate_visit_uid"),
                    "source_anchor_frame_pose_role": anchor.get("frame_pose_role"),
                    "source_anchor_position_m": anchor_position,
                    "source_anchor_confidence": anchor.get("confidence"),
                    "source_anchor_visit_rank": anchor.get("visit_rank") or anchor.get("m168_detector_visit_rank"),
                    "planned_position_m": source_position,
                    "source_position": source_position,
                    "source_position_m": source_position,
                    "source_rotation": DEFAULT_ROTATION_XYZW,
                    "source_rotation_xyzw": DEFAULT_ROTATION_XYZW,
                    "shell_radius_m": radius,
                    "bearing_relative_deg": bearing,
                    "hm3d_scene_docker_path": anchor.get("scene_docker_path"),
                    "hm3d_navmesh_docker_path": anchor.get("navmesh_docker_path"),
                    "resolved_scene_path": None,
                    "resolved_navmesh_path": None,
                    "requires_navmesh_snap_validation": True,
                    "policy_input_allowed": True,
                    "source_placement_input_basis": (
                        "M191 seed row plus M168 policy-visible source positions, scene path, and navmesh path only"
                    ),
                    "budget_guard_id": "m192_scale_fixed_request_pose_render_budget_guard_v1",
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_success_label_for_policy": False,
                    "uses_target_object_id_or_success_label": False,
                    "claim_boundary": (
                        "M192 materializes source-pool scale inputs only; no detector, goal-evaluation, "
                        "or trajectory result is claimed."
                    ),
                }
            )

        request_rows.append(
            {
                **request,
                "version": VERSION,
                "row_type": "source_pool_scale_request",
                "selected_method_id": SELECTED_METHOD,
                "primary_ablation_id": PRIMARY_ABLATION,
                "protected_default_policy_id": PROTECTED_DEFAULT,
                "materialized_source_pose_rows": materialized_for_request,
                "materialized_render_plan_rows": materialized_for_request * len(YAW_OFFSETS_DEG),
                "source_anchor_rows_available": len(anchors),
                "source_anchor_rows_used": len({str(item[0].get("observation_pose_id")) for item in plan}),
                "materialization_status": "ready" if materialized_for_request == pose_budget else "blocked",
                "claim_boundary": (
                    "M192 request row freezes the scale denominator and source-pool budget only; "
                    "no render, detector, goal, or trajectory claim is made."
                ),
            }
        )

    return request_rows, pose_rows, missing_anchor_rows, anchor_audit_rows


def build_render_plan_rows(pose_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frame_index_by_scan: Counter[str] = Counter()
    for pose in sorted(
        pose_rows,
        key=lambda row: (
            str(row.get("scene_key")),
            str(row.get("adapter_episode_id")),
            int(row.get("observation_pose_index") or 0),
        ),
    ):
        scan_id = str(pose.get("scan_id"))
        sequence = DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"
        for yaw in YAW_OFFSETS_DEG:
            frame_index = frame_index_by_scan[scan_id]
            frame_index_by_scan[scan_id] += 1
            frame_id = f"frame-{frame_index:06d}"
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "source_pool_render_plan",
                    "scale_denominator_id": pose.get("scale_denominator_id"),
                    "scale_request_uid": pose.get("scale_request_uid"),
                    "scale_batch_id": pose.get("scale_batch_id"),
                    "adapter_episode_id": pose.get("adapter_episode_id"),
                    "benchmark_row_uid": pose.get("benchmark_row_uid"),
                    "trigger_row_uid": pose.get("trigger_row_uid"),
                    "scan_id": scan_id,
                    "scene_key": pose.get("scene_key"),
                    "object_category": pose.get("object_category"),
                    "selected_method_id": pose.get("selected_method_id"),
                    "primary_ablation_id": pose.get("primary_ablation_id"),
                    "protected_default_policy_id": pose.get("protected_default_policy_id"),
                    "route_id": pose.get("route_id"),
                    "observation_pose_id": pose.get("observation_pose_id"),
                    "observation_pose_index": pose.get("observation_pose_index"),
                    "pose_family": pose.get("pose_family"),
                    "pose_role": pose.get("pose_role"),
                    "frame_id": frame_id,
                    "frame_index": frame_index,
                    "bearing_relative_deg": pose.get("bearing_relative_deg"),
                    "shell_radius_m": pose.get("shell_radius_m"),
                    "render_source": "e008_m192_source_pool_protected_confidence_scale_denominator_materialization",
                    "render_width": RENDER_WIDTH,
                    "render_height": RENDER_HEIGHT,
                    "hm3d_scene_docker_path": pose.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": pose.get("hm3d_navmesh_docker_path"),
                    "planned_source_position": pose.get("planned_position_m"),
                    "source_position": pose.get("source_position"),
                    "source_position_source": "E008-M192 source_pool_observation_pose_rows",
                    "source_rotation": pose.get("source_rotation"),
                    "source_rotation_xyzw": pose.get("source_rotation_xyzw"),
                    "yaw_offset_deg": yaw,
                    "requires_navmesh_snap_validation": True,
                    "source_snap_validation_ready": False,
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_success_label_for_policy": False,
                    "uses_target_object_id_or_success_label": False,
                    "expected_color": str(sequence / f"{frame_id}.color.jpg"),
                    "expected_depth": str(sequence / f"{frame_id}.depth.pgm"),
                    "expected_pose": str(sequence / f"{frame_id}.pose.txt"),
                }
            )
    return rows


def build_expected_file_summary_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row.get("scan_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for scan_id, scan_rows in sorted(grouped.items()):
        sequence = DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"
        rows.append(
            {
                "version": VERSION,
                "row_type": "expected_render_file_summary",
                "scale_request_uid": scan_rows[0].get("scale_request_uid"),
                "scale_batch_id": scan_rows[0].get("scale_batch_id"),
                "scan_id": scan_id,
                "adapter_episode_id": scan_rows[0].get("adapter_episode_id"),
                "scene_key": scan_rows[0].get("scene_key"),
                "object_category": scan_rows[0].get("object_category"),
                "sequence_dir": str(sequence),
                "expected_color_frames": len(scan_rows),
                "expected_depth_frames": len(scan_rows),
                "expected_pose_frames": len(scan_rows),
                "expected_info_files": 1,
                "expected_total_files": len(scan_rows) * 3 + 1,
            }
        )
    return rows


def build_batch_rows(request_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in request_rows:
        grouped[str(row.get("scale_batch_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for batch_id, batch_rows in sorted(grouped.items()):
        rows.append(
            {
                "version": VERSION,
                "row_type": "m192_scale_batch",
                "scale_batch_id": batch_id,
                "scale_denominator_id": SELECTED_DENOMINATOR,
                "request_rows": len(batch_rows),
                "source_pose_rows": sum(int(row.get("materialized_source_pose_rows") or 0) for row in batch_rows),
                "render_plan_rows": sum(int(row.get("materialized_render_plan_rows") or 0) for row in batch_rows),
                "scene_keys": sorted({str(row.get("scene_key")) for row in batch_rows}),
                "object_categories": sorted({str(row.get("object_category")) for row in batch_rows}),
                "job_status": "materialized_not_launched",
                "render_or_detector_long_job_launch_now": False,
            }
        )
    return rows


def build_readiness_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m191_contract_ready",
            "gate_status": "pass" if coverage.get("m191_contract_ready") else "fail",
            "observed": coverage.get("input_m191_status"),
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate_id": "all_seed_requests_materialized",
            "gate_status": "pass" if coverage.get("all_seed_requests_materialized") else "fail",
            "observed": {
                "seed_request_rows": coverage.get("seed_request_rows"),
                "materialized_request_rows": coverage.get("materialized_request_rows"),
                "missing_source_anchor_rows": coverage.get("missing_source_anchor_rows"),
            },
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate_id": "source_pose_and_render_budget_match",
            "gate_status": "pass" if coverage.get("source_pose_and_render_budget_match") else "fail",
            "observed": {
                "expected_source_pose_rows": coverage.get("expected_source_pose_rows"),
                "source_pose_rows": coverage.get("source_pose_rows"),
                "expected_render_plan_rows": coverage.get("expected_render_plan_rows"),
                "render_plan_rows": coverage.get("render_plan_rows"),
            },
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate_id": "blocked_input_audit",
            "gate_status": "pass" if coverage.get("blocked_input_hit_rows") == 0 else "fail",
            "observed": coverage.get("blocked_input_hit_rows"),
            "next_action": "Do not continue until ObjectNav goal/viewpoint and success-label leakage is removed.",
        },
        {
            "version": VERSION,
            "gate_id": "long_job_launch_guard",
            "gate_status": "pass" if not coverage.get("render_or_detector_long_job_launched") else "fail",
            "observed": coverage.get("render_or_detector_long_job_launched"),
            "next_action": "M193 must record snap validation and launcher contract before any render/detector launch.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_scale_denominator_materialization",
            "supported": True,
            "claim_boundary": (
                "M192 supports only leakage-audited materialization of the M191 30-episode scale denominator."
            ),
        },
        {
            "version": VERSION,
            "claim_id": "supported_source_pool_acquisition_test_setup",
            "supported": True,
            "claim_boundary": (
                "M192 freezes the source-pool acquisition rows needed to compare against the no-source-pool "
                "detector-confidence ablation after downstream detector/trajectory gates."
            ),
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_render_detector_recovery",
            "supported": False,
            "claim_boundary": "M192 does not render RGB-D frames or run open-vocabulary detector inference.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M192 does not execute Habitat trajectories and cannot support SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": (
                "Final RGB-D/open-vocabulary robustness requires M193+ launch, detector outputs, heldout scale, "
                "ablation comparison, and external baseline checks."
            ),
        },
    ]


def build_reviewer_defense_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why materialize all 30 triggered episodes after M177 used only 8?",
            "answer": (
                "M177 was a bounded smoke test. M191 selected the first scale denominator as all triggered "
                "HM3D ObjectNav val_mini episodes to test whether source-pool acquisition generalizes beyond "
                "the diagnostic subset."
            ),
            "evidence": {
                "seed_request_rows": coverage.get("seed_request_rows"),
                "source_pose_rows": coverage.get("source_pose_rows"),
                "render_plan_rows": coverage.get("render_plan_rows"),
            },
        },
        {
            "version": VERSION,
            "question": "Does M192 change ranking to make the method look better?",
            "answer": (
                "No. M192 only expands candidate-source acquisition. The execution default remains protected "
                "detector-confidence, and the primary ablation is no-source-pool detector-confidence."
            ),
            "evidence": {
                "selected_method_id": SELECTED_METHOD,
                "protected_default_policy_id": PROTECTED_DEFAULT,
                "primary_ablation_id": PRIMARY_ABLATION,
            },
        },
        {
            "version": VERSION,
            "question": "Why not launch render/detector immediately?",
            "answer": (
                "M192 is the denominator/materialization gate. M193 must first validate navmesh/snap and write "
                "the long-job command contract before any background render/detector job."
            ),
            "evidence": {"selected_next_unit": NEXT_UNIT, "long_job_launched": False},
        },
    ]


def build_route_decision_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    ready = coverage.get("status") == READY_STATUS
    return [
        {
            "version": VERSION,
            "decision_id": "selected_next_unit",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M192 materialization blockers",
            "render_or_detector_long_job_launch_now": False,
            "trajectory_execution_now": False,
            "reason": (
                "Scale denominator source-pose/render-plan rows are materialized; M193 must perform snap "
                "validation and launcher contract."
                if ready
                else "M192 blockers must be resolved before launcher planning."
            ),
        },
        {
            "version": VERSION,
            "decision_id": "method_family_for_scale",
            "selected": True,
            "selected_method_id": SELECTED_METHOD,
            "safe_execution_default": PROTECTED_DEFAULT,
            "primary_ablation_id": PRIMARY_ABLATION,
            "reason": "Isolate source-pool acquisition gain from ranking changes under protected detector-confidence.",
        },
    ]


def build_command_ledger_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "command_id": "m192_materialize_scale_denominator",
            "stage": "materialization",
            "long_job": False,
            "status": "ready",
            "working_directory": str(ROOT),
            "command": (
                "python experiments/E008_real_navigation_benchmark/tools/"
                "run_m192_source_pool_protected_confidence_scale_denominator_materialization.py"
            ),
            "output_path": str(ARTIFACT_DIR),
            "expected_files": [
                "coverage.json",
                "source_pool_scale_request_rows.jsonl",
                "source_pool_observation_pose_rows.jsonl",
                "source_pool_render_plan_rows.jsonl",
                "source_anchor_audit_rows.jsonl",
            ],
            "verification_command": (
                "python - <<'PY'\n"
                "import json\n"
                "from pathlib import Path\n"
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/"
                "E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status'].endswith('_ready') and c['source_pose_rows']==240 and c['render_plan_rows']==960\n"
                "PY"
            ),
        },
        {
            "version": VERSION,
            "command_id": "m193_snap_launcher_contract",
            "stage": "next_unit",
            "long_job": False,
            "status": "planned_next",
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/plan_m193_source_pool_scale_navmesh_snap_launcher_contract.py",
            "output_path": (
                "experiments/E008_real_navigation_benchmark/artifacts/"
                "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0/"
            ),
            "expected_files": ["coverage.json", "snap_validation_rows.jsonl", "long_job_command_rows.jsonl"],
            "verification_command": "inspect coverage.json status and m194 launch readiness",
        },
    ]


def build_report(coverage: dict[str, Any]) -> str:
    summary_rows = [
        {
            "metric": "seed_request_rows",
            "value": coverage.get("seed_request_rows"),
        },
        {
            "metric": "source_pose_rows",
            "value": coverage.get("source_pose_rows"),
        },
        {
            "metric": "render_plan_rows",
            "value": coverage.get("render_plan_rows"),
        },
        {
            "metric": "missing_source_anchor_rows",
            "value": coverage.get("missing_source_anchor_rows"),
        },
        {
            "metric": "blocked_input_hit_rows",
            "value": coverage.get("blocked_input_hit_rows"),
        },
        {
            "metric": "m193_gate_ready",
            "value": coverage.get("m193_gate_ready"),
        },
    ]
    return "\n".join(
        [
            "# E008-M192 Source-Pool Protected-Confidence Scale Denominator Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Scale denominator: `{coverage['scale_denominator_id']}`.",
            f"- Seed request rows: {coverage['seed_request_rows']}.",
            f"- Source pose rows: {coverage['source_pose_rows']} / expected {coverage['expected_source_pose_rows']}.",
            f"- Render plan rows: {coverage['render_plan_rows']} / expected {coverage['expected_render_plan_rows']}.",
            f"- Scale batches: {coverage['scale_batch_count']}.",
            f"- Missing source-anchor rows: {coverage['missing_source_anchor_rows']}.",
            f"- Blocked input hit rows: {coverage['blocked_input_hit_rows']}.",
            f"- Render/detector long job launched: {str(coverage['render_or_detector_long_job_launched']).lower()}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Summary Table",
            "",
            table(summary_rows, ["metric", "value"]),
            "",
            "## Claim Boundary",
            "",
            "- M192 supports scale denominator/source-pose/render-plan materialization only.",
            "- M192 does not render frames, run detectors, evaluate goal recovery, or execute trajectories.",
            "- Real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, and human-intent main claim remain blocked.",
            "",
            "## Next",
            "",
            f"- {NEXT_UNIT}.",
            "",
        ]
    )


def copy_rows_to_data_dir(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for source in files:
        shutil.copyfile(source, DATA_OUT_DIR / source.name)
    render_inputs = DATA_OUT_DIR / "render_inputs"
    render_inputs.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl", render_inputs / "render_plan_rows.jsonl")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m191_coverage = read_json(M191_DIR / "coverage.json")
    seed_rows = read_jsonl(M191_DIR / "m192_materialization_seed_rows.jsonl")
    candidate_rows = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")
    grouped_anchors = anchors_by_benchmark(candidate_rows)

    request_rows, pose_rows, missing_anchor_rows, anchor_audit_rows = build_pose_rows(seed_rows, grouped_anchors)
    render_rows = build_render_plan_rows(pose_rows)
    expected_file_rows = build_expected_file_summary_rows(render_rows)
    batch_rows = build_batch_rows(request_rows)
    blocked_rows = target_leakage_rows([*request_rows, *pose_rows, *render_rows])

    expected_source_pose_rows = sum(
        min(MAX_SOURCE_POSES_PER_REQUEST, int_or_default(row.get("planned_source_pose_rows"), MAX_SOURCE_POSES_PER_REQUEST))
        for row in seed_rows
    )
    expected_render_plan_rows = sum(
        int_or_default(row.get("planned_render_plan_rows"), MAX_SOURCE_POSES_PER_REQUEST * len(YAW_OFFSETS_DEG))
        for row in seed_rows
    )

    blockers: list[str] = []
    if m191_coverage.get("status") != "e008_m191_source_pool_protected_confidence_scaleup_contract_ready":
        blockers.append("m191_contract_not_ready")
    if not seed_rows:
        blockers.append("no_m191_seed_rows")
    if len(request_rows) != len(seed_rows):
        blockers.append("request_row_count_mismatch")
    if missing_anchor_rows:
        blockers.append("missing_source_anchor")
    if len(pose_rows) != expected_source_pose_rows:
        blockers.append("source_pose_row_count_mismatch")
    if len(render_rows) != expected_render_plan_rows:
        blockers.append("render_plan_row_count_mismatch")
    if blocked_rows:
        blockers.append("blocked_input_hit")

    status = READY_STATUS if not blockers else BLOCKED_STATUS
    unique_scenes = sorted({str(row.get("scene_key")) for row in seed_rows})
    unique_categories = sorted({str(row.get("object_category")) for row in seed_rows})
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "input_m191_status": m191_coverage.get("status"),
        "m191_contract_ready": m191_coverage.get("status")
        == "e008_m191_source_pool_protected_confidence_scaleup_contract_ready",
        "scale_denominator_id": SELECTED_DENOMINATOR,
        "selected_method_id": SELECTED_METHOD,
        "primary_ablation_id": PRIMARY_ABLATION,
        "protected_default_policy_id": PROTECTED_DEFAULT,
        "kept_method_component": SOURCE_POOL_COMPONENT,
        "seed_request_rows": len(seed_rows),
        "materialized_request_rows": len(request_rows),
        "all_seed_requests_materialized": len(request_rows) == len(seed_rows) and not missing_anchor_rows,
        "scale_scene_count": len(unique_scenes),
        "scale_category_count": len(unique_categories),
        "scale_scenes": unique_scenes,
        "scale_categories": unique_categories,
        "scale_batch_count": len({str(row.get("scale_batch_id")) for row in request_rows}),
        "source_anchor_candidate_rows": len(candidate_rows),
        "source_anchor_request_rows_available": sum(
            1 for row in seed_rows if grouped_anchors.get(str(row.get("benchmark_row_uid")))
        ),
        "source_anchor_audit_rows": len(anchor_audit_rows),
        "source_pose_rows": len(pose_rows),
        "expected_source_pose_rows": expected_source_pose_rows,
        "render_plan_rows": len(render_rows),
        "expected_render_plan_rows": expected_render_plan_rows,
        "source_pose_and_render_budget_match": (
            len(pose_rows) == expected_source_pose_rows and len(render_rows) == expected_render_plan_rows
        ),
        "source_pose_budget_per_episode": MAX_SOURCE_POSES_PER_REQUEST,
        "yaw_samples_per_pose": len(YAW_OFFSETS_DEG),
        "expected_file_summary_rows": len(expected_file_rows),
        "missing_source_anchor_rows": len(missing_anchor_rows),
        "blocked_input_hit_rows": len(blocked_rows),
        "uses_objectnav_target_for_source_placement": bool(blocked_rows),
        "m193_gate_ready": not blockers,
        "source_pose_output": str(DATA_OUT_DIR / "source_pool_observation_pose_rows.jsonl"),
        "render_plan_output": str(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl"),
        "render_or_detector_long_job_launched": False,
        "docker_trajectory_execution_now": False,
        "detector_candidate_rows_ready": False,
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if not blockers else "repair E008-M192 materialization blockers",
    }

    readiness_rows = build_readiness_rows(coverage)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows(coverage)
    route_rows = build_route_decision_rows(coverage)
    command_rows = build_command_ledger_rows()

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_pool_scale_request_rows.jsonl", request_rows)
    write_jsonl(ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl", pose_rows)
    write_jsonl(ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl", render_rows)
    write_jsonl(ARTIFACT_DIR / "source_anchor_audit_rows.jsonl", anchor_audit_rows)
    write_jsonl(ARTIFACT_DIR / "missing_source_anchor_rows.jsonl", missing_anchor_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_audit_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "scale_batch_rows.jsonl", batch_rows)
    write_jsonl(ARTIFACT_DIR / "expected_render_file_summary_rows.jsonl", expected_file_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "command_ledger_rows.jsonl", command_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))

    copy_rows_to_data_dir(
        [
            ARTIFACT_DIR / "source_pool_scale_request_rows.jsonl",
            ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl",
            ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl",
            ARTIFACT_DIR / "source_anchor_audit_rows.jsonl",
            ARTIFACT_DIR / "scale_batch_rows.jsonl",
            ARTIFACT_DIR / "expected_render_file_summary_rows.jsonl",
        ]
    )

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
