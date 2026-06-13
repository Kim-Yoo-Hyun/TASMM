#!/usr/bin/env python3
"""Decompose M185 source-pool protected-baseline failure and fix the next repair contract."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M183_DIR = EXP_ROOT / "artifacts" / "E008-M183_docker_trajectory_execution_contract_preflight_v0"
M184_DIR = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"
M185_DIR = EXP_ROOT / "artifacts" / "E008-M185_protected_detector_confidence_interpretation_scale_decision_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M186_source_pool_protected_baseline_failure_decomposition_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M186_source_pool_protected_baseline_failure_decomposition_v0"
)

VERSION = "e008_m186_source_pool_protected_baseline_failure_decomposition_v0"
READY_STATUS = "e008_m186_source_pool_protected_baseline_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m186_source_pool_protected_baseline_failure_decomposition_blocked"
NEXT_UNIT = "E008-M187 source-pool confidence-protected transition-cost repair row materialization"

METHOD_POLICY = "path_cost_ascending_reachable_subset_v0"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"
CONFIDENCE_ALL = "detector_confidence_all_candidates_v0"
REPAIR_POLICY = "confidence_protected_transition_cost_policy_v1"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


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
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def metric_by_episode(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in metric_rows:
        if row.get("metric_scope") == "scan_task_policy":
            grouped[str(row.get("adapter_episode_id"))][str(row.get("policy_id"))] = row
    return grouped


def policy_aggregates(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def attempts_by_episode_policy(attempt_rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in attempt_rows:
        grouped[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def candidates_by_episode_policy(candidate_rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)
    return {
        key: sorted(value, key=lambda row: int(row.get("visit_rank") or 10**9))
        for key, value in grouped.items()
    }


def first_success(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("eval_success"):
            return row
    return {}


def prefix_before_success(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("eval_success"):
            break
        out.append(row)
    return out


def classify_episode(method: dict[str, Any], protected: dict[str, Any]) -> str:
    delta_sr = delta(method.get("SR"), protected.get("SR")) or 0.0
    delta_spl = delta(method.get("SPL"), protected.get("SPL")) or 0.0
    delta_visits = delta(method.get("CandidateVisits"), protected.get("CandidateVisits")) or 0.0
    delta_path = delta(method.get("PathLengthM"), protected.get("PathLengthM")) or 0.0
    if delta_sr < -1e-9:
        return "method_loses_sr"
    if delta_sr > 1e-9:
        return "method_gains_sr"
    if method.get("SR") == 0 and protected.get("SR") == 0:
        return "shared_unrecovered_case"
    if delta_spl > 1e-9 and delta_visits <= 0:
        return "useful_path_cost_case"
    if delta_spl < -1e-9 and delta_visits > 0 and delta_path > 0:
        return "extra_visits_and_path_detour"
    if delta_spl < -1e-9 and delta_path > 0:
        return "path_detour_without_visit_increase"
    if delta_spl < -1e-9:
        return "spl_regression"
    return "tie"


def build_policy_summary_rows(aggregates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    protected = aggregates.get(PROTECTED_BASELINE, {})
    out: list[dict[str, Any]] = []
    for policy_id in [CONFIDENCE_ALL, PROTECTED_BASELINE, TRADEOFF_POLICY, METHOD_POLICY]:
        row = aggregates.get(policy_id, {})
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_task_policy_rows": row.get("scan_task_policy_rows"),
                "success_rows": row.get("success_rows"),
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "StopRank_mean_over_success": row.get("StopRank_mean_over_success"),
                "delta_SR_vs_protected": delta(row.get("SR"), protected.get("SR")),
                "delta_SPL_vs_protected": delta(row.get("SPL"), protected.get("SPL")),
                "delta_PathLengthM_mean_vs_protected": delta(
                    row.get("PathLengthM_mean"), protected.get("PathLengthM_mean")
                ),
                "delta_CandidateVisits_mean_vs_protected": delta(
                    row.get("CandidateVisits_mean"), protected.get("CandidateVisits_mean")
                ),
                "interpretation": "protected_baseline"
                if policy_id == PROTECTED_BASELINE
                else ("failed_selected_method" if policy_id == METHOD_POLICY else "comparison_policy"),
            }
        )
    return out


def build_attempt_decomposition_rows(
    metric_groups: dict[str, dict[str, dict[str, Any]]],
    attempt_groups: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode_id in sorted(metric_groups):
        for policy_id in [PROTECTED_BASELINE, METHOD_POLICY, TRADEOFF_POLICY]:
            metric = metric_groups[episode_id].get(policy_id, {})
            attempts = attempt_groups.get((episode_id, policy_id), [])
            prefix = prefix_before_success(attempts)
            success = first_success(attempts)
            proxy_values = [finite_float(row.get("source_to_candidate_path_cost_m")) for row in prefix]
            segment_values = [finite_float(row.get("segment_geodesic_m")) for row in prefix]
            under_values = [
                (seg - proxy)
                for seg, proxy in zip(segment_values, proxy_values)
                if seg is not None and proxy is not None
            ]
            low_proxy_detours = [
                row
                for row in prefix
                if (finite_float(row.get("source_to_candidate_path_cost_m")) or 0.0) <= 1.0
                and (finite_float(row.get("segment_geodesic_m")) or 0.0) >= 2.0
            ]
            rows.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": episode_id,
                    "benchmark_row_uid": metric.get("benchmark_row_uid"),
                    "scene_key": metric.get("scene_key"),
                    "object_category": metric.get("object_category"),
                    "policy_id": policy_id,
                    "SR": metric.get("SR"),
                    "SPL": metric.get("SPL"),
                    "PathLengthM": metric.get("PathLengthM"),
                    "CandidateVisits": metric.get("CandidateVisits"),
                    "StopRank": metric.get("StopRank"),
                    "pre_success_nonhit_attempts": len(prefix),
                    "success_proposal_uid": metric.get("success_proposal_uid"),
                    "success_source_to_candidate_path_cost_m": success.get("source_to_candidate_path_cost_m"),
                    "success_segment_geodesic_m": success.get("segment_geodesic_m"),
                    "pre_success_source_proxy_mean": mean(proxy_values),
                    "pre_success_executed_segment_mean": mean(segment_values),
                    "pre_success_proxy_underestimation_mean": mean(under_values),
                    "low_source_proxy_detour_rows": len(low_proxy_detours),
                    "claim_boundary": "Attempt decomposition uses executed trajectory diagnostics after M184; it is not a policy input.",
                }
            )
    return rows


def build_episode_delta_rows(
    metric_groups: dict[str, dict[str, dict[str, Any]]],
    attempt_groups: dict[tuple[str, str], list[dict[str, Any]]],
    candidate_groups: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode_id in sorted(metric_groups):
        method = metric_groups[episode_id].get(METHOD_POLICY, {})
        protected = metric_groups[episode_id].get(PROTECTED_BASELINE, {})
        tradeoff = metric_groups[episode_id].get(TRADEOFF_POLICY, {})
        method_attempts = attempt_groups.get((episode_id, METHOD_POLICY), [])
        protected_attempts = attempt_groups.get((episode_id, PROTECTED_BASELINE), [])
        method_success = first_success(method_attempts)
        protected_success = first_success(protected_attempts)
        method_top5 = {row.get("proposal_uid") for row in candidate_groups.get((episode_id, METHOD_POLICY), [])[:5]}
        protected_top5 = {
            row.get("proposal_uid") for row in candidate_groups.get((episode_id, PROTECTED_BASELINE), [])[:5]
        }
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "benchmark_row_uid": method.get("benchmark_row_uid") or protected.get("benchmark_row_uid"),
                "scene_key": method.get("scene_key") or protected.get("scene_key"),
                "object_category": method.get("object_category") or protected.get("object_category"),
                "method_SR": method.get("SR"),
                "protected_SR": protected.get("SR"),
                "method_SPL": method.get("SPL"),
                "protected_SPL": protected.get("SPL"),
                "tradeoff_SPL": tradeoff.get("SPL"),
                "method_PathLengthM": method.get("PathLengthM"),
                "protected_PathLengthM": protected.get("PathLengthM"),
                "method_CandidateVisits": method.get("CandidateVisits"),
                "protected_CandidateVisits": protected.get("CandidateVisits"),
                "method_StopRank": method.get("StopRank"),
                "protected_StopRank": protected.get("StopRank"),
                "delta_SR": delta(method.get("SR"), protected.get("SR")),
                "delta_SPL": delta(method.get("SPL"), protected.get("SPL")),
                "delta_PathLengthM": delta(method.get("PathLengthM"), protected.get("PathLengthM")),
                "delta_CandidateVisits": delta(method.get("CandidateVisits"), protected.get("CandidateVisits")),
                "success_proposal_changed": method.get("success_proposal_uid")
                != protected.get("success_proposal_uid"),
                "method_success_source_proxy_m": method_success.get("source_to_candidate_path_cost_m"),
                "protected_success_source_proxy_m": protected_success.get("source_to_candidate_path_cost_m"),
                "method_success_segment_m": method_success.get("segment_geodesic_m"),
                "protected_success_segment_m": protected_success.get("segment_geodesic_m"),
                "top5_overlap_with_protected": len(method_top5 & protected_top5),
                "classification": classify_episode(method, protected),
            }
        )
    return rows


def summarize_episode_delta(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "episode_rows": len(rows),
        "classification_counts": dict(sorted(Counter(str(row.get("classification")) for row in rows).items())),
        "method_worse_spl_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) < -1e-9 for row in rows),
        "method_better_spl_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) > 1e-9 for row in rows),
        "method_tie_spl_rows": sum(abs(finite_float(row.get("delta_SPL")) or 0.0) <= 1e-9 for row in rows),
        "success_proposal_changed_rows": sum(bool(row.get("success_proposal_changed")) for row in rows),
        "delta_SPL_mean": mean([finite_float(row.get("delta_SPL")) for row in rows]),
        "delta_PathLengthM_mean": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
        "delta_CandidateVisits_mean": mean([finite_float(row.get("delta_CandidateVisits")) for row in rows]),
        "top5_overlap_mean": mean([finite_float(row.get("top5_overlap_with_protected")) for row in rows]),
    }


def build_root_cause_rows(summary: dict[str, Any], attempt_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    method_attempts = [row for row in attempt_rows if row.get("policy_id") == METHOD_POLICY]
    protected_attempts = [row for row in attempt_rows if row.get("policy_id") == PROTECTED_BASELINE]
    method_under = mean([finite_float(row.get("pre_success_proxy_underestimation_mean")) for row in method_attempts])
    protected_under = mean([finite_float(row.get("pre_success_proxy_underestimation_mean")) for row in protected_attempts])
    return [
        {
            "version": VERSION,
            "root_cause_id": "source_proxy_cost_is_not_execution_cost",
            "status": "supported",
            "evidence": (
                f"method pre-success proxy-underestimation mean={fmt(method_under)} vs "
                f"protected={fmt(protected_under)}; method loses SPL on {summary['method_worse_spl_rows']} / "
                f"{summary['episode_rows']} episodes."
            ),
            "principle": "Ranking by source-to-candidate path cost is myopic once the robot executes a sequence of stops from its current state.",
        },
        {
            "version": VERSION,
            "root_cause_id": "path_cost_order_delays_success_candidates",
            "status": "supported",
            "evidence": (
                f"delta CandidateVisits mean={fmt(summary['delta_CandidateVisits_mean'])}; "
                f"delta PathLengthM mean={fmt(summary['delta_PathLengthM_mean'])}."
            ),
            "principle": "Path-cost ordering can visit many low-source-cost decoys before the high-confidence target candidate.",
        },
        {
            "version": VERSION,
            "root_cause_id": "source_pool_generation_is_useful_but_ranking_is_not",
            "status": "supported",
            "evidence": "M182 proxy recovery is 7 / 8 and M184 SR is 0.875, but M185 rejects scale-up on SPL.",
            "principle": "Candidate-source expansion should be kept, while the ranking policy must be confidence-protected and trajectory-aware.",
        },
    ]


def build_repair_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field, reason in [
        ("detector confidence / selection_score", "primary reliability signal and protected baseline anchor"),
        ("candidate_stop_position_m / snapped_position_m", "needed for path planning and execution"),
        ("robot current position / episode start position", "known robot state; needed for transition-cost planning"),
        ("navmesh path cost from current state to candidate", "online transition cost, not ObjectNav target information"),
        ("object_category / open-vocabulary query label", "task query for label compatibility"),
        ("source_pool route id and observation source metadata", "source-coverage provenance and debugging"),
    ]:
        rows.append(
            {
                "version": VERSION,
                "repair_policy_id": REPAIR_POLICY,
                "row_type": "allowed_input",
                "field": field,
                "allowed_for_policy": True,
                "reason": reason,
            }
        )
    for field in [
        "ObjectNav goal position",
        "ObjectNav viewpoint position",
        "candidate-to-goal distance",
        "candidate-to-nearest-viewpoint distance",
        "primary_eval_hit",
        "success proposal uid",
        "M184 trajectory outcome labels",
    ]:
        rows.append(
            {
                "version": VERSION,
                "repair_policy_id": REPAIR_POLICY,
                "row_type": "blocked_input",
                "field": field,
                "allowed_for_policy": False,
                "reason": "evaluation-only field; using it would leak target information into policy ranking",
            }
        )
    for component, rule in [
        (
            "confidence_protection",
            "Preserve detector-confidence ordering across 0.05 confidence bins; transition cost may only reorder inside a bin.",
        ),
        (
            "online_transition_cost",
            "Use current-state-to-candidate navmesh path cost for tie-breaking; do not rank by source-to-candidate proxy cost.",
        ),
        (
            "source_pool_keep",
            "Keep M177-M180 source-pool candidate expansion because it supplies recovered candidates for 7 / 8 proxy cases.",
        ),
        (
            "budget_guard",
            "Use the same full-ranked execution budget for comparability; report budget-5 only as a diagnostic.",
        ),
        (
            "protected_baseline_gate",
            "Next materialized policy must compare against detector_confidence_reachable_subset_v0 without changing denominator or metric thresholds.",
        ),
    ]:
        rows.append(
            {
                "version": VERSION,
                "repair_policy_id": REPAIR_POLICY,
                "row_type": "method_component",
                "component": component,
                "rule": rule,
                "derived_from_failure": True,
            }
        )
    return rows


def build_readiness_gate_rows(
    m184_cov: dict[str, Any],
    m185_cov: dict[str, Any],
    episode_summary: dict[str, Any],
    repair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed_rows = [row for row in repair_rows if row.get("row_type") == "allowed_input"]
    blocked_rows = [row for row in repair_rows if row.get("row_type") == "blocked_input"]
    component_rows = [row for row in repair_rows if row.get("row_type") == "method_component"]
    return [
        {
            "version": VERSION,
            "gate_id": "m184_trajectory_ready",
            "status": "pass" if m184_cov.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready" else "fail",
            "evidence": f"M184 status={m184_cov.get('status')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m185_scale_rejected_for_spl",
            "status": "pass" if m185_cov.get("scale_up_recommended") is False else "fail",
            "evidence": (
                f"scale_up_recommended={m185_cov.get('scale_up_recommended')}; "
                f"method SPL={m185_cov.get('decision_method_SPL')}; protected SPL={m185_cov.get('decision_protected_baseline_SPL')}."
            ),
        },
        {
            "version": VERSION,
            "gate_id": "episode_delta_materialized",
            "status": "pass" if int(episode_summary.get("episode_rows") or 0) > 0 else "fail",
            "evidence": f"episode rows={episode_summary.get('episode_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "failure_principle_identified",
            "status": "pass"
            if int(episode_summary.get("method_worse_spl_rows") or 0) > int(episode_summary.get("method_better_spl_rows") or 0)
            else "fail",
            "evidence": (
                f"worse SPL rows={episode_summary.get('method_worse_spl_rows')}; "
                f"better SPL rows={episode_summary.get('method_better_spl_rows')}."
            ),
        },
        {
            "version": VERSION,
            "gate_id": "repair_contract_complete",
            "status": "pass" if allowed_rows and blocked_rows and component_rows else "fail",
            "evidence": f"allowed={len(allowed_rows)}; blocked={len(blocked_rows)}; components={len(component_rows)}.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_pool_failure_decomposition",
            "supported": True,
            "claim_boundary": "M186 supports a diagnosis that source-pool path-cost ranking loses SPL against protected detector confidence.",
        },
        {
            "version": VERSION,
            "claim_id": "repaired_policy_performance",
            "supported": False,
            "claim_boundary": "M186 defines the next repair contract only; M187+ must materialize/evaluate it.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final SR/SPL claim requires repaired policy execution at larger heldout scale and external navigation/search baselines.",
        },
    ]


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "materialize_repaired_source_pool_policy" if ready else "repair_m186_failure_decomposition",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M186 source-pool failure decomposition",
            "repair_policy_id": REPAIR_POLICY,
            "launch_long_job_now": False,
            "reason": (
                "M186 identifies source-proxy ranking as the failure principle and fixes a confidence-protected "
                "transition-cost repair contract."
                if ready
                else "M186 readiness gates failed."
            ),
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    root_cause_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    repair_components = [row for row in repair_rows if row.get("row_type") == "method_component"]
    return "\n".join(
        [
            "# E008-M186 Source-Pool Protected-Baseline Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M184 status: `{coverage['m184_status']}`.",
            f"- M185 decision: `{coverage['m185_decision']}`.",
            f"- Method policy: `{METHOD_POLICY}`.",
            f"- Protected baseline: `{PROTECTED_BASELINE}`.",
            f"- Method worse `SPL` rows: {coverage['method_worse_spl_rows']} / {coverage['episode_rows']}.",
            f"- Mean delta `SPL`: {fmt(coverage['delta_SPL_mean'])}.",
            f"- Mean delta `PathLengthM`: {fmt(coverage['delta_PathLengthM_mean'])}.",
            f"- Mean delta `CandidateVisits`: {fmt(coverage['delta_CandidateVisits_mean'])}.",
            "",
            "## Policy Summary",
            "",
            table(
                policy_rows,
                [
                    "policy_id",
                    "SR",
                    "SPL",
                    "PathLengthM_mean",
                    "CandidateVisits_mean",
                    "delta_SPL_vs_protected",
                    "delta_CandidateVisits_mean_vs_protected",
                ],
            ),
            "",
            "## Episode Delta",
            "",
            table(
                episode_rows,
                [
                    "adapter_episode_id",
                    "object_category",
                    "classification",
                    "delta_SPL",
                    "delta_PathLengthM",
                    "delta_CandidateVisits",
                    "method_StopRank",
                    "protected_StopRank",
                    "top5_overlap_with_protected",
                ],
            ),
            "",
            "## Root Causes",
            "",
            table(root_cause_rows, ["root_cause_id", "status", "principle", "evidence"]),
            "",
            "## Repair Contract",
            "",
            table(repair_components, ["component", "rule", "derived_from_failure"]),
            "",
            "## Readiness Gates",
            "",
            table(gate_rows, ["gate_id", "status", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M186 is a failure-decomposition and contract unit, not a positive performance result.",
            "- The next policy must keep detector confidence protected and use transition cost only as a constrained routing signal.",
            "- Direct source-pool scale-up remains blocked until the repaired policy is materialized and evaluated.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m184_cov = read_json(M184_DIR / "coverage.json")
    m185_cov = read_json(M185_DIR / "coverage.json")
    metric_rows = read_jsonl(M184_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    attempt_rows_raw = read_jsonl(M184_DIR / "dynamic_stale_trajectory_attempt_rows.jsonl")
    candidate_rows_raw = read_jsonl(M183_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")

    metric_groups = metric_by_episode(metric_rows)
    attempt_groups = attempts_by_episode_policy(attempt_rows_raw)
    candidate_groups = candidates_by_episode_policy(candidate_rows_raw)
    aggregates = policy_aggregates(metric_rows)

    policy_rows = build_policy_summary_rows(aggregates)
    episode_rows = build_episode_delta_rows(metric_groups, attempt_groups, candidate_groups)
    attempt_rows = build_attempt_decomposition_rows(metric_groups, attempt_groups)
    episode_summary = summarize_episode_delta(episode_rows)
    root_cause_rows = build_root_cause_rows(episode_summary, attempt_rows)
    repair_rows = build_repair_contract_rows()
    gate_rows = build_readiness_gate_rows(m184_cov, m185_cov, episode_summary, repair_rows)
    ready = not any(row.get("status") == "fail" for row in gate_rows)
    route_rows = build_route_rows(ready)
    claim_rows = build_claim_boundary_rows()

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m184_status": m184_cov.get("status"),
        "m185_status": m185_cov.get("status"),
        "m185_decision": m185_cov.get("decision_decision"),
        "method_policy_id": METHOD_POLICY,
        "protected_baseline_id": PROTECTED_BASELINE,
        "repair_policy_id": REPAIR_POLICY,
        "episode_rows": episode_summary.get("episode_rows"),
        "method_worse_spl_rows": episode_summary.get("method_worse_spl_rows"),
        "method_better_spl_rows": episode_summary.get("method_better_spl_rows"),
        "method_tie_spl_rows": episode_summary.get("method_tie_spl_rows"),
        "success_proposal_changed_rows": episode_summary.get("success_proposal_changed_rows"),
        "delta_SPL_mean": episode_summary.get("delta_SPL_mean"),
        "delta_PathLengthM_mean": episode_summary.get("delta_PathLengthM_mean"),
        "delta_CandidateVisits_mean": episode_summary.get("delta_CandidateVisits_mean"),
        "top5_overlap_mean": episode_summary.get("top5_overlap_mean"),
        "policy_summary_rows": len(policy_rows),
        "episode_delta_rows": len(episode_rows),
        "attempt_decomposition_rows": len(attempt_rows),
        "root_cause_rows": len(root_cause_rows),
        "repair_contract_rows": len(repair_rows),
        "readiness_gate_rows": len(gate_rows),
        "readiness_gate_fail_rows": sum(1 for row in gate_rows if row.get("status") == "fail"),
        "positive_navigation_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "episode_delta_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "attempt_decomposition_rows.jsonl", attempt_rows)
        write_jsonl(output_dir / "root_cause_rows.jsonl", root_cause_rows)
        write_jsonl(output_dir / "repair_contract_rows.jsonl", repair_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_rows, episode_rows, root_cause_rows, repair_rows, gate_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
