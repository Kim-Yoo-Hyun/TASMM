#!/usr/bin/env python3
"""Interpret M113 ConceptGraphs HM3D goal-evaluation results and decide trajectory promotion."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M111_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M112_DIR = EXP_ROOT / "artifacts" / "E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"
M113_DIR = EXP_ROOT / "artifacts" / "E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0"
)

VERSION = "e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0"
READY_STATUS = "e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_ready"
BLOCKED_STATUS = "e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_blocked"
NEXT_UNIT = "E008-M115 ConceptGraphs HM3D case-level failure audit and repair route contract"

PRIMARY_RADIUS_M = 1.0
NEAR_MISS_RADIUS_M = 1.5
MODERATE_GAP_RADIUS_M = 3.0


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
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def min_finite(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [finite_float(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return min(values) if values else None


def max_int(rows: list[dict[str, Any]], key: str) -> int:
    values: list[int] = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        try:
            values.append(int(value))
        except (TypeError, ValueError):
            continue
    return max(values) if values else 0


def min_int(rows: list[dict[str, Any]], key: str) -> int | None:
    values: list[int] = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        try:
            values.append(int(value))
        except (TypeError, ValueError):
            continue
    return min(values) if values else None


def classify_goal_failure(best_any_vp_xz_m: float | None, best_goal_xz_m: float | None) -> str:
    if best_any_vp_xz_m is None:
        return "unknown_no_goal_distance"
    if best_any_vp_xz_m <= PRIMARY_RADIUS_M:
        return "covered_under_primary_radius"
    if best_any_vp_xz_m <= NEAR_MISS_RADIUS_M:
        return "near_miss_any_viewpoint_threshold_gap"
    if best_goal_xz_m is not None and best_goal_xz_m <= NEAR_MISS_RADIUS_M:
        return "stop_region_viewpoint_alignment_gap"
    if best_any_vp_xz_m <= MODERATE_GAP_RADIUS_M:
        return "moderate_candidate_localization_gap"
    return "severe_candidate_source_coverage_gap"


def recommended_next_action(failure_class: str) -> str:
    if failure_class == "severe_candidate_source_coverage_gap":
        return "audit_target_visibility_and_alternative_candidate_source_before_more_runtime"
    if failure_class == "stop_region_viewpoint_alignment_gap":
        return "audit_stop_region_viewpoint_alignment_and_candidate_snap_before_trajectory"
    if failure_class == "moderate_candidate_localization_gap":
        return "audit_candidate_localization_threshold_and_same_category_instance_confusion"
    if failure_class == "near_miss_any_viewpoint_threshold_gap":
        return "audit_metric_threshold_sensitivity_without_changing_primary_claim"
    if failure_class == "covered_under_primary_radius":
        return "debug_metric_join_before_policy_change"
    return "inspect_missing_goal_distance_rows"


def group_by_query(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        query_uid = str(row.get("query_uid") or f"{row.get('scan_id')}::{row.get('object_category')}")
        grouped[query_uid].append(row)
    return grouped


def build_case_interpretation_rows(
    source_rows: list[dict[str, Any]],
    path_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    path_by_query = group_by_query(path_rows)
    goal_by_query = group_by_query(goal_rows)
    source_by_query = {str(row.get("query_uid")): row for row in source_rows}
    query_uids = sorted(set(source_by_query) | set(path_by_query) | set(goal_by_query))

    out: list[dict[str, Any]] = []
    for query_uid in query_uids:
        source = source_by_query.get(query_uid, {})
        query_path_rows = path_by_query.get(query_uid, [])
        query_goal_rows = goal_by_query.get(query_uid, [])
        sample = query_goal_rows[0] if query_goal_rows else (query_path_rows[0] if query_path_rows else source)
        best_any = min_finite(query_goal_rows, "best_any_viewpoint_xz_m")
        best_goal = min_finite(query_goal_rows, "best_goal_xz_m")
        failure_class = classify_goal_failure(best_any, best_goal)
        primary_success_policy_count = sum(1 for row in query_goal_rows if bool(row.get("primary_hit")))
        any_vp_1p5_success_policy_count = sum(
            1 for row in query_goal_rows if bool(row.get("any_viewpoint_xz_1p5_hit"))
        )
        goal_1p5_success_policy_count = sum(1 for row in query_goal_rows if bool(row.get("goal_xz_1p5_hit")))
        first_path_cost = min_finite(query_path_rows, "first_path_ready_cost_m")
        out.append(
            {
                "version": VERSION,
                "row_type": "conceptgraphs_case_interpretation",
                "query_uid": query_uid,
                "adapter_episode_id": sample.get("adapter_episode_id"),
                "scan_id": sample.get("scan_id"),
                "scene_key": sample.get("scene_key"),
                "object_category": sample.get("object_category") or sample.get("label_canonical"),
                "m102_branch": sample.get("m102_branch") or source.get("m102_branch"),
                "m111_source_ready": bool(source.get("source_ready", sample.get("source_ready_after_m111"))),
                "m111_candidate_rows": source.get("candidate_rows") or sample.get("candidate_rows"),
                "m111_path_ready_candidate_rows": source.get("path_ready_candidate_rows")
                or sample.get("path_ready_rows"),
                "m112_policy_rows": len(query_path_rows),
                "m112_min_first_path_ready_cost_m": first_path_cost,
                "m112_top5_path_ready_rows_max": max_int(query_path_rows, "top5_path_ready_rows"),
                "m113_policy_rows": len(query_goal_rows),
                "m113_primary_success_policy_count": primary_success_policy_count,
                "m113_any_viewpoint_xz_1p5_success_policy_count": any_vp_1p5_success_policy_count,
                "m113_goal_xz_1p5_success_policy_count": goal_1p5_success_policy_count,
                "m113_best_any_viewpoint_xz_m_min": best_any,
                "m113_best_goal_xz_m_min": best_goal,
                "m113_best_any_viewpoint_rank_min": min_int(query_goal_rows, "best_any_viewpoint_xz_rank"),
                "goal_failure_class": failure_class,
                "source_gap_recovery_supported": primary_success_policy_count > 0,
                "direct_trajectory_promotion_ready": False,
                "recommended_next_action": recommended_next_action(failure_class),
                "interpretation": (
                    "ConceptGraphs produced path-ready source candidates, but the frozen candidate order "
                    "does not put a candidate inside the primary ObjectNav target-near radius."
                ),
                "claim_boundary": "M114 interprets M113 proxy goal-evaluation rows only; it does not execute Habitat trajectories.",
            }
        )
    return out


def build_policy_interpretation_rows(
    path_policy_rows: list[dict[str, Any]],
    goal_policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    path_by_policy = {str(row.get("policy_id")): row for row in path_policy_rows}
    rows: list[dict[str, Any]] = []
    for goal in sorted(goal_policy_rows, key=lambda row: str(row.get("policy_id"))):
        policy_id = str(goal.get("policy_id"))
        path = path_by_policy.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_interpretation",
                "policy_id": policy_id,
                "m112_mean_first_path_ready_cost_m": path.get("mean_first_path_ready_cost_m"),
                "m112_top1_path_ready_query_rows": path.get("top1_path_ready_query_rows"),
                "m113_scan_policy_rows": goal.get("scan_policy_rows"),
                "m113_primary_success_rows": goal.get("primary_success_rows"),
                "m113_primary_proxy_sr": goal.get("primary_proxy_sr"),
                "m113_primary_spl_proxy_mean": goal.get("primary_spl_proxy_mean"),
                "m113_any_viewpoint_xz_1p5_proxy_sr": goal.get("any_viewpoint_xz_1p5_proxy_sr"),
                "m113_goal_xz_1p5_proxy_sr": goal.get("goal_xz_1p5_proxy_sr"),
                "m113_best_any_viewpoint_xz_m_mean": goal.get("best_any_viewpoint_xz_m_mean"),
                "m113_best_goal_xz_m_mean": goal.get("best_goal_xz_m_mean"),
                "supports_policy_ranking_claim": False,
                "supports_source_gap_recovery_claim": False,
                "direct_trajectory_promotion_ready": False,
                "interpretation": (
                    "Path-cost or semantic ordering cannot recover source-gap cases when the candidate "
                    "set lacks a primary target-near candidate."
                ),
            }
        )
    return rows


def build_trajectory_decision_rows(case_rows: list[dict[str, Any]], m113_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    any_primary_success = bool(m113_coverage.get("source_gap_proxy_recovery_observed"))
    goal_center_near_cases = sum(
        1 for row in case_rows if int(row.get("m113_goal_xz_1p5_success_policy_count") or 0) > 0
    )
    return [
        {
            "version": VERSION,
            "route_id": "promote_conceptgraphs_hm3d_candidates_to_habitat_trajectory",
            "decision": "reject_now",
            "reason": "M113 has 0/2 primary proxy success for every ConceptGraphs policy, so trajectory execution would not test a recovered source-gap policy.",
            "source_gap_proxy_recovery_observed": any_primary_success,
            "direct_trajectory_promotion_ready": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        {
            "version": VERSION,
            "route_id": "run_relaxed_goal_center_trajectory_probe",
            "decision": "defer_until_case_audit",
            "reason": "One case has a goal-center 1.5m diagnostic hit, but it still misses the eval-viewpoint primary metric; this needs stop-region/viewpoint alignment audit before trajectory execution.",
            "goal_center_near_case_rows": goal_center_near_cases,
            "launch_long_job_now": False,
            "expected_paper_value": "diagnostic_only_before_m115",
        },
        {
            "version": VERSION,
            "route_id": "case_level_failure_audit_and_repair_route_contract",
            "decision": "select",
            "reason": "The useful next evidence is to separate severe source coverage failure from stop-region/viewpoint alignment failure and decide whether a new candidate source is justified.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
    ]


def build_repair_route_decision_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failure_counts = Counter(str(row.get("goal_failure_class")) for row in case_rows)
    severe_cases = failure_counts.get("severe_candidate_source_coverage_gap", 0)
    stop_region_cases = failure_counts.get("stop_region_viewpoint_alignment_gap", 0)
    return [
        {
            "version": VERSION,
            "route_id": "more_conceptgraphs_path_ranking_only",
            "decision": "reject_now",
            "reason": "M112 already shows path-cost ranking can reduce first-ready path cost, but M113 shows the candidates are not target-near under the primary metric.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "repeat_conceptgraphs_runtime_without_new_source_principle",
            "decision": "reject_now",
            "reason": "M107/M108 runtime outputs are complete; repeating the same route does not address the observed target-near miss.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "stop_region_viewpoint_alignment_audit",
            "decision": "select_case_subroute" if stop_region_cases else "not_applicable",
            "case_rows": stop_region_cases,
            "reason": "The toilet case is close to the goal center under a relaxed diagnostic but misses ObjectNav viewpoint success; audit metric semantics before a trajectory probe.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "alternative_candidate_source_or_visibility_audit",
            "decision": "select_case_subroute" if severe_cases else "not_applicable",
            "case_rows": severe_cases,
            "reason": "The sofa case remains far from target viewpoints, so a stronger candidate source or visibility audit is more justified than trajectory execution.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "m115_case_level_failure_audit_and_repair_contract",
            "decision": "select",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M115 should compactly decide whether the next experimental route is stop-region alignment, broader observation/source expansion, or an external map-navigation baseline.",
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failure_counts = Counter(str(row.get("goal_failure_class")) for row in case_rows)
    return [
        {
            "version": VERSION,
            "claim_id": "supported_negative_conceptgraphs_goal_eval_gate",
            "supported": True,
            "claim_boundary": "M114 supports a negative gate: ConceptGraphs HM3D candidates can be path-ready while still failing primary target-near goal evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_case_level_failure_split_diagnostic",
            "supported": True,
            "claim_boundary": f"M114 diagnoses two source-gap cases as {dict(sorted(failure_counts.items()))}; this is a diagnostic split, not a general failure taxonomy claim.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M113 primary proxy success is 0/2 for every ConceptGraphs policy, so M114 cannot claim source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M114 rejects trajectory promotion and produces no new Habitat SR/SPL result.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "The evidence remains a two-case source-gap diagnostic with generic ConceptGraphs source class names and no external navigation/search baseline.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M114 is a navigation/source-gap diagnostic and does not execute E006 utility or transfer gates.",
        },
    ]


def build_route_decision_rows(input_ready: bool) -> list[dict[str, Any]]:
    if not input_ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m114_inputs_or_interpretation",
                "selected_next_unit": "repair E008-M114 ConceptGraphs result interpretation inputs",
                "reason": "M111/M112/M113 inputs are incomplete or not ready.",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "conceptgraphs_goal_result_interpreted_trajectory_promotion_rejected",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M113 has no primary source-gap proxy recovery; M114 selects case-level failure audit and repair contract instead of trajectory execution.",
            "direct_trajectory_promotion_ready": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| {scan_id} | {object_category} | {m102_branch} | {m111_path_ready_candidate_rows}/{m111_candidate_rows} | "
        "{m113_primary_success_policy_count}/{m113_policy_rows} | {m113_goal_xz_1p5_success_policy_count}/{m113_policy_rows} | "
        "{m113_best_any_viewpoint_xz_m_min} | {m113_best_goal_xz_m_min} | {goal_failure_class} | {recommended_next_action} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m102_branch=row.get("m102_branch"),
            m111_path_ready_candidate_rows=row.get("m111_path_ready_candidate_rows"),
            m111_candidate_rows=row.get("m111_candidate_rows"),
            m113_primary_success_policy_count=row.get("m113_primary_success_policy_count"),
            m113_policy_rows=row.get("m113_policy_rows"),
            m113_goal_xz_1p5_success_policy_count=row.get("m113_goal_xz_1p5_success_policy_count"),
            m113_best_any_viewpoint_xz_m_min=fmt(row.get("m113_best_any_viewpoint_xz_m_min")),
            m113_best_goal_xz_m_min=fmt(row.get("m113_best_goal_xz_m_min")),
            goal_failure_class=row.get("goal_failure_class"),
            recommended_next_action=row.get("recommended_next_action"),
        )
        for row in case_rows
    ]
    policy_lines = [
        "| {policy_id} | {m112_mean_first_path_ready_cost_m} | {m113_primary_success_rows}/{m113_scan_policy_rows} | "
        "{m113_primary_proxy_sr} | {m113_goal_xz_1p5_proxy_sr} | {m113_best_any_viewpoint_xz_m_mean} |".format(
            policy_id=row.get("policy_id"),
            m112_mean_first_path_ready_cost_m=fmt(row.get("m112_mean_first_path_ready_cost_m")),
            m113_primary_success_rows=row.get("m113_primary_success_rows"),
            m113_scan_policy_rows=row.get("m113_scan_policy_rows"),
            m113_primary_proxy_sr=fmt(row.get("m113_primary_proxy_sr")),
            m113_goal_xz_1p5_proxy_sr=fmt(row.get("m113_goal_xz_1p5_proxy_sr")),
            m113_best_any_viewpoint_xz_m_mean=fmt(row.get("m113_best_any_viewpoint_xz_m_mean")),
        )
        for row in policy_rows
    ]
    repair_lines = [
        "| {route_id} | {decision} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            reason=row.get("reason"),
        )
        for row in repair_rows
    ]
    selected_route = next((row for row in trajectory_rows if row.get("decision") == "select"), {})
    return f"""# E008-M114 ConceptGraphs HM3D Goal Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M111 status: `{coverage['m111_status']}`.
