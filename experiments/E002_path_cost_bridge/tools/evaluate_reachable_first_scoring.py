#!/usr/bin/env python3
"""Test reachable-first semantic grid scoring for E002."""

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
    build_failure_rows,
    grid_attempt_cost,
    instance_sort_key,
    load_jsonl,
    old_location_success,
    prediction_payload,
    safe_rate,
    task_conditioned_budget,
    target_rank,
    target_reachable_rank,
    write_json,
    write_jsonl,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRID_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M05_occupancy_grid_astar_v0"
DEFAULT_M08_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M08_source_quality_filtered_grid_eval_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E002-M09_reachable_first_scoring_v0"
ANALYSIS_VERSION = "e002_reachable_first_semantic_grid_scoring_v0"
BASE_POLICY = "task_conditioned_budget_v0"
NEW_POLICY = "reachable_first_task_conditioned_budget_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round6(sum(values) / len(values))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["row_uid"], []).append(row)
    return grouped


def index_by_uid(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_uid"]: row for row in rows}


def prediction_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["row_uid"], row["policy"]): row for row in rows}


def reachable_first_semantic_order(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (
            not bool(row["candidate_grid_reachable"]),
            row["candidate_rank_non_persistent"],
            -float(row["candidate_score_non_persistent"]),
            row["candidate_grid_path_cost_m"] is None,
            row["candidate_grid_path_cost_m"] if row["candidate_grid_path_cost_m"] is not None else 999999.0,
            instance_sort_key(row["candidate_instance_id"]),
        ),
    )


def predict_reachable_first(
    query: dict[str, Any],
    candidates: list[dict[str, Any]],
    quality: dict[str, Any],
) -> dict[str, Any]:
    candidate_count = len(candidates)
    returned_k, reason = task_conditioned_budget(query, candidate_count)

    if reason == "trusted_low_motion_memory":
        success = old_location_success(query)
        cost = float(query["target_grid_path_cost_m"] or 0.0) if success else 1.0
        failure = None if success else "target_grid_unreachable" if not query["target_grid_reachable"] else "static_map_localization_error"
        payload = prediction_payload(
            NEW_POLICY,
            query,
            success,
            cost,
            1,
            1 if success else None,
            1 if success else None,
            "reachable_first_preserve_trusted_low_motion_memory",
            None,
            True,
            0,
            failure,
        )
    else:
        ordered = reachable_first_semantic_order(candidates)
        rank = target_rank(ordered)
        reachable_rank = target_reachable_rank(ordered)
        success = reachable_rank is not None and reachable_rank <= returned_k
        target_rank_in_returned = reachable_rank if success else None
        if success:
            cost = grid_attempt_cost(ordered, returned_k, reachable_rank)
        else:
            cost = grid_attempt_cost(ordered, returned_k)
        returned = ordered[: min(returned_k, len(ordered))]
        returned_unreachable_count = sum(1 for row in returned if not row["candidate_grid_reachable"])
        if success:
            failure = None
        elif not query["target_grid_reachable"]:
            failure = "target_grid_unreachable"
        elif returned_unreachable_count:
            failure = "returned_unreachable_candidate"
        elif returned_k == 0:
            failure = "no_candidate_returned"
        elif rank is None:
            failure = "target_missing_from_candidates"
        elif rank > returned_k:
            failure = "target_outside_returned_budget"
        else:
            failure = "unknown_reachable_first_policy_failure"

        payload = prediction_payload(
            NEW_POLICY,
            query,
            success,
            cost,
            returned_k,
            rank,
            target_rank_in_returned,
            f"reachable_first_{reason}",
            "reachable_first_semantic_rank",
            False,
            returned_unreachable_count,
            failure,
        )

    payload["eval_version"] = ANALYSIS_VERSION
    payload["source_quality_primary_mask"] = quality["source_quality_primary_mask"]
    payload["source_quality_strict_mask"] = quality["source_quality_strict_mask"]
    payload["include_in_target_reachable_eval"] = quality["include_in_target_reachable_eval"]
    payload["include_in_all_candidates_reachable_eval"] = quality[
        "include_in_all_candidates_reachable_eval"
    ]
    payload["source_failure_type"] = quality["source_failure_type"]
    payload["grid_scoring_revision"] = "reachable_first_semantic_rank_v0"
    return payload


