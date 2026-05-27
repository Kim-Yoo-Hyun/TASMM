#!/usr/bin/env python3
"""Plan E008-M07 HM3D rendered RGB-D detector candidate source."""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
VERSION = "e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"

M02_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M06_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M06_hm3d_semantic_candidate_source_smoke_v0"
E003_SCHEMA = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
    / "proposal_output_schema.json"
)
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
E003_VALIDATOR = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "validate_real_proposal_output.py"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
REAL_PROPOSAL_IMAGE = "research2/real-smoke:latest"

M08_DATASET_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
M08_INPUT_DIR = M08_DATASET_ROOT / "detector_inputs"
M09_OUT_DIR = EXP_ROOT / "artifacts" / "E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0"

YAW_OFFSETS_DEG = [0, 90, 180, 270]
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
HF_CACHE = Path.home() / ".cache" / "huggingface"

CATEGORY_DETECTOR_LABELS = {
    "bed": ["bed"],
    "chair": ["chair"],
    "tv_monitor": ["tv", "television", "monitor"],
}


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


def docker_image_status(image: str) -> dict[str, Any]:
    result = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{.Id}} {{.Size}}"],
        check=False,
        text=True,
        capture_output=True,
    )
    stdout = result.stdout.strip()
    image_id = ""
    size_bytes = None
    if result.returncode == 0 and stdout:
        parts = stdout.split()
        image_id = parts[0]
        if len(parts) > 1:
            try:
                size_bytes = int(parts[1])
            except ValueError:
                size_bytes = None
    return {
        "image": image,
        "available": result.returncode == 0,
        "image_id": image_id,
        "size_bytes": size_bytes,
        "returncode": result.returncode,
        "stderr_tail": result.stderr.strip()[-500:],
    }


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def detector_labels_for_category(category: str) -> list[str]:
    return CATEGORY_DETECTOR_LABELS.get(category, [category.replace("_", " ")])


