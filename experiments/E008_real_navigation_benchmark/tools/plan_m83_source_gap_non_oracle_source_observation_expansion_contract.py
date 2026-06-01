#!/usr/bin/env python3
"""Fix the M83 non-oracle source/observation expansion contract."""

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
M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M65_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
M80_DIR = EXP_ROOT / "artifacts" / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
M82_DIR = EXP_ROOT / "artifacts" / "E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M83_source_gap_non_oracle_source_observation_expansion_contract_v0"
)

VERSION = "e008_m83_source_gap_non_oracle_source_observation_expansion_contract_v0"
READY_STATUS = "e008_m83_source_gap_non_oracle_source_observation_expansion_contract_ready"
BLOCKED_STATUS = "e008_m83_source_gap_non_oracle_source_observation_expansion_contract_blocked"
NEXT_UNIT = "E008-M84 full-val-mini source-gap non-oracle source/observation expansion materialization smoke"

RENDER_JOB_ID = "E008-M85"
DETECTOR_JOB_ID = "E008-M86"
M84_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M84_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)


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


def group_by_episode(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("adapter_episode_id"))].append(row)
    return grouped


def labels_for_category(prompt_set: dict[str, Any], category: str) -> list[str]:
    labels: list[str] = []
    for label_row in prompt_set.get("labels", []):
        categories = [str(item) for item in label_row.get("hm3d_objectnav_categories", [])]
        if category in categories and bool(label_row.get("detector_prompt_enabled", True)):
            canonical = str(label_row.get("label_canonical"))
            if canonical and canonical not in labels:
                labels.append(canonical)
    return labels or [category]


def selected_long_actions(plan_rows: list[dict[str, Any]]) -> list[str]:
    out = []
    for row in plan_rows:
        action = str(row.get("action_id"))
        if bool(row.get("requires_long_job_later")) and action not in out:
            out.append(action)
    return sorted(out)


def build_case_rows(
    m82_source_gap_rows: list[dict[str, Any]],
    source_plan_rows: list[dict[str, Any]],
    observation_pose_rows: list[dict[str, Any]],
    render_plan_rows: list[dict[str, Any]],
    candidate_visit_rows: list[dict[str, Any]],
    prompt_set: dict[str, Any],
) -> list[dict[str, Any]]:
    plans_by_episode = group_by_episode(source_plan_rows)
    observations_by_episode = group_by_episode(observation_pose_rows)
    render_by_episode = group_by_episode(render_plan_rows)
    candidates_by_episode = group_by_episode(candidate_visit_rows)

    rows: list[dict[str, Any]] = []
    for source_gap in sorted(m82_source_gap_rows, key=lambda row: str(row.get("adapter_episode_id"))):
        episode = str(source_gap.get("adapter_episode_id"))
        plans = plans_by_episode.get(episode, [])
        observations = observations_by_episode.get(episode, [])
        render_rows = render_by_episode.get(episode, [])
        candidates = candidates_by_episode.get(episode, [])
        frame_roles = Counter(str(row.get("frame_pose_role") or row.get("pose_role") or "unknown") for row in candidates)
        shell_radii = sorted(
            {
                finite_float(row.get("shell_radius_m"))
                for row in [*observations, *candidates]
                if finite_float(row.get("shell_radius_m")) is not None
            }
        )
        object_category = str(source_gap.get("object_category"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_gap_contract_case",
                "adapter_episode_id": episode,
                "scan_id": source_gap.get("scan_id"),
                "scene_key": source_gap.get("scene_key"),
                "object_category": object_category,
                "target_labels": labels_for_category(prompt_set, object_category),
                "existing_append_recovered_primary_proxy": bool(
                    source_gap.get("existing_append_recovered_primary_proxy")
                ),
                "source_gap_resolved_before_m83": bool(source_gap.get("source_gap_resolved")),
                "m80_source_plan_rows": len(plans),
                "m64_observation_pose_rows": len(observations),
                "m64_render_frame_rows": len(render_rows),
                "m80_candidate_visit_rows": len(candidates),
                "m80_path_ready_candidate_rows": sum(1 for row in candidates if bool(row.get("path_ready"))),
                "candidate_frame_role_counts": dict(frame_roles),
                "available_shell_radii_m": shell_radii,
                "selected_long_job_action_ids": selected_long_actions(plans),
                "required_expansion": "new_non_oracle_observation_source_evidence",
                "selected_contract_routes": [
                    "non_oracle_local_shell_multiview_refresh_v1",
                    "non_oracle_high_path_source_refresh_v1",
                ],
                "contract_selection_uses_posthoc_eval": True,
                "final_policy_may_use_source_gap_label": False,
                "claim_boundary": (
                    "M83 selects source-gap cases for diagnostic expansion; final policy cannot use "
                    "source-gap labels, ObjectNav goals, or success labels as runtime inputs."
                ),
            }
        )
    return rows


