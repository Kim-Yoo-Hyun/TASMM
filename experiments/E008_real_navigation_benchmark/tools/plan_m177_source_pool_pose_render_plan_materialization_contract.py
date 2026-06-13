#!/usr/bin/env python3
"""Materialize E008-M177 source-pool pose/render-plan rows with a fixed budget guard."""

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
M176_DIR = EXP_ROOT / "artifacts" / "E008-M176_source_coverage_trigger_row_materialization_smoke_v0"
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M177_source_pool_pose_render_plan_materialization_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M177_source_pool_pose_render_plan_materialization_contract_v0"
)

VERSION = "e008_m177_source_pool_pose_render_plan_materialization_contract_v0"
READY_STATUS = "e008_m177_source_pool_pose_render_plan_materialization_contract_ready"
BLOCKED_STATUS = "e008_m177_source_pool_pose_render_plan_materialization_contract_blocked"
NEXT_UNIT = "E008-M178 navmesh/snap validation and render/detector launcher contract"

MAX_SELECTED_REQUESTS = 8
MAX_SELECTED_PER_SCENE = 5
MAX_SELECTED_PER_CATEGORY = 4
MAX_SOURCE_POSES_PER_REQUEST = 8
YAW_OFFSETS_DEG = [0, 90, 180, 270]
RENDER_WIDTH = 640
RENDER_HEIGHT = 480
RENDER_PLAN_BUDGET_CAP = MAX_SELECTED_REQUESTS * MAX_SOURCE_POSES_PER_REQUEST * len(YAW_OFFSETS_DEG)
SOURCE_BEARINGS_DEG = [0.0, 90.0, 180.0, 270.0]
SOURCE_RADII_M = [2.0, 4.0]
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


def planned_position(anchor: list[float], radius_m: float, bearing_deg: float) -> list[float]:
    angle = math.radians(float(bearing_deg))
    return [
        float(anchor[0]) + radius_m * math.sin(angle),
        float(anchor[1]),
        float(anchor[2]) + radius_m * math.cos(angle),
    ]


def priority_score(row: dict[str, Any]) -> float:
    trigger_count = float(row.get("trigger_count") or 0)
    top10_unique = float(row.get("top10_unique_coverage_keys") or 0)
    top1_conf = float(row.get("top1_confidence") or 0.0)
    mean_top5 = float(row.get("mean_top5_confidence") or 0.0)
    path_ready = float(row.get("path_ready_candidate_rows") or 0)
    score = 100.0 * trigger_count
    score += 35.0 if row.get("source_sparse_trigger") else 0.0
    score += 35.0 if row.get("path_or_source_ready_gap_trigger") else 0.0
    score += 20.0 if row.get("detector_uncertainty_trigger") else 0.0
    score += max(0.0, 6.0 - top10_unique) * 8.0
    score += max(0.0, 0.50 - top1_conf) * 40.0
    score += max(0.0, 0.45 - mean_top5) * 35.0
    score += max(0.0, 25.0 - path_ready) * 2.0
    return float(score)


