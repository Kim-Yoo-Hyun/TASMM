#!/usr/bin/env python3
"""Inspect M98 row groups and decide the next external-route step."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M99_row_group_heavier_route_decision_v0"
VERSION = "e005_m99_row_group_heavier_route_decision_v0"

M98_DIR = EXP_ROOT / "artifacts" / "E005-M98_conceptgraphs_reliability_boundary_v0"


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


def safe_mean(values: list[float | int | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return round(mean(valid), 6) if valid else None


def success_count(rows: list[dict[str, Any]], key: str) -> int:
    return sum(bool(row.get(key)) for row in rows)


def any_success(rows: list[dict[str, Any]], key: str) -> bool:
    return any(bool(row.get(key)) for row in rows)


def route_for_target(rows: list[dict[str, Any]]) -> str:
    h001_fail = not all(bool(row["h001_success"]) for row in rows)
    if not h001_fail:
        if any((not row["conceptgraphs_success"]) and (not row["real_detector_top5_success"]) for row in rows):
            return "memory_retains_target_when_external_routes_fail"
        return "all_or_many_routes_succeed"
    if any_success(rows, "conceptgraphs_success"):
        return "conceptgraphs_map_assisted_repair_candidate"
    if any_success(rows, "real_detector_top5_success"):
        return "real_detector_top5_repair_candidate"
    if any_success(rows, "unbounded_real_detector_success"):
        return "real_detector_unbounded_repair_candidate_not_budget_safe"
    if any(row.get("conceptgraphs_target_rank") is not None for row in rows):
        return "conceptgraphs_rank_relaxation_candidate"
    return "shared_uncovered_h001_failure"


def build_target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_target[row["base_row_uid"]].append(row)

    output: list[dict[str, Any]] = []
    for base_uid, target_rows in sorted(by_target.items()):
        groups = Counter(row["map_real_top5_h001_group"] for row in target_rows)
        h001_successes = [bool(row["h001_success"]) for row in target_rows]
        cg_ranks = [row.get("conceptgraphs_target_rank") for row in target_rows if row.get("conceptgraphs_target_rank") is not None]
        real_ranks = [row.get("real_detector_target_rank") for row in target_rows if row.get("real_detector_target_rank") is not None]
        output.append(
            {
                "base_row_uid": base_uid,
                "target_uid": target_rows[0].get("target_uid"),
                "scan_id": target_rows[0].get("scan_id"),
                "batch_id": target_rows[0].get("batch_id"),
                "label_canonical": target_rows[0].get("label_canonical"),
                "row_band_values": sorted({row.get("row_band") for row in target_rows}),
                "task_context_ids": sorted({row.get("task_context_id") for row in target_rows}),
                "row_count": len(target_rows),
                "dominant_m98_group": groups.most_common(1)[0][0],
                "m98_groups": dict(sorted(groups.items())),
                "target_repair_route": route_for_target(target_rows),
                "h001_success_rows": success_count(target_rows, "h001_success"),
                "static_success_rows": success_count(target_rows, "static_memory_success"),
                "context_agnostic_success_rows": success_count(target_rows, "context_agnostic_success"),
                "conceptgraphs_success_rows": success_count(target_rows, "conceptgraphs_success"),
                "real_top5_success_rows": success_count(target_rows, "real_detector_top5_success"),
                "real_task_budget_success_rows": success_count(target_rows, "real_detector_task_budget_success"),
                "unbounded_real_success_rows": success_count(target_rows, "unbounded_real_detector_success"),
                "h001_context_sensitive": len(set(h001_successes)) > 1,
                "old_dead_end_rows": success_count(target_rows, "old_location_dead_end_expected"),
                "min_conceptgraphs_rank": min(cg_ranks) if cg_ranks else None,
                "min_real_detector_rank": min(real_ranks) if real_ranks else None,
                "mean_h001_expected_search_cost": safe_mean([row.get("h001_expected_search_cost") for row in target_rows]),
                "mean_conceptgraphs_expected_search_cost": safe_mean([row.get("conceptgraphs_expected_search_cost") for row in target_rows]),
                "mean_real_detector_task_expected_search_cost": safe_mean(
                    [row.get("real_detector_task_expected_search_cost") for row in target_rows]
                ),
            }
        )
    return output


def summarize_field(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts = Counter(row.get(field) for row in rows)
    total = len(rows)
    return [
        {
            "field": field,
            "value": value,
            "count": count,
            "rate": round(count / total, 6) if total else 0.0,
        }
        for value, count in counts.most_common()
    ]


def build_inspection_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_routes = [
        "conceptgraphs_map_assisted_repair_candidate",
        "real_detector_top5_repair_candidate",
        "real_detector_unbounded_repair_candidate_not_budget_safe",
        "conceptgraphs_rank_relaxation_candidate",
        "shared_uncovered_h001_failure",
        "memory_retains_target_when_external_routes_fail",
    ]
    output: list[dict[str, Any]] = []
    for route in priority_routes:
        selected = [row for row in target_rows if row["target_repair_route"] == route]
        selected.sort(
            key=lambda row: (
                row["batch_id"] or "",
                row["scan_id"] or "",
                row["label_canonical"] or "",
                row["target_uid"] or "",
            )
        )
        for row in selected[:8]:
            out = dict(row)
            out["inspection_priority"] = priority_routes.index(route) + 1
            output.append(out)
    return output


def build_union_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "h001_success_rows": success_count(rows, "h001_success"),
        "static_memory_success_rows": success_count(rows, "static_memory_success"),
        "context_agnostic_success_rows": success_count(rows, "context_agnostic_success"),
        "conceptgraphs_success_rows": success_count(rows, "conceptgraphs_success"),
        "real_detector_top5_success_rows": success_count(rows, "real_detector_top5_success"),
        "real_detector_task_budget_success_rows": success_count(rows, "real_detector_task_budget_success"),
        "unbounded_real_detector_success_rows": success_count(rows, "unbounded_real_detector_success"),
        "h001_or_conceptgraphs_success_rows": sum(
            row["h001_success"] or row["conceptgraphs_success"] for row in rows
        ),
        "h001_or_real_detector_top5_success_rows": sum(
            row["h001_success"] or row["real_detector_top5_success"] for row in rows
        ),
        "h001_or_conceptgraphs_or_real_top5_success_rows": sum(
            row["h001_success"] or row["conceptgraphs_success"] or row["real_detector_top5_success"] for row in rows
        ),
        "h001_or_conceptgraphs_or_unbounded_real_success_rows": sum(
            row["h001_success"] or row["conceptgraphs_success"] or row["unbounded_real_detector_success"]
            for row in rows
        ),
    }


def build_route_decisions(
    rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    union_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    route_counts = Counter(row["target_repair_route"] for row in target_rows)
    h001_fail_rows = [row for row in rows if not row["h001_success"]]
    cg_repair_rows = [row for row in h001_fail_rows if row["conceptgraphs_success"]]
    shared_uncovered_targets = route_counts["shared_uncovered_h001_failure"]
    return [
        {
            "route_id": "map_assisted_h001_repair_first",
            "rank": 1,
            "selected": True,
            "decision": "selected_next",
            "next_unit": "E005-M100 ConceptGraphs-assisted H001 fallback policy smoke",
            "reason": [
                f"`ConceptGraphs` succeeds on {len(cg_repair_rows)} H001-failure rows.",
                f"A simple H001-or-ConceptGraphs union upper bound is {union_summary['h001_or_conceptgraphs_success_rows']} / {len(rows)} rows.",
                "This directly targets H001 failure rows without launching a new heavy external stack.",
                "It also forces a policy/cost ablation before any navigation bridge claim.",
            ],
            "claim_boundary": "This is an upper-bound/contract decision until M100 defines allowed inputs, visit order, and cost accounting.",
        },
        {
            "route_id": "heavier_external_route_now",
            "rank": 2,
            "selected": False,
            "decision": "defer",
            "next_unit": "`OpenMask3D` / `HOV-SG` feasibility only if M100 leaves critical shared gaps",
            "reason": [
                f"Shared uncovered H001-failure targets are {shared_uncovered_targets} / {len(target_rows)}.",
                "The current bottleneck is not only external proposal coverage; it is how H001 should use existing map candidates.",
                "Launching a heavy route now risks turning the work into baseline engineering before the method principle is fixed.",
            ],
            "claim_boundary": "Keep as reviewer-facing expansion route, not the immediate next step.",
        },
        {
            "route_id": "navigation_bridge_now",
            "rank": 3,
            "selected": False,
            "decision": "defer",
            "next_unit": "Navigation bridge after M100/M101 policy contract and cost accounting",
            "reason": [
                "Navigation before map-assisted fallback would confound memory policy failures with route execution.",
                "Real navigation `SR` / `SPL` are still not ready.",
                "M100 should decide candidate visit order and old-location dead-end handling first.",
            ],
            "claim_boundary": "Do not claim deployable search or navigation from M99.",
        },
        {
            "route_id": "human_context_upgrade_now",
            "rank": 4,
            "selected": False,
            "decision": "defer",
            "next_unit": "Optional E006 only if human intent becomes a main claim",
            "reason": [
                f"H001 context-sensitive target count is {sum(row['h001_context_sensitive'] for row in target_rows)} / {len(target_rows)}.",
                "The current evidence supports task context as a condition on memory trust, not as the main contribution.",
            ],
            "claim_boundary": "Human intent remains secondary unless a dedicated context-sensitive utility benchmark is added.",
        },
    ]


def build_claim_rows(
    rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    union_summary: dict[str, Any],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = next(row for row in route_rows if row["selected"])
    route_counts = Counter(row["target_repair_route"] for row in target_rows)
    return [
        {
            "claim_id": "C-M99-001",
            "claim": "The next method-facing step should be map-assisted H001 fallback, not a heavier external route or navigation bridge.",
            "claim_type": "route_decision",
            "status": "selected",
            "evidence": f"Selected `{selected['route_id']}`; H001-or-ConceptGraphs upper bound is {union_summary['h001_or_conceptgraphs_success_rows']} / {len(rows)} rows.",
            "boundary": "M99 is a decision/inspection artifact; it does not implement the fallback policy.",
            "next_validation_requirement": selected["next_unit"],
        },
        {
            "claim_id": "C-M99-002",
            "claim": "H001's external-route recovery rows support semantic memory value, but not task-context novelty by themselves.",
            "claim_type": "novelty_boundary",
            "status": "must_report",
            "evidence": f"Targets with H001 context-sensitive outcomes: {sum(row['h001_context_sensitive'] for row in target_rows)} / {len(target_rows)}.",
            "boundary": "Do not present old-memory recovery over `ConceptGraphs`/detector failure as a human-intent main contribution.",
            "next_validation_requirement": "Keep task context as a memory-trust condition unless E006 adds a dedicated utility benchmark.",
        },
        {
            "claim_id": "C-M99-003",
            "claim": "`ConceptGraphs` exposes a concrete H001 repair opportunity.",
            "claim_type": "method_gap",
            "status": "supported_diagnostic",
            "evidence": f"`conceptgraphs_map_assisted_repair_candidate` targets: {route_counts['conceptgraphs_map_assisted_repair_candidate']} / {len(target_rows)}.",
            "boundary": "A union upper bound is not a deployable policy because it has not paid old-location dead-end or candidate-visit costs.",
            "next_validation_requirement": "M100 must define allowed inputs, visit order, fallback trigger, and `ExpectedSearchCost` accounting.",
        },
        {
            "claim_id": "C-M99-004",
            "claim": "Heavier external proposal routes remain useful but are not the immediate blocker.",
            "claim_type": "reviewer_defense_boundary",
            "status": "deferred_with_reason",
            "evidence": f"`shared_uncovered_h001_failure` targets: {route_counts['shared_uncovered_h001_failure']} / {len(target_rows)}.",
            "boundary": "`OpenMask3D` / `HOV-SG` should be revisited if M100 leaves unresolved shared gaps or if reviewer baseline pressure remains high.",
            "next_validation_requirement": "After M100, decide M101: cost-aware map-assisted policy evaluation or heavier external route feasibility.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    group_summary_rows: list[dict[str, Any]],
    target_summary_rows: list[dict[str, Any]],
    union_summary: dict[str, Any],
    route_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    def table(rows: list[dict[str, Any]], field: str) -> str:
        selected = [row for row in rows if row["field"] == field]
        lines = ["| Value | Count | Rate |", "| --- | ---: | ---: |"]
        for row in selected:
            lines.append(f"| `{row['value']}` | {row['count']} | {row['rate']:.6f} |")
        return "\n".join(lines)

    union_lines = ["| Policy / Upper Bound | Rows |", "| --- | ---: |"]
    for key, value in union_summary.items():
        union_lines.append(f"| `{key}` | {value} |")

    route_lines = ["| Rank | Route | Decision | Next Unit |", "| ---: | --- | --- | --- |"]
    for row in route_rows:
        route_lines.append(f"| {row['rank']} | `{row['route_id']}` | `{row['decision']}` | {row['next_unit']} |")

    claim_lines = ["| Claim | Status | Evidence | Boundary |", "| --- | --- | --- | --- |"]
    for row in claim_rows:
        claim_lines.append(f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['boundary']} |")

    return f"""# E005-M99 Row-Group / External Route Decision

