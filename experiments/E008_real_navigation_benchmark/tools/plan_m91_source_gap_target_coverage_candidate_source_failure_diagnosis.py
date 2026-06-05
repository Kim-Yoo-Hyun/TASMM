#!/usr/bin/env python3
"""Diagnose M90 source-gap failures across target coverage and candidate-source stages."""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M70_TOOL = EXP_ROOT / "tools" / "run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py"
M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M84_DIR = EXP_ROOT / "artifacts" / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
M86_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"
M87_DIR = EXP_ROOT / "artifacts" / "E008-M87_source_gap_detector_candidate_navmesh_validation_v0"
M89_DIR = EXP_ROOT / "artifacts" / "E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0"
M90_DIR = EXP_ROOT / "artifacts" / "E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
)

VERSION = "e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
READY_STATUS = "e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_ready"
BLOCKED_STATUS = "e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_blocked"
NEXT_UNIT = "E008-M92 source-gap two-branch coverage/cap repair contract"

PRIMARY_RADIUS_M = 1.0
RELAXED_RADIUS_M = 1.5
CAP_RANK = 24


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def dist_xz(a: object, b: object) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    assert isinstance(a, list) and isinstance(b, list)
    return float(math.hypot(float(a[0]) - float(b[0]), float(a[2]) - float(b[2])))


def dist3(a: object, b: object) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    assert isinstance(a, list) and isinstance(b, list)
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def min_clean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return min(clean) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def frame_id(row: dict[str, Any]) -> str | None:
    ids = row.get("frame_ids")
    if isinstance(ids, list) and ids:
        return str(ids[0])
    bbox = row.get("bbox_2d")
    if isinstance(bbox, dict) and bbox:
        return str(next(iter(bbox.keys())))
    return None


def scan_id_from_eval_goal(row: dict[str, Any]) -> str:
    scene_key = str(row.get("scene_key"))
    source_episode_id = str(row.get("source_episode_id"))
    return f"hm3dnav_{scene_key.replace('-', '_')}_ep{source_episode_id}"


