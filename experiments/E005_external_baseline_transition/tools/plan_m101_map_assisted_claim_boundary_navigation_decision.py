#!/usr/bin/env python3
"""Decide how to use the M100 map-assisted fallback result."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M101_map_assisted_claim_boundary_navigation_decision_v0"
VERSION = "e005_m101_map_assisted_claim_boundary_navigation_decision_v0"

M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M95_DIR = EXP_ROOT / "artifacts" / "E005-M95_real_proposal_paper_boundary_v0"
M99_DIR = EXP_ROOT / "artifacts" / "E005-M99_row_group_heavier_route_decision_v0"
M100_DIR = EXP_ROOT / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"


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


def get_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    for row in rows:
        if row.get("policy") == policy:
            return row
    raise RuntimeError(f"Missing policy summary: {policy}")


def m75_metric_row(policy: str, role: str, metrics: dict[str, Any], include_main: bool) -> dict[str, Any]:
    row = metrics[policy]
    return {
        "policy": policy,
        "role": role,
        "include_in_main_table": include_main,
        "query_rows": row["rows"],
        "success_rows": row["query_bridge_success_rows"],
        "sr_proxy": row["query_bridge_success_rate"],
        "attempt_spl_proxy": row["mean_attempt_spl_proxy"],
        "mean_expected_search_cost_all": row["mean_expected_search_cost"],
        "fallback_used_rows": 0,
        "old_dead_end_avoided_rows": row["old_location_dead_end_avoided_rows"],
        "deployable_policy": True,
        "status": "main_table_ready_with_boundary" if include_main else "appendix_or_ablation",
    }


def build_paper_table_rows(m100_rows: list[dict[str, Any]], m75_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    policies = [
        ("real_static_memory_only_v0", "legacy_baseline", None),
        ("real_detector_confidence_top5_v0", "detector_confidence_baseline", None),
        ("conceptgraphs_only_strict_top5_v0", "external_map_baseline", get_policy(m100_rows, "conceptgraphs_only_strict_top5_v0")),
        ("real_context_agnostic_memory_trust_reobserve_v0", "context_agnostic_method_baseline", None),
        ("h001_real_task_context_memory_trust_v0", "method_baseline", get_policy(m100_rows, "h001_real_task_context_memory_trust_v0")),
        (
            "h001_then_conceptgraphs_top5_on_observed_miss_v0",
            "selected_method_candidate",
            get_policy(m100_rows, "h001_then_conceptgraphs_top5_on_observed_miss_v0"),
        ),
        (
            "significant_moved_conceptgraphs_first_else_h001_v0",
            "ablation_not_selected",
            get_policy(m100_rows, "significant_moved_conceptgraphs_first_else_h001_v0"),
        ),
        (
            "h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0",
            "sensitivity_not_main",
            get_policy(m100_rows, "h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0"),
        ),
    ]

    rows: list[dict[str, Any]] = []
    for policy, role, summary in policies:
        if summary is None:
            rows.append(m75_metric_row(policy, role, m75_metrics, include_main=True))
            continue
        include_main = role in {"external_map_baseline", "method_baseline", "selected_method_candidate"}
        rows.append(
            {
                "policy": policy,
                "role": role,
                "include_in_main_table": include_main,
                "query_rows": summary["query_rows"],
                "success_rows": summary["success_rows"],
                "sr_proxy": summary["sr_proxy"],
                "attempt_spl_proxy": summary["attempt_spl_proxy"],
                "mean_expected_search_cost_all": summary["mean_expected_search_cost_all"],
                "fallback_used_rows": summary["fallback_used_rows"],
                "old_dead_end_avoided_rows": summary["old_dead_end_avoided_rows"],
                "deployable_policy": summary["deployable_policy"],
                "status": "main_table_ready_with_boundary" if include_main else "appendix_or_ablation",
            }
        )
    return rows


def build_route_rows(m100: dict[str, Any], m99: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": "paper_table_integration_and_navigation_bridge_next",
            "rank": 1,
            "selected": True,
            "decision": "selected",
            "next_unit": "E007-M01 navigation/path-cost bridge contract",
            "reason": [
                f"M100 selected fallback improves success to {m100['selected_success_rows']} / {m100['query_rows']} and `AttemptSPL` to {m100['selected_attempt_spl_proxy']}.",
                "The fallback pays explicit `ExpectedSearchCost`, so it is stronger than a raw union upper bound.",
                "The result is now mature enough to enter a paper-facing query-level table with boundary labels.",
                "Direction B still requires search/navigation execution evidence, so the next research expansion should bridge to path/navigation metrics.",
            ],
            "claim_boundary": "Use M100 as query-level map-assisted policy evidence, not as final real navigation or final robustness evidence.",
        },
        {
            "route_id": "heavier_external_route_restart_now",
            "rank": 2,
            "selected": False,
            "decision": "defer",
            "next_unit": "`OpenMask3D` / `HOV-SG` restart only if navigation bridge exposes proposal-source bottlenecks or reviewer baseline pressure remains high",
            "reason": [
                f"M99 found `ConceptGraphs` map-assisted repair candidate targets {m99['conceptgraphs_repair_candidate_targets']}; M100 converts them into a costed policy gain.",
                "The immediate blocker is no longer a missing external route but the lack of executed navigation/search bridge.",
                "`OpenMask3D` still has a local Docker/`MinkowskiEngine` blocker, and `HOV-SG` still needs source/runtime audit.",
            ],
            "claim_boundary": "Keep as a later robustness/baseline expansion path.",
        },
        {
            "route_id": "stop_at_query_level_paper_now",
            "rank": 3,
            "selected": False,
            "decision": "defer",
            "next_unit": "Possible intermediate paper only after a complete claim-evidence ledger and related-work table",
            "reason": [
                "M100 is a strong query-level result, but the final target is Direction B with open-vocabulary search/navigation.",
                "Stopping now would make the contribution narrower and easier to attack as proxy-only.",
            ],
            "claim_boundary": "Intermediate submission remains possible, but it is not the top-tier maximizing path.",
        },
        {
            "route_id": "human_context_upgrade_now",
            "rank": 4,
            "selected": False,
            "decision": "defer",
            "next_unit": "Optional E006 only if human intent is promoted to a main claim",
            "reason": [
                "M100 does not add a context-sensitive utility benchmark.",
                "Prior evidence still shows narrow context-specific gain.",
            ],
            "claim_boundary": "Human task context remains a conditioning signal, not the main contribution.",
        },
    ]


def build_claim_rows(m100: dict[str, Any], selected_policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C-M101-001",
            "claim": "M100 can be included as a paper-facing query-level policy row.",
            "claim_type": "paper_table_integration",
            "status": "ready_with_boundary",
            "evidence": (
                f"`{m100['selected_policy']}` improves H001 success {m100['h001_success_rows']} / {m100['query_rows']} "
                f"to {m100['selected_success_rows']} / {m100['query_rows']} and `AttemptSPL` "
                f"{m100['h001_attempt_spl_proxy']} -> {m100['selected_attempt_spl_proxy']}."
            ),
            "boundary": "This is query-level policy evidence, not final real navigation `SR` / `SPL`.",
            "next_validation_requirement": "Navigation/path-cost bridge contract before deployable search or navigation claims.",
        },
        {
            "claim_id": "C-M101-002",
            "claim": "The selected fallback is preferable to map-first variants for the main row.",
            "claim_type": "ablation_selection",
            "status": "supported",
            "evidence": (
                f"Selected fallback `AttemptSPL` is {selected_policy['attempt_spl_proxy']} with success "
                f"{selected_policy['success_rows']} / {selected_policy['query_rows']}; map-first variants are retained as ablations."
            ),
            "boundary": "Old-location dead-end avoidance can be reported separately, but it is not the main policy selector yet.",
            "next_validation_requirement": "If dead-end avoidance becomes central, add a utility-weighted metric.",
        },
        {
            "claim_id": "C-M101-003",
            "claim": "Heavier external mapping/proposal routes are not the immediate next step.",
            "claim_type": "route_boundary",
            "status": "deferred_with_reason",
            "evidence": "M100 already converts `ConceptGraphs` coverage into a costed policy improvement.",
            "boundary": "`OpenMask3D` / `HOV-SG` remain later routes for robustness and reviewer baseline pressure.",
            "next_validation_requirement": "Revisit after navigation bridge or if paper-table reviewers require more external routes.",
        },
        {
            "claim_id": "C-M101-004",
            "claim": "Final robustness and navigation claims remain blocked.",
            "claim_type": "blocked_claims",
            "status": "blocked",
            "evidence": "M100/M101 do not add simulator, navmesh, trajectory execution, or new perception source.",
            "boundary": "Do not claim final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
            "next_validation_requirement": "E007-M01 navigation/path-cost bridge contract.",
        },
    ]


def build_navigation_bridge_contract(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = next(row for row in route_rows if row["selected"])
    return {
        "selected_next_unit": selected["next_unit"],
        "purpose": "Connect M100 query-level candidate visit order to executed or path-cost-aware search/navigation metrics.",
        "minimum_inputs": [
            "M100 selected policy rows with candidate visit order and fallback trigger",
            "current/old scan ids and target object ids from the 195-row denominator",
            "path-cost source: existing E002 occupancy-grid A* proxy or a new simulator/navmesh source",
            "navigation/search baselines: H001-only, `ConceptGraphs`-only, detector-confidence, selected fallback",
        ],
        "required_outputs": [
            "`ExpectedSearchCost` with path-aware cost",
            "`AttemptSPL` or `SPL` proxy under candidate visit order",
            "old-location dead-end cost",
            "success/failure split by row_band and task_context_id",
            "claim boundary for real navigation `SR` / `SPL`",
        ],
        "blocked_shortcuts": [
            "Do not equate query-level `AttemptSPL` with real navigation `SPL`.",
            "Do not use target rank, target match distance, or success labels as policy inputs.",
            "Do not hide path-source-limited rows.",
        ],
    }


def build_report(
    coverage: dict[str, Any],
    table_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    nav_contract: dict[str, Any],
) -> str:
    table_lines = ["| Policy | Role | Include | Success | AttemptSPL | Mean Cost | Status |", "| --- | --- | --- | ---: | ---: | ---: | --- |"]
    for row in table_rows:
        success = f"{row.get('success_rows', 'n/a')} / {row.get('query_rows', 'n/a')}"
        table_lines.append(
            f"| `{row['policy']}` | `{row['role']}` | `{row['include_in_main_table']}` | "
            f"{success} | {row.get('attempt_spl_proxy', 'n/a')} | {row.get('mean_expected_search_cost_all', 'n/a')} | `{row['status']}` |"
        )

    route_lines = ["| Rank | Route | Decision | Next Unit |", "| ---: | --- | --- | --- |"]
    for row in route_rows:
        route_lines.append(f"| {row['rank']} | `{row['route_id']}` | `{row['decision']}` | {row['next_unit']} |")

    claim_lines = ["| Claim | Status | Evidence | Boundary |", "| --- | --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['boundary']} |")

    return f"""# E005-M101 Map-Assisted Fallback Claim Boundary

