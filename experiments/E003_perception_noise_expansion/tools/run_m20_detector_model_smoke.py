#!/usr/bin/env python3
"""Run E003-M20 detector dependency/model smoke."""

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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M20_detector_model_smoke_v0"
DEFAULT_HF_CACHE = Path.home() / ".cache" / "huggingface"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
IMAGE_TAG = "research2/real-smoke"
BACKEND_ID = "groundingdino_rgbd_backproject_v0"
MODEL_ID = "IDEA-Research/grounding-dino-tiny"
M20_VERSION = "e003_m20_detector_model_smoke_v0"


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


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M20 Detector Model Smoke",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Selected backend: `{coverage['selected_backend_id']}`",
            f"- Model id: `{coverage['model_id']}`",
            f"- Docker image tag: `{coverage['image_tag']}`",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker model smoke executed: {coverage['docker_model_smoke_executed']}",
            f"- Backend contract ready: {coverage['backend_contract_ready']}",
            f"- Model loaded: {coverage['model_loaded']}",
            f"- Inference device: `{coverage['inference_device']}`",
            f"- Scanned frames: {coverage['scanned_frame_count']}",
            f"- Prediction rows: {coverage['prediction_rows']}",
            f"- Validator error rows: {coverage['validator_error_rows']}",
            f"- Validator warning rows: {coverage['validator_warning_rows']}",
            f"- Non-empty detector prediction smoke ready: {coverage['non_empty_detector_prediction_smoke_ready']}",
            f"- Detector backend integrated: {coverage['detector_backend_integrated']}",
            f"- Detector predictions ready: {coverage['detector_predictions_ready']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M20 supports a Dockerized non-empty model prediction smoke for the selected real-detector route.",
            "- E003-M20 supports saying that the selected backend can load dependencies, consume RGB-D sequence inputs, and emit schema-valid proposal rows.",
            "- E003-M20 does not support real perception robustness or proposal-recall claims because outputs are not yet matched/evaluated against the target denominator.",
            "",
            "## 에이전트 추론",
            "",
            "- The next unit should match detector proposals to the M17 target denominator and report proposal recall, false positives, and centroid-localization error.",
            "- M20 should stay a smoke gate, not a paper-table result.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for M20 if the smoke is non-empty and validator-clean.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--hf-cache", default=DEFAULT_HF_CACHE, type=Path)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--docker-sudo", action="store_true")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    parser.add_argument("--max-scans", default=1, type=int)
    parser.add_argument("--max-frames-per-scan", default=6, type=int)
    parser.add_argument("--max-labels", default=12, type=int)
    parser.add_argument("--max-predictions", default=20, type=int)
    parser.add_argument("--threshold", default=0.08, type=float)
    parser.add_argument("--text-threshold", default=0.08, type=float)
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
    args.hf_cache.mkdir(parents=True, exist_ok=True)

    manifest = args.m17_dir / "real_proposal_query_manifest.jsonl"
    targets = args.m17_dir / "real_proposal_object_targets.jsonl"
    prompt_set = args.m17_dir / "prompt_set.json"
    schema = args.m17_dir / "proposal_output_schema.json"
    container_output = args.out_dir / "container_output"
    predictions = container_output / "real_proposals.jsonl"
    backend_contract = container_output / "backend_contract.json"
    model_smoke = container_output / "model_smoke.json"
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
        "-e",
        "HF_HOME=/hf-cache",
        "-e",
        "TRANSFORMERS_CACHE=/hf-cache/transformers",
        "-v",
        f"{args.dataset_root}:/data:ro",
        "-v",
        f"{args.m17_dir}:/inputs:ro",
        "-v",
        f"{container_output}:/outputs",
        "-v",
        f"{args.hf_cache}:/hf-cache",
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
        "model-smoke",
        "--model-id",
        MODEL_ID,
        "--max-scans",
        str(args.max_scans),
        "--max-frames-per-scan",
        str(args.max_frames_per_scan),
        "--max-labels",
        str(args.max_labels),
        "--max-predictions",
        str(args.max_predictions),
        "--min-predictions",
        "1",
        "--threshold",
        str(args.threshold),
        "--text-threshold",
        str(args.text_threshold),
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
    run_result = {"available": False, "returncode": None, "stderr": "docker build unavailable", "stdout": ""}
    if docker_info["available"] and (not args.build or (build_result and build_result["available"])):
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
        "--schema-only-smoke",
    ]
    validator_result = subprocess.run(validator_cmd, check=False, text=True, capture_output=True)
    validator_coverage = load_json(validator_out / "coverage.json") if (validator_out / "coverage.json").exists() else {}
    model_status = load_json(model_smoke) if model_smoke.exists() else {}
    backend_payload = load_json(backend_contract) if backend_contract.exists() else {}
    backend_status = backend_payload.get("backend_status", {})

    prediction_rows = int(validator_coverage.get("prediction_rows", 0) or 0)
    validator_errors = int(validator_coverage.get("error_rows", 0) or 0)
    non_empty_ready = prediction_rows > 0 and validator_errors == 0 and validator_result.returncode == 0

    status = "detector_model_smoke_ready"
    if not docker_info["available"]:
        status = "docker_daemon_unavailable"
    elif args.build and build_result and not build_result["available"]:
        status = "detector_model_smoke_build_failed"
    elif not run_result["available"]:
        status = "detector_model_smoke_run_failed"
    elif not model_status.get("model_loaded"):
        status = "detector_model_smoke_model_load_failed"
    elif not non_empty_ready:
        status = "detector_model_smoke_no_valid_predictions"

    coverage = {
        "backend_contract": str(backend_contract),
        "backend_contract_ready": bool(backend_status.get("valid")),
        "build_command": build_cmd,
        "detector_backend_integrated": bool(model_status.get("detector_backend_integrated")),
        "detector_predictions_ready": bool(non_empty_ready),
        "docker_build_executed": build_result is not None,
        "docker_build_result": build_result,
        "docker_info": docker_info,
        "docker_model_smoke_executed": run_result["available"],
        "docker_run_result": run_result,
        "image_tag": IMAGE_TAG,
        "inference_device": model_status.get("device", "unknown"),
        "manifest_rows": len(manifest_rows),
        "m20_version": M20_VERSION,
        "model_id": MODEL_ID,
        "model_loaded": bool(model_status.get("model_loaded")),
        "model_status": model_status,
        "non_empty_detector_prediction_smoke_ready": bool(non_empty_ready),
        "paper_table_command_ready": False,
        "prediction_rows": prediction_rows,
        "prompt_label_count": len(prompt_payload.get("labels", [])),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_command": run_cmd,
        "scanned_frame_count": model_status.get("scanned_frame_count", 0),
        "selected_backend_id": BACKEND_ID,
        "status": status,
        "validator_coverage": validator_coverage,
        "validator_error_rows": validator_errors,
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr": validator_result.stderr.strip(),
            "stdout": validator_result.stdout.strip(),
        },
        "validator_warning_rows": int(validator_coverage.get("warning_rows", 0) or 0),
    }

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "docker_model_run_plan.json", {"command": run_cmd, "image_tag": IMAGE_TAG})
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")

    return 0 if status == "detector_model_smoke_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
