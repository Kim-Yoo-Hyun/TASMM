#!/usr/bin/env python3
"""Fix the E008-M24 H001 candidate-source instantiation contract."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M24_h001_candidate_source_instantiation_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M24_h001_candidate_source_instantiation_contract_v0"
VERSION = "e008_m24_h001_candidate_source_instantiation_contract_v0"

M03_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M10_DIR = EXP_ROOT / "artifacts" / "E008-M10_detector_candidate_navmesh_validation_v0"
M17_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M22_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M23_DIR = EXP_ROOT / "artifacts" / "E008-M23_trajectory_proxy_consistency_h001_source_decision_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key)) for row in rows))


def path_ready_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("navmesh_validation_status") == "candidate_path_ready")


def scan_count(rows: list[dict[str, Any]]) -> int:
    return len({str(row.get("scan_id")) for row in rows if row.get("scan_id")})


def any_leakage(rows: list[dict[str, Any]]) -> bool:
    return any(bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint")) for row in rows)


def build_candidate_source_schema_rows() -> list[dict[str, Any]]:
    fields = [
        ("source_row_uid", "string", True, True, "Unique id for the materialized H001 source row."),
        ("adapter_episode_id", "string", True, True, "Episode join key from E008-M02/M03."),
        ("scan_id", "string", True, True, "Detector/navigation scan id used by E008 artifacts."),
        ("scene_key", "string", True, True, "HM3D scene key."),
        ("object_category", "string", True, True, "ObjectNav category/query label."),
        ("task_context_id", "enum", True, True, "Structured context such as routine/high-value/noisy-high-value fetch."),
        ("source_role", "enum", True, True, "initial_memory_proxy, current_observation, external_map, or eval_oracle."),
        ("source_stage", "enum", True, True, "initial_start_pose_yaw_sweep_v0 or expanded_non_oracle_multiview_v0."),
        ("proposal_uid", "string", True, True, "Detector/map proposal id generated before policy execution."),
        ("raw_candidate_uid", "string", False, True, "Detector raw candidate id before consolidation."),
        ("label_canonical", "string", True, True, "Canonical detector/map label."),
        ("candidate_position_m", "float[3]", True, True, "Candidate centroid or snapped stop position."),
        ("candidate_stop_position_m", "float[3]", True, True, "Navigable candidate stop point when available."),
        ("candidate_confidence", "float", False, True, "Detector/map confidence produced before policy execution."),
        ("selection_score", "float", False, True, "Pre-execution selection score."),
        ("path_ready", "bool", True, True, "Whether the candidate can be reached from the current source pose."),
        ("source_to_candidate_path_cost_m", "float", False, True, "Pre-execution path cost to the candidate if path-ready."),
        ("memory_age_stage", "enum", True, True, "initial_snapshot or current_reobservation; proxy only on HM3D."),
        ("staleness_proxy_score", "float", False, True, "Derived only from source stage and non-eval evidence."),
        ("memory_trust_feature_group", "string", False, True, "Feature group consumed by H001 trust policy."),
        ("eval_goal_position", "float[3]", False, False, "ObjectNav target position; metric-only."),
        ("eval_viewpoint_position", "float[3]", False, False, "ObjectNav target viewpoint; metric-only."),
        ("candidate_to_eval_goal_distance", "float", False, False, "Post-hoc evaluation distance."),
        ("success_label", "bool", False, False, "Post-hoc execution success."),
    ]
    return [
        {
            "version": VERSION,
            "field": field,
            "type": typ,
            "required_for_materialization": required,
            "allowed_for_policy_input": allowed,
            "description": description,
        }
        for field, typ, required, allowed, description in fields
    ]


def build_task_context_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts = [
        {
            "task_context_id": "routine_fetch",
            "success_reward": 1.0,
            "check_cost": 1.0,
            "failure_cost": 1.0,
            "max_candidate_budget": 3,
            "trust_threshold_role": "conservative_budget",
        },
        {
            "task_context_id": "high_value_fetch",
            "success_reward": 5.0,
            "check_cost": 1.0,
            "failure_cost": 5.0,
            "max_candidate_budget": 5,
            "trust_threshold_role": "recall_oriented_budget",
        },
        {
            "task_context_id": "noisy_high_value_fetch",
            "success_reward": 5.0,
            "check_cost": 1.0,
            "failure_cost": 8.0,
            "max_candidate_budget": 5,
            "trust_threshold_role": "reobserve_oriented_budget",
        },
    ]
    rows = []
    for episode in episode_rows:
        for context in contexts:
            rows.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": episode.get("adapter_episode_id"),
                    "scan_id": episode.get("scan_id"),
                    "scene_key": episode.get("scene_key"),
                    "object_category": episode.get("object_category"),
                    **context,
                    "allowed_for_policy_input": True,
                    "claim_boundary": "structured_task_context_not_natural_language_intent",
                }
            )
    return rows


def build_source_availability_rows(
    m03_sources: list[dict[str, Any]],
    m10_rows: list[dict[str, Any]],
    m17_rows: list[dict[str, Any]],
    m18_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m03_by_source = {str(row.get("candidate_source")): row for row in m03_sources}
    return [
        {
            "version": VERSION,
            "source_role": "eval_oracle",
            "source_id": "ObjectNav eval goals",
            "source_artifact": str(M03_DIR / "episode_goal_eval_rows.jsonl"),
            "rows_ready": len(episode_rows),
            "path_ready_rows": 0,
            "episode_rows": len(episode_rows),
            "policy_input_allowed": False,
            "materializable_as_h001_source": False,
            "status": "ready_eval_only",
            "claim_boundary": "ObjectNav goals/viewpoints are metric-only and must not instantiate memory candidates.",
            "m03_status": m03_by_source.get("ObjectNav eval goals", {}).get("status"),
        },
        {
            "version": VERSION,
            "source_role": "initial_memory_proxy",
            "source_id": "initial_start_pose_yaw_sweep_detector_candidates",
            "source_artifact": str(M10_DIR / "candidate_navmesh_rows.jsonl"),
            "rows_ready": len(m10_rows),
            "path_ready_rows": path_ready_count(m10_rows),
            "episode_rows": scan_count(m10_rows),
            "policy_input_allowed": True,
            "materializable_as_h001_source": bool(m10_rows),
            "status": "source_rows_available_proxy_not_true_stale_memory",
            "claim_boundary": "This is an initial observation memory proxy on static HM3D, not a true dynamic stale-memory source.",
            "m03_status": m03_by_source.get("stale_memory_candidates", {}).get("status"),
        },
        {
            "version": VERSION,
            "source_role": "current_observation",
            "source_id": "expanded_non_oracle_multiview_detector_candidates",
            "source_artifact": str(M17_DIR / "candidate_navmesh_rows.jsonl"),
            "rows_ready": len(m17_rows),
            "path_ready_rows": path_ready_count(m17_rows),
            "episode_rows": scan_count(m17_rows),
            "policy_input_allowed": True,
            "materializable_as_h001_source": bool(m17_rows),
            "status": "source_rows_available",
            "claim_boundary": "Current observation candidates are non-oracle detector outputs; they support H001 source instantiation but not final robustness.",
            "m03_status": m03_by_source.get("current_observation_candidates", {}).get("status"),
        },
        {
            "version": VERSION,
            "source_role": "detector_baseline",
            "source_id": "expanded_detector_visit_order_rows",
            "source_artifact": str(M18_DIR / "candidate_visit_order_rows.jsonl"),
            "rows_ready": len(m18_rows),
            "path_ready_rows": sum(1 for row in m18_rows if row.get("path_ready")),
            "episode_rows": scan_count(m18_rows),
            "policy_input_allowed": True,
            "materializable_as_h001_source": True,
            "status": "already_used_by_detector_policy_smoke",
            "claim_boundary": "This supports detector-policy baselines and candidate ordering, not H001 memory trust by itself.",
            "m03_status": m03_by_source.get("hm3d_rgbd_detector_candidates", {}).get("status"),
        },
        {
            "version": VERSION,
            "source_role": "external_map",
            "source_id": "hm3d_external_map_candidates",
            "source_artifact": "",
            "rows_ready": 0,
            "path_ready_rows": 0,
            "episode_rows": 0,
            "policy_input_allowed": True,
            "materializable_as_h001_source": False,
            "status": "missing_for_hm3d",
            "claim_boundary": "ConceptGraphs/Open3DSG/HOV-SG style HM3D map candidates are not yet available.",
            "m03_status": m03_by_source.get("hm3d_external_map_candidates", {}).get("status"),
        },
        {
            "version": VERSION,
            "source_role": "runtime_event",
            "source_id": "observed_miss_after_h001_queue_exhaustion",
            "source_artifact": "",
            "rows_ready": 0,
            "path_ready_rows": 0,
            "episode_rows": 0,
            "policy_input_allowed": True,
            "materializable_as_h001_source": False,
            "status": "requires_h001_execution_runner",
            "claim_boundary": "Observed miss can only be produced by execution, not by ObjectNav goal labels.",
            "m03_status": m03_by_source.get("observed_miss_runtime_event", {}).get("status"),
        },
    ]


def build_policy_contract_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_ready = {row["source_role"]: bool(row["materializable_as_h001_source"]) for row in source_rows}
    specs = [
        (
            "real_static_memory_proxy_v0",
            "static_stale_memory",
            ["initial_memory_proxy"],
            "visit initial memory proxy candidates by source confidence/rank",
            "baseline_ready_proxy_not_true_stale",
        ),
        (
            "real_detector_confidence_expanded_v0",
            "detector_confidence_ranking",
            ["current_observation"],
            "visit expanded current-observation candidates by confidence",
            "already_smoked_by_m22_detector_policy",
        ),
        (
            "real_context_agnostic_memory_trust_reobserve_v0",
            "context_agnostic_memory_trust",
            ["initial_memory_proxy", "current_observation"],
            "compare initial memory proxy and current observation without task utility",
            "ready_for_materialization_runner_missing",
        ),
        (
            "h001_real_task_context_memory_trust_v0",
            "h001_memory_trust",
            ["initial_memory_proxy", "current_observation"],
            "condition memory trust and re-observation on structured task context",
            "ready_for_materialization_runner_missing",
        ),
        (
            "h001_then_external_map_after_observed_miss_v0",
            "h001_plus_external_map_fallback",
            ["initial_memory_proxy", "current_observation", "external_map", "runtime_event"],
            "run H001 queue first, then external map candidates after observed miss",
            "blocked_external_map_and_runtime_event_missing",
        ),
    ]
    rows = []
    for policy_id, family, required_sources, order_contract, status_if_ready in specs:
        ready = all(source_ready.get(source, False) for source in required_sources)
        if "external_map" in required_sources or "runtime_event" in required_sources:
            ready = False
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_family": family,
                "required_source_roles": required_sources,
                "candidate_visit_order_contract": order_contract,
                "source_inputs_ready": ready,
                "execution_runner_ready": False,
                "policy_execution_ready": False,
                "status": status_if_ready if ready else "blocked_missing_required_source_or_runner",
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M24 fixes source contract only; no H001 navigation performance is claimed.",
            }
        )
    return rows


def build_leakage_guard_rows() -> list[dict[str, Any]]:
    allowed = [
        ("object_category", "ObjectNav query category is available before action."),
        ("scene_key", "Scene identity is needed for simulator/map loading."),
        ("episode_start_pose", "Start pose is part of the navigation episode."),
        ("initial_start_pose_yaw_sweep_candidates", "Generated from non-oracle start-pose observations."),
        ("expanded_non_oracle_multiview_candidates", "Generated from bounded non-oracle observation expansion."),
        ("confidence_selection_score", "Produced by detector before metric evaluation."),
        ("navmesh_reachability_to_candidate", "Candidate path cost is available from map/navmesh before success evaluation."),
        ("task_context_id", "Structured task context is a policy input; not natural-language parsing."),
    ]
    blocked = [
        ("ObjectNav eval_goal_position", "Ground-truth target position."),
        ("ObjectNav eval_viewpoints", "Ground-truth target viewpoints."),
        ("candidate_to_eval_goal_distance", "Post-hoc distance to answer."),
        ("candidate_to_eval_viewpoint_distance", "Post-hoc distance to answer viewpoint."),
        ("M19 primary_hit", "Success label from goal-evaluation proxy."),
        ("M22 trajectory_success", "Execution success label."),
        ("M22 success_proposal_uid", "Answer-revealing stop id."),
        ("oracle_viewpoint_path_m", "Shortest path to target viewpoint."),
    ]
    rows = []
    for field, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "policy_input": "allowed",
                "reason": reason,
            }
        )
    for field, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "policy_input": "blocked",
                "reason": reason,
            }
        )
    return rows


def build_materialization_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "step": "materialize_initial_memory_proxy_rows",
            "input_artifact": str(M10_DIR / "candidate_navmesh_rows.jsonl"),
            "output_file": "h001_candidate_source_rows.jsonl",
            "source_role": "initial_memory_proxy",
            "selected_next_unit": "E008-M25 H001 candidate-source materialization smoke",
            "reason": "Convert initial start-pose detector candidates to a memory-proxy source without using ObjectNav target labels.",
        },
        {
            "version": VERSION,
            "step": "materialize_current_observation_rows",
            "input_artifact": str(M17_DIR / "candidate_navmesh_rows.jsonl"),
            "output_file": "h001_candidate_source_rows.jsonl",
            "source_role": "current_observation",
            "selected_next_unit": "E008-M25 H001 candidate-source materialization smoke",
            "reason": "Convert expanded non-oracle detector candidates to current-evidence source rows.",
        },
        {
            "version": VERSION,
            "step": "materialize_task_context_rows",
            "input_artifact": str(M03_DIR / "episode_goal_eval_rows.jsonl"),
            "output_file": "h001_query_context_rows.jsonl",
            "source_role": "task_context",
            "selected_next_unit": "E008-M25 H001 candidate-source materialization smoke",
            "reason": "Attach structured task context to episodes without claiming natural-language intent understanding.",
        },
        {
            "version": VERSION,
            "step": "write_policy_execution_plan",
            "input_artifact": "h001_candidate_source_rows.jsonl + h001_query_context_rows.jsonl",
            "output_file": "h001_policy_execution_plan_rows.jsonl",
            "source_role": "policy_plan",
            "selected_next_unit": "E008-M25 H001 candidate-source materialization smoke",
            "reason": "Prepare M26 trajectory runner inputs while keeping policy and metric fields separated.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "HM3D can instantiate non-leaking H001 candidate-source rows.",
            "status": "contract_supported",
            "boundary": "M24 proves source ingredients and schema, not policy execution.",
        },
        {
            "version": VERSION,
            "claim": "Initial HM3D observation candidates are true stale semantic memory.",
            "status": "not_supported",
            "boundary": "They are an initial-memory proxy on static HM3D; dynamic stale-memory evidence still comes from 3RScan/3DSSG.",
        },
        {
            "version": VERSION,
            "claim": "H001 improves real navigation SR/SPL.",
            "status": "not_supported",
            "boundary": "No H001 policy trajectory rows exist yet.",
        },
        {
            "version": VERSION,
            "claim": "ObjectNav target goals can be used to create memory candidates.",
            "status": "rejected",
            "boundary": "ObjectNav goals/viewpoints are evaluation-only fields.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    source_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> str:
    source_table = "\n".join(
        f"| {row['source_role']} | {row['rows_ready']} | {row['path_ready_rows']} | {row['status']} | {row['claim_boundary']} |"
        for row in source_rows
    )
    policy_table = "\n".join(
        f"| {row['policy_id']} | {', '.join(row['required_source_roles'])} | {row['source_inputs_ready']} | {row['status']} |"
        for row in policy_rows
    )
    leakage_table = "\n".join(
        f"| {row['field']} | {row['policy_input']} | {row['reason']} |" for row in leakage_rows
    )
    return f"""# E008-M24 H001 Candidate-Source Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Initial memory-proxy candidate rows: {coverage['initial_memory_proxy_candidate_rows']}.
