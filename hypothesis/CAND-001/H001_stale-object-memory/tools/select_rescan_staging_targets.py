#!/usr/bin/env python3
"""Select 3RScan rescans worth staging for H001.

This script ranks metadata pairs where the reference semantic payload is local
but the rescan semantic payload may be missing. It estimates object displacement
from the scene transform and object transform, using the reference object
centroid only. This is for data staging triage, not for policy inference.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "rescan_staging_targets"


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
        centroid = group.get("obb", {}).get("centroid")
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
        "semseg": (scan_dir / "semseg.v2.json").is_file(),
        "sequence_zip": (scan_dir / "sequence.zip").is_file(),
        "sequence_dir": (scan_dir / "sequence").is_dir(),
    }


def summarize_target(dataset_root: Path, reference_scan_id: str, pair_metadata: dict) -> tuple[dict | None, list[dict]]:
    ref_payload = payload_status(dataset_root, reference_scan_id)
    if not ref_payload["semseg"]:
        return None, []

    rescan_id = pair_metadata.get("reference")
    rescan_payload = payload_status(dataset_root, rescan_id)
    ref_objects = load_semseg_objects(
        dataset_root / "3RScan" / "scans" / reference_scan_id / "semseg.v2.json"
    )
    scene_inverse = invert_rigid_row_transform(pair_metadata["transform"])

    rows = []
    for item in pair_metadata.get("rigid", []):
        ref_id = str(item["instance_reference"])
        ref_obj = ref_objects.get(ref_id)
        if ref_obj is None:
            continue
        scene_aligned_old = transform_point_row(ref_obj["centroid"], scene_inverse)
        object_direct = transform_point_row(ref_obj["centroid"], item["transform"])
        proxy_planar = planar_distance(scene_aligned_old, object_direct)
        rows.append(
            {
                "reference_scan_id": reference_scan_id,
                "rescan_id": rescan_id,
                "instance_reference": ref_id,
                "instance_rescan": str(item["instance_rescan"]),
                "label": ref_obj["label"],
                "proxy_scene_aligned_motion_planar_m": round(proxy_planar, 6),
            }
        )

    values = [row["proxy_scene_aligned_motion_planar_m"] for row in rows]
    moved_025 = sum(1 for value in values if value >= 0.25)
    moved_05 = sum(1 for value in values if value >= 0.5)
    moved_10 = sum(1 for value in values if value >= 1.0)
    score = moved_10 * 4 + moved_05 * 2 + moved_025
    if rescan_payload["semseg"]:
        score += 2
    if rescan_payload["sequence_zip"] or rescan_payload["sequence_dir"]:
        score += 1

    summary = {
        "reference_scan_id": reference_scan_id,
        "rescan_id": rescan_id,
        "reference_payload": ref_payload,
        "rescan_payload": rescan_payload,
        "metadata_rigid": len(pair_metadata.get("rigid", [])),
        "proxy_rows": len(rows),
        "proxy_planar_median_m": round_or_none(median(values)),
        "proxy_planar_mean_m": round_or_none(sum(values) / len(values) if values else None),
        "proxy_planar_max_m": round_or_none(max(values) if values else None),
        "proxy_moved_gt_0_25m": moved_025,
        "proxy_moved_gt_0_5m": moved_05,
        "proxy_moved_gt_1_0m": moved_10,
        "metadata_removed": len(pair_metadata.get("removed", [])),
        "score": score,
        "top_proxy_displacements": sorted(
            rows,
            key=lambda row: row["proxy_scene_aligned_motion_planar_m"],
            reverse=True,
        )[:5],
    }
    return summary, rows


def write_report(path: Path, summaries: list[dict], coverage: dict) -> None:
    lines = [
        "# Rescan Staging Targets",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Metadata pairs scanned: {coverage['metadata_pairs_scanned']}",
        f"- Pairs with local reference semantic payload: {coverage['pairs_with_reference_semseg']}",
        f"- Candidate rows written: {coverage['candidate_rows_written']}",
        "",
        "## Top Targets",
        "",
        "| Reference | Rescan | Rescan semseg | Rigid | >=0.25m | >=0.5m | >=1.0m | Median proxy | Max proxy | Removed | Score |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summaries[:15]:
        lines.append(
            "| {ref} | {rescan} | {semseg} | {rigid} | {m025} | {m05} | {m10} | {median} | {maxv} | {removed} | {score} |".format(
                ref=item["reference_scan_id"],
                rescan=item["rescan_id"],
                semseg=item["rescan_payload"]["semseg"],
                rigid=item["proxy_rows"],
                m025=item["proxy_moved_gt_0_25m"],
                m05=item["proxy_moved_gt_0_5m"],
                m10=item["proxy_moved_gt_1_0m"],
                median=item["proxy_planar_median_m"],
                maxv=item["proxy_planar_max_m"],
                removed=item["metadata_removed"],
                score=item["score"],
            )
        )
    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No metric claim is supported by proxy staging targets.",
            "- These targets only indicate which rescan semantic payloads may be worth staging next.",
            "",
            "## Agent Inference",
            "",
            "- H001 needs a high-displacement ready pair before observation-grounded update can be judged fairly.",
            "- The current local ready pair is useful for code path validation but weak for stale-memory value evidence.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    metadata = load_json(args.dataset_root / "3RScan" / "files" / "3RScan.json")
    summaries = []
    rows = []
    scanned = 0
    reference_semseg = 0
    for group in metadata:
        reference_scan_id = group.get("reference")
        if not reference_scan_id:
            continue
        for pair_metadata in group.get("scans", []):
            scanned += 1
            summary, pair_rows = summarize_target(args.dataset_root, reference_scan_id, pair_metadata)
            if summary is None:
                continue
            reference_semseg += 1
            summaries.append(summary)
            rows.extend(pair_rows)

    summaries.sort(
        key=lambda item: (
            item["score"],
            item["proxy_moved_gt_1_0m"],
            item["proxy_planar_max_m"] or 0.0,
            item["proxy_rows"],
        ),
        reverse=True,
    )
    coverage = {
        "dataset_root": str(args.dataset_root),
        "metadata_pairs_scanned": scanned,
        "pairs_with_reference_semseg": reference_semseg,
        "candidate_rows_written": len(rows),
        "status": "ready" if summaries else "blocked",
    }
    with (args.out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_jsonl(args.out_dir / "targets.jsonl", summaries)
    write_jsonl(args.out_dir / "proxy_rows.jsonl", rows)
    write_report(args.out_dir / "report.md", summaries, coverage)

    print(json.dumps({"coverage": coverage, "top_targets": summaries[:5]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
