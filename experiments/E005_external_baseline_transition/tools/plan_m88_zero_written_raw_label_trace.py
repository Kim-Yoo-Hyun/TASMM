#!/usr/bin/env python3
"""Audit the zero-written scan path before a detector or prompt rerun."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
RUNNER_SOURCE = ROOT / "experiments" / "E003_perception_noise_expansion" / "docker" / "real_proposals" / "run_rgbd_ov_proposals.py"
M68_BATCH_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0" / "batches" / "heldout_b02"
M69_BATCH_DIR = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0" / "heldout_b02"
M80_BATCH_DIR = EXP_ROOT / "artifacts" / "E005-M80_confidence_log_depth_detector_run_v0" / "heldout_b02"
M87_DIR = EXP_ROOT / "artifacts" / "E005-M87_candidate_survival_threshold_zero_written_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M88_zero_written_raw_label_trace_v0"
VERSION = "e005_m88_zero_written_raw_label_trace_v0"
ZERO_WRITTEN_SCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"
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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> list[str]:
    labels = []
    for row in prompt_payload.get("labels", []):
        if row.get("detector_prompt_enabled", True):
            labels.append(str(row["label_canonical"]))
    return labels


def select_scan_labels(manifest_row: dict[str, Any], prompt_payload: dict[str, Any], max_labels: int) -> list[str]:
    enabled = set(detector_prompt_labels(prompt_payload))
    target_labels = [str(label) for label in manifest_row.get("target_labels", []) if str(label) in enabled]
    ordered = [label for label in PRIORITY_LABELS if label in target_labels]
    ordered.extend(label for label in target_labels if label not in ordered)
    if not ordered:
        ordered = sorted(enabled)
    return ordered[:max_labels]


def frame_summary(path: Path, scan_id: str) -> dict[str, Any]:
    rows = [row for row in read_jsonl(path) if str(row.get("scan_id")) == scan_id]
    label_counts = Counter(str(row.get("label_count")) for row in rows)
    return {
        "frames": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "policy_selected_prediction_count": sum(int(row.get("policy_selected_prediction_count") or 0) for row in rows),
        "projected_candidate_count": sum(int(row.get("projected_candidate_count") or 0) for row in rows),
        "raw_prediction_count": sum(int(row.get("raw_prediction_count") or 0) for row in rows),
        "skipped_no_depth_prediction_count": sum(int(row.get("skipped_no_depth_prediction_count") or 0) for row in rows),
        "written_prediction_count": sum(int(row.get("written_prediction_count") or 0) for row in rows),
        "zero_written_frames": sum(1 for row in rows if int(row.get("written_prediction_count") or 0) == 0),
    }


def count_jsonl_by_scan(path: Path, scan_id: str) -> int:
    return sum(1 for row in read_jsonl(path) if str(row.get("scan_id")) == scan_id)


def count_jsonl_by_scan_label(path: Path) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in read_jsonl(path):
        counts[(str(row.get("scan_id")), str(row.get("label_canonical")))] += 1
    return [
        {"label_canonical": label, "row_count": count, "scan_id": scan_id}
        for (scan_id, label), count in sorted(counts.items())
    ]


def line_number(pattern: str) -> int | None:
    if not RUNNER_SOURCE.exists():
        return None
    for index, line in enumerate(RUNNER_SOURCE.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern in line:
            return index
    return None


def source_stage_audit() -> list[dict[str, Any]]:
    return [
        {
            "line": line_number("raw_prediction_count += len(result[\"scores\"])"),
            "stage": "raw_detector_predictions_counted",
            "why_it_matters": "M69/M80 raw counts are recorded before projection and cleanup.",
        },
        {
            "line": line_number("label_canonical = resolve_canonical_label(label_text, prompt_map, labels)"),
            "stage": "raw_label_text_resolved_to_canonical_label",
            "why_it_matters": "A wrong canonical label here can make projected candidates fail prompt-label cleanup.",
        },
        {
            "line": line_number("raw_candidates.append(base_row)"),
            "stage": "projected_candidate_added_to_raw_candidates",
            "why_it_matters": "M69/M80 projected counts imply rows reached this list.",
        },
        {
            "line": line_number("if label not in enabled_labels:"),
            "stage": "drop_non_prompt_label",
            "why_it_matters": "Rows can disappear before the pre-cap pool if canonical labels are outside the prompt set.",
        },
        {
            "line": line_number("if require_scan_prompt_label and label not in active_scan_labels.get(scan_id, set()):"),
            "stage": "drop_not_scan_prompt_label",
            "why_it_matters": "Rows can disappear before the pre-cap pool if canonical labels are not active for that scan.",
        },
        {
            "line": line_number("candidate_pool_stage = ("),
            "stage": "pre_cap_pool_stage_after_cleanup",
            "why_it_matters": "The exported pre-cap pool is already post-cleanup, so a zero pool localizes the loss before ranking/caps.",
        },
        {
            "line": line_number("write_jsonl(pre_cap_candidate_pool_output, pre_cap_candidate_pool_rows)"),
            "stage": "pre_cap_pool_written",
            "why_it_matters": "Existing pre-cap artifacts cannot show rows dropped before this write.",
        },
        {
            "line": line_number("item[\"written_prediction_count\"] = frame_selected_counts.get(key, 0)"),
            "stage": "frame_written_counts_updated_after_selection",
            "why_it_matters": "Frame diagnostics show final selected/written counts, not cleanup-drop reasons.",
        },
    ]


def command_plan_flags() -> dict[str, Any]:
    plan = read_json(M68_BATCH_DIR / "detector_run_command_plan.json")
    exact = [str(item) for item in plan.get("exact_command", [])]
    flags: dict[str, Any] = {}
    for index, token in enumerate(exact):
        if token.startswith("--"):
            next_value = exact[index + 1] if index + 1 < len(exact) and not exact[index + 1].startswith("--") else True
            flags[token] = next_value
    return {
        "batch_id": plan.get("batch_id"),
        "flags": flags,
        "shell_command": plan.get("shell_command"),
        "working_directory": plan.get("working_directory"),
    }


def prompt_entry(prompt_payload: dict[str, Any], label: str) -> dict[str, Any] | None:
    for row in prompt_payload.get("labels", []):
        if str(row.get("label_canonical")) == label:
            return row
    return None


def build_trace_rows() -> list[dict[str, Any]]:
    prompt_payload = read_json(M68_BATCH_DIR / "prompt_set.json")
    manifest_rows = read_jsonl(M68_BATCH_DIR / "real_proposal_query_manifest.jsonl")
    manifest_by_scan = {str(row.get("scan_id")): row for row in manifest_rows}
    zero_rows = read_jsonl(M87_DIR / "zero_written_rows.jsonl")
    direct_rows = [
        row
        for row in read_jsonl(M68_BATCH_DIR / "direct_bridge_query_rows.jsonl")
        if str(row.get("current_rescan_id")) == ZERO_WRITTEN_SCAN_ID
    ]
    object_targets = [
        row
        for row in read_jsonl(M68_BATCH_DIR / "real_proposal_object_targets.jsonl")
        if str(row.get("scan_id")) == ZERO_WRITTEN_SCAN_ID
    ]
    manifest_row = manifest_by_scan.get(ZERO_WRITTEN_SCAN_ID, {})
    enabled_labels = detector_prompt_labels(prompt_payload)
    active_scan_labels = select_scan_labels(
        manifest_row,
        prompt_payload,
        int(command_plan_flags()["flags"].get("--max-labels", 9)),
    )
    m69_frame = frame_summary(M69_BATCH_DIR / "frame_diagnostics.jsonl", ZERO_WRITTEN_SCAN_ID)
    m80_frame = frame_summary(M80_BATCH_DIR / "frame_diagnostics.jsonl", ZERO_WRITTEN_SCAN_ID)
    m69_pre_cap_count = count_jsonl_by_scan(
        M69_BATCH_DIR / "container_output" / "pre_cap_candidate_pool.jsonl", ZERO_WRITTEN_SCAN_ID
    )
    m80_pre_cap_count = count_jsonl_by_scan(
        M80_BATCH_DIR / "container_output" / "pre_cap_candidate_pool.jsonl", ZERO_WRITTEN_SCAN_ID
    )
    m69_written_count = count_jsonl_by_scan(
        M69_BATCH_DIR / "container_output" / "real_proposals.jsonl", ZERO_WRITTEN_SCAN_ID
    )
    m80_written_count = count_jsonl_by_scan(
        M80_BATCH_DIR / "container_output" / "real_proposals.jsonl", ZERO_WRITTEN_SCAN_ID
    )
    return [
        {
            "active_scan_labels_reconstructed": active_scan_labels,
            "batch_id": "heldout_b02",
            "direct_query_rows": len(direct_rows),
            "enabled_prompt_label_count": len(enabled_labels),
            "enabled_prompt_labels": enabled_labels,
            "existing_artifact_has_raw_label_text_distribution": False,
            "existing_artifact_has_cleanup_drop_reason_by_scan": False,
            "label_canonical": "chair",
            "m69_pre_cap_rows_for_scan": m69_pre_cap_count,
            "m69_real_proposal_rows_for_scan": m69_written_count,
            "m69_scan_frame_summary": m69_frame,
            "m80_pre_cap_rows_for_scan": m80_pre_cap_count,
            "m80_real_proposal_rows_for_scan": m80_written_count,
            "m80_scan_frame_summary": m80_frame,
            "manifest_target_labels": manifest_row.get("target_labels", []),
            "object_targets": len(object_targets),
            "prompt_entry_for_chair": prompt_entry(prompt_payload, "chair"),
            "scan_id": ZERO_WRITTEN_SCAN_ID,
            "target_uids": sorted({str(row.get("target_uid")) for row in zero_rows}),
            "zero_written_rows": len(zero_rows),
        }
    ]


def build_trace_contract(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_for_instrumentation": [
            "scan_id",
            "frame_id",
            "raw detector label_text",
            "resolved label_canonical",
            "active scan labels",
            "enabled prompt labels",
            "projection status",
            "cleanup drop reason",
            "per-scan/per-frame/per-label counts",
        ],
        "blocked_for_instrumentation_or_repair_policy": [
            "target_uid",
            "candidate_is_target",
            "matched target id",
            "nearest target distance",
            "query success/failure label",
        ],
        "minimal_runner_patch": {
            "add_flag": "--export-cleanup-trace",
            "add_output": "cleanup_trace.jsonl or cleanup_trace_summary.json",
            "fields": [
                "scan_id",
                "frame_id",
                "stage",
                "label_text_normalized_count",
                "label_canonical_count",
                "drop_reason_count",
                "active_scan_labels",
            ],
            "targeted_rerun_scope": "heldout_b02 scan 569d8f0f if runner supports scan filtering; otherwise heldout_b02 with trace enabled",
        },
        "decision": {
            "detector_rerun_now": False,
            "prompt_repair_now": False,
            "threshold_relaxation_now": False,
            "next_recommended_unit": coverage["next_recommended_unit"],
        },
        "version": VERSION,
    }


def build_report(coverage: dict[str, Any], trace_row: dict[str, Any], source_rows: list[dict[str, Any]]) -> str:
    source_lines = ["| Stage | Runner line | Interpretation |", "| --- | ---: | --- |"]
    for row in source_rows:
        source_lines.append(
            f"| `{row['stage']}` | {row['line'] or '-'} | {row['why_it_matters']} |"
        )

    return "\n".join(
        [
            "# E005-M88 Zero-Written Raw-Label Trace Audit",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Scan: `{coverage['scan_id']}`.",
            f"- Zero-written targets: {coverage['zero_written_targets']} targets / {coverage['zero_written_query_rows']} query rows.",
            f"- M69 raw/projected/written: {coverage['m69_raw_prediction_count']} / {coverage['m69_projected_candidate_count']} / {coverage['m69_written_prediction_count']}.",
            f"- M80 raw/projected/written: {coverage['m80_raw_prediction_count']} / {coverage['m80_projected_candidate_count']} / {coverage['m80_written_prediction_count']}.",
            f"- M69/M80 pre-cap rows for this scan: {coverage['m69_pre_cap_rows_for_scan']} / {coverage['m80_pre_cap_rows_for_scan']}.",
            f"- Reconstructed active scan labels: `{', '.join(trace_row['active_scan_labels_reconstructed'])}`.",
            f"- Prompt has `chair`: {str(coverage['prompt_has_chair']).lower()}.",
            f"- Existing artifact has raw-label text distribution: {str(coverage['raw_label_trace_available']).lower()}.",
            "",
            "## Source Localization",
            "",
            *source_lines,
            "",
            "## Agent Inference",
            "",
            "- The loss is after successful RGB-D projection and before the exported pre-cap pool.",
            "- Because the pre-cap pool is exported after prompt-label cleanup, ranking, spatial consolidation, and per-scan-label caps cannot explain this zero-written scan.",
            "- Because M69 `confidence` and M80 `confidence_log_depth` have the same raw/projected/written counts, the failure is not caused by the score mode.",
            "- The current artifacts do not record raw label text or cleanup drop reasons per scan, so the exact label mismatch cannot be proven without one lightweight instrumentation rerun.",
            "",
            "## Claim Boundary",
            "",
            "- This is an instrumentation audit, not prompt repair, detector repair, or final real RGB-D/open-vocabulary robustness evidence.",
            "- Do not claim that `chair` prompt repair fixes the failure until cleanup-trace counts show the candidate labels are actually being dropped for a repairable label-normalization reason.",
            "- Do not relax the 1.5m threshold based on this scan; this scan has zero pre-cap rows.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trace_rows = build_trace_rows()
    trace_row = trace_rows[0]
    source_rows = source_stage_audit()
    flags = command_plan_flags()
    m69_summary = read_json(M69_BATCH_DIR / "container_output" / "pre_cap_policy_summary.json")
    m80_summary = read_json(M80_BATCH_DIR / "container_output" / "pre_cap_policy_summary.json")
    m69_frame = trace_row["m69_scan_frame_summary"]
    m80_frame = trace_row["m80_scan_frame_summary"]
    prompt_has_chair = "chair" in trace_row["enabled_prompt_labels"] and "chair" in trace_row["active_scan_labels_reconstructed"]
    m69_pre_cap_count = int(trace_row["m69_pre_cap_rows_for_scan"])
    m80_pre_cap_count = int(trace_row["m80_pre_cap_rows_for_scan"])
    coverage = {
        "active_scan_labels_reconstructed": trace_row["active_scan_labels_reconstructed"],
        "detector_rerun_now": False,
        "exact_filter_reason_known": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "global_m69_dropped_non_prompt_label_rows": int(m69_summary.get("dropped_non_prompt_label_rows") or 0),
        "global_m69_dropped_not_scan_prompt_label_rows": int(m69_summary.get("dropped_not_scan_prompt_label_rows") or 0),
        "global_m80_dropped_non_prompt_label_rows": int(m80_summary.get("dropped_non_prompt_label_rows") or 0),
        "global_m80_dropped_not_scan_prompt_label_rows": int(m80_summary.get("dropped_not_scan_prompt_label_rows") or 0),
        "likely_loss_stage": "prompt_label_cleanup_before_spatial_consolidation_and_caps",
        "m69_pre_cap_rows_for_scan": m69_pre_cap_count,
        "m69_projected_candidate_count": int(m69_frame["projected_candidate_count"]),
        "m69_raw_prediction_count": int(m69_frame["raw_prediction_count"]),
        "m69_real_proposal_rows_for_scan": int(trace_row["m69_real_proposal_rows_for_scan"]),
        "m69_written_prediction_count": int(m69_frame["written_prediction_count"]),
        "m80_pre_cap_rows_for_scan": m80_pre_cap_count,
        "m80_projected_candidate_count": int(m80_frame["projected_candidate_count"]),
        "m80_raw_prediction_count": int(m80_frame["raw_prediction_count"]),
        "m80_real_proposal_rows_for_scan": int(trace_row["m80_real_proposal_rows_for_scan"]),
        "m80_written_prediction_count": int(m80_frame["written_prediction_count"]),
        "next_recommended_unit": "E005-M89 target-independent cleanup-trace runner patch / heldout_b02 trace rerun",
        "pre_cap_loss_rate_m69": safe_rate(
            int(m69_frame["projected_candidate_count"]) - m69_pre_cap_count,
            int(m69_frame["projected_candidate_count"]),
        ),
        "pre_cap_loss_rate_m80": safe_rate(
            int(m80_frame["projected_candidate_count"]) - m80_pre_cap_count,
            int(m80_frame["projected_candidate_count"]),
        ),
        "prompt_has_chair": prompt_has_chair,
        "prompt_repair_now": False,
        "raw_label_trace_available": False,
        "runner_flags": flags,
        "runner_patch_required_for_exact_reason": True,
        "scan_id": ZERO_WRITTEN_SCAN_ID,
        "score_mode_explains_failure": False,
        "source_stage_count": len(source_rows),
        "status": "e005_m88_zero_written_raw_label_trace_audit_ready_trace_missing",
        "threshold_relaxation_now": False,
        "version": VERSION,
        "zero_written_query_rows": sum(int(row.get("query_exposure_rows") or 0) for row in read_jsonl(M87_DIR / "zero_written_rows.jsonl")),
        "zero_written_targets": len(read_jsonl(M87_DIR / "zero_written_rows.jsonl")),
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "trace_rows.jsonl", trace_rows)
    write_jsonl(OUT_DIR / "source_stage_audit.jsonl", source_rows)
    write_jsonl(OUT_DIR / "m69_pre_cap_scan_label_counts.jsonl", count_jsonl_by_scan_label(M69_BATCH_DIR / "container_output" / "pre_cap_candidate_pool.jsonl"))
    write_jsonl(OUT_DIR / "m80_pre_cap_scan_label_counts.jsonl", count_jsonl_by_scan_label(M80_BATCH_DIR / "container_output" / "pre_cap_candidate_pool.jsonl"))
    write_json(OUT_DIR / "trace_contract.json", build_trace_contract(coverage))
    write_text(OUT_DIR / "report.md", build_report(coverage, trace_row, source_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
