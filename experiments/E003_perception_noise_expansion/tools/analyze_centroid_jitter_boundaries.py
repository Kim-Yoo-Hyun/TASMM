#!/usr/bin/env python3
"""Analyze E003 annotation centroid-jitter failure boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M10_annotation_centroid_jitter_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M11_centroid_jitter_failure_boundary_v0"
ANALYSIS_VERSION = "e003_centroid_jitter_failure_boundary_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
CENTROID_JITTER_PROFILE = "annotation_centroid_jitter_v0"
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


def jitter_group(manifest: dict[str, Any]) -> str:
    if manifest["target_jitter_exceeds_success_threshold"]:
        return "target_jitter_exceeds_threshold"
    if manifest["target_rank_delta"] not in {0, None}:
        return "target_rank_changed_within_threshold"
    if int(manifest["rank_changed_candidate_rows"]) > 0:
        return "candidate_rank_changed_only"
    return "within_threshold_rank_stable"


def transition_label(clean_success: bool, stress_success: bool, prefix: str) -> str:
    if clean_success and stress_success:
        return f"stable_{prefix}_success"
    if clean_success and not stress_success:
        return f"centroid_{prefix}_regression"
    if not clean_success and stress_success:
        return f"centroid_{prefix}_improvement"
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

    if failure_type == "target_centroid_jitter_exceeds_threshold":
        if stress_identity and not stress_localized:
            return "identity_success_over_jitter_localization_failure"
        if identity_transition == "centroid_identity_regression":
            return "over_jitter_with_identity_regression"
        return "over_jitter_persistent_localization_failure"

    if identity_transition == "centroid_identity_regression":
        if stress["target_rank"] is None:
            return "centroid_missing_target_unexpected"
        if target_outside_budget(stress):
            if manifest["target_rank_delta"] not in {0, None}:
                return "rank_jitter_budget_identity_regression"
            return "persistent_budget_identity_regression"
        if int(stress["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
            return "reachability_identity_regression"
        return "centroid_identity_policy_regression"

    if identity_transition == "centroid_identity_improvement":
        if manifest["target_rank_delta"] is not None and int(manifest["target_rank_delta"]) < 0:
            return "rank_jitter_identity_improvement"
        return "centroid_identity_improvement"

    if localization_transition == "centroid_localization_regression":
        if stress_identity and not stress_localized:
            return "identity_success_localization_regression"
        if target_outside_budget(stress):
            return "budget_localization_regression"
        return "centroid_localization_policy_regression"

    if localization_transition == "centroid_localization_improvement":
        return "centroid_localization_improvement"

    if localization_transition == "stable_localization_failure":
        if stress["stale_old_location_fp"]:
            return "stale_static_localization_failure"
        if target_outside_budget(stress):
            return "persistent_budget_localization_boundary"
        if group == "target_rank_changed_within_threshold":
            return "rank_changed_persistent_localization_failure"
        return "persistent_localization_failure"

    if group == "target_rank_changed_within_threshold":
        return "rank_changed_survived_localization"
    if group == "candidate_rank_changed_only":
        return "candidate_rank_changed_survived_localization"
    return "within_threshold_stable_localization"


def build_boundary_rows(
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_row_uid = index_manifest(manifest_rows)
    clean_index = clean_prediction_index(predictions)
    rows = []
    for stress in predictions:
        if stress["proposal_noise_profile_id"] != CENTROID_JITTER_PROFILE:
            continue
        clean = clean_index[(stress["original_row_uid"], stress["policy"])]
        manifest = manifest_by_row_uid[stress["row_uid"]]
        group = jitter_group(manifest)
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
                "jitter_group": group,
                "target_retained": bool(manifest["target_retained"]),
                "target_jitter_exceeds_success_threshold": bool(
                    manifest["target_jitter_exceeds_success_threshold"]
                ),
                "target_rank_changed_by_centroid_jitter": manifest["target_rank_delta"]
                not in {0, None},
                "rank_changed_candidate_rows": int(manifest["rank_changed_candidate_rows"]),
                "target_centroid_jitter_m": stress["target_centroid_jitter_m"],
                "target_planar_jitter_m": stress["target_planar_jitter_m"],
                "mean_candidate_centroid_jitter_m": manifest["mean_candidate_centroid_jitter_m"],
                "mean_candidate_planar_jitter_m": manifest["mean_candidate_planar_jitter_m"],
                "max_candidate_centroid_jitter_m": manifest["max_candidate_centroid_jitter_m"],
                "clean_identity_success": bool(clean["search_success"]),
                "centroid_identity_success": bool(stress["search_success"]),
                "clean_localization_success": bool(clean["localization_success"]),
                "centroid_localization_success": bool(stress["localization_success"]),
                "centroid_localization_failure_type": stress["localization_failure_type"],
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
                "centroid_target_rank": stress["target_rank"],
                "target_rank_delta": delta_rank,
                "manifest_target_rank_delta": manifest["target_rank_delta"],
                "clean_returned_location_count": clean["returned_location_count"],
                "centroid_returned_location_count": stress["returned_location_count"],
                "returned_location_count_delta": int(stress["returned_location_count"])
                - int(clean["returned_location_count"]),
                "clean_expected_search_cost": clean["expected_search_cost"],
                "centroid_expected_search_cost": stress["expected_search_cost"],
                "expected_search_cost_delta": round6(
                    float(stress["expected_search_cost"]) - float(clean["expected_search_cost"])
                ),
                "clean_attempt_spl_proxy": clean["attempt_spl_proxy"],
                "centroid_attempt_spl_proxy": stress["attempt_spl_proxy"],
                "attempt_spl_delta": round6(
                    float(stress["attempt_spl_proxy"]) - float(clean["attempt_spl_proxy"])
                ),
                "clean_task_utility": clean["task_utility"],
                "centroid_task_utility": stress["task_utility"],
                "task_utility_delta": round6(float(stress["task_utility"]) - float(clean["task_utility"])),
                "clean_returned_unreachable_count": clean["returned_unreachable_count"],
                "centroid_returned_unreachable_count": stress["returned_unreachable_count"],
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
            "centroid_identity_sr": None,
            "identity_sr_delta": None,
            "clean_localization_sr": None,
            "centroid_localization_sr": None,
            "localization_sr_delta": None,
            "centroid_identity_localization_gap": None,
            "identity_success_localization_failure_rows": 0,
            "identity_success_localization_failure_rate": None,
            "centroid_identity_regression_rows": 0,
            "centroid_localization_regression_rows": 0,
            "target_jitter_exceeds_threshold_rate": None,
            "target_rank_changed_rate": None,
            "transition_counts": {},
            "localization_transition_counts": {},
            "boundary_counts": {},
            "jitter_group_counts": {},
        }
    clean_identity = sum(1 for row in rows if row["clean_identity_success"])
    centroid_identity = sum(1 for row in rows if row["centroid_identity_success"])
    clean_localization = sum(1 for row in rows if row["clean_localization_success"])
    centroid_localization = sum(1 for row in rows if row["centroid_localization_success"])
    identity_transition_counts = Counter(row["identity_transition"] for row in rows)
    localization_transition_counts = Counter(row["localization_transition"] for row in rows)
    boundary_counts = Counter(row["boundary_type"] for row in rows)
    group_counts = Counter(row["jitter_group"] for row in rows)
    rank_deltas = [float(row["target_rank_delta"]) for row in rows if row["target_rank_delta"] is not None]
    return {
        "rows": len(rows),
        "clean_identity_sr": safe_rate(clean_identity, len(rows)),
        "centroid_identity_sr": safe_rate(centroid_identity, len(rows)),
        "identity_sr_delta": round6((centroid_identity - clean_identity) / len(rows)),
        "clean_localization_sr": safe_rate(clean_localization, len(rows)),
        "centroid_localization_sr": safe_rate(centroid_localization, len(rows)),
        "localization_sr_delta": round6((centroid_localization - clean_localization) / len(rows)),
        "clean_identity_localization_gap": round6((clean_identity - clean_localization) / len(rows)),
        "centroid_identity_localization_gap": round6((centroid_identity - centroid_localization) / len(rows)),
        "identity_success_localization_failure_rows": sum(
            1 for row in rows if row["identity_success_localization_failure"]
        ),
        "identity_success_localization_failure_rate": safe_rate(
            sum(1 for row in rows if row["identity_success_localization_failure"]),
            len(rows),
        ),
        "centroid_identity_regression_rows": identity_transition_counts["centroid_identity_regression"],
        "centroid_identity_improvement_rows": identity_transition_counts["centroid_identity_improvement"],
        "centroid_localization_regression_rows": localization_transition_counts[
            "centroid_localization_regression"
        ],
        "centroid_localization_improvement_rows": localization_transition_counts[
            "centroid_localization_improvement"
        ],
        "target_jitter_exceeds_threshold_rows": sum(
            1 for row in rows if row["target_jitter_exceeds_success_threshold"]
        ),
        "target_jitter_exceeds_threshold_rate": safe_rate(
            sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"]),
            len(rows),
        ),
        "target_rank_changed_rows": sum(1 for row in rows if row["target_rank_changed_by_centroid_jitter"]),
        "target_rank_changed_rate": safe_rate(
            sum(1 for row in rows if row["target_rank_changed_by_centroid_jitter"]),
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
        "mean_target_centroid_jitter_m": mean([float(row["target_centroid_jitter_m"]) for row in rows]),
        "mean_target_planar_jitter_m": mean([float(row["target_planar_jitter_m"]) for row in rows]),
        "mean_expected_search_cost_delta": mean([float(row["expected_search_cost_delta"]) for row in rows]),
        "mean_attempt_spl_delta": mean([float(row["attempt_spl_delta"]) for row in rows]),
        "mean_task_utility_delta": mean([float(row["task_utility_delta"]) for row in rows]),
        "returned_unreachable_event_delta": sum(
            1 for row in rows if int(row["centroid_returned_unreachable_count"]) > 0
        )
        - sum(1 for row in rows if int(row["clean_returned_unreachable_count"]) > 0),
        "identity_transition_counts": counter_dict(identity_transition_counts),
        "localization_transition_counts": counter_dict(localization_transition_counts),
        "boundary_counts": counter_dict(boundary_counts),
        "jitter_group_counts": counter_dict(group_counts),
    }


def build_manifest_summary(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stress_rows = [
        row for row in manifest_rows if row["proposal_noise_profile_id"] == CENTROID_JITTER_PROFILE
    ]
    threshold_rows = [row for row in stress_rows if row["target_jitter_exceeds_success_threshold"]]
    target_rank_changed_rows = [row for row in stress_rows if row["target_rank_delta"] not in {0, None}]
    return {
        "stress_query_rows": len(stress_rows),
        "target_retained_rows": sum(1 for row in stress_rows if row["target_retained"]),
        "target_retained_rate": safe_rate(
            sum(1 for row in stress_rows if row["target_retained"]), len(stress_rows)
        ),
        "target_jitter_exceeds_threshold_rows": len(threshold_rows),
        "target_jitter_exceeds_threshold_rate": safe_rate(len(threshold_rows), len(stress_rows)),
        "target_rank_changed_rows": len(target_rank_changed_rows),
        "target_rank_changed_rate": safe_rate(len(target_rank_changed_rows), len(stress_rows)),
        "rank_changed_candidate_rows": sum(int(row["rank_changed_candidate_rows"]) for row in stress_rows),
        "mean_target_centroid_jitter_m": mean(
            [float(row["target_centroid_jitter_m"]) for row in stress_rows]
        ),
        "mean_target_planar_jitter_m": mean(
            [float(row["target_planar_jitter_m"]) for row in stress_rows]
        ),
        "mean_candidate_centroid_jitter_m": mean(
            [float(row["mean_candidate_centroid_jitter_m"]) for row in stress_rows]
        ),
        "mean_candidate_planar_jitter_m": mean(
            [float(row["mean_candidate_planar_jitter_m"]) for row in stress_rows]
        ),
        "grid_path_recomputed_for_centroid_jitter": any(
            bool(row["grid_path_recomputed_for_centroid_jitter"]) for row in stress_rows
        ),
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
            "task_centroid_identity_sr": None,
            "reachable_centroid_identity_sr": None,
            "identity_sr_delta_reachable_minus_task": None,
            "task_centroid_localization_sr": None,
            "reachable_centroid_localization_sr": None,
            "localization_sr_delta_reachable_minus_task": None,
        }
    task_identity = sum(1 for item in paired if item["task_conditioned_budget_v0"]["centroid_identity_success"])
    reachable_identity = sum(
        1 for item in paired if item["reachable_first_task_conditioned_budget_v0"]["centroid_identity_success"]
    )
    task_localization = sum(
        1 for item in paired if item["task_conditioned_budget_v0"]["centroid_localization_success"]
    )
    reachable_localization = sum(
        1 for item in paired if item["reachable_first_task_conditioned_budget_v0"]["centroid_localization_success"]
    )
    task_unreachable_events = sum(
        1
        for item in paired
        if int(item["task_conditioned_budget_v0"]["centroid_returned_unreachable_count"]) > 0
    )
    reachable_unreachable_events = sum(
        1
        for item in paired
        if int(item["reachable_first_task_conditioned_budget_v0"]["centroid_returned_unreachable_count"]) > 0
    )
    return {
        "rows": len(paired),
        "task_centroid_identity_sr": safe_rate(task_identity, len(paired)),
        "reachable_centroid_identity_sr": safe_rate(reachable_identity, len(paired)),
        "identity_sr_delta_reachable_minus_task": round6((reachable_identity - task_identity) / len(paired)),
        "task_centroid_localization_sr": safe_rate(task_localization, len(paired)),
        "reachable_centroid_localization_sr": safe_rate(reachable_localization, len(paired)),
        "localization_sr_delta_reachable_minus_task": round6(
            (reachable_localization - task_localization) / len(paired)
        ),
        "reachable_identity_success_gain_rows": sum(
            1
            for item in paired
            if item["reachable_first_task_conditioned_budget_v0"]["centroid_identity_success"]
            and not item["task_conditioned_budget_v0"]["centroid_identity_success"]
        ),
        "reachable_identity_success_loss_rows": sum(
            1
            for item in paired
            if item["task_conditioned_budget_v0"]["centroid_identity_success"]
            and not item["reachable_first_task_conditioned_budget_v0"]["centroid_identity_success"]
        ),
        "reachable_localization_success_gain_rows": sum(
            1
            for item in paired
            if item["reachable_first_task_conditioned_budget_v0"]["centroid_localization_success"]
            and not item["task_conditioned_budget_v0"]["centroid_localization_success"]
        ),
        "reachable_localization_success_loss_rows": sum(
            1
            for item in paired
            if item["task_conditioned_budget_v0"]["centroid_localization_success"]
            and not item["reachable_first_task_conditioned_budget_v0"]["centroid_localization_success"]
        ),
        "task_unreachable_event_rate": safe_rate(task_unreachable_events, len(paired)),
        "reachable_unreachable_event_rate": safe_rate(reachable_unreachable_events, len(paired)),
        "unreachable_event_delta_reachable_minus_task": round6(
            (reachable_unreachable_events - task_unreachable_events) / len(paired)
        ),
        "mean_expected_search_cost_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["centroid_expected_search_cost"])
                - float(item["task_conditioned_budget_v0"]["centroid_expected_search_cost"])
                for item in paired
            ]
        ),
        "mean_task_utility_delta_reachable_minus_task": mean(
            [
                float(item["reachable_first_task_conditioned_budget_v0"]["centroid_task_utility"])
                - float(item["task_conditioned_budget_v0"]["centroid_task_utility"])
                for item in paired
            ]
        ),
    }


def build_reachable_vs_task_summary(boundary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"all": compare_reachable_vs_task_subset(boundary_rows)}
    for group in sorted({row["jitter_group"] for row in boundary_rows}):
        rows = [row for row in boundary_rows if row["jitter_group"] == group]
        output[f"jitter_group:{group}"] = compare_reachable_vs_task_subset(rows)
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
        {(row["jitter_group"], row["task_context_id"], row["row_band"]) for row in boundary_rows}
    ):
        rows = [
            row
            for row in boundary_rows
            if row["jitter_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
        ]
        output[f"{group}|{context}|{band}"] = compare_reachable_vs_task_subset(rows)
    return output


def build_summary(boundary_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "manifest": build_manifest_summary(manifest_rows),
        "all": summarize_subset(boundary_rows),
        "by_jitter_group": {},
        "by_jitter_group_policy": {},
        "by_jitter_group_context_band_policy": {},
        "by_policy_context_band": {},
        "reachable_vs_task": build_reachable_vs_task_summary(boundary_rows),
        "primary_policy_boundary_counts": {},
        "primary_policy_label_counts": {},
    }
    groups = [
        "target_jitter_exceeds_threshold",
        "target_rank_changed_within_threshold",
        "candidate_rank_changed_only",
        "within_threshold_rank_stable",
    ]
    policies = sorted({row["policy"] for row in boundary_rows})
    for group in groups:
        rows = [row for row in boundary_rows if row["jitter_group"] == group]
        summary["by_jitter_group"][group] = summarize_subset(rows)
        for policy in policies:
            policy_rows = [row for row in rows if row["policy"] == policy]
            summary["by_jitter_group_policy"][f"{group}|{policy}"] = summarize_subset(policy_rows)

    for key in sorted(
        {
            (row["jitter_group"], row["task_context_id"], row["row_band"], row["policy"])
            for row in boundary_rows
        }
    ):
        group, context, band, policy = key
        rows = [
            row
            for row in boundary_rows
            if row["jitter_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
            and row["policy"] == policy
        ]
        summary["by_jitter_group_context_band_policy"][
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
    for row in boundary_rows:
        if row["policy"] not in PRIMARY_POLICIES:
            continue
        if row["localization_transition"] == "stable_localization_success":
            continue
        next_test = "centroid jitter localization threshold calibration"
        if row["boundary_type"] in {
            "rank_jitter_budget_identity_regression",
            "persistent_budget_identity_regression",
            "persistent_budget_localization_boundary",
        }:
            next_test = "budget calibration under centroid rank perturbation"
        elif row["boundary_type"] == "reachability_identity_regression":
            next_test = "recompute grid/path cost after jittered centroid"
        elif row["boundary_type"].startswith("persistent"):
            next_test = "separate persistent method failure from centroid-jitter failure"
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
                "jitter_group": row["jitter_group"],
                "identity_transition": row["identity_transition"],
                "localization_transition": row["localization_transition"],
                "boundary_type": row["boundary_type"],
                "target_centroid_jitter_m": row["target_centroid_jitter_m"],
                "target_planar_jitter_m": row["target_planar_jitter_m"],
                "target_jitter_exceeds_success_threshold": row[
                    "target_jitter_exceeds_success_threshold"
                ],
                "target_rank_delta": row["target_rank_delta"],
                "clean_target_rank": row["clean_target_rank"],
                "centroid_target_rank": row["centroid_target_rank"],
                "centroid_returned_location_count": row["centroid_returned_location_count"],
                "centroid_localization_failure_type": row["centroid_localization_failure_type"],
                "expected_search_cost_delta": row["expected_search_cost_delta"],
                "task_utility_delta": row["task_utility_delta"],
                "next_test": next_test,
            }
        )
    return rows


def build_policy_delta_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, item in summary["by_jitter_group_policy"].items():
        group, policy = key.split("|", 1)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "jitter_group": group,
                "policy": policy,
                "rows": item["rows"],
                "clean_identity_sr": item["clean_identity_sr"],
                "centroid_identity_sr": item["centroid_identity_sr"],
                "identity_sr_delta": item["identity_sr_delta"],
                "clean_localization_sr": item["clean_localization_sr"],
                "centroid_localization_sr": item["centroid_localization_sr"],
                "localization_sr_delta": item["localization_sr_delta"],
                "centroid_identity_localization_gap": item["centroid_identity_localization_gap"],
                "identity_success_localization_failure_rows": item[
                    "identity_success_localization_failure_rows"
                ],
                "centroid_identity_regression_rows": item["centroid_identity_regression_rows"],
                "centroid_localization_regression_rows": item[
                    "centroid_localization_regression_rows"
                ],
                "mean_target_centroid_jitter_m": item["mean_target_centroid_jitter_m"],
                "mean_target_rank_delta": item["mean_target_rank_delta"],
                "mean_expected_search_cost_delta": item["mean_expected_search_cost_delta"],
                "mean_attempt_spl_delta": item["mean_attempt_spl_delta"],
                "mean_task_utility_delta": item["mean_task_utility_delta"],
                "returned_unreachable_event_delta": item["returned_unreachable_event_delta"],
            }
        )
    return rows


def get_metric(summary: dict[str, Any], group: str, context: str, band: str, policy: str) -> dict[str, Any]:
    return summary["by_jitter_group_context_band_policy"].get(
        f"{group}|{context}|{band}|{policy}",
        summarize_subset([]),
    )


def build_claim_boundary(summary: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    manifest = summary["manifest"]
    task_sig_all = summary["by_policy_context_band"].get(
        "task_conditioned_budget_v0|routine_fetch|significant_moved",
        summarize_subset([]),
    )
    reachable_sig_all = summary["by_policy_context_band"].get(
        "reachable_first_task_conditioned_budget_v0|routine_fetch|significant_moved",
        summarize_subset([]),
    )
    task_sig_threshold = get_metric(
        summary,
        "target_jitter_exceeds_threshold",
        "routine_fetch",
        "significant_moved",
        "task_conditioned_budget_v0",
    )
    reachable_vs_task_sig = summary["reachable_vs_task"]["routine_fetch|significant_moved"]
    return {
        "status": "centroid_jitter_boundary_ready",
        "safe_claims": [
            "E003-M11 supports controlled annotation-proxy centroid-jitter failure-boundary analysis.",
            "Identity retrieval and spatial localization should be reported as separate success metrics under centroid noise.",
            "Correct-target identity success can still become localization failure when target centroid jitter exceeds the success threshold.",
        ],
        "partial_or_weakened_claims": [
            "The current jitter profile perturbs annotation centroids, not real RGB-D or open-vocabulary detector outputs.",
            "Occupancy-grid path costs are reused by instance id and are not recomputed after centroid perturbation.",
            "`reachable_first_task_conditioned_budget_v0` reduces returned-unreachable events in some subsets, but does not improve identity or localization `SR` under the current centroid-jitter profile.",
        ],
        "unsupported_claims": [
            "real RGB-D localization robustness",
            "open-vocabulary localization robustness",
            "real navigation `SR` / `SPL`",
            "deployable search policy",
            "natural-language intention understanding",
        ],
        "key_evidence": {
            "boundary_rows": coverage["boundary_rows"],
            "hard_boundary_rows": coverage["hard_boundary_rows"],
            "stress_query_rows": manifest["stress_query_rows"],
            "target_jitter_exceeds_threshold_rows": manifest[
                "target_jitter_exceeds_threshold_rows"
            ],
            "target_jitter_exceeds_threshold_rate": manifest[
                "target_jitter_exceeds_threshold_rate"
            ],
            "target_rank_changed_rows": manifest["target_rank_changed_rows"],
            "target_rank_changed_rate": manifest["target_rank_changed_rate"],
            "significant_routine_task_identity_sr": task_sig_all["centroid_identity_sr"],
            "significant_routine_task_localization_sr": task_sig_all[
                "centroid_localization_sr"
            ],
            "significant_routine_reachable_identity_sr": reachable_sig_all[
                "centroid_identity_sr"
            ],
            "significant_routine_reachable_localization_sr": reachable_sig_all[
                "centroid_localization_sr"
            ],
            "significant_routine_threshold_task_identity_sr": task_sig_threshold[
                "centroid_identity_sr"
            ],
            "significant_routine_threshold_task_localization_sr": task_sig_threshold[
                "centroid_localization_sr"
            ],
            "significant_routine_reachable_minus_task_identity_delta": reachable_vs_task_sig[
                "identity_sr_delta_reachable_minus_task"
            ],
            "significant_routine_reachable_minus_task_localization_delta": reachable_vs_task_sig[
                "localization_sr_delta_reachable_minus_task"
            ],
            "significant_routine_unreachable_event_delta_reachable_minus_task": reachable_vs_task_sig[
                "unreachable_event_delta_reachable_minus_task"
            ],
            "grid_path_recomputed_for_centroid_jitter": manifest[
                "grid_path_recomputed_for_centroid_jitter"
            ],
            "uses_real_rgbd_perception": coverage["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": coverage["uses_open_vocab_perception"],
            "uses_real_navigation": coverage["uses_real_navigation"],
        },
        "next_stress_profile_decision": {
            "selected": "E003-M12 combined-noise route decision",
            "reason": "Individual controlled profiles now cover score/rank jitter, proposal dropout, false positives, and centroid jitter; the next step should decide whether to combine profiles or switch to Dockerized real proposal generation.",
            "defer": [
                "real RGB-D/open-vocabulary localization claims until detector/proposal outputs are staged",
                "real navigation `SR` / `SPL` until simulator/navmesh/trajectory execution is available",
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
    status = "centroid_jitter_boundary_ready"
    if len(boundary_rows) != expected_boundary_rows:
        status = "review_needed"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "input_dir": str(input_dir),
        "input_status": input_coverage["status"],
        "reference_profile": REFERENCE_PROFILE,
        "stress_profile": CENTROID_JITTER_PROFILE,
        "policies": policies,
        "manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "stress_query_rows": stress_query_rows,
        "expected_boundary_rows": expected_boundary_rows,
        "boundary_rows": len(boundary_rows),
        "hard_boundary_rows": len(hard_boundary_rows),
        "docker_required": False,
        "docker_reason": "E003-M11 is repository-local analysis over E003-M10 JSONL artifacts; detector/open-vocabulary implementations remain Docker-required.",
        "uses_annotation_proxy_noise": input_coverage["uses_annotation_proxy_noise"],
        "uses_real_rgbd_perception": input_coverage["uses_real_rgbd_perception"],
        "uses_open_vocab_perception": input_coverage["uses_open_vocab_perception"],
        "uses_real_navigation": input_coverage["uses_real_navigation"],
        "grid_path_recomputed_for_centroid_jitter": summary["manifest"][
            "grid_path_recomputed_for_centroid_jitter"
        ],
        "next_recommended_unit": "E003-M12 combined-noise route decision",
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
        "# E003-M11 Centroid Jitter Failure Boundary",
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
        f"- Target jitter exceeds threshold rows: {manifest['target_jitter_exceeds_threshold_rows']}",
        f"- Target jitter exceeds threshold rate: {manifest['target_jitter_exceeds_threshold_rate']}",
        f"- Target rank changed rows: {manifest['target_rank_changed_rows']}",
        f"- Target rank changed rate: {manifest['target_rank_changed_rate']}",
        f"- Mean target centroid jitter m: {manifest['mean_target_centroid_jitter_m']}",
        f"- Mean target planar jitter m: {manifest['mean_target_planar_jitter_m']}",
        f"- Grid path recomputed for centroid jitter: {coverage['grid_path_recomputed_for_centroid_jitter']}",
        f"- Uses real RGB-D perception: {coverage['uses_real_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocab_perception']}",
        f"- Uses real navigation: {coverage['uses_real_navigation']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch` Boundary",
        "",
        "| Group | Policy | rows | identity `SR` | localization `SR` | localization delta | identity-localization gap | identity regressions | localization regressions | mean jitter m |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in [
        "target_jitter_exceeds_threshold",
        "target_rank_changed_within_threshold",
        "candidate_rank_changed_only",
        "within_threshold_rank_stable",
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
                        str(item["centroid_identity_sr"]),
                        str(item["centroid_localization_sr"]),
                        str(item["localization_sr_delta"]),
                        str(item["centroid_identity_localization_gap"]),
                        str(item["centroid_identity_regression_rows"]),
                        str(item["centroid_localization_regression_rows"]),
                        str(item["mean_target_centroid_jitter_m"]),
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
            f"- Identity `SR` delta reachable-first minus task: {reachable_vs_task_sig['identity_sr_delta_reachable_minus_task']}",
            f"- Localization `SR` delta reachable-first minus task: {reachable_vs_task_sig['localization_sr_delta_reachable_minus_task']}",
            f"- Returned-unreachable event delta reachable-first minus task: {reachable_vs_task_sig['unreachable_event_delta_reachable_minus_task']}",
            f"- Reachable-first localization gain rows: {reachable_vs_task_sig['reachable_localization_success_gain_rows']}",
            f"- Reachable-first localization loss rows: {reachable_vs_task_sig['reachable_localization_success_loss_rows']}",
            "",
            "## 논문 주장",
        ]
    )
    lines.extend([f"- {claim}" for claim in claim_boundary["safe_claims"]])
    lines.extend(
        [
            "",
            "## 에이전트 추론",
            "",
            "- Centroid jitter creates a measurable gap between correct-target identity retrieval and spatial localization.",
            "- The current reachable-first policy mainly changes unreachable-return behavior; it does not improve identity or localization success under this centroid-jitter profile.",
            "- Because grid path costs are not recomputed after centroid perturbation, this result should stay a controlled localization-noise proxy rather than a navigation claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M11. Continue to E003-M12 combined-noise route decision unless redirected to Dockerized real proposal generation.",
            "",
            "## Outputs",
            "",
        ]
    )
    for name in [
        "boundary_rows.jsonl",
        "hard_boundary_rows.jsonl",
        "policy_delta_rows.jsonl",
        "summary.json",
        "claim_boundary.json",
        "coverage.json",
        "report.md",
    ]:
        lines.append(f"- `{name}`")
    lines.append("")
    return "\n".join(lines)


def run(input_dir: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    input_coverage = load_json(input_dir / "coverage.json")
    predictions = load_jsonl(input_dir / "predictions.jsonl")
    manifest_rows = load_jsonl(input_dir / "noise_manifest.jsonl")
    boundary_rows = build_boundary_rows(predictions, manifest_rows)
    summary = build_summary(boundary_rows, manifest_rows)
    hard_boundary_rows = build_hard_boundary_rows(boundary_rows)
    policy_delta_rows = build_policy_delta_rows(summary)
    coverage = build_coverage(
        input_dir,
        out_dir,
        input_coverage,
        predictions,
        manifest_rows,
        boundary_rows,
        hard_boundary_rows,
        summary,
    )
    claim_boundary = build_claim_boundary(summary, coverage)
    report = build_report(coverage, summary, claim_boundary, out_dir)

    write_jsonl(out_dir / "boundary_rows.jsonl", boundary_rows)
    write_jsonl(out_dir / "hard_boundary_rows.jsonl", hard_boundary_rows)
    write_jsonl(out_dir / "policy_delta_rows.jsonl", policy_delta_rows)
    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "claim_boundary.json", claim_boundary)
    write_json(out_dir / "coverage.json", coverage)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    return coverage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    coverage = run(args.input_dir, args.out_dir)
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
