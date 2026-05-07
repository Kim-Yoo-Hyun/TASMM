#!/usr/bin/env python3
"""Prepare the E003-M18 Dockerized real-proposal detector scaffold."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M18_dockerized_real_proposal_detector_scaffold_v0"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
CONTAINER_RUNNER = DOCKER_DIR / "run_rgbd_ov_proposals.py"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
IMAGE_TAG = "research2/real-smoke"
SCAFFOLD_VERSION = "e003_m18_dockerized_real_proposal_detector_scaffold_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def command_status(command: list[str], input_text: str | None = None, display_command: list[str] | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True, input=input_text)
    except FileNotFoundError as exc:
        return {
            "available": False,
            "command": display_command or command,
            "returncode": None,
            "stderr": str(exc),
            "stdout": "",
        }
    return {
        "available": result.returncode == 0,
        "command": display_command or command,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "stdout": result.stdout.strip(),
    }


def docker_command(command: list[str], use_sudo: bool) -> list[str]:
    if not use_sudo:
        return command
    return ["sudo", "-S", "-p", ""] + command


def docker_display_command(command: list[str], use_sudo: bool) -> list[str]:
    if not use_sudo:
        return command
    return ["sudo", "-S", "-p", ""] + command


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M18 Dockerized Real-Proposal Detector Scaffold",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Dockerfile ready: {coverage['dockerfile_ready']}",
            f"- Container runner ready: {coverage['container_runner_ready']}",
            f"- Container runner local smoke ready: {coverage['container_runner_local_smoke_ready']}",
            f"- Host wrapper ready: {coverage['host_wrapper_ready']}",
            f"- Proposal output validator ready: {coverage['validator_ready']}",
            f"- Validator smoke ready: {coverage['validator_smoke_ready']}",
            f"- Docker CLI ready: {coverage['docker_cli_ready']}",
            f"- Docker daemon ready: {coverage['docker_daemon_ready']}",
            f"- Docker socket: {coverage['docker_socket_status']['stdout']}",
            f"- Current user groups: {coverage['current_groups']['stdout']}",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker smoke executed: {coverage['docker_smoke_executed']}",
            f"- Docker smoke validator ready: {coverage['docker_smoke_validator_ready']}",
            f"- Docker image tag: {coverage['image_tag']}",
            f"- Detector backend integrated: {coverage['detector_backend_integrated']}",
            f"- Detector predictions ready: {coverage['detector_predictions_ready']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M18 supports a Docker execution contract for later real RGB-D/open-vocabulary proposal generation.",
            "- E003-M18 supports schema validation for future `real_proposal_prediction_jsonl_v0` outputs.",
            "- E003-M18 does not support real perception robustness results because no detector backend prediction has been generated.",
            "",
            "## 에이전트 추론",
            "",
            "- E003 should continue to the Dockerized real-proposal route before E004/E005 because real perception evidence is the current top-tier bottleneck.",
            "- The scaffold writes only empty smoke output by default so detector evidence is not fabricated.",
            "- Docker build/smoke validates the execution contract, but a detector backend is still required before paper-table perception metrics.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M18 scaffold if Docker build and smoke have executed. Next is detector backend integration.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--build", action="store_true", help="Attempt docker build if the daemon is available.")
    parser.add_argument("--smoke-run", action="store_true", help="Attempt docker smoke run if build succeeds.")
    parser.add_argument("--docker-sudo", action="store_true", help="Run docker commands through sudo -S.")
    parser.add_argument("--sudo-password-stdin", action="store_true", help="Read one sudo password line from stdin.")
    args = parser.parse_args()
    sudo_input = None
    if args.docker_sudo and args.sudo_password_stdin:
        if sys.stdin.isatty():
            sudo_input = getpass.getpass("")
        else:
            sudo_input = sys.stdin.readline()
        if sudo_input and not sudo_input.endswith("\n"):
            sudo_input += "\n"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.m17_dir / "real_proposal_query_manifest.jsonl"
    target_path = args.m17_dir / "real_proposal_object_targets.jsonl"
    prompt_set_path = args.m17_dir / "prompt_set.json"
    schema_path = args.m17_dir / "proposal_output_schema.json"
    empty_predictions = args.out_dir / "empty_scaffold_real_proposals.jsonl"
    local_runner_output = args.out_dir / "container_runner_local_smoke" / "real_proposals.jsonl"
    validator_out = args.out_dir / "validator_smoke"
    docker_output_dir = args.out_dir / "docker_smoke_output"

    required_paths = [manifest_path, target_path, prompt_set_path, schema_path, DOCKERFILE, CONTAINER_RUNNER, VALIDATOR]
    missing_paths = [str(path) for path in required_paths if not path.exists()]
    if missing_paths:
        write_json(args.out_dir / "coverage.json", {"missing_paths": missing_paths, "status": "missing_required_paths"})
        return 2

    manifest_rows = load_jsonl(manifest_path)
    target_rows = load_jsonl(target_path)
    prompt_set = load_json(prompt_set_path)
    empty_predictions.write_text("", encoding="utf-8")

    validator_cmd = [
        sys.executable,
        str(VALIDATOR),
        "--predictions",
        str(empty_predictions),
        "--manifest",
        str(manifest_path),
        "--targets",
        str(target_path),
        "--schema",
        str(schema_path),
        "--out-dir",
        str(validator_out),
        "--allow-empty-scaffold",
    ]
    validator_result = subprocess.run(validator_cmd, check=False, text=True, capture_output=True)

    local_runner_cmd = [
        sys.executable,
        str(CONTAINER_RUNNER),
        "--manifest",
        str(manifest_path),
        "--schema",
        str(schema_path),
        "--output",
        str(local_runner_output),
        "--detector",
        "open_vocab_rgbd_detector_v0",
        "--prompt-set",
        str(prompt_set_path),
        "--seed",
        "101",
    ]
    local_runner_result = subprocess.run(local_runner_cmd, check=False, text=True, capture_output=True)

    build_cmd = [
        "docker",
        "build",
        "-f",
        str(DOCKERFILE),
        "-t",
        IMAGE_TAG,
        str(DOCKER_DIR),
    ]
    detector_run_cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--gpus",
        "all",
        "-v",
        f"{args.dataset_root}:/data:ro",
        "-v",
        f"{args.m17_dir}:/inputs:ro",
        "-v",
        f"{docker_output_dir}:/outputs",
        IMAGE_TAG,
        "python",
        "/workspace/tools/run_rgbd_ov_proposals.py",
        "--manifest",
        "/inputs/real_proposal_query_manifest.jsonl",
        "--schema",
        "/inputs/proposal_output_schema.json",
        "--output",
        "/outputs/real_proposals.jsonl",
        "--detector",
        "open_vocab_rgbd_detector_v0",
        "--prompt-set",
        "/inputs/prompt_set.json",
        "--seed",
        "101",
    ]
    smoke_run_cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-v",
        f"{args.dataset_root}:/data:ro",
        "-v",
        f"{args.m17_dir}:/inputs:ro",
        "-v",
        f"{docker_output_dir}:/outputs",
        IMAGE_TAG,
        "python",
        "/workspace/tools/run_rgbd_ov_proposals.py",
        "--manifest",
        "/inputs/real_proposal_query_manifest.jsonl",
        "--schema",
        "/inputs/proposal_output_schema.json",
        "--output",
        "/outputs/real_proposals.jsonl",
        "--detector",
        "open_vocab_rgbd_detector_v0",
        "--prompt-set",
        "/inputs/prompt_set.json",
        "--seed",
        "101",
    ]

    docker_version = command_status(
        docker_command(["docker", "--version"], args.docker_sudo),
        input_text=sudo_input,
        display_command=docker_display_command(["docker", "--version"], args.docker_sudo),
    )
    docker_info = command_status(
        docker_command(["docker", "info", "--format", "{{.ServerVersion}}"], args.docker_sudo),
        input_text=sudo_input,
        display_command=docker_display_command(["docker", "info", "--format", "{{.ServerVersion}}"], args.docker_sudo),
    )
    docker_socket_status = command_status(["ls", "-l", "/var/run/docker.sock"])
    current_id = command_status(["id"])
    current_groups = command_status(["groups"])
    build_result: dict[str, Any] | None = None
    smoke_result: dict[str, Any] | None = None
    docker_smoke_validator_result: dict[str, Any] | None = None
    docker_smoke_validator_coverage: dict[str, Any] = {}
    if args.build and docker_info["available"]:
        build_result = command_status(
            docker_command(build_cmd, args.docker_sudo),
            input_text=sudo_input,
            display_command=docker_display_command(build_cmd, args.docker_sudo),
        )
        if args.smoke_run and build_result["available"]:
            docker_output_dir.mkdir(parents=True, exist_ok=True)
            smoke_result = command_status(
                docker_command(smoke_run_cmd, args.docker_sudo),
                input_text=sudo_input,
                display_command=docker_display_command(smoke_run_cmd, args.docker_sudo),
            )
            if smoke_result["available"]:
                docker_smoke_validator_cmd = [
                    sys.executable,
                    str(VALIDATOR),
                    "--predictions",
                    str(docker_output_dir / "real_proposals.jsonl"),
                    "--manifest",
                    str(manifest_path),
                    "--targets",
                    str(target_path),
                    "--schema",
                    str(schema_path),
                    "--out-dir",
                    str(args.out_dir / "docker_smoke_validator"),
                    "--allow-empty-scaffold",
                ]
                validator_process = subprocess.run(docker_smoke_validator_cmd, check=False, text=True, capture_output=True)
                docker_smoke_validator_result = {
                    "command": docker_smoke_validator_cmd,
                    "returncode": validator_process.returncode,
                    "stderr": validator_process.stderr.strip(),
                    "stdout": validator_process.stdout.strip(),
                }
                docker_smoke_validator_path = args.out_dir / "docker_smoke_validator" / "coverage.json"
                if docker_smoke_validator_path.exists():
                    docker_smoke_validator_coverage = load_json(docker_smoke_validator_path)

    validator_coverage_path = validator_out / "coverage.json"
    validator_coverage = load_json(validator_coverage_path) if validator_coverage_path.exists() else {}
    docker_daemon_ready = bool(docker_info["available"])
    docker_build_executed = build_result is not None
    docker_smoke_executed = smoke_result is not None
    status = "docker_scaffold_ready"
    if not docker_daemon_ready:
        status = "docker_scaffold_ready_daemon_permission_blocked"
    elif args.build and build_result and not build_result["available"]:
        status = "docker_scaffold_ready_build_failed"
    elif args.smoke_run and smoke_result and not smoke_result["available"]:
        status = "docker_scaffold_ready_smoke_failed"

    coverage = {
        "build_command": build_cmd,
        "container_runner": str(CONTAINER_RUNNER),
        "container_runner_local_smoke_command": local_runner_cmd,
        "container_runner_local_smoke_ready": local_runner_result.returncode == 0 and local_runner_output.exists(),
        "container_runner_local_smoke_result": {
            "returncode": local_runner_result.returncode,
            "stderr": local_runner_result.stderr.strip(),
            "stdout": local_runner_result.stdout.strip(),
        },
        "container_runner_ready": CONTAINER_RUNNER.exists(),
        "detector_backend_integrated": False,
        "detector_predictions_ready": False,
        "docker_build_executed": docker_build_executed,
        "docker_build_result": build_result,
        "docker_cli_ready": bool(docker_version["available"]),
        "docker_command_uses_sudo": args.docker_sudo,
        "docker_daemon_ready": docker_daemon_ready,
        "docker_info": docker_info,
        "docker_smoke_executed": docker_smoke_executed,
        "docker_smoke_result": smoke_result,
        "docker_smoke_validator_coverage": docker_smoke_validator_coverage,
        "docker_smoke_validator_ready": bool(docker_smoke_validator_coverage.get("valid")),
        "docker_smoke_validator_result": docker_smoke_validator_result,
        "docker_socket_status": docker_socket_status,
        "docker_version": docker_version,
        "current_groups": current_groups,
        "current_id": current_id,
        "dockerfile": str(DOCKERFILE),
        "dockerfile_ready": DOCKERFILE.exists(),
        "host_wrapper_ready": True,
        "image_tag": IMAGE_TAG,
        "manifest_rows": len(manifest_rows),
        "next_recommended_unit": "E003-M19 real detector backend integration or Docker build smoke after daemon access",
        "object_target_rows": len(target_rows),
        "paper_table_command_ready": False,
        "prompt_label_count": len(prompt_set.get("labels", [])),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "detector_run_command": detector_run_cmd,
        "smoke_run_command": smoke_run_cmd,
        "scaffold_version": SCAFFOLD_VERSION,
        "status": status,
        "validator_command": validator_cmd,
        "validator_ready": VALIDATOR.exists(),
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr": validator_result.stderr.strip(),
            "stdout": validator_result.stdout.strip(),
        },
        "validator_smoke_coverage": validator_coverage,
        "validator_smoke_ready": validator_result.returncode == 0 and validator_coverage.get("valid") is True,
    }

    write_json(args.out_dir / "docker_build_plan.json", {"command": build_cmd, "image_tag": IMAGE_TAG})
    write_json(
        args.out_dir / "docker_run_command_plan.json",
        {
            "detector_command": detector_run_cmd,
            "image_tag": IMAGE_TAG,
            "smoke_command": smoke_run_cmd,
        },
    )
    write_json(
        args.out_dir / "validator_contract.json",
        {
            "allow_empty_scaffold": True,
            "non_empty_detector_output_required_for_metrics": True,
            "schema": str(schema_path),
            "validator": str(VALIDATOR),
        },
    )
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")

    return 0 if coverage["validator_smoke_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
