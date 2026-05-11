#!/usr/bin/env python3
"""Plan E003-M41 support-aware selection policy gate."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M38_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M38_split_or_temporal_spatial_gate_v0"
DEFAULT_M40_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M40_temporal_spatial_support_runner_smoke_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M41_support_aware_selection_policy_gate_v0"
RUNNER = EXPERIMENT_ROOT / "docker" / "real_proposals" / "run_rgbd_ov_proposals.py"
WRAPPER = EXPERIMENT_ROOT / "tools" / "run_m22_frame_scaling_diagnostics.py"
M41_VERSION = "e003_m41_support_aware_selection_policy_gate_v0"
SUPPORT_EVIDENCE_POLICY_ID = "temporal_spatial_support_evidence_v0"
SELECTED_SCORE_MODE = "confidence_sqrt_depth_support_temporal_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command_payload(argv: list[str]) -> dict[str, Any]:
    return {
        "argv": argv,
        "shell": shlex.join(argv),
    }


def find_lines(source: list[str], needle: str) -> list[dict[str, Any]]:
    return [
        {
            "line": idx,
            "needle": needle,
            "snippet": line.rstrip(),
        }
        for idx, line in enumerate(source, start=1)
        if needle in line
    ]


def inspect_sources() -> dict[str, Any]:
    runner_source = RUNNER.read_text(encoding="utf-8").splitlines()
    wrapper_source = WRAPPER.read_text(encoding="utf-8").splitlines()
    runner_points = {
        "score_candidate": find_lines(runner_source, "def score_candidate("),
        "support_fields_available": find_lines(runner_source, 'row["support_evidence_policy"] = SUPPORT_EVIDENCE_POLICY_ID'),
        "consolidation_ranking": find_lines(runner_source, "ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode)"),
        "selection_score_write": find_lines(runner_source, 'row["selection_score"] = round(score_candidate(row, score_mode), 8)'),
        "selection_score_mode_choices": find_lines(runner_source, "--selection-score-mode"),
    }
    wrapper_points = {
        "selection_score_mode_arg": find_lines(wrapper_source, "--selection-score-mode"),
        "support_evidence_policy_arg": find_lines(wrapper_source, "--support-evidence-policy"),
        "support_evidence_radii_arg": find_lines(wrapper_source, "--support-evidence-radii-m"),
    }
    runner_missing = [name for name, hits in runner_points.items() if not hits]
    wrapper_missing = [name for name, hits in wrapper_points.items() if not hits]
    return {
        "runner": {
            "missing_expected_points": runner_missing,
            "path": str(RUNNER),
            "points": runner_points,
            "status": "runner_support_aware_policy_sites_found" if not runner_missing else "runner_site_inspection_incomplete",
        },
        "wrapper": {
            "missing_expected_points": wrapper_missing,
            "path": str(WRAPPER),
            "points": wrapper_points,
            "status": "wrapper_support_arg_sites_found" if not wrapper_missing else "wrapper_site_inspection_incomplete",
        },
    }


def build_policy_contract() -> dict[str, Any]:
    return {
        "contract_id": SELECTED_SCORE_MODE,
        "m41_version": M41_VERSION,
        "selected_route": "support_aware_scoring_before_consolidation_and_final_rank",
        "support_evidence_policy_required": SUPPORT_EVIDENCE_POLICY_ID,
        "runner_arg": {
            "arg": "--selection-score-mode",
            "new_choice": SELECTED_SCORE_MODE,
        },
        "support_args_kept": [
            {
                "arg": "--support-evidence-policy",
                "required_value": SUPPORT_EVIDENCE_POLICY_ID,
            },
            {
                "arg": "--support-evidence-radii-m",
                "required_value": "0.75,1.0,1.5,2.0",
            },
        ],
        "formula": {
            "base_score": "confidence * min(1, sqrt(depth_valid_pixel_count) / sqrt(5000))",
            "temporal_factor": "min(1, support_temporal_neighbor_frame_count_r2p0m / 2)",
            "spatial_factor": "min(1, support_spatial_neighbor_count_r1p0m / 8)",
            "selection_score": "base_score * (1 + 0.25 * temporal_factor + 0.10 * spatial_factor)",
        },
        "where_it_applies": [
            "same-scan/same-label spatial consolidation representative ranking",
            "per-scan-label cap ranking",
            "final global max-predictions ranking",
        ],
        "where_it_does_not_apply": [
            "no hard support filter in M42",
            "no labelwise support threshold in M42",
            "no change to max_predictions or per_scan_label_cap in M42",
        ],
        "reasoning": [
            "M38 showed post-hoc support filters can lose heldout matched targets.",
            "M40 showed temporal support is available on selected rows, but selection quality is still weak.",
            "A soft score bonus can test support usefulness without suppressing single-frame true targets.",
        ],
    }


def build_rejected_routes() -> dict[str, Any]:
    return {
        "m41_version": M41_VERSION,
        "rejected_or_deferred_routes": [
            {
                "route": "hard_support_filter_v0",
                "status": "rejected_for_next_unit",
                "reason": "M38 heldout transfer lost matched targets; hard filtering risks dropping true objects visible in only one or two frames.",
            },
            {
                "route": "labelwise_support_cap_learning_v0",
                "status": "deferred",
                "reason": "M37/M38 show the current 8-scan artifact is label-sparse, so labelwise caps are not reliable yet.",
            },
            {
                "route": "final_artifact_postprocessing_v0",
                "status": "rejected",
                "reason": "Final proposal artifacts do not preserve candidates removed before spatial consolidation and caps.",
            },
            {
                "route": "support_only_ranking_v0",
                "status": "rejected_for_next_unit",
                "reason": "Spatial support is dense in M40 and can be dominated by duplicate detections; detector confidence/depth should remain the base signal.",
            },
        ],
    }


def build_verification_plan() -> dict[str, Any]:
    py_compile = [
        "python",
        "-m",
        "py_compile",
        str(RUNNER.relative_to(REPO_ROOT)),
        str(WRAPPER.relative_to(REPO_ROOT)),
        str(Path(__file__).resolve().relative_to(REPO_ROOT)),
    ]
    m42_smoke = [
        "sg",
        "docker",
        "-c",
        (
            "python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py "
            "--build "
            "--out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M42_support_aware_selection_runner_smoke_v0 "
            "--max-scans 1 "
            "--max-frames-per-scan 2 "
            "--max-labels 32 "
            "--max-predictions 400 "
            "--max-predictions-per-frame 20 "
            "--candidate-selection-policy cap_aware_label_balanced_ranking_v0 "
            f"--selection-score-mode {SELECTED_SCORE_MODE} "
            "--pre-cap-per-scan-label-cap 40 "
            "--pre-cap-spatial-consolidation-radius-m 0.5 "
            "--raw-candidate-collection-cap 20000 "
            f"--support-evidence-policy {SUPPORT_EVIDENCE_POLICY_ID} "
            "--support-evidence-radii-m 0.75,1.0,1.5,2.0"
        ),
    ]
    return {
        "contract_id": "e003_m41_verification_plan",
        "m41_version": M41_VERSION,
        "commands_executed_in_m41": [
            command_payload(py_compile),
            command_payload(["python", str(Path(__file__).resolve().relative_to(REPO_ROOT))]),
        ],
        "commands_reserved_for_m42_after_runner_edit": [
            command_payload(m42_smoke),
        ],
        "m42_smoke_success_checks": [
            "status is temporal_spatial_support_runner_smoke_ready or support_aware_selection_runner_smoke_ready",
            "validator errors/warnings are 0/0",
            "support_evidence.ready is true",
            "pre_cap_policy_summary.score_mode equals confidence_sqrt_depth_support_temporal_v0",
            "rows_with_support_policy equals prediction_rows",
            "matched proposals are not lower than the M40 smoke matched proposals unless a failure note is recorded",
        ],
        "scaled_success_checks_for_later": [
            "matched-target retention vs M33 baseline >= 0.95",
            "false-positive proposal rows reduce by at least 10% vs comparable support-instrumented baseline",
            "proposal precision improves vs comparable support-instrumented baseline",
            "dev/heldout split transfer is reported before paper-table claim",
        ],
        "long_running_rule": "Run any scaled Docker rerun in tmux/nohup with timestamped logs under logs/.",
    }


def build_coverage(m38: dict[str, Any], m40: dict[str, Any], source_inspection: dict[str, Any]) -> dict[str, Any]:
    m40_support = m40.get("support_evidence", {})
    m40_matching = m40.get("matching_coverage", {})
    source_ready = (
        source_inspection["runner"]["status"] == "runner_support_aware_policy_sites_found"
        and source_inspection["wrapper"]["status"] == "wrapper_support_arg_sites_found"
    )
    return {
        "status": "support_aware_selection_policy_gate_ready",
        "m41_version": M41_VERSION,
        "selected_score_mode": SELECTED_SCORE_MODE,
        "selected_route": "support_aware_scoring_before_consolidation_and_final_rank",
        "source_inspection_ready": source_ready,
        "m38_support_transfer_pass": bool(m38.get("support_transfer_pass")),
        "m40_support_ready": bool(m40_support.get("ready")),
        "m40_prediction_rows": int(m40.get("prediction_rows", 0) or 0),
        "m40_rows_with_support_policy": int(m40_support.get("rows_with_support_policy", 0) or 0),
        "m40_rows_with_spatial_support": int(m40_support.get("rows_with_spatial_support", 0) or 0),
        "m40_rows_with_temporal_support": int(m40_support.get("rows_with_temporal_support", 0) or 0),
        "m40_matched_proposals": int(m40_matching.get("matched_proposal_rows", 0) or 0),
        "m40_false_positive_proposals": int(m40_matching.get("false_positive_proposal_rows", 0) or 0),
        "m40_proposal_precision_smoke": m40_matching.get("proposal_precision_smoke"),
        "support_hard_filter_recommended": False,
        "support_cap_change_recommended": False,
        "runner_code_update_required": True,
        "short_smoke_required_before_long_rerun": True,
        "long_rerun_ready": False,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "next_recommended_unit": "E003-M42 support-aware selection runner smoke",
    }


def build_report(coverage: dict[str, Any], policy_contract: dict[str, Any]) -> str:
    formula = policy_contract["formula"]
    return "\n".join(
        [
            "# E003-M41 Support-Aware Selection Policy Gate",
            "",
            f"Implementation unit: `E003-M41_support_aware_selection_policy_gate_v0`.",
            "",
            "## Decision",
            "",
            f"- Status: `{coverage['status']}`",
            f"- Selected score mode: `{coverage['selected_score_mode']}`",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Next recommended unit: `{coverage['next_recommended_unit']}`",
            "",
            "## Policy Contract",
            "",
            f"- Base score: `{formula['base_score']}`",
            f"- Temporal factor: `{formula['temporal_factor']}`",
            f"- Spatial factor: `{formula['spatial_factor']}`",
            f"- Selection score: `{formula['selection_score']}`",
            "",
            "## Facts",
            "",
            f"- M40 support ready: `{str(coverage['m40_support_ready']).lower()}`",
            f"- M40 prediction rows: {coverage['m40_prediction_rows']}",
            f"- M40 rows with support policy: {coverage['m40_rows_with_support_policy']}",
            f"- M40 rows with spatial / temporal support: {coverage['m40_rows_with_spatial_support']} / {coverage['m40_rows_with_temporal_support']}",
            f"- M40 matched / false-positive proposals: {coverage['m40_matched_proposals']} / {coverage['m40_false_positive_proposals']}",
            f"- M40 proposal precision smoke: {coverage['m40_proposal_precision_smoke']}",
            "",
            "## Claim Boundary",
            "",
            "- This gate does not execute Docker.",
            "- This gate does not prove support-aware selection improves proposal quality.",
            "- This gate blocks a long rerun until M42 implements the selected score mode and passes a short smoke.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m38-dir", default=DEFAULT_M38_DIR, type=Path)
    parser.add_argument("--m40-dir", default=DEFAULT_M40_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    m38 = load_json(args.m38_dir.resolve() / "coverage.json")
    m40 = load_json(args.m40_dir.resolve() / "coverage.json")
    source_inspection = inspect_sources()
    policy_contract = build_policy_contract()
    rejected_routes = build_rejected_routes()
    verification_plan = build_verification_plan()
    coverage = build_coverage(m38, m40, source_inspection)

    out_dir = args.out_dir.resolve()
    write_json(out_dir / "source_inspection.json", source_inspection)
    write_json(out_dir / "policy_contract.json", policy_contract)
    write_json(out_dir / "rejected_routes.json", rejected_routes)
    write_json(out_dir / "verification_plan.json", verification_plan)
    write_json(out_dir / "coverage.json", coverage)
    write_text(out_dir / "report.md", build_report(coverage, policy_contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
