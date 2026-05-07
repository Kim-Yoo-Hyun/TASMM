#!/usr/bin/env python3
"""Generate and evaluate E003 annotation combined-moderate stress rows."""

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
DEFAULT_CONTRACT = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E003-M12_combined_noise_route_decision_v0"
    / "combined_profile_contract.json"
)
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M13_annotation_combined_moderate_v0"
EVAL_VERSION = "e003_annotation_combined_moderate_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
COMBINED_PROFILE = "annotation_combined_moderate_v0"

SEMANTIC_GROUPS = {
    "seating": {"chair", "stool", "bench", "couch", "sofa", "rocking chair"},
    "surface": {"table", "couch table", "side table", "desk", "stand", "shelf"},
    "container": {"box", "item", "object", "sack", "backpack", "laundry basket", "trash can"},
    "soft": {"pillow", "sack"},
    "utility": {"vacuum", "water heater", "trash can", "drum", "gymnastic ball"},
    "plant": {"plant"},
}


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


def clamp_score(value: float) -> float:
    return min(1.0, max(0.0, value))


def clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


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


def contract_params(contract: dict[str, Any]) -> dict[str, Any]:
    params = contract["moderate_noise_parameters"]
    return {
        "seed_set": [int(seed) for seed in contract["seed_set"]],
        "score_jitter_sigma": float(params["score_jitter_sigma"]),
        "target_drop_rate": float(params["target_drop_rate"]),
        "non_target_candidate_drop_rate": float(params["non_target_candidate_drop_rate"]),
        "min_false_positive_candidates": int(params["min_false_positive_candidates"]),
        "max_false_positive_candidates": int(params["max_false_positive_candidates"]),
        "centroid_planar_sigma_m": float(params["centroid_planar_sigma_m"]),
        "centroid_z_sigma_m": float(params["centroid_z_sigma_m"]),
        "max_planar_jitter_m": float(params["max_planar_jitter_m"]),
        "max_z_jitter_m": float(params["max_z_jitter_m"]),
        "preserve_at_least_one_candidate": bool(params["preserve_at_least_one_candidate"]),
    }


def base_candidate_output(
    row: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    profile_id: str,
    role: str,
    seed: int | None,
    *,
    retained: bool = True,
    drop_reason: str | None = None,
    added_by_noise: bool = False,
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
    output["original_candidate_centroid"] = row.get("candidate_centroid")
    output["candidate_retained_by_noise"] = retained
    output["candidate_drop_reason"] = drop_reason
    output["candidate_added_by_noise"] = added_by_noise
    output["candidate_false_positive_source"] = None
    output["candidate_false_positive_relation"] = None
    output["candidate_score_noise_delta"] = 0.0
    output["candidate_combined_score_jitter_delta"] = 0.0
    output["candidate_centroid_jitter_delta"] = [0.0, 0.0, 0.0]
    output["candidate_centroid_jitter_m"] = 0.0
    output["candidate_planar_jitter_m"] = 0.0
    output["grid_path_recomputed_for_centroid_jitter"] = False
    return output


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
    output["proposal_noise_target_policy"] = "combined_moderate" if profile_id == COMBINED_PROFILE else "preserve_target"
    output["current_proposal_source"] = "annotation_semseg_noisy_proxy"
    output["observation_source"] = "annotation_semseg_noisy_proxy"
    output["uses_real_rgbd_perception"] = False
    output["uses_open_vocab_perception"] = False
    for key in [
        "target_dropped_by_noise",
        "target_drop_forced_retained",
        "forced_non_target_retained",
        "false_positive_added_count",
        "false_positive_available_count",
        "false_positive_above_target_count",
        "target_pushed_down_by_false_positive",
        "target_rank_changed_by_combined_noise",
        "target_rank_changed_by_centroid_jitter",
        "target_centroid_jitter_m",
        "target_planar_jitter_m",
        "target_jitter_exceeds_success_threshold",
        "grid_path_recomputed_for_centroid_jitter",
    ]:
        output[key] = manifest[key]
    return output


def rank_candidates(rows: list[dict[str, Any]], profile_id: str) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row["candidate_score_non_persistent"]),
            int(row["original_candidate_rank_non_persistent"])
            if row["original_candidate_rank_non_persistent"] is not None
            else 9999,
            float(row["candidate_euclidean_cost_from_old_m"]),
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{profile_id}_ranked_combined_candidates"
    return ranked


def build_clean_candidates(
    original_row_uid: str,
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_uid = noisy_row_uid(original_row_uid, REFERENCE_PROFILE)
    rows = [
        base_candidate_output(
            row,
            original_row_uid,
            row_uid,
            REFERENCE_PROFILE,
            "clean_reference",
            None,
        )
        for row in candidates
    ]
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row["original_candidate_rank_non_persistent"]),
            -float(row["candidate_score_non_persistent"]),
            float(row["candidate_euclidean_cost_from_old_m"]),
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
        "candidate_rows_after_dropout": len(ranked),
        "candidate_rows_noisy": len(ranked),
        "candidate_rows_dropped": 0,
        "candidate_rows_added": 0,
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_drop_forced_retained": False,
        "forced_non_target_retained": False,
        "target_rank_original": target_rank,
        "target_rank_noisy": target_rank,
        "target_rank_delta": 0,
        "target_rank_changed_by_combined_noise": False,
        "target_rank_changed_by_centroid_jitter": False,
        "dropped_target_candidate": False,
        "dropped_non_target_candidate_rows": 0,
        "false_positive_available_count": 0,
        "false_positive_added_count": 0,
        "same_label_false_positive_count": 0,
        "semantic_group_false_positive_count": 0,
        "fallback_false_positive_count": 0,
        "false_positive_above_target_count": 0,
        "target_pushed_down_by_false_positive": False,
        "rank_changed_candidate_rows": 0,
        "score_jitter_sigma": 0.0,
        "target_centroid_jitter_m": 0.0,
        "target_planar_jitter_m": 0.0,
        "target_jitter_exceeds_success_threshold": False,
        "mean_candidate_centroid_jitter_m": 0.0,
        "mean_candidate_planar_jitter_m": 0.0,
        "max_candidate_centroid_jitter_m": 0.0,
        "grid_path_recomputed_for_centroid_jitter": False,
        "added_candidate_label_counts": {},
    }


