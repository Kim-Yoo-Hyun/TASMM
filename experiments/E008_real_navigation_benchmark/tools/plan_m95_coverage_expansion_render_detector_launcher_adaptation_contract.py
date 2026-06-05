#!/usr/bin/env python3
"""Create the M95 coverage-expansion render/detector launcher adaptation contract."""

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
E003_RUNNER = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
M93_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M94_DIR = EXP_ROOT / "artifacts" / "E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M95_coverage_expansion_render_detector_launcher_adaptation_contract_v0"
)
M97_DETECTOR_OUT_DIR = EXP_ROOT / "artifacts" / "E008-M97_coverage_expansion_detector_candidate_source_v0"

VERSION = "e008_m95_coverage_expansion_render_detector_launcher_adaptation_contract_v0"
READY_STATUS = "e008_m95_coverage_expansion_render_detector_launcher_adaptation_contract_ready"
BLOCKED_STATUS = "e008_m95_coverage_expansion_render_detector_launcher_adaptation_contract_blocked"
NEXT_UNIT = "E008-M96 coverage-expansion render frame staging background launch"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
REAL_SMOKE_IMAGE = "research2/real-smoke:latest"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"
LOG_DIR = ROOT / "logs"
RENDER_TMUX_SESSION = "e008_m96_coverage_render"
DETECTOR_TMUX_SESSION = "e008_m97_coverage_detector"


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


