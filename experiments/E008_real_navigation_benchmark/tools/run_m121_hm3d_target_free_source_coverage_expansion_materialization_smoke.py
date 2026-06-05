#!/usr/bin/env python3
"""Materialize E008-M121 target-free source-coverage expansion rows."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M120_DIR = EXP_ROOT / "artifacts" / "E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)

VERSION = "e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
READY_STATUS = "e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready"
READY_WARNING_STATUS = (
    "e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready_with_snap_warnings"
)
BLOCKED_STATUS = "e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_blocked"
NEXT_UNIT = "E008-M122 HM3D target-free source-coverage render/detector launcher contract"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
SCENE_DATASET_CONFIG = (
    "/data/versioned_data/hm3d-0.2/hm3d/minival/"
    "hm3d_annotated_minival_basis.scene_dataset_config.json"
)

YAW_OFFSETS = [0, 45, 90, 135, 180, 225, 270, 315]
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


def dist(a: list[float], b: list[float]) -> float:
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def route_sample_plan(route_id: str) -> tuple[str, list[tuple[float, float]]]:
    if route_id == "target_free_navigable_coverage_sweep_v0":
        radii = [2.0, 4.0, 6.0]
        bearings = [float(index * 45) for index in range(8)]
        family = "target_free_start_radial_coverage_sweep"
    elif route_id == "target_free_path_prefix_diversity_sweep_v0":
        radii = [3.0, 5.0]
        bearings = [22.5 + float(index * 45) for index in range(8)]
        family = "target_free_start_path_prefix_diversity_proxy"
    else:
        return "unsupported_route", []
    return family, [(radius, bearing) for radius in radii for bearing in bearings]


def planned_position(start: list[float], radius_m: float, bearing_deg: float) -> list[float]:
    angle = math.radians(bearing_deg)
    return [
        float(start[0]) + radius_m * math.sin(angle),
        float(start[1]),
        float(start[2]) + radius_m * math.cos(angle),
    ]


def build_observation_pose_rows(
    case_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    case_by_episode = {str(row.get("adapter_episode_id")): row for row in case_rows}
    rows: list[dict[str, Any]] = []
    for contract in sorted(contract_rows, key=lambda row: str(row.get("route_id"))):
        case = case_by_episode.get(str(contract.get("adapter_episode_id")), {})
        start = case.get("start_position")
        rotation = case.get("start_rotation")
        route_id = str(contract.get("route_id"))
        pose_family, samples = route_sample_plan(route_id)
        if not finite_vec(start) or not finite_vec(rotation, 4):
            continue
        for index, (radius, bearing) in enumerate(samples):
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "target_free_observation_pose",
                    "adapter_episode_id": contract.get("adapter_episode_id"),
                    "scan_id": contract.get("scan_id"),
                    "scene_key": contract.get("scene_key"),
                    "object_category": contract.get("object_category"),
                    "route_id": route_id,
                    "observation_pose_id": f"{contract.get('adapter_episode_id')}:m121:{route_id}:pose-{index:03d}",
                    "observation_pose_index": index,
                    "pose_family": pose_family,
                    "pose_role": "target_free_source_coverage_pose",
                    "planned_position_m": planned_position([float(value) for value in start], radius, bearing),
                    "source_position_m": planned_position([float(value) for value in start], radius, bearing),
                    "source_rotation_xyzw": rotation,
                    "planned_rotation_xyzw": rotation,
                    "start_position_m": start,
                    "shell_radius_m": radius,
                    "bearing_relative_deg": bearing,
                    "hm3d_scene_docker_path": case.get("scene_docker_path"),
                    "hm3d_navmesh_docker_path": case.get("navmesh_docker_path"),
                    "resolved_scene_path": case.get("resolved_scene_path"),
                    "resolved_navmesh_path": case.get("resolved_navmesh_path"),
                    "policy_input_allowed": True,
                    "requires_navmesh_snap_validation": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_target_object_id_or_success_label": False,
                    "source_placement_input_basis": "HM3D scene/navmesh/start pose and route id only",
                    "claim_boundary": (
                        "This row is a target-free source pose candidate. ObjectNav target/viewpoint fields are "
                        "not used for source placement."
                    ),
                }
            )
    return rows


def parse_json_stdout(stdout: str) -> Any:
    for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
        if line.startswith("[") or line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON object found in docker stdout")


def run_habitat_snap_validation(input_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    code = f"""
import json
import math
from pathlib import Path

import habitat_sim

