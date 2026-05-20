#!/usr/bin/env python3
"""Aggregate ConceptGraphs heldout query metrics across all heldout batches."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
DEFAULT_M45_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0"
VERSION = "e005_m49_conceptgraphs_full_heldout_aggregation_v0"
PRIMARY_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
RELAXED_POLICY = "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"
CENTROID_POLICY = "conceptgraphs_clip_rank_centroid_strict_top5_v0"


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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def metric_from_policy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    detected = [row for row in rows if row.get("target_detected")]
    return {
        "rows": len(rows),
        "query_bridge_success_rows": sum(1 for row in rows if row.get("query_bridge_success")),
        "query_bridge_success_rate": safe_rate(sum(1 for row in rows if row.get("query_bridge_success")), len(rows)),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in rows if row.get("expected_search_cost") is not None]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows if row.get("attempt_spl_proxy") is not None]),
        "mean_target_rank_if_detected": safe_mean([float(row["target_rank"]) for row in detected if row.get("target_rank") is not None]),
    }


def derive_batch_coverage(m45_dir: Path, batch_id: str, policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = read_json(m45_dir / f"metrics_{batch_id}.json")
    object_rows = read_jsonl(m45_dir / f"object_rows_{batch_id}.jsonl")
    candidate_rows = read_jsonl(m45_dir / f"candidate_rows_{batch_id}.jsonl")
    suite = next(iter(metrics.get("suites", {}).values()), {})
    primary = suite.get("policy_metrics", {}).get(PRIMARY_POLICY, {})
    relaxed = suite.get("policy_metrics", {}).get(RELAXED_POLICY, {})
    primary_rows = [row for row in policy_rows if row.get("policy") == PRIMARY_POLICY]
    return {
        "status": "derived_from_metric_rows",
        "scan_count": suite.get("scan_count", len({row.get("scan_id") for row in primary_rows})),
        "query_rows": suite.get("query_rows", len(primary_rows)),
        "target_uid_count": suite.get("target_uid_count", len({row.get("target_uid") for row in primary_rows})),
        "object_rows": len(object_rows),
        "candidate_rows": len(candidate_rows),
        "strict_bbox_top5_success_rows": primary.get("query_bridge_success_rows", sum(1 for row in primary_rows if row.get("query_bridge_success"))),
        "strict_bbox_top5_success_rate": primary.get("query_bridge_success_rate"),
        "relaxed_bbox_1m_top3_success_rows": relaxed.get("query_bridge_success_rows"),
        "relaxed_bbox_1m_top3_success_rate": relaxed.get("query_bridge_success_rate"),
    }


def summarize_rows(rows: list[dict[str, Any]], key: str, success_field: str = "query_bridge_success") -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    summary = []
    for value, group in sorted(grouped.items()):
        success = sum(1 for row in group if row.get(success_field))
        summary.append(
            {
                key: value,
                "rows": len(group),
                "success_rows": success,
                "success_rate": safe_rate(success, len(group)),
                "target_detected_rows": sum(1 for row in group if row.get("target_detected")),
                "target_detected_rate": safe_rate(sum(1 for row in group if row.get("target_detected")), len(group)),
                "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in group if row.get("expected_search_cost") is not None]),
            }
        )
    return summary


def build_report(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    primary = metrics["policy_metrics"][PRIMARY_POLICY]
    relaxed = metrics["policy_metrics"][RELAXED_POLICY]
    centroid = metrics["policy_metrics"][CENTROID_POLICY]
    return "\n".join(
        [
            "# E005-M49 ConceptGraphs Full Heldout Aggregation",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Batches: {', '.join(coverage['batch_ids'])}.",
            f"- Scans: {coverage['scan_count']}.",
            f"- Query rows: {coverage['query_rows']}.",
            f"- Target uids: {coverage['target_uid_count']} summed over batches.",
            f"- Object rows: {coverage['object_rows']}.",
            f"- Candidate rows: {coverage['candidate_rows']}.",
            f"- Primary policy: `{PRIMARY_POLICY}`.",
            f"- Primary strict bbox top5 success rows/rate: {primary['query_bridge_success_rows']} / {primary['query_bridge_success_rate']}.",
            f"- Primary `ExpectedSearchCost`: {primary['mean_expected_search_cost']}.",
            f"- Primary proxy `SPL`: {primary['mean_attempt_spl_proxy']}.",
            f"- Relaxed bbox 1m top3 success rows/rate: {relaxed['query_bridge_success_rows']} / {relaxed['query_bridge_success_rate']}.",
            f"- Centroid strict top5 success rows/rate: {centroid['query_bridge_success_rows']} / {centroid['query_bridge_success_rate']}.",
            "",
            "## Claim Boundary",
            "",
            "- This is a full 9-scan heldout `ConceptGraphs` external mapping baseline aggregation for the current E005 query contract.",
            "- This supports external-baseline comparison readiness, not final H001 superiority by itself.",
            "- It does not support final real navigation `SR` / `SPL`; proxy search metrics remain separate from embodied navigation.",
            "",
            "## Agent Inference",
            "",
            "- The primary strict result is substantially lower than the relaxed bbox result, so geometry threshold sensitivity remains a reviewer-facing boundary.",
            "- The next defensible gate is to compare this aggregated `ConceptGraphs-only open-vocabulary map` baseline against H001 policies under the same query schema.",
            "",
        ]
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    batch_rows: list[dict[str, Any]] = []
    policy_rows_all: list[dict[str, Any]] = []
    errors: list[str] = []

    for batch_id in args.batch_ids:
        coverage = read_json(args.m45_dir / f"coverage_{batch_id}.json")
        policy_rows = read_jsonl(args.m45_dir / f"policy_rows_{batch_id}.jsonl")
        if not coverage:
            coverage = derive_batch_coverage(args.m45_dir, batch_id, policy_rows)
        if "ready" not in str(coverage.get("status", "")):
            if coverage.get("status") != "derived_from_metric_rows":
                errors.append(f"coverage_not_ready:{batch_id}:{coverage.get('status')}")
        if not policy_rows:
            errors.append(f"missing_policy_rows:{batch_id}")
        batch_rows.append(
            {
                "batch_id": batch_id,
                "status": coverage.get("status"),
                "scan_count": coverage.get("scan_count", 0),
                "query_rows": coverage.get("query_rows", 0),
                "target_uid_count": coverage.get("target_uid_count", 0),
                "object_rows": coverage.get("object_rows", 0),
                "candidate_rows": coverage.get("candidate_rows", 0),
                "strict_bbox_top5_success_rows": coverage.get("strict_bbox_top5_success_rows", 0),
                "strict_bbox_top5_success_rate": coverage.get("strict_bbox_top5_success_rate"),
                "relaxed_bbox_1m_top3_success_rows": coverage.get("relaxed_bbox_1m_top3_success_rows", 0),
                "relaxed_bbox_1m_top3_success_rate": coverage.get("relaxed_bbox_1m_top3_success_rate"),
            }
        )
        policy_rows_all.extend(policy_rows)

    if errors:
        coverage = {
            "status": "e005_m49_conceptgraphs_full_heldout_aggregation_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "batch_ids": args.batch_ids,
            "errors": errors,
            "next_recommended_unit": "Repair missing M45 batch metrics",
        }
        write_json(args.out_dir / "coverage.json", coverage)
        write_jsonl(args.out_dir / "batch_rows.jsonl", batch_rows)
        write_text(args.out_dir / "report.md", "# E005-M49 ConceptGraphs Full Heldout Aggregation\n\nBlocked.\n")
        return coverage

    policy_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows_all:
        policy_groups[str(row.get("policy"))].append(row)

    policy_metrics = {policy: metric_from_policy_rows(rows) for policy, rows in sorted(policy_groups.items())}
    primary_rows = policy_groups.get(PRIMARY_POLICY, [])
    metrics = {
        "version": VERSION,
        "policy_metrics": policy_metrics,
        "primary_policy": PRIMARY_POLICY,
        "primary_by_label": summarize_rows(primary_rows, "label_canonical"),
        "primary_by_task_context": summarize_rows(primary_rows, "task_context_id"),
        "primary_by_row_band": summarize_rows(primary_rows, "row_band"),
    }
    coverage = {
        "status": "e005_m49_conceptgraphs_full_heldout_aggregation_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_ids": args.batch_ids,
        "scan_count": sum(int(row["scan_count"] or 0) for row in batch_rows),
        "query_rows": len(primary_rows),
        "query_rows_from_batch_coverage": sum(int(row["query_rows"] or 0) for row in batch_rows),
        "target_uid_count": sum(int(row["target_uid_count"] or 0) for row in batch_rows),
        "object_rows": sum(int(row["object_rows"] or 0) for row in batch_rows),
        "candidate_rows": sum(int(row["candidate_rows"] or 0) for row in batch_rows),
        "primary_policy": PRIMARY_POLICY,
        "primary_strict_bbox_top5_success_rows": policy_metrics[PRIMARY_POLICY]["query_bridge_success_rows"],
        "primary_strict_bbox_top5_success_rate": policy_metrics[PRIMARY_POLICY]["query_bridge_success_rate"],
        "relaxed_bbox_1m_top3_success_rows": policy_metrics[RELAXED_POLICY]["query_bridge_success_rows"],
        "relaxed_bbox_1m_top3_success_rate": policy_metrics[RELAXED_POLICY]["query_bridge_success_rate"],
        "centroid_strict_top5_success_rows": policy_metrics[CENTROID_POLICY]["query_bridge_success_rows"],
        "centroid_strict_top5_success_rate": policy_metrics[CENTROID_POLICY]["query_bridge_success_rate"],
        "label_count": len(Counter(str(row.get("label_canonical")) for row in primary_rows)),
        "paper_table_claim_ready": True,
        "final_h001_superiority_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M50 H001 vs ConceptGraphs heldout comparison gate",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "batch_rows.jsonl", batch_rows)
    write_jsonl(args.out_dir / "policy_rows_primary.jsonl", primary_rows)
    write_jsonl(args.out_dir / "primary_by_label.jsonl", metrics["primary_by_label"])
    write_jsonl(args.out_dir / "primary_by_task_context.jsonl", metrics["primary_by_task_context"])
    write_text(args.out_dir / "report.md", build_report(coverage, metrics))
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-ids", nargs="+", default=["heldout_b01", "heldout_b02", "heldout_b03"])
    parser.add_argument("--m45-dir", type=Path, default=DEFAULT_M45_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    coverage = run(args)
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