def build_prompt_set(episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels: dict[str, dict[str, Any]] = {}
    for row in episode_rows:
        category = str(row["object_category"])
        for label in detector_labels_for_category(category):
            item = labels.setdefault(
                label,
                {
                    "aliases": [],
                    "detector_prompt_enabled": True,
                    "hm3d_objectnav_categories": set(),
                    "label_canonical": label,
                    "object_count": 0,
                    "prompt_role": "detector_target",
                    "prompts": set(),
                    "scan_ids": set(),
                },
            )
            item["hm3d_objectnav_categories"].add(category)
            item["object_count"] += 1
            item["prompts"].update({label, f"a {label}", f"the {label}"})
            item["scan_ids"].add(episode_scan_id(row))

    out_labels = []
    for label, payload in sorted(labels.items()):
        out_labels.append(
            {
                "aliases": sorted(payload["aliases"]),
                "detector_prompt_enabled": payload["detector_prompt_enabled"],
                "hm3d_objectnav_categories": sorted(payload["hm3d_objectnav_categories"]),
                "label_canonical": label,
                "object_count": payload["object_count"],
                "prompt_role": payload["prompt_role"],
                "prompts": sorted(payload["prompts"]),
                "scan_count": len(payload["scan_ids"]),
                "scan_ids": sorted(payload["scan_ids"]),
            }
        )
    return {
        "batch_id": "e008_m07_tiny_start_pose_sweep",
        "detector_profile_id": "open_vocab_rgbd_detector_v0",
        "detector_target_label_count": len(out_labels),
        "label_count": len(out_labels),
        "labels": out_labels,
        "m07_version": VERSION,
        "prompt_policy": "ObjectNav category is mapped to detector-facing labels without exposing ObjectNav goal/viewpoint fields.",
        "prompt_set_id": "e008_m07_hm3d_objectnav_detector_prompts_v0",
        "source": "E008-M02 HM3D ObjectNav adapter rows",
    }


def episode_scan_id(row: dict[str, Any]) -> str:
    return f"hm3dnav_{safe_id(str(row['scene_key']))}_ep{safe_id(str(row['source_episode_id']))}"


def build_render_plan_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        scan_id = episode_scan_id(episode)
        for frame_index, yaw_offset in enumerate(YAW_OFFSETS_DEG):
            rows.append(
                {
                    "adapter_episode_id": episode["adapter_episode_id"],
                    "frame_id": f"frame-{frame_index:06d}",
                    "frame_index": frame_index,
                    "habitat_image": HABITAT_IMAGE,
                    "hm3d_scene_docker_path": episode["scene_docker_path"],
                    "hm3d_navmesh_docker_path": episode["navmesh_docker_path"],
                    "object_category": episode["object_category"],
                    "policy_input_allowed": True,
                    "render_source": "episode_start_pose_fixed_yaw_sweep",
                    "render_width": FRAME_WIDTH,
                    "render_height": FRAME_HEIGHT,
                    "scan_id": scan_id,
                    "scene_key": episode["scene_key"],
                    "source_position": episode["start_position"],
                    "source_rotation": episode["start_rotation"],
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                    "yaw_offset_deg": yaw_offset,
                    "expected_color": str(M08_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence" / f"frame-{frame_index:06d}.color.jpg"),
                    "expected_depth": str(M08_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence" / f"frame-{frame_index:06d}.depth.pgm"),
                    "expected_pose": str(M08_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence" / f"frame-{frame_index:06d}.pose.txt"),
                }
            )
    return rows


def build_manifest_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        scan_id = episode_scan_id(episode)
        detector_labels = detector_labels_for_category(str(episode["object_category"]))
        rows.append(
            {
                "adapter_episode_id": episode["adapter_episode_id"],
                "batch_id": "e008_m07_tiny_start_pose_sweep",
                "bridge_query_row_count": 1,
                "bridge_query_target_count": 1,
                "detector_config_id": "h001_hm3d_objectnav_groundingdino_tiny_rgbd_backproject_v0",
                "detector_profile_id": "open_vocab_rgbd_detector_v0",
                "detector_target_count": len(detector_labels),
                "evaluation_target_count": 0,
                "frame_id_format": "frame-%06d",
                "frame_sampling_strategy": "episode_start_pose_fixed_yaw_sweep",
                "max_frames": len(YAW_OFFSETS_DEG),
                "object_category": episode["object_category"],
                "object_target_path": "/inputs/real_proposal_object_targets.jsonl",
                "paper_table_role": "hm3d_navigation_candidate_source_input_not_final_result",
                "policy_input_allowed": True,
                "prompt_set_id": "e008_m07_hm3d_objectnav_detector_prompts_v0",
                "prompt_set_path": "/inputs/prompt_set.json",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": "/inputs/proposal_output_schema.json",
                "route_id": "hm3d_rendered_rgbd_detector_candidate_source",
                "sampled_frame_count": len(YAW_OFFSETS_DEG),
                "sampled_frame_indices": list(range(len(YAW_OFFSETS_DEG))),
                "scan_id": scan_id,
                "scene_key": episode["scene_key"],
                "sequence_dir_compat_path": str(M08_DATASET_ROOT / "3RScan" / "scans" / scan_id / "sequence"),
                "source_position": episode["start_position"],
                "source_rotation": episode["start_rotation"],
                "target_label_count": len(detector_labels),
                "target_labels": detector_labels,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
            }
        )
    return rows


def build_object_target_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        scan_id = episode_scan_id(episode)
        for label in detector_labels_for_category(str(episode["object_category"])):
            rows.append(
                {
                    "adapter_episode_id": episode["adapter_episode_id"],
                    "detector_prompt_enabled": True,
                    "evaluation_target_enabled": False,
                    "hm3d_objectnav_category": episode["object_category"],
                    "label_canonical": label,
                    "m07_version": VERSION,
                    "object_category": episode["object_category"],
                    "scan_id": scan_id,
                    "source": "E008-M02 HM3D ObjectNav category only",
                    "target_uid": f"e008-m07:{scan_id}:{safe_id(label)}",
                    "uses_objectnav_eval_goal": False,
                    "uses_objectnav_eval_viewpoint": False,
                }
            )
    return rows


def build_blocked_input_rows() -> list[dict[str, Any]]:
    blocked = [
        ("closest_goal_object_id", "ObjectNav target object id is evaluation-only leakage."),
        ("eval_goal_position", "ObjectNav goal position must not seed candidate locations."),
        ("eval_first_viewpoint_position", "ObjectNav viewpoint is an oracle navigation target."),
        ("goals_by_category", "Contains target positions and viewpoints."),
        ("geodesic_distance", "Shortest-path metric field; not a policy input."),
        ("euclidean_distance", "Evaluation diagnostic field; not a policy input."),
        ("success_label", "Post-execution label."),
        ("target_match_distance", "Post-hoc matching result."),
    ]
    allowed = [
        ("scene_id_raw", "Required to render the simulator scene."),
        ("start_position", "Allowed observation pose from the episode start."),
        ("start_rotation", "Allowed observation orientation from the episode start."),
        ("object_category", "The task category/query itself."),
        ("fixed_yaw_offsets", "Deterministic non-goal-conditioned observation sweep."),
        ("RGB-D render", "Generated from allowed start pose only."),
        ("detector confidence", "Allowed after detector inference because it is produced before navigation action."),
        ("candidate centroid_world_m", "Allowed if produced by RGB-D backprojection before policy execution."),
    ]
    rows = [
        {"field": field, "policy_input": "blocked", "reason": reason}
        for field, reason in blocked
    ]
    rows.extend({"field": field, "policy_input": "allowed", "reason": reason} for field, reason in allowed)
    return rows


def build_detector_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "hm3d_start_pose_rendered_rgbd_detector_candidates",
            "selected": True,
            "decision": "selected_next",
            "candidate_sources_unblocked": ["current_observation_candidates", "hm3d_rgbd_detector_candidates"],
            "requires_long_job": False,
            "next_unit": "E008-M08 HM3D rendered RGB-D frame staging smoke",
            "reason": "M06 semantic-coordinate route failed; rendered RGB-D creates deployable observation evidence without ObjectNav target leakage.",
        },
        {
            "rank": 2,
            "route_id": "objectnav_goal_viewpoint_candidate_source",
            "selected": False,
            "decision": "blocked_as_oracle_leakage",
            "candidate_sources_unblocked": [],
            "requires_long_job": False,
            "next_unit": "none",
            "reason": "Goal/viewpoint rows remain evaluation-only upper-bound data.",
        },
        {
            "rank": 3,
            "route_id": "hm3d_external_map_candidates_conceptgraphs_hovsg",
            "selected": False,
            "decision": "defer_until_detector_frame_source_ready",
            "candidate_sources_unblocked": ["external_map_candidates"],
            "requires_long_job": True,
            "next_unit": "later E008 external map baseline route",
            "reason": "External mapping can be added after a rendered observation stream and candidate schema are fixed.",
        },
    ]


def build_candidate_output_contract_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_uid", "string", True, True, "Unique id after detector candidate aggregation."),
        ("adapter_episode_id", "string", True, True, "Episode id linking candidate to ObjectNav execution row."),
        ("scan_id", "string", True, True, "Compatibility id for detector runner; one scan id per episode observation set."),
        ("scene_key", "string", True, True, "HM3D scene key."),
        ("candidate_source", "enum", True, True, "current_observation_detector / external_map / stale_memory."),
        ("candidate_label", "string", True, True, "Detector-facing label such as bed/chair/tv."),
        ("object_category", "string", True, True, "ObjectNav task category such as tv_monitor."),
        ("candidate_xyz", "float[3]", True, True, "Backprojected RGB-D candidate centroid in Habitat scene coordinates."),
        ("candidate_confidence", "float", False, True, "Detector confidence."),
        ("frame_ids", "string[]", False, True, "Rendered frames supporting the candidate."),
        ("candidate_rank", "int", True, True, "Policy visit order after H001 ranking."),
        ("path_cost_estimate_m", "float", False, True, "Navmesh path estimate, computed after candidate snapping."),
        ("eval_goal_position", "float[3]", False, False, "Blocked evaluation-only field."),
        ("success_label", "bool", False, False, "Post-execution/evaluation label."),
    ]
    return [
        {
            "field": field,
            "type": typ,
            "required": required,
            "policy_input_allowed": allowed,
            "description": description,
        }
        for field, typ, required, allowed, description in fields
    ]


def detector_command_plan(label_count: int, scan_count: int) -> dict[str, Any]:
    max_predictions = max(2000, scan_count * max(label_count, 1) * len(YAW_OFFSETS_DEG) * 100)
    command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--dataset-root",
        str(M08_DATASET_ROOT),
        "--m17-dir",
        str(M08_INPUT_DIR),
        "--out-dir",
        str(M09_OUT_DIR),
        "--max-scans",
        str(scan_count),
        "--max-frames-per-scan",
        str(len(YAW_OFFSETS_DEG)),
        "--max-labels",
        str(label_count),
        "--max-predictions",
        str(max_predictions),
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
        "50000",
        "--export-pre-cap-candidate-pool",
        "--docker-sudo",
        "--sudo-password-stdin",
    ]
    return {
        "command_id": "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_command_v0",
        "exact_command": command,
        "expected_files": [
            str(M09_OUT_DIR / "coverage.json"),
            str(M09_OUT_DIR / "container_output" / "real_proposals.jsonl"),
            str(M09_OUT_DIR / "validator" / "coverage.json"),
            str(M09_OUT_DIR / "matching" / "coverage.json"),
        ],
        "input_dir": str(M08_INPUT_DIR),
        "long_running_policy": "launch in tmux with timestamped log under logs/ when detector inference is run",
        "output_dir": str(M09_OUT_DIR),
        "shell_command": shlex.join(command),
        "tmux_session": "e008_m09_hm3d_rgbd_detector",
        "tmux_template": (
            "tmux new-session -d -s e008_m09_hm3d_rgbd_detector "
            f"'cd {ROOT} && <sudo-password-provider> {shlex.join(command)} "
            "> logs/<YYYYMMDD_HHMMSS>_e008_m09_hm3d_rgbd_detector.log 2>&1'"
        ),
        "verification_command": [
            "python",
            "experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py",
            "--predictions",
            str(M09_OUT_DIR / "container_output" / "real_proposals.jsonl"),
            "--manifest",
            str(M08_INPUT_DIR / "real_proposal_query_manifest.jsonl"),
            "--targets",
            str(M08_INPUT_DIR / "real_proposal_object_targets.jsonl"),
            "--schema",
            str(M08_INPUT_DIR / "proposal_output_schema.json"),
            "--out-dir",
            str(M09_OUT_DIR / "validator"),
            "--schema-only-smoke",
        ],
        "working_directory": str(ROOT),
    }