def build_route_rows(
    case_rows: list[dict[str, Any]],
    source_plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plans_by_episode = group_by_episode(source_plan_rows)
    rows: list[dict[str, Any]] = []
    for case in case_rows:
        episode = str(case.get("adapter_episode_id"))
        for plan in sorted(plans_by_episode.get(episode, []), key=lambda row: str(row.get("action_id"))):
            action_id = str(plan.get("action_id"))
            if action_id == "existing_append_probe_audit_v0":
                route_id = "existing_append_probe_audit_v0"
                route_status = "completed_insufficient"
                materialize_in_m84 = False
                expected_effect = "Already evaluated by M81/M82; did not recover source-gap rows."
            elif action_id == "non_oracle_local_shell_multiview_refresh_v0":
                route_id = "non_oracle_local_shell_multiview_refresh_v1"
                route_status = "selected_primary"
                materialize_in_m84 = True
                expected_effect = "Densify policy-visible local-shell poses and multiview frames without using ObjectNav goal/viewpoint fields."
            elif action_id == "non_oracle_high_path_source_refresh_v0":
                route_id = "non_oracle_high_path_source_refresh_v1"
                route_status = "selected_secondary"
                materialize_in_m84 = True
                expected_effect = "Refresh views from policy-visible high-path/candidate-source inventory without using success labels."
            else:
                route_id = action_id
                route_status = "defer"
                materialize_in_m84 = False
                expected_effect = "No M83 contract route assigned."
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "source_observation_expansion_route",
                    "adapter_episode_id": episode,
                    "scan_id": case.get("scan_id"),
                    "scene_key": case.get("scene_key"),
                    "object_category": case.get("object_category"),
                    "m80_action_id": action_id,
                    "route_id": route_id,
                    "route_status": route_status,
                    "materialize_in_m84": materialize_in_m84,
                    "requires_long_job_after_m84": bool(plan.get("requires_long_job_later")) and materialize_in_m84,
                    "policy_input_allowed_for_final_policy": False,
                    "contract_input_allowed_for_diagnostic_expansion": True,
                    "expected_effect": expected_effect,
                    "claim_boundary": (
                        "Route rows define diagnostic source expansion; they do not prove target recovery "
                        "or final deployable policy behavior."
                    ),
                }
            )
    return rows


