#!/usr/bin/env python3
"""Run H001 task-context conditioning gate.

This hypothesis-stage gate tests whether structured task context can change
memory trust / candidate budget decisions in a useful way. It does not claim
natural-language intention understanding. Contexts are given as simple cost
profiles.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

import run_perception_noise_gate as noise


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "task_context_gate"
CONTEXTS = [
    {
        "name": "routine_fetch",
        "success_reward": 1.0,
        "check_cost": 0.15,
        "failure_cost": 0.0,
        "max_budget": 3,
        "high_ambiguity_budget": 2,
        "description": "ordinary task; keep bounded search cost",
    },
    {
        "name": "high_value_fetch",
        "success_reward": 3.0,
        "check_cost": 0.15,
        "failure_cost": 0.25,
        "max_budget": 5,
        "high_ambiguity_budget": 5,
        "description": "important task; accept larger candidate set to avoid misses",
    },
    {
        "name": "noisy_high_value_fetch",
        "success_reward": 3.0,
        "check_cost": 0.15,
        "failure_cost": 0.25,
        "max_budget": 5,
        "high_ambiguity_budget": 5,
        "description": "important task under noisy perception; expand budget when perception risk is high",
    },
]
STRESS_SCENARIOS = {"target_dropout_stress", "heavy_noise_stress"}


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def fixed_uncertainty_budget(row: dict, ranked: list[dict]) -> int:
    stats = noise.candidate_stats(ranked)
    _state, returned_k, _reason = noise.topk_decision(row, ranked, stats)
    return returned_k


def is_high_ambiguity(ranked: list[dict]) -> bool:
    if not ranked:
        return False
    stats = noise.candidate_stats(ranked)
    entropy = stats.get("candidate_entropy")
    margin = stats.get("score_margin_top1_top2")
    return bool(
        len(ranked) >= 5
        or (entropy is not None and entropy >= 0.90)
        or (margin is not None and margin <= 0.10)
        or stats.get("candidate_set_size_under_margin_0_1", 0) > 1
    )


def conditioned_budget(
    row: dict,
    ranked: list[dict],
    context: dict,
    scenario_name: str,
) -> tuple[int, str]:
    if not row["old_memory_is_stale"]:
        return 1, "trusted_low_motion_memory"
    if not ranked:
        return 0, "no_candidate_reobserve"

    base_k = fixed_uncertainty_budget(row, ranked)
    high_ambiguity = is_high_ambiguity(ranked)
    candidate_count = len(ranked)
    name = context["name"]

    if name == "routine_fetch":
        budget = max(base_k, context["high_ambiguity_budget"] if high_ambiguity else 1)
        return min(candidate_count, context["max_budget"], budget), "routine_bounded_budget"

    if name == "high_value_fetch":
        budget = context["high_ambiguity_budget"] if high_ambiguity else max(base_k, 3)
        return min(candidate_count, context["max_budget"], budget), "high_value_expand_budget"

    if name == "noisy_high_value_fetch":
        noisy = scenario_name in STRESS_SCENARIOS
        if noisy:
            return min(candidate_count, context["max_budget"]), "noisy_high_value_max_budget"
        budget = context["high_ambiguity_budget"] if high_ambiguity else max(base_k, 3)
        return min(candidate_count, context["max_budget"], budget), "noisy_high_value_expand_budget"

    raise RuntimeError(f"unknown context: {name}")


def checked_locations(rank: int | None, returned_k: int, stale: bool) -> int:
    if not stale:
        return 1
    if returned_k <= 0:
        return 3
    if rank is not None and rank <= returned_k:
        return rank
    return returned_k + 1


def utility(success: bool, cost: int, context: dict) -> float:
    value = context["success_reward"] if success else -context["failure_cost"]
    return value - context["check_cost"] * cost


def predict_one(
    row: dict,
    ranked: list[dict],
    context: dict,
    scenario_name: str,
    policy: str,
) -> dict:
    if not row["old_memory_is_stale"]:
        success = True
        rank = 1
        returned_k = 1
        reason = "trusted_low_motion_memory"
    else:
        rank = noise.target_rank(ranked)
        if policy == "fixed_uncertainty_topk_v0":
            returned_k = fixed_uncertainty_budget(row, ranked)
            reason = "fixed_uncertainty_budget"
        elif policy == "task_conditioned_budget_v0":
            returned_k, reason = conditioned_budget(row, ranked, context, scenario_name)
        else:
            raise RuntimeError(f"unknown policy: {policy}")
        success = rank is not None and rank <= returned_k
    cost = checked_locations(rank, returned_k, row["old_memory_is_stale"])
    return {
        "policy": policy,
        "task_context": context["name"],
        "decision_reason": reason,
        "target_rank": rank,
        "returned_location_count": returned_k,
        "checked_locations": cost,
        "search_success": success,
        "task_utility": round(utility(success, cost, context), 6),
        "attempt_spl_proxy": round((1.0 / cost) if success and cost > 0 else 0.0, 6),
        "uses_candidate_observation": bool(row["old_memory_is_stale"] and returned_k > 0),
    }


def run_scenario(
    scenario: dict,
    context: dict,
    query_rows: list[dict],
    candidates_by_uid: dict[str, list[dict]],
    seed: int,
) -> list[dict]:
    outputs = []
    for trial in range(scenario["trials"]):
        rng = random.Random(seed + scenario["seed_offset"] + trial)
        for row in query_rows:
            perturbed, target_observable, target_dropped, non_target_dropped = noise.perturb_candidates(
                row, candidates_by_uid.get(row["row_uid"], []), scenario, rng
            )
            ranked = noise.rank_by_score(perturbed)
            for policy in ["fixed_uncertainty_topk_v0", "task_conditioned_budget_v0"]:
                pred = predict_one(row, ranked, context, scenario["name"], policy)
                outputs.append(
                    {
                        "scenario": scenario["name"],
                        "trial": trial,
                        "row_uid": row["row_uid"],
                        "pair_uid": row["pair_uid"],
                        "object_label": row["object_label"],
                        "row_band": row["row_band"],
                        "old_memory_is_stale": row["old_memory_is_stale"],
                        "target_observable": target_observable,
                        "target_dropped": target_dropped > 0,
                        "non_target_dropped_count": non_target_dropped,
                        "perturbed_candidate_count": len(perturbed),
                        **pred,
                    }
                )
    return outputs


def summarize_subset(rows: list[dict], subset_name: str) -> dict:
    output = {}
    for context in CONTEXTS:
        context_rows = [row for row in rows if row["task_context"] == context["name"]]
        output[context["name"]] = {}
        for policy in ["fixed_uncertainty_topk_v0", "task_conditioned_budget_v0"]:
            items = [row for row in context_rows if row["policy"] == policy]
            observable = [row for row in items if row["target_observable"]]
            low_motion = [row for row in items if row["row_band"] == "low_motion_control"]
            output[context["name"]][policy] = {
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
                "mean_task_utility_all": mean([row["task_utility"] for row in items]),
                "mean_task_utility_when_target_observable": mean(
                    [row["task_utility"] for row in observable]
                ),
                "attempt_spl_proxy_all": mean([row["attempt_spl_proxy"] for row in items]),
                "mean_checked_locations_all": mean(
                    [float(row["checked_locations"]) for row in items]
                ),
                "mean_returned_location_count": mean(
                    [float(row["returned_location_count"]) for row in items]
                ),
                "low_motion_static_preserved_rate": safe_rate(
                    sum(
                        1
                        for row in low_motion
                        if row["search_success"] and not row["uses_candidate_observation"]
                    ),
                    len(low_motion),
                ),
            }
        fixed = output[context["name"]]["fixed_uncertainty_topk_v0"]
        conditioned = output[context["name"]]["task_conditioned_budget_v0"]
        output[context["name"]]["delta"] = {
            "mean_task_utility_all": round(
                conditioned["mean_task_utility_all"] - fixed["mean_task_utility_all"],
                6,
            ),
            "mean_task_utility_when_target_observable": round(
                conditioned["mean_task_utility_when_target_observable"]
                - fixed["mean_task_utility_when_target_observable"],
                6,
            ),
            "search_success_rate_when_target_observable": round(
                conditioned["search_success_rate_when_target_observable"]
                - fixed["search_success_rate_when_target_observable"],
                6,
            ),
        }
    return output


def summarize(predictions: list[dict]) -> dict:
    metrics = {}
    for scenario in noise.SCENARIOS:
        scenario_rows = [row for row in predictions if row["scenario"] == scenario["name"]]
        metrics[scenario["name"]] = {
            "all": summarize_subset(scenario_rows, "all"),
            "significant_moved": summarize_subset(
                [row for row in scenario_rows if row["row_band"] == "significant_moved"],
                "significant_moved",
            ),
            "low_motion_control": summarize_subset(
                [row for row in scenario_rows if row["row_band"] == "low_motion_control"],
                "low_motion_control",
            ),
        }
    return metrics


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
    routine_delta = primary["routine_fetch"]["delta"]
    high_value_delta = primary["high_value_fetch"]["delta"]
    stress = metrics["heavy_noise_stress"]["significant_moved"]["noisy_high_value_fetch"]
    low = metrics["ranking_noise_moderate"]["low_motion_control"]["routine_fetch"][
        "task_conditioned_budget_v0"
    ]
    gate_pass = (
        routine_delta["mean_task_utility_all"] >= 0.0
        and high_value_delta["mean_task_utility_all"] >= 0.10
        and high_value_delta["search_success_rate_when_target_observable"] >= 0.05
        and stress["delta"]["mean_task_utility_when_target_observable"] >= 0.50
        and stress["delta"]["search_success_rate_when_target_observable"] >= 0.25
        and low["low_motion_static_preserved_rate"] >= 0.95
    )
    return "conditioning_pass" if gate_pass else "fail"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=1701)
    args = parser.parse_args()

    query_rows = noise.load_jsonl(args.input_dir / "query_rows.jsonl")
    candidate_rows = noise.load_jsonl(args.input_dir / "candidate_rows.jsonl")
    input_coverage = noise.load_json(args.input_dir / "coverage.json")
    candidates_by_uid = noise.group_by_uid(candidate_rows)

    predictions = []
    for scenario in noise.SCENARIOS:
        for context in CONTEXTS:
            predictions.extend(
                run_scenario(scenario, context, query_rows, candidates_by_uid, args.seed)
            )
    metrics = summarize(predictions)
    coverage = {
        "input_dir": str(args.input_dir),
        "query_rows": len(query_rows),
        "validated_pair_count": input_coverage.get("validated_pair_count"),
        "significant_moved_rows": sum(
            1 for row in query_rows if row["row_band"] == "significant_moved"
        ),
        "low_motion_control_rows": sum(
            1 for row in query_rows if row["row_band"] == "low_motion_control"
        ),
        "contexts": CONTEXTS,
        "primary_scenario": "ranking_noise_moderate",
        "stress_scenario": "heavy_noise_stress",
        "uses_structured_task_context": True,
        "uses_natural_language_understanding": False,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "ranking_uses_persistent_cross_scan_ids": False,
        "not_supported_claims": [
            "natural-language intention understanding",
            "learned task policy",
            "real navigation SR/SPL",
            "deployable search policy",
            "real RGB-D/open-vocabulary perception robustness",
        ],
    }
    coverage["status"] = decide_status(metrics)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "predictions_sample.jsonl", prediction_sample(predictions))
    print(
        json.dumps(
            {
                "coverage": coverage,
                "primary_significant": metrics["ranking_noise_moderate"]["significant_moved"],
                "heavy_noise_significant": metrics["heavy_noise_stress"]["significant_moved"],
                "primary_low_motion": metrics["ranking_noise_moderate"]["low_motion_control"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
