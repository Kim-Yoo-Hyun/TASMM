#!/usr/bin/env python3
"""Materialize the E008-M64 full-val-mini high-path scale denominator."""

from __future__ import annotations

import gzip
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M61_DIR = EXP_ROOT / "artifacts" / "E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0"
M63_DIR = EXP_ROOT / "artifacts" / "E008-M63_high_path_tail_slot_scaleup_contract_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
)

VERSION = "e008_m64_full_val_mini_high_path_scale_materialization_v0"
READY_STATUS = "e008_m64_full_val_mini_high_path_scale_materialization_ready"
BLOCKED_STATUS = "e008_m64_full_val_mini_high_path_scale_materialization_blocked"
NEXT_UNIT = "E008-M65 full-val-mini render frame staging and detector candidate-source contract"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
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
DOCKER_DATA_ROOT = Path("/data")

TASK_CONTEXTS = ["high_value_fetch", "noisy_high_value_fetch", "routine_fetch"]
YAW_OFFSETS_DEG = [0, 90, 180, 270]
LOCAL_SHELL_RADII_M = [1.5, 3.0]
LOCAL_SHELL_BEARINGS_DEG = [0, 90, 180, 270]
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

CORE_POLICIES = [
    "static_stale_memory_top1_v0",
    "detector_confidence_budget5_v0",
    "fixed_topk_current_observation_budget5_v0",
    "source_diverse_current_observation_budget5_v1",
    "h001_task_conditioned_source_diverse_budget5_v1",
    "h001_task_conditioned_safe_source_diverse_budget5_v2",
    "task_agnostic_source_diverse_budget5_v1",
    "h001_task_conditioned_high_path_tail_slot_budget5_v3",
]

CATEGORY_DETECTOR_LABELS = {
    "bed": ["bed"],
    "chair": ["chair"],
    "plant": ["plant"],
    "sofa": ["sofa"],
    "toilet": ["toilet"],
    "tv_monitor": ["tv", "television", "monitor"],
}

