#!/usr/bin/env python3
"""Evaluate M201 additive union rows against ObjectNav targets as eval-only labels."""

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

VERSION = "e008_m202_additive_source_pool_candidate_union_goal_evaluation_proxy_v0"
READY_STATUS = "e008_m202_additive_source_pool_candidate_union_goal_evaluation_proxy_ready"
BLOCKED_STATUS = "e008_m202_additive_source_pool_candidate_union_goal_evaluation_proxy_blocked"
NEXT_UNIT = "E008-M203 additive source-pool candidate-union proxy result interpretation and trajectory decision"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M202_additive_source_pool_candidate_union_goal_evaluation_proxy_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M202_additive_source_pool_candidate_union_goal_evaluation_proxy_v0"
)

M70_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
M197_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
M201_DIR = EXP_ROOT / "artifacts" / "E008-M201_additive_source_pool_candidate_union_row_materialization_v0"

PRIMARY_METRIC = "any_viewpoint_xz_1p0"
SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
BASELINE_ONLY_POLICY = "no_source_pool_detector_confidence_reachable_subset_v0"
SOURCE_POOL_REPLACEMENT_NEGATIVE = "source_pool_replacement_detector_confidence_reachable_subset_v0"
UNGUARDED_UNION_ABLATION = "additive_union_unguarded_confidence_sort_v0"


