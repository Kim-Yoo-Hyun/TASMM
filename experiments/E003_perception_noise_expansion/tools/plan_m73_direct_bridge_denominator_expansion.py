#!/usr/bin/env python3
"""Plan the direct current-rescan bridge denominator expansion."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_QUERY_ROWS = EXPERIMENT_ROOT.parent / "E001_semantic_pair_dynamic_search_proxy" / "artifacts" / "E001-M02_query_construction_v0" / "query_rows.jsonl"
DEFAULT_M58_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M58_direct_current_rescan_bridge_design_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
M73_VERSION = "e003_m73_direct_bridge_denominator_expansion_plan_v0"
PROMPT_SET_ID = "e003_m73_direct_bridge_denominator_expansion_prompts_v0"
DETECTOR_PROFILE_ID = "open_vocab_rgbd_detector_v0"
DETECTOR_CONFIG_ID = "h001_direct_current_rescan_groundingdino_tiny_rgbd_backproject_v0"
MAX_FRAMES_PER_SCAN = 24
MAX_PREDICTIONS = 20000
MAX_PREDICTIONS_PER_FRAME = 100
GENERIC_CONTEXT_LABELS = {"clutter", "item", "kitchen object", "object", "objects"}
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
ALIAS_MAP = {
    "bath cabinet": ["bathroom cabinet"],
    "bench": ["seat"],
    "commode": ["toilet"],
    "couch": ["sofa"],
    "couch table": ["coffee table"],
    "gymnastic ball": ["exercise ball"],
    "laundry basket": ["clothes basket"],
    "pillow": ["cushion"],
    "rocking chair": ["chair"],
    "side table": ["end table"],
    "sofa": ["couch"],
    "sofa chair": ["armchair"],
    "trash can": ["waste bin"],
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


def scan_payload_status(scans_root: Path, scan_id: str) -> dict[str, Any]:
    scan_dir = scans_root / scan_id
    sequence_dir = scan_dir / "sequence"
    color_count = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.exists() else 0
    depth_count = len(list(sequence_dir.glob("*.depth.pgm"))) if sequence_dir.exists() else 0
    pose_count = len(list(sequence_dir.glob("*.pose.txt"))) if sequence_dir.exists() else 0
    frame_count = min(color_count, depth_count, pose_count)
    return {
        "color_frames": color_count,
        "depth_frames": depth_count,
        "frame_triplet_lower_bound": frame_count,
        "ply_path": str(scan_dir / "labels.instances.annotated.v2.ply"),
        "pose_frames": pose_count,
        "scan_dir": str(scan_dir),
        "scan_id": scan_id,
        "segs_path": str(scan_dir / "mesh.refined.0.010000.segs.v2.json"),
        "semantic_triplet_ready": (
            (scan_dir / "labels.instances.annotated.v2.ply").exists()
            and (scan_dir / "semseg.v2.json").exists()
            and (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists()
        ),
        "semseg_path": str(scan_dir / "semseg.v2.json"),
        "sequence_dir_ready": sequence_dir.exists() and frame_count > 0,
        "sequence_zip_path": str(scan_dir / "sequence.zip"),
    }


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


def build_query_rows(rows: list[dict[str, Any]], ready_scan_ids: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in rows:
        scan_id = str(row["rescan_id"])
        if scan_id not in ready_scan_ids:
            continue
        label = str(row["object_label"])
        role = prompt_role(label)
        payload = {
            "base_row_uid": row["base_row_uid"],
            "bridge_query_uid": f"m73:{row['row_uid']}",
            "current_rescan_id": scan_id,
            "label_canonical": label,
            "m73_version": M73_VERSION,
            "object_instance_id_ref": str(row["object_instance_id_ref"]),
            "object_instance_id_rescan": str(row["object_instance_id_rescan"]),
            "pair_uid": row["pair_uid"],
            "reference_scan_id": row["reference_scan_id"],
            "row_band": row["row_band"],
            "row_uid": row["row_uid"],
            "target_uid": f"{scan_id}:{row['object_instance_id_rescan']}",
            "task_context_id": row["task_context_id"],
        }
        if role != "detector_target":
            payload.update({"exclude_reason": f"{role}_label", "prompt_role": role})
            excluded.append(payload)
            continue
        payload.update(
            {
                "allowed_for_detector": ["current_rescan_id", "label_canonical", "prompt_set", "RGB-D sequence"],
                "blocked_for_detector": [
                    "target_uid",
                    "object_instance_id_rescan",
                    "candidate_is_target",
                    "matched_3dssg_instance_id",
                    "task outcome labels",
                ],
                "bridge_role": "direct_current_rescan_denominator_query",
                "prompt_role": role,
            }
        )
        selected.append(payload)
    return (
        sorted(selected, key=lambda row: (row["current_rescan_id"], row["label_canonical"], row["row_uid"])),
        sorted(excluded, key=lambda row: (row["current_rescan_id"], row["label_canonical"], row["row_uid"])),
    )


def build_object_targets(
    query_rows: list[dict[str, Any]],
    objects_by_scan: dict[str, dict[str, Any]],
    scans_root: Path,
) -> list[dict[str, Any]]:
    labels_by_scan: dict[str, set[str]] = defaultdict(set)
    query_rows_by_target_uid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        labels_by_scan[row["current_rescan_id"]].add(row["label_canonical"])
        query_rows_by_target_uid[row["target_uid"]].append(row)

    object_rows: list[dict[str, Any]] = []
    for scan_id, labels in sorted(labels_by_scan.items()):
        scan_dir = scans_root / scan_id
        semseg_by_id = semseg_index(scan_dir)
        for obj in objects_by_scan.get(scan_id, {}).get("objects", []):
            label = str(obj.get("label"))
            if label not in labels:
                continue
            object_id = str(obj.get("id"))
            target_uid = f"{scan_id}:{object_id}"
            linked_queries = query_rows_by_target_uid.get(target_uid, [])
            aliases = aliases_for_label(label)
            role = prompt_role(label)
            extent = object_extent(semseg_by_id.get(object_id))
            object_rows.append(
                {
                    "affordances": obj.get("affordances", []),
                    "aliases": aliases,
                    "attributes": obj.get("attributes", {}),
                    "bridge_query_base_row_uids": sorted({row["base_row_uid"] for row in linked_queries}),
                    "bridge_query_row_uids": [row["row_uid"] for row in linked_queries],
                    "bridge_query_task_contexts": sorted({row["task_context_id"] for row in linked_queries}),
                    "detector_prompt_enabled": role == "detector_target",
                    "eigen13": obj.get("eigen13"),
                    "evaluation_target_enabled": extent["semseg_present"] and role == "detector_target",
                    "global_id": obj.get("global_id"),
                    "is_bridge_query_target": bool(linked_queries),
                    "label_canonical": label,
                    "m73_version": M73_VERSION,
                    "nyu40": obj.get("nyu40"),
                    "object_instance_id": object_id,
                    "ply_color": obj.get("ply_color"),
                    "prompt_role": role,
                    "rio27": obj.get("rio27"),
                    "scan_id": scan_id,
                    "source_objects_json": "local_dataset/3DSSG/objects.json",
                    "source_semseg_json": str(scan_dir / "semseg.v2.json"),
                    "target_uid": target_uid,
                    **extent,
                }
            )
    return sorted(object_rows, key=lambda row: (row["scan_id"], row["label_canonical"], int(row["object_instance_id"])))


def build_prompt_set(object_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in object_rows:
        if row["detector_prompt_enabled"]:
            grouped[row["label_canonical"]].append(row)
    labels = []
    for label, rows in sorted(grouped.items()):
        aliases = aliases_for_label(label)
        labels.append(
            {
                "aliases": aliases,
                "detector_prompt_enabled": True,
                "label_canonical": label,
                "object_count": len(rows),
                "prompt_role": "detector_target",
                "prompts": prompts_for_label(label, aliases),
                "scan_count": len({row["scan_id"] for row in rows}),
                "scan_ids": sorted({row["scan_id"] for row in rows}),
            }
        )
    return {
        "detector_profile_id": DETECTOR_PROFILE_ID,
        "detector_target_label_count": len(labels),
        "label_count": len(labels),
        "labels": labels,
        "m73_version": M73_VERSION,
        "prompt_policy": "prompt detector-ready labels from all RGB-D-ready exact current-rescan E001 query rows",
        "prompt_set_id": PROMPT_SET_ID,
        "source": "E001 query rows filtered by exact current-rescan RGB-D payload readiness",
    }


def build_scan_manifest(query_rows: list[dict[str, Any]], object_rows: list[dict[str, Any]], scans_root: Path) -> list[dict[str, Any]]:
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    objects_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        rows_by_scan[row["current_rescan_id"]].append(row)
    for row in object_rows:
        objects_by_scan[row["scan_id"]].append(row)

    manifest = []
    for scan_id, rows in sorted(rows_by_scan.items()):
        status = scan_payload_status(scans_root, scan_id)
        sampling = frame_sampling(int(status["frame_triplet_lower_bound"]))
        labels = sorted({row["label_canonical"] for row in rows})
        object_targets = [row for row in objects_by_scan[scan_id] if row["evaluation_target_enabled"]]
        manifest.append(
            {
                **status,
                **sampling,
                "bridge_base_row_count": len({row["base_row_uid"] for row in rows}),
                "bridge_query_row_count": len(rows),
                "bridge_query_target_count": len({row["target_uid"] for row in rows}),
                "connected_to_e001_dynamic_pairs": True,
                "detector_config_id": DETECTOR_CONFIG_ID,
                "detector_profile_id": DETECTOR_PROFILE_ID,
                "detector_target_count": len(object_targets),
                "evaluation_target_count": len(object_targets),
                "frame_id_format": "frame-%06d",
                "manifest_row_uid": f"m73-direct-current-rescan:{scan_id}",
                "object_target_count": len(object_targets),
                "object_target_path": "/inputs/real_proposal_object_targets.jsonl",
                "paper_table_role": "direct_bridge_denominator_expansion_input_not_final_result",
                "prompt_set_id": PROMPT_SET_ID,
                "prompt_set_path": "/inputs/prompt_set.json",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": "/inputs/proposal_output_schema.json",
                "route_id": "direct_current_rescan_denominator_expansion",
                "staging_version": M73_VERSION,
                "target_label_count": len(labels),
                "target_labels": labels,
            }
        )
    return manifest


def build_detector_command(out_dir: Path, label_count: int) -> dict[str, Any]:
    output_dir = EXPERIMENT_ROOT / "artifacts" / "E003-M74_direct_bridge_denominator_detector_run_v0"
    exact_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--m17-dir",
        str(out_dir),
        "--out-dir",
        str(output_dir),
        "--max-scans",
        "4",
        "--max-frames-per-scan",
        str(MAX_FRAMES_PER_SCAN),
        "--max-labels",
        str(label_count),
        "--max-predictions",
        str(MAX_PREDICTIONS),
        "--max-predictions-per-frame",
        str(MAX_PREDICTIONS_PER_FRAME),
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
        "400000",
        "--export-pre-cap-candidate-pool",
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
    ]
    return {
        "command_id": "e003_m74_direct_bridge_denominator_detector_run_command_v0",
        "exact_command": exact_command,
        "expected_files": [
            str(output_dir / "coverage.json"),
            str(output_dir / "container_output" / "real_proposals.jsonl"),
            str(output_dir / "matching" / "coverage.json"),
            str(output_dir / "validator" / "coverage.json"),
        ],
        "long_running_policy": "launch in tmux/nohup with timestamped log under logs/",
        "m17_compatible_input_dir": str(out_dir),
        "next_unit_after_detector_run": "E003-M75 expanded direct bridge query-level evaluation",
        "output_dir": str(output_dir),
        "shell_command": " ".join(exact_command),
        "tmux_template": "tmux new-session -d -s e003_m74_direct_denominator '<sudo-password-provider> " + " ".join(exact_command) + " > logs/YYYYMMDD_HHMMSS_e003_m74_direct_bridge_denominator_detector_run.log 2>&1'",
        "verification_command": [
            "python",
            "experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py",
            "--predictions",
            str(output_dir / "container_output" / "real_proposals.jsonl"),
            "--manifest",
            str(out_dir / "real_proposal_query_manifest.jsonl"),
            "--targets",
            str(out_dir / "real_proposal_object_targets.jsonl"),
            "--schema",
            str(out_dir / "proposal_output_schema.json"),
            "--out-dir",
            str(output_dir / "validator"),
            "--schema-only-smoke",
        ],
        "working_directory": str(REPO_ROOT),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M73 Direct Bridge Denominator Expansion Plan",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- RGB-D-ready exact current-rescan scans: {coverage['selected_scan_count']}.",
            f"- Detector-ready expanded query rows: {coverage['detector_ready_query_rows']}.",
            f"- Detector-ready expanded base rows: {coverage['detector_ready_base_rows']}.",
            f"- Previous M58 query rows: {coverage['previous_m58_query_rows']}.",
            f"- Added query rows over M58: {coverage['added_query_rows_over_m58']}.",
            f"- Prompt labels: {coverage['prompt_label_count']} / {coverage['prompt_labels']}.",
            f"- Sampled frame count: {coverage['sampled_frame_count']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M73 only supports a planned denominator expansion contract.",
            "- It does not support real RGB-D/open-vocabulary search improvement until E003-M74/E003-M75 run and join detector outputs back to query-level metrics.",
            "",
            "## 에이전트 추론",
            "",
            "- This is the right fallback after `OpenMask3D` Docker failure because it increases the exact current-rescan bridge denominator without changing the core method claim.",
            "- The plan expands from failure-only rows to all detector-ready task contexts on already staged current rescans, which gives both success and failure cases for reviewer defense.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before launching the recorded E003-M74 background detector run.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--query-rows", default=DEFAULT_QUERY_ROWS, type=Path)
    parser.add_argument("--m58-dir", default=DEFAULT_M58_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.dataset_root = args.dataset_root.resolve()
    args.query_rows = args.query_rows.resolve()
    args.m58_dir = args.m58_dir.resolve()
    args.out_dir = args.out_dir.resolve()

    scans_root = args.dataset_root / "3RScan" / "scans"
    objects_by_scan = object_scan_index(args.dataset_root / "3DSSG" / "objects.json")
    query_rows = load_jsonl(args.query_rows)
    m58_coverage = load_json(args.m58_dir / "coverage.json")
    schema_source = args.m58_dir / "proposal_output_schema.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    candidate_scan_ids = sorted({str(row["rescan_id"]) for row in query_rows})
    scan_status_rows = [scan_payload_status(scans_root, scan_id) for scan_id in candidate_scan_ids]
    ready_scan_ids = {
        row["scan_id"]
        for row in scan_status_rows
        if row["semantic_triplet_ready"] and row["sequence_dir_ready"] and row["frame_triplet_lower_bound"] > 0
    }
    selected_query_rows, excluded_query_rows = build_query_rows(query_rows, ready_scan_ids)
    object_targets = build_object_targets(selected_query_rows, objects_by_scan, scans_root)
    prompt_set = build_prompt_set(object_targets)
    scan_manifest = build_scan_manifest(selected_query_rows, object_targets, scans_root)
    label_count = int(prompt_set["detector_target_label_count"])
    command_plan = build_detector_command(args.out_dir, label_count)
    if schema_source.exists():
        shutil.copyfile(schema_source, args.out_dir / "proposal_output_schema.json")

    label_counts = Counter(row["label_canonical"] for row in selected_query_rows)
    task_counts = Counter(row["task_context_id"] for row in selected_query_rows)
    band_counts = Counter(row["row_band"] for row in selected_query_rows)
    prompt_labels = [row["label_canonical"] for row in prompt_set["labels"]]
    previous_query_rows = int(m58_coverage.get("direct_bridge_query_rows", 0) or 0)
    previous_base_rows = int(m58_coverage.get("direct_bridge_base_rows", 0) or 0)
    coverage = {
        "added_base_rows_over_m58": len({row["base_row_uid"] for row in selected_query_rows}) - previous_base_rows,
        "added_query_rows_over_m58": len(selected_query_rows) - previous_query_rows,
        "candidate_scan_count": len(candidate_scan_ids),
        "detector_command_plan": str(args.out_dir / "detector_run_command_plan.json"),
        "detector_ready_base_rows": len({row["base_row_uid"] for row in selected_query_rows}),
        "detector_ready_query_rows": len(selected_query_rows),
        "detector_rerun_launched": False,
        "excluded_query_rows": len(excluded_query_rows),
        "excluded_query_rows_by_reason": counter_dict(Counter(row["exclude_reason"] for row in excluded_query_rows)),
        "m73_version": M73_VERSION,
        "next_recommended_unit": "E003-M74 expanded direct bridge detector background launch",
        "object_target_rows": len(object_targets),
        "paper_table_command_ready": False,
        "previous_m58_base_rows": previous_base_rows,
        "previous_m58_query_rows": previous_query_rows,
        "prompt_label_count": label_count,
        "prompt_labels": prompt_labels,
        "query_label_counts": counter_dict(label_counts),
        "query_row_band_counts": counter_dict(band_counts),
        "query_task_context_counts": counter_dict(task_counts),
        "real_rgbd_open_vocab_search_claim_ready": False,
        "sampled_frame_count": sum(int(row["sampled_frame_count"]) for row in scan_manifest),
        "selected_scan_count": len(scan_manifest),
        "selected_scan_ids": [row["scan_id"] for row in scan_manifest],
        "source_query_rows": len(query_rows),
        "status": "direct_bridge_denominator_expansion_plan_ready",
        "target_uid_count": len({row["target_uid"] for row in selected_query_rows}),
    }

    write_jsonl(args.out_dir / "scan_payload_status.jsonl", scan_status_rows)
    write_jsonl(args.out_dir / "direct_bridge_query_rows.jsonl", selected_query_rows)
    write_jsonl(args.out_dir / "excluded_query_rows.jsonl", excluded_query_rows)
    write_jsonl(args.out_dir / "real_proposal_query_manifest.jsonl", scan_manifest)
    write_jsonl(args.out_dir / "real_proposal_object_targets.jsonl", object_targets)
    write_json(args.out_dir / "prompt_set.json", prompt_set)
    write_json(args.out_dir / "detector_run_command_plan.json", command_plan)
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
