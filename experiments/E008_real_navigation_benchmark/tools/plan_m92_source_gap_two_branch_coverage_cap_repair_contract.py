#!/usr/bin/env python3
"""Fix the M92 two-branch source-gap repair contract after M91."""

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
M91_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M92_source_gap_two_branch_coverage_cap_repair_contract_v0"
)
M93_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)

VERSION = "e008_m92_source_gap_two_branch_coverage_cap_repair_contract_v0"
READY_STATUS = "e008_m92_source_gap_two_branch_coverage_cap_repair_contract_ready"
BLOCKED_STATUS = "e008_m92_source_gap_two_branch_coverage_cap_repair_contract_blocked"
NEXT_UNIT = "E008-M93 source-gap two-branch repair row materialization smoke"

M91_READY_STATUS = "e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_ready"
COVERAGE_FAILURE = "observation_or_detector_target_coverage_gap"
CAP_FAILURE = "localization_threshold_gap_with_low_confidence_cap_suppression"


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
    return "NA" if value_f is None else f"{value_f:.6f}"


def branch_id_for_failure(failure_type: str) -> str:
    if failure_type == COVERAGE_FAILURE:
        return "coverage_expansion_branch"
    if failure_type in {CAP_FAILURE, "cap_or_ranking_suppressed_primary_target_candidate"}:
        return "cap_threshold_rescue_branch"
    return "manual_review_branch"


def build_branch_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "repair_branch_contract",
            "branch_id": "coverage_expansion_branch",
            "branch_status": "selected_for_m93_materialization",
            "target_failure_types": [COVERAGE_FAILURE],
            "selected_route_id": "non_oracle_wide_shell_frontier_refresh_v2",
            "materialization_scope": "create additional policy-visible observation/source rows before any new detector run",
            "allowed_runtime_inputs": [
                "ObjectNav category text / detector prompt labels",
                "episode start pose",
                "HM3D scene and navmesh",
                "policy-visible source inventory from M84",
                "existing detector frame/source diagnostics",
                "source-to-candidate path/source diversity metadata",
            ],
            "blocked_runtime_inputs": [
                "ObjectNav eval goal position",
                "ObjectNav eval viewpoint positions",
                "candidate-to-eval distance",
                "target-near hit labels",
                "nearest target candidate rank",
            ],
            "m93_expected_output": "coverage_expansion_observation_plan_rows.jsonl",
            "m93_pass_condition": "at least one leakage-safe observation/source expansion route is materialized for every coverage-gap case",
            "expected_effect": "test whether absent pre-cap target coverage is a source-coverage problem before claiming policy failure",
            "claim_boundary": "This branch is a source-repair contract; it does not prove source-gap recovery until post-M93 render/detector/goal-eval gates pass.",
        },
        {
            "version": VERSION,
            "row_type": "repair_branch_contract",
            "branch_id": "cap_threshold_rescue_branch",
            "branch_status": "selected_for_m93_materialization",
            "target_failure_types": [
                CAP_FAILURE,
                "cap_or_ranking_suppressed_primary_target_candidate",
            ],
            "selected_route_id": "cap_stress_low_confidence_diversity_probe_v0",
            "materialization_scope": "create leakage-safe cap/ranking stress rows over policy-visible pre-cap candidate features",
            "allowed_runtime_inputs": [
                "ObjectNav category text / detector prompt labels",
                "pre-cap label/confidence rows",
                "2D box and depth-validity diagnostics",
                "frame/source id",
                "source diversity metadata",
                "source-to-candidate path cost",
                "fixed budget/cap configuration",
            ],
            "blocked_runtime_inputs": [
                "selection by ObjectNav eval goal distance",
                "selection by eval viewpoint distance",
                "selection by relaxed target-near hit label",
                "success proposal uid",
                "trajectory success label",
            ],
            "m93_expected_output": "cap_threshold_candidate_probe_rows.jsonl",
            "m93_pass_condition": "candidate rescue rows are ranked only by policy-visible confidence/depth/source/path features and keep budget-loss sentinels",
            "expected_effect": "test whether low-confidence relaxed candidates were suppressed by cap/threshold choices without leaking target labels into policy",
            "claim_boundary": "This branch is diagnostic until loss-safe budget evaluation shows it can surface candidates without hurting existing successes.",
        },
    ]


