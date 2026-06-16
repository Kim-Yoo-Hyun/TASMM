#!/usr/bin/env python3
"""Execute M204 additive source-pool candidate-union rows in Habitat."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M130_TOOL = EXP_ROOT / "tools" / "run_m130_target_free_detector_policy_trajectory_execution_smoke.py"

VERSION = "e008_m205_additive_source_pool_candidate_union_docker_trajectory_execution_v0"
READY_STATUS = "e008_m205_additive_source_pool_candidate_union_docker_trajectory_execution_ready"
BLOCKED_STATUS = "e008_m205_additive_source_pool_candidate_union_docker_trajectory_execution_blocked"
NEXT_UNIT = "E008-M206 additive source-pool candidate-union trajectory result interpretation"

SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
BASELINE_POLICIES = [
    "no_source_pool_detector_confidence_reachable_subset_v0",
    "source_pool_replacement_detector_confidence_reachable_subset_v0",
    "additive_union_unguarded_confidence_sort_v0",
]

DEFAULT_M204_CONTRACT = (
    EXP_ROOT / "artifacts" / "E008-M204_additive_source_pool_candidate_union_docker_trajectory_contract_v0"
)
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M205_additive_source_pool_candidate_union_docker_trajectory_execution_v0"
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m204-contract", default=str(DEFAULT_M204_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "additive_candidate_union_trajectory_smoke",
            "supported": ready,
            "claim_boundary": "M205 executes M204 additive source-pool candidate-union rows in Habitat as a bounded trajectory smoke.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M205 is not a final navigation benchmark until protected-baseline interpretation, heldout transfer, and external navigation/search baselines pass.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M205 tests one additive source-pool route; it does not establish final RGB-D/open-vocabulary robustness.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M205 rows do not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_additive_candidate_union_trajectory_result"
            if ready
            else "repair_m205_runtime_or_contract",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M205 additive source-pool trajectory execution",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "additive_candidate_union_trajectory_result_ready": ready,
        }
    ]


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> str:
    m37 = load_module(
        EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py",
        "e008_m37_report_helper_for_m205",
    )
    policy_rows = [row for row in aggregate_rows if row.get("metric_scope") == "policy_aggregate"]
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_baseline[str(row.get("baseline_policy_id"))].append(row)
    pairwise_summary = []
    for baseline_id, rows in sorted(by_baseline.items()):
        pairwise_summary.append(
            {
                "baseline_policy_id": baseline_id,
                "rows": len(rows),
                "delta_SR_mean": m37.mean([m37.finite_float(row.get("delta_SR")) for row in rows]),
                "delta_SPL_mean": m37.mean([m37.finite_float(row.get("delta_SPL")) for row in rows]),
                "delta_PathLengthM_mean": m37.mean([m37.finite_float(row.get("delta_PathLengthM")) for row in rows]),
                "delta_CandidateVisits_mean": m37.mean(
                    [
                        m37.finite_float(row.get("method_CandidateVisits"))
                        - m37.finite_float(row.get("baseline_CandidateVisits"))
                        for row in rows
                        if m37.finite_float(row.get("method_CandidateVisits")) is not None
                        and m37.finite_float(row.get("baseline_CandidateVisits")) is not None
                    ]
                ),
            }
        )
    return "\n".join(
        [
            "# E008-M205 Additive Source-Pool Candidate-Union Docker Trajectory Execution",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Inside Docker: {coverage['inside_docker']}.",
            f"- Trajectory candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Trajectory attempt rows: {coverage['trajectory_attempt_rows']}.",
            f"- Scan-policy metric rows: {coverage['scan_task_policy_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Final real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.",
            "",
            "## Policy Aggregates",
            "",
            m37.markdown_table(
                policy_rows,
                [
                    "group_id",
                    "success_rows",
                    "scan_task_policy_rows",
                    "SR",
                    "SPL",
                    "PathLengthM_mean",
                    "CandidateVisits_mean",
                    "StopRank_mean_over_success",
                ],
            ),
            "",
            "## Pairwise Delta Summary",
            "",
            m37.markdown_table(
                pairwise_summary,
                [
                    "baseline_policy_id",
                    "rows",
                    "delta_SR_mean",
                    "delta_SPL_mean",
                    "delta_PathLengthM_mean",
                    "delta_CandidateVisits_mean",
                ],
            ),
            "",
            "## Claim Boundary",
            "",
            "- M205 is an executed bounded trajectory smoke, not a final navigation benchmark.",
            "- `ObjectNav` goal/viewpoints are used only after stops for metric computation.",
            "- Human intent, deployable policy, final RGB-D/open-vocabulary robustness, and final `SR` / `SPL` remain blocked.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    m130 = load_module(M130_TOOL, "e008_m130_runner_for_m205")

    m130.VERSION = VERSION
    m130.READY_STATUS = READY_STATUS
    m130.BLOCKED_STATUS = BLOCKED_STATUS
    m130.NEXT_UNIT = NEXT_UNIT
    m130.DEFAULT_M129_CONTRACT = Path(args.m204_contract)
    m130.DEFAULT_ARTIFACT_DIR = Path(args.out_root)
    m130.DEFAULT_DATA_OUT_DIR = Path(args.derived_out_root)
    m130.METHOD_POLICY = SELECTED_POLICY
    m130.BASELINE_POLICIES = BASELINE_POLICIES
    m130.build_claim_boundary_rows = build_claim_boundary_rows
    m130.build_route_decision_rows = build_route_decision_rows
    m130.build_report = build_report

    original_argv = sys.argv[:]
    try:
        sys.argv = [
            sys.argv[0],
            "--m129-contract",
            str(args.m204_contract),
            "--out-root",
            str(args.out_root),
            "--derived-out-root",
            str(args.derived_out_root),
        ]
        m130.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
