#!/usr/bin/env python3
"""Validate H001 reference-rescan geometry transform direction."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "pair_geometry_check"
REFERENCE_SCAN_ID = "ddc73797-765b-241a-9e2c-097c5989baf6"
RESCAN_ID = "c7895f07-339c-2d13-8176-7418b6e8d7ce"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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
        object_id = str(group.get("objectId", group.get("id")))
        obb = group.get("obb", {})
        centroid = obb.get("centroid")
        if centroid is None:
            continue
        objects[object_id] = {
            "label": group.get("label"),
            "centroid": [float(value) for value in centroid],
            "axes_lengths": [float(value) for value in obb.get("axesLengths", [])],
        }
    return objects


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


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def summarize_candidate(rows: list[dict], key: str) -> dict:
    errors = [row[key] for row in rows if row[key] is not None]
    return {
        "candidate": key,
        "count": len(errors),
        "mean_error_m": sum(errors) / len(errors) if errors else None,
        "median_error_m": median(errors),
        "max_error_m": max(errors) if errors else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--reference-scan-id", default=REFERENCE_SCAN_ID)
    parser.add_argument("--rescan-id", default=RESCAN_ID)
    parser.add_argument("--median-threshold-m", type=float, default=0.35)
    parser.add_argument("--max-threshold-m", type=float, default=1.0)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    pair_metadata = find_pair_metadata(
        load_json(args.dataset_root / "3RScan" / "files" / "3RScan.json"),
        args.reference_scan_id,
        args.rescan_id,
    )
    ref_objects = load_semseg_objects(
        args.dataset_root
        / "3RScan"
        / "scans"
        / args.reference_scan_id
        / "semseg.v2.json"
    )
    rescan_objects = load_semseg_objects(
        args.dataset_root / "3RScan" / "scans" / args.rescan_id / "semseg.v2.json"
    )

    scene_transform = pair_metadata["transform"]
    scene_transform_inverse = invert_rigid_row_transform(scene_transform)

    rigid_rows = []
    for item in pair_metadata.get("rigid", []):
        ref_id = str(item["instance_reference"])
        rescan_id = str(item["instance_rescan"])
        ref_obj = ref_objects.get(ref_id)
        rescan_obj = rescan_objects.get(rescan_id)
        row = {
            "instance_reference": ref_id,
            "instance_rescan": rescan_id,
            "ref_label": ref_obj.get("label") if ref_obj else None,
            "rescan_label": rescan_obj.get("label") if rescan_obj else None,
            "ref_geometry_join": ref_obj is not None,
            "rescan_geometry_join": rescan_obj is not None,
            "label_match": bool(ref_obj and rescan_obj and ref_obj.get("label") == rescan_obj.get("label")),
            "reference_centroid": ref_obj["centroid"] if ref_obj else None,
            "rescan_centroid": rescan_obj["centroid"] if rescan_obj else None,
        }
        if ref_obj and rescan_obj:
            object_transform = item["transform"]
            object_transform_inverse = invert_rigid_row_transform(object_transform)
            candidates = {
                "object_direct_error_m": transform_point_row(ref_obj["centroid"], object_transform),
                "object_inverse_error_m": transform_point_row(ref_obj["centroid"], object_transform_inverse),
                "scene_direct_error_m": transform_point_row(ref_obj["centroid"], scene_transform),
                "scene_inverse_error_m": transform_point_row(ref_obj["centroid"], scene_transform_inverse),
            }
            for key, transformed in candidates.items():
                row[key] = distance(transformed, rescan_obj["centroid"])
            row["best_candidate"] = min(candidates, key=lambda key: row[key])
            row["best_error_m"] = row[row["best_candidate"]]
            row["row_geometry_valid"] = bool(row["label_match"] and row["best_error_m"] <= args.max_threshold_m)
        else:
            for key in [
                "object_direct_error_m",
                "object_inverse_error_m",
                "scene_direct_error_m",
                "scene_inverse_error_m",
            ]:
                row[key] = None
            row["best_candidate"] = None
            row["best_error_m"] = None
            row["row_geometry_valid"] = False
        rigid_rows.append(row)

    candidate_summaries = [
        summarize_candidate(rigid_rows, key)
        for key in [
            "object_direct_error_m",
            "object_inverse_error_m",
            "scene_direct_error_m",
            "scene_inverse_error_m",
        ]
    ]
    best_summary = min(
        [item for item in candidate_summaries if item["count"] > 0],
        key=lambda item: item["median_error_m"],
    )

    removed_rows = []
    for raw_id in pair_metadata.get("removed", []):
        object_id = str(raw_id)
        removed_rows.append(
            {
                "instance_reference": object_id,
                "ref_geometry_join": object_id in ref_objects,
                "present_in_rescan_semseg": object_id in rescan_objects,
                "ref_label": ref_objects.get(object_id, {}).get("label"),
                "rescan_label": rescan_objects.get(object_id, {}).get("label"),
            }
        )

    coverage = {
        "dataset_root": str(args.dataset_root),
        "reference_scan_id": args.reference_scan_id,
        "rescan_id": args.rescan_id,
        "metadata_rigid": len(pair_metadata.get("rigid", [])),
        "metadata_removed": len(pair_metadata.get("removed", [])),
        "reference_semseg_objects": len(ref_objects),
        "rescan_semseg_objects": len(rescan_objects),
        "rigid_ref_geometry_join": sum(1 for row in rigid_rows if row["ref_geometry_join"]),
        "rigid_rescan_geometry_join": sum(1 for row in rigid_rows if row["rescan_geometry_join"]),
        "rigid_label_match": sum(1 for row in rigid_rows if row["label_match"]),
        "rigid_row_geometry_valid": sum(1 for row in rigid_rows if row["row_geometry_valid"]),
        "removed_ref_geometry_join": sum(1 for row in removed_rows if row["ref_geometry_join"]),
        "removed_absent_in_rescan_semseg": sum(
            1 for row in removed_rows if not row["present_in_rescan_semseg"]
        ),
        "candidate_summaries": candidate_summaries,
        "best_transform_candidate": best_summary["candidate"],
        "best_median_error_m": best_summary["median_error_m"],
        "best_max_error_m": best_summary["max_error_m"],
    }
    coverage["rigid_pair_geometry_ready"] = (
        coverage["rigid_ref_geometry_join"] == coverage["metadata_rigid"]
        and coverage["rigid_rescan_geometry_join"] == coverage["metadata_rigid"]
        and coverage["rigid_label_match"] == coverage["metadata_rigid"]
        and coverage["rigid_row_geometry_valid"] == coverage["metadata_rigid"]
        and coverage["best_median_error_m"] is not None
        and coverage["best_median_error_m"] <= args.median_threshold_m
        and coverage["best_max_error_m"] is not None
        and coverage["best_max_error_m"] <= args.max_threshold_m
    )
    coverage["removed_absence_ready"] = (
        coverage["removed_absent_in_rescan_semseg"] == coverage["metadata_removed"]
    )
    coverage["transform_direction_validated"] = (
        coverage["rigid_pair_geometry_ready"] and coverage["removed_absence_ready"]
    )
    coverage["pair_geometry_status"] = (
        "ready"
        if coverage["transform_direction_validated"]
        else "rigid_moved_ready_removed_needs_review"
        if coverage["rigid_pair_geometry_ready"]
        else "partial_rigid_moved_ready_needs_review"
        if coverage["rigid_row_geometry_valid"] > 0
        else "needs_review"
    )

    with (args.out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_jsonl(args.out_dir / "rigid_geometry.jsonl", rigid_rows)
    write_jsonl(args.out_dir / "removed_geometry.jsonl", removed_rows)

    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
