#!/usr/bin/env python3
"""Run H001 row-filtered high-displacement query smoke.

This is a hypothesis-stage smoke test. It uses a staged high-displacement
reference-rescan semantic pair and evaluates only row-level geometry-valid
rigid moved objects. It does not evaluate removed-object suppression and does
not run navigation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_RIGID_GEOMETRY = H001_ROOT / "artifacts" / "high_displacement_pair_geometry" / "rigid_geometry.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "high_displacement_query_smoke"
REFERENCE_SCAN_ID = "569d8f0d-72aa-2f24-8ac6-c6ee8d927c4b"
RESCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"
POLICIES = [
    "scene_aligned_static_map",
    "staleness_only",
    "label_nearest_current_observation",
    "label_top3_current_observation",
    "label_all_current_observation",
    "oracle_current_pose",
]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def find_pair_metadata(scan3r_json: list[dict], reference_scan_id: str, rescan_id: str) -> dict:
    for group in scan3r_json:
        if group.get("reference") != reference_scan_id:
            continue
        for scan in group.get("scans", []):
            if scan.get("reference") == rescan_id:
                return scan
    raise RuntimeError(f"target pair metadata not found: {reference_scan_id} -> {rescan_id}")


def transform_point_row(point: list[float], matrix: list[float]) -> list[float]:
    x, y, z = point
    return [
        x * matrix[0] + y * matrix[4] + z * matrix[8] + matrix[12],
        x * matrix[1] + y * matrix[5] + z * matrix[9] + matrix[13],
        x * matrix[2] + y * matrix[6] + z * matrix[10] + matrix[14],
    ]


def invert_rigid_row_transform(matrix: list[float]) -> list[float]:
    rotation_t = [
        matrix[0],
        matrix[4],
        matrix[8],
        0.0,
        matrix[1],
        matrix[5],
        matrix[9],
        0.0,
        matrix[2],
        matrix[6],
        matrix[10],
        0.0,
    ]
    tx, ty, tz = matrix[12], matrix[13], matrix[14]
    inv_translation = [
        -(tx * rotation_t[0] + ty * rotation_t[4] + tz * rotation_t[8]),
        -(tx * rotation_t[1] + ty * rotation_t[5] + tz * rotation_t[9]),
        -(tx * rotation_t[2] + ty * rotation_t[6] + tz * rotation_t[10]),
    ]
    return rotation_t + inv_translation + [1.0]


def load_semseg_objects(path: Path) -> list[dict]:
    data = load_json(path)
    objects = []
    for group in data.get("segGroups", []):
        centroid = group.get("obb", {}).get("centroid")
        if centroid is None:
            continue
        objects.append(
            {
                "instance_id": str(group.get("objectId", group.get("id"))),
                "label": group.get("label", ""),
                "centroid": [float(value) for value in centroid],
            }
        )
    return objects


def planar_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def point_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(a, b)))


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def build_query_rows(
    dataset_root: Path,
    rigid_rows: list[dict],
    stale_threshold_m: float,
) -> list[dict]:
    pair_metadata = find_pair_metadata(
        load_json(dataset_root / "3RScan" / "files" / "3RScan.json"),
        REFERENCE_SCAN_ID,
        RESCAN_ID,
    )
    scene_inverse = invert_rigid_row_transform(pair_metadata["transform"])
    query_rows = []
    for row in rigid_rows:
        if not row.get("row_geometry_valid"):
            continue
        old_scene_aligned = transform_point_row(row["reference_centroid"], scene_inverse)
        current = row["rescan_centroid"]
        displacement_planar = planar_distance(old_scene_aligned, current)
        query_rows.append(
            {
                "episode_id": "h001_high_disp_569d8f0d_569d8f0f",
                "reference_scan_id": REFERENCE_SCAN_ID,
                "rescan_id": RESCAN_ID,
                "object_instance_id_ref": row["instance_reference"],
                "object_instance_id_rescan": row["instance_rescan"],
                "object_label": row["ref_label"],
                "query": f"find the {row['ref_label']}",
                "change_type": "rigid_moved",
                "row_geometry_valid": True,
                "row_geometry_error_m": row["best_error_m"],
                "row_best_candidate": row["best_candidate"],
                "old_scene_aligned_centroid": old_scene_aligned,
                "pair_current_centroid": current,
                "scene_aligned_static_error_m": row["scene_inverse_error_m"],
                "scene_aligned_static_planar_error_m": displacement_planar,
                "significant_moved": displacement_planar >= stale_threshold_m,
                "expected_memory_state": "needs_reobservation"
                if displacement_planar >= stale_threshold_m
                else "trusted_or_low_motion",
                "evaluation_scope": "moved_recovery_only",
                "old_memory_is_stale": displacement_planar >= stale_threshold_m,
            }
        )
    return query_rows


def ranked_same_label_candidates(row: dict, rescan_objects: list[dict]) -> list[dict]:
    candidates = [
        item
        for item in rescan_objects
        if item["label"] == row["object_label"]
    ]
    ranked = sorted(
        candidates,
        key=lambda item: (
            planar_distance(item["centroid"], row["old_scene_aligned_centroid"]),
            item["instance_id"],
        ),
    )
    output = []
    for rank, item in enumerate(ranked, start=1):
        output.append(
            {
                "rank": rank,
                "instance_id": item["instance_id"],
                "label": item["label"],
                "centroid": item["centroid"],
                "distance_to_old_scene_aligned_m": round_or_none(
                    planar_distance(item["centroid"], row["old_scene_aligned_centroid"])
                ),
                "distance_to_target_current_m": round_or_none(
                    point_distance(item["centroid"], row["pair_current_centroid"])
                ),
                "is_target_instance": item["instance_id"] == row["object_instance_id_rescan"],
            }
        )
    return output


def predict(policy: str, row: dict, candidates: list[dict], success_threshold_m: float) -> dict:
    target_rank = next(
        (item["rank"] for item in candidates if item["is_target_instance"]),
        None,
    )
    if policy == "scene_aligned_static_map":
        error = point_distance(row["old_scene_aligned_centroid"], row["pair_current_centroid"])
        return {
            "policy": policy,
            "memory_state": "trusted",
            "action": "return_scene_aligned_old_location",
            "returns_old_location": True,
            "suppresses_old_location": False,
            "uses_rescan_semseg_observation": False,
            "uses_exact_current_pose": False,
            "candidate_count": 1,
            "target_rank": None,
            "exact_recovery": error <= success_threshold_m,
            "candidate_recall_at_1": error <= success_threshold_m,
            "candidate_recall_at_3": error <= success_threshold_m,
            "candidate_recall_all": error <= success_threshold_m,
            "target_error_m": round_or_none(error),
            "reason": "Scene-aligned static map returns the old object memory in the current scene frame.",
        }

    if policy == "staleness_only":
        return {
            "policy": policy,
            "memory_state": "needs_reobservation",
            "action": "suppress_old_location",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": False,
            "uses_exact_current_pose": False,
            "candidate_count": 0,
            "target_rank": None,
            "exact_recovery": False,
            "candidate_recall_at_1": False,
            "candidate_recall_at_3": False,
            "candidate_recall_all": False,
            "target_error_m": None,
            "reason": "Suppress stale old location but do not use a current observation source.",
        }

    if policy == "label_nearest_current_observation":
        chosen = candidates[0] if candidates else None
        error = point_distance(chosen["centroid"], row["pair_current_centroid"]) if chosen else None
        exact = bool(chosen and chosen["is_target_instance"] and error <= success_threshold_m)
        return {
            "policy": policy,
            "memory_state": "updated_from_current_observation",
            "action": "return_nearest_same_label_current_observation",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": 1 if chosen else 0,
            "target_rank": target_rank,
            "exact_recovery": exact,
            "candidate_recall_at_1": target_rank == 1,
            "candidate_recall_at_3": target_rank is not None and target_rank <= 3,
            "candidate_recall_all": target_rank is not None,
            "target_error_m": round_or_none(error),
            "chosen_instance_id": chosen["instance_id"] if chosen else None,
            "reason": "Use current semseg observations, but choose only the same-label observation nearest to the stale old location.",
        }

    if policy == "label_top3_current_observation":
        top_k = candidates[:3]
        return {
            "policy": policy,
            "memory_state": "candidate_set_from_current_observation",
            "action": "return_top3_same_label_current_observations",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": len(top_k),
            "target_rank": target_rank,
            "exact_recovery": False,
            "candidate_recall_at_1": target_rank == 1,
            "candidate_recall_at_3": target_rank is not None and target_rank <= 3,
            "candidate_recall_all": target_rank is not None,
            "target_error_m": None,
            "candidate_instance_ids": [item["instance_id"] for item in top_k],
            "reason": "Use current semseg observations and return a bounded same-label candidate set.",
        }

    if policy == "label_all_current_observation":
        return {
            "policy": policy,
            "memory_state": "candidate_set_from_current_observation",
            "action": "return_all_same_label_current_observations",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": False,
            "candidate_count": len(candidates),
            "target_rank": target_rank,
            "exact_recovery": False,
            "candidate_recall_at_1": target_rank == 1,
            "candidate_recall_at_3": target_rank is not None and target_rank <= 3,
            "candidate_recall_all": target_rank is not None,
            "target_error_m": None,
            "candidate_instance_ids": [item["instance_id"] for item in candidates],
            "reason": "Use current semseg observations and return all same-label candidates; this measures recall but exposes search burden.",
        }

    if policy == "oracle_current_pose":
        return {
            "policy": policy,
            "memory_state": "trusted_current",
            "action": "return_pair_validated_current_target",
            "returns_old_location": False,
            "suppresses_old_location": True,
            "uses_rescan_semseg_observation": True,
            "uses_exact_current_pose": True,
            "candidate_count": 1,
            "target_rank": target_rank,
            "exact_recovery": True,
            "candidate_recall_at_1": True,
            "candidate_recall_at_3": True,
            "candidate_recall_all": True,
            "target_error_m": 0.0,
            "chosen_instance_id": row["object_instance_id_rescan"],
            "reason": "Upper bound using the pair-validated target instance.",
        }

    raise RuntimeError(f"unknown policy: {policy}")


def summarize_policy(policy: str, predictions: list[dict], subset_name: str, subset_rows: list[dict]) -> dict:
    ids = {row["object_instance_id_ref"] for row in subset_rows}
    items = [row for row in predictions if row["object_instance_id_ref"] in ids and row["policy"] == policy]
    den = len(items)
    stale_items = [row for row in items if row["old_memory_is_stale"]]
    stale_den = len(stale_items)
    return {
        "policy": policy,
        "subset": subset_name,
        "rows": den,
        "stale_rows": stale_den,
        "suppresses_old_location_rate": safe_rate(
            sum(1 for row in items if row["suppresses_old_location"]), den
        ),
        "stale_old_location_false_positive_rate": safe_rate(
            sum(1 for row in stale_items if row["returns_old_location"] and not row["exact_recovery"]),
            stale_den,
        ),
        "exact_recovery_rate": safe_rate(sum(1 for row in items if row["exact_recovery"]), den),
        "candidate_recall_at_1": safe_rate(sum(1 for row in items if row["candidate_recall_at_1"]), den),
        "candidate_recall_at_3": safe_rate(sum(1 for row in items if row["candidate_recall_at_3"]), den),
        "candidate_recall_all": safe_rate(sum(1 for row in items if row["candidate_recall_all"]), den),
        "mean_candidate_count": round_or_none(
            sum(row["candidate_count"] for row in items) / den if den else None
        ),
        "uses_rescan_semseg_observation": any(row["uses_rescan_semseg_observation"] for row in items),
        "uses_exact_current_pose": any(row["uses_exact_current_pose"] for row in items),
    }


def write_report(out_dir: Path, coverage: dict, metrics: dict) -> None:
    lines = [
        "# High-Displacement Query Smoke Report",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Reference scan: `{coverage['reference_scan_id']}`",
        f"- Rescan: `{coverage['rescan_id']}`",
        f"- Input rigid rows: {coverage['input_rigid_rows']}",
        f"- Row-valid rigid rows: {coverage['row_valid_rigid_rows']}",
        f"- Significant moved rows: {coverage['significant_moved_rows']}",
        f"- Low-motion row-valid controls: {coverage['low_motion_row_valid_rows']}",
        f"- Removed-object suppression evaluated: {coverage['evaluates_removed_suppression']}",
        f"- Uses navigation: {coverage['uses_navigation']}",
        "",
        "## Significant Moved Metrics",
        "",
        "| Policy | Exact recovery | Recall@1 | Recall@3 | Recall all | Stale FP | Mean candidates | Exact pose |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for policy in POLICIES:
        item = metrics["significant_moved"][policy]
        lines.append(
            "| {policy} | {exact} | {r1} | {r3} | {rall} | {fp} | {cands} | {exact_pose} |".format(
                policy=policy,
                exact=item["exact_recovery_rate"],
                r1=item["candidate_recall_at_1"],
                r3=item["candidate_recall_at_3"],
                rall=item["candidate_recall_all"],
                fp=item["stale_old_location_false_positive_rate"],
                cands=item["mean_candidate_count"],
                exact_pose=item["uses_exact_current_pose"],
            )
        )
    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No navigation claim is supported.",
            "- No removed-object suppression claim is supported by this smoke.",
            "- `oracle_current_pose` is an upper bound, not a deployable method.",
            "- `label_*_current_observation` policies use `semseg.v2.json` as an annotation-level current-observation proxy.",
            "",
            "## Agent Inference",
            "",
            "- H001 can suppress stale old-location returns on high-displacement moved rows.",
            "- Label-only current observation is not enough for exact moved-object recovery in a chair-heavy scene.",
            "- The next method gate needs instance re-identification or visual/geometric evidence beyond same-label current observations.",
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--rigid-geometry", type=Path, default=DEFAULT_RIGID_GEOMETRY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stale-threshold-m", type=float, default=1.0)
    parser.add_argument("--success-threshold-m", type=float, default=0.5)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rigid_rows = load_jsonl(args.rigid_geometry)
    query_rows = build_query_rows(args.dataset_root, rigid_rows, args.stale_threshold_m)
    rescan_objects = load_semseg_objects(
        args.dataset_root / "3RScan" / "scans" / RESCAN_ID / "semseg.v2.json"
    )

    predictions = []
    candidate_rows = []
    for row in query_rows:
        candidates = ranked_same_label_candidates(row, rescan_objects)
        candidate_rows.append(
            {
                "object_instance_id_ref": row["object_instance_id_ref"],
                "object_instance_id_rescan": row["object_instance_id_rescan"],
                "object_label": row["object_label"],
                "significant_moved": row["significant_moved"],
                "candidate_count": len(candidates),
                "target_rank": next(
                    (item["rank"] for item in candidates if item["is_target_instance"]),
                    None,
                ),
                "candidates": candidates,
            }
        )
        for policy in POLICIES:
            pred = predict(policy, row, candidates, args.success_threshold_m)
            predictions.append({**row, **pred})

    significant_rows = [row for row in query_rows if row["significant_moved"]]
    low_motion_rows = [row for row in query_rows if not row["significant_moved"]]
    metrics = {
        "all_row_valid": {
            policy: summarize_policy(policy, predictions, "all_row_valid", query_rows)
            for policy in POLICIES
        },
        "significant_moved": {
            policy: summarize_policy(policy, predictions, "significant_moved", significant_rows)
            for policy in POLICIES
        },
        "low_motion": {
            policy: summarize_policy(policy, predictions, "low_motion", low_motion_rows)
            for policy in POLICIES
        },
    }
    coverage = {
        "dataset_root": str(args.dataset_root),
        "reference_scan_id": REFERENCE_SCAN_ID,
        "rescan_id": RESCAN_ID,
        "input_rigid_rows": len(rigid_rows),
        "row_valid_rigid_rows": len(query_rows),
        "significant_moved_rows": len(significant_rows),
        "low_motion_row_valid_rows": len(low_motion_rows),
        "stale_threshold_m": args.stale_threshold_m,
        "success_threshold_m": args.success_threshold_m,
        "evaluates_removed_suppression": False,
        "uses_navigation": False,
        "status": "complete" if significant_rows else "needs_more_rows",
    }

    with (args.out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    with (args.out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_jsonl(args.out_dir / "query_rows.jsonl", query_rows)
    write_jsonl(args.out_dir / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(args.out_dir / "predictions.jsonl", predictions)
    write_report(args.out_dir, coverage, metrics)

    print(json.dumps({"coverage": coverage, "metrics": metrics}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
