#!/usr/bin/env python3
"""Materialize M80 loss-safe candidate-source expansion rows."""

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
M68_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M79_DIR = EXP_ROOT / "artifacts" / "E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
)

VERSION = "e008_m80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
READY_STATUS = "e008_m80_loss_safe_candidate_source_expansion_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m80_loss_safe_candidate_source_expansion_row_materialization_smoke_blocked"
NEXT_UNIT = "E008-M81 full-val-mini loss-safe candidate-source expansion leakage-safe goal-evaluation smoke"

SOURCE_POLICY = "detector_confidence_reachable_subset_v0"
ALL_POLICY = "detector_confidence_all_candidates_v0"
PATH_POLICY = "path_cost_ascending_reachable_subset_v0"
CORE_POLICY = "detector_confidence_budget5_core_v0"
APPEND_POLICY = "loss_safe_append_source_probe_budget8_v0"
SOURCE_EXPAND_POLICY = "loss_safe_observation_source_expansion_probe_v0"

CORE_BUDGET = 5
APPEND_BUDGET = 8
APPEND_SLOTS = APPEND_BUDGET - CORE_BUDGET

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
    "M78 guarded_loss identity",
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
        str(row.get("candidate_source_role") or "current_observation"),
        str(row.get("frame_pose_role") or "unknown_frame_pose_role"),
        str(row.get("observation_pose_id") or "unknown_observation_pose_id"),
    )


def visit_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (finite_int(row.get("visit_rank")), finite_int(row.get("candidate_rank_m09")), candidate_key(row))


def path_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    path_cost = finite_float(row.get("source_to_candidate_path_cost_m"))
    confidence = finite_float(row.get("confidence")) or 0.0
    return (
        path_cost if path_cost is not None else 1e9,
        -confidence,
        finite_int(row.get("candidate_rank_m09")),
        candidate_key(row),
    )


def path_ready(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("path_ready"))
        and bool(row.get("candidate_usable_for_path_smoke", True))
        and str(row.get("navmesh_validation_status")) == "candidate_path_ready"
    )


def enrich_candidate(row: dict[str, Any], navmesh_by_proposal: dict[str, dict[str, Any]]) -> dict[str, Any]:
    nav = navmesh_by_proposal.get(str(row.get("proposal_uid")), {})
    enriched = dict(row)
    for key, value in nav.items():
        enriched.setdefault(key, value)
    enriched["candidate_source_role"] = enriched.get("candidate_source_role") or "current_observation"
    enriched["candidate_usable_for_path_smoke"] = bool(nav.get("candidate_usable_for_path_smoke", row.get("path_ready")))
    enriched["path_ready"] = bool(row.get("path_ready")) and bool(nav.get("source_to_snapped_path_found", True))
    enriched["navmesh_validation_status"] = row.get("navmesh_validation_status") or nav.get("navmesh_validation_status")
    enriched["source_to_candidate_path_cost_m"] = row.get("source_to_candidate_path_cost_m")
    if enriched["source_to_candidate_path_cost_m"] is None:
        enriched["source_to_candidate_path_cost_m"] = nav.get("source_to_snapped_geodesic_m")
    enriched["candidate_position_m"] = nav.get("centroid_world_m")
    enriched["snapped_position_m"] = nav.get("snapped_position_m")
    enriched["candidate_stop_position_m"] = nav.get("snapped_position_m")
    enriched["execution_stop_position_m"] = nav.get("snapped_position_m")
    enriched["source_position_m"] = nav.get("source_position")
    enriched["scene_docker_path"] = nav.get("scene_docker_path")
    enriched["navmesh_docker_path"] = nav.get("navmesh_docker_path")
    enriched["frame_id"] = nav.get("frame_id")
    enriched["frame_pose_role"] = nav.get("frame_pose_role")
    enriched["observation_pose_id"] = nav.get("observation_pose_id")
    enriched["shell_radius_m"] = nav.get("shell_radius_m")
    enriched["source_to_snapped_geodesic_m"] = nav.get("source_to_snapped_geodesic_m")
    return enriched


