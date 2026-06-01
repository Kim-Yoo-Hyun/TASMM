#!/usr/bin/env python3
"""Evaluate M76 repair rows against ObjectNav targets as eval-only labels."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
M70_TOOL = EXP_ROOT / "tools" / "run_m70_full_val_mini_detector_candidate_goal_evaluation_smoke.py"
M64_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M68_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M76_DIR = EXP_ROOT / "artifacts" / "E008-M76_source_gap_spl_repair_row_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0"
)

VERSION = "e008_m77_source_gap_spl_repair_goal_evaluation_smoke_v0"
READY_STATUS = "e008_m77_source_gap_spl_repair_goal_evaluation_smoke_ready"
BLOCKED_STATUS = "e008_m77_source_gap_spl_repair_goal_evaluation_smoke_blocked"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
GUARDED_POLICY = "spl_guarded_confidence_path_tail_budget5_v0"
SOURCE_PROBE_POLICY = "candidate_source_expansion_probe_v0"
EVAL_POLICIES = {BASELINE_POLICY, GUARDED_POLICY}
EVAL_SCOPES = ("full_rank", "budget5")


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
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def safe_ratio(num: int, den: int) -> float:
    return float(num / den) if den else 0.0


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def build_candidate_index(nav_rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index = {str(row.get("proposal_uid")): row for row in nav_rows if row.get("proposal_uid")}
    for row in repair_rows:
        proposal_uid = str(row.get("proposal_uid"))
        if proposal_uid in index:
            continue
        index[proposal_uid] = {
            "proposal_uid": proposal_uid,
            "snapped_position_m": row.get("snapped_position_m") or row.get("execution_stop_position_m"),
            "uses_objectnav_eval_goal": False,
            "uses_objectnav_eval_viewpoint": False,
        }
    return index


def enrich_candidate_goal_rows(
    goal_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    *,
    eval_budget_scope: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for goal_row, visit_row in zip(goal_rows, visit_rows):
        enriched = dict(goal_row)
        enriched.update(
            {
                "version": VERSION,
                "eval_budget_scope": eval_budget_scope,
                "policy_plan_uid": visit_row.get("policy_plan_uid"),
                "benchmark_row_uid": visit_row.get("benchmark_row_uid"),
                "task_context_id": visit_row.get("task_context_id"),
                "candidate_visit_uid": visit_row.get("candidate_visit_uid"),
                "source_candidate_visit_uid": visit_row.get("source_candidate_visit_uid"),
                "source_policy_id": visit_row.get("source_policy_id"),
                "source_visit_rank": visit_row.get("source_visit_rank"),
                "candidate_source_role": visit_row.get("candidate_source_role"),
                "frame_pose_role": visit_row.get("frame_pose_role"),
                "observation_pose_id": visit_row.get("observation_pose_id"),
                "repair_component": visit_row.get("repair_component"),
                "within_budget5": bool(visit_row.get("within_budget5")),
                "m76_budget_rank": visit_row.get("m76_budget_rank"),
                "goal_eval_in_next_unit": bool(visit_row.get("goal_eval_in_next_unit")),
                "execute_in_next_runner": bool(visit_row.get("execute_in_next_runner")),
                "probe_only": bool(visit_row.get("probe_only")),
                "policy_input_uses_eval_goal_or_viewpoint": bool(
                    visit_row.get("policy_input_uses_eval_goal_or_viewpoint")
                ),
                "policy_input_uses_success_label": bool(visit_row.get("policy_input_uses_success_label")),
                "uses_m70_proxy_success_for_filtering": bool(visit_row.get("uses_m70_proxy_success_for_filtering")),
                "uses_m71_failure_class_for_policy": bool(visit_row.get("uses_m71_failure_class_for_policy")),
                "uses_m73_trajectory_result_for_policy": bool(visit_row.get("uses_m73_trajectory_result_for_policy")),
                "claim_boundary": "M77 joins ObjectNav goal/viewpoint fields only for evaluation; these fields are not policy inputs.",
            }
        )
        out.append(enriched)
    return out


def enrich_metric_rows(
    scan_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    plan_index: dict[tuple[str, str], dict[str, Any]],
    *,
    eval_budget_scope: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched_scan: list[dict[str, Any]] = []
    for row in scan_rows:
        out = dict(row)
        out["version"] = VERSION
        out["eval_budget_scope"] = eval_budget_scope
        plan = plan_index.get((str(row.get("policy_id")), str(row.get("adapter_episode_id"))), {})
        out["policy_plan_uid"] = plan.get("policy_plan_uid")
        out["task_context_id"] = plan.get("task_context_id")
        out["diagnostic_source_gap_boundary_for_reporting"] = bool(
            plan.get("diagnostic_source_gap_boundary_for_reporting")
        )
        out["diagnostic_source_ready_failure_for_reporting"] = bool(
            plan.get("diagnostic_source_ready_failure_for_reporting")
        )
        out["goal_eval_in_next_unit"] = bool(plan.get("goal_eval_in_next_unit"))
        out["probe_only"] = bool(plan.get("probe_only"))
        out["claim_boundary"] = "M77 metric rows are proxy goal-evaluation diagnostics, not executed navigation SR/SPL."
        enriched_scan.append(out)

    enriched_aggregate: list[dict[str, Any]] = []
    for row in aggregate_rows:
        out = dict(row)
        out["version"] = VERSION
        out["eval_budget_scope"] = eval_budget_scope
        out["claim_boundary"] = "M77 aggregate rows are leakage-safe proxy diagnostics, not executed navigation SR/SPL."
        enriched_aggregate.append(out)
    return enriched_scan, enriched_aggregate


def evaluate_scope(
    m12: Any,
    visit_rows: list[dict[str, Any]],
    candidate_index: dict[str, dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
    plan_index: dict[tuple[str, str], dict[str, Any]],
    *,
    eval_budget_scope: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if eval_budget_scope == "budget5":
        scoped_visit_rows = [row for row in visit_rows if bool(row.get("within_budget5"))]
    else:
        scoped_visit_rows = list(visit_rows)
    raw_candidate_goal_rows = m12.build_candidate_goal_eval_rows(
        scoped_visit_rows,
        candidate_index,
        eval_index,
        oracle_index,
    )
    candidate_goal_rows = enrich_candidate_goal_rows(
        raw_candidate_goal_rows,
        scoped_visit_rows,
        eval_budget_scope=eval_budget_scope,
    )
    scan_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    scan_rows, aggregate_rows = enrich_metric_rows(
        scan_rows,
        aggregate_rows,
        plan_index,
        eval_budget_scope=eval_budget_scope,
    )
    failure_rows = m12.build_failure_rows(scan_rows)
    for row in failure_rows:
        row["version"] = VERSION
        row["eval_budget_scope"] = eval_budget_scope
        row["claim_boundary"] = "M77 failure rows are diagnostic and use eval labels only after policy rows are fixed."
    return candidate_goal_rows, scan_rows, aggregate_rows, failure_rows


def build_pairwise_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope_episode: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_rows:
        by_scope_episode[(str(row.get("eval_budget_scope")), str(row.get("adapter_episode_id")))][
            str(row.get("policy_id"))
        ] = row

    out: list[dict[str, Any]] = []
    for (scope, episode_id), policies in sorted(by_scope_episode.items()):
        baseline = policies.get(BASELINE_POLICY)
        method = policies.get(GUARDED_POLICY)
        if not baseline or not method:
            continue
        base_spl = finite_float(baseline.get("primary_spl_proxy")) or 0.0
        method_spl = finite_float(method.get("primary_spl_proxy")) or 0.0
        base_rank = finite_float(baseline.get("primary_first_hit_rank"))
        method_rank = finite_float(method.get("primary_first_hit_rank"))
        base_best_vp = finite_float(baseline.get("best_any_viewpoint_xz_m"))
        method_best_vp = finite_float(method.get("best_any_viewpoint_xz_m"))
        base_hit = bool(baseline.get("primary_hit"))
        method_hit = bool(method.get("primary_hit"))
        if method_hit and not base_hit:
            comparison = "guarded_gain"
        elif base_hit and not method_hit:
            comparison = "guarded_loss"
        elif method_hit and base_hit:
            comparison = "both_hit"
        else:
            comparison = "both_fail"
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_pairwise_delta",
                "eval_budget_scope": scope,
                "adapter_episode_id": episode_id,
                "scan_id": baseline.get("scan_id"),
                "scene_key": baseline.get("scene_key"),
                "object_category": baseline.get("object_category"),
                "baseline_policy_id": BASELINE_POLICY,
                "method_policy_id": GUARDED_POLICY,
                "baseline_primary_hit": base_hit,
                "method_primary_hit": method_hit,
                "comparison": comparison,
                "baseline_primary_first_hit_rank": baseline.get("primary_first_hit_rank"),
                "method_primary_first_hit_rank": method.get("primary_first_hit_rank"),
                "delta_primary_first_hit_rank": method_rank - base_rank
                if method_rank is not None and base_rank is not None
                else None,
                "baseline_primary_spl_proxy": base_spl,
                "method_primary_spl_proxy": method_spl,
                "delta_primary_spl_proxy": method_spl - base_spl,
                "baseline_best_any_viewpoint_xz_m": base_best_vp,
                "method_best_any_viewpoint_xz_m": method_best_vp,
                "delta_best_any_viewpoint_xz_m": method_best_vp - base_best_vp
                if method_best_vp is not None and base_best_vp is not None
                else None,
                "diagnostic_source_gap_boundary_for_reporting": bool(
                    baseline.get("diagnostic_source_gap_boundary_for_reporting")
                ),
                "diagnostic_source_ready_failure_for_reporting": bool(
                    baseline.get("diagnostic_source_ready_failure_for_reporting")
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    baseline.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                )
                or bool(method.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
                "claim_boundary": "Pairwise deltas are proxy diagnostics; no trajectory execution happened in M77.",
            }
        )
    return out


def aggregate_by_policy_scope(aggregate_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("eval_budget_scope")), str(row.get("policy_id"))): row
        for row in aggregate_rows
    }


def build_delta_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        grouped[str(row.get("eval_budget_scope"))].append(row)
    out: list[dict[str, Any]] = []
    for scope, rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "row_type": "policy_delta_summary",
                "eval_budget_scope": scope,
                "episode_rows": len(rows),
                "guarded_gain_rows": sum(1 for row in rows if row.get("comparison") == "guarded_gain"),
                "guarded_loss_rows": sum(1 for row in rows if row.get("comparison") == "guarded_loss"),
                "both_hit_rows": sum(1 for row in rows if row.get("comparison") == "both_hit"),
                "both_fail_rows": sum(1 for row in rows if row.get("comparison") == "both_fail"),
                "source_gap_rows": sum(1 for row in rows if row.get("diagnostic_source_gap_boundary_for_reporting")),
                "source_gap_guarded_gain_rows": sum(
                    1
                    for row in rows
                    if row.get("diagnostic_source_gap_boundary_for_reporting")
                    and row.get("comparison") == "guarded_gain"
                ),
                "source_gap_guarded_loss_rows": sum(
                    1
                    for row in rows
                    if row.get("diagnostic_source_gap_boundary_for_reporting")
                    and row.get("comparison") == "guarded_loss"
                ),
                "delta_primary_spl_proxy_mean": mean(
                    [finite_float(row.get("delta_primary_spl_proxy")) for row in rows]
                ),
                "delta_rank_mean_over_both_hit": mean(
                    [
                        finite_float(row.get("delta_primary_first_hit_rank"))
                        for row in rows
                        if row.get("comparison") == "both_hit"
                    ]
                ),
                "claim_boundary": "M77 summaries compare fixed M76 orders and do not use eval labels for ranking.",
            }
        )
    return out


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        boundary = "source_gap" if row.get("diagnostic_source_gap_boundary_for_reporting") else "source_ready_or_other"
        if row.get("diagnostic_source_ready_failure_for_reporting"):
            boundary = "source_ready_threshold_failure"
        grouped[(str(row.get("eval_budget_scope")), str(row.get("policy_id")), boundary)].append(row)
    out: list[dict[str, Any]] = []
    for (scope, policy_id, boundary), rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "row_type": "source_boundary_goal_metric",
                "eval_budget_scope": scope,
                "policy_id": policy_id,
                "source_boundary": boundary,
                "episode_rows": len(rows),
                "primary_success_rows": sum(1 for row in rows if row.get("primary_hit")),
                "primary_proxy_sr": safe_ratio(sum(1 for row in rows if row.get("primary_hit")), len(rows)),
                "primary_spl_proxy_mean": mean(
                    [finite_float(row.get("primary_spl_proxy")) for row in rows]
                ),
                "claim_boundary": "Source-boundary rows are reporting-only diagnostics after policy materialization.",
            }
        )
    return out


def build_leakage_rows(candidate_goal_rows: list[dict[str, Any]], eval_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        grouped[(str(row.get("eval_budget_scope")), str(row.get("policy_id")))].append(row)
    rows: list[dict[str, Any]] = []
    for (scope, policy_id), items in sorted(grouped.items()):
        rows.append(
            {
                "version": VERSION,
                "row_type": "leakage_audit",
                "eval_budget_scope": scope,
                "policy_id": policy_id,
                "candidate_goal_eval_rows": len(items),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    item.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for item in items
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "policy_input_uses_eval_goal_or_viewpoint_rows": sum(
                    1 for item in items if item.get("policy_input_uses_eval_goal_or_viewpoint")
                ),
                "policy_input_uses_success_label_rows": sum(
                    1 for item in items if item.get("policy_input_uses_success_label")
                ),
                "uses_m70_proxy_success_for_filtering_rows": sum(
                    1 for item in items if item.get("uses_m70_proxy_success_for_filtering")
                ),
                "uses_m71_failure_class_for_policy_rows": sum(
                    1 for item in items if item.get("uses_m71_failure_class_for_policy")
                ),
                "uses_m73_trajectory_result_for_policy_rows": sum(
                    1 for item in items if item.get("uses_m73_trajectory_result_for_policy")
                ),
                "eval_goal_rows_joined": len(
                    {item["adapter_episode_id"] for item in items if item.get("eval_goal_position")}
                ),
                "loaded_all_viewpoint_episode_rows": sum(
                    1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
                ),
                "leakage_audit_pass": not any(
                    item.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                    or item.get("policy_input_uses_eval_goal_or_viewpoint")
                    or item.get("policy_input_uses_success_label")
                    or item.get("uses_m70_proxy_success_for_filtering")
                    or item.get("uses_m71_failure_class_for_policy")
                    or item.get("uses_m73_trajectory_result_for_policy")
                    for item in items
                ),
                "claim_boundary": "ObjectNav goal/viewpoint fields are metric-only fields in M77.",
            }
        )
    return rows


def gate_status(condition: bool) -> str:
    return "pass" if condition else "fail"


def build_gate_rows(
    *,
    missing_inputs: list[str],
    m76_coverage: dict[str, Any],
    leakage_pass: bool,
    aggregate_index: dict[tuple[str, str], dict[str, Any]],
    delta_summary_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    full_base = aggregate_index.get(("full_rank", BASELINE_POLICY), {})
    full_method = aggregate_index.get(("full_rank", GUARDED_POLICY), {})
    budget_base = aggregate_index.get(("budget5", BASELINE_POLICY), {})
    budget_method = aggregate_index.get(("budget5", GUARDED_POLICY), {})

    full_no_success_loss = int(full_method.get("primary_success_rows") or 0) >= int(
        full_base.get("primary_success_rows") or 0
    )
    budget_no_success_loss = int(budget_method.get("primary_success_rows") or 0) >= int(
        budget_base.get("primary_success_rows") or 0
    )
    budget_positive_gain = int(budget_method.get("primary_success_rows") or 0) > int(
        budget_base.get("primary_success_rows") or 0
    )
    full_spl_no_regression = (finite_float(full_method.get("primary_spl_proxy_mean")) or 0.0) >= (
        finite_float(full_base.get("primary_spl_proxy_mean")) or 0.0
    )
    budget_spl_no_regression = (finite_float(budget_method.get("primary_spl_proxy_mean")) or 0.0) >= (
        finite_float(budget_base.get("primary_spl_proxy_mean")) or 0.0
    )
    delta_by_scope = {str(row.get("eval_budget_scope")): row for row in delta_summary_rows}
    budget_source_gap_gain = int(delta_by_scope.get("budget5", {}).get("source_gap_guarded_gain_rows") or 0) > 0
    budget_source_gap_no_loss = int(delta_by_scope.get("budget5", {}).get("source_gap_guarded_loss_rows") or 0) == 0

    trajectory_contract_ready = (
        not missing_inputs
        and leakage_pass
        and full_no_success_loss
        and budget_no_success_loss
        and budget_spl_no_regression
        and (budget_positive_gain or budget_source_gap_gain or full_spl_no_regression)
    )
    selected_next = (
        "E008-M78 full-val-mini source-gap/SPL repair trajectory contract and Docker preflight"
        if trajectory_contract_ready
        else "E008-M78 full-val-mini source-gap/SPL repair result interpretation and next-route decision"
    )

    rows = [
        {
            "version": VERSION,
            "gate_id": "m76_ready",
            "gate_status": gate_status(m76_coverage.get("status") == "e008_m76_source_gap_spl_repair_row_materialization_smoke_ready"),
            "blocks_trajectory_contract": False,
            "rationale": "M76 repair row materialization must be ready before proxy evaluation.",
        },
        {
            "version": VERSION,
            "gate_id": "missing_inputs",
            "gate_status": gate_status(not missing_inputs),
            "blocks_trajectory_contract": bool(missing_inputs),
            "rationale": "M77 requires M64 episodes, M68 candidate navmesh rows, and M76 repair rows.",
        },
        {
            "version": VERSION,
            "gate_id": "leakage_audit",
            "gate_status": gate_status(leakage_pass),
            "blocks_trajectory_contract": not leakage_pass,
            "rationale": "Goal/viewpoint fields must be metric-only and never policy inputs.",
        },
        {
            "version": VERSION,
            "gate_id": "full_rank_no_success_loss",
            "gate_status": gate_status(full_no_success_loss),
            "blocks_trajectory_contract": not full_no_success_loss,
            "rationale": "Guarded policy should not lose full-rank proxy success against detector-confidence baseline.",
        },
        {
            "version": VERSION,
            "gate_id": "budget5_no_success_loss",
            "gate_status": gate_status(budget_no_success_loss),
            "blocks_trajectory_contract": not budget_no_success_loss,
            "rationale": "Deployable budget-5 variant cannot be promoted if it loses proxy success.",
        },
        {
            "version": VERSION,
            "gate_id": "budget5_positive_repair",
            "gate_status": "pass" if budget_positive_gain else "warning",
            "blocks_trajectory_contract": False,
            "rationale": "Positive budget-5 gain is preferred but not required if SPL/source-gap gates justify a trajectory check.",
        },
        {
            "version": VERSION,
            "gate_id": "budget5_spl_no_regression",
            "gate_status": gate_status(budget_spl_no_regression),
            "blocks_trajectory_contract": not budget_spl_no_regression,
            "rationale": "M75 selected an SPL guard; budget-5 SPL proxy regression would weaken the repair.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_budget5_no_loss",
            "gate_status": gate_status(budget_source_gap_no_loss),
            "blocks_trajectory_contract": not budget_source_gap_no_loss,
            "rationale": "Source-gap reporting rows are diagnostic, but guarded repair should not worsen them.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_contract_ready",
            "gate_status": gate_status(trajectory_contract_ready),
            "blocks_trajectory_contract": not trajectory_contract_ready,
            "rationale": "Only pass if M77 supports a leakage-safe repaired row set worth rerunning in Docker.",
        },
    ]
    return rows, selected_next


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_leakage_safe_repair_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M77 evaluates fixed M76 repair rows against ObjectNav target labels without policy leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repaired_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M77 does not execute Habitat trajectories and cannot report final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M77 can report source-gap proxy behavior, but source-gap recovery requires candidate-source evidence and trajectory validation.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M77 is a navigation proxy evaluation over current detector candidates, not a final RGB-D/open-vocabulary robustness benchmark.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M77 does not introduce a natural-language or human-intent understanding module.",
        },
    ]


def build_route_decision_rows(selected_next: str, gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fail_gates = [row["gate_id"] for row in gate_rows if row.get("gate_status") == "fail"]
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "selected_next_unit": selected_next,
            "failed_gates": fail_gates,
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "claim_boundary": "M77 does not launch a Docker trajectory job; M78 must fix the next contract or decision.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    delta_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    aggregate_lines = []
    for row in sorted(aggregate_rows, key=lambda item: (str(item.get("eval_budget_scope")), str(item.get("policy_id")))):
        aggregate_lines.append(
            "| {scope} | `{policy}` | {hits}/{denom} | {sr} | {spl} | {rank} | {vp15} | {goal10} |".format(
                scope=row.get("eval_budget_scope"),
                policy=row.get("policy_id"),
                hits=row.get("primary_success_rows"),
                denom=row.get("scan_policy_rows"),
                sr=fmt(row.get("primary_proxy_sr")),
                spl=fmt(row.get("primary_spl_proxy_mean")),
                rank=fmt(row.get("primary_first_hit_rank_mean_over_success")),
                vp15=fmt(row.get("any_viewpoint_xz_1p5_proxy_sr")),
                goal10=fmt(row.get("goal_xz_1p0_proxy_sr")),
            )
        )
    delta_lines = []
    for row in sorted(delta_summary_rows, key=lambda item: str(item.get("eval_budget_scope"))):
        delta_lines.append(
            "| {scope} | {gain} | {loss} | {both_hit} | {both_fail} | {spl_delta} | {sg_gain} | {sg_loss} |".format(
                scope=row.get("eval_budget_scope"),
                gain=row.get("guarded_gain_rows"),
                loss=row.get("guarded_loss_rows"),
                both_hit=row.get("both_hit_rows"),
                both_fail=row.get("both_fail_rows"),
                spl_delta=fmt(row.get("delta_primary_spl_proxy_mean")),
                sg_gain=row.get("source_gap_guarded_gain_rows"),
                sg_loss=row.get("source_gap_guarded_loss_rows"),
            )
        )
    gate_lines = [
        f"| `{row['gate_id']}` | {row['gate_status']} | {row['blocks_trajectory_contract']} |"
        for row in gate_rows
    ]
    return f"""# E008-M77 Source-Gap/SPL Repair Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M76 status: `{coverage['m76_status']}`.
