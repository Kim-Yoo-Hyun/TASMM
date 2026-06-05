#!/usr/bin/env python3
"""Materialize M93 source-gap two-branch repair rows from the M92 contract."""

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
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M84_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M84_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M86_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"
M87_DIR = EXP_ROOT / "artifacts" / "E008-M87_source_gap_detector_candidate_navmesh_validation_v0"
M88_DIR = EXP_ROOT / "artifacts" / "E008-M88_source_gap_detector_candidate_visit_order_path_smoke_v0"
M89_DIR = EXP_ROOT / "artifacts" / "E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0"
M92_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0"
)

VERSION = "e008_m93_source_gap_two_branch_repair_row_materialization_smoke_v0"
READY_STATUS = "e008_m93_source_gap_two_branch_repair_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m93_source_gap_two_branch_repair_row_materialization_smoke_blocked"
NEXT_UNIT = "E008-M94 source-gap two-branch repair evaluation route decision"

YAW_OFFSETS = [0, 45, 90, 135, 180, 225, 270, 315]
MATERIALIZED_CONTRACT_IDS = {
    "m93_case_repair_assignment",
    "m93_branch_contract_copy",
    "m93_coverage_expansion_observation_plan",
    "m93_cap_threshold_candidate_probe",
    "m93_budget_loss_sentinel",
    "m93_next_long_job_ledger",
}
SAFE_FALSE_FLAG_KEYS = {
    "uses_objectnav_eval_goal",
    "uses_objectnav_eval_viewpoint",
    "uses_objectnav_eval_goal_or_viewpoint_for_policy",
    "rank_uses_eval_distance",
    "runtime_policy_may_use_m91_eval_distances",
    "runtime_policy_may_use_m91_failure_type",
}
FORBIDDEN_POLICY_KEY_SUBSTRINGS = (
    "goal_xz",
    "any_viewpoint",
    "eval_distance",
    "target_near",
    "primary_hit",
    "first_hit",
    "success_label",
)


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


def finite_int(value: object, default: int = 10**9) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def frame_id(row: dict[str, Any]) -> str:
    ids = row.get("frame_ids")
    if isinstance(ids, list) and ids:
        return str(ids[0])
    uid = str(row.get("raw_candidate_uid") or row.get("proposal_uid") or "")
    for part in uid.split(":"):
        if part.startswith("frame-"):
            return part
    return "frame-unknown"


def bbox_area(row: dict[str, Any]) -> float:
    boxes = row.get("bbox_2d")
    if not isinstance(boxes, dict):
        return 0.0
    first = next(iter(boxes.values()), None)
    if not isinstance(first, list) or len(first) != 4:
        return 0.0
    x0, y0, x1, y1 = [finite_float(item) or 0.0 for item in first]
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def detector_label_text(label: str) -> str:
    if label in {"sofa", "toilet", "bed", "chair", "plant"}:
        return f"a {label}"
    return label


def sequence_dir(scan_id: str) -> Path:
    return DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"


