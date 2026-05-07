#!/usr/bin/env python3
"""Summarize E001 baseline failures and claim boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M03_baseline_evaluation_v0"
DEFAULT_QUERY_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E001-M04_failure_analysis_v0"
ANALYSIS_VERSION = "e001_failure_analysis_v0"
METHOD = "task_conditioned_budget_v0"
COMPARISON_POLICIES = [
    "scene_aligned_static_map",
    "label_nearest_current_observation",
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "oracle_current_target",
]


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


def key(row: dict[str, Any]) -> tuple[str, str]:
    return row["row_uid"], row["policy"]


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def group_predictions(predictions: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in predictions:
        grouped[row["row_uid"]][row["policy"]] = row
    return grouped


def summarize_counts(
    predictions: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    method_preds = [row for row in predictions if row["policy"] == METHOD]
    method_failures = [row for row in failures if row["policy"] == METHOD]
    return {
        "prediction_rows": len(predictions),
        "failure_rows": len(failures),
        "method_prediction_rows": len(method_preds),
        "method_failure_rows": len(method_failures),
        "failure_type_counts_all": dict(sorted(Counter(row["failure_type"] for row in failures).items())),
        "failure_policy_counts": dict(sorted(Counter(row["policy"] for row in failures).items())),
        "failure_context_counts": dict(sorted(Counter(row["task_context_id"] for row in failures).items())),
        "failure_row_band_counts": dict(sorted(Counter(row["row_band"] for row in failures).items())),
        "method_failure_type_counts": dict(sorted(Counter(row["failure_type"] for row in method_failures).items())),
        "method_failure_context_band_counts": {
            f"{context}|{band}|{failure_type}": count
            for (context, band, failure_type), count in sorted(
                Counter(
                    (row["task_context_id"], row["row_band"], row["failure_type"])
                    for row in method_failures
                ).items()
            )
        },
    }


def compare_method_to_policies(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = group_predictions(predictions)
    comparisons: dict[str, Counter] = {
        policy: Counter() for policy in COMPARISON_POLICIES
    }
    utility_delta: dict[str, list[float]] = {policy: [] for policy in COMPARISON_POLICIES}
    cost_delta: dict[str, list[float]] = {policy: [] for policy in COMPARISON_POLICIES}
    sr_delta: dict[str, list[float]] = {policy: [] for policy in COMPARISON_POLICIES}

    for policy_rows in grouped.values():
        method = policy_rows.get(METHOD)
        if method is None:
            continue
        for policy in COMPARISON_POLICIES:
            baseline = policy_rows.get(policy)
            if baseline is None:
                continue
            if method["search_success"] and not baseline["search_success"]:
                comparisons[policy]["method_success_baseline_fail"] += 1
            elif not method["search_success"] and baseline["search_success"]:
                comparisons[policy]["baseline_success_method_fail"] += 1
            elif method["search_success"] and baseline["search_success"]:
                comparisons[policy]["both_success"] += 1
            else:
                comparisons[policy]["both_fail"] += 1
            utility_delta[policy].append(float(method["task_utility"]) - float(baseline["task_utility"]))
            cost_delta[policy].append(float(method["expected_search_cost"]) - float(baseline["expected_search_cost"]))
            sr_delta[policy].append(float(method["search_success"]) - float(baseline["search_success"]))

    output = {}
    for policy in COMPARISON_POLICIES:
        total = sum(comparisons[policy].values())
        output[policy] = {
            "rows": total,
            **dict(sorted(comparisons[policy].items())),
            "mean_task_utility_delta": round_or_none(
                sum(utility_delta[policy]) / len(utility_delta[policy]) if utility_delta[policy] else None
            ),
            "mean_expected_search_cost_delta": round_or_none(
                sum(cost_delta[policy]) / len(cost_delta[policy]) if cost_delta[policy] else None
            ),
            "mean_proxy_sr_delta": round_or_none(
                sum(sr_delta[policy]) / len(sr_delta[policy]) if sr_delta[policy] else None
            ),
        }
    return output


def hard_cases(
    predictions: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    query_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = group_predictions(predictions)
    method_failure_uids = {
        row["row_uid"] for row in failures if row["policy"] == METHOD
    }
    rows = []
    for row_uid in sorted(method_failure_uids):
        method = grouped[row_uid][METHOD]
        query = query_by_uid[row_uid]
        top5 = grouped[row_uid].get("always_top5")
        oracle = grouped[row_uid].get("oracle_current_target")
        rows.append(
            {
                "row_uid": row_uid,
                "base_row_uid": method["base_row_uid"],
                "pair_uid": method["pair_uid"],
                "task_context_id": method["task_context_id"],
                "object_label": method["object_label"],
                "row_band": method["row_band"],
                "ambiguity_band": method["ambiguity_band"],
                "same_label_candidate_count": query["same_label_candidate_count"],
                "scene_aligned_static_planar_error_m": query["scene_aligned_static_planar_error_m"],
                "method_target_rank": method["target_rank"],
                "method_returned_location_count": method["returned_location_count"],
                "method_expected_search_cost": method["expected_search_cost"],
                "top5_success": top5["search_success"] if top5 else None,
                "oracle_success": oracle["search_success"] if oracle else None,
                "failure_type": "target_outside_returned_budget"
                if method["target_rank"] and method["target_rank"] > method["returned_location_count"]
                else "method_failure",
                "next_test": "E004 budget rule revision or E002 path-aware candidate ordering",
            }
        )
    return rows


def claim_boundary(metrics: dict[str, Any], eval_coverage: dict[str, Any], failure_summary: dict[str, Any]) -> dict[str, Any]:
    routine = metrics["significant_moved"]["routine_fetch"][METHOD]
    high_value = metrics["significant_moved"]["high_value_fetch"][METHOD]
    low_motion = metrics["low_motion_control"]["routine_fetch"][METHOD]
    static = metrics["significant_moved"]["routine_fetch"]["scene_aligned_static_map"]
    top5_high = metrics["significant_moved"]["high_value_fetch"]["always_top5"]
    oracle_high = metrics["significant_moved"]["high_value_fetch"]["oracle_current_target"]
    return {
        "safe_claims": [
            "E001 supports annotation-level semantic-pair dynamic object search proxy evaluation on locally ready 3RScan/3DSSG pairs.",
            "On significant moved rows, task_conditioned_budget_v0 suppresses stale old-location false positives relative to scene_aligned_static_map.",
            "Structured task context changes the search budget and creates a routine-vs-high-value tradeoff in proxy SR and ExpectedSearchCost.",
            "Low-motion rows are preserved under task_conditioned_budget_v0 in the current E001 data.",
        ],
        "safe_claim_evidence": {
            "validated_pair_count": eval_coverage.get("validated_pair_count"),
            "query_rows": eval_coverage.get("query_rows"),
            "significant_moved_rows_per_context": metrics["significant_moved"]["routine_fetch"][METHOD]["rows"],
            "routine_fetch_method_proxy_sr": routine["proxy_sr"],
            "routine_fetch_method_expected_search_cost": routine["mean_expected_search_cost"],
            "high_value_fetch_method_proxy_sr": high_value["proxy_sr"],
            "high_value_fetch_method_expected_search_cost": high_value["mean_expected_search_cost"],
            "static_map_stale_fp_rate": static["stale_old_location_fp_rate"],
            "method_stale_fp_rate": routine["stale_old_location_fp_rate"],
            "low_motion_preservation_rate": low_motion["low_motion_preservation_rate"],
            "high_value_equals_always_top5_proxy_sr": high_value["proxy_sr"] == top5_high["proxy_sr"],
            "method_below_oracle_proxy_sr": high_value["proxy_sr"] < oracle_high["proxy_sr"],
        },
        "weakened_or_partial_claims": [
            "Routine context improves search-cost behavior but does not maximize proxy SR against always_top5.",
            "High-value context matches always_top5 proxy SR on significant moved rows but does not close the oracle gap.",
            "Failure analysis still shows target_outside_returned_budget cases for task_conditioned_budget_v0.",
        ],
        "unsupported_claims": [
            "real navigation SR/SPL",
            "path-cost-aware search policy",
            "RGB-D perception robustness",
            "open-vocabulary perception robustness",
            "natural-language intention understanding",
            "learned task policy",
            "full 3RScan/3DSSG benchmark-scale conclusion",
        ],
        "unsupported_reasons": {
            "real_navigation": "E001 uses candidate-count ExpectedSearchCost and proxy SR/AttemptSPL; path_cost_ready is false.",
            "rgbd_or_open_vocab": "E001 uses annotation_semseg current candidates; eval coverage marks RGB-D and open-vocabulary perception as false.",
            "natural_language": "Task context is structured and controlled, not parsed from language.",
            "benchmark_scale": "Only 12 ready_minimal reference-rescan pairs are evaluated under the current local dataset.",
        },
        "next_required_evidence": [
            "E001 failure analysis review on hard target_outside_returned_budget rows.",
            "Additional pair staging to increase significant moved denominator.",
            "E002 path/search-cost bridge with candidate_path_cost_m and old-location dead-end cost.",
            "E003 RGB-D or open-vocabulary proposal replacement after sequence/proposal availability is staged.",
            "E004 task-context ablation after the clean E001 denominator is expanded.",
        ],
        "method_failure_rows": failure_summary["method_failure_rows"],
    }


def build_report(
    failure_summary: dict[str, Any],
    comparisons: dict[str, Any],
    boundary: dict[str, Any],
    hard_case_rows: list[dict[str, Any]],
    out_dir: Path,
) -> str:
    lines = [
        "# E001-M04 Failure Analysis",
        "",
        "## Status",
        "",
        "claim_boundary_ready",
        "",
        "## 사실",
        "",
        f"- Prediction rows: {failure_summary['prediction_rows']}",
        f"- Failure rows: {failure_summary['failure_rows']}",
        f"- `task_conditioned_budget_v0` failure rows: {failure_summary['method_failure_rows']}",
        f"- Hard case rows written: {len(hard_case_rows)}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Failure Types",
        "",
        "| Failure type | Count |",
        "| --- | ---: |",
    ]
    for name, count in failure_summary["failure_type_counts_all"].items():
        lines.append(f"| `{name}` | {count} |")

    lines.extend(
        [
            "",
            "## Method Failures",
            "",
            "| Context / band / failure | Count |",
            "| --- | ---: |",
        ]
    )
    for name, count in failure_summary["method_failure_context_band_counts"].items():
        lines.append(f"| `{name}` | {count} |")

    lines.extend(
        [
            "",
            "## Method vs Baselines",
            "",
            "| Baseline | Method success / baseline fail | Baseline success / method fail | Utility delta | Cost delta | proxy `SR` delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for policy, item in comparisons.items():
        lines.append(
            "| `{policy}` | {msbf} | {bsmf} | {ud} | {cd} | {sd} |".format(
                policy=policy,
                msbf=item.get("method_success_baseline_fail", 0),
                bsmf=item.get("baseline_success_method_fail", 0),
                ud=item["mean_task_utility_delta"],
                cd=item["mean_expected_search_cost_delta"],
                sd=item["mean_proxy_sr_delta"],
            )
        )

    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "Safe claims:",
        ]
    )
    lines.extend(f"- {item}" for item in boundary["safe_claims"])
    lines.extend(
        [
            "",
            "Unsupported claims:",
        ]
    )
    lines.extend(f"- {item}" for item in boundary["unsupported_claims"])
    lines.extend(
        [
            "",
            "## 에이전트 추론",
            "",
            "- E001 is useful as a clean proxy benchmark and denominator, but it is not yet a top-tier-complete embodied result.",
            "- The current method's main weakness is not stale old-location suppression; it is candidate-budget misses under bounded routine search.",
            "- E002 should convert candidate-count cost into path/search cost before any navigation-style claim.",
            "- E003 should replace `annotation_semseg` candidates before any perception robustness claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- No immediate decision is required. The next TODO can be additional staging or E002 path-cost preparation.",
            "",
            "## Outputs",
            "",
            "- `failure_summary.json`",
            "- `claim_boundary.json`",
            "- `hard_cases.jsonl`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--query-dir", type=Path, default=DEFAULT_QUERY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    predictions = load_jsonl(args.eval_dir / "predictions.jsonl")
    failures = load_jsonl(args.eval_dir / "failure_rows.jsonl")
    metrics = load_json(args.eval_dir / "metrics.json")
    eval_coverage = load_json(args.eval_dir / "coverage.json")
    query_rows = load_jsonl(args.query_dir / "query_rows.jsonl")
    query_by_uid = {row["row_uid"]: row for row in query_rows}

    failure_summary = {
        "analysis_version": ANALYSIS_VERSION,
        "eval_dir": str(args.eval_dir),
        "query_dir": str(args.query_dir),
        **summarize_counts(predictions, failures),
    }
    comparisons = compare_method_to_policies(predictions)
    hard_case_rows = hard_cases(predictions, failures, query_by_uid)
    boundary = claim_boundary(metrics, eval_coverage, failure_summary)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "failure_summary.json", failure_summary)
    write_json(args.out_dir / "method_vs_baselines.json", comparisons)
    write_json(args.out_dir / "claim_boundary.json", boundary)
    write_jsonl(args.out_dir / "hard_cases.jsonl", hard_case_rows)
    (args.out_dir / "report.md").write_text(
        build_report(failure_summary, comparisons, boundary, hard_case_rows, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "claim_boundary_ready",
                "failure_rows": failure_summary["failure_rows"],
                "method_failure_rows": failure_summary["method_failure_rows"],
                "hard_cases": len(hard_case_rows),
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