rows = [json.loads(line) for line in Path({json.dumps('/work/' + str(input_path.relative_to(ROOT)))}).read_text().splitlines() if line.strip()]

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
    scene_path = row.get("hm3d_scene_docker_path")
    if scene_path:
        by_scene.setdefault(str(scene_path), []).append(row)

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
            planned = row.get("planned_position_m")
            start = row.get("start_position_m")
            out["pathfinder_loaded"] = bool(sim.pathfinder.is_loaded)
            out["planned_position_valid"] = finite_vec(planned)
            out["start_position_valid"] = finite_vec(start)
            out["planned_source_navigable"] = bool(sim.pathfinder.is_navigable(planned)) if finite_vec(planned) else False
            if finite_vec(planned):
                snapped = sim.pathfinder.snap_point(planned)
                snapped_list = as_float_list(snapped)
            else:
                snapped_list = None
            out["snapped_position_m"] = snapped_list
            out["snapped_position_valid"] = finite_vec(snapped_list)
            out["snapped_navigable"] = bool(sim.pathfinder.is_navigable(snapped_list)) if finite_vec(snapped_list) else False
            out["snap_distance_m"] = dist(planned, snapped_list) if finite_vec(planned) and finite_vec(snapped_list) else None
            out["start_to_planned_euclidean_m"] = dist(start, planned) if finite_vec(start) and finite_vec(planned) else None
            out["start_to_snapped_euclidean_m"] = dist(start, snapped_list) if finite_vec(start) and finite_vec(snapped_list) else None
            path = find_path(sim, start, snapped_list) if finite_vec(start) and finite_vec(snapped_list) else {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": "missing_start_or_snapped"}}
            out["start_to_snapped_path_found"] = path["path_found"]
            out["start_to_snapped_geodesic_m"] = path["geodesic_distance"]
            out["start_to_snapped_path_point_count"] = path["point_count"]
            out["start_to_snapped_path_error"] = path["error"]
            out["render_position_m"] = snapped_list if finite_vec(snapped_list) else planned
            out["snap_validation_ready"] = bool(out["pathfinder_loaded"] and out["snapped_navigable"] and out["start_to_snapped_path_found"])
            out["snap_warning_large_move"] = bool(out["snap_distance_m"] is not None and float(out["snap_distance_m"]) > 2.0)
            result_rows.append(out)
    except Exception as exc:
        for row in scene_rows:
            out = dict(row)
            seen.add(row.get("observation_pose_id"))
            out["pathfinder_loaded"] = False
            out["scene_error"] = repr(exc)
            out["snap_validation_ready"] = False
            result_rows.append(out)
    finally:
        if sim is not None:
            sim.close()

for row in rows:
    if row.get("observation_pose_id") not in seen:
        out = dict(row)
        out["pathfinder_loaded"] = False
        out["snap_validation_ready"] = False
        out["skip_reason"] = "missing_scene_path"
        result_rows.append(out)

print(json.dumps(result_rows, sort_keys=True))
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{RESEARCH3_DATA_ROOT}:/data:ro",
        "-v",
        f"{ROOT}:/work:ro",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python - <<'PY'\n" + code + "\nPY",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=180)
    meta = {
        "command": " ".join(cmd[:10]) + " ...",
        "mounts": [f"{RESEARCH3_DATA_ROOT}:/data:ro", f"{ROOT}:/work:ro"],
        "ok": proc.returncode == 0,
        "requested_observation_pose_rows": sum(1 for _ in input_path.open("r", encoding="utf-8")),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-1000:],
        "stdout_tail": proc.stdout[-1000:],
    }
    if proc.returncode != 0:
        return [], meta
    try:
        return parse_json_stdout(proc.stdout), meta
    except Exception as exc:
        meta["ok"] = False
        meta["parse_error"] = str(exc)
        return [], meta


