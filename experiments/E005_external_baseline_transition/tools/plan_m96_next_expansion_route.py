#!/usr/bin/env python3
"""Decide the next expansion route after the E005-M95 paper boundary."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M96_next_expansion_route_decision_v0"
M95_DIR = EXP_ROOT / "artifacts" / "E005-M95_real_proposal_paper_boundary_v0"
VERSION = "e005_m96_next_expansion_route_decision_v0"


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


def route_options(m95: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": "external_proposal_mapping_baseline_first",
            "rank": 1,
            "selected": True,
            "primary_goal": "Strengthen the real RGB-D/open-vocabulary robustness boundary before navigation claims.",
            "addresses_blocked_claims": [
                "final_real_rgbd_open_vocab_robustness",
                "detector/proposal baseline rigor",
                "heldout transfer pressure",
            ],
            "rationale": [
                "M95 blocks final robustness because current real proposals are diagnostic, not a strong perception baseline.",
                f"M75 proposal precision is {m95['m75_proposal_precision']} and target detection is {m95['m75_target_detected_rows']} / {m95['query_rows']}.",
                "M93/M94 repair improves target detection but does not improve H001 success or detector task-budget success.",
                "Navigation before stronger proposal/mapping evidence would conflate perception failure with navigation policy failure.",
            ],
            "first_followup_unit": "E005-M97 external proposal/mapping baseline feasibility matrix",
            "candidate_routes": [
                {
                    "candidate": "ConceptGraphs-derived proposal/map route",
                    "priority": "high",
                    "reason": "Already built and denominator-aligned; can test whether map-level candidates, not detector boxes, cover the missing robustness boundary.",
                    "burden": "low_to_medium",
                },
                {
                    "candidate": "OpenMask3D",
                    "priority": "medium",
                    "reason": "Strong 3D instance proposal baseline candidate, but local Docker/MinkowskiEngine blocker remains.",
                    "burden": "high",
                },
                {
                    "candidate": "HOV-SG",
                    "priority": "medium",
                    "reason": "Closer to hierarchical open-vocabulary semantic mapping; likely useful for Direction B, but needs source/runtime audit.",
                    "burden": "high",
                },
                {
                    "candidate": "Open3DSG bounded vocab adapter",
                    "priority": "supporting",
                    "reason": "Already denominator-aligned as scene-graph route; useful as a table row, not sufficient as a proposal robustness route.",
                    "burden": "low",
                },
            ],
            "risk": "Can become baseline engineering if not tied to the H001 memory-decision failure taxonomy.",
            "decision": "selected",
        },
        {
            "route_id": "navigation_search_bridge_first",
            "rank": 2,
            "selected": False,
            "primary_goal": "Move toward real navigation SR/SPL and Direction B embodied evaluation.",
            "addresses_blocked_claims": ["real_navigation_sr_spl", "deployable_search_policy"],
            "rationale": [
                "Direction B ultimately needs navigation/search execution evidence.",
                "However, M95 still blocks real RGB-D/open-vocabulary robustness, so navigation metrics would be confounded by proposal failures.",
                "Simulator/navmesh, episode generation, path execution, and navigation baselines are not integrated yet.",
            ],
            "first_followup_unit": "E007 navigation bridge design after external proposal baseline decision",
            "candidate_routes": [
                {
                    "candidate": "offline candidate-visit execution with navmesh/path costs",
                    "priority": "medium",
                    "reason": "Closest bridge from E002/E005 `ExpectedSearchCost` to executed search.",
                    "burden": "medium_high",
                },
                {
                    "candidate": "HM3D-OVON / GOAT-Bench modular baseline",
                    "priority": "later",
                    "reason": "Strong reviewer-facing navigation baseline, but likely requires major environment integration.",
                    "burden": "high",
                },
            ],
            "risk": "High confounding risk if perception/mapping baseline strength is not settled first.",
            "decision": "defer_after_external_baseline_gate",
        },
        {
            "route_id": "all_batch_local_detector_cleanup",
            "rank": 3,
            "selected": False,
            "primary_goal": "Run b01/b03 active-label or detector-cleanup variants for a complete local repair table.",
            "addresses_blocked_claims": ["detector/prompt failure analysis"],
            "rationale": [
                "M94 already selected stop-and-record because M93 does not improve H001 success.",
                "More local cleanup may improve detector rows but is unlikely to improve the main semantic memory claim.",
            ],
            "first_followup_unit": "Only if a complete detector-repair appendix is explicitly needed.",
            "candidate_routes": [],
            "risk": "Looks like detector tuning rather than semantic mapping novelty.",
            "decision": "defer",
        },
        {
            "route_id": "human_context_upgrade",
            "rank": 4,
            "selected": False,
            "primary_goal": "Promote human task context from secondary condition to main contribution.",
            "addresses_blocked_claims": ["human_intent_main_contribution"],
            "rationale": [
                "M75/M95 still show only a 1-row gain over context-agnostic memory trust.",
                "This route needs a dedicated context-sensitive utility benchmark and stronger context-agnostic baselines.",
            ],
            "first_followup_unit": "Optional E006 only if user explicitly wants human intent as a main claim.",
            "candidate_routes": [],
            "risk": "Weak top-tier claim unless context-dependent utility changes decisions broadly.",
            "decision": "defer",
        },
    ]


def decision_criteria() -> list[dict[str, Any]]:
    return [
        {
            "criterion": "directly_addresses_current_blocker",
            "weight": "high",
            "preferred_route": "external_proposal_mapping_baseline_first",
            "reason": "M95 blocks final robustness on proposal/mapping evidence, not on navigation path execution alone.",
        },
        {
            "criterion": "minimizes_claim_confounding",
            "weight": "high",
            "preferred_route": "external_proposal_mapping_baseline_first",
            "reason": "Navigation before perception robustness would mix mapper/proposal errors with policy errors.",
        },
        {
            "criterion": "top_tier_reviewer_pressure",
            "weight": "high",
            "preferred_route": "external_proposal_mapping_baseline_first",
            "reason": "Reviewers will ask why stronger open-vocabulary mapping/proposal baselines were not compared before navigation claims.",
        },
        {
            "criterion": "direction_b_alignment",
            "weight": "medium",
            "preferred_route": "navigation_search_bridge_first",
            "reason": "Direction B ultimately requires embodied search/navigation evidence, but it is a downstream step after baseline pressure.",
        },
        {
            "criterion": "engineering_burden",
            "weight": "medium",
            "preferred_route": "external_proposal_mapping_baseline_first",
            "reason": "A feasibility matrix can be done before long Docker/navigation integration work.",
        },
    ]


def build_claim_boundary(m95_claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for claim in m95_claims:
        rows.append(
            {
                "claim_id": claim["claim_id"],
                "claim": claim["claim"],
                "claim_type": claim["claim_type"],
                "status_after_m96": claim["status"],
                "m96_effect": "unchanged",
                "next_validation_requirement": claim["next_validation_requirement"],
            }
        )
    rows.append(
        {
            "claim_id": "C-M96-001",
            "claim": "Next expansion should prioritize external proposal/mapping baseline feasibility before navigation bridge execution.",
            "claim_type": "route_decision",
            "status_after_m96": "selected",
            "m96_effect": "new_route_boundary",
            "next_validation_requirement": "E005-M97 feasibility matrix with candidate routes, blockers, data contracts, and first smoke decision.",
        }
    )
    return rows


def report(coverage: dict[str, Any], routes: list[dict[str, Any]], criteria: list[dict[str, Any]]) -> str:
    selected = next(row for row in routes if row["selected"])
    route_lines = []
    for row in routes:
        route_lines.append(
            f"| {row['rank']} | `{row['route_id']}` | {str(row['selected']).lower()} | {row['decision']} | {row['primary_goal']} |"
        )
    criteria_lines = []
    for row in criteria:
        criteria_lines.append(
            f"| `{row['criterion']}` | {row['weight']} | `{row['preferred_route']}` | {row['reason']} |"
        )
    return f"""# E005-M96 Next Expansion Route Decision

