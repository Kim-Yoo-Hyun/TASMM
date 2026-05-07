#!/usr/bin/env python3
"""Analyze E003 clean-vs-noisy robustness and failure boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M03_noisy_policy_eval_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M04_robustness_failure_analysis_v0"
ANALYSIS_VERSION = "e003_robustness_failure_analysis_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
STRESS_PROFILE = "annotation_score_jitter_v0"
PRIMARY_POLICIES = [
    "task_conditioned_budget_v0",
    "reachable_first_task_conditioned_budget_v0",
]
REPORT_POLICIES = [
    "scene_aligned_static_map",
    "always_top1",
    "always_top3",
    "always_top5",
    "fixed_uncertainty_topk_v0",
    "task_conditioned_budget_v0",
    "reachable_first_task_conditioned_budget_v0",
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


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round6(num / den)


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round6(sum(values) / len(values))


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def index_predictions(predictions: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (row["original_row_uid"], row["policy"], row["proposal_noise_profile_id"]): row
        for row in predictions
    }


def target_rank_delta(clean: dict[str, Any], stress: dict[str, Any]) -> int | None:
    if clean["target_rank"] is None or stress["target_rank"] is None:
        return None
    return int(stress["target_rank"]) - int(clean["target_rank"])


def transition_label(clean_success: bool, stress_success: bool) -> str:
    if clean_success and stress_success:
        return "stable_success"
    if clean_success and not stress_success:
        return "noise_regression"
    if not clean_success and stress_success:
        return "noise_improvement"
    return "stable_failure"


def boundary_type(clean: dict[str, Any], stress: dict[str, Any], transition: str) -> str:
    if transition == "noise_regression":
        if stress["target_rank"] is not None and stress["target_rank"] > stress["returned_location_count"]:
            return "rank_noise_pushes_target_outside_budget"
        if int(stress["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
            return "rank_noise_increases_unreachable_returns"
        return "noise_regression_other"
    if transition == "stable_failure":
        if stress["stale_old_location_fp"]:
            return "stale_memory_static_failure"
        if stress["target_rank"] is not None and stress["target_rank"] > stress["returned_location_count"]:
            return "budget_boundary_persistent"
        if stress["returns_old_location"]:
            return "old_location_outside_threshold"
        return "persistent_failure_other"
    if transition == "noise_improvement":
        return "rank_noise_moves_target_inside_budget"
    return "stable_success"


def build_transition_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = index_predictions(predictions)
    keys = sorted(
        {
            (row["original_row_uid"], row["policy"])
            for row in predictions
            if row["proposal_noise_profile_id"] == REFERENCE_PROFILE
        }
    )
    rows = []
    for original_row_uid, policy in keys:
        clean = index[(original_row_uid, policy, REFERENCE_PROFILE)]
        stress = index[(original_row_uid, policy, STRESS_PROFILE)]
        clean_success = bool(clean["search_success"])
        stress_success = bool(stress["search_success"])
        transition = transition_label(clean_success, stress_success)
        rank_delta = target_rank_delta(clean, stress)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": original_row_uid,
                "base_row_uid": clean["base_row_uid"],
                "pair_uid": clean["pair_uid"],
                "policy": policy,
                "task_context_id": clean["task_context_id"],
                "row_band": clean["row_band"],
                "object_label": clean["object_label"],
                "ambiguity_band": clean["ambiguity_band"],
                "old_memory_is_stale": clean["old_memory_is_stale"],
                "transition": transition,
                "boundary_type": boundary_type(clean, stress, transition),
                "clean_success": clean_success,
                "stress_success": stress_success,
                "clean_target_rank": clean["target_rank"],
                "stress_target_rank": stress["target_rank"],
                "target_rank_delta": rank_delta,
                "clean_returned_location_count": clean["returned_location_count"],
                "stress_returned_location_count": stress["returned_location_count"],
                "returned_location_count_delta": int(stress["returned_location_count"])
                - int(clean["returned_location_count"]),
                "clean_expected_search_cost": clean["expected_search_cost"],
                "stress_expected_search_cost": stress["expected_search_cost"],
                "expected_search_cost_delta": round6(
                    float(stress["expected_search_cost"]) - float(clean["expected_search_cost"])
                ),
                "clean_attempt_spl_proxy": clean["attempt_spl_proxy"],
                "stress_attempt_spl_proxy": stress["attempt_spl_proxy"],
                "attempt_spl_delta": round6(
                    float(stress["attempt_spl_proxy"]) - float(clean["attempt_spl_proxy"])
                ),
                "clean_task_utility": clean["task_utility"],
                "stress_task_utility": stress["task_utility"],
                "task_utility_delta": round6(float(stress["task_utility"]) - float(clean["task_utility"])),
                "clean_returned_unreachable_count": clean["returned_unreachable_count"],
                "stress_returned_unreachable_count": stress["returned_unreachable_count"],
                "returned_unreachable_count_delta": int(stress["returned_unreachable_count"])
                - int(clean["returned_unreachable_count"]),
                "target_retained_clean": clean["target_retained"],
                "target_retained_stress": stress["target_retained"],
                "uses_real_rgbd_perception": stress["uses_real_rgbd_perception"],
                "uses_open_vocab_perception": stress["uses_open_vocab_perception"],
            }
        )
    return rows


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "clean_proxy_sr": None,
            "stress_proxy_sr": None,
            "proxy_sr_delta": None,
            "noise_regression_rate": None,
        }
    clean_success = sum(1 for row in rows if row["clean_success"])
    stress_success = sum(1 for row in rows if row["stress_success"])
    transition_counts = Counter(row["transition"] for row in rows)
    boundary_counts = Counter(row["boundary_type"] for row in rows)
    rank_deltas = [float(row["target_rank_delta"]) for row in rows if row["target_rank_delta"] is not None]
    return {
        "rows": len(rows),
        "clean_proxy_sr": safe_rate(clean_success, len(rows)),
        "stress_proxy_sr": safe_rate(stress_success, len(rows)),
        "proxy_sr_delta": round6((stress_success - clean_success) / len(rows)),
        "noise_regression_rows": transition_counts["noise_regression"],
        "noise_regression_rate": safe_rate(transition_counts["noise_regression"], len(rows)),
        "noise_improvement_rows": transition_counts["noise_improvement"],
        "stable_failure_rows": transition_counts["stable_failure"],
        "stable_success_rows": transition_counts["stable_success"],
        "target_rank_worse_rows": sum(1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] > 0),
        "target_rank_better_rows": sum(1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] < 0),
        "target_rank_same_rows": sum(1 for row in rows if row["target_rank_delta"] == 0),
        "mean_target_rank_delta": mean(rank_deltas),
        "mean_expected_search_cost_delta": mean([float(row["expected_search_cost_delta"]) for row in rows]),
        "mean_attempt_spl_delta": mean([float(row["attempt_spl_delta"]) for row in rows]),
        "mean_task_utility_delta": mean([float(row["task_utility_delta"]) for row in rows]),
        "returned_unreachable_event_delta": sum(
            1
            for row in rows
            if int(row["stress_returned_unreachable_count"]) > 0
        )
        - sum(1 for row in rows if int(row["clean_returned_unreachable_count"]) > 0),
        "transition_counts": counter_dict(transition_counts),
        "boundary_counts": counter_dict(boundary_counts),
    }


def build_summary_tables(transition_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "all": summarize_subset(transition_rows),
        "by_policy": {},
        "by_policy_context_band": {},
        "stress_reachable_vs_task": {},
        "primary_policy_hard_labels": {},
        "primary_policy_hard_ambiguity": {},
    }
    for policy in sorted({row["policy"] for row in transition_rows}):
        rows = [row for row in transition_rows if row["policy"] == policy]
        output["by_policy"][policy] = summarize_subset(rows)
    for key in sorted({(row["policy"], row["task_context_id"], row["row_band"]) for row in transition_rows}):
        policy, context, band = key
        rows = [
            row
            for row in transition_rows
            if row["policy"] == policy and row["task_context_id"] == context and row["row_band"] == band
        ]
        output["by_policy_context_band"][f"{policy}|{context}|{band}"] = summarize_subset(rows)

    primary_regressions = [
        row
        for row in transition_rows
        if row["policy"] in PRIMARY_POLICIES and row["transition"] == "noise_regression"
    ]
    output["stress_reachable_vs_task"] = build_reachable_vs_task_summary(transition_rows)
    output["primary_policy_hard_labels"] = counter_dict(Counter(row["object_label"] for row in primary_regressions))
    output["primary_policy_hard_ambiguity"] = counter_dict(Counter(row["ambiguity_band"] for row in primary_regressions))
    return output


def compare_reachable_vs_task_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_uid: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row["policy"] in PRIMARY_POLICIES:
            by_uid[row["original_row_uid"]][row["policy"]] = row

    paired = [
        pair
        for pair in by_uid.values()
        if "task_conditioned_budget_v0" in pair
        and "reachable_first_task_conditioned_budget_v0" in pair
    ]
    if not paired:
        return {
            "rows": 0,
            "task_stress_proxy_sr": None,
            "reachable_stress_proxy_sr": None,
            "stress_proxy_sr_delta_reachable_minus_task": None,
            "stress_unreachable_event_delta_reachable_minus_task": None,
        }

    task_success = sum(1 for pair in paired if pair["task_conditioned_budget_v0"]["stress_success"])
    reachable_success = sum(
        1 for pair in paired if pair["reachable_first_task_conditioned_budget_v0"]["stress_success"]
    )
    task_unreachable_events = sum(
        1
        for pair in paired
        if int(pair["task_conditioned_budget_v0"]["stress_returned_unreachable_count"]) > 0
    )
    reachable_unreachable_events = sum(
        1
        for pair in paired
        if int(pair["reachable_first_task_conditioned_budget_v0"]["stress_returned_unreachable_count"]) > 0
    )
    unreachable_count_deltas = [
        int(pair["reachable_first_task_conditioned_budget_v0"]["stress_returned_unreachable_count"])
        - int(pair["task_conditioned_budget_v0"]["stress_returned_unreachable_count"])
        for pair in paired
    ]
    cost_deltas = [
        float(pair["reachable_first_task_conditioned_budget_v0"]["stress_expected_search_cost"])
        - float(pair["task_conditioned_budget_v0"]["stress_expected_search_cost"])
        for pair in paired
    ]
    return {
        "rows": len(paired),
        "task_stress_proxy_sr": safe_rate(task_success, len(paired)),
        "reachable_stress_proxy_sr": safe_rate(reachable_success, len(paired)),
        "stress_proxy_sr_delta_reachable_minus_task": round6((reachable_success - task_success) / len(paired)),
        "reachable_success_gain_rows": sum(
            1
            for pair in paired
            if pair["reachable_first_task_conditioned_budget_v0"]["stress_success"]
            and not pair["task_conditioned_budget_v0"]["stress_success"]
        ),
        "reachable_success_loss_rows": sum(
            1
            for pair in paired
            if pair["task_conditioned_budget_v0"]["stress_success"]
            and not pair["reachable_first_task_conditioned_budget_v0"]["stress_success"]
        ),
        "task_unreachable_event_rate": safe_rate(task_unreachable_events, len(paired)),
        "reachable_unreachable_event_rate": safe_rate(reachable_unreachable_events, len(paired)),
        "stress_unreachable_event_delta_reachable_minus_task": round6(
            (reachable_unreachable_events - task_unreachable_events) / len(paired)
        ),
        "mean_unreachable_count_delta_reachable_minus_task": mean([float(item) for item in unreachable_count_deltas]),
        "mean_expected_search_cost_delta_reachable_minus_task": mean(cost_deltas),
    }


def build_reachable_vs_task_summary(transition_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "all": compare_reachable_vs_task_subset(transition_rows),
    }
    for context in sorted({row["task_context_id"] for row in transition_rows}):
        rows = [row for row in transition_rows if row["task_context_id"] == context]
        output[f"task_context:{context}"] = compare_reachable_vs_task_subset(rows)
    for band in sorted({row["row_band"] for row in transition_rows}):
        rows = [row for row in transition_rows if row["row_band"] == band]
        output[f"row_band:{band}"] = compare_reachable_vs_task_subset(rows)
    for context, band in sorted({(row["task_context_id"], row["row_band"]) for row in transition_rows}):
        rows = [
            row
            for row in transition_rows
            if row["task_context_id"] == context and row["row_band"] == band
        ]
        output[f"{context}|{band}"] = compare_reachable_vs_task_subset(rows)
    return output


def build_policy_delta_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for policy, item in summary["by_policy"].items():
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "policy": policy,
                "rows": item["rows"],
                "clean_proxy_sr": item["clean_proxy_sr"],
                "stress_proxy_sr": item["stress_proxy_sr"],
                "proxy_sr_delta": item["proxy_sr_delta"],
                "noise_regression_rows": item["noise_regression_rows"],
                "noise_improvement_rows": item["noise_improvement_rows"],
                "mean_target_rank_delta": item["mean_target_rank_delta"],
                "mean_expected_search_cost_delta": item["mean_expected_search_cost_delta"],
                "mean_attempt_spl_delta": item["mean_attempt_spl_delta"],
                "mean_task_utility_delta": item["mean_task_utility_delta"],
                "returned_unreachable_event_delta": item["returned_unreachable_event_delta"],
            }
        )
    return rows


def build_hard_failure_rows(transition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in transition_rows:
        if row["policy"] not in PRIMARY_POLICIES:
            continue
        if row["transition"] not in {"noise_regression", "stable_failure"}:
            continue
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": row["original_row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "policy": row["policy"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "ambiguity_band": row["ambiguity_band"],
                "transition": row["transition"],
                "boundary_type": row["boundary_type"],
                "clean_target_rank": row["clean_target_rank"],
                "stress_target_rank": row["stress_target_rank"],
                "target_rank_delta": row["target_rank_delta"],
                "stress_returned_location_count": row["stress_returned_location_count"],
                "expected_search_cost_delta": row["expected_search_cost_delta"],
                "task_utility_delta": row["task_utility_delta"],
                "next_test": "budget calibration or additional noise profile"
                if row["boundary_type"] == "rank_noise_pushes_target_outside_budget"
                else "separate persistent budget boundary from perception-noise regression",
            }
        )
    return rows


def build_claim_boundary(
    coverage: dict[str, Any],
    summary: dict[str, Any],
    hard_failure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    task_all = summary["by_policy"]["task_conditioned_budget_v0"]
    reachable_all = summary["by_policy"]["reachable_first_task_conditioned_budget_v0"]
    task_sig_routine = summary["by_policy_context_band"][
        "task_conditioned_budget_v0|routine_fetch|significant_moved"
    ]
    reachable_sig_routine = summary["by_policy_context_band"][
        "reachable_first_task_conditioned_budget_v0|routine_fetch|significant_moved"
    ]
    always_top5_sig_routine = summary["by_policy_context_band"][
        "always_top5|routine_fetch|significant_moved"
    ]
    reachable_vs_task_sig_routine = summary["stress_reachable_vs_task"][
        "routine_fetch|significant_moved"
    ]
    return {
        "status": "robustness_boundary_ready",
        "safe_claims": [
            "E003 currently supports controlled annotation-proxy ranking-noise evaluation.",
            "`task_conditioned_budget_v0` and `reachable_first_task_conditioned_budget_v0` keep target-retained denominators explicit under score/rank perturbation.",
            "`reachable_first_task_conditioned_budget_v0` can reduce returned-unreachable attempts, but this is an occupancy-grid proxy effect.",
        ],
        "weakened_or_partial_claims": [
            "Ranking noise causes measurable proxy SR and utility degradation for `task_conditioned_budget_v0` on significant moved `routine_fetch` rows.",
            "The reachable-first variant lowers unreachable returns but does not recover the observed ranking-noise success drop.",
            "`always_top5` can be more robust to target-preserving ranking noise at the cost of larger candidate budgets.",
        ],
        "unsupported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary perception robustness",
            "real navigation `SR` / `SPL`",
            "detector proposal recall robustness",
            "natural-language intention understanding",
        ],
        "unsupported_reasons": {
            "real_perception": "M03/M04 use annotation-proxy candidates; coverage reports uses_real_rgbd_perception=false and uses_open_vocab_perception=false.",
            "proposal_recall": "The active stress profile preserves target presence; target-drop profiles are not included.",
            "navigation": "E003 only attaches occupancy-grid candidate reachability as a proxy signal; it does not execute navigation.",
            "language": "Task context remains structured metadata.",
        },
        "key_evidence": {
            "prediction_rows": coverage["prediction_rows"],
            "candidate_grid_signal_rows": coverage["candidate_grid_signal_rows"],
            "target_drop_profiles_included": coverage["target_drop_profiles_included"],
            "task_all_proxy_sr_delta": task_all["proxy_sr_delta"],
            "task_all_noise_regression_rows": task_all["noise_regression_rows"],
            "reachable_all_proxy_sr_delta": reachable_all["proxy_sr_delta"],
            "reachable_all_returned_unreachable_event_delta": reachable_all["returned_unreachable_event_delta"],
            "task_significant_routine_proxy_sr_delta": task_sig_routine["proxy_sr_delta"],
            "task_significant_routine_cost_delta": task_sig_routine["mean_expected_search_cost_delta"],
            "reachable_significant_routine_proxy_sr_delta": reachable_sig_routine["proxy_sr_delta"],
            "reachable_significant_routine_returned_unreachable_event_delta": reachable_sig_routine[
                "returned_unreachable_event_delta"
            ],
            "reachable_vs_task_significant_routine_stress_sr_delta": reachable_vs_task_sig_routine[
                "stress_proxy_sr_delta_reachable_minus_task"
            ],
            "reachable_vs_task_significant_routine_unreachable_event_delta": reachable_vs_task_sig_routine[
                "stress_unreachable_event_delta_reachable_minus_task"
            ],
            "always_top5_significant_routine_proxy_sr_delta": always_top5_sig_routine["proxy_sr_delta"],
            "primary_hard_failure_rows": len(hard_failure_rows),
        },
        "next_required_evidence": [
            "E003-M05 should either add a controlled target-drop/false-positive/centroid-jitter profile or stage real RGB-D/open-vocabulary proposals.",
            "If top-tier claim targets perception robustness, real proposal generation must replace annotation-proxy candidates.",
            "If near-term implementation stays annotation-proxy, next stress should separate target dropout from rank-only noise.",
        ],
    }


def build_coverage(
    eval_coverage: dict[str, Any],
    transition_rows: list[dict[str, Any]],
    hard_failure_rows: list[dict[str, Any]],
    out_dir: Path,
) -> dict[str, Any]:
    expected_transition_rows = eval_coverage["noisy_query_rows"] // 2 * len(eval_coverage["policies"])
    status = "robustness_boundary_ready"
    if len(transition_rows) != expected_transition_rows:
        status = "review_needed"
    if eval_coverage["target_drop_profiles_included"]:
        status = "review_needed"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "input_dir": eval_coverage["outputs"]["predictions"],
        "reference_profile": REFERENCE_PROFILE,
        "stress_profile": STRESS_PROFILE,
        "policies": eval_coverage["policies"],
        "expected_transition_rows": expected_transition_rows,
        "transition_rows": len(transition_rows),
        "hard_failure_rows": len(hard_failure_rows),
        "target_drop_profiles_included": eval_coverage["target_drop_profiles_included"],
        "uses_annotation_proxy_noise": eval_coverage["uses_annotation_proxy_noise"],
        "uses_real_rgbd_perception": eval_coverage["uses_real_rgbd_perception"],
        "uses_open_vocab_perception": eval_coverage["uses_open_vocab_perception"],
        "uses_real_navigation": eval_coverage["uses_real_navigation"],
        "outputs": {
            "transition_rows": str(out_dir / "transition_rows.jsonl"),
            "hard_failure_rows": str(out_dir / "hard_failure_rows.jsonl"),
            "policy_delta_rows": str(out_dir / "policy_delta_rows.jsonl"),
            "summary": str(out_dir / "summary.json"),
            "claim_boundary": str(out_dir / "claim_boundary.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    coverage: dict[str, Any],
    summary: dict[str, Any],
    claim_boundary: dict[str, Any],
    out_dir: Path,
) -> str:
    task_sig_routine = summary["by_policy_context_band"][
        "task_conditioned_budget_v0|routine_fetch|significant_moved"
    ]
    reachable_sig_routine = summary["by_policy_context_band"][
        "reachable_first_task_conditioned_budget_v0|routine_fetch|significant_moved"
    ]
    reachable_vs_task_sig_routine = summary["stress_reachable_vs_task"][
        "routine_fetch|significant_moved"
    ]
    lines = [
        "# E003-M04 Robustness Failure Analysis",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Transition rows: {coverage['transition_rows']}",
        f"- Hard failure rows: {coverage['hard_failure_rows']}",
        f"- Reference profile: `{coverage['reference_profile']}`",
        f"- Stress profile: `{coverage['stress_profile']}`",
        f"- Target-drop profiles included: {coverage['target_drop_profiles_included']}",
        f"- Uses real RGB-D perception: {coverage['uses_real_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocab_perception']}",
        f"- Uses real navigation: {coverage['uses_real_navigation']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch` Delta",
        "",
        "| Policy | clean `SR` | stress `SR` | delta `SR` | noise regressions | cost delta | `AttemptSPL` delta | utility delta | unreachable event delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in [
        "always_top1",
        "always_top3",
        "always_top5",
        "task_conditioned_budget_v0",
        "reachable_first_task_conditioned_budget_v0",
    ]:
        item = summary["by_policy_context_band"][f"{policy}|routine_fetch|significant_moved"]
        lines.append(
            "| `{policy}` | {clean} | {stress} | {sr_delta} | {regressions} | {cost_delta} | {spl_delta} | {utility_delta} | {unreach_delta} |".format(
                policy=policy,
                clean=item["clean_proxy_sr"],
                stress=item["stress_proxy_sr"],
                sr_delta=item["proxy_sr_delta"],
                regressions=item["noise_regression_rows"],
                cost_delta=item["mean_expected_search_cost_delta"],
                spl_delta=item["mean_attempt_spl_delta"],
                utility_delta=item["mean_task_utility_delta"],
                unreach_delta=item["returned_unreachable_event_delta"],
            )
        )

    lines.extend(
        [
            "",
            "## Hard Boundary",
            "",
            f"- `task_conditioned_budget_v0` significant moved `routine_fetch` delta `SR`: {task_sig_routine['proxy_sr_delta']}",
            f"- `task_conditioned_budget_v0` significant moved `routine_fetch` noise regression rows: {task_sig_routine['noise_regression_rows']}",
            f"- `reachable_first_task_conditioned_budget_v0` significant moved `routine_fetch` delta `SR`: {reachable_sig_routine['proxy_sr_delta']}",
            f"- `reachable_first_task_conditioned_budget_v0` stress-vs-clean returned-unreachable event delta: {reachable_sig_routine['returned_unreachable_event_delta']}",
            f"- Noisy `reachable_first_task_conditioned_budget_v0` vs noisy `task_conditioned_budget_v0` returned-unreachable event delta: {reachable_vs_task_sig_routine['stress_unreachable_event_delta_reachable_minus_task']}",
            f"- Noisy `reachable_first_task_conditioned_budget_v0` vs noisy `task_conditioned_budget_v0` proxy `SR` delta: {reachable_vs_task_sig_routine['stress_proxy_sr_delta_reachable_minus_task']}",
            f"- Primary hard label counts: {claim_boundary['key_evidence'].get('primary_hard_failure_rows')} rows total; see `hard_failure_rows.jsonl`.",
            "",
            "## 논문 주장",
            "",
        ]
    )
    for item in claim_boundary["safe_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 에이전트 추론", ""])
    for item in claim_boundary["weakened_or_partial_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Unsupported Claims", ""])
    for item in claim_boundary["unsupported_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 사용자 판단 필요", ""])
    lines.append("- None for M04. The next implementation choice is whether E003-M05 stages real proposal sources or adds another controlled annotation-proxy stress profile.")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `transition_rows.jsonl`",
            "- `hard_failure_rows.jsonl`",
            "- `policy_delta_rows.jsonl`",
            "- `summary.json`",
            "- `claim_boundary.json`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    predictions = load_jsonl(args.eval_dir / "predictions.jsonl")
    eval_coverage = load_json(args.eval_dir / "coverage.json")
    transition_rows = build_transition_rows(predictions)
    summary = build_summary_tables(transition_rows)
    policy_delta_rows = build_policy_delta_rows(summary)
    hard_failure_rows = build_hard_failure_rows(transition_rows)
    claim_boundary = build_claim_boundary(eval_coverage, summary, hard_failure_rows)
    coverage = build_coverage(eval_coverage, transition_rows, hard_failure_rows, args.out_dir)

    if coverage["status"] != "robustness_boundary_ready":
        claim_boundary["status"] = coverage["status"]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "transition_rows.jsonl", transition_rows)
    write_jsonl(args.out_dir / "hard_failure_rows.jsonl", hard_failure_rows)
    write_jsonl(args.out_dir / "policy_delta_rows.jsonl", policy_delta_rows)
    write_json(args.out_dir / "summary.json", summary)
    write_json(args.out_dir / "claim_boundary.json", claim_boundary)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(coverage, summary, claim_boundary, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "transition_rows": coverage["transition_rows"],
                "hard_failure_rows": coverage["hard_failure_rows"],
                "task_significant_routine": summary["by_policy_context_band"][
                    "task_conditioned_budget_v0|routine_fetch|significant_moved"
                ],
                "reachable_significant_routine": summary["by_policy_context_band"][
                    "reachable_first_task_conditioned_budget_v0|routine_fetch|significant_moved"
                ],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
