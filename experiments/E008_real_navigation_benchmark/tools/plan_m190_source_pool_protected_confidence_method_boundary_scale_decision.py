#!/usr/bin/env python3
"""Fix the M190 method boundary after source-pool transition repair failed."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m190_source_pool_protected_confidence_method_boundary_scale_decision_v0"
READY_STATUS = "e008_m190_source_pool_protected_confidence_method_boundary_scale_decision_ready"
BLOCKED_STATUS = "e008_m190_source_pool_protected_confidence_method_boundary_scale_decision_blocked"
NEXT_UNIT = "E008-M191 source-pool protected-confidence scale-up contract"

M184_ROOT = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"
M188_ROOT = EXP_ROOT / "artifacts" / "E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
M189_ROOT = EXP_ROOT / "artifacts" / "E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0"
OUT_ROOT = EXP_ROOT / "artifacts" / "E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0"
DATA_OUT_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0"

PROTECTED_POLICY = "detector_confidence_reachable_subset_v0"
REJECTED_REPAIR_POLICY = "confidence_protected_transition_cost_policy_v1"
REJECTED_PATH_POLICY = "path_cost_ascending_reachable_subset_v0"
TRANSITION_ONLY_POLICY = "transition_cost_only_reachable_subset_v0"
SOURCE_POOL_COMPONENT = "fixed_budget_source_pool_candidate_generation"


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


def sanitize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def aggregate_by_policy(rows: list[dict[str, Any]], policy_key: str = "policy_id") -> dict[str, dict[str, Any]]:
    return {
        str(row.get(policy_key) or row.get("group_id")): row
        for row in rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def bool_all(values: list[bool]) -> bool:
    return bool(values) and all(values)


def build_method_boundary_rows(
    m184_agg: dict[str, dict[str, Any]],
    m188_agg: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    protected_exec = m184_agg.get(PROTECTED_POLICY, {})
    protected_proxy = m188_agg.get(PROTECTED_POLICY, {})
    repair_proxy = m188_agg.get(REJECTED_REPAIR_POLICY, {})
    path_exec = m184_agg.get(REJECTED_PATH_POLICY, {})
    transition_proxy = m188_agg.get(TRANSITION_ONLY_POLICY, {})
    return [
        {
            "version": VERSION,
            "component_or_policy": SOURCE_POOL_COMPONENT,
            "role": "kept_method_component",
            "decision": "keep_as_candidate_source_expansion",
            "evidence": "M177-M180 materialized 64 source poses and 180 path-ready candidates; M182/M188 proxy recovery is 7/8.",
            "paper_claim_status": "candidate_source_component_supported_diagnostic",
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "component_or_policy": PROTECTED_POLICY,
            "role": "protected_execution_default",
            "decision": "keep_as_safe_execution_policy",
            "docker_SR": protected_exec.get("SR"),
            "docker_SPL": protected_exec.get("SPL"),
            "docker_CandidateVisits_mean": protected_exec.get("CandidateVisits_mean"),
            "proxy_SR": protected_proxy.get("primary_proxy_sr"),
            "proxy_SPL": protected_proxy.get("primary_spl_proxy_mean"),
            "paper_claim_status": "safe_baseline_and_current_default",
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "component_or_policy": REJECTED_PATH_POLICY,
            "role": "rejected_main_ranking_policy",
            "decision": "reject_for_scale_up",
            "docker_SR": path_exec.get("SR"),
            "docker_SPL": path_exec.get("SPL"),
            "reason": "Ties protected detector confidence on SR but loses Docker SPL.",
            "paper_claim_status": "negative_ablation",
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "component_or_policy": REJECTED_REPAIR_POLICY,
            "role": "rejected_repair_policy",
            "decision": "reject_for_trajectory_promotion",
            "proxy_SR": repair_proxy.get("primary_proxy_sr"),
            "proxy_SPL": repair_proxy.get("primary_spl_proxy_mean"),
            "protected_proxy_SPL": protected_proxy.get("primary_spl_proxy_mean"),
            "reason": "Ties protected proxy SR but loses proxy SPL; M189 shows this is objective mismatch, not implementation failure.",
            "paper_claim_status": "negative_ablation",
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "component_or_policy": TRANSITION_ONLY_POLICY,
            "role": "rejected_ablation",
            "decision": "reject_as_search_success_objective",
            "proxy_SR": transition_proxy.get("primary_proxy_sr"),
            "proxy_SPL": transition_proxy.get("primary_spl_proxy_mean"),
            "reason": "Optimizing transition cost alone lowers route cost but does not optimize cost-to-first-success.",
            "paper_claim_status": "negative_ablation",
            "trajectory_execution_now": False,
        },
    ]


def build_claim_evidence_rows(m184_agg: dict[str, dict[str, Any]], m188_cov: dict[str, Any], m189_cov: dict[str, Any]) -> list[dict[str, Any]]:
    protected_exec = m184_agg.get(PROTECTED_POLICY, {})
    return [
        {
            "version": VERSION,
            "claim_id": "source_pool_expansion_surfaces_recoverable_candidates",
            "status": "diagnostic_supported",
            "evidence": "Source-pool branch has 180 path-ready candidates and 7/8 leakage-safe proxy recoveries.",
            "metric": "proxy_SR",
            "value": m188_cov.get("protected_primary_proxy_sr"),
            "claim_boundary": "Supports candidate-source expansion as a semantic-map/re-observation component, not final navigation improvement.",
        },
        {
            "version": VERSION,
            "claim_id": "protected_detector_confidence_is_current_safe_policy",
            "status": "supported_as_default",
            "evidence": "Protected policy is strongest among current source-pool policies by proxy SPL and already has bounded Docker trajectory evidence.",
            "docker_SR": protected_exec.get("SR"),
            "docker_SPL": protected_exec.get("SPL"),
            "proxy_SR": m188_cov.get("protected_primary_proxy_sr"),
            "proxy_SPL": m188_cov.get("protected_primary_spl_proxy_mean"),
            "claim_boundary": "This is a protected baseline/default, not the final novelty claim.",
        },
        {
            "version": VERSION,
            "claim_id": "transition_cost_reranking_improves_source_pool_search",
            "status": "rejected",
            "evidence": "Selected transition repair proxy SPL is below protected detector confidence.",
            "selected_proxy_SPL": m188_cov.get("selected_primary_spl_proxy_mean"),
            "protected_proxy_SPL": m188_cov.get("protected_primary_spl_proxy_mean"),
            "same_success_proposal_rows": m189_cov.get("same_success_proposal_rows"),
            "claim_boundary": "Use as negative ablation/failure diagnosis only.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl_improvement",
            "status": "not_ready",
            "evidence": "Current branch is an 8-episode bounded smoke; selected ranking policies have not beaten the protected policy.",
            "claim_boundary": "Requires scale-up split, heldout transfer, external navigation/search baselines, and Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "not_ready",
            "evidence": "E006-M08 remains negative for human intent as a main claim.",
            "claim_boundary": "Structured task context can remain as secondary conditioning/ablation unless redesigned and revalidated.",
        },
    ]


def build_scale_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "no_immediate_transition_repair_trajectory",
            "decision": "do_not_launch_docker_trajectory_for_m187_repair",
            "reason": "M188/M189 show the repaired order is weaker than protected detector confidence before execution.",
            "trajectory_execution_now": False,
            "status": "fixed",
        },
        {
            "version": VERSION,
            "decision_id": "scale_source_pool_acquisition_not_rerank",
            "decision": "scale_candidate_source_expansion_with_protected_confidence_default",
            "reason": "The source-pool branch repairs source coverage, while ranking must remain confidence-protected until a success-likelihood guard is justified.",
            "trajectory_execution_now": False,
            "status": "selected_next_contract",
        },
        {
            "version": VERSION,
            "decision_id": "m191_contract",
            "decision": "write_scale_up_contract_before_any_long_job",
            "selected_next_unit": NEXT_UNIT,
            "required_before_execution": [
                "fixed heldout denominator",
                "source-pool generation budget and priority guard",
                "protected detector-confidence execution default",
                "candidate-generation ablation against no source-pool expansion",
                "leakage-safe eval goal usage audit",
                "Docker trajectory command ledger",
            ],
            "trajectory_execution_now": False,
            "status": "selected",
        },
    ]


def build_baseline_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "baseline_id": "static_stale_memory",
            "required_role": "naive stale semantic memory baseline",
            "m190_status": "still_required_for_main_table",
            "pressure": "Shows whether old memory alone creates dead-end search.",
        },
        {
            "version": VERSION,
            "baseline_id": PROTECTED_POLICY,
            "required_role": "protected current-evidence baseline",
            "m190_status": "current_safe_execution_default",
            "pressure": "Any H001 policy must beat or explain tradeoff against this baseline.",
        },
        {
            "version": VERSION,
            "baseline_id": "no_source_pool_expansion_detector_confidence_v0",
            "required_role": "candidate-generation ablation",
            "m190_status": "must_be_materialized_in_m191_or_later",
            "pressure": "Tests whether source-pool acquisition contributes beyond confidence ranking.",
        },
        {
            "version": VERSION,
            "baseline_id": "ConceptGraphs_only_open_vocabulary_map",
            "required_role": "external map baseline",
            "m190_status": "still_required_for_top_tier_claim",
            "pressure": "Tests whether external map proposals solve the same source-coverage gap.",
        },
        {
            "version": VERSION,
            "baseline_id": "task_agnostic_reobservation",
            "required_role": "task-context ablation",
            "m190_status": "required_if_human_intent_is_repromoted",
            "pressure": "Tests whether human/task context changes source-acquisition decisions.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why is this not just detector-confidence ranking?",
            "answer": "M190 does not claim the ranking itself is new; the retained component is the semantic-map decision to acquire a source-pool before protected confidence ranking.",
            "evidence_pointer": "M177-M180 source-pool materialization and M182/M188 7/8 recoverable candidates.",
        },
        {
            "version": VERSION,
            "question": "Why not path-cost or transition-cost reranking?",
            "answer": "M185-M189 show cost-reranking ties SR but loses SPL because route cost is not cost-to-first-success.",
            "evidence_pointer": "M188 selected/protected proxy SPL 0.244850/0.292591; M189 root-cause rows.",
        },
        {
            "version": VERSION,
            "question": "Where is the semantic mapping contribution?",
            "answer": "The defensible contribution must be framed as map-exposed memory/source-coverage and re-observation decisions, not a generic list reranker.",
            "evidence_pointer": "M175-M177 source-coverage trigger to source-pool acquisition boundary.",
        },
        {
            "version": VERSION,
            "question": "Can we claim final real navigation improvement now?",
            "answer": "No. The current evidence is bounded smoke plus proxy diagnosis; M191 must define scale-up before more Docker execution.",
            "evidence_pointer": "M184 bounded Docker trajectory, M185/M188/M189 negative gates.",
        },
    ]


def build_readiness_gate_rows(
    m184_cov: dict[str, Any],
    m188_cov: dict[str, Any],
    m189_cov: dict[str, Any],
) -> list[dict[str, Any]]:
    inputs_ready = bool_all(
        [
            m184_cov.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready",
            m188_cov.get("status") == "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_ready",
            m189_cov.get("status") == "e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_ready",
        ]
    )
    protected_beats_repair = (
        (finite_float(m188_cov.get("protected_primary_spl_proxy_mean")) or -1.0)
        > (finite_float(m188_cov.get("selected_primary_spl_proxy_mean")) or -1.0)
    )
    return [
        {
            "version": VERSION,
            "gate_id": "input_artifacts_ready",
            "status": "pass" if inputs_ready else "fail",
            "reason": "M184/M188/M189 required coverage statuses are ready." if inputs_ready else "Required input artifacts are missing or not ready.",
        },
        {
            "version": VERSION,
            "gate_id": "transition_repair_positive_claim",
            "status": "fail" if protected_beats_repair else "warning",
            "reason": "Protected detector confidence has higher proxy SPL than transition repair.",
        },
        {
            "version": VERSION,
            "gate_id": "source_pool_component_boundary",
            "status": "pass" if m189_cov.get("source_pool_candidate_generation_kept") else "fail",
            "reason": "M189 keeps source-pool generation and rejects only the repair ranking.",
        },
        {
            "version": VERSION,
            "gate_id": "immediate_docker_trajectory_launch",
            "status": "fail",
            "reason": "No new ranking policy passed the proxy gate; launch would be conclusion-fitting.",
        },
        {
            "version": VERSION,
            "gate_id": "scale_contract_readiness",
            "status": "pass" if inputs_ready else "fail",
            "reason": "The next valid step is a scale-up contract around source-pool acquisition plus protected confidence.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "source-pool candidate-source expansion is retained",
            "allowed": True,
            "boundary": "Allowed only as a diagnostic method component that addresses source coverage before confidence ranking.",
        },
        {
            "version": VERSION,
            "claim": "transition-cost repair improves navigation/search",
            "allowed": False,
            "boundary": "M188/M189 reject it; it can appear only as a negative ablation and motivation for success-likelihood/source-acquisition design.",
        },
        {
            "version": VERSION,
            "claim": "protected detector confidence is the current execution default",
            "allowed": True,
            "boundary": "Allowed as a protected baseline/default, not as the paper's contribution.",
        },
        {
            "version": VERSION,
            "claim": "final real navigation SR/SPL improvement",
            "allowed": False,
            "boundary": "Requires M191 scale contract and later Docker trajectory execution on a larger heldout denominator.",
        },
        {
            "version": VERSION,
            "claim": "final real RGB-D/open-vocabulary robustness",
            "allowed": False,
            "boundary": "Requires external proposal/map baselines, heldout transfer, and robust detector artifact comparison.",
        },
        {
            "version": VERSION,
            "claim": "human intent as main contribution",
            "allowed": False,
            "boundary": "E006-M08 remains negative; task context can remain secondary unless E006-M09 redesign passes.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "selected_next_unit",
            "selected_next_unit": NEXT_UNIT,
            "trajectory_execution_now": False,
            "long_job_launch_now": False,
            "reason": "Scale-up must be specified around candidate-source expansion and protected confidence before new Docker runs.",
        },
        {
            "version": VERSION,
            "decision_id": "method_family_boundary",
            "selected_method_family": "source_pool_acquisition_plus_protected_confidence_execution",
            "rejected_method_family": "within_pool_transition_cost_reranking",
            "reason": "The failure diagnosis forces acquisition/source coverage as the next method surface rather than more local reranking.",
        },
    ]


def write_report(
    coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    report = f"""# E008-M190 Source-Pool Protected-Confidence Method Boundary