def build_comparison_rows(
    base_predictions: dict[tuple[str, str], dict[str, Any]],
    new_predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for new in new_predictions:
        base = base_predictions[(new["row_uid"], BASE_POLICY)]
        base_success = bool(base["grid_path_success"])
        new_success = bool(new["grid_path_success"])
        if base_success and not new_success:
            outcome = "success_loss"
        elif new_success and not base_success:
            outcome = "success_gain"
        elif new_success and base_success:
            outcome = "both_success"
        else:
            outcome = "both_fail"

        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": new["row_uid"],
                "base_row_uid": new["base_row_uid"],
                "pair_uid": new["pair_uid"],
                "task_context_id": new["task_context_id"],
                "row_band": new["row_band"],
                "object_label": new["object_label"],
                "source_quality_primary_mask": new["source_quality_primary_mask"],
                "source_quality_strict_mask": new["source_quality_strict_mask"],
                "comparison_outcome": outcome,
                "base_success": base_success,
                "reachable_first_success": new_success,
                "base_returned_unreachable_count": base["returned_unreachable_count"],
                "reachable_first_returned_unreachable_count": new["returned_unreachable_count"],
                "returned_unreachable_delta": int(new["returned_unreachable_count"])
                - int(base["returned_unreachable_count"]),
                "base_returned_location_count": base["returned_location_count"],
                "reachable_first_returned_location_count": new["returned_location_count"],
                "base_cost_m": base["expected_grid_path_cost_m"],
                "reachable_first_cost_m": new["expected_grid_path_cost_m"],
                "cost_delta_m": round6(
                    float(new["expected_grid_path_cost_m"]) - float(base["expected_grid_path_cost_m"])
                ),
                "base_attempt_spl_proxy": base["grid_attempt_spl_proxy"],
                "reachable_first_attempt_spl_proxy": new["grid_attempt_spl_proxy"],
                "base_utility": base["grid_path_utility_proxy"],
                "reachable_first_utility": new["grid_path_utility_proxy"],
                "utility_delta": round6(
                    float(new["grid_path_utility_proxy"]) - float(base["grid_path_utility_proxy"])
                ),
                "base_failure_type": base["grid_failure_type"],
                "reachable_first_failure_type": new["grid_failure_type"],
            }
        )
    return rows


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def summarize_policy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    successes = [row for row in rows if row["grid_path_success"]]
    returned_unreachable = [row for row in rows if int(row["returned_unreachable_count"]) > 0]
    success_rate = safe_rate(len(successes), len(rows))
    mean_cost = mean([float(row["expected_grid_path_cost_m"]) for row in rows])
    return {
        "rows": len(rows),
        "grid_proxy_sr": success_rate,
        "mean_expected_grid_path_cost_m": mean_cost,
        "grid_attempt_spl_proxy": mean([float(row["grid_attempt_spl_proxy"]) for row in rows]),
        "mean_grid_path_utility_proxy": mean([float(row["grid_path_utility_proxy"]) for row in rows]),
        "returned_unreachable_rows": len(returned_unreachable),
        "returned_unreachable_rate": safe_rate(len(returned_unreachable), len(rows)),
        "total_returned_unreachable_count": sum(int(row["returned_unreachable_count"]) for row in rows),
        "mean_returned_location_count": mean([float(row["returned_location_count"]) for row in rows]),
        "stale_old_location_fp_rate": safe_rate(
            sum(1 for row in stale if row["stale_old_location_fp"]),
            len(stale),
        ),
        "low_motion_preservation_rate": safe_rate(
            sum(1 for row in low_motion if row["low_motion_preserved"]),
            len(low_motion),
        ),
        "success_per_meter": round6(success_rate / mean_cost)
        if success_rate is not None and mean_cost and mean_cost > 0
        else None,
    }


def summarize_comparisons(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "status": "empty",
        }
    success_loss_rows = [row for row in rows if row["comparison_outcome"] == "success_loss"]
    success_gain_rows = [row for row in rows if row["comparison_outcome"] == "success_gain"]
    returned_delta = sum(int(row["returned_unreachable_delta"]) for row in rows)
    return {
        "rows": len(rows),
        "comparison_counts": counter_dict(Counter(row["comparison_outcome"] for row in rows)),
        "success_loss_rows": len(success_loss_rows),
        "success_gain_rows": len(success_gain_rows),
        "returned_unreachable_reduction_rows": sum(
            1 for row in rows if int(row["returned_unreachable_delta"]) < 0
        ),
        "returned_unreachable_increase_rows": sum(
            1 for row in rows if int(row["returned_unreachable_delta"]) > 0
        ),
        "returned_unreachable_delta_total": returned_delta,
        "mean_cost_delta_m": mean([float(row["cost_delta_m"]) for row in rows]),
        "mean_utility_delta": mean([float(row["utility_delta"]) for row in rows]),
        "gate_pass": len(success_loss_rows) == 0 and returned_delta < 0,
    }


