#!/usr/bin/env python3
"""Close the current E008 source-gap repair route after M101."""

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
M97_DIR = EXP_ROOT / "artifacts" / "E008-M97_coverage_expansion_detector_candidate_source_v0"
M98_DIR = EXP_ROOT / "artifacts" / "E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0"
M100_DIR = EXP_ROOT / "artifacts" / "E008-M100_coverage_expansion_detector_candidate_goal_evaluation_smoke_v0"
M101_DIR = EXP_ROOT / "artifacts" / "E008-M101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0"
)

VERSION = "e008_m102_coverage_expansion_failure_audit_source_gap_repair_closure_v0"
READY_STATUS = "e008_m102_coverage_expansion_failure_audit_source_gap_repair_closure_ready"
BLOCKED_STATUS = "e008_m102_coverage_expansion_failure_audit_source_gap_repair_closure_blocked"
NEXT_UNIT = "E008-M103 alternative proposal-source feasibility and source-gap recovery contract"


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


def pre_cap_count(coverage: dict[str, Any]) -> Any:
    nested = coverage.get("candidate_pool_export")
    if isinstance(nested, dict) and nested.get("candidate_pool_rows") is not None:
        return nested.get("candidate_pool_rows")
    return coverage.get("pre_cap_candidate_rows")


def rows_for_scan(rows: list[dict[str, Any]], scan_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("scan_id")) == scan_id]


def build_case_closure_rows(
    m91_failure_rows: list[dict[str, Any]],
    m94_policy_rows: list[dict[str, Any]],
    m100_scan_rows: list[dict[str, Any]],
    m101_case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m101_by_scan = {str(row.get("scan_id")): row for row in m101_case_rows}
    out: list[dict[str, Any]] = []
    for row in sorted(m91_failure_rows, key=lambda item: str(item.get("scan_id"))):
        scan_id = str(row.get("scan_id"))
        failure_type = str(row.get("dominant_failure_type"))
        pre_cap_best = finite_float(row.get("pre_cap_min_any_viewpoint_xz_m"))
        final_best = finite_float(row.get("best_final_any_viewpoint_xz_m"))
        if failure_type == "observation_or_detector_target_coverage_gap":
            branch_id = "coverage_expansion_branch"
            scan_goal_rows = rows_for_scan(m100_scan_rows, scan_id)
            m101 = m101_by_scan.get(scan_id, {})
            post_best = finite_float(m101.get("m100_best_any_viewpoint_xz_m_min"))
            primary_hits = int(m101.get("m100_primary_success_policy_count") or 0)
            relaxed_hits = int(m101.get("m100_relaxed_success_policy_count") or 0)
            closure_status = "closed_failed_target_coverage_after_expansion"
            closure_reason = (
                "M96-M100 made the coverage-expanded detector route source-ready enough for path rows, "
                "but the closest candidate is still far from every ObjectNav target viewpoint."
            )
            what_learned = (
                "The bottleneck is not path ordering or another same-detector long run; the current "
                "GroundingDINO bbox-depth candidate source does not produce a target-near sofa candidate."
            )
            evidence_rows = len(scan_goal_rows)
        else:
            branch_id = "cap_threshold_rescue_branch"
            scan_policy_rows = rows_for_scan(m94_policy_rows, scan_id)
            post_best = min_finite(scan_policy_rows, "best_any_viewpoint_xz_m")
            primary_hits = sum(1 for item in scan_policy_rows if bool(item.get("primary_any_viewpoint_xz_1p0_hit")))
            relaxed_hits = sum(1 for item in scan_policy_rows if bool(item.get("relaxed_any_viewpoint_xz_1p5_hit")))
            closure_status = "closed_failed_cap_threshold_rescue"
            closure_reason = (
                "M94 tested fixed-order cap/threshold probe rows after the policy order was frozen, "
                "but no probe policy produced primary or relaxed target-near recovery."
            )
            what_learned = (
                "The earlier relaxed pre-cap toilet evidence cannot be promoted by a simple cap/ranking "
                "repair once source readiness, path metadata, and fixed budget constraints are enforced."
            )
            evidence_rows = len(scan_policy_rows)
        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_case_closure",
                "scan_id": scan_id,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "m91_dominant_failure_type": failure_type,
                "m91_dropped_stage": row.get("dropped_stage"),
                "m91_pre_cap_candidate_rows": row.get("pre_cap_candidate_rows"),
                "m91_pre_cap_any_viewpoint_1p0_hits": row.get("pre_cap_any_viewpoint_1p0_hits"),
                "m91_pre_cap_any_viewpoint_1p5_hits": row.get("pre_cap_any_viewpoint_1p5_hits"),
                "m91_pre_cap_min_any_viewpoint_xz_m": pre_cap_best,
                "m91_final_candidate_rows": row.get("final_candidate_rows"),
                "m91_final_best_any_viewpoint_xz_m": final_best,
                "assigned_repair_branch": branch_id,
                "repair_branch_status": closure_status,
                "post_repair_evidence_rows": evidence_rows,
                "post_repair_primary_hit_rows": primary_hits,
                "post_repair_relaxed_hit_rows": relaxed_hits,
                "post_repair_best_any_viewpoint_xz_m": post_best,
                "post_repair_delta_vs_m91_pre_cap_best_m": (
                    post_best - pre_cap_best if post_best is not None and pre_cap_best is not None else None
                ),
                "source_gap_recovery_supported": False,
                "trajectory_promotion_ready": False,
                "closure_reason": closure_reason,
                "what_we_learned": what_learned,
                "claim_boundary": "M102 closes the current source-gap repair route; it does not create new detector or trajectory evidence.",
            }
        )
    return out


