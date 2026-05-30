#!/usr/bin/env python3
"""Compare E008-M12 and E008-M19 goal-eval rows and select the next navigation gate."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0"
VERSION = "e008_m20_expanded_detector_goal_failure_comparison_navigation_decision_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M12_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M12_detector_candidate_goal_evaluation_smoke_v0"
M13_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M13_detector_goal_failure_audit_v0"
M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M19_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"

HIGH_COST_WARNING_M = 25.0
LATE_HIT_RANK_WARNING = 10


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def bool_value(value: object) -> bool:
    return bool(value)


def delta(after: object, before: object) -> float | None:
    a = finite_float(after)
    b = finite_float(before)
    if a is None or b is None:
        return None
    return float(a - b)


def scan_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for row in rows:
        if row.get("metric_scope") == "scan_policy":
            out[(str(row.get("policy_id")), str(row.get("scan_id")))] = row
    return out


def aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in rows:
        if row.get("metric_scope") == "policy_aggregate":
            out[str(row.get("policy_id"))] = row
    return out


def warning_flags(row: dict[str, Any]) -> list[str]:
    flags = []
    rank = finite_float(row.get("m19_primary_first_hit_rank"))
    cost = finite_float(row.get("m19_primary_first_hit_cost_m"))
    if rank is not None and rank > LATE_HIT_RANK_WARNING:
        flags.append("late_primary_hit_rank")
    if cost is not None and cost > HIGH_COST_WARNING_M:
        flags.append("high_primary_hit_cost")
    if not row.get("m19_goal_xz_1p0_hit"):
        flags.append("goal_xz_1p0_miss")
    if int(row.get("m19_blocked_rows") or 0) > 0:
        flags.append("blocked_candidates_present")
    return flags


def build_policy_delta_rows(m12_metrics: list[dict[str, Any]], m19_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before = aggregate_rows(m12_metrics)
    after = aggregate_rows(m19_metrics)
    rows = []
    for policy_id in sorted(set(before) | set(after)):
        b = before.get(policy_id, {})
        a = after.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "m12_primary_success_rows": b.get("primary_success_rows"),
                "m19_primary_success_rows": a.get("primary_success_rows"),
                "primary_success_rows_delta": delta(a.get("primary_success_rows"), b.get("primary_success_rows")),
                "m12_primary_proxy_sr": b.get("primary_proxy_sr"),
                "m19_primary_proxy_sr": a.get("primary_proxy_sr"),
                "primary_proxy_sr_delta": delta(a.get("primary_proxy_sr"), b.get("primary_proxy_sr")),
                "m12_primary_spl_proxy_mean": b.get("primary_spl_proxy_mean"),
                "m19_primary_spl_proxy_mean": a.get("primary_spl_proxy_mean"),
                "primary_spl_proxy_delta": delta(a.get("primary_spl_proxy_mean"), b.get("primary_spl_proxy_mean")),
                "m12_goal_xz_1p0_proxy_sr": b.get("goal_xz_1p0_proxy_sr"),
                "m19_goal_xz_1p0_proxy_sr": a.get("goal_xz_1p0_proxy_sr"),
                "goal_xz_1p0_proxy_sr_delta": delta(a.get("goal_xz_1p0_proxy_sr"), b.get("goal_xz_1p0_proxy_sr")),
                "m12_mean_hit_rank_over_success": b.get("primary_first_hit_rank_mean_over_success"),
                "m19_mean_hit_rank_over_success": a.get("primary_first_hit_rank_mean_over_success"),
                "mean_hit_rank_delta": delta(
                    a.get("primary_first_hit_rank_mean_over_success"),
                    b.get("primary_first_hit_rank_mean_over_success"),
                ),
                "claim_boundary": "goal_eval_proxy_delta_not_real_navigation_sr_spl",
            }
        )
    return rows


def build_scan_comparison_rows(
    m12_metrics: list[dict[str, Any]],
    m19_metrics: list[dict[str, Any]],
    episode_failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    before = scan_rows(m12_metrics)
    after = scan_rows(m19_metrics)
    failure_by_scan = {str(row.get("scan_id")): row for row in episode_failure_rows}
    rows = []
    for key in sorted(set(before) | set(after)):
        policy_id, scan_id = key
        b = before.get(key, {})
        a = after.get(key, {})
        failure = failure_by_scan.get(scan_id, {})
        m12_hit = bool_value(b.get("primary_hit"))
        m19_hit = bool_value(a.get("primary_hit"))
        row = {
            "version": VERSION,
            "policy_id": policy_id,
            "scan_id": scan_id,
            "adapter_episode_id": a.get("adapter_episode_id") or b.get("adapter_episode_id"),
            "scene_key": a.get("scene_key") or b.get("scene_key"),
            "object_category": a.get("object_category") or b.get("object_category"),
            "m13_failure_class": failure.get("primary_failure_class"),
            "m13_recommended_next_action": failure.get("recommended_next_action"),
            "m12_primary_hit": m12_hit,
            "m19_primary_hit": m19_hit,
            "primary_failure_resolved_by_expansion": (not m12_hit) and m19_hit,
            "previous_success_preserved": m12_hit and m19_hit,
            "unresolved_primary_failure": not m19_hit,
            "m12_best_any_viewpoint_xz_m": b.get("best_any_viewpoint_xz_m"),
            "m19_best_any_viewpoint_xz_m": a.get("best_any_viewpoint_xz_m"),
            "best_any_viewpoint_xz_delta_m": delta(a.get("best_any_viewpoint_xz_m"), b.get("best_any_viewpoint_xz_m")),
            "m12_best_goal_xz_m": b.get("best_goal_xz_m"),
            "m19_best_goal_xz_m": a.get("best_goal_xz_m"),
            "best_goal_xz_delta_m": delta(a.get("best_goal_xz_m"), b.get("best_goal_xz_m")),
            "m12_primary_first_hit_rank": b.get("primary_first_hit_rank"),
            "m19_primary_first_hit_rank": a.get("primary_first_hit_rank"),
            "m12_primary_first_hit_cost_m": b.get("primary_first_hit_cost_m"),
            "m19_primary_first_hit_cost_m": a.get("primary_first_hit_cost_m"),
            "m12_primary_spl_proxy": b.get("primary_spl_proxy"),
            "m19_primary_spl_proxy": a.get("primary_spl_proxy"),
            "m12_goal_xz_1p0_hit": bool_value(b.get("goal_xz_1p0_hit")),
            "m19_goal_xz_1p0_hit": bool_value(a.get("goal_xz_1p0_hit")),
            "m19_candidate_rows": a.get("candidate_rows"),
            "m19_path_ready_rows": a.get("path_ready_rows"),
            "m19_blocked_rows": a.get("blocked_rows"),
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool_value(
                a.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
            )
            or bool_value(b.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
        }
        row["execution_warning_flags"] = warning_flags(row)
        if row["unresolved_primary_failure"]:
            row["comparison_status"] = "unresolved_after_expansion"
        elif row["primary_failure_resolved_by_expansion"]:
            row["comparison_status"] = "primary_proxy_failure_resolved_by_expansion"
        else:
            row["comparison_status"] = "previous_primary_proxy_success_preserved"
        rows.append(row)
    return rows


def build_episode_summary_rows(scan_comparison_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_comparison_rows:
        by_scan[str(row.get("scan_id"))].append(row)
    out = []
    for scan_id, rows in sorted(by_scan.items()):
        m12_success = sum(1 for row in rows if row.get("m12_primary_hit"))
        m19_success = sum(1 for row in rows if row.get("m19_primary_hit"))
        resolved = sum(1 for row in rows if row.get("primary_failure_resolved_by_expansion"))
        warnings = Counter(flag for row in rows for flag in row.get("execution_warning_flags", []))
        first = rows[0]
        out.append(
            {
                "version": VERSION,
                "scan_id": scan_id,
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "m13_failure_class": first.get("m13_failure_class"),
                "m12_primary_success_policy_count": m12_success,
                "m19_primary_success_policy_count": m19_success,
                "resolved_policy_count": resolved,
                "m19_goal_xz_1p0_success_policy_count": sum(1 for row in rows if row.get("m19_goal_xz_1p0_hit")),
                "m19_mean_primary_hit_rank": mean(
                    [finite_float(row.get("m19_primary_first_hit_rank")) for row in rows]
                ),
                "m19_mean_primary_hit_cost_m": mean(
                    [finite_float(row.get("m19_primary_first_hit_cost_m")) for row in rows]
                ),
                "warning_counts": dict(sorted(warnings.items())),
                "episode_status": "resolved_all_primary_proxy_failures"
                if m19_success == len(rows) and resolved > 0
                else "success_preserved"
                if m19_success == len(rows)
                else "unresolved_after_expansion",
                "claim_boundary": "episode_goal_eval_proxy_not_real_navigation_sr_spl",
            }
        )
    return out


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def build_gate_rows(
    coverage_m03: dict[str, Any],
    coverage_m17: dict[str, Any],
    coverage_m18: dict[str, Any],
    coverage_m19: dict[str, Any],
    scan_comparison_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    warnings = Counter(flag for row in scan_comparison_rows for flag in row.get("execution_warning_flags", []))
    min_success = int(coverage_m19.get("primary_success_count_min") or 0)
    eval_episode_rows = int(coverage_m19.get("eval_episode_rows") or 0)
    h001_ready = bool(coverage_m03.get("h001_navigation_policy_execution_ready"))
    return [
        {
            "gate": "leakage_safe_goal_eval",
            "status": "pass" if coverage_m19.get("leakage_audit_pass") else "fail",
            "evidence": f"uses eval goal/viewpoint for policy = {coverage_m19.get('uses_objectnav_eval_goal_or_viewpoint_for_policy')}",
            "required_before": "any navigation metric claim",
        },
        {
            "gate": "expanded_goal_proxy_coverage",
            "status": "pass" if min_success == eval_episode_rows and eval_episode_rows > 0 else "fail",
            "evidence": f"min policy primary hits {min_success}/{eval_episode_rows}",
            "required_before": "trajectory execution preflight",
        },
        {
            "gate": "object_center_proxy",
            "status": "warning",
            "evidence": "goal_xz_1p0 proxy hit is 4/6, while ObjectNav viewpoint proxy is 6/6",
            "required_before": "object-center claim",
        },
        {
            "gate": "path_ready_candidates",
            "status": "pass" if coverage_m17.get("every_scan_has_path_ready_candidate") else "fail",
            "evidence": f"path-ready candidates {coverage_m17.get('candidate_usable_for_path_smoke_rows')}/{coverage_m17.get('candidate_rows')}",
            "required_before": "trajectory execution preflight",
        },
        {
            "gate": "candidate_path_warning_accounting",
            "status": "warning" if int(coverage_m18.get("failure_rows") or 0) else "pass",
            "evidence": f"E008-M18 failure rows {coverage_m18.get('failure_rows')}",
            "required_before": "paper-facing navigation table",
        },
        {
            "gate": "rank_cost_warning_accounting",
            "status": "warning" if warnings else "pass",
            "evidence": json.dumps(dict(sorted(warnings.items())), sort_keys=True),
            "required_before": "deployable search policy claim",
        },
        {
            "gate": "h001_navigation_candidate_sources",
            "status": "pass" if h001_ready else "fail",
            "evidence": f"h001_navigation_policy_execution_ready={h001_ready}; h001_candidate_source_rows_ready={coverage_m03.get('h001_candidate_source_rows_ready')}",
            "required_before": "H001 real navigation claim",
        },
        {
            "gate": "trajectory_execution_metrics",
            "status": "fail",
            "evidence": "no simulator trajectory execution rows or SR/SPL rows produced yet",
            "required_before": "real navigation SR/SPL claim",
        },
        {
            "gate": "scale_for_top_tier",
            "status": "warning",
            "evidence": f"current E008 goal-eval subset has {eval_episode_rows} episodes over 2 scenes",
            "required_before": "top-tier main-table claim",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    policy_lines = [
        "| {policy_id} | {m12_primary_success_rows} | {m19_primary_success_rows} | {primary_proxy_sr_delta} | {primary_spl_proxy_delta} | {goal_xz_1p0_proxy_sr_delta} | {mean_hit_rank_delta} |".format(
            **{key: format_value(row.get(key)) for key in row}
        )
        for row in policy_rows
    ]
    episode_lines = [
        "| {scan_id} | {object_category} | {m13_failure_class} | {m12_primary_success_policy_count}/4 | {m19_primary_success_policy_count}/4 | {resolved_policy_count} | {m19_goal_xz_1p0_success_policy_count}/4 | {m19_mean_primary_hit_rank} | {m19_mean_primary_hit_cost_m} |".format(
            **{key: format_value(row.get(key)) for key in row}
        )
        for row in episode_rows
    ]
    gate_lines = [
        f"| `{row['gate']}` | {row['status']} | {row['evidence']} | {row['required_before']} |"
        for row in gate_rows
    ]
    return f"""# E008-M20 Expanded Detector-Goal Failure Comparison And Navigation Decision

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- E008-M12 primary failure rows: {coverage['m12_primary_failure_rows']}.
- E008-M19 primary failure rows: {coverage['m19_primary_failure_rows']}.
- Policies with primary proxy success 6/6 after expansion: {coverage['m19_policies_with_6_of_6_primary_success']} / {coverage['policy_count']}.
- Episodes whose primary proxy failure was resolved for at least one policy: {coverage['episodes_with_resolved_failures']}.
- Eval-only `ObjectNav` goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.
- H001 navigation policy execution ready: {coverage['h001_navigation_policy_execution_ready']}.

