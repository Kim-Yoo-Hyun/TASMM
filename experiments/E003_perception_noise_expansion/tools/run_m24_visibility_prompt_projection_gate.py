#!/usr/bin/env python3
"""Run E003-M24 visibility-aware denominator and prompt/projection diagnostic."""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M22_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M22_frame_scaling_projection_diagnostic_v0"
DEFAULT_M23_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M23_proposal_consolidation_calibration_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M24_visibility_prompt_projection_gate_v0"
M24_VERSION = "e003_m24_visibility_prompt_projection_gate_v0"


PRIORITY_LABELS = [
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


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


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

    return {
        "color_height": int_value("m_colorHeight", 540),
        "color_intrinsic": matrix_values("m_calibrationColorIntrinsic"),
        "color_width": int_value("m_colorWidth", 960),
        "depth_height": int_value("m_depthHeight", 172),
        "depth_shift": float_value("m_depthShift", 1000.0),
        "depth_width": int_value("m_depthWidth", 224),
    }


def load_pose_matrix(path: Path) -> list[list[float]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            values = [float(item) for item in line.split()]
            if values:
                rows.append(values)
    if len(rows) != 4 or any(len(row) != 4 for row in rows):
        raise ValueError(f"invalid pose matrix: {path}")
    return rows


def world_to_camera(pose_c2w: list[list[float]], point_world: list[float]) -> list[float]:
    rotation = [row[:3] for row in pose_c2w[:3]]
    translation = [pose_c2w[i][3] for i in range(3)]
    shifted = [float(point_world[i]) - translation[i] for i in range(3)]
    return [sum(rotation[row][col] * shifted[row] for row in range(3)) for col in range(3)]


def project_color(info: dict[str, Any], camera_point: list[float]) -> dict[str, float | bool | None]:
    intrinsic = info.get("color_intrinsic") or []
    fx = float(intrinsic[0]) if len(intrinsic) > 0 else 1.0
    cx = float(intrinsic[2]) if len(intrinsic) > 2 else float(info["color_width"]) / 2.0
    fy = float(intrinsic[5]) if len(intrinsic) > 5 else 1.0
    cy = float(intrinsic[6]) if len(intrinsic) > 6 else float(info["color_height"]) / 2.0
    x, y, z = camera_point
    if z <= 0 or fx == 0 or fy == 0:
        return {"in_front": False, "in_color_bounds": False, "target_camera_z_m": z, "u_color": None, "v_color": None}
    u = fx * x / z + cx
    v = fy * y / z + cy
    return {
        "in_front": True,
        "in_color_bounds": 0 <= u < float(info["color_width"]) and 0 <= v < float(info["color_height"]),
        "target_camera_z_m": z,
        "u_color": u,
        "v_color": v,
    }


def read_pgm_u16(path: Path) -> tuple[int, int, list[int]]:
    data = path.read_bytes()
    index = 0

    def next_token() -> str:
        nonlocal index
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index < len(data) and data[index] == ord("#"):
            while index < len(data) and data[index] not in b"\r\n":
                index += 1
            return next_token()
        start = index
        while index < len(data) and data[index] not in b" \t\r\n":
            index += 1
        return data[start:index].decode("ascii")

    magic = next_token()
    if magic != "P5":
        raise ValueError(f"unsupported PGM magic {magic}: {path}")
    width = int(next_token())
    height = int(next_token())
    max_value = int(next_token())
    while index < len(data) and data[index] in b" \t\r\n":
        index += 1
    raw = data[index:]
    if max_value <= 255:
        values = list(raw[: width * height])
    else:
        expected = width * height * 2
        values = list(struct.unpack(">" + "H" * (width * height), raw[:expected]))
    return width, height, values


def depth_sample_m(
    depth_payload: tuple[int, int, list[int]],
    info: dict[str, Any],
    u_color: float,
    v_color: float,
    radius_px: int,
) -> float | None:
    depth_width, depth_height, values = depth_payload
    u_depth = int(round(u_color * float(info["depth_width"]) / float(info["color_width"])))
    v_depth = int(round(v_color * float(info["depth_height"]) / float(info["color_height"])))
    samples = []
    for y in range(max(0, v_depth - radius_px), min(depth_height, v_depth + radius_px + 1)):
        offset = y * depth_width
        for x in range(max(0, u_depth - radius_px), min(depth_width, u_depth + radius_px + 1)):
            value = values[offset + x]
            if value > 0:
                samples.append(float(value) / float(info["depth_shift"]))
    if not samples:
        return None
    return float(median(samples))


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("label_canonical"))
        for row in prompt_payload.get("labels", [])
        if row.get("detector_prompt_enabled") and row.get("label_canonical")
    }


