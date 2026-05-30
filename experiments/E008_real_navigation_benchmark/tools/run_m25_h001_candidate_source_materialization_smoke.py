#!/usr/bin/env python3
"""Materialize H001 candidate-source rows from the E008-M24 contract."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M25_h001_candidate_source_materialization_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M25_h001_candidate_source_materialization_smoke_v0"
VERSION = "e008_m25_h001_candidate_source_materialization_smoke_v0"

M03_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M10_DIR = EXP_ROOT / "artifacts" / "E008-M10_detector_candidate_navmesh_validation_v0"
M17_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M24_DIR = EXP_ROOT / "artifacts" / "E008-M24_h001_candidate_source_instantiation_contract_v0"

TASK_CONTEXT_BUDGETS = {
    "routine_fetch": {
        "success_reward": 1.0,
        "check_cost": 1.0,
        "failure_cost": 1.0,
        "max_candidate_budget": 3,
        "h001_current_observation_budget": 2,
        "h001_initial_memory_budget": 1,
        "h001_visit_order": "initial_memory_proxy_top1_then_current_observation_top2",
    },
    "high_value_fetch": {
        "success_reward": 5.0,
        "check_cost": 1.0,
        "failure_cost": 5.0,
        "max_candidate_budget": 5,
        "h001_current_observation_budget": 4,
        "h001_initial_memory_budget": 1,
        "h001_visit_order": "initial_memory_proxy_top1_then_current_observation_top4",
    },
    "noisy_high_value_fetch": {
        "success_reward": 5.0,
        "check_cost": 1.0,
        "failure_cost": 8.0,
        "max_candidate_budget": 5,
        "h001_current_observation_budget": 3,
        "h001_initial_memory_budget": 1,
        "h001_visit_order": "current_observation_top3_then_initial_memory_proxy_guard_top1",
    },
}

POLICY_SPECS = [
    {
        "policy_id": "real_static_memory_proxy_v0",
        "policy_family": "static_stale_memory",
        "required_source_roles": ["initial_memory_proxy"],
        "uses_task_context_budget": False,
        "fixed_candidate_budget": 5,
        "candidate_visit_order_contract": "initial_memory_proxy_confidence_desc",
    },
    {
        "policy_id": "real_detector_confidence_expanded_v0",
        "policy_family": "detector_confidence_ranking",
        "required_source_roles": ["current_observation"],
        "uses_task_context_budget": False,
        "fixed_candidate_budget": 5,
        "candidate_visit_order_contract": "current_observation_confidence_desc",
    },
    {
        "policy_id": "real_context_agnostic_memory_trust_reobserve_v0",
        "policy_family": "context_agnostic_memory_trust",
        "required_source_roles": ["initial_memory_proxy", "current_observation"],
        "uses_task_context_budget": False,
        "fixed_candidate_budget": 4,
        "candidate_visit_order_contract": "initial_memory_proxy_top1_then_current_observation_top3",
    },
    {
        "policy_id": "h001_real_task_context_memory_trust_v0",
        "policy_family": "h001_memory_trust",
        "required_source_roles": ["initial_memory_proxy", "current_observation"],
        "uses_task_context_budget": True,
        "fixed_candidate_budget": None,
        "candidate_visit_order_contract": "task_context_conditioned_memory_trust_and_reobservation_budget",
    },
    {
        "policy_id": "h001_then_external_map_after_observed_miss_v0",
        "policy_family": "h001_plus_external_map_fallback",
        "required_source_roles": ["initial_memory_proxy", "current_observation", "external_map", "runtime_event"],
        "uses_task_context_budget": True,
        "fixed_candidate_budget": None,
        "candidate_visit_order_contract": "h001_queue_then_external_map_after_runtime_miss",
    },
]


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def safe_rate(num: int, den: int) -> float | None:
    return round(float(num) / float(den), 6) if den else None


def query_label_compatible(object_category: object, label: object) -> bool:
    query = str(object_category or "").lower().replace("-", "_")
    candidate = str(label or "").lower().replace("-", "_")
    if not query or not candidate:
        return False
    aliases = {
        "tv_monitor": {"tv", "television", "monitor", "tv_monitor"},
        "television": {"tv", "television", "monitor", "tv_monitor"},
        "tv": {"tv", "television", "monitor", "tv_monitor"},
    }
    if query in aliases:
        return candidate in aliases[query]
    return query == candidate


def is_path_ready(row: dict[str, Any]) -> bool:
    return (
        row.get("navmesh_validation_status") == "candidate_path_ready"
        and bool(row.get("source_to_snapped_path_found"))
        and finite_float(row.get("source_to_snapped_geodesic_m")) is not None
    )


def reliability_score(row: dict[str, Any]) -> float:
    confidence = finite_float(row.get("confidence")) or 0.0
    snap_distance = finite_float(row.get("snap_distance_m")) or 0.0
    path_factor = 1.0 if is_path_ready(row) else 0.25
    return round(max(0.0, min(1.0, confidence * path_factor / (1.0 + max(0.0, snap_distance)))), 6)


def source_row_uid(source_role: str, task_context_id: str, proposal_uid: object) -> str:
    clean = str(proposal_uid or "missing").replace("/", "_")
    return f"m25::{source_role}::{task_context_id}::{clean}"


def build_episode_scan_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        adapter_episode_id = str(row.get("adapter_episode_id"))
        if adapter_episode_id and adapter_episode_id not in out:
            out[adapter_episode_id] = {
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "source_position": row.get("source_position"),
                "scene_docker_path": row.get("scene_docker_path"),
                "navmesh_docker_path": row.get("navmesh_docker_path"),
            }
    return out


def build_query_context_rows(
    episode_rows: list[dict[str, Any]],
    context_contract_rows: list[dict[str, Any]],
    episode_scan_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    episode_eval_by_id = {str(row.get("adapter_episode_id")): row for row in episode_rows}
    rows = []
    for context in context_contract_rows:
        adapter_episode_id = str(context.get("adapter_episode_id"))
        context_id = str(context.get("task_context_id"))
        scan_meta = episode_scan_index.get(adapter_episode_id, {})
        episode_eval = episode_eval_by_id.get(adapter_episode_id, {})
        spec = TASK_CONTEXT_BUDGETS[context_id]
        rows.append(
            {
                "version": VERSION,
                "query_context_uid": f"m25::{adapter_episode_id}::{context_id}",
                "adapter_episode_id": adapter_episode_id,
                "scan_id": scan_meta.get("scan_id"),
                "scene_key": context.get("scene_key") or scan_meta.get("scene_key"),
                "object_category": context.get("object_category") or scan_meta.get("object_category"),
                "task_context_id": context_id,
                "success_reward": spec["success_reward"],
                "check_cost": spec["check_cost"],
                "failure_cost": spec["failure_cost"],
                "max_candidate_budget": spec["max_candidate_budget"],
                "h001_initial_memory_budget": spec["h001_initial_memory_budget"],
                "h001_current_observation_budget": spec["h001_current_observation_budget"],
                "h001_visit_order_contract": spec["h001_visit_order"],
                "episode_start_position_m": episode_eval.get("start_position"),
                "episode_start_rotation": episode_eval.get("start_rotation"),
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal": False,
                "uses_objectnav_eval_viewpoint": False,
                "claim_boundary": "structured_task_context_not_natural_language_intent",
            }
        )
    return rows


def materialize_source_rows(
    candidate_rows: list[dict[str, Any]],
    task_context_rows: list[dict[str, Any]],
    source_role: str,
    source_stage: str,
    memory_age_stage: str,
    staleness_proxy_score: float,
) -> list[dict[str, Any]]:
    contexts_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_context_rows:
        contexts_by_episode[str(row.get("adapter_episode_id"))].append(row)

    out = []
    for candidate in candidate_rows:
        adapter_episode_id = str(candidate.get("adapter_episode_id"))
        if not query_label_compatible(candidate.get("object_category"), candidate.get("label_canonical")):
            continue
        path_ready = is_path_ready(candidate)
        path_cost = finite_float(candidate.get("source_to_snapped_geodesic_m")) if path_ready else None
        reliability = reliability_score(candidate)
        for context in contexts_by_episode.get(adapter_episode_id, []):
            task_context_id = str(context.get("task_context_id"))
            out.append(
                {
                    "version": VERSION,
                    "source_row_uid": source_row_uid(source_role, task_context_id, candidate.get("proposal_uid")),
                    "adapter_episode_id": adapter_episode_id,
                    "scan_id": candidate.get("scan_id"),
                    "scene_key": candidate.get("scene_key"),
                    "object_category": candidate.get("object_category"),
                    "task_context_id": task_context_id,
                    "source_role": source_role,
                    "source_stage": source_stage,
                    "proposal_uid": candidate.get("proposal_uid"),
                    "raw_candidate_uid": candidate.get("raw_candidate_uid"),
                    "label_canonical": candidate.get("label_canonical"),
                    "candidate_rank": candidate.get("candidate_rank"),
                    "candidate_position_m": candidate.get("centroid_world_m"),
                    "candidate_stop_position_m": candidate.get("snapped_position_m"),
                    "candidate_source_position_m": candidate.get("source_position"),
                    "candidate_confidence": finite_float(candidate.get("confidence")),
                    "selection_score": finite_float(candidate.get("selection_score")),
                    "proposal_reliability_score": reliability,
                    "path_ready": path_ready,
                    "source_to_candidate_path_cost_m": path_cost,
                    "snap_distance_m": finite_float(candidate.get("snap_distance_m")),
                    "navmesh_validation_status": candidate.get("navmesh_validation_status"),
                    "frame_id": candidate.get("frame_id"),
                    "yaw_offset_deg": candidate.get("yaw_offset_deg"),
                    "memory_age_stage": memory_age_stage,
                    "staleness_proxy_score": staleness_proxy_score,
                    "memory_trust_feature_group": f"{source_role}_confidence_path_reliability_v0",
                    "policy_input_allowed": bool(candidate.get("policy_input_allowed")),
                    "uses_objectnav_eval_goal": bool(candidate.get("uses_objectnav_eval_goal")),
                    "uses_objectnav_eval_viewpoint": bool(candidate.get("uses_objectnav_eval_viewpoint")),
                    "claim_boundary": "hm3d_initial_memory_is_proxy_not_true_dynamic_stale_memory"
                    if source_role == "initial_memory_proxy"
                    else "current_observation_is_non_oracle_detector_source_not_final_robustness",
                }
            )
    return out


def summarize_by_episode_context(source_rows: list[dict[str, Any]], query_context_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_key_role: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        rows_by_key_role[(str(row["adapter_episode_id"]), str(row["task_context_id"]), str(row["source_role"]))].append(row)

    out = []
    for context in query_context_rows:
        adapter_episode_id = str(context["adapter_episode_id"])
        task_context_id = str(context["task_context_id"])
        initial = rows_by_key_role[(adapter_episode_id, task_context_id, "initial_memory_proxy")]
        current = rows_by_key_role[(adapter_episode_id, task_context_id, "current_observation")]
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "scan_id": context.get("scan_id"),
                "scene_key": context.get("scene_key"),
                "object_category": context.get("object_category"),
                "task_context_id": task_context_id,
                "initial_memory_proxy_rows": len(initial),
                "initial_memory_proxy_path_ready_rows": sum(1 for row in initial if row.get("path_ready")),
                "current_observation_rows": len(current),
                "current_observation_path_ready_rows": sum(1 for row in current if row.get("path_ready")),
                "source_pair_materialized": bool(initial and current),
                "h001_materialization_ready": bool(initial and current),
            }
        )
    return out


def build_policy_plan_rows(query_context_rows: list[dict[str, Any]], source_summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary_by_key = {
        (str(row["adapter_episode_id"]), str(row["task_context_id"])): row for row in source_summary_rows
    }
    rows = []
    for context in query_context_rows:
        key = (str(context["adapter_episode_id"]), str(context["task_context_id"]))
        summary = summary_by_key[key]
        source_counts = {
            "initial_memory_proxy": int(summary["initial_memory_proxy_rows"]),
            "current_observation": int(summary["current_observation_rows"]),
            "external_map": 0,
            "runtime_event": 0,
        }
        path_ready_counts = {
            "initial_memory_proxy": int(summary["initial_memory_proxy_path_ready_rows"]),
            "current_observation": int(summary["current_observation_path_ready_rows"]),
            "external_map": 0,
            "runtime_event": 0,
        }
        for spec in POLICY_SPECS:
            required = list(spec["required_source_roles"])
            ready = all(source_counts.get(role, 0) > 0 for role in required)
            path_ready = all(path_ready_counts.get(role, 0) > 0 for role in required if role not in {"runtime_event"})
            if "runtime_event" in required or "external_map" in required:
                ready = False
                path_ready = False
            if spec["uses_task_context_budget"]:
                max_budget = int(context["max_candidate_budget"])
                h001_initial_budget = int(context["h001_initial_memory_budget"])
                h001_current_budget = int(context["h001_current_observation_budget"])
                visit_order = context["h001_visit_order_contract"] if spec["policy_id"] == "h001_real_task_context_memory_trust_v0" else spec["candidate_visit_order_contract"]
            else:
                max_budget = int(spec["fixed_candidate_budget"] or 0)
                h001_initial_budget = 1 if "initial_memory_proxy" in required else 0
                h001_current_budget = max(0, max_budget - h001_initial_budget) if "current_observation" in required else 0
                visit_order = spec["candidate_visit_order_contract"]
            rows.append(
                {
                    "version": VERSION,
                    "policy_plan_uid": f"m25::{context['adapter_episode_id']}::{context['task_context_id']}::{spec['policy_id']}",
                    "policy_id": spec["policy_id"],
                    "policy_family": spec["policy_family"],
                    "adapter_episode_id": context["adapter_episode_id"],
                    "scan_id": context.get("scan_id"),
                    "scene_key": context.get("scene_key"),
                    "object_category": context.get("object_category"),
                    "task_context_id": context["task_context_id"],
                    "required_source_roles": required,
                    "source_rows_by_role": source_counts,
                    "path_ready_rows_by_role": path_ready_counts,
                    "source_inputs_ready": ready,
                    "path_ready_inputs_ready": path_ready,
                    "uses_task_context_budget": bool(spec["uses_task_context_budget"]),
                    "max_candidate_budget": max_budget,
                    "h001_initial_memory_budget": h001_initial_budget,
                    "h001_current_observation_budget": h001_current_budget,
                    "candidate_visit_order_contract": visit_order,
                    "materialized_for_next_runner": ready and path_ready,
                    "policy_execution_ready": False,
                    "real_navigation_sr_spl_ready": False,
                    "status": "ready_for_h001_visit_order_path_smoke" if ready and path_ready else "blocked_missing_required_source_or_runtime_event",
                    "claim_boundary": "M25 materializes source rows and execution plans only; no trajectory or success claim is made.",
                }
            )
    return rows


def build_leakage_audit_rows(
    source_rows: list[dict[str, Any]],
    query_context_rows: list[dict[str, Any]],
    policy_plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        {
            "check_id": "source_rows_no_eval_goal",
            "passed": not any(bool(row.get("uses_objectnav_eval_goal")) for row in source_rows),
            "rows_checked": len(source_rows),
            "blocked_field": "ObjectNav eval_goal_position",
        },
        {
            "check_id": "source_rows_no_eval_viewpoint",
            "passed": not any(bool(row.get("uses_objectnav_eval_viewpoint")) for row in source_rows),
            "rows_checked": len(source_rows),
            "blocked_field": "ObjectNav eval_viewpoints",
        },
        {
            "check_id": "query_context_no_eval_goal",
            "passed": not any(bool(row.get("uses_objectnav_eval_goal")) for row in query_context_rows),
            "rows_checked": len(query_context_rows),
            "blocked_field": "ObjectNav eval_goal_position",
        },
        {
            "check_id": "query_context_no_eval_viewpoint",
            "passed": not any(bool(row.get("uses_objectnav_eval_viewpoint")) for row in query_context_rows),
            "rows_checked": len(query_context_rows),
            "blocked_field": "ObjectNav eval_viewpoints",
        },
        {
            "check_id": "policy_plans_no_success_labels",
            "passed": not any("success_label" in row or "trajectory_success" in row for row in policy_plan_rows),
            "rows_checked": len(policy_plan_rows),
            "blocked_field": "execution success labels",
        },
    ]
    for row in checks:
        row["version"] = VERSION
    return checks


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "H001 candidate-source rows can be materialized on HM3D without ObjectNav goal leakage.",
            "status": "materialization_supported",
            "boundary": "Rows are source and policy-plan inputs only; no H001 trajectory execution or success metric is produced.",
        },
        {
            "version": VERSION,
            "claim": "Initial HM3D memory-proxy rows are true dynamic stale semantic memory.",
            "status": "not_supported",
            "boundary": "`HM3D ObjectNav` is static here; dynamic stale-memory evidence remains 3RScan/3DSSG unless dynamic state injection is implemented.",
        },
        {
            "version": VERSION,
            "claim": "Structured task context is human intent understanding.",
            "status": "not_supported",
            "boundary": "M25 uses structured context budgets only, not natural-language parsing or intent inference.",
        },
        {
            "version": VERSION,
            "claim": "H001 improves real navigation SR/SPL.",
            "status": "not_supported",
            "boundary": "M25 does not execute navigation trajectories; next unit must build H001 visit-order/path rows before trajectory execution.",
        },
    ]


def build_report(coverage: dict[str, Any], policy_summary_rows: list[dict[str, Any]]) -> str:
    policy_lines = "\n".join(
        "| {policy_id} | {plan_rows} | {materialized_ready_rows} | {blocked_rows} | {status} |".format(**row)
        for row in policy_summary_rows
    )
    return f"""# E008-M25 H001 Candidate-Source Materialization Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- H001 candidate-source rows: {coverage['h001_candidate_source_rows']}.
