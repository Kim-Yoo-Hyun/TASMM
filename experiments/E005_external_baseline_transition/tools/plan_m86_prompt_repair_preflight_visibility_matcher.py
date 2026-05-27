#!/usr/bin/env python3
"""Decide whether prompt repair or visibility/matcher audit comes first."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M86_prompt_repair_preflight_visibility_matcher_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M85_DIR = EXP_ROOT / "artifacts" / "E005-M85_prompt_label_recall_audit_v0"
VERSION = "e005_m86_prompt_repair_preflight_visibility_matcher_v0"
BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
BROAD_LABELS = {"object", "furniture", "item", "thing"}
MATCH_THRESHOLD_M = 1.0
RELAXED_THRESHOLD_M = 1.5


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


def load_targets() -> dict[str, dict[str, Any]]:
    return {str(row["target_uid"]): row for row in read_jsonl(M68_DIR / "real_proposal_object_targets.jsonl")}


def load_query_exposure() -> dict[str, dict[str, Any]]:
    exposure: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"query_rows": 0, "task_context_counts": Counter(), "row_band_counts": Counter()}
    )
    for batch_id in BATCHES:
        for row in read_jsonl(M68_DIR / "batches" / batch_id / "direct_bridge_query_rows.jsonl"):
            target_uid = str(row.get("target_uid"))
            if not target_uid:
                continue
            exposure[target_uid]["query_rows"] += 1
            exposure[target_uid]["task_context_counts"][str(row.get("task_context_id"))] += 1
            exposure[target_uid]["row_band_counts"][str(row.get("row_band"))] += 1
    return {
        key: {
            "query_rows": int(value["query_rows"]),
            "task_context_counts": dict(sorted(value["task_context_counts"].items())),
            "row_band_counts": dict(sorted(value["row_band_counts"].items())),
        }
        for key, value in exposure.items()
    }


def load_real_proposals() -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    by_raw_uid: dict[str, dict[str, Any]] = {}
    by_scan_label: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for batch_id in BATCHES:
        for row in read_jsonl(M69_DIR / batch_id / "container_output" / "real_proposals.jsonl"):
            raw_uid = row.get("raw_candidate_uid")
            if raw_uid:
                by_raw_uid[str(raw_uid)] = row
            key = (str(row.get("scan_id")), str(row.get("label_canonical")))
            by_scan_label[key].append(row)
    return by_raw_uid, dict(by_scan_label)


def load_frame_summary() -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "raw_prediction_count": 0,
            "projected_candidate_count": 0,
            "policy_selected_prediction_count": 0,
            "written_prediction_count": 0,
            "sampled_frame_count": 0,
        }
    )
    for batch_id in BATCHES:
        for row in read_jsonl(M69_DIR / batch_id / "frame_diagnostics.jsonl"):
            scan_id = str(row.get("scan_id"))
            summary[scan_id]["raw_prediction_count"] += int(row.get("raw_prediction_count") or 0)
            summary[scan_id]["projected_candidate_count"] += int(row.get("projected_candidate_count") or 0)
            summary[scan_id]["policy_selected_prediction_count"] += int(row.get("policy_selected_prediction_count") or 0)
            summary[scan_id]["written_prediction_count"] += int(row.get("written_prediction_count") or 0)
            summary[scan_id]["sampled_frame_count"] += 1
    return dict(summary)


def nearest_selected_same_label(
    selected_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
    scan_id: str,
    label: str,
    centroid: list[float],
) -> dict[str, Any]:
    rows = [row for row in selected_by_scan_label.get((scan_id, label), []) if row.get("centroid_world_m")]
    if not rows:
        return {
            "nearest_selected_same_label_distance_m": None,
            "nearest_selected_same_label_uid": None,
            "nearest_selected_same_label_rank": None,
            "nearest_selected_same_label_match_status": None,
            "selected_same_label_candidate_count": 0,
        }
    ranked = sorted(rows, key=lambda row: distance(row["centroid_world_m"], centroid))
    nearest = ranked[0]
    return {
        "nearest_selected_same_label_distance_m": round(distance(nearest["centroid_world_m"], centroid), 6),
        "nearest_selected_same_label_uid": nearest.get("proposal_uid"),
        "nearest_selected_same_label_rank": nearest.get("pre_cap_rank"),
        "nearest_selected_same_label_match_status": nearest.get("match_status"),
        "selected_same_label_candidate_count": len(rows),
    }


def select_recommended_action(row: dict[str, Any]) -> str:
    audit_class = str(row["audit_class"])
    label = str(row["label_canonical"])
    nearest_pre_cap = row.get("nearest_pre_cap_same_label_distance_m")
    nearest_selected = row.get("nearest_selected_same_label_distance_m")
    survived = bool(row["nearest_pre_cap_survived_selection"])
    selected_count = int(row["selected_same_label_candidate_count"])
    written_count = int(row["scan_written_prediction_count"])
    projected_count = int(row["scan_projected_candidate_count"])

    if label in BROAD_LABELS or audit_class == "prompt_contract_gap_broad_or_missing_label":
        return "denominator_or_prompt_contract_decision_before_detector_repair"
    if audit_class == "detector_or_label_parse_no_same_label_candidates":
        if written_count == 0 and projected_count > 0:
            return "scan_level_policy_filter_or_label_parse_audit_before_prompt_rerun"
        return "bounded_prompt_alias_preflight_only_after_nonleaky_alias_rule"
    if nearest_pre_cap is not None and nearest_pre_cap <= MATCH_THRESHOLD_M and not survived:
        return "candidate_survival_audit_before_matcher_or_prompt_change"
    if nearest_pre_cap is not None and nearest_pre_cap <= MATCH_THRESHOLD_M and survived:
        return "matcher_assignment_audit_before_prompt_change"
    if nearest_selected is not None and nearest_selected <= RELAXED_THRESHOLD_M:
        return "match_threshold_geometry_calibration_audit_before_prompt_change"
    if nearest_pre_cap is not None and nearest_pre_cap <= RELAXED_THRESHOLD_M:
        return "candidate_survival_then_relaxed_threshold_audit_before_prompt_change"
    if selected_count > 0:
        return "visibility_or_geometry_offset_audit_before_prompt_change"
    return "prompt_repair_not_supported_without_detector_or_visibility_evidence"


def build_rows() -> list[dict[str, Any]]:
    targets = load_targets()
    exposure = load_query_exposure()
    selected_by_raw, selected_by_scan_label = load_real_proposals()
    frame_summary = load_frame_summary()
    audit_rows = read_jsonl(M85_DIR / "recall_miss_audit_rows.jsonl")
    out_rows: list[dict[str, Any]] = []
    for row in audit_rows:
        target_uid = str(row["target_uid"])
        scan_id = str(row["scan_id"])
        label = str(row["label_canonical"])
        target = targets.get(target_uid, {})
        centroid = target.get("centroid_world_m") or []
        nearest_raw_uid = row.get("nearest_pre_cap_same_label_uid")
        nearest_survived = bool(nearest_raw_uid and str(nearest_raw_uid) in selected_by_raw)
        selected_nearest = (
            nearest_selected_same_label(selected_by_scan_label, scan_id, label, centroid)
            if centroid
            else {
                "nearest_selected_same_label_distance_m": None,
                "nearest_selected_same_label_uid": None,
                "nearest_selected_same_label_rank": None,
                "nearest_selected_same_label_match_status": None,
                "selected_same_label_candidate_count": 0,
            }
        )
        query_info = exposure.get(target_uid, {"query_rows": 0, "task_context_counts": {}, "row_band_counts": {}})
        frame_info = frame_summary.get(scan_id, {})
        out = {
            "audit_class": row.get("audit_class"),
            "batch_id": row.get("batch_id"),
            "label_canonical": label,
            "nearest_pre_cap_same_label_distance_m": row.get("nearest_pre_cap_same_label_distance_m"),
            "nearest_pre_cap_same_label_uid": nearest_raw_uid,
            "nearest_pre_cap_survived_selection": nearest_survived,
            "offline_diagnosis_only": True,
            "prompt_in_batch": bool(row.get("label_in_batch_prompt_set")),
            "query_exposure_rows": int(query_info.get("query_rows") or 0),
            "record_type": "e005_m86_prompt_repair_preflight_visibility_matcher",
            "scan_id": scan_id,
            "scan_policy_selected_prediction_count": int(frame_info.get("policy_selected_prediction_count", 0)),
            "scan_projected_candidate_count": int(frame_info.get("projected_candidate_count", 0)),
            "scan_raw_prediction_count": int(frame_info.get("raw_prediction_count", 0)),
            "scan_written_prediction_count": int(frame_info.get("written_prediction_count", 0)),
            "target_uid": target_uid,
            "task_context_counts": query_info.get("task_context_counts", {}),
            "row_band_counts": query_info.get("row_band_counts", {}),
        }
        out.update(selected_nearest)
        out["recommended_next_action"] = select_recommended_action(out)
        out_rows.append(out)
    return out_rows


def build_contract(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_for_offline_audit": [
            "target_uid",
            "target centroid",
            "pre-cap candidate centroid",
            "selected proposal centroid",
            "query success/failure rows",
        ],
        "allowed_for_repair_policy_or_detector_rerun": [
            "scan_id",
            "label_canonical",
            "prompt labels and aliases fixed before detector run",
            "RGB-D sequence frames and camera poses",
            "pre-cap candidate confidence/depth/centroid fields not joined to target identity",
            "target-independent label normalization rules",
        ],
        "blocked_for_repair_policy_or_detector_rerun": [
            "target_uid",
            "object_instance_id",
            "matched_3dssg_instance_id",
            "nearest target distance",
            "candidate-is-target labels",
            "query success/failure labels",
        ],
        "decision": {
            "bounded_prompt_repair_preflight_ready": coverage["bounded_prompt_repair_preflight_ready"],
            "launch_detector_rerun_now": False,
            "selected_next_route": coverage["selected_next_route"],
            "visibility_matcher_audit_first": coverage["visibility_matcher_audit_first"],
        },
        "next_unit_scope": [
            "candidate survival for near-threshold pre-cap rows",
            "selected-vs-pre-cap suppression for commode/chair/door/stool misses",
            "match-threshold sensitivity at 1.0m vs 1.5m",
            "zero-written scan diagnosis for the 569d8f0f chair cluster",
        ],
        "version": VERSION,
    }


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    action_lines = ["| Recommended action | Targets | Query rows |", "| --- | ---: | ---: |"]
    action_counts: Counter[str] = Counter(str(row["recommended_next_action"]) for row in rows)
    action_query_rows: Counter[str] = Counter()
    for row in rows:
        action_query_rows[str(row["recommended_next_action"])] += int(row["query_exposure_rows"])
    for action, count in action_counts.most_common():
        action_lines.append(f"| `{action}` | {count} | {action_query_rows[action]} |")

    target_lines = [
        "| Target | Label | Class | Query rows | Pre-cap dist | Selected dist | Survived | Action |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        pre_cap_dist = row["nearest_pre_cap_same_label_distance_m"]
        selected_dist = row["nearest_selected_same_label_distance_m"]
        target_lines.append(
            "| `{target}` | `{label}` | `{klass}` | {query_rows} | {pre} | {selected} | {survived} | `{action}` |".format(
                target=row["target_uid"],
                label=row["label_canonical"],
                klass=row["audit_class"],
                query_rows=row["query_exposure_rows"],
                pre="-" if pre_cap_dist is None else f"{pre_cap_dist:.3f}",
                selected="-" if selected_dist is None else f"{selected_dist:.3f}",
                survived=str(bool(row["nearest_pre_cap_survived_selection"])).lower(),
                action=row["recommended_next_action"],
            )
        )

    return "\n".join(
        [
            "# E005-M86 Prompt Repair Preflight / Visibility-Matcher Decision",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Selected route: `{coverage['selected_next_route']}`.",
            f"- Audited targets: {coverage['audited_targets']}.",
            f"- Query exposure rows: {coverage['query_exposure_rows']} / {coverage['query_rows']} total rows.",
            f"- Visibility/matcher audit targets: {coverage['visibility_matcher_audit_targets']} ({coverage['visibility_matcher_query_exposure_rows']} query rows).",
            f"- Zero-written scan targets: {coverage['zero_written_scan_targets']} ({coverage['zero_written_scan_query_exposure_rows']} query rows).",
            f"- Broad-label contract targets: {coverage['broad_label_contract_targets']} ({coverage['broad_label_contract_query_exposure_rows']} query rows).",
            f"- Bounded prompt repair preflight ready: {str(coverage['bounded_prompt_repair_preflight_ready']).lower()}.",
            f"- Launch detector rerun now: false.",
            "",
            "## Recommended Action Counts",
            "",
            *action_lines,
            "",
            "## Target-Level Audit",
            "",
            *target_lines,
            "",
            "## Claim Boundary",
            "",
            "- E005-M86 is a decision artifact, not a detector rerun.",
            "- It does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
            "- Prompt repair is not claim-ready because most recall misses are either near-threshold/candidate-survival issues or one scan-level zero-written case, not a clean synonym gap.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    m75 = read_json(M75_DIR / "coverage.json")
    action_counts: Counter[str] = Counter(str(row["recommended_next_action"]) for row in rows)
    action_query_rows: Counter[str] = Counter()
    for row in rows:
        action_query_rows[str(row["recommended_next_action"])] += int(row["query_exposure_rows"])

    visibility_actions = {
        "candidate_survival_audit_before_matcher_or_prompt_change",
        "matcher_assignment_audit_before_prompt_change",
        "match_threshold_geometry_calibration_audit_before_prompt_change",
        "candidate_survival_then_relaxed_threshold_audit_before_prompt_change",
        "visibility_or_geometry_offset_audit_before_prompt_change",
    }
    zero_written_action = "scan_level_policy_filter_or_label_parse_audit_before_prompt_rerun"
    broad_action = "denominator_or_prompt_contract_decision_before_detector_repair"
    prompt_ready_action = "bounded_prompt_alias_preflight_only_after_nonleaky_alias_rule"

    visibility_rows = [row for row in rows if row["recommended_next_action"] in visibility_actions]
    zero_written_rows = [row for row in rows if row["recommended_next_action"] == zero_written_action]
    broad_rows = [row for row in rows if row["recommended_next_action"] == broad_action]
    prompt_ready_rows = [row for row in rows if row["recommended_next_action"] == prompt_ready_action]
    relaxed_rows = [
        row
        for row in rows
        if row["nearest_pre_cap_same_label_distance_m"] is not None
        and float(row["nearest_pre_cap_same_label_distance_m"]) <= RELAXED_THRESHOLD_M
    ]
    survived_rows = [row for row in rows if row["nearest_pre_cap_survived_selection"]]
    selected_route = "candidate_survival_match_threshold_and_zero_written_scan_audit_before_prompt_rerun"
    coverage = {
        "audited_targets": len(rows),
        "bounded_prompt_repair_preflight_ready": bool(prompt_ready_rows) and not visibility_rows,
        "broad_label_contract_query_exposure_rows": sum(int(row["query_exposure_rows"]) for row in broad_rows),
        "broad_label_contract_targets": len(broad_rows),
        "deployable_search_policy_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "launch_detector_rerun_now": False,
        "nearest_pre_cap_survived_selection_targets": len(survived_rows),
        "next_recommended_unit": "E005-M87 candidate-survival / match-threshold / zero-written scan audit",
        "prompt_alias_preflight_candidate_targets": len(prompt_ready_rows),
        "query_rows": int(m75.get("query_rows", 195)),
        "query_exposure_rows": sum(int(row["query_exposure_rows"]) for row in rows),
        "real_navigation_sr_spl_claim_ready": False,
        "relaxed_1p5_pre_cap_candidate_targets": len(relaxed_rows),
        "selected_next_route": selected_route,
        "status": "e005_m86_prompt_repair_preflight_visibility_matcher_decision_ready",
        "visibility_matcher_audit_first": True,
        "visibility_matcher_audit_targets": len(visibility_rows),
        "visibility_matcher_query_exposure_rows": sum(int(row["query_exposure_rows"]) for row in visibility_rows),
        "zero_written_scan_query_exposure_rows": sum(int(row["query_exposure_rows"]) for row in zero_written_rows),
        "zero_written_scan_targets": len(zero_written_rows),
        "recommended_action_counts": dict(action_counts.most_common()),
        "recommended_action_query_rows": dict(action_query_rows.most_common()),
        "version": VERSION,
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision_contract.json", build_contract(coverage))
    write_jsonl(OUT_DIR / "audit_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
