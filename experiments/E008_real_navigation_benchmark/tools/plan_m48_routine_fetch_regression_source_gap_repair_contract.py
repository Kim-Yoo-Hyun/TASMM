#!/usr/bin/env python3
"""Plan routine-fetch task-context regression and source-gap repair contract."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M48_routine_fetch_task_context_regression_source_gap_repair_contract_v0"
)

M44_DIR = EXP_ROOT / "artifacts" / "E008-M44_source_diverse_redesign_row_materialization_smoke_v0"
M46_DIR = EXP_ROOT / "artifacts" / "E008-M46_source_diverse_redesign_trajectory_execution_smoke_v0"
M47_DIR = EXP_ROOT / "artifacts" / "E008-M47_source_diverse_result_interpretation_scale_decision_v0"

VERSION = "e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_v0"
READY_STATUS = "e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_ready"
BLOCKED_STATUS = "e008_m48_routine_fetch_task_context_regression_source_gap_repair_contract_blocked"
NEXT_UNIT = "E008-M49 routine-fetch regression repair row materialization smoke"

STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_CURRENT_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_DIVERSE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
H001_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
REPAIR_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"

BASELINE_POLICIES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]
M49_POLICIES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
    REPAIR_POLICY,
]

PRIMARY_BUDGET = 5
EXPECTED_SCAN_TASK_ROWS = 18

ALLOWED_POLICY_FIELDS = [
    "adapter_episode_id",
    "scan_id",
    "scene_key",
    "task_context_id",
    "object_category",
    "policy_id",
    "candidate_source_role",
    "source_role",
    "dynamic_stale_overlay_role",
    "proposal_uid",
    "raw_candidate_uid",
    "frame_id",
    "label_canonical",
    "confidence",
    "ranking_score",
    "path_ready",
    "candidate_usable_for_path_smoke",
    "source_to_candidate_path_cost_m",
    "source_diversity_key",
    "candidate_position_m",
    "snapped_position_m",
    "execution_stop_position_m",
    "primary_budget_cap",
]

BLOCKED_POLICY_FIELDS = [
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_viewpoints",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "eval_success",
    "trajectory_success",
    "SR",
    "SPL",
    "StopRank",
    "PathLengthM",
    "FailureType",
    "success_proposal_uid",
    "success_source_role",
    "success_dynamic_stale_overlay_role",
    "diagnostic_source_gap_boundary",
    "diagnostic_source_gap_boundary_for_reporting",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "NA"
    return str(value)


def scan_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_task_policy"]


def policy_plan_uid(adapter_episode_id: str, task_context_id: str, policy_id: str) -> str:
    return f"m44::{adapter_episode_id}::{task_context_id}::{policy_id}"


def index_by_plan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def index_metric_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        out[(str(row.get("adapter_episode_id")), str(row.get("task_context_id")), str(row.get("policy_id")))] = row
    return out


def visit_summary(rows: list[dict[str, Any]], success_proposal_uid: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        proposal_uid = str(row.get("proposal_uid") or "")
        out.append(
            {
                "visit_rank": row.get("visit_rank"),
                "proposal_uid": proposal_uid,
                "frame_id": row.get("frame_id"),
                "candidate_source_role": row.get("candidate_source_role"),
                "dynamic_stale_overlay_role": row.get("dynamic_stale_overlay_role"),
                "candidate_order_component": row.get("candidate_order_component"),
                "confidence": row.get("confidence"),
                "ranking_score": row.get("ranking_score"),
                "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
                "diagnostic_is_success_proposal": bool(success_proposal_uid and proposal_uid == success_proposal_uid),
            }
        )
    return out


def success_rank(rows: list[dict[str, Any]], success_proposal_uid: str | None) -> int | None:
    if not success_proposal_uid:
        return None
    for row in rows:
        if str(row.get("proposal_uid")) == str(success_proposal_uid):
            return int(row.get("visit_rank") or 0)
    return None


def proposal_rank(rows: list[dict[str, Any]], proposal_uid: str | None) -> int | None:
    if not proposal_uid:
        return None
    for row in rows:
        if str(row.get("proposal_uid")) == str(proposal_uid):
            return int(row.get("visit_rank") or 0)
    return None


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def build_regression_diagnosis_rows(
    regression_rows: list[dict[str, Any]],
    metric_by_key: dict[tuple[str, str, str], dict[str, Any]],
    rows_by_plan: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for reg in sorted(regression_rows, key=lambda row: (str(row.get("adapter_episode_id")), str(row.get("object_category")))):
        episode_id = str(reg.get("adapter_episode_id"))
        task_context_id = str(reg.get("task_context_id"))
        object_category = str(reg.get("object_category"))
        h001 = metric_by_key.get((episode_id, task_context_id, H001_POLICY), {})
        task_agnostic = metric_by_key.get((episode_id, task_context_id, TASK_AGNOSTIC_POLICY), {})
        detector = metric_by_key.get((episode_id, task_context_id, DETECTOR_POLICY), {})
        source_diverse = metric_by_key.get((episode_id, task_context_id, SOURCE_DIVERSE_CURRENT_POLICY), {})

        h001_rows = rows_by_plan.get(policy_plan_uid(episode_id, task_context_id, H001_POLICY), [])
        task_rows = rows_by_plan.get(policy_plan_uid(episode_id, task_context_id, TASK_AGNOSTIC_POLICY), [])
        detector_rows = rows_by_plan.get(policy_plan_uid(episode_id, task_context_id, DETECTOR_POLICY), [])
        source_rows = rows_by_plan.get(policy_plan_uid(episode_id, task_context_id, SOURCE_DIVERSE_CURRENT_POLICY), [])

        h001_success = h001.get("success_proposal_uid")
        task_success = task_agnostic.get("success_proposal_uid")
        row = {
            "version": VERSION,
            "adapter_episode_id": episode_id,
            "scan_id": h001.get("scan_id") or task_agnostic.get("scan_id"),
            "scene_key": h001.get("scene_key") or task_agnostic.get("scene_key"),
            "task_context_id": task_context_id,
            "object_category": object_category,
            "diagnostic_source_gap_boundary_for_reporting": bool(reg.get("diagnostic_source_gap_boundary")),
            "m47_suspected_cause": reg.get("suspected_cause"),
            "h001_policy_id": H001_POLICY,
            "task_agnostic_policy_id": TASK_AGNOSTIC_POLICY,
            "h001_SR": h001.get("SR"),
            "task_agnostic_SR": task_agnostic.get("SR"),
            "delta_SR": delta(h001.get("SR"), task_agnostic.get("SR")),
            "h001_SPL": h001.get("SPL"),
            "task_agnostic_SPL": task_agnostic.get("SPL"),
            "delta_SPL": delta(h001.get("SPL"), task_agnostic.get("SPL")),
            "h001_CandidateVisits": h001.get("CandidateVisits"),
            "task_agnostic_CandidateVisits": task_agnostic.get("CandidateVisits"),
            "detector_SR": detector.get("SR"),
            "source_diverse_current_SR": source_diverse.get("SR"),
            "h001_success_proposal_uid": h001_success,
            "task_agnostic_success_proposal_uid": task_success,
            "h001_success_rank_in_h001": success_rank(h001_rows, h001_success),
            "task_agnostic_success_rank_in_task_agnostic": success_rank(task_rows, task_success),
            "task_agnostic_success_rank_in_h001": proposal_rank(h001_rows, task_success),
            "task_agnostic_success_rank_in_detector": proposal_rank(detector_rows, task_success),
            "task_agnostic_success_rank_in_source_diverse_current": proposal_rank(source_rows, task_success),
            "h001_top5_visit_order": visit_summary(h001_rows, h001_success or task_success),
            "task_agnostic_top5_visit_order": visit_summary(task_rows, task_success),
            "detector_top5_visit_order": visit_summary(detector_rows, detector.get("success_proposal_uid")),
            "source_diverse_current_top5_visit_order": visit_summary(
                source_rows, source_diverse.get("success_proposal_uid")
            ),
            "diagnostic_uses_execution_outcome": True,
            "allowed_for_policy_input": False,
            "repair_need": classify_repair_need(reg, h001, task_agnostic, h001_rows, task_rows),
        }
        out.append(row)
    return out


def classify_repair_need(
    regression: dict[str, Any],
    h001: dict[str, Any],
    task_agnostic: dict[str, Any],
    h001_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
) -> str:
    source_gap = bool(regression.get("diagnostic_source_gap_boundary"))
    h001_sr = finite_float(h001.get("SR"))
    task_sr = finite_float(task_agnostic.get("SR"))
    if source_gap and h001_sr == 0.0 and task_sr == 1.0:
        h001_first = h001_rows[0].get("candidate_source_role") if h001_rows else None
        task_success_rank = success_rank(task_rows, task_agnostic.get("success_proposal_uid"))
        return (
            "source_gap_repair_required_delay_stale_old_memory_and_preserve_task_agnostic_current_candidate"
            if h001_first == "stale_old_memory" and task_success_rank is not None
            else "source_gap_repair_required"
        )
    if h001_sr == 1.0 and task_sr == 1.0:
        h001_rank = success_rank(h001_rows, h001.get("success_proposal_uid"))
        task_rank = success_rank(task_rows, task_agnostic.get("success_proposal_uid"))
        if h001_rank is not None and task_rank is not None and h001_rank > task_rank:
            return "source_ready_efficiency_repair_required_do_not_push_current_success_candidates_late"
        return "source_ready_efficiency_repair_required"
    return "manual_review_required"


def build_repair_principle_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "principle_id": "routine_fetch_source_ready_efficiency_guard",
            "applies_to": "routine_fetch rows where current-observation candidates are already source-ready.",
            "failure_diagnosis": "Task conditioning can preserve success but push the reachable current candidate later than task-agnostic source-diverse ordering, increasing path length and visits.",
            "method_form": "For routine_fetch, task conditioning must not demote deterministic source-diverse current candidates behind a stale/contextual preference unless proposal reliability or path cost justifies it.",
            "allowed_inputs": ["task_context_id", "candidate_source_role", "source_diversity_key", "confidence", "ranking_score", "source_to_candidate_path_cost_m"],
            "blocked_inputs": ["trajectory_success", "success_proposal_uid", "candidate_to_eval_goal_xz_m"],
        },
        {
            "version": VERSION,
            "principle_id": "routine_fetch_source_gap_stale_suppression",
            "applies_to": "routine_fetch rows where stale old memory appears before current candidates and source-gap failure is observed after execution.",
            "failure_diagnosis": "A stale-old-memory first stop can spend the budget before a source-diverse current candidate is visited.",
            "method_form": "Delay stale_old_memory for routine_fetch unless stale path cost is very low and the current pool is too weak; fill remaining slots from source-diverse current ordering before stale fallback.",
            "allowed_inputs": ["task_context_id", "candidate_source_role", "source_to_candidate_path_cost_m", "path_ready", "candidate_usable_for_path_smoke"],
            "blocked_inputs": ["diagnostic_source_gap_boundary", "SR", "SPL", "FailureType"],
        },
        {
            "version": VERSION,
            "principle_id": "source_gap_candidate_pool_preservation",
            "applies_to": "M49 materialization of the repaired H001 policy.",
            "failure_diagnosis": "H001 v1 can miss a current source-diverse candidate that the task-agnostic ablation reaches under the same budget.",
            "method_form": "The repaired policy must preserve the deterministic source-diverse current candidate pool and use task context only as a trust/cost tie-breaker, not as a hard removal rule.",
            "allowed_inputs": ["source_diversity_key", "frame_id", "proposal_uid", "confidence", "ranking_score", "path_ready"],
            "blocked_inputs": ["eval_goal_position", "primary_eval_hit", "task_agnostic_success_proposal_uid"],
        },
    ]


def build_repair_policy_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": REPAIR_POLICY,
            "policy_role": "test_method_task_conditioned_safe_source_diverse_memory_trust",
            "primary_budget_cap": PRIMARY_BUDGET,
            "candidate_visit_order_contract": "routine_fetch_safe_source_diverse_v2",
            "targeted_failure_modes": [
                "routine_fetch_source_ready_efficiency_loss",
                "routine_fetch_source_gap_stale_first_budget_waste",
            ],
            "rule_summary": [
                "Keep source-diverse current ordering as the base candidate pool.",
                "Use task_context_id only to adjust memory trust and stale fallback timing.",
                "For routine_fetch, current/source-diverse candidates should be visited before stale_old_memory unless stale path cost is low and current pool is unavailable.",
                "Keep top-k budget matched at 5 stops.",
            ],
            "allowed_input_family": "candidate metadata, current/stale source role, proposal confidence, path readiness, source-diversity and path-cost proxies.",
            "blocked_input_family": "ObjectNav eval goal/viewpoint, execution success, SR/SPL, success proposal uid, and diagnostic source-gap boundary.",
            "requires_m49_materialization": True,
            "requires_m50_trajectory_execution": True,
            "supports_performance_claim_now": False,
        }
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "version": VERSION,
            "field": field,
            "allowed_for_policy": True,
            "policy_use": "Allowed for M49 repaired policy materialization and baseline reproduction.",
        }
        for field in ALLOWED_POLICY_FIELDS
    ]
    rows.extend(
        {
            "version": VERSION,
            "field": field,
            "allowed_for_policy": False,
            "policy_use": "Diagnostic or eval-only after execution; never used for repaired policy ordering.",
        }
        for field in BLOCKED_POLICY_FIELDS
    )
    return rows


def build_m49_materialization_plan_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy_id in M49_POLICIES:
        rows.append(
            {
                "version": VERSION,
                "m49_policy_id": policy_id,
                "include_in_m49": True,
                "primary_budget_cap": 1 if policy_id == STATIC_POLICY else PRIMARY_BUDGET,
                "expected_scan_task_plan_rows": EXPECTED_SCAN_TASK_ROWS,
                "expected_candidate_rows": EXPECTED_SCAN_TASK_ROWS if policy_id == STATIC_POLICY else EXPECTED_SCAN_TASK_ROWS * PRIMARY_BUDGET,
                "source_for_materialization": "reuse_m44_baseline_rows"
                if policy_id in BASELINE_POLICIES
                else "re_materialize_from_m44_source_diverse_candidate_pool_with_m48_contract",
                "policy_role": policy_role(policy_id),
                "must_remain_unchanged_from_m44": policy_id in BASELINE_POLICIES,
                "claim_boundary": "M49 is materialization only; trajectory performance requires a later Docker Habitat execution.",
            }
        )
    return rows


def policy_role(policy_id: str) -> str:
    if policy_id == STATIC_POLICY:
        return "naive_lower_bound"
    if policy_id == DETECTOR_POLICY:
        return "budget_matched_detector_baseline"
    if policy_id == FIXED_CURRENT_POLICY:
        return "budget_matched_fixed_current_baseline"
    if policy_id == SOURCE_DIVERSE_CURRENT_POLICY:
        return "source_diversity_current_observation_baseline"
    if policy_id == TASK_AGNOSTIC_POLICY:
        return "task_context_ablation"
    if policy_id == H001_POLICY:
        return "previous_h001_task_conditioned_source_diverse"
    if policy_id == REPAIR_POLICY:
        return "repaired_h001_task_conditioned_safe_source_diverse"
    return "unknown"


def build_regression_repair_target_rows(diagnosis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in diagnosis_rows:
        source_gap = bool(row.get("diagnostic_source_gap_boundary_for_reporting"))
        task_success = row.get("task_agnostic_success_proposal_uid")
        h001_success = row.get("h001_success_proposal_uid")
        if source_gap:
            target = {
                "diagnostic_target": "task_agnostic_success_candidate_retained_for_post_materialization_audit",
                "target_proposal_uid_for_audit_only": task_success,
                "expected_m49_materialization_property": "candidate retained in repaired H001 top5 and stale_old_memory not first when current candidates are path-ready.",
            }
        else:
            target = {
                "diagnostic_target": "h001_success_candidate_not_demoted_by_routine_fetch_task_context",
                "target_proposal_uid_for_audit_only": h001_success or task_success,
                "expected_m49_materialization_property": "candidate rank should not be worse than the task-agnostic/source-diverse-current rank when policy-visible current evidence is available.",
            }
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": row["adapter_episode_id"],
                "task_context_id": row["task_context_id"],
                "object_category": row["object_category"],
                "diagnostic_source_gap_boundary_for_reporting": source_gap,
                **target,
                "uses_execution_outcome_for_audit_only": True,
                "allowed_for_policy_input": False,
            }
        )
    return out


def build_gate_rows(
    m44_coverage: dict[str, Any],
    m46_coverage: dict[str, Any],
    m47_coverage: dict[str, Any],
    regression_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    m49_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked = {row["field"] for row in input_rows if row["allowed_for_policy"] is False}
    expected_m49_plan_rows = EXPECTED_SCAN_TASK_ROWS * len(M49_POLICIES)
    expected_m49_candidate_rows = EXPECTED_SCAN_TASK_ROWS + (len(M49_POLICIES) - 1) * EXPECTED_SCAN_TASK_ROWS * PRIMARY_BUDGET
    return [
        {
            "version": VERSION,
            "gate_id": "m47_ready_and_scale_blocked",
            "passed": m47_coverage.get("status") == "e008_m47_source_diverse_result_interpretation_scale_decision_ready"
            and not bool(m47_coverage.get("scale_up_recommended_now")),
            "evidence": f"M47 status `{m47_coverage.get('status')}`, scale_up={m47_coverage.get('scale_up_recommended_now')}.",
        },
        {
            "version": VERSION,
            "gate_id": "regression_cases_available",
            "passed": len(regression_rows) == 2,
            "evidence": f"regression rows={len(regression_rows)}; expected=2 routine_fetch rows.",
        },
        {
            "version": VERSION,
            "gate_id": "m44_materialization_available",
            "passed": m44_coverage.get("status") == "e008_m44_source_diverse_redesign_row_materialization_smoke_ready"
            and len(plan_rows) == EXPECTED_SCAN_TASK_ROWS * len(BASELINE_POLICIES),
            "evidence": f"M44 status `{m44_coverage.get('status')}`, plan rows={len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m46_execution_available_for_diagnosis",
            "passed": m46_coverage.get("status") == "e008_m46_source_diverse_redesign_trajectory_execution_smoke_ready",
            "evidence": f"M46 status `{m46_coverage.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "repair_policy_defined",
            "passed": any(row["m49_policy_id"] == REPAIR_POLICY for row in m49_rows),
            "evidence": f"M49 policy rows={len(m49_rows)}, repair policy=`{REPAIR_POLICY}`.",
        },
        {
            "version": VERSION,
            "gate_id": "eval_fields_blocked",
            "passed": {"SR", "SPL", "trajectory_success", "success_proposal_uid", "diagnostic_source_gap_boundary"}.issubset(blocked),
            "evidence": "M48 input contract blocks execution outcomes and diagnostic source-gap boundary for policy ordering.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_denominator_contract_ready",
            "passed": expected_m49_plan_rows == 126 and expected_m49_candidate_rows == 558,
            "evidence": f"M49 expected plan rows={expected_m49_plan_rows}, expected candidate rows={expected_m49_candidate_rows}.",
        },
        {
            "version": VERSION,
            "gate_id": "claim_boundary_preserved",
            "passed": True,
            "evidence": "M48 is a contract unit only; final navigation, final robustness, and human-intent main claims remain false.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "routine_fetch_failure_diagnosis",
            "supported": True,
            "claim_boundary": "M48 diagnoses the two M47 routine_fetch regressions using already executed M46 rows.",
        },
        {
            "version": VERSION,
            "claim_id": "repair_policy_contract",
            "supported": True,
            "claim_boundary": "M48 defines a leakage-safe repair contract for M49 materialization; it does not show performance improvement.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_repaired_navigation_improvement",
            "supported": False,
            "claim_boundary": "The repaired policy must be materialized and executed before any navigation improvement claim.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context remains a condition on memory trust/re-observation, not a main human-intent claim.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M48 does not execute Docker Habitat trajectories and cannot support final real navigation SR/SPL.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_navigation_benchmark_now",
            "selected": False,
            "reason": "M47 scale-up is blocked by routine_fetch regression and source-gap under-recovery.",
        },
        {
            "version": VERSION,
            "route_id": "materialize_repaired_routine_fetch_policy",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else "repair M48 contract inputs",
            "reason": "M49 should add the repaired H001 v2 policy while preserving all M44 baselines unchanged.",
            "launch_long_job_now": False,
            "requires_docker": False,
        },
    ]


def write_report(
    coverage: dict[str, Any],
    diagnosis_rows: list[dict[str, Any]],
    principle_rows: list[dict[str, Any]],
    m49_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M48 Routine-Fetch Regression Repair Contract",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- M47 status: `{coverage['m47_status']}`",
        f"- Regression diagnosis rows: `{coverage['regression_case_diagnosis_rows']}`",
        f"- Repair policy: `{REPAIR_POLICY}`",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Final real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        "",
        "## Regression Diagnosis",
        "",
        "| Episode | Object | Source Gap | H001 SR/SPL | Task-Agnostic SR/SPL | H001 Visits | Task-Agnostic Visits | Repair Need |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in diagnosis_rows:
        lines.append(
            "| "
            f"`{row['adapter_episode_id']}` | `{row['object_category']}` | "
            f"`{str(row['diagnostic_source_gap_boundary_for_reporting']).lower()}` | "
            f"{fmt(row.get('h001_SR'))}/{fmt(row.get('h001_SPL'))} | "
            f"{fmt(row.get('task_agnostic_SR'))}/{fmt(row.get('task_agnostic_SPL'))} | "
            f"{fmt(row.get('h001_CandidateVisits'))} | {fmt(row.get('task_agnostic_CandidateVisits'))} | "
            f"{row['repair_need']} |"
        )

    lines.extend(
        [
            "",
            "## Repair Principles",
            "",
            "| Principle | Failure Diagnosis | Method Form |",
            "|---|---|---|",
        ]
    )
    for row in principle_rows:
        lines.append(f"| `{row['principle_id']}` | {row['failure_diagnosis']} | {row['method_form']} |")

    lines.extend(
        [
            "",
            "## M49 Materialization Contract",
            "",
            "| Policy | Expected Plan Rows | Expected Candidate Rows | Source |",
            "|---|---:|---:|---|",
        ]
    )
    for row in m49_rows:
        lines.append(
            "| "
            f"`{row['m49_policy_id']}` | {row['expected_scan_task_plan_rows']} | "
            f"{row['expected_candidate_rows']} | {row['source_for_materialization']} |"
        )

    lines.extend(
        [
            "",
            "## Readiness Gates",
            "",
            "| Gate | Passed | Evidence |",
            "|---|---|---|",
        ]
    )
    for row in gate_rows:
        lines.append(f"| `{row['gate_id']}` | `{str(row['passed']).lower()}` | {row['evidence']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not scale the navigation benchmark yet.",
            "- Add `h001_task_conditioned_safe_source_diverse_budget5_v2` as a repaired policy in M49.",
            "- Preserve all M44 baselines unchanged so the next comparison is attributable to the repair only.",
            "- Treat the known success proposal ids as audit-only diagnostics, not policy inputs.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m44_coverage = read_json(M44_DIR / "coverage.json")
    m46_coverage = read_json(M46_DIR / "coverage.json")
    m47_coverage = read_json(M47_DIR / "coverage.json")
    m44_plan_rows = read_jsonl(M44_DIR / "trajectory_execution_plan_rows.jsonl")
    m44_candidate_rows = read_jsonl(M44_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    m46_metric_rows = scan_metric_rows(read_jsonl(M46_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl"))
    m47_regression_rows = read_jsonl(M47_DIR / "regression_case_rows.jsonl")

    if not m44_coverage or not m46_coverage or not m47_coverage:
        raise SystemExit("missing M44/M46/M47 coverage")
    if not m44_plan_rows or not m44_candidate_rows or not m46_metric_rows or not m47_regression_rows:
        raise SystemExit("missing M44/M46/M47 row inputs")

    rows_by_plan = index_by_plan(m44_candidate_rows)
    metric_by_key = index_metric_rows(m46_metric_rows)

    diagnosis_rows = build_regression_diagnosis_rows(m47_regression_rows, metric_by_key, rows_by_plan)
    principle_rows = build_repair_principle_rows()
    repair_policy_rows = build_repair_policy_contract_rows()
    input_rows = build_input_contract_rows()
    m49_rows = build_m49_materialization_plan_rows()
    target_rows = build_regression_repair_target_rows(diagnosis_rows)
    gate_rows = build_gate_rows(
        m44_coverage,
        m46_coverage,
        m47_coverage,
        m47_regression_rows,
        m44_plan_rows,
        m49_rows,
        input_rows,
    )
    ready = all(row["passed"] for row in gate_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m44_status": m44_coverage.get("status"),
        "m46_status": m46_coverage.get("status"),
        "m47_status": m47_coverage.get("status"),
        "m44_plan_rows": len(m44_plan_rows),
        "m44_candidate_rows": len(m44_candidate_rows),
        "m46_scan_task_metric_rows": len(m46_metric_rows),
        "m47_regression_case_rows": len(m47_regression_rows),
        "regression_case_diagnosis_rows": len(diagnosis_rows),
        "repair_principle_rows": len(principle_rows),
        "repair_policy_contract_rows": len(repair_policy_rows),
        "input_contract_rows": len(input_rows),
        "m49_materialization_plan_rows": len(m49_rows),
        "m49_expected_execution_plan_rows": EXPECTED_SCAN_TASK_ROWS * len(M49_POLICIES),
        "m49_expected_candidate_rows": EXPECTED_SCAN_TASK_ROWS
        + (len(M49_POLICIES) - 1) * EXPECTED_SCAN_TASK_ROWS * PRIMARY_BUDGET,
        "readiness_gate_rows": len(gate_rows),
        "readiness_gate_pass_rows": sum(1 for row in gate_rows if row["passed"]),
        "selected_repair_policy": REPAIR_POLICY,
        "selected_next_unit": NEXT_UNIT if ready else "repair M48 contract inputs",
        "scale_up_recommended_now": False,
        "launch_long_job_now": False,
        "requires_docker_now": False,
        "m49_requires_docker": False,
        "m50_requires_docker": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "regression_case_diagnosis_rows.jsonl", diagnosis_rows)
    write_jsonl(ARTIFACT_DIR / "repair_principle_rows.jsonl", principle_rows)
    write_jsonl(ARTIFACT_DIR / "repair_policy_contract_rows.jsonl", repair_policy_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "m49_materialization_plan_rows.jsonl", m49_rows)
    write_jsonl(ARTIFACT_DIR / "regression_repair_target_rows.jsonl", target_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_report(coverage, diagnosis_rows, principle_rows, m49_rows, gate_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "repair_policy_contract_rows.jsonl", repair_policy_rows)
    write_jsonl(DATA_OUT_DIR / "m49_materialization_plan_rows.jsonl", m49_rows)
    write_jsonl(DATA_OUT_DIR / "regression_repair_target_rows.jsonl", target_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
