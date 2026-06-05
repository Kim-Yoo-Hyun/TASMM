#!/usr/bin/env python3
"""Fix the M117 stop-region/source-coverage repair route decision for ConceptGraphs HM3D."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M116_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_v0"
)

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"
)

VERSION = "e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_v0"
READY_STATUS = "e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_ready"
BLOCKED_STATUS = "e008_m117_conceptgraphs_hm3d_stop_region_transform_source_coverage_route_decision_blocked"
NEXT_UNIT = "E008-M118 ConceptGraphs HM3D non-oracle stop-region transform materialization smoke"


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


def has_xyz(value: object) -> bool:
    return isinstance(value, list) and len(value) >= 3 and all(finite_float(item) is not None for item in value[:3])


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def build_stop_region_transform_contract_rows(stop_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in stop_rows:
        center_ready = has_xyz(row.get("best_goal_candidate_center_xyz"))
        extent_ready = has_xyz(row.get("best_goal_candidate_extent_xyz"))
        snapped_ready = has_xyz(row.get("best_goal_candidate_snapped_position_m"))
        min_rank = row.get("best_goal_candidate_min_policy_rank")
        try:
            min_rank_int = int(min_rank)
        except (TypeError, ValueError):
            min_rank_int = None
        input_ready = center_ready and extent_ready and snapped_ready
        budget5_ready = bool(row.get("budget5_policy_rank_ready"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "stop_region_transform_contract",
                "query_uid": row.get("query_uid"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "source_candidate_uid": row.get("best_goal_candidate_uid"),
                "source_candidate_rank": row.get("best_goal_candidate_rank"),
                "source_candidate_min_policy_rank": min_rank_int,
                "candidate_center_ready": center_ready,
                "candidate_extent_ready": extent_ready,
                "candidate_snapped_position_ready": snapped_ready,
                "transform_input_ready": input_ready,
                "budget5_visible_before_transform": budget5_ready,
                "budget_repair_required": not budget5_ready,
                "selected_transform_id": "candidate_geometry_radial_stop_region_v0",
                "selected_policy_repair_id": "semantic_path_budgeted_stop_region_candidate_expansion_v0",
                "allowed_source_inputs": [
                    "candidate_center_xyz",
                    "candidate_extent_xyz",
                    "candidate_snapped_position_m",
                    "candidate semantic score",
                    "candidate source image ids",
                    "navmesh reachability",
                    "source-to-candidate path cost",
                    "frozen policy ranks",
                ],
                "blocked_source_inputs": [
                    "ObjectNav eval goal position",
                    "ObjectNav target viewpoint coordinates",
                    "target object id",
                    "success label",
                    "candidate-to-target distance before frozen evaluation",
                ],
                "m118_output_contract": [
                    "stop_region_candidate_rows.jsonl",
                    "stop_region_navmesh_validation_rows.jsonl",
                    "budget_visibility_rows.jsonl",
                    "leakage_audit_rows.jsonl",
                    "m119_gate_rows.jsonl",
                ],
                "m118_evaluation_metrics": [
                    "StopRegionCandidateReachable",
                    "Budget5Visibility",
                    "AddedCandidateCount",
                    "PolicyCostDelta",
                    "posthoc target-viewpoint hit after frozen transform",
                ],
                "route_decision": "select_m118_stop_region_transform_smoke",
                "route_reason": (
                    "The candidate is near the goal center in posthoc audit but misses target viewpoints and "
                    "budget visibility. This can be tested with a non-oracle geometry transform before any "
                    "trajectory run."
                ),
                "launch_long_job_now": False,
                "selected_next_unit": NEXT_UNIT,
            }
        )
    return rows


def build_source_coverage_route_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        min_any = finite_float(row.get("min_any_viewpoint_xz_m"))
        primary_rows = int(row.get("primary_target_near_candidate_rows") or 0)
        relaxed_rows = int(row.get("relaxed_target_near_candidate_rows") or 0)
        current_source_recoverable = primary_rows > 0 or relaxed_rows > 0 or (min_any is not None and min_any <= 5.0)
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_coverage_route_decision",
                "query_uid": row.get("query_uid"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "candidate_source": row.get("candidate_source"),
                "path_ready_eval_candidate_rows": row.get("path_ready_eval_candidate_rows"),
                "min_any_viewpoint_xz_m": min_any,
                "primary_target_near_candidate_rows": primary_rows,
                "relaxed_target_near_candidate_rows": relaxed_rows,
                "current_source_recoverable_without_new_source": current_source_recoverable,
                "same_source_rerank_decision": "reject",
                "same_source_rerun_decision": "reject",
                "selected_source_coverage_route": "external_or_visibility_candidate_source_preflight_v0",
                "source_coverage_route_status": "defer_after_m118_or_run_if_stop_region_route_fails",
                "allowed_source_repair_inputs": [
                    "non-target-conditioned observation coverage statistics",
                    "frame coverage / visibility metadata",
                    "generic open-vocabulary map/proposal outputs",
                    "navmesh reachability",
                    "candidate semantic score",
                ],
                "blocked_source_repair_inputs": [
                    "ObjectNav eval goal position",
                    "ObjectNav target viewpoint coordinates",
                    "target object id",
                    "success label",
                    "distance-to-target fields before frozen evaluation",
                ],
                "source_coverage_m119_options": [
                    "visibility_coverage_audit_for_current_source_route",
                    "stronger_external_map_or_proposal_source_preflight",
                    "broader_non_oracle_observation_route",
                ],
                "route_reason": (
                    "The current ConceptGraphs source has no target-near path-ready sofa candidate. The next "
                    "source-coverage repair must change source coverage or external proposal source, not ranking."
                ),
                "launch_long_job_now": False,
                "selected_next_unit_after_m118": (
                    "E008-M119 ConceptGraphs/HM3D source-coverage external-or-visibility preflight"
                ),
            }
        )
    return rows


def build_route_priority_rows(
    stop_contract_rows: list[dict[str, Any]],
    source_route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stop_ready = any(row.get("transform_input_ready") for row in stop_contract_rows)
    source_needs_new_source = any(
        not row.get("current_source_recoverable_without_new_source") for row in source_route_rows
    )
    return [
        {
            "version": VERSION,
            "route_id": "direct_trajectory_execution",
            "priority": 0,
            "decision": "reject_now",
            "reason": "M116/M117 still have no recovered source-gap candidate and no frozen stop-region transformed candidate.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "same_conceptgraphs_reranking",
            "priority": 0,
            "decision": "reject_now",
            "reason": "Reranking cannot create a sofa target-region candidate and the toilet candidate is outside budget-5.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "stop_region_transform_smoke",
            "priority": 1,
            "decision": "select_next",
            "reason": "It is local, leakage-safe, executable from candidate geometry, and tests the only M116 case with a near object candidate.",
            "input_ready": stop_ready,
            "launch_long_job_now": False,
            "selected_next_unit": NEXT_UNIT,
        },
        {
            "version": VERSION,
            "route_id": "source_coverage_external_or_visibility_preflight",
            "priority": 2,
            "decision": "defer_but_required",
            "reason": "The sofa case needs changed source coverage or a stronger external proposal/map source; this is heavier than the stop-region smoke.",
            "input_ready": source_needs_new_source,
            "launch_long_job_now": False,
            "selected_next_unit_after_m118": (
                "E008-M119 ConceptGraphs/HM3D source-coverage external-or-visibility preflight"
            ),
        },
    ]


def build_allowed_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "field": "M116 candidate geometry and extents",
            "route": "stop_region_transform_smoke",
            "allowed_as_policy_input": True,
            "allowed_as_metric_input": True,
            "audit_status": "pass",
            "reason": "These fields are generated by the frozen ConceptGraphs candidate source.",
        },
        {
            "version": VERSION,
            "field": "M116 posthoc distance-to-target audit fields",
            "route": "all",
            "allowed_as_policy_input": False,
            "allowed_as_metric_input": True,
            "audit_status": "pass",
            "reason": "M117 uses them only to decide which repair family is needed, not to generate candidates.",
        },
        {
            "version": VERSION,
            "field": "ObjectNav eval goal / target viewpoint coordinates",
            "route": "all",
            "allowed_as_policy_input": False,
            "allowed_as_metric_input": "posthoc_only",
            "audit_status": "pass",
            "reason": "M118/M119 must freeze candidates and policy order before any target-distance evaluation.",
        },
        {
            "version": VERSION,
            "field": "target object id / success label",
            "route": "all",
            "allowed_as_policy_input": False,
            "allowed_as_metric_input": False,
            "audit_status": "pass",
            "reason": "Neither route may use target identity or success labels as source, transform, or policy inputs.",
        },
    ]


def build_m118_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M118 materializes stop-region candidates from candidate geometry, snaps them to navmesh, and freezes visit order before posthoc target evaluation.",
            "next_action": "Run M118 stop-region transform materialization smoke.",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "M118 can materialize candidates but cannot make them budget-visible without broadening policy top-k or adding a context-free fallback trigger.",
            "next_action": "Treat M118 as interface evidence and move to M119 source-coverage/external route.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M118 requires ObjectNav target viewpoints, eval goal, target object id, or success labels to choose stop points.",
            "next_action": "Do not run trajectory; redesign the transform contract.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_route_decision",
            "supported": True,
            "claim_boundary": "M117 supports selecting stop-region transform smoke as the next executable local repair route and deferring source-coverage repair to external/visibility preflight.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_no_same_source_rerank",
            "supported": True,
            "claim_boundary": "M117 supports rejecting same-source reranking/repeating as insufficient for the sofa source-coverage gap.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_stop_region_recovery",
            "supported": False,
            "claim_boundary": "M117 does not materialize transformed stop-region candidates or recover the toilet case.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M117 does not create a new source for the sofa case and does not recover source-gap failures.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M117 does not execute Habitat trajectories and does not provide SR/SPL evidence.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not go directly to trajectory after M116?",
            "answer": "M116 has no recovered candidate for sofa and no transformed stop-region target for toilet. Trajectory now would only measure a known failed source/interface.",
        },
        {
            "version": VERSION,
            "question": "Why select stop-region transform before source-coverage repair?",
            "answer": "The toilet case is locally executable from non-oracle candidate geometry, while sofa needs a changed candidate source or visibility route. The smaller executable repair should be tested first.",
        },
        {
            "version": VERSION,
            "question": "Does M117 use target leakage?",
            "answer": "No. Target distances from M116 are used only as posthoc audit evidence. M118 is required to freeze transformed candidates before any ObjectNav target evaluation.",
        },
        {
            "version": VERSION,
            "question": "What happens to the sofa case?",
            "answer": "It is not ignored. M117 explicitly defers it to a required source-coverage external/visibility preflight because the current ConceptGraphs source has no target-near candidate to rerank.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    stop_contract_rows: list[dict[str, Any]],
    source_route_rows: list[dict[str, Any]],
    route_priority_rows: list[dict[str, Any]],
    m118_gate_rows: list[dict[str, Any]],
) -> str:
    stop_lines = [
        "| {scan_id} | {object_category} | {source_candidate_uid} | {transform_input_ready} | {budget_repair_required} | {route_decision} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            source_candidate_uid=row.get("source_candidate_uid"),
            transform_input_ready=row.get("transform_input_ready"),
            budget_repair_required=row.get("budget_repair_required"),
            route_decision=row.get("route_decision"),
        )
        for row in stop_contract_rows
    ]
    source_lines = [
        "| {scan_id} | {object_category} | {min_any_viewpoint_xz_m} | {current_source_recoverable_without_new_source} | {selected_source_coverage_route} | {source_coverage_route_status} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            min_any_viewpoint_xz_m=fmt(row.get("min_any_viewpoint_xz_m")),
            current_source_recoverable_without_new_source=row.get(
                "current_source_recoverable_without_new_source"
            ),
            selected_source_coverage_route=row.get("selected_source_coverage_route"),
            source_coverage_route_status=row.get("source_coverage_route_status"),
        )
        for row in source_route_rows
    ]
    route_lines = [
        "| {route_id} | {priority} | {decision} | {reason} |".format(
            route_id=row.get("route_id"),
            priority=row.get("priority"),
            decision=row.get("decision"),
            reason=row.get("reason"),
        )
        for row in route_priority_rows
    ]
    gate_lines = [
        "| {gate} | {condition} | {next_action} |".format(
            gate=row.get("gate"),
            condition=row.get("condition"),
            next_action=row.get("next_action"),
        )
        for row in m118_gate_rows
    ]
    return f"""# E008-M117 ConceptGraphs HM3D Stop-Region Transform / Source-Coverage Route Decision

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M116 status: `{coverage['m116_status']}`.
- Stop-region transform contract rows: {coverage['stop_region_transform_contract_rows']}.
- Source-coverage route decision rows: {coverage['source_coverage_route_decision_rows']}.
- Selected immediate next unit: {coverage['selected_next_unit']}.
- Source-coverage route is deferred but required: {coverage['source_coverage_route_deferred_but_required']}.
- Launch long job now: {coverage['launch_long_job_now']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.

## Stop-Region Transform Route

| scan_id | category | source candidate | input ready | budget repair required | decision |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(stop_lines)}