- Input M112 status: `{coverage['m112_status']}`.
- Input M113 status: `{coverage['m113_status']}`.
- Query rows: {coverage['query_rows']}.
- M111 candidate rows: {coverage['m111_candidate_rows']}; path-ready candidates: {coverage['m111_path_ready_candidate_rows']}.
- M112 visit-order rows: {coverage['m112_visit_order_rows']}.
- M113 candidate-goal eval rows: {coverage['m113_candidate_goal_eval_rows']}.
- M113 primary success count max: {coverage['m113_primary_success_count_max']}.
- Mean best any-viewpoint XZ distance: {fmt(coverage['m113_best_any_viewpoint_xz_m_mean'])}m.
- Goal-center 1.5m diagnostic case rows: {coverage['goal_center_1p5_diagnostic_case_rows']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Interpretation

| scan_id | category | prior branch | path-ready | primary hits | goal 1.5m diagnostic | best any-vp XZ m | best goal XZ m | failure class | next action |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(case_lines)}

## Policy Interpretation

| policy_id | M112 mean first path cost m | primary hits | proxy SR | goal 1.5m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(policy_lines)}

## Repair Route Decision

| route | decision | reason |
| --- | --- | --- |
{chr(10).join(repair_lines)}

## Decision

- Trajectory promotion is rejected because M113 has 0 / 2 primary proxy success for every `ConceptGraphs` policy.
- The useful next unit is `{selected_route.get('selected_next_unit')}`.
- M114 selects a case-level failure audit before any additional long-running render, mapping, or trajectory job.

