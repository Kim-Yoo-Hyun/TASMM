#!/usr/bin/env python3
"""Plan E003-M39 temporal-spatial support instrumentation gate."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M38_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M38_split_or_temporal_spatial_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M39_temporal_spatial_support_instrumentation_gate_v0"
RUNNER = EXPERIMENT_ROOT / "docker" / "real_proposals" / "run_rgbd_ov_proposals.py"
WRAPPER = EXPERIMENT_ROOT / "tools" / "run_m22_frame_scaling_diagnostics.py"
M39_VERSION = "e003_m39_temporal_spatial_support_instrumentation_gate_v0"
SUPPORT_POLICY_ID = "temporal_spatial_support_evidence_v0"
SUPPORT_RADII_M = [0.75, 1.0, 1.5, 2.0]


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


def radius_suffix(radius_m: float) -> str:
    return str(radius_m).replace(".", "p")


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


def inspect_runner(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8").splitlines()
    points = {
        "support_helper_anchor_score_candidate": find_line(source, "def score_candidate("),
        "policy_function": find_line(source, "def select_cap_aware_label_balanced_candidates("),
        "cleaned_candidate_append": find_line(source, "cleaned.append(row)"),
        "grouping_after_cleaned": find_line(
            source,
            'grouped.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(row)',
        ),
        "spatial_consolidation_start": find_line(source, "consolidated = []"),
        "label_balancing_start": find_line(source, "balanced = []"),
        "policy_summary_write": find_line(source, "write_json(pre_cap_policy_output, pre_cap_policy_summary)"),
        "proposal_jsonl_write": find_line(source, "write_jsonl(output_path, rows)"),
        "argparse_candidate_selection_policy": find_line(source, '"--candidate-selection-policy"'),
        "argparse_raw_candidate_collection_cap": find_line(source, '"--raw-candidate-collection-cap"'),
    }
    missing = [name for name, item in points.items() if item["line"] is None]
    insertion_ready = (
        points["cleaned_candidate_append"]["line"] is not None
        and points["grouping_after_cleaned"]["line"] is not None
        and int(points["cleaned_candidate_append"]["line"]) < int(points["grouping_after_cleaned"]["line"])
    )
    return {
        "missing_expected_points": missing,
        "preferred_insertion_point": {
            "id": "select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped",
            "ready": insertion_ready,
            "after": points["cleaned_candidate_append"],
            "before": points["grouping_after_cleaned"],
            "reason": "Support evidence must be computed after prompt/label cleanup but before spatial consolidation and caps remove candidates.",
        },
        "runner": str(path),
        "source_line_count": len(source),
        "status": "runner_instrumentation_sites_found" if not missing and insertion_ready else "runner_instrumentation_site_inspection_incomplete",
        "points": points,
    }


def inspect_wrapper(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8").splitlines()
    points = {
        "argparse_candidate_selection_policy": find_line(source, '"--candidate-selection-policy"'),
        "argparse_raw_candidate_collection_cap": find_line(source, '"--raw-candidate-collection-cap"'),
        "run_cmd_candidate_selection_policy": find_line(source, "args.candidate_selection_policy"),
        "run_cmd_pre_cap_policy_output": find_line(source, '"/outputs/pre_cap_policy_summary.json"'),
        "pre_cap_policy_summary_load": find_line(source, "pre_cap_policy_summary = load_json(pre_cap_policy_output)"),
    }
    missing = [name for name, item in points.items() if item["line"] is None]
    return {
        "missing_expected_points": missing,
        "status": "wrapper_pass_through_sites_found" if not missing else "wrapper_pass_through_site_inspection_incomplete",
        "points": points,
        "wrapper": str(path),
        "source_line_count": len(source),
    }


def build_support_field_contract() -> dict[str, Any]:
    radius_fields = []
    for radius in SUPPORT_RADII_M:
        suffix = radius_suffix(radius)
        radius_fields.extend(
            [
                {
                    "field": f"support_spatial_neighbor_count_r{suffix}m",
                    "type": "int",
                    "required_when_enabled": True,
                    "definition": "Number of same-scan, same-label cleaned candidates within the radius, excluding the candidate itself.",
                },
                {
                    "field": f"support_temporal_neighbor_frame_count_r{suffix}m",
                    "type": "int",
                    "required_when_enabled": True,
                    "definition": "Number of distinct other RGB-D frame ids represented by same-scan, same-label neighbors within the radius.",
                },
                {
                    "field": f"support_max_neighbor_confidence_r{suffix}m",
                    "type": "float|null",
                    "required_when_enabled": True,
                    "definition": "Maximum detector confidence among same-scan, same-label neighbors within the radius; null when no neighbor exists.",
                },
            ]
        )
    return {
        "contract_id": SUPPORT_POLICY_ID,
        "m39_version": M39_VERSION,
        "compute_stage": "after_prompt_label_cleanup_before_spatial_consolidation_and_caps",
        "candidate_group_key": ["scan_id", "label_canonical"],
        "coordinate_source": "centroid_world_m from projected RGB-D depth and camera pose",
        "radii_m": SUPPORT_RADII_M,
        "required_prediction_fields_when_enabled": [
            {
                "field": "support_evidence_policy",
                "type": "string",
                "value": SUPPORT_POLICY_ID,
            },
            {
                "field": "support_group_key",
                "type": "string",
                "format": "<scan_id>::<label_canonical>",
            },
            {
                "field": "support_group_candidate_count",
                "type": "int",
                "definition": "Number of cleaned candidates in the same support group before consolidation.",
            },
            {
                "field": "support_group_frame_count",
                "type": "int",
                "definition": "Number of distinct RGB-D frames in the same support group before consolidation.",
            },
            *radius_fields,
        ],
        "summary_json_fields_when_enabled": [
            "support_evidence_policy",
            "support_evidence_stage",
            "support_evidence_radii_m",
            "support_evidence_candidate_rows",
            "support_evidence_groups",
            "support_evidence_output",
            "support_evidence_attached_to_selected_rows",
        ],
        "compatibility_rule": "The existing real_proposal_prediction_jsonl_v0 validator allows additional fields, so M40 can add support fields without changing required proposal fields.",
    }


def build_instrumentation_contract(runner: dict[str, Any], wrapper: dict[str, Any], m38: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "e003_m39_temporal_spatial_support_instrumentation",
        "m39_version": M39_VERSION,
        "m38_input_status": m38.get("status"),
        "m38_selected_route": m38.get("selected_route"),
        "m38_support_transfer_pass": bool(m38.get("support_transfer_pass")),
        "m38_stronger_split_feasible_with_current_scans": bool(m38.get("stronger_split_feasible_with_current_scans")),
        "selected_instrumentation_route": "docker_runner_pre_consolidation_support_evidence_v0",
        "deterministic_postprocessing_route_ready": False,
        "deterministic_postprocessing_rejection_reason": (
            "M33/M38 artifacts preserve final selected proposals, not the cleaned raw candidate pool before spatial consolidation and caps."
        ),
        "runner_edit_scope_for_m40": [
            str(RUNNER.relative_to(REPO_ROOT)),
            str(WRAPPER.relative_to(REPO_ROOT)),
        ],
        "runner_insertion_point": runner["preferred_insertion_point"],
        "runner_new_args_for_m40": [
            {
                "arg": "--support-evidence-policy",
                "choices": ["none", SUPPORT_POLICY_ID],
                "default": "none",
                "purpose": "Enable pre-consolidation support evidence without changing default runner behavior.",
            },
            {
                "arg": "--support-evidence-radii-m",
                "default": ",".join(str(radius) for radius in SUPPORT_RADII_M),
                "purpose": "Comma-separated radii used for same-label spatial/temporal support diagnostics.",
            },
            {
                "arg": "--support-evidence-output",
                "default": "/outputs/support_evidence_summary.json",
                "purpose": "Write support instrumentation summary beside pre_cap_policy_summary.json.",
            },
        ],
        "wrapper_pass_through_for_m40": [
            "--support-evidence-policy",
            "--support-evidence-radii-m",
            "--support-evidence-output",
        ],
        "implementation_notes_for_m40": [
            "Add helper functions near score_candidate: parse_support_radii_m, support_radius_suffix, compute_temporal_spatial_support.",
            "Call compute_temporal_spatial_support on cleaned candidates before grouped is built.",
            "Attach support fields to selected rows that survive consolidation and caps.",
            "Add support summary fields to pre_cap_policy_summary and model_smoke metadata.",
            "Keep default support policy as none so earlier artifacts remain reproducible.",
        ],
        "source_inspection": {
            "runner": runner,
            "wrapper": wrapper,
        },
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
    m39_plan = [
        "python",
        str(Path(__file__).resolve().relative_to(REPO_ROOT)),
    ]
    m40_smoke = [
        "python",
        str(WRAPPER.relative_to(REPO_ROOT)),
        "--out-dir",
        "experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0",
        "--max-scans",
        "1",
        "--max-frames-per-scan",
        "2",
        "--max-labels",
        "32",
        "--max-predictions",
        "400",
        "--max-predictions-per-frame",
        "20",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence_sqrt_depth",
        "--pre-cap-per-scan-label-cap",
        "40",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "20000",
        "--support-evidence-policy",
        SUPPORT_POLICY_ID,
        "--support-evidence-radii-m",
        ",".join(str(radius) for radius in SUPPORT_RADII_M),
    ]
    validate = [
        "python",
        str((EXPERIMENT_ROOT / "tools" / "validate_real_proposal_output.py").relative_to(REPO_ROOT)),
        "--predictions",
        "experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/real_proposals.jsonl",
        "--summary",
        "experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/validation_summary.json",
    ]
    return {
        "contract_id": "e003_m39_verification_plan",
        "m39_version": M39_VERSION,
        "commands_executed_in_m39": [
            command_payload(py_compile),
            command_payload(m39_plan),
        ],
        "commands_reserved_for_m40_after_runner_edit": [
            command_payload(m40_smoke),
            command_payload(validate),
        ],
        "m40_success_checks": [
            "real_proposals.jsonl exists and passes existing proposal validator.",
            "pre_cap_policy_summary.json includes support_evidence_policy and support_evidence_candidate_rows.",
            "support_evidence_summary.json exists when support evidence is enabled.",
            "At least one selected proposal row has support_evidence_policy and non-negative support counts.",
            "Default run with --support-evidence-policy none preserves current behavior.",
        ],
        "long_running_rule": "If M40 smoke expands beyond a short run, launch it in tmux/nohup with timestamped logs under logs/ and return to the main task.",
    }


def build_coverage(m38: dict[str, Any], runner: dict[str, Any], wrapper: dict[str, Any]) -> dict[str, Any]:
    runner_ready = runner["status"] == "runner_instrumentation_sites_found"
    wrapper_ready = wrapper["status"] == "wrapper_pass_through_sites_found"
    return {
        "status": "temporal_spatial_support_instrumentation_gate_ready",
        "m39_version": M39_VERSION,
        "m38_selected_route": m38.get("selected_route"),
        "m38_support_transfer_pass": bool(m38.get("support_transfer_pass")),
        "m38_stronger_split_feasible_with_current_scans": bool(m38.get("stronger_split_feasible_with_current_scans")),
        "selected_instrumentation_route": "docker_runner_pre_consolidation_support_evidence_v0",
        "selected_insertion_point": "select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped",
        "runner_instrumentation_required": True,
        "runner_instrumentation_site_ready": runner_ready,
        "wrapper_pass_through_site_ready": wrapper_ready,
        "deterministic_postprocessing_route_ready": False,
        "support_field_contract_ready": True,
        "runner_args_contract_ready": True,
        "wrapper_args_contract_ready": True,
        "verification_plan_ready": True,
        "docker_run_executed": False,
        "long_rerun_ready": False,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "next_recommended_unit": "E003-M40 temporal-spatial support runner implementation smoke",
    }


def build_report(
    *,
    coverage: dict[str, Any],
    instrumentation_contract: dict[str, Any],
    support_field_contract: dict[str, Any],
    verification_plan: dict[str, Any],
) -> str:
    insertion = instrumentation_contract["runner_insertion_point"]
    selected_policy = instrumentation_contract["m38_selected_route"]
    m40_smoke = verification_plan["commands_reserved_for_m40_after_runner_edit"][0]["shell"]
    validate = verification_plan["commands_reserved_for_m40_after_runner_edit"][1]["shell"]
    lines = [
        "# E003-M39 Temporal-Spatial Support Instrumentation Gate",
        "",
        f"Implementation unit: `E003-M39_temporal_spatial_support_instrumentation_gate_v0`.",
        "",
        "## Decision",
        "",
        f"- Status: `{coverage['status']}`",
        f"- Selected route: `{coverage['selected_instrumentation_route']}`",
        f"- M38 selected route: `{selected_policy}`",
        f"- Deterministic post-processing route ready: `{str(coverage['deterministic_postprocessing_route_ready']).lower()}`",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`",
        "",
        "## Rationale",
        "",
        "- M38 showed that the current dev-selected post-hoc support filter does not transfer well enough to heldout scans.",
        "- The current artifacts preserve final selected proposals, not the cleaned candidate pool before spatial consolidation and caps.",
        "- Therefore support evidence must be instrumented in the Docker runner before candidates are removed by consolidation or final caps.",
        "",
        "## Insertion Point",
        "",
        f"- Insertion id: `{insertion['id']}`",
        f"- After line: `{insertion['after']['line']}`",
        f"- Before line: `{insertion['before']['line']}`",
        f"- Ready: `{str(insertion['ready']).lower()}`",
        "",
        "## Field Contract",
        "",
        f"- Support policy id: `{support_field_contract['contract_id']}`",
        f"- Compute stage: `{support_field_contract['compute_stage']}`",
        f"- Group key: `{support_field_contract['candidate_group_key']}`",
        f"- Radii: `{support_field_contract['radii_m']}`",
        "",
        "Required per-row fields when enabled include `support_evidence_policy`, `support_group_key`, "
        "`support_group_candidate_count`, `support_group_frame_count`, and radius-specific spatial, temporal, "
        "and neighbor-confidence fields.",
        "",
        "## M40 Verification Commands",
        "",
        "After the runner edit, run:",
        "",
        "```bash",
        m40_smoke,
        validate,
        "```",
        "",
        "## Claim Boundary",
        "",
        "- This gate does not execute a new detector run.",
        "- This gate does not make the real RGB-D/open-vocabulary robustness claim ready.",
        "- It makes the runner-side instrumentation contract ready for M40.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m38-dir", default=DEFAULT_M38_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    m38_dir = args.m38_dir.resolve()
    out_dir = args.out_dir.resolve()
    m38 = load_json(m38_dir / "coverage.json")
    runner = inspect_runner(RUNNER)
    wrapper = inspect_wrapper(WRAPPER)
    support_field_contract = build_support_field_contract()
    instrumentation_contract = build_instrumentation_contract(runner, wrapper, m38)
    verification_plan = build_verification_plan()
    coverage = build_coverage(m38, runner, wrapper)

    write_json(out_dir / "support_field_contract.json", support_field_contract)
    write_json(out_dir / "instrumentation_contract.json", instrumentation_contract)
    write_json(out_dir / "verification_plan.json", verification_plan)
    write_json(out_dir / "coverage.json", coverage)
    write_text(
        out_dir / "report.md",
        build_report(
            coverage=coverage,
            instrumentation_contract=instrumentation_contract,
            support_field_contract=support_field_contract,
            verification_plan=verification_plan,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
