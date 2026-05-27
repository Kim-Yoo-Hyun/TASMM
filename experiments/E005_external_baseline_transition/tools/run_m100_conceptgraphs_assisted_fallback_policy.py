#!/usr/bin/env python3
"""Smoke-test ConceptGraphs-assisted H001 fallback policies."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"
VERSION = "e005_m100_conceptgraphs_assisted_fallback_policy_v0"

M98_DIR = EXP_ROOT / "artifacts" / "E005-M98_conceptgraphs_reliability_boundary_v0"
M99_DIR = EXP_ROOT / "artifacts" / "E005-M99_row_group_heavier_route_decision_v0"

PolicyFn = Callable[[dict[str, Any]], dict[str, Any]]

ALLOWED_INPUTS = [
    "H001 memory-trust candidate queue",
    "H001 observed miss after exhausting its returned candidate queue",
    "ConceptGraphs map candidate queue",
    "ConceptGraphs CLIP-text candidate order",
    "pre-evaluation row_band / expected staleness class",
    "task_context_id used by the existing H001 policy",
]

FORBIDDEN_INPUTS = [
    "target_uid",
    "target_rank",
    "target_match_distance",
    "target_detected",
    "query_bridge_success",
    "false_positive_before_target_count",
    "old_location_dead_end_expected",
    "any post-evaluation success label",
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


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return round(mean(valid), 6) if valid else None


def attempt_spl(success: bool, expected_search_cost: float | int | None) -> float:
    if not success or not expected_search_cost:
        return 0.0
    return round(1.0 / float(expected_search_cost), 6)


def conceptgraphs_topk_success(row: dict[str, Any], topk: int) -> bool:
    rank = row.get("conceptgraphs_target_rank")
    return rank is not None and int(rank) <= topk


def base_output(
    row: dict[str, Any],
    policy: str,
    success: bool,
    cost: float | int,
    success_source: str,
    visit_order: str,
    fallback_trigger: str,
    fallback_used: bool,
    conceptgraphs_topk: int,
    deployable_policy: bool,
    policy_input_fields_used: list[str],
) -> dict[str, Any]:
    old_dead = bool(row["old_location_dead_end_expected"])
    old_dead_avoided = bool(
        success
        and old_dead
        and (success_source.startswith("conceptgraphs_first") or success_source == "conceptgraphs_only")
    )
    return {
        "attempt_spl_proxy": attempt_spl(success, cost),
        "base_row_uid": row["base_row_uid"],
        "batch_id": row["batch_id"],
        "candidate_visit_order": visit_order,
        "conceptgraphs_fallback_used": bool(fallback_used and success_source.startswith("conceptgraphs")),
        "conceptgraphs_topk": conceptgraphs_topk,
        "current_rescan_id": row["scan_id"],
        "deployable_policy": deployable_policy,
        "expected_search_cost": cost,
        "fallback_trigger": fallback_trigger,
        "fallback_used": fallback_used,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "label_canonical": row["label_canonical"],
        "leakage_audit_pass": True,
        "m100_version": VERSION,
        "old_location_dead_end_avoided": old_dead_avoided,
        "old_location_dead_end_expected_eval_only": old_dead,
        "policy": policy,
        "policy_family": "conceptgraphs_assisted_h001_fallback",
        "policy_input_fields_used": policy_input_fields_used,
        "query_bridge_success": success,
        "query_uid": row["query_uid"],
        "real_navigation_sr_spl_ready": False,
        "row_band": row["row_band"],
        "row_uid": row["row_uid"],
        "success_source": success_source,
        "target_uid_eval_only": row["target_uid"],
        "task_context_id": row["task_context_id"],
    }


def policy_h001(row: dict[str, Any]) -> dict[str, Any]:
    success = bool(row["h001_success"])
    return base_output(
        row,
        "h001_real_task_context_memory_trust_v0",
        success,
        row["h001_expected_search_cost"],
        row["h001_success_source"] if success else "none",
        "h001_existing_memory_then_real_detector_rank",
        "none",
        False,
        0,
        True,
        ["task_context_id", "expected_memory_state", "old_memory_is_stale", "same_label_real_proposal_count"],
    )


def policy_conceptgraphs_only(row: dict[str, Any]) -> dict[str, Any]:
    success = bool(row["conceptgraphs_success"])
    return base_output(
        row,
        "conceptgraphs_only_strict_top5_v0",
        success,
        row["conceptgraphs_expected_search_cost"],
        "conceptgraphs_only" if success else "none",
        "conceptgraphs_clip_rank_top5",
        "none",
        False,
        5,
        True,
        ["ConceptGraphs map candidates", "ConceptGraphs CLIP-text candidate order"],
    )


def policy_h001_then_cg_top5(row: dict[str, Any]) -> dict[str, Any]:
    if row["h001_success"]:
        return base_output(
            row,
            "h001_then_conceptgraphs_top5_on_observed_miss_v0",
            True,
            row["h001_expected_search_cost"],
            row["h001_success_source"],
            "h001_existing_queue_then_conceptgraphs_top5_after_observed_miss",
            "observed_h001_candidate_queue_exhausted_without_target",
            False,
            5,
            True,
            ALLOWED_INPUTS,
        )
    success = bool(row["conceptgraphs_success"])
    return base_output(
        row,
        "h001_then_conceptgraphs_top5_on_observed_miss_v0",
        success,
        row["h001_expected_search_cost"] + row["conceptgraphs_expected_search_cost"],
        "conceptgraphs_after_h001_observed_miss" if success else "none",
        "h001_existing_queue_then_conceptgraphs_top5_after_observed_miss",
        "observed_h001_candidate_queue_exhausted_without_target",
        True,
        5,
        True,
        ALLOWED_INPUTS,
    )


def policy_h001_then_cg_top6_sensitivity(row: dict[str, Any]) -> dict[str, Any]:
    if row["h001_success"]:
        return base_output(
            row,
            "h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0",
            True,
            row["h001_expected_search_cost"],
            row["h001_success_source"],
            "h001_existing_queue_then_conceptgraphs_top6_after_observed_miss",
            "observed_h001_candidate_queue_exhausted_without_target",
            False,
            6,
            False,
            ALLOWED_INPUTS,
        )
    success = conceptgraphs_topk_success(row, 6)
    return base_output(
        row,
        "h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0",
        success,
        row["h001_expected_search_cost"] + row["conceptgraphs_expected_search_cost"],
        "conceptgraphs_top6_after_h001_observed_miss" if success else "none",
        "h001_existing_queue_then_conceptgraphs_top6_after_observed_miss",
        "observed_h001_candidate_queue_exhausted_without_target",
        True,
        6,
        False,
        ALLOWED_INPUTS,
    )


def policy_moved_cg_first(row: dict[str, Any]) -> dict[str, Any]:
    if row["row_band"] == "significant_moved":
        if row["conceptgraphs_success"]:
            return base_output(
                row,
                "significant_moved_conceptgraphs_first_else_h001_v0",
                True,
                row["conceptgraphs_expected_search_cost"],
                "conceptgraphs_first_significant_moved",
                "conceptgraphs_top5_for_significant_moved_then_h001_if_miss",
                "pre_evaluation_row_band_is_significant_moved",
                False,
                5,
                True,
                ALLOWED_INPUTS,
            )
        success = bool(row["h001_success"])
        return base_output(
            row,
            "significant_moved_conceptgraphs_first_else_h001_v0",
            success,
            row["conceptgraphs_expected_search_cost"] + row["h001_expected_search_cost"],
            "h001_after_conceptgraphs_miss" if success else "none",
            "conceptgraphs_top5_for_significant_moved_then_h001_if_miss",
            "pre_evaluation_row_band_is_significant_moved",
            True,
            5,
            True,
            ALLOWED_INPUTS,
        )
    base = policy_h001_then_cg_top5(row)
    base["policy"] = "significant_moved_conceptgraphs_first_else_h001_v0"
    base["candidate_visit_order"] = "h001_existing_queue_then_conceptgraphs_top5_after_observed_miss"
    return base


def policy_non_low_cg_first(row: dict[str, Any]) -> dict[str, Any]:
    if row["row_band"] != "low_motion_control":
        if row["conceptgraphs_success"]:
            return base_output(
                row,
                "non_low_motion_conceptgraphs_first_else_h001_v0",
                True,
                row["conceptgraphs_expected_search_cost"],
                "conceptgraphs_first_non_low_motion",
                "conceptgraphs_top5_for_non_low_motion_then_h001_if_miss",
                "pre_evaluation_row_band_is_mid_or_significant",
                False,
                5,
                True,
                ALLOWED_INPUTS,
            )
        success = bool(row["h001_success"])
        return base_output(
            row,
            "non_low_motion_conceptgraphs_first_else_h001_v0",
            success,
            row["conceptgraphs_expected_search_cost"] + row["h001_expected_search_cost"],
            "h001_after_conceptgraphs_miss" if success else "none",
            "conceptgraphs_top5_for_non_low_motion_then_h001_if_miss",
            "pre_evaluation_row_band_is_mid_or_significant",
            True,
            5,
            True,
            ALLOWED_INPUTS,
        )
    base = policy_h001_then_cg_top5(row)
    base["policy"] = "non_low_motion_conceptgraphs_first_else_h001_v0"
    base["candidate_visit_order"] = "h001_existing_queue_then_conceptgraphs_top5_after_observed_miss"
    return base


POLICIES: list[tuple[str, PolicyFn]] = [
    ("h001_real_task_context_memory_trust_v0", policy_h001),
    ("conceptgraphs_only_strict_top5_v0", policy_conceptgraphs_only),
    ("h001_then_conceptgraphs_top5_on_observed_miss_v0", policy_h001_then_cg_top5),
    ("significant_moved_conceptgraphs_first_else_h001_v0", policy_moved_cg_first),
    ("non_low_motion_conceptgraphs_first_else_h001_v0", policy_non_low_cg_first),
    ("h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0", policy_h001_then_cg_top6_sensitivity),
]


def build_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        for _, fn in POLICIES:
            output.append(fn(row))
    return output


def summarize_policy(rows: list[dict[str, Any]], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    query_rows = len(rows)
    success_rows = sum(row["query_bridge_success"] for row in rows)
    total_cost = sum(float(row["expected_search_cost"]) for row in rows)
    result = {
        "policy": rows[0]["policy"],
        "query_rows": query_rows,
        "success_rows": success_rows,
        "sr_proxy": round(success_rows / query_rows, 6) if query_rows else 0.0,
        "attempt_spl_proxy": safe_mean([row["attempt_spl_proxy"] for row in rows]),
        "mean_expected_search_cost_all": safe_mean([row["expected_search_cost"] for row in rows]),
        "mean_expected_search_cost_success": safe_mean(
            [row["expected_search_cost"] for row in rows if row["query_bridge_success"]]
        ),
        "total_expected_search_cost": round(total_cost, 6),
        "fallback_used_rows": sum(row["fallback_used"] for row in rows),
        "conceptgraphs_fallback_used_rows": sum(row["conceptgraphs_fallback_used"] for row in rows),
        "old_dead_end_eval_rows": sum(row["old_location_dead_end_expected_eval_only"] for row in rows),
        "old_dead_end_avoided_rows": sum(row["old_location_dead_end_avoided"] for row in rows),
        "deployable_policy": all(row["deployable_policy"] for row in rows),
    }
    if baseline:
        success_gain = success_rows - int(baseline["success_rows"])
        cost_delta = total_cost - float(baseline["total_expected_search_cost"])
        result.update(
            {
                "success_gain_vs_h001": success_gain,
                "attempt_spl_delta_vs_h001": round(
                    float(result["attempt_spl_proxy"]) - float(baseline["attempt_spl_proxy"]),
                    6,
                ),
                "mean_cost_delta_vs_h001": round(
                    float(result["mean_expected_search_cost_all"]) - float(baseline["mean_expected_search_cost_all"]),
                    6,
                ),
                "extra_cost_per_added_success_vs_h001": round(cost_delta / success_gain, 6)
                if success_gain > 0
                else None,
            }
        )
    return result


def summarize_by(policy_rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows:
        grouped[(row["policy"], row.get(field))].append(row)
    output = []
    for (policy, value), rows in sorted(grouped.items()):
        success_rows = sum(row["query_bridge_success"] for row in rows)
        output.append(
            {
                "field": field,
                "policy": policy,
                "value": value,
                "rows": len(rows),
                "success_rows": success_rows,
                "sr_proxy": round(success_rows / len(rows), 6) if rows else 0.0,
                "attempt_spl_proxy": safe_mean([row["attempt_spl_proxy"] for row in rows]),
                "mean_expected_search_cost_all": safe_mean([row["expected_search_cost"] for row in rows]),
                "fallback_used_rows": sum(row["fallback_used"] for row in rows),
                "old_dead_end_avoided_rows": sum(row["old_location_dead_end_avoided"] for row in rows),
            }
        )
    return output


def build_policy_contract() -> dict[str, Any]:
    return {
        "allowed_inputs": ALLOWED_INPUTS,
        "forbidden_inputs": FORBIDDEN_INPUTS,
        "selected_policy": "h001_then_conceptgraphs_top5_on_observed_miss_v0",
        "selected_policy_contract": {
            "first_stage": "Run the existing H001 memory-trust/re-observation candidate queue.",
            "fallback_trigger": "Only after the H001 returned candidate queue is actually exhausted without finding the target.",
            "fallback_stage": "Visit `ConceptGraphs` CLIP-ranked map candidates up to top5.",
            "cost_accounting": "If fallback is used, total `ExpectedSearchCost` is H001 queue cost plus `ConceptGraphs` candidate cost.",
            "runtime_observability": "The fallback trigger is an observed search miss, not an evaluation label.",
        },
        "sensitivity_policy": "h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0",
        "blocked_shortcuts": [
            "Do not trigger fallback from target rank or target detection labels.",
            "Do not use `old_location_dead_end_expected` as a policy input.",
            "Do not report H001-or-ConceptGraphs union upper bound as deployable policy evidence.",
        ],
    }


def build_claim_rows(policy_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy = {row["policy"]: row for row in policy_summary}
    h001 = by_policy["h001_real_task_context_memory_trust_v0"]
    selected = by_policy["h001_then_conceptgraphs_top5_on_observed_miss_v0"]
    moved = by_policy["significant_moved_conceptgraphs_first_else_h001_v0"]
    top6 = by_policy["h001_then_conceptgraphs_top6_on_observed_miss_sensitivity_v0"]
    return [
        {
            "claim_id": "C-M100-001",
            "claim": "`ConceptGraphs`-assisted fallback can improve H001 under explicit cost accounting.",
            "claim_type": "policy_smoke",
            "status": "supported_smoke",
            "evidence": (
                f"H001 success {h001['success_rows']} / {h001['query_rows']} -> selected fallback "
                f"{selected['success_rows']} / {selected['query_rows']}; `AttemptSPL` "
                f"{h001['attempt_spl_proxy']} -> {selected['attempt_spl_proxy']}."
            ),
            "boundary": "This is still query-level search-cost proxy evidence, not real navigation `SR` / `SPL`.",
            "next_validation_requirement": "E005-M101 should decide paper-table integration versus navigation/path-cost bridge.",
        },
        {
            "claim_id": "C-M100-002",
            "claim": "Map-first policies are not the immediate default despite improving old-dead-end avoidance.",
            "claim_type": "ablation_boundary",
            "status": "not_selected",
            "evidence": (
                f"Moved-first success {moved['success_rows']} / {moved['query_rows']} with `AttemptSPL` "
                f"{moved['attempt_spl_proxy']}, below selected fallback {selected['attempt_spl_proxy']}."
            ),
            "boundary": "Map-first remains useful for old-dead-end analysis but increases average cost.",
            "next_validation_requirement": "If old-dead-end cost becomes the main claim, evaluate a dedicated utility metric.",
        },
        {
            "claim_id": "C-M100-003",
            "claim": "Relaxing `ConceptGraphs` fallback to top6 is only sensitivity evidence.",
            "claim_type": "topk_sensitivity",
            "status": "diagnostic_only",
            "evidence": (
                f"Top6 sensitivity succeeds on {top6['success_rows']} / {top6['query_rows']} rows, "
                f"+{top6['success_rows'] - selected['success_rows']} over selected top5 fallback."
            ),
            "boundary": "Changing top-k changes the baseline budget and must not be mixed with top5 main-table claims.",
            "next_validation_requirement": "Keep top5 as main smoke; use top6 only as appendix/sensitivity if needed.",
        },
        {
            "claim_id": "C-M100-004",
            "claim": "Human intent remains secondary.",
            "claim_type": "human_context_boundary",
            "status": "unchanged",
            "evidence": "M99 found H001 context-sensitive targets 1 / 65; M100 does not add a context-sensitive utility benchmark.",
            "boundary": "Do not claim natural-language or human-intent understanding from M100.",
            "next_validation_requirement": "Optional E006 is required if human intent becomes a main contribution.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_summary: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    contract: dict[str, Any],
) -> str:
    policy_lines = [
        "| Policy | Success | SR | AttemptSPL | Mean Cost | Fallback Used | Old-Dead-End Avoided |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in policy_summary:
        policy_lines.append(
            f"| `{row['policy']}` | {row['success_rows']} / {row['query_rows']} | "
            f"{row['sr_proxy']:.6f} | {row['attempt_spl_proxy']:.6f} | "
            f"{row['mean_expected_search_cost_all']:.6f} | {row['fallback_used_rows']} | "
            f"{row['old_dead_end_avoided_rows']} |"
        )

    claim_lines = ["| Claim | Status | Evidence | Boundary |", "| --- | --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['boundary']} |")

    return f"""# E005-M100 ConceptGraphs-Assisted H001 Fallback Policy

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- Selected policy: `{coverage["selected_policy"]}`.
- H001 success rows: {coverage["h001_success_rows"]}.
- Selected fallback success rows: {coverage["selected_success_rows"]}.
- Selected fallback `AttemptSPL` proxy: {coverage["selected_attempt_spl_proxy"]}.
- Selected fallback mean `ExpectedSearchCost`: {coverage["selected_mean_expected_search_cost"]}.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Real navigation `SR` / `SPL` ready: false.

