#!/usr/bin/env python3
"""Run H001 non-oracle search-region prior smoke.

This is a hypothesis-stage diagnostic. It evaluates whether stale semantic
memory can propose bounded re-observation regions that contain the
pair-validated moved-object location. It does not predict exact object poses
and does not run navigation.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_QUERY_ROWS = H001_ROOT / "artifacts" / "real_pair_query_smoke" / "query_rows.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "search_region_prior_smoke"
REFERENCE_SCAN_ID = "ddc73797-765b-241a-9e2c-097c5989baf6"

CONTEXT_RELATIONS = {"standing on", "lying on", "attached to", "hanging on"}
STRUCTURAL_CONTEXT_LABELS = {"floor", "wall", "ceiling"}
POLICY_SPECS = [
    {"policy": "old_location_r1", "mode": "old_only", "radius_m": 1.0},
    {"policy": "old_location_r2", "mode": "old_only", "radius_m": 2.0},
    {"policy": "old_location_r3", "mode": "old_only", "radius_m": 3.0},
    {"policy": "old_location_r4", "mode": "old_only", "radius_m": 4.0},
    {"policy": "semantic_context_r2", "mode": "old_plus_informative_context", "radius_m": 2.0},
    {"policy": "semantic_context_r3", "mode": "old_plus_informative_context", "radius_m": 3.0},
    {"policy": "semantic_context_r4", "mode": "old_plus_informative_context", "radius_m": 4.0},
    {"policy": "oracle_current_region", "mode": "oracle_current", "radius_m": 0.35},
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


def find_scan(scans: list[dict], scan_id: str) -> dict:
    for scan in scans:
        if scan.get("scan") == scan_id:
            return scan
    raise RuntimeError(f"scan not found: {scan_id}")


def load_semseg_centroids(path: Path) -> dict[str, dict]:
    data = load_json(path)
    centroids = {}
    for group in data.get("segGroups", []):
        object_id = str(group.get("objectId", group.get("id")))
        obb = group.get("obb", {})
        centroid = obb.get("centroid")
        if centroid is None:
            continue
        centroids[object_id] = {
            "label": group.get("label", ""),
            "centroid": [float(value) for value in centroid],
        }
    return centroids


def load_relation_context(dataset_root: Path) -> dict[str, list[dict]]:
    objects_path = dataset_root / "3DSSG" / "objects.json"
    relationships_path = dataset_root / "3DSSG" / "relationships.json"
    object_scan = find_scan(load_json(objects_path)["scans"], REFERENCE_SCAN_ID)
    relationship_scan = find_scan(load_json(relationships_path)["scans"], REFERENCE_SCAN_ID)
    labels = {str(obj["id"]): obj.get("label", "") for obj in object_scan.get("objects", [])}

    context: dict[str, list[dict]] = {}
    for subj, obj, _, name in relationship_scan.get("relationships", []):
        subj_id = str(subj)
        obj_id = str(obj)
        if name not in CONTEXT_RELATIONS:
            continue
        context.setdefault(subj_id, []).append(
            {
                "role": "subject",
                "relation": name,
                "other_instance_id": obj_id,
                "other_label": labels.get(obj_id, ""),
            }
        )
        context.setdefault(obj_id, []).append(
            {
                "role": "object",
                "relation": name,
                "other_instance_id": subj_id,
                "other_label": labels.get(subj_id, ""),
            }
        )
    return context


def planar_distance(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def dedupe_regions(regions: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for region in regions:
        key = (region["center_source"], region["center_instance_id"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(region)
    return deduped


def build_regions(
    spec: dict,
    row: dict,
    relation_context: dict[str, list[dict]],
    reference_centroids: dict[str, dict],
) -> list[dict]:
    radius = spec["radius_m"]
    object_id = str(row["object_instance_id_ref"])
    if spec["mode"] == "oracle_current":
        return [
            {
                "center_source": "oracle_current",
                "center_instance_id": row.get("object_instance_id_rescan") or object_id,
                "center_label": row.get("object_label", ""),
                "center": row["pair_current_centroid"],
                "radius_m": radius,
                "is_oracle": True,
            }
        ]

    regions = [
        {
            "center_source": "old_object",
            "center_instance_id": object_id,
            "center_label": row.get("object_label", ""),
            "center": row["old_centroid_ref"],
            "radius_m": radius,
            "is_oracle": False,
        }
    ]
    if spec["mode"] == "old_only":
        return regions

    for context_item in relation_context.get(object_id, []):
        label = context_item.get("other_label", "")
        if label in STRUCTURAL_CONTEXT_LABELS:
            continue
        other_id = str(context_item.get("other_instance_id"))
        other = reference_centroids.get(other_id)
        if other is None:
            continue
        regions.append(
            {
                "center_source": "informative_relation_context",
                "center_instance_id": other_id,
                "center_label": label,
                "relation": context_item.get("relation"),
                "center": other["centroid"],
                "radius_m": radius,
                "is_oracle": False,
            }
        )
    return dedupe_regions(regions)


def evaluate_policy(
    spec: dict,
    rows: list[dict],
    relation_context: dict[str, list[dict]],
    reference_centroids: dict[str, dict],
) -> tuple[list[dict], dict]:
    predictions = []
    rigid_rows = [row for row in rows if row["change_type"] == "rigid_moved"]
    removed_rows = [row for row in rows if row["change_type"] == "removed"]
    control_rows = [row for row in rows if row["change_type"] == "unchanged_control"]

    for row in rows:
        if row["change_type"] == "rigid_moved":
            regions = build_regions(spec, row, relation_context, reference_centroids)
            current = row["pair_current_centroid"]
            distances = [planar_distance(region["center"], current) for region in regions if region.get("center")]
            hit = any(distance <= spec["radius_m"] for distance in distances)
            informative_region_count = sum(
                1 for region in regions if region["center_source"] == "informative_relation_context"
            )
            area_proxy = len(regions) * math.pi * spec["radius_m"] ** 2
            predictions.append(
                {
                    "policy": spec["policy"],
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "object_label": row["object_label"],
                    "change_type": row["change_type"],
                    "target_type": "search_region_target",
                    "search_region_hit": hit,
                    "search_region_count": len(regions),
                    "informative_region_count": informative_region_count,
                    "search_region_radius_m": spec["radius_m"],
                    "search_area_proxy_m2": round(area_proxy, 6),
                    "min_planar_distance_to_current_m": round_or_none(min(distances) if distances else None),
                    "old_to_current_planar_distance_m": round_or_none(
                        planar_distance(row["old_centroid_ref"], current)
                    ),
                    "uses_oracle_center": spec["mode"] == "oracle_current",
                    "regions": regions,
                }
            )
        elif row["change_type"] == "removed":
            predictions.append(
                {
                    "policy": spec["policy"],
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "object_label": row["object_label"],
                    "change_type": row["change_type"],
                    "target_type": "absent_target",
                    "search_region_hit": False,
                    "search_region_count": 0,
                    "informative_region_count": 0,
                    "search_region_radius_m": spec["radius_m"],
                    "search_area_proxy_m2": 0.0,
                    "min_planar_distance_to_current_m": None,
                    "old_to_current_planar_distance_m": None,
                    "uses_oracle_center": spec["mode"] == "oracle_current",
                    "regions": [],
                }
            )
        elif row["change_type"] == "unchanged_control":
            predictions.append(
                {
                    "policy": spec["policy"],
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "object_label": row["object_label"],
                    "change_type": row["change_type"],
                    "target_type": "old_location_target",
                    "search_region_hit": False,
                    "search_region_count": 0,
                    "informative_region_count": 0,
                    "search_region_radius_m": spec["radius_m"],
                    "search_area_proxy_m2": 0.0,
                    "min_planar_distance_to_current_m": None,
                    "old_to_current_planar_distance_m": None,
                    "uses_oracle_center": spec["mode"] == "oracle_current",
                    "regions": [],
                }
            )

    rigid_predictions = [row for row in predictions if row["change_type"] == "rigid_moved"]
    hits = sum(1 for row in rigid_predictions if row["search_region_hit"])
    total_regions = sum(row["search_region_count"] for row in rigid_predictions)
    total_area = sum(row["search_area_proxy_m2"] for row in rigid_predictions)
    informative_targets = sum(1 for row in rigid_predictions if row["informative_region_count"] > 0)
    target_counts = Counter(row["target_type"] for row in predictions)

    mean_region_count = total_regions / len(rigid_predictions) if rigid_predictions else None
    mean_area = total_area / len(rigid_predictions) if rigid_predictions else None
    hit_rate = safe_rate(hits, len(rigid_predictions))
    metrics = {
        "policy": spec["policy"],
        "mode": spec["mode"],
        "search_region_radius_m": spec["radius_m"],
        "rigid_moved_object_queries": len(rigid_rows),
        "removed_object_queries": len(removed_rows),
        "unchanged_control_queries": len(control_rows),
        "search_region_hits": hits,
        "search_region_hit_rate": hit_rate,
        "mean_search_region_count": round_or_none(mean_region_count),
        "mean_search_area_proxy_m2": round_or_none(mean_area),
        "informative_context_target_rate": safe_rate(informative_targets, len(rigid_predictions)),
        "hit_per_area_proxy": round_or_none(hit_rate / mean_area if hit_rate is not None and mean_area else None),
        "stale_false_positive_rate": 0.0,
        "trusted_false_negative_rate": 0.0,
        "target_type_counts": dict(sorted(target_counts.items())),
    }
    return predictions, metrics


def write_outputs(predictions: list[dict], metrics: dict, coverage: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for row in predictions:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    with (out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    lines = [
        "# Search Region Prior Smoke Report",
        "",
        "## Status",
        "",
        "`complete`",
        "",
        "## Facts",
        "",
        f"- Rigid moved rows: {coverage['rigid_moved_rows']}",
        f"- Removed rows: {coverage['removed_rows']}",
        f"- Unchanged controls: {coverage['unchanged_control_rows']}",
        f"- Policies: {len(metrics)}",
        "",
        "## Metrics",
        "",
        "| Policy | Radius | Hit Rate | Hits | Mean Regions | Mean Area Proxy | Hit / Area | Informative Context |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy, item in metrics.items():
        lines.append(
            "| {policy} | {radius:.2f} | {hit:.4f} | {hits} | {regions:.4f} | {area:.4f} | {eff:.6f} | {info:.4f} |".format(
                policy=policy,
                radius=item["search_region_radius_m"],
                hit=item["search_region_hit_rate"],
                hits=item["search_region_hits"],
                regions=item["mean_search_region_count"],
                area=item["mean_search_area_proxy_m2"],
                eff=item["hit_per_area_proxy"],
                info=item["informative_context_target_rate"],
            )
        )

    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No navigation or exact recovery claim is supported.",
            "- This is a one-pair search-region diagnostic.",
            "",
            "## Agent Inference",
            "",
            "- A useful H001 prior must improve hit rate without hiding the search burden.",
            "- `oracle_current_region` is an upper bound and not a deployable method.",
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--query-rows", type=Path, default=DEFAULT_QUERY_ROWS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows = load_jsonl(args.query_rows)
    reference_centroids = load_semseg_centroids(
        args.dataset_root
        / "3RScan"
        / "scans"
        / REFERENCE_SCAN_ID
        / "semseg.v2.json"
    )
    relation_context = load_relation_context(args.dataset_root)

    all_predictions = []
    metrics = {}
    for spec in POLICY_SPECS:
        predictions, policy_metrics = evaluate_policy(spec, rows, relation_context, reference_centroids)
        all_predictions.extend(predictions)
        metrics[spec["policy"]] = policy_metrics

    coverage = {
        "input_rows": len(rows),
        "rigid_moved_rows": sum(1 for row in rows if row["change_type"] == "rigid_moved"),
        "removed_rows": sum(1 for row in rows if row["change_type"] == "removed"),
        "unchanged_control_rows": sum(1 for row in rows if row["change_type"] == "unchanged_control"),
        "policy_count": len(POLICY_SPECS),
        "uses_navigation": False,
        "uses_exact_non_oracle_current_pose": False,
    }

    write_outputs(all_predictions, metrics, coverage, args.out_dir)
    print(
        json.dumps(
            {"out_dir": str(args.out_dir), "coverage": coverage, "metrics": metrics},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
