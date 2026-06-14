#!/usr/bin/env python3
"""Evaluate M196 source-pool scale visit-order rows against ObjectNav targets."""

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
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M70_TOOL = EXP_ROOT / "tools" / "run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py"

VERSION = "e008_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
)
M64_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M195_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
M196_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0"
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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_source_gap_metric_rows(
    scan_source_rows: list[dict[str, Any]],
    policy_ids: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for boundary in scan_source_rows:
        if not boundary.get("source_gap"):
            continue
        for policy_id in policy_ids:
            rows.append(
                {
                    "version": VERSION,
                    "metric_scope": "scan_policy",
                    "policy_id": policy_id,
                    "scan_id": boundary.get("scan_id"),
                    "adapter_episode_id": boundary.get("adapter_episode_id"),
                    "scene_key": boundary.get("scene_key"),
                    "object_category": boundary.get("object_category"),
                    "candidate_rows": 0,
                    "path_ready_rows": 0,
                    "blocked_rows": 0,
                    "primary_metric": PRIMARY_METRIC,
                    "primary_hit": False,
                    "primary_first_hit_rank": None,
                    "primary_first_hit_cost_m": None,
                    "primary_spl_proxy": 0.0,
                    "any_viewpoint_xz_0p5_hit": False,
                    "any_viewpoint_xz_0p5_first_rank": None,
                    "any_viewpoint_xz_1p0_hit": False,
                    "any_viewpoint_xz_1p0_first_rank": None,
                    "any_viewpoint_xz_1p5_hit": False,
                    "any_viewpoint_xz_1p5_first_rank": None,
                    "goal_xz_1p0_hit": False,
                    "goal_xz_1p0_first_rank": None,
                    "goal_xz_1p5_hit": False,
                    "goal_xz_1p5_first_rank": None,
                    "best_goal_xz_m": None,
                    "best_goal_xz_rank": None,
                    "best_any_viewpoint_xz_m": None,
                    "best_any_viewpoint_xz_rank": None,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                    "source_boundary_status": boundary.get("source_boundary_status"),
                    "source_ready_after_m195": False,
                    "source_gap_after_m195": True,
                }
            )
    return rows


def aggregate_full_denominator(m12: Any, scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metric_rows:
        by_policy[str(row["policy_id"])].append(row)
    return [m12.summarize_policy_aggregate(policy_id, rows) for policy_id, rows in sorted(by_policy.items())]


def enrich_scan_goal_rows(
    scan_metric_rows: list[dict[str, Any]],
    scan_source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundary_by_scan = {str(row.get("scan_id")): row for row in scan_source_rows}
    out: list[dict[str, Any]] = []
    for metric in scan_metric_rows:
        boundary = boundary_by_scan.get(str(metric.get("scan_id")), {})
        row = dict(metric)
        row.update(
            {
                "version": VERSION,
                "metric_scope": "source_pool_scale_scan_policy_goal_eval",
                "source_pool_scale_origin": True,
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m195": bool(boundary.get("source_ready")),
                "source_gap_after_m195": bool(boundary.get("source_gap")),
                "source_pool_routes": boundary.get("target_free_routes"),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "source_gap_recovery_evaluated": True,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M197 scores fixed M196 source-pool scale visit-order rows against ObjectNav goals/viewpoints only after policy order is frozen.",
            }
        )
        out.append(row)
    return out


def enrich_failure_rows(failure_rows: list[dict[str, Any]], scan_source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boundary_by_scan = {str(row.get("scan_id")): row for row in scan_source_rows}
    out: list[dict[str, Any]] = []
    for row in failure_rows:
        boundary = boundary_by_scan.get(str(row.get("scan_id")), {})
        enriched = dict(row)
        source_gap = bool(boundary.get("source_gap"))
        enriched.update(
            {
                "version": VERSION,
                "source_pool_scale_origin": True,
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m195": bool(boundary.get("source_ready")),
                "source_gap_after_m195": source_gap,
                "failure_type": "source_gap_no_detector_candidate"
                if source_gap
                else row.get("failure_type", "no_candidate_within_any_gt_viewpoint_xz_1p0"),
                "suspected_cause": "source-pool detector produced no query-compatible candidate for this scale denominator row"
                if source_gap
                else row.get("suspected_cause"),
                "claim_boundary": "M197 failure rows are leakage-safe proxy diagnostics, not executed navigation failures.",
            }
        )
        out.append(enriched)
    return out


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_source_pool_scale_leakage_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M197 joins fixed M196 source-pool scale visit rows to ObjectNav targets only as evaluation labels.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M197 is not a Habitat trajectory execution and cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M197 still requires trajectory execution, heldout transfer, and external navigation/search baseline comparison.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M197 detector policies are task-agnostic and do not test structured human intent as a main effect.",
        },
    ]


def build_route_decision_rows(ready: bool, any_primary_success: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "source_pool_scale_goal_eval_proxy_ready_but_navigation_claim_blocked"
            if ready
            else "repair_m197_source_pool_scale_goal_eval_proxy",
            "selected": ready,
            "selected_next_unit": "E008-M198 source-pool scale proxy result interpretation and trajectory-execution decision"
            if ready
            else "repair E008-M197 source-pool scale leakage-safe goal-evaluation proxy",
            "reason": "M197 evaluates frozen source-pool scale visit-order rows on the full 30-row denominator; next interpret proxy recovery before Docker trajectory execution."
            if ready and any_primary_success
            else "M197 is leakage-safe but shows no proxy recovery; diagnose before trajectory execution."
            if ready
            else "M197 rows are incomplete or use blocked eval-only fields as policy inputs.",
            "source_pool_scale_proxy_recovery_observed": any_primary_success,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    scan_goal_rows: list[dict[str, Any]],
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
    failure_counts = Counter(str(row["failure_type"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    source_lines = []
    for row in scan_goal_rows[:24]:
        source_lines.append(
            "| {scan_id} | {object_category} | {policy_id} | {source_boundary_status} | {primary_hit} | "
            "{primary_first_hit_rank} | {primary_spl_proxy} | {best_any_viewpoint_xz_m} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    return f"""# E008-M197 Source-Pool Scale Leakage-Safe Goal-Evaluation Proxy

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M196 status: `{coverage['m196_status']}`.
- Full denominator scan rows: {coverage['full_denominator_scan_rows']}.
- Source-ready scan rows: {coverage['source_ready_scan_rows']}.
- Source-gap scan rows: {coverage['source_gap_scan_rows']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Full-denominator scan-policy rows: {coverage['source_pool_scale_scan_goal_metric_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).
- Source-pool scale proxy recovery observed: {coverage['source_pool_scale_proxy_recovery_observed']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Sample Scan Policy Rows

| scan_id | category | policy_id | source boundary | primary hit | first hit rank | proxy SPL | best any-vp XZ m |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
{chr(10).join(source_lines)}

## Claim Boundary

- M197 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- M197 reports proxy diagnostics, not executed navigation `SR` / `SPL`.
- Source-gap rows remain in the 30-row denominator as failures.
"""


def main() -> None:
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval_for_m197")
    m70 = load_module(M70_TOOL, "e008_m70_goal_loader_for_m197")
    m12.VERSION = VERSION
    m70.VERSION = VERSION

    m196_coverage = read_json(M196_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_ARTIFACT_DIR / "val_mini_episode_rows.jsonl")
    scan_source_rows = read_jsonl(M195_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")
    nav_rows = read_jsonl(M195_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(M196_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")
    if not episode_rows:
        raise SystemExit("missing M64 val_mini_episode_rows.jsonl")
    if not scan_source_rows:
        raise SystemExit("missing M195 scan_source_boundary_rows.jsonl")
    if not nav_rows:
        raise SystemExit("missing M195 candidate_navmesh_validation_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M196 candidate_visit_order_rows.jsonl")

    target_episode_ids = {str(row.get("adapter_episode_id")) for row in scan_source_rows}
    target_episode_rows = [row for row in episode_rows if str(row.get("adapter_episode_id")) in target_episode_ids]
    goal_rows = m70.build_full_val_mini_eval_goal_rows(target_episode_rows)
    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in goal_rows}
    candidate_index = {str(row["proposal_uid"]): row for row in nav_rows}

    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, _ = m12.build_metric_rows(candidate_goal_rows)
    policy_ids = sorted({str(row.get("policy_id")) for row in visit_rows if row.get("policy_id")})
    source_gap_metric_rows = build_source_gap_metric_rows(scan_source_rows, policy_ids)
    full_scan_metric_rows = scan_metric_rows + source_gap_metric_rows
    aggregate_rows = aggregate_full_denominator(m12, full_scan_metric_rows)
    policy_goal_metric_rows = full_scan_metric_rows + aggregate_rows
    source_pool_scan_goal_metric_rows = enrich_scan_goal_rows(full_scan_metric_rows, scan_source_rows)
    failure_rows = enrich_failure_rows(m12.build_failure_rows(full_scan_metric_rows), scan_source_rows)
    leakage_audit_rows = m12.build_leakage_audit_rows(candidate_goal_rows, eval_index)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in aggregate_rows]
    any_primary_success = any(count > 0 for count in primary_success_counts)
    source_ready_scan_rows = sum(1 for row in scan_source_rows if row.get("source_ready"))
    source_gap_scan_rows = sum(1 for row in scan_source_rows if row.get("source_gap"))
    ready = (
        bool(aggregate_rows)
        and len(goal_rows) == len(scan_source_rows)
        and len(source_pool_scan_goal_metric_rows) == len(scan_source_rows) * len(policy_ids)
        and leakage_pass
        and not uses_eval_policy
    )
    route_decision_rows = build_route_decision_rows(ready, any_primary_success)
    claim_boundary_rows = build_claim_boundary_rows()
    primary_metrics = {str(row["policy_id"]): row for row in aggregate_rows}

    coverage = {
        "version": VERSION,
        "status": "e008_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy_ready"
        if ready
        else "e008_m197_source_pool_scale_leakage_safe_goal_evaluation_proxy_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m196_status": m196_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "full_denominator_scan_rows": len(scan_source_rows),
        "source_ready_scan_rows": source_ready_scan_rows,
        "source_gap_scan_rows": source_gap_scan_rows,
        "eval_episode_rows": len(goal_rows),
        "expected_eval_episode_rows": len(scan_source_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "candidate_navmesh_rows": len(nav_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "source_ready_scan_policy_metric_rows": len(scan_metric_rows),
        "source_gap_scan_policy_metric_rows": len(source_gap_metric_rows),
        "source_pool_scale_scan_goal_metric_rows": len(source_pool_scan_goal_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_goal_metric_rows": len(policy_goal_metric_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_failure_rows": len(failure_rows),
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "source_pool_scale_proxy_recovery_observed": any_primary_success,
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
        write_jsonl(output_dir / "source_pool_scale_eval_goal_rows.jsonl", goal_rows)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_goal_metric_rows)
        write_jsonl(output_dir / "source_pool_scale_scan_goal_metric_rows.jsonl", source_pool_scan_goal_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, source_pool_scan_goal_metric_rows, failure_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
