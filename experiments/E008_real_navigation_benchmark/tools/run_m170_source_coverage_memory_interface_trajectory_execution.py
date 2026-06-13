#!/usr/bin/env python3
"""Execute E008-M169 source-coverage memory-interface rows in Habitat."""

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

VERSION = "e008_m170_source_coverage_memory_interface_trajectory_execution_v0"
READY_STATUS = "e008_m170_source_coverage_memory_interface_trajectory_execution_ready"
BLOCKED_STATUS = "e008_m170_source_coverage_memory_interface_trajectory_execution_blocked"
NEXT_UNIT = "E008-M171 source-coverage memory-interface trajectory result interpretation / protected-baseline gate"

DEFAULT_M169_CONTRACT = EXP_ROOT / "artifacts" / "E008-M169_source_coverage_memory_interface_trajectory_contract_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"

METHOD_POLICY = "source_coverage_memory_interface_policy_v1"
BASELINE_POLICIES = [
    "detector_confidence_reachable_subset_v0",
    "source_coverage_only_task_agnostic_v1",
    "confidence_floor_only_v1",
    "path_cost_only_reachable_subset_v1",
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
    parser.add_argument("--m169-contract", default=str(DEFAULT_M169_CONTRACT))
    parser.add_argument("--out-root", default=str(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DATA_OUT_DIR))
    return parser.parse_args()


def patch_m37_for_m170(m37: Any, contract: Path, out_root: Path, derived_out_root: Path) -> None:
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
            "claim_id": "source_coverage_memory_interface_trajectory_execution",
            "supported": ready,
            "claim_boundary": "M170 executes the fixed M169 source-coverage memory-interface policy suite in Habitat.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_memory_interface_navigation_improvement",
            "supported": False,
            "claim_boundary": "Requires M171 protected-baseline interpretation before any positive navigation claim.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Requires interpretation, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_source_coverage_memory_interface_trajectory_result" if ready else "repair_m170_runner_or_contract",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M170 source-coverage memory-interface trajectory execution",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "source_coverage_memory_interface_trajectory_result_ready": ready,
        }
    ]


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> str:
    m37 = load_m37_module()
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
            }
        )
    return "\n".join(
        [
            "# E008-M170 Source-Coverage Memory-Interface Trajectory Execution",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Trajectory candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Scan-task-policy metric rows: {coverage['scan_task_policy_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Aggregates",
            "",
            m37.markdown_table(policy_rows, ["group_id", "success_rows", "scan_task_policy_rows", "SR", "SPL", "PathLengthM_mean", "CandidateVisits_mean"]),
            "",
            "## Pairwise Delta Summary",
            "",
            m37.markdown_table(pairwise_summary, ["baseline_policy_id", "rows", "delta_SR_mean", "delta_SPL_mean", "delta_PathLengthM_mean"]),
            "",
            "## Claim Boundary",
            "",
            "- M170 is an execution result, not final interpretation.",
            "- `ObjectNav` goal/viewpoints are used only after stops for metric computation.",
            "- Positive navigation claims require M171 protected-baseline interpretation.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    contract = Path(args.m169_contract)
    out_root = Path(args.out_root)
    derived_out_root = Path(args.derived_out_root)
    if not contract.is_absolute():
        contract = ROOT / contract
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    if not derived_out_root.is_absolute():
        derived_out_root = ROOT / derived_out_root

    m37 = load_m37_module()
    patch_m37_for_m170(m37, contract, out_root, derived_out_root)
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
