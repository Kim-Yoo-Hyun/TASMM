#!/usr/bin/env python3
"""Plan ConceptGraphs heldout runtime after heldout sequence staging."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "E005_external_baseline_transition"
M38_DIR = EXP_DIR / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
M40_DIR = EXP_DIR / "artifacts" / "E005-M40_heldout_sequence_staging_verification_v0"
OUT_DIR = EXP_DIR / "artifacts" / "E005-M41_conceptgraphs_heldout_runtime_preflight_v0"
SCANS_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
CONFIG_PATH = STAGED_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml"
MODEL_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache"
GSA_CACHE = MODEL_CACHE / "gsa"
IMAGE = "research2/conceptgraphs-smoke:latest"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"
DEPTH_ALIGNED_SIZE = (224, 172)


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


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout)
        return {
            "cmd": cmd,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "ok": False, "returncode": None, "stderr": repr(exc), "stdout": ""}


def docker_image_ready() -> bool:
    return run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)["ok"]


def image_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        with Image.open(path) as image:
            return {"exists": True, "height": image.size[1], "mode": image.mode, "width": image.size[0]}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "exists": True}


def parse_depth_intrinsic(info_path: Path) -> dict[str, Any]:
    if not info_path.exists():
        return {"exists": False}
    values: list[float] | None = None
    for line in info_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("m_calibrationDepthIntrinsic"):
            _, raw = line.split("=", 1)
            values = [float(token) for token in raw.split()]
            break
    if not values or len(values) < 11:
        return {"exists": True, "parse_ready": False}
    return {
        "exists": True,
        "fx": values[0],
        "fy": values[5],
        "cx": values[2],
        "cy": values[6],
        "parse_ready": True,
    }


def count_raw_sequence(scan_id: str) -> dict[str, Any]:
    scan_dir = SCANS_ROOT / scan_id
    sequence_dir = scan_dir / "sequence"
    color_files = sorted(sequence_dir.glob("*.color.jpg")) if sequence_dir.exists() else []
    depth_files = sorted(sequence_dir.glob("*.depth.pgm")) if sequence_dir.exists() else []
    pose_files = sorted(sequence_dir.glob("*.pose.txt")) if sequence_dir.exists() else []
    return {
        "raw_color_frames": len(color_files),
        "raw_depth_frames": len(depth_files),
        "raw_frame_triplet_lower_bound": min(len(color_files), len(depth_files), len(pose_files)),
        "raw_pose_frames": len(pose_files),
        "raw_sample_color": image_info(color_files[0]) if color_files else {"exists": False},
        "raw_sample_depth": image_info(depth_files[0]) if depth_files else {"exists": False},
        "scan_dir": str(scan_dir),
        "sequence_dir": str(sequence_dir),
        "sequence_dir_ready": sequence_dir.exists() and bool(color_files and depth_files and pose_files),
        "sequence_info_path": str(sequence_dir / "_info.txt"),
        "sequence_zip_path": str(scan_dir / "sequence.zip"),
        "sequence_zip_ready": (scan_dir / "sequence.zip").exists(),
        "source_intrinsic_depth": parse_depth_intrinsic(sequence_dir / "_info.txt"),
    }


def count_staged(scan_id: str) -> dict[str, Any]:
    scan_root = STAGED_ROOT / scan_id
    color_files = sorted((scan_root / "color").glob("*.jpg")) if scan_root.exists() else []
    depth_files = sorted((scan_root / "depth").glob("*.png")) if scan_root.exists() else []
    pose_files = sorted((scan_root / "pose").glob("*.txt")) if scan_root.exists() else []
    full_pcd = scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"
    full_pcd_post = scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"
    gsa_count = len(list((scan_root / "gsa_detections_none").glob("*.pkl.gz"))) if scan_root.exists() else 0
    staged_payload_ready = (
        scan_root.exists()
        and len(color_files) > 0
        and len(color_files) == len(depth_files) == len(pose_files)
        and (scan_root / "intrinsic" / "intrinsic_color.txt").exists()
        and (scan_root / "intrinsic" / "intrinsic_depth.txt").exists()
    )
    return {
        "conceptgraphs_runtime_output_ready": full_pcd.exists() and full_pcd_post.exists(),
        "gsa_detection_count": gsa_count,
        "runtime_full_pcd": str(full_pcd),
        "runtime_full_pcd_post": str(full_pcd_post),
        "staged_color_jpg_count": len(color_files),
        "staged_depth_png_count": len(depth_files),
        "staged_frame_triplet_lower_bound": min(len(color_files), len(depth_files), len(pose_files)),
        "staged_intrinsic_color_exists": (scan_root / "intrinsic" / "intrinsic_color.txt").exists(),
        "staged_intrinsic_depth_exists": (scan_root / "intrinsic" / "intrinsic_depth.txt").exists(),
        "staged_payload_ready": staged_payload_ready,
        "staged_pose_txt_count": len(pose_files),
        "staged_scan_dir": str(scan_root),
        "staged_scan_dir_exists": scan_root.exists(),
    }


def heldout_scan_rows() -> list[dict[str, Any]]:
    m38_rows = load_jsonl(M38_DIR / "scan_rows.jsonl")
    m40 = load_json(M40_DIR / "coverage.json")
    m40_ready_scan_ids = set(m40["target_scan_ids"])
    rows: list[dict[str, Any]] = []
    for row in m38_rows:
        if row.get("split") != "heldout_sequence_required":
            continue
        scan_id = str(row["scan_id"])
        raw = count_raw_sequence(scan_id)
        staged = count_staged(scan_id)
        staging_required = not staged["staged_payload_ready"]
        runtime_required = not staged["conceptgraphs_runtime_output_ready"]
        rows.append(
            {
                "base_target_rows": int(row.get("eligible_base_target_rows", row.get("base_target_rows", 0))),
                "eligible_query_rows": int(row.get("eligible_query_rows", 0)),
                "expected_output_full_pcd": staged["runtime_full_pcd"],
                "expected_output_full_pcd_post": staged["runtime_full_pcd_post"],
                "heldout_sequence_ready_by_m40": scan_id in m40_ready_scan_ids,
                "label_count": int(row.get("eligible_label_count", row.get("label_count", 0))),
                "label_counts": row.get("eligible_label_counts", row.get("label_counts", {})),
                "runtime_required": runtime_required,
                "scan_id": scan_id,
                "split": row.get("split"),
                "staging_required": staging_required,
                **raw,
                **staged,
            }
        )
    return sorted(rows, key=lambda item: item["scan_id"])


def batch_rows(scan_ids: list[str], batch_size: int = 3) -> list[dict[str, Any]]:
    rows = []
    for batch_idx, start in enumerate(range(0, len(scan_ids), batch_size), start=1):
        ids = scan_ids[start : start + batch_size]
        rows.append(
            {
                "batch_id": f"heldout_b{batch_idx:02d}",
                "expected_log_pattern": f"logs/<timestamp>_e005_m43_conceptgraphs_heldout_runtime_b{batch_idx:02d}.log",
                "scan_count": len(ids),
                "scan_ids": ids,
                "tmux_session": f"e005_m43_conceptgraphs_heldout_runtime_b{batch_idx:02d}",
            }
        )
    return rows


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]], batches: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M41 ConceptGraphs Heldout Runtime Preflight",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Heldout scans: {coverage['heldout_scan_count']}.",
        f"- M40 sequence-ready scans: {coverage['m40_ready_scan_count']} / {coverage['heldout_scan_count']}.",
        f"- ConceptGraphs staged payload ready scans: {coverage['staged_payload_ready_scan_count']} / {coverage['heldout_scan_count']}.",
        f"- Runtime output ready scans: {coverage['runtime_output_ready_scan_count']} / {coverage['heldout_scan_count']}.",
        f"- Raw frame triplet lower bound total: {coverage['raw_frame_triplet_lower_bound_total']}.",
        f"- Staging required scans: {coverage['staging_required_scan_count']}.",
        f"- Runtime launch ready now: {str(coverage['runtime_launch_ready_now']).lower()}.",
        f"- Docker image ready: {str(coverage['docker_image_ready']).lower()}.",
        f"- Model checkpoints ready: {str(coverage['model_checkpoints_ready']).lower()}.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}`: sequence {seq_ready}, staged {staged}, runtime output {runtime}, raw triplets {raw_triplets}, "
            "staged triplets {staged_triplets}, labels {label_count}, query rows {query_rows}.".format(
                scan_id=row["scan_id"],
                seq_ready=str(row["heldout_sequence_ready_by_m40"]).lower(),
                staged=str(row["staged_payload_ready"]).lower(),
                runtime=str(row["conceptgraphs_runtime_output_ready"]).lower(),
                raw_triplets=row["raw_frame_triplet_lower_bound"],
                staged_triplets=row["staged_frame_triplet_lower_bound"],
                label_count=row["label_count"],
                query_rows=row["eligible_query_rows"],
            )
        )
    lines.extend(["", "## Runtime Batch Plan", ""])
    for batch in batches:
        lines.append(
            f"- `{batch['batch_id']}`: scans {batch['scan_count']}, tmux `{batch['tmux_session']}`, ids {batch['scan_ids']}."
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M41 is a preflight and launch-plan gate only.",
            "- It does not launch heldout `ConceptGraphs` runtime.",
            "- It does not support heldout performance, final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.",
            "",
            "## Agent Inference",
            "",
            "- The immediate blocker is `ConceptGraphs` staged-layout materialization for heldout scans, not sequence payload acquisition.",
            "- Runtime should be launched in bounded batches after staging materialization, because each scan runs GPU-heavy `GSA` and `cfslam` steps.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m40 = load_json(M40_DIR / "coverage.json")
    scan_rows = heldout_scan_rows()
    scan_ids = [row["scan_id"] for row in scan_rows]
    runtime_scan_ids = [row["scan_id"] for row in scan_rows if row["runtime_required"]]
    staging_required_scan_ids = [row["scan_id"] for row in scan_rows if row["staging_required"]]
    label_counter: Counter[str] = Counter()
    for row in scan_rows:
        label_counter.update({str(k): int(v) for k, v in row.get("label_counts", {}).items()})
    docker_ready = docker_image_ready()
    model_checkpoints_ready = (
        (GSA_CACHE / "sam_vit_h_4b8939.pth").exists()
        and (GSA_CACHE / "groundingdino_swint_ogc.pth").exists()
    )
    staged_payload_ready_count = sum(1 for row in scan_rows if row["staged_payload_ready"])
    runtime_ready_count = sum(1 for row in scan_rows if row["conceptgraphs_runtime_output_ready"])
    m40_ready_count = sum(1 for row in scan_rows if row["heldout_sequence_ready_by_m40"])
    runtime_launch_ready = (
        m40.get("status") == "e005_m40_heldout_sequence_staging_ready"
        and m40_ready_count == len(scan_rows)
        and staged_payload_ready_count == len(scan_rows)
        and runtime_ready_count < len(scan_rows)
        and docker_ready
        and model_checkpoints_ready
        and CONFIG_PATH.exists()
    )
    status = (
        "e005_m41_heldout_runtime_preflight_ready_for_launch"
        if runtime_launch_ready
        else "e005_m41_heldout_runtime_preflight_ready_with_staging_required"
    )
    coverage = {
        "blocked_claims": [
            "No heldout ConceptGraphs runtime performance yet.",
            "No final external baseline performance yet.",
            "No final real RGB-D/open-vocabulary robustness yet.",
            "No real navigation SR/SPL yet.",
        ],
        "conceptgraphs_config_exists": CONFIG_PATH.exists(),
        "docker_image": IMAGE,
        "docker_image_ready": docker_ready,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "heldout_query_rows_after_exclusion": m40["heldout_query_rows_after_exclusion"],
        "heldout_scan_count": len(scan_rows),
        "label_count": len(label_counter),
        "label_counts": dict(sorted(label_counter.items())),
        "m40_ready_scan_count": m40_ready_count,
        "m41_version": "e005_m41_conceptgraphs_heldout_runtime_preflight_v0",
        "model_checkpoints_ready": model_checkpoints_ready,
        "next_recommended_unit": (
            "E005-M42 ConceptGraphs heldout staging materialization"
            if staging_required_scan_ids
            else "E005-M43 ConceptGraphs heldout runtime batch launch"
        ),
        "paper_table_claim_ready": False,
        "raw_frame_triplet_lower_bound_total": sum(row["raw_frame_triplet_lower_bound"] for row in scan_rows),
        "runtime_launch_ready_now": runtime_launch_ready,
        "runtime_output_ready_scan_count": runtime_ready_count,
        "runtime_required_scan_count": len(runtime_scan_ids),
        "runtime_required_scan_ids": runtime_scan_ids,
        "runtime_strategy": "bounded_3scan_batches_after_staging_materialization",
        "staged_payload_ready_scan_count": staged_payload_ready_count,
        "staged_root": str(STAGED_ROOT),
        "staging_required_scan_count": len(staging_required_scan_ids),
        "staging_required_scan_ids": staging_required_scan_ids,
        "status": status,
    }
    batches = batch_rows(runtime_scan_ids, batch_size=3)
    staging_plan = {
        "claim_boundary": "staging-only; no performance claim",
        "depth_output_format": "png",
        "frame_id_rule": "frame-000000.* -> 000000.*",
        "input_sequence_root": str(SCANS_ROOT),
        "output_staged_root": str(STAGED_ROOT),
        "requires_color_resize_to_depth_resolution": True,
        "requires_depth_pgm_to_png_conversion": True,
        "requires_pose_copy": True,
        "target_color_size": {"height": DEPTH_ALIGNED_SIZE[1], "width": DEPTH_ALIGNED_SIZE[0]},
        "target_scan_ids": staging_required_scan_ids,
        "write_intrinsic_from_sequence_info": True,
    }
    runtime_plan = {
        "batch_rows": batches,
        "dataset_config": str(CONFIG_PATH),
        "dataset_root": str(STAGED_ROOT),
        "image": IMAGE,
        "runtime_launch_ready_now": runtime_launch_ready,
        "save_suffix": SAVE_SUFFIX,
        "scan_ids": runtime_scan_ids,
        "selected_class_set": "none",
        "selected_device": "cuda",
        "selected_stride": 5,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "heldout_runtime_scan_rows.jsonl", scan_rows)
    write_jsonl(OUT_DIR / "runtime_batch_rows.jsonl", batches)
    write_json(OUT_DIR / "staging_materialization_plan.json", staging_plan)
    write_json(OUT_DIR / "runtime_launch_plan.json", runtime_plan)
    write_text(OUT_DIR / "report.md", build_report(coverage, scan_rows, batches))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