def summarize_by_context(
    base_rows: list[dict[str, Any]],
    new_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for subset in ["all", "significant_moved", "mid_motion_review", "low_motion_control"]:
        output[subset] = {}
        subset_base = subset_rows(base_rows, subset)
        subset_new = subset_rows(new_rows, subset)
        subset_comp = subset_rows(comparison_rows, subset)
        for context in sorted({row["task_context_id"] for row in subset_new}):
            base_context = [row for row in subset_base if row["task_context_id"] == context]
            new_context = [row for row in subset_new if row["task_context_id"] == context]
            comp_context = [row for row in subset_comp if row["task_context_id"] == context]
            output[subset][context] = {
                BASE_POLICY: summarize_policy_rows(base_context),
                NEW_POLICY: summarize_policy_rows(new_context),
                "comparison": summarize_comparisons(comp_context),
            }
    return output


def build_summary(
    primary_base: list[dict[str, Any]],
    primary_new: list[dict[str, Any]],
    primary_comparison: list[dict[str, Any]],
    strict_base: list[dict[str, Any]],
    strict_new: list[dict[str, Any]],
    strict_comparison: list[dict[str, Any]],
) -> dict[str, Any]:
    primary_all = summarize_comparisons(primary_comparison)
    strict_all = summarize_comparisons(strict_comparison)
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": "reachable_first_scoring_gate_pass"
        if primary_all["gate_pass"]
        else "reachable_first_scoring_review_needed",
        "target_reachable_eval": summarize_by_context(
            primary_base,
            primary_new,
            primary_comparison,
        ),
        "all_candidates_reachable_eval": summarize_by_context(
            strict_base,
            strict_new,
            strict_comparison,
        ),
        "gate_summary": {
            "target_reachable_eval": primary_all,
            "all_candidates_reachable_eval": strict_all,
        },
        "claim_boundary": {
            "supported": [
                "reachable-first semantic scoring can be tested under the source-filtered grid-path proxy denominator",
                "returned-unreachable attempts can be reduced without recall loss if target_reachable_eval gate passes",
            ],
            "unsupported": [
                "real navigation SR/SPL",
                "deployable search policy",
                "collision-aware robot planning",
                "RGB-D/open-vocabulary perception robustness",
            ],
        },
    }


def table_row(metrics: dict[str, Any], policy: str) -> str:
    item = metrics[policy]
    return "| `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
        policy,
        item["rows"],
        item["grid_proxy_sr"],
        item["mean_expected_grid_path_cost_m"],
        item["grid_attempt_spl_proxy"],
        item["mean_grid_path_utility_proxy"],
        item["returned_unreachable_rate"],
        item["total_returned_unreachable_count"],
    )