def build_allowed_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "input_group": "hm3d_episode_start_navmesh_scene",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": ["episode_start_pose", "navmesh", "scene_glb", "scene_dataset_config"],
            "rationale": "Available before evaluation and needed to place non-oracle observation sources.",
        },
        {
            "version": VERSION,
            "input_group": "policy_visible_observation_inventory",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": ["observation_pose_id", "pose_role", "shell_radius_m", "frame_id", "snap_validation_status"],
            "rationale": "Existing non-oracle observation sources can seed denser source coverage.",
        },
        {
            "version": VERSION,
            "input_group": "detector_candidate_source_metadata",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": [
                "label_canonical",
                "confidence",
                "candidate_rank",
                "candidate_source_role",
                "frame_pose_role",
                "source_to_candidate_path_cost_m",
                "path_ready",
            ],
            "rationale": "Detector and path metadata are available before eval labels and can guide source refresh.",
        },
        {
            "version": VERSION,
            "input_group": "task_category_prompt_labels",
            "input_status": "allowed_for_policy_and_materialization",
            "fields": ["object_category", "detector prompt labels"],
            "rationale": "ObjectNav category text is the query label, not the hidden goal location.",
        },
        {
            "version": VERSION,
            "input_group": "posthoc_source_gap_case_selection",
            "input_status": "allowed_for_diagnostic_unit_selection_only",
            "fields": ["M82 source-gap decision rows", "M81 append-gain diagnosis"],
            "rationale": "Allowed to choose a failure-analysis unit; blocked as a runtime trigger for final policy.",
        },
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "input_group": "objectnav_eval_geometry",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["ObjectNav goal position", "ObjectNav viewpoint position", "candidate_to_eval_goal_*"],
            "rationale": "Goal/viewpoint geometry is evaluation-only and cannot define source poses.",
        },
        {
            "version": VERSION,
            "input_group": "success_or_failure_labels",
            "input_status": "blocked_for_policy_and_materialization",
            "fields": ["primary_eval_hit", "trajectory_success", "SR", "SPL", "success_proposal_uid"],
            "rationale": "Success labels can be joined only after fixed candidate/source rows are materialized.",
        },
        {
            "version": VERSION,
            "input_group": "posthoc_failure_taxonomy_as_runtime_trigger",
            "input_status": "blocked_for_final_policy",
            "fields": ["source_gap label", "M71 failure class", "M78 guarded_loss identity"],
            "rationale": "These are reviewer-facing diagnostics, not deployable runtime conditions.",
        },
        {
            "version": VERSION,
            "input_group": "future_detector_outputs",
            "input_status": "blocked_for_m84_planning",
            "fields": ["M85/M86 proposal rows", "future matching rows"],
            "rationale": "M84 must fix render/detector inputs before any new detector output exists.",
        },
    ]


def build_materialization_contract_rows(case_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_routes = [row for row in route_rows if bool(row.get("materialize_in_m84"))]
    case_count = len(case_rows)
    route_count = len(selected_routes)
    return [
        {
            "version": VERSION,
            "contract_id": "m84_case_filter",
            "output_file": str(M84_ARTIFACT_DIR / "source_gap_case_rows.jsonl"),
            "expected_rows_min": case_count,
            "expected_rows_max": case_count,
            "required_invariant": "same_adapter_episode_ids_as_m83_source_gap_contract_case_rows",
        },
        {
            "version": VERSION,
            "contract_id": "m84_observation_pose_plan",
            "output_file": str(M84_ARTIFACT_DIR / "source_gap_observation_pose_plan_rows.jsonl"),
            "expected_rows_min": case_count * 8,
            "expected_rows_max": case_count * 96,
            "required_invariant": "no_pose_uses_objectnav_eval_goal_or_viewpoint",
        },
        {
            "version": VERSION,
            "contract_id": "m84_render_plan",
            "output_file": str(M84_ARTIFACT_DIR / "source_gap_render_plan_rows.jsonl"),
            "expected_rows_min": case_count * 32,
            "expected_rows_max": case_count * 384,
            "required_invariant": "all_expected_paths_under_research2_local_dataset_hm3d_navigation_bridge",
        },
        {
            "version": VERSION,
            "contract_id": "m84_detector_manifest",
            "output_file": str(M84_ARTIFACT_DIR / "source_gap_detector_manifest_rows.jsonl"),
            "expected_rows_min": case_count,
            "expected_rows_max": case_count,
            "required_invariant": "manifest_uses_category_prompt_labels_only",
        },
        {
            "version": VERSION,
            "contract_id": "m84_route_materialization",
            "output_file": str(M84_ARTIFACT_DIR / "source_gap_expansion_route_materialization_rows.jsonl"),
            "expected_rows_min": route_count,
            "expected_rows_max": route_count,
            "required_invariant": "selected_m83_routes_are_materialized_or_explicitly_blocked_with_reason",
        },
        {
            "version": VERSION,
            "contract_id": "m84_long_job_ledger",
            "output_file": str(M84_ARTIFACT_DIR / "long_job_command_rows.jsonl"),
            "expected_rows_min": 2,
            "expected_rows_max": 2,
            "required_invariant": "render_and_detector_commands_record_workdir_output_log_and_verification_command",
        },
    ]


def build_long_job_policy_rows(generated_at: str) -> list[dict[str, Any]]:
    stamp = generated_at.replace("-", "").replace(":", "").replace("T", "_")
    return [
        {
            "version": VERSION,
            "job_id": RENDER_JOB_ID,
            "job_type": "source_gap_non_oracle_render_frame_staging",
            "job_status": "deferred_until_m84_materialization",
            "launch_now": False,
            "tmux_session": "e008_m85_source_gap_render",
            "working_directory": str(ROOT),
            "output_path": str(M84_DATA_DIR),
            "log_path_template": str(ROOT / "logs" / f"{stamp}_e008_m85_source_gap_render.log"),
            "expected_files": [
                "rendered_frame_rows.jsonl",
                "snap_validation_rows.jsonl",
                "render_summary.json",
                "3RScan/scans/<scan_id>/sequence/frame-*.color.jpg",
                "3RScan/scans/<scan_id>/sequence/frame-*.depth.pgm",
                "3RScan/scans/<scan_id>/sequence/frame-*.pose.txt",
            ],
            "verification_command_template": (
                "python experiments/E008_real_navigation_benchmark/tools/verify_m85_source_gap_render_frame_staging.py "
                "--require-ready"
            ),
            "rationale": "M83 records policy only; M84 must write the exact launchable command after materializing inputs.",
        },
        {
            "version": VERSION,
            "job_id": DETECTOR_JOB_ID,
            "job_type": "source_gap_open_vocabulary_detector_candidate_source",
            "job_status": "deferred_until_render_verification",
            "launch_now": False,
            "tmux_session": "e008_m86_source_gap_detector",
            "working_directory": str(ROOT),
            "output_path": str(
                EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"
            ),
            "log_path_template": str(ROOT / "logs" / f"{stamp}_e008_m86_source_gap_detector.log"),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
                "matching/coverage.json",
            ],
            "verification_command_template": (
                "python experiments/E008_real_navigation_benchmark/tools/verify_m86_source_gap_detector_candidate_source.py "
                "--require-ready"
            ),
            "rationale": "Detector launch must wait until rendered frames and detector manifests pass M85 verification.",
        },
    ]


