#!/usr/bin/env python3
"""Analyze E002 occupancy-grid source and policy failures."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRID_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
DEFAULT_EVAL_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M06_grid_path_policy_evaluation_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M07_grid_failure_source_analysis_v0"
ANALYSIS_VERSION = "e002_grid_failure_source_analysis_v0"
TASK_POLICY = "task_conditioned_budget_v0"
GRID_POLICY = "grid_path_aware_task_conditioned_budget_v0"
EPS = 1e-9


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_predictions(predictions: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["row_uid"], row["policy"]): row for row in predictions}


def target_candidate_by_row(candidate_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for row in candidate_rows:
        if row["candidate_is_target"]:
            output[row["row_uid"]] = row
    return output


def build_target_source_rows(
    query_rows: list[dict[str, Any]],
    target_candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for query in query_rows:
        if query["target_grid_reachable"]:
            continue
        target = target_candidates.get(query["row_uid"])
        source_failure = None
        projection_status = None
        if target:
            source_failure = target.get("candidate_grid_failure_type")
            projection_status = target.get("candidate_projection_status")
        if source_failure is None:
            source_failure = query.get("grid_failure_type") or "unknown_target_grid_source_failure"
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "pair_uid": query["pair_uid"],
                "rescan_id": query["rescan_id"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "object_label": query["object_label"],
                "target_instance_id": query["object_instance_id_rescan"],
                "source_failure_type": source_failure,
                "projection_status": projection_status,
                "start_projection_status": query.get("start_projection_status"),
                "start_nearest_free_cell_distance_m": query.get("start_nearest_free_cell_distance_m"),
                "candidate_grid_reachable_count": query.get("candidate_grid_reachable_count"),
                "candidate_grid_unreachable_count": query.get("candidate_grid_unreachable_count"),
                "interpretation": "source_or_grid_construction_limit",
                "next_test": "inspect occupancy-grid projection, free-space connectivity, and object centroid-to-free-cell distance",
            }
        )
    return rows


def build_returned_unreachable_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        if int(row["returned_unreachable_count"]) <= 0:
            continue
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "task_context_id": row["task_context_id"],
                "policy": row["policy"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "target_grid_reachable": row["target_grid_reachable"],
                "grid_path_success": row["grid_path_success"],
                "returned_location_count": row["returned_location_count"],
                "returned_unreachable_count": row["returned_unreachable_count"],
                "expected_grid_path_cost_m": row["expected_grid_path_cost_m"],
                "grid_failure_type": row["grid_failure_type"],
                "interpretation": "policy_returned_unreachable_candidate"
                if row["target_grid_reachable"]
                else "source_limit_dominates_policy_return",
                "next_test": "filter unreachable candidates before ranking or calibrate grid projection",
            }
        )
    return rows


def compare_task_vs_grid(
    query_rows: list[dict[str, Any]],
    prediction_index: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for query in query_rows:
        task = prediction_index[(query["row_uid"], TASK_POLICY)]
        grid = prediction_index[(query["row_uid"], GRID_POLICY)]
        task_success = bool(task["grid_path_success"])
        grid_success = bool(grid["grid_path_success"])
        task_cost = float(task["expected_grid_path_cost_m"])
        grid_cost = float(grid["expected_grid_path_cost_m"])
        task_utility = float(task["grid_path_utility_proxy"])
        grid_utility = float(grid["grid_path_utility_proxy"])

        if task_success and not grid_success:
            comparison = "grid_aware_regression_success_loss"
        elif grid_success and not task_success:
            comparison = "grid_aware_improvement_success_gain"
        elif task_success and grid_success:
            if grid_cost + EPS < task_cost:
                comparison = "grid_aware_cost_improvement"
            elif task_cost + EPS < grid_cost:
                comparison = "grid_aware_cost_regression"
            else:
                comparison = "grid_aware_tie_success"
        else:
            if task["grid_failure_type"] == grid["grid_failure_type"]:
                comparison = "both_fail_same_type"
            else:
                comparison = "both_fail_different_type"

        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "pair_uid": query["pair_uid"],
                "rescan_id": query["rescan_id"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "object_label": query["object_label"],
                "target_grid_reachable": query["target_grid_reachable"],
                "comparison": comparison,
                "task_success": task_success,
                "grid_aware_success": grid_success,
                "task_cost_m": round6(task_cost),
                "grid_aware_cost_m": round6(grid_cost),
                "cost_delta_grid_minus_task_m": round6(grid_cost - task_cost),
                "task_utility": round6(task_utility),
                "grid_aware_utility": round6(grid_utility),
                "utility_delta_grid_minus_task": round6(grid_utility - task_utility),
                "task_failure_type": task["grid_failure_type"],
                "grid_aware_failure_type": grid["grid_failure_type"],
                "task_returned_unreachable_count": task["returned_unreachable_count"],
                "grid_aware_returned_unreachable_count": grid["returned_unreachable_count"],
                "task_returned_location_count": task["returned_location_count"],
                "grid_aware_returned_location_count": grid["returned_location_count"],
                "interpretation": interpret_comparison(comparison),
            }
        )
    return rows


def interpret_comparison(comparison: str) -> str:
    if comparison == "grid_aware_regression_success_loss":
        return "grid-aware ordering ranks reachable but wrong candidates ahead of the target under the fixed budget"
    if comparison == "grid_aware_improvement_success_gain":
        return "grid-aware ordering recovers target where semantic ranking budget misses"
    if comparison == "grid_aware_cost_improvement":
        return "grid-aware ordering preserves success and lowers grid path cost"
    if comparison == "grid_aware_cost_regression":
        return "grid-aware ordering preserves success but increases grid path cost"
    if comparison == "grid_aware_tie_success":
        return "same success and cost under both orderings"
    return "both policies fail; inspect source failure and budget separately"


def summarize_comparisons(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "all": summarize_comparison_subset(rows),
    }
    for band in sorted({row["row_band"] for row in rows}):
        output[f"row_band:{band}"] = summarize_comparison_subset([row for row in rows if row["row_band"] == band])
    for context in sorted({row["task_context_id"] for row in rows}):
        output[f"task_context:{context}"] = summarize_comparison_subset([row for row in rows if row["task_context_id"] == context])
    return output


def summarize_comparison_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    cost_deltas = [row["cost_delta_grid_minus_task_m"] for row in rows if row["task_success"] and row["grid_aware_success"]]
    utility_deltas = [row["utility_delta_grid_minus_task"] for row in rows]
    return {
        "rows": len(rows),
        "comparison_counts": counter_dict(Counter(row["comparison"] for row in rows)),
        "grid_aware_success_gain_rows": sum(1 for row in rows if row["comparison"] == "grid_aware_improvement_success_gain"),
        "grid_aware_success_loss_rows": sum(1 for row in rows if row["comparison"] == "grid_aware_regression_success_loss"),
        "grid_aware_cost_improvement_rows": sum(1 for row in rows if row["comparison"] == "grid_aware_cost_improvement"),
        "grid_aware_cost_regression_rows": sum(1 for row in rows if row["comparison"] == "grid_aware_cost_regression"),
        "mean_cost_delta_on_both_success_m": round6(sum(cost_deltas) / len(cost_deltas)) if cost_deltas else None,
        "mean_utility_delta_grid_minus_task": round6(sum(utility_deltas) / len(utility_deltas)) if utility_deltas else None,
    }


def build_summary(
    target_source_rows: list[dict[str, Any]],
    returned_unreachable_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    grid_coverage: dict[str, Any],
    eval_coverage: dict[str, Any],
) -> dict[str, Any]:
    target_base_uids = {row["base_row_uid"] for row in target_source_rows}
    returned_target_reachable = [row for row in returned_unreachable_rows if row["target_grid_reachable"]]
    returned_source_limited = [row for row in returned_unreachable_rows if not row["target_grid_reachable"]]
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": "grid_failure_source_analysis_ready"
        if len(target_source_rows) == eval_coverage["grid_target_unreachable_rows"]
        and len(comparison_rows) == eval_coverage["query_rows"]
        else "review_needed",
        "grid_query_rows": eval_coverage["query_rows"],
        "target_unreachable_query_rows": len(target_source_rows),
        "target_unreachable_base_rows": len(target_base_uids),
        "target_unreachable_rate": safe_rate(len(target_source_rows), eval_coverage["query_rows"]),
        "target_source_failure_counts": counter_dict(Counter(row["source_failure_type"] for row in target_source_rows)),
        "target_source_row_band_counts": counter_dict(Counter(row["row_band"] for row in target_source_rows)),
        "target_source_label_counts": counter_dict(Counter(row["object_label"] for row in target_source_rows)),
        "target_source_scan_counts": counter_dict(Counter(row["rescan_id"] for row in target_source_rows)),
        "returned_unreachable_prediction_rows": len(returned_unreachable_rows),
        "returned_unreachable_with_reachable_target_rows": len(returned_target_reachable),
        "returned_unreachable_source_limited_rows": len(returned_source_limited),
        "returned_unreachable_policy_counts": counter_dict(Counter(row["policy"] for row in returned_unreachable_rows)),
        "returned_unreachable_failure_counts": counter_dict(Counter(row["grid_failure_type"] for row in returned_unreachable_rows)),
        "grid_aware_comparison": summarize_comparisons(comparison_rows),
        "m05_candidate_grid_reachable_rows": grid_coverage["candidate_grid_reachable_rows"],
        "m05_candidate_grid_unreachable_rows": grid_coverage["candidate_grid_unreachable_rows"],
        "m06_policy_failure_counts": eval_coverage["policy_failure_counts"],
        "m06_failure_type_counts": eval_coverage["failure_type_counts"],
        "claim_boundary": {
            "supported": [
                "target/source failure can be separated from policy failure under occupancy-grid path-cost proxy",
                "grid-aware ordering is currently not a supported improvement claim",
                "task-conditioned budget should be compared against always_top5 and oracle under grid cost",
            ],
            "unsupported": [
                "real navigation SR/SPL",
                "deployable search policy",
                "collision-aware robot planning",
                "RGB-D/open-vocabulary perception robustness",
            ],
        },
    }


def build_report(summary: dict[str, Any], out_dir: Path) -> str:
    comparison_all = summary["grid_aware_comparison"]["all"]
    significant = summary["grid_aware_comparison"].get("row_band:significant_moved", {})
    lines = [
        "# E002-M07 Grid Failure Source Analysis",
        "",
        "## Status",
        "",
        summary["status"],
        "",
        "## 사실",
        "",
        f"- Grid query rows: {summary['grid_query_rows']}",
        f"- Target-unreachable query rows: {summary['target_unreachable_query_rows']}",
        f"- Target-unreachable base rows: {summary['target_unreachable_base_rows']}",
        f"- Target-unreachable rate: {summary['target_unreachable_rate']}",
        f"- Returned-unreachable prediction rows: {summary['returned_unreachable_prediction_rows']}",
        f"- Returned-unreachable rows with reachable target: {summary['returned_unreachable_with_reachable_target_rows']}",
        f"- Returned-unreachable rows dominated by source limitation: {summary['returned_unreachable_source_limited_rows']}",
        f"- Candidate grid reachable rows from M05: {summary['m05_candidate_grid_reachable_rows']}",
        f"- Candidate grid unreachable rows from M05: {summary['m05_candidate_grid_unreachable_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Target Source Failures",
        "",
        "| Source failure | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["target_source_failure_counts"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Grid-Aware Comparison",
            "",
            "| Scope | Rows | Success gain | Success loss | Cost improvement | Cost regression | Mean utility delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            "| `all` | {rows} | {gain} | {loss} | {cost_gain} | {cost_loss} | {utility} |".format(
                rows=comparison_all.get("rows"),
                gain=comparison_all.get("grid_aware_success_gain_rows"),
                loss=comparison_all.get("grid_aware_success_loss_rows"),
                cost_gain=comparison_all.get("grid_aware_cost_improvement_rows"),
                cost_loss=comparison_all.get("grid_aware_cost_regression_rows"),
                utility=comparison_all.get("mean_utility_delta_grid_minus_task"),
            ),
            "| `significant_moved` | {rows} | {gain} | {loss} | {cost_gain} | {cost_loss} | {utility} |".format(
                rows=significant.get("rows"),
                gain=significant.get("grid_aware_success_gain_rows"),
                loss=significant.get("grid_aware_success_loss_rows"),
                cost_gain=significant.get("grid_aware_cost_improvement_rows"),
                cost_loss=significant.get("grid_aware_cost_regression_rows"),
                utility=significant.get("mean_utility_delta_grid_minus_task"),
            ),
            "",
            "## 논문 주장",
            "",
            "- E002-M07 supports separating occupancy-grid source limits from policy failures.",
            "- E002-M07 supports keeping `target_grid_unreachable` rows explicit instead of dropping them.",
            "- E002-M07 does not support a positive claim for `grid_path_aware_task_conditioned_budget_v0`.",
            "- E002-M07 does not support real navigation `SR` / `SPL`, deployable search policy, or RGB-D/open-vocabulary robustness claims.",
            "",
            "## 에이전트 추론",
            "",
            "- Target-unreachable rows are mostly source/grid-construction limits, so they should be reported separately from method misses.",
            "- Grid-aware ordering reduces some returned-unreachable attempts, but it also loses target recall under fixed budgets.",
            "- The next method step should improve reachable-candidate scoring or add a source-quality mask before claiming navigation-style value.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E002-M07. Next action should be either a source-quality mask or a grid-aware scoring revision.",
            "",
            "## Outputs",
            "",
            "- `target_source_rows.jsonl`",
            "- `returned_unreachable_rows.jsonl`",
            "- `grid_aware_comparison_rows.jsonl`",
            "- `summary.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    grid_query_rows = load_jsonl(args.grid_dir / "grid_query_rows.jsonl")
    grid_candidate_rows = load_jsonl(args.grid_dir / "grid_candidate_rows.jsonl")
    grid_coverage = load_json(args.grid_dir / "coverage.json")
    predictions = load_jsonl(args.eval_dir / "predictions.jsonl")
    eval_coverage = load_json(args.eval_dir / "coverage.json")

    target_candidates = target_candidate_by_row(grid_candidate_rows)
    prediction_index = group_predictions(predictions)
    target_source_rows = build_target_source_rows(grid_query_rows, target_candidates)
    returned_unreachable_rows = build_returned_unreachable_rows(predictions)
    comparison_rows = compare_task_vs_grid(grid_query_rows, prediction_index)
    summary = build_summary(
        target_source_rows,
        returned_unreachable_rows,
        comparison_rows,
        grid_coverage,
        eval_coverage,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "target_source_rows.jsonl", target_source_rows)
    write_jsonl(args.out_dir / "returned_unreachable_rows.jsonl", returned_unreachable_rows)
    write_jsonl(args.out_dir / "grid_aware_comparison_rows.jsonl", comparison_rows)
    write_json(args.out_dir / "summary.json", summary)
    (args.out_dir / "report.md").write_text(build_report(summary, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": summary["status"],
                "target_unreachable_query_rows": summary["target_unreachable_query_rows"],
                "target_unreachable_base_rows": summary["target_unreachable_base_rows"],
                "returned_unreachable_prediction_rows": summary["returned_unreachable_prediction_rows"],
                "grid_aware_all": summary["grid_aware_comparison"]["all"],
                "grid_aware_significant": summary["grid_aware_comparison"].get("row_band:significant_moved"),
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
