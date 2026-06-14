#!/usr/bin/env python3
"""Check H001 target reference-rescan annotation pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "pair_annotation_check"
REFERENCE_SCAN_ID = "ddc73797-765b-241a-9e2c-097c5989baf6"
RESCAN_ID = "c7895f07-339c-2d13-8176-7418b6e8d7ce"
REQUIRED_3RSCAN_FILES = [
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_scan(scans: list[dict], scan_id: str) -> dict | None:
    for scan in scans:
        if scan.get("scan") == scan_id:
            return scan
    return None


def find_pair_metadata(scan3r_json: list[dict]) -> dict:
    for group in scan3r_json:
        if group.get("reference") != REFERENCE_SCAN_ID:
            continue
        for scan in group.get("scans", []):
            if scan.get("reference") == RESCAN_ID:
                return scan
    raise RuntimeError("target pair metadata not found")


def scan_payload_status(dataset_root: Path, scan_id: str) -> dict:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    files = {name: (scan_dir / name).is_file() for name in REQUIRED_3RSCAN_FILES}
    return {
        "scan_id": scan_id,
        "scan_dir_exists": scan_dir.is_dir(),
        "required_files": files,
        "semantic_payload_ready": all(files.values()),
        "sequence_zip": (scan_dir / "sequence.zip").is_file(),
        "sequence_dir": (scan_dir / "sequence").is_dir(),
    }


def object_map(objects_scan: dict | None) -> dict[str, dict]:
    if objects_scan is None:
        return {}
    return {str(obj["id"]): obj for obj in objects_scan.get("objects", [])}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    metadata = find_pair_metadata(load_json(args.dataset_root / "3RScan" / "files" / "3RScan.json"))
    objects_data = load_json(args.dataset_root / "3DSSG" / "objects.json")
    relationships_data = load_json(args.dataset_root / "3DSSG" / "relationships.json")

    ref_objects_scan = find_scan(objects_data["scans"], REFERENCE_SCAN_ID)
    rescan_objects_scan = find_scan(objects_data["scans"], RESCAN_ID)
    ref_rel_scan = find_scan(relationships_data["scans"], REFERENCE_SCAN_ID)
    rescan_rel_scan = find_scan(relationships_data["scans"], RESCAN_ID)

    ref_objects = object_map(ref_objects_scan)
    rescan_objects = object_map(rescan_objects_scan)

    rigid_rows = []
    for item in metadata.get("rigid", []):
        ref_id = str(item["instance_reference"])
        rescan_id = str(item["instance_rescan"])
        ref_obj = ref_objects.get(ref_id)
        rescan_obj = rescan_objects.get(rescan_id)
        rigid_rows.append(
            {
                "instance_reference": ref_id,
                "instance_rescan": rescan_id,
                "ref_label": ref_obj.get("label") if ref_obj else None,
                "rescan_label": rescan_obj.get("label") if rescan_obj else None,
                "ref_join": ref_obj is not None,
                "rescan_join": rescan_obj is not None,
                "label_match": ref_obj is not None
                and rescan_obj is not None
                and ref_obj.get("label") == rescan_obj.get("label"),
            }
        )

    removed_rows = []
    for raw_id in metadata.get("removed", []):
        ref_id = str(raw_id)
        ref_obj = ref_objects.get(ref_id)
        rescan_obj = rescan_objects.get(ref_id)
        removed_rows.append(
            {
                "instance_reference": ref_id,
                "ref_label": ref_obj.get("label") if ref_obj else None,
                "ref_join": ref_obj is not None,
                "present_in_rescan_objects": rescan_obj is not None,
                "rescan_label": rescan_obj.get("label") if rescan_obj else None,
            }
        )

    unchanged_reference_ids = set(ref_objects) - {
        str(item["instance_reference"]) for item in metadata.get("rigid", [])
    } - {str(item) for item in metadata.get("removed", [])} - {
        str(item) for item in metadata.get("nonrigid", [])
    }
    unchanged_join_count = sum(1 for object_id in unchanged_reference_ids if object_id in rescan_objects)

    ref_payload = scan_payload_status(args.dataset_root, REFERENCE_SCAN_ID)
    rescan_payload = scan_payload_status(args.dataset_root, RESCAN_ID)
    coverage = {
        "dataset_root": str(args.dataset_root),
        "reference_scan_id": REFERENCE_SCAN_ID,
        "rescan_id": RESCAN_ID,
        "reference_payload": ref_payload,
        "rescan_payload": rescan_payload,
        "metadata_rigid": len(metadata.get("rigid", [])),
        "metadata_removed": len(metadata.get("removed", [])),
        "metadata_nonrigid": len(metadata.get("nonrigid", [])),
        "reference_3dssg_objects": len(ref_objects),
        "rescan_3dssg_objects": len(rescan_objects),
        "reference_3dssg_relationships": len(ref_rel_scan.get("relationships", [])) if ref_rel_scan else 0,
        "rescan_3dssg_relationships": len(rescan_rel_scan.get("relationships", [])) if rescan_rel_scan else 0,
        "rigid_ref_join": sum(1 for row in rigid_rows if row["ref_join"]),
        "rigid_rescan_join": sum(1 for row in rigid_rows if row["rescan_join"]),
        "rigid_label_match": sum(1 for row in rigid_rows if row["label_match"]),
        "removed_ref_join": sum(1 for row in removed_rows if row["ref_join"]),
        "removed_absent_in_rescan": sum(1 for row in removed_rows if not row["present_in_rescan_objects"]),
        "unchanged_reference_ids": len(unchanged_reference_ids),
        "unchanged_join_count": unchanged_join_count,
    }
    coverage["graph_pair_ready"] = (
        coverage["rigid_ref_join"] == coverage["metadata_rigid"]
        and coverage["rigid_rescan_join"] == coverage["metadata_rigid"]
        and coverage["rigid_label_match"] == coverage["metadata_rigid"]
        and coverage["removed_absent_in_rescan"] == coverage["metadata_removed"]
    )
    coverage["geometry_pair_ready"] = (
        ref_payload["semantic_payload_ready"] and rescan_payload["semantic_payload_ready"]
    )
    coverage["pair_gate_status"] = (
        "graph_ready_geometry_blocked"
        if coverage["graph_pair_ready"] and not coverage["geometry_pair_ready"]
        else "ready"
        if coverage["graph_pair_ready"] and coverage["geometry_pair_ready"]
        else "blocked"
    )

    with (args.out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_jsonl(args.out_dir / "rigid_join.jsonl", rigid_rows)
    write_jsonl(args.out_dir / "removed_join.jsonl", removed_rows)

    if coverage["geometry_pair_ready"]:
        inference_rows = [
            "- `3DSSG` graph annotations are sufficient for an annotation-level pair check.",
            "- The target reference-rescan pair is ready for geometry validation.",
            "- H001 should still stay in hypothesis-stage until transform direction and centroid plausibility are checked.",
        ]
    else:
        inference_rows = [
            "- `3DSSG` graph annotations are sufficient for an annotation-level pair check.",
            "- The real geometry pair gate remains blocked because the target rescan `3RScan` semantic payload is not present locally.",
            "- H001 should not be promoted to experiment-stage evidence until geometry payload is staged or the hypothesis is reframed as graph-only.",
        ]

    report = [
        "# Pair Annotation Check",
        "",
        "## Status",
        "",
        coverage["pair_gate_status"],
        "",
        "## Facts",
        "",
        f"- Dataset root: `{args.dataset_root}`",
        f"- Reference scan: `{REFERENCE_SCAN_ID}`",
        f"- Rescan: `{RESCAN_ID}`",
        f"- Rigid metadata rows: {coverage['metadata_rigid']}",
        f"- Rigid label matches: {coverage['rigid_label_match']} / {coverage['metadata_rigid']}",
        f"- Removed rows absent in rescan objects: {coverage['removed_absent_in_rescan']} / {coverage['metadata_removed']}",
        f"- Reference `3RScan` semantic payload ready: {ref_payload['semantic_payload_ready']}",
        f"- Rescan `3RScan` semantic payload ready: {rescan_payload['semantic_payload_ready']}",
        f"- Graph pair ready: {coverage['graph_pair_ready']}",
        f"- Geometry pair ready: {coverage['geometry_pair_ready']}",
        "",
        "## Agent Inference",
        "",
        *inference_rows,
        "",
        "## Outputs",
        "",
        "- `coverage.json`",
        "- `rigid_join.jsonl`",
        "- `removed_join.jsonl`",
    ]
    (args.out_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
