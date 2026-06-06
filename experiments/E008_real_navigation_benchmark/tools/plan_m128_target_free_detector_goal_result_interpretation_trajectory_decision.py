#!/usr/bin/env python3
"""Interpret M127 target-free detector-goal results and decide trajectory promotion."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M125_DIR = EXP_ROOT / "artifacts" / "E008-M125_target_free_detector_candidate_navmesh_validation_v0"
M126_DIR = EXP_ROOT / "artifacts" / "E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0"
M127_DIR = EXP_ROOT / "artifacts" / "E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M128_target_free_detector_goal_result_interpretation_trajectory_decision_v0"
)

VERSION = "e008_m128_target_free_detector_goal_result_interpretation_trajectory_decision_v0"
READY_STATUS = "e008_m128_target_free_detector_goal_result_interpretation_trajectory_decision_ready"
BLOCKED_STATUS = "e008_m128_target_free_detector_goal_result_interpretation_trajectory_decision_blocked"
NEXT_UNIT = "E008-M129 target-free detector-policy trajectory execution contract and Docker preflight"

REFERENCE_POLICY = "detector_confidence_reachable_subset_v0"


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


def delta(value: object, base: object) -> float | None:
    value_f = finite_float(value)
    base_f = finite_float(base)
    if value_f is None or base_f is None:
        return None
    return value_f - base_f


def aggregate_goal_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def build_case_interpretation_rows(
    m125_coverage: dict[str, Any],
    m126_coverage: dict[str, Any],
    scan_goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not scan_goal_rows:
        return []

    sample = scan_goal_rows[0]
    primary_hits = sum(1 for row in scan_goal_rows if bool(row.get("primary_hit")))
    goal_hits = sum(1 for row in scan_goal_rows if bool(row.get("goal_xz_1p0_hit")))
    best_any = min(
        value
        for value in (finite_float(row.get("best_any_viewpoint_xz_m")) for row in scan_goal_rows)
        if value is not None
    )
    best_goal = min(
        value for value in (finite_float(row.get("best_goal_xz_m")) for row in scan_goal_rows) if value is not None
    )
    min_hit_cost = min(
        value
        for value in (finite_float(row.get("primary_first_hit_cost_m")) for row in scan_goal_rows)
        if value is not None
    )
    if primary_hits and not goal_hits:
        result_class = "target_viewpoint_proxy_recovered_goal_center_miss"
    elif primary_hits:
        result_class = "target_viewpoint_and_goal_center_proxy_recovered"
    else:
        result_class = "target_viewpoint_proxy_not_recovered"

    return [
        {
            "version": VERSION,
            "row_type": "target_free_case_interpretation",
            "adapter_episode_id": sample.get("adapter_episode_id"),
            "scan_id": sample.get("scan_id"),
            "scene_key": sample.get("scene_key"),
            "object_category": sample.get("object_category"),
            "m125_candidate_rows": m125_coverage.get("candidate_rows"),
            "m125_path_ready_candidate_rows": m125_coverage.get("source_to_snapped_path_found_rows"),
            "m126_visit_order_rows": m126_coverage.get("visit_order_rows"),
            "m127_policy_rows": len(scan_goal_rows),
            "m127_primary_success_policy_count": primary_hits,
            "m127_goal_xz_1p0_success_policy_count": goal_hits,
            "m127_best_any_viewpoint_xz_m_min": best_any,
            "m127_best_goal_xz_m_min": best_goal,
            "m127_min_primary_first_hit_cost_m": min_hit_cost,
            "target_free_result_class": result_class,
            "target_free_proxy_recovery_supported": primary_hits > 0,
            "trajectory_contract_promotion_ready": primary_hits > 0,
            "direct_long_job_launch_now": False,
            "interpretation": (
                "Target-free observation expansion produced path-ready detector candidates close enough to "
                "an ObjectNav eval viewpoint under the frozen post-policy metric, but the goal-center metric "
                "still misses and the denominator is one case."
            ),
            "claim_boundary": "M128 interprets M127 proxy rows only; it does not execute Habitat trajectories.",
        }
    ]


def build_policy_interpretation_rows(goal_policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy = {str(row.get("policy_id")): row for row in goal_policy_rows}
    reference = by_policy.get(REFERENCE_POLICY, {})
    rows: list[dict[str, Any]] = []
    for row in sorted(goal_policy_rows, key=lambda item: str(item.get("policy_id"))):
        policy_id = str(row.get("policy_id"))
        spl_delta = delta(row.get("primary_spl_proxy_mean"), reference.get("primary_spl_proxy_mean"))
        rank_delta = delta(
            row.get("primary_first_hit_rank_mean_over_success"),
            reference.get("primary_first_hit_rank_mean_over_success"),
        )
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_interpretation",
                "policy_id": policy_id,
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_success_rows": row.get("primary_success_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
                "spl_delta_vs_detector_confidence_reachable_subset": spl_delta,
                "hit_rank_delta_vs_detector_confidence_reachable_subset": rank_delta,
                "supports_single_case_proxy_recovery": bool(row.get("primary_success_rows")),
                "supports_policy_sr_claim": False,
                "supports_policy_spl_diagnostic": spl_delta is not None and spl_delta > 0,
                "trajectory_contract_candidate": bool(row.get("primary_success_rows")),
                "interpretation": (
                    "All policies recover the single target-free case under the viewpoint proxy; path-cost "
                    "policies improve proxy SPL but not hit rank, so this is a trajectory-smoke trigger, "
                    "not a final policy claim."
                ),
            }
        )
    return rows


def build_trajectory_decision_rows(proxy_recovered: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "promote_m127_target_free_detector_policies_to_habitat_trajectory_contract",
            "decision": "select" if proxy_recovered else "reject_now",
            "reason": (
                "M127 recovers the target-free source-coverage case under leakage-safe viewpoint proxy; "
                "the next useful gate is a bounded Docker trajectory contract, not another detector long job."
                if proxy_recovered
                else "M127 has no primary proxy recovery, so trajectory execution would measure a known source miss."
            ),
            "selected_next_unit": NEXT_UNIT if proxy_recovered else None,
            "trajectory_contract_promotion_ready": proxy_recovered,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        {
            "version": VERSION,
            "route_id": "run_more_target_free_render_detector_before_trajectory",
            "decision": "reject_now" if proxy_recovered else "defer",
            "reason": "The current positive proxy case should be trajectory-checked before spending another long render/detector cycle.",
            "launch_long_job_now": False,
            "expected_paper_value": "lower_than_bounded_trajectory_smoke_now",
        },
        {
            "version": VERSION,
            "route_id": "claim_final_real_navigation_sr_spl_or_rgbd_robustness",
            "decision": "reject_now",
            "reason": "M127/M128 cover one target-free proxy case and do not execute trajectories or external navigation baselines.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
    ]


def build_claim_boundary_rows(proxy_recovered: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_single_case_target_free_proxy_recovery",
            "supported": proxy_recovered,
            "claim_boundary": "M127/M128 support only a single-case leakage-safe target-free viewpoint-proxy recovery diagnostic.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_trajectory_contract_promotion",
            "supported": proxy_recovered,
            "claim_boundary": "A bounded trajectory contract is justified as the next gate, but the trajectory result is not yet available.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "No new Habitat trajectory is executed in M128.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "The evidence is one target-free detector case and lacks heldout transfer and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "M128 does not define a deployable trigger or budgeted real policy; it only selects the next trajectory contract.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M128 is a target-free navigation-source gate and does not reopen the E006 human-intent utility failure.",
        },
    ]


def build_route_decision_rows(input_ready: bool, proxy_recovered: bool) -> list[dict[str, Any]]:
    if not input_ready:
        return [
            {
                "version": VERSION,
                "decision": "repair_m128_inputs",
                "selected_next_unit": "repair E008-M128 input readiness",
                "reason": "M125/M126/M127 inputs are incomplete or not ready.",
                "launch_long_job_now": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "target_free_goal_result_interpreted_select_trajectory_contract"
            if proxy_recovered
            else "target_free_goal_result_interpreted_reject_trajectory",
            "selected_next_unit": NEXT_UNIT if proxy_recovered else "E008 target-free source repair after M128",
            "reason": (
                "M127 has leakage-safe proxy recovery on the selected target-free case, so M129 should fix the trajectory execution contract and Docker preflight."
                if proxy_recovered
                else "M127 failed proxy recovery; additional source repair is needed before trajectory execution."
            ),
            "trajectory_contract_promotion_ready": proxy_recovered,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
) -> str:
    case_lines = [
        "| {scan_id} | {object_category} | {m125_path_ready_candidate_rows}/{m125_candidate_rows} | "
        "{m127_primary_success_policy_count}/{m127_policy_rows} | {m127_goal_xz_1p0_success_policy_count}/{m127_policy_rows} | "
        "{m127_best_any_viewpoint_xz_m_min} | {m127_best_goal_xz_m_min} | {m127_min_primary_first_hit_cost_m} | {target_free_result_class} |".format(
            scan_id=row.get("scan_id"),
            object_category=row.get("object_category"),
            m125_path_ready_candidate_rows=row.get("m125_path_ready_candidate_rows"),
            m125_candidate_rows=row.get("m125_candidate_rows"),
            m127_primary_success_policy_count=row.get("m127_primary_success_policy_count"),
            m127_policy_rows=row.get("m127_policy_rows"),
            m127_goal_xz_1p0_success_policy_count=row.get("m127_goal_xz_1p0_success_policy_count"),
            m127_best_any_viewpoint_xz_m_min=fmt(row.get("m127_best_any_viewpoint_xz_m_min")),
            m127_best_goal_xz_m_min=fmt(row.get("m127_best_goal_xz_m_min")),
            m127_min_primary_first_hit_cost_m=fmt(row.get("m127_min_primary_first_hit_cost_m")),
            target_free_result_class=row.get("target_free_result_class"),
        )
        for row in case_rows
    ]
    policy_lines = [
        "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | "
        "{primary_spl_proxy_mean} | {primary_first_hit_rank_mean_over_success} | "
        "{spl_delta_vs_detector_confidence_reachable_subset} | {goal_xz_1p0_proxy_sr} |".format(
            policy_id=row.get("policy_id"),
            primary_success_rows=row.get("primary_success_rows"),
            scan_policy_rows=row.get("scan_policy_rows"),
            primary_proxy_sr=fmt(row.get("primary_proxy_sr")),
            primary_spl_proxy_mean=fmt(row.get("primary_spl_proxy_mean")),
            primary_first_hit_rank_mean_over_success=fmt(row.get("primary_first_hit_rank_mean_over_success")),
            spl_delta_vs_detector_confidence_reachable_subset=fmt(
                row.get("spl_delta_vs_detector_confidence_reachable_subset")
            ),
            goal_xz_1p0_proxy_sr=fmt(row.get("goal_xz_1p0_proxy_sr")),
        )
        for row in policy_rows
    ]
    trajectory_lines = [
        "| {route_id} | {decision} | {reason} |".format(
            route_id=row.get("route_id"),
            decision=row.get("decision"),
            reason=row.get("reason"),
        )
        for row in trajectory_rows
    ]
    return f"""# E008-M128 Target-Free Detector-Goal Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M125 status: `{coverage['m125_status']}`.