## Facts

- Status: `{coverage["status"]}`.
- M95 blocked claims: {coverage["m95_blocked_claim_count"]}.
- M95 allowed diagnostic claims: {coverage["m95_allowed_diagnostic_claim_count"]}.
- Current final real RGB-D/open-vocabulary robustness ready: false.
- Current deployable search policy ready: false.
- Current real navigation `SR` / `SPL` ready: false.
- Selected route: `{coverage["selected_next_route"]}`.
- Next recommended unit: `{coverage["next_recommended_unit"]}`.

## Route Options

| Rank | Route | Selected | Decision | Goal |
| ---: | --- | --- | --- | --- |
{chr(10).join(route_lines)}

## Decision Criteria

| Criterion | Weight | Preferred Route | Reason |
| --- | --- | --- | --- |
{chr(10).join(criteria_lines)}

## Selected Route

The selected route is `{selected["route_id"]}`.

## Claim Boundary

- Do not run another local detector cleanup as the main path.
- Do not start real navigation `SR` / `SPL` execution before the external proposal/mapping baseline decision is fixed.
- Use E005-M97 to decide which external proposal/mapping route is feasible enough to run first.

## Agent Inference

- External proposal/mapping baseline feasibility should come before navigation execution because it directly addresses the current M95 robustness blocker.
- Navigation remains essential for Direction B, but doing it now would make failures hard to attribute.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m95 = read_json(M95_DIR / "coverage.json")
    m95_claims = read_jsonl(M95_DIR / "final_claim_boundary_rows.jsonl")
    routes = route_options(m95)
    criteria = decision_criteria()
    claim_rows = build_claim_boundary(m95_claims)
    selected = next(row for row in routes if row["selected"])
    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m95_allowed_diagnostic_claim_count": m95["allowed_diagnostic_claim_count"],
        "m95_blocked_claim_count": m95["blocked_claim_count"],
        "m95_status": m95["status"],
        "next_recommended_unit": "E005-M97 external proposal/mapping baseline feasibility matrix",
        "route_option_count": len(routes),
        "selected_next_route": selected["route_id"],
        "status": "e005_m96_next_expansion_route_decision_ready",
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", {"coverage": coverage, "routes": routes, "criteria": criteria, "claims": claim_rows})
    write_jsonl(OUT_DIR / "route_options.jsonl", routes)
    write_jsonl(OUT_DIR / "decision_criteria.jsonl", criteria)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(OUT_DIR / "report.md", report(coverage, routes, criteria))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
