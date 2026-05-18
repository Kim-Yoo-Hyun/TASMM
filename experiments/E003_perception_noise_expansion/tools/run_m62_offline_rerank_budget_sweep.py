#!/usr/bin/env python3
"""Run E003-M62 offline proposal rerank and budget repair sweep."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M59_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M59_direct_current_rescan_detector_run_v0"
DEFAULT_M60_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
DEFAULT_M61_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M61_direct_bridge_rank_failure_gate_v0"
DEFAULT_E001_DIR = REPO_ROOT / "experiments" / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M62_offline_rerank_budget_repair_v0"
M62_VERSION = "e003_m62_offline_rerank_budget_repair_v0"
TASK_POLICY = "detector_task_budget_v0"
ORDER_MODES = [
    "confidence_desc",
    "confidence_sqrt_depth",
    "confidence_log_depth",
    "confidence_size_guard",
    "old_memory_distance_guard",
    "oracle_target_first_upper_bound",
]
BUDGET_MODES = [
    "task_budget",
    "task_budget_plus1",
    "task_budget_plus2",
    "top5_budget",
    "adaptive_uncertainty_top5",
    "unbounded_until_target_or_exhausted",
]
NON_DEPLOYABLE_ORDER_MODES = {"oracle_target_first_upper_bound"}


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


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(a, b)))


def depth_value(row: dict[str, Any]) -> float:
    return float(row.get("depth_valid_pixel_count") or 0.0)


def confidence(row: dict[str, Any]) -> float:
    return float(row.get("confidence") or row.get("selection_score") or 0.0)


def size_guard_score(row: dict[str, Any]) -> float:
    # Penalize extremely small/large projected supports without using target labels.
    depth = max(depth_value(row), 1.0)
    preferred = 6000.0
    log_penalty = abs(math.log(depth / preferred))
    return confidence(row) / (1.0 + log_penalty)


def old_distance(row: dict[str, Any], e001_query: dict[str, Any]) -> float | None:
    old = e001_query.get("old_scene_aligned_centroid")
    centroid = row.get("centroid_world_m")
    if not old or not centroid:
        return None
    return distance(centroid, old)


def score(row: dict[str, Any], order_mode: str, target_uid: str, e001_query: dict[str, Any]) -> tuple[float, float, str]:
    old_dist = old_distance(row, e001_query)
    if order_mode == "confidence_desc":
        primary = confidence(row)
    elif order_mode == "confidence_sqrt_depth":
        primary = confidence(row) * math.sqrt(max(depth_value(row), 1.0))
    elif order_mode == "confidence_log_depth":
        primary = confidence(row) * math.log1p(max(depth_value(row), 0.0))
    elif order_mode == "confidence_size_guard":
        primary = size_guard_score(row)
    elif order_mode == "old_memory_distance_guard":
        base = confidence(row)
        if bool(e001_query.get("old_location_dead_end_expected")) and old_dist is not None:
            # Use stale-memory metadata only: demote proposals close to the old failed location.
            base *= min(2.0, max(0.25, old_dist / max(float(e001_query.get("success_threshold_m") or 0.5), 0.1)))
        primary = base
    elif order_mode == "oracle_target_first_upper_bound":
        primary = 10.0 if str(row.get("matched_target_uid")) == target_uid else confidence(row)
    else:
        raise RuntimeError(f"unknown order_mode: {order_mode}")
    tie_break = confidence(row)
    return primary, tie_break, str(row.get("proposal_uid", ""))


def order_proposals(
    rows: list[dict[str, Any]],
    order_mode: str,
    target_uid: str,
    e001_query: dict[str, Any],
) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -score(row, order_mode, target_uid, e001_query)[0],
            -score(row, order_mode, target_uid, e001_query)[1],
            int(row.get("pre_cap_rank") or 10**9),
            score(row, order_mode, target_uid, e001_query)[2],
        ),
    )


def task_budget_from_m60(policy_by_row: dict[tuple[str, str], dict[str, Any]], row_uid: str) -> int:
    return int(policy_by_row[(row_uid, TASK_POLICY)]["returned_location_count"])


def budget_for_mode(
    budget_mode: str,
    task_budget: int,
    candidate_count: int,
    target_rank: int | None,
    e001_query: dict[str, Any],
) -> tuple[int, str]:
    if budget_mode == "task_budget":
        return task_budget, "original_task_budget"
    if budget_mode == "task_budget_plus1":
        return min(candidate_count, task_budget + 1), "task_budget_plus1"
    if budget_mode == "task_budget_plus2":
        return min(candidate_count, task_budget + 2), "task_budget_plus2"
    if budget_mode == "top5_budget":
        return min(candidate_count, 5), "fixed_top5_detector_budget"
    if budget_mode == "adaptive_uncertainty_top5":
        if bool(e001_query.get("old_location_dead_end_expected")) or candidate_count >= 12:
            return min(candidate_count, max(task_budget, 5)), "adaptive_uncertainty_top5"
        return task_budget, "adaptive_keep_task_budget"
    if budget_mode == "unbounded_until_target_or_exhausted":
        if target_rank is not None:
            return target_rank, "visit_until_detected_target"
        return candidate_count, "exhaust_detector_candidates"
    raise RuntimeError(f"unknown budget_mode: {budget_mode}")


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def evaluate_sweep(
    query_rows: list[dict[str, Any]],
    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    e001_by_row_uid: dict[str, dict[str, Any]],
    policy_by_row: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prediction_rows = []
    for query in query_rows:
        row_uid = str(query["row_uid"])
        target_uid = str(query["target_uid"])
        e001_query = e001_by_row_uid[row_uid]
        same_label = proposals_by_scan_label.get((query["current_rescan_id"], query["label_canonical"]), [])
        task_budget = task_budget_from_m60(policy_by_row, row_uid)
        for order_mode in ORDER_MODES:
            ordered = order_proposals(same_label, order_mode, target_uid, e001_query)
            target_rank = None
            target_proposal_uid = None
            fp_before = None
            for rank, proposal in enumerate(ordered, start=1):
                if str(proposal.get("matched_target_uid")) == target_uid:
                    target_rank = rank
                    target_proposal_uid = str(proposal.get("proposal_uid"))
                    fp_before = sum(1 for prev in ordered[: rank - 1] if str(prev.get("matched_target_uid")) != target_uid)
                    break
            for budget_mode in BUDGET_MODES:
                returned_k, decision_reason = budget_for_mode(
                    budget_mode=budget_mode,
                    task_budget=task_budget,
                    candidate_count=len(ordered),
                    target_rank=target_rank,
                    e001_query=e001_query,
                )
                success = bool(target_rank is not None and target_rank <= returned_k)
                expected_cost = int(target_rank) if success and target_rank is not None else int(returned_k) + 1
                prediction_rows.append(
                    {
                        "m62_version": M62_VERSION,
                        "row_uid": row_uid,
                        "base_row_uid": query["base_row_uid"],
                        "pair_uid": query["pair_uid"],
                        "target_uid": target_uid,
                        "current_rescan_id": query["current_rescan_id"],
                        "label_canonical": query["label_canonical"],
                        "task_context_id": query["task_context_id"],
                        "row_band": query["row_band"],
                        "order_mode": order_mode,
                        "budget_mode": budget_mode,
                        "deployable_policy": order_mode not in NON_DEPLOYABLE_ORDER_MODES,
                        "decision_reason": decision_reason,
                        "candidate_count": len(ordered),
                        "target_detected": target_rank is not None,
                        "target_rank": target_rank,
                        "target_proposal_uid": target_proposal_uid,
                        "false_positive_before_target_count": fp_before,
                        "task_budget": task_budget,
                        "returned_location_count": returned_k,
                        "query_bridge_success": success,
                        "expected_search_cost": expected_cost,
                        "attempt_spl_proxy": attempt_spl(success, expected_cost),
                        "old_location_dead_end_expected": query["old_location_dead_end_expected"],
                        "old_location_dead_end_avoided": bool(query["old_location_dead_end_expected"] and success),
                        "real_rgbd_open_vocab_search_claim_ready": False,
                    }
                )

    summary_rows = []
    for order_mode in ORDER_MODES:
        for budget_mode in BUDGET_MODES:
            rows = [row for row in prediction_rows if row["order_mode"] == order_mode and row["budget_mode"] == budget_mode]
            successes = [row for row in rows if row["query_bridge_success"]]
            stale = [row for row in rows if row["old_location_dead_end_expected"]]
            detected = [row for row in rows if row["target_detected"]]
            summary_rows.append(
                {
                    "m62_version": M62_VERSION,
                    "order_mode": order_mode,
                    "budget_mode": budget_mode,
                    "deployable_policy": order_mode not in NON_DEPLOYABLE_ORDER_MODES,
                    "rows": len(rows),
                    "success_rows": len(successes),
                    "success_rate": safe_rate(len(successes), len(rows)),
                    "detected_rows": len(detected),
                    "mean_target_rank_if_detected": safe_mean(
                        [int(row["target_rank"]) for row in detected if row["target_rank"] is not None]
                    ),
                    "mean_false_positive_before_target_if_detected": safe_mean(
                        [
                            int(row["false_positive_before_target_count"])
                            for row in detected
                            if row["false_positive_before_target_count"] is not None
                        ]
                    ),
                    "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
                    "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
                    "old_location_dead_end_avoided_rows": sum(
                        1 for row in stale if row["old_location_dead_end_avoided"]
                    ),
                    "old_location_dead_end_avoided_rate": safe_rate(
                        sum(1 for row in stale if row["old_location_dead_end_avoided"]),
                        len(stale),
                    ),
                }
            )
    return prediction_rows, summary_rows


def select_best(summary_rows: list[dict[str, Any]], deployable: bool) -> dict[str, Any]:
    candidates = [row for row in summary_rows if bool(row["deployable_policy"]) == deployable]
    return sorted(
        candidates,
        key=lambda row: (
            -int(row["success_rows"]),
            float(row["mean_expected_search_cost"] or 10**9),
            -float(row["mean_attempt_spl_proxy"] or 0.0),
            str(row["order_mode"]),
            str(row["budget_mode"]),
        ),
    )[0]


def route_decision(best_deployable: dict[str, Any], best_oracle: dict[str, Any], m61_route: dict[str, Any]) -> dict[str, Any]:
    deployable_success = int(best_deployable["success_rows"])
    oracle_success = int(best_oracle["success_rows"])
    if deployable_success >= 3:
        selected = "integrate_deployable_rerank_budget_then_openmask3d"
        rationale = (
            "A deployable offline repair reaches the current proposal upper-bound on M60, but recall-miss rows remain. "
            "Integrate the repair as a method ablation, then run OpenMask3D feasibility for remaining recall misses."
        )
    elif deployable_success > 0:
        selected = "record_budget_repair_partial_then_openmask3d"
        rationale = (
            "Deployable budget/rerank repair recovers some detected targets, but the direct bridge remains dominated by recall miss and rank failure. "
            "Record it as a partial ablation and move to OpenMask3D feasibility."
        )
    elif oracle_success > 0:
        selected = "openmask3d_feasibility_with_rerank_upper_bound_note"
        rationale = (
            "Only non-deployable oracle reranking improves the bridge, so current proposal fields are not enough for a deployable repair. "
            "Move to OpenMask3D feasibility while keeping the oracle result as an upper-bound diagnostic."
        )
    else:
        selected = "openmask3d_feasibility_next"
        rationale = "Current proposals cannot repair the query bridge even with the tested budget/rerank sweep."
    return {
        "best_deployable_policy": {
            key: best_deployable[key]
            for key in [
                "order_mode",
                "budget_mode",
                "success_rows",
                "success_rate",
                "mean_expected_search_cost",
                "mean_attempt_spl_proxy",
            ]
        },
        "best_oracle_policy": {
            key: best_oracle[key]
            for key in [
                "order_mode",
                "budget_mode",
                "success_rows",
                "success_rate",
                "mean_expected_search_cost",
                "mean_attempt_spl_proxy",
            ]
        },
        "m61_selected_route": m61_route.get("selected_next_route"),
        "rationale": rationale,
        "selected_next_route": selected,
    }


def build_report(coverage: dict[str, Any], route: dict[str, Any]) -> str:
    best = route["best_deployable_policy"]
    oracle = route["best_oracle_policy"]
    return "\n".join(
        [
            "# E003-M62 Offline Rerank/Budget Repair Sweep",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}",
            f"- Sweep policies: {coverage['sweep_policy_rows']}",
            f"- Best deployable policy: `{best['order_mode']}` + `{best['budget_mode']}`.",
            f"- Best deployable success rows/rate: {best['success_rows']} / {best['success_rate']}",
            f"- Best deployable mean expected search cost: {best['mean_expected_search_cost']}",
            f"- Best oracle policy: `{oracle['order_mode']}` + `{oracle['budget_mode']}`.",
            f"- Best oracle success rows/rate: {oracle['success_rows']} / {oracle['success_rate']}",
            f"- Selected next route: `{route['selected_next_route']}`",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M62 supports an offline repair/upper-bound diagnostic for current M59 proposals.",
            "- E003-M62 does not support a final real RGB-D/open-vocabulary search claim.",
            "- E003-M62 can justify whether to spend compute on `OpenMask3D` by separating rank/budget repair from proposal recall miss.",
            "",
            "## 에이전트 추론",
            "",
            f"- {route['rationale']}",
            "- If a deployable policy improves only by expanding budget, it should be treated as a cost/recall tradeoff rather than a detector-quality improvement.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. Continue with the selected next route unless the scope changes.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m59-dir", default=DEFAULT_M59_DIR, type=Path)
    parser.add_argument("--m60-dir", default=DEFAULT_M60_DIR, type=Path)
    parser.add_argument("--m61-dir", default=DEFAULT_M61_DIR, type=Path)
    parser.add_argument("--e001-dir", default=DEFAULT_E001_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    proposals = load_jsonl(args.m59_dir / "matching" / "matched_proposals.jsonl")
    query_rows = load_jsonl(args.m60_dir / "query_bridge_rows.jsonl")
    policy_rows = load_jsonl(args.m60_dir / "policy_rows.jsonl")
    e001_rows = load_jsonl(args.e001_dir / "query_rows.jsonl")
    m61_route = load_json(args.m61_dir / "route_decision.json")

    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in proposals:
        proposals_by_scan_label[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    e001_by_row_uid = {str(row["row_uid"]): row for row in e001_rows}
    policy_by_row = {(str(row["row_uid"]), str(row["policy"])): row for row in policy_rows}

    prediction_rows, summary_rows = evaluate_sweep(
        query_rows=query_rows,
        proposals_by_scan_label=proposals_by_scan_label,
        e001_by_row_uid=e001_by_row_uid,
        policy_by_row=policy_by_row,
    )
    best_deployable = select_best(summary_rows, deployable=True)
    best_oracle = select_best(summary_rows, deployable=False)
    route = route_decision(best_deployable, best_oracle, m61_route)
    status = "offline_rerank_budget_repair_ready"
    if int(route["best_deployable_policy"]["success_rows"]) == 0:
        status = "offline_rerank_budget_repair_no_deployable_gain"

    coverage = {
        "best_deployable_success_rows": route["best_deployable_policy"]["success_rows"],
        "best_oracle_success_rows": route["best_oracle_policy"]["success_rows"],
        "m62_version": M62_VERSION,
        "next_recommended_unit": "OpenMask3D feasibility or deployable budget repair integration based on route_decision.json",
        "paper_table_command_ready": False,
        "query_rows": len(query_rows),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "selected_next_route": route["selected_next_route"],
        "status": status,
        "sweep_policy_rows": len(summary_rows),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "prediction_rows.jsonl", prediction_rows)
    write_jsonl(args.out_dir / "summary_rows.jsonl", summary_rows)
    write_json(args.out_dir / "route_decision.json", route)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, route))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
