#!/usr/bin/env python3
"""Select the E003-M16 Dockerized real-proposal route."""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_QUERY_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_PAIR_MANIFEST_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M01_pair_manifest_v0"
)
DEFAULT_M15_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M15_controlled_perception_claim_summary_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M16_real_proposal_route_decision_v0"
ANALYSIS_VERSION = "e003_m16_real_proposal_route_decision_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return dict(grouped)


def load_scan_ids_from_3dssg(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = load_json(path)
    return {str(row["scan"]) for row in payload.get("scans", []) if "scan" in row}


def zip_sequence_stats(sequence_zip: Path) -> dict[str, Any]:
    if not sequence_zip.exists():
        return {
            "sequence_zip_valid": False,
            "sequence_zip_error": None,
            "zip_entries": 0,
            "color_frames": 0,
            "depth_frames": 0,
            "pose_frames": 0,
            "frame_triplet_lower_bound": 0,
            "has_info": False,
        }
    try:
        with zipfile.ZipFile(sequence_zip) as zf:
            names = zf.namelist()
    except Exception as exc:  # pragma: no cover - artifact audit path
        return {
            "sequence_zip_valid": False,
            "sequence_zip_error": str(exc),
            "zip_entries": 0,
            "color_frames": 0,
            "depth_frames": 0,
            "pose_frames": 0,
            "frame_triplet_lower_bound": 0,
            "has_info": False,
        }
    color_frames = sum(1 for name in names if name.endswith(".color.jpg"))
    depth_frames = sum(1 for name in names if name.endswith(".depth.pgm") or name.endswith(".depth.png"))
    pose_frames = sum(1 for name in names if name.endswith(".pose.txt"))
    return {
        "sequence_zip_valid": True,
        "sequence_zip_error": None,
        "zip_entries": len(names),
        "color_frames": color_frames,
        "depth_frames": depth_frames,
        "pose_frames": pose_frames,
        "frame_triplet_lower_bound": min(color_frames, depth_frames, pose_frames),
        "has_info": "_info.txt" in names,
    }


def discover_scan_payloads(dataset_root: Path) -> dict[str, dict[str, Any]]:
    scans_dir = dataset_root / "3RScan" / "scans"
    object_scans = load_scan_ids_from_3dssg(dataset_root / "3DSSG" / "objects.json")
    relationship_scans = load_scan_ids_from_3dssg(dataset_root / "3DSSG" / "relationships.json")
    output: dict[str, dict[str, Any]] = {}
    if not scans_dir.exists():
        return output
    for scan_dir in sorted(path for path in scans_dir.iterdir() if path.is_dir()):
        sequence_zip = scan_dir / "sequence.zip"
        sequence_dir = scan_dir / "sequence"
        semantic_triplet = all(
            (scan_dir / filename).exists()
            for filename in [
                "labels.instances.annotated.v2.ply",
                "semseg.v2.json",
                "mesh.refined.0.010000.segs.v2.json",
            ]
        )
        zip_stats = zip_sequence_stats(sequence_zip)
        sequence_ready = (
            zip_stats["sequence_zip_valid"]
            and zip_stats["frame_triplet_lower_bound"] > 0
            and zip_stats["has_info"]
        ) or sequence_dir.exists()
        output[scan_dir.name] = {
            "analysis_version": ANALYSIS_VERSION,
            "scan_id": scan_dir.name,
            "scan_dir": str(scan_dir),
            "semantic_triplet_ready": semantic_triplet,
            "ply_ready": (scan_dir / "labels.instances.annotated.v2.ply").exists(),
            "semseg_ready": (scan_dir / "semseg.v2.json").exists(),
            "segs_ready": (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists(),
            "sequence_zip_ready": sequence_zip.exists(),
            "sequence_dir_ready": sequence_dir.exists(),
            "sequence_ready": sequence_ready,
            "sequence_zip_path": str(sequence_zip) if sequence_zip.exists() else None,
            "objects_3dssg_ready": scan_dir.name in object_scans,
            "relationships_3dssg_ready": scan_dir.name in relationship_scans,
            "proposal_alignment_scan_ready": sequence_ready
            and semantic_triplet
            and scan_dir.name in object_scans,
            **zip_stats,
        }
    return output


def build_query_alignment_rows(
    query_rows: list[dict[str, Any]],
    scan_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in query_rows:
        ref_payload = scan_payloads.get(row["reference_scan_id"], {})
        rescan_payload = scan_payloads.get(row["rescan_id"], {})
        current_rgbd_ready = bool(rescan_payload.get("proposal_alignment_scan_ready"))
        current_sequence_ready = bool(rescan_payload.get("sequence_ready"))
        reference_sequence_ready = bool(ref_payload.get("sequence_ready"))
        blockers = []
        if not current_sequence_ready:
            blockers.append("current_rescan_sequence_missing")
        if not bool(rescan_payload.get("semantic_triplet_ready")):
            blockers.append("current_rescan_semantic_triplet_missing")
        if not bool(rescan_payload.get("objects_3dssg_ready")):
            blockers.append("current_rescan_3dssg_objects_missing")
        if not current_rgbd_ready:
            blockers.append("current_detector_alignment_not_ready")
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "metadata_split": row["metadata_split"],
                "reference_scan_id": row["reference_scan_id"],
                "rescan_id": row["rescan_id"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "object_instance_id_rescan": row["object_instance_id_rescan"],
                "reference_sequence_ready": reference_sequence_ready,
                "current_rescan_sequence_ready": current_sequence_ready,
                "current_rescan_semantic_triplet_ready": bool(
                    rescan_payload.get("semantic_triplet_ready")
                ),
                "current_rescan_3dssg_objects_ready": bool(
                    rescan_payload.get("objects_3dssg_ready")
                ),
                "current_rescan_3dssg_relationships_ready": bool(
                    rescan_payload.get("relationships_3dssg_ready")
                ),
                "current_real_rgbd_proposal_ready": current_rgbd_ready,
                "current_open_vocab_proposal_ready": False,
                "existing_e003_rgbd_ready": bool(row.get("e003_rgbd_ready")),
                "existing_e003_open_vocab_ready": bool(row.get("e003_open_vocab_ready")),
                "current_sequence_frame_triplet_lower_bound": rescan_payload.get(
                    "frame_triplet_lower_bound", 0
                ),
                "blockers": blockers,
                "recommended_action": "stage_sequence_ready_current_rescan"
                if blockers
                else "eligible_for_dockerized_detector",
            }
        )
    return rows


def build_pair_alignment_rows(
    manifest_rows: list[dict[str, Any]],
    query_rows: list[dict[str, Any]],
    scan_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    query_by_pair = group_by(query_rows, "pair_uid")
    rows = []
    for row in manifest_rows:
        pair_queries = query_by_pair.get(row["pair_uid"], [])
        ref_payload = scan_payloads.get(row["reference_scan_id"], {})
        rescan_payload = scan_payloads.get(row["rescan_id"], {})
        current_ready = bool(rescan_payload.get("proposal_alignment_scan_ready"))
        reference_ready = bool(ref_payload.get("proposal_alignment_scan_ready"))
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "pair_uid": row["pair_uid"],
                "metadata_split": row["metadata_split"],
                "eligibility_status": row["eligibility_status"],
                "next_stage": row["next_stage"],
                "reference_scan_id": row["reference_scan_id"],
                "rescan_id": row["rescan_id"],
                "query_rows": len(pair_queries),
                "reference_proposal_alignment_scan_ready": reference_ready,
                "current_rescan_proposal_alignment_scan_ready": current_ready,
                "reference_sequence_ready": bool(ref_payload.get("sequence_ready")),
                "current_rescan_sequence_ready": bool(rescan_payload.get("sequence_ready")),
                "pair_real_current_proposal_ready": len(pair_queries) > 0 and current_ready,
                "pair_reference_sequence_only": len(pair_queries) > 0
                and reference_ready
                and not current_ready,
                "exclusion_reasons": row.get("exclusion_reasons", []),
                "recommended_action": "use_current_e001_denominator"
                if len(pair_queries) > 0 and current_ready
                else "stage_current_rescan_sequence_or_rebuild_denominator",
            }
        )
    return rows


def build_proposal_source_rows(
    query_rows: list[dict[str, Any]],
    query_alignment_rows: list[dict[str, Any]],
    pair_alignment_rows: list[dict[str, Any]],
    scan_gate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_ready_rows = [row for row in query_alignment_rows if row["current_real_rgbd_proposal_ready"]]
    current_ref_seq_rows = [row for row in query_alignment_rows if row["reference_sequence_ready"]]
    sequence_scan_rows = [row for row in scan_gate_rows if row["proposal_alignment_scan_ready"]]
    ready_pair_current_rows = [
        row for row in pair_alignment_rows if row["pair_real_current_proposal_ready"]
    ]
    reference_only_pair_rows = [
        row for row in pair_alignment_rows if row["pair_reference_sequence_only"]
    ]
    return [
        {
            "analysis_version": ANALYSIS_VERSION,
            "proposal_source_id": "current_e001_rescan_rgbd_sequence",
            "source_type": "real_rgbd_frames_for_current_rescan",
            "status": "blocked",
            "query_rows_total": len(query_rows),
            "ready_query_rows": len(current_ready_rows),
            "ready_pair_rows": len(ready_pair_current_rows),
            "main_blocker": "current E001 rescan ids have no sequence.zip/sequence payload",
            "paper_claim_if_ready": "real RGB-D proposal robustness on the existing E001 denominator",
            "next_action": "stage sequence payloads for current E001 rescans or rebuild denominator",
        },
        {
            "analysis_version": ANALYSIS_VERSION,
            "proposal_source_id": "current_e001_reference_sequence_only",
            "source_type": "reference_scan_rgbd_frames",
            "status": "insufficient_for_current_proposals",
            "query_rows_total": len(query_rows),
            "ready_query_rows": len(current_ref_seq_rows),
            "ready_pair_rows": len(reference_only_pair_rows),
            "main_blocker": "reference RGB-D can support memory-side inspection but not current-scene proposal recall",
            "paper_claim_if_ready": "not sufficient for real current-proposal robustness",
            "next_action": "do not use as the main real-proposal denominator",
        },
        {
            "analysis_version": ANALYSIS_VERSION,
            "proposal_source_id": "sequence_ready_scan_bootstrap",
            "source_type": "real_rgbd_frames_from_sequence-ready_3RScan_scans",
            "status": "staging_candidate",
            "sequence_ready_scans": len(sequence_scan_rows),
            "ready_query_rows": 0,
            "main_blocker": "sequence-ready scans are not current rescans in the existing E001 query denominator",
            "paper_claim_if_ready": "real RGB-D/open-vocabulary proposal pilot after rebuilding a compatible query denominator",
            "next_action": "create E003-M17 real-proposal denominator staging from sequence-ready scans and 3DSSG object ids",
        },
        {
            "analysis_version": ANALYSIS_VERSION,
            "proposal_source_id": "annotation_proxy_noise_suite",
            "source_type": "annotation_semseg_proxy",
            "status": "complete_controlled_non_real",
            "query_rows_total": len(query_rows),
            "ready_query_rows": len(query_rows),
            "main_blocker": "not detector output",
            "paper_claim_if_ready": "controlled annotation-proxy robustness only",
            "next_action": "keep as controlled table, not real perception table",
        },
    ]


def build_proposal_output_schema() -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "schema_id": "real_proposal_prediction_jsonl_v0",
        "file_name": "real_proposals.jsonl",
        "one_row_per": "detector proposal before matching and optional matched proposal after matching",
        "required_fields": {
            "proposal_uid": "stable unique id for this proposal row",
            "row_uid": "E001/E003 query row id",
            "pair_uid": "reference->rescan pair id",
            "scan_id": "current rescan id used for RGB-D proposals",
            "frame_ids": "list of RGB-D frame ids that support the proposal",
            "detector_id": "detector or open-vocabulary model id",
            "detector_config_id": "frozen detector config id",
            "prompt_set_id": "text prompt set id for open-vocabulary detector",
            "seed": "detector/postprocessing seed",
            "label_text": "raw detector label",
            "label_canonical": "canonical label mapped to 3DSSG/classes vocabulary when possible",
            "confidence": "detector confidence score",
            "bbox_2d": "optional 2D boxes keyed by frame id",
            "mask_rle": "optional mask encoding keyed by frame id",
            "depth_valid_pixel_count": "valid depth support count",
            "camera_intrinsics_source": "source of intrinsics, usually sequence _info.txt",
            "camera_pose_source": "source pose files used for 3D projection",
            "centroid_world_m": "proposal centroid in scan/world coordinate",
            "point_support_world": "optional sampled world points or path to support points",
            "matched_3dssg_instance_id": "matched 3DSSG object id or null",
            "match_status": "matched, unmatched_false_positive, target_missed, ignored_low_confidence",
            "match_distance_m": "distance to matched 3DSSG object centroid when available",
            "match_iou_3d": "optional 3D IoU when support geometry exists",
        },
        "blocked_fields": [
            "candidate_is_target must not be used by detector or ranking policy",
            "matched_3dssg_instance_id is evaluation-only and must not be used by policy before scoring",
            "object_instance_id_rescan is evaluation-only for proposal recall and matching",
        ],
        "derived_metrics_enabled": [
            "proposal_recall",
            "false_positive_rate",
            "label_mapping_accuracy",
            "centroid_localization_error_m",
            "identity_proxy_SR",
            "localization_proxy_SR",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "stale old-location FP",
        ],
    }


def build_docker_command_plan(out_dir: Path) -> dict[str, Any]:
    staged_input = (
        EXPERIMENT_ROOT
        / "artifacts"
        / "E003-M17_real_proposal_denominator_staging_v0"
    )
    proposal_output = (
        EXPERIMENT_ROOT
        / "artifacts"
        / "E003-M18_dockerized_real_proposals_v0"
    )
    command = [
        "docker",
        "run",
        "--gpus",
        "all",
        "--rm",
        "-v",
        f"{DEFAULT_DATASET_ROOT}:/data:ro",
        "-v",
        f"{staged_input}:/inputs:ro",
        "-v",
        f"{proposal_output}:/outputs",
        "h001-real-proposals:ovdet-v0",
        "python",
        "/workspace/tools/run_rgbd_ov_proposals.py",
        "--manifest",
        "/inputs/real_proposal_query_manifest.jsonl",
        "--schema",
        "/inputs/proposal_output_schema.json",
        "--output",
        "/outputs/real_proposals.jsonl",
        "--detector",
        "open_vocab_rgbd_detector_v0",
        "--prompt-set",
        "/inputs/prompt_set.json",
        "--seed",
        "101",
    ]
    return {
        "analysis_version": ANALYSIS_VERSION,
        "plan_id": "dockerized_real_proposal_command_plan_v0",
        "status": "planned_not_executable_until_E003_M17_staging",
        "docker_image_tag": "h001-real-proposals:ovdet-v0",
        "dockerfile_required": True,
        "dockerfile_planned_path": "experiments/E003_perception_noise_expansion/docker/real_proposals/Dockerfile",
        "mounted_dataset_path": str(DEFAULT_DATASET_ROOT),
        "staged_input_dir": str(staged_input),
        "proposal_output_dir": str(proposal_output),
        "command": command,
        "command_string": " ".join(command),
        "required_inputs_before_execution": [
            "real_proposal_query_manifest.jsonl with current rescan sequence-ready rows",
            "proposal_output_schema.json copied from E003-M16",
            "prompt_set.json with object labels and open-vocabulary aliases",
            "Dockerfile or published image tag",
            "proposal-to-3DSSG matching script or evaluation command",
        ],
        "paper_table_command_ready": False,
        "reason_not_ready": "current E001 denominator has 0 current-rescan RGB-D proposal-ready rows",
        "output_schema_source": str(out_dir / "proposal_output_schema.json"),
    }


def build_route_decision(
    proposal_source_rows: list[dict[str, Any]],
    query_alignment_rows: list[dict[str, Any]],
    scan_gate_rows: list[dict[str, Any]],
    docker_plan: dict[str, Any],
    promotion_gate: dict[str, Any],
) -> dict[str, Any]:
    current_ready_rows = sum(1 for row in query_alignment_rows if row["current_real_rgbd_proposal_ready"])
    sequence_ready_scans = sum(1 for row in scan_gate_rows if row["proposal_alignment_scan_ready"])
    if current_ready_rows > 0:
        status = "dockerized_detector_ready_for_current_denominator"
        selected_route = "current_e001_rescan_rgbd_sequence"
        next_action = "E003-M17 dockerized detector smoke run"
    elif sequence_ready_scans > 0:
        status = "real_proposal_denominator_staging_required"
        selected_route = "sequence_ready_scan_bootstrap"
        next_action = "E003-M17 real-proposal denominator staging"
    else:
        status = "blocked_no_sequence_ready_source"
        selected_route = "blocked"
        next_action = "stage 3RScan sequence payloads"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "selected_route": selected_route,
        "next_action": next_action,
        "current_e001_query_rows": len(query_alignment_rows),
        "current_e001_real_rgbd_ready_rows": current_ready_rows,
        "sequence_ready_alignment_scans": sequence_ready_scans,
        "controlled_claim_ready": promotion_gate.get("controlled_claim_ready"),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "real_navigation_claim_ready": False,
        "proposal_sources": {
            row["proposal_source_id"]: {
                "status": row["status"],
                "next_action": row["next_action"],
            }
            for row in proposal_source_rows
        },
        "docker_command_plan_status": docker_plan["status"],
        "decision_reason": (
            "The existing E001 query denominator has no current-rescan sequence-ready rows, "
            "but local sequence-ready scans exist. The next useful step is to stage a "
            "real-proposal denominator before running a Dockerized detector."
        ),
        "non_claims": [
            "real RGB-D perception robustness is still not supported",
            "open-vocabulary detector robustness is still not supported",
            "real navigation SR/SPL is still not supported",
            "deployable search policy is still not supported",
        ],
    }


