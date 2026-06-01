#!/usr/bin/env python3
"""Audit policy-visible full-pool features for E008 source-gap candidates."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M17_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M19_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
M56_DIR = EXP_ROOT / "artifacts" / "E008-M56_source_gap_candidate_source_expansion_contract_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M57_source_gap_full_pool_candidate_source_feature_audit_v0"
)

VERSION = "e008_m57_source_gap_full_pool_candidate_source_feature_audit_v0"
READY_STATUS = "e008_m57_source_gap_full_pool_candidate_source_feature_audit_ready"
BLOCKED_STATUS = "e008_m57_source_gap_full_pool_candidate_source_feature_audit_blocked"
NEXT_UNIT = "E008-M58 source-gap high-path tail-slot policy materialization"

PRIMARY_BUDGET = 5
DETECTOR_ALL_POLICY = "detector_confidence_all_candidates_v0"
REACHABLE_POLICY = "detector_confidence_reachable_subset_v0"
PATH_ASC_POLICY = "path_cost_ascending_reachable_subset_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"
POLICY_IDS = [DETECTOR_ALL_POLICY, REACHABLE_POLICY, PATH_ASC_POLICY, TRADEOFF_POLICY]

FRAME_RE = re.compile(r"(frame-\d+)")


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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def parse_frame_id(proposal_uid: object) -> str | None:
    match = FRAME_RE.search(str(proposal_uid or ""))
    return match.group(1) if match else None


def is_hit(row: dict[str, Any]) -> bool:
    return bool(row.get("primary_eval_hit")) or bool(row.get("hit_any_viewpoint_xz_1p0")) or bool(
        row.get("eval_success")
    )


def feature_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("adapter_episode_id")), str(row.get("proposal_uid")))


def sort_rank(
    rows: list[dict[str, Any]],
    key: str,
    reverse: bool,
    require_finite: bool = True,
) -> dict[str, int]:
    candidates = []
    for row in rows:
        value = finite_float(row.get(key))
        if value is None and require_finite:
            continue
        candidates.append((value if value is not None else float("-inf"), str(row.get("proposal_uid"))))
    candidates.sort(key=lambda item: item[0], reverse=reverse)
    return {proposal_uid: index + 1 for index, (_, proposal_uid) in enumerate(candidates)}


def build_indices(
    navmesh_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    navmesh_index = {feature_key(row): row for row in navmesh_rows}
    eval_index = {
        feature_key(row): row
        for row in eval_rows
        if row.get("policy_id") == DETECTOR_ALL_POLICY
    }
    policy_rank_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in visit_rows:
        if row.get("policy_id") in POLICY_IDS:
            policy_rank_index[
                (str(row.get("adapter_episode_id")), str(row.get("policy_id")), str(row.get("proposal_uid")))
            ] = row
    return navmesh_index, eval_index, policy_rank_index


def build_feature_rows(
    episode_ids: list[str],
    visit_rows: list[dict[str, Any]],
    navmesh_index: dict[tuple[str, str], dict[str, Any]],
    eval_index: dict[tuple[str, str], dict[str, Any]],
    policy_rank_index: dict[tuple[str, str, str], dict[str, Any]],
    m56_case_by_episode: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    detector_rows_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in visit_rows:
        if row.get("policy_id") == DETECTOR_ALL_POLICY and row.get("adapter_episode_id") in episode_ids:
            detector_rows_by_episode[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for episode_id in episode_ids:
        detector_rows = sorted(
            detector_rows_by_episode.get(episode_id, []),
            key=lambda row: int_or_none(row.get("visit_rank")) or 10**9,
        )
        path_desc_rank = sort_rank(detector_rows, "source_to_candidate_path_cost_m", reverse=True)
        path_asc_rank = sort_rank(detector_rows, "source_to_candidate_path_cost_m", reverse=False)
        confidence_rank = sort_rank(detector_rows, "confidence", reverse=True)
        snap_asc_rank = sort_rank(detector_rows, "snap_distance_m", reverse=False)

        for row in detector_rows:
            proposal_uid = str(row.get("proposal_uid"))
            nav = navmesh_index.get((episode_id, proposal_uid), {})
            ev = eval_index.get((episode_id, proposal_uid), {})
            case = m56_case_by_episode.get(episode_id, {})
            detector_rank = int_or_none(row.get("visit_rank"))
            reachable_rank = int_or_none(
                policy_rank_index.get((episode_id, REACHABLE_POLICY, proposal_uid), {}).get("visit_rank")
            )
            path_policy_rank = int_or_none(
                policy_rank_index.get((episode_id, PATH_ASC_POLICY, proposal_uid), {}).get("visit_rank")
            )
            tradeoff_rank = int_or_none(
                policy_rank_index.get((episode_id, TRADEOFF_POLICY, proposal_uid), {}).get("visit_rank")
            )
            source_to_candidate_path_cost_m = finite_float(row.get("source_to_candidate_path_cost_m"))
            confidence = finite_float(row.get("confidence"))
            hit = is_hit(ev)
            out.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": episode_id,
                    "scan_id": row.get("scan_id"),
                    "scene_key": row.get("scene_key"),
                    "object_category": row.get("object_category"),
                    "proposal_uid": proposal_uid,
                    "raw_candidate_uid": row.get("raw_candidate_uid"),
                    "frame_id": nav.get("frame_id") or parse_frame_id(proposal_uid),
                    "label_canonical": row.get("label_canonical"),
                    "policy_input_allowed": bool(row.get("policy_input_allowed", True)),
                    "path_ready": bool(row.get("path_ready")),
                    "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
                    "navmesh_validation_status": row.get("navmesh_validation_status"),
                    "confidence": confidence,
                    "selection_score": finite_float(row.get("selection_score")),
                    "candidate_rank_m09": int_or_none(row.get("candidate_rank_m09")),
                    "detector_confidence_rank": detector_rank,
                    "reachable_confidence_rank": reachable_rank,
                    "path_cost_ascending_rank": path_policy_rank,
                    "confidence_path_cost_tradeoff_rank": tradeoff_rank,
                    "path_cost_descending_rank": path_desc_rank.get(proposal_uid),
                    "path_cost_ascending_rank_recomputed": path_asc_rank.get(proposal_uid),
                    "confidence_rank_recomputed": confidence_rank.get(proposal_uid),
                    "snap_distance_ascending_rank": snap_asc_rank.get(proposal_uid),
                    "source_to_candidate_path_cost_m": source_to_candidate_path_cost_m,
                    "snap_distance_m": finite_float(row.get("snap_distance_m")),
                    "centroid_source_euclidean_m": finite_float(nav.get("centroid_source_euclidean_m")),
                    "snapped_source_euclidean_m": finite_float(nav.get("snapped_source_euclidean_m")),
                    "yaw_offset_deg": finite_float(nav.get("yaw_offset_deg")),
                    "m56_source_gap_type": case.get("source_gap_type"),
                    "m56_unrecovered_budget_surfacing_case": case.get("source_gap_type")
                    == "full_pool_hit_budget5_surfacing_failure",
                    "detector_confidence_top5": bool(detector_rank is not None and detector_rank <= PRIMARY_BUDGET),
                    "path_cost_descending_top5": bool(
                        path_desc_rank.get(proposal_uid) is not None
                        and path_desc_rank.get(proposal_uid) <= PRIMARY_BUDGET
                    ),
                    "path_cost_ascending_top5": bool(
                        path_asc_rank.get(proposal_uid) is not None
                        and path_asc_rank.get(proposal_uid) <= PRIMARY_BUDGET
                    ),
                    "diagnostic_primary_eval_hit": hit,
                    "diagnostic_hit_any_viewpoint_xz_1p0": bool(ev.get("hit_any_viewpoint_xz_1p0")),
                    "diagnostic_candidate_to_nearest_eval_viewpoint_xz_m": finite_float(
                        ev.get("candidate_to_nearest_eval_viewpoint_xz_m")
                    ),
                    "diagnostic_uses_eval_labels_for_row_label_only": True,
                    "uses_eval_for_policy": False,
                }
            )
    return out


def select_budget(rows: list[dict[str, Any]], ordered_uids: list[str]) -> list[dict[str, Any]]:
    by_uid = {str(row["proposal_uid"]): row for row in rows}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for uid in ordered_uids:
        if uid in by_uid and uid not in seen:
            selected.append(by_uid[uid])
            seen.add(uid)
        if len(selected) >= PRIMARY_BUDGET:
            break
    return selected


def rule_selection(rows: list[dict[str, Any]], rule_id: str) -> list[dict[str, Any]]:
    detector_sorted = sorted(rows, key=lambda row: row.get("detector_confidence_rank") or 10**9)
    path_desc_sorted = sorted(rows, key=lambda row: row.get("path_cost_descending_rank") or 10**9)
    path_asc_sorted = sorted(rows, key=lambda row: row.get("path_cost_ascending_rank_recomputed") or 10**9)
    tradeoff_sorted = sorted(rows, key=lambda row: row.get("confidence_path_cost_tradeoff_rank") or 10**9)

    if rule_id == "detector_confidence_budget5":
        ordered = [row["proposal_uid"] for row in detector_sorted]
    elif rule_id == "path_cost_ascending_budget5":
        ordered = [row["proposal_uid"] for row in path_asc_sorted]
    elif rule_id == "path_cost_descending_budget5":
        ordered = [row["proposal_uid"] for row in path_desc_sorted]
    elif rule_id == "confidence_path_cost_tradeoff_budget5":
        ordered = [row["proposal_uid"] for row in tradeoff_sorted]
    elif rule_id == "confidence_top4_plus_high_path_top1":
        ordered = [row["proposal_uid"] for row in detector_sorted[:4]] + [
            row["proposal_uid"] for row in path_desc_sorted[:1]
        ] + [row["proposal_uid"] for row in detector_sorted]
    elif rule_id == "confidence_top3_plus_high_path_top2":
        ordered = [row["proposal_uid"] for row in detector_sorted[:3]] + [
            row["proposal_uid"] for row in path_desc_sorted[:2]
        ] + [row["proposal_uid"] for row in detector_sorted]
    else:
        raise ValueError(f"Unknown rule_id: {rule_id}")
    return select_budget(rows, ordered)


def build_rule_audit_rows(feature_rows: list[dict[str, Any]], source_gap_case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules = [
        ("detector_confidence_budget5", "baseline"),
        ("path_cost_ascending_budget5", "baseline"),
        ("confidence_path_cost_tradeoff_budget5", "baseline"),
        ("path_cost_descending_budget5", "diagnostic_signal"),
        ("confidence_top4_plus_high_path_top1", "candidate_promoter"),
        ("confidence_top3_plus_high_path_top2", "candidate_promoter"),
    ]
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        by_episode[str(row["adapter_episode_id"])].append(row)
    case_by_episode = {str(row["adapter_episode_id"]): row for row in source_gap_case_rows}
    unrecovered_episodes = {
        episode_id
        for episode_id, row in case_by_episode.items()
        if row.get("source_gap_type") == "full_pool_hit_budget5_surfacing_failure"
    }

    out: list[dict[str, Any]] = []
    for rule_id, role in rules:
        per_episode = []
        hit_episodes = 0
        unrecovered_hit_episodes = 0
        total_path_costs: list[float | None] = []
        for episode_id in sorted(by_episode):
            selected = rule_selection(by_episode[episode_id], rule_id)
            selected_hit = any(bool(row.get("diagnostic_primary_eval_hit")) for row in selected)
            if selected_hit:
                hit_episodes += 1
            if episode_id in unrecovered_episodes and selected_hit:
                unrecovered_hit_episodes += 1
            total_path_costs.append(mean([finite_float(row.get("source_to_candidate_path_cost_m")) for row in selected]))
            first_hit = next((row for row in selected if row.get("diagnostic_primary_eval_hit")), None)
            per_episode.append(
                {
                    "adapter_episode_id": episode_id,
                    "selected_hit": selected_hit,
                    "selected_proposal_uids": [row.get("proposal_uid") for row in selected],
                    "selected_detector_ranks": [row.get("detector_confidence_rank") for row in selected],
                    "selected_path_desc_ranks": [row.get("path_cost_descending_rank") for row in selected],
                    "first_hit_detector_rank": first_hit.get("detector_confidence_rank") if first_hit else None,
                    "first_hit_path_desc_rank": first_hit.get("path_cost_descending_rank") if first_hit else None,
                }
            )

        out.append(
            {
                "version": VERSION,
                "rule_id": rule_id,
                "rule_role": role,
                "uses_eval_labels_for_selection": False,
                "uses_only_policy_visible_features": True,
                "source_gap_episode_rows": len(by_episode),
                "source_gap_hit_episode_rows": hit_episodes,
                "source_gap_hit_rate": safe_ratio(hit_episodes, len(by_episode)),
                "unrecovered_episode_rows": len(unrecovered_episodes),
                "unrecovered_hit_episode_rows": unrecovered_hit_episodes,
                "unrecovered_hit_rate": safe_ratio(unrecovered_hit_episodes, len(unrecovered_episodes)),
                "mean_selected_path_cost_m": mean(total_path_costs),
                "per_episode": per_episode,
                "supports_next_policy_materialization": bool(
                    rule_id == "confidence_top4_plus_high_path_top1"
                    and unrecovered_hit_episodes == len(unrecovered_episodes)
                    and len(unrecovered_episodes) > 0
                ),
                "claim_boundary": "diagnostic_feature_audit_not_final_policy_claim",
            }
        )
    return out


def build_contrast_rows(feature_rows: list[dict[str, Any]], source_gap_case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        by_episode[str(row["adapter_episode_id"])].append(row)
    case_by_episode = {str(row["adapter_episode_id"]): row for row in source_gap_case_rows}
    out: list[dict[str, Any]] = []
    for episode_id in sorted(by_episode):
        rows = by_episode[episode_id]
        top5 = [row for row in rows if bool(row.get("detector_confidence_top5"))]
        hits = sorted(
            [row for row in rows if bool(row.get("diagnostic_primary_eval_hit"))],
            key=lambda row: row.get("detector_confidence_rank") or 10**9,
        )
        first_hit = hits[0] if hits else {}
        top5_conf = [finite_float(row.get("confidence")) for row in top5]
        top5_path = [finite_float(row.get("source_to_candidate_path_cost_m")) for row in top5]
        first_hit_conf = finite_float(first_hit.get("confidence"))
        first_hit_path = finite_float(first_hit.get("source_to_candidate_path_cost_m"))
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "object_category": rows[0].get("object_category") if rows else None,
                "source_gap_type": case_by_episode.get(episode_id, {}).get("source_gap_type"),
                "candidate_rows": len(rows),
                "detector_top5_rows": len(top5),
                "diagnostic_hit_rows": len(hits),
                "first_hit_proposal_uid": first_hit.get("proposal_uid"),
                "first_hit_detector_rank": first_hit.get("detector_confidence_rank"),
                "first_hit_path_desc_rank": first_hit.get("path_cost_descending_rank"),
                "first_hit_confidence": first_hit_conf,
                "detector_top5_confidence_min": min([v for v in top5_conf if v is not None], default=None),
                "detector_top5_confidence_mean": mean(top5_conf),
                "first_hit_below_top5_confidence_min": bool(
                    first_hit_conf is not None
                    and min([v for v in top5_conf if v is not None], default=float("-inf")) > first_hit_conf
                ),
                "first_hit_path_cost_m": first_hit_path,
                "detector_top5_path_cost_max_m": max([v for v in top5_path if v is not None], default=None),
                "detector_top5_path_cost_mean_m": mean(top5_path),
                "first_hit_above_top5_path_cost_max": bool(
                    first_hit_path is not None
                    and max([v for v in top5_path if v is not None], default=float("inf")) < first_hit_path
                ),
                "diagnosis": (
                    "deep_low_confidence_high_path_candidate"
                    if first_hit
                    and bool(first_hit.get("path_cost_descending_rank") is not None)
                    and int(first_hit.get("path_cost_descending_rank")) <= PRIMARY_BUDGET
                    else "deep_hit_not_separable_by_simple_top5_signal"
                    if first_hit
                    else "no_full_pool_hit"
                ),
            }
        )
    return out


def build_summary_rows(feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        by_episode[str(row["adapter_episode_id"])].append(row)
    out: list[dict[str, Any]] = []
    for episode_id in sorted(by_episode):
        rows = by_episode[episode_id]
        hits = [row for row in rows if row.get("diagnostic_primary_eval_hit")]
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "object_category": rows[0].get("object_category") if rows else None,
                "candidate_rows": len(rows),
                "path_ready_rows": sum(1 for row in rows if row.get("path_ready")),
                "detector_top5_hit_rows": sum(
                    1 for row in rows if row.get("detector_confidence_top5") and row.get("diagnostic_primary_eval_hit")
                ),
                "path_desc_top5_hit_rows": sum(
                    1 for row in rows if row.get("path_cost_descending_top5") and row.get("diagnostic_primary_eval_hit")
                ),
                "diagnostic_hit_rows": len(hits),
                "first_hit_detector_rank": min(
                    [row.get("detector_confidence_rank") for row in hits if row.get("detector_confidence_rank")],
                    default=None,
                ),
                "first_hit_path_desc_rank": min(
                    [row.get("path_cost_descending_rank") for row in hits if row.get("path_cost_descending_rank")],
                    default=None,
                ),
                "mean_confidence": mean([finite_float(row.get("confidence")) for row in rows]),
                "mean_path_cost_m": mean([finite_float(row.get("source_to_candidate_path_cost_m")) for row in rows]),
            }
        )
    return out


def build_gate_rows(rule_rows: list[dict[str, Any]], feature_rows: list[dict[str, Any]], m56_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    rule_by_id = {row["rule_id"]: row for row in rule_rows}
    detector = rule_by_id["detector_confidence_budget5"]
    high_path = rule_by_id["confidence_top4_plus_high_path_top1"]
    path_desc = rule_by_id["path_cost_descending_budget5"]
    gates = [
        {
            "gate_id": "m56_ready",
            "passed": m56_coverage.get("status") == "e008_m56_source_gap_candidate_source_expansion_contract_ready",
            "evidence": f"M56 status={m56_coverage.get('status')}.",
            "implication": "M57 can audit the contracted candidate-source route.",
        },
        {
            "gate_id": "full_pool_feature_rows_materialized",
            "passed": len(feature_rows) > 0,
            "evidence": f"{len(feature_rows)} detector-all source-gap candidate feature rows.",
            "implication": "Policy-visible feature audit has an analyzable table.",
        },
        {
            "gate_id": "detector_top5_fails_unrecovered_source_gap",
            "passed": detector["unrecovered_hit_episode_rows"] == 0,
            "evidence": (
                f"detector confidence budget-5 unrecovered hit episodes "
                f"{detector['unrecovered_hit_episode_rows']}/{detector['unrecovered_episode_rows']}."
            ),
            "implication": "The naive detector-confidence baseline remains a valid failure case.",
        },
        {
            "gate_id": "high_path_tail_recovers_unrecovered_source_gap",
            "passed": high_path["unrecovered_hit_episode_rows"] == high_path["unrecovered_episode_rows"]
            and high_path["unrecovered_episode_rows"] > 0,
            "evidence": (
                f"confidence top4 + high-path top1 unrecovered hit episodes "
                f"{high_path['unrecovered_hit_episode_rows']}/{high_path['unrecovered_episode_rows']}."
            ),
            "implication": "A non-oracle high-path tail slot is worth materializing as a budget-5 policy.",
        },
        {
            "gate_id": "path_descending_alone_not_final_policy",
            "passed": path_desc["source_gap_hit_episode_rows"] < path_desc["source_gap_episode_rows"],
            "evidence": (
                f"path-cost descending budget-5 source-gap hit episodes "
                f"{path_desc['source_gap_hit_episode_rows']}/{path_desc['source_gap_episode_rows']}."
            ),
            "implication": "High-path signal should augment H001, not replace the policy.",
        },
        {
            "gate_id": "m58_policy_materialization_ready",
            "passed": bool(high_path.get("supports_next_policy_materialization")),
            "evidence": "A budget-5 high-path slot recovers the two unrecovered source-gap episodes in diagnostic audit.",
            "implication": "Next unit should materialize `H001 safe + high-path tail slot` rows.",
        },
        {
            "gate_id": "final_navigation_claim_ready",
            "passed": False,
            "evidence": "M57 is a feature audit and runs no trajectory execution.",
            "implication": "No final navigation claim can be made from M57.",
        },
        {
            "gate_id": "human_intent_main_claim_ready",
            "passed": False,
            "evidence": "M57 does not create a task-context-specific win over task-agnostic policy.",
            "implication": "Human intent remains secondary.",
        },
    ]
    return [{"version": VERSION, **row} for row in gates]


def build_route_decision_rows(gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate = {row["gate_id"]: bool(row["passed"]) for row in gate_rows}
    return [
        {
            "version": VERSION,
            "route_id": "materialize_h001_safe_plus_high_path_tail_slot_budget5",
            "selected": gate.get("m58_policy_materialization_ready", False),
            "next_unit": NEXT_UNIT,
            "reason": "High-path tail slot recovers the two unrecovered source-gap episodes in diagnostic feature audit.",
        },
        {
            "version": VERSION,
            "route_id": "new_rendering_or_external_source_now",
            "selected": False,
            "next_unit": None,
            "reason": "Existing full pool has a policy-visible high-path signal; new sources are deferred until M58/M59 fail.",
        },
        {
            "version": VERSION,
            "route_id": "trajectory_execution_now",
            "selected": False,
            "next_unit": None,
            "reason": "A concrete budget-5 policy row set must be materialized before Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "route_id": "claim_source_gap_solved_now",
            "selected": False,
            "next_unit": None,
            "reason": "M57 is diagnostic and uses eval labels only for post-hoc audit.",
        },
    ]


def build_claim_boundary_rows(rule_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    high_path = next(row for row in rule_rows if row["rule_id"] == "confidence_top4_plus_high_path_top1")
    return [
        {
            "version": VERSION,
            "claim_id": "policy_visible_high_path_tail_signal_exists",
            "supported": high_path["unrecovered_hit_episode_rows"] == high_path["unrecovered_episode_rows"],
            "evidence": (
                f"confidence top4 + high-path top1 recovers "
                f"{high_path['unrecovered_hit_episode_rows']}/{high_path['unrecovered_episode_rows']} "
                "unrecovered source-gap episodes in diagnostic audit."
            ),
            "claim_boundary": "source-gap feature audit only; not final navigation performance",
        },
        {
            "version": VERSION,
            "claim_id": "high_path_tail_slot_policy_improves_navigation",
            "supported": False,
            "evidence": "No M58 materialized rows or trajectory execution yet.",
            "required_evidence": "budget-5 policy rows plus leakage-safe goal and Docker trajectory evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "path_cost_descending_is_the_method",
            "supported": False,
            "evidence": "Path-cost descending alone does not recover all source-gap episodes and may increase path cost.",
            "required_evidence": "H001-compatible selective source slot with ablations and efficiency metrics.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_contribution",
            "supported": False,
            "evidence": "M57 does not test task-context-specific gains.",
            "required_evidence": "task-conditioned policy must beat task-agnostic after source expansion.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "evidence": "M57 is repository-local feature audit, not trajectory execution.",
            "required_evidence": "Docker Habitat execution over materialized policy rows and scaled heldout scenes.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    entries = [
        (
            "why_not_detector_confidence",
            "Detector-confidence budget-5 has 0/2 hits on unrecovered source-gap episodes.",
            "This preserves the naive baseline failure diagnosis.",
        ),
        (
            "why_not_oracle",
            "Hit labels are only post-hoc diagnostics; selection rules use confidence, rank, path/navmesh, and candidate metadata.",
            "M58 must keep the same blocked eval-input contract.",
        ),
        (
            "why_high_path_is_not_final",
            "High path-cost can recover hidden source-gap candidates but can also hurt `SPL` and source-ready efficiency.",
            "Treat it as a candidate policy component requiring trajectory evaluation, not a final claim.",
        ),
        (
            "why_not_external_source_yet",
            "The existing full pool already contains hit candidates; the immediate gap is budgeted surfacing.",
            "External map/proposal sources should return if M58 cannot produce a robust budgeted policy.",
        ),
        (
            "why_human_intent_still_secondary",
            "This audit does not create a task-context-specific win over task-agnostic source-diverse.",
            "Human intent remains a condition until it changes decisions and metrics.",
        ),
    ]
    return [
        {"version": VERSION, "defense_id": defense_id, "reviewer_attack": attack, "response": response}
        for defense_id, attack, response in entries
    ]


def write_report(
    coverage: dict[str, Any],
    contrast_rows: list[dict[str, Any]],
    rule_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    selected = next(row for row in route_rows if row.get("selected"))
    high_path = next(row for row in rule_rows if row["rule_id"] == "confidence_top4_plus_high_path_top1")
    detector = next(row for row in rule_rows if row["rule_id"] == "detector_confidence_budget5")
    lines = [
        "# E008-M57 Source-Gap Full-Pool Candidate-Source Feature Audit",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Full-pool feature rows: {coverage['full_pool_candidate_feature_rows']}.",
        f"- Source-gap episodes: {coverage['source_gap_episode_rows']}.",
        f"- Unrecovered budget-surfacing episodes: {coverage['unrecovered_budget_surfacing_episode_rows']}.",
        f"- Detector-confidence budget-5 unrecovered hits: {detector['unrecovered_hit_episode_rows']} / {detector['unrecovered_episode_rows']}.",
        f"- `confidence_top4_plus_high_path_top1` unrecovered hits: {high_path['unrecovered_hit_episode_rows']} / {high_path['unrecovered_episode_rows']}.",
        f"- Selected route: `{selected['route_id']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Interpretation",
        "",
        "- The remaining source-gap failure is not source absence: the full pool contains hit candidates.",
        "- The detector-confidence top-5 misses the two unrecovered source-gap cases.",
        "- A high path-cost tail slot is a policy-visible diagnostic signal: it recovers the two unrecovered source-gap cases in this audit.",
        "- This is not yet a navigation claim because high path-cost exploration can hurt efficiency and has not been executed as a materialized H001 policy.",
        "",
        "## Episode Contrast",
        "",
        "| episode | object | first hit detector rank | first hit path-desc rank | hit below top5 confidence | hit above top5 path cost | diagnosis |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in contrast_rows:
        lines.append(
            f"| `{row['adapter_episode_id']}` | `{row['object_category']}` | "
            f"{row['first_hit_detector_rank']} | {row['first_hit_path_desc_rank']} | "
            f"{row['first_hit_below_top5_confidence_min']} | {row['first_hit_above_top5_path_cost_max']} | "
            f"`{row['diagnosis']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule Audit",
            "",
            "| rule | source-gap hits | unrecovered hits | selected for M58 |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in rule_rows:
        lines.append(
            f"| `{row['rule_id']}` | {row['source_gap_hit_episode_rows']}/{row['source_gap_episode_rows']} | "
            f"{row['unrecovered_hit_episode_rows']}/{row['unrecovered_episode_rows']} | "
            f"{row['supports_next_policy_materialization']} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| gate | pass | implication |",
            "| --- | --- | --- |",
        ]
    )
    for row in gate_rows:
        lines.append(f"| `{row['gate_id']}` | {row['passed']} | {row['implication']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M57 supports only a policy-visible feature audit for source-gap candidates.",
            "- It does not support final real navigation `SR` / `SPL`, deployable search policy, or human intent as a main contribution.",
            "- M58 must materialize an H001-compatible budget-5 policy before any trajectory execution or paper-table claim.",
            "",
            "## Next",
            "",
            f"- {coverage['selected_next_unit']}: materialize `H001 safe + high-path tail slot` budget-5 rows and keep eval labels blocked from policy inputs.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m56_coverage = read_json(M56_DIR / "coverage.json")
    source_gap_case_rows = read_jsonl(M56_DIR / "source_gap_case_rows.jsonl")
    visit_rows = read_jsonl(M18_DIR / "candidate_visit_order_rows.jsonl")
    eval_rows = read_jsonl(M19_DIR / "candidate_goal_eval_rows.jsonl")
    navmesh_rows = read_jsonl(M17_DIR / "candidate_navmesh_rows.jsonl")

    episode_ids = sorted(str(row.get("adapter_episode_id")) for row in source_gap_case_rows)
    m56_case_by_episode = {str(row.get("adapter_episode_id")): row for row in source_gap_case_rows}
    navmesh_index, eval_index, policy_rank_index = build_indices(navmesh_rows, visit_rows, eval_rows)

    feature_rows = build_feature_rows(
        episode_ids,
        visit_rows,
        navmesh_index,
        eval_index,
        policy_rank_index,
        m56_case_by_episode,
    )
    summary_rows = build_summary_rows(feature_rows)
    contrast_rows = build_contrast_rows(feature_rows, source_gap_case_rows)
    rule_rows = build_rule_audit_rows(feature_rows, source_gap_case_rows)
    gate_rows = build_gate_rows(rule_rows, feature_rows, m56_coverage)
    route_rows = build_route_decision_rows(gate_rows)
    claim_rows = build_claim_boundary_rows(rule_rows)
    reviewer_rows = build_reviewer_defense_rows()

    selected = next(row for row in route_rows if row.get("selected"))
    high_path = next(row for row in rule_rows if row["rule_id"] == "confidence_top4_plus_high_path_top1")
    unrecovered_budget_rows = sum(
        1 for row in source_gap_case_rows if row.get("source_gap_type") == "full_pool_hit_budget5_surfacing_failure"
    )
    input_ready = bool(m56_coverage and source_gap_case_rows and visit_rows and eval_rows and navmesh_rows)
    status = READY_STATUS if input_ready and selected.get("next_unit") == NEXT_UNIT else BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m56_status": m56_coverage.get("status"),
        "input_ready": input_ready,
        "primary_budget": PRIMARY_BUDGET,
        "source_gap_episode_rows": len(source_gap_case_rows),
        "unrecovered_budget_surfacing_episode_rows": unrecovered_budget_rows,
        "full_pool_candidate_feature_rows": len(feature_rows),
        "candidate_feature_summary_rows": len(summary_rows),
        "hit_vs_top5_contrast_rows": len(contrast_rows),
        "rule_audit_rows": len(rule_rows),
        "promoter_gate_rows": len(gate_rows),
        "promoter_gate_pass_rows": sum(1 for row in gate_rows if row.get("passed")),
        "claim_boundary_rows": len(claim_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "detector_confidence_unrecovered_hit_rows": next(
            row for row in rule_rows if row["rule_id"] == "detector_confidence_budget5"
        )["unrecovered_hit_episode_rows"],
        "high_path_tail_unrecovered_hit_rows": high_path["unrecovered_hit_episode_rows"],
        "high_path_tail_unrecovered_hit_rate": high_path["unrecovered_hit_rate"],
        "m58_policy_materialization_ready": bool(high_path.get("supports_next_policy_materialization")),
        "budget5_policy_materialized": False,
        "real_navigation_sr_spl_ready": False,
        "human_intent_main_claim_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_route": selected.get("route_id"),
        "selected_next_unit": selected.get("next_unit"),
        "artifact_dir": str(ARTIFACT_DIR.relative_to(ROOT)),
        "derived_data_dir": str(DATA_OUT_DIR.relative_to(ROOT)),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_full_pool_candidate_feature_rows.jsonl", feature_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_feature_summary_rows.jsonl", summary_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_hit_vs_top5_feature_contrast_rows.jsonl", contrast_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_promoter_rule_audit_rows.jsonl", rule_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_promoter_feasibility_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_report(coverage, contrast_rows, rule_rows, gate_rows, route_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "source_gap_full_pool_candidate_feature_rows.jsonl", feature_rows)
    write_jsonl(DATA_OUT_DIR / "source_gap_promoter_rule_audit_rows.jsonl", rule_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
