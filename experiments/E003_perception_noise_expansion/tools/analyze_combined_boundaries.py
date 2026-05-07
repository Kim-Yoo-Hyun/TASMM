#!/usr/bin/env python3
"""Analyze E003 annotation combined-noise failure boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M13_annotation_combined_moderate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M14_combined_noise_failure_boundary_v0"
ANALYSIS_VERSION = "e003_combined_noise_failure_boundary_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
COMBINED_PROFILE = "annotation_combined_moderate_v0"
PRIMARY_POLICIES = [
    "task_conditioned_budget_v0",
    "reachable_first_task_conditioned_budget_v0",
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
    return round6(num / den)


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return round6(sum(clean) / len(clean))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def as_bool(value: Any) -> bool:
    return bool(value)


def index_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_uid"]: row for row in manifest_rows}


def clean_prediction_index(predictions: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    output = {}
    for row in predictions:
        if row["proposal_noise_profile_id"] == REFERENCE_PROFILE:
            output[(row["original_row_uid"], row["policy"])] = row
    return output


def combined_group(manifest: dict[str, Any]) -> str:
    if manifest["target_dropped_by_noise"]:
        return "target_dropped"
    if manifest["target_jitter_exceeds_success_threshold"]:
        return "centroid_localization_exceeded"
    if manifest["target_pushed_down_by_false_positive"]:
        return "false_positive_target_pushed_down"
    if manifest["target_rank_changed_by_combined_noise"] or manifest["target_rank_delta"] not in {0, None}:
        return "rank_budget_shift_no_push"
    if int(manifest["false_positive_added_count"]) > 0:
        return "false_positive_added_no_push"
    if int(manifest["candidate_rows_dropped"]) > 0 or int(manifest["rank_changed_candidate_rows"]) > 0:
        return "candidate_dropout_or_score_shift"
    return "stable_combined_control"


def transition_label(clean_success: bool, stress_success: bool, prefix: str) -> str:
    if clean_success and stress_success:
        return f"stable_{prefix}_success"
    if clean_success and not stress_success:
        return f"combined_{prefix}_regression"
    if not clean_success and stress_success:
        return f"combined_{prefix}_improvement"
    return f"stable_{prefix}_failure"


def rank_delta(clean: dict[str, Any], stress: dict[str, Any]) -> int | None:
    if clean["target_rank"] is None or stress["target_rank"] is None:
        return None
    return int(stress["target_rank"]) - int(clean["target_rank"])


def target_outside_budget(row: dict[str, Any]) -> bool:
    target_rank = row["target_rank"]
    returned_count = row["returned_location_count"]
    return target_rank is not None and int(target_rank) > int(returned_count)


def boundary_type(
    clean: dict[str, Any],
    stress: dict[str, Any],
    manifest: dict[str, Any],
    identity_transition: str,
    localization_transition: str,
    group: str,
) -> str:
    stress_identity = bool(stress["search_success"])
    stress_localized = bool(stress["localization_success"])
    failure_type = str(stress.get("localization_failure_type") or "none")

    if group == "target_dropped":
        if stress_localized:
            return "target_dropped_static_memory_or_control_success"
        return "target_dropped_proposal_recall_ceiling"

    if failure_type == "target_centroid_jitter_exceeds_threshold":
        if stress_identity and not stress_localized:
            return "identity_success_over_jitter_localization_failure"
        if identity_transition == "combined_identity_regression":
            return "over_jitter_with_identity_regression"
        return "over_jitter_persistent_localization_failure"

    if identity_transition == "combined_identity_regression":
        if stress["target_rank"] is None:
            return "target_missing_identity_regression"
        if target_outside_budget(stress):
            if group == "false_positive_target_pushed_down":
                return "false_positive_push_budget_identity_regression"
            if group == "rank_budget_shift_no_push":
                return "rank_shift_budget_identity_regression"
            return "budget_identity_regression"
        if int(stress["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
            return "reachability_identity_regression"
        return "combined_identity_policy_regression"

    if identity_transition == "combined_identity_improvement":
        if group == "false_positive_target_pushed_down":
            return "false_positive_push_unexpected_identity_improvement"
        if group == "rank_budget_shift_no_push":
            return "rank_shift_identity_improvement"
        return "combined_identity_improvement"

    if localization_transition == "combined_localization_regression":
        if stress_identity and not stress_localized:
            return "identity_success_localization_regression"
        if target_outside_budget(stress):
            return "budget_localization_regression"
        return "combined_localization_policy_regression"

    if localization_transition == "combined_localization_improvement":
        return "combined_localization_improvement"

    if localization_transition == "stable_localization_failure":
        if stress["stale_old_location_fp"]:
            return "stale_static_localization_failure"
        if target_outside_budget(stress):
            if group == "false_positive_target_pushed_down":
                return "persistent_false_positive_push_budget_boundary"
            return "persistent_budget_localization_boundary"
        if group == "false_positive_target_pushed_down":
            return "persistent_false_positive_push_boundary"
        return "persistent_localization_failure"

    if group == "false_positive_target_pushed_down":
        return "false_positive_push_survived"
    if group == "rank_budget_shift_no_push":
        return "rank_shift_survived"
    if group == "false_positive_added_no_push":
        return "false_positive_added_survived"
    if group == "candidate_dropout_or_score_shift":
        return "candidate_dropout_or_score_shift_survived"
    return "stable_combined_success"


def build_boundary_rows(
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_row_uid = index_manifest(manifest_rows)
    clean_index = clean_prediction_index(predictions)
    rows = []
    for stress in predictions:
        if stress["proposal_noise_profile_id"] != COMBINED_PROFILE:
            continue
        clean = clean_index[(stress["original_row_uid"], stress["policy"])]
        manifest = manifest_by_row_uid[stress["row_uid"]]
        group = combined_group(manifest)
        identity_transition = transition_label(
            bool(clean["search_success"]),
            bool(stress["search_success"]),
            "identity",
        )
        localization_transition = transition_label(
            bool(clean["localization_success"]),
            bool(stress["localization_success"]),
            "localization",
        )
        delta_rank = rank_delta(clean, stress)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": stress["original_row_uid"],
                "row_uid": stress["row_uid"],
                "base_row_uid": stress["base_row_uid"],
                "pair_uid": stress["pair_uid"],
                "proposal_noise_seed": stress["proposal_noise_seed"],
                "policy": stress["policy"],
                "task_context_id": stress["task_context_id"],
                "row_band": stress["row_band"],
                "object_label": stress["object_label"],
                "ambiguity_band": stress["ambiguity_band"],
                "old_memory_is_stale": stress["old_memory_is_stale"],
                "combined_group": group,
                "target_retained": bool(manifest["target_retained"]),
                "target_dropped_by_noise": bool(manifest["target_dropped_by_noise"]),
                "target_drop_forced_retained": bool(manifest["target_drop_forced_retained"]),
                "false_positive_added_count": int(manifest["false_positive_added_count"]),
                "false_positive_available_count": int(manifest["false_positive_available_count"]),
                "false_positive_above_target_count": int(manifest["false_positive_above_target_count"]),
                "target_pushed_down_by_false_positive": bool(
                    manifest["target_pushed_down_by_false_positive"]
                ),
                "same_label_false_positive_count": int(manifest["same_label_false_positive_count"]),
                "semantic_group_false_positive_count": int(
                    manifest["semantic_group_false_positive_count"]
                ),
                "fallback_false_positive_count": int(manifest["fallback_false_positive_count"]),
                "candidate_rows_original": int(manifest["candidate_rows_original"]),
                "candidate_rows_after_dropout": int(manifest["candidate_rows_after_dropout"]),
                "candidate_rows_noisy": int(manifest["candidate_rows_noisy"]),
                "candidate_rows_added": int(manifest["candidate_rows_added"]),
                "candidate_rows_dropped": int(manifest["candidate_rows_dropped"]),
                "dropped_non_target_candidate_rows": int(manifest["dropped_non_target_candidate_rows"]),
                "rank_changed_candidate_rows": int(manifest["rank_changed_candidate_rows"]),
                "target_jitter_exceeds_success_threshold": bool(
                    manifest["target_jitter_exceeds_success_threshold"]
                ),
                "target_rank_changed_by_centroid_jitter": bool(
                    manifest["target_rank_changed_by_centroid_jitter"]
                ),
                "target_rank_changed_by_combined_noise": bool(
                    manifest["target_rank_changed_by_combined_noise"]
                ),
                "target_centroid_jitter_m": stress["target_centroid_jitter_m"],
                "target_planar_jitter_m": stress["target_planar_jitter_m"],
                "mean_candidate_centroid_jitter_m": manifest["mean_candidate_centroid_jitter_m"],
                "mean_candidate_planar_jitter_m": manifest["mean_candidate_planar_jitter_m"],
                "max_candidate_centroid_jitter_m": manifest["max_candidate_centroid_jitter_m"],
                "clean_identity_success": bool(clean["search_success"]),
                "combined_identity_success": bool(stress["search_success"]),
                "clean_localization_success": bool(clean["localization_success"]),
                "combined_localization_success": bool(stress["localization_success"]),
                "combined_localization_failure_type": stress["localization_failure_type"],
                "identity_success_localization_failure": bool(stress["search_success"])
                and not bool(stress["localization_success"]),
                "identity_transition": identity_transition,
                "localization_transition": localization_transition,
                "boundary_type": boundary_type(
                    clean,
                    stress,
                    manifest,
                    identity_transition,
                    localization_transition,
                    group,
                ),
                "clean_target_rank": clean["target_rank"],
                "combined_target_rank": stress["target_rank"],
                "target_rank_delta": delta_rank,
                "manifest_target_rank_delta": manifest["target_rank_delta"],
                "target_rank_original": manifest["target_rank_original"],
                "target_rank_noisy": manifest["target_rank_noisy"],
                "clean_returned_location_count": clean["returned_location_count"],
                "combined_returned_location_count": stress["returned_location_count"],
                "returned_location_count_delta": int(stress["returned_location_count"])
                - int(clean["returned_location_count"]),
                "clean_expected_search_cost": clean["expected_search_cost"],
                "combined_expected_search_cost": stress["expected_search_cost"],
                "expected_search_cost_delta": round6(
                    float(stress["expected_search_cost"]) - float(clean["expected_search_cost"])
                ),
                "clean_attempt_spl_proxy": clean["attempt_spl_proxy"],
                "combined_attempt_spl_proxy": stress["attempt_spl_proxy"],
                "attempt_spl_delta": round6(
                    float(stress["attempt_spl_proxy"]) - float(clean["attempt_spl_proxy"])
                ),
                "clean_task_utility": clean["task_utility"],
                "combined_task_utility": stress["task_utility"],
                "task_utility_delta": round6(float(stress["task_utility"]) - float(clean["task_utility"])),
                "clean_returned_unreachable_count": clean["returned_unreachable_count"],
                "combined_returned_unreachable_count": stress["returned_unreachable_count"],
                "returned_unreachable_count_delta": int(stress["returned_unreachable_count"])
                - int(clean["returned_unreachable_count"]),
                "grid_path_recomputed_for_centroid_jitter": stress[
                    "grid_path_recomputed_for_centroid_jitter"
                ],
                "uses_real_rgbd_perception": stress["uses_real_rgbd_perception"],
                "uses_open_vocab_perception": stress["uses_open_vocab_perception"],
                "uses_real_navigation": bool(stress.get("uses_real_navigation", False)),
            }
        )
    return rows


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "clean_identity_sr": None,
            "combined_identity_sr": None,
            "identity_sr_delta": None,
            "clean_localization_sr": None,
            "combined_localization_sr": None,
            "localization_sr_delta": None,
            "combined_identity_localization_gap": None,
            "identity_success_localization_failure_rows": 0,
            "identity_success_localization_failure_rate": None,
            "combined_identity_regression_rows": 0,
            "combined_localization_regression_rows": 0,
            "target_dropped_rate": None,
            "false_positive_added_rate": None,
            "target_pushed_down_rate": None,
            "target_rank_changed_rate": None,
            "target_jitter_exceeds_threshold_rate": None,
            "target_rank_better_rows": 0,
            "target_rank_worse_rows": 0,
            "target_rank_same_rows": 0,
            "mean_target_rank_delta": None,
            "mean_false_positive_added_count": None,
            "mean_false_positive_above_target_count": None,
            "mean_candidate_rows_dropped": None,
            "mean_candidate_rows_added": None,
            "mean_target_centroid_jitter_m": None,
            "mean_target_planar_jitter_m": None,
            "mean_expected_search_cost_delta": None,
            "mean_attempt_spl_delta": None,
            "mean_task_utility_delta": None,
            "returned_unreachable_event_delta": 0,
            "identity_transition_counts": {},
            "localization_transition_counts": {},
            "boundary_counts": {},
            "combined_group_counts": {},
        }
    clean_identity = sum(1 for row in rows if row["clean_identity_success"])
    combined_identity = sum(1 for row in rows if row["combined_identity_success"])
    clean_localization = sum(1 for row in rows if row["clean_localization_success"])
    combined_localization = sum(1 for row in rows if row["combined_localization_success"])
    identity_transition_counts = Counter(row["identity_transition"] for row in rows)
    localization_transition_counts = Counter(row["localization_transition"] for row in rows)
    boundary_counts = Counter(row["boundary_type"] for row in rows)
    group_counts = Counter(row["combined_group"] for row in rows)
    rank_deltas = [as_float(row["target_rank_delta"]) for row in rows if row["target_rank_delta"] is not None]
    return {
        "rows": len(rows),
        "clean_identity_sr": safe_rate(clean_identity, len(rows)),
        "combined_identity_sr": safe_rate(combined_identity, len(rows)),
        "identity_sr_delta": round6((combined_identity - clean_identity) / len(rows)),
        "clean_localization_sr": safe_rate(clean_localization, len(rows)),
        "combined_localization_sr": safe_rate(combined_localization, len(rows)),
        "localization_sr_delta": round6((combined_localization - clean_localization) / len(rows)),
        "clean_identity_localization_gap": round6((clean_identity - clean_localization) / len(rows)),
        "combined_identity_localization_gap": round6((combined_identity - combined_localization) / len(rows)),
        "identity_success_localization_failure_rows": sum(
            1 for row in rows if row["identity_success_localization_failure"]
        ),
        "identity_success_localization_failure_rate": safe_rate(
            sum(1 for row in rows if row["identity_success_localization_failure"]),
            len(rows),
        ),
        "combined_identity_regression_rows": identity_transition_counts["combined_identity_regression"],
        "combined_identity_improvement_rows": identity_transition_counts["combined_identity_improvement"],
        "combined_localization_regression_rows": localization_transition_counts[
            "combined_localization_regression"
        ],
        "combined_localization_improvement_rows": localization_transition_counts[
            "combined_localization_improvement"
        ],
        "target_dropped_rows": sum(1 for row in rows if row["target_dropped_by_noise"]),
        "target_dropped_rate": safe_rate(sum(1 for row in rows if row["target_dropped_by_noise"]), len(rows)),
        "false_positive_added_rows": sum(1 for row in rows if int(row["false_positive_added_count"]) > 0),
        "false_positive_added_rate": safe_rate(
            sum(1 for row in rows if int(row["false_positive_added_count"]) > 0),
            len(rows),
        ),
        "target_pushed_down_rows": sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
        "target_pushed_down_rate": safe_rate(
            sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
            len(rows),
        ),
        "target_rank_changed_rows": sum(1 for row in rows if row["target_rank_changed_by_combined_noise"]),
        "target_rank_changed_rate": safe_rate(
            sum(1 for row in rows if row["target_rank_changed_by_combined_noise"]),
            len(rows),
        ),
        "target_jitter_exceeds_threshold_rows": sum(
            1 for row in rows if row["target_jitter_exceeds_success_threshold"]
        ),
        "target_jitter_exceeds_threshold_rate": safe_rate(
            sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"]),
            len(rows),
        ),
        "target_rank_better_rows": sum(
            1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] < 0
        ),
        "target_rank_worse_rows": sum(
            1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] > 0
        ),
        "target_rank_same_rows": sum(1 for row in rows if row["target_rank_delta"] == 0),
        "mean_target_rank_delta": mean(rank_deltas),
        "mean_false_positive_added_count": mean([as_float(row["false_positive_added_count"]) for row in rows]),
        "mean_false_positive_above_target_count": mean(
            [as_float(row["false_positive_above_target_count"]) for row in rows]
        ),
        "mean_candidate_rows_dropped": mean([as_float(row["candidate_rows_dropped"]) for row in rows]),
        "mean_candidate_rows_added": mean([as_float(row["candidate_rows_added"]) for row in rows]),
        "mean_target_centroid_jitter_m": mean([as_float(row["target_centroid_jitter_m"]) for row in rows]),
        "mean_target_planar_jitter_m": mean([as_float(row["target_planar_jitter_m"]) for row in rows]),
        "mean_expected_search_cost_delta": mean([as_float(row["expected_search_cost_delta"]) for row in rows]),
        "mean_attempt_spl_delta": mean([as_float(row["attempt_spl_delta"]) for row in rows]),
        "mean_task_utility_delta": mean([as_float(row["task_utility_delta"]) for row in rows]),
        "returned_unreachable_event_delta": sum(
            1 for row in rows if int(row["combined_returned_unreachable_count"]) > 0
        )
        - sum(1 for row in rows if int(row["clean_returned_unreachable_count"]) > 0),
        "identity_transition_counts": counter_dict(identity_transition_counts),
        "localization_transition_counts": counter_dict(localization_transition_counts),
        "boundary_counts": counter_dict(boundary_counts),
        "combined_group_counts": counter_dict(group_counts),
    }


def build_manifest_summary(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stress_rows = [
        row for row in manifest_rows if row["proposal_noise_profile_id"] == COMBINED_PROFILE
    ]
    target_dropped_rows = [row for row in stress_rows if row["target_dropped_by_noise"]]
    fp_added_rows = [row for row in stress_rows if int(row["false_positive_added_count"]) > 0]
    pushed_rows = [row for row in stress_rows if row["target_pushed_down_by_false_positive"]]
    rank_changed_rows = [row for row in stress_rows if row["target_rank_changed_by_combined_noise"]]
    jitter_rows = [row for row in stress_rows if row["target_jitter_exceeds_success_threshold"]]
    return {
        "stress_query_rows": len(stress_rows),
        "target_retained_rows": sum(1 for row in stress_rows if row["target_retained"]),
        "target_retained_rate": safe_rate(sum(1 for row in stress_rows if row["target_retained"]), len(stress_rows)),
        "target_dropped_rows": len(target_dropped_rows),
        "target_dropped_rate": safe_rate(len(target_dropped_rows), len(stress_rows)),
        "target_drop_forced_retained_rows": sum(1 for row in stress_rows if row["target_drop_forced_retained"]),
        "false_positive_added_rows": len(fp_added_rows),
        "false_positive_added_rate": safe_rate(len(fp_added_rows), len(stress_rows)),
        "target_pushed_down_rows": len(pushed_rows),
        "target_pushed_down_rate": safe_rate(len(pushed_rows), len(stress_rows)),
        "target_rank_changed_rows": len(rank_changed_rows),
        "target_rank_changed_rate": safe_rate(len(rank_changed_rows), len(stress_rows)),
        "target_jitter_exceeds_threshold_rows": len(jitter_rows),
        "target_jitter_exceeds_threshold_rate": safe_rate(len(jitter_rows), len(stress_rows)),
        "rank_changed_candidate_rows": sum(int(row["rank_changed_candidate_rows"]) for row in stress_rows),
        "candidate_rows_dropped": sum(int(row["candidate_rows_dropped"]) for row in stress_rows),
        "candidate_rows_added": sum(int(row["candidate_rows_added"]) for row in stress_rows),
        "same_label_false_positive_count": sum(int(row["same_label_false_positive_count"]) for row in stress_rows),
        "semantic_group_false_positive_count": sum(
            int(row["semantic_group_false_positive_count"]) for row in stress_rows
        ),
        "fallback_false_positive_count": sum(int(row["fallback_false_positive_count"]) for row in stress_rows),
        "mean_candidate_rows_dropped": mean([as_float(row["candidate_rows_dropped"]) for row in stress_rows]),
        "mean_candidate_rows_added": mean([as_float(row["candidate_rows_added"]) for row in stress_rows]),
        "mean_target_centroid_jitter_m": mean([as_float(row["target_centroid_jitter_m"]) for row in stress_rows]),
        "mean_target_planar_jitter_m": mean([as_float(row["target_planar_jitter_m"]) for row in stress_rows]),
        "mean_candidate_centroid_jitter_m": mean(
            [as_float(row["mean_candidate_centroid_jitter_m"]) for row in stress_rows]
        ),
        "mean_candidate_planar_jitter_m": mean(
            [as_float(row["mean_candidate_planar_jitter_m"]) for row in stress_rows]
        ),
        "grid_path_recomputed_for_centroid_jitter": any(
            bool(row["grid_path_recomputed_for_centroid_jitter"]) for row in stress_rows
        ),
        "combined_group_counts": counter_dict(Counter(combined_group(row) for row in stress_rows)),
    }


def compare_reachable_vs_task_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_row_uid: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row["policy"] in PRIMARY_POLICIES:
            by_row_uid[row["row_uid"]][row["policy"]] = row
    paired = [
        item
        for item in by_row_uid.values()
        if "task_conditioned_budget_v0" in item
        and "reachable_first_task_conditioned_budget_v0" in item
    ]
    if not paired:
        return {
            "rows": 0,
            "task_combined_identity_sr": None,
            "reachable_combined_identity_sr": None,
            "identity_sr_delta_reachable_minus_task": None,
            "task_combined_localization_sr": None,
            "reachable_combined_localization_sr": None,
            "localization_sr_delta_reachable_minus_task": None,
        }
    task_identity = sum(1 for item in paired if item["task_conditioned_budget_v0"]["combined_identity_success"])
    reachable_identity = sum(
        1 for item in paired if item["reachable_first_task_conditioned_budget_v0"]["combined_identity_success"]
    )
    task_localization = sum(
        1 for item in paired if item["task_conditioned_budget_v0"]["combined_localization_success"]
    )
    reachable_localization = sum(
        1 for item in paired if item["reachable_first_task_conditioned_budget_v0"]["combined_localization_success"]
    )
    task_unreachable_events = sum(
        1
        for item in paired
        if int(item["task_conditioned_budget_v0"]["combined_returned_unreachable_count"]) > 0
    )
    reachable_unreachable_events = sum(
        1
        for item in paired
        if int(item["reachable_first_task_conditioned_budget_v0"]["combined_returned_unreachable_count"]) > 0
    )
    return {
        "rows": len(paired),
        "task_combined_identity_sr": safe_rate(task_identity, len(paired)),
        "reachable_combined_identity_sr": safe_rate(reachable_identity, len(paired)),
        "identity_sr_delta_reachable_minus_task": round6((reachable_identity - task_identity) / len(paired)),
        "task_combined_localization_sr": safe_rate(task_localization, len(paired)),
        "reachable_combined_localization_sr": safe_rate(reachable_localization, len(paired)),
        "localization_sr_delta_reachable_minus_task": round6(
            (reachable_localization - task_localization) / len(paired)
        ),
        "reachable_identity_success_gain_rows": sum(
            1
            for item in paired
            if item["reachable_first_task_conditioned_budget_v0"]["combined_identity_success"]
            and not item["task_conditioned_budget_v0"]["combined_identity_success"]
        ),
        "reachable_identity_success_loss_rows": sum(
            1
            for item in paired
            if item["task_conditioned_budget_v0"]["combined_identity_success"]
            and not item["reachable_first_task_conditioned_budget_v0"]["combined_identity_success"]
        ),
        "reachable_localization_success_gain_rows": sum(
            1
            for item in paired
            if item["reachable_first_task_conditioned_budget_v0"]["combined_localization_success"]
            and not item["task_conditioned_budget_v0"]["combined_localization_success"]
        ),
        "reachable_localization_success_loss_rows": sum(
            1
            for item in paired
            if item["task_conditioned_budget_v0"]["combined_localization_success"]
            and not item["reachable_first_task_conditioned_budget_v0"]["combined_localization_success"]
        ),
        "task_unreachable_event_rate": safe_rate(task_unreachable_events, len(paired)),
        "reachable_unreachable_event_rate": safe_rate(reachable_unreachable_events, len(paired)),
        "unreachable_event_delta_reachable_minus_task": round6(
            (reachable_unreachable_events - task_unreachable_events) / len(paired)
        ),
        "mean_expected_search_cost_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["combined_expected_search_cost"])
                - float(item["task_conditioned_budget_v0"]["combined_expected_search_cost"])
                for item in paired
            ]
        ),
        "mean_task_utility_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["combined_task_utility"])
                - float(item["task_conditioned_budget_v0"]["combined_task_utility"])
                for item in paired
            ]
        ),
    }


def build_reachable_vs_task_summary(boundary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"all": compare_reachable_vs_task_subset(boundary_rows)}
    for group in sorted({row["combined_group"] for row in boundary_rows}):
        rows = [row for row in boundary_rows if row["combined_group"] == group]
        output[f"combined_group:{group}"] = compare_reachable_vs_task_subset(rows)
    for context in sorted({row["task_context_id"] for row in boundary_rows}):
        rows = [row for row in boundary_rows if row["task_context_id"] == context]
        output[f"task_context:{context}"] = compare_reachable_vs_task_subset(rows)
    for band in sorted({row["row_band"] for row in boundary_rows}):
        rows = [row for row in boundary_rows if row["row_band"] == band]
        output[f"row_band:{band}"] = compare_reachable_vs_task_subset(rows)
    for context, band in sorted({(row["task_context_id"], row["row_band"]) for row in boundary_rows}):
        rows = [
            row
            for row in boundary_rows
            if row["task_context_id"] == context and row["row_band"] == band
        ]
        output[f"{context}|{band}"] = compare_reachable_vs_task_subset(rows)
    for group, context, band in sorted(
        {(row["combined_group"], row["task_context_id"], row["row_band"]) for row in boundary_rows}
    ):
        rows = [
            row
            for row in boundary_rows
            if row["combined_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
        ]
        output[f"{group}|{context}|{band}"] = compare_reachable_vs_task_subset(rows)
    return output


def build_summary(boundary_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "manifest": build_manifest_summary(manifest_rows),
        "all": summarize_subset(boundary_rows),
        "by_combined_group": {},
        "by_combined_group_policy": {},
        "by_combined_group_context_band_policy": {},
        "by_policy_context_band": {},
        "reachable_vs_task": build_reachable_vs_task_summary(boundary_rows),
        "primary_policy_boundary_counts": {},
        "primary_policy_label_counts": {},
    }
    groups = [
        "target_dropped",
        "centroid_localization_exceeded",
        "false_positive_target_pushed_down",
        "rank_budget_shift_no_push",
        "false_positive_added_no_push",
        "candidate_dropout_or_score_shift",
        "stable_combined_control",
    ]
    policies = sorted({row["policy"] for row in boundary_rows})
    for group in groups:
        rows = [row for row in boundary_rows if row["combined_group"] == group]
        summary["by_combined_group"][group] = summarize_subset(rows)
        for policy in policies:
            policy_rows = [row for row in rows if row["policy"] == policy]
            summary["by_combined_group_policy"][f"{group}|{policy}"] = summarize_subset(policy_rows)

    for key in sorted(
        {
            (row["combined_group"], row["task_context_id"], row["row_band"], row["policy"])
            for row in boundary_rows
        }
    ):
        group, context, band, policy = key
        rows = [
            row
            for row in boundary_rows
            if row["combined_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
            and row["policy"] == policy
        ]
        summary["by_combined_group_context_band_policy"][
            f"{group}|{context}|{band}|{policy}"
        ] = summarize_subset(rows)

    for key in sorted({(row["policy"], row["task_context_id"], row["row_band"]) for row in boundary_rows}):
        policy, context, band = key
        rows = [
            row
            for row in boundary_rows
            if row["policy"] == policy and row["task_context_id"] == context and row["row_band"] == band
        ]
        summary["by_policy_context_band"][f"{policy}|{context}|{band}"] = summarize_subset(rows)

    primary_rows = [row for row in boundary_rows if row["policy"] in PRIMARY_POLICIES]
    hard_primary_rows = [
        row
        for row in primary_rows
        if row["localization_transition"] != "stable_localization_success"
    ]
    summary["primary_policy_boundary_counts"] = counter_dict(Counter(row["boundary_type"] for row in primary_rows))
    summary["primary_policy_label_counts"] = counter_dict(Counter(row["object_label"] for row in hard_primary_rows))
    return summary


def build_hard_boundary_rows(boundary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    hard_groups = {
        "target_dropped",
        "centroid_localization_exceeded",
        "false_positive_target_pushed_down",
        "rank_budget_shift_no_push",
    }
    for row in boundary_rows:
        if row["policy"] not in PRIMARY_POLICIES:
            continue
        if row["localization_transition"] == "stable_localization_success" and row["combined_group"] not in hard_groups:
            continue
        next_test = "separate combined-noise components with controlled ablation"
        if row["combined_group"] == "target_dropped":
            next_test = "proposal-recall ceiling and detector recall validation"
        elif row["combined_group"] == "centroid_localization_exceeded":
            next_test = "localization threshold calibration under centroid jitter"
        elif row["boundary_type"] in {
            "false_positive_push_budget_identity_regression",
            "rank_shift_budget_identity_regression",
            "budget_identity_regression",
            "persistent_false_positive_push_budget_boundary",
            "persistent_budget_localization_boundary",
        }:
            next_test = "budget and reachable-first calibration under distractor rank shift"
        elif row["boundary_type"] == "reachability_identity_regression":
            next_test = "grid reachability source audit under combined noise"
        elif row["boundary_type"].startswith("persistent"):
            next_test = "separate persistent method failure from combined-noise failure"
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": row["original_row_uid"],
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "proposal_noise_seed": row["proposal_noise_seed"],
                "policy": row["policy"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "ambiguity_band": row["ambiguity_band"],
                "combined_group": row["combined_group"],
                "identity_transition": row["identity_transition"],
                "localization_transition": row["localization_transition"],
                "boundary_type": row["boundary_type"],
                "target_dropped_by_noise": row["target_dropped_by_noise"],
                "false_positive_added_count": row["false_positive_added_count"],
                "false_positive_above_target_count": row["false_positive_above_target_count"],
                "target_pushed_down_by_false_positive": row["target_pushed_down_by_false_positive"],
                "target_jitter_exceeds_success_threshold": row["target_jitter_exceeds_success_threshold"],
                "target_centroid_jitter_m": row["target_centroid_jitter_m"],
                "clean_target_rank": row["clean_target_rank"],
                "combined_target_rank": row["combined_target_rank"],
                "target_rank_delta": row["target_rank_delta"],
                "combined_returned_location_count": row["combined_returned_location_count"],
                "combined_localization_failure_type": row["combined_localization_failure_type"],
                "expected_search_cost_delta": row["expected_search_cost_delta"],
                "task_utility_delta": row["task_utility_delta"],
                "next_test": next_test,
            }
        )
    return rows


def build_policy_delta_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, item in summary["by_combined_group_policy"].items():
        group, policy = key.split("|", 1)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "combined_group": group,
                "policy": policy,
                "rows": item["rows"],
                "clean_identity_sr": item["clean_identity_sr"],
                "combined_identity_sr": item["combined_identity_sr"],
                "identity_sr_delta": item["identity_sr_delta"],
                "clean_localization_sr": item["clean_localization_sr"],
                "combined_localization_sr": item["combined_localization_sr"],
                "localization_sr_delta": item["localization_sr_delta"],
                "combined_identity_localization_gap": item["combined_identity_localization_gap"],
                "combined_identity_regression_rows": item["combined_identity_regression_rows"],
                "combined_localization_regression_rows": item["combined_localization_regression_rows"],
                "target_dropped_rate": item["target_dropped_rate"],
                "false_positive_added_rate": item["false_positive_added_rate"],
                "target_pushed_down_rate": item["target_pushed_down_rate"],
                "target_rank_changed_rate": item["target_rank_changed_rate"],
                "target_jitter_exceeds_threshold_rate": item["target_jitter_exceeds_threshold_rate"],
                "mean_target_rank_delta": item["mean_target_rank_delta"],
                "mean_false_positive_added_count": item["mean_false_positive_added_count"],
                "mean_false_positive_above_target_count": item["mean_false_positive_above_target_count"],
                "mean_target_centroid_jitter_m": item["mean_target_centroid_jitter_m"],
                "mean_expected_search_cost_delta": item["mean_expected_search_cost_delta"],
                "mean_attempt_spl_delta": item["mean_attempt_spl_delta"],
                "mean_task_utility_delta": item["mean_task_utility_delta"],
                "returned_unreachable_event_delta": item["returned_unreachable_event_delta"],
            }
        )
    return rows


def get_metric(summary: dict[str, Any], group: str, context: str, band: str, policy: str) -> dict[str, Any]:
    return summary["by_combined_group_context_band_policy"].get(
        f"{group}|{context}|{band}|{policy}",
        summarize_subset([]),
    )


def get_policy_context_metric(summary: dict[str, Any], policy: str, context: str, band: str) -> dict[str, Any]:
    return summary["by_policy_context_band"].get(
        f"{policy}|{context}|{band}",
        summarize_subset([]),
    )


def build_claim_boundary(summary: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    manifest = summary["manifest"]
    task_sig_all = get_policy_context_metric(
        summary,
        "task_conditioned_budget_v0",
        "routine_fetch",
        "significant_moved",
    )
    reachable_sig_all = get_policy_context_metric(
        summary,
        "reachable_first_task_conditioned_budget_v0",
        "routine_fetch",
        "significant_moved",
    )
    task_sig_dropped = get_metric(
        summary,
        "target_dropped",
        "routine_fetch",
        "significant_moved",
        "task_conditioned_budget_v0",
    )
    task_sig_push = get_metric(
        summary,
        "false_positive_target_pushed_down",
        "routine_fetch",
        "significant_moved",
        "task_conditioned_budget_v0",
    )
    reachable_sig_push = get_metric(
        summary,
        "false_positive_target_pushed_down",
        "routine_fetch",
        "significant_moved",
        "reachable_first_task_conditioned_budget_v0",
    )
    reachable_vs_task_sig = summary["reachable_vs_task"]["routine_fetch|significant_moved"]
    return {
        "status": "combined_noise_boundary_ready",
        "safe_claims": [
            "E003-M14 supports controlled annotation-proxy combined-noise failure-boundary analysis.",
            "Combined stress exposes separable proposal-recall, distractor rank/budget, and centroid-localization boundaries.",
            "`reachable_first_task_conditioned_budget_v0` improves significant moved `routine_fetch` identity/localization success relative to `task_conditioned_budget_v0` under the combined annotation-proxy stress profile.",
        ],
        "partial_or_weakened_claims": [
            "The current combined profile uses annotation-derived proxy perturbations, not real RGB-D or open-vocabulary detector proposals.",
            "Target-dropped rows are proposal-recall ceiling cases and should not be counted as recoverable stale-memory policy failures.",
            "False positives are annotation-derived semantic-group or fallback distractors; same-label detector hallucinations are not covered.",
            "Occupancy-grid reachability is reused by instance id and is not recomputed after centroid perturbation.",
            "Current `ExpectedSearchCost`, `AttemptSPL`, and `SR` are proxy metrics, not real navigation `SPL` or execution `SR`.",
        ],
        "unsupported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary detector robustness",
            "real navigation `SR` / `SPL`",
            "deployable search policy",
            "natural-language intention understanding",
        ],
        "key_evidence": {
            "boundary_rows": coverage["boundary_rows"],
            "hard_boundary_rows": coverage["hard_boundary_rows"],
            "stress_query_rows": manifest["stress_query_rows"],
            "target_dropped_rows": manifest["target_dropped_rows"],
            "false_positive_added_rows": manifest["false_positive_added_rows"],
            "target_pushed_down_rows": manifest["target_pushed_down_rows"],
            "target_rank_changed_rows": manifest["target_rank_changed_rows"],
            "target_jitter_exceeds_threshold_rows": manifest["target_jitter_exceeds_threshold_rows"],
            "significant_routine_task_identity_sr": task_sig_all["combined_identity_sr"],
            "significant_routine_task_localization_sr": task_sig_all["combined_localization_sr"],
            "significant_routine_reachable_identity_sr": reachable_sig_all["combined_identity_sr"],
            "significant_routine_reachable_localization_sr": reachable_sig_all["combined_localization_sr"],
            "significant_routine_reachable_minus_task_identity_delta": reachable_vs_task_sig[
                "identity_sr_delta_reachable_minus_task"
            ],
            "significant_routine_reachable_minus_task_localization_delta": reachable_vs_task_sig[
                "localization_sr_delta_reachable_minus_task"
            ],
            "significant_routine_reachable_identity_success_gain_rows": reachable_vs_task_sig[
                "reachable_identity_success_gain_rows"
            ],
            "significant_routine_reachable_identity_success_loss_rows": reachable_vs_task_sig[
                "reachable_identity_success_loss_rows"
            ],
            "significant_routine_task_target_dropped_rows": task_sig_dropped["rows"],
            "significant_routine_task_target_dropped_identity_sr": task_sig_dropped["combined_identity_sr"],
            "significant_routine_push_task_identity_sr": task_sig_push["combined_identity_sr"],
            "significant_routine_push_reachable_identity_sr": reachable_sig_push["combined_identity_sr"],
            "grid_path_recomputed_for_centroid_jitter": manifest[
                "grid_path_recomputed_for_centroid_jitter"
            ],
            "uses_real_rgbd_perception": coverage["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": coverage["uses_open_vocab_perception"],
            "uses_real_navigation": coverage["uses_real_navigation"],
        },
        "next_recommended_unit": {
            "selected": "E003-M15 controlled perception-robustness claim summary",
            "reason": "Individual and combined annotation-proxy stress profiles now have implementation and boundary analyses; the next step should consolidate the supported claim before any Dockerized real proposal route.",
            "defer": [
                "Dockerized real RGB-D/open-vocabulary proposal generation until a proposal source and scan alignment are selected",
                "real navigation evaluation until simulator/navmesh/trajectory execution source is available",
            ],
        },
    }


def build_coverage(
    input_dir: Path,
    out_dir: Path,
    input_coverage: dict[str, Any],
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
    hard_boundary_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    stress_query_rows = summary["manifest"]["stress_query_rows"]
    policies = sorted({row["policy"] for row in predictions})
    expected_boundary_rows = stress_query_rows * len(policies)
    status = "combined_noise_boundary_ready"
    if len(boundary_rows) != expected_boundary_rows:
        status = "review_needed"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "input_dir": str(input_dir),
        "input_status": input_coverage["status"],
        "reference_profile": REFERENCE_PROFILE,
        "stress_profile": COMBINED_PROFILE,
        "policies": policies,
        "manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "stress_query_rows": stress_query_rows,
        "expected_boundary_rows": expected_boundary_rows,
        "boundary_rows": len(boundary_rows),
        "hard_boundary_rows": len(hard_boundary_rows),
        "docker_required": False,
        "docker_reason": "E003-M14 is repository-local analysis over E003-M13 JSONL artifacts; real detector/open-vocabulary implementations remain Docker-required.",
        "uses_annotation_proxy_noise": input_coverage["uses_annotation_proxy_noise"],
        "uses_real_rgbd_perception": input_coverage["uses_real_rgbd_perception"],
        "uses_open_vocab_perception": input_coverage["uses_open_vocab_perception"],
        "uses_real_navigation": input_coverage["uses_real_navigation"],
        "grid_path_recomputed_for_centroid_jitter": summary["manifest"][
            "grid_path_recomputed_for_centroid_jitter"
        ],
        "next_recommended_unit": "E003-M15 controlled perception-robustness claim summary",
        "outputs": {
            "boundary_rows": str(out_dir / "boundary_rows.jsonl"),
            "hard_boundary_rows": str(out_dir / "hard_boundary_rows.jsonl"),
            "policy_delta_rows": str(out_dir / "policy_delta_rows.jsonl"),
            "summary": str(out_dir / "summary.json"),
            "claim_boundary": str(out_dir / "claim_boundary.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    coverage: dict[str, Any],
    summary: dict[str, Any],
    claim_boundary: dict[str, Any],
    out_dir: Path,
) -> str:
    manifest = summary["manifest"]
    reachable_vs_task_sig = summary["reachable_vs_task"]["routine_fetch|significant_moved"]
    lines = [
        "# E003-M14 Combined Noise Failure Boundary",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Boundary rows: {coverage['boundary_rows']}",
        f"- Hard boundary rows: {coverage['hard_boundary_rows']}",
        f"- Stress query rows: {manifest['stress_query_rows']}",
        f"- Target dropped rows: {manifest['target_dropped_rows']}",
        f"- False-positive added rows: {manifest['false_positive_added_rows']}",
        f"- Target pushed-down rows: {manifest['target_pushed_down_rows']}",
        f"- Target rank changed rows: {manifest['target_rank_changed_rows']}",
        f"- Target jitter exceeds threshold rows: {manifest['target_jitter_exceeds_threshold_rows']}",
        f"- Mean target centroid jitter m: {manifest['mean_target_centroid_jitter_m']}",
        f"- Combined group counts: {manifest['combined_group_counts']}",
        f"- Uses real RGB-D perception: {coverage['uses_real_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocab_perception']}",
        f"- Uses real navigation: {coverage['uses_real_navigation']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch` Boundary",
        "",
        "| Group | Policy | rows | identity `SR` | localization `SR` | identity delta | localization delta | target drop | target push | rank changed | jitter exceeded | cost delta | utility delta |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in [
        "target_dropped",
        "centroid_localization_exceeded",
        "false_positive_target_pushed_down",
        "rank_budget_shift_no_push",
        "false_positive_added_no_push",
        "candidate_dropout_or_score_shift",
        "stable_combined_control",
    ]:
        for policy in [
            "task_conditioned_budget_v0",
            "reachable_first_task_conditioned_budget_v0",
            "always_top5",
            "oracle_current_target",
        ]:
            item = get_metric(summary, group, "routine_fetch", "significant_moved", policy)
            if item["rows"] == 0:
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        group,
                        f"`{policy}`",
                        str(item["rows"]),
                        str(item["combined_identity_sr"]),
                        str(item["combined_localization_sr"]),
                        str(item["identity_sr_delta"]),
                        str(item["localization_sr_delta"]),
                        str(item["target_dropped_rate"]),
                        str(item["target_pushed_down_rate"]),
                        str(item["target_rank_changed_rate"]),
                        str(item["target_jitter_exceeds_threshold_rate"]),
                        str(item["mean_expected_search_cost_delta"]),
                        str(item["mean_task_utility_delta"]),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Reachable-First vs Task-Conditioned",
            "",
            f"- Significant moved `routine_fetch` paired rows: {reachable_vs_task_sig['rows']}",
            f"- `task_conditioned_budget_v0` combined identity `SR`: {reachable_vs_task_sig['task_combined_identity_sr']}",
            f"- `reachable_first_task_conditioned_budget_v0` combined identity `SR`: {reachable_vs_task_sig['reachable_combined_identity_sr']}",
            f"- Identity `SR` delta reachable-first minus task: {reachable_vs_task_sig['identity_sr_delta_reachable_minus_task']}",
            f"- Localization `SR` delta reachable-first minus task: {reachable_vs_task_sig['localization_sr_delta_reachable_minus_task']}",
            f"- Reachable-first identity gain rows: {reachable_vs_task_sig['reachable_identity_success_gain_rows']}",
            f"- Reachable-first identity loss rows: {reachable_vs_task_sig['reachable_identity_success_loss_rows']}",
            f"- Returned-unreachable event delta reachable-first minus task: {reachable_vs_task_sig['unreachable_event_delta_reachable_minus_task']}",
            "",
            "## Boundary Counts",
            "",
            f"- Primary policy boundary counts: {summary['primary_policy_boundary_counts']}",
            f"- Primary policy hard label counts: {summary['primary_policy_label_counts']}",
            "",
            "## 논문 주장",
            "",
        ]
    )
    for item in claim_boundary["safe_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 에이전트 추론", ""])
    for item in claim_boundary["partial_or_weakened_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Unsupported Claims", ""])
    for item in claim_boundary["unsupported_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 사용자 판단 필요", ""])
    lines.append("- None for E003-M14. Next unit should consolidate the controlled perception-robustness claim before any Dockerized real proposal route.")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `boundary_rows.jsonl`",
            "- `hard_boundary_rows.jsonl`",
            "- `policy_delta_rows.jsonl`",
            "- `summary.json`",
            "- `claim_boundary.json`",
            "- `coverage.json`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    input_coverage = load_json(args.input_dir / "coverage.json")
    predictions = load_jsonl(args.input_dir / "predictions.jsonl")
    manifest_rows = load_jsonl(args.input_dir / "noise_manifest.jsonl")

    boundary_rows = build_boundary_rows(predictions, manifest_rows)
    summary = build_summary(boundary_rows, manifest_rows)
    hard_boundary_rows = build_hard_boundary_rows(boundary_rows)
    policy_delta_rows = build_policy_delta_rows(summary)
    coverage = build_coverage(
        args.input_dir,
        args.out_dir,
        input_coverage,
        predictions,
        manifest_rows,
        boundary_rows,
        hard_boundary_rows,
        summary,
    )
    claim_boundary = build_claim_boundary(summary, coverage)
    report = build_report(coverage, summary, claim_boundary, args.out_dir)

    write_jsonl(args.out_dir / "boundary_rows.jsonl", boundary_rows)
    write_jsonl(args.out_dir / "hard_boundary_rows.jsonl", hard_boundary_rows)
    write_jsonl(args.out_dir / "policy_delta_rows.jsonl", policy_delta_rows)
    write_json(args.out_dir / "summary.json", summary)
    write_json(args.out_dir / "claim_boundary.json", claim_boundary)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": coverage["status"], "out_dir": str(args.out_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
