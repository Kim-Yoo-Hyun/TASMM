#!/usr/bin/env python3
"""Validate E008-M177 source poses and write the E008-M179 render/detector launcher contract."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import shlex
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M15_RENDER_TOOL = EXP_ROOT / "tools" / "run_m15_non_oracle_observation_expansion_frame_staging.py"
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M177_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M177_source_pool_pose_render_plan_materialization_contract_v0"
M177_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M177_source_pool_pose_render_plan_materialization_contract_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
)
M179_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M179_bounded_render_detector_execution_verification_v0"

VERSION = "e008_m178_navmesh_snap_render_detector_launcher_contract_v0"
READY_STATUS = "e008_m178_navmesh_snap_render_detector_launcher_contract_ready"
READY_WARNING_STATUS = "e008_m178_navmesh_snap_render_detector_launcher_contract_ready_with_snap_warnings"
BLOCKED_STATUS = "e008_m178_navmesh_snap_render_detector_launcher_contract_blocked"
NEXT_UNIT = "E008-M179 bounded render/detector execution and verification"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
REAL_SMOKE_IMAGE = "research2/real-smoke"
SCENE_DATASET_CONFIG = (
    "/data/versioned_data/hm3d-0.2/hm3d/minival/"
    "hm3d_annotated_minival_basis.scene_dataset_config.json"
)
LOG_DIR = ROOT / "logs"
RENDER_TMUX_SESSION = "e008_m179_source_pool_render"
DETECTOR_TMUX_SESSION = "e008_m179_source_pool_detector"
YAW_OFFSETS_DEG = [0, 90, 180, 270]
RENDER_WIDTH = 640
RENDER_HEIGHT = 480


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


def command_status(command: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - contract records local preflight failures.
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stderr": repr(exc),
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
    direct = command_status(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=20)
    sudo_n = command_status(["sudo", "-n", "docker", "info", "--format", "{{.ServerVersion}}"], timeout=20)
    if direct["available"]:
        return {"available": True, "mode": "direct", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo_n}
    if sudo_n["available"]:
        return {"available": True, "mode": "sudo_n", "selected_prefix": ["sudo", "-n", "docker"], "direct": direct, "sudo_n": sudo_n}
    return {"available": False, "mode": "unavailable", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo_n}


def image_status(prefix: list[str], image: str) -> dict[str, Any]:
    if not prefix:
        return {"available": False, "command": [], "returncode": None, "stderr": "docker unavailable", "stdout": ""}
    return command_status([*prefix, "image", "inspect", image, "--format", "{{.Id}}"], timeout=30)


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in command)


def parse_json_stdout(stdout: str) -> Any:
    for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
        if line.startswith("[") or line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON payload in docker stdout")


def run_habitat_snap_validation(input_path: Path, docker: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prefix = docker.get("selected_prefix") or ["docker"]
    if not docker.get("available"):
        return [], {"ok": False, "returncode": None, "stderr_tail": "docker unavailable", "stdout_tail": ""}
    code = f"""
import json
import math
from pathlib import Path

import habitat_sim

rows = [json.loads(line) for line in Path({json.dumps('/work/' + str(input_path.relative_to(ROOT)))}).read_text(encoding='utf-8').splitlines() if line.strip()]

def finite_vec(vec):
    try:
        return len(vec) == 3 and all(math.isfinite(float(value)) for value in vec)
    except Exception:
        return False

def as_float_list(vec):
    return [float(value) for value in vec]

def dist(a, b):
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))

