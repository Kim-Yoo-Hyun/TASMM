#!/usr/bin/env python3
"""Evaluate E001 clean baseline policies.

This is the first main-experiment evaluation for the semantic-pair proxy task.
It uses annotation-level current candidates and structured task context only;
it does not evaluate navigation, RGB-D perception, open-vocabulary perception,
or natural-language intention understanding.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M03_baseline_evaluation_v0"
EVAL_VERSION = "e001_baseline_eval_v0"
POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "task_conditioned_budget_v0",
    "oracle_current_target",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
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


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            row["candidate_rank_non_persistent"],
            -row["candidate_score_non_persistent"],
            row["candidate_euclidean_cost_from_old_m"],
            int(row["candidate_instance_id"]) if str(row["candidate_instance_id"]).isdigit() else row["candidate_instance_id"],
        ),
    )


def target_rank(ranked: list[dict[str, Any]]) -> int | None:
    for index, row in enumerate(ranked, start=1):
        if row["candidate_is_target"]:
            return index
    return None


def checked_locations(success: bool, rank: int | None, returned_k: int, returns_old_location: bool) -> int:
    if returns_old_location:
        return 1 if success else 2
    if returned_k <= 0:
        return 1
    if success and rank is not None:
        return rank
    return returned_k + 1


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / expected_cost, 6)


def utility(success: bool, expected_cost: int, row: dict[str, Any]) -> float:
    reward = float(row["success_reward"]) if success else -float(row["failure_cost"])
    return round(reward - float(row["check_cost"]) * expected_cost, 6)


def fixed_uncertainty_budget(row: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_candidate"
    if row["ambiguity_band"] == "trivial_candidate":
        return 1, "fixed_uncertainty_trivial"
    if row["ambiguity_band"] == "rank_sensitive":
        return min(3, candidate_count), "fixed_uncertainty_rank_sensitive"
    return min(3, candidate_count), "fixed_uncertainty_high_ambiguity"


def task_conditioned_budget(row: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_candidate_reobserve"
    if row["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"

    max_budget = int(row["max_candidate_budget"])
    high_ambiguity_budget = int(row["high_ambiguity_budget"])
    if row["task_context_id"] == "routine_fetch":
        if row["ambiguity_band"] == "trivial_candidate":
            return 1, "routine_trivial_candidate"
        if row["ambiguity_band"] == "high_ambiguity":
            return min(candidate_count, max_budget, high_ambiguity_budget), "routine_high_ambiguity_bounded"
        return min(candidate_count, max_budget, 3), "routine_rank_sensitive_budget"

    if row["task_context_id"] in {"high_value_fetch", "noisy_high_value_fetch"}:
        if row["ambiguity_band"] == "trivial_candidate":
            return 1, "high_value_trivial_candidate"
        return min(candidate_count, max_budget), "high_value_expand_budget"

    raise RuntimeError(f"unknown task_context_id: {row['task_context_id']}")


def predict_policy(policy: str, row: dict[str, Any], ranked: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_count = len(ranked)
    rank = target_rank(ranked)
    returns_old = False
    uses_candidate_observation = False
    returned_k = 0
    decision_reason = policy

    if policy == "scene_aligned_static_map":
        returns_old = True
        success = float(row["scene_aligned_static_error_m"]) <= float(row["success_threshold_m"])
        returned_k = 1
        rank_in_returned = 1 if success else None
    elif policy == "oracle_current_target":
        return prediction_payload(
            policy,
            row,
            True,
            rank,
            1,
            1,
            1,
            False,
            False,
            "oracle_current_target",
        )
    else:
        uses_candidate_observation = True
        if policy in {"label_nearest_current_observation", "always_top1"}:
            returned_k = min(1, candidate_count)
            decision_reason = "top1_current_observation"
        elif policy == "always_top3":
            returned_k = min(3, candidate_count)
            decision_reason = "always_top3"
        elif policy == "always_top5":
            returned_k = min(5, candidate_count)
            decision_reason = "always_top5"
        elif policy == "fixed_uncertainty_topk_v0":
            if row["expected_memory_state"] == "trusted_or_low_motion":
                returns_old = True
                uses_candidate_observation = False
                returned_k = 1
                success = float(row["scene_aligned_static_error_m"]) <= float(row["success_threshold_m"])
                rank_in_returned = 1 if success else None
                decision_reason = "trusted_low_motion_memory"
                expected_cost = checked_locations(success, rank, returned_k, returns_old)
                return prediction_payload(
                    policy,
                    row,
                    success,
                    rank,
                    rank_in_returned,
                    returned_k,
                    expected_cost,
                    returns_old,
                    uses_candidate_observation,
                    decision_reason,
                )
            returned_k, decision_reason = fixed_uncertainty_budget(row, candidate_count)
        elif policy == "task_conditioned_budget_v0":
            returned_k, decision_reason = task_conditioned_budget(row, candidate_count)
            if decision_reason == "trusted_low_motion_memory":
                returns_old = True
                uses_candidate_observation = False
                returned_k = 1
                success = float(row["scene_aligned_static_error_m"]) <= float(row["success_threshold_m"])
                rank_in_returned = 1 if success else None
                expected_cost = checked_locations(success, rank, returned_k, returns_old)
                return prediction_payload(
                    policy,
                    row,
                    success,
                    rank,
                    rank_in_returned,
                    returned_k,
                    expected_cost,
                    returns_old,
                    uses_candidate_observation,
                    decision_reason,
                )
        else:
            raise RuntimeError(f"unknown policy: {policy}")

        success = rank is not None and rank <= returned_k
        rank_in_returned = rank if success else None

    expected_cost = checked_locations(success, rank, returned_k, returns_old)
    return prediction_payload(
        policy,
        row,
        success,
        rank,
        rank_in_returned,
        returned_k,
        expected_cost,
        returns_old,
        uses_candidate_observation,
        decision_reason,
    )


def prediction_payload(
    policy: str,
    row: dict[str, Any],
    success: bool,
    target_rank_value: int | None,
    rank_in_returned: int | None,
    returned_k: int,
    expected_cost: int,
    returns_old: bool,
    uses_candidate_observation: bool,
    decision_reason: str,
) -> dict[str, Any]:
    stale_old_fp = bool(row["old_memory_is_stale"] and returns_old and not success)
    return {
        "eval_version": EVAL_VERSION,
        "row_uid": row["row_uid"],
        "base_row_uid": row["base_row_uid"],
        "pair_uid": row["pair_uid"],
        "metadata_split": row["metadata_split"],
        "task_context_id": row["task_context_id"],
        "policy": policy,
        "decision_reason": decision_reason,
        "object_label": row["object_label"],
        "object_instance_id_ref": row["object_instance_id_ref"],
        "row_band": row["row_band"],
        "ambiguity_band": row["ambiguity_band"],
        "old_memory_is_stale": row["old_memory_is_stale"],
        "returns_old_location": returns_old,
        "uses_candidate_observation": uses_candidate_observation,
        "target_rank": target_rank_value,
        "target_rank_in_returned": rank_in_returned,
        "returned_location_count": returned_k,
        "search_success": success,
        "proxy_sr": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "task_utility": utility(success, expected_cost, row),
        "stale_old_location_fp": stale_old_fp,
        "low_motion_preserved": bool(
            row["row_band"] == "low_motion_control" and success and returns_old
        ),
        "success_threshold_m": row["success_threshold_m"],
        "scene_aligned_static_error_m": row["scene_aligned_static_error_m"],
        "scene_aligned_static_planar_error_m": row["scene_aligned_static_planar_error_m"],
        "same_label_candidate_count": row["same_label_candidate_count"],
        "path_cost_ready": row["path_cost_ready"],
        "observation_source": row["observation_source"],
        "intent_condition_source": row["intent_condition_source"],
    }


def failure_type(row: dict[str, Any]) -> str:
    if row["search_success"]:
        return "none"
    if row["stale_old_location_fp"]:
        return "stale_old_location_returned"
    if row["returns_old_location"]:
        return "static_map_localization_error"
    if row["returned_location_count"] == 0:
        return "no_candidate_returned"
    if row["target_rank"] is None:
        return "target_missing_from_candidates"
    if row["target_rank"] > row["returned_location_count"]:
        return "target_outside_returned_budget"
    return "unknown_failure"


def summarize_policy(items: list[dict[str, Any]], subset_name: str) -> dict[str, Any]:
    stale_items = [row for row in items if row["old_memory_is_stale"]]
    low_motion = [row for row in items if row["row_band"] == "low_motion_control"]
    returned_mean = mean([float(row["returned_location_count"]) for row in items])
    success_rate = safe_rate(sum(1 for row in items if row["search_success"]), len(items))
    return {
        "subset": subset_name,
        "rows": len(items),
        "proxy_sr": success_rate,
        "recall_at_returned_k": success_rate,
        "stale_old_location_fp_rate": safe_rate(
            sum(1 for row in stale_items if row["stale_old_location_fp"]),
            len(stale_items),
        ),
        "low_motion_preservation_rate": safe_rate(
            sum(1 for row in low_motion if row["low_motion_preserved"]),
            len(low_motion),
        ),
        "mean_expected_search_cost": mean([float(row["expected_search_cost"]) for row in items]),
        "attempt_spl_proxy": mean([float(row["attempt_spl_proxy"]) for row in items]),
        "mean_task_utility": mean([float(row["task_utility"]) for row in items]),
        "mean_returned_location_count": returned_mean,
        "success_per_returned_location": round(success_rate / returned_mean, 6)
        if success_rate is not None and returned_mean
        else None,
    }


def summarize_by_context_and_policy(predictions: list[dict[str, Any]], subset_name: str) -> dict[str, Any]:
    contexts = sorted({row["task_context_id"] for row in predictions})
    output: dict[str, Any] = {}
    for context in contexts:
        context_rows = [row for row in predictions if row["task_context_id"] == context]
        output[context] = {}
        for policy in POLICIES:
            policy_rows = [row for row in context_rows if row["policy"] == policy]
            output[context][policy] = summarize_policy(policy_rows, subset_name)
        method = output[context]["task_conditioned_budget_v0"]
        for baseline in ["scene_aligned_static_map", "always_top1", "always_top3", "always_top5", "fixed_uncertainty_topk_v0"]:
            base = output[context][baseline]
            output[context][f"delta_vs_{baseline}"] = {
                "proxy_sr": round_or_none(
                    None
                    if method["proxy_sr"] is None or base["proxy_sr"] is None
                    else method["proxy_sr"] - base["proxy_sr"]
                ),
                "mean_expected_search_cost": round_or_none(
                    None
                    if method["mean_expected_search_cost"] is None
                    or base["mean_expected_search_cost"] is None
                    else method["mean_expected_search_cost"] - base["mean_expected_search_cost"]
                ),
                "attempt_spl_proxy": round_or_none(
                    None
                    if method["attempt_spl_proxy"] is None or base["attempt_spl_proxy"] is None
                    else method["attempt_spl_proxy"] - base["attempt_spl_proxy"]
                ),
                "mean_task_utility": round_or_none(
                    None
                    if method["mean_task_utility"] is None or base["mean_task_utility"] is None
                    else method["mean_task_utility"] - base["mean_task_utility"]
                ),
            }
    return output


def summarize(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "all": summarize_by_context_and_policy(predictions, "all"),
        "significant_moved": summarize_by_context_and_policy(
            [row for row in predictions if row["row_band"] == "significant_moved"],
            "significant_moved",
        ),
        "low_motion_control": summarize_by_context_and_policy(
            [row for row in predictions if row["row_band"] == "low_motion_control"],
            "low_motion_control",
        ),
        "mid_motion_review": summarize_by_context_and_policy(
            [row for row in predictions if row["row_band"] == "mid_motion_review"],
            "mid_motion_review",
        ),
    }


def build_failure_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        ftype = failure_type(row)
        if ftype == "none":
            continue
        rows.append(
            {
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "task_context_id": row["task_context_id"],
                "policy": row["policy"],
                "object_label": row["object_label"],
                "row_band": row["row_band"],
                "ambiguity_band": row["ambiguity_band"],
                "failure_type": ftype,
                "suspected_cause": "stale memory trusted"
                if ftype == "stale_old_location_returned"
                else "old memory location outside success threshold"
                if ftype == "static_map_localization_error"
                else "candidate budget too small"
                if ftype == "target_outside_returned_budget"
                else "candidate source missing target"
                if ftype == "target_missing_from_candidates"
                else "no candidate budget returned",
                "next_test": "E002 path-cost old-location dead-end validation"
                if ftype == "stale_old_location_returned"
                else "check whether mid-motion rows should force re-observation"
                if ftype == "static_map_localization_error"
                else "increase task-conditioned budget or improve candidate ranking",
                "target_rank": row["target_rank"],
                "returned_location_count": row["returned_location_count"],
                "expected_search_cost": row["expected_search_cost"],
            }
        )
    return rows


def build_report(metrics: dict[str, Any], coverage: dict[str, Any], out_dir: Path) -> str:
    primary_contexts = ["routine_fetch", "high_value_fetch", "noisy_high_value_fetch"]
    table_policies = [
        "scene_aligned_static_map",
        "label_nearest_current_observation",
        "always_top1",
        "always_top3",
        "always_top5",
        "fixed_uncertainty_topk_v0",
        "task_conditioned_budget_v0",
        "oracle_current_target",
    ]
    lines = [
        "# E001-M03 Baseline Evaluation",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Query rows: {coverage['query_rows']}",
        f"- Base query rows: {coverage['base_query_rows']}",
        f"- Candidate rows: {coverage['candidate_rows']}",
        f"- Predictions: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Policies: {', '.join(f'`{item}`' for item in POLICIES)}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved Rows",
        "",
    ]
    for context in primary_contexts:
        lines.extend(
            [
                f"### `{context}`",
                "",
                "| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for policy in table_policies:
            item = metrics["significant_moved"][context][policy]
            lines.append(
                "| `{policy}` | {sr} | {cost} | {spl} | {utility} | {stale} |".format(
                    policy=policy,
                    sr=item["proxy_sr"],
                    cost=item["mean_expected_search_cost"],
                    spl=item["attempt_spl_proxy"],
                    utility=item["mean_task_utility"],
                    stale=item["stale_old_location_fp_rate"],
                )
            )
        lines.append("")

    lines.extend(
        [
            "## 논문 주장",
            "",
            "- This artifact supports clean annotation-level E001 baseline comparison for semantic-pair dynamic object search proxy tasks.",
            "- This artifact does not support real navigation `SR` / `SPL`, RGB-D perception robustness, open-vocabulary perception robustness, learned policy, or natural-language intention understanding.",
            "",
            "## 에이전트 추론",
            "",
            "- `task_conditioned_budget_v0` should be judged against both fixed top-k and oracle upper bound, not only against the static map.",
            "- Structured task context is used as a controlled variable so E004 can later test whether memory trust changes are useful before adding LLM parsing.",
            "- E002 should reuse `expected_search_cost` and replace candidate-count cost with path/search cost.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E001-M03. Continue to E001 failure analysis or E002 path-cost bridge after reviewing baseline table.",
            "",
            "## Outputs",
            "",
            "- `predictions.jsonl`",
            "- `failure_rows.jsonl`",
            "- `metrics.json`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def decide_status(metrics: dict[str, Any]) -> str:
    routine = metrics["significant_moved"]["routine_fetch"]
    high_value = metrics["significant_moved"]["high_value_fetch"]
    low_motion = metrics["low_motion_control"]["routine_fetch"]["task_conditioned_budget_v0"]
    method_routine = routine["task_conditioned_budget_v0"]
    method_high = high_value["task_conditioned_budget_v0"]
    static = routine["scene_aligned_static_map"]
    top5 = high_value["always_top5"]
    oracle = high_value["oracle_current_target"]

    suppresses_stale = (
        method_routine["stale_old_location_fp_rate"] == 0.0
        and static["stale_old_location_fp_rate"] == 1.0
    )
    high_value_near_top5 = method_high["proxy_sr"] == top5["proxy_sr"]
    below_oracle = method_high["proxy_sr"] <= oracle["proxy_sr"]
    low_motion_ok = low_motion["low_motion_preservation_rate"] is not None and low_motion["low_motion_preservation_rate"] >= 0.95
    return "baseline_ready" if suppresses_stale and high_value_near_top5 and below_oracle and low_motion_ok else "review_needed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions: list[dict[str, Any]] = []
    for row in query_rows:
        ranked = rank_candidates(candidates_by_uid.get(row["row_uid"], []))
        for policy in POLICIES:
            predictions.append(predict_policy(policy, row, ranked))

    failure_rows = build_failure_rows(predictions)
    metrics = summarize(predictions)
    failure_counts = Counter(row["failure_type"] for row in failure_rows)
    coverage = {
        "eval_version": EVAL_VERSION,
        "input_dir": str(args.input_dir),
        "query_rows": len(query_rows),
        "base_query_rows": input_coverage.get("base_query_rows"),
        "candidate_rows": len(candidate_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "validated_pair_count": input_coverage.get("validated_pair_count"),
        "base_row_band_counts": input_coverage.get("base_row_band_counts"),
        "task_context_counts": input_coverage.get("task_context_counts"),
        "policies": POLICIES,
        "failure_type_counts": dict(sorted(failure_counts.items())),
        "uses_structured_task_context": True,
        "uses_natural_language_understanding": False,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "uses_annotation_level_current_observation": True,
        "path_cost_ready": False,
        "outputs": {
            "predictions": str(args.out_dir / "predictions.jsonl"),
            "failure_rows": str(args.out_dir / "failure_rows.jsonl"),
            "metrics": str(args.out_dir / "metrics.json"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }
    coverage["status"] = decide_status(metrics)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(metrics, coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "query_rows": coverage["query_rows"],
                "prediction_rows": coverage["prediction_rows"],
                "failure_rows": coverage["failure_rows"],
                "routine_significant": metrics["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"],
                "high_value_significant": metrics["significant_moved"]["high_value_fetch"]["task_conditioned_budget_v0"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
