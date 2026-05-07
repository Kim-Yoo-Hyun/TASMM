#!/usr/bin/env python3
"""Validate E003 real proposal JSONL outputs against the M17 denominator."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M18_dockerized_real_proposal_detector_scaffold_v0" / "validator_smoke"
ALLOWED_MATCH_STATUS = {
    "matched",
    "unmatched_false_positive",
    "target_missed",
    "ignored_low_confidence",
    "unmatched",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_centroid(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(is_number(item) for item in value)


def validate_prediction_row(
    row: dict[str, Any],
    row_index: int,
    required_fields: set[str],
    valid_scans: set[str],
    valid_labels: set[str],
    seen_proposal_uids: set[str],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    missing = sorted(field for field in required_fields if field not in row)
    for field in missing:
        issues.append({"field": field, "issue": "missing_required_field", "row_index": row_index, "severity": "error"})

    scan_id = row.get("scan_id")
    if scan_id not in valid_scans:
        issues.append({"field": "scan_id", "issue": "unknown_scan_id", "row_index": row_index, "severity": "error"})

    proposal_uid = row.get("proposal_uid")
    if not proposal_uid:
        issues.append({"field": "proposal_uid", "issue": "empty_proposal_uid", "row_index": row_index, "severity": "error"})
    elif proposal_uid in seen_proposal_uids:
        issues.append({"field": "proposal_uid", "issue": "duplicate_proposal_uid", "row_index": row_index, "severity": "error"})
    else:
        seen_proposal_uids.add(str(proposal_uid))

    label = row.get("label_canonical")
    if label is not None and label not in valid_labels:
        issues.append({"field": "label_canonical", "issue": "label_not_in_m17_prompt_or_target_set", "row_index": row_index, "severity": "warning"})

    confidence = row.get("confidence")
    if confidence is not None and (not is_number(confidence) or not 0.0 <= float(confidence) <= 1.0):
        issues.append({"field": "confidence", "issue": "confidence_outside_0_1", "row_index": row_index, "severity": "error"})

    match_status = row.get("match_status")
    if match_status is not None and match_status not in ALLOWED_MATCH_STATUS:
        issues.append({"field": "match_status", "issue": "unknown_match_status", "row_index": row_index, "severity": "error"})

    if match_status != "target_missed" and "centroid_world_m" in row and not validate_centroid(row.get("centroid_world_m")):
        issues.append({"field": "centroid_world_m", "issue": "invalid_centroid_world_m", "row_index": row_index, "severity": "error"})

    frame_ids = row.get("frame_ids")
    if frame_ids is not None and not isinstance(frame_ids, list):
        issues.append({"field": "frame_ids", "issue": "frame_ids_not_list", "row_index": row_index, "severity": "error"})

    return issues


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M18 Proposal Output Validator",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Prediction rows: {coverage['prediction_rows']}",
            f"- Error rows: {coverage['error_rows']}",
            f"- Warning rows: {coverage['warning_rows']}",
            f"- Empty scaffold allowed: {coverage['allow_empty_scaffold']}",
            f"- Schema-only smoke: {coverage['schema_only_smoke']}",
            f"- Detector predictions ready: {coverage['detector_predictions_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            "",
            "## 논문 주장",
            "",
            "- This validator can support schema and denominator checks for later real detector outputs.",
            "- This validator smoke does not support real perception robustness results.",
            "",
            "## 에이전트 추론",
            "",
            "- Empty-output validation is useful only for checking the Docker/output contract.",
            "- A non-empty detector output must pass the same validator before proposal recall or search metrics are computed.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for validator smoke.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--manifest", default=DEFAULT_M17_DIR / "real_proposal_query_manifest.jsonl", type=Path)
    parser.add_argument("--targets", default=DEFAULT_M17_DIR / "real_proposal_object_targets.jsonl", type=Path)
    parser.add_argument("--schema", default=DEFAULT_M17_DIR / "proposal_output_schema.json", type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--allow-empty-scaffold", action="store_true")
    parser.add_argument("--schema-only-smoke", action="store_true")
    args = parser.parse_args()

    schema = load_json(args.schema)
    manifest_rows = load_jsonl(args.manifest)
    target_rows = load_jsonl(args.targets)
    prediction_rows = load_jsonl(args.predictions) if args.predictions.exists() else []

    required_fields = set(schema.get("required_fields", {}).keys())
    valid_scans = {str(row["scan_id"]) for row in manifest_rows}
    valid_labels = {
        str(row["label_canonical"])
        for row in target_rows
        if row.get("detector_prompt_enabled") or row.get("evaluation_target_enabled")
    }

    issue_rows: list[dict[str, Any]] = []
    seen_proposal_uids: set[str] = set()
    per_scan = Counter()
    per_match_status = Counter()
    for idx, row in enumerate(prediction_rows, start=1):
        per_scan[str(row.get("scan_id"))] += 1
        per_match_status[str(row.get("match_status"))] += 1
        issue_rows.extend(
            validate_prediction_row(
                row=row,
                row_index=idx,
                required_fields=required_fields,
                valid_scans=valid_scans,
                valid_labels=valid_labels,
                seen_proposal_uids=seen_proposal_uids,
            )
        )

    error_count = sum(1 for row in issue_rows if row["severity"] == "error")
    warning_count = sum(1 for row in issue_rows if row["severity"] == "warning")
    empty_allowed = args.allow_empty_scaffold and not prediction_rows
    valid = error_count == 0 and (bool(prediction_rows) or empty_allowed)
    detector_ready = bool(prediction_rows) and error_count == 0
    paper_table_ready = detector_ready and not args.schema_only_smoke
    status = "proposal_output_valid"
    if empty_allowed:
        status = "scaffold_empty_output_validated"
    elif not prediction_rows:
        status = "proposal_output_empty_error"
    elif error_count:
        status = "proposal_output_schema_error"
    elif args.schema_only_smoke:
        status = "proposal_schema_smoke_valid"

    coverage = {
        "allow_empty_scaffold": args.allow_empty_scaffold,
        "detector_predictions_ready": detector_ready,
        "error_rows": error_count,
        "manifest_rows": len(manifest_rows),
        "paper_table_command_ready": paper_table_ready,
        "prediction_rows": len(prediction_rows),
        "prediction_rows_by_match_status": dict(sorted(per_match_status.items())),
        "prediction_rows_by_scan": dict(sorted(per_scan.items())),
        "predictions": str(args.predictions),
        "real_rgbd_or_open_vocab_claim_ready": paper_table_ready,
        "schema_only_smoke": args.schema_only_smoke,
        "schema_id": schema.get("schema_id"),
        "status": status,
        "target_rows": len(target_rows),
        "valid": valid,
        "warning_rows": warning_count,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "validation_rows.jsonl", issue_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")

    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
