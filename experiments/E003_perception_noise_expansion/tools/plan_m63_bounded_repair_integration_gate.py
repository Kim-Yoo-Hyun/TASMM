#!/usr/bin/env python3
"""Plan E003-M63 bounded rerank/budget repair integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M60_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
DEFAULT_M61_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M61_direct_bridge_rank_failure_gate_v0"
DEFAULT_M62_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M62_offline_rerank_budget_repair_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M63_bounded_repair_integration_gate_v0"
M63_VERSION = "e003_m63_bounded_repair_integration_gate_v0"
UNBOUNDED_BUDGET = "unbounded_until_target_or_exhausted"
ORACLE_ORDER = "oracle_target_first_upper_bound"
BOUNDED_BUDGETS = {
    "task_budget",
    "task_budget_plus1",
    "task_budget_plus2",
    "top5_budget",
    "adaptive_uncertainty_top5",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_delta(left: int | float | None, right: int | float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 6)


def policy_id(row: dict[str, Any]) -> str:
    return f"{row['order_mode']}+{row['budget_mode']}"


def role_row(role: str, row: dict[str, Any], note: str) -> dict[str, Any]:
    return {
        "m63_version": M63_VERSION,
        "paper_role": role,
        "policy_id": policy_id(row),
        "order_mode": row["order_mode"],
        "budget_mode": row["budget_mode"],
        "deployable_policy": row["deployable_policy"],
        "success_rows": row["success_rows"],
        "success_rate": row["success_rate"],
        "detected_rows": row["detected_rows"],
        "mean_expected_search_cost": row["mean_expected_search_cost"],
        "mean_attempt_spl_proxy": row["mean_attempt_spl_proxy"],
        "mean_target_rank_if_detected": row["mean_target_rank_if_detected"],
        "mean_false_positive_before_target_if_detected": row["mean_false_positive_before_target_if_detected"],
        "old_location_dead_end_avoided_rows": row["old_location_dead_end_avoided_rows"],
        "old_location_dead_end_avoided_rate": row["old_location_dead_end_avoided_rate"],
        "note": note,
    }


def best_row(rows: list[dict[str, Any]], *, prefer_adaptive: bool = False) -> dict[str, Any]:
    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        adaptive_bonus = 1 if prefer_adaptive and row["budget_mode"] == "adaptive_uncertainty_top5" else 0
        old_memory_bonus = 1 if row["order_mode"] == "old_memory_distance_guard" else 0
        return (
            int(row["success_rows"]),
            -float(row["mean_expected_search_cost"]),
            float(row["mean_attempt_spl_proxy"]),
            adaptive_bonus,
            old_memory_bonus,
            -float(row["mean_false_positive_before_target_if_detected"] or 0.0),
            policy_id(row),
        )

    return max(rows, key=key)


def select_rows(summary_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id = {policy_id(row): row for row in summary_rows}
    deployable = [row for row in summary_rows if row["deployable_policy"]]
    bounded = [row for row in deployable if row["budget_mode"] in BOUNDED_BUDGETS]
    bounded_non_task = [row for row in bounded if row["budget_mode"] != "task_budget"]
    task_budget_only = [row for row in bounded if row["budget_mode"] == "task_budget"]
    unbounded = [row for row in deployable if row["budget_mode"] == UNBOUNDED_BUDGET]
    oracle = [row for row in summary_rows if row["order_mode"] == ORACLE_ORDER]
    return {
        "baseline_task_budget": by_id["confidence_desc+task_budget"],
        "confidence_top5_control": by_id["confidence_desc+top5_budget"],
        "confidence_adaptive_control": by_id["confidence_desc+adaptive_uncertainty_top5"],
        "best_task_budget_rerank": best_row(task_budget_only),
        "selected_bounded": best_row(bounded_non_task, prefer_adaptive=True),
        "best_unbounded": best_row(unbounded),
        "oracle_task_budget": by_id[f"{ORACLE_ORDER}+task_budget"],
        "best_oracle": best_row(oracle),
    }


def selected_prediction_rows(
    prediction_rows: list[dict[str, Any]],
    selected: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    wanted = {
        "baseline_task_budget": selected["baseline_task_budget"],
        "confidence_top5_control": selected["confidence_top5_control"],
        "selected_bounded": selected["selected_bounded"],
        "best_unbounded": selected["best_unbounded"],
        "oracle_task_budget": selected["oracle_task_budget"],
    }
    output = []
    for role, policy in wanted.items():
        for row in prediction_rows:
            if row["order_mode"] == policy["order_mode"] and row["budget_mode"] == policy["budget_mode"]:
                output.append(
                    {
                        "m63_version": M63_VERSION,
                        "paper_role": role,
                        "policy_id": policy_id(policy),
                        "row_uid": row["row_uid"],
                        "target_uid": row["target_uid"],
                        "current_rescan_id": row["current_rescan_id"],
                        "label_canonical": row["label_canonical"],
                        "target_detected": row["target_detected"],
                        "target_rank": row["target_rank"],
                        "task_budget": row["task_budget"],
                        "returned_location_count": row["returned_location_count"],
                        "query_bridge_success": row["query_bridge_success"],
                        "expected_search_cost": row["expected_search_cost"],
                        "attempt_spl_proxy": row["attempt_spl_proxy"],
                        "old_location_dead_end_expected": row["old_location_dead_end_expected"],
                        "old_location_dead_end_avoided": row["old_location_dead_end_avoided"],
                    }
                )
    return output


def build_contract(
    selected: dict[str, dict[str, Any]],
    m60_metrics: dict[str, Any],
    m61_route: dict[str, Any],
    m62_coverage: dict[str, Any],
) -> dict[str, Any]:
    baseline = selected["baseline_task_budget"]
    top5 = selected["confidence_top5_control"]
    adaptive = selected["confidence_adaptive_control"]
    selected_bounded = selected["selected_bounded"]
    task_rerank = selected["best_task_budget_rerank"]
    unbounded = selected["best_unbounded"]
    oracle = selected["oracle_task_budget"]
    query_rows = int(m62_coverage["query_rows"])
    bounded_success_gain = int(selected_bounded["success_rows"]) - int(baseline["success_rows"])
    bounded_cost_delta = safe_delta(selected_bounded["mean_expected_search_cost"], baseline["mean_expected_search_cost"])
    rerank_vs_confidence_adaptive_success_gain = int(selected_bounded["success_rows"]) - int(adaptive["success_rows"])
    rerank_vs_confidence_adaptive_attempt_spl_delta = safe_delta(
        selected_bounded["mean_attempt_spl_proxy"],
        adaptive["mean_attempt_spl_proxy"],
    )
    upper_bound_gap_rows = int(unbounded["success_rows"]) - int(selected_bounded["success_rows"])
    oracle_rank_gap_rows = int(oracle["success_rows"]) - int(selected_bounded["success_rows"])
    bounded_ablation_ready = bounded_success_gain > 0 and float(selected_bounded["mean_expected_search_cost"]) <= 6.0
    rerank_unique_gain_ready = rerank_vs_confidence_adaptive_success_gain > 0
    return {
        "m63_version": M63_VERSION,
        "source_units": {
            "m60_status": m60_metrics.get("status", "metrics_json"),
            "m61_selected_route": m61_route.get("selected_next_route"),
            "m62_status": m62_coverage.get("status"),
        },
        "selected_policy": {
            "policy_name": "bounded_budget_repair_v0",
            "implementation_policy_id": policy_id(selected_bounded),
            "order_mode": selected_bounded["order_mode"],
            "budget_mode": selected_bounded["budget_mode"],
            "role": "paper_safe_ablation",
            "success_rows": selected_bounded["success_rows"],
            "success_rate": selected_bounded["success_rate"],
            "mean_expected_search_cost": selected_bounded["mean_expected_search_cost"],
            "mean_attempt_spl_proxy": selected_bounded["mean_attempt_spl_proxy"],
        },
        "controls": {
            "original_task_budget_policy_id": policy_id(baseline),
            "confidence_top5_policy_id": policy_id(top5),
            "confidence_adaptive_policy_id": policy_id(adaptive),
            "best_task_budget_rerank_policy_id": policy_id(task_rerank),
            "unbounded_upper_bound_policy_id": policy_id(unbounded),
            "oracle_task_budget_policy_id": policy_id(oracle),
        },
        "claim_readiness": {
            "bounded_budget_repair_ablation_ready": bounded_ablation_ready,
            "bounded_rerank_unique_gain_ready": rerank_unique_gain_ready,
            "unbounded_policy_claim_ready": False,
            "real_rgbd_open_vocab_search_claim_ready": False,
            "real_navigation_sr_spl_ready": False,
            "paper_table_command_ready": False,
        },
        "deltas": {
            "bounded_success_gain_vs_original_task_budget": bounded_success_gain,
            "bounded_success_rate_gain_vs_original_task_budget": safe_rate(bounded_success_gain, query_rows),
            "bounded_cost_delta_vs_original_task_budget": bounded_cost_delta,
            "bounded_success_gain_vs_confidence_adaptive_control": rerank_vs_confidence_adaptive_success_gain,
            "bounded_attempt_spl_delta_vs_confidence_adaptive_control": rerank_vs_confidence_adaptive_attempt_spl_delta,
            "best_task_budget_rerank_success_rows": task_rerank["success_rows"],
            "best_task_budget_rerank_success_gain_vs_original": int(task_rerank["success_rows"]) - int(baseline["success_rows"]),
            "unbounded_upper_bound_gap_rows": upper_bound_gap_rows,
            "oracle_task_budget_gap_rows": oracle_rank_gap_rows,
        },
        "allowed_inputs": [
            "detector proposal confidence",
            "proposal centroid/depth-support diagnostics",
            "task budget",
            "old-memory centroid",
            "old-location dead-end flag",
        ],
        "forbidden_inputs": [
            "matched_target_uid",
            "target_rank",
            "query_bridge_success",
            "3DSSG target instance id at inference time",
            "oracle target ordering",
        ],
        "paper_safe_statement": (
            "Bounded budget repair can be reported as a small direct-bridge ablation: it recovers 2 / 7 rows "
            "from the original 0 / 7 task-budget result. Rerank itself has no unique success gain over the "
            "confidence adaptive top-5 control on this denominator, so it should not be claimed as an independent "
            "method improvement yet."
        ),
        "non_claims": [
            "Do not claim final real RGB-D/open-vocabulary search robustness.",
            "Do not claim real navigation SR/SPL.",
            "Do not present unbounded visit-until-target search as cost-efficient.",
            "Do not claim unique task-adaptive reranking gain until the denominator is expanded.",
        ],
    }


def build_route(contract: dict[str, Any], m61_route: dict[str, Any]) -> dict[str, Any]:
    upper_bound_gap = contract["deltas"]["unbounded_upper_bound_gap_rows"]
    oracle_gap = contract["deltas"]["oracle_task_budget_gap_rows"]
    if upper_bound_gap > 0 or oracle_gap > 0:
        selected = "openmask3d_feasibility_gate_next"
        rationale = (
            "M63 fixes bounded repair as a paper-safe ablation but leaves a gap to the current-proposal/oracle "
            "upper bound. The remaining blocker is proposal recall and rank quality, so the next gate should "
            "decide OpenMask3D feasibility for the recall-miss targets."
        )
    else:
        selected = "expand_direct_bridge_denominator_before_openmask3d"
        rationale = (
            "Bounded repair reaches the current upper bound, so the immediate need is a larger denominator before "
            "adding another external proposal baseline."
        )
    return {
        "m63_version": M63_VERSION,
        "m61_selected_route": m61_route.get("selected_next_route"),
        "selected_next_route": selected,
        "next_recommended_unit": "E003-M64 OpenMask3D feasibility decision gate",
        "rationale": rationale,
        "route_options": {
            "openmask3d_feasibility_gate_next": {
                "benefit": "attacks detector recall miss and 3D instance proposal quality",
                "risk": "heavier dependency; still needs same query-level bridge evaluation",
            },
            "expand_direct_bridge_denominator_before_openmask3d": {
                "benefit": "reduces small-denominator risk before heavy external baseline work",
                "risk": "does not address current proposal recall miss by itself",
            },
        },
    }


def build_report(coverage: dict[str, Any], contract: dict[str, Any], route: dict[str, Any]) -> str:
    selected = contract["selected_policy"]
    deltas = contract["deltas"]
    readiness = contract["claim_readiness"]
    return "\n".join(
        [
            "# E003-M63 Bounded Repair Integration Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}",
            f"- Selected bounded policy: `{selected['implementation_policy_id']}`.",
            f"- Selected bounded success rows/rate: {selected['success_rows']} / {selected['success_rate']}",
            f"- Selected bounded mean expected search cost: {selected['mean_expected_search_cost']}",
            f"- Original task-budget success rows: {coverage['original_task_budget_success_rows']}",
            f"- Best task-budget rerank success rows: {coverage['best_task_budget_rerank_success_rows']}",
            f"- Unbounded upper-bound success rows: {coverage['unbounded_upper_bound_success_rows']}",
            f"- Oracle task-budget success rows: {coverage['oracle_task_budget_success_rows']}",
            f"- Bounded success gain vs original task budget: {deltas['bounded_success_gain_vs_original_task_budget']}",
            f"- Bounded success gain vs confidence adaptive control: {deltas['bounded_success_gain_vs_confidence_adaptive_control']}",
            f"- Bounded budget repair ablation ready: {readiness['bounded_budget_repair_ablation_ready']}",
            f"- Bounded rerank unique gain ready: {readiness['bounded_rerank_unique_gain_ready']}",
            f"- Selected next route: `{route['selected_next_route']}`",
            "",
            "## 논문 주장",
            "",
            "- E003-M63 supports using bounded budget repair as a small direct-bridge ablation.",
            "- E003-M63 does not support claiming unique bounded rerank gain on the current 7-row denominator.",
            "- E003-M63 keeps unbounded visit-until-target as an upper-bound diagnostic, not a cost-efficient method.",
            "- E003-M63 does not support final real RGB-D/open-vocabulary search or real navigation claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The safest paper use is to report bounded budget repair separately from unbounded upper bound.",
            "- The remaining upper-bound gap and recall-miss rows justify an `OpenMask3D` feasibility decision next.",
            "- If M64 is blocked, the fallback is to expand the direct bridge denominator before another heavy baseline.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. Continue to E003-M64 unless the scope changes.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m60-dir", type=Path, default=DEFAULT_M60_DIR)
    parser.add_argument("--m61-dir", type=Path, default=DEFAULT_M61_DIR)
    parser.add_argument("--m62-dir", type=Path, default=DEFAULT_M62_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    m60_metrics = load_json(args.m60_dir / "metrics.json")
    m61_route = load_json(args.m61_dir / "route_decision.json")
    m62_coverage = load_json(args.m62_dir / "coverage.json")
    summary_rows = load_jsonl(args.m62_dir / "summary_rows.jsonl")
    prediction_rows = load_jsonl(args.m62_dir / "prediction_rows.jsonl")

    selected = select_rows(summary_rows)
    contract = build_contract(selected, m60_metrics, m61_route, m62_coverage)
    route = build_route(contract, m61_route)
    selected_rows = [
        role_row(
            "original_task_budget",
            selected["baseline_task_budget"],
            "Original direct bridge task-budget baseline.",
        ),
        role_row(
            "confidence_top5_control",
            selected["confidence_top5_control"],
            "Fixed top-5 detector-confidence control.",
        ),
        role_row(
            "confidence_adaptive_control",
            selected["confidence_adaptive_control"],
            "Adaptive top-5 budget without memory-distance rerank.",
        ),
        role_row(
            "best_task_budget_rerank",
            selected["best_task_budget_rerank"],
            "Best rerank under the original task budget; diagnostic only.",
        ),
        role_row(
            "selected_bounded_ablation",
            selected["selected_bounded"],
            "Paper-safe bounded repair ablation, but not a unique rerank gain claim.",
        ),
        role_row(
            "unbounded_upper_bound",
            selected["best_unbounded"],
            "Upper-bound diagnostic only; not a cost-efficient deployable claim.",
        ),
        role_row(
            "oracle_task_budget_upper_bound",
            selected["oracle_task_budget"],
            "Non-deployable oracle ordering under task budget.",
        ),
    ]
    row_outcomes = selected_prediction_rows(prediction_rows, selected)
    coverage = {
        "m63_version": M63_VERSION,
        "status": "bounded_repair_integration_gate_ready",
        "query_rows": m62_coverage["query_rows"],
        "source_m62_status": m62_coverage["status"],
        "original_task_budget_success_rows": selected["baseline_task_budget"]["success_rows"],
        "confidence_top5_success_rows": selected["confidence_top5_control"]["success_rows"],
        "selected_bounded_success_rows": selected["selected_bounded"]["success_rows"],
        "selected_bounded_success_rate": selected["selected_bounded"]["success_rate"],
        "selected_bounded_mean_expected_search_cost": selected["selected_bounded"]["mean_expected_search_cost"],
        "best_task_budget_rerank_success_rows": selected["best_task_budget_rerank"]["success_rows"],
        "unbounded_upper_bound_success_rows": selected["best_unbounded"]["success_rows"],
        "oracle_task_budget_success_rows": selected["oracle_task_budget"]["success_rows"],
        "bounded_budget_repair_ablation_ready": contract["claim_readiness"]["bounded_budget_repair_ablation_ready"],
        "bounded_rerank_unique_gain_ready": contract["claim_readiness"]["bounded_rerank_unique_gain_ready"],
        "real_rgbd_open_vocab_search_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "paper_table_command_ready": False,
        "selected_next_route": route["selected_next_route"],
        "next_recommended_unit": route["next_recommended_unit"],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "policy_contract.json", contract)
    write_json(args.out_dir / "route_decision.json", route)
    write_jsonl(args.out_dir / "paper_table_rows.jsonl", selected_rows)
    write_jsonl(args.out_dir / "row_outcomes.jsonl", row_outcomes)
    write_text(args.out_dir / "report.md", build_report(coverage, contract, route))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