def load_m12_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m12_goal_eval_for_m202", M12_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M12_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def safe_ratio(num: int, den: int) -> float | None:
    return float(num / den) if den else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_eval_label_lookup(
    m70_candidate_goal_rows: list[dict[str, Any]],
    m197_candidate_goal_rows: list[dict[str, Any]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for source_id, rows in [("M70", m70_candidate_goal_rows), ("M197", m197_candidate_goal_rows)]:
        for row in rows:
            if row.get("policy_id") != "detector_confidence_reachable_subset_v0":
                continue
            key = (source_id, str(row.get("adapter_episode_id")), str(row.get("proposal_uid")))
            lookup[key] = row
    return lookup


def copy_eval_field(label_row: dict[str, Any], key: str) -> Any:
    return label_row.get(key)


def build_candidate_goal_eval_rows(
    union_policy_rows: list[dict[str, Any]],
    eval_label_lookup: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in union_policy_rows:
        label_row = eval_label_lookup.get(
            (
                str(row.get("m202_eval_source")),
                str(row.get("adapter_episode_id")),
                str(row.get("proposal_uid")),
            ),
            {},
        )
        primary_hit = bool(label_row.get("hit_any_viewpoint_xz_1p0"))
        out.append(
            {
                "version": VERSION,
                "policy_id": row.get("policy_id"),
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "visit_rank": row.get("visit_rank"),
                "union_rank": row.get("union_rank"),
                "proposal_uid": row.get("proposal_uid"),
                "raw_candidate_uid": row.get("raw_candidate_uid"),
                "label_canonical": row.get("label_canonical"),
                "candidate_source_family": row.get("candidate_source_family"),
                "union_action": row.get("union_action"),
                "m202_eval_source": row.get("m202_eval_source"),
                "path_ready": bool(row.get("path_ready")),
                "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
                "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
                "cumulative_known_path_cost_m": row.get("cumulative_known_path_cost_m"),
                "candidate_snapped_position_m": row.get("candidate_snapped_position_m") if row.get("path_ready") else None,
                "eval_goal_position": copy_eval_field(label_row, "eval_goal_position"),
                "eval_goal_object_id": copy_eval_field(label_row, "eval_goal_object_id"),
                "eval_viewpoint_count": copy_eval_field(label_row, "eval_viewpoint_count"),
                "eval_all_viewpoint_count_loaded": copy_eval_field(label_row, "eval_all_viewpoint_count_loaded") or 0,
                "candidate_to_eval_goal_xz_m": copy_eval_field(label_row, "candidate_to_eval_goal_xz_m"),
                "candidate_to_eval_goal_3d_m": copy_eval_field(label_row, "candidate_to_eval_goal_3d_m"),
                "candidate_to_eval_first_viewpoint_xz_m": copy_eval_field(label_row, "candidate_to_eval_first_viewpoint_xz_m"),
                "candidate_to_eval_first_viewpoint_3d_m": copy_eval_field(label_row, "candidate_to_eval_first_viewpoint_3d_m"),
                "candidate_to_nearest_eval_viewpoint_xz_m": copy_eval_field(label_row, "candidate_to_nearest_eval_viewpoint_xz_m"),
                "candidate_to_nearest_eval_viewpoint_3d_m": copy_eval_field(label_row, "candidate_to_nearest_eval_viewpoint_3d_m"),
                "hit_goal_xz_1p0": bool(label_row.get("hit_goal_xz_1p0")),
                "hit_goal_xz_1p5": bool(label_row.get("hit_goal_xz_1p5")),
                "hit_goal_xz_2p0": bool(label_row.get("hit_goal_xz_2p0")),
                "hit_any_viewpoint_xz_0p5": bool(label_row.get("hit_any_viewpoint_xz_0p5")),
                "hit_any_viewpoint_xz_1p0": primary_hit,
                "hit_any_viewpoint_xz_1p5": bool(label_row.get("hit_any_viewpoint_xz_1p5")),
                "hit_first_viewpoint_xz_1p0": bool(label_row.get("hit_first_viewpoint_xz_1p0")),
                "oracle_viewpoint_path_m": copy_eval_field(label_row, "oracle_viewpoint_path_m"),
                "oracle_goal_snapped_path_m": copy_eval_field(label_row, "oracle_goal_snapped_path_m"),
                "episode_eval_geodesic_distance_m": copy_eval_field(label_row, "episode_eval_geodesic_distance_m"),
                "policy_input_allowed": bool(row.get("policy_input_allowed")),
                "uses_objectnav_eval_goal_for_policy": False,
                "uses_objectnav_eval_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "source_boundary_status": row.get("source_boundary_status"),
                "source_ready_after_m195": bool(row.get("source_ready_after_m195")),
                "source_gap_after_m195": bool(row.get("source_gap_after_m195")),
                "primary_eval_metric": PRIMARY_METRIC,
                "primary_eval_hit": primary_hit,
                "eval_label_joined": bool(label_row),
            }
        )
    return out


def zero_scan_metric_row(policy_id: str, goal_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "metric_scope": "m202_scan_policy_goal_eval",
        "policy_id": policy_id,
        "scan_id": f"hm3dnav_{str(goal_row.get('scene_key')).replace('-', '_')}_ep{goal_row.get('source_episode_id')}",
        "adapter_episode_id": goal_row.get("adapter_episode_id"),
        "scene_key": goal_row.get("scene_key"),
        "object_category": goal_row.get("object_category"),
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
        "source_boundary_status": "no_policy_candidate_rows_for_episode",
        "source_ready_after_m195": False,
        "source_gap_after_m195": True,
        "zero_filled_for_full_denominator": True,
    }


def normalize_scan_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        enriched = dict(row)
        enriched["version"] = VERSION
        enriched["metric_scope"] = "m202_scan_policy_goal_eval"
        out.append(enriched)
    return out


def build_full_denominator_scan_metrics(
    m12: Any,
    candidate_goal_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    policy_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scan_metric_rows, _ = m12.build_metric_rows(candidate_goal_rows)
    scan_metric_rows = normalize_scan_metric_rows(scan_metric_rows)
    present = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id")))
        for row in scan_metric_rows
    }
    for policy_id in policy_ids:
        for goal_row in goal_rows:
            key = (policy_id, str(goal_row.get("adapter_episode_id")))
            if key not in present:
                scan_metric_rows.append(zero_scan_metric_row(policy_id, goal_row))
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_metric_rows:
        by_policy[str(row["policy_id"])].append(row)
    aggregate_rows = []
    for policy_id, policy_rows in sorted(by_policy.items()):
        aggregate = m12.summarize_policy_aggregate(policy_id, policy_rows)
        aggregate["version"] = VERSION
        aggregate["metric_scope"] = "m202_policy_goal_eval_aggregate"
        aggregate_rows.append(aggregate)
    return scan_metric_rows, aggregate_rows


def index_scan_metrics(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in rows
    }


def build_source_contribution_rows(scan_metric_rows: list[dict[str, Any]], candidate_goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = index_scan_metrics(scan_metric_rows)
    selected_candidates_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        if row.get("policy_id") == SELECTED_POLICY:
            selected_candidates_by_episode[str(row.get("adapter_episode_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for episode_id, candidates in sorted(selected_candidates_by_episode.items()):
        candidates.sort(key=lambda row: int(row.get("visit_rank") or 10**9))
        first_hit = next((row for row in candidates if row.get("hit_any_viewpoint_xz_1p0")), None)
        selected = metrics.get((SELECTED_POLICY, episode_id), {})
        baseline = metrics.get((BASELINE_ONLY_POLICY, episode_id), {})
        replacement = metrics.get((SOURCE_POOL_REPLACEMENT_NEGATIVE, episode_id), {})
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": selected.get("scan_id"),
                "scene_key": selected.get("scene_key"),
                "object_category": selected.get("object_category"),
                "selected_primary_hit": bool(selected.get("primary_hit")),
                "baseline_primary_hit": bool(baseline.get("primary_hit")),
                "replacement_primary_hit": bool(replacement.get("primary_hit")),
                "selected_first_hit_rank": selected.get("primary_first_hit_rank"),
                "selected_first_hit_source_family": first_hit.get("candidate_source_family") if first_hit else None,
                "selected_first_hit_union_action": first_hit.get("union_action") if first_hit else None,
                "selected_first_hit_proposal_uid": first_hit.get("proposal_uid") if first_hit else None,
                "source_pool_incremental_recovery": bool(selected.get("primary_hit"))
                and not bool(baseline.get("primary_hit")),
                "baseline_success_preserved": bool(baseline.get("primary_hit")) <= bool(selected.get("primary_hit")),
                "selected_minus_baseline_spl_proxy": (finite_float(selected.get("primary_spl_proxy")) or 0.0)
                - (finite_float(baseline.get("primary_spl_proxy")) or 0.0),
            }
        )
    return rows


def build_policy_comparison_rows(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy = {str(row.get("policy_id")): row for row in aggregate_rows}
    baseline = by_policy.get(BASELINE_ONLY_POLICY, {})
    rows: list[dict[str, Any]] = []
    for policy_id in [SELECTED_POLICY, SOURCE_POOL_REPLACEMENT_NEGATIVE, UNGUARDED_UNION_ABLATION]:
        row = by_policy.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "baseline_policy_id": BASELINE_ONLY_POLICY,
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_success_rows": row.get("primary_success_rows"),
                "baseline_primary_success_rows": baseline.get("primary_success_rows"),
                "delta_primary_success_rows": int(row.get("primary_success_rows") or 0)
                - int(baseline.get("primary_success_rows") or 0),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
                "delta_primary_proxy_sr": (finite_float(row.get("primary_proxy_sr")) or 0.0)
                - (finite_float(baseline.get("primary_proxy_sr")) or 0.0),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
                "delta_primary_spl_proxy_mean": (finite_float(row.get("primary_spl_proxy_mean")) or 0.0)
                - (finite_float(baseline.get("primary_spl_proxy_mean")) or 0.0),
                "candidate_rows": row.get("candidate_rows"),
                "baseline_candidate_rows": baseline.get("candidate_rows"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": row.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
            }
        )
    return rows


def build_failure_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in scan_metric_rows:
        if row.get("primary_hit"):
            continue
        rows.append(
            {
                "version": VERSION,
                "policy_id": row.get("policy_id"),
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "failure_type": "no_candidate_within_any_gt_viewpoint_xz_1p0",
                "candidate_rows": row.get("candidate_rows"),
                "best_any_viewpoint_xz_m": row.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": row.get("best_any_viewpoint_xz_rank"),
                "source_boundary_status": row.get("source_boundary_status"),
                "source_gap_after_m195": bool(row.get("source_gap_after_m195")),
                "claim_boundary": "M202 failure rows are leakage-safe proxy diagnostics, not executed navigation failures.",
            }
        )
    return rows


def build_leakage_audit_rows(candidate_goal_rows: list[dict[str, Any]], eval_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    policy_ids = sorted({str(row.get("policy_id")) for row in candidate_goal_rows})
    for policy_id in policy_ids:
        policy_rows = [row for row in candidate_goal_rows if row.get("policy_id") == policy_id]
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "candidate_goal_eval_rows": len(policy_rows),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "eval_goal_rows_joined": len({row.get("adapter_episode_id") for row in policy_rows if row.get("eval_goal_position")}),
                "loaded_all_viewpoint_episode_rows": sum(
                    1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
                ),
                "eval_label_joined_rows": sum(1 for row in policy_rows if row.get("eval_label_joined")),
                "policy_input_allowed_fields_only": True,
                "leakage_audit_pass": not any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows
                ),
            }
        )
    return rows


def build_claim_boundary_rows(positive_gate_pass: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_additive_union_proxy_eval",
            "supported": True,
            "claim_boundary": "M202 evaluates frozen M201 union rows against ObjectNav goals/viewpoints only as evaluation labels.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_repaired_proxy_improvement_gate",
            "supported": positive_gate_pass,
            "claim_boundary": "A repaired proxy improvement is supported only if selected additive union preserves protected baseline SR and improves proxy SPL or recovery count on the same 30 rows.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M202 is not a Habitat trajectory execution and cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M202 still requires trajectory execution, heldout transfer, and external navigation/search baseline comparison.",
        },
    ]


def build_route_decision_rows(ready: bool, positive_gate_pass: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_m203_proxy_result_interpretation_and_trajectory_decision"
            if ready
            else "repair_m202_goal_eval_proxy",
            "selected": ready,
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M202 additive source-pool candidate-union goal-evaluation proxy",
            "reason": "M202 proxy evaluation is leakage-safe; M203 must decide whether the proxy gate is strong enough for Docker trajectory planning."
            if ready and positive_gate_pass
            else "M202 proxy evaluation is leakage-safe but positive gate is weak or negative; M203 must record the boundary before trajectory planning."
            if ready
            else "M202 rows are incomplete or leak eval-only fields.",
            "positive_proxy_gate_pass": positive_gate_pass,
            "trajectory_execution_allowed_after_m202": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    source_contribution_rows: list[dict[str, Any]],
) -> str:
    source_counts = Counter(
        str(row.get("selected_first_hit_source_family"))
        for row in source_contribution_rows
        if row.get("selected_primary_hit")
    )
    source_line = ", ".join(f"`{key}` {value}" for key, value in sorted(source_counts.items())) or "none"
    return f"""# E008-M202 Additive Source-Pool Candidate-Union Goal-Evaluation Proxy

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M201 status: `{coverage['m201_status']}`.
- Full denominator rows: {coverage['full_denominator_rows']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy metric rows: {coverage['scan_policy_metric_rows']}.
- Primary metric: `{coverage['primary_metric']}`.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Selected policy primary success: {coverage['selected_primary_success_rows']} / {coverage['full_denominator_rows']}.
- Baseline-only primary success: {coverage['baseline_primary_success_rows']} / {coverage['full_denominator_rows']}.
- Selected minus baseline success delta: {coverage['selected_minus_baseline_success_rows']}.
- Selected minus baseline proxy SPL delta: {fmt(coverage['selected_minus_baseline_spl_proxy_mean'])}.
- Source-pool incremental recovery rows: {coverage['source_pool_incremental_recovery_rows']}.
- Selected first-hit source counts: {source_line}.
- Positive proxy gate pass: {coverage['positive_proxy_gate_pass']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

{markdown_table(aggregate_rows, ['policy_id', 'primary_success_rows', 'scan_policy_rows', 'primary_proxy_sr', 'primary_spl_proxy_mean', 'primary_first_hit_rank_mean_over_success', 'candidate_rows'])}

## Comparison To Protected Baseline

{markdown_table(comparison_rows, ['policy_id', 'delta_primary_success_rows', 'delta_primary_proxy_sr', 'delta_primary_spl_proxy_mean', 'candidate_rows'])}

## Interpretation

M202 evaluates the frozen M201 visit order only after the policy rows are fixed. It can support a proxy-level repair gate if selected additive union preserves the protected baseline and improves recovery or proxy `SPL`. It still does not execute `Habitat` trajectories, so final real navigation `SR` / `SPL` remains blocked.
"""


def main() -> None:
    m12 = load_m12_module()
    m201_coverage = read_json(M201_DIR / "coverage.json")
    goal_rows = read_jsonl(M70_DIR / "full_val_mini_eval_goal_rows.jsonl")
    m70_candidate_goal_rows = read_jsonl(M70_DIR / "candidate_goal_eval_rows.jsonl")
    m197_candidate_goal_rows = read_jsonl(M197_DIR / "candidate_goal_eval_rows.jsonl")
    union_policy_rows = read_jsonl(M201_DIR / "union_policy_rows.jsonl")
    if not m201_coverage:
        raise SystemExit(f"missing {M201_DIR / 'coverage.json'}")
    if not goal_rows:
        raise SystemExit(f"missing {M70_DIR / 'full_val_mini_eval_goal_rows.jsonl'}")
    if not m70_candidate_goal_rows:
        raise SystemExit(f"missing {M70_DIR / 'candidate_goal_eval_rows.jsonl'}")
    if not m197_candidate_goal_rows:
        raise SystemExit(f"missing {M197_DIR / 'candidate_goal_eval_rows.jsonl'}")
    if not union_policy_rows:
        raise SystemExit(f"missing {M201_DIR / 'union_policy_rows.jsonl'}")

    eval_label_lookup = build_eval_label_lookup(m70_candidate_goal_rows, m197_candidate_goal_rows)
    eval_index = {
        str(row.get("adapter_episode_id")): {
            **row,
            "eval_all_viewpoint_count_loaded": max(
                [
                    int(label.get("eval_all_viewpoint_count_loaded") or 0)
                    for label in eval_label_lookup.values()
                    if label.get("adapter_episode_id") == row.get("adapter_episode_id")
                ]
                or [0]
            ),
        }
        for row in goal_rows
    }
    policy_ids = sorted({str(row.get("policy_id")) for row in union_policy_rows})
    candidate_goal_rows = build_candidate_goal_eval_rows(union_policy_rows, eval_label_lookup)
    scan_metric_rows, aggregate_rows = build_full_denominator_scan_metrics(
        m12,
        candidate_goal_rows,
        goal_rows,
        policy_ids,
    )
    policy_goal_metric_rows = scan_metric_rows + aggregate_rows
    source_contribution_rows = build_source_contribution_rows(scan_metric_rows, candidate_goal_rows)
    comparison_rows = build_policy_comparison_rows(aggregate_rows)
    failure_rows = build_failure_rows(scan_metric_rows)
    leakage_audit_rows = build_leakage_audit_rows(candidate_goal_rows, eval_index)
    by_policy = {str(row.get("policy_id")): row for row in aggregate_rows}
    selected = by_policy.get(SELECTED_POLICY, {})
    baseline = by_policy.get(BASELINE_ONLY_POLICY, {})
    selected_success = int(selected.get("primary_success_rows") or 0)
    baseline_success = int(baseline.get("primary_success_rows") or 0)
    selected_spl = finite_float(selected.get("primary_spl_proxy_mean")) or 0.0
    baseline_spl = finite_float(baseline.get("primary_spl_proxy_mean")) or 0.0
    selected_minus_baseline_success = selected_success - baseline_success
    selected_minus_baseline_spl = selected_spl - baseline_spl
    source_pool_incremental_recovery_rows = sum(
        1 for row in source_contribution_rows if row.get("source_pool_incremental_recovery")
    )
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    eval_label_join_pass = all(row.get("eval_label_joined") for row in candidate_goal_rows)
    denominator_ok = all(int(row.get("scan_policy_rows") or 0) == len(goal_rows) for row in aggregate_rows)
    positive_gate_pass = selected_success >= baseline_success and (
        selected_success > baseline_success or selected_spl > baseline_spl + 1e-12
    )
    ready = bool(aggregate_rows) and denominator_ok and leakage_pass and eval_label_join_pass
    claim_boundary_rows = build_claim_boundary_rows(positive_gate_pass)
    route_decision_rows = build_route_decision_rows(ready, positive_gate_pass)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m201_status": m201_coverage.get("status"),
        "full_denominator_rows": len(goal_rows),
        "policy_count": len(policy_ids),
        "policy_ids": policy_ids,
        "union_policy_rows": len(union_policy_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "eval_label_lookup_rows": len(eval_label_lookup),
        "eval_label_join_pass": eval_label_join_pass,
        "eval_label_joined_rows": sum(1 for row in candidate_goal_rows if row.get("eval_label_joined")),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_goal_metric_rows": len(policy_goal_metric_rows),
        "failure_rows": len(failure_rows),
        "source_contribution_rows": len(source_contribution_rows),
        "primary_metric": PRIMARY_METRIC,
        "selected_policy_id": SELECTED_POLICY,
        "baseline_policy_id": BASELINE_ONLY_POLICY,
        "selected_primary_success_rows": selected_success,
        "baseline_primary_success_rows": baseline_success,
        "selected_primary_proxy_sr": selected.get("primary_proxy_sr"),
        "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
        "selected_primary_spl_proxy_mean": selected.get("primary_spl_proxy_mean"),
        "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
        "selected_minus_baseline_success_rows": selected_minus_baseline_success,
        "selected_minus_baseline_proxy_sr": (finite_float(selected.get("primary_proxy_sr")) or 0.0)
        - (finite_float(baseline.get("primary_proxy_sr")) or 0.0),
        "selected_minus_baseline_spl_proxy_mean": selected_minus_baseline_spl,
        "source_pool_incremental_recovery_rows": source_pool_incremental_recovery_rows,
        "positive_proxy_gate_pass": positive_gate_pass,
        "denominator_audit_pass": denominator_ok,
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "m203_interpretation_ready": ready,
        "trajectory_execution_promoted": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_goal_metric_rows)
        write_jsonl(output_dir / "source_contribution_rows.jsonl", source_contribution_rows)
        write_jsonl(output_dir / "policy_comparison_rows.jsonl", comparison_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, comparison_rows, source_contribution_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
