#!/usr/bin/env python3
"""Materialize full-val-mini detector candidate visit-order/path rows after E008-M68."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M68_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M11_TOOL = EXP_ROOT / "tools" / "run_m11_detector_candidate_visit_order_path_smoke.py"
VERSION = "e008_m69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"


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


def build_episode_task_policy_rows(
    scan_metric_rows: list[dict[str, Any]],
    episode_task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tasks_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in episode_task_rows:
        tasks_by_scan[str(row.get("scan_id"))].append(row)

    out: list[dict[str, Any]] = []
    for metric in scan_metric_rows:
        for task in tasks_by_scan.get(str(metric.get("scan_id")), []):
            out.append(
                {
                    "version": VERSION,
                    "metric_scope": "episode_task_policy",
                    "policy_id": metric.get("policy_id"),
                    "candidate_scope": metric.get("candidate_scope"),
                    "scan_id": metric.get("scan_id"),
                    "adapter_episode_id": metric.get("adapter_episode_id"),
                    "scene_key": metric.get("scene_key"),
                    "object_category": task.get("object_category") or metric.get("object_category"),
                    "split_id": task.get("split_id"),
                    "scan_task_context_uid": task.get("scan_task_context_uid"),
                    "task_context_id": task.get("task_context_id"),
                    "source_ready": task.get("source_ready"),
                    "source_gap": task.get("source_gap"),
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
                    and bool(task.get("source_ready")),
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                        "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                    ),
                    "real_navigation_sr_spl_ready": False,
                    "claim_boundary": "M69 repeats scan-level detector path metrics over structured task contexts for accounting only; detector order itself is task-agnostic.",
                }
            )
    return out


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_detector_visit_order_path_materialization",
            "supported": True,
            "claim_boundary": "M69 materializes detector candidate visit-order and known source-to-candidate path-cost rows over the full-val-mini source-ready set.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M69 does not run goal evaluation or execute Habitat trajectories, so it cannot support real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M69 uses M67 detector candidates and M68 navmesh rows; target recall and external navigation/search baselines remain unresolved.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M69 detector order is task-agnostic; structured task context is only repeated for denominator accounting.",
        },
    ]


def build_route_decision_rows(ready: bool, uses_eval_policy: bool) -> list[dict[str, Any]]:
    if ready and not uses_eval_policy:
        return [
            {
                "version": VERSION,
                "decision": "proceed_after_full_val_mini_visit_order_path_smoke",
                "selected_next_unit": "E008-M70 full-val-mini leakage-safe detector candidate goal-evaluation smoke",
                "reason": "M69 materializes full-val-mini detector visit-order/path rows without eval-goal leakage; next step is eval-only goal hit scoring.",
                "launch_long_job_now": False,
                "real_navigation_sr_spl_ready": False,
                "final_real_rgbd_open_vocab_robustness_ready": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "repair_m69_visit_order_path_smoke",
            "selected_next_unit": "repair E008-M69 visit-order/path smoke",
            "reason": "Visit-order/path rows are incomplete or leakage audit failed.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    failure_counts: Counter[str],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {ranked_candidate_rows} | {path_ready_ranked_rows} | {blocked_ranked_rows} | "
            "{top1_path_ready_scan_rows} | {mean_first_path_ready_cost_m} | {mean_top5_cumulative_known_path_cost_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M69 Full-Val-Mini Detector Candidate Visit-Order Path Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M68 status: `{coverage['m68_status']}`.
- Input candidate rows: {coverage['input_candidate_rows']}.
- Query-compatible candidate rows: {coverage['query_compatible_candidate_rows']}.
- Path-ready candidate rows: {coverage['path_ready_candidate_rows']} / {coverage['query_compatible_candidate_rows']}.
- Failure rows retained for policy accounting: {coverage['failure_rows']} ({failure_line}).
- Evaluated scan rows: {coverage['evaluated_scan_rows']}.
- Episode-task policy metric rows: {coverage['episode_task_policy_metric_rows']}.
- Visit-order rows: {coverage['visit_order_rows']}.
- Policy metric rows: {coverage['policy_metric_rows']}.
- Eval-only `ObjectNav` goal/viewpoint fields used for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | ranked rows | path-ready rows | blocked rows | top1-ready scans | mean first-ready cost m | mean top5 known cost m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- E008-M69 is a visit-order/path-cost smoke over full-val-mini detector candidates, not an executed navigation benchmark.
- E008-M69 does not claim real navigation `SR` / `SPL`.
- E008-M69 does not use `ObjectNav` goal/viewpoint coordinates as policy input.
- Non-path-ready rows remain explicit failure/accounting rows rather than being silently removed.
- Task contexts are included only for denominator accounting; detector visit order is task-agnostic in this unit.
"""


