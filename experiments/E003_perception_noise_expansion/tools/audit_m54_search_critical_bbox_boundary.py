#!/usr/bin/env python3
"""Audit whether bbox-depth detector failures are search-critical for E001/E002."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_QUERY_DIR = (
    RESEARCH_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_E001_EVAL_DIR = (
    RESEARCH_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M03_baseline_evaluation_v0"
)
DEFAULT_E002_EVAL_DIR = (
    RESEARCH_ROOT
    / "experiments"
    / "E002_path_cost_bridge"
    / "artifacts"
    / "E002-M09_reachable_first_scoring_v0"
)
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M45_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M45_scaled_candidate_pool_export_replay_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M54_search_critical_bbox_failure_boundary_v0"
M54_VERSION = "e003_m54_search_critical_bbox_failure_boundary_v0"
E001_PRIMARY_POLICY = "task_conditioned_budget_v0"
E002_PRIMARY_POLICY = "reachable_first_task_conditioned_budget_v0"
M45_POLICIES = (
    "confidence",
    "confidence_sqrt_depth",
    "confidence_sqrt_depth_support_temporal_v0",
)


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


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def false_positive_count(row: dict[str, Any]) -> int:
    return max(
        0,
        int(row.get("detector_proposal_rows", 0) or 0)
        - int(row.get("matched_proposal_rows", 0) or 0),
    )


def key(scan_id: Any, instance_id: Any) -> tuple[str, str]:
    return (str(scan_id), str(instance_id))


def build_label_stats(
    label_metric_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    visible_target_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    visible_by_label: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    scan_labels_by_label: dict[str, set[str]] = defaultdict(set)
    for row in visible_target_rows:
        label = str(row.get("label_canonical"))
        scan_id = str(row.get("scan_id"))
        scan_labels_by_label[label].add(scan_id)
        if bool(row.get("depth_consistent_visible_proxy")):
            visible_by_label[label]["visible_proxy_target_rows"] += 1
            if bool(row.get("m23_selected_matched")):
                visible_by_label[label]["visible_proxy_matched_target_rows"] += 1
            else:
                visible_by_label[label]["visible_proxy_missed_target_rows"] += 1
        if bool(row.get("centroid_frustum_visible_proxy")):
            visible_by_label[label]["centroid_frustum_visible_proxy_rows"] += 1

    target_by_label = Counter(str(row.get("label_canonical")) for row in target_rows)
    stats: dict[str, dict[str, Any]] = {}
    for row in label_metric_rows:
        label = str(row.get("label_canonical"))
        proposal_rows = int(row.get("detector_proposal_rows", 0) or 0)
        matched_proposal_rows = int(row.get("matched_proposal_rows", 0) or 0)
        matched_target_rows = int(row.get("matched_target_rows", 0) or 0)
        target_count = int(row.get("target_rows", 0) or 0)
        fp_rows = false_positive_count(row)
        visible = visible_by_label[label]
        visible_targets = int(visible.get("visible_proxy_target_rows", 0) or 0)
        visible_matched = int(visible.get("visible_proxy_matched_target_rows", 0) or 0)
        visible_missed = int(visible.get("visible_proxy_missed_target_rows", 0) or 0)
        risk_reasons = []
        if fp_rows >= 100:
            risk_reasons.append("high_false_positive_load")
        if proposal_rows and safe_rate(matched_proposal_rows, proposal_rows) is not None:
            if safe_rate(matched_proposal_rows, proposal_rows) < 0.1:
                risk_reasons.append("low_proposal_precision")
        if target_count and safe_rate(matched_target_rows, target_count) is not None:
            if safe_rate(matched_target_rows, target_count) < 0.75:
                risk_reasons.append("low_target_recall")
        if visible_missed:
            risk_reasons.append("depth_visible_proxy_target_miss")
        stats[label] = {
            "detector_proposal_rows": proposal_rows,
            "false_positive_proposal_rows": fp_rows,
            "false_positive_rate": safe_rate(fp_rows, proposal_rows),
            "label_canonical": label,
            "matched_proposal_rows": matched_proposal_rows,
            "matched_target_rows": matched_target_rows,
            "proposal_precision": safe_rate(matched_proposal_rows, proposal_rows),
            "risk_reasons": risk_reasons,
            "risk_score": 2 * int(fp_rows >= 100)
            + 2 * int(visible_missed > 0)
            + int(target_count > 0 and matched_target_rows / target_count < 0.75)
            + int(proposal_rows > 0 and matched_proposal_rows / proposal_rows < 0.1),
            "scan_count_with_label": len(scan_labels_by_label[label]),
            "target_recall": safe_rate(matched_target_rows, target_count),
            "target_rows": target_count,
            "target_rows_from_target_file": int(target_by_label[label]),
            "unmatched_target_rows": max(0, target_count - matched_target_rows),
            "visible_proxy_matched_target_rows": visible_matched,
            "visible_proxy_missed_target_rows": visible_missed,
            "visible_proxy_recall": safe_rate(visible_matched, visible_targets),
            "visible_proxy_target_rows": visible_targets,
        }
    return stats


def load_primary_predictions(rows: list[dict[str, Any]], policy: str, success_key: str) -> dict[str, dict[str, Any]]:
    output = {}
    for row in rows:
        if row.get("policy") != policy:
            continue
        item = dict(row)
        item["_primary_success"] = bool(row.get(success_key))
        output[str(row.get("row_uid"))] = item
    return output


def failure_map(rows: list[dict[str, Any]], policy: str) -> dict[str, dict[str, Any]]:
    output = {}
    for row in rows:
        if row.get("policy") == policy:
            output[str(row.get("row_uid"))] = row
    return output


def aggregate_decisions(
    queries: list[dict[str, Any]],
    e001_primary: dict[str, dict[str, Any]],
    e002_primary: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for query in queries:
        label = str(query.get("object_label"))
        item = rows.setdefault(
            label,
            {
                "e001_primary_failure_rows": 0,
                "e001_primary_rows": 0,
                "e002_primary_failure_rows": 0,
                "e002_primary_rows": 0,
                "label_canonical": label,
                "query_rows": 0,
                "row_bands": Counter(),
                "task_contexts": Counter(),
            },
        )
        item["query_rows"] += 1
        item["row_bands"][str(query.get("row_band"))] += 1
        item["task_contexts"][str(query.get("task_context_id"))] += 1
        e001 = e001_primary.get(str(query.get("row_uid")))
        if e001:
            item["e001_primary_rows"] += 1
            if not bool(e001.get("_primary_success")):
                item["e001_primary_failure_rows"] += 1
        e002 = e002_primary.get(str(query.get("row_uid")))
        if e002:
            item["e002_primary_rows"] += 1
            if not bool(e002.get("_primary_success")):
                item["e002_primary_failure_rows"] += 1
    for item in rows.values():
        item["e001_primary_failure_rate"] = safe_rate(
            int(item["e001_primary_failure_rows"]),
            int(item["e001_primary_rows"]),
        )
        item["e002_primary_failure_rate"] = safe_rate(
            int(item["e002_primary_failure_rows"]),
            int(item["e002_primary_rows"]),
        )
        item["row_bands"] = dict(sorted(item["row_bands"].items()))
        item["task_contexts"] = dict(sorted(item["task_contexts"].items()))
    return rows


def build_m45_label_rows(m45_dir: Path, selected_labels: set[str]) -> list[dict[str, Any]]:
    per_policy: dict[str, dict[str, dict[str, Any]]] = {}
    for policy in M45_POLICIES:
        path = m45_dir / "offline_replay" / policy / "matching" / "label_metrics.jsonl"
        if not path.exists():
            continue
        per_policy[policy] = {str(row.get("label_canonical")): row for row in load_jsonl(path)}
    confidence = per_policy.get("confidence", {})
    rows = []
    for label in sorted(selected_labels):
        base = confidence.get(label)
        base_matched = int(base.get("matched_target_rows", 0) or 0) if base else 0
        base_fp = false_positive_count(base) if base else 0
        for policy, by_label in per_policy.items():
            row = by_label.get(label)
            if not row:
                continue
            matched = int(row.get("matched_target_rows", 0) or 0)
            fp = false_positive_count(row)
            proposals = int(row.get("detector_proposal_rows", 0) or 0)
            rows.append(
                {
                    "delta_false_positive_rows_vs_confidence": fp - base_fp,
                    "delta_matched_target_rows_vs_confidence": matched - base_matched,
                    "detector_proposal_rows": proposals,
                    "false_positive_proposal_rows": fp,
                    "label_canonical": label,
                    "matched_target_rows": matched,
                    "policy": policy,
                    "proposal_precision": safe_rate(int(row.get("matched_proposal_rows", 0) or 0), proposals),
                    "target_recall": safe_rate(matched, int(row.get("target_rows", 0) or 0)),
                }
            )
    return rows


def build_query_audit_rows(
    queries: list[dict[str, Any]],
    target_by_key: dict[tuple[str, str], dict[str, Any]],
    label_stats: dict[str, dict[str, Any]],
    e001_primary: dict[str, dict[str, Any]],
    e002_primary: dict[str, dict[str, Any]],
    e001_failures: dict[str, dict[str, Any]],
    e002_failures: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for query in queries:
        label = str(query.get("object_label"))
        current_key = key(query.get("rescan_id"), query.get("object_instance_id_rescan"))
        reference_key = key(query.get("reference_scan_id"), query.get("object_instance_id_ref"))
        current_target = target_by_key.get(current_key)
        reference_target = target_by_key.get(reference_key)
        stats = label_stats.get(label)
        e001 = e001_primary.get(str(query.get("row_uid")))
        e002 = e002_primary.get(str(query.get("row_uid")))
        e001_success = bool(e001.get("_primary_success")) if e001 else None
        e002_success = bool(e002.get("_primary_success")) if e002 else None
        e001_failure = e001_failures.get(str(query.get("row_uid")))
        e002_failure = e002_failures.get(str(query.get("row_uid")))
        if current_target:
            causality_level = "exact_current_query_join"
        elif reference_target:
            causality_level = "reference_memory_only_join"
        elif stats:
            causality_level = "label_transfer_only"
        else:
            causality_level = "out_of_detector_scope"
        risk_reasons = list(stats.get("risk_reasons", [])) if stats else []
        existing_search_failure = (e001_success is False) or (e002_success is False)
        if current_target and not bool(current_target.get("matched")):
            search_critical_status = "direct_current_target_missed"
        elif current_target and stats and int(stats.get("false_positive_proposal_rows", 0)) > 0:
            search_critical_status = "direct_current_target_with_same_label_fp_pressure"
        elif existing_search_failure and risk_reasons:
            search_critical_status = "existing_search_failure_with_label_level_detector_risk"
        elif risk_reasons:
            search_critical_status = "label_level_detector_risk_no_current_proxy_failure"
        elif stats:
            search_critical_status = "label_level_low_risk_or_unresolved"
        else:
            search_critical_status = "out_of_detector_scope"
        rows.append(
            {
                "base_row_uid": query.get("base_row_uid"),
                "causality_level": causality_level,
                "current_detector_target_matched": bool(current_target.get("matched")) if current_target else None,
                "current_join_available": bool(current_target),
                "e001_failure_type": e001_failure.get("failure_type") if e001_failure else None,
                "e001_primary_success": e001_success,
                "e002_failure_type": e002_failure.get("failure_type") if e002_failure else None,
                "e002_primary_success": e002_success,
                "label_canonical": label,
                "m33_false_positive_proposal_rows": int(stats.get("false_positive_proposal_rows", 0)) if stats else None,
                "m33_target_recall": stats.get("target_recall") if stats else None,
                "m33_visible_proxy_missed_target_rows": int(stats.get("visible_proxy_missed_target_rows", 0)) if stats else None,
                "object_instance_id_ref": str(query.get("object_instance_id_ref")),
                "object_instance_id_rescan": str(query.get("object_instance_id_rescan")),
                "pair_uid": query.get("pair_uid"),
                "reference_detector_target_matched": bool(reference_target.get("matched")) if reference_target else None,
                "reference_join_available": bool(reference_target),
                "reference_scan_id": query.get("reference_scan_id"),
                "rescan_id": query.get("rescan_id"),
                "risk_reasons": risk_reasons,
                "row_band": query.get("row_band"),
                "row_uid": query.get("row_uid"),
                "search_critical_status": search_critical_status,
                "task_context_id": query.get("task_context_id"),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            str(item["causality_level"]),
            str(item["search_critical_status"]),
            str(item["label_canonical"]),
            str(item["row_uid"]),
        ),
    )


def build_label_risk_rows(
    decision_by_label: dict[str, dict[str, Any]],
    label_stats: dict[str, dict[str, Any]],
    m45_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m45_by_label_policy: dict[tuple[str, str], dict[str, Any]] = {
        (str(row["label_canonical"]), str(row["policy"])): row for row in m45_rows
    }
    rows = []
    for label, decision in decision_by_label.items():
        stats = label_stats.get(label)
        if not stats:
            rows.append(
                {
                    **decision,
                    "detector_overlap_scope": "out_of_detector_label_scope",
                    "m33_false_positive_proposal_rows": None,
                    "m33_proposal_precision": None,
                    "m33_target_recall": None,
                    "m33_visible_proxy_missed_target_rows": None,
                    "risk_reasons": [],
                    "search_bridge_priority": 0,
                }
            )
            continue
        e001_failures = int(decision.get("e001_primary_failure_rows", 0) or 0)
        e002_failures = int(decision.get("e002_primary_failure_rows", 0) or 0)
        risk_score = int(stats.get("risk_score", 0) or 0)
        priority = risk_score + 3 * int(e002_failures > 0) + 2 * int(e001_failures > 0)
        support_row = m45_by_label_policy.get((label, "confidence_sqrt_depth_support_temporal_v0"))
        sqrt_row = m45_by_label_policy.get((label, "confidence_sqrt_depth"))
        rows.append(
            {
                **decision,
                "detector_overlap_scope": "label_transfer_only",
                "m33_false_positive_proposal_rows": int(stats.get("false_positive_proposal_rows", 0) or 0),
                "m33_matched_target_rows": int(stats.get("matched_target_rows", 0) or 0),
                "m33_proposal_precision": stats.get("proposal_precision"),
                "m33_target_recall": stats.get("target_recall"),
                "m33_target_rows": int(stats.get("target_rows", 0) or 0),
                "m33_visible_proxy_missed_target_rows": int(stats.get("visible_proxy_missed_target_rows", 0) or 0),
                "m45_confidence_sqrt_depth_delta_fp": sqrt_row.get("delta_false_positive_rows_vs_confidence")
                if sqrt_row
                else None,
                "m45_confidence_sqrt_depth_delta_matched": sqrt_row.get("delta_matched_target_rows_vs_confidence")
                if sqrt_row
                else None,
                "m45_support_delta_fp": support_row.get("delta_false_positive_rows_vs_confidence")
                if support_row
                else None,
                "m45_support_delta_matched": support_row.get("delta_matched_target_rows_vs_confidence")
                if support_row
                else None,
                "risk_reasons": stats.get("risk_reasons", []),
                "search_bridge_priority": priority,
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item.get("search_bridge_priority", 0) or 0),
            -int(item.get("e002_primary_failure_rows", 0) or 0),
            -int(item.get("e001_primary_failure_rows", 0) or 0),
            -int(item.get("m33_false_positive_proposal_rows", 0) or 0),
            str(item["label_canonical"]),
        ),
    )


def summarize_queries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    causality_counts = Counter(str(row["causality_level"]) for row in rows)
    status_counts = Counter(str(row["search_critical_status"]) for row in rows)
    exact_current = [row for row in rows if row["causality_level"] == "exact_current_query_join"]
    reference_only = [row for row in rows if row["causality_level"] == "reference_memory_only_join"]
    risk_existing = [
        row
        for row in rows
        if row["search_critical_status"] == "existing_search_failure_with_label_level_detector_risk"
    ]
    return {
        "causality_counts": dict(sorted(causality_counts.items())),
        "exact_current_query_join_rows": len(exact_current),
        "existing_search_failure_with_label_level_detector_risk_rows": len(risk_existing),
        "label_transfer_or_reference_only_rows": len(reference_only)
        + causality_counts.get("label_transfer_only", 0),
        "reference_memory_only_join_rows": len(reference_only),
        "search_critical_status_counts": dict(sorted(status_counts.items())),
    }


def build_report(coverage: dict[str, Any], top_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E003-M54 Search-Critical Bbox Failure Boundary",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- E001 query rows: {coverage['e001_query_rows']}.",
        f"- E002 reachable-first rows: {coverage['e002_primary_rows']}.",
        f"- M33 detector scans / frames: {coverage['m33_evaluated_scan_count']} / {coverage['m33_evaluated_frame_count']}.",
        f"- E001 current `rescan_id` overlap with M33 detector scans: {coverage['current_rescan_scan_overlap_count']}.",
        f"- Exact current query-instance joins: {coverage['exact_current_query_join_rows']}.",
        f"- Reference-memory-only joins: {coverage['reference_memory_only_join_rows']}.",
        f"- Label overlap count: {coverage['label_overlap_count']}.",
        f"- Existing E001/E002 search failures with label-level detector risk: {coverage['existing_search_failure_with_label_level_detector_risk_rows']}.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Search-Critical Labels",
        "",
    ]
    for row in top_rows[:10]:
        lines.append(
            f"- `{row['label_canonical']}`: priority {row['search_bridge_priority']}, "
            f"E001 fail {row['e001_primary_failure_rows']}/{row['e001_primary_rows']}, "
            f"E002 fail {row['e002_primary_failure_rows']}/{row['e002_primary_rows']}, "
            f"M33 FP {row['m33_false_positive_proposal_rows']}, "
            f"target recall {row['m33_target_recall']}, "
            f"visible misses {row['m33_visible_proxy_missed_target_rows']}, "
            f"risk {row['risk_reasons']}."
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M54 does not establish a final real RGB-D/open-vocabulary search robustness claim.",
            "- E003-M54 supports a claim boundary: current M33/M45 detector failures cannot be causally attached to E001/E002 current search instances because the detector-ready scans do not overlap with E001 current rescans.",
            "- M54 can only support a label-level bridge risk until a dynamic-pair-aligned real-proposal denominator exists.",
            "",
            "## 에이전트 추론",
            "",
            "- `chair` and `pillow` are the strongest immediate bridge labels because they already cause E002 search failures and also show M33 detector risk.",
            "- High false-positive labels such as `plant`, `shelf`, `sofa`, `table`, and `box` remain detector-pressure risks, but they are not yet proven to cause E001/E002 decision failure in the current artifact alignment.",
            "- The next step should build a dynamic-pair-aligned bridge or explicitly convert the claim to label-level detector stress; another external detector alone will not fix the missing E001/E002 current-rescan join.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if `E003-M55 dynamic-pair-aligned real-proposal bridge gate` is accepted as the next route.",
            "- Choose immediate `OpenMask3D` only if the goal is proposal-quality evidence with a weaker search-bridge claim.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e001-query-dir", default=DEFAULT_E001_QUERY_DIR, type=Path)
    parser.add_argument("--e001-eval-dir", default=DEFAULT_E001_EVAL_DIR, type=Path)
    parser.add_argument("--e002-eval-dir", default=DEFAULT_E002_EVAL_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m45-dir", default=DEFAULT_M45_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queries = load_jsonl(args.e001_query_dir / "query_rows.jsonl")
    e001_predictions = load_jsonl(args.e001_eval_dir / "predictions.jsonl")
    e001_failure_rows = load_jsonl(args.e001_eval_dir / "failure_rows.jsonl")
    e002_predictions = load_jsonl(args.e002_eval_dir / "reachable_first_predictions.jsonl")
    e002_failure_rows = load_jsonl(args.e002_eval_dir / "failure_rows.jsonl")
    m33_coverage = load_json(args.m33_dir / "coverage.json")
    m45_coverage = load_json(args.m45_dir / "coverage.json")
    target_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_target_recall_rows.jsonl")
    label_metric_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_label_metrics.jsonl")
    visible_target_rows = load_jsonl(args.m33_dir / "visibility_denominator" / "target_denominator_rows.jsonl")

    target_by_key = {key(row.get("scan_id"), row.get("object_instance_id")): row for row in target_rows}
    label_stats = build_label_stats(label_metric_rows, target_rows, visible_target_rows)
    e001_primary = load_primary_predictions(e001_predictions, E001_PRIMARY_POLICY, "search_success")
    e002_primary = load_primary_predictions(e002_predictions, E002_PRIMARY_POLICY, "grid_proxy_sr")
    e001_failures = failure_map(e001_failure_rows, E001_PRIMARY_POLICY)
    e002_failures = failure_map(e002_failure_rows, E002_PRIMARY_POLICY)
    decision_by_label = aggregate_decisions(queries, e001_primary, e002_primary)
    query_labels = {str(row.get("object_label")) for row in queries}
    m45_label_rows = build_m45_label_rows(args.m45_dir, query_labels & set(label_stats))
    label_risk_rows = build_label_risk_rows(decision_by_label, label_stats, m45_label_rows)
    query_audit_rows = build_query_audit_rows(
        queries=queries,
        target_by_key=target_by_key,
        label_stats=label_stats,
        e001_primary=e001_primary,
        e002_primary=e002_primary,
        e001_failures=e001_failures,
        e002_failures=e002_failures,
    )
    query_summary = summarize_queries(query_audit_rows)

    e001_current_scans = {str(row.get("rescan_id")) for row in queries}
    e001_reference_scans = {str(row.get("reference_scan_id")) for row in queries}
    m33_scans = {str(row.get("scan_id")) for row in target_rows}
    current_rescan_overlap = e001_current_scans & m33_scans
    reference_scan_overlap = e001_reference_scans & m33_scans
    exact_current_keys = {
        key(row.get("rescan_id"), row.get("object_instance_id_rescan"))
        for row in queries
    } & set(target_by_key)
    reference_keys = {
        key(row.get("reference_scan_id"), row.get("object_instance_id_ref"))
        for row in queries
    } & set(target_by_key)
    top_search_critical = [
        row
        for row in label_risk_rows
        if row.get("detector_overlap_scope") == "label_transfer_only"
        and int(row.get("search_bridge_priority", 0) or 0) > 0
    ]
    e002_fail_labels = {
        str(row.get("object_label"))
        for row in e002_failure_rows
        if row.get("policy") == E002_PRIMARY_POLICY
    }
    e001_fail_labels = {
        str(row.get("object_label"))
        for row in e001_failure_rows
        if row.get("policy") == E001_PRIMARY_POLICY
    }
    label_overlap = query_labels & set(label_stats)
    e002_costs = [
        float(row.get("expected_grid_path_cost_m", 0) or 0)
        for row in e002_predictions
        if row.get("policy") == E002_PRIMARY_POLICY
    ]
    coverage = {
        **query_summary,
        "current_rescan_scan_overlap_count": len(current_rescan_overlap),
        "current_rescan_scan_overlap": sorted(current_rescan_overlap),
        "dynamic_pair_current_join_ready": bool(exact_current_keys),
        "e001_primary_failure_labels": sorted(e001_fail_labels),
        "e001_primary_failure_rows": sum(1 for row in e001_primary.values() if not row["_primary_success"]),
        "e001_primary_policy": E001_PRIMARY_POLICY,
        "e001_query_rows": len(queries),
        "e002_mean_expected_grid_path_cost_m": mean(e002_costs) if e002_costs else None,
        "e002_primary_failure_labels": sorted(e002_fail_labels),
        "e002_primary_failure_rows": sum(1 for row in e002_primary.values() if not row["_primary_success"]),
        "e002_primary_policy": E002_PRIMARY_POLICY,
        "e002_primary_rows": len(e002_primary),
        "exact_current_query_join_keys": [list(item) for item in sorted(exact_current_keys)],
        "label_overlap_count": len(label_overlap),
        "label_overlap": sorted(label_overlap),
        "m33_evaluated_frame_count": m33_coverage.get("evaluated_frame_count"),
        "m33_evaluated_scan_count": m33_coverage.get("evaluated_scan_count"),
        "m33_false_positive_proposal_rows": m33_coverage.get("false_positive_proposal_rows"),
        "m33_matched_target_rows": m33_coverage.get("matched_target_rows"),
        "m33_proposal_precision": m33_coverage.get("proposal_precision"),
        "m45_frozen_verdict": (m45_coverage.get("frozen_interpretation_contract_verdict") or {}).get("verdict"),
        "m45_support_aware_fail_redesign": bool(
            (m45_coverage.get("frozen_interpretation_contract_verdict") or {}).get("fail_redesign")
        ),
        "m54_version": M54_VERSION,
        "next_recommended_unit": "E003-M55 dynamic-pair-aligned real-proposal bridge gate",
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_search_claim_ready": False,
        "reference_memory_join_keys": [list(item) for item in sorted(reference_keys)],
        "reference_scan_overlap_count": len(reference_scan_overlap),
        "reference_scan_overlap": sorted(reference_scan_overlap),
        "search_critical_label_candidates": [
            {
                "e001_primary_failure_rows": row.get("e001_primary_failure_rows"),
                "e002_primary_failure_rows": row.get("e002_primary_failure_rows"),
                "label_canonical": row.get("label_canonical"),
                "m33_false_positive_proposal_rows": row.get("m33_false_positive_proposal_rows"),
                "m33_target_recall": row.get("m33_target_recall"),
                "m33_visible_proxy_missed_target_rows": row.get("m33_visible_proxy_missed_target_rows"),
                "risk_reasons": row.get("risk_reasons"),
                "search_bridge_priority": row.get("search_bridge_priority"),
            }
            for row in top_search_critical[:10]
        ],
        "status": "search_critical_bbox_failure_boundary_ready",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_jsonl(args.out_dir / "query_search_boundary_rows.jsonl", query_audit_rows)
    write_jsonl(args.out_dir / "label_search_risk_rows.jsonl", label_risk_rows)
    write_jsonl(args.out_dir / "m45_label_policy_delta_rows.jsonl", m45_label_rows)
    write_text(args.out_dir / "report.md", build_report(coverage, top_search_critical))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