def build_case_assignment_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(case_rows, key=lambda item: str(item.get("scan_id"))):
        failure_type = str(row.get("dominant_failure_type"))
        branch_id = branch_id_for_failure(failure_type)
        if branch_id == "coverage_expansion_branch":
            selected_route = "non_oracle_wide_shell_frontier_refresh_v2"
            repair_question = "Can policy-visible observation/source expansion create target-near candidates absent from the pre-cap pool?"
            m93_materialization = "coverage_expansion_observation_plan"
        elif branch_id == "cap_threshold_rescue_branch":
            selected_route = "cap_stress_low_confidence_diversity_probe_v0"
            repair_question = "Can cap/threshold-aware ranking surface low-confidence relaxed candidates without using eval distances?"
            m93_materialization = "cap_threshold_candidate_probe"
        else:
            selected_route = "manual_source_gap_review_v0"
            repair_question = "Is the M91 failure type unsupported by the two selected branches?"
            m93_materialization = "manual_review"

        rows.append(
            {
                "version": VERSION,
                "row_type": "case_repair_assignment",
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "m91_dominant_failure_type": failure_type,
                "m91_dropped_stage": row.get("dropped_stage"),
                "m91_pre_cap_candidate_rows": row.get("pre_cap_candidate_rows"),
                "m91_final_candidate_rows": row.get("final_candidate_rows"),
                "m91_pre_cap_any_viewpoint_1p0_hits": row.get("pre_cap_any_viewpoint_1p0_hits"),
                "m91_pre_cap_any_viewpoint_1p5_hits": row.get("pre_cap_any_viewpoint_1p5_hits"),
                "m91_pre_cap_min_any_viewpoint_xz_m": row.get("pre_cap_min_any_viewpoint_xz_m"),
                "m91_best_pre_cap_confidence": row.get("best_pre_cap_confidence"),
                "m91_best_pre_cap_confidence_rank": row.get("best_pre_cap_confidence_rank"),
                "branch_id": branch_id,
                "selected_route_id": selected_route,
                "m93_materialization_target": m93_materialization,
                "repair_question": repair_question,
                "posthoc_diagnostic_selection_allowed": True,
                "runtime_policy_may_use_m91_eval_distances": False,
                "runtime_policy_may_use_m91_failure_type": False,
                "trajectory_promotion_ready": False,
                "claim_boundary": "M92 assigns repair branches from M91 diagnostics, but final policy/materialization cannot use eval goal/viewpoint distances or success labels.",
            }
        )
    return rows


