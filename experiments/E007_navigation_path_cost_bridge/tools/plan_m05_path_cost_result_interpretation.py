#!/usr/bin/env python3
"""Interpret E007-M04 path-cost metrics for paper-table use and claim boundaries."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
M04_DIR = EXP_ROOT / "artifacts" / "E007-M04_path_cost_policy_metrics_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M05_path_cost_result_interpretation_v0"
VERSION = "e007_m05_path_cost_result_interpretation_v0"

METHOD_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"
H001_POLICY = "h001_real_task_context_memory_trust_v0"
CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC_POLICY = "real_static_memory_only_v0"
DETECTOR_POLICY = "real_detector_confidence_top5_v0"
CONCEPTGRAPHS_POLICY = "conceptgraphs_only_strict_top5_v0"

POLICY_LABELS = {
    STATIC_POLICY: "Static stale memory",
    DETECTOR_POLICY: "Detector-confidence top-5",
    CONCEPTGRAPHS_POLICY: "ConceptGraphs-only map",
    CONTEXT_AGNOSTIC_POLICY: "Context-agnostic memory trust",
    H001_POLICY: "H001 memory trust",
    METHOD_POLICY: "H001 + ConceptGraphs fallback",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_policy(rows: list[dict[str, Any]], policy: str, subset: str = "full_denominator") -> dict[str, Any]:
    for row in rows:
        if row.get("policy") == policy and row.get("subset") == subset:
            return row
    raise RuntimeError(f"Missing policy summary: {policy}/{subset}")


def find_delta(rows: list[dict[str, Any]], baseline: str) -> dict[str, Any]:
    for row in rows:
        if row.get("baseline_policy") == baseline:
            return row
    raise RuntimeError(f"Missing paired delta: {baseline}")


def build_bridge_table_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for policy in [
        STATIC_POLICY,
        DETECTOR_POLICY,
        CONCEPTGRAPHS_POLICY,
        CONTEXT_AGNOSTIC_POLICY,
        H001_POLICY,
        METHOD_POLICY,
    ]:
        row = find_policy(policy_rows, policy)
        output.append(
            {
                "table_id": "E007-Bridge-A_occupancy_grid_path_cost_proxy",
                "policy": policy,
                "paper_label": POLICY_LABELS[policy],
                "include_in_bridge_table": True,
                "query_rows": row["query_policy_rows"],
                "source_ready_rows": row["path_source_ready_rows"],
                "source_limited_rows": row["path_source_limited_rows"],
                "source_limited_rate": row["path_source_limited_rate"],
                "full_success_rows": row["query_bridge_success_rows_full_denominator"],
                "full_success_rate": row["query_bridge_success_rate_full_denominator"],
                "source_ready_path_success_rows": row["path_success_rows_source_ready"],
                "source_ready_path_success_rate": row["path_success_rate_source_ready"],
                "lower_bound_full_success_rate": row["path_success_lower_bound_rate_full_denominator"],
                "mean_path_expected_search_cost_m": row["mean_path_expected_search_cost_m_source_ready"],
                "mean_path_attempt_spl_proxy": row["mean_path_attempt_spl_proxy_source_ready"],
                "source_limited_reason_counts": row["source_limited_reason_counts"],
                "paper_use": "bridge_main_table_with_proxy_boundary"
                if policy in {STATIC_POLICY, DETECTOR_POLICY, CONCEPTGRAPHS_POLICY, H001_POLICY, METHOD_POLICY}
                else "ablation_bridge_row",
            }
        )
    return output


def build_table_decision_rows(policy_rows: list[dict[str, Any]], delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    method = find_policy(policy_rows, METHOD_POLICY)
    h001_delta = find_delta(delta_rows, H001_POLICY)
    conceptgraphs_delta = find_delta(delta_rows, CONCEPTGRAPHS_POLICY)
    static_delta = find_delta(delta_rows, STATIC_POLICY)
    return [
        {
            "decision_id": "D-E007-M05-001",
            "decision": "include_e007_m04_as_bridge_table",
            "selected": True,
            "paper_location": "main_or_near-main bridge table",
            "reason": (
                f"Method full success {method['query_bridge_success_rows_full_denominator']} / {method['query_policy_rows']}; "
                f"paired source-ready deltas are +{static_delta['success_rate_delta']} vs static and "
                f"+{conceptgraphs_delta['success_rate_delta']} vs ConceptGraphs."
            ),
            "boundary": "Use as occupancy-grid path-cost proxy evidence, not real navigation `SR` / `SPL`.",
        },
        {
            "decision_id": "D-E007-M05-002",
            "decision": "frame_method_vs_h001_as_repair_tradeoff",
            "selected": True,
            "paper_location": "claim text and reviewer defense",
            "reason": (
                f"Vs H001-only, success delta {h001_delta['success_rate_delta']} and `PathAttemptSPLProxy` delta "
                f"{h001_delta['mean_path_attempt_spl_delta']} are positive, but path cost delta is "
                f"{h001_delta['mean_path_cost_delta_m']}m."
            ),
            "boundary": "Do not write unconditional dominance over H001-only.",
        },
        {
            "decision_id": "D-E007-M05-003",
            "decision": "block_old_location_dead_end_cost_as_primary_metric",
            "selected": True,
            "paper_location": "claim boundary / appendix",
            "reason": "The current E002/E007 path source starts at the old-memory centroid, making static old-location path cost zero and dead-end cost only a lower-bound diagnostic.",
            "boundary": "`OldLocationDeadEndCostM` requires a robot/start-pose or executed search source before it can become a main metric.",
        },
    ]


def build_reviewer_attack_rows(coverage: dict[str, Any], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    method = find_policy(policy_rows, METHOD_POLICY)
    detector = find_policy(policy_rows, DETECTOR_POLICY)
    return [
        {
            "attack_id": "R-E007-M05-001",
            "reviewer_attack": "The path metric is not real navigation.",
            "risk": "high",
            "defense": "State that E007 reports `PathAttemptSPLProxy` under `occupancy_grid_astar_v0`; real `SR` / `SPL` remains blocked until simulator/navmesh/trajectory execution.",
            "evidence_or_next_check": "E007-M04 claim row blocks real navigation `SR` / `SPL`.",
        },
        {
            "attack_id": "R-E007-M05-002",
            "reviewer_attack": "Source-ready subset may hide failures.",
            "risk": "medium",
            "defense": "Report full denominator, source-ready subset, and source-limited rate together.",
            "evidence_or_next_check": f"{coverage['source_limited_query_policy_rows']} / {coverage['query_policy_rows']} query-policy rows are source-limited.",
        },
        {
            "attack_id": "R-E007-M05-003",
            "reviewer_attack": "Some successful rows use upstream expected-search-cost rank rather than direct route-target flags.",
            "risk": "medium",
            "defense": "Record the boundary and do not present those rows as direct route-localization evidence.",
            "evidence_or_next_check": f"{coverage['eval_expected_search_cost_stop_rows']} / {coverage['query_policy_rows']} rows use `eval_expected_search_cost_rank`.",
        },
        {
            "attack_id": "R-E007-M05-004",
            "reviewer_attack": "H001 + ConceptGraphs fallback increases path cost over H001-only.",
            "risk": "medium",
            "defense": "Frame the contribution as repair tradeoff: higher success and slightly higher `PathAttemptSPLProxy`, with extra path cost explicitly paid.",
            "evidence_or_next_check": "Paired delta vs H001-only: success +0.054545, `PathAttemptSPLProxy` +0.004390, path cost +0.941948m.",
        },
        {
            "attack_id": "R-E007-M05-005",
            "reviewer_attack": "Detector-confidence baseline is source-limited more often than the method, making comparisons uneven.",
            "risk": "medium",
            "defense": "Use paired source-ready deltas for main comparisons and report source-limited rates.",
            "evidence_or_next_check": f"Detector source-limited rate {detector['path_source_limited_rate']}; method source-limited rate {method['path_source_limited_rate']}.",
        },
    ]


def build_claim_rows(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    static_delta = find_delta(delta_rows, STATIC_POLICY)
    conceptgraphs_delta = find_delta(delta_rows, CONCEPTGRAPHS_POLICY)
    h001_delta = find_delta(delta_rows, H001_POLICY)
    return [
        {
            "claim_id": "C-E007-M05-001",
            "claim": "E007-M04 is paper-facing bridge-table evidence.",
            "status": "ready_with_proxy_boundary",
            "evidence": (
                f"Paired source-ready success delta is {static_delta['success_rate_delta']} vs static and "
                f"{conceptgraphs_delta['success_rate_delta']} vs ConceptGraphs-only."
            ),
            "boundary": "Call it an occupancy-grid path-cost proxy, not real navigation.",
        },
        {
            "claim_id": "C-E007-M05-002",
            "claim": "The selected method improves over H001-only as a cost-aware repair tradeoff.",
            "status": "supported_with_tradeoff",
            "evidence": (
                f"Vs H001-only: success +{h001_delta['success_rate_delta']}, `PathAttemptSPLProxy` "
                f"+{h001_delta['mean_path_attempt_spl_delta']}, path cost +{h001_delta['mean_path_cost_delta_m']}m."
            ),
            "boundary": "Do not claim path-cost optimality or unconditional dominance over H001-only.",
        },
        {
            "claim_id": "C-E007-M05-003",
            "claim": "Old-location dead-end cost is not yet a primary metric.",
            "status": "blocked_as_primary_metric",
            "evidence": "The current path source starts from the old-memory centroid.",
            "boundary": "Needs start-pose sensitivity, robot spawn, or executed navigation before main claim use.",
        },
        {
            "claim_id": "C-E007-M05-004",
            "claim": "Real navigation `SR` / `SPL` remains blocked.",
            "status": "blocked",
            "evidence": "E007-M05 does not add simulator, navmesh, controller, or trajectory execution.",
            "boundary": "Use `PathAttemptSPLProxy` only.",
        },
    ]


def build_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e007_m06_path_start_source_limit_sensitivity_next",
            "selected": True,
            "decision": "selected",
            "next_unit": "E007-M06 path-start/source-limit sensitivity and reviewer-defense audit",
            "reason": [
                "E007-M04 is positive but has source-limited rows and a path-start proxy assumption.",
                "Reviewer defense should quantify dependence on source limits, stop-rank fallback, and old-memory start before moving to real navigation.",
            ],
        },
        {
            "rank": 2,
            "route_id": "real_navigation_sr_spl_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "Simulator/navmesh/trajectory execution integration",
            "reason": [
                "Real navigation `SR` / `SPL` requires more infrastructure than the current occupancy-grid proxy.",
                "Starting it before source-limit defense risks a weaker paper table.",
            ],
        },
        {
            "rank": 3,
            "route_id": "external_baseline_restart_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "`OpenMask3D` / `HOV-SG` only if E007-M06 shows baseline pressure remains unresolved",
            "reason": [
                "E007-M04 already compares static, detector, ConceptGraphs-only, context-agnostic, and H001-only under a path proxy.",
                "External routes are still valuable, but not the immediate blocker for the path-cost table.",
            ],
        },
    ]


def build_report(
    coverage: dict[str, Any],
    bridge_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    reviewer_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    bridge_table = [
        "| Policy | Full Success | Source Ready | Path Success | Path Cost | `PathAttemptSPLProxy` | Source-Limited | Paper Use |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in bridge_rows:
        bridge_table.append(
            f"| `{row['policy']}` | {row['full_success_rows']} / {row['query_rows']} | "
            f"{row['source_ready_rows']} / {row['query_rows']} | "
            f"{row['source_ready_path_success_rows']} / {row['source_ready_rows']} | "
            f"{row['mean_path_expected_search_cost_m']} | {row['mean_path_attempt_spl_proxy']} | "
            f"{row['source_limited_rate']} | `{row['paper_use']}` |"
        )

    decision_table = ["| Decision | Selected | Boundary |", "| --- | --- | --- |"]
    for row in decision_rows:
        decision_table.append(f"| `{row['decision']}` | `{row['selected']}` | {row['boundary']} |")

    reviewer_table = ["| Attack | Risk | Defense |", "| --- | --- | --- |"]
    for row in reviewer_rows:
        reviewer_table.append(f"| {row['reviewer_attack']} | `{row['risk']}` | {row['defense']} |")

    claim_table = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_table.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    route_table = ["| Rank | Route | Decision | Next Unit |", "| ---: | --- | --- | --- |"]
    for row in route_rows:
        route_table.append(f"| {row['rank']} | `{row['route_id']}` | `{row['decision']}` | {row['next_unit']} |")

    return f"""# E007-M05 Path-Cost Result Interpretation

