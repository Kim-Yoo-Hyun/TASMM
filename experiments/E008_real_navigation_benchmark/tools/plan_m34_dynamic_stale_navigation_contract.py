#!/usr/bin/env python3
"""Design the dynamic-stale navigation benchmark contract after M33."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M34_dynamic_stale_navigation_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M34_dynamic_stale_navigation_contract_v0"
VERSION = "e008_m34_dynamic_stale_navigation_contract_v0"

M22_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M31_DIR = EXP_ROOT / "artifacts" / "E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0"
M32_DIR = EXP_ROOT / "artifacts" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"
M33_DIR = EXP_ROOT / "artifacts" / "E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0"
E001_M02_DIR = ROOT / "experiments" / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0"
E002_M09_DIR = ROOT / "experiments" / "E002_path_cost_bridge" / "artifacts" / "E002-M09_reachable_first_scoring_v0"

SELECTED_ROUTE = "hm3d_counterfactual_stale_overlay_v0"
NEXT_UNIT = "E008-M35 dynamic-stale overlay row materialization smoke"
PRIMARY_DETECTOR_BASELINE = "detector_confidence_reachable_subset_v0"
H001_POLICY = "h001_task_conditioned_memory_trust_navigation_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def index_by_plan(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_plan_uid")): row for row in rows if row.get("policy_plan_uid")}


def build_source_option_rows(
    m33_cov: dict[str, Any],
    m31_candidates: list[dict[str, Any]],
    e001_query_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_roles = Counter(str(row.get("source_role")) for row in m31_candidates)
    return [
        {
            "version": VERSION,
            "source_route_id": "scale_current_hm3d_objectnav_fallback_v0",
            "status": "rejected_for_main_claim",
            "uses_true_temporal_stale_memory": False,
            "uses_habitat_navmesh_execution": True,
            "can_run_without_new_download": True,
            "available_episode_rows": m33_cov.get("m32_scan_task_metric_rows"),
            "available_candidate_rows": len(m31_candidates),
            "reason": "M33 shows H001 underperforms detector trajectories and the setup has no controlled old/new stale-memory intervention.",
            "selected": False,
        },
        {
            "version": VERSION,
            "source_route_id": SELECTED_ROUTE,
            "status": "selected_for_next_smoke",
            "uses_true_temporal_stale_memory": False,
            "uses_habitat_navmesh_execution": True,
            "can_run_without_new_download": True,
            "available_episode_rows": m33_cov.get("m32_scan_task_metric_rows"),
            "available_candidate_rows": len(m31_candidates),
            "initial_memory_proxy_rows": source_roles.get("initial_memory_proxy", 0),
            "current_observation_rows": source_roles.get("current_observation", 0),
            "reason": "Use existing Habitat executable episodes and inject a counterfactual stale old-memory layer so static stale memory, detector-only current observation, and H001 memory trust can be compared on the same trajectory denominator.",
            "selected": True,
        },
        {
            "version": VERSION,
            "source_route_id": "3rscan_3dssg_true_dynamic_pair_navigation_v0",
            "status": "deferred_true_dynamic_route",
            "uses_true_temporal_stale_memory": True,
            "uses_habitat_navmesh_execution": False,
            "can_run_without_new_download": True,
            "available_query_rows": len(e001_query_rows),
            "reason": "3RScan/3DSSG provides true reference-rescan stale semantic memory, but there is no ready Habitat navmesh or collision-aware simulator route for real SR/SPL.",
            "selected": False,
        },
        {
            "version": VERSION,
            "source_route_id": "3rscan_occupancy_grid_astar_dynamic_pair_v0",
            "status": "supporting_proxy_route",
            "uses_true_temporal_stale_memory": True,
            "uses_habitat_navmesh_execution": False,
            "can_run_without_new_download": True,
            "available_query_rows": len(e001_query_rows),
            "reason": "E002 provides occupancy-grid A* proxy path-cost evidence on true dynamic pairs, but it is not real Habitat SR/SPL.",
            "selected": False,
        },
    ]


def build_intervention_rows(
    m31_plans: list[dict[str, Any]],
    m32_metrics: list[dict[str, Any]],
    m31_source_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metrics = index_by_plan(m32_metrics)
    source_gap_keys = {
        (str(row.get("adapter_episode_id")), str(row.get("task_context_id"))) for row in m31_source_gap_rows
    }
    rows = []
    for plan in sorted(m31_plans, key=lambda row: (str(row.get("scan_id")), str(row.get("task_context_id")))):
        plan_uid = str(plan.get("policy_plan_uid"))
        metric = metrics.get(plan_uid, {})
        episode_id = str(plan.get("adapter_episode_id"))
        task_id = str(plan.get("task_context_id"))
        source_gap = (episode_id, task_id) in source_gap_keys
        rows.append(
            {
                "version": VERSION,
                "benchmark_row_uid": f"m34::{plan_uid}",
                "selected_route": SELECTED_ROUTE,
                "adapter_episode_id": episode_id,
                "scan_id": plan.get("scan_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "task_context_id": task_id,
                "intervention_type": "counterfactual_stale_old_memory_overlay",
                "old_memory_source": "initial_memory_proxy_or_injected_stale_same_category_candidate",
                "current_evidence_source": "non_oracle_rendered_rgbd_detector_candidates",
                "navigation_source": "HM3D_ObjectNav_Habitat_navmesh",
                "candidate_visit_order_input": "stale_memory_candidates + current_observation_candidates + structured_task_context + path/reachability fields",
                "source_gap_boundary": source_gap,
                "m31_candidate_rows": plan.get("candidate_rows"),
                "m31_path_ready_candidate_rows": plan.get("path_ready_candidate_rows"),
                "m32_trajectory_success": bool(metric.get("trajectory_success")),
                "m32_spl": metric.get("SPL"),
                "m32_path_length_m": metric.get("PathLengthM"),
                "m32_candidate_visits": metric.get("CandidateVisits"),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_m32_success_label": False,
                "diagnostic_can_use_eval_goal_after_execution": True,
                "materialize_in_next_unit": True,
                "claim_boundary": "Counterfactual stale overlay is a navigation benchmark construction, not evidence of true temporal object movement.",
            }
        )
    return rows


def build_policy_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": "static_stale_memory_top1_v0",
            "policy_family": "naive_stale_memory",
            "role": "naive_baseline",
            "allowed_inputs": "episode start, stale old-memory candidate pose, category, task context only for reporting",
            "expected_failure": "visits stale old location even when current evidence is available",
            "paper_question": "Why is static semantic memory insufficient?",
        },
        {
            "version": VERSION,
            "policy_id": "fixed_topk_current_observation_v0",
            "policy_family": "fixed_budget_reobserve",
            "role": "naive_baseline",
            "allowed_inputs": "current detector candidates, confidence, path-ready fields, fixed top-k budget",
            "expected_failure": "wastes budget or misses stale-memory useful cases because trust does not depend on task or memory state",
            "paper_question": "Why not always re-observe a fixed number of current candidates?",
        },
        {
            "version": VERSION,
            "policy_id": PRIMARY_DETECTOR_BASELINE,
            "policy_family": "detector_confidence",
            "role": "required_navigation_baseline",
            "allowed_inputs": "current detector candidates, detector confidence, navmesh reachability",
            "expected_failure": "should be strong under current HM3D smoke; H001 must beat or explain it only under stale-memory interventions",
            "paper_question": "Why not use a current detector ranking directly?",
        },
        {
            "version": VERSION,
            "policy_id": "task_agnostic_memory_trust_navigation_v0",
            "policy_family": "ablation",
            "role": "ablation",
            "allowed_inputs": "staleness, current proposal reliability, path cost, no task utility differences",
            "expected_failure": "cannot change re-observation budget or memory trust by task value",
            "paper_question": "Does structured task context matter beyond global trust?",
        },
        {
            "version": VERSION,
            "policy_id": H001_POLICY,
            "policy_family": "h001",
            "role": "test_method",
            "allowed_inputs": "staleness, task value, current proposal reliability, reachability, path/search cost, fixed candidate budget",
            "expected_failure": "if it does not beat detector/current-only or task-agnostic trust under stale intervention, navigation claim remains blocked",
            "paper_question": "Does memory trust and re-observation need to be task- and cost-conditioned?",
        },
        {
            "version": VERSION,
            "policy_id": "oracle_current_target_upper_bound_v0",
            "policy_family": "oracle",
            "role": "upper_bound_not_method",
            "allowed_inputs": "eval-only target after execution for upper-bound reporting only",
            "expected_failure": "not applicable",
            "paper_question": "How much headroom remains after candidate-source construction?",
        },
    ]


def build_metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "metric_id": "SR",
            "metric_role": "primary_navigation",
            "definition": "success after executing candidate stops under eval-only ObjectNav goal/viewpoint check",
            "claim_ready_after_m34": False,
        },
        {
            "version": VERSION,
            "metric_id": "SPL",
            "metric_role": "primary_navigation_efficiency",
            "definition": "success-weighted oracle path length over executed path length",
            "claim_ready_after_m34": False,
        },
        {
            "version": VERSION,
            "metric_id": "OldLocationDeadEndCostM",
            "metric_role": "stale_memory_diagnostic",
            "definition": "path length spent visiting injected stale old-memory locations before reaching a current target or exhausting budget",
            "claim_ready_after_m34": False,
        },
        {
            "version": VERSION,
            "metric_id": "StaleVisitRate",
            "metric_role": "stale_memory_diagnostic",
            "definition": "fraction of rows where a policy visits stale old-memory candidate before a successful current observation",
            "claim_ready_after_m34": False,
        },
        {
            "version": VERSION,
            "metric_id": "ReObservationRate",
            "metric_role": "decision_diagnostic",
            "definition": "fraction of rows where policy chooses current-observation candidates before or instead of stale memory",
            "claim_ready_after_m34": False,
        },
        {
            "version": VERSION,
            "metric_id": "SourceGapRate",
            "metric_role": "candidate_source_boundary",
            "definition": "fraction of benchmark rows where no non-oracle current candidate can hit the eval target region",
            "claim_ready_after_m34": False,
        },
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    blocked_fields = [
        ("eval_goal_object_id", "ObjectNav target object id is evaluation-only."),
        ("eval_goal_position", "ObjectNav target position is evaluation-only."),
        ("eval_viewpoints", "ObjectNav target viewpoints are evaluation-only."),
        ("candidate_to_eval_goal_xz_m", "Distance to eval goal leaks the answer."),
        ("candidate_to_nearest_eval_viewpoint_xz_m", "Distance to eval viewpoint leaks the answer."),
        ("m32_trajectory_success", "Trajectory success is post-hoc metric-only."),
        ("m33_source_gap_label", "Source-gap label is diagnostic-only."),
        ("detector_success_delta", "Baseline comparison result is post-hoc."),
    ]
    return [
        {
            "version": VERSION,
            "field": field,
            "blocked_for_policy": True,
            "allowed_for_metric_or_offline_diagnostic": True,
            "reason": reason,
        }
        for field, reason in blocked_fields
    ]


def build_readiness_gate_rows(
    m33_cov: dict[str, Any],
    intervention_rows: list[dict[str, Any]],
    e001_query_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_rows = [row for row in intervention_rows if row.get("materialize_in_next_unit")]
    source_gap_rows = [row for row in intervention_rows if row.get("source_gap_boundary")]
    return [
        {
            "version": VERSION,
            "gate_id": "m33_baseline_alignment_ready",
            "status": "pass" if m33_cov.get("baseline_alignment_ready") else "fail",
            "evidence": f"M33 status={m33_cov.get('status')}; H001 vs detector SR delta={m33_cov.get('h001_minus_primary_detector_SR')}.",
        },
        {
            "version": VERSION,
            "gate_id": "scale_current_hm3d_smoke_as_main_result",
            "status": "fail",
            "evidence": "Current H001 fallback underperforms detector and lacks dynamic stale-memory intervention.",
        },
        {
            "version": VERSION,
            "gate_id": "hm3d_counterfactual_stale_overlay_materialization",
            "status": "pass" if route_rows else "fail",
            "evidence": f"Materialization plan rows={len(route_rows)}; source-gap diagnostic rows={len(source_gap_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "true_dynamic_pair_navigation_source",
            "status": "fail",
            "evidence": f"E001 dynamic-pair query rows={len(e001_query_rows)}, but no ready Habitat/navmesh execution source exists for 3RScan/3DSSG.",
        },
        {
            "version": VERSION,
            "gate_id": "paper_claim_after_m34",
            "status": "fail",
            "evidence": "M34 is a contract/design unit; no trajectory result is produced.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_navigation_contract",
            "status": "supported_contract_only",
            "safe_claim": "M34 defines a leakage-safe route for converting the current HM3D navigation smoke into a dynamic-stale benchmark construction.",
        },
        {
            "version": VERSION,
            "claim_id": "true_dynamic_stale_navigation",
            "status": "not_ready",
            "safe_claim": "Do not claim true temporal dynamic object navigation until 3RScan/3DSSG stale pairs are connected to executable navigation or an equivalent intervention is validated.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_real_navigation_improvement",
            "status": "blocked",
            "safe_claim": "Do not claim H001 improves real navigation SR/SPL from M34.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "Structured task context remains an ablation/conditioning signal, not a natural-language intent contribution.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m34_selected_route",
            "selected_route": SELECTED_ROUTE,
            "selected_next_unit": NEXT_UNIT,
            "decision": "materialize_counterfactual_stale_overlay_before_any_scale_up",
            "reason": "M33 blocks scaling the current H001 fallback result; the next useful step is to create a stale-memory intervention denominator with fixed policy inputs and blocked eval fields.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m34_detector_baseline_policy",
            "selected_route": SELECTED_ROUTE,
            "selected_next_unit": NEXT_UNIT,
            "decision": f"carry_forward_{PRIMARY_DETECTOR_BASELINE}",
            "reason": "Detector trajectory rows are the required baseline because they dominate the current H001 smoke.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    source_options: list[dict[str, Any]],
    intervention_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected = next(row for row in source_options if row.get("selected"))
    source_gap_count = sum(1 for row in intervention_rows if row.get("source_gap_boundary"))
    lines = [
        "# E008-M34 Dynamic-Stale Navigation Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected route: `{coverage['selected_route']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Planned intervention rows: {coverage['intervention_plan_rows']}.",
        f"- Source-gap diagnostic rows: {source_gap_count}.",
        f"- Current H001 vs detector `SR` delta from M33: {fmt(coverage['m33_h001_minus_detector_SR'])}.",
        f"- Current H001 vs detector `SPL` delta from M33: {fmt(coverage['m33_h001_minus_detector_SPL'])}.",
        f"- True `3RScan` dynamic-pair query rows available as proxy source: {coverage['e001_query_rows']}.",
        "",
        "## Source Route Decision",
        "",
        "| route | status | true temporal stale memory | Habitat execution | selected | reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in source_options:
        lines.append(
            f"| `{row['source_route_id']}` | {row['status']} | {row['uses_true_temporal_stale_memory']} | {row['uses_habitat_navmesh_execution']} | {row['selected']} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Selected Contract",
            "",
            f"- `{selected['source_route_id']}` is selected for the next smoke because it can use existing `Habitat` executable rows while adding an explicit stale-memory intervention layer.",
            "- This is not a true temporal movement claim. It is a controlled benchmark construction to test whether stale-memory trust decisions can beat static memory and current detector ranking under the same navigation denominator.",
            "- Eval-only ObjectNav goals/viewpoints remain metric-only and blocked from policy input.",
            "",
            "## Required Policies",
            "",
        ]
    )
    for row in policy_rows:
        lines.append(f"- `{row['policy_id']}`: {row['role']} - {row['expected_failure']}")
    lines.extend(
        [
            "",
            "## Required Metrics",
            "",
        ]
    )
    for row in metric_rows:
        lines.append(f"- `{row['metric_id']}`: {row['definition']}")
    lines.extend(
        [
            "",
            "## Gates",
            "",
        ]
    )
    for row in gate_rows:
        lines.append(f"- `{row['gate_id']}`: {row['status']} - {row['evidence']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}`: {row['status']} - {row['safe_claim']}")
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            f"- Decision: `{route_rows[0]['decision']}`.",
            f"- Next: {route_rows[0]['selected_next_unit']}.",
            f"- Reason: {route_rows[0]['reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m22_cov = read_json(M22_DIR / "coverage.json")
    m32_cov = read_json(M32_DIR / "coverage.json")
    m33_cov = read_json(M33_DIR / "coverage.json")
    m31_candidates = read_jsonl(M31_DIR / "h001_fallback_candidate_visit_order_rows.jsonl")
    m31_plans = read_jsonl(M31_DIR / "trajectory_execution_plan_rows.jsonl")
    m31_source_gap_rows = read_jsonl(M31_DIR / "source_gap_boundary_rows.jsonl")
    m32_metrics = read_jsonl(M32_DIR / "trajectory_policy_metric_rows.jsonl")
    e001_query_rows = read_jsonl(E001_M02_DIR / "query_rows.jsonl")
    e002_cov = read_json(E002_M09_DIR / "coverage.json")

    source_options = build_source_option_rows(m33_cov, m31_candidates, e001_query_rows)
    intervention_rows = build_intervention_rows(m31_plans, m32_metrics, m31_source_gap_rows)
    policy_rows = build_policy_contract_rows()
    metric_rows = build_metric_contract_rows()
    blocked_rows = build_blocked_input_rows()
    gate_rows = build_readiness_gate_rows(m33_cov, intervention_rows, e001_query_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()

    source_roles = Counter(str(row.get("source_role")) for row in m31_candidates)
    coverage = {
        "version": VERSION,
        "status": "e008_m34_dynamic_stale_navigation_contract_ready",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m22_status": m22_cov.get("status"),
        "m32_status": m32_cov.get("status"),
        "m33_status": m33_cov.get("status"),
        "selected_route": SELECTED_ROUTE,
        "selected_next_unit": NEXT_UNIT,
        "source_option_rows": len(source_options),
        "intervention_plan_rows": len(intervention_rows),
        "policy_contract_rows": len(policy_rows),
        "metric_contract_rows": len(metric_rows),
        "blocked_input_rows": len(blocked_rows),
        "readiness_gate_rows": len(gate_rows),
        "claim_boundary_rows": len(claim_rows),
        "route_decision_rows": len(route_rows),
        "m31_candidate_visit_rows": len(m31_candidates),
        "m31_execution_plan_rows": len(m31_plans),
        "m31_source_role_counts": dict(sorted(source_roles.items())),
        "m31_source_gap_rows": len(m31_source_gap_rows),
        "m33_h001_minus_detector_SR": m33_cov.get("h001_minus_primary_detector_SR"),
        "m33_h001_minus_detector_SPL": m33_cov.get("h001_minus_primary_detector_SPL"),
        "m33_source_gap_h001_SR": m33_cov.get("source_gap_h001_SR"),
        "m33_source_gap_detector_SR": m33_cov.get("source_gap_detector_SR"),
        "e001_query_rows": len(e001_query_rows),
        "e002_status": e002_cov.get("status"),
        "contract_ready": True,
        "materialization_ready_next": True,
        "dynamic_stale_navigation_result_ready": False,
        "true_temporal_dynamic_navigation_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_intervention_option_rows.jsonl", source_options)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_intervention_plan_rows.jsonl", intervention_rows)
    write_jsonl(ARTIFACT_DIR / "policy_baseline_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_intervention_plan_rows.jsonl", intervention_rows)
    write_jsonl(DATA_OUT_DIR / "policy_baseline_contract_rows.jsonl", policy_rows)
    write_jsonl(DATA_OUT_DIR / "metric_contract_rows.jsonl", metric_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, source_options, intervention_rows, policy_rows, metric_rows, gate_rows, claim_rows, route_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
