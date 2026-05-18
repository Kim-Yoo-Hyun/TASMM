#!/usr/bin/env python3
"""Analyze E003-M60 direct bridge failures and choose the next repair route."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M60_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M61_direct_bridge_rank_failure_gate_v0"
M61_VERSION = "e003_m61_direct_bridge_rank_failure_gate_v0"
TASK_POLICY = "detector_task_budget_v0"
TOP5_POLICY = "detector_top5_v0"
UNBOUNDED_POLICY = "detector_unbounded_until_target_or_exhausted_v0"


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


def classify_failure(query: dict[str, Any], policies_by_row: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    row_uid = str(query["row_uid"])
    task = policies_by_row[(row_uid, TASK_POLICY)]
    top5 = policies_by_row[(row_uid, TOP5_POLICY)]
    unbounded = policies_by_row[(row_uid, UNBOUNDED_POLICY)]
    target_detected = bool(query["query_target_detected"])
    task_success = bool(task["query_bridge_success"])
    top5_success = bool(top5["query_bridge_success"])
    unbounded_success = bool(unbounded["query_bridge_success"])

    if task_success:
        failure_class = "resolved_by_current_task_budget"
        repair_hint = "none"
    elif not target_detected:
        failure_class = "detector_recall_miss"
        repair_hint = "proposal_source_or_prompt_recall"
    elif top5_success:
        failure_class = "task_budget_mismatch"
        repair_hint = "budget_conditioning_or_rank_promote_detected_target"
    elif unbounded_success:
        failure_class = "false_positive_rank_failure"
        repair_hint = "proposal_rerank_or_false_positive_suppression"
    else:
        failure_class = "unresolved_detector_bridge_failure"
        repair_hint = "manual_audit"

    target_rank = query.get("query_target_rank_by_detector_score")
    task_budget = int(task["returned_location_count"])
    rank_gap = int(target_rank) - task_budget if target_rank is not None else None
    top5_gap = int(target_rank) - int(top5["returned_location_count"]) if target_rank is not None else None
    return {
        "m61_version": M61_VERSION,
        "row_uid": row_uid,
        "base_row_uid": query["base_row_uid"],
        "pair_uid": query["pair_uid"],
        "target_uid": query["target_uid"],
        "current_rescan_id": query["current_rescan_id"],
        "label_canonical": query["label_canonical"],
        "task_context_id": query["task_context_id"],
        "row_band": query["row_band"],
        "old_location_dead_end_expected": query["old_location_dead_end_expected"],
        "query_target_detected": target_detected,
        "query_target_rank_by_detector_score": target_rank,
        "query_target_best_match_distance_m": query.get("query_target_best_match_distance_m"),
        "same_label_detector_proposal_count": query["same_label_detector_proposal_count"],
        "same_label_false_positive_count": query["same_label_false_positive_count"],
        "same_label_matched_other_target_count": query["same_label_matched_other_target_count"],
        "same_label_unmatched_false_positive_count": query["same_label_unmatched_false_positive_count"],
        "false_positive_before_target_count": query["false_positive_before_target_count"],
        "task_budget": task_budget,
        "top5_budget": int(top5["returned_location_count"]),
        "rank_gap_vs_task_budget": rank_gap,
        "rank_gap_vs_top5": top5_gap,
        "task_policy_success": task_success,
        "top5_success": top5_success,
        "unbounded_success": unbounded_success,
        "failure_class": failure_class,
        "repair_hint": repair_hint,
    }


def summarize_by_unique_target(failure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in failure_rows:
        grouped[str(row["target_uid"])].append(row)
    class_by_target = {}
    for target_uid, rows in sorted(grouped.items()):
        classes = Counter(row["failure_class"] for row in rows)
        if classes.get("detector_recall_miss"):
            target_class = "detector_recall_miss"
        elif classes.get("false_positive_rank_failure"):
            target_class = "false_positive_rank_failure"
        elif classes.get("task_budget_mismatch"):
            target_class = "task_budget_mismatch"
        else:
            target_class = classes.most_common(1)[0][0]
        class_by_target[target_uid] = {
            "failure_class": target_class,
            "label_canonical": rows[0]["label_canonical"],
            "query_rows": len(rows),
            "target_detected": any(row["query_target_detected"] for row in rows),
        }
    counts = Counter(row["failure_class"] for row in class_by_target.values())
    return {
        "unique_target_rows": len(class_by_target),
        "unique_target_failure_class_counts": dict(sorted(counts.items())),
        "unique_targets": class_by_target,
    }


def route_decision(failure_rows: list[dict[str, Any]], target_summary: dict[str, Any]) -> dict[str, Any]:
    row_counts = Counter(row["failure_class"] for row in failure_rows)
    detected_not_task = [
        row
        for row in failure_rows
        if row["query_target_detected"] and not row["task_policy_success"]
    ]
    target_counts = Counter(target["failure_class"] for target in target_summary["unique_targets"].values())
    rerank_upper_bound_rows = sum(1 for row in failure_rows if row["query_target_detected"])
    budget_top5_gain_rows = sum(1 for row in failure_rows if row["top5_success"] and not row["task_policy_success"])
    recall_miss_rows = row_counts.get("detector_recall_miss", 0)
    recall_miss_targets = target_counts.get("detector_recall_miss", 0)
    mean_rank_gap = safe_mean(
        [row["rank_gap_vs_task_budget"] for row in detected_not_task if row["rank_gap_vs_task_budget"] is not None]
    )

    if recall_miss_rows > len(failure_rows) / 2 and recall_miss_targets >= 2:
        selected = "proposal_rerank_then_openmask3d_feasibility"
        rationale = (
            "Current detector misses the largest number of query rows, but detected targets are also outside "
            "the task budget. Run an offline rerank/budget repair first because it is cheap and defines the "
            "upper bound on current proposals; then move to OpenMask3D if recall miss remains."
        )
    elif detected_not_task:
        selected = "proposal_rerank_budget_repair_first"
        rationale = (
            "The current proposals contain detected targets, but ranking and task budget block success. "
            "Repair rank/budget before paying for a heavier external proposal baseline."
        )
    else:
        selected = "openmask3d_feasibility_next"
        rationale = "The direct bridge is dominated by detector recall miss, so a stronger 3D proposal source is needed."

    return {
        "budget_top5_gain_rows": budget_top5_gain_rows,
        "detected_target_rerank_upper_bound_rows": rerank_upper_bound_rows,
        "mean_rank_gap_vs_task_budget_for_detected_failures": mean_rank_gap,
        "recall_miss_rows": recall_miss_rows,
        "recall_miss_unique_targets": recall_miss_targets,
        "rationale": rationale,
        "selected_next_route": selected,
        "route_options": {
            "detector_budget_repair": {
                "benefit": "Top-5 budget recovers rows whose targets are already detected within rank 5.",
                "ceiling_rows_on_m60": budget_top5_gain_rows,
                "risk": "Does not solve detector recall miss and increases search cost.",
            },
            "proposal_rerank": {
                "benefit": "Can convert detected targets into task-budget successes without another Docker detector run.",
                "ceiling_rows_on_m60": rerank_upper_bound_rows,
                "risk": "Cannot recover targets that current detector never matched.",
            },
            "openmask3d_feasibility": {
                "benefit": "Directly attacks missed 3D instance proposal targets.",
                "ceiling_rows_on_m60": len(failure_rows),
                "risk": "Heavier dependency and still needs rank/budget evaluation after proposal generation.",
            },
        },
    }


def build_report(coverage: dict[str, Any], route: dict[str, Any], target_summary: dict[str, Any]) -> str:
    counts = coverage["failure_class_counts"]
    return "\n".join(
        [
            "# E003-M61 Direct Bridge Rank/Failure Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}",
            f"- Unique targets: {target_summary['unique_target_rows']}",
            f"- Failure class counts: {counts}",
            f"- Unique target failure class counts: {target_summary['unique_target_failure_class_counts']}",
            f"- Detected target rerank upper-bound rows: {route['detected_target_rerank_upper_bound_rows']}",
            f"- Top-5 budget gain rows: {route['budget_top5_gain_rows']}",
            f"- Recall miss rows: {route['recall_miss_rows']}",
            f"- Recall miss unique targets: {route['recall_miss_unique_targets']}",
            f"- Mean rank gap vs task budget for detected failures: {route['mean_rank_gap_vs_task_budget_for_detected_failures']}",
            f"- Selected next route: `{route['selected_next_route']}`",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M61 supports a failure taxonomy for the direct bridge.",
            "- E003-M61 does not support a final real RGB-D/open-vocabulary search claim.",
            "- E003-M61 supports saying the current failure is mixed: detector recall miss plus rank/budget failure.",
            "",
            "## 에이전트 추론",
            "",
            f"- {route['rationale']}",
            "- `OpenMask3D` remains important, but a small offline rank/budget repair should come first to avoid misattributing current-proposal ranking failures to proposal-source recall only.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. Continue with the selected next route unless the research scope changes.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m60-dir", default=DEFAULT_M60_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    query_rows = load_jsonl(args.m60_dir / "query_bridge_rows.jsonl")
    policy_rows = load_jsonl(args.m60_dir / "policy_rows.jsonl")
    m60_coverage = load_json(args.m60_dir / "coverage.json")
    policies_by_row = {(str(row["row_uid"]), str(row["policy"])): row for row in policy_rows}

    failure_rows = [classify_failure(row, policies_by_row) for row in query_rows]
    target_summary = summarize_by_unique_target(failure_rows)
    route = route_decision(failure_rows, target_summary)
    failure_counts = Counter(row["failure_class"] for row in failure_rows)
    status = "direct_bridge_rank_failure_gate_ready"
    if route["selected_next_route"] == "openmask3d_feasibility_next":
        status = "direct_bridge_external_proposal_needed"

    coverage = {
        "failure_class_counts": dict(sorted(failure_counts.items())),
        "m60_dir": str(args.m60_dir),
        "m60_status": m60_coverage.get("status"),
        "m61_version": M61_VERSION,
        "next_recommended_unit": "E003-M62 offline proposal rerank/budget repair sweep before OpenMask3D feasibility",
        "paper_table_command_ready": False,
        "query_rows": len(query_rows),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "selected_next_route": route["selected_next_route"],
        "status": status,
        "unique_target_failure_class_counts": target_summary["unique_target_failure_class_counts"],
        "unique_targets": target_summary["unique_target_rows"],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "target_summary.json", target_summary)
    write_json(args.out_dir / "route_decision.json", route)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, route, target_summary))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
