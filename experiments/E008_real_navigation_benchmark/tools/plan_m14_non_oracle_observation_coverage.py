#!/usr/bin/env python3
"""Plan non-oracle observation coverage expansion after E008-M13."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M14_non_oracle_observation_coverage_plan_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M14_non_oracle_observation_coverage_plan_v0"
VERSION = "e008_m14_non_oracle_observation_coverage_plan_v0"

M07_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
M13_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M13_detector_goal_failure_audit_v0"

M15_DATASET_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
YAW_OFFSETS_DEG = [0, 90, 180, 270]
LOCAL_SHELL_RADII_M = [1.5, 3.0]
LOCAL_SHELL_BEARINGS_DEG = [0, 90, 180, 270]

CATEGORY_DETECTOR_LABELS = {
    "bed": ["bed"],
    "chair": ["chair"],
    "tv_monitor": ["tv", "television", "monitor"],
}

ALLOWED_INPUTS = [
    "scene_file",
    "navmesh_file",
    "episode_start_position",
    "episode_start_rotation",
    "object_category",
    "current_detector_candidate_rows",
    "reachable_navmesh_samples",
    "fixed_render_budget",
]

BLOCKED_INPUTS = [
    "eval_goal_position",
    "eval_viewpoints",
    "closest_goal_object_id",
    "success_label",
    "candidate_to_goal_distance",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def detector_labels_for_category(category: str) -> list[str]:
    return CATEGORY_DETECTOR_LABELS.get(category, [category.replace("_", " ")])


def yaw_from_xyzw(rotation: object) -> float:
    if not isinstance(rotation, list) or len(rotation) != 4:
        return 0.0
    x, y, z, w = [finite_float(value) or 0.0 for value in rotation]
    # Y-up yaw estimate for Habitat agent rotations.
    return math.atan2(2.0 * (w * y + x * z), 1.0 - 2.0 * (y * y + z * z))


def planned_position(source_position: list[float], source_rotation: list[float], radius_m: float, bearing_deg: int) -> list[float]:
    yaw = yaw_from_xyzw(source_rotation)
    theta = yaw + math.radians(float(bearing_deg))
    dx = radius_m * math.sin(theta)
    dz = radius_m * math.cos(theta)
    return [float(source_position[0] + dx), float(source_position[1]), float(source_position[2] + dz)]


def scan_episode_index(render_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in sorted(render_rows, key=lambda item: (str(item.get("scan_id")), int(item.get("frame_index") or 0))):
        scan_id = str(row.get("scan_id"))
        if scan_id in out:
            continue
        out[scan_id] = {
            "adapter_episode_id": row.get("adapter_episode_id"),
            "scan_id": scan_id,
            "scene_key": row.get("scene_key"),
            "object_category": row.get("object_category"),
            "hm3d_scene_docker_path": row.get("hm3d_scene_docker_path"),
            "hm3d_navmesh_docker_path": row.get("hm3d_navmesh_docker_path"),
            "source_position": row.get("source_position"),
            "source_rotation": row.get("source_rotation"),
        }
    return out


def build_observation_pose_rows(episode_index: dict[str, dict[str, Any]], m13_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failure_index = {str(row.get("scan_id")): row for row in m13_rows}
    rows: list[dict[str, Any]] = []
    for scan_id, episode in sorted(episode_index.items()):
        source_position = episode.get("source_position")
        source_rotation = episode.get("source_rotation")
        if not isinstance(source_position, list) or len(source_position) != 3:
            raise SystemExit(f"missing source_position for {scan_id}")
        if not isinstance(source_rotation, list) or len(source_rotation) != 4:
            raise SystemExit(f"missing source_rotation for {scan_id}")
        source_position_f = [float(value) for value in source_position]
        source_rotation_f = [float(value) for value in source_rotation]
        failure = failure_index.get(scan_id, {})

        pose_rows = [
            {
                "pose_role": "start_pose",
                "pose_family": "existing_start_pose",
                "shell_radius_m": 0.0,
                "bearing_relative_deg": 0,
                "planned_position_m": source_position_f,
                "planned_rotation_xyzw": source_rotation_f,
                "requires_navmesh_snap_validation": False,
            }
        ]
        for radius_m in LOCAL_SHELL_RADII_M:
            for bearing_deg in LOCAL_SHELL_BEARINGS_DEG:
                pose_rows.append(
                    {
                        "pose_role": "local_shell_pose",
                        "pose_family": f"start_neighborhood_radius_{str(radius_m).replace('.', 'p')}m",
                        "shell_radius_m": radius_m,
                        "bearing_relative_deg": bearing_deg,
                        "planned_position_m": planned_position(source_position_f, source_rotation_f, radius_m, bearing_deg),
                        "planned_rotation_xyzw": source_rotation_f,
                        "requires_navmesh_snap_validation": True,
                    }
                )

        for pose_index, pose in enumerate(pose_rows):
            rows.append(
                {
                    "version": VERSION,
                    "route_id": "bounded_start_neighborhood_multiview_v0",
                    "scan_id": scan_id,
                    "adapter_episode_id": episode.get("adapter_episode_id"),
                    "scene_key": episode.get("scene_key"),
                    "object_category": episode.get("object_category"),
                    "observation_pose_id": f"{scan_id}:obs-{pose_index:03d}",
                    "observation_pose_index": pose_index,
                    "planning_scope": "all_episode_uniform_policy",
                    "m13_primary_failure_class": failure.get("primary_failure_class"),
                    "m13_recommended_next_action": failure.get("recommended_next_action"),
                    "hm3d_scene_docker_path": episode.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": episode.get("hm3d_navmesh_docker_path"),
                    "source_position_m": source_position_f,
                    "source_rotation_xyzw": source_rotation_f,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "policy_input_allowed": True,
                    "position_status": "planned_unvalidated_until_m15",
                    **pose,
                }
            )
    return rows


def build_render_plan_rows(observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frame_counts: Counter[str] = Counter()
    for pose in observation_rows:
        scan_id = str(pose["scan_id"])
        for yaw_offset in YAW_OFFSETS_DEG:
            frame_index = frame_counts[scan_id]
            frame_counts[scan_id] += 1
            frame_id = f"frame-{frame_index:06d}"
            sequence_dir = M15_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence"
            rows.append(
                {
                    "version": VERSION,
                    "route_id": "bounded_start_neighborhood_multiview_v0",
                    "render_source": "non_oracle_start_neighborhood_multiview",
                    "scan_id": scan_id,
                    "adapter_episode_id": pose.get("adapter_episode_id"),
                    "scene_key": pose.get("scene_key"),
                    "object_category": pose.get("object_category"),
                    "observation_pose_id": pose.get("observation_pose_id"),
                    "observation_pose_index": pose.get("observation_pose_index"),
                    "pose_role": pose.get("pose_role"),
                    "shell_radius_m": pose.get("shell_radius_m"),
                    "bearing_relative_deg": pose.get("bearing_relative_deg"),
                    "frame_id": frame_id,
                    "frame_index": frame_index,
                    "yaw_offset_deg": yaw_offset,
                    "render_width": FRAME_WIDTH,
                    "render_height": FRAME_HEIGHT,
                    "hm3d_scene_docker_path": pose.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": pose.get("hm3d_navmesh_docker_path"),
                    "source_position": pose.get("planned_position_m"),
                    "source_rotation": pose.get("planned_rotation_xyzw"),
                    "requires_navmesh_snap_validation": pose.get("requires_navmesh_snap_validation"),
                    "position_status": pose.get("position_status"),
                    "expected_color": str(sequence_dir / f"{frame_id}.color.jpg"),
                    "expected_depth": str(sequence_dir / f"{frame_id}.depth.pgm"),
                    "expected_pose": str(sequence_dir / f"{frame_id}.pose.txt"),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "policy_input_allowed": True,
                }
            )
    return rows


def build_manifest_rows(episode_index: dict[str, dict[str, Any]], render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_count_by_scan = Counter(str(row["scan_id"]) for row in render_rows)
    rows = []
    for scan_id, episode in sorted(episode_index.items()):
        labels = detector_labels_for_category(str(episode.get("object_category")))
        rows.append(
            {
                "version": VERSION,
                "route_id": "bounded_start_neighborhood_multiview_v0",
                "batch_id": "e008_m14_non_oracle_observation_expansion_plan",
                "scan_id": scan_id,
                "adapter_episode_id": episode.get("adapter_episode_id"),
                "scene_key": episode.get("scene_key"),
                "object_category": episode.get("object_category"),
                "sequence_dir_compat_path": str(M15_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence"),
                "sampled_frame_count": frame_count_by_scan[scan_id],
                "target_labels": labels,
                "target_label_count": len(labels),
                "prompt_set_id": "e008_m14_hm3d_objectnav_detector_prompts_v0",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "frame_sampling_strategy": "uniform_start_neighborhood_multiview",
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "paper_table_role": "candidate_source_expansion_plan_not_final_result",
            }
        )
    return rows


def build_prompt_set(episode_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels: dict[str, dict[str, Any]] = {}
    for episode in episode_index.values():
        scan_id = str(episode["scan_id"])
        category = str(episode["object_category"])
        for label in detector_labels_for_category(category):
            item = labels.setdefault(
                label,
                {
                    "label_canonical": label,
                    "prompts": set(),
                    "hm3d_objectnav_categories": set(),
                    "scan_ids": set(),
                    "detector_prompt_enabled": True,
                },
            )
            item["prompts"].update({label, f"a {label}", f"the {label}"})
            item["hm3d_objectnav_categories"].add(category)
            item["scan_ids"].add(scan_id)
    out_labels = []
    for label, item in sorted(labels.items()):
        out_labels.append(
            {
                "label_canonical": label,
                "prompts": sorted(item["prompts"]),
                "hm3d_objectnav_categories": sorted(item["hm3d_objectnav_categories"]),
                "scan_ids": sorted(item["scan_ids"]),
                "scan_count": len(item["scan_ids"]),
                "detector_prompt_enabled": item["detector_prompt_enabled"],
                "prompt_role": "detector_target",
                "aliases": [],
            }
        )
    return {
        "version": VERSION,
        "prompt_set_id": "e008_m14_hm3d_objectnav_detector_prompts_v0",
        "prompt_policy": "ObjectNav category is mapped to detector labels without exposing ObjectNav goal/viewpoint fields.",
        "label_count": len(out_labels),
        "detector_target_label_count": len(out_labels),
        "labels": out_labels,
    }


def build_object_target_rows(episode_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for scan_id, episode in sorted(episode_index.items()):
        for label in detector_labels_for_category(str(episode.get("object_category"))):
            rows.append(
                {
                    "version": VERSION,
                    "route_id": "bounded_start_neighborhood_multiview_v0",
                    "scan_id": scan_id,
                    "adapter_episode_id": episode.get("adapter_episode_id"),
                    "scene_key": episode.get("scene_key"),
                    "object_category": episode.get("object_category"),
                    "label_canonical": label,
                    "label_text": label,
                    "prompt_set_id": "e008_m14_hm3d_objectnav_detector_prompts_v0",
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                }
            )
    return rows


def build_policy_rows(m13_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "bounded_start_neighborhood_multiview_v0",
            "decision": "selected",
            "planning_scope": "all_episode_uniform_policy",
            "reason": "M13 shows shared all-policy failures and pre-cap target-region misses, so target coverage should be expanded before reranking or simulator execution.",
            "m13_failed_all_policies_episode_rows": m13_coverage.get("failed_all_policies_episode_rows"),
            "m13_precap_target_region_missing_episode_rows": m13_coverage.get("precap_target_region_missing_episode_rows"),
            "uses_eval_failure_labels_to_select_episode_subset": False,
        },
        {
            "version": VERSION,
            "route_id": "visit_order_reranking_only_v0",
            "decision": "rejected_now",
            "reason": "M13 post-cap/snap suppression count is 0 and failures are shared across all policies.",
            "uses_eval_failure_labels_to_select_episode_subset": False,
        },
        {
            "version": VERSION,
            "route_id": "failed_episode_only_expansion_v0",
            "decision": "rejected_for_metric",
            "reason": "Expanding only failed episodes would use eval-only failure labels to change policy input.",
            "uses_eval_failure_labels_to_select_episode_subset": True,
        },
        {
            "version": VERSION,
            "route_id": "oracle_goal_viewpoint_render_v0",
            "decision": "blocked",
            "reason": "ObjectNav goal positions and viewpoints are eval-only labels.",
            "uses_eval_failure_labels_to_select_episode_subset": True,
        },
        {
            "version": VERSION,
            "route_id": "trajectory_execution_now_v0",
            "decision": "deferred",
            "reason": "Target coverage is not stable enough for a real SR/SPL execution table.",
            "uses_eval_failure_labels_to_select_episode_subset": False,
        },
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    rows = []
    for field in ALLOWED_INPUTS:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "input_status": "allowed",
                "usage": "coverage_planning_or_future_m15_validation",
                "policy_input_allowed": True,
            }
        )
    for field in BLOCKED_INPUTS:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "input_status": "blocked",
                "usage": "eval_only_or_forbidden_for_policy",
                "policy_input_allowed": False,
            }
        )
    return rows


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "next_unit": "E008-M15 non-oracle observation expansion frame staging smoke",
            "expected_command": "python experiments/E008_real_navigation_benchmark/tools/run_m15_non_oracle_observation_expansion_frame_staging.py",
            "verification_command": "python experiments/E008_real_navigation_benchmark/tools/verify_m15_non_oracle_observation_expansion_frame_staging.py",
            "expected_input": str(ARTIFACT_DIR / "expanded_render_plan_rows.jsonl"),
            "expected_output_root": str(M15_DATASET_ROOT),
            "launch_long_job_now": False,
            "reason": "M14 fixes the plan only; M15 should render/snap/verify expanded observations without ObjectNav goal/viewpoint leakage.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
) -> str:
    selected = next(row for row in policy_rows if row["decision"] == "selected")
    pose_counts = Counter(str(row["pose_role"]) for row in observation_rows)
    return f"""# E008-M14 Non-Oracle Observation Coverage Plan

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M13 status: `{coverage['m13_status']}`.
- Episode rows: {coverage['episode_rows']}.
- Observation pose rows: {coverage['observation_pose_rows']}.
- Expanded render rows: {coverage['expanded_render_plan_rows']}.
- Frames per episode: {coverage['frames_per_episode']}.
- Pose counts: `start_pose` {pose_counts.get('start_pose', 0)}, `local_shell_pose` {pose_counts.get('local_shell_pose', 0)}.
- Selected route: `{selected['route_id']}`.
- Selected next unit: `{coverage['selected_next_unit']}`.
- Long job launched: {coverage['launch_long_job_now']}.