def group_policy_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row.get("adapter_episode_id"))][str(row.get("policy_id"))].append(row)
    for policies in grouped.values():
        for policy_id, items in policies.items():
            if policy_id == PATH_POLICY:
                items.sort(key=path_cost_sort_key)
            else:
                items.sort(key=visit_sort_key)
    return grouped


def m69_source_uid(row: dict[str, Any]) -> str:
    return (
        "m69::"
        f"{row.get('adapter_episode_id')}::"
        f"{row.get('policy_id')}::"
        f"{finite_int(row.get('visit_rank'), 0):04d}::"
        f"{row.get('proposal_uid')}"
    )


def clone_candidate(
    source: dict[str, Any],
    *,
    policy_id: str,
    policy_role: str,
    visit_rank: int,
    candidate_order_component: str,
    source_policy_id: str,
    source_visit_rank: int | None,
    primary_budget_cap: int,
    rank_source_fields: list[str],
) -> dict[str, Any]:
    adapter_episode_id = str(source.get("adapter_episode_id"))
    policy_plan_uid = f"m80::{adapter_episode_id}::{policy_id}"
    return {
        "version": VERSION,
        "source_version": source.get("version"),
        "source_candidate_visit_uid": m69_source_uid(source),
        "source_policy_id": source_policy_id,
        "source_visit_rank": source_visit_rank,
        "adapter_episode_id": adapter_episode_id,
        "scan_id": source.get("scan_id"),
        "scene_key": source.get("scene_key"),
        "object_category": source.get("object_category"),
        "policy_id": policy_id,
        "policy_role": policy_role,
        "policy_plan_uid": policy_plan_uid,
        "candidate_visit_uid": f"{policy_plan_uid}::{visit_rank:04d}",
        "candidate_order_component": candidate_order_component,
        "visit_rank": visit_rank,
        "primary_budget_cap": primary_budget_cap,
        "within_detector_budget5": visit_rank <= CORE_BUDGET,
        "within_policy_budget": visit_rank <= primary_budget_cap,
        "proposal_uid": source.get("proposal_uid"),
        "raw_candidate_uid": source.get("raw_candidate_uid"),
        "label_canonical": source.get("label_canonical"),
        "confidence": source.get("confidence"),
        "selection_score": source.get("selection_score"),
        "ranking_score": source.get("ranking_score"),
        "confidence_path_cost_tradeoff_score": source.get("confidence_path_cost_tradeoff_score"),
        "candidate_rank_m09": source.get("candidate_rank_m09") or source.get("candidate_rank"),
        "candidate_source_role": source.get("candidate_source_role") or "current_observation",
        "frame_id": source.get("frame_id"),
        "frame_pose_role": source.get("frame_pose_role"),
        "observation_pose_id": source.get("observation_pose_id"),
        "shell_radius_m": source.get("shell_radius_m"),
        "candidate_position_m": source.get("candidate_position_m"),
        "snapped_position_m": source.get("snapped_position_m"),
        "candidate_stop_position_m": source.get("candidate_stop_position_m"),
        "execution_stop_position_m": source.get("execution_stop_position_m"),
        "source_position_m": source.get("source_position_m"),
        "source_to_candidate_path_cost_m": source.get("source_to_candidate_path_cost_m"),
        "source_to_snapped_geodesic_m": source.get("source_to_snapped_geodesic_m"),
        "cumulative_known_path_cost_m": source.get("cumulative_known_path_cost_m"),
        "path_ready": source.get("path_ready"),
        "candidate_usable_for_path_smoke": source.get("candidate_usable_for_path_smoke"),
        "navmesh_validation_status": source.get("navmesh_validation_status"),
        "scene_docker_path": source.get("scene_docker_path"),
        "navmesh_docker_path": source.get("navmesh_docker_path"),
        "m80_rank_source_fields": rank_source_fields,
        "execute_in_next_runner": False,
        "goal_eval_in_next_unit": True,
        "trajectory_execution_ready_now": False,
        "policy_input_allowed": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "uses_m70_proxy_success_for_filtering": False,
        "uses_m71_failure_class_for_policy": False,
        "uses_m73_trajectory_result_for_policy": False,
        "uses_m78_loss_identity_for_policy": False,
        "claim_boundary": "M80 materializes leakage-safe row order only; M81 must evaluate proxy success.",
    }


