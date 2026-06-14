#!/usr/bin/env python3
"""Run H001 budget baseline gate.

This hypothesis-stage gate checks whether task-conditioned candidate budgets
are doing more than simply returning a large fixed top-k set. It compares
`task_conditioned_budget_v0` against always-top-k and fixed uncertainty
baselines under the same controlled proposal-noise scenarios.
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
import run_task_context_gate as task


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "budget_baseline_gate"
POLICIES = [
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "task_conditioned_budget_v0",
]


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


def fixed_budget(policy: str, row: dict, ranked: list[dict], context: dict, scenario_name: str) -> tuple[int, str]:
    if not row["old_memory_is_stale"]:
        return 1, "trusted_low_motion_memory"
    candidate_count = len(ranked)
    if policy == "always_top1":
        return min(1, candidate_count), "always_top1"
    if policy == "always_top3":
        return min(3, candidate_count), "always_top3"
    if policy == "always_top5":
        return min(5, candidate_count), "always_top5"
    if policy == "fixed_uncertainty_topk_v0":
        return task.fixed_uncertainty_budget(row, ranked), "fixed_uncertainty_budget"
    if policy == "task_conditioned_budget_v0":
        return task.conditioned_budget(row, ranked, context, scenario_name)
    raise RuntimeError(f"unknown policy: {policy}")


def predict_one(row: dict, ranked: list[dict], context: dict, scenario_name: str, policy: str) -> dict:
    returned_k, reason = fixed_budget(policy, row, ranked, context, scenario_name)
    if not row["old_memory_is_stale"]:
        rank = 1
        success = True
    else:
        rank = noise.target_rank(ranked)
        success = rank is not None and rank <= returned_k
    checked = task.checked_locations(rank, returned_k, row["old_memory_is_stale"])
    utility = task.utility(success, checked, context)
    return {
        "policy": policy,
        "task_context": context["name"],
        "decision_reason": reason,
        "target_rank": rank,
        "returned_location_count": returned_k,
        "checked_locations": checked,
        "search_success": success,
        "task_utility": round(utility, 6),
        "attempt_spl_proxy": round((1.0 / checked) if success and checked > 0 else 0.0, 6),
        "uses_candidate_observation": bool(row["old_memory_is_stale"] and returned_k > 0),
    }


def run_scenario(
    scenario: dict,
    context: dict,
    query_rows: list[dict],
    candidates_by_uid: dict[str, list[dict]],
    seed: int,
) -> list[dict]:
    rows = []
    for trial in range(scenario["trials"]):
        rng = random.Random(seed + scenario["seed_offset"] + trial)
        for row in query_rows:
            perturbed, target_observable, target_dropped, non_target_dropped = noise.perturb_candidates(
                row, candidates_by_uid.get(row["row_uid"], []), scenario, rng
            )
            ranked = noise.rank_by_score(perturbed)
            for policy in POLICIES:
                pred = predict_one(row, ranked, context, scenario["name"], policy)
                rows.append(
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
    return rows


def summarize_policy(items: list[dict], subset_name: str) -> dict:
    observable = [row for row in items if row["target_observable"]]
    low_motion = [row for row in items if row["row_band"] == "low_motion_control"]
    success_obs = safe_rate(sum(1 for row in observable if row["search_success"]), len(observable))
    returned = mean([float(row["returned_location_count"]) for row in items])
    return {
        "subset": subset_name,
        "rows": len(items),
        "target_observable_rate": safe_rate(sum(1 for row in items if row["target_observable"]), len(items)),
        "search_success_rate_all": safe_rate(sum(1 for row in items if row["search_success"]), len(items)),
        "search_success_rate_when_target_observable": success_obs,
        "mean_task_utility_all": mean([row["task_utility"] for row in items]),
        "mean_task_utility_when_target_observable": mean([row["task_utility"] for row in observable]),
        "attempt_spl_proxy_all": mean([row["attempt_spl_proxy"] for row in items]),
        "mean_checked_locations_all": mean([float(row["checked_locations"]) for row in items]),
        "mean_returned_location_count": returned,
        "observable_success_per_returned_location": round(success_obs / returned, 6)
        if success_obs is not None and returned
        else None,
        "low_motion_static_preserved_rate": safe_rate(
            sum(1 for row in low_motion if row["search_success"] and not row["uses_candidate_observation"]),
            len(low_motion),
        ),
    }


def summarize_subset(rows: list[dict], subset_name: str) -> dict:
    output = {}
    for context in task.CONTEXTS:
        context_rows = [row for row in rows if row["task_context"] == context["name"]]
        output[context["name"]] = {}
        for policy in POLICIES:
            items = [row for row in context_rows if row["policy"] == policy]
            output[context["name"]][policy] = summarize_policy(items, subset_name)
        conditioned = output[context["name"]]["task_conditioned_budget_v0"]
        for baseline in ["always_top3", "always_top5", "fixed_uncertainty_topk_v0"]:
            base = output[context["name"]][baseline]
            output[context["name"]][f"delta_vs_{baseline}"] = {
                "mean_task_utility_all": round(
                    conditioned["mean_task_utility_all"] - base["mean_task_utility_all"],
                    6,
                ),
                "search_success_rate_when_target_observable": round(
                    conditioned["search_success_rate_when_target_observable"]
                    - base["search_success_rate_when_target_observable"],
                    6,
                ),
                "mean_returned_location_count": round(
                    conditioned["mean_returned_location_count"] - base["mean_returned_location_count"],
                    6,
                ),
                "observable_success_per_returned_location": round(
                    conditioned["observable_success_per_returned_location"]
                    - base["observable_success_per_returned_location"],
                    6,
                ),
            }
    return output


def summarize(predictions: list[dict]) -> dict:
    output = {}
    for scenario in noise.SCENARIOS:
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
        }
    return output


def prediction_sample(predictions: list[dict], limit: int = 2000) -> list[dict]:
    priority = [
        row
        for row in predictions
        if row["row_band"] == "significant_moved"
        and row["scenario"] in {"ranking_noise_moderate", "heavy_noise_stress"}
    ]
    return priority[:limit]


def decide_status(metrics: dict) -> str:
    primary = metrics["ranking_noise_moderate"]["significant_moved"]
    routine = primary["routine_fetch"]
    high_value = primary["high_value_fetch"]
    heavy = metrics["heavy_noise_stress"]["significant_moved"]["noisy_high_value_fetch"]
    low = metrics["ranking_noise_moderate"]["low_motion_control"]["routine_fetch"][
        "task_conditioned_budget_v0"
    ]
    routine_efficiency = (
        routine["delta_vs_always_top5"]["observable_success_per_returned_location"] >= 0.05
        and routine["delta_vs_fixed_uncertainty_topk_v0"]["mean_task_utility_all"] >= 0.0
    )
    high_value_near_top5 = (
        high_value["delta_vs_always_top5"]["mean_task_utility_all"] >= -0.02
        and high_value["delta_vs_fixed_uncertainty_topk_v0"]["mean_task_utility_all"] >= 0.10
    )
    heavy_near_top5 = (
        heavy["delta_vs_always_top5"]["mean_task_utility_all"] >= -0.02
        and heavy["delta_vs_fixed_uncertainty_topk_v0"]["mean_task_utility_all"] >= 0.50
    )
    low_ok = low["low_motion_static_preserved_rate"] >= 0.95
    return "budget_baseline_pass" if routine_efficiency and high_value_near_top5 and heavy_near_top5 and low_ok else "fail"


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
        for context in task.CONTEXTS:
            predictions.extend(run_scenario(scenario, context, query_rows, candidates_by_uid, args.seed))

    metrics = summarize(predictions)
    coverage = {
        "input_dir": str(args.input_dir),
        "query_rows": len(query_rows),
        "validated_pair_count": input_coverage.get("validated_pair_count"),
        "significant_moved_rows": sum(1 for row in query_rows if row["row_band"] == "significant_moved"),
        "low_motion_control_rows": sum(1 for row in query_rows if row["row_band"] == "low_motion_control"),
        "contexts": task.CONTEXTS,
        "policies": POLICIES,
        "primary_scenario": "ranking_noise_moderate",
        "stress_scenario": "heavy_noise_stress",
        "status_interpretation": "pass means task-conditioned budget is not just fixed top-k; it is budget-efficient in routine context and near always-top5 in high-value contexts",
        "uses_structured_task_context": True,
        "uses_natural_language_understanding": False,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
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
                "primary_routine": metrics["ranking_noise_moderate"]["significant_moved"]["routine_fetch"],
                "primary_high_value": metrics["ranking_noise_moderate"]["significant_moved"]["high_value_fetch"],
                "heavy_noisy_high_value": metrics["heavy_noise_stress"]["significant_moved"]["noisy_high_value_fetch"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
