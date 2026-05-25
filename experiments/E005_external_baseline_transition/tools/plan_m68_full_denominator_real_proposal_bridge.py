#!/usr/bin/env python3
"""Build the E005-M68 full-denominator real proposal bridge plan."""

from __future__ import annotations

import json
import math
import shlex
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
DATASET_ROOT = ROOT / "local_dataset"
SCANS_ROOT = DATASET_ROOT / "3RScan" / "scans"
M45_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
M45_METRIC_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M67_COVERAGE = EXP_ROOT / "artifacts" / "E005-M67_real_rgbd_ov_robustness_route_v0" / "coverage.json"
M73_SCHEMA = E003_ROOT / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0" / "proposal_output_schema.json"
M75_COVERAGE = E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0" / "coverage.json"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M69_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
VERSION = "e005_m68_full_denominator_real_proposal_bridge_plan_v0"

MAX_FRAMES_PER_SCAN = 24
MAX_PREDICTIONS_PER_FRAME = 100
RAW_CANDIDATE_COLLECTION_CAP = 400000
THRESHOLD = "0.08"
TEXT_THRESHOLD = "0.08"
TMUX_PREFIX = "e005_m69_real_proposal"

BATCH_QUERY_FILES = {
    "heldout_b01": M45_CONTRACT_DIR / "heldout_b01_query_rows.jsonl",
    "heldout_b02": M45_CONTRACT_DIR / "heldout_b02_query_rows.jsonl",
    "heldout_b03": M45_CONTRACT_DIR / "heldout_b03_query_rows.jsonl",
}
BATCH_TARGET_FILES = {
    "heldout_b01": M45_METRIC_DIR / "target_rows.jsonl",
    "heldout_b02": M45_METRIC_DIR / "target_rows_heldout_b02.jsonl",
    "heldout_b03": M45_METRIC_DIR / "target_rows_heldout_b03.jsonl",
}

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
    "stool": ["chair"],
    "trash can": ["waste bin"],
    "tv": ["television"],
    "tv stand": ["television stand"],
}


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


def frame_sampling(frame_count: int) -> dict[str, Any]:
    if frame_count <= 0:
        return {
            "frame_sampling_strategy": "none",
            "frame_stride": None,
            "max_frames": MAX_FRAMES_PER_SCAN,
            "sampled_frame_count": 0,
            "sampled_frame_indices": [],
        }
    stride = max(1, math.ceil(frame_count / MAX_FRAMES_PER_SCAN))
    indices = list(range(0, frame_count, stride))[:MAX_FRAMES_PER_SCAN]
    return {
        "frame_sampling_strategy": "uniform_stride",
        "frame_stride": stride,
        "max_frames": MAX_FRAMES_PER_SCAN,
        "sampled_frame_count": len(indices),
        "sampled_frame_indices": indices,
    }


