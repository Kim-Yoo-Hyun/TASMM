#!/usr/bin/env python3
"""Define the E007 navigation/path-cost bridge contract."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M01_navigation_path_cost_bridge_contract_v0"
VERSION = "e007_m01_navigation_path_cost_bridge_contract_v0"

E002_GRID_DIR = ROOT / "experiments" / "E002_path_cost_bridge" / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
E005_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E005_M45_DIR = E005_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
E005_M69_DIR = E005_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
E005_M100_DIR = E005_ROOT / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"
E005_M101_DIR = E005_ROOT / "artifacts" / "E005-M101_map_assisted_claim_boundary_navigation_decision_v0"


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


def load_conceptgraphs_eval_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(E005_M45_DIR.glob("candidate_eval_rows_heldout_b*.jsonl")):
        rows.extend(read_jsonl(path))
    return rows


def load_real_detector_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(E005_M69_DIR.glob("heldout_b*/container_output/real_proposals.jsonl")):
        rows.extend(read_jsonl(path))
    return rows


def build_source_readiness_rows(
    selected_rows: list[dict[str, Any]],
    grid_rows: list[dict[str, Any]],
    conceptgraphs_rows: list[dict[str, Any]],
    real_detector_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_row_uids = {row["row_uid"] for row in selected_rows}
    selected_query_uids = {row["query_uid"] for row in selected_rows}
    grid_by_row = {row["row_uid"]: row for row in grid_rows}
    grid_overlap = [grid_by_row[row_uid] for row_uid in selected_row_uids if row_uid in grid_by_row]
    conceptgraphs_query_uids = {row["query_uid"] for row in conceptgraphs_rows if row.get("query_uid")}
    real_detector_scan_labels = {
        (row.get("scan_id"), row.get("label_canonical")) for row in real_detector_rows if row.get("scan_id")
    }

    return [
        {
            "source_id": "m100_selected_policy_rows",
            "role": "query_level_candidate_visit_order",
            "status": "ready_for_contract",
            "rows": len(selected_rows),
            "query_overlap_rows": len(selected_rows),
            "coordinate_sequence_ready": False,
            "notes": "M100 stores policy order and query-level cost, but not a materialized coordinate sequence.",
        },
        {
            "source_id": "e002_occupancy_grid_astar_v0",
            "role": "path_cost_source",
            "status": "compatible_proxy_source",
            "rows": len(grid_rows),
            "query_overlap_rows": len(grid_overlap),
            "target_grid_reachable_overlap_rows": sum(1 for row in grid_overlap if row.get("target_grid_reachable")),
            "grid_path_ready_overlap_rows": sum(1 for row in grid_overlap if row.get("grid_path_cost_ready")),
            "real_navigation_path_cost_ready_rows": sum(1 for row in grid_overlap if row.get("real_navigation_path_cost_ready")),
            "row_band_counts": dict(Counter(row.get("row_band") for row in grid_overlap)),
            "notes": "All 195 M100 rows overlap E002 grid rows, but this is still an occupancy-grid proxy, not real navigation.",
        },
        {
            "source_id": "e005_m45_conceptgraphs_candidate_eval",
            "role": "external_map_candidate_coordinates",
            "status": "ready_for_materialization_audit",
            "rows": len(conceptgraphs_rows),
            "unique_query_rows": len(conceptgraphs_query_uids),
            "query_overlap_rows": len(selected_query_uids & conceptgraphs_query_uids),
            "top5_rows": sum(1 for row in conceptgraphs_rows if row.get("rank", 999999) <= 5),
            "coordinate_fields": ["candidate_center_xyz", "candidate_bbox_min_xyz", "candidate_bbox_max_xyz"],
            "notes": "ConceptGraphs top-k candidates have world coordinates for the 195-row denominator.",
        },
        {
            "source_id": "e005_m69_real_detector_proposals",
            "role": "detector_confidence_candidate_coordinates",
            "status": "available_with_join_audit_needed",
            "rows": len(real_detector_rows),
            "unique_scan_label_pairs": len(real_detector_scan_labels),
            "coordinate_fields": ["centroid_world_m"],
            "notes": "GroundingDINO RGB-D proposal rows have coordinates, but E007-M02 must join them back to query rows and ranks.",
        },
        {
            "source_id": "simulator_or_navmesh",
            "role": "real_navigation_source",
            "status": "not_ready",
            "rows": 0,
            "query_overlap_rows": 0,
            "notes": "No simulator episode, navmesh geodesic path, or robot trajectory source is integrated in E007-M01.",
        },
    ]


def build_metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric_id": "PathExpectedSearchCost",
            "status": "contract_ready",
            "unit": "meters_or_source_limited",
            "definition": "Cumulative path cost of the executed candidate visit sequence until success or exhaustion.",
            "primary_source": "occupancy_grid_astar_v0",
            "fallback_source": "euclidean_polyline_proxy_v0 only for sensitivity",
            "blocked_shortcut": "Do not reuse M100 candidate-count `ExpectedSearchCost` as path cost.",
        },
        {
            "metric_id": "PathAttemptSPLProxy",
            "status": "contract_ready",
            "unit": "ratio",
            "definition": "Success-weighted shortest target path divided by executed path cost, clipped to [0, 1].",
            "primary_source": "occupancy_grid_astar_v0 target and candidate route costs",
            "fallback_source": "none for main path table if target or route is source-limited",
            "blocked_shortcut": "Do not report this as real navigation `SPL`.",
        },
        {
            "metric_id": "OldLocationDeadEndCostM",
            "status": "contract_ready",
            "unit": "meters",
            "definition": "Path cost spent visiting stale old-memory locations before fallback or failure.",
            "primary_source": "old memory coordinate plus occupancy-grid route materialization",
            "fallback_source": "fixed inspection penalty only for diagnostic comparison",
            "blocked_shortcut": "Do not use `old_location_dead_end_expected` as a policy input.",
        },
        {
            "metric_id": "PathSourceLimitedRate",
            "status": "contract_ready",
            "unit": "row_fraction",
            "definition": "Fraction of rows/candidates that cannot receive a valid proxy path because of missing projection or disconnected free space.",
            "primary_source": "E002 grid projection and route status fields",
            "fallback_source": "none",
            "blocked_shortcut": "Do not silently drop source-limited rows from the denominator.",
        },
        {
            "metric_id": "FailureReductionByBand",
            "status": "contract_ready",
            "unit": "rows",
            "definition": "Policy failure changes split by `row_band`, `task_context_id`, source-limited status, and fallback usage.",
            "primary_source": "M100 selected rows joined with E002/E005 route rows",
            "fallback_source": "query-level row groups if path source is missing",
            "blocked_shortcut": "Do not average away significant-moved failures.",
        },
    ]


def build_baseline_rows(paper_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    include = {
        "real_static_memory_only_v0": "static stale memory baseline",
        "real_detector_confidence_top5_v0": "detector-confidence ranking baseline",
        "conceptgraphs_only_strict_top5_v0": "ConceptGraphs-only open-vocabulary map baseline",
        "real_context_agnostic_memory_trust_reobserve_v0": "task-agnostic re-observation baseline",
        "h001_real_task_context_memory_trust_v0": "H001 memory-trust baseline",
        "h001_then_conceptgraphs_top5_on_observed_miss_v0": "selected H001 + ConceptGraphs fallback policy",
        "significant_moved_conceptgraphs_first_else_h001_v0": "old-dead-end ablation",
    }
    rows: list[dict[str, Any]] = []
    for row in paper_rows:
        policy = row["policy"]
        if policy not in include:
            continue
        rows.append(
            {
                "policy": policy,
                "bridge_role": include[policy],
                "query_rows": row["query_rows"],
                "query_success_rows": row["success_rows"],
                "query_attempt_spl_proxy": row["attempt_spl_proxy"],
                "query_mean_expected_search_cost": row["mean_expected_search_cost_all"],
                "path_cost_metric_required": True,
                "path_metric_ready": False,
                "include_in_e007_m02": policy != "significant_moved_conceptgraphs_first_else_h001_v0",
                "include_as_ablation": policy == "significant_moved_conceptgraphs_first_else_h001_v0",
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C-E007-M01-001",
            "claim": "M100 can be bridged to path-aware search cost without changing the 195-row denominator.",
            "status": "contract_supported",
            "evidence": "M100 row ids fully overlap E002 occupancy-grid rows.",
            "boundary": "No path metric is reported in M01; M02 must materialize candidate routes first.",
        },
        {
            "claim_id": "C-E007-M01-002",
            "claim": "E007 should use E002 `occupancy_grid_astar_v0` as the first path-cost source.",
            "status": "selected",
            "evidence": "The source already covers the M100 denominator and exposes reachable/source-limited rows.",
            "boundary": "This remains a free-space proxy, not simulator or real robot navigation.",
        },
        {
            "claim_id": "C-E007-M01-003",
            "claim": "Real navigation `SR` / `SPL` is not ready.",
            "status": "blocked",
            "evidence": "No simulator episode, navmesh geodesic path, collision model, or trajectory execution is integrated.",
            "boundary": "Use `PathAttemptSPLProxy` or `AttemptSPL` only with explicit proxy naming.",
        },
        {
            "claim_id": "C-E007-M01-004",
            "claim": "Human intent remains a structured task-context condition rather than a main contribution.",
            "status": "unchanged",
            "evidence": "E007-M01 adds navigation/path-cost contract only.",
            "boundary": "Human intent main claim still needs a separate E006 context-sensitive utility benchmark.",
        },
    ]


def build_command_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "unit": "E007-M01",
            "status": "ready",
            "purpose": "Write navigation/path-cost bridge contract.",
            "command": "python experiments/E007_navigation_path_cost_bridge/tools/plan_m01_navigation_path_cost_bridge_contract.py",
            "docker_required": False,
            "output": str(OUT_DIR.relative_to(ROOT)),
        },
        {
            "unit": "E007-M02",
            "status": "next",
            "purpose": "Join M100 policy rows with E002 grid rows, ConceptGraphs candidates, and real detector candidates.",
            "command": "python experiments/E007_navigation_path_cost_bridge/tools/audit_m02_path_source_compatibility.py",
            "docker_required": False,
            "output": "experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/",
        },
        {
            "unit": "E007-M03",
            "status": "planned",
            "purpose": "Evaluate path-aware policies under `occupancy_grid_astar_v0`.",
            "command": "python experiments/E007_navigation_path_cost_bridge/tools/run_m03_path_cost_policy_eval.py",
            "docker_required": False,
            "output": "experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_path_cost_policy_eval_v0/",
        },
        {
            "unit": "E007-M04",
            "status": "planned_after_proxy",
            "purpose": "Decide whether simulator/navmesh execution is required before `SR` / `SPL` claims.",
            "command": "TBD after E007-M03",
            "docker_required": True,
            "output": "TBD",
        },
    ]


def build_contract(
    coverage: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "selected_path_cost_source": coverage["selected_path_cost_source"],
        "selected_next_unit": coverage["selected_next_unit"],
        "scope": "Bridge M100 query-level candidate visit order to path-aware search-cost proxy metrics.",
        "denominator": {
            "query_rows": coverage["query_rows"],
            "row_uid_overlap_with_e002": coverage["e002_row_uid_overlap_rows"],
            "denominator_preserved": coverage["denominator_preserved"],
        },
        "minimum_inputs": [
            "M100 selected policy rows with `row_uid`, `query_uid`, fallback trigger, and candidate visit order.",
            "E002 `occupancy_grid_astar_v0` grid rows for path source and source-limited accounting.",
            "E005-M45 `ConceptGraphs` candidate coordinates for external map candidate route materialization.",
            "E005-M69 real detector proposal coordinates for detector-confidence baseline route materialization.",
        ],
        "metrics": [row["metric_id"] for row in metric_rows],
        "baselines": [row["policy"] for row in baseline_rows if row["include_in_e007_m02"]],
        "blocked_shortcuts": [
            "Do not equate M100 query-level `AttemptSPL` with path `SPL`.",
            "Do not drop target-unreachable or candidate-unreachable rows without a source-limited label.",
            "Do not use target rank, target match distance, target detection labels, or success labels as policy inputs.",
            "Do not claim final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL` from E007-M01.",
        ],
    }


def build_report(
    coverage: dict[str, Any],
    source_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
) -> str:
    source_lines = [
        "| Source | Role | Status | Rows | Overlap | Notes |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in source_rows:
        source_lines.append(
            f"| `{row['source_id']}` | {row['role']} | `{row['status']}` | "
            f"{row.get('rows', 0)} | {row.get('query_overlap_rows', 'n/a')} | {row['notes']} |"
        )

    metric_lines = [
        "| Metric | Status | Primary Source | Blocked Shortcut |",
        "| --- | --- | --- | --- |",
    ]
    for row in metric_rows:
        metric_lines.append(
            f"| `{row['metric_id']}` | `{row['status']}` | {row['primary_source']} | {row['blocked_shortcut']} |"
        )

    baseline_lines = [
        "| Policy | Role | Query Success | Query AttemptSPL | Include M02 |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in baseline_rows:
        baseline_lines.append(
            f"| `{row['policy']}` | {row['bridge_role']} | "
            f"{row['query_success_rows']} / {row['query_rows']} | {row['query_attempt_spl_proxy']} | "
            f"{row['include_in_e007_m02']} |"
        )

    claim_lines = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    command_lines = ["| Unit | Status | Command | Docker |", "| --- | --- | --- | --- |"]
    for row in command_rows:
        command_lines.append(f"| {row['unit']} | `{row['status']}` | `{row['command']}` | {row['docker_required']} |")

    return f"""# E007-M01 Navigation Path-Cost Bridge Contract

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- M100 selected policy: `{coverage["m100_selected_policy"]}`.
- E002 row overlap: {coverage["e002_row_uid_overlap_rows"]} / {coverage["query_rows"]}.
- E002 target-grid reachable overlap: {coverage["e002_target_grid_reachable_overlap_rows"]} / {coverage["query_rows"]}.
- Selected path-cost source: `{coverage["selected_path_cost_source"]}`.
- Selected next unit: {coverage["selected_next_unit"]}.
- Real navigation `SR` / `SPL` ready: false.

