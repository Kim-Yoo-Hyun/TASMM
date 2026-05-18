#!/usr/bin/env python3
"""Plan the E003-M65 OpenMask3D scene-format/model smoke bridge."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M64_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M64_openmask3d_feasibility_decision_v0"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M65_openmask3d_scene_format_model_smoke_plan_v0"
DEFAULT_3RSCAN_SCANS = REPO_ROOT / "local_dataset" / "3RScan" / "scans"
M65_VERSION = "e003_m65_openmask3d_scene_format_model_smoke_plan_v0"
FRAME_RE = re.compile(r"frame-(\d{6})\.")


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


def parse_info_txt(path: Path) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    if not path.exists():
        return parsed
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = [item.strip() for item in line.split("=", 1)]
        if not key:
            continue
        lowered = value.lower()
        if lowered in {"true", "false"}:
            parsed[key] = lowered == "true"
            continue
        try:
            parsed[key] = int(value)
            continue
        except ValueError:
            pass
        try:
            parsed[key] = float(value)
            continue
        except ValueError:
            values = []
            for item in value.split():
                try:
                    values.append(float(item))
                except ValueError:
                    values = []
                    break
            parsed[key] = values if values else value
    return parsed


def frame_ids_for(sequence_dir: Path, suffix: str) -> set[int]:
    ids: set[int] = set()
    for path in sequence_dir.glob(f"frame-*.{suffix}"):
        match = FRAME_RE.search(path.name)
        if match:
            ids.add(int(match.group(1)))
    return ids


def select_uniform(ids: list[int], max_count: int) -> list[int]:
    if len(ids) <= max_count:
        return ids
    if max_count <= 1:
        return [ids[0]]
    selected_indices = [round(i * (len(ids) - 1) / (max_count - 1)) for i in range(max_count)]
    selected = [ids[idx] for idx in selected_indices]
    deduped: list[int] = []
    seen: set[int] = set()
    for value in selected:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    cursor = 0
    while len(deduped) < max_count and cursor < len(ids):
        value = ids[cursor]
        if value not in seen:
            deduped.append(value)
            seen.add(value)
        cursor += 1
    return sorted(deduped)


def matrix4_from_color_info(info: dict[str, Any]) -> list[list[float]]:
    matrix = info.get("m_calibrationColorIntrinsic")
    if isinstance(matrix, list) and len(matrix) == 16:
        return [matrix[i : i + 4] for i in range(0, 16, 4)]
    fx = float(info.get("m_calibrationColorIntrinsic_fx", 0.0))
    fy = float(info.get("m_calibrationColorIntrinsic_fy", 0.0))
    cx = float(info.get("m_calibrationColorIntrinsic_cx", 0.0))
    cy = float(info.get("m_calibrationColorIntrinsic_cy", 0.0))
    return [
        [fx, 0.0, cx, 0.0],
        [0.0, fy, cy, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def build_scene_manifest(
    smoke_contract: dict[str, Any],
    gap_rows: list[dict[str, Any]],
    scans_root: Path,
    planned_m66_dir: Path,
    max_frames_per_scan: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected_scans = [str(item) for item in smoke_contract["selected_scans_for_first_smoke"]]
    direct_gap_rows = [row for row in gap_rows if row.get("openmask3d_relevance") == "direct"]
    direct_rows_by_scan = {}
    for row in direct_gap_rows:
        direct_rows_by_scan.setdefault(str(row["current_rescan_id"]), []).append(row)

    scene_rows: list[dict[str, Any]] = []
    scene_entries: list[dict[str, Any]] = []
    for scan_id in selected_scans:
        scan_dir = scans_root / scan_id
        sequence_dir = scan_dir / "sequence"
        info = parse_info_txt(sequence_dir / "_info.txt")
        available = sorted(
            frame_ids_for(sequence_dir, "color.jpg")
            & frame_ids_for(sequence_dir, "depth.pgm")
            & frame_ids_for(sequence_dir, "pose.txt")
        )
        selected_frames = select_uniform(available, max_frames_per_scan)
        staged_scene_dir = planned_m66_dir / "staged_scenes" / scan_id
        scene_ply = scan_dir / "labels.instances.annotated.v2.ply"
        frame_rows = []
        for target_index, source_frame_id in enumerate(selected_frames):
            source_stem = f"frame-{source_frame_id:06d}"
            frame_rows.append(
                {
                    "target_frame_id": target_index,
                    "source_frame_id": source_frame_id,
                    "source_color": str(sequence_dir / f"{source_stem}.color.jpg"),
                    "source_depth_pgm": str(sequence_dir / f"{source_stem}.depth.pgm"),
                    "source_pose": str(sequence_dir / f"{source_stem}.pose.txt"),
                    "staged_color": str(staged_scene_dir / "color" / f"{target_index}.jpg"),
                    "staged_depth_png": str(staged_scene_dir / "depth" / f"{target_index}.png"),
                    "staged_pose": str(staged_scene_dir / "pose" / f"{target_index}.txt"),
                    "depth_conversion": "pgm_to_png_uint16_preserve_depth_shift",
                }
            )

        direct_targets = direct_rows_by_scan.get(scan_id, [])
        target_labels = sorted({str(row["label_canonical"]) for row in direct_targets})
        target_uids = sorted({str(row["target_uid"]) for row in direct_targets})
        entry = {
            "available_rgbd_pose_frame_triplets": len(available),
            "color_resolution": {
                "height": info.get("m_colorHeight"),
                "width": info.get("m_colorWidth"),
            },
            "depth_resolution": {
                "height": info.get("m_depthHeight"),
                "width": info.get("m_depthWidth"),
            },
            "depth_scale": info.get("m_depthShift", 1000),
            "direct_gap_query_rows": len(direct_targets),
            "direct_gap_target_labels": target_labels,
            "direct_gap_target_uids": target_uids,
            "frame_rows": frame_rows,
            "intrinsic_color_matrix_4x4": matrix4_from_color_info(info),
            "openmask3d_scene_dir": str(staged_scene_dir),
            "planned_frame_count": len(selected_frames),
            "scan_id": scan_id,
            "scene_ply_source": str(scene_ply),
            "scene_ply_staged": str(staged_scene_dir / f"{scan_id}.ply"),
            "selected_source_frame_ids": selected_frames,
            "source_info_txt": str(sequence_dir / "_info.txt"),
            "source_scan_dir": str(scan_dir),
            "staged_intrinsic_color_txt": str(staged_scene_dir / "intrinsic" / "intrinsic_color.txt"),
            "stage_ready_now": False,
            "stage_requirements": [
                "copy_or_symlink_scene_ply",
                "copy_or_symlink_color_jpg",
                "copy_pose_txt_as_no_padding_frame_id",
                "write_intrinsic_color_txt_as_4x4_matrix",
                "convert_depth_pgm_to_png_with_depth_scale_1000",
            ],
        }
        scene_entries.append(entry)
        for row in frame_rows:
            scene_rows.append(
                {
                    "scan_id": scan_id,
                    "target_frame_id": row["target_frame_id"],
                    "source_frame_id": row["source_frame_id"],
                    "source_color": row["source_color"],
                    "source_depth_pgm": row["source_depth_pgm"],
                    "source_pose": row["source_pose"],
                    "staged_color": row["staged_color"],
                    "staged_depth_png": row["staged_depth_png"],
                    "staged_pose": row["staged_pose"],
                }
            )

    manifest = {
        "depth_conversion_note": "3RScan depth is .pgm. OpenMask3D single-scene README expects depth images as .png/.jpg/.jpeg, so M66 must convert PGM to 16-bit PNG while preserving depthShift=1000 semantics.",
        "m65_version": M65_VERSION,
        "max_frames_per_scan": max_frames_per_scan,
        "openmask3d_expected_layout": {
            "color": "color/{FRAME_ID}.jpg",
            "depth": "depth/{FRAME_ID}.png",
            "frame_id_rule": "no zero padding, starts from 0",
            "intrinsic": "intrinsic/intrinsic_color.txt",
            "ply": "{scene_id}.ply",
            "pose": "pose/{FRAME_ID}.txt",
            "source": "https://github.com/OpenMask3D/openmask3d",
        },
        "planned_m66_stage_root": str(planned_m66_dir / "staged_scenes"),
        "scene_count": len(scene_entries),
        "scenes": scene_entries,
        "selected_prompt_labels": smoke_contract["selected_prompt_labels"],
        "selected_scans": selected_scans,
        "source_m64_smoke_contract": str(DEFAULT_M64_DIR / "smoke_contract.json"),
        "status": "scene_format_manifest_ready",
    }
    return manifest, scene_rows


def build_command_plan(
    out_dir: Path,
    scene_manifest_path: Path,
    adapter_contract_path: Path,
    verification_command_path: Path,
    planned_m66_dir: Path,
    scene_manifest: dict[str, Any],
) -> dict[str, Any]:
    log_path = REPO_ROOT / "logs" / "$(date +%Y%m%d_%H%M%S)_e003_m66_openmask3d_model_smoke.log"
    return {
        "background_policy": {
            "long_running_steps": [
                "OpenMask3D repository clone or dependency setup",
                "Docker image pull/build",
                "Mask/SAM checkpoint download",
                "scene staging with depth conversion",
                "OpenMask3D inference",
                "adapter conversion and matching",
            ],
            "log_path_template": str(log_path),
            "must_return_to_main_task_after_launch": True,
            "session_name": "e003_m66_openmask3d_smoke",
            "template": "tmux new-session -d -s e003_m66_openmask3d_smoke 'cd /home/yoohyun/research2 && bash experiments/E003_perception_noise_expansion/artifacts/E003-M65_openmask3d_scene_format_model_smoke_plan_v0/run_m66_openmask3d_smoke.sh > logs/$(date +%Y%m%d_%H%M%S)_e003_m66_openmask3d_model_smoke.log 2>&1'",
        },
        "blockers_before_launch": [
            "Create M66 staging/launch wrapper from this plan",
            "Confirm OpenMask3D Dockerfile or environment route",
            "Provide or download Mask module checkpoint and SAM checkpoint",
            "Run scene staging and verify converted PNG depth files",
        ],
        "command_plan_id": "openmask3d_m66_background_launch_plan_v0",
        "docker_image": "research2/openmask3d-smoke:latest",
        "expected_files_after_success": [
            str(planned_m66_dir / "staged_scenes" / "<scan_id>" / "<scan_id>.ply"),
            str(planned_m66_dir / "staged_scenes" / "<scan_id>" / "intrinsic" / "intrinsic_color.txt"),
            str(planned_m66_dir / "openmask3d_raw" / "<scan_id>" / "<timestamp>" / "<scan_id>_masks.pt"),
            str(planned_m66_dir / "openmask3d_raw" / "<scan_id>" / "<timestamp>" / "<scan_id>_openmask3d_features.npy"),
            str(planned_m66_dir / "container_output" / "real_proposals.jsonl"),
            str(planned_m66_dir / "validator" / "coverage.json"),
            str(planned_m66_dir / "matching" / "coverage.json"),
        ],
        "m65_artifacts": {
            "adapter_contract": str(adapter_contract_path),
            "scene_manifest": str(scene_manifest_path),
            "verification_command": str(verification_command_path),
        },
        "next_launch_status": "not_launched",
        "openmask3d_repo_dir": str(EXPERIMENT_ROOT / "external" / "openmask3d"),
        "planned_m66_dir": str(planned_m66_dir),
        "prompt_labels": scene_manifest["selected_prompt_labels"],
        "runnable_now": False,
        "scene_count": scene_manifest["scene_count"],
        "stage_command_template": "python experiments/E003_perception_noise_expansion/tools/stage_m66_openmask3d_scene_format.py --manifest {scene_manifest} --out-dir {planned_m66_dir}/staged_scenes",
        "status": "openmask3d_command_plan_ready_not_launched",
        "workdir": str(REPO_ROOT),
    }


def build_adapter_contract(schema: dict[str, Any], scene_manifest: dict[str, Any], planned_m66_dir: Path) -> dict[str, Any]:
    required_fields = sorted(schema.get("required_fields", {}).keys())
    return {
        "adapter_contract_id": "openmask3d_to_real_proposal_prediction_jsonl_v0",
        "allowed_inputs": [
            "OpenMask3D class-agnostic mask tensor",
            "OpenMask3D per-mask CLIP feature array",
            "staged scene point cloud",
            "staged frame manifest",
            "prompt labels from M64",
        ],
        "forbidden_inputs": [
            "target_uid before evaluation",
            "3DSSG object instance id before evaluation",
            "query_bridge_success",
            "M60/M63 matched_target_uid before proposal row creation",
        ],
        "input_files": [
            str(planned_m66_dir / "openmask3d_raw" / "<scan_id>" / "<timestamp>" / "<scan_id>_masks.pt"),
            str(planned_m66_dir / "openmask3d_raw" / "<scan_id>" / "<timestamp>" / "<scan_id>_openmask3d_features.npy"),
            str(planned_m66_dir / "staged_scenes" / "<scan_id>" / "<scan_id>.ply"),
        ],
        "output_file": str(planned_m66_dir / "container_output" / "real_proposals.jsonl"),
        "output_schema_id": schema.get("schema_id", "real_proposal_prediction_jsonl_v0"),
        "required_output_fields": required_fields,
        "row_mapping": {
            "bbox_2d": "null unless a crop/frame diagnostic is exported",
            "camera_intrinsics_source": "OpenMask3D staged intrinsic/intrinsic_color.txt derived from 3RScan _info.txt",
            "camera_pose_source": "OpenMask3D staged pose/{frame_id}.txt derived from 3RScan sequence poses",
            "centroid_world_m": "mean or robust center of scene points selected by one OpenMask3D mask",
            "confidence": "normalized CLIP text-feature similarity for the prompt label",
            "depth_valid_pixel_count": "mask point count or supporting projected depth count",
            "detector_config_id": "openmask3d_scene_format_model_smoke_v0",
            "detector_id": "OpenMask3D",
            "frame_ids": "staged no-padding frame ids that contributed features",
            "label_canonical": "prompt label after local canonicalization",
            "label_text": "raw prompt label",
            "mask_rle": "null for 3D mask output unless 2D mask diagnostic is retained",
            "match_distance_m": "null before M21 matching",
            "match_iou_3d": "null unless 3D IoU support is added",
            "match_status": "unmatched before M21 matching",
            "matched_3dssg_instance_id": "null before M21 matching",
            "pair_uid": "copied from M58/M64 direct bridge rows for the scan/label query context",
            "point_support_world": "path to sampled scene points for the OpenMask3D mask",
            "prompt_set_id": "m64_chair_pillow_direct_gap_v0",
            "proposal_uid": "stable hash of scan_id, mask_index, label, and adapter version",
            "row_uid": "copied to each applicable direct bridge query row for scan/label",
            "scan_id": "current_rescan_id",
            "seed": "fixed adapter seed, default 0",
        },
        "scene_count": scene_manifest["scene_count"],
        "selected_prompt_labels": scene_manifest["selected_prompt_labels"],
        "status": "proposal_adapter_contract_ready",
        "verification_route": [
            "schema validation with validate_real_proposal_output.py",
            "M21 centroid matching against M17 target denominator",
            "M60 query-level bridge evaluation against direct bridge rows",
            "M63 bounded repair comparison as a non-final ablation",
        ],
    }


def build_verification_command(planned_m66_dir: Path) -> dict[str, Any]:
    return {
        "claim_boundary": "Passing this command verifies an OpenMask3D smoke bridge only. It does not by itself support the final real RGB-D/open-vocabulary search claim.",
        "expected_inputs": [
            str(planned_m66_dir / "container_output" / "real_proposals.jsonl"),
            str(planned_m66_dir / "staged_scenes"),
            str(planned_m66_dir / "openmask3d_raw"),
        ],
        "expected_outputs": [
            str(planned_m66_dir / "validator" / "coverage.json"),
            str(planned_m66_dir / "matching" / "coverage.json"),
        ],
        "lightweight_checks": [
            "find experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/staged_scenes -maxdepth 3 -type f | head -40",
            "find experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/openmask3d_raw -type f | rg 'masks\\.pt|features\\.npy' | head -20",
        ],
        "m21_matching_command": "python experiments/E003_perception_noise_expansion/tools/evaluate_m21_detector_matching.py --m20-dir experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0 --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/matching --match-distance-threshold-m 1.0",
        "schema_validation_command": "python experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py --predictions experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/container_output/real_proposals.jsonl --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M66_openmask3d_model_smoke_v0/validator --schema-only-smoke",
        "status": "verification_command_ready",
        "verification_command_id": "openmask3d_m66_verification_command_v0",
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M65 OpenMask3D Smoke Plan",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Selected scans: {coverage['selected_scan_count']}",
            f"- Selected prompt labels: {', '.join(coverage['selected_prompt_labels'])}",
            f"- Planned frame rows: {coverage['planned_frame_rows']}",
            f"- Direct detector-recall-miss rows represented: {coverage['direct_gap_rows_represented']}",
            f"- Scene-format manifest ready: {coverage['scene_format_manifest_ready']}",
            f"- Command plan ready: {coverage['command_plan_ready']}",
            f"- Adapter contract ready: {coverage['adapter_contract_ready']}",
            f"- Verification command ready: {coverage['verification_command_ready']}",
            f"- Docker/model run launched: {coverage['docker_or_model_run_launched']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- M65는 `OpenMask3D`를 direct bridge detector-recall-miss row에 연결하기 위한 실행 전 contract다.",
            "- M65만으로는 `OpenMask3D` 성능, real RGB-D robustness, open-vocabulary search 개선을 주장하지 않는다.",
            "",
            "## 에이전트 추론",
            "",
            "- `OpenMask3D`는 3D instance mask와 CLIP feature를 내므로 현재 `bbox-depth` route의 target-undetected failure를 분리하기에 적합하다.",
            "- 로컬 3RScan depth가 `.pgm`이고 공식 single-scene layout은 `.png/.jpg/.jpeg` depth를 기대하므로 M66의 첫 구현 단위는 depth-preserving staging이어야 한다.",
            "",
            "## 사용자 판단 필요",
            "",
            "- 없음. 다음 단계는 M66에서 staging wrapper와 Docker/model smoke를 background job으로 launch하는 것이다.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m64-dir", default=DEFAULT_M64_DIR, type=Path)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--scans-root", default=DEFAULT_3RSCAN_SCANS, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--max-frames-per-scan", default=24, type=int)
    args = parser.parse_args()

    smoke_contract = load_json(args.m64_dir / "smoke_contract.json")
    gap_rows = load_jsonl(args.m64_dir / "gap_rows.jsonl")
    schema = load_json(args.m17_dir / "proposal_output_schema.json")
    planned_m66_dir = EXPERIMENT_ROOT / "artifacts" / "E003-M66_openmask3d_model_smoke_v0"

    scene_manifest, scene_rows = build_scene_manifest(
        smoke_contract=smoke_contract,
        gap_rows=gap_rows,
        scans_root=args.scans_root,
        planned_m66_dir=planned_m66_dir,
        max_frames_per_scan=args.max_frames_per_scan,
    )
    adapter_contract = build_adapter_contract(schema=schema, scene_manifest=scene_manifest, planned_m66_dir=planned_m66_dir)
    verification_command = build_verification_command(planned_m66_dir=planned_m66_dir)
    command_plan = build_command_plan(
        out_dir=args.out_dir,
        scene_manifest_path=args.out_dir / "scene_format_manifest.json",
        adapter_contract_path=args.out_dir / "proposal_adapter_contract.json",
        verification_command_path=args.out_dir / "verification_command.json",
        planned_m66_dir=planned_m66_dir,
        scene_manifest=scene_manifest,
    )

    direct_rows = [row for row in gap_rows if row.get("openmask3d_relevance") == "direct"]
    represented_scans = {str(scene["scan_id"]) for scene in scene_manifest["scenes"]}
    direct_represented = [row for row in direct_rows if str(row["current_rescan_id"]) in represented_scans]
    frame_count_by_scan = {str(scene["scan_id"]): int(scene["planned_frame_count"]) for scene in scene_manifest["scenes"]}
    target_label_counts = Counter(str(row["label_canonical"]) for row in direct_represented)

    coverage = {
        "adapter_contract_ready": adapter_contract["status"] == "proposal_adapter_contract_ready",
        "command_plan": str(args.out_dir / "openmask3d_command_plan.json"),
        "command_plan_ready": command_plan["status"] == "openmask3d_command_plan_ready_not_launched",
        "direct_gap_rows_represented": len(direct_represented),
        "docker_or_model_run_launched": False,
        "frame_count_by_scan": frame_count_by_scan,
        "m65_version": M65_VERSION,
        "next_action": "E003-M66 stage OpenMask3D scene format, then launch Docker/model smoke as a background job",
        "planned_frame_rows": len(scene_rows),
        "real_rgbd_open_vocab_search_claim_ready": False,
        "scene_format_manifest": str(args.out_dir / "scene_format_manifest.json"),
        "scene_format_manifest_ready": scene_manifest["status"] == "scene_format_manifest_ready",
        "selected_prompt_labels": scene_manifest["selected_prompt_labels"],
        "selected_scan_count": scene_manifest["scene_count"],
        "selected_scans": scene_manifest["selected_scans"],
        "status": "openmask3d_scene_format_model_smoke_plan_ready",
        "target_label_counts": dict(sorted(target_label_counts.items())),
        "verification_command": str(args.out_dir / "verification_command.json"),
        "verification_command_ready": verification_command["status"] == "verification_command_ready",
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "scene_format_manifest.json", scene_manifest)
    write_jsonl(args.out_dir / "scene_frame_manifest.jsonl", scene_rows)
    write_json(args.out_dir / "openmask3d_command_plan.json", command_plan)
    write_json(args.out_dir / "proposal_adapter_contract.json", adapter_contract)
    write_json(args.out_dir / "verification_command.json", verification_command)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")

    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