def build_allowed_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "branch_scope": "both_branches",
            "input_group": "task_category_prompt",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": ["object_category", "detector prompt labels", "query label aliases"],
            "rationale": "The category text is the query, not the hidden ObjectNav goal location.",
        },
        {
            "version": VERSION,
            "branch_scope": "both_branches",
            "input_group": "hm3d_navigation_state",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": ["scene_key", "episode start pose", "navmesh", "scene glb", "source-to-candidate path cost"],
            "rationale": "Navigation state is available before evaluation and is required for source/readiness checks.",
        },
        {
            "version": VERSION,
            "branch_scope": "coverage_expansion_branch",
            "input_group": "policy_visible_source_inventory",
            "input_status": "allowed_for_materialization",
            "fields": ["M84 observation poses", "pose_role", "shell_radius_m", "route_id", "snap validation"],
            "rationale": "Coverage repair can expand from existing non-oracle source poses without target coordinates.",
        },
        {
            "version": VERSION,
            "branch_scope": "coverage_expansion_branch",
            "input_group": "detector_frame_diagnostics",
            "input_status": "allowed_for_materialization",
            "fields": ["frame_id", "raw prediction count", "written prediction count", "frame/source role"],
            "rationale": "Frame/source diagnostics can identify under-observed policy-visible regions without eval labels.",
        },
        {
            "version": VERSION,
            "branch_scope": "cap_threshold_rescue_branch",
            "input_group": "pre_cap_policy_visible_candidate_features",
            "input_status": "allowed_for_diagnostic_materialization",
            "fields": [
                "label_canonical",
                "confidence",
                "bbox_2d",
                "depth_valid_pixel_count",
                "frame_id",
                "observation_pose_id",
                "source-to-candidate path cost",
            ],
            "rationale": "Cap stress can use detector-visible features but not eval-nearest target labels.",
        },
        {
            "version": VERSION,
            "branch_scope": "cap_threshold_rescue_branch",
            "input_group": "fixed_budget_and_cap_configuration",
            "input_status": "allowed_for_diagnostic_materialization",
            "fields": ["per-label cap", "per-policy visit budget", "budget-loss sentinel id"],
            "rationale": "The branch tests whether cap/threshold choices suppressed useful candidates under a fixed budget.",
        },
        {
            "version": VERSION,
            "branch_scope": "m92_only",
            "input_group": "posthoc_m91_failure_taxonomy",
            "input_status": "allowed_for_branch_assignment_only",
            "fields": ["dominant_failure_type", "dropped_stage", "pre-cap hit counts"],
            "rationale": "Allowed to choose the next diagnostic branch, blocked as a deployable runtime trigger.",
        },
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "input_group": "objectnav_eval_goal_geometry",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["eval_goal_position", "eval_goal_object_id", "candidate_to_eval_goal_xz_m"],
            "rationale": "Goal geometry is evaluation-only and cannot choose source poses or rank candidates.",
        },
        {
            "version": VERSION,
            "input_group": "objectnav_eval_viewpoint_geometry",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["eval viewpoint positions", "candidate_to_nearest_eval_viewpoint_xz_m"],
            "rationale": "Viewpoint geometry is used only after fixed rows exist to score proxy success.",
        },
        {
            "version": VERSION,
            "input_group": "target_near_hit_labels",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["hit_any_viewpoint_xz_1p0", "hit_any_viewpoint_xz_1p5", "hit_goal_xz_1p0"],
            "rationale": "These labels are post-hoc metrics, not ranking features.",
        },
        {
            "version": VERSION,
            "input_group": "nearest_target_candidate_identity",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["nearest_target_rank", "pre_cap_candidate_pool_uid selected by eval distance"],
            "rationale": "Nearest-target rows can diagnose suppression but cannot seed the repair policy.",
        },
        {
            "version": VERSION,
            "input_group": "success_or_failure_labels",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["proxy success", "trajectory success", "SR", "SPL", "source-gap recovered"],
            "rationale": "Success labels are joined only after fixed rows are evaluated.",
        },
        {
            "version": VERSION,
            "input_group": "m91_failure_type_runtime_trigger",
            "input_status": "blocked_for_final_policy",
            "fields": ["dominant_failure_type", "dropped_stage"],
            "rationale": "M91 labels are allowed for diagnostic branch selection, not deployable online switching.",
        },
        {
            "version": VERSION,
            "input_group": "future_repair_outputs",
            "input_status": "blocked_for_m93_planning",
            "fields": ["future render success", "future detector rows", "future goal-eval rows"],
            "rationale": "M93 must materialize rows before future jobs exist.",
        },
        {
            "version": VERSION,
            "input_group": "human_intent_as_main_signal",
            "input_status": "blocked_for_m92_claim",
            "fields": ["natural-language intent parser output", "preference label", "human feedback success"],
            "rationale": "E008-M92 does not run a human-intent ablation; task context remains a secondary condition.",
        },
    ]


