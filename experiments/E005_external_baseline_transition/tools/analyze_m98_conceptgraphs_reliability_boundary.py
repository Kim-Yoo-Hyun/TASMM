#!/usr/bin/env python3
"""Analyze ConceptGraphs-derived map reliability against real proposals and H001."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M98_conceptgraphs_reliability_boundary_v0"
VERSION = "e005_m98_conceptgraphs_reliability_boundary_v0"

M49_DIR = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M95_DIR = EXP_ROOT / "artifacts" / "E005-M95_real_proposal_paper_boundary_v0"
M97_DIR = EXP_ROOT / "artifacts" / "E005-M97_external_proposal_mapping_feasibility_v0"

POL_CG = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
POL_REAL_TOP5 = "real_detector_confidence_top5_v0"
POL_REAL_TASK = "real_detector_task_budget_v0"
POL_H001 = "real_task_context_memory_trust_reobserve_v0"
POL_CONTEXT = "real_context_agnostic_memory_trust_reobserve_v0"
POL_STATIC = "real_static_memory_only_v0"
POL_UNBOUNDED = "real_unbounded_old_memory_distance_guard_until_target_v0"


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bool_success(row: dict[str, Any], key: str = "query_bridge_success") -> bool:
    return bool(row.get(key))


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return round(mean(valid), 6) if valid else None


def load_policy_rows() -> dict[str, dict[str, dict[str, Any]]]:
    rows_by_query: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in read_jsonl(M75_DIR / "policy_rows.jsonl"):
        rows_by_query[row["query_uid"]][row["policy"]] = row
    return dict(rows_by_query)


def load_query_rows() -> dict[str, dict[str, Any]]:
    return {row["query_uid"]: row for row in read_jsonl(M75_DIR / "query_bridge_rows.jsonl")}


def pair_outcome(left_success: bool, right_success: bool, left_name: str, right_name: str) -> str:
    if left_success and right_success:
        return "both_success"
    if left_success:
        return f"{left_name}_only"
    if right_success:
        return f"{right_name}_only"
    return "both_fail"


def target_overlap(cg_target_detected: bool, real_target_detected: bool) -> str:
    if cg_target_detected and real_target_detected:
        return "both_map_and_real_target_detected"
    if cg_target_detected:
        return "map_only_target_detected"
    if real_target_detected:
        return "real_only_target_detected"
    return "neither_target_detected"


def reliability_group(
    cg_success: bool,
    real_top5_success: bool,
    real_task_success: bool,
    h001_success: bool,
    real_target_detected: bool,
) -> str:
    if h001_success and cg_success and real_top5_success:
        return "all_h001_map_real_top5_success"
    if h001_success and cg_success and not real_top5_success:
        return "h001_and_map_success_real_top5_failure"
    if h001_success and not cg_success and real_top5_success:
        return "h001_and_real_top5_success_map_failure"
    if h001_success and not cg_success and not real_top5_success:
        return "h001_recovers_both_map_and_real_top5_failure"
    if (not h001_success) and cg_success:
        return "map_success_h001_failure"
    if (not h001_success) and real_top5_success:
        return "real_top5_success_h001_failure"
    if real_target_detected and not real_task_success:
        return "target_detected_but_budget_h001_map_fail"
    return "shared_failure_no_map_no_detector_budget_no_h001"


def build_rows() -> list[dict[str, Any]]:
    policies = load_policy_rows()
    query_rows = load_query_rows()
    required = [POL_CG, POL_REAL_TOP5, POL_REAL_TASK, POL_H001, POL_CONTEXT, POL_STATIC, POL_UNBOUNDED]
    output = []
    for query_uid, policy_map in sorted(policies.items()):
        missing = [policy for policy in required if policy not in policy_map]
        if missing:
            raise RuntimeError(f"Missing policies for {query_uid}: {missing}")
        qrow = query_rows.get(query_uid, {})
        cg = policy_map[POL_CG]
        real_top5 = policy_map[POL_REAL_TOP5]
        real_task = policy_map[POL_REAL_TASK]
        h001 = policy_map[POL_H001]
        context = policy_map[POL_CONTEXT]
        static = policy_map[POL_STATIC]
        unbounded = policy_map[POL_UNBOUNDED]
        cg_success = bool_success(cg)
        real_top5_success = bool_success(real_top5)
        real_task_success = bool_success(real_task)
        h001_success = bool_success(h001)
        row = {
            "query_uid": query_uid,
            "row_uid": h001.get("row_uid"),
            "base_row_uid": h001.get("base_row_uid"),
            "pair_uid": h001.get("pair_uid"),
            "scan_id": h001.get("current_rescan_id"),
            "batch_id": qrow.get("batch_id"),
            "target_uid": h001.get("target_uid"),
            "label_canonical": h001.get("label_canonical"),
            "task_context_id": h001.get("task_context_id"),
            "row_band": h001.get("row_band"),
            "old_location_dead_end_expected": h001.get("old_location_dead_end_expected"),
            "conceptgraphs_target_detected": bool(cg.get("target_detected")),
            "conceptgraphs_success": cg_success,
            "conceptgraphs_target_rank": cg.get("target_rank"),
            "conceptgraphs_false_positive_before_target_count": cg.get("false_positive_before_target_count"),
            "conceptgraphs_expected_search_cost": cg.get("expected_search_cost"),
            "real_target_detected": bool(real_top5.get("target_detected")),
            "real_detector_top5_success": real_top5_success,
            "real_detector_task_budget_success": real_task_success,
            "real_detector_target_rank": real_top5.get("target_rank"),
            "real_detector_false_positive_before_target_count": real_top5.get("false_positive_before_target_count"),
            "real_detector_task_expected_search_cost": real_task.get("expected_search_cost"),
            "h001_success": h001_success,
            "h001_expected_search_cost": h001.get("expected_search_cost"),
            "h001_success_source": h001.get("success_source"),
            "context_agnostic_success": bool_success(context),
            "static_memory_success": bool_success(static),
            "unbounded_real_detector_success": bool_success(unbounded),
            "target_detection_overlap": target_overlap(bool(cg.get("target_detected")), bool(real_top5.get("target_detected"))),
            "map_real_top5_h001_group": reliability_group(
                cg_success,
                real_top5_success,
                real_task_success,
                h001_success,
                bool(real_top5.get("target_detected")),
            ),
            "h001_vs_conceptgraphs": pair_outcome(
                h001_success,
                cg_success,
                "h001",
                "conceptgraphs",
            ),
            "h001_vs_real_top5": pair_outcome(
                h001_success,
                real_top5_success,
                "h001",
                "real_top5",
            ),
            "conceptgraphs_vs_real_top5": pair_outcome(
                cg_success,
                real_top5_success,
                "conceptgraphs",
                "real_top5",
            ),
            "conceptgraphs_vs_real_task_budget": pair_outcome(
                cg_success,
                real_task_success,
                "conceptgraphs",
                "real_task_budget",
            ),
        }
        output.append(row)
    return output


def summarize(rows: list[dict[str, Any]], group_field: str, group_value: str | None = None) -> dict[str, Any]:
    subset = rows if group_value is None else [row for row in rows if row.get(group_field) == group_value]
    if not subset:
        return {"group_field": group_field, "group_value": group_value, "rows": 0}
    return {
        "group_field": group_field,
        "group_value": group_value if group_value is not None else "ALL",
        "rows": len(subset),
        "conceptgraphs_target_detected_rows": sum(row["conceptgraphs_target_detected"] for row in subset),
        "conceptgraphs_success_rows": sum(row["conceptgraphs_success"] for row in subset),
        "real_target_detected_rows": sum(row["real_target_detected"] for row in subset),
        "real_detector_top5_success_rows": sum(row["real_detector_top5_success"] for row in subset),
        "real_detector_task_budget_success_rows": sum(row["real_detector_task_budget_success"] for row in subset),
        "h001_success_rows": sum(row["h001_success"] for row in subset),
        "context_agnostic_success_rows": sum(row["context_agnostic_success"] for row in subset),
        "static_memory_success_rows": sum(row["static_memory_success"] for row in subset),
        "unbounded_real_detector_success_rows": sum(row["unbounded_real_detector_success"] for row in subset),
        "mean_conceptgraphs_rank_detected": safe_mean([row["conceptgraphs_target_rank"] for row in subset if row["conceptgraphs_target_detected"]]),
        "mean_real_detector_rank_detected": safe_mean([row["real_detector_target_rank"] for row in subset if row["real_target_detected"]]),
        "mean_conceptgraphs_fp_before_target": safe_mean([row["conceptgraphs_false_positive_before_target_count"] for row in subset if row["conceptgraphs_target_detected"]]),
        "mean_real_detector_fp_before_target": safe_mean([row["real_detector_false_positive_before_target_count"] for row in subset if row["real_target_detected"]]),
    }


def counter_rows(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts = Counter(row[field] for row in rows)
    return [
        {
            "field": field,
            "value": value,
            "rows": count,
            "rate": round(count / len(rows), 6) if rows else 0.0,
        }
        for value, count in counts.most_common()
    ]


def build_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = [summarize(rows, "ALL")]
    for field in ["row_band", "task_context_id", "batch_id"]:
        for value in sorted({row.get(field) for row in rows}):
            summaries.append(summarize(rows, field, value))
    return summaries


def build_pair_outcomes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for field in [
        "h001_vs_conceptgraphs",
        "h001_vs_real_top5",
        "conceptgraphs_vs_real_top5",
        "conceptgraphs_vs_real_task_budget",
        "target_detection_overlap",
        "map_real_top5_h001_group",
    ]:
        output.extend(counter_rows(rows, field))
    return output


def build_claim_boundary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["map_real_top5_h001_group"] for row in rows)
    pair_h001_cg = Counter(row["h001_vs_conceptgraphs"] for row in rows)
    target_overlap_counts = Counter(row["target_detection_overlap"] for row in rows)
    return [
        {
            "claim_id": "C-M98-001",
            "claim": "`ConceptGraphs` map candidates are useful as a reliability diagnostic, but not enough for final robustness.",
            "claim_type": "diagnostic_supported",
            "status": "supported_with_boundary",
            "evidence": f"`ConceptGraphs` strict top5 succeeds on {sum(row['conceptgraphs_success'] for row in rows)} / {len(rows)} rows and target-detects {sum(row['conceptgraphs_target_detected'] for row in rows)} / {len(rows)} rows.",
            "boundary": "M98 is not a new external runtime result and cannot prove final real RGB-D/open-vocabulary robustness.",
            "next_validation_requirement": "Use row groups to decide whether a heavier external proposal route is needed after M98.",
        },
        {
            "claim_id": "C-M98-002",
            "claim": "H001 recovers many rows where both external map strict-top5 and real detector top5 fail.",
            "claim_type": "memory_decision_diagnostic",
            "status": "supported_diagnostic",
            "evidence": f"`h001_recovers_both_map_and_real_top5_failure` rows: {counts['h001_recovers_both_map_and_real_top5_failure']}. H001-only vs `ConceptGraphs`: {pair_h001_cg['h001_only']}.",
            "boundary": "This supports memory-decision value, not final deployable policy or navigation.",
            "next_validation_requirement": "M98/M99 must separate old-memory recovery from real proposal coverage before stronger robustness claims.",
        },
        {
            "claim_id": "C-M98-003",
            "claim": "External map/proposal evidence still challenges H001 on a nonzero set of rows.",
            "claim_type": "reviewer_defense_boundary",
            "status": "must_report",
            "evidence": f"`map_success_h001_failure` rows: {counts['map_success_h001_failure']}; `real_top5_success_h001_failure` rows: {counts['real_top5_success_h001_failure']}.",
            "boundary": "Do not hide cases where external map or detector top5 succeeds but H001 fails.",
            "next_validation_requirement": "Inspect these rows before writing a paper-level superiority claim.",
        },
        {
            "claim_id": "C-M98-004",
            "claim": "A heavier external proposal route remains justified if shared coverage gaps are paper-critical.",
            "claim_type": "next_route_boundary",
            "status": "conditional",
            "evidence": f"Neither map nor real detector target-detects {target_overlap_counts['neither_target_detected']} / {len(rows)} rows; shared no-map/no-detector-budget/no-H001 failures: {counts['shared_failure_no_map_no_detector_budget_no_h001']}.",
            "boundary": "`OpenMask3D` and `HOV-SG` remain later high-value routes, but M98 alone does not launch them.",
            "next_validation_requirement": "After M98, choose between row inspection, external route repair, or navigation bridge design.",
        },
    ]


def report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    overall = summary_rows[0]

    def table(rows: list[dict[str, Any]], field: str) -> str:
        selected = [row for row in rows if row["field"] == field]
        lines = ["| Value | Rows | Rate |", "| --- | ---: | ---: |"]
        for row in selected:
            lines.append(f"| `{row['value']}` | {row['rows']} | {row['rate']:.6f} |")
        return "\n".join(lines)

    claim_lines = ["| Claim | Status | Evidence |", "| --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['evidence']} |")

    return f"""# E005-M98 ConceptGraphs-Derived Reliability Boundary

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- `ConceptGraphs` strict top5 success: {coverage["conceptgraphs_success_rows"]} / {coverage["query_rows"]}.
- Real detector top5 success: {coverage["real_detector_top5_success_rows"]} / {coverage["query_rows"]}.
- Real detector task-budget success: {coverage["real_detector_task_budget_success_rows"]} / {coverage["query_rows"]}.
- H001 real memory-trust success: {coverage["h001_success_rows"]} / {coverage["query_rows"]}.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Real navigation `SR` / `SPL` ready: false.

