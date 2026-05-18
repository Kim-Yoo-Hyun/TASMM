#!/usr/bin/env python3
"""Preflight DualMap runtime readiness before a one-scan smoke."""

from __future__ import annotations

import importlib.util
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M05_dualmap_runtime_preflight_v0"
)
M04_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M04_dualmap_staging_root_materialization_v0"
)
DUALMAP_REPO = ROOT / "local_dataset" / "external_repos" / "DualMap"
EXPECTED_COMMIT = "157235ec49e6a1f439babbc571c4c02ad1f06aa9"
SMOKE_SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
STAGED_DATASET = ROOT / "local_dataset" / "DualMap_staged" / "3rscan_scannet_exported" / "scannet"
STAGED_CONFIG = (
    ROOT
    / "local_dataset"
    / "DualMap_staged"
    / "3rscan_scannet_exported"
    / "config"
    / "dualmap_3rscan_scannet.yaml"
)
OUTPUT_PATH = ROOT / "local_dataset" / "DualMap_outputs" / SMOKE_SCAN_ID

REQUIRED_MODULES = [
    "hydra",
    "omegaconf",
    "torch",
    "cv2",
    "imageio",
    "numpy",
    "open3d",
    "open_clip",
    "ultralytics",
    "rerun",
    "faiss",
    "kornia",
    "natsort",
    "scipy",
    "tyro",
    "supervision",
]


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 20,
    input_text: str | None = None,
) -> dict:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=input_text,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # pragma: no cover - defensive diagnostics
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def git_status() -> dict:
    if not (DUALMAP_REPO / ".git").exists():
        return {
            "repo_path": str(DUALMAP_REPO),
            "exists": False,
            "head": None,
            "head_matches_expected": False,
            "submodule_status": "",
            "submodule_ready": False,
        }
    head = run(["git", "rev-parse", "HEAD"], cwd=DUALMAP_REPO)
    submodules = run(["git", "submodule", "status", "--recursive"], cwd=DUALMAP_REPO)
    submodule_status = submodules["stdout"]
    # In git-submodule status, a leading '-' means not initialized.
    submodule_ready = bool(submodule_status) and not any(
        line.startswith("-") for line in submodule_status.splitlines()
    )
    return {
        "repo_path": str(DUALMAP_REPO),
        "exists": True,
        "expected_commit": EXPECTED_COMMIT,
        "head": head["stdout"] if head["ok"] else None,
        "head_matches_expected": head["stdout"] == EXPECTED_COMMIT,
        "submodule_status": submodule_status,
        "submodule_ready": submodule_ready,
        "environment_yml_exists": (DUALMAP_REPO / "environment.yml").exists(),
        "runner_dataset_exists": (DUALMAP_REPO / "applications" / "runner_dataset.py").exists(),
        "object_source_exists": (DUALMAP_REPO / "utils" / "object.py").exists(),
    }


def dependency_status() -> dict:
    rows = []
    missing = []
    for module in REQUIRED_MODULES:
        present = importlib.util.find_spec(module) is not None
        rows.append({"module": module, "present_in_current_python": present})
        if not present:
            missing.append(module)
    return {
        "required_module_count": len(REQUIRED_MODULES),
        "missing_module_count": len(missing),
        "missing_modules": missing,
        "current_python_runtime_ready": len(missing) == 0,
        "rows": rows,
    }


