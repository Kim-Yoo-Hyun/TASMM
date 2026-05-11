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
SUPPORT_EVIDENCE_NONE = "none"
SUPPORT_EVIDENCE_POLICY_ID = "temporal_spatial_support_evidence_v0"
SUPPORT_AWARE_SCORE_MODE = "confidence_sqrt_depth_support_temporal_v0"


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


def support_radius_suffix(radius_m: float) -> str:
    return str(radius_m).replace(".", "p")


def parse_support_radii_m(value: str) -> list[float]:
    return sorted({float(item.strip()) for item in value.split(",") if item.strip()})


def summarize_support_evidence(
    prediction_rows: list[dict[str, Any]],
    support_summary: dict[str, Any],
    support_evidence_policy: str,
    support_evidence_radii_m: str,
) -> dict[str, Any]:
    enabled = support_evidence_policy != SUPPORT_EVIDENCE_NONE
    if not enabled:
        return {
            "enabled": False,
            "ready": True,
            "row_field_error_count": 0,
            "rows_with_support_policy": 0,
        }

    radii_m = parse_support_radii_m(support_evidence_radii_m)
    base_fields = [
        "support_evidence_policy",
        "support_group_candidate_count",
        "support_group_frame_count",
        "support_group_key",
    ]
    radius_fields = []
    for radius in radii_m:
        suffix = support_radius_suffix(radius)
        radius_fields.extend(
            [
                f"support_spatial_neighbor_count_r{suffix}m",
                f"support_temporal_neighbor_frame_count_r{suffix}m",
                f"support_max_neighbor_confidence_r{suffix}m",
            ]
        )

    row_field_errors = []
    rows_with_policy = 0
    rows_with_spatial_support = 0
    rows_with_temporal_support = 0
    for row_index, row in enumerate(prediction_rows, start=1):
        if row.get("support_evidence_policy") == support_evidence_policy:
            rows_with_policy += 1
        missing = [field for field in [*base_fields, *radius_fields] if field not in row]
        if missing:
            row_field_errors.append({"missing_fields": missing, "row_index": row_index})
            continue
        row_has_spatial_support = False
        row_has_temporal_support = False
        for radius in radii_m:
            suffix = support_radius_suffix(radius)
            spatial = row.get(f"support_spatial_neighbor_count_r{suffix}m")
            temporal = row.get(f"support_temporal_neighbor_frame_count_r{suffix}m")
            if not isinstance(spatial, int) or spatial < 0:
                row_field_errors.append(
                    {"field": f"support_spatial_neighbor_count_r{suffix}m", "issue": "invalid_count", "row_index": row_index}
                )
            if not isinstance(temporal, int) or temporal < 0:
                row_field_errors.append(
                    {"field": f"support_temporal_neighbor_frame_count_r{suffix}m", "issue": "invalid_count", "row_index": row_index}
                )
            row_has_spatial_support = row_has_spatial_support or bool(isinstance(spatial, int) and spatial > 0)
            row_has_temporal_support = row_has_temporal_support or bool(isinstance(temporal, int) and temporal > 0)
        rows_with_spatial_support += int(row_has_spatial_support)
        rows_with_temporal_support += int(row_has_temporal_support)

    summary_policy = support_summary.get("support_evidence_policy")
    summary_selected_rows = int(support_summary.get("support_evidence_attached_to_selected_rows", 0) or 0)
    ready = (
        rows_with_policy > 0
        and summary_policy == support_evidence_policy
        and summary_selected_rows == rows_with_policy
        and not row_field_errors
    )
    return {
        "enabled": True,
        "ready": ready,
        "row_field_error_count": len(row_field_errors),
        "row_field_error_examples": row_field_errors[:10],
        "rows_with_spatial_support": rows_with_spatial_support,
        "rows_with_support_policy": rows_with_policy,
        "rows_with_temporal_support": rows_with_temporal_support,
        "support_evidence_policy": support_evidence_policy,
        "support_evidence_radii_m": radii_m,
        "support_summary": support_summary,
    }