def build_coverage(
    out_dir: Path,
    scan_gate_rows: list[dict[str, Any]],
    query_alignment_rows: list[dict[str, Any]],
    pair_alignment_rows: list[dict[str, Any]],
    proposal_source_rows: list[dict[str, Any]],
    route_decision: dict[str, Any],
) -> dict[str, Any]:
    query_real_ready = sum(1 for row in query_alignment_rows if row["current_real_rgbd_proposal_ready"])
    query_reference_seq = sum(1 for row in query_alignment_rows if row["reference_sequence_ready"])
    query_current_seq = sum(1 for row in query_alignment_rows if row["current_rescan_sequence_ready"])
    sequence_scan_ready = sum(1 for row in scan_gate_rows if row["sequence_ready"])
    alignment_scan_ready = sum(1 for row in scan_gate_rows if row["proposal_alignment_scan_ready"])
    current_pair_ready = sum(1 for row in pair_alignment_rows if row["pair_real_current_proposal_ready"])
    status = route_decision["status"]
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "scan_gate_rows": len(scan_gate_rows),
        "sequence_ready_scans": sequence_scan_ready,
        "proposal_alignment_scan_ready": alignment_scan_ready,
        "query_alignment_rows": len(query_alignment_rows),
        "query_rows_reference_sequence_ready": query_reference_seq,
        "query_rows_current_rescan_sequence_ready": query_current_seq,
        "query_rows_current_real_rgbd_proposal_ready": query_real_ready,
        "pair_alignment_rows": len(pair_alignment_rows),
        "pair_rows_current_real_proposal_ready": current_pair_ready,
        "proposal_source_rows": len(proposal_source_rows),
        "docker_required_for_future_detector": True,
        "docker_required_for_m16": False,
        "docker_reason": "E003-M16 is a repository-local route decision and schema plan; future real detector execution must use Docker.",
        "selected_route": route_decision["selected_route"],
        "next_recommended_unit": route_decision["next_action"],
        "outputs": {
            "proposal_source_rows": str(out_dir / "proposal_source_rows.jsonl"),
            "scan_alignment_gate_rows": str(out_dir / "scan_alignment_gate_rows.jsonl"),
            "query_alignment_gate_rows": str(out_dir / "query_alignment_gate_rows.jsonl"),
            "pair_alignment_gate_rows": str(out_dir / "pair_alignment_gate_rows.jsonl"),
            "proposal_output_schema": str(out_dir / "proposal_output_schema.json"),
            "docker_command_plan": str(out_dir / "docker_command_plan.json"),
            "route_decision": str(out_dir / "route_decision.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    out_dir: Path,
    coverage: dict[str, Any],
    proposal_source_rows: list[dict[str, Any]],
    route_decision: dict[str, Any],
    docker_plan: dict[str, Any],
) -> str:
    lines = [
        "# E003-M16 Real Proposal Route Decision",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Scan gate rows: {coverage['scan_gate_rows']}",
        f"- Sequence-ready scans: {coverage['sequence_ready_scans']}",
        f"- Proposal-alignment-ready scans: {coverage['proposal_alignment_scan_ready']}",
        f"- Query alignment rows: {coverage['query_alignment_rows']}",
        f"- Query rows with reference sequence ready: {coverage['query_rows_reference_sequence_ready']}",
        f"- Query rows with current rescan sequence ready: {coverage['query_rows_current_rescan_sequence_ready']}",
        f"- Query rows with current real RGB-D proposal ready: {coverage['query_rows_current_real_rgbd_proposal_ready']}",
        f"- Pair rows with current real proposal ready: {coverage['pair_rows_current_real_proposal_ready']}",
        f"- Selected route: `{route_decision['selected_route']}`",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`",
        f"- M16 Docker required: {coverage['docker_required_for_m16']}",
        f"- Future detector Docker required: {coverage['docker_required_for_future_detector']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Proposal Source Decision",
        "",
        "| Source | Status | Ready rows/scans | Next action |",
        "| --- | --- | ---: | --- |",
    ]
    for row in proposal_source_rows:
        if row["proposal_source_id"] == "sequence_ready_scan_bootstrap":
            ready = row.get("sequence_ready_scans", 0)
        else:
            ready = row.get("ready_query_rows", 0)
        lines.append(
            f"| `{row['proposal_source_id']}` | `{row['status']}` | {ready} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Docker Command Plan",
            "",
            f"- Status: `{docker_plan['status']}`",
            f"- Docker image tag: `{docker_plan['docker_image_tag']}`",
            f"- Dockerfile planned path: `{docker_plan['dockerfile_planned_path']}`",
            f"- Paper-table command ready: {docker_plan['paper_table_command_ready']}",
            f"- Reason not ready: {docker_plan['reason_not_ready']}",
            "",
            "Planned command:",
            "",
            "```bash",
            docker_plan["command_string"],
            "```",
            "",
            "## 논문 주장",
            "",
            "- E003-M16 supports saying that the controlled E003 table is ready, but real proposal evaluation is not yet ready.",
            "- E003-M16 supports selecting `sequence_ready_scan_bootstrap` as the next staging route because current E001 rescans have 0 sequence-ready rows.",
            "- E003-M16 supports a concrete proposal output schema and Docker command plan for later real detector execution.",
            "- E003-M16 does not support real RGB-D/open-vocabulary robustness results yet.",
            "",
            "## 에이전트 추론",
            "",
            "- The current E001 denominator cannot be upgraded to real current-scene proposals without staging current rescan RGB-D frames.",
            "- Reference scan sequences are useful for inspection, but current object proposal recall must be measured on the rescan/current scene.",
            "- The most direct top-tier strengthening path is E003-M17 denominator staging followed by a Dockerized detector smoke run.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for route decision. Next is `E003-M17 real-proposal denominator staging` unless redirected to E004 task-context memory trust.",
            "",
            "## Outputs",
            "",
            "- `proposal_source_rows.jsonl`",
            "- `scan_alignment_gate_rows.jsonl`",
            "- `query_alignment_gate_rows.jsonl`",
            "- `pair_alignment_gate_rows.jsonl`",
            "- `proposal_output_schema.json`",
            "- `docker_command_plan.json`",
            "- `route_decision.json`",
            "- `coverage.json`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--query-dir", type=Path, default=DEFAULT_QUERY_DIR)
    parser.add_argument("--pair-manifest-dir", type=Path, default=DEFAULT_PAIR_MANIFEST_DIR)
    parser.add_argument("--m15-dir", type=Path, default=DEFAULT_M15_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    query_rows = load_jsonl(args.query_dir / "query_rows.jsonl")
    manifest_rows = load_jsonl(args.pair_manifest_dir / "manifest.jsonl")
    promotion_gate = load_json(args.m15_dir / "promotion_gate.json")

    scan_payloads = discover_scan_payloads(args.dataset_root)
    scan_gate_rows = list(scan_payloads.values())
    query_alignment_rows = build_query_alignment_rows(query_rows, scan_payloads)
    pair_alignment_rows = build_pair_alignment_rows(manifest_rows, query_rows, scan_payloads)
    proposal_source_rows = build_proposal_source_rows(
        query_rows,
        query_alignment_rows,
        pair_alignment_rows,
        scan_gate_rows,
    )
    proposal_schema = build_proposal_output_schema()
    docker_plan = build_docker_command_plan(args.out_dir)
    route_decision = build_route_decision(
        proposal_source_rows,
        query_alignment_rows,
        scan_gate_rows,
        docker_plan,
        promotion_gate,
    )
    coverage = build_coverage(
        args.out_dir,
        scan_gate_rows,
        query_alignment_rows,
        pair_alignment_rows,
        proposal_source_rows,
        route_decision,
    )
    report = build_report(
        args.out_dir,
        coverage,
        proposal_source_rows,
        route_decision,
        docker_plan,
    )

    write_jsonl(args.out_dir / "proposal_source_rows.jsonl", proposal_source_rows)
    write_jsonl(args.out_dir / "scan_alignment_gate_rows.jsonl", scan_gate_rows)
    write_jsonl(args.out_dir / "query_alignment_gate_rows.jsonl", query_alignment_rows)
    write_jsonl(args.out_dir / "pair_alignment_gate_rows.jsonl", pair_alignment_rows)
    write_json(args.out_dir / "proposal_output_schema.json", proposal_schema)
    write_json(args.out_dir / "docker_command_plan.json", docker_plan)
    write_json(args.out_dir / "route_decision.json", route_decision)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": coverage["status"], "out_dir": str(args.out_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
