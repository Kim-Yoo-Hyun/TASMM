#!/usr/bin/env python3
"""Plan the E005-M38 ConceptGraphs heldout/scale expansion."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
VERSION = "e005_m38_conceptgraphs_heldout_scale_v0"

E001_QUERY_ROWS = (
    ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
    / "query_rows.jsonl"
)
M21_ROWS = EXP_ROOT / "artifacts" / "E005-M21_conceptgraphs_staging_materialization_v0" / "materialization_rows.jsonl"
M35_COVERAGE = EXP_ROOT / "artifacts" / "E005-M35_conceptgraphs_4scan_query_metric_v0" / "coverage.json"
M36_AGGREGATE = EXP_ROOT / "artifacts" / "E005-M36_conceptgraphs_failure_boundary_v0" / "aggregate.json"
M37_DECISION = EXP_ROOT / "artifacts" / "E005-M37_external_baseline_comparison_v0" / "route_decision.json"
SCAN_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
CONCEPTGRAPHS_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
GENERIC_LABELS = {"item"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def label_counts(rows: list[dict[str, Any]], key: str = "object_label") -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def row_band_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row["row_band"]) for row in rows).items()))


def task_context_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row["task_context_id"]) for row in rows).items()))


def scan_payload_status(scan_id: str) -> dict[str, Any]:
    scan_dir = SCAN_ROOT / scan_id
    staged_dir = CONCEPTGRAPHS_ROOT / scan_id
    sequence_zip = scan_dir / "sequence.zip"
    return {
        "scan_id": scan_id,
        "scan_dir_exists": scan_dir.exists(),
        "sequence_zip_exists": sequence_zip.exists(),
        "sequence_zip_path": str(sequence_zip),
        "conceptgraphs_staged_dir_exists": staged_dir.exists(),
        "conceptgraphs_staged_dir": str(staged_dir),
        "conceptgraphs_runtime_output_ready": bool(
            (staged_dir / "pcd_saves").exists()
            and list((staged_dir / "pcd_saves").glob("*_post.pkl.gz"))
        ),
    }


def split_for_scan(scan_id: str, existing_metric_scans: set[str]) -> str:
    if scan_id in existing_metric_scans:
        return "dev_existing_4scan_metric_ready"
    return "heldout_sequence_required"


def build_scale_query_rows(rows: list[dict[str, Any]], existing_metric_scans: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scale_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for row in rows:
        label = str(row["object_label"])
        bridge_query_uid = f"m38:{row['base_row_uid']}:{row['task_context_id']}"
        common = {
            "m38_version": VERSION,
            "bridge_query_uid": bridge_query_uid,
            "bridge_role": "conceptgraphs_heldout_scale_query",
            "split": split_for_scan(str(row["rescan_id"]), existing_metric_scans),
            "current_rescan_id": row["rescan_id"],
            "reference_scan_id": row["reference_scan_id"],
            "pair_uid": row["pair_uid"],
            "base_row_uid": row["base_row_uid"],
            "row_uid": row["row_uid"],
            "target_uid": f"{row['rescan_id']}:{row['object_instance_id_rescan']}",
            "object_instance_id_ref": row["object_instance_id_ref"],
            "object_instance_id_rescan": row["object_instance_id_rescan"],
            "label_canonical": label,
            "task_context_id": row["task_context_id"],
            "row_band": row["row_band"],
            "old_memory_is_stale": row.get("old_memory_is_stale"),
            "old_location_dead_end_expected": row.get("old_location_dead_end_expected"),
            "expected_memory_state": row.get("expected_memory_state"),
            "allowed_for_detector": ["current_rescan_id", "label_canonical", "prompt_set", "RGB-D sequence"],
            "blocked_for_detector": [
                "target_uid",
                "object_instance_id_rescan",
                "candidate_is_target",
                "matched_3dssg_instance_id",
                "task outcome labels",
            ],
        }
        if label in GENERIC_LABELS:
            excluded_rows.append({**common, "exclude_reason": "generic_context_label", "prompt_role": "generic_context"})
        else:
            scale_rows.append({**common, "prompt_role": "detector_target"})
    return scale_rows, excluded_rows


def build_scan_rows(rows: list[dict[str, Any]], scale_rows: list[dict[str, Any]], existing_metric_scans: set[str]) -> list[dict[str, Any]]:
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scale_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_scan[str(row["rescan_id"])].append(row)
    for row in scale_rows:
        scale_by_scan[str(row["current_rescan_id"])].append(row)

    scan_rows: list[dict[str, Any]] = []
    for scan_id in sorted(rows_by_scan):
        source_rows = rows_by_scan[scan_id]
        eligible_rows = scale_by_scan.get(scan_id, [])
        payload = scan_payload_status(scan_id)
        labels = set(str(row["object_label"]) for row in source_rows)
        eligible_labels = set(str(row["label_canonical"]) for row in eligible_rows)
        scan_rows.append(
            {
                **payload,
                "split": split_for_scan(scan_id, existing_metric_scans),
                "source_query_rows": len(source_rows),
                "eligible_query_rows": len(eligible_rows),
                "base_target_rows": len({str(row["base_row_uid"]) for row in source_rows}),
                "eligible_base_target_rows": len({str(row["base_row_uid"]) for row in eligible_rows}),
                "label_count": len(labels),
                "eligible_label_count": len(eligible_labels),
                "label_counts": label_counts(source_rows),
                "eligible_label_counts": label_counts(eligible_rows, key="label_canonical") if eligible_rows else {},
                "row_band_counts": row_band_counts(source_rows),
                "task_context_counts": task_context_counts(source_rows),
                "download_required_for_scale": not payload["sequence_zip_exists"],
                "staging_required_for_scale": not payload["conceptgraphs_staged_dir_exists"],
                "runtime_required_for_scale": not payload["conceptgraphs_runtime_output_ready"],
            }
        )
    return scan_rows


def summarize_split(scale_rows: list[dict[str, Any]], scan_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scans_by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scale_rows:
        rows_by_split[str(row["split"])].append(row)
    for row in scan_rows:
        scans_by_split[str(row["split"])].append(row)

    dev_labels = {str(row["label_canonical"]) for row in rows_by_split.get("dev_existing_4scan_metric_ready", [])}
    heldout_labels = {str(row["label_canonical"]) for row in rows_by_split.get("heldout_sequence_required", [])}
    return {
        "splits": {
            split: {
                "scan_count": len(scans_by_split.get(split, [])),
                "query_rows": len(rows),
                "base_target_rows": len({str(row["base_row_uid"]) for row in rows}),
                "label_counts": label_counts(rows, key="label_canonical") if rows else {},
                "row_band_counts": row_band_counts(rows) if rows else {},
                "task_context_counts": task_context_counts(rows) if rows else {},
            }
            for split, rows in sorted(rows_by_split.items())
        },
        "dev_label_count": len(dev_labels),
        "heldout_label_count": len(heldout_labels),
        "heldout_labels_seen_in_dev": sorted(heldout_labels & dev_labels),
        "heldout_labels_not_seen_in_dev": sorted(heldout_labels - dev_labels),
        "dev_labels_not_in_heldout": sorted(dev_labels - heldout_labels),
    }


def build_contract(
    scale_rows: list[dict[str, Any]],
    excluded_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    split_summary: dict[str, Any],
    m35: dict[str, Any],
    m36: dict[str, Any],
    m37: dict[str, Any],
) -> dict[str, Any]:
    missing_sequence = [row["scan_id"] for row in scan_rows if row["download_required_for_scale"]]
    heldout_rows = [row for row in scale_rows if row["split"] == "heldout_sequence_required"]
    return {
        "m38_version": VERSION,
        "status": "e005_m38_conceptgraphs_heldout_scale_plan_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "target_scale_contract": {
            "name": "all_query_rescan_universe_13scan_v0",
            "source": "E001 query rows, excluding generic context labels",
            "total_source_query_rows": len(scale_rows) + len(excluded_rows),
            "eligible_query_rows": len(scale_rows),
            "excluded_query_rows": len(excluded_rows),
            "scan_count": len(scan_rows),
            "base_target_rows": len({str(row["base_row_uid"]) for row in scale_rows}),
            "task_contexts": sorted({str(row["task_context_id"]) for row in scale_rows}),
            "generic_label_policy": "exclude labels in GENERIC_LABELS from detector/query metric table",
        },
        "split_contract": {
            "dev_existing_4scan_metric_ready": "Current E005-M35/M36 4-scan metric/failure-boundary set.",
            "heldout_sequence_required": "Remaining E001 query rescans; sequence.zip must be acquired before ConceptGraphs runtime.",
            "split_summary": split_summary,
        },
        "metric_contract": {
            "primary": "strict_bbox_0p5m_top5",
            "sanity": "strict_center_0p5m_top5",
            "diagnostic_only": "relaxed_bbox_1m_top3",
            "blocked_claims": [
                "Do not use relaxed 1m hits as strict success.",
                "Do not claim final external baseline performance until heldout scans have runtime outputs and metrics.",
                "Do not claim real navigation SR/SPL from this table.",
            ],
        },
        "current_evidence": {
            "m35_status": m35.get("status"),
            "m35_scan_count": m35.get("scan_count"),
            "m35_final_baseline_claim_ready": m35.get("final_baseline_claim_ready"),
            "m36_primary_failure_classes": (
                m36.get("suites", {}).get("primary_m60", {}).get("overall", {}).get("failure_class_counts")
            ),
            "m37_selected_next_route": m37.get("selected_next_route"),
        },
        "next_execution_requirements": {
            "missing_sequence_scan_count": len(missing_sequence),
            "missing_sequence_scan_ids": missing_sequence,
            "heldout_query_rows_after_exclusion": len(heldout_rows),
            "download_or_staging_required": bool(missing_sequence),
            "next_recommended_unit": "E005-M39 ConceptGraphs heldout sequence acquisition / staging launch",
        },
        "claim_status": {
            "heldout_contract_ready": True,
            "scale_runtime_ready": False,
            "paper_table_claim_ready": False,
            "final_conceptgraphs_baseline_claim_ready": False,
        },
    }


def build_report(contract: dict[str, Any]) -> str:
    split = contract["split_contract"]["split_summary"]
    target = contract["target_scale_contract"]
    requirements = contract["next_execution_requirements"]
    claim = contract["claim_status"]
    lines = [
        "# E005-M38 ConceptGraphs Heldout Scale",
        "",
        "## Status",
        "",
        contract["status"],
        "",
        "## Facts",
        "",
        f"- Target scale: `{target['name']}`.",
        f"- Source query rows: {target['total_source_query_rows']}.",
        f"- Eligible query rows after generic-label exclusion: {target['eligible_query_rows']}.",
        f"- Excluded query rows: {target['excluded_query_rows']}.",
        f"- Scan count: {target['scan_count']}.",
        f"- Base target rows: {target['base_target_rows']}.",
        f"- Dev existing split scans: {split['splits'].get('dev_existing_4scan_metric_ready', {}).get('scan_count', 0)}.",
        f"- Dev existing split query rows: {split['splits'].get('dev_existing_4scan_metric_ready', {}).get('query_rows', 0)}.",
        f"- Heldout sequence-required scans: {split['splits'].get('heldout_sequence_required', {}).get('scan_count', 0)}.",
        f"- Heldout sequence-required query rows: {split['splits'].get('heldout_sequence_required', {}).get('query_rows', 0)}.",
        f"- Heldout labels seen in dev: {len(split['heldout_labels_seen_in_dev'])}.",
        f"- Heldout labels not seen in dev: {len(split['heldout_labels_not_seen_in_dev'])}.",
        f"- Missing sequence scan count: {requirements['missing_sequence_scan_count']}.",
        "",
        "## Claim Boundary",
        "",
        f"- Heldout contract ready: {str(claim['heldout_contract_ready']).lower()}.",
        f"- Scale runtime ready: {str(claim['scale_runtime_ready']).lower()}.",
        f"- Paper table claim ready: {str(claim['paper_table_claim_ready']).lower()}.",
        "- Keep `strict_bbox_0p5m_top5`, `strict_center_0p5m_top5`, and `relaxed_bbox_1m_top3` separate.",
        "",
        "## Agent Inference",
        "",
        "- The current 4-scan result should become the dev/diagnostic split, not the final external baseline table.",
        "- The next useful expansion is the full E001 current-rescan query universe: 13 scans and 291 eligible query rows.",
        "- The blocker is data/runtime scale, not query schema: 9 heldout scans need `sequence.zip` acquisition/staging before `ConceptGraphs` runtime.",
        "- Heldout labels include both dev-seen and dev-unseen categories, so this split can expose label-transfer weakness instead of hiding it.",
        "",
        "## Next",
        "",
        f"- Next recommended unit: `{requirements['next_recommended_unit']}`.",
        "- Launch downloads/staging as a background job with logs under `logs/`; do not block Codex on sequence acquisition.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    e001_rows = read_jsonl(E001_QUERY_ROWS)
    m21_rows = read_jsonl(M21_ROWS)
    m35 = read_json(M35_COVERAGE)
    m36 = read_json(M36_AGGREGATE)
    m37 = read_json(M37_DECISION)
    existing_metric_scans = set(str(row["scan_id"]) for row in m21_rows)
    if m35.get("scan_ids"):
        existing_metric_scans = set(str(scan_id) for scan_id in m35["scan_ids"])

    scale_rows, excluded_rows = build_scale_query_rows(e001_rows, existing_metric_scans)
    scan_rows = build_scan_rows(e001_rows, scale_rows, existing_metric_scans)
    split_summary = summarize_split(scale_rows, scan_rows)
    contract = build_contract(scale_rows, excluded_rows, scan_rows, split_summary, m35, m36, m37)
    coverage = {
        "m38_version": VERSION,
        "status": contract["status"],
        "generated_at": contract["generated_at"],
        "target_scale": contract["target_scale_contract"]["name"],
        "scan_count": contract["target_scale_contract"]["scan_count"],
        "eligible_query_rows": contract["target_scale_contract"]["eligible_query_rows"],
        "excluded_query_rows": contract["target_scale_contract"]["excluded_query_rows"],
        "dev_existing_scan_count": split_summary["splits"].get("dev_existing_4scan_metric_ready", {}).get("scan_count", 0),
        "heldout_sequence_required_scan_count": split_summary["splits"].get("heldout_sequence_required", {}).get("scan_count", 0),
        "heldout_sequence_required_query_rows": split_summary["splits"].get("heldout_sequence_required", {}).get("query_rows", 0),
        "missing_sequence_scan_count": contract["next_execution_requirements"]["missing_sequence_scan_count"],
        "heldout_labels_seen_in_dev": len(split_summary["heldout_labels_seen_in_dev"]),
        "heldout_labels_not_seen_in_dev": len(split_summary["heldout_labels_not_seen_in_dev"]),
        "paper_table_claim_ready": False,
        "next_recommended_unit": contract["next_execution_requirements"]["next_recommended_unit"],
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "heldout_contract.json", contract)
    write_jsonl(OUT_DIR / "scale_query_rows.jsonl", scale_rows)
    write_jsonl(OUT_DIR / "excluded_query_rows.jsonl", excluded_rows)
    write_jsonl(OUT_DIR / "scan_rows.jsonl", scan_rows)
    write_text(OUT_DIR / "report.md", build_report(contract))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