def build_failure_mechanism_rows(
    m91_coverage: dict[str, Any],
    m97_coverage: dict[str, Any],
    m98_coverage: dict[str, Any],
    m100_coverage: dict[str, Any],
    m101_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "mechanism_id": "target_near_candidate_absent_even_pre_cap",
            "severity": "blocking_for_current_detector_route",
            "evidence": (
                f"M91 found {m91_coverage.get('cases_with_pre_cap_primary_hit')} source-gap cases with "
                "pre-cap primary target-near hits and only one relaxed hit; the sofa case remained far even before caps."
            ),
            "method_implication": "A ranking-only repair cannot recover a candidate that was never generated near the target.",
        },
        {
            "version": VERSION,
            "mechanism_id": "same_detector_coverage_expansion_not_sufficient",
            "severity": "blocking_for_more_same_route_long_jobs",
            "evidence": (
                f"M97 wrote {m97_coverage.get('prediction_rows')} final proposals from "
                f"{pre_cap_count(m97_coverage)} pre-cap candidates, "
                f"but M100 primary success stayed {m100_coverage.get('primary_success_count_max')}."
            ),
            "method_implication": "More coverage under the same bbox-depth proposal principle has low expected value without a new failure-specific change.",
        },
        {
            "version": VERSION,
            "mechanism_id": "source_reachability_filters_out_high_confidence_candidates",
            "severity": "diagnostic",
            "evidence": (
                f"M98 path-ready candidates are {m98_coverage.get('source_to_snapped_path_found_rows')} / "
                f"{m98_coverage.get('candidate_rows')}; {m98_coverage.get('candidate_rows', 0) - m98_coverage.get('source_to_snapped_path_found_rows', 0)} "
                "candidates are unreachable from the episode source."
            ),
            "method_implication": "Navigation evidence must keep source-ready/source-gap accounting separate from detector score ordering.",
        },
        {
            "version": VERSION,
            "mechanism_id": "policy_order_not_primary_bottleneck",
            "severity": "blocking_for_trajectory_promotion",
            "evidence": (
                "M100 evaluates four fixed policies and all have 0/1 primary proxy success; "
                f"M101 records current two-branch repair route failed = {m101_coverage.get('current_two_branch_repair_route_failed')}."
            ),
            "method_implication": "Executing trajectories would measure a known candidate-source miss, not a policy improvement.",
        },
    ]