- Input M126 status: `{coverage['m126_status']}`.
- Input M127 status: `{coverage['m127_status']}`.
- Target-free scan rows: {coverage['target_free_scan_rows']}.
- M125 path-ready candidates: {coverage['m125_path_ready_candidate_rows']} / {coverage['m125_candidate_rows']}.
- M126 visit-order rows: {coverage['m126_visit_order_rows']}.
- M127 candidate-goal eval rows: {coverage['m127_candidate_goal_eval_rows']}.
- M127 primary proxy success max: {coverage['m127_primary_success_count_max']}.
- M127 `goal_xz_1p0` proxy success max: {coverage['goal_xz_1p0_success_count_max']}.
- Best any-viewpoint XZ distance: {fmt(coverage['best_any_viewpoint_xz_m_min'])}m.
- Best goal-center XZ distance: {fmt(coverage['best_goal_xz_m_min'])}m.
- Trajectory contract promotion ready: {coverage['trajectory_contract_promotion_ready']}.
- Direct long job launch now: {coverage['launch_long_job_now']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Case Interpretation

| scan_id | category | path-ready | primary hits | goal 1.0m hits | best any-vp XZ m | best goal XZ m | min hit cost m | result class |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(case_lines)}

## Policy Interpretation

| policy_id | primary hits | proxy SR | proxy SPL | mean hit rank | SPL delta vs reachable detector | goal 1.0m proxy SR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(policy_lines)}

