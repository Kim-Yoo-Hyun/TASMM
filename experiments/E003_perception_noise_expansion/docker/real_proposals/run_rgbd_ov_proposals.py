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
from collections import Counter
from pathlib import Path
from typing import Any


SCAFFOLD_VERSION = "e003_m18_container_scaffold_v0"
BACKEND_CONTRACT_VERSION = "e003_m19_real_detector_backend_contract_v0"
MODEL_SMOKE_VERSION = "e003_m20_detector_model_smoke_v0"
SELECTED_BACKEND_ID = "groundingdino_rgbd_backproject_v0"
GROUNDED_SAM_BACKEND_ID = "grounded_sam_mask_backproject_v0"
DEFAULT_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
DEFAULT_SAM_MODEL_ID = "facebook/sam-vit-base"
DEFAULT_DETECTOR_CONFIG_ID = "h001_real_proposals_groundingdino_tiny_rgbd_backproject_v0"
GROUNDED_SAM_DETECTOR_CONFIG_ID = "h001_real_proposals_grounded_sam_mask_backproject_v0"
SUPPORT_EVIDENCE_NONE = "none"
SUPPORT_EVIDENCE_POLICY_ID = "temporal_spatial_support_evidence_v0"
SUPPORT_EVIDENCE_STAGE = "after_prompt_label_cleanup_before_spatial_consolidation_and_caps"
SUPPORT_AWARE_SCORE_MODE = "confidence_sqrt_depth_support_temporal_v0"
SEGMENTATION_NONE = "none"
SEGMENTATION_SAM_VIT_B = "sam_vit_b"
MASK_DEPTH_FILTER_ID = "median_mad_trimmed_mask_depth_v0"


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


