#!/usr/bin/env python3
"""Evaluate E008-M126 target-free detector visit-order rows against ObjectNav targets."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0"
DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M127_target_free_detector_candidate_goal_evaluation_smoke_v0"
)
M64_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M125_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M125_target_free_detector_candidate_navmesh_validation_v0"
M126_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M70_TOOL = EXP_ROOT / "tools" / "run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py"
VERSION = "e008_m127_target_free_detector_candidate_goal_evaluation_smoke_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    if hasattr(module, "PRIMARY_METRIC"):
        module.PRIMARY_METRIC = PRIMARY_METRIC
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_target_free_scan_goal_metric_rows(
    scan_metric_rows: list[dict[str, Any]],
    scan_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundary_by_scan = {str(row.get("scan_id")): row for row in scan_source_rows}
    out: list[dict[str, Any]] = []
    for metric in scan_metric_rows:
        scan_id = str(metric.get("scan_id"))
        boundary = boundary_by_scan.get(scan_id, {})
        row = dict(metric)
        row.update(
            {
                "version": VERSION,
                "metric_scope": "target_free_scan_policy_goal_eval",
                "target_free_source_coverage_origin": True,
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m125": bool(boundary.get("source_ready")),
                "source_gap_after_m125": bool(boundary.get("source_gap")),
                "target_free_routes": boundary.get("target_free_routes"),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "source_gap_recovery_evaluated": True,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M127 scores fixed M126 target-free visit-order rows against ObjectNav goals/viewpoints only after policy order is frozen.",
            }
        )
        out.append(row)
    return out


def enrich_failure_rows(
    failure_rows: list[dict[str, Any]],
    scan_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundary_by_scan = {str(row.get("scan_id")): row for row in scan_source_rows}
    out: list[dict[str, Any]] = []
    for row in failure_rows:
        boundary = boundary_by_scan.get(str(row.get("scan_id")), {})
        enriched = dict(row)
        enriched.update(
            {
                "version": VERSION,
                "target_free_source_coverage_origin": True,
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m125": bool(boundary.get("source_ready")),
                "claim_boundary": "M127 failure rows are leakage-safe proxy diagnostics, not executed navigation failures.",
            }
        )
        out.append(enriched)
    return out


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_target_free_leakage_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M127 joins fixed M126 target-free detector visit rows to ObjectNav targets only as evaluation labels.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M127 is not a Habitat trajectory execution and cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M127 covers one target-free source-coverage case and does not provide heldout transfer or external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M127 detector policies are task-agnostic and do not test structured human intent as a main effect.",
        },
    ]


def build_route_decision_rows(ready: bool, any_primary_success: bool) -> list[dict[str, Any]]:
    if ready:
        return [
            {
                "version": VERSION,
                "decision": "target_free_goal_eval_smoke_ready_but_navigation_claim_blocked",
                "selected_next_unit": "E008-M128 target-free detector-goal result interpretation and trajectory-execution decision",
                "reason": "M127 evaluates frozen target-free detector visit-order rows against ObjectNav targets without policy leakage; next step is to interpret source-gap recovery and decide whether trajectory execution is justified.",
                "target_free_proxy_recovery_observed": any_primary_success,
                "launch_long_job_now": False,
                "real_navigation_sr_spl_ready": False,
                "final_real_rgbd_open_vocab_robustness_ready": False,
            }
        ]
    return [
        {
            "version": VERSION,
            "decision": "repair_m127_target_free_goal_evaluation_smoke",
            "selected_next_unit": "repair E008-M127 target-free goal-evaluation smoke",
            "reason": "M127 rows are incomplete or use blocked eval-only fields as policy inputs.",
            "target_free_proxy_recovery_observed": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    target_free_scan_goal_metric_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | "
            "{primary_first_hit_rank_mean_over_success} | {any_viewpoint_xz_1p5_proxy_sr} | {goal_xz_1p0_proxy_sr} | {best_any_viewpoint_xz_m_mean} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    scan_lines = []
    for row in target_free_scan_goal_metric_rows:
        scan_lines.append(
            "| {scan_id} | {object_category} | {policy_id} | {primary_hit} | {primary_first_hit_rank} | "
            "{primary_first_hit_cost_m} | {primary_spl_proxy} | {best_any_viewpoint_xz_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_counts = Counter(str(row["policy_id"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M127 Target-Free Detector Candidate Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M126 status: `{coverage['m126_status']}`.
- Scan-source rows: {coverage['scan_source_rows']}.
- Eval episode rows: {coverage['eval_episode_rows']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Target-free scan goal metric rows: {coverage['target_free_scan_goal_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).
- Target-free proxy recovery observed: {coverage['target_free_proxy_recovery_observed']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Target-Free Scan Policy Rows

| scan_id | category | policy_id | primary hit | first hit rank | first hit cost m | proxy SPL | best any-vp XZ m |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(scan_lines)}

## Claim Boundary

- M127 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- M127 reports `GoalEvalProxySR` / `GoalEvalProxySPL` style diagnostics, not real navigation `SR` / `SPL`.
- M127 covers the single target-free source-coverage case selected by M120-M126.
- M127 does not make final real RGB-D/open-vocabulary robustness, deployable policy, or human-intent main claims.
"""