def build_render_plan_rows(snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frame_index = 0
    for pose in sorted(
        snap_rows,
        key=lambda row: (str(row.get("route_id")), int(row.get("observation_pose_index") or 0)),
    ):
        for yaw in YAW_OFFSETS:
            frame_id = f"frame-{frame_index:06d}"
            sequence = DATA_OUT_DIR / "3RScan" / "scans" / str(pose.get("scan_id")) / "sequence"
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "target_free_render_plan",
                    "adapter_episode_id": pose.get("adapter_episode_id"),
                    "scan_id": pose.get("scan_id"),
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
                    "render_source": "e008_m121_target_free_source_coverage_expansion",
                    "render_width": RENDER_WIDTH,
                    "render_height": RENDER_HEIGHT,
                    "hm3d_scene_docker_path": pose.get("hm3d_scene_docker_path"),
                    "hm3d_navmesh_docker_path": pose.get("hm3d_navmesh_docker_path"),
                    "planned_source_position": pose.get("planned_position_m"),
                    "source_position": pose.get("render_position_m"),
                    "source_position_source": "E008-M121 snap_validation render_position_m",
                    "source_rotation": pose.get("source_rotation_xyzw"),
                    "source_rotation_xyzw": pose.get("source_rotation_xyzw"),
                    "yaw_offset_deg": yaw,
                    "requires_navmesh_snap_validation": False,
                    "source_snap_distance_m": pose.get("snap_distance_m"),
                    "source_snap_validation_ready": pose.get("snap_validation_ready"),
                    "source_start_to_snapped_geodesic_m": pose.get("start_to_snapped_geodesic_m"),
                    "policy_input_allowed": True,
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "expected_color": str(sequence / f"{frame_id}.color.jpg"),
                    "expected_depth": str(sequence / f"{frame_id}.depth.pgm"),
                    "expected_pose": str(sequence / f"{frame_id}.pose.txt"),
                }
            )
            frame_index += 1
    return rows


def detector_label_text(label: str) -> str:
    if label:
        return f"a {label}"
    return label


def build_detector_manifest_rows(
    contract_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    render_by_route = Counter(str(row.get("route_id")) for row in render_rows)
    pose_by_route: dict[str, set[str]] = defaultdict(set)
    for row in render_rows:
        pose_by_route[str(row.get("route_id"))].add(str(row.get("observation_pose_id")))
    rows: list[dict[str, Any]] = []
    for contract in sorted(contract_rows, key=lambda row: str(row.get("route_id"))):
        label = str(contract.get("object_category"))
        route_id = str(contract.get("route_id"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "target_free_detector_manifest",
                "adapter_episode_id": contract.get("adapter_episode_id"),
                "scan_id": contract.get("scan_id"),
                "scene_key": contract.get("scene_key"),
                "object_category": label,
                "route_id": route_id,
                "observation_pose_rows": len(pose_by_route.get(route_id, set())),
                "render_plan_rows": render_by_route.get(route_id, 0),
                "render_plan_jsonl": str(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl"),
                "target_free_observation_pose_jsonl": str(DATA_OUT_DIR / "target_free_observation_pose_rows.jsonl"),
                "snap_validation_jsonl": str(DATA_OUT_DIR / "target_free_snap_validation_rows.jsonl"),
                "prompt_labels": [label],
                "prompts": [detector_label_text(label), label, f"the {label}"],
                "detector_prompt_uses_object_category": True,
                "source_placement_uses_object_category": False,
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                "claim_boundary": (
                    "Detector prompt may use the query category after target-free source poses are frozen; "
                    "source placement does not use ObjectNav target coordinates."
                ),
            }
        )
    return rows


def build_prompt_set(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted({str(row.get("object_category")) for row in manifest_rows if row.get("object_category")})
    return {
        "version": VERSION,
        "prompt_rows": [
            {
                "label_canonical": label,
                "prompts": [detector_label_text(label), label, f"the {label}"],
                "prompt_role": "detector_target",
                "detector_prompt_enabled": True,
            }
            for label in labels
        ],
    }


def target_leakage_present(rows: list[dict[str, Any]]) -> bool:
    forbidden_truthy_keys = [
        "uses_objectnav_eval_goal",
        "uses_objectnav_eval_viewpoint",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy",
        "uses_objectnav_eval_goal_or_viewpoint_for_source_placement",
        "uses_target_object_id_or_success_label",
    ]
    return any(any(bool(row.get(key)) for key in forbidden_truthy_keys) for row in rows)


def build_m122_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": (
                "Observation pose rows, snap validation rows, render plan rows, and detector manifest rows "
                "match the M120 contract with no ObjectNav target/viewpoint source-placement leakage."
            ),
            "observed": coverage["m122_launcher_contract_ready"],
            "next_action": "Write M122 launcher contract and only then launch render/detector as a background job if needed.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M121 materializes rows but snap readiness is partial or route diversity is low.",
            "observed": coverage["status"] == READY_WARNING_STATUS,
            "next_action": "Keep rows as diagnostic and avoid recovery claims until render/detector verifies source recovery.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M121 uses target/viewpoint fields, success labels, target object id, or posthoc target distance to place sources.",
            "observed": coverage["uses_objectnav_target_for_source_placement"],
            "next_action": "Do not launch render/detector; redesign target-free source expansion.",
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_target_free_source_materialization",
            "supported": True,
            "claim_boundary": "M121 supports target-free source pose and render/detector manifest materialization only.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M121 does not render frames, run detector/mapping inference, or show sofa recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M121 does not execute Habitat trajectories and cannot support real navigation SR/SPL.",
        },
    ]