def summarize_cleanup_trace(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts: Counter[str] = Counter()
    scan_decision_counts: Counter[str] = Counter()
    scan_label_decision_counts: Counter[str] = Counter()
    frame_decision_counts: Counter[str] = Counter()
    for row in rows:
        decision = str(row.get("cleanup_decision"))
        scan_id = str(row.get("scan_id"))
        frame_id = str(row.get("frame_id"))
        label = str(row.get("label_canonical"))
        decision_counts[decision] += 1
        scan_decision_counts[f"{scan_id}::{decision}"] += 1
        scan_label_decision_counts[f"{scan_id}::{label}::{decision}"] += 1
        frame_decision_counts[f"{scan_id}::{frame_id}::{decision}"] += 1
    return {
        "cleanup_trace_version": "candidate_cleanup_trace_v0",
        "decision_counts": dict(sorted(decision_counts.items())),
        "frame_decision_counts": dict(sorted(frame_decision_counts.items())),
        "row_count": len(rows),
        "scan_decision_counts": dict(sorted(scan_decision_counts.items())),
        "scan_label_decision_counts": dict(sorted(scan_label_decision_counts.items())),
    }


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
    active_exact = {
        normalize_label_text(candidate): candidate
        for candidate in active_labels
        if normalize_label_text(candidate)
    }
    if normalized in active_exact:
        return active_exact[normalized]

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


def detector_config_id(backend_id: str) -> str:
    if backend_id == GROUNDED_SAM_BACKEND_ID:
        return GROUNDED_SAM_DETECTOR_CONFIG_ID
    return DEFAULT_DETECTOR_CONFIG_ID


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


def encode_binary_mask_rle(mask: Any) -> dict[str, Any]:
    import numpy as np

    mask_array = np.asarray(mask, dtype=np.uint8)
    flat = mask_array.reshape(-1)
    counts: list[int] = []
    current = 0
    run_length = 0
    for value in flat:
        bit = 1 if int(value) else 0
        if bit == current:
            run_length += 1
        else:
            counts.append(run_length)
            current = bit
            run_length = 1
    counts.append(run_length)
    return {
        "counts": counts,
        "encoding": "uncompressed_rle_c_order",
        "size": [int(mask_array.shape[0]), int(mask_array.shape[1])],
    }


def resize_mask_to_depth(mask: Any, depth_shape: tuple[int, int]) -> Any:
    import numpy as np
    from PIL import Image

    mask_array = np.asarray(mask, dtype=np.uint8)
    depth_h, depth_w = depth_shape
    if mask_array.shape == (depth_h, depth_w):
        return mask_array.astype(bool)
    resized = Image.fromarray(mask_array * 255).resize((depth_w, depth_h), Image.Resampling.NEAREST)
    return (np.asarray(resized, dtype=np.uint8) > 0)


def backproject_mask_to_world(
    mask: Any,
    depth_path: Path,
    pose_path: Path,
    info: dict[str, Any],
    min_depth_valid_pixels: int,
    point_sample_cap: int,
) -> dict[str, Any] | None:
    import numpy as np
    from PIL import Image

    depth = np.array(Image.open(depth_path), dtype=np.float32)
    if depth.ndim != 2:
        return None
    depth_h, depth_w = depth.shape
    mask_depth = resize_mask_to_depth(mask, (depth_h, depth_w))
    mask_area_px = int(mask_depth.sum())
    if mask_area_px <= 0:
        return None

    valid_mask = mask_depth & np.isfinite(depth) & (depth > 0)
    valid_depth = depth[valid_mask]
    if valid_depth.size < min_depth_valid_pixels:
        return None

    median_depth = float(np.median(valid_depth))
    mad = float(np.median(np.abs(valid_depth - median_depth)))
    if mad > 0:
        tolerance = 3.0 * 1.4826 * mad
        trimmed_mask = valid_mask & (np.abs(depth - median_depth) <= tolerance)
    else:
        low, high = np.percentile(valid_depth, [5, 95])
        trimmed_mask = valid_mask & (depth >= low) & (depth <= high)
    if int(trimmed_mask.sum()) < min_depth_valid_pixels:
        trimmed_mask = valid_mask

    ys, xs = np.nonzero(trimmed_mask)
    if xs.size == 0:
        return None
    if point_sample_cap > 0 and xs.size > point_sample_cap:
        sample_indices = np.linspace(0, xs.size - 1, point_sample_cap).astype(np.int64)
        xs = xs[sample_indices]
        ys = ys[sample_indices]

    depth_shift = float(info.get("depth_shift") or 1000.0)
    z = depth[ys, xs].astype(np.float64) / depth_shift
    intrinsic = info.get("depth_intrinsic") or []
    fx = float(intrinsic[0]) if len(intrinsic) > 0 else 1.0
    cx = float(intrinsic[2]) if len(intrinsic) > 2 else depth_w / 2.0
    fy = float(intrinsic[5]) if len(intrinsic) > 5 else 1.0
    cy = float(intrinsic[6]) if len(intrinsic) > 6 else depth_h / 2.0
    if fx == 0 or fy == 0:
        return None

    x = (xs.astype(np.float64) - cx) * z / fx
    y = (ys.astype(np.float64) - cy) * z / fy
    pose = load_pose_matrix(pose_path)
    world_points = []
    for px, py, pz in zip(x, y, z):
        world = matvec4(pose, [float(px), float(py), float(pz), 1.0])
        world_points.append([float(world[0]), float(world[1]), float(world[2])])
    centroid = [
        float(np.mean([point[axis] for point in world_points]))
        for axis in range(3)
    ]
    if any(not math.isfinite(value) for value in centroid):
        return None
    return {
        "centroid_world_m": centroid,
        "depth_median_m": float(np.median(z)),
        "depth_valid_pixel_count": int(trimmed_mask.sum()),
        "mask_area_px": mask_area_px,
        "mask_depth_valid_pixel_count": int(trimmed_mask.sum()),
        "mask_depth_valid_ratio": float(trimmed_mask.sum()) / float(mask_area_px),
        "point_support_world": [
            [round(float(value), 6) for value in point]
            for point in world_points[: min(len(world_points), 64)]
        ],
    }


def load_sam_backend(segmentation_backend: str, sam_model_id: str, device: str) -> tuple[Any, Any] | None:
    if segmentation_backend == SEGMENTATION_NONE:
        return None
    if segmentation_backend != SEGMENTATION_SAM_VIT_B:
        raise ValueError(f"unsupported segmentation backend: {segmentation_backend}")
    from transformers import SamModel, SamProcessor

    processor = SamProcessor.from_pretrained(sam_model_id)
    model = SamModel.from_pretrained(sam_model_id)
    model.to(device)
    model.eval()
    return processor, model


def build_sam_masks(
    image: Any,
    boxes_xyxy: list[list[float]],
    sam_backend: tuple[Any, Any] | None,
    device: str,
) -> list[dict[str, Any] | None]:
    if not boxes_xyxy:
        return []
    if sam_backend is None:
        return [None for _ in boxes_xyxy]

    import numpy as np
    import torch

    sam_processor, sam_model = sam_backend
    inputs = sam_processor(image, input_boxes=[boxes_xyxy], return_tensors="pt")
    model_inputs = move_batch_to_device(inputs, device)
    with torch.no_grad():
        outputs = sam_model(**model_inputs)
    masks = sam_processor.image_processor.post_process_masks(
        outputs.pred_masks.detach().cpu(),
        inputs["original_sizes"].detach().cpu(),
        inputs["reshaped_input_sizes"].detach().cpu(),
    )[0]
    mask_array = masks.detach().cpu().numpy()
    iou_scores = getattr(outputs, "iou_scores", None)
    score_array = iou_scores.detach().cpu().numpy()[0] if iou_scores is not None else None
    result: list[dict[str, Any] | None] = []
    for idx in range(len(boxes_xyxy)):
        per_box = mask_array[idx]
        if per_box.ndim == 3:
            score_values = score_array[idx] if score_array is not None else np.ones(per_box.shape[0], dtype=np.float32)
            best_idx = int(np.argmax(score_values))
            selected = per_box[best_idx]
            selected_score = float(score_values[best_idx])
        else:
            selected = per_box
            selected_score = float(score_array[idx]) if score_array is not None and score_array.ndim == 1 else None
        result.append(
            {
                "mask": np.asarray(selected > 0, dtype=np.uint8),
                "sam_iou_score": selected_score,
            }
        )
    return result


def move_batch_to_device(batch: Any, device: str) -> dict[str, Any]:
    moved: dict[str, Any] = {}
    for key, value in batch.items():
        moved[key] = value.to(device) if hasattr(value, "to") else value
    return moved


def distance_m(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def score_candidate(row: dict[str, Any], score_mode: str) -> float:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    depth_pixels = float(row.get("depth_valid_pixel_count", 0.0) or 0.0)
    sqrt_depth_score = confidence * min(1.0, math.sqrt(depth_pixels) / math.sqrt(5000.0))
    if score_mode == "confidence":
        return confidence
    if score_mode == "confidence_log_depth":
        return confidence * min(1.0, math.log1p(depth_pixels) / math.log1p(5000.0))
    if score_mode == "confidence_sqrt_depth":
        return sqrt_depth_score
    if score_mode == SUPPORT_AWARE_SCORE_MODE:
        temporal = float(row.get("support_temporal_neighbor_frame_count_r2p0m", 0) or 0)
        spatial = float(row.get("support_spatial_neighbor_count_r1p0m", 0) or 0)
        temporal_factor = min(1.0, max(0.0, temporal) / 2.0)
        spatial_factor = min(1.0, max(0.0, spatial) / 8.0)
        return sqrt_depth_score * (1.0 + 0.25 * temporal_factor + 0.10 * spatial_factor)
    raise ValueError(f"unknown selection score mode: {score_mode}")


def parse_support_radii_m(value: str) -> list[float]:
    radii = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        radius = float(item)
        if radius <= 0 or not math.isfinite(radius):
            raise ValueError(f"invalid support evidence radius: {item}")
        radii.append(radius)
    if not radii:
        raise ValueError("support evidence radii must contain at least one positive value")
    return sorted(set(radii))


def support_radius_suffix(radius_m: float) -> str:
    return str(radius_m).replace(".", "p")


def candidate_frame_ids(row: dict[str, Any]) -> set[str]:
    return {str(frame_id) for frame_id in row.get("frame_ids", [])}


def compute_temporal_spatial_support(
    candidates: list[dict[str, Any]],
    radii_m: list[float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    enriched = [dict(row) for row in candidates]
    if not enriched:
        return enriched, {
            "support_evidence_attached_to_candidate_rows": 0,
            "support_evidence_candidate_rows": 0,
            "support_evidence_groups": 0,
            "support_evidence_policy": SUPPORT_EVIDENCE_POLICY_ID,
            "support_evidence_radii_m": radii_m,
            "support_evidence_stage": SUPPORT_EVIDENCE_STAGE,
            "support_radius_stats": {},
        }

    max_radius = max(radii_m)
    grouped: dict[tuple[str, str], list[int]] = {}
    for idx, row in enumerate(enriched):
        grouped.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(idx)

    radius_stats = {
        support_radius_suffix(radius): {
            "candidate_rows_with_spatial_support": 0,
            "candidate_rows_with_temporal_support": 0,
            "max_spatial_neighbor_count": 0,
            "max_temporal_neighbor_frame_count": 0,
        }
        for radius in radii_m
    }

    for (scan_id, label), indices in grouped.items():
        group_frame_ids = set()
        for idx in indices:
            group_frame_ids.update(candidate_frame_ids(enriched[idx]))

        spatial_counts = {idx: {radius: 0 for radius in radii_m} for idx in indices}
        temporal_frames = {idx: {radius: set() for radius in radii_m} for idx in indices}
        max_confidence = {idx: {radius: None for radius in radii_m} for idx in indices}

        # Grid bucketing keeps later larger reruns deterministic without a dependency.
        buckets: dict[tuple[int, int, int], list[int]] = {}
        for idx in indices:
            centroid = enriched[idx]["centroid_world_m"]
            bucket = tuple(int(math.floor(float(value) / max_radius)) for value in centroid)
            buckets.setdefault(bucket, []).append(idx)

        seen_pairs: set[tuple[int, int]] = set()
        for bucket, bucket_indices in buckets.items():
            bx, by, bz = bucket
            neighbor_indices = []
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        neighbor_indices.extend(buckets.get((bx + ox, by + oy, bz + oz), []))
            for i in bucket_indices:
                for j in neighbor_indices:
                    if i >= j or (i, j) in seen_pairs:
                        continue
                    seen_pairs.add((i, j))
                    d_m = distance_m(enriched[i]["centroid_world_m"], enriched[j]["centroid_world_m"])
                    if d_m > max_radius:
                        continue
                    frames_i = candidate_frame_ids(enriched[i])
                    frames_j = candidate_frame_ids(enriched[j])
                    confidence_i = float(enriched[i].get("confidence", 0.0) or 0.0)
                    confidence_j = float(enriched[j].get("confidence", 0.0) or 0.0)
                    for radius in radii_m:
                        if d_m > radius:
                            continue
                        spatial_counts[i][radius] += 1
                        spatial_counts[j][radius] += 1
                        temporal_frames[i][radius].update(frames_j - frames_i)
                        temporal_frames[j][radius].update(frames_i - frames_j)
                        max_confidence[i][radius] = (
                            confidence_j
                            if max_confidence[i][radius] is None
                            else max(float(max_confidence[i][radius]), confidence_j)
                        )
                        max_confidence[j][radius] = (
                            confidence_i
                            if max_confidence[j][radius] is None
                            else max(float(max_confidence[j][radius]), confidence_i)
                        )

        for idx in indices:
            row = enriched[idx]
            row["support_evidence_policy"] = SUPPORT_EVIDENCE_POLICY_ID
            row["support_group_candidate_count"] = len(indices)
            row["support_group_frame_count"] = len(group_frame_ids)
            row["support_group_key"] = f"{scan_id}::{label}"
            for radius in radii_m:
                suffix = support_radius_suffix(radius)
                spatial_count = spatial_counts[idx][radius]
                temporal_count = len(temporal_frames[idx][radius])
                row[f"support_spatial_neighbor_count_r{suffix}m"] = spatial_count
                row[f"support_temporal_neighbor_frame_count_r{suffix}m"] = temporal_count
                row[f"support_max_neighbor_confidence_r{suffix}m"] = (
                    round(float(max_confidence[idx][radius]), 6)
                    if max_confidence[idx][radius] is not None
                    else None
                )
                stats = radius_stats[suffix]
                if spatial_count > 0:
                    stats["candidate_rows_with_spatial_support"] += 1
                if temporal_count > 0:
                    stats["candidate_rows_with_temporal_support"] += 1
                stats["max_spatial_neighbor_count"] = max(stats["max_spatial_neighbor_count"], spatial_count)
                stats["max_temporal_neighbor_frame_count"] = max(
                    stats["max_temporal_neighbor_frame_count"],
                    temporal_count,
                )

    return enriched, {
        "support_evidence_attached_to_candidate_rows": len(enriched),
        "support_evidence_candidate_rows": len(enriched),
        "support_evidence_groups": len(grouped),
        "support_evidence_policy": SUPPORT_EVIDENCE_POLICY_ID,
        "support_evidence_radii_m": radii_m,
        "support_evidence_stage": SUPPORT_EVIDENCE_STAGE,
        "support_radius_stats": radius_stats,
    }


def select_cap_aware_label_balanced_candidates(
    candidates: list[dict[str, Any]],
    active_scan_labels: dict[str, set[str]],
    enabled_labels: set[str],
    max_predictions: int,
    per_scan_label_cap: int,
    require_scan_prompt_label: bool,
    score_mode: str,
    spatial_consolidation_radius_m: float,
    support_evidence_policy: str,
    support_evidence_radii_m: list[float],
    export_cleanup_trace: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cleaned = []
    cleanup_trace_rows: list[dict[str, Any]] = []
    dropped_non_prompt = 0
    dropped_not_scan_prompt = 0
    for row in candidates:
        scan_id = str(row["scan_id"])
        label = str(row["label_canonical"])
        active_labels = sorted(active_scan_labels.get(scan_id, set()))
        frame_id = str(row.get("frame_ids", ["unknown"])[0])
        cleanup_decision = "keep"
        drop_reason = None
        if label not in enabled_labels:
            dropped_non_prompt += 1
            cleanup_decision = "drop"
            drop_reason = "drop_non_prompt_label"
        elif require_scan_prompt_label and label not in active_scan_labels.get(scan_id, set()):
            dropped_not_scan_prompt += 1
            cleanup_decision = "drop"
            drop_reason = "drop_not_scan_prompt_label"
        if export_cleanup_trace:
            cleanup_trace_rows.append(
                {
                    "active_scan_labels": active_labels,
                    "cleanup_decision": cleanup_decision,
                    "cleanup_stage": "after_projection_before_pre_cap_pool",
                    "drop_reason": drop_reason,
                    "enabled_prompt_label_count": len(enabled_labels),
                    "enabled_prompt_labels": sorted(enabled_labels),
                    "frame_id": frame_id,
                    "label_canonical": label,
                    "label_text": row.get("label_text"),
                    "raw_candidate_uid": row.get("raw_candidate_uid"),
                    "record_type": "candidate_cleanup_trace_v0",
                    "scan_id": scan_id,
                }
            )
        if drop_reason is not None:
            continue
        cleaned.append(dict(row))

    support_summary: dict[str, Any] | None = None
    if support_evidence_policy == SUPPORT_EVIDENCE_POLICY_ID:
        cleaned, support_summary = compute_temporal_spatial_support(cleaned, support_evidence_radii_m)
    elif support_evidence_policy != SUPPORT_EVIDENCE_NONE:
        raise ValueError(f"unknown support evidence policy: {support_evidence_policy}")

    candidate_pool_stage = (
        SUPPORT_EVIDENCE_STAGE
        if support_evidence_policy == SUPPORT_EVIDENCE_POLICY_ID
        else "after_prompt_label_cleanup_before_spatial_consolidation_and_caps"
    )
    candidate_pool_rows = [
        {
            **dict(row),
            "pre_cap_candidate_pool_stage": candidate_pool_stage,
            "pre_cap_candidate_pool_uid": str(row["raw_candidate_uid"]),
        }
        for row in cleaned
    ]

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in cleaned:
        grouped.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(row)

    consolidated = []
    for _, rows in sorted(grouped.items()):
        ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row["raw_candidate_uid"])))
        local_kept: list[dict[str, Any]] = []
        for row in ranked:
            if spatial_consolidation_radius_m <= 0 or all(
                distance_m(row["centroid_world_m"], kept["centroid_world_m"]) > spatial_consolidation_radius_m
                for kept in local_kept
            ):
                local_kept.append(row)
        consolidated.extend(local_kept)

    balanced = []
    balanced_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in consolidated:
        balanced_groups.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(row)
    for key, rows in sorted(balanced_groups.items()):
        ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row["raw_candidate_uid"])))
        for rank, row in enumerate(ranked[:per_scan_label_cap], start=1):
            row = dict(row)
            row["pre_cap_group_key"] = f"{key[0]}::{key[1]}"
            row["pre_cap_group_rank"] = rank
            row["selection_score"] = round(score_candidate(row, score_mode), 8)
            balanced.append(row)

    ranked_final = sorted(balanced, key=lambda row: (-float(row["selection_score"]), str(row["raw_candidate_uid"])))
    selected = ranked_final[:max_predictions]
    for rank, row in enumerate(selected, start=1):
        row["candidate_selection_policy"] = "cap_aware_label_balanced_ranking_v0"
        row["pre_cap_rank"] = rank

    summary = {
        "candidate_selection_policy": "cap_aware_label_balanced_ranking_v0",
        "dropped_non_prompt_label_rows": dropped_non_prompt,
        "dropped_not_scan_prompt_label_rows": dropped_not_scan_prompt,
        "max_predictions": max_predictions,
        "max_predictions_reached_after_policy": len(ranked_final) > max_predictions,
        "per_scan_label_cap": per_scan_label_cap,
        "policy_input_candidate_count": len(cleaned),
        "score_mode": score_mode,
        "selected_candidate_count": len(selected),
        "spatial_consolidated_candidate_count": len(consolidated),
        "spatial_consolidation_radius_m": spatial_consolidation_radius_m,
    }
    if support_summary:
        selected_support_rows = sum(
            1 for row in selected if row.get("support_evidence_policy") == SUPPORT_EVIDENCE_POLICY_ID
        )
        summary.update(
            {
                "support_evidence_attached_to_selected_rows": selected_support_rows,
                "support_evidence_candidate_rows": support_summary["support_evidence_candidate_rows"],
                "support_evidence_groups": support_summary["support_evidence_groups"],
                "support_evidence_policy": support_summary["support_evidence_policy"],
                "support_evidence_radii_m": support_summary["support_evidence_radii_m"],
                "support_evidence_stage": support_summary["support_evidence_stage"],
            }
        )
        summary["_support_summary"] = support_summary
    return selected, summary, candidate_pool_rows, cleanup_trace_rows


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
    candidate_selection_policy: str,
    selection_score_mode: str,
    pre_cap_per_scan_label_cap: int,
    pre_cap_spatial_consolidation_radius_m: float,
    require_scan_prompt_label: bool,
    raw_candidate_collection_cap: int,
    pre_cap_policy_output: Path,
    support_evidence_policy: str,
    support_evidence_radii_m: list[float],
    support_evidence_output: Path,
    export_pre_cap_candidate_pool: bool,
    pre_cap_candidate_pool_output: Path,
    export_cleanup_trace: bool,
    cleanup_trace_output: Path,
    selected_scan_ids: list[str],
    segmentation_backend: str,
    sam_model_id: str,
    mask_depth_filter: str,
    mask_min_depth_valid_pixels: int,
    mask_point_sample_cap: int,
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
    use_grounded_sam = backend_id == GROUNDED_SAM_BACKEND_ID
    if use_grounded_sam and mask_depth_filter != MASK_DEPTH_FILTER_ID:
        raise ValueError(f"unsupported mask depth filter: {mask_depth_filter}")
    if use_grounded_sam and segmentation_backend == SEGMENTATION_NONE:
        raise ValueError("grounded_sam_mask_backproject_v0 requires --segmentation-backend sam_vit_b")
    sam_backend = load_sam_backend(segmentation_backend, sam_model_id, device) if use_grounded_sam else None

    rows: list[dict[str, Any]] = []
    raw_candidates: list[dict[str, Any]] = []
    prompt_map = prompt_lookup(prompt_payload)
    prompt_set_id = str(prompt_payload.get("prompt_set_id", "unknown_prompt_set"))
    inference_rows = []
    max_predictions_reached = False
    raw_candidate_collection_cap_reached = False
    skipped_no_depth = 0
    skipped_mask_projection = 0
    scanned_frame_count = 0
    raw_prediction_count = 0
    mask_projected_candidate_count = 0
    active_scan_labels: dict[str, set[str]] = {}
    selected_scan_set = {str(scan_id) for scan_id in selected_scan_ids if str(scan_id)}
    if selected_scan_set:
        selected_scan_rows = [
            row for row in manifest_rows if str(row.get("scan_id")) in selected_scan_set
        ][:max_scans]
        if not selected_scan_rows:
            raise ValueError(f"no manifest rows matched --scan-id values: {sorted(selected_scan_set)}")
    else:
        selected_scan_rows = manifest_rows[:max_scans]
    use_cap_aware_policy = candidate_selection_policy == "cap_aware_label_balanced_ranking_v0"

    for manifest_row in selected_scan_rows:
        scan_id = str(manifest_row.get("scan_id"))
        sequence_dir = dataset_root / "3RScan" / "scans" / scan_id / "sequence"
        info_path = sequence_dir / "_info.txt"
        info = parse_info_txt(info_path)
        labels = select_scan_labels(manifest_row, prompt_payload, max_labels=max_labels)
        active_scan_labels[scan_id] = set(labels)
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
            frame_skipped_mask_projection = 0
            frame_projected_candidates = 0
            frame_id = f"frame-{frame_index:06d}"
            result_labels = result.get("text_labels", result["labels"])
            raw_prediction_count += len(result["scores"])
            frame_detections = []
            for local_index, (box, score, raw_label) in enumerate(
                zip(result["boxes"], result["scores"], result_labels),
                start=1,
            ):
                if use_cap_aware_policy and len(raw_candidates) >= raw_candidate_collection_cap:
                    raw_candidate_collection_cap_reached = True
                    break
                if not use_cap_aware_policy and len(rows) + len(frame_detections) >= max_predictions:
                    max_predictions_reached = True
                    break
                if (
                    not use_cap_aware_policy
                    and max_predictions_per_frame is not None
                    and len(frame_detections) >= max_predictions_per_frame
                ):
                    break
                bbox = [round(float(value), 3) for value in box.tolist()]
                label_text = str(raw_label)
                label_canonical = resolve_canonical_label(label_text, prompt_map, labels)
                frame_detections.append(
                    {
                        "bbox": bbox,
                        "label_canonical": label_canonical,
                        "label_text": label_text,
                        "local_index": local_index,
                        "score": score,
                    }
                )

            sam_masks = build_sam_masks(
                image=image,
                boxes_xyxy=[row["bbox"] for row in frame_detections],
                sam_backend=sam_backend,
                device=device,
            )
            if not use_cap_aware_policy:
                frame_predictions = 0

            for detection, sam_output in zip(frame_detections, sam_masks):
                bbox = detection["bbox"]
                bbox_projection = backproject_bbox_to_world(
                    bbox_xyxy=bbox,
                    color_size=image.size,
                    depth_path=paths["depth"],
                    pose_path=paths["pose"],
                    info=info,
                )
                mask_projection = None
                mask_rle = None
                if use_grounded_sam:
                    if sam_output is not None:
                        mask_projection = backproject_mask_to_world(
                            mask=sam_output["mask"],
                            depth_path=paths["depth"],
                            pose_path=paths["pose"],
                            info=info,
                            min_depth_valid_pixels=mask_min_depth_valid_pixels,
                            point_sample_cap=mask_point_sample_cap,
                        )
                        mask_rle = encode_binary_mask_rle(sam_output["mask"])
                    if mask_projection is None:
                        skipped_mask_projection += 1
                        frame_skipped_mask_projection += 1
                        continue
                    projection = mask_projection
                    mask_projected_candidate_count += 1
                else:
                    projection = bbox_projection
                if projection is None:
                    skipped_no_depth += 1
                    frame_skipped_no_depth += 1
                    continue
                frame_projected_candidates += 1
                raw_candidate_uid = f"{proposal_run_id}:{scan_id}:{frame_id}:raw:{detection['local_index']:05d}"
                base_row = {
                    "bbox_2d": {frame_id: bbox},
                    "camera_intrinsics_source": str(info_path),
                    "camera_pose_source": str(paths["pose"]),
                    "centroid_world_m": [round(float(value), 6) for value in projection["centroid_world_m"]],
                    "confidence": round(float(detection["score"]), 6),
                    "depth_valid_pixel_count": int(projection["depth_valid_pixel_count"]),
                    "detector_config_id": detector_config_id(backend_id),
                    "detector_id": backend_id,
                    "frame_ids": [frame_id],
                    "label_canonical": detection["label_canonical"],
                    "label_text": detection["label_text"],
                    "mask_rle": {frame_id: mask_rle} if mask_rle is not None else None,
                    "match_distance_m": None,
                    "match_iou_3d": None,
                    "match_status": "unmatched",
                    "matched_3dssg_instance_id": None,
                    "pair_uid": str(manifest_row.get("manifest_row_uid")),
                    "point_support_world": [],
                    "prompt_set_id": prompt_set_id,
                    "raw_candidate_uid": raw_candidate_uid,
                    "raw_frame_local_index": detection["local_index"],
                    "row_uid": f"{proposal_run_id}:{scan_id}:{frame_id}:{detection['local_index']}",
                    "scan_id": scan_id,
                    "seed": str(seed),
                }
                if use_grounded_sam:
                    base_row.update(
                        {
                            "bbox_centroid_world_m": (
                                [round(float(value), 6) for value in bbox_projection["centroid_world_m"]]
                                if bbox_projection
                                else None
                            ),
                            "geometry_source": "mask_depth_backprojection_v0",
                            "mask_area_px": int(projection["mask_area_px"]),
                            "mask_backend_id": segmentation_backend,
                            "mask_backprojection_policy": mask_depth_filter,
                            "mask_centroid_world_m": [
                                round(float(value), 6) for value in projection["centroid_world_m"]
                            ],
                            "mask_depth_valid_pixel_count": int(projection["mask_depth_valid_pixel_count"]),
                            "mask_depth_valid_ratio": round(float(projection["mask_depth_valid_ratio"]), 6),
                            "mask_sam_iou_score": (
                                round(float(sam_output["sam_iou_score"]), 6)
                                if sam_output and sam_output.get("sam_iou_score") is not None
                                else None
                            ),
                            "mask_support_point_sample_path": None,
                            "point_support_world": projection.get("point_support_world", []),
                        }
                    )
                if use_cap_aware_policy:
                    raw_candidates.append(base_row)
                    continue
                proposal_uid = f"{proposal_run_id}:{scan_id}:{frame_id}:{len(rows) + 1:05d}"
                base_row["candidate_selection_policy"] = "detector_order_v0"
                base_row["proposal_uid"] = proposal_uid
                rows.append(
                    base_row
                )
                frame_predictions += 1
            inference_rows.append(
                {
                    "frame_id": frame_id,
                    "label_count": len(labels),
                    "legacy_pre_policy_frame_cap_applied": (
                        not use_cap_aware_policy
                        and max_predictions_per_frame is not None
                        and frame_predictions >= max_predictions_per_frame
                    ),
                    "policy_selected_prediction_count": frame_predictions,
                    "projected_candidate_count": frame_projected_candidates,
                    "raw_prediction_count": len(result["scores"]),
                    "scan_id": scan_id,
                    "skipped_mask_projection_count": frame_skipped_mask_projection,
                    "skipped_no_depth_prediction_count": frame_skipped_no_depth,
                    "written_prediction_count": frame_predictions,
                }
            )
            if raw_candidate_collection_cap_reached:
                break
            if max_predictions_reached:
                break
            if stop_after_min_predictions and len(rows) >= min_predictions:
                break
        if raw_candidate_collection_cap_reached:
            break
        if max_predictions_reached:
            break
        if stop_after_min_predictions and len(rows) >= min_predictions:
            break

    pre_cap_policy_summary: dict[str, Any] | None = None
    support_evidence_summary: dict[str, Any] | None = None
    pre_cap_candidate_pool_rows: list[dict[str, Any]] = []
    cleanup_trace_rows: list[dict[str, Any]] = []
    cleanup_trace_summary: dict[str, Any] | None = None
    if use_cap_aware_policy:
        (
            selected_rows,
            pre_cap_policy_summary,
            pre_cap_candidate_pool_rows,
            cleanup_trace_rows,
        ) = select_cap_aware_label_balanced_candidates(
            candidates=raw_candidates,
            active_scan_labels=active_scan_labels,
            enabled_labels=set(detector_prompt_labels(prompt_payload)),
            max_predictions=max_predictions,
            per_scan_label_cap=pre_cap_per_scan_label_cap,
            require_scan_prompt_label=require_scan_prompt_label,
            score_mode=selection_score_mode,
            spatial_consolidation_radius_m=pre_cap_spatial_consolidation_radius_m,
            support_evidence_policy=support_evidence_policy,
            support_evidence_radii_m=support_evidence_radii_m,
            export_cleanup_trace=bool(export_cleanup_trace),
        )
        if export_pre_cap_candidate_pool:
            write_jsonl(pre_cap_candidate_pool_output, pre_cap_candidate_pool_rows)
        if export_cleanup_trace:
            cleanup_trace_summary = summarize_cleanup_trace(cleanup_trace_rows)
            cleanup_trace_summary.update(
                {
                    "cleanup_trace_output": str(cleanup_trace_output),
                    "cleanup_trace_stage": "after_projection_before_pre_cap_pool",
                    "cleanup_trace_target_independent": True,
                    "blocked_fields": [
                        "target_uid",
                        "candidate_is_target",
                        "matched_3dssg_instance_id",
                        "nearest_target_distance",
                        "query_success_label",
                    ],
                }
            )
            write_jsonl(cleanup_trace_output, cleanup_trace_rows)
        support_evidence_summary = pre_cap_policy_summary.pop("_support_summary", None)
        rows = []
        frame_selected_counts: dict[tuple[str, str], int] = {}
        for index, row in enumerate(selected_rows, start=1):
            row = dict(row)
            frame_id = str(row["frame_ids"][0])
            scan_id = str(row["scan_id"])
            row["proposal_uid"] = f"{proposal_run_id}:{scan_id}:{frame_id}:{index:05d}"
            rows.append(row)
            frame_selected_counts[(scan_id, frame_id)] = frame_selected_counts.get((scan_id, frame_id), 0) + 1
        for item in inference_rows:
            key = (str(item["scan_id"]), str(item["frame_id"]))
            item["policy_selected_prediction_count"] = frame_selected_counts.get(key, 0)
            item["written_prediction_count"] = frame_selected_counts.get(key, 0)
        pre_cap_policy_summary.update(
            {
                "final_prediction_rows": len(rows),
                "pre_cap_candidate_pool_exported": bool(export_pre_cap_candidate_pool),
                "pre_cap_candidate_pool_output": str(pre_cap_candidate_pool_output)
                if export_pre_cap_candidate_pool
                else None,
                "pre_cap_candidate_pool_rows": len(pre_cap_candidate_pool_rows)
                if export_pre_cap_candidate_pool
                else 0,
                "cleanup_trace_exported": bool(export_cleanup_trace),
                "cleanup_trace_output": str(cleanup_trace_output) if export_cleanup_trace else None,
                "cleanup_trace_rows": len(cleanup_trace_rows) if export_cleanup_trace else 0,
                "projected_candidate_count": len(raw_candidates),
                "raw_candidate_collection_cap": raw_candidate_collection_cap,
                "raw_candidate_collection_cap_reached": raw_candidate_collection_cap_reached,
                "raw_prediction_count": raw_prediction_count,
                "require_scan_prompt_label": require_scan_prompt_label,
                "skipped_mask_projection_count": skipped_mask_projection,
                "skipped_no_depth_prediction_count": skipped_no_depth,
            }
        )
        if support_evidence_summary:
            selected_support_rows = sum(
                1 for row in rows if row.get("support_evidence_policy") == SUPPORT_EVIDENCE_POLICY_ID
            )
            support_evidence_summary.update(
                {
                    "final_prediction_rows": len(rows),
                    "support_evidence_attached_to_selected_rows": selected_support_rows,
                    "support_evidence_output": str(support_evidence_output),
                }
            )
            pre_cap_policy_summary["support_evidence_attached_to_selected_rows"] = selected_support_rows
            pre_cap_policy_summary["support_evidence_output"] = str(support_evidence_output)
            write_json(support_evidence_output, support_evidence_summary)
        write_json(pre_cap_policy_output, pre_cap_policy_summary)
        max_predictions_reached = bool(pre_cap_policy_summary["max_predictions_reached_after_policy"])

    write_jsonl(output_path, rows)
    prediction_ready = len(rows) >= min_predictions
    return {
        "backend_id": backend_id,
        "candidate_selection_policy": candidate_selection_policy,
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
        "mask_depth_filter": mask_depth_filter if use_grounded_sam else None,
        "mask_min_depth_valid_pixels": mask_min_depth_valid_pixels if use_grounded_sam else None,
        "mask_point_sample_cap": mask_point_sample_cap if use_grounded_sam else None,
        "mask_projected_candidate_count": mask_projected_candidate_count if use_grounded_sam else 0,
        "output": str(output_path),
        "pre_cap_per_scan_label_cap": pre_cap_per_scan_label_cap if use_cap_aware_policy else None,
        "pre_cap_candidate_pool_exported": bool(export_pre_cap_candidate_pool and use_cap_aware_policy),
        "pre_cap_candidate_pool_output": str(pre_cap_candidate_pool_output)
        if export_pre_cap_candidate_pool and use_cap_aware_policy
        else None,
        "pre_cap_candidate_pool_rows": len(pre_cap_candidate_pool_rows)
        if export_pre_cap_candidate_pool and use_cap_aware_policy
        else 0,
        "cleanup_trace_exported": bool(export_cleanup_trace and use_cap_aware_policy),
        "cleanup_trace_output": str(cleanup_trace_output) if export_cleanup_trace and use_cap_aware_policy else None,
        "cleanup_trace_rows": len(cleanup_trace_rows) if export_cleanup_trace and use_cap_aware_policy else 0,
        "cleanup_trace_summary": cleanup_trace_summary,
        "pre_cap_policy_applied": use_cap_aware_policy,
        "pre_cap_policy_output": str(pre_cap_policy_output) if use_cap_aware_policy else None,
        "pre_cap_policy_summary": pre_cap_policy_summary,
        "pre_cap_spatial_consolidation_radius_m": (
            pre_cap_spatial_consolidation_radius_m if use_cap_aware_policy else None
        ),
        "prediction_rows": len(rows),
        "projected_candidate_count": len(raw_candidates) if use_cap_aware_policy else len(rows),
        "proposal_run_id": proposal_run_id,
        "raw_candidate_collection_cap": raw_candidate_collection_cap if use_cap_aware_policy else None,
        "raw_candidate_collection_cap_reached": raw_candidate_collection_cap_reached,
        "raw_prediction_count": raw_prediction_count,
        "sam_model_id": sam_model_id if use_grounded_sam else None,
        "selection_score_mode": selection_score_mode if use_cap_aware_policy else None,
        "scanned_frame_count": scanned_frame_count,
        "segmentation_backend": segmentation_backend if use_grounded_sam else SEGMENTATION_NONE,
        "selected_scan_count": len(selected_scan_rows),
        "selected_scan_ids": [str(row.get("scan_id")) for row in selected_scan_rows],
        "selected_candidate_count": len(rows) if use_cap_aware_policy else None,
        "skipped_no_depth_predictions": skipped_no_depth,
        "skipped_mask_projection_count": skipped_mask_projection if use_grounded_sam else 0,
        "stop_after_min_predictions": stop_after_min_predictions,
        "support_evidence_output": str(support_evidence_output) if support_evidence_summary else None,
        "support_evidence_policy": support_evidence_policy if use_cap_aware_policy else SUPPORT_EVIDENCE_NONE,
        "support_evidence_summary": support_evidence_summary,
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
    if backend_id not in {SELECTED_BACKEND_ID, GROUNDED_SAM_BACKEND_ID}:
        warnings.append(f"backend_id differs from supported E003 backends: {backend_id}")

    selected_backend = {
        "backend_id": backend_id,
        "detector_family": "GroundingDINO + SAM" if backend_id == GROUNDED_SAM_BACKEND_ID else "GroundingDINO",
        "expected_model_dependency": "GroundingDINO-compatible open-vocabulary 2D detector",
        "geometry_stage": (
            "SAM mask-depth backprojection into scan/world coordinates"
            if backend_id == GROUNDED_SAM_BACKEND_ID
            else "RGB-D depth backprojection from 2D boxes into scan/world coordinates"
        ),
        "model_dependency_installed": False,
        "output_schema": "real_proposal_prediction_jsonl_v0",
        "segmentation_dependency": (
            "facebook/sam-vit-base via transformers"
            if backend_id == GROUNDED_SAM_BACKEND_ID
            else "optional SAM/SAM2 mask refinement after 2D box detection"
        ),
    }

    return {
        "backend_id": backend_id,
        "detector_prompt_label_count": len(labels),
        "errors": errors,
        "scan_rows": scan_rows,
        "selected_backend": selected_backend,
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
    parser.add_argument("--scan-id", action="append", default=[])
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--prompt-set", required=True, type=Path)
    parser.add_argument("--proposal-run-id", default="m20")
    parser.add_argument("--seed", default="101")
    parser.add_argument("--continue-after-min-predictions", action="store_true")
    parser.add_argument("--text-threshold", default=0.10, type=float)
    parser.add_argument("--threshold", default=0.10, type=float)
    parser.add_argument(
        "--segmentation-backend",
        choices=[SEGMENTATION_NONE, SEGMENTATION_SAM_VIT_B],
        default=SEGMENTATION_NONE,
    )
    parser.add_argument("--sam-model-id", default=DEFAULT_SAM_MODEL_ID)
    parser.add_argument("--mask-depth-filter", choices=[MASK_DEPTH_FILTER_ID], default=MASK_DEPTH_FILTER_ID)
    parser.add_argument("--mask-min-depth-valid-pixels", default=200, type=int)
    parser.add_argument("--mask-point-sample-cap", default=2048, type=int)
    parser.add_argument(
        "--candidate-selection-policy",
        choices=["detector_order_v0", "cap_aware_label_balanced_ranking_v0"],
        default="detector_order_v0",
    )
    parser.add_argument(
        "--selection-score-mode",
        choices=["confidence", "confidence_log_depth", "confidence_sqrt_depth", SUPPORT_AWARE_SCORE_MODE],
        default="confidence",
    )
    parser.add_argument("--pre-cap-per-scan-label-cap", default=24, type=int)
    parser.add_argument("--pre-cap-spatial-consolidation-radius-m", default=0.5, type=float)
    parser.add_argument("--require-scan-prompt-label", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--raw-candidate-collection-cap", default=50000, type=int)
    parser.add_argument("--pre-cap-policy-output", default=Path("/outputs/pre_cap_policy_summary.json"), type=Path)
    parser.add_argument("--export-pre-cap-candidate-pool", action="store_true")
    parser.add_argument(
        "--pre-cap-candidate-pool-output",
        default=Path("/outputs/pre_cap_candidate_pool.jsonl"),
        type=Path,
    )
    parser.add_argument("--export-cleanup-trace", action="store_true")
    parser.add_argument("--cleanup-trace-output", default=Path("/outputs/cleanup_trace.jsonl"), type=Path)
    parser.add_argument(
        "--support-evidence-policy",
        choices=[SUPPORT_EVIDENCE_NONE, SUPPORT_EVIDENCE_POLICY_ID],
        default=SUPPORT_EVIDENCE_NONE,
    )
    parser.add_argument("--support-evidence-radii-m", default="0.75,1.0,1.5,2.0")
    parser.add_argument("--support-evidence-output", default=Path("/outputs/support_evidence_summary.json"), type=Path)
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
                    "SAM masks from the same RGB frame and detector boxes",
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
                "selected_backend_id": args.detector,
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
                candidate_selection_policy=args.candidate_selection_policy,
                selection_score_mode=args.selection_score_mode,
                pre_cap_per_scan_label_cap=max(1, args.pre_cap_per_scan_label_cap),
                pre_cap_spatial_consolidation_radius_m=max(0.0, args.pre_cap_spatial_consolidation_radius_m),
                require_scan_prompt_label=bool(args.require_scan_prompt_label),
                raw_candidate_collection_cap=max(1, args.raw_candidate_collection_cap),
                pre_cap_policy_output=args.pre_cap_policy_output,
                support_evidence_policy=args.support_evidence_policy,
                support_evidence_radii_m=parse_support_radii_m(args.support_evidence_radii_m),
                support_evidence_output=args.support_evidence_output,
                export_pre_cap_candidate_pool=bool(args.export_pre_cap_candidate_pool),
                pre_cap_candidate_pool_output=args.pre_cap_candidate_pool_output,
                export_cleanup_trace=bool(args.export_cleanup_trace),
                cleanup_trace_output=args.cleanup_trace_output,
                selected_scan_ids=[str(scan_id) for scan_id in args.scan_id],
                segmentation_backend=args.segmentation_backend,
                sam_model_id=args.sam_model_id,
                mask_depth_filter=args.mask_depth_filter,
                mask_min_depth_valid_pixels=max(1, args.mask_min_depth_valid_pixels),
                mask_point_sample_cap=max(1, args.mask_point_sample_cap),
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
                    "detector_config_id": detector_config_id(args.detector),
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
            "detector_config_id": detector_config_id(args.detector),
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
        "detector_config_id": detector_config_id(args.detector),
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
