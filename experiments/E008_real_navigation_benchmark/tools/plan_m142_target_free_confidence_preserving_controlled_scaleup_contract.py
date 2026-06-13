#!/usr/bin/env python3
"""Build the E008-M142 confidence-preserving controlled scale-up contract."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M68_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M70_DIR = EXP_ROOT / "artifacts" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
M73_DIR = EXP_ROOT / "artifacts" / "E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0"
M138_DIR = EXP_ROOT / "artifacts" / "E008-M138_target_free_confidence_preserving_repair_materialization_smoke_v0"
M140_DIR = EXP_ROOT / "artifacts" / "E008-M140_target_free_confidence_preserving_repair_trajectory_execution_smoke_v0"
M141_DIR = EXP_ROOT / "artifacts" / "E008-M141_target_free_confidence_preserving_repair_result_interpretation_scale_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M142_target_free_confidence_preserving_controlled_scaleup_contract_v0"
)

VERSION = "e008_m142_target_free_confidence_preserving_controlled_scaleup_contract_v0"
READY_STATUS = "e008_m142_target_free_confidence_preserving_controlled_scaleup_contract_ready"
BLOCKED_STATUS = "e008_m142_target_free_confidence_preserving_controlled_scaleup_contract_blocked"
NEXT_UNIT = "E008-M143 full-val-mini confidence-preserving trajectory-cost materialization"

SELECTED_POLICY = "confidence_band_trajectory_tiebreak_v0"
PRIMARY_BASELINE = "detector_confidence_reachable_subset_v0"
CONFIDENCE_ONLY_BASELINE = "trajectory_greedy_confidence_only_reachable_v0"
HARD_VETO_ABLATION = "confidence_preserving_hard_veto_v0"
PRIOR_REPAIR_BASELINE = "trajectory_greedy_confidence_path_repair_v0"
PATH_COST_BASELINE = "path_cost_ascending_reachable_subset_v0"
POLICIES = [
    SELECTED_POLICY,
    HARD_VETO_ABLATION,
    PRIMARY_BASELINE,
    CONFIDENCE_ONLY_BASELINE,
    PRIOR_REPAIR_BASELINE,
    PATH_COST_BASELINE,
]

CONFIDENCE_BAND_ABS = 0.03
MIN_PATH_ADVANTAGE_M = 1.0


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
        return str(value)
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def unique_count(rows: list[dict[str, Any]], key: str) -> int:
    return len({str(row.get(key)) for row in rows if row.get(key) is not None})


def path_ready_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("candidate_usable_for_path_smoke") is True
        or row.get("navmesh_validation_status") == "candidate_path_ready"
    ]


def build_episode_stats(nav_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready_rows = path_ready_rows(nav_rows)
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ready_rows:
        by_episode[str(row.get("adapter_episode_id"))].append(row)
    path_ready_counts = [len(rows) for rows in by_episode.values()]
    return {
        "candidate_rows": len(nav_rows),
        "path_ready_candidate_rows": len(ready_rows),
        "episode_rows": unique_count(nav_rows, "adapter_episode_id"),
        "path_ready_episode_rows": len(by_episode),
        "scene_count": unique_count(nav_rows, "scene_key"),
        "category_count": unique_count(nav_rows, "object_category"),
        "policy_count": len(POLICIES),
        "candidate_policy_rows_upper_bound": len(ready_rows) * len(POLICIES),
        "trajectory_execution_plan_rows": len(by_episode) * len(POLICIES),
        "trajectory_cost_matrix_rows_upper_bound": sum(count * count for count in path_ready_counts),
        "min_path_ready_candidates_per_episode": min(path_ready_counts) if path_ready_counts else 0,
        "max_path_ready_candidates_per_episode": max(path_ready_counts) if path_ready_counts else 0,
        "mean_path_ready_candidates_per_episode": (
            sum(path_ready_counts) / len(path_ready_counts) if path_ready_counts else 0.0
        ),
        "scene_keys": sorted({str(row.get("scene_key")) for row in ready_rows}),
        "object_categories": sorted({str(row.get("object_category")) for row in ready_rows}),
    }


def build_denominator_rows(
    stats: dict[str, Any],
    m70_coverage: dict[str, Any],
    m73_coverage: dict[str, Any],
    m140_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "denominator_id": "m140_target_free_one_case_reference",
            "role": "completed_reference_not_scale_claim",
            "episode_rows": 1,
            "scene_count": m140_coverage.get("scene_count"),
            "policy_count": m140_coverage.get("policy_count"),
            "trajectory_execution_plan_rows": m140_coverage.get("trajectory_execution_plan_rows"),
            "trajectory_candidate_rows": m140_coverage.get("trajectory_candidate_rows"),
            "current_status": "executed",
            "claim_use": "scale_seed_only",
        },
        {
            "version": VERSION,
            "denominator_id": "full_val_mini_source_ready_confidence_preserving_scale",
            "role": "selected_first_scale",
            "episode_rows": stats["episode_rows"],
            "path_ready_episode_rows": stats["path_ready_episode_rows"],
            "scene_count": stats["scene_count"],
            "category_count": stats["category_count"],
            "candidate_rows": stats["candidate_rows"],
            "path_ready_candidate_rows": stats["path_ready_candidate_rows"],
            "candidate_policy_rows_upper_bound": stats["candidate_policy_rows_upper_bound"],
            "trajectory_cost_matrix_rows_upper_bound": stats["trajectory_cost_matrix_rows_upper_bound"],
            "trajectory_execution_plan_rows": stats["trajectory_execution_plan_rows"],
            "m70_proxy_primary_success_max": m70_coverage.get("primary_success_count_max"),
            "m73_prior_trajectory_SR": m73_coverage.get("trajectory_SR"),
            "m73_prior_trajectory_SPL_mean": m73_coverage.get("trajectory_SPL_mean"),
            "current_status": "needs_m143_materialization",
            "claim_use": "controlled_scale_eval_after_execution",
        },
        {
            "version": VERSION,
            "denominator_id": "heldout_scene_or_external_navigation_transfer",
            "role": "future_top_tier_requirement",
            "episode_rows": None,
            "path_ready_episode_rows": None,
            "scene_count": None,
            "category_count": None,
            "current_status": "not_materialized",
            "claim_use": "required_before_final_real_navigation_claim",
            "required_external_baselines": ["VLFM", "HM3D-OVON", "HOV-SG_or_equivalent_map_navigation"],
        },
    ]


def build_policy_freeze_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy_id in POLICIES:
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": policy_role(policy_id),
                "required_for_m143": True,
                "selected_method": policy_id == SELECTED_POLICY,
                "protected_baseline": policy_id in {PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE},
                "negative_control": policy_id in {PRIOR_REPAIR_BASELINE, PATH_COST_BASELINE},
                "confidence_band_abs": CONFIDENCE_BAND_ABS if policy_id == SELECTED_POLICY else None,
                "min_path_advantage_m": MIN_PATH_ADVANTAGE_M if policy_id == SELECTED_POLICY else None,
                "per_case_retuning_allowed": False,
                "uses_candidate_to_candidate_trajectory_cost": policy_id
                in {SELECTED_POLICY, HARD_VETO_ABLATION, PRIOR_REPAIR_BASELINE},
                "uses_source_to_candidate_path_cost": policy_id == PATH_COST_BASELINE,
                "uses_detector_confidence": policy_id
                in {SELECTED_POLICY, HARD_VETO_ABLATION, PRIMARY_BASELINE, CONFIDENCE_ONLY_BASELINE, PRIOR_REPAIR_BASELINE},
            }
        )
    return rows


def policy_role(policy_id: str) -> str:
    return {
        SELECTED_POLICY: "selected_confidence_preserving_method",
        HARD_VETO_ABLATION: "hard_feasibility_veto_ablation",
        PRIMARY_BASELINE: "protected_detector_confidence_baseline",
        CONFIDENCE_ONLY_BASELINE: "strong_confidence_only_baseline",
        PRIOR_REPAIR_BASELINE: "negative_prior_repair_baseline",
        PATH_COST_BASELINE: "negative_path_cost_baseline",
    }.get(policy_id, "unknown")


def build_input_guard_rows() -> list[dict[str, Any]]:
    return [
        guard(
            "detector_confidence",
            "allowed",
            "Open-vocabulary detector score is the protected naive baseline signal.",
        ),
        guard(
            "candidate_label_and_coordinates",
            "allowed",
            "Needed for query compatibility, navmesh snapping, and trajectory candidate construction.",
        ),
        guard(
            "source_pose_and_navmesh_reachability",
            "allowed",
            "Needed to separate source-ready rows from unreachable candidate/source failures.",
        ),
        guard(
            "candidate_to_candidate_trajectory_cost",
            "allowed_after_m143_materialization",
            "Allowed only as precomputed candidate graph cost, never from ObjectNav goal/viewpoint labels.",
        ),
        guard(
            "ObjectNav_goal_or_viewpoint",
            "blocked_for_policy",
            "May be used only after stopping for `SR` / `SPL` metric computation.",
        ),
        guard(
            "posthoc_target_distance_or_success_label",
            "blocked_for_policy",
            "Would make the scale-up an oracle fit rather than a deployable decision layer.",
        ),
        guard(
            "per_episode_confidence_band_tuning",
            "blocked_for_policy",
            "M142 freezes confidence band and min path advantage before any scale run.",
        ),
        guard(
            "dropping_hard_cases_after_metric",
            "blocked_for_reporting",
            "All exclusions must be source-readiness exclusions before policy evaluation.",
        ),
    ]


def guard(signal: str, status: str, rationale: str) -> dict[str, Any]:
    return {"version": VERSION, "signal": signal, "status": status, "rationale": rationale}


def build_metric_rows() -> list[dict[str, Any]]:
    return [
        metric("SR", "primary", "Success rate over fixed source-ready denominator."),
        metric("SPL", "primary", "Navigation efficiency; selected policy must not regress versus detector-confidence."),
        metric("CandidateVisits", "primary_diagnostic", "Search effort proxy inside executed trajectory."),
        metric("PathLengthM", "secondary", "Executed path length before success/failure."),
        metric("FailureType", "secondary", "Separate detector miss, source gap, unreachable candidate, and policy-order failure."),
        metric("FalseVetoRate", "guardrail", "Rate at which hard feasibility veto suppresses target-near or matched target candidates."),
        metric("ProxyToTrajectoryFlip", "guardrail", "Detects when proxy path ranking disagrees with executed trajectory outcome."),
        metric("SourceReadyCoverage", "guardrail", "Fraction of fixed denominator with path-ready candidates and runnable scenes."),
    ]


def metric(metric_id: str, role: str, rationale: str) -> dict[str, Any]:
    return {"version": VERSION, "metric_id": metric_id, "metric_role": role, "rationale": rationale}


def build_gate_rows(stats: dict[str, Any], m141_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    controlled_ready = bool(m141_coverage.get("controlled_scale_up_ready"))
    scale_episode_count = int(stats.get("path_ready_episode_rows", 0))
    return [
        gate(
            "m141_controlled_scale_seed",
            "pass" if controlled_ready else "fail",
            "M141 marks confidence-preserving repair as scale-up-worthy but not final claim evidence.",
            blocks_m143=True,
            blocks_final=False,
        ),
        gate(
            "policy_freeze_before_scale",
            "pass",
            "M142 freezes selected policy, confidence band 0.03, min path advantage 1.0, and comparison set.",
            blocks_m143=True,
            blocks_final=False,
        ),
        gate(
            "source_ready_scale_denominator",
            "pass" if scale_episode_count >= 30 else "warning",
            f"First scale denominator has {scale_episode_count} path-ready full-val-mini episodes.",
            blocks_m143=False,
            blocks_final=True,
        ),
        gate(
            "candidate_to_candidate_cost_missing",
            "warning",
            "Full-val-mini candidate-to-candidate trajectory cost matrix is not materialized yet.",
            blocks_m143=False,
            blocks_final=True,
        ),
        gate(
            "protected_baseline_required",
            "pass",
            "Detector-confidence and confidence-only baselines remain mandatory in the scale table.",
            blocks_m143=True,
            blocks_final=False,
        ),
        gate(
            "pass_condition_precommitted",
            "pass",
            "Scale result passes only if selected policy does not regress detector-confidence SR/SPL and improves visits or failure reduction.",
            blocks_m143=True,
            blocks_final=False,
        ),
        gate(
            "false_veto_audit_required",
            "warning",
            "M138 hard-veto count was high; M143/M144 must report false-veto and target-near veto rows.",
            blocks_m143=False,
            blocks_final=True,
        ),
        gate(
            "external_navigation_baseline_missing",
            "warning",
            "`VLFM`, `HM3D-OVON`, and `HOV-SG` style executable baselines are still future work.",
            blocks_m143=False,
            blocks_final=True,
        ),
        gate(
            "final_real_navigation_claim",
            "fail",
            "M142 is a contract and cannot support final `SR` / `SPL` claims.",
            blocks_m143=False,
            blocks_final=True,
        ),
    ]


def gate(
    gate_id: str,
    status: str,
    rationale: str,
    *,
    blocks_m143: bool,
    blocks_final: bool,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "gate_id": gate_id,
        "gate_status": status,
        "rationale": rationale,
        "blocks_m143_materialization": blocks_m143 and status == "fail",
        "blocks_final_real_navigation_claim": blocks_final and status in {"fail", "warning"},
    }


def build_pass_warning_fail_rows() -> list[dict[str, Any]]:
    return [
        outcome(
            "pass",
            "selected_policy_SR_and_SPL_not_lower_than_detector_confidence_and_candidate_visits_or_failure_rate_improves",
            "Supports continuing toward heldout/external-baseline validation, not final claim by itself.",
        ),
        outcome(
            "pass",
            "hard_veto_false_veto_rate_zero_or_explicitly_lower_than_baseline_failure_reduction",
            "Shows veto is a feasibility guard rather than target suppression.",
        ),
        outcome(
            "warning",
            "selected_policy_ties_detector_confidence_on_SR_SPL_without_visit_or_failure_gain",
            "May remain a diagnostic method-form result but not a strong contribution.",
        ),
        outcome(
            "warning",
            "source_ready_denominator_is_small_or_label_group_narrow",
            "Requires additional source materialization before paper claim.",
        ),
        outcome(
            "fail",
            "selected_policy_regresses_detector_confidence_SR_or_SPL",
            "Reject navigation-improvement claim or rewrite method principle.",
        ),
        outcome(
            "fail",
            "gain_depends_on_posthoc_target_distance_goal_viewpoint_or_per_case_threshold_tuning",
            "Reject as leakage or result fitting.",
        ),
        outcome(
            "fail",
            "hard_veto_suppresses_matched_target_or_near_target_candidates_at_meaningful_rate",
            "Reject hard-veto component or require redesigned guard.",
        ),
    ]


def outcome(status: str, condition: str, action: str) -> dict[str, Any]:
    return {"version": VERSION, "outcome_status": status, "condition": condition, "required_action": action}


def build_materialization_plan_rows(stats: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "unit_id": "E008-M143",
            "unit_name": NEXT_UNIT,
            "selected_next": True,
            "input_artifacts": [
                str(M68_DIR.relative_to(ROOT)),
                str(M69_DIR.relative_to(ROOT)),
                str(M141_DIR.relative_to(ROOT)),
            ],
            "expected_path_ready_episode_rows": stats["path_ready_episode_rows"],
            "expected_path_ready_candidate_rows": stats["path_ready_candidate_rows"],
            "expected_policy_count": len(POLICIES),
            "expected_candidate_policy_rows_upper_bound": stats["candidate_policy_rows_upper_bound"],
            "expected_trajectory_cost_matrix_rows_upper_bound": stats["trajectory_cost_matrix_rows_upper_bound"],
            "expected_execution_plan_rows": stats["trajectory_execution_plan_rows"],
            "requires_docker_or_habitat_pathfinder": True,
            "launch_long_job_now": False,
            "verification_command": (
                "python experiments/E008_real_navigation_benchmark/tools/"
                "run_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization.py --help"
            ),
        },
        {
            "version": VERSION,
            "unit_id": "E008-M144",
            "unit_name": "full-val-mini confidence-preserving trajectory execution contract / Docker preflight",
            "selected_next": False,
            "input_artifacts": ["E008-M143 outputs"],
            "requires_docker_or_habitat_pathfinder": True,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "unit_id": "E008-M145",
            "unit_name": "full-val-mini confidence-preserving trajectory execution",
            "selected_next": False,
            "input_artifacts": ["E008-M144 contract"],
            "requires_docker_or_habitat_pathfinder": True,
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        claim(
            "controlled_scaleup_contract",
            True,
            "M142 fixes the denominator, policy suite, input guards, metrics, and pass/fail gates before scale execution.",
        ),
        claim(
            "method_form_is_failure_derived",
            True,
            "M142 preserves the M130/M135 diagnosis that path/trajectory cost must not replace detector confidence.",
        ),
        claim(
            "full_val_mini_navigation_improvement",
            False,
            "Requires M143 materialization, M144 preflight, M145 execution, and M146 interpretation.",
        ),
        claim(
            "final_real_navigation_sr_spl",
            False,
            "Requires scale result, heldout transfer, external navigation/search baselines, and failure analysis.",
        ),
        claim(
            "human_intent_main_claim",
            False,
            "M142 does not redesign E006; human intent remains secondary under current evidence.",
        ),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        defense(
            "is_scale_up_forcing_the_hypothesis",
            "No. M142 freezes the policy and disconfirmation gates before materialization or execution.",
        ),
        defense(
            "why_reuse_full_val_mini",
            "It is the existing leakage-safe source-ready denominator with 30 episodes and 900 path-ready detector candidates.",
        ),
        defense(
            "why_detector_confidence_is_protected",
            "M130/M135 showed path/trajectory cost can hurt SPL when it replaces confidence; the method must preserve that baseline.",
        ),
        defense(
            "what_can_make_the_claim_fail",
            "Any SR/SPL regression, target/near-target false veto, hidden denominator filtering, or posthoc goal-distance tuning rejects the claim.",
        ),
    ]


def defense(issue_id: str, response: str) -> dict[str, Any]:
    return {"version": VERSION, "issue_id": issue_id, "reviewer_response": response}


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "bounded_one_case_diagnostic_only",
            "decision": "reject_as_next",
            "selected": False,
            "reason": "Top-tier direction needs scale beyond M140 one-case smoke.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "full_val_mini_confidence_preserving_controlled_scaleup",
            "decision": "select_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "Existing full-val-mini detector route is source-ready and leakage-safe, while M142 freezes the policy before scale.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "claim_final_navigation_now",
            "decision": "reject_now",
            "selected": False,
            "reason": "M142 is a contract; final claim requires execution, heldout transfer, and external baselines.",
            "launch_long_job_now": False,
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        cells: list[str] = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                value = fmt(value)
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(
    coverage: dict[str, Any],
    denominator_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M142 Confidence-Preserving Controlled Scale-Up Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M141 status: `{coverage['m141_status']}`.",
            f"- Selected policy: `{SELECTED_POLICY}`.",
            f"- First scale denominator: `full_val_mini_source_ready_confidence_preserving_scale`.",
            f"- Scale episode rows: {coverage['scale_episode_rows']}.",
            f"- Path-ready candidate rows: {coverage['scale_path_ready_candidate_rows']}.",
            f"- Expected policy candidate rows upper bound: {coverage['expected_candidate_policy_rows_upper_bound']}.",
            f"- Expected trajectory cost matrix rows upper bound: {coverage['expected_trajectory_cost_matrix_rows_upper_bound']}.",
            f"- Expected execution plan rows: {coverage['expected_execution_plan_rows']}.",
            f"- Launch long job now: {coverage['launch_long_job_now']}.",
            f"- Final real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Denominator Contract",
            "",
            markdown_table(
                denominator_rows,
                [
                    "denominator_id",
                    "role",
                    "episode_rows",
                    "path_ready_episode_rows",
                    "path_ready_candidate_rows",
                    "trajectory_execution_plan_rows",
                    "current_status",
                    "claim_use",
                ],
            ),
            "",
            "## Frozen Policy Suite",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "policy_role",
                    "selected_method",
                    "protected_baseline",
                    "negative_control",
                    "per_case_retuning_allowed",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m143_materialization", "blocks_final_real_navigation_claim", "rationale"]),
            "",
            "## Materialization Plan",
            "",
            markdown_table(
                materialization_rows,
                [
                    "unit_id",
                    "unit_name",
                    "selected_next",
                    "expected_path_ready_episode_rows",
                    "expected_policy_count",
                    "expected_execution_plan_rows",
                    "requires_docker_or_habitat_pathfinder",
                ],
            ),
            "",
            "## Route Decision",
            "",
            markdown_table(route_rows, ["route_id", "decision", "selected", "selected_next_unit", "reason"]),
            "",
            "## Claim Boundary",
            "",
            "- M142 is a contract and does not execute trajectories.",
            "- M142 prevents hypothesis fitting by freezing the method and failure gates before M143/M145.",
            "- Final navigation claims remain blocked until scale execution, heldout transfer, external baselines, and failure analysis pass.",
            "",
        ]
    )


def mirror_outputs(files: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    m68_coverage = read_json(M68_DIR / "coverage.json")
    m69_coverage = read_json(M69_DIR / "coverage.json")
    m70_coverage = read_json(M70_DIR / "coverage.json")
    m73_coverage = read_json(M73_DIR / "coverage.json")
    m138_coverage = read_json(M138_DIR / "coverage.json")
    m140_coverage = read_json(M140_DIR / "coverage.json")
    m141_coverage = read_json(M141_DIR / "coverage.json")
    nav_rows = read_jsonl(M68_DIR / "candidate_navmesh_validation_rows.jsonl")

    required_inputs = [
        M68_DIR / "coverage.json",
        M68_DIR / "candidate_navmesh_validation_rows.jsonl",
        M69_DIR / "coverage.json",
        M70_DIR / "coverage.json",
        M73_DIR / "coverage.json",
        M138_DIR / "coverage.json",
        M140_DIR / "coverage.json",
        M141_DIR / "coverage.json",
    ]
    missing_inputs = [str(path.relative_to(ROOT)) for path in required_inputs if not path.exists()]
    stats = build_episode_stats(nav_rows)
    denominator_rows = build_denominator_rows(stats, m70_coverage, m73_coverage, m140_coverage)
    policy_rows = build_policy_freeze_rows()
    input_guard_rows = build_input_guard_rows()
    metric_rows = build_metric_rows()
    gate_rows = build_gate_rows(stats, m141_coverage)
    pass_warning_fail_rows = build_pass_warning_fail_rows()
    materialization_rows = build_materialization_plan_rows(stats)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    gate_fail_count = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    gate_warning_count = sum(1 for row in gate_rows if row.get("gate_status") == "warning")
    m143_blocked = any(row.get("blocks_m143_materialization") for row in gate_rows)
    status = READY_STATUS if not missing_inputs and not m143_blocked else BLOCKED_STATUS
    label_counts = Counter(str(row.get("object_category")) for row in nav_rows if row.get("object_category"))

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "missing_inputs": missing_inputs,
        "m68_status": m68_coverage.get("status"),
        "m69_status": m69_coverage.get("status"),
        "m70_status": m70_coverage.get("status"),
        "m73_status": m73_coverage.get("status"),
        "m138_status": m138_coverage.get("status"),
        "m140_status": m140_coverage.get("status"),
        "m141_status": m141_coverage.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE,
        "confidence_band_abs": CONFIDENCE_BAND_ABS,
        "min_path_advantage_m": MIN_PATH_ADVANTAGE_M,
        "scale_denominator_id": "full_val_mini_source_ready_confidence_preserving_scale",
        "scale_episode_rows": stats["episode_rows"],
        "scale_path_ready_episode_rows": stats["path_ready_episode_rows"],
        "scale_candidate_rows": stats["candidate_rows"],
        "scale_path_ready_candidate_rows": stats["path_ready_candidate_rows"],
        "scale_scene_count": stats["scene_count"],
        "scale_category_count": stats["category_count"],
        "scale_object_categories": stats["object_categories"],
        "scale_label_counts": dict(sorted(label_counts.items())),
        "expected_policy_count": len(POLICIES),
        "expected_candidate_policy_rows_upper_bound": stats["candidate_policy_rows_upper_bound"],
        "expected_trajectory_cost_matrix_rows_upper_bound": stats["trajectory_cost_matrix_rows_upper_bound"],
        "expected_execution_plan_rows": stats["trajectory_execution_plan_rows"],
        "min_path_ready_candidates_per_episode": stats["min_path_ready_candidates_per_episode"],
        "max_path_ready_candidates_per_episode": stats["max_path_ready_candidates_per_episode"],
        "mean_path_ready_candidates_per_episode": stats["mean_path_ready_candidates_per_episode"],
        "m70_proxy_primary_success_max": m70_coverage.get("primary_success_count_max"),
        "m73_prior_trajectory_SR": m73_coverage.get("trajectory_SR"),
        "m73_prior_trajectory_SPL_mean": m73_coverage.get("trajectory_SPL_mean"),
        "m141_controlled_scale_up_ready": bool(m141_coverage.get("controlled_scale_up_ready")),
        "m141_final_real_navigation_ready": bool(m141_coverage.get("real_navigation_sr_spl_ready")),
        "gate_rows": len(gate_rows),
        "gate_fail_count": gate_fail_count,
        "gate_warning_count": gate_warning_count,
        "m143_materialization_ready": status == READY_STATUS,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "denominator_contract_rows.jsonl", denominator_rows)
    write_jsonl(ARTIFACT_DIR / "policy_freeze_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(ARTIFACT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "pass_warning_fail_gate_rows.jsonl", pass_warning_fail_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "m143_materialization_plan_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, denominator_rows, policy_rows, gate_rows, materialization_rows, route_rows),
        encoding="utf-8",
    )
    mirror_outputs(
        [
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "denominator_contract_rows.jsonl",
            ARTIFACT_DIR / "policy_freeze_rows.jsonl",
            ARTIFACT_DIR / "input_guard_rows.jsonl",
            ARTIFACT_DIR / "metric_contract_rows.jsonl",
            ARTIFACT_DIR / "pass_warning_fail_gate_rows.jsonl",
            ARTIFACT_DIR / "readiness_gate_rows.jsonl",
            ARTIFACT_DIR / "m143_materialization_plan_rows.jsonl",
            ARTIFACT_DIR / "claim_boundary_rows.jsonl",
            ARTIFACT_DIR / "reviewer_defense_rows.jsonl",
            ARTIFACT_DIR / "route_decision_rows.jsonl",
            ARTIFACT_DIR / "report.md",
        ]
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
