#!/usr/bin/env python3
"""Stage E003-M17 real-proposal denominator inputs."""

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
DEFAULT_M16_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M16_real_proposal_route_decision_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
STAGING_VERSION = "e003_m17_real_proposal_denominator_staging_v0"
PROMPT_SET_ID = "e003_m17_3dssg_sequence_ready_prompts_v0"
DETECTOR_PROFILE_ID = "open_vocab_rgbd_detector_v0"
DETECTOR_CONFIG_ID = "h001_real_proposals_ovdet_v0"
MAX_FRAMES_PER_SCAN = 64
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
    "couch": ["sofa"],
    "couch table": ["coffee table"],
    "commode": ["toilet"],
    "floor /other room": ["floor"],
    "laundry basket": ["clothes basket"],
    "side table": ["end table"],
    "sofa": ["couch"],
    "sofa chair": ["armchair"],
    "tv": ["television"],
    "tv stand": ["television stand"],
    "wall /other room": ["wall"],
}


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


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def object_scan_index(objects_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(objects_path)
    return {row["scan"]: row for row in payload.get("scans", [])}


def semseg_index(scan_dir: Path) -> dict[str, dict[str, Any]]:
    semseg_path = scan_dir / "semseg.v2.json"
    if not semseg_path.exists():
        return {}
    payload = load_json(semseg_path)
    output = {}
    for group in payload.get("segGroups", []):
        object_id = str(group.get("objectId", group.get("id")))
        output[object_id] = group
    return output


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
            "semseg_present": False,
            "centroid_world_m": None,
            "obb_axes_lengths_m": None,
            "segments_count": 0,
        }
    obb = semseg_group.get("obb", {})
    return {
        "semseg_present": True,
        "centroid_world_m": obb.get("centroid"),
        "obb_axes_lengths_m": obb.get("axesLengths"),
        "segments_count": len(semseg_group.get("segments", [])),
    }