## Overall Summary

| Metric | Rows |
| --- | ---: |
| `ConceptGraphs` target detected | {overall["conceptgraphs_target_detected_rows"]} |
| `ConceptGraphs` strict top5 success | {overall["conceptgraphs_success_rows"]} |
| Real detector target detected | {overall["real_target_detected_rows"]} |
| Real detector top5 success | {overall["real_detector_top5_success_rows"]} |
| Real detector task-budget success | {overall["real_detector_task_budget_success_rows"]} |
| H001 success | {overall["h001_success_rows"]} |
| Context-agnostic success | {overall["context_agnostic_success_rows"]} |
| Static memory success | {overall["static_memory_success_rows"]} |

## H001 / Map / Real Detector Groups

{table(pair_rows, "map_real_top5_h001_group")}

## Target Detection Overlap

{table(pair_rows, "target_detection_overlap")}

## Pairwise Outcomes

### H001 vs `ConceptGraphs`

{table(pair_rows, "h001_vs_conceptgraphs")}

### H001 vs Real Detector Top5

{table(pair_rows, "h001_vs_real_top5")}

### `ConceptGraphs` vs Real Detector Top5

{table(pair_rows, "conceptgraphs_vs_real_top5")}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- `ConceptGraphs` is useful as a map/proposal reliability diagnostic because it is much stronger than real detector top5 under the same 195-row denominator.
- H001 still recovers many rows where both `ConceptGraphs` strict top5 and real detector top5 fail, so the semantic memory decision layer is not reducible to external map retrieval.
- The result is still not final real RGB-D/open-vocabulary robustness because M98 reuses existing artifacts and does not add a fresh proposal source.
- The next decision should inspect M98 row groups before choosing a heavier `OpenMask3D`/`HOV-SG` route or moving toward navigation bridge design.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m49 = read_json(M49_DIR / "coverage.json")
    m75 = read_json(M75_DIR / "coverage.json")
    m95 = read_json(M95_DIR / "coverage.json")
    m97 = read_json(M97_DIR / "coverage.json")
    rows = build_rows()
    summary_rows = build_summary_rows(rows)
    pair_rows = build_pair_outcomes(rows)
    claim_rows = build_claim_boundary(rows)
    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "conceptgraphs_success_rows": sum(row["conceptgraphs_success"] for row in rows),
        "conceptgraphs_target_detected_rows": sum(row["conceptgraphs_target_detected"] for row in rows),
        "h001_success_rows": sum(row["h001_success"] for row in rows),
        "m49_status": m49.get("status"),
        "m75_status": m75.get("status"),
        "m95_status": m95.get("status"),
        "m97_selected_first_route": m97.get("selected_first_route"),
        "next_recommended_unit": "E005-M99 row-group inspection or heavier external route decision",
        "query_rows": len(rows),
        "real_detector_task_budget_success_rows": sum(row["real_detector_task_budget_success"] for row in rows),
        "real_detector_top5_success_rows": sum(row["real_detector_top5_success"] for row in rows),
        "real_detector_target_detected_rows": sum(row["real_target_detected"] for row in rows),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "status": "e005_m98_conceptgraphs_reliability_boundary_ready",
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", {"coverage": coverage, "summary_rows": summary_rows, "pair_outcomes": pair_rows, "claims": claim_rows})
    write_jsonl(OUT_DIR / "row_group_rows.jsonl", rows)
    write_jsonl(OUT_DIR / "summary_rows.jsonl", summary_rows)
    write_csv(OUT_DIR / "summary_rows.csv", summary_rows)
    write_jsonl(OUT_DIR / "pair_outcome_rows.jsonl", pair_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(OUT_DIR / "report.md", report(coverage, summary_rows, pair_rows, claim_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