- Query context rows: {coverage['h001_query_context_rows']}.
- Policy execution plan rows: {coverage['h001_policy_execution_plan_rows']}.
- Materialized-ready policy plan rows: {coverage['materialized_ready_policy_plan_rows']}.
- Source leakage audit pass: {coverage['source_input_leakage_pass']}.
- Initial memory-proxy source rows: {coverage['initial_memory_proxy_materialized_rows']}.
- Current-observation source rows: {coverage['current_observation_materialized_rows']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Plan Summary

| Policy | Plan rows | Ready rows | Blocked rows | Status |
| --- | ---: | ---: | ---: | --- |
{policy_lines}

## Claim Boundary

- M25 materializes source rows and policy execution plans; it does not execute H001 policies.
- `initial_memory_proxy` remains a static-HM3D memory proxy, not true dynamic stale memory.
- Structured `task_context_id` is a decision condition, not a natural-language human-intent claim.
- Final real navigation `SR` / `SPL` remains false until H001 source rows are converted to visit-order rows and executed in `Habitat`.
"""


def main() -> None:
    m24_coverage = read_json(M24_DIR / "coverage.json")
    if m24_coverage.get("selected_next_unit") != "E008-M25 H001 candidate-source materialization smoke":
        raise SystemExit("E008-M24 did not select E008-M25")

    episode_rows = read_jsonl(M03_DIR / "episode_goal_eval_rows.jsonl")
    m10_rows = read_jsonl(M10_DIR / "candidate_navmesh_rows.jsonl")
    m17_rows = read_jsonl(M17_DIR / "candidate_navmesh_rows.jsonl")
    task_context_contract_rows = read_jsonl(M24_DIR / "task_context_contract_rows.jsonl")
    if not episode_rows or not m10_rows or not m17_rows or not task_context_contract_rows:
        raise SystemExit("missing E008-M03/M10/M17/M24 source inputs")

    episode_scan_index = build_episode_scan_index(m10_rows + m17_rows)
    query_context_rows = build_query_context_rows(episode_rows, task_context_contract_rows, episode_scan_index)
    initial_rows = materialize_source_rows(
        m10_rows,
        query_context_rows,
        source_role="initial_memory_proxy",
        source_stage="initial_start_pose_yaw_sweep_v0",
        memory_age_stage="initial_snapshot_proxy",
        staleness_proxy_score=1.0,
    )
    current_rows = materialize_source_rows(
        m17_rows,
        query_context_rows,
        source_role="current_observation",
        source_stage="expanded_non_oracle_multiview_v0",
        memory_age_stage="current_reobservation",
        staleness_proxy_score=0.0,
    )
    source_rows = sorted(
        initial_rows + current_rows,
        key=lambda row: (
            str(row.get("adapter_episode_id")),
            str(row.get("task_context_id")),
            str(row.get("source_role")),
            int(row.get("candidate_rank") or 10**9),
            str(row.get("proposal_uid")),
        ),
    )
    source_summary_rows = summarize_by_episode_context(source_rows, query_context_rows)
    policy_plan_rows = build_policy_plan_rows(query_context_rows, source_summary_rows)
    policy_summary_rows = []
    for policy_id in [spec["policy_id"] for spec in POLICY_SPECS]:
        rows = [row for row in policy_plan_rows if row["policy_id"] == policy_id]
        ready = sum(1 for row in rows if row.get("materialized_for_next_runner"))
        blocked = len(rows) - ready
        policy_summary_rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "plan_rows": len(rows),
                "materialized_ready_rows": ready,
                "blocked_rows": blocked,
                "status": "ready_for_h001_visit_order_path_smoke" if ready and not blocked else "blocked_or_partial",
            }
        )

    leakage_rows = build_leakage_audit_rows(source_rows, query_context_rows, policy_plan_rows)
    claim_rows = build_claim_boundary_rows()
    source_role_counts = Counter(str(row.get("source_role")) for row in source_rows)
    path_ready_by_role = Counter(str(row.get("source_role")) for row in source_rows if row.get("path_ready"))
    status_counts = Counter(str(row.get("navmesh_validation_status")) for row in source_rows)
    source_input_leakage_pass = all(row.get("passed") for row in leakage_rows)
    materialized_ready_policy_rows = sum(1 for row in policy_plan_rows if row.get("materialized_for_next_runner"))
    actionable_ready = materialized_ready_policy_rows >= 72 and source_input_leakage_pass
    selected_next = (
        "E008-M26 H001 visit-order/path smoke"
        if actionable_ready
        else "repair E008-M25 H001 candidate-source materialization"
    )
    status = (
        "e008_m25_h001_candidate_source_materialization_smoke_ready_policy_path_next"
        if actionable_ready
        else "e008_m25_h001_candidate_source_materialization_smoke_blocked"
    )
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "build_h001_visit_order_path_smoke_next" if actionable_ready else "repair_materialized_sources",
            "selected_next_unit": selected_next,
            "reason": "H001 source rows and policy plans are materialized without eval-goal leakage; next step should rank/visit candidates before trajectory execution."
            if actionable_ready
            else "Source materialization or leakage audit failed.",
            "launch_long_job_now": False,
            "h001_candidate_source_rows_ready": bool(source_rows),
            "h001_policy_execution_plan_ready": actionable_ready,
            "h001_navigation_policy_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "dynamic_stale_memory_claim_ready_on_hm3d": False,
        }
    ]
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m24_status": m24_coverage.get("status"),
        "episode_rows": len(episode_rows),
        "task_context_rows_input": len(task_context_contract_rows),
        "h001_query_context_rows": len(query_context_rows),
        "h001_candidate_source_rows": len(source_rows),
        "initial_memory_proxy_materialized_rows": int(source_role_counts.get("initial_memory_proxy", 0)),
        "current_observation_materialized_rows": int(source_role_counts.get("current_observation", 0)),
        "initial_memory_proxy_path_ready_rows": int(path_ready_by_role.get("initial_memory_proxy", 0)),
        "current_observation_path_ready_rows": int(path_ready_by_role.get("current_observation", 0)),
        "source_role_counts": dict(sorted(source_role_counts.items())),
        "path_ready_source_role_counts": dict(sorted(path_ready_by_role.items())),
        "navmesh_status_counts": dict(sorted(status_counts.items())),
        "source_pair_summary_rows": len(source_summary_rows),
        "source_pair_ready_rows": sum(1 for row in source_summary_rows if row.get("h001_materialization_ready")),
        "h001_policy_execution_plan_rows": len(policy_plan_rows),
        "materialized_ready_policy_plan_rows": materialized_ready_policy_rows,
        "blocked_policy_plan_rows": len(policy_plan_rows) - materialized_ready_policy_rows,
        "policy_summary_rows": len(policy_summary_rows),
        "source_input_leakage_pass": source_input_leakage_pass,
        "leakage_audit_rows": len(leakage_rows),
        "h001_candidate_source_rows_ready": bool(source_rows),
        "h001_policy_execution_plan_ready": actionable_ready,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "real_navigation_sr_spl_smoke_ready": False,
        "dynamic_stale_memory_claim_ready_on_hm3d": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_initial_memory_proxy_not_true_dynamic_stale_memory": True,
        "structured_task_context_not_natural_language_intent": True,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
        "ready_policy_plan_rate": safe_rate(materialized_ready_policy_rows, len(policy_plan_rows)),
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "h001_candidate_source_rows.jsonl", source_rows)
        write_jsonl(output_dir / "h001_query_context_rows.jsonl", query_context_rows)
        write_jsonl(output_dir / "h001_source_pair_summary_rows.jsonl", source_summary_rows)
        write_jsonl(output_dir / "h001_policy_execution_plan_rows.jsonl", policy_plan_rows)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", policy_summary_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, policy_summary_rows), encoding="utf-8")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
