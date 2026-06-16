#!/usr/bin/env python3
"""Plan the E008-M122 target-free source-coverage render/detector launcher contract."""

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
M16_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py"
M66_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m66_full_val_mini_render_frame_staging.py"
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"

M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M121_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)
M121_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0"
)
M123_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M123_target_free_source_coverage_render_frame_staging_launch_v0"
)
M124_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M124_target_free_source_coverage_detector_candidate_source_v0"
)

VERSION = "e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_v0"
READY_STATUS = "e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_ready"
READY_WARNING_STATUS = (
    "e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_ready_with_snap_warnings"
)
BLOCKED_STATUS = "e008_m122_hm3d_target_free_source_coverage_render_detector_launcher_contract_blocked"
NEXT_UNIT = "E008-M123 HM3D target-free source-coverage render frame staging background launch"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
REAL_SMOKE_IMAGE = "research2/real-smoke:latest"
SCENE_DATASET_CONFIG = (
    "/data/versioned_data/hm3d-0.2/hm3d/minival/"
    "hm3d_annotated_minival_basis.scene_dataset_config.json"
)
LOG_DIR = ROOT / "logs"
RENDER_TMUX_SESSION = "e008_m123_target_free_render"
DETECTOR_TMUX_SESSION = "e008_m124_target_free_detector"


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


def command_status(command: list[str], timeout: int = 20) -> dict[str, Any]:
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
    direct = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    sudo_n = command_status(["sudo", "-n", "docker", "info", "--format", "{{.ServerVersion}}"])
    if direct["available"]:
        return {"available": True, "mode": "direct", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo_n}
    if sudo_n["available"]:
        return {"available": True, "mode": "sudo_n", "selected_prefix": ["sudo", "-n", "docker"], "direct": direct, "sudo_n": sudo_n}
    return {"available": False, "mode": "unavailable", "selected_prefix": ["docker"], "direct": direct, "sudo_n": sudo_n}


def image_status(prefix: list[str], image: str) -> dict[str, Any]:
    if not prefix:
        return {"available": False, "command": [], "returncode": None, "stderr": "docker unavailable", "stdout": ""}
    return command_status([*prefix, "image", "inspect", image, "--format", "{{.Id}}"])


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


def load_m15_render_tool() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m15_render_tool", M15_RENDER_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 render tool: {M15_RENDER_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_script_for_m122() -> str:
    module = load_m15_render_tool()
    module.DATA_OUT_DIR = M121_DATA_DIR
    module.SCENE_DATASET_CONFIG = SCENE_DATASET_CONFIG
    return module.render_script()


def copy_with_version(rows: list[dict[str, Any]], row_type: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        next_row = dict(row)
        next_row["source_version"] = next_row.get("version")
        next_row["version"] = VERSION
        next_row["row_type"] = row_type
        out.append(next_row)
    return out


def route_frame_indices(render_rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row.get("route_id"))].append(int(row.get("frame_index") or 0))
    return {key: sorted(values) for key, values in grouped.items()}


def build_object_target_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for manifest in manifest_rows:
        scan_id = str(manifest.get("scan_id"))
        label = str(manifest.get("object_category"))
        key = (scan_id, label)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "version": VERSION,
                "row_type": "target_free_detector_object_target",
                "adapter_episode_id": manifest.get("adapter_episode_id"),
                "detector_prompt_enabled": True,
                "evaluation_target_enabled": False,
                "hm3d_objectnav_category": label,
                "label_canonical": label,
                "label_text": label,
                "object_category": label,
                "policy_input_allowed": True,
                "prompt_set_id": "e008_m122_target_free_detector_prompts_v0",
                "scan_id": scan_id,
                "scene_key": manifest.get("scene_key"),
                "source": "E008-M122 HM3D ObjectNav category text only after source rows are frozen",
                "target_uid": f"e008-m122:{scan_id}:{label}",
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
        "prompt_set_id": "e008_m122_target_free_detector_prompts_v0",
        "prompt_policy": "M122 uses query category text only after target-free source rows are frozen; ObjectNav goal/viewpoint fields are blocked.",
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


