#!/usr/bin/env python3
"""Run E003-M22 detector frame-scaling and projection diagnostics."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M22_frame_scaling_projection_diagnostic_v0"
DEFAULT_HF_CACHE = Path.home() / ".cache" / "huggingface"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
DOCKERFILE = DOCKER_DIR / "Dockerfile"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
MATCHER = EXPERIMENT_ROOT / "tools" / "evaluate_m21_detector_matching.py"
IMAGE_TAG = "research2/real-smoke"
BACKEND_ID = "groundingdino_rgbd_backproject_v0"
MODEL_ID = "IDEA-Research/grounding-dino-tiny"
M22_VERSION = "e003_m22_frame_scaling_projection_diagnostic_v0"


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


def docker_command(command: list[str], use_sudo: bool) -> list[str]:
    if not use_sudo:
        return command
    return ["sudo", "-S", "-p", ""] + command


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def summarize_frame_diagnostics(model_status: dict[str, Any], prediction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    inference_rows = model_status.get("inference_rows", [])
    raw_total = sum(int(row.get("raw_prediction_count", 0) or 0) for row in inference_rows)
    written_total = sum(int(row.get("written_prediction_count", 0) or 0) for row in inference_rows)
    skipped_no_depth = sum(int(row.get("skipped_no_depth_prediction_count", 0) or 0) for row in inference_rows)
    frame_count = len(inference_rows)
    frames_with_raw = sum(1 for row in inference_rows if int(row.get("raw_prediction_count", 0) or 0) > 0)
    frames_with_written = sum(1 for row in inference_rows if int(row.get("written_prediction_count", 0) or 0) > 0)
    not_projected_or_capped = max(0, raw_total - written_total - skipped_no_depth)
    labels = Counter(str(row.get("label_canonical")) for row in prediction_rows)
    scans = Counter(str(row.get("scan_id")) for row in prediction_rows)
    return {
        "frame_rows": frame_count,
        "frames_with_raw_predictions": frames_with_raw,
        "frames_with_written_predictions": frames_with_written,
        "not_projected_or_capped_prediction_count": not_projected_or_capped,
        "prediction_labels": dict(sorted(labels.items())),
        "prediction_scans": dict(sorted(scans.items())),
        "raw_prediction_count": raw_total,
        "raw_to_written_rate": safe_rate(written_total, raw_total),
        "scanned_frame_count": int(model_status.get("scanned_frame_count", 0) or 0),
        "skipped_no_depth_prediction_count": skipped_no_depth,
        "skipped_no_depth_rate_vs_raw": safe_rate(skipped_no_depth, raw_total),
        "written_prediction_count": written_total,
    }


def summarize_matching_failures(matched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("match_status")) for row in matched_rows)
    nearest = [
        float(row["nearest_same_label_distance_m"])
        for row in matched_rows
        if row.get("nearest_same_label_distance_m") is not None
    ]
    matched_errors = [
        float(row["match_distance_m"])
        for row in matched_rows
        if row.get("match_distance_m") is not None
    ]
    return {
        "match_status_counts": dict(sorted(status_counts.items())),
        "matched_error_mean_m": mean(matched_errors) if matched_errors else None,
        "nearest_same_label_distance_mean_m": mean(nearest) if nearest else None,
        "rows_with_no_same_label_target": status_counts.get("unmatched_no_same_label_target", 0),
        "rows_with_same_label_but_over_threshold": status_counts.get("unmatched_false_positive", 0),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M22 Frame Scaling Projection Diagnostic",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Docker build executed: {coverage['docker_build_executed']}",
            f"- Docker frame-scaling run executed: {coverage['docker_run_executed']}",
            f"- Max scans: {coverage['run_config']['max_scans']}",
            f"- Max frames per scan: {coverage['run_config']['max_frames_per_scan']}",
            f"- Max predictions per frame: {coverage['run_config']['max_predictions_per_frame']}",
            f"- Scanned frames: {coverage['frame_diagnostics']['scanned_frame_count']}",
            f"- Frames with written predictions: {coverage['frame_diagnostics']['frames_with_written_predictions']}",
            f"- Raw predictions: {coverage['frame_diagnostics']['raw_prediction_count']}",
            f"- Written predictions: {coverage['frame_diagnostics']['written_prediction_count']}",
            f"- Skipped no-depth predictions: {coverage['frame_diagnostics']['skipped_no_depth_prediction_count']}",
            f"- Validator errors/warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matched proposal rows: {coverage['matching_coverage']['matched_proposal_rows']}",
            f"- False-positive proposal rows: {coverage['matching_coverage']['false_positive_proposal_rows']}",
            f"- Proposal precision smoke: {coverage['matching_coverage']['proposal_precision_smoke']}",
            f"- Scan target recall smoke: {coverage['matching_coverage']['scan_target_recall_smoke']}",
            f"- Label-overlap target recall smoke: {coverage['matching_coverage']['label_overlap_target_recall_smoke']}",
            f"- Mean matched centroid error m: {coverage['matching_coverage']['matched_centroid_error_m']['mean']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M22 supports separating frame coverage, projection loss, and matching failure after removing the M20 early stop.",
            "- E003-M22 does not support real RGB-D/open-vocabulary robustness because it is still a small diagnostic run, not a visibility-aware detector benchmark.",
            "",
            "## 에이전트 추론",
            "",
            "- If multi-frame recall remains low while raw predictions are abundant, the bottleneck is likely projection/matching quality or prompt/threshold calibration rather than frame coverage alone.",
            "- The next unit should choose between projection calibration and scaling to more scans based on this diagnostic.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M22 diagnostic.",
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
    parser.add_argument("--max-predictions", default=120, type=int)
    parser.add_argument("--max-predictions-per-frame", default=20, type=int)
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
        "--max-predictions-per-frame",
        str(args.max_predictions_per_frame),
        "--min-predictions",
        "1",
        "--proposal-run-id",
        "m22",
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

    validator_coverage = load_json(validator_out / "coverage.json") if (validator_out / "coverage.json").exists() else {}
    matching_coverage = load_json(matching_out / "coverage.json") if (matching_out / "coverage.json").exists() else {}
    model_status = load_json(model_smoke) if model_smoke.exists() else {}
    backend_payload = load_json(backend_contract) if backend_contract.exists() else {}
    prediction_rows = load_jsonl(predictions) if predictions.exists() else []
    matched_rows = load_jsonl(matching_out / "matched_proposals.jsonl") if (matching_out / "matched_proposals.jsonl").exists() else []

    frame_diagnostics = summarize_frame_diagnostics(model_status, prediction_rows)
    matching_failures = summarize_matching_failures(matched_rows)
    validator_errors = int(validator_coverage.get("error_rows", 0) or 0)
    validator_warnings = int(validator_coverage.get("warning_rows", 0) or 0)

    status = "frame_scaling_projection_diagnostic_ready"
    if not docker_info["available"]:
        status = "docker_daemon_unavailable"
    elif args.build and build_result and not build_result["available"]:
        status = "frame_scaling_docker_build_failed"
    elif not run_result["available"]:
        status = "frame_scaling_docker_run_failed"
    elif validator_result.returncode != 0 or validator_errors:
        status = "frame_scaling_validator_failed"
    elif matching_result.returncode != 0:
        status = "frame_scaling_matching_failed"

    coverage = {
        "backend_contract_ready": bool(backend_payload.get("backend_status", {}).get("valid")),
        "docker_build_executed": build_result is not None,
        "docker_build_result": build_result,
        "docker_info": docker_info,
        "docker_run_executed": run_result["available"],
        "docker_run_result": run_result,
        "frame_diagnostics": frame_diagnostics,
        "image_tag": IMAGE_TAG,
        "m22_version": M22_VERSION,
        "matching_coverage": matching_coverage,
        "matching_failures": matching_failures,
        "matching_result": {
            "returncode": matching_result.returncode,
            "stderr": matching_result.stderr.strip(),
            "stdout": matching_result.stdout.strip(),
        },
        "model_status": model_status,
        "paper_table_command_ready": False,
        "prediction_rows": len(prediction_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_command": run_cmd,
        "run_config": {
            "max_frames_per_scan": args.max_frames_per_scan,
            "max_labels": args.max_labels,
            "max_predictions": args.max_predictions,
            "max_predictions_per_frame": args.max_predictions_per_frame,
            "max_scans": args.max_scans,
            "text_threshold": args.text_threshold,
            "threshold": args.threshold,
        },
        "status": status,
        "validator_coverage": validator_coverage,
        "validator_error_rows": validator_errors,
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr": validator_result.stderr.strip(),
            "stdout": validator_result.stdout.strip(),
        },
        "validator_warning_rows": validator_warnings,
    }

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "docker_frame_scaling_run_plan.json", {"command": run_cmd, "image_tag": IMAGE_TAG})
    write_jsonl(args.out_dir / "frame_diagnostics.jsonl", model_status.get("inference_rows", []))
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0 if status == "frame_scaling_projection_diagnostic_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
