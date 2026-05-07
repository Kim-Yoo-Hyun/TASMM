#!/usr/bin/env python3
"""Container-side scaffold for E003 real proposal generation.

This runner supports three small stages:

- scaffold-smoke: validate mounted inputs and write an empty output.
- backend-contract-smoke: validate RGB-D frame/depth/pose access.
- model-smoke: load a GroundingDINO-compatible backend and write a small
  non-empty RGB-D backprojected proposal output when inference succeeds.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SCAFFOLD_VERSION = "e003_m18_container_scaffold_v0"
BACKEND_CONTRACT_VERSION = "e003_m19_real_detector_backend_contract_v0"
MODEL_SMOKE_VERSION = "e003_m20_detector_model_smoke_v0"
SELECTED_BACKEND_ID = "groundingdino_rgbd_backproject_v0"
DEFAULT_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
DEFAULT_DETECTOR_CONFIG_ID = "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0"


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


def frame_triplet_paths(sequence_dir: Path, frame_index: int) -> dict[str, Path]:
    stem = f"frame-{frame_index:06d}"
    return {
        "color": sequence_dir / f"{stem}.color.jpg",
        "depth": sequence_dir / f"{stem}.depth.pgm",
        "pose": sequence_dir / f"{stem}.pose.txt",
    }


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> list[str]:
    labels = []
    for row in prompt_payload.get("labels", []):
        if row.get("detector_prompt_enabled"):
            labels.append(str(row.get("label_canonical")))
    return sorted({label for label in labels if label})


def prompt_lookup(prompt_payload: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in prompt_payload.get("labels", []):
        canonical = str(row.get("label_canonical", "")).strip()
        if not canonical:
            continue
        lookup[canonical.lower()] = canonical
        for prompt in row.get("prompts", []):
            lookup[str(prompt).strip().lower()] = canonical
    return lookup


def normalize_label_text(label: Any) -> str:
    text = str(label).strip().lower().replace(".", " ")
    for prefix in ("a ", "an ", "the "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return " ".join(text.split())


def resolve_canonical_label(label: Any, prompt_map: dict[str, str], active_labels: list[str]) -> str:
    normalized = normalize_label_text(label)
    direct = prompt_map.get(normalized)
    if direct:
        return direct

    matches = []
    for candidate in active_labels:
        candidate_norm = normalize_label_text(candidate)
        index = normalized.find(candidate_norm)
        if index >= 0:
            matches.append((index, -len(candidate_norm), candidate))
    if matches:
        return sorted(matches)[0][2]

    for prompt, canonical in prompt_map.items():
        prompt_norm = normalize_label_text(prompt)
        if prompt_norm and prompt_norm in normalized:
            return canonical
    return normalized


def select_scan_labels(row: dict[str, Any], prompt_payload: dict[str, Any], max_labels: int) -> list[str]:
    enabled = set(detector_prompt_labels(prompt_payload))
    target_labels = [str(label) for label in row.get("target_labels", []) if str(label) in enabled]
    priority = [
        "chair",
        "table",
        "sofa",
        "cabinet",
        "box",
        "bench",
        "plant",
        "pillow",
        "picture",
        "door",
        "light",
        "shelf",
        "tv",
        "sink",
        "curtain",
        "bag",
    ]
    ordered = [label for label in priority if label in target_labels]
    ordered.extend(label for label in target_labels if label not in ordered)
    if not ordered:
        ordered = sorted(enabled)
    return ordered[:max_labels]


def parse_info_txt(path: Path) -> dict[str, Any]:
    payload: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            payload[key.strip()] = value.strip()

    def int_value(key: str, default: int) -> int:
        try:
            return int(float(payload.get(key, default)))
        except (TypeError, ValueError):
            return default

    def float_value(key: str, default: float) -> float:
        try:
            return float(payload.get(key, default))
        except (TypeError, ValueError):
            return default

    def matrix_values(key: str) -> list[float]:
        values = []
        for item in payload.get(key, "").split():
            try:
                values.append(float(item))
            except ValueError:
                continue
        return values

    depth_intrinsic = matrix_values("m_calibrationDepthIntrinsic")
    color_intrinsic = matrix_values("m_calibrationColorIntrinsic")
    return {
        "color_height": int_value("m_colorHeight", 540),
        "color_intrinsic": color_intrinsic,
        "color_width": int_value("m_colorWidth", 960),
        "depth_height": int_value("m_depthHeight", 172),
        "depth_intrinsic": depth_intrinsic,
        "depth_shift": float_value("m_depthShift", 1000.0),
        "depth_width": int_value("m_depthWidth", 224),
        "raw": payload,
    }


def load_pose_matrix(path: Path) -> list[list[float]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            values = [float(item) for item in line.split()]
            if values:
                rows.append(values)
    if len(rows) != 4 or any(len(row) != 4 for row in rows):
        return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    if any(not math.isfinite(value) for row in rows for value in row):
        return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    return rows


def matvec4(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[row][col] * vector[col] for col in range(4)) for row in range(4)]


def backproject_bbox_to_world(
    bbox_xyxy: list[float],
    color_size: tuple[int, int],
    depth_path: Path,
    pose_path: Path,
    info: dict[str, Any],
) -> dict[str, Any] | None:
    import numpy as np
    from PIL import Image

    depth = np.array(Image.open(depth_path), dtype=np.float32)
    if depth.ndim != 2:
        return None
    color_w, color_h = color_size
    depth_h, depth_w = depth.shape
    x1, y1, x2, y2 = bbox_xyxy
    x1 = max(0.0, min(float(color_w - 1), x1))
    x2 = max(0.0, min(float(color_w - 1), x2))
    y1 = max(0.0, min(float(color_h - 1), y1))
    y2 = max(0.0, min(float(color_h - 1), y2))
    if x2 <= x1 or y2 <= y1:
        return None

    sx = depth_w / max(float(color_w), 1.0)
    sy = depth_h / max(float(color_h), 1.0)
    dx1 = max(0, min(depth_w - 1, int(math.floor(x1 * sx))))
    dx2 = max(0, min(depth_w, int(math.ceil(x2 * sx))))
    dy1 = max(0, min(depth_h - 1, int(math.floor(y1 * sy))))
    dy2 = max(0, min(depth_h, int(math.ceil(y2 * sy))))
    if dx2 <= dx1 or dy2 <= dy1:
        return None

    region = depth[dy1:dy2, dx1:dx2]
    valid = region[np.isfinite(region) & (region > 0)]
    if valid.size == 0:
        return None

    depth_shift = float(info.get("depth_shift") or 1000.0)
    z = float(np.median(valid) / depth_shift)
    if not math.isfinite(z) or z <= 0:
        return None

    intrinsic = info.get("depth_intrinsic") or []
    fx = float(intrinsic[0]) if len(intrinsic) > 0 else 1.0
    cx = float(intrinsic[2]) if len(intrinsic) > 2 else depth_w / 2.0
    fy = float(intrinsic[5]) if len(intrinsic) > 5 else 1.0
    cy = float(intrinsic[6]) if len(intrinsic) > 6 else depth_h / 2.0
    if fx == 0 or fy == 0:
        return None

    u = ((x1 + x2) / 2.0) * sx
    v = ((y1 + y2) / 2.0) * sy
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    world = matvec4(load_pose_matrix(pose_path), [x, y, z, 1.0])
    centroid = [float(world[0]), float(world[1]), float(world[2])]
    if any(not math.isfinite(value) for value in centroid):
        return None
    return {
        "centroid_world_m": centroid,
        "depth_median_m": z,
        "depth_valid_pixel_count": int(valid.size),
    }


def move_batch_to_device(batch: Any, device: str) -> dict[str, Any]:
    moved: dict[str, Any] = {}
    for key, value in batch.items():
        moved[key] = value.to(device) if hasattr(value, "to") else value
    return moved


def run_model_smoke(
    manifest_rows: list[dict[str, Any]],
    prompt_payload: dict[str, Any],
    dataset_root: Path,
    output_path: Path,
    backend_id: str,
    model_id: str,
    max_scans: int,
    max_frames_per_scan: int,
    max_labels: int,
    max_predictions: int,
    max_predictions_per_frame: int | None,
    min_predictions: int,
    proposal_run_id: str,
    stop_after_min_predictions: bool,
    threshold: float,
    text_threshold: float,
    seed: str,
) -> dict[str, Any]:
    import torch
    import transformers
    from PIL import Image
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    torch.manual_seed(int(seed))
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    rows: list[dict[str, Any]] = []
    prompt_map = prompt_lookup(prompt_payload)
    prompt_set_id = str(prompt_payload.get("prompt_set_id", "unknown_prompt_set"))
    inference_rows = []
    max_predictions_reached = False
    skipped_no_depth = 0
    scanned_frame_count = 0
    selected_scan_rows = manifest_rows[:max_scans]

    for manifest_row in selected_scan_rows:
        scan_id = str(manifest_row.get("scan_id"))
        sequence_dir = dataset_root / "3RScan" / "scans" / scan_id / "sequence"
        info_path = sequence_dir / "_info.txt"
        info = parse_info_txt(info_path)
        labels = select_scan_labels(manifest_row, prompt_payload, max_labels=max_labels)
        text_labels = [[f"a {label}" for label in labels]]
        for frame_index in [int(index) for index in manifest_row.get("sampled_frame_indices", [])[:max_frames_per_scan]]:
            paths = frame_triplet_paths(sequence_dir, frame_index)
            image = Image.open(paths["color"]).convert("RGB")
            scanned_frame_count += 1
            inputs = processor(images=image, text=text_labels, return_tensors="pt")
            model_inputs = move_batch_to_device(inputs, device)
            with torch.no_grad():
                outputs = model(**model_inputs)
            target_sizes = [image.size[::-1]]
            try:
                results = processor.post_process_grounded_object_detection(
                    outputs,
                    model_inputs["input_ids"],
                    threshold=threshold,
                    text_threshold=text_threshold,
                    target_sizes=target_sizes,
                )
            except TypeError:
                results = processor.post_process_grounded_object_detection(
                    outputs,
                    model_inputs["input_ids"],
                    box_threshold=threshold,
                    text_threshold=text_threshold,
                    target_sizes=target_sizes,
                )
            result = results[0]
            frame_predictions = 0
            frame_skipped_no_depth = 0
            frame_id = f"frame-{frame_index:06d}"
            result_labels = result.get("text_labels", result["labels"])
            for local_index, (box, score, raw_label) in enumerate(
                zip(result["boxes"], result["scores"], result_labels),
                start=1,
            ):
                if len(rows) >= max_predictions:
                    max_predictions_reached = True
                    break
                if max_predictions_per_frame is not None and frame_predictions >= max_predictions_per_frame:
                    break
                bbox = [round(float(value), 3) for value in box.tolist()]
                label_text = str(raw_label)
                label_canonical = resolve_canonical_label(label_text, prompt_map, labels)
                projection = backproject_bbox_to_world(
                    bbox_xyxy=bbox,
                    color_size=image.size,
                    depth_path=paths["depth"],
                    pose_path=paths["pose"],
                    info=info,
                )
                if projection is None:
                    skipped_no_depth += 1
                    frame_skipped_no_depth += 1
                    continue
                proposal_uid = f"{proposal_run_id}:{scan_id}:{frame_id}:{len(rows) + 1:05d}"
                rows.append(
                    {
                        "bbox_2d": {frame_id: bbox},
                        "camera_intrinsics_source": str(info_path),
                        "camera_pose_source": str(paths["pose"]),
                        "centroid_world_m": [round(float(value), 6) for value in projection["centroid_world_m"]],
                        "confidence": round(float(score), 6),
                        "depth_valid_pixel_count": int(projection["depth_valid_pixel_count"]),
                        "detector_config_id": DEFAULT_DETECTOR_CONFIG_ID,
                        "detector_id": backend_id,
                        "frame_ids": [frame_id],
                        "label_canonical": label_canonical,
                        "label_text": label_text,
                        "mask_rle": None,
                        "match_distance_m": None,
                        "match_iou_3d": None,
                        "match_status": "unmatched",
                        "matched_3dssg_instance_id": None,
                        "pair_uid": str(manifest_row.get("manifest_row_uid")),
                        "point_support_world": [],
                        "prompt_set_id": prompt_set_id,
                        "proposal_uid": proposal_uid,
                        "row_uid": f"{proposal_run_id}:{scan_id}:{frame_id}:{local_index}",
                        "scan_id": scan_id,
                        "seed": str(seed),
                    }
                )
                frame_predictions += 1
            inference_rows.append(
                {
                    "frame_id": frame_id,
                    "label_count": len(labels),
                    "raw_prediction_count": len(result["scores"]),
                    "scan_id": scan_id,
                    "skipped_no_depth_prediction_count": frame_skipped_no_depth,
                    "written_prediction_count": frame_predictions,
                }
            )
            if max_predictions_reached:
                break
            if stop_after_min_predictions and len(rows) >= min_predictions:
                break
        if max_predictions_reached:
            break
        if stop_after_min_predictions and len(rows) >= min_predictions:
            break

    write_jsonl(output_path, rows)
    prediction_ready = len(rows) >= min_predictions
    return {
        "backend_id": backend_id,
        "device": device,
        "detector_backend_integrated": True,
        "detector_predictions_ready": prediction_ready,
        "inference_rows": inference_rows,
        "max_frames_per_scan": max_frames_per_scan,
        "max_labels": max_labels,
        "max_predictions": max_predictions,
        "max_predictions_per_frame": max_predictions_per_frame,
        "max_predictions_reached": max_predictions_reached,
        "max_scans": max_scans,
        "min_predictions": min_predictions,
        "model_id": model_id,
        "model_loaded": True,
        "model_smoke_version": MODEL_SMOKE_VERSION,
        "output": str(output_path),
        "prediction_rows": len(rows),
        "proposal_run_id": proposal_run_id,
        "scanned_frame_count": scanned_frame_count,
        "selected_scan_count": len(selected_scan_rows),
        "skipped_no_depth_predictions": skipped_no_depth,
        "stop_after_min_predictions": stop_after_min_predictions,
        "status": "model_smoke_predictions_ready" if prediction_ready else "model_smoke_no_predictions",
        "threshold": threshold,
        "text_threshold": text_threshold,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
    }


def validate_inputs(manifest: Path, schema: Path, prompt_set: Path) -> dict[str, Any]:
    manifest_rows = load_jsonl(manifest)
    schema_payload = load_json(schema)
    prompt_payload = load_json(prompt_set)
    required_fields = schema_payload.get("required_fields", {})
    prompt_labels = prompt_payload.get("labels", [])

    errors: list[str] = []
    if not manifest_rows:
        errors.append("manifest has 0 rows")
    if schema_payload.get("schema_id") != "real_proposal_prediction_jsonl_v0":
        errors.append("schema_id is not real_proposal_prediction_jsonl_v0")
    if not isinstance(required_fields, dict) or not required_fields:
        errors.append("schema required_fields is empty")
    if not prompt_labels:
        errors.append("prompt_set labels are empty")

    scan_count = len({row.get("scan_id") for row in manifest_rows})
    sampled_frames = sum(int(row.get("sampled_frame_count", 0) or 0) for row in manifest_rows)
    detector_target_count = sum(int(row.get("detector_target_count", 0) or 0) for row in manifest_rows)

    return {
        "detector_target_count": detector_target_count,
        "errors": errors,
        "manifest_rows": len(manifest_rows),
        "prompt_label_count": len(prompt_labels),
        "sampled_frame_count": sampled_frames,
        "scan_count": scan_count,
        "schema_id": schema_payload.get("schema_id"),
        "valid": not errors,
    }


def validate_rgbd_sequence_contract(
    manifest_rows: list[dict[str, Any]],
    prompt_payload: dict[str, Any],
    dataset_root: Path,
    backend_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    scan_rows = []
    total_sampled_frames = 0
    total_ready_triplets = 0
    total_missing_triplets = 0

    labels = detector_prompt_labels(prompt_payload)
    if not labels:
        errors.append("no detector prompt labels available")

    for row in manifest_rows:
        scan_id = str(row.get("scan_id"))
        sampled_indices = [int(index) for index in row.get("sampled_frame_indices", [])]
        sequence_dir = dataset_root / "3RScan" / "scans" / scan_id / "sequence"
        info_path = sequence_dir / "_info.txt"
        ready_triplets = 0
        missing_triplets = 0
        missing_examples = []
        if not sequence_dir.exists():
            errors.append(f"missing sequence dir for scan {scan_id}: {sequence_dir}")
        if not info_path.exists():
            errors.append(f"missing _info.txt for scan {scan_id}: {info_path}")
        for frame_index in sampled_indices:
            total_sampled_frames += 1
            paths = frame_triplet_paths(sequence_dir, frame_index)
            missing = [name for name, path in paths.items() if not path.exists()]
            if missing:
                missing_triplets += 1
                total_missing_triplets += 1
                if len(missing_examples) < 5:
                    missing_examples.append({"frame_index": frame_index, "missing": missing})
            else:
                ready_triplets += 1
                total_ready_triplets += 1
        scan_rows.append(
            {
                "info_ready": info_path.exists(),
                "missing_examples": missing_examples,
                "missing_triplets": missing_triplets,
                "ready_triplets": ready_triplets,
                "sampled_frame_count": len(sampled_indices),
                "scan_id": scan_id,
                "sequence_dir": str(sequence_dir),
            }
        )

    if total_missing_triplets:
        errors.append(f"missing RGB-D/pose frame triplets: {total_missing_triplets}")
    if backend_id != SELECTED_BACKEND_ID:
        warnings.append(f"backend_id differs from selected default: {backend_id}")

    return {
        "backend_id": backend_id,
        "detector_prompt_label_count": len(labels),
        "errors": errors,
        "scan_rows": scan_rows,
        "selected_backend": {
            "backend_id": SELECTED_BACKEND_ID,
            "detector_family": "GroundingDINO",
            "expected_model_dependency": "GroundingDINO-compatible open-vocabulary 2D detector",
            "geometry_stage": "RGB-D depth backprojection from 2D boxes/masks into scan/world coordinates",
            "model_dependency_installed": False,
            "output_schema": "real_proposal_prediction_jsonl_v0",
            "segmentation_dependency": "optional SAM/SAM2 mask refinement after 2D box detection",
        },
        "total_missing_triplets": total_missing_triplets,
        "total_ready_triplets": total_ready_triplets,
        "total_sampled_frames": total_sampled_frames,
        "valid": not errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--detector", default="open_vocab_rgbd_detector_v0")
    parser.add_argument("--backend-contract-output", type=Path)
    parser.add_argument("--dataset-root", default=Path("/data"), type=Path)
    parser.add_argument("--max-frames-per-scan", default=4, type=int)
    parser.add_argument("--max-labels", default=12, type=int)
    parser.add_argument("--max-predictions", default=20, type=int)
    parser.add_argument("--max-predictions-per-frame", type=int)
    parser.add_argument("--max-scans", default=1, type=int)
    parser.add_argument("--min-predictions", default=1, type=int)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--prompt-set", required=True, type=Path)
    parser.add_argument("--proposal-run-id", default="m20")
    parser.add_argument("--seed", default="101")
    parser.add_argument("--continue-after-min-predictions", action="store_true")
    parser.add_argument("--text-threshold", default=0.10, type=float)
    parser.add_argument("--threshold", default=0.10, type=float)
    parser.add_argument(
        "--mode",
        choices=["scaffold-smoke", "backend-contract-smoke", "model-smoke"],
        default="scaffold-smoke",
        help="Validate mounted inputs without fabricating detector predictions.",
    )
    args = parser.parse_args()

    input_status = validate_inputs(args.manifest, args.schema, args.prompt_set)
    if not input_status["valid"]:
        write_json(
            args.output.parent / "run_metadata.json",
            {
                "detector_backend_integrated": False,
                "detector_predictions_ready": False,
                "errors": input_status["errors"],
                "mode": args.mode,
                "scaffold_version": SCAFFOLD_VERSION,
                "status": "input_validation_failed",
            },
        )
        return 2

    manifest_rows = load_jsonl(args.manifest)
    prompt_payload = load_json(args.prompt_set)
    backend_status = None
    if args.mode in {"backend-contract-smoke", "model-smoke"}:
        backend_status = validate_rgbd_sequence_contract(
            manifest_rows=manifest_rows,
            prompt_payload=prompt_payload,
            dataset_root=args.dataset_root,
            backend_id=args.detector,
        )
        backend_contract_output = args.backend_contract_output or (args.output.parent / "backend_contract.json")
        write_json(
            backend_contract_output,
            {
                "allowed_detector_inputs": [
                    "RGB frames",
                    "Depth frames",
                    "Camera poses",
                    "Camera intrinsics",
                    "Open-vocabulary prompt text",
                ],
                "backend_status": backend_status,
                "blocked_detector_inputs": [
                    "3DSSG object instance ids",
                    "evaluation target ids",
                    "candidate_is_target",
                    "matched_3dssg_instance_id",
                ],
                "contract_version": BACKEND_CONTRACT_VERSION,
                "detector_backend_integrated": False,
                "detector_predictions_ready": False,
                "selected_backend_id": SELECTED_BACKEND_ID,
            },
        )
        if not backend_status["valid"]:
            write_json(
                args.output.parent / "run_metadata.json",
                {
                    "backend_status": backend_status,
                    "detector_backend_integrated": False,
                    "detector_predictions_ready": False,
                    "mode": args.mode,
                    "scaffold_version": SCAFFOLD_VERSION,
                    "status": "backend_contract_validation_failed",
                },
            )
            return 2

    if args.mode == "model-smoke":
        try:
            model_status = run_model_smoke(
                manifest_rows=manifest_rows,
                prompt_payload=prompt_payload,
                dataset_root=args.dataset_root,
                output_path=args.output,
                backend_id=args.detector,
                model_id=args.model_id,
                max_scans=max(1, args.max_scans),
                max_frames_per_scan=max(1, args.max_frames_per_scan),
                max_labels=max(1, args.max_labels),
                max_predictions=max(1, args.max_predictions),
                max_predictions_per_frame=(
                    max(1, args.max_predictions_per_frame) if args.max_predictions_per_frame else None
                ),
                min_predictions=max(1, args.min_predictions),
                proposal_run_id=args.proposal_run_id,
                stop_after_min_predictions=not args.continue_after_min_predictions,
                threshold=args.threshold,
                text_threshold=args.text_threshold,
                seed=str(args.seed),
            )
        except Exception as exc:
            model_status = {
                "backend_id": args.detector,
                "detector_backend_integrated": False,
                "detector_predictions_ready": False,
                "error": repr(exc),
                "model_id": args.model_id,
                "model_loaded": False,
                "model_smoke_version": MODEL_SMOKE_VERSION,
                "prediction_rows": 0,
                "status": "model_smoke_failed",
            }
            write_json(args.output.parent / "model_smoke.json", model_status)
            write_json(
                args.output.parent / "run_metadata.json",
                {
                    "backend_contract_ready": bool(backend_status and backend_status.get("valid")),
                    "backend_status": backend_status,
                    "detector_backend_integrated": False,
                    "detector_config_id": DEFAULT_DETECTOR_CONFIG_ID,
                    "detector_id": args.detector,
                    "detector_predictions_ready": False,
                    "mode": args.mode,
                    "model_status": model_status,
                    "status": "model_smoke_failed",
                },
            )
            return 2

        write_json(args.output.parent / "model_smoke.json", model_status)
        metadata = {
            "backend_contract_ready": bool(backend_status and backend_status.get("valid")),
            "backend_status": backend_status,
            "detector_backend_integrated": bool(model_status.get("detector_backend_integrated")),
            "detector_config_id": DEFAULT_DETECTOR_CONFIG_ID,
            "detector_id": args.detector,
            "detector_predictions_ready": bool(model_status.get("detector_predictions_ready")),
            "input_status": input_status,
            "mode": args.mode,
            "model_status": model_status,
            "output": str(args.output),
            "prompt_set": str(args.prompt_set),
            "scaffold_version": SCAFFOLD_VERSION,
            "seed": str(args.seed),
            "status": model_status["status"],
        }
        write_json(args.output.parent / "run_metadata.json", metadata)
        print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
        return 0 if model_status.get("detector_predictions_ready") else 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")
    metadata = {
        "backend_contract_ready": bool(backend_status and backend_status.get("valid")),
        "backend_status": backend_status,
        "detector_backend_integrated": False,
        "detector_config_id": "h001_real_proposals_ovdet_v0",
        "detector_id": args.detector,
        "detector_predictions_ready": False,
        "input_status": input_status,
        "mode": args.mode,
        "output": str(args.output),
        "prompt_set": str(args.prompt_set),
        "scaffold_note": "Empty JSONL is a Docker contract smoke output, not detector evidence.",
        "scaffold_version": SCAFFOLD_VERSION,
        "seed": str(args.seed),
        "status": "scaffold_smoke_passed",
    }
    write_json(args.output.parent / "run_metadata.json", metadata)
    print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
