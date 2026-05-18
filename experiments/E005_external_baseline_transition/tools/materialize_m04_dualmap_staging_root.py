#!/usr/bin/env python3
"""Materialize a 3RScan staging root for a DualMap Dataset Mode smoke."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
M03_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M03_dualmap_3rscan_staging_feasibility_v0"
)
OUT_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M04_dualmap_staging_root_materialization_v0"
)
STAGED_ROOT = ROOT / "local_dataset" / "DualMap_staged" / "3rscan_scannet_exported"
STAGED_DATASET = STAGED_ROOT / "scannet"
STAGED_EXPORTED = STAGED_DATASET / "exported"
DUALMAP_OUTPUT_ROOT = ROOT / "local_dataset" / "DualMap_outputs"
FRAME_RE = re.compile(r"frame-(\d{6})\.color\.jpg$")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def symlink_force(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() and Path(os.readlink(dst)) == src:
        return False
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)
    return True


def convert_depth_pgm_to_png(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        try:
            with Image.open(dst) as existing:
                if existing.size == (224, 172):
                    return False
        except Exception:
            pass
    with Image.open(src) as img:
        img.save(dst)
    return True


def write_matrix(path: Path, matrix: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(" ".join(f"{value:.9g}" for value in row) for row in matrix) + "\n"
    path.write_text(text, encoding="utf-8")


def collect_frame_ids(sequence_dir: Path) -> list[str]:
    frame_ids = []
    for color_path in sorted(sequence_dir.glob("frame-*.color.jpg")):
        match = FRAME_RE.match(color_path.name)
        if not match:
            continue
        frame_id = match.group(1)
        if (
            (sequence_dir / f"frame-{frame_id}.depth.pgm").exists()
            and (sequence_dir / f"frame-{frame_id}.pose.txt").exists()
        ):
            frame_ids.append(frame_id)
    return frame_ids


def materialize_scan(row: dict) -> dict:
    scan_id = row["scan_id"]
    sequence_dir = Path(row["sequence_dir"])
    scene_dir = STAGED_EXPORTED / scan_id
    color_dir = scene_dir / "color"
    depth_dir = scene_dir / "depth"
    pose_dir = scene_dir / "pose"
    intrinsic_dir = scene_dir / "intrinsic"
    for directory in [color_dir, depth_dir, pose_dir, intrinsic_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    frame_ids = collect_frame_ids(sequence_dir)
    color_links_written = 0
    pose_links_written = 0
    depth_png_written = 0

    for frame_id in frame_ids:
        color_src = sequence_dir / f"frame-{frame_id}.color.jpg"
        depth_src = sequence_dir / f"frame-{frame_id}.depth.pgm"
        pose_src = sequence_dir / f"frame-{frame_id}.pose.txt"
        if symlink_force(color_src, color_dir / f"{frame_id}.jpg"):
            color_links_written += 1
        if symlink_force(pose_src, pose_dir / f"{frame_id}.txt"):
            pose_links_written += 1
        if convert_depth_pgm_to_png(depth_src, depth_dir / f"{frame_id}.png"):
            depth_png_written += 1

    write_matrix(intrinsic_dir / "intrinsic_depth.txt", row["depth_intrinsic_matrix"])

    color_files = sorted(color_dir.glob("*.jpg"))
    depth_files = sorted(depth_dir.glob("*.png"))
    pose_files = sorted(pose_dir.glob("*.txt"))
    sample_depth = {}
    if depth_files:
        with Image.open(depth_files[0]) as img:
            sample_depth = {"mode": img.mode, "size": list(img.size)}

    loader_structure_ready = (
        len(frame_ids) > 0
        and len(color_files) == len(depth_files) == len(pose_files) == len(frame_ids)
        and (intrinsic_dir / "intrinsic_depth.txt").exists()
    )
    return {
        "scan_id": scan_id,
        "source_sequence_dir": str(sequence_dir),
        "staged_scene_dir": str(scene_dir),
        "frame_count": len(frame_ids),
        "color_symlink_count": len(color_files),
        "depth_png_count": len(depth_files),
        "pose_symlink_count": len(pose_files),
        "color_links_written_this_run": color_links_written,
        "pose_links_written_this_run": pose_links_written,
        "depth_png_written_this_run": depth_png_written,
        "intrinsic_depth_path": str(intrinsic_dir / "intrinsic_depth.txt"),
        "sample_depth_png": sample_depth,
        "loader_structure_ready": loader_structure_ready,
    }


def write_dataset_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "dataset_name: 'scannet'",
                "camera_params:",
                "  image_height: 172",
                "  image_width: 224",
                "  png_depth_scale: 1000.0",
                "  crop_edge: 0",
                "",
            ]
        ),
        encoding="utf-8",
    )


def command_plan(scan_id: str, dataset_config_path: Path) -> dict:
    output_path = DUALMAP_OUTPUT_ROOT / scan_id
    return {
        "purpose": "One-scan DualMap runtime smoke after staging root materialization.",
        "working_directory": "<DualMap repo root>",
        "expected_input_scene_dir": str(STAGED_EXPORTED / scan_id),
        "expected_output_path": str(output_path),
        "command": [
            "python",
            "-m",
            "applications.runner_dataset",
            "dataset_name=scannet",
            f"scene_id={scan_id}",
            f"dataset_path={STAGED_DATASET}",
            f"dataset_conf_path={dataset_config_path}",
            f"output_path={output_path}",
            "use_rerun=false",
            "run_local_mapping_only=true",
            "save_local_map=true",
            "use_parallel=false",
            "stride=20",
        ],
        "expected_files_after_runtime": [
            f"{output_path}/<scene_or_run_id>/map/*.pkl",
            f"{output_path}/<scene_or_run_id>/map/layout.pcd",
            f"{output_path}/<scene_or_run_id>/system_time.csv",
        ],
        "verification_command": (
            "find "
            f"{output_path} "
            "-path '*/map/*.pkl' -o -path '*/map/layout.pcd' -o -name system_time.csv"
        ),
        "launched_in_e005_m04": False,
    }


def schema_inspection_plan() -> dict:
    return {
        "purpose": "Inspect DualMap object map PKL schema after a runtime smoke creates map/*.pkl.",
        "input": f"{DUALMAP_OUTPUT_ROOT}/<scan_id>/<scene_or_run_id>/map/*.pkl",
        "output": str(OUT_DIR / "object_pkl_schema_report.json"),
        "minimum_fields_to_check": [
            "object or map element id",
            "semantic label or text descriptor",
            "centroid or representative 3D location",
            "retrieval or confidence score",
            "observation support / frame support if available",
        ],
        "performance_claim_ready_after_schema_only": False,
    }


def write_report(path: Path, rows: list[dict], coverage: dict) -> None:
    lines = [
        "# E005-M04 DualMap Staging Root Materialization",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Staged dataset root: `{coverage['staged_dataset_path']}`.",
        f"- Materialized scans: {coverage['materialized_scan_count']} / {coverage['selected_scan_count']}.",
        f"- Total staged frames: {coverage['total_frame_count']}.",
        f"- Color symlinks: {coverage['total_color_symlink_count']}.",
        f"- Depth PNG files: {coverage['total_depth_png_count']}.",
        f"- Pose symlinks: {coverage['total_pose_symlink_count']}.",
        f"- Intrinsic files: {coverage['intrinsic_file_count']}.",
        f"- One-scan runtime command plan ready: {str(coverage['runtime_command_plan_ready']).lower()}.",
        f"- `DualMap` runtime launched: {str(coverage['dualmap_runtime_launched']).lower()}.",
        f"- Object `*.pkl` schema inspected: {str(coverage['object_pkl_schema_inspected']).lower()}.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan}`: ready={ready}, frames={frames}, color={color}, depth={depth}, pose={pose}, sample_depth={sample}".format(
                scan=row["scan_id"],
                ready=str(row["loader_structure_ready"]).lower(),
                frames=row["frame_count"],
                color=row["color_symlink_count"],
                depth=row["depth_png_count"],
                pose=row["pose_symlink_count"],
                sample=row["sample_depth_png"],
            )
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E005-M04 does not support a `DualMap` performance claim.",
            "- E005-M04 supports a staging-root materialization claim: selected `3RScan` scans can be represented as a `DualMap` `ScanNetDataset`-style folder with image/depth/pose/intrinsic files present.",
            "- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
            "",
            "## 에이전트 추론",
            "",
            "- The next blocker is no longer local file layout. It is `DualMap` runtime dependency/model readiness and object `*.pkl` schema inspection.",
            "- Color/depth resolution alignment remains a runtime validation risk because local `3RScan` color is 960x540 while depth is 224x172.",
            "- A one-scan runtime smoke should start with the smallest staged scan before running all four scans.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_in = read_jsonl(M03_DIR / "scan_preflight_rows.jsonl")
    rows_in = [row for row in rows_in if row.get("staging_preflight_ready")]
    dataset_config_path = STAGED_ROOT / "config" / "dualmap_3rscan_scannet.yaml"
    write_dataset_config(dataset_config_path)
    materialized_rows = [materialize_scan(row) for row in rows_in]
    materialized_scan_count = sum(1 for row in materialized_rows if row["loader_structure_ready"])
    smallest_ready = min(
        (row for row in materialized_rows if row["loader_structure_ready"]),
        key=lambda row: row["frame_count"],
        default=None,
    )
    runtime_plan = command_plan(smallest_ready["scan_id"], dataset_config_path) if smallest_ready else {}
    schema_plan = schema_inspection_plan()
    coverage = {
        "e005_version": "e005_m04_dualmap_staging_root_materialization_v0",
        "status": (
            "e005_m04_dualmap_staging_root_materialized_smoke_ready"
            if materialized_scan_count == len(rows_in) and rows_in
            else "e005_m04_dualmap_staging_root_materialization_incomplete"
        ),
        "selected_scan_count": len(rows_in),
        "materialized_scan_count": materialized_scan_count,
        "staged_dataset_path": str(STAGED_DATASET),
        "dataset_config_path": str(dataset_config_path),
        "total_frame_count": sum(row["frame_count"] for row in materialized_rows),
        "total_color_symlink_count": sum(row["color_symlink_count"] for row in materialized_rows),
        "total_depth_png_count": sum(row["depth_png_count"] for row in materialized_rows),
        "total_pose_symlink_count": sum(row["pose_symlink_count"] for row in materialized_rows),
        "intrinsic_file_count": sum(1 for row in materialized_rows if Path(row["intrinsic_depth_path"]).exists()),
        "runtime_smoke_scan_id": smallest_ready["scan_id"] if smallest_ready else None,
        "runtime_command_plan_ready": bool(runtime_plan),
        "dualmap_runtime_launched": False,
        "object_pkl_schema_inspected": False,
        "dualmap_performance_claim_ready": False,
        "external_baseline_comparison_ready": False,
        "next_recommended_unit": "E005-M05 DualMap one-scan loader/runtime smoke or dependency preflight",
    }
    decision = {
        "status": coverage["status"],
        "selected_route": "DualMap",
        "selected_adapter": "scannet_exported_3rscan_adapter_v0",
        "staging_root_materialized": coverage["status"].endswith("_ready"),
        "runtime_command_plan_ready": coverage["runtime_command_plan_ready"],
        "dualmap_runtime_launched": False,
        "object_pkl_schema_inspected": False,
        "dualmap_performance_claim_ready": False,
        "external_baseline_comparison_ready": False,
        "blockers": [
            "DualMap repo/dependencies/model weights are not executed in E005-M04.",
            "Object PKL schema remains unknown until a one-scan runtime smoke succeeds or serialization source is inspected.",
            "Color/depth resolution alignment must be validated in runtime because 3RScan color and depth resolutions differ.",
        ],
        "next_recommended_unit": coverage["next_recommended_unit"],
    }
    write_jsonl(OUT_DIR / "materialization_rows.jsonl", materialized_rows)
    write_json(OUT_DIR / "stage_manifest.json", {"rows": materialized_rows})
    write_json(OUT_DIR / "runtime_smoke_plan.json", runtime_plan)
    write_json(OUT_DIR / "schema_inspection_plan.json", schema_plan)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_report(OUT_DIR / "report.md", materialized_rows, coverage)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