## Trajectory Decision

| route | decision | reason |
| --- | --- | --- |
{chr(10).join(trajectory_lines)}

## Claim Boundary

- M128 supports moving to a bounded trajectory-contract gate because M127 has leakage-safe target-free viewpoint-proxy recovery.
- M128 does not itself support real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human-intent main contribution.
- The result is one target-free case; M129/M130 must separate executed navigation behavior from proxy goal-evaluation behavior.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m125_coverage = read_json(M125_DIR / "coverage.json")
    m126_coverage = read_json(M126_DIR / "coverage.json")
    m127_coverage = read_json(M127_DIR / "coverage.json")
    scan_goal_rows = read_jsonl(M127_DIR / "target_free_scan_goal_metric_rows.jsonl")
    goal_policy_rows = aggregate_goal_rows(read_jsonl(M127_DIR / "policy_goal_metric_rows.jsonl"))

    input_ready = (
        m125_coverage.get("status") == "e008_m125_target_free_detector_candidate_navmesh_validation_ready"
        and m126_coverage.get("status") == "e008_m126_target_free_detector_candidate_visit_order_path_smoke_ready"
        and m127_coverage.get("status") == "e008_m127_target_free_detector_candidate_goal_evaluation_smoke_ready"
        and bool(scan_goal_rows)
        and bool(goal_policy_rows)
        and bool(m127_coverage.get("leakage_audit_pass"))
    )

    case_rows = build_case_interpretation_rows(m125_coverage, m126_coverage, scan_goal_rows)
    policy_rows = build_policy_interpretation_rows(goal_policy_rows)
    proxy_recovered = bool(m127_coverage.get("target_free_proxy_recovery_observed")) and input_ready
    trajectory_rows = build_trajectory_decision_rows(proxy_recovered)
    claim_rows = build_claim_boundary_rows(proxy_recovered)
    route_rows = build_route_decision_rows(input_ready, proxy_recovered)

    best_any = min((finite_float(row.get("m127_best_any_viewpoint_xz_m_min")) for row in case_rows), default=None)
    best_goal = min((finite_float(row.get("m127_best_goal_xz_m_min")) for row in case_rows), default=None)
    goal_success_max = max(
        (int(row.get("m127_goal_xz_1p0_success_policy_count") or 0) for row in case_rows),
        default=0,
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m125_status": m125_coverage.get("status"),
        "m126_status": m126_coverage.get("status"),
        "m127_status": m127_coverage.get("status"),
        "target_free_scan_rows": len(case_rows),
        "m125_candidate_rows": m125_coverage.get("candidate_rows"),
        "m125_path_ready_candidate_rows": m125_coverage.get("source_to_snapped_path_found_rows"),
        "m126_visit_order_rows": m126_coverage.get("visit_order_rows"),
        "m127_candidate_goal_eval_rows": m127_coverage.get("candidate_goal_eval_rows"),
        "m127_primary_success_count_max": m127_coverage.get("primary_success_count_max"),
        "goal_xz_1p0_success_count_max": goal_success_max,
        "best_any_viewpoint_xz_m_min": best_any,
        "best_goal_xz_m_min": best_goal,
        "target_free_proxy_recovery_observed": bool(m127_coverage.get("target_free_proxy_recovery_observed")),
        "leakage_audit_pass": bool(m127_coverage.get("leakage_audit_pass")),
        "trajectory_contract_promotion_ready": proxy_recovered,
        "direct_trajectory_execution_ready": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if proxy_recovered else "E008 target-free source repair after M128",
    }

    output_files: dict[str, Any] = {
        "coverage.json": coverage,
        "target_free_case_interpretation_rows.jsonl": case_rows,
        "policy_interpretation_rows.jsonl": policy_rows,
        "trajectory_decision_rows.jsonl": trajectory_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
    }
    for name, payload in output_files.items():
        if name.endswith(".jsonl"):
            write_jsonl(ARTIFACT_DIR / name, payload)
        else:
            write_json(ARTIFACT_DIR / name, payload)

    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, case_rows, policy_rows, trajectory_rows),
        encoding="utf-8",
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
