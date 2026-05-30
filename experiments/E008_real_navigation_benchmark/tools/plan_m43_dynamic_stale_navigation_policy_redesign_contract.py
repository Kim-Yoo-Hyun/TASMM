#!/usr/bin/env python3
"""Fix the M43 dynamic-stale navigation policy redesign contract."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0"
)

M39_DIR = EXP_ROOT / "artifacts" / "E008-M39_budget_matched_policy_repair_source_gap_contract_v0"
M40_DIR = EXP_ROOT / "artifacts" / "E008-M40_budget_matched_repair_row_materialization_smoke_v0"
M42_DIR = EXP_ROOT / "artifacts" / "E008-M42_budget_matched_repair_result_interpretation_scale_decision_v0"

VERSION = "e008_m43_dynamic_stale_navigation_policy_redesign_contract_v0"
STATUS = "e008_m43_dynamic_stale_navigation_policy_redesign_contract_ready"
NEXT_UNIT = "E008-M44 source-diverse redesign row materialization smoke"

SELECTED_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
SOURCE_DIVERSE_BASELINE = "source_diverse_current_observation_budget5_v1"
FIXED_TOPK_POLICY = "fixed_topk_current_observation_budget5_v0"
DETECTOR_BUDGET5_POLICY = "detector_confidence_budget5_v0"
STATIC_POLICY = "static_stale_memory_top1_v0"

PRIMARY_BUDGET = 5
SOURCE_EXPANSION_ROUTE = "source_diverse_current_candidate_pool_rerank_v1"

BLOCKED_POLICY_FIELDS = [
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
    "diagnostic_source_gap_boundary",
]


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
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def find_budget_row(rows: list[dict[str, Any]], policy_id: str, scope: str) -> dict[str, Any]:
    for row in rows:
        if row.get("policy_id") == policy_id and row.get("budget_scope") == scope:
            return row
    return {}


def unique_scan_task_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in plan_rows:
        key = (str(row.get("adapter_episode_id")), str(row.get("task_context_id")))
        if key not in by_key:
            by_key[key] = {
                "adapter_episode_id": row.get("adapter_episode_id"),
                "benchmark_row_uid": row.get("benchmark_row_uid"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "diagnostic_source_gap_boundary": bool(row.get("diagnostic_source_gap_boundary")),
                "source_m36_policy_plan_uid": row.get("source_m36_policy_plan_uid"),
            }
    return sorted(by_key.values(), key=lambda row: (str(row["scan_id"]), str(row["task_context_id"])))


def build_failed_gate_diagnosis_rows(scale_gate_rows: list[dict[str, Any]], budget_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detector_gap = find_budget_row(budget_rows, "detector_confidence_reachable_subset_v0", "source_gap")
    rows = []
    for gate in scale_gate_rows:
        gate_id = str(gate.get("gate_id"))
        if gate.get("passed"):
            diagnosis = "passed_lower_bound_only"
            design_change = "keep_as_lower_bound_not_main_claim"
        elif gate_id == "beats_detector_confidence_budget_matched":
            diagnosis = "h001_current_repair_collapses_to_detector_budget5"
            design_change = "add a policy-visible source-diverse reranking decision over the full current candidate pool"
        elif gate_id == "beats_fixed_current_topk_budget_matched":
            diagnosis = "h001_current_repair_collapses_to_fixed_top5"
            design_change = "show that the method selects different top-5 candidates than confidence/fixed order"
        elif gate_id == "beats_task_agnostic_memory_trust":
            diagnosis = "task_context_does_not_change_sr_spl"
            design_change = "make task value affect source diversity slots, stale suppression, or re-observation budget"
        elif gate_id == "source_gap_solved":
            diagnosis = "budgeted_source_gap_not_absent_source"
            design_change = "use detector full-candidate evidence to promote candidates beyond confidence top-5 without eval labels"
        elif gate_id == "task_context_main_effect":
            diagnosis = "structured_context_not_causal_yet"
            design_change = "keep human intent secondary until task-conditioned rows beat task-agnostic rows"
        else:
            diagnosis = "requires_manual_review"
            design_change = "record before scale"
        rows.append(
            {
                "version": VERSION,
                "gate_id": gate_id,
                "m42_passed": bool(gate.get("passed")),
                "m42_evidence": gate.get("evidence"),
                "diagnosis": diagnosis,
                "required_design_change": design_change,
                "detector_source_gap_full_SR": detector_gap.get("SR"),
                "detector_source_gap_cap5_SR": detector_gap.get("cap5_SR"),
                "detector_source_gap_stop_rank_mean": detector_gap.get("StopRank_mean_over_success"),
            }
        )
    return rows


def build_redesign_principle_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "principle_id": "separate_source_pool_from_visit_order",
            "principle": "A failed top-5 navigation row should be treated as candidate-pool/ranking evidence before calling it a navigation-policy failure.",
            "m42_motivation": "Detector full-candidate source-gap rows can succeed, but budget-5 rows fail.",
            "method_requirement": "M44 must materialize source-diverse top-5 rows from the full M36 current-candidate pool.",
        },
        {
            "version": VERSION,
            "principle_id": "task_context_must_change_action",
            "principle": "Structured task context is only useful if it changes source-diversity slots, stale suppression, or visit order.",
            "m42_motivation": "H001 and task-agnostic policies tie on SR/SPL in every M41 task context.",
            "method_requirement": "M44 must include task-agnostic and fixed source-diverse ablations.",
        },
        {
            "version": VERSION,
            "principle_id": "keep_budget_matched_protocol",
            "principle": "The redesigned method must keep the same candidate-visit budget as the current-observation baselines.",
            "m42_motivation": "Detector all-candidate success is not a fair budget-matched main baseline.",
            "method_requirement": "Primary rows keep a 5-stop budget; over-budget detector remains diagnostic upper bound.",
        },
        {
            "version": VERSION,
            "principle_id": "no_eval_leakage",
            "principle": "Source-gap labels, eval goals, trajectory success, and ObjectNav viewpoints cannot be policy inputs.",
            "m42_motivation": "M42 source-gap boundary is diagnostic-only.",
            "method_requirement": "M44 materialization must use policy-visible candidate fields only.",
        },
    ]


def build_policy_redesign_contract_rows() -> list[dict[str, Any]]:
    common_inputs = [
        "candidate confidence",
        "candidate path/reachability fields",
        "candidate source/frame diversity",
        "stale old-memory candidate",
        "old-location dead-end cost proxy",
        "structured task context",
    ]
    return [
        {
            "version": VERSION,
            "policy_id": STATIC_POLICY,
            "policy_role": "naive_lower_bound",
            "materialize_in_m44": True,
            "primary_budget_cap": 1,
            "uses_source_diverse_pool": False,
            "uses_task_context_for_decision": False,
            "allowed_inputs": ["stale old-memory candidate", "episode start", "category"],
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "lower-bound stale-memory failure diagnosis",
        },
        {
            "version": VERSION,
            "policy_id": DETECTOR_BUDGET5_POLICY,
            "policy_role": "budget_matched_detector_baseline",
            "materialize_in_m44": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "uses_source_diverse_pool": False,
            "uses_task_context_for_decision": False,
            "allowed_inputs": ["candidate confidence", "candidate path/reachability fields"],
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "required current-observation confidence baseline",
        },
        {
            "version": VERSION,
            "policy_id": FIXED_TOPK_POLICY,
            "policy_role": "budget_matched_fixed_current_baseline",
            "materialize_in_m44": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "uses_source_diverse_pool": False,
            "uses_task_context_for_decision": False,
            "allowed_inputs": ["current candidates", "original confidence order", "fixed top-5 budget"],
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "why not fixed top-k",
        },
        {
            "version": VERSION,
            "policy_id": SOURCE_DIVERSE_BASELINE,
            "policy_role": "source_diversity_baseline",
            "materialize_in_m44": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "uses_source_diverse_pool": True,
            "uses_task_context_for_decision": False,
            "allowed_inputs": ["full current candidate pool", "source/frame diversity", "path/reachability fields", "confidence"],
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "why not source-diverse current observation without memory/task conditioning",
        },
        {
            "version": VERSION,
            "policy_id": TASK_AGNOSTIC_POLICY,
            "policy_role": "task_context_ablation",
            "materialize_in_m44": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "uses_source_diverse_pool": True,
            "uses_task_context_for_decision": False,
            "allowed_inputs": [item for item in common_inputs if item != "structured task context"],
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "required ablation for task context",
        },
        {
            "version": VERSION,
            "policy_id": SELECTED_POLICY,
            "policy_role": "test_method",
            "materialize_in_m44": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "uses_source_diverse_pool": True,
            "uses_task_context_for_decision": True,
            "allowed_inputs": common_inputs,
            "blocked_inputs": BLOCKED_POLICY_FIELDS,
            "expected_role": "test whether task-conditioned source diversity can beat current and task-agnostic baselines",
        },
    ]


def build_source_expansion_contract_rows(budget_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detector_gap = find_budget_row(budget_rows, "detector_confidence_reachable_subset_v0", "source_gap")
    return [
        {
            "version": VERSION,
            "route_id": "threshold_tuning_only_v1",
            "selected": False,
            "reason": "M42 failure is not just a scalar threshold problem; H001 already ties current baselines under budget-5.",
            "next_unit": None,
        },
        {
            "version": VERSION,
            "route_id": SOURCE_EXPANSION_ROUTE,
            "selected": True,
            "source_pool": "M36 full current-observation candidate pool plus stale old-memory candidate",
            "candidate_visit_budget": PRIMARY_BUDGET,
            "detector_source_gap_full_SR": detector_gap.get("SR"),
            "detector_source_gap_cap5_SR": detector_gap.get("cap5_SR"),
            "detector_source_gap_stop_rank_mean": detector_gap.get("StopRank_mean_over_success"),
            "reason": "Source-gap rows are reachable by detector full-candidate ordering but not by budget-5 confidence order; M44 should test source-diverse top-5 selection.",
            "next_unit": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "route_id": "new_rendered_observation_expansion_v1",
            "selected": False,
            "reason": "Do not launch new rendering before testing whether the existing full candidate pool can be re-ranked under the same budget.",
            "next_unit": None,
        },
        {
            "version": VERSION,
            "route_id": "human_intent_main_claim_upgrade_v1",
            "selected": False,
            "reason": "Task context is not yet causal on SR/SPL; keep it as a conditioning variable until M44/M45 beats task-agnostic rows.",
            "next_unit": None,
        },
    ]


def task_slot_plan(context_id: str) -> dict[str, Any]:
    if context_id == "routine_fetch":
        return {
            "task_utility": "low",
            "source_diversity_slots": 3,
            "confidence_slots": 1,
            "stale_memory_slots_if_low_dead_end": 1,
            "stale_suppression_strength": "medium",
        }
    if context_id == "noisy_high_value_fetch":
        return {
            "task_utility": "high_noisy",
            "source_diversity_slots": 4,
            "confidence_slots": 1,
            "stale_memory_slots_if_low_dead_end": 0,
            "stale_suppression_strength": "high",
        }
    return {
        "task_utility": "high",
        "source_diversity_slots": 4,
        "confidence_slots": 1,
        "stale_memory_slots_if_low_dead_end": 0,
        "stale_suppression_strength": "high",
    }


def build_task_context_contract_rows(scan_task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts = sorted({str(row.get("task_context_id")) for row in scan_task_rows})
    return [
        {
            "version": VERSION,
            "task_context_id": context_id,
            **task_slot_plan(context_id),
            "claim_boundary": "This is a structured task-context control variable, not natural-language intent understanding.",
            "m44_required_ablation": TASK_AGNOSTIC_POLICY,
        }
        for context_id in contexts
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    allowed = [
        "adapter_episode_id",
        "scan_id",
        "scene_key",
        "object_category",
        "task_context_id",
        "candidate confidence",
        "candidate source_role",
        "candidate source/frame id",
        "candidate snapped/execution_stop_position_m",
        "path/reachability fields computed before evaluation",
        "stale old-memory candidate position",
        "old-location dead-end cost proxy",
    ]
    return [
        {
            "version": VERSION,
            "field_group": "allowed_policy_inputs",
            "fields": allowed,
            "policy_use": "M44 row materialization and M45 trajectory execution policy ordering.",
        },
        {
            "version": VERSION,
            "field_group": "blocked_policy_inputs",
            "fields": BLOCKED_POLICY_FIELDS,
            "policy_use": "Diagnostic or metric only after execution; never for M44 materialization.",
        },
    ]


def build_m44_materialization_plan_rows(scan_task_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for scan_task in scan_task_rows:
        slot_plan = task_slot_plan(str(scan_task.get("task_context_id")))
        for policy in policy_rows:
            if not policy.get("materialize_in_m44"):
                continue
            rows.append(
                {
                    "version": VERSION,
                    "m44_plan_uid": (
                        f"m44::{scan_task.get('adapter_episode_id')}::"
                        f"{scan_task.get('task_context_id')}::{policy['policy_id']}"
                    ),
                    "adapter_episode_id": scan_task.get("adapter_episode_id"),
                    "benchmark_row_uid": scan_task.get("benchmark_row_uid"),
                    "scan_id": scan_task.get("scan_id"),
                    "scene_key": scan_task.get("scene_key"),
                    "object_category": scan_task.get("object_category"),
                    "task_context_id": scan_task.get("task_context_id"),
                    "policy_id": policy["policy_id"],
                    "policy_role": policy["policy_role"],
                    "primary_budget_cap": policy["primary_budget_cap"],
                    "candidate_source_pool": (
                        "m36_full_current_candidate_pool_plus_stale"
                        if policy["uses_source_diverse_pool"]
                        else "m40_budget_matched_existing_pool"
                    ),
                    "source_expansion_route": SOURCE_EXPANSION_ROUTE if policy["uses_source_diverse_pool"] else "none",
                    "use_diagnostic_source_gap_boundary_for_policy": False,
                    "diagnostic_source_gap_boundary_for_reporting": bool(scan_task.get("diagnostic_source_gap_boundary")),
                    "uses_task_context_for_decision": policy["uses_task_context_for_decision"],
                    "task_source_diversity_slots": slot_plan["source_diversity_slots"]
                    if policy["uses_task_context_for_decision"]
                    else None,
                    "task_stale_memory_slots_if_low_dead_end": slot_plan["stale_memory_slots_if_low_dead_end"]
                    if policy["uses_task_context_for_decision"]
                    else None,
                    "materialization_goal": "produce leakage-safe top-5 candidate visit-order rows for M45 execution",
                    "requires_docker_for_m44_materialization": False,
                    "requires_docker_for_m45_execution": True,
                }
            )
    return rows


def build_evaluation_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m44_materialization_ready",
            "required_for": "M45 trajectory execution",
            "pass_condition": "all planned M44 rows have <=5 policy-visible candidates, no blocked fields, and candidate source counts are reported",
        },
        {
            "version": VERSION,
            "gate_id": "beats_current_observation_budget5",
            "required_for": "navigation improvement claim",
            "pass_condition": f"{SELECTED_POLICY} improves SR or SPL over detector/fixed current top-5 without using more stop budget",
        },
        {
            "version": VERSION,
            "gate_id": "beats_task_agnostic_source_diverse",
            "required_for": "task-context claim",
            "pass_condition": f"{SELECTED_POLICY} improves over {TASK_AGNOSTIC_POLICY} on at least one primary task group without loss on others",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_recovery",
            "required_for": "source-gap recovery claim",
            "pass_condition": "source-gap diagnostic rows show nonzero SR under the redesigned budget-5 policy",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "policy_redesign_contract_ready",
            "supported": True,
            "claim_boundary": "M43 fixes a redesign contract and M44 materialization plan; it is not a trajectory result.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M43 has no new trajectory execution and does not support final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Task context remains structured conditioning until it beats task-agnostic source-diverse rows.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_recovery",
            "supported": False,
            "claim_boundary": "M43 only plans source-diverse materialization; recovery must be measured in M45.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_m41_m42_now",
            "selected": False,
            "reason": "M42 failed detector/fixed/task-agnostic and source-gap gates.",
        },
        {
            "version": VERSION,
            "route_id": "source_diverse_policy_redesign",
            "selected": True,
            "reason": "Detector full-candidate source-gap rows show target can exist beyond budget-5 confidence order; redesign must test source-diverse top-5 selection.",
            "selected_next_unit": NEXT_UNIT,
        },
    ]


def write_report(
    coverage: dict[str, Any],
    failed_gate_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    evaluation_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M43 Dynamic-Stale Navigation Policy Redesign Contract",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- Selected policy: `{coverage['selected_policy_id']}`",
        f"- Selected source route: `{coverage['selected_source_expansion_route']}`",
        f"- M44 planned rows: {coverage['m44_materialization_plan_rows']}",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Final real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        "",
        "## Failure Diagnosis",
        "",
        "| Failed Gate | M42 Passed | Diagnosis | Required Change |",
        "|---|---|---|---|",
    ]
    for row in failed_gate_rows:
        lines.append(
            f"| `{row['gate_id']}` | `{str(row['m42_passed']).lower()}` | "
            f"{row['diagnosis']} | {row['required_design_change']} |"
        )
    lines.extend(
        [
            "",
            "## Policy Contract",
            "",
            "| Policy | Role | Budget | Source-Diverse | Task-Context Decision |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in policy_rows:
        lines.append(
            f"| `{row['policy_id']}` | {row['policy_role']} | {row['primary_budget_cap']} | "
            f"`{str(row['uses_source_diverse_pool']).lower()}` | `{str(row['uses_task_context_for_decision']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Source Route",
            "",
            "| Route | Selected | Reason |",
            "|---|---|---|",
        ]
    )
    for row in source_rows:
        lines.append(f"| `{row['route_id']}` | `{str(row['selected']).lower()}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Task Context Contract",
            "",
            "| Task Context | Utility | Source Diversity Slots | Stale Slots | Suppression |",
            "|---|---|---:|---:|---|",
        ]
    )
    for row in task_rows:
        lines.append(
            f"| `{row['task_context_id']}` | {row['task_utility']} | {row['source_diversity_slots']} | "
            f"{row['stale_memory_slots_if_low_dead_end']} | {row['stale_suppression_strength']} |"
        )
    lines.extend(
        [
            "",
            "## Evaluation Gates",
            "",
            "| Gate | Required For | Pass Condition |",
            "|---|---|---|",
        ]
    )
    for row in evaluation_rows:
        lines.append(f"| `{row['gate_id']}` | {row['required_for']} | {row['pass_condition']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not scale M41/M42 as final navigation evidence.",
            "- M44 should materialize source-diverse budget-5 rows from the full M36 current candidate pool.",
            "- M45 should execute those rows in Docker `Habitat` before any positive navigation claim.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m39_coverage = read_json(M39_DIR / "coverage.json")
    m40_coverage = read_json(M40_DIR / "coverage.json")
    m42_coverage = read_json(M42_DIR / "coverage.json")
    budget_rows = read_jsonl(M39_DIR / "budget_alignment_rows.jsonl")
    scale_gate_rows = read_jsonl(M42_DIR / "scale_gate_rows.jsonl")
    m40_plan_rows = read_jsonl(M40_DIR / "trajectory_execution_plan_rows.jsonl")

    scan_task_rows = unique_scan_task_rows(m40_plan_rows)
    failed_gate_rows = build_failed_gate_diagnosis_rows(scale_gate_rows, budget_rows)
    principle_rows = build_redesign_principle_rows()
    policy_rows = build_policy_redesign_contract_rows()
    source_rows = build_source_expansion_contract_rows(budget_rows)
    task_rows = build_task_context_contract_rows(scan_task_rows)
    input_guard_rows = build_input_guard_rows()
    m44_plan_rows = build_m44_materialization_plan_rows(scan_task_rows, policy_rows)
    evaluation_rows = build_evaluation_gate_rows()
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    detector_gap = find_budget_row(budget_rows, "detector_confidence_reachable_subset_v0", "source_gap")
    source_gap_scan_task_rows = [row for row in scan_task_rows if row.get("diagnostic_source_gap_boundary")]
    policy_counts = Counter(row["policy_id"] for row in m44_plan_rows)

    coverage = {
        "version": VERSION,
        "status": STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m39_status": m39_coverage.get("status"),
        "m40_status": m40_coverage.get("status"),
        "m42_status": m42_coverage.get("status"),
        "failed_gate_diagnosis_rows": len(failed_gate_rows),
        "redesign_principle_rows": len(principle_rows),
        "policy_redesign_contract_rows": len(policy_rows),
        "source_expansion_contract_rows": len(source_rows),
        "task_context_contract_rows": len(task_rows),
        "input_guard_rows": len(input_guard_rows),
        "m44_materialization_plan_rows": len(m44_plan_rows),
        "m44_policy_counts": dict(sorted(policy_counts.items())),
        "unique_scan_task_rows": len(scan_task_rows),
        "source_ready_scan_task_rows": len(scan_task_rows) - len(source_gap_scan_task_rows),
        "source_gap_scan_task_rows": len(source_gap_scan_task_rows),
        "detector_source_gap_full_SR": detector_gap.get("SR"),
        "detector_source_gap_cap5_SR": detector_gap.get("cap5_SR"),
        "detector_source_gap_stop_rank_mean": detector_gap.get("StopRank_mean_over_success"),
        "selected_policy_id": SELECTED_POLICY,
        "selected_source_expansion_route": SOURCE_EXPANSION_ROUTE,
        "scale_up_recommended_now": False,
        "m44_materialization_ready": True,
        "m45_trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "failed_gate_diagnosis_rows.jsonl", failed_gate_rows)
    write_jsonl(ARTIFACT_DIR / "redesign_principle_rows.jsonl", principle_rows)
    write_jsonl(ARTIFACT_DIR / "policy_redesign_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "source_expansion_contract_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "task_context_contract_rows.jsonl", task_rows)
    write_jsonl(ARTIFACT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(ARTIFACT_DIR / "m44_materialization_plan_rows.jsonl", m44_plan_rows)
    write_jsonl(ARTIFACT_DIR / "evaluation_gate_rows.jsonl", evaluation_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "m44_materialization_plan_rows.jsonl", m44_plan_rows)
    write_report(coverage, failed_gate_rows, policy_rows, source_rows, task_rows, evaluation_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
