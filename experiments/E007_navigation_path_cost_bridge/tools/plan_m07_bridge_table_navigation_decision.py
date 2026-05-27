#!/usr/bin/env python3
"""Package E007 bridge-table evidence and decide the navigation expansion route."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
M05_DIR = EXP_ROOT / "artifacts" / "E007-M05_path_cost_result_interpretation_v0"
M06_DIR = EXP_ROOT / "artifacts" / "E007-M06_path_start_source_limit_sensitivity_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M07_bridge_table_package_navigation_decision_v0"
VERSION = "e007_m07_bridge_table_package_navigation_decision_v0"

METHOD_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"
H001_POLICY = "h001_real_task_context_memory_trust_v0"
STATIC_POLICY = "real_static_memory_only_v0"
DETECTOR_POLICY = "real_detector_confidence_top5_v0"
CONCEPTGRAPHS_POLICY = "conceptgraphs_only_strict_top5_v0"
CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
POLICIES = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    CONCEPTGRAPHS_POLICY,
    CONTEXT_AGNOSTIC_POLICY,
    H001_POLICY,
    METHOD_POLICY,
]


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


def find_row(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for row in rows:
        if row.get(key) == value:
            return row
    raise RuntimeError(f"Missing row where {key}={value}")


def find_delta(rows: list[dict[str, Any]], subset_id: str, baseline: str) -> dict[str, Any]:
    for row in rows:
        if row.get("subset_id") == subset_id and row.get("baseline_policy") == baseline:
            return row
    raise RuntimeError(f"Missing paired delta: {subset_id}/{baseline}")


def build_paper_table_rows(
    bridge_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for policy in POLICIES:
        bridge = find_row(bridge_rows, "policy", policy)
        sens = find_row(sensitivity_rows, "policy", policy)
        output.append(
            {
                "table_id": "E007-Final-A_path_cost_proxy_bridge",
                "policy": policy,
                "paper_label": bridge["paper_label"],
                "full_success_rows": bridge["full_success_rows"],
                "query_rows": bridge["query_rows"],
                "full_success_rate": bridge["full_success_rate"],
                "source_ready_rows": bridge["source_ready_rows"],
                "source_ready_path_success_rows": bridge["source_ready_path_success_rows"],
                "source_ready_path_success_rate": bridge["source_ready_path_success_rate"],
                "source_ready_lower_bound_success_rows": sens["source_ready_success_rows"],
                "direct_failure_lower_bound_success_rows": sens["source_ready_direct_or_failure_success_rows"],
                "mean_path_expected_search_cost_m": bridge["mean_path_expected_search_cost_m"],
                "mean_path_attempt_spl_proxy": bridge["mean_path_attempt_spl_proxy"],
                "source_limited_rows": bridge["source_limited_rows"],
                "source_limited_rate": bridge["source_limited_rate"],
                "stop_rank_rows": sens["eval_expected_search_cost_rank_rows"],
                "old_first_non_target_zero_step_rows": sens["old_first_non_target_zero_step_rows"],
                "paper_use": bridge["paper_use"],
                "required_caption_boundary": (
                    "Occupancy-grid path-cost proxy. Full denominator, source-ready lower bound, "
                    "direct/failure lower bound, and source-limited rate must be reported together."
                ),
            }
        )
    return output


def build_claim_ledger_rows(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    static_direct = find_delta(delta_rows, "source_ready_direct_or_failure_only", STATIC_POLICY)
    detector_direct = find_delta(delta_rows, "source_ready_direct_or_failure_only", DETECTOR_POLICY)
    cg_direct = find_delta(delta_rows, "source_ready_direct_or_failure_only", CONCEPTGRAPHS_POLICY)
    h001_direct = find_delta(delta_rows, "source_ready_direct_or_failure_only", H001_POLICY)
    return [
        {
            "claim_id": "C-E007-M07-001",
            "claim_type": "allowed",
            "paper_claim": "The E007 path-cost bridge table is ready as an occupancy-grid proxy table.",
            "evidence": (
                "E007-M05 selected paper-facing bridge table; E007-M06 confirmed source-limit/direct-only sensitivity."
            ),
            "paper_location": "main_or_near_main_table",
            "boundary": "Not real navigation `SR` / `SPL`.",
        },
        {
            "claim_id": "C-E007-M07-002",
            "claim_type": "allowed",
            "paper_claim": "H001 + ConceptGraphs fallback improves proxy path-cost search over static memory, detector-confidence ranking, and ConceptGraphs-only.",
            "evidence": (
                f"Direct/failure source-ready success deltas: +{static_direct['success_rate_delta']} vs static, "
                f"+{detector_direct['success_rate_delta']} vs detector, +{cg_direct['success_rate_delta']} vs ConceptGraphs."
            ),
            "paper_location": "results_text",
            "boundary": "Use proxy path-cost wording and include denominator/source-limit rows.",
        },
        {
            "claim_id": "C-E007-M07-003",
            "claim_type": "allowed_with_tradeoff",
            "paper_claim": "H001 + ConceptGraphs fallback is a map-assisted repair tradeoff over H001-only.",
            "evidence": (
                f"Direct/failure source-ready delta vs H001-only: success +{h001_direct['success_rate_delta']}, "
                f"`PathAttemptSPLProxy` +{h001_direct['path_attempt_spl_delta']}, "
                f"path cost +{h001_direct['path_cost_delta_m']}m."
            ),
            "paper_location": "ablation_or_analysis",
            "boundary": "Do not claim path-cost optimality or unconditional dominance over H001-only.",
        },
        {
            "claim_id": "C-E007-M07-004",
            "claim_type": "blocked",
            "paper_claim": "Real navigation `SR` / `SPL` is improved.",
            "evidence": "No simulator, navmesh, controller, start-pose sampling, or trajectory execution has been integrated.",
            "paper_location": "claim_boundary",
            "boundary": "Requires real navigation benchmark/source preflight and later execution.",
        },
        {
            "claim_id": "C-E007-M07-005",
            "claim_type": "blocked",
            "paper_claim": "`OldLocationDeadEndCostM` is a primary metric.",
            "evidence": "E007-M06 found 153 old-first non-target zero-step route rows under old-memory centroid start.",
            "paper_location": "claim_boundary_or_appendix",
            "boundary": "Requires robot/start-pose, spawn sensitivity, or executed navigation.",
        },
        {
            "claim_id": "C-E007-M07-006",
            "claim_type": "blocked",
            "paper_claim": "Final real RGB-D/open-vocabulary robustness is solved.",
            "evidence": "E005 real-proposal table remains diagnostic, with final robustness false.",
            "paper_location": "claim_boundary",
            "boundary": "Needs heldout transfer, visibility-aware denominator, and stronger proposal/mapping baselines.",
        },
    ]


def build_reviewer_package_rows() -> list[dict[str, Any]]:
    return [
        {
            "reviewer_issue": "This is not real navigation.",
            "defense": "State the table is `occupancy_grid_astar_v0` proxy evidence and reserve real `SR` / `SPL` for a later navigation experiment.",
            "must_show_in_paper": "Metric names must include `Proxy` or `occupancy-grid path-cost`; table caption must block real `SR` / `SPL`.",
        },
        {
            "reviewer_issue": "Source-ready subset hides failures.",
            "defense": "Report full success, source-ready lower bound, direct/failure lower bound, and source-limited rows in the same table.",
            "must_show_in_paper": "Include columns for source-limited rows and direct/failure lower-bound success.",
        },
        {
            "reviewer_issue": "H001-only is nearly as good and cheaper.",
            "defense": "Frame H001 + ConceptGraphs fallback as repair tradeoff: higher success with extra path cost.",
            "must_show_in_paper": "Include H001-only ablation row and path-cost delta analysis.",
        },
        {
            "reviewer_issue": "Old-location dead-end cost is biased.",
            "defense": "Block `OldLocationDeadEndCostM` as primary and explain old-memory centroid path-start bias.",
            "must_show_in_paper": "Put dead-end metric in blocked-claim ledger until navigation episodes exist.",
        },
    ]


def build_navigation_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e008_m01_real_navigation_benchmark_source_preflight",
            "selected": True,
            "decision": "selected_next",
            "next_unit": "E008-M01 real navigation benchmark/source preflight and episode contract",
            "launch_long_job_now": False,
            "reason": [
                "E007 proxy bridge table is now packaged and reviewer-defensible.",
                "Direction B requires real navigation `SR` / `SPL`, but the next step must choose benchmark/source, start poses, episodes, and baselines before any simulator run.",
                "A preflight/contract step is low-risk and avoids launching a long job without a defensible evaluation design.",
            ],
        },
        {
            "rank": 2,
            "route_id": "full_real_navigation_execution_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "simulator_navmesh_controller_execution",
            "launch_long_job_now": False,
            "reason": [
                "Real navigation execution needs a benchmark/source contract first.",
                "`OldLocationDeadEndCostM` is still blocked without robot/start-pose or executed navigation.",
            ],
        },
        {
            "rank": 3,
            "route_id": "external_detector_mapping_baseline_restart_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "`OpenMask3D` / `HOV-SG` / additional map baseline route",
            "launch_long_job_now": False,
            "reason": [
                "E007-M06 did not show that the bridge table is dominated by proposal-source limits.",
                "External baselines remain useful later, but real navigation source design is the next Direction B bottleneck.",
            ],
        },
        {
            "rank": 4,
            "route_id": "paper_folder_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "paper folder creation",
            "launch_long_job_now": False,
            "reason": [
                "Paper folder should wait until thesis, main result table, method figure, target venue, and claim-evidence ledger are concrete.",
                "E007 provides one table package, but real navigation and final robustness claims are still open.",
            ],
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "action": "Create E008-M01 real navigation benchmark/source preflight and episode contract.",
            "status": "next",
            "notes": "No simulator or long-running job should launch before the contract is written.",
        },
        {
            "order": 2,
            "action": "Carry forward E007-Final-A table rows into the future paper claim ledger.",
            "status": "ready",
            "notes": "Use proxy boundary and source-limit columns.",
        },
        {
            "order": 3,
            "action": "Keep `OldLocationDeadEndCostM` blocked until start-pose/executed navigation exists.",
            "status": "blocked_claim",
            "notes": "E007-M06 old-first zero-step evidence is the reason.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    table_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    reviewer_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    table = [
        "| Policy | Full Success | Source-Ready LB | Direct/Failure LB | Path Cost | `PathAttemptSPLProxy` | Source-Limited |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in table_rows:
        table.append(
            f"| `{row['policy']}` | {row['full_success_rows']} / {row['query_rows']} | "
            f"{row['source_ready_lower_bound_success_rows']} / {row['query_rows']} | "
            f"{row['direct_failure_lower_bound_success_rows']} / {row['query_rows']} | "
            f"{row['mean_path_expected_search_cost_m']} | {row['mean_path_attempt_spl_proxy']} | "
            f"{row['source_limited_rows']} / {row['query_rows']} |"
        )

    claims = ["| Claim Type | Claim | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claims.append(f"| `{row['claim_type']}` | {row['paper_claim']} | {row['boundary']} |")

    reviewers = ["| Reviewer Issue | Defense | Must Show |", "| --- | --- | --- |"]
    for row in reviewer_rows:
        reviewers.append(f"| {row['reviewer_issue']} | {row['defense']} | {row['must_show_in_paper']} |")

    routes = ["| Rank | Route | Decision | Next Unit |", "| ---: | --- | --- | --- |"]
    for row in route_rows:
        routes.append(f"| {row['rank']} | `{row['route_id']}` | `{row['decision']}` | {row['next_unit']} |")

    return f"""# E007-M07 Bridge Table Package And Navigation Decision

