#!/usr/bin/env python3
"""Fix the E008-M137 confidence-preserving trajectory repair contract."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M133_DIR = EXP_ROOT / "artifacts" / "E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
M135_DIR = EXP_ROOT / "artifacts" / "E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0"
M136_DIR = EXP_ROOT / "artifacts" / "E008-M136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0"
)

VERSION = "e008_m137_target_free_confidence_preserving_trajectory_repair_contract_v0"
READY_STATUS = "e008_m137_target_free_confidence_preserving_trajectory_repair_contract_ready"
BLOCKED_STATUS = "e008_m137_target_free_confidence_preserving_trajectory_repair_contract_blocked"
NEXT_UNIT = "E008-M138 target-free confidence-preserving trajectory repair materialization smoke"

PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_BASELINE = "trajectory_greedy_confidence_only_reachable_v0"
FAILED_REPAIR = "trajectory_greedy_confidence_path_repair_v0"
PATH_ONLY_BASELINE = "trajectory_greedy_path_only_reachable_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
SELECTED_POLICY = "confidence_band_trajectory_tiebreak_v0"
HARD_VETO_POLICY = "confidence_preserving_hard_veto_v0"
SOURCE_GAP_POLICY = "source_gap_triggered_coverage_fallback_v0"

CONFIDENCE_BAND_ABS = 0.03
MIN_PATH_ADVANTAGE_M = 1.0
M138_SCRIPT = "experiments/E008_real_navigation_benchmark/tools/run_m138_target_free_confidence_preserving_repair_materialization.py"

BLOCKED_POLICY_FIELDS = [
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
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
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "NA"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def primary_candidate_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in candidate_rows
        if row.get("policy_id") == PRIMARY_BASELINE
        and row.get("path_ready")
        and not row.get("policy_input_uses_eval_goal_or_viewpoint")
        and not row.get("policy_input_uses_success_label")
    ]
    return sorted(
        rows,
        key=lambda row: (
            -(finite_float(row.get("confidence")) or -math.inf),
            int(row.get("candidate_rank_m09") or 10**9),
            str(row.get("proposal_uid")),
        ),
    )


def metric_row(metric_rows: list[dict[str, Any]], policy_id: str) -> dict[str, Any]:
    for row in metric_rows:
        if row.get("metric_scope") == "policy_aggregate" and row.get("policy_id") == policy_id:
            return row
    return {}


def confidence_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [finite_float(row.get("confidence")) for row in rows]
    clean = [value for value in values if value is not None]
    top = max(clean) if clean else None
    low = min(clean) if clean else None
    in_band = [
        row
        for row in rows
        if top is not None and finite_float(row.get("confidence")) is not None
        and top - float(finite_float(row.get("confidence"))) <= CONFIDENCE_BAND_ABS
    ]
    return {
        "confidence_min": low,
        "confidence_max": top,
        "confidence_range": (top - low) if top is not None and low is not None else None,
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "top_band_candidate_rows": len(in_band),
        "top_band_candidate_proposals": [row.get("proposal_uid") for row in in_band],
    }


def build_policy_contract_rows(stats: dict[str, Any]) -> list[dict[str, Any]]:
    common = {
        "version": VERSION,
        "row_type": "policy_contract",
        "candidate_universe": "path_ready_label_compatible_candidates_from_m133",
        "protected_naive_baseline": PRIMARY_BASELINE,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_success_label_for_policy": False,
        "uses_task_context_for_decision": False,
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "min_path_advantage_m": MIN_PATH_ADVANTAGE_M,
        "m138_materialize": True,
        "m139_execute": True,
    }
    return [
        {
            **common,
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_confidence_preserving_repair",
            "selected_for_m138": True,
            "ranking_form": (
                "preserve detector-confidence order across confidence bands; inside each band only, choose a lower "
                "current-pose geodesic candidate when the path advantage is at least 1.0m; hard-veto path-infeasible candidates"
            ),
            "path_cost_use": "within-band tie-break and feasibility guard only",
            "primary_expected_fix": "avoid M135 confidence-efficiency regression while retaining a trajectory-cost safety signal",
            "required_comparison": PRIMARY_BASELINE,
            "pass_condition_for_m139": "same candidate universe, no eval-goal leakage, no confidence-order override outside the band",
        },
        {
            **common,
            "policy_id": HARD_VETO_POLICY,
            "policy_role": "hard_feasibility_veto_ablation",
            "selected_for_m138": True,
            "ranking_form": "detector-confidence order with only path-ready/current-segment infeasibility vetoes",
            "path_cost_use": "veto only; no rank change among feasible candidates",
            "primary_expected_fix": "tests whether feasibility filtering alone is enough",
            "required_comparison": PRIMARY_BASELINE,
            "pass_condition_for_m139": "preserves confidence ordering among all non-vetoed candidates",
        },
        {
            **common,
            "policy_id": SOURCE_GAP_POLICY,
            "policy_role": "source_gap_fallback_contract_not_immediate_main",
            "selected_for_m138": False,
            "ranking_form": "trigger source-coverage fallback only when confidence-protected candidate set has no feasible candidate or low-confidence ambiguous evidence",
            "path_cost_use": "source-gap trigger and fallback budget allocator",
            "primary_expected_fix": "separate candidate-source failure from ranking failure",
            "required_comparison": "`ConceptGraphs` / detector-confidence fallback routes",
            "pass_condition_for_m139": "not immediate on the current one-case M138 unless trigger fires without eval labels",
        },
        {
            **common,
            "policy_id": CONFIDENCE_ONLY_BASELINE,
            "policy_role": "strong_confidence_only_ablation",
            "selected_for_m138": True,
            "ranking_form": "pure detector-confidence ordering over path-ready candidates",
            "path_cost_use": "none",
            "primary_expected_fix": "strong ablation that M135 tied with detector-confidence",
            "required_comparison": SELECTED_POLICY,
            "pass_condition_for_m139": "same candidate universe retained",
        },
        {
            **common,
            "policy_id": FAILED_REPAIR,
            "policy_role": "negative_prior_repair_baseline",
            "selected_for_m138": True,
            "ranking_form": "previous M133/M135 confidence minus normalized current-pose path-cost repair",
            "path_cost_use": "unrestricted ranking score replacement",
            "primary_expected_fix": "none; retained to prove M137 prevents the M135 failure",
            "required_comparison": SELECTED_POLICY,
            "pass_condition_for_m139": "kept only as negative control",
        },
        {
            **common,
            "policy_id": PATH_COST_BASELINE,
            "policy_role": "negative_source_to_candidate_path_baseline",
            "selected_for_m138": True,
            "ranking_form": "source-to-candidate path-cost ascending",
            "path_cost_use": "primary ranking signal",
            "primary_expected_fix": "none; retained to show path-cost replacement remains weak",
            "required_comparison": SELECTED_POLICY,
            "pass_condition_for_m139": "same candidate universe retained",
        },
    ]


def build_confidence_band_rows(stats: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "confidence_band_contract",
            "band_id": "top_confidence_band_v0",
            "confidence_band_abs": CONFIDENCE_BAND_ABS,
            "confidence_min": stats.get("confidence_min"),
            "confidence_max": stats.get("confidence_max"),
            "confidence_range": stats.get("confidence_range"),
            "candidate_rows_in_top_band": stats.get("top_band_candidate_rows"),
            "allowed_override": "only candidates within confidence_band_abs of the current best confidence may be reordered by trajectory cost",
            "blocked_override": "a candidate outside the current confidence band cannot jump ahead only because it is closer",
            "min_path_advantage_m": MIN_PATH_ADVANTAGE_M,
            "tie_break_order": [
                "current_pose_to_candidate_geodesic_m ascending",
                "detector confidence descending",
                "candidate_rank_m09 ascending",
                "proposal_uid stable sort",
            ],
        },
        {
            "version": VERSION,
            "row_type": "confidence_band_contract",
            "band_id": "future_scale_calibration_note",
            "confidence_band_abs": CONFIDENCE_BAND_ABS,
            "confidence_min": stats.get("confidence_min"),
            "confidence_max": stats.get("confidence_max"),
            "confidence_range": stats.get("confidence_range"),
            "candidate_rows_in_top_band": stats.get("top_band_candidate_rows"),
            "allowed_override": "M137 uses a fixed conservative band for the one-case materialization; scale-up should calibrate the band on heldout scenes",
            "blocked_override": "do not tune the band using ObjectNav success labels or eval-goal distances",
            "min_path_advantage_m": MIN_PATH_ADVANTAGE_M,
            "tie_break_order": ["heldout calibration required before final paper claim"],
        },
    ]


def build_allowed_input_rows() -> list[dict[str, Any]]:
    allowed = [
        ("confidence", "detector confidence score"),
        ("selection_score", "detector/ranker score"),
        ("candidate_rank_m09", "detector candidate rank"),
        ("proposal_uid", "stable candidate id"),
        ("label_canonical", "query-compatible candidate label"),
        ("path_ready", "navmesh/source-readiness flag"),
        ("blocked_candidate_for_path_policy", "policy-visible candidate path blocker"),
        ("candidate_stop_position_m", "navmesh candidate stop"),
        ("execution_stop_position_m", "candidate execution stop"),
        ("current_pose_to_candidate_geodesic_m", "current-pose to candidate path cost from trajectory matrix"),
        ("current_pose_to_candidate_path_found", "current-pose path feasibility"),
        ("source_to_candidate_path_cost_m", "first-step prior and negative-control baseline only"),
        ("trajectory_cost_matrix_id", "path-cost matrix identifier"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "source": source,
            "allowed_for_policy": True,
            "uses_objectnav_eval_goal_or_viewpoint": False,
            "uses_success_label": False,
        }
        for field, source in allowed
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "blocked_for_policy": True,
            "reason": "ObjectNav eval goal/viewpoint, hit label, or posthoc metric distance is metric-only and cannot affect M138 ranking.",
        }
        for field in BLOCKED_POLICY_FIELDS
    ]


def build_guardrail_rows() -> list[dict[str, Any]]:
    return [
        guardrail(
            "confidence_order_protection",
            "candidate outside confidence band cannot outrank current band member by path cost alone",
            "prevents_m135_confidence_efficiency_regression",
        ),
        guardrail(
            "hard_feasibility_veto",
            "candidate may be dropped or delayed only if path_ready is false, blocked_candidate_for_path_policy is true, or current segment has no path",
            "keeps path cost as feasibility guard",
        ),
        guardrail(
            "no_eval_goal_policy_input",
            "ObjectNav goal/viewpoint coordinates and success labels remain metric-only",
            "preserves leakage-safe trajectory policy",
        ),
        guardrail(
            "protected_baseline_comparison",
            "M139 must compare against detector-confidence and confidence-only baselines on the same candidate universe",
            "keeps top-tier reviewer defense against naive baseline",
        ),
        guardrail(
            "one_case_boundary",
            "M138/M139 one-case result cannot become final real navigation claim without scale and external baselines",
            "prevents overclaiming",
        ),
    ]


def guardrail(guardrail_id: str, rule: str, purpose: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "row_type": "policy_guardrail",
        "guardrail_id": guardrail_id,
        "rule": rule,
        "purpose": purpose,
    }


def build_readiness_gate_rows(
    missing_inputs: list[str],
    m133_ready: bool,
    m136_ready: bool,
    candidate_rows: list[dict[str, Any]],
    blocked_hits: int,
) -> list[dict[str, Any]]:
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            "M133/M135/M136 artifacts needed for M137 are present.",
            True,
        ),
        (
            "m133_candidate_universe_ready",
            m133_ready and bool(candidate_rows),
            "M133 path-ready candidate universe and trajectory cost matrix are ready.",
            True,
        ),
        (
            "m136_failure_diagnosis_ready",
            m136_ready,
            "M136 identifies why current repair must not be scaled.",
            True,
        ),
        (
            "blocked_fields_absent_from_candidate_policy_rows",
            blocked_hits == 0,
            "M133 policy candidate rows do not contain eval-goal/success policy fields.",
            True,
        ),
        (
            "confidence_preserving_contract_ready",
            True,
            "Selected M137 policy uses path cost only as tie-break/veto/source-gap trigger.",
            True,
        ),
        (
            "long_job_not_required",
            True,
            "M137 is a contract unit; M138 is repository-local materialization and M139 is the next Docker trajectory execution gate.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m138": blocks_m138 and not passed,
            "rationale": rationale,
        }
        for gate_id, passed, rationale, blocks_m138 in gates
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "supported_confidence_preserving_contract",
            True,
            "M137 fixes a contract that protects detector-confidence ordering and limits path cost to tie-break/veto/source-gap trigger roles.",
        ),
        claim(
            "unsupported_materialized_policy_rows",
            False,
            "M137 does not materialize new candidate visit-order rows; that is M138.",
        ),
        claim(
            "unsupported_executed_navigation_improvement",
            False,
            "M137 does not execute Habitat trajectories; that is M139 or later.",
        ),
        claim(
            "unsupported_final_real_navigation_sr_spl",
            False,
            "Final SR/SPL still needs execution, scale, heldout transfer, and external navigation/search baselines.",
        ),
        claim(
            "unsupported_human_intent_main_claim",
            False,
            "M137 is target-free repair and does not change E006-M08 human-intent boundary.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "why_not_scale_m135_repair",
            "M135 selected repair loses `SPL` to detector-confidence / confidence-only baselines, so scaling it would scale a known strong-baseline failure.",
        ),
        defense(
            "why_confidence_band",
            "The closest naive baseline is detector-confidence; M137 only allows path cost to reorder candidates when detector evidence is effectively tied.",
        ),
        defense(
            "why_hard_veto",
            "Path feasibility is a valid action constraint, but using path length as a global replacement score caused the M130/M135 regression.",
        ),
        defense(
            "why_not_claim_navigation_yet",
            "M137 is a contract with one-case inputs; final navigation requires M138 materialization, M139 execution, scale, and external baselines.",
        ),
        defense(
            "how_this_tests_novelty",
            "It converts the failure diagnosis into a method-form constraint: semantic memory/search policies must preserve reliable current evidence while using map geometry as a guarded decision signal.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_m138_plan_rows() -> list[dict[str, Any]]:
    command = (
        "python "
        f"{M138_SCRIPT} "
        "--m133-root experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0 "
        "--m137-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0"
    )
    return [
        {
            "version": VERSION,
            "row_type": "m138_materialization_plan",
            "selected_next_unit": NEXT_UNIT,
            "script_to_implement": M138_SCRIPT,
            "requires_docker": False,
            "long_running_job": False,
            "input_artifacts": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M137_target_free_confidence_preserving_trajectory_repair_contract_v0",
            ],
            "output_artifact": "experiments/E008_real_navigation_benchmark/artifacts/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0",
            "derived_output": "local_dataset/HM3D_navigation_bridge/E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0",
            "expected_files": [
                "coverage.json",
                "confidence_preserving_candidate_rows.jsonl",
                "confidence_preserving_execution_plan_rows.jsonl",
                "policy_order_audit_rows.jsonl",
                "leakage_audit_rows.jsonl",
                "readiness_gate_rows.jsonl",
                "report.md",
            ],
            "exact_command_template": command,
            "claim_boundary": "M138 materializes confidence-preserving visit-order rows only; executed SR/SPL remains blocked until M139.",
        }
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_m135_trajectory_greedy_confidence_path_repair",
            "decision": "reject_now",
            "selected": False,
            "reason": "M136 shows the current repair loses `SPL` to detector-confidence / confidence-only baselines.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "confidence_band_trajectory_tiebreak_materialization",
            "decision": "select_next" if ready else "blocked_until_inputs_ready",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else None,
            "reason": "This is the minimal repair that keeps detector-confidence as the protected naive baseline.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "source_gap_triggered_coverage_fallback",
            "decision": "defer",
            "selected": False,
            "reason": "Keep as a future source-gap route; do not mix source-generation repair into the immediate ranking repair.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_sr_spl",
            "decision": "reject_now",
            "selected": False,
            "reason": "M137 is contract-only and does not produce executed navigation metrics.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    band_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M137 Target-Free Confidence-Preserving Trajectory Repair Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M133 status: `{coverage['m133_status']}`.",
            f"- M136 status: `{coverage['m136_status']}`.",
            f"- Base path-ready candidates: {coverage['base_path_ready_candidate_rows']}.",
            f"- M135 selected repair `SPL`: {fmt(coverage['m135_failed_repair_SPL'])}.",
            f"- M135 detector-confidence `SPL`: {fmt(coverage['m135_detector_confidence_SPL'])}.",
            f"- Selected policy: `{coverage['selected_policy']}`.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "policy_role",
                    "selected_for_m138",
                    "path_cost_use",
                    "required_comparison",
                ],
            ),
            "",
            "## Confidence Band",
            "",
            markdown_table(
                band_rows,
                [
                    "band_id",
                    "confidence_band_abs",
                    "confidence_min",
                    "confidence_max",
                    "candidate_rows_in_top_band",
                    "min_path_advantage_m",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m138", "rationale"]),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Claim Boundary",
            "",
            "- M137 supports a confidence-preserving repair contract only.",
            "- M137 does not materialize rows or execute trajectories.",
            "- Final real navigation `SR` / `SPL` remains blocked.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    m133_coverage = read_json(M133_DIR / "coverage.json")
    m135_metrics = read_jsonl(M135_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    m136_coverage = read_json(M136_DIR / "coverage.json")
    m133_candidate_rows = read_jsonl(M133_DIR / "trajectory_repair_candidate_rows.jsonl")

    required_inputs = [
        M133_DIR / "coverage.json",
        M133_DIR / "trajectory_repair_candidate_rows.jsonl",
        M133_DIR / "trajectory_cost_matrix_rows.jsonl",
        M135_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        M136_DIR / "coverage.json",
        M136_DIR / "repair_diagnosis_rows.jsonl",
    ]
    missing_inputs = [str(path.relative_to(ROOT)) for path in required_inputs if not path.exists()]
    primary_rows = primary_candidate_rows(m133_candidate_rows)
    stats = confidence_stats(primary_rows)
    blocked_hits = sum(1 for row in primary_rows for field in BLOCKED_POLICY_FIELDS if field in row)
    m133_ready = m133_coverage.get("status") == "e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_ready"
    m136_ready = (
        m136_coverage.get("status")
        == "e008_m136_target_free_trajectory_aware_repair_result_interpretation_scale_decision_ready"
    )

    policy_rows = build_policy_contract_rows(stats)
    band_rows = build_confidence_band_rows(stats)
    allowed_rows = build_allowed_input_rows()
    blocked_rows = build_blocked_input_rows()
    guardrail_rows = build_guardrail_rows()
    gate_rows = build_readiness_gate_rows(missing_inputs, m133_ready, m136_ready, primary_rows, blocked_hits)
    ready = not any(row["blocks_m138"] for row in gate_rows)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    plan_rows = build_m138_plan_rows()
    route_rows = build_route_decision_rows(ready)

    policy_counter = Counter(str(row.get("policy_id")) for row in m133_candidate_rows)
    detector_metric = metric_row(m135_metrics, PRIMARY_BASELINE)
    failed_metric = metric_row(m135_metrics, FAILED_REPAIR)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "missing_inputs": missing_inputs,
        "m133_status": m133_coverage.get("status"),
        "m136_status": m136_coverage.get("status"),
        "m136_selected_next_unit": m136_coverage.get("selected_next_unit"),
        "m135_detector_confidence_SPL": detector_metric.get("SPL"),
        "m135_failed_repair_SPL": failed_metric.get("SPL"),
        "m135_failed_repair_candidate_visits": failed_metric.get("CandidateVisits_mean"),
        "base_path_ready_candidate_rows": len(primary_rows),
        "candidate_rows_by_policy": dict(sorted(policy_counter.items())),
        "blocked_policy_field_hits_in_primary_candidate_rows": blocked_hits,
        "confidence_min": stats.get("confidence_min"),
        "confidence_max": stats.get("confidence_max"),
        "confidence_range": stats.get("confidence_range"),
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "top_band_candidate_rows": stats.get("top_band_candidate_rows"),
        "policy_contract_rows": len(policy_rows),
        "selected_policy": SELECTED_POLICY,
        "selected_next_unit": NEXT_UNIT if ready else None,
        "readiness_gate_rows": len(gate_rows),
        "gate_fail_count": sum(1 for row in gate_rows if row.get("gate_status") == "fail"),
        "launch_long_job_now": False,
        "m138_materialization_ready": ready,
        "m139_trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    output_files = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "policy_contract_rows.jsonl",
        ARTIFACT_DIR / "confidence_band_contract_rows.jsonl",
        ARTIFACT_DIR / "allowed_input_rows.jsonl",
        ARTIFACT_DIR / "blocked_input_rows.jsonl",
        ARTIFACT_DIR / "policy_guardrail_rows.jsonl",
        ARTIFACT_DIR / "readiness_gate_rows.jsonl",
        ARTIFACT_DIR / "claim_boundary_rows.jsonl",
        ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
        ARTIFACT_DIR / "m138_materialization_plan_rows.jsonl",
        ARTIFACT_DIR / "route_decision_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]
    write_json(output_files[0], coverage)
    write_jsonl(output_files[1], policy_rows)
    write_jsonl(output_files[2], band_rows)
    write_jsonl(output_files[3], allowed_rows)
    write_jsonl(output_files[4], blocked_rows)
    write_jsonl(output_files[5], guardrail_rows)
    write_jsonl(output_files[6], gate_rows)
    write_jsonl(output_files[7], claim_rows)
    write_jsonl(output_files[8], reviewer_rows)
    write_jsonl(output_files[9], plan_rows)
    write_jsonl(output_files[10], route_rows)
    output_files[11].write_text(
        build_report(coverage, policy_rows, band_rows, gate_rows, route_rows),
        encoding="utf-8",
    )
    mirror_outputs(output_files)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
