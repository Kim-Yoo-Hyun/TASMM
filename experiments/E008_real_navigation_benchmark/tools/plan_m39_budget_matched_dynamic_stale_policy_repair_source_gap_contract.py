#!/usr/bin/env python3
"""Plan budget-matched dynamic-stale policy repair after E008-M38."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M39_budget_matched_policy_repair_source_gap_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M39_budget_matched_policy_repair_source_gap_contract_v0"
)
VERSION = "e008_m39_budget_matched_policy_repair_source_gap_contract_v0"

M36_DIR = EXP_ROOT / "artifacts" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
M37_DIR = EXP_ROOT / "artifacts" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
M38_DIR = EXP_ROOT / "artifacts" / "E008-M38_dynamic_stale_overlay_result_interpretation_baseline_alignment_v0"

PRIMARY_BUDGET = 5
DIAGNOSTIC_BUDGETS = [3, 5, 8, 10, 12]

STATIC_POLICY = "static_stale_memory_top1_v0"
FIXED_TOPK_POLICY = "fixed_topk_current_observation_v0"
DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
TASK_AGNOSTIC_POLICY = "task_agnostic_memory_trust_navigation_v0"
H001_POLICY = "h001_task_conditioned_memory_trust_navigation_v0"

NEXT_UNIT = "E008-M40 budget-matched repair row materialization smoke"

BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "trajectory_success",
    "success_proposal_uid",
    "success_source_role",
    "success_dynamic_stale_overlay_role",
    "FailureType",
    "SR",
    "SPL",
    "StopRank",
    "PathLengthM",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def scan_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def success_within_budget(row: dict[str, Any], budget: int) -> bool:
    stop_rank = finite_float(row.get("StopRank"))
    return bool(row.get("trajectory_success")) and stop_rank is not None and stop_rank <= budget


def aggregate_metric_rows(rows: list[dict[str, Any]], extra: dict[str, Any]) -> dict[str, Any]:
    success_rows = sum(1 for row in rows if bool(row.get("trajectory_success")))
    return {
        **extra,
        "rows": len(rows),
        "success_rows": success_rows,
        "SR": safe_ratio(success_rows, len(rows)),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "OldLocationDeadEndCostM_mean": mean([finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]),
        "StopRank_mean_over_success": mean(
            [finite_float(row.get("StopRank")) for row in rows if bool(row.get("trajectory_success"))]
        ),
        "stale_visit_first_rows": sum(1 for row in rows if bool(row.get("stale_visit_first"))),
        "current_observation_first_rows": sum(1 for row in rows if bool(row.get("current_observation_first"))),
        "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
    }


def build_budget_alignment_rows(metrics: list[dict[str, Any]], plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan_index = {str(row.get("policy_plan_uid")): row for row in plans}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        scope = "source_gap" if bool(row.get("diagnostic_source_gap_boundary")) else "source_ready"
        grouped[(str(row.get("policy_id")), scope)].append(row)
        grouped[(str(row.get("policy_id")), "all_rows")].append(row)

    rows: list[dict[str, Any]] = []
    policies = [DETECTOR_POLICY, FIXED_TOPK_POLICY, H001_POLICY, STATIC_POLICY, TASK_AGNOSTIC_POLICY]
    for policy_id in policies:
        for scope in ["source_ready", "source_gap", "all_rows"]:
            current = grouped.get((policy_id, scope), [])
            if not current:
                continue
            plan_rows = [plan_index.get(str(row.get("policy_plan_uid")), {}) for row in current]
            budget_fields = {
                f"cap{budget}_success_rows": sum(1 for row in current if success_within_budget(row, budget))
                for budget in DIAGNOSTIC_BUDGETS
            }
            budget_fields.update(
                {
                    f"cap{budget}_SR": safe_ratio(budget_fields[f"cap{budget}_success_rows"], len(current))
                    for budget in DIAGNOSTIC_BUDGETS
                }
            )
            aggregate = aggregate_metric_rows(
                current,
                {
                    "version": VERSION,
                    "policy_id": policy_id,
                    "budget_scope": scope,
                    "primary_budget_cap": PRIMARY_BUDGET,
                    "candidate_rows_mean": mean([finite_float(plan.get("candidate_rows")) for plan in plan_rows]),
                    "path_ready_candidate_rows_mean": mean(
                        [finite_float(plan.get("path_ready_candidate_rows")) for plan in plan_rows]
                    ),
                    "candidate_budget_mismatch": classify_budget_mismatch(policy_id, scope, current),
                    **budget_fields,
                },
            )
            rows.append(aggregate)
    return rows


def classify_budget_mismatch(policy_id: str, scope: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_rows"
    cap5_sr = safe_ratio(sum(1 for row in rows if success_within_budget(row, PRIMARY_BUDGET)), len(rows))
    full_sr = safe_ratio(sum(1 for row in rows if bool(row.get("trajectory_success"))), len(rows))
    stop_mean = mean([finite_float(row.get("StopRank")) for row in rows if bool(row.get("trajectory_success"))])
    if policy_id == DETECTOR_POLICY and scope == "source_gap" and full_sr > cap5_sr:
        return "detector_success_requires_over_budget_search"
    if policy_id == H001_POLICY and scope == "source_ready" and full_sr > cap5_sr:
        return "h001_source_ready_success_delayed_by_stale_first_or_visit_order"
    if scope == "source_gap" and full_sr == 0.0:
        return "bounded_source_gap_failure"
    if scope == "source_ready" and cap5_sr == full_sr == 1.0:
        return "budget_matched_source_ready_success"
    return f"full_sr_{fmt(full_sr)}_cap5_sr_{fmt(cap5_sr)}_stop_mean_{fmt(stop_mean)}"


def build_repair_policy_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": "static_stale_memory_top1_v0",
            "policy_role": "naive_lower_bound",
            "materialize_in_m40": True,
            "primary_budget_cap": 1,
            "allowed_inputs": "stale old-memory candidate pose, category, episode start",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "old-location false positive under dynamic stale memory",
            "claim_role": "naive static memory lower bound",
        },
        {
            "version": VERSION,
            "policy_id": "fixed_topk_current_observation_budget5_v0",
            "policy_role": "budget_matched_current_only_baseline",
            "materialize_in_m40": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "allowed_inputs": "current observation candidates, detector confidence, navmesh path-ready fields, fixed top-5 budget",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "source-gap rows where target appears after budget or not in current top-5",
            "claim_role": "required baseline: why not simply use current observations",
        },
        {
            "version": VERSION,
            "policy_id": "detector_confidence_budget5_v0",
            "policy_role": "budget_matched_detector_baseline",
            "materialize_in_m40": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "allowed_inputs": "current observation candidates, detector confidence, navmesh reachability/path-ready fields",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "same source-gap top-5 miss as fixed current top-k",
            "claim_role": "budget-matched detector confidence baseline",
        },
        {
            "version": VERSION,
            "policy_id": "task_agnostic_dead_end_penalized_budget5_v0",
            "policy_role": "ablation_no_task_context",
            "materialize_in_m40": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "allowed_inputs": "staleness flag, old-location dead-end cost, current proposal reliability, path cost, no task utility differences",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "cannot alter trust/re-observation by task value",
            "claim_role": "task-context ablation",
        },
        {
            "version": VERSION,
            "policy_id": "h001_dead_end_penalized_budget5_v0",
            "policy_role": "test_method_repair",
            "materialize_in_m40": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "allowed_inputs": "structured task context, stale-memory flag, old-location dead-end cost, current proposal confidence, path/reachability fields",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "if task-conditioned trust is still not better than task-agnostic or fixed current top-k, H001 navigation claim remains blocked",
            "claim_role": "repaired H001 policy under equal budget",
        },
        {
            "version": VERSION,
            "policy_id": "detector_confidence_all_candidates_upper_bound_v0",
            "policy_role": "diagnostic_upper_bound_not_primary",
            "materialize_in_m40": False,
            "primary_budget_cap": "all_candidates",
            "allowed_inputs": "current observation candidates and detector confidence only",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "not budget matched; should be reported only as source coverage upper bound",
            "claim_role": "diagnostic upper bound only",
        },
        {
            "version": VERSION,
            "policy_id": "source_gap_expand_then_budget5_v0",
            "policy_role": "future_source_expansion_route",
            "materialize_in_m40": False,
            "primary_budget_cap": PRIMARY_BUDGET,
            "allowed_inputs": "source-gap flag from allowed pre-execution source coverage diagnostics, bounded additional observation/source expansion contract",
            "blocked_inputs": sorted(BLOCKED_POLICY_FIELDS),
            "expected_failure": "requires new observation/source materialization before trajectory execution",
            "claim_role": "future route for source-gap rows, not an M40 policy row",
        },
    ]


def build_repair_principle_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "principle_id": "budget_match_before_navigation_claim",
            "diagnosed_failure": "Detector confidence succeeds on source-gap rows only after 12/19/30 current candidates, so full-detector success is not a fair bounded policy baseline.",
            "method_requirement": "Every primary policy row must share a fixed candidate-stop budget, with full-detector reported as an upper bound.",
            "next_test": "M40 materializes cap-5 detector, fixed current, task-agnostic repair, and H001 repair rows.",
        },
        {
            "version": VERSION,
            "principle_id": "dead_end_penalty_before_stale_first",
            "diagnosed_failure": "H001 loses source-ready cap-5 success and SPL because stale old-memory is visited before current evidence in 12/18 rows.",
            "method_requirement": "Stale old-memory can be visited before current evidence only when old-location dead-end cost is low or current evidence is weak under the task context.",
            "next_test": "M40 materializes `h001_dead_end_penalized_budget5_v0` and its task-agnostic ablation.",
        },
        {
            "version": VERSION,
            "principle_id": "source_gap_separation",
            "diagnosed_failure": "Source-gap rows cannot be solved by bounded ranking alone under the current candidate source.",
            "method_requirement": "Report source-ready and source-gap rows separately; treat source-gap repair as source expansion, not merely policy reranking.",
            "next_test": "M40 keeps source-gap rows visible and marks them separately in readiness gates.",
        },
        {
            "version": VERSION,
            "principle_id": "task_context_secondary_until_gain",
            "diagnosed_failure": "Task-conditioned H001 does not improve SR over task-agnostic memory trust in M37/M38.",
            "method_requirement": "Task context stays an ablation until it changes budgeted success, SPL, or dead-end cost beyond task-agnostic trust.",
            "next_test": "Compare `h001_dead_end_penalized_budget5_v0` to `task_agnostic_dead_end_penalized_budget5_v0`.",
        },
    ]


def build_source_gap_contract_rows(budget_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["policy_id"], row["budget_scope"]): row for row in budget_rows}
    detector_gap = by_key.get((DETECTOR_POLICY, "source_gap"), {})
    fixed_gap = by_key.get((FIXED_TOPK_POLICY, "source_gap"), {})
    h001_gap = by_key.get((H001_POLICY, "source_gap"), {})
    detector_ready = by_key.get((DETECTOR_POLICY, "source_ready"), {})
    h001_ready = by_key.get((H001_POLICY, "source_ready"), {})
    task_ready = by_key.get((TASK_AGNOSTIC_POLICY, "source_ready"), {})
    return [
        {
            "version": VERSION,
            "contract_scope": "source_ready_primary_policy_table",
            "rows": h001_ready.get("rows"),
            "primary_budget_cap": PRIMARY_BUDGET,
            "required_comparison": "H001 repair must match or beat fixed current top-k and task-agnostic repair on SR/SPL/dead-end cost.",
            "current_evidence": f"H001 full SR {fmt(h001_ready.get('SR'))}, cap5 SR {fmt(h001_ready.get('cap5_SR'))}; task-agnostic cap5 SR {fmt(task_ready.get('cap5_SR'))}; detector cap5 SR {fmt(detector_ready.get('cap5_SR'))}.",
            "paper_handling": "eligible for primary policy comparison after M40/M41 execution.",
        },
        {
            "version": VERSION,
            "contract_scope": "source_gap_separate_boundary",
            "rows": h001_gap.get("rows"),
            "primary_budget_cap": PRIMARY_BUDGET,
            "required_comparison": "Do not count source-gap rows as a pure policy failure without separate source-expansion analysis.",
            "current_evidence": f"H001 cap5 SR {fmt(h001_gap.get('cap5_SR'))}; fixed current cap5 SR {fmt(fixed_gap.get('cap5_SR'))}; detector cap5 SR {fmt(detector_gap.get('cap5_SR'))}; detector full SR {fmt(detector_gap.get('SR'))}.",
            "paper_handling": "report as source-gap lower-bound and source-expansion requirement.",
        },
        {
            "version": VERSION,
            "contract_scope": "detector_upper_bound_boundary",
            "rows": detector_gap.get("rows"),
            "primary_budget_cap": "not_primary",
            "required_comparison": "Full detector confidence is an upper bound because it requires over-budget search on source-gap rows.",
            "current_evidence": f"source-gap detector cap5 SR {fmt(detector_gap.get('cap5_SR'))}, cap12 SR {fmt(detector_gap.get('cap12_SR'))}, full SR {fmt(detector_gap.get('SR'))}, mean visits {fmt(detector_gap.get('CandidateVisits_mean'))}.",
            "paper_handling": "upper-bound / coverage diagnostic only.",
        },
    ]


def build_allowed_input_contract_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for policy in policy_rows:
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy["policy_id"],
                "materialize_in_m40": policy["materialize_in_m40"],
                "allowed_inputs": policy["allowed_inputs"],
                "blocked_inputs": policy["blocked_inputs"],
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
                "uses_m37_metric_for_policy": False,
                "can_use_m37_metric_for_diagnostic_after_execution": True,
            }
        )
    return rows


def build_m40_materialization_plan_rows(
    m36_plans: list[dict[str, Any]],
    policy_contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    h001_rows = [row for row in m36_plans if row.get("policy_id") == H001_POLICY]
    policy_ids = [row["policy_id"] for row in policy_contract_rows if row.get("materialize_in_m40")]
    rows = []
    for base in sorted(h001_rows, key=lambda row: str(row.get("policy_plan_uid"))):
        for policy_id in policy_ids:
            rows.append(
                {
                    "version": VERSION,
                    "m40_plan_uid": f"m40::{base.get('adapter_episode_id')}::{base.get('task_context_id')}::{policy_id}",
                    "source_m36_policy_plan_uid": base.get("policy_plan_uid"),
                    "adapter_episode_id": base.get("adapter_episode_id"),
                    "scan_id": base.get("scan_id"),
                    "scene_key": base.get("scene_key"),
                    "object_category": base.get("object_category"),
                    "task_context_id": base.get("task_context_id"),
                    "policy_id": policy_id,
                    "primary_budget_cap": 1 if policy_id == STATIC_POLICY else PRIMARY_BUDGET,
                    "diagnostic_source_gap_boundary": bool(base.get("diagnostic_source_gap_boundary")),
                    "source_gap_handling": (
                        "separate_source_gap_boundary"
                        if bool(base.get("diagnostic_source_gap_boundary"))
                        else "source_ready_primary_policy_table"
                    ),
                    "requires_candidate_rematerialization": True,
                    "requires_docker_execution": False,
                    "runner_after_materialization": "E008-M41 budget-matched repair trajectory execution smoke",
                    "policy_input_uses_eval_goal_or_viewpoint": False,
                    "policy_input_uses_success_label": False,
                    "uses_m37_metric_for_policy": False,
                    "claim_boundary": "M39 creates only the materialization contract; no repaired trajectory result is produced.",
                }
            )
    return rows


def build_readiness_gate_rows(
    budget_rows: list[dict[str, Any]],
    m40_plan_rows: list[dict[str, Any]],
    policy_contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cap5_detector_gap = next(
        (row for row in budget_rows if row.get("policy_id") == DETECTOR_POLICY and row.get("budget_scope") == "source_gap"),
        {},
    )
    h001_ready = next(
        (row for row in budget_rows if row.get("policy_id") == H001_POLICY and row.get("budget_scope") == "source_ready"),
        {},
    )
    return [
        {
            "version": VERSION,
            "gate_id": "m40_materialization_contract_ready",
            "status": "pass" if m40_plan_rows else "fail",
            "evidence": f"m40 plan rows {len(m40_plan_rows)} from {len(policy_contract_rows)} policy contract rows.",
            "next_action": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "gate_id": "budget_mismatch_confirmed",
            "status": "pass" if cap5_detector_gap.get("cap5_SR") == 0.0 and cap5_detector_gap.get("SR") == 1.0 else "warning",
            "evidence": f"source-gap detector cap5 SR {fmt(cap5_detector_gap.get('cap5_SR'))}, full SR {fmt(cap5_detector_gap.get('SR'))}.",
            "next_action": "keep full detector as upper bound and add budget-matched detector row",
        },
        {
            "version": VERSION,
            "gate_id": "h001_source_ready_repair_needed",
            "status": "pass" if h001_ready.get("cap5_SR") is not None and h001_ready.get("cap5_SR") < h001_ready.get("SR") else "warning",
            "evidence": f"H001 source-ready full SR {fmt(h001_ready.get('SR'))}, cap5 SR {fmt(h001_ready.get('cap5_SR'))}.",
            "next_action": "materialize dead-end-penalized budget5 H001 repair",
        },
        {
            "version": VERSION,
            "gate_id": "scale_up_blocked_until_repair",
            "status": "pass",
            "evidence": "M38 marked scale_up_recommended_now false; M39 preserves repair-before-scale.",
            "next_action": "do not launch broader navigation reruns before M40/M41",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_matched_repair_contract",
            "supported": True,
            "boundary": "M39 supports a policy/source-gap contract for the next materialization step, not a trajectory result.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_navigation_improvement",
            "supported": False,
            "boundary": "Still blocked until repaired rows are materialized and executed under budget-matched baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_policy_failure",
            "supported": False,
            "boundary": "Source-gap rows are separated from primary policy failure until source expansion is implemented.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "boundary": "Task context remains an ablation until it beats task-agnostic repair under the same budget.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "boundary": "Final navigation claim requires M40/M41 execution, scale, and navigation/search baselines.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m39_next_unit",
            "decision": "materialize_budget_matched_repair_rows_next",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M39 has a fixed budget contract and source-gap boundary; next step is row materialization before Docker trajectory execution.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m39_no_scale_yet",
            "decision": "do_not_scale_before_repair_execution",
            "selected_next_unit": NEXT_UNIT,
            "reason": "Current H001 loses to budget-matched current-observation efficiency on source-ready rows and cannot solve source-gap rows.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    budget_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E008-M39 Budget-Matched Policy Repair / Source-Gap Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Input M38 status: `{coverage['m38_status']}`.",
        f"- Primary budget cap: {coverage['primary_budget_cap']} stops.",
        f"- M40 materialization plan rows: {coverage['m40_materialization_plan_rows']}.",
        f"- Source-ready rows: {coverage['source_ready_rows']}.",
        f"- Source-gap rows: {coverage['source_gap_rows']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Budget Alignment",
        "",
        "| policy_id | scope | rows | full SR | cap5 SR | SPL | visits | mismatch |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in budget_rows:
        if row.get("budget_scope") in {"source_ready", "source_gap"}:
            lines.append(
                "| {policy} | {scope} | {rows} | {sr} | {cap5} | {spl} | {visits} | {mismatch} |".format(
                    policy=row.get("policy_id"),
                    scope=row.get("budget_scope"),
                    rows=row.get("rows"),
                    sr=fmt(row.get("SR")),
                    cap5=fmt(row.get("cap5_SR")),
                    spl=fmt(row.get("SPL")),
                    visits=fmt(row.get("CandidateVisits_mean")),
                    mismatch=row.get("candidate_budget_mismatch"),
                )
            )
    lines.extend(
        [
            "",
            "## Repair Policies",
            "",
            "| policy_id | role | materialize | budget | claim_role |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in policy_rows:
        lines.append(
            f"| {row['policy_id']} | {row['policy_role']} | {row['materialize_in_m40']} | {row['primary_budget_cap']} | {row['claim_role']} |"
        )
    lines.extend(
        [
            "",
            "## Source-Gap Contract",
            "",
        ]
    )
    for row in source_gap_rows:
        lines.append(f"- `{row['contract_scope']}`: {row['paper_handling']} {row['current_evidence']}")
    lines.extend(
        [
            "",
            "## Readiness Gates",
            "",
        ]
    )
    for row in readiness_rows:
        lines.append(f"- `{row['gate_id']}`: {row['status']}. {row['evidence']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}`: supported={str(row['supported']).lower()}. {row['boundary']}")
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            f"- Selected next unit: {route_rows[0]['selected_next_unit']}.",
            f"- Decision: `{route_rows[0]['decision']}`.",
            f"- Reason: {route_rows[0]['reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m36_cov = read_json(M36_DIR / "coverage.json")
    m37_cov = read_json(M37_DIR / "coverage.json")
    m38_cov = read_json(M38_DIR / "coverage.json")
    m36_plans = read_jsonl(M36_DIR / "trajectory_execution_plan_rows.jsonl")
    m37_all_metrics = read_jsonl(M37_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    m37_metrics = scan_policy_rows(m37_all_metrics)

    budget_rows = build_budget_alignment_rows(m37_metrics, m36_plans)
    policy_contract_rows = build_repair_policy_contract_rows()
    principle_rows = build_repair_principle_rows()
    source_gap_rows = build_source_gap_contract_rows(budget_rows)
    allowed_input_rows = build_allowed_input_contract_rows(policy_contract_rows)
    m40_plan_rows = build_m40_materialization_plan_rows(m36_plans, policy_contract_rows)
    readiness_rows = build_readiness_gate_rows(budget_rows, m40_plan_rows, policy_contract_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    source_ready_rows = len(
        {
            (row.get("adapter_episode_id"), row.get("task_context_id"))
            for row in m37_metrics
            if row.get("policy_id") == H001_POLICY and not bool(row.get("diagnostic_source_gap_boundary"))
        }
    )
    source_gap_count = len(
        {
            (row.get("adapter_episode_id"), row.get("task_context_id"))
            for row in m37_metrics
            if row.get("policy_id") == H001_POLICY and bool(row.get("diagnostic_source_gap_boundary"))
        }
    )
    coverage = {
        "version": VERSION,
        "status": "e008_m39_budget_matched_policy_repair_source_gap_contract_ready",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m36_status": m36_cov.get("status"),
        "m37_status": m37_cov.get("status"),
        "m38_status": m38_cov.get("status"),
        "primary_budget_cap": PRIMARY_BUDGET,
        "diagnostic_budgets": DIAGNOSTIC_BUDGETS,
        "m37_scan_task_policy_rows": len(m37_metrics),
        "m36_execution_plan_rows": len(m36_plans),
        "budget_alignment_rows": len(budget_rows),
        "repair_policy_contract_rows": len(policy_contract_rows),
        "repair_principle_rows": len(principle_rows),
        "source_gap_contract_rows": len(source_gap_rows),
        "allowed_input_contract_rows": len(allowed_input_rows),
        "m40_materialization_plan_rows": len(m40_plan_rows),
        "readiness_gate_rows": len(readiness_rows),
        "claim_boundary_rows": len(claim_rows),
        "route_decision_rows": len(route_rows),
        "source_ready_rows": source_ready_rows,
        "source_gap_rows": source_gap_count,
        "budget_matched_policy_repair_contract_ready": bool(m40_plan_rows),
        "source_gap_contract_ready": bool(source_gap_rows),
        "scale_up_recommended_now": False,
        "trajectory_execution_launched": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "budget_alignment_rows.jsonl", budget_rows)
    write_jsonl(ARTIFACT_DIR / "repair_policy_contract_rows.jsonl", policy_contract_rows)
    write_jsonl(ARTIFACT_DIR / "repair_principle_rows.jsonl", principle_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_contract_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_contract_rows.jsonl", allowed_input_rows)
    write_jsonl(ARTIFACT_DIR / "m40_materialization_plan_rows.jsonl", m40_plan_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, budget_rows, policy_contract_rows, source_gap_rows, readiness_rows, claim_rows, route_rows),
        encoding="utf-8",
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "budget_alignment_rows.jsonl", budget_rows)
    write_jsonl(DATA_OUT_DIR / "repair_policy_contract_rows.jsonl", policy_contract_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_contract_rows.jsonl", source_gap_rows)
    write_jsonl(DATA_OUT_DIR / "m40_materialization_plan_rows.jsonl", m40_plan_rows)
    write_jsonl(DATA_OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
