#!/usr/bin/env python3
"""Verify E005-M58 Open3DSG object-candidate export contracts and optional rows."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M58_object_candidate_export_plan_v0"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_jsonl_sample(path: Path, limit: int = 1000) -> tuple[int, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    count = 0
    if not path.exists():
        return 0, rows, errors
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            if len(rows) >= limit:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
                else:
                    errors.append(f"line {line_no}: row is not an object")
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: JSONDecodeError {exc}")
    return count, rows, errors


def validate_required_files() -> list[str]:
    required = [
        "source_context.json",
        "object_candidate_schema.json",
        "query_candidate_schema.json",
        "export_hook_contract.json",
        "docker_command_contract.json",
        "verification_contract.json",
        "next_actions.json",
        "smoke_manifest.json",
    ]
    return [name for name in required if not (LOCAL_DATA_DIR / name).exists()]


def validate_plan_contracts() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    object_schema = read_json(LOCAL_DATA_DIR / "object_candidate_schema.json")
    query_schema = read_json(LOCAL_DATA_DIR / "query_candidate_schema.json")
    docker_contract = read_json(LOCAL_DATA_DIR / "docker_command_contract.json")
    source_context = read_json(LOCAL_DATA_DIR / "source_context.json")

    if object_schema.get("schema_id") != "open3dsg_object_candidate_jsonl_v0":
        errors.append("object_candidate_schema.json has unexpected schema_id")
    if query_schema.get("schema_id") != "open3dsg_query_candidate_jsonl_v0":
        errors.append("query_candidate_schema.json has unexpected schema_id")

    object_required = set(object_schema.get("required_fields", []))
    for field in {"candidate_label", "candidate_rank", "candidate_score", "object_id", "scan_id"}:
        if field not in object_required:
            errors.append(f"object candidate schema missing {field}")

    query_required = set(query_schema.get("required_fields", []))
    for field in {"query_id", "query_label", "candidate_object_id", "strict_bbox_hit"}:
        if field not in query_required:
            errors.append(f"query candidate schema missing {field}")

    source_mount = docker_contract.get("source_mount", {})
    if source_mount.get("mode") != "read_only":
        errors.append("Docker command contract does not mark source mount read_only")
    if source_mount.get("host") != str(STAGED_ROOT):
        errors.append("Docker command contract source host is not Open3DSG_staged")
    output_mount = docker_contract.get("output_mount", {})
    if not str(output_mount.get("host", "")).startswith(str(ROOT / "local_dataset" / "Open3DSG_bridge")):
        errors.append("Docker command contract output host is not under research2/local_dataset/Open3DSG_bridge")

    assets = source_context.get("runtime_assets", {})
    if not assets.get("selected_checkpoint_exists"):
        errors.append("selected checkpoint is missing")
    if not assets.get("feature_dir_exists"):
        errors.append("feature dir is missing")

    context = {
        "object_required_fields": sorted(object_required),
        "query_required_fields": sorted(query_required),
        "docker_command_status": docker_contract.get("command_status"),
        "selected_checkpoint_exists": assets.get("selected_checkpoint_exists"),
        "feature_dir_exists": assets.get("feature_dir_exists"),
    }
    return errors, context


def validate_candidate_rows(require_output: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    object_schema = read_json(LOCAL_DATA_DIR / "object_candidate_schema.json")
    required_fields = set(object_schema.get("required_fields", []))
    row_path = LOCAL_DATA_DIR / "open3dsg_object_candidates.jsonl"
    row_count, rows, parse_errors = load_jsonl_sample(row_path)
    errors.extend(parse_errors)

    if require_output and row_count == 0:
        errors.append("require-output was set but open3dsg_object_candidates.jsonl has no rows")

    missing_field_counts: dict[str, int] = {}
    for row in rows:
        missing = sorted(required_fields - set(row))
        for field in missing:
            missing_field_counts[field] = missing_field_counts.get(field, 0) + 1
    if missing_field_counts:
        errors.append(f"candidate rows missing required fields: {missing_field_counts}")

    return errors, {
        "candidate_row_path": str(row_path),
        "candidate_row_file_exists": row_path.exists(),
        "candidate_row_count": row_count,
        "sampled_rows": len(rows),
        "missing_field_counts": missing_field_counts,
    }


def run(require_output: bool) -> dict[str, Any]:
    missing = validate_required_files()
    plan_errors, plan_context = validate_plan_contracts()
    row_errors, row_context = validate_candidate_rows(require_output=require_output)
    errors = [f"missing file: {name}" for name in missing] + plan_errors + row_errors
    candidate_rows_exist = bool(row_context["candidate_row_count"])
    if errors:
        status = "e005_m58_open3dsg_object_candidate_export_verification_failed"
    elif candidate_rows_exist:
        status = "e005_m58_open3dsg_object_candidate_rows_ready"
    else:
        status = "e005_m58_open3dsg_object_candidate_plan_ready_no_rows_yet"
    result = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "require_output": require_output,
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "source_root": str(STAGED_ROOT),
        "source_modified": False,
        "errors": errors,
        "plan_context": plan_context,
        "row_context": row_context,
    }
    write_json(ARTIFACT_DIR / "verification.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-output", action="store_true")
    args = parser.parse_args()
    result = run(require_output=args.require_output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