Generated: {datetime.now().isoformat(timespec="seconds")}

## Status

- Status: `{coverage["status"]}`
- Kept component: `{SOURCE_POOL_COMPONENT}`
- Safe execution default: `{PROTECTED_POLICY}`
- Rejected repair policy: `{REJECTED_REPAIR_POLICY}`
- Selected next unit: {coverage["selected_next_unit"]}

## 사실

- M184 protected detector-confidence Docker `SR` / `SPL`: {fmt(coverage["protected_docker_sr"])} / {fmt(coverage["protected_docker_spl"])}
- M188 selected repair proxy `SR` / `SPL`: {fmt(coverage["selected_proxy_sr"])} / {fmt(coverage["selected_proxy_spl"])}
- M188 protected proxy `SR` / `SPL`: {fmt(coverage["protected_proxy_sr"])} / {fmt(coverage["protected_proxy_spl"])}
- M189 same-success proposal rows: {coverage["same_success_proposal_rows"]}
- M189 selected delayed/costlier rows: {coverage["selected_delayed_or_costlier_rows"]}
- M189 shared source-coverage/localization gap rows: {coverage["shared_source_coverage_or_localization_gap_rows"]}

## Method Boundary

{table(method_rows, ["component_or_policy", "role", "decision", "paper_claim_status", "trajectory_execution_now"])}

