#!/usr/bin/env python3
"""Materialize ConceptGraphs staged layout for E005 heldout scans."""

from __future__ import annotations

import json
import shutil
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "E005_external_baseline_transition"
M41_DIR = EXP_DIR / "artifacts" / "E005-M41_conceptgraphs_heldout_runtime_preflight_v0"
OUT_DIR = EXP_DIR / "artifacts" / "E005-M42_conceptgraphs_heldout_staging_materialization_v0"
SCANS_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
CONFIG_PATH = STAGED_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml"
DEPTH_ALIGNED_SIZE = (224, 172)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def image_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        with Image.open(path) as image:
            return {"exists": True, "height": image.size[1], "mode": image.mode, "width": image.size[0]}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "exists": True}


def parse_depth_intrinsic(sequence_info: Path) -> dict[str, Any]:
    if not sequence_info.exists():
        return {"exists": False, "parse_ready": False}
    values: list[float] | None = None
    for line in sequence_info.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("m_calibrationDepthIntrinsic"):
            _, raw = line.split("=", 1)
            values = [float(token) for token in raw.split()]
            break
    if not values or len(values) < 11:
        return {"exists": True, "parse_ready": False}
    return {
        "cx": values[2],
        "cy": values[6],
        "exists": True,
        "fx": values[0],
        "fy": values[5],
        "parse_ready": True,
    }


def write_intrinsic_matrix(target_intrinsic: Path, intrinsic: dict[str, Any]) -> bool:
    if not intrinsic.get("parse_ready"):
        return False
    matrix = "\n".join(
        [
            f"{intrinsic['fx']:.6f} 0 {intrinsic['cx']:.6f} 0",
            f"0 {intrinsic['fy']:.6f} {intrinsic['cy']:.6f} 0",
            "0 0 1 0",
            "0 0 0 1",
            "",
        ]
    )
    target_intrinsic.mkdir(parents=True, exist_ok=True)
    for name in ["intrinsic_color.txt", "intrinsic_depth.txt"]:
        path = target_intrinsic / name
        if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != matrix:
            path.write_text(matrix, encoding="utf-8")
    return True


def raw_frame_ids(sequence_dir: Path) -> list[str]:
    color_ids = {path.name.removeprefix("frame-").removesuffix(".color.jpg") for path in sequence_dir.glob("frame-*.color.jpg")}
    depth_ids = {path.name.removeprefix("frame-").removesuffix(".depth.pgm") for path in sequence_dir.glob("frame-*.depth.pgm")}
    pose_ids = {path.name.removeprefix("frame-").removesuffix(".pose.txt") for path in sequence_dir.glob("frame-*.pose.txt")}
    return sorted(color_ids & depth_ids & pose_ids)


