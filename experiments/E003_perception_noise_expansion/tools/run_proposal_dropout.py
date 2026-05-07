#!/usr/bin/env python3
"""Generate and evaluate E003 controlled annotation-proposal dropout."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from evaluate_noisy_policies import (
    POLICIES,
    attach_grid_fields,
    build_failure_rows,
    grid_reachability_index,
    group_by_uid,
    predict_policy,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_M02_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_GRID_DIR = (
    REPO_ROOT
    / "experiments"
    / "E002_path_cost_bridge"
    / "artifacts"
    / "E002-M05_occupancy_grid_astar_v0"
)
DEFAULT_CONTRACT = EXPERIMENT_ROOT / "artifacts" / "E003-M05_route_v0" / "controlled_profile_contract.json"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M06_annotation_proposal_dropout_v0"
EVAL_VERSION = "e003_annotation_proposal_dropout_v0"
REFERENCE_PROFILE = "clean_annotation_oracle_v0"
DROPOUT_PROFILE = "annotation_proposal_dropout_v0"


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


def deterministic_rng(seed: int, *parts: str) -> random.Random:
    joined = "|".join([str(seed), *parts])
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def instance_key(value: Any) -> Any:
    text = str(value)
    return int(text) if text.isdigit() else text


def noisy_row_uid(row_uid: str, profile_id: str, seed: int | None = None) -> str:
    if seed is None:
        return f"{row_uid}::noise={profile_id}"
    return f"{row_uid}::noise={profile_id}::seed={seed}"


def build_query_row(
    row: dict[str, Any],
    profile_id: str,
    role: str,
    seed: int | None,
    target_dropped: bool,
) -> dict[str, Any]:
    output = dict(row)
    output["original_row_uid"] = row["row_uid"]
    output["row_uid"] = noisy_row_uid(row["row_uid"], profile_id, seed)
    output["noise_version"] = EVAL_VERSION
    output["perception_profile_id"] = "annotation_proxy_noise"
    output["proposal_noise_profile_id"] = profile_id
    output["proposal_noise_role"] = role
    output["proposal_noise_seed"] = seed
    output["proposal_noise_target_policy"] = (
        "allow_target_drop" if profile_id == DROPOUT_PROFILE else "preserve_target"
    )
    output["current_proposal_source"] = "annotation_semseg_noisy_proxy"
    output["observation_source"] = "annotation_semseg_noisy_proxy"
    output["uses_real_rgbd_perception"] = False
    output["uses_open_vocab_perception"] = False
    output["target_dropped_by_noise"] = target_dropped
    return output


def rank_retained_candidates(rows: list[dict[str, Any]], profile_id: str) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row["original_candidate_rank_non_persistent"]),
            -float(row["candidate_score_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{profile_id}_ranked_retained_candidates"
    return ranked


def build_candidate_output(
    row: dict[str, Any],
    original_row_uid: str,
    noisy_uid: str,
    profile_id: str,
    role: str,
    seed: int | None,
    retained: bool,
    drop_reason: str | None,
) -> dict[str, Any]:
    output = dict(row)
    output["original_row_uid"] = original_row_uid
    output["row_uid"] = noisy_uid
    output["noise_version"] = EVAL_VERSION
    output["perception_profile_id"] = "annotation_proxy_noise"
    output["proposal_noise_profile_id"] = profile_id
    output["proposal_noise_role"] = role
    output["proposal_noise_seed"] = seed
    output["candidate_observation_source"] = "annotation_semseg_noisy_proxy"
    output["original_candidate_rank_non_persistent"] = row["candidate_rank_non_persistent"]
    output["original_candidate_score_non_persistent"] = row["candidate_score_non_persistent"]
    output["candidate_score_noise_delta"] = 0.0
    output["candidate_retained_by_noise"] = retained
    output["candidate_drop_reason"] = drop_reason
    output["candidate_added_by_noise"] = False
    return output


def build_clean_candidates(
    original_row_uid: str,
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile_id = REFERENCE_PROFILE
    row_uid = noisy_row_uid(original_row_uid, profile_id)
    rows = [
        build_candidate_output(
            row,
            original_row_uid,
            row_uid,
            profile_id,
            "clean_reference",
            None,
            True,
            None,
        )
        for row in candidates
    ]
    ranked = rank_retained_candidates(rows, profile_id)
    target_rows = [row for row in ranked if row["candidate_is_target"]]
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": profile_id,
        "proposal_noise_seed": None,
        "candidate_rows_original": len(candidates),
        "candidate_rows_retained": len(ranked),
        "candidate_rows_dropped": 0,
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_drop_forced_retained": False,
        "target_rank_original": target_rows[0]["original_candidate_rank_non_persistent"] if target_rows else None,
        "target_rank_noisy": target_rows[0]["candidate_rank_non_persistent"] if target_rows else None,
        "dropped_target_candidate": False,
        "dropped_non_target_candidate_rows": 0,
    }


def should_drop_target(original_row_uid: str, seed: int, target_drop_rate: float) -> bool:
    rng = deterministic_rng(seed, original_row_uid, "target", DROPOUT_PROFILE)
    return rng.random() < target_drop_rate


def should_drop_non_target(
    original_row_uid: str,
    candidate_instance_id: Any,
    seed: int,
    drop_rate: float,
) -> bool:
    rng = deterministic_rng(seed, original_row_uid, str(candidate_instance_id), "non_target", DROPOUT_PROFILE)
    return rng.random() < drop_rate


def build_dropout_candidates(
    original_row_uid: str,
    candidates: list[dict[str, Any]],
    seed: int,
    target_drop_rate: float,
    non_target_drop_rate: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_uid = noisy_row_uid(original_row_uid, DROPOUT_PROFILE, seed)
    target_rows = [row for row in candidates if row["candidate_is_target"]]
    non_target_rows = [row for row in candidates if not row["candidate_is_target"]]
    drop_target = bool(target_rows) and should_drop_target(original_row_uid, seed, target_drop_rate)

    retained = []
    dropped = []
    for row in candidates:
        if row["candidate_is_target"]:
            is_dropped = drop_target
            reason = "target_dropout" if is_dropped else None
        else:
            is_dropped = should_drop_non_target(
                original_row_uid,
                row["candidate_instance_id"],
                seed,
                non_target_drop_rate,
            )
            reason = "non_target_dropout" if is_dropped else None
        output = build_candidate_output(
            row,
            original_row_uid,
            row_uid,
            DROPOUT_PROFILE,
            "controlled_proposal_recall_stress",
            seed,
            not is_dropped,
            reason,
        )
        if is_dropped:
            dropped.append(output)
        else:
            retained.append(output)

    forced_target_retained = False
    if not retained and target_rows:
        best_target = min(target_rows, key=lambda row: int(row["candidate_rank_non_persistent"]))
        retained.append(
            build_candidate_output(
                best_target,
                original_row_uid,
                row_uid,
                DROPOUT_PROFILE,
                "controlled_proposal_recall_stress",
                seed,
                True,
                "forced_keep_to_preserve_candidate",
            )
        )
        forced_target_retained = True

    ranked = rank_retained_candidates(retained, DROPOUT_PROFILE)
    retained_target_rows = [row for row in ranked if row["candidate_is_target"]]
    original_target_rank = (
        int(target_rows[0]["candidate_rank_non_persistent"]) if target_rows else None
    )
    noisy_target_rank = retained_target_rows[0]["candidate_rank_non_persistent"] if retained_target_rows else None
    dropped_target = bool(target_rows) and not retained_target_rows
    return ranked, {
        "noise_version": EVAL_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": DROPOUT_PROFILE,
        "proposal_noise_seed": seed,
        "candidate_rows_original": len(candidates),
        "candidate_rows_retained": len(ranked),
        "candidate_rows_dropped": len(candidates) - len(ranked),
        "target_retained": len(retained_target_rows) == 1,
        "target_dropped_by_noise": dropped_target,
        "target_drop_forced_retained": forced_target_retained,
        "target_rank_original": original_target_rank,
        "target_rank_noisy": noisy_target_rank,
        "target_rank_delta": noisy_target_rank - original_target_rank
        if noisy_target_rank is not None and original_target_rank is not None
        else None,
        "dropped_target_candidate": dropped_target,
        "dropped_non_target_candidate_rows": sum(1 for row in dropped if not row["candidate_is_target"]),
        "target_drop_rate": target_drop_rate,
        "non_target_candidate_drop_rate": non_target_drop_rate,
    }


def build_noisy_rows(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates_by_uid = group_by_uid(candidate_rows)
    seeds = [int(seed) for seed in contract["recommended_seed_set"]]
    target_drop_rate = float(contract["dropout_policy"]["target_drop_rate"])
    non_target_drop_rate = float(contract["dropout_policy"]["non_target_candidate_drop_rate"])
    noisy_query_rows: list[dict[str, Any]] = []
    noisy_candidate_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for row in query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        clean_candidates, clean_manifest = build_clean_candidates(row["row_uid"], candidates)
        noisy_query_rows.append(
            build_query_row(row, REFERENCE_PROFILE, "clean_reference", None, False)
        )
        noisy_candidate_rows.extend(clean_candidates)
        manifest_rows.append(clean_manifest)

    for seed in seeds:
        for row in query_rows:
            candidates = candidates_by_uid.get(row["row_uid"], [])
            dropout_candidates, dropout_manifest = build_dropout_candidates(
                row["row_uid"],
                candidates,
                seed,
                target_drop_rate,
                non_target_drop_rate,
            )
            noisy_query_rows.append(
                build_query_row(
                    row,
                    DROPOUT_PROFILE,
                    "controlled_proposal_recall_stress",
                    seed,
                    bool(dropout_manifest["target_dropped_by_noise"]),
                )
            )
            noisy_candidate_rows.extend(dropout_candidates)
            manifest_rows.append(dropout_manifest)

    return noisy_query_rows, noisy_candidate_rows, manifest_rows


def build_predictions(
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    grid_dir: Path,
) -> list[dict[str, Any]]:
    grid_candidate_path = grid_dir / "grid_candidate_rows.jsonl"
    grid_candidate_rows = load_jsonl(grid_candidate_path) if grid_candidate_path.exists() else []
    grid_index = grid_reachability_index(grid_candidate_rows)
    candidate_rows = attach_grid_fields(noisy_candidate_rows, grid_index)
    candidates_by_uid = group_by_uid(candidate_rows)

    predictions = []
    for row in noisy_query_rows:
        candidates = candidates_by_uid.get(row["row_uid"], [])
        for policy in POLICIES:
            prediction = predict_policy(policy, row, candidates)
            prediction["eval_version"] = EVAL_VERSION
            prediction["target_dropped_by_noise"] = bool(row["target_dropped_by_noise"])
            predictions.append(prediction)
    return predictions


def subset_rows(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "all":
        return rows
    return [row for row in rows if row["row_band"] == subset]


def denominator_rows(rows: list[dict[str, Any]], denominator: str) -> list[dict[str, Any]]:
    if denominator == "all_rows":
        return rows
    if denominator == "target_retained_eval":
        return [row for row in rows if row["target_retained"]]
    if denominator == "target_dropped_eval":
        return [row for row in rows if row["target_dropped_by_noise"]]
    raise RuntimeError(f"unknown denominator: {denominator}")


def summarize_prediction_rows(rows: list[dict[str, Any]], subset: str) -> dict[str, Any]:
    stale = [row for row in rows if row["old_memory_is_stale"]]
    low_motion = [row for row in rows if row["row_band"] == "low_motion_control"]
    success_rate = safe_rate(sum(1 for row in rows if row["search_success"]), len(rows))
    returned_mean = mean([float(row["returned_location_count"]) for row in rows])
    return {
        "subset": subset,
        "rows": len(rows),
        "proposal_recall": safe_rate(sum(1 for row in rows if row["target_retained"]), len(rows)),
        "target_dropped_rate": safe_rate(sum(1 for row in rows if row["target_dropped_by_noise"]), len(rows)),
        "proxy_sr": success_rate,
        "target_retained_eval_sr": safe_rate(
            sum(1 for row in rows if row["target_retained"] and row["search_success"]),
            sum(1 for row in rows if row["target_retained"]),
        ),
        "target_dropped_eval_sr": safe_rate(
            sum(1 for row in rows if row["target_dropped_by_noise"] and row["search_success"]),
            sum(1 for row in rows if row["target_dropped_by_noise"]),
        ),
        "stale_old_location_fp_rate": safe_rate(
            sum(1 for row in stale if row["stale_old_location_fp"]),
            len(stale),
        ),
        "low_motion_preservation_rate": safe_rate(
            sum(1 for row in low_motion if row["low_motion_preserved"]),
            len(low_motion),
        ),
        "mean_expected_search_cost": mean([float(row["expected_search_cost"]) for row in rows]),
        "attempt_spl_proxy": mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "mean_task_utility": mean([float(row["task_utility"]) for row in rows]),
        "mean_returned_location_count": returned_mean,
        "returned_unreachable_rate": safe_rate(
            sum(1 for row in rows if row["returned_unreachable_count"] > 0),
            len(rows),
        ),
    }


def summarize_by_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for denominator in ["all_rows", "target_retained_eval", "target_dropped_eval"]:
        den_rows = denominator_rows(rows, denominator)
        output[denominator] = {}
        for subset in ["all", "significant_moved", "mid_motion_review", "low_motion_control"]:
            subset_predictions = subset_rows(den_rows, subset)
            output[denominator][subset] = {}
            for context in sorted({row["task_context_id"] for row in subset_predictions}):
                context_rows = [row for row in subset_predictions if row["task_context_id"] == context]
                output[denominator][subset][context] = {}
                for policy in POLICIES:
                    policy_rows = [row for row in context_rows if row["policy"] == policy]
                    output[denominator][subset][context][policy] = summarize_prediction_rows(
                        policy_rows,
                        subset,
                    )
    return output


def build_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "profiles": {},
        "dropout_seeds": {},
    }
    for profile in [REFERENCE_PROFILE, DROPOUT_PROFILE]:
        profile_rows = [row for row in predictions if row["proposal_noise_profile_id"] == profile]
        metrics["profiles"][profile] = summarize_by_policy(profile_rows)
    seeds = sorted({row["proposal_noise_seed"] for row in predictions if row["proposal_noise_profile_id"] == DROPOUT_PROFILE})
    for seed in seeds:
        seed_rows = [
            row
            for row in predictions
            if row["proposal_noise_profile_id"] == DROPOUT_PROFILE and row["proposal_noise_seed"] == seed
        ]
        metrics["dropout_seeds"][str(seed)] = summarize_by_policy(seed_rows)
    return metrics


def summarize_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        by_profile[row["proposal_noise_profile_id"]].append(row)
    output: dict[str, Any] = {}
    for profile, rows in by_profile.items():
        output[profile] = {
            "rows": len(rows),
            "target_retained_rows": sum(1 for row in rows if row["target_retained"]),
            "target_dropped_rows": sum(1 for row in rows if row["target_dropped_by_noise"]),
            "target_dropped_rate": safe_rate(sum(1 for row in rows if row["target_dropped_by_noise"]), len(rows)),
            "mean_candidate_rows_original": mean([float(row["candidate_rows_original"]) for row in rows]),
            "mean_candidate_rows_retained": mean([float(row["candidate_rows_retained"]) for row in rows]),
            "mean_candidate_rows_dropped": mean([float(row["candidate_rows_dropped"]) for row in rows]),
            "dropped_non_target_candidate_rows": sum(int(row["dropped_non_target_candidate_rows"]) for row in rows),
            "target_drop_forced_retained_rows": sum(1 for row in rows if row["target_drop_forced_retained"]),
        }
    return output


def build_coverage(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    metrics: dict[str, Any],
    contract: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    expected_noisy_query_rows = len(query_rows) * (1 + len(contract["recommended_seed_set"]))
    manifest_summary = summarize_manifest(manifest_rows)
    dropout_summary = manifest_summary[DROPOUT_PROFILE]
    significant_routine_retained = metrics["profiles"][DROPOUT_PROFILE]["target_retained_eval"]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"]
    significant_routine_dropped = metrics["profiles"][DROPOUT_PROFILE]["target_dropped_eval"]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"]
    status = "proposal_dropout_eval_ready"
    if len(noisy_query_rows) != expected_noisy_query_rows:
        status = "review_needed"
    if len(predictions) != len(noisy_query_rows) * len(POLICIES):
        status = "review_needed"
    if dropout_summary["target_dropped_rows"] <= 0:
        status = "review_needed"
    return {
        "eval_version": EVAL_VERSION,
        "status": status,
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "profiles": [REFERENCE_PROFILE, DROPOUT_PROFILE],
        "dropout_seeds": contract["recommended_seed_set"],
        "target_drop_rate": contract["dropout_policy"]["target_drop_rate"],
        "non_target_candidate_drop_rate": contract["dropout_policy"]["non_target_candidate_drop_rate"],
        "noisy_query_rows": len(noisy_query_rows),
        "noisy_candidate_rows": len(noisy_candidate_rows),
        "noise_manifest_rows": len(manifest_rows),
        "prediction_rows": len(predictions),
        "failure_rows": len(failure_rows),
        "manifest_summary": manifest_summary,
        "target_drop_profiles_included": True,
        "uses_annotation_proxy_noise": True,
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "uses_real_navigation": False,
        "docker_required": bool(contract["docker_required"]),
        "docker_reason": contract["docker_reason"],
        "significant_moved_routine_task_retained_metrics": significant_routine_retained,
        "significant_moved_routine_task_dropped_metrics": significant_routine_dropped,
        "failure_type_counts": counter_dict(Counter(row["failure_type"] for row in failure_rows)),
        "outputs": {
            "noise_manifest": str(out_dir / "noise_manifest.jsonl"),
            "noisy_query_rows": str(out_dir / "noisy_query_rows.jsonl"),
            "noisy_candidate_rows": str(out_dir / "noisy_candidate_rows.jsonl"),
            "predictions": str(out_dir / "predictions.jsonl"),
            "failure_rows": str(out_dir / "failure_rows.jsonl"),
            "metrics": str(out_dir / "metrics.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], out_dir: Path) -> str:
    clean_task = metrics["profiles"][REFERENCE_PROFILE]["all_rows"]["significant_moved"]["routine_fetch"]["task_conditioned_budget_v0"]
    retained_task = coverage["significant_moved_routine_task_retained_metrics"]
    dropped_task = coverage["significant_moved_routine_task_dropped_metrics"]
    retained_reachable = metrics["profiles"][DROPOUT_PROFILE]["target_retained_eval"]["significant_moved"]["routine_fetch"]["reachable_first_task_conditioned_budget_v0"]
    dropped_reachable = metrics["profiles"][DROPOUT_PROFILE]["target_dropped_eval"]["significant_moved"]["routine_fetch"]["reachable_first_task_conditioned_budget_v0"]
    lines = [
        "# E003-M06 Annotation Proposal Dropout",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input query rows: {coverage['input_query_rows']}",
        f"- Input candidate rows: {coverage['input_candidate_rows']}",
        f"- Dropout seeds: {', '.join(str(seed) for seed in coverage['dropout_seeds'])}",
        f"- Target drop rate: {coverage['target_drop_rate']}",
        f"- Non-target candidate drop rate: {coverage['non_target_candidate_drop_rate']}",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Prediction rows: {coverage['prediction_rows']}",
        f"- Failure rows: {coverage['failure_rows']}",
        f"- Dropout target dropped rows: {coverage['manifest_summary'][DROPOUT_PROFILE]['target_dropped_rows']}",
        f"- Dropout target dropped rate: {coverage['manifest_summary'][DROPOUT_PROFILE]['target_dropped_rate']}",
        f"- Dropout forced target-retained rows: {coverage['manifest_summary'][DROPOUT_PROFILE]['target_drop_forced_retained_rows']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Significant Moved `routine_fetch`",
        "",
        "| Denominator | Policy | proxy `SR` | proposal recall | target dropped rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| clean all | `task_conditioned_budget_v0` | {clean_task['proxy_sr']} | {clean_task['proposal_recall']} | {clean_task['target_dropped_rate']} | {clean_task['mean_expected_search_cost']} | {clean_task['attempt_spl_proxy']} | {clean_task['mean_task_utility']} |",
        f"| dropout target-retained | `task_conditioned_budget_v0` | {retained_task['proxy_sr']} | {retained_task['proposal_recall']} | {retained_task['target_dropped_rate']} | {retained_task['mean_expected_search_cost']} | {retained_task['attempt_spl_proxy']} | {retained_task['mean_task_utility']} |",
        f"| dropout target-dropped | `task_conditioned_budget_v0` | {dropped_task['proxy_sr']} | {dropped_task['proposal_recall']} | {dropped_task['target_dropped_rate']} | {dropped_task['mean_expected_search_cost']} | {dropped_task['attempt_spl_proxy']} | {dropped_task['mean_task_utility']} |",
        f"| dropout target-retained | `reachable_first_task_conditioned_budget_v0` | {retained_reachable['proxy_sr']} | {retained_reachable['proposal_recall']} | {retained_reachable['target_dropped_rate']} | {retained_reachable['mean_expected_search_cost']} | {retained_reachable['attempt_spl_proxy']} | {retained_reachable['mean_task_utility']} |",
        f"| dropout target-dropped | `reachable_first_task_conditioned_budget_v0` | {dropped_reachable['proxy_sr']} | {dropped_reachable['proposal_recall']} | {dropped_reachable['target_dropped_rate']} | {dropped_reachable['mean_expected_search_cost']} | {dropped_reachable['attempt_spl_proxy']} | {dropped_reachable['mean_task_utility']} |",
        "",
        "## 논문 주장",
        "",
        "- E003-M06 supports controlled annotation-proxy proposal-recall stress evaluation.",
        "- E003-M06 supports separating target-retained and target-dropped denominators.",
        "- E003-M06 does not support real RGB-D or open-vocabulary detector robustness.",
        "",
        "## 에이전트 추론",
        "",
        "- Target-dropped rows approximate detector proposal recall failure more directly than score/rank jitter.",
        "- A positive retained-denominator result should not be mixed with target-dropped failures; both denominators are required.",
        "- Since the selected route is repository-local artifact transformation, Docker is not required here; future detector/open-vocabulary implementation must be Dockerized.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M06. Next step should analyze dropout failure boundary or add a false-positive/centroid-jitter profile.",
        "",
        "## Outputs",
        "",
        "- `noise_manifest.jsonl`",
        "- `noisy_query_rows.jsonl`",
        "- `noisy_candidate_rows.jsonl`",
        "- `predictions.jsonl`",
        "- `failure_rows.jsonl`",
        "- `metrics.json`",
        "- `coverage.json`",
        "- `report.md`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e001-m02-dir", type=Path, default=DEFAULT_E001_M02_DIR)
    parser.add_argument("--grid-dir", type=Path, default=DEFAULT_GRID_DIR)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.e001_m02_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.e001_m02_dir / "candidate_rows.jsonl")
    contract = load_json(args.contract)
    noisy_query_rows, noisy_candidate_rows, manifest_rows = build_noisy_rows(
        query_rows,
        candidate_rows,
        contract,
    )
    predictions = build_predictions(noisy_query_rows, noisy_candidate_rows, args.grid_dir)
    failure_rows = build_failure_rows(predictions)
    for row in failure_rows:
        row["eval_version"] = EVAL_VERSION
        row["next_test"] = "separate target-retained and target-dropped proposal-recall failure"
    metrics = build_metrics(predictions)
    coverage = build_coverage(
        query_rows,
        candidate_rows,
        noisy_query_rows,
        noisy_candidate_rows,
        manifest_rows,
        predictions,
        failure_rows,
        metrics,
        contract,
        args.out_dir,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "noise_manifest.jsonl", manifest_rows)
    write_jsonl(args.out_dir / "noisy_query_rows.jsonl", noisy_query_rows)
    write_jsonl(args.out_dir / "noisy_candidate_rows.jsonl", noisy_candidate_rows)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_jsonl(args.out_dir / "failure_rows.jsonl", failure_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(coverage, metrics, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "noisy_query_rows": coverage["noisy_query_rows"],
                "noisy_candidate_rows": coverage["noisy_candidate_rows"],
                "prediction_rows": coverage["prediction_rows"],
                "target_dropped_rows": coverage["manifest_summary"][DROPOUT_PROFILE]["target_dropped_rows"],
                "significant_moved_routine_task_retained": coverage[
                    "significant_moved_routine_task_retained_metrics"
                ],
                "significant_moved_routine_task_dropped": coverage[
                    "significant_moved_routine_task_dropped_metrics"
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
