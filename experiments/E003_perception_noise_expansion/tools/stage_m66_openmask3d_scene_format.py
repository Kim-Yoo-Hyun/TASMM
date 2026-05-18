#!/usr/bin/env python3
"""Stage E003-M66 3RScan scenes into the OpenMask3D single-scene layout."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M65_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M65_openmask3d_scene_format_model_smoke_plan_v0"
DEFAULT_M66_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M66_openmask3d_model_smoke_v0"
M66_STAGE_VERSION = "e003_m66_openmask3d_scene_format_stage_v0"


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


def write_matrix(path: Path, matrix: list[list[float]]) -> None:
    lines = [" ".join(f"{float(value):.12g}" for value in row) for row in matrix]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_file(src: Path, dst: Path, *, force: bool) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return False
    shutil.copy2(src, dst)
    return True


def convert_pgm_to_png(src: Path, dst: Path, *, force: bool) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return False
    with Image.open(src) as image:
        image.save(dst, format="PNG")
    return True


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M66 OpenMask3D Scene Staging",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Scene count: {coverage['scene_count']}",
            f"- Planned frame rows: {coverage['planned_frame_rows']}",
            f"- Staged color files: {coverage['staged_color_files']}",
            f"- Staged depth PNG files: {coverage['staged_depth_png_files']}",
            f"- Staged pose files: {coverage['staged_pose_files']}",
            f"- Staged PLY files: {coverage['staged_ply_files']}",
            f"- Intrinsic files: {coverage['staged_intrinsic_files']}",
            f"- Missing files: {coverage['missing_file_rows']}",
            f"- Stage root: `{coverage['stage_root']}`",
            "",
            "## 논문 주장",
            "",
            "- E003-M66 scene staging only verifies that local `3RScan` payloads can be converted to the `OpenMask3D` single-scene layout.",
            "- It does not support a real RGB-D/open-vocabulary search claim.",
            "",
            "## 에이전트 추론",
            "",
            "- Staging is a required precondition before any `OpenMask3D` Docker/model smoke.",
            "- `.pgm` depth files are converted to `.png` while preserving the stored depth values and `depth_scale=1000` contract.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for scene staging.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_M65_DIR / "scene_format_manifest.json", type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_M66_DIR, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    stage_root = args.out_dir / "staged_scenes"
    stage_rows: list[dict[str, Any]] = []
    scene_summaries: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []

    staged_counts = {
        "color": 0,
        "depth_png": 0,
        "intrinsic": 0,
        "ply": 0,
        "pose": 0,
    }
    for scene in manifest["scenes"]:
        scan_id = str(scene["scan_id"])
        scene_dir = stage_root / scan_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        source_ply = Path(scene["scene_ply_source"])
        target_ply = scene_dir / f"{scan_id}.ply"
        if source_ply.exists():
            copy_file(source_ply, target_ply, force=args.force)
            staged_counts["ply"] += int(target_ply.exists())
        else:
            missing_rows.append({"scan_id": scan_id, "path": str(source_ply), "type": "source_ply"})

        intrinsic_path = scene_dir / "intrinsic" / "intrinsic_color.txt"
        write_matrix(intrinsic_path, scene["intrinsic_color_matrix_4x4"])
        staged_counts["intrinsic"] += int(intrinsic_path.exists())

        frame_rows = []
        for frame in scene["frame_rows"]:
            target_frame_id = int(frame["target_frame_id"])
            color_src = Path(frame["source_color"])
            depth_src = Path(frame["source_depth_pgm"])
            pose_src = Path(frame["source_pose"])
            color_dst = scene_dir / "color" / f"{target_frame_id}.jpg"
            depth_dst = scene_dir / "depth" / f"{target_frame_id}.png"
            pose_dst = scene_dir / "pose" / f"{target_frame_id}.txt"
            row = {
                "scan_id": scan_id,
                "source_frame_id": frame["source_frame_id"],
                "target_frame_id": target_frame_id,
                "staged_color": str(color_dst),
                "staged_depth_png": str(depth_dst),
                "staged_pose": str(pose_dst),
            }
            if color_src.exists():
                copy_file(color_src, color_dst, force=args.force)
            else:
                missing_rows.append({"scan_id": scan_id, "path": str(color_src), "type": "source_color"})
            if depth_src.exists():
                convert_pgm_to_png(depth_src, depth_dst, force=args.force)
            else:
                missing_rows.append({"scan_id": scan_id, "path": str(depth_src), "type": "source_depth_pgm"})
            if pose_src.exists():
                copy_file(pose_src, pose_dst, force=args.force)
            else:
                missing_rows.append({"scan_id": scan_id, "path": str(pose_src), "type": "source_pose"})

            row.update(
                {
                    "color_exists": color_dst.exists(),
                    "depth_png_exists": depth_dst.exists(),
                    "pose_exists": pose_dst.exists(),
                }
            )
            staged_counts["color"] += int(color_dst.exists())
            staged_counts["depth_png"] += int(depth_dst.exists())
            staged_counts["pose"] += int(pose_dst.exists())
            frame_rows.append(row)
            stage_rows.append(row)

        scene_summaries.append(
            {
                "frame_rows": len(frame_rows),
                "intrinsic_path": str(intrinsic_path),
                "scan_id": scan_id,
                "scene_dir": str(scene_dir),
                "scene_ply": str(target_ply),
                "stage_ready": (
                    target_ply.exists()
                    and intrinsic_path.exists()
                    and all(row["color_exists"] and row["depth_png_exists"] and row["pose_exists"] for row in frame_rows)
                ),
            }
        )

    planned_frame_rows = sum(int(scene["planned_frame_count"]) for scene in manifest["scenes"])
    stage_ready = not missing_rows and all(row["stage_ready"] for row in scene_summaries)
    coverage = {
        "m66_stage_version": M66_STAGE_VERSION,
        "missing_file_rows": len(missing_rows),
        "planned_frame_rows": planned_frame_rows,
        "scene_count": len(scene_summaries),
        "scene_summaries": scene_summaries,
        "stage_ready": stage_ready,
        "stage_root": str(stage_root),
        "staged_color_files": staged_counts["color"],
        "staged_depth_png_files": staged_counts["depth_png"],
        "staged_intrinsic_files": staged_counts["intrinsic"],
        "staged_ply_files": staged_counts["ply"],
        "staged_pose_files": staged_counts["pose"],
        "status": "openmask3d_scene_stage_ready" if stage_ready else "openmask3d_scene_stage_incomplete",
    }

    stage_dir = args.out_dir / "stage"
    write_json(stage_dir / "coverage.json", coverage)
    write_json(stage_dir / "stage_manifest.json", {"m66_stage_version": M66_STAGE_VERSION, "scenes": scene_summaries})
    write_jsonl(stage_dir / "stage_rows.jsonl", stage_rows)
    write_jsonl(stage_dir / "missing_files.jsonl", missing_rows)
    (stage_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if stage_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