def summarize_candidate_pool_export(
    candidate_pool_rows: list[dict[str, Any]],
    pre_cap_policy_summary: dict[str, Any],
    *,
    export_enabled: bool,
    output_path: Path,
    support_evidence_policy: str,
) -> dict[str, Any]:
    if not export_enabled:
        return {
            "enabled": False,
            "ready": True,
            "candidate_pool_rows": 0,
        }

    required_fields = [
        "scan_id",
        "frame_ids",
        "label_canonical",
        "centroid_world_m",
        "confidence",
        "depth_valid_pixel_count",
        "raw_candidate_uid",
    ]
    if support_evidence_policy == SUPPORT_EVIDENCE_POLICY_ID:
        required_fields.extend(
            [
                "support_evidence_policy",
                "support_spatial_neighbor_count_r1p0m",
                "support_temporal_neighbor_frame_count_r2p0m",
            ]
        )
    field_errors = []
    for row_index, row in enumerate(candidate_pool_rows, start=1):
        missing = [field for field in required_fields if field not in row]
        if missing:
            field_errors.append({"missing_fields": missing, "row_index": row_index})
            if len(field_errors) >= 10:
                break

    expected_rows = int(pre_cap_policy_summary.get("policy_input_candidate_count", 0) or 0)
    rows_with_support_policy = sum(
        1 for row in candidate_pool_rows if row.get("support_evidence_policy") == support_evidence_policy
    )
    ready = (
        output_path.exists()
        and len(candidate_pool_rows) > 0
        and len(candidate_pool_rows) == expected_rows
        and not field_errors
        and (
            support_evidence_policy != SUPPORT_EVIDENCE_POLICY_ID
            or rows_with_support_policy == len(candidate_pool_rows)
        )
    )
    return {
        "enabled": True,
        "ready": ready,
        "candidate_pool_rows": len(candidate_pool_rows),
        "expected_policy_input_candidate_count": expected_rows,
        "field_error_count": len(field_errors),
        "field_error_examples": field_errors,
        "output": str(output_path),
        "rows_with_support_policy": rows_with_support_policy,
    }


