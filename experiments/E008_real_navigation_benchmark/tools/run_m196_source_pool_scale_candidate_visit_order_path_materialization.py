#!/usr/bin/env python3
"""Materialize M195 source-pool scale candidate visit-order/path rows."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M11_TOOL = EXP_ROOT / "tools" / "run_m11_detector_candidate_visit_order_path_smoke.py"
M126_TOOL = EXP_ROOT / "tools" / "run_m126_target_free_detector_candidate_visit_order_path_smoke.py"

VERSION = "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0"
)
M195_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_leakage_audit_rows(
    visit_rows: list[dict[str, Any]],
    scan_metric_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    m126: Any,
) -> list[dict[str, Any]]:
    rows = m126.build_leakage_audit_rows(visit_rows, scan_metric_rows, aggregate_rows)
    for row in rows:
        row["version"] = VERSION
        row["scope"] = "source_pool_scale_visit_order_path_materialization"
    return rows


def build_claim_boundary_rows(status: str) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_source_pool_scale_visit_order_materialization",
            "supported": status
            in {
                "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_ready",
                "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_ready_with_source_warnings",
            },
            "claim_boundary": "M196 materializes source-pool scale detector candidate visit-order and source-to-candidate path-cost rows without eval-goal/viewpoint policy leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M196 keeps source-gap rows explicit but does not compare candidates against eval-only ObjectNav goals or viewpoints.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M196 does not execute Habitat trajectories, so it cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M196 is a denominator/path-materialization gate; robustness requires M197 goal evaluation, M198+ trajectory execution, heldout transfer, and external baseline comparison.",
        },
    ]


def build_route_decision_rows(ready: bool, warning: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_after_source_pool_scale_visit_order_path_materialization" if ready else "repair_m196",
            "selected": ready,
            "selected_next_unit": "E008-M197 source-pool scale leakage-safe goal-evaluation proxy"
            if ready
            else "repair E008-M196 source-pool scale candidate visit-order/path materialization",
            "reason": "M196 retains the 30-row scale denominator and separates source-ready from source-gap rows."
            if ready and warning
            else "M196 materialized visit-order/path rows without source-gap warnings."
            if ready
            else "M196 did not produce leakage-safe source-ready visit-order/path rows.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    source_boundary_counts: Counter[str],
    failure_counts: Counter[str],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_scan_rows} | {mean_first_path_ready_rank} | {mean_first_path_ready_cost_m} | "
            "{mean_top5_cumulative_known_path_cost_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    source_line = ", ".join(f"`{key}` {value}" for key, value in sorted(source_boundary_counts.items())) or "none"
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M196 Source-Pool Scale Candidate Visit-Order Path Materialization

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M195 status: `{coverage['m195_status']}`.
- Denominator scan rows: {coverage['denominator_scan_rows']}.
- Source-ready scan rows: {coverage['source_ready_scan_rows']}.
- Source-gap scan rows: {coverage['source_gap_scan_rows']} ({source_line}).
- Input candidate rows: {coverage['input_candidate_rows']}.
- Query-compatible candidate rows: {coverage['query_compatible_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']}.
- Failure rows retained for accounting: {coverage['failure_rows']} ({failure_line}).
- Visit-order rows: {coverage['visit_order_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready scans | mean first-ready rank | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- M196 is a path-materialization gate, not a goal-recovery or trajectory result.
- Source-gap scan rows stay in the denominator and are not silently dropped.
- M196 does not claim final `SR`, `SPL`, or real RGB-D/open-vocabulary robustness.
"""


def main() -> None:
    m11 = load_module(M11_TOOL, "e008_m11_visit_order_for_m196")
    m126 = load_module(M126_TOOL, "e008_m126_helpers_for_m196")
    m11.VERSION = VERSION
    m126.VERSION = VERSION

    m195_coverage = read_json(M195_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M195_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    scan_source_rows = read_jsonl(M195_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing M195 candidate_navmesh_validation_rows.jsonl")
    if not scan_source_rows:
        raise SystemExit("missing M195 scan_source_boundary_rows.jsonl")

    query_compatible_rows = [
        row
        for row in candidate_rows
        if m11.query_label_compatible(row.get("object_category"), row.get("label_canonical"))
    ]
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_scan[str(row.get("scan_id"))].append(row)

    visit_rows, scan_metric_rows, aggregate_rows = m11.build_visit_order_rows(rows_by_scan)
    scan_source_policy_rows = m126.build_scan_source_policy_rows(scan_metric_rows, scan_source_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = m11.build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)
    leakage_audit_rows = build_leakage_audit_rows(visit_rows, scan_metric_rows, aggregate_rows, m126)
    leakage_pass = all(row.get("passed") for row in leakage_audit_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows)
    source_ready_scan_rows = sum(1 for row in scan_source_rows if row.get("source_ready"))
    source_gap_scan_rows = sum(1 for row in scan_source_rows if row.get("source_gap"))
    source_boundary_counts = Counter(str(row.get("source_boundary_status")) for row in scan_source_rows)
    path_ready_candidate_rows = sum(1 for row in query_compatible_rows if m11.is_path_ready(row))

    ready_core = bool(aggregate_rows) and path_ready_candidate_rows > 0 and leakage_pass and not uses_eval_policy
    warning = source_gap_scan_rows > 0 or source_ready_scan_rows < len(scan_source_rows)
    status = (
        "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_ready_with_source_warnings"
        if ready_core and warning
        else "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_ready"
        if ready_core
        else "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_blocked"
    )
    ready = status != "e008_m196_source_pool_scale_candidate_visit_order_path_materialization_blocked"
    route_decision_rows = build_route_decision_rows(ready, warning)
    claim_boundary_rows = build_claim_boundary_rows(status)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m195_status": m195_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "denominator_scan_rows": len(scan_source_rows),
        "evaluated_scan_rows": len(rows_by_scan),
        "source_ready_scan_rows": source_ready_scan_rows,
        "source_gap_scan_rows": source_gap_scan_rows,
        "source_boundary_status_counts": dict(sorted(source_boundary_counts.items())),
        "input_candidate_rows": len(candidate_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "path_ready_candidate_rows": path_ready_candidate_rows,
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "policy_count": len(m11.POLICIES),
        "visit_order_rows": len(visit_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "scan_source_policy_metric_rows": len(scan_source_policy_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "leakage_audit_pass": leakage_pass,
        "candidate_visit_order_path_materialization_ready": ready,
        "source_gap_recovery_evaluated": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_visit_order_rows.jsonl", visit_rows)
        write_jsonl(output_dir / "policy_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "scan_policy_metric_rows.jsonl", scan_metric_rows)
        write_jsonl(output_dir / "scan_source_policy_metric_rows.jsonl", scan_source_policy_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, source_boundary_counts, failure_counts))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
