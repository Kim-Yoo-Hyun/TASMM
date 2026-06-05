#!/usr/bin/env python3
"""Interpret M89 source-gap detector-goal results and decide trajectory promotion."""

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
M87_DIR = EXP_ROOT / "artifacts" / "E008-M87_source_gap_detector_candidate_navmesh_validation_v0"
M88_DIR = EXP_ROOT / "artifacts" / "E008-M88_source_gap_detector_candidate_visit_order_path_smoke_v0"
M89_DIR = EXP_ROOT / "artifacts" / "E008-M89_source_gap_detector_candidate_goal_evaluation_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0"
)

VERSION = "e008_m90_source_gap_detector_goal_result_interpretation_trajectory_decision_v0"
READY_STATUS = "e008_m90_source_gap_detector_goal_result_interpretation_trajectory_decision_ready"
BLOCKED_STATUS = "e008_m90_source_gap_detector_goal_result_interpretation_trajectory_decision_blocked"
NEXT_UNIT = "E008-M91 source-gap target-coverage and candidate-source failure diagnosis"

PRIMARY_RADIUS_M = 1.0
NEAR_MISS_RADIUS_M = 1.5
SEVERE_GAP_RADIUS_M = 3.0


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


def min_finite(values: list[object]) -> float | None:
    clean = [finite_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return min(clean) if clean else None


def classify_distance(best_any_viewpoint_xz_m: float | None) -> str:
    if best_any_viewpoint_xz_m is None:
        return "unknown_no_distance"
    if best_any_viewpoint_xz_m <= PRIMARY_RADIUS_M:
        return "covered_under_primary_radius"
    if best_any_viewpoint_xz_m <= NEAR_MISS_RADIUS_M:
        return "near_miss_threshold_gap"
    if best_any_viewpoint_xz_m <= SEVERE_GAP_RADIUS_M:
        return "moderate_candidate_localization_gap"
    return "severe_candidate_source_coverage_gap"


def next_action_for_gap(distance_class: str) -> str:
    if distance_class == "severe_candidate_source_coverage_gap":
        return "audit_target_visibility_and_expand_candidate_source_coverage"
    if distance_class == "moderate_candidate_localization_gap":
        return "audit_candidate_localization_viewpoint_threshold_and_box_projection"
    if distance_class == "near_miss_threshold_gap":
        return "audit_metric_threshold_and_stop-region_alignment"
    if distance_class == "covered_under_primary_radius":
        return "debug_metric_join_before_any_policy_change"
    return "inspect_missing_distance_rows"


def build_case_interpretation_rows(
    source_ready_rows: list[dict[str, Any]],
    path_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    path_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    goal_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in path_rows:
        path_by_scan[str(row.get("scan_id"))].append(row)
    for row in goal_rows:
        goal_by_scan[str(row.get("scan_id"))].append(row)

    out: list[dict[str, Any]] = []
    for source_row in sorted(source_ready_rows, key=lambda row: str(row.get("scan_id"))):
        scan_id = str(source_row.get("scan_id"))
        case_path_rows = path_by_scan.get(scan_id, [])
        case_goal_rows = goal_by_scan.get(scan_id, [])
        best_any = min_finite([row.get("best_any_viewpoint_xz_m") for row in case_goal_rows])
        best_goal = min_finite([row.get("best_goal_xz_m") for row in case_goal_rows])
        primary_success_policy_count = sum(1 for row in case_goal_rows if bool(row.get("primary_hit")))
        distance_class = classify_distance(best_any)
        top1_path_ready_count = sum(1 for row in case_path_rows if bool(row.get("top1_path_ready")))
        top5_path_ready_counts = [
            int(row.get("top5_path_ready_rows") or 0)
            for row in case_path_rows
            if row.get("top5_path_ready_rows") is not None
        ]
        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_case_interpretation",
                "adapter_episode_id": source_row.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": source_row.get("scene_key"),
                "object_category": source_row.get("object_category"),
                "source_ready_after_m86_m87": bool(source_row.get("source_ready_after_m86_m87")),
                "m87_candidate_rows": source_row.get("candidate_rows"),
                "m87_path_ready_candidate_rows": source_row.get("path_ready_candidate_rows"),
                "m88_policy_rows": len(case_path_rows),
                "m88_top1_path_ready_policy_rows": top1_path_ready_count,
                "m88_top5_path_ready_rows_max": max(top5_path_ready_counts) if top5_path_ready_counts else 0,
                "m89_policy_rows": len(case_goal_rows),
                "m89_primary_success_policy_count": primary_success_policy_count,
                "best_any_viewpoint_xz_m_min": best_any,
                "best_goal_xz_m_min": best_goal,
                "distance_failure_class": distance_class,
                "source_gap_recovery_supported": primary_success_policy_count > 0,
                "direct_trajectory_promotion_ready": False,
                "recommended_next_action": next_action_for_gap(distance_class),
                "interpretation": (
                    "navmesh/path readiness is not enough because detector candidates do not land near "
                    "the ObjectNav target stop region under the primary proxy metric"
                ),
                "claim_boundary": "M90 interprets M89 proxy rows only; it does not execute Habitat trajectories.",
            }
        )
    return out