def build_materialization_contract_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    coverage_cases = [row for row in case_rows if row.get("branch_id") == "coverage_expansion_branch"]
    cap_cases = [row for row in case_rows if row.get("branch_id") == "cap_threshold_rescue_branch"]
    return [
        {
            "version": VERSION,
            "contract_id": "m93_case_repair_assignment",
            "output_file": str(M93_ARTIFACT_DIR / "case_repair_assignment_rows.jsonl"),
            "expected_rows_min": len(case_rows),
            "expected_rows_max": len(case_rows),
            "required_invariant": "same_adapter_episode_ids_as_m92_case_repair_assignment_rows",
        },
        {
            "version": VERSION,
            "contract_id": "m93_branch_contract_copy",
            "output_file": str(M93_ARTIFACT_DIR / "repair_branch_contract_rows.jsonl"),
            "expected_rows_min": 2,
            "expected_rows_max": 2,
            "required_invariant": "coverage_expansion_branch_and_cap_threshold_rescue_branch_present",
        },
        {
            "version": VERSION,
            "contract_id": "m93_coverage_expansion_observation_plan",
            "output_file": str(M93_ARTIFACT_DIR / "coverage_expansion_observation_plan_rows.jsonl"),
            "expected_rows_min": len(coverage_cases) * 12,
            "expected_rows_max": len(coverage_cases) * 192,
            "required_invariant": "no_row_contains_objectnav_eval_goal_or_viewpoint_fields",
        },
        {
            "version": VERSION,
            "contract_id": "m93_cap_threshold_candidate_probe",
            "output_file": str(M93_ARTIFACT_DIR / "cap_threshold_candidate_probe_rows.jsonl"),
            "expected_rows_min": len(cap_cases) * 24,
            "expected_rows_max": len(cap_cases) * 512,
            "required_invariant": "candidate_order_uses_policy_visible_features_not_eval_distance",
        },
        {
            "version": VERSION,
            "contract_id": "m93_budget_loss_sentinel",
            "output_file": str(M93_ARTIFACT_DIR / "budget_loss_sentinel_rows.jsonl"),
            "expected_rows_min": len(case_rows),
            "expected_rows_max": len(case_rows) * 8,
            "required_invariant": "cap_rescue_rows_must_not_replace_detector_confidence_topk_without_explicit_loss_check",
        },
        {
            "version": VERSION,
            "contract_id": "m93_next_long_job_ledger",
            "output_file": str(M93_ARTIFACT_DIR / "long_job_command_rows.jsonl"),
            "expected_rows_min": 0,
            "expected_rows_max": 2,
            "required_invariant": "M93_may_record_future_render_detector_commands_but_must_not_launch_them",
        },
    ]


def build_evaluation_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "stage_id": "E008-M93",
            "branch_id": "coverage_expansion_branch",
            "required_check": "materialize leakage-safe observation/source expansion rows",
            "pass_condition": "coverage-gap cases have planned source poses and render/detector manifests without eval-goal fields",
            "claim_if_pass": "coverage repair is launch-ready, not recovered",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M93",
            "branch_id": "cap_threshold_rescue_branch",
            "required_check": "materialize cap/threshold candidate probe rows",
            "pass_condition": "probe rows are ranked by confidence/depth/source/path features and carry budget-loss sentinels",
            "claim_if_pass": "cap-suppression diagnosis is replay-ready, not a deployable rescue policy",
        },
        {
            "version": VERSION,
            "stage_id": "post-M93 render/detector gate",
            "branch_id": "coverage_expansion_branch",
            "required_check": "render frames and rerun detector only after M93 fixes rows and long-job ledger",
            "pass_condition": "new detector candidates produce primary or relaxed target-near coverage without source-ready regressions",
            "claim_if_pass": "coverage expansion can be evaluated for source-gap recovery",
        },
        {
            "version": VERSION,
            "stage_id": "post-M93 goal-eval gate",
            "branch_id": "cap_threshold_rescue_branch",
            "required_check": "evaluate cap-rescue rows with fixed budget and loss sentinels",
            "pass_condition": "low-confidence rescue improves target-near proxy while preserving existing successes",
            "claim_if_pass": "cap/threshold rescue is a candidate repair, still before trajectory promotion",
        },
        {
            "version": VERSION,
            "stage_id": "trajectory_promotion_gate",
            "branch_id": "both_branches",
            "required_check": "run Habitat trajectories only after leakage-safe proxy recovery and loss-safety pass",
            "pass_condition": "source-gap recovery and no budget regression hold before Docker trajectory execution",
            "claim_if_pass": "trajectory execution is justified; final navigation claim still needs heldout/external baselines",
        },
    ]