## Claim Evidence

{table(claim_rows, ["claim_id", "status", "claim_boundary"])}

## Readiness Gates

{table(readiness_rows, ["gate_id", "status", "reason"])}

## Route Decision

{table(route_rows, ["decision_id", "selected_next_unit", "trajectory_execution_now", "long_job_launch_now", "reason"])}

## 논문 주장

M190 supports only a method-boundary claim: source-pool candidate-source expansion remains useful, but execution should default to protected detector confidence until a stronger success-likelihood policy is proven. It does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or human intent as a main claim.

## 에이전트 추론

The principle-driven next step is scale-up of source acquisition, not another local reranker. M188/M189 show that transition-cost optimization changes order without adding recovery and can reduce cost-to-first-success. A new Docker trajectory launch before a fixed scale contract would overfit the current 8-episode diagnostic.
"""
    write_text(OUT_ROOT / "report.md", report)


def main() -> None:
    m184_cov = read_json(M184_ROOT / "coverage.json")
    m188_cov = read_json(M188_ROOT / "coverage.json")
    m189_cov = read_json(M189_ROOT / "coverage.json")
    m184_metric_rows = read_jsonl(M184_ROOT / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    m188_aggregate_rows = read_jsonl(M188_ROOT / "aggregate_policy_goal_metric_rows.jsonl")
    m189_root_rows = read_jsonl(M189_ROOT / "root_cause_rows.jsonl")
    m189_method_rows = read_jsonl(M189_ROOT / "method_decision_rows.jsonl")

    m184_agg = aggregate_by_policy(m184_metric_rows)
    m188_agg = aggregate_by_policy(m188_aggregate_rows)

    input_ready = bool_all(
        [
            m184_cov.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready",
            m188_cov.get("status") == "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_ready",
            m189_cov.get("status") == "e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_ready",
            bool(m184_agg.get(PROTECTED_POLICY)),
            bool(m188_agg.get(PROTECTED_POLICY)),
            bool(m188_agg.get(REJECTED_REPAIR_POLICY)),
            bool(m189_root_rows),
            bool(m189_method_rows),
        ]
    )

    method_rows = build_method_boundary_rows(m184_agg, m188_agg)
    claim_rows = build_claim_evidence_rows(m184_agg, m188_cov, m189_cov)
    scale_rows = build_scale_decision_rows()
    baseline_rows = build_baseline_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    readiness_rows = build_readiness_gate_rows(m184_cov, m188_cov, m189_cov)
    route_rows = build_route_decision_rows()
    claim_boundary_rows = build_claim_boundary_rows()

    protected_exec = m184_agg.get(PROTECTED_POLICY, {})
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_m184_status": m184_cov.get("status"),
        "input_m188_status": m188_cov.get("status"),
        "input_m189_status": m189_cov.get("status"),
        "input_artifacts_ready": input_ready,
        "kept_method_component": SOURCE_POOL_COMPONENT,
        "safe_execution_default_policy_id": PROTECTED_POLICY,
        "rejected_repair_policy_id": REJECTED_REPAIR_POLICY,
        "rejected_path_policy_id": REJECTED_PATH_POLICY,
        "protected_docker_sr": protected_exec.get("SR"),
        "protected_docker_spl": protected_exec.get("SPL"),
        "protected_docker_candidate_visits_mean": protected_exec.get("CandidateVisits_mean"),
        "selected_proxy_sr": m188_cov.get("selected_primary_proxy_sr"),
        "selected_proxy_spl": m188_cov.get("selected_primary_spl_proxy_mean"),
        "protected_proxy_sr": m188_cov.get("protected_primary_proxy_sr"),
        "protected_proxy_spl": m188_cov.get("protected_primary_spl_proxy_mean"),
        "same_success_proposal_rows": m189_cov.get("same_success_proposal_rows"),
        "selected_delayed_or_costlier_rows": m189_cov.get("same_success_delayed_or_costlier_rows"),
        "selected_cheaper_route_rows": m189_cov.get("same_success_cheaper_route_rows"),
        "shared_source_coverage_or_localization_gap_rows": m189_cov.get("shared_gap_rows"),
        "transition_repair_positive_claim_supported": False,
        "source_pool_candidate_generation_kept": True,
        "protected_detector_confidence_execution_default": True,
        "scale_up_required": True,
        "trajectory_execution_now": False,
        "long_job_launch_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_rgbd_open_vocabulary_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    write_json(OUT_ROOT / "coverage.json", coverage)
    write_json(DATA_OUT_ROOT / "coverage.json", coverage)
    write_jsonl(OUT_ROOT / "method_boundary_rows.jsonl", method_rows)
    write_jsonl(OUT_ROOT / "claim_evidence_rows.jsonl", claim_rows)
    write_jsonl(OUT_ROOT / "scale_decision_rows.jsonl", scale_rows)
    write_jsonl(OUT_ROOT / "baseline_boundary_rows.jsonl", baseline_rows)
    write_jsonl(OUT_ROOT / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(OUT_ROOT / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(OUT_ROOT / "route_decision_rows.jsonl", route_rows)
    write_jsonl(OUT_ROOT / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_report(coverage, method_rows, claim_rows, readiness_rows, route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    if not input_ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