def build_long_job_rows(command_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "job_id": "e008_m08_hm3d_rendered_rgbd_frame_staging_smoke",
            "status": "not_launched",
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/run_m08_hm3d_rendered_rgbd_frame_staging_smoke.py",
            "output_path": str(M08_DATASET_ROOT),
            "expected_files": [
                str(M08_INPUT_DIR / "real_proposal_query_manifest.jsonl"),
                str(M08_INPUT_DIR / "real_proposal_object_targets.jsonl"),
                str(M08_INPUT_DIR / "prompt_set.json"),
                str(M08_INPUT_DIR / "proposal_output_schema.json"),
            ],
            "verification_command": "python experiments/E008_real_navigation_benchmark/tools/verify_m08_hm3d_rendered_rgbd_frame_staging.py",
            "log_path": "logs/<YYYYMMDD_HHMMSS>_e008_m08_hm3d_rendered_rgbd_frame_staging.log",
            "reason": "Frame rendering can become I/O-heavy; run in background if scaled beyond the 6-episode smoke.",
        },
        {
            "job_id": "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke",
            "status": "not_launched",
            "working_directory": str(ROOT),
            "command": command_plan["shell_command"],
            "output_path": str(M09_OUT_DIR),
            "expected_files": command_plan["expected_files"],
            "verification_command": shlex.join(command_plan["verification_command"]),
            "log_path": "logs/<YYYYMMDD_HHMMSS>_e008_m09_hm3d_rgbd_detector.log",
            "reason": "Detector inference can use GPU and must not block Codex in the foreground.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(
    coverage: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    image_rows: list[dict[str, Any]],
) -> str:
    manifest_summary = [
        {
            "scan_id": row["scan_id"],
            "category": row["object_category"],
            "labels": ",".join(row["target_labels"]),
            "frames": row["sampled_frame_count"],
        }
        for row in manifest_rows
    ]
    route_summary = [
        {
            "rank": row["rank"],
            "route_id": row["route_id"],
            "decision": row["decision"],
            "next_unit": row["next_unit"],
        }
        for row in route_rows
    ]
    return (
        "# E008-M07 HM3D Rendered RGB-D Detector Candidate Source Plan\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Episode rows: {coverage['episode_rows']}.\n"
        f"- Render plan rows: {coverage['render_plan_rows']}.\n"
        f"- Detector manifest rows: {coverage['detector_manifest_rows']}.\n"
        f"- Detector labels: {coverage['detector_label_count']}.\n"
        f"- `Habitat` image ready: {str(coverage['habitat_image_ready']).lower()}.\n"
        f"- `real-smoke` detector image ready: {str(coverage['real_proposal_image_ready']).lower()}.\n"
        f"- M06 semantic route status: `{coverage['m06_status']}`.\n"
        f"- Long job launched: {str(coverage['launch_long_job_now']).lower()}.\n\n"
        "## Detector Manifest\n\n"
        + markdown_table(manifest_summary, ["scan_id", "category", "labels", "frames"])
        + "\n\n"
        "## Image / Runner Readiness\n\n"
        + markdown_table(image_rows, ["component", "ready", "path_or_image", "reason"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M07 is a plan and schema-materialization step, not detector or navigation execution.\n"
        "- E008-M07 does not claim real navigation `SR` / `SPL`.\n"
        "- E008-M07 does not claim final real RGB-D/open-vocabulary robustness.\n"
        "- E008-M07 blocks `ObjectNav` goal, viewpoint, object id, and shortest-path fields as policy inputs.\n\n"
        "## Agent Inference\n\n"
        "- The next defensible unit is a tiny frame-staging smoke at episode start poses, because semantic annotation coordinates were not reliable in E008-M06.\n"
        "- The E003 detector runner can be reused only if M08 stages rendered frames in the compatibility layout `3RScan/scans/<scan_id>/sequence` with `_info.txt`, color, depth, and pose files.\n"
        "- Candidate coordinates from detector backprojection still need a Habitat coordinate-frame/snap-to-navmesh validation before any executed `SR` / `SPL` claim.\n"
    )


def run() -> dict[str, Any]:
    episode_rows = read_jsonl(M02_DATA_DIR / "episode_adapter_rows.jsonl")
    m06 = read_json(M06_ARTIFACT_DIR / "coverage.json")
    if not episode_rows:
        raise RuntimeError(f"missing M02 episode rows: {M02_DATA_DIR / 'episode_adapter_rows.jsonl'}")

    render_rows = build_render_plan_rows(episode_rows)
    manifest_rows = build_manifest_rows(episode_rows)
    target_rows = build_object_target_rows(episode_rows)
    prompt_set = build_prompt_set(episode_rows)
    blocked_rows = build_blocked_input_rows()
    route_rows = build_detector_route_rows()
    output_contract_rows = build_candidate_output_contract_rows()
    command_plan = detector_command_plan(
        label_count=int(prompt_set["label_count"]),
        scan_count=len(manifest_rows),
    )
    long_job_rows = build_long_job_rows(command_plan)

    habitat_image = docker_image_status(HABITAT_IMAGE)
    real_image = docker_image_status(REAL_PROPOSAL_IMAGE)
    image_rows = [
        {
            "component": "Habitat render Docker image",
            "ready": habitat_image["available"],
            "path_or_image": HABITAT_IMAGE,
            "reason": "Needed by M08 to render RGB-D frames from start poses.",
        },
        {
            "component": "E003 detector Docker image",
            "ready": real_image["available"],
            "path_or_image": REAL_PROPOSAL_IMAGE,
            "reason": "Needed by M09 to run GroundingDINO RGB-D proposal generation.",
        },
        {
            "component": "E003 frame-scaling runner",
            "ready": E003_RUNNER.exists(),
            "path_or_image": str(E003_RUNNER),
            "reason": "Reusable detector runner wrapper for staged compatibility frames.",
        },
        {
            "component": "E003 proposal validator",
            "ready": E003_VALIDATOR.exists(),
            "path_or_image": str(E003_VALIDATOR),
            "reason": "Reusable schema validator for detector output.",
        },
        {
            "component": "E003 proposal output schema",
            "ready": E003_SCHEMA.exists(),
            "path_or_image": str(E003_SCHEMA),
            "reason": "Schema copied into the M08 detector input directory.",
        },
        {
            "component": "HM3D read-only source root",
            "ready": RESEARCH3_DATA_ROOT.exists(),
            "path_or_image": str(RESEARCH3_DATA_ROOT),
            "reason": "Mounted read-only for M08 Habitat rendering.",
        },
    ]
    readiness = all(bool(row["ready"]) for row in image_rows)
    category_counts = Counter(str(row["object_category"]) for row in episode_rows)
    detector_labels = sorted({label for row in manifest_rows for label in row["target_labels"]})
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan_ready"
        if readiness
        else "e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan_blocked_readiness",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m08_dataset_root": str(M08_DATASET_ROOT),
        "m08_detector_input_dir": str(M08_INPUT_DIR),
        "m09_output_dir": str(M09_OUT_DIR),
        "m06_status": m06.get("status"),
        "m06_candidate_rows_ready": m06.get("candidate_rows_ready"),
        "episode_rows": len(episode_rows),
        "scene_count": len({row["scene_key"] for row in episode_rows}),
        "object_category_counts": dict(sorted(category_counts.items())),
        "render_strategy": "episode_start_pose_fixed_yaw_sweep",
        "render_frame_width": FRAME_WIDTH,
        "render_frame_height": FRAME_HEIGHT,
        "yaw_offsets_deg": YAW_OFFSETS_DEG,
        "render_plan_rows": len(render_rows),
        "detector_manifest_rows": len(manifest_rows),
        "detector_label_count": len(detector_labels),
        "detector_labels": detector_labels,
        "detector_route_ready": readiness,
        "habitat_image_ready": habitat_image["available"],
        "real_proposal_image_ready": real_image["available"],
        "real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M08 HM3D rendered RGB-D frame staging smoke",
        "blocked_policy_inputs": [row["field"] for row in blocked_rows if row["policy_input"] == "blocked"],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    if E003_SCHEMA.exists():
        shutil.copyfile(E003_SCHEMA, ARTIFACT_DIR / "proposal_output_schema.json")
        shutil.copyfile(E003_SCHEMA, DATA_OUT_DIR / "proposal_output_schema.json")

    outputs = [
        (ARTIFACT_DIR, True),
        (DATA_OUT_DIR, False),
    ]
    for base, include_report in outputs:
        write_json(base / "coverage.json", coverage)
        write_jsonl(base / "render_plan_rows.jsonl", render_rows)
        write_jsonl(base / "real_proposal_query_manifest.jsonl", manifest_rows)
        write_jsonl(base / "real_proposal_object_targets.jsonl", target_rows)
        write_json(base / "prompt_set.json", prompt_set)
        write_jsonl(base / "blocked_input_rows.jsonl", blocked_rows)
        write_jsonl(base / "candidate_output_contract_rows.jsonl", output_contract_rows)
        write_jsonl(base / "detector_route_rows.jsonl", route_rows)
        write_jsonl(base / "image_runner_readiness_rows.jsonl", image_rows)
        write_jsonl(base / "long_job_command_rows.jsonl", long_job_rows)
        write_json(base / "detector_run_command_plan.json", command_plan)
        if include_report:
            write_text(base / "report.md", build_report(coverage, manifest_rows, route_rows, image_rows))

    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
