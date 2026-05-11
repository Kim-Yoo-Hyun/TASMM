#!/usr/bin/env python3
"""Plan the E003-M58 direct current-rescan detector/evaluation bridge."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_M54_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M54_search_critical_bbox_failure_boundary_v0"
DEFAULT_M55_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M55_dynamic_pair_bridge_gate_v0"
DEFAULT_M56_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M56_current_rescan_sequence_staging_plan_v0"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M58_direct_current_rescan_bridge_design_v0"
M58_VERSION = "e003_m58_direct_current_rescan_bridge_design_v0"
PROMPT_SET_ID = "e003_m58_direct_current_rescan_bridge_prompts_v0"
DETECTOR_PROFILE_ID = "open_vocab_rgbd_detector_v0"
DETECTOR_CONFIG_ID = "h001_direct_current_rescan_groundingdino_tiny_rgbd_backproject_v0"
MAX_FRAMES_PER_SCAN = 24
STRUCTURAL_CONTEXT_LABELS = {
    "ceiling",
    "doorframe",
    "floor",
    "floor /other room",
    "shower wall",
    "wall",
    "wall /other room",
    "window",
}
GENERIC_CONTEXT_LABELS = {
    "clutter",
    "item",
    "kitchen object",
    "object",
    "objects",
}
ALIAS_MAP = {
    "bath cabinet": ["bathroom cabinet"],
    "commode": ["toilet"],
    "couch": ["sofa"],
    "couch table": ["coffee table"],
    "laundry basket": ["clothes basket"],
    "pillow": ["cushion"],
    "side table": ["end table"],
    "sofa": ["couch"],
    "sofa chair": ["armchair"],
    "tv": ["television"],
    "tv stand": ["television stand"],
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def object_scan_index(objects_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(objects_path)
    return {str(row["scan"]): row for row in payload.get("scans", [])}


def semseg_index(scan_dir: Path) -> dict[str, dict[str, Any]]:
    path = scan_dir / "semseg.v2.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    return {str(row.get("objectId", row.get("id"))): row for row in payload.get("segGroups", [])}


def prompt_role(label: str) -> str:
    if label in STRUCTURAL_CONTEXT_LABELS:
        return "structural_context"
    if label in GENERIC_CONTEXT_LABELS:
        return "generic_context"
    return "detector_target"


def aliases_for_label(label: str) -> list[str]:
    aliases = set(ALIAS_MAP.get(label, []))
    if "/" in label:
        aliases.update(part.strip() for part in label.split("/") if part.strip())
    return sorted(alias for alias in aliases if alias and alias != label)


def prompts_for_label(label: str, aliases: list[str]) -> list[str]:
    prompts = {label, f"a {label}", f"the {label}"}
    for alias in aliases:
        prompts.update({alias, f"a {alias}", f"the {alias}"})
    return sorted(prompts)


def frame_sampling(frame_count: int, max_frames: int = MAX_FRAMES_PER_SCAN) -> dict[str, Any]:
    if frame_count <= 0:
        return {
            "frame_sampling_strategy": "none",
            "frame_stride": None,
            "max_frames": max_frames,
            "sampled_frame_count": 0,
            "sampled_frame_indices": [],
        }
    stride = max(1, math.ceil(frame_count / max_frames))
    indices = list(range(0, frame_count, stride))[:max_frames]
    return {
        "frame_sampling_strategy": "uniform_stride",
        "frame_stride": stride,
        "max_frames": max_frames,
        "sampled_frame_count": len(indices),
        "sampled_frame_indices": indices,
    }


def object_extent(semseg_group: dict[str, Any] | None) -> dict[str, Any]:
    if not semseg_group:
        return {
            "centroid_world_m": None,
            "obb_axes_lengths_m": None,
            "segments_count": 0,
            "semseg_present": False,
        }
    obb = semseg_group.get("obb", {})
    return {
        "centroid_world_m": obb.get("centroid"),
        "obb_axes_lengths_m": obb.get("axesLengths"),
        "segments_count": len(semseg_group.get("segments", [])),
        "semseg_present": True,
    }


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def build_direct_query_rows(
    m54_rows: list[dict[str, Any]],
    verified_scan_ids: set[str],
) -> list[dict[str, Any]]:
    rows = []
    for row in m54_rows:
        if row.get("search_critical_status") != "existing_search_failure_with_label_level_detector_risk":
            continue
        if str(row.get("rescan_id")) not in verified_scan_ids:
            continue
        rows.append(
            {
                "m58_version": M58_VERSION,
                "bridge_query_uid": f"m58:{row['row_uid']}",
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "reference_scan_id": row["reference_scan_id"],
                "current_rescan_id": row["rescan_id"],
                "object_instance_id_ref": str(row["object_instance_id_ref"]),
                "object_instance_id_rescan": str(row["object_instance_id_rescan"]),
                "target_uid": f"{row['rescan_id']}:{row['object_instance_id_rescan']}",
                "label_canonical": row["label_canonical"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "e001_primary_success": row.get("e001_primary_success"),
                "e001_failure_type": row.get("e001_failure_type"),
                "e002_primary_success": row.get("e002_primary_success"),
                "e002_failure_type": row.get("e002_failure_type"),
                "m33_label_target_recall": row.get("m33_target_recall"),
                "m33_label_false_positive_rows": row.get("m33_false_positive_proposal_rows"),
                "m33_label_visible_proxy_missed_target_rows": row.get("m33_visible_proxy_missed_target_rows"),
                "risk_reasons": row.get("risk_reasons", []),
                "bridge_role": "direct_current_rescan_search_failure_query",
                "allowed_for_detector": [
                    "current_rescan_id",
                    "label_canonical",
                    "prompt_set",
                    "RGB-D sequence",
                ],
                "blocked_for_detector": [
                    "target_uid",
                    "object_instance_id_rescan",
                    "e001_primary_success",
                    "e002_primary_success",
                    "failure_type",
                    "matched_3dssg_instance_id",
                ],
            }
        )
    return sorted(rows, key=lambda row: (row["current_rescan_id"], row["label_canonical"], row["row_uid"]))


def build_object_targets(
    direct_query_rows: list[dict[str, Any]],
    verification_rows: list[dict[str, Any]],
    objects_by_scan: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    labels_by_scan: dict[str, set[str]] = defaultdict(set)
    query_rows_by_target_uid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in direct_query_rows:
        labels_by_scan[row["current_rescan_id"]].add(row["label_canonical"])
        query_rows_by_target_uid[row["target_uid"]].append(row)

    verification_by_scan = {str(row["scan_id"]): row for row in verification_rows}
    object_rows: list[dict[str, Any]] = []
    for scan_id, labels in sorted(labels_by_scan.items()):
        scan_state = verification_by_scan[scan_id]
        scan_dir = Path(scan_state["scan_dir"])
        semseg_by_id = semseg_index(scan_dir)
        for obj in objects_by_scan.get(scan_id, {}).get("objects", []):
            label = str(obj.get("label"))
            if label not in labels:
                continue
            object_id = str(obj.get("id"))
            target_uid = f"{scan_id}:{object_id}"
            linked_queries = query_rows_by_target_uid.get(target_uid, [])
            role = prompt_role(label)
            extent = object_extent(semseg_by_id.get(object_id))
            object_rows.append(
                {
                    "m58_version": M58_VERSION,
                    "target_uid": target_uid,
                    "scan_id": scan_id,
                    "object_instance_id": object_id,
                    "global_id": obj.get("global_id"),
                    "label_canonical": label,
                    "prompt_role": role,
                    "detector_prompt_enabled": role == "detector_target",
                    "evaluation_target_enabled": extent["semseg_present"] and role == "detector_target",
                    "is_bridge_query_target": bool(linked_queries),
                    "bridge_query_row_uids": [row["row_uid"] for row in linked_queries],
                    "bridge_query_base_row_uids": sorted({row["base_row_uid"] for row in linked_queries}),
                    "bridge_query_task_contexts": sorted({row["task_context_id"] for row in linked_queries}),
                    "source_objects_json": "local_dataset/3DSSG/objects.json",
                    "source_semseg_json": str(scan_dir / "semseg.v2.json"),
                    "attributes": obj.get("attributes", {}),
                    "affordances": obj.get("affordances", []),
                    "nyu40": obj.get("nyu40"),
                    "rio27": obj.get("rio27"),
                    "eigen13": obj.get("eigen13"),
                    "ply_color": obj.get("ply_color"),
                    **extent,
                }
            )
    return sorted(object_rows, key=lambda row: (row["scan_id"], row["label_canonical"], int(row["object_instance_id"])))


def build_query_manifest_rows(
    verification_rows: list[dict[str, Any]],
    direct_query_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    labels_by_scan: dict[str, set[str]] = defaultdict(set)
    query_rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in direct_query_rows:
        labels_by_scan[row["current_rescan_id"]].add(row["label_canonical"])
        query_rows_by_scan[row["current_rescan_id"]].append(row)
    for row in object_target_rows:
        targets_by_scan[row["scan_id"]].append(row)

    rows = []
    for scan_state in sorted(verification_rows, key=lambda row: row["scan_id"]):
        scan_id = str(scan_state["scan_id"])
        if scan_id not in labels_by_scan:
            continue
        targets = targets_by_scan[scan_id]
        detector_targets = [row for row in targets if row["detector_prompt_enabled"]]
        evaluation_targets = [row for row in targets if row["evaluation_target_enabled"]]
        bridge_targets = [row for row in targets if row["is_bridge_query_target"]]
        sampling = frame_sampling(int(scan_state["frame_triplet_lower_bound"]))
        labels = sorted(labels_by_scan[scan_id])
        rows.append(
            {
                "m58_version": M58_VERSION,
                "staging_version": M58_VERSION,
                "manifest_row_uid": f"m58-direct-current-rescan:{scan_id}",
                "route_id": "direct_current_rescan_detector_bridge",
                "scan_id": scan_id,
                "scan_dir": scan_state["scan_dir"],
                "sequence_zip_path": scan_state["sequence_zip_path"],
                "sequence_dir_ready": scan_state["sequence_dir_ready"],
                "semantic_triplet_ready": True,
                "ply_path": str(Path(scan_state["scan_dir"]) / "labels.instances.annotated.v2.ply"),
                "semseg_path": str(Path(scan_state["scan_dir"]) / "semseg.v2.json"),
                "segs_path": str(Path(scan_state["scan_dir"]) / "mesh.refined.0.010000.segs.v2.json"),
                "color_frames": scan_state["color_frames"],
                "depth_frames": scan_state["depth_frames"],
                "pose_frames": scan_state["pose_frames"],
                "frame_triplet_lower_bound": scan_state["frame_triplet_lower_bound"],
                "frame_id_format": "frame-%06d",
                "detector_profile_id": DETECTOR_PROFILE_ID,
                "detector_config_id": DETECTOR_CONFIG_ID,
                "prompt_set_id": PROMPT_SET_ID,
                "prompt_set_path": "/inputs/prompt_set.json",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": "/inputs/proposal_output_schema.json",
                "object_target_path": "/inputs/real_proposal_object_targets.jsonl",
                "target_labels": labels,
                "target_label_count": len(labels),
                "object_target_count": len(targets),
                "detector_target_count": len(detector_targets),
                "evaluation_target_count": len(evaluation_targets),
                "bridge_query_target_count": len(bridge_targets),
                "bridge_query_row_count": len(query_rows_by_scan[scan_id]),
                "bridge_base_row_count": len({row["base_row_uid"] for row in query_rows_by_scan[scan_id]}),
                "connected_to_e001_dynamic_pairs": True,
                "paper_table_role": "direct_bridge_input_not_final_result",
                **sampling,
            }
        )
    return rows


def build_prompt_set(object_target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels: dict[str, dict[str, Any]] = {}
    for row in object_target_rows:
        label = row["label_canonical"]
        if label not in labels:
            aliases = aliases_for_label(label)
            labels[label] = {
                "aliases": aliases,
                "detector_prompt_enabled": row["detector_prompt_enabled"],
                "label_canonical": label,
                "object_count": 0,
                "prompt_role": row["prompt_role"],
                "prompts": prompts_for_label(label, aliases),
                "scan_ids": set(),
            }
        labels[label]["object_count"] += 1
        labels[label]["scan_ids"].add(row["scan_id"])

    label_rows = []
    for label, payload in sorted(labels.items()):
        label_rows.append(
            {
                **{key: value for key, value in payload.items() if key != "scan_ids"},
                "scan_count": len(payload["scan_ids"]),
                "scan_ids": sorted(payload["scan_ids"]),
            }
        )
    return {
        "m58_version": M58_VERSION,
        "prompt_set_id": PROMPT_SET_ID,
        "source": "E003-M54 search-failure current-rescan labels",
        "detector_profile_id": DETECTOR_PROFILE_ID,
        "prompt_policy": "prompt only direct bridge search-failure labels for the first current-rescan detector bridge",
        "label_count": len(label_rows),
        "detector_target_label_count": sum(1 for row in label_rows if row["detector_prompt_enabled"]),
        "labels": label_rows,
    }


def build_scan_summary_rows(
    manifest_rows: list[dict[str, Any]],
    direct_query_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queries_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in direct_query_rows:
        queries_by_scan[row["current_rescan_id"]].append(row)
    for row in object_target_rows:
        targets_by_scan[row["scan_id"]].append(row)

    rows = []
    for manifest in manifest_rows:
        scan_id = manifest["scan_id"]
        queries = queries_by_scan[scan_id]
        targets = targets_by_scan[scan_id]
        rows.append(
            {
                "m58_version": M58_VERSION,
                "scan_id": scan_id,
                "frame_triplet_lower_bound": manifest["frame_triplet_lower_bound"],
                "sampled_frame_count": manifest["sampled_frame_count"],
                "bridge_query_rows": len(queries),
                "bridge_base_rows": len({row["base_row_uid"] for row in queries}),
                "bridge_target_objects": sum(1 for row in targets if row["is_bridge_query_target"]),
                "same_label_distractor_objects": sum(1 for row in targets if not row["is_bridge_query_target"]),
                "target_labels": manifest["target_labels"],
                "query_task_context_counts": counter_dict(Counter(row["task_context_id"] for row in queries)),
                "query_label_counts": counter_dict(Counter(row["label_canonical"] for row in queries)),
                "e001_failure_rows": sum(1 for row in queries if row["e001_primary_success"] is False),
                "e002_failure_rows": sum(1 for row in queries if row["e002_primary_success"] is False),
            }
        )
    return rows


def build_evaluation_contract() -> dict[str, Any]:
    return {
        "contract_id": "e003_m58_direct_bridge_evaluation_contract_v0",
        "input_files": {
            "detector_predictions": "E003-M59/container_output/real_proposals.jsonl",
            "direct_bridge_query_rows": "E003-M58/direct_bridge_query_rows.jsonl",
            "object_targets": "E003-M58/real_proposal_object_targets.jsonl",
            "query_manifest": "E003-M58/real_proposal_query_manifest.jsonl",
        },
        "join_keys": {
            "query_to_target": ["target_uid"],
            "proposal_to_target": ["scan_id", "label_canonical", "nearest centroid within threshold"],
            "query_to_scan": ["current_rescan_id", "scan_id"],
        },
        "allowed_policy_inputs": [
            "scan_id",
            "label_canonical",
            "proposal centroid/confidence/depth support",
            "task_context_id",
            "staleness/memory metadata available before evaluation",
            "path/search cost fields available before evaluation",
        ],
        "blocked_policy_inputs": [
            "target_uid",
            "object_instance_id_rescan",
            "matched_3dssg_instance_id",
            "match_distance_m",
            "e001/e002 success labels",
        ],
        "required_metrics": [
            "query_target_detected",
            "query_target_rank_by_detector_score",
            "same_label_false_positive_count",
            "false_positive_before_target_count",
            "detector_bridge_resolvable_failure_rate",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "stale old-location dead-end avoided",
        ],
        "claim_boundary": {
            "safe_after_m58": [
                "A direct current-rescan detector/evaluation bridge denominator is designed.",
                "The bridge preserves E001/E002 dynamic-pair current-rescan identity.",
            ],
            "unsupported_after_m58": [
                "real RGB-D/open-vocabulary search robustness",
                "deployable search policy",
                "real navigation SR/SPL",
                "external baseline comparison",
            ],
        },
    }


def build_command_plan(out_dir: Path) -> dict[str, Any]:
    m59_out = EXPERIMENT_ROOT / "artifacts" / "E003-M59_direct_current_rescan_detector_run_v0"
    command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--m17-dir",
        str(out_dir),
        "--out-dir",
        str(m59_out),
        "--max-scans",
        "4",
        "--max-frames-per-scan",
        str(MAX_FRAMES_PER_SCAN),
        "--max-labels",
        "8",
        "--max-predictions",
        "4000",
        "--max-predictions-per-frame",
        "60",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "200000",
        "--export-pre-cap-candidate-pool",
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
    ]
    log_path = REPO_ROOT / "logs" / "YYYYMMDD_HHMMSS_e003_m59_direct_current_rescan_detector_run.log"
    return {
        "command_id": "e003_m59_direct_current_rescan_detector_run_command_v0",
        "working_directory": str(REPO_ROOT),
        "m17_compatible_input_dir": str(out_dir),
        "output_dir": str(m59_out),
        "exact_command": command,
        "shell_command": " ".join(f"'{item}'" if " " in item else item for item in command),
        "long_running_policy": "launch in tmux/nohup with timestamped log under logs/",
        "tmux_template": (
            "tmux new -d -s e003_m59_direct_bridge "
            f"'cd {REPO_ROOT} && <sudo-password-provider> {' '.join(command)} > {log_path} 2>&1'"
        ),
        "expected_files": [
            str(m59_out / "coverage.json"),
            str(m59_out / "container_output" / "real_proposals.jsonl"),
            str(m59_out / "matching" / "coverage.json"),
            str(m59_out / "validator" / "coverage.json"),
        ],
        "verification_command": [
            "python",
            "experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py",
            "--predictions",
            str(m59_out / "container_output" / "real_proposals.jsonl"),
            "--manifest",
            str(out_dir / "real_proposal_query_manifest.jsonl"),
            "--targets",
            str(out_dir / "real_proposal_object_targets.jsonl"),
            "--schema",
            str(out_dir / "proposal_output_schema.json"),
            "--out-dir",
            str(m59_out / "validator"),
            "--schema-only-smoke",
        ],
        "next_unit_after_detector_run": "E003-M60 direct current-rescan query-level bridge evaluation",
    }


def build_coverage(
    out_dir: Path,
    direct_query_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
    prompt_set: dict[str, Any],
    scan_summary_rows: list[dict[str, Any]],
    evaluation_contract: dict[str, Any],
) -> dict[str, Any]:
    bridge_target_uids = {row["target_uid"] for row in direct_query_rows}
    linked_target_uids = {row["target_uid"] for row in object_target_rows if row["is_bridge_query_target"]}
    missing_target_uids = sorted(bridge_target_uids - linked_target_uids)
    status = "direct_current_rescan_bridge_design_ready"
    if missing_target_uids or not manifest_rows:
        status = "review_needed"
    return {
        "m58_version": M58_VERSION,
        "status": status,
        "direct_bridge_query_rows": len(direct_query_rows),
        "direct_bridge_base_rows": len({row["base_row_uid"] for row in direct_query_rows}),
        "direct_bridge_scan_rows": len(manifest_rows),
        "direct_bridge_target_labels": sorted({row["label_canonical"] for row in direct_query_rows}),
        "bridge_query_target_uids": len(bridge_target_uids),
        "linked_bridge_query_target_uids": len(linked_target_uids),
        "missing_bridge_query_target_uids": missing_target_uids,
        "object_target_rows": len(object_target_rows),
        "bridge_query_target_object_rows": sum(1 for row in object_target_rows if row["is_bridge_query_target"]),
        "same_label_distractor_object_rows": sum(1 for row in object_target_rows if not row["is_bridge_query_target"]),
        "prompt_label_count": prompt_set["label_count"],
        "detector_target_label_count": prompt_set["detector_target_label_count"],
        "sampled_frame_count": sum(int(row["sampled_frame_count"]) for row in manifest_rows),
        "frame_triplet_lower_bound_total": sum(int(row["frame_triplet_lower_bound"]) for row in manifest_rows),
        "paper_table_command_ready": False,
        "detector_run_executed": False,
        "real_rgbd_or_open_vocab_search_claim_ready": False,
        "evaluation_contract_id": evaluation_contract["contract_id"],
        "next_recommended_unit": "E003-M59 direct current-rescan detector bridge Docker run",
        "outputs": {
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
            "direct_bridge_query_rows": str(out_dir / "direct_bridge_query_rows.jsonl"),
            "real_proposal_query_manifest": str(out_dir / "real_proposal_query_manifest.jsonl"),
            "real_proposal_object_targets": str(out_dir / "real_proposal_object_targets.jsonl"),
            "scan_bridge_summary": str(out_dir / "scan_bridge_summary.jsonl"),
            "prompt_set": str(out_dir / "prompt_set.json"),
            "proposal_output_schema": str(out_dir / "proposal_output_schema.json"),
            "evaluation_contract": str(out_dir / "evaluation_contract.json"),
            "detector_run_command_plan": str(out_dir / "detector_run_command_plan.json"),
        },
        "scan_summary": scan_summary_rows,
    }


def build_report(coverage: dict[str, Any], command_plan: dict[str, Any]) -> str:
    lines = [
        "# E003-M58 Direct Current-Rescan Detector Bridge Design",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Direct bridge query rows: {coverage['direct_bridge_query_rows']}",
        f"- Direct bridge base rows: {coverage['direct_bridge_base_rows']}",
        f"- Direct bridge scans: {coverage['direct_bridge_scan_rows']}",
        f"- Target labels: {coverage['direct_bridge_target_labels']}",
        f"- Linked bridge query target uids: {coverage['linked_bridge_query_target_uids']} / {coverage['bridge_query_target_uids']}",
        f"- Object target rows: {coverage['object_target_rows']}",
        f"- Same-label distractor object rows: {coverage['same_label_distractor_object_rows']}",
        f"- Prompt label count: {coverage['prompt_label_count']}",
        f"- Sampled frame count for next detector run: {coverage['sampled_frame_count']}",
        f"- Detector run executed: {coverage['detector_run_executed']}",
        f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
        f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_or_open_vocab_search_claim_ready']}",
        "",
        "## Scan Summary",
        "",
        "| Scan | labels | query rows | base rows | bridge targets | distractors | sampled frames |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in coverage["scan_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['scan_id']}`",
                    ", ".join(f"`{label}`" for label in row["target_labels"]),
                    str(row["bridge_query_rows"]),
                    str(row["bridge_base_rows"]),
                    str(row["bridge_target_objects"]),
                    str(row["same_label_distractor_objects"]),
                    str(row["sampled_frame_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M58 supports saying that the direct current-rescan bridge denominator is ready.",
            "- E003-M58 does not support a real RGB-D/open-vocabulary search result because no detector run or query-level bridge evaluation has been executed.",
            "- E003-M58 preserves E001/E002 dynamic-pair current-rescan identity, which is the missing causality link from E003-M54.",
            "",
            "## 에이전트 추론",
            "",
            "- The next detector run should use this artifact as the `--m17-dir` input so the existing Docker runner and M21 matcher can be reused without schema drift.",
            "- The first bridge uses only `chair` and `pillow` prompts because those are the labels with existing E001/E002 search failures and M33 detector risk.",
            "- Query-level bridge evaluation should be a separate step after detector output exists; otherwise detector matching and search-decision metrics would be mixed.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. The next unit should execute or launch the recorded detector command if compute is available.",
            "",
            "## Next Command Plan",
            "",
            f"- Output dir: `{command_plan['output_dir']}`",
            f"- Next unit: `{command_plan['next_unit_after_detector_run']}`",
            f"- Exact command: `{' '.join(command_plan['exact_command'])}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--m54-dir", default=DEFAULT_M54_DIR, type=Path)
    parser.add_argument("--m55-dir", default=DEFAULT_M55_DIR, type=Path)
    parser.add_argument("--m56-dir", default=DEFAULT_M56_DIR, type=Path)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    m54_rows = load_jsonl(args.m54_dir / "query_search_boundary_rows.jsonl")
    m55_coverage = load_json(args.m55_dir / "coverage.json")
    verification_rows = load_jsonl(args.m56_dir / "verification" / "verification_rows.jsonl")
    verified_scan_ids = {str(row["scan_id"]) for row in verification_rows if row.get("ready")}
    objects_by_scan = object_scan_index(args.dataset_root / "3DSSG" / "objects.json")

    direct_query_rows = build_direct_query_rows(m54_rows, verified_scan_ids)
    expected_scans = set(m55_coverage.get("search_failure_current_rescans", []))
    verification_rows = [row for row in verification_rows if str(row["scan_id"]) in expected_scans]
    object_target_rows = build_object_targets(direct_query_rows, verification_rows, objects_by_scan)
    manifest_rows = build_query_manifest_rows(verification_rows, direct_query_rows, object_target_rows)
    prompt_set = build_prompt_set(object_target_rows)
    scan_summary_rows = build_scan_summary_rows(manifest_rows, direct_query_rows, object_target_rows)
    evaluation_contract = build_evaluation_contract()
    command_plan = build_command_plan(args.out_dir)

    schema_payload = load_json(args.m17_dir / "proposal_output_schema.json")
    coverage = build_coverage(
        args.out_dir,
        direct_query_rows,
        manifest_rows,
        object_target_rows,
        prompt_set,
        scan_summary_rows,
        evaluation_contract,
    )

    write_jsonl(args.out_dir / "direct_bridge_query_rows.jsonl", direct_query_rows)
    write_jsonl(args.out_dir / "real_proposal_query_manifest.jsonl", manifest_rows)
    write_jsonl(args.out_dir / "real_proposal_object_targets.jsonl", object_target_rows)
    write_jsonl(args.out_dir / "scan_bridge_summary.jsonl", scan_summary_rows)
    write_json(args.out_dir / "prompt_set.json", prompt_set)
    write_json(args.out_dir / "proposal_output_schema.json", schema_payload)
    write_json(args.out_dir / "evaluation_contract.json", evaluation_contract)
    write_json(args.out_dir / "detector_run_command_plan.json", command_plan)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage, command_plan))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
