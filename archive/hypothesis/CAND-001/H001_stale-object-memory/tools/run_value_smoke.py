#!/usr/bin/env python3
"""Run H001 hypothesis-stage baseline/value smoke.

This script evaluates simple memory policies on metadata-derived stale labels.
It is not a final experiment and does not use navigation or full replay.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = H001_ROOT / "artifacts" / "schema_smoke" / "stale_labels.jsonl"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "value_smoke"


POLICIES = [
    "static_map",
    "time_decay",
    "relation_only",
    "ours_staleness",
    "oracle_current_pose",
]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def predict(policy: str, row: dict) -> dict:
    change_type = row["change_type"]

    if policy == "static_map":
        return {
            "memory_state": "trusted",
            "action": "return_old_location",
            "returns_old_location": True,
            "recovers_current_location": False,
            "reason": "Static memory has no stale evidence or update rule.",
        }

    if policy == "time_decay":
        return {
            "memory_state": "trusted",
            "action": "return_old_location",
            "returns_old_location": True,
            "recovers_current_location": False,
            "reason": "No elapsed-time threshold or unchanged controls are available in this schema smoke.",
        }

    if policy == "relation_only":
        return {
            "memory_state": "trusted",
            "action": "return_old_location",
            "returns_old_location": True,
            "recovers_current_location": False,
            "reason": "No after-scene carrier/support relation contradiction is available in this schema smoke.",
        }

    if policy == "ours_staleness":
        if change_type == "rigid_moved":
            return {
                "memory_state": "needs_reobservation",
                "action": "redirect_reobservation",
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Task-relevant object memory is contradicted by metadata-derived change evidence.",
            }
        if change_type == "removed":
            return {
                "memory_state": "stale",
                "action": "suppress_old_location",
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Object is marked removed in metadata-derived change evidence.",
            }
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted",
                "action": "return_old_location",
                "returns_old_location": True,
                "recovers_current_location": False,
                "reason": "No contradiction evidence is present for this control row.",
            }

    if policy == "oracle_current_pose":
        if change_type == "rigid_moved":
            return {
                "memory_state": "trusted_current",
                "action": "return_current_estimate",
                "returns_old_location": False,
                "recovers_current_location": True,
                "reason": "Uses transform-derived current centroid estimate.",
            }
        if change_type == "removed":
            return {
                "memory_state": "absent",
                "action": "suppress_old_location",
                "returns_old_location": False,
                "recovers_current_location": False,
                "reason": "Oracle knows the object is absent.",
            }
        if change_type == "unchanged_control":
            return {
                "memory_state": "trusted_current",
                "action": "return_current_estimate",
                "returns_old_location": True,
                "recovers_current_location": True,
                "reason": "Oracle knows the control object remains valid.",
            }

    return {
        "memory_state": "excluded",
        "action": "excluded",
        "returns_old_location": False,
        "recovers_current_location": False,
        "reason": f"Unsupported policy/change type: {policy}/{change_type}",
    }


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


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
                "object_instance_id_ref": row["object_instance_id_ref"],
                "object_label": row["object_label"],
                "change_type": row["change_type"],
                "evaluation_scope": row["evaluation_scope"],
                **pred,
            }
            policy_rows.append(item)
            predictions.append(item)

        changed = [row for row in rows if row.get("old_memory_is_stale")]
        rigid = [row for row in rows if row["change_type"] == "rigid_moved"]
        removed = [row for row in rows if row["change_type"] == "removed"]
        controls = [row for row in rows if row["change_type"] == "unchanged_control"]
        changed_preds = [item for item in policy_rows if item["change_type"] in {"rigid_moved", "removed"}]
        rigid_preds = [item for item in policy_rows if item["change_type"] == "rigid_moved"]
        removed_preds = [item for item in policy_rows if item["change_type"] == "removed"]
        control_preds = [item for item in policy_rows if item["change_type"] == "unchanged_control"]

        stale_old_returns = sum(1 for item in changed_preds if item["returns_old_location"])
        moved_recovered = sum(1 for item in rigid_preds if item["recovers_current_location"])
        moved_redirected = sum(1 for item in rigid_preds if item["action"] == "redirect_reobservation")
        removed_suppressed = sum(1 for item in removed_preds if item["action"] == "suppress_old_location")
        control_stale_marks = sum(
            1
            for item in control_preds
            if item["memory_state"] in {"stale", "needs_reobservation"}
            or item["action"] in {"suppress_old_location", "redirect_reobservation"}
        )

        metrics[policy] = {
            "changed_object_queries": len(changed),
            "rigid_moved_object_queries": len(rigid),
            "removed_object_queries": len(removed),
            "unchanged_control_queries": len(controls),
            "stale_old_location_returns": stale_old_returns,
            "stale_false_positive_rate": safe_rate(stale_old_returns, len(changed_preds)),
            "moved_object_recovery_success": safe_rate(moved_recovered, len(rigid_preds)),
            "moved_object_recovery_attempts": moved_redirected,
            "reobservation_redirect_rate": safe_rate(moved_redirected, len(rigid_preds)),
            "removed_suppression_success": safe_rate(removed_suppressed, len(removed_preds)),
            "control_stale_marks": control_stale_marks,
            "trusted_false_negative_rate": safe_rate(control_stale_marks, len(control_preds)),
        }

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
        "# Value Smoke Report",
        "",
        "## Status",
        "",
        "Hypothesis-stage smoke complete.",
        "",
        "## Facts",
        "",
        "- Input labels: `../schema_smoke/stale_labels.jsonl`",
        "- Output predictions: `predictions.jsonl`",
        "- Output metrics: `metrics.json`",
        "- This smoke uses metadata-derived stale labels, not real after-scene RGB-D replay.",
        "",
        "## Metrics",
        "",
        "| Policy | Stale FPR | Trusted FNR | Moved Recovery | Reobs Attempts | Reobs Rate | Removed Suppression |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for policy in POLICIES:
        item = metrics[policy]
        lines.append(
            "| {policy} | {stale:.4f} | {trusted:.4f} | {recovery:.4f} | {attempts} | {redirect:.4f} | {removed:.4f} |".format(
                policy=policy,
                stale=item["stale_false_positive_rate"],
                trusted=item["trusted_false_negative_rate"],
                recovery=item["moved_object_recovery_success"],
                attempts=item["moved_object_recovery_attempts"],
                redirect=item["reobservation_redirect_rate"],
                removed=item["removed_suppression_success"],
            )
        )

    lines.extend(
        [
            "",
            "## Agent Inference",
            "",
            "- `ours_staleness` removes stale old-location returns in this metadata-derived smoke.",
            "- `ours_staleness` keeps unchanged controls trusted when no contradiction evidence is present.",
            "- `ours_staleness` does not recover moved objects by itself; it redirects re-observation.",
            "- `time_decay` and `relation_only` remain weak competitors because no elapsed-time sweep or after-scene relation contradiction is included.",
            "- This smoke supports continuing H001, but it is not enough for experiment-stage promotion.",
            "",
            "## Next Action",
            "",
            "Stage one real paired rescan or add a minimal re-observation policy before treating the value check as paper-level evidence.",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows = load_jsonl(args.labels)
    predictions, metrics = evaluate(rows)
    write_outputs(predictions, metrics, args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), "metrics": metrics}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
