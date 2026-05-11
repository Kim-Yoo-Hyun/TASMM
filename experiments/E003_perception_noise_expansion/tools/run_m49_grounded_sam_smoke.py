#!/usr/bin/env python3
"""Run E003-M49 Grounded-SAM Docker/model smoke."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M48_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M48_grounded_sam_contract_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M49_grounded_sam_smoke_v0"
DEFAULT_HF_CACHE = Path.home() / ".cache" / "huggingface"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
MATCHER = EXPERIMENT_ROOT / "tools" / "evaluate_m21_detector_matching.py"
IMAGE_TAG = "research2/real-smoke"
BACKEND_ID = "grounded_sam_mask_backproject_v0"
BASE_BACKEND_ID = "groundingdino_rgbd_backproject_v0"
GROUNDINGDINO_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
SAM_MODEL_ID = "facebook/sam-vit-base"
M49_VERSION = "e003_m49_grounded_sam_model_smoke_v0"


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def command_status(command: list[str], input_text: str | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True, input=input_text)
    except FileNotFoundError as exc:
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stderr_tail": str(exc),
            "stdout_tail": "",
        }
    return {
        "available": result.returncode == 0,
        "command": command,
        "returncode": result.returncode,
        "stderr_tail": result.stderr.strip()[-4000:],
        "stdout_tail": result.stdout.strip()[-4000:],
    }


def docker_command(command: list[str], use_sudo: bool) -> list[str]:
    if not use_sudo:
        return command
    return ["sudo", "-S", "-p", ""] + command


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def summarize_masks(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mask_rows = [row for row in rows if row.get("geometry_source") == "mask_depth_backprojection_v0"]
    valid_counts = [
        int(row.get("mask_depth_valid_pixel_count", 0) or 0)
        for row in mask_rows
        if row.get("mask_depth_valid_pixel_count") is not None
    ]
    valid_ratios = [
        float(row.get("mask_depth_valid_ratio"))
        for row in mask_rows
        if row.get("mask_depth_valid_ratio") is not None
    ]
    with_rle = sum(1 for row in mask_rows if row.get("mask_rle"))
    with_bbox_centroid = sum(1 for row in mask_rows if row.get("bbox_centroid_world_m") is not None)
    return {
        "all_prediction_rows_have_mask_geometry": bool(rows) and len(mask_rows) == len(rows),
        "mask_backprojection_policy_rows": sum(
            1 for row in mask_rows if row.get("mask_backprojection_policy") == "median_mad_trimmed_mask_depth_v0"
        ),
        "mask_depth_valid_pixel_count_mean": mean(valid_counts) if valid_counts else None,
        "mask_depth_valid_ratio_mean": mean(valid_ratios) if valid_ratios else None,
        "mask_geometry_rows": len(mask_rows),
        "prediction_rows": len(rows),
        "rows_with_bbox_centroid_diagnostic": with_bbox_centroid,
        "rows_with_mask_rle": with_rle,
    }


def build_report(coverage: dict[str, Any]) -> str:
    matching = coverage.get("matching_coverage", {})
    mask = coverage.get("mask_summary", {})
    return "\n".join(
        [
            "# E003-M49 Grounded-SAM Docker/Model Smoke",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Backend id: `{coverage['backend_id']}`.",
            f"- GroundingDINO model id: `{coverage['groundingdino_model_id']}`.",
            f"- SAM model id: `{coverage['sam_model_id']}`.",
            f"- Docker build executed: {coverage['docker_build_executed']}.",
            f"- Docker run executed: {coverage['docker_run_executed']}.",
            f"- Prediction rows: {coverage['prediction_rows']}.",
            f"- Mask geometry rows: {mask.get('mask_geometry_rows')}.",
            f"- Rows with mask RLE: {mask.get('rows_with_mask_rle')}.",
            f"- Validator errors/warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}.",
            f"- M21 matcher returncode: {coverage['matching_result']['returncode']}.",
            f"- Matched proposal rows: {matching.get('matched_proposal_rows')}.",
            f"- False-positive proposal rows: {matching.get('false_positive_proposal_rows')}.",
            f"- Proposal precision smoke: {matching.get('proposal_precision_smoke')}.",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}.",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M49 supports only a short implementation smoke for `Grounded-SAM` mask-depth proposal rows.",
            "- E003-M49 does not support final real RGB-D/open-vocabulary robustness or search/navigation claims.",
            "",
            "## 에이전트 추론",
            "",
            "- If this smoke is ready, the next defensible step is a same-subset comparison against the current bbox-depth `GroundingDINO` route.",
            "- A positive same-subset result would still require heldout transfer and external baseline scaling before a paper-table claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for the smoke implementation if validator and M21 matcher pass.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m48-dir", default=DEFAULT_M48_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--hf-cache", default=DEFAULT_HF_CACHE, type=Path)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--docker-sudo", action="store_true")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    parser.add_argument("--max-scans", default=1, type=int)
    parser.add_argument("--max-frames-per-scan", default=2, type=int)
    parser.add_argument("--max-labels", default=12, type=int)
    parser.add_argument("--max-predictions", default=400, type=int)
    parser.add_argument("--max-predictions-per-frame", default=20, type=int)
    parser.add_argument("--threshold", default=0.08, type=float)
    parser.add_argument("--text-threshold", default=0.08, type=float)
    parser.add_argument("--mask-min-depth-valid-pixels", default=200, type=int)
    parser.add_argument("--mask-point-sample-cap", default=2048, type=int)
    parser.add_argument("--sam-model-id", default=SAM_MODEL_ID)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m17_dir = args.m17_dir.resolve()
    args.m48_dir = args.m48_dir.resolve()
    args.dataset_root = args.dataset_root.resolve()
    args.out_dir = args.out_dir.resolve()
    args.hf_cache = args.hf_cache.resolve()

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
    matching_out = args.out_dir / "matching"

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
        "HF_HUB_DISABLE_PROGRESS_BARS=1",
        "-e",
        "TRANSFORMERS_CACHE=/hf-cache/transformers",
        "-e",
        "TRANSFORMERS_VERBOSITY=error",
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
        GROUNDINGDINO_MODEL_ID,
        "--segmentation-backend",
        "sam_vit_b",
        "--sam-model-id",
        args.sam_model_id,
        "--mask-depth-filter",
        "median_mad_trimmed_mask_depth_v0",
        "--mask-min-depth-valid-pixels",
        str(args.mask_min_depth_valid_pixels),
        "--mask-point-sample-cap",
        str(args.mask_point_sample_cap),
        "--max-scans",
        str(args.max_scans),
        "--max-frames-per-scan",
        str(args.max_frames_per_scan),
        "--max-labels",
        str(args.max_labels),
        "--max-predictions",
        str(args.max_predictions),
        "--max-predictions-per-frame",
        str(args.max_predictions_per_frame),
        "--min-predictions",
        "1",
        "--proposal-run-id",
        "m49",
        "--continue-after-min-predictions",
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
    run_result = {"available": False, "returncode": None, "stderr_tail": "docker build unavailable", "stdout_tail": ""}
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

    matching_cmd = [
        sys.executable,
        str(MATCHER),
        "--m17-dir",
        str(args.m17_dir),
        "--m20-dir",
        str(args.out_dir),
        "--out-dir",
        str(matching_out),
    ]
    matching_result = subprocess.run(matching_cmd, check=False, text=True, capture_output=True)

    prediction_rows = load_jsonl(predictions) if predictions.exists() else []
    validator_coverage = load_json(validator_out / "coverage.json") if (validator_out / "coverage.json").exists() else {}
    matching_coverage = load_json(matching_out / "coverage.json") if (matching_out / "coverage.json").exists() else {}
    model_status = load_json(model_smoke) if model_smoke.exists() else {}
    backend_payload = load_json(backend_contract) if backend_contract.exists() else {}
    m48_contract = load_json(args.m48_dir / "contract.json") if (args.m48_dir / "contract.json").exists() else {}
    mask_summary = summarize_masks(prediction_rows)

    validator_errors = int(validator_coverage.get("error_rows", 0) or 0)
    validator_warnings = int(validator_coverage.get("warning_rows", 0) or 0)
    ready = (
        bool(prediction_rows)
        and mask_summary["all_prediction_rows_have_mask_geometry"]
        and validator_result.returncode == 0
        and validator_errors == 0
        and matching_result.returncode == 0
    )
    status = "grounded_sam_model_smoke_ready"
    if not docker_info["available"]:
        status = "docker_daemon_unavailable"
    elif args.build and build_result and not build_result["available"]:
        status = "grounded_sam_docker_build_failed"
    elif not run_result["available"]:
        status = "grounded_sam_docker_run_failed"
    elif validator_result.returncode != 0 or validator_errors:
        status = "grounded_sam_validator_failed"
    elif matching_result.returncode != 0:
        status = "grounded_sam_matching_failed"
    elif not prediction_rows:
        status = "grounded_sam_no_predictions"
    elif not mask_summary["all_prediction_rows_have_mask_geometry"]:
        status = "grounded_sam_mask_geometry_incomplete"

    coverage = {
        "backend_contract": backend_payload,
        "backend_id": BACKEND_ID,
        "base_backend_id": BASE_BACKEND_ID,
        "docker_build_executed": build_result is not None,
        "docker_build_result": build_result,
        "docker_info": docker_info,
        "docker_run_executed": run_result["available"],
        "docker_run_result": run_result,
        "expected_files": [
            "container_output/real_proposals.jsonl",
            "container_output/backend_contract.json",
            "container_output/model_smoke.json",
            "validator/coverage.json",
            "matching/coverage.json",
            "coverage.json",
        ],
        "groundingdino_model_id": GROUNDINGDINO_MODEL_ID,
        "m48_contract_id": m48_contract.get("contract_id"),
        "m49_version": M49_VERSION,
        "mask_summary": mask_summary,
        "matching_coverage": matching_coverage,
        "matching_result": {
            "returncode": matching_result.returncode,
            "stderr_tail": matching_result.stderr.strip()[-4000:],
            "stdout_tail": matching_result.stdout.strip()[-4000:],
        },
        "model_status": model_status,
        "next_recommended_unit": "E003-M50 same-subset bbox-depth vs mask-depth comparison gate",
        "output_path": str(args.out_dir),
        "paper_table_command_ready": False,
        "prediction_rows": len(prediction_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_command": run_cmd,
        "run_config": {
            "mask_min_depth_valid_pixels": args.mask_min_depth_valid_pixels,
            "mask_point_sample_cap": args.mask_point_sample_cap,
            "max_frames_per_scan": args.max_frames_per_scan,
            "max_labels": args.max_labels,
            "max_predictions": args.max_predictions,
            "max_predictions_per_frame": args.max_predictions_per_frame,
            "max_scans": args.max_scans,
            "text_threshold": args.text_threshold,
            "threshold": args.threshold,
        },
        "sam_model_id": args.sam_model_id,
        "status": status,
        "validator_coverage": validator_coverage,
        "validator_error_rows": validator_errors,
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr_tail": validator_result.stderr.strip()[-4000:],
            "stdout_tail": validator_result.stdout.strip()[-4000:],
        },
        "validator_warning_rows": validator_warnings,
        "verification_command": (
            "python -m json.tool "
            "experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0/coverage.json"
        ),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "docker_grounded_sam_run_plan.json", {"command": run_cmd, "image_tag": IMAGE_TAG})
    write_jsonl(args.out_dir / "mask_summary_rows.jsonl", [mask_summary])
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
