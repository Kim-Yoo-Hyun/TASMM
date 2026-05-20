#!/usr/bin/env python3
"""Gate H001-vs-ConceptGraphs comparison readiness."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
E004_M03 = ROOT / "experiments" / "E004_task_context_memory_trust" / "artifacts" / "E004-M03_memory_trust_policy_v0"
E004_M05 = ROOT / "experiments" / "E004_task_context_memory_trust" / "artifacts" / "E004-M05_scale_split_stress_v0"
E005_M35 = ROOT / "experiments" / "E005_external_baseline_transition" / "artifacts" / "E005-M35_conceptgraphs_4scan_query_metric_v0"
E005_M45 = ROOT / "experiments" / "E005_external_baseline_transition" / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
E005_M49 = ROOT / "experiments" / "E005_external_baseline_transition" / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0"
OUT_DIR = ROOT / "experiments" / "E005_external_baseline_transition" / "artifacts" / "E005-M50_h001_vs_conceptgraphs_gate_v0"
VERSION = "e005_m50_h001_vs_conceptgraphs_gate_v0"
H001_POLICY = "task_context_memory_trust_reobserve_v0"
CONCEPTGRAPHS_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"


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


def metric(metrics: dict[str, Any], policy: str) -> dict[str, Any]:
    return metrics.get("policy_metrics", {}).get(policy, {})


def normalize_uid(row: dict[str, Any]) -> str:
    value = str(row.get("query_uid") or row.get("row_uid") or "")
    return value.removeprefix("m38:")


def policy_rows(path: Path, policy: str) -> list[dict[str, Any]]:
    return [row for row in read_jsonl(path) if row.get("policy") == policy]


def build_report(coverage: dict[str, Any], comparison_rows: list[dict[str, Any]]) -> str:
    h001 = comparison_rows[0]
    cg = comparison_rows[1]
    return "\n".join(
        [
            "# E005-M50 H001 Vs ConceptGraphs Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- H001 source: `E004-M03`, policy `{H001_POLICY}`, rows {h001['rows']}.",
            f"- H001 success rows/rate: {h001['success_rows']} / {h001['success_rate']}.",
            f"- H001 mean `ExpectedSearchCost`: {h001['mean_expected_search_cost']}.",
            f"- H001 mean proxy `SPL`: {h001['mean_attempt_spl_proxy']}.",
            f"- `ConceptGraphs` source: `E005-M49`, policy `{CONCEPTGRAPHS_POLICY}`, rows {cg['rows']}.",
            f"- `ConceptGraphs` strict bbox top5 success rows/rate: {cg['success_rows']} / {cg['success_rate']}.",
            f"- `ConceptGraphs` mean `ExpectedSearchCost`: {cg['mean_expected_search_cost']}.",
            f"- `ConceptGraphs` mean proxy `SPL`: {cg['mean_attempt_spl_proxy']}.",
            f"- E004/H001 vs `ConceptGraphs` heldout common query rows: {coverage['h001_vs_conceptgraphs_heldout_common_queries']}.",
            f"- E004/H001 vs `ConceptGraphs` dev common query rows: {coverage['h001_vs_conceptgraphs_dev_common_queries']}.",
            "",
            "## Claim Boundary",
            "",
            "- The two rows above are not an apples-to-apples superiority comparison because they use different query universes and proposal/map sources.",
            "- `ConceptGraphs` is now usable as an external open-vocabulary map baseline table entry for its own heldout contract.",
            "- H001 superiority over `ConceptGraphs` remains blocked until H001 policies are replayed on the same `M38` heldout query contract, or both methods are evaluated on a newly fixed common split.",
            "",
            "## Next Unit",
            "",
            "- E005-M51 should define and run H001 heldout policy replay on the `M38` query rows before claiming method superiority.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    e004_m03_metrics = read_json(E004_M03 / "metrics.json")
    e004_m05_metrics = read_json(E004_M05 / "metrics.json")
    e005_m49_metrics = read_json(E005_M49 / "metrics.json")
    e005_m49_coverage = read_json(E005_M49 / "coverage.json")

    h001_rows = policy_rows(E004_M03 / "policy_rows.jsonl", H001_POLICY)
    cg_dev_rows = policy_rows(E005_M35 / "policy_rows.jsonl", CONCEPTGRAPHS_POLICY)
    cg_heldout_rows: list[dict[str, Any]] = []
    for batch_id in ["b01", "b02", "b03"]:
        cg_heldout_rows.extend(policy_rows(E005_M45 / f"policy_rows_heldout_{batch_id}.jsonl", CONCEPTGRAPHS_POLICY))

    h001_uids = {normalize_uid(row) for row in h001_rows}
    cg_dev_uids = {normalize_uid(row) for row in cg_dev_rows}
    cg_heldout_uids = {normalize_uid(row) for row in cg_heldout_rows}

    h001_metric = metric(e004_m03_metrics, H001_POLICY)
    cg_metric = e005_m49_metrics.get("policy_metrics", {}).get(CONCEPTGRAPHS_POLICY, {})
    comparison_rows = [
        {
            "method": "H001",
            "source": "E004-M03_memory_trust_policy_v0",
            "policy": H001_POLICY,
            "rows": h001_metric.get("rows"),
            "success_rows": h001_metric.get("query_bridge_success_rows"),
            "success_rate": h001_metric.get("query_bridge_success_rate"),
            "mean_expected_search_cost": h001_metric.get("mean_expected_search_cost"),
            "mean_attempt_spl_proxy": h001_metric.get("mean_attempt_spl_proxy"),
            "split": "E003-M75/E004 96-row direct bridge denominator",
            "paired_with_conceptgraphs": False,
        },
        {
            "method": "ConceptGraphs",
            "source": "E005-M49_conceptgraphs_full_heldout_aggregation_v0",
            "policy": CONCEPTGRAPHS_POLICY,
            "rows": cg_metric.get("rows"),
            "success_rows": cg_metric.get("query_bridge_success_rows"),
            "success_rate": cg_metric.get("query_bridge_success_rate"),
            "mean_expected_search_cost": cg_metric.get("mean_expected_search_cost"),
            "mean_attempt_spl_proxy": cg_metric.get("mean_attempt_spl_proxy"),
            "split": "E005-M38 heldout 9-scan / 195-query contract",
            "paired_with_conceptgraphs": True,
        },
    ]
    coverage = {
        "status": "e005_m50_h001_vs_conceptgraphs_gate_ready_common_split_required",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_policy": H001_POLICY,
        "conceptgraphs_policy": CONCEPTGRAPHS_POLICY,
        "h001_query_rows": len(h001_uids),
        "conceptgraphs_dev_query_rows": len(cg_dev_uids),
        "conceptgraphs_heldout_query_rows": len(cg_heldout_uids),
        "conceptgraphs_heldout_scan_count": e005_m49_coverage.get("scan_count"),
        "h001_vs_conceptgraphs_dev_common_queries": len(h001_uids & cg_dev_uids),
        "h001_vs_conceptgraphs_heldout_common_queries": len(h001_uids & cg_heldout_uids),
        "aggregate_side_by_side_ready": True,
        "paired_superiority_claim_ready": False,
        "paper_table_conceptgraphs_baseline_ready": bool(e005_m49_coverage.get("paper_table_claim_ready")),
        "h001_task_context_claim_strength": e004_m05_metrics.get("overall", {}).get("task_vs_context_success_delta"),
        "final_real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M51 H001 heldout policy replay contract",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "comparison_rows.jsonl", comparison_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, comparison_rows))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
