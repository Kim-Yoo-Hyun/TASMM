#!/usr/bin/env python3
"""Decide whether to repair Open3DSG or move to another external route."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M63_open3dsg_route_decision_v0"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M49_METRICS = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0" / "metrics.json"
M52_METRICS = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0" / "metrics.json"
M60_METRICS = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "metrics.json"
M60_POLICY_ROWS = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "open3dsg_policy_rows.jsonl"
M61_OBJECT_ROWS = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M61_denominator_aligned_export_v0" / "open3dsg_object_candidates.jsonl"
VERSION = "e005_m63_open3dsg_route_decision_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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


def normalize_label(value: str) -> str:
    text = value.lower().strip().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def split_vocab_label(raw_label: str) -> list[str]:
    return str(raw_label).split("\t")


def primary_label(raw_label: str) -> str:
    parts = split_vocab_label(raw_label)
    if len(parts) >= 2 and parts[0].strip().isdigit():
        return normalize_label(parts[1])
    return normalize_label(raw_label)


def predicted_terms(raw_label: str) -> set[str]:
    parts = split_vocab_label(raw_label)
    terms: set[str] = set()
    for field in parts[1:]:
        for token in re.split(r"[/;,]", field):
            token = normalize_label(token)
            if token:
                terms.add(token)
    return terms


def vec3(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    try:
        return [float(value[0]), float(value[1]), float(value[2])]
    except (TypeError, ValueError):
        return None


def candidate_center_and_extent(row: dict[str, Any]) -> tuple[list[float] | None, list[float] | None]:
    geom = row.get("bbox_or_center", {})
    center = vec3(geom.get("center"))
    extent = None
    bbox = geom.get("bbox")
    if isinstance(bbox, list) and len(bbox) >= 6:
        extent = vec3(bbox[:3])
        if center is None:
            center = vec3(bbox[3:6])
    return center, extent


def target_center_and_extent(row: dict[str, Any] | None) -> tuple[list[float] | None, list[float] | None]:
    if not row:
        return None, None
    return vec3(row.get("centroid_world_m")), vec3(row.get("obb_axes_lengths_m"))


def aabb_distance(
    center_a: list[float] | None,
    extent_a: list[float] | None,
    center_b: list[float] | None,
    extent_b: list[float] | None,
) -> float | None:
    if center_a is None or extent_a is None or center_b is None or extent_b is None:
        return None
    sq = 0.0
    for i in range(3):
        min_a = center_a[i] - extent_a[i] / 2.0
        max_a = center_a[i] + extent_a[i] / 2.0
        min_b = center_b[i] - extent_b[i] / 2.0
        max_b = center_b[i] + extent_b[i] / 2.0
        gap = max(min_b - max_a, min_a - max_b, 0.0)
        sq += gap * gap
    return math.sqrt(sq)


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def load_query_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in ["heldout_b01", "heldout_b02", "heldout_b03"]:
        rows.extend(read_jsonl(M45_CONTRACT_DIR / f"{batch}_query_rows.jsonl"))
    return rows


def load_target_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(M45_METRIC_DIR.glob("target_rows*.jsonl")):
        for row in read_jsonl(path):
            rows[str(row["target_uid"])] = row
    return rows


def rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_object: dict[str, dict[str, Any]] = {}
    for row in candidates:
        object_id = str(row["object_id"])
        previous = best_by_object.get(object_id)
        if previous is None or (
            float(row["candidate_score"]),
            -int(row["candidate_rank"]),
        ) > (
            float(previous["candidate_score"]),
            -int(previous["candidate_rank"]),
        ):
            best_by_object[object_id] = row
    return sorted(
        best_by_object.values(),
        key=lambda row: (-float(row["candidate_score"]), int(row["candidate_rank"]), str(row["object_id"])),
    )


def evaluate_diagnostic_policy(
    query_rows: list[dict[str, Any]],
    target_by_uid: dict[str, dict[str, Any]],
    objects_by_scan: dict[str, list[dict[str, Any]]],
    *,
    policy: str,
    match_mode: str,
    threshold_m: float,
    budget: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_rows: list[dict[str, Any]] = []
    for query in query_rows:
        scan_id = str(query["current_rescan_id"])
        label = normalize_label(str(query["label_canonical"]))
        candidates: list[dict[str, Any]] = []
        for obj in objects_by_scan.get(scan_id, []):
            if match_mode == "primary" and primary_label(str(obj.get("candidate_label", ""))) == label:
                candidates.append(obj)
            elif match_mode == "predicted_terms" and label in predicted_terms(str(obj.get("candidate_label", ""))):
                candidates.append(obj)
        ranked = rank_candidates(candidates)
        target_center, target_extent = target_center_and_extent(target_by_uid.get(str(query["target_uid"])))
        target_rank: int | None = None
        for rank, obj in enumerate(ranked, start=1):
            distance = aabb_distance(*candidate_center_and_extent(obj), target_center, target_extent)
            if distance is not None and distance <= threshold_m:
                target_rank = rank
                break
        target_detected = target_rank is not None
        success = bool(target_rank is not None and target_rank <= budget)
        returned = min(len(ranked), budget)
        expected_cost = int(target_rank) if success and target_rank is not None else returned + 1
        if not ranked:
            failure_class = "no_candidates"
        elif target_rank is None:
            failure_class = "target_not_detected"
        elif target_rank > budget:
            failure_class = "target_present_but_rank_gt_budget"
        else:
            failure_class = "strict_hit"
        policy_rows.append(
            {
                "record_type": "open3dsg_diagnostic_policy_result",
                "version": VERSION,
                "policy": policy,
                "match_mode": match_mode,
                "query_uid": query["bridge_query_uid"],
                "row_uid": query["row_uid"],
                "target_uid": query["target_uid"],
                "scan_id": scan_id,
                "query_label": query["label_canonical"],
                "candidate_count": len(ranked),
                "target_detected": target_detected,
                "target_rank": target_rank,
                "query_bridge_success": success,
                "expected_search_cost": expected_cost,
                "attempt_spl_proxy": 0.0 if not success else round(1.0 / float(expected_cost), 6),
                "old_location_dead_end_expected": bool(query["old_location_dead_end_expected"]),
                "old_location_dead_end_avoided": bool(query["old_location_dead_end_expected"] and success),
                "failure_class": failure_class,
                "threshold_m": threshold_m,
                "budget": budget,
                "diagnostic_not_paper_claim": True,
            }
        )
    success_rows = [row for row in policy_rows if row["query_bridge_success"]]
    detected_rows = [row for row in policy_rows if row["target_detected"]]
    old_dead_end_rows = [row for row in policy_rows if row["old_location_dead_end_expected"]]
    old_dead_end_avoided = [row for row in old_dead_end_rows if row["old_location_dead_end_avoided"]]
    metrics = {
        "policy": policy,
        "match_mode": match_mode,
        "rows": len(policy_rows),
        "query_bridge_success_rows": len(success_rows),
        "query_bridge_success_rate": safe_rate(len(success_rows), len(policy_rows)),
        "target_detected_rows": len(detected_rows),
        "target_detected_rate": safe_rate(len(detected_rows), len(policy_rows)),
        "mean_target_rank_if_detected": safe_mean([int(row["target_rank"]) for row in detected_rows if row.get("target_rank") is not None]),
        "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in policy_rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in policy_rows]),
        "old_location_dead_end_avoided_rows": len(old_dead_end_avoided),
        "old_location_dead_end_avoided_rate": safe_rate(len(old_dead_end_avoided), len(old_dead_end_rows)),
        "failure_class_counts": dict(sorted(Counter(row["failure_class"] for row in policy_rows).items())),
    }
    return metrics, policy_rows


def build_failure_audit_rows(
    query_rows: list[dict[str, Any]],
    objects_by_scan: dict[str, list[dict[str, Any]]],
    current_policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    strict_by_query = {
        row["query_uid"]: row
        for row in current_policy_rows
        if row.get("policy") == "open3dsg_objects_probs_bbox_strict_top5_v0"
    }
    rows: list[dict[str, Any]] = []
    for query in query_rows:
        scan_id = str(query["current_rescan_id"])
        target_object_id = str(query["object_instance_id_rescan"])
        label = normalize_label(str(query["label_canonical"]))
        same_scan = objects_by_scan.get(scan_id, [])
        target_objects = [row for row in same_scan if str(row.get("object_id")) == target_object_id]
        primary_candidates = [row for row in same_scan if primary_label(str(row.get("candidate_label", ""))) == label]
        expanded_candidates = [row for row in same_scan if label in predicted_terms(str(row.get("candidate_label", "")))]
        target_primary = [row for row in target_objects if primary_label(str(row.get("candidate_label", ""))) == label]
        target_expanded = [row for row in target_objects if label in predicted_terms(str(row.get("candidate_label", "")))]
        rows.append(
            {
                "record_type": "open3dsg_route_failure_audit",
                "version": VERSION,
                "query_uid": query["bridge_query_uid"],
                "row_uid": query["row_uid"],
                "scan_id": scan_id,
                "target_uid": query["target_uid"],
                "target_object_id": target_object_id,
                "query_label": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "current_strict_success": bool(strict_by_query.get(query["bridge_query_uid"], {}).get("query_bridge_success")),
                "current_strict_failure_class": strict_by_query.get(query["bridge_query_uid"], {}).get("failure_class"),
                "same_scan_object_candidate_rows": len(same_scan),
                "primary_label_candidate_objects": len({str(row["object_id"]) for row in primary_candidates}),
                "expanded_term_candidate_objects": len({str(row["object_id"]) for row in expanded_candidates}),
                "target_object_candidate_rows": len(target_objects),
                "target_object_present_in_top20_candidates": bool(target_objects),
                "target_has_primary_label_candidate": bool(target_primary),
                "target_has_expanded_term_candidate": bool(target_expanded),
                "diagnostic_target_id_used": True,
            }
        )
    return rows


def metric_row(source: str, policy: str, metric: dict[str, Any], note: str) -> dict[str, Any]:
    return {
        "source": source,
        "policy": policy,
        "rows": metric.get("rows"),
        "success_rows": metric.get("query_bridge_success_rows"),
        "success_rate": metric.get("query_bridge_success_rate"),
        "target_detected_rows": metric.get("target_detected_rows"),
        "target_detected_rate": metric.get("target_detected_rate"),
        "mean_expected_search_cost": metric.get("mean_expected_search_cost"),
        "mean_attempt_spl_proxy": metric.get("mean_attempt_spl_proxy"),
        "note": note,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(decision: dict[str, Any], comparison_rows: list[dict[str, Any]], failure_summary: dict[str, Any]) -> str:
    lines = [
        "# E005-M63 Open3DSG Route Decision",
        "",
        "## Facts",
        "",
    ]
    for row in comparison_rows:
        lines.append(
            f"- `{row['source']}` / `{row['policy']}`: success {row['success_rows']} / {row['rows']} "
            f"= {row['success_rate']}, target detected {row['target_detected_rows']} / {row['rows']}, "
            f"mean `ExpectedSearchCost` {row['mean_expected_search_cost']}."
        )
    lines.extend(
        [
            f"- Open3DSG target object present in exported top20 rows: {failure_summary['target_object_present_rows']} / {failure_summary['rows']}.",
            f"- Open3DSG target has primary-label candidate: {failure_summary['target_primary_rows']} / {failure_summary['rows']}.",
            f"- Open3DSG target has predicted-term candidate: {failure_summary['target_expanded_rows']} / {failure_summary['rows']}.",
            f"- Queries with no primary-label candidates but at least one expanded-term candidate: {failure_summary['no_primary_but_expanded_rows']} / {failure_summary['rows']}.",
            "",
            "## Paper Claims",
            "",
            "- Current fixed M60 supports an `Open3DSG` denominator-aligned bridge result, but not a final strong baseline claim.",
            "- M63 supports a bounded repair direction: predicted vocabulary term expansion may recover a large part of the current `Open3DSG` gap.",
            "- The expanded-term metrics are diagnostic until implemented as a pre-registered M60/M64 policy and audited for leakage/generalization.",
            "",
            "## Agent Inference",
            "",
            f"- Selected route: `{decision['selected_route']}`.",
            f"- Reason: current strict success is {decision['current_open3dsg_strict_success_rows']} rows, while diagnostic expanded-term strict success is {decision['diagnostic_expanded_strict_success_rows']} rows.",
            f"- Diagnostic expanded-term strict success exceeds `ConceptGraphs` strict success by {decision['diagnostic_expanded_minus_conceptgraphs_strict_rows']} rows.",
            "- This suggests the immediate blocker is the Open3DSG vocabulary/query adapter, not only the scene graph model.",
            "- Moving directly to `HOV-SG` / `OpenMask3D` before this bounded repair would leave an avoidable reviewer question unresolved.",
            "",
            "## User Judgment Needed",
            "",
            "- Treat M64 as a bounded adapter repair, not as a new method contribution by itself.",
            "- Stop the `Open3DSG` route if M64 does not preserve the diagnostic gain under leakage-safe implementation and failure analysis.",
            "",
            "## Next",
            "",
            f"- {decision['next_recommended_unit']}.",
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    query_rows = load_query_rows()
    target_by_uid = load_target_rows()
    object_rows = read_jsonl(M61_OBJECT_ROWS)
    objects_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in object_rows:
        objects_by_scan[str(row["scan_id"])].append(row)

    current_m60 = read_json(M60_METRICS)["policy_metrics"]
    concept = read_json(M49_METRICS)["policy_metrics"]
    h001 = read_json(M52_METRICS)["policy_metrics"]
    current_policy_rows = read_jsonl(M60_POLICY_ROWS)
    diagnostic_strict, strict_rows = evaluate_diagnostic_policy(
        query_rows,
        target_by_uid,
        objects_by_scan,
        policy="open3dsg_predicted_terms_bbox_strict_top5_diagnostic_v0",
        match_mode="predicted_terms",
        threshold_m=0.5,
        budget=5,
    )
    diagnostic_relaxed, relaxed_rows = evaluate_diagnostic_policy(
        query_rows,
        target_by_uid,
        objects_by_scan,
        policy="open3dsg_predicted_terms_bbox_relaxed_1m_top3_diagnostic_v0",
        match_mode="predicted_terms",
        threshold_m=1.0,
        budget=3,
    )
    failure_rows = build_failure_audit_rows(query_rows, objects_by_scan, current_policy_rows)
    failure_summary = {
        "rows": len(failure_rows),
        "target_object_present_rows": sum(1 for row in failure_rows if row["target_object_present_in_top20_candidates"]),
        "target_primary_rows": sum(1 for row in failure_rows if row["target_has_primary_label_candidate"]),
        "target_expanded_rows": sum(1 for row in failure_rows if row["target_has_expanded_term_candidate"]),
        "no_primary_but_expanded_rows": sum(1 for row in failure_rows if row["primary_label_candidate_objects"] == 0 and row["expanded_term_candidate_objects"] > 0),
        "current_strict_failure_counts": dict(sorted(Counter(str(row["current_strict_failure_class"]) for row in failure_rows).items())),
        "no_primary_by_label": dict(sorted(Counter(str(row["query_label"]) for row in failure_rows if row["primary_label_candidate_objects"] == 0).items())),
    }
    comparison_rows = [
        metric_row("H001", "task_context_memory_trust_reobserve_v0", h001["task_context_memory_trust_reobserve_v0"], "main method"),
        metric_row("H001", "static_memory_only_v0", h001["static_memory_only_v0"], "naive baseline"),
        metric_row("H001", "context_agnostic_memory_trust_reobserve_v0", h001["context_agnostic_memory_trust_reobserve_v0"], "ablation"),
        metric_row("ConceptGraphs", "conceptgraphs_clip_rank_bbox_strict_top5_v0", concept["conceptgraphs_clip_rank_bbox_strict_top5_v0"], "positive external map baseline"),
        metric_row("ConceptGraphs", "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0", concept["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"], "external relaxed diagnostic"),
        metric_row("Open3DSG", "open3dsg_objects_probs_bbox_strict_top5_v0", current_m60["open3dsg_objects_probs_bbox_strict_top5_v0"], "fixed M60 current primary-label adapter"),
        metric_row("Open3DSG", "open3dsg_objects_probs_bbox_relaxed_1m_top3_v0", current_m60["open3dsg_objects_probs_bbox_relaxed_1m_top3_v0"], "fixed M60 current primary-label adapter"),
        metric_row("Open3DSG", diagnostic_strict["policy"], diagnostic_strict, "diagnostic predicted-vocabulary term expansion"),
        metric_row("Open3DSG", diagnostic_relaxed["policy"], diagnostic_relaxed, "diagnostic predicted-vocabulary term expansion"),
    ]
    current_open3dsg = current_m60["open3dsg_objects_probs_bbox_strict_top5_v0"]
    concept_strict = concept["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    diagnostic_gain = int(diagnostic_strict["query_bridge_success_rows"]) - int(current_open3dsg["query_bridge_success_rows"])
    selected_route = (
        "bounded_open3dsg_predicted_vocab_expansion_repair_next"
        if diagnostic_gain >= 30 and int(diagnostic_strict["query_bridge_success_rows"]) >= int(concept_strict["query_bridge_success_rows"])
        else "move_to_hovsg_or_openmask3d_next"
    )
    decision = {
        "status": "e005_m63_open3dsg_route_decision_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "selected_route": selected_route,
        "query_rows": len(query_rows),
        "current_open3dsg_strict_success_rows": current_open3dsg["query_bridge_success_rows"],
        "current_open3dsg_strict_success_rate": current_open3dsg["query_bridge_success_rate"],
        "diagnostic_expanded_strict_success_rows": diagnostic_strict["query_bridge_success_rows"],
        "diagnostic_expanded_strict_success_rate": diagnostic_strict["query_bridge_success_rate"],
        "diagnostic_expanded_relaxed_success_rows": diagnostic_relaxed["query_bridge_success_rows"],
        "diagnostic_expanded_relaxed_success_rate": diagnostic_relaxed["query_bridge_success_rate"],
        "conceptgraphs_strict_success_rows": concept_strict["query_bridge_success_rows"],
        "diagnostic_expanded_minus_current_open3dsg_strict_rows": diagnostic_gain,
        "diagnostic_expanded_minus_conceptgraphs_strict_rows": int(diagnostic_strict["query_bridge_success_rows"]) - int(concept_strict["query_bridge_success_rows"]),
        "h001_minus_diagnostic_expanded_strict_rows": int(h001["task_context_memory_trust_reobserve_v0"]["query_bridge_success_rows"]) - int(diagnostic_strict["query_bridge_success_rows"]),
        "open3dsg_main_table_baseline_ready": False,
        "diagnostic_not_paper_claim": True,
        "next_recommended_unit": "E005-M64 leakage-safe Open3DSG predicted-vocabulary expansion policy implementation/evaluation",
    }
    write_json(ARTIFACT_DIR / "coverage.json", decision)
    write_json(ARTIFACT_DIR / "failure_summary.json", failure_summary)
    write_jsonl(ARTIFACT_DIR / "comparison_rows.jsonl", comparison_rows)
    write_jsonl(ARTIFACT_DIR / "failure_audit_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "diagnostic_policy_rows.jsonl", strict_rows + relaxed_rows)
    write_csv(ARTIFACT_DIR / "comparison_rows.csv", comparison_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(decision, comparison_rows, failure_summary), encoding="utf-8")
    return decision


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