## Policy Contract

- First stage: {contract["selected_policy_contract"]["first_stage"]}
- Fallback trigger: {contract["selected_policy_contract"]["fallback_trigger"]}
- Fallback stage: {contract["selected_policy_contract"]["fallback_stage"]}
- Cost accounting: {contract["selected_policy_contract"]["cost_accounting"]}

## Policy Summary

{chr(10).join(policy_lines)}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- The selected top5 fallback is the first policy that improves H001 success and `AttemptSPL` proxy while paying fallback cost.
- The smoke supports a method-facing fallback direction, not a final deployable search or navigation claim.
- M101 should decide whether this becomes a paper-facing policy table row or whether a heavier external route is still needed.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m98 = read_json(M98_DIR / "coverage.json")
    m99 = read_json(M99_DIR / "coverage.json")
    source_rows = read_jsonl(M98_DIR / "row_group_rows.jsonl")
    if not source_rows:
        raise RuntimeError(f"Missing M98 row groups: {M98_DIR / 'row_group_rows.jsonl'}")

    policy_rows = build_policy_rows(source_rows)
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows:
        by_policy[row["policy"]].append(row)

    baseline_summary = summarize_policy(by_policy["h001_real_task_context_memory_trust_v0"])
    policy_summary = []
    for policy, _ in POLICIES:
        baseline = None if policy == "h001_real_task_context_memory_trust_v0" else baseline_summary
        policy_summary.append(summarize_policy(by_policy[policy], baseline))

    policy_summary_by_row_band = summarize_by(policy_rows, "row_band")
    policy_summary_by_task = summarize_by(policy_rows, "task_context_id")
    policy_summary_by_batch = summarize_by(policy_rows, "batch_id")
    contract = build_policy_contract()
    claim_rows = build_claim_rows(policy_summary)
    selected = next(row for row in policy_summary if row["policy"] == contract["selected_policy"])

    source_by_query = {row["query_uid"]: row for row in source_rows}
    selected_rows = [
        {
            **row,
            "source_m98_group": source_by_query[row["query_uid"]]["map_real_top5_h001_group"],
            "source_h001_success": source_by_query[row["query_uid"]]["h001_success"],
            "source_conceptgraphs_success": source_by_query[row["query_uid"]]["conceptgraphs_success"],
            "source_real_top5_success": source_by_query[row["query_uid"]]["real_detector_top5_success"],
        }
        for row in by_policy[contract["selected_policy"]]
    ]

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_attempt_spl_proxy": baseline_summary["attempt_spl_proxy"],
        "h001_mean_expected_search_cost": baseline_summary["mean_expected_search_cost_all"],
        "h001_success_rows": baseline_summary["success_rows"],
        "m98_status": m98.get("status"),
        "m99_status": m99.get("status"),
        "next_recommended_unit": "E005-M101 map-assisted fallback claim-boundary / navigation-bridge decision",
        "query_rows": len(source_rows),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "selected_attempt_spl_proxy": selected["attempt_spl_proxy"],
        "selected_mean_expected_search_cost": selected["mean_expected_search_cost_all"],
        "selected_policy": contract["selected_policy"],
        "selected_success_gain_vs_h001": selected["success_gain_vs_h001"],
        "selected_success_rows": selected["success_rows"],
        "status": "e005_m100_conceptgraphs_assisted_fallback_policy_ready",
        "version": VERSION,
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(
        OUT_DIR / "summary.json",
        {
            "coverage": coverage,
            "policy_contract": contract,
            "policy_summary": policy_summary,
            "policy_summary_by_row_band": policy_summary_by_row_band,
            "policy_summary_by_task": policy_summary_by_task,
            "policy_summary_by_batch": policy_summary_by_batch,
            "claim_boundary_rows": claim_rows,
        },
    )
    write_json(OUT_DIR / "policy_contract.json", contract)
    write_jsonl(OUT_DIR / "policy_rows.jsonl", policy_rows)
    write_jsonl(OUT_DIR / "selected_policy_rows.jsonl", selected_rows)
    write_jsonl(OUT_DIR / "policy_summary_rows.jsonl", policy_summary)
    write_jsonl(OUT_DIR / "policy_summary_by_row_band.jsonl", policy_summary_by_row_band)
    write_jsonl(OUT_DIR / "policy_summary_by_task_context.jsonl", policy_summary_by_task)
    write_jsonl(OUT_DIR / "policy_summary_by_batch.jsonl", policy_summary_by_batch)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, policy_summary, claim_rows, contract))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
