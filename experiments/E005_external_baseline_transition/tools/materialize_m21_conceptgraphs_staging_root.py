#!/usr/bin/env python3
"""Materialize a ConceptGraphs-compatible 3RScan staging root."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M20_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M20_conceptgraphs_interface_audit_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M21_conceptgraphs_staging_materialization_v0"
SOURCE_ROOT = ROOT / "local_dataset" / "DualMap_staged" / "3rscan_scannet_exported" / "scannet" / "exported"
TARGET_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
CONFIG_PATH = TARGET_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml"
DEPTH_ALIGNED_SIZE = (224, 172)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
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


def symlink_force(src: Path, dst: Path) -> bool:
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() and Path(os.readlink(dst)) == src:
        return False
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)
    return True


def image_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        with Image.open(path) as image:
            return {"exists": True, "width": image.size[0], "height": image.size[1], "mode": image.mode}
    except Exception as exc:  # noqa: BLE001 - verifier records corrupt image cases.
        return {"exists": True, "error": str(exc)}


def resize_color_to_depth(src: Path, dst: Path, target_size: tuple[int, int]) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        existing = image_info(dst)
        if existing.get("width") == target_size[0] and existing.get("height") == target_size[1]:
            return False
    with Image.open(src) as image:
        rgb = image.convert("RGB")
        resized = rgb.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(dst, format="JPEG", quality=95)
    return True


def common_frame_ids(scan_dir: Path) -> list[str]:
    color_ids = {path.stem for path in (scan_dir / "color").glob("*.jpg")}
    depth_ids = {path.stem for path in (scan_dir / "depth").glob("*.png")}
    pose_ids = {path.stem for path in (scan_dir / "pose").glob("*.txt")}
    return sorted(color_ids & depth_ids & pose_ids)


def write_dataset_config() -> None:
    write_text(
        CONFIG_PATH,
        "\n".join(
            [
                "dataset_name: 'scannet'",
                "camera_params:",
                "  image_height: 172",
                "  image_width: 224",
                "  fx: 0.0",
                "  fy: 0.0",
                "  cx: 0.0",
                "  cy: 0.0",
                "  png_depth_scale: 1000.0",
                "",
            ]
        ),
    )


def materialize_scan(scan_id: str) -> dict[str, Any]:
    source_scan = SOURCE_ROOT / scan_id
    target_scan = TARGET_ROOT / scan_id
    target_color = target_scan / "color"
    target_depth = target_scan / "depth"
    target_pose = target_scan / "pose"
    target_intrinsic = target_scan / "intrinsic"
    for directory in [target_color, target_depth, target_pose, target_intrinsic]:
        directory.mkdir(parents=True, exist_ok=True)

    frame_ids = common_frame_ids(source_scan)
    color_written = 0
    depth_links_written = 0
    pose_links_written = 0
    for frame_id in frame_ids:
        if resize_color_to_depth(source_scan / "color" / f"{frame_id}.jpg", target_color / f"{frame_id}.jpg", DEPTH_ALIGNED_SIZE):
            color_written += 1
        if symlink_force(source_scan / "depth" / f"{frame_id}.png", target_depth / f"{frame_id}.png"):
            depth_links_written += 1
        if symlink_force(source_scan / "pose" / f"{frame_id}.txt", target_pose / f"{frame_id}.txt"):
            pose_links_written += 1

    source_intrinsic = source_scan / "intrinsic" / "intrinsic_depth.txt"
    intrinsic_color = target_intrinsic / "intrinsic_color.txt"
    intrinsic_depth = target_intrinsic / "intrinsic_depth.txt"
    if source_intrinsic.exists():
        shutil.copyfile(source_intrinsic, intrinsic_color)
        shutil.copyfile(source_intrinsic, intrinsic_depth)

    color_files = sorted(target_color.glob("*.jpg"))
    depth_files = sorted(target_depth.glob("*.png"))
    pose_files = sorted(target_pose.glob("*.txt"))
    sample_color = image_info(color_files[0]) if color_files else {"exists": False}
    sample_depth = image_info(depth_files[0]) if depth_files else {"exists": False}
    frame_count_ok = len(frame_ids) > 0 and len(color_files) == len(depth_files) == len(pose_files) == len(frame_ids)
    resolution_aligned = (
        sample_color.get("width") == sample_depth.get("width") == DEPTH_ALIGNED_SIZE[0]
        and sample_color.get("height") == sample_depth.get("height") == DEPTH_ALIGNED_SIZE[1]
    )
    ready = frame_count_ok and resolution_aligned and intrinsic_color.exists()
    return {
        "scan_id": scan_id,
        "source_scan_dir": str(source_scan),
        "target_scan_dir": str(target_scan),
        "common_frame_count": len(frame_ids),
        "color_jpg_count": len(color_files),
        "depth_png_count": len(depth_files),
        "pose_txt_count": len(pose_files),
        "color_resized_this_run": color_written,
        "depth_symlinks_written_this_run": depth_links_written,
        "pose_symlinks_written_this_run": pose_links_written,
        "intrinsic_color_exists": intrinsic_color.exists(),
        "intrinsic_depth_copy_exists": intrinsic_depth.exists(),
        "sample_color": sample_color,
        "sample_depth": sample_depth,
        "frame_count_ok": frame_count_ok,
        "resolution_aligned": resolution_aligned,
        "conceptgraphs_scannet_ready": ready,
    }


def build_runtime_preflight_plan(scan_ids: list[str]) -> dict[str, Any]:
    smoke_scan = scan_ids[-1] if scan_ids else ""
    return {
        "status": "planned_not_launched",
        "next_unit": "E005-M22 ConceptGraphs Docker/runtime preflight",
        "working_directory": "<ConceptGraphs repo root>",
        "dataset_root": str(TARGET_ROOT),
        "dataset_config": str(CONFIG_PATH),
        "smoke_scan_id": smoke_scan,
        "expected_inputs_for_smoke_scan": [
            f"{TARGET_ROOT}/{smoke_scan}/color/*.jpg",
            f"{TARGET_ROOT}/{smoke_scan}/depth/*.png",
            f"{TARGET_ROOT}/{smoke_scan}/pose/*.txt",
            f"{TARGET_ROOT}/{smoke_scan}/intrinsic/intrinsic_color.txt",
        ],
        "expected_outputs_after_runtime": [
            f"{TARGET_ROOT}/{smoke_scan}/gsa_detections_<variant>/*.pkl.gz",
            f"{TARGET_ROOT}/{smoke_scan}/pcd_saves/full_pcd_<variant>_<suffix>.pkl.gz",
            f"{TARGET_ROOT}/{smoke_scan}/pcd_saves/full_pcd_<variant>_<suffix>_post.pkl.gz",
        ],
        "claim_boundary": [
            "E005-M21 staging is not a ConceptGraphs result.",
            "Runtime smoke and object-map schema inspection are required before E004 query-level comparison.",
            "Depth-aligned smoke is not final full-resolution open-vocabulary robustness evidence.",
        ],
    }


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]], plan: dict[str, Any]) -> str:
    lines = [
        "# E005-M21 ConceptGraphs Staging Materialization",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Source root: `{coverage['source_root']}`.",
        f"- Target root: `{coverage['target_root']}`.",
        f"- Dataset config: `{coverage['dataset_config']}`.",
        f"- Materialized scans: {coverage['ready_scan_count']} / {coverage['selected_scan_count']}.",
        f"- Total frames: {coverage['total_frame_count']}.",
        f"- Color JPGs: {coverage['total_color_jpg_count']}.",
        f"- Depth PNGs: {coverage['total_depth_png_count']}.",
        f"- Pose TXTs: {coverage['total_pose_txt_count']}.",
        f"- Resolution-aligned scans: {coverage['resolution_aligned_scan_count']} / {coverage['selected_scan_count']}.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}`: frames {frames}, ready {ready}, color {color}, depth {depth}, pose {pose}, resolution aligned {aligned}".format(
                scan_id=row["scan_id"],
                frames=row["common_frame_count"],
                ready=str(row["conceptgraphs_scannet_ready"]).lower(),
                color=row["color_jpg_count"],
                depth=row["depth_png_count"],
                pose=row["pose_txt_count"],
                aligned=str(row["resolution_aligned"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Runtime Preflight Plan",
            "",
            f"- Next unit: `{plan['next_unit']}`.",
            f"- Smoke scan: `{plan['smoke_scan_id']}`.",
            "- Runtime launched in E005-M21: false.",
            "",
            "## Claim Boundary",
            "",
            "- E005-M21 is staging/materialization evidence only.",
            "- No `ConceptGraphs` performance claim is supported yet.",
            "- No final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claim is supported yet.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    local_rows = read_jsonl(M20_DIR / "local_scan_rows.jsonl")
    scan_ids = [row["scan_id"] for row in local_rows]
    write_dataset_config()
    materialization_rows = [materialize_scan(scan_id) for scan_id in scan_ids]
    ready_scan_count = sum(row["conceptgraphs_scannet_ready"] for row in materialization_rows)
    resolution_aligned_count = sum(row["resolution_aligned"] for row in materialization_rows)
    status = "e005_m21_conceptgraphs_staging_materialized_smoke_ready"
    if ready_scan_count != len(scan_ids) or not CONFIG_PATH.exists():
        status = "e005_m21_conceptgraphs_staging_materialized_with_blockers"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_root": str(SOURCE_ROOT),
        "target_root": str(TARGET_ROOT),
        "dataset_config": str(CONFIG_PATH),
        "selected_scan_count": len(scan_ids),
        "ready_scan_count": ready_scan_count,
        "resolution_aligned_scan_count": resolution_aligned_count,
        "total_frame_count": sum(row["common_frame_count"] for row in materialization_rows),
        "total_color_jpg_count": sum(row["color_jpg_count"] for row in materialization_rows),
        "total_depth_png_count": sum(row["depth_png_count"] for row in materialization_rows),
        "total_pose_txt_count": sum(row["pose_txt_count"] for row in materialization_rows),
        "config_exists": CONFIG_PATH.exists(),
        "runtime_launched": False,
        "conceptgraphs_performance_claim_ready": False,
        "next_recommended_unit": "E005-M22 ConceptGraphs Docker/runtime preflight",
    }
    plan = build_runtime_preflight_plan(scan_ids)
    decision = {
        "status": status,
        "decision": "conceptgraphs_staging_root_ready_for_runtime_preflight" if status.endswith("_ready") else "repair_staging_blockers",
        "next_action": coverage["next_recommended_unit"],
        "claim_boundary": plan["claim_boundary"],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "materialization_rows.jsonl", materialization_rows)
    write_jsonl(OUT_DIR / "verification_rows.jsonl", materialization_rows)
    write_json(OUT_DIR / "runtime_preflight_plan.json", plan)
    write_json(OUT_DIR / "decision.json", decision)
    write_json(OUT_DIR / "stage_manifest.json", {"target_root": str(TARGET_ROOT), "scan_ids": scan_ids, "dataset_config": str(CONFIG_PATH)})
    write_text(OUT_DIR / "report.md", build_report(coverage, materialization_rows, plan))
    write_text(
        TARGET_ROOT / "README.md",
        "\n".join(
            [
                "# ConceptGraphs 3RScan Depth-Aligned Staging Root",
                "",
                "Generated by E005-M21 for ConceptGraphs runtime preflight.",
                "",
                f"- Source root: `{SOURCE_ROOT}`",
                f"- Dataset config: `{CONFIG_PATH}`",
                "- Claim boundary: staging only, not ConceptGraphs performance evidence.",
                "",
            ]
        ),
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