def build_readiness_gate_rows(
    m82_coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_routes = [row for row in route_rows if bool(row.get("materialize_in_m84"))]
    return [
        {
            "version": VERSION,
            "gate_id": "m82_ready_and_selected_m83",
            "gate_status": "pass"
            if m82_coverage.get("status") == "e008_m82_loss_safe_candidate_source_expansion_result_interpretation_ready"
            and str(m82_coverage.get("selected_next_unit", "")).startswith("E008-M83")
            else "fail",
            "rationale": "M83 starts only after M82 blocks trajectory promotion and selects source expansion.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_cases_present",
            "gate_status": "pass" if case_rows else "fail",
            "rationale": "The contract needs unresolved source-gap cases.",
        },
        {
            "version": VERSION,
            "gate_id": "existing_append_insufficient",
            "gate_status": "pass"
            if case_rows and not any(row.get("existing_append_recovered_primary_proxy") for row in case_rows)
            else "fail",
            "rationale": "M82 shows append rows do not recover source-gap cases.",
        },
        {
            "version": VERSION,
            "gate_id": "selected_non_oracle_routes_present",
            "gate_status": "pass" if len(selected_routes) >= len(case_rows) * 2 else "fail",
            "rationale": "Each source-gap case should have local-shell and high-path refresh routes.",
        },
        {
            "version": VERSION,
            "gate_id": "input_guard_fixed",
            "gate_status": "pass" if allowed_rows and blocked_rows else "fail",
            "rationale": "Allowed and blocked input groups must be explicit before materialization.",
        },
        {
            "version": VERSION,
            "gate_id": "m84_output_contract_fixed",
            "gate_status": "pass" if materialization_rows else "fail",
            "rationale": "M84 must have expected output files and row-count guards.",
        },
        {
            "version": VERSION,
            "gate_id": "no_long_job_launched_in_m83",
            "gate_status": "pass",
            "rationale": "M83 is a contract artifact only; render/detector jobs wait for M84/M85/M86.",
        },
        {
            "version": VERSION,
            "gate_id": "deployable_runtime_trigger_not_ready",
            "gate_status": "warning",
            "rationale": "M83 uses source-gap cases for failure-analysis selection, not as a final runtime trigger.",
        },
    ]


def build_evaluation_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "stage_id": "E008-M84",
            "required_check": "materialize source-gap observation/render/detector manifests",
            "pass_condition": "all selected M83 routes have rows, no eval goal/viewpoint fields, and output paths stay under local_dataset/HM3D_navigation_bridge",
            "claim_if_pass": "source expansion inputs are leakage-safe and launch-ready",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M85",
            "required_check": "render source-gap frames in Docker/Habitat and verify frame files",
            "pass_condition": "ready frames equal expected frames, pose/depth/color files exist, and snap warnings are reported separately",
            "claim_if_pass": "non-oracle RGB-D source evidence exists for the selected source-gap rows",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M86",
            "required_check": "run open-vocabulary detector on M85 frames",
            "pass_condition": "candidate rows, pre-cap rows, validator coverage, and matching diagnostics are exported",
            "claim_if_pass": "real RGB-D/open-vocabulary proposal route can be inspected for source-gap repair",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M87",
            "required_check": "snap detector candidates to navmesh and compute source-to-candidate paths",
            "pass_condition": "coordinate-valid, snapped navigable, and source-to-candidate path-ready rows are reported",
            "claim_if_pass": "expanded candidates are navigation-compatible enough for proxy visit-order evaluation",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M88",
            "required_check": "leakage-safe source-gap goal-evaluation proxy",
            "pass_condition": "new expanded-source policy improves source-gap primary proxy without budget-5 loss",
            "claim_if_pass": "source/observation expansion repairs the current source-gap proxy blocker",
        },
        {
            "version": VERSION,
            "stage_id": "E008-M89",
            "required_check": "trajectory promotion decision",
            "pass_condition": "M88 source-gap recovery and loss-safety pass before any Habitat trajectory run",
            "claim_if_pass": "trajectory execution is justified for the repaired source-gap policy",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_non_oracle_expansion_contract",
            "supported": True,
            "claim_boundary": "M83 supports a leakage-aware contract for source-gap source/observation expansion.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M83 does not create new detector candidates or evaluate source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "M83 still uses post-hoc source-gap cases for diagnostic selection; final runtime trigger is not defined.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M83 does not execute Habitat trajectories or compare external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M83 only plans future RGB-D/open-vocabulary evidence; robustness needs M85-M88 outputs.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M83 has no human-intent ablation; task context remains secondary unless E006 is promoted.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "rationale": "M84 should materialize source-gap observation pose, render, detector manifest, and long-job ledger rows before launching render/detector jobs.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| `{episode}` | {category} | {obs} | {cand} | {routes} |".format(
            episode=row.get("adapter_episode_id"),
            category=row.get("object_category"),
            obs=row.get("m64_observation_pose_rows"),
            cand=row.get("m80_candidate_visit_rows"),
            routes=", ".join(row.get("selected_contract_routes", [])),
        )
        for row in case_rows
    ]
    route_lines = [
        "| `{episode}` | `{route}` | {status} | {materialize} |".format(
            episode=row.get("adapter_episode_id"),
            route=row.get("route_id"),
            status=row.get("route_status"),
            materialize=row.get("materialize_in_m84"),
        )
        for row in route_rows
    ]
    gate_lines = [
        f"| `{row['gate_id']}` | {row['gate_status']} | {row['rationale']} |"
        for row in readiness_rows
    ]
    return f"""# E008-M83 Source-Gap Non-Oracle Source/Observation Expansion Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M82 status: `{coverage['m82_status']}`.
- Source-gap contract cases: {coverage['source_gap_case_rows']}.
- Selected materialization routes: {coverage['selected_materialization_route_rows']}.
- M84 materialization contract rows: {coverage['materialization_contract_rows']}.
- Launch long job now: {coverage['launch_long_job_now']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Source-Gap Cases

| adapter_episode_id | category | M64 obs poses | M80 candidates | selected routes |
| --- | --- | ---: | ---: | --- |
{chr(10).join(case_lines)}

## Expansion Routes

| adapter_episode_id | route | status | materialize in M84 |
| --- | --- | --- | --- |
{chr(10).join(route_lines)}

## Readiness Gates

| gate | status | rationale |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M83 supports only a non-oracle source/observation expansion contract.
- M83 does not support source-gap recovery, deployable search policy, final real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human intent as a main claim.
"""