def prompt_rows_for_labels(labels: set[str], assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_label: dict[str, set[str]] = defaultdict(set)
    by_label_scan: dict[str, set[str]] = defaultdict(set)
    for row in assignments:
        label = str(row.get("object_category"))
        if label in labels:
            by_label[label].add(label)
            by_label_scan[label].add(str(row.get("scan_id")))
    output: list[dict[str, Any]] = []
    for label in sorted(labels):
        output.append(
            {
                "label_canonical": label,
                "prompts": [detector_label_text(label), label, f"the {label}"],
                "prompt_role": "detector_target",
                "detector_prompt_enabled": True,
                "hm3d_objectnav_categories": sorted(by_label.get(label, {label})),
                "scan_ids": sorted(by_label_scan.get(label, set())),
                "scan_count": len(by_label_scan.get(label, set())),
                "aliases": [],
            }
        )
    return output


def copy_with_version(rows: list[dict[str, Any]], row_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        new_row = dict(row)
        new_row["source_version"] = new_row.get("version")
        new_row["version"] = VERSION
        new_row["row_type"] = row_type
        output.append(new_row)
    return output


def build_coverage_observation_rows(
    assignments: list[dict[str, Any]],
    m84_observation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in m84_observation_rows:
        by_episode[str(row.get("adapter_episode_id"))].append(row)

    output: list[dict[str, Any]] = []
    for assignment in sorted(assignments, key=lambda row: str(row.get("adapter_episode_id"))):
        if assignment.get("branch_id") != "coverage_expansion_branch":
            continue
        episode = str(assignment.get("adapter_episode_id"))
        source_rows = sorted(
            by_episode.get(episode, []),
            key=lambda row: (finite_int(row.get("observation_pose_index")), str(row.get("observation_pose_id"))),
        )
        for index, source in enumerate(source_rows):
            output.append(
                {
                    "version": VERSION,
                    "row_type": "coverage_expansion_observation_plan",
                    "branch_id": "coverage_expansion_branch",
                    "adapter_episode_id": episode,
                    "scan_id": assignment.get("scan_id"),
                    "scene_key": assignment.get("scene_key"),
                    "object_category": assignment.get("object_category"),
                    "route_id": assignment.get("selected_route_id"),
                    "source_route_id": source.get("route_id"),
                    "observation_pose_id": f"{episode}:m93-wide-{index:03d}",
                    "source_observation_pose_id": source.get("observation_pose_id"),
                    "observation_pose_index": index,
                    "pose_family": "m93_wide_shell_frontier_refresh",
                    "pose_role": source.get("pose_role"),
                    "planned_position_m": source.get("planned_position_m"),
                    "planned_rotation_xyzw": source.get("planned_rotation_xyzw"),
                    "source_position_m": source.get("source_position_m"),
                    "source_rotation_xyzw": source.get("source_rotation_xyzw"),
                    "shell_radius_m": source.get("shell_radius_m"),
                    "requires_navmesh_snap_validation": bool(source.get("requires_navmesh_snap_validation")),
                    "hm3d_scene_docker_path": source.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": source.get("hm3d_navmesh_docker_path"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "claim_boundary": "Coverage branch materializes policy-visible source expansion only; target recovery is unclaimed until render/detector/eval gates pass.",
                }
            )
    return output


def build_coverage_render_rows(observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_counts: dict[str, int] = defaultdict(int)
    rows: list[dict[str, Any]] = []
    for obs in sorted(
        observation_rows,
        key=lambda row: (str(row.get("adapter_episode_id")), finite_int(row.get("observation_pose_index"))),
    ):
        scan_id = str(obs.get("scan_id"))
        for yaw in YAW_OFFSETS:
            frame_index = frame_counts[scan_id]
            frame_counts[scan_id] += 1
            frame = f"frame-{frame_index:06d}"
            seq = sequence_dir(scan_id)
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "coverage_expansion_render_plan",
                    "branch_id": obs.get("branch_id"),
                    "adapter_episode_id": obs.get("adapter_episode_id"),
                    "scan_id": scan_id,
                    "scene_key": obs.get("scene_key"),
                    "object_category": obs.get("object_category"),
                    "route_id": obs.get("route_id"),
                    "source_route_id": obs.get("source_route_id"),
                    "observation_pose_id": obs.get("observation_pose_id"),
                    "source_observation_pose_id": obs.get("source_observation_pose_id"),
                    "observation_pose_index": obs.get("observation_pose_index"),
                    "pose_family": obs.get("pose_family"),
                    "pose_role": obs.get("pose_role"),
                    "frame_index": frame_index,
                    "frame_id": frame,
                    "yaw_offset_deg": yaw,
                    "bearing_relative_deg": 0,
                    "render_width": 640,
                    "render_height": 480,
                    "render_source": "e008_m93_coverage_expansion_source_gap_repair",
                    "source_position": obs.get("planned_position_m"),
                    "source_rotation": obs.get("planned_rotation_xyzw"),
                    "shell_radius_m": obs.get("shell_radius_m"),
                    "requires_navmesh_snap_validation": bool(obs.get("requires_navmesh_snap_validation")),
                    "hm3d_scene_docker_path": obs.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": obs.get("hm3d_navmesh_docker_path"),
                    "expected_color": str(seq / f"{frame}.color.jpg"),
                    "expected_depth": str(seq / f"{frame}.depth.pgm"),
                    "expected_pose": str(seq / f"{frame}.pose.txt"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                }
            )
    return rows


def build_detector_input_rows(
    assignments: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    frames_by_episode: dict[str, list[int]] = defaultdict(list)
    routes_by_episode: dict[str, set[str]] = defaultdict(set)
    seq_by_episode: dict[str, str] = {}
    for row in render_rows:
        episode = str(row.get("adapter_episode_id"))
        frames_by_episode[episode].append(int(row.get("frame_index")))
        routes_by_episode[episode].add(str(row.get("route_id")))
        seq_by_episode[episode] = str(sequence_dir(str(row.get("scan_id"))))

    coverage_assignments = [row for row in assignments if row.get("branch_id") == "coverage_expansion_branch"]
    labels = {str(row.get("object_category")) for row in coverage_assignments if row.get("object_category")}
    prompt_set = {
        "version": VERSION,
        "prompt_set_id": "e008_m93_coverage_expansion_detector_prompts_v0",
        "prompt_policy": "M93 uses ObjectNav category text only; ObjectNav goal/viewpoint fields are blocked.",
        "label_count": len(labels),
        "detector_target_label_count": len(labels),
        "labels": prompt_rows_for_labels(labels, coverage_assignments),
    }
    proposal_schema = read_json(M84_DATA_DIR / "detector_inputs" / "proposal_output_schema.json")
    if proposal_schema:
        proposal_schema = dict(proposal_schema)
        proposal_schema["source_schema"] = proposal_schema.get("schema_id")
        proposal_schema["version"] = VERSION
        proposal_schema["schema_id"] = "real_proposal_prediction_jsonl_v0"

    object_targets: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for assignment in sorted(coverage_assignments, key=lambda row: str(row.get("adapter_episode_id"))):
        episode = str(assignment.get("adapter_episode_id"))
        label = str(assignment.get("object_category"))
        object_targets.append(
            {
                "version": VERSION,
                "source": "E008-M93 HM3D ObjectNav category only",
                "target_uid": f"e008-m93:{assignment.get('scan_id')}:{label}",
                "adapter_episode_id": episode,
                "detector_prompt_enabled": True,
                "evaluation_target_enabled": False,
                "hm3d_objectnav_category": label,
                "label_canonical": label,
                "label_text": label,
                "object_category": label,
                "policy_input_allowed": True,
                "prompt_set_id": prompt_set["prompt_set_id"],
                "scan_id": assignment.get("scan_id"),
                "scene_key": assignment.get("scene_key"),
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            }
        )
        sampled = sorted(set(frames_by_episode.get(episode, [])))
        manifests.append(
            {
                "version": VERSION,
                "row_type": "coverage_expansion_detector_manifest",
                "branch_id": "coverage_expansion_branch",
                "batch_id": "e008_m93_source_gap_two_branch_repair",
                "detector_config_id": "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0",
                "adapter_episode_id": episode,
                "scan_id": assignment.get("scan_id"),
                "scene_key": assignment.get("scene_key"),
                "object_category": label,
                "target_labels": [label],
                "target_label_count": 1,
                "detector_target_count": 1,
                "evaluation_target_count": 0,
                "prompt_set_id": prompt_set["prompt_set_id"],
                "prompt_set_path": str(DATA_OUT_DIR / "detector_inputs" / "prompt_set.json"),
                "object_target_path": str(DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl"),
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": str(DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json"),
                "sequence_dir_compat_path": seq_by_episode.get(episode),
                "frame_id_format": "frame-{index:06d}",
                "frame_sampling_strategy": "m93_coverage_expansion_dense_multiview",
                "sampled_frame_indices": sampled,
                "sampled_frame_count": len(sampled),
                "max_frames": len(sampled),
                "route_ids": sorted(routes_by_episode.get(episode, set())),
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "paper_table_role": "source_gap_repair_materialization_not_result",
            }
        )
    return manifests, object_targets, prompt_set, proposal_schema


def policy_feature_score(row: dict[str, Any], path_row: dict[str, Any] | None = None) -> float:
    confidence = finite_float(row.get("confidence")) or 0.0
    depth = finite_float(row.get("depth_valid_pixel_count")) or 0.0
    area = bbox_area(row)
    path_cost = finite_float(path_row.get("source_to_candidate_path_cost_m")) if path_row else None
    depth_term = min(1.0, math.log1p(depth) / math.log1p(300000.0))
    area_term = min(1.0, math.log1p(area) / math.log1p(640.0 * 480.0))
    path_term = 0.0 if path_cost is None else 1.0 / (1.0 + max(0.0, path_cost))
    return round((0.55 * confidence) + (0.20 * depth_term) + (0.10 * area_term) + (0.15 * path_term), 6)


def select_diverse(rows: list[dict[str, Any]], cap: int, key_name: str) -> list[dict[str, Any]]:
    by_frame_selected: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    for row in rows:
        fid = str(row.get(key_name) or frame_id(row))
        if by_frame_selected[fid] >= 3:
            continue
        selected.append(row)
        by_frame_selected[fid] += 1
        if len(selected) >= cap:
            break
    if len(selected) < cap:
        seen = {str(row.get("raw_candidate_uid")) for row in selected}
        for row in rows:
            if str(row.get("raw_candidate_uid")) in seen:
                continue
            selected.append(row)
            if len(selected) >= cap:
                break
    return selected


def build_cap_probe_rows(
    assignments: list[dict[str, Any]],
    pre_cap_rows: list[dict[str, Any]],
    navmesh_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    nav_by_raw = {str(row.get("raw_candidate_uid")): row for row in navmesh_rows}
    visit_by_raw = {str(row.get("raw_candidate_uid")): row for row in visit_rows}
    output: list[dict[str, Any]] = []
    for assignment in sorted(assignments, key=lambda row: str(row.get("adapter_episode_id"))):
        if assignment.get("branch_id") != "cap_threshold_rescue_branch":
            continue
        scan_id = str(assignment.get("scan_id"))
        label = str(assignment.get("object_category"))
        candidates = [
            row
            for row in pre_cap_rows
            if str(row.get("scan_id")) == scan_id and str(row.get("label_canonical")) == label
        ]
        for idx, row in enumerate(
            sorted(candidates, key=lambda item: (-(finite_float(item.get("confidence")) or 0.0), str(item.get("raw_candidate_uid")))),
            start=1,
        ):
            row["_pre_cap_confidence_rank"] = idx
            row["_frame_id"] = frame_id(row)
            row["_policy_feature_score"] = policy_feature_score(row, visit_by_raw.get(str(row.get("raw_candidate_uid"))))

        policies = [
            (
                "confidence_top24_baseline_cap_v0",
                sorted(
                    candidates,
                    key=lambda item: (
                        -(finite_float(item.get("confidence")) or 0.0),
                        str(item.get("raw_candidate_uid")),
                    ),
                )[:24],
                "baseline_preservation",
            ),
            (
                "confidence_depth_source_diverse_cap24_v0",
                select_diverse(
                    sorted(
                        candidates,
                        key=lambda item: (
                            -(item.get("_policy_feature_score") or 0.0),
                            str(item.get("_frame_id")),
                            str(item.get("raw_candidate_uid")),
                        ),
                    ),
                    24,
                    "_frame_id",
                ),
                "policy_visible_depth_source_path_probe",
            ),
            (
                "low_confidence_tail_depth_source_diverse_cap24_v0",
                select_diverse(
                    sorted(
                        [row for row in candidates if finite_int(row.get("_pre_cap_confidence_rank")) > 24],
                        key=lambda item: (
                            -(item.get("_policy_feature_score") or 0.0),
                            -((finite_float(item.get("depth_valid_pixel_count")) or 0.0)),
                            str(item.get("_frame_id")),
                            str(item.get("raw_candidate_uid")),
                        ),
                    ),
                    24,
                    "_frame_id",
                ),
                "cap_threshold_stress_probe",
            ),
        ]
        for policy_id, selected_rows, probe_role in policies:
            for rank, source in enumerate(selected_rows, start=1):
                raw_uid = str(source.get("raw_candidate_uid"))
                nav = nav_by_raw.get(raw_uid, {})
                visit = visit_by_raw.get(raw_uid, {})
                output.append(
                    {
                        "version": VERSION,
                        "row_type": "cap_threshold_candidate_probe",
                        "branch_id": "cap_threshold_rescue_branch",
                        "adapter_episode_id": assignment.get("adapter_episode_id"),
                        "scan_id": scan_id,
                        "scene_key": assignment.get("scene_key"),
                        "object_category": label,
                        "label_canonical": source.get("label_canonical"),
                        "label_text": source.get("label_text"),
                        "probe_policy_id": policy_id,
                        "probe_role": probe_role,
                        "candidate_budget": 24,
                        "probe_rank": rank,
                        "pre_cap_confidence_rank": source.get("_pre_cap_confidence_rank"),
                        "selection_score": source.get("_policy_feature_score")
                        if policy_id != "confidence_top24_baseline_cap_v0"
                        else source.get("confidence"),
                        "confidence": source.get("confidence"),
                        "depth_valid_pixel_count": source.get("depth_valid_pixel_count"),
                        "bbox_area_px": round(bbox_area(source), 3),
                        "frame_id": source.get("_frame_id"),
                        "frame_ids": source.get("frame_ids"),
                        "raw_frame_local_index": source.get("raw_frame_local_index"),
                        "raw_candidate_uid": raw_uid,
                        "pre_cap_candidate_pool_uid": source.get("pre_cap_candidate_pool_uid"),
                        "row_uid": source.get("row_uid"),
                        "centroid_world_m": source.get("centroid_world_m"),
                        "detector_id": source.get("detector_id"),
                        "detector_config_id": source.get("detector_config_id"),
                        "prompt_set_id": source.get("prompt_set_id"),
                        "navmesh_metadata_available": bool(nav),
                        "navmesh_validation_status": nav.get("navmesh_validation_status"),
                        "candidate_usable_for_path_smoke": nav.get("candidate_usable_for_path_smoke"),
                        "snap_distance_m": nav.get("snap_distance_m"),
                        "path_metadata_available": bool(visit),
                        "path_ready": visit.get("path_ready"),
                        "source_to_candidate_path_cost_m": visit.get("source_to_candidate_path_cost_m"),
                        "source_diversity_key": source.get("_frame_id"),
                        "rank_features": [
                            "confidence",
                            "depth_valid_pixel_count",
                            "bbox_area_px",
                            "frame/source diversity",
                            "source_to_candidate_path_cost_m_if_available",
                        ],
                        "rank_uses_eval_distance": False,
                        "policy_input_allowed": True,
                        "uses_objectnav_eval_goal": False,
                        "uses_objectnav_eval_viewpoint": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "claim_boundary": "Cap branch rows are diagnostic candidates; they cannot replace top-k policy until budget-loss evaluation passes.",
                    }
                )
    return output


def build_budget_loss_sentinel_rows(
    assignments: list[dict[str, Any]],
    cap_probe_rows: list[dict[str, Any]],
    m89_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_by_case_policy: dict[tuple[str, str], dict[str, Any]] = {}
    for row in m89_metric_rows:
        metric_by_case_policy[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))] = row
    cap_counts: Counter[tuple[str, str]] = Counter(
        (str(row.get("adapter_episode_id")), str(row.get("probe_policy_id"))) for row in cap_probe_rows
    )
    output: list[dict[str, Any]] = []
    for assignment in sorted(assignments, key=lambda row: str(row.get("adapter_episode_id"))):
        episode = str(assignment.get("adapter_episode_id"))
        output.append(
            {
                "version": VERSION,
                "row_type": "budget_loss_sentinel",
                "adapter_episode_id": episode,
                "scan_id": assignment.get("scan_id"),
                "scene_key": assignment.get("scene_key"),
                "object_category": assignment.get("object_category"),
                "branch_id": assignment.get("branch_id"),
                "sentinel_id": f"{episode}:preserve_detector_confidence_top24",
                "baseline_policy_id": "detector_confidence_all_candidates_v0",
                "protected_budget": 24,
                "baseline_candidate_rows": metric_by_case_policy.get((episode, "detector_confidence_all_candidates_v0"), {}).get("candidate_rows"),
                "baseline_path_ready_rows": metric_by_case_policy.get((episode, "detector_confidence_all_candidates_v0"), {}).get("path_ready_rows"),
                "replacement_allowed_now": False,
                "requires_goal_eval_before_replacement": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "M93 only materializes repair rows; loss-safe replacement requires M94+ post-policy evaluation.",
            }
        )
        if assignment.get("branch_id") == "cap_threshold_rescue_branch":
            for policy_id in sorted({policy for case, policy in cap_counts if case == episode}):
                output.append(
                    {
                        "version": VERSION,
                        "row_type": "budget_loss_sentinel",
                        "adapter_episode_id": episode,
                        "scan_id": assignment.get("scan_id"),
                        "scene_key": assignment.get("scene_key"),
                        "object_category": assignment.get("object_category"),
                        "branch_id": assignment.get("branch_id"),
                        "sentinel_id": f"{episode}:{policy_id}:loss_check",
                        "baseline_policy_id": "detector_confidence_all_candidates_v0",
                        "probe_policy_id": policy_id,
                        "probe_candidate_rows": cap_counts[(episode, policy_id)],
                        "protected_budget": 24,
                        "replacement_allowed_now": False,
                        "requires_goal_eval_before_replacement": True,
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "claim_boundary": "Probe rows may expose a suppressed candidate, but top-k replacement must show no unacceptable loss on existing successes.",
                    }
                )
    return output


def build_long_job_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in source_rows:
        new_row = dict(row)
        new_row["source_version"] = new_row.get("version")
        new_row["version"] = VERSION
        new_row["job_status"] = "deferred_after_m93_materialization"
        new_row["launch_now"] = False
        new_row["working_directory"] = str(ROOT)
        new_row["output_path"] = str(DATA_OUT_DIR if "render" in str(row.get("job_type")) else ARTIFACT_DIR)
        new_row["verification_command_template"] = (
            "python experiments/E008_real_navigation_benchmark/tools/run_m93_source_gap_two_branch_repair_row_materialization_smoke.py --verify-only"
        )
        new_row["exact_command"] = None
        new_row["reason_not_launched"] = "M93 is row materialization only; render/detector launch belongs to a later explicit route decision."
        output.append(new_row)
    return output[:2]


def audit_policy_rows(file_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocked_hits: list[dict[str, Any]] = []
    false_flag_violations: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        for key, value in row.items():
            key_lower = key.lower()
            if key in SAFE_FALSE_FLAG_KEYS:
                if value not in {False, None}:
                    false_flag_violations.append({"row_index": index, "key": key, "value": value})
                continue
            if any(part in key_lower for part in FORBIDDEN_POLICY_KEY_SUBSTRINGS):
                blocked_hits.append({"row_index": index, "key": key})
    passed = not blocked_hits and not false_flag_violations
    return {
        "version": VERSION,
        "row_type": "leakage_audit",
        "file": file_name,
        "rows": len(rows),
        "policy_leakage_audit_pass": passed,
        "blocked_key_hits": blocked_hits[:20],
        "false_flag_violations": false_flag_violations[:20],
        "allowed_false_flag_keys": sorted(SAFE_FALSE_FLAG_KEYS),
    }


def check_contracts(
    contract_rows: list[dict[str, Any]],
    outputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contract in contract_rows:
        contract_id = str(contract.get("contract_id"))
        if contract_id not in MATERIALIZED_CONTRACT_IDS:
            continue
        output_file = Path(str(contract.get("output_file")))
        name = output_file.name
        actual = len(outputs.get(name, []))
        expected_min = finite_int(contract.get("expected_rows_min"), 0)
        expected_max = finite_int(contract.get("expected_rows_max"), 10**9)
        rows.append(
            {
                "version": VERSION,
                "row_type": "materialization_contract_check",
                "contract_id": contract_id,
                "output_file": str(ARTIFACT_DIR / name),
                "expected_rows_min": expected_min,
                "expected_rows_max": expected_max,
                "actual_rows": actual,
                "contract_pass": expected_min <= actual <= expected_max,
                "required_invariant": contract.get("required_invariant"),
            }
        )
    return rows


def build_route_decision_rows(status: str, contract_checks: list[dict[str, Any]], leak_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready = status == READY_STATUS
    return [
        {
            "version": VERSION,
            "decision": "m93_materialization_ready_select_m94" if ready else "m93_materialization_blocked",
            "selected_next_unit": NEXT_UNIT if ready else None,
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "coverage_render_detector_ready_for_future_route": ready,
            "cap_threshold_probe_ready_for_future_eval": ready,
            "trajectory_promotion_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "reason": "M93 wrote leakage-safe two-branch repair rows; M94 should decide whether to evaluate cap probes first or launch coverage render/detector."
            if ready
            else "M93 materialization failed contract or leakage checks.",
            "failed_contract_checks": [row for row in contract_checks if not row.get("contract_pass")],
            "failed_leakage_audits": [row for row in leak_rows if not row.get("policy_leakage_audit_pass")],
        }
    ]


def write_report(coverage: dict[str, Any]) -> None:
    status = coverage.get("status")
    lines = [
        "# E008-M93 Source-Gap Two-Branch Repair Row Materialization Smoke",
        "",
        "## Result",
        "",
        f"- status: `{status}`",
        f"- coverage observation rows: {coverage.get('coverage_expansion_observation_plan_rows')}",
        f"- coverage render rows: {coverage.get('coverage_expansion_render_plan_rows')}",
        f"- coverage detector manifest rows: {coverage.get('coverage_expansion_detector_manifest_rows')}",
        f"- cap threshold candidate probe rows: {coverage.get('cap_threshold_candidate_probe_rows')}",
        f"- budget loss sentinel rows: {coverage.get('budget_loss_sentinel_rows')}",
        f"- long job command rows: {coverage.get('long_job_command_rows')}",
        "",
        "## Claim Boundary",
        "",
        "- M93 is a materialization smoke, not a recovery result.",
        "- Coverage branch rows are launch-ready inputs for a later render/detector gate.",
        "- Cap branch rows are diagnostic probe rows and cannot replace confidence top-k until loss-safe evaluation passes.",
        "- Real navigation `SR` / `SPL` and final real RGB-D/open-vocabulary robustness remain unsupported at M93.",
        "",
        "## Next",
        "",
        f"- selected next unit: `{coverage.get('selected_next_unit')}`",
    ]
    write_text(ARTIFACT_DIR / "report.md", "\n".join(lines) + "\n")


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_OUT_DIR / "detector_inputs").mkdir(parents=True, exist_ok=True)

    m92_coverage = read_json(M92_DIR / "coverage.json")
    assignment_source_rows = read_jsonl(M92_DIR / "case_repair_assignment_rows.jsonl")
    branch_source_rows = read_jsonl(M92_DIR / "repair_branch_contract_rows.jsonl")
    materialization_contract_rows = read_jsonl(M92_DIR / "materialization_contract_rows.jsonl")
    long_job_source_rows = read_jsonl(M92_DIR / "long_job_policy_rows.jsonl")
    m84_observation_rows = read_jsonl(M84_DIR / "source_gap_observation_pose_plan_rows.jsonl")
    pre_cap_rows = read_jsonl(M86_DIR / "container_output" / "pre_cap_candidate_pool.jsonl")
    navmesh_rows = read_jsonl(M87_DIR / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(M88_DIR / "candidate_visit_order_rows.jsonl")
    m89_metric_rows = read_jsonl(M89_DIR / "source_gap_case_goal_metric_rows.jsonl")

    assignments = copy_with_version(assignment_source_rows, "case_repair_assignment")
    branch_rows = copy_with_version(branch_source_rows, "repair_branch_contract")
    coverage_observation_rows = build_coverage_observation_rows(assignments, m84_observation_rows)
    coverage_render_rows = build_coverage_render_rows(coverage_observation_rows)
    manifest_rows, object_target_rows, prompt_set, proposal_schema = build_detector_input_rows(
        assignments,
        coverage_render_rows,
    )
    cap_probe_rows = build_cap_probe_rows(assignments, pre_cap_rows, navmesh_rows, visit_rows)
    budget_sentinel_rows = build_budget_loss_sentinel_rows(assignments, cap_probe_rows, m89_metric_rows)
    long_job_rows = build_long_job_rows(long_job_source_rows)

    outputs = {
        "case_repair_assignment_rows.jsonl": assignments,
        "repair_branch_contract_rows.jsonl": branch_rows,
        "coverage_expansion_observation_plan_rows.jsonl": coverage_observation_rows,
        "coverage_expansion_render_plan_rows.jsonl": coverage_render_rows,
        "coverage_expansion_detector_manifest_rows.jsonl": manifest_rows,
        "coverage_expansion_object_target_rows.jsonl": object_target_rows,
        "cap_threshold_candidate_probe_rows.jsonl": cap_probe_rows,
        "budget_loss_sentinel_rows.jsonl": budget_sentinel_rows,
        "long_job_command_rows.jsonl": long_job_rows,
    }

    output_paths: list[Path] = []
    for name, rows in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, rows)
        output_paths.append(path)

    write_json(DATA_OUT_DIR / "detector_inputs" / "prompt_set.json", prompt_set)
    write_jsonl(DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl", object_target_rows)
    write_json(DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json", proposal_schema)
    write_json(ARTIFACT_DIR / "coverage_expansion_prompt_set.json", prompt_set)
    write_json(ARTIFACT_DIR / "coverage_expansion_proposal_output_schema.json", proposal_schema)

    contract_checks = check_contracts(materialization_contract_rows, outputs)
    leakage_rows = [
        audit_policy_rows("coverage_expansion_observation_plan_rows.jsonl", coverage_observation_rows),
        audit_policy_rows("coverage_expansion_render_plan_rows.jsonl", coverage_render_rows),
        audit_policy_rows("coverage_expansion_detector_manifest_rows.jsonl", manifest_rows),
        audit_policy_rows("cap_threshold_candidate_probe_rows.jsonl", cap_probe_rows),
    ]
    readiness_rows = [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m92_contract_ready",
            "gate_pass": m92_coverage.get("status") == "e008_m92_source_gap_two_branch_coverage_cap_repair_contract_ready",
            "observed": m92_coverage.get("status"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "coverage_branch_rows_present",
            "gate_pass": len(coverage_observation_rows) >= 12 and len(manifest_rows) >= 1,
            "observed": {"observation_rows": len(coverage_observation_rows), "manifest_rows": len(manifest_rows)},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "cap_probe_rows_present",
            "gate_pass": len(cap_probe_rows) >= 24,
            "observed": len(cap_probe_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "contract_checks_pass",
            "gate_pass": all(row.get("contract_pass") for row in contract_checks),
            "observed": Counter(str(row.get("contract_pass")) for row in contract_checks),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "policy_leakage_audits_pass",
            "gate_pass": all(row.get("policy_leakage_audit_pass") for row in leakage_rows),
            "observed": Counter(str(row.get("policy_leakage_audit_pass")) for row in leakage_rows),
        },
    ]
    status = READY_STATUS if all(row.get("gate_pass") for row in readiness_rows) else BLOCKED_STATUS

    claim_boundary_rows = [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "source_gap_repair_materialization",
            "support_status": "supported" if status == READY_STATUS else "blocked",
            "allowed_claim": "M93 materializes leakage-safe two-branch repair rows from M92.",
            "blocked_claims": [
                "coverage branch recovers target candidates",
                "cap branch improves source-gap success",
                "real navigation SR/SPL improves",
                "final real RGB-D/open-vocabulary robustness is solved",
            ],
        }
    ]
    route_rows = build_route_decision_rows(status, contract_checks, leakage_rows)

    extra_outputs = {
        "materialization_contract_check_rows.jsonl": contract_checks,
        "leakage_audit_rows.jsonl": leakage_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "claim_boundary_rows.jsonl": claim_boundary_rows,
        "route_decision_rows.jsonl": route_rows,
    }
    for name, rows in extra_outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, rows)
        output_paths.append(path)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m92_status": m92_coverage.get("status"),
        "case_repair_assignment_rows": len(assignments),
        "repair_branch_contract_rows": len(branch_rows),
        "coverage_expansion_observation_plan_rows": len(coverage_observation_rows),
        "coverage_expansion_render_plan_rows": len(coverage_render_rows),
        "coverage_expansion_detector_manifest_rows": len(manifest_rows),
        "cap_threshold_candidate_probe_rows": len(cap_probe_rows),
        "budget_loss_sentinel_rows": len(budget_sentinel_rows),
        "long_job_command_rows": len(long_job_rows),
        "contract_check_rows": len(contract_checks),
        "failed_contract_check_rows": sum(1 for row in contract_checks if not row.get("contract_pass")),
        "leakage_audit_rows": len(leakage_rows),
        "failed_leakage_audit_rows": sum(1 for row in leakage_rows if not row.get("policy_leakage_audit_pass")),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if not row.get("gate_pass")),
        "launch_long_job_now": False,
        "coverage_branch_render_detector_input_ready": status == READY_STATUS,
        "cap_branch_probe_eval_input_ready": status == READY_STATUS,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else None,
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    output_paths.append(ARTIFACT_DIR / "coverage.json")
    write_report(coverage)
    output_paths.append(ARTIFACT_DIR / "report.md")
    mirror_outputs(output_paths)

    if status != READY_STATUS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
