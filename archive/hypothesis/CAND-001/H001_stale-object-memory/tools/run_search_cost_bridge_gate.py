#!/usr/bin/env python3
"""Run H001 search-cost bridge gate.

This hypothesis-stage gate connects the existing bounded top-k memory output
to search-task proxies. It does not claim real navigation. The bridge metrics
are candidate-inspection success, expected checked locations, and an
attempt-count `SPL` proxy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MULTI_PAIR_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_UNCERTAINTY_DIR = H001_ROOT / "artifacts" / "uncertainty_topk_gate"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "search_cost_bridge_gate"
POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "label_top3_current_observation",
    "non_persistent_anchor_v0",
    "uncertainty_topk_v0",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def group_by_uid(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def rank_by_distance(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["distance_to_old_scene_aligned_m"],
            int(row["candidate_instance_id"]),
        ),
    )


def rank_by_non_persistent(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["ranks"]["full_non_persistent"],
            -row["scores"]["full_non_persistent"],
            row["distance_to_old_scene_aligned_m"],
            int(row["candidate_instance_id"]),
        ),
    )


def target_rank(ranked: list[dict]) -> int | None:
    for index, row in enumerate(ranked, start=1):
        if row["eval_is_target_instance"]:
            return index
    return None


def expected_cost(rank: int | None, returned_k: int) -> int:
    if returned_k <= 0:
        return 1
    if rank is not None and rank <= returned_k:
        return rank
    return returned_k + 1


def attempt_spl(success: bool, cost: int) -> float:
    if not success or cost <= 0:
        return 0.0
    return 1.0 / cost


def candidate_distance_at_rank(ranked: list[dict], rank: int | None) -> float | None:
    if rank is None or rank <= 0 or rank > len(ranked):
        return None
    return ranked[rank - 1].get("distance_to_old_scene_aligned_m")


def static_prediction(row: dict) -> dict:
    success = not row["old_memory_is_stale"]
    cost = 1 if success else 2
    return {
        "policy": "scene_aligned_static_map",
        "returned_location_count": 1,
        "target_rank_in_returned": 1 if success else None,
        "search_success": success,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "visits_stale_old_location": bool(row["old_memory_is_stale"]),
        "stale_dead_end": bool(row["old_memory_is_stale"]),
        "candidate_distance_to_old_m": None,
    }


def ranked_policy_prediction(policy: str, row: dict, ranked: list[dict], returned_k: int) -> dict:
    rank = target_rank(ranked)
    success = rank is not None and rank <= returned_k
    cost = expected_cost(rank, returned_k)
    return {
        "policy": policy,
        "returned_location_count": returned_k,
        "target_rank_in_returned": rank,
        "search_success": success,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "visits_stale_old_location": False,
        "stale_dead_end": False,
        "candidate_distance_to_old_m": round_or_none(candidate_distance_at_rank(ranked, rank)),
    }


def uncertainty_prediction(row: dict, uncertainty_by_uid: dict[str, dict]) -> dict:
    item = uncertainty_by_uid[row["row_uid"]]
    returns_old = bool(item["returns_old_location"])
    returned_k = 1 if returns_old else int(item["returned_candidate_count"])
    rank = 1 if returns_old and item["exact_recovery"] else item["target_rank"]
    success = bool(item["exact_recovery"] if returns_old else item["candidate_recall_at_returned_k"])
    cost = int(item["expected_search_cost_proxy"]) if item["expected_search_cost_proxy"] is not None else 1
    return {
        "policy": "uncertainty_topk_v0",
        "returned_location_count": returned_k,
        "target_rank_in_returned": rank,
        "search_success": success,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "visits_stale_old_location": bool(returns_old and row["old_memory_is_stale"]),
        "stale_dead_end": bool(returns_old and row["old_memory_is_stale"] and not success),
        "candidate_distance_to_old_m": None,
        "decision_reason": item.get("decision_reason"),
        "high_uncertainty_route": item.get("high_uncertainty_route"),
    }


def build_predictions(
    query_rows: list[dict],
    candidates_by_uid: dict[str, list[dict]],
    uncertainty_by_uid: dict[str, dict],
) -> list[dict]:
    rows = []
    for row in query_rows:
        distance_ranked = rank_by_distance(candidates_by_uid.get(row["row_uid"], []))
        np_ranked = rank_by_non_persistent(candidates_by_uid.get(row["row_uid"], []))
        policy_items = [
            static_prediction(row),
            ranked_policy_prediction(
                "label_nearest_current_observation",
                row,
                distance_ranked,
                min(1, len(distance_ranked)),
            ),
            ranked_policy_prediction(
                "label_top3_current_observation",
                row,
                distance_ranked,
                min(3, len(distance_ranked)),
            ),
            ranked_policy_prediction(
                "non_persistent_anchor_v0",
                row,
                np_ranked,
                min(1, len(np_ranked)),
            ),
            uncertainty_prediction(row, uncertainty_by_uid),
        ]
        for item in policy_items:
            rows.append(
                {
                    "row_uid": row["row_uid"],
                    "pair_uid": row["pair_uid"],
                    "object_label": row["object_label"],
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "row_band": row["row_band"],
                    "old_memory_is_stale": row["old_memory_is_stale"],
                    "same_label_candidate_count": row.get("same_label_candidate_count"),
                    "scene_aligned_static_planar_error_m": row.get(
                        "scene_aligned_static_planar_error_m"
                    ),
                    **item,
                }
            )
    return rows


def summarize(rows: list[dict], subset_name: str) -> dict:
    by_policy = {}
    for policy in POLICIES:
        items = [row for row in rows if row["policy"] == policy]
        successes = [row for row in items if row["search_success"]]
        stale_items = [row for row in items if row["old_memory_is_stale"]]
        by_policy[policy] = {
            "subset": subset_name,
            "rows": len(items),
            "search_success_rate": safe_rate(len(successes), len(items)),
            "mean_expected_checked_locations": mean(
                [float(row["expected_checked_locations"]) for row in items]
            ),
            "mean_expected_checked_locations_success_only": mean(
                [float(row["expected_checked_locations"]) for row in successes]
            ),
            "attempt_spl_proxy": mean([float(row["attempt_spl_proxy"]) for row in items]),
            "mean_returned_location_count": mean(
                [float(row["returned_location_count"]) for row in items]
            ),
            "stale_old_location_visit_rate": safe_rate(
                sum(1 for row in stale_items if row["visits_stale_old_location"]),
                len(stale_items),
            ),
            "stale_dead_end_rate": safe_rate(
                sum(1 for row in stale_items if row["stale_dead_end"]),
                len(stale_items),
            ),
            "mean_candidate_distance_to_old_m": mean(
                [
                    float(row["candidate_distance_to_old_m"])
                    for row in items
                    if row.get("candidate_distance_to_old_m") is not None
                ]
            ),
        }
    return by_policy


def pair_breakdown(rows: list[dict]) -> list[dict]:
    output = []
    for pair_uid in sorted({row["pair_uid"] for row in rows}):
        pair_rows = [row for row in rows if row["pair_uid"] == pair_uid]
        output.append(
            {
                "pair_uid": pair_uid,
                "significant_rows": len(
                    {
                        row["row_uid"]
                        for row in pair_rows
                        if row["row_band"] == "significant_moved"
                    }
                ),
                "metrics": summarize(pair_rows, pair_uid),
            }
        )
    return output


def decide_status(coverage: dict, metrics: dict) -> str:
    sig = metrics["significant_moved"]
    uncertainty = sig["uncertainty_topk_v0"]
    static = sig["scene_aligned_static_map"]
    label_top3 = sig["label_top3_current_observation"]
    direct_np = sig["non_persistent_anchor_v0"]
    low = metrics["low_motion_control"]["uncertainty_topk_v0"]
    metric_pass = (
        coverage["significant_moved_rows"] >= 10
        and uncertainty["search_success_rate"] == 1.0
        and uncertainty["search_success_rate"] > static["search_success_rate"]
        and uncertainty["search_success_rate"] > label_top3["search_success_rate"]
        and uncertainty["attempt_spl_proxy"] > direct_np["attempt_spl_proxy"]
        and uncertainty["mean_expected_checked_locations"] <= 2.0
        and uncertainty["stale_dead_end_rate"] == 0.0
        and low["search_success_rate"] >= 0.95
    )
    return "bridge_pass" if metric_pass else "fail"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--multi-pair-dir", type=Path, default=DEFAULT_MULTI_PAIR_DIR)
    parser.add_argument("--uncertainty-dir", type=Path, default=DEFAULT_UNCERTAINTY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.multi_pair_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.multi_pair_dir / "candidate_rows.jsonl")
    uncertainty_rows = load_jsonl(args.uncertainty_dir / "predictions.jsonl")
    multi_pair_coverage = load_json(args.multi_pair_dir / "coverage.json")
    uncertainty_coverage = load_json(args.uncertainty_dir / "coverage.json")

    candidates_by_uid = group_by_uid(candidate_rows)
    uncertainty_by_uid = {row["row_uid"]: row for row in uncertainty_rows}
    predictions = build_predictions(query_rows, candidates_by_uid, uncertainty_by_uid)

    significant = [row for row in predictions if row["row_band"] == "significant_moved"]
    low_motion = [row for row in predictions if row["row_band"] == "low_motion_control"]
    high_ambiguity = [
        row
        for row in predictions
        if row["row_band"] == "significant_moved"
        and row.get("same_label_candidate_count") is not None
        and row["same_label_candidate_count"] >= 5
    ]
    metrics = {
        "significant_moved": summarize(significant, "significant_moved"),
        "low_motion_control": summarize(low_motion, "low_motion_control"),
        "high_ambiguity_significant": summarize(
            high_ambiguity, "high_ambiguity_significant"
        ),
        "per_pair_significant": pair_breakdown(significant),
    }

    coverage = {
        "input_multi_pair_dir": str(args.multi_pair_dir),
        "input_uncertainty_dir": str(args.uncertainty_dir),
        "validated_pair_count": multi_pair_coverage.get("validated_pair_count"),
        "query_rows": len(query_rows),
        "significant_moved_rows": len(
            [row for row in query_rows if row["row_band"] == "significant_moved"]
        ),
        "low_motion_control_rows": len(
            [row for row in query_rows if row["row_band"] == "low_motion_control"]
        ),
        "uses_navigation": False,
        "uses_navmesh_or_obstacle_map": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "uses_annotation_level_current_observation": uncertainty_coverage.get(
            "uses_annotation_level_current_observation"
        ),
        "ranking_uses_persistent_cross_scan_ids": False,
        "metric_is_proxy_for_sr_spl": True,
        "proxy_sr_definition": "target found within returned candidate-location budget",
        "proxy_spl_definition": "mean 1 / checked_locations for successful rows, 0 for failures",
        "not_supported_claims": [
            "real navigation SR",
            "real navigation SPL",
            "deployable search policy",
            "RGB-D perception robustness",
            "open-vocabulary perception robustness",
        ],
    }
    coverage["status"] = decide_status(coverage, metrics)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    print(
        json.dumps(
            {
                "coverage": coverage,
                "significant_moved": metrics["significant_moved"],
                "low_motion_control": metrics["low_motion_control"],
                "high_ambiguity_significant": metrics["high_ambiguity_significant"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
