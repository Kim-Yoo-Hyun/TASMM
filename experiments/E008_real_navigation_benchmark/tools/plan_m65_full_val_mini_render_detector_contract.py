#!/usr/bin/env python3
"""Plan the E008-M65 full-val-mini render and detector candidate-source contract."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M65_full_val_mini_render_detector_contract_v0"
M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M64_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M07_DIR = EXP_ROOT / "artifacts" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
M15_RENDER_TOOL = EXP_ROOT / "tools" / "run_m15_non_oracle_observation_expansion_frame_staging.py"
M66_VERIFY_TOOL = EXP_ROOT / "tools" / "verify_m66_full_val_mini_render_frame_staging.py"
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
M67_DIR = EXP_ROOT / "artifacts" / "E008-M67_full_val_mini_detector_candidate_source_v0"

VERSION = "e008_m65_full_val_mini_render_detector_contract_v0"
READY_STATUS = "e008_m65_full_val_mini_render_detector_contract_ready"
BLOCKED_STATUS = "e008_m65_full_val_mini_render_detector_contract_blocked"
NEXT_UNIT = "E008-M66 full-val-mini render frame staging background launch"
DETECTOR_NEXT_UNIT = "E008-M67 full-val-mini detector candidate-source background launch"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
REAL_SMOKE_IMAGE = "research2/real-smoke:latest"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
LOG_DIR = ROOT / "logs"
RENDER_TMUX_SESSION = "e008_m66_full_val_mini_render"
DETECTOR_TMUX_SESSION = "e008_m67_full_val_mini_detector"
FRAME_INDICES = list(range(36))


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
    command = [*prefix, "image", "inspect", image, "--format", "{{.Id}}"]
    return command_status(command)


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in command)


def m15_render_script_for_m65() -> str:
    spec = importlib.util.spec_from_file_location("e008_m15_render_tool", M15_RENDER_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 render tool: {M15_RENDER_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DATA_OUT_DIR = DATA_OUT_DIR
    module.SCENE_DATASET_CONFIG = SCENE_DATASET_CONFIG
    return module.render_script()


def render_sequence_dir(scan_id: str) -> Path:
    return DATA_OUT_DIR / "3RScan" / "scans" / scan_id / "sequence"


def rewrite_render_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for row in rows:
        scan_id = str(row["scan_id"])
        frame_id = str(row["frame_id"])
        sequence_dir = render_sequence_dir(scan_id)
        patched = dict(row)
        patched.update(
            {
                "version": VERSION,
                "source_version": row.get("version"),
                "m65_contract_id": VERSION,
                "expected_color": str(sequence_dir / f"{frame_id}.color.jpg"),
                "expected_depth": str(sequence_dir / f"{frame_id}.depth.pgm"),
                "expected_pose": str(sequence_dir / f"{frame_id}.pose.txt"),
                "position_status": "planned_unvalidated_until_m66_render",
                "render_source": "full_val_mini_non_oracle_start_neighborhood_multiview_m65_contract",
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            }
        )
        rewritten.append(patched)
    return rewritten


def build_detector_manifest(
    source_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    detector_input_dir: Path,
) -> list[dict[str, Any]]:
    frame_indices_by_scan: dict[str, list[int]] = defaultdict(list)
    for row in render_rows:
        frame_indices_by_scan[str(row["scan_id"])].append(int(row["frame_index"]))

    manifest_rows: list[dict[str, Any]] = []
    for row in source_rows:
        scan_id = str(row["scan_id"])
        target_labels = [str(label) for label in row.get("target_labels", []) if str(label)]
        frame_indices = sorted(set(frame_indices_by_scan.get(scan_id, [])))
        patched = dict(row)
        patched.update(
            {
                "version": VERSION,
                "source_version": row.get("version"),
                "m65_contract_id": VERSION,
                "batch_id": "e008_m65_full_val_mini_candidate_source_contract",
                "detector_config_id": "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0",
                "detector_target_count": len(target_labels),
                "evaluation_target_count": 0,
                "frame_id_format": "frame-{index:06d}",
                "max_frames": len(frame_indices),
                "object_target_path": str(detector_input_dir / "real_proposal_object_targets.jsonl"),
                "prompt_set_path": str(detector_input_dir / "prompt_set.json"),
                "proposal_output_schema_path": str(detector_input_dir / "proposal_output_schema.json"),
                "sampled_frame_count": len(frame_indices),
                "sampled_frame_indices": frame_indices,
                "sequence_dir_compat_path": str(render_sequence_dir(scan_id)),
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            }
        )
        manifest_rows.append(patched)
    return manifest_rows


def build_object_target_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        for label in manifest.get("target_labels", []):
            label = str(label)
            rows.append(
                {
                    "version": VERSION,
                    "source": "E008-M64 HM3D ObjectNav category only",
                    "target_uid": f"e008-m65:{manifest['scan_id']}:{label}",
                    "adapter_episode_id": manifest.get("adapter_episode_id"),
                    "detector_prompt_enabled": True,
                    "evaluation_target_enabled": False,
                    "hm3d_objectnav_category": manifest.get("object_category"),
                    "label_canonical": label,
                    "label_text": label,
                    "object_category": manifest.get("object_category"),
                    "policy_input_allowed": True,
                    "prompt_set_id": manifest.get("prompt_set_id"),
                    "route_id": manifest.get("route_id"),
                    "scan_id": manifest.get("scan_id"),
                    "scene_key": manifest.get("scene_key"),
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                }
            )
    return rows


def expected_file_summary_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row["scan_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for scan_id, items in sorted(grouped.items()):
        sequence_dir = render_sequence_dir(scan_id)
        rows.append(
            {
                "scan_id": scan_id,
                "sequence_dir": str(sequence_dir),
                "expected_color_frames": len(items),
                "expected_depth_frames": len(items),
                "expected_pose_frames": len(items),
                "expected_info_files": 1,
                "expected_total_files": len(items) * 3 + 1,
            }
        )
    return rows


def host_path_from_docker_path(docker_path: str) -> Path:
    value = Path(docker_path)
    if not str(value).startswith("/data/"):
        return value
    return RESEARCH2_DATA_ROOT / value.relative_to("/data")


def build_preflight_rows(render_rows: list[dict[str, Any]], detector_manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m64 = read_json(M64_DIR / "coverage.json")
    scene_paths = sorted({str(row["hm3d_scene_docker_path"]) for row in render_rows})
    navmesh_paths = sorted({str(row["hm3d_navmesh_docker_path"]) for row in render_rows})
    docker = docker_status()
    prefix = docker["selected_prefix"]
    habitat = image_status(prefix, HABITAT_IMAGE) if docker["available"] else {"available": False}
    real_smoke = image_status(prefix, REAL_SMOKE_IMAGE) if docker["available"] else {"available": False}
    rows = [
        {
            "gate_id": "m64_ready",
            "gate_status": "pass" if m64.get("status") == "e008_m64_full_val_mini_high_path_scale_materialization_ready" else "fail",
            "blocks_m65": True,
            "blocks_m66": True,
            "details": m64.get("status"),
        },
        {
            "gate_id": "render_plan_rows_match_contract",
            "gate_status": "pass" if len(render_rows) == 1080 else "fail",
            "blocks_m65": True,
            "blocks_m66": True,
            "details": len(render_rows),
        },
        {
            "gate_id": "detector_manifest_rows_match_contract",
            "gate_status": "pass" if len(detector_manifest_rows) == 30 else "fail",
            "blocks_m65": True,
            "blocks_m66": False,
            "details": len(detector_manifest_rows),
        },
        {
            "gate_id": "sampled_frame_indices_ready",
            "gate_status": "pass"
            if all(row.get("sampled_frame_indices") == FRAME_INDICES for row in detector_manifest_rows)
            else "fail",
            "blocks_m65": True,
            "blocks_m66": False,
            "details": "36 frame indices per scan",
        },
        {
            "gate_id": "scene_files_host_ready",
            "gate_status": "pass" if all(host_path_from_docker_path(path).exists() for path in scene_paths) else "fail",
            "blocks_m65": True,
            "blocks_m66": True,
            "details": f"{len(scene_paths)} unique scene files",
        },
        {
            "gate_id": "navmesh_files_host_ready",
            "gate_status": "pass" if all(host_path_from_docker_path(path).exists() for path in navmesh_paths) else "fail",
            "blocks_m65": True,
            "blocks_m66": True,
            "details": f"{len(navmesh_paths)} unique navmesh files",
        },
        {
            "gate_id": "docker_available",
            "gate_status": "pass" if docker["available"] else "warning",
            "blocks_m65": False,
            "blocks_m66": True,
            "details": docker["mode"],
        },
        {
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat.get("available") else "warning",
            "blocks_m65": False,
            "blocks_m66": True,
            "details": HABITAT_IMAGE,
        },
        {
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_smoke.get("available") else "warning",
            "blocks_m65": False,
            "blocks_m67": True,
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "gate_id": "render_frames_ready",
            "gate_status": "future",
            "blocks_m65": False,
            "blocks_m66": False,
            "blocks_final_navigation_claim": True,
            "details": "M66 launches/produces rendered frames; M65 only records the contract.",
        },
        {
            "gate_id": "detector_candidate_rows_ready",
            "gate_status": "future",
            "blocks_m65": False,
            "blocks_m67": False,
            "blocks_final_navigation_claim": True,
            "details": "M67 launches/produces open-vocabulary detector candidates after M66 verification.",
        },
    ]
    return rows


def build_command_rows(docker_prefix: list[str]) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    render_log = LOG_DIR / f"{timestamp}_e008_m66_full_val_mini_render.log"
    detector_log = LOG_DIR / f"{timestamp}_e008_m67_full_val_mini_detector.log"
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
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "-v",
        f"{render_input_dir}:/inputs:ro",
        "-v",
        f"{DATA_OUT_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m65.py",
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
        str(M67_DIR),
        "--max-scans",
        "30",
        "--max-frames-per-scan",
        "36",
        "--max-labels",
        "8",
        "--max-predictions",
        "60000",
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
        "300000",
        "--export-pre-cap-candidate-pool",
    ]
    detector_shell = f"cd {shlex.quote(str(ROOT))} && {shell_join(detector_command)} > {shlex.quote(str(detector_log))} 2>&1"
    detector_tmux = f"mkdir -p {shlex.quote(str(LOG_DIR))} && tmux new-session -d -s {shlex.quote(DETECTOR_TMUX_SESSION)} {shlex.quote(detector_shell)}"
    return [
        {
            "job_id": "E008-M66",
            "job_status": "contract_recorded_not_launched",
            "job_type": "full_val_mini_render_frame_staging",
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
            "expected_file_count": 30 * (36 * 3 + 1) + 3,
            "verification_command": f"python {M66_VERIFY_TOOL.relative_to(ROOT)} --require-ready",
            "next_if_verified": DETECTOR_NEXT_UNIT,
        },
        {
            "job_id": "E008-M67",
            "job_status": "contract_recorded_not_launched",
            "job_type": "full_val_mini_open_vocabulary_detector_candidate_source",
            "working_directory": str(ROOT),
            "tmux_session": DETECTOR_TMUX_SESSION,
            "command": detector_tmux,
            "inner_command": detector_shell,
            "output_path": str(M67_DIR),
            "log_path": str(detector_log),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
                "matching/coverage.json",
            ],
            "verification_command": (
                "python experiments/E008_real_navigation_benchmark/tools/"
                "verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py "
                f"--m15-artifact-dir {ARTIFACT_DIR} "
                f"--m15-data-dir {DATA_OUT_DIR} "
                f"--m16-dir {M67_DIR} "
                f"--tmux-session {DETECTOR_TMUX_SESSION} --require-ready"
            ),
            "launch_after": "E008-M66 verification ready",
        },
    ]


def build_route_rows(m65_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "route_id": "m66_render_background_launch_next",
            "selected": m65_ready,
            "selected_next_unit": NEXT_UNIT if m65_ready else "repair E008-M65 contract",
            "launch_long_job_now": False,
            "reason": "M65 records the command/input contract only; M66 should launch rendering in tmux.",
        },
        {
            "route_id": "m67_detector_launch_after_render",
            "selected": False,
            "selected_next_unit": DETECTOR_NEXT_UNIT,
            "launch_long_job_now": False,
            "reason": "Detector inference depends on verified rendered RGB-D frames.",
        },
        {
            "route_id": "full_val_mini_trajectory_execution_now",
            "selected": False,
            "selected_next_unit": "NA",
            "launch_long_job_now": False,
            "reason": "Trajectory execution requires detector candidates, navmesh validation, and visit-order materialization.",
        },
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


def build_report(coverage: dict[str, Any], gate_rows: list[dict[str, Any]], command_rows: list[dict[str, Any]]) -> str:
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
    return "\n".join(
        [
            "# E008-M65 Full-Val-Mini Render Detector Contract",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M64 status: `{coverage['m64_status']}`.",
            f"- Render plan rows: {coverage['render_plan_rows']}.",
            f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
            f"- Detector object target rows: {coverage['detector_object_target_rows']}.",
            f"- Prompt label count: {coverage['prompt_label_count']}.",
            f"- Expected render frame files: {coverage['expected_render_frame_files']}.",
            f"- Long job launched: {coverage['long_job_launched']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Readiness Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m65", "blocks_m66", "blocks_m67", "blocks_final_navigation_claim"]),
            "",
            "## Long-Job Commands",
            "",
            markdown_table(command_summary, ["job_id", "job_status", "tmux_session", "output_path", "log_path"]),
            "",
            "## 논문 주장",
            "",
            "- M65 supports only the reproducibility contract for full `val_mini` rendering and detector candidate-source generation.",
            "- M65 does not support real navigation `SR` / `SPL`, deployable search policy, or final RGB-D/open-vocabulary robustness.",
            "",
            "## 에이전트 추론",
            "",
            "- M66 should launch rendering first because detector inference requires verified RGB-D frames and pose files.",
            "- M67 detector inference should not start until M66 verification passes on all 1,080 planned frames.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. The next operational step is the M66 background render launch if GPU/Docker are available.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    m64_coverage = read_json(M64_DIR / "coverage.json")
    source_render_rows = read_jsonl(M64_DIR / "render_plan_rows.jsonl")
    source_manifest_rows = read_jsonl(M64_DIR / "detector_manifest_rows.jsonl")
    prompt_set = read_json(M64_DIR / "prompt_set.json")

    render_rows = rewrite_render_rows(source_render_rows)
    detector_input_dir = DATA_OUT_DIR / "detector_inputs"
    render_input_dir = DATA_OUT_DIR / "render_inputs"
    detector_manifest_rows = build_detector_manifest(source_manifest_rows, render_rows, detector_input_dir)
    target_rows = build_object_target_rows(detector_manifest_rows)
    expected_rows = expected_file_summary_rows(render_rows)

    write_jsonl(render_input_dir / "render_plan_rows.jsonl", render_rows)
    write_text(render_input_dir / "render_m65.py", m15_render_script_for_m65())
    write_jsonl(detector_input_dir / "real_proposal_query_manifest.jsonl", detector_manifest_rows)
    write_jsonl(detector_input_dir / "real_proposal_object_targets.jsonl", target_rows)
    write_json(detector_input_dir / "prompt_set.json", prompt_set)
    write_json(detector_input_dir / "proposal_output_schema.json", read_json(M07_DIR / "proposal_output_schema.json"))

    docker = docker_status()
    command_rows = build_command_rows(docker["selected_prefix"])
    gate_rows = build_preflight_rows(render_rows, detector_manifest_rows)
    m65_blockers = [row["gate_id"] for row in gate_rows if row.get("blocks_m65") and row.get("gate_status") == "fail"]
    route_rows = build_route_rows(not m65_blockers)
    category_counts = Counter(str(row.get("object_category")) for row in detector_manifest_rows)
    label_counts = Counter(str(row.get("label_canonical")) for row in target_rows)
    expected_render_frame_files = len(render_rows) * 3 + len({str(row["scan_id"]) for row in render_rows})
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if not m65_blockers else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m64_status": m64_coverage.get("status"),
        "m64_artifact_root": str(M64_DIR),
        "m64_derived_root": str(M64_DATA_DIR),
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(detector_manifest_rows),
        "detector_object_target_rows": len(target_rows),
        "prompt_label_count": int(prompt_set.get("label_count", 0) or 0),
        "expected_file_summary_rows": len(expected_rows),
        "expected_render_frame_files": expected_render_frame_files,
        "category_counts": dict(sorted(category_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "m65_blockers": m65_blockers,
        "docker_status": docker,
        "long_job_launched": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "render_frames_ready": False,
        "detector_candidate_rows_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if not m65_blockers else "repair E008-M65 contract",
    }

    write_jsonl(ARTIFACT_DIR / "render_plan_rows.jsonl", render_rows)
    write_jsonl(ARTIFACT_DIR / "detector_manifest_rows.jsonl", detector_manifest_rows)
    write_jsonl(ARTIFACT_DIR / "detector_object_target_rows.jsonl", target_rows)
    write_json(ARTIFACT_DIR / "prompt_set.json", prompt_set)
    write_json(ARTIFACT_DIR / "proposal_output_schema.json", read_json(M07_DIR / "proposal_output_schema.json"))
    write_jsonl(ARTIFACT_DIR / "expected_file_summary_rows.jsonl", expected_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, gate_rows, command_rows))

    write_jsonl(DATA_OUT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(DATA_OUT_DIR / "long_job_command_rows.jsonl", command_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_text(DATA_OUT_DIR / "report.md", build_report(coverage, gate_rows, command_rows))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"] == READY_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
