#!/usr/bin/env python3
"""Preflight 3RScan to DualMap dataset-format staging feasibility."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M03_dualmap_3rscan_staging_feasibility_v0"
)
M02_DECISION = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M02_dualmap_interface_audit_v0"
    / "decision.json"
)
M73_COVERAGE = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
    / "coverage.json"
)
M73_QUERY_MANIFEST = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
    / "real_proposal_query_manifest.jsonl"
)
SCANS_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
STAGED_ROOT = ROOT / "local_dataset" / "DualMap_staged" / "3rscan_scannet_exported"

FRAME_RE = re.compile(r"frame-(\d+)\.(color|depth|pose)\.(jpg|pgm|txt)$")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
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


def parse_info(path: Path) -> dict:
    info: dict[str, object] = {}
    if not path.exists():
        return info
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key in {
            "m_colorWidth",
            "m_colorHeight",
            "m_depthWidth",
            "m_depthHeight",
            "m_depthShift",
            "m_frames.size",
        }:
            try:
                info[key] = int(float(value))
            except ValueError:
                info[key] = value
        elif key in {
            "m_calibrationColorIntrinsic",
            "m_calibrationDepthIntrinsic",
            "m_calibrationColorExtrinsic",
            "m_calibrationDepthExtrinsic",
        }:
            vals = []
            for part in value.split():
                try:
                    vals.append(float(part))
                except ValueError:
                    pass
            info[key] = vals
        else:
            info[key] = value
    return info


def frame_indices(sequence_dir: Path, suffix: str) -> set[int]:
    indices: set[int] = set()
    for path in sequence_dir.glob(f"frame-*.{suffix}"):
        match = FRAME_RE.match(path.name)
        if match:
            indices.add(int(match.group(1)))
    return indices


def pose_matrix_ready(path: Path) -> bool:
    if not path.exists():
        return False
    vals: list[float] = []
    for part in path.read_text(encoding="utf-8", errors="replace").split():
        try:
            vals.append(float(part))
        except ValueError:
            return False
    return len(vals) == 16 and all(math.isfinite(v) for v in vals)


def intrinsic_matrix_from_info(info: dict, which: str) -> list[list[float]] | None:
    key = f"m_calibration{which}Intrinsic"
    vals = info.get(key)
    if not isinstance(vals, list) or len(vals) < 16:
        return None
    return [vals[0:4], vals[4:8], vals[8:12], vals[12:16]]


def manifest_by_scan() -> dict[str, dict]:
    rows = read_jsonl(M73_QUERY_MANIFEST)
    return {row["scan_id"]: row for row in rows if "scan_id" in row}


def selected_scans() -> list[str]:
    cov = read_json(M73_COVERAGE)
    scan_ids = cov.get("selected_scan_ids")
    if isinstance(scan_ids, list) and scan_ids:
        return sorted(str(scan_id) for scan_id in scan_ids)
    return []


def scan_preflight(scan_id: str, manifest: dict) -> dict:
    scan_dir = SCANS_ROOT / scan_id
    sequence_dir = scan_dir / "sequence"
    info_path = sequence_dir / "_info.txt"
    info = parse_info(info_path)

    color_idx = frame_indices(sequence_dir, "color.jpg") if sequence_dir.exists() else set()
    depth_idx = frame_indices(sequence_dir, "depth.pgm") if sequence_dir.exists() else set()
    pose_idx = frame_indices(sequence_dir, "pose.txt") if sequence_dir.exists() else set()
    triplet_idx = sorted(color_idx & depth_idx & pose_idx)
    sampled_idx = manifest.get("sampled_frame_indices") or []
    sampled_ready = [idx for idx in sampled_idx if idx in triplet_idx]
    first_pose_ready = pose_matrix_ready(sequence_dir / f"frame-{triplet_idx[0]:06d}.pose.txt") if triplet_idx else False

    color_intrinsic = intrinsic_matrix_from_info(info, "Color")
    depth_intrinsic = intrinsic_matrix_from_info(info, "Depth")
    semantic_triplet_ready = all(
        (scan_dir / name).exists()
        for name in [
            "labels.instances.annotated.v2.ply",
            "semseg.v2.json",
            "mesh.refined.0.010000.segs.v2.json",
        ]
    )
    frame_count_declared = info.get("m_frames.size")
    frame_count_matches_info = frame_count_declared == len(triplet_idx)
    scan_ready = (
        sequence_dir.exists()
        and info_path.exists()
        and bool(triplet_idx)
        and len(color_idx) == len(depth_idx) == len(pose_idx) == len(triplet_idx)
        and first_pose_ready
        and depth_intrinsic is not None
        and semantic_triplet_ready
    )

    return {
        "scan_id": scan_id,
        "scan_dir": str(scan_dir),
        "sequence_dir": str(sequence_dir),
        "sequence_dir_ready": sequence_dir.exists(),
        "info_ready": info_path.exists(),
        "semantic_triplet_ready": semantic_triplet_ready,
        "color_frame_count": len(color_idx),
        "depth_frame_count": len(depth_idx),
        "pose_frame_count": len(pose_idx),
        "triplet_frame_count": len(triplet_idx),
        "declared_frame_count": frame_count_declared,
        "frame_count_matches_info": frame_count_matches_info,
        "first_pose_matrix_ready": first_pose_ready,
        "sampled_frame_count_from_m73": len(sampled_idx),
        "sampled_frame_ready_count": len(sampled_ready),
        "color_size": {
            "width": info.get("m_colorWidth"),
            "height": info.get("m_colorHeight"),
        },
        "depth_size": {
            "width": info.get("m_depthWidth"),
            "height": info.get("m_depthHeight"),
        },
        "depth_shift": info.get("m_depthShift"),
        "color_intrinsic_ready": color_intrinsic is not None,
        "depth_intrinsic_ready": depth_intrinsic is not None,
        "depth_intrinsic_matrix": depth_intrinsic,
        "selected_dualmap_layout": "scannet_exported_3rscan_adapter_v0",
        "staged_scene_dir": str(STAGED_ROOT / "scannet" / "exported" / scan_id),
        "required_materialization": [
            "symlink or copy sequence/frame-*.color.jpg to color/*.jpg",
            "convert sequence/frame-*.depth.pgm to depth/*.png",
            "symlink or copy sequence/frame-*.pose.txt to pose/*.txt",
            "write intrinsic/intrinsic_depth.txt from _info depth intrinsic",
            "write custom config/data_config/dataset/3rscan_scannet.yaml with depth image size and depth scale",
        ],
        "staging_preflight_ready": scan_ready,
    }


def staging_plan(rows: list[dict]) -> dict:
    selected_adapter = "scannet_exported_3rscan_adapter_v0"
    ready_rows = [row for row in rows if row["staging_preflight_ready"]]
    return {
        "staging_version": "e005_m03_dualmap_3rscan_staging_feasibility_v0",
        "selected_adapter": selected_adapter,
        "why_scannet_adapter": (
            "DualMap already has a ScanNetDataset loader that expects "
            "exported/<scene_id>/color, depth, pose, and intrinsic directories. "
            "3RScan sequence files already provide per-frame JPG color, PGM depth, "
            "4x4 pose text, and intrinsics in _info.txt, so the remaining work is "
            "bounded materialization rather than dataset download."
        ),
        "why_not_self_collected_adapter_first": (
            "DualMap SelfCollectedDataset expects rgb/*.png, depth/*.png, and a "
            "single pose.txt. This is also possible, but the ScanNet exported route "
            "preserves the existing per-frame pose files and color JPG files with "
            "fewer transformations."
        ),
        "staged_root": str(STAGED_ROOT),
        "staged_dataset_path_for_dualmap": str(STAGED_ROOT / "scannet"),
        "dualmap_dataset_name": "scannet",
        "dualmap_scene_ids": [row["scan_id"] for row in ready_rows],
        "custom_dataset_config": {
            "path": str(OUT_DIR / "dualmap_3rscan_scannet.yaml"),
            "content": {
                "dataset_name": "scannet",
                "camera_params": {
                    "image_height": 172,
                    "image_width": 224,
                    "png_depth_scale": 1000.0,
                },
            },
        },
        "materialization_policy": {
            "copy_color": False,
            "symlink_color": True,
            "copy_pose": False,
            "symlink_pose": True,
            "convert_depth_pgm_to_png": True,
            "write_intrinsic_depth": True,
            "do_not_copy_full_dataset": True,
        },
        "object_pkl_schema_inspection_route": {
            "preferred": (
                "After one staged scan passes DualMap loader/runtime smoke, inspect "
                "output/map_results/<scan_id>/map/*.pkl keys and representative "
                "values with a lightweight schema dumper."
            ),
            "fallback": (
                "If runtime blocks on model/dependency setup, clone or inspect the "
                "official source serialization path and record only schema evidence, "
                "with no performance claim."
            ),
            "performance_claim_ready": False,
        },
        "runner_override_template": [
            "python -m applications.runner_dataset",
            "dataset_name=scannet",
            "scene_id=<3rscan_scan_id>",
            f"dataset_path={STAGED_ROOT / 'scannet'}",
            f"dataset_conf_path={OUT_DIR / 'dualmap_3rscan_scannet.yaml'}",
            f"output_path={ROOT / 'local_dataset' / 'DualMap_outputs' / '<3rscan_scan_id>'}",
            "use_rerun=false",
            "run_local_mapping_only=true",
            "save_local_map=true",
        ],
    }


def decision(rows: list[dict], m02: dict) -> dict:
    ready_count = sum(1 for row in rows if row["staging_preflight_ready"])
    all_ready = ready_count == len(rows) and bool(rows)
    return {
        "status": (
            "e005_m03_dualmap_3rscan_staging_feasibility_ready_with_conversion_required"
            if all_ready
            else "e005_m03_dualmap_3rscan_staging_feasibility_blocked"
        ),
        "selected_route": m02.get("selected_route", "DualMap"),
        "selected_adapter": "scannet_exported_3rscan_adapter_v0",
        "selected_scan_count": len(rows),
        "preflight_ready_scan_count": ready_count,
        "dataset_format_staging_feasible": all_ready,
        "materialization_required": True,
        "depth_conversion_required": True,
        "dualmap_runtime_launched": False,
        "dualmap_performance_claim_ready": False,
        "external_baseline_comparison_ready": False,
        "object_pkl_schema_inspection_ready": False,
        "blockers": [
            "Staging root has not been materialized yet.",
            "3RScan depth PGM files must be converted to PNG for DualMap loaders.",
            "Custom 3RScan-as-ScanNet dataset config must be used because 3RScan depth images are 224x172 with depth scale 1000.",
            "DualMap dependencies, model weights, and object PKL output schema are not verified by this preflight.",
            "Coordinate/intrinsic compatibility needs a one-scan loader/runtime smoke before any external baseline metric claim.",
        ],
        "next_recommended_unit": "E005-M04 DualMap 3RScan staging root materialization smoke",
    }


def write_yaml_template(path: Path) -> None:
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


def write_report(path: Path, rows: list[dict], plan: dict, decision_data: dict) -> None:
    ready_count = decision_data["preflight_ready_scan_count"]
    scan_count = decision_data["selected_scan_count"]
    total_triplets = sum(row["triplet_frame_count"] for row in rows)
    lines = [
        "# E005-M03 DualMap 3RScan Staging Feasibility",
        "",
        "## Status",
        "",
        decision_data["status"],
        "",
        "## 사실",
        "",
        f"- Selected scans from E003-M73: {scan_count}.",
        f"- Preflight-ready scans: {ready_count} / {scan_count}.",
        f"- Total RGB-D-pose triplets across selected scans: {total_triplets}.",
        "- Selected adapter: `scannet_exported_3rscan_adapter_v0`.",
        "- Materialization was not executed in E005-M03.",
        "- Depth conversion from `.pgm` to `.png` is required before a DualMap loader smoke.",
        "- Custom `3RScan`-as-`ScanNet` dataset config is required because local depth frames are 224x172 with depth scale 1000.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan}`: ready={ready}, triplets={triplets}, sampled={sampled}/{sampled_total}, "
            "color={cw}x{ch}, depth={dw}x{dh}".format(
                scan=row["scan_id"],
                ready=str(row["staging_preflight_ready"]).lower(),
                triplets=row["triplet_frame_count"],
                sampled=row["sampled_frame_ready_count"],
                sampled_total=row["sampled_frame_count_from_m73"],
                cw=row["color_size"]["width"],
                ch=row["color_size"]["height"],
                dw=row["depth_size"]["width"],
                dh=row["depth_size"]["height"],
            )
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E005-M03 does not support a `DualMap` performance claim.",
            "- E005-M03 supports a dataset-format feasibility claim: the selected E003-M73 `3RScan` scans have enough RGB-D-pose payload to be staged for a `DualMap` Dataset Mode smoke.",
            "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
            "",
            "## 에이전트 추론",
            "",
            "- The `ScanNetDataset` route is the lowest-change adapter because it preserves per-frame pose files and color JPG files.",
            "- The main materialization work is depth conversion and writing `intrinsic/intrinsic_depth.txt`; it is not another dataset download problem.",
            "- Object `*.pkl` schema inspection should happen only after a one-scan `DualMap` smoke or official serialization-source inspection.",
            "- `DualMap` must remain an external baseline route, not a renamed internal ablation.",
            "",
            "## Next",
            "",
            f"- {decision_data['next_recommended_unit']}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m02 = read_json(M02_DECISION)
    manifest = manifest_by_scan()
    scan_ids = selected_scans()
    rows = [scan_preflight(scan_id, manifest.get(scan_id, {})) for scan_id in scan_ids]
    plan = staging_plan(rows)
    decision_data = decision(rows, m02)
    coverage = {
        "e005_version": "e005_m03_dualmap_3rscan_staging_feasibility_v0",
        "status": decision_data["status"],
        "selected_scan_count": decision_data["selected_scan_count"],
        "preflight_ready_scan_count": decision_data["preflight_ready_scan_count"],
        "dataset_format_staging_feasible": decision_data["dataset_format_staging_feasible"],
        "selected_adapter": decision_data["selected_adapter"],
        "materialization_required": decision_data["materialization_required"],
        "depth_conversion_required": decision_data["depth_conversion_required"],
        "dualmap_runtime_launched": decision_data["dualmap_runtime_launched"],
        "object_pkl_schema_inspection_ready": decision_data["object_pkl_schema_inspection_ready"],
        "next_recommended_unit": decision_data["next_recommended_unit"],
    }
    write_jsonl(OUT_DIR / "scan_preflight_rows.jsonl", rows)
    write_json(OUT_DIR / "staging_plan.json", plan)
    write_json(OUT_DIR / "decision.json", decision_data)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_yaml_template(OUT_DIR / "dualmap_3rscan_scannet.yaml")
    write_report(OUT_DIR / "report.md", rows, plan, decision_data)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