def resize_color(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    existing = image_info(dst)
    if existing.get("width") == DEPTH_ALIGNED_SIZE[0] and existing.get("height") == DEPTH_ALIGNED_SIZE[1]:
        return False
    with Image.open(src) as image:
        resized = image.convert("RGB").resize(DEPTH_ALIGNED_SIZE, Image.Resampling.LANCZOS)
        resized.save(dst, format="JPEG", quality=95)
    return True


def convert_depth(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    existing = image_info(dst)
    if existing.get("width") == DEPTH_ALIGNED_SIZE[0] and existing.get("height") == DEPTH_ALIGNED_SIZE[1]:
        return False
    with Image.open(src) as image:
        image.save(dst, format="PNG")
    return True


def copy_pose(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return False
    shutil.copyfile(src, dst)
    return True


def chmod_for_container(scan_root: Path) -> dict[str, int]:
    changed_dirs = 0
    changed_files = 0
    for path in [scan_root, *scan_root.rglob("*")]:
        try:
            desired = 0o777 if path.is_dir() else 0o666
            current = stat.S_IMODE(path.stat().st_mode)
            if current != desired:
                path.chmod(desired)
                if path.is_dir():
                    changed_dirs += 1
                else:
                    changed_files += 1
        except FileNotFoundError:
            continue
    return {"permission_changed_dirs": changed_dirs, "permission_changed_files": changed_files}


def materialize_scan(scan_id: str) -> dict[str, Any]:
    source_scan = SCANS_ROOT / scan_id
    sequence_dir = source_scan / "sequence"
    target_scan = STAGED_ROOT / scan_id
    target_color = target_scan / "color"
    target_depth = target_scan / "depth"
    target_pose = target_scan / "pose"
    target_intrinsic = target_scan / "intrinsic"
    for directory in [target_color, target_depth, target_pose, target_intrinsic]:
        directory.mkdir(parents=True, exist_ok=True)

    frame_ids = raw_frame_ids(sequence_dir)
    color_written = 0
    depth_written = 0
    pose_written = 0
    errors: list[dict[str, str]] = []
    for frame_id in frame_ids:
        try:
            if resize_color(sequence_dir / f"frame-{frame_id}.color.jpg", target_color / f"{frame_id}.jpg"):
                color_written += 1
            if convert_depth(sequence_dir / f"frame-{frame_id}.depth.pgm", target_depth / f"{frame_id}.png"):
                depth_written += 1
            if copy_pose(sequence_dir / f"frame-{frame_id}.pose.txt", target_pose / f"{frame_id}.txt"):
                pose_written += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"error": repr(exc), "frame_id": frame_id})

    intrinsic = parse_depth_intrinsic(sequence_dir / "_info.txt")
    intrinsic_written = write_intrinsic_matrix(target_intrinsic, intrinsic)
    permission_result = chmod_for_container(target_scan)

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
    ready = (
        frame_count_ok
        and resolution_aligned
        and intrinsic_written
        and (target_intrinsic / "intrinsic_color.txt").exists()
        and (target_intrinsic / "intrinsic_depth.txt").exists()
        and not errors
    )
    return {
        "color_jpg_count": len(color_files),
        "color_resized_this_run": color_written,
        "common_frame_count": len(frame_ids),
        "conceptgraphs_scannet_ready": ready,
        "depth_png_count": len(depth_files),
        "depth_png_written_this_run": depth_written,
        "errors": errors[:20],
        "error_count": len(errors),
        "frame_count_ok": frame_count_ok,
        "intrinsic_color_exists": (target_intrinsic / "intrinsic_color.txt").exists(),
        "intrinsic_depth_exists": (target_intrinsic / "intrinsic_depth.txt").exists(),
        "intrinsic_written_or_ready": intrinsic_written,
        "pose_copied_this_run": pose_written,
        "pose_txt_count": len(pose_files),
        "resolution_aligned": resolution_aligned,
        "sample_color": sample_color,
        "sample_depth": sample_depth,
        "scan_id": scan_id,
        "source_intrinsic_depth": intrinsic,
        "source_scan_dir": str(source_scan),
        "target_scan_dir": str(target_scan),
        **permission_result,
    }


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M42 ConceptGraphs Heldout Staging Materialization",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Target scans: {coverage['target_scan_count']}.",
        f"- Ready scans: {coverage['ready_scan_count']} / {coverage['target_scan_count']}.",
        f"- Total frames: {coverage['total_frame_count']}.",
        f"- Color JPGs: {coverage['total_color_jpg_count']}.",
        f"- Depth PNGs: {coverage['total_depth_png_count']}.",
        f"- Pose TXTs: {coverage['total_pose_txt_count']}.",
        f"- Resolution-aligned scans: {coverage['resolution_aligned_scan_count']} / {coverage['target_scan_count']}.",
        f"- Error count: {coverage['error_count']}.",
        f"- Runtime launched: {str(coverage['runtime_launched']).lower()}.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}`: ready {ready}, frames {frames}, color/depth/pose {color}/{depth}/{pose}, "
            "resized/converted/copied {cw}/{dw}/{pw}, errors {errors}.".format(
                scan_id=row["scan_id"],
                ready=str(row["conceptgraphs_scannet_ready"]).lower(),
                frames=row["common_frame_count"],
                color=row["color_jpg_count"],
                depth=row["depth_png_count"],
                pose=row["pose_txt_count"],
                cw=row["color_resized_this_run"],
                dw=row["depth_png_written_this_run"],
                pw=row["pose_copied_this_run"],
                errors=row["error_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M42 is staging/materialization evidence only.",
            "- E005-M42 does not launch `ConceptGraphs` runtime and does not support heldout performance.",
            "- Final external baseline, real RGB-D/open-vocabulary robustness, and real navigation `SR` / `SPL` claims remain blocked.",
            "",
            "## Agent Inference",
            "",
            "- Heldout runtime can be launched next only if all staged rows are ready.",
            "- The next runtime should use bounded batches because `GSA` and `cfslam` are GPU-heavy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m41 = load_json(M41_DIR / "coverage.json")
    scan_ids = list(m41["staging_required_scan_ids"])
    write_dataset_config()
    rows = [materialize_scan(scan_id) for scan_id in scan_ids]
    ready_count = sum(1 for row in rows if row["conceptgraphs_scannet_ready"])
    resolution_count = sum(1 for row in rows if row["resolution_aligned"])
    error_count = sum(int(row["error_count"]) for row in rows)
    status = (
        "e005_m42_conceptgraphs_heldout_staging_materialized_ready"
        if rows and ready_count == len(rows) and error_count == 0
        else "e005_m42_conceptgraphs_heldout_staging_materialized_with_blockers"
    )
    coverage = {
        "config_exists": CONFIG_PATH.exists(),
        "dataset_config": str(CONFIG_PATH),
        "error_count": error_count,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m42_version": "e005_m42_conceptgraphs_heldout_staging_materialization_v0",
        "next_recommended_unit": "E005-M43 ConceptGraphs heldout runtime batch launch",
        "paper_table_claim_ready": False,
        "ready_scan_count": ready_count,
        "resolution_aligned_scan_count": resolution_count,
        "runtime_launched": False,
        "source_root": str(SCANS_ROOT),
        "status": status,
        "target_root": str(STAGED_ROOT),
        "target_scan_count": len(rows),
        "target_scan_ids": scan_ids,
        "total_color_jpg_count": sum(row["color_jpg_count"] for row in rows),
        "total_depth_png_count": sum(row["depth_png_count"] for row in rows),
        "total_frame_count": sum(row["common_frame_count"] for row in rows),
        "total_pose_txt_count": sum(row["pose_txt_count"] for row in rows),
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "materialization_rows.jsonl", rows)
    write_jsonl(OUT_DIR / "verification_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