def build_result_interpretation_rows(
    m87_coverage: dict[str, Any],
    m88_coverage: dict[str, Any],
    m89_coverage: dict[str, Any],
    aggregate_goal_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    distance_classes = Counter(str(row.get("distance_failure_class")) for row in case_rows)
    rows: list[dict[str, Any]] = [
        {
            "version": VERSION,
            "row_type": "pipeline_interpretation",
            "stage_chain": "M87_navmesh_ready_to_M88_visit_order_ready_to_M89_goal_eval_failed",
            "m87_gate_verdict": m87_coverage.get("gate_verdict"),
            "m87_source_ready_source_gap_case_rows": m87_coverage.get("source_ready_source_gap_case_rows"),
            "m88_path_ready_candidate_rows": m88_coverage.get("path_ready_candidate_rows"),
            "m88_visit_order_rows": m88_coverage.get("visit_order_rows"),
            "m89_primary_success_count_max": m89_coverage.get("primary_success_count_max"),
            "m89_source_gap_proxy_recovery_observed": bool(m89_coverage.get("source_gap_proxy_recovery_observed")),
            "distance_failure_class_counts": dict(distance_classes),
            "interpretation": (
                "The source-gap route passed coordinate/navmesh/path gates, but failed the target-near "
                "goal-evaluation gate. This is a candidate-source/target-coverage failure before a "
                "trajectory-control failure."
            ),
            "supports_policy_ranking_claim": False,
            "supports_candidate_source_claim": False,
            "supports_trajectory_promotion": False,
        }
    ]
    for row in sorted(aggregate_goal_rows, key=lambda item: str(item.get("policy_id"))):
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_interpretation",
                "policy_id": row.get("policy_id"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_success_rows": row.get("primary_success_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
                "interpretation": "policy ordering cannot recover source-gap cases when no candidate is inside the primary target-near radius",
                "supports_policy_ranking_claim": False,
                "direct_trajectory_promotion_ready": False,
            }
        )
    return rows


