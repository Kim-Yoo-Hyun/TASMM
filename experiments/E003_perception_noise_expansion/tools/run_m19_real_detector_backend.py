#!/usr/bin/env python3
"""Run E003-M19 real detector backend contract integration."""

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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M19_real_detector_backend_integration_v0"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
IMAGE_TAG = "research2/real-smoke"
BACKEND_ID = "groundingdino_rgbd_backproject_v0"
M19_VERSION = "e003_m19_real_detector_backend_integration_v0"


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
    result = subprocess.run(command, check=False, text=True, capture_output=True, input=input_text)
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


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M19 Real Detector Backend Integration",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Selected backend: `{coverage['selected_backend_id']}`",
            f"- Docker image tag: `{coverage['image_tag']}`",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker backend contract smoke executed: {coverage['docker_backend_contract_smoke_executed']}",
            f"- Backend contract ready: {coverage['backend_contract_ready']}",
            f"- RGB-D frame triplets ready: {coverage['rgbd_triplets_ready']}",
            f"- RGB-D frame triplets missing: {coverage['rgbd_triplets_missing']}",
            f"- Manifest rows: {coverage['manifest_rows']}",
            f"- Prompt labels: {coverage['prompt_label_count']}",
            f"- Detector backend integrated: {coverage['detector_backend_integrated']}",
            f"- Detector predictions ready: {coverage['detector_predictions_ready']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M19 supports selecting a concrete real-detector backend contract and connecting it to the Docker runner.",
            "- E003-M19 supports saying that E003-M17 RGB-D frames, depth, poses, and prompts are consumable by the selected backend route.",
            "- E003-M19 does not support detector performance or real perception robustness because model inference is not integrated yet.",
            "",
            "## 에이전트 추론",
            "",
            "- `groundingdino_rgbd_backproject_v0` is a practical first backend contract because it separates open-vocabulary 2D detection from RGB-D 3D projection.",
            "- The contract explicitly blocks evaluation-only 3DSSG instance ids from detector inference.",
            "- The next unit should add model dependencies and run a small non-empty detector prediction smoke.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M19. Next is detector dependency/model smoke.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--docker-sudo", action="store_true")
    parser.add_argument("--sudo-password-stdin", action="store_true")
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
    manifest = args.m17_dir / "real_proposal_query_manifest.jsonl"
    targets = args.m17_dir / "real_proposal_object_targets.jsonl"
    prompt_set = args.m17_dir / "prompt_set.json"
    schema = args.m17_dir / "proposal_output_schema.json"
    container_output = args.out_dir / "container_output"
    predictions = container_output / "real_proposals.jsonl"
    backend_contract = container_output / "backend_contract.json"
    validator_out = args.out_dir / "validator"

    manifest_rows = load_jsonl(manifest)
    prompt_payload = load_json(prompt_set)

    build_cmd = [
        "docker",
        "build",
        "-f",
        str(DOCKERFILE),
        "-t",
        IMAGE_TAG,
        str(DOCKER_DIR),
    ]
    run_cmd = [
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
        f"{container_output}:/outputs",
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
        BACKEND_ID,
        "--prompt-set",
        "/inputs/prompt_set.json",
        "--dataset-root",
        "/data",
        "--backend-contract-output",
        "/outputs/backend_contract.json",
        "--mode",
        "backend-contract-smoke",
        "--seed",
        "101",
    ]

    docker_info = command_status(
        docker_command(["docker", "info", "--format", "{{.ServerVersion}}"], args.docker_sudo),
        input_text=sudo_input,
    )
    build_result: dict[str, Any] | None = None
    if args.build and docker_info["available"]:
        build_result = command_status(docker_command(build_cmd, args.docker_sudo), input_text=sudo_input)

    container_output.mkdir(parents=True, exist_ok=True)
    run_result = command_status(docker_command(run_cmd, args.docker_sudo), input_text=sudo_input)

    validator_cmd = [
        sys.executable,
        str(VALIDATOR),
        "--predictions",
        str(predictions),
        "--manifest",
        str(manifest),
        "--targets",
        str(targets),
        "--schema",
        str(schema),
        "--out-dir",
        str(validator_out),
        "--allow-empty-scaffold",
    ]
    validator_result = subprocess.run(validator_cmd, check=False, text=True, capture_output=True)
    validator_coverage = load_json(validator_out / "coverage.json") if (validator_out / "coverage.json").exists() else {}
    backend_payload = load_json(backend_contract) if backend_contract.exists() else {}
    backend_status = backend_payload.get("backend_status", {})

    status = "real_detector_backend_contract_ready"
    if not run_result["available"]:
        status = "real_detector_backend_contract_failed"
    elif not backend_status.get("valid"):
        status = "real_detector_backend_contract_invalid"

    coverage = {
        "backend_contract": str(backend_contract),
        "backend_contract_ready": bool(backend_status.get("valid")),
        "build_command": build_cmd,
        "detector_backend_integrated": False,
        "detector_predictions_ready": False,
        "docker_backend_contract_smoke_executed": run_result["available"],
        "docker_build_executed": build_result is not None,
        "docker_build_result": build_result,
        "docker_info": docker_info,
        "docker_run_result": run_result,
        "image_tag": IMAGE_TAG,
        "manifest_rows": len(manifest_rows),
        "m19_version": M19_VERSION,
        "paper_table_command_ready": False,
        "prediction_rows": validator_coverage.get("prediction_rows", 0),
        "prompt_label_count": len(prompt_payload.get("labels", [])),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "rgbd_triplets_missing": backend_status.get("total_missing_triplets"),
        "rgbd_triplets_ready": backend_status.get("total_ready_triplets"),
        "run_command": run_cmd,
        "selected_backend_id": BACKEND_ID,
        "status": status,
        "validator_coverage": validator_coverage,
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr": validator_result.stderr.strip(),
            "stdout": validator_result.stdout.strip(),
        },
    }

    write_json(args.out_dir / "backend_decision.json", backend_payload)
    write_json(args.out_dir / "docker_backend_run_plan.json", {"command": run_cmd, "image_tag": IMAGE_TAG})
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")

    return 0 if status == "real_detector_backend_contract_ready" and validator_result.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
