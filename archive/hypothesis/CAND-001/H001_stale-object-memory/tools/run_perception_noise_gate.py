#!/usr/bin/env python3
"""Run H001 perception-noise robustness gate.

This is a hypothesis-stage controlled-noise gate. It perturbs annotation-level
current object proposals to test whether stale-memory update decisions remain
useful when proposal ranking is imperfect. It does not use real RGB-D or
open-vocabulary detections.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "perception_noise_gate"
SCORE_KEY = "full_non_persistent"
POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "label_top3_current_observation",
    "non_persistent_anchor_v0",
    "uncertainty_topk_v0",
]
FEATURE_KEYS = [
    "shape_similarity",
    "orientation_similarity",
    "height_similarity",
    "relation_label_overlap",
    "local_label_context_histogram",
    "support_surface_context",
]
SCENARIOS = [
    {
        "name": "clean_replay",
        "trials": 1,
        "seed_offset": 0,
        "localization_jitter_m": 0.0,
        "feature_noise_std": 0.0,
        "non_target_dropout_prob": 0.0,
        "target_dropout_prob": 0.0,
        "false_positive_prob": 0.0,
        "false_positive_max": 0,
    },
    {
        "name": "ranking_noise_moderate",
        "trials": 100,
        "seed_offset": 1000,
        "localization_jitter_m": 0.20,
        "feature_noise_std": 0.08,
        "non_target_dropout_prob": 0.10,
        "target_dropout_prob": 0.0,
        "false_positive_prob": 0.50,
        "false_positive_max": 1,
    },
    {
        "name": "target_dropout_stress",
        "trials": 100,
        "seed_offset": 2000,
        "localization_jitter_m": 0.20,
        "feature_noise_std": 0.08,
        "non_target_dropout_prob": 0.10,
        "target_dropout_prob": 0.20,
        "false_positive_prob": 0.50,
        "false_positive_max": 1,
    },
    {
        "name": "heavy_noise_stress",
        "trials": 100,
        "seed_offset": 3000,
        "localization_jitter_m": 0.35,
        "feature_noise_std": 0.15,
        "non_target_dropout_prob": 0.20,
        "target_dropout_prob": 0.10,
        "false_positive_prob": 1.00,
        "false_positive_max": 2,
    },
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


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def geometry_score(features: dict) -> float:
    return (
        0.6 * features["shape_similarity"]
        + 0.25 * features["orientation_similarity"]
        + 0.25 * features["height_similarity"]
        + 0.25 * features["old_location_prior"]
    )


def score_features(features: dict, ablation: str) -> float:
    geom = geometry_score(features)
    if ablation == "full_non_persistent":
        return (
            geom
            + 1.0 * features["relation_label_overlap"]
            + 1.2 * features["local_label_context_histogram"]
            + 0.4 * features["support_surface_context"]
        )
    if ablation == "geometry_only":
        return geom
    if ablation == "relation_label_only":
        return features["relation_label_overlap"] + 0.4 * features["support_surface_context"]
    if ablation == "local_label_context_only":
        return features["local_label_context_histogram"]
    if ablation == "geometry_plus_relation_label":
        return geom + 1.0 * features["relation_label_overlap"] + 0.4 * features["support_surface_context"]
    if ablation == "geometry_plus_local_context":
        return geom + 1.2 * features["local_label_context_histogram"]
    if ablation == "old_location_only":
        return features["old_location_prior"]
    raise RuntimeError(f"unknown ablation: {ablation}")


def group_by_uid(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def candidate_order(row: dict) -> int:
    value = str(row["candidate_instance_id"])
    return int(value) if value.isdigit() else 1_000_000


def rank_by_distance(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["distance_to_old_scene_aligned_m"],
            candidate_order(row),
        ),
    )


def rank_by_score(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            -row["scores"][SCORE_KEY],
            row["distance_to_old_scene_aligned_m"],
            candidate_order(row),
        ),
    )


def target_rank(ranked: list[dict]) -> int | None:
    for index, row in enumerate(ranked, start=1):
        if row["eval_is_target_instance"]:
            return index
    return None


def normalized_entropy(scores: list[float]) -> float | None:
    if len(scores) <= 1:
        return None
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    total = sum(exp_scores)
    probs = [score / total for score in exp_scores]
    entropy = -sum(prob * math.log(prob) for prob in probs if prob > 0)
    return entropy / math.log(len(scores))


def candidate_set_size_under_margin(ranked: list[dict], margin: float = 0.1) -> int:
    if not ranked:
        return 0
    top_score = ranked[0]["scores"][SCORE_KEY]
    return sum(1 for row in ranked if top_score - row["scores"][SCORE_KEY] <= margin)


def candidate_stats(ranked: list[dict]) -> dict:
    scores = [row["scores"][SCORE_KEY] for row in ranked]
    return {
        "candidate_entropy": round_or_none(normalized_entropy(scores)),
        "score_margin_top1_top2": round_or_none(
            ranked[0]["scores"][SCORE_KEY] - ranked[1]["scores"][SCORE_KEY]
            if len(ranked) > 1
            else None
        ),
        "candidate_set_size_under_margin_0_1": candidate_set_size_under_margin(ranked, 0.1),
    }


def topk_decision(row: dict, ranked: list[dict], stats: dict) -> tuple[str, int, str]:
    if not row["old_memory_is_stale"]:
        return "trusted_or_low_motion", 1, "low_motion_trusted_old_location"
    if not ranked:
        return "needs_reobservation", 0, "no_same_label_candidate"
    candidate_count = len(ranked)
    entropy = stats["candidate_entropy"]
    margin = stats["score_margin_top1_top2"]
    margin_set = stats["candidate_set_size_under_margin_0_1"]
    if candidate_count == 1:
        return "single_current_candidate", 1, "unique_same_label_candidate"
    if candidate_count == 2:
        return "topk_current_candidates", 2, "two_same_label_candidates"
    if candidate_count >= 5 and entropy is not None and entropy >= 0.90:
        return "topk_current_candidates", min(3, candidate_count), "high_ambiguity_high_entropy"
    if margin is not None and margin <= 0.10:
        return "topk_current_candidates", min(3, candidate_count), "low_top1_top2_margin"
    if margin_set > 1:
        return "topk_current_candidates", min(3, margin_set), "multiple_candidates_inside_margin"
    return "single_current_candidate", 1, "confident_top1"


def expected_cost(rank: int | None, returned_k: int, stale: bool) -> int | None:
    if not stale:
        return 1
    if returned_k <= 0:
        return None
    if rank is not None and rank <= returned_k:
        return rank
    return returned_k + 1


def attempt_spl(success: bool, cost: int | None) -> float:
    if not success or cost is None or cost <= 0:
        return 0.0
    return 1.0 / cost


def perturb_features(row: dict, scenario: dict, rng: random.Random) -> dict:
    output = json.loads(json.dumps(row))
    features = output["features"]
    jittered_distance = max(
        0.0,
        float(output["distance_to_old_scene_aligned_m"])
        + rng.gauss(0.0, scenario["localization_jitter_m"]),
    )
    output["distance_to_old_scene_aligned_m"] = round(jittered_distance, 6)
    features["old_location_prior"] = round(math.exp(-jittered_distance / 2.0), 6)
    for key in FEATURE_KEYS:
        features[key] = round(
            clamp01(float(features[key]) + rng.gauss(0.0, scenario["feature_noise_std"])),
            6,
        )
    output["scores"] = {
        key: round_or_none(score_features(features, key))
        for key in output["scores"].keys()
    }
    return output


def synthetic_false_positive(
    row_uid: str,
    template_rows: list[dict],
    scenario: dict,
    rng: random.Random,
    index: int,
) -> dict:
    template = rng.choice(template_rows)
    fake = json.loads(json.dumps(template))
    fake["candidate_instance_id"] = str(900000 + index)
    fake["eval_is_target_instance"] = False
    fake["noise_injected_false_positive"] = True
    fake["distance_to_old_scene_aligned_m"] = round(
        max(0.0, rng.gauss(float(template["distance_to_old_scene_aligned_m"]), 0.75)),
        6,
    )
    features = fake["features"]
    features["old_location_prior"] = round(math.exp(-fake["distance_to_old_scene_aligned_m"] / 2.0), 6)
    for key in FEATURE_KEYS:
        features[key] = round(clamp01(rng.uniform(0.15, 0.95)), 6)
    fake["scores"] = {
        key: round_or_none(score_features(features, key))
        for key in fake["scores"].keys()
    }
    fake["row_uid"] = row_uid
    return fake


def perturb_candidates(
    row: dict,
    base_rows: list[dict],
    scenario: dict,
    rng: random.Random,
) -> tuple[list[dict], bool, int, int]:
    kept = []
    target_present_before = any(item["eval_is_target_instance"] for item in base_rows)
    target_dropped = 0
    non_target_dropped = 0
    for item in base_rows:
        drop_prob = (
            scenario["target_dropout_prob"]
            if item["eval_is_target_instance"]
            else scenario["non_target_dropout_prob"]
        )
        if rng.random() < drop_prob:
            if item["eval_is_target_instance"]:
                target_dropped += 1
            else:
                non_target_dropped += 1
            continue
        kept.append(perturb_features(item, scenario, rng))
    fp_count = 0
    if kept and scenario["false_positive_max"] > 0 and rng.random() < scenario["false_positive_prob"]:
        fp_count = rng.randint(1, scenario["false_positive_max"])
        for index in range(fp_count):
            kept.append(synthetic_false_positive(row["row_uid"], kept, scenario, rng, index))
    target_observable = target_present_before and any(item["eval_is_target_instance"] for item in kept)
    return kept, target_observable, target_dropped, non_target_dropped


def predict_ranked_policy(
    policy: str,
    row: dict,
    ranked: list[dict],
    returned_k: int,
    target_observable: bool,
) -> dict:
    if not row["old_memory_is_stale"]:
        return {
            "policy": policy,
            "search_success": True,
            "target_observable": target_observable,
            "target_rank": 1,
            "returned_location_count": 1,
            "expected_checked_locations": 1,
            "attempt_spl_proxy": 1.0,
            "stale_dead_end": False,
            "uses_candidate_observation": False,
        }
    rank = target_rank(ranked)
    success = rank is not None and rank <= returned_k
    cost = expected_cost(rank, returned_k, True)
    return {
        "policy": policy,
        "search_success": success,
        "target_observable": target_observable,
        "target_rank": rank,
        "returned_location_count": returned_k,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "stale_dead_end": False,
        "uses_candidate_observation": True,
    }


def predict_static(row: dict, target_observable: bool) -> dict:
    if not row["old_memory_is_stale"]:
        success = True
        cost = 1
    else:
        success = False
        cost = 2
    return {
        "policy": "scene_aligned_static_map",
        "search_success": success,
        "target_observable": target_observable,
        "target_rank": None if row["old_memory_is_stale"] else 1,
        "returned_location_count": 1,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "stale_dead_end": bool(row["old_memory_is_stale"]),
        "uses_candidate_observation": False,
    }


def predict_uncertainty(row: dict, ranked: list[dict], target_observable: bool) -> dict:
    if not row["old_memory_is_stale"]:
        return {
            "policy": "uncertainty_topk_v0",
            "search_success": True,
            "target_observable": target_observable,
            "target_rank": 1,
            "returned_location_count": 1,
            "expected_checked_locations": 1,
            "attempt_spl_proxy": 1.0,
            "stale_dead_end": False,
            "uses_candidate_observation": False,
            "decision_reason": "low_motion_trusted_old_location",
            "high_uncertainty_route": False,
        }
    stats = candidate_stats(ranked)
    _state, returned_k, reason = topk_decision(row, ranked, stats)
    rank = target_rank(ranked)
    success = rank is not None and rank <= returned_k
    cost = expected_cost(rank, returned_k, True)
    return {
        "policy": "uncertainty_topk_v0",
        "search_success": success,
        "target_observable": target_observable,
        "target_rank": rank,
        "returned_location_count": returned_k,
        "expected_checked_locations": cost,
        "attempt_spl_proxy": attempt_spl(success, cost),
        "stale_dead_end": False,
        "uses_candidate_observation": returned_k > 0,
        "decision_reason": reason,
        "high_uncertainty_route": returned_k > 1,
        **stats,
    }


def run_scenario(
    scenario: dict,
    query_rows: list[dict],
    candidates_by_uid: dict[str, list[dict]],
    base_seed: int,
) -> list[dict]:
    predictions = []
    for trial in range(scenario["trials"]):
        rng = random.Random(base_seed + scenario["seed_offset"] + trial)
        for row in query_rows:
            perturbed, target_observable, target_dropped, non_target_dropped = perturb_candidates(
                row, candidates_by_uid.get(row["row_uid"], []), scenario, rng
            )
            distance_ranked = rank_by_distance(perturbed)
            score_ranked = rank_by_score(perturbed)
            policy_outputs = [
                predict_static(row, target_observable),
                predict_ranked_policy(
                    "label_nearest_current_observation",
                    row,
                    distance_ranked,
                    min(1, len(distance_ranked)),
                    target_observable,
                ),
                predict_ranked_policy(
                    "label_top3_current_observation",
                    row,
                    distance_ranked,
                    min(3, len(distance_ranked)),
                    target_observable,
                ),
                predict_ranked_policy(
                    "non_persistent_anchor_v0",
                    row,
                    score_ranked,
                    min(1, len(score_ranked)),
                    target_observable,
                ),
                predict_uncertainty(row, score_ranked, target_observable),
            ]
            for item in policy_outputs:
                predictions.append(
                    {
                        "scenario": scenario["name"],
                        "trial": trial,
                        "row_uid": row["row_uid"],
                        "pair_uid": row["pair_uid"],
                        "object_label": row["object_label"],
                        "object_instance_id_ref": row["object_instance_id_ref"],
                        "row_band": row["row_band"],
                        "old_memory_is_stale": row["old_memory_is_stale"],
                        "base_candidate_count": len(candidates_by_uid.get(row["row_uid"], [])),
                        "perturbed_candidate_count": len(perturbed),
                        "target_dropped": target_dropped > 0,
                        "non_target_dropped_count": non_target_dropped,
                        "false_positive_count": sum(
                            1 for candidate in perturbed if candidate.get("noise_injected_false_positive")
                        ),
                        **item,
                    }
                )
    return predictions


def summarize_subset(rows: list[dict], subset_name: str) -> dict:
    output = {}
    for policy in POLICIES:
        items = [row for row in rows if row["policy"] == policy]
        observable = [row for row in items if row["target_observable"]]
        stale_items = [row for row in items if row["old_memory_is_stale"]]
        low_items = [row for row in items if row["row_band"] == "low_motion_control"]
        output[policy] = {
            "subset": subset_name,
            "rows": len(items),
            "target_observable_rate": safe_rate(
                sum(1 for row in items if row["target_observable"]), len(items)
            ),
            "search_success_rate_all": safe_rate(
                sum(1 for row in items if row["search_success"]), len(items)
            ),
            "search_success_rate_when_target_observable": safe_rate(
                sum(1 for row in observable if row["search_success"]), len(observable)
            ),
            "attempt_spl_proxy_all": mean([float(row["attempt_spl_proxy"]) for row in items]),
            "attempt_spl_proxy_when_target_observable": mean(
                [float(row["attempt_spl_proxy"]) for row in observable]
            ),
            "mean_checked_locations_all": mean(
                [
                    float(row["expected_checked_locations"])
                    for row in items
                    if row["expected_checked_locations"] is not None
                ]
            ),
            "mean_returned_location_count": mean(
                [float(row["returned_location_count"]) for row in items]
            ),
            "stale_dead_end_rate": safe_rate(
                sum(1 for row in stale_items if row["stale_dead_end"]), len(stale_items)
            ),
            "low_motion_static_preserved_rate": safe_rate(
                sum(1 for row in low_items if row["search_success"] and not row["uses_candidate_observation"]),
                len(low_items),
            ),
            "mean_target_rank_observable": mean(
                [
                    float(row["target_rank"])
                    for row in observable
                    if row["target_rank"] is not None
                ]
            ),
            "mean_false_positive_count": mean(
                [float(row["false_positive_count"]) for row in items]
            ),
            "mean_non_target_dropped_count": mean(
                [float(row["non_target_dropped_count"]) for row in items]
            ),
        }
    return output


def summarize(predictions: list[dict], query_rows: list[dict]) -> dict:
    output = {}
    for scenario in SCENARIOS:
        scenario_rows = [row for row in predictions if row["scenario"] == scenario["name"]]
        output[scenario["name"]] = {
            "all": summarize_subset(scenario_rows, "all"),
            "significant_moved": summarize_subset(
                [row for row in scenario_rows if row["row_band"] == "significant_moved"],
                "significant_moved",
            ),
            "low_motion_control": summarize_subset(
                [row for row in scenario_rows if row["row_band"] == "low_motion_control"],
                "low_motion_control",
            ),
            "high_ambiguity_significant": summarize_subset(
                [
                    row
                    for row in scenario_rows
                    if row["row_band"] == "significant_moved"
                    and row["base_candidate_count"] >= 5
                ],
                "high_ambiguity_significant",
            ),
        }
    output["row_counts"] = {
        "query_rows": len(query_rows),
        "significant_moved_rows": sum(1 for row in query_rows if row["row_band"] == "significant_moved"),
        "low_motion_control_rows": sum(1 for row in query_rows if row["row_band"] == "low_motion_control"),
    }
    return output


def prediction_sample(predictions: list[dict], limit: int = 2000) -> list[dict]:
    priority = [
        row
        for row in predictions
        if row["row_band"] == "significant_moved"
        and row["scenario"] in {"ranking_noise_moderate", "target_dropout_stress", "heavy_noise_stress"}
    ]
    return priority[:limit]


def decide_status(metrics: dict) -> str:
    primary = metrics["ranking_noise_moderate"]["significant_moved"]
    uncertainty = primary["uncertainty_topk_v0"]
    direct = primary["non_persistent_anchor_v0"]
    label_top3 = primary["label_top3_current_observation"]
    low = metrics["ranking_noise_moderate"]["low_motion_control"]["uncertainty_topk_v0"]
    gate_pass = (
        uncertainty["target_observable_rate"] == 1.0
        and uncertainty["search_success_rate_when_target_observable"] is not None
        and uncertainty["search_success_rate_when_target_observable"] >= 0.90
        and uncertainty["search_success_rate_when_target_observable"]
        > direct["search_success_rate_when_target_observable"]
        and uncertainty["search_success_rate_when_target_observable"]
        > label_top3["search_success_rate_when_target_observable"]
        and uncertainty["attempt_spl_proxy_when_target_observable"]
        > direct["attempt_spl_proxy_when_target_observable"]
        and uncertainty["mean_checked_locations_all"] <= 2.0
        and uncertainty["stale_dead_end_rate"] == 0.0
        and low["low_motion_static_preserved_rate"] >= 0.95
    )
    return "robustness_pass" if gate_pass else "fail"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=1701)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions = []
    for scenario in SCENARIOS:
        predictions.extend(run_scenario(scenario, query_rows, candidates_by_uid, args.seed))
    metrics = summarize(predictions, query_rows)
    coverage = {
        "input_dir": str(args.input_dir),
        "query_rows": len(query_rows),
        "validated_pair_count": input_coverage.get("validated_pair_count"),
        "significant_moved_rows": metrics["row_counts"]["significant_moved_rows"],
        "low_motion_control_rows": metrics["row_counts"]["low_motion_control_rows"],
        "scenarios": SCENARIOS,
        "primary_scenario": "ranking_noise_moderate",
        "uses_controlled_annotation_level_proposal_noise": True,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "uses_navigation": False,
        "uses_persistent_cross_scan_ids_for_ranking": False,
        "not_supported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary perception robustness",
            "deployable search policy",
            "real navigation SR/SPL",
        ],
    }
    coverage["status"] = decide_status(metrics)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    full_predictions_path = args.out_dir / "predictions.jsonl"
    if full_predictions_path.exists():
        full_predictions_path.unlink()
    write_jsonl(args.out_dir / "predictions_sample.jsonl", prediction_sample(predictions))
    print(
        json.dumps(
            {
                "coverage": coverage,
                "primary_significant": metrics["ranking_noise_moderate"]["significant_moved"],
                "target_dropout_stress_significant": metrics["target_dropout_stress"]["significant_moved"],
                "heavy_noise_stress_significant": metrics["heavy_noise_stress"]["significant_moved"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
