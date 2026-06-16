#!/usr/bin/env python3
"""Materialize M201 additive source-pool candidate-union rows."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m201_additive_source_pool_candidate_union_row_materialization_v0"
READY_STATUS = "e008_m201_additive_source_pool_candidate_union_row_materialization_ready"
BLOCKED_STATUS = "e008_m201_additive_source_pool_candidate_union_row_materialization_blocked"
NEXT_UNIT = "E008-M202 additive source-pool candidate-union leakage-safe goal-evaluation proxy"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M201_additive_source_pool_candidate_union_row_materialization_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M201_additive_source_pool_candidate_union_row_materialization_v0"
)

M69_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M70_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
M195_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
M196_DIR = EXP_ROOT / "artifacts" / "E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0"
M197_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
M200_DIR = EXP_ROOT / "artifacts" / "E008-M200_additive_source_pool_candidate_union_repair_contract_v0"

PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
BASELINE_ONLY_POLICY = "no_source_pool_detector_confidence_reachable_subset_v0"
SOURCE_POOL_REPLACEMENT_NEGATIVE = "source_pool_replacement_detector_confidence_reachable_subset_v0"
UNGUARDED_UNION_ABLATION = "additive_union_unguarded_confidence_sort_v0"

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_first_viewpoint_position",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_goal_xz_m",
    "primary_eval_hit",
    "primary_spl_proxy",
    "best_any_viewpoint_xz_m",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    path.write_text(
        "".join(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def rows_for_policy(rows: list[dict[str, Any]], policy_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("policy_id") == policy_id]


def group_by_episode(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get("adapter_episode_id"))].append(row)
    for episode_rows in out.values():
        episode_rows.sort(key=lambda row: (int(row.get("visit_rank") or 10**9), str(row.get("proposal_uid"))))
    return dict(out)


def build_eval_position_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[float] | None]:
    out: dict[tuple[str, str, str], list[float] | None] = {}
    for row in rows:
        key = (str(row.get("adapter_episode_id")), str(row.get("policy_id")), str(row.get("proposal_uid")))
        position = row.get("candidate_snapped_position_m")
        out[key] = position if isinstance(position, list) else None
    return out


def rounded_xz(position: object) -> tuple[float | None, float | None]:
    if not isinstance(position, list) or len(position) < 3:
        return None, None
    x = finite_float(position[0])
    z = finite_float(position[2])
    return (round(x, 2) if x is not None else None, round(z, 2) if z is not None else None)


def location_key(row: dict[str, Any]) -> tuple[str, str, str, float | None, float | None, str]:
    x, z = rounded_xz(row.get("candidate_snapped_position_m"))
    raw_uid = str(row.get("raw_candidate_uid") or row.get("proposal_uid"))
    return (
        str(row.get("adapter_episode_id")),
        str(row.get("object_category")),
        str(row.get("label_canonical")),
        x,
        z,
        raw_uid,
    )


def proposal_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("adapter_episode_id")), str(row.get("proposal_uid")))


def make_candidate_row(
    row: dict[str, Any],
    source_family: str,
    rank_field: str,
    position_lookup: dict[tuple[str, str, str], list[float] | None],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    episode_id = str(row.get("adapter_episode_id"))
    position = position_lookup.get((episode_id, PROTECTED_BASELINE, str(row.get("proposal_uid"))))
    return {
        "version": VERSION,
        "adapter_episode_id": episode_id,
        "scan_id": row.get("scan_id"),
        "scene_key": row.get("scene_key"),
        "object_category": row.get("object_category"),
        "candidate_source_family": source_family,
        "source_policy_id": PROTECTED_BASELINE,
        "proposal_uid": row.get("proposal_uid"),
        "raw_candidate_uid": row.get("raw_candidate_uid"),
        "label_canonical": row.get("label_canonical"),
        "candidate_snapped_position_m": position,
        "base_candidate_rank": row.get("visit_rank") if rank_field == "base_candidate_rank" else None,
        "source_pool_candidate_rank": row.get("visit_rank") if rank_field == "source_pool_candidate_rank" else None,
        "confidence": row.get("confidence"),
        "selection_score": row.get("selection_score"),
        "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
        "snap_distance_m": row.get("snap_distance_m"),
        "path_ready": bool(row.get("path_ready")),
        "navmesh_validation_status": row.get("navmesh_validation_status"),
        "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
        "query_label_compatible": bool(row.get("query_label_compatible")),
        "policy_input_allowed": bool(row.get("policy_input_allowed")) and not bool(row.get("uses_objectnav_eval_goal")) and not bool(row.get("uses_objectnav_eval_viewpoint")),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "source_boundary_status": boundary.get("source_boundary_status"),
        "source_ready_after_m195": bool(boundary.get("source_ready")),
        "source_gap_after_m195": bool(boundary.get("source_gap")),
        "m202_eval_source": "M70" if source_family == "no_source_detector" else "M197",
    }


def build_union_candidate_rows(
    baseline_by_episode: dict[str, list[dict[str, Any]]],
    source_by_episode: dict[str, list[dict[str, Any]]],
    baseline_position_lookup: dict[tuple[str, str, str], list[float] | None],
    source_position_lookup: dict[tuple[str, str, str], list[float] | None],
    boundary_by_episode: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    union_candidates: list[dict[str, Any]] = []
    dedup_rows: list[dict[str, Any]] = []
    episode_ids = sorted(set(baseline_by_episode) | set(boundary_by_episode))
    for episode_id in episode_ids:
        boundary = boundary_by_episode.get(episode_id, {})
        seen_locations: set[tuple[str, str, str, float | None, float | None, str]] = set()
        seen_proposals: set[tuple[str, str]] = set()
        baseline_rows: list[dict[str, Any]] = []
        source_rows: list[dict[str, Any]] = []
        duplicate_rows: list[dict[str, Any]] = []

        for row in baseline_by_episode.get(episode_id, []):
            candidate = make_candidate_row(row, "no_source_detector", "base_candidate_rank", baseline_position_lookup, boundary)
            candidate["union_action"] = "keep_baseline"
            candidate["duplicate_reason"] = None
            candidate["candidate_dedup_location_key"] = list(location_key(candidate))
            union_candidates.append(candidate)
            baseline_rows.append(candidate)
            seen_locations.add(location_key(candidate))
            seen_proposals.add(proposal_key(candidate))

        for row in source_by_episode.get(episode_id, []):
            candidate = make_candidate_row(row, "source_pool_detector", "source_pool_candidate_rank", source_position_lookup, boundary)
            loc_key = location_key(candidate)
            prop_key = proposal_key(candidate)
            duplicate_reason = None
            if prop_key in seen_proposals:
                duplicate_reason = "same_episode_proposal_uid"
            elif loc_key in seen_locations and loc_key[-3:-1] != (None, None):
                duplicate_reason = "same_episode_category_label_rounded_xz_raw_candidate"
            if duplicate_reason:
                candidate["union_action"] = "drop_duplicate_source_pool"
                candidate["duplicate_reason"] = duplicate_reason
                duplicate_rows.append(candidate)
            else:
                candidate["union_action"] = "append_source_pool"
                candidate["duplicate_reason"] = None
                source_rows.append(candidate)
                seen_locations.add(loc_key)
                seen_proposals.add(prop_key)
            candidate["candidate_dedup_location_key"] = list(loc_key)
            union_candidates.append(candidate)

        dedup_rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": boundary.get("scan_id") or (baseline_rows[0].get("scan_id") if baseline_rows else None),
                "scene_key": boundary.get("scene_key") or (baseline_rows[0].get("scene_key") if baseline_rows else None),
                "object_category": boundary.get("object_category") or (baseline_rows[0].get("object_category") if baseline_rows else None),
                "baseline_candidate_rows": len(baseline_rows),
                "source_pool_input_rows": len(source_by_episode.get(episode_id, [])),
                "source_pool_appended_rows": len(source_rows),
                "source_pool_duplicate_dropped_rows": len(duplicate_rows),
                "selected_union_candidate_rows": len(baseline_rows) + len(source_rows),
                "source_gap_after_m195": bool(boundary.get("source_gap")),
                "source_ready_after_m195": bool(boundary.get("source_ready")),
                "dedup_pass": len(source_rows) + len(duplicate_rows) == len(source_by_episode.get(episode_id, [])),
            }
        )
    return union_candidates, dedup_rows


def selected_candidates_for_episode(union_candidates: list[dict[str, Any]], episode_id: str) -> list[dict[str, Any]]:
    baseline = [
        row
        for row in union_candidates
        if row.get("adapter_episode_id") == episode_id and row.get("union_action") == "keep_baseline"
    ]
    source = [
        row
        for row in union_candidates
        if row.get("adapter_episode_id") == episode_id and row.get("union_action") == "append_source_pool"
    ]
    baseline.sort(key=lambda row: (int(row.get("base_candidate_rank") or 10**9), str(row.get("proposal_uid"))))
    source.sort(
        key=lambda row: (
            int(row.get("source_pool_candidate_rank") or 10**9),
            -(finite_float(row.get("confidence")) or -1.0),
            finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
            str(row.get("proposal_uid")),
        )
    )
    return baseline + source


def unguarded_candidates_for_episode(union_candidates: list[dict[str, Any]], episode_id: str) -> list[dict[str, Any]]:
    kept = [
        row
        for row in union_candidates
        if row.get("adapter_episode_id") == episode_id
        and row.get("union_action") in {"keep_baseline", "append_source_pool"}
    ]
    return sorted(
        kept,
        key=lambda row: (
            -(finite_float(row.get("confidence")) or -1.0),
            finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
            0 if row.get("candidate_source_family") == "no_source_detector" else 1,
            str(row.get("proposal_uid")),
        ),
    )


def materialize_policy_rows(
    policy_id: str,
    episode_candidates: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode_id in sorted(episode_candidates):
        cumulative_known_cost = 0.0
        for rank, candidate in enumerate(episode_candidates[episode_id], start=1):
            path_cost = finite_float(candidate.get("source_to_candidate_path_cost_m"))
            if candidate.get("path_ready") and path_cost is not None:
                cumulative_known_cost += path_cost
            out = {
                key: candidate.get(key)
                for key in [
                    "adapter_episode_id",
                    "scan_id",
                    "scene_key",
                    "object_category",
                    "candidate_source_family",
                    "source_policy_id",
                    "proposal_uid",
                    "raw_candidate_uid",
                    "label_canonical",
                    "candidate_snapped_position_m",
                    "base_candidate_rank",
                    "source_pool_candidate_rank",
                    "confidence",
                    "selection_score",
                    "source_to_candidate_path_cost_m",
                    "snap_distance_m",
                    "path_ready",
                    "navmesh_validation_status",
                    "blocked_candidate_for_path_policy",
                    "query_label_compatible",
                    "policy_input_allowed",
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy",
                    "source_boundary_status",
                    "source_ready_after_m195",
                    "source_gap_after_m195",
                    "m202_eval_source",
                    "union_action",
                ]
            }
            out.update(
                {
                    "version": VERSION,
                    "policy_id": policy_id,
                    "visit_rank": rank,
                    "union_rank": rank,
                    "cumulative_known_path_cost_m": cumulative_known_cost,
                }
            )
            rows.append(out)
    return rows


def build_policy_rows(union_candidates: list[dict[str, Any]], episode_ids: list[str]) -> list[dict[str, Any]]:
    selected_by_episode = {episode_id: selected_candidates_for_episode(union_candidates, episode_id) for episode_id in episode_ids}
    baseline_by_episode = {
        episode_id: [
            row
            for row in selected_by_episode[episode_id]
            if row.get("candidate_source_family") == "no_source_detector"
        ]
        for episode_id in episode_ids
    }
    replacement_by_episode = {
        episode_id: [
            row
            for row in selected_by_episode[episode_id]
            if row.get("candidate_source_family") == "source_pool_detector"
        ]
        for episode_id in episode_ids
    }
    unguarded_by_episode = {episode_id: unguarded_candidates_for_episode(union_candidates, episode_id) for episode_id in episode_ids}
    out: list[dict[str, Any]] = []
    out.extend(materialize_policy_rows(SELECTED_POLICY, selected_by_episode))
    out.extend(materialize_policy_rows(BASELINE_ONLY_POLICY, baseline_by_episode))
    out.extend(materialize_policy_rows(SOURCE_POOL_REPLACEMENT_NEGATIVE, replacement_by_episode))
    out.extend(materialize_policy_rows(UNGUARDED_UNION_ABLATION, unguarded_by_episode))
    return out


def build_prefix_audit_rows(
    baseline_by_episode: dict[str, list[dict[str, Any]]],
    union_policy_rows: list[dict[str, Any]],
    episode_ids: list[str],
) -> list[dict[str, Any]]:
    selected_rows = [
        row for row in union_policy_rows if row.get("policy_id") == SELECTED_POLICY
    ]
    selected_by_episode = group_by_episode(selected_rows)
    out: list[dict[str, Any]] = []
    for episode_id in episode_ids:
        baseline_sequence = [str(row.get("proposal_uid")) for row in baseline_by_episode.get(episode_id, [])]
        selected_prefix = [
            str(row.get("proposal_uid"))
            for row in selected_by_episode.get(episode_id, [])[: len(baseline_sequence)]
        ]
        mutation_count = sum(1 for left, right in zip(baseline_sequence, selected_prefix) if left != right)
        mutation_count += abs(len(baseline_sequence) - len(selected_prefix))
        loss_count = len(set(baseline_sequence) - set(selected_prefix))
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "baseline_candidate_rows": len(baseline_sequence),
                "selected_union_candidate_rows": len(selected_by_episode.get(episode_id, [])),
                "baseline_prefix_rows_checked": len(baseline_sequence),
                "baseline_prefix_mutation_count": mutation_count,
                "baseline_candidate_loss_count": loss_count,
                "baseline_prefix_preserved": mutation_count == 0,
                "baseline_candidate_loss_free": loss_count == 0,
                "audit_pass": mutation_count == 0 and loss_count == 0,
            }
        )
    return out


def build_policy_metric_rows(union_policy_rows: list[dict[str, Any]], episode_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_policy_episode: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in union_policy_rows:
        by_policy_episode[(str(row.get("policy_id")), str(row.get("adapter_episode_id")))].append(row)
    for (policy_id, episode_id), candidates in sorted(by_policy_episode.items()):
        top5 = candidates[:5]
        rows.append(
            {
                "version": VERSION,
                "metric_scope": "m201_episode_policy_materialization",
                "policy_id": policy_id,
                "adapter_episode_id": episode_id,
                "scan_id": candidates[0].get("scan_id") if candidates else None,
                "scene_key": candidates[0].get("scene_key") if candidates else None,
                "object_category": candidates[0].get("object_category") if candidates else None,
                "candidate_rows": len(candidates),
                "baseline_candidate_rows": sum(1 for row in candidates if row.get("candidate_source_family") == "no_source_detector"),
                "source_pool_candidate_rows": sum(1 for row in candidates if row.get("candidate_source_family") == "source_pool_detector"),
                "path_ready_rows": sum(1 for row in candidates if row.get("path_ready")),
                "top5_source_pool_rows": sum(1 for row in top5 if row.get("candidate_source_family") == "source_pool_detector"),
                "top5_cumulative_known_path_cost_m": sum(
                    finite_float(row.get("source_to_candidate_path_cost_m")) or 0.0
                    for row in top5
                    if row.get("path_ready")
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in candidates
                ),
            }
        )
    policy_ids = sorted({str(row.get("policy_id")) for row in union_policy_rows})
    for policy_id in policy_ids:
        subset = [row for row in rows if row.get("policy_id") == policy_id and row.get("metric_scope") == "m201_episode_policy_materialization"]
        rows.append(
            {
                "version": VERSION,
                "metric_scope": "m201_policy_materialization_aggregate",
                "policy_id": policy_id,
                "scan_policy_rows": len(subset),
                "expected_scan_policy_rows": len(episode_ids),
                "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in subset),
                "baseline_candidate_rows": sum(int(row.get("baseline_candidate_rows") or 0) for row in subset),
                "source_pool_candidate_rows": sum(int(row.get("source_pool_candidate_rows") or 0) for row in subset),
                "path_ready_rows": sum(int(row.get("path_ready_rows") or 0) for row in subset),
                "top5_source_pool_rows": sum(int(row.get("top5_source_pool_rows") or 0) for row in subset),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in subset
                ),
            }
        )
    return rows


def build_leakage_audit_rows(union_candidate_rows: list[dict[str, Any]], union_policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, records in [
        ("union_candidate_rows", union_candidate_rows),
        ("union_policy_rows", union_policy_rows),
    ]:
        present_blocked = sorted(field for field in BLOCKED_POLICY_FIELDS if any(field in row for row in records))
        policy_leak_rows = sum(1 for row in records if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
        rows.append(
            {
                "version": VERSION,
                "artifact": name,
                "row_count": len(records),
                "blocked_policy_fields_present": present_blocked,
                "blocked_policy_field_count": len(present_blocked),
                "eval_goal_or_viewpoint_policy_leak_rows": policy_leak_rows,
                "leakage_audit_pass": not present_blocked and policy_leak_rows == 0,
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_additive_union_row_materialization",
            "supported": True,
            "claim_boundary": "M201 materializes additive union policy rows while preserving the no-source detector baseline prefix.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repaired_policy_performance",
            "supported": False,
            "claim_boundary": "M201 does not score union rows against ObjectNav goals; M202 is required before performance claims.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M201 does not execute Habitat trajectories.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_m202_additive_union_goal_eval_proxy" if ready else "repair_m201_additive_union_rows",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M201 additive source-pool candidate-union row materialization",
            "reason": "M201 preserves the protected baseline prefix, drops only duplicate source-pool candidates, and keeps leakage audit pass."
            if ready
            else "M201 failed baseline-prefix, dedup, leakage, or denominator audit.",
            "launch_long_job_now": False,
            "trajectory_execution_allowed_after_m201": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    prefix_audit_rows: list[dict[str, Any]],
    dedup_rows: list[dict[str, Any]],
    policy_metric_rows: list[dict[str, Any]],
) -> str:
    aggregate_rows = [
        row for row in policy_metric_rows if row.get("metric_scope") == "m201_policy_materialization_aggregate"
    ]
    prefix_summary = [
        {
            "audit": "baseline_prefix",
            "rows": len(prefix_audit_rows),
            "pass_rows": sum(1 for row in prefix_audit_rows if row.get("audit_pass")),
            "mutation_count": sum(int(row.get("baseline_prefix_mutation_count") or 0) for row in prefix_audit_rows),
            "loss_count": sum(int(row.get("baseline_candidate_loss_count") or 0) for row in prefix_audit_rows),
        },
        {
            "audit": "dedup",
            "rows": len(dedup_rows),
            "pass_rows": sum(1 for row in dedup_rows if row.get("dedup_pass")),
            "mutation_count": 0,
            "loss_count": sum(int(row.get("source_pool_duplicate_dropped_rows") or 0) for row in dedup_rows),
        },
    ]
    return f"""# E008-M201 Additive Source-Pool Candidate-Union Row Materialization

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M200 status: `{coverage['m200_status']}`.
- Denominator rows: {coverage['denominator_rows']}.
- Protected baseline input rows: {coverage['baseline_input_rows']}.
- Source-pool input rows: {coverage['source_pool_input_rows']}.
- Source-pool appended rows: {coverage['source_pool_appended_rows']}.
- Source-pool duplicate dropped rows: {coverage['source_pool_duplicate_dropped_rows']}.
- Selected union policy rows: {coverage['selected_union_policy_rows']}.
- Baseline prefix audit pass: {coverage['baseline_prefix_audit_pass']}.
- Baseline candidate loss count: {coverage['baseline_candidate_loss_count']}.
- Dedup audit pass: {coverage['dedup_audit_pass']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Materialization Aggregate

{markdown_table(aggregate_rows, ['policy_id', 'scan_policy_rows', 'candidate_rows', 'baseline_candidate_rows', 'source_pool_candidate_rows', 'path_ready_rows', 'top5_source_pool_rows'])}

## Audit Summary

{markdown_table(prefix_summary, ['audit', 'rows', 'pass_rows', 'mutation_count', 'loss_count'])}

## Interpretation

M201 materializes the M200 contract without changing the 30-row denominator. The selected policy keeps every protected no-source detector candidate in the same prefix order and appends only non-duplicate source-pool candidates. This is still a materialization gate, not a performance result; M202 must evaluate the frozen union rows before any trajectory or navigation claim.
"""


def main() -> None:
    m69_coverage = read_json(M69_DIR / "coverage.json")
    m70_coverage = read_json(M70_DIR / "coverage.json")
    m196_coverage = read_json(M196_DIR / "coverage.json")
    m197_coverage = read_json(M197_DIR / "coverage.json")
    m200_coverage = read_json(M200_DIR / "coverage.json")
    if not m69_coverage:
        raise SystemExit(f"missing {M69_DIR / 'coverage.json'}")
    if not m70_coverage:
        raise SystemExit(f"missing {M70_DIR / 'coverage.json'}")
    if not m196_coverage:
        raise SystemExit(f"missing {M196_DIR / 'coverage.json'}")
    if not m197_coverage:
        raise SystemExit(f"missing {M197_DIR / 'coverage.json'}")
    if not m200_coverage:
        raise SystemExit(f"missing {M200_DIR / 'coverage.json'}")

    m69_visit_rows = rows_for_policy(read_jsonl(M69_DIR / "candidate_visit_order_rows.jsonl"), PROTECTED_BASELINE)
    m70_goal_rows = rows_for_policy(read_jsonl(M70_DIR / "candidate_goal_eval_rows.jsonl"), PROTECTED_BASELINE)
    m196_visit_rows = rows_for_policy(read_jsonl(M196_DIR / "candidate_visit_order_rows.jsonl"), PROTECTED_BASELINE)
    m197_goal_rows = rows_for_policy(read_jsonl(M197_DIR / "candidate_goal_eval_rows.jsonl"), PROTECTED_BASELINE)
    boundary_rows = read_jsonl(M195_DIR / "scan_source_boundary_rows.jsonl")
    if not m69_visit_rows:
        raise SystemExit("missing M69 protected baseline visit rows")
    if not m70_goal_rows:
        raise SystemExit("missing M70 protected baseline goal-eval rows")
    if not m196_visit_rows:
        raise SystemExit("missing M196 protected source-pool visit rows")
    if not m197_goal_rows:
        raise SystemExit("missing M197 protected source-pool goal-eval rows")
    if not boundary_rows:
        raise SystemExit("missing M195 scan_source_boundary_rows.jsonl")

    baseline_by_episode = group_by_episode(m69_visit_rows)
    source_by_episode = group_by_episode(m196_visit_rows)
    boundary_by_episode = {str(row.get("adapter_episode_id")): row for row in boundary_rows}
    episode_ids = sorted(boundary_by_episode)
    baseline_position_lookup = build_eval_position_lookup(m70_goal_rows)
    source_position_lookup = build_eval_position_lookup(m197_goal_rows)

    union_candidate_rows, dedup_audit_rows = build_union_candidate_rows(
        baseline_by_episode,
        source_by_episode,
        baseline_position_lookup,
        source_position_lookup,
        boundary_by_episode,
    )
    union_policy_rows = build_policy_rows(union_candidate_rows, episode_ids)
    prefix_audit_rows = build_prefix_audit_rows(baseline_by_episode, union_policy_rows, episode_ids)
    leakage_audit_rows = build_leakage_audit_rows(union_candidate_rows, union_policy_rows)
    policy_metric_rows = build_policy_metric_rows(union_policy_rows, episode_ids)
    claim_boundary_rows = build_claim_boundary_rows()

    baseline_prefix_pass = all(row.get("audit_pass") for row in prefix_audit_rows)
    baseline_candidate_loss_count = sum(int(row.get("baseline_candidate_loss_count") or 0) for row in prefix_audit_rows)
    dedup_pass = all(row.get("dedup_pass") for row in dedup_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    selected_union_rows = [row for row in union_policy_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_episode_count = len({row.get("adapter_episode_id") for row in selected_union_rows})
    source_appended = sum(1 for row in union_candidate_rows if row.get("union_action") == "append_source_pool")
    source_dropped = sum(1 for row in union_candidate_rows if row.get("union_action") == "drop_duplicate_source_pool")
    source_gap_rows = sum(1 for row in boundary_rows if row.get("source_gap"))
    source_ready_rows = sum(1 for row in boundary_rows if row.get("source_ready"))
    missing_position_rows = sum(1 for row in union_candidate_rows if row.get("candidate_snapped_position_m") is None)
    ready = (
        selected_episode_count == len(episode_ids)
        and baseline_prefix_pass
        and baseline_candidate_loss_count == 0
        and dedup_pass
        and leakage_pass
        and missing_position_rows == 0
        and len(episode_ids) == int(m200_coverage.get("denominator_rows") or len(episode_ids))
    )
    route_decision_rows = build_route_decision_rows(ready)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m69_status": m69_coverage.get("status"),
        "m70_status": m70_coverage.get("status"),
        "m196_status": m196_coverage.get("status"),
        "m197_status": m197_coverage.get("status"),
        "m200_status": m200_coverage.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "baseline_only_policy_id": BASELINE_ONLY_POLICY,
        "negative_replacement_policy_id": SOURCE_POOL_REPLACEMENT_NEGATIVE,
        "unguarded_union_ablation_policy_id": UNGUARDED_UNION_ABLATION,
        "denominator_rows": len(episode_ids),
        "expected_denominator_rows": m200_coverage.get("denominator_rows"),
        "source_ready_rows": source_ready_rows,
        "source_gap_rows": source_gap_rows,
        "baseline_input_rows": len(m69_visit_rows),
        "source_pool_input_rows": len(m196_visit_rows),
        "source_pool_appended_rows": source_appended,
        "source_pool_duplicate_dropped_rows": source_dropped,
        "union_candidate_rows": len(union_candidate_rows),
        "union_policy_rows": len(union_policy_rows),
        "selected_union_policy_rows": len(selected_union_rows),
        "selected_union_episode_rows": selected_episode_count,
        "baseline_prefix_audit_rows": len(prefix_audit_rows),
        "baseline_prefix_audit_pass": baseline_prefix_pass,
        "baseline_candidate_loss_count": baseline_candidate_loss_count,
        "dedup_audit_rows": len(dedup_audit_rows),
        "dedup_audit_pass": dedup_pass,
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "missing_candidate_position_rows": missing_position_rows,
        "m202_proxy_eval_ready": ready,
        "trajectory_execution_promoted": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "union_candidate_rows.jsonl", union_candidate_rows)
        write_jsonl(output_dir / "union_policy_rows.jsonl", union_policy_rows)
        write_jsonl(output_dir / "baseline_prefix_audit_rows.jsonl", prefix_audit_rows)
        write_jsonl(output_dir / "dedup_audit_rows.jsonl", dedup_audit_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "policy_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, prefix_audit_rows, dedup_audit_rows, policy_metric_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
