#!/usr/bin/env python3
"""Aggregate E005 real-proposal query metrics across heldout batches."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
DEFAULT_M71_ROOT = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
VERSION = "e005_m75_real_proposal_aggregate_route_v0"

DEFAULT_BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
H001_POLICY = "real_task_context_memory_trust_reobserve_v0"
CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC_POLICY = "real_static_memory_only_v0"
DETECTOR_TASK_POLICY = "real_detector_task_budget_v0"
DETECTOR_TOP5_POLICY = "real_detector_confidence_top5_v0"
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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def summarize_policy_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["policy"])].append(row)

    summary: dict[str, dict[str, Any]] = {}
    for policy, policy_rows in sorted(grouped.items()):
        row_count = len(policy_rows)
        success_rows = sum(1 for row in policy_rows if bool(row.get("query_bridge_success")))
        target_detected_rows = sum(1 for row in policy_rows if bool(row.get("target_detected")))
        old_dead_end_rows = [row for row in policy_rows if row.get("old_location_dead_end_expected") is not None]
        old_dead_end_expected = sum(1 for row in old_dead_end_rows if bool(row.get("old_location_dead_end_expected")))
        old_dead_end_avoided = sum(1 for row in old_dead_end_rows if bool(row.get("old_location_dead_end_avoided")))
        summary[policy] = {
            "rows": row_count,
            "query_bridge_success_rows": success_rows,
            "query_bridge_success_rate": safe_rate(success_rows, row_count),
            "target_detected_rows": target_detected_rows,
            "target_detected_rate": safe_rate(target_detected_rows, row_count),
            "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in policy_rows]),
            "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in policy_rows]),
            "mean_returned_location_count": safe_mean([float(row["returned_location_count"]) for row in policy_rows]),
            "old_location_dead_end_expected_rows": old_dead_end_expected,
            "old_location_dead_end_avoided_rows": old_dead_end_avoided,
            "old_location_dead_end_avoided_rate": safe_rate(old_dead_end_avoided, old_dead_end_expected),
        }
    return summary


def summarize_query_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_detected = sum(1 for row in rows if bool(row.get("query_target_detected")))
    unique_targets = {str(row["target_uid"]) for row in rows}
    unique_detected = {str(row["target_uid"]) for row in rows if bool(row.get("query_target_detected"))}
    return {
        "query_rows": len(rows),
        "query_target_detected_rows": target_detected,
        "query_target_detected_rate": safe_rate(target_detected, len(rows)),
        "unique_target_uids": len(unique_targets),
        "unique_target_detected_uids": len(unique_detected),
        "unique_target_detected_rate": safe_rate(len(unique_detected), len(unique_targets)),
        "mean_target_rank_when_detected": safe_mean(
            [
                int(row["query_target_rank_by_real_detector_confidence"])
                for row in rows
                if row.get("query_target_rank_by_real_detector_confidence") is not None
            ]
        ),
        "mean_false_positive_before_target_when_detected": safe_mean(
            [
                int(row["false_positive_before_target_count"])
                for row in rows
                if row.get("false_positive_before_target_count") is not None
            ]
        ),
        "mean_same_label_real_proposals_per_query": safe_mean(
            [int(row["same_label_real_proposal_count"]) for row in rows]
        ),
        "query_rows_by_batch": dict(Counter(str(row["batch_id"]) for row in rows)),
        "query_rows_by_label": dict(Counter(str(row["label_canonical"]) for row in rows)),
        "query_rows_by_slice": dict(Counter(str(row["query_slice_id"]) for row in rows)),
        "query_rows_by_task_context": dict(Counter(str(row["task_context_id"]) for row in rows)),
    }


def metric_delta(metrics: dict[str, dict[str, Any]], left: str, right: str) -> dict[str, Any] | None:
    if left not in metrics or right not in metrics:
        return None
    a = metrics[left]
    b = metrics[right]
    return {
        "success_rows_delta": int(a["query_bridge_success_rows"]) - int(b["query_bridge_success_rows"]),
        "success_rate_delta": round(float(a["query_bridge_success_rate"]) - float(b["query_bridge_success_rate"]), 6),
        "mean_expected_search_cost_delta": round(
            float(a["mean_expected_search_cost"]) - float(b["mean_expected_search_cost"]), 6
        ),
        "mean_attempt_spl_proxy_delta": round(
            float(a["mean_attempt_spl_proxy"]) - float(b["mean_attempt_spl_proxy"]), 6
        ),
    }


def load_batch(root: Path, batch_id: str) -> dict[str, Any]:
    batch_dir = root / batch_id
    coverage = read_json(batch_dir / "coverage.json")
    metrics = read_json(batch_dir / "metrics.json")
    route_decision = read_json(batch_dir / "route_decision.json")
    query_rows = read_jsonl(batch_dir / "query_bridge_rows.jsonl")
    policy_rows = read_jsonl(batch_dir / "policy_rows.jsonl")
    failure_rows = read_jsonl(batch_dir / "failure_rows.jsonl")
    ready = bool(
        coverage
        and coverage.get("status")
        in {
            "e005_m71_real_proposal_query_metric_ready_with_false_positive_boundary",
            "e005_m71_real_proposal_query_metric_ready_target_detection_weak",
        }
        and query_rows
        and policy_rows
    )
    return {
        "batch_id": batch_id,
        "ready": ready,
        "coverage": coverage,
        "metrics": metrics,
        "route_decision": route_decision,
        "query_rows": query_rows,
        "policy_rows": policy_rows,
        "failure_rows": failure_rows,
    }


def build_decision(
    *,
    requested_batches: list[str],
    ready_batches: list[str],
    query_summary: dict[str, Any],
    policy_metrics: dict[str, dict[str, Any]],
    failure_counts: dict[str, int],
) -> dict[str, Any]:
    missing_batches = [batch for batch in requested_batches if batch not in ready_batches]
    h001 = policy_metrics.get(H001_POLICY, {})
    context = policy_metrics.get(CONTEXT_AGNOSTIC_POLICY, {})
    gates = {
        "all_requested_batches_ready": not missing_batches,
        "aggregate_target_detection_sufficient_for_robustness_diagnostic": float(
            query_summary.get("query_target_detected_rate") or 0.0
        )
        >= 0.70,
        "h001_beats_real_detector_task_budget": bool(
            h001 and int(h001["query_bridge_success_rows"]) > int(policy_metrics[DETECTOR_TASK_POLICY]["query_bridge_success_rows"])
        ),
        "h001_beats_real_detector_top5": bool(
            h001 and int(h001["query_bridge_success_rows"]) > int(policy_metrics[DETECTOR_TOP5_POLICY]["query_bridge_success_rows"])
        ),
        "h001_beats_static_memory": bool(
            h001 and int(h001["query_bridge_success_rows"]) > int(policy_metrics[STATIC_POLICY]["query_bridge_success_rows"])
        ),
        "h001_beats_conceptgraphs_same_batch": bool(
            h001 and int(h001["query_bridge_success_rows"]) > int(policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rows"])
        ),
        "h001_beats_context_agnostic_memory_trust": bool(
            h001
            and context
            and (
                int(h001["query_bridge_success_rows"]) > int(context["query_bridge_success_rows"])
                or (
                    int(h001["query_bridge_success_rows"]) == int(context["query_bridge_success_rows"])
                    and float(h001["mean_expected_search_cost"]) < float(context["mean_expected_search_cost"])
                )
            )
        ),
        "human_intent_main_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
    }

    if missing_batches:
        selected = "wait_for_remaining_batch_verification"
        rationale = "At least one real-proposal heldout batch is still missing; aggregate claim is not available."
    elif not gates["aggregate_target_detection_sufficient_for_robustness_diagnostic"]:
        selected = "repair_detector_or_prompt_route_before_real_robustness_claim"
        rationale = "Aggregate target detection is below the diagnostic threshold, so the bottleneck is detector/prompt coverage."
    elif not gates["h001_beats_context_agnostic_memory_trust"]:
        selected = "aggregate_diagnostic_ready_memory_trust_supported_task_context_not_supported"
        rationale = "H001 beats detector-only and external map rows, but not context-agnostic memory trust."
    else:
        selected = "aggregate_diagnostic_ready_review_claim_boundary"
        rationale = "The aggregate is ready for review, but final robustness and navigation claims still require stronger downstream evidence."

    return {
        "selected_next_route": selected,
        "rationale": rationale,
        "ready_batches": ready_batches,
        "missing_batches": missing_batches,
        "gates": gates,
        "failure_class_counts": failure_counts,
        "delta_vs_real_detector_task_budget": metric_delta(policy_metrics, H001_POLICY, DETECTOR_TASK_POLICY),
        "delta_vs_real_detector_top5": metric_delta(policy_metrics, H001_POLICY, DETECTOR_TOP5_POLICY),
        "delta_vs_static_memory": metric_delta(policy_metrics, H001_POLICY, STATIC_POLICY),
        "delta_vs_context_agnostic_memory_trust": metric_delta(policy_metrics, H001_POLICY, CONTEXT_AGNOSTIC_POLICY),
        "delta_vs_conceptgraphs_same_batch": metric_delta(policy_metrics, H001_POLICY, CONCEPTGRAPHS_POLICY),
        "claim_boundary": {
            "aggregate_query_metric_ready": not missing_batches,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "human_intent_main_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "next_recommended_unit": "E005-M73 heldout_b03 verification" if missing_batches else "E005-M76 detector/prompt repair or paper-table boundary decision",
    }


def build_report(coverage: dict[str, Any], query_summary: dict[str, Any], policy_metrics: dict[str, Any], decision: dict[str, Any]) -> str:
    h001 = policy_metrics.get(H001_POLICY, {})
    context = policy_metrics.get(CONTEXT_AGNOSTIC_POLICY, {})
    detector = policy_metrics.get(DETECTOR_TASK_POLICY, {})
    top5 = policy_metrics.get(DETECTOR_TOP5_POLICY, {})
    cg = policy_metrics.get(CONCEPTGRAPHS_POLICY, {})
    return "\n".join(
        [
            "# E005-M75 Real Proposal Aggregate Route",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Requested batches: {coverage['requested_batches']}.",
            f"- Ready batches: {coverage['ready_batches']}.",
            f"- Missing batches: {coverage['missing_batches']}.",
            f"- Query rows: {query_summary['query_rows']}.",
            f"- Query target detected rows/rate: {query_summary['query_target_detected_rows']} / {query_summary['query_target_detected_rate']}.",
            f"- Mean target rank when detected: {query_summary['mean_target_rank_when_detected']}.",
            f"- Mean false positives before target when detected: {query_summary['mean_false_positive_before_target_when_detected']}.",
            f"- `real_detector_task_budget_v0`: {detector.get('query_bridge_success_rows')} / {detector.get('query_bridge_success_rate')}.",
            f"- `real_detector_confidence_top5_v0`: {top5.get('query_bridge_success_rows')} / {top5.get('query_bridge_success_rate')}.",
            f"- `real_task_context_memory_trust_reobserve_v0`: {h001.get('query_bridge_success_rows')} / {h001.get('query_bridge_success_rate')}.",
            f"- `real_context_agnostic_memory_trust_reobserve_v0`: {context.get('query_bridge_success_rows')} / {context.get('query_bridge_success_rate')}.",
            f"- `ConceptGraphs` same-batch strict bbox top5: {cg.get('query_bridge_success_rows')} / {cg.get('query_bridge_success_rate')}.",
            f"- Selected next route: `{decision['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            "- This aggregate does not support final real RGB-D/open-vocabulary robustness.",
            "- This aggregate does not support deployable search policy or real navigation `SR` / `SPL`.",
            "- Human task context remains a secondary ablation until H001 beats context-agnostic memory trust.",
            "",
            "## Agent Inference",
            "",
            f"- {decision['rationale']}",
            "- The aggregate table should separate detector target-recall limits from memory-policy effects.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m71-root", default=DEFAULT_M71_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--batches", nargs="+", default=list(DEFAULT_BATCHES))
    parser.add_argument("--require-all", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested_batches = [str(batch) for batch in args.batches]
    loaded = [load_batch(args.m71_root, batch) for batch in requested_batches]
    ready = [batch for batch in loaded if batch["ready"]]
    ready_batches = [batch["batch_id"] for batch in ready]
    missing_batches = [batch["batch_id"] for batch in loaded if not batch["ready"]]
    if args.require_all and missing_batches:
        raise RuntimeError(f"missing ready batches: {missing_batches}")

    query_rows = [row for batch in ready for row in batch["query_rows"]]
    policy_rows = [row for batch in ready for row in batch["policy_rows"]]
    failure_rows = [row for batch in ready for row in batch["failure_rows"]]
    if not query_rows or not policy_rows:
        raise RuntimeError("no ready query/policy rows found")

    query_summary = summarize_query_rows(query_rows)
    policy_metrics = summarize_policy_rows(policy_rows)
    failure_counts = dict(Counter(str(row["failure_class"]) for row in failure_rows))
    decision = build_decision(
        requested_batches=requested_batches,
        ready_batches=ready_batches,
        query_summary=query_summary,
        policy_metrics=policy_metrics,
        failure_counts=failure_counts,
    )
    status = "e005_m75_real_proposal_aggregate_partial_waiting_remaining_batch"
    if not missing_batches:
        status = "e005_m75_real_proposal_aggregate_ready_with_claim_boundary"

    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "requested_batches": requested_batches,
        "ready_batches": ready_batches,
        "missing_batches": missing_batches,
        "query_rows": query_summary["query_rows"],
        "query_target_detected_rows": query_summary["query_target_detected_rows"],
        "query_target_detected_rate": query_summary["query_target_detected_rate"],
        "h001_success_rows": policy_metrics[H001_POLICY]["query_bridge_success_rows"],
        "h001_success_rate": policy_metrics[H001_POLICY]["query_bridge_success_rate"],
        "context_agnostic_success_rows": policy_metrics[CONTEXT_AGNOSTIC_POLICY]["query_bridge_success_rows"],
        "conceptgraphs_same_batch_success_rows": policy_metrics[CONCEPTGRAPHS_POLICY]["query_bridge_success_rows"],
        "real_detector_task_budget_success_rows": policy_metrics[DETECTOR_TASK_POLICY]["query_bridge_success_rows"],
        "real_detector_top5_success_rows": policy_metrics[DETECTOR_TOP5_POLICY]["query_bridge_success_rows"],
        "selected_next_route": decision["selected_next_route"],
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "human_intent_main_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": decision["next_recommended_unit"],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "query_bridge_rows.jsonl", query_rows)
    write_jsonl(args.out_dir / "policy_rows.jsonl", policy_rows)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "query_summary.json", query_summary)
    write_json(args.out_dir / "policy_metrics.json", policy_metrics)
    write_json(args.out_dir / "route_decision.json", decision)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, query_summary, policy_metrics, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
