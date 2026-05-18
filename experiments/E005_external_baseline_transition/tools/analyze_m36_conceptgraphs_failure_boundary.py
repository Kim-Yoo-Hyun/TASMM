#!/usr/bin/env python3
"""Analyze E005-M35 ConceptGraphs query failures and claim boundary."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M35_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M35_conceptgraphs_4scan_query_metric_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M36_conceptgraphs_failure_boundary_v0"
VERSION = "e005_m36_conceptgraphs_failure_boundary_v0"


STRICT_BBOX_TOP5 = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
RELAXED_BBOX_TOP3 = "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"
STRICT_CENTER_TOP5 = "conceptgraphs_clip_rank_centroid_strict_top5_v0"


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
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def first_rank(rows: list[dict[str, Any]], distance_field: str, threshold: float) -> tuple[int | None, str | None, float | None]:
    for row in sorted(rows, key=lambda item: int(item["rank"])):
        distance_value = float(row[distance_field])
        if distance_value <= threshold:
            return int(row["rank"]), str(row["candidate_uid"]), round(distance_value, 6)
    return None, None, None


def min_distance(rows: list[dict[str, Any]], distance_field: str) -> float | None:
    if not rows:
        return None
    return round(min(float(row[distance_field]) for row in rows), 6)


def top_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = sorted(rows, key=lambda item: int(item["rank"]))[0]
    return {
        "candidate_uid": first["candidate_uid"],
        "rank": int(first["rank"]),
        "semantic_score": first.get("semantic_score"),
        "center_distance_m": first.get("eval_center_distance_m"),
        "bbox_distance_m": first.get("eval_bbox_distance_m"),
    }


def classify_query(strict_rank: int | None, relaxed_rank: int | None, center_rank: int | None) -> str:
    if strict_rank is not None and strict_rank <= 5:
        if center_rank is None or center_rank > 5:
            return "strict_bbox_top5_success_centroid_miss"
        return "strict_bbox_top5_success"
    if strict_rank is not None and strict_rank > 5:
        return "strict_candidate_rank_gt5"
    if relaxed_rank is not None and relaxed_rank <= 3:
        return "relaxed_top3_only_no_strict"
    if relaxed_rank is not None:
        return "relaxed_candidate_rank_gt3_no_strict"
    return "no_relaxed_candidate"


def build_query_rows(eval_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_query: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    policy_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in eval_rows:
        rows_by_query[(str(row["query_suite"]), str(row["query_uid"]))].append(row)
    for row in policy_rows:
        policy_by_key[(str(row["query_suite"]), str(row["query_uid"]), str(row["policy"]))] = row

    query_rows: list[dict[str, Any]] = []
    for (suite, query_uid), candidates in sorted(rows_by_query.items()):
        ordered = sorted(candidates, key=lambda item: int(item["rank"]))
        first = ordered[0]
        strict_rank, strict_uid, strict_dist = first_rank(ordered, "eval_bbox_distance_m", 0.5)
        relaxed_rank, relaxed_uid, relaxed_dist = first_rank(ordered, "eval_bbox_distance_m", 1.0)
        center_rank, center_uid, center_dist = first_rank(ordered, "eval_center_distance_m", 0.5)
        strict_policy = policy_by_key.get((suite, query_uid, STRICT_BBOX_TOP5), {})
        relaxed_policy = policy_by_key.get((suite, query_uid, RELAXED_BBOX_TOP3), {})
        center_policy = policy_by_key.get((suite, query_uid, STRICT_CENTER_TOP5), {})
        failure_class = classify_query(strict_rank, relaxed_rank, center_rank)
        query_rows.append(
            {
                "m36_version": VERSION,
                "query_suite": suite,
                "query_uid": query_uid,
                "scan_id": first["scan_id"],
                "label_canonical": first["query_label"],
                "target_uid": first["target_uid"],
                "task_context_id": first.get("task_context_id"),
                "row_band": first.get("row_band"),
                "old_memory_is_stale": first.get("old_memory_is_stale"),
                "old_location_dead_end_expected": first.get("old_location_dead_end_expected"),
                "candidate_count": len(ordered),
                "strict_bbox_rank": strict_rank,
                "strict_bbox_candidate_uid": strict_uid,
                "strict_bbox_distance_m": strict_dist,
                "relaxed_bbox_1m_rank": relaxed_rank,
                "relaxed_bbox_1m_candidate_uid": relaxed_uid,
                "relaxed_bbox_1m_distance_m": relaxed_dist,
                "strict_center_rank": center_rank,
                "strict_center_candidate_uid": center_uid,
                "strict_center_distance_m": center_dist,
                "min_bbox_distance_m": min_distance(ordered, "eval_bbox_distance_m"),
                "min_center_distance_m": min_distance(ordered, "eval_center_distance_m"),
                "top_candidate": top_candidate(ordered),
                "strict_bbox_top5_success": bool(strict_policy.get("query_bridge_success", False)),
                "relaxed_bbox_1m_top3_success": bool(relaxed_policy.get("query_bridge_success", False)),
                "strict_center_top5_success": bool(center_policy.get("query_bridge_success", False)),
                "failure_class": failure_class,
            }
        )
    return query_rows


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    strict_success = sum(1 for row in rows if row["strict_bbox_top5_success"])
    relaxed_success = sum(1 for row in rows if row["relaxed_bbox_1m_top3_success"])
    center_success = sum(1 for row in rows if row["strict_center_top5_success"])
    return {
        "rows": len(rows),
        "strict_bbox_top5_success_rows": strict_success,
        "strict_bbox_top5_success_rate": safe_rate(strict_success, len(rows)),
        "relaxed_bbox_1m_top3_success_rows": relaxed_success,
        "relaxed_bbox_1m_top3_success_rate": safe_rate(relaxed_success, len(rows)),
        "strict_center_top5_success_rows": center_success,
        "strict_center_top5_success_rate": safe_rate(center_success, len(rows)),
        "mean_candidate_count": safe_mean([float(row["candidate_count"]) for row in rows]),
        "mean_min_bbox_distance_m": safe_mean([float(row["min_bbox_distance_m"]) for row in rows if row["min_bbox_distance_m"] is not None]),
        "failure_class_counts": dict(sorted(Counter(row["failure_class"] for row in rows).items())),
    }


def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[str(row.get(key))].append(row)
    return {name: summarize_group(items) for name, items in sorted(by_key.items())}


def build_aggregate(query_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_suite: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        by_suite[str(row["query_suite"])].append(row)
    suites = {}
    for suite, rows in sorted(by_suite.items()):
        suites[suite] = {
            "overall": summarize_group(rows),
            "by_scan": grouped(rows, "scan_id"),
            "by_label": grouped(rows, "label_canonical"),
            "by_task_context": grouped(rows, "task_context_id"),
            "by_row_band": grouped(rows, "row_band"),
            "by_failure_class": grouped(rows, "failure_class"),
        }
    return {
        "suites": suites,
        "primary_claim_boundary": {
            "supported": [
                "4 staged scans can be converted from ConceptGraphs map outputs into query-level candidate metrics.",
                "Primary M60 strict bbox top5 succeeds on a subset of queries.",
                "Relaxed bbox 1m top3 suggests map-object coverage is broader than strict localization success.",
            ],
            "not_supported": [
                "Final ConceptGraphs baseline performance on full dataset.",
                "Final real RGB-D/open-vocabulary robustness.",
                "Real navigation SR/SPL.",
                "Generality across unseen scenes or labels.",
                "Centroid-localization success equivalent to bbox-overlap success.",
            ],
            "next_validation_requirements": [
                "Scale beyond 4 staged scans.",
                "Hold out scan/label groups and report transfer.",
                "Compare against at least one additional external mapping/proposal route.",
                "Keep strict 0.5m and relaxed 1.0m metrics separate.",
                "Inspect label/scan-specific failure classes before method claims.",
            ],
        },
    }


def top_failure_rows(query_rows: list[dict[str, Any]], suite: str, limit: int = 12) -> list[dict[str, Any]]:
    rows = [row for row in query_rows if row["query_suite"] == suite and not row["strict_bbox_top5_success"]]
    rows.sort(key=lambda row: (row["relaxed_bbox_1m_top3_success"], row["min_bbox_distance_m"] if row["min_bbox_distance_m"] is not None else 999))
    return rows[:limit]


def build_report(coverage: dict[str, Any], aggregate: dict[str, Any], query_rows: list[dict[str, Any]]) -> str:
    primary = aggregate["suites"]["primary_m60"]["overall"]
    expanded = aggregate["suites"]["expanded_m73"]["overall"]
    primary_by_label = aggregate["suites"]["primary_m60"]["by_label"]
    expanded_by_label = aggregate["suites"]["expanded_m73"]["by_label"]
    primary_failures = top_failure_rows(query_rows, "primary_m60", 6)
    lines = [
        "# E005-M36 ConceptGraphs Failure Boundary",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Primary `M60` rows: {primary['rows']}.",
        f"- Primary strict bbox top5: {primary['strict_bbox_top5_success_rows']} / {primary['rows']} = {primary['strict_bbox_top5_success_rate']}.",
        f"- Primary relaxed bbox 1m top3: {primary['relaxed_bbox_1m_top3_success_rows']} / {primary['rows']} = {primary['relaxed_bbox_1m_top3_success_rate']}.",
        f"- Primary strict center top5: {primary['strict_center_top5_success_rows']} / {primary['rows']} = {primary['strict_center_top5_success_rate']}.",
        f"- Expanded `M73` rows: {expanded['rows']}.",
        f"- Expanded strict bbox top5: {expanded['strict_bbox_top5_success_rows']} / {expanded['rows']} = {expanded['strict_bbox_top5_success_rate']}.",
        f"- Expanded relaxed bbox 1m top3: {expanded['relaxed_bbox_1m_top3_success_rows']} / {expanded['rows']} = {expanded['relaxed_bbox_1m_top3_success_rate']}.",
        f"- Primary failure classes: `{primary['failure_class_counts']}`.",
        f"- Expanded failure classes: `{expanded['failure_class_counts']}`.",
        "",
        "## Label Boundary",
        "",
    ]
    for label, row in primary_by_label.items():
        lines.append(
            f"- Primary `{label}`: strict bbox top5 {row['strict_bbox_top5_success_rows']} / {row['rows']}, "
            f"relaxed top3 {row['relaxed_bbox_1m_top3_success_rows']} / {row['rows']}, failures `{row['failure_class_counts']}`."
        )
    lines.append("")
    for label, row in expanded_by_label.items():
        lines.append(
            f"- Expanded `{label}`: strict bbox top5 {row['strict_bbox_top5_success_rows']} / {row['rows']}, "
            f"relaxed top3 {row['relaxed_bbox_1m_top3_success_rows']} / {row['rows']}."
        )
    lines.extend(
        [
            "",
            "## Primary Failure Examples",
            "",
        ]
    )
    for row in primary_failures:
        lines.append(
            "- `{query}` `{label}` scan `{scan}`: failure `{failure}`, strict rank `{strict}`, relaxed rank `{relaxed}`, min bbox {dist}.".format(
                query=row["query_uid"],
                label=row["label_canonical"],
                scan=row["scan_id"],
                failure=row["failure_class"],
                strict=row["strict_bbox_rank"],
                relaxed=row["relaxed_bbox_1m_rank"],
                dist=row["min_bbox_distance_m"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: 4 staged scans can be converted from `ConceptGraphs` map outputs into query-level candidate metrics.",
            "- Supported: `ConceptGraphs` has strict bbox hits on this small staged subset.",
            "- Not supported: final external baseline claim, full real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.",
            "- Required next: scale, heldout split, additional external route, and strict/relaxed metric separation.",
            "",
            "## Agent Inference",
            "",
            "- Bbox success is materially stronger than centroid success, so object extent alignment is carrying part of the result.",
            "- Relaxed success is much higher than strict success on primary `M60`, which means map coverage exists but strict localization/ranking remains a key boundary.",
            "- Expanded `M73` has stronger strict bbox rate than primary `M60`, so the primary benchmark is harder or narrower; do not overstate generality from the expanded diagnostic.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m35 = read_json(M35_DIR / "coverage.json")
    eval_rows = read_jsonl(M35_DIR / "candidate_eval_rows.jsonl")
    policy_rows = read_jsonl(M35_DIR / "policy_rows.jsonl")
    errors: list[str] = []
    if m35.get("status") != "e005_m35_conceptgraphs_4scan_query_metric_ready_with_strict_hits":
        errors.append("m35_not_ready_with_strict_hits")
    if not eval_rows:
        errors.append("missing_candidate_eval_rows")
    if not policy_rows:
        errors.append("missing_policy_rows")
    if errors:
        coverage = {
            "status": "e005_m36_conceptgraphs_failure_boundary_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "errors": errors,
            "next_recommended_unit": "Repair M35 inputs",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", "# E005-M36 ConceptGraphs Failure Boundary\n\nBlocked.\n")
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    query_rows = build_query_rows(eval_rows, policy_rows)
    aggregate = build_aggregate(query_rows)
    primary = aggregate["suites"]["primary_m60"]["overall"]
    expanded = aggregate["suites"]["expanded_m73"]["overall"]
    coverage = {
        "status": "e005_m36_conceptgraphs_failure_boundary_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m35_status": m35.get("status"),
        "primary_rows": primary["rows"],
        "primary_strict_bbox_top5_success_rows": primary["strict_bbox_top5_success_rows"],
        "primary_strict_bbox_top5_success_rate": primary["strict_bbox_top5_success_rate"],
        "primary_relaxed_bbox_1m_top3_success_rows": primary["relaxed_bbox_1m_top3_success_rows"],
        "primary_relaxed_bbox_1m_top3_success_rate": primary["relaxed_bbox_1m_top3_success_rate"],
        "primary_strict_center_top5_success_rows": primary["strict_center_top5_success_rows"],
        "primary_strict_center_top5_success_rate": primary["strict_center_top5_success_rate"],
        "expanded_rows": expanded["rows"],
        "expanded_strict_bbox_top5_success_rows": expanded["strict_bbox_top5_success_rows"],
        "expanded_strict_bbox_top5_success_rate": expanded["strict_bbox_top5_success_rate"],
        "expanded_relaxed_bbox_1m_top3_success_rows": expanded["relaxed_bbox_1m_top3_success_rows"],
        "expanded_relaxed_bbox_1m_top3_success_rate": expanded["relaxed_bbox_1m_top3_success_rate"],
        "final_baseline_claim_ready": False,
        "small_subset_claim_boundary_ready": True,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M37 external baseline comparison table / next-route decision",
    }
    write_jsonl(OUT_DIR / "query_failure_rows.jsonl", query_rows)
    write_jsonl(OUT_DIR / "primary_failure_examples.jsonl", top_failure_rows(query_rows, "primary_m60", 12))
    write_json(OUT_DIR / "aggregate.json", aggregate)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, aggregate, query_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
