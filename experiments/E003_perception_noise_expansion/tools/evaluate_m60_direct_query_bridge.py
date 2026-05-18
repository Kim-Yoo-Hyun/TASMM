#!/usr/bin/env python3
"""Evaluate the E003-M60 direct current-rescan query-level detector bridge."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M58_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M58_direct_current_rescan_bridge_design_v0"
DEFAULT_M59_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M59_direct_current_rescan_detector_run_v0"
DEFAULT_E001_DIR = REPO_ROOT / "experiments" / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
M60_VERSION = "e003_m60_direct_current_rescan_query_bridge_v0"
POLICIES = [
    "detector_top1_v0",
    "detector_top3_v0",
    "detector_top5_v0",
    "detector_task_budget_v0",
    "detector_unbounded_until_target_or_exhausted_v0",
]


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


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def task_conditioned_budget(query: dict[str, Any], candidate_count: int) -> tuple[int, str]:
    if candidate_count <= 0:
        return 0, "no_detector_candidate"
    if query["expected_memory_state"] == "trusted_or_low_motion":
        return 0, "trusted_low_motion_memory"

    max_budget = int(query["max_candidate_budget"])
    high_ambiguity_budget = int(query["high_ambiguity_budget"])
    if query["task_context_id"] == "routine_fetch":
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "routine_trivial_candidate"
        if query["ambiguity_band"] == "high_ambiguity":
            return min(candidate_count, max_budget, high_ambiguity_budget), "routine_high_ambiguity_bounded"
        return min(candidate_count, max_budget, 3), "routine_rank_sensitive_budget"

    if query["task_context_id"] in {"high_value_fetch", "noisy_high_value_fetch"}:
        if query["ambiguity_band"] == "trivial_candidate":
            return 1, "high_value_trivial_candidate"
        return min(candidate_count, max_budget), "high_value_expand_budget"

    raise RuntimeError(f"unknown task_context_id: {query['task_context_id']}")


def proposal_score(row: dict[str, Any]) -> float:
    value = row.get("selection_score")
    if value is None:
        value = row.get("confidence", 0.0)
    return float(value or 0.0)


def order_proposals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -proposal_score(row),
            int(row.get("pre_cap_rank") or 10**9),
            int(row.get("pre_cap_group_rank") or 10**9),
            str(row.get("proposal_uid", "")),
        ),
    )


def policy_budget(policy: str, e001_query: dict[str, Any], candidate_count: int, target_rank: int | None) -> tuple[int, str]:
    if policy == "detector_top1_v0":
        return min(1, candidate_count), "detector_confidence_top1"
    if policy == "detector_top3_v0":
        return min(3, candidate_count), "detector_confidence_top3"
    if policy == "detector_top5_v0":
        return min(5, candidate_count), "detector_confidence_top5"
    if policy == "detector_task_budget_v0":
        return task_conditioned_budget(e001_query, candidate_count)
    if policy == "detector_unbounded_until_target_or_exhausted_v0":
        if target_rank is not None:
            return target_rank, "visit_until_detected_target"
        return candidate_count, "exhaust_detector_candidates_then_old_location"
    raise RuntimeError(f"unknown policy: {policy}")


def build_query_rows(
    direct_rows: list[dict[str, Any]],
    e001_by_row_uid: dict[str, dict[str, Any]],
    matched_proposals: list[dict[str, Any]],
    target_recall_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    proposals_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in matched_proposals:
        proposals_by_scan_label[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    for key, rows in list(proposals_by_scan_label.items()):
        proposals_by_scan_label[key] = order_proposals(rows)

    query_rows = []
    for direct in direct_rows:
        e001 = e001_by_row_uid[direct["row_uid"]]
        target_uid = str(direct["target_uid"])
        same_label = proposals_by_scan_label.get((direct["current_rescan_id"], direct["label_canonical"]), [])
        target_proposal = None
        target_rank = None
        for rank, proposal in enumerate(same_label, start=1):
            if str(proposal.get("matched_target_uid")) == target_uid:
                target_proposal = proposal
                target_rank = rank
                break

        target_recall = target_recall_by_uid.get(target_uid, {})
        query_target_detected = bool(target_recall.get("matched")) and target_rank is not None
        false_positive_before_target = None
        if query_target_detected and target_rank is not None:
            false_positive_before_target = sum(
                1
                for proposal in same_label[: target_rank - 1]
                if str(proposal.get("matched_target_uid")) != target_uid
            )

        static_success = float(e001["scene_aligned_static_error_m"]) <= float(e001["success_threshold_m"])
        old_location_dead_end_expected = bool(e001.get("old_location_dead_end_expected")) or bool(
            e001.get("old_memory_is_stale") and not static_success
        )
        query_rows.append(
            {
                "m60_version": M60_VERSION,
                "bridge_query_uid": direct["bridge_query_uid"],
                "row_uid": direct["row_uid"],
                "base_row_uid": direct["base_row_uid"],
                "pair_uid": direct["pair_uid"],
                "reference_scan_id": direct["reference_scan_id"],
                "current_rescan_id": direct["current_rescan_id"],
                "target_uid": target_uid,
                "object_instance_id_rescan": direct["object_instance_id_rescan"],
                "label_canonical": direct["label_canonical"],
                "task_context_id": direct["task_context_id"],
                "row_band": direct["row_band"],
                "ambiguity_band": e001["ambiguity_band"],
                "expected_memory_state": e001["expected_memory_state"],
                "old_memory_is_stale": bool(e001["old_memory_is_stale"]),
                "old_location_dead_end_expected": old_location_dead_end_expected,
                "scene_aligned_static_error_m": e001["scene_aligned_static_error_m"],
                "success_threshold_m": e001["success_threshold_m"],
                "e001_primary_success": bool(direct["e001_primary_success"]),
                "e001_failure_type": direct["e001_failure_type"],
                "e002_primary_success": direct.get("e002_primary_success"),
                "e002_failure_type": direct.get("e002_failure_type"),
                "query_target_detected": query_target_detected,
                "query_target_rank_by_detector_score": target_rank,
                "query_target_best_proposal_uid": target_proposal.get("proposal_uid") if target_proposal else None,
                "query_target_best_match_distance_m": target_proposal.get("match_distance_m") if target_proposal else None,
                "query_target_best_confidence": target_proposal.get("confidence") if target_proposal else None,
                "same_label_detector_proposal_count": len(same_label),
                "same_label_false_positive_count": sum(
                    1 for proposal in same_label if str(proposal.get("matched_target_uid")) != target_uid
                ),
                "same_label_matched_other_target_count": sum(
                    1
                    for proposal in same_label
                    if proposal.get("match_status") == "matched" and str(proposal.get("matched_target_uid")) != target_uid
                ),
                "same_label_unmatched_false_positive_count": sum(
                    1 for proposal in same_label if proposal.get("match_status") != "matched"
                ),
                "false_positive_before_target_count": false_positive_before_target,
                "target_recall_best_proposal_uid": target_recall.get("best_proposal_uid"),
                "target_recall_best_match_distance_m": target_recall.get("best_match_distance_m"),
                "allowed_policy_inputs": [
                    "current_rescan_id",
                    "label_canonical",
                    "detector proposal confidence/centroid",
                    "task_context_id",
                    "pre-evaluation staleness metadata",
                ],
                "blocked_policy_inputs": [
                    "target_uid",
                    "object_instance_id_rescan",
                    "matched_3dssg_instance_id",
                    "match_distance_m",
                    "e001/e002 success labels",
                ],
            }
        )
    return query_rows


def build_policy_rows(query_rows: list[dict[str, Any]], e001_by_row_uid: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for query in query_rows:
        e001 = e001_by_row_uid[query["row_uid"]]
        candidate_count = int(query["same_label_detector_proposal_count"])
        target_rank = query["query_target_rank_by_detector_score"]
        for policy in POLICIES:
            returned_k, reason = policy_budget(policy, e001, candidate_count, target_rank)
            success = bool(query["query_target_detected"] and target_rank is not None and target_rank <= returned_k)
            rank_in_returned = target_rank if success else None
            expected_cost = int(target_rank) if success and target_rank is not None else int(returned_k) + 1
            old_dead_end_avoided = bool(query["old_location_dead_end_expected"] and success)
            rows.append(
                {
                    "m60_version": M60_VERSION,
                    "row_uid": query["row_uid"],
                    "base_row_uid": query["base_row_uid"],
                    "pair_uid": query["pair_uid"],
                    "target_uid": query["target_uid"],
                    "current_rescan_id": query["current_rescan_id"],
                    "label_canonical": query["label_canonical"],
                    "task_context_id": query["task_context_id"],
                    "row_band": query["row_band"],
                    "policy": policy,
                    "decision_reason": reason,
                    "query_target_detected": query["query_target_detected"],
                    "target_rank": target_rank,
                    "target_rank_in_returned": rank_in_returned,
                    "returned_location_count": returned_k,
                    "query_bridge_success": success,
                    "detector_bridge_resolved_e001_failure": bool(not query["e001_primary_success"] and success),
                    "detector_bridge_resolved_e002_failure": bool(query["e002_primary_success"] is False and success),
                    "e002_failure_in_scope": bool(query["e002_primary_success"] is False),
                    "same_label_detector_proposal_count": candidate_count,
                    "same_label_false_positive_count": query["same_label_false_positive_count"],
                    "false_positive_before_target_count": query["false_positive_before_target_count"],
                    "expected_search_cost": expected_cost,
                    "attempt_spl_proxy": attempt_spl(success, expected_cost),
                    "old_location_dead_end_expected": query["old_location_dead_end_expected"],
                    "stale_old_location_dead_end_avoided": old_dead_end_avoided,
                    "real_navigation_sr_spl_ready": False,
                    "real_rgbd_open_vocab_query_claim_ready": False,
                }
            )
    return rows


def summarize_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    e002_rows = [row for row in rows if row["e002_failure_in_scope"]]
    stale_rows = [row for row in rows if row["old_location_dead_end_expected"]]
    return {
        "rows": len(rows),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "e001_failure_resolved_rows": sum(1 for row in rows if row["detector_bridge_resolved_e001_failure"]),
        "e001_failure_resolved_rate": safe_rate(
            sum(1 for row in rows if row["detector_bridge_resolved_e001_failure"]),
            len(rows),
        ),
        "e002_failure_resolved_rows": sum(1 for row in rows if row["detector_bridge_resolved_e002_failure"]),
        "e002_failure_resolved_rate": safe_rate(
            sum(1 for row in rows if row["detector_bridge_resolved_e002_failure"]),
            len(e002_rows),
        ),
        "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_avoided_rows": sum(1 for row in stale_rows if row["stale_old_location_dead_end_avoided"]),
        "old_location_dead_end_avoided_rate": safe_rate(
            sum(1 for row in stale_rows if row["stale_old_location_dead_end_avoided"]),
            len(stale_rows),
        ),
    }


def summarize(query_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy = {}
    for policy in POLICIES:
        by_policy[policy] = summarize_policy([row for row in policy_rows if row["policy"] == policy])
    detected = [row for row in query_rows if row["query_target_detected"]]
    unique_target_uids = sorted({row["target_uid"] for row in query_rows})
    detected_target_uids = sorted({row["target_uid"] for row in detected})
    false_before = [
        int(row["false_positive_before_target_count"])
        for row in detected
        if row["false_positive_before_target_count"] is not None
    ]
    return {
        "query_rows": len(query_rows),
        "unique_target_uids": len(unique_target_uids),
        "query_target_detected_rows": len(detected),
        "query_target_detected_rate": safe_rate(len(detected), len(query_rows)),
        "unique_target_detected_uids": len(detected_target_uids),
        "unique_target_detected_rate": safe_rate(len(detected_target_uids), len(unique_target_uids)),
        "mean_target_rank_when_detected": safe_mean(
            [int(row["query_target_rank_by_detector_score"]) for row in detected if row["query_target_rank_by_detector_score"]]
        ),
        "mean_false_positive_before_target_when_detected": safe_mean(false_before),
        "mean_same_label_detector_proposals_per_query": safe_mean(
            [int(row["same_label_detector_proposal_count"]) for row in query_rows]
        ),
        "policy_metrics": by_policy,
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    task_policy = metrics["policy_metrics"]["detector_task_budget_v0"]
    unbounded = metrics["policy_metrics"]["detector_unbounded_until_target_or_exhausted_v0"]
    top5 = metrics["policy_metrics"]["detector_top5_v0"]
    lines = [
        "# E003-M60 Direct Current-Rescan Query Bridge",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Direct bridge query rows: {metrics['query_rows']}",
        f"- Unique bridge targets: {metrics['unique_target_uids']}",
        f"- Query target detected rows: {metrics['query_target_detected_rows']}",
        f"- Query target detected rate: {metrics['query_target_detected_rate']}",
        f"- Unique target detected rate: {metrics['unique_target_detected_rate']}",
        f"- Mean target rank when detected: {metrics['mean_target_rank_when_detected']}",
        f"- Mean false positives before target when detected: {metrics['mean_false_positive_before_target_when_detected']}",
        f"- `detector_task_budget_v0` success rows/rate: {task_policy['query_bridge_success_rows']} / {task_policy['query_bridge_success_rate']}",
        f"- `detector_top5_v0` success rows/rate: {top5['query_bridge_success_rows']} / {top5['query_bridge_success_rate']}",
        f"- `detector_unbounded_until_target_or_exhausted_v0` success rows/rate: {unbounded['query_bridge_success_rows']} / {unbounded['query_bridge_success_rate']}",
        f"- M59 proposal rows: {coverage['m59_prediction_rows']}",
        f"- M59 validator errors/warnings: {coverage['m59_validator_error_rows']} / {coverage['m59_validator_warning_rows']}",
        f"- M59 matching precision smoke: {coverage['m59_proposal_precision_smoke']}",
        f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
        f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
        "",
        "## 논문 주장",
        "",
        "- E003-M60 supports a direct current-rescan query-level bridge diagnostic.",
        "- E003-M60 shows whether M59 detector proposals can recover the exact E001/E002 search-failure targets.",
        "- E003-M60 does not yet support a final real RGB-D/open-vocabulary search robustness claim because the denominator has only 7 query rows and no external baseline comparison.",
        "",
        "## 에이전트 추론",
        "",
        "- Target detection and search-budget success must remain separate.",
        "- The detector finds some missed current targets, but task-budget success can still fail when the target is ranked behind false positives.",
        "- The next unit should analyze whether this is mainly detector recall failure, false-positive/rank failure, or task-budget mismatch before jumping to a heavier external baseline.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M60. Continue to a bridge failure/rank analysis gate before external baseline expansion.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m58-dir", default=DEFAULT_M58_DIR, type=Path)
    parser.add_argument("--m59-dir", default=DEFAULT_M59_DIR, type=Path)
    parser.add_argument("--e001-dir", default=DEFAULT_E001_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    direct_rows = load_jsonl(args.m58_dir / "direct_bridge_query_rows.jsonl")
    e001_rows = load_jsonl(args.e001_dir / "query_rows.jsonl")
    matched_proposals = load_jsonl(args.m59_dir / "matching" / "matched_proposals.jsonl")
    target_recall_rows = load_jsonl(args.m59_dir / "matching" / "target_recall_rows.jsonl")
    m59_coverage = load_json(args.m59_dir / "coverage.json")
    m59_matching = load_json(args.m59_dir / "matching" / "coverage.json")

    e001_by_row_uid = {str(row["row_uid"]): row for row in e001_rows}
    missing = sorted(row["row_uid"] for row in direct_rows if str(row["row_uid"]) not in e001_by_row_uid)
    if missing:
        raise RuntimeError(f"missing E001 query rows: {missing}")

    target_recall_by_uid = {str(row["target_uid"]): row for row in target_recall_rows}
    query_rows = build_query_rows(
        direct_rows=direct_rows,
        e001_by_row_uid=e001_by_row_uid,
        matched_proposals=matched_proposals,
        target_recall_by_uid=target_recall_by_uid,
    )
    policy_rows = build_policy_rows(query_rows=query_rows, e001_by_row_uid=e001_by_row_uid)
    metrics = summarize(query_rows=query_rows, policy_rows=policy_rows)

    task_success = metrics["policy_metrics"]["detector_task_budget_v0"]["query_bridge_success_rows"]
    detected = metrics["query_target_detected_rows"]
    status = "direct_query_bridge_ready"
    if detected == 0:
        status = "direct_query_bridge_detector_target_miss"
    elif task_success == 0:
        status = "direct_query_bridge_budget_rank_gap"

    coverage = {
        "detector_budget_policy_success_rows": task_success,
        "direct_bridge_query_rows": len(query_rows),
        "m58_dir": str(args.m58_dir),
        "m59_dir": str(args.m59_dir),
        "m59_matching_status": m59_matching.get("status"),
        "m59_prediction_rows": m59_coverage.get("prediction_rows"),
        "m59_proposal_precision_smoke": m59_matching.get("proposal_precision_smoke"),
        "m59_scan_target_recall_smoke": m59_matching.get("scan_target_recall_smoke"),
        "m59_validator_error_rows": m59_coverage.get("validator_error_rows"),
        "m59_validator_warning_rows": m59_coverage.get("validator_warning_rows"),
        "m60_version": M60_VERSION,
        "next_recommended_unit": "E003-M61 direct bridge rank/failure analysis before external baseline expansion",
        "paper_table_command_ready": False,
        "policy_rows": len(policy_rows),
        "query_target_detected_rows": detected,
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "status": status,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "query_bridge_rows.jsonl", query_rows)
    write_jsonl(args.out_dir / "policy_rows.jsonl", policy_rows)
    write_json(args.out_dir / "metrics.json", metrics)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, metrics))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status in {"direct_query_bridge_ready", "direct_query_bridge_budget_rank_gap"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