## Claim Boundary

- This artifact is a plan, not a rendered-frame result.
- It does not claim real navigation `SR` / `SPL`.
- It does not claim final real RGB-D/open-vocabulary robustness.
- It blocks `ObjectNav` goal positions, viewpoints, success labels, and candidate-to-goal distances as policy inputs.

## Agent Inference

M13 makes reranking a weak next move because the failures are shared across policies and mostly missing from the pre-cap candidate pool. The next defensible route is a uniform, non-oracle observation expansion over all six episodes, followed by M15 frame staging and leakage checks.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m13_coverage = read_json(M13_ARTIFACT_DIR / "coverage.json")
    m13_rows = read_jsonl(M13_ARTIFACT_DIR / "episode_failure_audit_rows.jsonl")
    render_rows_m07 = read_jsonl(M07_ARTIFACT_DIR / "render_plan_rows.jsonl")
    if not m13_rows:
        raise SystemExit("missing M13 episode_failure_audit_rows.jsonl")
    if not render_rows_m07:
        raise SystemExit("missing M07 render_plan_rows.jsonl")

    episode_index = scan_episode_index(render_rows_m07)
    observation_rows = build_observation_pose_rows(episode_index, m13_rows)
    expanded_render_rows = build_render_plan_rows(observation_rows)
    manifest_rows = build_manifest_rows(episode_index, expanded_render_rows)
    prompt_set = build_prompt_set(episode_index)
    object_target_rows = build_object_target_rows(episode_index)
    policy_rows = build_policy_rows(m13_coverage)
    input_contract_rows = build_input_contract_rows()
    next_action_rows = build_next_action_rows()

    frames_by_scan = Counter(str(row["scan_id"]) for row in expanded_render_rows)
    coverage = {
        "version": VERSION,
        "status": "e008_m14_non_oracle_observation_coverage_plan_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m13_status": m13_coverage.get("status"),
        "episode_rows": len(episode_index),
        "m13_failed_all_policies_episode_rows": m13_coverage.get("failed_all_policies_episode_rows"),
        "m13_precap_target_region_missing_episode_rows": m13_coverage.get("precap_target_region_missing_episode_rows"),
        "m13_near_miss_localization_episode_rows": m13_coverage.get("near_miss_localization_episode_rows"),
        "m13_post_cap_or_snap_suppression_episode_rows": m13_coverage.get("post_cap_or_snap_suppression_episode_rows"),
        "observation_pose_rows": len(observation_rows),
        "expanded_render_plan_rows": len(expanded_render_rows),
        "frames_per_episode": sorted(set(frames_by_scan.values())),
        "local_shell_radii_m": LOCAL_SHELL_RADII_M,
        "local_shell_bearings_deg": LOCAL_SHELL_BEARINGS_DEG,
        "yaw_offsets_deg": YAW_OFFSETS_DEG,
        "detector_manifest_rows": len(manifest_rows),
        "object_target_rows": len(object_target_rows),
        "prompt_label_count": prompt_set["label_count"],
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_eval_failure_labels_to_select_episode_subset": False,
        "requires_m15_navmesh_snap_validation": True,
        "requires_m15_frame_staging": True,
        "requires_detector_rerun_after_m15": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M15 non-oracle observation expansion frame staging smoke",
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_json(output_dir / "expanded_prompt_set.json", prompt_set)
        write_jsonl(output_dir / "observation_pose_plan_rows.jsonl", observation_rows)
        write_jsonl(output_dir / "expanded_render_plan_rows.jsonl", expanded_render_rows)
        write_jsonl(output_dir / "expanded_detector_manifest_rows.jsonl", manifest_rows)
        write_jsonl(output_dir / "expanded_real_proposal_object_targets.jsonl", object_target_rows)
        write_jsonl(output_dir / "coverage_route_policy_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "next_action_rows.jsonl", next_action_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_rows, observation_rows, expanded_render_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
