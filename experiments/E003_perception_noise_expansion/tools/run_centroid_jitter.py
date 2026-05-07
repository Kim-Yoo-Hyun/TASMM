#!/usr/bin/env python3
"""Generate and evaluate E003 annotation centroid-jitter stress rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from evaluate_noisy_policies import (
    POLICIES,
    attach_grid_fields,
    grid_reachability_index,
    group_by_uid,
    predict_policy,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_M02_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_GRID_DIR = (
    REPO_ROOT
    / "experiments"
    / "E002_path_cost_bridge"
    / "artifacts"
    / "E002-M05_occupancy_grid_astar_v0"
)
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M10_annotation_centroid_jitter_v0"
EVAL_VERSION = "e003_annotation_centroid_jitter_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
CENTROID_JITTER_PROFILE = "annotation_centroid_jitter_v0"
CENTROID_JITTER_SEEDS = [43, 47, 53]
PLANAR_SIGMA_M = 0.25
Z_SIGMA_M = 0.05
MAX_PLANAR_JITTER_M = 0.75
MAX_Z_JITTER_M = 0.15


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


def deterministic_rng(seed: int, *parts: str) -> random.Random:
    joined = "|".join([str(seed), *parts])
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def instance_key(value: Any) -> Any:
    text = str(value)
    return int(text) if text.isdigit() else text


def point_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def planar_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[1]) - float(b[1])) ** 2)


def clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def jitter_delta(seed: int, original_row_uid: str, candidate_instance_id: Any) -> list[float]:
    rng = deterministic_rng(seed, original_row_uid, str(candidate_instance_id), CENTROID_JITTER_PROFILE)
    dx = rng.gauss(0.0, PLANAR_SIGMA_M)
    dy = rng.gauss(0.0, PLANAR_SIGMA_M)
    planar = math.sqrt(dx * dx + dy * dy)
    if planar > MAX_PLANAR_JITTER_M and planar > 0.0:
        scale = MAX_PLANAR_JITTER_M / planar
        dx *= scale
        dy *= scale
    dz = clamp(rng.gauss(0.0, Z_SIGMA_M), MAX_Z_JITTER_M)
    return [dx, dy, dz]


def noisy_row_uid(row_uid: str, profile_id: str, seed: int | None = None) -> str:
    if seed is None:
        return f"{row_uid}::noise={profile_id}"
    return f"{row_uid}::noise={profile_id}::seed={seed}"


def build_query_row(
    row: dict[str, Any],
    profile_id: str,
    role: str,
    seed: int | None,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    output = dict(row)
    output["original_row_uid"] = row["row_uid"]
    output["row_uid"] = noisy_row_uid(row["row_uid"], profile_id, seed)
    output["noise_version"] = EVAL_VERSION
    output["perception_profile_id"] = "annotation_proxy_noise"
    output["proposal_noise_profile_id"] = profile_id
    output["proposal_noise_role"] = role
    output["proposal_noise_seed"] = seed
    output["proposal_noise_target_policy"] = "preserve_target"
    output["current_proposal_source"] = "annotation_semseg_noisy_proxy"
    output["observation_source"] = "annotation_semseg_noisy_proxy"
    output["uses_real_rgbd_perception"] = False
    output["uses_open_vocab_perception"] = False
    output["target_dropped_by_noise"] = False
    output["target_centroid_jitter_m"] = manifest["target_centroid_jitter_m"]
    output["target_planar_jitter_m"] = manifest["target_planar_jitter_m"]
    output["target_jitter_exceeds_success_threshold"] = manifest["target_jitter_exceeds_success_threshold"]
    output["target_rank_changed_by_centroid_jitter"] = manifest["target_rank_delta"] not in {0, None}
    output["centroid_jitter_profile_sigma_m"] = PLANAR_SIGMA_M
    output["grid_path_recomputed_for_centroid_jitter"] = False
    return output


def base_candidate_output(
    row: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    profile_id: str,
    role: str,
    seed: int | None,
) -> dict[str, Any]:
    output = dict(row)
    output["original_row_uid"] = original_row_uid
    output["row_uid"] = noisy_uid
    output["noise_version"] = EVAL_VERSION
    output["perception_profile_id"] = "annotation_proxy_noise"
    output["proposal_noise_profile_id"] = profile_id
    output["proposal_noise_role"] = role
    output["proposal_noise_seed"] = seed
    output["candidate_observation_source"] = "annotation_semseg_noisy_proxy"
    output["original_candidate_rank_non_persistent"] = row["candidate_rank_non_persistent"]
    output["original_candidate_score_non_persistent"] = row["candidate_score_non_persistent"]
    output["original_candidate_centroid"] = row["candidate_centroid"]
    output["candidate_retained_by_noise"] = True
    output["candidate_added_by_noise"] = False
    output["candidate_centroid_jitter_delta"] = [0.0, 0.0, 0.0]
    output["candidate_centroid_jitter_m"] = 0.0
    output["candidate_planar_jitter_m"] = 0.0
    output["candidate_score_noise_delta"] = 0.0
    output["candidate_path_cost_source"] = "jittered_euclidean_old_memory_to_candidate_centroid"
    output["grid_path_recomputed_for_centroid_jitter"] = False
    return output


def rank_candidates(rows: list[dict[str, Any]], profile_id: str) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row["candidate_score_non_persistent"]),
            int(row["original_candidate_rank_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{profile_id}_ranked_jittered_centroids"
    return ranked


def build_clean_candidates(
    query_row: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original_row_uid = query_row["row_uid"]
    row_uid = noisy_row_uid(original_row_uid, REFERENCE_PROFILE)
    rows = [
        base_candidate_output(row, original_row_uid, row_uid, REFERENCE_PROFILE, "clean_reference", None)
        for row in candidates
    ]
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row["original_candidate_rank_non_persistent"]),
            -float(row["candidate_score_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{REFERENCE_PROFILE}_ranked_candidates"
    target_rows = [row for row in ranked if row["candidate_is_target"]]
    target_rank = target_rows[0]["candidate_rank_non_persistent"] if target_rows else None
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": REFERENCE_PROFILE,
        "proposal_noise_seed": None,
        "candidate_rows": len(ranked),
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_rank_original": target_rank,
        "target_rank_noisy": target_rank,
        "target_rank_delta": 0,
        "rank_changed_candidate_rows": 0,
        "target_centroid_jitter_m": 0.0,
        "target_planar_jitter_m": 0.0,
        "target_jitter_exceeds_success_threshold": False,
        "mean_candidate_centroid_jitter_m": 0.0,
        "mean_candidate_planar_jitter_m": 0.0,
        "max_candidate_centroid_jitter_m": 0.0,
        "grid_path_recomputed_for_centroid_jitter": False,
    }


def jitter_candidate(
    query_row: dict[str, Any],
    row: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    seed: int,
) -> dict[str, Any]:
    output = base_candidate_output(
        row,
        original_row_uid,
        noisy_uid,
        CENTROID_JITTER_PROFILE,
        "controlled_centroid_localization_stress",
        seed,
    )
    delta = jitter_delta(seed, original_row_uid, row["candidate_instance_id"])
    original = [float(value) for value in row["candidate_centroid"]]
    jittered = [original[index] + delta[index] for index in range(3)]
    old = query_row["old_scene_aligned_centroid"]
    original_score = float(row["candidate_score_non_persistent"])
    distance_from_old = point_distance(old, jittered)
    noisy_score = 1.0 / (1.0 + distance_from_old)
    output["candidate_centroid"] = [round6(value) for value in jittered]
    output["candidate_centroid_jitter_delta"] = [round6(value) for value in delta]
    output["candidate_centroid_jitter_m"] = round6(point_distance(original, jittered))
    output["candidate_planar_jitter_m"] = round6(planar_distance(original, jittered))
    output["candidate_euclidean_cost_from_old_m"] = round6(distance_from_old)
    output["candidate_path_cost_m"] = round6(distance_from_old)
    output["candidate_path_cost_ready"] = True
    output["candidate_score_non_persistent"] = round6(noisy_score)
    output["candidate_score_noise_delta"] = round6(noisy_score - original_score)
    return output


def build_centroid_jitter_candidates(
    query_row: dict[str, Any],
    candidates: list[dict[str, Any]],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original_row_uid = query_row["row_uid"]
    row_uid = noisy_row_uid(original_row_uid, CENTROID_JITTER_PROFILE, seed)
    rows = [jitter_candidate(query_row, row, original_row_uid, row_uid, seed) for row in candidates]
    ranked = rank_candidates(rows, CENTROID_JITTER_PROFILE)
    target_rows = [row for row in ranked if row["candidate_is_target"]]
    original_target_rows = [row for row in candidates if row["candidate_is_target"]]
    target_rank_original = (
        int(original_target_rows[0]["candidate_rank_non_persistent"]) if original_target_rows else None
    )
    target_rank_noisy = target_rows[0]["candidate_rank_non_persistent"] if target_rows else None
    target_jitter = float(target_rows[0]["candidate_centroid_jitter_m"]) if target_rows else None
    target_planar_jitter = float(target_rows[0]["candidate_planar_jitter_m"]) if target_rows else None
    rank_changed_rows = [
        row
        for row in ranked
        if int(row["candidate_rank_non_persistent"]) != int(row["original_candidate_rank_non_persistent"])
    ]
    jitter_values = [float(row["candidate_centroid_jitter_m"]) for row in ranked]
    planar_values = [float(row["candidate_planar_jitter_m"]) for row in ranked]
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": CENTROID_JITTER_PROFILE,
        "proposal_noise_seed": seed,
        "candidate_rows": len(ranked),
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_rank_original": target_rank_original,
        "target_rank_noisy": target_rank_noisy,
        "target_rank_delta": target_rank_noisy - target_rank_original
        if target_rank_noisy is not None and target_rank_original is not None
        else None,
        "rank_changed_candidate_rows": len(rank_changed_rows),
        "target_centroid_jitter_m": round6(target_jitter),
        "target_planar_jitter_m": round6(target_planar_jitter),
        "target_jitter_exceeds_success_threshold": bool(
            target_jitter is not None and target_jitter > float(query_row["success_threshold_m"])
        ),
        "mean_candidate_centroid_jitter_m": mean(jitter_values),
        "mean_candidate_planar_jitter_m": mean(planar_values),
        "max_candidate_centroid_jitter_m": round6(max(jitter_values)) if jitter_values else None,
        "planar_sigma_m": PLANAR_SIGMA_M,
        "z_sigma_m": Z_SIGMA_M,
        "max_planar_jitter_m": MAX_PLANAR_JITTER_M,
        "max_z_jitter_m": MAX_Z_JITTER_M,
        "grid_path_recomputed_for_centroid_jitter": False,
    }


def build_noisy_rows(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_uid = group_by_uid(candidate_rows)
    noisy_query_rows: list[dict[str, Any]] = []
    noisy_candidate_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for row in query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        clean_candidates, clean_manifest = build_clean_candidates(row, candidates)
        noisy_query_rows.append(
            build_query_row(row, REFERENCE_PROFILE, "clean_reference", None, clean_manifest)
        )
        noisy_candidate_rows.extend(clean_candidates)
        manifest_rows.append(clean_manifest)

    for seed in CENTROID_JITTER_SEEDS:
        for row in query_rows:
            candidates = candidates_by_uid.get(row["row_uid"], [])
            noisy_candidates, manifest = build_centroid_jitter_candidates(row, candidates, seed)
            noisy_query_rows.append(
                build_query_row(
                    row,
                    CENTROID_JITTER_PROFILE,
                    "controlled_centroid_localization_stress",
                    seed,
                    manifest,
                )
            )
            noisy_candidate_rows.extend(noisy_candidates)
            manifest_rows.append(manifest)

    return noisy_query_rows, noisy_candidate_rows, manifest_rows


def localization_success(row: dict[str, Any]) -> bool:
    if row["returns_old_location"]:
        return bool(row["search_success"])
    if not row["search_success"]:
        return False
    return not bool(row["target_jitter_exceeds_success_threshold"])


def localization_failure_type(row: dict[str, Any]) -> str:
    if row["localization_success"]:
        return "none"
    if row["returns_old_location"]:
        return "static_map_localization_error"
    if not row["search_success"]:
        return "identity_or_budget_failure"
    if row["target_jitter_exceeds_success_threshold"]:
        return "target_centroid_jitter_exceeds_threshold"
    return "unknown_localization_failure"


def build_predictions(
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    grid_dir: Path,
) -> list[dict[str, Any]]:
    grid_candidate_path = grid_dir / "grid_candidate_rows.jsonl"
    grid_candidate_rows = load_jsonl(grid_candidate_path) if grid_candidate_path.exists() else []
    grid_index = grid_reachability_index(grid_candidate_rows)
    candidate_rows = attach_grid_fields(noisy_candidate_rows, grid_index)
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions = []
    for row in noisy_query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        for policy in POLICIES:
            prediction = predict_policy(policy, row, candidates)
            prediction["eval_version"] = EVAL_VERSION
            prediction["target_dropped_by_noise"] = False
            prediction["target_centroid_jitter_m"] = row["target_centroid_jitter_m"]
            prediction["target_planar_jitter_m"] = row["target_planar_jitter_m"]
            prediction["target_jitter_exceeds_success_threshold"] = bool(
                row["target_jitter_exceeds_success_threshold"]
            )
            prediction["target_rank_changed_by_centroid_jitter"] = bool(
                row["target_rank_changed_by_centroid_jitter"]
            )
            prediction["grid_path_recomputed_for_centroid_jitter"] = False
            prediction["localization_success"] = localization_success(prediction)
            prediction["localization_proxy_sr"] = prediction["localization_success"]
            prediction["localization_failure_type"] = localization_failure_type(prediction)
            predictions.append(prediction)
    return predictions


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def denominator_rows(rows: list[dict[str, Any]], denominator: str) -> list[dict[str, Any]]:
    if denominator == "all_rows":
        return rows
    if denominator == "target_jitter_within_threshold_eval":
        return [row for row in rows if not row["target_jitter_exceeds_success_threshold"]]
    if denominator == "target_jitter_exceeds_threshold_eval":
        return [row for row in rows if row["target_jitter_exceeds_success_threshold"]]
    if denominator == "target_rank_changed_eval":
        return [row for row in rows if row["target_rank_changed_by_centroid_jitter"]]
    raise RuntimeError(f"unknown denominator: {denominator}")


def summarize_prediction_rows(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    return {
        "subset": subset,
        "rows": len(rows),
        "identity_proxy_sr": safe_rate(sum(1 for row in rows if row["search_success"]), len(rows)),
        "localization_proxy_sr": safe_rate(sum(1 for row in rows if row["localization_success"]), len(rows)),
        "target_retained_rate": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
        "target_jitter_exceeds_threshold_rate": safe_rate(
            sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"]),
            len(rows),
        ),
        "target_rank_changed_rate": safe_rate(
            sum(1 for row in rows if row["target_rank_changed_by_centroid_jitter"]),
            len(rows),
        ),
        "mean_target_centroid_jitter_m": mean([float(row["target_centroid_jitter_m"]) for row in rows]),
        "mean_target_planar_jitter_m": mean([float(row["target_planar_jitter_m"]) for row in rows]),
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
        "returned_unreachable_rate": safe_rate(
            sum(1 for row in rows if row["returned_unreachable_count"] > 0),
            len(rows),
        ),
        "localization_failure_counts": counter_dict(Counter(row["localization_failure_type"] for row in rows)),
    }


def summarize_by_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    denominators = [
        "all_rows",
        "target_jitter_within_threshold_eval",
        "target_jitter_exceeds_threshold_eval",
        "target_rank_changed_eval",
    ]
    for denominator in denominators:
        den_rows = denominator_rows(rows, denominator)
        output[denominator] = {}
        for subset in ["all", "significant_moved", "mid_motion_review", "low_motion_control"]:
            subset_predictions = subset_rows(den_rows, subset)
            output[denominator][subset] = {}
            for context in sorted({row["task_context_id"] for row in subset_predictions}):
                context_rows = [row for row in subset_predictions if row["task_context_id"] == context]
                output[denominator][subset][context] = {}
                for policy in POLICIES:
                    policy_rows = [row for row in context_rows if row["policy"] == policy]
                    output[denominator][subset][context][policy] = summarize_prediction_rows(
                        policy_rows,
                        subset,
                    )
    return output


def build_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "profiles": {},
        "centroid_jitter_seeds": {},
    }
    for profile in [REFERENCE_PROFILE, CENTROID_JITTER_PROFILE]:
        profile_rows = [row for row in predictions if row["proposal_noise_profile_id"] == profile]
        metrics["profiles"][profile] = summarize_by_policy(profile_rows)
    for seed in CENTROID_JITTER_SEEDS:
        seed_rows = [
            row
            for row in predictions
            if row["proposal_noise_profile_id"] == CENTROID_JITTER_PROFILE
            and row["proposal_noise_seed"] == seed
        ]
        metrics["centroid_jitter_seeds"][str(seed)] = summarize_by_policy(seed_rows)
    return metrics


def summarize_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        by_profile[row["proposal_noise_profile_id"]].append(row)
    output: dict[str, Any] = {}
    for profile, rows in by_profile.items():
        output[profile] = {
            "rows": len(rows),
            "target_retained_rows": sum(1 for row in rows if row["target_retained"]),
            "target_retained_rate": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
            "target_rank_changed_rows": sum(1 for row in rows if row["target_rank_delta"] not in {0, None}),
            "target_rank_changed_rate": safe_rate(
                sum(1 for row in rows if row["target_rank_delta"] not in {0, None}), len(rows)
            ),
            "target_jitter_exceeds_threshold_rows": sum(
                1 for row in rows if row["target_jitter_exceeds_success_threshold"]
            ),
            "target_jitter_exceeds_threshold_rate": safe_rate(
                sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"]),
                len(rows),
            ),
            "mean_target_centroid_jitter_m": mean([float(row["target_centroid_jitter_m"]) for row in rows]),
            "mean_target_planar_jitter_m": mean([float(row["target_planar_jitter_m"]) for row in rows]),
            "mean_candidate_centroid_jitter_m": mean(
                [float(row["mean_candidate_centroid_jitter_m"]) for row in rows]
            ),
            "mean_candidate_planar_jitter_m": mean(
                [float(row["mean_candidate_planar_jitter_m"]) for row in rows]
            ),
            "rank_changed_candidate_rows": sum(int(row["rank_changed_candidate_rows"]) for row in rows),
            "grid_path_recomputed_for_centroid_jitter": all(
                bool(row["grid_path_recomputed_for_centroid_jitter"]) for row in rows
            ),
        }
    return output


def build_failure_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        if row["localization_success"]:
            continue
        if row["localization_failure_type"] == "identity_or_budget_failure" and row["proposal_noise_profile_id"] == REFERENCE_PROFILE:
            next_test = "compare clean baseline identity failure"
        elif row["localization_failure_type"] == "target_centroid_jitter_exceeds_threshold":
            next_test = "centroid-jitter failure-boundary analysis"
        else:
            next_test = "review localization failure boundary"
        rows.append(
            {
                "row_uid": row["row_uid"],
                "original_row_uid": row["original_row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "task_context_id": row["task_context_id"],
                "proposal_noise_profile_id": row["proposal_noise_profile_id"],
                "proposal_noise_seed": row["proposal_noise_seed"],
                "policy": row["policy"],
                "object_label": row["object_label"],
                "row_band": row["row_band"],
                "ambiguity_band": row["ambiguity_band"],
                "failure_type": row["localization_failure_type"],
                "target_rank": row["target_rank"],
                "returned_location_count": row["returned_location_count"],
                "expected_search_cost": row["expected_search_cost"],
                "target_centroid_jitter_m": row["target_centroid_jitter_m"],
                "target_planar_jitter_m": row["target_planar_jitter_m"],
                "target_jitter_exceeds_success_threshold": row["target_jitter_exceeds_success_threshold"],
                "identity_proxy_success": row["search_success"],
                "localization_success": row["localization_success"],
                "next_test": next_test,
            }
        )
    return rows


def build_coverage(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    metrics: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    manifest_summary = summarize_manifest(manifest_rows)
    jitter_summary = manifest_summary[CENTROID_JITTER_PROFILE]
    expected_noisy_query_rows = len(query_rows) * (1 + len(CENTROID_JITTER_SEEDS))
    sig_routine_task = metrics["profiles"][CENTROID_JITTER_PROFILE]["all_rows"]["significant_moved"][
        "routine_fetch"
    ]["task_conditioned_budget_v0"]
    sig_routine_reachable = metrics["profiles"][CENTROID_JITTER_PROFILE]["all_rows"][
        "significant_moved"
    ]["routine_fetch"]["reachable_first_task_conditioned_budget_v0"]
    sig_routine_exceeds_task = metrics["profiles"][CENTROID_JITTER_PROFILE][
        "target_jitter_exceeds_threshold_eval"
    ]["significant_moved"].get("routine_fetch", {}).get("task_conditioned_budget_v0", summarize_prediction_rows([], "significant_moved"))
    status = "centroid_jitter_eval_ready"
    if len(noisy_query_rows) != expected_noisy_query_rows:
        status = "review_needed"
    if len(predictions) != len(noisy_query_rows) * len(POLICIES):
        status = "review_needed"
    if jitter_summary["target_retained_rate"] != 1.0:
        status = "review_needed"
    if jitter_summary["mean_target_centroid_jitter_m"] in {None, 0.0}:
        status = "review_needed"
    return {
        "eval_version": EVAL_VERSION,
        "status": status,
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "profiles": [REFERENCE_PROFILE, CENTROID_JITTER_PROFILE],
        "centroid_jitter_seeds": CENTROID_JITTER_SEEDS,
        "planar_sigma_m": PLANAR_SIGMA_M,
        "z_sigma_m": Z_SIGMA_M,
        "max_planar_jitter_m": MAX_PLANAR_JITTER_M,
        "max_z_jitter_m": MAX_Z_JITTER_M,
        "noisy_query_rows": len(noisy_query_rows),
        "noisy_candidate_rows": len(noisy_candidate_rows),
        "noise_manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "manifest_summary": manifest_summary,
        "target_drop_profiles_included": False,
        "uses_annotation_proxy_noise": True,
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "uses_real_navigation": False,
        "docker_required": False,
        "docker_reason": "This profile is a repository-local artifact transform over annotation candidates; real detector/open-vocabulary paper-body implementation remains Docker-required.",
        "grid_path_recomputed_for_centroid_jitter": False,
        "grid_path_note": "E002 grid reachability is reused by instance id; occupancy-grid path costs are not recomputed after centroid jitter.",
        "significant_moved_routine_task_centroid_jitter_metrics": sig_routine_task,
        "significant_moved_routine_reachable_centroid_jitter_metrics": sig_routine_reachable,
        "significant_moved_routine_task_threshold_exceeded_metrics": sig_routine_exceeds_task,
        "failure_type_counts": counter_dict(Counter(row["failure_type"] for row in failure_rows)),
        "next_recommended_unit": "E003-M11_centroid_jitter_failure_boundary_v0",
        "outputs": {
            "noise_manifest": str(out_dir / "noise_manifest.jsonl"),
            "noisy_query_rows": str(out_dir / "noisy_query_rows.jsonl"),
            "noisy_candidate_rows": str(out_dir / "noisy_candidate_rows.jsonl"),
            "predictions": str(out_dir / "predictions.jsonl"),
            "failure_rows": str(out_dir / "failure_rows.jsonl"),
            "metrics": str(out_dir / "metrics.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], out_dir: Path) -> str:
    clean_task = metrics["profiles"][REFERENCE_PROFILE]["all_rows"]["significant_moved"]["routine_fetch"][
        "task_conditioned_budget_v0"
    ]
    jitter_task = coverage["significant_moved_routine_task_centroid_jitter_metrics"]
    jitter_reachable = coverage["significant_moved_routine_reachable_centroid_jitter_metrics"]
    jitter_exceeds_task = coverage["significant_moved_routine_task_threshold_exceeded_metrics"]
    jitter_always_top5 = metrics["profiles"][CENTROID_JITTER_PROFILE]["all_rows"]["significant_moved"][
        "routine_fetch"
    ]["always_top5"]
    jitter_oracle = metrics["profiles"][CENTROID_JITTER_PROFILE]["all_rows"]["significant_moved"][
        "routine_fetch"
    ]["oracle_current_target"]
    summary = coverage["manifest_summary"][CENTROID_JITTER_PROFILE]
    lines = [
        "# E003-M10 Annotation Centroid Jitter",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input query rows: {coverage['input_query_rows']}",
        f"- Input candidate rows: {coverage['input_candidate_rows']}",
        f"- Centroid jitter seeds: {', '.join(str(seed) for seed in coverage['centroid_jitter_seeds'])}",
        f"- Planar sigma m: {coverage['planar_sigma_m']}",
        f"- Max planar jitter m: {coverage['max_planar_jitter_m']}",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Target rank changed rows: {summary['target_rank_changed_rows']} / {summary['rows']}",
        f"- Target jitter exceeds threshold rows: {summary['target_jitter_exceeds_threshold_rows']} / {summary['rows']}",
        f"- Mean target centroid jitter m: {summary['mean_target_centroid_jitter_m']}",
        f"- Mean target planar jitter m: {summary['mean_target_planar_jitter_m']}",
        f"- Grid path recomputed for centroid jitter: {coverage['grid_path_recomputed_for_centroid_jitter']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch`",
        "",
        "| Profile | Policy | rows | identity `SR` | localization `SR` | target jitter exceed rate | rank changed rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| clean | `task_conditioned_budget_v0` | {clean_task['rows']} | {clean_task['identity_proxy_sr']} | {clean_task['localization_proxy_sr']} | {clean_task['target_jitter_exceeds_threshold_rate']} | {clean_task['target_rank_changed_rate']} | {clean_task['mean_expected_search_cost']} | {clean_task['attempt_spl_proxy']} | {clean_task['mean_task_utility']} |",
        f"| centroid-jitter | `task_conditioned_budget_v0` | {jitter_task['rows']} | {jitter_task['identity_proxy_sr']} | {jitter_task['localization_proxy_sr']} | {jitter_task['target_jitter_exceeds_threshold_rate']} | {jitter_task['target_rank_changed_rate']} | {jitter_task['mean_expected_search_cost']} | {jitter_task['attempt_spl_proxy']} | {jitter_task['mean_task_utility']} |",
        f"| centroid-jitter | `reachable_first_task_conditioned_budget_v0` | {jitter_reachable['rows']} | {jitter_reachable['identity_proxy_sr']} | {jitter_reachable['localization_proxy_sr']} | {jitter_reachable['target_jitter_exceeds_threshold_rate']} | {jitter_reachable['target_rank_changed_rate']} | {jitter_reachable['mean_expected_search_cost']} | {jitter_reachable['attempt_spl_proxy']} | {jitter_reachable['mean_task_utility']} |",
        f"| centroid-jitter | `always_top5` | {jitter_always_top5['rows']} | {jitter_always_top5['identity_proxy_sr']} | {jitter_always_top5['localization_proxy_sr']} | {jitter_always_top5['target_jitter_exceeds_threshold_rate']} | {jitter_always_top5['target_rank_changed_rate']} | {jitter_always_top5['mean_expected_search_cost']} | {jitter_always_top5['attempt_spl_proxy']} | {jitter_always_top5['mean_task_utility']} |",
        f"| centroid-jitter | `oracle_current_target` | {jitter_oracle['rows']} | {jitter_oracle['identity_proxy_sr']} | {jitter_oracle['localization_proxy_sr']} | {jitter_oracle['target_jitter_exceeds_threshold_rate']} | {jitter_oracle['target_rank_changed_rate']} | {jitter_oracle['mean_expected_search_cost']} | {jitter_oracle['attempt_spl_proxy']} | {jitter_oracle['mean_task_utility']} |",
        "",
        "## Threshold-Exceeded Subset",
        "",
        f"- Significant moved `routine_fetch` `task_conditioned_budget_v0` threshold-exceeded rows: {jitter_exceeds_task['rows']}",
        f"- Threshold-exceeded identity `SR`: {jitter_exceeds_task['identity_proxy_sr']}",
        f"- Threshold-exceeded localization `SR`: {jitter_exceeds_task['localization_proxy_sr']}",
        "",
        "## 논문 주장",
        "",
        "- E003-M10 supports controlled annotation-proxy centroid localization jitter stress evaluation.",
        "- E003-M10 separates identity/rank success from localization success under jittered candidate centroids.",
        "- E003-M10 does not support real RGB-D localization noise or real navigation `SR` / `SPL`.",
        "",
        "## 에이전트 추론",
        "",
        "- Centroid jitter is the missing individual controlled perception-like profile after rank jitter, proposal dropout, and false-positive contamination.",
        "- `localization_proxy_sr` is stricter than identity `SR` because returning the correct target with an over-jittered centroid is not counted as localized success.",
        "- Occupancy-grid path costs are not recomputed after jitter; this run should be followed by a boundary analysis before any combined-noise profile.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M10. Continue to E003-M11 centroid-jitter failure-boundary analysis unless redirected to Dockerized real proposal generation.",
        "",
        "## Outputs",
        "",
        "- `noise_manifest.jsonl`",
        "- `noisy_query_rows.jsonl`",
        "- `noisy_candidate_rows.jsonl`",
        "- `predictions.jsonl`",
        "- `failure_rows.jsonl`",
        "- `metrics.json`",
        "- `coverage.json`",
        "- `report.md`",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e001-m02-dir", type=Path, default=DEFAULT_E001_M02_DIR)
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_rows = load_jsonl(args.e001_m02_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.e001_m02_dir / "candidate_rows.jsonl")
    noisy_query_rows, noisy_candidate_rows, manifest_rows = build_noisy_rows(query_rows, candidate_rows)
    predictions = build_predictions(noisy_query_rows, noisy_candidate_rows, args.grid_dir)
    failure_rows = build_failure_rows(predictions)
    metrics = build_metrics(predictions)
    coverage = build_coverage(
        query_rows,
        candidate_rows,
        noisy_query_rows,
        noisy_candidate_rows,
        manifest_rows,
        predictions,
        failure_rows,
        metrics,
        args.out_dir,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "noise_manifest.jsonl", manifest_rows)
    write_jsonl(args.out_dir / "noisy_query_rows.jsonl", noisy_query_rows)
    write_jsonl(args.out_dir / "noisy_candidate_rows.jsonl", noisy_candidate_rows)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(coverage, metrics, args.out_dir),
        encoding="utf-8",
    )

    jitter_summary = coverage["manifest_summary"][CENTROID_JITTER_PROFILE]
    print(
        json.dumps(
            {
                "status": coverage["status"],
                "noisy_query_rows": coverage["noisy_query_rows"],
                "noisy_candidate_rows": coverage["noisy_candidate_rows"],
                "prediction_rows": coverage["prediction_rows"],
                "target_rank_changed_rows": jitter_summary["target_rank_changed_rows"],
                "target_jitter_exceeds_threshold_rows": jitter_summary[
                    "target_jitter_exceeds_threshold_rows"
                ],
                "significant_moved_routine_task_centroid_jitter": coverage[
                    "significant_moved_routine_task_centroid_jitter_metrics"
                ],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
