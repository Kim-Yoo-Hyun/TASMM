#!/usr/bin/env python3
"""Audit prompt/label recall misses and fix the repair contract."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M85_prompt_label_recall_audit_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
M77_DIR = EXP_ROOT / "artifacts" / "E005-M77_offline_detector_prompt_repair_v0"
M84_DIR = EXP_ROOT / "artifacts" / "E005-M84_prompt_label_external_route_decision_v0"
VERSION = "e005_m85_prompt_label_recall_audit_v0"
BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
BROAD_LABELS = {"object", "furniture", "item", "thing"}


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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def load_prompt_info() -> dict[str, dict[str, dict[str, Any]]]:
    prompt_info: dict[str, dict[str, dict[str, Any]]] = {}
    for batch_id in ("all", *BATCHES):
        path = M68_DIR / "prompt_set.json" if batch_id == "all" else M68_DIR / "batches" / batch_id / "prompt_set.json"
        data = read_json(path)
        prompt_info[batch_id] = {str(row["label_canonical"]): row for row in data.get("labels", [])}
    return prompt_info


def load_targets() -> dict[str, dict[str, Any]]:
    return {str(row["target_uid"]): row for row in read_jsonl(M68_DIR / "real_proposal_object_targets.jsonl")}


def load_precap_rows() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for batch_id in BATCHES:
        out[batch_id] = read_jsonl(M69_DIR / batch_id / "container_output" / "pre_cap_candidate_pool.jsonl")
    return out


def load_frame_summary() -> dict[tuple[str, str], dict[str, int]]:
    summary: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "raw_prediction_count": 0,
            "projected_candidate_count": 0,
            "written_prediction_count": 0,
            "sampled_frame_count": 0,
        }
    )
    for batch_id in BATCHES:
        for row in read_jsonl(M69_DIR / batch_id / "frame_diagnostics.jsonl"):
            key = (batch_id, str(row.get("scan_id")))
            summary[key]["raw_prediction_count"] += int(row.get("raw_prediction_count") or 0)
            summary[key]["projected_candidate_count"] += int(row.get("projected_candidate_count") or 0)
            summary[key]["written_prediction_count"] += int(row.get("written_prediction_count") or 0)
            summary[key]["sampled_frame_count"] += 1
    return dict(summary)


def nearest_same_label(
    candidate_rows: list[dict[str, Any]],
    scan_id: str,
    label: str,
    centroid: list[float],
) -> dict[str, Any]:
    same_label = [
        row
        for row in candidate_rows
        if str(row.get("scan_id")) == scan_id and str(row.get("label_canonical")) == label and row.get("centroid_world_m")
    ]
    if not same_label:
        return {
            "nearest_pre_cap_same_label_confidence": None,
            "nearest_pre_cap_same_label_depth_valid_pixels": None,
            "nearest_pre_cap_same_label_distance_m": None,
            "nearest_pre_cap_same_label_frame_ids": [],
            "nearest_pre_cap_same_label_uid": None,
            "pre_cap_same_label_candidate_count": 0,
        }
    ranked = sorted(same_label, key=lambda row: distance(row["centroid_world_m"], centroid))
    nearest = ranked[0]
    return {
        "nearest_pre_cap_same_label_confidence": nearest.get("confidence"),
        "nearest_pre_cap_same_label_depth_valid_pixels": nearest.get("depth_valid_pixel_count"),
        "nearest_pre_cap_same_label_distance_m": round(distance(nearest["centroid_world_m"], centroid), 6),
        "nearest_pre_cap_same_label_frame_ids": nearest.get("frame_ids") or [],
        "nearest_pre_cap_same_label_uid": nearest.get("pre_cap_candidate_pool_uid") or nearest.get("raw_candidate_uid"),
        "pre_cap_same_label_candidate_count": len(same_label),
    }


def classify_row(row: dict[str, Any], prompt_row: dict[str, Any] | None, nearest: dict[str, Any]) -> str:
    label = str(row.get("label_canonical"))
    if label in BROAD_LABELS or prompt_row is None:
        return "prompt_contract_gap_broad_or_missing_label"
    candidate_count = int(nearest["pre_cap_same_label_candidate_count"])
    nearest_distance = nearest["nearest_pre_cap_same_label_distance_m"]
    if candidate_count == 0:
        return "detector_or_label_parse_no_same_label_candidates"
    if nearest_distance is not None and nearest_distance <= 1.0 and not row.get("pre_cap_detected"):
        return "matcher_or_target_assignment_audit_needed"
    if nearest_distance is not None and nearest_distance <= 2.0:
        return "localization_or_match_threshold_gap"
    return "visibility_or_detector_recall_miss_needs_projection_audit"


def build_audit_rows() -> list[dict[str, Any]]:
    prompt_info = load_prompt_info()
    targets = load_targets()
    precap = load_precap_rows()
    frame_summary = load_frame_summary()
    miss_rows = read_jsonl(M84_DIR / "prompt_detector_recall_miss_rows.jsonl")
    audit_rows: list[dict[str, Any]] = []
    for row in miss_rows:
        batch_id = str(row["batch_id"])
        scan_id = str(row["scan_id"])
        label = str(row["label_canonical"])
        target = targets.get(str(row["target_uid"]), {})
        prompt_row = prompt_info.get(batch_id, {}).get(label)
        all_prompt_row = prompt_info.get("all", {}).get(label)
        target_centroid = target.get("centroid_world_m") or []
        nearest = nearest_same_label(precap.get(batch_id, []), scan_id, label, target_centroid) if target_centroid else {}
        frames = frame_summary.get((batch_id, scan_id), {})
        audit_class = classify_row(row, prompt_row, nearest)
        out = {
            "allowed_repair_inputs": [
                "scan_id",
                "label_canonical",
                "prompt aliases from prompt_set",
                "RGB-D frames",
                "pre-cap candidate rows",
                "candidate confidence/depth/centroid",
            ],
            "audit_class": audit_class,
            "batch_id": batch_id,
            "blocked_policy_inputs": [
                "target_uid",
                "object_instance_id",
                "matched_3dssg_instance_id",
                "match_distance_m",
                "query success label",
            ],
            "label_canonical": label,
            "label_in_all_prompt_set": all_prompt_row is not None,
            "label_in_batch_prompt_set": prompt_row is not None,
            "label_is_broad": label in BROAD_LABELS,
            "m77_pre_cap_detected": bool(row.get("pre_cap_detected")),
            "m77_repair_class": row.get("repair_class"),
            "object_instance_id": target.get("object_instance_id"),
            "prompt_aliases": prompt_row.get("aliases", []) if prompt_row else [],
            "prompt_strings": prompt_row.get("prompts", []) if prompt_row else [],
            "record_type": "e005_m85_prompt_label_recall_audit",
            "scan_id": scan_id,
            "target_uid": row.get("target_uid"),
        }
        out.update(nearest)
        out.update({f"scan_{key}": value for key, value in frames.items()})
        audit_rows.append(out)
    return audit_rows


def build_contract(coverage: dict[str, Any], audit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "allowed_inputs_for_repair_policy": [
            "scan_id",
            "label_canonical",
            "prompt_set labels and aliases fixed before detector run",
            "RGB-D sequence frames and camera poses",
            "pre-cap candidate confidence/depth/centroid fields",
            "candidate label text before target matching",
        ],
        "blocked_inputs_for_repair_policy": [
            "target_uid",
            "object_instance_id",
            "matched_3dssg_instance_id",
            "nearest target distance",
            "target recovery label",
            "query-level success/failure labels",
        ],
        "claim_boundary": {
            "deployable_search_policy_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "m85_is_audit_not_detector_result": True,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "repair_steps": [
            {
                "output": "candidate label-normalization rule and denominator decision",
                "step": "broad_label_policy",
                "target_classes": ["prompt_contract_gap_broad_or_missing_label"],
            },
            {
                "output": "prompt alias expansion list fixed without target matching labels",
                "step": "prompt_alias_policy",
                "target_classes": ["detector_or_label_parse_no_same_label_candidates"],
            },
            {
                "output": "visibility/match-threshold audit before changing detector prompts",
                "step": "projection_and_matcher_audit",
                "target_classes": ["localization_or_match_threshold_gap", "matcher_or_target_assignment_audit_needed"],
            },
            {
                "output": "only after above: decide whether to launch a bounded prompt-repair detector rerun",
                "step": "bounded_detector_rerun_gate",
                "target_classes": ["detector_or_label_parse_no_same_label_candidates"],
            },
        ],
        "selected_next_unit": coverage["next_recommended_unit"],
        "version": VERSION,
    }


def build_report(coverage: dict[str, Any], audit_rows: list[dict[str, Any]]) -> str:
    class_lines = ["| Audit class | Targets |", "| --- | ---: |"]
    for label, count in coverage["audit_class_counts"].items():
        class_lines.append(f"| `{label}` | {count} |")
    row_lines = [
        "| Target | Label | Batch | Class | Prompt in batch | Pre-cap same-label | Nearest dist | Scan written preds |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in audit_rows:
        dist = row.get("nearest_pre_cap_same_label_distance_m")
        dist_text = "-" if dist is None else f"{dist:.3f}"
        row_lines.append(
            "| `{target}` | `{label}` | `{batch}` | `{cls}` | {prompt} | {count} | {dist} | {written} |".format(
                target=row["target_uid"],
                label=row["label_canonical"],
                batch=row["batch_id"],
                cls=row["audit_class"],
                prompt=str(row["label_in_batch_prompt_set"]).lower(),
                count=row["pre_cap_same_label_candidate_count"],
                dist=dist_text,
                written=row.get("scan_written_prediction_count", 0),
            )
        )
    return "\n".join(
        [
            "# E005-M85 Prompt/Label Recall Miss Audit",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Selected route: `{coverage['selected_next_route']}`.",
            f"- Audited recall-miss targets: {coverage['audited_recall_miss_targets']} / {coverage['target_rows']}.",
            f"- Broad/missing-label targets: {coverage['broad_or_missing_label_targets']}.",
            f"- No-same-label candidate targets: {coverage['no_same_label_candidate_targets']}.",
            f"- Localization or matcher-audit targets: {coverage['localization_or_matcher_audit_targets']}.",
            "",
            "## Audit Class Counts",
            "",
            *class_lines,
            "",
            "## Target Rows",
            "",
            *row_lines,
            "",
            "## Repair Contract",
            "",
            "- Do not use `target_uid`, `object_instance_id`, target match distance, or query success labels inside a detector or repair policy.",
            "- Use target-linked fields only for offline diagnosis and final evaluation.",
            "- Handle broad labels separately from detector recall; `object` should not silently become an open-ended prompt success criterion.",
            "- Run visibility/matcher audit before changing detector prompts for targets whose nearest same-label candidate is near the 1m match threshold.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_rows = build_audit_rows()
    class_counts = Counter(str(row["audit_class"]) for row in audit_rows)
    broad_or_missing = class_counts.get("prompt_contract_gap_broad_or_missing_label", 0)
    no_same_label = class_counts.get("detector_or_label_parse_no_same_label_candidates", 0)
    localization_or_matcher = (
        class_counts.get("localization_or_match_threshold_gap", 0)
        + class_counts.get("matcher_or_target_assignment_audit_needed", 0)
    )
    coverage = {
        "audit_class_counts": dict(class_counts.most_common()),
        "audited_recall_miss_targets": len(audit_rows),
        "broad_or_missing_label_targets": broad_or_missing,
        "deployable_search_policy_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "localization_or_matcher_audit_targets": localization_or_matcher,
        "next_recommended_unit": "E005-M86 prompt repair preflight or visibility/matcher audit",
        "no_same_label_candidate_targets": no_same_label,
        "real_navigation_sr_spl_claim_ready": False,
        "selected_next_route": "visibility_matcher_audit_then_bounded_prompt_repair_preflight",
        "status": "e005_m85_prompt_label_recall_audit_ready",
        "target_rows": int(read_json(M84_DIR / "coverage.json").get("target_rows", 65)),
        "version": VERSION,
    }
    contract = build_contract(coverage, audit_rows)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "repair_contract.json", contract)
    write_jsonl(OUT_DIR / "recall_miss_audit_rows.jsonl", audit_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, audit_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