def build_object_target_rows(
    ready_scan_rows: list[dict[str, Any]],
    objects_by_scan: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for scan_row in ready_scan_rows:
        scan_id = scan_row["scan_id"]
        scan_dir = Path(scan_row["scan_dir"])
        semseg_by_id = semseg_index(scan_dir)
        scan_objects = objects_by_scan.get(scan_id, {}).get("objects", [])
        for obj in scan_objects:
            label = str(obj["label"])
            role = prompt_role(label)
            object_id = str(obj["id"])
            extent = object_extent(semseg_by_id.get(object_id))
            rows.append(
                {
                    "staging_version": STAGING_VERSION,
                    "target_uid": f"{scan_id}:{object_id}",
                    "scan_id": scan_id,
                    "object_instance_id": object_id,
                    "global_id": obj.get("global_id"),
                    "label_canonical": label,
                    "prompt_role": role,
                    "detector_prompt_enabled": role == "detector_target",
                    "evaluation_target_enabled": extent["semseg_present"] and role == "detector_target",
                    "attributes": obj.get("attributes", {}),
                    "affordances": obj.get("affordances", []),
                    "nyu40": obj.get("nyu40"),
                    "rio27": obj.get("rio27"),
                    "eigen13": obj.get("eigen13"),
                    "ply_color": obj.get("ply_color"),
                    "source_objects_json": "local_dataset/3DSSG/objects.json",
                    "source_semseg_json": str(scan_dir / "semseg.v2.json"),
                    **extent,
                }
            )
    return rows


def build_query_manifest_rows(
    ready_scan_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    targets_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in object_target_rows:
        targets_by_scan[row["scan_id"]].append(row)

    rows = []
    for scan_row in ready_scan_rows:
        scan_id = scan_row["scan_id"]
        targets = targets_by_scan[scan_id]
        detector_targets = [row for row in targets if row["detector_prompt_enabled"]]
        evaluation_targets = [row for row in targets if row["evaluation_target_enabled"]]
        labels = sorted({row["label_canonical"] for row in detector_targets})
        sampling = frame_sampling(int(scan_row["frame_triplet_lower_bound"]))
        rows.append(
            {
                "staging_version": STAGING_VERSION,
                "manifest_row_uid": f"m17-real-proposal:{scan_id}",
                "route_id": "sequence_ready_scan_bootstrap",
                "scan_id": scan_id,
                "scan_dir": scan_row["scan_dir"],
                "sequence_zip_path": scan_row["sequence_zip_path"],
                "sequence_dir_ready": scan_row["sequence_dir_ready"],
                "semantic_triplet_ready": scan_row["semantic_triplet_ready"],
                "ply_path": str(Path(scan_row["scan_dir"]) / "labels.instances.annotated.v2.ply"),
                "semseg_path": str(Path(scan_row["scan_dir"]) / "semseg.v2.json"),
                "segs_path": str(Path(scan_row["scan_dir"]) / "mesh.refined.0.010000.segs.v2.json"),
                "objects_3dssg_ready": scan_row["objects_3dssg_ready"],
                "relationships_3dssg_ready": scan_row["relationships_3dssg_ready"],
                "color_frames": scan_row["color_frames"],
                "depth_frames": scan_row["depth_frames"],
                "pose_frames": scan_row["pose_frames"],
                "frame_triplet_lower_bound": scan_row["frame_triplet_lower_bound"],
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
                "not_connected_to_e001_dynamic_pairs": True,
                "paper_table_role": "real_proposal_staging_input_not_final_result",
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
                "label_canonical": label,
                "prompt_role": row["prompt_role"],
                "detector_prompt_enabled": row["detector_prompt_enabled"],
                "aliases": aliases,
                "prompts": prompts_for_label(label, aliases),
                "object_count": 0,
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
        "staging_version": STAGING_VERSION,
        "prompt_set_id": PROMPT_SET_ID,
        "source": "3DSSG labels from sequence-ready 3RScan scans",
        "detector_profile_id": DETECTOR_PROFILE_ID,
        "prompt_policy": "prompt all non-structural, non-generic labels as detector targets; retain structural/generic labels as context/evaluation metadata",
        "label_count": len(label_rows),
        "detector_target_label_count": sum(1 for row in label_rows if row["detector_prompt_enabled"]),
        "structural_context_label_count": sum(
            1 for row in label_rows if row["prompt_role"] == "structural_context"
        ),
        "generic_context_label_count": sum(
            1 for row in label_rows if row["prompt_role"] == "generic_context"
        ),
        "labels": label_rows,
    }


def build_scan_summary_rows(
    query_manifest_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    targets_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in object_target_rows:
        targets_by_scan[row["scan_id"]].append(row)
    rows = []
    for manifest in query_manifest_rows:
        scan_targets = targets_by_scan[manifest["scan_id"]]
        role_counts = Counter(row["prompt_role"] for row in scan_targets)
        rows.append(
            {
                "staging_version": STAGING_VERSION,
                "scan_id": manifest["scan_id"],
                "frame_triplet_lower_bound": manifest["frame_triplet_lower_bound"],
                "sampled_frame_count": manifest["sampled_frame_count"],
                "object_target_count": len(scan_targets),
                "detector_target_count": sum(
                    1 for row in scan_targets if row["detector_prompt_enabled"]
                ),
                "evaluation_target_count": sum(
                    1 for row in scan_targets if row["evaluation_target_enabled"]
                ),
                "semseg_present_count": sum(1 for row in scan_targets if row["semseg_present"]),
                "prompt_role_counts": counter_dict(role_counts),
                "unique_detector_labels": sorted(
                    {row["label_canonical"] for row in scan_targets if row["detector_prompt_enabled"]}
                ),
            }
        )
    return rows


def build_staging_decision(
    query_manifest_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
    prompt_set: dict[str, Any],
    m16_coverage: dict[str, Any],
) -> dict[str, Any]:
    return {
        "staging_version": STAGING_VERSION,
        "status": "real_proposal_denominator_staged",
        "source_route": "sequence_ready_scan_bootstrap",
        "input_basis": "E003-M16 selected sequence-ready scan bootstrap because current E001 rescans had 0 sequence-ready query rows.",
        "scan_manifest_rows": len(query_manifest_rows),
        "object_target_rows": len(object_target_rows),
        "evaluation_target_rows": sum(1 for row in object_target_rows if row["evaluation_target_enabled"]),
        "prompt_label_count": prompt_set["label_count"],
        "detector_target_label_count": prompt_set["detector_target_label_count"],
        "schema_copied_from": m16_coverage["outputs"]["proposal_output_schema"],
        "docker_command_plan_source": m16_coverage["outputs"]["docker_command_plan"],
        "paper_table_command_ready": False,
        "paper_table_command_blocker": "Docker detector implementation/image is not staged and detector output has not been generated.",
        "claim_boundary": {
            "safe": [
                "E003-M17 provides real RGB-D/open-vocabulary detector input staging.",
                "E003-M17 does not provide detector predictions or real perception metrics.",
            ],
            "unsupported": [
                "real RGB-D perception robustness",
                "open-vocabulary detector robustness",
                "real navigation SR/SPL",
                "deployable search policy",
            ],
        },
        "next_recommended_unit": "E003-M18 Dockerized real-proposal detector scaffold",
    }


def build_coverage(
    out_dir: Path,
    ready_scan_rows: list[dict[str, Any]],
    query_manifest_rows: list[dict[str, Any]],
    object_target_rows: list[dict[str, Any]],
    prompt_set: dict[str, Any],
    schema_copied: bool,
    staging_decision: dict[str, Any],
) -> dict[str, Any]:
    evaluation_targets = [row for row in object_target_rows if row["evaluation_target_enabled"]]
    detector_targets = [row for row in object_target_rows if row["detector_prompt_enabled"]]
    status = "real_proposal_denominator_staged"
    if not query_manifest_rows or not schema_copied or not prompt_set["labels"]:
        status = "review_needed"
    return {
        "staging_version": STAGING_VERSION,
        "status": status,
        "source_route": "sequence_ready_scan_bootstrap",
        "ready_scan_rows": len(ready_scan_rows),
        "query_manifest_rows": len(query_manifest_rows),
        "object_target_rows": len(object_target_rows),
        "detector_target_rows": len(detector_targets),
        "evaluation_target_rows": len(evaluation_targets),
        "prompt_label_count": prompt_set["label_count"],
        "detector_target_label_count": prompt_set["detector_target_label_count"],
        "schema_copied": schema_copied,
        "paper_table_command_ready": staging_decision["paper_table_command_ready"],
        "detector_predictions_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "docker_required_for_m17": False,
        "docker_required_for_next_detector": True,
        "docker_reason": "E003-M17 stages detector inputs with repository-local JSON artifacts; E003-M18 detector execution must use Docker.",
        "next_recommended_unit": staging_decision["next_recommended_unit"],
        "outputs": {
            "real_proposal_query_manifest": str(out_dir / "real_proposal_query_manifest.jsonl"),
            "real_proposal_object_targets": str(out_dir / "real_proposal_object_targets.jsonl"),
            "scan_target_summary": str(out_dir / "scan_target_summary.jsonl"),
            "prompt_set": str(out_dir / "prompt_set.json"),
            "proposal_output_schema": str(out_dir / "proposal_output_schema.json"),
            "staging_decision": str(out_dir / "staging_decision.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    out_dir: Path,
    coverage: dict[str, Any],
    staging_decision: dict[str, Any],
    scan_summary_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# E003-M17 Real Proposal Denominator Staging",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Source route: `{coverage['source_route']}`",
        f"- Ready scan rows: {coverage['ready_scan_rows']}",
        f"- Query manifest rows: {coverage['query_manifest_rows']}",
        f"- Object target rows: {coverage['object_target_rows']}",
        f"- Detector target rows: {coverage['detector_target_rows']}",
        f"- Evaluation target rows: {coverage['evaluation_target_rows']}",
        f"- Prompt label count: {coverage['prompt_label_count']}",
        f"- Detector target label count: {coverage['detector_target_label_count']}",
        f"- Proposal schema copied: {coverage['schema_copied']}",
        f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
        f"- Detector predictions ready: {coverage['detector_predictions_ready']}",
        f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
        f"- Docker required for M17: {coverage['docker_required_for_m17']}",
        f"- Docker required for next detector: {coverage['docker_required_for_next_detector']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Scan Summary",
        "",
        "| Scan | frames | sampled | objects | detector targets | evaluation targets |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in scan_summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['scan_id']}`",
                    str(row["frame_triplet_lower_bound"]),
                    str(row["sampled_frame_count"]),
                    str(row["object_target_count"]),
                    str(row["detector_target_count"]),
                    str(row["evaluation_target_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M17 supports real RGB-D/open-vocabulary detector input staging.",
            "- E003-M17 supports saying that sequence-ready 3RScan scans can now be passed to a Dockerized detector using a fixed manifest, prompt set, and output schema.",
            "- E003-M17 does not support real perception robustness results because detector predictions have not been generated.",
            "",
            "## 에이전트 추론",
            "",
            "- This staging intentionally rebuilds the real-proposal denominator from sequence-ready scans because current E001 rescans have no sequence-ready rows.",
            "- Object targets are split into detector targets, structural context, and generic context so prompt labels do not silently define the evaluation denominator.",
            "- The next step should create or select the Dockerized detector scaffold before any paper-table command is considered ready.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M17. Next recommended unit: `{staging_decision['next_recommended_unit']}`.",
            "",
            "## Outputs",
            "",
            "- `real_proposal_query_manifest.jsonl`",
            "- `real_proposal_object_targets.jsonl`",
            "- `scan_target_summary.jsonl`",
            "- `prompt_set.json`",
            "- `proposal_output_schema.json`",
            "- `staging_decision.json`",
            "- `coverage.json`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--m16-dir", type=Path, default=DEFAULT_M16_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m16_coverage = load_json(args.m16_dir / "coverage.json")
    m16_schema_path = args.m16_dir / "proposal_output_schema.json"
    proposal_schema = load_json(m16_schema_path)
    scan_gate_rows = load_jsonl(args.m16_dir / "scan_alignment_gate_rows.jsonl")
    ready_scan_rows = [row for row in scan_gate_rows if row["proposal_alignment_scan_ready"]]
    objects_by_scan = object_scan_index(args.dataset_root / "3DSSG" / "objects.json")

    object_target_rows = build_object_target_rows(ready_scan_rows, objects_by_scan)
    query_manifest_rows = build_query_manifest_rows(ready_scan_rows, object_target_rows)
    prompt_set = build_prompt_set(object_target_rows)
    scan_summary_rows = build_scan_summary_rows(query_manifest_rows, object_target_rows)

    write_json(args.out_dir / "proposal_output_schema.json", proposal_schema)
    schema_copied = (args.out_dir / "proposal_output_schema.json").exists()
    staging_decision = build_staging_decision(
        query_manifest_rows,
        object_target_rows,
        prompt_set,
        m16_coverage,
    )
    coverage = build_coverage(
        args.out_dir,
        ready_scan_rows,
        query_manifest_rows,
        object_target_rows,
        prompt_set,
        schema_copied,
        staging_decision,
    )
    report = build_report(args.out_dir, coverage, staging_decision, scan_summary_rows)

    write_jsonl(args.out_dir / "real_proposal_query_manifest.jsonl", query_manifest_rows)
    write_jsonl(args.out_dir / "real_proposal_object_targets.jsonl", object_target_rows)
    write_jsonl(args.out_dir / "scan_target_summary.jsonl", scan_summary_rows)
    write_json(args.out_dir / "prompt_set.json", prompt_set)
    write_json(args.out_dir / "staging_decision.json", staging_decision)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": coverage["status"], "out_dir": str(args.out_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
