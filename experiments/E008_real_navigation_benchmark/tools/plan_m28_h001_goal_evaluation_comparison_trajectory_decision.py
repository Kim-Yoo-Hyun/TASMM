#!/usr/bin/env python3
"""Compare M27 H001 goal-eval results and decide the next trajectory gate."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0"
)
M22_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M27_DIR = EXP_ROOT / "artifacts" / "E008-M27_h001_goal_evaluation_smoke_v0"
VERSION = "e008_m28_h001_goal_evaluation_comparison_trajectory_decision_v0"

H001_POLICY = "h001_real_task_context_memory_trust_v0"
BASELINE_POLICIES = [
    "real_static_memory_proxy_v0",
    "real_detector_confidence_expanded_v0",
    "real_context_agnostic_memory_trust_reobserve_v0",
]
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
MIN_SCALE_EPISODES_FOR_TRAJECTORY_CLAIM = 20


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


def safe_ratio(num: int, denom: int) -> float | None:
    return round(float(num) / float(denom), 6) if denom else None


def delta(a: object, b: object) -> float | None:
    af = finite_float(a)
    bf = finite_float(b)
    if af is None or bf is None:
        return None
    return round(af - bf, 6)


def scan_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_policy"]


def aggregate_policy_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id")): row
        for row in rows
        if row.get("metric_scope") == "aggregate_policy"
    }


def index_scan_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    out = {}
    for row in scan_policy_rows(rows):
        out[
            (
                str(row.get("adapter_episode_id")),
                str(row.get("task_context_id")),
                str(row.get("policy_id")),
            )
        ] = row
    return out


def index_best_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_plan[str(row.get("policy_plan_uid"))].append(row)
    best = {}
    for plan_uid, plan_rows in by_plan.items():
        ranked = sorted(
            plan_rows,
            key=lambda row: (
                finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) is None,
                finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) or float("inf"),
                int(row.get("visit_rank") or 10**9),
            ),
        )
        if ranked:
            best[plan_uid] = ranked[0]
    return best


def outcome(h001_hit: bool, baseline_hit: bool) -> str:
    if h001_hit and baseline_hit:
        return "both_success"
    if h001_hit and not baseline_hit:
        return "h001_only_success"
    if baseline_hit and not h001_hit:
        return "baseline_only_success"
    return "both_fail"


def classify_h001_failure(
    h001: dict[str, Any],
    detector: dict[str, Any],
    context: dict[str, Any],
    static: dict[str, Any],
) -> tuple[str, str]:
    h001_hit = bool(h001.get("primary_hit"))
    detector_hit = bool(detector.get("primary_hit"))
    context_hit = bool(context.get("primary_hit"))
    static_hit = bool(static.get("primary_hit"))
    h001_best = finite_float(h001.get("best_any_viewpoint_xz_m"))
    if h001_hit:
        return "h001_primary_hit", "trajectory execution can be tested after higher-priority failure rows are repaired"
    if detector_hit:
        if h001_best is not None and h001_best <= 1.5:
            return (
                "detector_only_success_h001_near_miss",
                "repair H001 threshold/candidate budget before trajectory execution",
            )
        return (
            "detector_only_success_h001_candidate_gap",
            "repair H001 current-observation fallback before trajectory execution",
        )
    if context_hit:
        return (
            "context_agnostic_success_h001_policy_loss",
            "inspect task-context memory-trust ordering before trajectory execution",
        )
    if static_hit:
        return (
            "static_memory_success_h001_policy_loss",
            "inspect stale-memory trust guard before trajectory execution",
        )
    if h001_best is not None and h001_best <= 1.5:
        return (
            "all_policy_miss_h001_near_miss",
            "inspect localization threshold and stop-position snapping before trajectory execution",
        )
    return (
        "all_policy_miss_candidate_source_gap",
        "expand or repair candidate source before trajectory execution",
    )


def build_episode_task_comparison_rows(
    metric_rows: list[dict[str, Any]],
    best_candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    index = index_scan_policy(metric_rows)
    h001_keys = sorted(
        (episode_id, task_context_id)
        for episode_id, task_context_id, policy_id in index
        if policy_id == H001_POLICY
    )
    rows = []
    for episode_id, task_context_id in h001_keys:
        h001 = index.get((episode_id, task_context_id, H001_POLICY), {})
        detector = index.get((episode_id, task_context_id, "real_detector_confidence_expanded_v0"), {})
        context = index.get((episode_id, task_context_id, "real_context_agnostic_memory_trust_reobserve_v0"), {})
        static = index.get((episode_id, task_context_id, "real_static_memory_proxy_v0"), {})
        failure_type, next_test = classify_h001_failure(h001, detector, context, static)
        h001_best = best_candidates.get(str(h001.get("policy_plan_uid")), {})
        detector_best = best_candidates.get(str(detector.get("policy_plan_uid")), {})
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": h001.get("scan_id"),
                "scene_key": h001.get("scene_key"),
                "object_category": h001.get("object_category"),
                "task_context_id": task_context_id,
                "h001_primary_hit": bool(h001.get("primary_hit")),
                "detector_primary_hit": bool(detector.get("primary_hit")),
                "context_agnostic_primary_hit": bool(context.get("primary_hit")),
                "static_primary_hit": bool(static.get("primary_hit")),
                "h001_vs_detector_outcome": outcome(
                    bool(h001.get("primary_hit")), bool(detector.get("primary_hit"))
                ),
                "h001_vs_context_agnostic_outcome": outcome(
                    bool(h001.get("primary_hit")), bool(context.get("primary_hit"))
                ),
                "h001_vs_static_outcome": outcome(
                    bool(h001.get("primary_hit")), bool(static.get("primary_hit"))
                ),
                "h001_best_any_viewpoint_xz_m": h001.get("best_any_viewpoint_xz_m"),
                "detector_best_any_viewpoint_xz_m": detector.get("best_any_viewpoint_xz_m"),
                "context_agnostic_best_any_viewpoint_xz_m": context.get("best_any_viewpoint_xz_m"),
                "static_best_any_viewpoint_xz_m": static.get("best_any_viewpoint_xz_m"),
                "h001_minus_detector_best_any_viewpoint_xz_m": delta(
                    h001.get("best_any_viewpoint_xz_m"), detector.get("best_any_viewpoint_xz_m")
                ),
                "h001_primary_spl_proxy": h001.get("primary_spl_proxy"),
                "detector_primary_spl_proxy": detector.get("primary_spl_proxy"),
                "context_agnostic_primary_spl_proxy": context.get("primary_spl_proxy"),
                "h001_minus_detector_spl_proxy": delta(
                    h001.get("primary_spl_proxy"), detector.get("primary_spl_proxy")
                ),
                "h001_minus_context_agnostic_spl_proxy": delta(
                    h001.get("primary_spl_proxy"), context.get("primary_spl_proxy")
                ),
                "h001_candidate_rows": h001.get("candidate_rows"),
                "detector_candidate_rows": detector.get("candidate_rows"),
                "h001_best_candidate_source_role": h001_best.get("source_role"),
                "h001_best_candidate_order_component": h001_best.get("candidate_order_component"),
                "h001_best_candidate_visit_rank": h001_best.get("visit_rank"),
                "detector_best_candidate_source_role": detector_best.get("source_role"),
                "detector_best_candidate_order_component": detector_best.get("candidate_order_component"),
                "detector_best_candidate_visit_rank": detector_best.get("visit_rank"),
                "failure_type": failure_type,
                "next_test": next_test,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    h001.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                )
                or bool(detector.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
                or bool(context.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
                or bool(static.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
            }
        )
    return rows


def build_baseline_delta_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = aggregate_policy_rows(metric_rows)
    h001 = aggregates.get(H001_POLICY, {})
    rows = []
    for baseline_id in BASELINE_POLICIES:
        baseline = aggregates.get(baseline_id, {})
        rows.append(
            {
                "version": VERSION,
                "h001_policy_id": H001_POLICY,
                "baseline_policy_id": baseline_id,
                "h001_primary_success_rows": h001.get("primary_success_rows"),
                "baseline_primary_success_rows": baseline.get("primary_success_rows"),
                "primary_success_rows_delta_h001_minus_baseline": delta(
                    h001.get("primary_success_rows"), baseline.get("primary_success_rows")
                ),
                "h001_primary_proxy_sr": h001.get("primary_proxy_sr"),
                "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
                "primary_proxy_sr_delta_h001_minus_baseline": delta(
                    h001.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")
                ),
                "h001_primary_spl_proxy_mean": h001.get("primary_spl_proxy_mean"),
                "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
                "primary_spl_proxy_delta_h001_minus_baseline": delta(
                    h001.get("primary_spl_proxy_mean"), baseline.get("primary_spl_proxy_mean")
                ),
                "h001_goal_xz_1p0_proxy_sr": h001.get("goal_xz_1p0_proxy_sr"),
                "baseline_goal_xz_1p0_proxy_sr": baseline.get("goal_xz_1p0_proxy_sr"),
                "goal_xz_1p0_delta_h001_minus_baseline": delta(
                    h001.get("goal_xz_1p0_proxy_sr"), baseline.get("goal_xz_1p0_proxy_sr")
                ),
                "claim_status": "diagnostic_goal_eval_proxy_not_real_navigation",
            }
        )
    return rows


def build_pair_outcome_rows(
    episode_task_rows: list[dict[str, Any]],
    baseline_delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    baseline_to_field = {
        "real_detector_confidence_expanded_v0": "h001_vs_detector_outcome",
        "real_context_agnostic_memory_trust_reobserve_v0": "h001_vs_context_agnostic_outcome",
        "real_static_memory_proxy_v0": "h001_vs_static_outcome",
    }
    deltas = {row["baseline_policy_id"]: row for row in baseline_delta_rows}
    for baseline_id, field in baseline_to_field.items():
        counts = Counter(row.get(field) for row in episode_task_rows)
        delta_row = deltas.get(baseline_id, {})
        rows.append(
            {
                "version": VERSION,
                "h001_policy_id": H001_POLICY,
                "baseline_policy_id": baseline_id,
                "comparison_rows": len(episode_task_rows),
                "both_success": counts.get("both_success", 0),
                "h001_only_success": counts.get("h001_only_success", 0),
                "baseline_only_success": counts.get("baseline_only_success", 0),
                "both_fail": counts.get("both_fail", 0),
                "primary_success_rows_delta_h001_minus_baseline": delta_row.get(
                    "primary_success_rows_delta_h001_minus_baseline"
                ),
                "primary_proxy_sr_delta_h001_minus_baseline": delta_row.get(
                    "primary_proxy_sr_delta_h001_minus_baseline"
                ),
                "primary_spl_proxy_delta_h001_minus_baseline": delta_row.get(
                    "primary_spl_proxy_delta_h001_minus_baseline"
                ),
            }
        )
    return rows


def build_failure_taxonomy_rows(episode_task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in episode_task_rows:
        if row.get("h001_primary_hit"):
            continue
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "failure_type": row.get("failure_type"),
                "h001_vs_detector_outcome": row.get("h001_vs_detector_outcome"),
                "h001_best_any_viewpoint_xz_m": row.get("h001_best_any_viewpoint_xz_m"),
                "detector_best_any_viewpoint_xz_m": row.get("detector_best_any_viewpoint_xz_m"),
                "h001_best_candidate_source_role": row.get("h001_best_candidate_source_role"),
                "h001_best_candidate_order_component": row.get("h001_best_candidate_order_component"),
                "detector_best_candidate_order_component": row.get("detector_best_candidate_order_component"),
                "next_test": row.get("next_test"),
            }
        )
    return rows


def build_gate_rows(
    m27_coverage: dict[str, Any],
    baseline_delta_rows: list[dict[str, Any]],
    episode_count: int,
) -> list[dict[str, Any]]:
    deltas = {row["baseline_policy_id"]: row for row in baseline_delta_rows}
    vs_static = deltas.get("real_static_memory_proxy_v0", {})
    vs_context = deltas.get("real_context_agnostic_memory_trust_reobserve_v0", {})
    vs_detector = deltas.get("real_detector_confidence_expanded_v0", {})

    def status_from_delta(value: object, *, allow_equal: bool = False) -> str:
        num = finite_float(value)
        if num is None:
            return "fail"
        if num > 0:
            return "pass"
        if allow_equal and num == 0:
            return "warning"
        return "fail"

    rows = [
        {
            "version": VERSION,
            "gate_id": "leakage_guard",
            "status": "pass" if m27_coverage.get("leakage_audit_pass") else "fail",
            "evidence": f"leakage_audit_pass={m27_coverage.get('leakage_audit_pass')}",
            "decision_effect": "required_for_any_next_step",
        },
        {
            "version": VERSION,
            "gate_id": "beats_static_memory",
            "status": status_from_delta(vs_static.get("primary_success_rows_delta_h001_minus_baseline")),
            "evidence": f"success_delta={vs_static.get('primary_success_rows_delta_h001_minus_baseline')}",
            "decision_effect": "supports_memory_update_over_static_baseline",
        },
        {
            "version": VERSION,
            "gate_id": "beats_context_agnostic_memory_trust",
            "status": status_from_delta(
                vs_context.get("primary_success_rows_delta_h001_minus_baseline"), allow_equal=True
            ),
            "evidence": (
                f"success_delta={vs_context.get('primary_success_rows_delta_h001_minus_baseline')}; "
                f"spl_delta={vs_context.get('primary_spl_proxy_delta_h001_minus_baseline')}"
            ),
            "decision_effect": "warning_if_only_spl_not_success_improves",
        },
        {
            "version": VERSION,
            "gate_id": "beats_detector_confidence",
            "status": status_from_delta(vs_detector.get("primary_success_rows_delta_h001_minus_baseline")),
            "evidence": (
                f"success_delta={vs_detector.get('primary_success_rows_delta_h001_minus_baseline')}; "
                f"sr_delta={vs_detector.get('primary_proxy_sr_delta_h001_minus_baseline')}"
            ),
            "decision_effect": "blocks_positive_h001_navigation_proxy_claim_if_fail",
        },
        {
            "version": VERSION,
            "gate_id": "true_dynamic_stale_memory_source",
            "status": "fail" if m27_coverage.get("h001_initial_memory_proxy_not_true_dynamic_stale_memory") else "pass",
            "evidence": (
                "initial_memory_proxy_not_true_dynamic_stale_memory="
                f"{m27_coverage.get('h001_initial_memory_proxy_not_true_dynamic_stale_memory')}"
            ),
            "decision_effect": "blocks_dynamic_stale_memory_claim_on_hm3d",
        },
        {
            "version": VERSION,
            "gate_id": "navigation_scale",
            "status": "pass" if episode_count >= MIN_SCALE_EPISODES_FOR_TRAJECTORY_CLAIM else "fail",
            "evidence": f"episode_count={episode_count}; required>={MIN_SCALE_EPISODES_FOR_TRAJECTORY_CLAIM}",
            "decision_effect": "blocks_paper_navigation_claim_if_fail",
        },
        {
            "version": VERSION,
            "gate_id": "h001_trajectory_execution_ready_now",
            "status": "fail",
            "evidence": "M27 is goal-eval proxy only and H001 underperforms detector-confidence ranking.",
            "decision_effect": "select_repair_before_trajectory_execution",
        },
    ]
    return rows


def write_report(
    path: Path,
    coverage: dict[str, Any],
    baseline_delta_rows: list[dict[str, Any]],
    pair_outcome_rows: list[dict[str, Any]],
    failure_taxonomy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M28 H001 Goal-Evaluation Comparison",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Episode-task comparison rows: {coverage['episode_task_comparison_rows']}.",
        f"- H001 primary success rows: {coverage['h001_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Detector-confidence primary success rows: {coverage['detector_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Context-agnostic primary success rows: {coverage['context_agnostic_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Static-memory primary success rows: {coverage['static_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- H001-vs-detector detector-only rows: {coverage['h001_vs_detector_baseline_only_rows']}.",
        f"- H001 failure rows: {coverage['h001_failure_rows']}.",
        f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
        "",
        "## Baseline Deltas",
        "",
        "| Baseline | Success delta | SR delta | SPL delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in baseline_delta_rows:
        lines.append(
            "| `{}` | {} | {} | {} |".format(
                row["baseline_policy_id"],
                row.get("primary_success_rows_delta_h001_minus_baseline"),
                row.get("primary_proxy_sr_delta_h001_minus_baseline"),
                row.get("primary_spl_proxy_delta_h001_minus_baseline"),
            )
        )
    lines.extend(
        [
            "",
            "## Pair Outcomes",
            "",
            "| Baseline | both success | H001 only | baseline only | both fail |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in pair_outcome_rows:
        lines.append(
            "| `{}` | {} | {} | {} | {} |".format(
                row["baseline_policy_id"],
                row["both_success"],
                row["h001_only_success"],
                row["baseline_only_success"],
                row["both_fail"],
            )
        )
    lines.extend(
        [
            "",
            "## Failure Taxonomy",
            "",
            "| Failure type | Rows |",
            "| --- | ---: |",
        ]
    )
    for failure_type, count in Counter(row["failure_type"] for row in failure_taxonomy_rows).most_common():
        lines.append(f"| `{failure_type}` | {count} |")
    lines.extend(
        [
            "",
            "## Trajectory Gate",
            "",
            "| Gate | Status | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for row in gate_rows:
        lines.append(f"| `{row['gate_id']}` | `{row['status']}` | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M28 supports a leakage-safe comparison and route decision only.",
            "- M28 does not support positive H001 real navigation `SR` / `SPL`.",
            "- H001 is better than static memory but not better than detector-confidence ranking in this 6-episode proxy.",
            "- Structured task context remains secondary because H001 does not improve success over context-agnostic memory trust.",
            "",
            "## Next",
            "",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m27_coverage = read_json(M27_DIR / "coverage.json")
    m22_coverage = read_json(M22_DIR / "coverage.json")
    metric_rows = read_jsonl(M27_DIR / "h001_policy_goal_metric_rows.jsonl")
    candidate_rows = read_jsonl(M27_DIR / "h001_candidate_goal_eval_rows.jsonl")

    best_candidates = index_best_candidate(candidate_rows)
    episode_task_rows = build_episode_task_comparison_rows(metric_rows, best_candidates)
    baseline_delta_rows = build_baseline_delta_rows(metric_rows)
    pair_outcome_rows = build_pair_outcome_rows(episode_task_rows, baseline_delta_rows)
    failure_taxonomy_rows = build_failure_taxonomy_rows(episode_task_rows)
    episode_count = len({row.get("adapter_episode_id") for row in episode_task_rows})
    gate_rows = build_gate_rows(m27_coverage, baseline_delta_rows, episode_count)

    pair_outcomes = {row["baseline_policy_id"]: row for row in pair_outcome_rows}
    aggregates = aggregate_policy_rows(metric_rows)
    h001_aggregate = aggregates.get(H001_POLICY, {})
    detector_aggregate = aggregates.get("real_detector_confidence_expanded_v0", {})
    context_aggregate = aggregates.get("real_context_agnostic_memory_trust_reobserve_v0", {})
    static_aggregate = aggregates.get("real_static_memory_proxy_v0", {})
    failure_counts = Counter(row["failure_type"] for row in failure_taxonomy_rows)
    gate_counts = Counter(row["status"] for row in gate_rows)
    trajectory_execution_recommended_now = (
        gate_counts.get("fail", 0) == 0
        and pair_outcomes.get("real_detector_confidence_expanded_v0", {}).get("baseline_only_success", 1) == 0
    )
    selected_next_unit = (
        "E008-M30 H001 trajectory execution smoke"
        if trajectory_execution_recommended_now
        else "E008-M29 H001 current-observation fallback/source repair contract"
    )
    route_decision = {
        "version": VERSION,
        "decision": "repair_h001_before_trajectory_execution"
        if not trajectory_execution_recommended_now
        else "trajectory_execution_smoke_ready",
        "reason": (
            "H001 is better than static memory but loses to detector-confidence ranking on M27 GoalEvalProxy; "
            "repair current-observation fallback/source policy before spending Docker trajectory execution."
        )
        if not trajectory_execution_recommended_now
        else "All trajectory gates passed.",
        "selected_next_unit": selected_next_unit,
        "launch_long_job_now": False,
        "h001_trajectory_execution_recommended_now": trajectory_execution_recommended_now,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }
    claim_boundary_rows = [
        {
            "version": VERSION,
            "claim_id": "supported_h001_beats_static_memory_goal_proxy",
            "supported": True,
            "claim_boundary": "H001 improves over static memory on M27 GoalEvalProxy but this is not real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_h001_beats_detector_confidence_goal_proxy",
            "supported": False,
            "claim_boundary": "Detector-confidence ranking has higher primary GoalEvalProxySR than H001 on the current 6-episode smoke.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context changes SPL/cost behavior but does not improve success over context-agnostic memory trust.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_h001_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "H001 has not been trajectory-executed and currently fails the detector-confidence proxy gate.",
        },
    ]

    coverage = {
        "version": VERSION,
        "status": "e008_m28_h001_goal_eval_comparison_decision_ready_repair_first"
        if not trajectory_execution_recommended_now
        else "e008_m28_h001_goal_eval_comparison_decision_ready_trajectory_next",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m27_status": m27_coverage.get("status"),
        "m22_status": m22_coverage.get("status"),
        "episode_count": episode_count,
        "episode_task_comparison_rows": len(episode_task_rows),
        "scan_policy_rows_per_policy": h001_aggregate.get("scan_policy_rows"),
        "baseline_delta_rows": len(baseline_delta_rows),
        "pair_outcome_rows": len(pair_outcome_rows),
        "failure_taxonomy_rows": len(failure_taxonomy_rows),
        "trajectory_gate_rows": len(gate_rows),
        "trajectory_gate_pass": gate_counts.get("pass", 0),
        "trajectory_gate_warning": gate_counts.get("warning", 0),
        "trajectory_gate_fail": gate_counts.get("fail", 0),
        "h001_primary_success_rows": h001_aggregate.get("primary_success_rows"),
        "detector_primary_success_rows": detector_aggregate.get("primary_success_rows"),
        "context_agnostic_primary_success_rows": context_aggregate.get("primary_success_rows"),
        "static_primary_success_rows": static_aggregate.get("primary_success_rows"),
        "h001_primary_proxy_sr": h001_aggregate.get("primary_proxy_sr"),
        "detector_primary_proxy_sr": detector_aggregate.get("primary_proxy_sr"),
        "context_agnostic_primary_proxy_sr": context_aggregate.get("primary_proxy_sr"),
        "static_primary_proxy_sr": static_aggregate.get("primary_proxy_sr"),
        "h001_vs_detector_baseline_only_rows": pair_outcomes.get(
            "real_detector_confidence_expanded_v0", {}
        ).get("baseline_only_success"),
        "h001_vs_detector_h001_only_rows": pair_outcomes.get("real_detector_confidence_expanded_v0", {}).get(
            "h001_only_success"
        ),
        "h001_vs_context_success_delta": next(
            (
                row.get("primary_success_rows_delta_h001_minus_baseline")
                for row in baseline_delta_rows
                if row.get("baseline_policy_id") == "real_context_agnostic_memory_trust_reobserve_v0"
            ),
            None,
        ),
        "h001_vs_detector_success_delta": next(
            (
                row.get("primary_success_rows_delta_h001_minus_baseline")
                for row in baseline_delta_rows
                if row.get("baseline_policy_id") == "real_detector_confidence_expanded_v0"
            ),
            None,
        ),
        "h001_failure_rows": len(failure_taxonomy_rows),
        "failure_type_counts": dict(failure_counts),
        "leakage_audit_pass": m27_coverage.get("leakage_audit_pass"),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in episode_task_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "h001_trajectory_execution_recommended_now": trajectory_execution_recommended_now,
        "repair_recommended_before_trajectory_execution": not trajectory_execution_recommended_now,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next_unit,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "h001_baseline_delta_rows.jsonl", baseline_delta_rows)
    write_jsonl(ARTIFACT_DIR / "episode_task_comparison_rows.jsonl", episode_task_rows)
    write_jsonl(ARTIFACT_DIR / "pair_outcome_rows.jsonl", pair_outcome_rows)
    write_jsonl(ARTIFACT_DIR / "failure_taxonomy_rows.jsonl", failure_taxonomy_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", [route_decision])
    write_report(
        ARTIFACT_DIR / "report.md",
        coverage,
        baseline_delta_rows,
        pair_outcome_rows,
        failure_taxonomy_rows,
        gate_rows,
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "h001_baseline_delta_rows.jsonl", baseline_delta_rows)
    write_jsonl(DATA_OUT_DIR / "episode_task_comparison_rows.jsonl", episode_task_rows)
    write_jsonl(DATA_OUT_DIR / "failure_taxonomy_rows.jsonl", failure_taxonomy_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
