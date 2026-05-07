#!/usr/bin/env python3
"""Generate and evaluate E003 annotation-derived false-positive stress rows."""

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
    build_failure_rows,
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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M08_annotation_false_positive_v0"
EVAL_VERSION = "e003_annotation_false_positive_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
FALSE_POSITIVE_PROFILE = "annotation_false_positive_v0"
FALSE_POSITIVE_SEEDS = [31, 37, 41]
MAX_FALSE_POSITIVE_CANDIDATES = 3
MIN_FALSE_POSITIVE_CANDIDATES = 2

SEMANTIC_GROUPS = {
    "seating": {"chair", "stool", "bench", "couch", "sofa", "rocking chair"},
    "surface": {"table", "couch table", "side table", "desk", "stand", "shelf"},
    "container": {"box", "item", "object", "sack", "backpack", "laundry basket", "trash can"},
    "soft": {"pillow", "sack"},
    "utility": {"vacuum", "water heater", "trash can", "drum", "gymnastic ball"},
    "plant": {"plant"},
}


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


def clamp_score(value: float) -> float:
    return min(1.0, max(0.0, value))


def label_groups(label: str) -> set[str]:
    return {name for name, labels in SEMANTIC_GROUPS.items() if label in labels}


def semantic_relation(query_label: str, candidate_label: str) -> tuple[str, float]:
    if query_label == candidate_label:
        return "same_label", 1.0
    if label_groups(query_label) & label_groups(candidate_label):
        return "same_semantic_group", 0.82
    return "scene_distractor_fallback", 0.55


def noisy_row_uid(row_uid: str, profile_id: str, seed: int | None = None) -> str:
    if seed is None:
        return f"{row_uid}::noise={profile_id}"
    return f"{row_uid}::noise={profile_id}::seed={seed}"


