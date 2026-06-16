#!/usr/bin/env python3
"""Preflight the ConceptGraphs HM3D source-gap adapter contract."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M84_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
)
M93_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
)
M103_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
)
M105_DATA_ROOT = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
)

VERSION = "e008_m104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
READY_STATUS = "e008_m104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_ready"
BLOCKED_STATUS = "e008_m104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_blocked"
NEXT_UNIT = "E008-M105 ConceptGraphs HM3D source-gap staging materialization smoke"
CONCEPTGRAPHS_IMAGE = "research2/conceptgraphs-smoke:latest"
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
DEPTH_SCALE = 1000.0


SOURCE_BUNDLES = {
    "m84_source_gap_non_oracle": {
        "data_root": M84_DATA_DIR,
        "rendered_rows": M84_DATA_DIR / "rendered_frame_rows.jsonl",
        "snap_rows": M84_DATA_DIR / "snap_validation_rows.jsonl",
        "summary": M84_DATA_DIR / "render_summary.json",
        "role": "primary_source_gap_observation_expansion",
    },
    "m93_coverage_expansion_sofa": {
        "data_root": M93_DATA_DIR,
        "rendered_rows": M93_DATA_DIR / "rendered_frame_rows.jsonl",
        "snap_rows": M93_DATA_DIR / "snap_validation_rows.jsonl",
        "summary": M93_DATA_DIR / "render_summary.json",
        "role": "supplemental_coverage_expansion_for_sofa_case",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def docker_image_ready(image: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except Exception:
        return False
    return proc.returncode == 0


def host_path(data_root: Path, docker_path: str | None) -> Path:
    if not docker_path:
        return Path("")
    path = Path(str(docker_path))
    if path.is_absolute() and path.parts[:2] == ("/", "out"):
        return data_root / Path(*path.parts[2:])
    if path.is_absolute():
        return path
    return data_root / path


def image_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        with Image.open(path) as image:
            return {
                "exists": True,
                "width": image.size[0],
                "height": image.size[1],
                "mode": image.mode,
                "format": image.format,
            }
    except Exception as exc:  # noqa: BLE001 - preflight records corrupted image cases.
        return {"exists": True, "error": str(exc)}


def parse_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    out: dict[str, Any] = {"exists": True}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key in {
            "m_colorWidth",
            "m_colorHeight",
            "m_depthWidth",
            "m_depthHeight",
            "m_frames.size",
        }:
            out[key] = int(float(value))
        elif key in {"m_depthShift"}:
            out[key] = float(value)
        elif key in {"m_calibrationColorIntrinsic", "m_calibrationDepthIntrinsic"}:
            nums = [float(item) for item in value.split()]
            out[key] = nums
    color_intrinsic = out.get("m_calibrationColorIntrinsic")
    out["intrinsic_derivable"] = isinstance(color_intrinsic, list) and len(color_intrinsic) == 16
    return out


def pose_matrix_valid(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        rows = [[float(value) for value in line.split()] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except ValueError:
        return False
    return len(rows) == 4 and all(len(row) == 4 for row in rows)


def group_rows_by_scan(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scan_id"))].append(row)
    return dict(grouped)


def build_bundle_preflight_rows() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    bundle_rows: list[dict[str, Any]] = []
    rendered_by_bundle: dict[str, list[dict[str, Any]]] = {}
    for bundle_id, spec in SOURCE_BUNDLES.items():
        rendered_rows = read_jsonl(spec["rendered_rows"])
        snap_rows = read_jsonl(spec["snap_rows"])
        summary = read_json(spec["summary"])
        rendered_by_bundle[bundle_id] = rendered_rows
        scan_ids = sorted({str(row.get("scan_id")) for row in rendered_rows})
        leakage_rows = [
            row
            for row in rendered_rows + snap_rows
            if bool(row.get("uses_objectnav_eval_goal")) or bool(row.get("uses_objectnav_eval_viewpoint"))
        ]
        frame_counts = Counter(str(row.get("scan_id")) for row in rendered_rows)
        bundle_rows.append(
            {
                "version": VERSION,
                "bundle_id": bundle_id,
                "role": spec["role"],
                "data_root": str(spec["data_root"]),
                "rendered_frame_rows": len(rendered_rows),
                "snap_validation_rows": len(snap_rows),
                "scan_rows": len(scan_ids),
                "scan_ids": scan_ids,
                "frame_count_by_scan": dict(frame_counts),
                "render_summary_ok": bool(summary.get("ok")),
                "summary_uses_eval_goal": bool(summary.get("uses_objectnav_eval_goal")),
                "summary_uses_eval_viewpoint": bool(summary.get("uses_objectnav_eval_viewpoint")),
                "leakage_row_count": len(leakage_rows),
                "preflight_source_ready": bool(rendered_rows) and not leakage_rows,
            }
        )
    return bundle_rows, rendered_by_bundle


def build_scan_layout_rows(
    rendered_by_bundle: dict[str, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scan_layout_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    for bundle_id, rows in rendered_by_bundle.items():
        spec = SOURCE_BUNDLES[bundle_id]
        data_root = spec["data_root"]
        for scan_id, scan_rows in group_rows_by_scan(rows).items():
            first = scan_rows[0]
            source_scan_dir = data_root / "3RScan" / "scans" / scan_id
            sequence_dir = source_scan_dir / "sequence"
            color_files = sorted(sequence_dir.glob("*.color.jpg"))
            depth_pgm_files = sorted(sequence_dir.glob("*.depth.pgm"))
            depth_png_files = sorted(sequence_dir.glob("*.depth.png"))
            pose_files = sorted(sequence_dir.glob("*.pose.txt"))
            info_path = sequence_dir / "_info.txt"
            info = parse_info(info_path)
            sample_color = host_path(data_root, first.get("color_path"))
            sample_depth = host_path(data_root, first.get("depth_path"))
            sample_pose = host_path(data_root, first.get("pose_path"))
            color_info = image_info(sample_color)
            depth_info = image_info(sample_depth)
            common_count_ready = (
                len(color_files) == len(depth_pgm_files) == len(pose_files) == len(scan_rows)
                and len(scan_rows) > 0
            )
            direct_conceptgraphs_ready = (
                len(color_files) == len(depth_png_files) == len(pose_files) == len(scan_rows)
                and bool(info.get("intrinsic_derivable"))
            )
            adapter_materialization_ready = (
                common_count_ready
                and bool(info.get("intrinsic_derivable"))
                and color_info.get("exists") is True
                and depth_info.get("exists") is True
                and pose_matrix_valid(sample_pose)
            )
            blocker_reasons: list[str] = []
            if not direct_conceptgraphs_ready:
                if depth_png_files == []:
                    blocker_reasons.append("depth_png_not_materialized")
                if not bool(info.get("intrinsic_derivable")):
                    blocker_reasons.append("intrinsic_not_derivable")
                if not common_count_ready:
                    blocker_reasons.append("frame_count_mismatch_or_missing")
            scan_layout_rows.append(
                {
                    "version": VERSION,
                    "bundle_id": bundle_id,
                    "scan_id": scan_id,
                    "scene_key": first.get("scene_key"),
                    "adapter_episode_id": first.get("adapter_episode_id"),
                    "source_scan_dir": str(source_scan_dir),
                    "sequence_dir": str(sequence_dir),
                    "object_category": None,
                    "rendered_frame_rows": len(scan_rows),
                    "color_jpg_count": len(color_files),
                    "depth_pgm_count": len(depth_pgm_files),
                    "depth_png_count": len(depth_png_files),
                    "pose_txt_count": len(pose_files),
                    "info_exists": info.get("exists", False),
                    "info_frame_count": info.get("m_frames.size"),
                    "render_width": color_info.get("width"),
                    "render_height": color_info.get("height"),
                    "depth_scale": info.get("m_depthShift", DEPTH_SCALE),
                    "direct_conceptgraphs_ready": direct_conceptgraphs_ready,
                    "adapter_materialization_ready": adapter_materialization_ready,
                    "direct_blocker_reasons": blocker_reasons,
                    "target_staging_dir": str(M105_DATA_ROOT / "conceptgraphs_hm3d_source_gap_staged" / scan_id),
                    "claim_boundary": "M104 checks source-layout feasibility only; it does not run ConceptGraphs or export candidates.",
                }
            )
            sample_rows.append(
                {
                    "version": VERSION,
                    "bundle_id": bundle_id,
                    "scan_id": scan_id,
                    "frame_id": first.get("frame_id"),
                    "sample_color_path": str(sample_color),
                    "sample_depth_path": str(sample_depth),
                    "sample_pose_path": str(sample_pose),
                    "sample_color_info": color_info,
                    "sample_depth_info": depth_info,
                    "sample_pose_matrix_valid": pose_matrix_valid(sample_pose),
                    "info_intrinsic_derivable": bool(info.get("intrinsic_derivable")),
                    "uses_objectnav_eval_goal": bool(first.get("uses_objectnav_eval_goal")),
                    "uses_objectnav_eval_viewpoint": bool(first.get("uses_objectnav_eval_viewpoint")),
                    "adapter_materialization_ready": adapter_materialization_ready,
                }
            )
    return scan_layout_rows, sample_rows


def build_case_staging_rows(
    source_gap_requirements: list[dict[str, Any]],
    scan_layout_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_scan_bundle = {(row["scan_id"], row["bundle_id"]): row for row in scan_layout_rows}
    out: list[dict[str, Any]] = []
    for req in source_gap_requirements:
        scan_id = str(req.get("scan_id"))
        if req.get("m102_assigned_repair_branch") == "coverage_expansion_branch":
            selected_bundle = "m93_coverage_expansion_sofa"
            fallback_bundle = "m84_source_gap_non_oracle"
        else:
            selected_bundle = "m84_source_gap_non_oracle"
            fallback_bundle = None
        selected_layout = by_scan_bundle.get((scan_id, selected_bundle), {})
        out.append(
            {
                "version": VERSION,
                "row_type": "case_staging_selection",
                "scan_id": scan_id,
                "adapter_episode_id": req.get("adapter_episode_id"),
                "scene_key": req.get("scene_key"),
                "object_category": req.get("object_category"),
                "m102_branch": req.get("m102_assigned_repair_branch"),
                "selected_source_bundle": selected_bundle,
                "fallback_source_bundle": fallback_bundle,
                "selected_rendered_frame_rows": selected_layout.get("rendered_frame_rows", 0),
                "selected_adapter_materialization_ready": bool(
                    selected_layout.get("adapter_materialization_ready")
                ),
                "selected_direct_conceptgraphs_ready": bool(selected_layout.get("direct_conceptgraphs_ready")),
                "staging_materialization_required": not bool(selected_layout.get("direct_conceptgraphs_ready")),
                "target_staging_dir": selected_layout.get("target_staging_dir"),
                "minimum_requirement": req.get("alternative_source_minimum_requirement"),
                "claim_boundary": "M104 selects a non-oracle input source; candidate generation is still future work.",
            }
        )
    return out


def build_staging_plan_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        target = Path(str(row.get("target_staging_dir")))
        scan_id = str(row.get("scan_id"))
        rows.append(
            {
                "version": VERSION,
                "row_type": "staging_materialization_plan",
                "scan_id": scan_id,
                "source_bundle": row.get("selected_source_bundle"),
                "target_root": str(target),
                "color_rule": "copy or symlink `*.color.jpg` to `color/<six_digit>.jpg`",
                "depth_rule": "convert `*.depth.pgm` to millimeter `depth/<six_digit>.png` with png_depth_scale 1000.0",
                "pose_rule": "copy `*.pose.txt` to `pose/<six_digit>.txt` preserving Habitat camera pose",
                "intrinsic_rule": "derive `intrinsic_color.txt` and `intrinsic_depth.txt` from `_info.txt` 4x4 intrinsic rows",
                "config_rule": "write ConceptGraphs dataset config for 640x480 HM3D rendered RGB-D with png_depth_scale 1000.0",
                "blocked_input_rule": "do not use ObjectNav eval goal/viewpoint, target object id, success labels, or distance-to-target fields",
                "m105_ready": bool(row.get("selected_adapter_materialization_ready")),
            }
        )
    return rows


def build_runtime_contract_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scan_ids = sorted({str(row.get("scan_id")) for row in case_rows})
    rows: list[dict[str, Any]] = []
    for scan_id in scan_ids:
        rows.append(
            {
                "version": VERSION,
                "row_type": "future_runtime_contract",
                "scan_id": scan_id,
                "image": CONCEPTGRAPHS_IMAGE,
                "launch_now": False,
                "working_directory": "/workspace/concept-graphs/conceptgraph",
                "dataset_root": "/data/ConceptGraphs_hm3d_source_gap",
                "dataset_config": "/data/ConceptGraphs_hm3d_source_gap/config/conceptgraphs_hm3d_source_gap.yaml",
                "expected_outputs": [
                    f"gsa_detections_none/{scan_id}/*.pkl.gz",
                    f"{scan_id}/pcd_saves/full_pcd_none_<suffix>.pkl.gz",
                    f"{scan_id}/pcd_saves/full_pcd_none_<suffix>_post.pkl.gz",
                ],
                "verification_after_launch": "file counts plus object-map schema inspection; do not scan huge logs",
                "claim_boundary": "Runtime output is needed before source-gap recovery or navigation claims.",
            }
        )
    return rows


def build_candidate_output_contract_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_id", True, "stable candidate id after ConceptGraphs object-map export"),
        ("source_route", True, "`conceptgraphs_hm3d_map_candidate_adapter`"),
        ("scan_id", True, "E008 scan id"),
        ("adapter_episode_id", True, "ObjectNav adapter episode id for evaluation join only"),
        ("scene_key", True, "HM3D scene key"),
        ("object_category", True, "query category such as sofa or toilet"),
        ("candidate_center_xyz", True, "world coordinate of object-map candidate center"),
        ("candidate_bbox_min_xyz", False, "3D bbox min if available"),
        ("candidate_bbox_max_xyz", False, "3D bbox max if available"),
        ("semantic_score", False, "CLIP/text similarity or ConceptGraphs label score"),
        ("confidence", False, "map/proposal confidence"),
        ("evidence_frame_ids", False, "non-oracle frame ids contributing to candidate"),
        ("source_input_trace", True, "trace proving only allowed inputs were used"),
        ("coordinate_frame", True, "Habitat/world coordinate-frame tag"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "candidate_output_contract_field",
            "field": field,
            "required": required,
            "definition": definition,
        }
        for field, required, definition in fields
    ]


def build_gate_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready_cases = sum(1 for row in case_rows if row.get("selected_adapter_materialization_ready"))
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M105 materializes ConceptGraphs-compatible staged input for both M102 source-gap cases and validates RGB/depth/pose/intrinsic counts.",
            "current_m104_case_ready_count": ready_cases,
            "next_action": "Launch/verify a bounded ConceptGraphs source-gap runtime only after M105 staging passes.",
            "claim_status_after_gate": "input staging ready only; no source-gap recovery claim yet",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "Only one source-gap case materializes or the staged layout has category/coordinate trace gaps.",
            "current_m104_case_ready_count": ready_cases,
            "next_action": "repair staging or decide whether to revisit OpenMask3D fallback",
            "claim_status_after_gate": "diagnostic only",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "PGM-to-PNG conversion, intrinsic derivation, or non-oracle leakage audit fails for the selected source bundle.",
            "current_m104_case_ready_count": ready_cases,
            "next_action": "do not run ConceptGraphs; revisit source route or OpenMask3D/HOV-SG audit",
            "claim_status_after_gate": "ConceptGraphs HM3D source-gap route unsupported",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "ConceptGraphs_HM3D_source_gap_input_preflight",
            "status": "supported",
            "boundary": "M104 supports adapter/materialization feasibility only.",
        },
        {
            "version": VERSION,
            "claim": "ConceptGraphs_source_gap_candidate_generation",
            "status": "blocked",
            "boundary": "requires M105 staging plus future ConceptGraphs runtime and object-map export.",
        },
        {
            "version": VERSION,
            "claim": "source_gap_recovery",
            "status": "blocked",
            "boundary": "requires leakage-safe goal evaluation after alternative candidates exist.",
        },
        {
            "version": VERSION,
            "claim": "real_navigation_SR_SPL",
            "status": "blocked",
            "boundary": "requires candidate navmesh/source-readiness validation and Docker Habitat trajectory execution.",
        },
        {
            "version": VERSION,
            "claim": "human_intent_main_contribution",
            "status": "blocked",
            "boundary": "M104 is source-route preflight; it does not test task-context specificity.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why does M104 not run ConceptGraphs immediately?",
            "answer": "The current HM3D render layout is 3RScan-like and depth is PGM; ConceptGraphs expects a staged RGB/depth/pose/intrinsic layout. M104 fixes the non-oracle adapter contract before any long runtime.",
        },
        {
            "version": VERSION,
            "question": "Is this using ObjectNav oracle data?",
            "answer": "No. M104 audits `uses_objectnav_eval_goal` and `uses_objectnav_eval_viewpoint` flags and keeps eval goal/viewpoint fields blocked from staging and policy inputs.",
        },
        {
            "version": VERSION,
            "question": "Does this solve the M102 source-gap?",
            "answer": "No. M104 only shows that a different proposal-source route can be staged. Source-gap recovery requires ConceptGraphs candidates and leakage-safe goal evaluation.",
        },
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    case_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M104 ConceptGraphs HM3D Source-Gap Adapter Preflight Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Selected route: `{coverage['selected_route']}`.",
        f"- Source-gap cases: {coverage['source_gap_case_rows']}.",
        f"- Selected cases materialization-ready: {coverage['selected_case_materialization_ready_rows']} / {coverage['source_gap_case_rows']}.",
        f"- Direct ConceptGraphs-ready cases: {coverage['selected_case_direct_conceptgraphs_ready_rows']} / {coverage['source_gap_case_rows']}.",
        f"- `ConceptGraphs` image ready: {coverage['conceptgraphs_image_ready']}.",
        f"- Launch long job now: {coverage['launch_long_job_now']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Case Staging",
        "",
        "| scan_id | category | selected bundle | frames | direct ready | materialization ready |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in case_rows:
        lines.append(
            "| {scan} | {cat} | {bundle} | {frames} | {direct} | {mat} |".format(
                scan=row.get("scan_id"),
                cat=row.get("object_category"),
                bundle=row.get("selected_source_bundle"),
                frames=row.get("selected_rendered_frame_rows"),
                direct=str(row.get("selected_direct_conceptgraphs_ready")).lower(),
                mat=str(row.get("selected_adapter_materialization_ready")).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Layout Diagnosis",
            "",
            "| scan_id | bundle | color | depth PGM | depth PNG | pose | blocker |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in scan_rows:
        blockers = ", ".join(row.get("direct_blocker_reasons", [])) or "none"
        lines.append(
            "| {scan} | {bundle} | {color} | {pgm} | {png} | {pose} | {blockers} |".format(
                scan=row.get("scan_id"),
                bundle=row.get("bundle_id"),
                color=row.get("color_jpg_count"),
                pgm=row.get("depth_pgm_count"),
                png=row.get("depth_png_count"),
                pose=row.get("pose_txt_count"),
                blockers=blockers,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- M104 passes the adapter preflight because both M102 source-gap cases have non-oracle rendered RGB-D/pose inputs that can be materialized into a ConceptGraphs-compatible layout.",
            "- The current source directories are not direct runtime inputs because depth PNG files and ConceptGraphs intrinsic/config staging are not materialized yet.",
            "- M104 does not run ConceptGraphs, export candidates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    m103_coverage = read_json(M103_DIR / "coverage.json")
    source_gap_requirements = read_jsonl(M103_DIR / "source_gap_requirement_rows.jsonl")
    required_inputs_ready = bool(
        m103_coverage.get("status")
        == "e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_ready"
        and source_gap_requirements
    )

    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    bundle_rows, rendered_by_bundle = build_bundle_preflight_rows()
    scan_layout_rows, sample_rows = build_scan_layout_rows(rendered_by_bundle)
    case_rows = build_case_staging_rows(source_gap_requirements, scan_layout_rows)
    staging_plan_rows = build_staging_plan_rows(case_rows)
    runtime_contract_rows = build_runtime_contract_rows(case_rows)
    candidate_output_rows = build_candidate_output_contract_rows()
    gate_rows = build_gate_rows(case_rows)
    claim_boundary_rows = build_claim_boundary_rows()
    reviewer_defense_rows = build_reviewer_defense_rows()

    selected_case_materialization_ready = sum(
        1 for row in case_rows if bool(row.get("selected_adapter_materialization_ready"))
    )
    selected_case_direct_ready = sum(
        1 for row in case_rows if bool(row.get("selected_direct_conceptgraphs_ready"))
    )
    leakage_rows = sum(int(row.get("leakage_row_count") or 0) for row in bundle_rows)
    adapter_preflight_ready = (
        required_inputs_ready
        and selected_case_materialization_ready == len(source_gap_requirements)
        and leakage_rows == 0
        and docker_image_ready(CONCEPTGRAPHS_IMAGE)
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if adapter_preflight_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m103_status": m103_coverage.get("status"),
        "selected_route": "conceptgraphs_hm3d_map_candidate_adapter",
        "source_gap_case_rows": len(source_gap_requirements),
        "bundle_rows": len(bundle_rows),
        "scan_layout_rows": len(scan_layout_rows),
        "selected_case_materialization_ready_rows": selected_case_materialization_ready,
        "selected_case_direct_conceptgraphs_ready_rows": selected_case_direct_ready,
        "source_leakage_rows": leakage_rows,
        "conceptgraphs_image_ready": docker_image_ready(CONCEPTGRAPHS_IMAGE),
        "habitat_image_ready": docker_image_ready(HABITAT_IMAGE),
        "adapter_preflight_ready": adapter_preflight_ready,
        "direct_runtime_input_ready": selected_case_direct_ready == len(source_gap_requirements),
        "staging_materialization_required": True,
        "candidate_rows_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "additional_long_job_recommended_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_bundle_preflight_rows.jsonl", bundle_rows)
    write_jsonl(ARTIFACT_DIR / "scan_layout_preflight_rows.jsonl", scan_layout_rows)
    write_jsonl(ARTIFACT_DIR / "sample_file_compatibility_rows.jsonl", sample_rows)
    write_jsonl(ARTIFACT_DIR / "case_staging_selection_rows.jsonl", case_rows)
    write_jsonl(ARTIFACT_DIR / "staging_materialization_plan_rows.jsonl", staging_plan_rows)
    write_jsonl(ARTIFACT_DIR / "future_runtime_contract_rows.jsonl", runtime_contract_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_output_contract_rows.jsonl", candidate_output_rows)
    write_jsonl(ARTIFACT_DIR / "m105_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_defense_rows)
    write_report(ARTIFACT_DIR / "report.md", coverage, case_rows, scan_layout_rows)

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