def select_scan_labels(row: dict[str, Any], enabled_labels: set[str], max_labels: int) -> list[str]:
    target_labels = [str(label) for label in row.get("target_labels", []) if str(label) in enabled_labels]
    ordered = [label for label in PRIORITY_LABELS if label in target_labels]
    ordered.extend(label for label in target_labels if label not in ordered)
    if not ordered:
        ordered = sorted(enabled_labels)
    return ordered[:max_labels]


def matched_target_map(path: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(path)
    return {str(row["target_uid"]): row for row in rows if row.get("matched")}


def classify_bottleneck(row: dict[str, Any]) -> str:
    if row["m22_matched"] and row["m23_selected_matched"]:
        return "retained_match_after_calibration"
    if row["m22_matched"] and not row["m23_selected_matched"]:
        return "calibration_dropped_m22_match"
    if not row["active_prompt_label"]:
        return "prompt_not_active_in_m22"
    if row["centroid_in_color_bounds_frame_count"] <= 0:
        return "not_centroid_projected_in_sampled_frames"
    if row["depth_valid_frame_count"] <= 0:
        return "projection_has_no_depth_support"
    if row["depth_consistent_frame_count"] <= 0:
        return "depth_inconsistent_or_occluded_centroid_proxy"
    return "detector_or_threshold_missed_visible_target"


def build_label_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = sorted({row["label_canonical"] for row in target_rows})
    rows = []
    for label in labels:
        group = [row for row in target_rows if row["label_canonical"] == label]
        rows.append(
            {
                "active_prompt_target_rows": sum(1 for row in group if row["active_prompt_label"]),
                "bottleneck_counts": dict(sorted(Counter(row["bottleneck_category"] for row in group).items())),
                "centroid_frustum_visible_rows": sum(1 for row in group if row["centroid_frustum_visible_proxy"]),
                "depth_consistent_visible_rows": sum(1 for row in group if row["depth_consistent_visible_proxy"]),
                "evaluation_target_rows": len(group),
                "label_canonical": label,
                "m22_matched_rows": sum(1 for row in group if row["m22_matched"]),
                "m23_selected_matched_rows": sum(1 for row in group if row["m23_selected_matched"]),
            }
        )
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M24 Visibility Prompt Projection Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Evaluated scans: {coverage['evaluated_scan_count']}",
            f"- Evaluated frames: {coverage['evaluated_frame_count']}",
            f"- Scan-level evaluation target rows: {coverage['scan_eval_target_rows']}",
            f"- Active M22 prompt target rows: {coverage['active_prompt_target_rows']}",
            f"- Prompt-not-active target rows: {coverage['prompt_not_active_target_rows']}",
            f"- Centroid frustum-visible target rows: {coverage['centroid_frustum_visible_target_rows']}",
            f"- Depth-valid projected target rows: {coverage['depth_valid_projected_target_rows']}",
            f"- Depth-consistent visible-proxy target rows: {coverage['depth_consistent_visible_proxy_target_rows']}",
            f"- M22 matched target rows: {coverage['m22_matched_target_rows']}",
            f"- M23 selected matched target rows: {coverage['m23_selected_matched_target_rows']}",
            f"- M22 matched outside centroid frustum proxy rows: {coverage['m22_matched_outside_centroid_frustum_proxy_rows']}",
            f"- Detector/threshold missed depth-consistent visible target rows: {coverage['detector_or_threshold_missed_visible_target_rows']}",
            f"- M22 recall over scan denominator: {coverage['m22_recall_over_scan_denominator']}",
            f"- M22 recall over active prompt denominator: {coverage['m22_recall_over_active_prompt_denominator']}",
            f"- M22 recall over depth-consistent visible proxy denominator: {coverage['m22_recall_over_depth_consistent_visible_proxy_denominator']}",
            f"- M23 recall over depth-consistent visible proxy denominator: {coverage['m23_recall_over_depth_consistent_visible_proxy_denominator']}",
            f"- Dominant bottleneck: {coverage['dominant_bottleneck_category']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M24 supports a diagnostic separation between active-prompt coverage, visibility-proxy denominator, depth/projection support, and detector matching.",
            "- E003-M24 does not support real RGB-D/open-vocabulary robustness because the visibility proxy uses target centroids and one scan's sampled frames.",
            "",
            "## 에이전트 추론",
            "",
            "- If many scan-level targets are not active prompts or not visible in sampled frames, scan-level recall is not an appropriate detector denominator.",
            "- M22 recall should be judged against active-prompt and visibility-aware denominators before interpreting low scan-level recall as detector failure.",
            "- M23 improves precision but drops matched targets, so the next detector step should use match-preserving calibration with a visibility-aware denominator.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M24 diagnostic.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m22-dir", default=DEFAULT_M22_DIR, type=Path)
    parser.add_argument("--m23-dir", default=DEFAULT_M23_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--max-labels", default=12, type=int)
    parser.add_argument("--depth-sample-radius-px", default=2, type=int)
    parser.add_argument("--min-depth-tolerance-m", default=0.4, type=float)
    parser.add_argument("--max-depth-tolerance-m", default=1.5, type=float)
    args = parser.parse_args()

    targets = [
        row
        for row in load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
        if row.get("evaluation_target_enabled")
    ]
    manifest_rows = load_jsonl(args.m17_dir / "real_proposal_query_manifest.jsonl")
    prompt_payload = load_json(args.m17_dir / "prompt_set.json")
    frame_rows = load_jsonl(args.m22_dir / "frame_diagnostics.jsonl")
    m22_matches = matched_target_map(args.m22_dir / "matching" / "target_recall_rows.jsonl")
    m23_matches = matched_target_map(args.m23_dir / "selected_target_recall_rows.jsonl")

    evaluated_scans = sorted({str(row["scan_id"]) for row in frame_rows})
    frames_by_scan: dict[str, list[str]] = defaultdict(list)
    for row in frame_rows:
        frames_by_scan[str(row["scan_id"])].append(str(row["frame_id"]))

    enabled_labels = detector_prompt_labels(prompt_payload)
    manifest_by_scan = {str(row["scan_id"]): row for row in manifest_rows}
    active_labels_by_scan = {
        scan_id: select_scan_labels(manifest_by_scan[scan_id], enabled_labels, args.max_labels)
        for scan_id in evaluated_scans
        if scan_id in manifest_by_scan
    }

    info_cache: dict[str, dict[str, Any]] = {}
    pose_cache: dict[tuple[str, str], list[list[float]]] = {}
    depth_cache: dict[tuple[str, str], tuple[int, int, list[int]]] = {}
    frame_visibility_rows: list[dict[str, Any]] = []
    target_denominator_rows: list[dict[str, Any]] = []

    for target in [row for row in targets if str(row["scan_id"]) in evaluated_scans]:
        scan_id = str(target["scan_id"])
        scan_dir = Path(str(manifest_by_scan[scan_id]["scan_dir"]))
        sequence_dir = scan_dir / "sequence"
        if scan_id not in info_cache:
            info_cache[scan_id] = parse_info_txt(sequence_dir / "_info.txt")
        info = info_cache[scan_id]
        active_label = str(target["label_canonical"]) in set(active_labels_by_scan.get(scan_id, []))
        axes = [float(value) for value in target.get("obb_axes_lengths_m", []) if value is not None]
        object_radius = max(axes) / 2.0 if axes else 0.0
        depth_tolerance = max(args.min_depth_tolerance_m, min(args.max_depth_tolerance_m, object_radius))

        frame_rows_for_target = []
        for frame_id in frames_by_scan[scan_id]:
            pose_key = (scan_id, frame_id)
            if pose_key not in pose_cache:
                pose_cache[pose_key] = load_pose_matrix(sequence_dir / f"{frame_id}.pose.txt")
            camera_point = world_to_camera(pose_cache[pose_key], target["centroid_world_m"])
            projected = project_color(info, camera_point)
            depth_m = None
            depth_delta = None
            depth_consistent = False
            status = "behind_camera"
            if projected["in_front"] and not projected["in_color_bounds"]:
                status = "out_of_color_frame"
            elif projected["in_front"] and projected["in_color_bounds"]:
                depth_key = (scan_id, frame_id)
                if depth_key not in depth_cache:
                    depth_cache[depth_key] = read_pgm_u16(sequence_dir / f"{frame_id}.depth.pgm")
                depth_m = depth_sample_m(
                    depth_payload=depth_cache[depth_key],
                    info=info,
                    u_color=float(projected["u_color"]),
                    v_color=float(projected["v_color"]),
                    radius_px=args.depth_sample_radius_px,
                )
                if depth_m is None:
                    status = "no_depth_at_projected_centroid"
                else:
                    depth_delta = depth_m - float(projected["target_camera_z_m"])
                    depth_consistent = abs(depth_delta) <= depth_tolerance
                    if depth_consistent:
                        status = "depth_consistent_centroid_proxy"
                    elif depth_delta < -depth_tolerance:
                        status = "depth_closer_than_centroid"
                    else:
                        status = "depth_farther_than_centroid"

            frame_row = {
                "active_prompt_label": active_label,
                "depth_consistent_centroid_proxy": depth_consistent,
                "depth_delta_m": round(depth_delta, 6) if depth_delta is not None else None,
                "depth_median_m": round(depth_m, 6) if depth_m is not None else None,
                "depth_tolerance_m": round(depth_tolerance, 6),
                "frame_id": frame_id,
                "in_color_bounds": bool(projected["in_color_bounds"]),
                "in_front": bool(projected["in_front"]),
                "label_canonical": target["label_canonical"],
                "object_instance_id": target["object_instance_id"],
                "projection_status": status,
                "scan_id": scan_id,
                "target_camera_z_m": round(float(projected["target_camera_z_m"]), 6),
                "target_uid": target["target_uid"],
                "u_color": round(float(projected["u_color"]), 3) if projected["u_color"] is not None else None,
                "v_color": round(float(projected["v_color"]), 3) if projected["v_color"] is not None else None,
            }
            frame_rows_for_target.append(frame_row)
            frame_visibility_rows.append(frame_row)

        in_bounds_count = sum(1 for row in frame_rows_for_target if row["in_color_bounds"])
        depth_valid_count = sum(1 for row in frame_rows_for_target if row["depth_median_m"] is not None)
        depth_consistent_count = sum(1 for row in frame_rows_for_target if row["depth_consistent_centroid_proxy"])
        m22_match = m22_matches.get(str(target["target_uid"]))
        m23_match = m23_matches.get(str(target["target_uid"]))
        denom_row = {
            "active_prompt_label": active_label,
            "active_prompt_labels_for_scan": active_labels_by_scan.get(scan_id, []),
            "bottleneck_category": None,
            "centroid_frustum_visible_proxy": active_label and in_bounds_count > 0,
            "centroid_in_color_bounds_frame_count": in_bounds_count,
            "depth_consistent_frame_count": depth_consistent_count,
            "depth_consistent_visible_proxy": active_label and depth_consistent_count > 0,
            "depth_valid_frame_count": depth_valid_count,
            "evaluation_target_enabled": True,
            "frame_count": len(frame_rows_for_target),
            "in_front_frame_count": sum(1 for row in frame_rows_for_target if row["in_front"]),
            "label_canonical": target["label_canonical"],
            "m22_best_match_distance_m": m22_match.get("best_match_distance_m") if m22_match else None,
            "m22_matched": bool(m22_match),
            "m23_selected_best_match_distance_m": m23_match.get("best_match_distance_m") if m23_match else None,
            "m23_selected_matched": bool(m23_match),
            "object_instance_id": target["object_instance_id"],
            "prompt_set_enabled": str(target["label_canonical"]) in enabled_labels,
            "scan_id": scan_id,
            "target_uid": target["target_uid"],
        }
        denom_row["bottleneck_category"] = classify_bottleneck(denom_row)
        target_denominator_rows.append(denom_row)

    bottleneck_counts = Counter(row["bottleneck_category"] for row in target_denominator_rows)
    active_rows = [row for row in target_denominator_rows if row["active_prompt_label"]]
    frustum_rows = [row for row in target_denominator_rows if row["centroid_frustum_visible_proxy"]]
    depth_valid_rows = [row for row in target_denominator_rows if row["active_prompt_label"] and row["depth_valid_frame_count"] > 0]
    depth_consistent_rows = [row for row in target_denominator_rows if row["depth_consistent_visible_proxy"]]
    m22_matched = [row for row in target_denominator_rows if row["m22_matched"]]
    m23_matched = [row for row in target_denominator_rows if row["m23_selected_matched"]]
    m22_active_matched = [row for row in active_rows if row["m22_matched"]]
    m22_frustum_matched = [row for row in frustum_rows if row["m22_matched"]]
    m22_depth_consistent_matched = [row for row in depth_consistent_rows if row["m22_matched"]]
    m23_active_matched = [row for row in active_rows if row["m23_selected_matched"]]
    m23_frustum_matched = [row for row in frustum_rows if row["m23_selected_matched"]]
    m23_depth_consistent_matched = [row for row in depth_consistent_rows if row["m23_selected_matched"]]
    dominant_bottleneck = bottleneck_counts.most_common(1)[0][0] if bottleneck_counts else None

    gate_decision = {
        "m24_version": M24_VERSION,
        "next_recommended_unit": "E003-M25 prompt-expanded / visibility-aware detector rerun gate",
        "paper_table_promotion_ready": False,
        "primary_decision": "do_not_scale_to_paper_table_before_visibility_and_prompt_calibration",
        "reason": (
            "scan-level recall mixes inactive prompts and non-visible target centroids; "
            "threshold/NMS calibration also drops matched targets under M23"
        ),
        "required_before_real_claim": [
            "visibility-aware denominator over evaluated frames",
            "active prompt budget or prompt expansion policy",
            "projection/depth consistency sanity check",
            "multi-scan detector rerun after denominator and prompt policy are fixed",
        ],
    }

    coverage = {
        "active_prompt_target_rows": len(active_rows),
        "bottleneck_counts": dict(sorted(bottleneck_counts.items())),
        "centroid_frustum_visible_target_rows": len(frustum_rows),
        "depth_consistent_visible_proxy_target_rows": len(depth_consistent_rows),
        "depth_sample_radius_px": args.depth_sample_radius_px,
        "depth_valid_projected_target_rows": len(depth_valid_rows),
        "dominant_bottleneck_category": dominant_bottleneck,
        "detector_or_threshold_missed_visible_target_rows": bottleneck_counts.get(
            "detector_or_threshold_missed_visible_target", 0
        ),
        "evaluated_frame_count": len(frame_rows),
        "evaluated_scan_count": len(evaluated_scans),
        "evaluated_scans": evaluated_scans,
        "m22_matched_target_rows": len(m22_matched),
        "m22_matched_active_prompt_target_rows": len(m22_active_matched),
        "m22_matched_centroid_frustum_visible_target_rows": len(m22_frustum_matched),
        "m22_matched_depth_consistent_visible_proxy_target_rows": len(m22_depth_consistent_matched),
        "m22_matched_outside_centroid_frustum_proxy_rows": sum(
            1 for row in m22_matched if not row["centroid_frustum_visible_proxy"]
        ),
        "m22_matched_outside_depth_consistent_visible_proxy_rows": sum(
            1 for row in m22_matched if not row["depth_consistent_visible_proxy"]
        ),
        "m22_recall_over_active_prompt_denominator": safe_rate(len(m22_active_matched), len(active_rows)),
        "m22_recall_over_active_prompt_intersection_denominator": safe_rate(len(m22_active_matched), len(active_rows)),
        "m22_recall_over_centroid_frustum_visible_proxy_denominator": safe_rate(
            len(m22_frustum_matched), len(frustum_rows)
        ),
        "m22_recall_over_depth_consistent_visible_proxy_denominator": safe_rate(
            len(m22_depth_consistent_matched), len(depth_consistent_rows)
        ),
        "m22_recall_over_depth_consistent_visible_proxy_intersection_denominator": safe_rate(
            len(m22_depth_consistent_matched), len(depth_consistent_rows)
        ),
        "m22_recall_over_scan_denominator": safe_rate(len(m22_matched), len(target_denominator_rows)),
        "m23_recall_over_active_prompt_denominator": safe_rate(len(m23_active_matched), len(active_rows)),
        "m23_recall_over_active_prompt_intersection_denominator": safe_rate(len(m23_active_matched), len(active_rows)),
        "m23_recall_over_centroid_frustum_visible_proxy_denominator": safe_rate(
            len(m23_frustum_matched), len(frustum_rows)
        ),
        "m23_recall_over_depth_consistent_visible_proxy_denominator": safe_rate(
            len(m23_depth_consistent_matched), len(depth_consistent_rows)
        ),
        "m23_recall_over_depth_consistent_visible_proxy_intersection_denominator": safe_rate(
            len(m23_depth_consistent_matched), len(depth_consistent_rows)
        ),
        "m23_recall_over_scan_denominator": safe_rate(len(m23_matched), len(target_denominator_rows)),
        "m23_selected_matched_target_rows": len(m23_matched),
        "m23_selected_matched_active_prompt_target_rows": len(m23_active_matched),
        "m23_selected_matched_centroid_frustum_visible_target_rows": len(m23_frustum_matched),
        "m23_selected_matched_depth_consistent_visible_proxy_target_rows": len(m23_depth_consistent_matched),
        "m23_selected_matched_outside_centroid_frustum_proxy_rows": sum(
            1 for row in m23_matched if not row["centroid_frustum_visible_proxy"]
        ),
        "m23_selected_matched_outside_depth_consistent_visible_proxy_rows": sum(
            1 for row in m23_matched if not row["depth_consistent_visible_proxy"]
        ),
        "m24_version": M24_VERSION,
        "max_depth_tolerance_m": args.max_depth_tolerance_m,
        "max_labels": args.max_labels,
        "min_depth_tolerance_m": args.min_depth_tolerance_m,
        "paper_table_command_ready": False,
        "prompt_not_active_target_rows": len(target_denominator_rows) - len(active_rows),
        "real_rgbd_or_open_vocab_claim_ready": False,
        "scan_eval_target_rows": len(target_denominator_rows),
        "status": "visibility_prompt_projection_gate_ready",
        "visibility_proxy_is_true_visibility": False,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "target_visibility_frame_rows.jsonl", frame_visibility_rows)
    write_jsonl(args.out_dir / "target_denominator_rows.jsonl", target_denominator_rows)
    write_jsonl(args.out_dir / "label_bottleneck_rows.jsonl", build_label_rows(target_denominator_rows))
    write_json(args.out_dir / "gate_decision.json", gate_decision)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