def build_query_row(
    row: dict[str, Any],
    profile_id: str,
    role: str,
    seed: int | None,
    manifest: dict[str, Any] | None,
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
    output["false_positive_added_count"] = 0 if manifest is None else manifest["false_positive_added_count"]
    output["false_positive_available_count"] = 0 if manifest is None else manifest["false_positive_available_count"]
    output["target_pushed_down_by_false_positive"] = False if manifest is None else manifest["target_pushed_down_by_false_positive"]
    output["false_positive_above_target_count"] = 0 if manifest is None else manifest["false_positive_above_target_count"]
    return output


def build_candidate_output(
    row: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    profile_id: str,
    role: str,
    seed: int | None,
    added_by_noise: bool,
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
    output["original_candidate_rank_non_persistent"] = row.get("candidate_rank_non_persistent")
    output["original_candidate_score_non_persistent"] = row.get("candidate_score_non_persistent")
    output["candidate_score_noise_delta"] = 0.0
    output["candidate_retained_by_noise"] = True
    output["candidate_added_by_noise"] = added_by_noise
    output["candidate_false_positive_source"] = None
    return output


def rank_candidates(rows: list[dict[str, Any]], profile_id: str) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row["candidate_score_non_persistent"]),
            int(row["original_candidate_rank_non_persistent"])
            if row["original_candidate_rank_non_persistent"] is not None
            else 9999,
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{profile_id}_ranked_candidates"
    return ranked


def build_clean_candidates(
    original_row_uid: str,
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_uid = noisy_row_uid(original_row_uid, REFERENCE_PROFILE)
    rows = [
        build_candidate_output(
            row,
            original_row_uid,
            row_uid,
            REFERENCE_PROFILE,
            "clean_reference",
            None,
            False,
        )
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
        "candidate_rows_original": len(candidates),
        "candidate_rows_noisy": len(ranked),
        "candidate_rows_added": 0,
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_rank_original": target_rank,
        "target_rank_noisy": target_rank,
        "target_rank_delta": 0,
        "false_positive_available_count": 0,
        "false_positive_added_count": 0,
        "same_label_false_positive_count": 0,
        "semantic_group_false_positive_count": 0,
        "fallback_false_positive_count": 0,
        "false_positive_above_target_count": 0,
        "target_pushed_down_by_false_positive": False,
        "added_candidate_label_counts": {},
    }


def unique_candidate_pool(candidate_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_rescan: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in candidate_rows:
        key = str(row["candidate_instance_id"])
        current = by_rescan[row["rescan_id"]].get(key)
        if current is None:
            by_rescan[row["rescan_id"]][key] = row
    return {rescan_id: list(items.values()) for rescan_id, items in by_rescan.items()}


def desired_false_positive_count(candidates: list[dict[str, Any]]) -> int:
    original_count = len(candidates)
    if original_count <= 1:
        return MIN_FALSE_POSITIVE_CANDIDATES
    if original_count <= 3:
        return MIN_FALSE_POSITIVE_CANDIDATES
    return MAX_FALSE_POSITIVE_CANDIDATES


def score_distractor(
    query_row: dict[str, Any],
    source_row: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    relation, semantic_score = semantic_relation(query_row["object_label"], source_row["candidate_label"])
    distance = point_distance(query_row["old_scene_aligned_centroid"], source_row["candidate_centroid"])
    distance_score = 1.0 / (1.0 + distance)
    rng = deterministic_rng(
        seed,
        query_row["base_row_uid"],
        str(source_row["candidate_instance_id"]),
        FALSE_POSITIVE_PROFILE,
    )
    jitter = rng.uniform(-0.035, 0.035)
    score = clamp_score(0.55 * semantic_score + 0.45 * distance_score + jitter)
    return {
        "source_row": source_row,
        "semantic_relation": relation,
        "semantic_score": round6(semantic_score),
        "distance_from_old_m": round6(distance),
        "distance_score": round6(distance_score),
        "false_positive_score": round6(score),
    }


def select_false_positives(
    query_row: dict[str, Any],
    candidates: list[dict[str, Any]],
    pool_by_rescan: dict[str, list[dict[str, Any]]],
    seed: int,
) -> tuple[list[dict[str, Any]], int]:
    existing_ids = {str(row["candidate_instance_id"]) for row in candidates}
    raw_pool = [
        row
        for row in pool_by_rescan.get(query_row["rescan_id"], [])
        if str(row["candidate_instance_id"]) not in existing_ids
    ]
    scored = [score_distractor(query_row, row, seed) for row in raw_pool]
    scored.sort(
        key=lambda item: (
            item["semantic_relation"] == "scene_distractor_fallback",
            -float(item["false_positive_score"]),
            float(item["distance_from_old_m"]),
            instance_key(item["source_row"]["candidate_instance_id"]),
        )
    )
    desired = min(desired_false_positive_count(candidates), len(scored))
    return scored[:desired], len(scored)


def build_false_positive_candidate(
    query_row: dict[str, Any],
    source: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    seed: int,
    index: int,
) -> dict[str, Any]:
    source_row = source["source_row"]
    output = dict(source_row)
    output["base_row_uid"] = query_row["base_row_uid"]
    output["pair_uid"] = query_row["pair_uid"]
    output["reference_scan_id"] = query_row["reference_scan_id"]
    output["rescan_id"] = query_row["rescan_id"]
    output["metadata_split"] = query_row["metadata_split"]
    output["object_instance_id_ref"] = query_row["object_instance_id_ref"]
    output["object_label"] = query_row["object_label"]
    output["same_label_candidate_count"] = query_row["same_label_candidate_count"]
    output["ambiguity_band"] = query_row["ambiguity_band"]
    output["task_context_id"] = query_row["task_context_id"]
    output["candidate_is_target"] = False
    output["candidate_score_semantic"] = source["semantic_score"]
    output["candidate_score_non_persistent"] = source["false_positive_score"]
    output["candidate_rank_semantic"] = 9999
    output["candidate_rank_non_persistent"] = 9999
    output["candidate_visit_order_index"] = 9999
    output["candidate_visit_policy"] = f"{FALSE_POSITIVE_PROFILE}_unranked_added_candidate"
    output["candidate_euclidean_cost_from_old_m"] = source["distance_from_old_m"]
    output["candidate_path_cost_m"] = None
    output["candidate_proposal_confidence"] = source["false_positive_score"]
    output = build_candidate_output(
        output,
        original_row_uid,
        noisy_uid,
        FALSE_POSITIVE_PROFILE,
        "controlled_candidate_contamination_stress",
        seed,
        True,
    )
    output["original_candidate_rank_non_persistent"] = None
    output["original_candidate_score_non_persistent"] = None
    output["candidate_false_positive_source"] = "same_rescan_annotation_candidate_pool"
    output["candidate_false_positive_index"] = index
    output["candidate_false_positive_relation"] = source["semantic_relation"]
    output["candidate_added_label"] = source_row["candidate_label"]
    return output


def build_false_positive_candidates(
    query_row: dict[str, Any],
    candidates: list[dict[str, Any]],
    pool_by_rescan: dict[str, list[dict[str, Any]]],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original_row_uid = query_row["row_uid"]
    row_uid = noisy_row_uid(original_row_uid, FALSE_POSITIVE_PROFILE, seed)
    retained = [
        build_candidate_output(
            row,
            original_row_uid,
            row_uid,
            FALSE_POSITIVE_PROFILE,
            "controlled_candidate_contamination_stress",
            seed,
            False,
        )
        for row in candidates
    ]
    selected, available_count = select_false_positives(query_row, candidates, pool_by_rescan, seed)
    added = [
        build_false_positive_candidate(query_row, source, original_row_uid, row_uid, seed, index)
        for index, source in enumerate(selected, start=1)
    ]
    ranked = rank_candidates(retained + added, FALSE_POSITIVE_PROFILE)
    target_rows = [row for row in ranked if row["candidate_is_target"]]
    target_rank_noisy = target_rows[0]["candidate_rank_non_persistent"] if target_rows else None
    original_target_rows = [row for row in candidates if row["candidate_is_target"]]
    target_rank_original = (
        int(original_target_rows[0]["candidate_rank_non_persistent"]) if original_target_rows else None
    )
    false_positive_above_target = [
        row
        for row in ranked
        if row["candidate_added_by_noise"]
        and target_rank_noisy is not None
        and int(row["candidate_rank_non_persistent"]) < int(target_rank_noisy)
    ]
    relation_counts = Counter(row["candidate_false_positive_relation"] for row in added)
    label_counts = Counter(row["candidate_label"] for row in added)
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": FALSE_POSITIVE_PROFILE,
        "proposal_noise_seed": seed,
        "candidate_rows_original": len(candidates),
        "candidate_rows_noisy": len(ranked),
        "candidate_rows_added": len(added),
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_rank_original": target_rank_original,
        "target_rank_noisy": target_rank_noisy,
        "target_rank_delta": target_rank_noisy - target_rank_original
        if target_rank_noisy is not None and target_rank_original is not None
        else None,
        "false_positive_available_count": available_count,
        "false_positive_added_count": len(added),
        "same_label_false_positive_count": relation_counts["same_label"],
        "semantic_group_false_positive_count": relation_counts["same_semantic_group"],
        "fallback_false_positive_count": relation_counts["scene_distractor_fallback"],
        "false_positive_above_target_count": len(false_positive_above_target),
        "target_pushed_down_by_false_positive": bool(
            target_rank_noisy is not None
            and target_rank_original is not None
            and target_rank_noisy > target_rank_original
        ),
        "added_candidate_label_counts": counter_dict(label_counts),
        "max_false_positive_candidates": MAX_FALSE_POSITIVE_CANDIDATES,
        "min_false_positive_candidates": MIN_FALSE_POSITIVE_CANDIDATES,
    }


def build_noisy_rows(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_uid = group_by_uid(candidate_rows)
    pool_by_rescan = unique_candidate_pool(candidate_rows)
    noisy_query_rows: list[dict[str, Any]] = []
    noisy_candidate_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for row in query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        clean_candidates, clean_manifest = build_clean_candidates(row["row_uid"], candidates)
        noisy_query_rows.append(
            build_query_row(row, REFERENCE_PROFILE, "clean_reference", None, clean_manifest)
        )
        noisy_candidate_rows.extend(clean_candidates)
        manifest_rows.append(clean_manifest)

    for seed in FALSE_POSITIVE_SEEDS:
        for row in query_rows:
            candidates = candidates_by_uid.get(row["row_uid"], [])
            noisy_candidates, manifest = build_false_positive_candidates(
                row,
                candidates,
                pool_by_rescan,
                seed,
            )
            noisy_query_rows.append(
                build_query_row(
                    row,
                    FALSE_POSITIVE_PROFILE,
                    "controlled_candidate_contamination_stress",
                    seed,
                    manifest,
                )
            )
            noisy_candidate_rows.extend(noisy_candidates)
            manifest_rows.append(manifest)

    return noisy_query_rows, noisy_candidate_rows, manifest_rows


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
            prediction["false_positive_added_count"] = int(row["false_positive_added_count"])
            prediction["false_positive_available_count"] = int(row["false_positive_available_count"])
            prediction["target_pushed_down_by_false_positive"] = bool(
                row["target_pushed_down_by_false_positive"]
            )
            prediction["false_positive_above_target_count"] = int(
                row["false_positive_above_target_count"]
            )
            predictions.append(prediction)
    return predictions


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def denominator_rows(rows: list[dict[str, Any]], denominator: str) -> list[dict[str, Any]]:
    if denominator == "all_rows":
        return rows
    if denominator == "false_positive_added_eval":
        return [row for row in rows if int(row["false_positive_added_count"]) > 0]
    if denominator == "target_pushed_down_eval":
        return [row for row in rows if row["target_pushed_down_by_false_positive"]]
    if denominator == "no_false_positive_available_eval":
        return [
            row
            for row in rows
            if int(row["false_positive_added_count"]) == 0
            and int(row["false_positive_available_count"]) == 0
        ]
    raise RuntimeError(f"unknown denominator: {denominator}")


def summarize_prediction_rows(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    success_rate = safe_rate(sum(1 for row in rows if row["search_success"]), len(rows))
    returned_mean = mean([float(row["returned_location_count"]) for row in rows])
    return {
        "subset": subset,
        "rows": len(rows),
        "target_retained_rate": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
        "false_positive_added_rate": safe_rate(
            sum(1 for row in rows if int(row["false_positive_added_count"]) > 0),
            len(rows),
        ),
        "target_pushed_down_rate": safe_rate(
            sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
            len(rows),
        ),
        "mean_false_positive_added_count": mean([float(row["false_positive_added_count"]) for row in rows]),
        "mean_false_positive_above_target_count": mean(
            [float(row["false_positive_above_target_count"]) for row in rows]
        ),
        "proxy_sr": success_rate,
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
    }


def summarize_by_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    denominators = [
        "all_rows",
        "false_positive_added_eval",
        "target_pushed_down_eval",
        "no_false_positive_available_eval",
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
        "false_positive_seeds": {},
    }
    for profile in [REFERENCE_PROFILE, FALSE_POSITIVE_PROFILE]:
        profile_rows = [row for row in predictions if row["proposal_noise_profile_id"] == profile]
        metrics["profiles"][profile] = summarize_by_policy(profile_rows)
    for seed in FALSE_POSITIVE_SEEDS:
        seed_rows = [
            row
            for row in predictions
            if row["proposal_noise_profile_id"] == FALSE_POSITIVE_PROFILE
            and row["proposal_noise_seed"] == seed
        ]
        metrics["false_positive_seeds"][str(seed)] = summarize_by_policy(seed_rows)
    return metrics


def matched_clean_prediction_rows(
    predictions: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    clean_index = {
        (row["original_row_uid"], row["policy"]): row
        for row in predictions
        if row["proposal_noise_profile_id"] == REFERENCE_PROFILE
    }
    return [clean_index[(row["original_row_uid"], row["policy"])] for row in stress_rows]


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
            "false_positive_available_rows": sum(
                1 for row in rows if int(row["false_positive_available_count"]) > 0
            ),
            "false_positive_added_rows": sum(
                1 for row in rows if int(row["false_positive_added_count"]) > 0
            ),
            "target_pushed_down_rows": sum(
                1 for row in rows if row["target_pushed_down_by_false_positive"]
            ),
            "target_pushed_down_rate": safe_rate(
                sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
                len(rows),
            ),
            "mean_candidate_rows_original": mean([float(row["candidate_rows_original"]) for row in rows]),
            "mean_candidate_rows_noisy": mean([float(row["candidate_rows_noisy"]) for row in rows]),
            "mean_candidate_rows_added": mean([float(row["candidate_rows_added"]) for row in rows]),
            "same_label_false_positive_count": sum(int(row["same_label_false_positive_count"]) for row in rows),
            "semantic_group_false_positive_count": sum(
                int(row["semantic_group_false_positive_count"]) for row in rows
            ),
            "fallback_false_positive_count": sum(int(row["fallback_false_positive_count"]) for row in rows),
            "false_positive_above_target_rows": sum(
                1 for row in rows if int(row["false_positive_above_target_count"]) > 0
            ),
        }
    return output


def enrich_failure_rows(
    failure_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index = {(row["row_uid"], row["policy"]): row for row in predictions}
    output = []
    for row in failure_rows:
        pred = index[(row["row_uid"], row["policy"])]
        item = dict(row)
        item["eval_version"] = EVAL_VERSION
        item["false_positive_added_count"] = pred["false_positive_added_count"]
        item["target_pushed_down_by_false_positive"] = pred["target_pushed_down_by_false_positive"]
        item["false_positive_above_target_count"] = pred["false_positive_above_target_count"]
        item["next_test"] = "false-positive failure-boundary analysis"
        output.append(item)
    return output


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
    false_summary = manifest_summary[FALSE_POSITIVE_PROFILE]
    expected_noisy_query_rows = len(query_rows) * (1 + len(FALSE_POSITIVE_SEEDS))
    significant_routine_task_rows = [
        row
        for row in predictions
        if row["proposal_noise_profile_id"] == FALSE_POSITIVE_PROFILE
        and row["row_band"] == "significant_moved"
        and row["task_context_id"] == "routine_fetch"
        and row["policy"] == "task_conditioned_budget_v0"
        and int(row["false_positive_added_count"]) > 0
    ]
    matched_clean_significant_routine_task = summarize_prediction_rows(
        matched_clean_prediction_rows(predictions, significant_routine_task_rows),
        "significant_moved",
    )
    significant_routine_task = metrics["profiles"][FALSE_POSITIVE_PROFILE]["false_positive_added_eval"][
        "significant_moved"
    ]["routine_fetch"]["task_conditioned_budget_v0"]
    significant_routine_reachable = metrics["profiles"][FALSE_POSITIVE_PROFILE][
        "false_positive_added_eval"
    ]["significant_moved"]["routine_fetch"]["reachable_first_task_conditioned_budget_v0"]
    status = "false_positive_eval_ready"
    if len(noisy_query_rows) != expected_noisy_query_rows:
        status = "review_needed"
    if len(predictions) != len(noisy_query_rows) * len(POLICIES):
        status = "review_needed"
    if false_summary["false_positive_added_rows"] <= 0:
        status = "review_needed"
    if false_summary["target_retained_rate"] != 1.0:
        status = "review_needed"
    return {
        "eval_version": EVAL_VERSION,
        "status": status,
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "profiles": [REFERENCE_PROFILE, FALSE_POSITIVE_PROFILE],
        "false_positive_seeds": FALSE_POSITIVE_SEEDS,
        "max_false_positive_candidates": MAX_FALSE_POSITIVE_CANDIDATES,
        "min_false_positive_candidates": MIN_FALSE_POSITIVE_CANDIDATES,
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
        "matched_clean_significant_moved_routine_task_metrics": matched_clean_significant_routine_task,
        "significant_moved_routine_task_false_positive_metrics": significant_routine_task,
        "significant_moved_routine_reachable_false_positive_metrics": significant_routine_reachable,
        "failure_type_counts": counter_dict(Counter(row["failure_type"] for row in failure_rows)),
        "next_recommended_unit": "E003-M09_false_positive_failure_boundary_v0",
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
    clean_task = coverage["matched_clean_significant_moved_routine_task_metrics"]
    false_task = coverage["significant_moved_routine_task_false_positive_metrics"]
    false_reachable = coverage["significant_moved_routine_reachable_false_positive_metrics"]
    false_always_top5 = metrics["profiles"][FALSE_POSITIVE_PROFILE]["false_positive_added_eval"][
        "significant_moved"
    ]["routine_fetch"]["always_top5"]
    false_oracle = metrics["profiles"][FALSE_POSITIVE_PROFILE]["false_positive_added_eval"][
        "significant_moved"
    ]["routine_fetch"]["oracle_current_target"]
    summary = coverage["manifest_summary"][FALSE_POSITIVE_PROFILE]
    lines = [
        "# E003-M08 Annotation False Positive Stress",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input query rows: {coverage['input_query_rows']}",
        f"- Input candidate rows: {coverage['input_candidate_rows']}",
        f"- False-positive seeds: {', '.join(str(seed) for seed in coverage['false_positive_seeds'])}",
        f"- Max false-positive candidates per row: {coverage['max_false_positive_candidates']}",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- False-positive added rows: {summary['false_positive_added_rows']} / {summary['rows']}",
        f"- Target pushed-down rows: {summary['target_pushed_down_rows']} / {summary['rows']}",
        f"- Same-label false positives: {summary['same_label_false_positive_count']}",
        f"- Semantic-group false positives: {summary['semantic_group_false_positive_count']}",
        f"- Fallback false positives: {summary['fallback_false_positive_count']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch`",
        "",
        "| Profile | Policy | rows | proxy `SR` | target retained | FP added rate | target pushed-down rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| matched clean | `task_conditioned_budget_v0` | {clean_task['rows']} | {clean_task['proxy_sr']} | {clean_task['target_retained_rate']} | {clean_task['false_positive_added_rate']} | {clean_task['target_pushed_down_rate']} | {clean_task['mean_expected_search_cost']} | {clean_task['attempt_spl_proxy']} | {clean_task['mean_task_utility']} |",
        f"| false-positive | `task_conditioned_budget_v0` | {false_task['rows']} | {false_task['proxy_sr']} | {false_task['target_retained_rate']} | {false_task['false_positive_added_rate']} | {false_task['target_pushed_down_rate']} | {false_task['mean_expected_search_cost']} | {false_task['attempt_spl_proxy']} | {false_task['mean_task_utility']} |",
        f"| false-positive | `reachable_first_task_conditioned_budget_v0` | {false_reachable['rows']} | {false_reachable['proxy_sr']} | {false_reachable['target_retained_rate']} | {false_reachable['false_positive_added_rate']} | {false_reachable['target_pushed_down_rate']} | {false_reachable['mean_expected_search_cost']} | {false_reachable['attempt_spl_proxy']} | {false_reachable['mean_task_utility']} |",
        f"| false-positive | `always_top5` | {false_always_top5['rows']} | {false_always_top5['proxy_sr']} | {false_always_top5['target_retained_rate']} | {false_always_top5['false_positive_added_rate']} | {false_always_top5['target_pushed_down_rate']} | {false_always_top5['mean_expected_search_cost']} | {false_always_top5['attempt_spl_proxy']} | {false_always_top5['mean_task_utility']} |",
        f"| false-positive | `oracle_current_target` | {false_oracle['rows']} | {false_oracle['proxy_sr']} | {false_oracle['target_retained_rate']} | {false_oracle['false_positive_added_rate']} | {false_oracle['target_pushed_down_rate']} | {false_oracle['mean_expected_search_cost']} | {false_oracle['attempt_spl_proxy']} | {false_oracle['mean_task_utility']} |",
        "",
        "## 논문 주장",
        "",
        "- E003-M08 supports controlled annotation-derived false-positive contamination stress evaluation.",
        "- E003-M08 keeps target presence fixed, so failures are ranking/budget contamination failures rather than proposal-recall failures.",
        "- E003-M08 does not support real RGB-D or open-vocabulary detector hallucination robustness.",
        "",
        "## 에이전트 추론",
        "",
        "- False-positive contamination complements dropout because it adds distractors instead of removing them.",
        "- Positive or negative effects must be separated from real detector hallucination claims because all added candidates still come from annotation-derived object candidates.",
        "- The next unit should analyze false-positive failure boundaries before combining dropout, false positives, and centroid jitter.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M08. Continue to E003-M09 false-positive failure-boundary analysis unless redirected to Dockerized real proposal generation.",
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
    noisy_query_rows, noisy_candidate_rows, manifest_rows = build_noisy_rows(
        query_rows,
        candidate_rows,
    )
    predictions = build_predictions(noisy_query_rows, noisy_candidate_rows, args.grid_dir)
    failure_rows = enrich_failure_rows(build_failure_rows(predictions), predictions)
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

    false_summary = coverage["manifest_summary"][FALSE_POSITIVE_PROFILE]
    print(
        json.dumps(
            {
                "status": coverage["status"],
                "noisy_query_rows": coverage["noisy_query_rows"],
                "noisy_candidate_rows": coverage["noisy_candidate_rows"],
                "prediction_rows": coverage["prediction_rows"],
                "false_positive_added_rows": false_summary["false_positive_added_rows"],
                "target_pushed_down_rows": false_summary["target_pushed_down_rows"],
                "significant_moved_routine_task_false_positive": coverage[
                    "significant_moved_routine_task_false_positive_metrics"
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
