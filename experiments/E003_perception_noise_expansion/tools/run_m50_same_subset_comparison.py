#!/usr/bin/env python3
"""Run E003-M50 same-subset bbox-depth vs mask-depth comparison gate."""

from __future__ import annotations

import argparse
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
DEFAULT_M49_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M49_grounded_sam_smoke_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M50_same_subset_bbox_vs_mask_v0"
DEFAULT_HF_CACHE = Path.home() / ".cache" / "huggingface"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "real_proposals"
VALIDATOR = EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py"
MATCHER = EXPERIMENT_ROOT / "tools" / "evaluate_m21_detector_matching.py"
IMAGE_TAG = "research2/real-smoke"
BBOX_BACKEND_ID = "groundingdino_rgbd_backproject_v0"
MASK_BACKEND_ID = "grounded_sam_mask_backproject_v0"
GROUNDINGDINO_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
M50_VERSION = "e003_m50_same_subset_bbox_vs_mask_v0"


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


def command_status(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
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


def metric_block(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "false_positive_proposal_rows": coverage.get("false_positive_proposal_rows"),
        "input_prediction_rows": coverage.get("input_prediction_rows"),
        "label_overlap_target_recall_smoke": coverage.get("label_overlap_target_recall_smoke"),
        "matched_centroid_error_mean_m": (coverage.get("matched_centroid_error_m") or {}).get("mean"),
        "matched_proposal_rows": coverage.get("matched_proposal_rows"),
        "matched_target_rows": coverage.get("matched_target_rows"),
        "proposal_precision_smoke": coverage.get("proposal_precision_smoke"),
        "scan_target_recall_smoke": coverage.get("scan_target_recall_smoke"),
        "status": coverage.get("status"),
    }


def numeric_delta(mask_value: Any, bbox_value: Any) -> float | None:
    if mask_value is None or bbox_value is None:
        return None
    return float(mask_value) - float(bbox_value)


def compare_metrics(mask_metrics: dict[str, Any], bbox_metrics: dict[str, Any]) -> dict[str, Any]:
    delta = {
        key: numeric_delta(mask_metrics.get(key), bbox_metrics.get(key))
        for key in [
            "false_positive_proposal_rows",
            "input_prediction_rows",
            "label_overlap_target_recall_smoke",
            "matched_centroid_error_mean_m",
            "matched_proposal_rows",
            "matched_target_rows",
            "proposal_precision_smoke",
            "scan_target_recall_smoke",
        ]
    }
    matched_not_worse = (
        mask_metrics.get("matched_target_rows") is not None
        and bbox_metrics.get("matched_target_rows") is not None
        and int(mask_metrics["matched_target_rows"]) >= int(bbox_metrics["matched_target_rows"])
    )
    false_positive_not_worse = (
        mask_metrics.get("false_positive_proposal_rows") is not None
        and bbox_metrics.get("false_positive_proposal_rows") is not None
        and int(mask_metrics["false_positive_proposal_rows"]) <= int(bbox_metrics["false_positive_proposal_rows"])
    )
    precision_better = (
        mask_metrics.get("proposal_precision_smoke") is not None
        and bbox_metrics.get("proposal_precision_smoke") is not None
        and float(mask_metrics["proposal_precision_smoke"]) > float(bbox_metrics["proposal_precision_smoke"])
    )
    centroid_better = (
        mask_metrics.get("matched_centroid_error_mean_m") is not None
        and bbox_metrics.get("matched_centroid_error_mean_m") is not None
        and float(mask_metrics["matched_centroid_error_mean_m"]) < float(bbox_metrics["matched_centroid_error_mean_m"])
    )
    weak_positive = matched_not_worse and (false_positive_not_worse or precision_better or centroid_better)
    hard_positive = matched_not_worse and false_positive_not_worse and (precision_better or centroid_better)
    return {
        "delta_mask_minus_bbox": delta,
        "false_positive_not_worse": false_positive_not_worse,
        "hard_positive": hard_positive,
        "matched_not_worse": matched_not_worse,
        "precision_better": precision_better,
        "centroid_better": centroid_better,
        "weak_positive": weak_positive,
    }


def build_report(coverage: dict[str, Any]) -> str:
    bbox = coverage["bbox_depth_metrics"]
    mask = coverage["mask_depth_metrics"]
    decision = coverage["route_decision"]
    return "\n".join(
        [
            "# E003-M50 Same-Subset Bbox-Depth Vs Mask-Depth",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Bbox-depth backend: `{coverage['bbox_backend_id']}`.",
            f"- Mask-depth backend: `{coverage['mask_backend_id']}`.",
            f"- Same-subset config: max scans {coverage['run_config']['max_scans']}, frames {coverage['run_config']['max_frames_per_scan']}, labels {coverage['run_config']['max_labels']}.",
            f"- Bbox prediction rows: {bbox.get('input_prediction_rows')}.",
            f"- Mask prediction rows: {mask.get('input_prediction_rows')}.",
            f"- Bbox matched / FP / precision: {bbox.get('matched_target_rows')} / {bbox.get('false_positive_proposal_rows')} / {bbox.get('proposal_precision_smoke')}.",
            f"- Mask matched / FP / precision: {mask.get('matched_target_rows')} / {mask.get('false_positive_proposal_rows')} / {mask.get('proposal_precision_smoke')}.",
            f"- Bbox mean matched centroid error m: {bbox.get('matched_centroid_error_mean_m')}.",
            f"- Mask mean matched centroid error m: {mask.get('matched_centroid_error_mean_m')}.",
            f"- Weak positive: {coverage['comparison']['weak_positive']}.",
            f"- Hard positive: {coverage['comparison']['hard_positive']}.",
            f"- Selected next route: `{decision['selected_next_route']}`.",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M50 is a same-subset diagnostic gate, not a final robustness result.",
            "- It does not support real RGB-D/open-vocabulary robustness, heldout transfer, or navigation/search claims.",
            "",
            "## 에이전트 추론",
            "",
            f"- {decision['reason']}",
            "- The next route should be chosen from this gate before any scaled `Grounded-SAM` rerun.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if the selected next route is accepted.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m49-dir", default=DEFAULT_M49_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--hf-cache", default=DEFAULT_HF_CACHE, type=Path)
    parser.add_argument("--build", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m17_dir = args.m17_dir.resolve()
    args.m49_dir = args.m49_dir.resolve()
    args.dataset_root = args.dataset_root.resolve()
    args.out_dir = args.out_dir.resolve()
    args.hf_cache = args.hf_cache.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.hf_cache.mkdir(parents=True, exist_ok=True)

    m49_coverage = load_json(args.m49_dir / "coverage.json")
    m49_run_config = m49_coverage["run_config"]
    bbox_out = args.out_dir / "bbox_depth_baseline"
    container_output = bbox_out / "container_output"
    predictions = container_output / "real_proposals.jsonl"
    validator_out = bbox_out / "validator"
    matching_out = bbox_out / "matching"

    manifest = args.m17_dir / "real_proposal_query_manifest.jsonl"
    targets = args.m17_dir / "real_proposal_object_targets.jsonl"
    prompt_set = args.m17_dir / "prompt_set.json"
    schema = args.m17_dir / "proposal_output_schema.json"

    docker_info = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    build_result = None
    if args.build and docker_info["available"]:
        build_result = command_status(
            [
                "docker",
                "build",
                "-f",
                str(DOCKER_DIR / "Dockerfile"),
                "-t",
                IMAGE_TAG,
                str(DOCKER_DIR),
            ]
        )

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
        BBOX_BACKEND_ID,
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
        "none",
        "--max-scans",
        str(m49_run_config["max_scans"]),
        "--max-frames-per-scan",
        str(m49_run_config["max_frames_per_scan"]),
        "--max-labels",
        str(m49_run_config["max_labels"]),
        "--max-predictions",
        str(m49_run_config["max_predictions"]),
        "--max-predictions-per-frame",
        str(m49_run_config["max_predictions_per_frame"]),
        "--min-predictions",
        "1",
        "--proposal-run-id",
        "m50_bbox",
        "--continue-after-min-predictions",
        "--threshold",
        str(m49_run_config["threshold"]),
        "--text-threshold",
        str(m49_run_config["text_threshold"]),
        "--seed",
        "101",
    ]

    container_output.mkdir(parents=True, exist_ok=True)
    run_result = {"available": False, "returncode": None, "stderr_tail": "docker unavailable", "stdout_tail": ""}
    if docker_info["available"] and (not args.build or (build_result and build_result["available"])):
        run_result = command_status(run_cmd)

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
        str(bbox_out),
        "--out-dir",
        str(matching_out),
    ]
    matching_result = subprocess.run(matching_cmd, check=False, text=True, capture_output=True)

    bbox_matching = load_json(matching_out / "coverage.json") if (matching_out / "coverage.json").exists() else {}
    bbox_validator = load_json(validator_out / "coverage.json") if (validator_out / "coverage.json").exists() else {}
    bbox_model = load_json(container_output / "model_smoke.json") if (container_output / "model_smoke.json").exists() else {}
    mask_matching = m49_coverage.get("matching_coverage") or {}
    bbox_metrics = metric_block(bbox_matching)
    mask_metrics = metric_block(mask_matching)
    comparison = compare_metrics(mask_metrics=mask_metrics, bbox_metrics=bbox_metrics)

    if comparison["hard_positive"]:
        selected_next = "grounded_sam_scaled_rerun_candidate"
        reason = "Mask-depth is not worse on matched targets and false positives, and improves precision or matched centroid error on the same subset."
    elif comparison["weak_positive"]:
        selected_next = "grounded_sam_same_subset_extension_before_scaled_rerun"
        reason = "Mask-depth has a weak positive signal, but the evidence is too small for scaled rerun without another same-subset extension."
    else:
        selected_next = "do_not_scale_grounded_sam_yet"
        reason = "Mask-depth does not beat the bbox-depth route on the same subset; scaling now would be a weak use of compute."

    bbox_ready = (
        run_result["available"]
        and validator_result.returncode == 0
        and int(bbox_validator.get("error_rows", 0) or 0) == 0
        and matching_result.returncode == 0
        and bool(bbox_matching)
    )
    status = "same_subset_comparison_ready" if bbox_ready else "same_subset_comparison_failed"

    coverage = {
        "bbox_backend_id": BBOX_BACKEND_ID,
        "bbox_depth_metrics": bbox_metrics,
        "bbox_depth_model_status": bbox_model,
        "bbox_depth_output": str(bbox_out),
        "bbox_depth_validator": bbox_validator,
        "build_result": build_result,
        "comparison": comparison,
        "docker_info": docker_info,
        "docker_run_result": run_result,
        "m49_mask_depth_output": str(args.m49_dir),
        "m50_version": M50_VERSION,
        "mask_backend_id": MASK_BACKEND_ID,
        "mask_depth_metrics": mask_metrics,
        "next_recommended_unit": "E003-M51 route decision after same-subset comparison",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "route_decision": {
            "reason": reason,
            "selected_next_route": selected_next,
        },
        "run_command": run_cmd,
        "run_config": {
            "max_frames_per_scan": m49_run_config["max_frames_per_scan"],
            "max_labels": m49_run_config["max_labels"],
            "max_predictions": m49_run_config["max_predictions"],
            "max_predictions_per_frame": m49_run_config["max_predictions_per_frame"],
            "max_scans": m49_run_config["max_scans"],
            "text_threshold": m49_run_config["text_threshold"],
            "threshold": m49_run_config["threshold"],
        },
        "status": status,
        "validator_result": {
            "returncode": validator_result.returncode,
            "stderr_tail": validator_result.stderr.strip()[-4000:],
            "stdout_tail": validator_result.stdout.strip()[-4000:],
        },
        "matching_result": {
            "returncode": matching_result.returncode,
            "stderr_tail": matching_result.stderr.strip()[-4000:],
            "stdout_tail": matching_result.stdout.strip()[-4000:],
        },
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "bbox_depth_run_plan.json", {"command": run_cmd, "image_tag": IMAGE_TAG})
    write_jsonl(
        args.out_dir / "comparison_rows.jsonl",
        [
            {"backend": "bbox_depth", **bbox_metrics},
            {"backend": "mask_depth", **mask_metrics},
            {"backend": "delta_mask_minus_bbox", **comparison["delta_mask_minus_bbox"]},
        ],
    )
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0 if bbox_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
