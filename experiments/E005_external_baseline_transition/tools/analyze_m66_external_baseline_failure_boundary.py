#!/usr/bin/env python3
"""Build E005-M66 external-baseline failure-boundary rows."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M66_external_baseline_failure_boundary_v0"
VERSION = "e005_m66_external_baseline_failure_boundary_v0"

M52_POLICY_ROWS = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0" / "policy_rows.jsonl"
M60_POLICY_ROWS = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "open3dsg_policy_rows.jsonl"
M64_POLICY_ROWS = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0" / "open3dsg_vocab_policy_rows.jsonl"
M65_TABLE_ROWS = EXP_ROOT / "artifacts" / "E005-M65_open3dsg_table_integration_v0" / "paper_table_rows.jsonl"

H001 = "task_context_memory_trust_reobserve_v0"
STATIC = "static_memory_only_v0"
CONTEXT_AGNOSTIC = "context_agnostic_memory_trust_reobserve_v0"
DETECTOR_TOP5 = "detector_top5_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
OPEN3DSG_PRIMARY = "open3dsg_objects_probs_bbox_strict_top5_v0"
OPEN3DSG_VOCAB = "open3dsg_predicted_terms_bbox_strict_top5_v0"

MAIN_POLICIES = [
    STATIC,
    DETECTOR_TOP5,
    CONCEPTGRAPHS,
    OPEN3DSG_PRIMARY,
    OPEN3DSG_VOCAB,
    CONTEXT_AGNOSTIC,
    H001,
]

PAIRINGS = [
    ("h001_vs_conceptgraphs", H001, CONCEPTGRAPHS),
    ("h001_vs_open3dsg_vocab", H001, OPEN3DSG_VOCAB),
    ("h001_vs_static", H001, STATIC),
    ("h001_vs_context_agnostic", H001, CONTEXT_AGNOSTIC),
    ("open3dsg_vocab_vs_primary", OPEN3DSG_VOCAB, OPEN3DSG_PRIMARY),
    ("open3dsg_vocab_vs_conceptgraphs", OPEN3DSG_VOCAB, CONCEPTGRAPHS),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def select_policy_rows(path: Path, policies: set[str]) -> dict[str, dict[str, dict[str, Any]]]:
    rows_by_policy: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in read_jsonl(path):
        policy = str(row.get("policy"))
        if policy in policies:
            rows_by_policy[policy][str(row["query_uid"])] = row
    return rows_by_policy


def outcome(a_success: bool, b_success: bool, a_name: str, b_name: str) -> str:
    if a_success and b_success:
        return "both_success"
    if a_success and not b_success:
        return f"{a_name}_only"
    if b_success and not a_success:
        return f"{b_name}_only"
    return "both_fail"


def boundary_label(row: dict[str, Any]) -> str:
    h001 = row[f"{H001}_success"]
    concept = row[f"{CONCEPTGRAPHS}_success"]
    vocab = row[f"{OPEN3DSG_VOCAB}_success"]
    static = row[f"{STATIC}_success"]
    context = row[f"{CONTEXT_AGNOSTIC}_success"]
    primary = row[f"{OPEN3DSG_PRIMARY}_success"]
    h001_source = row.get(f"{H001}_success_source")
    vocab_failure = row.get(f"{OPEN3DSG_VOCAB}_failure_class")
    primary_failure = row.get(f"{OPEN3DSG_PRIMARY}_failure_class")
    if h001 and concept and vocab:
        return "all_main_external_and_h001_success"
    if h001 and not concept and not vocab:
        if h001_source == "old_memory":
            return "h001_old_memory_recovers_external_map_failures"
        return "h001_reobservation_recovers_external_map_failures"
    if h001 and vocab and not concept:
        return "open3dsg_vocab_and_h001_recover_conceptgraphs_failure"
    if h001 and concept and not vocab:
        return "h001_and_conceptgraphs_recover_open3dsg_vocab_failure"
    if vocab and not primary:
        return "open3dsg_vocab_repairs_primary_label_mismatch"
    if h001 and not static:
        return "h001_recovers_static_stale_memory_failure"
    if h001 and not context:
        return "task_context_specific_gain_case"
    if context and not h001:
        return "context_agnostic_beats_task_context_case"
    if vocab and not h001:
        return "external_scene_graph_beats_h001_case"
    if not h001 and not concept and not vocab:
        if vocab_failure in {"target_object_not_in_predicted_term_candidates", "no_predicted_term_candidates"}:
            return "shared_failure_open_vocab_candidate_coverage"
        if primary_failure == "target_present_but_rank_gt_budget":
            return "shared_failure_rank_or_budget"
        return "shared_failure_unresolved_proxy_denominator"
    return "mixed_boundary_case"


def compact_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {
            "success": False,
            "target_detected": False,
            "target_rank": None,
            "expected_search_cost": None,
            "failure_class": "missing_policy_row",
            "success_source": "missing_policy_row",
            "decision_reason": "missing_policy_row",
        }
    return {
        "success": bool(row.get("query_bridge_success")),
        "target_detected": bool(row.get("target_detected")),
        "target_rank": row.get("target_rank"),
        "expected_search_cost": row.get("expected_search_cost"),
        "failure_class": row.get("failure_class"),
        "success_source": row.get("success_source"),
        "decision_reason": row.get("decision_reason"),
        "candidate_count": row.get("candidate_count"),
        "returned_location_count": row.get("returned_location_count"),
    }


def build_boundary_rows() -> list[dict[str, Any]]:
    m52 = select_policy_rows(M52_POLICY_ROWS, {STATIC, DETECTOR_TOP5, CONCEPTGRAPHS, CONTEXT_AGNOSTIC, H001})
    m60 = select_policy_rows(M60_POLICY_ROWS, {OPEN3DSG_PRIMARY})
    m64 = select_policy_rows(M64_POLICY_ROWS, {OPEN3DSG_VOCAB})
    all_by_policy: dict[str, dict[str, dict[str, Any]]] = {}
    all_by_policy.update(m52)
    all_by_policy.update(m60)
    all_by_policy.update(m64)
    query_uids = sorted(set().union(*(set(rows) for rows in all_by_policy.values())))
    rows: list[dict[str, Any]] = []
    for query_uid in query_uids:
        base = next(
            (
                all_by_policy[policy].get(query_uid)
                for policy in [H001, CONCEPTGRAPHS, OPEN3DSG_VOCAB, STATIC]
                if all_by_policy.get(policy, {}).get(query_uid)
            ),
            {},
        )
        row: dict[str, Any] = {
            "record_type": "e005_m66_external_baseline_failure_boundary",
            "version": VERSION,
            "query_uid": query_uid,
            "row_uid": base.get("row_uid"),
            "target_uid": base.get("target_uid"),
            "pair_uid": base.get("pair_uid"),
            "scan_id": base.get("current_rescan_id") or base.get("scan_id"),
            "label_canonical": base.get("label_canonical") or base.get("query_label"),
            "task_context_id": base.get("task_context_id"),
            "row_band": base.get("row_band"),
            "query_slice_id": base.get("query_slice_id") or base.get("expected_memory_state"),
            "old_location_dead_end_expected": bool(base.get("old_location_dead_end_expected")),
        }
        for policy in MAIN_POLICIES:
            compact = compact_policy(all_by_policy.get(policy, {}).get(query_uid))
            prefix = policy
            row[f"{prefix}_success"] = compact["success"]
            row[f"{prefix}_target_detected"] = compact["target_detected"]
            row[f"{prefix}_target_rank"] = compact["target_rank"]
            row[f"{prefix}_expected_search_cost"] = compact["expected_search_cost"]
            row[f"{prefix}_failure_class"] = compact["failure_class"]
            row[f"{prefix}_success_source"] = compact["success_source"]
            row[f"{prefix}_decision_reason"] = compact["decision_reason"]
        for outcome_name, a_policy, b_policy in PAIRINGS:
            row[outcome_name] = outcome(
                bool(row[f"{a_policy}_success"]),
                bool(row[f"{b_policy}_success"]),
                a_policy,
                b_policy,
            )
        row["boundary_label"] = boundary_label(row)
        row["human_intent_boundary"] = (
            "task_context_specific_gain"
            if row["h001_vs_context_agnostic"] == f"{H001}_only"
            else "task_context_specific_loss"
            if row["h001_vs_context_agnostic"] == f"{CONTEXT_AGNOSTIC}_only"
            else "no_task_context_specific_difference"
        )
        rows.append(row)
    return rows


def summarize(rows: list[dict[str, Any]], group_fields: list[str]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for field in group_fields:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(field))].append(row)
        for value, group in sorted(grouped.items()):
            entry: dict[str, Any] = {
                "record_type": "e005_m66_boundary_summary",
                "version": VERSION,
                "group_field": field,
                "group_value": value,
                "rows": len(group),
            }
            for policy in MAIN_POLICIES:
                entry[f"{policy}_success_rows"] = sum(1 for row in group if row[f"{policy}_success"])
            for outcome_name, _, _ in PAIRINGS:
                counts = Counter(str(row[outcome_name]) for row in group)
                for key, count in sorted(counts.items()):
                    entry[f"{outcome_name}:{key}"] = count
            label_counts = Counter(str(row["boundary_label"]) for row in group)
            for key, count in sorted(label_counts.items()):
                entry[f"boundary:{key}"] = count
            summary.append(entry)
    return summary


def claim_boundary_rows(boundary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["boundary_label"] for row in boundary_rows)
    pair_counts = {name: Counter(str(row[name]) for row in boundary_rows) for name, _, _ in PAIRINGS}
    return [
        {
            "claim_id": "C-M66-001",
            "claim_type": "allowed_main",
            "claim": "H001's external-baseline advantage is concentrated in rows where external map retrieval fails but old semantic memory or bounded re-observation succeeds.",
            "status": "ready_with_proxy_boundary",
            "evidence": {
                "h001_vs_conceptgraphs": dict(pair_counts["h001_vs_conceptgraphs"]),
                "h001_vs_open3dsg_vocab": dict(pair_counts["h001_vs_open3dsg_vocab"]),
                "boundary_counts": dict(counts),
            },
            "allowed_wording": "H001 recovers failure modes of external map retrieval on the fixed proxy-search denominator.",
            "forbidden_wording": "H001 is generally better than external mappers in real RGB-D/open-vocabulary robotics settings.",
        },
        {
            "claim_id": "C-M66-002",
            "claim_type": "allowed_baseline_boundary",
            "claim": "`Open3DSG` predicted-vocabulary adapter mainly repairs the primary-label vocabulary mismatch.",
            "status": "ready_with_adapter_boundary",
            "evidence": {
                "open3dsg_vocab_vs_primary": dict(pair_counts["open3dsg_vocab_vs_primary"]),
                "boundary_counts": dict(counts),
            },
            "allowed_wording": "The predicted-vocabulary adapter is a leakage-safe correction for query-vocabulary mismatch.",
            "forbidden_wording": "The adapter proves a new open-vocabulary mapping method.",
        },
        {
            "claim_id": "C-M66-003",
            "claim_type": "secondary_only",
            "claim": "Human intent is represented as structured task context, but the row-level boundary does not support it as the main claim.",
            "status": "secondary_ablation_only",
            "evidence": {
                "h001_vs_context_agnostic": dict(pair_counts["h001_vs_context_agnostic"]),
                "task_context_specific_gain_rows": sum(
                    1 for row in boundary_rows if row["human_intent_boundary"] == "task_context_specific_gain"
                ),
                "task_context_specific_loss_rows": sum(
                    1 for row in boundary_rows if row["human_intent_boundary"] == "task_context_specific_loss"
                ),
            },
            "allowed_wording": "Structured task context is retained as a condition and ablation.",
            "forbidden_wording": "Human intent understanding is the main source of improvement.",
        },
        {
            "claim_id": "C-M66-004",
            "claim_type": "blocked",
            "claim": "Final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL`.",
            "status": "blocked",
            "evidence": {
                "real_rgbd_open_vocab_claim_ready": False,
                "real_navigation_sr_spl_ready": False,
            },
            "allowed_wording": "M66 is a proxy-search failure-boundary table.",
            "forbidden_wording": "M66 validates real RGB-D/open-vocabulary robustness or real navigation.",
        },
    ]


def markdown_summary(summary_rows: list[dict[str, Any]], max_rows: int = 18) -> str:
    selected = summary_rows[:max_rows]
    lines = [
        "| Group | Rows | H001 | ConceptGraphs | Open3DSG vocab | Boundary highlights |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in selected:
        highlights = []
        for key, value in row.items():
            if key.startswith("boundary:") and value:
                highlights.append(f"{key.removeprefix('boundary:')}={value}")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{row['group_field']}={row['group_value']}",
                    str(row["rows"]),
                    str(row[f"{H001}_success_rows"]),
                    str(row[f"{CONCEPTGRAPHS}_success_rows"]),
                    str(row[f"{OPEN3DSG_VOCAB}_success_rows"]),
                    "; ".join(highlights[:3]),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_report(
    coverage: dict[str, Any],
    boundary_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> str:
    h001_concept = Counter(row["h001_vs_conceptgraphs"] for row in boundary_rows)
    h001_vocab = Counter(row["h001_vs_open3dsg_vocab"] for row in boundary_rows)
    vocab_primary = Counter(row["open3dsg_vocab_vs_primary"] for row in boundary_rows)
    human = Counter(row["human_intent_boundary"] for row in boundary_rows)
    lines = [
        "# E005-M66 External Baseline Failure Boundary",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Query rows: {coverage['query_rows']}.",
        f"- H001 vs `ConceptGraphs`: {dict(h001_concept)}.",
        f"- H001 vs `Open3DSG` predicted-vocabulary adapter: {dict(h001_vocab)}.",
        f"- `Open3DSG` predicted-vocabulary vs primary-label adapter: {dict(vocab_primary)}.",
        f"- Human intent boundary: {dict(human)}.",
        "",
        "## Boundary Summary",
        "",
        markdown_summary(summary_rows),
        "## Paper Claims",
        "",
        "- M66 supports a proxy-search failure-boundary claim, not a real RGB-D/open-vocabulary robustness claim.",
        "- `Open3DSG` predicted-vocabulary adapter should be presented as a bounded vocabulary-mismatch repair.",
        "- Human intent remains a structured task-context ablation because task-context-specific gains are sparse.",
        "",
        "## Agent Inference",
        "",
        "- The strongest next experimental expansion is real RGB-D/open-vocabulary robustness, because the current table boundary is now defensible.",
        "- Real navigation `SR` / `SPL` should wait until the robustness bridge has a stable denominator and baseline set.",
        "",
        "## Next",
        "",
        f"- {coverage['next_recommended_unit']}.",
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    boundary_rows = build_boundary_rows()
    if len(boundary_rows) != 195:
        raise RuntimeError(f"unexpected boundary row count: {len(boundary_rows)}")
    summary_rows = summarize(boundary_rows, ["row_band", "query_slice_id", "task_context_id", "label_canonical"])
    claims = claim_boundary_rows(boundary_rows)
    pair_counts = {name: dict(Counter(str(row[name]) for row in boundary_rows)) for name, _, _ in PAIRINGS}
    coverage = {
        "status": "e005_m66_external_baseline_failure_boundary_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_dir": str(OUT_DIR),
        "query_rows": len(boundary_rows),
        "summary_rows": len(summary_rows),
        "claim_boundary_rows": len(claims),
        "pair_outcome_counts": pair_counts,
        "boundary_label_counts": dict(sorted(Counter(row["boundary_label"] for row in boundary_rows).items())),
        "human_intent_boundary_counts": dict(sorted(Counter(row["human_intent_boundary"] for row in boundary_rows).items())),
        "real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M67 real RGB-D/open-vocabulary robustness expansion route decision",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "boundary_rows.jsonl", boundary_rows)
    write_jsonl(OUT_DIR / "summary_rows.jsonl", summary_rows)
    write_csv(OUT_DIR / "summary_rows.csv", summary_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claims)
    write_text(OUT_DIR / "report.md", build_report(coverage, boundary_rows, summary_rows, claims))
    return coverage


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
