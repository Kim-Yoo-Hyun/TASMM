#!/usr/bin/env python3
"""Verify the E005-M60 Open3DSG query-conversion contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M60_query_conversion_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_contract_v0"
M59_LOCAL_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M59_object_candidate_export_smoke_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_jsonl(path: Path) -> tuple[int, list[str]]:
    if not path.exists():
        return 0, []
    errors: list[str] = []
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    errors.append(f"line {line_no}: row is not an object")
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: JSONDecodeError {exc}")
    return count, errors


def required_file_errors() -> list[str]:
    required = [
        "input_inventory.json",
        "query_conversion_contract.json",
        "execution_contract.json",
        "coverage.json",
        "report.md",
    ]
    return [f"missing file: {name}" for name in required if not (LOCAL_DATA_DIR / name).exists()]


def validate_contracts(require_m59_rows: bool) -> tuple[list[str], dict[str, Any]]:
    errors = required_file_errors()
    coverage = read_json(LOCAL_DATA_DIR / "coverage.json")
    contract = read_json(LOCAL_DATA_DIR / "query_conversion_contract.json")
    inventory = read_json(LOCAL_DATA_DIR / "input_inventory.json")
    execution = read_json(LOCAL_DATA_DIR / "execution_contract.json")

    if contract.get("contract_id") != "open3dsg_query_level_conversion_contract_v0":
        errors.append("unexpected query_conversion_contract.contract_id")
    if execution.get("contract_id") != "open3dsg_query_conversion_execution_contract_v0":
        errors.append("unexpected execution_contract.contract_id")
    if coverage.get("m45_query_rows") != 195:
        errors.append(f"unexpected denominator rows: {coverage.get('m45_query_rows')}")
    if coverage.get("source_modified") is not False:
        errors.append("source_modified is not false")

    object_rows_path = M59_LOCAL_DIR / "open3dsg_object_candidates.jsonl"
    m59_rows, parse_errors = count_jsonl(object_rows_path)
    errors.extend([f"m59_object_candidates:{error}" for error in parse_errors])
    if require_m59_rows and m59_rows == 0:
        errors.append("require-m59-rows was set but M59 object candidate rows are missing")

    join_rule = contract.get("join_rule", [])
    if not any("Do not use target_uid" in str(item) for item in join_rule):
        errors.append("join_rule does not record leakage prohibition")
    if "open3dsg_policy_rows.jsonl" not in contract.get("output_schemas", {}):
        errors.append("missing open3dsg_policy_rows output schema")
    if "ExpectedSearchCost" not in json.dumps(contract.get("metrics", [])):
        errors.append("metrics do not include ExpectedSearchCost")

    context = {
        "coverage_status": coverage.get("status"),
        "m45_query_rows": coverage.get("m45_query_rows"),
        "m59_object_candidate_rows_at_plan_time": coverage.get("m59_object_candidate_rows"),
        "m59_object_candidate_rows_now": m59_rows,
        "m58_object_schema_id": inventory.get("m58_object_schema_id"),
        "future_command": execution.get("future_command"),
        "query_level_performance_claim_ready": bool(coverage.get("query_level_performance_claim_ready")),
    }
    return errors, context


def run(require_m59_rows: bool) -> dict[str, Any]:
    errors, context = validate_contracts(require_m59_rows=require_m59_rows)
    if errors:
        status = "e005_m60_open3dsg_query_conversion_contract_verification_failed"
    elif context["m59_object_candidate_rows_now"] > 0:
        status = "e005_m60_open3dsg_query_conversion_contract_ready_for_conversion_smoke"
    else:
        status = "e005_m60_open3dsg_query_conversion_contract_ready_waiting_m59_rows"
    result = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "require_m59_rows": require_m59_rows,
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "errors": errors,
        "context": context,
    }
    write_json(ARTIFACT_DIR / "verification.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-m59-rows", action="store_true")
    args = parser.parse_args()
    result = run(require_m59_rows=args.require_m59_rows)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
