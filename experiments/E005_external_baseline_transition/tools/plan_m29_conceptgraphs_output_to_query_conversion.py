#!/usr/bin/env python3
"""Plan conversion from ConceptGraphs object-map outputs to query-level rows."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M27_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
M28_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M28_conceptgraphs_output_schema_v0"
M60_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M29_conceptgraphs_output_to_query_conversion_plan_v0"

VERSION = "e005_m29_conceptgraphs_output_to_query_conversion_plan_v0"


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


def schema_field(schema: dict[str, Any], *keys: str) -> Any:
    current: Any = schema
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def object_fields(schema: dict[str, Any], section: str) -> dict[str, Any]:
    fields = schema_field(schema, section, "fields", "objects", "first_item_fields")
    return fields if isinstance(fields, dict) else {}


def object_count(schema: dict[str, Any], section: str) -> int:
    value = schema_field(schema, section, "fields", "objects", "length")
    return int(value) if isinstance(value, int) else 0


def infer_smoke_scan_id(m28_coverage: dict[str, Any]) -> str:
    full_pcd = m28_coverage.get("inventory", {}).get("full_pcd", "")
    if full_pcd:
        path = Path(full_pcd)
        if len(path.parts) >= 3:
            return path.parent.parent.name
    return ""


def build_query_join_rows(query_rows: list[dict[str, Any]], smoke_scan_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in query_rows:
        if row.get("current_rescan_id") != smoke_scan_id:
            continue
        rows.append(
            {
                "bridge_query_uid": row.get("bridge_query_uid"),
                "current_rescan_id": row.get("current_rescan_id"),
                "reference_scan_id": row.get("reference_scan_id"),
                "pair_uid": row.get("pair_uid"),
                "label_canonical": row.get("label_canonical"),
                "task_context_id": row.get("task_context_id"),
                "expected_memory_state": row.get("expected_memory_state"),
                "old_memory_is_stale": row.get("old_memory_is_stale"),
                "old_location_dead_end_expected": row.get("old_location_dead_end_expected"),
                "policy_allowed_inputs": row.get("allowed_policy_inputs", []),
                "eval_only_fields": row.get("blocked_policy_inputs", []),
                "success_threshold_m": row.get("success_threshold_m"),
            }
        )
    return rows


def build_candidate_schema(post_fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "conceptgraphs_object_candidate_jsonl_v0",
        "source_artifact": "full_pcd_post.objects",
        "required_source_fields": {
            "geometry": ["pcd_np", "bbox_np"],
            "semantic_features": ["clip_ft"],
            "confidence": ["conf", "num_detections", "n_points"],
            "traceability": ["image_idx", "mask_idx", "color_path", "xyxy"],
        },
        "observed_source_fields": sorted(post_fields),
        "output_fields": [
            "candidate_uid",
            "scan_id",
            "source_baseline",
            "source_object_index",
            "candidate_center_xyz",
            "candidate_bbox_min_xyz",
            "candidate_bbox_max_xyz",
            "candidate_extent_xyz",
            "candidate_point_count",
            "candidate_num_detections",
            "candidate_confidence_mean",
            "candidate_confidence_max",
            "candidate_clip_feature_source",
            "query_uid",
            "query_label",
            "semantic_score",
            "rank",
            "policy_allowed_input",
            "eval_match_distance_m",
            "eval_success",
        ],
        "policy_input_rule": {
            "allowed": [
                "candidate geometry from ConceptGraphs object map",
                "candidate confidence/visibility trace",
                "candidate CLIP similarity to query label",
                "task_context_id",
                "pre-evaluation staleness metadata",
            ],
            "blocked": [
                "target_uid",
                "object_instance_id_rescan",
                "matched_3dssg_instance_id",
                "eval_match_distance_m before ranking",
                "E001/E002/E003 success labels before ranking",
            ],
        },
    }


def build_conversion_contract(smoke_scan_id: str, class_set_none_variant: bool) -> dict[str, Any]:
    return {
        "contract_id": "conceptgraphs_to_tasmm_query_bridge_v0",
        "input_artifacts": {
            "conceptgraphs_runtime": str(M27_DIR),
            "conceptgraphs_schema": str(M28_DIR),
            "query_bridge_rows": str(M60_DIR / "query_bridge_rows.jsonl"),
        },
        "scan_join_key": "current_rescan_id == ConceptGraphs scene_id",
        "object_export": [
            "Load full_pcd_post.pkl.gz inside the ConceptGraphs Docker image or another env with numpy/open3d-compatible pickle support.",
            "For each post object, compute center from pcd_np mean and bbox min/max from bbox_np.",
            "Export one candidate row per object before applying any task or label-specific ranking.",
        ],
        "semantic_scoring": {
            "class_set_none_variant": class_set_none_variant,
            "direct_class_name_filtering_ready": not class_set_none_variant,
            "required_next_gate": "CLIP text encoder smoke for query labels against object clip_ft",
            "fallback_if_clip_text_gate_fails": "class-agnostic localization/object-map candidate export only; no open-vocabulary ranking claim",
        },
        "query_ranking": [
            "Join query rows by scan_id and score candidates for each label_canonical.",
            "Rank by semantic_score first; later E004 memory-trust policy can decide whether to trust stale memory or re-observe.",
            "Keep target identity and match distance eval-only until after ranking.",
        ],
        "metrics_after_export": [
            "query_bridge_success",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "same-label false-positive count",
            "old-location dead-end cost",
        ],
        "next_recommended_unit": "E005-M30 one-scan ConceptGraphs object candidate export and CLIP-text scoring smoke",
        "smoke_scan_id": smoke_scan_id,
    }


def build_report(coverage: dict[str, Any], gates: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M29 ConceptGraphs Output-To-Query Conversion Plan",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Smoke scan: `{coverage['smoke_scan_id']}`.",
            f"- M28 status: `{coverage['m28_status']}`.",
            f"- Raw ConceptGraphs objects: {coverage['raw_object_count']}.",
            f"- Post ConceptGraphs objects: {coverage['post_object_count']}.",
            f"- Linked E003-M60 query rows for smoke scan: {coverage['linked_query_rows']}.",
            f"- Linked labels: {', '.join(coverage['linked_labels']) if coverage['linked_labels'] else 'none'}.",
            "",
            "## Agent Inference",
            "",
            "- The object-map geometry path is ready because `pcd_np` and `bbox_np` are present.",
            "- The open-vocabulary ranking path still needs a CLIP text scoring smoke because the current run uses the class-set-none path.",
            "- M29 is a conversion contract, not a performance result.",
            "",
            "## Gates",
            "",
            f"- Map candidate export ready: {str(gates['map_candidate_export_ready']).lower()}.",
            f"- Query join ready: {str(gates['query_join_ready']).lower()}.",
            f"- Open-vocabulary semantic score ready: {str(gates['open_vocab_semantic_score_ready']).lower()}.",
            f"- Query-level baseline result ready: {str(gates['query_level_baseline_result_ready']).lower()}.",
            "",
            "## Next",
            "",
            "- E005-M30 should export one-scan ConceptGraphs object candidates and test CLIP-text similarity for the linked `pillow` query without using target identity before ranking.",
            "",
        ]
    )


def main() -> int:
    m28_coverage = read_json(M28_DIR / "coverage.json")
    schema = read_json(M28_DIR / "schema_summary.json")
    query_rows = read_jsonl(M60_DIR / "query_bridge_rows.jsonl")

    smoke_scan_id = infer_smoke_scan_id(m28_coverage)
    post_fields = object_fields(schema, "full_pcd_post")
    required_geometry = {"pcd_np", "bbox_np"}
    required_trace = {"conf", "num_detections", "n_points"}
    class_set_none_variant = "gsa_detections_none" in str(m28_coverage.get("inventory", {}).get("sample_gsa_detection", ""))
    join_rows = build_query_join_rows(query_rows, smoke_scan_id)
    gates = {
        "m28_ready": m28_coverage.get("status") == "e005_m28_conceptgraphs_output_schema_ready",
        "map_candidate_export_ready": required_geometry.issubset(post_fields) and required_trace.issubset(post_fields),
        "query_join_ready": bool(join_rows),
        "open_vocab_semantic_score_ready": False,
        "query_level_baseline_result_ready": False,
        "needs_docker_or_numpy_env_for_pickle": True,
        "needs_clip_text_encoder_smoke": True,
    }
    status = (
        "e005_m29_conceptgraphs_output_to_query_conversion_plan_ready_with_clip_text_gate"
        if gates["m28_ready"] and gates["map_candidate_export_ready"] and gates["query_join_ready"]
        else "e005_m29_conceptgraphs_output_to_query_conversion_plan_blocked"
    )
    m27_launch = read_json(M27_DIR / "coverage.json")
    m27_verify = read_json(M27_DIR / "verification" / "coverage.json")
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m27_launch_status": m27_launch.get("status"),
        "m27_verification_status": m27_verify.get("status"),
        "m28_status": m28_coverage.get("status"),
        "smoke_scan_id": smoke_scan_id,
        "raw_object_count": object_count(schema, "full_pcd"),
        "post_object_count": object_count(schema, "full_pcd_post"),
        "gsa_detection_count": m28_coverage.get("inventory", {}).get("gsa_detection_count", 0),
        "linked_query_rows": len(join_rows),
        "linked_labels": sorted({str(row.get("label_canonical")) for row in join_rows if row.get("label_canonical")}),
        "class_set_none_variant": class_set_none_variant,
        "next_recommended_unit": "E005-M30 one-scan ConceptGraphs object candidate export and CLIP-text scoring smoke"
        if status.endswith("clip_text_gate")
        else "Repair E005-M28 schema / query join before conversion",
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "readiness_gates.json", gates)
    write_json(OUT_DIR / "candidate_schema.json", build_candidate_schema(post_fields))
    write_json(OUT_DIR / "conversion_contract.json", build_conversion_contract(smoke_scan_id, class_set_none_variant))
    write_jsonl(OUT_DIR / "query_join_rows.jsonl", join_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, gates))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
