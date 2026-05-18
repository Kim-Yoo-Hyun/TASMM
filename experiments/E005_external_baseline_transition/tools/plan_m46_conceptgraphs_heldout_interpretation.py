#!/usr/bin/env python3
"""Interpret heldout ConceptGraphs metrics and fix the next comparison route."""

from __future__ import annotations

import glob
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M46_conceptgraphs_heldout_interpretation_v0"
M38_DIR = EXP_ROOT / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
M41_DIR = EXP_ROOT / "artifacts" / "E005-M41_conceptgraphs_heldout_runtime_preflight_v0"
M45_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"
VERSION = "e005_m46_conceptgraphs_heldout_interpretation_v0"


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


def output_ready(scan_id: str) -> bool:
    scan_root = STAGED_ROOT / scan_id
    return (
        len(glob.glob(str(scan_root / "gsa_detections_none" / "*.pkl.gz"))) > 0
        and (scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz").exists()
        and (scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz").exists()
    )


def batch_status_rows(batch_rows: list[dict[str, Any]], scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_count_by_scan = Counter(str(row["current_rescan_id"]) for row in scale_rows)
    rows: list[dict[str, Any]] = []
    for batch in batch_rows:
        scan_ids = [str(scan_id) for scan_id in batch["scan_ids"]]
        ready = [scan_id for scan_id in scan_ids if output_ready(scan_id)]
        rows.append(
            {
                "batch_id": batch["batch_id"],
                "scan_ids": scan_ids,
                "scan_count": len(scan_ids),
                "ready_scan_count": len(ready),
                "runtime_outputs_ready": len(ready) == len(scan_ids),
                "query_rows": sum(query_count_by_scan.get(scan_id, 0) for scan_id in scan_ids),
                "tmux_session": batch["tmux_session"],
            }
        )
    return rows


def novelty_comparison_contract() -> list[dict[str, Any]]:
    return [
        {
            "row_id": "static_stale_memory",
            "role": "naive_baseline",
            "tests": "Whether using old semantic memory without update/re-observation fails under dynamic objects.",
            "required_metrics": ["ExpectedSearchCost", "proxy_SR", "proxy_SPL", "stale_old_location_dead_end_rate"],
            "novelty_pressure": "If H001 does not beat this, stale-memory update is not justified.",
        },
        {
            "row_id": "detector_confidence_ranking",
            "role": "naive_current_observation_baseline",
            "tests": "Whether detector confidence alone explains the gain.",
            "required_metrics": ["ExpectedSearchCost", "proxy_SR", "proxy_SPL", "false_positive_before_target_count"],
            "novelty_pressure": "If H001 only matches confidence ranking, the method is a weak reranker.",
        },
        {
            "row_id": "conceptgraphs_only_open_vocabulary_map",
            "role": "external_mapping_baseline",
            "tests": "Whether an open-vocabulary object map alone solves the query without task-conditioned memory decisions.",
            "required_metrics": [
                "strict_bbox_top5",
                "relaxed_bbox_1m_top3",
                "strict_centroid_top5",
                "ExpectedSearchCost",
                "proxy_SR",
                "proxy_SPL",
            ],
            "novelty_pressure": "If ConceptGraphs-only is enough, H001 must shift to a system/baseline contribution or show decision-level gains.",
        },
        {
            "row_id": "task_agnostic_reobservation",
            "role": "ablation_baseline",
            "tests": "Whether memory trust/re-observation helps without human task context.",
            "required_metrics": ["ExpectedSearchCost", "proxy_SR", "proxy_SPL", "context_delta_by_task"],
            "novelty_pressure": "If task-agnostic policy matches H001, human intent/context is not a main contribution.",
        },
        {
            "row_id": "h001_task_conditioned_memory_trust_reobservation_search_cost",
            "role": "proposed_method",
            "tests": "Whether task-conditioned memory trust, re-observation, and search-cost decisions improve dynamic object search.",
            "required_metrics": [
                "ExpectedSearchCost",
                "proxy_SR",
                "proxy_SPL",
                "stale_memory_recovery",
                "failure_reduction_by_class",
            ],
            "novelty_pressure": "Top-tier claim requires consistent gains and ablations showing which component prevents which failure.",
        },
    ]


def recommendation(m45: dict[str, Any], batch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    remaining = [row for row in batch_rows if not row["runtime_outputs_ready"]]
    strict_rate = m45.get("strict_bbox_top5_success_rate")
    if remaining:
        route = "run_remaining_heldout_batches_before_external_baseline_claim"
        reason = (
            "`heldout_b01` is positive but covers only part of the heldout query set; "
            "top-tier baseline rigor needs the remaining heldout batches before final baseline comparison."
        )
    elif strict_rate is not None and strict_rate > 0:
        route = "aggregate_full_heldout_and_compare_h001_policy"
        reason = "All heldout ConceptGraphs batches are ready; the next novelty gate is method-vs-baseline comparison."
    else:
        route = "diagnose_conceptgraphs_target_miss_before_method_claim"
        reason = "Heldout external baseline has weak target recovery; diagnose map/retrieval failures before method comparison."
    return {
        "selected_next_route": route,
        "reason": reason,
        "remaining_batches": [row["batch_id"] for row in remaining],
        "next_recommended_unit": (
            "E005-M47 launch remaining ConceptGraphs heldout runtime batch"
            if remaining
            else "E005-M49 aggregate full heldout ConceptGraphs metrics and compare H001 policy"
        ),
    }


def build_report(
    coverage: dict[str, Any],
    m45: dict[str, Any],
    batch_rows: list[dict[str, Any]],
    novelty_rows: list[dict[str, Any]],
    route: dict[str, Any],
) -> str:
    completed = [row for row in batch_rows if row["runtime_outputs_ready"]]
    remaining = [row for row in batch_rows if not row["runtime_outputs_ready"]]
    return "\n".join(
        [
            "# E005-M46 ConceptGraphs Heldout Interpretation",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- `heldout_b01` query rows: {m45.get('query_rows')} / {m45.get('heldout_all_query_rows')}.",
            f"- `heldout_b01` strict bbox top5: {m45.get('strict_bbox_top5_success_rows')} / {m45.get('strict_bbox_top5_success_rate')}.",
            f"- `heldout_b01` relaxed bbox 1m top3: {m45.get('relaxed_bbox_1m_top3_success_rows')} / {m45.get('relaxed_bbox_1m_top3_success_rate')}.",
            f"- Completed heldout batches: {[row['batch_id'] for row in completed]}.",
            f"- Remaining heldout batches: {[row['batch_id'] for row in remaining]}.",
            "",
            "## Interpretation",
            "",
            "- `ConceptGraphs` target recovery is strong enough to keep it as the first external mapping baseline route.",
            "- The gap between strict centroid and strict bbox supports reporting semantic-map objects as spatial extents, not just points.",
            "- `heldout_b01` is not enough for final baseline rigor because it covers only one batch and is label-skewed.",
            "",
            "## Novelty Comparison Contract",
            "",
            *[
                f"- `{row['row_id']}`: {row['tests']}"
                for row in novelty_rows
            ],
            "",
            "## Decision",
            "",
            f"- Selected route: `{route['selected_next_route']}`.",
            f"- Reason: {route['reason']}",
            "",
            "## Claim Boundary",
            "",
            "- Remaining heldout batches are necessary for external-baseline rigor, but not sufficient for novelty.",
            "- Novelty must come from H001 improving `ExpectedSearchCost`, proxy `SR`, proxy `SPL`, stale-memory recovery, and failure reduction over the fixed comparison rows.",
            "- Do not claim final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL` from M46.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m45 = read_json(M45_DIR / "coverage.json")
    m38 = read_json(M38_DIR / "coverage.json")
    scale_rows = read_jsonl(M38_DIR / "scale_query_rows.jsonl")
    raw_batch_rows = read_jsonl(M41_DIR / "runtime_batch_rows.jsonl")
    batches = batch_status_rows(raw_batch_rows, scale_rows)
    novelty_rows = novelty_comparison_contract()
    route = recommendation(m45, batches)
    coverage = {
        "version": VERSION,
        "status": "e005_m46_conceptgraphs_heldout_interpretation_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m45_status": m45.get("status"),
        "m38_status": m38.get("status"),
        "heldout_all_query_rows": m45.get("heldout_all_query_rows"),
        "heldout_b01_query_rows": m45.get("query_rows"),
        "heldout_b01_strict_bbox_top5_success_rate": m45.get("strict_bbox_top5_success_rate"),
        "heldout_b01_relaxed_bbox_1m_top3_success_rate": m45.get("relaxed_bbox_1m_top3_success_rate"),
        "completed_batch_count": sum(1 for row in batches if row["runtime_outputs_ready"]),
        "remaining_batch_count": sum(1 for row in batches if not row["runtime_outputs_ready"]),
        "remaining_batches": route["remaining_batches"],
        "selected_next_route": route["selected_next_route"],
        "top_tier_novelty_contract_ready": True,
        "remaining_heldout_required_for_baseline_rigor": bool(route["remaining_batches"]),
        "remaining_heldout_sufficient_for_novelty": False,
        "final_baseline_claim_ready": False,
        "paper_table_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": route["next_recommended_unit"],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "batch_status_rows.jsonl", batches)
    write_jsonl(OUT_DIR / "novelty_comparison_contract.jsonl", novelty_rows)
    write_json(OUT_DIR / "route_decision.json", route)
    write_text(OUT_DIR / "report.md", build_report(coverage, m45, batches, novelty_rows, route))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