def build_detector_manifest_rows(
    raw_manifest_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    object_target_path: Path,
    prompt_set_path: Path,
    schema_path: Path,
) -> list[dict[str, Any]]:
    indices_by_route = route_frame_indices(render_rows)
    rows: list[dict[str, Any]] = []
    for manifest in sorted(raw_manifest_rows, key=lambda row: str(row.get("route_id"))):
        route_id = str(manifest.get("route_id"))
        indices = indices_by_route.get(route_id, [])
        scan_id = str(manifest.get("scan_id"))
        label = str(manifest.get("object_category"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "target_free_detector_manifest",
                "adapter_episode_id": manifest.get("adapter_episode_id"),
                "batch_id": "e008_m122_target_free_source_coverage",
                "detector_config_id": "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0",
                "detector_target_count": 1,
                "evaluation_target_count": 0,
                "frame_id_format": "frame-{index:06d}",
                "frame_sampling_strategy": "m121_target_free_source_coverage_multiview",
                "max_frames": len(indices),
                "object_category": label,
                "object_target_path": str(object_target_path),
                "paper_table_role": "target_free_source_coverage_materialization_not_result",
                "policy_input_allowed": True,
                "prompt_set_id": "e008_m122_target_free_detector_prompts_v0",
                "prompt_set_path": str(prompt_set_path),
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": str(schema_path),
                "route_id": route_id,
                "route_ids": [route_id],
                "sampled_frame_count": len(indices),
                "sampled_frame_indices": indices,
                "scan_id": scan_id,
                "scene_key": manifest.get("scene_key"),
                "sequence_dir_compat_path": str(M121_DATA_DIR / "3RScan" / "scans" / scan_id / "sequence"),
                "target_label_count": 1,
                "target_labels": [label],
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                "claim_boundary": (
                    "Detector prompt uses object category only after M121 target-free source poses are frozen; "
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
        sequence = M121_DATA_DIR / "3RScan" / "scans" / scan_id / "sequence"
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
    render_input_dir = M121_DATA_DIR / "render_inputs"
    detector_input_dir = M121_DATA_DIR / "detector_inputs"
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
                "data_bearing_root": str(M121_DATA_DIR),
            }
        )

    render_script = render_input_dir / "render_m122_target_free.py"
    write_text(render_script, render_script_for_m122())
    rows.append(
        {
            "version": VERSION,
            "row_type": "launcher_input_materialization",
            "file_role": "render_script",
            "path": str(render_script),
            "rows": None,
            "ready": render_script.exists() and render_script.stat().st_size > 0,
            "data_bearing_root": str(M121_DATA_DIR),
        }
    )
    return rows


def build_long_job_command_rows(docker: dict[str, Any], detector_manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    render_log = LOG_DIR / f"{timestamp}_e008_m123_target_free_render.log"
    detector_log = LOG_DIR / f"{timestamp}_e008_m124_target_free_detector.log"
    render_input_dir = M121_DATA_DIR / "render_inputs"
    detector_input_dir = M121_DATA_DIR / "detector_inputs"
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
        f"{M121_DATA_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m122_target_free.py",
    ]
    render_shell = f"cd {shlex.quote(str(ROOT))} && {shell_join(docker_render)} > {shlex.quote(str(render_log))} 2>&1"
    render_tmux = f"mkdir -p {shlex.quote(str(LOG_DIR))} && tmux new-session -d -s {shlex.quote(RENDER_TMUX_SESSION)} {shlex.quote(render_shell)}"

    detector_command = [
        "python",
        str(E003_RUNNER),
        "--dataset-root",
        str(M121_DATA_DIR),
        "--m17-dir",
        str(detector_input_dir),
        "--out-dir",
        str(M124_ARTIFACT_DIR),
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
            "job_id": "E008-M123",
            "job_status": "contract_recorded_not_launched",
            "job_type": "target_free_source_coverage_render_frame_staging",
            "working_directory": str(ROOT),
            "tmux_session": RENDER_TMUX_SESSION,
            "command": render_tmux,
            "inner_command": render_shell,
            "output_path": str(M121_DATA_DIR),
            "log_path": str(render_log),
            "expected_files": [
                "rendered_frame_rows.jsonl",
                "snap_validation_rows.jsonl",
                "render_summary.json",
                "3RScan/scans/<scan_id>/sequence/frame-*.color.jpg",
                "3RScan/scans/<scan_id>/sequence/frame-*.depth.pgm",
                "3RScan/scans/<scan_id>/sequence/frame-*.pose.txt",
            ],
            "verification_command": (
                f"python {M66_VERIFY_TOOL.relative_to(ROOT)} "
                f"--artifact-dir {M123_ARTIFACT_DIR} --data-out-dir {M121_DATA_DIR} --require-ready"
            ),
            "launch_now": False,
            "next_if_verified": "E008-M124 target-free source-coverage detector candidate-source background launch",
        },
        {
            "version": VERSION,
            "row_type": "long_job_command",
            "job_id": "E008-M124",
            "job_status": "deferred_until_m123_render_verification",
            "job_type": "target_free_source_coverage_open_vocabulary_detector",
            "working_directory": str(ROOT),
            "tmux_session": DETECTOR_TMUX_SESSION,
            "command": detector_tmux,
            "inner_command": detector_shell,
            "output_path": str(M124_ARTIFACT_DIR),
            "log_path": str(detector_log),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
            ],
            "verification_command": (
                f"python {M16_VERIFY_TOOL.relative_to(ROOT)} "
                f"--m15-artifact-dir {M123_ARTIFACT_DIR} "
                f"--m15-data-dir {M121_DATA_DIR} "
                f"--m16-dir {M124_ARTIFACT_DIR} "
                f"--tmux-session {DETECTOR_TMUX_SESSION} --require-ready"
            ),
            "launch_now": False,
            "next_if_verified": "E008-M125 target-free detector candidate navmesh/source-readiness validation",
        },
    ]


