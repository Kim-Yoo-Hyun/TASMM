#!/usr/bin/env python3
"""Audit candidate survival, match thresholds, and zero-written scans after M86."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M87_candidate_survival_threshold_zero_written_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
M80_DIR = EXP_ROOT / "artifacts" / "E005-M80_confidence_log_depth_detector_run_v0"
M86_DIR = EXP_ROOT / "artifacts" / "E005-M86_prompt_repair_preflight_visibility_matcher_v0"
VERSION = "e005_m87_candidate_survival_threshold_zero_written_v0"
BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
STRICT_THRESHOLD_M = 1.0
RELAXED_THRESHOLD_M = 1.5
LOOSE_DIAGNOSTIC_THRESHOLD_M = 2.0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def load_targets_by_scan_label() -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(M68_DIR / "real_proposal_object_targets.jsonl"):
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(row)
    return dict(grouped)


def load_proposal_indices(root: Path) -> dict[str, dict[str, Any]]:
    by_proposal_uid: dict[str, dict[str, Any]] = {}
    by_raw_uid: dict[str, dict[str, Any]] = {}
    for batch_id in BATCHES:
        for row in read_jsonl(root / batch_id / "matching" / "matched_proposals.jsonl"):
            if row.get("proposal_uid"):
                by_proposal_uid[str(row["proposal_uid"])] = row
            if row.get("raw_candidate_uid"):
                by_raw_uid[str(row["raw_candidate_uid"])] = row
    return {"proposal": by_proposal_uid, "raw": by_raw_uid}


def load_pre_cap_by_uid() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for batch_id in BATCHES:
        for row in read_jsonl(M69_DIR / batch_id / "container_output" / "pre_cap_candidate_pool.jsonl"):
            uid = row.get("pre_cap_candidate_pool_uid") or row.get("raw_candidate_uid")
            if uid:
                rows[str(uid)] = row
    return rows


def load_target_recall_by_uid(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for batch_id in BATCHES:
        for row in read_jsonl(root / batch_id / "matching" / "target_recall_rows.jsonl"):
            if row.get("target_uid"):
                rows[str(row["target_uid"])] = row
    return rows


def load_scan_frame_summary(root: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "frames": 0,
            "raw_prediction_count": 0,
            "projected_candidate_count": 0,
            "policy_selected_prediction_count": 0,
            "written_prediction_count": 0,
            "label_counts": Counter(),
            "zero_written_frames": 0,
        }
    )
    for batch_id in BATCHES:
        for row in read_jsonl(root / batch_id / "frame_diagnostics.jsonl"):
            scan_id = str(row.get("scan_id"))
            out[scan_id]["frames"] += 1
            out[scan_id]["raw_prediction_count"] += int(row.get("raw_prediction_count") or 0)
            out[scan_id]["projected_candidate_count"] += int(row.get("projected_candidate_count") or 0)
            out[scan_id]["policy_selected_prediction_count"] += int(row.get("policy_selected_prediction_count") or 0)
            out[scan_id]["written_prediction_count"] += int(row.get("written_prediction_count") or 0)
            out[scan_id]["label_counts"][str(row.get("label_count"))] += 1
            if int(row.get("written_prediction_count") or 0) == 0:
                out[scan_id]["zero_written_frames"] += 1

    normalized: dict[str, dict[str, Any]] = {}
    for scan_id, row in out.items():
        normalized[scan_id] = dict(row)
        normalized[scan_id]["label_counts"] = dict(sorted(row["label_counts"].items()))
    return normalized


def pre_cap_pool_count_by_scan(root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for batch_id in BATCHES:
        for row in read_jsonl(root / batch_id / "container_output" / "pre_cap_candidate_pool.jsonl"):
            counts[str(row.get("scan_id"))] += 1
    return dict(counts)


def nearest_target_for_candidate(
    candidate: dict[str, Any] | None,
    targets_by_scan_label: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    if not candidate or not candidate.get("centroid_world_m"):
        return {
            "candidate_nearest_distance_m": None,
            "candidate_nearest_target_uid": None,
            "candidate_nearest_target_instance_id": None,
        }
    targets = targets_by_scan_label.get((str(candidate.get("scan_id")), str(candidate.get("label_canonical"))), [])
    nearest = None
    nearest_distance = None
    for target in targets:
        dist = distance(candidate["centroid_world_m"], target["centroid_world_m"])
        if nearest_distance is None or dist < nearest_distance:
            nearest_distance = dist
            nearest = target
    return {
        "candidate_nearest_distance_m": round(nearest_distance, 6) if nearest_distance is not None else None,
        "candidate_nearest_target_uid": nearest.get("target_uid") if nearest else None,
        "candidate_nearest_target_instance_id": nearest.get("object_instance_id") if nearest else None,
    }


def threshold_recoverable(nearest_target_uid: str | None, distance_m: float | None, target_uid: str, threshold: float) -> bool:
    return nearest_target_uid == target_uid and distance_m is not None and float(distance_m) <= threshold


def classify_row(row: dict[str, Any]) -> str:
    if row["audit_class"] == "prompt_contract_gap_broad_or_missing_label":
        return "broad_label_denominator_contract"
    if row["zero_written_scan_issue"]:
        return "zero_written_scan_requires_raw_label_trace"
    if row["strict_pre_cap_recoverable_but_suppressed"]:
        return "pre_cap_strict_candidate_suppressed_by_selection_policy"
    if row["selected_instance_ambiguity"] or row["pre_cap_instance_ambiguity"]:
        return "same_label_instance_ambiguity_not_prompt_repair"
    if row["selected_relaxed_1p5_recoverable"]:
        return "selected_candidate_recoverable_by_1p5_threshold_calibration"
    if row["pre_cap_relaxed_1p5_recoverable"]:
        return "pre_cap_candidate_needs_selection_plus_1p5_threshold_calibration"
    if row["selected_loose_2p0_recoverable"] or row["pre_cap_loose_2p0_recoverable"]:
        return "only_loose_2p0_diagnostic_not_claim_ready"
    return "not_recoverable_from_existing_candidates"


def build_rows() -> list[dict[str, Any]]:
    targets_by_scan_label = load_targets_by_scan_label()
    pre_cap_by_uid = load_pre_cap_by_uid()
    m69_indices = load_proposal_indices(M69_DIR)
    m80_indices = load_proposal_indices(M80_DIR)
    m69_recall = load_target_recall_by_uid(M69_DIR)
    m80_recall = load_target_recall_by_uid(M80_DIR)
    m69_frames = load_scan_frame_summary(M69_DIR)
    m80_frames = load_scan_frame_summary(M80_DIR)
    m69_pre_cap_counts = pre_cap_pool_count_by_scan(M69_DIR)
    m80_pre_cap_counts = pre_cap_pool_count_by_scan(M80_DIR)

    rows: list[dict[str, Any]] = []
    for base in read_jsonl(M86_DIR / "audit_rows.jsonl"):
        target_uid = str(base["target_uid"])
        scan_id = str(base["scan_id"])
        label = str(base["label_canonical"])
        pre_cap_uid = base.get("nearest_pre_cap_same_label_uid")
        selected_uid = base.get("nearest_selected_same_label_uid")
        pre_cap_candidate = pre_cap_by_uid.get(str(pre_cap_uid)) if pre_cap_uid else None
        selected_candidate = m69_indices["proposal"].get(str(selected_uid)) if selected_uid else None
        selected_raw_candidate = m69_indices["raw"].get(str(pre_cap_uid)) if pre_cap_uid else None
        pre_cap_nearest = nearest_target_for_candidate(pre_cap_candidate, targets_by_scan_label)
        selected_nearest = nearest_target_for_candidate(selected_candidate, targets_by_scan_label)

        selected_nearest_uid = selected_nearest["candidate_nearest_target_uid"]
        selected_distance = selected_nearest["candidate_nearest_distance_m"]
        pre_cap_nearest_uid = pre_cap_nearest["candidate_nearest_target_uid"]
        pre_cap_distance = pre_cap_nearest["candidate_nearest_distance_m"]

        m69_frame = m69_frames.get(scan_id, {})
        m80_frame = m80_frames.get(scan_id, {})
        zero_written = (
            int(m69_frame.get("raw_prediction_count", 0)) > 0
            and int(m69_frame.get("projected_candidate_count", 0)) > 0
            and int(m69_frame.get("written_prediction_count", 0)) == 0
            and int(m69_pre_cap_counts.get(scan_id, 0)) == 0
        )
        m80_zero_written = (
            int(m80_frame.get("raw_prediction_count", 0)) > 0
            and int(m80_frame.get("projected_candidate_count", 0)) > 0
            and int(m80_frame.get("written_prediction_count", 0)) == 0
            and int(m80_pre_cap_counts.get(scan_id, 0)) == 0
        )

        out = {
            "audit_class": base.get("audit_class"),
            "batch_id": base.get("batch_id"),
            "label_canonical": label,
            "m69_current_matched": bool(m69_recall.get(target_uid, {}).get("matched")),
            "m69_pre_cap_pool_count_for_scan": int(m69_pre_cap_counts.get(scan_id, 0)),
            "m69_scan_frame_summary": m69_frame,
            "m80_confidence_log_depth_matched": bool(m80_recall.get(target_uid, {}).get("matched")),
            "m80_pre_cap_pool_count_for_scan": int(m80_pre_cap_counts.get(scan_id, 0)),
            "m80_scan_frame_summary": m80_frame,
            "m80_zero_written_persists": bool(m80_frame and m80_zero_written),
            "nearest_pre_cap_same_label_distance_m": base.get("nearest_pre_cap_same_label_distance_m"),
            "nearest_pre_cap_same_label_uid": pre_cap_uid,
            "nearest_pre_cap_survived_exact_selection": bool(selected_raw_candidate),
            "nearest_selected_same_label_distance_m": base.get("nearest_selected_same_label_distance_m"),
            "nearest_selected_same_label_uid": selected_uid,
            "pre_cap_candidate_found": pre_cap_candidate is not None,
            "pre_cap_candidate_nearest_distance_m": pre_cap_distance,
            "pre_cap_candidate_nearest_target_uid": pre_cap_nearest_uid,
            "pre_cap_instance_ambiguity": bool(pre_cap_nearest_uid and pre_cap_nearest_uid != target_uid),
            "pre_cap_loose_2p0_recoverable": threshold_recoverable(
                pre_cap_nearest_uid, pre_cap_distance, target_uid, LOOSE_DIAGNOSTIC_THRESHOLD_M
            ),
            "pre_cap_relaxed_1p5_recoverable": threshold_recoverable(
                pre_cap_nearest_uid, pre_cap_distance, target_uid, RELAXED_THRESHOLD_M
            ),
            "pre_cap_strict_1p0_recoverable": threshold_recoverable(
                pre_cap_nearest_uid, pre_cap_distance, target_uid, STRICT_THRESHOLD_M
            ),
            "query_exposure_rows": int(base.get("query_exposure_rows") or 0),
            "record_type": "e005_m87_candidate_survival_threshold_zero_written",
            "scan_id": scan_id,
            "selected_candidate_found": selected_candidate is not None,
            "selected_candidate_match_status": selected_candidate.get("match_status") if selected_candidate else None,
            "selected_candidate_matched_target_uid": selected_candidate.get("matched_target_uid") if selected_candidate else None,
            "selected_candidate_nearest_distance_m": selected_distance,
            "selected_candidate_nearest_target_uid": selected_nearest_uid,
            "selected_instance_ambiguity": bool(selected_nearest_uid and selected_nearest_uid != target_uid),
            "selected_loose_2p0_recoverable": threshold_recoverable(
                selected_nearest_uid, selected_distance, target_uid, LOOSE_DIAGNOSTIC_THRESHOLD_M
            ),
            "selected_relaxed_1p5_recoverable": threshold_recoverable(
                selected_nearest_uid, selected_distance, target_uid, RELAXED_THRESHOLD_M
            ),
            "selected_strict_1p0_recoverable": threshold_recoverable(
                selected_nearest_uid, selected_distance, target_uid, STRICT_THRESHOLD_M
            ),
            "target_uid": target_uid,
            "zero_written_scan_issue": zero_written,
        }
        out["strict_pre_cap_recoverable_but_suppressed"] = bool(
            out["pre_cap_strict_1p0_recoverable"] and not out["nearest_pre_cap_survived_exact_selection"]
        )
        out["m87_failure_class"] = classify_row(out)
        rows.append(out)
    return rows


def class_counts(rows: list[dict[str, Any]], key: str) -> tuple[dict[str, int], dict[str, int]]:
    target_counts: Counter[str] = Counter(str(row[key]) for row in rows)
    query_counts: Counter[str] = Counter()
    for row in rows:
        query_counts[str(row[key])] += int(row["query_exposure_rows"])
    return dict(target_counts.most_common()), dict(query_counts.most_common())


def build_contract(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_for_m87_audit": [
            "M86 recall-miss target uid and target centroid",
            "M69 pre-cap candidate pool",
            "M69 matched proposal nearest same-label target fields",
            "M69/M80 frame diagnostics and target recall rows",
        ],
        "blocked_for_detector_or_policy_repair": [
            "candidate-is-target label",
            "target uid",
            "nearest target distance",
            "query success/failure label",
        ],
        "decision": {
            "launch_detector_rerun_now": False,
            "bounded_prompt_repair_ready": False,
            "selected_next_route": coverage["selected_next_route"],
            "threshold_relaxation_claim_ready": coverage["threshold_relaxation_claim_ready"],
            "zero_written_trace_required": coverage["zero_written_trace_required"],
        },
        "next_unit_scope": [
            "instrument raw/post-label-filter candidate counts for the zero-written scan",
            "verify why raw/projected rows become zero pre-cap rows for `569d8f0f`",
            "keep 1.5m threshold recovery as diagnostic until false-positive inflation is measured",
        ],
        "version": VERSION,
    }


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    class_lines = ["| Failure class | Targets | Query rows |", "| --- | ---: | ---: |"]
    class_target_counts = coverage["failure_class_target_counts"]
    class_query_counts = coverage["failure_class_query_rows"]
    for key, value in class_target_counts.items():
        class_lines.append(f"| `{key}` | {value} | {class_query_counts.get(key, 0)} |")

    target_lines = [
        "| Target | Label | Query rows | Pre-cap nearest | Selected nearest | M87 class |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        pre_cap = row["pre_cap_candidate_nearest_distance_m"]
        selected = row["selected_candidate_nearest_distance_m"]
        target_lines.append(
            "| `{target}` | `{label}` | {query_rows} | {pre} | {selected} | `{klass}` |".format(
                target=row["target_uid"],
                label=row["label_canonical"],
                query_rows=row["query_exposure_rows"],
                pre="-" if pre_cap is None else f"{pre_cap:.3f}",
                selected="-" if selected is None else f"{selected:.3f}",
                klass=row["m87_failure_class"],
            )
        )

    return "\n".join(
        [
            "# E005-M87 Candidate Survival / Threshold / Zero-Written Audit",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Audited targets: {coverage['audited_targets']}.",
            f"- Query exposure rows: {coverage['query_exposure_rows']} / {coverage['query_rows']} total rows.",
            f"- Strict pre-cap candidate suppressed targets: {coverage['strict_pre_cap_recoverable_but_suppressed_targets']}.",
            f"- Selected candidate recoverable at 1.5m targets: {coverage['selected_relaxed_1p5_recoverable_targets']}.",
            f"- Pre-cap candidate recoverable at 1.5m targets: {coverage['pre_cap_relaxed_1p5_recoverable_targets']}.",
            f"- Instance-ambiguity targets: {coverage['instance_ambiguity_targets']}.",
            f"- Zero-written scan targets: {coverage['zero_written_scan_targets']}.",
            f"- Bounded prompt repair ready: {str(coverage['bounded_prompt_repair_ready']).lower()}.",
            f"- Launch detector rerun now: {str(coverage['launch_detector_rerun_now']).lower()}.",
            "",
            "## Failure Classes",
            "",
            *class_lines,
            "",
            "## Target-Level Audit",
            "",
            *target_lines,
            "",
            "## Interpretation",
            "",
            "- The largest remaining exposure is the `569d8f0f` zero-written scan cluster: raw/projected candidates exist, but no pre-cap rows or written rows survive.",
            "- Some missed targets have near-threshold candidates, but a 1.5m match threshold is diagnostic only until false-positive inflation is measured.",
            "- Same-label instance ambiguity appears for targets where the closest candidate belongs to a neighboring instance, so prompt repair is not the right first fix.",
            "",
            "## Claim Boundary",
            "",
            "- E005-M87 is an offline audit over existing artifacts, not a detector rerun or final robustness result.",
            "- It does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
            "- Prompt repair remains blocked because the dominant unresolved case is zero-written scan tracing, not a clean synonym/prompt gap.",
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
    failure_target_counts, failure_query_counts = class_counts(rows, "m87_failure_class")
    query_rows = 195
    query_exposure_rows = sum(int(row["query_exposure_rows"]) for row in rows)
    zero_written_rows = [row for row in rows if row["zero_written_scan_issue"]]
    instance_rows = [row for row in rows if row["selected_instance_ambiguity"] or row["pre_cap_instance_ambiguity"]]
    strict_suppressed_rows = [row for row in rows if row["strict_pre_cap_recoverable_but_suppressed"]]
    selected_relaxed_rows = [row for row in rows if row["selected_relaxed_1p5_recoverable"]]
    pre_cap_relaxed_rows = [row for row in rows if row["pre_cap_relaxed_1p5_recoverable"]]
    selected_route = "zero_written_raw_label_trace_before_prompt_or_threshold_repair"
    coverage = {
        "audited_targets": len(rows),
        "bounded_prompt_repair_ready": False,
        "deployable_search_policy_claim_ready": False,
        "failure_class_query_rows": failure_query_counts,
        "failure_class_target_counts": failure_target_counts,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "instance_ambiguity_query_rows": sum(int(row["query_exposure_rows"]) for row in instance_rows),
        "instance_ambiguity_targets": len(instance_rows),
        "launch_detector_rerun_now": False,
        "next_recommended_unit": "E005-M88 zero-written raw-label trace / post-filter instrumentation audit",
        "pre_cap_relaxed_1p5_recoverable_query_rows": sum(int(row["query_exposure_rows"]) for row in pre_cap_relaxed_rows),
        "pre_cap_relaxed_1p5_recoverable_targets": len(pre_cap_relaxed_rows),
        "query_exposure_rate": safe_rate(query_exposure_rows, query_rows),
        "query_exposure_rows": query_exposure_rows,
        "query_rows": query_rows,
        "real_navigation_sr_spl_claim_ready": False,
        "selected_next_route": selected_route,
        "selected_relaxed_1p5_recoverable_query_rows": sum(int(row["query_exposure_rows"]) for row in selected_relaxed_rows),
        "selected_relaxed_1p5_recoverable_targets": len(selected_relaxed_rows),
        "status": "e005_m87_candidate_survival_threshold_zero_written_audit_ready",
        "strict_pre_cap_recoverable_but_suppressed_query_rows": sum(
            int(row["query_exposure_rows"]) for row in strict_suppressed_rows
        ),
        "strict_pre_cap_recoverable_but_suppressed_targets": len(strict_suppressed_rows),
        "threshold_relaxation_claim_ready": False,
        "version": VERSION,
        "zero_written_scan_query_rows": sum(int(row["query_exposure_rows"]) for row in zero_written_rows),
        "zero_written_scan_targets": len(zero_written_rows),
        "zero_written_trace_required": bool(zero_written_rows),
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision_contract.json", build_contract(coverage))
    write_jsonl(OUT_DIR / "audit_rows.jsonl", rows)
    write_jsonl(OUT_DIR / "zero_written_rows.jsonl", zero_written_rows)
    write_jsonl(OUT_DIR / "threshold_candidate_rows.jsonl", selected_relaxed_rows + pre_cap_relaxed_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