## Facts

- Status: `{coverage["status"]}`.
- Selected table role: `{coverage["selected_table_role"]}`.
- Selected next unit: {coverage["selected_next_unit"]}.
- Method policy: `{METHOD_POLICY}`.
- Real navigation `SR` / `SPL` ready: false.

## Bridge Table Decision

{chr(10).join(bridge_table)}

## Paper Boundary Decisions

{chr(10).join(decision_table)}

## Reviewer Defense

{chr(10).join(reviewer_table)}

## Claim Boundary

{chr(10).join(claim_table)}

## Route Decision

{chr(10).join(route_table)}

## Agent Inference

- E007-M04 should be used as a paper-facing bridge table, not as final navigation evidence.
- The method is clearly better than static memory, detector-confidence ranking, and `ConceptGraphs`-only under paired source-ready path metrics.
- Against H001-only, the result is a useful repair tradeoff: success and `PathAttemptSPLProxy` improve slightly while path cost increases.
- E007-M06 should quantify whether the table is sensitive to source-limited rows, stop-rank fallback, and the old-memory path-start assumption.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m04_coverage = read_json(M04_DIR / "coverage.json")
    policy_rows = read_jsonl(M04_DIR / "policy_metric_summary_rows.jsonl")
    delta_rows = read_jsonl(M04_DIR / "paired_policy_delta_rows.jsonl")
    if not policy_rows:
        raise RuntimeError("Missing E007-M04 policy rows.")
    if not delta_rows:
        raise RuntimeError("Missing E007-M04 paired delta rows.")

    bridge_rows = build_bridge_table_rows(policy_rows)
    decision_rows = build_table_decision_rows(policy_rows, delta_rows)
    reviewer_rows = build_reviewer_attack_rows(m04_coverage, policy_rows)
    claim_rows = build_claim_rows(delta_rows)
    route_rows = build_route_rows()
    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m05_path_cost_result_interpretation_ready",
        "version": VERSION,
        "m04_status": m04_coverage.get("status"),
        "selected_table_role": "paper_facing_occupancy_grid_path_cost_bridge_table",
        "bridge_table_ready": True,
        "main_navigation_table_ready": False,
        "old_location_dead_end_cost_primary_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": "E007-M06 path-start/source-limit sensitivity and reviewer-defense audit",
        "method_policy": METHOD_POLICY,
        "source_limited_query_policy_rows": m04_coverage.get("source_limited_query_policy_rows"),
        "eval_expected_search_cost_stop_rows": m04_coverage.get("eval_expected_search_cost_stop_rows"),
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "bridge_table_rows.jsonl", bridge_rows)
    write_jsonl(OUT_DIR / "paper_boundary_decision_rows.jsonl", decision_rows)
    write_jsonl(OUT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(OUT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "bridge_table_rows": bridge_rows,
            "paper_boundary_decision_rows": decision_rows,
            "reviewer_defense_rows": reviewer_rows,
            "claim_boundary_rows": claim_rows,
            "route_decision_rows": route_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, bridge_rows, decision_rows, reviewer_rows, claim_rows, route_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