def build_pre_cap_candidate_eval_rows(
    pre_cap_rows: list[dict[str, Any]],
    eval_index_by_scan: dict[str, dict[str, Any]],
    render_by_scan_frame: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    ranked_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pre_cap_rows:
        ranked_by_scan[str(row.get("scan_id"))].append(row)

    confidence_rank: dict[str, int] = {}
    for scan_id, rows in ranked_by_scan.items():
        for idx, row in enumerate(
            sorted(rows, key=lambda item: finite_float(item.get("confidence")) or -1.0, reverse=True),
            start=1,
        ):
            confidence_rank[str(row.get("pre_cap_candidate_pool_uid"))] = idx

    out: list[dict[str, Any]] = []
    for row in pre_cap_rows:
        scan_id = str(row.get("scan_id"))
        eval_goal = eval_index_by_scan.get(scan_id)
        if not eval_goal:
            continue
        frame = frame_id(row)
        render = render_by_scan_frame.get((scan_id, str(frame)), {})
        centroid = row.get("centroid_world_m")
        viewpoints = eval_goal.get("eval_all_viewpoint_positions") or []
        nearest_any_xz = min_clean([dist_xz(centroid, viewpoint) for viewpoint in viewpoints])
        nearest_any_3d = min_clean([dist3(centroid, viewpoint) for viewpoint in viewpoints])
        goal_xz = dist_xz(centroid, eval_goal.get("eval_goal_position"))
        goal_3d = dist3(centroid, eval_goal.get("eval_goal_position"))
        first_xz = dist_xz(centroid, eval_goal.get("eval_first_viewpoint_position"))
        rank = confidence_rank.get(str(row.get("pre_cap_candidate_pool_uid")))
        out.append(
            {
                "version": VERSION,
                "row_type": "pre_cap_candidate_eval",
                "scan_id": scan_id,
                "adapter_episode_id": eval_goal.get("adapter_episode_id"),
                "scene_key": eval_goal.get("scene_key"),
                "object_category": eval_goal.get("object_category"),
                "label_canonical": row.get("label_canonical"),
                "frame_id": frame,
                "observation_pose_id": render.get("observation_pose_id"),
                "pose_role": render.get("pose_role"),
                "route_id": render.get("route_id"),
                "shell_radius_m": render.get("shell_radius_m"),
                "yaw_offset_deg": render.get("yaw_offset_deg"),
                "pre_cap_candidate_pool_uid": row.get("pre_cap_candidate_pool_uid"),
                "raw_candidate_uid": row.get("raw_candidate_uid"),
                "centroid_world_m": centroid,
                "confidence": row.get("confidence"),
                "confidence_rank_within_scan_label": rank,
                "inside_final_label_cap_by_confidence": rank is not None and rank <= CAP_RANK,
                "bbox_2d": row.get("bbox_2d"),
                "depth_valid_pixel_count": row.get("depth_valid_pixel_count"),
                "candidate_to_eval_goal_xz_m": goal_xz,
                "candidate_to_eval_goal_3d_m": goal_3d,
                "candidate_to_eval_first_viewpoint_xz_m": first_xz,
                "candidate_to_nearest_eval_viewpoint_xz_m": nearest_any_xz,
                "candidate_to_nearest_eval_viewpoint_3d_m": nearest_any_3d,
                "hit_goal_xz_1p0": goal_xz is not None and goal_xz <= PRIMARY_RADIUS_M,
                "hit_any_viewpoint_xz_1p0": nearest_any_xz is not None and nearest_any_xz <= PRIMARY_RADIUS_M,
                "hit_any_viewpoint_xz_1p5": nearest_any_xz is not None and nearest_any_xz <= RELAXED_RADIUS_M,
                "policy_input_allowed": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "Pre-cap rows are diagnosed against ObjectNav goals/viewpoints only after candidate generation; they are not policy inputs.",
            }
        )
    return out


def build_observation_coverage_rows(
    pose_rows: list[dict[str, Any]],
    eval_index_by_episode: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in pose_rows:
        eval_goal = eval_index_by_episode.get(str(row.get("adapter_episode_id")))
        if not eval_goal:
            continue
        pose = row.get("planned_position_m")
        out.append(
            {
                "version": VERSION,
                "row_type": "observation_pose_eval_distance",
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "observation_pose_id": row.get("observation_pose_id"),
                "pose_role": row.get("pose_role"),
                "route_id": row.get("route_id"),
                "shell_radius_m": row.get("shell_radius_m"),
                "planned_position_m": pose,
                "pose_to_eval_goal_xz_m": dist_xz(pose, eval_goal.get("eval_goal_position")),
                "pose_to_eval_first_viewpoint_xz_m": dist_xz(pose, eval_goal.get("eval_first_viewpoint_position")),
                "policy_input_allowed": bool(row.get("policy_input_allowed")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            }
        )
    return out


def best_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    valid = [row for row in rows if finite_float(row.get(key)) is not None]
    if not valid:
        return None
    return min(valid, key=lambda row: float(row[key]))


def build_case_diagnosis_rows(
    m90_rows: list[dict[str, Any]],
    eval_goal_rows: list[dict[str, Any]],
    prompt_labels: set[str],
    manifest_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    frame_rows: list[dict[str, Any]],
    frame_diag_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    nav_rows: list[dict[str, Any]],
    m89_case_rows: list[dict[str, Any]],
    pre_cap_eval_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_scan = {str(row.get("scan_id")): row for row in manifest_rows}
    scan_ready_by_scan = {str(row.get("scan_id")): row for row in scan_rows}
    summary_by_scan = {str(row.get("scan_id")): row for row in summary_rows}
    eval_by_scan = {scan_id_from_eval_goal(row): row for row in eval_goal_rows}

    frame_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    frame_diag_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nav_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    m89_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pre_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    obs_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        frame_by_scan[str(row.get("scan_id"))].append(row)
    for row in frame_diag_rows:
        frame_diag_by_scan[str(row.get("scan_id"))].append(row)
    for row in nav_rows:
        nav_by_scan[str(row.get("scan_id"))].append(row)
    for row in m89_case_rows:
        m89_by_scan[str(row.get("scan_id"))].append(row)
    for row in pre_cap_eval_rows:
        pre_by_scan[str(row.get("scan_id"))].append(row)
    for row in observation_rows:
        obs_by_scan[str(row.get("scan_id"))].append(row)

    out: list[dict[str, Any]] = []
    for m90 in sorted(m90_rows, key=lambda row: str(row.get("scan_id"))):
        scan_id = str(m90.get("scan_id"))
        category = str(m90.get("object_category"))
        eval_goal = eval_by_scan.get(scan_id, {})
        pre_rows = pre_by_scan.get(scan_id, [])
        obs_rows = obs_by_scan.get(scan_id, [])
        nav_scan_rows = nav_by_scan.get(scan_id, [])
        m89_rows = m89_by_scan.get(scan_id, [])
        frame_diag_scan_rows = frame_diag_by_scan.get(scan_id, [])
        best_pre_any = best_row(pre_rows, "candidate_to_nearest_eval_viewpoint_xz_m")
        best_pre_goal = best_row(pre_rows, "candidate_to_eval_goal_xz_m")
        best_final_any = best_row(m89_rows, "best_any_viewpoint_xz_m")
        best_obs_goal = best_row(obs_rows, "pose_to_eval_goal_xz_m")
        best_obs_first = best_row(obs_rows, "pose_to_eval_first_viewpoint_xz_m")
        pre_primary_hits = sum(1 for row in pre_rows if bool(row.get("hit_any_viewpoint_xz_1p0")))
        pre_relaxed_hits = sum(1 for row in pre_rows if bool(row.get("hit_any_viewpoint_xz_1p5")))
        pre_goal_hits = sum(1 for row in pre_rows if bool(row.get("hit_goal_xz_1p0")))
        final_primary_hits = sum(1 for row in m89_rows if bool(row.get("primary_hit")))
        path_ready_rows = sum(1 for row in nav_scan_rows if bool(row.get("source_to_snapped_path_found")))
        prompt_ready = category in prompt_labels
        scan_ready = scan_ready_by_scan.get(scan_id, {}).get("scan_ready")
        ready_frames = sum(1 for row in frame_by_scan.get(scan_id, []) if bool(row.get("frame_ready")))
        raw_predictions = sum(int(row.get("raw_prediction_count") or 0) for row in frame_diag_scan_rows)
        selected_predictions = sum(int(row.get("written_prediction_count") or 0) for row in frame_diag_scan_rows)
        dropped_stage = "unknown"
        dominant_failure_type = "unknown"
        if pre_primary_hits > 0 and final_primary_hits == 0:
            dropped_stage = "primary_target_near_candidate_dropped_after_pre_cap"
            dominant_failure_type = "cap_or_ranking_suppressed_primary_target_candidate"
        elif pre_primary_hits == 0 and pre_relaxed_hits > 0:
            dropped_stage = "relaxed_target_near_candidate_exists_pre_cap_but_no_primary_hit"
            dominant_failure_type = "localization_threshold_gap_with_low_confidence_cap_suppression"
        elif pre_primary_hits == 0 and pre_relaxed_hits == 0:
            dropped_stage = "target_near_candidate_absent_even_pre_cap"
            dominant_failure_type = "observation_or_detector_target_coverage_gap"
        if not prompt_ready:
            dominant_failure_type = "prompt_label_gap"
        elif not scan_ready or ready_frames == 0:
            dominant_failure_type = "render_frame_readiness_gap"

        selected_next_action = {
            "observation_or_detector_target_coverage_gap": "expand_non_oracle_observation_coverage_before_any_trajectory",
            "localization_threshold_gap_with_low_confidence_cap_suppression": "test_relaxed_candidate_rescue_and_stop_region_alignment",
            "cap_or_ranking_suppressed_primary_target_candidate": "test_cap_aware_target_near_rescue_without_eval_leakage",
            "prompt_label_gap": "repair_prompt_label_mapping",
            "render_frame_readiness_gap": "repair_render_frame_staging",
        }.get(dominant_failure_type, "manual_source_gap_diagnosis")

        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_failure_diagnosis",
                "scan_id": scan_id,
                "adapter_episode_id": m90.get("adapter_episode_id"),
                "scene_key": m90.get("scene_key"),
                "object_category": category,
                "m90_distance_failure_class": m90.get("distance_failure_class"),
                "prompt_label_ready": prompt_ready,
                "manifest_target_labels": manifest_by_scan.get(scan_id, {}).get("target_labels"),
                "render_scan_ready": bool(scan_ready),
                "ready_frame_rows": ready_frames,
                "expected_frame_rows": scan_ready_by_scan.get(scan_id, {}).get("expected_frames"),
                "raw_prediction_rows": raw_predictions,
                "selected_prediction_rows": selected_predictions,
                "pre_cap_candidate_rows": summary_by_scan.get(scan_id, {}).get("pre_cap_candidate_rows"),
                "final_candidate_rows": summary_by_scan.get(scan_id, {}).get("detector_candidate_rows"),
                "navmesh_path_ready_rows": path_ready_rows,
                "m89_primary_success_policy_count": m90.get("m89_primary_success_policy_count"),
                "eval_goal_object_id": eval_goal.get("eval_goal_object_id"),
                "eval_viewpoint_count": eval_goal.get("eval_all_viewpoint_count_loaded"),
                "min_observation_pose_to_goal_xz_m": best_obs_goal.get("pose_to_eval_goal_xz_m") if best_obs_goal else None,
                "min_observation_pose_to_first_viewpoint_xz_m": best_obs_first.get("pose_to_eval_first_viewpoint_xz_m") if best_obs_first else None,
                "pre_cap_min_any_viewpoint_xz_m": best_pre_any.get("candidate_to_nearest_eval_viewpoint_xz_m") if best_pre_any else None,
                "pre_cap_min_goal_xz_m": best_pre_goal.get("candidate_to_eval_goal_xz_m") if best_pre_goal else None,
                "pre_cap_any_viewpoint_1p0_hits": pre_primary_hits,
                "pre_cap_any_viewpoint_1p5_hits": pre_relaxed_hits,
                "pre_cap_goal_1p0_hits": pre_goal_hits,
                "best_pre_cap_confidence": best_pre_any.get("confidence") if best_pre_any else None,
                "best_pre_cap_confidence_rank": best_pre_any.get("confidence_rank_within_scan_label") if best_pre_any else None,
                "best_pre_cap_frame_id": best_pre_any.get("frame_id") if best_pre_any else None,
                "best_pre_cap_pose_role": best_pre_any.get("pose_role") if best_pre_any else None,
                "best_pre_cap_route_id": best_pre_any.get("route_id") if best_pre_any else None,
                "best_final_any_viewpoint_xz_m": best_final_any.get("best_any_viewpoint_xz_m") if best_final_any else None,
                "dropped_stage": dropped_stage,
                "dominant_failure_type": dominant_failure_type,
                "selected_next_action": selected_next_action,
                "source_gap_recovery_supported": False,
                "direct_trajectory_promotion_ready": False,
                "claim_boundary": "M91 diagnoses target coverage with eval-only ObjectNav labels; it does not create policy inputs or executed navigation evidence.",
            }
        )
    return out


def build_stage_gate_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates = [
        ("prompt_label_ready", "prompt/category mapping"),
        ("render_scan_ready", "rendered RGB-D frame readiness"),
        ("raw_prediction_rows", "raw detector projection"),
        ("pre_cap_candidate_rows", "pre-cap candidate availability"),
        ("final_candidate_rows", "post-cap candidate availability"),
        ("navmesh_path_ready_rows", "navmesh/path readiness"),
        ("pre_cap_any_viewpoint_1p0_hits", "pre-cap primary target-near coverage"),
        ("pre_cap_any_viewpoint_1p5_hits", "pre-cap relaxed target-near coverage"),
        ("m89_primary_success_policy_count", "final policy primary target-near success"),
    ]
    out: list[dict[str, Any]] = []
    for row in case_rows:
        for field, gate_name in gates:
            value = row.get(field)
            if isinstance(value, bool):
                passed = value
            elif isinstance(value, (int, float)):
                passed = value > 0
            else:
                passed = value is not None
            out.append(
                {
                    "version": VERSION,
                    "row_type": "stage_gate",
                    "scan_id": row.get("scan_id"),
                    "object_category": row.get("object_category"),
                    "gate_id": field,
                    "gate_name": gate_name,
                    "value": value,
                    "passed": passed,
                    "claim_boundary": "Stage gates are diagnostic and use eval labels only for post-hoc target coverage.",
                }
            )
    return out


def build_pre_cap_nearest_rows(pre_cap_eval_rows: list[dict[str, Any]], limit_per_scan: int = 5) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pre_cap_eval_rows:
        grouped[str(row.get("scan_id"))].append(row)
    out: list[dict[str, Any]] = []
    for scan_id, rows in grouped.items():
        valid = [row for row in rows if finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) is not None]
        for rank, row in enumerate(
            sorted(valid, key=lambda item: float(item["candidate_to_nearest_eval_viewpoint_xz_m"]))[:limit_per_scan],
            start=1,
        ):
            out.append(
                {
                    "version": VERSION,
                    "row_type": "pre_cap_nearest_target_candidate",
                    "nearest_target_rank": rank,
                    "scan_id": scan_id,
                    "adapter_episode_id": row.get("adapter_episode_id"),
                    "object_category": row.get("object_category"),
                    "pre_cap_candidate_pool_uid": row.get("pre_cap_candidate_pool_uid"),
                    "raw_candidate_uid": row.get("raw_candidate_uid"),
                    "frame_id": row.get("frame_id"),
                    "observation_pose_id": row.get("observation_pose_id"),
                    "pose_role": row.get("pose_role"),
                    "route_id": row.get("route_id"),
                    "confidence": row.get("confidence"),
                    "confidence_rank_within_scan_label": row.get("confidence_rank_within_scan_label"),
                    "inside_final_label_cap_by_confidence": row.get("inside_final_label_cap_by_confidence"),
                    "candidate_to_nearest_eval_viewpoint_xz_m": row.get("candidate_to_nearest_eval_viewpoint_xz_m"),
                    "candidate_to_eval_goal_xz_m": row.get("candidate_to_eval_goal_xz_m"),
                    "hit_any_viewpoint_xz_1p0": row.get("hit_any_viewpoint_xz_1p0"),
                    "hit_any_viewpoint_xz_1p5": row.get("hit_any_viewpoint_xz_1p5"),
                    "hit_goal_xz_1p0": row.get("hit_goal_xz_1p0"),
                    "claim_boundary": "Nearest pre-cap rows identify candidate-source failure mode; they are not a policy ranking input.",
                }
            )
    return out


def build_repair_option_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failure_counts = Counter(str(row.get("dominant_failure_type")) for row in case_rows)
    return [
        {
            "version": VERSION,
            "route_id": "trajectory_execution_now",
            "decision": "reject",
            "reason": "M91 confirms target-near coverage is missing or suppressed before trajectory execution.",
            "covered_failure_types": [],
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
        },
        {
            "version": VERSION,
            "route_id": "cap_or_ranking_repair_only",
            "decision": "reject_as_complete_repair",
            "reason": "A cap/ranking-only repair can address relaxed low-confidence toilet evidence but cannot recover the sofa case where no pre-cap target-near candidate exists.",
            "covered_failure_types": [
                "localization_threshold_gap_with_low_confidence_cap_suppression",
                "cap_or_ranking_suppressed_primary_target_candidate",
            ],
            "uncovered_failure_types": ["observation_or_detector_target_coverage_gap"],
            "failure_type_counts": dict(failure_counts),
        },
        {
            "version": VERSION,
            "route_id": "observation_coverage_repair_only",
            "decision": "warning_partial",
            "reason": "Observation coverage is necessary for the severe sofa gap, but the toilet case also needs low-confidence/threshold-aware candidate rescue.",
            "covered_failure_types": ["observation_or_detector_target_coverage_gap"],
            "uncovered_failure_types": ["localization_threshold_gap_with_low_confidence_cap_suppression"],
            "failure_type_counts": dict(failure_counts),
        },
        {
            "version": VERSION,
            "route_id": "two_branch_coverage_cap_repair_contract",
            "decision": "select",
            "selected_next_unit": NEXT_UNIT,
            "reason": "The source-gap subset contains both absent pre-cap target coverage and low-confidence relaxed target-near suppression, so the next contract should separate observation coverage repair from cap/threshold rescue.",
            "covered_failure_types": sorted(failure_counts),
            "failure_type_counts": dict(failure_counts),
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_source_gap_failure_taxonomy",
            "supported": True,
            "claim_boundary": "M91 supports a source-gap failure taxonomy over the two M83-M90 source-gap cases.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M91 diagnoses why source-gap recovery failed; it does not recover any case.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M91 is not a Habitat trajectory execution and rejects trajectory promotion now.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M91 covers two source-gap cases only and uses eval-only target labels for post-hoc diagnosis.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    if not ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m91_inputs_or_diagnosis",
                "selected_next_unit": "repair E008-M91 source-gap diagnosis",
                "reason": "Required M84-M90 artifacts are incomplete.",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "source_gap_failure_diagnosis_ready_select_two_branch_repair_contract",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M91 separates severe absent target coverage from relaxed low-confidence/cap suppression; M92 should contract both repair branches before any long job.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    nearest_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> str:
    case_lines = []
    for row in case_rows:
        case_lines.append(
            "| {scan_id} | {object_category} | {ready_frame_rows} | {pre_cap_candidate_rows} | "
            "{pre_cap_any_viewpoint_1p0_hits} / {pre_cap_any_viewpoint_1p5_hits} | "
            "{final_candidate_rows} | {navmesh_path_ready_rows} | {best_final_any_viewpoint_xz_m} | "
            "{dominant_failure_type} |".format(
                scan_id=row.get("scan_id"),
                object_category=row.get("object_category"),
                ready_frame_rows=row.get("ready_frame_rows"),
                pre_cap_candidate_rows=row.get("pre_cap_candidate_rows"),
                pre_cap_any_viewpoint_1p0_hits=row.get("pre_cap_any_viewpoint_1p0_hits"),
                pre_cap_any_viewpoint_1p5_hits=row.get("pre_cap_any_viewpoint_1p5_hits"),
                final_candidate_rows=row.get("final_candidate_rows"),
                navmesh_path_ready_rows=row.get("navmesh_path_ready_rows"),
                best_final_any_viewpoint_xz_m=fmt(row.get("best_final_any_viewpoint_xz_m")),
                dominant_failure_type=row.get("dominant_failure_type"),
            )
        )
    nearest_lines = []
    for row in nearest_rows:
        if int(row.get("nearest_target_rank") or 0) > 3:
            continue
        nearest_lines.append(
            "| {scan_id} | {nearest_target_rank} | {frame_id} | {confidence} | {confidence_rank_within_scan_label} | "
            "{candidate_to_nearest_eval_viewpoint_xz_m} | {candidate_to_eval_goal_xz_m} | {hit_any_viewpoint_xz_1p0} | {hit_any_viewpoint_xz_1p5} |".format(
                scan_id=row.get("scan_id"),
                nearest_target_rank=row.get("nearest_target_rank"),
                frame_id=row.get("frame_id"),
                confidence=fmt(row.get("confidence")),
                confidence_rank_within_scan_label=row.get("confidence_rank_within_scan_label"),
                candidate_to_nearest_eval_viewpoint_xz_m=fmt(row.get("candidate_to_nearest_eval_viewpoint_xz_m")),
                candidate_to_eval_goal_xz_m=fmt(row.get("candidate_to_eval_goal_xz_m")),
                hit_any_viewpoint_xz_1p0=row.get("hit_any_viewpoint_xz_1p0"),
                hit_any_viewpoint_xz_1p5=row.get("hit_any_viewpoint_xz_1p5"),
            )
        )
    selected_repair = next((row for row in repair_rows if row.get("decision") == "select"), {})
    return f"""# E008-M91 Source-Gap Target-Coverage Failure Diagnosis

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M90 status: `{coverage['m90_status']}`.
- Source-gap cases: {coverage['source_gap_case_rows']}.
- Render-ready frames: {coverage['ready_frame_rows']} / {coverage['expected_frame_rows']}.
- Pre-cap candidates: {coverage['pre_cap_candidate_rows']}.
- Final candidates: {coverage['final_candidate_rows']}.
- Cases with pre-cap primary target-near hit: {coverage['cases_with_pre_cap_primary_hit']}.
- Cases with pre-cap relaxed target-near hit: {coverage['cases_with_pre_cap_relaxed_hit']}.
- Cases with final primary hit: {coverage['cases_with_final_primary_hit']}.
- Dominant failure types: `{coverage['dominant_failure_type_counts']}`.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Diagnosis

| scan_id | category | frames | pre-cap | pre-cap 1.0 / 1.5 hits | final | path-ready | final best any-vp XZ m | dominant failure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(case_lines)}

## Nearest Pre-Cap Target Candidates

| scan_id | rank | frame | confidence | confidence rank | nearest any-vp XZ m | goal XZ m | primary hit | relaxed hit |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(nearest_lines)}

## Decision

- Trajectory execution remains rejected.
- Cap/ranking-only repair is not sufficient because the sofa case has no pre-cap target-near candidate.
- Observation coverage-only repair is also incomplete because the toilet case has relaxed low-confidence target-near evidence suppressed before final candidate rows.
- Selected route: `{selected_repair.get('route_id')}` -> `{selected_repair.get('selected_next_unit')}`.

## Claim Boundary

- M91 is a post-hoc failure diagnosis using `ObjectNav` eval-only goal/viewpoint labels.
- M91 does not claim source-gap recovery, deployable search policy, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.
"""


def main() -> None:
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    m70 = load_module(M70_TOOL, "e008_m70_goal_loader")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m84_coverage = read_json(M84_DIR / "coverage.json")
    m85_coverage = read_json(M84_DIR / "m85_verification_coverage.json")
    m86_coverage = read_json(M86_DIR / "e008_m86_verification_coverage.json")
    m90_coverage = read_json(M90_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_DIR / "val_mini_episode_rows.jsonl")
    m90_case_rows = read_jsonl(M90_DIR / "source_gap_case_interpretation_rows.jsonl")
    source_gap_episode_ids = {str(row.get("adapter_episode_id")) for row in m90_case_rows}
    source_gap_episode_rows = [
        row for row in episode_rows if str(row.get("adapter_episode_id")) in source_gap_episode_ids
    ]
    eval_goal_rows = m70.build_full_val_mini_eval_goal_rows(source_gap_episode_rows)
    eval_index_by_episode = m12.build_eval_goal_index(eval_goal_rows)
    eval_index_by_scan = {
        scan_id_from_eval_goal(row): eval_index_by_episode[str(row["adapter_episode_id"])]
        for row in eval_goal_rows
        if str(row.get("adapter_episode_id")) in eval_index_by_episode
    }

    prompt_set = read_json(M84_DIR / "prompt_set.json")
    prompt_labels = {str(row.get("label_canonical")) for row in prompt_set.get("labels", [])}
    manifest_rows = read_jsonl(M84_DIR / "source_gap_detector_manifest_rows.jsonl")
    pose_rows = read_jsonl(M84_DIR / "source_gap_observation_pose_plan_rows.jsonl")
    render_plan_rows = read_jsonl(M84_DIR / "source_gap_render_plan_rows.jsonl")
    frame_rows = read_jsonl(M84_DIR / "verification_frame_rows.jsonl")
    scan_rows = read_jsonl(M84_DIR / "verification_scan_rows.jsonl")
    frame_diag_rows = read_jsonl(M86_DIR / "frame_diagnostics.jsonl")
    summary_rows = read_jsonl(M86_DIR / "e008_m86_candidate_summary_rows.jsonl")
    pre_cap_rows = read_jsonl(M86_DIR / "container_output" / "pre_cap_candidate_pool.jsonl")
    nav_rows = read_jsonl(M87_DIR / "candidate_navmesh_validation_rows.jsonl")
    m89_case_rows = read_jsonl(M89_DIR / "source_gap_case_goal_metric_rows.jsonl")

    render_by_scan_frame = {
        (str(row.get("scan_id")), str(row.get("frame_id"))): row for row in render_plan_rows
    }
    pre_cap_eval_rows = build_pre_cap_candidate_eval_rows(
        pre_cap_rows,
        eval_index_by_scan,
        render_by_scan_frame,
    )
    observation_rows = build_observation_coverage_rows(pose_rows, eval_index_by_episode)
    case_rows = build_case_diagnosis_rows(
        m90_case_rows,
        eval_goal_rows,
        prompt_labels,
        manifest_rows,
        scan_rows,
        frame_rows,
        frame_diag_rows,
        summary_rows,
        nav_rows,
        m89_case_rows,
        pre_cap_eval_rows,
        observation_rows,
    )
    stage_gate_rows = build_stage_gate_rows(case_rows)
    nearest_rows = build_pre_cap_nearest_rows(pre_cap_eval_rows)
    repair_rows = build_repair_option_rows(case_rows)
    claim_rows = build_claim_boundary_rows()

    input_ready = (
        m84_coverage.get("status") == "e008_m84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_ready"
        and m85_coverage.get("status") == "e008_m85_source_gap_render_frame_staging_verified"
        and m86_coverage.get("status") == "e008_m86_source_gap_detector_candidate_source_verified"
        and m90_coverage.get("status") == "e008_m90_source_gap_detector_goal_result_interpretation_trajectory_decision_ready"
        and len(case_rows) == len(m90_case_rows) == 2
    )
    route_rows = build_route_decision_rows(input_ready)
    failure_counts = Counter(str(row.get("dominant_failure_type")) for row in case_rows)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m84_status": m84_coverage.get("status"),
        "m85_status": m85_coverage.get("status"),
        "m86_status": m86_coverage.get("status"),
        "m90_status": m90_coverage.get("status"),
        "source_gap_case_rows": len(case_rows),
        "expected_frame_rows": sum(int(row.get("expected_frames") or 0) for row in scan_rows),
        "ready_frame_rows": sum(int(row.get("ready_frames") or 0) for row in scan_rows),
        "raw_prediction_rows": sum(int(row.get("raw_prediction_count") or 0) for row in frame_diag_rows),
        "pre_cap_candidate_rows": len(pre_cap_rows),
        "pre_cap_candidate_eval_rows": len(pre_cap_eval_rows),
        "final_candidate_rows": int(m86_coverage.get("prediction_rows") or 0),
        "navmesh_candidate_rows": len(nav_rows),
        "cases_with_pre_cap_primary_hit": sum(
            1 for row in case_rows if int(row.get("pre_cap_any_viewpoint_1p0_hits") or 0) > 0
        ),
        "cases_with_pre_cap_relaxed_hit": sum(
            1 for row in case_rows if int(row.get("pre_cap_any_viewpoint_1p5_hits") or 0) > 0
        ),
        "cases_with_final_primary_hit": sum(
            1 for row in case_rows if int(row.get("m89_primary_success_policy_count") or 0) > 0
        ),
        "dominant_failure_type_counts": dict(sorted(failure_counts.items())),
        "direct_trajectory_promotion_ready": False,
        "source_gap_recovery_supported": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    outputs = {
        "coverage.json": coverage,
        "source_gap_failure_diagnosis_rows.jsonl": case_rows,
        "stage_gate_rows.jsonl": stage_gate_rows,
        "pre_cap_nearest_target_candidate_rows.jsonl": nearest_rows,
        "observation_coverage_rows.jsonl": observation_rows,
        "pre_cap_candidate_eval_rows.jsonl": pre_cap_eval_rows,
        "repair_option_rows.jsonl": repair_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
    }
    for name, payload in outputs.items():
        if name.endswith(".json"):
            write_json(ARTIFACT_DIR / name, payload)
            write_json(DATA_OUT_DIR / name, payload)
        else:
            assert isinstance(payload, list)
            write_jsonl(ARTIFACT_DIR / name, payload)
            write_jsonl(DATA_OUT_DIR / name, payload)

    report = build_report(coverage, case_rows, nearest_rows, repair_rows)
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
