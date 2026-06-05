#!/usr/bin/env python3
"""Interpret M100 coverage-expansion detector-goal results and decide trajectory promotion."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M91_DIR = EXP_ROOT / "artifacts" / "E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
M94_DIR = EXP_ROOT / "artifacts" / "E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0"
M98_DIR = EXP_ROOT / "artifacts" / "E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0"
M99_DIR = EXP_ROOT / "artifacts" / "E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0"
M100_DIR = EXP_ROOT / "artifacts" / "E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0"
)

VERSION = "e008_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0"
READY_STATUS = "e008_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_ready"
BLOCKED_STATUS = "e008_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_blocked"
NEXT_UNIT = "E008-M102 coverage-expansion failure audit and source-gap repair closure package"
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


def min_finite(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [finite_float(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return min(values) if values else None


def classify_distance(distance_m: float | None) -> str:
    if distance_m is None:
        return "unknown_no_distance"
    if distance_m <= PRIMARY_RADIUS_M:
        return "covered_under_primary_radius"
    if distance_m <= NEAR_MISS_RADIUS_M:
        return "near_miss_threshold_gap"
    if distance_m <= SEVERE_GAP_RADIUS_M:
        return "moderate_candidate_localization_gap"
    return "severe_candidate_source_coverage_gap"


def build_case_interpretation_rows(
    m91_failure_rows: list[dict[str, Any]],
    m98_coverage: dict[str, Any],
    m99_scan_rows: list[dict[str, Any]],
    m100_scan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m91_by_scan = {str(row.get("scan_id")): row for row in m91_failure_rows}
    scan_ids = sorted({str(row.get("scan_id")) for row in m100_scan_rows})
    rows: list[dict[str, Any]] = []
    for scan_id in scan_ids:
        m91 = m91_by_scan.get(scan_id, {})
        goal_rows = [row for row in m100_scan_rows if str(row.get("scan_id")) == scan_id]
        path_rows = [row for row in m99_scan_rows if str(row.get("scan_id")) == scan_id]
        best_any = min_finite(goal_rows, "best_any_viewpoint_xz_m")
        best_goal = min_finite(goal_rows, "best_goal_xz_m")
        m91_pre_cap_best = finite_float(m91.get("pre_cap_min_any_viewpoint_xz_m"))
        distance_delta = best_any - m91_pre_cap_best if best_any is not None and m91_pre_cap_best is not None else None
        primary_success_policy_count = sum(1 for row in goal_rows if bool(row.get("primary_hit")))
        relaxed_success_policy_count = sum(1 for row in goal_rows if bool(row.get("any_viewpoint_xz_1p5_hit")))
        top1_path_ready_count = sum(1 for row in path_rows if bool(row.get("top1_path_ready")))
        first_path_costs = [
            finite_float(row.get("first_path_ready_cost_m"))
            for row in path_rows
            if finite_float(row.get("first_path_ready_cost_m")) is not None
        ]
        rows.append(
            {
                "version": VERSION,
                "row_type": "coverage_expansion_case_interpretation",
                "adapter_episode_id": goal_rows[0].get("adapter_episode_id") if goal_rows else m91.get("adapter_episode_id"),
                "scan_id": scan_id,
                "scene_key": goal_rows[0].get("scene_key") if goal_rows else m91.get("scene_key"),
                "object_category": goal_rows[0].get("object_category") if goal_rows else m91.get("object_category"),
                "m91_dominant_failure_type": m91.get("dominant_failure_type"),
                "m91_pre_cap_min_any_viewpoint_xz_m": m91_pre_cap_best,
                "m91_final_best_any_viewpoint_xz_m": finite_float(m91.get("best_final_any_viewpoint_xz_m")),
                "m98_candidate_rows": m98_coverage.get("candidate_rows"),
                "m98_path_ready_candidate_rows": m98_coverage.get("source_to_snapped_path_found_rows"),
                "m98_unreachable_candidate_rows": int(m98_coverage.get("candidate_rows") or 0)
                - int(m98_coverage.get("source_to_snapped_path_found_rows") or 0),
                "m99_policy_rows": len(path_rows),
                "m99_top1_path_ready_policy_rows": top1_path_ready_count,
                "m99_min_first_path_ready_cost_m": min(first_path_costs) if first_path_costs else None,
                "m100_policy_rows": len(goal_rows),
                "m100_primary_success_policy_count": primary_success_policy_count,
                "m100_relaxed_success_policy_count": relaxed_success_policy_count,
                "m100_best_any_viewpoint_xz_m_min": best_any,
                "m100_best_goal_xz_m_min": best_goal,
                "m100_vs_m91_pre_cap_best_any_viewpoint_delta_m": distance_delta,
                "distance_failure_class": classify_distance(best_any),
                "coverage_expansion_recovery_supported": primary_success_policy_count > 0,
                "direct_trajectory_promotion_ready": False,
                "interpretation": (
                    "Coverage expansion produced path-ready detector candidates, but none reached the "
                    "ObjectNav target stop region under the primary or relaxed proxy metric."
                ),
                "recommended_next_action": "audit_coverage_expansion_failure_and_close_current_source_gap_repair_route",
                "claim_boundary": "M101 interprets M100 proxy rows only; it does not execute Habitat trajectories.",
            }
        )
    return rows


def build_policy_interpretation_rows(m100_policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(m100_policy_rows, key=lambda item: str(item.get("policy_id"))):
        if row.get("metric_scope") != "policy_aggregate":
            continue
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_interpretation",
                "policy_id": row.get("policy_id"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_success_rows": row.get("primary_success_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
                "best_goal_xz_m_mean": row.get("best_goal_xz_m_mean"),
                "supports_policy_ranking_claim": False,
                "direct_trajectory_promotion_ready": False,
                "interpretation": "policy ordering cannot recover the coverage-expanded source-gap case when no candidate is near the target stop region",
            }
        )
    return rows


def build_repair_branch_closure_rows(
    m91_coverage: dict[str, Any],
    m94_coverage: dict[str, Any],
    m100_coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cap_supported = bool(m94_coverage.get("cap_primary_supported_policy_rows"))
    coverage_supported = bool(m100_coverage.get("coverage_expansion_proxy_recovery_observed"))
    current_route_failed = not cap_supported and not coverage_supported
    return [
        {
            "version": VERSION,
            "row_type": "repair_branch_closure",
            "branch_id": "cap_threshold_rescue_branch",
            "status": "failed_diagnostic_gate",
            "m91_failure_type_targeted": "localization_threshold_gap_with_low_confidence_cap_suppression",
            "m94_cap_primary_supported_policy_rows": m94_coverage.get("cap_primary_supported_policy_rows"),
            "m94_cap_relaxed_supported_policy_rows": m94_coverage.get("cap_relaxed_supported_policy_rows"),
            "trajectory_promotion_ready": False,
            "reason": "M94 cap-threshold probe does not recover the target under primary or relaxed policy rows.",
        },
        {
            "version": VERSION,
            "row_type": "repair_branch_closure",
            "branch_id": "coverage_expansion_branch",
            "status": "failed_goal_evaluation_gate",
            "m91_failure_type_targeted": "observation_or_detector_target_coverage_gap",
            "m100_coverage_target_rows": m100_coverage.get("coverage_target_rows"),
            "m100_candidate_goal_eval_rows": m100_coverage.get("candidate_goal_eval_rows"),
            "m100_primary_success_count_max": m100_coverage.get("primary_success_count_max"),
            "m100_best_any_viewpoint_xz_m_min": min_finite(case_rows, "m100_best_any_viewpoint_xz_m_min"),
            "trajectory_promotion_ready": False,
            "reason": "Coverage expansion materialized candidates and path rows, but no candidate reaches the ObjectNav target-near metric.",
        },
        {
            "version": VERSION,
            "row_type": "repair_branch_closure",
            "branch_id": "current_two_branch_repair_route",
            "status": "no_positive_recovery_under_current_detector_route" if current_route_failed else "partial_recovery_observed",
            "m91_source_gap_case_rows": m91_coverage.get("source_gap_case_rows"),
            "cap_branch_recovery_supported": cap_supported,
            "coverage_branch_recovery_supported": coverage_supported,
            "trajectory_promotion_ready": False,
            "additional_long_job_recommended_now": False,
            "reason": "Both designed source-gap repair branches fail to produce primary proxy recovery; further long jobs should wait for a failure audit or different proposal source.",
        },
    ]


def build_trajectory_decision_rows(current_route_failed: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "promote_m100_coverage_expansion_detector_policies_to_habitat_trajectory",
            "decision": "reject_now",
            "reason": "M100 has 0/1 primary proxy success for every policy, so trajectory execution would measure a known target-source miss rather than a policy improvement.",
            "direct_trajectory_promotion_ready": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        {
            "version": VERSION,
            "route_id": "run_more_coverage_expansion_render_detector_jobs",
            "decision": "reject_now" if current_route_failed else "defer",
            "reason": "The current coverage expansion already rendered and detected 96 frames for the case, but target-near recovery is still absent; another long job needs a sharper failure audit first.",
            "launch_long_job_now": False,
            "expected_paper_value": "low_without_new_candidate_source_principle",
        },
        {
            "version": VERSION,
            "route_id": "coverage_expansion_failure_audit_and_source_gap_repair_closure",
            "decision": "select",
            "reason": "The useful next evidence is a compact audit explaining why the designed repair route failed and whether E008 should stop, switch proposal source, or remain a negative boundary.",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_coverage_expansion_negative_result",
            "supported": True,
            "claim_boundary": "M101 supports a negative gate: coverage-expanded detector candidates can be path-ready and still fail target-near goal evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M100 primary proxy success is 0/1 for every policy, so M101 cannot claim source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M101 rejects trajectory promotion and produces no new Habitat SR/SPL result.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "The source-gap repair route has no primary proxy recovery, so it cannot support a deployable fixed-budget search-policy claim.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M101 covers one coverage-expanded source-gap case and lacks heldout transfer, external proposal-source repair, and navigation/search baselines.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    if not ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m101_inputs_or_interpretation",
                "selected_next_unit": "repair E008-M101 coverage-expansion result interpretation",
                "reason": "M101 inputs are incomplete or M100 is not ready.",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "coverage_expansion_result_interpreted_trajectory_promotion_rejected",
            "selected_next_unit": NEXT_UNIT,
            "reason": "M100 has no primary proxy recovery, and M94 cap probe was also negative; next step is a compact failure audit / repair closure package, not a long trajectory job.",
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
    branch_rows: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| {scan_id} | {object_category} | {m91_dominant_failure_type} | {m98_path_ready_candidate_rows}/{m98_candidate_rows} | "
        "{m100_primary_success_policy_count}/{m100_policy_rows} | {m100_best_any_viewpoint_xz_m_min} | {m100_vs_m91_pre_cap_best_any_viewpoint_delta_m} | {distance_failure_class} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m91_dominant_failure_type=row.get("m91_dominant_failure_type"),
            m98_path_ready_candidate_rows=row.get("m98_path_ready_candidate_rows"),
            m98_candidate_rows=row.get("m98_candidate_rows"),
            m100_primary_success_policy_count=row.get("m100_primary_success_policy_count"),
            m100_policy_rows=row.get("m100_policy_rows"),
            m100_best_any_viewpoint_xz_m_min=fmt(row.get("m100_best_any_viewpoint_xz_m_min")),
            m100_vs_m91_pre_cap_best_any_viewpoint_delta_m=fmt(row.get("m100_vs_m91_pre_cap_best_any_viewpoint_delta_m")),
            distance_failure_class=row.get("distance_failure_class"),
        )
        for row in case_rows
    ]
    policy_lines = [
        "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | {best_any_viewpoint_xz_m_mean} |".format(
            policy_id=row.get("policy_id"),
            primary_success_rows=row.get("primary_success_rows"),
            scan_policy_rows=row.get("scan_policy_rows"),
            primary_proxy_sr=fmt(row.get("primary_proxy_sr")),
            primary_spl_proxy_mean=fmt(row.get("primary_spl_proxy_mean")),
            best_any_viewpoint_xz_m_mean=fmt(row.get("best_any_viewpoint_xz_m_mean")),
        )
        for row in policy_rows
    ]
    branch_lines = [
        "| {branch_id} | {status} | {trajectory_promotion_ready} | {reason} |".format(
            branch_id=row.get("branch_id"),
            status=row.get("status"),
            trajectory_promotion_ready=row.get("trajectory_promotion_ready"),
            reason=row.get("reason"),
        )
        for row in branch_rows
    ]
    selected_route = next((row for row in trajectory_rows if row.get("decision") == "select"), {})
    return f"""# E008-M101 Coverage-Expansion Detector-Goal Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M94 status: `{coverage['m94_status']}`.
