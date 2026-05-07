#!/usr/bin/env python3
"""Record E001 additional pair staging status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M05_additional_pair_staging_v0"
DEFAULT_PAIR_UID = "5630cfcb-12bf-2860-87ee-b4e4a5bf0cb0->d7d40d75-7a5d-2b36-9746-3e807d3e7558"
REQUIRED_FILES = [
    "semseg.v2.json",
    "labels.instances.annotated.v2.ply",
    "mesh.refined.0.010000.segs.v2.json",
]


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


def scan_payload(dataset_root: Path, scan_id: str) -> dict[str, Any]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    files = {
        name: {
            "exists": (scan_dir / name).is_file(),
            "bytes": (scan_dir / name).stat().st_size if (scan_dir / name).is_file() else 0,
        }
        for name in REQUIRED_FILES
    }
    return {
        "scan_id": scan_id,
        "scan_dir": str(scan_dir),
        "scan_dir_exists": scan_dir.is_dir(),
        "required_files": files,
        "semantic_triplet_ready": all(item["exists"] for item in files.values()),
        "sequence_available": (scan_dir / "sequence.zip").is_file() or (scan_dir / "sequence").is_dir(),
    }


def build_report(summary: dict[str, Any]) -> str:
    target = summary["target_pair"]
    lines = [
        "# E001-M05 Additional Pair Staging",
        "",
        "## Status",
        "",
        summary["status"],
        "",
        "## 사실",
        "",
        f"- Target pair: `{summary['target_pair_uid']}`",
        f"- Reference scan: `{target['reference_scan_id']}`",
        f"- Rescan: `{target['rescan_id']}`",
        f"- Reference semantic triplet ready: {summary['reference_payload']['semantic_triplet_ready']}",
        f"- Rescan semantic triplet ready: {summary['rescan_payload']['semantic_triplet_ready']}",
        f"- Rescan `sequence` available: {summary['rescan_payload']['sequence_available']}",
        f"- Ready pairs after staging: {summary['after']['ready_minimal_pairs']}",
        f"- Validated pairs after staging: {summary['after']['validated_pair_count']}",
        f"- Base query rows after staging: {summary['after']['base_query_rows']}",
        f"- Significant moved base rows after staging: {summary['after']['significant_moved_base_rows']}",
        f"- Target pair base rows: {target['base_query_rows']}",
        f"- Target pair significant moved rows: {target['significant_moved_rows']}",
        f"- Target significant moved labels: {', '.join(target['significant_moved_labels']) if target['significant_moved_labels'] else 'none'}",
        "",
        "## 논문 주장",
        "",
        "- This artifact supports only payload staging and denominator expansion.",
        "- This artifact does not itself support a new method-performance claim.",
        "- This is not evidence that the full dataset is exhausted or insufficient.",
        "",
        "## 에이전트 추론",
        "",
        "- The issue was local payload coverage, not lack of `3RScan` / `3DSSG` metadata pairs.",
        "- The staged rescan adds one significant moved base row and three low-motion control rows.",
        "- Because `sequence` is still absent, this pair helps E001/E002 before it helps E003 RGB-D replay.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None. Continue to E002 path-cost bridge preparation.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--pair-uid", default=DEFAULT_PAIR_UID)
    args = parser.parse_args()

    reference_scan_id, rescan_id = args.pair_uid.split("->", 1)
    manifest_rows = load_jsonl(EXPERIMENT_ROOT / "artifacts" / "E001-M01_pair_manifest_v0" / "manifest.jsonl")
    base_rows = load_jsonl(EXPERIMENT_ROOT / "artifacts" / "E001-M02_query_construction_v0" / "base_query_rows.jsonl")
    m01_coverage = load_json(EXPERIMENT_ROOT / "artifacts" / "E001-M01_pair_manifest_v0" / "coverage.json")
    m02_coverage = load_json(EXPERIMENT_ROOT / "artifacts" / "E001-M02_query_construction_v0" / "coverage.json")

    target_manifest = [row for row in manifest_rows if row["pair_uid"] == args.pair_uid]
    target_base_rows = [row for row in base_rows if row["pair_uid"] == args.pair_uid]
    significant = [row for row in target_base_rows if row["row_band"] == "significant_moved"]
    summary = {
        "status": "staging_ready" if target_manifest and target_manifest[0]["eligibility_status"] == "ready_minimal" else "blocked",
        "target_pair_uid": args.pair_uid,
        "reference_payload": scan_payload(args.dataset_root, reference_scan_id),
        "rescan_payload": scan_payload(args.dataset_root, rescan_id),
        "target_pair": {
            "reference_scan_id": reference_scan_id,
            "rescan_id": rescan_id,
            "manifest_status": target_manifest[0]["eligibility_status"] if target_manifest else "missing",
            "base_query_rows": len(target_base_rows),
            "significant_moved_rows": len(significant),
            "low_motion_control_rows": sum(1 for row in target_base_rows if row["row_band"] == "low_motion_control"),
            "mid_motion_review_rows": sum(1 for row in target_base_rows if row["row_band"] == "mid_motion_review"),
            "significant_moved_labels": [row["object_label"] for row in significant],
            "base_rows": [
                {
                    "object_label": row["object_label"],
                    "row_band": row["row_band"],
                    "scene_aligned_static_planar_error_m": row["scene_aligned_static_planar_error_m"],
                }
                for row in target_base_rows
            ],
        },
        "after": {
            "ready_minimal_pairs": m01_coverage["eligibility_status_counts"].get("ready_minimal", 0),
            "blocked_pairs": m01_coverage["eligibility_status_counts"].get("blocked", 0),
            "validated_pair_count": m02_coverage["validated_pair_count"],
            "base_query_rows": m02_coverage["base_query_rows"],
            "query_rows": m02_coverage["query_rows"],
            "significant_moved_base_rows": m02_coverage["base_row_band_counts"].get("significant_moved", 0),
            "low_motion_control_base_rows": m02_coverage["base_row_band_counts"].get("low_motion_control", 0),
            "mid_motion_review_base_rows": m02_coverage["base_row_band_counts"].get("mid_motion_review", 0),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "staging_summary.json", summary)
    (args.out_dir / "report.md").write_text(build_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