def build_reviewer_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Did target-free source placement use ObjectNav goal/viewpoint leakage?",
            "answer": (
                "No. M121 source poses are start-centered route samples validated against navmesh; target/viewpoint "
                "fields remain blocked for source placement."
            ),
            "evidence": {
                "uses_objectnav_target_for_source_placement": coverage["uses_objectnav_target_for_source_placement"],
                "allowed_blocked_audit_pass": coverage["allowed_blocked_audit_pass"],
            },
        },
        {
            "version": VERSION,
            "question": "Does M121 prove ConceptGraphs or detector recovery?",
            "answer": "No. It only writes render/detector-ready rows. Recovery needs M122+ render/detector and leakage-safe goal evaluation.",
        },
        {
            "version": VERSION,
            "question": "Why not promote to trajectory execution now?",
            "answer": "There are no detector candidates or visit-order/path rows from the target-free frames yet.",
        },
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M121 HM3D Target-Free Source-Coverage Expansion Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Input M120 status: `{coverage['m120_status']}`.",
            f"- Source-coverage case rows: {coverage['source_coverage_case_rows']}.",
            f"- M120 materialization contract rows: {coverage['m120_materialization_contract_rows']}.",
            f"- Observation pose rows: {coverage['observation_pose_rows']}.",
            f"- Snap validation rows: {coverage['snap_validation_rows']}.",
            f"- Snap-ready rows: {coverage['snap_ready_rows']}.",
            f"- Unique snapped XZ cells: {coverage['unique_snapped_xz_cells']}.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
            f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
            f"- Uses ObjectNav target/viewpoint for source placement: {coverage['uses_objectnav_target_for_source_placement']}.",
            f"- Launch long job now: {coverage['launch_long_job_now']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M121 materializes target-free source poses and render/detector launcher inputs only.",
            "- M121 does not render RGB-D frames, run open-vocabulary detector/mapping inference, recover the remaining sofa case, execute trajectories, or support real navigation `SR` / `SPL`.",
            "- M122 must convert these rows into a long-job launcher contract before any render/detector run.",
            "",
        ]
    )