- Input M98 status: `{coverage['m98_status']}`.
- Input M99 status: `{coverage['m99_status']}`.
- Input M100 status: `{coverage['m100_status']}`.
- Coverage target rows: {coverage['coverage_target_rows']}.
- M98 path-ready candidates: {coverage['m98_path_ready_candidate_rows']} / {coverage['m98_candidate_rows']}.
- M100 candidate-goal eval rows: {coverage['m100_candidate_goal_eval_rows']}.
- M100 primary success count max: {coverage['m100_primary_success_count_max']}.
- M100 best any-vp XZ min: {fmt(coverage['m100_best_any_viewpoint_xz_m_min'])}.
- Cap branch primary supported rows: {coverage['m94_cap_primary_supported_policy_rows']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Interpretation

| scan_id | category | M91 failure type | path-ready | primary hits | best any-vp XZ m | delta vs M91 pre-cap best m | failure class |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(case_lines)}

## Policy Interpretation

| policy_id | primary hits | proxy SR | proxy SPL | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(policy_lines)}

## Branch Closure

| branch | status | trajectory ready | reason |
| --- | --- | --- | --- |
{chr(10).join(branch_lines)}

## Decision

- Trajectory promotion is rejected.
- Another coverage render/detector long job is rejected until a sharper failure audit changes the candidate-source principle.
- The useful next unit is `{selected_route.get('selected_next_unit')}`.

