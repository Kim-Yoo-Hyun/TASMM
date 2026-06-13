#!/usr/bin/env python3
"""Execute E008-M156 budget-aware utility rows in Habitat."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M37_PATH = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"

VERSION = "e008_m157_budget_aware_utility_trajectory_execution_v0"
READY_STATUS = "e008_m157_budget_aware_utility_trajectory_execution_ready"
BLOCKED_STATUS = "e008_m157_budget_aware_utility_trajectory_execution_blocked"
NEXT_UNIT = "E008-M158 budget-aware utility trajectory result interpretation / protected-baseline gate"

DEFAULT_M156_CONTRACT = (
    EXP_ROOT / "artifacts" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
)
DEFAULT_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M157_budget_aware_utility_trajectory_execution_v0"
)
DEFAULT_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M157_budget_aware_utility_trajectory_execution_v0"
)

METHOD_POLICY = "budget_aware_confidence_path_utility_v0"
BASELINE_POLICIES = [
    "detector_confidence_reachable_subset_v0",
    "budget_aware_utility_without_path_gain_v0",
    "budget_aware_utility_without_visit_penalty_v0",
    "budget_aware_utility_without_source_gap_bonus_v0",
    "budget_guarded_no_visit_guard_v1",
    "budget_guarded_no_confidence_floor_v1",
]


def load_m37_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m37_runner", M37_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load M37 runner from {M37_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m156-contract", default=str(DEFAULT_M156_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def patch_m37_for_m157(m37: Any, contract: Path, out_root: Path, derived_out_root: Path) -> None:
    m37.VERSION = VERSION
    m37.READY_STATUS = READY_STATUS
    m37.BLOCKED_STATUS = BLOCKED_STATUS
    m37.DEFAULT_M36_CONTRACT = contract
    m37.DEFAULT_ARTIFACT_DIR = out_root
    m37.DEFAULT_DATA_OUT_DIR = derived_out_root
    m37.M03_ARTIFACT_DIR = contract
    m37.M04_ARTIFACT_DIR = contract
    m37.H001_POLICY = METHOD_POLICY
    m37.BASELINE_POLICIES = BASELINE_POLICIES
    m37.build_claim_boundary_rows = build_claim_boundary_rows
    m37.build_route_decision_rows = build_route_decision_rows
    m37.build_report = build_report


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_aware_utility_trajectory_execution",
            "supported": ready,
            "claim_boundary": "M157 executes the fixed M156 budget-aware utility policy suite in Habitat.",
        },
        {
            "version": VERSION,
            "claim_id": "budget_aware_navigation_improvement",
            "supported": False,
            "claim_boundary": "Requires M158 protected-baseline interpretation before any positive navigation claim.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M157 is an internal full-val-mini execution result; final navigation claim still requires interpretation, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M157 target-free rows do not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_budget_aware_utility_trajectory_result"
            if ready
            else "repair_m157_runner_or_contract",
            "selected_next_unit": NEXT_UNIT
            if ready
            else "repair E008-M157 budget-aware utility trajectory execution",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "budget_aware_utility_trajectory_result_ready": ready,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
) -> str:
    m37 = load_m37_module()
    policy_rows = [row for row in aggregate_rows if row.get("metric_scope") == "policy_aggregate"]
    pairwise_summary: list[dict[str, Any]] = []
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_baseline[str(row.get("baseline_policy_id"))].append(row)
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
            "# E008-M157 Budget-Aware Utility Trajectory Execution",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Inside Docker: {coverage['inside_docker']}.",
            f"- Trajectory candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Trajectory attempt rows: {coverage['trajectory_attempt_rows']}.",
            f"- Scan-task-policy metric rows: {coverage['scan_task_policy_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
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
            "- M157 is an execution result, not final interpretation.",
            "- `ObjectNav` goal/viewpoints are used only after stops for metric computation.",
            "- Final `SR` / `SPL`, deployable policy, final RGB-D/open-vocabulary robustness, and human intent as a main claim remain blocked until M158+.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    contract = Path(args.m156_contract)
    out_root = Path(args.out_root)
    derived_out_root = Path(args.derived_out_root)
    if not contract.is_absolute():
        contract = ROOT / contract
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    if not derived_out_root.is_absolute():
        derived_out_root = ROOT / derived_out_root

    m37 = load_m37_module()
    patch_m37_for_m157(m37, contract, out_root, derived_out_root)
    original_argv = sys.argv[:]
    try:
        sys.argv = [
            sys.argv[0],
            "--m36-contract",
            str(contract),
            "--out-root",
            str(out_root),
            "--derived-out-root",
            str(derived_out_root),
        ]
        m37.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
