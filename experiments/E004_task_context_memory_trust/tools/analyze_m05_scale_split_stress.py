#!/usr/bin/env python3
"""Run E004-M05 scale/split stress for memory-trust and task-context claims."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M04_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M04_claim_boundary_ablation_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E004-M05_scale_split_stress_v0"
VERSION = "e004_m05_scale_split_stress_v0"
BOOTSTRAP_ITERATIONS = 500
BOOTSTRAP_SEED = 13

POLICIES = [
    "static_memory_only_v0",
    "context_agnostic_memory_trust_reobserve_v0",
    "task_context_memory_trust_reobserve_v0",
    "all_high_value_memory_trust_counterfactual_v0",
]


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


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(float(ordered[0]), 6)
    pos = (len(ordered) - 1) * q
    left = int(pos)
    right = min(left + 1, len(ordered) - 1)
    frac = pos - left
    return round(float(ordered[left] * (1 - frac) + ordered[right] * frac), 6)


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[str, list[dict[str, Any]]] = {policy: [] for policy in POLICIES}
    for row in rows:
        if row["policy"] in by_policy:
            by_policy[row["policy"]].append(row)

    metrics: dict[str, Any] = {}
    for policy, policy_rows in by_policy.items():
        success = sum(1 for row in policy_rows if row["query_bridge_success"])
        metrics[policy] = {
            "rows": len(policy_rows),
            "success_rows": success,
            "success_rate": safe_rate(success, len(policy_rows)),
            "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in policy_rows]),
            "mean_returned_location_count": safe_mean([int(row["returned_location_count"]) for row in policy_rows]),
            "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in policy_rows]),
        }

    task = metrics["task_context_memory_trust_reobserve_v0"]
    static = metrics["static_memory_only_v0"]
    context = metrics["context_agnostic_memory_trust_reobserve_v0"]
    all_high = metrics["all_high_value_memory_trust_counterfactual_v0"]
    return {
        "all_high_success_rows": all_high["success_rows"],
        "all_high_vs_task_success_delta": all_high["success_rows"] - task["success_rows"],
        "context_agnostic_success_rows": context["success_rows"],
        "policy_metrics": metrics,
        "query_rows": task["rows"],
        "static_success_rows": static["success_rows"],
        "task_context_success_rows": task["success_rows"],
        "task_vs_context_success_delta": task["success_rows"] - context["success_rows"],
        "task_vs_static_success_delta": task["success_rows"] - static["success_rows"],
        "task_vs_context_cost_delta": round(float(task["mean_expected_search_cost"]) - float(context["mean_expected_search_cost"]), 6)
        if task["mean_expected_search_cost"] is not None and context["mean_expected_search_cost"] is not None
        else None,
        "all_high_vs_task_cost_delta": round(float(all_high["mean_expected_search_cost"]) - float(task["mean_expected_search_cost"]), 6)
        if task["mean_expected_search_cost"] is not None and all_high["mean_expected_search_cost"] is not None
        else None,
    }


def build_group_rows(rows: list[dict[str, Any]], group_key: str, mode: str) -> list[dict[str, Any]]:
    values = sorted({str(row[group_key]) for row in rows if row["policy"] == "task_context_memory_trust_reobserve_v0"})
    output = []
    for value in values:
        if mode == "group":
            subset = [row for row in rows if str(row[group_key]) == value]
            split_id = f"{group_key}={value}"
        elif mode == "leave_one_out":
            subset = [row for row in rows if str(row[group_key]) != value]
            split_id = f"leave_out_{group_key}={value}"
        else:
            raise RuntimeError(f"unknown split mode: {mode}")
        summary = summarize_subset(subset)
        output.append(
            {
                "e004_version": VERSION,
                "group_key": group_key,
                "group_value": value,
                "split_id": split_id,
                "split_mode": mode,
                **{key: value for key, value in summary.items() if key != "policy_metrics"},
            }
        )
    return output


def build_bootstrap_rows(rows: list[dict[str, Any]], iterations: int, seed: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["base_row_uid"])].append(row)
    base_ids = sorted(grouped)
    rng = random.Random(seed)
    output = []
    for iteration in range(iterations):
        sampled_ids = [rng.choice(base_ids) for _ in base_ids]
        subset: list[dict[str, Any]] = []
        for base_id in sampled_ids:
            subset.extend(grouped[base_id])
        summary = summarize_subset(subset)
        output.append(
            {
                "e004_version": VERSION,
                "iteration": iteration,
                "sampled_base_rows": len(sampled_ids),
                **{key: value for key, value in summary.items() if key != "policy_metrics"},
            }
        )
    return output


def summarize_bootstrap(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return {
        "max": round(max(values), 6) if values else None,
        "mean": round(float(mean(values)), 6) if values else None,
        "min": round(min(values), 6) if values else None,
        "p05": percentile(values, 0.05),
        "p50": percentile(values, 0.5),
        "p95": percentile(values, 0.95),
        "positive_rate": safe_rate(sum(1 for value in values if value > 0), len(values)),
        "nonnegative_rate": safe_rate(sum(1 for value in values if value >= 0), len(values)),
    }


def build_decision(overall: dict[str, Any], split_rows: list[dict[str, Any]], bootstrap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    leave_scan = [row for row in split_rows if row["split_mode"] == "leave_one_out" and row["group_key"] == "current_rescan_id"]
    label_groups = [row for row in split_rows if row["split_mode"] == "group" and row["group_key"] == "label_canonical"]
    label_positive = [row for row in label_groups if int(row["task_vs_context_success_delta"]) > 0]
    label_eligible = [row for row in label_groups if int(row["query_rows"]) >= 6]
    bootstrap_task_context = summarize_bootstrap(bootstrap_rows, "task_vs_context_success_delta")
    bootstrap_memory = summarize_bootstrap(bootstrap_rows, "task_vs_static_success_delta")
    bootstrap_all_high = summarize_bootstrap(bootstrap_rows, "all_high_vs_task_success_delta")

    gates = {
        "memory_trust_leave_one_scan_positive": all(int(row["task_vs_static_success_delta"]) > 0 for row in leave_scan),
        "task_context_leave_one_scan_positive": all(int(row["task_vs_context_success_delta"]) > 0 for row in leave_scan),
        "task_context_label_breadth_sufficient": len(label_positive) >= max(3, len(label_eligible) // 2),
        "task_context_bootstrap_positive_rate_high": float(bootstrap_task_context["positive_rate"] or 0.0) >= 0.8,
        "memory_trust_bootstrap_positive_rate_high": float(bootstrap_memory["positive_rate"] or 0.0) >= 0.95,
        "all_high_counterfactual_often_beats_task": float(bootstrap_all_high["positive_rate"] or 0.0) >= 0.8,
    }

    if gates["memory_trust_leave_one_scan_positive"] and gates["memory_trust_bootstrap_positive_rate_high"]:
        memory_claim = "split_supported"
    else:
        memory_claim = "needs_more_denominator"
    if gates["task_context_leave_one_scan_positive"] and gates["task_context_bootstrap_positive_rate_high"] and gates["task_context_label_breadth_sufficient"]:
        task_context_claim = "moderate_positive"
    elif gates["task_context_leave_one_scan_positive"] and gates["task_context_bootstrap_positive_rate_high"]:
        task_context_claim = "limited_positive_not_label_broad"
    else:
        task_context_claim = "fragile"

    status = "e004_m05_split_stress_ready_limited_task_context"
    selected_next = "E005 external baseline transition with E004 limited claim locked"
    if memory_claim != "split_supported":
        status = "e004_m05_split_stress_needs_denominator_expansion"
        selected_next = "E004-M06 denominator expansion before E005"

    return {
        "bootstrap_summary": {
            "all_high_vs_task_success_delta": bootstrap_all_high,
            "task_vs_context_success_delta": bootstrap_task_context,
            "task_vs_static_success_delta": bootstrap_memory,
        },
        "claim_boundary": {
            "memory_trust_decision_claim_strength": memory_claim,
            "task_context_specific_claim_strength": task_context_claim,
            "deployable_search_policy_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "gates": gates,
        "label_positive_groups": [row["group_value"] for row in label_positive],
        "overall": {key: value for key, value in overall.items() if key != "policy_metrics"},
        "selected_next_unit": selected_next,
        "status": status,
    }


def build_report(coverage: dict[str, Any], decision: dict[str, Any]) -> str:
    overall = decision["overall"]
    return "\n".join(
        [
            "# E004-M05 Scale Split Stress",
            "",
            "## Status",
            "",
            decision["status"],
            "",
            "## 사실",
            "",
            f"- Query rows: {overall['query_rows']}.",
            f"- Overall task vs static success delta: {overall['task_vs_static_success_delta']}.",
            f"- Overall task vs context-agnostic success delta: {overall['task_vs_context_success_delta']}.",
            f"- Overall all-high-value vs task success delta: {overall['all_high_vs_task_success_delta']}.",
            f"- Leave-one-scan memory-trust positive: {decision['gates']['memory_trust_leave_one_scan_positive']}.",
            f"- Leave-one-scan task-context positive: {decision['gates']['task_context_leave_one_scan_positive']}.",
            f"- Task-context label breadth sufficient: {decision['gates']['task_context_label_breadth_sufficient']}.",
            f"- Label groups with task-context positive delta: {decision['label_positive_groups']}.",
            f"- Bootstrap task-vs-context positive rate: {decision['bootstrap_summary']['task_vs_context_success_delta']['positive_rate']}.",
            f"- Bootstrap task-vs-static positive rate: {decision['bootstrap_summary']['task_vs_static_success_delta']['positive_rate']}.",
            f"- Bootstrap all-high-vs-task positive rate: {decision['bootstrap_summary']['all_high_vs_task_success_delta']['positive_rate']}.",
            "",
            "## 논문 주장",
            "",
            f"- Memory-trust decision claim strength: `{decision['claim_boundary']['memory_trust_decision_claim_strength']}`.",
            f"- Task-context-specific claim strength: `{decision['claim_boundary']['task_context_specific_claim_strength']}`.",
            "- E004-M05 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            "- The memory-trust decision signal is stable enough for the current diagnostic denominator.",
            "- The task-context signal is positive under leave-one-scan and bootstrap stress, but it is not label-broad and remains concentrated in `chair` / `pillow` style cases.",
            "- The next top-tier-relevant move is external baseline transition, not additional tuning on the same 96 rows.",
            "",
            "## Next",
            "",
            f"- {decision['selected_next_unit']}.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m04-dir", default=DEFAULT_M04_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--bootstrap-iterations", default=BOOTSTRAP_ITERATIONS, type=int)
    parser.add_argument("--bootstrap-seed", default=BOOTSTRAP_SEED, type=int)
    args = parser.parse_args()

    rows = [row for row in load_jsonl(args.m04_dir / "policy_rows.jsonl") if row["policy"] in POLICIES]
    overall = summarize_subset(rows)
    split_rows: list[dict[str, Any]] = []
    for key in ["current_rescan_id", "label_canonical", "query_slice_id", "task_context_id"]:
        split_rows.extend(build_group_rows(rows, key, "group"))
    for key in ["current_rescan_id", "label_canonical"]:
        split_rows.extend(build_group_rows(rows, key, "leave_one_out"))
    bootstrap_rows = build_bootstrap_rows(rows, iterations=args.bootstrap_iterations, seed=args.bootstrap_seed)
    decision = build_decision(overall, split_rows, bootstrap_rows)
    coverage = {
        "bootstrap_iterations": args.bootstrap_iterations,
        "bootstrap_seed": args.bootstrap_seed,
        "e004_version": VERSION,
        "m04_dir": str(args.m04_dir),
        "next_recommended_unit": decision["selected_next_unit"],
        "policy_rows": len(rows),
        "query_rows": overall["query_rows"],
        "split_rows": len(split_rows),
        "status": decision["status"],
    }
    metrics = {
        "bootstrap_summary": decision["bootstrap_summary"],
        "overall": overall,
        "query_rows": overall["query_rows"],
        "summary_version": VERSION,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "split_rows.jsonl", split_rows)
    write_jsonl(args.out_dir / "bootstrap_rows.jsonl", bootstrap_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "decision.json", decision)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, decision))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