## Facts

- Status: `{coverage["status"]}`.
- Paper table package ready: {coverage["paper_table_package_ready"]}.
- Bridge table role: `{coverage["bridge_table_role"]}`.
- Real navigation `SR` / `SPL` ready: {str(coverage["real_navigation_sr_spl_ready"]).lower()}.
- Selected next unit: {coverage["selected_next_unit"]}.

## Final E007 Table Package

{chr(10).join(table)}

## Claim-Evidence Ledger

{chr(10).join(claims)}

## Reviewer Defense Package

{chr(10).join(reviewers)}

## Navigation Expansion Decision

{chr(10).join(routes)}

## Agent Inference

- E007 should be treated as a completed bridge-table package, not as real navigation evidence.
- The next top-tier bottleneck is the real navigation benchmark/source contract, not another proxy table.
- The next step should be `E008-M01` preflight/contract only; do not launch simulator or long-running jobs yet.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m05 = read_json(M05_DIR / "coverage.json")
    m06 = read_json(M06_DIR / "coverage.json")
    bridge_rows = read_jsonl(M05_DIR / "bridge_table_rows.jsonl")
    sensitivity_rows = read_jsonl(M06_DIR / "policy_sensitivity_rows.jsonl")
    delta_rows = read_jsonl(M06_DIR / "paired_delta_sensitivity_rows.jsonl")
    if not bridge_rows:
        raise RuntimeError("Missing E007-M05 bridge table rows.")
    if not sensitivity_rows:
        raise RuntimeError("Missing E007-M06 policy sensitivity rows.")
    if not delta_rows:
        raise RuntimeError("Missing E007-M06 paired delta sensitivity rows.")

    table_rows = build_paper_table_rows(bridge_rows, sensitivity_rows)
    claim_rows = build_claim_ledger_rows(delta_rows)
    reviewer_rows = build_reviewer_package_rows()
    route_rows = build_navigation_decision_rows()
    next_action_rows = build_next_action_rows()
    selected = next(row for row in route_rows if row["selected"])

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m07_bridge_table_package_navigation_decision_ready",
        "version": VERSION,
        "m05_status": m05.get("status"),
        "m06_status": m06.get("status"),
        "paper_table_package_ready": True,
        "bridge_table_role": "paper_facing_occupancy_grid_path_cost_proxy_table",
        "table_rows": len(table_rows),
        "allowed_claim_rows": sum(1 for row in claim_rows if row["claim_type"].startswith("allowed")),
        "blocked_claim_rows": sum(1 for row in claim_rows if row["claim_type"] == "blocked"),
        "real_navigation_sr_spl_ready": False,
        "old_location_dead_end_cost_primary_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
        "selected_route": selected["route_id"],
        "selected_next_unit": selected["next_unit"],
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "paper_table_rows.jsonl", table_rows)
    write_jsonl(OUT_DIR / "claim_evidence_ledger_rows.jsonl", claim_rows)
    write_jsonl(OUT_DIR / "reviewer_defense_package_rows.jsonl", reviewer_rows)
    write_jsonl(OUT_DIR / "navigation_expansion_decision_rows.jsonl", route_rows)
    write_jsonl(OUT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "paper_table_rows": table_rows,
            "claim_evidence_ledger_rows": claim_rows,
            "reviewer_defense_package_rows": reviewer_rows,
            "navigation_expansion_decision_rows": route_rows,
            "next_action_rows": next_action_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, table_rows, claim_rows, reviewer_rows, route_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
