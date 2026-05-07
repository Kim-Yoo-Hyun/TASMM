#!/usr/bin/env python3
"""Evaluate E002 policies with occupancy-grid A* path costs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M06_grid_path_policy_evaluation_v0"
EVAL_VERSION = "e002_grid_path_policy_eval_v0"
GRID_UNREACHABLE_ATTEMPT_COST_M = 1.0
OLD_LOCATION_FAILURE_COST_M = 1.0
POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "task_conditioned_budget_v0",
    "grid_path_aware_task_conditioned_budget_v0",
    "oracle_current_target",
]


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


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


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


def instance_sort_key(value: Any) -> Any:
    text = str(value)
    return int(text) if text.isdigit() else text


def old_location_success(query: dict[str, Any]) -> bool:
    return (
        float(query["scene_aligned_static_error_m"]) <= float(query["success_threshold_m"])
        and bool(query["target_grid_reachable"])
    )


def fixed_uncertainty_budget(query: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_candidate"
    if query["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"
    if query["ambiguity_band"] == "trivial_candidate":
        return 1, "fixed_uncertainty_trivial"
    if query["ambiguity_band"] == "rank_sensitive":
        return min(3, candidate_count), "fixed_uncertainty_rank_sensitive"
    return min(3, candidate_count), "fixed_uncertainty_high_ambiguity"


def task_conditioned_budget(query: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_candidate"
    if query["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"

    max_budget = int(query["max_candidate_budget"])
    high_ambiguity_budget = int(query["high_ambiguity_budget"])
    if query["task_context_id"] == "routine_fetch":
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "routine_trivial_candidate"
        if query["ambiguity_band"] == "high_ambiguity":
            return min(candidate_count, max_budget, high_ambiguity_budget), "routine_high_ambiguity_bounded"
        return min(candidate_count, max_budget, 3), "routine_rank_sensitive_budget"
    if query["task_context_id"] in {"high_value_fetch", "noisy_high_value_fetch"}:
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "high_value_trivial_candidate"
        return min(candidate_count, max_budget), "high_value_expand_budget"
    raise RuntimeError(f"unknown task_context_id: {query['task_context_id']}")


def ordered_candidates(candidates: list[dict[str, Any]], order_policy: str) -> list[dict[str, Any]]:
    if order_policy == "non_persistent_rank":
        return sorted(
            candidates,
            key=lambda row: (
                row["candidate_rank_non_persistent"],
                -row["candidate_score_non_persistent"],
                row["candidate_grid_path_cost_m"] is None,
                row["candidate_grid_path_cost_m"] if row["candidate_grid_path_cost_m"] is not None else 999999.0,
                instance_sort_key(row["candidate_instance_id"]),
            ),
        )
    if order_policy == "grid_path_aware":
        return sorted(
            candidates,
            key=lambda row: (
                row["candidate_grid_visit_order_index"] is None,
                row["candidate_grid_visit_order_index"] if row["candidate_grid_visit_order_index"] is not None else 999999,
                row["candidate_rank_non_persistent"],
                instance_sort_key(row["candidate_instance_id"]),
            ),
        )
    raise RuntimeError(f"unknown order_policy: {order_policy}")


def target_rank(ordered: list[dict[str, Any]]) -> int | None:
    for index, row in enumerate(ordered, start=1):
        if row["candidate_is_target"]:
            return index
    return None


def target_reachable_rank(ordered: list[dict[str, Any]]) -> int | None:
    for index, row in enumerate(ordered, start=1):
        if row["candidate_is_target"] and row["candidate_grid_reachable"]:
            return index
    return None


def grid_attempt_cost(ordered: list[dict[str, Any]], returned_k: int, stop_rank: int | None = None) -> float:
    if returned_k <= 0:
        return 0.0
    limit = min(returned_k, len(ordered))
    if stop_rank is not None:
        limit = min(limit, stop_rank)
    total = 0.0
    for row in ordered[:limit]:
        if row["candidate_grid_reachable"] and row["candidate_grid_path_cost_m"] is not None:
            total += float(row["candidate_grid_path_cost_m"])
        else:
            total += GRID_UNREACHABLE_ATTEMPT_COST_M
    return total


def grid_spl(success: bool, actual_cost_m: float, optimal_cost_m: float | None) -> float:
    if not success or optimal_cost_m is None:
        return 0.0
    if optimal_cost_m <= 1e-9 and actual_cost_m <= 1e-9:
        return 1.0
    denom = max(actual_cost_m, optimal_cost_m, 1e-9)
    return round(optimal_cost_m / denom, 6)


def grid_utility(success: bool, actual_cost_m: float, query: dict[str, Any]) -> float:
    reward = float(query["success_reward"]) if success else -float(query["failure_cost"])
    return round(reward - float(query["check_cost"]) * actual_cost_m, 6)


def prediction_payload(
    policy: str,
    query: dict[str, Any],
    success: bool,
    actual_cost_m: float,
    returned_k: int,
    target_rank_value: int | None,
    target_rank_in_returned: int | None,
    decision_reason: str,
    order_policy: str | None,
    old_location_checked: bool,
    returned_unreachable_count: int,
    grid_failure_type: str | None,
) -> dict[str, Any]:
    optimal_cost_m = query["target_grid_path_cost_m"] if query["target_grid_reachable"] else None
    stale_fp = bool(query["old_memory_is_stale"] and old_location_checked and not success)
    return {
        "eval_version": EVAL_VERSION,
        "row_uid": query["row_uid"],
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "metadata_split": query["metadata_split"],
        "task_context_id": query["task_context_id"],
        "policy": policy,
        "decision_reason": decision_reason,
        "order_policy": order_policy,
        "object_label": query["object_label"],
        "object_instance_id_ref": query["object_instance_id_ref"],
        "row_band": query["row_band"],
        "ambiguity_band": query["ambiguity_band"],
        "old_memory_is_stale": query["old_memory_is_stale"],
        "old_location_checked": old_location_checked,
        "old_location_dead_end": stale_fp,
        "target_grid_reachable": query["target_grid_reachable"],
        "target_rank": target_rank_value,
        "target_rank_in_returned": target_rank_in_returned,
        "returned_location_count": returned_k,
        "returned_unreachable_count": returned_unreachable_count,
        "grid_path_success": success,
        "grid_proxy_sr": success,
        "expected_grid_path_cost_m": round6(actual_cost_m),
        "optimal_grid_path_cost_m": round6(float(optimal_cost_m)) if optimal_cost_m is not None else None,
        "grid_attempt_spl_proxy": grid_spl(success, actual_cost_m, float(optimal_cost_m) if optimal_cost_m is not None else None),
        "grid_path_utility_proxy": grid_utility(success, actual_cost_m, query),
        "stale_old_location_fp": stale_fp,
        "low_motion_preserved": bool(
            query["row_band"] == "low_motion_control" and success and old_location_checked
        ),
        "grid_failure_type": grid_failure_type,
        "grid_path_cost_profile_id": query["grid_path_cost_profile_id"],
        "grid_path_cost_source": query["grid_path_cost_source"],
        "real_navigation_path_cost_ready": query["real_navigation_path_cost_ready"],
    }


def predict(policy: str, query: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if policy == "scene_aligned_static_map":
        success = old_location_success(query)
        if success:
            cost = float(query["target_grid_path_cost_m"] or 0.0)
            failure = None
        else:
            cost = OLD_LOCATION_FAILURE_COST_M
            failure = "target_grid_unreachable" if not query["target_grid_reachable"] else "static_map_localization_error"
        return prediction_payload(
            policy,
            query,
            success,
            cost,
            1,
            1 if success else None,
            1 if success else None,
            "return_old_memory_location",
            None,
            True,
            0,
            failure,
        )

    if policy == "oracle_current_target":
        success = bool(query["target_grid_reachable"])
        cost = float(query["target_grid_path_cost_m"] or 0.0) if success else OLD_LOCATION_FAILURE_COST_M
        return prediction_payload(
            policy,
            query,
            success,
            cost,
            1,
            1 if success else None,
            1 if success else None,
            "oracle_direct_current_target" if success else "oracle_target_grid_unreachable",
            "oracle",
            False,
            0 if success else 1,
            None if success else "target_grid_unreachable",
        )

    order_policy = "grid_path_aware" if policy == "grid_path_aware_task_conditioned_budget_v0" else "non_persistent_rank"
    ordered = ordered_candidates(candidates, order_policy)
    rank = target_rank(ordered)
    reachable_rank = target_reachable_rank(ordered)
    candidate_count = len(ordered)

    if policy in {"label_nearest_current_observation", "always_top1"}:
        returned_k, reason = min(1, candidate_count), "top1_current_observation"
    elif policy == "always_top3":
        returned_k, reason = min(3, candidate_count), "always_top3"
    elif policy == "always_top5":
        returned_k, reason = min(5, candidate_count), "always_top5"
    elif policy == "fixed_uncertainty_topk_v0":
        returned_k, reason = fixed_uncertainty_budget(query, candidate_count)
    elif policy == "task_conditioned_budget_v0":
        returned_k, reason = task_conditioned_budget(query, candidate_count)
    elif policy == "grid_path_aware_task_conditioned_budget_v0":
        returned_k, reason = task_conditioned_budget(query, candidate_count)
        if reason != "trusted_low_motion_memory":
            reason = f"grid_path_aware_{reason}"
    else:
        raise RuntimeError(f"unknown policy: {policy}")

    if reason == "trusted_low_motion_memory":
        success = old_location_success(query)
        cost = float(query["target_grid_path_cost_m"] or 0.0) if success else OLD_LOCATION_FAILURE_COST_M
        failure = None if success else "target_grid_unreachable" if not query["target_grid_reachable"] else "static_map_localization_error"
        return prediction_payload(
            policy,
            query,
            success,
            cost,
            1,
            1 if success else None,
            1 if success else None,
            reason,
            None,
            True,
            0,
            failure,
        )

    success = reachable_rank is not None and reachable_rank <= returned_k
    target_rank_in_returned = reachable_rank if success else None
    if success:
        cost = grid_attempt_cost(ordered, returned_k, reachable_rank)
    else:
        cost = grid_attempt_cost(ordered, returned_k)
    returned = ordered[: min(returned_k, len(ordered))]
    returned_unreachable_count = sum(1 for row in returned if not row["candidate_grid_reachable"])
    if success:
        failure = None
    elif not query["target_grid_reachable"]:
        failure = "target_grid_unreachable"
    elif returned_unreachable_count:
        failure = "returned_unreachable_candidate"
    elif returned_k == 0:
        failure = "no_candidate_returned"
    elif rank is None:
        failure = "target_missing_from_candidates"
    elif rank > returned_k:
        failure = "target_outside_returned_budget"
    else:
        failure = "unknown_grid_policy_failure"

    return prediction_payload(
        policy,
        query,
        success,
        cost,
        returned_k,
        rank,
        target_rank_in_returned,
        reason,
        order_policy,
        False,
        returned_unreachable_count,
        failure,
    )


def failure_type(row: dict[str, Any]) -> str:
    if row["grid_path_success"]:
        return "none"
    if row["stale_old_location_fp"]:
        return "stale_old_location_returned"
    if row["grid_failure_type"]:
        return row["grid_failure_type"]
    if row["old_location_checked"]:
        return "static_map_localization_error"
    return "unknown_failure"


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
                "target_grid_reachable": row["target_grid_reachable"],
                "target_rank": row["target_rank"],
                "returned_location_count": row["returned_location_count"],
                "returned_unreachable_count": row["returned_unreachable_count"],
                "expected_grid_path_cost_m": row["expected_grid_path_cost_m"],
                "next_test": "inspect occupancy-grid projection and disconnected components"
                if ftype in {"target_grid_unreachable", "returned_unreachable_candidate"}
                else "revise budget or grid-aware ordering"
                if ftype == "target_outside_returned_budget"
                else "review motion band and static threshold",
            }
        )
    return rows


def summarize_policy(items: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in items if row["old_memory_is_stale"]]
    low_motion = [row for row in items if row["row_band"] == "low_motion_control"]
    target_unreachable = [row for row in items if not row["target_grid_reachable"]]
    success_rate = safe_rate(sum(1 for row in items if row["grid_path_success"]), len(items))
    mean_cost = mean([float(row["expected_grid_path_cost_m"]) for row in items])
    return {
        "subset": subset,
        "rows": len(items),
        "grid_proxy_sr": success_rate,
        "mean_expected_grid_path_cost_m": mean_cost,
        "grid_attempt_spl_proxy": mean([float(row["grid_attempt_spl_proxy"]) for row in items]),
        "mean_grid_path_utility_proxy": mean([float(row["grid_path_utility_proxy"]) for row in items]),
        "stale_old_location_fp_rate": safe_rate(
            sum(1 for row in stale if row["stale_old_location_fp"]),
            len(stale),
        ),
        "low_motion_preservation_rate": safe_rate(
            sum(1 for row in low_motion if row["low_motion_preserved"]),
            len(low_motion),
        ),
        "target_grid_unreachable_rate": safe_rate(len(target_unreachable), len(items)),
        "returned_unreachable_rate": safe_rate(
            sum(1 for row in items if row["returned_unreachable_count"] > 0),
            len(items),
        ),
        "mean_returned_location_count": mean([float(row["returned_location_count"]) for row in items]),
        "success_per_meter": round(success_rate / mean_cost, 6)
        if success_rate is not None and mean_cost and mean_cost > 0
        else None,
    }


def delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 6)


def metric_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "grid_proxy_sr": delta(left["grid_proxy_sr"], right["grid_proxy_sr"]),
        "mean_expected_grid_path_cost_m": delta(left["mean_expected_grid_path_cost_m"], right["mean_expected_grid_path_cost_m"]),
        "grid_attempt_spl_proxy": delta(left["grid_attempt_spl_proxy"], right["grid_attempt_spl_proxy"]),
        "mean_grid_path_utility_proxy": delta(left["mean_grid_path_utility_proxy"], right["mean_grid_path_utility_proxy"]),
    }


def summarize_by_context(predictions: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for context in sorted({row["task_context_id"] for row in predictions}):
        context_rows = [row for row in predictions if row["task_context_id"] == context]
        output[context] = {}
        for policy in POLICIES:
            rows = [row for row in context_rows if row["policy"] == policy]
            output[context][policy] = summarize_policy(rows, subset)

        method = output[context]["task_conditioned_budget_v0"]
        grid_method = output[context]["grid_path_aware_task_conditioned_budget_v0"]
        for baseline in ["scene_aligned_static_map", "always_top1", "always_top3", "always_top5", "fixed_uncertainty_topk_v0", "oracle_current_target"]:
            base = output[context][baseline]
            output[context][f"delta_task_vs_{baseline}"] = metric_delta(method, base)
            output[context][f"delta_grid_aware_vs_{baseline}"] = metric_delta(grid_method, base)
        output[context]["delta_grid_aware_vs_task_conditioned_budget_v0"] = metric_delta(grid_method, method)
    return output


def summarize(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "all": summarize_by_context(predictions, "all"),
        "significant_moved": summarize_by_context(
            [row for row in predictions if row["row_band"] == "significant_moved"],
            "significant_moved",
        ),
        "low_motion_control": summarize_by_context(
            [row for row in predictions if row["row_band"] == "low_motion_control"],
            "low_motion_control",
        ),
        "mid_motion_review": summarize_by_context(
            [row for row in predictions if row["row_band"] == "mid_motion_review"],
            "mid_motion_review",
        ),
    }


def decide_status(metrics: dict[str, Any], coverage: dict[str, Any]) -> str:
    routine = metrics["significant_moved"]["routine_fetch"]
    task = routine["task_conditioned_budget_v0"]
    static = routine["scene_aligned_static_map"]
    low = metrics["low_motion_control"]["routine_fetch"]["task_conditioned_budget_v0"]
    oracle = routine["oracle_current_target"]
    if (
        coverage["denominator_preserved"]
        and coverage["grid_target_reachable_rows"] > 0
        and static["stale_old_location_fp_rate"] == 1.0
        and task["stale_old_location_fp_rate"] == 0.0
        and low["low_motion_preservation_rate"] is not None
        and oracle["grid_proxy_sr"] is not None
    ):
        return "grid_path_policy_eval_ready"
    return "review_needed"


def build_report(metrics: dict[str, Any], coverage: dict[str, Any], out_dir: Path) -> str:
    policies = [
        "scene_aligned_static_map",
        "always_top1",
        "always_top3",
        "always_top5",
        "fixed_uncertainty_topk_v0",
        "task_conditioned_budget_v0",
        "grid_path_aware_task_conditioned_budget_v0",
        "oracle_current_target",
    ]
    lines = [
        "# E002-M06 Grid Path Policy Evaluation",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Query rows: {coverage['query_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Grid path-cost profile: `{coverage['grid_path_cost_profile_id']}`",
        f"- Target grid reachable rows: {coverage['grid_target_reachable_rows']}",
        f"- Real navigation path-cost rows: {coverage['real_navigation_path_cost_ready_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved Rows",
        "",
    ]
    for context in ["routine_fetch", "high_value_fetch", "noisy_high_value_fetch"]:
        lines.extend(
            [
                f"### `{context}`",
                "",
                "| Policy | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Stale FP | Target unreachable |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for policy in policies:
            item = metrics["significant_moved"][context][policy]
            lines.append(
                "| `{policy}` | {sr} | {cost} | {spl} | {utility} | {stale} | {unreach} |".format(
                    policy=policy,
                    sr=item["grid_proxy_sr"],
                    cost=item["mean_expected_grid_path_cost_m"],
                    spl=item["grid_attempt_spl_proxy"],
                    utility=item["mean_grid_path_utility_proxy"],
                    stale=item["stale_old_location_fp_rate"],
                    unreach=item["target_grid_unreachable_rate"],
                )
            )
        lines.append("")

    lines.extend(
        [
            "## 논문 주장",
            "",
            "- E002-M06 supports policy comparison under `occupancy_grid_astar_v0` free-space path-cost proxy.",
            "- E002-M06 does not support real navigation `SR` / `SPL`, simulator execution, collision-aware robot planning, or deployable search policy claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The useful comparison is against `oracle_current_target`, because target-unreachable rows lower the grid upper bound.",
            "- Grid-aware ordering is now directly testable against semantic ranking under the same task-conditioned budget.",
            "- Rows with unreachable targets should be analyzed as grid/source limitations before using them as method failures.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E002-M06. Continue to failure/source analysis or E003 perception-noise expansion.",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "grid_query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "grid_candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions = []
    for query in query_rows:
        candidates = candidates_by_uid.get(query["row_uid"], [])
        for policy in POLICIES:
            predictions.append(predict(policy, query, candidates))

    failure_rows = build_failure_rows(predictions)
    metrics = summarize(predictions)
    coverage = {
        "status": "pending",
        "input_dir": str(args.input_dir),
        "grid_path_cost_profile_id": input_coverage.get("grid_path_cost_profile_id"),
        "grid_path_cost_source": input_coverage.get("grid_path_cost_source"),
        "query_rows": len(query_rows),
        "candidate_rows": len(candidate_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "row_band_counts": input_coverage.get("row_band_counts"),
        "denominator_preserved": input_coverage.get("denominator_preserved") is True
        and len(query_rows) == input_coverage.get("query_rows")
        and len(candidate_rows) == input_coverage.get("candidate_rows"),
        "grid_target_reachable_rows": input_coverage.get("target_grid_reachable_rows", 0),
        "grid_target_unreachable_rows": input_coverage.get("target_grid_unreachable_rows", 0),
        "real_navigation_path_cost_ready_rows": input_coverage.get("real_navigation_path_cost_ready_rows"),
        "uses_grid_path_cost_proxy": True,
        "uses_real_navigation": False,
        "uses_simulator_execution": False,
        "uses_collision_aware_robot_planning": False,
        "failure_type_counts": dict(sorted(Counter(row["failure_type"] for row in failure_rows).items())),
        "policy_failure_counts": dict(sorted(Counter(row["policy"] for row in failure_rows).items())),
        "unsupported_claims": [
            "real navigation SR/SPL",
            "collision-aware robot planning",
            "simulator execution",
            "deployable search policy",
            "RGB-D/open-vocabulary perception robustness",
        ],
        "outputs": {
            "predictions": str(args.out_dir / "predictions.jsonl"),
            "failure_rows": str(args.out_dir / "failure_rows.jsonl"),
            "metrics": str(args.out_dir / "metrics.json"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }
    coverage["status"] = decide_status(metrics, coverage)

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
                "routine_significant_task": metrics["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"],
                "routine_significant_grid_aware": metrics["significant_moved"]["routine_fetch"]["grid_path_aware_task_conditioned_budget_v0"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
