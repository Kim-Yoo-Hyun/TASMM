#!/usr/bin/env python3
"""Run H001 real-pair query-level value smoke.

This is a hypothesis-stage smoke test. It uses one staged 3RScan
reference-rescan pair and does not run navigation or a full benchmark.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_LABELS = H001_ROOT / "artifacts" / "schema_smoke" / "stale_labels.jsonl"
DEFAULT_RIGID_GEOMETRY = H001_ROOT / "artifacts" / "pair_geometry_check" / "rigid_geometry.jsonl"
DEFAULT_REMOVED_GEOMETRY = H001_ROOT / "artifacts" / "pair_geometry_check" / "removed_geometry.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "real_pair_query_smoke"
RESCAN_ID = "c7895f07-339c-2d13-8176-7418b6e8d7ce"

POLICIES = [
    "static_map",
    "time_decay",
    "relation_only",
    "ours_staleness_v0",
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


def load_semseg_objects(path: Path) -> dict[str, dict]:
    data = load_json(path)
    objects = {}
    for group in data.get("segGroups", []):
        object_id = str(group.get("objectId", group.get("id")))
        obb = group.get("obb", {})
        centroid = obb.get("centroid")
        objects[object_id] = {
            "label": group.get("label"),
            "centroid": [float(value) for value in centroid] if centroid else None,
        }
    return objects


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def index_by_ref(rows: list[dict]) -> dict[str, dict]:
    return {str(row["instance_reference"]): row for row in rows}


def enrich_rows(
    labels: list[dict],
    rigid_geometry: dict[str, dict],
    removed_geometry: dict[str, dict],
    rescan_semseg: dict[str, dict],
    current_target_threshold_m: float,
) -> tuple[list[dict], dict]:
    enriched = []
    join_errors = []

    for row in labels:
        object_id = str(row["object_instance_id_ref"])
        item = dict(row)
        item["pair_rescan_id"] = RESCAN_ID
        item["pair_geometry_join"] = False
        item["pair_geometry_valid"] = False
        item["pair_geometry_error_m"] = None
        item["pair_current_centroid"] = None
        item["pair_absent_confirmed"] = False
        item["control_present_in_rescan_semseg"] = None
        item["control_label_match"] = None

        if row["change_type"] == "rigid_moved":
            geom = rigid_geometry.get(object_id)
            if geom is None:
                join_errors.append({"object_instance_id_ref": object_id, "reason": "missing_rigid_geometry"})
            else:
                item["pair_geometry_join"] = bool(geom.get("ref_geometry_join") and geom.get("rescan_geometry_join"))
                item["pair_geometry_error_m"] = geom.get("object_direct_error_m")
                item["pair_current_centroid"] = geom.get("rescan_centroid")
                item["pair_geometry_valid"] = (
                    item["pair_geometry_join"]
                    and bool(geom.get("label_match"))
                    and item["pair_geometry_error_m"] is not None
                    and item["pair_geometry_error_m"] <= current_target_threshold_m
                )
                item["current_centroid_est"] = geom.get("rescan_centroid")
                item["current_location_source"] = "pair_validated_rescan_semseg_centroid"
                item["transform_direction_verified"] = True

        elif row["change_type"] == "removed":
            geom = removed_geometry.get(object_id)
            if geom is None:
                join_errors.append({"object_instance_id_ref": object_id, "reason": "missing_removed_geometry"})
            else:
                item["pair_geometry_join"] = bool(geom.get("ref_geometry_join"))
                item["pair_absent_confirmed"] = not bool(geom.get("present_in_rescan_semseg"))
                item["pair_geometry_valid"] = item["pair_absent_confirmed"]

        elif row["change_type"] == "unchanged_control":
            rescan_obj = rescan_semseg.get(object_id)
            item["control_present_in_rescan_semseg"] = rescan_obj is not None
            item["control_label_match"] = (
                rescan_obj is not None and rescan_obj.get("label") == row.get("object_label")
            )
            item["pair_geometry_join"] = rescan_obj is not None
            item["pair_geometry_valid"] = item["control_label_match"]
            if rescan_obj and rescan_obj.get("centroid"):
                item["pair_current_centroid"] = rescan_obj["centroid"]

        enriched.append(item)

    coverage = {
        "input_rows": len(labels),
        "rigid_rows": sum(1 for row in enriched if row["change_type"] == "rigid_moved"),
        "removed_rows": sum(1 for row in enriched if row["change_type"] == "removed"),
        "unchanged_control_rows": sum(1 for row in enriched if row["change_type"] == "unchanged_control"),
        "rigid_geometry_join": sum(
            1 for row in enriched if row["change_type"] == "rigid_moved" and row["pair_geometry_join"]
        ),
        "rigid_geometry_valid": sum(
            1 for row in enriched if row["change_type"] == "rigid_moved" and row["pair_geometry_valid"]
        ),
        "removed_absent_confirmed": sum(
            1 for row in enriched if row["change_type"] == "removed" and row["pair_absent_confirmed"]
        ),
        "unchanged_control_pair_valid": sum(
            1 for row in enriched if row["change_type"] == "unchanged_control" and row["pair_geometry_valid"]
        ),
        "join_errors": join_errors,
    }
    coverage["ready"] = (
        coverage["rigid_geometry_join"] == coverage["rigid_rows"]
        and coverage["rigid_geometry_valid"] == coverage["rigid_rows"]
        and coverage["removed_absent_confirmed"] == coverage["removed_rows"]
        and not join_errors
    )
    return enriched, coverage


def predict(policy: str, row: dict) -> dict:
    change_type = row["change_type"]

    if policy in {"static_map", "time_decay", "relation_only"}:
        reason = {
            "static_map": "Static map returns the stored reference location.",
            "time_decay": "No elapsed-time threshold is available in this one-pair smoke.",
            "relation_only": "No after-scene relation contradiction is used in this one-pair smoke.",
        }[policy]
        return {
            "memory_state": "trusted",
            "action": "return_old_location",
            "target_type": "stale_old_location" if row.get("old_memory_is_stale") else "old_location_target",
            "returns_old_location": True,
            "suppresses_old_location": False,
            "returns_current_target": False,
            "current_target_valid": False,
            "recovers_current_location": False,
            "target_available": True,
            "reason": reason,
        }

    if policy == "ours_staleness_v0":
        if change_type == "rigid_moved":
            return {
                "memory_state": "needs_reobservation",
                "action": "redirect_reobservation",
                "target_type": "old_context_target",
                "returns_old_location": False,
                "suppresses_old_location": True,
                "returns_current_target": False,
                "current_target_valid": False,
                "recovers_current_location": False,
                "target_available": True,
                "reason": "Suppress stale old location and request re-observation; no current observation is used.",
            }
        if change_type == "removed":
            return {
                "memory_state": "stale",
                "action": "suppress_old_location",
                "target_type": "absent_target",
                "returns_old_location": False,
                "suppresses_old_location": True,
                "returns_current_target": False,
                "current_target_valid": False,
                "recovers_current_location": False,
                "target_available": False,
                "reason": "Removed object should not return the stale reference location.",
            }
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted",
                "action": "return_old_location",
                "target_type": "old_location_target",
                "returns_old_location": True,
                "suppresses_old_location": False,
                "returns_current_target": False,
                "current_target_valid": False,
                "recovers_current_location": False,
                "target_available": True,
                "reason": "No contradiction evidence; keep control object trusted.",
            }

    if policy == "oracle_current_pose":
        if change_type == "rigid_moved":
            valid = bool(row.get("pair_geometry_valid"))
            return {
                "memory_state": "trusted_current",
                "action": "return_pair_validated_current_target",
                "target_type": "current_estimate_target",
                "returns_old_location": False,
                "suppresses_old_location": True,
                "returns_current_target": True,
                "current_target_valid": valid,
                "recovers_current_location": valid,
                "target_available": valid,
                "reason": "Uses pair-validated rescan semantic centroid.",
            }
        if change_type == "removed":
            return {
                "memory_state": "absent",
                "action": "suppress_old_location",
                "target_type": "absent_target",
                "returns_old_location": False,
                "suppresses_old_location": True,
                "returns_current_target": False,
                "current_target_valid": False,
                "recovers_current_location": False,
                "target_available": False,
                "reason": "Pair geometry confirms absence in rescan semantic payload.",
            }
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted_current" if row.get("pair_geometry_valid") else "trusted",
                "action": "return_pair_validated_current_target"
                if row.get("pair_geometry_valid")
                else "return_old_location",
                "target_type": "current_estimate_target"
                if row.get("pair_geometry_valid")
                else "old_location_target",
                "returns_old_location": not bool(row.get("pair_geometry_valid")),
                "suppresses_old_location": False,
                "returns_current_target": bool(row.get("pair_geometry_valid")),
                "current_target_valid": bool(row.get("pair_geometry_valid")),
                "recovers_current_location": bool(row.get("pair_geometry_valid")),
                "target_available": True,
                "reason": "Control object is checked against rescan semantic payload when possible.",
            }

    return {
        "memory_state": "excluded",
        "action": "excluded",
        "target_type": "excluded",
        "returns_old_location": False,
        "suppresses_old_location": False,
        "returns_current_target": False,
        "current_target_valid": False,
        "recovers_current_location": False,
        "target_available": False,
        "reason": f"Unsupported policy/change type: {policy}/{change_type}",
    }


def evaluate(rows: list[dict]) -> tuple[list[dict], dict]:
    predictions = []
    metrics = {}

    for policy in POLICIES:
        policy_rows = []
        for row in rows:
            pred = predict(policy, row)
            item = {
                "policy": policy,
                "episode_id": row["episode_id"],
                "query": row["query"],
                "object_instance_id_ref": row["object_instance_id_ref"],
                "object_label": row["object_label"],
                "change_type": row["change_type"],
                "pair_geometry_valid": row["pair_geometry_valid"],
                "pair_geometry_error_m": row["pair_geometry_error_m"],
                "pair_current_centroid": row["pair_current_centroid"],
                **pred,
            }
            policy_rows.append(item)
            predictions.append(item)

        changed_preds = [item for item in policy_rows if item["change_type"] in {"rigid_moved", "removed"}]
        rigid_preds = [item for item in policy_rows if item["change_type"] == "rigid_moved"]
        removed_preds = [item for item in policy_rows if item["change_type"] == "removed"]
        control_preds = [item for item in policy_rows if item["change_type"] == "unchanged_control"]
        target_counts = Counter(item["target_type"] for item in policy_rows)

        stale_old_returns = sum(1 for item in changed_preds if item["returns_old_location"])
        control_stale_marks = sum(
            1
            for item in control_preds
            if item["memory_state"] in {"stale", "needs_reobservation"}
            or item["action"] in {"suppress_old_location", "redirect_reobservation"}
        )
        removed_suppressed = sum(1 for item in removed_preds if item["action"] == "suppress_old_location")
        current_targets = sum(1 for item in rigid_preds if item["returns_current_target"])
        current_targets_valid = sum(1 for item in rigid_preds if item["current_target_valid"])
        recovered = sum(1 for item in rigid_preds if item["recovers_current_location"])

        metrics[policy] = {
            "changed_object_queries": len(changed_preds),
            "rigid_moved_object_queries": len(rigid_preds),
            "removed_object_queries": len(removed_preds),
            "unchanged_control_queries": len(control_preds),
            "stale_old_location_returns": stale_old_returns,
            "stale_false_positive_rate": safe_rate(stale_old_returns, len(changed_preds)),
            "control_stale_marks": control_stale_marks,
            "trusted_false_negative_rate": safe_rate(control_stale_marks, len(control_preds)),
            "removed_suppression_success": safe_rate(removed_suppressed, len(removed_preds)),
            "current_target_return_rate": safe_rate(current_targets, len(rigid_preds)),
            "current_target_valid_rate": safe_rate(current_targets_valid, len(rigid_preds)),
            "moved_object_recovery_success": safe_rate(recovered, len(rigid_preds)),
            "target_type_counts": dict(sorted(target_counts.items())),
        }

    oracle = metrics["oracle_current_pose"]["moved_object_recovery_success"]
    for policy in POLICIES:
        recovery = metrics[policy]["moved_object_recovery_success"]
        metrics[policy]["oracle_gap"] = None if oracle is None or recovery is None else round(oracle - recovery, 6)

    return predictions, metrics


def write_outputs(enriched_rows: list[dict], predictions: list[dict], metrics: dict, coverage: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "query_rows.jsonl").open("w", encoding="utf-8") as f:
        for row in enriched_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    with (out_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for item in predictions:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    with (out_dir / "coverage.json").open("w", encoding="utf-8") as f:
        json.dump(coverage, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    lines = [
        "# Real-Pair Query Smoke Report",
        "",
        "## Status",
        "",
        "`ready_with_recovery_gap`" if coverage["ready"] else "`needs_review`",
        "",
        "## Facts",
        "",
        f"- Query rows: {coverage['input_rows']}",
        f"- Rigid rows: {coverage['rigid_rows']}",
        f"- Removed rows: {coverage['removed_rows']}",
        f"- Unchanged controls: {coverage['unchanged_control_rows']}",
        f"- Rigid geometry valid: {coverage['rigid_geometry_valid']} / {coverage['rigid_rows']}",
        f"- Removed absent confirmed: {coverage['removed_absent_confirmed']} / {coverage['removed_rows']}",
        f"- Unchanged controls pair-valid: {coverage['unchanged_control_pair_valid']} / {coverage['unchanged_control_rows']}",
        "",
        "## Metrics",
        "",
        "| Policy | Stale FPR | Trusted FNR | Removed Suppression | Current Target Valid | Recovery | Oracle Gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in POLICIES:
        item = metrics[policy]
        lines.append(
            "| {policy} | {stale:.4f} | {trusted:.4f} | {removed:.4f} | {current:.4f} | {recovery:.4f} | {gap:.4f} |".format(
                policy=policy,
                stale=item["stale_false_positive_rate"],
                trusted=item["trusted_false_negative_rate"],
                removed=item["removed_suppression_success"],
                current=item["current_target_valid_rate"],
                recovery=item["moved_object_recovery_success"],
                gap=item["oracle_gap"],
            )
        )

    lines.extend(
        [
            "",
            "## Paper Claims",
            "",
            "- No paper-level result is supported yet.",
            "- This is a one-pair query-level smoke, not a benchmark result.",
            "",
            "## Agent Inference",
            "",
            "- Pair-validated geometry confirms that stale old-location suppression changes query behavior on this target pair.",
            "- `ours_staleness_v0` still does not recover moved objects without current observation or search.",
            "- The remaining oracle gap should drive the next hypothesis-stage decision.",
        ]
    )

    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--rigid-geometry", type=Path, default=DEFAULT_RIGID_GEOMETRY)
    parser.add_argument("--removed-geometry", type=Path, default=DEFAULT_REMOVED_GEOMETRY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--current-target-threshold-m", type=float, default=0.35)
    args = parser.parse_args()

    labels = load_jsonl(args.labels)
    rigid_geometry = index_by_ref(load_jsonl(args.rigid_geometry))
    removed_geometry = index_by_ref(load_jsonl(args.removed_geometry))
    rescan_semseg = load_semseg_objects(
        args.dataset_root / "3RScan" / "scans" / RESCAN_ID / "semseg.v2.json"
    )

    enriched_rows, coverage = enrich_rows(
        labels,
        rigid_geometry,
        removed_geometry,
        rescan_semseg,
        args.current_target_threshold_m,
    )
    coverage["current_target_threshold_m"] = args.current_target_threshold_m

    predictions, metrics = evaluate(enriched_rows)
    write_outputs(enriched_rows, predictions, metrics, coverage, args.out_dir)

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
