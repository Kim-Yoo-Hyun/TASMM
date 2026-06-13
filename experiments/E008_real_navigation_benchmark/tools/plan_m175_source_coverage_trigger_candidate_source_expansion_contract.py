#!/usr/bin/env python3
"""Freeze E008-M175 source-coverage trigger/candidate-source expansion contract."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M120_DIR = EXP_ROOT / "artifacts" / "E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0"
M121_DIR = EXP_ROOT / "artifacts" / "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0"
M124_DIR = EXP_ROOT / "artifacts" / "E008-M124_target_free_source_coverage_detector_candidate_source_v0"
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
M174_DIR = EXP_ROOT / "artifacts" / "E008-M174_source_coverage_utility_pareto_materialization_smoke_v0"
M174B_DIR = EXP_ROOT / "artifacts" / "E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0"
)

VERSION = "e008_m175_source_coverage_trigger_candidate_source_expansion_contract_v0"
READY_STATUS = "e008_m175_source_coverage_trigger_candidate_source_expansion_contract_ready"
BLOCKED_STATUS = "e008_m175_source_coverage_trigger_candidate_source_expansion_contract_blocked"
NEXT_UNIT = "E008-M176 source-coverage trigger row materialization smoke"

SELECTED_METHOD = "source_coverage_triggered_candidate_source_expansion_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_RERANK_NEGATIVE = "source_coverage_budgeted_utility_policy_v1"


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


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    try:
        value_f = float(value)
    except (TypeError, ValueError):
        return "null" if value is None else str(value)
    if not math.isfinite(value_f):
        return "null"
    return f"{value_f:.6f}"


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        out.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(out)


def build_method_contract_rows(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = seed_rows[0] if seed_rows else {}
    return [
        {
            "version": VERSION,
            "row_type": "method_contract",
            "method_id": SELECTED_METHOD,
            "method_role": "selected_next_method_contract",
            "principle": seed.get(
                "principle",
                "Source coverage should trigger candidate-source expansion before detector-confidence ranking.",
            ),
            "method_form": (
                "First compute source-coverage and current-evidence triggers from allowed pre-execution fields. "
                "If a trigger fires, request or include target-free candidate-source rows, then rank the expanded "
                "candidate pool with the protected detector-confidence order. If no trigger fires, preserve the "
                "detector-confidence reachable order exactly."
            ),
            "failure_diagnosis_used": "M174b shows within-pool source-coverage reranking has zero selected-policy activity.",
            "why_this_form_is_forced": (
                "M174/M174b rule out posthoc utility tuning under the fixed candidate pool; the missing factor must "
                "therefore be exposed at the map/source-acquisition interface before ranking."
            ),
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "closed_negative_policy_id": SOURCE_COVERAGE_RERANK_NEGATIVE,
            "benchmark_denominator_change_allowed": False,
            "candidate_source_pool_expansion_allowed": True,
            "posthoc_threshold_change_allowed": False,
            "posthoc_weight_tuning_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "materialize_before_execution": True,
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "method_id": PROTECTED_BASELINE,
            "method_role": "protected_naive_baseline",
            "principle": "Current detector confidence remains the default reliability order.",
            "method_form": "Rank reachable current candidates by detector confidence without source expansion.",
            "failure_diagnosis_used": "This is the simplest baseline M175 must preserve before claiming a method change.",
            "why_this_form_is_forced": "M171-M174b show that source-coverage features cannot replace confidence without guards.",
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "closed_negative_policy_id": None,
            "benchmark_denominator_change_allowed": False,
            "candidate_source_pool_expansion_allowed": False,
            "posthoc_threshold_change_allowed": False,
            "posthoc_weight_tuning_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "materialize_before_execution": True,
        },
    ]


def build_trigger_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "current_source_coverage_sparse_v1",
            "selected_for_m176": True,
            "trigger_family": "source_coverage",
            "allowed_signal": "unique source-pose/source-coverage keys available before evaluation",
            "trigger_rule": "fire when the current source set has insufficient source-pose diversity for the fixed query budget",
            "m176_materialization_note": (
                "M176 must compute this from source coverage keys and source-ready split rows only; no target/viewpoint "
                "distance may be used."
            ),
            "why_needed": "M119-M127 show that adding target-free source observations can recover a source-coverage case, while M174b shows reranking alone cannot.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "detector_confidence_uncertainty_v1",
            "selected_for_m176": True,
            "trigger_family": "current_evidence_reliability",
            "allowed_signal": "detector-confidence distribution and reachable current-candidate count",
            "trigger_rule": "fire when current candidates are low-confidence or too few under the fixed budget",
            "m176_materialization_note": "Thresholds must be fixed before goal-evaluation and reported in trigger rows.",
            "why_needed": "Candidate-source expansion is only useful when current evidence is weak enough to justify re-observation cost.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "path_or_source_ready_gap_v1",
            "selected_for_m176": True,
            "trigger_family": "navigation_feasibility",
            "allowed_signal": "path-ready/source-ready status and candidate-source availability",
            "trigger_rule": "fire when source-ready rows exist but current path-ready candidate support is sparse",
            "m176_materialization_note": "Do not use nearest eval-viewpoint distance; use only pre-execution reachability/source readiness.",
            "why_needed": "A semantic map that cannot expose navigable source gaps collapses into detector-confidence ranking.",
        },
        {
            "version": VERSION,
            "row_type": "trigger_contract",
            "trigger_id": "structured_task_context_budget_gate_v1",
            "selected_for_m176": False,
            "trigger_family": "task_context_secondary_condition",
            "allowed_signal": "structured task context if a future E006 redesign re-promotes it",
            "trigger_rule": "optional budget gate only; it cannot be the main source-expansion trigger in M176",
            "m176_materialization_note": "Keep human intent as a logged ablation axis unless a new E006-M09 policy redesign passes.",
            "why_needed": "E006-M08 rejects human intent as a main claim under current evidence, so M175 must not hide the source-coverage mechanism behind task context.",
        },
    ]


def build_input_contract_rows(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = seed_rows[0] if seed_rows else {}
    allowed = list(seed.get("allowed_inputs") or [])
    blocked = list(seed.get("blocked_inputs") or [])
    allowed.extend(
        [
            "target-free source pose pool",
            "candidate-source budget",
            "source expansion route id",
        ]
    )
    blocked.extend(
        [
            "nearest eval-viewpoint distance",
            "candidate-to-target distance",
            "post-execution StopRank",
            "posthoc threshold selected from M176 goal-evaluation",
        ]
    )
    rows: list[dict[str, Any]] = []
    for field in allowed:
        rows.append(
            {
                "version": VERSION,
                "row_type": "input_contract",
                "field_group": field,
                "allowed_for_m176": True,
                "blocked_for_m176": False,
                "reason": "Available before evaluation and compatible with source expansion/re-observation planning.",
            }
        )
    for field in blocked:
        rows.append(
            {
                "version": VERSION,
                "row_type": "input_contract",
                "field_group": field,
                "allowed_for_m176": False,
                "blocked_for_m176": True,
                "reason": "Would leak evaluation labels or tune the method after seeing navigation/goal outcomes.",
            }
        )
    return rows


def build_candidate_source_route_rows(m120: dict[str, Any], m121: dict[str, Any], m124: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "candidate_source_route",
            "route_id": "m121_target_free_source_pose_pool_template_v1",
            "decision": "select_as_template",
            "selected_for_m176": True,
            "requires_long_job_now": False,
            "reuses_existing_artifact": True,
            "source_artifact": "E008-M121_hm3d_target_free_source_coverage_expansion_materialization_smoke_v0",
            "known_status": m121.get("status"),
            "known_observation_pose_rows": m121.get("observation_pose_rows"),
            "known_render_plan_rows": m121.get("render_plan_rows"),
            "known_detector_prediction_rows": m124.get("prediction_rows"),
            "known_path_ready_candidate_rows": None,
            "why_selected": "It is the existing target-free source expansion route with target/viewpoint source-placement leakage false.",
            "claim_boundary": "Template reuse is not a full-denominator recovery claim.",
        },
        {
            "version": VERSION,
            "row_type": "candidate_source_route",
            "route_id": "full_val_mini_triggered_source_pool_materialization_v1",
            "decision": "select_primary_m176_route",
            "selected_for_m176": True,
            "requires_long_job_now": False,
            "reuses_existing_artifact": False,
            "source_artifact": "new M176 rows under local_dataset/HM3D_navigation_bridge",
            "known_status": None,
            "known_observation_pose_rows": None,
            "known_render_plan_rows": None,
            "known_detector_prediction_rows": None,
            "known_path_ready_candidate_rows": None,
            "why_selected": "M176 must test whether source-coverage triggers can create policy-visible source requests on the fixed full-val-mini denominator.",
            "claim_boundary": "No render/detector/trajectory claim until downstream materialization changes selected policy rows.",
        },
        {
            "version": VERSION,
            "row_type": "candidate_source_route",
            "route_id": "external_map_assisted_source_pool_v1",
            "decision": "defer_baseline_route",
            "selected_for_m176": False,
            "requires_long_job_now": False,
            "reuses_existing_artifact": False,
            "source_artifact": "ConceptGraphs/Open3DSG/HOV-SG style map route",
            "known_status": m120.get("status"),
            "known_observation_pose_rows": None,
            "known_render_plan_rows": None,
            "known_detector_prediction_rows": None,
            "known_path_ready_candidate_rows": None,
            "why_selected": "Keep as a stronger external-baseline pressure route after the internal source-trigger interface is fixed.",
            "claim_boundary": "Cannot be used to claim H001 superiority until the baseline is run under the same denominator and input guards.",
        },
        {
            "version": VERSION,
            "row_type": "candidate_source_route",
            "route_id": "same_fixed_pool_source_coverage_rerank_v1",
            "decision": "reject_closed_negative",
            "selected_for_m176": False,
            "requires_long_job_now": False,
            "reuses_existing_artifact": False,
            "source_artifact": "E008-M174/M174b",
            "known_status": "closed_negative",
            "known_observation_pose_rows": None,
            "known_render_plan_rows": None,
            "known_detector_prediction_rows": None,
            "known_path_ready_candidate_rows": None,
            "why_selected": "M174b shows this route is inert under fixed guards and even the no-confidence-guard negative control.",
            "claim_boundary": "Do not revive without a new non-posthoc principle and a new precommitted contract.",
        },
    ]


def build_m176_materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "m176_materialization_plan",
            "artifact_name": "source_coverage_trigger_rows.jsonl",
            "required": True,
            "contents": "one row per benchmark/query context with trigger decisions and allowed-signal values",
            "pass_condition": "at least one non-leaky trigger row and zero blocked-input failures",
        },
        {
            "version": VERSION,
            "row_type": "m176_materialization_plan",
            "artifact_name": "candidate_source_expansion_plan_rows.jsonl",
            "required": True,
            "contents": "target-free source-pool rows requested by selected triggers",
            "pass_condition": "source rows are attached before evaluation and preserve the fixed benchmark denominator",
        },
        {
            "version": VERSION,
            "row_type": "m176_materialization_plan",
            "artifact_name": "allowed_input_audit_rows.jsonl",
            "required": True,
            "contents": "field-level audit for allowed/blocked M175 inputs",
            "pass_condition": "blocked fields are absent from trigger and source-placement rows",
        },
        {
            "version": VERSION,
            "row_type": "m176_materialization_plan",
            "artifact_name": "route_decision_rows.jsonl",
            "required": True,
            "contents": "decision among render/detector expansion, external-map route, or stop-and-record",
            "pass_condition": "no Docker trajectory execution is selected until policy-visible rows change",
        },
    ]


def build_pre_execution_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "pre_execution_gate",
            "gate_id": "m176_contract_materialization_gate",
            "gate_stage": "before_render_or_detector_long_job",
            "pass_condition": "M176 writes trigger and candidate-source expansion plan rows with leakage audit pass.",
            "current_status": "next",
            "blocks_docker_trajectory_execution": True,
        },
        {
            "version": VERSION,
            "row_type": "pre_execution_gate",
            "gate_id": "policy_visible_change_gate",
            "gate_stage": "before_docker_trajectory_execution",
            "pass_condition": "expanded candidate-source rows change selected policy rows relative to detector-confidence baseline.",
            "current_status": "not_ready",
            "blocks_docker_trajectory_execution": True,
        },
        {
            "version": VERSION,
            "row_type": "pre_execution_gate",
            "gate_id": "protected_baseline_preservation_gate",
            "gate_stage": "before_any_claim",
            "pass_condition": "detector-confidence reachable subset remains unchanged and reported as the protected naive baseline.",
            "current_status": "required",
            "blocks_docker_trajectory_execution": False,
        },
        {
            "version": VERSION,
            "row_type": "pre_execution_gate",
            "gate_id": "trajectory_preflight_gate",
            "gate_stage": "after_policy_visible_change",
            "pass_condition": "runner-compatible rows, source-ready/source-gap split, path costs, and Docker/data preflight pass.",
            "current_status": "future",
            "blocks_docker_trajectory_execution": True,
        },
    ]


def build_disconfirmation_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "disconfirmation_condition",
            "condition_id": "no_nonleaky_trigger_rows",
            "interpretation": "Source coverage is not available as a deployable trigger under the current row schema.",
            "next_action_if_observed": "close the internal trigger route or move to external map-assisted proposal-source route.",
        },
        {
            "version": VERSION,
            "row_type": "disconfirmation_condition",
            "condition_id": "source_expansion_no_policy_visible_change",
            "interpretation": "Candidate-source expansion is materialized but does not alter the decision layer.",
            "next_action_if_observed": "do not run trajectories; decompose whether detector confidence or source pose coverage suppresses the expansion.",
        },
        {
            "version": VERSION,
            "row_type": "disconfirmation_condition",
            "condition_id": "only_visit_cost_increases",
            "interpretation": "The method adds observation burden without evidence of recovery or policy improvement.",
            "next_action_if_observed": "record as negative and require stronger source selector or external map baseline.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "method_form_from_failure_diagnosis",
            "supported": True,
            "claim_boundary": "M175 supports only that the next method form should be source-coverage-triggered source expansion, derived from M174b failure diagnosis.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "within_pool_source_coverage_reranking",
            "supported": False,
            "claim_boundary": "Closed negative under M174b unless a new precommitted principle is introduced.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still requires M176 materialization, render/detector or external candidate generation, policy-visible row change, Docker trajectory execution, and protected-baseline interpretation.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context remains secondary until a future E006 redesign passes strong-baseline and transfer gates.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "reviewer_defense",
            "issue_id": "why_not_tune_utility_weights",
            "response": "M174b shows the selected utility has zero positive rows and the no-confidence-guard negative control also has zero positive rows; tuning would be conclusion-fitting.",
        },
        {
            "version": VERSION,
            "row_type": "reviewer_defense",
            "issue_id": "why_semantic_mapping",
            "response": "The decision is about whether the map has sufficient observation/source coverage before ranking, not about a standalone detector score.",
        },
        {
            "version": VERSION,
            "row_type": "reviewer_defense",
            "issue_id": "why_no_docker_trajectory_now",
            "response": "M175 is a contract; Docker trajectory execution is blocked until expanded source rows change policy-visible rows and pass preflight.",
        },
        {
            "version": VERSION,
            "row_type": "reviewer_defense",
            "issue_id": "why_not_claim_human_intent",
            "response": "E006-M08 currently rejects human intent as a main claim, so M175 keeps task context as a secondary budget/ablation axis.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    trigger_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M175 Source-Coverage Trigger / Candidate-Source Expansion Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M174b status: `{coverage['m174b_status']}`.",
            f"- M174b selected changed episode rows: {coverage['m174b_selected_changed_episode_rows']}.",
            f"- M174b selected positive utility rows: {coverage['m174b_selected_positive_utility_rows']}.",
            f"- M121 target-free observation pose rows available as template: {coverage['m121_observation_pose_rows']}.",
            f"- M124 target-free detector prediction rows available as diagnostic template: {coverage['m124_prediction_rows']}.",
            f"- Selected method family: `{coverage['selected_method_id']}`.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Method Contract",
            "",
            table(method_rows, ["method_id", "method_role", "protected_baseline_policy_id", "candidate_source_pool_expansion_allowed", "posthoc_weight_tuning_allowed"]),
            "",
            "## Trigger Contract",
            "",
            table(trigger_rows, ["trigger_id", "selected_for_m176", "trigger_family", "allowed_signal"]),
            "",
            "## Candidate-Source Routes",
            "",
            table(route_rows, ["route_id", "decision", "selected_for_m176", "requires_long_job_now", "known_status"]),
            "",
            "## Pre-Execution Gates",
            "",
            table(gate_rows, ["gate_id", "gate_stage", "current_status", "blocks_docker_trajectory_execution"]),
            "",
            "## Claim Boundary",
            "",
            "- M175 is not a navigation performance result.",
            "- M175 does not relaunch Docker, render, detector, or trajectory jobs.",
            "- M175 keeps within-pool source-coverage reranking closed negative and moves source coverage to the map/source acquisition interface.",
            "- M176 must materialize non-leaky trigger/source-expansion rows before any downstream execution is justified.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m120 = read_json(M120_DIR / "coverage.json")
    m121 = read_json(M121_DIR / "coverage.json")
    m124 = read_json(M124_DIR / "e008_m124_verification_coverage.json")
    m168 = read_json(M168_DIR / "coverage.json")
    m174 = read_json(M174_DIR / "coverage.json")
    m174b = read_json(M174B_DIR / "coverage.json")
    seed_rows = read_jsonl(M174B_DIR / "next_contract_seed_rows.jsonl")
    failure_rows = read_jsonl(M174B_DIR / "failure_mechanism_rows.jsonl")

    missing: list[str] = []
    if m174b.get("status") != "e008_m174b_source_coverage_utility_conservatism_failure_decomposition_ready":
        missing.append("M174b ready coverage")
    if not seed_rows:
        missing.append("M174b next contract seed rows")
    if not failure_rows:
        missing.append("M174b failure mechanism rows")
    if m120.get("status") != "e008_m120_hm3d_target_free_source_coverage_expansion_contract_ready":
        missing.append("M120 target-free source expansion contract")
    if not str(m121.get("status", "")).startswith("e008_m121_hm3d_target_free_source_coverage_expansion_materialization_smoke_ready"):
        missing.append("M121 target-free source materialization")

    ready = not missing

    method_rows = build_method_contract_rows(seed_rows)
    trigger_rows = build_trigger_contract_rows()
    input_rows = build_input_contract_rows(seed_rows)
    route_rows = build_candidate_source_route_rows(m120, m121, m124)
    m176_rows = build_m176_materialization_plan_rows()
    gate_rows = build_pre_execution_gate_rows()
    disconfirm_rows = build_disconfirmation_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m120_status": m120.get("status"),
        "m121_status": m121.get("status"),
        "m124_status": m124.get("status"),
        "m168_status": m168.get("status"),
        "m174_status": m174.get("status"),
        "m174b_status": m174b.get("status"),
        "m174b_selected_changed_episode_rows": m174b.get("selected_changed_episode_rows"),
        "m174b_selected_positive_utility_rows": m174b.get("selected_positive_utility_rows"),
        "m174b_no_confidence_guard_positive_utility_rows": m174b.get("no_confidence_guard_positive_utility_rows"),
        "m121_observation_pose_rows": m121.get("observation_pose_rows"),
        "m121_render_plan_rows": m121.get("render_plan_rows"),
        "m124_prediction_rows": m124.get("prediction_rows"),
        "m124_pre_cap_candidate_rows": m124.get("pre_cap_candidate_rows"),
        "selected_method_id": SELECTED_METHOD,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "method_contract_rows": len(method_rows),
        "trigger_contract_rows": len(trigger_rows),
        "input_contract_rows": len(input_rows),
        "candidate_source_route_rows": len(route_rows),
        "m176_materialization_plan_rows": len(m176_rows),
        "pre_execution_gate_rows": len(gate_rows),
        "disconfirmation_rows": len(disconfirm_rows),
        "claim_boundary_rows": len(claim_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "within_pool_source_coverage_rerank_closed_negative": True,
        "posthoc_tuning_allowed": False,
        "docker_trajectory_execution_ready": False,
        "render_or_detector_long_job_ready_now": False,
        "m176_materialization_ready_next": ready,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M175 inputs",
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "method_contract_rows.jsonl", method_rows)
    write_jsonl(ARTIFACT_DIR / "trigger_contract_rows.jsonl", trigger_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_source_route_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m176_materialization_plan_rows.jsonl", m176_rows)
    write_jsonl(ARTIFACT_DIR / "pre_execution_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "disconfirmation_rows.jsonl", disconfirm_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "m174b_failure_mechanism_snapshot_rows.jsonl", failure_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, method_rows, trigger_rows, route_rows, gate_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