def find_path(sim, start, end):
    out = {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": ""}}
    try:
        path = habitat_sim.ShortestPath()
        path.requested_start = [float(value) for value in start]
        path.requested_end = [float(value) for value in end]
        found = bool(sim.pathfinder.find_path(path))
        out["path_found"] = found
        out["geodesic_distance"] = float(path.geodesic_distance) if found else None
        out["point_count"] = len(path.points) if found else 0
    except Exception as exc:
        out["error"] = repr(exc)
    return out

by_scene = {{}}
for row in rows:
    scene = row.get("hm3d_scene_docker_path")
    if scene:
        by_scene.setdefault(str(scene), []).append(row)

result_rows = []
seen = set()
for scene_path, scene_rows in by_scene.items():
    sim = None
    try:
        sim_cfg = habitat_sim.SimulatorConfiguration()
        sim_cfg.scene_id = scene_path
        sim_cfg.scene_dataset_config_file = {json.dumps(SCENE_DATASET_CONFIG)}
        sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.AgentConfiguration()]))
        navmesh_path = scene_rows[0].get("hm3d_navmesh_docker_path")
        if navmesh_path and not sim.pathfinder.is_loaded:
            sim.pathfinder.load_nav_mesh(str(navmesh_path))
        for row in scene_rows:
            out = dict(row)
            seen.add(row.get("observation_pose_id"))
            planned = row.get("planned_position_m") or row.get("source_position")
            anchor = row.get("source_anchor_position_m")
            out["pathfinder_loaded"] = bool(sim.pathfinder.is_loaded)
            out["planned_position_valid"] = finite_vec(planned)
            out["source_anchor_position_valid"] = finite_vec(anchor)
            out["planned_source_navigable"] = bool(sim.pathfinder.is_navigable(planned)) if finite_vec(planned) else False
            out["source_anchor_navigable"] = bool(sim.pathfinder.is_navigable(anchor)) if finite_vec(anchor) else False
            if finite_vec(planned):
                snapped = sim.pathfinder.snap_point(planned)
                snapped_list = as_float_list(snapped)
            else:
                snapped_list = None
            out["snapped_position_m"] = snapped_list
            out["snapped_position_valid"] = finite_vec(snapped_list)
            out["snapped_navigable"] = bool(sim.pathfinder.is_navigable(snapped_list)) if finite_vec(snapped_list) else False
            out["snap_distance_m"] = dist(planned, snapped_list) if finite_vec(planned) and finite_vec(snapped_list) else None
            path = find_path(sim, anchor, snapped_list) if finite_vec(anchor) and finite_vec(snapped_list) else {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": "missing_anchor_or_snapped"}}
            out["source_anchor_to_snapped_path_found"] = path["path_found"]
            out["source_anchor_to_snapped_geodesic_m"] = path["geodesic_distance"]
            out["source_anchor_to_snapped_path_point_count"] = path["point_count"]
            out["source_anchor_to_snapped_path_error"] = path["error"]
            out["render_position_m"] = snapped_list if finite_vec(snapped_list) else planned
            out["snap_validation_ready"] = bool(out["pathfinder_loaded"] and out["snapped_navigable"])
            out["source_ready_for_m180"] = bool(out["snap_validation_ready"] and out["source_anchor_to_snapped_path_found"])
            out["snap_warning_large_move"] = bool(out["snap_distance_m"] is not None and float(out["snap_distance_m"]) > 2.0)
            result_rows.append(out)
    except Exception as exc:
        for row in scene_rows:
            out = dict(row)
            seen.add(row.get("observation_pose_id"))
            out["pathfinder_loaded"] = False
            out["scene_error"] = repr(exc)
            out["snap_validation_ready"] = False
            out["source_ready_for_m180"] = False
            result_rows.append(out)
    finally:
        if sim is not None:
            sim.close()

for row in rows:
    if row.get("observation_pose_id") not in seen:
        out = dict(row)
        out["pathfinder_loaded"] = False
        out["skip_reason"] = "missing_scene_path"
        out["snap_validation_ready"] = False
        out["source_ready_for_m180"] = False
        result_rows.append(out)

print(json.dumps(result_rows, sort_keys=True))
"""
    cmd = [
        *prefix,
        "run",
        "--rm",
        "-v",
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "-v",
        f"{ROOT}:/work:ro",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python - <<'PY'\n" + code + "\nPY",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=360)
    meta = {
        "command": shell_join(cmd[:12]) + " ...",
        "mounts": [f"{RESEARCH2_DATA_ROOT}:/data:ro", f"{ROOT}:/work:ro"],
        "ok": proc.returncode == 0,
        "requested_observation_pose_rows": sum(1 for _ in input_path.open("r", encoding="utf-8")),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
        "stdout_tail": proc.stdout[-2000:],
    }
    if proc.returncode != 0:
        return [], meta
    try:
        return parse_json_stdout(proc.stdout), meta
    except Exception as exc:  # noqa: BLE001 - record parse failure as artifact.
        meta["ok"] = False
        meta["parse_error"] = str(exc)
        return [], meta


def load_m15_render_tool() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m15_render_tool", M15_RENDER_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 render tool: {M15_RENDER_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_script_for_m178() -> str:
    module = load_m15_render_tool()
    module.DATA_OUT_DIR = DATA_OUT_DIR
    module.SCENE_DATASET_CONFIG = SCENE_DATASET_CONFIG
    return module.render_script()


def build_render_plan_rows(snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frame_index_by_scan: Counter[str] = Counter()
    for pose in sorted(
        [row for row in snap_rows if row.get("snap_validation_ready")],
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
                    "render_source": "e008_m178_navmesh_snap_render_detector_launcher_contract",
                    "render_width": RENDER_WIDTH,
                    "render_height": RENDER_HEIGHT,
                    "hm3d_scene_docker_path": pose.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": pose.get("hm3d_navmesh_docker_path"),
                    "planned_source_position": pose.get("planned_position_m"),
                    "source_position": pose.get("render_position_m"),
                    "source_position_source": "E008-M178 snap_validation render_position_m",
                    "source_rotation": pose.get("source_rotation") or pose.get("source_rotation_xyzw"),
                    "source_rotation_xyzw": pose.get("source_rotation_xyzw") or pose.get("source_rotation"),
                    "yaw_offset_deg": yaw,
                    "requires_navmesh_snap_validation": False,
                    "source_snap_distance_m": pose.get("snap_distance_m"),
                    "source_snap_validation_ready": pose.get("snap_validation_ready"),
                    "source_ready_for_m180": pose.get("source_ready_for_m180"),
                    "source_anchor_to_snapped_geodesic_m": pose.get("source_anchor_to_snapped_geodesic_m"),
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


def build_object_target_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for render in render_rows:
        scan_id = str(render.get("scan_id"))
        label = str(render.get("object_category"))
        key = (scan_id, label)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_pool_detector_object_target",
                "adapter_episode_id": render.get("adapter_episode_id"),
                "detector_prompt_enabled": True,
                "evaluation_target_enabled": False,
                "hm3d_objectnav_category": label,
                "label_canonical": label,
                "label_text": label,
                "object_category": label,
                "policy_input_allowed": True,
                "prompt_set_id": "e008_m178_source_pool_detector_prompts_v0",
                "scan_id": scan_id,
                "scene_key": render.get("scene_key"),
                "source": "E008-M178 HM3D ObjectNav category text only after source-pool rows are frozen",
                "target_uid": f"e008-m178:{scan_id}:{label}",
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
            }
        )
    return rows


def build_prompt_set(object_target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label: dict[str, set[str]] = defaultdict(set)
    by_category: dict[str, set[str]] = defaultdict(set)
    for row in object_target_rows:
        label = str(row.get("label_canonical"))
        by_label[label].add(str(row.get("scan_id")))
        by_category[label].add(str(row.get("hm3d_objectnav_category")))
    return {
        "version": VERSION,
        "prompt_set_id": "e008_m178_source_pool_detector_prompts_v0",
        "prompt_policy": (
            "M178 uses query category text only after source-pool source rows are frozen; "
            "ObjectNav goal/viewpoint fields are blocked."
        ),
        "label_count": len(by_label),
        "detector_target_label_count": len(by_label),
        "labels": [
            {
                "aliases": [],
                "detector_prompt_enabled": True,
                "hm3d_objectnav_categories": sorted(by_category[label]),
                "label_canonical": label,
                "prompt_role": "detector_target",
                "prompts": [f"a {label}", label, f"the {label}"],
                "scan_count": len(by_label[label]),
                "scan_ids": sorted(by_label[label]),
            }
            for label in sorted(by_label)
        ],
    }


def proposal_output_schema() -> dict[str, Any]:
    source = M93_DATA_DIR / "detector_inputs" / "proposal_output_schema.json"
    payload = read_json(source)
    if not payload:
        payload = {
            "schema_id": "real_proposal_prediction_jsonl_v0",
            "file_name": "real_proposals.jsonl",
            "required_fields": {
                "scan_id": "HM3D adapter scan id",
                "frame_ids": "RGB-D frame ids supporting the proposal",
                "label_canonical": "canonical detector label",
                "confidence": "detector confidence score",
                "centroid_world_m": "proposal centroid in world coordinates",
                "proposal_uid": "stable proposal id",
            },
            "blocked_fields": [
                "ObjectNav goal/viewpoint fields must not be used by detector or ranking policy",
                "candidate-to-target distance is evaluation-only",
            ],
        }
    payload = dict(payload)
    payload["source_version"] = payload.get("version")
    payload["version"] = VERSION
    payload["source_schema_path"] = str(source)
    payload["blocked_fields"] = sorted(
        set(payload.get("blocked_fields", []))
        | {
            "ObjectNav eval goal and target viewpoints are blocked for source placement and detector ranking",
            "target object id, candidate-to-target distance, and success labels are blocked policy inputs",
        }
    )
    return payload


def route_frame_indices(render_rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row.get("scan_id"))].append(int(row.get("frame_index") or 0))
    return {key: sorted(values) for key, values in grouped.items()}


def build_detector_manifest_rows(
    render_rows: list[dict[str, Any]],
    object_target_path: Path,
    prompt_set_path: Path,
    schema_path: Path,
) -> list[dict[str, Any]]:
    indices_by_scan = route_frame_indices(render_rows)
    first_by_scan: dict[str, dict[str, Any]] = {}
    for row in render_rows:
        first_by_scan.setdefault(str(row.get("scan_id")), row)
    rows: list[dict[str, Any]] = []
    for scan_id, indices in sorted(indices_by_scan.items()):
        render = first_by_scan[scan_id]
        label = str(render.get("object_category"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_pool_detector_manifest",
                "adapter_episode_id": render.get("adapter_episode_id"),
                "batch_id": "e008_m178_source_pool",
                "detector_config_id": "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0",
                "detector_target_count": 1,
                "evaluation_target_count": 0,
                "frame_id_format": "frame-{index:06d}",
                "frame_sampling_strategy": "m177_source_pool_budgeted_multiview",
                "max_frames": len(indices),
                "object_category": label,
                "object_target_path": str(object_target_path),
                "paper_table_role": "source_pool_materialization_not_result",
                "policy_input_allowed": True,
                "prompt_set_id": "e008_m178_source_pool_detector_prompts_v0",
                "prompt_set_path": str(prompt_set_path),
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": str(schema_path),
                "route_id": "source_pool_budgeted_priority_expansion_v1",
                "route_ids": ["source_pool_budgeted_priority_expansion_v1"],
                "sampled_frame_count": len(indices),
                "sampled_frame_indices": indices,
                "scan_id": scan_id,
                "scene_key": render.get("scene_key"),
                "sequence_dir_compat_path": str(DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"),
                "target_label_count": 1,
                "target_labels": [label],
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                "claim_boundary": (
                    "Detector prompt uses object category only after M177/M178 source-pool source poses are frozen; "
                    "no ObjectNav target/viewpoint source-placement input is used."
                ),
            }
        )
    return rows


def expected_file_summary_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row.get("scan_id"))].append(row)
    out: list[dict[str, Any]] = []
    for scan_id, rows in sorted(grouped.items()):
        sequence = DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"
        out.append(
            {
                "version": VERSION,
                "row_type": "expected_render_file_summary",
                "scan_id": scan_id,
                "adapter_episode_id": rows[0].get("adapter_episode_id"),
                "scene_key": rows[0].get("scene_key"),
                "object_category": rows[0].get("object_category"),
                "sequence_dir": str(sequence),
                "expected_color_frames": len(rows),
                "expected_depth_frames": len(rows),
                "expected_pose_frames": len(rows),
                "expected_info_files": 1,
                "expected_total_files": len(rows) * 3 + 1,
            }
        )
    return out


def write_launcher_inputs(
    render_rows: list[dict[str, Any]],
    detector_manifest_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
    prompt_payload: dict[str, Any],
    schema_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    render_input_dir = DATA_OUT_DIR / "render_inputs"
    detector_input_dir = DATA_OUT_DIR / "detector_inputs"
    render_input_dir.mkdir(parents=True, exist_ok=True)
    detector_input_dir.mkdir(parents=True, exist_ok=True)
    files: list[tuple[Path, str, Any, str]] = [
        (render_input_dir / "render_plan_rows.jsonl", "render_plan_rows", render_rows, "jsonl"),
        (detector_input_dir / "real_proposal_query_manifest.jsonl", "real_proposal_query_manifest", detector_manifest_rows, "jsonl"),
        (detector_input_dir / "real_proposal_object_targets.jsonl", "real_proposal_object_targets", object_target_rows, "jsonl"),
        (detector_input_dir / "prompt_set.json", "prompt_set", prompt_payload, "json"),
        (detector_input_dir / "proposal_output_schema.json", "proposal_output_schema", schema_payload, "json"),
    ]
    rows: list[dict[str, Any]] = []
    for path, role, payload, file_type in files:
        if file_type == "jsonl":
            write_jsonl(path, payload)
            row_count = len(payload)
        else:
            write_json(path, payload)
            row_count = payload.get("label_count") if role == "prompt_set" else None
        rows.append(
            {
                "version": VERSION,
                "row_type": "launcher_input_materialization",
                "file_role": role,
                "path": str(path),
                "rows": row_count,
                "ready": path.exists() and path.stat().st_size > 0,
                "data_bearing_root": str(DATA_OUT_DIR),
            }
        )
    render_script = render_input_dir / "render_m178_source_pool.py"
    write_text(render_script, render_script_for_m178())
    rows.append(
        {
            "version": VERSION,
            "row_type": "launcher_input_materialization",
            "file_role": "render_script",
            "path": str(render_script),
            "rows": None,
            "ready": render_script.exists() and render_script.stat().st_size > 0,
            "data_bearing_root": str(DATA_OUT_DIR),
        }
    )
    return rows


def build_long_job_command_rows(docker: dict[str, Any], detector_manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    render_log = LOG_DIR / f"{timestamp}_e008_m179_source_pool_render.log"
    detector_log = LOG_DIR / f"{timestamp}_e008_m179_source_pool_detector.log"
    render_input_dir = DATA_OUT_DIR / "render_inputs"
    detector_input_dir = DATA_OUT_DIR / "detector_inputs"
    docker_prefix = docker.get("selected_prefix") or ["docker"]
    max_frames_per_manifest = max((int(row.get("sampled_frame_count") or 0) for row in detector_manifest_rows), default=0)
    max_scans = max(len(detector_manifest_rows), 1)
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
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "-v",
        f"{render_input_dir}:/inputs:ro",
        "-v",
        f"{DATA_OUT_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m178_source_pool.py",
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
        str(M179_ARTIFACT_DIR / "detector"),
        "--max-scans",
        str(max_scans),
        "--max-frames-per-scan",
        str(max_frames_per_manifest),
        "--max-labels",
        "1",
        "--max-predictions",
        "12000",
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
            "row_type": "long_job_command",
            "job_id": "E008-M179-render",
            "job_status": "contract_recorded_not_launched",
            "job_type": "source_pool_render_frame_staging",
            "tmux_session": RENDER_TMUX_SESSION,
            "working_directory": str(ROOT),
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
            "verification_command": "python experiments/E008_real_navigation_benchmark/tools/verify_m179_bounded_render_detector_execution.py --require-render-ready",
            "launch_now": False,
        },
        {
            "version": VERSION,
            "row_type": "long_job_command",
            "job_id": "E008-M179-detector",
            "job_status": "deferred_until_render_verification",
            "job_type": "source_pool_open_vocabulary_detector",
            "tmux_session": DETECTOR_TMUX_SESSION,
            "working_directory": str(ROOT),
            "command": detector_tmux,
            "inner_command": detector_shell,
            "output_path": str(M179_ARTIFACT_DIR / "detector"),
            "log_path": str(detector_log),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
            ],
            "verification_command": "python experiments/E008_real_navigation_benchmark/tools/verify_m179_bounded_render_detector_execution.py --require-ready",
            "launch_now": False,
        },
    ]


def build_readiness_rows(
    m177: dict[str, Any],
    snap_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    detector_manifest_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    docker: dict[str, Any],
) -> list[dict[str, Any]]:
    prefix = docker.get("selected_prefix") or ["docker"]
    habitat_image = image_status(prefix, HABITAT_IMAGE) if docker.get("available") else {"available": False}
    real_image = image_status(prefix, REAL_SMOKE_IMAGE) if docker.get("available") else {"available": False}
    selected_scans = {str(row.get("scan_id")) for row in read_jsonl(M177_ARTIFACT_DIR / "selected_source_request_rows.jsonl")}
    snap_ready_scans = {str(row.get("scan_id")) for row in snap_rows if row.get("snap_validation_ready")}
    source_ready_scans = {str(row.get("scan_id")) for row in snap_rows if row.get("source_ready_for_m180")}
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m177_ready",
            "gate_status": "pass" if m177.get("status") == "e008_m177_source_pool_pose_render_plan_materialization_contract_ready" else "fail",
            "blocks_m178": True,
            "details": m177.get("status"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "snap_validation_rows_ready",
            "gate_status": "pass" if snap_rows and all(row.get("snap_validation_ready") for row in snap_rows) else "warning" if snap_rows else "fail",
            "blocks_m178": not bool(snap_rows),
            "details": {
                "snap_rows": len(snap_rows),
                "snap_ready_rows": sum(1 for row in snap_rows if row.get("snap_validation_ready")),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "selected_request_scan_coverage_ready",
            "gate_status": "pass" if selected_scans and selected_scans <= snap_ready_scans else "fail",
            "blocks_m178": True,
            "details": {
                "selected_request_scans": len(selected_scans),
                "snap_ready_selected_scans": len(selected_scans & snap_ready_scans),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "source_readiness_for_m180_visible",
            "gate_status": "pass" if selected_scans and selected_scans <= source_ready_scans else "warning",
            "blocks_m178": False,
            "details": {
                "selected_request_scans": len(selected_scans),
                "source_ready_selected_scans": len(selected_scans & source_ready_scans),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "bounded_render_rows_ready",
            "gate_status": "pass" if 0 < len(render_rows) <= 256 else "fail",
            "blocks_m178": True,
            "details": len(render_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "detector_manifest_ready",
            "gate_status": "pass" if detector_manifest_rows else "fail",
            "blocks_m178": True,
            "details": len(detector_manifest_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "launcher_inputs_written",
            "gate_status": "pass" if input_rows and all(row.get("ready") for row in input_rows) else "fail",
            "blocks_m178": True,
            "details": Counter(str(row.get("ready")) for row in input_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "external_hm3d_data_readonly_source_ready",
            "gate_status": "pass" if RESEARCH2_DATA_ROOT.exists() else "fail",
            "blocks_m179": True,
            "details": str(RESEARCH2_DATA_ROOT),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "docker_available",
            "gate_status": "pass" if docker.get("available") else "fail",
            "blocks_m178": True,
            "details": docker.get("mode"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat_image.get("available") else "warning",
            "blocks_m179": True,
            "details": HABITAT_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_image.get("available") else "warning",
            "blocks_m179": True,
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "tmux_sessions_free",
            "gate_status": "pass" if not tmux_running(RENDER_TMUX_SESSION) and not tmux_running(DETECTOR_TMUX_SESSION) else "warning",
            "blocks_m179": True,
            "details": [RENDER_TMUX_SESSION, DETECTOR_TMUX_SESSION],
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "source_pool_snap_launcher_contract",
            "support_status": "supported_if_ready",
            "allowed_claim": "M178 validates source-pool pose snap readiness and writes exact bounded render/detector launcher inputs.",
            "blocked_claims": [
                "expanded source-pool candidates recover targets",
                "real RGB-D/open-vocabulary robustness is solved",
                "real navigation SR/SPL improves",
                "deployable search policy is ready",
                "human intent is a main contribution",
            ],
        }
    ]


def build_reviewer_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Does M178 change the denominator or tune thresholds after seeing evaluation success?",
            "answer": "No. It consumes the fixed M177 selected request/pose budget and validates only navmesh snap/source readiness before any detector or goal evaluation.",
            "evidence": {
                "selected_request_rows": coverage["selected_request_rows"],
                "source_pose_rows": coverage["source_pose_rows"],
                "render_plan_rows": coverage["render_plan_rows"],
            },
        },
        {
            "version": VERSION,
            "question": "Why is detector prompt use allowed here?",
            "answer": "The object category is a query input, but ObjectNav goal coordinates/viewpoints, success labels, and target ids remain blocked.",
        },
        {
            "version": VERSION,
            "question": "Does M178 itself support real navigation claims?",
            "answer": "No. It is a launcher/preflight contract. M179-M185 remain required before any interpretation.",
        },
    ]


def build_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M178 readiness gates pass and M179 render/detector commands are recorded but not launched.",
            "observed": coverage["m179_gate_ready"],
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "Snap validation is partial or source-readiness warning exists.",
            "observed": bool(coverage["snap_warning_rows"] or coverage["source_ready_warning_rows"]),
            "next_action": "Proceed only as diagnostic and keep source-ready/source-gap split in M180.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M177 not ready, Docker/Habitat unavailable, no snap-ready rows, no render rows, or no launcher inputs.",
            "observed": bool(coverage["blockers"]),
            "next_action": "Do not launch M179 until blockers are fixed.",
        },
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M178 Navmesh/Snap Render/Detector Launcher Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M177 status: `{coverage['m177_status']}`.",
            f"- Selected request rows: {coverage['selected_request_rows']}.",
            f"- Source pose rows: {coverage['source_pose_rows']}.",
            f"- Snap-ready rows: {coverage['snap_ready_rows']} / {coverage['snap_validation_rows']}.",
            f"- Source-ready rows for M180: {coverage['source_ready_rows']} / {coverage['snap_validation_rows']}.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
            f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
            f"- Launcher input rows: {coverage['launcher_input_materialization_rows']}.",
            f"- M179 gate ready: {str(coverage['m179_gate_ready']).lower()}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M178 validates source-pool pose feasibility and records render/detector launcher inputs only.",
            "- It does not render frames, run detector inference, evaluate targets, or execute trajectories.",
            "- Real navigation `SR` / `SPL` remains blocked until M184, and protected interpretation remains blocked until M185.",
            "",
            "## Next",
            "",
            f"- {NEXT_UNIT}.",
            "",
        ]
    )


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    m177 = read_json(M177_ARTIFACT_DIR / "coverage.json")
    selected_requests = read_jsonl(M177_ARTIFACT_DIR / "selected_source_request_rows.jsonl")
    pose_rows = read_jsonl(M177_ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl")
    write_jsonl(ARTIFACT_DIR / "snap_input_rows.jsonl", pose_rows)
    docker = docker_status()
    snap_rows, snap_meta = run_habitat_snap_validation(ARTIFACT_DIR / "snap_input_rows.jsonl", docker)
    render_rows = build_render_plan_rows(snap_rows)
    object_target_rows = build_object_target_rows(render_rows)
    prompt_payload = build_prompt_set(object_target_rows)
    schema_payload = proposal_output_schema()
    detector_manifest_rows = build_detector_manifest_rows(
        render_rows,
        DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl",
        DATA_OUT_DIR / "detector_inputs" / "prompt_set.json",
        DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json",
    )
    expected_rows = expected_file_summary_rows(render_rows)
    input_rows = write_launcher_inputs(
        render_rows=render_rows,
        detector_manifest_rows=detector_manifest_rows,
        object_target_rows=object_target_rows,
        prompt_payload=prompt_payload,
        schema_payload=schema_payload,
    )
    command_rows = build_long_job_command_rows(docker, detector_manifest_rows)
    readiness_rows = build_readiness_rows(m177, snap_rows, render_rows, detector_manifest_rows, input_rows, docker)
    blockers = [
        str(row.get("gate_id"))
        for row in readiness_rows
        if row.get("blocks_m178") and row.get("gate_status") == "fail"
    ]
    warning_rows = [row for row in readiness_rows if row.get("gate_status") == "warning"]
    status = BLOCKED_STATUS if blockers else READY_WARNING_STATUS if warning_rows else READY_STATUS
    source_ready_warning_rows = [
        row for row in readiness_rows if row.get("gate_id") == "source_readiness_for_m180_visible" and row.get("gate_status") == "warning"
    ]
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "warnings": [str(row.get("gate_id")) for row in warning_rows],
        "m177_status": m177.get("status"),
        "selected_request_rows": len(selected_requests),
        "source_pose_rows": len(pose_rows),
        "snap_validation_rows": len(snap_rows),
        "snap_ready_rows": sum(1 for row in snap_rows if row.get("snap_validation_ready")),
        "source_ready_rows": sum(1 for row in snap_rows if row.get("source_ready_for_m180")),
        "snap_warning_rows": sum(1 for row in snap_rows if row.get("snap_warning_large_move")),
        "source_ready_warning_rows": len(source_ready_warning_rows),
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(detector_manifest_rows),
        "object_target_rows": len(object_target_rows),
        "expected_file_summary_rows": len(expected_rows),
        "launcher_input_materialization_rows": len(input_rows),
        "long_job_command_rows": len(command_rows),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if row.get("gate_status") == "fail"),
        "readiness_gate_warning_rows": len(warning_rows),
        "snap_validation_meta": snap_meta,
        "render_input_dir": str(DATA_OUT_DIR / "render_inputs"),
        "detector_input_dir": str(DATA_OUT_DIR / "detector_inputs"),
        "render_plan_output": str(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl"),
        "detector_manifest_output": str(DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl"),
        "m179_gate_ready": status in {READY_STATUS, READY_WARNING_STATUS},
        "launch_long_job_now": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "detector_candidate_rows_ready": False,
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if status in {READY_STATUS, READY_WARNING_STATUS} else "repair E008-M178 blockers",
    }
    gate_rows = build_gate_rows(coverage)
    route_rows = [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision": "m178_ready_select_m179" if coverage["m179_gate_ready"] else "m178_blocked",
            "selected_next_unit": coverage["selected_next_unit"],
            "requires_long_job_next": coverage["m179_gate_ready"],
            "launch_long_job_now": False,
            "reason": (
                "M178 validated source-pool snap readiness and wrote bounded render/detector launcher inputs."
                if coverage["m179_gate_ready"]
                else "M178 has blocking readiness failures."
            ),
        }
    ]
    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "next_unit": coverage["selected_next_unit"],
            "action": "Launch E008-M179 render job in tmux; after render verification, launch detector job.",
            "launch_long_job_now": False,
        }
    ]

    outputs: dict[str, Any] = {
        "snap_validation_rows.jsonl": snap_rows,
        "source_pool_render_plan_rows.jsonl": render_rows,
        "source_pool_detector_manifest_rows.jsonl": detector_manifest_rows,
        "source_pool_object_target_rows.jsonl": object_target_rows,
        "expected_file_summary_rows.jsonl": expected_rows,
        "launcher_input_materialization_rows.jsonl": input_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "long_job_command_rows.jsonl": command_rows,
        "m179_gate_rows.jsonl": gate_rows,
        "claim_boundary_rows.jsonl": build_claim_rows(),
        "reviewer_defense_rows.jsonl": build_reviewer_rows(coverage),
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_action_rows,
    }
    output_paths: list[Path] = []
    for name, payload in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, payload)
        output_paths.append(path)
    write_json(ARTIFACT_DIR / "source_pool_prompt_set.json", prompt_payload)
    write_json(ARTIFACT_DIR / "source_pool_proposal_output_schema.json", schema_payload)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    output_paths.extend(
        [
            ARTIFACT_DIR / "source_pool_prompt_set.json",
            ARTIFACT_DIR / "source_pool_proposal_output_schema.json",
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "report.md",
        ]
    )
    mirror_outputs(output_paths)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["m179_gate_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
