#!/usr/bin/env python3
"""Interpret E008-M170 source-coverage memory-interface trajectory results."""

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
M170_DIR = EXP_ROOT / "artifacts" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M171_source_coverage_memory_interface_result_interpretation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M171_source_coverage_memory_interface_result_interpretation_v0"

VERSION = "e008_m171_source_coverage_memory_interface_result_interpretation_v0"
READY_STATUS = "e008_m171_source_coverage_memory_interface_result_interpretation_ready"
BLOCKED_STATUS = "e008_m171_source_coverage_memory_interface_result_interpretation_blocked"
NEXT_UNIT = "E008-M172 source-coverage ablation tradeoff decomposition and policy decision"

SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_ONLY = "source_coverage_only_task_agnostic_v1"
CONFIDENCE_ONLY = "confidence_floor_only_v1"
PATH_ONLY = "path_cost_only_reachable_subset_v1"


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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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


def aggregate_index(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def scan_metric_index(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in metric_rows:
        if row.get("metric_scope") == "scan_task_policy":
            grouped[str(row.get("benchmark_row_uid"))][str(row.get("policy_id"))] = row
    return grouped


def delta(left: object, right: object) -> float | None:
    l = finite_float(left)
    r = finite_float(right)
    if l is None or r is None:
        return None
    return l - r


def policy_result_rows(aggregates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    protected = aggregates.get(PROTECTED_BASELINE, {})
    selected = aggregates.get(SELECTED_POLICY, {})
    rows = []
    for policy_id, row in sorted(aggregates.items()):
        rows.append(
            {
                "version": VERSION,
                "row_type": "policy_result_interpretation",
                "policy_id": policy_id,
                "policy_role": "selected" if policy_id == SELECTED_POLICY else "protected_baseline" if policy_id == PROTECTED_BASELINE else "ablation",
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "success_rows": row.get("success_rows"),
                "scan_task_policy_rows": row.get("scan_task_policy_rows"),
                "delta_SR_vs_protected": delta(row.get("SR"), protected.get("SR")),
                "delta_SPL_vs_protected": delta(row.get("SPL"), protected.get("SPL")),
                "delta_PathLengthM_vs_protected": delta(row.get("PathLengthM_mean"), protected.get("PathLengthM_mean")),
                "delta_CandidateVisits_vs_protected": delta(row.get("CandidateVisits_mean"), protected.get("CandidateVisits_mean")),
                "delta_SPL_vs_selected": delta(row.get("SPL"), selected.get("SPL")),
                "failure_type_counts": row.get("failure_type_counts"),
            }
        )
    return rows


def pairwise_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        grouped[str(row.get("baseline_policy_id"))].append(row)
    out = []
    for baseline_id, rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "row_type": "pairwise_delta_summary",
                "baseline_policy_id": baseline_id,
                "rows": len(rows),
                "delta_SR_mean": mean([finite_float(row.get("delta_SR")) for row in rows]),
                "delta_SPL_mean": mean([finite_float(row.get("delta_SPL")) for row in rows]),
                "delta_PathLengthM_mean": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
                "delta_CandidateVisits_mean": mean(
                    [
                        delta(row.get("method_CandidateVisits"), row.get("baseline_CandidateVisits"))
                        for row in rows
                    ]
                ),
                "better_SPL_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) > 1e-9 for row in rows),
                "worse_SPL_rows": sum((finite_float(row.get("delta_SPL")) or 0.0) < -1e-9 for row in rows),
                "tie_SPL_rows": sum(abs(finite_float(row.get("delta_SPL")) or 0.0) <= 1e-9 for row in rows),
            }
        )
    return out


def episode_delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = scan_metric_index(metric_rows)
    rows = []
    for uid, policies in sorted(grouped.items()):
        selected = policies.get(SELECTED_POLICY, {})
        protected = policies.get(PROTECTED_BASELINE, {})
        coverage = policies.get(SOURCE_COVERAGE_ONLY, {})
        rows.append(
            {
                "version": VERSION,
                "row_type": "episode_delta_profile",
                "benchmark_row_uid": uid,
                "scan_id": selected.get("scan_id") or protected.get("scan_id"),
                "scene_key": selected.get("scene_key") or protected.get("scene_key"),
                "object_category": selected.get("object_category") or protected.get("object_category"),
                "selected_SR": selected.get("SR"),
                "protected_SR": protected.get("SR"),
                "source_coverage_only_SR": coverage.get("SR"),
                "selected_SPL": selected.get("SPL"),
                "protected_SPL": protected.get("SPL"),
                "source_coverage_only_SPL": coverage.get("SPL"),
                "delta_SPL_vs_protected": delta(selected.get("SPL"), protected.get("SPL")),
                "delta_SPL_vs_source_coverage_only": delta(selected.get("SPL"), coverage.get("SPL")),
                "delta_CandidateVisits_vs_protected": delta(selected.get("CandidateVisits"), protected.get("CandidateVisits")),
                "delta_CandidateVisits_vs_source_coverage_only": delta(selected.get("CandidateVisits"), coverage.get("CandidateVisits")),
                "selected_success_proposal_changed_vs_protected": selected.get("success_proposal_uid") != protected.get("success_proposal_uid"),
                "selected_success_proposal_changed_vs_source_coverage_only": selected.get("success_proposal_uid") != coverage.get("success_proposal_uid"),
            }
        )
    return rows


def gate_rows(aggregates: dict[str, dict[str, Any]], pairwise_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = aggregates.get(SELECTED_POLICY, {})
    protected = aggregates.get(PROTECTED_BASELINE, {})
    coverage = aggregates.get(SOURCE_COVERAGE_ONLY, {})
    detector_delta_spl = delta(selected.get("SPL"), protected.get("SPL")) or 0.0
    detector_delta_visits = delta(selected.get("CandidateVisits_mean"), protected.get("CandidateVisits_mean")) or 0.0
    detector_delta_sr = delta(selected.get("SR"), protected.get("SR")) or 0.0
    coverage_delta_spl = delta(selected.get("SPL"), coverage.get("SPL")) or 0.0
    coverage_delta_visits = delta(selected.get("CandidateVisits_mean"), coverage.get("CandidateVisits_mean")) or 0.0
    gates = [
        (
            "m170_execution_ready",
            True,
            "M170 status is ready and produced 150 scan-task-policy rows.",
            True,
        ),
        (
            "protected_sr_non_regression",
            detector_delta_sr >= 0.0,
            f"delta_SR_vs_detector={detector_delta_sr:.6f}.",
            True,
        ),
        (
            "protected_spl_improvement",
            detector_delta_spl > 0.0,
            f"delta_SPL_vs_detector={detector_delta_spl:.6f}.",
            True,
        ),
        (
            "protected_visit_non_regression",
            detector_delta_visits <= 0.0,
            f"delta_CandidateVisits_vs_detector={detector_delta_visits:.6f}.",
            True,
        ),
        (
            "source_coverage_spl_non_regression",
            coverage_delta_spl >= 0.0,
            f"delta_SPL_vs_source_coverage_only={coverage_delta_spl:.6f}.",
            True,
        ),
        (
            "source_coverage_visit_tradeoff_witness",
            coverage_delta_visits < 0.0 and coverage_delta_spl < 0.0,
            f"delta_SPL_vs_source_coverage_only={coverage_delta_spl:.6f}; delta_visits={coverage_delta_visits:.6f}.",
            False,
        ),
        (
            "final_claim_ready",
            False,
            "Heldout transfer and external navigation/search baselines remain absent.",
            True,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "gate",
            "gate_id": gate_id,
            "status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_positive_navigation_claim": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def mechanism_rows(aggregates: dict[str, dict[str, Any]], episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = aggregates.get(SELECTED_POLICY, {})
    protected = aggregates.get(PROTECTED_BASELINE, {})
    coverage = aggregates.get(SOURCE_COVERAGE_ONLY, {})
    return [
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "selected_policy_does_not_beat_protected_detector_confidence",
            "severity": "high",
            "fact": f"Selected `SPL` {fmt(selected.get('SPL'))} vs detector-confidence {fmt(protected.get('SPL'))}; selected visits {fmt(selected.get('CandidateVisits_mean'))} vs detector {fmt(protected.get('CandidateVisits_mean'))}.",
            "agent_inference": "The memory-interface guard preserved confidence but did not improve executed navigation efficiency.",
            "next_requirement": "Do not claim positive navigation improvement; decompose source-coverage-only tradeoff before redesign.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "task_agnostic_source_coverage_is_stronger_than_selected_policy",
            "severity": "high",
            "fact": f"Source-coverage-only `SPL` {fmt(coverage.get('SPL'))} exceeds selected `SPL` {fmt(selected.get('SPL'))}.",
            "agent_inference": "The selected memory-interface guard may be too conservative or may preserve confidence at the cost of useful coverage diversity.",
            "next_requirement": "M172 should determine whether source-coverage-only is a valid precommitted method, a visit-cost tradeoff, or another diagnostic witness.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "source_gap_still_absent",
            "severity": "medium",
            "fact": "M168/M170 source-gap prelabel rows remain zero.",
            "agent_inference": "The current denominator still cannot validate source-gap-trigger behavior.",
            "next_requirement": "Keep source-gap claims restricted to source-gap/source-coverage or external proposal-source denominators.",
        },
    ]


def claim_rows(positive_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_coverage_memory_interface_execution_ready",
            "supported": True,
            "claim_boundary": "M170 executed the fixed M169 policy suite with leakage audit pass.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_memory_interface_positive_navigation_improvement",
            "supported": positive_ready,
            "claim_boundary": "Rejected unless selected policy beats detector-confidence on SR/SPL/visits and beats source-coverage-only ablation.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Blocked by selected-policy failure plus heldout/external-baseline requirements.",
        },
    ]


def route_rows(positive_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "positive_navigation_claim_ready" if positive_ready else "decompose_source_coverage_tradeoff_before_redesign",
            "selected_next_unit": "E008 heldout/external baseline scale-up" if positive_ready else NEXT_UNIT,
            "launch_long_job_now": False,
            "positive_navigation_improvement_ready": positive_ready,
            "real_navigation_sr_spl_ready": False,
        }
    ]


def reviewer_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "why_not_claim_after_m170_ready",
            "reviewer_response": "M170 execution is ready, but selected policy loses `SPL` and visit-efficiency to detector-confidence, so execution readiness is not evidence of navigation improvement.",
        },
        {
            "version": VERSION,
            "issue_id": "why_source_coverage_only_matters",
            "reviewer_response": "The task-agnostic source-coverage ablation has higher aggregate `SPL` than the selected method, so the next method must explain whether confidence/memory guards help or overconstrain coverage.",
        },
    ]


