#!/usr/bin/env python3
"""Analyze E003 annotation false-positive failure boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M08_annotation_false_positive_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M09_false_positive_failure_boundary_v0"
ANALYSIS_VERSION = "e003_false_positive_failure_boundary_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
FALSE_POSITIVE_PROFILE = "annotation_false_positive_v0"
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


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round6(sum(values) / len(values))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def index_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_uid"]: row for row in manifest_rows}


def clean_prediction_index(predictions: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    output = {}
    for row in predictions:
        if row["proposal_noise_profile_id"] == REFERENCE_PROFILE:
            output[(row["original_row_uid"], row["policy"])] = row
    return output


def contamination_group(manifest: dict[str, Any]) -> str:
    if manifest["target_pushed_down_by_false_positive"]:
        return "target_pushed_down"
    if int(manifest["false_positive_added_count"]) > 0:
        return "false_positive_added_no_push"
    if int(manifest["false_positive_available_count"]) == 0:
        return "no_false_positive_available"
    return "false_positive_available_not_added"


def transition_label(clean_success: bool, stress_success: bool) -> str:
    if clean_success and stress_success:
        return "stable_success"
    if clean_success and not stress_success:
        return "false_positive_regression"
    if not clean_success and stress_success:
        return "false_positive_improvement"
    return "stable_failure"


def rank_delta(clean: dict[str, Any], stress: dict[str, Any]) -> int | None:
    if clean["target_rank"] is None or stress["target_rank"] is None:
        return None
    return int(stress["target_rank"]) - int(clean["target_rank"])


def target_outside_budget(row: dict[str, Any], prefix: str) -> bool:
    target_rank = row[f"{prefix}_target_rank"]
    returned_k = row[f"{prefix}_returned_location_count"]
    return target_rank is not None and int(target_rank) > int(returned_k)


def boundary_type(
    clean: dict[str, Any],
    stress: dict[str, Any],
    manifest: dict[str, Any],
    transition: str,
    group: str,
) -> str:
    if group == "no_false_positive_available":
        if transition == "stable_success":
            return "no_false_positive_available_stable_success"
        if stress["returns_old_location"]:
            return "no_false_positive_available_static_memory_boundary"
        return "no_false_positive_available_control_boundary"

    if group == "target_pushed_down":
        if transition == "false_positive_regression":
            if stress["target_rank"] is not None and int(stress["target_rank"]) > int(stress["returned_location_count"]):
                return "target_push_budget_regression"
            if int(stress["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
                return "target_push_reachability_regression"
            return "target_push_policy_regression"
        if transition == "stable_failure":
            if stress["stale_old_location_fp"]:
                return "target_push_stale_static_failure"
            if stress["target_rank"] is not None and int(stress["target_rank"]) > int(stress["returned_location_count"]):
                return "target_push_persistent_budget_boundary"
            return "target_push_persistent_failure"
        if transition == "false_positive_improvement":
            return "target_push_unexpected_improvement"
        return "target_push_survived_budget"

    if group == "false_positive_added_no_push":
        if transition == "false_positive_regression":
            if int(stress["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
                return "false_positive_reachability_regression"
            if stress["target_rank"] is not None and int(stress["target_rank"]) > int(stress["returned_location_count"]):
                return "false_positive_budget_regression"
            return "false_positive_policy_regression"
        if transition == "stable_failure":
            if stress["stale_old_location_fp"]:
                return "false_positive_stale_static_failure"
            if stress["target_rank"] is not None and int(stress["target_rank"]) > int(stress["returned_location_count"]):
                return "false_positive_persistent_budget_boundary"
            return "false_positive_persistent_failure"
        if transition == "false_positive_improvement":
            return "false_positive_added_improvement"
        return "false_positive_added_stable_success"

    if transition == "stable_success":
        return "false_positive_available_not_added_stable_success"
    return "false_positive_available_not_added_boundary"


def build_boundary_rows(
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_row_uid = index_manifest(manifest_rows)
    clean_index = clean_prediction_index(predictions)
    rows = []
    for stress in predictions:
        if stress["proposal_noise_profile_id"] != FALSE_POSITIVE_PROFILE:
            continue
        clean = clean_index[(stress["original_row_uid"], stress["policy"])]
        manifest = manifest_by_row_uid[stress["row_uid"]]
        group = contamination_group(manifest)
        clean_success = bool(clean["search_success"])
        stress_success = bool(stress["search_success"])
        transition = transition_label(clean_success, stress_success)
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
                "contamination_group": group,
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
                "candidate_rows_noisy": int(manifest["candidate_rows_noisy"]),
                "candidate_rows_added": int(manifest["candidate_rows_added"]),
                "clean_success": clean_success,
                "false_positive_success": stress_success,
                "transition": transition,
                "boundary_type": boundary_type(clean, stress, manifest, transition, group),
                "clean_target_rank": clean["target_rank"],
                "false_positive_target_rank": stress["target_rank"],
                "target_rank_delta": delta_rank,
                "clean_returned_location_count": clean["returned_location_count"],
                "false_positive_returned_location_count": stress["returned_location_count"],
                "returned_location_count_delta": int(stress["returned_location_count"])
                - int(clean["returned_location_count"]),
                "clean_expected_search_cost": clean["expected_search_cost"],
                "false_positive_expected_search_cost": stress["expected_search_cost"],
                "expected_search_cost_delta": round6(
                    float(stress["expected_search_cost"]) - float(clean["expected_search_cost"])
                ),
                "clean_attempt_spl_proxy": clean["attempt_spl_proxy"],
                "false_positive_attempt_spl_proxy": stress["attempt_spl_proxy"],
                "attempt_spl_delta": round6(
                    float(stress["attempt_spl_proxy"]) - float(clean["attempt_spl_proxy"])
                ),
                "clean_task_utility": clean["task_utility"],
                "false_positive_task_utility": stress["task_utility"],
                "task_utility_delta": round6(float(stress["task_utility"]) - float(clean["task_utility"])),
                "clean_returned_unreachable_count": clean["returned_unreachable_count"],
                "false_positive_returned_unreachable_count": stress["returned_unreachable_count"],
                "returned_unreachable_count_delta": int(stress["returned_unreachable_count"])
                - int(clean["returned_unreachable_count"]),
                "uses_real_rgbd_perception": stress["uses_real_rgbd_perception"],
                "uses_open_vocab_perception": stress["uses_open_vocab_perception"],
            }
        )
    return rows


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "clean_proxy_sr": None,
            "false_positive_proxy_sr": None,
            "proxy_sr_delta": None,
            "false_positive_regression_rows": 0,
            "false_positive_regression_rate": None,
            "false_positive_improvement_rows": 0,
            "stable_failure_rows": 0,
            "stable_success_rows": 0,
            "target_pushed_down_rate": None,
            "mean_false_positive_added_count": None,
            "mean_false_positive_above_target_count": None,
            "target_rank_worse_rows": 0,
            "target_rank_same_rows": 0,
            "mean_target_rank_delta": None,
            "mean_candidate_rows_added": None,
            "mean_expected_search_cost_delta": None,
            "mean_attempt_spl_delta": None,
            "mean_task_utility_delta": None,
            "returned_unreachable_event_delta": 0,
            "transition_counts": {},
            "boundary_counts": {},
            "contamination_group_counts": {},
        }
    clean_success = sum(1 for row in rows if row["clean_success"])
    stress_success = sum(1 for row in rows if row["false_positive_success"])
    transition_counts = Counter(row["transition"] for row in rows)
    boundary_counts = Counter(row["boundary_type"] for row in rows)
    group_counts = Counter(row["contamination_group"] for row in rows)
    rank_deltas = [float(row["target_rank_delta"]) for row in rows if row["target_rank_delta"] is not None]
    return {
        "rows": len(rows),
        "clean_proxy_sr": safe_rate(clean_success, len(rows)),
        "false_positive_proxy_sr": safe_rate(stress_success, len(rows)),
        "proxy_sr_delta": round6((stress_success - clean_success) / len(rows)),
        "false_positive_regression_rows": transition_counts["false_positive_regression"],
        "false_positive_regression_rate": safe_rate(
            transition_counts["false_positive_regression"], len(rows)
        ),
        "false_positive_improvement_rows": transition_counts["false_positive_improvement"],
        "stable_failure_rows": transition_counts["stable_failure"],
        "stable_success_rows": transition_counts["stable_success"],
        "target_pushed_down_rate": safe_rate(
            sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
            len(rows),
        ),
        "mean_false_positive_added_count": mean([float(row["false_positive_added_count"]) for row in rows]),
        "mean_false_positive_above_target_count": mean(
            [float(row["false_positive_above_target_count"]) for row in rows]
        ),
        "target_rank_worse_rows": sum(
            1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] > 0
        ),
        "target_rank_same_rows": sum(1 for row in rows if row["target_rank_delta"] == 0),
        "mean_target_rank_delta": mean(rank_deltas),
        "mean_candidate_rows_added": mean([float(row["candidate_rows_added"]) for row in rows]),
        "mean_expected_search_cost_delta": mean([float(row["expected_search_cost_delta"]) for row in rows]),
        "mean_attempt_spl_delta": mean([float(row["attempt_spl_delta"]) for row in rows]),
        "mean_task_utility_delta": mean([float(row["task_utility_delta"]) for row in rows]),
        "returned_unreachable_event_delta": sum(
            1 for row in rows if int(row["false_positive_returned_unreachable_count"]) > 0
        )
        - sum(1 for row in rows if int(row["clean_returned_unreachable_count"]) > 0),
        "transition_counts": counter_dict(transition_counts),
        "boundary_counts": counter_dict(boundary_counts),
        "contamination_group_counts": counter_dict(group_counts),
    }


def build_manifest_summary(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stress_rows = [
        row for row in manifest_rows if row["proposal_noise_profile_id"] == FALSE_POSITIVE_PROFILE
    ]
    added_rows = [row for row in stress_rows if int(row["false_positive_added_count"]) > 0]
    no_available_rows = [
        row for row in stress_rows if int(row["false_positive_available_count"]) == 0
    ]
    target_pushed_rows = [
        row for row in stress_rows if row["target_pushed_down_by_false_positive"]
    ]
    return {
        "stress_query_rows": len(stress_rows),
        "false_positive_added_rows": len(added_rows),
        "no_false_positive_available_rows": len(no_available_rows),
        "target_pushed_down_rows": len(target_pushed_rows),
        "false_positive_added_rate": safe_rate(len(added_rows), len(stress_rows)),
        "target_pushed_down_rate": safe_rate(len(target_pushed_rows), len(stress_rows)),
        "no_false_positive_available_rate": safe_rate(len(no_available_rows), len(stress_rows)),
        "target_retained_rows": sum(1 for row in stress_rows if row["target_retained"]),
        "target_retained_rate": safe_rate(
            sum(1 for row in stress_rows if row["target_retained"]), len(stress_rows)
        ),
        "mean_candidate_rows_original": mean([float(row["candidate_rows_original"]) for row in stress_rows]),
        "mean_candidate_rows_noisy": mean([float(row["candidate_rows_noisy"]) for row in stress_rows]),
        "mean_candidate_rows_added": mean([float(row["candidate_rows_added"]) for row in stress_rows]),
        "same_label_false_positive_count": sum(int(row["same_label_false_positive_count"]) for row in stress_rows),
        "semantic_group_false_positive_count": sum(
            int(row["semantic_group_false_positive_count"]) for row in stress_rows
        ),
        "fallback_false_positive_count": sum(int(row["fallback_false_positive_count"]) for row in stress_rows),
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
            "task_false_positive_proxy_sr": None,
            "reachable_false_positive_proxy_sr": None,
            "false_positive_proxy_sr_delta_reachable_minus_task": None,
            "false_positive_unreachable_event_delta_reachable_minus_task": None,
        }
    task_success = sum(1 for item in paired if item["task_conditioned_budget_v0"]["false_positive_success"])
    reachable_success = sum(
        1 for item in paired if item["reachable_first_task_conditioned_budget_v0"]["false_positive_success"]
    )
    task_unreachable_events = sum(
        1
        for item in paired
        if int(item["task_conditioned_budget_v0"]["false_positive_returned_unreachable_count"]) > 0
    )
    reachable_unreachable_events = sum(
        1
        for item in paired
        if int(item["reachable_first_task_conditioned_budget_v0"]["false_positive_returned_unreachable_count"]) > 0
    )
    return {
        "rows": len(paired),
        "task_false_positive_proxy_sr": safe_rate(task_success, len(paired)),
        "reachable_false_positive_proxy_sr": safe_rate(reachable_success, len(paired)),
        "false_positive_proxy_sr_delta_reachable_minus_task": round6(
            (reachable_success - task_success) / len(paired)
        ),
        "reachable_success_gain_rows": sum(
            1
            for item in paired
            if item["reachable_first_task_conditioned_budget_v0"]["false_positive_success"]
            and not item["task_conditioned_budget_v0"]["false_positive_success"]
        ),
        "reachable_success_loss_rows": sum(
            1
            for item in paired
            if item["task_conditioned_budget_v0"]["false_positive_success"]
            and not item["reachable_first_task_conditioned_budget_v0"]["false_positive_success"]
        ),
        "task_unreachable_event_rate": safe_rate(task_unreachable_events, len(paired)),
        "reachable_unreachable_event_rate": safe_rate(reachable_unreachable_events, len(paired)),
        "false_positive_unreachable_event_delta_reachable_minus_task": round6(
            (reachable_unreachable_events - task_unreachable_events) / len(paired)
        ),
        "mean_expected_search_cost_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["false_positive_expected_search_cost"])
                - float(item["task_conditioned_budget_v0"]["false_positive_expected_search_cost"])
                for item in paired
            ]
        ),
        "mean_task_utility_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["false_positive_task_utility"])
                - float(item["task_conditioned_budget_v0"]["false_positive_task_utility"])
                for item in paired
            ]
        ),
    }


def build_reachable_vs_task_summary(boundary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"all": compare_reachable_vs_task_subset(boundary_rows)}
    for group in sorted({row["contamination_group"] for row in boundary_rows}):
        rows = [row for row in boundary_rows if row["contamination_group"] == group]
        output[f"contamination_group:{group}"] = compare_reachable_vs_task_subset(rows)
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
        {(row["contamination_group"], row["task_context_id"], row["row_band"]) for row in boundary_rows}
    ):
        rows = [
            row
            for row in boundary_rows
            if row["contamination_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
        ]
        output[f"{group}|{context}|{band}"] = compare_reachable_vs_task_subset(rows)
    return output


def build_summary(boundary_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "manifest": build_manifest_summary(manifest_rows),
        "all": summarize_subset(boundary_rows),
        "by_contamination_group": {},
        "by_contamination_group_policy": {},
        "by_contamination_group_context_band_policy": {},
        "by_policy_context_band": {},
        "reachable_vs_task": build_reachable_vs_task_summary(boundary_rows),
        "primary_policy_boundary_counts": {},
        "primary_policy_label_counts": {},
    }
    groups = [
        "target_pushed_down",
        "false_positive_added_no_push",
        "no_false_positive_available",
        "false_positive_available_not_added",
    ]
    policies = sorted({row["policy"] for row in boundary_rows})
    for group in groups:
        rows = [row for row in boundary_rows if row["contamination_group"] == group]
        summary["by_contamination_group"][group] = summarize_subset(rows)
        for policy in policies:
            policy_rows = [row for row in rows if row["policy"] == policy]
            summary["by_contamination_group_policy"][f"{group}|{policy}"] = summarize_subset(policy_rows)

    for key in sorted(
        {
            (row["contamination_group"], row["task_context_id"], row["row_band"], row["policy"])
            for row in boundary_rows
        }
    ):
        group, context, band, policy = key
        rows = [
            row
            for row in boundary_rows
            if row["contamination_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
            and row["policy"] == policy
        ]
        summary["by_contamination_group_context_band_policy"][
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
        if row["transition"] in {"false_positive_regression", "stable_failure"}
    ]
    summary["primary_policy_boundary_counts"] = counter_dict(Counter(row["boundary_type"] for row in primary_rows))
    summary["primary_policy_label_counts"] = counter_dict(Counter(row["object_label"] for row in hard_primary_rows))
    return summary


def build_hard_boundary_rows(boundary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in boundary_rows:
        if row["policy"] not in PRIMARY_POLICIES:
            continue
        if row["transition"] == "stable_success" and row["contamination_group"] != "target_pushed_down":
            continue
        next_test = "budget calibration under false-positive contamination"
        if row["boundary_type"].endswith("reachability_regression"):
            next_test = "reachable-first ordering and grid source audit"
        elif row["contamination_group"] == "no_false_positive_available":
            next_test = "exclude no-false-positive-available rows from contamination denominator"
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
                "contamination_group": row["contamination_group"],
                "transition": row["transition"],
                "boundary_type": row["boundary_type"],
                "clean_target_rank": row["clean_target_rank"],
                "false_positive_target_rank": row["false_positive_target_rank"],
                "target_rank_delta": row["target_rank_delta"],
                "false_positive_above_target_count": row["false_positive_above_target_count"],
                "false_positive_added_count": row["false_positive_added_count"],
                "false_positive_returned_location_count": row["false_positive_returned_location_count"],
                "expected_search_cost_delta": row["expected_search_cost_delta"],
                "task_utility_delta": row["task_utility_delta"],
                "next_test": next_test,
            }
        )
    return rows


def build_policy_delta_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, item in summary["by_contamination_group_policy"].items():
        group, policy = key.split("|", 1)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "contamination_group": group,
                "policy": policy,
                "rows": item["rows"],
                "clean_proxy_sr": item["clean_proxy_sr"],
                "false_positive_proxy_sr": item["false_positive_proxy_sr"],
                "proxy_sr_delta": item["proxy_sr_delta"],
                "false_positive_regression_rows": item["false_positive_regression_rows"],
                "false_positive_improvement_rows": item["false_positive_improvement_rows"],
                "mean_target_rank_delta": item["mean_target_rank_delta"],
                "mean_false_positive_added_count": item["mean_false_positive_added_count"],
                "mean_false_positive_above_target_count": item["mean_false_positive_above_target_count"],
                "mean_expected_search_cost_delta": item["mean_expected_search_cost_delta"],
                "mean_attempt_spl_delta": item["mean_attempt_spl_delta"],
                "mean_task_utility_delta": item["mean_task_utility_delta"],
                "returned_unreachable_event_delta": item["returned_unreachable_event_delta"],
            }
        )
    return rows


def get_metric(summary: dict[str, Any], group: str, context: str, band: str, policy: str) -> dict[str, Any]:
    return summary["by_contamination_group_context_band_policy"].get(
        f"{group}|{context}|{band}|{policy}",
        summarize_subset([]),
    )


def build_claim_boundary(summary: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    manifest = summary["manifest"]
    task_sig_target_push = get_metric(
        summary,
        "target_pushed_down",
        "routine_fetch",
        "significant_moved",
        "task_conditioned_budget_v0",
    )
    reachable_sig_target_push = get_metric(
        summary,
        "target_pushed_down",
        "routine_fetch",
        "significant_moved",
        "reachable_first_task_conditioned_budget_v0",
    )
    reachable_vs_task_sig = summary["reachable_vs_task"]["routine_fetch|significant_moved"]
    return {
        "status": "false_positive_boundary_ready",
        "safe_claims": [
            "E003-M09 supports controlled annotation-derived false-positive failure-boundary analysis.",
            "False-positive contamination causes recoverable and non-recoverable ranking/budget failures while preserving target presence.",
            "`reachable_first_task_conditioned_budget_v0` reduces the false-positive damage relative to `task_conditioned_budget_v0` in the significant moved `routine_fetch` subset.",
        ],
        "partial_or_weakened_claims": [
            "The current false positives are annotation-derived semantic-group or same-scene distractors; same-label false positives are not covered because E001 already includes same-label candidates.",
            "The result is a bridge toward perception-noise robustness, not a real open-vocabulary detector hallucination result.",
            "Target-pushed-down rows isolate budget/ranking sensitivity, but real RGB-D/open-vocabulary proposal generation is still required for detector claims.",
        ],
        "unsupported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary detector hallucination robustness",
            "real navigation `SR` / `SPL`",
            "deployable search policy",
            "natural-language intention understanding",
        ],
        "key_evidence": {
            "boundary_rows": coverage["boundary_rows"],
            "hard_boundary_rows": coverage["hard_boundary_rows"],
            "stress_query_rows": manifest["stress_query_rows"],
            "false_positive_added_rows": manifest["false_positive_added_rows"],
            "target_pushed_down_rows": manifest["target_pushed_down_rows"],
            "target_pushed_down_rate": manifest["target_pushed_down_rate"],
            "same_label_false_positive_count": manifest["same_label_false_positive_count"],
            "semantic_group_false_positive_count": manifest["semantic_group_false_positive_count"],
            "fallback_false_positive_count": manifest["fallback_false_positive_count"],
            "target_push_significant_routine_task_sr": task_sig_target_push["false_positive_proxy_sr"],
            "target_push_significant_routine_reachable_sr": reachable_sig_target_push["false_positive_proxy_sr"],
            "significant_routine_reachable_minus_task_sr_delta": reachable_vs_task_sig[
                "false_positive_proxy_sr_delta_reachable_minus_task"
            ],
            "significant_routine_reachable_success_gain_rows": reachable_vs_task_sig[
                "reachable_success_gain_rows"
            ],
            "uses_real_rgbd_perception": coverage["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": coverage["uses_open_vocab_perception"],
            "uses_real_navigation": coverage["uses_real_navigation"],
        },
        "next_stress_profile_decision": {
            "selected": "annotation_centroid_jitter_v0",
            "reason": "Score/rank jitter, proposal dropout, and false-positive contamination are now covered; centroid jitter is the remaining controlled perception-like profile before combining profiles.",
            "defer": [
                "annotation_combined_moderate_v0 until centroid jitter has a separate boundary",
                "real RGB-D/open-vocabulary detector route until Dockerized proposal generation is staged",
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
    status = "false_positive_boundary_ready"
    if len(boundary_rows) != expected_boundary_rows:
        status = "review_needed"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "input_dir": str(input_dir),
        "input_status": input_coverage["status"],
        "reference_profile": REFERENCE_PROFILE,
        "stress_profile": FALSE_POSITIVE_PROFILE,
        "policies": policies,
        "manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "stress_query_rows": stress_query_rows,
        "expected_boundary_rows": expected_boundary_rows,
        "boundary_rows": len(boundary_rows),
        "hard_boundary_rows": len(hard_boundary_rows),
        "docker_required": False,
        "docker_reason": "E003-M09 is repository-local analysis over E003-M08 JSONL artifacts; detector/open-vocabulary implementations remain Docker-required.",
        "uses_annotation_proxy_noise": input_coverage["uses_annotation_proxy_noise"],
        "uses_real_rgbd_perception": input_coverage["uses_real_rgbd_perception"],
        "uses_open_vocab_perception": input_coverage["uses_open_vocab_perception"],
        "uses_real_navigation": input_coverage["uses_real_navigation"],
        "next_stress_profile": "annotation_centroid_jitter_v0",
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
        "# E003-M09 False Positive Failure Boundary",
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
        f"- False-positive added rows: {manifest['false_positive_added_rows']}",
        f"- Target pushed-down rows: {manifest['target_pushed_down_rows']}",
        f"- Target pushed-down rate: {manifest['target_pushed_down_rate']}",
        f"- Same-label false positives: {manifest['same_label_false_positive_count']}",
        f"- Semantic-group false positives: {manifest['semantic_group_false_positive_count']}",
        f"- Fallback false positives: {manifest['fallback_false_positive_count']}",
        f"- Uses real RGB-D perception: {coverage['uses_real_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocab_perception']}",
        f"- Uses real navigation: {coverage['uses_real_navigation']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch` Boundary",
        "",
        "| Group | Policy | rows | clean `SR` | FP `SR` | delta `SR` | regressions | improvements | mean target-rank delta | cost delta | utility delta |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in [
        "target_pushed_down",
        "false_positive_added_no_push",
        "no_false_positive_available",
    ]:
        for policy in [
            "always_top5",
            "task_conditioned_budget_v0",
            "reachable_first_task_conditioned_budget_v0",
            "oracle_current_target",
        ]:
            item = get_metric(summary, group, "routine_fetch", "significant_moved", policy)
            lines.append(
                "| `{group}` | `{policy}` | {rows} | {clean} | {stress} | {delta} | {regressions} | {improvements} | {rank_delta} | {cost_delta} | {utility_delta} |".format(
                    group=group,
                    policy=policy,
                    rows=item["rows"],
                    clean=item["clean_proxy_sr"],
                    stress=item["false_positive_proxy_sr"],
                    delta=item["proxy_sr_delta"],
                    regressions=item.get("false_positive_regression_rows"),
                    improvements=item.get("false_positive_improvement_rows"),
                    rank_delta=item.get("mean_target_rank_delta"),
                    cost_delta=item.get("mean_expected_search_cost_delta"),
                    utility_delta=item.get("mean_task_utility_delta"),
                )
            )
    lines.extend(
        [
            "",
            "## Reachable-First Comparison",
            "",
            f"- Significant moved `routine_fetch` rows: {reachable_vs_task_sig['rows']}",
            f"- `task_conditioned_budget_v0` FP proxy `SR`: {reachable_vs_task_sig['task_false_positive_proxy_sr']}",
            f"- `reachable_first_task_conditioned_budget_v0` FP proxy `SR`: {reachable_vs_task_sig['reachable_false_positive_proxy_sr']}",
            f"- Reachable-first minus task proxy `SR` delta: {reachable_vs_task_sig['false_positive_proxy_sr_delta_reachable_minus_task']}",
            f"- Reachable-first success gain rows: {reachable_vs_task_sig['reachable_success_gain_rows']}",
            f"- Reachable-first success loss rows: {reachable_vs_task_sig['reachable_success_loss_rows']}",
            f"- Reachable-first unreachable event delta: {reachable_vs_task_sig['false_positive_unreachable_event_delta_reachable_minus_task']}",
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
    lines.extend(
        [
            f"- Next stress profile should be `{claim_boundary['next_stress_profile_decision']['selected']}`.",
            f"- Reason: {claim_boundary['next_stress_profile_decision']['reason']}",
            "",
            "## Unsupported Claims",
            "",
        ]
    )
    for item in claim_boundary["unsupported_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 사용자 판단 필요", ""])
    lines.append("- None for E003-M09. Next implementation unit should start `annotation_centroid_jitter_v0` unless redirected to Dockerized real proposal generation.")
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
