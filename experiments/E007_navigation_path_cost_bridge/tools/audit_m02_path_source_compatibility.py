#!/usr/bin/env python3
"""Materialize E007-M02 candidate routes and audit path-source compatibility."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M02_path_source_compatibility_v0"
VERSION = "e007_m02_path_source_compatibility_v0"

E002_GRID_DIR = ROOT / "experiments" / "E002_path_cost_bridge" / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
E005_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E005_M45_DIR = E005_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
E005_M69_DIR = E005_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
E005_M75_DIR = E005_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
E005_M100_DIR = E005_ROOT / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"
E007_M01_DIR = EXP_ROOT / "artifacts" / "E007-M01_navigation_path_cost_bridge_contract_v0"

POLICIES = [
    "real_static_memory_only_v0",
    "real_detector_confidence_top5_v0",
    "conceptgraphs_only_strict_top5_v0",
    "real_context_agnostic_memory_trust_reobserve_v0",
    "h001_real_task_context_memory_trust_v0",
    "h001_then_conceptgraphs_top5_on_observed_miss_v0",
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


def index_by_policy_query(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["policy"], row["query_uid"]): row for row in rows if row.get("policy") and row.get("query_uid")}


def load_conceptgraphs_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(E005_M45_DIR.glob("candidate_eval_rows_heldout_b*.jsonl")):
        rows.extend(read_jsonl(path))
    return rows


def load_real_detector_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(E005_M69_DIR.glob("heldout_b*/container_output/real_proposals.jsonl")):
        rows.extend(read_jsonl(path))
    return rows


def has_xyz(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(isinstance(item, (int, float)) for item in value)


def source_limited_start(grid_row: dict[str, Any]) -> bool:
    status = grid_row.get("start_projection_status")
    return status in {None, "start_unprojectable", "no_free_cell_within_radius"}


def old_memory_row(
    *,
    query_row: dict[str, Any],
    grid_row: dict[str, Any],
    policy: str,
    route_index: int,
    segment: str,
    eval_row: dict[str, Any],
) -> dict[str, Any]:
    xyz = grid_row.get("old_scene_aligned_centroid")
    coord_ready = has_xyz(xyz)
    projection_ready = coord_ready and not source_limited_start(grid_row)
    return {
        "route_uid": f"{query_row['query_uid']}|{policy}|{route_index:03d}",
        "policy": policy,
        "query_uid": query_row["query_uid"],
        "row_uid": query_row["row_uid"],
        "base_row_uid": query_row.get("base_row_uid"),
        "route_index": route_index,
        "segment": segment,
        "candidate_source": "old_memory",
        "candidate_uid": f"old_memory:{query_row.get('base_row_uid')}",
        "candidate_rank": 1,
        "candidate_label": query_row.get("label_canonical"),
        "candidate_xyz": xyz,
        "coordinate_ready": coord_ready,
        "candidate_grid_projection_ready": projection_ready,
        "path_source_status": "old_memory_start_ready" if projection_ready else "old_memory_start_source_limited",
        "path_cost_metric_ready": False,
        "grid_path_cost_source": grid_row.get("grid_path_cost_source"),
        "start_projection_status": grid_row.get("start_projection_status"),
        "target_grid_reachable_eval_only": grid_row.get("target_grid_reachable"),
        "query_bridge_success_eval_only": eval_row.get("query_bridge_success"),
        "candidate_is_target_eval_only": eval_row.get("success_source") == "old_memory",
        "row_band": query_row.get("row_band"),
        "task_context_id": query_row.get("task_context_id"),
    }


def detector_route_rows(
    *,
    query_row: dict[str, Any],
    grid_row: dict[str, Any],
    eval_row: dict[str, Any],
    detector_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    policy: str,
    start_index: int,
    limit: int,
    segment: str,
) -> list[dict[str, Any]]:
    key = (query_row.get("current_rescan_id"), query_row.get("label_canonical"))
    candidates = detector_by_scan_label.get(key, [])[:limit]
    rows: list[dict[str, Any]] = []
    for offset, candidate in enumerate(candidates, start=0):
        route_index = start_index + offset
        xyz = candidate.get("centroid_world_m")
        coord_ready = has_xyz(xyz)
        rows.append(
            {
                "route_uid": f"{query_row['query_uid']}|{policy}|{route_index:03d}",
                "policy": policy,
                "query_uid": query_row["query_uid"],
                "row_uid": query_row["row_uid"],
                "base_row_uid": query_row.get("base_row_uid"),
                "route_index": route_index,
                "segment": segment,
                "candidate_source": "real_detector_rgbd_proposal",
                "candidate_uid": candidate.get("proposal_uid") or candidate.get("row_uid"),
                "candidate_rank": candidate.get("pre_cap_group_rank") or candidate.get("pre_cap_rank"),
                "candidate_label": candidate.get("label_canonical"),
                "candidate_xyz": xyz,
                "coordinate_ready": coord_ready,
                "candidate_grid_projection_ready": False,
                "path_source_status": "external_coordinate_ready_grid_projection_pending"
                if coord_ready
                else "external_coordinate_missing",
                "path_cost_metric_ready": False,
                "grid_path_cost_source": grid_row.get("grid_path_cost_source"),
                "selection_score": candidate.get("selection_score"),
                "confidence": candidate.get("confidence"),
                "target_grid_reachable_eval_only": grid_row.get("target_grid_reachable"),
                "query_bridge_success_eval_only": eval_row.get("query_bridge_success"),
                "candidate_is_target_eval_only": candidate.get("proposal_uid") == eval_row.get("target_proposal_uid"),
                "row_band": query_row.get("row_band"),
                "task_context_id": query_row.get("task_context_id"),
            }
        )
    return rows


def conceptgraphs_route_rows(
    *,
    query_row: dict[str, Any],
    grid_row: dict[str, Any],
    eval_row: dict[str, Any],
    conceptgraphs_by_query: dict[str, list[dict[str, Any]]],
    policy: str,
    start_index: int,
    limit: int,
    segment: str,
) -> list[dict[str, Any]]:
    candidates = conceptgraphs_by_query.get(query_row["query_uid"], [])[:limit]
    rows: list[dict[str, Any]] = []
    for offset, candidate in enumerate(candidates, start=0):
        route_index = start_index + offset
        xyz = candidate.get("candidate_center_xyz")
        coord_ready = has_xyz(xyz)
        rows.append(
            {
                "route_uid": f"{query_row['query_uid']}|{policy}|{route_index:03d}",
                "policy": policy,
                "query_uid": query_row["query_uid"],
                "row_uid": query_row["row_uid"],
                "base_row_uid": query_row.get("base_row_uid"),
                "route_index": route_index,
                "segment": segment,
                "candidate_source": "conceptgraphs_map_candidate",
                "candidate_uid": candidate.get("candidate_uid"),
                "candidate_rank": candidate.get("rank"),
                "candidate_label": candidate.get("target_label_canonical") or candidate.get("query_label"),
                "candidate_xyz": xyz,
                "coordinate_ready": coord_ready,
                "candidate_grid_projection_ready": False,
                "path_source_status": "external_coordinate_ready_grid_projection_pending"
                if coord_ready
                else "external_coordinate_missing",
                "path_cost_metric_ready": False,
                "grid_path_cost_source": grid_row.get("grid_path_cost_source"),
                "semantic_score": candidate.get("semantic_score"),
                "target_grid_reachable_eval_only": grid_row.get("target_grid_reachable"),
                "query_bridge_success_eval_only": eval_row.get("query_bridge_success"),
                "candidate_is_target_eval_only": bool(candidate.get("eval_bbox_success_strict")),
                "row_band": query_row.get("row_band"),
                "task_context_id": query_row.get("task_context_id"),
            }
        )
    return rows


def memory_trust_route_rows(
    *,
    query_row: dict[str, Any],
    grid_row: dict[str, Any],
    eval_row: dict[str, Any],
    materialization_row: dict[str, Any],
    detector_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    policy: str,
    segment: str,
) -> list[dict[str, Any]]:
    route_rows: list[dict[str, Any]] = []
    returned = int(materialization_row.get("returned_location_count") or 0)
    if returned <= 0:
        return route_rows

    route_index = 1
    remaining = returned
    if materialization_row.get("old_memory_first"):
        route_rows.append(
            old_memory_row(
                query_row=query_row,
                grid_row=grid_row,
                policy=policy,
                route_index=route_index,
                segment=segment,
                eval_row=eval_row,
            )
        )
        route_index += 1
        remaining -= 1

    if remaining > 0:
        route_rows.extend(
            detector_route_rows(
                query_row=query_row,
                grid_row=grid_row,
                eval_row=eval_row,
                detector_by_scan_label=detector_by_scan_label,
                policy=policy,
                start_index=route_index,
                limit=remaining,
                segment=segment,
            )
        )
    return route_rows


def build_route_rows(
    selected_rows: list[dict[str, Any]],
    m100_by_policy_query: dict[tuple[str, str], dict[str, Any]],
    m75_by_policy_query: dict[tuple[str, str], dict[str, Any]],
    grid_by_row: dict[str, dict[str, Any]],
    conceptgraphs_by_query: dict[str, list[dict[str, Any]]],
    detector_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    route_rows: list[dict[str, Any]] = []
    for query_row in selected_rows:
        grid_row = grid_by_row.get(query_row["row_uid"])
        if not grid_row:
            continue

        static_eval = m75_by_policy_query.get(("real_static_memory_only_v0", query_row["query_uid"]), {})
        route_rows.append(
            old_memory_row(
                query_row=query_row,
                grid_row=grid_row,
                policy="real_static_memory_only_v0",
                route_index=1,
                segment="static_old_memory",
                eval_row=static_eval,
            )
        )

        detector_eval = m75_by_policy_query.get(("real_detector_confidence_top5_v0", query_row["query_uid"]), {})
        route_rows.extend(
            detector_route_rows(
                query_row=query_row,
                grid_row=grid_row,
                eval_row=detector_eval,
                detector_by_scan_label=detector_by_scan_label,
                policy="real_detector_confidence_top5_v0",
                start_index=1,
                limit=int(detector_eval.get("returned_location_count") or 5),
                segment="detector_confidence_top5",
            )
        )

        cg_eval = m100_by_policy_query.get(("conceptgraphs_only_strict_top5_v0", query_row["query_uid"]), {})
        route_rows.extend(
            conceptgraphs_route_rows(
                query_row=query_row,
                grid_row=grid_row,
                eval_row=cg_eval,
                conceptgraphs_by_query=conceptgraphs_by_query,
                policy="conceptgraphs_only_strict_top5_v0",
                start_index=1,
                limit=5,
                segment="conceptgraphs_only_top5",
            )
        )

        context_eval = m75_by_policy_query.get(("real_context_agnostic_memory_trust_reobserve_v0", query_row["query_uid"]), {})
        route_rows.extend(
            memory_trust_route_rows(
                query_row=query_row,
                grid_row=grid_row,
                eval_row=context_eval,
                materialization_row=context_eval,
                detector_by_scan_label=detector_by_scan_label,
                policy="real_context_agnostic_memory_trust_reobserve_v0",
                segment="context_agnostic_memory_then_detector",
            )
        )

        h001_eval = m100_by_policy_query.get(("h001_real_task_context_memory_trust_v0", query_row["query_uid"]), {})
        h001_materialization = m75_by_policy_query.get(
            ("real_task_context_memory_trust_reobserve_v0", query_row["query_uid"]), {}
        )
        route_rows.extend(
            memory_trust_route_rows(
                query_row=query_row,
                grid_row=grid_row,
                eval_row=h001_eval,
                materialization_row=h001_materialization,
                detector_by_scan_label=detector_by_scan_label,
                policy="h001_real_task_context_memory_trust_v0",
                segment="h001_memory_then_detector",
            )
        )

        selected_eval = m100_by_policy_query.get(
            ("h001_then_conceptgraphs_top5_on_observed_miss_v0", query_row["query_uid"]), {}
        )
        selected_h001_rows = memory_trust_route_rows(
            query_row=query_row,
            grid_row=grid_row,
            eval_row=selected_eval,
            materialization_row=h001_materialization,
            detector_by_scan_label=detector_by_scan_label,
            policy="h001_then_conceptgraphs_top5_on_observed_miss_v0",
            segment="h001_memory_then_detector",
        )
        route_rows.extend(selected_h001_rows)
        if selected_eval.get("fallback_used"):
            route_rows.extend(
                conceptgraphs_route_rows(
                    query_row=query_row,
                    grid_row=grid_row,
                    eval_row=selected_eval,
                    conceptgraphs_by_query=conceptgraphs_by_query,
                    policy="h001_then_conceptgraphs_top5_on_observed_miss_v0",
                    start_index=len(selected_h001_rows) + 1,
                    limit=5,
                    segment="conceptgraphs_fallback_top5",
                )
            )
    return route_rows


def intended_count(policy: str, query_uid: str, m100: dict[tuple[str, str], dict[str, Any]], m75: dict[tuple[str, str], dict[str, Any]]) -> int:
    if policy == "real_static_memory_only_v0":
        return 1
    if policy == "real_detector_confidence_top5_v0":
        row = m75.get((policy, query_uid), {})
        return int(row.get("returned_location_count") or 0)
    if policy == "conceptgraphs_only_strict_top5_v0":
        return 5
    if policy == "real_context_agnostic_memory_trust_reobserve_v0":
        row = m75.get((policy, query_uid), {})
        return int(row.get("returned_location_count") or 0)
    if policy == "h001_real_task_context_memory_trust_v0":
        row = m75.get(("real_task_context_memory_trust_reobserve_v0", query_uid), {})
        return int(row.get("returned_location_count") or 0)
    if policy == "h001_then_conceptgraphs_top5_on_observed_miss_v0":
        h001 = m75.get(("real_task_context_memory_trust_reobserve_v0", query_uid), {})
        selected = m100.get((policy, query_uid), {})
        return int(h001.get("returned_location_count") or 0) + (5 if selected.get("fallback_used") else 0)
    raise KeyError(policy)


def eval_row_for_policy(
    policy: str,
    query_uid: str,
    m100: dict[tuple[str, str], dict[str, Any]],
    m75: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    if policy in {"conceptgraphs_only_strict_top5_v0", "h001_real_task_context_memory_trust_v0", "h001_then_conceptgraphs_top5_on_observed_miss_v0"}:
        return m100.get((policy, query_uid), {})
    if policy == "h001_real_task_context_memory_trust_v0":
        return m100.get((policy, query_uid), {})
    return m75.get((policy, query_uid), {})


def build_query_materialization_rows(
    selected_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    m100_by_policy_query: dict[tuple[str, str], dict[str, Any]],
    m75_by_policy_query: dict[tuple[str, str], dict[str, Any]],
    grid_by_row: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    routes_by_policy_query: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in route_rows:
        routes_by_policy_query[(row["policy"], row["query_uid"])].append(row)

    rows: list[dict[str, Any]] = []
    for query_row in selected_rows:
        grid_row = grid_by_row.get(query_row["row_uid"], {})
        for policy in POLICIES:
            routes = routes_by_policy_query.get((policy, query_row["query_uid"]), [])
            eval_row = eval_row_for_policy(policy, query_row["query_uid"], m100_by_policy_query, m75_by_policy_query)
            intended = intended_count(policy, query_row["query_uid"], m100_by_policy_query, m75_by_policy_query)
            coordinate_ready_count = sum(1 for row in routes if row.get("coordinate_ready"))
            projection_ready_count = sum(1 for row in routes if row.get("candidate_grid_projection_ready"))
            external_pending_count = sum(
                1 for row in routes if row.get("path_source_status") == "external_coordinate_ready_grid_projection_pending"
            )
            missing_coordinate_count = sum(1 for row in routes if row.get("path_source_status") == "external_coordinate_missing")
            if not routes and policy != "real_static_memory_only_v0":
                status = "source_limited_no_candidate_route"
            elif not routes and intended > 0:
                status = "missing_candidate_route"
            elif missing_coordinate_count:
                status = "coordinate_gap"
            elif external_pending_count:
                status = "coordinate_ready_external_projection_pending"
            elif projection_ready_count == len(routes) and routes:
                status = "path_source_ready_for_proxy_cost"
            elif not routes:
                status = "no_route_expected_or_no_candidate"
            else:
                status = "mixed_source_status"
            rows.append(
                {
                    "policy": policy,
                    "query_uid": query_row["query_uid"],
                    "row_uid": query_row["row_uid"],
                    "base_row_uid": query_row.get("base_row_uid"),
                    "intended_route_count": intended,
                    "materialized_route_count": len(routes),
                    "coordinate_ready_count": coordinate_ready_count,
                    "candidate_grid_projection_ready_count": projection_ready_count,
                    "external_projection_pending_count": external_pending_count,
                    "missing_coordinate_count": missing_coordinate_count,
                    "route_materialization_status": status,
                    "route_count_matches_intent": len(routes) >= intended,
                    "expected_search_cost_eval_only": eval_row.get("expected_search_cost"),
                    "returned_location_count_eval_only": eval_row.get("returned_location_count"),
                    "query_bridge_success_eval_only": eval_row.get("query_bridge_success"),
                    "success_source_eval_only": eval_row.get("success_source"),
                    "fallback_used_eval_only": eval_row.get("fallback_used", False),
                    "target_grid_reachable_eval_only": grid_row.get("target_grid_reachable"),
                    "row_band": query_row.get("row_band"),
                    "task_context_id": query_row.get("task_context_id"),
                }
            )
    return rows


def build_policy_summary_rows(query_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    query_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in route_rows:
        routes_by_policy[row["policy"]].append(row)
    for row in query_rows:
        query_by_policy[row["policy"]].append(row)

    rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        qrows = query_by_policy[policy]
        rrows = routes_by_policy[policy]
        status_counts = Counter(row["route_materialization_status"] for row in qrows)
        rows.append(
            {
                "policy": policy,
                "query_rows": len(qrows),
                "route_rows": len(rrows),
                "queries_with_materialized_route": sum(1 for row in qrows if row["materialized_route_count"] > 0),
                "queries_route_count_matches_intent": sum(1 for row in qrows if row["route_count_matches_intent"]),
                "coordinate_ready_route_rows": sum(1 for row in rrows if row.get("coordinate_ready")),
                "candidate_grid_projection_ready_route_rows": sum(1 for row in rrows if row.get("candidate_grid_projection_ready")),
                "external_projection_pending_route_rows": sum(
                    1 for row in rrows if row.get("path_source_status") == "external_coordinate_ready_grid_projection_pending"
                ),
                "missing_coordinate_route_rows": sum(1 for row in rrows if row.get("path_source_status") == "external_coordinate_missing"),
                "status_counts": dict(status_counts),
                "path_cost_metric_ready": False,
            }
        )
    return rows


def build_source_gap_rows(query_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gap_rows: list[dict[str, Any]] = []
    for row in query_rows:
        if row["route_materialization_status"] in {
            "missing_candidate_route",
            "coordinate_gap",
            "source_limited_no_candidate_route",
        }:
            gap_rows.append(
                {
                    "policy": row["policy"],
                    "query_uid": row["query_uid"],
                    "row_uid": row["row_uid"],
                    "gap_type": row["route_materialization_status"],
                    "intended_route_count": row["intended_route_count"],
                    "materialized_route_count": row["materialized_route_count"],
                    "row_band": row["row_band"],
                    "task_context_id": row["task_context_id"],
                }
            )
    return gap_rows


def build_claim_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C-E007-M02-001",
            "claim": "M100 policy rows can be materialized into candidate-route rows on the 195-row denominator.",
            "status": "supported_for_coordinate_audit",
            "evidence": f"{coverage['query_policy_rows']} query-policy rows and {coverage['route_rows']} route rows were generated.",
            "boundary": "This is route materialization, not path-cost evaluation.",
        },
        {
            "claim_id": "C-E007-M02-002",
            "claim": "`ConceptGraphs` and real detector candidates have coordinates but still need grid projection before path-cost metrics.",
            "status": "projection_pending",
            "evidence": f"External projection pending route rows: {coverage['external_projection_pending_route_rows']}.",
            "boundary": "Do not report `PathExpectedSearchCost` or `PathAttemptSPLProxy` until external candidates are projected onto the E002 grid.",
        },
        {
            "claim_id": "C-E007-M02-003",
            "claim": "Real navigation `SR` / `SPL` remains unsupported.",
            "status": "blocked",
            "evidence": "E007-M02 does not add simulator, navmesh, or trajectory execution.",
            "boundary": "Use only proxy path-cost terminology after E007-M03, and only if grid projection succeeds.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_summary_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    policy_lines = [
        "| Policy | Query Rows | Route Rows | Queries Route-Ready | Projection-Ready Rows | External Pending Rows | Status Counts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in policy_summary_rows:
        policy_lines.append(
            f"| `{row['policy']}` | {row['query_rows']} | {row['route_rows']} | "
            f"{row['queries_with_materialized_route']} | {row['candidate_grid_projection_ready_route_rows']} | "
            f"{row['external_projection_pending_route_rows']} | `{row['status_counts']}` |"
        )

    gap_lines = ["| Policy | Gap Type | Rows |", "| --- | --- | ---: |"]
    gap_counts = Counter((row["policy"], row["gap_type"]) for row in source_gap_rows)
    for (policy, gap_type), count in sorted(gap_counts.items()):
        gap_lines.append(f"| `{policy}` | `{gap_type}` | {count} |")
    if not gap_counts:
        gap_lines.append("| none | none | 0 |")

    claim_lines = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    return f"""# E007-M02 Path Source Compatibility

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- Query-policy rows: {coverage["query_policy_rows"]}.
- Route rows: {coverage["route_rows"]}.
- Queries with all six policies materialized at least once: {coverage["queries_all_policies_materialized"]} / {coverage["query_rows"]}.
- Candidate grid projection-ready route rows: {coverage["candidate_grid_projection_ready_route_rows"]}.
- External projection pending route rows: {coverage["external_projection_pending_route_rows"]}.
- Source gap rows: {coverage["source_gap_rows"]}.
- Selected next unit: {coverage["selected_next_unit"]}.
- Real navigation `SR` / `SPL` ready: false.

