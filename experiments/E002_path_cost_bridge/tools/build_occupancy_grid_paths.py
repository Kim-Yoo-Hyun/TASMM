#!/usr/bin/env python3
"""Attach occupancy-grid A* path costs to E002 rows."""

from __future__ import annotations

import argparse
import heapq
import json
import math
from collections import Counter, deque
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M01_path_cost_inputs_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
PROFILE_ID = "occupancy_grid_astar_v0"
GRID_RESOLUTION_M = 0.10
ROBOT_RADIUS_M = 0.18
FLOOR_DILATION_M = 0.12
OBSTACLE_MIN_HEIGHT_M = 0.08
OBSTACLE_MAX_HEIGHT_M = 1.60
MAX_PROJECTION_RADIUS_M = 1.25
BOUNDS_MARGIN_M = 0.50
FLOOR_LABEL_TOKENS = {"floor", "carpet", "rug"}
CEILING_LABEL_TOKENS = {"ceiling"}


Cell = tuple[int, int]
Point = list[float]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("median requires non-empty list")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def label_has_token(label: str, tokens: set[str]) -> bool:
    lower = label.lower()
    return any(token in lower for token in tokens)


def load_label_map(semseg_path: Path) -> dict[int, str]:
    data = load_json(semseg_path)
    labels: dict[int, str] = {}
    for group in data.get("segGroups", []):
        object_id = group.get("objectId", group.get("id"))
        if object_id is None:
            continue
        labels[int(object_id)] = str(group.get("label", ""))
    return labels


