#!/usr/bin/env python3
"""Fix the M120 target-free source-coverage expansion contract."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M119_DIR = EXP_ROOT / "artifacts" / "E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M120_hm3d_target_free_source_coverage_expansion_contract_v0"
)

VERSION = "e008_m120_hm3d_target_free_source_coverage_expansion_contract_v0"
READY_STATUS = "e008_m120_hm3d_target_free_source_coverage_expansion_contract_ready"
BLOCKED_STATUS = "e008_m120_hm3d_target_free_source_coverage_expansion_contract_blocked"
NEXT_UNIT = "E008-M121 HM3D target-free source-coverage expansion materialization smoke"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[str(row.get(key))] = row
    return out


def build_case_rows(
    source_case_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    episodes = index_by(episode_rows, "adapter_episode_id")
    visibility_by_episode: dict[str, list[dict[str, Any]]] = {}
    for row in visibility_rows:
        visibility_by_episode.setdefault(str(row.get("adapter_episode_id")), []).append(row)

    rows: list[dict[str, Any]] = []
    for source_case in source_case_rows:
        episode_id = str(source_case.get("adapter_episode_id"))
        episode = episodes.get(episode_id, {})
        visibility = visibility_by_episode.get(episode_id, [])
        min_source_to_target = [
            row.get("min_source_pose_to_any_viewpoint_xz_m")
            for row in visibility
            if isinstance(row.get("min_source_pose_to_any_viewpoint_xz_m"), (int, float))
        ]
        rows.append(
            {
                "version": VERSION,
                "row_type": "target_free_source_coverage_case",
                "adapter_episode_id": episode_id,
                "scan_id": source_case.get("scan_id"),
                "scene_key": source_case.get("scene_key"),
                "object_category": source_case.get("object_category"),
                "source_episode_id": episode.get("source_episode_id"),
                "split": episode.get("split"),
                "scene_docker_path": episode.get("scene_docker_path"),
                "navmesh_docker_path": episode.get("navmesh_docker_path"),
                "resolved_scene_path": episode.get("resolved_scene_path"),
                "resolved_navmesh_path": episode.get("resolved_navmesh_path"),
                "start_position": episode.get("start_position"),
                "start_rotation": episode.get("start_rotation"),
                "m119_candidate_rows": source_case.get("candidate_rows"),
                "m119_path_ready_candidate_rows": source_case.get("path_ready_candidate_rows"),
                "m119_primary_target_near_candidate_rows": source_case.get(
                    "primary_target_near_candidate_rows"
                ),
                "m119_relaxed_target_near_candidate_rows": source_case.get(
                    "relaxed_target_near_candidate_rows"
                ),
                "m119_min_any_viewpoint_xz_m_metric_only": source_case.get("min_any_viewpoint_xz_m"),
                "m119_min_source_pose_to_any_viewpoint_xz_m_metric_only": (
                    min(min_source_to_target) if min_source_to_target else None
                ),
                "case_selection_basis": "M119 posthoc source-coverage diagnosis",
                "deployable_trigger_supported": False,
                "target_free_source_expansion_required": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric_only": True,
                "claim_boundary": (
                    "This case row carries M119 posthoc diagnosis. M120 expansion policies below must not "
                    "use ObjectNav goal/viewpoint coordinates to place source poses."
                ),
            }
        )
    return rows


def build_route_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes = [
        {
            "route_id": "target_free_navigable_coverage_sweep_v0",
            "rank": 1,
            "decision": "select_primary",
            "pose_generation_principle": "sample reachable navmesh poses by scene/start coverage, not by object target position",
            "planned_pose_budget_per_case": 24,
            "yaw_samples_per_pose": 8,
            "requires_habitat_navmesh": True,
            "requires_render_job_after_materialization": True,
            "why_needed": "M84/M93 source poses remained far from the target view region; the next route must expand source coverage rather than rerank existing candidates.",
        },
        {
            "route_id": "target_free_path_prefix_diversity_sweep_v0",
            "rank": 2,
            "decision": "select_secondary",
            "pose_generation_principle": "sample diverse path-prefix/frontier poses reachable from the episode start with no target/viewpoint input",
            "planned_pose_budget_per_case": 16,
            "yaw_samples_per_pose": 8,
            "requires_habitat_navmesh": True,
            "requires_render_job_after_materialization": True,
            "why_needed": "If uniform coverage oversamples open space, path-prefix diversity pressures whether source coverage improves under a navigation-feasible observation budget.",
        },
        {
            "route_id": "same_source_external_mapper_audit_v0",
            "rank": 99,
            "decision": "reject_as_recovery_route",
            "pose_generation_principle": "reuse M84/M93 far source frames and change only the mapper/proposal method",
            "planned_pose_budget_per_case": 0,
            "yaw_samples_per_pose": 0,
            "requires_habitat_navmesh": False,
            "requires_render_job_after_materialization": False,
            "why_needed": "M119 shows same-source frames are a visibility/source-coverage negative; this route can be diagnostic only, not recovery evidence.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in case_rows:
        for route in routes:
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "target_free_source_expansion_route",
                    "adapter_episode_id": case.get("adapter_episode_id"),
                    "scan_id": case.get("scan_id"),
                    "scene_key": case.get("scene_key"),
                    "object_category": case.get("object_category"),
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_target_object_id_or_success_label": False,
                    "policy_input_allowed": route["decision"] != "reject_as_recovery_route",
                    "claim_boundary": "Route rows define source coverage planning only; no recovery or navigation claim is supported.",
                    **route,
                }
            )
    return rows


def build_materialization_contract_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row for row in route_rows if str(row.get("decision")).startswith("select")]
    rows: list[dict[str, Any]] = []
    for row in selected:
        pose_budget = int(row.get("planned_pose_budget_per_case") or 0)
        yaw_samples = int(row.get("yaw_samples_per_pose") or 0)
        rows.append(
            {
                "version": VERSION,
                "row_type": "m121_materialization_contract",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "route_id": row.get("route_id"),
                "m121_expected_observation_pose_rows": pose_budget,
                "m121_expected_render_plan_rows": pose_budget * yaw_samples,
                "m121_coordinate_validation_required": True,
                "m121_snap_to_navmesh_required": True,
                "m121_render_launch_in_m120": False,
                "m121_detector_launch_in_m120": False,
                "m121_allowed_inputs": [
                    "HM3D scene",
                    "HM3D navmesh",
                    "episode start pose",
                    "scene reachable-space/navmesh sampling",
                    "source-coverage route id",
                    "query object category for later detector prompts",
                ],
                "m121_blocked_inputs": [
                    "ObjectNav eval goal position",
                    "ObjectNav target viewpoint coordinates",
                    "target object id",
                    "candidate-to-target distance",
                    "success labels",
                ],
                "claim_boundary": (
                    "M121 may materialize target-free source rows. Target/viewpoint fields remain "
                    "metric-only after rows are frozen."
                ),
            }
        )
    return rows


def build_allowed_blocked_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "field_group": "HM3D scene, navmesh, episode start pose",
            "allowed_for_source_placement": True,
            "allowed_for_metric": True,
            "audit_status": "pass",
            "reason": "These fields are available before evaluation and define the embodiment/source coverage problem.",
        },
        {
            "version": VERSION,
            "field_group": "query object category and detector prompt labels",
            "allowed_for_source_placement": False,
            "allowed_for_metric": True,
            "audit_status": "pass",
            "reason": "Object category can be used for later proposal scoring, but source pose placement must remain target-free.",
        },
        {
            "version": VERSION,
            "field_group": "ObjectNav eval goal and target viewpoints",
            "allowed_for_source_placement": False,
            "allowed_for_metric": "after_source_rows_are_frozen_only",
            "audit_status": "pass",
            "reason": "M120/M121 cannot use target fields to place source poses; they are allowed only for posthoc source-coverage evaluation.",
        },
        {
            "version": VERSION,
            "field_group": "target object id, candidate-to-target distance, success labels",
            "allowed_for_source_placement": False,
            "allowed_for_metric": False,
            "audit_status": "pass",
            "reason": "These would leak evaluation outcomes into source placement or policy selection.",
        },
    ]


def build_m121_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M121 materializes target-free source poses from scene/navmesh/start coverage, validates snap-to-navmesh, and writes render/detector manifests without target fields.",
            "next_action": "Run M121 materialization smoke, then decide whether to launch render/detector jobs.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M121 materializes rows but only duplicates M84/M93 source pose families or yields low pose diversity.",
            "next_action": "Treat as source-coverage diagnostic and redesign pose generator before long jobs.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M121 uses ObjectNav target positions, target viewpoints, target object id, success labels, or posthoc candidate-target distances to place source poses.",
            "next_action": "Do not launch render/detector/trajectory; redesign target-free source expansion.",
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_target_free_source_expansion_contract",
            "supported": True,
            "claim_boundary": "M120 fixes a target-free source-coverage expansion contract and M121 gate.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M120 does not materialize frames, run detectors/mappers, recover the sofa case, or improve navigation metrics.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M120 is a contract unit and does not execute Habitat trajectories.",
        },
    ]


def build_reviewer_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why is M120 not just target leakage from M119?",
            "answer": "M119 uses target/viewpoint distances only after source rows are frozen to diagnose failure. M120 blocks those fields for source placement and requires M121 to generate poses from scene/navmesh/start coverage only.",
        },
        {
            "version": VERSION,
            "question": "Why not rerank existing ConceptGraphs candidates?",
            "answer": "M119 shows the remaining sofa case has no primary or relaxed target-near path-ready candidate; source coverage must change before ranking can be fairly evaluated.",
        },
        {
            "version": VERSION,
            "question": "Why not immediately run VLMaps, HOV-SG, or OpenMask3D?",
            "answer": "External mappers over the same far source frames would confound mapper quality with source coverage. M120 fixes the source-coverage contract before external mapper pressure.",
        },
    ]


def write_report(path: Path, coverage: dict[str, Any], case_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> None:
    selected_routes = [row for row in route_rows if str(row.get("decision")).startswith("select")]
    lines = [
        "# E008-M120 HM3D Target-Free Source-Coverage Expansion Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Input M119 status: `{coverage['m119_status']}`.",
        f"- Source-coverage case rows: {coverage['source_coverage_case_rows']}.",
        f"- Target-free route rows: {coverage['target_free_source_expansion_route_rows']}.",
        f"- Selected route rows: {coverage['selected_route_rows']}.",
        f"- M121 materialization contract rows: {coverage['m121_materialization_contract_rows']}.",
        f"- Uses ObjectNav target/viewpoint for source placement: {coverage['uses_objectnav_target_for_source_placement']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Launch long job now: {coverage['launch_long_job_now']}.",
        "",
        "## Selected Case",
        "",
        "| scan_id | category | m119 candidates | m119 path-ready | min any-vp XZ m |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in case_rows:
        lines.append(
            f"| {row.get('scan_id')} | {row.get('object_category')} | {row.get('m119_candidate_rows')} | "
            f"{row.get('m119_path_ready_candidate_rows')} | {row.get('m119_min_any_viewpoint_xz_m_metric_only')} |"
        )
    lines.extend(
        [
            "",
            "## Selected Routes",
            "",
            "| route | decision | pose budget | yaw samples |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in selected_routes:
        lines.append(
            f"| {row.get('route_id')} | {row.get('decision')} | "
            f"{row.get('planned_pose_budget_per_case')} | {row.get('yaw_samples_per_pose')} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M120 fixes the target-free source-coverage expansion contract only.",
            "- M120 does not render frames, run detectors/mappers, recover the sofa case, execute trajectories, or claim real navigation `SR` / `SPL`.",
            "- M121 must validate source pose materialization without ObjectNav target/viewpoint leakage before any long job.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m119_coverage = read_json(M119_DIR / "coverage.json")
    source_case_rows = read_jsonl(M119_DIR / "source_coverage_case_rows.jsonl")
    visibility_rows = read_jsonl(M119_DIR / "visibility_proxy_rows.jsonl")
    m120_gate_rows_from_m119 = read_jsonl(M119_DIR / "m120_gate_rows.jsonl")
    episode_rows = read_jsonl(M64_DIR / "val_mini_episode_rows.jsonl")

    m119_ready = m119_coverage.get("status") == "e008_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_ready"
    pass_gate_present = any(row.get("gate") == "pass" for row in m120_gate_rows_from_m119)

    case_rows = build_case_rows(source_case_rows, visibility_rows, episode_rows) if m119_ready else []
    route_rows = build_route_rows(case_rows)
    materialization_rows = build_materialization_contract_rows(route_rows)
    allowed_blocked_rows = build_allowed_blocked_rows()
    m121_gate_rows = build_m121_gate_rows()
    claim_rows = build_claim_rows()
    reviewer_rows = build_reviewer_rows()

    selected_route_rows = [row for row in route_rows if str(row.get("decision")).startswith("select")]
    uses_target_for_source_placement = any(
        bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_source_placement"))
        for row in [*case_rows, *route_rows]
    )
    allowed_blocked_audit_pass = all(row.get("audit_status") == "pass" for row in allowed_blocked_rows)
    status = (
        READY_STATUS
        if m119_ready
        and pass_gate_present
        and case_rows
        and selected_route_rows
        and materialization_rows
        and not uses_target_for_source_placement
        and allowed_blocked_audit_pass
        else BLOCKED_STATUS
    )

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m119_status": m119_coverage.get("status"),
        "m119_selected_next_unit": m119_coverage.get("selected_next_unit"),
        "m119_pass_gate_present": pass_gate_present,
        "source_coverage_case_rows": len(case_rows),
        "target_free_source_expansion_route_rows": len(route_rows),
        "selected_route_rows": len(selected_route_rows),
        "m121_materialization_contract_rows": len(materialization_rows),
        "allowed_blocked_input_rows": len(allowed_blocked_rows),
        "allowed_blocked_audit_pass": allowed_blocked_audit_pass,
        "uses_objectnav_target_for_source_placement": uses_target_for_source_placement,
        "launch_long_job_now": False,
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "real_navigation_sr_spl_ready": False,
        "human_intent_main_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "target_free_source_coverage_case_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "target_free_source_expansion_route_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "m121_materialization_contract_rows.jsonl", materialization_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_blocked_input_rows.jsonl", allowed_blocked_rows)
    write_jsonl(ARTIFACT_DIR / "m121_gate_rows.jsonl", m121_gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_report(ARTIFACT_DIR / "report.md", coverage, case_rows, route_rows)

    for file_name in [
        "coverage.json",
        "target_free_source_coverage_case_rows.jsonl",
        "target_free_source_expansion_route_rows.jsonl",
        "m121_materialization_contract_rows.jsonl",
        "allowed_blocked_input_rows.jsonl",
        "m121_gate_rows.jsonl",
        "claim_boundary_rows.jsonl",
        "reviewer_defense_rows.jsonl",
        "report.md",
    ]:
        shutil.copy2(ARTIFACT_DIR / file_name, DATA_OUT_DIR / file_name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