def sync_derived() -> None:
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m82_coverage = read_json(M82_DIR / "coverage.json")
    m82_source_gap_rows = read_jsonl(M82_DIR / "source_gap_decision_rows.jsonl")
    source_plan_rows = read_jsonl(M80_DIR / "source_observation_expansion_plan_rows.jsonl")
    candidate_visit_rows = read_jsonl(M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl")
    observation_pose_rows = read_jsonl(M64_DIR / "observation_pose_plan_rows.jsonl")
    render_plan_rows = read_jsonl(M64_DIR / "render_plan_rows.jsonl")
    prompt_set = read_json(M65_DIR / "prompt_set.json") or read_json(M64_DIR / "prompt_set.json")

    missing_inputs = []
    for path, rows in [
        (M82_DIR / "coverage.json", [m82_coverage] if m82_coverage else []),
        (M82_DIR / "source_gap_decision_rows.jsonl", m82_source_gap_rows),
        (M80_DIR / "source_observation_expansion_plan_rows.jsonl", source_plan_rows),
        (M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl", candidate_visit_rows),
        (M64_DIR / "observation_pose_plan_rows.jsonl", observation_pose_rows),
        (M64_DIR / "render_plan_rows.jsonl", render_plan_rows),
        (M65_DIR / "prompt_set.json", [prompt_set] if prompt_set else []),
    ]:
        if not rows:
            missing_inputs.append(str(path))

    case_rows = build_case_rows(
        m82_source_gap_rows,
        source_plan_rows,
        observation_pose_rows,
        render_plan_rows,
        candidate_visit_rows,
        prompt_set,
    )
    route_rows = build_route_rows(case_rows, source_plan_rows)
    allowed_rows = build_allowed_input_rows()
    blocked_rows = build_blocked_input_rows()
    materialization_rows = build_materialization_contract_rows(case_rows, route_rows)
    long_job_rows = build_long_job_policy_rows(generated_at)
    readiness_rows = build_readiness_gate_rows(
        m82_coverage,
        case_rows,
        route_rows,
        allowed_rows,
        blocked_rows,
        materialization_rows,
    )
    evaluation_rows = build_evaluation_gate_rows()
    claim_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    selected_materialization_route_rows = sum(1 for row in route_rows if bool(row.get("materialize_in_m84")))
    fail_rows = sum(1 for row in readiness_rows if row.get("gate_status") == "fail")
    status = READY_STATUS if not missing_inputs and fail_rows == 0 else BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m82_status": m82_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "source_gap_case_rows": len(case_rows),
        "source_gap_case_ids": [row.get("adapter_episode_id") for row in case_rows],
        "source_gap_resolved_before_m83": any(row.get("source_gap_resolved_before_m83") for row in case_rows),
        "source_plan_rows": len(source_plan_rows),
        "source_observation_route_rows": len(route_rows),
        "selected_materialization_route_rows": selected_materialization_route_rows,
        "allowed_input_rows": len(allowed_rows),
        "blocked_input_rows": len(blocked_rows),
        "materialization_contract_rows": len(materialization_rows),
        "long_job_policy_rows": len(long_job_rows),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": fail_rows,
        "readiness_gate_warning_rows": sum(1 for row in readiness_rows if row.get("gate_status") == "warning"),
        "evaluation_gate_rows": len(evaluation_rows),
        "claim_boundary_rows": len(claim_rows),
        "m84_materialization_contract_ready": status == READY_STATUS,
        "m85_render_launch_ready_now": False,
        "m86_detector_launch_ready_now": False,
        "trajectory_execution_ready_now": False,
        "goal_evaluation_ready_now": False,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_jsonl(ARTIFACT_DIR / "source_gap_contract_case_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "source_observation_expansion_route_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_rows.jsonl", allowed_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_contract_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_policy_rows.jsonl", long_job_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(ARTIFACT_DIR / "evaluation_gate_rows.jsonl", evaluation_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, route_rows, readiness_rows),
        encoding="utf-8",
    )

    sync_derived()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
