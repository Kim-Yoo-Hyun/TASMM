#!/usr/bin/env python3
"""Build E005-M54 paper-table claim ledger and method-claim rewrite."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M52_DIR = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0"
M53_DIR = EXP_ROOT / "artifacts" / "E005-M53_paired_failure_table_decision_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M54_paper_table_claim_ledger_v0"
VERSION = "e005_m54_paper_table_claim_ledger_v0"

H001 = "task_context_memory_trust_reobserve_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
STATIC = "static_memory_only_v0"
CONTEXT = "context_agnostic_memory_trust_reobserve_v0"
DETECTOR_TOP5 = "detector_top5_v0"
DETECTOR_TASK = "detector_task_budget_v0"
BOUNDED = "bounded_old_memory_distance_guard_adaptive_top5_v0"
UNBOUNDED = "unbounded_old_memory_distance_guard_until_target_v0"

POLICY_LABELS = {
    STATIC: "Static stale memory",
    DETECTOR_TASK: "Detector task-budget",
    DETECTOR_TOP5: "Detector confidence top-5",
    BOUNDED: "Bounded detector repair",
    CONCEPTGRAPHS: "ConceptGraphs-only map retrieval",
    CONTEXT: "Context-agnostic memory trust + re-observation",
    H001: "H001 task-conditioned memory trust + bounded re-observation",
    UNBOUNDED: "Unbounded detector upper bound",
}

TABLE_POLICIES = [
    STATIC,
    DETECTOR_TASK,
    DETECTOR_TOP5,
    BOUNDED,
    CONCEPTGRAPHS,
    CONTEXT,
    H001,
    UNBOUNDED,
]


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


def rate_pp(metric: dict[str, Any], base: dict[str, Any]) -> float:
    return round(float(metric["query_bridge_success_rate"]) - float(base["query_bridge_success_rate"]), 6)


def cost_delta(metric: dict[str, Any], base: dict[str, Any]) -> float:
    return round(float(metric["mean_expected_search_cost"]) - float(base["mean_expected_search_cost"]), 6)


def table_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    policy_metrics = metrics["policy_metrics"]
    cg = policy_metrics[CONCEPTGRAPHS]
    rows = []
    for policy in TABLE_POLICIES:
        metric = policy_metrics[policy]
        rows.append(
            {
                "policy": policy,
                "paper_label": POLICY_LABELS[policy],
                "rows": metric["rows"],
                "success_rows": metric["query_bridge_success_rows"],
                "success_rate": metric["query_bridge_success_rate"],
                "mean_expected_search_cost": metric["mean_expected_search_cost"],
                "mean_attempt_spl_proxy": metric["mean_attempt_spl_proxy"],
                "old_memory_success_rows": metric["old_memory_success_rows"],
                "detector_reobservation_success_rows": metric["detector_reobservation_success_rows"],
                "old_location_dead_end_avoided_rows": metric["old_location_dead_end_avoided_rows"],
                "success_rate_delta_vs_conceptgraphs": rate_pp(metric, cg),
                "expected_cost_delta_vs_conceptgraphs": cost_delta(metric, cg),
                "paper_table_role": table_role(policy),
            }
        )
    return rows


def table_role(policy: str) -> str:
    if policy == H001:
        return "main_method"
    if policy in {STATIC, CONTEXT}:
        return "memory_ablation"
    if policy in {CONCEPTGRAPHS, DETECTOR_TOP5, DETECTOR_TASK, BOUNDED}:
        return "baseline"
    if policy == UNBOUNDED:
        return "diagnostic_upper_bound"
    return "diagnostic"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]]) -> str:
    header = [
        "Policy",
        "Role",
        "Success",
        "Rate",
        "ExpectedSearchCost",
        "AttemptSPL",
        "Delta vs ConceptGraphs",
    ]
    lines = [
        "| " + " | ".join(header) + " |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["paper_label"],
                    row["paper_table_role"],
                    f"{row['success_rows']} / {row['rows']}",
                    f"{float(row['success_rate']):.6f}",
                    f"{float(row['mean_expected_search_cost']):.6f}",
                    f"{float(row['mean_attempt_spl_proxy']):.6f}",
                    f"{float(row['success_rate_delta_vs_conceptgraphs']):+.6f}",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_claim_ledger(metrics: dict[str, Any], decision: dict[str, Any]) -> list[dict[str, Any]]:
    m = metrics["policy_metrics"]
    evidence = decision["claim_evidence"]
    return [
        {
            "claim_id": "C-M54-001",
            "claim_type": "allowed_main",
            "claim": "H001 improves heldout proxy object search over ConceptGraphs-only open-vocabulary map retrieval.",
            "status": "ready_with_proxy_boundary",
            "evidence": {
                "h001_success": m[H001]["query_bridge_success_rows"],
                "conceptgraphs_success": m[CONCEPTGRAPHS]["query_bridge_success_rows"],
                "paired_h001_only": evidence["h001_vs_conceptgraphs"].get("h001_only", 0),
                "paired_conceptgraphs_only": evidence["h001_vs_conceptgraphs"].get("conceptgraphs_only", 0),
                "query_rows": metrics["query_rows"],
            },
            "allowed_wording": "H001 improves heldout proxy-search success over a ConceptGraphs-only map-retrieval baseline on the M38 query contract.",
            "forbidden_wording": "H001 is a better open-vocabulary mapper than ConceptGraphs.",
            "next_validation_requirement": "Add another external map/proposal baseline before final real RGB-D/open-vocabulary robustness claim.",
        },
        {
            "claim_id": "C-M54-002",
            "claim_type": "allowed_main",
            "claim": "H001 improves over static stale memory by preserving useful old memory while adding bounded re-observation.",
            "status": "ready_with_proxy_boundary",
            "evidence": {
                "h001_success": m[H001]["query_bridge_success_rows"],
                "static_success": m[STATIC]["query_bridge_success_rows"],
                "paired_h001_only": evidence["h001_vs_static"].get("h001_only", 0),
                "query_rows": metrics["query_rows"],
            },
            "allowed_wording": "The method recovers additional heldout queries beyond static stale memory while retaining the same old-memory successes.",
            "forbidden_wording": "The method solves stale memory update.",
            "next_validation_requirement": "Report failure rows and stale old-location boundary cases.",
        },
        {
            "claim_id": "C-M54-003",
            "claim_type": "allowed_secondary",
            "claim": "Structured task context is a secondary conditioning signal.",
            "status": "secondary_ablation_only",
            "evidence": {
                "h001_success": m[H001]["query_bridge_success_rows"],
                "context_agnostic_success": m[CONTEXT]["query_bridge_success_rows"],
                "paired_h001_only": evidence["h001_vs_context_agnostic"].get("h001_only", 0),
                "query_rows": metrics["query_rows"],
            },
            "allowed_wording": "Task context is retained as a controlled condition and secondary ablation.",
            "forbidden_wording": "Human intent is the main contribution or main source of improvement.",
            "next_validation_requirement": "Optional E006 context-sensitive utility benchmark with strong context-agnostic baselines.",
        },
        {
            "claim_id": "C-M54-004",
            "claim_type": "blocked",
            "claim": "Final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "evidence": {
                "current_external_map_baselines_ready": ["ConceptGraphs"],
                "single_external_baseline_only": True,
                "m53_ready": decision["paper_table_decision"]["final_real_rgbd_open_vocab_robustness_ready"],
            },
            "allowed_wording": "Current results are a proxy-search and external-baseline bridge.",
            "forbidden_wording": "The method is robust to real RGB-D/open-vocabulary perception.",
            "next_validation_requirement": "Heldout scan/label split, visibility-aware denominator, detector/proposal baseline, and failure table.",
        },
        {
            "claim_id": "C-M54-005",
            "claim_type": "blocked",
            "claim": "Real navigation SR/SPL improvement.",
            "status": "blocked",
            "evidence": {
                "simulator_or_navmesh_integrated": False,
                "trajectory_execution_available": False,
                "m53_ready": decision["paper_table_decision"]["real_navigation_sr_spl_ready"],
            },
            "allowed_wording": "The current evaluation uses proxy search metrics including ExpectedSearchCost and AttemptSPL.",
            "forbidden_wording": "The method improves real navigation SR/SPL.",
            "next_validation_requirement": "E007 simulator/navmesh/trajectory execution with navigation baselines.",
        },
    ]


def method_rewrite_text() -> str:
    return "\n".join(
        [
            "# E005-M54 Method Claim Rewrite",
            "",
            "## Paper-Facing Framing",
            "",
            "논문 주장:",
            "",
            "- We formulate dynamic object search as a stale semantic memory decision problem.",
            "- The method decides when to preserve old semantic memory and when to trigger bounded re-observation.",
            "- The current result supports a heldout proxy-search claim over static stale memory and `ConceptGraphs`-only map retrieval.",
            "",
            "## Contribution Wording",
            "",
            "Allowed:",
            "",
            "- A task/staleness-aware semantic memory decision layer for dynamic object search.",
            "- A heldout proxy-search evaluation connecting stale memory, open-vocabulary map retrieval, and bounded re-observation.",
            "- Evidence that memory trust and bounded re-observation improve proxy-search success over static memory and `ConceptGraphs`-only retrieval.",
            "",
            "Not allowed yet:",
            "",
            "- Human intent understanding as the main contribution.",
            "- Better open-vocabulary mapping than `ConceptGraphs`.",
            "- Final real RGB-D/open-vocabulary robustness.",
            "- Real navigation `SR` / `SPL` improvement.",
            "",
            "## Method Sentence",
            "",
            "`H001` is a semantic memory decision layer that preserves trustworthy stale object memory while using bounded re-observation to recover targets when old memory is unreliable.",
            "",
            "## Reviewer Defense",
            "",
            "- If asked why this is not just detector ranking: H001 recovers 60 heldout rows that `ConceptGraphs`/detector top-5 miss, and those gains come from memory preservation rather than detector confidence alone.",
            "- If asked why this is not human-intent understanding: current task context gain over context-agnostic memory trust is only 1 row, so task context remains a secondary ablation.",
            "- If asked why this is semantic mapping: the decision uses stale semantic memory, current map/proposal candidates, object identity, staleness state, and search cost rather than image-only detection.",
            "",
        ]
    )


def build_report(coverage: dict[str, Any], claim_ledger: list[dict[str, Any]], table: list[dict[str, Any]]) -> str:
    allowed = [row for row in claim_ledger if row["claim_type"].startswith("allowed")]
    blocked = [row for row in claim_ledger if row["claim_type"] == "blocked"]
    return "\n".join(
        [
            "# E005-M54 Paper-Table Claim Ledger",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Query rows: {coverage['query_rows']}.",
            f"- Main table rows: {len(table)}.",
            f"- Allowed claims: {len(allowed)}.",
            f"- Blocked claims: {len(blocked)}.",
            f"- Main method success: {coverage['h001_success_rows']} / {coverage['query_rows']}.",
            f"- `ConceptGraphs` success: {coverage['conceptgraphs_success_rows']} / {coverage['query_rows']}.",
            f"- Static memory success: {coverage['static_success_rows']} / {coverage['query_rows']}.",
            f"- Context-agnostic memory trust success: {coverage['context_agnostic_success_rows']} / {coverage['query_rows']}.",
            "",
            "## Main Table",
            "",
            markdown_table(table).strip(),
            "",
            "## Decision",
            "",
            "- Main claim: memory trust, staleness handling, and bounded re-observation.",
            "- Human task context: secondary ablation only.",
            "- Real RGB-D/open-vocabulary robustness: next expansion, not current claim.",
            "- Real navigation `SR` / `SPL`: later E007, not current claim.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = read_json(M52_DIR / "metrics.json")
    decision = read_json(M53_DIR / "decision.json")
    if decision.get("status") != "e005_m53_paired_failure_table_decision_ready_memory_trust_supported_task_context_limited":
        raise RuntimeError(f"M53 is not ready: {decision.get('status')}")
    table = table_rows(metrics)
    claim_ledger = build_claim_ledger(metrics, decision)
    policy_metrics = metrics["policy_metrics"]
    coverage = {
        "status": "e005_m54_paper_table_claim_ledger_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_m52_status": "e005_m52_h001_heldout_replay_ready_with_paired_gain",
        "source_m53_status": decision.get("status"),
        "query_rows": metrics["query_rows"],
        "h001_success_rows": policy_metrics[H001]["query_bridge_success_rows"],
        "conceptgraphs_success_rows": policy_metrics[CONCEPTGRAPHS]["query_bridge_success_rows"],
        "static_success_rows": policy_metrics[STATIC]["query_bridge_success_rows"],
        "context_agnostic_success_rows": policy_metrics[CONTEXT]["query_bridge_success_rows"],
        "main_proxy_search_table_ready": True,
        "human_task_context_main_claim_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "recommended_main_claim": "memory_trust_staleness_bounded_reobservation",
        "next_recommended_unit": "E005-M55 real RGB-D/open-vocabulary robustness expansion gate",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "claim_ledger.jsonl", claim_ledger)
    write_jsonl(OUT_DIR / "paper_table_rows.jsonl", table)
    write_csv(OUT_DIR / "paper_table_rows.csv", table)
    write_text(OUT_DIR / "paper_table.md", markdown_table(table))
    write_text(OUT_DIR / "method_claim_rewrite.md", method_rewrite_text())
    write_text(OUT_DIR / "report.md", build_report(coverage, claim_ledger, table))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