BLOCKED_POLICY_FIELDS = {
    "closest_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "diagnostic_primary_eval_hit",
    "diagnostic_hit_any_viewpoint_xz_1p0",
    "eval_success",
    "trajectory_success",
    "success_proposal_uid",
    "success_source_role",
    "success_dynamic_stale_overlay_role",
    "FailureType",
    "SR",
    "SPL",
    "StopRank",
    "PathLengthM",
    "diagnostic_source_gap_boundary",
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


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "NA" if value is None else str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def scene_key_from_scene_id(scene_id: str) -> str:
    parts = scene_id.split("/")
    if len(parts) >= 3:
        return parts[-2]
    return "unknown_scene"


def scan_id_from_episode(scene_key: str, episode_id: str) -> str:
    return f"hm3dnav_{scene_key.replace('-', '_')}_ep{episode_id}"


def scene_paths(scene_id: str) -> tuple[Path, Path]:
    rel = scene_id.replace("hm3d_v0.2/", "")
    scene_path = RESEARCH3_DATA_ROOT / "versioned_data" / "hm3d-0.2" / "hm3d" / rel
    navmesh_path = scene_path.with_suffix(".basis.navmesh")
    if not navmesh_path.exists() and scene_path.name.endswith(".basis.glb"):
        navmesh_path = scene_path.with_name(scene_path.name.replace(".basis.glb", ".basis.navmesh"))
    return scene_path, navmesh_path


def docker_scene_path(scene_path: Path) -> str:
    rel = scene_path.relative_to(RESEARCH3_DATA_ROOT)
    return str(DOCKER_DATA_ROOT / rel)


def yaw_from_xyzw(rotation: object) -> float:
    if not isinstance(rotation, list) or len(rotation) != 4:
        return 0.0
    x, y, z, w = [finite_float(value) or 0.0 for value in rotation]
    return math.atan2(2.0 * (w * y + x * z), 1.0 - 2.0 * (y * y + z * z))


def planned_position(source_position: list[float], source_rotation: list[float], radius_m: float, bearing_deg: int) -> list[float]:
    yaw = yaw_from_xyzw(source_rotation)
    theta = yaw + math.radians(float(bearing_deg))
    dx = radius_m * math.sin(theta)
    dz = radius_m * math.cos(theta)
    return [float(source_position[0] + dx), float(source_position[1]), float(source_position[2] + dz)]


def load_val_mini_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for content_file in sorted(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        for episode in payload.get("episodes", []):
            scene_id = str(episode.get("scene_id", ""))
            scene_key = scene_key_from_scene_id(scene_id)
            source_episode_id = str(episode.get("episode_id"))
            adapter_episode_id = f"{scene_key}::{source_episode_id}"
            scene_path, navmesh_path = scene_paths(scene_id)
            start_position = [float(v) for v in episode.get("start_position", [])]
            start_rotation = [float(v) for v in episode.get("start_rotation", [])]
            rows.append(
                {
                    "version": VERSION,
                    "dataset": "HM3D ObjectNav v2",
                    "split": "val_mini",
                    "content_file": content_file.name,
                    "source_episode_id": source_episode_id,
                    "adapter_episode_id": adapter_episode_id,
                    "scan_id": scan_id_from_episode(scene_key, source_episode_id),
                    "scene_id_raw": scene_id,
                    "scene_key": scene_key,
                    "object_category": episode.get("object_category"),
                    "start_position": start_position,
                    "start_rotation": start_rotation,
                    "scene_ready": scene_path.exists(),
                    "navmesh_ready": navmesh_path.exists(),
                    "resolved_scene_path": str(scene_path),
                    "resolved_navmesh_path": str(navmesh_path),
                    "scene_docker_path": docker_scene_path(scene_path),
                    "navmesh_docker_path": docker_scene_path(navmesh_path),
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "policy_input_allowed": True,
                }
            )
    return sorted(rows, key=lambda row: (str(row["scene_key"]), int(row["source_episode_id"])))


def m61_seen_episode_ids() -> set[str]:
    rows = read_jsonl(M61_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    return {
        str(row.get("adapter_episode_id"))
        for row in rows
        if row.get("metric_scope") == "scan_task_policy" and row.get("adapter_episode_id")
    }


def build_episode_task_rows(episode_rows: list[dict[str, Any]], seen_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_categories = {
        str(row["object_category"])
        for row in episode_rows
        if str(row["adapter_episode_id"]) in seen_ids
    }
    for episode in episode_rows:
        split_id = (
            "seen_m61_reference"
            if str(episode["adapter_episode_id"]) in seen_ids
            else "val_mini_unseen_episode_holdout"
        )
        for task_context in TASK_CONTEXTS:
            rows.append(
                {
                    **episode,
                    "task_context_id": task_context,
                    "scan_task_context_uid": f"m64::{episode['adapter_episode_id']}::{task_context}",
                    "selected_denominator_id": "val_mini_full_episode_scale",
                    "split_id": split_id,
                    "split_role": "diagnostic_reference_not_train"
                    if split_id == "seen_m61_reference"
                    else "first_scale_eval",
                    "category_seen_in_m61": str(episode["object_category"]) in seen_categories,
                    "uses_task_context_for_decision": task_context != "routine_fetch",
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "claim_boundary": "M64 materializes scale denominator rows only; no detector candidates or trajectories are executed.",
                }
            )
    return rows


def build_observation_pose_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        source_position = [float(value) for value in episode["start_position"]]
        source_rotation = [float(value) for value in episode["start_rotation"]]
        pose_specs = [
            {
                "pose_role": "start_pose",
                "pose_family": "existing_start_pose",
                "shell_radius_m": 0.0,
                "bearing_relative_deg": 0,
                "planned_position_m": source_position,
                "planned_rotation_xyzw": source_rotation,
                "requires_navmesh_snap_validation": False,
            }
        ]
        for radius_m in LOCAL_SHELL_RADII_M:
            for bearing_deg in LOCAL_SHELL_BEARINGS_DEG:
                pose_specs.append(
                    {
                        "pose_role": "local_shell_pose",
                        "pose_family": f"start_neighborhood_radius_{str(radius_m).replace('.', 'p')}m",
                        "shell_radius_m": radius_m,
                        "bearing_relative_deg": bearing_deg,
                        "planned_position_m": planned_position(source_position, source_rotation, radius_m, bearing_deg),
                        "planned_rotation_xyzw": source_rotation,
                        "requires_navmesh_snap_validation": True,
                    }
                )
        for pose_index, pose in enumerate(pose_specs):
            rows.append(
                {
                    "version": VERSION,
                    "route_id": "bounded_start_neighborhood_multiview_v0",
                    "adapter_episode_id": episode["adapter_episode_id"],
                    "scan_id": episode["scan_id"],
                    "scene_key": episode["scene_key"],
                    "object_category": episode["object_category"],
                    "observation_pose_id": f"{episode['scan_id']}:obs-{pose_index:03d}",
                    "observation_pose_index": pose_index,
                    "source_position_m": source_position,
                    "source_rotation_xyzw": source_rotation,
                    "hm3d_scene_docker_path": episode["scene_docker_path"],
                    "hm3d_navmesh_docker_path": episode["navmesh_docker_path"],
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "policy_input_allowed": True,
                    "position_status": "planned_unvalidated_until_m65",
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
            sequence_dir = DATA_OUT_DIR / "render_inputs" / "3RScan" / "scans" / scan_id / "sequence"
            rows.append(
                {
                    "version": VERSION,
                    "route_id": "bounded_start_neighborhood_multiview_v0",
                    "render_source": "full_val_mini_non_oracle_start_neighborhood_multiview",
                    "adapter_episode_id": pose["adapter_episode_id"],
                    "scan_id": scan_id,
                    "scene_key": pose["scene_key"],
                    "object_category": pose["object_category"],
                    "observation_pose_id": pose["observation_pose_id"],
                    "observation_pose_index": pose["observation_pose_index"],
                    "pose_role": pose["pose_role"],
                    "shell_radius_m": pose["shell_radius_m"],
                    "bearing_relative_deg": pose["bearing_relative_deg"],
                    "frame_id": frame_id,
                    "frame_index": frame_index,
                    "yaw_offset_deg": yaw_offset,
                    "render_width": FRAME_WIDTH,
                    "render_height": FRAME_HEIGHT,
                    "hm3d_scene_docker_path": pose["hm3d_scene_docker_path"],
                    "hm3d_navmesh_docker_path": pose["hm3d_navmesh_docker_path"],
                    "source_position": pose["planned_position_m"],
                    "source_rotation": pose["planned_rotation_xyzw"],
                    "requires_navmesh_snap_validation": pose["requires_navmesh_snap_validation"],
                    "position_status": pose["position_status"],
                    "expected_color": str(sequence_dir / f"{frame_id}.color.jpg"),
                    "expected_depth": str(sequence_dir / f"{frame_id}.depth.pgm"),
                    "expected_pose": str(sequence_dir / f"{frame_id}.pose.txt"),
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "policy_input_allowed": True,
                }
            )
    return rows


def detector_labels_for_category(category: str) -> list[str]:
    return CATEGORY_DETECTOR_LABELS.get(category, [category.replace("_", " ")])


def build_detector_manifest_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        labels = detector_labels_for_category(str(episode["object_category"]))
        sequence_dir = DATA_OUT_DIR / "render_inputs" / "3RScan" / "scans" / str(episode["scan_id"]) / "sequence"
        rows.append(
            {
                "version": VERSION,
                "batch_id": "e008_m64_full_val_mini_candidate_source_plan",
                "route_id": "bounded_start_neighborhood_multiview_v0",
                "adapter_episode_id": episode["adapter_episode_id"],
                "scan_id": episode["scan_id"],
                "scene_key": episode["scene_key"],
                "object_category": episode["object_category"],
                "frame_sampling_strategy": "uniform_start_neighborhood_multiview",
                "sampled_frame_count": 36,
                "target_label_count": len(labels),
                "target_labels": labels,
                "prompt_set_id": "e008_m64_hm3d_val_mini_detector_prompts_v0",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "sequence_dir_compat_path": str(sequence_dir),
                "paper_table_role": "candidate_source_scale_plan_not_final_result",
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "policy_input_allowed": True,
            }
        )
    return rows


def build_prompt_set(episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_to_categories: dict[str, set[str]] = defaultdict(set)
    label_to_scans: dict[str, set[str]] = defaultdict(set)
    for episode in episode_rows:
        category = str(episode["object_category"])
        for label in detector_labels_for_category(category):
            label_to_categories[label].add(category)
            label_to_scans[label].add(str(episode["scan_id"]))
    labels = []
    for label in sorted(label_to_scans):
        labels.append(
            {
                "label_canonical": label,
                "prompt_role": "detector_target",
                "detector_prompt_enabled": True,
                "hm3d_objectnav_categories": sorted(label_to_categories[label]),
                "prompts": sorted({label, f"a {label}", f"the {label}"}),
                "scan_count": len(label_to_scans[label]),
                "scan_ids": sorted(label_to_scans[label]),
                "aliases": [],
            }
        )
    return {
        "version": VERSION,
        "prompt_set_id": "e008_m64_hm3d_val_mini_detector_prompts_v0",
        "prompt_policy": "ObjectNav category is mapped to detector labels without exposing ObjectNav goal/viewpoint fields.",
        "detector_target_label_count": len(labels),
        "label_count": len(labels),
        "labels": labels,
    }


def policy_role(policy_id: str) -> str:
    if policy_id == "h001_task_conditioned_high_path_tail_slot_budget5_v3":
        return "method_candidate"
    if policy_id == "h001_task_conditioned_safe_source_diverse_budget5_v2":
        return "base_h001_ablation"
    if policy_id == "h001_task_conditioned_source_diverse_budget5_v1":
        return "earlier_h001_ablation"
    if policy_id == "task_agnostic_source_diverse_budget5_v1":
        return "task_context_ablation"
    if policy_id in {"detector_confidence_budget5_v0", "fixed_topk_current_observation_budget5_v0"}:
        return "current_observation_baseline"
    if policy_id == "source_diverse_current_observation_budget5_v1":
        return "source_diversity_baseline"
    if policy_id == "static_stale_memory_top1_v0":
        return "static_memory_lower_bound"
    return "supporting_baseline"


def candidate_budget(policy_id: str) -> int:
    return 1 if policy_id == "static_stale_memory_top1_v0" else 5


def build_policy_plan_rows(episode_task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_row in episode_task_rows:
        for policy_id in CORE_POLICIES:
            rows.append(
                {
                    "version": VERSION,
                    "selected_denominator_id": "val_mini_full_episode_scale",
                    "policy_plan_uid": f"m64::{task_row['adapter_episode_id']}::{task_row['task_context_id']}::{policy_id}",
                    "scan_task_context_uid": task_row["scan_task_context_uid"],
                    "adapter_episode_id": task_row["adapter_episode_id"],
                    "scan_id": task_row["scan_id"],
                    "scene_key": task_row["scene_key"],
                    "object_category": task_row["object_category"],
                    "task_context_id": task_row["task_context_id"],
                    "split_id": task_row["split_id"],
                    "policy_id": policy_id,
                    "policy_role": policy_role(policy_id),
                    "candidate_budget": candidate_budget(policy_id),
                    "source_boundary_reporting_required": True,
                    "candidate_source_status": "requires_m65_render_detector_candidate_source",
                    "candidate_rows_materialized_now": 0,
                    "execute_in_next_runner": False,
                    "requires_docker_for_trajectory": True,
                    "uses_task_context_for_decision": "task_conditioned" in policy_id or policy_id.startswith("h001_"),
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "policy_input_uses_success_label": False,
                    "policy_input_allowed": True,
                    "claim_boundary": "M64 materializes full-val-mini policy plan rows only; candidates and trajectory metrics are future units.",
                }
            )
    return rows


def build_source_boundary_contract_rows(episode_rows: list[dict[str, Any]], seen_ids: set[str]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "boundary_id": "source_ready",
            "expected_scope": "episodes_with_current_detector_or_memory_source_after_M65",
            "reporting_required": True,
            "policy_trigger_allowed": False,
            "claim_boundary": "source_ready is a reporting scope unless a policy-visible source feature exists before metric computation.",
        },
        {
            "version": VERSION,
            "boundary_id": "source_gap",
            "expected_scope": "episodes_without top-budget current source after M65 candidate materialization",
            "reporting_required": True,
            "policy_trigger_allowed": False,
            "claim_boundary": "source_gap is diagnostic/reporting-only and cannot be used as a policy trigger.",
        },
        {
            "version": VERSION,
            "boundary_id": "seen_m61_reference",
            "episode_rows": sum(1 for row in episode_rows if str(row["adapter_episode_id"]) in seen_ids),
            "reporting_required": True,
            "policy_trigger_allowed": False,
            "claim_boundary": "seen reference rows preserve M61 comparison only; they are not a training split.",
        },
        {
            "version": VERSION,
            "boundary_id": "val_mini_unseen_episode_holdout",
            "episode_rows": sum(1 for row in episode_rows if str(row["adapter_episode_id"]) not in seen_ids),
            "reporting_required": True,
            "policy_trigger_allowed": False,
            "claim_boundary": "holdout rows support bounded scale evaluation after execution, not final scene transfer.",
        },
    ]


def build_readiness_rows(
    m63_coverage: dict[str, Any],
    episode_rows: list[dict[str, Any]],
    episode_task_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    leakage_pass = all(row["blocked_field_hits"] == 0 for row in leakage_rows)

    def gate(gate_id: str, passed: bool, rationale: str, blocks_m65: bool = False, blocks_final: bool = True) -> dict[str, Any]:
        return {
            "version": VERSION,
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "rationale": rationale,
            "blocks_m64": not passed and gate_id
            in {
                "m63_contract_ready",
                "episode_count_matches_contract",
                "episode_task_context_rows_match_contract",
                "render_plan_rows_match_contract",
                "detector_manifest_rows_match_episodes",
                "core_policy_plan_rows_match_contract",
                "leakage_audit_pass",
                "scene_navmesh_ready",
            },
            "blocks_m65": blocks_m65 and not passed,
            "blocks_final_navigation_claim": blocks_final and not passed,
        }

    return [
        gate(
            "m63_contract_ready",
            m63_coverage.get("status") == "e008_m63_high_path_tail_slot_scaleup_contract_ready",
            "M63 scale-up contract is ready.",
        ),
        gate("episode_count_matches_contract", len(episode_rows) == 30, "val_mini episode denominator has 30 rows."),
        gate(
            "episode_task_context_rows_match_contract",
            len(episode_task_rows) == 90,
            "30 episodes x 3 task contexts are materialized.",
        ),
        gate(
            "render_plan_rows_match_contract",
            len(render_rows) == 1080,
            "30 episodes x 36 planned frames are materialized.",
        ),
        gate(
            "detector_manifest_rows_match_episodes",
            len(manifest_rows) == 30,
            "One detector manifest row per val_mini episode is materialized.",
        ),
        gate(
            "core_policy_plan_rows_match_contract",
            len(policy_rows) == 720,
            "90 scan-task contexts x 8 core policies are materialized.",
        ),
        gate("leakage_audit_pass", leakage_pass, "Blocked policy fields are absent from policy-facing rows."),
        gate(
            "scene_navmesh_ready",
            all(row["scene_ready"] and row["navmesh_ready"] for row in episode_rows),
            "All selected val_mini episodes have scene and navmesh paths.",
        ),
        gate(
            "candidate_source_rows_ready",
            False,
            "M64 does not render frames, run detector inference, or navmesh-validate candidates.",
            blocks_m65=True,
        ),
        gate(
            "full_val_mini_trajectory_execution_ready",
            False,
            "M64 is denominator/materialization only; Docker trajectory execution remains future.",
            blocks_m65=True,
        ),
    ]


def audit_blocked_fields(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    hits = Counter()
    for row in rows:
        for field in BLOCKED_POLICY_FIELDS:
            if field in row and row.get(field) not in (None, "", [], {}):
                hits[field] += 1
    return {
        "version": VERSION,
        "row_group": name,
        "row_count": len(rows),
        "blocked_field_hits": sum(hits.values()),
        "blocked_field_hit_counts": dict(sorted(hits.items())),
        "leakage_audit_pass": sum(hits.values()) == 0,
    }


def build_m65_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "step_id": "m65_render_frame_staging_or_launch_contract",
            "expected_rows": 1080,
            "requires_docker": True,
            "long_job": True,
            "launch_in_m64": False,
            "output": "rendered RGB-D frame rows and snap validation rows",
        },
        {
            "version": VERSION,
            "step_id": "m66_detector_candidate_source_run",
            "expected_manifest_rows": 30,
            "requires_docker": True,
            "long_job": True,
            "launch_in_m64": False,
            "output": "real RGB-D/open-vocabulary candidate rows",
        },
        {
            "version": VERSION,
            "step_id": "m67_navmesh_validation_and_candidate_policy_rows",
            "expected_policy_plan_rows": 720,
            "requires_docker": True,
            "long_job": False,
            "launch_in_m64": False,
            "output": "path-ready candidate visit rows for M64 policies",
        },
        {
            "version": VERSION,
            "step_id": "m68_or_later_trajectory_execution",
            "expected_scan_task_policy_rows": 720,
            "requires_docker": True,
            "long_job": True,
            "launch_in_m64": False,
            "output": "Habitat trajectory rows and SR/SPL metrics",
        },
    ]


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "m65_render_candidate_source_contract_next",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else None,
            "launch_long_job_now": False,
            "rationale": "M64 creates a full-val-mini denominator and policy plan; M65 must fix the Docker render/detector execution contract before launching long jobs.",
        },
        {
            "version": VERSION,
            "route_id": "launch_full_val_mini_docker_now",
            "selected": False,
            "selected_next_unit": None,
            "launch_long_job_now": False,
            "rationale": "M64 has no rendered frames or candidate rows yet, so direct trajectory execution would be premature.",
        },
        {
            "version": VERSION,
            "route_id": "jump_to_val_full_scene_transfer",
            "selected": False,
            "selected_next_unit": None,
            "launch_long_job_now": False,
            "rationale": "Scene transfer should wait until val_mini candidate-source and trajectory materialization pass.",
        },
    ]


def write_report(
    coverage: dict[str, Any],
    episode_summary_rows: list[dict[str, Any]],
    policy_summary_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M64 Full-Val-Mini High-Path Scale Materialization",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Episode rows: {coverage['episode_rows']}.",
        f"- Episode-task-context rows: {coverage['episode_task_context_rows']}.",
        f"- Planned render frames: {coverage['render_plan_rows']}.",
        f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
        f"- Core policy execution plan rows: {coverage['policy_execution_plan_rows']}.",
        f"- Seen M61 reference episodes: {coverage['seen_m61_reference_episode_rows']}.",
        f"- Val-mini unseen holdout episodes: {coverage['holdout_episode_rows']}.",
        f"- Candidate rows materialized now: {coverage['candidate_rows_materialized_now']}.",
        f"- Long job launched: {coverage['long_job_launched']}.",
        f"- Final real navigation `SR` / `SPL` ready: {coverage['final_real_navigation_sr_spl_ready']}.",
        "",
        "## Episode Summary",
        "",
        markdown_table(
            episode_summary_rows,
            ["split_id", "episode_rows", "scan_task_context_rows", "scene_count", "category_count", "categories"],
        ),
        "",
        "## Policy Summary",
        "",
        markdown_table(
            policy_summary_rows,
            ["policy_id", "policy_role", "policy_plan_rows", "candidate_budget", "candidate_source_status"],
        ),
        "",
        "## Readiness Gates",
        "",
        markdown_table(readiness_rows, ["gate_id", "gate_status", "blocks_m64", "blocks_m65", "blocks_final_navigation_claim"]),
        "",
        "## Route Decision",
        "",
        markdown_table(route_rows, ["route_id", "selected", "selected_next_unit", "launch_long_job_now"]),
        "",
        "## Claim Boundary",
        "",
        "- M64 materializes the full `val_mini` denominator and policy plan only.",
        "- M64 does not render frames, run open-vocabulary detector inference, validate candidates, or execute `Habitat` trajectories.",
        "- Final real navigation `SR` / `SPL`, deployable search policy, final RGB-D/open-vocabulary robustness, and human-intent main claims remain false.",
        "",
    ]
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def summarize_episodes(episode_task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in episode_task_rows:
        grouped[str(row["split_id"])].append(row)
    out = []
    for split_id, rows in sorted(grouped.items()):
        episode_ids = {str(row["adapter_episode_id"]) for row in rows}
        scenes = sorted({str(row["scene_key"]) for row in rows})
        categories = sorted({str(row["object_category"]) for row in rows})
        out.append(
            {
                "version": VERSION,
                "split_id": split_id,
                "episode_rows": len(episode_ids),
                "scan_task_context_rows": len(rows),
                "scene_count": len(scenes),
                "category_count": len(categories),
                "categories": categories,
            }
        )
    return out


def summarize_policies(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows:
        grouped[str(row["policy_id"])].append(row)
    out = []
    for policy_id in CORE_POLICIES:
        rows = grouped[policy_id]
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "policy_plan_rows": len(rows),
                "candidate_budget": candidate_budget(policy_id),
                "candidate_source_status": "requires_m65_render_detector_candidate_source",
            }
        )
    return out


def copy_outputs_to_data_dir(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src in paths:
        rel = src.relative_to(ARTIFACT_DIR)
        dst = DATA_OUT_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().replace(microsecond=0).isoformat()
    m63_coverage = read_json(M63_DIR / "coverage.json")
    seen_ids = m61_seen_episode_ids()
    episode_rows = load_val_mini_rows()
    episode_task_rows = build_episode_task_rows(episode_rows, seen_ids)
    observation_rows = build_observation_pose_rows(episode_rows)
    render_rows = build_render_plan_rows(observation_rows)
    manifest_rows = build_detector_manifest_rows(episode_rows)
    prompt_set = build_prompt_set(episode_rows)
    policy_rows = build_policy_plan_rows(episode_task_rows)
    source_boundary_rows = build_source_boundary_contract_rows(episode_rows, seen_ids)
    m65_plan_rows = build_m65_plan_rows()
    leakage_rows = [
        audit_blocked_fields("episode_task_context_rows", episode_task_rows),
        audit_blocked_fields("observation_pose_rows", observation_rows),
        audit_blocked_fields("render_plan_rows", render_rows),
        audit_blocked_fields("detector_manifest_rows", manifest_rows),
        audit_blocked_fields("core_policy_execution_plan_rows", policy_rows),
    ]
    readiness_rows = build_readiness_rows(
        m63_coverage,
        episode_rows,
        episode_task_rows,
        render_rows,
        manifest_rows,
        policy_rows,
        leakage_rows,
    )
    m64_blocked = any(row["blocks_m64"] for row in readiness_rows)
    status = BLOCKED_STATUS if m64_blocked else READY_STATUS
    route_rows = build_route_rows(status == READY_STATUS)
    episode_summary_rows = summarize_episodes(episode_task_rows)
    policy_summary_rows = summarize_policies(policy_rows)

    holdout_ids = {str(row["adapter_episode_id"]) for row in episode_rows if str(row["adapter_episode_id"]) not in seen_ids}
    coverage = {
        "version": VERSION,
        "generated_at": generated_at,
        "status": status,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else "repair E008-M64 materialization blockers",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m63_status": m63_coverage.get("status"),
        "selected_denominator_id": "val_mini_full_episode_scale",
        "episode_rows": len(episode_rows),
        "episode_task_context_rows": len(episode_task_rows),
        "observation_pose_rows": len(observation_rows),
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(manifest_rows),
        "prompt_label_count": len(prompt_set["labels"]),
        "policy_execution_plan_rows": len(policy_rows),
        "source_boundary_contract_rows": len(source_boundary_rows),
        "m65_plan_rows": len(m65_plan_rows),
        "leakage_audit_rows": len(leakage_rows),
        "readiness_gate_pass_rows": sum(1 for row in readiness_rows if row["gate_status"] == "pass"),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if row["gate_status"] == "fail"),
        "seen_m61_reference_episode_rows": len(seen_ids),
        "holdout_episode_rows": len(holdout_ids),
        "scene_count": len({str(row["scene_key"]) for row in episode_rows}),
        "category_count": len({str(row["object_category"]) for row in episode_rows}),
        "categories": sorted({str(row["object_category"]) for row in episode_rows}),
        "candidate_rows_materialized_now": 0,
        "long_job_launched": False,
        "render_frames_ready": False,
        "detector_candidate_rows_ready": False,
        "trajectory_execution_ready": False,
        "full_val_mini_materialization_ready": status == READY_STATUS,
        "final_real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    output_files = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "val_mini_episode_rows.jsonl",
        ARTIFACT_DIR / "episode_task_context_rows.jsonl",
        ARTIFACT_DIR / "observation_pose_plan_rows.jsonl",
        ARTIFACT_DIR / "render_plan_rows.jsonl",
        ARTIFACT_DIR / "detector_manifest_rows.jsonl",
        ARTIFACT_DIR / "prompt_set.json",
        ARTIFACT_DIR / "core_policy_execution_plan_rows.jsonl",
        ARTIFACT_DIR / "source_boundary_contract_rows.jsonl",
        ARTIFACT_DIR / "episode_summary_rows.jsonl",
        ARTIFACT_DIR / "policy_summary_rows.jsonl",
        ARTIFACT_DIR / "leakage_audit_rows.jsonl",
        ARTIFACT_DIR / "readiness_gate_rows.jsonl",
        ARTIFACT_DIR / "m65_plan_rows.jsonl",
        ARTIFACT_DIR / "route_decision_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]
    write_json(output_files[0], coverage)
    write_jsonl(output_files[1], episode_rows)
    write_jsonl(output_files[2], episode_task_rows)
    write_jsonl(output_files[3], observation_rows)
    write_jsonl(output_files[4], render_rows)
    write_jsonl(output_files[5], manifest_rows)
    write_json(output_files[6], prompt_set)
    write_jsonl(output_files[7], policy_rows)
    write_jsonl(output_files[8], source_boundary_rows)
    write_jsonl(output_files[9], episode_summary_rows)
    write_jsonl(output_files[10], policy_summary_rows)
    write_jsonl(output_files[11], leakage_rows)
    write_jsonl(output_files[12], readiness_rows)
    write_jsonl(output_files[13], m65_plan_rows)
    write_jsonl(output_files[14], route_rows)
    write_report(coverage, episode_summary_rows, policy_summary_rows, readiness_rows, route_rows)

    # Keep detector/renderer-compatible copies under the derived data root.
    render_inputs = DATA_OUT_DIR / "render_inputs"
    detector_inputs = DATA_OUT_DIR / "detector_inputs"
    render_inputs.mkdir(parents=True, exist_ok=True)
    detector_inputs.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ARTIFACT_DIR / "render_plan_rows.jsonl", render_inputs / "render_plan_rows.jsonl")
    shutil.copyfile(ARTIFACT_DIR / "detector_manifest_rows.jsonl", detector_inputs / "real_proposal_query_manifest.jsonl")
    shutil.copyfile(ARTIFACT_DIR / "prompt_set.json", detector_inputs / "prompt_set.json")
    copy_outputs_to_data_dir(
        [
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "val_mini_episode_rows.jsonl",
            ARTIFACT_DIR / "episode_task_context_rows.jsonl",
            ARTIFACT_DIR / "core_policy_execution_plan_rows.jsonl",
            ARTIFACT_DIR / "source_boundary_contract_rows.jsonl",
            ARTIFACT_DIR / "readiness_gate_rows.jsonl",
            ARTIFACT_DIR / "m65_plan_rows.jsonl",
            ARTIFACT_DIR / "route_decision_rows.jsonl",
            ARTIFACT_DIR / "report.md",
        ]
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
