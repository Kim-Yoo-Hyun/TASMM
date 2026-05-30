#!/usr/bin/env python3
"""Evaluate expanded detector visit-order rows against ObjectNav targets as eval-only labels."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
VERSION = "e008_m19_expanded_detector_candidate_goal_evaluation_smoke_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"


def load_m12_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m12_goal_eval", M12_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M12_TOOL}")
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
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | "
            "{primary_first_hit_rank_mean_over_success} | {any_viewpoint_xz_1p5_proxy_sr} | {goal_xz_1p0_proxy_sr} | {best_any_viewpoint_xz_m_mean} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_counts = Counter(str(row["policy_id"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M19 Expanded Detector Candidate Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M18 status: `{coverage['m18_status']}`.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- E008-M19 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- E008-M19 is a leakage-safe goal-evaluation smoke, not executed navigation.
- It reports `GoalEvalProxySR` / `GoalEvalProxySPL` style diagnostics, not real navigation `SR` / `SPL`.
- Non-path-ready candidates from E008-M17/M18 remain explicit accounting rows.

## Agent Inference

Expanded non-oracle observations can now be evaluated against `ObjectNav` targets without policy leakage. The next decision should compare E008-M12 and E008-M19 failure rows before any simulator trajectory execution or H001 candidate-source execution claim.
"""


def main() -> None:
    m12 = load_m12_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m18_coverage = read_json(M18_ARTIFACT_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    nav_rows = read_jsonl(M17_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    visit_rows = read_jsonl(M18_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")

    if not goal_rows:
        raise SystemExit("missing M03 episode_goal_eval_rows.jsonl")
    if not nav_rows:
        raise SystemExit("missing M17 candidate_navmesh_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M18 candidate_visit_order_rows.jsonl")

    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in oracle_rows}
    candidate_index = {str(row["proposal_uid"]): row for row in nav_rows}
    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = m12.build_failure_rows(scan_metric_rows)
    leakage_audit_rows = m12.build_leakage_audit_rows(candidate_goal_rows, eval_index)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    primary_metrics = {str(row["policy_id"]): row for row in aggregate_rows}
    ready = bool(aggregate_rows) and leakage_pass and not uses_eval_policy
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in aggregate_rows]
    selected_next = (
        "E008-M20 expanded detector-goal failure comparison and navigation-execution decision"
        if ready
        else "repair E008-M19 leakage-safe goal evaluation"
    )

    route_decision_rows = [
        {
            "decision": "expanded_goal_eval_smoke_ready_but_navigation_claim_blocked" if ready else "blocked",
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "h001_navigation_policy_execution_ready": False,
            "launch_long_job_now": False,
            "reason": "Expanded visit-order rows can be evaluated against ObjectNav targets without policy leakage; compare E008-M12 and E008-M19 failures before trajectory execution."
            if ready
            else "Expanded goal-evaluation rows are missing or use blocked eval-only fields.",
            "real_navigation_sr_spl_ready": False,
            "selected_next_unit": selected_next,
            "version": VERSION,
        }
    ]

    coverage = {
        "aggregate_policy_rows": len(aggregate_rows),
        "artifact_output_root": str(ARTIFACT_DIR),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "candidate_navmesh_rows": len(nav_rows),
        "derived_output_root": str(DATA_OUT_DIR),
        "eval_episode_rows": len(goal_rows),
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "leakage_audit_pass": leakage_pass,
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "m18_status": m18_coverage.get("status"),
        "policy_goal_metric_rows": len(policy_metric_rows),
        "policy_primary_metrics": {
            policy_id: {
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
            }
            for policy_id, row in primary_metrics.items()
        },
        "primary_failure_rows": len(failure_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "real_navigation_sr_spl_ready": False,
        "scan_policy_metric_rows": len(scan_metric_rows),
        "selected_next_unit": selected_next,
        "status": "e008_m19_expanded_detector_candidate_goal_evaluation_smoke_ready"
        if ready
        else "e008_m19_expanded_detector_candidate_goal_evaluation_smoke_blocked",
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "version": VERSION,
        "visit_order_rows": len(visit_rows),
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, aggregate_rows, failure_rows), encoding="utf-8")
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
