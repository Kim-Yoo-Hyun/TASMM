#!/usr/bin/env python3
"""Build the E001 reference-rescan pair manifest.

This script records denominator coverage for 3RScan / 3DSSG semantic pairs.
It intentionally does not filter by object displacement; that belongs to the
query-construction stage.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M01_pair_manifest_v0"
MANIFEST_VERSION = "e001_pair_manifest_v0"

REQUIRED_3RSCAN_FILES = {
    "semseg": "semseg.v2.json",
    "ply": "labels.instances.annotated.v2.ply",
    "segs": "mesh.refined.0.010000.segs.v2.json",
}

PAYLOAD_EXCLUSION_KEYS = {
    "missing_reference_scan_dir",
    "missing_rescan_scan_dir",
    "missing_reference_semseg",
    "missing_rescan_semseg",
    "missing_reference_ply",
    "missing_rescan_ply",
    "missing_reference_segs",
    "missing_rescan_segs",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def scan_ids_from_3dssg(path: Path) -> set[str]:
    data = load_json(path)
    return {str(scan.get("scan")) for scan in data.get("scans", []) if scan.get("scan")}


def scan_payload(dataset_root: Path, scan_id: str) -> dict[str, bool]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    sequence_zip = (scan_dir / "sequence.zip").is_file()
    sequence_dir = (scan_dir / "sequence").is_dir()
    return {
        "scan_dir": scan_dir.is_dir(),
        "semseg": (scan_dir / REQUIRED_3RSCAN_FILES["semseg"]).is_file(),
        "ply": (scan_dir / REQUIRED_3RSCAN_FILES["ply"]).is_file(),
        "segs": (scan_dir / REQUIRED_3RSCAN_FILES["segs"]).is_file(),
        "sequence": sequence_zip or sequence_dir,
        "sequence_zip": sequence_zip,
        "sequence_dir": sequence_dir,
    }


def count_local_scan_payloads(dataset_root: Path) -> dict[str, int]:
    scans_root = dataset_root / "3RScan" / "scans"
    if not scans_root.is_dir():
        return {
            "scan_dirs": 0,
            "semantic_payload_triplet": 0,
            "sequence_available": 0,
        }

    scan_dirs = [path for path in scans_root.iterdir() if path.is_dir()]
    semantic_ready = 0
    sequence_ready = 0
    for scan_dir in scan_dirs:
        has_required = all((scan_dir / filename).is_file() for filename in REQUIRED_3RSCAN_FILES.values())
        semantic_ready += int(has_required)
        sequence_ready += int((scan_dir / "sequence.zip").is_file() or (scan_dir / "sequence").is_dir())
    return {
        "scan_dirs": len(scan_dirs),
        "semantic_payload_triplet": semantic_ready,
        "sequence_available": sequence_ready,
    }


def pair_next_stage(exclusion_reasons: list[str]) -> str:
    if not exclusion_reasons:
        return "query_construction_v0"
    if any(reason in PAYLOAD_EXCLUSION_KEYS for reason in exclusion_reasons):
        return "needs_staging"
    return "exclude"


def build_row(
    dataset_root: Path,
    group: dict[str, Any],
    pair_metadata: dict[str, Any],
    objects_scan_ids: set[str],
    relationship_scan_ids: set[str],
) -> dict[str, Any]:
    reference_scan_id = str(group["reference"])
    rescan_id = str(pair_metadata["reference"])
    reference_payload = scan_payload(dataset_root, reference_scan_id)
    rescan_payload = scan_payload(dataset_root, rescan_id)
    reference_3dssg = {
        "objects": reference_scan_id in objects_scan_ids,
        "relationships": reference_scan_id in relationship_scan_ids,
    }
    rescan_3dssg = {
        "objects": rescan_id in objects_scan_ids,
        "relationships": rescan_id in relationship_scan_ids,
    }

    rigid_count = len(pair_metadata.get("rigid", []))
    removed_count = len(pair_metadata.get("removed", []))
    exclusion_reasons: list[str] = []

    for prefix, payload in [
        ("reference", reference_payload),
        ("rescan", rescan_payload),
    ]:
        if not payload["scan_dir"]:
            exclusion_reasons.append(f"missing_{prefix}_scan_dir")
        for key in ["semseg", "ply", "segs"]:
            if not payload[key]:
                exclusion_reasons.append(f"missing_{prefix}_{key}")

    if rigid_count <= 0:
        exclusion_reasons.append("missing_rigid_metadata")
    if not reference_3dssg["objects"]:
        exclusion_reasons.append("missing_reference_3dssg_objects")
    if not reference_3dssg["relationships"]:
        exclusion_reasons.append("missing_reference_3dssg_relationships")

    eligibility_status = "ready_minimal" if not exclusion_reasons else "blocked"
    return {
        "manifest_version": MANIFEST_VERSION,
        "pair_uid": f"{reference_scan_id}->{rescan_id}",
        "reference_scan_id": reference_scan_id,
        "rescan_id": rescan_id,
        "metadata_split": group.get("type"),
        "metadata_rigid_count": rigid_count,
        "metadata_removed_count": removed_count,
        "reference_payload": reference_payload,
        "rescan_payload": rescan_payload,
        "reference_3dssg": reference_3dssg,
        "rescan_3dssg": rescan_3dssg,
        "eligibility_status": eligibility_status,
        "exclusion_reasons": exclusion_reasons,
        "next_stage": pair_next_stage(exclusion_reasons),
    }


def build_report(coverage: dict[str, Any], out_dir: Path) -> str:
    ready = coverage["eligibility_status_counts"].get("ready_minimal", 0)
    blocked = coverage["eligibility_status_counts"].get("blocked", 0)
    lines = [
        "# E001-M01 Pair Manifest",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Dataset root: `{coverage['dataset_root']}`",
        f"- Manifest version: `{coverage['manifest_version']}`",
        f"- Metadata groups scanned: {coverage['metadata_groups_scanned']}",
        f"- Metadata pairs scanned: {coverage['metadata_pairs_scanned']}",
        f"- Local `3RScan` scan directories: {coverage['local_scan_payloads']['scan_dirs']}",
        f"- Local semantic payload triplets: {coverage['local_scan_payloads']['semantic_payload_triplet']}",
        f"- Local sequence payloads: {coverage['local_scan_payloads']['sequence_available']}",
        f"- `3DSSG` object scan entries: {coverage['3dssg_object_scan_entries']}",
        f"- `3DSSG` relationship scan entries: {coverage['3dssg_relationship_scan_entries']}",
        f"- `ready_minimal` pairs: {ready}",
        f"- Blocked pairs: {blocked}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Coverage",
        "",
        "| Split | Total pairs | Ready minimal | Blocked |",
        "| --- | ---: | ---: | ---: |",
    ]
    for split in sorted(coverage["split_counts"]):
        total = coverage["split_counts"][split]
        ready_split = coverage["ready_minimal_by_split"].get(split, 0)
        blocked_split = total - ready_split
        lines.append(f"| `{split}` | {total} | {ready_split} | {blocked_split} |")

    lines.extend(
        [
            "",
            "## Main Exclusion Reasons",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    for reason, count in sorted(
        coverage["exclusion_reason_counts"].items(), key=lambda item: (-item[1], item[0])
    )[:12]:
        lines.append(f"| `{reason}` | {count} |")

    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- This artifact supports the denominator and payload-coverage claim for E001.",
            "- This artifact does not support dynamic object search performance, navigation `SR` / `SPL`, RGB-D robustness, open-vocabulary robustness, or human-intent claims.",
            "",
            "## 에이전트 추론",
            "",
            "- E001-M01 should keep blocked pairs in the manifest because paper reviewers will ask how much of `3RScan` / `3DSSG` was excluded before evaluation.",
            "- `sequence` availability is recorded now so E003 can later reuse the same denominator without changing pair IDs.",
            "- Query construction should use only `ready_minimal` rows and should decide significant moved / low-motion status separately.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E001-M01. Continue to E001-M02 query construction.",
            "",
            "## Outputs",
            "",
            "- `manifest.jsonl`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = args.dataset_root / "3RScan" / "files" / "3RScan.json"
    objects_path = args.dataset_root / "3DSSG" / "objects.json"
    relationships_path = args.dataset_root / "3DSSG" / "relationships.json"

    metadata = load_json(metadata_path)
    objects_scan_ids = scan_ids_from_3dssg(objects_path)
    relationship_scan_ids = scan_ids_from_3dssg(relationships_path)

    rows: list[dict[str, Any]] = []
    for group in metadata:
        if not group.get("reference"):
            continue
        for pair_metadata in group.get("scans", []):
            if not pair_metadata.get("reference"):
                continue
            rows.append(build_row(args.dataset_root, group, pair_metadata, objects_scan_ids, relationship_scan_ids))

    status_counts = Counter(row["eligibility_status"] for row in rows)
    split_counts = Counter(str(row["metadata_split"]) for row in rows)
    ready_by_split = Counter(
        str(row["metadata_split"]) for row in rows if row["eligibility_status"] == "ready_minimal"
    )
    next_stage_counts = Counter(row["next_stage"] for row in rows)
    exclusion_reason_counts = Counter(
        reason for row in rows for reason in row.get("exclusion_reasons", [])
    )

    local_payloads = count_local_scan_payloads(args.dataset_root)
    coverage = {
        "manifest_version": MANIFEST_VERSION,
        "dataset_root": str(args.dataset_root),
        "metadata_groups_scanned": len(metadata),
        "metadata_pairs_scanned": len(rows),
        "local_scan_payloads": local_payloads,
        "3dssg_object_scan_entries": len(objects_scan_ids),
        "3dssg_relationship_scan_entries": len(relationship_scan_ids),
        "eligibility_status_counts": dict(sorted(status_counts.items())),
        "next_stage_counts": dict(sorted(next_stage_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "ready_minimal_by_split": dict(sorted(ready_by_split.items())),
        "exclusion_reason_counts": dict(sorted(exclusion_reason_counts.items())),
        "status": "ready" if status_counts.get("ready_minimal", 0) > 0 else "blocked",
        "outputs": {
            "manifest": str(args.out_dir / "manifest.jsonl"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }

    write_jsonl(args.out_dir / "manifest.jsonl", rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "metadata_pairs_scanned": coverage["metadata_pairs_scanned"],
                "eligibility_status_counts": coverage["eligibility_status_counts"],
                "next_stage_counts": coverage["next_stage_counts"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