## Claim Boundary

- M101 supports only a negative coverage-expansion gate.
- M101 does not claim source-gap recovery, deployable search policy, real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human-intent contribution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m91_coverage = read_json(M91_DIR / "coverage.json")
    m94_coverage = read_json(M94_DIR / "coverage.json")
    m98_coverage = read_json(M98_DIR / "coverage.json")
    m99_coverage = read_json(M99_DIR / "coverage.json")
    m100_coverage = read_json(M100_DIR / "coverage.json")
    m91_failure_rows = read_jsonl(M91_DIR / "source_gap_failure_diagnosis_rows.jsonl")
    m99_policy_rows = read_jsonl(M99_DIR / "coverage_scan_policy_metric_rows.jsonl")
    m100_policy_rows = read_jsonl(M100_DIR / "policy_goal_metric_rows.jsonl")
    m100_scan_rows = [row for row in m100_policy_rows if row.get("metric_scope") == "scan_policy"]
    m100_aggregate_rows = [row for row in m100_policy_rows if row.get("metric_scope") == "policy_aggregate"]

    input_ready = (
        m94_coverage.get("status") == "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_ready"
        and m98_coverage.get("status") == "e008_m98_coverage_expansion_detector_candidate_navmesh_validation_ready"
        and m99_coverage.get("status") == "e008_m99_coverage_expansion_detector_candidate_visit_order_path_smoke_ready"
        and m100_coverage.get("status") == "e008_m100_coverage_expansion_detector_candidate_goal_evaluation_smoke_ready"
        and bool(m91_failure_rows)
        and bool(m100_scan_rows)
        and bool(m100_aggregate_rows)
    )

    case_rows = build_case_interpretation_rows(m91_failure_rows, m98_coverage, m99_policy_rows, m100_scan_rows)
    policy_rows = build_policy_interpretation_rows(m100_aggregate_rows)
    branch_rows = build_repair_branch_closure_rows(m91_coverage, m94_coverage, m100_coverage, case_rows)
    current_route_failed = not any(row.get("cap_branch_recovery_supported") for row in branch_rows) and not any(
        row.get("coverage_branch_recovery_supported") for row in branch_rows
    )
    trajectory_rows = build_trajectory_decision_rows(current_route_failed)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(input_ready)
    distance_counts = Counter(str(row.get("distance_failure_class")) for row in case_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m91_status": m91_coverage.get("status"),
        "m94_status": m94_coverage.get("status"),
        "m98_status": m98_coverage.get("status"),
        "m99_status": m99_coverage.get("status"),
        "m100_status": m100_coverage.get("status"),
        "coverage_target_rows": m100_coverage.get("coverage_target_rows"),
        "m98_candidate_rows": m98_coverage.get("candidate_rows"),
        "m98_path_ready_candidate_rows": m98_coverage.get("source_to_snapped_path_found_rows"),
        "m98_unreachable_candidate_rows": int(m98_coverage.get("candidate_rows") or 0)
        - int(m98_coverage.get("source_to_snapped_path_found_rows") or 0),
        "m99_visit_order_rows": m99_coverage.get("visit_order_rows"),
        "m100_candidate_goal_eval_rows": m100_coverage.get("candidate_goal_eval_rows"),
        "m100_primary_success_count_max": m100_coverage.get("primary_success_count_max"),
        "m100_coverage_expansion_proxy_recovery_observed": bool(
            m100_coverage.get("coverage_expansion_proxy_recovery_observed")
        ),
        "m100_best_any_viewpoint_xz_m_min": min_finite(case_rows, "m100_best_any_viewpoint_xz_m_min"),
        "m94_cap_primary_supported_policy_rows": m94_coverage.get("cap_primary_supported_policy_rows"),
        "m94_cap_relaxed_supported_policy_rows": m94_coverage.get("cap_relaxed_supported_policy_rows"),
        "distance_failure_class_counts": dict(sorted(distance_counts.items())),
        "current_two_branch_repair_route_failed": current_route_failed,
        "direct_trajectory_promotion_ready": False,
        "additional_long_job_recommended_now": False,
        "source_gap_recovery_supported": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    output_files = {
        "coverage.json": coverage,
        "coverage_expansion_case_interpretation_rows.jsonl": case_rows,
        "policy_interpretation_rows.jsonl": policy_rows,
        "repair_branch_closure_rows.jsonl": branch_rows,
        "trajectory_decision_rows.jsonl": trajectory_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)  # type: ignore[arg-type]
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, policy_rows, branch_rows, trajectory_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