def copy_outputs(file_names: list[str]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_OUT_DIR / "render_inputs").mkdir(parents=True, exist_ok=True)
    (DATA_OUT_DIR / "detector_inputs").mkdir(parents=True, exist_ok=True)
    for name in file_names:
        src = ARTIFACT_DIR / name
        dst = DATA_OUT_DIR / name
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    shutil.copy2(ARTIFACT_DIR / "target_free_render_plan_rows.jsonl", DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl")
    shutil.copy2(
        ARTIFACT_DIR / "target_free_detector_manifest_rows.jsonl",
        DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl",
    )
    shutil.copy2(ARTIFACT_DIR / "target_free_prompt_set.json", DATA_OUT_DIR / "detector_inputs" / "prompt_set.json")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m120 = read_json(M120_DIR / "coverage.json")
    case_rows = read_jsonl(M120_DIR / "target_free_source_coverage_case_rows.jsonl")
    contract_rows = read_jsonl(M120_DIR / "m121_materialization_contract_rows.jsonl")
    allowed_blocked_rows = read_jsonl(M120_DIR / "allowed_blocked_input_rows.jsonl")
    observation_rows = build_observation_pose_rows(case_rows, contract_rows)

    snap_input_path = ARTIFACT_DIR / "target_free_snap_input_rows.jsonl"
    write_jsonl(snap_input_path, observation_rows)
    snap_rows, docker_meta = run_habitat_snap_validation(snap_input_path)
    if not snap_rows and observation_rows:
        snap_rows = [
            {
                **row,
                "pathfinder_loaded": False,
                "snap_validation_ready": False,
                "skip_reason": "docker_snap_validation_failed",
            }
            for row in observation_rows
        ]

    render_rows = build_render_plan_rows(snap_rows)
    detector_manifest_rows = build_detector_manifest_rows(contract_rows, render_rows)
    prompt_set = build_prompt_set(detector_manifest_rows)
    allowed_blocked_rows = [
        {**row, "source_version": row.get("version"), "version": VERSION, "row_type": "m121_allowed_blocked_input"}
        for row in allowed_blocked_rows
    ]

    expected_observation_rows = sum(int(row.get("m121_expected_observation_pose_rows") or 0) for row in contract_rows)
    expected_render_rows = sum(int(row.get("m121_expected_render_plan_rows") or 0) for row in contract_rows)
    snap_ready = sum(1 for row in snap_rows if row.get("snap_validation_ready"))
    route_ready_count = sum(
        1
        for route_id in sorted({str(row.get("route_id")) for row in observation_rows})
        if any(row.get("snap_validation_ready") for row in snap_rows if str(row.get("route_id")) == route_id)
    )
    unique_snapped_xz_cells = {
        (round(float(row["render_position_m"][0]), 1), round(float(row["render_position_m"][2]), 1))
        for row in snap_rows
        if finite_vec(row.get("render_position_m"))
    }
    leakage_rows = [*observation_rows, *snap_rows, *render_rows, *detector_manifest_rows]
    uses_target_for_source = target_leakage_present(leakage_rows)
    allowed_blocked_pass = all(row.get("audit_status") == "pass" for row in allowed_blocked_rows)
    materialization_ready = (
        m120.get("status") == "e008_m120_hm3d_target_free_source_coverage_expansion_contract_ready"
        and len(case_rows) > 0
        and len(contract_rows) > 0
        and len(observation_rows) == expected_observation_rows
        and len(snap_rows) == len(observation_rows)
        and len(render_rows) == expected_render_rows
        and len(detector_manifest_rows) == len(contract_rows)
        and not uses_target_for_source
        and allowed_blocked_pass
    )
    strict_snap_ready = snap_ready == len(snap_rows) and snap_ready > 0
    snap_ready_with_warnings = snap_ready >= min(24, len(snap_rows)) and route_ready_count == len(contract_rows)
    m122_ready = materialization_ready and (strict_snap_ready or snap_ready_with_warnings)
    if materialization_ready and strict_snap_ready:
        status = READY_STATUS
    elif materialization_ready and snap_ready_with_warnings:
        status = READY_WARNING_STATUS
    else:
        status = BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m120_status": m120.get("status"),
        "source_coverage_case_rows": len(case_rows),
        "m120_materialization_contract_rows": len(contract_rows),
        "expected_observation_pose_rows": expected_observation_rows,
        "expected_render_plan_rows": expected_render_rows,
        "observation_pose_rows": len(observation_rows),
        "snap_validation_rows": len(snap_rows),
        "snap_ready_rows": snap_ready,
        "snap_ready_route_rows": route_ready_count,
        "large_snap_warning_rows": sum(1 for row in snap_rows if row.get("snap_warning_large_move")),
        "unique_snapped_xz_cells": len(unique_snapped_xz_cells),
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(detector_manifest_rows),
        "allowed_blocked_input_rows": len(allowed_blocked_rows),
        "allowed_blocked_audit_pass": allowed_blocked_pass,
        "uses_objectnav_target_for_source_placement": uses_target_for_source,
        "docker_snap_validation_ok": docker_meta.get("ok"),
        "docker_returncode": docker_meta.get("returncode"),
        "materialization_ready": materialization_ready,
        "strict_snap_validation_ready": strict_snap_ready,
        "m122_launcher_contract_ready": m122_ready,
        "launch_long_job_now": False,
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if m122_ready else "repair E008-M121 target-free source materialization",
    }
    m122_gate_rows = build_m122_gate_rows(coverage)
    claim_rows = build_claim_rows()
    reviewer_rows = build_reviewer_rows(coverage)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_snap_validation_meta.json", docker_meta)
    write_json(ARTIFACT_DIR / "target_free_prompt_set.json", prompt_set)
    write_jsonl(ARTIFACT_DIR / "target_free_observation_pose_rows.jsonl", observation_rows)
    write_jsonl(ARTIFACT_DIR / "target_free_snap_validation_rows.jsonl", snap_rows)
    write_jsonl(ARTIFACT_DIR / "target_free_render_plan_rows.jsonl", render_rows)
    write_jsonl(ARTIFACT_DIR / "target_free_detector_manifest_rows.jsonl", detector_manifest_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_blocked_input_rows.jsonl", allowed_blocked_rows)
    write_jsonl(ARTIFACT_DIR / "m122_gate_rows.jsonl", m122_gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))

    copy_outputs(
        [
            "coverage.json",
            "docker_snap_validation_meta.json",
            "target_free_prompt_set.json",
            "target_free_observation_pose_rows.jsonl",
            "target_free_snap_validation_rows.jsonl",
            "target_free_render_plan_rows.jsonl",
            "target_free_detector_manifest_rows.jsonl",
            "allowed_blocked_input_rows.jsonl",
            "m122_gate_rows.jsonl",
            "claim_boundary_rows.jsonl",
            "reviewer_defense_rows.jsonl",
            "report.md",
        ]
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
