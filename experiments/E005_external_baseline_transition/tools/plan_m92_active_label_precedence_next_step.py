#!/usr/bin/env python3
"""Decide whether M91 should go to query conversion or bounded batch rerun."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M92_active_label_precedence_next_step_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M82_DIR = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0" / "heldout_b02"
M91_DIR = EXP_ROOT / "artifacts" / "E005-M91_active_label_precedence_smoke_v0" / "heldout_b02"
M91_ANALYSIS_DIR = EXP_ROOT / "artifacts" / "E005-M91_active_label_precedence_analysis_v0"
M90_DIR = EXP_ROOT / "artifacts" / "E005-M90_label_normalization_prompt_scope_repair_v0"
M51_DIR = EXP_ROOT / "artifacts" / "E005-M51_h001_heldout_policy_replay_contract_v0"
VERSION = "e005_m92_active_label_precedence_next_step_v0"
BATCH_ID = "heldout_b02"
SCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"
H001_POLICY = "real_task_context_memory_trust_reobserve_v0"
CONTEXT_AGNOSTIC_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC_POLICY = "real_static_memory_only_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float, den: int | float) -> float | None:
    return round(float(num) / float(den), 6) if den else None


def safe_mean(values: list[int | float]) -> float | None:
    return round(float(mean(values)), 6) if values else None


def task_budget(task_context_id: str, candidate_count: int) -> int:
    if candidate_count <= 0:
        return 0
    if task_context_id == "routine_fetch":
        return min(candidate_count, 3)
    if task_context_id in {"high_value_fetch", "noisy_high_value_fetch"}:
        return min(candidate_count, 5)
    raise RuntimeError(f"unknown task_context_id: {task_context_id}")


def h001_detector_budget(adapter: dict[str, Any], task_context_id: str, candidate_count: int) -> int:
    if candidate_count <= 0:
        return 0
    state = str(adapter["expected_memory_state"])
    stale = bool(adapter["old_memory_is_stale"])
    if state == "trusted_or_low_motion" and not stale:
        if task_context_id == "routine_fetch":
            return 0
        if task_context_id == "high_value_fetch":
            return min(candidate_count, 3)
        if task_context_id == "noisy_high_value_fetch":
            return min(candidate_count, 1)
    if state == "review" and not stale:
        if task_context_id == "routine_fetch":
            return min(candidate_count, 3)
        if task_context_id == "high_value_fetch":
            return min(candidate_count, 5)
        if task_context_id == "noisy_high_value_fetch":
            return min(candidate_count, 3)
    if task_context_id == "routine_fetch":
        return min(candidate_count, 3)
    if task_context_id == "high_value_fetch":
        return min(candidate_count, 5)
    if task_context_id == "noisy_high_value_fetch":
        return min(candidate_count, 3)
    raise RuntimeError(f"unknown task_context_id: {task_context_id}")


def static_success(adapter: dict[str, Any]) -> bool:
    if "static_memory_success" in adapter:
        return bool(adapter["static_memory_success"])
    return float(adapter["scene_aligned_static_error_m"]) <= float(adapter["success_threshold_m"])


def proposal_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row.get("selection_score") or row.get("confidence") or 0.0),
            int(row.get("pre_cap_rank") or 10**9),
            str(row.get("proposal_uid") or ""),
        ),
    )


def rank_by_target(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rank, row in enumerate(proposal_order(rows), start=1):
        target_uid = row.get("matched_target_uid")
        if not target_uid or target_uid in out:
            continue
        out[str(target_uid)] = {
            "confidence": row.get("confidence"),
            "false_positive_before_target_count": rank - 1,
            "match_distance_m": row.get("match_distance_m"),
            "proposal_uid": row.get("proposal_uid"),
            "rank": rank,
        }
    return out


def m82_policy_success_by_scan(policy: str) -> dict[str, int]:
    rows = read_jsonl(M82_DIR / "policy_rows.jsonl")
    counts: Counter[str] = Counter()
    for row in rows:
        if row.get("policy") == policy and row.get("query_bridge_success"):
            counts[str(row.get("current_rescan_id"))] += 1
    return dict(counts)


def m82_scan_policy_rows(policy: str, scan_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in read_jsonl(M82_DIR / "policy_rows.jsonl")
        if row.get("policy") == policy and row.get("current_rescan_id") == scan_id
    ]


def active_labels_by_scan(prompt_set: dict[str, Any]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for row in prompt_set.get("labels", []):
        label = str(row.get("label_canonical", "")).strip()
        if not label:
            continue
        for scan_id in row.get("scan_ids", []):
            out[str(scan_id)].add(label)
    return out


def build_side_effect_rows(prompt_set: dict[str, Any], direct_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts = read_jsonl(M90_DIR / "prompt_conflict_rows.jsonl")
    conflicted_labels = {label for row in conflicts for label in row.get("canonical_labels", [])}
    active = active_labels_by_scan(prompt_set)
    query_rows_by_scan_label: Counter[tuple[str, str]] = Counter(
        (str(row["current_rescan_id"]), str(row["label_canonical"])) for row in direct_rows
    )
    rows: list[dict[str, Any]] = []
    for scan_id, labels in sorted(active.items()):
        exposed = sorted(labels & conflicted_labels)
        if len(exposed) <= 1:
            continue
        rows.append(
            {
                "active_conflicted_labels": exposed,
                "batch_id": BATCH_ID,
                "chair_rows": query_rows_by_scan_label.get((scan_id, "chair"), 0),
                "conflict_exposed_query_rows": sum(query_rows_by_scan_label.get((scan_id, label), 0) for label in exposed),
                "scan_id": scan_id,
                "stool_rows": query_rows_by_scan_label.get((scan_id, "stool"), 0),
            }
        )
    return rows


def build_query_conversion_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    direct_rows = [
        row
        for row in read_jsonl(M68_DIR / "batches" / BATCH_ID / "direct_bridge_query_rows.jsonl")
        if row.get("current_rescan_id") == SCAN_ID
    ]
    adapter_by_uid = {str(row["row_uid"]): row for row in read_jsonl(M51_DIR / "adapter_preview_rows.jsonl")}
    proposals = read_jsonl(M91_DIR / "matching" / "matched_proposals.jsonl")
    ranks = rank_by_target(proposals)
    candidate_count = len(proposal_order(proposals))

    m82_query_by_uid = {
        str(row["query_uid"]): row for row in read_jsonl(M82_DIR / "query_bridge_rows.jsonl") if row.get("current_rescan_id") == SCAN_ID
    }
    m82_h001_by_uid = {
        str(row["query_uid"]): row for row in m82_scan_policy_rows(H001_POLICY, SCAN_ID)
    }

    rows: list[dict[str, Any]] = []
    for direct in direct_rows:
        adapter = adapter_by_uid[str(direct["row_uid"])]
        target_uid = str(direct["target_uid"])
        rank_info = ranks.get(target_uid, {})
        rank = rank_info.get("rank")
        task_k = task_budget(str(direct["task_context_id"]), candidate_count)
        h001_k = h001_detector_budget(adapter, str(direct["task_context_id"]), candidate_count)
        old_success = static_success(adapter)
        old_first = bool(adapter["expected_memory_state"] == "trusted_or_low_motion" and not adapter["old_memory_is_stale"])
        h001_success = bool((old_first and old_success) or (rank is not None and int(rank) <= h001_k))
        rows.append(
            {
                "batch_id": BATCH_ID,
                "candidate_count": candidate_count,
                "current_rescan_id": SCAN_ID,
                "expected_memory_state": adapter["expected_memory_state"],
                "h001_detector_budget": h001_k,
                "h001_success_after_m91_one_scan_conversion": h001_success,
                "h001_success_before_m91_m82": bool(m82_h001_by_uid.get(str(direct["bridge_query_uid"]), {}).get("query_bridge_success")),
                "label_canonical": direct["label_canonical"],
                "m82_query_target_detected": bool(m82_query_by_uid.get(str(direct["bridge_query_uid"]), {}).get("query_target_detected")),
                "m91_detector_task_budget_success": bool(rank is not None and int(rank) <= task_k),
                "m91_detector_top5_success": bool(rank is not None and int(rank) <= 5),
                "m91_query_target_detected": rank is not None,
                "m91_target_rank": rank,
                "old_memory_first": old_first,
                "query_uid": direct["bridge_query_uid"],
                "row_band": direct["row_band"],
                "row_uid": direct["row_uid"],
                "static_memory_success": old_success,
                "target_uid": target_uid,
                "task_context_id": direct["task_context_id"],
                **{f"target_{key}": value for key, value in rank_info.items() if key != "rank"},
            }
        )
    summary = {
        "affected_query_rows": len(rows),
        "affected_unique_targets": len({row["target_uid"] for row in rows}),
        "candidate_count": candidate_count,
        "h001_success_after_rows": sum(1 for row in rows if row["h001_success_after_m91_one_scan_conversion"]),
        "h001_success_before_rows": sum(1 for row in rows if row["h001_success_before_m91_m82"]),
        "m82_query_target_detected_rows": sum(1 for row in rows if row["m82_query_target_detected"]),
        "m91_detector_task_budget_success_rows": sum(1 for row in rows if row["m91_detector_task_budget_success"]),
        "m91_detector_top5_success_rows": sum(1 for row in rows if row["m91_detector_top5_success"]),
        "m91_query_target_detected_rows": sum(1 for row in rows if row["m91_query_target_detected"]),
        "mean_m91_target_rank": safe_mean([int(row["m91_target_rank"]) for row in rows if row["m91_target_rank"] is not None]),
        "target_rank_by_uid": {target_uid: info["rank"] for target_uid, info in sorted(ranks.items())},
    }
    return rows, summary


def build_coverage(query_summary: dict[str, Any], side_effect_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m82_cov = read_json(M82_DIR / "coverage.json")
    m91_cov = read_json(M91_ANALYSIS_DIR / "coverage.json")
    m91_match = read_json(M91_DIR / "matching" / "coverage.json")
    b02_query_rows = int(m82_cov.get("query_rows") or 0)
    old_detected = int(m82_cov.get("query_target_detected_rows") or 0)
    old_top5 = int(m82_cov.get("real_detector_top5_success_rows") or 0)
    old_task = int(m82_cov.get("real_detector_task_budget_success_rows") or 0)
    old_h001 = int(m82_cov.get("real_h001_success_rows") or 0)
    detected_gain = int(query_summary["m91_query_target_detected_rows"]) - int(query_summary["m82_query_target_detected_rows"])
    top5_gain = int(query_summary["m91_detector_top5_success_rows"])
    task_gain = int(query_summary["m91_detector_task_budget_success_rows"])
    h001_gain = int(query_summary["h001_success_after_rows"]) - int(query_summary["h001_success_before_rows"])
    side_effect_rows_total = sum(int(row["conflict_exposed_query_rows"]) for row in side_effect_rows)
    side_effect_stool_rows = sum(int(row["stool_rows"]) for row in side_effect_rows)

    selected_next_route = "bounded_heldout_b02_rerun_before_full_query_claim"
    if side_effect_rows_total == 0 and h001_gain > 0:
        selected_next_route = "query_level_conversion_then_full_batch_if_needed"

    return {
        "status": "e005_m92_active_label_precedence_next_step_decision_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_id": BATCH_ID,
        "scan_id": SCAN_ID,
        "m91_status": m91_cov.get("status"),
        "m91_matching_status": m91_match.get("status"),
        "one_scan_query_conversion_ready": True,
        "affected_query_rows": query_summary["affected_query_rows"],
        "affected_unique_targets": query_summary["affected_unique_targets"],
        "affected_m82_target_detected_rows": query_summary["m82_query_target_detected_rows"],
        "affected_m91_target_detected_rows": query_summary["m91_query_target_detected_rows"],
        "affected_m91_detector_top5_success_rows": query_summary["m91_detector_top5_success_rows"],
        "affected_m91_detector_task_budget_success_rows": query_summary["m91_detector_task_budget_success_rows"],
        "affected_h001_success_before_rows": query_summary["h001_success_before_rows"],
        "affected_h001_success_after_rows": query_summary["h001_success_after_rows"],
        "affected_h001_success_delta_rows": h001_gain,
        "b02_lower_bound_query_target_detected_rows_if_no_side_effect": old_detected + detected_gain,
        "b02_lower_bound_detector_top5_rows_if_no_side_effect": old_top5 + top5_gain,
        "b02_lower_bound_detector_task_budget_rows_if_no_side_effect": old_task + task_gain,
        "b02_lower_bound_h001_rows_if_no_side_effect": old_h001 + h001_gain,
        "b02_query_rows": b02_query_rows,
        "b02_lower_bound_target_detected_rate_if_no_side_effect": safe_rate(old_detected + detected_gain, b02_query_rows),
        "side_effect_risk_scan_count": len(side_effect_rows),
        "side_effect_risk_query_rows": side_effect_rows_total,
        "side_effect_risk_stool_query_rows": side_effect_stool_rows,
        "selected_next_route": selected_next_route,
        "bounded_rerun_needed": selected_next_route == "bounded_heldout_b02_rerun_before_full_query_claim",
        "claim_boundary": {
            "m91_failure_specific_repair_smoke_ready": True,
            "m91_full_batch_query_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "next_recommended_unit": "E005-M93 bounded heldout_b02 active-label precedence rerun launch/verification",
    }


def build_report(coverage: dict[str, Any], query_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M92 Active-Label Precedence Next-Step Decision",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Affected scan: `{coverage['scan_id']}`.",
            f"- Affected query rows / targets: {coverage['affected_query_rows']} / {coverage['affected_unique_targets']}.",
            f"- M82 target detected rows on affected scan: {coverage['affected_m82_target_detected_rows']}.",
            f"- M91 target detected rows on affected scan: {coverage['affected_m91_target_detected_rows']}.",
            f"- M91 target ranks by uid: `{query_summary['target_rank_by_uid']}`.",
            f"- M91 detector top5 / task-budget success rows on affected scan: {coverage['affected_m91_detector_top5_success_rows']} / {coverage['affected_m91_detector_task_budget_success_rows']}.",
            f"- H001 success rows before / after one-scan conversion: {coverage['affected_h001_success_before_rows']} / {coverage['affected_h001_success_after_rows']}.",
            f"- b02 no-side-effect lower-bound target detected rows/rate: {coverage['b02_lower_bound_query_target_detected_rows_if_no_side_effect']} / {coverage['b02_lower_bound_target_detected_rate_if_no_side_effect']}.",
            f"- Side-effect risk scans / query rows / `stool` rows: {coverage['side_effect_risk_scan_count']} / {coverage['side_effect_risk_query_rows']} / {coverage['side_effect_risk_stool_query_rows']}.",
            f"- Selected next route: `{coverage['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M91 is valid as failure-specific repair smoke evidence.",
            "- One-scan conversion alone is not enough for a full b02 query claim because another b02 scan exposes the same `chair` / `stool` prompt conflict.",
            "- Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain unsupported.",
            "",
            "## Agent Inference",
            "",
            "- The repair should be promoted to a bounded `heldout_b02` rerun before updating the main query-level table.",
            "- The expected benefit is target-detection recovery, not immediate H001 success gain: recovered target ranks are mostly outside the H001 detector budget.",
            "- This keeps the direction defensible: M91/M92 support robustness diagnosis, while the main paper contribution remains semantic memory trust / re-observation / search-cost decision.",
            "",
        ]
    )


def main() -> int:
    m91_cov = read_json(M91_ANALYSIS_DIR / "coverage.json")
    m91_match = read_json(M91_DIR / "matching" / "coverage.json")
    if m91_cov.get("status") != "e005_m91_active_label_precedence_smoke_ready":
        raise RuntimeError(f"M91 analysis is not ready: {m91_cov.get('status')}")
    if m91_match.get("status") != "detector_matching_smoke_ready":
        raise RuntimeError(f"M91 matching is not ready: {m91_match.get('status')}")

    query_rows, query_summary = build_query_conversion_rows()
    direct_rows = read_jsonl(M68_DIR / "batches" / BATCH_ID / "direct_bridge_query_rows.jsonl")
    prompt_set = read_json(M68_DIR / "batches" / BATCH_ID / "prompt_set.json")
    side_effect_rows = build_side_effect_rows(prompt_set, direct_rows)
    coverage = build_coverage(query_summary, side_effect_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT_DIR / "one_scan_query_conversion_rows.jsonl", query_rows)
    write_jsonl(OUT_DIR / "side_effect_risk_rows.jsonl", side_effect_rows)
    write_json(OUT_DIR / "query_conversion_summary.json", query_summary)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, query_summary))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