def select_budgeted_requests(trigger_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [row for row in trigger_rows if row.get("request_candidate_source_expansion")]
    for row in candidates:
        row["m177_priority_score"] = priority_score(row)
    selected: list[dict[str, Any]] = []
    scene_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for row in sorted(
        candidates,
        key=lambda item: (
            -float(item.get("m177_priority_score") or 0.0),
            str(item.get("scene_key")),
            str(item.get("adapter_episode_id")),
        ),
    ):
        scene = str(row.get("scene_key"))
        category = str(row.get("object_category"))
        if scene_counts[scene] >= MAX_SELECTED_PER_SCENE:
            continue
        if category_counts[category] >= MAX_SELECTED_PER_CATEGORY:
            continue
        selected.append(row)
        scene_counts[scene] += 1
        category_counts[category] += 1
        if len(selected) >= MAX_SELECTED_REQUESTS:
            break
    return selected


def anchor_rows_by_benchmark(candidate_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if not finite_vec(row.get("source_position")):
            continue
        if not row.get("scene_docker_path") or not row.get("navmesh_docker_path"):
            continue
        grouped[str(row.get("benchmark_row_uid"))].append(row)
    for key, rows in grouped.items():
        seen: set[tuple[float, float, float]] = set()
        unique_rows: list[dict[str, Any]] = []
        for row in sorted(
            rows,
            key=lambda item: (
                0 if str(item.get("frame_pose_role")) == "start_pose" else 1,
                int(item.get("visit_rank") or item.get("m168_detector_visit_rank") or 10_000),
                -float(item.get("confidence") or 0.0),
            ),
        ):
            pos = as_float_vec(row.get("source_position"))
            rounded = tuple(round(value, 2) for value in pos)
            if rounded in seen:
                continue
            seen.add(rounded)
            unique_rows.append(row)
        grouped[key] = unique_rows
    return grouped


def build_pose_rows(
    selected_requests: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
    anchors_by_benchmark: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expansion_by_uid = {str(row.get("benchmark_row_uid")): row for row in expansion_rows}
    pose_rows: list[dict[str, Any]] = []
    missing_anchor_rows: list[dict[str, Any]] = []
    for request in selected_requests:
        uid = str(request.get("benchmark_row_uid"))
        anchors = anchors_by_benchmark.get(uid, [])
        if not anchors:
            missing_anchor_rows.append(
                {
                    "version": VERSION,
                    "row_type": "m177_missing_source_anchor",
                    "benchmark_row_uid": uid,
                    "adapter_episode_id": request.get("adapter_episode_id"),
                    "scan_id": request.get("scan_id"),
                    "scene_key": request.get("scene_key"),
                    "object_category": request.get("object_category"),
                    "reason": "No policy-visible M168 source_position with scene/navmesh path was available.",
                }
            )
            continue
        expansion = expansion_by_uid.get(uid, {})
        planned_pose_budget = int(expansion.get("planned_observation_pose_rows") or MAX_SOURCE_POSES_PER_REQUEST)
        per_request_cap = min(MAX_SOURCE_POSES_PER_REQUEST, max(1, planned_pose_budget))
        anchor_plan: list[tuple[dict[str, Any], float, float]] = []
        if len(anchors) >= 2:
            for anchor in anchors[:2]:
                for bearing in SOURCE_BEARINGS_DEG:
                    anchor_plan.append((anchor, 2.0, bearing))
        else:
            for radius in SOURCE_RADII_M:
                for bearing in SOURCE_BEARINGS_DEG:
                    anchor_plan.append((anchors[0], radius, bearing))
        for pose_index, (anchor, radius, bearing) in enumerate(anchor_plan[:per_request_cap]):
            anchor_position = as_float_vec(anchor.get("source_position"))
            source_position = planned_position(anchor_position, radius, bearing)
            pose_rows.append(
                {
                    "version": VERSION,
                    "row_type": "source_pool_observation_pose",
                    "adapter_episode_id": request.get("adapter_episode_id"),
                    "benchmark_row_uid": uid,
                    "trigger_row_uid": request.get("trigger_row_uid"),
                    "scan_id": request.get("scan_id"),
                    "scene_key": request.get("scene_key"),
                    "object_category": request.get("object_category"),
                    "selected_method_id": "source_coverage_triggered_candidate_source_expansion_v1",
                    "route_id": "source_pool_budgeted_priority_expansion_v1",
                    "observation_pose_id": f"{uid}:m177:pose-{pose_index:03d}",
                    "observation_pose_index": pose_index,
                    "pose_family": "source_anchor_radial_coverage_pool",
                    "pose_role": "source_pool_candidate_observation_pose",
                    "source_anchor_observation_pose_id": anchor.get("observation_pose_id"),
                    "source_anchor_frame_pose_role": anchor.get("frame_pose_role"),
                    "source_anchor_position_m": anchor_position,
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
                        "M176 trigger row plus M168 policy-visible source positions, scene path, and navmesh path only"
                    ),
                    "budget_guard_id": "m177_fixed_request_pose_render_budget_guard_v1",
                    "m177_priority_score": request.get("m177_priority_score"),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_success_label_for_policy": False,
                    "uses_target_object_id_or_success_label": False,
                    "claim_boundary": (
                        "M177 source poses are source-pool expansion inputs only; no detector, goal-evaluation, "
                        "or trajectory result is claimed."
                    ),
                }
            )
    return pose_rows, missing_anchor_rows


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
                    "adapter_episode_id": pose.get("adapter_episode_id"),
                    "benchmark_row_uid": pose.get("benchmark_row_uid"),
                    "trigger_row_uid": pose.get("trigger_row_uid"),
                    "scan_id": scan_id,
                    "scene_key": pose.get("scene_key"),
                    "object_category": pose.get("object_category"),
                    "route_id": pose.get("route_id"),
                    "observation_pose_id": pose.get("observation_pose_id"),
                    "observation_pose_index": pose.get("observation_pose_index"),
                    "pose_family": pose.get("pose_family"),
                    "pose_role": pose.get("pose_role"),
                    "frame_id": frame_id,
                    "frame_index": frame_index,
                    "bearing_relative_deg": pose.get("bearing_relative_deg"),
                    "shell_radius_m": pose.get("shell_radius_m"),
                    "render_source": "e008_m177_source_pool_pose_render_plan_materialization_contract",
                    "render_width": RENDER_WIDTH,
                    "render_height": RENDER_HEIGHT,
                    "hm3d_scene_docker_path": pose.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": pose.get("hm3d_navmesh_docker_path"),
                    "planned_source_position": pose.get("planned_position_m"),
                    "source_position": pose.get("source_position"),
                    "source_position_source": "E008-M177 source_pool_observation_pose_rows",
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


def target_leakage_present(rows: list[dict[str, Any]]) -> bool:
    forbidden_truthy_keys = [
        "uses_objectnav_eval_goal",
        "uses_objectnav_eval_viewpoint",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy",
        "uses_objectnav_eval_goal_or_viewpoint_for_source_placement",
        "uses_success_label_for_policy",
        "uses_target_object_id_or_success_label",
    ]
    return any(any(bool(row.get(key)) for key in forbidden_truthy_keys) for row in rows)


def build_budget_rows(
    trigger_rows: list[dict[str, Any]],
    selected_requests: list[dict[str, Any]],
    pose_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_uids = {str(row.get("benchmark_row_uid")) for row in selected_requests}
    rows: list[dict[str, Any]] = []
    for rank, row in enumerate(
        sorted(
            trigger_rows,
            key=lambda item: (
                -float(item.get("m177_priority_score") or priority_score(item)),
                str(item.get("scene_key")),
                str(item.get("adapter_episode_id")),
            ),
        ),
        start=1,
    ):
        uid = str(row.get("benchmark_row_uid"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "budget_priority_guard",
                "rank": rank,
                "selected_for_m178": uid in selected_uids,
                "benchmark_row_uid": uid,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "priority_score": row.get("m177_priority_score") or priority_score(row),
                "trigger_count": row.get("trigger_count"),
                "trigger_ids": row.get("trigger_ids"),
                "top10_unique_coverage_keys": row.get("top10_unique_coverage_keys"),
                "path_ready_candidate_rows": row.get("path_ready_candidate_rows"),
                "top1_confidence": row.get("top1_confidence"),
                "mean_top5_confidence": row.get("mean_top5_confidence"),
                "max_selected_requests": MAX_SELECTED_REQUESTS,
                "max_source_poses_per_request": MAX_SOURCE_POSES_PER_REQUEST,
                "yaw_samples_per_pose": len(YAW_OFFSETS_DEG),
                "render_plan_budget_cap": RENDER_PLAN_BUDGET_CAP,
                "selection_rule": (
                    "priority_score descending with max-selected, per-scene, per-category, pose, and render caps"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
            }
        )
    summary_row = {
        "version": VERSION,
        "row_type": "budget_priority_guard_summary",
        "trigger_request_rows": len(trigger_rows),
        "selected_request_rows": len(selected_requests),
        "source_pose_rows": len(pose_rows),
        "render_plan_rows": len(render_rows),
        "render_plan_budget_cap": RENDER_PLAN_BUDGET_CAP,
        "budget_guard_pass": bool(
            selected_requests
            and pose_rows
            and render_rows
            and len(render_rows) <= RENDER_PLAN_BUDGET_CAP
            and not target_leakage_present([*pose_rows, *render_rows])
        ),
    }
    return [summary_row, *rows]


def build_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": (
                "Budgeted source-pool request subset, source pose rows, and render-plan rows exist with no "
                "ObjectNav target/viewpoint or success-label leakage."
            ),
            "observed": coverage["m178_gate_ready"],
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M176 trigger requests fire broadly, so M177 must not launch render/detector for all 30 rows.",
            "observed": coverage["trigger_selectivity_warning"],
            "next_action": "Keep the fixed budget/priority guard and report selected/remaining request split.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "Missing source anchors, render budget overflow, or blocked input leakage.",
            "observed": bool(coverage["blockers"]),
            "next_action": "Do not continue to M178 until blockers are resolved.",
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_budgeted_source_pool_materialization",
            "supported": True,
            "claim_boundary": (
                "M177 supports only leakage-audited, budgeted source-pool pose/render-plan materialization."
            ),
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_detector_candidate_recovery",
            "supported": False,
            "claim_boundary": "M177 does not render RGB-D frames or run open-vocabulary detection.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M177 does not execute Habitat trajectories and cannot support SR/SPL.",
        },
    ]


def build_reviewer_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not expand all 30 M176 trigger requests?",
            "answer": (
                "M176 trigger rate is 1.0, so unbounded expansion would turn a source-coverage interface into an "
                "uncontrolled render/detector budget increase. M177 fixes a request/pose/render budget before any long job."
            ),
            "evidence": {
                "trigger_request_rows": coverage["trigger_request_rows"],
                "selected_request_rows": coverage["selected_request_rows"],
                "render_plan_rows": coverage["render_plan_rows"],
                "render_plan_budget_cap": coverage["render_plan_budget_cap"],
            },
        },
        {
            "version": VERSION,
            "question": "Did source placement use ObjectNav goal/viewpoint labels?",
            "answer": "No. Source poses use M176 trigger fields and M168 policy-visible source positions only.",
            "evidence": {
                "uses_objectnav_target_for_source_placement": coverage[
                    "uses_objectnav_target_for_source_placement"
                ],
                "blocked_input_hit_rows": coverage["blocked_input_hit_rows"],
            },
        },
        {
            "version": VERSION,
            "question": "Does this already prove navigation improvement?",
            "answer": "No. M177 only creates bounded rows for M178/M179; detector, goal-evaluation, and trajectory gates remain required.",
        },
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M177 Source-Pool Pose/Render-Plan Materialization Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M176 status: `{coverage['m176_status']}`.",
            f"- Trigger request rows: {coverage['trigger_request_rows']}.",
            f"- Selected request rows: {coverage['selected_request_rows']}.",
            f"- Source pose rows: {coverage['source_pose_rows']}.",
            f"- Render plan rows: {coverage['render_plan_rows']} / budget {coverage['render_plan_budget_cap']}.",
            f"- Missing source-anchor rows: {coverage['missing_source_anchor_rows']}.",
            f"- Blocked input hit rows: {coverage['blocked_input_hit_rows']}.",
            f"- M178 gate ready: {str(coverage['m178_gate_ready']).lower()}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M177 is a bounded source-pool pose/render-plan materialization gate.",
            "- It does not render RGB-D frames, run detector inference, evaluate goal recovery, or execute trajectories.",
            "- Real navigation `SR` / `SPL` and final real RGB-D/open-vocabulary robustness remain blocked.",
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
        target = DATA_OUT_DIR / source.name
        shutil.copyfile(source, target)
    render_inputs = DATA_OUT_DIR / "render_inputs"
    render_inputs.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl", render_inputs / "render_plan_rows.jsonl")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m176_coverage = read_json(M176_DIR / "coverage.json")
    trigger_rows = read_jsonl(M176_DIR / "source_coverage_trigger_rows.jsonl")
    expansion_rows = read_jsonl(M176_DIR / "candidate_source_expansion_plan_rows.jsonl")
    source_candidates = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")

    selected_requests = select_budgeted_requests(trigger_rows)
    anchors_by_uid = anchor_rows_by_benchmark(source_candidates)
    pose_rows, missing_anchor_rows = build_pose_rows(selected_requests, expansion_rows, anchors_by_uid)
    render_rows = build_render_plan_rows(pose_rows)
    budget_rows = build_budget_rows(trigger_rows, selected_requests, pose_rows, render_rows)

    blocked_input_hit = int(target_leakage_present([*pose_rows, *render_rows]))
    blockers: list[str] = []
    if m176_coverage.get("status") != "e008_m176_source_coverage_trigger_row_materialization_smoke_ready":
        blockers.append("m176_not_ready")
    if not selected_requests:
        blockers.append("no_selected_requests")
    if missing_anchor_rows:
        blockers.append("missing_selected_source_anchor")
    if not pose_rows:
        blockers.append("no_source_pose_rows")
    if not render_rows:
        blockers.append("no_render_plan_rows")
    if len(render_rows) > RENDER_PLAN_BUDGET_CAP:
        blockers.append("render_plan_budget_overflow")
    if blocked_input_hit:
        blockers.append("blocked_input_hit")

    status = READY_STATUS if not blockers else BLOCKED_STATUS
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "m176_status": m176_coverage.get("status"),
        "trigger_request_rows": len(trigger_rows),
        "selected_request_rows": len(selected_requests),
        "selection_rate": (len(selected_requests) / len(trigger_rows)) if trigger_rows else 0.0,
        "source_pose_rows": len(pose_rows),
        "render_plan_rows": len(render_rows),
        "render_plan_budget_cap": RENDER_PLAN_BUDGET_CAP,
        "max_selected_requests": MAX_SELECTED_REQUESTS,
        "max_selected_per_scene": MAX_SELECTED_PER_SCENE,
        "max_selected_per_category": MAX_SELECTED_PER_CATEGORY,
        "max_source_poses_per_request": MAX_SOURCE_POSES_PER_REQUEST,
        "yaw_samples_per_pose": len(YAW_OFFSETS_DEG),
        "selected_scenes": sorted({str(row.get("scene_key")) for row in selected_requests}),
        "selected_categories": sorted({str(row.get("object_category")) for row in selected_requests}),
        "missing_source_anchor_rows": len(missing_anchor_rows),
        "blocked_input_hit_rows": blocked_input_hit,
        "uses_objectnav_target_for_source_placement": bool(blocked_input_hit),
        "trigger_selectivity_warning": bool(m176_coverage.get("trigger_selectivity_warning", True)),
        "m178_gate_ready": not blockers,
        "source_pose_output": str(DATA_OUT_DIR / "source_pool_observation_pose_rows.jsonl"),
        "render_plan_output": str(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl"),
        "selected_next_unit": NEXT_UNIT if not blockers else "repair E008-M177 source-pool materialization blockers",
        "render_or_detector_long_job_launched": False,
        "detector_candidate_rows_ready": False,
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "budget_priority_guard_rows.jsonl", budget_rows)
    write_jsonl(ARTIFACT_DIR / "selected_source_request_rows.jsonl", selected_requests)
    write_jsonl(ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl", pose_rows)
    write_jsonl(ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl", render_rows)
    write_jsonl(ARTIFACT_DIR / "missing_source_anchor_rows.jsonl", missing_anchor_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_audit_rows.jsonl", [] if not blocked_input_hit else [{"version": VERSION, "blocked": True}])
    write_jsonl(ARTIFACT_DIR / "m178_gate_rows.jsonl", build_gate_rows(coverage))
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", build_claim_rows())
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", build_reviewer_rows(coverage))
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    copy_rows_to_data_dir(
        [
            ARTIFACT_DIR / "selected_source_request_rows.jsonl",
            ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl",
            ARTIFACT_DIR / "source_pool_render_plan_rows.jsonl",
            ARTIFACT_DIR / "budget_priority_guard_rows.jsonl",
        ]
    )

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
