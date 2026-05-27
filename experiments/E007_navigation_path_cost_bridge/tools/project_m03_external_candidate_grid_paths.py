#!/usr/bin/env python3
"""Project E007 route candidates onto the E002 occupancy-grid profile."""

from __future__ import annotations

import heapq
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
E002_TOOL_DIR = ROOT / "experiments" / "E002_path_cost_bridge" / "tools"
if str(E002_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(E002_TOOL_DIR))

from build_occupancy_grid_paths import (  # noqa: E402
    GRID_RESOLUTION_M,
    PROFILE_ID,
    ROBOT_RADIUS_M,
    astar_path_cost,
    build_grid,
    cell_payload,
    nearest_free_cell,
    round6,
)


EXP_ROOT = ROOT / "experiments" / "E007_navigation_path_cost_bridge"
OUT_DIR = EXP_ROOT / "artifacts" / "E007-M03_external_candidate_grid_projection_v0"
VERSION = "e007_m03_external_candidate_grid_projection_v0"
DATASET_ROOT = ROOT / "local_dataset"
E002_GRID_DIR = ROOT / "experiments" / "E002_path_cost_bridge" / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
E007_M02_DIR = EXP_ROOT / "artifacts" / "E007-M02_path_source_compatibility_v0"


Cell = tuple[int, int]
Point = list[float]


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


def point_key(point: Point) -> tuple[float, float, float]:
    return tuple(round(float(value), 6) for value in point)  # type: ignore[return-value]


