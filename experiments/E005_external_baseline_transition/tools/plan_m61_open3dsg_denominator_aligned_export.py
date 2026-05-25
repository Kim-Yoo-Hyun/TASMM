#!/usr/bin/env python3
"""Plan E005-M61 denominator-aligned Open3DSG object export."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M61_denominator_aligned_export_plan_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M61_denominator_aligned_export_plan_v0"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M60_LOCAL_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M60_query_conversion_contract_v0"
VERSION = "e005_m61_open3dsg_denominator_aligned_export_plan_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_query_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in ["heldout_b01", "heldout_b02", "heldout_b03"]:
        rows.extend(read_jsonl(M45_CONTRACT_DIR / f"{batch}_query_rows.jsonl"))
    return rows


def load_relationships(split: str) -> list[dict[str, Any]]:
    path = STAGED_ROOT / "training_repro" / "data" / "3RScan" / "3DSSG_subset" / f"relationships_{split}.json"
    payload = read_json(path)
    rows = payload.get("scans", [])
    return rows if isinstance(rows, list) else []


def preprocessed_path(scan_id: str, split_id: int) -> Path:
    return (
        STAGED_ROOT
        / "training_repro"
        / "output"
        / "datasets"
        / "OpenSG_3RScan"
        / "preprocessed"
        / scan_id
        / f"data_dict_{str(hex(int(split_id)))[-1]}.pkl"
    )


def feature_paths(scan_id: str, split_id: int) -> list[Path]:
    feature_root = (
        STAGED_ROOT
        / "training_repro"
        / "output"
        / "features"
        / "clip_features_h001_official_blip_top5_scales3"
    )
    feature_id = f"{scan_id}-{str(hex(int(split_id)))[-1]}.pt"
    dirs = sorted(path for path in feature_root.iterdir() if path.is_dir()) if feature_root.exists() else []
    return [path / feature_id for path in dirs]


def relationship_record(split_name: str, relationship: dict[str, Any]) -> dict[str, Any]:
    scan_id = str(relationship["scan"])
    split_id = int(relationship["split"])
    features = feature_paths(scan_id, split_id)
    feature_ready = bool(features) and all(path.exists() for path in features)
    preprocessed = preprocessed_path(scan_id, split_id)
    return {
        "scan_id": scan_id,
        "subset_split_id": split_id,
        "raw_scan_id": f"{scan_id}-{str(hex(split_id))[-1]}",
        "source_split": split_name,
        "preprocessed_path": str(preprocessed),
        "preprocessed_ready": preprocessed.exists(),
        "feature_paths": [str(path) for path in features],
        "feature_ready": feature_ready,
        "relationship_count": len(relationship.get("relationships", [])),
    }


def query_scan_summary(query_rows: list[dict[str, Any]], relationship_by_scan: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        by_scan[str(row["current_rescan_id"])].append(row)
    summaries = []
    for scan_id, rows in sorted(by_scan.items()):
        relationships = relationship_by_scan.get(scan_id, [])
        source_splits = sorted({str(row["source_split"]) for row in relationships})
        summaries.append(
            {
                "scan_id": scan_id,
                "query_rows": len(rows),
                "label_counts": dict(sorted(Counter(str(row["label_canonical"]) for row in rows).items())),
                "open3dsg_relationship_splits": source_splits,
                "open3dsg_subgraphs": len(relationships),
                "preprocessed_ready_subgraphs": sum(1 for row in relationships if row["preprocessed_ready"]),
                "feature_ready_subgraphs": sum(1 for row in relationships if row["feature_ready"]),
                "ready_for_targeted_export": bool(relationships)
                and all(row["preprocessed_ready"] and row["feature_ready"] for row in relationships),
            }
        )
    return summaries


def build_report(coverage: dict[str, Any], scan_summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M61 Open3DSG Denominator-Aligned Export Plan",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- M38/M45 query denominator rows: {coverage['query_rows']}.",
        f"- Query scan count: {coverage['query_scan_count']}.",
        f"- Query scans present in `Open3DSG` train split: {coverage['train_query_scan_count']}.",
        f"- Query scans present in `Open3DSG` validation split: {coverage['validation_query_scan_count']}.",
        f"- Target subgraphs for train+validation export: {coverage['target_subgraph_count']}.",
        f"- Target subgraphs with preprocessed payloads: {coverage['preprocessed_ready_subgraphs']} / {coverage['target_subgraph_count']}.",
        f"- Target subgraphs with feature payloads: {coverage['feature_ready_subgraphs']} / {coverage['target_subgraph_count']}.",
        f"- Current M60 scan overlap before M61: {coverage['m60_scan_overlap_count_before_m61']}.",
        "",
        "## Selected Route",
        "",
        "- First, run a validation-overlap smoke only if a quick nonzero M60 sanity check is needed.",
        "- For the paper-facing `Open3DSG` comparison, run the train+validation targeted export so all 195 denominator rows can be evaluated.",
        "- Do not modify `/home/yoohyun/research/local_dataset/Open3DSG_staged`; use a mounted runtime patch and store derived rows under `research2/local_dataset/Open3DSG_bridge/`.",
        "",
        "## Scan Coverage",
        "",
        "| scan_id | query rows | split | subgraphs | ready | labels |",
        "| --- | ---: | --- | ---: | --- | --- |",
    ]
    for row in scan_summaries:
        labels = ", ".join(f"{label}:{count}" for label, count in row["label_counts"].items())
        lines.append(
            "| {scan_id} | {query_rows} | {splits} | {subgraphs} | {ready} | {labels} |".format(
                scan_id=row["scan_id"],
                query_rows=row["query_rows"],
                splits=",".join(row["open3dsg_relationship_splits"]) or "missing",
                subgraphs=row["open3dsg_subgraphs"],
                ready="yes" if row["ready_for_targeted_export"] else "no",
                labels=labels,
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M61 is an export-alignment plan, not an `Open3DSG` performance result.",
            "- `Open3DSG` performance claim remains false until M61 rows are exported and M60 is rerun with nonzero query/eval rows.",
            "- If validation-only export is run, report it as a smoke check over 72 / 195 query rows, not as a full denominator result.",
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    query_rows = load_query_rows()
    query_scans = sorted({str(row["current_rescan_id"]) for row in query_rows})
    relationship_rows: list[dict[str, Any]] = []
    for split_name in ["train", "validation", "test"]:
        for relationship in load_relationships(split_name):
            scan_id = str(relationship.get("scan"))
            if scan_id in query_scans:
                relationship_rows.append(relationship_record(split_name, relationship))
    relationship_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in relationship_rows:
        relationship_by_scan[str(row["scan_id"])].append(row)
    scan_summaries = query_scan_summary(query_rows, relationship_by_scan)
    rows_by_source_split = Counter(str(row["source_split"]) for row in relationship_rows)
    query_rows_by_source_split = Counter()
    for summary in scan_summaries:
        splits = summary["open3dsg_relationship_splits"]
        if splits:
            for split in splits:
                query_rows_by_source_split[split] += int(summary["query_rows"])
        else:
            query_rows_by_source_split["missing"] += int(summary["query_rows"])

    val_target_scans = [
        row["scan_id"]
        for row in scan_summaries
        if row["open3dsg_relationship_splits"] == ["validation"]
    ]
    all_target_scans = [row["scan_id"] for row in scan_summaries if row["ready_for_targeted_export"]]
    m60 = read_json(M60_LOCAL_DIR / "coverage.json")
    target_ready = bool(query_rows) and len(all_target_scans) == len(query_scans) and all(
        row["ready_for_targeted_export"] for row in scan_summaries
    )
    status = (
        "e005_m61_open3dsg_denominator_aligned_export_plan_ready"
        if target_ready
        else "e005_m61_open3dsg_denominator_aligned_export_plan_blocked_payloads"
    )
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "query_rows": len(query_rows),
        "query_scan_count": len(query_scans),
        "query_scans": query_scans,
        "train_query_scan_count": sum(1 for row in scan_summaries if row["open3dsg_relationship_splits"] == ["train"]),
        "validation_query_scan_count": sum(1 for row in scan_summaries if row["open3dsg_relationship_splits"] == ["validation"]),
        "missing_query_scan_count": sum(1 for row in scan_summaries if not row["open3dsg_relationship_splits"]),
        "target_subgraph_count": len(relationship_rows),
        "target_subgraphs_by_source_split": dict(sorted(rows_by_source_split.items())),
        "query_rows_by_source_split": dict(sorted(query_rows_by_source_split.items())),
        "preprocessed_ready_subgraphs": sum(1 for row in relationship_rows if row["preprocessed_ready"]),
        "feature_ready_subgraphs": sum(1 for row in relationship_rows if row["feature_ready"]),
        "validation_overlap_smoke": {
            "target_scans": val_target_scans,
            "query_rows": sum(row["query_rows"] for row in scan_summaries if row["scan_id"] in val_target_scans),
            "subgraph_count": sum(
                len(relationship_by_scan[scan_id])
                for scan_id in val_target_scans
            ),
            "claim_boundary": "smoke_only_not_full_denominator",
        },
        "full_denominator_export": {
            "target_scans": all_target_scans,
            "query_rows": sum(row["query_rows"] for row in scan_summaries if row["scan_id"] in all_target_scans),
            "subgraph_count": len(relationship_rows),
            "requires_runtime_patch": [
                "OPEN3DSG_OBJECT_DUMP_TARGET_SCAN_IDS filter",
                "train+validation target relationship source for test dataloader",
            ],
            "claim_boundary": "performance_claim_false_until_m60_rerun",
        },
        "m60_scan_overlap_count_before_m61": m60.get("scan_overlap_count"),
        "m60_query_candidate_rows_before_m61": m60.get("query_candidate_rows"),
        "source_modified": False,
        "selected_next_unit": "E005-M61 targeted Open3DSG export launch/verification",
    }
    write_jsonl(LOCAL_DATA_DIR / "target_relationship_rows.jsonl", relationship_rows)
    write_json(LOCAL_DATA_DIR / "scan_coverage.json", scan_summaries)
    write_json(LOCAL_DATA_DIR / "coverage.json", coverage)
    write_text(LOCAL_DATA_DIR / "report.md", build_report(coverage, scan_summaries))
    write_jsonl(ARTIFACT_DIR / "target_relationship_rows.jsonl", relationship_rows)
    write_json(ARTIFACT_DIR / "scan_coverage.json", scan_summaries)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, scan_summaries))
    return coverage


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"].endswith("_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
