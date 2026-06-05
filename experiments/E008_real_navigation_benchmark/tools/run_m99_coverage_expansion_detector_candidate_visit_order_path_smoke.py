#!/usr/bin/env python3
"""Materialize coverage-expansion detector candidate visit-order/path rows after E008-M98."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0"
M98_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M98_coverage_expansion_detector_candidate_navmesh_validation_v0"
M11_TOOL = EXP_ROOT / "tools" / "run_m11_detector_candidate_visit_order_path_smoke.py"
VERSION = "e008_m99_coverage_expansion_detector_candidate_visit_order_path_smoke_v0"


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
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
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
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_coverage_scan_policy_rows(
    scan_metric_rows: list[dict[str, Any]],
    scan_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundary_by_scan = {str(row.get("scan_id")): row for row in scan_source_rows}
    out: list[dict[str, Any]] = []
    for metric in scan_metric_rows:
        boundary = boundary_by_scan.get(str(metric.get("scan_id")), {})
        out.append(
            {
                "version": VERSION,
                "metric_scope": "coverage_expansion_scan_policy",
                "policy_id": metric.get("policy_id"),
                "candidate_scope": metric.get("candidate_scope"),
                "scan_id": metric.get("scan_id"),
                "adapter_episode_id": metric.get("adapter_episode_id"),
                "scene_key": metric.get("scene_key"),
                "object_category": boundary.get("object_category") or metric.get("object_category"),
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m98": bool(boundary.get("source_ready")),
                "source_gap_after_m98": bool(boundary.get("source_gap")),
                "input_candidate_rows": metric.get("input_candidate_rows"),
                "ranked_candidate_rows": metric.get("ranked_candidate_rows"),
                "path_ready_ranked_rows": metric.get("path_ready_ranked_rows"),
                "blocked_ranked_rows": metric.get("blocked_ranked_rows"),
                "first_path_ready_rank": metric.get("first_path_ready_rank"),
                "first_path_ready_cost_m": metric.get("first_path_ready_cost_m"),
                "top1_path_ready": metric.get("top1_path_ready"),
                "top5_path_ready_rows": metric.get("top5_path_ready_rows"),
                "top5_blocked_rows": metric.get("top5_blocked_rows"),
                "top5_cumulative_known_path_cost_m": metric.get("top5_cumulative_known_path_cost_m"),
                "candidate_visit_order_path_smoke_ready": bool(metric.get("candidate_visit_order_path_smoke_ready"))
                and bool(boundary.get("source_ready")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M99 evaluates coverage-expansion detector visit order and source-to-candidate path costs only; it does not score goal hits or execute trajectories.",
            }
        )
    return out


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_coverage_expansion_visit_order_path_materialization",
            "supported": True,
            "claim_boundary": "M99 materializes coverage-expansion detector candidate visit-order and source-to-candidate path-cost rows without eval-goal/viewpoint policy leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M99 does not compare candidates against eval-only ObjectNav goals or viewpoints, so it cannot claim target recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M99 does not execute Habitat trajectories, so it cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M99 is a one-case coverage-expansion path smoke and still lacks heldout transfer and external navigation/search baselines.",
        },
    ]


def build_route_decision_rows(ready: bool, uses_eval_policy: bool) -> list[dict[str, Any]]:
    if ready and not uses_eval_policy:
        return [
            {
                "version": VERSION,
                "decision": "proceed_after_coverage_expansion_visit_order_path_smoke",
                "selected_next_unit": "E008-M100 coverage-expansion leakage-safe detector candidate goal-evaluation smoke",
                "reason": "M99 materializes coverage-expansion detector visit-order/path rows without eval-goal leakage; next step is eval-only goal-hit scoring for source-gap recovery.",
                "launch_long_job_now": False,
                "real_navigation_sr_spl_ready": False,
                "final_real_rgbd_open_vocab_robustness_ready": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "repair_m99_coverage_expansion_visit_order_path_smoke",
            "selected_next_unit": "repair E008-M99 coverage-expansion visit-order/path smoke",
            "reason": "Visit-order/path rows are incomplete or leakage audit failed.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    coverage_scan_policy_rows: list[dict[str, Any]],
    failure_counts: Counter[str],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_scan_rows} | {mean_first_path_ready_rank} | {mean_first_path_ready_cost_m} | {mean_top5_cumulative_known_path_cost_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    scan_lines = []
    for row in coverage_scan_policy_rows:
        scan_lines.append(
            "| {scan_id} | {object_category} | {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | "
            "{first_path_ready_rank} | {first_path_ready_cost_m} | {top5_path_ready_rows} | {source_boundary_status} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M99 Coverage-Expansion Detector Candidate Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M98 status: `{coverage['m98_status']}`.
- Input candidate rows: {coverage['input_candidate_rows']}.
- Query-compatible candidate rows: {coverage['query_compatible_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']} / {coverage['query_compatible_candidate_rows']}.
- Failure rows retained for policy accounting: {coverage['failure_rows']} ({failure_line}).
- Visit-order rows: {coverage['visit_order_rows']}.
- Coverage scan policy metric rows: {coverage['coverage_scan_policy_metric_rows']}.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready cases | mean first-ready rank | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Coverage Scan Policy Rows

| scan_id | category | policy_id | ranked | path-ready | first-ready rank | first-ready cost m | top5 path-ready | boundary |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(scan_lines)}

## Claim Boundary

- M99 is a coverage-expansion visit-order/path-cost smoke, not an executed navigation benchmark.
- M99 does not claim source-gap recovery because eval-only goal/viewpoint matching is not run here.
- M99 does not claim real navigation `SR` / `SPL`.
- M99 does not use `ObjectNav` goal/viewpoint coordinates as policy input.
- Non-path-ready rows remain explicit failure/accounting rows rather than being silently removed.
"""


