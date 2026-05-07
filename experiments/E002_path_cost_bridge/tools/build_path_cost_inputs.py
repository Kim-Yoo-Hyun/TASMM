#!/usr/bin/env python3
"""Build E002 path-cost bridge inputs from E001 query/candidate rows."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_DIR = REPO_ROOT / "experiments" / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M01_path_cost_inputs_v0"
PROFILE_ID = "euclidean_polyline_proxy_v0"
OLD_LOCATION_DEAD_END_COST_M = 1.0


def load_json(path: Path) -> dict[str, Any]:
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


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def path_aware_order(query: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = query["old_scene_aligned_centroid"]
    enriched = []
    for candidate in candidates:
        direct_cost = distance(start, candidate["candidate_centroid"])
        enriched.append(
            {
                **candidate,
                "path_cost_profile_id": PROFILE_ID,
                "candidate_path_cost_source": "euclidean_old_memory_to_candidate_centroid",
                "candidate_path_cost_m": round6(direct_cost),
                "candidate_path_cost_ready": True,
                "real_navigation_path_cost_ready": False,
            }
        )

    ordered = sorted(
        enriched,
        key=lambda row: (
            row["candidate_path_cost_m"],
            row["candidate_rank_non_persistent"],
            int(row["candidate_instance_id"]) if str(row["candidate_instance_id"]).isdigit() else row["candidate_instance_id"],
        ),
    )
    cumulative = 0.0
    previous = start
    output = []
    for index, row in enumerate(ordered, start=1):
        step = distance(previous, row["candidate_centroid"])
        cumulative += step
        output.append(
            {
                **row,
                "candidate_visit_policy": "path_aware_euclidean_order_v0",
                "candidate_path_visit_order_index": index,
                "candidate_path_step_cost_m": round6(step),
                "candidate_path_cumulative_cost_m": round6(cumulative),
            }
        )
        previous = row["candidate_centroid"]
    return output


def target_path_stats(ordered: list[dict[str, Any]]) -> dict[str, Any]:
    for row in ordered:
        if row["candidate_is_target"]:
            return {
                "target_path_rank": row["candidate_path_visit_order_index"],
                "target_path_cost_m": row["candidate_path_cumulative_cost_m"],
                "target_direct_path_cost_m": row["candidate_path_cost_m"],
            }
    return {
        "target_path_rank": None,
        "target_path_cost_m": None,
        "target_direct_path_cost_m": None,
    }


def build_rows(
    query_rows: list[dict[str, Any]],
    candidates_by_uid: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path_queries = []
    path_candidates = []
    for query in query_rows:
        ordered = path_aware_order(query, candidates_by_uid.get(query["row_uid"], []))
        stats = target_path_stats(ordered)
        old_dead_end_expected = bool(query["old_memory_is_stale"])
        query_out = {
            **query,
            "path_cost_profile_id": PROFILE_ID,
            "path_cost_source": "euclidean_polyline_proxy",
            "path_cost_proxy_ready": True,
            "real_navigation_path_cost_ready": False,
            "path_cost_ready": True,
            "navmesh_or_free_space_source": None,
            "search_start_policy": "old_memory_location_proxy",
            "path_start_centroid": query["old_scene_aligned_centroid"],
            "old_location_dead_end_expected": old_dead_end_expected,
            "old_location_dead_end_cost_m": OLD_LOCATION_DEAD_END_COST_M if old_dead_end_expected else 0.0,
            "old_location_dead_end_cost_source": "fixed_inspection_penalty_distance_equivalent",
            "candidate_visit_order_policy": "path_aware_euclidean_order_v0",
            "candidate_path_count": len(ordered),
            **stats,
        }
        path_queries.append(query_out)
        path_candidates.extend(ordered)
    return path_queries, path_candidates


def build_report(coverage: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# E002-M01 Path Cost Inputs",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Query rows: {coverage['query_rows']}",
        f"- Candidate rows: {coverage['candidate_rows']}",
        f"- Rows with path-cost proxy: {coverage['path_cost_proxy_ready_rows']}",
        f"- Rows with real navigation path cost: {coverage['real_navigation_path_cost_ready_rows']}",
        f"- Significant moved rows: {coverage['row_band_counts'].get('significant_moved', 0)}",
        f"- Old-location dead-end rows: {coverage['old_location_dead_end_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Path Profile",
        "",
        f"- `path_cost_profile_id`: `{PROFILE_ID}`",
        "- Source: Euclidean polyline proxy from old memory location to ordered candidate centroids.",
        f"- Old-location dead-end cost: {OLD_LOCATION_DEAD_END_COST_M}m distance-equivalent inspection penalty for stale rows.",
        "",
        "## 논문 주장",
        "",
        "- E002-M01 supports path-cost bridge input construction.",
        "- E002-M01 does not support real navigation `SR` / `SPL` or deployable search policy claims.",
        "",
        "## 에이전트 추론",
        "",
        "- The E001 denominator is preserved while adding path-cost fields.",
        "- This makes the next E002 step an evaluation problem rather than a schema problem.",
        "- Real navigation claims still require navmesh, occupancy, simulator, or robot trajectory path cost.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E002-M01. Continue to E002 path-cost policy evaluation.",
        "",
        "## Outputs",
        "",
        "- `path_query_rows.jsonl`",
        "- `path_candidate_rows.jsonl`",
        "- `coverage.json`",
        "- `report.md`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_E001_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    candidates_by_uid = group_by_uid(candidate_rows)
    path_queries, path_candidates = build_rows(query_rows, candidates_by_uid)

    row_band_counts = Counter(row["row_band"] for row in path_queries)
    task_context_counts = Counter(row["task_context_id"] for row in path_queries)
    target_ranks = [
        row["target_path_rank"]
        for row in path_queries
        if row["target_path_rank"] is not None
    ]
    coverage = {
        "status": "path_cost_inputs_ready" if len(path_queries) == len(query_rows) else "review_needed",
        "input_dir": str(args.input_dir),
        "input_validated_pair_count": input_coverage.get("validated_pair_count"),
        "query_rows": len(path_queries),
        "candidate_rows": len(path_candidates),
        "row_band_counts": dict(sorted(row_band_counts.items())),
        "task_context_counts": dict(sorted(task_context_counts.items())),
        "path_cost_profile_id": PROFILE_ID,
        "path_cost_source": "euclidean_polyline_proxy",
        "path_cost_proxy_ready_rows": sum(1 for row in path_queries if row["path_cost_proxy_ready"]),
        "real_navigation_path_cost_ready_rows": sum(
            1 for row in path_queries if row["real_navigation_path_cost_ready"]
        ),
        "old_location_dead_end_cost_m": OLD_LOCATION_DEAD_END_COST_M,
        "old_location_dead_end_rows": sum(
            1 for row in path_queries if row["old_location_dead_end_expected"]
        ),
        "target_path_rank_min": min(target_ranks) if target_ranks else None,
        "target_path_rank_max": max(target_ranks) if target_ranks else None,
        "target_path_rank_mean": round6(sum(target_ranks) / len(target_ranks) if target_ranks else None),
        "denominator_preserved": len(path_queries) == len(query_rows),
        "unsupported_claims": [
            "real navigation SR/SPL",
            "collision-aware path planning",
            "deployable search policy",
            "RGB-D/open-vocabulary perception robustness",
        ],
        "outputs": {
            "path_query_rows": str(args.out_dir / "path_query_rows.jsonl"),
            "path_candidate_rows": str(args.out_dir / "path_candidate_rows.jsonl"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "path_query_rows.jsonl", path_queries)
    write_jsonl(args.out_dir / "path_candidate_rows.jsonl", path_candidates)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "query_rows": coverage["query_rows"],
                "candidate_rows": coverage["candidate_rows"],
                "old_location_dead_end_rows": coverage["old_location_dead_end_rows"],
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