def docker_status(sudo_password: str | None = None) -> dict:
    # Prefer sudo -n because this workspace commonly uses Docker through sudo.
    attempts = [
        (["docker", "info", "--format", "{{.ServerVersion}}"], None),
        (["sudo", "-n", "docker", "info", "--format", "{{.ServerVersion}}"], None),
    ]
    if sudo_password:
        attempts.append(
            (
                ["sudo", "-S", "docker", "info", "--format", "{{.ServerVersion}}"],
                sudo_password + "\n",
            )
        )
    selected = None
    for cmd, input_text in attempts:
        result = run(cmd, timeout=10, input_text=input_text)
        if result["ok"]:
            selected = result
            break
    runtime_result = run(
        ["sudo", "-n", "docker", "info", "--format", "{{json .Runtimes}}"], timeout=10
    )
    if sudo_password and not runtime_result["ok"]:
        runtime_result = run(
            ["sudo", "-S", "docker", "info", "--format", "{{json .Runtimes}}"],
            timeout=10,
            input_text=sudo_password + "\n",
        )
    return {
        "docker_info_ready": selected is not None,
        "server_version": selected["stdout"] if selected else None,
        "selected_command": selected["cmd"] if selected else None,
        "nvidia_runtime_detected": "nvidia" in runtime_result.get("stdout", ""),
        "runtime_probe_ok": runtime_result["ok"],
    }


def gpu_status() -> dict:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ],
        timeout=10,
    )
    return {
        "nvidia_smi_ready": result["ok"],
        "summary": result["stdout"],
    }


def staged_scan_status() -> dict:
    scene_dir = STAGED_DATASET / "exported" / SMOKE_SCAN_ID
    color_dir = scene_dir / "color"
    depth_dir = scene_dir / "depth"
    pose_dir = scene_dir / "pose"
    intrinsic_path = scene_dir / "intrinsic" / "intrinsic_depth.txt"
    color_paths = sorted(color_dir.glob("*.jpg"))
    depth_paths = sorted(depth_dir.glob("*.png"))
    pose_paths = sorted(pose_dir.glob("*.txt"))
    sample_color = None
    sample_depth = None
    if color_paths:
        with Image.open(color_paths[0]) as image:
            sample_color = {"path": str(color_paths[0]), "size": list(image.size), "mode": image.mode}
    if depth_paths:
        with Image.open(depth_paths[0]) as image:
            sample_depth = {"path": str(depth_paths[0]), "size": list(image.size), "mode": image.mode}
    return {
        "scan_id": SMOKE_SCAN_ID,
        "scene_dir": str(scene_dir),
        "scene_dir_exists": scene_dir.exists(),
        "staged_config_exists": STAGED_CONFIG.exists(),
        "color_count": len(color_paths),
        "depth_count": len(depth_paths),
        "pose_count": len(pose_paths),
        "intrinsic_exists": intrinsic_path.exists(),
        "frame_counts_match": len(color_paths) == len(depth_paths) == len(pose_paths) and len(color_paths) > 0,
        "sample_color": sample_color,
        "sample_depth": sample_depth,
        "color_depth_size_match": bool(
            sample_color and sample_depth and sample_color["size"] == sample_depth["size"]
        ),
    }


def static_object_schema() -> dict:
    object_py = DUALMAP_REPO / "utils" / "object.py"
    if not object_py.exists():
        return {"static_schema_inspected": False, "fields": []}
    text = object_py.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"def __getstate__\(self\):(?P<body>.*?)\n    def __setstate__", text, re.S)
    if not match:
        return {"static_schema_inspected": False, "fields": []}
    fields = re.findall(r'"([^"]+)":', match.group("body"))
    return {
        "static_schema_inspected": True,
        "source": str(object_py),
        "serialization_method": "pickle via BaseObject.__getstate__",
        "fields": fields,
        "minimum_e004_candidate_fields_present_by_source": {
            "object_id": "uid" in fields,
            "semantic_label": "class_id" in fields,
            "centroid_or_points": "pcd_points" in fields,
            "clip_or_retrieval_feature": "clip_ft" in fields,
            "confidence_score": False,
            "observation_support": False,
        },
    }