def build_long_job_policy_rows(generated_at: str) -> list[dict[str, Any]]:
    stamp = generated_at.replace("-", "").replace(":", "").replace("T", "_")
    return [
        {
            "version": VERSION,
            "job_id": "E008-post-M93-coverage-render",
            "branch_id": "coverage_expansion_branch",
            "job_type": "coverage_expansion_render_frame_staging",
            "job_status": "deferred_until_m93_materialization",
            "launch_now": False,
            "tmux_session": "e008_m93_coverage_render",
            "working_directory": str(ROOT),
            "output_path": str(M93_DATA_DIR),
            "log_path_template": str(ROOT / "logs" / f"{stamp}_e008_m93_coverage_render.log"),
            "expected_files": [
                "coverage_expansion_observation_plan_rows.jsonl",
                "coverage_expansion_render_plan_rows.jsonl",
                "coverage_expansion_detector_manifest_rows.jsonl",
            ],
            "verification_command_template": "python experiments/E008_real_navigation_benchmark/tools/run_m93_source_gap_two_branch_repair_row_materialization_smoke.py --verify-only",
            "rationale": "M92 is a contract; any render job waits until M93 writes exact leakage-safe rows.",
        },
        {
            "version": VERSION,
            "job_id": "E008-post-M93-coverage-detector",
            "branch_id": "coverage_expansion_branch",
            "job_type": "coverage_expansion_open_vocabulary_detector",
            "job_status": "deferred_until_render_verification",
            "launch_now": False,
            "tmux_session": "e008_m93_coverage_detector",
            "working_directory": str(ROOT),
            "output_path": str(M93_ARTIFACT_DIR),
            "log_path_template": str(ROOT / "logs" / f"{stamp}_e008_m93_coverage_detector.log"),
            "expected_files": ["coverage.json", "pre_cap_candidate_pool.jsonl", "real_proposals.jsonl"],
            "verification_command_template": "verify future detector candidate-source output with row counts and schema checks",
            "rationale": "Detector inference is not launched until coverage branch render inputs are verified.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_two_branch_repair_contract",
            "supported": True,
            "claim_boundary": "M92 supports the claim that the source-gap failures require separate coverage-expansion and cap/threshold-rescue repair routes.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M92 does not materialize repaired rows, rerun detector inference, or evaluate source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "M92 uses M91 post-hoc diagnostics for branch assignment; it does not define a deployable online trigger.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M92 does not execute Habitat trajectories or report real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M92 only fixes the next repair contract; robustness needs repaired detector outputs across heldout cases and external baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M92 does not add human-intent ablations; structured task context remains a secondary condition.",
        },
    ]