def main() -> None:
    m11 = load_m11_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m68_coverage = read_json(M68_ARTIFACT_DIR / "coverage.json")
    candidate_rows = read_jsonl(M68_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    episode_task_rows = read_jsonl(M68_ARTIFACT_DIR / "episode_task_source_ready_rows.jsonl")
    scan_source_rows = read_jsonl(M68_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")
    if not candidate_rows:
        raise SystemExit("missing E008-M68 candidate_navmesh_validation_rows.jsonl")

    query_compatible_rows = [
        row for row in candidate_rows if m11.query_label_compatible(row.get("object_category"), row.get("label_canonical"))
    ]
    rows_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_compatible_rows:
        rows_by_scan[str(row.get("scan_id"))].append(row)

    visit_rows, scan_metric_rows, aggregate_rows = m11.build_visit_order_rows(rows_by_scan)
    episode_task_policy_rows = build_episode_task_policy_rows(scan_metric_rows, episode_task_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = m11.build_failure_rows(query_compatible_rows)
    failure_counts = Counter(str(row.get("navmesh_validation_status")) for row in failure_rows)
    ready = bool(aggregate_rows) and all(row.get("candidate_visit_order_path_smoke_ready") for row in aggregate_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in aggregate_rows)
    route_decision_rows = build_route_decision_rows(ready, uses_eval_policy)
    claim_boundary_rows = build_claim_boundary_rows()

    coverage = {
        "version": VERSION,
        "status": "e008_m69_full_val_mini_detector_candidate_visit_order_path_smoke_ready"
        if ready and not uses_eval_policy
        else "e008_m69_full_val_mini_detector_candidate_visit_order_path_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m68_status": m68_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "input_candidate_rows": len(candidate_rows),
        "query_compatible_candidate_rows": len(query_compatible_rows),
        "evaluated_scan_rows": len(rows_by_scan),
        "m68_path_ready_scan_rows": m68_coverage.get("path_ready_scan_rows"),
        "m68_source_ready_episode_task_rows": m68_coverage.get("source_ready_episode_task_rows"),
        "scan_source_boundary_rows": len(scan_source_rows),
        "episode_task_source_rows": len(episode_task_rows),
        "episode_task_policy_metric_rows": len(episode_task_policy_rows),
        "path_ready_candidate_rows": sum(1 for row in query_compatible_rows if m11.is_path_ready(row)),
        "failure_rows": len(failure_rows),
        "failure_status_counts": dict(sorted(failure_counts.items())),
        "policy_count": len(m11.POLICIES),
        "visit_order_rows": len(visit_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "candidate_visit_order_path_smoke_ready": ready and not uses_eval_policy,
        "source_ready_episode_task_policy_rows": sum(
            1 for row in episode_task_policy_rows if row.get("candidate_visit_order_path_smoke_ready")
        ),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(ARTIFACT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(ARTIFACT_DIR / "episode_task_policy_metric_rows.jsonl", episode_task_policy_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, aggregate_rows, failure_counts), encoding="utf-8")

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_visit_order_rows.jsonl", visit_rows)
    write_jsonl(DATA_OUT_DIR / "policy_metric_rows.jsonl", policy_metric_rows)
    write_jsonl(DATA_OUT_DIR / "episode_task_policy_metric_rows.jsonl", episode_task_policy_rows)
    write_jsonl(DATA_OUT_DIR / "failure_rows.jsonl", failure_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_decision_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
