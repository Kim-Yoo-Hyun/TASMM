#!/usr/bin/env python3
"""Build the E008-M63 high-path tail-slot scale-up and source-boundary contract."""

from __future__ import annotations

import gzip
import json
import math
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M61_DIR = EXP_ROOT / "artifacts" / "E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0"
M62_DIR = EXP_ROOT / "artifacts" / "E008-M62_high_path_tail_slot_result_interpretation_scale_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M63_high_path_tail_slot_scaleup_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M63_high_path_tail_slot_scaleup_contract_v0"
)

VERSION = "e008_m63_high_path_tail_slot_scaleup_contract_v0"
READY_STATUS = "e008_m63_high_path_tail_slot_scaleup_contract_ready"
BLOCKED_STATUS = "e008_m63_high_path_tail_slot_scaleup_contract_blocked"
NEXT_UNIT = "E008-M64 full-val-mini high-path scale denominator materialization"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
OBJECTNAV_ROOT = (
    RESEARCH2_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
)

TASK_CONTEXTS = ["high_value_fetch", "noisy_high_value_fetch", "routine_fetch"]
FRAMES_PER_EPISODE = 36
CORE_POLICIES = [
    "static_stale_memory_top1_v0",
    "detector_confidence_budget5_v0",
    "fixed_topk_current_observation_budget5_v0",
    "source_diverse_current_observation_budget5_v1",
    "h001_task_conditioned_source_diverse_budget5_v1",
    "h001_task_conditioned_safe_source_diverse_budget5_v2",
    "task_agnostic_source_diverse_budget5_v1",
    "h001_task_conditioned_high_path_tail_slot_budget5_v3",
]
OPTIONAL_POLICY = "h001_source_ready_guarded_tail_slot_budget5_v4"


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
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "NA" if value is None else str(value)


def scene_key_from_scene_id(scene_id: str) -> str:
    parts = scene_id.split("/")
    if len(parts) >= 3:
        return parts[-2]
    return "unknown_scene"


def scene_paths(scene_id: str) -> tuple[Path, Path]:
    rel = scene_id.replace("hm3d_v0.2/", "")
    scene_path = RESEARCH2_DATA_ROOT / "versioned_data" / "hm3d-0.2" / "hm3d" / rel
    navmesh_path = scene_path.with_suffix(".basis.navmesh")
    if not navmesh_path.exists() and scene_path.name.endswith(".basis.glb"):
        navmesh_path = scene_path.with_name(scene_path.name.replace(".basis.glb", ".basis.navmesh"))
    return scene_path, navmesh_path