def build_report(coverage: dict[str, Any]) -> str:
    matching = coverage.get("matching_coverage", {})
    centroid_error = matching.get("matched_centroid_error_m", {})
    support = coverage.get("support_evidence", {})
    candidate_pool = coverage.get("candidate_pool_export", {})
    support_enabled = coverage.get("run_config", {}).get("support_evidence_policy") != SUPPORT_EVIDENCE_NONE
    support_aware = coverage.get("run_config", {}).get("selection_score_mode") == SUPPORT_AWARE_SCORE_MODE
    candidate_pool_enabled = bool(coverage.get("run_config", {}).get("export_pre_cap_candidate_pool"))
    title = (
        "# E003-M44 Pre-Cap Candidate-Pool Export Smoke"
        if candidate_pool_enabled
        else "# E003-M42 Support-Aware Selection Runner Smoke"
        if support_aware
        else "# E003-M40 Temporal-Spatial Support Runner Smoke"
        if support_enabled
        else "# E003-M22 Frame Scaling Projection Diagnostic"
    )
    claim_lines = (
        [
            "- E003-M44 supports runner-side export of the cleaned pre-cap candidate pool for offline replay.",
            "- E003-M44 does not support final real RGB-D/open-vocabulary robustness because it is a short export/replay smoke.",
        ]
        if candidate_pool_enabled
        else
        [
            "- E003-M42 supports a short runner smoke for the selected support-aware score mode.",
            "- E003-M42 does not support final real RGB-D/open-vocabulary robustness because it is not a scaled heldout evaluation.",
        ]
        if support_aware
        else [
            "- E003-M40 supports runner-side instrumentation of temporal/spatial proposal support evidence.",
            "- E003-M40 does not support final real RGB-D/open-vocabulary robustness because it is a short smoke, not a heldout policy evaluation.",
        ]
        if support_enabled
        else [
            "- E003-M22 supports separating frame coverage, projection loss, and matching failure after removing the M20 early stop.",
            "- E003-M22 does not support real RGB-D/open-vocabulary robustness because it is still a small diagnostic run, not a visibility-aware detector benchmark.",
        ]
    )
    inference_lines = (
        [
            "- The candidate pool should allow score-mode ablations without repeating detector inference.",
            "- The next check is whether offline replay reproduces the runner-selected stable candidates.",
        ]
        if candidate_pool_enabled
        else
        [
            "- The next decision should compare this smoke against E003-M40 before committing to a longer rerun.",
            "- A scaled claim still requires recall-preserving false-positive reduction beyond this short smoke.",
        ]
        if support_aware
        else [
            "- Support evidence is now available before downstream support-aware selection or scaled reruns.",
            "- The next unit should test whether the support fields can reduce false positives without losing matched targets.",
        ]
        if support_enabled
        else [
            "- If multi-frame recall remains low while raw predictions are abundant, the bottleneck is likely projection/matching quality or prompt/threshold calibration rather than frame coverage alone.",
            "- The next unit should choose between projection calibration and scaling to more scans based on this diagnostic.",
        ]
    )
    user_line = (
        "- None for E003-M44 smoke."
        if candidate_pool_enabled
        else "- None for E003-M42 smoke."
        if support_aware
        else "- None for E003-M40 smoke."
        if support_enabled
        else "- None for E003-M22 diagnostic."
    )
    return "\n".join(
        [
            title,
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
            f"- Candidate selection policy: `{coverage['run_config']['candidate_selection_policy']}`",
            f"- Selection score mode: `{coverage['run_config']['selection_score_mode']}`",
            f"- Support evidence policy: `{coverage['run_config']['support_evidence_policy']}`",
            f"- Scanned frames: {coverage['frame_diagnostics']['scanned_frame_count']}",
            f"- Frames with written predictions: {coverage['frame_diagnostics']['frames_with_written_predictions']}",
            f"- Raw predictions: {coverage['frame_diagnostics']['raw_prediction_count']}",
            f"- Written predictions: {coverage['frame_diagnostics']['written_prediction_count']}",
            f"- Support evidence ready: {support.get('ready')}",
            f"- Rows with support policy: {support.get('rows_with_support_policy')}",
            f"- Support row field errors: {support.get('row_field_error_count')}",
            f"- Candidate pool export ready: {candidate_pool.get('ready')}",
            f"- Candidate pool rows: {candidate_pool.get('candidate_pool_rows')}",
            f"- Candidate pool field errors: {candidate_pool.get('field_error_count')}",
            f"- Skipped no-depth predictions: {coverage['frame_diagnostics']['skipped_no_depth_prediction_count']}",
            f"- Validator errors/warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}",
            f"- Matched proposal rows: {matching.get('matched_proposal_rows')}",
            f"- False-positive proposal rows: {matching.get('false_positive_proposal_rows')}",
            f"- Proposal precision smoke: {matching.get('proposal_precision_smoke')}",
            f"- Scan target recall smoke: {matching.get('scan_target_recall_smoke')}",
            f"- Label-overlap target recall smoke: {matching.get('label_overlap_target_recall_smoke')}",
            f"- Mean matched centroid error m: {centroid_error.get('mean')}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            *claim_lines,
            "",
            "## 에이전트 추론",
            "",
            *inference_lines,
            "",
            "## 사용자 판단 필요",
            "",
            user_line,
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
    parser.add_argument(
        "--candidate-selection-policy",
        choices=["detector_order_v0", "cap_aware_label_balanced_ranking_v0"],
        default="detector_order_v0",
    )
    parser.add_argument(
        "--selection-score-mode",
        choices=["confidence", "confidence_log_depth", "confidence_sqrt_depth", SUPPORT_AWARE_SCORE_MODE],
        default="confidence",
    )
    parser.add_argument("--pre-cap-per-scan-label-cap", default=24, type=int)
    parser.add_argument("--pre-cap-spatial-consolidation-radius-m", default=0.5, type=float)
    parser.add_argument("--raw-candidate-collection-cap", default=50000, type=int)
    parser.add_argument("--no-require-scan-prompt-label", action="store_true")
    parser.add_argument(
        "--support-evidence-policy",
        choices=[SUPPORT_EVIDENCE_NONE, SUPPORT_EVIDENCE_POLICY_ID],
        default=SUPPORT_EVIDENCE_NONE,
    )
    parser.add_argument("--support-evidence-radii-m", default="0.75,1.0,1.5,2.0")
    parser.add_argument("--export-pre-cap-candidate-pool", action="store_true")
    args = parser.parse_args()

    args.m17_dir = args.m17_dir.resolve()
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
    support_evidence_output = container_output / "support_evidence_summary.json"
    pre_cap_candidate_pool_output = container_output / "pre_cap_candidate_pool.jsonl"
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
        "--candidate-selection-policy",
        args.candidate_selection_policy,
        "--selection-score-mode",
        args.selection_score_mode,
        "--pre-cap-per-scan-label-cap",
        str(args.pre_cap_per_scan_label_cap),
        "--pre-cap-spatial-consolidation-radius-m",
        str(args.pre_cap_spatial_consolidation_radius_m),
        "--raw-candidate-collection-cap",
        str(args.raw_candidate_collection_cap),
        "--pre-cap-policy-output",
        "/outputs/pre_cap_policy_summary.json",
        "--support-evidence-policy",
        args.support_evidence_policy,
        "--support-evidence-radii-m",
        args.support_evidence_radii_m,
        "--support-evidence-output",
        "/outputs/support_evidence_summary.json",
    ]
    if args.export_pre_cap_candidate_pool:
        run_cmd.extend(
            [
                "--export-pre-cap-candidate-pool",
                "--pre-cap-candidate-pool-output",
                "/outputs/pre_cap_candidate_pool.jsonl",
            ]
        )
    if args.no_require_scan_prompt_label:
        run_cmd.append("--no-require-scan-prompt-label")

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
    pre_cap_policy_output = container_output / "pre_cap_policy_summary.json"
    pre_cap_policy_summary = load_json(pre_cap_policy_output) if pre_cap_policy_output.exists() else {}
    support_evidence_summary = load_json(support_evidence_output) if support_evidence_output.exists() else {}
    pre_cap_candidate_pool_rows = (
        load_jsonl(pre_cap_candidate_pool_output) if pre_cap_candidate_pool_output.exists() else []
    )
    prediction_rows = load_jsonl(predictions) if predictions.exists() else []
    matched_rows = load_jsonl(matching_out / "matched_proposals.jsonl") if (matching_out / "matched_proposals.jsonl").exists() else []

    frame_diagnostics = summarize_frame_diagnostics(model_status, prediction_rows)
    matching_failures = summarize_matching_failures(matched_rows)
    support_evidence = summarize_support_evidence(
        prediction_rows=prediction_rows,
        support_summary=support_evidence_summary,
        support_evidence_policy=args.support_evidence_policy,
        support_evidence_radii_m=args.support_evidence_radii_m,
    )
    candidate_pool_export = summarize_candidate_pool_export(
        candidate_pool_rows=pre_cap_candidate_pool_rows,
        pre_cap_policy_summary=pre_cap_policy_summary,
        export_enabled=bool(args.export_pre_cap_candidate_pool),
        output_path=pre_cap_candidate_pool_output,
        support_evidence_policy=args.support_evidence_policy,
    )
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
    elif args.support_evidence_policy != SUPPORT_EVIDENCE_NONE and not support_evidence["ready"]:
        status = "temporal_spatial_support_runner_smoke_failed"
    elif args.export_pre_cap_candidate_pool and not candidate_pool_export["ready"]:
        status = "pre_cap_candidate_pool_export_smoke_failed"
    elif args.export_pre_cap_candidate_pool:
        status = "pre_cap_candidate_pool_export_smoke_ready"
    elif args.selection_score_mode == SUPPORT_AWARE_SCORE_MODE:
        status = "support_aware_selection_runner_smoke_ready"
    elif args.support_evidence_policy != SUPPORT_EVIDENCE_NONE:
        status = "temporal_spatial_support_runner_smoke_ready"

    coverage = {
        "backend_contract_ready": bool(backend_payload.get("backend_status", {}).get("valid")),
        "candidate_pool_export": candidate_pool_export,
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
        "pre_cap_policy_applied": bool(model_status.get("pre_cap_policy_applied")),
        "pre_cap_policy_summary": pre_cap_policy_summary,
        "prediction_rows": len(prediction_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_command": run_cmd,
        "run_config": {
            "candidate_selection_policy": args.candidate_selection_policy,
            "max_frames_per_scan": args.max_frames_per_scan,
            "max_labels": args.max_labels,
            "max_predictions": args.max_predictions,
            "max_predictions_per_frame": args.max_predictions_per_frame,
            "max_scans": args.max_scans,
            "pre_cap_per_scan_label_cap": args.pre_cap_per_scan_label_cap,
            "pre_cap_spatial_consolidation_radius_m": args.pre_cap_spatial_consolidation_radius_m,
            "raw_candidate_collection_cap": args.raw_candidate_collection_cap,
            "require_scan_prompt_label": not args.no_require_scan_prompt_label,
            "selection_score_mode": args.selection_score_mode,
            "support_evidence_policy": args.support_evidence_policy,
            "support_evidence_radii_m": args.support_evidence_radii_m,
            "export_pre_cap_candidate_pool": bool(args.export_pre_cap_candidate_pool),
            "text_threshold": args.text_threshold,
            "threshold": args.threshold,
        },
        "status": status,
        "support_evidence": support_evidence,
        "support_evidence_summary": support_evidence_summary,
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
    ready_statuses = {
        "frame_scaling_projection_diagnostic_ready",
        "temporal_spatial_support_runner_smoke_ready",
        "support_aware_selection_runner_smoke_ready",
        "pre_cap_candidate_pool_export_smoke_ready",
    }
    return 0 if status in ready_statuses else 2


if __name__ == "__main__":
    raise SystemExit(main())
