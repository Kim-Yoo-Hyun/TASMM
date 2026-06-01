#!/usr/bin/env python3
"""Materialize M76 source-gap/SPL repair rows from the M75 contract."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M72_DIR = EXP_ROOT / "artifacts" / "E008-M72_full_val_mini_detector_policy_trajectory_contract_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E008-M75_source_gap_spl_repair_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M76_source_gap_spl_repair_row_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M76_source_gap_spl_repair_row_materialization_smoke_v0"
)

VERSION = "e008_m76_source_gap_spl_repair_row_materialization_smoke_v0"
READY_STATUS = "e008_m76_source_gap_spl_repair_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m76_source_gap_spl_repair_row_materialization_smoke_blocked"
NEXT_UNIT = "E008-M77 full-val-mini source-gap/SPL repair leakage-safe goal-evaluation smoke"

PRIMARY_POLICY = "detector_confidence_reachable_subset_v0"
ALL_CANDIDATE_POLICY = "detector_confidence_all_candidates_v0"
PATH_COST_POLICY = "path_cost_ascending_reachable_subset_v0"
SPL_GUARDED_POLICY = "spl_guarded_confidence_path_tail_budget5_v0"
SOURCE_PROBE_POLICY = "candidate_source_expansion_probe_v0"

PRIMARY_BUDGET = 5
CONFIDENCE_PREFIX = 4

BLOCKED_POLICY_FIELDS = {
    "ObjectNav goal position",
    "ObjectNav viewpoint position",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_*",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_*",
    "primary_eval_hit",
    "trajectory_success",
    "SR",
    "SPL",
    "success_proposal_uid",
    "success_source_role",
    "m70_primary_first_hit_rank",
    "m70_primary_first_hit_cost_m",
    "m70_primary_spl_proxy",
    "m71_failure_class",
    "M71 failure class",
    "diagnostic_source_gap_boundary",
}


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


def finite_int(value: object, default: int = 10**9) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def candidate_key(row: dict[str, Any]) -> str:
    return str(row.get("proposal_uid") or row.get("raw_candidate_uid") or row.get("candidate_visit_uid"))


def source_diversity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("candidate_source_role")),
        str(row.get("frame_pose_role")),
        str(row.get("observation_pose_id")),
    )


def path_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m"))
    confidence = finite_float(row.get("confidence")) or 0.0
    return (
        path_cost if path_cost is not None else 1e9,
        -confidence,
        finite_int(row.get("candidate_rank_m09")),
        candidate_key(row),
    )


def confidence_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    confidence = finite_float(row.get("confidence")) or 0.0
    return (-confidence, finite_int(row.get("candidate_rank_m09")), candidate_key(row))


def group_policy_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))].append(row)
    for policy_rows in grouped.values():
        for policy_id, items in policy_rows.items():
            if policy_id == PATH_COST_POLICY:
                items.sort(key=path_cost_sort_key)
            elif policy_id == ALL_CANDIDATE_POLICY:
                items.sort(key=lambda item: finite_int(item.get("visit_rank")))
            else:
                items.sort(key=lambda item: finite_int(item.get("visit_rank")))
    return grouped


def allowed_candidate(row: dict[str, Any]) -> bool:
    return bool(row.get("candidate_usable_for_path_smoke")) and bool(row.get("path_ready"))


def clone_candidate(
    source: dict[str, Any],
    *,
    policy_id: str,
    policy_role: str,
    visit_rank: int,
    repair_component: str,
    source_policy_id: str,
    source_visit_rank: int | None,
    rank_source_fields: list[str],
    execute_in_next_runner: bool,
    goal_eval_in_next_unit: bool,
    probe_only: bool,
) -> dict[str, Any]:
    benchmark_uid = str(source.get("benchmark_row_uid"))
    policy_plan_uid = f"m76::{benchmark_uid}::{policy_id}"
    budget_rank = visit_rank if visit_rank <= PRIMARY_BUDGET else None
    return {
        "version": VERSION,
        "source_version": source.get("version"),
        "source_candidate_visit_uid": source.get("candidate_visit_uid"),
        "source_policy_id": source_policy_id,
        "source_visit_rank": source_visit_rank,
        "adapter_episode_id": source.get("adapter_episode_id"),
        "benchmark_row_uid": benchmark_uid,
        "scan_id": source.get("scan_id"),
        "scene_key": source.get("scene_key"),
        "object_category": source.get("object_category"),
        "task_context_id": source.get("task_context_id"),
        "policy_id": policy_id,
        "policy_role": policy_role,
        "policy_plan_uid": policy_plan_uid,
        "candidate_visit_uid": f"{policy_plan_uid}::{visit_rank:04d}",
        "candidate_order_component": repair_component,
        "repair_component": repair_component,
        "visit_rank": visit_rank,
        "primary_budget_cap": PRIMARY_BUDGET,
        "m76_budget_rank": budget_rank,
        "within_budget5": visit_rank <= PRIMARY_BUDGET,
        "proposal_uid": source.get("proposal_uid"),
        "raw_candidate_uid": source.get("raw_candidate_uid"),
        "label_canonical": source.get("label_canonical"),
        "confidence": source.get("confidence"),
        "selection_score": source.get("selection_score"),
        "ranking_score": source.get("ranking_score"),
        "candidate_rank_m09": source.get("candidate_rank_m09"),
        "candidate_source_role": source.get("candidate_source_role"),
        "dynamic_stale_overlay_role": source.get("dynamic_stale_overlay_role"),
        "frame_id": source.get("frame_id"),
        "frame_pose_role": source.get("frame_pose_role"),
        "observation_pose_id": source.get("observation_pose_id"),
        "candidate_position_m": source.get("candidate_position_m"),
        "snapped_position_m": source.get("snapped_position_m"),
        "candidate_stop_position_m": source.get("candidate_stop_position_m"),
        "execution_stop_position_m": source.get("execution_stop_position_m"),
        "source_position_m": source.get("source_position_m"),
        "source_to_candidate_path_cost_m": source.get("source_to_candidate_path_cost_m"),
        "cumulative_known_path_cost_m": source.get("cumulative_known_path_cost_m"),
        "path_ready": source.get("path_ready"),
        "candidate_usable_for_path_smoke": source.get("candidate_usable_for_path_smoke"),
        "navmesh_validation_status": source.get("navmesh_validation_status"),
        "scene_docker_path": source.get("scene_docker_path"),
        "navmesh_docker_path": source.get("navmesh_docker_path"),
        "m76_rank_source_fields": rank_source_fields,
        "execute_in_next_runner": execute_in_next_runner,
        "goal_eval_in_next_unit": goal_eval_in_next_unit,
        "probe_only": probe_only,
        "policy_input_allowed": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "uses_m70_proxy_success_for_filtering": False,
        "uses_m71_failure_class_for_policy": False,
        "uses_m73_trajectory_result_for_policy": False,
        "claim_boundary": "M76 materializes leakage-safe repair rows only; M77 must evaluate proxy success before any trajectory rerun.",
    }


def materialize_primary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        out.append(
            clone_candidate(
                row,
                policy_id=PRIMARY_POLICY,
                policy_role="primary_detector_confidence_baseline_preserved",
                visit_rank=idx,
                repair_component="m76_primary_detector_confidence_order_reuse",
                source_policy_id=str(row.get("policy_id")),
                source_visit_rank=finite_int(row.get("visit_rank"), default=idx),
                rank_source_fields=[
                    "confidence",
                    "candidate_rank_m09",
                    "path_ready",
                    "navmesh_validation_status",
                ],
                execute_in_next_runner=True,
                goal_eval_in_next_unit=True,
                probe_only=False,
            )
        )
    return out


def materialize_spl_guarded(
    primary_rows: list[dict[str, Any]], path_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[tuple[dict[str, Any], str, str]] = []
    selected_keys: set[str] = set()

    for row in primary_rows[:CONFIDENCE_PREFIX]:
        selected.append((row, "m76_confidence_prefix_preserved", str(row.get("policy_id"))))
        selected_keys.add(candidate_key(row))

    tail_source: dict[str, Any] | None = None
    for row in path_rows:
        if candidate_key(row) not in selected_keys:
            tail_source = row
            break
    if tail_source is None and len(primary_rows) > CONFIDENCE_PREFIX:
        tail_source = primary_rows[CONFIDENCE_PREFIX]

    tail_inserted = False
    primary_rank5_key = candidate_key(primary_rows[CONFIDENCE_PREFIX]) if len(primary_rows) > CONFIDENCE_PREFIX else None
    if tail_source is not None:
        tail_inserted = candidate_key(tail_source) != primary_rank5_key
        selected.append((tail_source, "m76_guarded_path_cost_tail_slot", str(tail_source.get("policy_id"))))
        selected_keys.add(candidate_key(tail_source))

    for row in primary_rows:
        if candidate_key(row) in selected_keys:
            continue
        selected.append((row, "m76_detector_confidence_remainder", str(row.get("policy_id"))))
        selected_keys.add(candidate_key(row))

    out: list[dict[str, Any]] = []
    for idx, (row, component, source_policy_id) in enumerate(selected, start=1):
        out.append(
            clone_candidate(
                row,
                policy_id=SPL_GUARDED_POLICY,
                policy_role="selected_spl_guarded_repair_candidate",
                visit_rank=idx,
                repair_component=component,
                source_policy_id=source_policy_id,
                source_visit_rank=finite_int(row.get("visit_rank"), default=idx),
                rank_source_fields=[
                    "confidence",
                    "candidate_rank_m09",
                    "source_to_candidate_path_cost_m",
                    "candidate_source_role",
                    "frame_pose_role",
                    "observation_pose_id",
                    "path_ready",
                    "navmesh_validation_status",
                ],
                execute_in_next_runner=True,
                goal_eval_in_next_unit=True,
                probe_only=False,
            )
        )
    summary = {
        "tail_inserted": tail_inserted,
        "tail_proposal_uid": tail_source.get("proposal_uid") if tail_source else None,
        "tail_source_policy_id": tail_source.get("policy_id") if tail_source else None,
        "tail_source_to_candidate_path_cost_m": tail_source.get("source_to_candidate_path_cost_m")
        if tail_source
        else None,
        "top4_preserved": [
            candidate_key(row)
            for row in out[:CONFIDENCE_PREFIX]
        ]
        == [candidate_key(row) for row in primary_rows[:CONFIDENCE_PREFIX]],
    }
    return out, summary


def materialize_source_probe(all_rows: list[dict[str, Any]], path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path_ready_all = [row for row in all_rows if allowed_candidate(row)]
    selected: list[dict[str, Any]] = []
    selected_keys: set[str] = set()
    seen_source_keys: set[tuple[str, str, str]] = set()

    for row in sorted(path_ready_all, key=confidence_sort_key):
        if len(selected) >= 3:
            break
        selected.append(row)
        selected_keys.add(candidate_key(row))
        seen_source_keys.add(source_diversity_key(row))

    for row in path_rows:
        if len(selected) >= PRIMARY_BUDGET:
            break
        key = candidate_key(row)
        source_key = source_diversity_key(row)
        if key in selected_keys or source_key in seen_source_keys:
            continue
        selected.append(row)
        selected_keys.add(key)
        seen_source_keys.add(source_key)

    for row in path_rows:
        if len(selected) >= PRIMARY_BUDGET:
            break
        key = candidate_key(row)
        if key in selected_keys:
            continue
        selected.append(row)
        selected_keys.add(key)

    for row in sorted(path_ready_all, key=confidence_sort_key):
        if candidate_key(row) not in selected_keys:
            selected.append(row)
            selected_keys.add(candidate_key(row))

    out: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        source_policy_id = str(row.get("policy_id"))
        component = "m76_source_health_probe_budget_slot" if idx <= PRIMARY_BUDGET else "m76_source_health_probe_remainder"
        out.append(
            clone_candidate(
                row,
                policy_id=SOURCE_PROBE_POLICY,
                policy_role="source_gap_probe_not_final_policy",
                visit_rank=idx,
                repair_component=component,
                source_policy_id=source_policy_id,
                source_visit_rank=finite_int(row.get("visit_rank"), default=idx),
                rank_source_fields=[
                    "candidate_count",
                    "path_ready_candidate_count",
                    "source_role_counts",
                    "frame_pose_role",
                    "observation_pose_id",
                    "label_canonical",
                    "confidence",
                    "source_to_candidate_path_cost_m",
                ],
                execute_in_next_runner=False,
                goal_eval_in_next_unit=False,
                probe_only=True,
            )
        )
    return out


def build_plan_row(
    rows: list[dict[str, Any]],
    *,
    source_gap_episode_ids: set[str],
    source_ready_failure_episode_ids: set[str],
) -> dict[str, Any]:
    first = rows[0]
    source_counts = Counter(str(row.get("candidate_source_role")) for row in rows)
    top5 = [row for row in rows if bool(row.get("within_budget5"))]
    path_costs = [finite_float(row.get("source_to_candidate_path_cost_m")) for row in top5]
    policy_id = str(first.get("policy_id"))
    execute = bool(first.get("execute_in_next_runner"))
    goal_eval = bool(first.get("goal_eval_in_next_unit"))
    return {
        "version": VERSION,
        "row_type": "m76_repair_execution_plan",
        "policy_plan_uid": first.get("policy_plan_uid"),
        "policy_id": policy_id,
        "policy_role": first.get("policy_role"),
        "adapter_episode_id": first.get("adapter_episode_id"),
        "benchmark_row_uid": first.get("benchmark_row_uid"),
        "scan_id": first.get("scan_id"),
        "scene_key": first.get("scene_key"),
        "object_category": first.get("object_category"),
        "task_context_id": first.get("task_context_id"),
        "candidate_rows": len(rows),
        "budget5_candidate_rows": len(top5),
        "path_ready_candidate_rows": sum(1 for row in rows if bool(row.get("path_ready"))),
        "source_role_counts": dict(source_counts),
        "budget5_mean_source_to_candidate_path_cost_m": mean(path_costs),
        "primary_budget_cap": PRIMARY_BUDGET,
        "execute_in_next_runner": execute,
        "goal_eval_in_next_unit": goal_eval,
        "probe_only": bool(first.get("probe_only")),
        "diagnostic_source_gap_boundary_for_reporting": str(first.get("adapter_episode_id")) in source_gap_episode_ids,
        "diagnostic_source_ready_failure_for_reporting": str(first.get("adapter_episode_id"))
        in source_ready_failure_episode_ids,
        "requires_docker_for_trajectory": execute,
        "execution_candidate_file": "repair_candidate_visit_order_rows.jsonl",
        "start_state_source": "ObjectNav episode start state from M70/M72 contract; not used in M76 ranking",
        "termination_rule": "M77 evaluates proxy success; trajectory rerun remains blocked until proxy and leakage gates pass",
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_m70_proxy_success_for_filtering": False,
        "uses_m71_failure_class_for_policy": False,
        "uses_m73_trajectory_result_for_policy": False,
        "claim_boundary": "M76 materializes rows only; this is not a navigation SR/SPL result.",
    }


def leakage_audit(rows: list[dict[str, Any]], contract_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    audits: list[dict[str, Any]] = []
    contract_blocked = set(BLOCKED_POLICY_FIELDS)
    for row in contract_rows:
        contract_blocked.update(str(item) for item in row.get("blocked_inputs", []))

    for policy_id, items in sorted(group_by_policy(rows).items()):
        field_hits = Counter()
        truthy_blocked = Counter()
        for item in items:
            for blocked in contract_blocked:
                if blocked in item:
                    field_hits[blocked] += 1
                    if item.get(blocked):
                        truthy_blocked[blocked] += 1
            for key, value in item.items():
                if key.startswith("candidate_to_eval_") or key.startswith("candidate_to_nearest_eval_"):
                    field_hits[key] += 1
                    if value:
                        truthy_blocked[key] += 1
        audits.append(
            {
                "version": VERSION,
                "row_type": "leakage_audit",
                "policy_id": policy_id,
                "candidate_rows": len(items),
                "blocked_field_occurrences": sum(field_hits.values()),
                "truthy_blocked_field_occurrences": sum(truthy_blocked.values()),
                "blocked_fields_present": dict(sorted(field_hits.items())),
                "truthy_blocked_fields": dict(sorted(truthy_blocked.items())),
                "policy_input_uses_eval_goal_or_viewpoint_rows": sum(
                    1 for item in items if bool(item.get("policy_input_uses_eval_goal_or_viewpoint"))
                ),
                "policy_input_uses_success_label_rows": sum(
                    1 for item in items if bool(item.get("policy_input_uses_success_label"))
                ),
                "audit_pass": not truthy_blocked
                and not any(bool(item.get("policy_input_uses_eval_goal_or_viewpoint")) for item in items)
                and not any(bool(item.get("policy_input_uses_success_label")) for item in items),
                "claim_boundary": "Blocked diagnostic fields may appear only as false booleans in policy-audit flags.",
            }
        )
    return audits, all(bool(row.get("audit_pass")) for row in audits)


def group_by_policy(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("policy_id"))].append(row)
    return grouped


def build_budget_rows(plan_rows: list[dict[str, Any]], tail_summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(plan_rows, key=lambda item: (str(item.get("policy_id")), str(item.get("adapter_episode_id")))):
        tail = tail_summaries.get(str(row.get("benchmark_row_uid")), {})
        out.append(
            {
                "version": VERSION,
                "row_type": "budget_accounting",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "benchmark_row_uid": row.get("benchmark_row_uid"),
                "policy_id": row.get("policy_id"),
                "candidate_rows": row.get("candidate_rows"),
                "budget5_candidate_rows": row.get("budget5_candidate_rows"),
                "primary_budget_cap": row.get("primary_budget_cap"),
                "execute_in_next_runner": row.get("execute_in_next_runner"),
                "goal_eval_in_next_unit": row.get("goal_eval_in_next_unit"),
                "tail_inserted": tail.get("tail_inserted") if row.get("policy_id") == SPL_GUARDED_POLICY else None,
                "top4_preserved": tail.get("top4_preserved") if row.get("policy_id") == SPL_GUARDED_POLICY else None,
                "tail_source_policy_id": tail.get("tail_source_policy_id")
                if row.get("policy_id") == SPL_GUARDED_POLICY
                else None,
                "claim_boundary": "Budget accounting does not use eval success labels.",
            }
        )
    return out


def build_source_boundary_rows(
    plan_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failures = {str(row.get("adapter_episode_id")): row for row in failure_rows}
    out: list[dict[str, Any]] = []
    for row in sorted(plan_rows, key=lambda item: (str(item.get("adapter_episode_id")), str(item.get("policy_id")))):
        failure = failures.get(str(row.get("adapter_episode_id")))
        out.append(
            {
                "version": VERSION,
                "row_type": "source_boundary_accounting",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "benchmark_row_uid": row.get("benchmark_row_uid"),
                "policy_id": row.get("policy_id"),
                "diagnostic_failure_target": failure.get("repair_target") if failure else None,
                "diagnostic_source_gap_boundary_for_reporting": bool(
                    failure.get("diagnostic_source_gap_boundary")
                )
                if failure
                else False,
                "candidate_rows": row.get("candidate_rows"),
                "budget5_candidate_rows": row.get("budget5_candidate_rows"),
                "source_role_counts": row.get("source_role_counts"),
                "probe_only": row.get("probe_only"),
                "used_for_policy_ranking": False,
                "claim_boundary": "Failure target and source-gap flags are reporting-only diagnostics after materialization.",
            }
        )
    return out


def build_report(coverage: dict[str, Any]) -> str:
    return f"""# E008-M76 Source-Gap/SPL Repair Row Materialization Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Candidate rows: {coverage['repair_candidate_rows']}.
