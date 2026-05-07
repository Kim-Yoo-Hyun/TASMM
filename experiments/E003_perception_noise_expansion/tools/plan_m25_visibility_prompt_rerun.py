#!/usr/bin/env python3
"""Plan E003-M25 visibility-aware / prompt-expanded detector rerun gate."""

from __future__ import annotations

import argparse
import json
import shlex
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M23_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M23_proposal_consolidation_calibration_v0"
DEFAULT_M24_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M24_visibility_prompt_projection_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M25_visibility_prompt_rerun_gate_v0"
M25_VERSION = "e003_m25_visibility_prompt_rerun_gate_v0"


PRIORITY_LABELS = [
    "chair",
    "table",
    "sofa",
    "cabinet",
    "box",
    "bench",
    "plant",
    "pillow",
    "picture",
    "door",
    "light",
    "shelf",
    "tv",
    "sink",
    "curtain",
    "bag",
]


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


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("label_canonical"))
        for row in prompt_payload.get("labels", [])
        if row.get("detector_prompt_enabled") and row.get("label_canonical")
    }


def select_scan_labels(row: dict[str, Any], enabled_labels: set[str], max_labels: int) -> list[str]:
    target_labels = [str(label) for label in row.get("target_labels", []) if str(label) in enabled_labels]
    ordered = [label for label in PRIORITY_LABELS if label in target_labels]
    ordered.extend(label for label in target_labels if label not in ordered)
    if not ordered:
        ordered = sorted(enabled_labels)
    return ordered[:max_labels]