def scan_payload_status(scan_id: str) -> dict[str, Any]:
    scan_dir = SCANS_ROOT / scan_id
    sequence_dir = scan_dir / "sequence"
    color_count = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.exists() else 0
    depth_count = len(list(sequence_dir.glob("*.depth.pgm"))) if sequence_dir.exists() else 0
    pose_count = len(list(sequence_dir.glob("*.pose.txt"))) if sequence_dir.exists() else 0
    frame_count = min(color_count, depth_count, pose_count)
    semantic_ready = (
        (scan_dir / "labels.instances.annotated.v2.ply").exists()
        and (scan_dir / "semseg.v2.json").exists()
        and (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists()
    )
    return {
        "color_frames": color_count,
        "depth_frames": depth_count,
        "frame_triplet_lower_bound": frame_count,
        "ply_path": str(scan_dir / "labels.instances.annotated.v2.ply"),
        "pose_frames": pose_count,
        "scan_dir": str(scan_dir),
        "scan_id": scan_id,
        "semantic_triplet_ready": semantic_ready,
        "sequence_dir_ready": sequence_dir.exists() and frame_count > 0,
        "sequence_zip_path": str(scan_dir / "sequence.zip"),
    }


def load_batch_query_rows() -> dict[str, list[dict[str, Any]]]:
    return {batch_id: read_jsonl(path) for batch_id, path in BATCH_QUERY_FILES.items()}


def load_batch_target_rows() -> dict[str, list[dict[str, Any]]]:
    return {batch_id: read_jsonl(path) for batch_id, path in BATCH_TARGET_FILES.items()}


def normalize_query_rows(batch_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for batch_id, batch in sorted(batch_rows.items()):
        for row in batch:
            query_uid = str(row["bridge_query_uid"])
            if query_uid in seen:
                raise RuntimeError(f"duplicate query uid: {query_uid}")
            seen.add(query_uid)
            label = str(row["label_canonical"])
            normalized = dict(row)
            normalized.update(
                {
                    "bridge_query_uid": query_uid,
                    "bridge_role": "m68_full_denominator_real_proposal_query",
                    "m68_batch_id": batch_id,
                    "m68_version": VERSION,
                    "prompt_role": prompt_role(label),
                    "allowed_for_detector": ["current_rescan_id", "label_canonical", "prompt_set", "RGB-D sequence"],
                    "blocked_for_detector": [
                        "target_uid",
                        "object_instance_id_rescan",
                        "candidate_is_target",
                        "matched_3dssg_instance_id",
                        "task outcome labels",
                    ],
                    "real_rgbd_open_vocab_robustness_claim_ready": False,
                    "real_navigation_sr_spl_ready": False,
                }
            )
            rows.append(normalized)
    return sorted(rows, key=lambda row: (row["m68_batch_id"], row["current_rescan_id"], row["row_uid"]))


def normalize_object_targets(batch_targets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows_by_target: dict[str, dict[str, Any]] = {}
    for batch_id, batch in sorted(batch_targets.items()):
        for row in batch:
            target_uid = str(row["target_uid"])
            if target_uid in rows_by_target:
                raise RuntimeError(f"duplicate target uid across batches: {target_uid}")
            normalized = dict(row)
            label = str(row["label_canonical"])
            normalized.update(
                {
                    "aliases": aliases_for_label(label),
                    "detector_prompt_enabled": prompt_role(label) == "detector_target",
                    "evaluation_target_enabled": bool(row.get("semseg_present")) and prompt_role(label) == "detector_target",
                    "m68_batch_id": batch_id,
                    "m68_version": VERSION,
                    "prompt_role": prompt_role(label),
                    "source_target_file": str(BATCH_TARGET_FILES[batch_id]),
                }
            )
            rows_by_target[target_uid] = normalized
    return sorted(rows_by_target.values(), key=lambda row: (row["m68_batch_id"], row["scan_id"], row["target_uid"]))


def build_prompt_set(object_rows: list[dict[str, Any]], *, batch_id: str = "all") -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in object_rows:
        if row["detector_prompt_enabled"]:
            grouped[str(row["label_canonical"])].append(row)
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
        "batch_id": batch_id,
        "detector_profile_id": "open_vocab_rgbd_detector_v0",
        "detector_target_label_count": len(labels),
        "label_count": len(labels),
        "labels": labels,
        "m68_version": VERSION,
        "prompt_policy": "prompt detector-ready labels from the M38/M45 heldout denominator",
        "prompt_set_id": f"e005_m68_full_denominator_prompts_v0:{batch_id}",
        "source": "E005-M45 heldout query rows and target rows",
    }


def build_scan_manifest(query_rows: list[dict[str, Any]], object_rows: list[dict[str, Any]], *, batch_id: str) -> list[dict[str, Any]]:
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    objects_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        rows_by_scan[str(row["current_rescan_id"])].append(row)
    for row in object_rows:
        objects_by_scan[str(row["scan_id"])].append(row)

    manifest: list[dict[str, Any]] = []
    for scan_id, rows in sorted(rows_by_scan.items()):
        status = scan_payload_status(scan_id)
        sampling = frame_sampling(int(status["frame_triplet_lower_bound"]))
        labels = sorted({str(row["label_canonical"]) for row in rows})
        object_targets = [row for row in objects_by_scan.get(scan_id, []) if row["evaluation_target_enabled"]]
        manifest.append(
            {
                **status,
                **sampling,
                "batch_id": batch_id,
                "bridge_query_row_count": len(rows),
                "bridge_query_target_count": len({row["target_uid"] for row in rows}),
                "detector_config_id": "h001_full_denominator_groundingdino_tiny_rgbd_backproject_v0",
                "detector_profile_id": "open_vocab_rgbd_detector_v0",
                "evaluation_target_count": len(object_targets),
                "frame_id_format": "frame-%06d",
                "manifest_row_uid": f"m68-full-denominator:{batch_id}:{scan_id}",
                "object_target_count": len(object_targets),
                "object_target_path": "/inputs/real_proposal_object_targets.jsonl",
                "paper_table_role": "full_denominator_real_proposal_bridge_input_not_final_result",
                "prompt_set_id": f"e005_m68_full_denominator_prompts_v0:{batch_id}",
                "prompt_set_path": "/inputs/prompt_set.json",
                "proposal_output_schema_id": "real_proposal_prediction_jsonl_v0",
                "proposal_output_schema_path": "/inputs/proposal_output_schema.json",
                "route_id": "scale_real_proposal_bridge_to_m38_heldout_denominator",
                "target_label_count": len(labels),
                "target_labels": labels,
            }
        )
    return manifest


def detector_command_plan(input_dir: Path, output_dir: Path, *, batch_id: str, scan_count: int, label_count: int) -> dict[str, Any]:
    max_predictions = max(20000, scan_count * max(label_count, 1) * MAX_FRAMES_PER_SCAN * MAX_PREDICTIONS_PER_FRAME)
    exact_command = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--m17-dir",
        str(input_dir),
        "--out-dir",
        str(output_dir),
        "--max-scans",
        str(scan_count),
        "--max-frames-per-scan",
        str(MAX_FRAMES_PER_SCAN),
        "--max-labels",
        str(label_count),
        "--max-predictions",
        str(max_predictions),
        "--max-predictions-per-frame",
        str(MAX_PREDICTIONS_PER_FRAME),
        "--threshold",
        THRESHOLD,
        "--text-threshold",
        TEXT_THRESHOLD,
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        str(RAW_CANDIDATE_COLLECTION_CAP),
        "--export-pre-cap-candidate-pool",
        "--build",
        "--docker-sudo",
        "--sudo-password-stdin",
    ]
    log_template = f"logs/<YYYYMMDD_HHMMSS>_e005_m69_real_proposal_{batch_id}.log"
    return {
        "batch_id": batch_id,
        "command_id": f"e005_m69_real_proposal_detector_run_command_v0:{batch_id}",
        "exact_command": exact_command,
        "expected_files": [
            str(output_dir / "coverage.json"),
            str(output_dir / "container_output" / "real_proposals.jsonl"),
            str(output_dir / "matching" / "coverage.json"),
            str(output_dir / "validator" / "coverage.json"),
        ],
        "input_dir": str(input_dir),
        "label_count": label_count,
        "long_running_policy": "launch in tmux with timestamped log under logs/",
        "max_predictions": max_predictions,
        "next_unit_after_detector_run": "E005-M70 full-denominator real proposal completion verification and metric conversion",
        "output_dir": str(output_dir),
        "scan_count": scan_count,
        "shell_command": shlex.join(exact_command),
        "tmux_session": f"{TMUX_PREFIX}_{batch_id}",
        "tmux_template": (
            f"tmux new-session -d -s {TMUX_PREFIX}_{batch_id} "
            f"'cd {ROOT} && <sudo-password-provider> {shlex.join(exact_command)} > {log_template} 2>&1'"
        ),
        "verification_command": [
            "python",
            "experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py",
            "--predictions",
            str(output_dir / "container_output" / "real_proposals.jsonl"),
            "--manifest",
            str(input_dir / "real_proposal_query_manifest.jsonl"),
            "--targets",
            str(input_dir / "real_proposal_object_targets.jsonl"),
            "--schema",
            str(input_dir / "proposal_output_schema.json"),
            "--out-dir",
            str(output_dir / "validator"),
            "--schema-only-smoke",
        ],
        "working_directory": str(ROOT),
    }


def materialize_input_dir(
    input_dir: Path,
    query_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    prompt_set: dict[str, Any],
) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(input_dir / "direct_bridge_query_rows.jsonl", query_rows)
    write_jsonl(input_dir / "real_proposal_query_manifest.jsonl", manifest_rows)
    write_jsonl(input_dir / "real_proposal_object_targets.jsonl", target_rows)
    write_json(input_dir / "prompt_set.json", prompt_set)
    shutil.copyfile(M73_SCHEMA, input_dir / "proposal_output_schema.json")


def build_batch_rows(
    all_query_rows: list[dict[str, Any]],
    all_object_rows: list[dict[str, Any]],
    batch_ids: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch_id in batch_ids:
        query_rows = [row for row in all_query_rows if row["m68_batch_id"] == batch_id]
        object_rows = [row for row in all_object_rows if row["m68_batch_id"] == batch_id]
        manifest_rows = build_scan_manifest(query_rows, object_rows, batch_id=batch_id)
        prompt_set = build_prompt_set(object_rows, batch_id=batch_id)
        input_dir = OUT_DIR / "batches" / batch_id
        output_dir = M69_OUT_DIR / batch_id
        materialize_input_dir(input_dir, query_rows, object_rows, manifest_rows, prompt_set)
        command = detector_command_plan(
            input_dir,
            output_dir,
            batch_id=batch_id,
            scan_count=len(manifest_rows),
            label_count=int(prompt_set["label_count"]),
        )
        write_json(input_dir / "detector_run_command_plan.json", command)
        rows.append(
            {
                "batch_id": batch_id,
                "command_plan": str(input_dir / "detector_run_command_plan.json"),
                "input_dir": str(input_dir),
                "label_count": int(prompt_set["label_count"]),
                "object_target_rows": len(object_rows),
                "output_dir": str(output_dir),
                "query_rows": len(query_rows),
                "ready_scan_count": sum(
                    1 for row in manifest_rows if row["semantic_triplet_ready"] and row["sequence_dir_ready"]
                ),
                "sampled_frame_count": sum(int(row["sampled_frame_count"]) for row in manifest_rows),
                "scan_count": len(manifest_rows),
                "tmux_session": command["tmux_session"],
            }
        )
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M68 Full-Denominator Real Proposal Bridge Plan",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Query rows: {coverage['query_rows']}.",
            f"- Scan count: {coverage['scan_count']}; ready scans: {coverage['ready_scan_count']}.",
            f"- Object target rows: {coverage['object_target_rows']}.",
            f"- Prompt labels: {coverage['prompt_label_count']}.",
            f"- Sampled frame count: {coverage['sampled_frame_count']}.",
            f"- Batch count: {coverage['batch_count']}.",
            f"- Row-level overlap with E003-M75: {coverage['row_level_overlap_with_m75_rows']}.",
            "",
            "## Claim Boundary",
            "",
            "- M68 is a plan and input-materialization step, not a performance result.",
            "- Final real RGB-D/open-vocabulary robustness remains false until M69/M70 detector run and query-level metric conversion are complete.",
            "- Real navigation `SR` / `SPL` remains blocked.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m67 = read_json(M67_COVERAGE)
    m75 = read_json(M75_COVERAGE)
    if m67.get("status") != "e005_m67_real_rgbd_ov_robustness_route_ready":
        raise RuntimeError(f"M67 is not ready: {m67.get('status')}")
    if not M73_SCHEMA.exists():
        raise RuntimeError(f"missing proposal schema: {M73_SCHEMA}")

    batch_query_rows = load_batch_query_rows()
    batch_target_rows = load_batch_target_rows()
    batch_ids = sorted(batch_query_rows)
    all_query_rows = normalize_query_rows(batch_query_rows)
    all_object_rows = normalize_object_targets(batch_target_rows)
    all_manifest_rows = build_scan_manifest(all_query_rows, all_object_rows, batch_id="all")
    all_prompt_set = build_prompt_set(all_object_rows, batch_id="all")
    full_input_dir = OUT_DIR / "full_denominator_inputs"
    materialize_input_dir(full_input_dir, all_query_rows, all_object_rows, all_manifest_rows, all_prompt_set)

    full_command = detector_command_plan(
        full_input_dir,
        M69_OUT_DIR / "all",
        batch_id="all",
        scan_count=len(all_manifest_rows),
        label_count=int(all_prompt_set["label_count"]),
    )
    write_json(full_input_dir / "detector_run_command_plan.json", full_command)
    batch_rows = build_batch_rows(all_query_rows, all_object_rows, batch_ids)
    scan_status_rows = [scan_payload_status(row["scan_id"]) for row in all_manifest_rows]
    scan_ready = [
        row for row in all_manifest_rows if row["semantic_triplet_ready"] and row["sequence_dir_ready"]
    ]

    m75_row_uids = {
        str(row.get("row_uid"))
        for row in read_jsonl(E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0" / "query_bridge_rows.jsonl")
    }
    m68_row_uids = {str(row.get("row_uid")) for row in all_query_rows}
    row_overlap = len(m68_row_uids & m75_row_uids)

    coverage = {
        "status": "e005_m68_full_denominator_real_proposal_bridge_plan_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_dir": str(OUT_DIR),
        "batch_count": len(batch_rows),
        "detector_run_launched": False,
        "full_input_dir": str(full_input_dir),
        "full_output_dir": str(M69_OUT_DIR / "all"),
        "m67_selected_route": m67.get("selected_route"),
        "m75_query_rows": m75.get("direct_bridge_query_rows"),
        "next_recommended_unit": "E005-M69 full-denominator real proposal detector batch launch",
        "object_target_rows": len(all_object_rows),
        "prompt_label_count": int(all_prompt_set["label_count"]),
        "query_rows": len(all_query_rows),
        "ready_scan_count": len(scan_ready),
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "row_level_overlap_with_m75_rows": row_overlap,
        "sampled_frame_count": sum(int(row["sampled_frame_count"]) for row in all_manifest_rows),
        "scan_count": len(all_manifest_rows),
        "scan_ids": [row["scan_id"] for row in all_manifest_rows],
        "target_uid_count": len({row["target_uid"] for row in all_query_rows}),
    }
    if len(all_query_rows) != 195:
        raise RuntimeError(f"unexpected query rows: {len(all_query_rows)}")
    if len(all_manifest_rows) != 9:
        raise RuntimeError(f"unexpected scan count: {len(all_manifest_rows)}")
    if len(scan_ready) != len(all_manifest_rows):
        coverage["status"] = "e005_m68_full_denominator_real_proposal_bridge_plan_blocked_payload_missing"

    write_jsonl(OUT_DIR / "direct_bridge_query_rows.jsonl", all_query_rows)
    write_jsonl(OUT_DIR / "real_proposal_query_manifest.jsonl", all_manifest_rows)
    write_jsonl(OUT_DIR / "real_proposal_object_targets.jsonl", all_object_rows)
    write_jsonl(OUT_DIR / "scan_payload_status.jsonl", scan_status_rows)
    write_jsonl(OUT_DIR / "batch_plan_rows.jsonl", batch_rows)
    write_json(OUT_DIR / "prompt_set.json", all_prompt_set)
    write_json(OUT_DIR / "detector_run_command_plan.json", full_command)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