def build_runtime_command() -> dict:
    command = [
        "python",
        "-m",
        "applications.runner_dataset",
        "dataset_name=scannet",
        f"scene_id={SMOKE_SCAN_ID}",
        f"dataset_path={STAGED_DATASET}",
        f"dataset_conf_path={STAGED_CONFIG}",
        f"output_path={OUTPUT_PATH}",
        "use_rerun=false",
        "run_local_mapping_only=true",
        "save_local_map=true",
        "use_parallel=false",
        "stride=20",
    ]
    log_path = ROOT / "logs" / "YYYYMMDD_HHMMSS_e005_m06_dualmap_one_scan_runtime.log"
    return {
        "purpose": "Run only after dependency/submodule readiness is repaired.",
        "working_directory": str(DUALMAP_REPO),
        "command": command,
        "tmux_template": (
            "tmux new -d -s e005_m06_dualmap_runtime "
            f"'cd {DUALMAP_REPO} && {' '.join(command)} > {log_path} 2>&1'"
        ),
        "expected_output_path": str(OUTPUT_PATH),
        "verification_command": (
            f"find {OUTPUT_PATH} -path '*/map/*.pkl' -o "
            f"-path '*/map/layout.pcd' -o -name system_time.csv"
        ),
    }


def build_bootstrap_plan() -> dict:
    log_path = ROOT / "logs" / "YYYYMMDD_HHMMSS_e005_m06_dualmap_env_bootstrap.log"
    commands = [
        "git submodule set-url 3rdparty/mobileclip https://github.com/apple/ml-mobileclip.git",
        "git submodule update --init --recursive",
        "# Docker route is preferred for paper-body experiments; create a bounded DualMap smoke image before running full mapping.",
        "# If using conda for source-compatible preflight only: conda env create -f environment.yml",
    ]
    return {
        "status": "plan_only_not_launched",
        "working_directory": str(DUALMAP_REPO),
        "log_path_template": str(log_path),
        "commands": commands,
        "tmux_template": (
            "tmux new -d -s e005_m06_dualmap_env_bootstrap "
            f"'cd {DUALMAP_REPO} && "
            "git submodule set-url 3rdparty/mobileclip https://github.com/apple/ml-mobileclip.git && "
            f"git submodule update --init --recursive > {log_path} 2>&1'"
        ),
        "verification_command": "git submodule status --recursive && test -f 3rdparty/mobileclip/setup.py",
    }