def count_eval_targets_by_scan_label(target_rows: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in target_rows:
        if not row.get("evaluation_target_enabled"):
            continue
        counts[(str(row["scan_id"]), str(row["label_canonical"]))] += 1
    return counts


def active_target_count(scan_id: str, labels: list[str], target_counts: dict[tuple[str, str], int]) -> int:
    return sum(target_counts.get((scan_id, label), 0) for label in labels)


def build_prompt_budget_rows(
    manifest_rows: list[dict[str, Any]],
    target_counts: dict[tuple[str, str], int],
    enabled_labels: set[str],
    current_max_labels: int,
    expanded_max_labels: int,
) -> list[dict[str, Any]]:
    rows = []
    for row in sorted(manifest_rows, key=lambda item: str(item["scan_id"])):
        scan_id = str(row["scan_id"])
        current_labels = select_scan_labels(row, enabled_labels, current_max_labels)
        expanded_labels = select_scan_labels(row, enabled_labels, expanded_max_labels)
        target_labels = [str(label) for label in row.get("target_labels", []) if str(label) in enabled_labels]
        current_active_targets = active_target_count(scan_id, current_labels, target_counts)
        expanded_active_targets = active_target_count(scan_id, expanded_labels, target_counts)
        eval_targets = int(row.get("evaluation_target_count", 0) or 0)
        rows.append(
            {
                "current_active_eval_target_rows": current_active_targets,
                "current_active_label_count": len(current_labels),
                "current_max_labels": current_max_labels,
                "current_missing_eval_target_rows": max(0, eval_targets - current_active_targets),
                "current_missing_labels": [label for label in target_labels if label not in set(current_labels)],
                "evaluation_target_rows": eval_targets,
                "expanded_active_eval_target_rows": expanded_active_targets,
                "expanded_active_label_count": len(expanded_labels),
                "expanded_max_labels": expanded_max_labels,
                "expanded_missing_eval_target_rows": max(0, eval_targets - expanded_active_targets),
                "expanded_missing_labels": [label for label in target_labels if label not in set(expanded_labels)],
                "prompt_coverage_gain_rows": expanded_active_targets - current_active_targets,
                "sampled_frame_count": int(row.get("sampled_frame_count", 0) or 0),
                "scan_id": scan_id,
                "target_label_count": int(row.get("target_label_count", 0) or 0),
            }
        )
    return rows


def command_payload(command: list[str]) -> dict[str, Any]:
    return {
        "argv": command,
        "shell": shlex.join(command),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M25 Visibility Prompt Rerun Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- M17 staged scans: {coverage['m17_scan_rows']}",
            f"- Current max labels: {coverage['current_max_labels']}",
            f"- Expanded max labels: {coverage['expanded_max_labels']}",
            f"- Max target label count: {coverage['max_target_label_count']}",
            f"- Current active eval target rows: {coverage['current_active_eval_target_rows']}",
            f"- Expanded active eval target rows: {coverage['expanded_active_eval_target_rows']}",
            f"- Prompt coverage gain rows: {coverage['prompt_coverage_gain_rows']}",
            f"- M24 scan eval target rows: {coverage['m24_scan_eval_target_rows']}",
            f"- M24 active prompt target rows: {coverage['m24_active_prompt_target_rows']}",
            f"- M24 depth-consistent visible-proxy target rows: {coverage['m24_depth_consistent_visible_proxy_target_rows']}",
            f"- Primary calibration policy: `{coverage['primary_calibration_policy_id']}`",
            f"- Pilot Docker rerun max scans: {coverage['pilot_docker_config']['max_scans']}",
            f"- Pilot Docker rerun max frames per scan: {coverage['pilot_docker_config']['max_frames_per_scan']}",
            f"- Pilot Docker rerun max predictions per frame: {coverage['pilot_docker_config']['max_predictions_per_frame']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M25 supports fixing the rerun contract for prompt-expanded, visibility-aware real detector evaluation.",
            "- E003-M25 does not support real RGB-D/open-vocabulary robustness because it does not execute the rerun.",
            "",
            "## 에이전트 추론",
            "",
            "- The next Docker run should expand the prompt cap before interpreting detector recall.",
            "- The primary calibration should preserve M22 matched targets while the visibility-aware denominator is still diagnostic.",
            "- The selected M23 precision-maximizing config should stay secondary because it drops matched targets.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M25. Next is executing the prompt-expanded Docker rerun.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m23-dir", default=DEFAULT_M23_DIR, type=Path)
    parser.add_argument("--m24-dir", default=DEFAULT_M24_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--current-max-labels", default=12, type=int)
    parser.add_argument("--expanded-max-labels", default=32, type=int)
    parser.add_argument("--pilot-max-scans", default=2, type=int)
    parser.add_argument("--pilot-max-frames-per-scan", default=12, type=int)
    parser.add_argument("--pilot-max-predictions-per-frame", default=60, type=int)
    parser.add_argument("--pilot-threshold", default=0.08, type=float)
    parser.add_argument("--pilot-text-threshold", default=0.08, type=float)
    args = parser.parse_args()

    manifest_rows = load_jsonl(args.m17_dir / "real_proposal_query_manifest.jsonl")
    target_rows = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    prompt_payload = load_json(args.m17_dir / "prompt_set.json")
    m23_coverage = load_json(args.m23_dir / "coverage.json")
    m24_coverage = load_json(args.m24_dir / "coverage.json")
    target_counts = count_eval_targets_by_scan_label(target_rows)
    enabled_labels = detector_prompt_labels(prompt_payload)

    max_target_label_count = max(int(row.get("target_label_count", 0) or 0) for row in manifest_rows)
    if args.expanded_max_labels < max_target_label_count:
        raise ValueError(
            f"expanded max labels {args.expanded_max_labels} is smaller than max target label count {max_target_label_count}"
        )

    prompt_budget_rows = build_prompt_budget_rows(
        manifest_rows=manifest_rows,
        target_counts=target_counts,
        enabled_labels=enabled_labels,
        current_max_labels=args.current_max_labels,
        expanded_max_labels=args.expanded_max_labels,
    )

    current_active_targets = sum(row["current_active_eval_target_rows"] for row in prompt_budget_rows)
    expanded_active_targets = sum(row["expanded_active_eval_target_rows"] for row in prompt_budget_rows)
    total_eval_targets = sum(row["evaluation_target_rows"] for row in prompt_budget_rows)

    primary_calibration = m23_coverage.get("full_match_preserving_config")
    secondary_calibration = m23_coverage.get("near_match_preserving_config")
    precision_calibration = m23_coverage.get("selected_config")

    detector_run_dir = args.out_dir / "detector_rerun"
    calibration_dir = args.out_dir / "match_preserving_calibration"
    visibility_dir = args.out_dir / "visibility_denominator"
    pilot_max_predictions = args.pilot_max_scans * args.pilot_max_frames_per_scan * args.pilot_max_predictions_per_frame
    pilot_detector_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--out-dir",
        str(detector_run_dir),
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
        "--max-scans",
        str(args.pilot_max_scans),
        "--max-frames-per-scan",
        str(args.pilot_max_frames_per_scan),
        "--max-labels",
        str(args.expanded_max_labels),
        "--max-predictions",
        str(pilot_max_predictions),
        "--max-predictions-per-frame",
        str(args.pilot_max_predictions_per_frame),
        "--threshold",
        str(args.pilot_threshold),
        "--text-threshold",
        str(args.pilot_text_threshold),
    ]
    post_calibration_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m23_proposal_calibration.py",
        "--m22-dir",
        str(detector_run_dir),
        "--out-dir",
        str(calibration_dir),
        "--selection-policy",
        "full_match_preserving",
    ]
    post_visibility_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m24_visibility_prompt_projection_gate.py",
        "--m22-dir",
        str(detector_run_dir),
        "--m23-dir",
        str(calibration_dir),
        "--out-dir",
        str(visibility_dir),
        "--max-labels",
        str(args.expanded_max_labels),
    ]

    denominator_contract = {
        "contract_id": "m25_visibility_aware_detector_denominator_v0",
        "m25_version": M25_VERSION,
        "primary_report_denominators": [
            "scan_eval_target_rows",
            "expanded_active_prompt_target_rows",
            "centroid_frustum_visible_proxy_target_rows",
            "depth_consistent_visible_proxy_target_rows",
        ],
        "rules": [
            "Report scan-level recall only as a broad diagnostic denominator.",
            "Use expanded active-prompt target rows to separate prompt-cap failure from detector failure.",
            "Use depth-consistent centroid-visible proxy as a lower-bound visibility diagnostic, not true visibility.",
            "Always report matched-outside-visibility-proxy rows because centroid projection is not true object visibility.",
        ],
        "current_m24_reference": {
            "active_prompt_target_rows": m24_coverage.get("active_prompt_target_rows"),
            "depth_consistent_visible_proxy_target_rows": m24_coverage.get(
                "depth_consistent_visible_proxy_target_rows"
            ),
            "m22_matched_outside_centroid_frustum_proxy_rows": m24_coverage.get(
                "m22_matched_outside_centroid_frustum_proxy_rows"
            ),
            "m22_recall_over_depth_consistent_visible_proxy_denominator": m24_coverage.get(
                "m22_recall_over_depth_consistent_visible_proxy_denominator"
            ),
            "scan_eval_target_rows": m24_coverage.get("scan_eval_target_rows"),
        },
        "paper_claim_boundary": "diagnostic_until_multiscan_rerun_and_visibility_proxy_limitations_are_reported",
    }

    calibration_policy = {
        "m25_version": M25_VERSION,
        "primary_policy": {
            "calibration_config": primary_calibration,
            "policy_id": "m23_full_match_preserving_v0",
            "reason": "preserve all current M22 matched targets before interpreting recall under expanded prompts",
        },
        "secondary_policy": {
            "calibration_config": secondary_calibration,
            "policy_id": "m23_near_match_preserving_precision_v0",
            "reason": "higher precision but one current M22 match is dropped",
        },
        "not_primary_policy": {
            "calibration_config": precision_calibration,
            "policy_id": "m23_precision_selected_v0",
            "reason": "precision improves but matched target rows drop from 7 to 4",
        },
    }

    docker_rerun_plan = {
        "m25_version": M25_VERSION,
        "pilot_detector_command": command_payload(pilot_detector_command),
        "post_calibration_command": command_payload(post_calibration_command),
        "post_visibility_command": command_payload(post_visibility_command),
        "sudo_password_policy": "stdin_required_not_stored",
        "pilot_config": {
            "max_frames_per_scan": args.pilot_max_frames_per_scan,
            "max_labels": args.expanded_max_labels,
            "max_predictions": pilot_max_predictions,
            "max_predictions_per_frame": args.pilot_max_predictions_per_frame,
            "max_scans": args.pilot_max_scans,
            "text_threshold": args.pilot_text_threshold,
            "threshold": args.pilot_threshold,
        },
        "paper_table_command_ready": False,
    }

    coverage = {
        "current_active_eval_target_rows": current_active_targets,
        "current_active_eval_target_rate": safe_rate(current_active_targets, total_eval_targets),
        "current_max_labels": args.current_max_labels,
        "expanded_active_eval_target_rows": expanded_active_targets,
        "expanded_active_eval_target_rate": safe_rate(expanded_active_targets, total_eval_targets),
        "expanded_max_labels": args.expanded_max_labels,
        "m17_scan_rows": len(manifest_rows),
        "m24_active_prompt_target_rows": m24_coverage.get("active_prompt_target_rows"),
        "m24_depth_consistent_visible_proxy_target_rows": m24_coverage.get(
            "depth_consistent_visible_proxy_target_rows"
        ),
        "m24_scan_eval_target_rows": m24_coverage.get("scan_eval_target_rows"),
        "m25_version": M25_VERSION,
        "max_target_label_count": max_target_label_count,
        "paper_table_command_ready": False,
        "pilot_docker_config": docker_rerun_plan["pilot_config"],
        "primary_calibration_policy_id": calibration_policy["primary_policy"]["policy_id"],
        "prompt_coverage_gain_rows": expanded_active_targets - current_active_targets,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "status": "visibility_prompt_rerun_gate_ready",
        "total_eval_target_rows": total_eval_targets,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "scan_prompt_budget_rows.jsonl", prompt_budget_rows)
    write_json(args.out_dir / "denominator_contract.json", denominator_contract)
    write_json(args.out_dir / "calibration_policy.json", calibration_policy)
    write_json(args.out_dir / "docker_rerun_plan.json", docker_rerun_plan)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
