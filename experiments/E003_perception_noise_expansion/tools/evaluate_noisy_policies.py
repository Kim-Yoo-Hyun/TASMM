#!/usr/bin/env python3
"""Evaluate E003 policies on annotation-proxy noisy candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M02_annotation_proxy_noise_v0"
DEFAULT_GRID_DIR = (
    REPO_ROOT
    / "experiments"
    / "E002_path_cost_bridge"
    / "artifacts"
    / "E002-M05_occupancy_grid_astar_v0"
)
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M03_noisy_policy_eval_v0"
EVAL_VERSION = "e003_noisy_policy_eval_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
STRESS_PROFILE = "annotation_score_jitter_v0"
POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "task_conditioned_budget_v0",
    "reachable_first_task_conditioned_budget_v0",
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
    return round6(sum(values) / len(values))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def profile_ids(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({row["proposal_noise_profile_id"] for row in rows})


def instance_key(value: Any) -> Any:
    text = str(value)
    return int(text) if text.isdigit() else text


def grid_reachability_index(grid_candidate_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    output = {}
    for row in grid_candidate_rows:
        output[(row["row_uid"], str(row["candidate_instance_id"]))] = row
    return output


def attach_grid_fields(
    candidate_rows: list[dict[str, Any]],
    grid_index: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in candidate_rows:
        output = dict(row)
        original_row_uid = output.get("original_row_uid", output["row_uid"])
        grid = grid_index.get((original_row_uid, str(output["candidate_instance_id"])))
        output["candidate_grid_signal_available"] = grid is not None
        output["candidate_grid_reachable"] = bool(grid.get("candidate_grid_reachable")) if grid else None
        output["candidate_grid_path_cost_m"] = grid.get("candidate_grid_path_cost_m") if grid else None
        output["candidate_grid_failure_type"] = grid.get("candidate_grid_failure_type") if grid else None
        rows.append(output)
    return rows


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            row["candidate_rank_non_persistent"],
            -float(row["candidate_score_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )


def reachable_first_rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            row.get("candidate_grid_reachable") is False,
            row.get("candidate_grid_reachable") is None,
            row["candidate_rank_non_persistent"],
            -float(row["candidate_score_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )


def target_rank(ranked: list[dict[str, Any]]) -> int | None:
    for index, row in enumerate(ranked, start=1):
        if row["candidate_is_target"]:
            return index
    return None


def checked_locations(success: bool, rank: int | None, returned_k: int, returns_old: bool) -> int:
    if returns_old:
        return 1 if success else 2
    if returned_k <= 0:
        return 1
    if success and rank is not None:
        return rank
    return returned_k + 1


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round6(1.0 / expected_cost) or 0.0


def utility(success: bool, expected_cost: int, row: dict[str, Any]) -> float:
    reward = float(row["success_reward"]) if success else -float(row["failure_cost"])
    return round6(reward - float(row["check_cost"]) * expected_cost) or 0.0


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
    ranking_policy: str | None,
    target_retained: bool,
    candidate_grid_signal_available: bool,
    returned_unreachable_count: int,
) -> dict[str, Any]:
    stale_old_fp = bool(row["old_memory_is_stale"] and returns_old and not success)
    return {
        "eval_version": EVAL_VERSION,
        "row_uid": row["row_uid"],
        "original_row_uid": row.get("original_row_uid"),
        "base_row_uid": row["base_row_uid"],
        "pair_uid": row["pair_uid"],
        "metadata_split": row["metadata_split"],
        "task_context_id": row["task_context_id"],
        "proposal_noise_profile_id": row["proposal_noise_profile_id"],
        "proposal_noise_role": row.get("proposal_noise_role"),
        "proposal_noise_seed": row.get("proposal_noise_seed"),
        "policy": policy,
        "decision_reason": decision_reason,
        "ranking_policy": ranking_policy,
        "object_label": row["object_label"],
        "object_instance_id_ref": row["object_instance_id_ref"],
        "row_band": row["row_band"],
        "ambiguity_band": row["ambiguity_band"],
        "old_memory_is_stale": row["old_memory_is_stale"],
        "returns_old_location": returns_old,
        "uses_candidate_observation": uses_candidate_observation,
        "target_retained": target_retained,
        "target_dropped_by_noise": bool(row.get("target_dropped_by_noise", False)),
        "target_rank": target_rank_value,
        "target_rank_in_returned": rank_in_returned,
        "returned_location_count": returned_k,
        "returned_unreachable_count": returned_unreachable_count,
        "candidate_grid_signal_available": candidate_grid_signal_available,
        "search_success": success,
        "proxy_sr": success,
        "expected_search_cost": expected_cost,
        "attempt_spl_proxy": attempt_spl(success, expected_cost),
        "task_utility": utility(success, expected_cost, row),
        "stale_old_location_fp": stale_old_fp,
        "low_motion_preserved": bool(row["row_band"] == "low_motion_control" and success and returns_old),
        "success_threshold_m": row["success_threshold_m"],
        "scene_aligned_static_error_m": row["scene_aligned_static_error_m"],
        "scene_aligned_static_planar_error_m": row["scene_aligned_static_planar_error_m"],
        "same_label_candidate_count": row["same_label_candidate_count"],
        "path_cost_ready": row["path_cost_ready"],
        "observation_source": row["observation_source"],
        "perception_profile_id": row.get("perception_profile_id"),
        "intent_condition_source": row["intent_condition_source"],
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
    }


def predict_policy(policy: str, row: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    standard_ranked = rank_candidates(candidates)
    ranked = (
        reachable_first_rank_candidates(candidates)
        if policy == "reachable_first_task_conditioned_budget_v0"
        else standard_ranked
    )
    candidate_count = len(ranked)
    rank = target_rank(ranked)
    target_retained = rank is not None
    candidate_grid_signal_available = any(
        item.get("candidate_grid_signal_available") is True for item in candidates
    )
    returns_old = False
    uses_candidate_observation = False
    returned_k = 0
    decision_reason = policy
    ranking_policy = "reachable_first_semantic_rank" if policy == "reachable_first_task_conditioned_budget_v0" else "noisy_semantic_rank"

    if policy == "scene_aligned_static_map":
        returns_old = True
        success = float(row["scene_aligned_static_error_m"]) <= float(row["success_threshold_m"])
        returned_k = 1
        rank_in_returned = 1 if success else None
        ranking_policy = None
    elif policy == "oracle_current_target":
        success = target_retained
        return prediction_payload(
            policy,
            row,
            success,
            rank,
            1 if success else None,
            1,
            1,
            False,
            False,
            "oracle_current_target" if success else "oracle_target_dropped",
            "oracle",
            target_retained,
            candidate_grid_signal_available,
            0,
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
                    "trusted_low_motion_memory",
                    None,
                    target_retained,
                    candidate_grid_signal_available,
                    0,
                )
            returned_k, decision_reason = fixed_uncertainty_budget(row, candidate_count)
        elif policy in {"task_conditioned_budget_v0", "reachable_first_task_conditioned_budget_v0"}:
            returned_k, decision_reason = task_conditioned_budget(row, candidate_count)
            if policy == "reachable_first_task_conditioned_budget_v0":
                decision_reason = f"reachable_first_{decision_reason}"
            if decision_reason.endswith("trusted_low_motion_memory"):
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
                    None,
                    target_retained,
                    candidate_grid_signal_available,
                    0,
                )
        else:
            raise RuntimeError(f"unknown policy: {policy}")

        success = rank is not None and rank <= returned_k
        rank_in_returned = rank if success else None

    expected_cost = checked_locations(success, rank, returned_k, returns_old)
    returned = ranked[: min(returned_k, len(ranked))] if not returns_old else []
    returned_unreachable_count = sum(1 for item in returned if item.get("candidate_grid_reachable") is False)
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
        ranking_policy,
        target_retained,
        candidate_grid_signal_available,
        returned_unreachable_count,
    )


def failure_type(row: dict[str, Any]) -> str:
    if row["search_success"]:
        return "none"
    if not row["target_retained"]:
        return "target_dropped_by_noise"
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


def build_failure_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        ftype = failure_type(row)
        if ftype == "none":
            continue
        rows.append(
            {
                "row_uid": row["row_uid"],
                "original_row_uid": row["original_row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "task_context_id": row["task_context_id"],
                "proposal_noise_profile_id": row["proposal_noise_profile_id"],
                "policy": row["policy"],
                "object_label": row["object_label"],
                "row_band": row["row_band"],
                "ambiguity_band": row["ambiguity_band"],
                "failure_type": ftype,
                "target_rank": row["target_rank"],
                "returned_location_count": row["returned_location_count"],
                "expected_search_cost": row["expected_search_cost"],
                "returned_unreachable_count": row["returned_unreachable_count"],
                "suspected_cause": "ranking noise moved target outside returned budget"
                if ftype == "target_outside_returned_budget"
                else "stale memory trusted"
                if ftype == "stale_old_location_returned"
                else "old memory location outside success threshold"
                if ftype == "static_map_localization_error"
                else "proposal noise removed target"
                if ftype == "target_dropped_by_noise"
                else "review noisy policy behavior",
                "next_test": "compare clean vs score-jitter profile and hard labels",
            }
        )
    return rows


def summarize_policy(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    success_rate = safe_rate(sum(1 for row in rows if row["search_success"]), len(rows))
    returned_mean = mean([float(row["returned_location_count"]) for row in rows])
    return {
        "subset": subset,
        "rows": len(rows),
        "target_retained_rate": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
        "proxy_sr": success_rate,
        "recall_at_returned_k": success_rate,
        "stale_old_location_fp_rate": safe_rate(
            sum(1 for row in stale if row["stale_old_location_fp"]),
            len(stale),
        ),
        "low_motion_preservation_rate": safe_rate(
            sum(1 for row in low_motion if row["low_motion_preserved"]),
            len(low_motion),
        ),
        "mean_expected_search_cost": mean([float(row["expected_search_cost"]) for row in rows]),
        "attempt_spl_proxy": mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "mean_task_utility": mean([float(row["task_utility"]) for row in rows]),
        "mean_returned_location_count": returned_mean,
        "returned_unreachable_rate": safe_rate(
            sum(1 for row in rows if row["returned_unreachable_count"] > 0),
            len(rows),
        ),
        "success_per_returned_location": round6(success_rate / returned_mean)
        if success_rate is not None and returned_mean
        else None,
    }


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def summarize_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for subset in ["all", "significant_moved", "mid_motion_review", "low_motion_control"]:
        subset_predictions = subset_rows(rows, subset)
        output[subset] = {}
        for context in sorted({row["task_context_id"] for row in subset_predictions}):
            context_rows = [row for row in subset_predictions if row["task_context_id"] == context]
            output[subset][context] = {}
            for policy in POLICIES:
                policy_rows = [row for row in context_rows if row["policy"] == policy]
                output[subset][context][policy] = summarize_policy(policy_rows, subset)
    return output


def delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round6(left - right)


def metric_delta(stress: dict[str, Any], clean: dict[str, Any]) -> dict[str, Any]:
    return {
        "proxy_sr": delta(stress["proxy_sr"], clean["proxy_sr"]),
        "mean_expected_search_cost": delta(
            stress["mean_expected_search_cost"],
            clean["mean_expected_search_cost"],
        ),
        "attempt_spl_proxy": delta(stress["attempt_spl_proxy"], clean["attempt_spl_proxy"]),
        "mean_task_utility": delta(stress["mean_task_utility"], clean["mean_task_utility"]),
        "mean_returned_location_count": delta(
            stress["mean_returned_location_count"],
            clean["mean_returned_location_count"],
        ),
    }


def build_robustness_delta(metrics: dict[str, Any]) -> dict[str, Any]:
    if REFERENCE_PROFILE not in metrics or STRESS_PROFILE not in metrics:
        return {}
    output: dict[str, Any] = {}
    for subset in metrics[REFERENCE_PROFILE]:
        output[subset] = {}
        for context in metrics[REFERENCE_PROFILE][subset]:
            output[subset][context] = {}
            for policy in POLICIES:
                clean = metrics[REFERENCE_PROFILE][subset][context][policy]
                stress = metrics[STRESS_PROFILE][subset][context][policy]
                output[subset][context][policy] = metric_delta(stress, clean)
    return output


def build_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    output = {
        profile: summarize_profile([row for row in predictions if row["proposal_noise_profile_id"] == profile])
        for profile in profile_ids(predictions)
    }
    output["robustness_delta_score_jitter_minus_clean"] = build_robustness_delta(output)
    return output


def decide_status(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    if coverage["prediction_rows"] != coverage["noisy_query_rows"] * len(POLICIES):
        return "review_needed"
    clean = metrics[REFERENCE_PROFILE]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"]
    stress = metrics[STRESS_PROFILE]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"]
    if clean["target_retained_rate"] == 1.0 and stress["target_retained_rate"] == 1.0:
        return "noisy_policy_eval_ready"
    return "review_needed"


def build_report(metrics: dict[str, Any], coverage: dict[str, Any], out_dir: Path) -> str:
    table_policies = [
        "scene_aligned_static_map",
        "always_top1",
        "always_top3",
        "always_top5",
        "fixed_uncertainty_topk_v0",
        "task_conditioned_budget_v0",
        "reachable_first_task_conditioned_budget_v0",
        "oracle_current_target",
    ]
    lines = [
        "# E003-M03 Noisy Policy Evaluation",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Profiles: {', '.join(f'`{item}`' for item in coverage['profiles'])}",
        f"- Candidate grid signal rows: {coverage['candidate_grid_signal_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch`",
        "",
    ]
    for profile in [REFERENCE_PROFILE, STRESS_PROFILE]:
        lines.extend(
            [
                f"### `{profile}`",
                "",
                "| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for policy in table_policies:
            item = metrics[profile]["significant_moved"]["routine_fetch"][policy]
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

    delta_table = metrics["robustness_delta_score_jitter_minus_clean"]["significant_moved"]["routine_fetch"]
    lines.extend(
        [
            "## Robustness Delta",
            "",
            "`annotation_score_jitter_v0` minus `clean_annotation_oracle_v0` for significant moved `routine_fetch`:",
            "",
            "| Policy | Delta proxy `SR` | Delta cost | Delta `AttemptSPL` | Delta utility |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for policy in table_policies:
        item = delta_table[policy]
        lines.append(
            f"| `{policy}` | {item['proxy_sr']} | {item['mean_expected_search_cost']} | {item['attempt_spl_proxy']} | {item['mean_task_utility']} |"
        )

    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M03 supports evaluating controlled annotation-proxy ranking-noise robustness.",
            "- E003-M03 does not support real RGB-D or open-vocabulary perception robustness.",
            "- E003-M03 does not support real navigation `SR` / `SPL`.",
            "",
            "## 에이전트 추론",
            "",
            "- Since target presence is preserved, metric changes isolate rank/candidate-order robustness rather than proposal recall.",
            "- `reachable_first_task_conditioned_budget_v0` uses E002 grid reachability only as an auxiliary candidate-order signal, not as real navigation execution.",
            "- E003-M04 should summarize robustness boundaries before adding target dropout or false-positive profiles.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M03. Continue to E003-M04 robustness/failure analysis.",
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
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "noisy_query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "noisy_candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    grid_candidate_path = args.grid_dir / "grid_candidate_rows.jsonl"
    grid_candidate_rows = load_jsonl(grid_candidate_path) if grid_candidate_path.exists() else []
    grid_index = grid_reachability_index(grid_candidate_rows)
    candidate_rows = attach_grid_fields(candidate_rows, grid_index)
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions: list[dict[str, Any]] = []
    for row in query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        for policy in POLICIES:
            predictions.append(predict_policy(policy, row, candidates))

    failure_rows = build_failure_rows(predictions)
    metrics = build_metrics(predictions)
    coverage = {
        "eval_version": EVAL_VERSION,
        "status": "pending",
        "input_dir": str(args.input_dir),
        "grid_dir": str(args.grid_dir),
        "profiles": input_coverage["profiles"],
        "noisy_query_rows": len(query_rows),
        "noisy_candidate_rows": len(candidate_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "policies": POLICIES,
        "candidate_grid_signal_rows": sum(1 for row in candidate_rows if row["candidate_grid_signal_available"]),
        "uses_annotation_proxy_noise": True,
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "uses_real_navigation": False,
        "target_drop_profiles_included": input_coverage.get("target_drop_profiles_included", False),
        "failure_type_counts": counter_dict(Counter(row["failure_type"] for row in failure_rows)),
        "outputs": {
            "predictions": str(args.out_dir / "predictions.jsonl"),
            "failure_rows": str(args.out_dir / "failure_rows.jsonl"),
            "metrics": str(args.out_dir / "metrics.json"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }
    coverage["status"] = decide_status(coverage, metrics)

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
                "prediction_rows": coverage["prediction_rows"],
                "failure_rows": coverage["failure_rows"],
                "routine_significant_clean_task": metrics[REFERENCE_PROFILE]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"],
                "routine_significant_jitter_task": metrics[STRESS_PROFILE]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"],
                "routine_significant_jitter_reachable_first": metrics[STRESS_PROFILE]["significant_moved"]["routine_fetch"]["reachable_first_task_conditioned_budget_v0"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
