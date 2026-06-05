#!/usr/bin/env python3
"""Fix the M115 case-level failure audit and repair route contract for ConceptGraphs HM3D."""

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
M103_DIR = EXP_ROOT / "artifacts" / "E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
M110_DIR = EXP_ROOT / "artifacts" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
M111_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M112_DIR = EXP_ROOT / "artifacts" / "E008-M112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_v0"
M113_DIR = EXP_ROOT / "artifacts" / "E008-M113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_v0"
M114_DIR = EXP_ROOT / "artifacts" / "E008-M114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_v0"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0"
)

VERSION = "e008_m115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_v0"
READY_STATUS = "e008_m115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_ready"
BLOCKED_STATUS = "e008_m115_conceptgraphs_hm3d_case_level_failure_audit_repair_route_contract_blocked"
NEXT_UNIT = "E008-M116 ConceptGraphs HM3D stop-region/source-coverage audit materialization contract"

PRIMARY_ANY_VIEWPOINT_XZ_M = 1.0
DIAGNOSTIC_GOAL_CENTER_XZ_M = 1.5


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


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get(key))].append(row)
    return out


def proposal_best_rows(goal_eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate candidate-goal rows across policies by proposal id."""
    by_uid: dict[str, dict[str, Any]] = {}
    for row in goal_eval_rows:
        proposal_uid = str(row.get("proposal_uid"))
        if proposal_uid == "None":
            continue
        current = by_uid.get(proposal_uid)
        current_any = finite_float(current.get("candidate_to_nearest_eval_viewpoint_xz_m")) if current else None
        row_any = finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m"))
        if current is None or (row_any is not None and (current_any is None or row_any < current_any)):
            by_uid[proposal_uid] = row
    return list(by_uid.values())


def min_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    valid = [(finite_float(row.get(key)), row) for row in rows]
    valid = [(value, row) for value, row in valid if value is not None]
    if not valid:
        return None
    return min(valid, key=lambda item: item[0])[1]


def make_candidate_lookup(candidate_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in candidate_rows:
        for key in ("candidate_uid", "candidate_id"):
            uid = row.get(key)
            if uid is not None:
                lookup[str(uid)] = row
    return lookup


def build_case_failure_audit_rows(
    m114_case_rows: list[dict[str, Any]],
    goal_eval_rows: list[dict[str, Any]],
    candidate_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_by_scan = group_by(goal_eval_rows, "scan_id")
    out: list[dict[str, Any]] = []
    for case in sorted(m114_case_rows, key=lambda row: str(row.get("scan_id"))):
        scan_id = str(case.get("scan_id"))
        scan_eval_rows = [row for row in eval_by_scan.get(scan_id, []) if bool(row.get("path_ready"))]
        dedup_rows = proposal_best_rows(scan_eval_rows)
        best_any = min_by(dedup_rows, "candidate_to_nearest_eval_viewpoint_xz_m")
        best_goal = min_by(dedup_rows, "candidate_to_eval_goal_xz_m")
        best_any_uid = str(best_any.get("proposal_uid")) if best_any else None
        best_goal_uid = str(best_goal.get("proposal_uid")) if best_goal else None
        best_any_candidate = candidate_lookup.get(best_any_uid or "", {})
        best_goal_candidate = candidate_lookup.get(best_goal_uid or "", {})
        failure_class = str(case.get("goal_failure_class"))
        if failure_class == "severe_candidate_source_coverage_gap":
            repair_family = "alternative_candidate_source_or_visibility_audit"
            repair_priority = 1
            repair_principle = (
                "The current ConceptGraphs candidate source did not create any target-near candidate; "
                "repair must change target visibility/source coverage or use a stronger candidate source."
            )
            next_materialization = "source_coverage_audit_rows"
            pass_condition = (
                "At least one non-oracle source route or visibility audit explains whether the target region "
                "was observed and why no target-near map candidate was produced."
            )
        elif failure_class == "stop_region_viewpoint_alignment_gap":
            repair_family = "stop_region_viewpoint_alignment_audit"
            repair_priority = 2
            repair_principle = (
                "The route has a goal-center diagnostic candidate but misses ObjectNav stop-region viewpoints; "
                "repair must audit object-center-to-stop-region conversion before trajectory execution."
            )
            next_materialization = "stop_region_alignment_audit_rows"
            pass_condition = (
                "A non-oracle candidate-to-stop-region rule is specified and shown not to use ObjectNav target "
                "viewpoints or success distances as policy inputs."
            )
        else:
            repair_family = "manual_failure_inspection"
            repair_priority = 99
            repair_principle = "Failure class is unknown; inspect rows before selecting a repair route."
            next_materialization = "manual_inspection_rows"
            pass_condition = "Failure class is resolved without changing policy inputs."
        out.append(
            {
                "version": VERSION,
                "row_type": "case_failure_audit",
                "query_uid": case.get("query_uid"),
                "adapter_episode_id": case.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": case.get("scene_key"),
                "object_category": case.get("object_category"),
                "m102_branch": case.get("m102_branch"),
                "m114_failure_class": failure_class,
                "m111_candidate_rows": case.get("m111_candidate_rows"),
                "m111_path_ready_candidate_rows": case.get("m111_path_ready_candidate_rows"),
                "m113_primary_success_policy_count": case.get("m113_primary_success_policy_count"),
                "m113_best_any_viewpoint_xz_m": case.get("m113_best_any_viewpoint_xz_m_min"),
                "m113_best_goal_xz_m": case.get("m113_best_goal_xz_m_min"),
                "best_any_viewpoint_candidate_uid": best_any_uid,
                "best_any_viewpoint_candidate_rank": best_any.get("visit_rank") if best_any else None,
                "best_any_viewpoint_candidate_to_any_viewpoint_xz_m": best_any.get(
                    "candidate_to_nearest_eval_viewpoint_xz_m"
                )
                if best_any
                else None,
                "best_any_viewpoint_candidate_to_goal_xz_m": best_any.get("candidate_to_eval_goal_xz_m")
                if best_any
                else None,
                "best_any_viewpoint_candidate_path_cost_m": best_any.get("source_to_candidate_path_cost_m")
                if best_any
                else None,
                "best_any_viewpoint_candidate_center_xyz": best_any_candidate.get("candidate_center_xyz"),
                "best_any_viewpoint_candidate_source_class_names": best_any_candidate.get("source_class_names"),
                "best_goal_candidate_uid": best_goal_uid,
                "best_goal_candidate_rank": best_goal.get("visit_rank") if best_goal else None,
                "best_goal_candidate_to_goal_xz_m": best_goal.get("candidate_to_eval_goal_xz_m")
                if best_goal
                else None,
                "best_goal_candidate_to_any_viewpoint_xz_m": best_goal.get("candidate_to_nearest_eval_viewpoint_xz_m")
                if best_goal
                else None,
                "best_goal_candidate_path_cost_m": best_goal.get("source_to_candidate_path_cost_m")
                if best_goal
                else None,
                "best_goal_candidate_center_xyz": best_goal_candidate.get("candidate_center_xyz"),
                "best_goal_candidate_source_class_names": best_goal_candidate.get("source_class_names"),
                "goal_center_diagnostic_hit": bool(
                    finite_float(case.get("m113_best_goal_xz_m_min")) is not None
                    and float(case.get("m113_best_goal_xz_m_min")) <= DIAGNOSTIC_GOAL_CENTER_XZ_M
                ),
                "primary_target_near_hit": bool(
                    finite_float(case.get("m113_best_any_viewpoint_xz_m_min")) is not None
                    and float(case.get("m113_best_any_viewpoint_xz_m_min")) <= PRIMARY_ANY_VIEWPOINT_XZ_M
                ),
                "selected_repair_family": repair_family,
                "repair_priority": repair_priority,
                "repair_principle": repair_principle,
                "next_materialization": next_materialization,
                "m116_pass_condition": pass_condition,
                "trajectory_promotion_ready": False,
                "launch_long_job_now": False,
                "claim_boundary": "M115 diagnoses route-specific failures; it does not use eval target fields for policy ordering.",
            }
        )
    return out


def build_repair_route_contract_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_counts = Counter(str(row.get("selected_repair_family")) for row in case_rows)
    return [
        {
            "version": VERSION,
            "route_id": "direct_trajectory_execution_after_m113",
            "decision": "reject_now",
            "case_rows": len(case_rows),
            "reason": "M113/M114 have 0/2 primary source-gap recovery, so a trajectory run would not test a recovered policy.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "more_conceptgraphs_path_ranking_only",
            "decision": "reject_now",
            "case_rows": len(case_rows),
            "reason": "M112 already reduced first-ready path cost, but M113 shows target-near candidates are absent under the primary metric.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "repeat_same_conceptgraphs_runtime",
            "decision": "reject_now",
            "case_rows": len(case_rows),
            "reason": "M107/M108 runtime outputs are complete; repeating the same source route does not change the failure mechanism.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "relaxed_goal_center_trajectory_probe",
            "decision": "defer_until_stop_region_audit",
            "case_rows": family_counts.get("stop_region_viewpoint_alignment_audit", 0),
            "reason": "The toilet case has a goal-center diagnostic hit, but it fails ObjectNav viewpoint success; audit stop-region conversion before trajectory.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "stop_region_viewpoint_alignment_audit",
            "decision": "select_case_subroute",
            "case_rows": family_counts.get("stop_region_viewpoint_alignment_audit", 0),
            "reason": "Needed for goal-center-near but viewpoint-failed cases; this is a metric/stop-region interface audit, not a source-coverage repair.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "alternative_candidate_source_or_visibility_audit",
            "decision": "select_case_subroute",
            "case_rows": family_counts.get("alternative_candidate_source_or_visibility_audit", 0),
            "reason": "Needed for severe source coverage failures where current ConceptGraphs candidates remain far from every target viewpoint.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "openmask3d_or_hovsg_external_route",
            "decision": "defer_until_m116_audit",
            "case_rows": family_counts.get("alternative_candidate_source_or_visibility_audit", 0),
            "reason": "External source routes are plausible for severe coverage gaps, but M116 should first record whether the observed target region was absent, occluded, or misrepresented.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "m116_stop_region_source_coverage_audit_materialization",
            "decision": "select",
            "case_rows": len(case_rows),
            "reason": "M116 should materialize compact audit rows for both failure families before any additional long-running source or trajectory job.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
    ]


def build_route_selection_rows(input_ready: bool, case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not input_ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m115_inputs",
                "selected_next_unit": "repair E008-M115 input lineage",
                "reason": "One or more required M103/M110/M111/M112/M113/M114 inputs are missing or not ready.",
                "launch_long_job_now": False,
            }
        ]
    severe_cases = sum(
        1 for row in case_rows if row.get("selected_repair_family") == "alternative_candidate_source_or_visibility_audit"
    )
    stop_region_cases = sum(
        1 for row in case_rows if row.get("selected_repair_family") == "stop_region_viewpoint_alignment_audit"
    )
    return [
        {
            "version": VERSION,
            "decision": "m115_ready_select_m116_case_audit_materialization",
            "selected_next_unit": NEXT_UNIT,
            "reason": (
                "The next evidence should materialize leakage-safe audit rows for the two distinct failure "
                "families before any additional mapping/runtime/trajectory job."
            ),
            "severe_source_coverage_case_rows": severe_cases,
            "stop_region_alignment_case_rows": stop_region_cases,
            "source_gap_recovery_supported": False,
            "direct_trajectory_promotion_ready": False,
            "launch_long_job_now": False,
        }
    ]


def build_allowed_input_rows() -> list[dict[str, Any]]:
    allowed = [
        ("M110 candidate geometry", "candidate centers, extents, source frames, CLIP/text scores, and generic source class names"),
        ("M111 navmesh/source readiness", "snap/path readiness and source-to-candidate path costs"),
        ("M112 frozen visit order", "candidate ordering after policy inputs are fixed"),
        ("M113 eval distances", "diagnosis and metric auditing only after policy order is frozen"),
        ("M114 failure class", "route selection for audit design only, not candidate ordering"),
    ]
    blocked = [
        ("ObjectNav target viewpoint coordinates", "blocked for candidate generation, policy ordering, or trajectory target selection"),
        ("ObjectNav eval goal position", "blocked for candidate generation or policy ordering; metric-only after frozen policy"),
        ("target object id", "blocked for source generation, map filtering, or candidate selection"),
        ("distance-to-target fields", "blocked before frozen policy; allowed only for post-hoc diagnosis rows"),
        ("success/failure labels", "blocked for policy scoring or candidate filtering"),
    ]
    rows = [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "rule": rule,
            "policy_use_allowed": field not in {"M113 eval distances", "M114 failure class"},
            "audit_use_allowed": True,
        }
        for field, rule in allowed
    ]
    rows.extend(
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "rule": rule,
            "policy_use_allowed": False,
            "audit_use_allowed": "post_hoc_metric_only" if "distance" in field or "goal" in field else False,
        }
        for field, rule in blocked
    )
    return rows


def build_m116_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M116 materializes both `stop_region_alignment_audit_rows` and `source_coverage_audit_rows` with blocked-input audit passing.",
            "next_action": "Decide between a stop-region candidate transform smoke, broader observation/source expansion, or external map-navigation baseline preflight.",
            "claim_status_after_gate": "audit-ready only; no source-gap recovery or navigation claim",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M116 can audit only one failure family or cannot separate source absence from stop-region alignment cleanly.",
            "next_action": "Keep M115 as boundary evidence and select the lower-risk E006-M06 or external-baseline contract next.",
            "claim_status_after_gate": "partial failure taxonomy only",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M116 requires eval target fields for policy/source decisions or cannot reproduce M113/M114 case rows.",
            "next_action": "Do not launch more `ConceptGraphs`, render, or trajectory jobs; repair artifact lineage first.",
            "claim_status_after_gate": "blocked",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_case_specific_failure_split",
            "supported": True,
            "claim_boundary": "M115 supports a case-specific split between severe source coverage failure and stop-region/viewpoint alignment failure for two ConceptGraphs HM3D source-gap cases.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_repair_route_contract",
            "supported": True,
            "claim_boundary": "M115 supports selecting M116 audit materialization before any additional long-running mapping, rendering, or trajectory job.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M115 does not create new candidates or recover any M113 primary source-gap case.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M115 rejects direct trajectory execution and produces no Habitat SR/SPL result.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M115 is a two-case diagnostic contract, not heldout robustness evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M115 is unrelated to E006 utility/transfer evidence.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not execute trajectories now?",
            "answer": "M113/M114 show 0/2 primary proxy recovery. Trajectories would measure known candidate-source or stop-region failures, not a recovered policy.",
        },
        {
            "version": VERSION,
            "question": "Why not just improve ranking?",
            "answer": "M112 already tests path-aware ordering and lowers first-ready path cost, but M113 still finds no primary target-near candidate.",
        },
        {
            "version": VERSION,
            "question": "Why split sofa and toilet failures?",
            "answer": "The sofa candidate is 5.204041m from the nearest valid target viewpoint, while the toilet candidate is 1.388981m from the goal center but 1.732344m from the nearest valid viewpoint.",
        },
        {
            "version": VERSION,
            "question": "Does this make ConceptGraphs a failed baseline?",
            "answer": "No. It is a two-case source-gap route diagnostic. ConceptGraphs remains useful for 3RScan proxy-search baselines and map-assisted fallback, but this HM3D route needs repair before navigation claims.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| {scan_id} | {object_category} | {m114_failure_class} | {m113_best_any_viewpoint_xz_m} | "
        "{m113_best_goal_xz_m} | {selected_repair_family} | {next_materialization} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m114_failure_class=row.get("m114_failure_class"),
            m113_best_any_viewpoint_xz_m=fmt(row.get("m113_best_any_viewpoint_xz_m")),
            m113_best_goal_xz_m=fmt(row.get("m113_best_goal_xz_m")),
            selected_repair_family=row.get("selected_repair_family"),
            next_materialization=row.get("next_materialization"),
        )
        for row in case_rows
    ]
    route_lines = [
        "| {route_id} | {decision} | {case_rows} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            case_rows=row.get("case_rows"),
            reason=row.get("reason"),
        )
        for row in route_rows
    ]
    gate_lines = [
        "| {gate} | {condition} | {next_action} |".format(
            gate=row.get("gate"),
            condition=row.get("condition"),
            next_action=row.get("next_action"),
        )
        for row in gate_rows
    ]
    return f"""# E008-M115 ConceptGraphs HM3D Case-Level Failure Audit / Repair Route Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M114 status: `{coverage['m114_status']}`.
- Frozen visit-order input M112 status: `{coverage['m112_status']}`.
- Frozen M112 visit-order rows: {coverage['m112_visit_order_rows']}.
- Case rows: {coverage['case_failure_audit_rows']}.
- Failure split: {coverage['failure_class_counts']}.
- Selected repair families: {coverage['selected_repair_family_counts']}.
- Source-gap recovery supported: {coverage['source_gap_recovery_supported']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Launch long job now: {coverage['launch_long_job_now']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Audit

| scan_id | category | M114 failure class | best any-vp XZ m | best goal XZ m | selected repair | next materialization |
| --- | --- | --- | ---: | ---: | --- | --- |
{chr(10).join(case_lines)}

## Route Contract

| route | decision | cases | reason |
| --- | --- | ---: | --- |
{chr(10).join(route_lines)}

## M116 Gate

| gate | condition | next action |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M115 supports route selection and failure taxonomy for two `ConceptGraphs` HM3D source-gap cases only.
- M115 does not support source-gap recovery, trajectory promotion, final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m103_coverage = read_json(M103_DIR / "coverage.json")
    m110_coverage = read_json(M110_DIR / "coverage.json")
    m111_coverage = read_json(M111_DIR / "coverage.json")
    m112_coverage = read_json(M112_DIR / "coverage.json")
    m113_coverage = read_json(M113_DIR / "coverage.json")
    m114_coverage = read_json(M114_DIR / "coverage.json")
    m114_case_rows = read_jsonl(M114_DIR / "conceptgraphs_case_interpretation_rows.jsonl")
    m113_goal_eval_rows = read_jsonl(M113_DIR / "candidate_goal_eval_rows.jsonl")
    m110_candidate_rows = read_jsonl(M110_DIR / "candidate_rows.jsonl")

    input_ready = (
        m103_coverage.get("status") == "e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_ready"
        and m110_coverage.get("status") == "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_ready"
        and m111_coverage.get("status") == "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready"
        and m112_coverage.get("status") == "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke_ready"
        and m113_coverage.get("status") == "e008_m113_conceptgraphs_hm3d_candidate_goal_evaluation_smoke_ready"
        and m114_coverage.get("status") == "e008_m114_conceptgraphs_hm3d_goal_result_interpretation_trajectory_decision_ready"
        and bool(m114_case_rows)
        and bool(m113_goal_eval_rows)
        and bool(m110_candidate_rows)
    )

    candidate_lookup = make_candidate_lookup(m110_candidate_rows)
    case_rows = build_case_failure_audit_rows(m114_case_rows, m113_goal_eval_rows, candidate_lookup)
    route_rows = build_repair_route_contract_rows(case_rows)
    input_rows = build_allowed_input_rows()
    gate_rows = build_m116_gate_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_selection_rows = build_route_selection_rows(input_ready, case_rows)
    failure_counts = Counter(str(row.get("m114_failure_class")) for row in case_rows)
    repair_counts = Counter(str(row.get("selected_repair_family")) for row in case_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m103_status": m103_coverage.get("status"),
        "m110_status": m110_coverage.get("status"),
        "m111_status": m111_coverage.get("status"),
        "m112_status": m112_coverage.get("status"),
        "m113_status": m113_coverage.get("status"),
        "m114_status": m114_coverage.get("status"),
        "case_failure_audit_rows": len(case_rows),
        "failure_class_counts": dict(sorted(failure_counts.items())),
        "selected_repair_family_counts": dict(sorted(repair_counts.items())),
        "m110_candidate_rows": m110_coverage.get("candidate_rows"),
        "m111_path_ready_candidate_rows": m111_coverage.get("source_to_snapped_path_found_rows"),
        "m112_visit_order_rows": m112_coverage.get("visit_order_rows"),
        "m113_primary_success_count_max": m113_coverage.get("primary_success_count_max"),
        "m114_goal_center_1p5_diagnostic_case_rows": m114_coverage.get("goal_center_1p5_diagnostic_case_rows"),
        "selected_next_unit": NEXT_UNIT,
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "additional_long_job_recommended_now": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "case_failure_audit_rows.jsonl": case_rows,
        "repair_route_contract_rows.jsonl": route_rows,
        "route_selection_rows.jsonl": route_selection_rows,
        "allowed_blocked_input_rows.jsonl": input_rows,
        "input_boundary_rows.jsonl": input_rows,
        "m116_gate_rows.jsonl": gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, route_rows, gate_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
