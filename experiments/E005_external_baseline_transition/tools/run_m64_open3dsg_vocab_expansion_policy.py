#!/usr/bin/env python3
"""Run E005-M64 leakage-safe Open3DSG predicted-vocabulary policy."""

from __future__ import annotations

import argparse
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
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M64_vocab_expansion_policy_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0"
OBJECT_CANDIDATE_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M61_denominator_aligned_export_v0"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M49_METRICS = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0" / "metrics.json"
M52_METRICS = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0" / "metrics.json"
M60_METRICS = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "metrics.json"
VERSION = "e005_m64_open3dsg_vocab_expansion_policy_v0"

POLICIES = [
    {
        "policy": "open3dsg_predicted_terms_bbox_strict_top5_v0",
        "budget": 5,
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
    },
    {
        "policy": "open3dsg_predicted_terms_bbox_relaxed_1m_top3_v0",
        "budget": 3,
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
    },
    {
        "policy": "open3dsg_predicted_terms_center_strict_top5_v0",
        "budget": 5,
        "distance_field": "eval_center_distance_m",
        "threshold_m": 0.5,
    },
]

POLICY_ALLOWED_INPUTS = [
    "scan_id",
    "query_label",
    "candidate_label",
    "candidate_score",
    "candidate_rank",
]
POLICY_BLOCKED_INPUTS = [
    "gt_object_label",
    "id2name_label",
    "target_uid",
    "object_instance_id_rescan",
    "target_geometry",
    "target_success_labels",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_label(value: str) -> str:
    text = value.lower().strip().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def split_vocab_label(raw_label: str) -> list[str]:
    return str(raw_label).split("\t")


def predicted_terms(raw_label: str) -> list[str]:
    parts = split_vocab_label(raw_label)
    fields = parts[1:] if len(parts) >= 2 and parts[0].strip().isdigit() else parts
    terms: set[str] = set()
    for field in fields:
        for token in re.split(r"[/;,]", field):
            token = normalize_label(token)
            if token:
                terms.add(token)
    return sorted(terms)


def primary_predicted_term(raw_label: str) -> str:
    parts = split_vocab_label(raw_label)
    if len(parts) >= 2 and parts[0].strip().isdigit():
        return normalize_label(parts[1])
    return normalize_label(raw_label)


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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def vec3(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    try:
        return [float(value[0]), float(value[1]), float(value[2])]
    except (TypeError, ValueError):
        return None


def euclidean(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None:
        return None
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


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


def strip_object_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scan_id": str(row.get("scan_id")),
        "object_id": str(row.get("object_id")),
        "candidate_label": str(row.get("candidate_label", "")),
        "candidate_score": float(row.get("candidate_score", 0.0)),
        "candidate_rank": int(row.get("candidate_rank", 10**9)),
        "candidate_label_index": row.get("candidate_label_index"),
        "candidate_vocab": row.get("candidate_vocab"),
        "object_candidate_record_id": row.get("object_candidate_record_id"),
        "bbox_or_center": row.get("bbox_or_center", {}),
    }


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


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def failure_class(
    same_scan_candidates: int,
    ranked_candidates: list[dict[str, Any]],
    target_detected: bool,
    target_rank: int | None,
    budget: int,
) -> str:
    if same_scan_candidates == 0:
        return "scan_not_covered_by_object_candidate_source"
    if not ranked_candidates:
        return "no_predicted_term_candidates"
    if not target_detected:
        return "target_object_not_in_predicted_term_candidates"
    if target_rank is not None and target_rank > budget:
        return "target_present_but_rank_gt_budget"
    return "success_within_budget"


def metric_from_policy_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    detected_rows = [row for row in rows if row.get("target_detected")]
    success_rows = [row for row in rows if row.get("query_bridge_success")]
    old_dead_end_rows = [row for row in rows if row.get("old_location_dead_end_expected")]
    old_dead_end_avoided = [row for row in old_dead_end_rows if row.get("old_location_dead_end_avoided")]
    return {
        "rows": len(rows),
        "query_bridge_success_rows": len(success_rows),
        "query_bridge_success_rate": safe_rate(len(success_rows), len(rows)),
        "target_detected_rows": len(detected_rows),
        "target_detected_rate": safe_rate(len(detected_rows), len(rows)),
        "mean_target_rank_if_detected": safe_mean(
            [int(row["target_rank"]) for row in detected_rows if row.get("target_rank") is not None]
        ),
        "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
        "old_location_dead_end_rows": len(old_dead_end_rows),
        "old_location_dead_end_avoided_rows": len(old_dead_end_avoided),
        "old_location_dead_end_avoided_rate": safe_rate(len(old_dead_end_avoided), len(old_dead_end_rows)),
        "failure_class_counts": dict(sorted(Counter(str(row.get("failure_class")) for row in rows).items())),
    }


def comparison_metric_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sources = [
        (
            "H001",
            M52_METRICS,
            "task_context_memory_trust_reobserve_v0",
            "main method",
        ),
        (
            "H001",
            M52_METRICS,
            "static_memory_only_v0",
            "naive baseline",
        ),
        (
            "ConceptGraphs",
            M49_METRICS,
            "conceptgraphs_clip_rank_bbox_strict_top5_v0",
            "external map baseline",
        ),
        (
            "Open3DSG",
            M60_METRICS,
            "open3dsg_objects_probs_bbox_strict_top5_v0",
            "primary-label adapter",
        ),
    ]
    for source, path, policy, note in sources:
        payload = read_json(path)
        metric = payload.get("policy_metrics", {}).get(policy, {})
        if not metric:
            continue
        rows.append(
            {
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
        )
    for policy, metric in sorted(metrics["policy_metrics"].items()):
        rows.append(
            {
                "source": "Open3DSG",
                "policy": policy,
                "rows": metric.get("rows"),
                "success_rows": metric.get("query_bridge_success_rows"),
                "success_rate": metric.get("query_bridge_success_rate"),
                "target_detected_rows": metric.get("target_detected_rows"),
                "target_detected_rate": metric.get("target_detected_rate"),
                "mean_expected_search_cost": metric.get("mean_expected_search_cost"),
                "mean_attempt_spl_proxy": metric.get("mean_attempt_spl_proxy"),
                "note": "leakage-safe predicted-vocabulary expansion policy",
            }
        )
    return rows


def build_report(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    lines = [
        "# E005-M64 Open3DSG Vocabulary Expansion Policy",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Query denominator rows: {coverage['query_rows']}.",
        f"- Object candidate rows: {coverage['object_candidate_rows']}.",
        f"- Query scan overlap: {coverage['scan_overlap_count']} / {coverage['query_scan_count']}.",
        f"- Query candidate rows: {coverage['query_candidate_rows']}.",
        f"- Candidate eval rows: {coverage['candidate_eval_rows']}.",
        f"- Policy rows: {coverage['policy_rows']}.",
        f"- Source modified: {coverage['source_modified']}.",
        "",
        "## Leakage Audit",
        "",
        f"- Policy allowed inputs: `{', '.join(coverage['policy_allowed_inputs'])}`.",
        f"- Policy blocked inputs: `{', '.join(coverage['policy_blocked_inputs'])}`.",
        f"- Uses `gt_object_label`: {coverage['uses_gt_object_label']}.",
        f"- Uses `id2name_label`: {coverage['uses_id2name_label']}.",
        f"- Uses target uid before ranking: {coverage['uses_target_uid_before_ranking']}.",
        f"- Uses target geometry before ranking: {coverage['uses_target_geometry_before_ranking']}.",
        "",
        "## Policy Metrics",
        "",
    ]
    for policy, row in metrics["policy_metrics"].items():
        lines.append(
            f"- `{policy}`: success {row['query_bridge_success_rows']} / {row['rows']} "
            f"= {row['query_bridge_success_rate']}, target detected {row['target_detected_rows']} / {row['rows']}, "
            f"mean `ExpectedSearchCost` {row['mean_expected_search_cost']}, "
            f"mean proxy `SPL` {row['mean_attempt_spl_proxy']}."
        )
    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- This promotes the M63 diagnostic into a leakage-safe bounded adapter policy.",
            "- It can support an `Open3DSG` predicted-vocabulary baseline row, not a standalone method contribution.",
            "- Final real RGB-D/open-vocabulary robustness and real navigation `SR`/`SPL` claims remain false.",
            "",
            "## Agent Inference",
            "",
            "- The main blocker in the previous `Open3DSG` result was label-vocabulary mismatch, not only scene coverage.",
            "- The next unit should integrate this bounded policy into the paper-table claim ledger and state the reviewer boundary explicitly.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )
    return "\n".join(lines)


def write_all_outputs(
    query_candidate_rows: list[dict[str, Any]],
    candidate_eval_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    metrics: dict[str, Any],
    coverage: dict[str, Any],
    report: str,
) -> None:
    for root in [LOCAL_DATA_DIR, ARTIFACT_DIR]:
        write_jsonl(root / "open3dsg_vocab_query_candidate_rows.jsonl", query_candidate_rows)
        write_jsonl(root / "open3dsg_vocab_candidate_eval_rows.jsonl", candidate_eval_rows)
        write_jsonl(root / "open3dsg_vocab_policy_rows.jsonl", policy_rows)
        write_jsonl(root / "comparison_rows.jsonl", comparison_metric_rows(metrics))
        write_json(root / "metrics.json", metrics)
        write_json(root / "coverage.json", coverage)
        write_text(root / "report.md", report)


def run(require_object_candidates_ready: bool) -> dict[str, Any]:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    query_rows = load_query_rows()
    target_by_uid = load_target_rows()
    object_rows_raw = read_jsonl(OBJECT_CANDIDATE_DIR / "open3dsg_object_candidates.jsonl")
    manifest = read_json(OBJECT_CANDIDATE_DIR / "open3dsg_object_candidates.manifest.json")
    errors: list[str] = []
    if require_object_candidates_ready and not object_rows_raw:
        errors.append("require_object_candidates_ready_but_no_object_candidate_rows")
    if len(query_rows) != 195:
        errors.append(f"unexpected_query_denominator:{len(query_rows)}")

    objects_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_row in object_rows_raw:
        row = strip_object_candidate(raw_row)
        objects_by_scan[str(row["scan_id"])].append(row)

    query_candidate_rows: list[dict[str, Any]] = []
    candidate_eval_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    matched_terms_counter: Counter[str] = Counter()

    for query in query_rows:
        scan_id = str(query["current_rescan_id"])
        query_label = normalize_label(str(query["label_canonical"]))
        same_scan = objects_by_scan.get(scan_id, [])
        candidates: list[dict[str, Any]] = []
        matched_terms_by_record: dict[str, list[str]] = {}
        for obj in same_scan:
            terms = predicted_terms(str(obj["candidate_label"]))
            if query_label not in terms:
                continue
            candidates.append(obj)
            record_id = str(obj["object_candidate_record_id"])
            matched_terms_by_record[record_id] = [query_label]
            matched_terms_counter[query_label] += 1
        ranked = rank_candidates(candidates)
        target = target_by_uid.get(str(query["target_uid"]))
        target_center, target_extent = target_center_and_extent(target)
        eval_rows_for_query: list[dict[str, Any]] = []

        for rank, obj in enumerate(ranked, start=1):
            candidate_center, candidate_extent = candidate_center_and_extent(obj)
            center_distance = euclidean(candidate_center, target_center)
            bbox_distance = aabb_distance(candidate_center, candidate_extent, target_center, target_extent)
            candidate_uid = f"open3dsg:{obj['scan_id']}:{obj['object_id']}"
            record_id = str(obj["object_candidate_record_id"])
            qc = {
                "m64_version": VERSION,
                "record_type": "open3dsg_vocab_query_candidate",
                "query_uid": query["bridge_query_uid"],
                "row_uid": query["row_uid"],
                "scan_id": scan_id,
                "query_label": query["label_canonical"],
                "task_context_id": query["task_context_id"],
                "row_band": query["row_band"],
                "candidate_object_id": str(obj["object_id"]),
                "candidate_uid": candidate_uid,
                "candidate_label": obj["candidate_label"],
                "candidate_label_primary_predicted": primary_predicted_term(str(obj["candidate_label"])),
                "candidate_label_terms": predicted_terms(str(obj["candidate_label"])),
                "matched_predicted_terms": matched_terms_by_record.get(record_id, []),
                "candidate_score": float(obj["candidate_score"]),
                "candidate_rank": int(obj["candidate_rank"]),
                "rank": rank,
                "policy_allowed_input": True,
                "policy_input_fields_used": POLICY_ALLOWED_INPUTS,
                "source_object_candidate_record_id": obj["object_candidate_record_id"],
            }
            query_candidate_rows.append(qc)
            ev = {
                **qc,
                "record_type": "open3dsg_vocab_candidate_eval",
                "target_uid": query["target_uid"],
                "target_object_id": str(query["object_instance_id_rescan"]),
                "eval_center_distance_m": None if center_distance is None else round(center_distance, 6),
                "eval_bbox_distance_m": None if bbox_distance is None else round(bbox_distance, 6),
                "eval_center_success_strict": bool(center_distance is not None and center_distance <= 0.5),
                "eval_bbox_success_strict": bool(bbox_distance is not None and bbox_distance <= 0.5),
                "eval_bbox_success_relaxed_1m": bool(bbox_distance is not None and bbox_distance <= 1.0),
                "target_geometry_available": target_center is not None,
                "candidate_geometry_available": candidate_center is not None,
                "eval_only_fields_used_after_ranking": [
                    "target_uid",
                    "object_instance_id_rescan",
                    "target_geometry",
                    "candidate_geometry",
                ],
            }
            candidate_eval_rows.append(ev)
            eval_rows_for_query.append(ev)

        for policy in POLICIES:
            distance_field = policy["distance_field"]
            threshold = float(policy["threshold_m"])
            budget = int(policy["budget"])
            detected_rows = [
                row
                for row in eval_rows_for_query
                if row.get(distance_field) is not None and float(row[distance_field]) <= threshold
            ]
            target_rank = min((int(row["rank"]) for row in detected_rows), default=None)
            target_detected = target_rank is not None
            returned = min(len(ranked), budget)
            success = bool(target_rank is not None and target_rank <= budget)
            expected_cost = int(target_rank) if success and target_rank is not None else returned + 1
            policy_rows.append(
                {
                    "m64_version": VERSION,
                    "record_type": "open3dsg_vocab_policy_result",
                    "query_uid": query["bridge_query_uid"],
                    "row_uid": query["row_uid"],
                    "target_uid": query["target_uid"],
                    "scan_id": scan_id,
                    "query_label": query["label_canonical"],
                    "task_context_id": query["task_context_id"],
                    "row_band": query["row_band"],
                    "expected_memory_state": query["expected_memory_state"],
                    "old_memory_is_stale": bool(query["old_memory_is_stale"]),
                    "old_location_dead_end_expected": bool(query["old_location_dead_end_expected"]),
                    "policy": policy["policy"],
                    "candidate_count": len(ranked),
                    "same_scan_candidate_rows": len(same_scan),
                    "returned_location_count": returned,
                    "target_detected": target_detected,
                    "target_rank": target_rank,
                    "query_bridge_success": success,
                    "expected_search_cost": expected_cost,
                    "attempt_spl_proxy": attempt_spl(success, expected_cost),
                    "old_location_dead_end_avoided": bool(query["old_location_dead_end_expected"] and success),
                    "distance_field": distance_field,
                    "threshold_m": threshold,
                    "budget": budget,
                    "failure_class": failure_class(len(same_scan), ranked, target_detected, target_rank, budget),
                    "policy_allowed_input": True,
                    "policy_input_fields_used": POLICY_ALLOWED_INPUTS,
                    "policy_blocked_inputs": POLICY_BLOCKED_INPUTS,
                    "eval_only_fields_used_after_ranking": [
                        "target_uid",
                        "object_instance_id_rescan",
                        "target_geometry",
                        "candidate_geometry",
                    ],
                    "uses_gt_object_label": False,
                    "uses_id2name_label": False,
                    "uses_target_uid_before_ranking": False,
                    "uses_target_geometry_before_ranking": False,
                    "real_rgbd_open_vocabulary_robustness_claim_ready": False,
                    "real_navigation_sr_spl_ready": False,
                }
            )

    policy_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policy_rows:
        policy_groups[str(row["policy"])].append(row)
    metrics = {
        "version": VERSION,
        "policy_metrics": {policy: metric_from_policy_rows(rows) for policy, rows in sorted(policy_groups.items())},
        "by_failure_class": dict(sorted(Counter(row["failure_class"] for row in policy_rows).items())),
        "matched_query_label_candidate_rows": dict(sorted(matched_terms_counter.items())),
        "scan_overlap": {
            "object_candidate_scans": sorted(objects_by_scan),
            "query_scans": sorted({str(row["current_rescan_id"]) for row in query_rows}),
            "overlap": sorted(set(objects_by_scan) & {str(row["current_rescan_id"]) for row in query_rows}),
        },
    }
    scan_overlap_count = len(metrics["scan_overlap"]["overlap"])
    strict = metrics["policy_metrics"].get("open3dsg_predicted_terms_bbox_strict_top5_v0", {})
    relaxed = metrics["policy_metrics"].get("open3dsg_predicted_terms_bbox_relaxed_1m_top3_v0", {})
    status = (
        "e005_m64_open3dsg_vocab_expansion_policy_ready"
        if not errors and int(strict.get("query_bridge_success_rows", 0)) > 0
        else "e005_m64_open3dsg_vocab_expansion_policy_failed"
    )
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "query_rows": len(query_rows),
        "object_candidate_source": "E005-M61_denominator_aligned_export_v0",
        "object_candidate_rows": len(object_rows_raw),
        "object_candidate_completed_batches": manifest.get("completed_batches"),
        "object_candidate_rows_written_manifest": manifest.get("rows_written"),
        "object_candidate_scan_count": len(objects_by_scan),
        "target_geometry_rows": len(target_by_uid),
        "query_scan_count": len({str(row["current_rescan_id"]) for row in query_rows}),
        "scan_overlap_count": scan_overlap_count,
        "query_candidate_rows": len(query_candidate_rows),
        "candidate_eval_rows": len(candidate_eval_rows),
        "policy_rows": len(policy_rows),
        "policy_count": len(policy_groups),
        "source_modified": False,
        "errors": errors,
        "policy_allowed_inputs": POLICY_ALLOWED_INPUTS,
        "policy_blocked_inputs": POLICY_BLOCKED_INPUTS,
        "uses_gt_object_label": False,
        "uses_id2name_label": False,
        "uses_target_uid_before_ranking": False,
        "uses_target_geometry_before_ranking": False,
        "uses_target_success_labels_before_ranking": False,
        "diagnostic_promoted_to_policy": True,
        "open3dsg_vocab_policy_ready": status == "e005_m64_open3dsg_vocab_expansion_policy_ready",
        "open3dsg_main_table_candidate_ready": bool(
            int(strict.get("query_bridge_success_rows", 0)) >= 114
            and int(relaxed.get("query_bridge_success_rows", 0)) >= 144
        ),
        "final_external_baseline_claim_ready": False,
        "real_rgbd_open_vocabulary_robustness_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "paper_claim_boundary": "bounded Open3DSG predicted-vocabulary adapter baseline, not standalone method novelty",
        "next_recommended_unit": "E005-M65 Open3DSG vocabulary-policy claim-boundary / paper-table integration decision",
    }
    report = build_report(coverage, metrics)
    write_all_outputs(query_candidate_rows, candidate_eval_rows, policy_rows, metrics, coverage, report)
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-object-candidates-ready", action="store_true")
    args = parser.parse_args()
    result = run(require_object_candidates_ready=args.require_object_candidates_ready)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
