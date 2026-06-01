#!/usr/bin/env python3
"""Materialize M84 source-gap non-oracle source/observation expansion inputs."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import shlex
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
M15_RENDER_TOOL = EXP_ROOT / "tools" / "run_m15_non_oracle_observation_expansion_frame_staging.py"
M16_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
M66_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m66_full_val_mini_render_frame_staging.py"
M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M65_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
M80_DIR = EXP_ROOT / "artifacts" / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
M83_DIR = EXP_ROOT / "artifacts" / "E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M86_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"

VERSION = "e008_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
READY_STATUS = "e008_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_blocked"
NEXT_UNIT = "E008-M85 full-val-mini source-gap non-oracle render frame staging background launch"
DETECTOR_NEXT_UNIT = "E008-M86 full-val-mini source-gap detector candidate-source background launch"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
REAL_SMOKE_IMAGE = "research2/real-smoke:latest"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
LOG_DIR = ROOT / "logs"
RENDER_TMUX_SESSION = "e008_m85_source_gap_render"
DETECTOR_TMUX_SESSION = "e008_m86_source_gap_detector"
YAW_OFFSETS = [0, 45, 90, 135, 180, 225, 270, 315]


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


def command_status(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stderr": str(exc),
            "stdout": "",
        }
    return {
        "available": result.returncode == 0,
        "command": command,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "stdout": result.stdout.strip(),
    }


def docker_status() -> dict[str, Any]:
    direct = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    sudo = command_status(["sudo", "-n", "docker", "info", "--format", "{{.ServerVersion}}"])
    if direct["available"]:
        return {"available": True, "mode": "direct", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo}
    if sudo["available"]:
        return {"available": True, "mode": "sudo_n", "selected_prefix": ["sudo", "-n", "docker"], "direct": direct, "sudo_n": sudo}
    return {"available": False, "mode": "unavailable", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo}


def image_status(prefix: list[str], image: str) -> dict[str, Any]:
    return command_status([*prefix, "image", "inspect", image, "--format", "{{.Id}}"])


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in command)


def host_path_from_docker_path(docker_path: str) -> Path:
    value = Path(docker_path)
    if not str(value).startswith("/data/"):
        return value
    return RESEARCH3_DATA_ROOT / value.relative_to("/data")


def m15_render_script_for_m84() -> str:
    spec = importlib.util.spec_from_file_location("e008_m15_render_tool", M15_RENDER_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 render tool: {M15_RENDER_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DATA_OUT_DIR = DATA_OUT_DIR
    module.SCENE_DATASET_CONFIG = SCENE_DATASET_CONFIG
    return module.render_script()


def sequence_dir(scan_id: str) -> Path:
    return DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"


def group_by_episode(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("adapter_episode_id"))].append(row)
    return grouped


def observation_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("observation_pose_id")): row for row in rows if row.get("observation_pose_id")}


def candidate_sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
    append_first = 0 if str(row.get("candidate_order_component", "")).startswith("m80_append") else 1
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m"))
    confidence = finite_float(row.get("confidence")) or 0.0
    return (
        append_first,
        -(path_cost if path_cost is not None else -1.0),
        -confidence,
        str(row.get("proposal_uid")),
    )


def target_labels_for_case(case: dict[str, Any]) -> list[str]:
    labels = [str(label) for label in case.get("target_labels", []) if str(label)]
    return labels or [str(case.get("object_category"))]


def build_case_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "source_gap_case",
            "adapter_episode_id": row.get("adapter_episode_id"),
            "scan_id": row.get("scan_id"),
            "scene_key": row.get("scene_key"),
            "object_category": row.get("object_category"),
            "target_labels": target_labels_for_case(row),
            "source_gap_resolved_before_m84": bool(row.get("source_gap_resolved_before_m83")),
            "contract_selection_uses_posthoc_eval": bool(row.get("contract_selection_uses_posthoc_eval")),
            "final_policy_may_use_source_gap_label": False,
            "claim_boundary": "M84 materializes source-gap diagnostic cases only; final runtime policy cannot use this case label.",
        }
        for row in case_rows
    ]


def build_observation_pose_rows(
    case_rows: list[dict[str, Any]],
    source_observation_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    obs_by_episode = group_by_episode(source_observation_rows)
    cand_by_episode = group_by_episode(candidate_rows)
    obs_index = observation_by_id(source_observation_rows)
    output: list[dict[str, Any]] = []

    for case in sorted(case_rows, key=lambda row: str(row.get("adapter_episode_id"))):
        episode = str(case.get("adapter_episode_id"))
        base_rows = sorted(
            obs_by_episode.get(episode, []),
            key=lambda row: finite_int(row.get("observation_pose_index")),
        )
        local_rows = base_rows
        high_path_candidates = []
        seen_source_keys: set[tuple[float, float, float]] = set()
        for cand in sorted(cand_by_episode.get(episode, []), key=candidate_sort_key):
            if str(cand.get("policy_id")) != "loss_safe_append_source_probe_budget8_v0":
                continue
            if not bool(cand.get("path_ready")):
                continue
            source_position = cand.get("source_position_m")
            if not isinstance(source_position, list) or len(source_position) != 3:
                continue
            key = tuple(round(float(value), 3) for value in source_position)
            if key in seen_source_keys:
                continue
            seen_source_keys.add(key)
            high_path_candidates.append(cand)
            if len(high_path_candidates) >= 3:
                break

        for idx, obs in enumerate(local_rows):
            output.append(
                {
                    "version": VERSION,
                    "row_type": "source_gap_observation_pose_plan",
                    "route_id": "non_oracle_local_shell_multiview_refresh_v1",
                    "adapter_episode_id": episode,
                    "scan_id": obs.get("scan_id"),
                    "scene_key": obs.get("scene_key"),
                    "object_category": obs.get("object_category"),
                    "observation_pose_id": f"{episode}:m84-local-{idx:03d}",
                    "source_observation_pose_id": obs.get("observation_pose_id"),
                    "observation_pose_index": idx,
                    "pose_family": "m84_local_shell_refresh",
                    "pose_role": obs.get("pose_role"),
                    "planned_position_m": obs.get("planned_position_m"),
                    "planned_rotation_xyzw": obs.get("planned_rotation_xyzw"),
                    "source_position_m": obs.get("source_position_m"),
                    "source_rotation_xyzw": obs.get("source_rotation_xyzw"),
                    "shell_radius_m": obs.get("shell_radius_m"),
                    "requires_navmesh_snap_validation": bool(obs.get("requires_navmesh_snap_validation")),
                    "hm3d_scene_docker_path": obs.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": obs.get("hm3d_navmesh_docker_path"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "claim_boundary": "Local-shell refresh reuses policy-visible non-oracle observation poses.",
                }
            )

        for idx, cand in enumerate(high_path_candidates):
            source_obs = obs_index.get(str(cand.get("observation_pose_id")), {})
            source_position = cand.get("source_position_m") or source_obs.get("planned_position_m")
            rotation = source_obs.get("planned_rotation_xyzw") or source_obs.get("source_rotation_xyzw")
            output.append(
                {
                    "version": VERSION,
                    "row_type": "source_gap_observation_pose_plan",
                    "route_id": "non_oracle_high_path_source_refresh_v1",
                    "adapter_episode_id": episode,
                    "scan_id": cand.get("scan_id") or case.get("scan_id"),
                    "scene_key": cand.get("scene_key") or case.get("scene_key"),
                    "object_category": cand.get("object_category") or case.get("object_category"),
                    "observation_pose_id": f"{episode}:m84-highpath-{idx:03d}",
                    "source_observation_pose_id": cand.get("observation_pose_id"),
                    "source_candidate_visit_uid": cand.get("candidate_visit_uid"),
                    "source_proposal_uid": cand.get("proposal_uid"),
                    "observation_pose_index": len(local_rows) + idx,
                    "pose_family": "m84_high_path_source_refresh",
                    "pose_role": "high_path_source_pose",
                    "planned_position_m": source_position,
                    "planned_rotation_xyzw": rotation,
                    "source_position_m": source_position,
                    "source_rotation_xyzw": rotation,
                    "candidate_confidence": cand.get("confidence"),
                    "candidate_visit_rank": cand.get("visit_rank"),
                    "candidate_source_to_path_cost_m": cand.get("source_to_candidate_path_cost_m"),
                    "shell_radius_m": cand.get("shell_radius_m"),
                    "requires_navmesh_snap_validation": True,
                    "hm3d_scene_docker_path": cand.get("scene_docker_path") or source_obs.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": cand.get("navmesh_docker_path") or source_obs.get("hm3d_navmesh_docker_path"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "claim_boundary": "High-path refresh uses policy-visible candidate/source metadata only, not eval goal or success labels.",
                }
            )
    return output


def build_render_rows(observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_counts: dict[str, int] = defaultdict(int)
    rows: list[dict[str, Any]] = []
    for obs in sorted(
        observation_rows,
        key=lambda row: (str(row.get("adapter_episode_id")), finite_int(row.get("observation_pose_index")), str(row.get("route_id"))),
    ):
        scan_id = str(obs.get("scan_id"))
        for yaw in YAW_OFFSETS:
            frame_index = frame_counts[scan_id]
            frame_counts[scan_id] += 1
            frame_id = f"frame-{frame_index:06d}"
            seq = sequence_dir(scan_id)
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "source_gap_render_plan",
                    "source_observation_pose_id": obs.get("observation_pose_id"),
                    "route_id": obs.get("route_id"),
                    "adapter_episode_id": obs.get("adapter_episode_id"),
                    "scan_id": scan_id,
                    "scene_key": obs.get("scene_key"),
                    "object_category": obs.get("object_category"),
                    "observation_pose_id": obs.get("observation_pose_id"),
                    "observation_pose_index": obs.get("observation_pose_index"),
                    "pose_role": obs.get("pose_role"),
                    "pose_family": obs.get("pose_family"),
                    "frame_index": frame_index,
                    "frame_id": frame_id,
                    "yaw_offset_deg": yaw,
                    "bearing_relative_deg": 0,
                    "render_width": 640,
                    "render_height": 480,
                    "render_source": "source_gap_non_oracle_source_observation_expansion_m84",
                    "source_position": obs.get("planned_position_m"),
                    "source_rotation": obs.get("planned_rotation_xyzw"),
                    "shell_radius_m": obs.get("shell_radius_m"),
                    "requires_navmesh_snap_validation": bool(obs.get("requires_navmesh_snap_validation")),
                    "hm3d_scene_docker_path": obs.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": obs.get("hm3d_navmesh_docker_path"),
                    "expected_color": str(seq / f"{frame_id}.color.jpg"),
                    "expected_depth": str(seq / f"{frame_id}.depth.pgm"),
                    "expected_pose": str(seq / f"{frame_id}.pose.txt"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                }
            )
    return rows


def build_detector_manifest_rows(case_rows: list[dict[str, Any]], render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_indices_by_episode: dict[str, list[int]] = defaultdict(list)
    sequence_dir_by_episode: dict[str, str] = {}
    route_ids_by_episode: dict[str, set[str]] = defaultdict(set)
    for row in render_rows:
        episode = str(row.get("adapter_episode_id"))
        frame_indices_by_episode[episode].append(int(row.get("frame_index")))
        sequence_dir_by_episode[episode] = str(sequence_dir(str(row.get("scan_id"))))
        route_ids_by_episode[episode].add(str(row.get("route_id")))

    rows: list[dict[str, Any]] = []
    for case in sorted(case_rows, key=lambda row: str(row.get("adapter_episode_id"))):
        episode = str(case.get("adapter_episode_id"))
        labels = target_labels_for_case(case)
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_gap_detector_manifest",
                "batch_id": "e008_m84_source_gap_non_oracle_source_observation_expansion",
                "detector_config_id": "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0",
                "adapter_episode_id": episode,
                "scan_id": case.get("scan_id"),
                "scene_key": case.get("scene_key"),
                "object_category": case.get("object_category"),
                "target_labels": labels,
                "target_label_count": len(labels),
                "detector_target_count": len(labels),
                "evaluation_target_count": 0,
                "prompt_set_id": "e008_m84_source_gap_detector_prompts_v0",
                "prompt_set_path": str(DATA_OUT_DIR / "detector_inputs" / "prompt_set.json"),
                "object_target_path": str(DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl"),
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": str(DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json"),
                "sequence_dir_compat_path": sequence_dir_by_episode.get(episode),
                "frame_id_format": "frame-{index:06d}",
                "frame_sampling_strategy": "m84_source_gap_non_oracle_dense_multiview",
                "sampled_frame_indices": sorted(set(frame_indices_by_episode.get(episode, []))),
                "sampled_frame_count": len(set(frame_indices_by_episode.get(episode, []))),
                "max_frames": len(set(frame_indices_by_episode.get(episode, []))),
                "route_ids": sorted(route_ids_by_episode.get(episode, set())),
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "paper_table_role": "source_gap_expansion_materialization_not_result",
            }
        )
    return rows


def build_object_target_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        for label in manifest.get("target_labels", []):
            rows.append(
                {
                    "version": VERSION,
                    "source": "E008-M84 HM3D ObjectNav category only",
                    "target_uid": f"e008-m84:{manifest['scan_id']}:{label}",
                    "adapter_episode_id": manifest.get("adapter_episode_id"),
                    "detector_prompt_enabled": True,
                    "evaluation_target_enabled": False,
                    "hm3d_objectnav_category": manifest.get("object_category"),
                    "label_canonical": label,
                    "label_text": label,
                    "object_category": manifest.get("object_category"),
                    "policy_input_allowed": True,
                    "prompt_set_id": manifest.get("prompt_set_id"),
                    "scan_id": manifest.get("scan_id"),
                    "scene_key": manifest.get("scene_key"),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                }
            )
    return rows


def expected_file_summary_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = group_by_episode(render_rows)
    rows: list[dict[str, Any]] = []
    for episode, items in sorted(grouped.items()):
        scan_id = str(items[0].get("scan_id"))
        seq = sequence_dir(scan_id)
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode,
                "scan_id": scan_id,
                "sequence_dir": str(seq),
                "expected_color_frames": len(items),
                "expected_depth_frames": len(items),
                "expected_pose_frames": len(items),
                "expected_info_files": 1,
                "expected_total_files": len(items) * 3 + 1,
            }
        )
    return rows


def build_route_materialization_rows(route_rows: list[dict[str, Any]], observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    obs_by_episode_route: Counter[tuple[str, str]] = Counter(
        (str(row.get("adapter_episode_id")), str(row.get("route_id"))) for row in observation_rows
    )
    out: list[dict[str, Any]] = []
    for route in route_rows:
        episode = str(route.get("adapter_episode_id"))
        route_id = str(route.get("route_id"))
        materialized = bool(route.get("materialize_in_m84"))
        obs_count = obs_by_episode_route.get((episode, route_id), 0)
        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_expansion_route_materialization",
                "adapter_episode_id": episode,
                "scan_id": route.get("scan_id"),
                "scene_key": route.get("scene_key"),
                "object_category": route.get("object_category"),
                "route_id": route_id,
                "m83_route_status": route.get("route_status"),
                "materialize_in_m84": materialized,
                "materialized_observation_pose_rows": obs_count,
                "materialization_status": "materialized" if materialized and obs_count > 0 else "not_materialized",
                "reason": "route selected by M83" if materialized else "M83 marked route as completed or deferred",
                "claim_boundary": "Route materialization rows are input staging, not source-gap recovery evidence.",
            }
        )
    return out


def build_preflight_rows(
    m83_coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    route_materialization_rows: list[dict[str, Any]],
    docker: dict[str, Any],
) -> list[dict[str, Any]]:
    scene_paths = sorted({str(row.get("hm3d_scene_docker_path")) for row in render_rows if row.get("hm3d_scene_docker_path")})
    navmesh_paths = sorted({str(row.get("hm3d_navmesh_docker_path")) for row in render_rows if row.get("hm3d_navmesh_docker_path")})
    habitat = image_status(docker["selected_prefix"], HABITAT_IMAGE) if docker.get("available") else {"available": False}
    real_smoke = image_status(docker["selected_prefix"], REAL_SMOKE_IMAGE) if docker.get("available") else {"available": False}
    return [
        {
            "version": VERSION,
            "gate_id": "m83_ready",
            "gate_status": "pass"
            if m83_coverage.get("status") == "e008_m83_source_gap_non_oracle_source_observation_expansion_contract_ready"
            else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": m83_coverage.get("status"),
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_case_rows_match_contract",
            "gate_status": "pass" if len(case_rows) == int(m83_coverage.get("source_gap_case_rows") or 0) else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": len(case_rows),
        },
        {
            "version": VERSION,
            "gate_id": "observation_pose_rows_within_contract",
            "gate_status": "pass" if len(case_rows) * 8 <= len(observation_rows) <= len(case_rows) * 96 else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": len(observation_rows),
        },
        {
            "version": VERSION,
            "gate_id": "render_plan_rows_within_contract",
            "gate_status": "pass" if len(case_rows) * 32 <= len(render_rows) <= len(case_rows) * 384 else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": len(render_rows),
        },
        {
            "version": VERSION,
            "gate_id": "detector_manifest_rows_match_contract",
            "gate_status": "pass" if len(manifest_rows) == len(case_rows) else "fail",
            "blocks_m84": True,
            "blocks_m86": True,
            "details": len(manifest_rows),
        },
        {
            "version": VERSION,
            "gate_id": "selected_routes_materialized",
            "gate_status": "pass"
            if sum(1 for row in route_materialization_rows if row.get("materialization_status") == "materialized")
            == int(m83_coverage.get("selected_materialization_route_rows") or 0)
            else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": sum(1 for row in route_materialization_rows if row.get("materialization_status") == "materialized"),
        },
        {
            "version": VERSION,
            "gate_id": "no_eval_goal_or_viewpoint_policy_fields",
            "gate_status": "pass"
            if not any(bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) for row in [*observation_rows, *render_rows, *manifest_rows])
            else "fail",
            "blocks_m84": True,
            "blocks_m85": True,
            "details": "policy leakage guard",
        },
        {
            "version": VERSION,
            "gate_id": "scene_files_host_ready",
            "gate_status": "pass" if all(host_path_from_docker_path(path).exists() for path in scene_paths) else "fail",
            "blocks_m84": False,
            "blocks_m85": True,
            "details": f"{len(scene_paths)} unique scene files",
        },
        {
            "version": VERSION,
            "gate_id": "navmesh_files_host_ready",
            "gate_status": "pass" if all(host_path_from_docker_path(path).exists() for path in navmesh_paths) else "fail",
            "blocks_m84": False,
            "blocks_m85": True,
            "details": f"{len(navmesh_paths)} unique navmesh files",
        },
        {
            "version": VERSION,
            "gate_id": "docker_available",
            "gate_status": "pass" if docker.get("available") else "warning",
            "blocks_m84": False,
            "blocks_m85": True,
            "details": docker.get("mode"),
        },
        {
            "version": VERSION,
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat.get("available") else "warning",
            "blocks_m84": False,
            "blocks_m85": True,
            "details": HABITAT_IMAGE,
        },
        {
            "version": VERSION,
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_smoke.get("available") else "warning",
            "blocks_m84": False,
            "blocks_m86": True,
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "version": VERSION,
            "gate_id": "no_long_job_launched_in_m84",
            "gate_status": "pass",
            "blocks_m84": False,
            "blocks_m85": False,
            "details": "M84 materializes rows and command ledger only.",
        },
    ]


def build_long_job_command_rows(docker_prefix: list[str], render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    render_log = LOG_DIR / f"{timestamp}_e008_m85_source_gap_render.log"
    detector_log = LOG_DIR / f"{timestamp}_e008_m86_source_gap_detector.log"
    render_input_dir = DATA_OUT_DIR / "render_inputs"
    detector_input_dir = DATA_OUT_DIR / "detector_inputs"

    docker_render = [
        *docker_prefix,
        "run",
        "--rm",
        "--gpus",
        "all",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "HOME=/tmp",
        "-e",
        "XDG_CACHE_HOME=/tmp/.cache",
        "-v",
        f"{RESEARCH3_DATA_ROOT}:/data:ro",
        "-v",
        f"{render_input_dir}:/inputs:ro",
        "-v",
        f"{DATA_OUT_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m84.py",
    ]
    render_shell = f"cd {shlex.quote(str(ROOT))} && {shell_join(docker_render)} > {shlex.quote(str(render_log))} 2>&1"
    render_tmux = f"mkdir -p {shlex.quote(str(LOG_DIR))} && tmux new-session -d -s {shlex.quote(RENDER_TMUX_SESSION)} {shlex.quote(render_shell)}"

    detector_command = [
        "python",
        str(E003_RUNNER),
        "--dataset-root",
        str(DATA_OUT_DIR),
        "--m17-dir",
        str(detector_input_dir),
        "--out-dir",
        str(M86_DIR),
        "--max-scans",
        "2",
        "--max-frames-per-scan",
        str(max((len(rows) for rows in group_by_episode(render_rows).values()), default=0)),
        "--max-labels",
        "8",
        "--max-predictions",
        "20000",
        "--max-predictions-per-frame",
        "100",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence_log_depth",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "100000",
        "--export-pre-cap-candidate-pool",
    ]
    detector_shell = f"cd {shlex.quote(str(ROOT))} && {shell_join(detector_command)} > {shlex.quote(str(detector_log))} 2>&1"
    detector_tmux = f"mkdir -p {shlex.quote(str(LOG_DIR))} && tmux new-session -d -s {shlex.quote(DETECTOR_TMUX_SESSION)} {shlex.quote(detector_shell)}"
    return [
        {
            "version": VERSION,
            "job_id": "E008-M85",
            "job_status": "contract_recorded_not_launched",
            "job_type": "source_gap_non_oracle_render_frame_staging",
            "working_directory": str(ROOT),
            "tmux_session": RENDER_TMUX_SESSION,
            "command": render_tmux,
            "inner_command": render_shell,
            "output_path": str(DATA_OUT_DIR),
            "log_path": str(render_log),
            "expected_files": [
                "rendered_frame_rows.jsonl",
                "snap_validation_rows.jsonl",
                "render_summary.json",
                "3RScan/scans/<scan_id>/sequence/frame-*.color.jpg",
                "3RScan/scans/<scan_id>/sequence/frame-*.depth.pgm",
                "3RScan/scans/<scan_id>/sequence/frame-*.pose.txt",
            ],
            "expected_file_count": len(render_rows) * 3 + len({row.get("scan_id") for row in render_rows}) + 3,
            "verification_command": (
                "python experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py "
                f"--artifact-dir {ARTIFACT_DIR} --data-out-dir {DATA_OUT_DIR} --require-ready"
            ),
            "next_if_verified": DETECTOR_NEXT_UNIT,
        },
        {
            "version": VERSION,
            "job_id": "E008-M86",
            "job_status": "contract_recorded_not_launched",
            "job_type": "source_gap_open_vocabulary_detector_candidate_source",
            "working_directory": str(ROOT),
            "tmux_session": DETECTOR_TMUX_SESSION,
            "command": detector_tmux,
            "inner_command": detector_shell,
            "output_path": str(M86_DIR),
            "log_path": str(detector_log),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
                "matching/coverage.json",
            ],
            "verification_command": (
                f"python {M16_VERIFY_TOOL.relative_to(ROOT)} "
                f"--m15-artifact-dir {ARTIFACT_DIR} "
                f"--m15-data-dir {DATA_OUT_DIR} "
                f"--m16-dir {M86_DIR} "
                f"--tmux-session {DETECTOR_TMUX_SESSION} --require-ready"
            ),
            "launch_after": "E008-M85 verification ready",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_materialization_contract",
            "supported": True,
            "claim_boundary": "M84 supports launch-ready source-gap render/detector input materialization.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M84 does not run rendering, detector inference, goal evaluation, or trajectories.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_navigation",
            "supported": False,
            "claim_boundary": "M84 cannot support real navigation `SR` / `SPL` without M85-M89 evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M84 has no human-intent ablation; task context remains secondary.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "rationale": "M84 only materializes launch inputs; M85 should launch the render job in tmux if Docker/Habitat are ready.",
        }
    ]


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return "NA" if value is None else str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
) -> str:
    command_summary = [
        {
            "job_id": row["job_id"],
            "job_status": row["job_status"],
            "tmux_session": row["tmux_session"],
            "output_path": row["output_path"],
            "log_path": row["log_path"],
        }
        for row in command_rows
    ]
    case_summary = [
        {
            "adapter_episode_id": row["adapter_episode_id"],
            "object_category": row["object_category"],
            "target_labels": ",".join(row["target_labels"]),
        }
        for row in case_rows
    ]
    route_summary = [
        {
            "adapter_episode_id": row["adapter_episode_id"],
            "route_id": row["route_id"],
            "status": row["materialization_status"],
            "observation_rows": row["materialized_observation_pose_rows"],
        }
        for row in route_rows
    ]
    return "\n".join(
        [
            "# E008-M84 Source-Gap Source/Observation Expansion Materialization Smoke",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M83 status: `{coverage['m83_status']}`.",
            f"- Source-gap case rows: {coverage['source_gap_case_rows']}.",
            f"- Observation pose plan rows: {coverage['observation_pose_plan_rows']}.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
            f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
            f"- Detector object target rows: {coverage['detector_object_target_rows']}.",
            f"- Selected route materializations: {coverage['selected_route_materialized_rows']}.",
            f"- Long job launched: {str(coverage['long_job_launched']).lower()}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Source-Gap Cases",
            "",
            markdown_table(case_summary, ["adapter_episode_id", "object_category", "target_labels"]),
            "",
            "## Route Materialization",
            "",
            markdown_table(route_summary, ["adapter_episode_id", "route_id", "status", "observation_rows"]),
            "",
            "## Readiness Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m84", "blocks_m85", "blocks_m86"]),
            "",
            "## Long-Job Commands",
            "",
            markdown_table(command_summary, ["job_id", "job_status", "tmux_session", "output_path", "log_path"]),
            "",
            "## Claim Boundary",
            "",
            "- M84 supports source-gap source/observation expansion input materialization only.",
            "- M84 does not render frames, run detector inference, evaluate source-gap recovery, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    m83_coverage = read_json(M83_DIR / "coverage.json")
    m83_case_rows = read_jsonl(M83_DIR / "source_gap_contract_case_rows.jsonl")
    m83_route_rows = read_jsonl(M83_DIR / "source_observation_expansion_route_rows.jsonl")
    m64_observation_rows = read_jsonl(M64_DIR / "observation_pose_plan_rows.jsonl")
    m80_candidate_rows = read_jsonl(M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl")
    prompt_set = read_json(M65_DIR / "prompt_set.json") or read_json(M64_DIR / "prompt_set.json")
    proposal_schema = read_json(M65_DIR / "proposal_output_schema.json")

    missing_inputs = []
    for path, rows in [
        (M83_DIR / "coverage.json", [m83_coverage] if m83_coverage else []),
        (M83_DIR / "source_gap_contract_case_rows.jsonl", m83_case_rows),
        (M83_DIR / "source_observation_expansion_route_rows.jsonl", m83_route_rows),
        (M64_DIR / "observation_pose_plan_rows.jsonl", m64_observation_rows),
        (M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl", m80_candidate_rows),
        (M65_DIR / "prompt_set.json", [prompt_set] if prompt_set else []),
        (M65_DIR / "proposal_output_schema.json", [proposal_schema] if proposal_schema else []),
    ]:
        if not rows:
            missing_inputs.append(str(path))

    case_rows = build_case_rows(m83_case_rows)
    observation_rows = build_observation_pose_rows(case_rows, m64_observation_rows, m80_candidate_rows)
    render_rows = build_render_rows(observation_rows)
    detector_manifest_rows = build_detector_manifest_rows(case_rows, render_rows)
    detector_object_target_rows = build_object_target_rows(detector_manifest_rows)
    expected_rows = expected_file_summary_rows(render_rows)
    route_materialization_rows = build_route_materialization_rows(m83_route_rows, observation_rows)
    docker = docker_status()
    gate_rows = build_preflight_rows(
        m83_coverage,
        case_rows,
        observation_rows,
        render_rows,
        detector_manifest_rows,
        route_materialization_rows,
        docker,
    )
    command_rows = build_long_job_command_rows(docker["selected_prefix"], render_rows)
    claim_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    render_input_dir = DATA_OUT_DIR / "render_inputs"
    detector_input_dir = DATA_OUT_DIR / "detector_inputs"
    write_jsonl(render_input_dir / "render_plan_rows.jsonl", render_rows)
    write_text(render_input_dir / "render_m84.py", m15_render_script_for_m84())
    write_jsonl(detector_input_dir / "real_proposal_query_manifest.jsonl", detector_manifest_rows)
    write_jsonl(detector_input_dir / "real_proposal_object_targets.jsonl", detector_object_target_rows)
    write_json(detector_input_dir / "prompt_set.json", prompt_set)
    write_json(detector_input_dir / "proposal_output_schema.json", proposal_schema)

    m84_blockers = [
        row["gate_id"] for row in gate_rows if row.get("blocks_m84") and row.get("gate_status") == "fail"
    ]
    selected_materialized = sum(
        1 for row in route_materialization_rows if row.get("materialization_status") == "materialized"
    )
    status = READY_STATUS if not missing_inputs and not m84_blockers else BLOCKED_STATUS
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m83_status": m83_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "m84_blockers": m84_blockers,
        "source_gap_case_rows": len(case_rows),
        "observation_pose_plan_rows": len(observation_rows),
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(detector_manifest_rows),
        "detector_object_target_rows": len(detector_object_target_rows),
        "expected_file_summary_rows": len(expected_rows),
        "route_materialization_rows": len(route_materialization_rows),
        "selected_route_materialized_rows": selected_materialized,
        "readiness_gate_rows": len(gate_rows),
        "readiness_gate_fail_rows": sum(1 for row in gate_rows if row.get("gate_status") == "fail"),
        "readiness_gate_warning_rows": sum(1 for row in gate_rows if row.get("gate_status") == "warning"),
        "long_job_command_rows": len(command_rows),
        "claim_boundary_rows": len(claim_rows),
        "docker_status": docker,
        "render_input_dir": str(render_input_dir),
        "detector_input_dir": str(detector_input_dir),
        "render_script_ready": (render_input_dir / "render_m84.py").exists(),
        "detector_input_files_ready": all(
            [
                (detector_input_dir / "real_proposal_query_manifest.jsonl").exists(),
                (detector_input_dir / "real_proposal_object_targets.jsonl").exists(),
                (detector_input_dir / "prompt_set.json").exists(),
                (detector_input_dir / "proposal_output_schema.json").exists(),
            ]
        ),
        "m85_render_launch_ready_next": status == READY_STATUS,
        "m86_detector_launch_ready_now": False,
        "long_job_launched": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "render_frames_ready": False,
        "detector_candidate_rows_ready": False,
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else "repair E008-M84 materialization",
    }

    write_jsonl(ARTIFACT_DIR / "source_gap_case_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_observation_pose_plan_rows.jsonl", observation_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_render_plan_rows.jsonl", render_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_detector_manifest_rows.jsonl", detector_manifest_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_detector_object_target_rows.jsonl", detector_object_target_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_expansion_route_materialization_rows.jsonl", route_materialization_rows)
    write_jsonl(ARTIFACT_DIR / "expected_file_summary_rows.jsonl", expected_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "prompt_set.json", prompt_set)
    write_json(ARTIFACT_DIR / "proposal_output_schema.json", proposal_schema)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, case_rows, route_materialization_rows, gate_rows, command_rows))

    write_jsonl(DATA_OUT_DIR / "source_gap_case_rows.jsonl", case_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_observation_pose_plan_rows.jsonl", observation_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_render_plan_rows.jsonl", render_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_detector_manifest_rows.jsonl", detector_manifest_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_expansion_route_materialization_rows.jsonl", route_materialization_rows)
    write_jsonl(DATA_OUT_DIR / "expected_file_summary_rows.jsonl", expected_rows)
    write_jsonl(DATA_OUT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(DATA_OUT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_jsonl(DATA_OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(DATA_OUT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_text(DATA_OUT_DIR / "report.md", build_report(coverage, case_rows, route_materialization_rows, gate_rows, command_rows))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"] == READY_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
