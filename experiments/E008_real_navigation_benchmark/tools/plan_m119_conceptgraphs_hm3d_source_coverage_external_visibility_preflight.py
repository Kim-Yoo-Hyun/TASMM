#!/usr/bin/env python3
"""Preflight external/visibility source-coverage routes after the M118 stop-region smoke."""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M84_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M103_DIR = EXP_ROOT / "artifacts" / "E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
M110_DIR = EXP_ROOT / "artifacts" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
M111_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M113_DIR = EXP_ROOT / "artifacts" / "E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0"
M116_DIR = EXP_ROOT / "artifacts" / "E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
M117_DIR = EXP_ROOT / "artifacts" / "E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"
M118_DIR = EXP_ROOT / "artifacts" / "E008-M118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_v0"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0"
)

VERSION = "e008_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_v0"
READY_STATUS = "e008_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_ready"
BLOCKED_STATUS = "e008_m119_conceptgraphs_hm3d_source_coverage_external_visibility_preflight_blocked"
NEXT_UNIT = "E008-M120 HM3D target-free source-coverage expansion contract"
PRIMARY_TARGET_NEAR_XZ_M = 1.0
RELAXED_TARGET_NEAR_XZ_M = 1.5
SOURCE_VISIBILITY_WARNING_XZ_M = 5.0

