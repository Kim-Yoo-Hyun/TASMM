#!/usr/bin/env python3
"""Evaluate E002 grid policies after separating source-quality limits."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from evaluate_grid_path_policies import (  # noqa: E402
    POLICIES,
    build_failure_rows,
    load_json,
    load_jsonl,
    mean,
    safe_rate,
    summarize,
    write_json,
    write_jsonl,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRID_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
DEFAULT_EVAL_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M06_grid_path_policy_evaluation_v0"
DEFAULT_SOURCE_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M07_grid_failure_source_analysis_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M08_source_quality_filtered_grid_eval_v0"
ANALYSIS_VERSION = "e002_source_quality_filtered_grid_eval_v0"


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def source_rows_by_uid(source_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_uid"]: row for row in source_rows}


def build_source_quality_rows(
    query_rows: list[dict[str, Any]],
    target_source_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for query in query_rows:
        target_reachable = bool(query["target_grid_reachable"])
        all_candidates_reachable = (
            target_reachable and int(query.get("candidate_grid_unreachable_count", 0)) == 0
        )
        source_row = target_source_rows.get(query["row_uid"])
        source_failure_type = None if target_reachable else "unknown_target_grid_source_failure"
        projection_status = None
        if source_row:
            source_failure_type = source_row["source_failure_type"]
            projection_status = source_row.get("projection_status")

        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": query["row_uid"],
                "base_row_uid": query["base_row_uid"],
                "pair_uid": query["pair_uid"],
                "reference_scan_id": query["reference_scan_id"],
                "rescan_id": query["rescan_id"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "object_label": query["object_label"],
                "target_grid_reachable": target_reachable,
                "candidate_grid_reachable_count": query.get("candidate_grid_reachable_count"),
                "candidate_grid_unreachable_count": query.get("candidate_grid_unreachable_count"),
                "source_quality_primary_mask": "target_reachable_eval"
                if target_reachable
                else "source_limited_target_grid_unreachable",
                "source_quality_strict_mask": "all_candidates_reachable_eval"
                if all_candidates_reachable
                else "candidate_unreachable_diagnostic"
                if target_reachable
                else "source_limited_target_grid_unreachable",
                "include_in_target_reachable_eval": target_reachable,
                "include_in_all_candidates_reachable_eval": all_candidates_reachable,
                "source_failure_type": source_failure_type,
                "target_projection_status": projection_status,
                "start_projection_status": query.get("start_projection_status"),
                "start_nearest_free_cell_distance_m": query.get("start_nearest_free_cell_distance_m"),
                "target_grid_path_cost_m": query.get("target_grid_path_cost_m"),
                "grid_path_cost_profile_id": query["grid_path_cost_profile_id"],
                "interpretation": "policy_evaluable_grid_target"
                if target_reachable
                else "source_quality_limit_not_policy_failure",
            }
        )
    return rows


def attach_source_quality(
    predictions: list[dict[str, Any]],
    quality_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in predictions:
        quality = quality_by_uid[row["row_uid"]]
        enriched = dict(row)
        for key in [
            "source_quality_primary_mask",
            "source_quality_strict_mask",
            "include_in_target_reachable_eval",
            "include_in_all_candidates_reachable_eval",
            "source_failure_type",
        ]:
            enriched[key] = quality[key]
        rows.append(enriched)
    return rows


def policy_metric(metrics: dict[str, Any], subset: str, context: str, policy: str) -> dict[str, Any]:
    return metrics[subset][context][policy]


def policy_delta(left: dict[str, Any], right: dict[str, Any], key: str) -> float | None:
    if left.get(key) is None or right.get(key) is None:
        return None
    return round6(float(left[key]) - float(right[key]))


def build_key_comparisons(metrics: dict[str, Any], subset_name: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for row_subset in ["all", "significant_moved", "low_motion_control", "mid_motion_review"]:
        output[row_subset] = {}
        for context in ["routine_fetch", "high_value_fetch", "noisy_high_value_fetch"]:
            if context not in metrics[row_subset]:
                continue
            task = policy_metric(metrics, row_subset, context, "task_conditioned_budget_v0")
            static = policy_metric(metrics, row_subset, context, "scene_aligned_static_map")
            top5 = policy_metric(metrics, row_subset, context, "always_top5")
            oracle = policy_metric(metrics, row_subset, context, "oracle_current_target")
            grid = policy_metric(metrics, row_subset, context, "grid_path_aware_task_conditioned_budget_v0")
            output[row_subset][context] = {
                "subset_name": subset_name,
                "task_vs_static_sr_delta": policy_delta(task, static, "grid_proxy_sr"),
                "task_vs_top5_sr_delta": policy_delta(task, top5, "grid_proxy_sr"),
                "task_vs_oracle_sr_delta": policy_delta(task, oracle, "grid_proxy_sr"),
                "grid_aware_vs_task_sr_delta": policy_delta(grid, task, "grid_proxy_sr"),
                "grid_aware_vs_task_utility_delta": policy_delta(
                    grid, task, "mean_grid_path_utility_proxy"
                ),
                "task_sr": task["grid_proxy_sr"],
                "top5_sr": top5["grid_proxy_sr"],
                "oracle_sr": oracle["grid_proxy_sr"],
                "grid_aware_sr": grid["grid_proxy_sr"],
                "task_cost_m": task["mean_expected_grid_path_cost_m"],
                "top5_cost_m": top5["mean_expected_grid_path_cost_m"],
                "oracle_cost_m": oracle["mean_expected_grid_path_cost_m"],
                "task_attempt_spl_proxy": task["grid_attempt_spl_proxy"],
                "top5_attempt_spl_proxy": top5["grid_attempt_spl_proxy"],
            }
    return output


def summarize_source_limits(source_quality_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_limited = [
        row
        for row in source_quality_rows
        if row["source_quality_primary_mask"] == "source_limited_target_grid_unreachable"
    ]
    primary = [row for row in source_quality_rows if row["include_in_target_reachable_eval"]]
    strict = [row for row in source_quality_rows if row["include_in_all_candidates_reachable_eval"]]
    return {
        "query_rows": len(source_quality_rows),
        "target_reachable_eval_rows": len(primary),
        "source_limited_rows": len(source_limited),
        "all_candidates_reachable_eval_rows": len(strict),
        "target_reachable_eval_rate": safe_rate(len(primary), len(source_quality_rows)),
        "all_candidates_reachable_eval_rate": safe_rate(len(strict), len(source_quality_rows)),
        "source_limited_row_band_counts": counter_dict(
            Counter(row["row_band"] for row in source_limited)
        ),
        "source_limited_task_context_counts": counter_dict(
            Counter(row["task_context_id"] for row in source_limited)
        ),
        "source_failure_counts": counter_dict(
            Counter(row["source_failure_type"] for row in source_limited)
        ),
        "candidate_unreachable_diagnostic_rows": sum(
            1
            for row in source_quality_rows
            if row["source_quality_strict_mask"] == "candidate_unreachable_diagnostic"
        ),
        "candidate_unreachable_diagnostic_row_band_counts": counter_dict(
            Counter(
                row["row_band"]
                for row in source_quality_rows
                if row["source_quality_strict_mask"] == "candidate_unreachable_diagnostic"
            )
        ),
    }


def summarize_returned_unreachable(filtered_predictions: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[str, dict[str, Any]] = {}
    for policy in POLICIES:
        rows = [row for row in filtered_predictions if row["policy"] == policy]
        if not rows:
            continue
        unreachable_rows = [row for row in rows if int(row["returned_unreachable_count"]) > 0]
        by_policy[policy] = {
            "rows": len(rows),
            "returned_unreachable_rows": len(unreachable_rows),
            "returned_unreachable_rate": safe_rate(len(unreachable_rows), len(rows)),
            "mean_returned_unreachable_count": mean(
                [float(row["returned_unreachable_count"]) for row in rows]
            ),
        }
    return by_policy


def build_coverage(
    source_quality_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    primary_predictions: list[dict[str, Any]],
    strict_predictions: list[dict[str, Any]],
    primary_failures: list[dict[str, Any]],
    strict_failures: list[dict[str, Any]],
    source_summary: dict[str, Any],
    primary_metrics: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    routine_sig_oracle = primary_metrics["significant_moved"]["routine_fetch"][
        "oracle_current_target"
    ]["grid_proxy_sr"]
    status = (
        "source_quality_filtered_grid_eval_ready"
        if source_summary["target_reachable_eval_rows"] > 0
        and source_summary["source_limited_rows"]
        == source_summary["query_rows"] - source_summary["target_reachable_eval_rows"]
        and routine_sig_oracle == 1.0
        else "review_needed"
    )
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "query_rows": source_summary["query_rows"],
        "prediction_rows": len(predictions),
        "target_reachable_eval_rows": source_summary["target_reachable_eval_rows"],
        "target_reachable_eval_prediction_rows": len(primary_predictions),
        "target_reachable_eval_failure_rows": len(primary_failures),
        "source_limited_rows": source_summary["source_limited_rows"],
        "all_candidates_reachable_eval_rows": source_summary[
            "all_candidates_reachable_eval_rows"
        ],
        "all_candidates_reachable_eval_prediction_rows": len(strict_predictions),
        "all_candidates_reachable_eval_failure_rows": len(strict_failures),
        "source_quality_mask_policy": {
            "primary_policy_metric_mask": "target_reachable_eval",
            "diagnostic_source_mask": "source_limited_target_grid_unreachable",
            "strict_sensitivity_mask": "all_candidates_reachable_eval",
        },
        "claim_boundary": {
            "supported": [
                "source-limited target-unreachable rows can be separated from policy metrics",
                "filtered grid-path proxy metrics can be reported with oracle upper bound equal to 1.0 on target-reachable rows",
                "candidate-unreachable rows should be reported as a sensitivity diagnostic",
            ],
            "unsupported": [
                "real navigation SR/SPL",
                "deployable search policy",
                "collision-aware robot planning",
                "RGB-D/open-vocabulary perception robustness",
                "positive improvement claim for naive grid-path-aware ordering",
            ],
        },
        "outputs": {
            "source_quality_rows": str(out_dir / "source_quality_rows.jsonl"),
            "source_limit_rows": str(out_dir / "source_limit_rows.jsonl"),
            "filtered_predictions": str(out_dir / "filtered_predictions.jsonl"),
            "target_reachable_failure_rows": str(out_dir / "target_reachable_failure_rows.jsonl"),
            "metrics": str(out_dir / "metrics.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def table_row(metrics: dict[str, Any], subset: str, context: str, policy: str) -> str:
    item = metrics[subset][context][policy]
    return "| `{}` | {} | {} | {} | {} | {} | {} |".format(
        policy,
        item["rows"],
        item["grid_proxy_sr"],
        item["mean_expected_grid_path_cost_m"],
        item["grid_attempt_spl_proxy"],
        item["mean_grid_path_utility_proxy"],
        item["returned_unreachable_rate"],
    )


def build_report(
    coverage: dict[str, Any],
    source_summary: dict[str, Any],
    primary_metrics: dict[str, Any],
    strict_metrics: dict[str, Any],
    comparisons: dict[str, Any],
    out_dir: Path,
) -> str:
    policies = [
        "scene_aligned_static_map",
        "always_top1",
        "always_top3",
        "always_top5",
        "fixed_uncertainty_topk_v0",
        "task_conditioned_budget_v0",
        "grid_path_aware_task_conditioned_budget_v0",
        "oracle_current_target",
    ]
    routine = comparisons["target_reachable_eval"]["significant_moved"]["routine_fetch"]
    high_value = comparisons["target_reachable_eval"]["significant_moved"]["high_value_fetch"]
    lines = [
        "# E002-M08 Source-Quality Filtered Grid Evaluation",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Query rows: {coverage['query_rows']}",
        f"- Target-reachable eval rows: {coverage['target_reachable_eval_rows']}",
        f"- Source-limited target-unreachable rows: {coverage['source_limited_rows']}",
        f"- All-candidates-reachable sensitivity rows: {coverage['all_candidates_reachable_eval_rows']}",
        f"- Target-reachable eval prediction rows: {coverage['target_reachable_eval_prediction_rows']}",
        f"- Target-reachable eval failure rows: {coverage['target_reachable_eval_failure_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Source Limit Summary",
        "",
        "| Source failure | Rows |",
        "| --- | ---: |",
    ]
    for key, value in source_summary["source_failure_counts"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Target-Reachable Significant Moved Rows",
            "",
            "### `routine_fetch`",
            "",
            "| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for policy in policies:
        lines.append(table_row(primary_metrics, "significant_moved", "routine_fetch", policy))

    lines.extend(
        [
            "",
            "### `high_value_fetch`",
            "",
            "| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for policy in policies:
        lines.append(table_row(primary_metrics, "significant_moved", "high_value_fetch", policy))

    lines.extend(
        [
            "",
            "## Key Comparisons",
            "",
            "- `routine_fetch` target-reachable significant moved `task_conditioned_budget_v0` `SR`: "
            f"{routine['task_sr']} vs `always_top5` {routine['top5_sr']} vs oracle {routine['oracle_sr']}.",
            "- `high_value_fetch` target-reachable significant moved `task_conditioned_budget_v0` `SR`: "
            f"{high_value['task_sr']} vs `always_top5` {high_value['top5_sr']} vs oracle {high_value['oracle_sr']}.",
            "- `grid_path_aware_task_conditioned_budget_v0` remains unsupported as an improvement claim: "
            f"routine significant moved `SR` delta vs task-conditioned is {routine['grid_aware_vs_task_sr_delta']}.",
            "",
            "## Strict Sensitivity",
            "",
            "- `all_candidates_reachable_eval` rows: "
            f"{coverage['all_candidates_reachable_eval_rows']}.",
            "- Significant moved `routine_fetch` rows under strict sensitivity: "
            f"{strict_metrics['significant_moved']['routine_fetch']['task_conditioned_budget_v0']['rows']}.",
            "- This strict view is a diagnostic, not the primary denominator, because it removes many hard candidate-set rows.",
            "",
            "## 논문 주장",
            "",
            "- E002-M08 supports reporting source-quality-filtered grid-path proxy metrics separately from source-limited rows.",
            "- E002-M08 supports using `target_reachable_eval` as the primary grid-path proxy denominator.",
            "- E002-M08 does not support a positive claim for naive `grid_path_aware_task_conditioned_budget_v0`.",
            "- E002-M08 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The filtered denominator makes the oracle upper bound interpretable: target-reachable oracle `SR` becomes 1.0.",
            "- The core method signal is still task-conditioned stale-memory suppression, not path-aware ordering.",
            "- Candidate-unreachable rows should remain a diagnostic because removing all of them leaves too few significant moved rows for the main claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E002-M08. Next action should decide whether to revise grid-aware scoring or move to E003 perception-noise expansion.",
            "",
            "## Outputs",
            "",
            "- `source_quality_rows.jsonl`",
            "- `source_limit_rows.jsonl`",
            "- `filtered_predictions.jsonl`",
            "- `target_reachable_failure_rows.jsonl`",
            "- `metrics.json`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.grid_dir / "grid_query_rows.jsonl")
    predictions = load_jsonl(args.eval_dir / "predictions.jsonl")
    target_source_rows = load_jsonl(args.source_dir / "target_source_rows.jsonl")

    source_quality_rows = build_source_quality_rows(
        query_rows,
        source_rows_by_uid(target_source_rows),
    )
    quality_by_uid = {row["row_uid"]: row for row in source_quality_rows}
    enriched_predictions = attach_source_quality(predictions, quality_by_uid)

    primary_uids = {
        row["row_uid"] for row in source_quality_rows if row["include_in_target_reachable_eval"]
    }
    strict_uids = {
        row["row_uid"]
        for row in source_quality_rows
        if row["include_in_all_candidates_reachable_eval"]
    }
    source_limit_rows = [
        row
        for row in source_quality_rows
        if row["source_quality_primary_mask"] == "source_limited_target_grid_unreachable"
    ]
    primary_predictions = [row for row in enriched_predictions if row["row_uid"] in primary_uids]
    strict_predictions = [row for row in enriched_predictions if row["row_uid"] in strict_uids]
    primary_failures = build_failure_rows(primary_predictions)
    strict_failures = build_failure_rows(strict_predictions)

    source_summary = summarize_source_limits(source_quality_rows)
    primary_metrics = summarize(primary_predictions)
    strict_metrics = summarize(strict_predictions)
    metrics = {
        "analysis_version": ANALYSIS_VERSION,
        "target_reachable_eval": primary_metrics,
        "all_candidates_reachable_eval": strict_metrics,
        "key_comparisons": {
            "target_reachable_eval": build_key_comparisons(
                primary_metrics,
                "target_reachable_eval",
            ),
            "all_candidates_reachable_eval": build_key_comparisons(
                strict_metrics,
                "all_candidates_reachable_eval",
            ),
        },
        "returned_unreachable_diagnostic": summarize_returned_unreachable(primary_predictions),
        "source_quality_summary": source_summary,
    }
    coverage = build_coverage(
        source_quality_rows,
        enriched_predictions,
        primary_predictions,
        strict_predictions,
        primary_failures,
        strict_failures,
        source_summary,
        primary_metrics,
        args.out_dir,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "source_quality_rows.jsonl", source_quality_rows)
    write_jsonl(args.out_dir / "source_limit_rows.jsonl", source_limit_rows)
    write_jsonl(args.out_dir / "filtered_predictions.jsonl", enriched_predictions)
    write_jsonl(args.out_dir / "target_reachable_failure_rows.jsonl", primary_failures)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(
            coverage,
            source_summary,
            primary_metrics,
            strict_metrics,
            metrics["key_comparisons"],
            args.out_dir,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "target_reachable_eval_rows": coverage["target_reachable_eval_rows"],
                "source_limited_rows": coverage["source_limited_rows"],
                "all_candidates_reachable_eval_rows": coverage[
                    "all_candidates_reachable_eval_rows"
                ],
                "routine_significant_task": primary_metrics["significant_moved"][
                    "routine_fetch"
                ]["task_conditioned_budget_v0"],
                "routine_significant_oracle": primary_metrics["significant_moved"][
                    "routine_fetch"
                ]["oracle_current_target"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