def select_append_rows(core_rows: list[dict[str, Any]], policies: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_keys = {candidate_key(row) for row in core_rows}
    seen_source_keys = {source_diversity_key(row) for row in core_rows}

    def add_from(pool: list[dict[str, Any]], *, require_new_source: bool) -> None:
        nonlocal selected, selected_keys, seen_source_keys
        for row in pool:
            if len(selected) >= APPEND_SLOTS:
                return
            key = candidate_key(row)
            source_key = source_diversity_key(row)
            if key in selected_keys or not path_ready(row):
                continue
            if require_new_source and source_key in seen_source_keys:
                continue
            selected.append(row)
            selected_keys.add(key)
            seen_source_keys.add(source_key)

    reachable_tail = [row for row in policies.get(SOURCE_POLICY, [])[CORE_BUDGET:] if path_ready(row)]
    path_rows = [row for row in policies.get(PATH_POLICY, []) if path_ready(row)]
    all_rows = [row for row in policies.get(ALL_POLICY, []) if path_ready(row)]
    add_from(reachable_tail, require_new_source=True)
    add_from(path_rows, require_new_source=True)
    add_from(reachable_tail, require_new_source=False)
    add_from(path_rows, require_new_source=False)
    add_from(all_rows, require_new_source=False)
    return selected


def materialize_episode(
    adapter_episode_id: str,
    policies: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any] | None]:
    source_rows = [row for row in policies.get(SOURCE_POLICY, []) if path_ready(row)]
    if len(source_rows) < CORE_BUDGET:
        return [], {}, {
            "version": VERSION,
            "row_type": "missing_policy_input",
            "adapter_episode_id": adapter_episode_id,
            "source_policy_rows": len(source_rows),
            "required_core_budget": CORE_BUDGET,
            "claim_boundary": "M80 requires at least five path-ready detector-confidence reachable candidates.",
        }

    core_source_rows = source_rows[:CORE_BUDGET]
    append_source_rows = select_append_rows(core_source_rows, policies)
    core_rows: list[dict[str, Any]] = []
    append_rows: list[dict[str, Any]] = []

    for idx, row in enumerate(core_source_rows, start=1):
        core_rows.append(
            clone_candidate(
                row,
                policy_id=CORE_POLICY,
                policy_role="loss_safe_detector_confidence_budget5_core",
                visit_rank=idx,
                candidate_order_component="m80_detector_confidence_top5_preserved",
                source_policy_id=SOURCE_POLICY,
                source_visit_rank=finite_int(row.get("visit_rank"), default=idx),
                primary_budget_cap=CORE_BUDGET,
                rank_source_fields=[
                    "confidence",
                    "candidate_rank_m09",
                    "path_ready",
                    "navmesh_validation_status",
                ],
            )
        )
        append_rows.append(
            clone_candidate(
                row,
                policy_id=APPEND_POLICY,
                policy_role="loss_safe_append_source_probe_budget8",
                visit_rank=idx,
                candidate_order_component="m80_detector_confidence_top5_preserved_before_append",
                source_policy_id=SOURCE_POLICY,
                source_visit_rank=finite_int(row.get("visit_rank"), default=idx),
                primary_budget_cap=APPEND_BUDGET,
                rank_source_fields=[
                    "confidence",
                    "candidate_rank_m09",
                    "path_ready",
                    "navmesh_validation_status",
                ],
            )
        )

    for slot, row in enumerate(append_source_rows, start=CORE_BUDGET + 1):
        append_rows.append(
            clone_candidate(
                row,
                policy_id=APPEND_POLICY,
                policy_role="loss_safe_append_source_probe_budget8",
                visit_rank=slot,
                candidate_order_component="m80_append_policy_visible_source_probe_after_top5",
                source_policy_id=str(row.get("policy_id")),
                source_visit_rank=finite_int(row.get("visit_rank"), default=slot),
                primary_budget_cap=APPEND_BUDGET,
                rank_source_fields=[
                    "confidence",
                    "source_to_candidate_path_cost_m",
                    "candidate_source_role",
                    "frame_pose_role",
                    "observation_pose_id",
                    "path_ready",
                    "navmesh_validation_status",
                ],
            )
        )

    core_keys = [candidate_key(row) for row in core_rows]
    append_first5_keys = [candidate_key(row) for row in append_rows[:CORE_BUDGET]]
    invariant = {
        "version": VERSION,
        "row_type": "budget_invariant",
        "adapter_episode_id": adapter_episode_id,
        "core_top5_proposal_uids": core_keys,
        "append_first5_proposal_uids": append_first5_keys,
        "append_candidate_rows": len(append_rows),
        "append_after_top5_rows": max(0, len(append_rows) - CORE_BUDGET),
        "top5_preserved": core_keys == append_first5_keys,
        "budget_invariant_pass": core_keys == append_first5_keys and len(core_rows) == CORE_BUDGET and len(append_rows) == APPEND_BUDGET,
        "claim_boundary": "M80 protects detector-confidence budget-5 before any source expansion is evaluated.",
    }
    return core_rows + append_rows, invariant, None


