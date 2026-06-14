#!/usr/bin/env python3
"""Run H001 non-persistent anchor smoke.

This hypothesis-stage smoke ranks same-label current semantic objects without
using persistent cross-scan object-id anchors. Object ids are used only as row
identifiers and for evaluation.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_QUERY_ROWS = H001_ROOT / "artifacts" / "high_displacement_query_smoke" / "query_rows.jsonl"
DEFAULT_INSTANCE_PREDICTIONS = H001_ROOT / "artifacts" / "instance_evidence_v0" / "predictions.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "non_persistent_anchor_v0"
REFERENCE_SCAN_ID = "569d8f0d-72aa-2f24-8ac6-c6ee8d927c4b"
RESCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"
POLICIES = [
    "scene_aligned_static_map",
    "staleness_only",
    "label_nearest_current_observation",
    "label_top3_current_observation",
    "instance_evidence_v0",
    "non_persistent_anchor_v0",
    "oracle_current_pose",
]
ABLATIONS = [
    "full_non_persistent",
    "geometry_only",
    "relation_label_only",
    "local_label_context_only",
    "geometry_plus_relation_label",
    "geometry_plus_local_context",
    "old_location_only",
]
SUPPORT_PREDICATES = {
    "attached to",
    "hanging on",
    "lying on",
    "standing on",
    "supported by",
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def point_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def planar_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def transform_point_row(point: list[float], matrix: list[float]) -> list[float]:
    x, y, z = point
    return [
        x * matrix[0] + y * matrix[4] + z * matrix[8] + matrix[12],
        x * matrix[1] + y * matrix[5] + z * matrix[9] + matrix[13],
        x * matrix[2] + y * matrix[6] + z * matrix[10] + matrix[14],
    ]


def invert_rigid_row_transform(matrix: list[float]) -> list[float]:
    rotation_t = [
        matrix[0],
        matrix[4],
        matrix[8],
        0.0,
        matrix[1],
        matrix[5],
        matrix[9],
        0.0,
        matrix[2],
        matrix[6],
        matrix[10],
        0.0,
    ]
    tx, ty, tz = matrix[12], matrix[13], matrix[14]
    inv_translation = [
        -(tx * rotation_t[0] + ty * rotation_t[4] + tz * rotation_t[8]),
        -(tx * rotation_t[1] + ty * rotation_t[5] + tz * rotation_t[9]),
        -(tx * rotation_t[2] + ty * rotation_t[6] + tz * rotation_t[10]),
    ]
    return rotation_t + inv_translation + [1.0]


def find_pair_metadata(scan3r_json: list[dict], reference_scan_id: str, rescan_id: str) -> dict:
    for group in scan3r_json:
        if group.get("reference") != reference_scan_id:
            continue
        for scan in group.get("scans", []):
            if scan.get("reference") == rescan_id:
                return scan
    raise RuntimeError(f"target pair metadata not found: {reference_scan_id} -> {rescan_id}")


def load_semseg_objects(path: Path) -> dict[str, dict]:
    data = load_json(path)
    objects = {}
    for group in data.get("segGroups", []):
        obb = group.get("obb", {})
        centroid = obb.get("centroid")
        axes_lengths = obb.get("axesLengths")
        if centroid is None or axes_lengths is None:
            continue
        instance_id = str(group.get("objectId", group.get("id")))
        objects[instance_id] = {
            "instance_id": instance_id,
            "label": group.get("label", ""),
            "centroid": [float(value) for value in centroid],
            "axes_lengths": [float(value) for value in axes_lengths],
            "normalized_axes": [float(value) for value in obb.get("normalizedAxes", [])],
            "dominant_normal": [float(value) for value in group.get("dominantNormal", [])],
        }
    return objects


def load_relationships(path: Path) -> dict[str, list[list]]:
    data = load_json(path)
    return {scan["scan"]: scan.get("relationships", []) for scan in data.get("scans", [])}


def counter_jaccard(left: collections.Counter, right: collections.Counter) -> float:
    intersection = sum((left & right).values())
    union = sum((left | right).values())
    if union == 0:
        return 0.0
    return intersection / union


def sorted_axes(obj: dict) -> list[float]:
    return sorted(float(value) for value in obj["axes_lengths"])


def orientation_similarity(ref_obj: dict, candidate: dict) -> float:
    ref_axes = ref_obj.get("normalized_axes", [])
    cand_axes = candidate.get("normalized_axes", [])
    if len(ref_axes) != 9 or len(cand_axes) != 9:
        return 0.0
    ref_vectors = [ref_axes[index : index + 3] for index in range(0, 9, 3)]
    cand_vectors = [cand_axes[index : index + 3] for index in range(0, 9, 3)]
    return sum(
        max(
            abs(sum(ref_vector[i] * cand_vector[i] for i in range(3)))
            for cand_vector in cand_vectors
        )
        for ref_vector in ref_vectors
    ) / len(ref_vectors)


def shape_similarity(ref_obj: dict, candidate: dict) -> float:
    diff = point_distance(sorted_axes(ref_obj), sorted_axes(candidate))
    return math.exp(-diff / 0.25)


def height_similarity(old_scene_aligned_centroid: list[float], candidate: dict) -> float:
    return math.exp(-abs(old_scene_aligned_centroid[2] - candidate["centroid"][2]) / 0.3)


def old_location_prior(old_scene_aligned_centroid: list[float], candidate: dict) -> float:
    return math.exp(-planar_distance(old_scene_aligned_centroid, candidate["centroid"]) / 2.0)


def relationship_label_signature(
    relationships: list[list],
    obj_id: str,
    objects: dict[str, dict],
    support_only: bool = False,
) -> collections.Counter:
    signature: collections.Counter = collections.Counter()
    numeric_obj_id = int(obj_id)
    for source_id, target_id, _predicate_id, predicate in relationships:
        if support_only and predicate not in SUPPORT_PREDICATES:
            continue
        if source_id == numeric_obj_id:
            direction = "out"
            neighbor_id = str(target_id)
        elif target_id == numeric_obj_id:
            direction = "in"
            neighbor_id = str(source_id)
        else:
            continue
        if neighbor_id not in objects:
            continue
        signature[(direction, predicate, objects[neighbor_id]["label"])] += 1
    return signature


def radius_bin(distance: float) -> str | None:
    if distance <= 1.0:
        return "near"
    if distance <= 2.5:
        return "mid"
    if distance <= 5.0:
        return "far"
    return None


def sector_bin(dx: float, dy: float) -> str:
    if abs(dx) >= abs(dy):
        return "right" if dx >= 0 else "left"
    return "front" if dy >= 0 else "back"


def height_bin(dz: float) -> str:
    if abs(dz) < 0.5:
        return "same"
    return "above" if dz > 0 else "below"


def local_label_context_histogram(
    objects: dict[str, dict],
    target_id: str,
    target_centroid: list[float],
    scene_inverse: list[float] | None,
) -> collections.Counter:
    histogram: collections.Counter = collections.Counter()
    for obj_id, obj in objects.items():
        if obj_id == target_id:
            continue
        centroid = obj["centroid"]
        if scene_inverse is not None:
            centroid = transform_point_row(centroid, scene_inverse)
        dx = centroid[0] - target_centroid[0]
        dy = centroid[1] - target_centroid[1]
        dz = centroid[2] - target_centroid[2]
        distance = math.sqrt(dx * dx + dy * dy)
        r_bin = radius_bin(distance)
        if r_bin is None:
            continue
        key = (r_bin, sector_bin(dx, dy), height_bin(dz), obj["label"])
        histogram[key] += 1
    return histogram


def compute_feature_scores(
    row: dict,
    candidate: dict,
    ref_objects: dict[str, dict],
    rescan_objects: dict[str, dict],
    ref_relationships: list[list],
    rescan_relationships: list[list],
    scene_inverse: list[float],
) -> dict:
    ref_obj_id = row["object_instance_id_ref"]
    ref_obj = ref_objects[ref_obj_id]
    ref_relation = relationship_label_signature(ref_relationships, ref_obj_id, ref_objects)
    cand_relation = relationship_label_signature(
        rescan_relationships, candidate["instance_id"], rescan_objects
    )
    ref_support = relationship_label_signature(
        ref_relationships, ref_obj_id, ref_objects, support_only=True
    )
    cand_support = relationship_label_signature(
        rescan_relationships, candidate["instance_id"], rescan_objects, support_only=True
    )
    ref_context = local_label_context_histogram(
        ref_objects, ref_obj_id, row["old_scene_aligned_centroid"], scene_inverse
    )
    cand_context = local_label_context_histogram(
        rescan_objects, candidate["instance_id"], candidate["centroid"], None
    )
    return {
        "shape_similarity": shape_similarity(ref_obj, candidate),
        "orientation_similarity": orientation_similarity(ref_obj, candidate),
        "height_similarity": height_similarity(row["old_scene_aligned_centroid"], candidate),
        "old_location_prior": old_location_prior(row["old_scene_aligned_centroid"], candidate),
        "relation_label_overlap": counter_jaccard(ref_relation, cand_relation),
        "local_label_context_histogram": counter_jaccard(ref_context, cand_context),
        "support_surface_context": counter_jaccard(ref_support, cand_support),
        "relation_label_entry_count": sum(ref_relation.values()),
        "local_context_entry_count": sum(ref_context.values()),
    }


def geometry_score(features: dict) -> float:
    return (
        0.6 * features["shape_similarity"]
        + 0.25 * features["orientation_similarity"]
        + 0.25 * features["height_similarity"]
        + 0.25 * features["old_location_prior"]
    )


def score_features(features: dict, ablation: str) -> float:
    geom = geometry_score(features)
    if ablation == "full_non_persistent":
        return (
            geom
            + 1.0 * features["relation_label_overlap"]
            + 1.2 * features["local_label_context_histogram"]
            + 0.4 * features["support_surface_context"]
        )
    if ablation == "geometry_only":
        return geom
    if ablation == "relation_label_only":
        return features["relation_label_overlap"] + 0.4 * features["support_surface_context"]
    if ablation == "local_label_context_only":
        return features["local_label_context_histogram"]
    if ablation == "geometry_plus_relation_label":
        return geom + 1.0 * features["relation_label_overlap"] + 0.4 * features["support_surface_context"]
    if ablation == "geometry_plus_local_context":
        return geom + 1.2 * features["local_label_context_histogram"]
    if ablation == "old_location_only":
        return features["old_location_prior"]
    raise RuntimeError(f"unknown ablation: {ablation}")


def rank_candidates(feature_rows: list[dict], ablation: str) -> list[dict]:
    return sorted(
        feature_rows,
        key=lambda row: (
            -row["scores"][ablation],
            row["distance_to_old_scene_aligned_m"],
            int(row["candidate_instance_id"]),
        ),
    )


def normalized_entropy(scores: list[float]) -> float | None:
    if len(scores) <= 1:
        return None
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    total = sum(exp_scores)
    probs = [score / total for score in exp_scores]
    entropy = -sum(prob * math.log(prob) for prob in probs if prob > 0)
    return entropy / math.log(len(scores))


def candidate_set_size_under_margin(ranked_rows: list[dict], ablation: str, margin: float = 0.1) -> int:
    if not ranked_rows:
        return 0
    top_score = ranked_rows[0]["scores"][ablation]
    return sum(1 for row in ranked_rows if top_score - row["scores"][ablation] <= margin)


def build_feature_rows(
    query_rows: list[dict],
    ref_objects: dict[str, dict],
    rescan_objects: dict[str, dict],
    relationships: dict[str, list[list]],
    scene_inverse: list[float],
) -> tuple[list[dict], dict[str, list[dict]]]:
    all_feature_rows = []
    rows_by_object: dict[str, list[dict]] = {}
    for row in query_rows:
        row_features = []
        for candidate in rescan_objects.values():
            if candidate["label"] != row["object_label"]:
                continue
            features = compute_feature_scores(
                row,
                candidate,
                ref_objects,
                rescan_objects,
                relationships[REFERENCE_SCAN_ID],
                relationships[RESCAN_ID],
                scene_inverse,
            )
            scores = {name: score_features(features, name) for name in ABLATIONS}
            feature_row = {
                "object_instance_id_ref": row["object_instance_id_ref"],
                "object_label": row["object_label"],
                "candidate_instance_id": candidate["instance_id"],
                "candidate_label": candidate["label"],
                "significant_moved": row["significant_moved"],
                "old_memory_is_stale": row["old_memory_is_stale"],
                "distance_to_old_scene_aligned_m": round_or_none(
                    planar_distance(row["old_scene_aligned_centroid"], candidate["centroid"])
                ),
                "features": {
                    key: round_or_none(value) if isinstance(value, float) else value
                    for key, value in features.items()
                },
                "scores": {
                    key: round_or_none(value)
                    for key, value in scores.items()
                },
                "eval_is_target_instance": candidate["instance_id"]
                == row["object_instance_id_rescan"],
            }
            row_features.append(feature_row)
        ranked_by_ablation = {}
        for ablation in ABLATIONS:
            ranked = rank_candidates(row_features, ablation)
            ranked_by_ablation[ablation] = {
                item["candidate_instance_id"]: rank
                for rank, item in enumerate(ranked, start=1)
            }
        for feature_row in row_features:
            output_row = {
                **feature_row,
                "ranks": {
                    ablation: ranked_by_ablation[ablation][feature_row["candidate_instance_id"]]
                    for ablation in ABLATIONS
                },
            }
            all_feature_rows.append(output_row)
            rows_by_object.setdefault(row["object_instance_id_ref"], []).append(output_row)
    return all_feature_rows, rows_by_object


def sorted_feature_rows_for_object(
    rows_by_object: dict[str, list[dict]],
    object_instance_id_ref: str,
    ablation: str = "full_non_persistent",
) -> list[dict]:
    return rank_candidates(rows_by_object[object_instance_id_ref], ablation)


def target_rank(ranked_rows: list[dict], ablation: str = "full_non_persistent") -> int | None:
    for row in ranked_rows:
        if row["eval_is_target_instance"]:
            return row["ranks"][ablation]
    return None


def target_rank_for_label(ranked_rows: list[dict]) -> int | None:
    for row in ranked_rows:
        if row["eval_is_target_instance"]:
            return row["label_rank"]
    return None


def predict(
    policy: str,
    row: dict,
    ranked_label_candidates: list[dict],
    ranked_np_candidates: list[dict],
    success_threshold_m: float,
) -> dict:
    label_target_rank = target_rank_for_label(ranked_label_candidates)
    np_target_rank = target_rank(ranked_np_candidates)
    if policy == "scene_aligned_static_map":
        error = point_distance(row["old_scene_aligned_centroid"], row["pair_current_centroid"])
        exact = error <= success_threshold_m
        return {
            "policy": policy,
            "memory_state": "trusted",
            "action": "return_scene_aligned_old_location",
            "returns_old_location": True,
            "suppresses_old_location": False,
            "uses_rescan_semseg_observation": False,
            "uses_exact_current_pose": False,
            "candidate_count": 1,
            "target_rank": None,
            "exact_recovery": exact,
            "candidate_recall_at_1": exact,
            "candidate_recall_at_3": exact,
            "candidate_recall_all": exact,
            "target_error_m": round_or_none(error),
        }
    if policy == "staleness_only":
        return {
            "policy": policy,
            "memory_state": "needs_reobservation" if row["old_memory_is_stale"] else "trusted_or_low_motion",
            "action": "suppress_old_location" if row["old_memory_is_stale"] else "return_scene_aligned_old_location",
            "returns_old_location": not row["old_memory_is_stale"],
            "suppresses_old_location": row["old_memory_is_stale"],
            "uses_rescan_semseg_observation": False,
            "uses_exact_current_pose": False,
            "candidate_count": 0,
            "target_rank": None,
            "exact_recovery": False,
            "candidate_recall_at_1": False,
            "candidate_recall_at_3": False,
            "candidate_recall_all": False,
            "target_error_m": None,
        }
    if policy == "label_nearest_current_observation":
        chosen = ranked_label_candidates[0] if ranked_label_candidates else None
        error = point_distance(chosen["centroid"], row["pair_current_centroid"]) if chosen else None
        exact = bool(chosen and chosen["eval_is_target_instance"] and error <= success_threshold_m)
        return {
            "policy": policy,
            "memory_state": "updated_from_current_observation",
            "action": "return_nearest_same_label_current_observation",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": 1 if chosen else 0,
            "target_rank": label_target_rank,
            "exact_recovery": exact,
            "candidate_recall_at_1": label_target_rank == 1,
            "candidate_recall_at_3": label_target_rank is not None and label_target_rank <= 3,
            "candidate_recall_all": label_target_rank is not None,
            "target_error_m": round_or_none(error),
            "chosen_instance_id": chosen["candidate_instance_id"] if chosen else None,
        }
    if policy == "label_top3_current_observation":
        top_k = ranked_label_candidates[:3]
        return {
            "policy": policy,
            "memory_state": "candidate_set_from_current_observation",
            "action": "return_top3_same_label_current_observations",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": len(top_k),
            "target_rank": label_target_rank,
            "exact_recovery": False,
            "candidate_recall_at_1": label_target_rank == 1,
            "candidate_recall_at_3": label_target_rank is not None and label_target_rank <= 3,
            "candidate_recall_all": label_target_rank is not None,
            "target_error_m": None,
            "candidate_instance_ids": [item["candidate_instance_id"] for item in top_k],
        }
    if policy == "non_persistent_anchor_v0":
        if not row["old_memory_is_stale"]:
            error = point_distance(row["old_scene_aligned_centroid"], row["pair_current_centroid"])
            exact = error <= success_threshold_m
            return {
                "policy": policy,
                "memory_state": "trusted_or_low_motion",
                "action": "return_scene_aligned_old_location",
                "returns_old_location": True,
                "suppresses_old_location": False,
                "uses_rescan_semseg_observation": False,
                "uses_exact_current_pose": False,
                "candidate_count": 1,
                "target_rank": np_target_rank,
                "exact_recovery": exact,
                "candidate_recall_at_1": exact,
                "candidate_recall_at_3": exact,
                "candidate_recall_all": exact,
                "target_error_m": round_or_none(error),
                "chosen_instance_id": row["object_instance_id_ref"],
            }
        chosen = ranked_np_candidates[0] if ranked_np_candidates else None
        error = point_distance(chosen["centroid"], row["pair_current_centroid"]) if chosen else None
        exact = bool(chosen and chosen["eval_is_target_instance"] and error <= success_threshold_m)
        scores = [item["scores"]["full_non_persistent"] for item in ranked_np_candidates]
        return {
            "policy": policy,
            "memory_state": "updated_from_non_persistent_anchor",
            "action": "return_top_non_persistent_current_observation",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": 1 if chosen else 0,
            "target_rank": np_target_rank,
            "exact_recovery": exact,
            "candidate_recall_at_1": np_target_rank == 1,
            "candidate_recall_at_3": np_target_rank is not None and np_target_rank <= 3,
            "candidate_recall_all": np_target_rank is not None,
            "target_error_m": round_or_none(error),
            "chosen_instance_id": chosen["candidate_instance_id"] if chosen else None,
            "candidate_entropy": round_or_none(normalized_entropy(scores)),
            "score_margin_top1_top2": round_or_none(
                ranked_np_candidates[0]["scores"]["full_non_persistent"]
                - ranked_np_candidates[1]["scores"]["full_non_persistent"]
                if len(ranked_np_candidates) > 1
                else None
            ),
            "candidate_set_size_under_margin_0_1": candidate_set_size_under_margin(
                ranked_np_candidates, "full_non_persistent", 0.1
            ),
            "expected_search_cost_proxy": np_target_rank,
        }
    if policy == "oracle_current_pose":
        return {
            "policy": policy,
            "memory_state": "trusted_current",
            "action": "return_pair_validated_current_target",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": True,
            "candidate_count": 1,
            "target_rank": np_target_rank,
            "exact_recovery": True,
            "candidate_recall_at_1": True,
            "candidate_recall_at_3": True,
            "candidate_recall_all": True,
            "target_error_m": 0.0,
            "chosen_instance_id": row["object_instance_id_rescan"],
        }
    raise RuntimeError(f"unknown policy: {policy}")


def summarize_policy(policy: str, predictions: list[dict], subset_name: str, subset_rows: list[dict]) -> dict:
    ids = {row["object_instance_id_ref"] for row in subset_rows}
    items = [row for row in predictions if row["object_instance_id_ref"] in ids and row["policy"] == policy]
    den = len(items)
    stale_items = [row for row in items if row["old_memory_is_stale"]]
    low_motion_items = [row for row in items if not row["old_memory_is_stale"]]
    return {
        "policy": policy,
        "subset": subset_name,
        "rows": den,
        "stale_rows": len(stale_items),
        "suppresses_old_location_rate": safe_rate(
            sum(1 for row in items if row["suppresses_old_location"]), den
        ),
        "stale_old_location_false_positive_rate": safe_rate(
            sum(1 for row in stale_items if row["returns_old_location"] and not row["exact_recovery"]),
            len(stale_items),
        ),
        "exact_recovery_rate": safe_rate(sum(1 for row in items if row["exact_recovery"]), den),
        "candidate_recall_at_1": safe_rate(sum(1 for row in items if row["candidate_recall_at_1"]), den),
        "candidate_recall_at_3": safe_rate(sum(1 for row in items if row["candidate_recall_at_3"]), den),
        "candidate_recall_all": safe_rate(sum(1 for row in items if row["candidate_recall_all"]), den),
        "mean_candidate_count": round_or_none(
            sum(row["candidate_count"] for row in items) / den if den else None
        ),
        "uses_rescan_semseg_observation": any(row["uses_rescan_semseg_observation"] for row in items),
        "uses_exact_current_pose": any(row["uses_exact_current_pose"] for row in items),
        "low_motion_static_preserved_rate": safe_rate(
            sum(1 for row in low_motion_items if row["returns_old_location"] and row["exact_recovery"]),
            len(low_motion_items),
        ),
        "control_forced_reobservation_rate": safe_rate(
            sum(1 for row in low_motion_items if row["uses_rescan_semseg_observation"]),
            len(low_motion_items),
        ),
        "mean_candidate_entropy": round_or_none(
            sum(row.get("candidate_entropy", 0.0) for row in items if row.get("candidate_entropy") is not None)
            / sum(1 for row in items if row.get("candidate_entropy") is not None)
            if any(row.get("candidate_entropy") is not None for row in items)
            else None
        ),
        "mean_expected_search_cost_proxy": round_or_none(
            sum(row.get("expected_search_cost_proxy", 0) for row in items if row.get("expected_search_cost_proxy") is not None)
            / sum(1 for row in items if row.get("expected_search_cost_proxy") is not None)
            if any(row.get("expected_search_cost_proxy") is not None for row in items)
            else None
        ),
    }


def summarize_ablations(query_rows: list[dict], rows_by_object: dict[str, list[dict]]) -> dict:
    summary = {}
    for ablation in ABLATIONS:
        ablation_rows = []
        for row in query_rows:
            ranked = sorted_feature_rows_for_object(rows_by_object, row["object_instance_id_ref"], ablation)
            chosen = ranked[0] if ranked else None
            target = next((item for item in ranked if item["eval_is_target_instance"]), None)
            ablation_rows.append(
                {
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "significant_moved": row["significant_moved"],
                    "chosen_instance_id": chosen["candidate_instance_id"] if chosen else None,
                    "target_rank": target["ranks"][ablation] if target else None,
                    "exact_top1": bool(chosen and chosen["eval_is_target_instance"]),
                    "recall_at_3": bool(target and target["ranks"][ablation] <= 3),
                }
            )
        significant = [row for row in ablation_rows if row["significant_moved"]]
        hard = next((row for row in ablation_rows if row["object_instance_id_ref"] == "41"), None)
        summary[ablation] = {
            "significant_rows": len(significant),
            "significant_exact_top1_rate": safe_rate(
                sum(1 for row in significant if row["exact_top1"]), len(significant)
            ),
            "significant_recall_at_3": safe_rate(
                sum(1 for row in significant if row["recall_at_3"]), len(significant)
            ),
            "hard_row_41_rank": hard["target_rank"] if hard else None,
            "hard_row_41_chosen": hard["chosen_instance_id"] if hard else None,
        }
    return summary


def write_report(out_dir: Path, coverage: dict, metrics: dict) -> None:
    lines = [
        "# Non-Persistent Anchor V0 Smoke Report",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Reference scan: `{coverage['reference_scan_id']}`",
        f"- Rescan: `{coverage['rescan_id']}`",
        f"- Query rows: {coverage['query_rows']}",
        f"- Significant moved rows: {coverage['significant_moved_rows']}",
        f"- Low-motion controls: {coverage['low_motion_rows']}",
        f"- Same-label candidate count per row: {coverage['same_label_candidate_count']}",
        f"- Hard row: object `{coverage['hard_row_object_id']}`",
        f"- Ranking uses persistent cross-scan ids: {coverage['ranking_uses_persistent_cross_scan_ids']}",
        f"- Uses navigation: {coverage['uses_navigation']}",
        f"- Uses exact current pose for ranking: {coverage['uses_exact_current_pose_for_ranking']}",
        "",
        "## Significant Moved Metrics",
        "",
        "| Policy | Exact recovery | Recall@1 | Recall@3 | Stale FP | Mean candidates | Exact pose |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for policy in POLICIES:
        item = metrics["significant_moved"][policy]
        lines.append(
            "| {policy} | {exact} | {r1} | {r3} | {fp} | {cands} | {exact_pose} |".format(
                policy=policy,
                exact=item["exact_recovery_rate"],
                r1=item["candidate_recall_at_1"],
                r3=item["candidate_recall_at_3"],
                fp=item["stale_old_location_false_positive_rate"],
                cands=item["mean_candidate_count"],
                exact_pose=item["uses_exact_current_pose"],
            )
        )
    hard = metrics["hard_row_41"]
    lines.extend(
        [
            "",
            "## Hard Row 41",
            "",
            f"- `label_nearest_current_observation` target rank: {hard['label_nearest_rank']}",
            f"- `instance_evidence_v0` target rank: {hard['instance_evidence_rank']}",
            f"- `non_persistent_anchor_v0` target rank: {hard['non_persistent_rank']}",
            f"- `non_persistent_anchor_v0` chosen instance: `{hard['non_persistent_chosen']}`",
            f"- `non_persistent_anchor_v0` score margin top1-top2: {hard['non_persistent_score_margin_top1_top2']}",
            f"- `non_persistent_anchor_v0` candidate entropy: {hard['non_persistent_candidate_entropy']}",
            "",
            "## Ablations",
            "",
            "| Ablation | Significant exact top1 | Significant Recall@3 | Hard row 41 rank | Hard row 41 chosen |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for ablation, item in metrics["ablations"].items():
        lines.append(
            f"| {ablation} | {item['significant_exact_top1_rate']} | {item['significant_recall_at_3']} | {item['hard_row_41_rank']} | `{item['hard_row_41_chosen']}` |"
        )
    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No navigation claim is supported.",
            "- No RGB-D perception or open-vocabulary perception claim is supported.",
            "- `non_persistent_anchor_v0` still uses annotation-level `semseg.v2.json` and `3DSSG` relation labels.",
            "- Ranking does not use persistent cross-scan object-id anchors.",
            "- `oracle_current_pose` is an upper bound, not a deployable method.",
            "",
            "## Agent Inference",
            "",
            "- This smoke directly tests whether the `instance_evidence_v0` signal survives without stable annotation ids.",
            "- If `non_persistent_anchor_v0` keeps hard row `41` near the top, H001 becomes less annotation-dependent.",
            "- If exact recovery drops but Recall@3 remains high, the next route is likely uncertainty-aware search rather than direct recovery.",
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--query-rows", type=Path, default=DEFAULT_QUERY_ROWS)
    parser.add_argument("--instance-predictions", type=Path, default=DEFAULT_INSTANCE_PREDICTIONS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--success-threshold-m", type=float, default=0.5)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    query_rows = load_jsonl(args.query_rows)
    ref_objects = load_semseg_objects(
        args.dataset_root / "3RScan" / "scans" / REFERENCE_SCAN_ID / "semseg.v2.json"
    )
    rescan_objects = load_semseg_objects(
        args.dataset_root / "3RScan" / "scans" / RESCAN_ID / "semseg.v2.json"
    )
    relationships = load_relationships(args.dataset_root / "3DSSG" / "relationships.json")
    pair_metadata = find_pair_metadata(
        load_json(args.dataset_root / "3RScan" / "files" / "3RScan.json"),
        REFERENCE_SCAN_ID,
        RESCAN_ID,
    )
    scene_inverse = invert_rigid_row_transform(pair_metadata["transform"])
    feature_rows, rows_by_object = build_feature_rows(
        query_rows, ref_objects, rescan_objects, relationships, scene_inverse
    )

    previous_instance_predictions = {
        row["object_instance_id_ref"]: row
        for row in load_jsonl(args.instance_predictions)
        if row.get("policy") == "instance_evidence_v0"
    }
    predictions = []
    for row in query_rows:
        object_rows = rows_by_object[row["object_instance_id_ref"]]
        ranked_label = []
        for rank, item in enumerate(
            sorted(
                object_rows,
                key=lambda item: (
                    item["distance_to_old_scene_aligned_m"],
                    int(item["candidate_instance_id"]),
                ),
            ),
            start=1,
        ):
            ranked_label.append(
                {
                    **item,
                    "label_rank": rank,
                    "centroid": rescan_objects[item["candidate_instance_id"]]["centroid"],
                }
            )
        ranked_np = [
            {
                **item,
                "centroid": rescan_objects[item["candidate_instance_id"]]["centroid"],
            }
            for item in sorted_feature_rows_for_object(
                rows_by_object, row["object_instance_id_ref"], "full_non_persistent"
            )
        ]
        for policy in [
            "scene_aligned_static_map",
            "staleness_only",
            "label_nearest_current_observation",
            "label_top3_current_observation",
            "non_persistent_anchor_v0",
            "oracle_current_pose",
        ]:
            pred = predict(policy, row, ranked_label, ranked_np, args.success_threshold_m)
            predictions.append({**row, **pred})
        if row["object_instance_id_ref"] in previous_instance_predictions:
            predictions.append(previous_instance_predictions[row["object_instance_id_ref"]])

    significant_rows = [row for row in query_rows if row["significant_moved"]]
    low_motion_rows = [row for row in query_rows if not row["significant_moved"]]
    metrics = {
        "all_row_valid": {
            policy: summarize_policy(policy, predictions, "all_row_valid", query_rows)
            for policy in POLICIES
        },
        "significant_moved": {
            policy: summarize_policy(policy, predictions, "significant_moved", significant_rows)
            for policy in POLICIES
        },
        "low_motion": {
            policy: summarize_policy(policy, predictions, "low_motion", low_motion_rows)
            for policy in POLICIES
        },
        "ablations": summarize_ablations(query_rows, rows_by_object),
    }
    hard_predictions = [row for row in predictions if row["object_instance_id_ref"] == "41"]
    label_hard = next(row for row in hard_predictions if row["policy"] == "label_nearest_current_observation")
    instance_hard = next(row for row in hard_predictions if row["policy"] == "instance_evidence_v0")
    np_hard = next(row for row in hard_predictions if row["policy"] == "non_persistent_anchor_v0")
    metrics["hard_row_41"] = {
        "label_nearest_rank": label_hard["target_rank"],
        "instance_evidence_rank": instance_hard["target_rank"],
        "non_persistent_rank": np_hard["target_rank"],
        "non_persistent_chosen": np_hard.get("chosen_instance_id"),
        "non_persistent_score_margin_top1_top2": np_hard.get("score_margin_top1_top2"),
        "non_persistent_candidate_entropy": np_hard.get("candidate_entropy"),
        "non_persistent_candidate_set_size_under_margin_0_1": np_hard.get(
            "candidate_set_size_under_margin_0_1"
        ),
    }
    same_label_counts = sorted(
        {len(rows_by_object[row["object_instance_id_ref"]]) for row in query_rows}
    )
    coverage = {
        "dataset_root": str(args.dataset_root),
        "reference_scan_id": REFERENCE_SCAN_ID,
        "rescan_id": RESCAN_ID,
        "query_rows": len(query_rows),
        "significant_moved_rows": len(significant_rows),
        "low_motion_rows": len(low_motion_rows),
        "same_label_candidate_count": same_label_counts[0]
        if len(same_label_counts) == 1
        else same_label_counts,
        "hard_row_object_id": "41",
        "uses_annotation_level_current_observation": True,
        "ranking_uses_persistent_cross_scan_ids": False,
        "uses_exact_current_pose_for_ranking": False,
        "uses_navigation": False,
        "success_threshold_m": args.success_threshold_m,
        "status": "complete" if significant_rows and feature_rows else "needs_more_rows",
    }

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "feature_rows.jsonl", feature_rows)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_report(args.out_dir, coverage, metrics)

    print(
        json.dumps(
            {
                "coverage": coverage,
                "significant_moved": metrics["significant_moved"],
                "hard_row_41": metrics["hard_row_41"],
                "ablations": metrics["ablations"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