- Execution plan rows: {coverage['repair_execution_plan_rows']}.
- Goal-eval-ready plan rows: {coverage['goal_eval_ready_plan_rows']}.
- Probe-only plan rows: {coverage['probe_only_plan_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Budget compliance pass: {coverage['budget_compliance_pass']}.
- SPL guarded tail inserted rows: {coverage['spl_guarded_tail_inserted_plan_rows']}.
- SPL guarded top-4 preserved rows: {coverage['spl_guarded_top4_preserved_plan_rows']}.
- Source-gap reporting episodes: {coverage['source_gap_failure_episode_rows']}.
- Source-ready threshold/boundary failure episodes: {coverage['source_ready_failure_episode_rows']}.

## Materialized Policies

| policy_id | role | candidate rows | goal eval next | probe only |
| --- | --- | ---: | --- | --- |
| `{PRIMARY_POLICY}` | primary detector-confidence baseline preserved | {coverage['policy_candidate_rows'].get(PRIMARY_POLICY, 0)} | true | false |
| `{SPL_GUARDED_POLICY}` | confidence top-4 + guarded path-cost tail | {coverage['policy_candidate_rows'].get(SPL_GUARDED_POLICY, 0)} | true | false |
| `{SOURCE_PROBE_POLICY}` | source-health probe, not final policy | {coverage['policy_candidate_rows'].get(SOURCE_PROBE_POLICY, 0)} | false | true |

## Decision

- Selected next unit: {coverage['selected_next_unit']}.
- M76 supports a leakage-safe M77 proxy evaluation input.
- M76 does not support a repaired `SR` / `SPL` claim yet.
- Candidate-source probe rows do not solve source-gap failures; they separate candidate-source absence from ordering/SPL failure before heavier candidate-source expansion.
"""


def sync_derived(skip_copy: bool) -> None:
    if skip_copy:
        return
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-derived-copy", action="store_true", help="Do not copy artifacts to local_dataset.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = datetime.now().replace(microsecond=0).isoformat()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    candidate_rows = read_jsonl(M72_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    contract_rows = read_jsonl(M75_DIR / "policy_repair_contract_rows.jsonl")
    failure_rows = read_jsonl(M75_DIR / "failure_episode_repair_rows.jsonl")
    m75_coverage = read_json(M75_DIR / "coverage.json")

    missing_inputs = []
    if not candidate_rows:
        missing_inputs.append(str(M72_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl"))
    if not contract_rows:
        missing_inputs.append(str(M75_DIR / "policy_repair_contract_rows.jsonl"))
    if not m75_coverage:
        missing_inputs.append(str(M75_DIR / "coverage.json"))

    grouped = group_policy_rows(candidate_rows)
    materialized: list[dict[str, Any]] = []
    tail_summaries: dict[str, dict[str, Any]] = {}
    missing_policy_plan_rows: list[dict[str, Any]] = []

    for benchmark_uid in sorted(grouped):
        policies = grouped[benchmark_uid]
        primary_rows = [row for row in policies.get(PRIMARY_POLICY, []) if allowed_candidate(row)]
        path_rows = [row for row in policies.get(PATH_COST_POLICY, []) if allowed_candidate(row)]
        all_rows = policies.get(ALL_CANDIDATE_POLICY, [])

        if not primary_rows or not path_rows:
            missing_policy_plan_rows.append(
                {
                    "version": VERSION,
                    "row_type": "missing_policy_plan_input",
                    "benchmark_row_uid": benchmark_uid,
                    "primary_rows": len(primary_rows),
                    "path_rows": len(path_rows),
                    "all_candidate_rows": len(all_rows),
                    "claim_boundary": "M76 cannot materialize a repair plan without both detector-confidence and path-cost rows.",
                }
            )
            continue

        materialized.extend(materialize_primary(primary_rows))
        guarded_rows, tail_summary = materialize_spl_guarded(primary_rows, path_rows)
        tail_summaries[benchmark_uid] = tail_summary
        materialized.extend(guarded_rows)
        materialized.extend(materialize_source_probe(all_rows, path_rows))

    source_gap_episode_ids = {
        str(row.get("adapter_episode_id"))
        for row in failure_rows
        if bool(row.get("diagnostic_source_gap_boundary"))
    }
    source_ready_failure_episode_ids = {
        str(row.get("adapter_episode_id"))
        for row in failure_rows
        if not bool(row.get("diagnostic_source_gap_boundary"))
    }

    plan_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in materialized:
        plan_groups[str(row.get("policy_plan_uid"))].append(row)
    plan_rows = [
        build_plan_row(
            sorted(rows, key=lambda item: finite_int(item.get("visit_rank"))),
            source_gap_episode_ids=source_gap_episode_ids,
            source_ready_failure_episode_ids=source_ready_failure_episode_ids,
        )
        for rows in plan_groups.values()
    ]
    plan_rows.sort(key=lambda item: (str(item.get("adapter_episode_id")), str(item.get("policy_id"))))

    leakage_rows, leakage_pass = leakage_audit(materialized, contract_rows)
    budget_rows = build_budget_rows(plan_rows, tail_summaries)
    source_boundary_rows = build_source_boundary_rows(plan_rows, failure_rows)
    source_probe_rows = [
        row for row in materialized if row.get("policy_id") == SOURCE_PROBE_POLICY and bool(row.get("within_budget5"))
    ]
    policy_summary_rows = []
    for policy_id, rows in sorted(group_by_policy(materialized).items()):
        plan_count = len({str(row.get("policy_plan_uid")) for row in rows})
        policy_summary_rows.append(
            {
                "version": VERSION,
                "row_type": "policy_materialization_summary",
                "policy_id": policy_id,
                "candidate_rows": len(rows),
                "plan_rows": plan_count,
                "budget5_candidate_rows": sum(1 for row in rows if bool(row.get("within_budget5"))),
                "goal_eval_ready_plan_rows": sum(
                    1
                    for item in plan_rows
                    if item.get("policy_id") == policy_id and bool(item.get("goal_eval_in_next_unit"))
                ),
                "probe_only_plan_rows": sum(
                    1 for item in plan_rows if item.get("policy_id") == policy_id and bool(item.get("probe_only"))
                ),
                "execute_in_next_runner_plan_rows": sum(
                    1 for item in plan_rows if item.get("policy_id") == policy_id and bool(item.get("execute_in_next_runner"))
                ),
                "claim_boundary": "M76 summary is row materialization evidence only.",
            }
        )

    claim_boundary_rows = [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "repaired SR/SPL",
            "supported_now": False,
            "reason": "M76 materializes rows but does not run proxy goal evaluation or Docker trajectories.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "source-gap recovery",
            "supported_now": False,
            "reason": "Source-gap probe rows are diagnostic; actual recovery requires candidate-source expansion evidence.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "SPL improvement",
            "supported_now": False,
            "reason": "Guarded path-cost tail must be evaluated against detector-confidence baseline in M77/M78.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "final real navigation SR/SPL",
            "supported_now": False,
            "reason": "External navigation/search baselines and heldout transfer are still missing.",
        },
    ]

    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "rationale": "M76 rows are leakage-safe and M77 can score budget/full-rank proxy behavior before any Docker trajectory rerun.",
            "launch_long_job_now": False,
            "requires_docker_now": False,
        }
    ]

    policy_counts = Counter(str(row.get("policy_id")) for row in materialized)
    plan_policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    budget_compliance_pass = all(int(row.get("budget5_candidate_rows") or 0) <= PRIMARY_BUDGET for row in plan_rows)
    spl_guarded_tail_inserted = sum(1 for item in tail_summaries.values() if bool(item.get("tail_inserted")))
    spl_guarded_top4_preserved = sum(1 for item in tail_summaries.values() if bool(item.get("top4_preserved")))
    expected_benchmark_rows = len(grouped)
    goal_eval_ready_plan_rows = sum(1 for row in plan_rows if bool(row.get("goal_eval_in_next_unit")))
    probe_only_plan_rows = sum(1 for row in plan_rows if bool(row.get("probe_only")))

    status = READY_STATUS
    if missing_inputs or missing_policy_plan_rows or not materialized or not leakage_pass or not budget_compliance_pass:
        status = BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "generated_at": generated_at,
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "missing_inputs": missing_inputs,
        "m75_status": m75_coverage.get("status"),
        "repair_candidate_rows": len(materialized),
        "repair_execution_plan_rows": len(plan_rows),
        "policy_candidate_rows": dict(policy_counts),
        "policy_plan_rows": dict(plan_policy_counts),
        "expected_benchmark_rows": expected_benchmark_rows,
        "goal_eval_ready_plan_rows": goal_eval_ready_plan_rows,
        "probe_only_plan_rows": probe_only_plan_rows,
        "source_probe_budget_rows": len(source_probe_rows),
        "missing_policy_plan_rows": len(missing_policy_plan_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": leakage_pass,
        "budget_accounting_rows": len(budget_rows),
        "budget_compliance_pass": budget_compliance_pass,
        "source_boundary_accounting_rows": len(source_boundary_rows),
        "source_gap_failure_episode_rows": len(source_gap_episode_ids),
        "source_ready_failure_episode_rows": len(source_ready_failure_episode_ids),
        "spl_guarded_tail_inserted_plan_rows": spl_guarded_tail_inserted,
        "spl_guarded_top4_preserved_plan_rows": spl_guarded_top4_preserved,
        "repair_row_materialization_ready": status == READY_STATUS,
        "goal_evaluation_ready_now": status == READY_STATUS and goal_eval_ready_plan_rows > 0,
        "trajectory_execution_ready_now": False,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_jsonl(ARTIFACT_DIR / "repair_candidate_visit_order_rows.jsonl", materialized)
    write_jsonl(ARTIFACT_DIR / "repair_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_probe_rows.jsonl", source_probe_rows)
    write_jsonl(ARTIFACT_DIR / "policy_materialization_summary_rows.jsonl", policy_summary_rows)
    write_jsonl(ARTIFACT_DIR / "budget_accounting_rows.jsonl", budget_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_accounting_rows.jsonl", source_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "missing_policy_plan_rows.jsonl", missing_policy_plan_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage), encoding="utf-8")

    sync_derived(bool(args.skip_derived_copy))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