def build_trajectory_decision_rows(case_rows: list[dict[str, Any]], m89_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    any_success = bool(m89_coverage.get("source_gap_proxy_recovery_observed"))
    all_cases_failed = all(not bool(row.get("source_gap_recovery_supported")) for row in case_rows)
    return [
        {
            "version": VERSION,
            "route_id": "promote_m89_source_gap_detector_policies_to_habitat_trajectory",
            "decision": "reject_now",
            "reason": "M89 has 0/2 primary proxy success for every detector policy, so trajectory execution would mainly measure already-known candidate-source misses.",
            "source_gap_proxy_recovery_observed": any_success,
            "all_source_gap_cases_failed_primary_proxy": all_cases_failed,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        {
            "version": VERSION,
            "route_id": "run_trajectory_for_failure_accounting_only",
            "decision": "defer",
            "reason": "Failure-accounting trajectories are not the bottleneck until candidate-source target coverage is diagnosed.",
            "launch_long_job_now": False,
            "expected_paper_value": "low_before_candidate_source_repair",
        },
        {
            "version": VERSION,
            "route_id": "diagnose_source_gap_candidate_source_failure",
            "decision": "select",
            "reason": "The next useful evidence is whether failures come from target visibility, prompt/category mismatch, coordinate projection, or insufficient observation coverage.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_source_gap_pipeline_gate_negative_result",
            "supported": True,
            "claim_boundary": "M90 supports a negative gate: source-gap detector candidates can pass navmesh/path checks and still fail leakage-safe target-near goal evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M89 primary proxy success is 0/2 for every detector policy, so M90 cannot claim source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M90 rejects trajectory promotion; no new Habitat SR/SPL result is produced.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "Candidate-source coverage is not reliable enough to support a deployable search policy claim.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "The source-gap subset remains two cases and lacks heldout transfer and external navigation/search baselines.",
        },
    ]


def build_route_decision_rows(ready: bool, trajectory_ready: bool) -> list[dict[str, Any]]:
    if not ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m90_inputs_or_interpretation",
                "selected_next_unit": "repair E008-M90 source-gap result interpretation",
                "reason": "M90 inputs are incomplete or M89 is not ready.",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "source_gap_result_interpreted_trajectory_promotion_rejected",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M89 has no source-gap primary proxy recovery, so the next step is target-coverage/candidate-source failure diagnosis rather than trajectory execution.",
            "direct_trajectory_promotion_ready": trajectory_ready,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
) -> str:
    case_lines = []
    for row in case_rows:
        case_lines.append(
            "| {scan_id} | {object_category} | {m87_candidate_rows} | {m87_path_ready_candidate_rows} | "
            "{m89_primary_success_policy_count}/{m89_policy_rows} | {best_any_viewpoint_xz_m_min} | "
            "{distance_failure_class} | {recommended_next_action} |".format(
                scan_id=row.get("scan_id"),
                object_category=row.get("object_category"),
                m87_candidate_rows=row.get("m87_candidate_rows"),
                m87_path_ready_candidate_rows=row.get("m87_path_ready_candidate_rows"),
                m89_primary_success_policy_count=row.get("m89_primary_success_policy_count"),
                m89_policy_rows=row.get("m89_policy_rows"),
                best_any_viewpoint_xz_m_min=fmt(row.get("best_any_viewpoint_xz_m_min")),
                distance_failure_class=row.get("distance_failure_class"),
                recommended_next_action=row.get("recommended_next_action"),
            )
        )
    policy_lines = []
    for row in result_rows:
        if row.get("row_type") != "policy_interpretation":
            continue
        policy_lines.append(
            "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | {best_any_viewpoint_xz_m_mean} |".format(
                policy_id=row.get("policy_id"),
                primary_success_rows=row.get("primary_success_rows"),
                scan_policy_rows=row.get("scan_policy_rows"),
                primary_proxy_sr=fmt(row.get("primary_proxy_sr")),
                primary_spl_proxy_mean=fmt(row.get("primary_spl_proxy_mean")),
                best_any_viewpoint_xz_m_mean=fmt(row.get("best_any_viewpoint_xz_m_mean")),
            )
        )
    selected_route = next((row for row in trajectory_rows if row.get("decision") == "select"), {})
    return f"""# E008-M90 Source-Gap Detector-Goal Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M87 status: `{coverage['m87_status']}`.
- Input M88 status: `{coverage['m88_status']}`.
- Input M89 status: `{coverage['m89_status']}`.
- Source-gap cases: {coverage['source_gap_case_rows']}.
- M87 source-ready source-gap cases: {coverage['m87_source_ready_source_gap_case_rows']}.
- M88 path-ready detector candidates: {coverage['m88_path_ready_candidate_rows']} / {coverage['m88_input_candidate_rows']}.
- M89 candidate-goal eval rows: {coverage['m89_candidate_goal_eval_rows']}.
- M89 primary success count max: {coverage['m89_primary_success_count_max']}.
- Source-gap proxy recovery observed: {coverage['source_gap_proxy_recovery_observed']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Interpretation

| scan_id | category | candidates | path-ready | primary hits | best any-vp XZ m | failure class | next action |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(case_lines)}

## Policy Interpretation

| policy_id | primary hits | proxy SR | proxy SPL | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(policy_lines)}

## Decision

- Trajectory promotion is rejected now because M89 has no primary proxy success for any source-gap case.
- The useful next unit is `{selected_route.get('selected_next_unit')}`.
- This is a candidate-source / target-coverage diagnosis gate, not a final navigation result.

## Claim Boundary

- M90 supports only the negative gate that source-gap detector candidates can pass navmesh/path checks and still fail target-near goal evaluation.
- M90 does not claim source-gap recovery, deployable search policy, real navigation `SR` / `SPL`, or final real RGB-D/open-vocabulary robustness.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m87_coverage = read_json(M87_DIR / "coverage.json")
    m88_coverage = read_json(M88_DIR / "coverage.json")
    m89_coverage = read_json(M89_DIR / "coverage.json")
    source_ready_rows = read_jsonl(M87_DIR / "source_gap_case_source_ready_rows.jsonl")
    path_rows = read_jsonl(M88_DIR / "source_gap_case_policy_metric_rows.jsonl")
    goal_rows = read_jsonl(M89_DIR / "source_gap_case_goal_metric_rows.jsonl")
    policy_goal_rows = read_jsonl(M89_DIR / "policy_goal_metric_rows.jsonl")
    aggregate_goal_rows = [
        row for row in policy_goal_rows if row.get("metric_scope") == "policy_aggregate"
    ]

    input_ready = (
        m87_coverage.get("status") == "e008_m87_source_gap_detector_candidate_navmesh_validation_ready"
        and m88_coverage.get("status") == "e008_m88_source_gap_detector_candidate_visit_order_path_smoke_ready"
        and m89_coverage.get("status") == "e008_m89_source_gap_detector_candidate_goal_evaluation_smoke_ready"
        and bool(source_ready_rows)
        and bool(path_rows)
        and bool(goal_rows)
    )

    case_rows = build_case_interpretation_rows(source_ready_rows, path_rows, goal_rows)
    result_rows = build_result_interpretation_rows(
        m87_coverage,
        m88_coverage,
        m89_coverage,
        aggregate_goal_rows,
        case_rows,
    )
    trajectory_ready = bool(m89_coverage.get("source_gap_proxy_recovery_observed")) and any(
        bool(row.get("source_gap_recovery_supported")) for row in case_rows
    )
    trajectory_rows = build_trajectory_decision_rows(case_rows, m89_coverage)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(input_ready, trajectory_ready)

    distance_counts = Counter(str(row.get("distance_failure_class")) for row in case_rows)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m87_status": m87_coverage.get("status"),
        "m88_status": m88_coverage.get("status"),
        "m89_status": m89_coverage.get("status"),
        "source_gap_case_rows": len(source_ready_rows),
        "case_interpretation_rows": len(case_rows),
        "m87_input_candidate_rows": m87_coverage.get("candidate_rows"),
        "m87_source_ready_source_gap_case_rows": m87_coverage.get("source_ready_source_gap_case_rows"),
        "m88_input_candidate_rows": m88_coverage.get("input_candidate_rows"),
        "m88_path_ready_candidate_rows": m88_coverage.get("path_ready_candidate_rows"),
        "m88_visit_order_rows": m88_coverage.get("visit_order_rows"),
        "m89_candidate_goal_eval_rows": m89_coverage.get("candidate_goal_eval_rows"),
        "m89_primary_success_count_max": m89_coverage.get("primary_success_count_max"),
        "m89_source_gap_case_goal_metric_rows": m89_coverage.get("source_gap_case_goal_metric_rows"),
        "distance_failure_class_counts": dict(sorted(distance_counts.items())),
        "source_gap_proxy_recovery_observed": bool(m89_coverage.get("source_gap_proxy_recovery_observed")),
        "direct_trajectory_promotion_ready": trajectory_ready,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_case_interpretation_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "result_interpretation_rows.jsonl", result_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_decision_rows.jsonl", trajectory_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, result_rows, trajectory_rows),
        encoding="utf-8",
    )

    for name in [
        "coverage.json",
        "source_gap_case_interpretation_rows.jsonl",
        "result_interpretation_rows.jsonl",
        "trajectory_decision_rows.jsonl",
        "claim_boundary_rows.jsonl",
        "route_decision_rows.jsonl",
        "report.md",
    ]:
        shutil.copy2(ARTIFACT_DIR / name, DATA_OUT_DIR / name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