def build_readiness_gate_rows(
    m121: dict[str, Any],
    render_rows: list[dict[str, Any]],
    detector_manifest_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    docker: dict[str, Any],
) -> list[dict[str, Any]]:
    prefix = docker.get("selected_prefix") or ["docker"]
    habitat_image = image_status(prefix, HABITAT_IMAGE) if docker.get("available") else {"available": False}
    real_smoke_image = image_status(prefix, REAL_SMOKE_IMAGE) if docker.get("available") else {"available": False}
    snap_ready = int(m121.get("snap_ready_rows") or 0)
    snap_rows = int(m121.get("snap_validation_rows") or 0)
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m121_materialization_ready",
            "gate_status": "pass" if m121.get("m122_launcher_contract_ready") else "fail",
            "blocks_m122": True,
            "details": m121.get("status"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "target_free_render_rows_ready",
            "gate_status": "pass" if len(render_rows) == 320 else "fail",
            "blocks_m122": True,
            "details": len(render_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "target_free_detector_manifest_ready",
            "gate_status": "pass" if len(detector_manifest_rows) == 2 else "fail",
            "blocks_m122": True,
            "details": len(detector_manifest_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "launcher_inputs_written",
            "gate_status": "pass" if input_rows and all(row.get("ready") for row in input_rows) else "fail",
            "blocks_m122": True,
            "details": Counter(str(row.get("ready")) for row in input_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "target_viewpoint_source_placement_leakage_absent",
            "gate_status": "pass" if not m121.get("uses_objectnav_target_for_source_placement") else "fail",
            "blocks_m122": True,
            "details": m121.get("uses_objectnav_target_for_source_placement"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m121_snap_warning_visible",
            "gate_status": "warning" if snap_ready < snap_rows else "pass",
            "blocks_m122": False,
            "details": {"snap_ready_rows": snap_ready, "snap_validation_rows": snap_rows},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "external_hm3d_data_readonly_source_ready",
            "gate_status": "pass" if RESEARCH2_DATA_ROOT.exists() else "fail",
            "blocks_m123": True,
            "details": str(RESEARCH2_DATA_ROOT),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "docker_available",
            "gate_status": "pass" if docker.get("available") else "warning",
            "blocks_m123": True,
            "details": docker.get("mode"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat_image.get("available") else "warning",
            "blocks_m123": True,
            "details": HABITAT_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_smoke_image.get("available") else "warning",
            "blocks_m124": True,
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "tmux_sessions_free",
            "gate_status": "pass" if not tmux_running(RENDER_TMUX_SESSION) and not tmux_running(DETECTOR_TMUX_SESSION) else "warning",
            "blocks_m123": True,
            "details": [RENDER_TMUX_SESSION, DETECTOR_TMUX_SESSION],
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "no_long_job_launched_in_m122",
            "gate_status": "pass",
            "blocks_m122": False,
            "details": "M122 writes launcher contract and input files only.",
        },
    ]


def build_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M123 renders 320 target-free RGB-D/pose frames and M124 produces detector candidates with valid coordinates without target/viewpoint policy leakage.",
            "next_action": "Validate candidate navmesh/source-readiness in E008-M125.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M123/M124 completes but target-free source frames remain a visibility negative or snap-warning rows dominate detector output.",
            "next_action": "Keep as source-coverage diagnostic; do not claim source-gap recovery.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "Render/detector command uses ObjectNav target/viewpoint, target object id, candidate-target distance, or success label.",
            "next_action": "Do not launch trajectory or policy evaluation; redesign launcher inputs.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "target_free_render_detector_launcher_contract",
            "support_status": "supported_with_snap_warning",
            "allowed_claim": "M122 makes M121 target-free source rows render/detector launcher-ready and records exact long-job and verification commands.",
            "blocked_claims": [
                "target-free source expansion recovers the sofa source-gap case",
                "detector target recall improves",
                "real navigation SR/SPL improves",
                "final RGB-D/open-vocabulary robustness is solved",
                "human intent is a main contribution",
            ],
        }
    ]


def build_reviewer_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Does M122 leak ObjectNav goal/viewpoint information into source placement or detector ranking?",
            "answer": "No. Source poses were frozen in M121 from start/navmesh route sampling, and M122 detector inputs use only the object category text for prompts.",
        },
        {
            "version": VERSION,
            "question": "Why is M122 not source-gap recovery evidence?",
            "answer": "M122 only writes command and input contracts. Recovery requires M123 rendered frames, M124 detector candidates, M125 navmesh validation, and leakage-safe goal evaluation.",
        },
        {
            "version": VERSION,
            "question": "How are M121 snap warnings handled?",
            "answer": "M122 preserves snap-warning counts in readiness gates and does not upgrade them to navigation or recovery claims.",
        },
    ]