## Claim Boundary

- M114 supports a negative diagnostic gate: path-ready `ConceptGraphs` candidates are not sufficient for source-gap recovery.
- M114 does not claim source-gap recovery, real navigation `SR` / `SPL`, deployable search policy, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m111_coverage = read_json(M111_DIR / "coverage.json")
    m112_coverage = read_json(M112_DIR / "coverage.json")
    m113_coverage = read_json(M113_DIR / "coverage.json")
    source_rows = read_jsonl(M111_DIR / "query_source_boundary_rows.jsonl")
    path_query_rows = read_jsonl(M112_DIR / "query_policy_metric_rows.jsonl")
    path_policy_rows = [
        row for row in read_jsonl(M112_DIR / "policy_metric_rows.jsonl") if row.get("metric_scope") == "policy_aggregate"
    ]
    goal_query_rows = read_jsonl(M113_DIR / "conceptgraphs_query_goal_metric_rows.jsonl")
    goal_policy_rows = [
        row for row in read_jsonl(M113_DIR / "policy_goal_metric_rows.jsonl") if row.get("metric_scope") == "policy_aggregate"
    ]

    input_ready = (
        m111_coverage.get("status")
        == "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready"
        and m112_coverage.get("status") == "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_ready"
        and m113_coverage.get("status") == "e008_m113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_ready"
        and bool(source_rows)
        and bool(path_query_rows)
        and bool(goal_query_rows)
        and bool(goal_policy_rows)
    )

    case_rows = build_case_interpretation_rows(source_rows, path_query_rows, goal_query_rows)
    policy_rows = build_policy_interpretation_rows(path_policy_rows, goal_policy_rows)
    trajectory_rows = build_trajectory_decision_rows(case_rows, m113_coverage)
    repair_rows = build_repair_route_decision_rows(case_rows)
    claim_rows = build_claim_boundary_rows(case_rows)
    route_rows = build_route_decision_rows(input_ready)
    failure_counts = Counter(str(row.get("goal_failure_class")) for row in case_rows)
    goal_center_1p5_cases = sum(
        1 for row in case_rows if int(row.get("m113_goal_xz_1p5_success_policy_count") or 0) > 0
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m111_status": m111_coverage.get("status"),
        "m112_status": m112_coverage.get("status"),
        "m113_status": m113_coverage.get("status"),
        "query_rows": m113_coverage.get("query_rows"),
        "m111_candidate_rows": m111_coverage.get("candidate_rows"),
        "m111_path_ready_candidate_rows": m111_coverage.get("source_to_snapped_path_found_rows"),
        "m112_visit_order_rows": m112_coverage.get("visit_order_rows"),
        "m113_candidate_goal_eval_rows": m113_coverage.get("candidate_goal_eval_rows"),
        "m113_primary_success_count_max": m113_coverage.get("primary_success_count_max"),
        "m113_best_any_viewpoint_xz_m_mean": min_finite(policy_rows, "m113_best_any_viewpoint_xz_m_mean"),
        "goal_center_1p5_diagnostic_case_rows": goal_center_1p5_cases,
        "goal_failure_class_counts": dict(sorted(failure_counts.items())),
        "source_gap_proxy_recovery_observed": bool(m113_coverage.get("source_gap_proxy_recovery_observed")),
        "direct_trajectory_promotion_ready": False,
        "additional_long_job_recommended_now": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "conceptgraphs_case_interpretation_rows.jsonl": case_rows,
        "policy_interpretation_rows.jsonl": policy_rows,
        "trajectory_decision_rows.jsonl": trajectory_rows,
        "repair_route_decision_rows.jsonl": repair_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)

    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, policy_rows, repair_rows, trajectory_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