def parse_ascii_ply_vertices(path: Path) -> list[tuple[float, float, float, int]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        header: list[str] = []
        vertex_properties: list[str] = []
        vertex_count: int | None = None
        in_vertex = False
        for line in f:
            text = line.strip()
            header.append(text)
            if text == "format ascii 1.0":
                continue
            if text.startswith("element vertex "):
                vertex_count = int(text.split()[-1])
                in_vertex = True
                continue
            if text.startswith("element ") and not text.startswith("element vertex "):
                in_vertex = False
            if in_vertex and text.startswith("property "):
                vertex_properties.append(text.split()[-1])
            if text == "end_header":
                break

        if vertex_count is None:
            raise RuntimeError(f"missing vertex count in {path}")
        required = ["x", "y", "z", "objectId"]
        missing = [name for name in required if name not in vertex_properties]
        if missing:
            raise RuntimeError(f"missing PLY properties {missing} in {path}")

        x_idx = vertex_properties.index("x")
        y_idx = vertex_properties.index("y")
        z_idx = vertex_properties.index("z")
        object_idx = vertex_properties.index("objectId")

        vertices = []
        for _ in range(vertex_count):
            parts = f.readline().strip().split()
            if not parts:
                continue
            vertices.append(
                (
                    float(parts[x_idx]),
                    float(parts[y_idx]),
                    float(parts[z_idx]),
                    int(parts[object_idx]),
                )
            )
    return vertices


class OccupancyGrid:
    def __init__(
        self,
        scan_id: str,
        free_cells: set[Cell],
        min_x: float,
        min_y: float,
        width: int,
        height: int,
        floor_z: float,
        source_summary: dict[str, Any],
    ) -> None:
        self.scan_id = scan_id
        self.free_cells = free_cells
        self.min_x = min_x
        self.min_y = min_y
        self.width = width
        self.height = height
        self.floor_z = floor_z
        self.source_summary = source_summary

    def to_cell(self, point: Point) -> Cell:
        return (
            int(math.floor((float(point[0]) - self.min_x) / GRID_RESOLUTION_M)),
            int(math.floor((float(point[1]) - self.min_y) / GRID_RESOLUTION_M)),
        )

    def cell_center(self, cell: Cell) -> tuple[float, float]:
        return (
            self.min_x + (cell[0] + 0.5) * GRID_RESOLUTION_M,
            self.min_y + (cell[1] + 0.5) * GRID_RESOLUTION_M,
        )

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height


def disk_offsets(radius_cells: int) -> list[Cell]:
    offsets = []
    radius_sq = radius_cells * radius_cells
    for dx in range(-radius_cells, radius_cells + 1):
        for dy in range(-radius_cells, radius_cells + 1):
            if dx * dx + dy * dy <= radius_sq:
                offsets.append((dx, dy))
    return offsets


def dilate(cells: set[Cell], radius_cells: int, width: int, height: int) -> set[Cell]:
    if radius_cells <= 0:
        return set(cells)
    offsets = disk_offsets(radius_cells)
    output: set[Cell] = set()
    for cell in cells:
        for dx, dy in offsets:
            out = (cell[0] + dx, cell[1] + dy)
            if 0 <= out[0] < width and 0 <= out[1] < height:
                output.add(out)
    return output


def build_grid(dataset_root: Path, scan_id: str, query_points: list[Point]) -> tuple[OccupancyGrid | None, dict[str, Any]]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    ply_path = scan_dir / "labels.instances.annotated.v2.ply"
    semseg_path = scan_dir / "semseg.v2.json"
    if not ply_path.is_file() or not semseg_path.is_file():
        return None, {
            "scan_id": scan_id,
            "status": "missing_payload",
            "ply_path": str(ply_path),
            "semseg_path": str(semseg_path),
        }

    labels = load_label_map(semseg_path)
    floor_ids = {object_id for object_id, label in labels.items() if label_has_token(label, FLOOR_LABEL_TOKENS)}
    ceiling_ids = {object_id for object_id, label in labels.items() if label_has_token(label, CEILING_LABEL_TOKENS)}
    vertices = parse_ascii_ply_vertices(ply_path)
    floor_points = [(x, y, z) for x, y, z, object_id in vertices if object_id in floor_ids]
    if not floor_points:
        return None, {
            "scan_id": scan_id,
            "status": "no_floor_points",
            "vertex_count": len(vertices),
            "floor_object_ids": sorted(floor_ids),
        }

    floor_z = median([point[2] for point in floor_points])
    all_x = [point[0] for point in floor_points]
    all_y = [point[1] for point in floor_points]
    for point in query_points:
        all_x.append(float(point[0]))
        all_y.append(float(point[1]))
    min_x = min(all_x) - BOUNDS_MARGIN_M
    max_x = max(all_x) + BOUNDS_MARGIN_M
    min_y = min(all_y) - BOUNDS_MARGIN_M
    max_y = max(all_y) + BOUNDS_MARGIN_M
    width = max(1, int(math.ceil((max_x - min_x) / GRID_RESOLUTION_M)) + 1)
    height = max(1, int(math.ceil((max_y - min_y) / GRID_RESOLUTION_M)) + 1)

    def to_cell_xy(x: float, y: float) -> Cell:
        return (
            int(math.floor((x - min_x) / GRID_RESOLUTION_M)),
            int(math.floor((y - min_y) / GRID_RESOLUTION_M)),
        )

    floor_cells = {
        to_cell_xy(x, y)
        for x, y, _ in floor_points
    }
    floor_cells = {cell for cell in floor_cells if 0 <= cell[0] < width and 0 <= cell[1] < height}
    free_cells = dilate(
        floor_cells,
        int(math.ceil(FLOOR_DILATION_M / GRID_RESOLUTION_M)),
        width,
        height,
    )

    obstacle_cells: set[Cell] = set()
    min_obstacle_z = floor_z + OBSTACLE_MIN_HEIGHT_M
    max_obstacle_z = floor_z + OBSTACLE_MAX_HEIGHT_M
    for x, y, z, object_id in vertices:
        if object_id in floor_ids or object_id in ceiling_ids:
            continue
        if z < min_obstacle_z or z > max_obstacle_z:
            continue
        cell = to_cell_xy(x, y)
        if 0 <= cell[0] < width and 0 <= cell[1] < height:
            obstacle_cells.add(cell)

    inflated_obstacles = dilate(
        obstacle_cells,
        int(math.ceil(ROBOT_RADIUS_M / GRID_RESOLUTION_M)),
        width,
        height,
    )
    free_cells = free_cells - inflated_obstacles
    summary = {
        "scan_id": scan_id,
        "status": "ready" if free_cells else "no_free_cells",
        "ply_path": str(ply_path),
        "semseg_path": str(semseg_path),
        "vertex_count": len(vertices),
        "floor_object_ids": sorted(floor_ids),
        "ceiling_object_ids": sorted(ceiling_ids),
        "floor_point_count": len(floor_points),
        "floor_z_median": round6(floor_z),
        "grid_resolution_m": GRID_RESOLUTION_M,
        "robot_radius_m": ROBOT_RADIUS_M,
        "grid_width": width,
        "grid_height": height,
        "floor_cell_count": len(floor_cells),
        "free_cell_count": len(free_cells),
        "obstacle_cell_count": len(obstacle_cells),
        "inflated_obstacle_cell_count": len(inflated_obstacles),
    }
    if not free_cells:
        return None, summary
    return OccupancyGrid(scan_id, free_cells, min_x, min_y, width, height, floor_z, summary), summary


def nearest_free_cell(grid: OccupancyGrid, point: Point) -> dict[str, Any]:
    source = grid.to_cell(point)
    if source in grid.free_cells:
        center = grid.cell_center(source)
        return {
            "cell": source,
            "projection_distance_m": math.dist([float(point[0]), float(point[1])], [center[0], center[1]]),
            "status": "already_free",
        }

    max_radius = int(math.ceil(MAX_PROJECTION_RADIUS_M / GRID_RESOLUTION_M))
    visited = {source}
    queue: deque[tuple[Cell, int]] = deque([(source, 0)])
    best: tuple[float, Cell] | None = None
    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    while queue:
        cell, depth = queue.popleft()
        if depth > max_radius:
            continue
        if cell in grid.free_cells:
            center = grid.cell_center(cell)
            dist = math.dist([float(point[0]), float(point[1])], [center[0], center[1]])
            if best is None or dist < best[0]:
                best = (dist, cell)
        if depth == max_radius:
            continue
        for dx, dy in neighbors:
            next_cell = (cell[0] + dx, cell[1] + dy)
            if next_cell in visited:
                continue
            visited.add(next_cell)
            if grid.in_bounds(next_cell):
                queue.append((next_cell, depth + 1))

    if best is None:
        return {
            "cell": None,
            "projection_distance_m": None,
            "status": "no_free_cell_within_radius",
        }
    return {
        "cell": best[1],
        "projection_distance_m": best[0],
        "status": "projected_to_nearest_free",
    }


def astar_path_cost(grid: OccupancyGrid, start: Cell, goal: Cell) -> float | None:
    if start not in grid.free_cells or goal not in grid.free_cells:
        return None
    if start == goal:
        return 0.0
    neighbor_steps = [
        (1, 0, GRID_RESOLUTION_M),
        (-1, 0, GRID_RESOLUTION_M),
        (0, 1, GRID_RESOLUTION_M),
        (0, -1, GRID_RESOLUTION_M),
        (1, 1, GRID_RESOLUTION_M * math.sqrt(2.0)),
        (1, -1, GRID_RESOLUTION_M * math.sqrt(2.0)),
        (-1, 1, GRID_RESOLUTION_M * math.sqrt(2.0)),
        (-1, -1, GRID_RESOLUTION_M * math.sqrt(2.0)),
    ]

    def heuristic(cell: Cell) -> float:
        return GRID_RESOLUTION_M * math.hypot(cell[0] - goal[0], cell[1] - goal[1])

    queue: list[tuple[float, float, Cell]] = [(heuristic(start), 0.0, start)]
    best_cost: dict[Cell, float] = {start: 0.0}
    while queue:
        _, cost, cell = heapq.heappop(queue)
        if cell == goal:
            return cost
        if cost > best_cost.get(cell, float("inf")):
            continue
        for dx, dy, step_cost in neighbor_steps:
            next_cell = (cell[0] + dx, cell[1] + dy)
            if next_cell not in grid.free_cells:
                continue
            next_cost = cost + step_cost
            if next_cost >= best_cost.get(next_cell, float("inf")):
                continue
            best_cost[next_cell] = next_cost
            heapq.heappush(queue, (next_cost + heuristic(next_cell), next_cost, next_cell))
    return None


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def cell_payload(result: dict[str, Any]) -> dict[str, Any]:
    cell = result.get("cell")
    return [cell[0], cell[1]] if cell is not None else None


def build_rows(
    dataset_root: Path,
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_uid = group_by_uid(candidate_rows)
    scan_points: dict[str, list[Point]] = {}
    for row in query_rows:
        scan_points.setdefault(row["rescan_id"], []).append(row["path_start_centroid"])
        scan_points[row["rescan_id"]].append(row["current_target_centroid"])
    for row in candidate_rows:
        scan_points.setdefault(row["rescan_id"], []).append(row["candidate_centroid"])

    grids: dict[str, OccupancyGrid] = {}
    scan_summaries: list[dict[str, Any]] = []
    for scan_id, points in sorted(scan_points.items()):
        grid, summary = build_grid(dataset_root, scan_id, points)
        scan_summaries.append(summary)
        if grid is not None:
            grids[scan_id] = grid

    route_cache: dict[tuple[str, Cell, Cell], float | None] = {}
    projection_cache: dict[tuple[str, tuple[float, float, float]], dict[str, Any]] = {}

    def project(grid: OccupancyGrid, point: Point) -> dict[str, Any]:
        key = (grid.scan_id, tuple(round(float(value), 6) for value in point))
        if key not in projection_cache:
            projection_cache[key] = nearest_free_cell(grid, point)
        return projection_cache[key]

    def path_cost(grid: OccupancyGrid, start_cell: Cell, goal_cell: Cell) -> float | None:
        key = (grid.scan_id, start_cell, goal_cell)
        if key not in route_cache:
            route_cache[key] = astar_path_cost(grid, start_cell, goal_cell)
        return route_cache[key]

    out_queries: list[dict[str, Any]] = []
    out_candidates: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for query in query_rows:
        grid = grids.get(query["rescan_id"])
        query_candidates = candidates_by_uid.get(query["row_uid"], [])
        if grid is None:
            reason = "scan_grid_not_ready"
            out_queries.append(
                {
                    **query,
                    "grid_path_cost_profile_id": PROFILE_ID,
                    "grid_path_cost_source": "ply_floor_obstacle_occupancy_astar",
                    "grid_path_cost_ready": False,
                    "free_space_path_cost_ready": False,
                    "real_navigation_path_cost_ready": False,
                    "grid_failure_type": reason,
                    "target_grid_path_cost_m": None,
                    "target_grid_reachable": False,
                }
            )
            for candidate in query_candidates:
                out = {
                    **candidate,
                    "grid_path_cost_profile_id": PROFILE_ID,
                    "candidate_grid_path_cost_m": None,
                    "candidate_grid_reachable": False,
                    "candidate_grid_failure_type": reason,
                    "candidate_grid_visit_order_index": None,
                    "candidate_nearest_free_cell_distance_m": None,
                }
                out_candidates.append(out)
                failure_rows.append(failure_row(query, candidate, reason, None))
            continue

        start_projection = project(grid, query["path_start_centroid"])
        start_cell = start_projection.get("cell")
        start_ready = start_cell is not None
        enriched_candidates = []
        for candidate in query_candidates:
            candidate_projection = project(grid, candidate["candidate_centroid"])
            goal_cell = candidate_projection.get("cell")
            reason = None
            cost = None
            reachable = False
            if not start_ready:
                reason = "start_unprojectable"
            elif goal_cell is None:
                reason = "candidate_unprojectable"
            else:
                cost = path_cost(grid, start_cell, goal_cell)
                if cost is None:
                    reason = "disconnected_free_space"
                else:
                    reachable = True

            enriched = {
                **candidate,
                "grid_path_cost_profile_id": PROFILE_ID,
                "grid_path_cost_source": "ply_floor_obstacle_occupancy_astar",
                "candidate_grid_path_cost_m": round6(cost),
                "candidate_grid_reachable": reachable,
                "candidate_grid_failure_type": reason,
                "candidate_start_grid_cell": cell_payload(start_projection),
                "candidate_goal_grid_cell": cell_payload(candidate_projection),
                "start_nearest_free_cell_distance_m": round6(start_projection.get("projection_distance_m")),
                "candidate_nearest_free_cell_distance_m": round6(candidate_projection.get("projection_distance_m")),
                "start_projection_status": start_projection.get("status"),
                "candidate_projection_status": candidate_projection.get("status"),
                "candidate_grid_visit_order_index": None,
                "candidate_grid_path_cost_ready": reachable,
                "real_navigation_path_cost_ready": False,
            }
            enriched_candidates.append(enriched)
            if not reachable:
                failure_rows.append(failure_row(query, candidate, reason or "unknown_grid_failure", candidate_projection))

        reachable_candidates = sorted(
            [row for row in enriched_candidates if row["candidate_grid_reachable"]],
            key=lambda row: (
                row["candidate_grid_path_cost_m"],
                row["candidate_rank_non_persistent"],
                int(row["candidate_instance_id"]) if str(row["candidate_instance_id"]).isdigit() else row["candidate_instance_id"],
            ),
        )
        order_by_key = {id(row): index for index, row in enumerate(reachable_candidates, start=1)}
        for row in enriched_candidates:
            if row["candidate_grid_reachable"]:
                row["candidate_grid_visit_order_index"] = order_by_key[id(row)]
            out_candidates.append(row)

        target = next((row for row in enriched_candidates if row["candidate_is_target"]), None)
        target_reachable = bool(target and target["candidate_grid_reachable"])
        out_queries.append(
            {
                **query,
                "grid_path_cost_profile_id": PROFILE_ID,
                "grid_path_cost_source": "ply_floor_obstacle_occupancy_astar",
                "grid_path_cost_ready": start_ready,
                "free_space_path_cost_ready": start_ready,
                "real_navigation_path_cost_ready": False,
                "grid_failure_type": None if start_ready else "start_unprojectable",
                "grid_resolution_m": GRID_RESOLUTION_M,
                "robot_radius_m": ROBOT_RADIUS_M,
                "grid_scan_free_cell_count": grid.source_summary["free_cell_count"],
                "start_grid_cell": cell_payload(start_projection),
                "start_nearest_free_cell_distance_m": round6(start_projection.get("projection_distance_m")),
                "start_projection_status": start_projection.get("status"),
                "candidate_grid_reachable_count": sum(1 for row in enriched_candidates if row["candidate_grid_reachable"]),
                "candidate_grid_unreachable_count": sum(1 for row in enriched_candidates if not row["candidate_grid_reachable"]),
                "target_grid_path_cost_m": target["candidate_grid_path_cost_m"] if target else None,
                "target_grid_reachable": target_reachable,
                "target_grid_visit_order_index": target["candidate_grid_visit_order_index"] if target else None,
            }
        )
    return out_queries, out_candidates, scan_summaries, failure_rows


def failure_row(
    query: dict[str, Any],
    candidate: dict[str, Any],
    reason: str,
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "row_uid": query["row_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "rescan_id": query["rescan_id"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "object_label": query["object_label"],
        "candidate_instance_id": candidate["candidate_instance_id"],
        "candidate_is_target": candidate["candidate_is_target"],
        "failure_type": reason,
        "projection_status": projection.get("status") if projection else None,
        "next_test": "inspect floor coverage and obstacle inflation for this scan",
    }


def build_report(coverage: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# E002-M05 Occupancy Grid A*",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Dataset root: `{coverage['dataset_root']}`",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Query rows: {coverage['query_rows']}",
        f"- Candidate rows: {coverage['candidate_rows']}",
        f"- Scan grids ready: {coverage['scan_grid_ready_count']} / {coverage['scan_count']}",
        f"- Query rows with free-space path source: {coverage['free_space_path_cost_ready_rows']}",
        f"- Candidate rows reachable: {coverage['candidate_grid_reachable_rows']}",
        f"- Candidate rows unreachable: {coverage['candidate_grid_unreachable_rows']}",
        f"- Target rows reachable: {coverage['target_grid_reachable_rows']}",
        f"- Real navigation path-cost rows: {coverage['real_navigation_path_cost_ready_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Path Profile",
        "",
        f"- `grid_path_cost_profile_id`: `{PROFILE_ID}`",
        f"- Grid resolution: {GRID_RESOLUTION_M}m",
        f"- Robot radius: {ROBOT_RADIUS_M}m",
        "- Source: annotated PLY floor/obstacle occupancy with A* over 2D free cells.",
        "",
        "## Failure Types",
        "",
        "| Failure type | Rows |",
        "| --- | ---: |",
    ]
    for key, value in sorted(coverage["failure_type_counts"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E002-M05 supports free-space path-cost smoke construction from local `3RScan` geometry.",
            "- E002-M05 does not support real navigation `SR` / `SPL`, simulator execution, or deployable search policy claims.",
            "",
            "## 에이전트 추론",
            "",
            "- This upgrades E002 beyond straight-line Euclidean proxy where grid paths are reachable.",
            "- Unreachable rows are explicit artifacts, so denominator drift is avoided.",
            "- The next step should evaluate the existing policies against grid path costs rather than candidate-count or straight-line cost.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E002-M05. Continue to grid-path policy evaluation if this coverage is acceptable.",
            "",
            "## Outputs",
            "",
            "- `grid_query_rows.jsonl`",
            "- `grid_candidate_rows.jsonl`",
            "- `scan_grid_summaries.jsonl`",
            "- `failure_rows.jsonl`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "path_query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "path_candidate_rows.jsonl")
    out_queries, out_candidates, scan_summaries, failure_rows = build_rows(
        args.dataset_root,
        query_rows,
        candidate_rows,
    )

    row_band_counts = Counter(row["row_band"] for row in out_queries)
    failure_type_counts = Counter(row["failure_type"] for row in failure_rows)
    target_rows = [row for row in out_queries if row["target_grid_reachable"]]
    coverage = {
        "status": "grid_path_cost_smoke_ready"
        if len(out_queries) == len(query_rows)
        and len(out_candidates) == len(candidate_rows)
        and any(row["candidate_grid_reachable"] for row in out_candidates)
        else "review_needed",
        "dataset_root": str(args.dataset_root),
        "input_dir": str(args.input_dir),
        "grid_path_cost_profile_id": PROFILE_ID,
        "grid_path_cost_source": "ply_floor_obstacle_occupancy_astar",
        "query_rows": len(out_queries),
        "candidate_rows": len(out_candidates),
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "denominator_preserved": len(out_queries) == len(query_rows)
        and len(out_candidates) == len(candidate_rows),
        "row_band_counts": dict(sorted(row_band_counts.items())),
        "scan_count": len(scan_summaries),
        "scan_grid_ready_count": sum(1 for row in scan_summaries if row["status"] == "ready"),
        "scan_status_counts": dict(sorted(Counter(row["status"] for row in scan_summaries).items())),
        "free_space_path_cost_ready_rows": sum(1 for row in out_queries if row["free_space_path_cost_ready"]),
        "candidate_grid_reachable_rows": sum(1 for row in out_candidates if row["candidate_grid_reachable"]),
        "candidate_grid_unreachable_rows": sum(1 for row in out_candidates if not row["candidate_grid_reachable"]),
        "target_grid_reachable_rows": len(target_rows),
        "target_grid_unreachable_rows": len(out_queries) - len(target_rows),
        "target_grid_path_cost_m_mean": round6(
            sum(float(row["target_grid_path_cost_m"]) for row in target_rows) / len(target_rows)
            if target_rows
            else None
        ),
        "real_navigation_path_cost_ready_rows": sum(
            1 for row in out_queries if row["real_navigation_path_cost_ready"]
        ),
        "failure_rows": len(failure_rows),
        "failure_type_counts": dict(sorted(failure_type_counts.items())),
        "unsupported_claims": [
            "real navigation SR/SPL",
            "collision-aware robot planning",
            "simulator execution",
            "deployable search policy",
            "RGB-D/open-vocabulary perception robustness",
        ],
        "outputs": {
            "grid_query_rows": str(args.out_dir / "grid_query_rows.jsonl"),
            "grid_candidate_rows": str(args.out_dir / "grid_candidate_rows.jsonl"),
            "scan_grid_summaries": str(args.out_dir / "scan_grid_summaries.jsonl"),
            "failure_rows": str(args.out_dir / "failure_rows.jsonl"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "grid_query_rows.jsonl", out_queries)
    write_jsonl(args.out_dir / "grid_candidate_rows.jsonl", out_candidates)
    write_jsonl(args.out_dir / "scan_grid_summaries.jsonl", scan_summaries)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "query_rows": coverage["query_rows"],
                "candidate_rows": coverage["candidate_rows"],
                "scan_grid_ready_count": coverage["scan_grid_ready_count"],
                "scan_count": coverage["scan_count"],
                "candidate_grid_reachable_rows": coverage["candidate_grid_reachable_rows"],
                "target_grid_reachable_rows": coverage["target_grid_reachable_rows"],
                "real_navigation_path_cost_ready_rows": coverage["real_navigation_path_cost_ready_rows"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