def load_objectnav_split(split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    content_root = OBJECTNAV_ROOT / split / "content"
    for content_file in sorted(content_root.glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        for episode in payload.get("episodes", []):
            scene_id = str(episode.get("scene_id", ""))
            scene_key = scene_key_from_scene_id(scene_id)
            scene_path, navmesh_path = scene_paths(scene_id)
            rows.append(
                {
                    "split": split,
                    "content_file": content_file.name,
                    "source_episode_id": str(episode.get("episode_id")),
                    "adapter_episode_id": f"{scene_key}::{episode.get('episode_id')}",
                    "scene_id_raw": scene_id,
                    "scene_key": scene_key,
                    "object_category": episode.get("object_category"),
                    "scene_ready": scene_path.exists(),
                    "navmesh_ready": navmesh_path.exists(),
                    "start_position": episode.get("start_position"),
                    "start_rotation": episode.get("start_rotation"),
                    "goals_count": len(episode.get("goals", [])),
                    "info_geodesic_distance": (episode.get("info") or {}).get("geodesic_distance"),
                }
            )
    return rows


def split_inventory_rows(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for split, rows in rows_by_split.items():
        scenes = sorted({str(row["scene_key"]) for row in rows})
        cats = sorted({str(row["object_category"]) for row in rows})
        out.append(
            {
                "version": VERSION,
                "split": split,
                "content_files": len({str(row["content_file"]) for row in rows}),
                "episode_rows": len(rows),
                "scene_count": len(scenes),
                "category_count": len(cats),
                "categories": cats,
                "scene_ready_rows": sum(1 for row in rows if row["scene_ready"]),
                "navmesh_ready_rows": sum(1 for row in rows if row["navmesh_ready"]),
                "all_scene_navmesh_ready": all(row["scene_ready"] and row["navmesh_ready"] for row in rows),
            }
        )
    return out


def build_scale_rows(
    val_mini_rows: list[dict[str, Any]],
    val_rows: list[dict[str, Any]],
    m61_scan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m61_episode_ids = {str(row.get("adapter_episode_id")) for row in m61_scan_rows}
    val_mini_ids = {str(row["adapter_episode_id"]) for row in val_mini_rows}
    holdout_ids = val_mini_ids - m61_episode_ids
    val_mini_categories = sorted({str(row["object_category"]) for row in val_mini_rows})
    m61_categories = sorted({str(row.get("object_category")) for row in m61_scan_rows})
    unseen_categories = sorted(set(val_mini_categories) - set(m61_categories))

    return [
        scale_row(
            "m61_controlled_smoke_seen",
            "completed_reference",
            len(m61_episode_ids),
            len(m61_episode_ids) * len(TASK_CONTEXTS),
            len(m61_episode_ids) * len(TASK_CONTEXTS) * len(CORE_POLICIES),
            len({str(row.get("scene_key")) for row in m61_scan_rows}),
            len(m61_categories),
            "M61/M62 diagnostic reference only; not final claim denominator.",
        ),
        scale_row(
            "val_mini_full_episode_scale",
            "selected_next",
            len(val_mini_ids),
            len(val_mini_ids) * len(TASK_CONTEXTS),
            len(val_mini_ids) * len(TASK_CONTEXTS) * len(CORE_POLICIES),
            len({str(row["scene_key"]) for row in val_mini_rows}),
            len(val_mini_categories),
            "Immediate scale-up denominator. Adds heldout episodes and categories inside local val_mini.",
            holdout_episode_rows=len(holdout_ids),
            expected_render_frames=len(val_mini_ids) * FRAMES_PER_EPISODE,
            optional_policy_rows=len(val_mini_ids) * len(TASK_CONTEXTS),
            with_optional_policy_scan_task_rows=len(val_mini_ids)
            * len(TASK_CONTEXTS)
            * (len(CORE_POLICIES) + 1),
            unseen_categories_from_m61=unseen_categories,
        ),
        scale_row(
            "val_full_scene_transfer_future",
            "future_top_tier_scale",
            len(val_rows),
            len(val_rows) * len(TASK_CONTEXTS),
            len(val_rows) * len(TASK_CONTEXTS) * len(CORE_POLICIES),
            len({str(row["scene_key"]) for row in val_rows}),
            len({str(row["object_category"]) for row in val_rows}),
            "Future heldout scene-scale route for stronger navigation claim; do not launch before val_mini contract is verified.",
            expected_render_frames=len(val_rows) * FRAMES_PER_EPISODE,
            optional_policy_rows=len(val_rows) * len(TASK_CONTEXTS),
            with_optional_policy_scan_task_rows=len(val_rows)
            * len(TASK_CONTEXTS)
            * (len(CORE_POLICIES) + 1),
        ),
    ]


def scale_row(
    denominator_id: str,
    role: str,
    episode_rows: int,
    scan_task_context_rows: int,
    core_scan_task_policy_rows: int,
    scene_count: int,
    category_count: int,
    rationale: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "denominator_id": denominator_id,
        "role": role,
        "episode_rows": episode_rows,
        "task_context_count": len(TASK_CONTEXTS),
        "core_policy_count": len(CORE_POLICIES),
        "scan_task_context_rows": scan_task_context_rows,
        "core_scan_task_policy_rows": core_scan_task_policy_rows,
        "scene_count": scene_count,
        "category_count": category_count,
        "frames_per_episode_plan": FRAMES_PER_EPISODE,
        "rationale": rationale,
        **extra,
    }


def build_split_rows(val_mini_rows: list[dict[str, Any]], m61_scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m61_ids = {str(row.get("adapter_episode_id")) for row in m61_scan_rows}
    val_mini_ids = {str(row["adapter_episode_id"]) for row in val_mini_rows}
    holdout_ids = val_mini_ids - m61_ids

    def categories(ids: set[str]) -> list[str]:
        return sorted({str(row["object_category"]) for row in val_mini_rows if str(row["adapter_episode_id"]) in ids})

    return [
        {
            "version": VERSION,
            "split_id": "seen_m61_reference",
            "split_role": "diagnostic_reference_not_train",
            "episode_rows": len(m61_ids),
            "scan_task_context_rows": len(m61_ids) * len(TASK_CONTEXTS),
            "categories": categories(m61_ids),
            "use_for_claim": "reference_only",
        },
        {
            "version": VERSION,
            "split_id": "val_mini_unseen_episode_holdout",
            "split_role": "first_scale_eval",
            "episode_rows": len(holdout_ids),
            "scan_task_context_rows": len(holdout_ids) * len(TASK_CONTEXTS),
            "categories": categories(holdout_ids),
            "use_for_claim": "bounded_scale_eval",
        },
        {
            "version": VERSION,
            "split_id": "val_full_scene_transfer_future",
            "split_role": "future_scene_transfer",
            "episode_rows": None,
            "scan_task_context_rows": None,
            "categories": "see_objectnav_source_inventory_rows",
            "use_for_claim": "final_navigation_claim_candidate_only_after_external_baseline_plan",
        },
    ]


def build_policy_suite_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy_id in CORE_POLICIES:
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_status": "required_for_m64",
                "policy_role": policy_role(policy_id),
                "candidate_budget": 1 if policy_id == "static_stale_memory_top1_v0" else 5,
                "source_boundary_required": True,
                "full_aggregate_required": True,
                "allowed_for_main_claim": policy_id == "h001_task_conditioned_high_path_tail_slot_budget5_v3",
            }
        )
    rows.append(
        {
            "version": VERSION,
            "policy_id": OPTIONAL_POLICY,
            "policy_status": "optional_guard_policy_requires_policy_visible_trigger",
            "policy_role": "source_ready_efficiency_ablation",
            "candidate_budget": 5,
            "source_boundary_required": True,
            "full_aggregate_required": True,
            "allowed_for_main_claim": False,
            "guard_constraint": "must_not_use_ObjectNav_goal_viewpoints_success_labels_or_diagnostic_source_gap_boundary_as_policy_input",
        }
    )
    return rows


def policy_role(policy_id: str) -> str:
    if policy_id == "h001_task_conditioned_high_path_tail_slot_budget5_v3":
        return "method_candidate"
    if policy_id == "h001_task_conditioned_safe_source_diverse_budget5_v2":
        return "base_h001_ablation"
    if policy_id == "task_agnostic_source_diverse_budget5_v1":
        return "task_agnostic_ablation"
    if policy_id in {"detector_confidence_budget5_v0", "fixed_topk_current_observation_budget5_v0"}:
        return "current_observation_baseline"
    if policy_id == "static_stale_memory_top1_v0":
        return "static_memory_lower_bound"
    return "supporting_baseline"


def build_source_boundary_guard_rows(m62_source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    regression = [
        row
        for row in m62_source_rows
        if row.get("row_type") == "h001_source_boundary_delta"
        and row.get("source_boundary") == "source_ready"
        and row.get("source_ready_efficiency_regression")
    ]
    return [
        {
            "version": VERSION,
            "guard_id": "mandatory_source_boundary_reporting",
            "guard_status": "required",
            "rationale": "Report source_ready and source_gap separately in every M64/M65 table.",
            "pass_condition": "all_policy_rows_have_full_source_ready_source_gap_metrics",
        },
        {
            "version": VERSION,
            "guard_id": "source_ready_no_success_loss",
            "guard_status": "required",
            "rationale": "H001 high-path must not lose source-ready SR against detector/fixed baselines.",
            "pass_condition": "h001_source_ready_SR >= detector_source_ready_SR and h001_source_ready_SR >= fixed_source_ready_SR",
        },
        {
            "version": VERSION,
            "guard_id": "source_ready_efficiency_guard",
            "guard_status": "warning_required",
            "m62_regression_rows": len(regression),
            "rationale": "M62 shows source-ready SPL regression against detector/fixed; M64 must either remove it with a policy-visible guard or keep the claim restricted to recovery/efficiency tradeoff.",
            "pass_condition": "h001_source_ready_SPL >= detector_source_ready_SPL or claim_boundary_marks_tradeoff",
        },
        {
            "version": VERSION,
            "guard_id": "source_gap_recovery_primary",
            "guard_status": "required",
            "rationale": "The strongest M62 evidence is source-gap recovery; scale-up must preserve this as a separate primary row.",
            "pass_condition": "h001_source_gap_SR > detector_source_gap_SR and h001_source_gap_SR > task_agnostic_source_gap_SR",
        },
        {
            "version": VERSION,
            "guard_id": "no_eval_boundary_as_policy_input",
            "guard_status": "required",
            "rationale": "diagnostic_source_gap_boundary is reporting-only and must not trigger policy decisions.",
            "pass_condition": "leakage_audit_has_zero_blocked_field_hits",
        },
    ]


def build_baseline_plan_rows() -> list[dict[str, Any]]:
    return [
        baseline("static_stale_memory_top1_v0", "internal_required", "lower_bound", "M64"),
        baseline("detector_confidence_budget5_v0", "internal_required", "current_observation_efficiency", "M64"),
        baseline("fixed_topk_current_observation_budget5_v0", "internal_required", "simple_current_observation", "M64"),
        baseline("source_diverse_current_observation_budget5_v1", "internal_required", "current_source_diversity", "M64"),
        baseline("task_agnostic_source_diverse_budget5_v1", "internal_required", "task_context_ablation", "M64"),
        baseline("h001_task_conditioned_safe_source_diverse_budget5_v2", "internal_required", "base_h001_ablation", "M64"),
        baseline("Habitat_oracle_shortest_path_upper_bound", "metric_required", "upper_bound", "M64_or_M65"),
        baseline("VLFM", "external_future", "navigation_search_baseline", "after_M64_contract_verified"),
        baseline("HM3D-OVON_modular_baseline", "external_future", "open_vocabulary_navigation_baseline", "after_M64_contract_verified"),
        baseline("GOAT-Bench_modular_baseline", "external_future", "generalist_navigation_task_baseline", "future_direction_B"),
        baseline("ConceptGraphs_map_candidate_route", "external_mapping_bridge", "map_memory_baseline", "connect_E005_E007_to_E008_after_M64"),
    ]


def baseline(baseline_id: str, status: str, role: str, earliest_unit: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "baseline_id": baseline_id,
        "baseline_status": status,
        "baseline_role": role,
        "earliest_unit": earliest_unit,
        "claim_boundary": "external_future baselines are not required to launch in M63",
    }


def build_input_contract_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed = [
        "RGBD_frames_from_non_oracle_start_neighborhood_policy",
        "detector_confidence_and_depth_projection_fields",
        "candidate_source_role_and_path_cost_fields",
        "task_context_id_as_structured_memory_trust_condition",
        "policy_visible_full_pool_candidate_features",
        "episode_start_pose_and_scene_navmesh_for_path_execution",
    ]
    blocked = [
        "ObjectNav_goal_position_as_policy_input",
        "ObjectNav_viewpoints_as_policy_input",
        "success_labels_or_stop_success_as_policy_input",
        "diagnostic_source_gap_boundary_as_policy_trigger",
        "candidate_distance_to_eval_goal_before_stop",
        "heldout_split_membership_as_policy_input",
    ]
    allowed_rows = [
        {"version": VERSION, "input_id": item, "input_status": "allowed", "rationale": "policy_visible_or_execution_source"}
        for item in allowed
    ]
    blocked_rows = [
        {"version": VERSION, "input_id": item, "input_status": "blocked", "rationale": "would_leak_eval_or_split_information"}
        for item in blocked
    ]
    return allowed_rows, blocked_rows


def build_m64_plan_rows(scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = next(row for row in scale_rows if row["denominator_id"] == "val_mini_full_episode_scale")
    return [
        {
            "version": VERSION,
            "step_id": "m64_episode_denominator_materialization",
            "output": "episode_task_context_rows",
            "expected_rows": selected["scan_task_context_rows"],
            "requires_docker": False,
            "long_job": False,
        },
        {
            "version": VERSION,
            "step_id": "m64_candidate_source_plan",
            "output": "render_detector_candidate_source_plan",
            "expected_render_frames": selected["expected_render_frames"],
            "requires_docker": False,
            "long_job": False,
        },
        {
            "version": VERSION,
            "step_id": "m64_policy_plan_materialization",
            "output": "core_policy_execution_plan_rows",
            "expected_rows": selected["core_scan_task_policy_rows"],
            "requires_docker": False,
            "long_job": False,
        },
        {
            "version": VERSION,
            "step_id": "m65_or_later_docker_execution",
            "output": "Habitat_trajectory_rows",
            "expected_rows": selected["core_scan_task_policy_rows"],
            "requires_docker": True,
            "long_job": True,
            "launch_in_m63": False,
        },
    ]


def build_gate_rows(
    coverage_m62: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    inventory = {row["split"]: row for row in inventory_rows}
    selected = next(row for row in scale_rows if row["denominator_id"] == "val_mini_full_episode_scale")
    return [
        gate("m62_ready", coverage_m62.get("status") == "e008_m62_high_path_tail_slot_result_interpretation_scale_decision_ready", "M62 interpretation artifact is ready."),
        gate("diagnostic_table_ready", bool(coverage_m62.get("diagnostic_navigation_table_ready")), "M62 diagnostic navigation table is ready."),
        gate("source_ready_warning_recorded", bool(coverage_m62.get("source_ready_efficiency_warning")), "Source-ready efficiency warning is explicitly recorded."),
        gate("val_mini_episode_source_ready", inventory.get("val_mini", {}).get("episode_rows") == 30, "Local val_mini has 30 ObjectNav episodes."),
        gate("val_mini_navmesh_ready", bool(inventory.get("val_mini", {}).get("all_scene_navmesh_ready")), "All val_mini episodes have scene and navmesh paths."),
        gate("scale_denominator_expands_rows", selected["scan_task_context_rows"] > 18, "Selected denominator expands from 18 to 90 scan-task contexts."),
        gate("heldout_episode_split_defined", selected.get("holdout_episode_rows") == 24, "Unseen val_mini episode split is defined."),
        gate("external_navigation_baselines_integrated", False, "VLFM/HM3D-OVON/GOAT-Bench baselines are planned but not integrated."),
        gate("ready_to_launch_long_job_now", False, "M63 is a contract unit; no Docker long job is launched."),
    ]


def gate(gate_id: str, passed: bool, rationale: str) -> dict[str, Any]:
    return {
        "version": VERSION,
        "gate_id": gate_id,
        "gate_status": "pass" if passed else "fail",
        "rationale": rationale,
        "blocks_m64_contract": gate_id
        in {"m62_ready", "diagnostic_table_ready", "val_mini_episode_source_ready", "val_mini_navmesh_ready"}
        and not passed,
        "blocks_final_navigation_claim": gate_id in {"external_navigation_baselines_integrated", "ready_to_launch_long_job_now"} or not passed,
    }


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        claim("m63_scaleup_contract", True, "M63 fixes the scale denominator, source-boundary reporting, and next materialization route."),
        claim("bounded_diagnostic_navigation_table", True, "M62 table remains usable as bounded diagnostic evidence."),
        claim("full_val_mini_navigation_claim", False, "Requires M64 materialization and Docker trajectory execution."),
        claim("heldout_scene_transfer_claim", False, "Requires val or other scene-heldout denominator and external navigation baselines."),
        claim("source_ready_no_regression_claim", False, "M62 shows source-ready SPL regression; M64 must report or repair it."),
        claim("human_intent_main_claim", False, "Task context remains structured memory-trust condition only."),
    ]


def claim(claim_id: str, supported: bool, boundary: str) -> dict[str, Any]:
    return {"version": VERSION, "claim_id": claim_id, "supported": supported, "claim_boundary": boundary}


def build_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "m64_full_val_mini_materialization_first",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "rationale": "Scale the denominator to all local val_mini episodes before another Docker execution.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "launch_full_val_mini_docker_now",
            "selected": False,
            "selected_next_unit": None,
            "rationale": "Do not launch a long Docker trajectory job until M64 materializes rows and verifies policy/input leakage.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "jump_to_val_full_scene_transfer",
            "selected": False,
            "selected_next_unit": None,
            "rationale": "val full has 1000 episodes and 36 scenes; use after val_mini scale contract is verified.",
            "launch_long_job_now": False,
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    coverage: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M63 High-Path Tail-Slot Scale-Up Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Selected scale denominator: `{coverage['selected_denominator_id']}`.",
        f"- Selected episode rows: {coverage['selected_episode_rows']}.",
        f"- Selected scan-task context rows: {coverage['selected_scan_task_context_rows']}.",
        f"- Selected core scan-task-policy rows: {coverage['selected_core_scan_task_policy_rows']}.",
        f"- Expected render frames: {coverage['selected_expected_render_frames']}.",
        f"- Source-ready efficiency warning carried from M62: {coverage['source_ready_efficiency_warning']}.",
        f"- Launch long job now: {coverage['launch_long_job_now']}.",
        "",
        "## Source Inventory",
        "",
        markdown_table(inventory_rows, ["split", "content_files", "episode_rows", "scene_count", "category_count", "all_scene_navmesh_ready"]),
        "",
        "## Scale Denominators",
        "",
        markdown_table(scale_rows, ["denominator_id", "role", "episode_rows", "scan_task_context_rows", "core_scan_task_policy_rows", "scene_count", "category_count"]),
        "",
        "## Source Boundary Guards",
        "",
        markdown_table(guard_rows, ["guard_id", "guard_status", "pass_condition"]),
        "",
        "## Baseline Plan",
        "",
        markdown_table(baseline_rows, ["baseline_id", "baseline_status", "baseline_role", "earliest_unit"]),
        "",
        "## Readiness Gates",
        "",
        markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m64_contract", "blocks_final_navigation_claim"]),
        "",
        "## Decision",
        "",
    ]
    for row in route_rows:
        lines.append(f"- `{row['route_id']}` selected={row['selected']}: {row['rationale']}")
    lines.extend(
        [
            "",
            "M63 is a contract unit. It does not launch Docker execution and does not promote final real navigation, deployable search, real RGB-D/open-vocabulary robustness, or human-intent main claims.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    coverage_m62 = read_json(M62_DIR / "coverage.json")
    m61_metric_rows = read_jsonl(M61_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    m61_scan_rows = [row for row in m61_metric_rows if row.get("metric_scope") == "scan_task_policy"]
    m62_source_rows = read_jsonl(M62_DIR / "source_boundary_rows.jsonl")

    val_mini_rows = load_objectnav_split("val_mini")
    val_rows = load_objectnav_split("val")
    rows_by_split = {"val_mini": val_mini_rows, "val": val_rows}
    inventory_rows = split_inventory_rows(rows_by_split)
    scale_rows = build_scale_rows(val_mini_rows, val_rows, m61_scan_rows)
    split_rows = build_split_rows(val_mini_rows, m61_scan_rows)
    policy_rows = build_policy_suite_rows()
    guard_rows = build_source_boundary_guard_rows(m62_source_rows)
    baseline_rows = build_baseline_plan_rows()
    allowed_rows, blocked_rows = build_input_contract_rows()
    m64_rows = build_m64_plan_rows(scale_rows)
    gate_rows = build_gate_rows(coverage_m62, inventory_rows, scale_rows)
    claim_rows = build_claim_rows()
    route_rows = build_route_rows()

    m64_blocked = any(row["blocks_m64_contract"] for row in gate_rows)
    selected = next(row for row in scale_rows if row["denominator_id"] == "val_mini_full_episode_scale")
    status = READY_STATUS if not m64_blocked else BLOCKED_STATUS
    val_mini_cats = sorted({str(row["object_category"]) for row in val_mini_rows})
    m61_cats = sorted({str(row.get("object_category")) for row in m61_scan_rows})

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m62_status": coverage_m62.get("status"),
        "m62_diagnostic_navigation_table_ready": coverage_m62.get("diagnostic_navigation_table_ready"),
        "source_ready_efficiency_warning": coverage_m62.get("source_ready_efficiency_warning"),
        "selected_denominator_id": selected["denominator_id"],
        "selected_episode_rows": selected["episode_rows"],
        "selected_scan_task_context_rows": selected["scan_task_context_rows"],
        "selected_core_scan_task_policy_rows": selected["core_scan_task_policy_rows"],
        "selected_with_optional_policy_scan_task_rows": selected["with_optional_policy_scan_task_rows"],
        "selected_expected_render_frames": selected["expected_render_frames"],
        "selected_holdout_episode_rows": selected["holdout_episode_rows"],
        "selected_scene_count": selected["scene_count"],
        "selected_category_count": selected["category_count"],
        "m61_seen_episode_rows": len({str(row.get("adapter_episode_id")) for row in m61_scan_rows}),
        "m61_seen_categories": m61_cats,
        "val_mini_categories": val_mini_cats,
        "val_mini_unseen_categories_from_m61": sorted(set(val_mini_cats) - set(m61_cats)),
        "inventory_rows": len(inventory_rows),
        "scale_denominator_rows": len(scale_rows),
        "split_plan_rows": len(split_rows),
        "policy_suite_rows": len(policy_rows),
        "baseline_plan_rows": len(baseline_rows),
        "source_boundary_guard_rows": len(guard_rows),
        "readiness_gate_pass_rows": sum(1 for row in gate_rows if row["gate_status"] == "pass"),
        "readiness_gate_fail_rows": sum(1 for row in gate_rows if row["gate_status"] == "fail"),
        "m64_contract_ready": status == READY_STATUS,
        "launch_long_job_now": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if status == READY_STATUS else None,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "objectnav_source_inventory_rows.jsonl", inventory_rows)
    write_jsonl(ARTIFACT_DIR / "scale_denominator_contract_rows.jsonl", scale_rows)
    write_jsonl(ARTIFACT_DIR / "split_plan_rows.jsonl", split_rows)
    write_jsonl(ARTIFACT_DIR / "policy_suite_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_guard_rows.jsonl", guard_rows)
    write_jsonl(ARTIFACT_DIR / "baseline_plan_rows.jsonl", baseline_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_contract_rows.jsonl", allowed_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "m64_materialization_plan_rows.jsonl", m64_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_report(coverage, inventory_rows, scale_rows, guard_rows, baseline_rows, gate_rows, route_rows)

    for filename in [
        "coverage.json",
        "objectnav_source_inventory_rows.jsonl",
        "scale_denominator_contract_rows.jsonl",
        "split_plan_rows.jsonl",
        "policy_suite_rows.jsonl",
        "source_boundary_guard_rows.jsonl",
        "baseline_plan_rows.jsonl",
        "allowed_input_contract_rows.jsonl",
        "blocked_input_rows.jsonl",
        "m64_materialization_plan_rows.jsonl",
        "readiness_gate_rows.jsonl",
        "claim_boundary_rows.jsonl",
        "route_decision_rows.jsonl",
        "report.md",
    ]:
        shutil.copy2(ARTIFACT_DIR / filename, DATA_OUT_DIR / filename)

    print(json.dumps({"status": status, "selected_next_unit": coverage["selected_next_unit"]}, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
