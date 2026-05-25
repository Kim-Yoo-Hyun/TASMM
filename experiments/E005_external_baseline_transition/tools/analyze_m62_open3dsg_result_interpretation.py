#!/usr/bin/env python3
"""Interpret denominator-aligned Open3DSG query conversion results."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M62_open3dsg_result_interpretation_v0"
M49 = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0" / "metrics.json"
M52 = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0" / "metrics.json"
M60 = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "metrics.json"
M60_COVERAGE = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "coverage.json"
VERSION = "e005_m62_open3dsg_result_interpretation_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def metric_row(source: str, policy: str, metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source,
        "policy": policy,
        "rows": int(metric.get("rows", 0)),
        "success_rows": int(metric.get("query_bridge_success_rows", 0)),
        "success_rate": metric.get("query_bridge_success_rate"),
        "target_detected_rows": int(metric.get("target_detected_rows", 0)),
        "target_detected_rate": metric.get("target_detected_rate"),
        "mean_expected_search_cost": metric.get("mean_expected_search_cost"),
        "mean_attempt_spl_proxy": metric.get("mean_attempt_spl_proxy"),
        "old_location_dead_end_avoided_rows": metric.get("old_location_dead_end_avoided_rows"),
        "old_location_dead_end_avoided_rate": metric.get("old_location_dead_end_avoided_rate"),
        "failure_class_counts": metric.get("failure_class_counts", {}),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "policy",
        "rows",
        "success_rows",
        "success_rate",
        "target_detected_rows",
        "target_detected_rate",
        "mean_expected_search_cost",
        "mean_attempt_spl_proxy",
        "old_location_dead_end_avoided_rows",
        "old_location_dead_end_avoided_rate",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]], decision: dict[str, Any]) -> str:
    by_key = {(row["source"], row["policy"]): row for row in rows}
    h001 = by_key[("H001", "task_context_memory_trust_reobserve_v0")]
    static = by_key[("H001", "static_memory_only_v0")]
    context_agnostic = by_key[("H001", "context_agnostic_memory_trust_reobserve_v0")]
    concept = by_key[("ConceptGraphs", "conceptgraphs_clip_rank_bbox_strict_top5_v0")]
    concept_relaxed = by_key[("ConceptGraphs", "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0")]
    open3dsg = by_key[("Open3DSG", "open3dsg_objects_probs_bbox_strict_top5_v0")]
    open3dsg_relaxed = by_key[("Open3DSG", "open3dsg_objects_probs_bbox_relaxed_1m_top3_v0")]
    open3dsg_center = by_key[("Open3DSG", "open3dsg_objects_probs_center_strict_top5_v0")]
    lines = [
        "# E005-M62 Open3DSG Result Interpretation",
        "",
        "## Facts",
        "",
        f"- M60 status: `{coverage['status']}`.",
        f"- Query rows: {coverage['query_rows']}.",
        f"- Object candidate rows: {coverage['object_candidate_rows']}.",
        f"- Scan overlap: {coverage['scan_overlap_count']} / {coverage['query_scan_count']}.",
        f"- Query candidate rows: {coverage['query_candidate_rows']}.",
        f"- Policy rows: {coverage['policy_rows']}.",
        f"- H001 task-conditioned success: {h001['success_rows']} / {h001['rows']} = {h001['success_rate']}.",
        f"- Static memory success: {static['success_rows']} / {static['rows']} = {static['success_rate']}.",
        f"- Context-agnostic memory-trust success: {context_agnostic['success_rows']} / {context_agnostic['rows']} = {context_agnostic['success_rate']}.",
        f"- ConceptGraphs strict bbox top5 success: {concept['success_rows']} / {concept['rows']} = {concept['success_rate']}.",
        f"- ConceptGraphs relaxed bbox 1m top3 success: {concept_relaxed['success_rows']} / {concept_relaxed['rows']} = {concept_relaxed['success_rate']}.",
        f"- Open3DSG strict bbox top5 success: {open3dsg['success_rows']} / {open3dsg['rows']} = {open3dsg['success_rate']}.",
        f"- Open3DSG relaxed bbox 1m top3 success: {open3dsg_relaxed['success_rows']} / {open3dsg_relaxed['rows']} = {open3dsg_relaxed['success_rate']}.",
        f"- Open3DSG center strict top5 success: {open3dsg_center['success_rows']} / {open3dsg_center['rows']} = {open3dsg_center['success_rate']}.",
        f"- Open3DSG strict failure classes: `{open3dsg['failure_class_counts']}`.",
        "",
        "## Paper Claims",
        "",
        "- M61/M60 supports an `Open3DSG` bridge feasibility claim: denominator-aligned object candidates can be exported and converted into the H001 query metric schema.",
        "- M61/M60 does not support using current `Open3DSG` as a strong performance baseline in the main result table.",
        "- Current `Open3DSG` should be treated as a secondary external scene-graph route whose primary-label adapter is below `ConceptGraphs` unless bounded vocabulary/matching repair changes the result.",
        "",
        "## Agent Inference",
        "",
        f"- H001 exceeds current Open3DSG strict bbox top5 by {decision['h001_minus_open3dsg_strict_success_rows']} success rows.",
        f"- ConceptGraphs exceeds current Open3DSG strict bbox top5 by {decision['conceptgraphs_minus_open3dsg_strict_success_rows']} success rows.",
        "- The dominant Open3DSG failures are not only ranking failures. `no_same_label_candidates` and `target_object_not_in_open3dsg_candidates` indicate vocabulary/object-candidate coverage mismatch.",
        "- For top-tier defense, this strengthens the claim boundary: the paper should not depend on a single external map route, and Open3DSG needs adapter repair before becoming a main baseline.",
        "",
        "## User Judgment Needed",
        "",
        "- Decide whether to spend one bounded repair unit on Open3DSG vocabulary/matching diagnosis, or move to the next external baseline route such as `HOV-SG` / `OpenMask3D`.",
        "",
        "## Next",
        "",
        f"- Recommended next unit: `{decision['next_recommended_unit']}`.",
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    m49 = read_json(M49)["policy_metrics"]
    m52 = read_json(M52)["policy_metrics"]
    m60 = read_json(M60)["policy_metrics"]
    coverage = read_json(M60_COVERAGE)
    rows = [
        metric_row("H001", "static_memory_only_v0", m52["static_memory_only_v0"]),
        metric_row("H001", "context_agnostic_memory_trust_reobserve_v0", m52["context_agnostic_memory_trust_reobserve_v0"]),
        metric_row("H001", "task_context_memory_trust_reobserve_v0", m52["task_context_memory_trust_reobserve_v0"]),
        metric_row("ConceptGraphs", "conceptgraphs_clip_rank_bbox_strict_top5_v0", m49["conceptgraphs_clip_rank_bbox_strict_top5_v0"]),
        metric_row("ConceptGraphs", "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0", m49["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]),
        metric_row("Open3DSG", "open3dsg_objects_probs_bbox_strict_top5_v0", m60["open3dsg_objects_probs_bbox_strict_top5_v0"]),
        metric_row("Open3DSG", "open3dsg_objects_probs_bbox_relaxed_1m_top3_v0", m60["open3dsg_objects_probs_bbox_relaxed_1m_top3_v0"]),
        metric_row("Open3DSG", "open3dsg_objects_probs_center_strict_top5_v0", m60["open3dsg_objects_probs_center_strict_top5_v0"]),
    ]
    by_key = {(row["source"], row["policy"]): row for row in rows}
    decision = {
        "status": "e005_m62_open3dsg_result_interpretation_ready_primary_label_below_conceptgraphs",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "query_rows": coverage["query_rows"],
        "open3dsg_bridge_feasibility_ready": True,
        "open3dsg_main_table_performance_baseline_ready": False,
        "open3dsg_secondary_route_ready": True,
        "h001_minus_open3dsg_strict_success_rows": by_key[("H001", "task_context_memory_trust_reobserve_v0")]["success_rows"] - by_key[("Open3DSG", "open3dsg_objects_probs_bbox_strict_top5_v0")]["success_rows"],
        "conceptgraphs_minus_open3dsg_strict_success_rows": by_key[("ConceptGraphs", "conceptgraphs_clip_rank_bbox_strict_top5_v0")]["success_rows"] - by_key[("Open3DSG", "open3dsg_objects_probs_bbox_strict_top5_v0")]["success_rows"],
        "next_recommended_unit": "E005-M63 bounded Open3DSG vocabulary/object-candidate failure diagnosis or move to HOV-SG/OpenMask3D route",
    }
    report = build_report(coverage, rows, decision)
    write_json(ARTIFACT_DIR / "coverage.json", decision)
    write_jsonl(ARTIFACT_DIR / "comparison_rows.jsonl", rows)
    write_csv(ARTIFACT_DIR / "comparison_rows.csv", rows)
    (ARTIFACT_DIR / "report.md").write_text(report, encoding="utf-8")
    return decision


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
