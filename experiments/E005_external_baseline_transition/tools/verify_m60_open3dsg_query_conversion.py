#!/usr/bin/env python3
"""Verify E005-M60 Open3DSG query-level conversion outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M60_query_conversion_m61_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def count_jsonl(path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    count = 0
    if not path.exists():
        return 0, [f"missing:{path.name}"]
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:line {line_no}: JSONDecodeError {exc}")
                continue
            if not isinstance(row, dict):
                errors.append(f"{path.name}:line {line_no}: row is not object")
    return count, errors


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(require_policy_rows: bool) -> dict[str, Any]:
    coverage = read_json(LOCAL_DATA_DIR / "coverage.json")
    metrics = read_json(LOCAL_DATA_DIR / "metrics.json")
    errors: list[str] = []
    required_files = [
        "open3dsg_query_candidate_rows.jsonl",
        "open3dsg_candidate_eval_rows.jsonl",
        "open3dsg_policy_rows.jsonl",
        "metrics.json",
        "coverage.json",
        "report.md",
    ]
    for name in required_files:
        if not (LOCAL_DATA_DIR / name).exists():
            errors.append(f"missing file:{name}")
    query_candidate_rows, query_candidate_errors = count_jsonl(LOCAL_DATA_DIR / "open3dsg_query_candidate_rows.jsonl")
    candidate_eval_rows, candidate_eval_errors = count_jsonl(LOCAL_DATA_DIR / "open3dsg_candidate_eval_rows.jsonl")
    policy_rows, policy_errors = count_jsonl(LOCAL_DATA_DIR / "open3dsg_policy_rows.jsonl")
    errors.extend(query_candidate_errors)
    errors.extend(candidate_eval_errors)
    errors.extend(policy_errors)
    if coverage.get("query_rows") != 195:
        errors.append(f"unexpected query_rows:{coverage.get('query_rows')}")
    if coverage.get("object_candidate_rows") != 7600:
        errors.append(f"unexpected object_candidate_rows:{coverage.get('object_candidate_rows')}")
    if require_policy_rows and policy_rows != 585:
        errors.append(f"unexpected policy row count:{policy_rows}")
    if not metrics.get("policy_metrics"):
        errors.append("missing policy metrics")
    status = "e005_m60_open3dsg_query_conversion_verified" if not errors else "e005_m60_open3dsg_query_conversion_verification_failed"
    result = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "require_policy_rows": require_policy_rows,
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "errors": errors,
        "coverage_status": coverage.get("status"),
        "query_candidate_rows": query_candidate_rows,
        "candidate_eval_rows": candidate_eval_rows,
        "policy_rows": policy_rows,
        "policy_count": len(metrics.get("policy_metrics", {})),
        "scan_overlap_count": coverage.get("scan_overlap_count"),
        "query_level_performance_claim_ready": coverage.get("query_level_performance_claim_ready"),
    }
    write_json(ARTIFACT_DIR / "conversion_verification.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-policy-rows", action="store_true")
    args = parser.parse_args()
    result = run(require_policy_rows=args.require_policy_rows)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
