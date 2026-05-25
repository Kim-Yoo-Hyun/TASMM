#!/usr/bin/env python3
"""Verify E005-M64 Open3DSG predicted-vocabulary policy outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M64_vocab_expansion_policy_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0"


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


def policy_metric(metrics: dict[str, Any], policy: str) -> dict[str, Any]:
    return metrics.get("policy_metrics", {}).get(policy, {})


def run(require_ready: bool) -> dict[str, Any]:
    coverage = read_json(LOCAL_DATA_DIR / "coverage.json")
    metrics = read_json(LOCAL_DATA_DIR / "metrics.json")
    errors: list[str] = []
    required_files = [
        "open3dsg_vocab_query_candidate_rows.jsonl",
        "open3dsg_vocab_candidate_eval_rows.jsonl",
        "open3dsg_vocab_policy_rows.jsonl",
        "comparison_rows.jsonl",
        "metrics.json",
        "coverage.json",
        "report.md",
    ]
    for name in required_files:
        if not (LOCAL_DATA_DIR / name).exists():
            errors.append(f"missing file:{name}")
    query_candidate_rows, query_candidate_errors = count_jsonl(
        LOCAL_DATA_DIR / "open3dsg_vocab_query_candidate_rows.jsonl"
    )
    candidate_eval_rows, candidate_eval_errors = count_jsonl(
        LOCAL_DATA_DIR / "open3dsg_vocab_candidate_eval_rows.jsonl"
    )
    policy_rows, policy_errors = count_jsonl(LOCAL_DATA_DIR / "open3dsg_vocab_policy_rows.jsonl")
    comparison_rows, comparison_errors = count_jsonl(LOCAL_DATA_DIR / "comparison_rows.jsonl")
    errors.extend(query_candidate_errors)
    errors.extend(candidate_eval_errors)
    errors.extend(policy_errors)
    errors.extend(comparison_errors)

    if require_ready and coverage.get("status") != "e005_m64_open3dsg_vocab_expansion_policy_ready":
        errors.append(f"unexpected status:{coverage.get('status')}")
    if coverage.get("query_rows") != 195:
        errors.append(f"unexpected query_rows:{coverage.get('query_rows')}")
    if coverage.get("object_candidate_rows") != 7600:
        errors.append(f"unexpected object_candidate_rows:{coverage.get('object_candidate_rows')}")
    if policy_rows != 585:
        errors.append(f"unexpected policy row count:{policy_rows}")
    if candidate_eval_rows != query_candidate_rows:
        errors.append(f"candidate/eval row mismatch:{query_candidate_rows}!={candidate_eval_rows}")
    strict = policy_metric(metrics, "open3dsg_predicted_terms_bbox_strict_top5_v0")
    relaxed = policy_metric(metrics, "open3dsg_predicted_terms_bbox_relaxed_1m_top3_v0")
    if strict.get("query_bridge_success_rows") != 144:
        errors.append(f"unexpected strict success:{strict.get('query_bridge_success_rows')}")
    if relaxed.get("query_bridge_success_rows") != 147:
        errors.append(f"unexpected relaxed success:{relaxed.get('query_bridge_success_rows')}")
    if coverage.get("uses_gt_object_label") is not False:
        errors.append("leakage audit failed:uses_gt_object_label")
    if coverage.get("uses_id2name_label") is not False:
        errors.append("leakage audit failed:uses_id2name_label")
    if coverage.get("uses_target_uid_before_ranking") is not False:
        errors.append("leakage audit failed:uses_target_uid_before_ranking")
    if coverage.get("uses_target_geometry_before_ranking") is not False:
        errors.append("leakage audit failed:uses_target_geometry_before_ranking")
    if coverage.get("diagnostic_promoted_to_policy") is not True:
        errors.append("diagnostic_promoted_to_policy flag missing")
    if require_ready and coverage.get("open3dsg_vocab_policy_ready") is not True:
        errors.append("open3dsg_vocab_policy_ready is not true")

    status = (
        "e005_m64_open3dsg_vocab_expansion_policy_verified"
        if not errors
        else "e005_m64_open3dsg_vocab_expansion_policy_verification_failed"
    )
    result = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "require_ready": require_ready,
        "local_data_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "errors": errors,
        "coverage_status": coverage.get("status"),
        "query_candidate_rows": query_candidate_rows,
        "candidate_eval_rows": candidate_eval_rows,
        "policy_rows": policy_rows,
        "comparison_rows": comparison_rows,
        "strict_success_rows": strict.get("query_bridge_success_rows"),
        "strict_success_rate": strict.get("query_bridge_success_rate"),
        "relaxed_success_rows": relaxed.get("query_bridge_success_rows"),
        "relaxed_success_rate": relaxed.get("query_bridge_success_rate"),
        "open3dsg_vocab_policy_ready": coverage.get("open3dsg_vocab_policy_ready"),
        "open3dsg_main_table_candidate_ready": coverage.get("open3dsg_main_table_candidate_ready"),
    }
    write_json(ARTIFACT_DIR / "policy_verification.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    result = run(require_ready=args.require_ready)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