def main() -> None:
    m11 = load_m11_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m98_coverage = read_json(M98_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M98_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    scan_source_rows = read_jsonl(M98_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing E008-M98 candidate_navmesh_validation_rows.jsonl")
    if not scan_source_rows:
        raise SystemExit("missing E008-M98 scan_source_boundary_rows.jsonl")

    query_compatible_rows = [
        row
        for row in candidate_rows
        if m11.query_label_compatible(row.get("object_category"), row.get("label_canonical"))
    ]
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_scan[str(row.get("scan_id"))].append(row)

    visit_rows, scan_metric_rows, aggregate_rows = m11.build_visit_order_rows(rows_by_scan)
    coverage_scan_policy_rows = build_coverage_scan_policy_rows(scan_metric_rows, scan_source_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = m11.build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)
    ready = bool(aggregate_rows) and all(row.get("candidate_visit_order_path_smoke_ready") for row in aggregate_rows)
    scan_ready = all(row.get("source_ready") for row in scan_source_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows)
    route_decision_rows = build_route_decision_rows(ready and scan_ready, uses_eval_policy)
    claim_boundary_rows = build_claim_boundary_rows()

    coverage = {
        "version": VERSION,
        "status": "e008_m99_coverage_expansion_detector_candidate_visit_order_path_smoke_ready"
        if ready and scan_ready and not uses_eval_policy
        else "e008_m99_coverage_expansion_detector_candidate_visit_order_path_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m98_status": m98_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "input_candidate_rows": len(candidate_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "evaluated_scan_rows": len(rows_by_scan),
        "m98_path_ready_scan_rows": m98_coverage.get("path_ready_scan_rows"),
        "scan_source_boundary_rows": len(scan_source_rows),
        "path_ready_candidate_rows": sum(1 for row in query_compatible_rows if m11.is_path_ready(row)),
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "policy_count": len(m11.POLICIES),
        "visit_order_rows": len(visit_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "coverage_scan_policy_metric_rows": len(coverage_scan_policy_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "candidate_visit_order_path_smoke_ready": ready and scan_ready and not uses_eval_policy,
        "coverage_scan_policy_ready_rows": sum(
            1 for row in coverage_scan_policy_rows if row.get("candidate_visit_order_path_smoke_ready")
        ),
        "real_navigation_sr_spl_ready": False,
        "source_gap_recovery_evaluated": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(ARTIFACT_DIR / "coverage_scan_policy_metric_rows.jsonl", coverage_scan_policy_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, aggregate_rows, coverage_scan_policy_rows, failure_counts), encoding="utf-8"
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(DATA_OUT_DIR / "coverage_scan_policy_metric_rows.jsonl", coverage_scan_policy_rows)
    write_jsonl(DATA_OUT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_decision_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