## Policy Delta

| policy_id | M12 hits | M19 hits | proxy SR delta | proxy SPL delta | goal 1m SR delta | mean hit-rank delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(policy_lines)}

## Episode Delta

| scan_id | category | M13 failure class | M12 primary hits | M19 primary hits | resolved policies | M19 goal 1m hits | M19 mean hit rank | M19 mean hit cost m |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(episode_lines)}

## Gate Rows

| gate | status | evidence | required before |
| --- | --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- E008-M20 is a decision artifact, not an executed navigation benchmark.
- E008-M19 removes the M12 target-coverage blocker under `GoalEvalProxy`, but this is not real navigation `SR` / `SPL`.
- H001 real navigation remains blocked because stale-memory/current-observation candidate-source execution is still missing for `HM3D ObjectNav`.
- The next step should define trajectory-execution inputs, baselines, and metric rows before launching a simulator run.

## Agent Inference

The expanded observation route is ready to enter a trajectory-execution contract/preflight for detector/path-cost policies. It is not yet ready for a final H001 navigation claim because the actual H001 candidate-source queue has not been instantiated in the `HM3D ObjectNav` setting.
"""


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    coverage_m03 = read_json(M03_ARTIFACT_DIR / "coverage.json")
    coverage_m12 = read_json(M12_ARTIFACT_DIR / "coverage.json")
    coverage_m17 = read_json(M17_ARTIFACT_DIR / "coverage.json")
    coverage_m18 = read_json(M18_ARTIFACT_DIR / "coverage.json")
    coverage_m19 = read_json(M19_ARTIFACT_DIR / "coverage.json")
    m12_metrics = read_jsonl(M12_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")
    m19_metrics = read_jsonl(M19_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")
    episode_failure_rows = read_jsonl(M13_ARTIFACT_DIR / "episode_failure_audit_rows.jsonl")

    if not m12_metrics:
        raise SystemExit("missing E008-M12 policy_goal_metric_rows.jsonl")
    if not m19_metrics:
        raise SystemExit("missing E008-M19 policy_goal_metric_rows.jsonl")

    policy_delta_rows = build_policy_delta_rows(m12_metrics, m19_metrics)
    scan_comparison_rows = build_scan_comparison_rows(m12_metrics, m19_metrics, episode_failure_rows)
    episode_summary_rows = build_episode_summary_rows(scan_comparison_rows)
    gate_rows = build_gate_rows(coverage_m03, coverage_m17, coverage_m18, coverage_m19, scan_comparison_rows)
    gate_counts = Counter(row["status"] for row in gate_rows)
    policy_count = len(policy_delta_rows)
    policies_6_of_6 = sum(1 for row in policy_delta_rows if int(row.get("m19_primary_success_rows") or 0) == 6)
    episodes_with_resolved = sum(1 for row in episode_summary_rows if int(row.get("resolved_policy_count") or 0) > 0)
    selected_next = "E008-M21 expanded detector-policy trajectory execution contract and Docker preflight"

    route_decision_rows = [
        {
            "decision": "proceed_to_trajectory_execution_contract_not_final_sr_spl",
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "h001_navigation_policy_execution_ready": False,
            "launch_long_job_now": False,
            "reason": "E008-M19 removes the M12 GoalEvalProxy coverage blocker without policy leakage, but H001 candidate-source rows and trajectory execution metrics are still missing.",
            "real_navigation_sr_spl_ready": False,
            "selected_next_unit": selected_next,
            "version": VERSION,
        }
    ]

    coverage = {
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "episode_summary_rows": len(episode_summary_rows),
        "episodes_with_resolved_failures": episodes_with_resolved,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "gate_status_counts": dict(sorted(gate_counts.items())),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "m12_primary_failure_rows": coverage_m12.get("primary_failure_rows"),
        "m19_policies_with_6_of_6_primary_success": policies_6_of_6,
        "m19_primary_failure_rows": coverage_m19.get("primary_failure_rows"),
        "policy_count": policy_count,
        "policy_delta_rows": len(policy_delta_rows),
        "real_navigation_sr_spl_ready": False,
        "scan_comparison_rows": len(scan_comparison_rows),
        "selected_next_unit": selected_next,
        "status": "e008_m20_expanded_detector_goal_failure_comparison_navigation_decision_ready",
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
            coverage_m19.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
        ),
        "version": VERSION,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_delta_rows.jsonl", policy_delta_rows)
        write_jsonl(output_dir / "scan_comparison_rows.jsonl", scan_comparison_rows)
        write_jsonl(output_dir / "episode_summary_rows.jsonl", episode_summary_rows)
        write_jsonl(output_dir / "navigation_readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_delta_rows, episode_summary_rows, gate_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