def unique_candidate_pool(candidate_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_rescan: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in candidate_rows:
        key = str(row["candidate_instance_id"])
        by_rescan[row["rescan_id"]].setdefault(key, row)
    return {rescan_id: list(items.values()) for rescan_id, items in by_rescan.items()}


def should_drop_target(original_row_uid: str, seed: int, drop_rate: float) -> bool:
    rng = deterministic_rng(seed, original_row_uid, "target", COMBINED_PROFILE)
    return rng.random() < drop_rate


def should_drop_non_target(
    original_row_uid: str,
    candidate_instance_id: Any,
    seed: int,
    drop_rate: float,
) -> bool:
    rng = deterministic_rng(seed, original_row_uid, str(candidate_instance_id), "non_target", COMBINED_PROFILE)
    return rng.random() < drop_rate


def apply_dropout(
    original_row_uid: str,
    row_uid: str,
    candidates: list[dict[str, Any]],
    seed: int,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target_rows = [row for row in candidates if row["candidate_is_target"]]
    non_target_rows = [row for row in candidates if not row["candidate_is_target"]]
    drop_target = bool(target_rows) and should_drop_target(original_row_uid, seed, params["target_drop_rate"])
    retained: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    for row in candidates:
        if row["candidate_is_target"]:
            is_dropped = drop_target
            reason = "target_dropout" if is_dropped else None
        else:
            is_dropped = should_drop_non_target(
                original_row_uid,
                row["candidate_instance_id"],
                seed,
                params["non_target_candidate_drop_rate"],
            )
            reason = "non_target_dropout" if is_dropped else None
        output = base_candidate_output(
            row,
            original_row_uid,
            row_uid,
            COMBINED_PROFILE,
            "combined_moderate_dropout_stage",
            seed,
            retained=not is_dropped,
            drop_reason=reason,
        )
        if is_dropped:
            dropped.append(output)
        else:
            retained.append(output)

    forced_target_retained = False
    forced_non_target_retained = False
    if not retained and params["preserve_at_least_one_candidate"]:
        if non_target_rows:
            best_non_target = min(non_target_rows, key=lambda row: int(row["candidate_rank_non_persistent"]))
            retained.append(
                base_candidate_output(
                    best_non_target,
                    original_row_uid,
                    row_uid,
                    COMBINED_PROFILE,
                    "combined_moderate_forced_non_target_keep",
                    seed,
                    retained=True,
                    drop_reason="forced_keep_to_preserve_candidate",
                )
            )
            forced_non_target_retained = True
        elif target_rows:
            best_target = min(target_rows, key=lambda row: int(row["candidate_rank_non_persistent"]))
            retained.append(
                base_candidate_output(
                    best_target,
                    original_row_uid,
                    row_uid,
                    COMBINED_PROFILE,
                    "combined_moderate_forced_target_keep",
                    seed,
                    retained=True,
                    drop_reason="forced_keep_to_preserve_candidate",
                )
            )
            forced_target_retained = True

    retained_target_rows = [row for row in retained if row["candidate_is_target"]]
    return retained, {
        "candidate_rows_original": len(candidates),
        "candidate_rows_after_dropout": len(retained),
        "candidate_rows_dropped": len(candidates) - len(retained),
        "target_retained_after_dropout": len(retained_target_rows) == 1,
        "target_dropped_by_noise": bool(target_rows) and not retained_target_rows,
        "target_drop_forced_retained": forced_target_retained,
        "forced_non_target_retained": forced_non_target_retained,
        "dropped_target_candidate": bool(target_rows) and not retained_target_rows,
        "dropped_non_target_candidate_rows": len(non_target_rows)
        - sum(1 for row in retained if not row["candidate_is_target"]),
    }


def score_distractor(query_row: dict[str, Any], source_row: dict[str, Any], seed: int) -> dict[str, Any]:
    relation, semantic_score = semantic_relation(query_row["object_label"], source_row["candidate_label"])
    distance = point_distance(query_row["old_scene_aligned_centroid"], source_row["candidate_centroid"])
    distance_score = 1.0 / (1.0 + distance)
    rng = deterministic_rng(
        seed,
        query_row["base_row_uid"],
        str(source_row["candidate_instance_id"]),
        COMBINED_PROFILE,
        "false_positive",
    )
    jitter = rng.uniform(-0.03, 0.03)
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
    original_candidates: list[dict[str, Any]],
    retained_candidates: list[dict[str, Any]],
    pool_by_rescan: dict[str, list[dict[str, Any]]],
    seed: int,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    blocked_ids = {str(row["candidate_instance_id"]) for row in original_candidates}
    blocked_ids |= {str(row["candidate_instance_id"]) for row in retained_candidates}
    raw_pool = [
        row
        for row in pool_by_rescan.get(query_row["rescan_id"], [])
        if str(row["candidate_instance_id"]) not in blocked_ids
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
    desired = params["min_false_positive_candidates"]
    if len(retained_candidates) > 3:
        desired = params["max_false_positive_candidates"]
    return scored[: min(desired, len(scored))], len(scored)


def build_false_positive_candidate(
    query_row: dict[str, Any],
    source: dict[str, Any],
    original_row_uid: str,
    row_uid: str,
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
    output["candidate_visit_policy"] = f"{COMBINED_PROFILE}_unranked_false_positive"
    output["candidate_euclidean_cost_from_old_m"] = source["distance_from_old_m"]
    output["candidate_path_cost_m"] = None
    output["candidate_proposal_confidence"] = source["false_positive_score"]
    output = base_candidate_output(
        output,
        original_row_uid,
        row_uid,
        COMBINED_PROFILE,
        "combined_moderate_false_positive_stage",
        seed,
        retained=True,
        added_by_noise=True,
    )
    output["original_candidate_rank_non_persistent"] = None
    output["original_candidate_score_non_persistent"] = None
    output["candidate_false_positive_source"] = "same_rescan_annotation_candidate_pool"
    output["candidate_false_positive_index"] = index
    output["candidate_false_positive_relation"] = source["semantic_relation"]
    output["candidate_added_label"] = source_row["candidate_label"]
    return output


def apply_score_jitter(row: dict[str, Any], original_row_uid: str, seed: int, sigma: float) -> dict[str, Any]:
    output = dict(row)
    original_score = float(row["candidate_score_non_persistent"])
    rng = deterministic_rng(seed, original_row_uid, str(row["candidate_instance_id"]), "score_jitter", COMBINED_PROFILE)
    delta = rng.gauss(0.0, sigma)
    noisy_score = clamp_score(original_score + delta)
    output["candidate_score_non_persistent"] = round6(noisy_score)
    output["candidate_score_noise_delta"] = round6(delta)
    output["candidate_combined_score_jitter_delta"] = round6(noisy_score - original_score)
    return output


def jitter_delta(
    seed: int,
    original_row_uid: str,
    candidate_instance_id: Any,
    params: dict[str, Any],
) -> list[float]:
    rng = deterministic_rng(seed, original_row_uid, str(candidate_instance_id), "centroid_jitter", COMBINED_PROFILE)
    dx = rng.gauss(0.0, params["centroid_planar_sigma_m"])
    dy = rng.gauss(0.0, params["centroid_planar_sigma_m"])
    planar = math.sqrt(dx * dx + dy * dy)
    if planar > params["max_planar_jitter_m"] and planar > 0.0:
        scale = params["max_planar_jitter_m"] / planar
        dx *= scale
        dy *= scale
    dz = clamp(rng.gauss(0.0, params["centroid_z_sigma_m"]), params["max_z_jitter_m"])
    return [dx, dy, dz]


def apply_centroid_jitter(
    query_row: dict[str, Any],
    row: dict[str, Any],
    original_row_uid: str,
    seed: int,
    params: dict[str, Any],
) -> dict[str, Any]:
    output = dict(row)
    delta = jitter_delta(seed, original_row_uid, row["candidate_instance_id"], params)
    original = [float(value) for value in row["candidate_centroid"]]
    jittered = [original[index] + delta[index] for index in range(3)]
    old = query_row["old_scene_aligned_centroid"]
    distance_from_old = point_distance(old, jittered)
    output["candidate_centroid"] = [round6(value) for value in jittered]
    output["candidate_centroid_jitter_delta"] = [round6(value) for value in delta]
    output["candidate_centroid_jitter_m"] = round6(point_distance(original, jittered))
    output["candidate_planar_jitter_m"] = round6(planar_distance(original, jittered))
    output["candidate_euclidean_cost_from_old_m"] = round6(distance_from_old)
    output["candidate_path_cost_m"] = round6(distance_from_old)
    output["candidate_path_cost_ready"] = True
    output["grid_path_recomputed_for_centroid_jitter"] = False
    return output


def build_combined_candidates(
    query_row: dict[str, Any],
    candidates: list[dict[str, Any]],
    pool_by_rescan: dict[str, list[dict[str, Any]]],
    seed: int,
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original_row_uid = query_row["row_uid"]
    row_uid = noisy_row_uid(original_row_uid, COMBINED_PROFILE, seed)
    original_target_rows = [row for row in candidates if row["candidate_is_target"]]
    target_rank_original = (
        int(original_target_rows[0]["candidate_rank_non_persistent"]) if original_target_rows else None
    )

    retained, dropout_manifest = apply_dropout(original_row_uid, row_uid, candidates, seed, params)
    selected, available_count = select_false_positives(
        query_row,
        candidates,
        retained,
        pool_by_rescan,
        seed,
        params,
    )
    added = [
        build_false_positive_candidate(query_row, source, original_row_uid, row_uid, seed, index)
        for index, source in enumerate(selected, start=1)
    ]
    relation_counts = Counter(row["candidate_false_positive_relation"] for row in added)
    label_counts = Counter(row["candidate_label"] for row in added)

    score_jittered = [
        apply_score_jitter(row, original_row_uid, seed, params["score_jitter_sigma"])
        for row in retained + added
    ]
    centroid_jittered = [
        apply_centroid_jitter(query_row, row, original_row_uid, seed, params)
        for row in score_jittered
    ]
    ranked = rank_candidates(centroid_jittered, COMBINED_PROFILE)
    target_rows = [row for row in ranked if row["candidate_is_target"]]
    target_rank_noisy = target_rows[0]["candidate_rank_non_persistent"] if target_rows else None
    target_jitter = float(target_rows[0]["candidate_centroid_jitter_m"]) if target_rows else None
    target_planar_jitter = float(target_rows[0]["candidate_planar_jitter_m"]) if target_rows else None
    false_positive_above_target = [
        row
        for row in ranked
        if row["candidate_added_by_noise"]
        and target_rank_noisy is not None
        and int(row["candidate_rank_non_persistent"]) < int(target_rank_noisy)
    ]
    rank_changed_rows = [
        row
        for row in ranked
        if row["original_candidate_rank_non_persistent"] is not None
        and int(row["candidate_rank_non_persistent"]) != int(row["original_candidate_rank_non_persistent"])
    ]
    jitter_values = [float(row["candidate_centroid_jitter_m"]) for row in ranked]
    planar_values = [float(row["candidate_planar_jitter_m"]) for row in ranked]
    target_rank_delta = (
        target_rank_noisy - target_rank_original
        if target_rank_noisy is not None and target_rank_original is not None
        else None
    )
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": COMBINED_PROFILE,
        "proposal_noise_seed": seed,
        "candidate_rows_original": len(candidates),
        "candidate_rows_after_dropout": dropout_manifest["candidate_rows_after_dropout"],
        "candidate_rows_noisy": len(ranked),
        "candidate_rows_dropped": dropout_manifest["candidate_rows_dropped"],
        "candidate_rows_added": len(added),
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": dropout_manifest["target_dropped_by_noise"],
        "target_drop_forced_retained": dropout_manifest["target_drop_forced_retained"],
        "forced_non_target_retained": dropout_manifest["forced_non_target_retained"],
        "target_rank_original": target_rank_original,
        "target_rank_noisy": target_rank_noisy,
        "target_rank_delta": target_rank_delta,
        "target_rank_changed_by_combined_noise": target_rank_delta not in {0, None},
        "target_rank_changed_by_centroid_jitter": False,
        "dropped_target_candidate": dropout_manifest["dropped_target_candidate"],
        "dropped_non_target_candidate_rows": dropout_manifest["dropped_non_target_candidate_rows"],
        "false_positive_available_count": available_count,
        "false_positive_added_count": len(added),
        "same_label_false_positive_count": relation_counts["same_label"],
        "semantic_group_false_positive_count": relation_counts["same_semantic_group"],
        "fallback_false_positive_count": relation_counts["scene_distractor_fallback"],
        "false_positive_above_target_count": len(false_positive_above_target),
        "target_pushed_down_by_false_positive": bool(
            false_positive_above_target
            and target_rank_noisy is not None
            and target_rank_original is not None
            and target_rank_noisy > target_rank_original
        ),
        "rank_changed_candidate_rows": len(rank_changed_rows),
        "score_jitter_sigma": params["score_jitter_sigma"],
        "target_centroid_jitter_m": round6(target_jitter),
        "target_planar_jitter_m": round6(target_planar_jitter),
        "target_jitter_exceeds_success_threshold": bool(
            target_jitter is not None and target_jitter > float(query_row["success_threshold_m"])
        ),
        "mean_candidate_centroid_jitter_m": mean(jitter_values),
        "mean_candidate_planar_jitter_m": mean(planar_values),
        "max_candidate_centroid_jitter_m": round6(max(jitter_values)) if jitter_values else None,
        "grid_path_recomputed_for_centroid_jitter": False,
        "added_candidate_label_counts": counter_dict(label_counts),
        "target_drop_rate": params["target_drop_rate"],
        "non_target_candidate_drop_rate": params["non_target_candidate_drop_rate"],
        "min_false_positive_candidates": params["min_false_positive_candidates"],
        "max_false_positive_candidates": params["max_false_positive_candidates"],
        "centroid_planar_sigma_m": params["centroid_planar_sigma_m"],
        "max_planar_jitter_m": params["max_planar_jitter_m"],
    }


def build_noisy_rows(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_uid = group_by_uid(candidate_rows)
    pool_by_rescan = unique_candidate_pool(candidate_rows)
    params = contract_params(contract)
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

    for seed in params["seed_set"]:
        for row in query_rows:
            candidates = candidates_by_uid.get(row["row_uid"], [])
            combined_candidates, manifest = build_combined_candidates(
                row,
                candidates,
                pool_by_rescan,
                seed,
                params,
            )
            noisy_query_rows.append(
                build_query_row(
                    row,
                    COMBINED_PROFILE,
                    "combined_moderate_stress",
                    seed,
                    manifest,
                )
            )
            noisy_candidate_rows.extend(combined_candidates)
            manifest_rows.append(manifest)

    return noisy_query_rows, noisy_candidate_rows, manifest_rows


def localization_success(row: dict[str, Any]) -> bool:
    if row["returns_old_location"]:
        return bool(row["search_success"])
    if not row["target_retained"]:
        return False
    if not row["search_success"]:
        return False
    return not bool(row["target_jitter_exceeds_success_threshold"])


def localization_failure_type(row: dict[str, Any]) -> str:
    if row["localization_success"]:
        return "none"
    if row["returns_old_location"]:
        return "static_map_localization_error"
    if row["target_dropped_by_noise"] and not row["target_retained"]:
        return "target_dropped_by_noise"
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
            for key in [
                "target_dropped_by_noise",
                "target_drop_forced_retained",
                "forced_non_target_retained",
                "false_positive_added_count",
                "false_positive_available_count",
                "false_positive_above_target_count",
                "target_pushed_down_by_false_positive",
                "target_rank_changed_by_combined_noise",
                "target_rank_changed_by_centroid_jitter",
                "target_centroid_jitter_m",
                "target_planar_jitter_m",
                "target_jitter_exceeds_success_threshold",
                "grid_path_recomputed_for_centroid_jitter",
            ]:
                prediction[key] = row[key]
            prediction["localization_success"] = localization_success(prediction)
            prediction["localization_proxy_sr"] = prediction["localization_success"]
            prediction["localization_failure_type"] = localization_failure_type(prediction)
            prediction["uses_real_navigation"] = False
            predictions.append(prediction)
    return predictions


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def denominator_rows(rows: list[dict[str, Any]], denominator: str) -> list[dict[str, Any]]:
    if denominator == "all_rows":
        return rows
    if denominator == "target_retained_eval":
        return [row for row in rows if row["target_retained"]]
    if denominator == "target_dropped_eval":
        return [row for row in rows if row["target_dropped_by_noise"]]
    if denominator == "false_positive_added_eval":
        return [row for row in rows if int(row["false_positive_added_count"]) > 0]
    if denominator == "target_pushed_down_eval":
        return [row for row in rows if row["target_pushed_down_by_false_positive"]]
    if denominator == "target_rank_changed_eval":
        return [row for row in rows if row["target_rank_changed_by_combined_noise"]]
    if denominator == "target_jitter_within_threshold_eval":
        return [row for row in rows if row["target_retained"] and not row["target_jitter_exceeds_success_threshold"]]
    if denominator == "target_jitter_exceeds_threshold_eval":
        return [row for row in rows if row["target_jitter_exceeds_success_threshold"]]
    raise RuntimeError(f"unknown denominator: {denominator}")


def summarize_prediction_rows(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    identity_sr = safe_rate(sum(1 for row in rows if row["search_success"]), len(rows))
    localization_sr = safe_rate(sum(1 for row in rows if row["localization_success"]), len(rows))
    return {
        "subset": subset,
        "rows": len(rows),
        "identity_proxy_sr": identity_sr,
        "localization_proxy_sr": localization_sr,
        "identity_localization_gap": round6(identity_sr - localization_sr)
        if identity_sr is not None and localization_sr is not None
        else None,
        "target_retained_rate": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
        "target_dropped_rate": safe_rate(sum(1 for row in rows if row["target_dropped_by_noise"]), len(rows)),
        "false_positive_added_rate": safe_rate(
            sum(1 for row in rows if int(row["false_positive_added_count"]) > 0),
            len(rows),
        ),
        "target_pushed_down_rate": safe_rate(
            sum(1 for row in rows if row["target_pushed_down_by_false_positive"]),
            len(rows),
        ),
        "target_rank_changed_rate": safe_rate(
            sum(1 for row in rows if row["target_rank_changed_by_combined_noise"]),
            len(rows),
        ),
        "target_jitter_exceeds_threshold_rate": safe_rate(
            sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"]),
            len(rows),
        ),
        "mean_false_positive_added_count": mean([float(row["false_positive_added_count"]) for row in rows]),
        "mean_false_positive_above_target_count": mean(
            [float(row["false_positive_above_target_count"]) for row in rows]
        ),
        "mean_target_centroid_jitter_m": mean(
            [float(row["target_centroid_jitter_m"]) for row in rows if row["target_centroid_jitter_m"] is not None]
        ),
        "mean_target_planar_jitter_m": mean(
            [float(row["target_planar_jitter_m"]) for row in rows if row["target_planar_jitter_m"] is not None]
        ),
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
        "target_retained_eval",
        "target_dropped_eval",
        "false_positive_added_eval",
        "target_pushed_down_eval",
        "target_rank_changed_eval",
        "target_jitter_within_threshold_eval",
        "target_jitter_exceeds_threshold_eval",
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


def build_metrics(predictions: list[dict[str, Any]], seeds: list[int]) -> dict[str, Any]:
    metrics: dict[str, Any] = {"profiles": {}, "combined_seeds": {}}
    for profile in [REFERENCE_PROFILE, COMBINED_PROFILE]:
        profile_rows = [row for row in predictions if row["proposal_noise_profile_id"] == profile]
        metrics["profiles"][profile] = summarize_by_policy(profile_rows)
    for seed in seeds:
        seed_rows = [
            row
            for row in predictions
            if row["proposal_noise_profile_id"] == COMBINED_PROFILE
            and row["proposal_noise_seed"] == seed
        ]
        metrics["combined_seeds"][str(seed)] = summarize_by_policy(seed_rows)
    return metrics


def summarize_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        by_profile[row["proposal_noise_profile_id"]].append(row)
    output: dict[str, Any] = {}
    for profile, rows in by_profile.items():
        target_retained = sum(1 for row in rows if row["target_retained"])
        target_dropped = sum(1 for row in rows if row["target_dropped_by_noise"])
        false_positive_added = sum(1 for row in rows if int(row["false_positive_added_count"]) > 0)
        target_pushed_down = sum(1 for row in rows if row["target_pushed_down_by_false_positive"])
        target_rank_changed = sum(1 for row in rows if row["target_rank_delta"] not in {0, None})
        target_jitter_exceeds = sum(1 for row in rows if row["target_jitter_exceeds_success_threshold"])
        output[profile] = {
            "rows": len(rows),
            "target_retained_rows": target_retained,
            "target_retained_rate": safe_rate(target_retained, len(rows)),
            "target_dropped_rows": target_dropped,
            "target_dropped_rate": safe_rate(target_dropped, len(rows)),
            "target_drop_forced_retained_rows": sum(1 for row in rows if row["target_drop_forced_retained"]),
            "forced_non_target_retained_rows": sum(1 for row in rows if row["forced_non_target_retained"]),
            "false_positive_added_rows": false_positive_added,
            "false_positive_added_rate": safe_rate(false_positive_added, len(rows)),
            "target_pushed_down_rows": target_pushed_down,
            "target_pushed_down_rate": safe_rate(target_pushed_down, len(rows)),
            "target_rank_changed_rows": target_rank_changed,
            "target_rank_changed_rate": safe_rate(target_rank_changed, len(rows)),
            "target_jitter_exceeds_threshold_rows": target_jitter_exceeds,
            "target_jitter_exceeds_threshold_rate": safe_rate(target_jitter_exceeds, len(rows)),
            "mean_candidate_rows_dropped": mean([float(row["candidate_rows_dropped"]) for row in rows]),
            "mean_candidate_rows_added": mean([float(row["candidate_rows_added"]) for row in rows]),
            "mean_target_centroid_jitter_m": mean(
                [float(row["target_centroid_jitter_m"]) for row in rows if row["target_centroid_jitter_m"] is not None]
            ),
            "mean_target_planar_jitter_m": mean(
                [float(row["target_planar_jitter_m"]) for row in rows if row["target_planar_jitter_m"] is not None]
            ),
            "mean_candidate_centroid_jitter_m": mean(
                [float(row["mean_candidate_centroid_jitter_m"]) for row in rows if row["mean_candidate_centroid_jitter_m"] is not None]
            ),
            "mean_candidate_planar_jitter_m": mean(
                [float(row["mean_candidate_planar_jitter_m"]) for row in rows if row["mean_candidate_planar_jitter_m"] is not None]
            ),
            "rank_changed_candidate_rows": sum(int(row["rank_changed_candidate_rows"]) for row in rows),
            "same_label_false_positive_count": sum(int(row["same_label_false_positive_count"]) for row in rows),
            "semantic_group_false_positive_count": sum(int(row["semantic_group_false_positive_count"]) for row in rows),
            "fallback_false_positive_count": sum(int(row["fallback_false_positive_count"]) for row in rows),
            "grid_path_recomputed_for_centroid_jitter": any(
                bool(row["grid_path_recomputed_for_centroid_jitter"]) for row in rows
            ),
        }
    return output


def build_failure_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        if row["localization_success"]:
            continue
        if row["localization_failure_type"] == "target_dropped_by_noise":
            next_test = "combined-noise proposal-recall boundary analysis"
        elif row["localization_failure_type"] == "target_centroid_jitter_exceeds_threshold":
            next_test = "combined-noise localization boundary analysis"
        elif row["localization_failure_type"] == "identity_or_budget_failure":
            next_test = "combined-noise rank/budget boundary analysis"
        else:
            next_test = "review combined-noise failure boundary"
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
                "target_dropped_by_noise": row["target_dropped_by_noise"],
                "false_positive_added_count": row["false_positive_added_count"],
                "target_pushed_down_by_false_positive": row["target_pushed_down_by_false_positive"],
                "target_jitter_exceeds_success_threshold": row["target_jitter_exceeds_success_threshold"],
                "target_rank_changed_by_combined_noise": row["target_rank_changed_by_combined_noise"],
                "target_rank": row["target_rank"],
                "returned_location_count": row["returned_location_count"],
                "expected_search_cost": row["expected_search_cost"],
                "returned_unreachable_count": row["returned_unreachable_count"],
                "identity_proxy_success": row["search_success"],
                "localization_success": row["localization_success"],
                "next_test": next_test,
            }
        )
    return rows


def empty_metric() -> dict[str, Any]:
    return summarize_prediction_rows([], "significant_moved")


def get_metric(metrics: dict[str, Any], profile: str, denominator: str, subset: str, context: str, policy: str) -> dict[str, Any]:
    return (
        metrics["profiles"]
        .get(profile, {})
        .get(denominator, {})
        .get(subset, {})
        .get(context, {})
        .get(policy, empty_metric())
    )


def build_coverage(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    metrics: dict[str, Any],
    contract: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    params = contract_params(contract)
    manifest_summary = summarize_manifest(manifest_rows)
    combined_summary = manifest_summary[COMBINED_PROFILE]
    expected_noisy_query_rows = len(query_rows) * (1 + len(params["seed_set"]))
    sig_routine_task = get_metric(
        metrics,
        COMBINED_PROFILE,
        "all_rows",
        "significant_moved",
        "routine_fetch",
        "task_conditioned_budget_v0",
    )
    sig_routine_reachable = get_metric(
        metrics,
        COMBINED_PROFILE,
        "all_rows",
        "significant_moved",
        "routine_fetch",
        "reachable_first_task_conditioned_budget_v0",
    )
    sig_routine_target_dropped = get_metric(
        metrics,
        COMBINED_PROFILE,
        "target_dropped_eval",
        "significant_moved",
        "routine_fetch",
        "task_conditioned_budget_v0",
    )
    sig_routine_target_jitter_exceeded = get_metric(
        metrics,
        COMBINED_PROFILE,
        "target_jitter_exceeds_threshold_eval",
        "significant_moved",
        "routine_fetch",
        "task_conditioned_budget_v0",
    )
    status = "combined_moderate_eval_ready"
    if len(noisy_query_rows) != expected_noisy_query_rows:
        status = "review_needed"
    if len(predictions) != len(noisy_query_rows) * len(POLICIES):
        status = "review_needed"
    if combined_summary["false_positive_added_rows"] <= 0:
        status = "review_needed"
    return {
        "eval_version": EVAL_VERSION,
        "status": status,
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "profiles": [REFERENCE_PROFILE, COMBINED_PROFILE],
        "combined_seed_set": params["seed_set"],
        "moderate_noise_parameters": contract["moderate_noise_parameters"],
        "noisy_query_rows": len(noisy_query_rows),
        "noisy_candidate_rows": len(noisy_candidate_rows),
        "noise_manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "manifest_summary": manifest_summary,
        "target_drop_profiles_included": True,
        "uses_annotation_proxy_noise": True,
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "uses_real_navigation": False,
        "docker_required": False,
        "docker_reason": "This profile is a repository-local JSONL artifact transform and policy evaluation; real detector/open-vocabulary implementation remains Docker-required.",
        "grid_path_recomputed_for_centroid_jitter": False,
        "grid_path_note": "E002 grid reachability is reused by instance id; occupancy-grid path costs are not recomputed after centroid jitter.",
        "significant_moved_routine_task_combined_metrics": sig_routine_task,
        "significant_moved_routine_reachable_combined_metrics": sig_routine_reachable,
        "significant_moved_routine_task_target_dropped_metrics": sig_routine_target_dropped,
        "significant_moved_routine_task_jitter_exceeded_metrics": sig_routine_target_jitter_exceeded,
        "failure_type_counts": counter_dict(Counter(row["failure_type"] for row in failure_rows)),
        "next_recommended_unit": "E003-M14_combined_noise_failure_boundary_v0",
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
    clean_task = get_metric(
        metrics,
        REFERENCE_PROFILE,
        "all_rows",
        "significant_moved",
        "routine_fetch",
        "task_conditioned_budget_v0",
    )
    combined_task = coverage["significant_moved_routine_task_combined_metrics"]
    combined_reachable = coverage["significant_moved_routine_reachable_combined_metrics"]
    combined_top5 = get_metric(
        metrics,
        COMBINED_PROFILE,
        "all_rows",
        "significant_moved",
        "routine_fetch",
        "always_top5",
    )
    combined_oracle = get_metric(
        metrics,
        COMBINED_PROFILE,
        "all_rows",
        "significant_moved",
        "routine_fetch",
        "oracle_current_target",
    )
    dropped_task = coverage["significant_moved_routine_task_target_dropped_metrics"]
    jitter_exceeded_task = coverage["significant_moved_routine_task_jitter_exceeded_metrics"]
    summary = coverage["manifest_summary"][COMBINED_PROFILE]
    params = coverage["moderate_noise_parameters"]
    lines = [
        "# E003-M13 Annotation Combined Moderate",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input query rows: {coverage['input_query_rows']}",
        f"- Input candidate rows: {coverage['input_candidate_rows']}",
        f"- Combined seeds: {', '.join(str(seed) for seed in coverage['combined_seed_set'])}",
        f"- Score jitter sigma: {params['score_jitter_sigma']}",
        f"- Target drop rate: {params['target_drop_rate']}",
        f"- Non-target drop rate: {params['non_target_candidate_drop_rate']}",
        f"- False-positive candidates per row: {params['min_false_positive_candidates']} to {params['max_false_positive_candidates']}",
        f"- Centroid planar sigma m: {params['centroid_planar_sigma_m']}",
        f"- Max planar jitter m: {params['max_planar_jitter_m']}",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Target dropped rows: {summary['target_dropped_rows']} / {summary['rows']}",
        f"- False-positive added rows: {summary['false_positive_added_rows']} / {summary['rows']}",
        f"- Target pushed-down rows: {summary['target_pushed_down_rows']} / {summary['rows']}",
        f"- Target rank changed rows: {summary['target_rank_changed_rows']} / {summary['rows']}",
        f"- Target jitter exceeds threshold rows: {summary['target_jitter_exceeds_threshold_rows']} / {summary['rows']}",
        f"- Mean target centroid jitter m: {summary['mean_target_centroid_jitter_m']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch`",
        "",
        "| Profile | Policy | rows | identity `SR` | localization `SR` | proposal recall | target dropped | false positive | jitter exceeded | `ExpectedSearchCost` | `AttemptSPL` | Utility |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| clean | `task_conditioned_budget_v0` | {clean_task['rows']} | {clean_task['identity_proxy_sr']} | {clean_task['localization_proxy_sr']} | {clean_task['target_retained_rate']} | {clean_task['target_dropped_rate']} | {clean_task['false_positive_added_rate']} | {clean_task['target_jitter_exceeds_threshold_rate']} | {clean_task['mean_expected_search_cost']} | {clean_task['attempt_spl_proxy']} | {clean_task['mean_task_utility']} |",
        f"| combined | `task_conditioned_budget_v0` | {combined_task['rows']} | {combined_task['identity_proxy_sr']} | {combined_task['localization_proxy_sr']} | {combined_task['target_retained_rate']} | {combined_task['target_dropped_rate']} | {combined_task['false_positive_added_rate']} | {combined_task['target_jitter_exceeds_threshold_rate']} | {combined_task['mean_expected_search_cost']} | {combined_task['attempt_spl_proxy']} | {combined_task['mean_task_utility']} |",
        f"| combined | `reachable_first_task_conditioned_budget_v0` | {combined_reachable['rows']} | {combined_reachable['identity_proxy_sr']} | {combined_reachable['localization_proxy_sr']} | {combined_reachable['target_retained_rate']} | {combined_reachable['target_dropped_rate']} | {combined_reachable['false_positive_added_rate']} | {combined_reachable['target_jitter_exceeds_threshold_rate']} | {combined_reachable['mean_expected_search_cost']} | {combined_reachable['attempt_spl_proxy']} | {combined_reachable['mean_task_utility']} |",
        f"| combined | `always_top5` | {combined_top5['rows']} | {combined_top5['identity_proxy_sr']} | {combined_top5['localization_proxy_sr']} | {combined_top5['target_retained_rate']} | {combined_top5['target_dropped_rate']} | {combined_top5['false_positive_added_rate']} | {combined_top5['target_jitter_exceeds_threshold_rate']} | {combined_top5['mean_expected_search_cost']} | {combined_top5['attempt_spl_proxy']} | {combined_top5['mean_task_utility']} |",
        f"| combined | `oracle_current_target` | {combined_oracle['rows']} | {combined_oracle['identity_proxy_sr']} | {combined_oracle['localization_proxy_sr']} | {combined_oracle['target_retained_rate']} | {combined_oracle['target_dropped_rate']} | {combined_oracle['false_positive_added_rate']} | {combined_oracle['target_jitter_exceeds_threshold_rate']} | {combined_oracle['mean_expected_search_cost']} | {combined_oracle['attempt_spl_proxy']} | {combined_oracle['mean_task_utility']} |",
        "",
        "## Required Boundaries",
        "",
        f"- Significant moved `routine_fetch` target-dropped `task_conditioned_budget_v0` rows: {dropped_task['rows']}",
        f"- Target-dropped identity/localization `SR`: {dropped_task['identity_proxy_sr']} / {dropped_task['localization_proxy_sr']}",
        f"- Significant moved `routine_fetch` jitter-exceeded `task_conditioned_budget_v0` rows: {jitter_exceeded_task['rows']}",
        f"- Jitter-exceeded identity/localization `SR`: {jitter_exceeded_task['identity_proxy_sr']} / {jitter_exceeded_task['localization_proxy_sr']}",
        "",
        "## 논문 주장",
        "",
        "- E003-M13 supports controlled annotation-proxy combined perception-like stress evaluation.",
        "- E003-M13 combines proposal dropout, annotation-derived false positives, score/rank jitter, and centroid jitter.",
        "- E003-M13 does not support real RGB-D perception robustness, open-vocabulary detector robustness, or real navigation `SR` / `SPL`.",
        "",
        "## 에이전트 추론",
        "",
        "- This is the first E003 profile where proposal recall, distractor contamination, rank noise, and localization noise interact in one denominator.",
        "- Target-dropped and jitter-exceeded denominators must stay separate from the all-row aggregate.",
        "- A boundary analysis should follow before using this result as a paper claim.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M13. Continue to E003-M14 combined-noise failure-boundary analysis unless redirected to Dockerized real proposal staging.",
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
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_rows = load_jsonl(args.e001_m02_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.e001_m02_dir / "candidate_rows.jsonl")
    contract = load_json(args.contract)
    noisy_query_rows, noisy_candidate_rows, manifest_rows = build_noisy_rows(query_rows, candidate_rows, contract)
    predictions = build_predictions(noisy_query_rows, noisy_candidate_rows, args.grid_dir)
    failure_rows = build_failure_rows(predictions)
    metrics = build_metrics(predictions, contract_params(contract)["seed_set"])
    coverage = build_coverage(
        query_rows,
        candidate_rows,
        noisy_query_rows,
        noisy_candidate_rows,
        manifest_rows,
        predictions,
        failure_rows,
        metrics,
        contract,
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

    summary = coverage["manifest_summary"][COMBINED_PROFILE]
    print(
        json.dumps(
            {
                "status": coverage["status"],
                "noisy_query_rows": coverage["noisy_query_rows"],
                "noisy_candidate_rows": coverage["noisy_candidate_rows"],
                "prediction_rows": coverage["prediction_rows"],
                "target_dropped_rows": summary["target_dropped_rows"],
                "false_positive_added_rows": summary["false_positive_added_rows"],
                "target_pushed_down_rows": summary["target_pushed_down_rows"],
                "target_jitter_exceeds_threshold_rows": summary[
                    "target_jitter_exceeds_threshold_rows"
                ],
                "significant_moved_routine_task_combined": coverage[
                    "significant_moved_routine_task_combined_metrics"
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
