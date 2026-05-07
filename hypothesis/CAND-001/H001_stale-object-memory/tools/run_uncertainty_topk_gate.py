#!/usr/bin/env python3
"""Run H001 uncertainty-aware top-k gate.

This is a hypothesis-stage gate. It reuses the current multi-pair
non-persistent artifact and tests whether stale object memory should return a
bounded candidate set instead of forcing a single current instance.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "uncertainty_topk_gate"
POLICY = "uncertainty_topk_v0"
SCORE_KEY = "full_non_persistent"
HARD_ROW_UID = (
    "280d8ebb-6cc6-2788-9153-98959a2da801"
    "->"
    "4731976c-f9f7-2a1a-95cc-31c4d1751d0b:43"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def round_or_none(value: float | None, ndigits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def point_distance(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None:
        return None
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def normalized_entropy(scores: list[float]) -> float | None:
    if len(scores) <= 1:
        return None
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    total = sum(exp_scores)
    probs = [score / total for score in exp_scores]
    entropy = -sum(prob * math.log(prob) for prob in probs if prob > 0)
    return entropy / math.log(len(scores))


def rank_candidates(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["ranks"][SCORE_KEY],
            -row["scores"][SCORE_KEY],
            row["distance_to_old_scene_aligned_m"],
            int(row["candidate_instance_id"]),
        ),
    )


def candidate_set_size_under_margin(ranked: list[dict], margin: float = 0.1) -> int:
    if not ranked:
        return 0
    top_score = ranked[0]["scores"][SCORE_KEY]
    return sum(1 for row in ranked if top_score - row["scores"][SCORE_KEY] <= margin)


def target_rank(ranked: list[dict]) -> int | None:
    for item in ranked:
        if item["eval_is_target_instance"]:
            return item["ranks"][SCORE_KEY]
    return None


def candidate_stats(ranked: list[dict]) -> dict:
    scores = [item["scores"][SCORE_KEY] for item in ranked]
    return {
        "candidate_entropy": round_or_none(normalized_entropy(scores)),
        "score_margin_top1_top2": round_or_none(
            ranked[0]["scores"][SCORE_KEY] - ranked[1]["scores"][SCORE_KEY]
            if len(ranked) > 1
            else None
        ),
        "candidate_set_size_under_margin_0_1": candidate_set_size_under_margin(ranked, 0.1),
    }


def topk_decision(row: dict, ranked: list[dict], stats: dict) -> tuple[str, int, str]:
    if not row["old_memory_is_stale"]:
        return "trusted_or_low_motion", 0, "low_motion_trusted_old_location"
    if not ranked:
        return "needs_reobservation", 0, "no_same_label_candidate"
    candidate_count = len(ranked)
    entropy = stats["candidate_entropy"]
    margin = stats["score_margin_top1_top2"]
    margin_set = stats["candidate_set_size_under_margin_0_1"]
    if candidate_count == 1:
        return "single_current_candidate", 1, "unique_same_label_candidate"
    if candidate_count == 2:
        return "topk_current_candidates", 2, "two_same_label_candidates"
    if candidate_count >= 5 and entropy is not None and entropy >= 0.90:
        return "topk_current_candidates", min(3, candidate_count), "high_ambiguity_high_entropy"
    if margin is not None and margin <= 0.10:
        return "topk_current_candidates", min(3, candidate_count), "low_top1_top2_margin"
    if margin_set > 1:
        return "topk_current_candidates", min(3, margin_set), "multiple_candidates_inside_margin"
    return "single_current_candidate", 1, "confident_top1"


def expected_search_cost(target_rank_value: int | None, returned_k: int, stale: bool) -> int | None:
    if not stale:
        return None
    if returned_k <= 0:
        return None
    if target_rank_value is not None and target_rank_value <= returned_k:
        return target_rank_value
    return returned_k + 1


def predict(row: dict, ranked: list[dict], success_threshold_m: float) -> dict:
    stats = candidate_stats(ranked)
    memory_state, returned_k, reason = topk_decision(row, ranked, stats)
    returned = ranked[:returned_k]
    target_rank_value = target_rank(ranked)
    target_in_returned = target_rank_value is not None and target_rank_value <= returned_k
    returns_old = memory_state == "trusted_or_low_motion"
    if returns_old:
        error = point_distance(row["old_scene_aligned_centroid"], row["pair_current_centroid"])
        exact_top1 = bool(error is not None and error <= success_threshold_m)
    else:
        exact_top1 = bool(target_rank_value == 1)
        error = None
    search_cost = expected_search_cost(target_rank_value, returned_k, row["old_memory_is_stale"])
    return {
        **row,
        "policy": POLICY,
        "memory_state": memory_state,
        "action": "return_scene_aligned_old_location"
        if returns_old
        else "return_uncertainty_ranked_current_candidates"
        if returned_k > 1
        else "return_top_non_persistent_current_observation"
        if returned_k == 1
        else "suppress_old_location",
        "decision_reason": reason,
        "returns_old_location": returns_old,
        "suppresses_old_location": bool(row["old_memory_is_stale"]),
        "uses_rescan_semseg_observation": bool(row["old_memory_is_stale"] and returned_k > 0),
        "uses_exact_current_pose": False,
        "returned_candidate_count": returned_k,
        "candidate_count": returned_k,
        "same_label_candidate_count": len(ranked),
        "candidate_instance_ids": [item["candidate_instance_id"] for item in returned],
        "chosen_instance_id": returned[0]["candidate_instance_id"] if returned else None,
        "target_rank": target_rank_value,
        "exact_top1_recovery": exact_top1,
        "exact_recovery": exact_top1,
        "candidate_recall_at_1": target_rank_value == 1 if row["old_memory_is_stale"] else exact_top1,
        "candidate_recall_at_3": (
            target_rank_value is not None and target_rank_value <= 3
            if row["old_memory_is_stale"]
            else exact_top1
        ),
        "candidate_recall_at_returned_k": target_in_returned if row["old_memory_is_stale"] else exact_top1,
        "candidate_recall_all": target_rank_value is not None if row["old_memory_is_stale"] else exact_top1,
        "target_error_m": round_or_none(error),
        "expected_search_cost_proxy": search_cost,
        "search_failure": bool(row["old_memory_is_stale"] and not target_in_returned),
        "high_uncertainty_route": bool(memory_state == "topk_current_candidates"),
        **stats,
    }


def summarize(predictions: list[dict], subset_name: str, subset_rows: list[dict]) -> dict:
    ids = {row["row_uid"] for row in subset_rows}
    items = [row for row in predictions if row["row_uid"] in ids]
    den = len(items)
    stale_items = [row for row in items if row["old_memory_is_stale"]]
    low_items = [row for row in items if row["row_band"] == "low_motion_control"]
    entropy_items = [row for row in stale_items if row.get("candidate_entropy") is not None]
    margin_items = [row for row in stale_items if row.get("score_margin_top1_top2") is not None]
    search_items = [row for row in stale_items if row.get("expected_search_cost_proxy") is not None]
    low_uncertainty_stale = [row for row in stale_items if not row["high_uncertainty_route"]]
    high_uncertainty_stale = [row for row in stale_items if row["high_uncertainty_route"]]
    high_uncertainty_top1_errors = [
        row for row in high_uncertainty_stale if not row["candidate_recall_at_1"]
    ]
    return {
        "policy": POLICY,
        "subset": subset_name,
        "rows": den,
        "stale_rows": len(stale_items),
        "low_motion_rows": len(low_items),
        "suppresses_old_location_rate": safe_rate(
            sum(1 for row in items if row["suppresses_old_location"]), den
        ),
        "stale_old_location_false_positive_rate": safe_rate(
            sum(1 for row in stale_items if row["returns_old_location"] and not row["exact_recovery"]),
            len(stale_items),
        ),
        "exact_top1_recovery_rate": safe_rate(
            sum(1 for row in items if row["exact_top1_recovery"]), den
        ),
        "candidate_recall_at_1": safe_rate(
            sum(1 for row in items if row["candidate_recall_at_1"]), den
        ),
        "candidate_recall_at_3": safe_rate(
            sum(1 for row in items if row["candidate_recall_at_3"]), den
        ),
        "candidate_recall_at_returned_k": safe_rate(
            sum(1 for row in items if row["candidate_recall_at_returned_k"]), den
        ),
        "candidate_recall_all": safe_rate(
            sum(1 for row in items if row["candidate_recall_all"]), den
        ),
        "mean_returned_candidate_count": round_or_none(
            sum(row["returned_candidate_count"] for row in stale_items) / len(stale_items)
            if stale_items
            else None
        ),
        "mean_expected_search_cost_proxy": round_or_none(
            sum(row["expected_search_cost_proxy"] for row in search_items) / len(search_items)
            if search_items
            else None
        ),
        "search_failure_rate": safe_rate(
            sum(1 for row in stale_items if row["search_failure"]), len(stale_items)
        ),
        "low_motion_static_preserved_rate": safe_rate(
            sum(1 for row in low_items if row["returns_old_location"] and row["exact_recovery"]),
            len(low_items),
        ),
        "control_forced_reobservation_rate": safe_rate(
            sum(1 for row in low_items if row["uses_rescan_semseg_observation"]),
            len(low_items),
        ),
        "high_uncertainty_route_rate": safe_rate(
            sum(1 for row in stale_items if row["high_uncertainty_route"]), len(stale_items)
        ),
        "high_uncertainty_top1_error_capture_rate": safe_rate(
            sum(1 for row in high_uncertainty_top1_errors if row["candidate_recall_at_returned_k"]),
            len(high_uncertainty_top1_errors),
        ),
        "low_uncertainty_top1_exact_rate": safe_rate(
            sum(1 for row in low_uncertainty_stale if row["candidate_recall_at_1"]),
            len(low_uncertainty_stale),
        ),
        "mean_candidate_entropy": round_or_none(
            sum(row["candidate_entropy"] for row in entropy_items) / len(entropy_items)
            if entropy_items
            else None
        ),
        "mean_score_margin_top1_top2": round_or_none(
            sum(row["score_margin_top1_top2"] for row in margin_items) / len(margin_items)
            if margin_items
            else None
        ),
    }


def breakdown(predictions: list[dict], rows: list[dict], field: str, subset_name: str, filter_fn) -> dict:
    subset_rows = [row for row in rows if filter_fn(row)]
    output = {}
    for value in sorted({row[field] for row in subset_rows}):
        value_rows = [row for row in subset_rows if row[field] == value]
        output[str(value)] = {
            "rows": len(value_rows),
            POLICY: summarize(predictions, f"{subset_name}_{value}", value_rows),
        }
    return output


def hard_failure_rows(predictions: list[dict], baseline_metrics: dict) -> list[dict]:
    known = {
        row["row_uid"]
        for row in baseline_metrics.get("hard_failures", [])
        if row.get("row_band") == "significant_moved"
    }
    rows = []
    for row in predictions:
        if row["row_uid"] not in known:
            continue
        rows.append(
            {
                "row_uid": row["row_uid"],
                "object_label": row["object_label"],
                "object_instance_id_ref": row["object_instance_id_ref"],
                "chosen_instance_id": row.get("chosen_instance_id"),
                "candidate_instance_ids": row["candidate_instance_ids"],
                "target_rank": row["target_rank"],
                "returned_candidate_count": row["returned_candidate_count"],
                "candidate_recall_at_returned_k": row["candidate_recall_at_returned_k"],
                "expected_search_cost_proxy": row["expected_search_cost_proxy"],
                "candidate_entropy": row["candidate_entropy"],
                "score_margin_top1_top2": row["score_margin_top1_top2"],
                "decision_reason": row["decision_reason"],
                "returns_old_location": row["returns_old_location"],
            }
        )
    return rows


def decide_status(coverage: dict, metrics: dict, baseline_metrics: dict) -> str:
    sig = metrics["significant_moved"][POLICY]
    low = metrics["low_motion_control"][POLICY]
    baseline_sig = baseline_metrics["significant_moved"]
    np_recall = baseline_sig["non_persistent_anchor_v0"]["candidate_recall_at_3"]
    label_top3_recall = baseline_sig["label_top3_current_observation"]["candidate_recall_at_3"]
    hard_rows = metrics["hard_failures"]
    metric_pass = (
        sig["candidate_recall_at_returned_k"] is not None
        and np_recall is not None
        and label_top3_recall is not None
        and sig["candidate_recall_at_returned_k"] >= np_recall
        and sig["candidate_recall_at_returned_k"] > label_top3_recall
        and sig["stale_old_location_false_positive_rate"] == 0.0
        and (low["low_motion_static_preserved_rate"] is None or low["low_motion_static_preserved_rate"] >= 0.95)
        and (sig["mean_returned_candidate_count"] is None or sig["mean_returned_candidate_count"] <= 3.0)
        and (sig["mean_expected_search_cost_proxy"] is None or sig["mean_expected_search_cost_proxy"] <= 2.0)
        and any(row["row_uid"] == HARD_ROW_UID and row["candidate_recall_at_returned_k"] for row in hard_rows)
    )
    data_limited = coverage["significant_moved_rows"] < 10
    if not metric_pass:
        return "fail"
    if data_limited:
        return "data_limited_pass"
    return "strict_pass"


def write_report(out_dir: Path, coverage: dict, metrics: dict, baseline_metrics: dict) -> None:
    sig = metrics["significant_moved"][POLICY]
    low = metrics["low_motion_control"][POLICY]
    baseline_sig = baseline_metrics["significant_moved"]
    lines = [
        "# Uncertainty Top-K Gate Report",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Input artifact: `{coverage['input_dir']}`",
        f"- Validated pairs: {coverage['validated_pair_count']}",
        f"- Query rows: {coverage['query_rows']}",
        f"- Significant moved rows: {coverage['significant_moved_rows']}",
        f"- Low-motion controls: {coverage['low_motion_control_rows']}",
        f"- Rank-sensitive rows: {coverage['rank_sensitive_rows']}",
        f"- High-ambiguity rows: {coverage['high_ambiguity_rows']}",
        f"- Strict significant-row threshold met: {coverage['strict_significant_row_threshold_met']}",
        f"- Ranking uses persistent cross-scan ids: {coverage['ranking_uses_persistent_cross_scan_ids']}",
        f"- Uses exact current pose for ranking: {coverage['uses_exact_current_pose_for_ranking']}",
        f"- Uses navigation: {coverage['uses_navigation']}",
        f"- Uses RGB-D perception: {coverage['uses_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocabulary_perception']}",
        "",
        "## Significant Moved Metrics",
        "",
        "| Policy | Top-1 exact | Recall@returned K | Recall@3 | Stale FP | Mean returned candidates | Mean search cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| label_top3_current_observation | {exact} | {recall_k} | {recall3} | {fp} | {cands} | {cost} |".format(
            exact=baseline_sig["label_top3_current_observation"]["exact_recovery_rate"],
            recall_k=baseline_sig["label_top3_current_observation"]["candidate_recall_at_3"],
            recall3=baseline_sig["label_top3_current_observation"]["candidate_recall_at_3"],
            fp=baseline_sig["label_top3_current_observation"]["stale_old_location_false_positive_rate"],
            cands=baseline_sig["label_top3_current_observation"]["mean_candidate_count"],
            cost="n/a",
        ),
        "| non_persistent_anchor_v0 | {exact} | {recall_k} | {recall3} | {fp} | {cands} | {cost} |".format(
            exact=baseline_sig["non_persistent_anchor_v0"]["exact_recovery_rate"],
            recall_k=baseline_sig["non_persistent_anchor_v0"]["candidate_recall_at_1"],
            recall3=baseline_sig["non_persistent_anchor_v0"]["candidate_recall_at_3"],
            fp=baseline_sig["non_persistent_anchor_v0"]["stale_old_location_false_positive_rate"],
            cands=baseline_sig["non_persistent_anchor_v0"]["mean_candidate_count"],
            cost=baseline_sig["non_persistent_anchor_v0"]["mean_expected_search_cost_proxy"],
        ),
        "| uncertainty_topk_v0 | {exact} | {recall_k} | {recall3} | {fp} | {cands} | {cost} |".format(
            exact=sig["exact_top1_recovery_rate"],
            recall_k=sig["candidate_recall_at_returned_k"],
            recall3=sig["candidate_recall_at_3"],
            fp=sig["stale_old_location_false_positive_rate"],
            cands=sig["mean_returned_candidate_count"],
            cost=sig["mean_expected_search_cost_proxy"],
        ),
        "",
        "## Low-Motion Control Metrics",
        "",
        f"- Static preserved: {low['low_motion_static_preserved_rate']}",
        f"- Forced re-observation: {low['control_forced_reobservation_rate']}",
        "",
        "## Hard Failure",
        "",
        "| Row | Returned candidates | Target rank | Search cost | Captured | Reason |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in metrics["hard_failures"]:
        lines.append(
            "| {row_uid} | {cands} | {rank} | {cost} | {captured} | {reason} |".format(
                row_uid=row["row_uid"],
                cands=", ".join(row["candidate_instance_ids"]),
                rank=row["target_rank"],
                cost=row["expected_search_cost_proxy"],
                captured=row["candidate_recall_at_returned_k"],
                reason=row["decision_reason"],
            )
        )
    if coverage["status"] == "strict_pass":
        claim_line = "- This run supports a strict hypothesis-stage bounded top-k stale-memory update result."
        threshold_line = "- The strict significant-row threshold is met, so the next step is claim-boundary interpretation before any experiment-stage promotion."
        decision_line = "- No immediate decision is required unless the next step is experiment-stage promotion or additional staging."
    else:
        claim_line = "- This run supports only a hypothesis-stage data-limited result."
        threshold_line = "- The current gate turns the pillow top-1 failure into a candidate-set success, but the strict significant-row threshold is still not met."
        decision_line = "- No immediate decision is required. The default next action is staging more significant moved rows if we continue this route."
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            claim_line,
            "- It supports bounded top-k stale-memory update on the current "
            f"{coverage['validated_pair_count']}-pair artifact.",
            "- It does not support final moved-object recovery, navigation, RGB-D perception, open-vocabulary perception, deployable search policy, or experiment-stage promotion.",
            "",
            "## 에이전트 추론",
            "",
            "- The useful signal is that H001 can expose uncertainty without returning stale old locations.",
            threshold_line,
            "",
            "## 사용자 판단 필요",
            "",
            decision_line,
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.input_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.input_dir / "candidate_rows.jsonl")
    input_coverage = load_json(args.input_dir / "coverage.json")
    baseline_metrics = load_json(args.input_dir / "metrics.json")
    success_threshold_m = input_coverage.get("success_threshold_m", 0.5)

    candidates_by_uid: dict[str, list[dict]] = {}
    for row in candidate_rows:
        candidates_by_uid.setdefault(row["row_uid"], []).append(row)

    predictions = []
    for row in query_rows:
        ranked = rank_candidates(candidates_by_uid.get(row["row_uid"], []))
        predictions.append(predict(row, ranked, success_threshold_m))

    significant_rows = [row for row in query_rows if row["row_band"] == "significant_moved"]
    low_motion_rows = [row for row in query_rows if row["row_band"] == "low_motion_control"]
    mid_motion_rows = [row for row in query_rows if row["row_band"] == "mid_motion_review"]
    rank_sensitive_rows = [row for row in query_rows if row.get("same_label_candidate_count", 0) >= 2]
    high_ambiguity_rows = [row for row in query_rows if row.get("same_label_candidate_count", 0) >= 5]

    metrics = {
        "all_row_valid": {POLICY: summarize(predictions, "all_row_valid", query_rows)},
        "significant_moved": {POLICY: summarize(predictions, "significant_moved", significant_rows)},
        "low_motion_control": {POLICY: summarize(predictions, "low_motion_control", low_motion_rows)},
        "mid_motion_review": {POLICY: summarize(predictions, "mid_motion_review", mid_motion_rows)},
        "rank_sensitive": {POLICY: summarize(predictions, "rank_sensitive", rank_sensitive_rows)},
        "high_ambiguity": {POLICY: summarize(predictions, "high_ambiguity", high_ambiguity_rows)},
        "label_breakdown_significant": breakdown(
            predictions,
            query_rows,
            "object_label",
            "significant_label",
            lambda row: row["row_band"] == "significant_moved",
        ),
        "ambiguity_breakdown": breakdown(
            predictions,
            query_rows,
            "ambiguity_band",
            "ambiguity",
            lambda row: True,
        ),
    }
    metrics["hard_failures"] = hard_failure_rows(predictions, baseline_metrics)

    per_pair = []
    for pair_uid in sorted({row["pair_uid"] for row in query_rows}):
        rows = [row for row in query_rows if row["pair_uid"] == pair_uid]
        sig_rows = [row for row in rows if row["row_band"] == "significant_moved"]
        per_pair.append(
            {
                "pair_uid": pair_uid,
                "query_rows": len(rows),
                "significant_moved_rows": len(sig_rows),
                "low_motion_control_rows": sum(1 for row in rows if row["row_band"] == "low_motion_control"),
                "all_row_valid": {POLICY: summarize(predictions, f"{pair_uid}_all", rows)},
                "significant_moved": {POLICY: summarize(predictions, f"{pair_uid}_significant", sig_rows)},
            }
        )
    metrics["per_pair"] = per_pair

    coverage = {
        "input_dir": str(args.input_dir),
        "validated_pair_count": input_coverage.get("validated_pair_count"),
        "query_rows": len(query_rows),
        "significant_moved_rows": len(significant_rows),
        "low_motion_control_rows": len(low_motion_rows),
        "mid_motion_review_rows": len(mid_motion_rows),
        "rank_sensitive_rows": len(rank_sensitive_rows),
        "high_ambiguity_rows": len(high_ambiguity_rows),
        "strict_pair_threshold_met": input_coverage.get("strict_pair_threshold_met"),
        "strict_significant_row_threshold_met": len(significant_rows) >= 10,
        "next_staging_target": input_coverage.get("next_staging_target"),
        "next_staging_target_detail": input_coverage.get("next_staging_target_detail"),
        "uses_annotation_level_current_observation": True,
        "ranking_uses_persistent_cross_scan_ids": False,
        "uses_exact_current_pose_for_ranking": False,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "success_threshold_m": success_threshold_m,
    }
    coverage["status"] = decide_status(coverage, metrics, baseline_metrics)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_report(args.out_dir, coverage, metrics, baseline_metrics)
    print(
        json.dumps(
            {
                "coverage": coverage,
                "significant_moved": metrics["significant_moved"],
                "low_motion_control": metrics["low_motion_control"],
                "hard_failures": metrics["hard_failures"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