## Policy Summary

{chr(10).join(policy_lines)}

## Source Gaps

{chr(10).join(gap_lines)}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- The denominator can move forward to path-cost work, but external candidates must be projected onto the E002 grid first.
- M02 is enough to block a premature real navigation claim and to justify E007-M03 as a grid-projection/path-cost computation unit.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    m01 = read_json(E007_M01_DIR / "coverage.json")
    m100_rows = read_jsonl(E005_M100_DIR / "policy_rows.jsonl")
    m75_rows = read_jsonl(E005_M75_DIR / "policy_rows.jsonl")
    selected_rows = [
        row for row in m100_rows if row.get("policy") == "h001_then_conceptgraphs_top5_on_observed_miss_v0"
    ]
    grid_rows = read_jsonl(E002_GRID_DIR / "grid_query_rows.jsonl")
    conceptgraphs_rows = load_conceptgraphs_rows()
    detector_rows = load_real_detector_rows()

    if not selected_rows:
        raise RuntimeError("Missing M100 selected policy rows.")
    if not grid_rows:
        raise RuntimeError("Missing E002 grid query rows.")
    if not conceptgraphs_rows:
        raise RuntimeError("Missing ConceptGraphs candidate rows.")

    m100_by_policy_query = index_by_policy_query(m100_rows)
    m75_by_policy_query = index_by_policy_query(m75_rows)
    grid_by_row = {row["row_uid"]: row for row in grid_rows}

    conceptgraphs_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in conceptgraphs_rows:
        conceptgraphs_by_query[row["query_uid"]].append(row)
    for rows in conceptgraphs_by_query.values():
        rows.sort(key=lambda row: (int(row.get("rank") or 999999), row.get("candidate_uid") or ""))

    detector_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in detector_rows:
        detector_by_scan_label[(row.get("scan_id"), row.get("label_canonical"))].append(row)
    for rows in detector_by_scan_label.values():
        rows.sort(
            key=lambda row: (
                int(row.get("pre_cap_group_rank") or row.get("pre_cap_rank") or 999999),
                -float(row.get("selection_score") or row.get("confidence") or 0.0),
                row.get("proposal_uid") or "",
            )
        )

    route_rows = build_route_rows(
        selected_rows,
        m100_by_policy_query,
        m75_by_policy_query,
        grid_by_row,
        conceptgraphs_by_query,
        detector_by_scan_label,
    )
    query_materialization_rows = build_query_materialization_rows(
        selected_rows,
        route_rows,
        m100_by_policy_query,
        m75_by_policy_query,
        grid_by_row,
    )
    policy_summary_rows = build_policy_summary_rows(query_materialization_rows, route_rows)
    source_gap_rows = build_source_gap_rows(query_materialization_rows)
    policies_by_query: dict[str, set[str]] = defaultdict(set)
    for row in query_materialization_rows:
        if row["materialized_route_count"] > 0:
            policies_by_query[row["query_uid"]].add(row["policy"])

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m02_path_source_compatibility_ready_projection_pending",
        "version": VERSION,
        "m01_status": m01.get("status"),
        "query_rows": len(selected_rows),
        "query_policy_rows": len(query_materialization_rows),
        "route_rows": len(route_rows),
        "policies": POLICIES,
        "queries_all_policies_materialized": sum(1 for policies in policies_by_query.values() if set(POLICIES).issubset(policies)),
        "coordinate_ready_route_rows": sum(1 for row in route_rows if row.get("coordinate_ready")),
        "candidate_grid_projection_ready_route_rows": sum(1 for row in route_rows if row.get("candidate_grid_projection_ready")),
        "external_projection_pending_route_rows": sum(
            1 for row in route_rows if row.get("path_source_status") == "external_coordinate_ready_grid_projection_pending"
        ),
        "missing_coordinate_route_rows": sum(1 for row in route_rows if row.get("path_source_status") == "external_coordinate_missing"),
        "source_gap_rows": len(source_gap_rows),
        "path_cost_metric_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": "E007-M03 external candidate grid projection and path-cost route computation",
    }
    claim_rows = build_claim_rows(coverage)

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "policy_route_rows.jsonl", route_rows)
    write_jsonl(OUT_DIR / "query_materialization_rows.jsonl", query_materialization_rows)
    write_jsonl(OUT_DIR / "policy_summary_rows.jsonl", policy_summary_rows)
    write_jsonl(OUT_DIR / "source_gap_rows.jsonl", source_gap_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "policy_summary_rows": policy_summary_rows,
            "source_gap_rows": source_gap_rows,
            "claim_boundary_rows": claim_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, policy_summary_rows, source_gap_rows, claim_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
