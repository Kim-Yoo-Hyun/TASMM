#!/usr/bin/env python3
"""Run E008-M08 HM3D rendered RGB-D frame staging smoke."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
VERSION = "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_v0"

M07_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
VERIFY_SCRIPT = EXP_ROOT / "tools" / "verify_m08_hm3d_rendered_rgbd_frame_staging.py"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"

CAMERA_HEIGHT_M = 1.5
HFOV_DEG = 90.0
DEPTH_SHIFT = 1000.0


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_detector_inputs() -> list[dict[str, Any]]:
    input_dir = DATA_OUT_DIR / "detector_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    copies = [
        ("real_proposal_query_manifest.jsonl", "real_proposal_query_manifest.jsonl"),
        ("real_proposal_object_targets.jsonl", "real_proposal_object_targets.jsonl"),
        ("prompt_set.json", "prompt_set.json"),
        ("proposal_output_schema.json", "proposal_output_schema.json"),
    ]
    rows = []
    for src_name, dst_name in copies:
        src = M07_ARTIFACT_DIR / src_name
        dst = input_dir / dst_name
        if src.exists():
            shutil.copyfile(src, dst)
        rows.append(
            {
                "source": str(src),
                "target": str(dst),
                "ready": dst.exists() and dst.stat().st_size > 0,
            }
        )
    return rows


def render_script() -> str:
    return r'''
import json
import math
from pathlib import Path

import habitat_sim
import magnum as mn
import numpy as np
import quaternion
from PIL import Image

ROT_RO_CAM = np.diag([1.0, -1.0, -1.0]).astype(np.float64)
SCENE_DATASET_CONFIG = "__SCENE_DATASET_CONFIG__"
CAMERA_HEIGHT_M = __CAMERA_HEIGHT_M__
HFOV_DEG = __HFOV_DEG__
DEPTH_SHIFT = __DEPTH_SHIFT__


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def quaternion_from_xyzw(values):
    x, y, z, w = [float(value) for value in values]
    return quaternion.quaternion(w, x, y, z)


def quaternion_xyzw(q):
    return [float(q.x), float(q.y), float(q.z), float(q.w)]


def pose_matrix(base_position, base_rotation):
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = np.asarray(quaternion.as_rotation_matrix(base_rotation), dtype=np.float64) @ ROT_RO_CAM
    matrix[:3, 3] = np.asarray(base_position, dtype=np.float64)
    matrix[1, 3] += CAMERA_HEIGHT_M
    return matrix


def write_pose_matrix(path, matrix):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [" ".join(f"{float(value):.9f}" for value in row) for row in matrix]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def intrinsics(width, height, hfov_deg):
    fx = float(width) / (2.0 * math.tan(math.radians(float(hfov_deg)) / 2.0))
    fy = fx
    cx = float(width) / 2.0
    cy = float(height) / 2.0
    return fx, fy, cx, cy


def write_info(path, width, height, frame_count):
    fx, fy, cx, cy = intrinsics(width, height, HFOV_DEG)
    intrinsic = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    intrinsic_text = " ".join(f"{value:.9f}" for value in intrinsic)
    identity = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
    text = "\n".join(
        [
            "m_versionNumber = 4",
            "m_sensorName = habitat_sim_rgbd_render",
            f"m_colorWidth = {int(width)}",
            f"m_colorHeight = {int(height)}",
            f"m_depthWidth = {int(width)}",
            f"m_depthHeight = {int(height)}",
            f"m_depthShift = {DEPTH_SHIFT:.1f}",
            f"m_calibrationColorIntrinsic = {intrinsic_text} ",
            f"m_calibrationColorExtrinsic = {identity} ",
            f"m_calibrationDepthIntrinsic = {intrinsic_text} ",
            f"m_calibrationDepthExtrinsic = {identity} ",
            f"m_frames.size = {int(frame_count)}",
            "",
        ]
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_pgm_u16(path, depth_m):
    depth = np.asarray(depth_m, dtype=np.float32)
    depth = np.nan_to_num(depth, nan=0.0, posinf=0.0, neginf=0.0)
    depth_mm = np.clip(np.rint(depth * DEPTH_SHIFT), 0, 65535).astype(">u2")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(f"P5\n{depth_mm.shape[1]} {depth_mm.shape[0]}\n65535\n".encode("ascii"))
        handle.write(depth_mm.tobytes())


def make_sim(scene_path, navmesh_path, width, height):
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(scene_path)
    sim_cfg.scene_dataset_config_file = SCENE_DATASET_CONFIG
    sim_cfg.enable_physics = False

    color = habitat_sim.CameraSensorSpec()
    color.uuid = "color"
    color.sensor_type = habitat_sim.SensorType.COLOR
    color.resolution = [int(height), int(width)]
    color.position = mn.Vector3(0.0, CAMERA_HEIGHT_M, 0.0)
    color.hfov = HFOV_DEG

    depth = habitat_sim.CameraSensorSpec()
    depth.uuid = "depth"
    depth.sensor_type = habitat_sim.SensorType.DEPTH
    depth.resolution = [int(height), int(width)]
    depth.position = mn.Vector3(0.0, CAMERA_HEIGHT_M, 0.0)
    depth.hfov = HFOV_DEG

    agent_cfg = habitat_sim.agent.AgentConfiguration()
    agent_cfg.sensor_specifications = [color, depth]
    sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))
    if not sim.pathfinder.is_loaded:
        sim.pathfinder.load_nav_mesh(str(navmesh_path))
    if not sim.pathfinder.is_loaded:
        sim.close()
        raise RuntimeError(f"navmesh not loaded: {navmesh_path}")
    return sim


def main():
    render_rows = load_jsonl("/inputs/render_plan_rows.jsonl")
    out_root = Path("/out")
    output_rows = []
    errors = []
    sim = None
    active_scene = None
    agent = None
    frame_counts = {}
    for row in render_rows:
        frame_counts[str(row["scan_id"])] = frame_counts.get(str(row["scan_id"]), 0) + 1

    try:
        for row in render_rows:
            scene = str(row["hm3d_scene_docker_path"])
            navmesh = str(row["hm3d_navmesh_docker_path"])
            width = int(row["render_width"])
            height = int(row["render_height"])
            if active_scene != scene:
                if sim is not None:
                    sim.close()
                sim = make_sim(scene, navmesh, width, height)
                agent = sim.initialize_agent(0)
                active_scene = scene

            assert sim is not None and agent is not None
            base_position = np.asarray(row["source_position"], dtype=np.float64)
            base_rotation = quaternion_from_xyzw(row["source_rotation"])
            yaw_delta = quaternion.from_rotation_vector(np.array([0.0, math.radians(float(row["yaw_offset_deg"])), 0.0], dtype=np.float64))
            rotation = yaw_delta * base_rotation

            state = habitat_sim.AgentState()
            state.position = base_position.astype(np.float32)
            state.rotation = rotation
            agent.set_state(state, reset_sensors=True)
            obs = sim.get_sensor_observations()

            rgb = np.asarray(obs["color"])
            if rgb.ndim == 3 and rgb.shape[-1] == 4:
                rgb = rgb[:, :, :3]
            rgb = np.asarray(rgb, dtype=np.uint8)
            depth = np.asarray(obs["depth"], dtype=np.float32)
            if depth.ndim == 3:
                depth = depth[:, :, 0]

            color_path = out_root / Path(str(row["expected_color"])).relative_to("__DATA_OUT_DIR__")
            depth_path = out_root / Path(str(row["expected_depth"])).relative_to("__DATA_OUT_DIR__")
            pose_path = out_root / Path(str(row["expected_pose"])).relative_to("__DATA_OUT_DIR__")
            sequence_dir = color_path.parent
            sequence_dir.mkdir(parents=True, exist_ok=True)
            write_info(sequence_dir / "_info.txt", width, height, frame_counts[str(row["scan_id"])])

            Image.fromarray(rgb).save(color_path, quality=92)
            write_pgm_u16(depth_path, depth)
            camera_pose = pose_matrix(base_position, rotation)
            write_pose_matrix(pose_path, camera_pose)

            positive_depth = int(np.count_nonzero(np.asarray(depth) > 0))
            output_rows.append(
                {
                    "adapter_episode_id": row["adapter_episode_id"],
                    "color_path": str(color_path),
                    "depth_max_m": float(np.max(depth)) if depth.size else None,
                    "depth_mean_m": float(np.mean(depth)) if depth.size else None,
                    "depth_path": str(depth_path),
                    "depth_positive_pixels": positive_depth,
                    "frame_id": row["frame_id"],
                    "pose_path": str(pose_path),
                    "render_height": height,
                    "render_width": width,
                    "rotation_xyzw": quaternion_xyzw(rotation),
                    "scan_id": row["scan_id"],
                    "scene_key": row["scene_key"],
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "yaw_offset_deg": row["yaw_offset_deg"],
                }
            )
    except Exception as exc:
        errors.append({"error": repr(exc), "active_scene": active_scene})
        raise
    finally:
        if sim is not None:
            sim.close()

    write_jsonl(out_root / "rendered_frame_rows.jsonl", output_rows)
    summary = {
        "errors": errors,
        "frame_rows": len(output_rows),
        "ok": len(output_rows) == len(render_rows) and not errors,
        "scan_count": len(frame_counts),
        "uses_objectnav_eval_goal": False,
        "uses_objectnav_eval_viewpoint": False,
    }
    (out_root / "render_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
'''.replace("__SCENE_DATASET_CONFIG__", SCENE_DATASET_CONFIG).replace(
        "__CAMERA_HEIGHT_M__", str(CAMERA_HEIGHT_M)
    ).replace(
        "__HFOV_DEG__", str(HFOV_DEG)
    ).replace(
        "__DEPTH_SHIFT__", str(DEPTH_SHIFT)
    ).replace(
        "__DATA_OUT_DIR__", str(DATA_OUT_DIR)
    )


def run_docker_renderer() -> dict[str, Any]:
    render_input_dir = DATA_OUT_DIR / "render_inputs"
    render_input_dir.mkdir(parents=True, exist_ok=True)
    render_plan_rows = read_jsonl(M07_ARTIFACT_DIR / "render_plan_rows.jsonl")
    write_jsonl(render_input_dir / "render_plan_rows.jsonl", render_plan_rows)
    command = [
        "docker",
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
        "micromamba run -n base python /inputs/render_m08.py",
    ]
    (render_input_dir / "render_m08.py").write_text(render_script(), encoding="utf-8")
    result = subprocess.run(command, check=False, text=True, capture_output=True, timeout=600)
    return {
        "command": " ".join(command[:12]) + " ...",
        "returncode": result.returncode,
        "ok": result.returncode == 0,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
        "render_plan_rows": len(render_plan_rows),
    }


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "hm3d_rendered_rgbd_detector_candidate_smoke",
            "selected": ready,
            "decision": "selected_next" if ready else "blocked_until_frame_staging_ready",
            "next_unit": "E008-M09 HM3D rendered RGB-D detector candidate smoke",
            "launch_long_job_now": False,
            "reason": "Detector inference can start only after RGB-D frames, pose matrices, _info.txt, and detector input files are staged.",
        },
        {
            "rank": 2,
            "route_id": "hm3d_h001_navigation_execution",
            "selected": False,
            "decision": "defer",
            "next_unit": "later E008 candidate snapping and policy execution",
            "launch_long_job_now": False,
            "reason": "H001 execution requires detector/external-map candidate coordinates and snap-to-navmesh validation.",
        },
    ]


def build_report(coverage: dict[str, Any], route_rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M08 HM3D Rendered RGB-D Frame Staging Smoke",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
            f"- Rendered frame rows: {coverage['rendered_frame_rows']}.",
            f"- Ready frame rows: {coverage['ready_frame_rows']}.",
            f"- Ready scan rows: {coverage['ready_scan_rows']} / {coverage['scan_rows']}.",
            f"- Detector input files ready: {str(coverage['detector_input_files_ready']).lower()}.",
            f"- Docker render returncode: {coverage['docker_returncode']}.",
            f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.",
            f"- Final real RGB-D/open-vocabulary robustness ready: {str(coverage['real_rgbd_open_vocab_robustness_ready']).lower()}.",
            "",
            "## Route Decision",
            "",
            "| rank | route_id | decision | next_unit |",
            "| --- | --- | --- | --- |",
            *[
                f"| {row['rank']} | {row['route_id']} | {row['decision']} | {row['next_unit']} |"
                for row in route_rows
            ],
            "",
            "## Claim Boundary",
            "",
            "- E008-M08 is frame staging and detector-input validation only.",
            "- E008-M08 does not run detector inference, H001 navigation execution, or real navigation `SR` / `SPL`.",
            "- Coordinate-frame and snap-to-navmesh validation remain required before any policy execution claim.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    m07 = read_json(M07_ARTIFACT_DIR / "coverage.json")
    if m07.get("status") != "e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan_ready":
        raise RuntimeError(f"M07 not ready: {m07.get('status')}")

    input_copy_rows = copy_detector_inputs()
    docker_meta = run_docker_renderer()
    write_json(ARTIFACT_DIR / "docker_render_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "detector_input_copy_rows.jsonl", input_copy_rows)

    verify_result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        check=False,
        text=True,
        capture_output=True,
    )
    verification = read_json(ARTIFACT_DIR / "verification_coverage.json")
    rendered_frame_rows = read_jsonl(DATA_OUT_DIR / "rendered_frame_rows.jsonl")
    ready = docker_meta["ok"] and verify_result.returncode == 0 and verification.get("status") == "e008_m08_hm3d_rendered_rgbd_frame_staging_verified"
    route_rows = build_route_rows(ready)
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_ready"
        if ready
        else "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_failed",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m07_status": m07.get("status"),
        "docker_returncode": docker_meta["returncode"],
        "docker_render_ok": docker_meta["ok"],
        "verification_returncode": verify_result.returncode,
        "verification_status": verification.get("status"),
        "render_plan_rows": docker_meta["render_plan_rows"],
        "rendered_frame_rows": len(rendered_frame_rows),
        "ready_frame_rows": verification.get("ready_frame_rows", 0),
        "scan_rows": verification.get("scan_rows", 0),
        "ready_scan_rows": verification.get("ready_scan_rows", 0),
        "detector_input_files_ready": verification.get("detector_input_files_ready", False),
        "detector_manifest_rows": verification.get("detector_manifest_rows", 0),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M09 HM3D rendered RGB-D detector candidate smoke"
        if ready
        else "repair E008-M08 frame staging",
    }
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, route_rows))
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"] == "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
