#!/usr/bin/env python3
"""Build E001 query and candidate rows.

Rows are context-expanded from the start so later E002/E003/E004 stages can add
path cost, perception proposals, and task-conditioned memory trust without
changing the denominator.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_MANIFEST = EXPERIMENT_ROOT / "artifacts" / "E001-M01_pair_manifest_v0" / "manifest.jsonl"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M02_query_construction_v0"
QUERY_VERSION = "e001_query_v0"

GEOMETRY_VALID_THRESHOLD_M = 1.0
SIGNIFICANT_MOVED_THRESHOLD_M = 1.0
LOW_MOTION_THRESHOLD_M = 0.25
SUCCESS_THRESHOLD_M = 0.5

TASK_CONTEXT_PROFILES = {
    "routine_fetch": {
        "success_reward": 1.0,
        "check_cost": 0.15,
        "failure_cost": 0.0,
        "max_candidate_budget": 3,
        "high_ambiguity_budget": 2,
        "reobservation_threshold_profile": "routine",
    },
    "high_value_fetch": {
        "success_reward": 3.0,
        "check_cost": 0.15,
        "failure_cost": 0.25,
        "max_candidate_budget": 5,
        "high_ambiguity_budget": 5,
        "reobservation_threshold_profile": "high_value",
    },
    "noisy_high_value_fetch": {
        "success_reward": 3.0,
        "check_cost": 0.15,
        "failure_cost": 0.25,
        "max_candidate_budget": 5,
        "high_ambiguity_budget": 5,
        "reobservation_threshold_profile": "noisy_high_value",
    },
}


def load_json(path: Path) -> Any:
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


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def round_point(point: list[float]) -> list[float]:
    return [round(value, 6) for value in point]


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


def load_semseg_objects(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    objects: dict[str, dict[str, Any]] = {}
    for group in data.get("segGroups", []):
        object_id = str(group.get("objectId", group.get("id")))
        centroid = group.get("obb", {}).get("centroid")
        if centroid is None:
            continue
        objects[object_id] = {
            "object_id": object_id,
            "label": group.get("label", ""),
            "centroid": [float(value) for value in centroid],
        }
    return objects


def metadata_index(dataset_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    metadata = load_json(dataset_root / "3RScan" / "files" / "3RScan.json")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for group in metadata:
        reference_scan_id = group.get("reference")
        if not reference_scan_id:
            continue
        for pair_metadata in group.get("scans", []):
            rescan_id = pair_metadata.get("reference")
            if rescan_id:
                index[(str(reference_scan_id), str(rescan_id))] = pair_metadata
    return index


def semseg_path(dataset_root: Path, scan_id: str) -> Path:
    return dataset_root / "3RScan" / "scans" / scan_id / "semseg.v2.json"


def row_band(planar_displacement_m: float) -> str:
    if planar_displacement_m >= SIGNIFICANT_MOVED_THRESHOLD_M:
        return "significant_moved"
    if planar_displacement_m <= LOW_MOTION_THRESHOLD_M:
        return "low_motion_control"
    return "mid_motion_review"


def expected_memory_state(band: str) -> str:
    if band == "significant_moved":
        return "needs_reobservation"
    if band == "low_motion_control":
        return "trusted_or_low_motion"
    return "review"


def ambiguity_band(candidate_count: int) -> str:
    if candidate_count <= 1:
        return "trivial_candidate"
    if candidate_count <= 3:
        return "rank_sensitive"
    return "high_ambiguity"


def transform_errors(
    reference_centroid: list[float],
    target_centroid: list[float],
    pair_metadata: dict[str, Any],
    rigid_item: dict[str, Any],
) -> dict[str, float]:
    scene_transform = pair_metadata["transform"]
    scene_inverse = invert_rigid_row_transform(scene_transform)
    object_transform = rigid_item["transform"]
    object_inverse = invert_rigid_row_transform(object_transform)
    transformed = {
        "object_direct_error_m": transform_point_row(reference_centroid, object_transform),
        "object_inverse_error_m": transform_point_row(reference_centroid, object_inverse),
        "scene_direct_error_m": transform_point_row(reference_centroid, scene_transform),
        "scene_inverse_error_m": transform_point_row(reference_centroid, scene_inverse),
    }
    return {key: point_distance(value, target_centroid) for key, value in transformed.items()}


def ranked_candidates(
    rescan_objects: dict[str, dict[str, Any]],
    target_label: str,
    target_instance_id: str,
    old_scene_aligned_centroid: list[float],
) -> list[dict[str, Any]]:
    same_label = [
        obj for obj in rescan_objects.values() if obj.get("label") == target_label
    ]
    ranked = sorted(
        same_label,
        key=lambda obj: (
            point_distance(old_scene_aligned_centroid, obj["centroid"]),
            int(obj["object_id"]) if obj["object_id"].isdigit() else obj["object_id"],
        ),
    )
    rows = []
    for rank, obj in enumerate(ranked, start=1):
        distance = point_distance(old_scene_aligned_centroid, obj["centroid"])
        rows.append(
            {
                "candidate_instance_id": obj["object_id"],
                "candidate_label": obj["label"],
                "candidate_centroid": round_point(obj["centroid"]),
                "candidate_rank_semantic": rank,
                "candidate_rank_non_persistent": rank,
                "candidate_score_semantic": 1.0,
                "candidate_score_non_persistent": round(1.0 / (1.0 + distance), 6),
                "candidate_is_target": obj["object_id"] == target_instance_id,
                "candidate_visit_order_index": rank,
                "candidate_visit_policy": "ranked_candidates_then_old_location_check",
                "candidate_euclidean_cost_from_old_m": round_or_none(distance),
                "candidate_path_cost_m": None,
                "candidate_observation_source": "annotation_semseg",
                "candidate_proposal_confidence": None,
            }
        )
    return rows


def build_base_rows(
    dataset_root: Path,
    manifest_rows: list[dict[str, Any]],
    pair_index: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pair_rows: list[dict[str, Any]] = []
    base_query_rows: list[dict[str, Any]] = []
    base_candidate_rows: list[dict[str, Any]] = []

    for manifest_row in manifest_rows:
        if manifest_row["eligibility_status"] != "ready_minimal":
            continue
        reference_scan_id = manifest_row["reference_scan_id"]
        rescan_id = manifest_row["rescan_id"]
        pair_metadata = pair_index[(reference_scan_id, rescan_id)]
        reference_objects = load_semseg_objects(semseg_path(dataset_root, reference_scan_id))
        rescan_objects = load_semseg_objects(semseg_path(dataset_root, rescan_id))
        scene_inverse = invert_rigid_row_transform(pair_metadata["transform"])

        for rigid_item in pair_metadata.get("rigid", []):
            if not isinstance(rigid_item, dict):
                continue
            ref_id = str(rigid_item["instance_reference"])
            rescan_obj_id = str(rigid_item["instance_rescan"])
            ref_obj = reference_objects.get(ref_id)
            rescan_obj = rescan_objects.get(rescan_obj_id)
            label_match = bool(ref_obj and rescan_obj and ref_obj["label"] == rescan_obj["label"])
            errors: dict[str, float] = {}
            best_error: float | None = None
            best_candidate: str | None = None
            old_scene_aligned: list[float] | None = None
            scene_error: float | None = None
            scene_planar_error: float | None = None
            if ref_obj and rescan_obj:
                errors = transform_errors(ref_obj["centroid"], rescan_obj["centroid"], pair_metadata, rigid_item)
                best_candidate = min(errors, key=lambda key: errors[key])
                best_error = errors[best_candidate]
                old_scene_aligned = transform_point_row(ref_obj["centroid"], scene_inverse)
                scene_error = point_distance(old_scene_aligned, rescan_obj["centroid"])
                scene_planar_error = planar_distance(old_scene_aligned, rescan_obj["centroid"])

            row_geometry_valid = bool(
                label_match
                and best_error is not None
                and best_error <= GEOMETRY_VALID_THRESHOLD_M
                and old_scene_aligned is not None
                and scene_planar_error is not None
            )
            pair_row = {
                "pair_uid": manifest_row["pair_uid"],
                "reference_scan_id": reference_scan_id,
                "rescan_id": rescan_id,
                "metadata_split": manifest_row["metadata_split"],
                "object_instance_id_ref": ref_id,
                "object_instance_id_rescan": rescan_obj_id,
                "ref_label": ref_obj.get("label") if ref_obj else None,
                "rescan_label": rescan_obj.get("label") if rescan_obj else None,
                "ref_geometry_join": ref_obj is not None,
                "rescan_geometry_join": rescan_obj is not None,
                "label_match": label_match,
                "row_geometry_valid": row_geometry_valid,
                "row_best_candidate": best_candidate,
                "row_geometry_error_m": round_or_none(best_error),
                "scene_aligned_static_error_m": round_or_none(scene_error),
                "scene_aligned_static_planar_error_m": round_or_none(scene_planar_error),
                **{key: round_or_none(value) for key, value in errors.items()},
            }
            pair_rows.append(pair_row)
            if not row_geometry_valid or ref_obj is None or rescan_obj is None or old_scene_aligned is None:
                continue

            candidates = ranked_candidates(rescan_objects, ref_obj["label"], rescan_obj_id, old_scene_aligned)
            band = row_band(scene_planar_error)
            base_row_uid = f"{manifest_row['pair_uid']}:{ref_id}"
            candidate_count = len(candidates)
            base_query_row = {
                "query_version": QUERY_VERSION,
                "base_row_uid": base_row_uid,
                "pair_uid": manifest_row["pair_uid"],
                "reference_scan_id": reference_scan_id,
                "rescan_id": rescan_id,
                "metadata_split": manifest_row["metadata_split"],
                "object_instance_id_ref": ref_id,
                "object_instance_id_rescan": rescan_obj_id,
                "object_label": ref_obj["label"],
                "query_text_template": f"find the {ref_obj['label']}",
                "change_type": "rigid_moved",
                "row_band": band,
                "old_memory_is_stale": band == "significant_moved",
                "expected_memory_state": expected_memory_state(band),
                "old_scene_aligned_centroid": round_point(old_scene_aligned),
                "current_target_centroid": round_point(rescan_obj["centroid"]),
                "scene_aligned_static_error_m": round_or_none(scene_error),
                "scene_aligned_static_planar_error_m": round_or_none(scene_planar_error),
                "row_geometry_error_m": round_or_none(best_error),
                "row_best_candidate": best_candidate,
                "same_label_candidate_count": candidate_count,
                "ambiguity_band": ambiguity_band(candidate_count),
                "evaluation_scope": "dynamic_object_search_proxy",
                "success_threshold_m": SUCCESS_THRESHOLD_M,
                "search_start_policy": "not_set",
                "old_location_dead_end_expected": band == "significant_moved",
                "old_location_dead_end_cost_unit": "candidate_visit",
                "candidate_visit_order_policy": "ranked_candidates_then_old_location_check",
                "expected_search_cost_unit": "candidate_count",
                "expected_search_cost_proxy_ready": True,
                "path_cost_ready": False,
                "path_cost_profile_id": None,
                "navmesh_or_free_space_source": None,
                "proxy_sr_ready": True,
                "proxy_spl_ready": True,
                "observation_source": "annotation_semseg",
                "current_proposal_source": "semseg.v2.json",
                "rgbd_sequence_available": bool(manifest_row["rescan_payload"]["sequence"]),
                "open_vocab_proposal_source": None,
                "perception_profile_id": "oracle_annotation",
                "proposal_noise_profile_id": "none",
                "target_observable_assumption": "annotation_target_present",
                "e003_rgbd_ready": False,
                "e003_open_vocab_ready": False,
            }
            base_query_rows.append(base_query_row)
            for candidate in candidates:
                base_candidate_rows.append(
                    {
                        "base_row_uid": base_row_uid,
                        "pair_uid": manifest_row["pair_uid"],
                        "reference_scan_id": reference_scan_id,
                        "rescan_id": rescan_id,
                        "metadata_split": manifest_row["metadata_split"],
                        "object_instance_id_ref": ref_id,
                        "object_label": ref_obj["label"],
                        "same_label_candidate_count": candidate_count,
                        "ambiguity_band": ambiguity_band(candidate_count),
                        **candidate,
                    }
                )
    return pair_rows, base_query_rows, base_candidate_rows


def expand_contexts(
    base_query_rows: list[dict[str, Any]],
    base_candidate_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_base: dict[str, list[dict[str, Any]]] = {}
    for row in base_candidate_rows:
        candidates_by_base.setdefault(row["base_row_uid"], []).append(row)

    query_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for base_row in base_query_rows:
        for context_id, profile in TASK_CONTEXT_PROFILES.items():
            row_uid = f"{base_row['base_row_uid']}:{context_id}"
            query_row = {
                **base_row,
                "row_uid": row_uid,
                "task_context_id": context_id,
                "intent_condition_source": "structured_task_context",
                "success_reward": profile["success_reward"],
                "check_cost": profile["check_cost"],
                "failure_cost": profile["failure_cost"],
                "max_candidate_budget": profile["max_candidate_budget"],
                "high_ambiguity_budget": profile["high_ambiguity_budget"],
                "memory_trust_policy": "task_conditioned_budget_v0",
                "reobservation_policy": "reobserve_if_stale_or_high_uncertainty",
                "reobservation_threshold_profile": profile["reobservation_threshold_profile"],
            }
            query_rows.append(query_row)
            for candidate in candidates_by_base.get(base_row["base_row_uid"], []):
                candidate_rows.append(
                    {
                        **candidate,
                        "row_uid": row_uid,
                        "task_context_id": context_id,
                    }
                )
    return query_rows, candidate_rows


def build_report(coverage: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# E001-M02 Query Construction",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Dataset root: `{coverage['dataset_root']}`",
        f"- Manifest path: `{coverage['manifest_path']}`",
        f"- Ready manifest pairs: {coverage['ready_manifest_pairs']}",
        f"- Validated pair count: {coverage['validated_pair_count']}",
        f"- Pair rigid rows: {coverage['pair_rows']}",
        f"- Base query rows: {coverage['base_query_rows']}",
        f"- Context-expanded query rows: {coverage['query_rows']}",
        f"- Candidate rows: {coverage['candidate_rows']}",
        f"- Significant moved base rows: {coverage['base_row_band_counts'].get('significant_moved', 0)}",
        f"- Low-motion control base rows: {coverage['base_row_band_counts'].get('low_motion_control', 0)}",
        f"- Mid-motion review base rows: {coverage['base_row_band_counts'].get('mid_motion_review', 0)}",
        f"- Rows with `rgbd_sequence_available`: {coverage['rgbd_sequence_available_query_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Context Expansion",
        "",
        "| `task_context_id` | Query rows |",
        "| --- | ---: |",
    ]
    for context_id, count in sorted(coverage["task_context_counts"].items()):
        lines.append(f"| `{context_id}` | {count} |")

    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E001-M02 supports proxy query construction for semantic-pair dynamic object search.",
            "- Human intent is represented only as structured task context that changes memory trust, re-observation threshold, and candidate budget.",
            "- E001-M02 still does not support real navigation `SR` / `SPL`, RGB-D perception robustness, open-vocabulary perception robustness, learned policy, or natural-language intention understanding.",
            "",
            "## 에이전트 추론",
            "",
            "- `row_uid` is context-expanded, while `base_row_uid` preserves the object-level denominator.",
            "- E002 can attach `candidate_path_cost_m`, `path_cost_profile_id`, and path-aware `candidate_visit_order_policy` without rebuilding the query set.",
            "- E003 can replace `annotation_semseg` candidates with RGB-D or open-vocabulary proposals while preserving the same target rows.",
            "- E004 can compare task contexts directly because every base row is expanded over the same structured context profiles.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E001-M02. Continue to E001 baseline evaluation.",
            "",
            "## Outputs",
            "",
            "- `pair_rows.jsonl`",
            "- `base_query_rows.jsonl`",
            "- `query_rows.jsonl`",
            "- `candidate_rows.jsonl`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = load_jsonl(args.manifest)
    ready_manifest_rows = [row for row in manifest_rows if row["eligibility_status"] == "ready_minimal"]
    pair_index = metadata_index(args.dataset_root)
    pair_rows, base_query_rows, base_candidate_rows = build_base_rows(
        args.dataset_root, manifest_rows, pair_index
    )
    query_rows, candidate_rows = expand_contexts(base_query_rows, base_candidate_rows)

    validated_pair_count = len({row["pair_uid"] for row in base_query_rows})
    base_band_counts = Counter(row["row_band"] for row in base_query_rows)
    context_band_counts = Counter(row["row_band"] for row in query_rows)
    task_context_counts = Counter(row["task_context_id"] for row in query_rows)
    ambiguity_counts = Counter(row["ambiguity_band"] for row in base_query_rows)
    split_counts = Counter(str(row["metadata_split"]) for row in base_query_rows)

    coverage = {
        "status": "ready" if base_query_rows else "blocked",
        "dataset_root": str(args.dataset_root),
        "manifest_path": str(args.manifest),
        "query_version": QUERY_VERSION,
        "thresholds": {
            "geometry_valid_threshold_m": GEOMETRY_VALID_THRESHOLD_M,
            "significant_moved_threshold_m": SIGNIFICANT_MOVED_THRESHOLD_M,
            "low_motion_threshold_m": LOW_MOTION_THRESHOLD_M,
            "mid_motion_range_m": [LOW_MOTION_THRESHOLD_M, SIGNIFICANT_MOVED_THRESHOLD_M],
            "success_threshold_m": SUCCESS_THRESHOLD_M,
        },
        "ready_manifest_pairs": len(ready_manifest_rows),
        "validated_pair_count": validated_pair_count,
        "pair_rows": len(pair_rows),
        "base_query_rows": len(base_query_rows),
        "query_rows": len(query_rows),
        "candidate_rows": len(candidate_rows),
        "base_candidate_rows": len(base_candidate_rows),
        "base_row_band_counts": dict(sorted(base_band_counts.items())),
        "context_row_band_counts": dict(sorted(context_band_counts.items())),
        "task_context_counts": dict(sorted(task_context_counts.items())),
        "ambiguity_band_counts": dict(sorted(ambiguity_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "e002_expected_search_cost_proxy_ready_rows": sum(
            1 for row in query_rows if row["expected_search_cost_proxy_ready"]
        ),
        "e002_path_cost_ready_rows": sum(1 for row in query_rows if row["path_cost_ready"]),
        "rgbd_sequence_available_query_rows": sum(
            1 for row in query_rows if row["rgbd_sequence_available"]
        ),
        "e003_rgbd_ready_rows": sum(1 for row in query_rows if row["e003_rgbd_ready"]),
        "e003_open_vocab_ready_rows": sum(1 for row in query_rows if row["e003_open_vocab_ready"]),
        "uses_annotation_level_current_observation": True,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "uses_natural_language_intent_understanding": False,
        "outputs": {
            "pair_rows": str(args.out_dir / "pair_rows.jsonl"),
            "base_query_rows": str(args.out_dir / "base_query_rows.jsonl"),
            "query_rows": str(args.out_dir / "query_rows.jsonl"),
            "candidate_rows": str(args.out_dir / "candidate_rows.jsonl"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }

    write_jsonl(args.out_dir / "pair_rows.jsonl", pair_rows)
    write_jsonl(args.out_dir / "base_query_rows.jsonl", base_query_rows)
    write_jsonl(args.out_dir / "query_rows.jsonl", query_rows)
    write_jsonl(args.out_dir / "candidate_rows.jsonl", candidate_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "ready_manifest_pairs": coverage["ready_manifest_pairs"],
                "validated_pair_count": coverage["validated_pair_count"],
                "base_query_rows": coverage["base_query_rows"],
                "query_rows": coverage["query_rows"],
                "candidate_rows": coverage["candidate_rows"],
                "base_row_band_counts": coverage["base_row_band_counts"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
