#!/usr/bin/env python3
"""Convert one-scan ConceptGraphs candidates into query-level diagnostics."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M30_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M30_conceptgraphs_candidate_export_v0"
M60_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
M73_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M31_conceptgraphs_query_metric_v0"
VERSION = "e005_m31_conceptgraphs_query_metric_v0"

POLICIES = [
    {
        "policy": "conceptgraphs_clip_rank_centroid_strict_top5_v0",
        "distance_field": "eval_center_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 3,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_unbounded_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": "all",
    },
]


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


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(a, b)))


def bbox_distance(point: list[float], bbox_min: list[float], bbox_max: list[float]) -> float:
    sq = 0.0
    for value, low, high in zip(point, bbox_min, bbox_max):
        if value < low:
            sq += (low - value) ** 2
        elif value > high:
            sq += (value - high) ** 2
    return math.sqrt(sq)


def safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def load_query_rows() -> dict[str, dict[str, Any]]:
    return {str(row["bridge_query_uid"]): row for row in read_jsonl(M60_DIR / "query_bridge_rows.jsonl")}


def load_target_rows() -> dict[str, dict[str, Any]]:
    rows = read_jsonl(M73_DIR / "real_proposal_object_targets.jsonl")
    return {str(row["target_uid"]): row for row in rows}


def build_candidate_eval_rows(
    candidate_rows: list[dict[str, Any]],
    query_by_uid: dict[str, dict[str, Any]],
    target_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        query_uid = str(candidate["query_uid"])
        query = query_by_uid[query_uid]
        target_uid = str(query["target_uid"])
        target = target_by_uid[target_uid]
        target_centroid = [float(x) for x in target["centroid_world_m"]]
        center = [float(x) for x in candidate["candidate_center_xyz"]]
        bbox_min = [float(x) for x in candidate["candidate_bbox_min_xyz"]]
        bbox_max = [float(x) for x in candidate["candidate_bbox_max_xyz"]]
        center_distance = distance(center, target_centroid)
        box_distance = bbox_distance(target_centroid, bbox_min, bbox_max)
        success_threshold = float(query.get("success_threshold_m") or candidate.get("success_threshold_m") or 0.5)
        eval_rows.append(
            {
                **candidate,
                "m31_version": VERSION,
                "target_uid": target_uid,
                "target_centroid_world_m": [round(x, 6) for x in target_centroid],
                "target_label_canonical": target["label_canonical"],
                "target_object_instance_id": target["object_instance_id"],
                "eval_center_distance_m": round(center_distance, 6),
                "eval_bbox_distance_m": round(box_distance, 6),
                "eval_center_success_strict": center_distance <= success_threshold,
                "eval_bbox_success_strict": box_distance <= success_threshold,
                "eval_bbox_success_relaxed_1m": box_distance <= 1.0,
                "eval_success_threshold_m": success_threshold,
                "eval_relaxed_threshold_m": 1.0,
            }
        )
    return sorted(eval_rows, key=lambda row: (str(row["query_uid"]), int(row["rank"])))


def first_rank(rows: list[dict[str, Any]], distance_field: str, threshold_m: float) -> tuple[int | None, str | None, float | None]:
    for row in sorted(rows, key=lambda item: int(item["rank"])):
        distance_value = float(row[distance_field])
        if distance_value <= threshold_m:
            return int(row["rank"]), str(row["candidate_uid"]), round(distance_value, 6)
    return None, None, None


def build_policy_rows(eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        rows_by_query[str(row["query_uid"])].append(row)

    policy_rows: list[dict[str, Any]] = []
    for query_uid, query_candidates in sorted(rows_by_query.items()):
        ordered = sorted(query_candidates, key=lambda item: int(item["rank"]))
        for policy in POLICIES:
            target_rank, target_candidate_uid, match_distance = first_rank(
                ordered,
                str(policy["distance_field"]),
                float(policy["threshold_m"]),
            )
            candidate_count = len(ordered)
            if policy["budget"] == "all":
                returned = candidate_count
            else:
                returned = min(candidate_count, int(policy["budget"]))
            success = target_rank is not None and target_rank <= returned
            expected_cost = int(target_rank) if success and target_rank is not None else returned + 1
            first = ordered[0]
            policy_rows.append(
                {
                    "m31_version": VERSION,
                    "query_uid": query_uid,
                    "target_uid": first["target_uid"],
                    "scan_id": first["scan_id"],
                    "label_canonical": first["query_label"],
                    "task_context_id": first["task_context_id"],
                    "policy": policy["policy"],
                    "distance_field": policy["distance_field"],
                    "threshold_m": policy["threshold_m"],
                    "candidate_count": candidate_count,
                    "returned_location_count": returned,
                    "target_detected": target_rank is not None,
                    "target_rank": target_rank,
                    "target_candidate_uid": target_candidate_uid,
                    "target_match_distance_m": match_distance,
                    "false_positive_before_target_count": target_rank - 1 if target_rank is not None else None,
                    "query_bridge_success": success,
                    "expected_search_cost": expected_cost,
                    "attempt_spl_proxy": attempt_spl(success, expected_cost),
                    "old_memory_is_stale": first["old_memory_is_stale"],
                    "old_location_dead_end_expected": first["old_location_dead_end_expected"],
                    "query_level_baseline_result_ready": False,
                    "real_navigation_sr_spl_ready": False,
                }
            )
    return policy_rows


def summarize_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    detected = [row for row in rows if row["target_detected"]]
    return {
        "rows": len(rows),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "mean_target_rank_if_detected": safe_mean([float(row["target_rank"]) for row in detected]),
        "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
    }


def build_metrics(eval_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy = defaultdict(list)
    for row in policy_rows:
        by_policy[row["policy"]].append(row)
    return {
        "candidate_rows": len(eval_rows),
        "query_rows": len({row["query_uid"] for row in eval_rows}),
        "target_uid_count": len({row["target_uid"] for row in eval_rows}),
        "min_center_distance_m": min((float(row["eval_center_distance_m"]) for row in eval_rows), default=None),
        "min_bbox_distance_m": min((float(row["eval_bbox_distance_m"]) for row in eval_rows), default=None),
        "strict_center_hit_rows": sum(1 for row in eval_rows if row["eval_center_success_strict"]),
        "strict_bbox_hit_rows": sum(1 for row in eval_rows if row["eval_bbox_success_strict"]),
        "relaxed_bbox_1m_hit_rows": sum(1 for row in eval_rows if row["eval_bbox_success_relaxed_1m"]),
        "policy_metrics": {policy: summarize_policy(rows) for policy, rows in sorted(by_policy.items())},
    }


def failure_class(metrics: dict[str, Any]) -> str:
    if metrics["strict_bbox_hit_rows"] > 0:
        return "strict_bbox_hit_available"
    if metrics["relaxed_bbox_1m_hit_rows"] > 0:
        return "strict_threshold_miss_relaxed_bbox_hit"
    if metrics["candidate_rows"] > 0:
        return "map_candidate_target_miss"
    return "no_map_candidates"


def route_decision(metrics: dict[str, Any]) -> dict[str, Any]:
    failure = failure_class(metrics)
    if failure == "strict_bbox_hit_available":
        selected = "scale_conceptgraphs_to_4_staged_scans"
        rationale = "One-scan strict map-object match exists; the next question is scale and variance."
    elif failure == "strict_threshold_miss_relaxed_bbox_hit":
        selected = "scale_conceptgraphs_with_geometry_threshold_boundary"
        rationale = (
            "The top one-scan result misses the strict 0.5m gate but has a 1.0m bbox-near hit; "
            "scale is useful, but the claim must separate strict success from relaxed geometry near-miss."
        )
    else:
        selected = "inspect_geometry_alignment_before_scaling"
        rationale = "No target-near ConceptGraphs candidate was found; scaling without geometry diagnosis may waste runtime."
    return {
        "failure_class": failure,
        "rationale": rationale,
        "selected_next_route": selected,
    }


def build_report(coverage: dict[str, Any], metrics: dict[str, Any], route: dict[str, Any]) -> str:
    strict_bbox = metrics["policy_metrics"]["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    relaxed_bbox = metrics["policy_metrics"]["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]
    centroid = metrics["policy_metrics"]["conceptgraphs_clip_rank_centroid_strict_top5_v0"]
    return "\n".join(
        [
            "# E005-M31 ConceptGraphs Query Metric",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Query rows: {metrics['query_rows']}.",
            f"- Candidate rows: {metrics['candidate_rows']}.",
            f"- Min center distance m: {metrics['min_center_distance_m']}.",
            f"- Min bbox distance m: {metrics['min_bbox_distance_m']}.",
            f"- Strict center hit rows: {metrics['strict_center_hit_rows']}.",
            f"- Strict bbox hit rows: {metrics['strict_bbox_hit_rows']}.",
            f"- Relaxed bbox 1m hit rows: {metrics['relaxed_bbox_1m_hit_rows']}.",
            f"- Strict centroid top5 success rows/rate: {centroid['query_bridge_success_rows']} / {centroid['query_bridge_success_rate']}.",
            f"- Strict bbox top5 success rows/rate: {strict_bbox['query_bridge_success_rows']} / {strict_bbox['query_bridge_success_rate']}.",
            f"- Relaxed bbox 1m top3 success rows/rate: {relaxed_bbox['query_bridge_success_rows']} / {relaxed_bbox['query_bridge_success_rate']}.",
            f"- Failure class: `{route['failure_class']}`.",
            f"- Selected next route: `{route['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M31 is a one-scan diagnostic, not a `ConceptGraphs` baseline result claim.",
            "- Strict 0.5m success and relaxed 1.0m bbox-near success must be reported separately.",
            "- Real navigation `SR` / `SPL` remains unsupported.",
            "",
            "## Agent Inference",
            "",
            f"- {route['rationale']}",
            "- This result is useful because it turns the external map baseline route into a measurable query-level failure mode.",
            "",
        ]
    )


def main() -> int:
    m30_coverage = read_json(M30_DIR / "coverage.json")
    candidate_rows = read_jsonl(M30_DIR / "candidate_rows.jsonl")
    query_by_uid = load_query_rows()
    target_by_uid = load_target_rows()
    errors: list[str] = []
    if m30_coverage.get("status") != "e005_m30_conceptgraphs_candidate_export_ready":
        errors.append("m30_not_ready")
    missing_queries = sorted({row["query_uid"] for row in candidate_rows if row["query_uid"] not in query_by_uid})
    if missing_queries:
        errors.append(f"missing_query_rows:{missing_queries[:3]}")
    missing_targets = []
    for query_uid in {row["query_uid"] for row in candidate_rows if row["query_uid"] in query_by_uid}:
        target_uid = str(query_by_uid[query_uid]["target_uid"])
        if target_uid not in target_by_uid:
            missing_targets.append(target_uid)
    if missing_targets:
        errors.append(f"missing_target_rows:{missing_targets[:3]}")
    if errors:
        coverage = {
            "status": "e005_m31_conceptgraphs_query_metric_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "errors": errors,
            "next_recommended_unit": "Repair E005-M30/M60/M73 inputs",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", build_report(coverage, {"policy_metrics": defaultdict(dict)}, {"failure_class": "blocked", "selected_next_route": "repair_inputs", "rationale": "Inputs missing."}))
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    eval_rows = build_candidate_eval_rows(candidate_rows, query_by_uid, target_by_uid)
    policy_rows = build_policy_rows(eval_rows)
    metrics = build_metrics(eval_rows, policy_rows)
    route = route_decision(metrics)
    status = (
        "e005_m31_conceptgraphs_query_metric_strict_near_miss_ready"
        if route["failure_class"] == "strict_threshold_miss_relaxed_bbox_hit"
        else "e005_m31_conceptgraphs_query_metric_ready"
        if route["failure_class"] == "strict_bbox_hit_available"
        else "e005_m31_conceptgraphs_query_metric_target_miss_ready"
    )
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m30_status": m30_coverage.get("status"),
        "query_rows": metrics["query_rows"],
        "candidate_rows": metrics["candidate_rows"],
        "min_center_distance_m": metrics["min_center_distance_m"],
        "min_bbox_distance_m": metrics["min_bbox_distance_m"],
        "failure_class": route["failure_class"],
        "selected_next_route": route["selected_next_route"],
        "query_level_baseline_result_ready": False,
        "one_scan_diagnostic_ready": True,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M32 ConceptGraphs 4-scan scale decision",
    }
    write_jsonl(OUT_DIR / "candidate_eval_rows.jsonl", eval_rows)
    write_jsonl(OUT_DIR / "policy_rows.jsonl", policy_rows)
    write_json(OUT_DIR / "metrics.json", metrics)
    write_json(OUT_DIR / "route_decision.json", route)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, metrics, route))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
