#!/usr/bin/env python3
"""Evaluate M80 loss-safe candidate-source expansion rows against ObjectNav targets."""

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
M80_DIR = EXP_ROOT / "artifacts" / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0"
)

VERSION = "e008_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0"
READY_STATUS = "e008_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_ready"
BLOCKED_STATUS = "e008_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_blocked"
NEXT_UNIT = "E008-M82 full-val-mini loss-safe candidate-source expansion result interpretation and trajectory/source-expansion decision"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

CORE_POLICY = "detector_confidence_budget5_core_v0"
APPEND_POLICY = "loss_safe_append_source_probe_budget8_v0"
SOURCE_EXPAND_POLICY = "loss_safe_observation_source_expansion_probe_v0"
EVAL_POLICIES = {CORE_POLICY, APPEND_POLICY}
EVAL_SCOPES = ("detector_budget5", "policy_budget")


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


def candidate_key(row: dict[str, Any]) -> str:
    return str(row.get("proposal_uid") or row.get("raw_candidate_uid") or row.get("candidate_visit_uid"))


def build_candidate_index(visit_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in visit_rows:
        proposal_uid = str(row.get("proposal_uid"))
        if not proposal_uid or proposal_uid in out:
            continue
        out[proposal_uid] = {
            "proposal_uid": proposal_uid,
            "snapped_position_m": row.get("snapped_position_m") or row.get("execution_stop_position_m"),
            "uses_objectnav_eval_goal": False,
            "uses_objectnav_eval_viewpoint": False,
        }
    return out


def scope_rows(visit_rows: list[dict[str, Any]], eval_budget_scope: str) -> list[dict[str, Any]]:
    if eval_budget_scope == "detector_budget5":
        return [row for row in visit_rows if bool(row.get("within_detector_budget5"))]
    if eval_budget_scope == "policy_budget":
        return [row for row in visit_rows if bool(row.get("within_policy_budget"))]
    raise ValueError(f"unknown eval scope: {eval_budget_scope}")


def enrich_candidate_goal_rows(
    goal_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    *,
    eval_budget_scope: str,
    boundary_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for goal_row, visit_row in zip(goal_rows, visit_rows):
        boundary = boundary_index.get(str(visit_row.get("adapter_episode_id")), {})
        enriched = dict(goal_row)
        enriched.update(
            {
                "version": VERSION,
                "eval_budget_scope": eval_budget_scope,
                "policy_plan_uid": visit_row.get("policy_plan_uid"),
                "candidate_visit_uid": visit_row.get("candidate_visit_uid"),
                "source_candidate_visit_uid": visit_row.get("source_candidate_visit_uid"),
                "source_policy_id": visit_row.get("source_policy_id"),
                "source_visit_rank": visit_row.get("source_visit_rank"),
                "candidate_source_role": visit_row.get("candidate_source_role"),
                "frame_pose_role": visit_row.get("frame_pose_role"),
                "observation_pose_id": visit_row.get("observation_pose_id"),
                "candidate_order_component": visit_row.get("candidate_order_component"),
                "within_detector_budget5": bool(visit_row.get("within_detector_budget5")),
                "within_policy_budget": bool(visit_row.get("within_policy_budget")),
                "primary_budget_cap": visit_row.get("primary_budget_cap"),
                "goal_eval_in_next_unit": bool(visit_row.get("goal_eval_in_next_unit")),
                "execute_in_next_runner": bool(visit_row.get("execute_in_next_runner")),
                "policy_input_uses_eval_goal_or_viewpoint": bool(
                    visit_row.get("policy_input_uses_eval_goal_or_viewpoint")
                ),
                "policy_input_uses_success_label": bool(visit_row.get("policy_input_uses_success_label")),
                "uses_m70_proxy_success_for_filtering": bool(visit_row.get("uses_m70_proxy_success_for_filtering")),
                "uses_m71_failure_class_for_policy": bool(visit_row.get("uses_m71_failure_class_for_policy")),
                "uses_m73_trajectory_result_for_policy": bool(visit_row.get("uses_m73_trajectory_result_for_policy")),
                "uses_m78_loss_identity_for_policy": bool(visit_row.get("uses_m78_loss_identity_for_policy")),
                "source_gap_expansion_case": bool(boundary.get("source_gap_expansion_case")),
                "budget5_loss_sentinel_case": bool(boundary.get("budget5_loss_sentinel_case")),
                "localization_boundary_control_case": bool(boundary.get("localization_boundary_control_case")),
                "m79_case_types": boundary.get("m79_case_types", []),
                "claim_boundary": "M81 joins ObjectNav goal/viewpoint fields only for evaluation; these fields are not policy inputs.",
            }
        )
        out.append(enriched)
    return out


def enrich_metric_rows(
    scan_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    plan_index: dict[tuple[str, str], dict[str, Any]],
    boundary_index: dict[str, dict[str, Any]],
    *,
    eval_budget_scope: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched_scan: list[dict[str, Any]] = []
    for row in scan_rows:
        out = dict(row)
        out["version"] = VERSION
        out["eval_budget_scope"] = eval_budget_scope
        plan = plan_index.get((str(row.get("policy_id")), str(row.get("adapter_episode_id"))), {})
        boundary = boundary_index.get(str(row.get("adapter_episode_id")), {})
        out["policy_plan_uid"] = plan.get("policy_plan_uid")
        out["primary_budget_cap"] = plan.get("primary_budget_cap")
        out["detector_budget5_rows"] = plan.get("detector_budget5_rows")
        out["append_after_top5_rows"] = plan.get("append_after_top5_rows")
        out["source_gap_expansion_case"] = bool(boundary.get("source_gap_expansion_case"))
        out["budget5_loss_sentinel_case"] = bool(boundary.get("budget5_loss_sentinel_case"))
        out["localization_boundary_control_case"] = bool(boundary.get("localization_boundary_control_case"))
        out["source_ready"] = boundary.get("source_ready")
        out["source_gap"] = boundary.get("source_gap")
        out["goal_eval_in_next_unit"] = bool(plan.get("goal_eval_in_next_unit"))
        out["claim_boundary"] = "M81 metric rows are proxy goal-evaluation diagnostics, not executed navigation SR/SPL."
        enriched_scan.append(out)

    enriched_aggregate: list[dict[str, Any]] = []
    for row in aggregate_rows:
        out = dict(row)
        out["version"] = VERSION
        out["eval_budget_scope"] = eval_budget_scope
        out["claim_boundary"] = "M81 aggregate rows are leakage-safe proxy diagnostics, not executed navigation SR/SPL."
        enriched_aggregate.append(out)
    return enriched_scan, enriched_aggregate


def evaluate_scope(
    m12: Any,
    visit_rows: list[dict[str, Any]],
    candidate_index: dict[str, dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
    plan_index: dict[tuple[str, str], dict[str, Any]],
    boundary_index: dict[str, dict[str, Any]],
    *,
    eval_budget_scope: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scoped_visit_rows = scope_rows(visit_rows, eval_budget_scope)
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
        boundary_index=boundary_index,
    )
    scan_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    scan_rows, aggregate_rows = enrich_metric_rows(
        scan_rows,
        aggregate_rows,
        plan_index,
        boundary_index,
        eval_budget_scope=eval_budget_scope,
    )
    failure_rows = m12.build_failure_rows(scan_rows)
    for row in failure_rows:
        row["version"] = VERSION
        row["eval_budget_scope"] = eval_budget_scope
        boundary = boundary_index.get(str(row.get("adapter_episode_id")), {})
        row["source_gap_expansion_case"] = bool(boundary.get("source_gap_expansion_case"))
        row["budget5_loss_sentinel_case"] = bool(boundary.get("budget5_loss_sentinel_case"))
        row["localization_boundary_control_case"] = bool(boundary.get("localization_boundary_control_case"))
        row["claim_boundary"] = "M81 failure rows are diagnostic and use eval labels only after policy rows are fixed."
    return candidate_goal_rows, scan_rows, aggregate_rows, failure_rows


def build_pairwise_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope_episode: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scan_rows:
        by_scope_episode[(str(row.get("eval_budget_scope")), str(row.get("adapter_episode_id")))][
            str(row.get("policy_id"))
        ] = row

    out: list[dict[str, Any]] = []
    for (scope, episode_id), policies in sorted(by_scope_episode.items()):
        baseline = policies.get(CORE_POLICY)
        method = policies.get(APPEND_POLICY)
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
            comparison = "append_gain"
        elif base_hit and not method_hit:
            comparison = "append_loss"
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
                "baseline_policy_id": CORE_POLICY,
                "method_policy_id": APPEND_POLICY,
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
                "source_gap_expansion_case": bool(baseline.get("source_gap_expansion_case")),
                "budget5_loss_sentinel_case": bool(baseline.get("budget5_loss_sentinel_case")),
                "localization_boundary_control_case": bool(baseline.get("localization_boundary_control_case")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    baseline.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                )
                or bool(method.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
                "claim_boundary": "Pairwise deltas are proxy diagnostics; no trajectory execution happened in M81.",
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
                "append_gain_rows": sum(1 for row in rows if row.get("comparison") == "append_gain"),
                "append_loss_rows": sum(1 for row in rows if row.get("comparison") == "append_loss"),
                "both_hit_rows": sum(1 for row in rows if row.get("comparison") == "both_hit"),
                "both_fail_rows": sum(1 for row in rows if row.get("comparison") == "both_fail"),
                "source_gap_rows": sum(1 for row in rows if row.get("source_gap_expansion_case")),
                "source_gap_append_gain_rows": sum(
                    1 for row in rows if row.get("source_gap_expansion_case") and row.get("comparison") == "append_gain"
                ),
                "source_gap_append_loss_rows": sum(
                    1 for row in rows if row.get("source_gap_expansion_case") and row.get("comparison") == "append_loss"
                ),
                "budget5_loss_sentinel_rows": sum(1 for row in rows if row.get("budget5_loss_sentinel_case")),
                "budget5_loss_sentinel_append_loss_rows": sum(
                    1
                    for row in rows
                    if row.get("budget5_loss_sentinel_case") and row.get("comparison") == "append_loss"
                ),
                "localization_control_rows": sum(1 for row in rows if row.get("localization_boundary_control_case")),
                "delta_primary_spl_proxy_mean": mean([finite_float(row.get("delta_primary_spl_proxy")) for row in rows]),
                "delta_rank_mean_over_both_hit": mean(
                    [
                        finite_float(row.get("delta_primary_first_hit_rank"))
                        for row in rows
                        if row.get("comparison") == "both_hit"
                    ]
                ),
                "claim_boundary": "M81 summaries compare fixed M80 orders and do not use eval labels for ranking.",
            }
        )
    return out


def build_source_boundary_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        if row.get("source_gap_expansion_case"):
            boundary = "source_gap_expansion_case"
        elif row.get("budget5_loss_sentinel_case"):
            boundary = "budget5_loss_sentinel_case"
        elif row.get("localization_boundary_control_case"):
            boundary = "localization_boundary_control_case"
        else:
            boundary = "ordinary_source_ready_case"
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
                "primary_spl_proxy_mean": mean([finite_float(row.get("primary_spl_proxy")) for row in rows]),
                "claim_boundary": "Source-boundary rows are reporting-only diagnostics after M80 materialization.",
            }
        )
    return out


def build_budget_invariant_eval_rows(
    invariant_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    detector_pairs = {
        str(row.get("adapter_episode_id")): row
        for row in pairwise_rows
        if row.get("eval_budget_scope") == "detector_budget5"
    }
    out: list[dict[str, Any]] = []
    for invariant in invariant_rows:
        pair = detector_pairs.get(str(invariant.get("adapter_episode_id")), {})
        eval_top5_loss_safe = (
            bool(invariant.get("top5_preserved"))
            and pair.get("comparison") != "append_loss"
            and abs(float(pair.get("delta_primary_spl_proxy") or 0.0)) < 1e-9
        )
        out.append(
            {
                "version": VERSION,
                "row_type": "budget_invariant_eval",
                "adapter_episode_id": invariant.get("adapter_episode_id"),
                "top5_preserved": bool(invariant.get("top5_preserved")),
                "m80_budget_invariant_pass": bool(invariant.get("budget_invariant_pass")),
                "detector_budget5_comparison": pair.get("comparison"),
                "detector_budget5_delta_primary_spl_proxy": pair.get("delta_primary_spl_proxy"),
                "detector_budget5_eval_top5_loss_safe": eval_top5_loss_safe,
                "source_gap_expansion_case": bool(invariant.get("source_gap_expansion_case")),
                "budget5_loss_sentinel_case": bool(invariant.get("budget5_loss_sentinel_case")),
                "localization_boundary_control_case": bool(invariant.get("localization_boundary_control_case")),
                "claim_boundary": "Budget invariant eval rows check loss safety under detector budget-5 only.",
            }
        )
    return out


def build_source_plan_eval_rows(source_plan_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy_pairs = {
        str(row.get("adapter_episode_id")): row
        for row in pairwise_rows
        if row.get("eval_budget_scope") == "policy_budget"
    }
    out: list[dict[str, Any]] = []
    for row in source_plan_rows:
        pair = policy_pairs.get(str(row.get("adapter_episode_id")), {})
        out.append(
            {
                "version": VERSION,
                "row_type": "source_observation_expansion_eval_plan",
                "plan_uid": row.get("plan_uid"),
                "policy_id": row.get("policy_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "action_id": row.get("action_id"),
                "requires_long_job_later": bool(row.get("requires_long_job_later")),
                "launch_long_job_now": False,
                "policy_budget_existing_append_comparison": pair.get("comparison"),
                "existing_append_recovered_primary_proxy": pair.get("comparison") == "append_gain",
                "used_for_candidate_ranking": False,
                "policy_input_allowed_for_final_policy": False,
                "claim_boundary": "Source-plan eval rows interpret existing append behavior only; new source generation is still future work.",
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
                "uses_m78_loss_identity_for_policy_rows": sum(
                    1 for item in items if item.get("uses_m78_loss_identity_for_policy")
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
                    or item.get("uses_m78_loss_identity_for_policy")
                    for item in items
                ),
                "claim_boundary": "ObjectNav goal/viewpoint fields are metric-only fields in M81.",
            }
        )
    return rows


def gate_status(condition: bool) -> str:
    return "pass" if condition else "fail"


def build_gate_rows(
    *,
    missing_inputs: list[str],
    m80_coverage: dict[str, Any],
    leakage_pass: bool,
    aggregate_index: dict[tuple[str, str], dict[str, Any]],
    delta_summary_rows: list[dict[str, Any]],
    budget_invariant_eval_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    detector_delta = next(
        (row for row in delta_summary_rows if row.get("eval_budget_scope") == "detector_budget5"),
        {},
    )
    policy_delta = next(
        (row for row in delta_summary_rows if row.get("eval_budget_scope") == "policy_budget"),
        {},
    )
    detector_loss_safe = (
        int(detector_delta.get("append_loss_rows") or 0) == 0
        and int(detector_delta.get("append_gain_rows") or 0) == 0
        and all(bool(row.get("detector_budget5_eval_top5_loss_safe")) for row in budget_invariant_eval_rows)
    )
    policy_no_success_loss = int(policy_delta.get("append_loss_rows") or 0) == 0
    policy_positive_gain = int(policy_delta.get("append_gain_rows") or 0) > 0
    source_gap_gain = int(policy_delta.get("source_gap_append_gain_rows") or 0) > 0
    source_gap_loss = int(policy_delta.get("source_gap_append_loss_rows") or 0) > 0

    core_budget = aggregate_index.get(("detector_budget5", CORE_POLICY), {})
    append_budget5 = aggregate_index.get(("detector_budget5", APPEND_POLICY), {})
    append_policy_budget = aggregate_index.get(("policy_budget", APPEND_POLICY), {})
    core_policy_budget = aggregate_index.get(("policy_budget", CORE_POLICY), {})
    budget5_equal_success = int(core_budget.get("primary_success_rows") or 0) == int(
        append_budget5.get("primary_success_rows") or -1
    )
    policy_budget_no_success_loss = int(append_policy_budget.get("primary_success_rows") or 0) >= int(
        core_policy_budget.get("primary_success_rows") or 0
    )

    rows = [
        {
            "version": VERSION,
            "gate_id": "m80_ready",
            "gate_status": gate_status(m80_coverage.get("status") == "e008_m80_loss_safe_candidate_source_expansion_row_materialization_smoke_ready"),
            "blocks_next": False,
            "rationale": "M80 materialization must be ready before M81 goal evaluation.",
        },
        {
            "version": VERSION,
            "gate_id": "missing_inputs",
            "gate_status": gate_status(not missing_inputs),
            "blocks_next": bool(missing_inputs),
            "rationale": "M81 requires M64 episodes and M80 candidate rows/plans.",
        },
        {
            "version": VERSION,
            "gate_id": "leakage_audit",
            "gate_status": gate_status(leakage_pass),
            "blocks_next": not leakage_pass,
            "rationale": "Goal/viewpoint fields must be metric-only and never policy inputs.",
        },
        {
            "version": VERSION,
            "gate_id": "detector_budget5_eval_loss_safe",
            "gate_status": gate_status(detector_loss_safe and budget5_equal_success),
            "blocks_next": not (detector_loss_safe and budget5_equal_success),
            "rationale": "Append policy must match detector-confidence top-5 under the original budget-5 scope.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_budget_no_success_loss",
            "gate_status": gate_status(policy_no_success_loss and policy_budget_no_success_loss),
            "blocks_next": not (policy_no_success_loss and policy_budget_no_success_loss),
            "rationale": "Append-only budget-8 probe should not lose proxy success against the preserved core.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_budget_positive_gain",
            "gate_status": "pass" if policy_positive_gain else "warning",
            "blocks_next": False,
            "rationale": "Positive append gains indicate that extra source probes add recoverable candidates; absence of gain means new source generation is still needed.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_recovery",
            "gate_status": "pass" if source_gap_gain and not source_gap_loss else "warning",
            "blocks_next": False,
            "rationale": "Existing appended candidates should be checked separately from future source/observation expansion plans.",
        },
    ]
    selected_next = NEXT_UNIT
    return rows, selected_next


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_loss_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M81 evaluates fixed M80 rows against ObjectNav target labels without policy leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_detector_budget5_preservation_eval",
            "supported": True,
            "claim_boundary": "M81 can support detector budget-5 preservation if the detector_budget5 scope exactly matches the core metric.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "Append budget-8 proxy gains are not a budget-5 deployable search policy claim.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M81 does not execute Habitat trajectories and cannot report final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M81 is a navigation proxy evaluation over current detector candidates, not a final RGB-D/open-vocabulary robustness benchmark.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M81 does not introduce a natural-language or human-intent understanding module.",
        },
    ]


def build_route_decision_rows(selected_next: str, gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fail_gates = [row["gate_id"] for row in gate_rows if row.get("gate_status") == "fail"]
    warning_gates = [row["gate_id"] for row in gate_rows if row.get("gate_status") == "warning"]
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "selected_next_unit": selected_next,
            "failed_gates": fail_gates,
            "warning_gates": warning_gates,
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "claim_boundary": "M81 does not launch a Docker trajectory job; M82 must interpret the proxy result first.",
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
                gain=row.get("append_gain_rows"),
                loss=row.get("append_loss_rows"),
                both_hit=row.get("both_hit_rows"),
                both_fail=row.get("both_fail_rows"),
                spl_delta=fmt(row.get("delta_primary_spl_proxy_mean")),
                sg_gain=row.get("source_gap_append_gain_rows"),
                sg_loss=row.get("source_gap_append_loss_rows"),
            )
        )
    gate_lines = [
        f"| `{row['gate_id']}` | {row['gate_status']} | {row['blocks_next']} |"
        for row in gate_rows
    ]
    return f"""# E008-M81 Loss-Safe Candidate-Source Expansion Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M80 status: `{coverage['m80_status']}`.
- Eval episode rows: {coverage['eval_episode_rows']}.
- Loss-safe visit rows evaluated: {coverage['loss_safe_visit_rows_evaluated']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy metric rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Leakage audit pass: {coverage['leakage_audit_pass']}.
- Primary metric: `{coverage['primary_metric']}`.
- Detector budget-5 eval loss-safe: {coverage['detector_budget5_eval_loss_safe']}.
- Policy-budget append gain rows: {coverage['policy_budget_append_gain_rows']}.
- Source-gap append gain rows: {coverage['policy_budget_source_gap_append_gain_rows']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| scope | policy_id | primary hits | proxy SR | proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Pairwise Delta

`{APPEND_POLICY}` minus `{CORE_POLICY}`.

| scope | gain rows | loss rows | both hit | both fail | mean delta SPL proxy | source-gap gain | source-gap loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(delta_lines)}

## Gates

| gate_id | status | blocks next |
| --- | --- | --- |
{chr(10).join(gate_lines)}

## Claim Boundary

- M81 supports leakage-safe proxy evaluation of fixed M80 rows.
- M81 supports detector budget-5 preservation only if the `detector_budget5` scope remains identical.
- M81 does not support final real navigation `SR` / `SPL`; no `Habitat` trajectory is executed here.
- M81 does not make append budget-8 a deployable budget-5 search policy.
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
    m12 = load_module(M12_TOOL, "e008_m12_goal_eval_for_m81")
    m70 = load_module(M70_TOOL, "e008_m70_goal_eval_for_m81")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m80_coverage = read_json(M80_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_DIR / "val_mini_episode_rows.jsonl")
    visit_rows_all = read_jsonl(M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl")
    plan_rows = read_jsonl(M80_DIR / "loss_safe_policy_plan_rows.jsonl")
    invariant_rows = read_jsonl(M80_DIR / "budget_invariant_rows.jsonl")
    source_boundary_rows_m80 = read_jsonl(M80_DIR / "source_boundary_accounting_rows.jsonl")
    source_plan_rows = read_jsonl(M80_DIR / "source_observation_expansion_plan_rows.jsonl")

    missing_inputs: list[str] = []
    if not episode_rows:
        missing_inputs.append(str(M64_DIR / "val_mini_episode_rows.jsonl"))
    if not visit_rows_all:
        missing_inputs.append(str(M80_DIR / "loss_safe_candidate_visit_order_rows.jsonl"))
    if not plan_rows:
        missing_inputs.append(str(M80_DIR / "loss_safe_policy_plan_rows.jsonl"))
    if not invariant_rows:
        missing_inputs.append(str(M80_DIR / "budget_invariant_rows.jsonl"))
    if not source_boundary_rows_m80:
        missing_inputs.append(str(M80_DIR / "source_boundary_accounting_rows.jsonl"))
    if not m80_coverage:
        missing_inputs.append(str(M80_DIR / "coverage.json"))

    goal_rows = m70.build_full_val_mini_eval_goal_rows(episode_rows) if episode_rows else []
    eval_index = m12.build_eval_goal_index(goal_rows) if goal_rows else {}
    oracle_index = {str(row["adapter_episode_id"]): row for row in goal_rows}
    visit_rows = [
        row
        for row in visit_rows_all
        if row.get("policy_id") in EVAL_POLICIES
        and bool(row.get("goal_eval_in_next_unit"))
    ]
    candidate_index = build_candidate_index(visit_rows)
    plan_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in plan_rows
    }
    boundary_index = {str(row.get("adapter_episode_id")): row for row in source_boundary_rows_m80}

    all_candidate_goal_rows: list[dict[str, Any]] = []
    all_scan_rows: list[dict[str, Any]] = []
    all_aggregate_rows: list[dict[str, Any]] = []
    all_failure_rows: list[dict[str, Any]] = []
    if not missing_inputs:
        for scope in EVAL_SCOPES:
            candidate_goal_rows, scan_rows, aggregate_rows, failure_rows = evaluate_scope(
                m12,
                visit_rows,
                candidate_index,
                eval_index,
                oracle_index,
                plan_index,
                boundary_index,
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
    source_boundary_goal_rows = build_source_boundary_rows(all_scan_rows)
    budget_invariant_eval_rows = build_budget_invariant_eval_rows(invariant_rows, pairwise_rows)
    source_plan_eval_rows = build_source_plan_eval_rows(source_plan_rows, pairwise_rows)
    aggregate_index = aggregate_by_policy_scope(all_aggregate_rows)
    gate_rows, selected_next = build_gate_rows(
        missing_inputs=missing_inputs,
        m80_coverage=m80_coverage,
        leakage_pass=leakage_pass,
        aggregate_index=aggregate_index,
        delta_summary_rows=delta_summary_rows,
        budget_invariant_eval_rows=budget_invariant_eval_rows,
    )
    claim_boundary_rows = build_claim_boundary_rows()
    route_decision_rows = build_route_decision_rows(selected_next, gate_rows)
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in all_aggregate_rows]
    gate_fail_rows = sum(1 for row in gate_rows if row.get("gate_status") == "fail")
    gate_warning_rows = sum(1 for row in gate_rows if row.get("gate_status") == "warning")
    delta_by_scope = {str(row.get("eval_budget_scope")): row for row in delta_summary_rows}
    detector_loss_safe = all(bool(row.get("detector_budget5_eval_top5_loss_safe")) for row in budget_invariant_eval_rows)
    policy_delta = delta_by_scope.get("policy_budget", {})

    status = READY_STATUS
    if missing_inputs or not all_aggregate_rows or not leakage_pass or gate_fail_rows:
        status = BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m80_status": m80_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "eval_episode_rows": len(goal_rows),
        "expected_eval_episode_rows": len(episode_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "loss_safe_visit_rows_total": len(visit_rows_all),
        "loss_safe_visit_rows_evaluated": len(visit_rows),
        "candidate_goal_eval_rows": len(all_candidate_goal_rows),
        "scan_policy_metric_rows": len(all_scan_rows),
        "aggregate_policy_rows": len(all_aggregate_rows),
        "failure_rows": len(all_failure_rows),
        "pairwise_delta_rows": len(pairwise_rows),
        "delta_summary_rows": len(delta_summary_rows),
        "source_boundary_goal_metric_rows": len(source_boundary_goal_rows),
        "budget_invariant_eval_rows": len(budget_invariant_eval_rows),
        "source_observation_expansion_eval_plan_rows": len(source_plan_eval_rows),
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
                "append_gain_rows": row.get("append_gain_rows"),
                "append_loss_rows": row.get("append_loss_rows"),
                "both_hit_rows": row.get("both_hit_rows"),
                "both_fail_rows": row.get("both_fail_rows"),
                "delta_primary_spl_proxy_mean": row.get("delta_primary_spl_proxy_mean"),
                "source_gap_append_gain_rows": row.get("source_gap_append_gain_rows"),
                "source_gap_append_loss_rows": row.get("source_gap_append_loss_rows"),
                "budget5_loss_sentinel_append_loss_rows": row.get("budget5_loss_sentinel_append_loss_rows"),
            }
            for row in delta_summary_rows
        },
        "detector_budget5_eval_loss_safe": detector_loss_safe,
        "policy_budget_append_gain_rows": int(policy_delta.get("append_gain_rows") or 0),
        "policy_budget_append_loss_rows": int(policy_delta.get("append_loss_rows") or 0),
        "policy_budget_source_gap_append_gain_rows": int(policy_delta.get("source_gap_append_gain_rows") or 0),
        "policy_budget_source_gap_append_loss_rows": int(policy_delta.get("source_gap_append_loss_rows") or 0),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "goal_evaluation_ready": status == READY_STATUS,
        "trajectory_contract_ready": False,
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
    write_jsonl(ARTIFACT_DIR / "loss_safe_candidate_goal_eval_rows.jsonl", all_candidate_goal_rows)
    write_jsonl(ARTIFACT_DIR / "policy_goal_metric_rows.jsonl", all_scan_rows + all_aggregate_rows)
    write_jsonl(ARTIFACT_DIR / "scan_policy_goal_metric_rows.jsonl", all_scan_rows)
    write_jsonl(ARTIFACT_DIR / "aggregate_policy_goal_metric_rows.jsonl", all_aggregate_rows)
    write_jsonl(ARTIFACT_DIR / "failure_rows.jsonl", all_failure_rows)
    write_jsonl(ARTIFACT_DIR / "policy_pairwise_delta_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "policy_delta_summary_rows.jsonl", delta_summary_rows)
    write_jsonl(ARTIFACT_DIR / "source_boundary_goal_metric_rows.jsonl", source_boundary_goal_rows)
    write_jsonl(ARTIFACT_DIR / "budget_invariant_eval_rows.jsonl", budget_invariant_eval_rows)
    write_jsonl(ARTIFACT_DIR / "source_observation_expansion_eval_plan_rows.jsonl", source_plan_eval_rows)
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