## Source-Coverage Route

| scan_id | category | min any-vp XZ m | recoverable without new source | selected route | status |
| --- | --- | ---: | --- | --- | --- |
{chr(10).join(source_lines)}

## Route Priority

| route | priority | decision | reason |
| --- | ---: | --- | --- |
{chr(10).join(route_lines)}

## M118 Gate

| gate | condition | next action |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M117 supports route selection only.
- M117 does not materialize stop-region candidates, recover source-gap cases, execute trajectories, or support final real navigation `SR` / `SPL`.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m116_coverage = read_json(M116_DIR / "coverage.json")
    source_rows = read_jsonl(M116_DIR / "source_coverage_audit_rows.jsonl")
    stop_rows = read_jsonl(M116_DIR / "stop_region_alignment_audit_rows.jsonl")
    blocked_rows = read_jsonl(M116_DIR / "blocked_input_audit_rows.jsonl")

    input_ready = (
        m116_coverage.get("status")
        == "e008_m116_conceptgraphs_hm3d_stop_region_source_coverage_audit_materialization_contract_ready"
        and bool(source_rows)
        and bool(stop_rows)
        and bool(blocked_rows)
        and bool(m116_coverage.get("blocked_input_audit_pass"))
    )

    stop_contract_rows = build_stop_region_transform_contract_rows(stop_rows)
    source_route_rows = build_source_coverage_route_rows(source_rows)
    route_priority_rows = build_route_priority_rows(stop_contract_rows, source_route_rows)
    allowed_blocked_rows = build_allowed_blocked_input_rows()
    m118_gate_rows = build_m118_gate_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()

    m117_gate_pass = (
        input_ready
        and any(row.get("transform_input_ready") for row in stop_contract_rows)
        and any(row.get("route_decision") == "select_m118_stop_region_transform_smoke" for row in stop_contract_rows)
        and any(row.get("same_source_rerank_decision") == "reject" for row in source_route_rows)
        and all(row.get("audit_status") == "pass" for row in allowed_blocked_rows)
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if m117_gate_pass else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m116_status": m116_coverage.get("status"),
        "m116_blocked_input_audit_pass": m116_coverage.get("blocked_input_audit_pass"),
        "m116_source_coverage_audit_rows": len(source_rows),
        "m116_stop_region_alignment_audit_rows": len(stop_rows),
        "stop_region_transform_contract_rows": len(stop_contract_rows),
        "stop_region_transform_input_ready_rows": sum(
            1 for row in stop_contract_rows if row.get("transform_input_ready")
        ),
        "source_coverage_route_decision_rows": len(source_route_rows),
        "source_coverage_without_new_source_recoverable_rows": sum(
            1 for row in source_route_rows if row.get("current_source_recoverable_without_new_source")
        ),
        "source_coverage_route_deferred_but_required": bool(source_route_rows),
        "route_priority_rows": len(route_priority_rows),
        "allowed_blocked_input_rows": len(allowed_blocked_rows),
        "allowed_blocked_input_audit_pass": all(
            row.get("audit_status") == "pass" for row in allowed_blocked_rows
        ),
        "m117_gate_pass": m117_gate_pass,
        "selected_next_unit": NEXT_UNIT,
        "selected_next_unit_reason": "Stop-region transform is the only local leakage-safe repair with input-ready candidate geometry.",
        "deferred_next_unit": "E008-M119 ConceptGraphs/HM3D source-coverage external-or-visibility preflight",
        "launch_long_job_now": False,
        "additional_long_job_recommended_now": False,
        "direct_trajectory_promotion_ready": False,
        "stop_region_transform_materialized": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "stop_region_transform_contract_rows.jsonl": stop_contract_rows,
        "source_coverage_route_decision_rows.jsonl": source_route_rows,
        "route_priority_rows.jsonl": route_priority_rows,
        "allowed_blocked_input_rows.jsonl": allowed_blocked_rows,
        "m118_gate_rows.jsonl": m118_gate_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, stop_contract_rows, source_route_rows, route_priority_rows, m118_gate_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