## Facts

- Status: `{coverage["status"]}`.
- Query rows: {coverage["query_rows"]}.
- Unique target rows: {coverage["unique_target_rows"]}.
- H001 failure rows: {coverage["h001_failure_rows"]}.
- H001 failure targets: {coverage["h001_failure_targets"]}.
- `ConceptGraphs` map-assisted repair candidate rows: {coverage["conceptgraphs_repair_candidate_rows"]}.
- `ConceptGraphs` map-assisted repair candidate targets: {coverage["conceptgraphs_repair_candidate_targets"]}.
- Selected next unit: {coverage["selected_next_unit"]}.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Real navigation `SR` / `SPL` ready: false.

## Row-Level Groups

{table(group_summary_rows, "map_real_top5_h001_group")}

## Target-Level Repair Routes

{table(target_summary_rows, "target_repair_route")}

## Upper-Bound Success Rows

{chr(10).join(union_lines)}

## Route Decision

{chr(10).join(route_lines)}

## Claim Boundary

{chr(10).join(claim_lines)}

## Agent Inference

- `ConceptGraphs` is not only a baseline row; it exposes a concrete fallback opportunity for H001 failure rows.
- The immediate method risk is policy form and cost accounting, not lack of another heavy external baseline.
- Navigation bridge should wait until map-assisted fallback has an allowed-input contract and an `ExpectedSearchCost` policy.
- Human task context remains a condition on memory trust. M99 does not support human intent as the main contribution.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m98_coverage = read_json(M98_DIR / "coverage.json")
    rows = read_jsonl(M98_DIR / "row_group_rows.jsonl")
    if not rows:
        raise RuntimeError(f"Missing M98 row groups: {M98_DIR / 'row_group_rows.jsonl'}")

    target_rows = build_target_rows(rows)
    inspection_rows = build_inspection_rows(target_rows)
    group_summary_rows = summarize_field(rows, "map_real_top5_h001_group")
    target_summary_rows = summarize_field(target_rows, "target_repair_route")
    label_summary_rows = summarize_field(target_rows, "label_canonical")
    batch_summary_rows = summarize_field(target_rows, "batch_id")
    union_summary = build_union_summary(rows)
    route_rows = build_route_decisions(rows, target_rows, union_summary)
    claim_rows = build_claim_rows(rows, target_rows, union_summary, route_rows)
    selected_route = next(row for row in route_rows if row["selected"])

    h001_failure_rows = [row for row in rows if not row["h001_success"]]
    h001_failure_targets = {row["base_row_uid"] for row in h001_failure_rows}
    cg_repair_rows = [row for row in h001_failure_rows if row["conceptgraphs_success"]]
    cg_repair_targets = {row["base_row_uid"] for row in cg_repair_rows}

    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_failure_rows": len(h001_failure_rows),
        "h001_failure_targets": len(h001_failure_targets),
        "m98_status": m98_coverage.get("status"),
        "query_rows": len(rows),
        "unique_target_rows": len(target_rows),
        "conceptgraphs_repair_candidate_rows": len(cg_repair_rows),
        "conceptgraphs_repair_candidate_targets": len(cg_repair_targets),
        "h001_or_conceptgraphs_upper_bound_rows": union_summary["h001_or_conceptgraphs_success_rows"],
        "h001_or_conceptgraphs_or_real_top5_upper_bound_rows": union_summary[
            "h001_or_conceptgraphs_or_real_top5_success_rows"
        ],
        "h001_context_sensitive_targets": sum(row["h001_context_sensitive"] for row in target_rows),
        "selected_route": selected_route["route_id"],
        "selected_next_unit": selected_route["next_unit"],
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "status": "e005_m99_row_group_heavier_route_decision_ready",
        "version": VERSION,
    }

    summary = {
        "coverage": coverage,
        "union_summary": union_summary,
        "group_summary_rows": group_summary_rows,
        "target_summary_rows": target_summary_rows,
        "label_summary_rows": label_summary_rows,
        "batch_summary_rows": batch_summary_rows,
        "route_decisions": route_rows,
        "claim_boundary_rows": claim_rows,
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", summary)
    write_jsonl(OUT_DIR / "target_group_rows.jsonl", target_rows)
    write_jsonl(OUT_DIR / "inspection_rows.jsonl", inspection_rows)
    write_jsonl(OUT_DIR / "group_summary_rows.jsonl", group_summary_rows)
    write_jsonl(OUT_DIR / "target_summary_rows.jsonl", target_summary_rows)
    write_jsonl(OUT_DIR / "label_summary_rows.jsonl", label_summary_rows)
    write_jsonl(OUT_DIR / "batch_summary_rows.jsonl", batch_summary_rows)
    write_jsonl(OUT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(
        OUT_DIR / "report.md",
        build_report(coverage, group_summary_rows, target_summary_rows, union_summary, route_rows, claim_rows),
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
