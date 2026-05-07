#!/usr/bin/env python3
"""Run H001 minimal re-observation policy smoke."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_LABELS = H001_ROOT / "artifacts" / "schema_smoke" / "stale_labels.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "reobservation_smoke"
REFERENCE_SCAN_ID = "ddc73797-765b-241a-9e2c-097c5989baf6"
CONTEXT_RELATIONS = {"standing on", "lying on", "attached to", "hanging on"}
STRUCTURAL_CONTEXT_LABELS = {"floor", "wall", "ceiling"}

POLICIES = [
    "static_map",
    "ours_staleness_v0",
    "ours_staleness_oracle_context",
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


def find_scan(scans: list[dict], scan_id: str) -> dict:
    for scan in scans:
        if scan.get("scan") == scan_id:
            return scan
    raise RuntimeError(f"scan not found: {scan_id}")


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


def predict(policy: str, row: dict, relation_context: list[dict]) -> dict:
    change_type = row["change_type"]

    if policy == "static_map":
        return {
            "memory_state": "trusted",
            "target_type": "stale_old_location" if row.get("old_memory_is_stale") else "old_location_target",
            "target_available": True,
            "returns_old_location": True,
            "recovers_current_location": False,
            "reason": "Static map returns stored old location.",
        }

    if policy == "ours_staleness_v0":
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted",
                "target_type": "old_location_target",
                "target_available": True,
                "returns_old_location": True,
                "recovers_current_location": False,
                "reason": "No contradiction evidence; keep control object trusted.",
            }
        if change_type == "removed":
            return {
                "memory_state": "stale",
                "target_type": "absent_target",
                "target_available": False,
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Removed object should not return stale old location.",
            }
        if change_type == "rigid_moved":
            has_context = bool(relation_context)
            return {
                "memory_state": "needs_reobservation",
                "target_type": "old_context_target" if has_context else "old_location_suppressed",
                "target_available": has_context,
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Redirect to old relation context when available; no current observation is used.",
            }

    if policy == "ours_staleness_oracle_context":
        if change_type == "rigid_moved":
            return {
                "memory_state": "trusted_current",
                "target_type": "current_estimate_target",
                "target_available": row.get("current_centroid_est") is not None,
                "returns_old_location": False,
                "recovers_current_location": row.get("current_centroid_est") is not None,
                "reason": "Diagnostic upper bound that uses metadata-derived current estimate.",
            }
        return predict("ours_staleness_v0", row, relation_context)

    if policy == "oracle_current_pose":
        if change_type == "rigid_moved":
            return {
                "memory_state": "trusted_current",
                "target_type": "current_estimate_target",
                "target_available": row.get("current_centroid_est") is not None,
                "returns_old_location": False,
                "recovers_current_location": row.get("current_centroid_est") is not None,
                "reason": "Oracle uses metadata-derived current estimate.",
            }
        if change_type == "removed":
            return {
                "memory_state": "absent",
                "target_type": "absent_target",
                "target_available": False,
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Oracle knows removed object is absent.",
            }
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted_current",
                "target_type": "current_estimate_target",
                "target_available": True,
                "returns_old_location": True,
                "recovers_current_location": True,
                "reason": "Oracle keeps control object current.",
            }

    return {
        "memory_state": "excluded",
        "target_type": "excluded",
        "target_available": False,
        "returns_old_location": False,
        "recovers_current_location": False,
        "reason": f"Unsupported policy/change type: {policy}/{change_type}",
    }


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def evaluate(rows: list[dict], relation_context: dict[str, list[dict]]) -> tuple[list[dict], dict]:
    predictions = []
    metrics = {}

    for policy in POLICIES:
        policy_rows = []
        for row in rows:
            context = relation_context.get(row["object_instance_id_ref"], [])
            pred = predict(policy, row, context)
            item = {
                "policy": policy,
                "episode_id": row["episode_id"],
                "object_instance_id_ref": row["object_instance_id_ref"],
                "object_label": row["object_label"],
                "change_type": row["change_type"],
                "relation_context": context,
                **pred,
            }
            policy_rows.append(item)
            predictions.append(item)

        changed_preds = [item for item in policy_rows if item["change_type"] in {"rigid_moved", "removed"}]
        rigid_preds = [item for item in policy_rows if item["change_type"] == "rigid_moved"]
        control_preds = [item for item in policy_rows if item["change_type"] == "unchanged_control"]
        target_counts = Counter(item["target_type"] for item in policy_rows)

        stale_old_returns = sum(1 for item in changed_preds if item["returns_old_location"])
        control_stale_marks = sum(
            1
            for item in control_preds
            if item["memory_state"] in {"stale", "needs_reobservation"}
            or item["target_type"] in {"absent_target", "old_location_suppressed"}
        )
        moved_recovered = sum(1 for item in rigid_preds if item["recovers_current_location"])
        moved_target_available = sum(
            1
            for item in rigid_preds
            if item["target_available"] and item["target_type"] in {"old_context_target", "current_estimate_target"}
        )
        old_context_targets = sum(1 for item in rigid_preds if item["target_type"] == "old_context_target")
        informative_old_context_targets = sum(
            1
            for item in rigid_preds
            if item["target_type"] == "old_context_target"
            and any(
                context_item.get("other_label") not in STRUCTURAL_CONTEXT_LABELS
                for context_item in item["relation_context"]
            )
        )

        metrics[policy] = {
            "changed_object_queries": len(changed_preds),
            "rigid_moved_object_queries": len(rigid_preds),
            "unchanged_control_queries": len(control_preds),
            "stale_false_positive_rate": safe_rate(stale_old_returns, len(changed_preds)),
            "trusted_false_negative_rate": safe_rate(control_stale_marks, len(control_preds)),
            "moved_object_recovery_success": safe_rate(moved_recovered, len(rigid_preds)),
            "reobservation_target_available_rate": safe_rate(moved_target_available, len(rigid_preds)),
            "old_context_target_rate": safe_rate(old_context_targets, len(rigid_preds)),
            "informative_old_context_target_rate": safe_rate(informative_old_context_targets, len(rigid_preds)),
            "target_type_counts": dict(sorted(target_counts.items())),
        }

    oracle = metrics["oracle_current_pose"]["moved_object_recovery_success"]
    for policy in POLICIES:
        recovery = metrics[policy]["moved_object_recovery_success"]
        metrics[policy]["oracle_gap"] = None if oracle is None or recovery is None else round(oracle - recovery, 6)

    return predictions, metrics


def write_outputs(predictions: list[dict], metrics: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    metrics_path = out_dir / "metrics.json"
    report_path = out_dir / "report.md"

    with predictions_path.open("w", encoding="utf-8") as f:
        for item in predictions:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    lines = [
        "# Re-observation Smoke Report",
        "",
        "## Status",
        "",
        "Hypothesis-stage re-observation smoke complete.",
        "",
        "## Facts",
        "",
        "- Input labels: `../schema_smoke/stale_labels.jsonl`",
        "- Output predictions: `predictions.jsonl`",
        "- Output metrics: `metrics.json`",
        "- Old context is derived from `3DSSG` support/contact-style relationships.",
        "",
        "## Metrics",
        "",
        "| Policy | Stale FPR | Trusted FNR | Recovery | Target Available | Old Context | Informative Context | Oracle Gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in POLICIES:
        item = metrics[policy]
        lines.append(
            "| {policy} | {stale:.4f} | {trusted:.4f} | {recovery:.4f} | {target:.4f} | {context:.4f} | {informative:.4f} | {gap:.4f} |".format(
                policy=policy,
                stale=item["stale_false_positive_rate"],
                trusted=item["trusted_false_negative_rate"],
                recovery=item["moved_object_recovery_success"],
                target=item["reobservation_target_available_rate"],
                context=item["old_context_target_rate"],
                informative=item["informative_old_context_target_rate"],
                gap=item["oracle_gap"],
            )
        )

    lines.extend(
        [
            "",
            "## Agent Inference",
            "",
            "- `ours_staleness_v0` can produce old-context re-observation targets for moved objects when old relation context exists.",
            "- Some old-context targets may be weak if they only refer to structural context such as floor, wall, or ceiling.",
            "- `ours_staleness_v0` still does not recover moved objects because it does not observe or infer the new current location.",
            "- The remaining oracle gap isolates the need for real after-observation, search, or a learned relocation prior.",
            "",
            "## Next Action",
            "",
            "Decide whether H001 should next stage a real paired rescan or add a non-oracle search prior.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows = load_jsonl(args.labels)
    relation_context = load_relation_context(args.dataset_root)
    predictions, metrics = evaluate(rows, relation_context)
    write_outputs(predictions, metrics, args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), "metrics": metrics}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
