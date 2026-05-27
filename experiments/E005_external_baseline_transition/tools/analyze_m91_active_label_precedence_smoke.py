#!/usr/bin/env python3
"""Analyze E005-M91 active-label precedence cleanup smoke."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M89_RUN_DIR = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_run_v0" / "heldout_b02"
M90_DIR = EXP_ROOT / "artifacts" / "E005-M90_label_normalization_prompt_scope_repair_v0"
M91_RUN_DIR = EXP_ROOT / "artifacts" / "E005-M91_active_label_precedence_smoke_v0" / "heldout_b02"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M91_active_label_precedence_analysis_v0"
VERSION = "e005_m91_active_label_precedence_analysis_v0"
BLOCKED_FIELDS = {
    "target_uid",
    "candidate_is_target",
    "matched_3dssg_instance_id",
    "nearest_target_distance",
    "query_success_label",
}


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


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def cleanup_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(str(row.get("cleanup_decision")) for row in rows)
    drop_counts = Counter(str(row.get("drop_reason")) for row in rows if row.get("drop_reason") is not None)
    label_counts = Counter(str(row.get("label_canonical")) for row in rows)
    text_counts = Counter(str(row.get("label_text")) for row in rows)
    blocked_hits = [
        {"blocked_fields": sorted(field for field in BLOCKED_FIELDS if field in row), "row_index": idx}
        for idx, row in enumerate(rows, start=1)
        if any(field in row for field in BLOCKED_FIELDS)
    ]
    return {
        "blocked_field_hit_count": len(blocked_hits),
        "decision_counts": dict(sorted(decision_counts.items())),
        "drop_reason_counts": dict(sorted(drop_counts.items())),
        "label_canonical_counts": dict(sorted(label_counts.items())),
        "label_text_counts_top10": dict(text_counts.most_common(10)),
    }


def frame_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "frame_rows": len(rows),
        "policy_selected_prediction_count": sum(int(row.get("policy_selected_prediction_count") or 0) for row in rows),
        "projected_candidate_count": sum(int(row.get("projected_candidate_count") or 0) for row in rows),
        "raw_prediction_count": sum(int(row.get("raw_prediction_count") or 0) for row in rows),
        "skipped_no_depth_prediction_count": sum(int(row.get("skipped_no_depth_prediction_count") or 0) for row in rows),
        "written_prediction_count": sum(int(row.get("written_prediction_count") or 0) for row in rows),
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M91 Active-Label Precedence Smoke Analysis",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M89 pre-cap rows: {coverage['m89_pre_cap_rows']}.",
            f"- M91 pre-cap rows: {coverage['m91_pre_cap_rows']}.",
            f"- M89 final predictions: {coverage['m89_final_prediction_rows']}.",
            f"- M91 final predictions: {coverage['m91_final_prediction_rows']}.",
            f"- M91 cleanup decisions: `{coverage['m91_cleanup_summary']['decision_counts']}`.",
            f"- M91 canonical labels: `{coverage['m91_cleanup_summary']['label_canonical_counts']}`.",
            f"- M91 selected proposal cap respected: {str(coverage['selected_proposal_cap_respected']).lower()}.",
            f"- Blocked-field hits: {coverage['m91_cleanup_summary']['blocked_field_hit_count']}.",
            "",
            "## Agent Inference",
            "",
            "- The active-label precedence patch repairs the cleanup-stage zero-written failure if M91 pre-cap and final rows are positive while M89 remains zero.",
            "- This is still a one-scan smoke. It supports a runner repair sanity check, not final real RGB-D/open-vocabulary robustness.",
            "- Matching/query-level conversion must be run before any claim about recovered targets or search success.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m89_summary = read_json(M89_RUN_DIR / "container_output" / "pre_cap_policy_summary.json")
    m91_summary = read_json(M91_RUN_DIR / "container_output" / "pre_cap_policy_summary.json")
    m90_coverage = read_json(M90_DIR / "coverage.json")
    m91_run_coverage = read_json(M91_RUN_DIR / "coverage.json")
    m91_cleanup_rows = read_jsonl(M91_RUN_DIR / "container_output" / "cleanup_trace.jsonl")
    m91_prediction_rows = read_jsonl(M91_RUN_DIR / "container_output" / "real_proposals.jsonl")
    m91_frame_rows = read_jsonl(M91_RUN_DIR / "frame_diagnostics.jsonl")
    m91_cleanup = cleanup_summary(m91_cleanup_rows)
    per_scan_label_cap = int(m91_summary.get("per_scan_label_cap") or 24)
    m91_final_rows = int(m91_summary.get("final_prediction_rows") or line_count(M91_RUN_DIR / "container_output" / "real_proposals.jsonl"))
    m91_pre_cap_rows = int(m91_summary.get("pre_cap_candidate_pool_rows") or line_count(M91_RUN_DIR / "container_output" / "pre_cap_candidate_pool.jsonl"))
    selected_cap_respected = m91_final_rows <= per_scan_label_cap
    ready = (
        m91_pre_cap_rows > 0
        and m91_final_rows > 0
        and int(m89_summary.get("pre_cap_candidate_pool_rows") or 0) == 0
        and int(m89_summary.get("final_prediction_rows") or 0) == 0
        and m91_cleanup["decision_counts"].get("keep", 0) > 0
        and m91_cleanup["blocked_field_hit_count"] == 0
        and selected_cap_respected
    )
    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m89_final_prediction_rows": int(m89_summary.get("final_prediction_rows") or 0),
        "m89_pre_cap_rows": int(m89_summary.get("pre_cap_candidate_pool_rows") or 0),
        "m90_selected_route": m90_coverage.get("selected_route"),
        "m91_cleanup_summary": m91_cleanup,
        "m91_final_prediction_rows": m91_final_rows,
        "m91_frame_totals": frame_totals(m91_frame_rows),
        "m91_pre_cap_rows": m91_pre_cap_rows,
        "m91_prediction_rows": len(m91_prediction_rows),
        "m91_run_status": m91_run_coverage.get("status"),
        "next_recommended_unit": "E005-M92 one-scan matched-target/query conversion or bounded heldout rerun decision",
        "per_scan_label_cap": per_scan_label_cap,
        "selected_proposal_cap_respected": selected_cap_respected,
        "status": "e005_m91_active_label_precedence_smoke_ready" if ready else "e005_m91_active_label_precedence_smoke_not_ready",
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "m91_prediction_sample_rows.jsonl", m91_prediction_rows[:20])
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