def main() -> None:
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    m70 = load_module(M70_TOOL, "e008_m70_goal_loader")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m126_coverage = read_json(M126_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_ARTIFACT_DIR / "val_mini_episode_rows.jsonl")
    scan_source_rows = read_jsonl(M125_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")
    nav_rows = read_jsonl(M125_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(M126_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")
    if not episode_rows:
        raise SystemExit("missing M64 val_mini_episode_rows.jsonl")
    if not scan_source_rows:
        raise SystemExit("missing M125 scan_source_boundary_rows.jsonl")
    if not nav_rows:
        raise SystemExit("missing M125 candidate_navmesh_validation_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M126 candidate_visit_order_rows.jsonl")

    target_episode_ids = {str(row.get("adapter_episode_id")) for row in scan_source_rows}
    target_episode_rows = [row for row in episode_rows if str(row.get("adapter_episode_id")) in target_episode_ids]
    goal_rows = m70.build_full_val_mini_eval_goal_rows(target_episode_rows)
    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in goal_rows}
    candidate_index = {str(row["proposal_uid"]): row for row in nav_rows}

    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    policy_goal_metric_rows = scan_metric_rows + aggregate_rows
    target_free_scan_goal_metric_rows = build_target_free_scan_goal_metric_rows(scan_metric_rows, scan_source_rows)
    failure_rows = enrich_failure_rows(m12.build_failure_rows(scan_metric_rows), scan_source_rows)
    leakage_audit_rows = m12.build_leakage_audit_rows(candidate_goal_rows, eval_index)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    primary_metrics = {str(row["policy_id"]): row for row in aggregate_rows}
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in aggregate_rows]
    any_primary_success = any(count > 0 for count in primary_success_counts)
    ready = (
        bool(aggregate_rows)
        and len(goal_rows) == len(scan_source_rows)
        and len(target_free_scan_goal_metric_rows) == len(scan_source_rows) * len(aggregate_rows)
        and leakage_pass
        and not uses_eval_policy
    )
    route_decision_rows = build_route_decision_rows(ready, any_primary_success)
    claim_boundary_rows = build_claim_boundary_rows()

    coverage = {
        "version": VERSION,
        "status": "e008_m127_target_free_detector_candidate_goal_evaluation_smoke_ready"
        if ready
        else "e008_m127_target_free_detector_candidate_goal_evaluation_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m126_status": m126_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "scan_source_rows": len(scan_source_rows),
        "eval_episode_rows": len(goal_rows),
        "expected_eval_episode_rows": len(scan_source_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "candidate_navmesh_rows": len(nav_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "target_free_scan_goal_metric_rows": len(target_free_scan_goal_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_goal_metric_rows": len(policy_goal_metric_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_failure_rows": len(failure_rows),
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "target_free_proxy_recovery_observed": any_primary_success,
        "policy_primary_metrics": {
            policy_id: {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
            }
            for policy_id, row in primary_metrics.items()
        },
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "source_gap_recovery_evaluated": True,
        "real_navigation_sr_spl_ready": False,
        "real_navigation_sr_spl_smoke_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "target_free_eval_goal_rows.jsonl", goal_rows)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_goal_metric_rows)
        write_jsonl(output_dir / "target_free_scan_goal_metric_rows.jsonl", target_free_scan_goal_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, target_free_scan_goal_metric_rows, failure_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