## Facts

- Status: `{coverage["status"]}`.
- Selected route: `{coverage["selected_route"]}`.
- Selected next unit: {coverage["selected_next_unit"]}.
- Paper-table integration ready: {coverage["paper_table_integration_ready"]}.
- M100 selected policy: `{coverage["m100_selected_policy"]}`.
- M100 selected success: {coverage["m100_selected_success_rows"]} / {coverage["query_rows"]}.
- M100 selected `AttemptSPL`: {coverage["m100_selected_attempt_spl"]}.
- Real navigation `SR` / `SPL` ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.

## Paper-Table Rows

{chr(10).join(table_lines)}

## Route Decision

{chr(10).join(route_lines)}

## Navigation Bridge Contract

- Purpose: {nav_contract["purpose"]}
- Selected next unit: {nav_contract["selected_next_unit"]}
- Required outputs: {", ".join(nav_contract["required_outputs"])}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- M100 should become a paper-facing query-level method row, with explicit boundary labels.
- The next top-tier-motivated expansion is navigation/path-cost bridging, not another external mapping route.
- Heavier external baselines remain valuable later, but M101 does not select them as the immediate next action.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m75 = read_json(M75_DIR / "coverage.json")
    m95 = read_json(M95_DIR / "coverage.json")
    m99 = read_json(M99_DIR / "coverage.json")
    m100 = read_json(M100_DIR / "coverage.json")
    m100_rows = read_jsonl(M100_DIR / "policy_summary_rows.jsonl")
    if not m100 or not m100_rows:
        raise RuntimeError("M100 coverage or policy summary is missing.")

    selected_policy = get_policy(m100_rows, m100["selected_policy"])
    m75_metrics = read_json(M75_DIR / "policy_metrics.json")
    table_rows = build_paper_table_rows(m100_rows, m75_metrics)
    route_rows = build_route_rows(m100, m99)
    claim_rows = build_claim_rows(m100, selected_policy)
    nav_contract = build_navigation_bridge_contract(route_rows)
    selected_route = next(row for row in route_rows if row["selected"])

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m75_status": m75.get("status"),
        "m95_status": m95.get("status"),
        "m99_status": m99.get("status"),
        "m100_status": m100.get("status"),
        "m100_selected_attempt_spl": m100["selected_attempt_spl_proxy"],
        "m100_selected_mean_cost": m100["selected_mean_expected_search_cost"],
        "m100_selected_policy": m100["selected_policy"],
        "m100_selected_success_gain_vs_h001": m100["selected_success_gain_vs_h001"],
        "m100_selected_success_rows": m100["selected_success_rows"],
        "paper_table_integration_ready": True,
        "query_rows": m100["query_rows"],
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": selected_route["next_unit"],
        "selected_route": selected_route["route_id"],
        "status": "e005_m101_map_assisted_claim_boundary_navigation_decision_ready",
        "version": VERSION,
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "paper_table_rows": table_rows,
            "route_decision_rows": route_rows,
            "claim_boundary_rows": claim_rows,
            "navigation_bridge_contract": nav_contract,
        },
    )
    write_json(OUT_DIR / "navigation_bridge_contract.json", nav_contract)
    write_jsonl(OUT_DIR / "paper_table_rows.jsonl", table_rows)
    write_jsonl(OUT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, table_rows, route_rows, claim_rows, nav_contract))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