def load_m15_render_tool():
    spec = importlib.util.spec_from_file_location("e008_m15_render_tool", M15_RENDER_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import M15 render tool: {M15_RENDER_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_script_for_m95() -> str:
    module = load_m15_render_tool()
    module.DATA_OUT_DIR = M93_DATA_DIR
    module.SCENE_DATASET_CONFIG = SCENE_DATASET_CONFIG
    return module.render_script()


def copy_with_version(rows: list[dict[str, Any]], row_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        new_row = dict(row)
        new_row["source_version"] = new_row.get("version")
        new_row["version"] = VERSION
        new_row["row_type"] = row_type
        output.append(new_row)
    return output


def expected_file_summary_rows(render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in render_rows:
        grouped[str(row.get("scan_id"))].append(row)
    output: list[dict[str, Any]] = []
    for scan_id, rows in sorted(grouped.items()):
        seq = M93_DATA_DIR / "3RScan" / "scans" / scan_id / "sequence"
        output.append(
            {
                "version": VERSION,
                "row_type": "expected_render_file_summary",
                "scan_id": scan_id,
                "adapter_episode_id": rows[0].get("adapter_episode_id"),
                "scene_key": rows[0].get("scene_key"),
                "object_category": rows[0].get("object_category"),
                "sequence_dir": str(seq),
                "expected_color_frames": len(rows),
                "expected_depth_frames": len(rows),
                "expected_pose_frames": len(rows),
                "expected_info_files": 1,
                "expected_total_files": len(rows) * 3 + 1,
            }
        )
    return output


def write_m93_launcher_inputs(
    render_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    render_input_dir = M93_DATA_DIR / "render_inputs"
    detector_input_dir = M93_DATA_DIR / "detector_inputs"
    targets = [
        (render_input_dir / "render_plan_rows.jsonl", "render_plan_rows", render_rows),
        (detector_input_dir / "real_proposal_query_manifest.jsonl", "real_proposal_query_manifest", manifest_rows),
    ]
    rows: list[dict[str, Any]] = []
    for path, file_role, payload in targets:
        write_jsonl(path, payload)
        rows.append(
            {
                "version": VERSION,
                "row_type": "launcher_input_materialization",
                "file_role": file_role,
                "path": str(path),
                "rows": len(payload),
                "ready": path.exists() and path.stat().st_size > 0,
                "data_bearing_root": str(M93_DATA_DIR),
            }
        )
    render_script_path = render_input_dir / "render_m95_coverage.py"
    write_text(render_script_path, render_script_for_m95())
    rows.append(
        {
            "version": VERSION,
            "row_type": "launcher_input_materialization",
            "file_role": "render_script",
            "path": str(render_script_path),
            "rows": None,
            "ready": render_script_path.exists() and render_script_path.stat().st_size > 0,
            "data_bearing_root": str(M93_DATA_DIR),
        }
    )
    return rows


def build_long_job_command_rows(docker: dict[str, Any], render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    render_log = LOG_DIR / f"{timestamp}_e008_m96_coverage_render.log"
    detector_log = LOG_DIR / f"{timestamp}_e008_m97_coverage_detector.log"
    render_input_dir = M93_DATA_DIR / "render_inputs"
    detector_input_dir = M93_DATA_DIR / "detector_inputs"
    docker_prefix = docker.get("selected_prefix") or ["docker"]

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
        f"{M93_DATA_DIR}:/out",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python /inputs/render_m95_coverage.py",
    ]
    render_shell = f"cd {shlex.quote(str(ROOT))} && {shell_join(docker_render)} > {shlex.quote(str(render_log))} 2>&1"
    render_tmux = f"mkdir -p {shlex.quote(str(LOG_DIR))} && tmux new-session -d -s {shlex.quote(RENDER_TMUX_SESSION)} {shlex.quote(render_shell)}"

    max_frames_per_scan = max((len(rows) for rows in group_by_scan(render_rows).values()), default=0)
    detector_command = [
        "python",
        str(E003_RUNNER),
        "--dataset-root",
        str(M93_DATA_DIR),
        "--m17-dir",
        str(detector_input_dir),
        "--out-dir",
        str(M97_DETECTOR_OUT_DIR),
        "--max-scans",
        "1",
        "--max-frames-per-scan",
        str(max_frames_per_scan),
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
            "job_id": "E008-M96",
            "job_status": "contract_recorded_not_launched",
            "job_type": "coverage_expansion_render_frame_staging",
            "working_directory": str(ROOT),
            "tmux_session": RENDER_TMUX_SESSION,
            "command": render_tmux,
            "inner_command": render_shell,
            "output_path": str(M93_DATA_DIR),
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
                "python experiments/E008_real_navigation_benchmark/tools/verify_m66_full_val_mini_render_frame_staging.py "
                f"--artifact-dir {M93_ARTIFACT_DIR} --data-out-dir {M93_DATA_DIR} --require-ready"
            ),
            "launch_now": False,
            "next_if_verified": "E008-M97 coverage-expansion detector candidate-source background launch",
        },
        {
            "version": VERSION,
            "row_type": "long_job_command",
            "job_id": "E008-M97",
            "job_status": "deferred_until_m96_render_verification",
            "job_type": "coverage_expansion_open_vocabulary_detector",
            "working_directory": str(ROOT),
            "tmux_session": DETECTOR_TMUX_SESSION,
            "command": detector_tmux,
            "inner_command": detector_shell,
            "output_path": str(M97_DETECTOR_OUT_DIR),
            "log_path": str(detector_log),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
            ],
            "verification_command": (
                f"python {M16_VERIFY_TOOL.relative_to(ROOT)} "
                f"--m15-artifact-dir {M93_ARTIFACT_DIR} "
                f"--m15-data-dir {M93_DATA_DIR} "
                f"--m16-dir {M97_DETECTOR_OUT_DIR} "
                f"--tmux-session {DETECTOR_TMUX_SESSION} --require-ready"
            ),
            "launch_now": False,
            "next_if_verified": "E008-M98 coverage-expansion source-gap goal-evaluation smoke",
        },
    ]


def group_by_scan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scan_id"))].append(row)
    return grouped


def build_preflight_rows(
    m94_coverage: dict[str, Any],
    render_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    docker: dict[str, Any],
) -> list[dict[str, Any]]:
    prefix = docker.get("selected_prefix") or ["docker"]
    habitat_image = image_status(prefix, HABITAT_IMAGE) if docker.get("available") else {"available": False}
    real_smoke_image = image_status(prefix, REAL_SMOKE_IMAGE) if docker.get("available") else {"available": False}
    detector_inputs = [
        M93_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl",
        M93_DATA_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl",
        M93_DATA_DIR / "detector_inputs" / "prompt_set.json",
        M93_DATA_DIR / "detector_inputs" / "proposal_output_schema.json",
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m94_route_ready",
            "gate_status": "pass"
            if m94_coverage.get("status") == "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_ready"
            and m94_coverage.get("selected_route") == "coverage_expansion_launcher_adaptation_first"
            else "fail",
            "blocks_m95": True,
            "details": m94_coverage.get("selected_route"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "coverage_render_rows_ready",
            "gate_status": "pass" if len(render_rows) == 96 else "fail",
            "blocks_m95": True,
            "details": len(render_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "coverage_detector_manifest_ready",
            "gate_status": "pass" if len(manifest_rows) == 1 else "fail",
            "blocks_m95": True,
            "details": len(manifest_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "launcher_inputs_written",
            "gate_status": "pass" if input_rows and all(row.get("ready") for row in input_rows) else "fail",
            "blocks_m95": True,
            "details": Counter(str(row.get("ready")) for row in input_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "detector_input_files_ready",
            "gate_status": "pass" if all(path.exists() and path.stat().st_size > 0 for path in detector_inputs) else "fail",
            "blocks_m95": True,
            "details": [str(path) for path in detector_inputs],
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "external_hm3d_data_readonly_source_ready",
            "gate_status": "pass" if RESEARCH3_DATA_ROOT.exists() else "fail",
            "blocks_m96": True,
            "details": str(RESEARCH3_DATA_ROOT),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "docker_available",
            "gate_status": "pass" if docker.get("available") else "warning",
            "blocks_m96": True,
            "details": docker.get("mode"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat_image.get("available") else "warning",
            "blocks_m96": True,
            "details": HABITAT_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_smoke_image.get("available") else "warning",
            "blocks_m97": True,
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "tmux_sessions_free",
            "gate_status": "pass" if not tmux_running(RENDER_TMUX_SESSION) and not tmux_running(DETECTOR_TMUX_SESSION) else "warning",
            "blocks_m96": True,
            "details": [RENDER_TMUX_SESSION, DETECTOR_TMUX_SESSION],
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "no_long_job_launched_in_m95",
            "gate_status": "pass",
            "blocks_m95": False,
            "details": "M95 writes launcher contract and input files only.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "coverage_launcher_adaptation",
            "support_status": "supported",
            "allowed_claim": "M95 adapts M93 coverage rows into render/detector launcher-ready inputs and exact command ledger.",
            "blocked_claims": [
                "coverage branch recovers source-gap target",
                "detector candidate quality improves",
                "real navigation SR/SPL improves",
                "final real RGB-D/open-vocabulary robustness is solved",
            ],
        }
    ]


def build_route_decision_rows(status: str) -> list[dict[str, Any]]:
    ready = status == READY_STATUS
    return [
        {
            "version": VERSION,
            "decision": "m95_launcher_contract_ready_select_m96" if ready else "m95_launcher_contract_blocked",
            "selected_next_unit": NEXT_UNIT if ready else "repair M95 launcher adaptation contract",
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "render_launch_ready_next": ready,
            "detector_launch_ready_now": False,
            "trajectory_promotion_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "reason": (
                "M95 wrote M93 coverage render inputs, detector query manifest, exact render/detector command ledger, and verification commands."
                if ready
                else "M95 launcher adaptation has blocking gates."
            ),
        }
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M95 Coverage-Expansion Render/Detector Launcher Adaptation Contract",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M93 render plan rows: {coverage['coverage_render_rows']}.",
            f"- M93 detector manifest rows: {coverage['coverage_detector_manifest_rows']}.",
            f"- Launcher input rows: {coverage['launcher_input_materialization_rows']}.",
            f"- Long-job command rows: {coverage['long_job_command_rows']}.",
            f"- Render input dir: `{coverage['render_input_dir']}`.",
            f"- Detector input dir: `{coverage['detector_input_dir']}`.",
            f"- Selected next unit: `{coverage['selected_next_unit']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M95 is a launcher adaptation contract only.",
            "- M95 does not render RGB-D frames, run detector inference, evaluate source-gap recovery, or execute trajectories.",
            "- Final real navigation `SR` / `SPL`, deployable search policy, and final RGB-D/open-vocabulary robustness remain blocked.",
            "",
        ]
    )


def mirror_contract_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    M93_DATA_DIR.mkdir(parents=True, exist_ok=True)

    m94_coverage = read_json(M94_DIR / "coverage.json")
    render_rows = copy_with_version(
        read_jsonl(M93_ARTIFACT_DIR / "coverage_expansion_render_plan_rows.jsonl"),
        "coverage_expansion_render_plan",
    )
    manifest_rows = copy_with_version(
        read_jsonl(M93_ARTIFACT_DIR / "coverage_expansion_detector_manifest_rows.jsonl"),
        "coverage_expansion_detector_manifest",
    )
    input_rows = write_m93_launcher_inputs(render_rows, manifest_rows)
    expected_rows = expected_file_summary_rows(render_rows)
    docker = docker_status()
    preflight_rows = build_preflight_rows(m94_coverage, render_rows, manifest_rows, input_rows, docker)
    command_rows = build_long_job_command_rows(docker, render_rows)
    claim_rows = build_claim_boundary_rows()

    blockers = [
        row["gate_id"]
        for row in preflight_rows
        if row.get("blocks_m95") and row.get("gate_status") == "fail"
    ]
    status = READY_STATUS if not blockers else BLOCKED_STATUS
    route_rows = build_route_decision_rows(status)
    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "next_unit": NEXT_UNIT if status == READY_STATUS else "repair M95 launcher adaptation contract",
            "action": "Launch the recorded E008-M96 coverage render tmux job only after user asks for the next TODO.",
            "launch_long_job_now": False,
        }
    ]

    outputs = {
        "coverage_expansion_render_plan_rows.jsonl": render_rows,
        "coverage_expansion_detector_manifest_rows.jsonl": manifest_rows,
        "expected_file_summary_rows.jsonl": expected_rows,
        "launcher_input_materialization_rows.jsonl": input_rows,
        "readiness_gate_rows.jsonl": preflight_rows,
        "long_job_command_rows.jsonl": command_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_action_rows,
    }
    output_paths: list[Path] = []
    for name, rows in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, rows)
        output_paths.append(path)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "data_bearing_output_root": str(M93_DATA_DIR),
        "m94_status": m94_coverage.get("status"),
        "m94_selected_route": m94_coverage.get("selected_route"),
        "coverage_render_rows": len(render_rows),
        "coverage_detector_manifest_rows": len(manifest_rows),
        "expected_file_summary_rows": len(expected_rows),
        "launcher_input_materialization_rows": len(input_rows),
        "readiness_gate_rows": len(preflight_rows),
        "readiness_gate_fail_rows": sum(1 for row in preflight_rows if row.get("gate_status") == "fail"),
        "readiness_gate_warning_rows": sum(1 for row in preflight_rows if row.get("gate_status") == "warning"),
        "m95_blockers": blockers,
        "long_job_command_rows": len(command_rows),
        "render_input_dir": str(M93_DATA_DIR / "render_inputs"),
        "detector_input_dir": str(M93_DATA_DIR / "detector_inputs"),
        "render_script_ready": (M93_DATA_DIR / "render_inputs" / "render_m95_coverage.py").exists(),
        "detector_query_manifest_ready": (M93_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl").exists(),
        "render_launch_ready_next": status == READY_STATUS,
        "detector_launch_ready_now": False,
        "long_job_launched": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else "repair M95 launcher adaptation contract",
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    output_paths.extend([ARTIFACT_DIR / "coverage.json", ARTIFACT_DIR / "report.md"])
    mirror_contract_outputs(output_paths)

    if status != READY_STATUS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