def build_readiness_gate_rows(
    m91_coverage: dict[str, Any],
    branch_rows: list[dict[str, Any]],
    assignment_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    branch_ids = {str(row.get("branch_id")) for row in branch_rows}
    assigned_branch_ids = {str(row.get("branch_id")) for row in assignment_rows}
    failure_counts = Counter(str(row.get("m91_dominant_failure_type")) for row in assignment_rows)
    return [
        {
            "version": VERSION,
            "gate_id": "m91_ready_and_selected_m92",
            "gate_status": "pass"
            if m91_coverage.get("status") == M91_READY_STATUS
            and str(m91_coverage.get("selected_next_unit", "")).startswith("E008-M92")
            else "fail",
            "rationale": "M92 starts only after M91 diagnoses source-gap target coverage and selects two-branch repair.",
        },
        {
            "version": VERSION,
            "gate_id": "two_failure_types_present",
            "gate_status": "pass" if failure_counts.get(COVERAGE_FAILURE, 0) and failure_counts.get(CAP_FAILURE, 0) else "fail",
            "rationale": "Two-branch repair is justified only if coverage and cap/threshold failures are both present.",
        },
        {
            "version": VERSION,
            "gate_id": "branch_contracts_fixed",
            "gate_status": "pass"
            if {"coverage_expansion_branch", "cap_threshold_rescue_branch"}.issubset(branch_ids)
            else "fail",
            "rationale": "Both repair branches need explicit route, allowed inputs, and expected outputs.",
        },
        {
            "version": VERSION,
            "gate_id": "all_cases_assigned_to_supported_branch",
            "gate_status": "pass" if assigned_branch_ids <= branch_ids and len(assignment_rows) == 2 else "fail",
            "rationale": "Each M91 source-gap case must map to one M92 branch.",
        },
        {
            "version": VERSION,
            "gate_id": "input_boundary_fixed",
            "gate_status": "pass" if len(allowed_rows) >= 6 and len(blocked_rows) >= 8 else "fail",
            "rationale": "Allowed/blocked inputs must be explicit before M93 materialization.",
        },
        {
            "version": VERSION,
            "gate_id": "m93_output_contract_fixed",
            "gate_status": "pass" if len(materialization_rows) >= 5 else "fail",
            "rationale": "M93 needs concrete output files, row-count guards, and invariants.",
        },
        {
            "version": VERSION,
            "gate_id": "no_long_job_launched_in_m92",
            "gate_status": "pass",
            "rationale": "M92 is a planning/contract artifact only.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_promotion_blocked",
            "gate_status": "pass",
            "rationale": "M91 primary recovery is 0/2; M92 must not promote to trajectory execution.",
        },
    ]


def build_route_decision_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready = all(row.get("gate_status") in {"pass", "warning"} for row in readiness_rows)
    return [
        {
            "version": VERSION,
            "decision": "source_gap_two_branch_contract_ready_select_m93"
            if ready
            else "source_gap_two_branch_contract_blocked",
            "selected_next_unit": NEXT_UNIT if ready else "manual M92 input-boundary repair",
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "direct_trajectory_promotion_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "reason": (
                "M92 fixes separate coverage-expansion and cap/threshold-rescue contracts; "
                "M93 should materialize rows before any long job or trajectory execution."
            ),
        }
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "rationale": "M93 should write branch-specific repair rows, budget-loss sentinels, and future long-job ledgers without launching render/detector jobs.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    branch_rows: list[dict[str, Any]],
    assignment_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> str:
    branch_lines = [
        f"| {row['branch_id']} | {', '.join(row['target_failure_types'])} | {row['selected_route_id']} | {row['m93_expected_output']} |"
        for row in branch_rows
    ]
    assignment_lines = [
        "| {scan_id} | {object_category} | {m91_dominant_failure_type} | {branch_id} | {m91_pre_cap_any_viewpoint_1p0_hits} / {m91_pre_cap_any_viewpoint_1p5_hits} | {m91_pre_cap_min_any_viewpoint_xz_m} | {m91_best_pre_cap_confidence_rank} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m91_dominant_failure_type=row.get("m91_dominant_failure_type"),
            branch_id=row.get("branch_id"),
            m91_pre_cap_any_viewpoint_1p0_hits=row.get("m91_pre_cap_any_viewpoint_1p0_hits"),
            m91_pre_cap_any_viewpoint_1p5_hits=row.get("m91_pre_cap_any_viewpoint_1p5_hits"),
            m91_pre_cap_min_any_viewpoint_xz_m=fmt(row.get("m91_pre_cap_min_any_viewpoint_xz_m")),
            m91_best_pre_cap_confidence_rank=row.get("m91_best_pre_cap_confidence_rank"),
        )
        for row in assignment_rows
    ]
    gate_lines = [
        f"| {row['gate_id']} | {row['gate_status']} | {row['rationale']} |" for row in readiness_rows
    ]
    return f"""# E008-M92 Source-Gap Two-Branch Coverage/Cap Repair Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M91 status: `{coverage['m91_status']}`.
- Source-gap cases: {coverage['source_gap_case_rows']}.
- Repair branch rows: {coverage['repair_branch_rows']}.
- Coverage-expansion branch cases: {coverage['coverage_expansion_branch_case_rows']}.
- Cap/threshold-rescue branch cases: {coverage['cap_threshold_rescue_branch_case_rows']}.
- Allowed input rows: {coverage['allowed_input_rows']}.
- Blocked input rows: {coverage['blocked_input_rows']}.
- M93 materialization contract rows: {coverage['materialization_contract_rows']}.
- Long job launched: {coverage['launch_long_job_now']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Branch Contract

| branch | target failure type | route | M93 expected output |
| --- | --- | --- | --- |
{chr(10).join(branch_lines)}

## Case Assignment

| scan_id | category | M91 failure | M92 branch | pre-cap 1.0 / 1.5 hits | pre-cap nearest any-vp XZ m | best confidence rank |
| --- | --- | --- | --- | ---: | ---: | ---: |
{chr(10).join(assignment_lines)}

## Readiness Gates

| gate | status | rationale |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Decision

- M92 does not launch render, detector, or trajectory jobs.
- The sofa case is assigned to `coverage_expansion_branch` because M91 found no pre-cap target-near candidate.
- The toilet case is assigned to `cap_threshold_rescue_branch` because M91 found relaxed low-confidence candidates suppressed before final candidate rows.
- Selected route: `E008-M93 source-gap two-branch repair row materialization smoke`.

## Claim Boundary

- M92 supports only a two-branch repair contract.
- M92 does not claim source-gap recovery, deployable search policy, final real RGB-D/open-vocabulary robustness, human-intent main contribution, or real navigation `SR` / `SPL`.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m91_coverage = read_json(M91_DIR / "coverage.json")
    m91_case_rows = read_jsonl(M91_DIR / "source_gap_failure_diagnosis_rows.jsonl")

    branch_rows = build_branch_contract_rows()
    assignment_rows = build_case_assignment_rows(m91_case_rows)
    allowed_rows = build_allowed_input_rows()
    blocked_rows = build_blocked_input_rows()
    materialization_rows = build_materialization_contract_rows(assignment_rows)
    evaluation_rows = build_evaluation_contract_rows()
    generated_at = datetime.now().isoformat(timespec="seconds")
    long_job_rows = build_long_job_policy_rows(generated_at)
    claim_rows = build_claim_boundary_rows()
    readiness_rows = build_readiness_gate_rows(
        m91_coverage,
        branch_rows,
        assignment_rows,
        allowed_rows,
        blocked_rows,
        materialization_rows,
    )
    route_rows = build_route_decision_rows(readiness_rows)
    next_rows = build_next_action_rows()

    failure_counts = Counter(str(row.get("m91_dominant_failure_type")) for row in assignment_rows)
    branch_counts = Counter(str(row.get("branch_id")) for row in assignment_rows)
    input_ready = (
        m91_coverage.get("status") == M91_READY_STATUS
        and len(branch_rows) == 2
        and len(assignment_rows) == int(m91_coverage.get("source_gap_case_rows") or 0) == 2
        and branch_counts.get("coverage_expansion_branch", 0) == 1
        and branch_counts.get("cap_threshold_rescue_branch", 0) == 1
        and all(row.get("gate_status") in {"pass", "warning"} for row in readiness_rows)
    )
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m91_status": m91_coverage.get("status"),
        "source_gap_case_rows": len(assignment_rows),
        "m91_pre_cap_candidate_rows": m91_coverage.get("pre_cap_candidate_rows"),
        "m91_final_candidate_rows": m91_coverage.get("final_candidate_rows"),
        "m91_cases_with_pre_cap_primary_hit": m91_coverage.get("cases_with_pre_cap_primary_hit"),
        "m91_cases_with_pre_cap_relaxed_hit": m91_coverage.get("cases_with_pre_cap_relaxed_hit"),
        "m91_cases_with_final_primary_hit": m91_coverage.get("cases_with_final_primary_hit"),
        "m91_failure_type_counts": dict(sorted(failure_counts.items())),
        "repair_branch_rows": len(branch_rows),
        "coverage_expansion_branch_case_rows": branch_counts.get("coverage_expansion_branch", 0),
        "cap_threshold_rescue_branch_case_rows": branch_counts.get("cap_threshold_rescue_branch", 0),
        "allowed_input_rows": len(allowed_rows),
        "blocked_input_rows": len(blocked_rows),
        "materialization_contract_rows": len(materialization_rows),
        "evaluation_contract_rows": len(evaluation_rows),
        "long_job_policy_rows": len(long_job_rows),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if row.get("gate_status") == "fail"),
        "m93_materialization_ready": input_ready,
        "launch_long_job_now": False,
        "direct_trajectory_promotion_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    outputs: dict[str, Any] = {
        "coverage.json": coverage,
        "repair_branch_contract_rows.jsonl": branch_rows,
        "case_repair_assignment_rows.jsonl": assignment_rows,
        "allowed_input_rows.jsonl": allowed_rows,
        "blocked_input_rows.jsonl": blocked_rows,
        "materialization_contract_rows.jsonl": materialization_rows,
        "evaluation_contract_rows.jsonl": evaluation_rows,
        "long_job_policy_rows.jsonl": long_job_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_rows,
    }
    for name, payload in outputs.items():
        if name.endswith(".json"):
            write_json(ARTIFACT_DIR / name, payload)
            write_json(DATA_OUT_DIR / name, payload)
        else:
            assert isinstance(payload, list)
            write_jsonl(ARTIFACT_DIR / name, payload)
            write_jsonl(DATA_OUT_DIR / name, payload)

    report = build_report(coverage, branch_rows, assignment_rows, readiness_rows)
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
