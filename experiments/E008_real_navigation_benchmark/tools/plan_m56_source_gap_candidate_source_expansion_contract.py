#!/usr/bin/env python3
"""Define the source-gap candidate-source expansion contract after M55."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M16_DIR = EXP_ROOT / "artifacts" / "E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0"
M18_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M19_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
M43_DIR = EXP_ROOT / "artifacts" / "E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0"
M55_DIR = EXP_ROOT / "artifacts" / "E008-M55_source_gap_candidate_generation_repair_feasibility_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M56_source_gap_candidate_source_expansion_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M56_source_gap_candidate_source_expansion_contract_v0"
)

VERSION = "e008_m56_source_gap_candidate_source_expansion_contract_v0"
READY_STATUS = "e008_m56_source_gap_candidate_source_expansion_contract_ready"
BLOCKED_STATUS = "e008_m56_source_gap_candidate_source_expansion_contract_blocked"
NEXT_UNIT = "E008-M57 source-gap full-pool candidate-source feature audit"

PRIMARY_BUDGET = 5
FULL_POOL_PRIMARY_POLICY = "detector_confidence_all_candidates_v0"
REACHABLE_POLICY = "detector_confidence_reachable_subset_v0"
PATH_POLICY = "path_cost_ascending_reachable_subset_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"
M19_POLICIES = [FULL_POOL_PRIMARY_POLICY, REACHABLE_POLICY, PATH_POLICY, TRADEOFF_POLICY]


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


def min_finite(values: list[object]) -> float | None:
    clean = [finite_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return min(clean) if clean else None


def int_or_none(value: object) -> int | None:
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out


def is_hit(row: dict[str, Any]) -> bool:
    return bool(row.get("primary_eval_hit")) or bool(row.get("hit_any_viewpoint_xz_1p0")) or bool(
        row.get("eval_success")
    )


def build_visit_index(visit_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in visit_rows:
        out[(str(row.get("adapter_episode_id")), str(row.get("policy_id")), str(row.get("proposal_uid")))] = row
    return out


def first_hit(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    hits = [row for row in rows if is_hit(row)]
    hits.sort(key=lambda row: int_or_none(row.get("visit_rank")) or 10**9)
    return hits[0] if hits else None


def rows_by_episode_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)
    return out


def source_gap_episode_ids(m55_episode_rows: list[dict[str, Any]]) -> list[str]:
    return sorted(str(row.get("adapter_episode_id")) for row in m55_episode_rows)


def build_full_pool_hit_diagnostic_rows(
    episode_ids: list[str],
    m19_rows: list[dict[str, Any]],
    visit_index: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = rows_by_episode_policy(m19_rows)
    out: list[dict[str, Any]] = []
    for episode_id in episode_ids:
        for policy_id in M19_POLICIES:
            rows = grouped.get((episode_id, policy_id), [])
            hit = first_hit(rows)
            visit = {}
            if hit:
                visit = visit_index.get((episode_id, policy_id, str(hit.get("proposal_uid"))), {})
            hit_rank = int_or_none(hit.get("visit_rank")) if hit else None
            out.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": episode_id,
                    "policy_id": policy_id,
                    "candidate_rows": len(rows),
                    "path_ready_rows": sum(1 for row in rows if bool(row.get("path_ready"))),
                    "hit_rows": sum(1 for row in rows if is_hit(row)),
                    "first_hit_rank": hit_rank,
                    "first_hit_inside_budget5": bool(hit_rank is not None and hit_rank <= PRIMARY_BUDGET),
                    "first_hit_proposal_uid": hit.get("proposal_uid") if hit else None,
                    "first_hit_label_canonical": hit.get("label_canonical") if hit else None,
                    "first_hit_confidence": visit.get("confidence"),
                    "first_hit_selection_score": visit.get("selection_score"),
                    "first_hit_candidate_rank_m09": visit.get("candidate_rank_m09"),
                    "first_hit_source_to_candidate_path_cost_m": (
                        visit.get("source_to_candidate_path_cost_m")
                        if visit
                        else hit.get("source_to_candidate_path_cost_m")
                        if hit
                        else None
                    ),
                    "first_hit_candidate_to_nearest_eval_viewpoint_xz_m": (
                        hit.get("candidate_to_nearest_eval_viewpoint_xz_m") if hit else None
                    ),
                    "min_candidate_to_nearest_eval_viewpoint_xz_m": min_finite(
                        [row.get("candidate_to_nearest_eval_viewpoint_xz_m") for row in rows]
                    ),
                    "uses_eval_for_policy": any(
                        bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) for row in rows
                    ),
                    "diagnostic_eval_fields_used_for_hit_label": True,
                    "policy_input_allowed": all(bool(row.get("policy_input_allowed", True)) for row in rows),
                }
            )
    return out


def build_source_gap_case_rows(
    m55_episode_rows: list[dict[str, Any]],
    full_pool_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in full_pool_rows:
        by_episode[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for row in m55_episode_rows:
        episode_id = str(row.get("adapter_episode_id"))
        full_rows = by_episode.get(episode_id, [])
        primary = next((r for r in full_rows if r["policy_id"] == FULL_POOL_PRIMARY_POLICY), {})
        reachable = next((r for r in full_rows if r["policy_id"] == REACHABLE_POLICY), {})
        any_full_hit = any(int_or_none(r.get("first_hit_rank")) is not None for r in full_rows)
        all_hits_outside_budget = all(
            int_or_none(r.get("first_hit_rank")) is None or int_or_none(r.get("first_hit_rank")) > PRIMARY_BUDGET
            for r in full_rows
        )
        m55_top5_hit = bool(row.get("current_top5_variant_has_eval_hit"))
        if m55_top5_hit:
            source_gap_type = "recovered_positive_case_with_deep_detector_hit"
            next_requirement = "use as positive contrast; do not treat as an unrecovered source-gap failure"
        elif any_full_hit and all_hits_outside_budget:
            source_gap_type = "full_pool_hit_budget5_surfacing_failure"
            next_requirement = "audit policy-visible features that can promote deep full-pool candidates into budget-5"
        elif any_full_hit:
            source_gap_type = "full_pool_hit_available_for_budgeted_policy"
            next_requirement = "retain as positive source-gap case and audit why task-agnostic ties H001"
        else:
            source_gap_type = "candidate_absent_even_in_full_pool"
            next_requirement = "new observation rendering or external map/proposal source"
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scene_key": row.get("scene_key"),
                "scan_id": row.get("scan_id"),
                "object_category": row.get("object_category"),
                "task_context_rows": row.get("task_context_rows"),
                "m55_h001_v2_success_contexts": row.get("h001_v2_success_contexts"),
                "m55_task_agnostic_success_contexts": row.get("task_agnostic_success_contexts"),
                "m55_current_top5_variant_has_eval_hit": m55_top5_hit,
                "m55_repair_decision": row.get("repair_decision"),
                "m55_min_executed_top5_nearest_eval_viewpoint_xz_m": row.get(
                    "min_candidate_to_nearest_eval_viewpoint_xz_m"
                ),
                "m19_full_pool_has_hit": any_full_hit,
                "m19_all_full_pool_hits_outside_budget5": all_hits_outside_budget,
                "m19_detector_all_first_hit_rank": primary.get("first_hit_rank"),
                "m19_reachable_first_hit_rank": reachable.get("first_hit_rank"),
                "m19_detector_all_first_hit_confidence": primary.get("first_hit_confidence"),
                "m19_detector_all_first_hit_path_cost_m": primary.get(
                    "first_hit_source_to_candidate_path_cost_m"
                ),
                "source_gap_type": source_gap_type,
                "next_requirement": next_requirement,
                "policy_leakage_boundary": (
                    "M19 hit labels are diagnostic metric evidence; M57 policy inputs may use only "
                    "candidate label, confidence, frame/source, path/navmesh, source diversity, task context, "
                    "and stale-memory fields."
                ),
            }
        )
    return out


def build_candidate_source_route_rows(source_gap_case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    full_pool_hit_all = all(bool(row.get("m19_full_pool_has_hit")) for row in source_gap_case_rows)
    outside_budget_all = all(bool(row.get("m19_all_full_pool_hits_outside_budget5")) for row in source_gap_case_rows)
    return [
        {
            "version": VERSION,
            "route_id": "rerank_executed_top5_variants_v0",
            "selected": False,
            "next_unit": None,
            "reason": "M55 shows remaining failed contexts have no successful candidate in executed top-5 variants.",
        },
        {
            "version": VERSION,
            "route_id": "increase_visit_budget_to_full_pool_v0",
            "selected": False,
            "next_unit": None,
            "reason": "Full-pool visits can diagnose source-gap reachability but would weaken the budgeted policy contribution.",
        },
        {
            "version": VERSION,
            "route_id": "eval_label_guided_oracle_promotion_v0",
            "selected": False,
            "next_unit": None,
            "reason": "Eval hit labels, goal positions, and viewpoint distances are metric-only and must not define policy order.",
        },
        {
            "version": VERSION,
            "route_id": "non_oracle_full_pool_source_promoter_v0",
            "selected": bool(full_pool_hit_all and outside_budget_all),
            "next_unit": NEXT_UNIT,
            "reason": (
                "M19 full pool has source-gap hits for all episodes but ranks them outside budget-5; "
                "M57 should audit policy-visible features for a budgeted promoter."
            ),
        },
        {
            "version": VERSION,
            "route_id": "new_rendered_observation_expansion_v0",
            "selected": False,
            "next_unit": None,
            "reason": "Defer new rendering because the existing non-oracle expanded pool already contains source-gap hits.",
        },
        {
            "version": VERSION,
            "route_id": "external_map_or_proposal_source_v0",
            "selected": False,
            "next_unit": None,
            "reason": "External map/proposal sources remain important for top-tier breadth but should follow the full-pool feature audit.",
        },
        {
            "version": VERSION,
            "route_id": "human_intent_upgrade_now_v0",
            "selected": False,
            "next_unit": None,
            "reason": "Task context still ties task-agnostic source-diverse and should stay secondary.",
        },
    ]


def build_allowed_input_contract_rows() -> list[dict[str, Any]]:
    fields = [
        ("query", ["adapter_episode_id", "scene_key", "scan_id", "object_category", "task_context_id"]),
        (
            "detector_candidate",
            [
                "proposal_uid",
                "raw_candidate_uid",
                "label_canonical",
                "confidence",
                "selection_score",
                "candidate_rank_m09",
                "frame_id",
                "candidate_scope",
            ],
        ),
        (
            "geometry_and_navigation",
            [
                "candidate_position_m",
                "snapped_position_m",
                "snap_distance_m",
                "navmesh_validation_status",
                "path_ready",
                "source_to_candidate_path_cost_m",
                "source_to_snapped_geodesic_m",
                "centroid_source_euclidean_m",
            ],
        ),
        (
            "source_diversity",
            [
                "frame_id",
                "source_position",
                "yaw_offset_deg",
                "scene_key",
                "label_canonical",
                "source_diversity_key",
            ],
        ),
        (
            "memory_and_task",
            [
                "stale_old_memory_candidate",
                "old_location_dead_end_cost_proxy_m",
                "task_context_id",
                "task_value_bucket",
                "candidate_visit_budget",
            ],
        ),
    ]
    rows = []
    for group, names in fields:
        rows.append(
            {
                "version": VERSION,
                "input_group": group,
                "allowed": True,
                "fields": names,
                "reason": "Policy-visible before ObjectNav goal/viewpoint evaluation.",
            }
        )
    return rows


def build_blocked_input_rows() -> list[dict[str, Any]]:
    groups = [
        (
            "objectnav_eval_target",
            ["eval_goal_object_id", "eval_goal_position", "eval_viewpoints", "eval_all_viewpoint_positions"],
        ),
        (
            "metric_distances",
            [
                "candidate_to_eval_goal_xz_m",
                "candidate_to_nearest_eval_viewpoint_xz_m",
                "candidate_to_eval_first_viewpoint_xz_m",
            ],
        ),
        (
            "outcome_labels",
            [
                "primary_eval_hit",
                "eval_success",
                "trajectory_success",
                "SR",
                "SPL",
                "StopRank",
                "FailureType",
                "success_proposal_uid",
            ],
        ),
        (
            "posthoc_feasibility_labels",
            ["m55_repair_decision", "m19_full_pool_has_hit", "source_gap_type"],
        ),
    ]
    return [
        {
            "version": VERSION,
            "input_group": group,
            "allowed": False,
            "fields": fields,
            "reason": "Metric-only or post-hoc diagnosis; cannot be used to rank or generate policy candidates.",
        }
        for group, fields in groups
    ]


def build_policy_design_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "design_id": "m57_full_pool_feature_audit_v0",
            "stage": "next",
            "selected": True,
            "purpose": "Materialize policy-visible full-pool candidate features for source-gap episodes and compare deep-hit candidates against top-5 false positives.",
            "must_not_use": "eval hit labels as ranking features",
            "expected_output": "source-gap candidate feature rows, hit-vs-top5 diagnostic labels, promoter design feasibility gates",
        },
        {
            "version": VERSION,
            "design_id": "budget5_source_promoter_policy_v0",
            "stage": "after_m57_if_supported",
            "selected": False,
            "purpose": "Define a budget-5 policy that promotes full-pool candidates using only detector, geometry, source-diversity, path-cost, stale-memory, and task fields.",
            "must_not_use": "ObjectNav goal/viewpoint positions or hit labels",
            "expected_output": "M58 materialized policy rows if M57 finds non-oracle separation signal",
        },
        {
            "version": VERSION,
            "design_id": "new_observation_or_external_source_v0",
            "stage": "fallback_after_m57",
            "selected": False,
            "purpose": "Use additional non-oracle rendered views or external map/proposal sources if full-pool policy-visible features cannot surface deep hits.",
            "must_not_use": "eval-guided camera placement or eval-label candidate selection",
            "expected_output": "new source route contract and Docker/materialization plan",
        },
    ]


def build_materialization_plan_rows(
    source_gap_case_rows: list[dict[str, Any]],
    full_pool_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_pool_candidate_rows = sum(
        int(row.get("candidate_rows", 0) or 0)
        for row in full_pool_rows
        if row.get("policy_id") == FULL_POOL_PRIMARY_POLICY
    )
    reachable_candidate_rows = sum(
        int(row.get("candidate_rows", 0) or 0)
        for row in full_pool_rows
        if row.get("policy_id") == REACHABLE_POLICY
    )
    return [
        {
            "version": VERSION,
            "unit": NEXT_UNIT,
            "step_order": 1,
            "step_id": "read_inputs",
            "input_paths": [
                str((M18_DIR / "candidate_visit_order_rows.jsonl").relative_to(ROOT)),
                str((M19_DIR / "candidate_goal_eval_rows.jsonl").relative_to(ROOT)),
                str((M55_DIR / "source_gap_episode_rows.jsonl").relative_to(ROOT)),
            ],
            "expected_rows": full_pool_candidate_rows,
            "output": "full_pool_candidate_feature_rows.jsonl",
        },
        {
            "version": VERSION,
            "unit": NEXT_UNIT,
            "step_order": 2,
            "step_id": "source_gap_feature_contrast",
            "input_paths": ["full_pool_candidate_feature_rows.jsonl"],
            "expected_rows": reachable_candidate_rows,
            "output": "source_gap_hit_vs_top5_feature_contrast_rows.jsonl",
        },
        {
            "version": VERSION,
            "unit": NEXT_UNIT,
            "step_order": 3,
            "step_id": "non_oracle_promoter_gate",
            "input_paths": ["source_gap_hit_vs_top5_feature_contrast_rows.jsonl"],
            "expected_rows": len(source_gap_case_rows),
            "output": "source_gap_promoter_feasibility_gate_rows.jsonl",
        },
        {
            "version": VERSION,
            "unit": NEXT_UNIT,
            "step_order": 4,
            "step_id": "next_route_decision",
            "input_paths": ["source_gap_promoter_feasibility_gate_rows.jsonl"],
            "expected_rows": 1,
            "output": "route_decision_rows.jsonl",
        },
    ]


def build_evaluation_gate_rows(
    m55_coverage: dict[str, Any],
    source_gap_case_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_pool_hit_rows = sum(1 for row in source_gap_case_rows if bool(row.get("m19_full_pool_has_hit")))
    outside_budget_rows = sum(
        1 for row in source_gap_case_rows if bool(row.get("m19_all_full_pool_hits_outside_budget5"))
    )
    rows = [
        {
            "gate_id": "m55_ready",
            "passed": m55_coverage.get("status")
            == "e008_m55_source_gap_candidate_generation_repair_feasibility_ready",
            "evidence": f"M55 status={m55_coverage.get('status')}.",
            "implication": "M56 can build on the source-gap feasibility diagnosis.",
        },
        {
            "gate_id": "m19_full_pool_has_source_gap_hit_for_all_episodes",
            "passed": full_pool_hit_rows == len(source_gap_case_rows) and bool(source_gap_case_rows),
            "evidence": f"{full_pool_hit_rows}/{len(source_gap_case_rows)} source-gap episodes have a full-pool hit.",
            "implication": "The immediate blocker is not candidate absence; it is budgeted surfacing.",
        },
        {
            "gate_id": "full_pool_hits_outside_budget5",
            "passed": outside_budget_rows == len(source_gap_case_rows) and bool(source_gap_case_rows),
            "evidence": f"{outside_budget_rows}/{len(source_gap_case_rows)} source-gap episodes place full-pool hits outside budget-5.",
            "implication": "A budgeted source promoter is required before final navigation scale-up.",
        },
        {
            "gate_id": "allowed_input_contract_defined",
            "passed": bool(allowed_rows),
            "evidence": f"{len(allowed_rows)} allowed input groups.",
            "implication": "M57 can audit policy-visible features without changing the leakage boundary.",
        },
        {
            "gate_id": "blocked_eval_input_contract_defined",
            "passed": bool(blocked_rows),
            "evidence": f"{len(blocked_rows)} blocked input groups.",
            "implication": "Eval labels remain metric-only.",
        },
        {
            "gate_id": "budget5_policy_materialized",
            "passed": False,
            "evidence": "M56 is a contract; no new budget-5 policy rows are materialized yet.",
            "implication": "M57/M58 are required before another trajectory execution.",
        },
        {
            "gate_id": "task_context_main_claim_ready",
            "passed": False,
            "evidence": "H001 still ties task-agnostic source-diverse in M55.",
            "implication": "Human intent remains secondary.",
        },
        {
            "gate_id": "final_navigation_claim_ready",
            "passed": False,
            "evidence": "No new `SR` / `SPL` trajectory execution is run in M56.",
            "implication": "M56 does not change final navigation claim status.",
        },
    ]
    return [{"version": VERSION, **row} for row in rows]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_gap_blocker_refined_to_budgeted_surfacing",
            "supported": True,
            "evidence": "M19 full-pool diagnostic has source-gap hits for all three source-gap episodes, but all are outside budget-5.",
            "claim_boundary": "diagnostic contract claim, not final navigation claim",
        },
        {
            "version": VERSION,
            "claim_id": "full_pool_visit_policy_solves_source_gap",
            "supported": False,
            "evidence": "Full-pool hit existence is diagnostic and would require high candidate visits.",
            "required_evidence": "budget-5 policy that surfaces candidates using only allowed non-oracle fields.",
        },
        {
            "version": VERSION,
            "claim_id": "task_conditioned_source_gap_policy",
            "supported": False,
            "evidence": "M55 H001 source-gap `SR` ties task-agnostic source-diverse.",
            "required_evidence": "task-conditioned source selection must beat task-agnostic after source expansion.",
        },
        {
            "version": VERSION,
            "claim_id": "new_observation_or_external_map_required_now",
            "supported": False,
            "evidence": "Existing non-oracle expanded full pool already contains target candidates.",
            "required_evidence": "M57 must first test whether policy-visible full-pool features can surface hits.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "evidence": "M56 runs no trajectory execution and materializes no final policy table.",
            "required_evidence": "budgeted source expansion, Docker trajectory execution, baselines, and heldout-scale validation.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "why_not_new_rendering_immediately",
            "The existing M19 full pool already contains source-gap hit candidates for all three source-gap episodes.",
            "Audit policy-visible source features first; new rendering becomes justified only if no non-oracle surfacing signal exists.",
        ),
        (
            "why_not_full_pool_visits",
            "Full-pool hits appear at ranks 12, 19, and 40 under detector-confidence ordering, which violates the budgeted search-policy intent.",
            "Use full-pool visits only as diagnosis, not as the method claim.",
        ),
        (
            "why_no_oracle_promotion",
            "Hit labels come from ObjectNav goal/viewpoint evaluation and are blocked as policy inputs.",
            "M57 may attach hit labels only for post-hoc contrast analysis.",
        ),
        (
            "why_human_intent_still_secondary",
            "M55 shows H001 and task-agnostic source-diverse tie on source-gap rows.",
            "Task context can be reconsidered only after candidate-source expansion creates a setting where task utility changes decisions.",
        ),
        (
            "what_m56_adds",
            "M56 changes the technical blocker from source absence to budgeted source surfacing, which is a more precise failure diagnosis.",
            "This supports the next method-design step but not a final paper contribution by itself.",
        ),
    ]
    return [
        {"version": VERSION, "defense_id": defense_id, "reviewer_attack": attack, "response": response}
        for defense_id, attack, response in rows
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "m57_full_pool_feature_audit_next",
            "selected": True,
            "next_unit": NEXT_UNIT,
            "reason": "Source-gap hits exist in M19 full pool but are outside budget-5; audit policy-visible features before designing a new policy.",
        },
        {
            "version": VERSION,
            "route_id": "m58_budget5_policy_materialization_now",
            "selected": False,
            "next_unit": None,
            "reason": "Do not materialize a new policy until M57 confirms a non-oracle separation signal.",
        },
        {
            "version": VERSION,
            "route_id": "new_rendering_or_external_source_now",
            "selected": False,
            "next_unit": None,
            "reason": "Deferred until full-pool policy-visible feature audit fails or proves insufficient.",
        },
        {
            "version": VERSION,
            "route_id": "navigation_scaleup_now",
            "selected": False,
            "next_unit": None,
            "reason": "Scale-up remains blocked until a budgeted source-gap policy is materialized and executed.",
        },
    ]


def write_report(
    coverage: dict[str, Any],
    source_gap_case_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    selected = next(row for row in route_rows if row.get("selected"))
    lines = [
        "# E008-M56 Source-Gap Candidate-Source Expansion Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Source-gap episodes: {coverage['source_gap_episode_rows']}.",
        f"- M19 full-pool hit episodes: {coverage['m19_full_pool_hit_episode_rows']} / {coverage['source_gap_episode_rows']}.",
        f"- Full-pool hits outside budget-5 episodes: {coverage['full_pool_hit_outside_budget5_episode_rows']} / {coverage['source_gap_episode_rows']}.",
        f"- Selected route: `{selected['route_id']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Interpretation",
        "",
        "- M55 showed executed top-5 variants do not contain successful candidates for the remaining source-gap failures.",
        "- M19 shows the broader non-oracle expanded full pool does contain source-gap hit candidates for all three source-gap episodes.",
        "- Therefore the immediate blocker is budgeted source surfacing, not source absence.",
        "- M57 should audit whether policy-visible features can promote those deep candidates into budget-5 without using eval labels.",
        "",
        "## Source-Gap Cases",
        "",
        "| episode | object | M55 top-5 hit | detector-all first hit rank | reachable first hit rank | selected diagnosis |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in source_gap_case_rows:
        lines.append(
            f"| `{row['adapter_episode_id']}` | `{row['object_category']}` | "
            f"{row['m55_current_top5_variant_has_eval_hit']} | "
            f"{row['m19_detector_all_first_hit_rank']} | "
            f"{row['m19_reachable_first_hit_rank']} | "
            f"`{row['source_gap_type']}` |"
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
            "- M56 supports only a source-gap expansion contract.",
            "- It does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main contribution.",
            "- Full-pool hit labels are diagnostic only; M57 policy design must use only allowed non-oracle fields.",
            "",
            "## Next",
            "",
            f"- {coverage['selected_next_unit']}: materialize source-gap full-pool feature rows and decide whether a non-oracle budget-5 promoter is defensible.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m16_coverage = read_json(M16_DIR / "coverage.json")
    m43_coverage = read_json(M43_DIR / "coverage.json")
    m55_coverage = read_json(M55_DIR / "coverage.json")
    m55_episode_rows = read_jsonl(M55_DIR / "source_gap_episode_rows.jsonl")
    m18_visit_rows = read_jsonl(M18_DIR / "candidate_visit_order_rows.jsonl")
    m19_goal_rows = read_jsonl(M19_DIR / "candidate_goal_eval_rows.jsonl")

    episode_ids = source_gap_episode_ids(m55_episode_rows)
    visit_index = build_visit_index(m18_visit_rows)
    full_pool_hit_rows = build_full_pool_hit_diagnostic_rows(episode_ids, m19_goal_rows, visit_index)
    source_gap_case_rows = build_source_gap_case_rows(m55_episode_rows, full_pool_hit_rows)
    route_option_rows = build_candidate_source_route_rows(source_gap_case_rows)
    allowed_input_rows = build_allowed_input_contract_rows()
    blocked_input_rows = build_blocked_input_rows()
    policy_design_rows = build_policy_design_contract_rows()
    materialization_plan_rows = build_materialization_plan_rows(source_gap_case_rows, full_pool_hit_rows)
    evaluation_gate_rows = build_evaluation_gate_rows(
        m55_coverage, source_gap_case_rows, allowed_input_rows, blocked_input_rows
    )
    claim_boundary_rows = build_claim_boundary_rows()
    reviewer_defense_rows = build_reviewer_defense_rows()
    route_decision_rows = build_route_decision_rows()

    input_ready = bool(m16_coverage and m43_coverage and m55_coverage and m55_episode_rows and m18_visit_rows and m19_goal_rows)
    selected_route = next(row for row in route_decision_rows if row.get("selected"))
    full_pool_hit_episode_rows = sum(1 for row in source_gap_case_rows if bool(row.get("m19_full_pool_has_hit")))
    outside_budget_episode_rows = sum(
        1 for row in source_gap_case_rows if bool(row.get("m19_all_full_pool_hits_outside_budget5"))
    )
    unrecovered_budget_surfacing_episode_rows = sum(
        1 for row in source_gap_case_rows if row.get("source_gap_type") == "full_pool_hit_budget5_surfacing_failure"
    )
    gate_pass_rows = sum(1 for row in evaluation_gate_rows if row.get("passed"))
    status = (
        READY_STATUS
        if input_ready
        and full_pool_hit_episode_rows == len(source_gap_case_rows)
        and selected_route.get("next_unit") == NEXT_UNIT
        else BLOCKED_STATUS
    )

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m16_status": m16_coverage.get("status"),
        "m43_status": m43_coverage.get("status"),
        "m55_status": m55_coverage.get("status"),
        "input_ready": input_ready,
        "primary_budget": PRIMARY_BUDGET,
        "source_gap_episode_rows": len(source_gap_case_rows),
        "full_pool_hit_diagnostic_rows": len(full_pool_hit_rows),
        "m19_full_pool_hit_episode_rows": full_pool_hit_episode_rows,
        "full_pool_hit_outside_budget5_episode_rows": outside_budget_episode_rows,
        "unrecovered_budget_surfacing_episode_rows": unrecovered_budget_surfacing_episode_rows,
        "route_option_rows": len(route_option_rows),
        "allowed_input_rows": len(allowed_input_rows),
        "blocked_input_rows": len(blocked_input_rows),
        "policy_design_contract_rows": len(policy_design_rows),
        "materialization_plan_rows": len(materialization_plan_rows),
        "evaluation_gate_rows": len(evaluation_gate_rows),
        "evaluation_gate_pass_rows": gate_pass_rows,
        "claim_boundary_rows": len(claim_boundary_rows),
        "reviewer_defense_rows": len(reviewer_defense_rows),
        "selected_route": selected_route.get("route_id"),
        "selected_next_unit": selected_route.get("next_unit"),
        "budget5_policy_materialized": False,
        "candidate_source_expansion_contract_ready": status == READY_STATUS,
        "real_navigation_sr_spl_ready": False,
        "human_intent_main_claim_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "artifact_dir": str(ARTIFACT_DIR.relative_to(ROOT)),
        "derived_data_dir": str(DATA_OUT_DIR.relative_to(ROOT)),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_case_rows.jsonl", source_gap_case_rows)
    write_jsonl(ARTIFACT_DIR / "full_pool_hit_diagnostic_rows.jsonl", full_pool_hit_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_source_route_option_rows.jsonl", route_option_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_contract_rows.jsonl", allowed_input_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_input_rows)
    write_jsonl(ARTIFACT_DIR / "policy_design_contract_rows.jsonl", policy_design_rows)
    write_jsonl(ARTIFACT_DIR / "materialization_plan_rows.jsonl", materialization_plan_rows)
    write_jsonl(ARTIFACT_DIR / "evaluation_gate_rows.jsonl", evaluation_gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_defense_rows)
    write_report(coverage, source_gap_case_rows, route_decision_rows, evaluation_gate_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "source_gap_case_rows.jsonl", source_gap_case_rows)
    write_jsonl(DATA_OUT_DIR / "materialization_plan_rows.jsonl", materialization_plan_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_decision_rows)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
