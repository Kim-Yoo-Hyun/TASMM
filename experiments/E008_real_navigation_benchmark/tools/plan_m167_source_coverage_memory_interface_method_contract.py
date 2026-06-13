#!/usr/bin/env python3
"""Freeze the E008-M167 source-coverage memory-interface method contract."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M166_DIR = EXP_ROOT / "artifacts" / "E008-M166_navigation_failure_boundary_method_pivot_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M167_source_coverage_memory_interface_method_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M167_source_coverage_memory_interface_method_contract_v0"

VERSION = "e008_m167_source_coverage_memory_interface_method_contract_v0"
READY_STATUS = "e008_m167_source_coverage_memory_interface_method_contract_ready"
BLOCKED_STATUS = "e008_m167_source_coverage_memory_interface_method_contract_blocked"
NEXT_UNIT = "E008-M168 source-coverage memory-interface row materialization"

SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_ABLATION = "source_coverage_only_task_agnostic_v1"
CONFIDENCE_ONLY_ABLATION = "confidence_floor_only_v1"
PATH_ONLY_ABLATION = "path_cost_only_reachable_subset_v1"
STATIC_STALE_BASELINE = "static_stale_memory_interface_baseline"
CONCEPTGRAPHS_BASELINE = "ConceptGraphs-only open-vocabulary map"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    try:
        out = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{out:.6f}" if math.isfinite(out) else "NA"


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def method_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_source_coverage_memory_interface_policy",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "candidate/source exposure must be changed under confidence guard; local pairwise path swaps are excluded",
            "confidence_band_abs": 0.05,
            "coverage_unit": "frame_pose_role + bearing_relative_deg + shell_radius_bucket + observation_pose_id",
            "coverage_diversity_scope": "within confidence band only",
            "source_gap_trigger_scope": "disabled_on_current_denominator; allowed only when pre-labeled source-gap/source-coverage rows exist",
            "path_cost_scope": "secondary tie-break inside a coverage/confidence bucket, not a global rank objective",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "M165 rejects local rerank scale-up; this method changes the source/candidate interface while preserving the confidence floor and detector-confidence baseline.",
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": PROTECTED_BASELINE,
            "policy_role": "protected_naive_baseline",
            "base_order_policy_id": PROTECTED_BASELINE,
            "principle": "current evidence confidence first",
            "confidence_band_abs": 0.0,
            "coverage_unit": "none",
            "coverage_diversity_scope": "none",
            "source_gap_trigger_scope": "none",
            "path_cost_scope": "none",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "why_this_form": "This remains the protected baseline because M165 failed to beat it.",
        },
    ]


def input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("candidate_position_m", True, "candidate geometry"),
        ("execution_stop_position_m", True, "candidate stop point"),
        ("confidence", True, "current evidence reliability"),
        ("observation_pose_id", True, "source coverage identity"),
        ("frame_pose_role", True, "source coverage role"),
        ("bearing_relative_deg", True, "source coverage direction"),
        ("shell_radius_m", True, "source coverage radius"),
        ("source_to_candidate_path_cost_m", True, "path feasibility/cost tie-break"),
        ("path_ready", True, "hard feasibility guard"),
        ("source_gap_flag", True, "allowed only if precomputed before evaluation"),
    ]
    blocked = [
        ("eval_goal_position", False, "ObjectNav goal is metric-only"),
        ("eval_first_viewpoint_position", False, "ObjectNav viewpoint is metric-only"),
        ("eval_all_viewpoint_positions", False, "ObjectNav viewpoints are metric-only"),
        ("primary_eval_hit", False, "success label leakage"),
        ("SR", False, "metric output"),
        ("SPL", False, "metric output"),
        ("success_proposal_uid", False, "posthoc success leakage"),
        ("candidate_to_nearest_eval_viewpoint_xz_m", False, "metric-only distance"),
    ]
    rows = []
    for field, allowed_for_policy, rationale in allowed + blocked:
        rows.append(
            {
                "version": VERSION,
                "row_type": "input_contract",
                "field": field,
                "allowed_for_policy": allowed_for_policy,
                "rationale": rationale,
            }
        )
    return rows


def comparison_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": STATIC_STALE_BASELINE,
            "role": "required_baseline_when_stale_rows_exist",
            "materialized_in_m168": False,
            "reason": "current full-val-mini target-free denominator contains current-observation detector candidates only",
        },
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": PROTECTED_BASELINE,
            "role": "protected_primary_baseline",
            "materialized_in_m168": True,
            "reason": "must be beaten before any positive navigation claim",
        },
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": CONCEPTGRAPHS_BASELINE,
            "role": "external_map_baseline_pressure",
            "materialized_in_m168": False,
            "reason": "requires matched external candidate interface; not silently mixed with detector denominator",
        },
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": SOURCE_COVERAGE_ABLATION,
            "role": "task_agnostic_source_coverage_ablation",
            "materialized_in_m168": True,
            "reason": "tests whether source coverage alone explains the selected policy",
        },
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": SELECTED_POLICY,
            "role": "selected_h001_variant",
            "materialized_in_m168": True,
            "reason": "tests the M166 method pivot",
        },
    ]


def ablation_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": SOURCE_COVERAGE_ABLATION,
            "ablation": "remove memory/confidence trust and keep source coverage diversity",
            "expected_failure_if_principle_is_correct": "more source diversity but worse confidence/visit efficiency",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": CONFIDENCE_ONLY_ABLATION,
            "ablation": "keep confidence floor without source-coverage interface",
            "expected_failure_if_principle_is_correct": "near detector-confidence behavior and no source-coverage recovery",
        },
        {
            "version": VERSION,
            "row_type": "ablation_contract",
            "policy_id": PATH_ONLY_ABLATION,
            "ablation": "rank reachable candidates by path cost only",
            "expected_failure_if_principle_is_correct": "shorter first hops but worse target recovery or confidence reliability",
        },
    ]


def metric_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "protected_navigation_non_regression_v1",
            "required_for_positive_claim": True,
            "comparison_policy_id": PROTECTED_BASELINE,
            "pass_condition": "delta_SR >= 0 and delta_SPL > 0 and delta_CandidateVisits <= 0",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "source_coverage_mechanism_test_v1",
            "required_for_positive_claim": True,
            "comparison_policy_id": SOURCE_COVERAGE_ABLATION,
            "pass_condition": "selected policy beats source-coverage-only on SPL or visits without losing SR",
        },
        {
            "version": VERSION,
            "row_type": "metric_target",
            "metric_target_id": "external_baseline_future_gate_v1",
            "required_for_final_claim": True,
            "comparison_policy_id": CONCEPTGRAPHS_BASELINE,
            "pass_condition": "matched external candidate interface exists before direct final comparison",
        },
    ]


def materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "materialization_plan",
            "selected_next_unit": NEXT_UNIT,
            "source_candidate_root": "E008-M156_budget_aware_utility_trajectory_contract_v0/base_candidate_rows.jsonl",
            "source_support_root": "E008-M156_budget_aware_utility_trajectory_contract_v0/",
            "policies_to_materialize": [
                SELECTED_POLICY,
                PROTECTED_BASELINE,
                SOURCE_COVERAGE_ABLATION,
                CONFIDENCE_ONLY_ABLATION,
                PATH_ONLY_ABLATION,
            ],
            "required_outputs": [
                "source_coverage_candidate_rows.jsonl",
                "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "policy_plan_rows.jsonl",
                "policy_order_audit_rows.jsonl",
                "source_coverage_component_rows.jsonl",
                "leakage_audit_rows.jsonl",
            ],
            "launch_long_job_now": False,
        }
    ]


def claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "method_contract_ready",
            "supported": True,
            "claim_boundary": "M167 fixes method/input/baseline/metric contracts only; no row materialization or trajectory result yet.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_memory_interface_improves_navigation",
            "supported": False,
            "claim_boundary": "Requires M168 materialization, M169 Docker contract, later execution, and protected-baseline interpretation.",
        },
    ]


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_row_materialization",
            "selected_next_unit": NEXT_UNIT,
            "selected_policy_id": SELECTED_POLICY,
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "launch_long_job_now": False,
            "row_materialization_ready_next": True,
        }
    ]


def report(coverage: dict[str, Any], methods: list[dict[str, Any]], comparisons: list[dict[str, Any]], metrics: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M167 Source-Coverage Memory-Interface Method Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M166 status: `{coverage['m166_status']}`.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Posthoc threshold change allowed: {coverage['posthoc_threshold_change_allowed']}.",
            f"- Denominator change allowed: {coverage['denominator_change_allowed']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Method Contract",
            "",
            table(methods, ["policy_id", "policy_role", "principle", "coverage_diversity_scope", "path_cost_scope"]),
            "",
            "## Comparison Contract",
            "",
            table(comparisons, ["comparison_id", "role", "materialized_in_m168", "reason"]),
            "",
            "## Metric Targets",
            "",
            table(metrics, ["metric_target_id", "comparison_policy_id", "pass_condition"]),
            "",
            "## Claim Boundary",
            "",
            "- M167 is a pre-materialization contract step.",
            "- It does not claim navigation improvement.",
            "- `ConceptGraphs-only` and static stale memory are preserved in the comparison ledger but not mixed into the M168 detector denominator.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m166 = read_json(M166_DIR / "coverage.json")
    missing = []
    if m166.get("status") != "e008_m166_navigation_failure_boundary_method_pivot_contract_ready":
        missing.append("M166 ready coverage")
    if m166.get("selected_policy_id") != SELECTED_POLICY:
        missing.append("M166 selected policy mismatch")

    methods = method_rows()
    inputs = input_contract_rows()
    comparisons = comparison_rows()
    ablations = ablation_rows()
    metrics = metric_rows()
    materialization = materialization_plan_rows()
    claims = claim_rows()
    routes = route_rows()

    ready = not missing
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m166_status": m166.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "method_contract_rows": len(methods),
        "input_contract_rows": len(inputs),
        "comparison_contract_rows": len(comparisons),
        "ablation_contract_rows": len(ablations),
        "metric_target_rows": len(metrics),
        "materialization_plan_rows": len(materialization),
        "posthoc_threshold_change_allowed": False,
        "denominator_change_allowed": False,
        "row_materialization_ready_next": ready,
        "docker_execution_contract_ready_now": False,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M167 inputs",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "method_contract_rows.jsonl", methods)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", inputs)
    write_jsonl(ARTIFACT_DIR / "comparison_contract_rows.jsonl", comparisons)
    write_jsonl(ARTIFACT_DIR / "ablation_contract_rows.jsonl", ablations)
    write_jsonl(ARTIFACT_DIR / "metric_target_rows.jsonl", metrics)
    write_jsonl(ARTIFACT_DIR / "materialization_plan_rows.jsonl", materialization)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claims)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", routes)
    (ARTIFACT_DIR / "report.md").write_text(report(coverage, methods, comparisons, metrics), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