## Source Readiness

{chr(10).join(source_lines)}

## Metric Contract

{chr(10).join(metric_lines)}

## Baseline Contract

{chr(10).join(baseline_lines)}

## Claim Boundary

{chr(10).join(claim_lines)}

## Command Plan

{chr(10).join(command_lines)}

## Agent Inference

- E007 should not jump directly from query-level `AttemptSPL` to real navigation `SPL`.
- The right next step is E007-M02 candidate route materialization and source-compatibility audit.
- If E007-M02 preserves the 195-row denominator, E007-M03 can compute a paper-facing path-cost proxy table.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    m100_coverage = read_json(E005_M100_DIR / "coverage.json")
    m101_coverage = read_json(E005_M101_DIR / "coverage.json")
    paper_rows = read_jsonl(E005_M101_DIR / "paper_table_rows.jsonl")
    selected_rows = read_jsonl(E005_M100_DIR / "selected_policy_rows.jsonl")
    grid_rows = read_jsonl(E002_GRID_DIR / "grid_query_rows.jsonl")
    conceptgraphs_rows = load_conceptgraphs_eval_rows()
    real_detector_rows = load_real_detector_rows()

    if not selected_rows:
        raise RuntimeError("Missing M100 selected policy rows.")
    if not grid_rows:
        raise RuntimeError("Missing E002 occupancy-grid rows.")
    if not paper_rows:
        raise RuntimeError("Missing M101 paper-table rows.")

    selected_row_uids = {row["row_uid"] for row in selected_rows}
    grid_by_row = {row["row_uid"]: row for row in grid_rows}
    grid_overlap = [grid_by_row[row_uid] for row_uid in selected_row_uids if row_uid in grid_by_row]

    source_rows = build_source_readiness_rows(selected_rows, grid_rows, conceptgraphs_rows, real_detector_rows)
    metric_rows = build_metric_contract_rows()
    baseline_rows = build_baseline_rows(paper_rows)
    claim_rows = build_claim_boundary_rows()
    command_rows = build_command_plan_rows()

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m01_navigation_path_cost_bridge_contract_ready",
        "version": VERSION,
        "m100_status": m100_coverage.get("status"),
        "m101_status": m101_coverage.get("status"),
        "m100_selected_policy": m100_coverage.get("selected_policy"),
        "m100_selected_success_rows": m100_coverage.get("selected_success_rows"),
        "m100_selected_attempt_spl": m100_coverage.get("selected_attempt_spl_proxy"),
        "query_rows": len(selected_rows),
        "e002_grid_query_rows": len(grid_rows),
        "e002_row_uid_overlap_rows": len(grid_overlap),
        "e002_target_grid_reachable_overlap_rows": sum(1 for row in grid_overlap if row.get("target_grid_reachable")),
        "e002_grid_path_ready_overlap_rows": sum(1 for row in grid_overlap if row.get("grid_path_cost_ready")),
        "conceptgraphs_candidate_eval_rows": len(conceptgraphs_rows),
        "conceptgraphs_query_overlap_rows": len(
            {row["query_uid"] for row in selected_rows}
            & {row["query_uid"] for row in conceptgraphs_rows if row.get("query_uid")}
        ),
        "real_detector_proposal_rows": len(real_detector_rows),
        "denominator_preserved": len(grid_overlap) == len(selected_rows),
        "selected_path_cost_source": "e002_occupancy_grid_astar_v0",
        "path_cost_bridge_contract_ready": True,
        "path_cost_metric_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": "E007-M02 path-source compatibility and candidate-route materialization audit",
    }

    contract = build_contract(coverage, metric_rows, source_rows, baseline_rows)

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "contract.json", contract)
    write_jsonl(OUT_DIR / "source_readiness_rows.jsonl", source_rows)
    write_jsonl(OUT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(OUT_DIR / "baseline_rows.jsonl", baseline_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(OUT_DIR / "command_plan_rows.jsonl", command_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "contract": contract,
            "source_readiness_rows": source_rows,
            "metric_contract_rows": metric_rows,
            "baseline_rows": baseline_rows,
            "claim_boundary_rows": claim_rows,
            "command_plan_rows": command_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, source_rows, metric_rows, baseline_rows, claim_rows, command_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