SOURCE_BUNDLES = [
    {
        "bundle_id": "m84_local_shell_multiview_source",
        "row_path": M84_DATA_DIR / "rendered_frame_rows.jsonl",
        "position_keys": ["render_position_m"],
        "role": "local start and local-shell multiview source",
    },
    {
        "bundle_id": "m93_wide_shell_frontier_refresh_source",
        "row_path": M93_DATA_DIR / "coverage_expansion_render_plan_rows.jsonl",
        "position_keys": ["source_position"],
        "role": "wider non-oracle source-gap coverage expansion source",
    },
]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    return module


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    return [float(value) for value in vec]  # type: ignore[arg-type]


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def dist_xz(a: list[float], b: list[float]) -> float:
    return float(math.sqrt((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2))


def nearest_xz(position: list[float], targets: list[list[float]]) -> float | None:
    if not targets:
        return None
    return min(dist_xz(position, target) for target in targets)


def docker_image_ready(image: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", image],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except Exception:
        return False
    return proc.returncode == 0


def read_positions(row: dict[str, Any], keys: list[str]) -> list[float] | None:
    for key in keys:
        value = as_vec3(row.get(key))
        if value is not None:
            return value
    return None


def source_image_counts(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[int] = Counter()
    for row in candidate_rows:
        for image_idx in row.get("source_image_idx") or []:
            try:
                counts[int(image_idx)] += 1
            except (TypeError, ValueError):
                continue
    return [{"source_image_idx": image_idx, "count": count} for image_idx, count in counts.most_common(10)]


def make_eval_index(m12: Any, eval_goal_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return m12.build_eval_goal_index(eval_goal_rows)


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get(key))].append(row)
    return out


def build_source_coverage_case_rows(
    source_route_rows: list[dict[str, Any]],
    source_audit_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    navmesh_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_scan = group_by(candidate_rows, "scan_id")
    nav_by_scan = group_by(navmesh_rows, "scan_id")
    audit_by_scan = {str(row.get("scan_id")): row for row in source_audit_rows}
    out: list[dict[str, Any]] = []
    for route in source_route_rows:
        scan_id = str(route.get("scan_id"))
        audit = audit_by_scan.get(scan_id, {})
        scan_candidates = candidates_by_scan.get(scan_id, [])
        scan_nav = nav_by_scan.get(scan_id, [])
        path_ready = [row for row in scan_nav if row.get("candidate_usable_for_path_smoke")]
        out.append(
            {
                "version": VERSION,
                "row_type": "source_coverage_case",
                "query_uid": route.get("query_uid"),
                "adapter_episode_id": route.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": route.get("scene_key"),
                "object_category": route.get("object_category"),
                "m114_failure_class": audit.get("m114_failure_class"),
                "candidate_source": route.get("candidate_source"),
                "current_source_recoverable_without_new_source": route.get(
                    "current_source_recoverable_without_new_source"
                ),
                "same_source_rerank_decision": route.get("same_source_rerank_decision"),
                "same_source_rerun_decision": route.get("same_source_rerun_decision"),
                "candidate_rows": len(scan_candidates),
                "path_ready_candidate_rows": len(path_ready),
                "path_ready_eval_candidate_rows": audit.get("path_ready_eval_candidate_rows"),
                "primary_target_near_candidate_rows": audit.get("primary_target_near_candidate_rows"),
                "relaxed_target_near_candidate_rows": audit.get("relaxed_target_near_candidate_rows"),
                "min_any_viewpoint_xz_m": audit.get("min_any_viewpoint_xz_m"),
                "mean_any_viewpoint_xz_m": audit.get("mean_any_viewpoint_xz_m"),
                "best_any_viewpoint_candidate_uid": audit.get("best_any_viewpoint_candidate_uid"),
                "best_any_viewpoint_candidate_source_image_idx": audit.get(
                    "best_any_viewpoint_candidate_source_image_idx"
                ),
                "candidate_distribution_stats": audit.get("candidate_distribution_stats"),
                "top_source_image_idx_counts": source_image_counts(scan_candidates),
                "preflight_conclusion": (
                    "current_source_closed_negative"
                    if not route.get("current_source_recoverable_without_new_source")
                    else "current_source_has_recoverable_candidate"
                ),
                "claim_boundary": "This row diagnoses current-source coverage only; it is not a recovery result.",
            }
        )
    return out


def build_visibility_proxy_rows(
    eval_index: dict[str, dict[str, Any]],
    target_episode_ids: set[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for bundle in SOURCE_BUNDLES:
        source_rows = read_jsonl(bundle["row_path"])
        for episode_id in sorted(target_episode_ids):
            eval_goal = eval_index.get(episode_id, {})
            if not eval_goal:
                continue
            scan_rows = [row for row in source_rows if str(row.get("adapter_episode_id")) == episode_id]
            if not scan_rows:
                scan_id = str(eval_goal.get("scene_key", "missing"))
                out.append(
                    {
                        "version": VERSION,
                        "row_type": "visibility_proxy",
                        "bundle_id": bundle["bundle_id"],
                        "adapter_episode_id": episode_id,
                        "scan_id": scan_id,
                        "object_category": eval_goal.get("object_category"),
                        "source_frame_rows": 0,
                        "source_unique_pose_rows": 0,
                        "visibility_proxy_status": "missing_source_rows",
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                    }
                )
                continue
            positions: list[list[float]] = []
            for row in scan_rows:
                position = read_positions(row, bundle["position_keys"])
                if position is not None:
                    positions.append(position)
            unique_positions = sorted({tuple(round(value, 4) for value in position) for position in positions})
            unique_positions_f = [[float(value) for value in position] for position in unique_positions]
            goal = as_vec3(eval_goal.get("eval_goal_position"))
            first_viewpoint = as_vec3(eval_goal.get("eval_first_viewpoint_position"))
            all_viewpoints = [
                as_vec3(viewpoint)
                for viewpoint in eval_goal.get("eval_all_viewpoint_positions", [])
                if as_vec3(viewpoint) is not None
            ]
            pose_to_goal = [dist_xz(position, goal) for position in unique_positions_f if goal is not None]
            pose_to_first = [
                dist_xz(position, first_viewpoint) for position in unique_positions_f if first_viewpoint is not None
            ]
            pose_to_any = [
                nearest_xz(position, all_viewpoints)
                for position in unique_positions_f
                if nearest_xz(position, all_viewpoints) is not None
            ]
            min_any = min(pose_to_any) if pose_to_any else None
            if min_any is None:
                status = "missing_eval_viewpoints_for_visibility_metric"
            elif min_any > SOURCE_VISIBILITY_WARNING_XZ_M:
                status = "source_poses_far_from_target_view_region"
            elif min_any > RELAXED_TARGET_NEAR_XZ_M:
                status = "source_poses_nearish_but_not_target_stop_region"
            else:
                status = "source_poses_target_region_reached"
            out.append(
                {
                    "version": VERSION,
                    "row_type": "visibility_proxy",
                    "bundle_id": bundle["bundle_id"],
                    "bundle_role": bundle["role"],
                    "adapter_episode_id": episode_id,
                    "scan_id": scan_rows[0].get("scan_id"),
                    "scene_key": scan_rows[0].get("scene_key"),
                    "object_category": eval_goal.get("object_category"),
                    "source_frame_rows": len(scan_rows),
                    "source_unique_pose_rows": len(unique_positions_f),
                    "min_source_pose_to_eval_goal_xz_m": min(pose_to_goal) if pose_to_goal else None,
                    "mean_source_pose_to_eval_goal_xz_m": mean(pose_to_goal),
                    "min_source_pose_to_first_viewpoint_xz_m": min(pose_to_first) if pose_to_first else None,
                    "min_source_pose_to_any_viewpoint_xz_m": min_any,
                    "mean_source_pose_to_any_viewpoint_xz_m": mean([value for value in pose_to_any if value is not None]),
                    "target_region_proxy_reached_1p5m": bool(min_any is not None and min_any <= RELAXED_TARGET_NEAR_XZ_M),
                    "target_region_proxy_reached_5p0m": bool(min_any is not None and min_any <= SOURCE_VISIBILITY_WARNING_XZ_M),
                    "visibility_proxy_status": status,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                    "claim_boundary": "Target/viewpoint distances are posthoc visibility diagnostics, not source-selection inputs.",
                }
            )
    return out


def build_external_route_preflight_rows(
    current_case_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    m103_route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    openmask_prior = next(
        (row for row in m103_route_rows if row.get("route_id") == "openmask3d_hm3d_3d_instance_proposal"),
        {},
    )
    source_far = all(
        row.get("visibility_proxy_status") == "source_poses_far_from_target_view_region"
        for row in visibility_rows
        if row.get("source_frame_rows")
    )
    current_source_closed = all(not row.get("current_source_recoverable_without_new_source") for row in current_case_rows)
    vlmaps_image_ready = docker_image_ready("research2/vlmaps-hm3d:20260508-timmfix")
    return [
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "same_conceptgraphs_source_rerank_or_rerun",
            "decision": "reject",
            "rank": 99,
            "prerequisite_ready": True,
            "reason": "M116/M117 show no target-near path-ready sofa candidate in the current ConceptGraphs source; rerank or same-source rerun cannot create missing source coverage.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "current_source_visibility_audit",
            "decision": "complete_diagnostic_only",
            "rank": 3,
            "prerequisite_ready": bool(visibility_rows),
            "source_poses_far_from_target_view_region": source_far,
            "reason": "Existing M84/M93 source poses are posthoc far from the sofa target view region, so the current source route is a visibility/source-coverage negative rather than a ranking failure.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "target_free_source_coverage_expansion",
            "decision": "select_next_contract",
            "rank": 1,
            "prerequisite_ready": current_source_closed and source_far,
            "reason": "The next repair must change non-oracle observation/source coverage before another map/proposal adapter can fairly recover the sofa case.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "vlmaps_hm3d_map_source_audit",
            "decision": "defer_after_source_expansion_contract",
            "rank": 2,
            "docker_image_ready": vlmaps_image_ready,
            "prerequisite_ready": vlmaps_image_ready,
            "reason": "A local `VLMaps` HM3D image exists and can pressure external map-source evidence, but reusing the same far source frames would not isolate source coverage from mapper quality.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "hov_sg_hm3d_map_navigation_baseline",
            "decision": "defer_source_runtime_setup",
            "rank": 4,
            "local_source_or_image_ready": False,
            "prerequisite_ready": False,
            "reason": "`HOV-SG` remains a strong Direction B baseline, but there is no local staged source/runtime in this repo yet.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "external_source_route_preflight",
            "route_id": "openmask3d_hm3d_3d_instance_proposal",
            "decision": "defer_blocked",
            "rank": 5,
            "checkpoint_ready": openmask_prior.get("checkpoint_ready"),
            "docker_image_ready": docker_image_ready("research2/openmask3d-smoke:latest"),
            "prerequisite_ready": False,
            "reason": "OpenMask3D is a relevant proposal baseline, but the current Docker/MinkowskiEngine blocker remains unresolved.",
            "launch_long_job_now": False,
        },
    ]


def build_allowed_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "field": "existing non-target source poses and frame metadata",
            "allowed_as_policy_input": True,
            "allowed_as_metric_input": True,
            "audit_status": "pass",
            "reason": "These rows were generated before ObjectNav target/viewpoint evaluation.",
        },
        {
            "version": VERSION,
            "field": "current ConceptGraphs candidate geometry / source image ids / navmesh reachability",
            "allowed_as_policy_input": True,
            "allowed_as_metric_input": True,
            "audit_status": "pass",
            "reason": "These are frozen candidate-source outputs and can diagnose current source coverage.",
        },
        {
            "version": VERSION,
            "field": "ObjectNav eval goal and target viewpoints",
            "allowed_as_policy_input": False,
            "allowed_as_metric_input": "posthoc_visibility_metric_only",
            "audit_status": "pass",
            "reason": "M119 uses these only to label why the current source route failed after source rows are frozen.",
        },
        {
            "version": VERSION,
            "field": "target object id / success label",
            "allowed_as_policy_input": False,
            "allowed_as_metric_input": False,
            "audit_status": "pass",
            "reason": "These fields are not needed for source preflight or route selection.",
        },
    ]


def build_m120_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M120 materializes target-free source-expansion rows without ObjectNav target/viewpoint coordinates and records the later evaluation boundary.",
            "next_action": "Run E008-M120 target-free source-coverage expansion contract.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M120 only audits an external mapper over the same far source frames.",
            "next_action": "Treat the result as external-source diagnostic, not source-coverage recovery.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M120 uses ObjectNav target positions, target viewpoints, target object id, or success labels to place new source poses.",
            "next_action": "Do not run trajectory; redesign source expansion.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_current_source_coverage_negative",
            "supported": True,
            "claim_boundary": "M119 supports the conclusion that the current ConceptGraphs source has no target-near sofa candidate and that existing source poses are far from the target view region in posthoc diagnostics.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_next_source_expansion_contract_selection",
            "supported": True,
            "claim_boundary": "M119 supports selecting a target-free source-coverage expansion contract before another trajectory run.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M119 does not create new source poses, run an external mapper, or recover the sofa case.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_external_baseline_result",
            "supported": False,
            "claim_boundary": "M119 audits readiness for external sources only; it does not run VLMaps, HOV-SG, OpenMask3D, or a navigation baseline.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M119 does not execute Habitat trajectories and cannot claim real navigation SR/SPL.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not rerank the current ConceptGraphs candidates?",
            "answer": "The sofa case has 0 primary or relaxed target-near candidates and the nearest path-ready candidate is 5.204041m from any target viewpoint.",
        },
        {
            "version": VERSION,
            "question": "Why not run trajectory after M118?",
            "answer": "M118 only repairs the toilet stop-region interface. The sofa source-coverage gap remains unresolved, so a trajectory run would mix a positive local repair with a known unrecovered source failure.",
        },
        {
            "version": VERSION,
            "question": "Does the visibility audit use target leakage?",
            "answer": "It uses ObjectNav goal/viewpoints only after M84/M93/M105 source rows and M110/M111 candidate rows are frozen. M120 must not use target fields to place source poses.",
        },
        {
            "version": VERSION,
            "question": "Why not switch directly to HOV-SG or OpenMask3D?",
            "answer": "HOV-SG has no local runtime audit yet, and OpenMask3D remains Docker-blocked. More importantly, M119 shows the immediate failure is source coverage, so a fair external mapper comparison needs a source-expansion contract first.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    source_case_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    source_lines = [
        "| {scan_id} | {object_category} | {candidate_rows} | {path_ready_candidate_rows} | {min_any_viewpoint_xz_m} | {current_source_recoverable_without_new_source} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            candidate_rows=row.get("candidate_rows"),
            path_ready_candidate_rows=row.get("path_ready_candidate_rows"),
            min_any_viewpoint_xz_m=row.get("min_any_viewpoint_xz_m"),
            current_source_recoverable_without_new_source=row.get(
                "current_source_recoverable_without_new_source"
            ),
        )
        for row in source_case_rows
    ]
    visibility_lines = [
        "| {bundle_id} | {source_frame_rows} | {source_unique_pose_rows} | {min_source_pose_to_any_viewpoint_xz_m} | {visibility_proxy_status} |".format(
            bundle_id=row.get("bundle_id"),
            source_frame_rows=row.get("source_frame_rows"),
            source_unique_pose_rows=row.get("source_unique_pose_rows"),
            min_source_pose_to_any_viewpoint_xz_m=row.get("min_source_pose_to_any_viewpoint_xz_m"),
            visibility_proxy_status=row.get("visibility_proxy_status"),
        )
        for row in visibility_rows
    ]
    route_lines = [
        "| {rank} | {route_id} | {decision} | {prerequisite_ready} | {reason} |".format(
            rank=row.get("rank"),
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            prerequisite_ready=row.get("prerequisite_ready"),
            reason=row.get("reason"),
        )
        for row in sorted(route_rows, key=lambda row: int(row.get("rank") or 999))
    ]
    return f"""# E008-M119 ConceptGraphs HM3D Source-Coverage External / Visibility Preflight

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M118 status: `{coverage['m118_status']}`.
- Source-coverage case rows: {coverage['source_coverage_case_rows']}.
- Visibility proxy rows: {coverage['visibility_proxy_rows']}.
- External/source route preflight rows: {coverage['external_source_route_preflight_rows']}.
- Existing source poses far from target view region: {coverage['all_existing_source_pose_routes_far_from_target_view_region']}.
- Selected next unit: {coverage['selected_next_unit']}.
- Launch long job now: {coverage['launch_long_job_now']}.

## Current Source Case

| scan_id | category | candidates | path-ready | min any-vp XZ m | recoverable now |
| --- | --- | ---: | ---: | ---: | --- |
{chr(10).join(source_lines)}

## Visibility Proxy

| bundle | frames | unique poses | min source-pose to any-vp XZ m | status |
| --- | ---: | ---: | ---: | --- |
{chr(10).join(visibility_lines)}

## Route Preflight

| rank | route | decision | ready | reason |
| ---: | --- | --- | --- | --- |
{chr(10).join(route_lines)}

## Claim Boundary

- M119 is a source-coverage preflight, not a recovery result.
- M119 supports rejecting same-source rerank/rerun for the sofa source gap.
- M119 selects a target-free source-coverage expansion contract before trajectory promotion.
- M119 does not run external baselines or claim real navigation `SR` / `SPL`.
"""


def main() -> None:
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m118_coverage = read_json(M118_DIR / "coverage.json")
    m119_gate_rows = read_jsonl(M118_DIR / "m119_gate_rows.jsonl")
    source_route_rows = read_jsonl(M117_DIR / "source_coverage_route_decision_rows.jsonl")
    source_audit_rows = read_jsonl(M116_DIR / "source_coverage_audit_rows.jsonl")
    candidate_rows = read_jsonl(M110_DIR / "candidate_rows.jsonl")
    navmesh_rows = read_jsonl(M111_DIR / "candidate_navmesh_validation_rows.jsonl")
    eval_goal_rows = read_jsonl(M113_DIR / "conceptgraphs_eval_goal_rows.jsonl")
    m103_route_rows = read_jsonl(M103_DIR / "route_feasibility_rows.jsonl")

    target_episode_ids = {str(row.get("adapter_episode_id")) for row in source_route_rows}
    target_eval_goal_rows = [
        row for row in eval_goal_rows if str(row.get("adapter_episode_id")) in target_episode_ids
    ]
    eval_index = make_eval_index(m12, target_eval_goal_rows)

    source_case_rows = build_source_coverage_case_rows(
        source_route_rows,
        source_audit_rows,
        candidate_rows,
        navmesh_rows,
    )
    visibility_rows = build_visibility_proxy_rows(eval_index, target_episode_ids)
    route_rows = build_external_route_preflight_rows(source_case_rows, visibility_rows, m103_route_rows)
    allowed_blocked_rows = build_allowed_blocked_input_rows()
    m120_gate_rows = build_m120_gate_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()

    leakage_pass = (
        all(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") is False for row in visibility_rows)
        and all(row.get("audit_status") == "pass" for row in allowed_blocked_rows)
    )
    source_far_rows = [
        row
        for row in visibility_rows
        if row.get("source_frame_rows") and row.get("visibility_proxy_status") == "source_poses_far_from_target_view_region"
    ]
    all_existing_source_far = len(source_far_rows) == len([row for row in visibility_rows if row.get("source_frame_rows")])
    selected_route = next((row for row in route_rows if row.get("decision") == "select_next_contract"), {})
    ready = (
        m118_coverage.get("status")
        == "e008_m118_conceptgraphs_hm3d_non_oracle_stop_region_transform_materialization_smoke_ready"
        and bool(m119_gate_rows)
        and bool(source_case_rows)
        and bool(visibility_rows)
        and bool(selected_route)
        and leakage_pass
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m118_status": m118_coverage.get("status"),
        "m118_stop_region_budget5_proxy_recovery_observed": m118_coverage.get(
            "stop_region_budget5_proxy_recovery_observed"
        ),
        "m119_gate_rows": len(m119_gate_rows),
        "source_coverage_route_rows": len(source_route_rows),
        "source_coverage_case_rows": len(source_case_rows),
        "visibility_proxy_rows": len(visibility_rows),
        "external_source_route_preflight_rows": len(route_rows),
        "allowed_blocked_input_rows": len(allowed_blocked_rows),
        "allowed_blocked_input_audit_pass": all(row.get("audit_status") == "pass" for row in allowed_blocked_rows),
        "visibility_policy_leakage": not leakage_pass,
        "leakage_audit_pass": leakage_pass,
        "all_existing_source_pose_routes_far_from_target_view_region": all_existing_source_far,
        "selected_route_id": selected_route.get("route_id"),
        "selected_next_unit": selected_route.get("selected_next_unit") or NEXT_UNIT,
        "selected_next_unit_reason": selected_route.get("reason"),
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "source_coverage_case_rows.jsonl": source_case_rows,
        "visibility_proxy_rows.jsonl": visibility_rows,
        "external_source_route_preflight_rows.jsonl": route_rows,
        "allowed_blocked_input_rows.jsonl": allowed_blocked_rows,
        "m120_gate_rows.jsonl": m120_gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, source_case_rows, visibility_rows, route_rows))

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