def build_repair_route_closure_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "trajectory_execution_now",
            "closure_status": "closed_rejected",
            "reason": "Leakage-safe goal evaluation has no source-gap proxy recovery, so trajectory execution would not test a recoverable navigation policy.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "cap_threshold_rescue_branch",
            "closure_status": "closed_negative",
            "reason": "M94 cap probe rows have 0 primary and 0 relaxed supported policy rows.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "coverage_expansion_branch",
            "closure_status": "closed_negative",
            "reason": "M100 coverage expansion has 0/1 primary success and M101 classifies the remaining case as severe candidate-source coverage gap.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "more_groundingdino_bbox_depth_coverage_jobs",
            "closure_status": "closed_until_new_principle",
            "reason": "The same detector/source principle already produced 96 rendered frames and 853 pre-cap candidates for the remaining case without target-near recovery.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "current_two_branch_source_gap_repair_route",
            "closure_status": "closed_failed",
            "reason": "Both designed branches failed under fixed-order, leakage-safe evaluation.",
            "launch_long_job_now": False,
        },
    ]


def build_next_route_option_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "same_detector_more_render_or_lower_threshold",
            "decision": "reject_now",
            "reason": "M102 closes this because it does not change the candidate-source principle that failed in M91-M101.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "execute_negative_coverage_expansion_trajectory",
            "decision": "reject_now",
            "reason": "M100 has no primary proxy recovery, so the trajectory run would be low-value negative confirmation.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "alternative_proposal_source_feasibility_gate",
            "decision": "select",
            "reason": (
                "The next useful unit is a contract-level feasibility gate for a different candidate-source principle, "
                "not another long GroundingDINO bbox-depth rerun."
            ),
            "candidate_routes": [
                "ConceptGraphs-derived map candidates",
                "OpenMask3D 3D instance proposal route if environment blocker is worth revisiting",
                "HOV-SG or other map-navigation baseline after source/runtime audit",
                "HM3D semantic/source upper-bound for ceiling diagnosis only",
            ],
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "package_diagnostic_navigation_boundary_for_paper",
            "decision": "keep_as_parallel_writeup_boundary",
            "reason": "M102 supports a strong reviewer-defense boundary table, but it is not enough for final navigation SR/SPL claims.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_current_detector_source_gap_repair_failed",
            "supported": True,
            "claim_boundary": "The current GroundingDINO bbox-depth two-branch source-gap repair route failed under fixed-order, leakage-safe evaluation.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_need_candidate_source_principle_change",
            "supported": True,
            "claim_boundary": "M102 supports changing candidate-source principle before additional long jobs, because both ranking/cap and coverage-expansion branches failed.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "No M91-M101 branch produces primary source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M102 rejects trajectory promotion and produces no Habitat trajectory result.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M102 is a failure closure package over a small source-gap subset, not heldout robustness evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M102 is about candidate-source failure, not human-intent or task-context specificity.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not just run more coverage frames?",
            "answer": "M96-M100 already renders and evaluates the designed coverage branch; M100 still has 0/1 primary success and best any-viewpoint XZ 5.484739m.",
            "evidence_source": "M96-M101",
        },
        {
            "version": VERSION,
            "question": "Why not just lower the cap or threshold?",
            "answer": "M94 cap-threshold probe has 0 primary and 0 relaxed supported policy rows after fixed-order evaluation.",
            "evidence_source": "M94",
        },
        {
            "version": VERSION,
            "question": "Why is this still useful if it is negative?",
            "answer": "It isolates the current bottleneck as candidate-source generation rather than path ranking, memory trust, or trajectory execution.",
            "evidence_source": "M91-M102",
        },
        {
            "version": VERSION,
            "question": "Can this be a top-tier navigation claim?",
            "answer": "No. It is a reviewer-defense boundary and route-selection result; final navigation needs a positive alternative proposal source plus trajectory/baseline evidence.",
            "evidence_source": "M102 claim boundary",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| {scan_id} | {object_category} | {m91_dominant_failure_type} | {assigned_repair_branch} | "
        "{m91_pre_cap_min_any_viewpoint_xz_m} | {post_repair_best_any_viewpoint_xz_m} | {post_repair_primary_hit_rows} | {repair_branch_status} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m91_dominant_failure_type=row.get("m91_dominant_failure_type"),
            assigned_repair_branch=row.get("assigned_repair_branch"),
            m91_pre_cap_min_any_viewpoint_xz_m=fmt(row.get("m91_pre_cap_min_any_viewpoint_xz_m")),
            post_repair_best_any_viewpoint_xz_m=fmt(row.get("post_repair_best_any_viewpoint_xz_m")),
            post_repair_primary_hit_rows=row.get("post_repair_primary_hit_rows"),
            repair_branch_status=row.get("repair_branch_status"),
        )
        for row in case_rows
    ]
    mechanism_lines = [
        "| {mechanism_id} | {severity} | {method_implication} |".format(
            mechanism_id=row.get("mechanism_id"),
            severity=row.get("severity"),
            method_implication=row.get("method_implication"),
        )
        for row in mechanism_rows
    ]
    route_lines = [
        "| {route_id} | {closure_status} | {reason} |".format(
            route_id=row.get("route_id"),
            closure_status=row.get("closure_status"),
            reason=row.get("reason"),
        )
        for row in route_rows
    ]
    next_lines = [
        "| {route_id} | {decision} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            reason=row.get("reason"),
        )
        for row in next_rows
    ]
    return f"""# E008-M102 Coverage-Expansion Failure Audit / Source-Gap Closure

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M91 status: `{coverage['m91_status']}`.
- Input M94 status: `{coverage['m94_status']}`.
- Input M100 status: `{coverage['m100_status']}`.
- Input M101 status: `{coverage['m101_status']}`.
- Source-gap case rows: {coverage['source_gap_case_rows']}.
- Closed source-gap case rows: {coverage['closed_source_gap_case_rows']}.
- Current detector repair route closed: {coverage['current_detector_source_gap_repair_route_closed']}.
- Source-gap recovery supported: {coverage['source_gap_recovery_supported']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Additional long job recommended now: {coverage['additional_long_job_recommended_now']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Closure

| scan_id | category | M91 failure type | branch | M91 pre-cap best m | post-repair best m | primary hits | status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
{chr(10).join(case_lines)}

## Failure Mechanisms

| mechanism | severity | method implication |
| --- | --- | --- |
{chr(10).join(mechanism_lines)}

## Closed Routes

| route | status | reason |
| --- | --- | --- |
{chr(10).join(route_lines)}

## Next Route Options

| route | decision | reason |
| --- | --- | --- |
{chr(10).join(next_lines)}

## Claim Boundary

- M102 supports a negative, reviewer-facing closure: the current `GroundingDINO` bbox-depth two-branch source-gap repair route failed.
- M102 supports changing the candidate-source principle before more long detector/render jobs.
- M102 does not support source-gap recovery, deployable policy, real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human-intent contribution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m91_coverage = read_json(M91_DIR / "coverage.json")
    m94_coverage = read_json(M94_DIR / "coverage.json")
    m97_coverage = read_json(M97_DIR / "e008_m97_verification_coverage.json")
    m98_coverage = read_json(M98_DIR / "coverage.json")
    m100_coverage = read_json(M100_DIR / "coverage.json")
    m101_coverage = read_json(M101_DIR / "coverage.json")
    m91_failure_rows = read_jsonl(M91_DIR / "source_gap_failure_diagnosis_rows.jsonl")
    m94_policy_rows = read_jsonl(M94_DIR / "cap_probe_policy_metric_rows.jsonl")
    m100_policy_rows = read_jsonl(M100_DIR / "policy_goal_metric_rows.jsonl")
    m100_scan_rows = [row for row in m100_policy_rows if row.get("metric_scope") == "scan_policy"]
    m101_case_rows = read_jsonl(M101_DIR / "coverage_expansion_case_interpretation_rows.jsonl")

    input_ready = (
        m91_coverage.get("status") == "e008_m91_source_gap_target_coverage_candidate_source_failure_diagnosis_ready"
        and m94_coverage.get("status") == "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_ready"
        and m100_coverage.get("status") == "e008_m100_coverage_expansion_detector_candidate_goal_evaluation_smoke_ready"
        and m101_coverage.get("status")
        == "e008_m101_coverage_expansion_detector_goal_result_interpretation_trajectory_decision_ready"
        and bool(m91_failure_rows)
    )

    case_rows = build_case_closure_rows(m91_failure_rows, m94_policy_rows, m100_scan_rows, m101_case_rows)
    mechanism_rows = build_failure_mechanism_rows(m91_coverage, m97_coverage, m98_coverage, m100_coverage, m101_coverage)
    closure_rows = build_repair_route_closure_rows()
    next_rows = build_next_route_option_rows()
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    failure_type_counts = Counter(str(row.get("m91_dominant_failure_type")) for row in case_rows)
    branch_counts = Counter(str(row.get("assigned_repair_branch")) for row in case_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m91_status": m91_coverage.get("status"),
        "m94_status": m94_coverage.get("status"),
        "m97_status": m97_coverage.get("status"),
        "m98_status": m98_coverage.get("status"),
        "m100_status": m100_coverage.get("status"),
        "m101_status": m101_coverage.get("status"),
        "source_gap_case_rows": len(m91_failure_rows),
        "closed_source_gap_case_rows": len(case_rows),
        "case_failure_type_counts": dict(sorted(failure_type_counts.items())),
        "case_repair_branch_counts": dict(sorted(branch_counts.items())),
        "m94_cap_primary_supported_policy_rows": m94_coverage.get("cap_primary_supported_policy_rows"),
        "m94_cap_relaxed_supported_policy_rows": m94_coverage.get("cap_relaxed_supported_policy_rows"),
        "m97_prediction_rows": m97_coverage.get("prediction_rows"),
        "m97_pre_cap_candidate_rows": pre_cap_count(m97_coverage),
        "m98_path_ready_candidate_rows": m98_coverage.get("source_to_snapped_path_found_rows"),
        "m98_candidate_rows": m98_coverage.get("candidate_rows"),
        "m100_primary_success_count_max": m100_coverage.get("primary_success_count_max"),
        "m101_current_two_branch_repair_route_failed": m101_coverage.get("current_two_branch_repair_route_failed"),
        "current_detector_source_gap_repair_route_closed": True,
        "current_detector_source_gap_repair_route_closure_reason": "both designed current-detector branches failed under leakage-safe fixed-order evaluation",
        "source_gap_recovery_supported": False,
        "direct_trajectory_promotion_ready": False,
        "additional_long_job_recommended_now": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    output_files = {
        "coverage.json": coverage,
        "source_gap_case_closure_rows.jsonl": case_rows,
        "failure_mechanism_rows.jsonl": mechanism_rows,
        "repair_route_closure_rows.jsonl": closure_rows,
        "next_route_option_rows.jsonl": next_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "reviewer_defense_rows.jsonl": reviewer_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)  # type: ignore[arg-type]
        else:
            write_json(ARTIFACT_DIR / name, payload)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, mechanism_rows, closure_rows, next_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