def build_report(summary: dict[str, Any], coverage: dict[str, Any], out_dir: Path) -> str:
    routine = summary["target_reachable_eval"]["significant_moved"]["routine_fetch"]
    high_value = summary["target_reachable_eval"]["significant_moved"]["high_value_fetch"]
    gate = summary["gate_summary"]["target_reachable_eval"]
    lines = [
        "# E002-M09 Reachable-First Semantic Grid Scoring",
        "",
        "## Status",
        "",
        summary["status"],
        "",
        "## 사실",
        "",
        f"- Target-reachable eval rows: {coverage['target_reachable_eval_rows']}",
        f"- Strict all-candidates-reachable rows: {coverage['all_candidates_reachable_eval_rows']}",
        f"- Reachable-first prediction rows: {coverage['reachable_first_prediction_rows']}",
        f"- Target-reachable success loss rows: {gate['success_loss_rows']}",
        f"- Target-reachable success gain rows: {gate['success_gain_rows']}",
        f"- Target-reachable returned-unreachable delta total: {gate['returned_unreachable_delta_total']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Target-Reachable Significant Moved Rows",
        "",
        "### `routine_fetch`",
        "",
        "| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate | Returned-unreachable count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        table_row(routine, BASE_POLICY),
        table_row(routine, NEW_POLICY),
        "",
        "### `high_value_fetch`",
        "",
        "| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate | Returned-unreachable count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        table_row(high_value, BASE_POLICY),
        table_row(high_value, NEW_POLICY),
        "",
        "## Gate Summary",
        "",
        "| Scope | Rows | Success loss | Success gain | Returned-unreachable delta | Mean cost delta | Mean utility delta | Gate pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        "| `target_reachable_eval` | {rows} | {loss} | {gain} | {unreach} | {cost} | {utility} | {gate} |".format(
            rows=gate["rows"],
            loss=gate["success_loss_rows"],
            gain=gate["success_gain_rows"],
            unreach=gate["returned_unreachable_delta_total"],
            cost=gate["mean_cost_delta_m"],
            utility=gate["mean_utility_delta"],
            gate=gate["gate_pass"],
        ),
        "",
        "## 논문 주장",
        "",
        "- E002-M09 supports reachable-first semantic grid scoring only as a source-filtered grid-path proxy revision.",
        "- E002-M09 can support a returned-unreachable reduction claim if the gate passes with zero success loss.",
        "- E002-M09 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.",
        "",
        "## 에이전트 추론",
        "",
        "- This revision is safer than naive grid-path ordering because it preserves semantic rank among reachable candidates and only demotes grid-unreachable candidates.",
        "- A positive M09 result should be treated as method cleanup for E002, not as the main paper contribution by itself.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E002-M09. If accepted, the next experiment can move to E003 perception-noise expansion.",
        "",
        "## Outputs",
        "",
        "- `reachable_first_predictions.jsonl`",
        "- `comparison_rows.jsonl`",
        "- `strict_comparison_rows.jsonl`",
        "- `failure_rows.jsonl`",
        "- `metrics.json`",
        "- `coverage.json`",
        "- `report.md`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--m08-dir", type=Path, default=DEFAULT_M08_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.grid_dir / "grid_query_rows.jsonl")
    candidate_rows = load_jsonl(args.grid_dir / "grid_candidate_rows.jsonl")
    quality_rows = load_jsonl(args.m08_dir / "source_quality_rows.jsonl")
    m08_predictions = load_jsonl(args.m08_dir / "filtered_predictions.jsonl")
    m08_coverage = load_json(args.m08_dir / "coverage.json")

    quality_by_uid = index_by_uid(quality_rows)
    candidates_by_uid = group_by_uid(candidate_rows)
    base_prediction_by_key = prediction_index(m08_predictions)

    reachable_first_predictions = []
    for query in query_rows:
        quality = quality_by_uid[query["row_uid"]]
        if not quality["include_in_target_reachable_eval"]:
            continue
        reachable_first_predictions.append(
            predict_reachable_first(
                query,
                candidates_by_uid.get(query["row_uid"], []),
                quality,
            )
        )

    primary_uids = {row["row_uid"] for row in quality_rows if row["include_in_target_reachable_eval"]}
    strict_uids = {
        row["row_uid"] for row in quality_rows if row["include_in_all_candidates_reachable_eval"]
    }
    primary_base = [
        base_prediction_by_key[(uid, BASE_POLICY)]
        for uid in sorted(primary_uids)
    ]
    strict_base = [
        base_prediction_by_key[(uid, BASE_POLICY)]
        for uid in sorted(strict_uids)
    ]
    primary_new = reachable_first_predictions
    strict_new = [row for row in reachable_first_predictions if row["row_uid"] in strict_uids]
    primary_comparison = build_comparison_rows(base_prediction_by_key, primary_new)
    strict_comparison = [row for row in primary_comparison if row["row_uid"] in strict_uids]
    failure_rows = build_failure_rows(primary_new)

    summary = build_summary(
        primary_base,
        primary_new,
        primary_comparison,
        strict_base,
        strict_new,
        strict_comparison,
    )
    coverage = {
        "analysis_version": ANALYSIS_VERSION,
        "status": summary["status"],
        "input_grid_dir": str(args.grid_dir),
        "input_m08_dir": str(args.m08_dir),
        "query_rows": len(query_rows),
        "candidate_rows": len(candidate_rows),
        "target_reachable_eval_rows": len(primary_uids),
        "all_candidates_reachable_eval_rows": len(strict_uids),
        "reachable_first_prediction_rows": len(reachable_first_predictions),
        "failure_rows": len(failure_rows),
        "m08_target_reachable_eval_rows": m08_coverage["target_reachable_eval_rows"],
        "m08_source_limited_rows": m08_coverage["source_limited_rows"],
        "gate_condition": {
            "scope": "target_reachable_eval",
            "requires_success_loss_rows": 0,
            "requires_returned_unreachable_delta_total_below": 0,
        },
        "outputs": {
            "reachable_first_predictions": str(args.out_dir / "reachable_first_predictions.jsonl"),
            "comparison_rows": str(args.out_dir / "comparison_rows.jsonl"),
            "strict_comparison_rows": str(args.out_dir / "strict_comparison_rows.jsonl"),
            "failure_rows": str(args.out_dir / "failure_rows.jsonl"),
            "metrics": str(args.out_dir / "metrics.json"),
            "coverage": str(args.out_dir / "coverage.json"),
            "report": str(args.out_dir / "report.md"),
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "reachable_first_predictions.jsonl", reachable_first_predictions)
    write_jsonl(args.out_dir / "comparison_rows.jsonl", primary_comparison)
    write_jsonl(args.out_dir / "strict_comparison_rows.jsonl", strict_comparison)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", summary)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(summary, coverage, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": summary["status"],
                "target_reachable_eval": summary["gate_summary"]["target_reachable_eval"],
                "routine_significant": summary["target_reachable_eval"]["significant_moved"]["routine_fetch"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
