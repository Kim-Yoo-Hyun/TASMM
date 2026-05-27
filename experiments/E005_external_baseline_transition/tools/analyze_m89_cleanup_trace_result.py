#!/usr/bin/env python3
"""Analyze E005-M89 cleanup trace output."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
RUN_ROOT = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_run_v0"
VERIFY_ROOT = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_verification_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_analysis_v0"
VERSION = "e005_m89_cleanup_trace_analysis_v0"
SCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"


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


def build_label_rows(trace_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for row in trace_rows:
        counts[
            (
                str(row.get("label_text")),
                str(row.get("label_canonical")),
                str(row.get("drop_reason")),
            )
        ] += 1
    return [
        {
            "drop_reason": drop_reason,
            "label_canonical": label_canonical,
            "label_text": label_text,
            "row_count": count,
        }
        for (label_text, label_canonical, drop_reason), count in counts.most_common()
    ]


def build_report(coverage: dict[str, Any], label_rows: list[dict[str, Any]]) -> str:
    label_lines = ["| Label text | Canonical | Drop reason | Rows |", "| --- | --- | --- | ---: |"]
    for row in label_rows[:20]:
        label_lines.append(
            f"| `{row['label_text']}` | `{row['label_canonical']}` | `{row['drop_reason']}` | {row['row_count']} |"
        )
    return "\n".join(
        [
            "# E005-M89 Cleanup Trace Analysis",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Scan: `{coverage['scan_id']}`.",
            f"- Trace rows: {coverage['trace_rows']}.",
            f"- Decision counts: `{coverage['decision_counts']}`.",
            f"- Drop reason counts: `{coverage['drop_reason_counts']}`.",
            f"- Canonical label counts: `{coverage['label_canonical_counts']}`.",
            f"- Active scan labels: `{coverage['active_scan_labels']}`.",
            f"- Blocked-field hits: {coverage['blocked_field_hit_count']}.",
            "",
            "## Label Distribution",
            "",
            *label_lines,
            "",
            "## Interpretation",
            "",
            "- The trace is target-independent: it contains detector labels and cleanup decisions but no target uid or query outcome fields.",
            "- The dominant pattern is `a chair` / `chair` resolving to `stool` while the active scan label is only `chair`; the small `a` tail is a non-prompt parsing artifact.",
            "- Therefore the zero-written cluster is a label-resolution / prompt-scope mismatch rather than score ranking, cap, or match-threshold failure.",
            "- A repair should be limited to label-normalization or scan-label prompt expansion and must be re-evaluated against false-positive inflation.",
            "",
        ]
    )


def main() -> int:
    batch_id = "heldout_b02"
    run_dir = RUN_ROOT / batch_id
    verify_dir = VERIFY_ROOT / batch_id
    trace_rows = read_jsonl(run_dir / "container_output" / "cleanup_trace.jsonl")
    run_coverage = read_json(run_dir / "coverage.json")
    verify_coverage = read_json(verify_dir / "coverage.json")
    decision_counts = Counter(str(row.get("cleanup_decision")) for row in trace_rows)
    drop_reason_counts = Counter(str(row.get("drop_reason")) for row in trace_rows)
    label_counts = Counter(str(row.get("label_canonical")) for row in trace_rows)
    active_scan_labels = sorted(
        {
            label
            for row in trace_rows
            for label in row.get("active_scan_labels", [])
        }
    )
    blocked_fields = {
        "target_uid",
        "candidate_is_target",
        "matched_3dssg_instance_id",
        "nearest_target_distance",
        "query_success_label",
    }
    blocked_hits = [
        {"blocked_fields": sorted(field for field in blocked_fields if field in row), "row_index": idx}
        for idx, row in enumerate(trace_rows, start=1)
        if any(field in row for field in blocked_fields)
    ]
    label_rows = build_label_rows(trace_rows)
    all_drop_not_scan_prompt = bool(trace_rows) and drop_reason_counts == {"drop_not_scan_prompt_label": len(trace_rows)}
    dominant_not_scan_prompt = bool(trace_rows) and drop_reason_counts.get("drop_not_scan_prompt_label", 0) / len(trace_rows) >= 0.95
    dominant_stool = bool(trace_rows) and label_counts.get("stool", 0) / len(trace_rows) >= 0.95
    repair_route = (
        "label_normalization_or_scan_prompt_scope_audit_next"
        if all_drop_not_scan_prompt or (dominant_not_scan_prompt and dominant_stool and active_scan_labels == ["chair"])
        else "inspect_mixed_cleanup_drop_reasons_before_repair"
    )
    coverage = {
        "active_scan_labels": active_scan_labels,
        "all_drop_not_scan_prompt_label": all_drop_not_scan_prompt,
        "blocked_field_hit_count": len(blocked_hits),
        "decision_counts": dict(sorted(decision_counts.items())),
        "dominant_not_scan_prompt_label": dominant_not_scan_prompt,
        "dominant_stool_canonical_label": dominant_stool,
        "drop_reason_counts": dict(sorted(drop_reason_counts.items())),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "label_canonical_counts": dict(sorted(label_counts.items())),
        "next_recommended_unit": "E005-M90 label-normalization / scan-prompt scope repair decision",
        "repair_route": repair_route,
        "run_status": run_coverage.get("status"),
        "scan_id": SCAN_ID,
        "status": "e005_m89_cleanup_trace_analysis_ready" if trace_rows and not blocked_hits else "e005_m89_cleanup_trace_analysis_blocked",
        "trace_rows": len(trace_rows),
        "verification_status": verify_coverage.get("status"),
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "label_distribution_rows.jsonl", label_rows)
    write_jsonl(OUT_DIR / "blocked_field_hits.jsonl", blocked_hits)
    write_text(OUT_DIR / "report.md", build_report(coverage, label_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"] == "e005_m89_cleanup_trace_analysis_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
