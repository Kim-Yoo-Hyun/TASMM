#!/usr/bin/env python3
"""Plan E003-M29 Docker pre-cap policy integration gate."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M28_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M28_cap_aware_label_balanced_policy_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M29_pre_cap_policy_integration_gate_v0"
RUNNER = EXPERIMENT_ROOT / "docker" / "real_proposals" / "run_rgbd_ov_proposals.py"
M29_VERSION = "e003_m29_pre_cap_policy_integration_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def command_payload(command: list[str]) -> dict[str, Any]:
    return {
        "argv": command,
        "shell": shlex.join(command),
    }


def find_line(source: list[str], needle: str) -> dict[str, Any]:
    for idx, line in enumerate(source, start=1):
        if needle in line:
            return {
                "line": idx,
                "needle": needle,
                "snippet": line.rstrip(),
            }
    return {
        "line": None,
        "needle": needle,
        "snippet": None,
    }


def find_line_after(source: list[str], needle: str, after_line: int | None) -> dict[str, Any]:
    start = max(int(after_line or 1), 1)
    for idx, line in enumerate(source[start - 1 :], start=start):
        if needle in line:
            return {
                "line": idx,
                "needle": needle,
                "snippet": line.rstrip(),
            }
    return {
        "line": None,
        "needle": needle,
        "snippet": None,
    }


def inspect_runner(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8").splitlines()
    detector_loop = find_line(source, "for local_index, (box, score, raw_label) in enumerate(")
    points = {
        "detector_result_loop": detector_loop,
        "current_global_cap_check": find_line(source, "if len(rows) >= max_predictions:"),
        "current_frame_cap_check": find_line(
            source,
            "if max_predictions_per_frame is not None and frame_predictions >= max_predictions_per_frame:",
        ),
        "final_row_append": find_line_after(source, "rows.append(", detector_loop["line"]),
        "final_jsonl_write": find_line(source, "write_jsonl(output_path, rows)"),
        "argparse_max_predictions": find_line(source, 'parser.add_argument("--max-predictions", default=20, type=int)'),
        "argparse_max_predictions_per_frame": find_line(
            source,
            'parser.add_argument("--max-predictions-per-frame", type=int)',
        ),
        "model_status_metadata": find_line(source, 'write_json(args.output.parent / "model_smoke.json", model_status)'),
    }
    missing = [name for name, item in points.items() if item["line"] is None]
    return {
        "missing_expected_points": missing,
        "runner": str(path),
        "source_line_count": len(source),
        "status": "runner_cap_sites_found" if not missing else "runner_cap_site_inspection_incomplete",
        "points": points,
    }


def build_runner_args_contract(selected_policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "cap_aware_label_balanced_ranking_v0_runner_args",
        "m29_version": M29_VERSION,
        "default_preserves_existing_behavior": True,
        "new_or_changed_args": [
            {
                "arg": "--candidate-selection-policy",
                "choices": ["detector_order_v0", "cap_aware_label_balanced_ranking_v0"],
                "default": "detector_order_v0",
                "purpose": "Select whether detector proposals are written in detector order or ranked before final caps.",
            },
            {
                "arg": "--selection-score-mode",
                "choices": ["confidence", "confidence_log_depth", "confidence_sqrt_depth"],
                "default": str(selected_policy["score_mode"]),
                "purpose": "Score raw projected candidates before spatial consolidation and label-balanced caps.",
            },
            {
                "arg": "--pre-cap-per-scan-label-cap",
                "default": int(selected_policy["per_scan_label_cap"]),
                "purpose": "Retain at most this many candidates per scan and canonical label before the global output cap.",
            },
            {
                "arg": "--pre-cap-spatial-consolidation-radius-m",
                "default": float(selected_policy["spatial_consolidation_radius_m"]),
                "purpose": "Suppress lower-scored candidates of the same scan/label within this world-coordinate radius.",
            },
            {
                "arg": "--require-scan-prompt-label",
                "default": True,
                "purpose": "Drop resolved labels that are not active for the current scan prompt set before ranking.",
            },
            {
                "arg": "--raw-candidate-collection-cap",
                "default": 50000,
                "purpose": "Safety cap for raw projected candidates before policy selection; it is not a paper metric cap.",
            },
            {
                "arg": "--pre-cap-policy-output",
                "default": "/outputs/pre_cap_policy_summary.json",
                "purpose": "Write policy diagnostics beside real_proposals.jsonl for reproducibility.",
            },
        ],
        "existing_args_kept": [
            {
                "arg": "--max-predictions",
                "m29_semantics": "Final global output cap after policy selection.",
            },
            {
                "arg": "--max-predictions-per-frame",
                "m29_semantics": "Legacy detector-order cap only; when candidate-selection-policy is cap-aware, this must not truncate candidates before policy ranking.",
            },
            {
                "arg": "--max-labels",
                "m29_semantics": "Prompt budget remains fixed at the E003-M26 value, so M29 isolates proposal selection from prompt coverage.",
            },
        ],
        "selected_m28_values": selected_policy,
    }


def build_output_contract(selected_policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "cap_aware_label_balanced_ranking_v0_output_contract",
        "m29_version": M29_VERSION,
        "prediction_jsonl_schema": "real_proposal_prediction_jsonl_v0",
        "prediction_jsonl_rule": "Keep the existing required fields valid; additional policy fields are allowed by the validator.",
        "additional_prediction_fields": [
            "candidate_selection_policy",
            "selection_score",
            "pre_cap_rank",
            "pre_cap_group_key",
            "raw_candidate_uid",
            "raw_frame_local_index",
        ],
        "policy_summary_json": {
            "path_arg": "--pre-cap-policy-output",
            "required_fields": [
                "candidate_selection_policy",
                "score_mode",
                "raw_prediction_count",
                "projected_candidate_count",
                "policy_input_candidate_count",
                "spatial_consolidated_candidate_count",
                "selected_candidate_count",
                "final_prediction_rows",
                "dropped_non_prompt_label_rows",
                "dropped_not_scan_prompt_label_rows",
                "skipped_no_depth_prediction_count",
                "per_scan_label_cap",
                "spatial_consolidation_radius_m",
                "max_predictions",
                "max_predictions_reached_after_policy",
            ],
        },
        "model_status_additions": [
            "candidate_selection_policy",
            "pre_cap_policy_applied",
            "pre_cap_policy_output",
            "raw_prediction_count",
            "projected_candidate_count",
            "policy_input_candidate_count",
            "spatial_consolidated_candidate_count",
            "selected_candidate_count",
            "max_predictions_reached_after_policy",
        ],
        "frame_inference_row_additions": [
            "projected_candidate_count",
            "policy_selected_prediction_count",
            "legacy_pre_policy_frame_cap_applied",
        ],
        "selected_m28_values": selected_policy,
    }


def build_integration_contract(selected_policy: dict[str, Any], runner_inspection: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "e003_m29_runner_integration_contract_v0",
        "m29_version": M29_VERSION,
        "source_runner": runner_inspection["runner"],
        "current_cap_behavior": [
            "The current runner checks len(rows) >= max_predictions inside the detector result loop.",
            "The current runner checks frame_predictions >= max_predictions_per_frame inside the detector result loop.",
            "Therefore M26 can discard raw detector candidates before label-balanced ranking sees them.",
        ],
        "required_runner_flow": [
            "Run detector over the fixed M26 prompt/frame/scan configuration.",
            "Resolve canonical labels and backproject valid RGB-D boxes into raw projected candidate rows.",
            "Do not apply global or per-frame output caps while collecting raw projected candidates under cap_aware_label_balanced_ranking_v0.",
            "Drop non-prompt or not-scan-prompt labels before scoring.",
            "Score candidates using selection-score-mode.",
            "Spatially consolidate candidates per scan and label.",
            "Apply pre-cap-per-scan-label-cap per scan and label.",
            "Apply max-predictions only as the final global output cap.",
            "Write the unchanged real_proposal_prediction_jsonl_v0 rows plus optional policy diagnostic fields.",
            "Write pre_cap_policy_summary.json and mirror key counts into model_smoke.json/run_metadata.json.",
        ],
        "blocked_inputs": [
            "3DSSG object instance ids",
            "evaluation target ids",
            "candidate_is_target",
            "matched_3dssg_instance_id",
            "post-hoc match status",
        ],
        "allowed_inputs": [
            "RGB frames",
            "Depth frames",
            "Camera poses",
            "Camera intrinsics",
            "Open-vocabulary prompt text",
            "Detector score",
            "2D box",
            "Depth support pixel count",
        ],
        "selected_policy": selected_policy,
    }


def build_docker_rerun_plan(selected_policy: dict[str, Any]) -> dict[str, Any]:
    out_dir = (
        REPO_ROOT
        / "experiments"
        / "E003_perception_noise_expansion"
        / "artifacts"
        / "E003-M30_pre_cap_policy_docker_rerun_v0"
        / "detector_rerun"
    )
    detector_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--out-dir",
        str(out_dir),
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
        "--max-scans",
        "2",
        "--max-frames-per-scan",
        "12",
        "--max-labels",
        "32",
        "--max-predictions",
        "1440",
        "--max-predictions-per-frame",
        "60",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        str(selected_policy["score_mode"]),
        "--pre-cap-per-scan-label-cap",
        str(selected_policy["per_scan_label_cap"]),
        "--pre-cap-spatial-consolidation-radius-m",
        str(selected_policy["spatial_consolidation_radius_m"]),
    ]
    post_matching_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py",
        "--predictions",
        str(out_dir / "container_output" / "real_proposals.jsonl"),
        "--out-dir",
        str(out_dir / "matching"),
    ]
    return {
        "m29_version": M29_VERSION,
        "next_unit": "E003-M30 pre-cap policy Docker runner implementation/rerun",
        "runner_update_required_before_execution": True,
        "host_wrapper_update_required_before_execution": True,
        "detector_command_after_runner_update": command_payload(detector_command),
        "post_matching_command_after_rerun": command_payload(post_matching_command),
        "fixed_against_m26": {
            "max_scans": 2,
            "max_frames_per_scan": 12,
            "max_labels": 32,
            "max_predictions": 1440,
            "threshold": 0.08,
            "text_threshold": 0.08,
        },
        "success_gate_for_m30": [
            "Docker run completes with pre_cap_policy_applied=true.",
            "Validator error rows are 0.",
            "pre_cap_policy_summary.json exists and reports projected_candidate_count >= E003-M26 written predictions.",
            "Final output rows are <= max_predictions.",
            "Matching/visibility summaries can be compared against E003-M26.",
        ],
        "paper_table_command_ready": False,
    }


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_m28_policy"]
    points = coverage["runner_inspection"]["points"]
    return "\n".join(
        [
            "# E003-M29 Pre Cap Policy Integration Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Runner: `{coverage['runner_inspection']['runner']}`",
            f"- Detector result loop line: {points['detector_result_loop']['line']}",
            f"- Current global cap check line: {points['current_global_cap_check']['line']}",
            f"- Current per-frame cap check line: {points['current_frame_cap_check']['line']}",
            f"- Final row append line: {points['final_row_append']['line']}",
            f"- Final JSONL write line: {points['final_jsonl_write']['line']}",
            f"- Selected policy id: `{coverage['selected_policy_id']}`",
            f"- Selected score mode: `{selected['score_mode']}`",
            f"- Selected per-scan-label cap: {selected['per_scan_label_cap']}",
            f"- Selected spatial consolidation radius m: {selected['spatial_consolidation_radius_m']}",
            f"- Runner args contract ready: {coverage['runner_args_contract_ready']}",
            f"- Output contract ready: {coverage['output_contract_ready']}",
            f"- Docker rerun plan ready: {coverage['docker_rerun_plan_ready']}",
            f"- Runner code updated in M29: {coverage['runner_code_updated_in_m29']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M29 supports a reproducible implementation contract for moving `cap_aware_label_balanced_ranking_v0` before detector output caps.",
            "- E003-M29 does not support a detector-result claim because it does not rerun Docker detector inference.",
            "",
            "## 에이전트 추론",
            "",
            "- The current cap site is inside the detector result loop, so post-hoc replay can miss candidates that were truncated before M28 saw them.",
            "- M30 should implement candidate collection first and apply `max_predictions` only after label cleanup, scoring, spatial consolidation, and per-scan-label capping.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for M29. Next is implementing the runner and host-wrapper pass-through, then rerunning the fixed M26 pilot under the pre-cap policy.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m28-dir", default=DEFAULT_M28_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--runner", default=RUNNER, type=Path)
    args = parser.parse_args()

    m28_coverage = load_json(args.m28_dir / "coverage.json")
    selected_policy = m28_coverage["selected_policy"]
    runner_inspection = inspect_runner(args.runner)
    runner_args_contract = build_runner_args_contract(selected_policy)
    output_contract = build_output_contract(selected_policy)
    integration_contract = build_integration_contract(selected_policy, runner_inspection)
    docker_rerun_plan = build_docker_rerun_plan(selected_policy)

    coverage = {
        "docker_rerun_plan_ready": True,
        "m28_replay_after_detector_cap": bool(m28_coverage.get("replay_after_detector_cap")),
        "m29_version": M29_VERSION,
        "next_recommended_unit": "E003-M30 pre-cap policy Docker runner implementation/rerun",
        "output_contract_ready": True,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "runner_args_contract_ready": True,
        "runner_code_updated_in_m29": False,
        "runner_inspection": runner_inspection,
        "selected_m28_policy": selected_policy,
        "selected_policy_id": m28_coverage["next_policy_id"],
        "status": "pre_cap_policy_integration_gate_ready",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "runner_insertion_points.json", runner_inspection)
    write_json(args.out_dir / "runner_args_contract.json", runner_args_contract)
    write_json(args.out_dir / "output_contract.json", output_contract)
    write_json(args.out_dir / "integration_contract.json", integration_contract)
    write_json(args.out_dir / "docker_rerun_plan.json", docker_rerun_plan)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
