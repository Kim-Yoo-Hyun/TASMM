#!/usr/bin/env python3
"""Analyze E003 controlled proposal-dropout failure boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M06_annotation_proposal_dropout_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M07_dropout_failure_boundary_v0"
ANALYSIS_VERSION = "e003_dropout_failure_boundary_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
DROPOUT_PROFILE = "annotation_proposal_dropout_v0"
PRIMARY_POLICIES = [
    "task_conditioned_budget_v0",
    "reachable_first_task_conditioned_budget_v0",
]
REPORT_POLICIES = [
    "always_top1",
    "always_top3",
    "always_top5",
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


def index_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_uid"]: row for row in manifest_rows}


def clean_prediction_index(predictions: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    output = {}
    for row in predictions:
        if row["proposal_noise_profile_id"] == REFERENCE_PROFILE:
            output[(row["original_row_uid"], row["policy"])] = row
    return output


def denominator_group(manifest: dict[str, Any]) -> str:
    if manifest["target_dropped_by_noise"]:
        return "target_dropped"
    if manifest["target_drop_forced_retained"]:
        return "forced_retained"
    return "natural_target_retained"


def transition_label(clean_success: bool, dropout_success: bool) -> str:
    if clean_success and dropout_success:
        return "stable_success"
    if clean_success and not dropout_success:
        return "dropout_regression"
    if not clean_success and dropout_success:
        return "dropout_improvement"
    return "stable_failure"


def rank_delta(clean: dict[str, Any], dropout: dict[str, Any]) -> int | None:
    if clean["target_rank"] is None or dropout["target_rank"] is None:
        return None
    return int(dropout["target_rank"]) - int(clean["target_rank"])


def boundary_type(
    clean: dict[str, Any],
    dropout: dict[str, Any],
    manifest: dict[str, Any],
    transition: str,
    group: str,
) -> str:
    if group == "target_dropped":
        if dropout["search_success"]:
            if dropout["returns_old_location"] and not dropout["old_memory_is_stale"]:
                return "target_dropped_low_motion_static_memory_success"
            if dropout["returns_old_location"]:
                return "target_dropped_static_memory_success"
            return "target_dropped_unexpected_candidate_success"
        if dropout["returns_old_location"]:
            return "target_dropped_static_memory_failure"
        return "target_dropped_proposal_recall_ceiling"

    if group == "forced_retained":
        if transition == "dropout_improvement":
            return "forced_retained_artificial_recall_floor_improvement"
        if transition == "dropout_regression":
            return "forced_retained_budget_or_rank_regression"
        return "forced_retained_artificial_recall_floor"

    delta = rank_delta(clean, dropout)
    if transition == "dropout_improvement":
        if delta is not None and delta < 0:
            return "target_retained_distractor_dropout_improvement"
        return "target_retained_policy_improvement"
    if transition == "dropout_regression":
        if dropout["target_rank"] is None:
            return "target_retained_unexpected_missing_target"
        if int(dropout["target_rank"]) > int(dropout["returned_location_count"]):
            return "target_retained_budget_regression"
        if int(dropout["returned_unreachable_count"]) > int(clean["returned_unreachable_count"]):
            return "target_retained_reachability_regression"
        return "target_retained_policy_regression"
    if transition == "stable_failure":
        if dropout["stale_old_location_fp"]:
            return "target_retained_stale_static_failure"
        if dropout["target_rank"] is not None and int(dropout["target_rank"]) > int(dropout["returned_location_count"]):
            return "target_retained_persistent_budget_boundary"
        if dropout["returns_old_location"]:
            return "target_retained_static_memory_failure"
        return "target_retained_persistent_failure"
    return "target_retained_stable_success"


def build_boundary_rows(
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_row_uid = index_manifest(manifest_rows)
    clean_index = clean_prediction_index(predictions)
    rows = []
    for dropout in predictions:
        if dropout["proposal_noise_profile_id"] != DROPOUT_PROFILE:
            continue
        clean = clean_index[(dropout["original_row_uid"], dropout["policy"])]
        manifest = manifest_by_row_uid[dropout["row_uid"]]
        group = denominator_group(manifest)
        clean_success = bool(clean["search_success"])
        dropout_success = bool(dropout["search_success"])
        transition = transition_label(clean_success, dropout_success)
        delta_rank = rank_delta(clean, dropout)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": dropout["original_row_uid"],
                "row_uid": dropout["row_uid"],
                "base_row_uid": dropout["base_row_uid"],
                "pair_uid": dropout["pair_uid"],
                "proposal_noise_seed": dropout["proposal_noise_seed"],
                "policy": dropout["policy"],
                "task_context_id": dropout["task_context_id"],
                "row_band": dropout["row_band"],
                "object_label": dropout["object_label"],
                "ambiguity_band": dropout["ambiguity_band"],
                "old_memory_is_stale": dropout["old_memory_is_stale"],
                "denominator_group": group,
                "target_dropped_by_noise": bool(manifest["target_dropped_by_noise"]),
                "target_drop_forced_retained": bool(manifest["target_drop_forced_retained"]),
                "candidate_rows_original": manifest["candidate_rows_original"],
                "candidate_rows_retained": manifest["candidate_rows_retained"],
                "candidate_rows_dropped": manifest["candidate_rows_dropped"],
                "dropped_non_target_candidate_rows": manifest["dropped_non_target_candidate_rows"],
                "clean_success": clean_success,
                "dropout_success": dropout_success,
                "transition": transition,
                "boundary_type": boundary_type(clean, dropout, manifest, transition, group),
                "clean_target_rank": clean["target_rank"],
                "dropout_target_rank": dropout["target_rank"],
                "target_rank_delta": delta_rank,
                "clean_returned_location_count": clean["returned_location_count"],
                "dropout_returned_location_count": dropout["returned_location_count"],
                "returned_location_count_delta": int(dropout["returned_location_count"])
                - int(clean["returned_location_count"]),
                "clean_expected_search_cost": clean["expected_search_cost"],
                "dropout_expected_search_cost": dropout["expected_search_cost"],
                "expected_search_cost_delta": round6(
                    float(dropout["expected_search_cost"]) - float(clean["expected_search_cost"])
                ),
                "clean_attempt_spl_proxy": clean["attempt_spl_proxy"],
                "dropout_attempt_spl_proxy": dropout["attempt_spl_proxy"],
                "attempt_spl_delta": round6(
                    float(dropout["attempt_spl_proxy"]) - float(clean["attempt_spl_proxy"])
                ),
                "clean_task_utility": clean["task_utility"],
                "dropout_task_utility": dropout["task_utility"],
                "task_utility_delta": round6(float(dropout["task_utility"]) - float(clean["task_utility"])),
                "clean_returned_unreachable_count": clean["returned_unreachable_count"],
                "dropout_returned_unreachable_count": dropout["returned_unreachable_count"],
                "returned_unreachable_count_delta": int(dropout["returned_unreachable_count"])
                - int(clean["returned_unreachable_count"]),
                "uses_real_rgbd_perception": dropout["uses_real_rgbd_perception"],
                "uses_open_vocab_perception": dropout["uses_open_vocab_perception"],
            }
        )
    return rows


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "clean_proxy_sr": None,
            "dropout_proxy_sr": None,
            "proxy_sr_delta": None,
            "dropout_regression_rate": None,
        }
    clean_success = sum(1 for row in rows if row["clean_success"])
    dropout_success = sum(1 for row in rows if row["dropout_success"])
    transition_counts = Counter(row["transition"] for row in rows)
    boundary_counts = Counter(row["boundary_type"] for row in rows)
    group_counts = Counter(row["denominator_group"] for row in rows)
    rank_deltas = [float(row["target_rank_delta"]) for row in rows if row["target_rank_delta"] is not None]
    return {
        "rows": len(rows),
        "clean_proxy_sr": safe_rate(clean_success, len(rows)),
        "dropout_proxy_sr": safe_rate(dropout_success, len(rows)),
        "proxy_sr_delta": round6((dropout_success - clean_success) / len(rows)),
        "dropout_regression_rows": transition_counts["dropout_regression"],
        "dropout_regression_rate": safe_rate(transition_counts["dropout_regression"], len(rows)),
        "dropout_improvement_rows": transition_counts["dropout_improvement"],
        "stable_failure_rows": transition_counts["stable_failure"],
        "stable_success_rows": transition_counts["stable_success"],
        "target_rank_better_rows": sum(1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] < 0),
        "target_rank_worse_rows": sum(1 for row in rows if row["target_rank_delta"] is not None and row["target_rank_delta"] > 0),
        "target_rank_same_rows": sum(1 for row in rows if row["target_rank_delta"] == 0),
        "mean_target_rank_delta": mean(rank_deltas),
        "mean_candidate_rows_dropped": mean([float(row["candidate_rows_dropped"]) for row in rows]),
        "mean_non_target_candidate_rows_dropped": mean([float(row["dropped_non_target_candidate_rows"]) for row in rows]),
        "mean_expected_search_cost_delta": mean([float(row["expected_search_cost_delta"]) for row in rows]),
        "mean_attempt_spl_delta": mean([float(row["attempt_spl_delta"]) for row in rows]),
        "mean_task_utility_delta": mean([float(row["task_utility_delta"]) for row in rows]),
        "returned_unreachable_event_delta": sum(
            1 for row in rows if int(row["dropout_returned_unreachable_count"]) > 0
        )
        - sum(1 for row in rows if int(row["clean_returned_unreachable_count"]) > 0),
        "transition_counts": counter_dict(transition_counts),
        "boundary_counts": counter_dict(boundary_counts),
        "denominator_group_counts": counter_dict(group_counts),
    }


def build_manifest_summary(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    dropout_rows = [row for row in manifest_rows if row["proposal_noise_profile_id"] == DROPOUT_PROFILE]
    target_dropped = sum(1 for row in dropout_rows if row["target_dropped_by_noise"])
    forced_retained = sum(1 for row in dropout_rows if row["target_drop_forced_retained"])
    natural_retained = sum(
        1
        for row in dropout_rows
        if row["target_retained"] and not row["target_drop_forced_retained"]
    )
    target_drop_attempts = target_dropped + forced_retained
    return {
        "dropout_query_rows": len(dropout_rows),
        "natural_target_retained_rows": natural_retained,
        "forced_retained_rows": forced_retained,
        "target_dropped_rows": target_dropped,
        "target_drop_attempt_rows": target_drop_attempts,
        "reported_target_retained_rows": natural_retained + forced_retained,
        "reported_target_retained_rate": safe_rate(natural_retained + forced_retained, len(dropout_rows)),
        "strict_target_retained_rate_excluding_forced": safe_rate(natural_retained, len(dropout_rows)),
        "target_dropped_rate": safe_rate(target_dropped, len(dropout_rows)),
        "target_drop_attempt_rate": safe_rate(target_drop_attempts, len(dropout_rows)),
        "forced_retained_rate": safe_rate(forced_retained, len(dropout_rows)),
        "dropped_non_target_candidate_rows": sum(int(row["dropped_non_target_candidate_rows"]) for row in dropout_rows),
        "mean_candidate_rows_original": mean([float(row["candidate_rows_original"]) for row in dropout_rows]),
        "mean_candidate_rows_retained": mean([float(row["candidate_rows_retained"]) for row in dropout_rows]),
        "mean_candidate_rows_dropped": mean([float(row["candidate_rows_dropped"]) for row in dropout_rows]),
    }


def build_summary(boundary_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "manifest": build_manifest_summary(manifest_rows),
        "all": summarize_subset(boundary_rows),
        "by_denominator_group": {},
        "by_denominator_group_policy": {},
        "by_denominator_group_context_band_policy": {},
        "by_policy_context_band": {},
        "primary_policy_boundary_counts": {},
        "primary_policy_label_counts": {},
    }
    for group in ["natural_target_retained", "forced_retained", "target_dropped"]:
        rows = [row for row in boundary_rows if row["denominator_group"] == group]
        summary["by_denominator_group"][group] = summarize_subset(rows)
        for policy in sorted({row["policy"] for row in boundary_rows}):
            policy_rows = [row for row in rows if row["policy"] == policy]
            summary["by_denominator_group_policy"][f"{group}|{policy}"] = summarize_subset(policy_rows)

    for key in sorted(
        {
            (row["denominator_group"], row["task_context_id"], row["row_band"], row["policy"])
            for row in boundary_rows
        }
    ):
        group, context, band, policy = key
        rows = [
            row
            for row in boundary_rows
            if row["denominator_group"] == group
            and row["task_context_id"] == context
            and row["row_band"] == band
            and row["policy"] == policy
        ]
        summary["by_denominator_group_context_band_policy"][f"{group}|{context}|{band}|{policy}"] = summarize_subset(rows)

    for key in sorted({(row["policy"], row["task_context_id"], row["row_band"]) for row in boundary_rows}):
        policy, context, band = key
        rows = [
            row
            for row in boundary_rows
            if row["policy"] == policy and row["task_context_id"] == context and row["row_band"] == band
        ]
        summary["by_policy_context_band"][f"{policy}|{context}|{band}"] = summarize_subset(rows)

    primary_rows = [row for row in boundary_rows if row["policy"] in PRIMARY_POLICIES]
    summary["primary_policy_boundary_counts"] = counter_dict(Counter(row["boundary_type"] for row in primary_rows))
    hard_primary_rows = [
        row
        for row in primary_rows
        if row["transition"] in {"dropout_regression", "stable_failure"}
    ]
    summary["primary_policy_label_counts"] = counter_dict(Counter(row["object_label"] for row in hard_primary_rows))
    return summary


def build_hard_boundary_rows(boundary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in boundary_rows:
        if row["policy"] not in PRIMARY_POLICIES:
            continue
        if row["denominator_group"] == "natural_target_retained" and row["transition"] == "stable_success":
            continue
        next_test = "annotation_false_positive_v0"
        if row["denominator_group"] == "target_dropped":
            next_test = "real proposal recall or target-drop ceiling analysis"
        elif row["denominator_group"] == "forced_retained":
            next_test = "exclude forced-retained rows from strict proposal-recall denominator"
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "original_row_uid": row["original_row_uid"],
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "proposal_noise_seed": row["proposal_noise_seed"],
                "policy": row["policy"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "ambiguity_band": row["ambiguity_band"],
                "denominator_group": row["denominator_group"],
                "transition": row["transition"],
                "boundary_type": row["boundary_type"],
                "clean_target_rank": row["clean_target_rank"],
                "dropout_target_rank": row["dropout_target_rank"],
                "target_rank_delta": row["target_rank_delta"],
                "dropout_returned_location_count": row["dropout_returned_location_count"],
                "expected_search_cost_delta": row["expected_search_cost_delta"],
                "task_utility_delta": row["task_utility_delta"],
                "candidate_rows_dropped": row["candidate_rows_dropped"],
                "dropped_non_target_candidate_rows": row["dropped_non_target_candidate_rows"],
                "next_test": next_test,
            }
        )
    return rows


def build_policy_delta_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, item in summary["by_denominator_group_policy"].items():
        group, policy = key.split("|", 1)
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "denominator_group": group,
                "policy": policy,
                "rows": item["rows"],
                "clean_proxy_sr": item["clean_proxy_sr"],
                "dropout_proxy_sr": item["dropout_proxy_sr"],
                "proxy_sr_delta": item["proxy_sr_delta"],
                "dropout_regression_rows": item["dropout_regression_rows"],
                "dropout_improvement_rows": item["dropout_improvement_rows"],
                "mean_target_rank_delta": item["mean_target_rank_delta"],
                "mean_candidate_rows_dropped": item["mean_candidate_rows_dropped"],
                "mean_expected_search_cost_delta": item["mean_expected_search_cost_delta"],
                "mean_attempt_spl_delta": item["mean_attempt_spl_delta"],
                "mean_task_utility_delta": item["mean_task_utility_delta"],
                "returned_unreachable_event_delta": item["returned_unreachable_event_delta"],
            }
        )
    return rows


def build_claim_boundary(summary: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    manifest = summary["manifest"]
    task_natural_sig = summary["by_denominator_group_context_band_policy"][
        "natural_target_retained|routine_fetch|significant_moved|task_conditioned_budget_v0"
    ]
    task_dropped_sig = summary["by_denominator_group_context_band_policy"][
        "target_dropped|routine_fetch|significant_moved|task_conditioned_budget_v0"
    ]
    reachable_natural_sig = summary["by_denominator_group_context_band_policy"][
        "natural_target_retained|routine_fetch|significant_moved|reachable_first_task_conditioned_budget_v0"
    ]
    return {
        "status": "dropout_boundary_ready",
        "safe_claims": [
            "E003-M07 supports controlled annotation-proxy proposal-recall boundary analysis.",
            "Target-dropped rows should be treated as a proposal-recall ceiling, not as a recoverable memory-update failure.",
            "Forced-retained rows should be separated from strict target-retained robustness because they create an artificial recall floor.",
            "Target-retained dropout rows can test candidate-pruning sensitivity, but not false-positive contamination.",
        ],
        "partial_or_weakened_claims": [
            "Target-retained dropout can improve proxy SR by removing distractors, so positive retained-denominator results are not sufficient for perception robustness.",
            "The observed target-dropped failures motivate proposal recall accounting before claiming real RGB-D/open-vocabulary robustness.",
            "The current route remains annotation-proxy and should be described as a bridge experiment.",
        ],
        "unsupported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary detector robustness",
            "deployable search policy",
            "real navigation `SR` / `SPL`",
            "recovery when the true target is absent from all current proposals",
        ],
        "key_evidence": {
            "boundary_rows": coverage["boundary_rows"],
            "dropout_query_rows": manifest["dropout_query_rows"],
            "reported_target_retained_rate": manifest["reported_target_retained_rate"],
            "strict_target_retained_rate_excluding_forced": manifest[
                "strict_target_retained_rate_excluding_forced"
            ],
            "target_dropped_rate": manifest["target_dropped_rate"],
            "target_drop_attempt_rate": manifest["target_drop_attempt_rate"],
            "forced_retained_rows": manifest["forced_retained_rows"],
            "natural_retained_significant_routine_task_sr": task_natural_sig["dropout_proxy_sr"],
            "target_dropped_significant_routine_task_sr": task_dropped_sig["dropout_proxy_sr"],
            "natural_retained_significant_routine_reachable_sr": reachable_natural_sig["dropout_proxy_sr"],
            "uses_real_rgbd_perception": coverage["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": coverage["uses_open_vocab_perception"],
            "uses_real_navigation": coverage["uses_real_navigation"],
        },
        "next_stress_profile_decision": {
            "selected": "annotation_false_positive_v0",
            "reason": "Dropout removes candidates and can make ranking easier; false-positive contamination tests the opposite and is closer to open-vocabulary proposal hallucination.",
            "defer": [
                "annotation_centroid_jitter_v0 until localization/path-cost sensitivity is the main question",
                "annotation_combined_moderate_v0 until dropout and false-positive boundaries are both measured",
                "real RGB-D/open-vocabulary detector route until Dockerized proposal generation is staged",
            ],
        },
    }


def build_coverage(
    input_dir: Path,
    out_dir: Path,
    input_coverage: dict[str, Any],
    predictions: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
    hard_boundary_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    dropout_query_rows = summary["manifest"]["dropout_query_rows"]
    policies = sorted({row["policy"] for row in predictions})
    expected_boundary_rows = dropout_query_rows * len(policies)
    status = "dropout_boundary_ready" if len(boundary_rows) == expected_boundary_rows else "review_needed"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "input_dir": str(input_dir),
        "input_status": input_coverage["status"],
        "reference_profile": REFERENCE_PROFILE,
        "stress_profile": DROPOUT_PROFILE,
        "policies": policies,
        "dropout_query_rows": dropout_query_rows,
        "manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "expected_boundary_rows": expected_boundary_rows,
        "boundary_rows": len(boundary_rows),
        "hard_boundary_rows": len(hard_boundary_rows),
        "docker_required": False,
        "docker_reason": "E003-M07 is repository-local analysis over E003-M06 JSONL artifacts; detector/open-vocabulary implementations remain Docker-required.",
        "uses_annotation_proxy_noise": input_coverage["uses_annotation_proxy_noise"],
        "uses_real_rgbd_perception": input_coverage["uses_real_rgbd_perception"],
        "uses_open_vocab_perception": input_coverage["uses_open_vocab_perception"],
        "uses_real_navigation": input_coverage["uses_real_navigation"],
        "next_stress_profile": "annotation_false_positive_v0",
        "outputs": {
            "boundary_rows": str(out_dir / "boundary_rows.jsonl"),
            "hard_boundary_rows": str(out_dir / "hard_boundary_rows.jsonl"),
            "policy_delta_rows": str(out_dir / "policy_delta_rows.jsonl"),
            "summary": str(out_dir / "summary.json"),
            "claim_boundary": str(out_dir / "claim_boundary.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def metric(summary: dict[str, Any], group: str, context: str, band: str, policy: str) -> dict[str, Any]:
    return summary["by_denominator_group_context_band_policy"].get(
        f"{group}|{context}|{band}|{policy}",
        summarize_subset([]),
    )


def build_report(
    coverage: dict[str, Any],
    summary: dict[str, Any],
    claim_boundary: dict[str, Any],
    out_dir: Path,
) -> str:
    manifest = summary["manifest"]
    lines = [
        "# E003-M07 Dropout Failure Boundary",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input directory: `{coverage['input_dir']}`",
        f"- Boundary rows: {coverage['boundary_rows']}",
        f"- Hard boundary rows: {coverage['hard_boundary_rows']}",
        f"- Dropout query rows: {manifest['dropout_query_rows']}",
        f"- Natural target-retained rows: {manifest['natural_target_retained_rows']}",
        f"- Forced-retained rows: {manifest['forced_retained_rows']}",
        f"- Target-dropped rows: {manifest['target_dropped_rows']}",
        f"- Reported target-retained rate: {manifest['reported_target_retained_rate']}",
        f"- Strict target-retained rate excluding forced rows: {manifest['strict_target_retained_rate_excluding_forced']}",
        f"- Target-drop attempt rate including forced rows: {manifest['target_drop_attempt_rate']}",
        f"- Uses real RGB-D perception: {coverage['uses_real_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocab_perception']}",
        f"- Uses real navigation: {coverage['uses_real_navigation']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch` Boundary",
        "",
        "| Denominator | Policy | rows | clean `SR` | dropout `SR` | delta `SR` | regressions | improvements | mean rank delta | cost delta | utility delta |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in ["natural_target_retained", "forced_retained", "target_dropped"]:
        for policy in [
            "always_top5",
            "task_conditioned_budget_v0",
            "reachable_first_task_conditioned_budget_v0",
            "oracle_current_target",
        ]:
            item = metric(summary, group, "routine_fetch", "significant_moved", policy)
            lines.append(
                "| `{group}` | `{policy}` | {rows} | {clean} | {dropout} | {delta} | {regressions} | {improvements} | {rank_delta} | {cost_delta} | {utility_delta} |".format(
                    group=group,
                    policy=policy,
                    rows=item["rows"],
                    clean=item["clean_proxy_sr"],
                    dropout=item["dropout_proxy_sr"],
                    delta=item["proxy_sr_delta"],
                    regressions=item.get("dropout_regression_rows"),
                    improvements=item.get("dropout_improvement_rows"),
                    rank_delta=item.get("mean_target_rank_delta"),
                    cost_delta=item.get("mean_expected_search_cost_delta"),
                    utility_delta=item.get("mean_task_utility_delta"),
                )
            )

    lines.extend(
        [
            "",
            "## Boundary Counts",
            "",
            f"- Primary policy boundary counts: {summary['primary_policy_boundary_counts']}",
            f"- Primary policy hard label counts: {summary['primary_policy_label_counts']}",
            "",
            "## 논문 주장",
            "",
        ]
    )
    for item in claim_boundary["safe_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 에이전트 추론", ""])
    for item in claim_boundary["partial_or_weakened_claims"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            f"- Next stress profile should be `{claim_boundary['next_stress_profile_decision']['selected']}`.",
            f"- Reason: {claim_boundary['next_stress_profile_decision']['reason']}",
            "",
            "## Unsupported Claims",
            "",
        ]
    )
    for item in claim_boundary["unsupported_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 사용자 판단 필요", ""])
    lines.append("- None for E003-M07. Next implementation unit should start `annotation_false_positive_v0` unless the route is redirected to Dockerized real proposal generation.")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `boundary_rows.jsonl`",
            "- `hard_boundary_rows.jsonl`",
            "- `policy_delta_rows.jsonl`",
            "- `summary.json`",
            "- `claim_boundary.json`",
            "- `coverage.json`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    input_coverage = load_json(args.input_dir / "coverage.json")
    predictions = load_jsonl(args.input_dir / "predictions.jsonl")
    manifest_rows = load_jsonl(args.input_dir / "noise_manifest.jsonl")

    boundary_rows = build_boundary_rows(predictions, manifest_rows)
    summary = build_summary(boundary_rows, manifest_rows)
    hard_boundary_rows = build_hard_boundary_rows(boundary_rows)
    policy_delta_rows = build_policy_delta_rows(summary)
    coverage = build_coverage(
        args.input_dir,
        args.out_dir,
        input_coverage,
        predictions,
        manifest_rows,
        boundary_rows,
        hard_boundary_rows,
        summary,
    )
    claim_boundary = build_claim_boundary(summary, coverage)
    report = build_report(coverage, summary, claim_boundary, args.out_dir)

    write_jsonl(args.out_dir / "boundary_rows.jsonl", boundary_rows)
    write_jsonl(args.out_dir / "hard_boundary_rows.jsonl", hard_boundary_rows)
    write_jsonl(args.out_dir / "policy_delta_rows.jsonl", policy_delta_rows)
    write_json(args.out_dir / "summary.json", summary)
    write_json(args.out_dir / "claim_boundary.json", claim_boundary)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": coverage["status"], "out_dir": str(args.out_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