- Current-observation candidate rows: {coverage['current_observation_candidate_rows']}.
- Materialization input-ready: {coverage['h001_candidate_source_materialization_inputs_ready']}.
- H001 candidate-source rows ready now: {coverage['h001_candidate_source_rows_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Source Availability

| Source role | Rows | Path-ready | Status | Boundary |
| --- | ---: | ---: | --- | --- |
{source_table}

## Policy Contract

| Policy | Required sources | Source inputs ready | Status |
| --- | --- | --- | --- |
{policy_table}

## Leakage Guard

| Field | Policy input | Reason |
| --- | --- | --- |
{leakage_table}

## Claim Boundary

- M24 makes H001 source materialization feasible, but it does not execute H001 policies.
- `initial_memory_proxy` is not true dynamic stale memory. It is a non-oracle static-HM3D memory snapshot used to test the navigation adapter path.
- Final H001 real navigation `SR` / `SPL` remains false until materialized source rows are executed and compared against baselines at larger scale.
"""


def main() -> None:
    m03_coverage = read_json(M03_DIR / "coverage.json")
    m10_coverage = read_json(M10_DIR / "coverage.json")
    m17_coverage = read_json(M17_DIR / "coverage.json")
    m22_coverage = read_json(M22_DIR / "coverage.json")
    m23_coverage = read_json(M23_DIR / "coverage.json")

    m03_sources = read_jsonl(M03_DIR / "candidate_source_rows.jsonl")
    episode_rows = read_jsonl(M03_DIR / "episode_goal_eval_rows.jsonl")
    m10_rows = read_jsonl(M10_DIR / "candidate_navmesh_rows.jsonl")
    m17_rows = read_jsonl(M17_DIR / "candidate_navmesh_rows.jsonl")
    m18_rows = read_jsonl(M18_DIR / "candidate_visit_order_rows.jsonl")

    if not m23_coverage:
        raise SystemExit("missing E008-M23 coverage")
    if m23_coverage.get("selected_next_unit") != "E008-M24 H001 candidate-source instantiation contract":
        raise SystemExit("E008-M23 did not select E008-M24")
    if not episode_rows or not m10_rows or not m17_rows:
        raise SystemExit("missing E008-M03/M10/M17 source inputs")

    schema_rows = build_candidate_source_schema_rows()
    task_context_rows = build_task_context_rows(episode_rows)
    source_rows = build_source_availability_rows(m03_sources, m10_rows, m17_rows, m18_rows, episode_rows)
    policy_rows = build_policy_contract_rows(source_rows)
    leakage_rows = build_leakage_guard_rows()
    materialization_rows = build_materialization_plan_rows()
    claim_rows = build_claim_boundary_rows()

    leakage_pass = not any_leakage(m10_rows) and not any_leakage(m17_rows)
    inputs_ready = bool(m10_rows) and bool(m17_rows) and bool(task_context_rows) and leakage_pass
    selected_next = (
        "E008-M25 H001 candidate-source materialization smoke"
        if inputs_ready
        else "repair E008-M24 H001 source input contract"
    )
    status = (
        "e008_m24_h001_candidate_source_contract_ready_materialization_next"
        if inputs_ready
        else "e008_m24_h001_candidate_source_contract_blocked"
    )
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "materialize_h001_candidate_source_rows_next" if inputs_ready else "repair_source_contract",
            "reason": "Initial memory-proxy and current-observation candidate sources are available and leakage-guarded; materialization is the next unit."
            if inputs_ready
            else "Required source rows or leakage guard failed.",
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "h001_candidate_source_contract_ready": inputs_ready,
            "h001_candidate_source_rows_ready": 0,
            "h001_navigation_policy_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m03_status": m03_coverage.get("status"),
        "m10_status": m10_coverage.get("status"),
        "m17_status": m17_coverage.get("status"),
        "m22_status": m22_coverage.get("status"),
        "m23_status": m23_coverage.get("status"),
        "episode_rows": len(episode_rows),
        "task_context_rows_planned": len(task_context_rows),
        "initial_memory_proxy_candidate_rows": len(m10_rows),
        "initial_memory_proxy_path_ready_rows": path_ready_count(m10_rows),
        "current_observation_candidate_rows": len(m17_rows),
        "current_observation_path_ready_rows": path_ready_count(m17_rows),
        "detector_visit_order_rows": len(m18_rows),
        "source_availability_rows": len(source_rows),
        "candidate_source_schema_rows": len(schema_rows),
        "policy_contract_rows": len(policy_rows),
        "policy_contract_source_ready_rows": sum(1 for row in policy_rows if row.get("source_inputs_ready")),
        "leakage_guard_rows": len(leakage_rows),
        "source_input_leakage_pass": leakage_pass,
        "m10_status_counts": status_counts(m10_rows, "navmesh_validation_status"),
        "m17_status_counts": status_counts(m17_rows, "navmesh_validation_status"),
        "h001_candidate_source_materialization_inputs_ready": inputs_ready,
        "h001_candidate_source_rows_ready": 0,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_smoke_ready": bool(m22_coverage.get("real_navigation_sr_spl_smoke_ready")),
        "real_navigation_sr_spl_ready": False,
        "dynamic_stale_memory_claim_ready_on_hm3d": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_source_schema_rows.jsonl", schema_rows)
        write_jsonl(output_dir / "source_availability_rows.jsonl", source_rows)
        write_jsonl(output_dir / "task_context_contract_rows.jsonl", task_context_rows)
        write_jsonl(output_dir / "policy_instantiation_contract_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "leakage_guard_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "source_materialization_plan_rows.jsonl", materialization_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, source_rows, policy_rows, leakage_rows),
        encoding="utf-8",
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
