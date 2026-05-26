#!/usr/bin/env python3
"""Decide E005-M76 real-proposal claim boundary and repair route."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M76_real_proposal_claim_boundary_v0"
VERSION = "e005_m76_real_proposal_claim_boundary_v0"

M70_ROOT = EXP_ROOT / "artifacts" / "E005-M70_full_denominator_real_proposal_detector_verification_v0"
M75_ROOT = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"

BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
H001 = "real_task_context_memory_trust_reobserve_v0"
CONTEXT = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC = "real_static_memory_only_v0"
DETECTOR_TASK = "real_detector_task_budget_v0"
DETECTOR_TOP5 = "real_detector_confidence_top5_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def load_detector_batch_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in BATCHES:
        coverage = read_json(M70_ROOT / batch / "coverage.json")
        matching = coverage.get("matching", {})
        line_counts = coverage.get("line_counts", {})
        run_summary = coverage.get("run_summary", {})
        rows.append(
            {
                "batch_id": batch,
                "status": coverage.get("status"),
                "expected_files_ready": coverage.get("expected_files_ready"),
                "expected_file_count": coverage.get("expected_file_count"),
                "prediction_rows": int(line_counts.get("prediction_rows") or 0),
                "pre_cap_candidate_rows": int(line_counts.get("pre_cap_candidate_rows") or 0),
                "matched_target_rows": int(matching.get("matched_target_rows") or 0),
                "scan_eval_target_rows": int(matching.get("scan_eval_target_rows") or 0),
                "scan_target_recall": matching.get("scan_target_recall_smoke"),
                "proposal_precision": matching.get("proposal_precision_smoke"),
                "false_positive_rate": matching.get("false_positive_proposal_rate_smoke"),
                "false_positive_rows": int(matching.get("false_positive_proposal_rows") or 0),
                "mean_centroid_error_m": (matching.get("matched_centroid_error_m") or {}).get("mean"),
                "scanned_frame_count": run_summary.get("scanned_frame_count"),
                "raw_prediction_count": run_summary.get("raw_prediction_count"),
                "selected_candidate_count": run_summary.get("selected_candidate_count"),
            }
        )
    return rows


def detector_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    prediction_rows = sum(int(row["prediction_rows"]) for row in rows)
    pre_cap_rows = sum(int(row["pre_cap_candidate_rows"]) for row in rows)
    matched_targets = sum(int(row["matched_target_rows"]) for row in rows)
    target_rows = sum(int(row["scan_eval_target_rows"]) for row in rows)
    false_positive_rows = sum(int(row["false_positive_rows"]) for row in rows)
    return {
        "batches": len(rows),
        "prediction_rows": prediction_rows,
        "pre_cap_candidate_rows": pre_cap_rows,
        "matched_target_rows": matched_targets,
        "scan_eval_target_rows": target_rows,
        "scan_target_recall": safe_rate(matched_targets, target_rows),
        "proposal_precision": safe_rate(matched_targets, prediction_rows),
        "false_positive_rows": false_positive_rows,
        "false_positive_rate": safe_rate(false_positive_rows, prediction_rows),
        "mean_batch_centroid_error_m": safe_mean(
            [float(row["mean_centroid_error_m"]) for row in rows if row.get("mean_centroid_error_m") is not None]
        ),
        "all_batches_ready": all(row["status"] == "e005_m70_real_proposal_detector_batch_ready_with_false_positive_load" for row in rows),
    }


def summarize_group(policy_rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows:
        grouped[(str(row["policy"]), str(row.get(field)))] .append(row)
    rows: list[dict[str, Any]] = []
    for (policy, value), items in sorted(grouped.items()):
        success = sum(1 for row in items if bool(row.get("query_bridge_success")))
        rows.append(
            {
                "group_field": field,
                "group_value": value,
                "policy": policy,
                "rows": len(items),
                "success_rows": success,
                "success_rate": safe_rate(success, len(items)),
                "target_detected_rows": sum(1 for row in items if bool(row.get("target_detected"))),
                "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in items]),
                "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in items]),
            }
        )
    return rows


def pairwise_boundary_rows(failure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("failure_class")) for row in failure_rows)
    by_slice = Counter(str(row.get("query_slice_id")) for row in failure_rows)
    by_label = Counter(str(row.get("label_canonical")) for row in failure_rows)
    rows: list[dict[str, Any]] = []
    for failure_class, count in sorted(counts.items()):
        rows.append(
            {
                "record_type": "failure_class_count",
                "key": failure_class,
                "rows": count,
                "rate": safe_rate(count, len(failure_rows)),
            }
        )
    for query_slice, count in sorted(by_slice.items()):
        rows.append(
            {
                "record_type": "query_slice_count",
                "key": query_slice,
                "rows": count,
                "rate": safe_rate(count, len(failure_rows)),
            }
        )
    for label, count in by_label.most_common(15):
        rows.append(
            {
                "record_type": "label_count_top15",
                "key": label,
                "rows": count,
                "rate": safe_rate(count, len(failure_rows)),
            }
        )
    return rows


def repair_options(
    coverage: dict[str, Any],
    query_summary: dict[str, Any],
    detector: dict[str, Any],
    m75_decision: dict[str, Any],
) -> list[dict[str, Any]]:
    h001_vs_context = m75_decision.get("delta_vs_context_agnostic_memory_trust") or {}
    return [
        {
            "route_id": "include_m75_as_diagnostic_table",
            "rank": 1,
            "selected": True,
            "goal": "Use M75 as a real-proposal diagnostic table with explicit claim boundary.",
            "why": [
                "All three heldout batches are converted.",
                "H001 beats detector-only, static memory, and `ConceptGraphs` same-batch on the same 195-row denominator.",
                "The table exposes detector recall and false-positive bottlenecks rather than hiding them.",
            ],
            "burden": "low",
            "next_unit": "Update paper/report tables and keep final robustness blocked.",
        },
        {
            "route_id": "offline_pre_cap_precision_repair_design",
            "rank": 2,
            "selected": True,
            "goal": "Design an offline replay over existing pre-cap candidate pools before launching another detector run.",
            "why": [
                f"Aggregate proposal precision is {detector['proposal_precision']}, and false-positive rate is {detector['false_positive_rate']}.",
                f"Mean false positives before target is {query_summary['mean_false_positive_before_target_when_detected']}.",
                "Existing pre-cap pools can test ranking/suppression ideas without a new long-running Docker job.",
            ],
            "burden": "medium",
            "next_unit": "E005-M77 offline detector/prompt repair design.",
        },
        {
            "route_id": "prompt_label_recall_repair",
            "rank": 3,
            "selected": False,
            "goal": "Add synonym/label prompt repair only after offline failure rows show recall is the dominant recoverable blocker.",
            "why": [
                f"Query target detection is {coverage['query_target_detected_rate']}, below a strong final robustness threshold.",
                "Recall-miss rows cannot be recovered by reranking if the target never appears in proposals.",
            ],
            "burden": "medium_high",
            "next_unit": "Run only after E005-M77 identifies prompt/label recoverability.",
        },
        {
            "route_id": "external_3d_proposal_baseline",
            "rank": 4,
            "selected": False,
            "goal": "Revisit `OpenMask3D`, `HOV-SG`, or stronger `ConceptGraphs` proposal paths as external proposal baselines.",
            "why": [
                "Useful for top-tier robustness pressure.",
                "Too heavy to launch before the current detector failure modes are isolated.",
            ],
            "burden": "high",
            "next_unit": "Later external proposal baseline feasibility.",
        },
        {
            "route_id": "human_intent_main_claim_upgrade",
            "rank": 5,
            "selected": False,
            "goal": "Promote human intent only with a dedicated context-sensitive utility benchmark.",
            "why": [
                f"H001 vs context-agnostic success delta is {h001_vs_context.get('success_rows_delta')} row.",
                f"H001 ExpectedSearchCost delta vs context-agnostic is {h001_vs_context.get('mean_expected_search_cost_delta')}.",
            ],
            "burden": "medium_high",
            "next_unit": "Optional E006, not the immediate E005 path.",
        },
    ]


def build_decision(
    coverage: dict[str, Any],
    query_summary: dict[str, Any],
    policy_metrics: dict[str, dict[str, Any]],
    detector: dict[str, Any],
    m75_decision: dict[str, Any],
) -> dict[str, Any]:
    h001 = policy_metrics[H001]
    context = policy_metrics[CONTEXT]
    static = policy_metrics[STATIC]
    top5 = policy_metrics[DETECTOR_TOP5]
    task = policy_metrics[DETECTOR_TASK]
    cg = policy_metrics[CONCEPTGRAPHS]

    h001_vs_context_success = int(h001["query_bridge_success_rows"]) - int(context["query_bridge_success_rows"])
    h001_vs_context_cost = round(float(h001["mean_expected_search_cost"]) - float(context["mean_expected_search_cost"]), 6)

    gates = {
        "m75_full_aggregate_ready": coverage.get("status") == "e005_m75_real_proposal_aggregate_ready_with_claim_boundary",
        "detector_batches_ready": detector["all_batches_ready"],
        "diagnostic_table_ready": bool(
            coverage.get("status") == "e005_m75_real_proposal_aggregate_ready_with_claim_boundary"
            and detector["all_batches_ready"]
            and int(h001["query_bridge_success_rows"]) > int(cg["query_bridge_success_rows"])
            and int(h001["query_bridge_success_rows"]) > int(static["query_bridge_success_rows"])
            and int(h001["query_bridge_success_rows"]) > int(top5["query_bridge_success_rows"])
            and int(h001["query_bridge_success_rows"]) > int(task["query_bridge_success_rows"])
        ),
        "detector_prompt_repair_needed_before_final_robustness": bool(
            float(query_summary["query_target_detected_rate"]) < 0.80
            or float(detector["proposal_precision"]) < 0.10
            or float(policy_metrics[DETECTOR_TOP5]["query_bridge_success_rate"]) < 0.35
            or float(query_summary["mean_false_positive_before_target_when_detected"]) > 5.0
        ),
        "human_intent_main_claim_ready": bool(h001_vs_context_success >= 10 and h001_vs_context_cost <= 0.0),
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
    }

    if not gates["diagnostic_table_ready"]:
        selected = "repair_before_paper_table_use"
        next_unit = "E005-M77 detector/prompt repair design before table use"
        rationale = "The aggregate is not strong enough even as a diagnostic paper table."
    elif gates["detector_prompt_repair_needed_before_final_robustness"]:
        selected = "include_diagnostic_table_then_offline_detector_prompt_repair"
        next_unit = "E005-M77 offline detector/prompt repair design"
        rationale = "M75 is useful as a diagnostic table, but detector recall/precision and false-positive load block final robustness claims."
    else:
        selected = "include_diagnostic_table_without_immediate_detector_repair"
        next_unit = "E006 or E007 claim expansion decision"
        rationale = "M75 is clean enough for diagnostic use; remaining blocked claims are human-context and navigation claims."

    return {
        "selected_next_route": selected,
        "rationale": rationale,
        "next_recommended_unit": next_unit,
        "gates": gates,
        "paper_table_action": {
            "include_m75_real_proposal_table": gates["diagnostic_table_ready"],
            "table_role": "diagnostic_real_proposal_search_table",
            "final_robustness_wording_allowed": False,
            "human_intent_main_wording_allowed": gates["human_intent_main_claim_ready"],
            "navigation_sr_spl_wording_allowed": False,
        },
        "key_deltas": {
            "h001_minus_conceptgraphs_success_rows": int(h001["query_bridge_success_rows"]) - int(cg["query_bridge_success_rows"]),
            "h001_minus_detector_top5_success_rows": int(h001["query_bridge_success_rows"]) - int(top5["query_bridge_success_rows"]),
            "h001_minus_detector_task_budget_success_rows": int(h001["query_bridge_success_rows"]) - int(task["query_bridge_success_rows"]),
            "h001_minus_static_success_rows": int(h001["query_bridge_success_rows"]) - int(static["query_bridge_success_rows"]),
            "h001_minus_context_agnostic_success_rows": h001_vs_context_success,
            "h001_minus_context_agnostic_expected_search_cost": h001_vs_context_cost,
        },
        "blocked_claims": {
            "final_real_rgbd_open_vocab_robustness": "blocked_by_detector_recall_precision_false_positive_load_and_no_external_proposal_baseline",
            "deployable_search_policy": "blocked_by_diagnostic_policy_status_and_no_downstream_execution",
            "real_navigation_sr_spl": "blocked_by_no_simulator_navmesh_or_trajectory_execution",
            "human_intent_main_claim": "blocked_by_one_row_gain_and_worse_expected_search_cost_vs_context_agnostic",
        },
        "m75_selected_next_route": m75_decision.get("selected_next_route"),
    }


def claim_rows(
    decision: dict[str, Any],
    coverage: dict[str, Any],
    query_summary: dict[str, Any],
    detector: dict[str, Any],
) -> list[dict[str, Any]]:
    deltas = decision["key_deltas"]
    return [
        {
            "claim_id": "C-M76-001",
            "claim_type": "allowed_diagnostic",
            "claim": "M75 can be used as a full-denominator real RGB-D/open-vocabulary proposal diagnostic table.",
            "status": "ready_with_boundary",
            "evidence": {
                "query_rows": coverage["query_rows"],
                "target_detected_rows": coverage["query_target_detected_rows"],
                "h001_success_rows": coverage["h001_success_rows"],
                "conceptgraphs_success_rows": coverage["conceptgraphs_same_batch_success_rows"],
                "detector_top5_success_rows": coverage["real_detector_top5_success_rows"],
            },
            "allowed_wording": "On the full real-proposal diagnostic denominator, H001 improves query success over detector-only and `ConceptGraphs` same-batch retrieval.",
            "forbidden_wording": "This proves final real RGB-D/open-vocabulary robustness.",
        },
        {
            "claim_id": "C-M76-002",
            "claim_type": "blocked",
            "claim": "Final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "evidence": {
                "query_target_detected_rate": coverage["query_target_detected_rate"],
                "proposal_precision": detector["proposal_precision"],
                "mean_false_positive_before_target": query_summary["mean_false_positive_before_target_when_detected"],
            },
            "allowed_wording": "The current detector route exposes proposal recall and false-positive bottlenecks.",
            "forbidden_wording": "The current detector route is robust enough for final paper claims.",
        },
        {
            "claim_id": "C-M76-003",
            "claim_type": "blocked",
            "claim": "Human intent as a main contribution.",
            "status": "blocked",
            "evidence": {
                "h001_minus_context_success_rows": deltas["h001_minus_context_agnostic_success_rows"],
                "h001_minus_context_expected_search_cost": deltas["h001_minus_context_agnostic_expected_search_cost"],
            },
            "allowed_wording": "Structured task context remains a secondary memory-trust condition.",
            "forbidden_wording": "H001's main gain comes from human intent understanding.",
        },
        {
            "claim_id": "C-M76-004",
            "claim_type": "blocked",
            "claim": "Real navigation `SR` / `SPL` improvement.",
            "status": "blocked",
            "evidence": {
                "metrics_available": ["ExpectedSearchCost", "AttemptSPL"],
                "simulator_or_navmesh_ready": False,
            },
            "allowed_wording": "Navigation evidence is still a query-level proxy bridge.",
            "forbidden_wording": "The method improves real navigation `SR` or `SPL`.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    query_summary: dict[str, Any],
    policy_metrics: dict[str, dict[str, Any]],
    detector: dict[str, Any],
    decision: dict[str, Any],
    repairs: list[dict[str, Any]],
) -> str:
    h001 = policy_metrics[H001]
    context = policy_metrics[CONTEXT]
    static = policy_metrics[STATIC]
    top5 = policy_metrics[DETECTOR_TOP5]
    task = policy_metrics[DETECTOR_TASK]
    cg = policy_metrics[CONCEPTGRAPHS]
    selected_repairs = [row for row in repairs if row["selected"]]
    lines = [
        "# E005-M76 Real Proposal Claim Boundary",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Query rows: {coverage['query_rows']}.",
        f"- Target detected: {coverage['query_target_detected_rows']} / {coverage['query_rows']} = {coverage['query_target_detected_rate']}.",
        f"- Mean target rank when detected: {query_summary['mean_target_rank_when_detected']}.",
        f"- Mean false positives before target: {query_summary['mean_false_positive_before_target_when_detected']}.",
        f"- Detector aggregate precision: {detector['proposal_precision']} over {detector['prediction_rows']} selected proposals.",
        f"- Detector aggregate scan-target recall: {detector['scan_target_recall']} over {detector['scan_eval_target_rows']} target rows.",
        f"- H001: {h001['query_bridge_success_rows']} / {h001['rows']} = {h001['query_bridge_success_rate']}.",
        f"- Context-agnostic memory trust: {context['query_bridge_success_rows']} / {context['rows']} = {context['query_bridge_success_rate']}.",
        f"- Static memory: {static['query_bridge_success_rows']} / {static['rows']} = {static['query_bridge_success_rate']}.",
        f"- `ConceptGraphs` same-batch: {cg['query_bridge_success_rows']} / {cg['rows']} = {cg['query_bridge_success_rate']}.",
        f"- Detector task-budget: {task['query_bridge_success_rows']} / {task['rows']} = {task['query_bridge_success_rate']}.",
        f"- Detector top5: {top5['query_bridge_success_rows']} / {top5['rows']} = {top5['query_bridge_success_rate']}.",
        "",
        "## Decision",
        "",
        f"- Selected route: `{decision['selected_next_route']}`.",
        f"- Next unit: {decision['next_recommended_unit']}.",
        f"- Rationale: {decision['rationale']}",
        "",
        "## Claim Boundary",
        "",
        "- M75 is table-ready only as a diagnostic real-proposal search table.",
        "- Final real RGB-D/open-vocabulary robustness remains blocked.",
        "- Real navigation `SR` / `SPL` remains blocked.",
        "- Human intent remains secondary because H001 gains only 1 success row over context-agnostic memory trust and has higher mean `ExpectedSearchCost`.",
        "",
        "## Repair Route",
        "",
        "| Rank | Route | Selected | Burden | Next |",
        "| ---: | --- | --- | --- | --- |",
        *[
            f"| {row['rank']} | `{row['route_id']}` | {str(row['selected']).lower()} | {row['burden']} | {row['next_unit']} |"
            for row in repairs
        ],
        "",
        "## Agent Inference",
        "",
        "- The useful result is that H001 survives the full 195-row real-proposal diagnostic denominator against detector-only and `ConceptGraphs` same-batch rows.",
        "- The weak result is that this is still mostly a memory-decision diagnostic, not a final perception robustness or navigation result.",
        "- The next low-risk move is an offline repair design over existing pre-cap candidate pools before any new long detector run.",
        "",
        "## Selected Immediate Actions",
        "",
        *[f"- {row['next_unit']}" for row in selected_repairs],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    m75_coverage = read_json(M75_ROOT / "coverage.json")
    query_summary = read_json(M75_ROOT / "query_summary.json")
    policy_metrics = read_json(M75_ROOT / "policy_metrics.json")
    m75_decision = read_json(M75_ROOT / "route_decision.json")
    policy_rows = read_jsonl(M75_ROOT / "policy_rows.jsonl")
    failure_rows = read_jsonl(M75_ROOT / "failure_rows.jsonl")

    if m75_coverage.get("status") != "e005_m75_real_proposal_aggregate_ready_with_claim_boundary":
        raise RuntimeError("M75 full aggregate is not ready")
    for policy in [H001, CONTEXT, STATIC, DETECTOR_TASK, DETECTOR_TOP5, CONCEPTGRAPHS]:
        if policy not in policy_metrics:
            raise RuntimeError(f"missing policy metrics: {policy}")

    detector_batch_rows = load_detector_batch_rows()
    detector_summary = detector_aggregate(detector_batch_rows)
    decision = build_decision(m75_coverage, query_summary, policy_metrics, detector_summary, m75_decision)
    repairs = repair_options(m75_coverage, query_summary, detector_summary, m75_decision)
    claims = claim_rows(decision, m75_coverage, query_summary, detector_summary)
    group_rows = (
        summarize_group(policy_rows, "batch_id")
        + summarize_group(policy_rows, "query_slice_id")
        + summarize_group(policy_rows, "task_context_id")
    )
    boundary_rows = pairwise_boundary_rows(failure_rows)

    coverage = {
        "status": "e005_m76_real_proposal_claim_boundary_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m75_status": m75_coverage.get("status"),
        "query_rows": m75_coverage["query_rows"],
        "query_target_detected_rows": m75_coverage["query_target_detected_rows"],
        "query_target_detected_rate": m75_coverage["query_target_detected_rate"],
        "h001_success_rows": m75_coverage["h001_success_rows"],
        "context_agnostic_success_rows": m75_coverage["context_agnostic_success_rows"],
        "conceptgraphs_same_batch_success_rows": m75_coverage["conceptgraphs_same_batch_success_rows"],
        "real_detector_task_budget_success_rows": m75_coverage["real_detector_task_budget_success_rows"],
        "real_detector_top5_success_rows": m75_coverage["real_detector_top5_success_rows"],
        "mean_false_positive_before_target_when_detected": query_summary["mean_false_positive_before_target_when_detected"],
        "detector_proposal_precision": detector_summary["proposal_precision"],
        "detector_scan_target_recall": detector_summary["scan_target_recall"],
        "diagnostic_table_ready": decision["gates"]["diagnostic_table_ready"],
        "detector_prompt_repair_needed_before_final_robustness": decision["gates"][
            "detector_prompt_repair_needed_before_final_robustness"
        ],
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "human_intent_main_claim_ready": decision["gates"]["human_intent_main_claim_ready"],
        "real_navigation_sr_spl_claim_ready": False,
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "route_decision.json", decision)
    write_json(OUT_DIR / "detector_summary.json", detector_summary)
    write_jsonl(OUT_DIR / "detector_batch_rows.jsonl", detector_batch_rows)
    write_jsonl(OUT_DIR / "repair_options.jsonl", repairs)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claims)
    write_jsonl(OUT_DIR / "group_summary_rows.jsonl", group_rows)
    write_csv(OUT_DIR / "group_summary_rows.csv", group_rows)
    write_jsonl(OUT_DIR / "failure_boundary_summary.jsonl", boundary_rows)
    write_text(OUT_DIR / "report.md", build_report(m75_coverage, query_summary, policy_metrics, detector_summary, decision, repairs))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
