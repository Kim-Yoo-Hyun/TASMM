#!/usr/bin/env python3
"""Materialize expanded detector candidate visit-order rows after E008-M17."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M11_TOOL = EXP_ROOT / "tools" / "run_m11_detector_candidate_visit_order_path_smoke.py"
VERSION = "e008_m18_expanded_detector_candidate_visit_order_path_smoke_v0"


def load_m11_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m11_visit_order", M11_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M11_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True) + "\n")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], failure_counts: Counter[str]) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_scan_rows} | {mean_first_path_ready_cost_m} | {mean_top5_cumulative_known_path_cost_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M18 Expanded Detector Candidate Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M17 status: `{coverage['m17_status']}`.
- Input candidate rows: {coverage['input_candidate_rows']}.
- Query-compatible candidate rows: {coverage['query_compatible_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']} / {coverage['query_compatible_candidate_rows']}.
- Failure rows retained for policy accounting: {coverage['failure_rows']} ({failure_line}).
- Visit-order rows: {coverage['visit_order_rows']}.
- Policy metric rows: {coverage['policy_metric_rows']}.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready scans | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- E008-M18 is a visit-order/path-cost smoke over expanded detector candidates, not an executed navigation benchmark.
- E008-M18 does not claim real navigation `SR` / `SPL`.
- E008-M18 does not use `ObjectNav` goal/viewpoint coordinates as policy input.
- Non-path-ready rows remain explicit failure/accounting rows rather than being silently removed.
"""


def main() -> None:
    m11 = load_m11_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m17_coverage = read_json(M17_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M17_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing E008-M17 candidate_navmesh_rows.jsonl")

    query_compatible_rows = [
        row for row in candidate_rows if m11.query_label_compatible(row.get("object_category"), row.get("label_canonical"))
    ]
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_scan[str(row.get("scan_id"))].append(row)

    visit_rows, scan_metric_rows, aggregate_rows = m11.build_visit_order_rows(rows_by_scan)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = m11.build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)
    ready = bool(aggregate_rows) and all(row.get("candidate_visit_order_path_smoke_ready") for row in aggregate_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows)

    route_decision_rows = [
        {
            "decision": "proceed_after_expanded_visit_order_path_smoke" if ready and not uses_eval_policy else "blocked",
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "reason": "Expanded visit-order/path-cost rows are ready without eval-goal leakage; next step is leakage-safe goal evaluation."
            if ready and not uses_eval_policy
            else "Visit-order rows are not ready or use blocked eval-only fields.",
            "selected_next_unit": "E008-M19 expanded leakage-safe detector candidate goal-evaluation smoke"
            if ready and not uses_eval_policy
            else "repair E008-M18 visit-order path smoke",
            "version": VERSION,
        }
    ]

    coverage = {
        "aggregate_policy_rows": len(aggregate_rows),
        "artifact_output_root": str(ARTIFACT_DIR),
        "candidate_visit_order_path_smoke_ready": ready and not uses_eval_policy,
        "derived_output_root": str(DATA_OUT_DIR),
        "evaluated_scan_rows": len(rows_by_scan),
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "input_candidate_rows": len(candidate_rows),
        "launch_long_job_now": False,
        "m17_status": m17_coverage.get("status"),
        "path_ready_candidate_rows": sum(1 for row in query_compatible_rows if m11.is_path_ready(row)),
        "policy_count": len(m11.POLICIES),
        "policy_metric_rows": len(policy_metric_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "real_navigation_sr_spl_ready": False,
        "scan_policy_metric_rows": len(scan_metric_rows),
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
        "status": "e008_m18_expanded_detector_candidate_visit_order_path_smoke_ready"
        if ready and not uses_eval_policy
        else "e008_m18_expanded_detector_candidate_visit_order_path_smoke_blocked",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "version": VERSION,
        "visit_order_rows": len(visit_rows),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, aggregate_rows, failure_counts), encoding="utf-8")

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(DATA_OUT_DIR / "failure_rows.jsonl", failure_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
