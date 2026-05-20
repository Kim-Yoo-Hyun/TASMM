#!/usr/bin/env python3
"""Define the H001 heldout policy replay contract on the M38 query universe."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M49_DIR = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0"
M50_DIR = EXP_ROOT / "artifacts" / "E005-M50_h001_vs_conceptgraphs_gate_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M51_h001_heldout_policy_replay_contract_v0"
DATASET_ROOT = ROOT / "local_dataset"
THRESHOLD_M = 0.5
VERSION = "e005_m51_h001_heldout_policy_replay_contract_v0"
CONCEPTGRAPHS_PRIMARY_POLICY = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
H001_PRIMARY_POLICY = "task_context_memory_trust_reobserve_v0"


REQUIRED_E004_REPLAY_FIELDS = [
    "bridge_query_uid",
    "row_uid",
    "base_row_uid",
    "task_context_id",
    "label_canonical",
    "current_rescan_id",
    "pair_uid",
    "row_band",
    "old_memory_is_stale",
    "expected_memory_state",
    "same_label_detector_proposal_count",
    "old_location_dead_end_expected",
    "scene_aligned_static_error_m",
    "success_threshold_m",
    "query_target_rank_by_detector_score",
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


def point_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def planar_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def transform_point_row(point: list[float], matrix: list[float]) -> list[float]:
    x, y, z = point
    return [
        x * matrix[0] + y * matrix[4] + z * matrix[8] + matrix[12],
        x * matrix[1] + y * matrix[5] + z * matrix[9] + matrix[13],
        x * matrix[2] + y * matrix[6] + z * matrix[10] + matrix[14],
    ]


def invert_rigid_row_transform(matrix: list[float]) -> list[float]:
    rotation_t = [
        matrix[0],
        matrix[4],
        matrix[8],
        0.0,
        matrix[1],
        matrix[5],
        matrix[9],
        0.0,
        matrix[2],
        matrix[6],
        matrix[10],
        0.0,
    ]
    tx, ty, tz = matrix[12], matrix[13], matrix[14]
    inv_translation = [
        -(tx * rotation_t[0] + ty * rotation_t[4] + tz * rotation_t[8]),
        -(tx * rotation_t[1] + ty * rotation_t[5] + tz * rotation_t[9]),
        -(tx * rotation_t[2] + ty * rotation_t[6] + tz * rotation_t[10]),
    ]
    return rotation_t + inv_translation + [1.0]


def round_or_none(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def load_semseg_objects(scan_id: str) -> dict[str, dict[str, Any]]:
    path = DATASET_ROOT / "3RScan" / "scans" / scan_id / "semseg.v2.json"
    if not path.exists():
        return {}
    payload = read_json(path)
    rows = {}
    for group in payload.get("segGroups", []):
        object_id = str(group.get("objectId", group.get("id")))
        centroid = group.get("obb", {}).get("centroid")
        if centroid is None:
            continue
        rows[object_id] = {
            "object_id": object_id,
            "label": str(group.get("label", "")),
            "centroid": [float(value) for value in centroid],
        }
    return rows


def metadata_index() -> dict[tuple[str, str], dict[str, Any]]:
    payload = read_json(DATASET_ROOT / "3RScan" / "files" / "3RScan.json")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for group in payload:
        reference_scan_id = str(group.get("reference", ""))
        for scan in group.get("scans", []):
            rescan_id = str(scan.get("reference", ""))
            if reference_scan_id and rescan_id:
                index[(reference_scan_id, rescan_id)] = scan
    return index


def rigid_index(pair_metadata: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows = {}
    for rigid in pair_metadata.get("rigid", []):
        if isinstance(rigid, dict):
            rows[(str(rigid.get("instance_reference")), str(rigid.get("instance_rescan")))] = rigid
    return rows


def geometry_fields(query: dict[str, Any], pair_meta: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    ref_id = str(query["object_instance_id_ref"])
    rescan_id = str(query["object_instance_id_rescan"])
    ref_objects = load_semseg_objects(str(query["reference_scan_id"]))
    rescan_objects = load_semseg_objects(str(query["current_rescan_id"]))
    ref_obj = ref_objects.get(ref_id)
    rescan_obj = rescan_objects.get(rescan_id)
    rigid = rigid_index(pair_meta).get((ref_id, rescan_id))
    if not ref_obj:
        return {}, "missing_reference_semseg_object"
    if not rescan_obj:
        return {}, "missing_rescan_semseg_object"
    if not rigid:
        return {}, "missing_rigid_object_transform"
    if "transform" not in pair_meta:
        return {}, "missing_pair_scene_transform"

    scene_inverse = invert_rigid_row_transform(pair_meta["transform"])
    old_scene_aligned = transform_point_row(ref_obj["centroid"], scene_inverse)
    scene_error = point_distance(old_scene_aligned, rescan_obj["centroid"])
    scene_planar_error = planar_distance(old_scene_aligned, rescan_obj["centroid"])
    object_direct = point_distance(transform_point_row(ref_obj["centroid"], rigid["transform"]), rescan_obj["centroid"])
    object_inverse = point_distance(transform_point_row(ref_obj["centroid"], invert_rigid_row_transform(rigid["transform"])), rescan_obj["centroid"])
    return {
        "scene_aligned_static_error_m": round_or_none(scene_error),
        "scene_aligned_static_planar_error_m": round_or_none(scene_planar_error),
        "old_scene_aligned_centroid": [round(float(value), 6) for value in old_scene_aligned],
        "current_target_centroid": [round(float(value), 6) for value in rescan_obj["centroid"]],
        "row_geometry_error_m": round_or_none(min(object_direct, object_inverse)),
        "success_threshold_m": THRESHOLD_M,
        "static_memory_success": scene_error <= THRESHOLD_M,
    }, None


def load_heldout_queries() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch_id in ["heldout_b01", "heldout_b02", "heldout_b03"]:
        rows.extend(read_jsonl(M45_CONTRACT_DIR / f"{batch_id}_query_rows.jsonl"))
    return rows


def load_conceptgraphs_policy_rows() -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch_suffix in ["b01", "b02", "b03"]:
        rows.extend(read_jsonl(M45_METRIC_DIR / f"policy_rows_heldout_{batch_suffix}.jsonl"))
    primary = [row for row in rows if row.get("policy") == CONCEPTGRAPHS_PRIMARY_POLICY]
    return {str(row["query_uid"]): row for row in primary}


def build_adapter_rows(queries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pair_meta = metadata_index()
    cg_by_uid = load_conceptgraphs_policy_rows()
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for query in queries:
        query_uid = str(query["bridge_query_uid"])
        meta = pair_meta.get((str(query["reference_scan_id"]), str(query["current_rescan_id"])))
        cg = cg_by_uid.get(query_uid)
        if not meta:
            issues.append({"query_uid": query_uid, "issue": "missing_pair_metadata"})
            continue
        if not cg:
            issues.append({"query_uid": query_uid, "issue": "missing_conceptgraphs_policy_row"})
            continue
        geometry, issue = geometry_fields(query, meta)
        if issue:
            issues.append({"query_uid": query_uid, "issue": issue})
            continue
        row = {
            "m51_version": VERSION,
            "bridge_query_uid": query_uid,
            "row_uid": query["row_uid"],
            "base_row_uid": query["base_row_uid"],
            "pair_uid": query["pair_uid"],
            "reference_scan_id": query["reference_scan_id"],
            "current_rescan_id": query["current_rescan_id"],
            "target_uid": query["target_uid"],
            "object_instance_id_ref": query["object_instance_id_ref"],
            "object_instance_id_rescan": query["object_instance_id_rescan"],
            "label_canonical": query["label_canonical"],
            "task_context_id": query["task_context_id"],
            "row_band": query["row_band"],
            "expected_memory_state": query["expected_memory_state"],
            "old_memory_is_stale": bool(query["old_memory_is_stale"]),
            "old_location_dead_end_expected": bool(query["old_location_dead_end_expected"]),
            "current_observation_source": "ConceptGraphs",
            "current_observation_policy_source": CONCEPTGRAPHS_PRIMARY_POLICY,
            "same_label_detector_proposal_count": int(cg["candidate_count"]),
            "query_target_rank_by_detector_score": cg.get("target_rank"),
            "query_target_detected": bool(cg.get("target_detected")),
            "query_target_best_match_distance_m": cg.get("target_match_distance_m"),
            "target_recall_best_match_distance_m": cg.get("target_match_distance_m"),
            "false_positive_before_target_count": cg.get("false_positive_before_target_count"),
            "allowed_policy_inputs": [
                "task_context_id",
                "expected_memory_state",
                "old_memory_is_stale",
                "same_label_detector_proposal_count",
            ],
            "blocked_policy_inputs": [
                "target_uid",
                "object_instance_id_rescan",
                "query_target_rank_by_detector_score",
                "query_target_best_match_distance_m",
                "false_positive_before_target_count",
                "query_bridge_success",
            ],
            **geometry,
        }
        missing = [field for field in REQUIRED_E004_REPLAY_FIELDS if field not in row]
        if missing:
            issues.append({"query_uid": query_uid, "issue": "missing_required_adapter_fields", "fields": missing})
        rows.append(row)
    return rows, issues


def build_contract(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": coverage["status"],
        "source_artifacts": {
            "m38_query_contract": str(M45_CONTRACT_DIR),
            "conceptgraphs_policy_rows": str(M45_METRIC_DIR),
            "conceptgraphs_full_heldout_aggregation": str(M49_DIR),
            "m50_gate": str(M50_DIR),
            "dataset_root": str(DATASET_ROOT),
        },
        "target_query_universe": {
            "name": "M38 heldout_sequence_required",
            "query_rows": coverage["query_rows"],
            "scan_count": coverage["scan_count"],
            "task_contexts": coverage["task_context_counts"],
            "labels": coverage["label_count"],
        },
        "replay_adapter": {
            "current_observation_source": "ConceptGraphs",
            "target_rank_field": "query_target_rank_by_detector_score <- ConceptGraphs strict bbox target_rank",
            "candidate_count_field": "same_label_detector_proposal_count <- ConceptGraphs strict bbox candidate_count",
            "static_memory_field": "scene_aligned_static_error_m <- 3RScan scene inverse transform on reference object centroid",
            "success_threshold_m": THRESHOLD_M,
        },
        "policies_to_replay": [
            "static_memory_only_v0",
            "context_agnostic_memory_trust_reobserve_v0",
            H001_PRIMARY_POLICY,
            "detector_top1_v0",
            "detector_top3_v0",
            "detector_top5_v0",
            "detector_task_budget_v0",
            "bounded_old_memory_distance_guard_adaptive_top5_v0",
            "unbounded_old_memory_distance_guard_until_target_v0",
        ],
        "blocked_policy_inputs": [
            "target_uid",
            "object_instance_id_rescan",
            "query_target_rank_by_detector_score",
            "query_target_best_match_distance_m",
            "false_positive_before_target_count",
            "query_bridge_success",
            "static_memory_success",
        ],
        "primary_metrics": [
            "query_bridge_success_rate",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "old_location_dead_end_avoided_rate",
            "over_search_rate",
        ],
        "comparison_target": {
            "external_baseline": "ConceptGraphs",
            "baseline_policy": CONCEPTGRAPHS_PRIMARY_POLICY,
            "baseline_metric_source": str(M49_DIR / "metrics.json"),
            "paired_superiority_ready_after_replay": coverage["adapter_rows_ready"] == coverage["query_rows"],
        },
        "claim_boundary": [
            "This contract does not itself claim H001 superiority.",
            "H001 superiority requires replayed H001 policies and ConceptGraphs rows on the same M38 query rows.",
            "Real navigation SR/SPL remains unsupported until simulator/navmesh trajectory execution is added.",
        ],
        "next_unit": {
            "id": "E005-M52",
            "name": "H001 heldout policy replay run",
            "expected_command": "python experiments/E005_external_baseline_transition/tools/run_m52_h001_heldout_policy_replay.py",
        },
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M51 H001 Heldout Policy Replay Contract",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Heldout query rows: {coverage['query_rows']}.",
            f"- Adapter rows ready: {coverage['adapter_rows_ready']}.",
            f"- Adapter issues: {coverage['adapter_issue_count']}.",
            f"- Scans: {coverage['scan_count']}.",
            f"- Labels: {coverage['label_count']}.",
            f"- Static memory success rows: {coverage['static_memory_success_rows']}.",
            f"- ConceptGraphs target-detected rows: {coverage['conceptgraphs_target_detected_rows']}.",
            "",
            "## Claim Boundary",
            "",
            "- M51 is a replay contract and input-readiness gate, not a method result.",
            "- H001 vs `ConceptGraphs` superiority remains unclaimed until E005-M52 runs the replay.",
            "- `SR` / `SPL` remain proxy metrics, not real navigation metrics.",
            "",
            "## Agent Inference",
            "",
            "- The adapter can map `ConceptGraphs` target rank/count into the E004 policy schema while keeping target rank and match distance evaluation-only.",
            "- This is the right next step because E005-M50 showed no common query rows between previous H001 artifacts and the `ConceptGraphs` heldout result.",
            "",
            "## Next",
            "",
            "- E005-M52 H001 heldout policy replay run.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    queries = load_heldout_queries()
    adapter_rows, issues = build_adapter_rows(queries)
    conceptgraphs_detected = [row for row in adapter_rows if row.get("query_target_detected")]
    static_success = [row for row in adapter_rows if row.get("static_memory_success")]
    coverage = {
        "status": "e005_m51_h001_heldout_replay_contract_ready"
        if len(adapter_rows) == len(queries) and not issues
        else "e005_m51_h001_heldout_replay_contract_needs_adapter_repair",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "query_rows": len(queries),
        "adapter_rows_ready": len(adapter_rows),
        "adapter_issue_count": len(issues),
        "scan_count": len({row["current_rescan_id"] for row in adapter_rows}),
        "label_count": len({row["label_canonical"] for row in adapter_rows}),
        "task_context_counts": dict(sorted(Counter(row["task_context_id"] for row in adapter_rows).items())),
        "row_band_counts": dict(sorted(Counter(row["row_band"] for row in adapter_rows).items())),
        "static_memory_success_rows": len(static_success),
        "conceptgraphs_target_detected_rows": len(conceptgraphs_detected),
        "conceptgraphs_target_detected_rate": round(len(conceptgraphs_detected) / len(adapter_rows), 6) if adapter_rows else None,
        "ready_for_m52_replay": len(adapter_rows) == len(queries) and not issues,
        "paired_superiority_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M52 H001 heldout policy replay run"
        if len(adapter_rows) == len(queries) and not issues
        else "Repair E005-M51 adapter inputs",
    }
    contract = build_contract(coverage)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "contract.json", contract)
    write_jsonl(OUT_DIR / "adapter_preview_rows.jsonl", adapter_rows)
    write_jsonl(OUT_DIR / "adapter_issue_rows.jsonl", issues)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    return coverage


def main() -> int:
    coverage = run()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