def has_xyz(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(isinstance(item, (int, float)) for item in value)


def make_projection_cache() -> dict[tuple[str, tuple[float, float, float]], dict[str, Any]]:
    return {}


def project_point(
    grid: Any,
    point: Point,
    projection_cache: dict[tuple[str, tuple[float, float, float]], dict[str, Any]],
) -> dict[str, Any]:
    key = (grid.scan_id, point_key(point))
    if key not in projection_cache:
        projection_cache[key] = nearest_free_cell(grid, point)
    return projection_cache[key]


def path_cost(
    grid: Any,
    start_cell: Cell,
    goal_cell: Cell,
    route_cache: dict[tuple[str, Cell, Cell], float | None],
) -> float | None:
    key = (grid.scan_id, start_cell, goal_cell)
    if key not in route_cache:
        route_cache[key] = astar_path_cost(grid, start_cell, goal_cell)
    return route_cache[key]


def group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def build_scan_points(
    grid_query_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> dict[str, list[Point]]:
    grid_by_row = {row["row_uid"]: row for row in grid_query_rows}
    points: dict[str, list[Point]] = defaultdict(list)
    for row in grid_query_rows:
        scan_id = row["rescan_id"]
        for field in ["path_start_centroid", "old_scene_aligned_centroid", "current_target_centroid"]:
            value = row.get(field)
            if has_xyz(value):
                points[scan_id].append(value)
    for row in route_rows:
        grid_row = grid_by_row.get(row["row_uid"])
        xyz = row.get("candidate_xyz")
        if grid_row and has_xyz(xyz):
            points[grid_row["rescan_id"]].append(xyz)
    return points


def build_grids(scan_points: dict[str, list[Point]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    grids: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    for scan_id, points in sorted(scan_points.items()):
        grid, summary = build_grid(DATASET_ROOT, scan_id, points)
        summary = {
            **summary,
            "grid_profile_id": PROFILE_ID,
            "grid_rebuilt_for_e007_external_candidates": True,
            "query_point_count": len(points),
        }
        summaries.append(summary)
        if grid is not None:
            grids[scan_id] = grid
    return grids, summaries


def enrich_route_rows(
    route_rows: list[dict[str, Any]],
    grid_query_rows: list[dict[str, Any]],
    grids: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grid_by_row = {row["row_uid"]: row for row in grid_query_rows}
    rows_by_query_policy = group_rows(route_rows, "query_uid")
    projection_cache = make_projection_cache()
    route_cache: dict[tuple[str, Cell, Cell], float | None] = {}
    projected_rows: list[dict[str, Any]] = []
    source_limited_rows: list[dict[str, Any]] = []

    for query_uid, group in sorted(rows_by_query_policy.items()):
        by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            by_policy[row["policy"]].append(row)
        for policy, policy_rows in by_policy.items():
            ordered = sorted(policy_rows, key=lambda row: int(row["route_index"]))
            grid_row = grid_by_row.get(ordered[0]["row_uid"])
            if not grid_row:
                for route in ordered:
                    out = {
                        **route,
                        "m03_version": VERSION,
                        "grid_profile_id": PROFILE_ID,
                        "path_source_status": "query_grid_row_missing",
                        "candidate_grid_projection_ready": False,
                        "candidate_grid_path_ready": False,
                        "candidate_path_step_cost_m": None,
                        "candidate_path_cumulative_cost_m": None,
                    }
                    projected_rows.append(out)
                    source_limited_rows.append(source_limited_payload(out, "query_grid_row_missing"))
                continue

            scan_id = grid_row["rescan_id"]
            grid = grids.get(scan_id)
            if grid is None:
                for route in ordered:
                    out = {
                        **route,
                        "m03_version": VERSION,
                        "grid_profile_id": PROFILE_ID,
                        "scan_id": scan_id,
                        "path_source_status": "scan_grid_not_ready",
                        "candidate_grid_projection_ready": False,
                        "candidate_grid_path_ready": False,
                        "candidate_path_step_cost_m": None,
                        "candidate_path_cumulative_cost_m": None,
                    }
                    projected_rows.append(out)
                    source_limited_rows.append(source_limited_payload(out, "scan_grid_not_ready"))
                continue

            start_point = grid_row.get("path_start_centroid")
            if not has_xyz(start_point):
                start_projection = {"cell": None, "projection_distance_m": None, "status": "start_point_missing"}
            else:
                start_projection = project_point(grid, start_point, projection_cache)
            previous_cell = start_projection.get("cell")
            cumulative_cost = 0.0

            for route in ordered:
                candidate_xyz = route.get("candidate_xyz")
                if not has_xyz(candidate_xyz):
                    projection = {"cell": None, "projection_distance_m": None, "status": "candidate_coordinate_missing"}
                else:
                    projection = project_point(grid, candidate_xyz, projection_cache)

                goal_cell = projection.get("cell")
                step_cost = None
                ready = False
                if previous_cell is None:
                    status = "start_unprojectable"
                elif goal_cell is None:
                    status = "candidate_unprojectable"
                else:
                    from_cell = previous_cell
                    step_cost = path_cost(grid, from_cell, goal_cell, route_cache)
                    if step_cost is None:
                        status = "disconnected_free_space"
                    else:
                        ready = True
                        status = "path_ready"
                        cumulative_cost += step_cost
                        previous_cell = goal_cell

                out = {
                    **route,
                    "m03_version": VERSION,
                    "grid_profile_id": PROFILE_ID,
                    "grid_path_cost_source": "ply_floor_obstacle_occupancy_astar_rebuilt_for_e007",
                    "scan_id": scan_id,
                    "grid_resolution_m": GRID_RESOLUTION_M,
                    "robot_radius_m": ROBOT_RADIUS_M,
                    "start_grid_cell": cell_payload(start_projection),
                    "start_projection_status": start_projection.get("status"),
                    "start_nearest_free_cell_distance_m": round6(start_projection.get("projection_distance_m")),
                    "candidate_goal_grid_cell": cell_payload(projection),
                    "candidate_projection_status": projection.get("status"),
                    "candidate_nearest_free_cell_distance_m": round6(projection.get("projection_distance_m")),
                    "candidate_grid_projection_ready": goal_cell is not None,
                    "candidate_grid_path_ready": ready,
                    "path_source_status": status,
                    "candidate_step_from_grid_cell": cell_payload({"cell": from_cell}) if ready else None,
                    "candidate_step_to_grid_cell": cell_payload(projection),
                    "candidate_path_step_cost_m": round6(step_cost),
                    "candidate_path_cumulative_cost_m": round6(cumulative_cost) if ready else None,
                    "path_cost_metric_ready": ready,
                    "real_navigation_path_cost_ready": False,
                }
                projected_rows.append(out)
                if not ready:
                    source_limited_rows.append(source_limited_payload(out, status))
    return projected_rows, source_limited_rows


def source_limited_payload(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "route_uid": row.get("route_uid"),
        "policy": row.get("policy"),
        "query_uid": row.get("query_uid"),
        "row_uid": row.get("row_uid"),
        "candidate_source": row.get("candidate_source"),
        "candidate_uid": row.get("candidate_uid"),
        "route_index": row.get("route_index"),
        "reason": reason,
        "row_band": row.get("row_band"),
        "task_context_id": row.get("task_context_id"),
        "scan_id": row.get("scan_id"),
    }


def compute_target_rows(
    grid_query_rows: list[dict[str, Any]],
    selected_query_rows: list[dict[str, Any]],
    grids: dict[str, Any],
) -> list[dict[str, Any]]:
    selected_row_uids = {row["row_uid"] for row in selected_query_rows}
    projection_cache = make_projection_cache()
    route_cache: dict[tuple[str, Cell, Cell], float | None] = {}
    rows: list[dict[str, Any]] = []
    for query in grid_query_rows:
        if query["row_uid"] not in selected_row_uids:
            continue
        scan_id = query["rescan_id"]
        grid = grids.get(scan_id)
        if grid is None:
            rows.append(
                {
                    "row_uid": query["row_uid"],
                    "scan_id": scan_id,
                    "target_path_status": "scan_grid_not_ready",
                    "target_path_cost_m": None,
                    "target_grid_projection_ready": False,
                    "target_grid_path_ready": False,
                }
            )
            continue
        start = project_point(grid, query["path_start_centroid"], projection_cache)
        target = project_point(grid, query["current_target_centroid"], projection_cache)
        start_cell = start.get("cell")
        target_cell = target.get("cell")
        if start_cell is None:
            status = "start_unprojectable"
            cost = None
        elif target_cell is None:
            status = "target_unprojectable"
            cost = None
        else:
            cost = path_cost(grid, start_cell, target_cell, route_cache)
            status = "target_path_ready" if cost is not None else "target_disconnected_free_space"
        rows.append(
            {
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "scan_id": scan_id,
                "target_path_status": status,
                "target_path_cost_m": round6(cost),
                "start_grid_cell": cell_payload(start),
                "target_goal_grid_cell": cell_payload(target),
                "start_projection_status": start.get("status"),
                "target_projection_status": target.get("status"),
                "start_nearest_free_cell_distance_m": round6(start.get("projection_distance_m")),
                "target_nearest_free_cell_distance_m": round6(target.get("projection_distance_m")),
                "target_grid_projection_ready": target_cell is not None,
                "target_grid_path_ready": cost is not None,
                "row_band": query.get("row_band"),
                "task_context_id": query.get("task_context_id"),
            }
        )
    return rows


def build_query_path_rows(
    projected_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    query_materialization_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_by_row = {row["row_uid"]: row for row in target_rows}
    by_query_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in projected_rows:
        by_query_policy[(row["query_uid"], row["policy"])].append(row)
    materialization_by_query_policy = {
        (row["query_uid"], row["policy"]): row for row in query_materialization_rows
    }

    query_rows: list[dict[str, Any]] = []
    for (query_uid, policy), materialized in sorted(materialization_by_query_policy.items()):
        rows = by_query_policy.get((query_uid, policy), [])
        target = target_by_row.get(materialized["row_uid"], {})
        if not rows:
            query_rows.append(
                {
                    "query_uid": query_uid,
                    "policy": policy,
                    "row_uid": materialized["row_uid"],
                    "base_row_uid": materialized.get("base_row_uid"),
                    "route_rows": 0,
                    "candidate_grid_projection_ready_rows": 0,
                    "candidate_grid_path_ready_rows": 0,
                    "all_route_rows_path_ready": False,
                    "has_source_limited_route": True,
                    "source_limited_reason": "no_candidate_route",
                    "target_grid_path_ready": bool(target.get("target_grid_path_ready")),
                    "target_path_cost_m": target.get("target_path_cost_m"),
                    "route_cumulative_cost_m": None,
                    "path_cost_policy_eval_ready": False,
                    "query_bridge_success_eval_only": materialized.get("query_bridge_success_eval_only"),
                    "expected_search_cost_eval_only": materialized.get("expected_search_cost_eval_only"),
                    "returned_location_count_eval_only": materialized.get("returned_location_count_eval_only"),
                    "success_source_eval_only": materialized.get("success_source_eval_only"),
                    "fallback_used_eval_only": materialized.get("fallback_used_eval_only"),
                    "route_materialization_status": materialized.get("route_materialization_status"),
                    "intended_route_count": materialized.get("intended_route_count"),
                    "materialized_route_count": materialized.get("materialized_route_count"),
                    "row_band": materialized.get("row_band"),
                    "task_context_id": materialized.get("task_context_id"),
                }
            )
            continue
        ordered = sorted(rows, key=lambda row: int(row["route_index"]))
        route_count = len(ordered)
        ready_count = sum(1 for row in ordered if row.get("candidate_grid_path_ready"))
        projection_count = sum(1 for row in ordered if row.get("candidate_grid_projection_ready"))
        final_costs = [
            row.get("candidate_path_cumulative_cost_m")
            for row in ordered
            if row.get("candidate_path_cumulative_cost_m") is not None
        ]
        query_rows.append(
            {
                "query_uid": query_uid,
                "policy": policy,
                "row_uid": ordered[0]["row_uid"],
                "base_row_uid": ordered[0].get("base_row_uid"),
                "route_rows": route_count,
                "candidate_grid_projection_ready_rows": projection_count,
                "candidate_grid_path_ready_rows": ready_count,
                "all_route_rows_path_ready": ready_count == route_count,
                "has_source_limited_route": ready_count != route_count,
                "target_grid_path_ready": bool(target.get("target_grid_path_ready")),
                "target_path_cost_m": target.get("target_path_cost_m"),
                "route_cumulative_cost_m": final_costs[-1] if final_costs else None,
                "path_cost_policy_eval_ready": ready_count == route_count and bool(target.get("target_grid_path_ready")),
                "query_bridge_success_eval_only": materialized.get("query_bridge_success_eval_only"),
                "expected_search_cost_eval_only": materialized.get("expected_search_cost_eval_only"),
                "returned_location_count_eval_only": materialized.get("returned_location_count_eval_only"),
                "success_source_eval_only": materialized.get("success_source_eval_only"),
                "fallback_used_eval_only": materialized.get("fallback_used_eval_only"),
                "route_materialization_status": materialized.get("route_materialization_status"),
                "intended_route_count": materialized.get("intended_route_count"),
                "materialized_route_count": materialized.get("materialized_route_count"),
                "row_band": ordered[0].get("row_band"),
                "task_context_id": ordered[0].get("task_context_id"),
            }
        )
    return query_rows


def build_policy_summary_rows(query_rows: list[dict[str, Any]], projected_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    route_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        query_by_policy[row["policy"]].append(row)
    for row in projected_rows:
        route_by_policy[row["policy"]].append(row)

    rows: list[dict[str, Any]] = []
    for policy in sorted(query_by_policy):
        qrows = query_by_policy[policy]
        rrows = route_by_policy[policy]
        rows.append(
            {
                "policy": policy,
                "query_policy_rows": len(qrows),
                "route_rows": len(rrows),
                "route_projection_ready_rows": sum(1 for row in rrows if row.get("candidate_grid_projection_ready")),
                "route_path_ready_rows": sum(1 for row in rrows if row.get("candidate_grid_path_ready")),
                "query_policy_all_route_path_ready_rows": sum(1 for row in qrows if row.get("all_route_rows_path_ready")),
                "query_policy_eval_ready_rows": sum(1 for row in qrows if row.get("path_cost_policy_eval_ready")),
                "source_limited_query_policy_rows": sum(1 for row in qrows if row.get("has_source_limited_route")),
                "no_route_query_policy_rows": sum(1 for row in qrows if row.get("route_rows") == 0),
                "target_path_ready_rows": sum(1 for row in qrows if row.get("target_grid_path_ready")),
                "path_status_counts": dict(Counter(row.get("path_source_status") for row in rrows)),
            }
        )
    return rows


def build_claim_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C-E007-M03-001",
            "claim": "External candidate coordinates can be projected onto the E002 occupancy-grid profile for most route rows.",
            "status": "projection_supported_with_source_limits",
            "evidence": (
                f"{coverage['route_projection_ready_rows']} / {coverage['route_rows']} route rows have projected grid cells; "
                f"{coverage['route_path_ready_rows']} / {coverage['route_rows']} have step path costs."
            ),
            "boundary": "This is still a proxy path source, not real navigation.",
        },
        {
            "claim_id": "C-E007-M03-002",
            "claim": "Path-cost policy evaluation can proceed on the source-ready subset with explicit source-limited accounting.",
            "status": "ready_for_e007_m04",
            "evidence": (
                f"{coverage['query_policy_eval_ready_rows']} / {coverage['query_policy_rows']} query-policy rows are path-cost eval ready; "
                f"{coverage['source_limited_query_policy_rows']} query-policy rows are source-limited."
            ),
            "boundary": "Do not hide source-limited rows; report full denominator and source-ready subset separately.",
        },
        {
            "claim_id": "C-E007-M03-003",
            "claim": "Real navigation `SR` / `SPL` remains unsupported.",
            "status": "blocked",
            "evidence": "No simulator, navmesh, controller, or trajectory execution is integrated.",
            "boundary": "Use `PathAttemptSPLProxy` only after E007-M04 and keep real `SPL` false.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_summary_rows: list[dict[str, Any]],
    scan_summaries: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    policy_lines = [
        "| Policy | Query Rows | Eval Ready | No Route | Route Rows | Path Ready | Source-Limited Queries | Status Counts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in policy_summary_rows:
        policy_lines.append(
            f"| `{row['policy']}` | {row['query_policy_rows']} | {row['query_policy_eval_ready_rows']} | "
            f"{row['no_route_query_policy_rows']} | "
            f"{row['route_rows']} | {row['route_path_ready_rows']} | {row['source_limited_query_policy_rows']} | "
            f"`{row['path_status_counts']}` |"
        )

    scan_lines = ["| Scan | Status | Free Cells | Query Points |", "| --- | --- | ---: | ---: |"]
    for row in scan_summaries:
        scan_lines.append(
            f"| `{row['scan_id']}` | `{row['status']}` | {row.get('free_cell_count', 0)} | {row.get('query_point_count', 0)} |"
        )

    claim_lines = ["| Claim | Status | Boundary |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['boundary']} |")

    return f"""# E007-M03 External Candidate Grid Projection

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- Query-policy rows: {coverage["query_policy_rows"]}.
- Route rows: {coverage["route_rows"]}.
- Route projection-ready rows: {coverage["route_projection_ready_rows"]}.
- Route path-ready rows: {coverage["route_path_ready_rows"]}.
- Query-policy eval-ready rows: {coverage["query_policy_eval_ready_rows"]}.
- Source-limited query-policy rows: {coverage["source_limited_query_policy_rows"]}.
- No-route query-policy rows: {coverage["no_route_query_policy_rows"]}.
- Source-limited route rows: {coverage["source_limited_route_rows"]}.
- Selected next unit: {coverage["selected_next_unit"]}.
- Real navigation `SR` / `SPL` ready: false.

## Policy Summary

{chr(10).join(policy_lines)}

## Scan Grids

{chr(10).join(scan_lines)}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- E007 can now move from route materialization to path-cost policy evaluation, but only with explicit source-limited accounting.
- The paper-facing table should report both the full 195-row denominator and the source-ready subset.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    m02 = read_json(E007_M02_DIR / "coverage.json")
    route_rows = read_jsonl(E007_M02_DIR / "policy_route_rows.jsonl")
    query_materialization_rows = read_jsonl(E007_M02_DIR / "query_materialization_rows.jsonl")
    grid_query_rows = read_jsonl(E002_GRID_DIR / "grid_query_rows.jsonl")
    if not route_rows:
        raise RuntimeError("Missing E007-M02 route rows.")
    if not grid_query_rows:
        raise RuntimeError("Missing E002 grid query rows.")

    selected_queries = [
        row
        for row in query_materialization_rows
        if row.get("policy") == "h001_then_conceptgraphs_top5_on_observed_miss_v0"
    ]
    scan_points = build_scan_points(grid_query_rows, route_rows)
    grids, scan_summaries = build_grids(scan_points)
    projected_rows, source_limited_rows = enrich_route_rows(route_rows, grid_query_rows, grids)
    target_rows = compute_target_rows(grid_query_rows, selected_queries, grids)
    query_path_rows = build_query_path_rows(projected_rows, target_rows, query_materialization_rows)
    policy_summary_rows = build_policy_summary_rows(query_path_rows, projected_rows)

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e007_m03_external_candidate_grid_projection_ready",
        "version": VERSION,
        "m02_status": m02.get("status"),
        "grid_profile_id": PROFILE_ID,
        "grid_rebuilt_for_e007_external_candidates": True,
        "query_rows": len({row["row_uid"] for row in selected_queries}),
        "query_policy_rows": len(query_path_rows),
        "route_rows": len(projected_rows),
        "route_projection_ready_rows": sum(1 for row in projected_rows if row.get("candidate_grid_projection_ready")),
        "route_path_ready_rows": sum(1 for row in projected_rows if row.get("candidate_grid_path_ready")),
        "source_limited_route_rows": len(source_limited_rows),
        "source_limited_query_policy_rows": sum(1 for row in query_path_rows if row.get("has_source_limited_route")),
        "no_route_query_policy_rows": sum(1 for row in query_path_rows if row.get("route_rows") == 0),
        "target_path_ready_rows": sum(1 for row in target_rows if row.get("target_grid_path_ready")),
        "query_policy_all_route_path_ready_rows": sum(1 for row in query_path_rows if row.get("all_route_rows_path_ready")),
        "query_policy_eval_ready_rows": sum(1 for row in query_path_rows if row.get("path_cost_policy_eval_ready")),
        "path_cost_route_fields_ready": True,
        "path_cost_policy_metric_ready": False,
        "real_navigation_sr_spl_ready": False,
        "scan_count": len(scan_summaries),
        "scan_grid_ready_count": sum(1 for row in scan_summaries if row.get("status") == "ready"),
        "path_status_counts": dict(Counter(row.get("path_source_status") for row in projected_rows)),
        "selected_next_unit": "E007-M04 path-cost policy metric evaluation with source-limited accounting",
    }
    claim_rows = build_claim_rows(coverage)

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "projected_route_rows.jsonl", projected_rows)
    write_jsonl(OUT_DIR / "query_path_readiness_rows.jsonl", query_path_rows)
    write_jsonl(OUT_DIR / "target_path_rows.jsonl", target_rows)
    write_jsonl(OUT_DIR / "policy_path_summary_rows.jsonl", policy_summary_rows)
    write_jsonl(OUT_DIR / "source_limited_route_rows.jsonl", source_limited_rows)
    write_jsonl(OUT_DIR / "scan_grid_summaries.jsonl", scan_summaries)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "policy_path_summary_rows": policy_summary_rows,
            "claim_boundary_rows": claim_rows,
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, policy_summary_rows, scan_summaries, claim_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