def build_policy_plan_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    top5 = [row for row in rows if bool(row.get("within_detector_budget5"))]
    appended = [row for row in rows if int(row.get("visit_rank") or 0) > CORE_BUDGET]
    return {
        "version": VERSION,
        "row_type": "loss_safe_policy_plan",
        "policy_plan_uid": first.get("policy_plan_uid"),
        "policy_id": first.get("policy_id"),
        "policy_role": first.get("policy_role"),
        "adapter_episode_id": first.get("adapter_episode_id"),
        "scan_id": first.get("scan_id"),
        "scene_key": first.get("scene_key"),
        "object_category": first.get("object_category"),
        "candidate_rows": len(rows),
        "detector_budget5_rows": len(top5),
        "append_after_top5_rows": len(appended),
        "path_ready_candidate_rows": sum(1 for row in rows if bool(row.get("path_ready"))),
        "unique_observation_pose_ids": len({str(row.get("observation_pose_id")) for row in rows}),
        "unique_frame_pose_roles": len({str(row.get("frame_pose_role")) for row in rows}),
        "source_role_counts": dict(Counter(str(row.get("candidate_source_role")) for row in rows)),
        "mean_source_to_candidate_path_cost_m": mean(
            [finite_float(row.get("source_to_candidate_path_cost_m")) for row in rows]
        ),
        "budget5_mean_source_to_candidate_path_cost_m": mean(
            [finite_float(row.get("source_to_candidate_path_cost_m")) for row in top5]
        ),
        "primary_budget_cap": first.get("primary_budget_cap"),
        "execute_in_next_runner": False,
        "goal_eval_in_next_unit": True,
        "trajectory_execution_ready_now": False,
        "execution_candidate_file": "loss_safe_candidate_visit_order_rows.jsonl",
        "termination_rule": "M81 evaluates proxy success before any trajectory rerun.",
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "claim_boundary": "Policy plan rows are inputs for M81 goal-evaluation only, not navigation results.",
    }


