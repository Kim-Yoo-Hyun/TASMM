#!/usr/bin/env python3
"""Select H001 reference-rescan pairs with meaningful stale-object displacement.

This is a hypothesis-stage data gate. It checks local 3RScan semantic payloads
for reference-rescan pairs where a scene-aligned old object location differs
from the current rescan object location. It does not run navigation and does
not use object-specific transforms as a policy input.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "stale_pair_candidates"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def distance(a: list[float], b: list[float]) -> float:
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
            "label": group.get("label", ""),
            "centroid": [float(value) for value in centroid],
        }
    return objects


def payload_status(dataset_root: Path, scan_id: str) -> dict:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    return {
        "scan_id": scan_id,
        "scan_dir": str(scan_dir),
        "semseg": (scan_dir / "semseg.v2.json").is_file(),
        "sequence_zip": (scan_dir / "sequence.zip").is_file(),
        "sequence_dir": (scan_dir / "sequence").is_dir(),
    }


def summarize_pair(
    dataset_root: Path,
    reference_scan_id: str,
    rescan_id: str,
    pair_metadata: dict,
    thresholds: list[float],
) -> tuple[dict, list[dict]]:
    ref_payload = payload_status(dataset_root, reference_scan_id)
    rescan_payload = payload_status(dataset_root, rescan_id)
    if not ref_payload["semseg"] or not rescan_payload["semseg"]:
        return (
            {
                "reference_scan_id": reference_scan_id,
                "rescan_id": rescan_id,
                "status": "missing_semseg",
                "reference_payload": ref_payload,
                "rescan_payload": rescan_payload,
            },
            [],
        )

    ref_objects = load_semseg_objects(
        dataset_root / "3RScan" / "scans" / reference_scan_id / "semseg.v2.json"
    )
    rescan_objects = load_semseg_objects(
        dataset_root / "3RScan" / "scans" / rescan_id / "semseg.v2.json"
    )
    scene_inverse = invert_rigid_row_transform(pair_metadata["transform"])

    rigid_rows = []
    for item in pair_metadata.get("rigid", []):
        ref_id = str(item["instance_reference"])
        rescan_obj_id = str(item["instance_rescan"])
        ref_obj = ref_objects.get(ref_id)
        rescan_obj = rescan_objects.get(rescan_obj_id)
        row = {
            "reference_scan_id": reference_scan_id,
            "rescan_id": rescan_id,
            "instance_reference": ref_id,
            "instance_rescan": rescan_obj_id,
            "ref_label": ref_obj.get("label") if ref_obj else None,
            "rescan_label": rescan_obj.get("label") if rescan_obj else None,
            "ref_geometry_join": ref_obj is not None,
            "rescan_geometry_join": rescan_obj is not None,
            "label_match": bool(ref_obj and rescan_obj and ref_obj.get("label") == rescan_obj.get("label")),
            "scene_aligned_static_error_m": None,
            "scene_aligned_static_planar_error_m": None,
            "object_direct_error_m": None,
        }
        if ref_obj and rescan_obj:
            scene_aligned_old = transform_point_row(ref_obj["centroid"], scene_inverse)
            object_direct = transform_point_row(ref_obj["centroid"], item["transform"])
            row["scene_aligned_old_centroid"] = scene_aligned_old
            row["current_rescan_centroid"] = rescan_obj["centroid"]
            row["scene_aligned_static_error_m"] = distance(scene_aligned_old, rescan_obj["centroid"])
            row["scene_aligned_static_planar_error_m"] = planar_distance(
                scene_aligned_old, rescan_obj["centroid"]
            )
            row["object_direct_error_m"] = distance(object_direct, rescan_obj["centroid"])
        rigid_rows.append(row)

    valid_rows = [
        row
        for row in rigid_rows
        if row["label_match"]
        and row["scene_aligned_static_error_m"] is not None
        and row["object_direct_error_m"] is not None
    ]
    static_errors = [row["scene_aligned_static_error_m"] for row in valid_rows]
    static_planar_errors = [row["scene_aligned_static_planar_error_m"] for row in valid_rows]
    object_direct_errors = [row["object_direct_error_m"] for row in valid_rows]
    removed_ids = [str(item) for item in pair_metadata.get("removed", [])]
    removed_ref_join = sum(1 for object_id in removed_ids if object_id in ref_objects)
    removed_absent = sum(1 for object_id in removed_ids if object_id not in rescan_objects)

    moved_counts = {
        f"moved_gt_{str(threshold).replace('.', '_')}m": sum(
            1 for value in static_planar_errors if value >= threshold
        )
        for threshold in thresholds
    }
    top_displacements = sorted(
        [
            {
                "instance_reference": row["instance_reference"],
                "instance_rescan": row["instance_rescan"],
                "label": row["ref_label"],
                "scene_aligned_static_planar_error_m": round_or_none(
                    row["scene_aligned_static_planar_error_m"]
                ),
                "scene_aligned_static_error_m": round_or_none(row["scene_aligned_static_error_m"]),
                "object_direct_error_m": round_or_none(row["object_direct_error_m"]),
            }
            for row in valid_rows
        ],
        key=lambda item: item["scene_aligned_static_planar_error_m"] or 0.0,
        reverse=True,
    )[:5]

    score = (
        moved_counts.get("moved_gt_1_0m", 0) * 4
        + moved_counts.get("moved_gt_0_5m", 0) * 2
        + moved_counts.get("moved_gt_0_25m", 0)
    )
    if rescan_payload["sequence_zip"] or rescan_payload["sequence_dir"]:
        score += 2
    if ref_payload["sequence_zip"] or ref_payload["sequence_dir"]:
        score += 1

    summary = {
        "reference_scan_id": reference_scan_id,
        "rescan_id": rescan_id,
        "status": "ready" if valid_rows else "no_valid_rigid_rows",
        "reference_payload": ref_payload,
        "rescan_payload": rescan_payload,
        "metadata_rigid": len(pair_metadata.get("rigid", [])),
        "valid_rigid_rows": len(valid_rows),
        "metadata_removed": len(removed_ids),
        "removed_ref_join": removed_ref_join,
        "removed_absent_in_rescan_semseg": removed_absent,
        "scene_aligned_static_planar_median_m": round_or_none(median(static_planar_errors)),
        "scene_aligned_static_planar_mean_m": round_or_none(
            sum(static_planar_errors) / len(static_planar_errors) if static_planar_errors else None
        ),
        "scene_aligned_static_planar_max_m": round_or_none(max(static_planar_errors) if static_planar_errors else None),
        "scene_aligned_static_median_m": round_or_none(median(static_errors)),
        "object_direct_median_error_m": round_or_none(median(object_direct_errors)),
        "object_direct_max_error_m": round_or_none(max(object_direct_errors) if object_direct_errors else None),
        "top_displacements": top_displacements,
        "score": score,
        **moved_counts,
    }
    return summary, rigid_rows


def write_report(path: Path, summaries: list[dict], coverage: dict) -> None:
    lines = [
        "# Stale Pair Candidate Selection",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Local metadata pairs scanned: {coverage['metadata_pairs_scanned']}",
        f"- Pairs with local semantic payload: {coverage['pairs_with_local_semseg']}",
        f"- Ready pairs: {coverage['ready_pairs']}",
        f"- Rows written: {coverage['moved_rows_written']}",
        "",
        "## Top Pair Candidates",
        "",
        "| Reference | Rescan | Valid rigid | >=0.25m | >=0.5m | >=1.0m | Median planar | Max planar | Removed absent | Sequence | Score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for item in summaries[:10]:
        sequence = "ref+rescan" if (
            (item["reference_payload"]["sequence_zip"] or item["reference_payload"]["sequence_dir"])
            and (item["rescan_payload"]["sequence_zip"] or item["rescan_payload"]["sequence_dir"])
        ) else "ref" if (
            item["reference_payload"]["sequence_zip"] or item["reference_payload"]["sequence_dir"]
        ) else "rescan" if (
            item["rescan_payload"]["sequence_zip"] or item["rescan_payload"]["sequence_dir"]
        ) else "none"
        lines.append(
            "| {ref} | {rescan} | {valid} | {m025} | {m05} | {m10} | {median} | {maxv} | {removed} | {sequence} | {score} |".format(
                ref=item["reference_scan_id"],
                rescan=item["rescan_id"],
                valid=item["valid_rigid_rows"],
                m025=item.get("moved_gt_0_25m", 0),
                m05=item.get("moved_gt_0_5m", 0),
                m10=item.get("moved_gt_1_0m", 0),
                median=item["scene_aligned_static_planar_median_m"],
                maxv=item["scene_aligned_static_planar_max_m"],
                removed=item["removed_absent_in_rescan_semseg"],
                sequence=sequence,
                score=item["score"],
            )
        )
    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No navigation claim is supported.",
            "- No exact recovery claim is supported by this selection alone.",
            "- This gate only checks whether local pairs contain meaningful scene-aligned stale-object displacement.",
            "",
            "## Agent Inference",
            "",
            "- H001 should use scene-aligned old locations before judging stale memory.",
            "- A useful next smoke should run observation-grounded update on a high-displacement ready pair, not on raw unaligned coordinates.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--thresholds", type=float, nargs="+", default=[0.25, 0.5, 1.0])
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    metadata = load_json(args.dataset_root / "3RScan" / "files" / "3RScan.json")
    all_summaries = []
    all_rows = []
    scanned = 0
    local_semseg = 0
    for group in metadata:
        reference_scan_id = group.get("reference")
        if not reference_scan_id:
            continue
        for pair_metadata in group.get("scans", []):
            rescan_id = pair_metadata.get("reference")
            if not rescan_id:
                continue
            scanned += 1
            summary, rows = summarize_pair(
                args.dataset_root,
                reference_scan_id,
                rescan_id,
                pair_metadata,
                args.thresholds,
            )
            if summary["status"] != "missing_semseg":
                local_semseg += 1
                all_summaries.append(summary)
                all_rows.extend(rows)

    all_summaries.sort(
        key=lambda item: (
            item.get("score", 0),
            item.get("moved_gt_1_0m", 0),
            item.get("scene_aligned_static_planar_max_m") or 0.0,
            item.get("valid_rigid_rows", 0),
        ),
        reverse=True,
    )
    ready = [item for item in all_summaries if item["status"] == "ready"]
    coverage = {
        "dataset_root": str(args.dataset_root),
        "metadata_pairs_scanned": scanned,
        "pairs_with_local_semseg": local_semseg,
        "ready_pairs": len(ready),
        "moved_rows_written": len(all_rows),
        "status": "ready" if ready else "blocked",
    }

    with (args.out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_jsonl(args.out_dir / "candidate_pairs.jsonl", all_summaries)
    write_jsonl(args.out_dir / "moved_rows.jsonl", all_rows)
    write_report(args.out_dir / "report.md", all_summaries, coverage)

    print(json.dumps({"coverage": coverage, "top_candidates": all_summaries[:5]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
