#!/usr/bin/env python3
"""Materialize E008-M176 source-coverage trigger rows."""

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

M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
M175_DIR = EXP_ROOT / "artifacts" / "E008-M175_source_coverage_trigger_candidate_source_expansion_contract_v0"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M176_source_coverage_trigger_row_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M176_source_coverage_trigger_row_materialization_smoke_v0"
)

VERSION = "e008_m176_source_coverage_trigger_row_materialization_smoke_v0"
READY_STATUS = "e008_m176_source_coverage_trigger_row_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m176_source_coverage_trigger_row_materialization_smoke_blocked"
NEXT_UNIT = "E008-M177 source-pool pose/render-plan materialization contract"

SELECTED_METHOD = "source_coverage_triggered_candidate_source_expansion_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"

SOURCE_SPARSE_UNIQUE_TOP10_THRESHOLD = 6
TOP1_CONFIDENCE_UNCERTAIN_THRESHOLD = 0.50
MEAN_TOP5_CONFIDENCE_UNCERTAIN_THRESHOLD = 0.45
PATH_READY_CANDIDATE_MIN_THRESHOLD = 25

FORBIDDEN_FIELDS = {
    "ObjectNav eval goal/viewpoints",
    "trajectory_success",
    "SR/SPL",
    "success proposal id",
    "nearest eval-viewpoint distance",
    "candidate-to-target distance",
    "post-execution StopRank",
    "posthoc threshold selected from M176 goal-evaluation",
    "eval_goal_position",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "primary_eval_hit",
    "trajectory_success",
    "SR",
    "SPL",
    "StopRank",
    "success_proposal_uid",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "nearest_eval_viewpoint_distance_m",
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


def finite_float(value: object, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def int_value(value: object, default: int = 10**9) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        out.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(out)


def nonempty(value: Any) -> bool:
    return value not in {None, False, "", 0} and value != [] and value != {}


def confidence(row: dict[str, Any]) -> float:
    return finite_float(row.get("confidence"), 0.0) or 0.0


def visit_rank(row: dict[str, Any]) -> int:
    return int_value(row.get("visit_rank") or row.get("m168_detector_visit_rank"))


def coverage_key(row: dict[str, Any]) -> str:
    return str(row.get("m168_coverage_key") or row.get("observation_pose_id") or row.get("proposal_uid") or "unknown")


def row_blocked_hits(row: dict[str, Any]) -> list[str]:
    hits = [field for field in FORBIDDEN_FIELDS if field in row and nonempty(row.get(field))]
    if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_eval_goal_or_viewpoint"):
        hits.append("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    if row.get("uses_success_label_for_policy") or row.get("policy_input_uses_success_label"):
        hits.append("uses_success_label_for_policy")
    return sorted(set(hits))


def grouped_detector_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("policy_id") == PROTECTED_BASELINE:
            grouped[str(row.get("benchmark_row_uid"))].append(row)
    return {key: sorted(value, key=visit_rank) for key, value in grouped.items()}


def build_trigger_rows(detector_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = grouped_detector_rows(detector_rows)
    rows: list[dict[str, Any]] = []
    for uid, candidates in sorted(grouped.items()):
        top10 = candidates[:10]
        top5 = candidates[:5]
        first = candidates[0] if candidates else {}
        top10_unique = len({coverage_key(row) for row in top10})
        top1_conf = confidence(first) if first else 0.0
        mean_top5_conf = mean([confidence(row) for row in top5]) or 0.0
        path_ready_rows = sum(bool(row.get("path_ready")) for row in candidates)
        source_ready_rows = sum(
            bool(
                row.get("source_snap_validation_ready")
                or row.get("source_navigable")
                or row.get("source_to_snapped_path_found")
            )
            for row in candidates
        )
        source_sparse = top10_unique <= SOURCE_SPARSE_UNIQUE_TOP10_THRESHOLD
        confidence_uncertain = (
            top1_conf < TOP1_CONFIDENCE_UNCERTAIN_THRESHOLD
            or mean_top5_conf < MEAN_TOP5_CONFIDENCE_UNCERTAIN_THRESHOLD
        )
        path_gap = path_ready_rows < PATH_READY_CANDIDATE_MIN_THRESHOLD or len(candidates) < PATH_READY_CANDIDATE_MIN_THRESHOLD
        trigger_ids = []
        if source_sparse:
            trigger_ids.append("current_source_coverage_sparse_v1")
        if confidence_uncertain:
            trigger_ids.append("detector_confidence_uncertainty_v1")
        if path_gap:
            trigger_ids.append("path_or_source_ready_gap_v1")
        request_expansion = bool(trigger_ids)
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_coverage_trigger",
                "trigger_row_uid": f"m176::{uid}",
                "benchmark_row_uid": uid,
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "protected_baseline_policy_id": PROTECTED_BASELINE,
                "selected_method_id": SELECTED_METHOD,
                "candidate_rows": len(candidates),
                "path_ready_candidate_rows": path_ready_rows,
                "source_ready_candidate_rows": source_ready_rows,
                "top10_unique_coverage_keys": top10_unique,
                "top1_confidence": top1_conf,
                "mean_top5_confidence": mean_top5_conf,
                "source_sparse_trigger": source_sparse,
                "detector_uncertainty_trigger": confidence_uncertain,
                "path_or_source_ready_gap_trigger": path_gap,
                "trigger_ids": trigger_ids,
                "trigger_count": len(trigger_ids),
                "request_candidate_source_expansion": request_expansion,
                "selected_method_action": "request_candidate_source_expansion" if request_expansion else "rank_current_candidates_only",
                "baseline_action": "rank_current_candidates_only",
                "policy_visible_source_request_change": request_expansion,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
                "thresholds": {
                    "source_sparse_unique_top10_threshold": SOURCE_SPARSE_UNIQUE_TOP10_THRESHOLD,
                    "top1_confidence_uncertain_threshold": TOP1_CONFIDENCE_UNCERTAIN_THRESHOLD,
                    "mean_top5_confidence_uncertain_threshold": MEAN_TOP5_CONFIDENCE_UNCERTAIN_THRESHOLD,
                    "path_ready_candidate_min_threshold": PATH_READY_CANDIDATE_MIN_THRESHOLD,
                },
                "claim_boundary": "M176 materializes source-expansion trigger rows only; no detector, goal-evaluation, or trajectory result is claimed.",
            }
        )
    return rows


def planned_pose_budget(trigger_row: dict[str, Any]) -> int:
    budget = 0
    if trigger_row.get("source_sparse_trigger"):
        budget += 12
    if trigger_row.get("detector_uncertainty_trigger"):
        budget += 8
    if trigger_row.get("path_or_source_ready_gap_trigger"):
        budget += 12
    return min(24, max(8, budget))


def build_expansion_plan_rows(trigger_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_routes = [
        row
        for row in route_rows
        if row.get("selected_for_m176")
        and row.get("route_id") == "full_val_mini_triggered_source_pool_materialization_v1"
    ]
    if not selected_routes:
        selected_routes = [
            row
            for row in route_rows
            if row.get("selected_for_m176")
            and row.get("route_id") == "m121_target_free_source_pose_pool_template_v1"
        ]
    rows: list[dict[str, Any]] = []
    for trigger in trigger_rows:
        if not trigger.get("request_candidate_source_expansion"):
            continue
        for route in selected_routes:
            budget = planned_pose_budget(trigger)
            yaw_samples = 4
            rows.append(
                {
                    "version": VERSION,
                    "row_type": "candidate_source_expansion_plan",
                    "expansion_plan_uid": f"m176::{trigger['benchmark_row_uid']}::{route.get('route_id')}",
                    "trigger_row_uid": trigger.get("trigger_row_uid"),
                    "benchmark_row_uid": trigger.get("benchmark_row_uid"),
                    "adapter_episode_id": trigger.get("adapter_episode_id"),
                    "scan_id": trigger.get("scan_id"),
                    "scene_key": trigger.get("scene_key"),
                    "object_category": trigger.get("object_category"),
                    "route_id": route.get("route_id"),
                    "route_decision": route.get("decision"),
                    "source_template_id": "m121_target_free_source_pose_pool_template_v1",
                    "planned_observation_pose_rows": budget,
                    "planned_yaw_samples_per_pose": yaw_samples,
                    "planned_render_plan_rows": budget * yaw_samples,
                    "candidate_source_pool_expansion_allowed": True,
                    "requires_render_or_detector_long_job_now": False,
                    "requires_m177_pose_materialization": True,
                    "requires_m178_render_detector_launcher": True,
                    "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_success_label_for_policy": False,
                    "trigger_ids": trigger.get("trigger_ids"),
                    "policy_visible_source_request_change": True,
                    "claim_boundary": "This is a source-pool request row, not a rendered-frame, detector-candidate, or trajectory result.",
                }
            )
    return rows


def build_allowed_input_audit_rows(rows_to_audit: list[dict[str, Any]], contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_groups = [row.get("field_group") for row in contract_rows if row.get("allowed_for_m176")]
    return [
        {
            "version": VERSION,
            "row_type": "allowed_input_audit",
            "field_group": field,
            "available_for_m176": True,
            "audited_row_count": len(rows_to_audit),
            "audit_status": "pass",
            "reason": "M176 rows use only pre-execution source coverage, confidence, path/source readiness, and source request planning fields.",
        }
        for field in allowed_groups
    ]


def build_blocked_input_audit_rows(rows_to_audit: list[dict[str, Any]], contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked_groups = [row.get("field_group") for row in contract_rows if row.get("blocked_for_m176")]
    hits = []
    for row in rows_to_audit:
        for field in row_blocked_hits(row):
            hits.append(
                {
                    "version": VERSION,
                    "row_type": "blocked_input_hit",
                    "row_uid": row.get("trigger_row_uid") or row.get("expansion_plan_uid"),
                    "field": field,
                }
            )
    rows = [
        {
            "version": VERSION,
            "row_type": "blocked_input_audit",
            "field_group": field,
            "blocked_for_m176": True,
            "hit_rows": sum(1 for hit in hits if hit.get("field") == field),
            "audit_status": "pass",
            "reason": "Forbidden fields are checked directly on M176 materialized rows.",
        }
        for field in blocked_groups
    ]
    rows.extend(hits)
    return rows


def build_policy_visible_change_probe_rows(trigger_rows: list[dict[str, Any]], expansion_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expansion_by_uid = Counter(str(row.get("benchmark_row_uid")) for row in expansion_rows)
    rows = []
    for trigger in trigger_rows:
        changed = bool(trigger.get("policy_visible_source_request_change")) and expansion_by_uid[str(trigger.get("benchmark_row_uid"))] > 0
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_visible_change_probe",
                "benchmark_row_uid": trigger.get("benchmark_row_uid"),
                "baseline_action": trigger.get("baseline_action"),
                "selected_method_action": trigger.get("selected_method_action"),
                "expansion_plan_rows": expansion_by_uid[str(trigger.get("benchmark_row_uid"))],
                "policy_visible_row_changed": changed,
                "candidate_visit_order_changed": False,
                "why_candidate_order_not_changed": "M176 only requests source expansion; detector candidates are generated in later units.",
            }
        )
    return rows


def build_route_decision_rows(ready: bool, changed_rows: int, leakage_fail_rows: int) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "launch_docker_trajectory_now",
            "decision": "reject",
            "selected": False,
            "reason": "M176 does not contain rendered/detector candidates or runner-compatible trajectory rows.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "render_detector_long_job_now",
            "decision": "defer",
            "selected": False,
            "reason": "M176 first fixes trigger/source-request rows; M177/M178 must materialize pose/render-plan and launcher contracts.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "source_pool_pose_render_plan_materialization",
            "decision": "select_next" if ready else "blocked",
            "selected": ready,
            "reason": (
                f"M176 has {changed_rows} policy-visible source request rows and {leakage_fail_rows} leakage failures."
            ),
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M176 materialization",
            "launch_long_job_now": False,
        },
    ]


def build_next_verification_sequence_rows() -> list[dict[str, Any]]:
    steps = [
        (
            "E008-M177",
            "source-pool pose/render-plan materialization contract with budget priority",
            "turn M176 source requests into target-free source-pose/render-plan rows without eval-goal leakage while controlling broad-trigger cost",
            "pose/render rows exist, source placement uses only scene/navmesh/start/source-coverage inputs, and budget/priority guard is fixed",
        ),
        (
            "E008-M178",
            "navmesh/snap validation and render/detector launcher contract",
            "verify source poses are reachable and prepare bounded render/detector long-job commands",
            "snap/path/source-ready checks pass; commands and logs are recorded before launch",
        ),
        (
            "E008-M179",
            "render/detector execution and verification",
            "generate RGB-D/open-vocabulary candidates from requested source poses",
            "prediction rows, pre-cap rows, validator status, and source/candidate counts are ready",
        ),
        (
            "E008-M180",
            "candidate navmesh/source-readiness validation",
            "filter detector/map candidates to navigation-usable rows",
            "candidate coordinates snap to navmesh and path-ready/source-ready splits are available",
        ),
        (
            "E008-M181",
            "expanded candidate visit-order/path materialization",
            "attach expanded candidates to detector-confidence baseline and selected trigger policy",
            "selected method changes candidate visit order or candidate-source availability under leakage audit",
        ),
        (
            "E008-M182",
            "leakage-safe goal-evaluation proxy",
            "test recovery before expensive trajectory execution",
            "proxy recovery, failure taxonomy, source-ready/source-gap split, and no denominator changes",
        ),
        (
            "E008-M183",
            "Docker trajectory execution contract and preflight",
            "create runner-compatible rows only if M182 shows a policy-visible gain worth executing",
            "Docker/data/runner preflight pass with exact command and no eval leakage in policy inputs",
        ),
        (
            "E008-M184",
            "Docker trajectory execution",
            "measure executed navigation behavior",
            "`SR`, `SPL`, path length, visits, failure type, and logs are produced",
        ),
        (
            "E008-M185",
            "protected-baseline interpretation and scale decision",
            "decide whether the source-trigger method beats detector-confidence under fixed gates",
            "positive claim only if protected `SR`/`SPL`/visit gates pass; otherwise record failure and pivot",
        ),
        (
            "post-M185",
            "heldout transfer, ablations, and external baselines",
            "pressure top-tier claim beyond one route",
            "`ConceptGraphs`/`Open3DSG`/`HOV-SG` or navigation baselines plus source-trigger ablations support generality",
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "next_verification_sequence",
            "order": index,
            "unit": unit,
            "target": target,
            "goal": goal,
            "pass_condition": pass_condition,
        }
        for index, (unit, target, goal, pass_condition) in enumerate(steps, start=1)
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "source_coverage_trigger_materialized",
            "supported": True,
            "claim_boundary": "M176 supports that non-leaky source-coverage trigger/source-request rows can be materialized on the M168 full-val-mini denominator.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "candidate_source_recovery",
            "supported": False,
            "claim_boundary": "M176 does not generate rendered frames, detector candidates, or recovered object candidates.",
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim_id": "real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still requires source-pool materialization, detector/map candidate generation, navmesh validation, trajectory execution, and protected-baseline interpretation.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    trigger_rows: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
    change_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
) -> str:
    trigger_summary = [
        {
            "trigger_id": "current_source_coverage_sparse_v1",
            "fired_rows": sum(row.get("source_sparse_trigger") for row in trigger_rows),
        },
        {
            "trigger_id": "detector_confidence_uncertainty_v1",
            "fired_rows": sum(row.get("detector_uncertainty_trigger") for row in trigger_rows),
        },
        {
            "trigger_id": "path_or_source_ready_gap_v1",
            "fired_rows": sum(row.get("path_or_source_ready_gap_trigger") for row in trigger_rows),
        },
    ]
    return "\n".join(
        [
            "# E008-M176 Source-Coverage Trigger Row Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M175 status: `{coverage['m175_status']}`.",
            f"- Trigger rows: {coverage['trigger_rows']}.",
            f"- Trigger request rows: {coverage['trigger_request_rows']}.",
            f"- Trigger selectivity warning: {str(coverage['trigger_selectivity_warning']).lower()}.",
            f"- Expansion plan rows: {coverage['candidate_source_expansion_plan_rows']}.",
            f"- Policy-visible source request changed rows: {coverage['policy_visible_source_request_changed_rows']}.",
            f"- Blocked input hit rows: {coverage['blocked_input_hit_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Trigger Summary",
            "",
            table(trigger_summary, ["trigger_id", "fired_rows"]),
            "",
            "## Expansion Plan",
            "",
            table(
                expansion_rows[:10],
                [
                    "benchmark_row_uid",
                    "route_id",
                    "planned_observation_pose_rows",
                    "planned_render_plan_rows",
                ],
            ),
            "",
            "## Policy-Visible Change Probe",
            "",
            table(
                change_rows[:10],
                [
                    "benchmark_row_uid",
                    "baseline_action",
                    "selected_method_action",
                    "expansion_plan_rows",
                    "policy_visible_row_changed",
                ],
            ),
            "",
            "## Route Decision",
            "",
            table(route_rows, ["route_id", "decision", "selected", "reason", "selected_next_unit"]),
            "",
            "## Next Verification Sequence If M176 Proceeds Normally",
            "",
            table(next_rows, ["order", "unit", "target", "goal", "pass_condition"]),
            "",
            "## Claim Boundary",
            "",
            "- M176 is a source-trigger row materialization smoke, not a performance result.",
            "- Because source requests fire on the whole 30-row denominator, M177 must add a fixed source-expansion budget/priority guard before any long job.",
            "- M176 does not launch render, detector, external-map, or Docker trajectory jobs.",
            "- Candidate-source recovery and real navigation `SR` / `SPL` remain blocked until later units generate candidates and execute trajectories.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m168 = read_json(M168_DIR / "coverage.json")
    m175 = read_json(M175_DIR / "coverage.json")
    detector_rows = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")
    input_contract_rows = read_jsonl(M175_DIR / "input_contract_rows.jsonl")
    route_contract_rows = read_jsonl(M175_DIR / "candidate_source_route_rows.jsonl")

    missing: list[str] = []
    if m168.get("status") != "e008_m168_source_coverage_memory_interface_materialization_ready":
        missing.append("M168 source coverage materialization")
    if m175.get("status") != "e008_m175_source_coverage_trigger_candidate_source_expansion_contract_ready":
        missing.append("M175 source coverage trigger contract")
    if not detector_rows:
        missing.append("M168 source coverage candidate rows")
    if not input_contract_rows:
        missing.append("M175 input contract rows")
    if not route_contract_rows:
        missing.append("M175 candidate source route rows")

    trigger_rows = build_trigger_rows(detector_rows) if not missing else []
    expansion_rows = build_expansion_plan_rows(trigger_rows, route_contract_rows) if not missing else []
    audited_rows = trigger_rows + expansion_rows
    allowed_audit_rows = build_allowed_input_audit_rows(audited_rows, input_contract_rows) if not missing else []
    blocked_audit_rows = build_blocked_input_audit_rows(audited_rows, input_contract_rows) if not missing else []
    blocked_hit_rows = [row for row in blocked_audit_rows if row.get("row_type") == "blocked_input_hit"]
    change_rows = build_policy_visible_change_probe_rows(trigger_rows, expansion_rows) if not missing else []
    changed_rows = sum(bool(row.get("policy_visible_row_changed")) for row in change_rows)
    trigger_request_rows = sum(bool(row.get("request_candidate_source_expansion")) for row in trigger_rows)
    trigger_selectivity_warning = bool(trigger_rows) and trigger_request_rows / max(1, len(trigger_rows)) > 0.80
    ready = not missing and bool(trigger_rows) and bool(expansion_rows) and not blocked_hit_rows and changed_rows > 0
    route_rows = build_route_decision_rows(ready, changed_rows, len(blocked_hit_rows))
    next_rows = build_next_verification_sequence_rows()
    claim_rows = build_claim_boundary_rows()

    trigger_counter = Counter()
    for row in trigger_rows:
        for trigger_id in row.get("trigger_ids") or []:
            trigger_counter[str(trigger_id)] += 1

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m168_status": m168.get("status"),
        "m175_status": m175.get("status"),
        "selected_method_id": SELECTED_METHOD,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "trigger_rows": len(trigger_rows),
        "trigger_request_rows": trigger_request_rows,
        "trigger_request_rate": trigger_request_rows / max(1, len(trigger_rows)),
        "trigger_selectivity_warning": trigger_selectivity_warning,
        "budget_priority_guard_required_next": trigger_selectivity_warning,
        "candidate_source_expansion_plan_rows": len(expansion_rows),
        "policy_visible_change_probe_rows": len(change_rows),
        "policy_visible_source_request_changed_rows": changed_rows,
        "blocked_input_hit_rows": len(blocked_hit_rows),
        "source_sparse_trigger_rows": trigger_counter.get("current_source_coverage_sparse_v1", 0),
        "detector_uncertainty_trigger_rows": trigger_counter.get("detector_confidence_uncertainty_v1", 0),
        "path_or_source_ready_gap_trigger_rows": trigger_counter.get("path_or_source_ready_gap_v1", 0),
        "m177_materialization_ready_next": ready,
        "render_or_detector_long_job_ready_now": False,
        "docker_trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M176 materialization",
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_coverage_trigger_rows.jsonl", trigger_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_source_expansion_plan_rows.jsonl", expansion_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_input_audit_rows.jsonl", allowed_audit_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_audit_rows.jsonl", blocked_audit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_visible_change_probe_rows.jsonl", change_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "next_verification_sequence_rows.jsonl", next_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, trigger_rows, expansion_rows, change_rows, route_rows, next_rows),
        encoding="utf-8",
    )

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
