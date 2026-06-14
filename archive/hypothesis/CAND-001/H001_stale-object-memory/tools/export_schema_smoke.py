#!/usr/bin/env python3
"""Export H001 stale-label schema smoke rows.

This is a hypothesis-stage utility, not an experiment harness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "schema_smoke"
REFERENCE_SCAN_ID = "ddc73797-765b-241a-9e2c-097c5989baf6"
METADATA_RESCAN_ID = "c7895f07-339c-2d13-8176-7418b6e8d7ce"
EPISODE_ID = "h001_meta_ddc73797_c7895f07"
CONTROL_ROW_TARGET = 16
STRUCTURAL_CONTROL_LABELS = {"floor", "wall", "ceiling"}
PREFERRED_CONTROL_LABELS = {
    "sofa",
    "cabinet",
    "tv stand",
    "shelf",
    "lamp",
    "cart",
    "box",
    "tv",
    "decoration",
    "plant",
    "cushion",
    "monitor",
    "clock",
    "curtain",
}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_metadata_entry(scan3r_json: list[dict]) -> dict:
    for group in scan3r_json:
        if group.get("reference") != REFERENCE_SCAN_ID:
            continue
        for scan in group.get("scans", []):
            if scan.get("reference") == METADATA_RESCAN_ID:
                return scan
    raise RuntimeError("Target reference/rescan metadata entry not found")


def find_3dssg_scan(scans: list[dict], scan_id: str) -> dict:
    for scan in scans:
        if scan.get("scan") == scan_id:
            return scan
    raise RuntimeError(f"3DSSG scan not found: {scan_id}")


def read_reference_objects(dataset_root: Path) -> tuple[dict[str, dict], int]:
    objects_path = dataset_root / "3DSSG" / "objects.json"
    relationships_path = dataset_root / "3DSSG" / "relationships.json"
    object_scan = find_3dssg_scan(load_json(objects_path)["scans"], REFERENCE_SCAN_ID)
    relationship_scan = find_3dssg_scan(load_json(relationships_path)["scans"], REFERENCE_SCAN_ID)
    objects = {str(obj["id"]): obj for obj in object_scan.get("objects", [])}
    return objects, len(relationship_scan.get("relationships", []))


def parse_ascii_ply_centroids(path: Path) -> dict[str, dict]:
    with path.open("r", encoding="utf-8") as f:
        line = f.readline().strip()
        if line != "ply":
            raise RuntimeError(f"Not a PLY file: {path}")

        vertex_count = None
        vertex_props: list[str] = []
        in_vertex = False

        while True:
            line = f.readline()
            if not line:
                raise RuntimeError("PLY header ended unexpectedly")
            stripped = line.strip()
            if stripped == "end_header":
                break
            parts = stripped.split()
            if parts[:2] == ["format", "ascii"]:
                continue
            if parts[:2] == ["element", "vertex"]:
                vertex_count = int(parts[2])
                in_vertex = True
                continue
            if parts[:2] == ["element", "face"]:
                in_vertex = False
                continue
            if in_vertex and parts[:1] == ["property"]:
                vertex_props.append(parts[-1])

        if vertex_count is None:
            raise RuntimeError("PLY vertex count not found")

        prop_index = {name: idx for idx, name in enumerate(vertex_props)}
        for required in ("x", "y", "z", "objectId"):
            if required not in prop_index:
                raise RuntimeError(f"PLY property not found: {required}")

        stats: dict[str, dict] = {}
        for _ in range(vertex_count):
            values = f.readline().strip().split()
            if not values:
                continue
            object_id = values[prop_index["objectId"]]
            x = float(values[prop_index["x"]])
            y = float(values[prop_index["y"]])
            z = float(values[prop_index["z"]])

            item = stats.setdefault(
                object_id,
                {
                    "count": 0,
                    "sum": [0.0, 0.0, 0.0],
                    "min": [x, y, z],
                    "max": [x, y, z],
                },
            )
            item["count"] += 1
            item["sum"][0] += x
            item["sum"][1] += y
            item["sum"][2] += z
            item["min"] = [min(item["min"][i], value) for i, value in enumerate((x, y, z))]
            item["max"] = [max(item["max"][i], value) for i, value in enumerate((x, y, z))]

    centroids = {}
    for object_id, item in stats.items():
        count = item["count"]
        centroids[object_id] = {
            "vertex_count": count,
            "centroid": [round(value / count, 6) for value in item["sum"]],
            "bbox_min": [round(value, 6) for value in item["min"]],
            "bbox_max": [round(value, 6) for value in item["max"]],
        }
    return centroids


def row_vector_transform(point: list[float], flat_matrix: list[float]) -> list[float]:
    matrix = [flat_matrix[idx : idx + 4] for idx in range(0, 16, 4)]
    vector = [point[0], point[1], point[2], 1.0]
    output = []
    for col in range(3):
        output.append(sum(vector[row] * matrix[row][col] for row in range(4)))
    return [round(value, 6) for value in output]


def build_rows(metadata: dict, objects: dict[str, dict], centroids: dict[str, dict]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    skipped: list[dict] = []
    changed_ids = {
        str(item["instance_reference"])
        for item in metadata.get("rigid", [])
        if "instance_reference" in item
    }
    changed_ids.update(str(object_id) for object_id in metadata.get("removed", []))
    changed_ids.update(str(object_id) for object_id in metadata.get("nonrigid", []))

    def add_skip(change_type: str, object_id: str, reason: str) -> None:
        skipped.append({"change_type": change_type, "object_instance_id_ref": object_id, "reason": reason})

    for item in metadata.get("rigid", []):
        object_id = str(item["instance_reference"])
        obj = objects.get(object_id)
        geom = centroids.get(object_id)
        if obj is None:
            add_skip("rigid_moved", object_id, "missing_3dssg_object")
            continue
        if geom is None:
            add_skip("rigid_moved", object_id, "missing_ply_object")
            continue

        old_centroid = geom["centroid"]
        current_centroid = row_vector_transform(old_centroid, item["transform"])
        rows.append(
            {
                "episode_id": EPISODE_ID,
                "probe_type": "metadata_guided_synthetic_stale_probe",
                "reference_scan_id": REFERENCE_SCAN_ID,
                "metadata_rescan_id": METADATA_RESCAN_ID,
                "object_instance_id_ref": object_id,
                "object_instance_id_rescan": str(item.get("instance_rescan", "")),
                "object_label": obj.get("label", ""),
                "query": f"find the {obj.get('label', 'object')}",
                "task_relevant": True,
                "change_type": "rigid_moved",
                "old_location_source": "reference_instance_geometry",
                "old_centroid_ref": old_centroid,
                "old_bbox_min_ref": geom["bbox_min"],
                "old_bbox_max_ref": geom["bbox_max"],
                "old_vertex_count": geom["vertex_count"],
                "current_location_source": "3RScan_rigid_transform_row_vector_unverified",
                "current_centroid_est": current_centroid,
                "transform_direction_verified": False,
                "old_memory_is_stale": True,
                "expected_memory_state": "needs_reobservation",
                "evaluation_scope": "stale_false_positive_and_recovery",
                "label_source": "3RScan_metadata_plus_3DSSG",
                "include_in_h001_mini": True,
                "notes": "Object transform applied with row-vector convention used by local VLSAT transform_ply.py; direction still needs validation.",
            }
        )

    for object_id_raw in metadata.get("removed", []):
        object_id = str(object_id_raw)
        obj = objects.get(object_id)
        geom = centroids.get(object_id)
        if obj is None:
            add_skip("removed", object_id, "missing_3dssg_object")
            continue
        if geom is None:
            add_skip("removed", object_id, "missing_ply_object")
            continue

        rows.append(
            {
                "episode_id": EPISODE_ID,
                "probe_type": "metadata_guided_synthetic_stale_probe",
                "reference_scan_id": REFERENCE_SCAN_ID,
                "metadata_rescan_id": METADATA_RESCAN_ID,
                "object_instance_id_ref": object_id,
                "object_instance_id_rescan": None,
                "object_label": obj.get("label", ""),
                "query": f"find the {obj.get('label', 'object')}",
                "task_relevant": True,
                "change_type": "removed",
                "old_location_source": "reference_instance_geometry",
                "old_centroid_ref": geom["centroid"],
                "old_bbox_min_ref": geom["bbox_min"],
                "old_bbox_max_ref": geom["bbox_max"],
                "old_vertex_count": geom["vertex_count"],
                "current_location_source": "absent_removed",
                "current_centroid_est": None,
                "transform_direction_verified": None,
                "old_memory_is_stale": True,
                "expected_memory_state": "stale",
                "evaluation_scope": "stale_false_positive_only",
                "label_source": "3RScan_metadata_plus_3DSSG",
                "include_in_h001_mini": True,
                "notes": "Removed object supports stale false-positive evaluation, not moved-object recovery.",
            }
        )

    unchanged_candidates = []
    for object_id, obj in objects.items():
        label = obj.get("label", "")
        geom = centroids.get(object_id)
        if object_id in changed_ids:
            continue
        if geom is None:
            add_skip("unchanged_control", object_id, "missing_ply_object")
            continue
        if label in STRUCTURAL_CONTROL_LABELS:
            continue

        priority = 0 if label in PREFERRED_CONTROL_LABELS else 1
        unchanged_candidates.append((priority, label, int(object_id), object_id, obj, geom))

    unchanged_candidates.sort()
    for _, _, _, object_id, obj, geom in unchanged_candidates[:CONTROL_ROW_TARGET]:
        label = obj.get("label", "")
        rows.append(
            {
                "episode_id": EPISODE_ID,
                "probe_type": "metadata_guided_synthetic_stale_probe",
                "reference_scan_id": REFERENCE_SCAN_ID,
                "metadata_rescan_id": METADATA_RESCAN_ID,
                "object_instance_id_ref": object_id,
                "object_instance_id_rescan": object_id,
                "object_label": label,
                "query": f"find the {label or 'object'}",
                "task_relevant": True,
                "change_type": "unchanged_control",
                "old_location_source": "reference_instance_geometry",
                "old_centroid_ref": geom["centroid"],
                "old_bbox_min_ref": geom["bbox_min"],
                "old_bbox_max_ref": geom["bbox_max"],
                "old_vertex_count": geom["vertex_count"],
                "current_location_source": "assumed_unchanged_by_absence_from_3RScan_change_metadata",
                "current_centroid_est": geom["centroid"],
                "transform_direction_verified": None,
                "old_memory_is_stale": False,
                "expected_memory_state": "trusted",
                "evaluation_scope": "trusted_control",
                "label_source": "3RScan_metadata_negative_plus_3DSSG",
                "include_in_h001_mini": True,
                "notes": "Control row assumes unchanged because the object is absent from rigid/removed/nonrigid metadata for this rescan; this is a weak negative until a real rescan payload is staged.",
            }
        )

    coverage = {
        "episode_id": EPISODE_ID,
        "reference_scan_id": REFERENCE_SCAN_ID,
        "metadata_rescan_id": METADATA_RESCAN_ID,
        "metadata_rigid_count": len(metadata.get("rigid", [])),
        "metadata_removed_count": len(metadata.get("removed", [])),
        "metadata_nonrigid_count": len(metadata.get("nonrigid", [])),
        "included_rows": len(rows),
        "included_rigid_moved": sum(1 for row in rows if row["change_type"] == "rigid_moved"),
        "included_removed": sum(1 for row in rows if row["change_type"] == "removed"),
        "included_unchanged_control": sum(1 for row in rows if row["change_type"] == "unchanged_control"),
        "skipped_rows": len(skipped),
        "skipped": skipped,
        "acceptance": {
            "min_8_joined_rows": len(rows) >= 8,
            "min_5_rigid_moved": sum(1 for row in rows if row["change_type"] == "rigid_moved") >= 5,
            "min_2_removed": sum(1 for row in rows if row["change_type"] == "removed") >= 2,
            "min_8_unchanged_control": sum(1 for row in rows if row["change_type"] == "unchanged_control") >= 8,
            "all_rows_have_queries": all(row.get("query") for row in rows),
        },
    }
    coverage["ready_for_h001_mini_schema_smoke"] = all(coverage["acceptance"].values())
    return rows, coverage


def write_outputs(rows: list[dict], coverage: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "stale_labels.jsonl"
    coverage_path = out_dir / "coverage.json"
    report_path = out_dir / "report.md"

    with rows_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    with coverage_path.open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    report = [
        "# Schema Smoke Report",
        "",
        "## Status",
        "",
        "Ready for H001-Mini schema smoke." if coverage["ready_for_h001_mini_schema_smoke"] else "Not ready.",
        "",
        "## Facts",
        "",
        f"- Episode: `{coverage['episode_id']}`",
        f"- Reference scan: `{coverage['reference_scan_id']}`",
        f"- Metadata rescan: `{coverage['metadata_rescan_id']}`",
        f"- Metadata rigid rows: {coverage['metadata_rigid_count']}",
        f"- Metadata removed rows: {coverage['metadata_removed_count']}",
        f"- Metadata nonrigid rows: {coverage['metadata_nonrigid_count']}",
        f"- Included rows: {coverage['included_rows']}",
        f"- Included `rigid_moved` rows: {coverage['included_rigid_moved']}",
        f"- Included `removed` rows: {coverage['included_removed']}",
        f"- Included `unchanged_control` rows: {coverage['included_unchanged_control']}",
        f"- Skipped rows: {coverage['skipped_rows']}",
        "",
        "## Agent Inference",
        "",
        "- The schema has enough joined rows for a hypothesis-stage stale-memory smoke.",
        "- `unchanged_control` rows are weak negatives because paired rescan geometry is not staged locally.",
        "- Rigid current centroids are transform-derived and should not be treated as verified current pose evidence yet.",
        "- This artifact is not a final experiment result.",
        "",
        "## Outputs",
        "",
        "- `stale_labels.jsonl`",
        "- `coverage.json`",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    scan3r_path = args.dataset_root / "3RScan" / "files" / "3RScan.json"
    ply_path = (
        args.dataset_root
        / "3RScan"
        / "scans"
        / REFERENCE_SCAN_ID
        / "labels.instances.annotated.v2.ply"
    )

    metadata = find_metadata_entry(load_json(scan3r_path))
    objects, relationships_count = read_reference_objects(args.dataset_root)
    centroids = parse_ascii_ply_centroids(ply_path)
    rows, coverage = build_rows(metadata, objects, centroids)
    coverage["reference_3dssg_objects"] = len(objects)
    coverage["reference_3dssg_relationships"] = relationships_count
    write_outputs(rows, coverage, args.out_dir)

    print(json.dumps({"out_dir": str(args.out_dir), **coverage}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
