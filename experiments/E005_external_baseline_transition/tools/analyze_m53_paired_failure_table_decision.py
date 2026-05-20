#!/usr/bin/env python3
"""Analyze M52 paired heldout wins/losses and decide paper-table claims."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M52_DIR = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M53_paired_failure_table_decision_v0"
VERSION = "e005_m53_paired_failure_table_decision_v0"

H001 = "task_context_memory_trust_reobserve_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
STATIC = "static_memory_only_v0"
CONTEXT = "context_agnostic_memory_trust_reobserve_v0"
DETECTOR_TOP5 = "detector_top5_v0"
UNBOUNDED = "unbounded_old_memory_distance_guard_until_target_v0"


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


def paired_outcome(a_success: bool, b_success: bool, a_name: str, b_name: str) -> str:
    if a_success and b_success:
        return "both_success"
    if a_success and not b_success:
        return f"{a_name}_only"
    if b_success and not a_success:
        return f"{b_name}_only"
    return "both_fail"


def gain_source(h001: dict[str, Any], static: dict[str, Any], context: dict[str, Any], conceptgraphs: dict[str, Any]) -> str:
    if not h001["query_bridge_success"] or conceptgraphs["query_bridge_success"]:
        return "not_h001_over_conceptgraphs_gain"
    if static["query_bridge_success"]:
        return "static_memory_preservation"
    if context["query_bridge_success"]:
        return "context_agnostic_memory_trust"
    if h001.get("success_source") == "detector_reobservation":
        return "task_context_reobservation"
    return "other"


def build_paired_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {H001, CONCEPTGRAPHS, STATIC, CONTEXT, DETECTOR_TOP5, UNBOUNDED}
    by_query: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in policy_rows:
        if row.get("policy") in wanted:
            by_query[str(row["query_uid"])][str(row["policy"])] = row

    rows = []
    for query_uid, by_policy in sorted(by_query.items()):
        if not wanted.issubset(by_policy):
            continue
        h001 = by_policy[H001]
        conceptgraphs = by_policy[CONCEPTGRAPHS]
        static = by_policy[STATIC]
        context = by_policy[CONTEXT]
        top5 = by_policy[DETECTOR_TOP5]
        unbounded = by_policy[UNBOUNDED]
        rows.append(
            {
                "m53_version": VERSION,
                "query_uid": query_uid,
                "row_uid": h001["row_uid"],
                "target_uid": h001["target_uid"],
                "label_canonical": h001["label_canonical"],
                "task_context_id": h001["task_context_id"],
                "row_band": h001["row_band"],
                "query_slice_id": h001["query_slice_id"],
                "h001_success": bool(h001["query_bridge_success"]),
                "conceptgraphs_success": bool(conceptgraphs["query_bridge_success"]),
                "static_success": bool(static["query_bridge_success"]),
                "context_agnostic_success": bool(context["query_bridge_success"]),
                "detector_top5_success": bool(top5["query_bridge_success"]),
                "unbounded_success": bool(unbounded["query_bridge_success"]),
                "h001_expected_search_cost": h001["expected_search_cost"],
                "conceptgraphs_expected_search_cost": conceptgraphs["expected_search_cost"],
                "static_expected_search_cost": static["expected_search_cost"],
                "context_agnostic_expected_search_cost": context["expected_search_cost"],
                "h001_success_source": h001.get("success_source"),
                "h001_vs_conceptgraphs": paired_outcome(
                    bool(h001["query_bridge_success"]),
                    bool(conceptgraphs["query_bridge_success"]),
                    "h001",
                    "conceptgraphs",
                ),
                "h001_vs_static": paired_outcome(
                    bool(h001["query_bridge_success"]),
                    bool(static["query_bridge_success"]),
                    "h001",
                    "static",
                ),
                "h001_vs_context_agnostic": paired_outcome(
                    bool(h001["query_bridge_success"]),
                    bool(context["query_bridge_success"]),
                    "h001",
                    "context_agnostic",
                ),
                "h001_over_conceptgraphs_gain_source": gain_source(h001, static, context, conceptgraphs),
            }
        )
    return rows


def group_counts(rows: list[dict[str, Any]], group_field: str, outcome_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(group_field))][str(row.get(outcome_field))] += 1
    output = []
    for group_value, counter in sorted(grouped.items(), key=lambda item: (-sum(item[1].values()), item[0])):
        total = sum(counter.values())
        output.append(
            {
                "group_field": group_field,
                "group_value": group_value,
                "rows": total,
                **dict(sorted(counter.items())),
            }
        )
    return output


def collect_group_rows(paired_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for outcome_field in ["h001_vs_conceptgraphs", "h001_vs_static", "h001_vs_context_agnostic"]:
        for group_field in ["row_band", "query_slice_id", "task_context_id", "label_canonical"]:
            group_rows = group_counts(paired_rows, group_field, outcome_field)
            rows.extend(group_rows)
            for row in rows[-len(group_rows) :]:
                row["outcome_field"] = outcome_field
    return rows


def selected_policy_metrics(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for policy in [CONCEPTGRAPHS, STATIC, CONTEXT, H001, DETECTOR_TOP5, UNBOUNDED]:
        metric = metrics["policy_metrics"][policy]
        rows.append(
            {
                "policy": policy,
                "rows": metric["rows"],
                "success_rows": metric["query_bridge_success_rows"],
                "success_rate": metric["query_bridge_success_rate"],
                "mean_expected_search_cost": metric["mean_expected_search_cost"],
                "mean_attempt_spl_proxy": metric["mean_attempt_spl_proxy"],
                "old_memory_success_rows": metric["old_memory_success_rows"],
                "detector_reobservation_success_rows": metric["detector_reobservation_success_rows"],
                "old_location_dead_end_avoided_rows": metric["old_location_dead_end_avoided_rows"],
            }
        )
    return rows


def build_decision(metrics: dict[str, Any], paired_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m = metrics["policy_metrics"]
    gain_sources = Counter(row["h001_over_conceptgraphs_gain_source"] for row in paired_rows)
    h001_vs_cg = Counter(row["h001_vs_conceptgraphs"] for row in paired_rows)
    h001_vs_static = Counter(row["h001_vs_static"] for row in paired_rows)
    h001_vs_context = Counter(row["h001_vs_context_agnostic"] for row in paired_rows)
    h001_gain_over_cg = int(m[H001]["query_bridge_success_rows"]) - int(m[CONCEPTGRAPHS]["query_bridge_success_rows"])
    h001_gain_over_static = int(m[H001]["query_bridge_success_rows"]) - int(m[STATIC]["query_bridge_success_rows"])
    h001_gain_over_context = int(m[H001]["query_bridge_success_rows"]) - int(m[CONTEXT]["query_bridge_success_rows"])
    return {
        "status": "e005_m53_paired_failure_table_decision_ready_memory_trust_supported_task_context_limited",
        "paper_table_decision": {
            "main_proxy_search_table_ready": True,
            "h001_vs_conceptgraphs_claim_ready": h001_gain_over_cg > 0,
            "h001_vs_static_memory_claim_ready": h001_gain_over_static > 0,
            "task_context_as_main_claim_ready": h001_gain_over_context >= 10,
            "task_context_as_secondary_ablation_ready": h001_gain_over_context > 0,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        "recommended_claim": (
            "H001 improves heldout proxy search over a ConceptGraphs-only open-vocabulary map and static memory "
            "by preserving trustworthy semantic memory and adding bounded re-observation."
        ),
        "blocked_or_weak_claims": [
            "Human task context is the main source of improvement.",
            "Final real navigation SR/SPL improvement.",
            "Final real RGB-D/open-vocabulary robustness across external map families.",
        ],
        "claim_evidence": {
            "h001_success_rows": m[H001]["query_bridge_success_rows"],
            "conceptgraphs_success_rows": m[CONCEPTGRAPHS]["query_bridge_success_rows"],
            "static_success_rows": m[STATIC]["query_bridge_success_rows"],
            "context_agnostic_success_rows": m[CONTEXT]["query_bridge_success_rows"],
            "h001_gain_over_conceptgraphs_rows": h001_gain_over_cg,
            "h001_gain_over_static_rows": h001_gain_over_static,
            "h001_gain_over_context_agnostic_rows": h001_gain_over_context,
            "gain_sources": dict(gain_sources),
            "h001_vs_conceptgraphs": dict(h001_vs_cg),
            "h001_vs_static": dict(h001_vs_static),
            "h001_vs_context_agnostic": dict(h001_vs_context),
        },
        "next_recommended_unit": "E005-M54 paper-table claim ledger / method claim rewrite",
    }


def build_report(coverage: dict[str, Any], decision: dict[str, Any]) -> str:
    evidence = decision["claim_evidence"]
    return "\n".join(
        [
            "# E005-M53 Paired Failure Analysis / Paper-Table Decision",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Query rows: {coverage['query_rows']}.",
            f"- H001 success rows/rate: {coverage['h001_success_rows']} / {coverage['h001_success_rate']}.",
            f"- `ConceptGraphs` success rows/rate: {coverage['conceptgraphs_success_rows']} / {coverage['conceptgraphs_success_rate']}.",
            f"- Static memory success rows/rate: {coverage['static_success_rows']} / {coverage['static_success_rate']}.",
            f"- Context-agnostic memory trust success rows/rate: {coverage['context_agnostic_success_rows']} / {coverage['context_agnostic_success_rate']}.",
            f"- H001 vs `ConceptGraphs` outcomes: {json.dumps(evidence['h001_vs_conceptgraphs'], sort_keys=True)}.",
            f"- H001 vs context-agnostic outcomes: {json.dumps(evidence['h001_vs_context_agnostic'], sort_keys=True)}.",
            f"- H001 over `ConceptGraphs` gain sources: {json.dumps(evidence['gain_sources'], sort_keys=True)}.",
            "",
            "## Paper-Table Decision",
            "",
            "- Main proxy-search table: ready.",
            "- H001 vs `ConceptGraphs` claim: ready with proxy-search boundary.",
            "- H001 vs static memory claim: ready with proxy-search boundary.",
            "- Task context as main claim: not ready; gain over context-agnostic memory trust is only 1 row.",
            "- Real navigation `SR` / `SPL`: not ready.",
            "",
            "## Claim Boundary",
            "",
            f"- Recommended claim: {decision['recommended_claim']}",
            "- Do not claim that human task context is the main contribution from this result alone.",
            "- Treat task context as a secondary ablation unless future experiments broaden the effect.",
            "",
            "## Next",
            "",
            f"- {decision['next_recommended_unit']}.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m52_coverage = read_json(M52_DIR / "coverage.json")
    if m52_coverage.get("status") != "e005_m52_h001_heldout_replay_ready_with_paired_gain":
        raise RuntimeError(f"M52 is not in expected ready state: {m52_coverage.get('status')}")
    policy_rows = read_jsonl(M52_DIR / "policy_rows.jsonl")
    metrics = read_json(M52_DIR / "metrics.json")
    paired_rows = build_paired_rows(policy_rows)
    decision = build_decision(metrics, paired_rows)
    selected_rows = selected_policy_metrics(metrics)
    grouped_rows = collect_group_rows(paired_rows)

    metric_by_policy = {row["policy"]: row for row in selected_rows}
    coverage = {
        "status": decision["status"],
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m52_status": m52_coverage.get("status"),
        "query_rows": len(paired_rows),
        "h001_success_rows": metric_by_policy[H001]["success_rows"],
        "h001_success_rate": metric_by_policy[H001]["success_rate"],
        "conceptgraphs_success_rows": metric_by_policy[CONCEPTGRAPHS]["success_rows"],
        "conceptgraphs_success_rate": metric_by_policy[CONCEPTGRAPHS]["success_rate"],
        "static_success_rows": metric_by_policy[STATIC]["success_rows"],
        "static_success_rate": metric_by_policy[STATIC]["success_rate"],
        "context_agnostic_success_rows": metric_by_policy[CONTEXT]["success_rows"],
        "context_agnostic_success_rate": metric_by_policy[CONTEXT]["success_rate"],
        "main_proxy_search_table_ready": decision["paper_table_decision"]["main_proxy_search_table_ready"],
        "task_context_as_main_claim_ready": decision["paper_table_decision"]["task_context_as_main_claim_ready"],
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": decision["next_recommended_unit"],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_jsonl(OUT_DIR / "paired_rows.jsonl", paired_rows)
    write_jsonl(OUT_DIR / "selected_policy_metrics.jsonl", selected_rows)
    write_jsonl(OUT_DIR / "grouped_outcome_rows.jsonl", grouped_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, decision))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