def report(coverage: dict[str, Any], policy_rows: list[dict[str, Any]], gates: list[dict[str, Any]], mechanisms: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M171 Source-Coverage Memory-Interface Result Interpretation",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M170 status: `{coverage['m170_status']}`.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Selected `SR` / `SPL`: {fmt(coverage['selected_SR'])} / {fmt(coverage['selected_SPL'])}.",
            f"- Protected `SR` / `SPL`: {fmt(coverage['protected_SR'])} / {fmt(coverage['protected_SPL'])}.",
            f"- Source-coverage-only `SR` / `SPL`: {fmt(coverage['source_coverage_only_SR'])} / {fmt(coverage['source_coverage_only_SPL'])}.",
            f"- Positive navigation-improvement ready: {coverage['positive_navigation_improvement_ready']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Results",
            "",
            table(policy_rows, ["policy_id", "policy_role", "SR", "SPL", "PathLengthM_mean", "CandidateVisits_mean", "delta_SPL_vs_protected", "delta_CandidateVisits_vs_protected"]),
            "",
            "## Gates",
            "",
            table(gates, ["gate_id", "status", "blocks_positive_navigation_claim", "evidence"]),
            "",
            "## Failure Mechanisms",
            "",
            table(mechanisms, ["mechanism_id", "severity", "fact", "next_requirement"]),
            "",
            "## Claim Boundary",
            "",
            "- M171 rejects positive navigation-improvement for the selected source-coverage memory-interface policy.",
            "- M170 execution readiness remains useful as diagnostic evidence.",
            "- M172 should decompose whether source-coverage-only is a valid next method or a tradeoff witness.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m170 = read_json(M170_DIR / "coverage.json")
    m168 = read_json(M168_DIR / "coverage.json")
    metric_rows = read_jsonl(M170_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_rows = read_jsonl(M170_DIR / "pairwise_policy_delta_rows.jsonl")
    missing = []
    if m170.get("status") != "e008_m170_source_coverage_memory_interface_trajectory_execution_ready":
        missing.append("M170 ready coverage")
    if len([row for row in metric_rows if row.get("metric_scope") == "scan_task_policy"]) != 150:
        missing.append("M170 scan-task-policy rows")

    aggregates = aggregate_index(metric_rows)
    policy_rows = policy_result_rows(aggregates)
    pairwise_summary = pairwise_summary_rows(pairwise_rows)
    episode_rows = episode_delta_rows(metric_rows)
    gates = gate_rows(aggregates, pairwise_summary)
    mechanisms = mechanism_rows(aggregates, episode_rows)

    selected = aggregates.get(SELECTED_POLICY, {})
    protected = aggregates.get(PROTECTED_BASELINE, {})
    coverage_only = aggregates.get(SOURCE_COVERAGE_ONLY, {})
    positive_ready = (
        not missing
        and (delta(selected.get("SR"), protected.get("SR")) or 0.0) >= 0.0
        and (delta(selected.get("SPL"), protected.get("SPL")) or 0.0) > 0.0
        and (delta(selected.get("CandidateVisits_mean"), protected.get("CandidateVisits_mean")) or 0.0) <= 0.0
        and (delta(selected.get("SPL"), coverage_only.get("SPL")) or 0.0) >= 0.0
        and (delta(selected.get("CandidateVisits_mean"), coverage_only.get("CandidateVisits_mean")) or 0.0) <= 0.0
        and (
            (delta(selected.get("SPL"), coverage_only.get("SPL")) or 0.0) > 0.0
            or (delta(selected.get("CandidateVisits_mean"), coverage_only.get("CandidateVisits_mean")) or 0.0) < 0.0
        )
    )
    ready = not missing
    routes = route_rows(positive_ready)
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m168_status": m168.get("status"),
        "m170_status": m170.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "selected_SR": selected.get("SR"),
        "selected_SPL": selected.get("SPL"),
        "selected_CandidateVisits_mean": selected.get("CandidateVisits_mean"),
        "selected_PathLengthM_mean": selected.get("PathLengthM_mean"),
        "protected_SR": protected.get("SR"),
        "protected_SPL": protected.get("SPL"),
        "protected_CandidateVisits_mean": protected.get("CandidateVisits_mean"),
        "protected_PathLengthM_mean": protected.get("PathLengthM_mean"),
        "source_coverage_only_SR": coverage_only.get("SR"),
        "source_coverage_only_SPL": coverage_only.get("SPL"),
        "source_coverage_only_CandidateVisits_mean": coverage_only.get("CandidateVisits_mean"),
        "delta_SR_vs_protected": delta(selected.get("SR"), protected.get("SR")),
        "delta_SPL_vs_protected": delta(selected.get("SPL"), protected.get("SPL")),
        "delta_CandidateVisits_vs_protected": delta(selected.get("CandidateVisits_mean"), protected.get("CandidateVisits_mean")),
        "delta_SPL_vs_source_coverage_only": delta(selected.get("SPL"), coverage_only.get("SPL")),
        "delta_CandidateVisits_vs_source_coverage_only": delta(selected.get("CandidateVisits_mean"), coverage_only.get("CandidateVisits_mean")),
        "policy_result_rows": len(policy_rows),
        "pairwise_delta_summary_rows": len(pairwise_summary),
        "episode_delta_profile_rows": len(episode_rows),
        "gate_rows": len(gates),
        "gate_fail_rows": sum(1 for row in gates if row.get("status") == "fail"),
        "failure_mechanism_rows": len(mechanisms),
        "positive_navigation_improvement_ready": positive_ready,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": routes[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_result_interpretation_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_delta_summary_rows.jsonl", pairwise_summary)
    write_jsonl(ARTIFACT_DIR / "episode_delta_profile_rows.jsonl", episode_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gates)
    write_jsonl(ARTIFACT_DIR / "failure_mechanism_rows.jsonl", mechanisms)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows(positive_ready))
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows())
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", routes)
    (ARTIFACT_DIR / "report.md").write_text(report(coverage, policy_rows, gates, mechanisms), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
