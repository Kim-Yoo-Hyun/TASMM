#!/usr/bin/env python3
"""Plan Open3DSG query-level conversion before object-candidate rows are ready."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M60_query_conversion_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_contract_v0"
M58_LOCAL_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0"
M59_LOCAL_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M59_object_candidate_export_smoke_v0"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M52_DIR = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0"
M56_DIR = EXP_ROOT / "artifacts" / "E005-M56_robustness_denominator_open3dsg_audit_v0"
VERSION = "e005_m60_open3dsg_query_conversion_contract_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl_count(path: Path, sample_limit: int = 3) -> tuple[int, list[dict[str, Any]], list[str]]:
    if not path.exists():
        return 0, [], []
    count = 0
    samples: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            if len(samples) >= sample_limit:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    samples.append(row)
                else:
                    errors.append(f"line {line_no}: row is not an object")
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: JSONDecodeError {exc}")
    return count, samples, errors


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def query_file_counts() -> dict[str, Any]:
    batches = ["heldout_b01", "heldout_b02", "heldout_b03"]
    rows: dict[str, Any] = {}
    total = 0
    errors: list[str] = []
    sample_keys: dict[str, list[str]] = {}
    for batch in batches:
        path = M45_CONTRACT_DIR / f"{batch}_query_rows.jsonl"
        count, samples, parse_errors = read_jsonl_count(path)
        rows[batch] = {
            "path": str(path),
            "exists": path.exists(),
            "rows": count,
            "sample_query_uid": samples[0].get("bridge_query_uid") if samples else None,
        }
        total += count
        errors.extend([f"{batch}:{error}" for error in parse_errors])
        if samples:
            sample_keys[batch] = sorted(samples[0].keys())
    return {
        "query_batches": rows,
        "total_query_rows": total,
        "expected_total_query_rows": 195,
        "parse_errors": errors,
        "sample_keys_by_batch": sample_keys,
    }


def input_inventory() -> dict[str, Any]:
    object_schema = read_json(M58_LOCAL_DIR / "object_candidate_schema.json")
    query_schema = read_json(M58_LOCAL_DIR / "query_candidate_schema.json")
    object_rows_path = M59_LOCAL_DIR / "open3dsg_object_candidates.jsonl"
    m59_manifest_path = M59_LOCAL_DIR / "open3dsg_object_candidates.manifest.json"
    m59_completed_path = M59_LOCAL_DIR / "open3dsg_object_candidates.completed.jsonl"
    m59_count, m59_samples, m59_parse_errors = read_jsonl_count(object_rows_path)
    m52_metrics = read_json(M52_DIR / "metrics.json")
    m56_denominator = read_json(M56_DIR / "robustness_denominator_contract.json")
    return {
        "m58_local_dir": str(M58_LOCAL_DIR),
        "m59_local_dir": str(M59_LOCAL_DIR),
        "m58_object_schema_id": object_schema.get("schema_id"),
        "m58_query_schema_id": query_schema.get("schema_id"),
        "m58_object_required_fields": object_schema.get("required_fields", []),
        "m58_query_required_fields": query_schema.get("required_fields", []),
        "m59_object_rows": {
            "path": str(object_rows_path),
            "exists": object_rows_path.exists(),
            "rows": m59_count,
            "sample_count": len(m59_samples),
            "parse_errors": m59_parse_errors,
            "manifest_exists": m59_manifest_path.exists(),
            "completed_marker_exists": m59_completed_path.exists(),
        },
        "m45_query_denominator": query_file_counts(),
        "m45_target_rows": {
            "path": str(M45_METRIC_DIR / "target_rows.jsonl"),
            "exists": (M45_METRIC_DIR / "target_rows.jsonl").exists(),
            "rows": read_jsonl_count(M45_METRIC_DIR / "target_rows.jsonl")[0],
        },
        "m52_h001_reference_metrics": {
            "path": str(M52_DIR / "metrics.json"),
            "exists": (M52_DIR / "metrics.json").exists(),
            "comparison_policies": m52_metrics.get("comparison_policies", []),
            "h001_success_rows": (
                m52_metrics.get("policy_metrics", {})
                .get("task_context_memory_trust_reobserve_v0", {})
                .get("query_bridge_success_rows")
            ),
            "conceptgraphs_success_rows": (
                m52_metrics.get("policy_metrics", {})
                .get("conceptgraphs_clip_rank_bbox_strict_top5_v0", {})
                .get("query_bridge_success_rows")
            ),
        },
        "m56_table_c_status": {
            "path": str(M56_DIR / "robustness_denominator_contract.json"),
            "exists": (M56_DIR / "robustness_denominator_contract.json").exists(),
            "open3dsg_table_status": next(
                (
                    table.get("status")
                    for table in m56_denominator.get("tables", [])
                    if table.get("table_id") == "C_open3dsg_scene_graph_route_v0"
                ),
                None,
            ),
        },
    }


def build_contract(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": "open3dsg_query_level_conversion_contract_v0",
        "version": VERSION,
        "purpose": "Convert Open3DSG object-candidate rows into the same H001 heldout query-level policy table used for ConceptGraphs and H001 replay.",
        "source_status": "waiting_for_m59_object_candidate_rows",
        "source_policy": {
            "open3dsg_staged_root": "/home/yoohyun/research/local_dataset/Open3DSG_staged",
            "open3dsg_staged_mode": "read_only",
            "derived_output_root": str(LOCAL_DATA_DIR),
            "do_not_write_to": "/home/yoohyun/research/local_dataset/Open3DSG_staged",
        },
        "input_tables": {
            "object_candidates": {
                "schema_id": "open3dsg_object_candidate_jsonl_v0",
                "path": str(M59_LOCAL_DIR / "open3dsg_object_candidates.jsonl"),
                "required_before_execution": True,
                "current_rows": inventory["m59_object_rows"]["rows"],
                "required_fields": inventory["m58_object_required_fields"],
            },
            "query_denominator": {
                "source": "E005-M45 heldout query rows generated from M38",
                "paths": [
                    str(M45_CONTRACT_DIR / "heldout_b01_query_rows.jsonl"),
                    str(M45_CONTRACT_DIR / "heldout_b02_query_rows.jsonl"),
                    str(M45_CONTRACT_DIR / "heldout_b03_query_rows.jsonl"),
                ],
                "expected_rows": 195,
                "current_rows": inventory["m45_query_denominator"]["total_query_rows"],
                "required_fields": [
                    "bridge_query_uid",
                    "row_uid",
                    "current_rescan_id",
                    "label_canonical",
                    "target_uid",
                    "object_instance_id_rescan",
                    "task_context_id",
                    "row_band",
                    "expected_memory_state",
                    "old_memory_is_stale",
                    "old_location_dead_end_expected",
                ],
            },
            "target_geometry": {
                "preferred_source": str(M45_METRIC_DIR / "target_rows.jsonl"),
                "fallback_source": "/home/yoohyun/research2/local_dataset/3RScan/scans/<scan_id>/semseg.v2.json",
                "required_fields": [
                    "target_uid",
                    "scan_id",
                    "object_instance_id",
                    "centroid_world_m",
                    "label_canonical",
                ],
            },
        },
        "label_normalization": {
            "policy": "exact_canonical_after_light_normalization",
            "normalization_steps": [
                "lowercase",
                "strip leading/trailing whitespace",
                "replace underscores and hyphens with spaces",
                "collapse repeated spaces",
            ],
            "no_synonym_expansion_in_smoke": True,
            "why": "Avoid hidden semantic expansion before Open3DSG baseline quality is measured.",
        },
        "join_rule": [
            "For each query row, select object-candidate rows where scan_id equals current_rescan_id.",
            "Normalize candidate_label and query label_canonical with the same light canonicalizer.",
            "Keep rows whose normalized candidate_label equals normalized label_canonical.",
            "Group by candidate object_id; if multiple rows remain for the same object, keep the highest candidate_score and best candidate_rank.",
            "Rank candidate objects by candidate_score descending, then candidate_rank ascending, then object_id ascending.",
            "Do not use target_uid, object_instance_id_rescan, gt_object_label, id2name_label, or candidate_is_target before ranking.",
        ],
        "output_schemas": {
            "open3dsg_query_candidate_rows.jsonl": {
                "record_type": "open3dsg_query_candidate",
                "required_fields": [
                    "query_uid",
                    "query_label",
                    "target_uid",
                    "scan_id",
                    "candidate_object_id",
                    "candidate_uid",
                    "candidate_label",
                    "candidate_score",
                    "candidate_rank",
                    "rank",
                    "policy_allowed_input",
                    "source_object_candidate_record_id",
                ],
            },
            "open3dsg_candidate_eval_rows.jsonl": {
                "record_type": "open3dsg_candidate_eval",
                "required_fields": [
                    "query_uid",
                    "target_uid",
                    "candidate_uid",
                    "rank",
                    "eval_center_distance_m",
                    "eval_bbox_distance_m",
                    "eval_center_success_strict",
                    "eval_bbox_success_strict",
                    "eval_bbox_success_relaxed_1m",
                ],
            },
            "open3dsg_policy_rows.jsonl": {
                "record_type": "open3dsg_policy_result",
                "required_fields": [
                    "query_uid",
                    "target_uid",
                    "policy",
                    "candidate_count",
                    "returned_location_count",
                    "target_detected",
                    "target_rank",
                    "query_bridge_success",
                    "expected_search_cost",
                    "attempt_spl_proxy",
                    "real_navigation_sr_spl_ready",
                ],
            },
        },
        "policies": [
            {
                "policy": "open3dsg_objects_probs_bbox_strict_top5_v0",
                "rank_source": "candidate_score",
                "distance_field": "eval_bbox_distance_m",
                "threshold_m": 0.5,
                "budget": 5,
            },
            {
                "policy": "open3dsg_objects_probs_bbox_relaxed_1m_top3_v0",
                "rank_source": "candidate_score",
                "distance_field": "eval_bbox_distance_m",
                "threshold_m": 1.0,
                "budget": 3,
            },
            {
                "policy": "open3dsg_objects_probs_center_strict_top5_v0",
                "rank_source": "candidate_score",
                "distance_field": "eval_center_distance_m",
                "threshold_m": 0.5,
                "budget": 5,
            },
        ],
        "metrics": [
            "target_detected_rate",
            "query_bridge_success_rate",
            "mean_target_rank_if_detected",
            "ExpectedSearchCost",
            "AttemptSPL_proxy",
            "old_location_dead_end_avoided_rate",
            "failure_class_counts",
        ],
        "failure_classes": [
            "m59_object_candidates_missing",
            "no_same_label_candidates",
            "target_object_not_in_open3dsg_candidates",
            "target_present_but_rank_gt_budget",
            "geometry_join_missing",
            "strict_threshold_miss_relaxed_hit",
            "strict_hit",
        ],
        "claim_boundary": {
            "allowed_after_contract_only": "Open3DSG query-level conversion path is specified but not executed.",
            "allowed_after_m60_rows_pass": "Open3DSG can be reported as a second external map/scene-graph baseline on the M38 proxy-search denominator.",
            "still_forbidden": [
                "final real RGB-D/open-vocabulary robustness",
                "deployable navigation policy",
                "real navigation SR/SPL",
                "Open3DSG superiority or inferiority before rows are exported and converted",
            ],
        },
    }


def build_execution_contract() -> dict[str, Any]:
    return {
        "contract_id": "open3dsg_query_conversion_execution_contract_v0",
        "future_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            "run_m60_open3dsg_query_conversion.py --require-m59-ready"
        ),
        "future_verification_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            "verify_m60_open3dsg_query_conversion_contract.py --require-m59-rows"
        ),
        "expected_output_dir": str(LOCAL_DATA_DIR),
        "expected_output_files_after_execution": [
            "open3dsg_query_candidate_rows.jsonl",
            "open3dsg_candidate_eval_rows.jsonl",
            "open3dsg_policy_rows.jsonl",
            "metrics.json",
            "coverage.json",
            "report.md",
        ],
        "execution_blocker": "M59 object-candidate rows are required before conversion can run.",
    }


def status_from_inventory(inventory: dict[str, Any]) -> tuple[str, list[str]]:
    errors: list[str] = []
    if inventory["m58_object_schema_id"] != "open3dsg_object_candidate_jsonl_v0":
        errors.append("m58_object_schema_missing_or_unexpected")
    if inventory["m58_query_schema_id"] != "open3dsg_query_candidate_jsonl_v0":
        errors.append("m58_query_schema_missing_or_unexpected")
    if inventory["m45_query_denominator"]["total_query_rows"] != 195:
        errors.append(f"m45_query_denominator_unexpected:{inventory['m45_query_denominator']['total_query_rows']}")
    if inventory["m45_query_denominator"]["parse_errors"]:
        errors.append("m45_query_denominator_parse_errors")
    if inventory["m59_object_rows"]["parse_errors"]:
        errors.append("m59_object_candidate_parse_errors")
    if errors:
        return "e005_m60_open3dsg_query_conversion_contract_blocked", errors
    if inventory["m59_object_rows"]["rows"] > 0:
        return "e005_m60_open3dsg_query_conversion_contract_ready_for_conversion_smoke", errors
    return "e005_m60_open3dsg_query_conversion_contract_ready_waiting_m59_rows", errors


def build_report(coverage: dict[str, Any], contract: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M60 Open3DSG Query Conversion Contract",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- M58 object schema: `{coverage['m58_object_schema_id']}`.",
            f"- M58 query schema: `{coverage['m58_query_schema_id']}`.",
            f"- M38/M45 denominator rows: {coverage['m45_query_rows']} / 195.",
            f"- M59 object candidate rows: {coverage['m59_object_candidate_rows']}.",
            f"- Output root: `{coverage['local_data_dir']}`.",
            "- Source policy: `/home/yoohyun/research/local_dataset/Open3DSG_staged` remains read-only.",
            "",
            "## Contract",
            "",
            "- Join `Open3DSG` object candidates to M38 heldout queries by `scan_id == current_rescan_id` and normalized `candidate_label == label_canonical`.",
            "- Rank only by `Open3DSG` prediction score, with stable tie-breaks by candidate rank and object id.",
            "- Use target id and target geometry only after ranking for evaluation.",
            "- Report strict bbox top5, relaxed bbox 1m top3, strict center top5, `ExpectedSearchCost`, and `AttemptSPL` proxy.",
            "",
            "## Claim Boundary",
            "",
            f"- Contract-only claim: {contract['claim_boundary']['allowed_after_contract_only']}",
            f"- After rows pass: {contract['claim_boundary']['allowed_after_m60_rows_pass']}",
            "- Still forbidden: final real RGB-D/open-vocabulary robustness, deployable navigation, and real navigation `SR` / `SPL`.",
            "",
            "## Next",
            "",
            "- Relaunch E005-M59 with the lower-memory object-only patch.",
            "- If M59 writes candidate rows, implement/run the M60 conversion script using this contract.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    inventory = input_inventory()
    status, errors = status_from_inventory(inventory)
    contract = build_contract(inventory)
    execution_contract = build_execution_contract()
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "m58_object_schema_id": inventory["m58_object_schema_id"],
        "m58_query_schema_id": inventory["m58_query_schema_id"],
        "m45_query_rows": inventory["m45_query_denominator"]["total_query_rows"],
        "m59_object_candidate_rows": inventory["m59_object_rows"]["rows"],
        "errors": errors,
        "source_modified": False,
        "query_level_performance_claim_ready": inventory["m59_object_rows"]["rows"] > 0 and not errors,
        "next_recommended_unit": (
            "E005-M59 relaunch"
            if inventory["m59_object_rows"]["rows"] == 0
            else "E005-M60 conversion smoke implementation/run"
        ),
    }
    write_json(LOCAL_DATA_DIR / "input_inventory.json", inventory)
    write_json(LOCAL_DATA_DIR / "query_conversion_contract.json", contract)
    write_json(LOCAL_DATA_DIR / "execution_contract.json", execution_contract)
    write_json(LOCAL_DATA_DIR / "coverage.json", coverage)
    write_text(LOCAL_DATA_DIR / "report.md", build_report(coverage, contract))
    write_json(
        ARTIFACT_DIR / "artifact_pointer.json",
        {
            "status": status,
            "version": VERSION,
            "local_data_dir": str(LOCAL_DATA_DIR),
            "primary_contract": str(LOCAL_DATA_DIR / "query_conversion_contract.json"),
            "coverage": str(LOCAL_DATA_DIR / "coverage.json"),
        },
    )
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, contract))
    return coverage


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