def build_source_observation_plan_rows(expansion_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = [
        (
            "existing_append_probe_audit_v0",
            "audit existing appended candidates after preserved detector top-5",
            False,
        ),
        (
            "non_oracle_local_shell_multiview_refresh_v0",
            "later render/detect denser local shell around policy-visible observation inventory",
            True,
        ),
        (
            "non_oracle_high_path_source_refresh_v0",
            "later refresh source views from policy-visible high-path/source inventory",
            True,
        ),
    ]
    out: list[dict[str, Any]] = []
    for case in expansion_rows:
        if case.get("case_type") != "source_gap_unresolved" or not bool(case.get("selected_for_m80")):
            continue
        for idx, (action_id, action, requires_long_job_later) in enumerate(actions, start=1):
            out.append(
                {
                    "version": VERSION,
                    "row_type": "source_observation_expansion_plan",
                    "plan_uid": f"m80::{case.get('adapter_episode_id')}::{SOURCE_EXPAND_POLICY}::{idx:02d}",
                    "policy_id": SOURCE_EXPAND_POLICY,
                    "adapter_episode_id": case.get("adapter_episode_id"),
                    "scan_id": case.get("scan_id"),
                    "scene_key": case.get("scene_key"),
                    "object_category": case.get("object_category"),
                    "case_type": case.get("case_type"),
                    "action_id": action_id,
                    "action": action,
                    "requires_long_job_later": requires_long_job_later,
                    "launch_long_job_now": False,
                    "goal_eval_in_next_unit": False,
                    "execute_in_next_runner": False,
                    "trajectory_execution_ready_now": False,
                    "policy_input_allowed_for_final_policy": False,
                    "used_for_candidate_ranking": False,
                    "policy_input_uses_eval_goal_or_viewpoint": False,
                    "policy_input_uses_success_label": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_m70_proxy_success_for_filtering": False,
                    "uses_m71_failure_class_for_policy": False,
                    "uses_m73_trajectory_result_for_policy": False,
                    "uses_m78_loss_identity_for_policy": False,
                    "claim_boundary": "This plan names non-oracle source expansion work; it is not a recovered candidate or success result.",
                }
            )
    return out


def build_source_boundary_rows(
    scan_source_rows: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cases_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in expansion_rows:
        cases_by_episode[str(row.get("adapter_episode_id"))].append(row)
    out: list[dict[str, Any]] = []
    for row in sorted(scan_source_rows, key=lambda item: str(item.get("adapter_episode_id"))):
        cases = cases_by_episode.get(str(row.get("adapter_episode_id")), [])
        case_types = [str(case.get("case_type")) for case in cases]
        out.append(
            {
                "version": VERSION,
                "row_type": "source_boundary_accounting",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "source_ready": row.get("source_ready"),
                "source_gap": row.get("source_gap"),
                "source_boundary_status": row.get("source_boundary_status"),
                "candidate_rows": row.get("candidate_rows"),
                "path_ready_candidate_rows": row.get("path_ready_candidate_rows"),
                "m79_case_types": case_types,
                "source_gap_expansion_case": "source_gap_unresolved" in case_types,
                "budget5_loss_sentinel_case": "budget5_loss_sentinel" in case_types,
                "localization_boundary_control_case": "localization_boundary_control" in case_types,
                "used_for_policy_ranking": False,
                "claim_boundary": "M79 case labels are reporting diagnostics and are not M80 ranking inputs.",
            }
        )
    return out


def blocked_field_hits(row: dict[str, Any], blocked: set[str]) -> tuple[Counter[str], Counter[str]]:
    fields = Counter()
    truthy = Counter()
    for blocked_name in blocked:
        if blocked_name in row:
            fields[blocked_name] += 1
            if row.get(blocked_name):
                truthy[blocked_name] += 1
    for key, value in row.items():
        if key.startswith("candidate_to_eval_") or key.startswith("candidate_to_nearest_eval_"):
            fields[key] += 1
            if value:
                truthy[key] += 1
    return fields, truthy


def leakage_audit(
    candidate_rows: list[dict[str, Any]],
    source_plan_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    blocked = set(BLOCKED_POLICY_FIELDS)
    for row in contract_rows:
        blocked.update(str(item) for item in row.get("blocked_inputs", []))

    audits: list[dict[str, Any]] = []
    candidate_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        candidate_groups[str(row.get("policy_id"))].append(row)

    for policy_id, rows in sorted(candidate_groups.items()):
        field_hits = Counter()
        truthy_hits = Counter()
        for row in rows:
            fields, truthy = blocked_field_hits(row, blocked)
            field_hits.update(fields)
            truthy_hits.update(truthy)
        audits.append(
            {
                "version": VERSION,
                "row_type": "leakage_audit",
                "audited_unit": "candidate_policy_rows",
                "policy_id": policy_id,
                "candidate_rows": len(rows),
                "blocked_field_occurrences": sum(field_hits.values()),
                "truthy_blocked_field_occurrences": sum(truthy_hits.values()),
                "blocked_fields_present": dict(sorted(field_hits.items())),
                "truthy_blocked_fields": dict(sorted(truthy_hits.items())),
                "policy_input_uses_eval_goal_or_viewpoint_rows": sum(
                    1 for row in rows if bool(row.get("policy_input_uses_eval_goal_or_viewpoint"))
                ),
                "policy_input_uses_success_label_rows": sum(
                    1 for row in rows if bool(row.get("policy_input_uses_success_label"))
                ),
                "policy_input_allowed_for_final_policy": True,
                "used_for_candidate_ranking": True,
                "audit_pass": not truthy_hits
                and not any(bool(row.get("policy_input_uses_eval_goal_or_viewpoint")) for row in rows)
                and not any(bool(row.get("policy_input_uses_success_label")) for row in rows),
                "claim_boundary": "Blocked diagnostic fields may appear only as false booleans in audit flags.",
            }
        )

    source_field_hits = Counter()
    source_truthy_hits = Counter()
    for row in source_plan_rows:
        fields, truthy = blocked_field_hits(row, blocked)
        source_field_hits.update(fields)
        source_truthy_hits.update(truthy)
    audits.append(
        {
            "version": VERSION,
            "row_type": "leakage_audit",
            "audited_unit": "source_observation_expansion_plan_rows",
            "policy_id": SOURCE_EXPAND_POLICY,
            "candidate_rows": 0,
            "plan_rows": len(source_plan_rows),
            "blocked_field_occurrences": sum(source_field_hits.values()),
            "truthy_blocked_field_occurrences": sum(source_truthy_hits.values()),
            "blocked_fields_present": dict(sorted(source_field_hits.items())),
            "truthy_blocked_fields": dict(sorted(source_truthy_hits.items())),
            "policy_input_allowed_for_final_policy": False,
            "used_for_candidate_ranking": False,
            "audit_pass": not source_truthy_hits
            and not any(bool(row.get("policy_input_uses_eval_goal_or_viewpoint")) for row in source_plan_rows)
            and not any(bool(row.get("policy_input_uses_success_label")) for row in source_plan_rows),
            "claim_boundary": "Source-plan rows can be selected from diagnostics only because they are not final-policy ranking inputs.",
        }
    )
    return audits, all(bool(row.get("audit_pass")) for row in audits)


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "loss-safe detector budget-5 preservation",
            "supported_now": True,
            "reason": "M80 materializes append policy rows whose first five proposals exactly match detector-confidence top-5.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "source-gap recovery",
            "supported_now": False,
            "reason": "M80 creates source-observation expansion plans but does not generate new detections or run M81 goal evaluation.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "deployable search policy",
            "supported_now": False,
            "reason": "Candidate rows are offline materialization rows; policy execution and external baselines remain incomplete.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "real navigation SR/SPL",
            "supported_now": False,
            "reason": "M80 does not run Habitat trajectories and cannot claim SR/SPL.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "final real RGB-D/open-vocabulary robustness",
            "supported_now": False,
            "reason": "Detector candidates remain a bounded full-val-mini smoke; external detector/map baselines and heldout transfer are missing.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "human intent main contribution",
            "supported_now": False,
            "reason": "E008-M80 does not introduce a natural-language or human-intent benchmark.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "rationale": "The loss-safe rows are materialized; M81 should score proxy success without using eval labels for ranking.",
            "launch_long_job_now": False,
            "requires_docker_now": False,
        }
    ]


def build_report(coverage: dict[str, Any]) -> str:
    return f"""# E008-M80 Loss-Safe Candidate-Source Expansion Row Materialization Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M79 status: `{coverage['m79_status']}`.
- Candidate visit-order rows: {coverage['candidate_visit_order_rows']}.
- Detector budget-5 core rows: {coverage['detector_core_candidate_rows']}.
- Loss-safe append policy rows: {coverage['append_policy_candidate_rows']}.
- Policy plan rows: {coverage['policy_plan_rows']}.
- Source/observation expansion plan rows: {coverage['source_observation_expansion_plan_rows']}.
- Budget invariant rows: {coverage['budget_invariant_rows']}.
- Budget invariant pass: {coverage['budget_invariant_pass']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Source-gap expansion cases: {coverage['source_gap_expansion_cases']}.
- Budget-5 loss sentinel cases: {coverage['budget5_loss_sentinel_cases']}.
- Localization boundary control cases: {coverage['localization_control_cases']}.

## Materialized Policies

| policy_id | rows | plan rows | next use |
| --- | ---: | ---: | --- |
| `{CORE_POLICY}` | {coverage['policy_candidate_rows'].get(CORE_POLICY, 0)} | {coverage['policy_plan_counts'].get(CORE_POLICY, 0)} | M81 baseline preservation check |
| `{APPEND_POLICY}` | {coverage['policy_candidate_rows'].get(APPEND_POLICY, 0)} | {coverage['policy_plan_counts'].get(APPEND_POLICY, 0)} | M81 append-only proxy check |
| `{SOURCE_EXPAND_POLICY}` | 0 | {coverage['source_observation_expansion_plan_rows']} | later non-oracle source expansion planning |

## Decision

- Selected next unit: {coverage['selected_next_unit']}.
- M80 supports loss-safe row materialization and detector top-5 preservation.
- M80 does not support source-gap recovery, deployable search policy, final RGB-D robustness, or real navigation `SR` / `SPL`.
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

    m79_coverage = read_json(M79_DIR / "coverage.json")
    m69_rows_raw = read_jsonl(M69_DIR / "candidate_visit_order_rows.jsonl")
    m68_candidate_rows = read_jsonl(M68_DIR / "candidate_navmesh_validation_rows.jsonl")
    scan_source_rows = read_jsonl(M68_DIR / "scan_source_boundary_rows.jsonl")
    expansion_rows = read_jsonl(M79_DIR / "expansion_case_rows.jsonl")
    contract_rows = read_jsonl(M79_DIR / "loss_safe_policy_contract_rows.jsonl")

    navmesh_by_proposal = {str(row.get("proposal_uid")): row for row in m68_candidate_rows}
    m69_rows = [enrich_candidate(row, navmesh_by_proposal) for row in m69_rows_raw]
    grouped = group_policy_rows(m69_rows)

    materialized: list[dict[str, Any]] = []
    invariant_rows: list[dict[str, Any]] = []
    missing_policy_input_rows: list[dict[str, Any]] = []
    for adapter_episode_id in sorted(grouped):
        rows, invariant, missing = materialize_episode(adapter_episode_id, grouped[adapter_episode_id])
        materialized.extend(rows)
        if invariant:
            invariant_rows.append(invariant)
        if missing:
            missing_policy_input_rows.append(missing)

    cases_by_episode: dict[str, list[str]] = defaultdict(list)
    for row in expansion_rows:
        cases_by_episode[str(row.get("adapter_episode_id"))].append(str(row.get("case_type")))
    for row in invariant_rows:
        case_types = cases_by_episode.get(str(row.get("adapter_episode_id")), [])
        row["source_gap_expansion_case"] = "source_gap_unresolved" in case_types
        row["budget5_loss_sentinel_case"] = "budget5_loss_sentinel" in case_types
        row["localization_boundary_control_case"] = "localization_boundary_control" in case_types

    plan_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in materialized:
        plan_groups[str(row.get("policy_plan_uid"))].append(row)
    policy_plan_rows = [
        build_policy_plan_row(sorted(rows, key=lambda item: finite_int(item.get("visit_rank"))))
        for rows in plan_groups.values()
    ]
    policy_plan_rows.sort(key=lambda item: (str(item.get("adapter_episode_id")), str(item.get("policy_id"))))

    source_plan_rows = build_source_observation_plan_rows(expansion_rows)
    source_boundary_rows = build_source_boundary_rows(scan_source_rows, expansion_rows)
    leakage_rows, leakage_pass = leakage_audit(materialized, source_plan_rows, contract_rows)
    claim_boundary_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    policy_counts = Counter(str(row.get("policy_id")) for row in materialized)
    policy_plan_counts = Counter(str(row.get("policy_id")) for row in policy_plan_rows)
    budget_pass = bool(invariant_rows) and all(bool(row.get("budget_invariant_pass")) for row in invariant_rows)
    expected_episode_rows = len(grouped)
    source_gap_cases = sum(1 for row in expansion_rows if row.get("case_type") == "source_gap_unresolved")
    loss_cases = sum(1 for row in expansion_rows if row.get("case_type") == "budget5_loss_sentinel")
    localization_cases = sum(1 for row in expansion_rows if row.get("case_type") == "localization_boundary_control")

    missing_inputs = []
    if not m79_coverage:
        missing_inputs.append(str(M79_DIR / "coverage.json"))
    if not m69_rows_raw:
        missing_inputs.append(str(M69_DIR / "candidate_visit_order_rows.jsonl"))
    if not m68_candidate_rows:
        missing_inputs.append(str(M68_DIR / "candidate_navmesh_validation_rows.jsonl"))
    if not scan_source_rows:
        missing_inputs.append(str(M68_DIR / "scan_source_boundary_rows.jsonl"))
    if not contract_rows:
        missing_inputs.append(str(M79_DIR / "loss_safe_policy_contract_rows.jsonl"))

    status = READY_STATUS
    if (
        missing_inputs
        or missing_policy_input_rows
        or not materialized
        or len(invariant_rows) != expected_episode_rows
        or not budget_pass
        or not leakage_pass
        or policy_counts.get(CORE_POLICY, 0) != expected_episode_rows * CORE_BUDGET
        or policy_counts.get(APPEND_POLICY, 0) != expected_episode_rows * APPEND_BUDGET
    ):
        status = BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "generated_at": generated_at,
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "missing_inputs": missing_inputs,
        "m79_status": m79_coverage.get("status"),
        "input_m69_candidate_visit_order_rows": len(m69_rows_raw),
        "input_m68_navmesh_rows": len(m68_candidate_rows),
        "candidate_visit_order_rows": len(materialized),
        "detector_core_candidate_rows": policy_counts.get(CORE_POLICY, 0),
        "append_policy_candidate_rows": policy_counts.get(APPEND_POLICY, 0),
        "policy_candidate_rows": dict(policy_counts),
        "policy_plan_rows": len(policy_plan_rows),
        "policy_plan_counts": dict(policy_plan_counts),
        "source_observation_expansion_plan_rows": len(source_plan_rows),
        "budget_invariant_rows": len(invariant_rows),
        "budget_invariant_pass": budget_pass,
        "top5_preservation_pass_rows": sum(1 for row in invariant_rows if bool(row.get("top5_preserved"))),
        "missing_policy_input_rows": len(missing_policy_input_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": leakage_pass,
        "source_boundary_accounting_rows": len(source_boundary_rows),
        "source_gap_expansion_cases": source_gap_cases,
        "budget5_loss_sentinel_cases": loss_cases,
        "localization_control_cases": localization_cases,
        "m81_goal_eval_input_ready": status == READY_STATUS,
        "goal_evaluation_ready_now": status == READY_STATUS,
        "trajectory_execution_ready_now": False,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_jsonl(ARTIFACT_DIR / "loss_safe_candidate_visit_order_rows.jsonl", materialized)
    write_jsonl(ARTIFACT_DIR / "loss_safe_policy_plan_rows.jsonl", policy_plan_rows)
    write_jsonl(ARTIFACT_DIR / "source_observation_expansion_plan_rows.jsonl", source_plan_rows)
    write_jsonl(ARTIFACT_DIR / "budget_invariant_rows.jsonl", invariant_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_accounting_rows.jsonl", source_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "missing_policy_input_rows.jsonl", missing_policy_input_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage), encoding="utf-8")

    sync_derived(bool(args.skip_derived_copy))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