def write_report(coverage: dict, decision: dict) -> None:
    lines = [
        "# E005-M05 DualMap Runtime Preflight",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Repo path: `{coverage['repo']['repo_path']}`.",
        f"- Repo head matches expected commit: {str(coverage['repo']['head_matches_expected']).lower()}.",
        f"- `mobileclip` submodule ready: {str(coverage['repo']['submodule_ready']).lower()}.",
        f"- Current Python runtime ready: {str(coverage['dependencies']['current_python_runtime_ready']).lower()}.",
        f"- Missing current Python modules: {coverage['dependencies']['missing_module_count']} / {coverage['dependencies']['required_module_count']}.",
        f"- Docker daemon ready: {str(coverage['docker']['docker_info_ready']).lower()}.",
        f"- NVIDIA runtime detected: {str(coverage['docker']['nvidia_runtime_detected']).lower()}.",
        f"- GPU probe: `{coverage['gpu']['summary']}`.",
        f"- Smoke scan frame counts match: {str(coverage['staged_scan']['frame_counts_match']).lower()}.",
        f"- Smoke scan color/depth/pose count: {coverage['staged_scan']['color_count']} / {coverage['staged_scan']['depth_count']} / {coverage['staged_scan']['pose_count']}.",
        f"- Static object pickle schema inspected: {str(coverage['object_schema']['static_schema_inspected']).lower()}.",
        f"- DualMap runtime launched: {str(coverage['dualmap_runtime_launched']).lower()}.",
        f"- Runtime object pickle inspected: {str(coverage['runtime_object_pkl_inspected']).lower()}.",
        "",
        "## Paper Claim Boundary",
        "",
        "- E005-M05 does not support a `DualMap` performance claim.",
        "- E005-M05 supports a runtime-readiness claim: the source and staged scan are present, but dependency/submodule readiness blocks a fair one-scan runtime smoke.",
        "- Static source inspection shows object `*.pkl` can expose object id, class id, point cloud points, colors, and CLIP feature, but runtime map outputs must still be generated before adapter metrics are valid.",
        "- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
        "## Agent Inference",
        "",
        "- The immediate blocker is no longer 3RScan file layout. It is `DualMap` dependency/bootstrap readiness.",
        "- Because paper-body experiments should use Docker, the next unit should create or launch a bounded `DualMap` Docker/submodule bootstrap rather than installing dependencies into the host Python.",
        "- The color/depth resolution mismatch is acceptable for loader smoke only if `DualMap` resizes both streams to the dataset config size; metric claims still need visual/depth alignment validation.",
        "",
        "## User Decision Needed",
        "",
        "- None before E005-M06.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in decision["blockers"])
    lines.extend(
        [
            "",
            "## Next",
            "",
            f"- {decision['next_recommended_unit']}",
            "",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docker-sudo-password-stdin",
        action="store_true",
        help="Read a sudo password from stdin for Docker probe only; never write it to artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sudo_password = sys.stdin.readline().rstrip("\n") if args.docker_sudo_password_stdin else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m04_runtime_plan = read_json(M04_DIR / "runtime_smoke_plan.json")
    coverage = {
        "e005_version": "e005_m05_dualmap_runtime_preflight_v0",
        "status": "e005_m05_dualmap_runtime_blocked_env_bootstrap_required",
        "repo": git_status(),
        "dependencies": dependency_status(),
        "docker": docker_status(sudo_password=sudo_password),
        "gpu": gpu_status(),
        "staged_scan": staged_scan_status(),
        "object_schema": static_object_schema(),
        "m04_runtime_plan": m04_runtime_plan,
        "runtime_command_plan": build_runtime_command(),
        "bootstrap_plan": build_bootstrap_plan(),
        "dualmap_runtime_launched": False,
        "runtime_object_pkl_inspected": False,
        "external_baseline_comparison_ready": False,
    }

    blockers = []
    if not coverage["repo"]["head_matches_expected"]:
        blockers.append("DualMap repo is missing or not pinned to the expected audited commit.")
    if not coverage["repo"]["submodule_ready"]:
        blockers.append("DualMap mobileclip submodule is not initialized.")
    if not coverage["dependencies"]["current_python_runtime_ready"]:
        blockers.append("Current Python environment is missing DualMap runtime dependencies.")
    if not coverage["staged_scan"]["frame_counts_match"]:
        blockers.append("Staged smoke scan color/depth/pose frame counts do not match.")
    if not coverage["staged_scan"]["intrinsic_exists"]:
        blockers.append("Staged smoke scan intrinsic_depth.txt is missing.")

    runtime_ready = not blockers and coverage["docker"]["docker_info_ready"]
    if runtime_ready:
        coverage["status"] = "e005_m05_dualmap_runtime_preflight_ready_for_one_scan_smoke"

    decision = {
        "status": coverage["status"],
        "selected_route": "DualMap",
        "runtime_ready": runtime_ready,
        "runtime_launched": False,
        "runtime_object_pkl_inspected": False,
        "static_object_schema_inspected": coverage["object_schema"]["static_schema_inspected"],
        "external_baseline_comparison_ready": False,
        "blockers": blockers,
        "next_recommended_unit": (
            "E005-M06 DualMap Docker/submodule bootstrap background launch"
            if blockers
            else "E005-M06 DualMap one-scan runtime smoke launch"
        ),
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_json(OUT_DIR / "dependency_rows.json", coverage["dependencies"]["rows"])
    write_json(OUT_DIR / "runtime_command_plan.json", coverage["runtime_command_plan"])
    write_json(OUT_DIR / "bootstrap_plan.json", coverage["bootstrap_plan"])
    write_json(OUT_DIR / "static_object_pkl_schema.json", coverage["object_schema"])
    write_report(coverage, decision)
    print(json.dumps({**decision, "artifact_dir": str(OUT_DIR)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