def build_route_decision_rows(status: str) -> list[dict[str, Any]]:
    ready = status in {READY_STATUS, READY_WARNING_STATUS}
    return [
        {
            "version": VERSION,
            "decision": "m122_launcher_contract_ready_select_m123" if ready else "m122_launcher_contract_blocked",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M122 launcher contract",
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "render_launch_ready_next": ready,
            "detector_launch_ready_now": False,
            "trajectory_promotion_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "reason": (
                "M122 wrote target-free render inputs, detector manifest/targets/prompt/schema, long-job command ledger, and verification commands."
                if ready
                else "M122 has blocking readiness gates."
            ),
        }
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M122 HM3D Target-Free Source-Coverage Render/Detector Launcher Contract",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M121 status: `{coverage['m121_status']}`.",
            f"- Render plan rows: {coverage['target_free_render_rows']}.",
            f"- Detector manifest rows: {coverage['target_free_detector_manifest_rows']}.",
            f"- Object target rows: {coverage['object_target_rows']}.",
            f"- Launcher input rows: {coverage['launcher_input_materialization_rows']}.",
            f"- Long-job command rows: {coverage['long_job_command_rows']}.",
            f"- M121 snap-ready rows: {coverage['m121_snap_ready_rows']} / {coverage['m121_snap_validation_rows']}.",
            f"- Uses ObjectNav target/viewpoint for source placement: {coverage['uses_objectnav_target_for_source_placement']}.",
            f"- Launch long job now: {coverage['launch_long_job_now']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M122 is a launcher contract only.",
            "- M122 does not render RGB-D frames, run detector inference, recover source-gap rows, execute trajectories, or support final real navigation `SR` / `SPL`.",
            "- M121 snap warnings remain visible and must be carried into M123/M124/M125 accounting.",
            "",
        ]
    )


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    M121_DATA_DIR.mkdir(parents=True, exist_ok=True)

    m121 = read_json(M121_ARTIFACT_DIR / "coverage.json")
    raw_render_rows = read_jsonl(M121_ARTIFACT_DIR / "target_free_render_plan_rows.jsonl")
    raw_manifest_rows = read_jsonl(M121_ARTIFACT_DIR / "target_free_detector_manifest_rows.jsonl")
    render_rows = copy_with_version(raw_render_rows, "target_free_render_plan")
    object_target_rows = build_object_target_rows(raw_manifest_rows)
    prompt_payload = build_prompt_set(object_target_rows)
    schema_payload = proposal_output_schema()
    detector_manifest_rows = build_detector_manifest_rows(
        raw_manifest_rows,
        render_rows,
        M121_DATA_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl",
        M121_DATA_DIR / "detector_inputs" / "prompt_set.json",
        M121_DATA_DIR / "detector_inputs" / "proposal_output_schema.json",
    )
    expected_rows = expected_file_summary_rows(render_rows)
    input_rows = write_launcher_inputs(
        render_rows=render_rows,
        detector_manifest_rows=detector_manifest_rows,
        object_target_rows=object_target_rows,
        prompt_payload=prompt_payload,
        schema_payload=schema_payload,
    )
    docker = docker_status()
    readiness_rows = build_readiness_gate_rows(m121, render_rows, detector_manifest_rows, input_rows, docker)
    command_rows = build_long_job_command_rows(docker, detector_manifest_rows)
    m123_gate_rows = build_gate_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_rows()

    blockers = [row["gate_id"] for row in readiness_rows if row.get("blocks_m122") and row.get("gate_status") == "fail"]
    warning_count = sum(1 for row in readiness_rows if row.get("gate_status") == "warning")
    if blockers:
        status = BLOCKED_STATUS
    elif warning_count:
        status = READY_WARNING_STATUS
    else:
        status = READY_STATUS
    route_rows = build_route_decision_rows(status)
    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "next_unit": NEXT_UNIT if status in {READY_STATUS, READY_WARNING_STATUS} else "repair E008-M122 launcher contract",
            "action": "Launch the recorded E008-M123 target-free render tmux job only after user asks for the next TODO.",
            "launch_long_job_now": False,
        }
    ]

    outputs: dict[str, Any] = {
        "target_free_render_plan_rows.jsonl": render_rows,
        "target_free_detector_manifest_rows.jsonl": detector_manifest_rows,
        "target_free_object_target_rows.jsonl": object_target_rows,
        "expected_file_summary_rows.jsonl": expected_rows,
        "launcher_input_materialization_rows.jsonl": input_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "long_job_command_rows.jsonl": command_rows,
        "m123_gate_rows.jsonl": m123_gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_action_rows,
    }
    output_paths: list[Path] = []
    for name, payload in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, payload)
        output_paths.append(path)
    write_json(ARTIFACT_DIR / "target_free_prompt_set.json", prompt_payload)
    write_json(ARTIFACT_DIR / "target_free_proposal_output_schema.json", schema_payload)
    output_paths.extend([ARTIFACT_DIR / "target_free_prompt_set.json", ARTIFACT_DIR / "target_free_proposal_output_schema.json"])

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "data_bearing_output_root": str(M121_DATA_DIR),
        "m121_status": m121.get("status"),
        "m121_snap_ready_rows": m121.get("snap_ready_rows"),
        "m121_snap_validation_rows": m121.get("snap_validation_rows"),
        "target_free_render_rows": len(render_rows),
        "target_free_detector_manifest_rows": len(detector_manifest_rows),
        "object_target_rows": len(object_target_rows),
        "expected_file_summary_rows": len(expected_rows),
        "launcher_input_materialization_rows": len(input_rows),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if row.get("gate_status") == "fail"),
        "readiness_gate_warning_rows": warning_count,
        "m122_blockers": blockers,
        "long_job_command_rows": len(command_rows),
        "render_input_dir": str(M121_DATA_DIR / "render_inputs"),
        "detector_input_dir": str(M121_DATA_DIR / "detector_inputs"),
        "render_script_ready": (M121_DATA_DIR / "render_inputs" / "render_m122_target_free.py").exists(),
        "detector_query_manifest_ready": (M121_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl").exists(),
        "render_launch_ready_next": status in {READY_STATUS, READY_WARNING_STATUS},
        "detector_launch_ready_now": False,
        "launch_long_job_now": False,
        "long_job_launched": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "uses_objectnav_target_for_source_placement": bool(m121.get("uses_objectnav_target_for_source_placement")),
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if status in {READY_STATUS, READY_WARNING_STATUS} else "repair E008-M122 launcher contract",
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    output_paths.extend([ARTIFACT_DIR / "coverage.json", ARTIFACT_DIR / "report.md"])
    mirror_outputs(output_paths)

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if status == BLOCKED_STATUS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
