#!/usr/bin/env python3
"""Execute E008-M50 routine-fetch repair rows as an E008-M51 trajectory smoke."""

from __future__ import annotations

import importlib.util
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M37_PATH = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"

VERSION = "e008_m51_routine_fetch_repair_trajectory_execution_smoke_v0"
READY_STATUS = "e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready"
BLOCKED_STATUS = "e008_m51_routine_fetch_repair_trajectory_execution_smoke_blocked"
NEXT_UNIT = "E008-M52 routine-fetch repair result interpretation and scale decision"

DEFAULT_M50_CONTRACT = EXP_ROOT / "artifacts" / "E008-M50_routine_fetch_repair_trajectory_contract_v0"
DEFAULT_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"
DEFAULT_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"

H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
BASELINE_POLICIES = [
    "static_stale_memory_top1_v0",
    "detector_confidence_budget5_v0",
    "fixed_topk_current_observation_budget5_v0",
    "source_diverse_current_observation_budget5_v1",
    "task_agnostic_source_diverse_budget5_v1",
    "h001_task_conditioned_source_diverse_budget5_v1",
]


def load_m37_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m37_runner", M37_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load M37 runner from {M37_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "routine_fetch_repair_trajectory_smoke",
            "supported": ready,
            "claim_boundary": "M51 executes the M50 repaired routine-fetch rows in Habitat as a smoke test.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M51 is still a tiny controlled HM3D ObjectNav smoke; final navigation claim requires scale and stronger navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context remains a memory-trust/re-observation condition, not natural-language human-intent understanding.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "interpret_routine_fetch_repair_trajectory_result" if ready else "repair_m51_runner",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M51 routine-fetch repair trajectory execution smoke",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "dynamic_stale_navigation_result_ready": ready,
        }
    ]


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> str:
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
            }
        )
    return "\n".join(
        [
            "# E008-M51 Routine-Fetch Repair Trajectory Execution Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Inside Docker: {coverage['inside_docker']}.",
            f"- Trajectory attempt rows: {coverage['trajectory_attempt_rows']}.",
            f"- Scan-task-policy metric rows: {coverage['scan_task_policy_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Dynamic-stale navigation result ready: {coverage['dynamic_stale_navigation_result_ready']}.",
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
                    "OldLocationDeadEndCostM_mean",
                ],
            ),
            "",
            "## H001 Pairwise Delta Summary",
            "",
            m37.markdown_table(
                pairwise_summary,
                ["baseline_policy_id", "rows", "delta_SR_mean", "delta_SPL_mean", "delta_PathLengthM_mean"],
            ),
            "",
            "## Claim Boundary",
            "",
            "- M51 is a repaired routine-fetch trajectory smoke, not a final navigation benchmark.",
            "- `ObjectNav` goal/viewpoints are used only after stops for metric computation.",
            "- Structured task context is not a natural-language human-intent claim.",
            "",
        ]
    )


def main() -> None:
    m37 = load_m37_module()
    m37.VERSION = VERSION
    m37.READY_STATUS = READY_STATUS
    m37.BLOCKED_STATUS = BLOCKED_STATUS
    m37.DEFAULT_M36_CONTRACT = DEFAULT_M50_CONTRACT
    m37.DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR
    m37.DEFAULT_DATA_OUT_DIR = DEFAULT_DATA_OUT_DIR
    m37.H001_POLICY = H001_POLICY
    m37.BASELINE_POLICIES = BASELINE_POLICIES
    m37.build_claim_boundary_rows = build_claim_boundary_rows
    m37.build_route_decision_rows = build_route_decision_rows
    m37.build_report = build_report
    m37.main()


if __name__ == "__main__":
    main()