- Eval episode rows: {coverage['eval_episode_rows']}.
- Repair visit rows evaluated: {coverage['repair_visit_rows_evaluated']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy metric rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Primary metric: `{coverage['primary_metric']}`.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| scope | policy_id | primary hits | proxy SR | proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Pairwise Delta

`{GUARDED_POLICY}` minus `{BASELINE_POLICY}`.

| scope | gain rows | loss rows | both hit | both fail | mean delta SPL proxy | source-gap gain | source-gap loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(delta_lines)}

## Gates

| gate_id | status | blocks trajectory contract |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M77 supports leakage-safe proxy evaluation of fixed M76 repair rows.
- M77 does not support final real navigation `SR` / `SPL`; no `Habitat` trajectory is executed here.
- M77 does not make `candidate_source_expansion_probe_v0` a final source-gap recovery policy.
"""


def sync_derived(skip_copy: bool) -> None:
    if skip_copy:
        return
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-derived-copy", action="store_true", help="Do not copy artifacts to local_dataset.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval_for_m77")
    m70 = load_module(M70_TOOL, "e008_m70_goal_eval_for_m77")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m76_coverage = read_json(M76_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_DIR / "val_mini_episode_rows.jsonl")
    nav_rows = read_jsonl(M68_DIR / "candidate_navmesh_validation_rows.jsonl")
    repair_rows = read_jsonl(M76_DIR / "repair_candidate_visit_order_rows.jsonl")
    plan_rows = read_jsonl(M76_DIR / "repair_execution_plan_rows.jsonl")

    missing_inputs: list[str] = []
    if not episode_rows:
        missing_inputs.append(str(M64_DIR / "val_mini_episode_rows.jsonl"))
    if not nav_rows:
        missing_inputs.append(str(M68_DIR / "candidate_navmesh_validation_rows.jsonl"))
    if not repair_rows:
        missing_inputs.append(str(M76_DIR / "repair_candidate_visit_order_rows.jsonl"))
    if not plan_rows:
        missing_inputs.append(str(M76_DIR / "repair_execution_plan_rows.jsonl"))
    if not m76_coverage:
        missing_inputs.append(str(M76_DIR / "coverage.json"))

    goal_rows = m70.build_full_val_mini_eval_goal_rows(episode_rows) if episode_rows else []
    eval_index = m12.build_eval_goal_index(goal_rows) if goal_rows else {}
    oracle_index = {str(row["adapter_episode_id"]): row for row in goal_rows}
    candidate_index = build_candidate_index(nav_rows, repair_rows)
    plan_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in plan_rows
    }

    eval_visit_rows = [
        row
        for row in repair_rows
        if row.get("policy_id") in EVAL_POLICIES
        and bool(row.get("goal_eval_in_next_unit"))
        and not bool(row.get("probe_only"))
    ]
    skipped_probe_rows = [
        row for row in repair_rows if row.get("policy_id") == SOURCE_PROBE_POLICY or bool(row.get("probe_only"))
    ]

    all_candidate_goal_rows: list[dict[str, Any]] = []
    all_scan_rows: list[dict[str, Any]] = []
    all_aggregate_rows: list[dict[str, Any]] = []
    all_failure_rows: list[dict[str, Any]] = []
    if not missing_inputs:
        for scope in EVAL_SCOPES:
            candidate_goal_rows, scan_rows, aggregate_rows, failure_rows = evaluate_scope(
                m12,
                eval_visit_rows,
                candidate_index,
                eval_index,
                oracle_index,
                plan_index,
                eval_budget_scope=scope,
            )
            all_candidate_goal_rows.extend(candidate_goal_rows)
            all_scan_rows.extend(scan_rows)
            all_aggregate_rows.extend(aggregate_rows)
            all_failure_rows.extend(failure_rows)

    leakage_rows = build_leakage_rows(all_candidate_goal_rows, eval_index)
    leakage_pass = bool(leakage_rows) and all(row.get("leakage_audit_pass") for row in leakage_rows)
    pairwise_rows = build_pairwise_rows(all_scan_rows)
    delta_summary_rows = build_delta_summary_rows(pairwise_rows)
    source_boundary_rows = build_source_boundary_rows(all_scan_rows)
    aggregate_index = aggregate_by_policy_scope(all_aggregate_rows)
    gate_rows, selected_next = build_gate_rows(
        missing_inputs=missing_inputs,
        m76_coverage=m76_coverage,
        leakage_pass=leakage_pass,
        aggregate_index=aggregate_index,
        delta_summary_rows=delta_summary_rows,
    )
    claim_boundary_rows = build_claim_boundary_rows()
    route_decision_rows = build_route_decision_rows(selected_next, gate_rows)
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in all_aggregate_rows]
    gate_fail_rows = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    gate_warning_rows = sum(1 for row in gate_rows if row.get("gate_status") == "warning")

    status = READY_STATUS
    if missing_inputs or not all_aggregate_rows or not leakage_pass:
        status = BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m76_status": m76_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "eval_episode_rows": len(goal_rows),
        "expected_eval_episode_rows": len(episode_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "repair_visit_rows_total": len(repair_rows),
        "repair_visit_rows_evaluated": len(eval_visit_rows),
        "skipped_probe_rows": len(skipped_probe_rows),
        "candidate_navmesh_rows": len(nav_rows),
        "candidate_goal_eval_rows": len(all_candidate_goal_rows),
        "scan_policy_metric_rows": len(all_scan_rows),
        "aggregate_policy_rows": len(all_aggregate_rows),
        "failure_rows": len(all_failure_rows),
        "pairwise_delta_rows": len(pairwise_rows),
        "delta_summary_rows": len(delta_summary_rows),
        "source_boundary_goal_metric_rows": len(source_boundary_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": leakage_pass,
        "gate_rows": len(gate_rows),
        "gate_fail_rows": gate_fail_rows,
        "gate_warning_rows": gate_warning_rows,
        "primary_metric": PRIMARY_METRIC,
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "policy_primary_metrics": {
            f"{scope}::{policy_id}": {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
            }
            for (scope, policy_id), row in aggregate_index.items()
        },
        "delta_summary": {
            str(row.get("eval_budget_scope")): {
                "guarded_gain_rows": row.get("guarded_gain_rows"),
                "guarded_loss_rows": row.get("guarded_loss_rows"),
                "both_hit_rows": row.get("both_hit_rows"),
                "both_fail_rows": row.get("both_fail_rows"),
                "delta_primary_spl_proxy_mean": row.get("delta_primary_spl_proxy_mean"),
                "source_gap_guarded_gain_rows": row.get("source_gap_guarded_gain_rows"),
                "source_gap_guarded_loss_rows": row.get("source_gap_guarded_loss_rows"),
            }
            for row in delta_summary_rows
        },
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "goal_evaluation_ready": status == READY_STATUS,
        "trajectory_contract_ready": any(
            row.get("gate_id") == "trajectory_contract_ready" and row.get("gate_status") == "pass"
            for row in gate_rows
        ),
        "trajectory_execution_ready_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    write_jsonl(ARTIFACT_DIR / "full_val_mini_eval_goal_rows.jsonl", goal_rows)
    write_jsonl(ARTIFACT_DIR / "repair_candidate_goal_eval_rows.jsonl", all_candidate_goal_rows)
    write_jsonl(ARTIFACT_DIR / "policy_goal_metric_rows.jsonl", all_scan_rows + all_aggregate_rows)
    write_jsonl(ARTIFACT_DIR / "scan_policy_goal_metric_rows.jsonl", all_scan_rows)
    write_jsonl(ARTIFACT_DIR / "aggregate_policy_goal_metric_rows.jsonl", all_aggregate_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", all_failure_rows)
    write_jsonl(ARTIFACT_DIR / "policy_pairwise_delta_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "policy_delta_summary_rows.jsonl", delta_summary_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_goal_metric_rows.jsonl", source_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, all_aggregate_rows, delta_summary_rows, gate_rows),
        encoding="utf-8",
    )

    sync_derived(bool(args.skip_derived_copy))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
