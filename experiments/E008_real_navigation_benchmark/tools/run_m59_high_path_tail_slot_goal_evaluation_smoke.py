#!/usr/bin/env python3
"""Evaluate M58 high-path tail-slot rows with ObjectNav labels as eval-only metrics."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0"

M03_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M58_DIR = EXP_ROOT / "artifacts" / "E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0"
M27_TOOL = EXP_ROOT / "tools" / "run_m27_h001_goal_evaluation_smoke.py"

VERSION = "e008_m59_high_path_tail_slot_goal_evaluation_smoke_v0"
READY_STATUS = "e008_m59_high_path_tail_slot_goal_evaluation_smoke_ready"
BLOCKED_STATUS = "e008_m59_high_path_tail_slot_goal_evaluation_smoke_blocked"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

M58_POLICY = "h001_task_conditioned_high_path_tail_slot_budget5_v3"
BASE_H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_CURRENT_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_DIVERSE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
STATIC_POLICY = "static_stale_memory_top1_v0"
OLD_H001_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"

BASELINE_POLICIES = [
    BASE_H001_POLICY,
    TASK_AGNOSTIC_POLICY,
    DETECTOR_POLICY,
    FIXED_CURRENT_POLICY,
    SOURCE_DIVERSE_CURRENT_POLICY,
    STATIC_POLICY,
    OLD_H001_POLICY,
]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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


def safe_ratio(num: int, den: int) -> float | None:
    return round(num / den, 6) if den else None


def delta(a: object, b: object) -> float | None:
    aa = finite_float(a)
    bb = finite_float(b)
    if aa is None or bb is None:
        return None
    return round(aa - bb, 6)


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return round(sum(clean) / len(clean), 6) if clean else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def enrich_candidate_goal_rows(
    candidate_goal_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    visit_index = {str(row.get("candidate_visit_uid")): row for row in visit_rows}
    out: list[dict[str, Any]] = []
    for row in candidate_goal_rows:
        current = dict(row)
        source = visit_index.get(str(row.get("candidate_visit_uid")), {})
        current["version"] = VERSION
        current["candidate_goal_eval_uid"] = f"m59::{row.get('candidate_visit_uid')}"
        if current.get("visit_rank") is None:
            current["visit_rank"] = source.get("visit_rank")
        for key in (
            "selected_route",
            "m58_selected_route",
            "m58_materialization_kind",
            "candidate_source_role",
            "dynamic_stale_overlay_role",
            "source_expansion_route",
            "source_gap_handling",
            "diagnostic_source_gap_boundary_for_reporting",
            "use_diagnostic_source_gap_boundary_for_policy",
            "uses_m57_diagnostic_hit_for_policy",
            "uses_task_context_for_decision",
            "diagnostic_not_policy_input",
            "primary_budget_cap",
            "source_diversity_key",
        ):
            current[key] = source.get(key)
        current["uses_objectnav_eval_goal_or_viewpoint_for_policy"] = bool(
            current.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
            or source.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
            or source.get("policy_input_uses_eval_goal_or_viewpoint")
        )
        current["uses_objectnav_eval_goal_or_viewpoint_for_metric"] = True
        current["claim_boundary"] = (
            "M59 joins M58 visit rows to ObjectNav targets for evaluation-only goal labels; "
            "policy order was already fixed in M58."
        )
        out.append(current)
    return out


def attach_plan_metadata(
    scan_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id")), str(row.get("task_context_id"))): row
        for row in plan_rows
    }
    out: list[dict[str, Any]] = []
    for row in scan_rows:
        current = dict(row)
        plan = plan_index.get(
            (str(row.get("policy_id")), str(row.get("adapter_episode_id")), str(row.get("task_context_id"))),
            {},
        )
        for key in (
            "diagnostic_source_gap_boundary_for_reporting",
            "old_location_dead_end_cost_proxy_m",
            "stale_old_memory_candidate_rows",
            "current_observation_candidate_rows",
            "stale_visit_rate_proxy",
            "reobservation_rate_proxy",
            "unique_frame_ids",
            "unique_source_diversity_keys",
            "runner_input_ready",
            "selected_route",
            "candidate_visit_order_contract",
        ):
            current[key] = plan.get(key)
        current["source_boundary"] = (
            "source_gap" if current.get("diagnostic_source_gap_boundary_for_reporting") else "source_ready"
        )
        out.append(current)
    return out


def aggregate_scan_rows(m27: Any, scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        grouped[(str(row.get("policy_id")), str(row.get("source_boundary")))].append(row)
    out = []
    for (policy_id, source_boundary), rows in sorted(grouped.items()):
        aggregate = m27.summarize_aggregate(
            rows,
            "aggregate_policy_source_boundary",
            {
                "policy_id": policy_id,
                "policy_family": rows[0].get("policy_family"),
                "task_context_id": "all",
                "source_boundary": source_boundary,
            },
        )
        aggregate["source_boundary_rows"] = len(rows)
        out.append(aggregate)
    return out


def by_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in rows if row.get("metric_scope") == "aggregate_policy"}


def by_policy_boundary(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("policy_id")), str(row.get("source_boundary"))): row
        for row in rows
        if row.get("metric_scope") == "aggregate_policy_source_boundary"
    }


def build_pairwise_rows(
    aggregate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full = by_policy(aggregate_rows)
    source = by_policy_boundary(source_rows)
    rows: list[dict[str, Any]] = []
    scopes = [("full_denominator", None), ("source_ready", "source_ready"), ("source_gap", "source_gap")]
    for scope, boundary in scopes:
        h001 = full.get(M58_POLICY) if boundary is None else source.get((M58_POLICY, boundary))
        if not h001:
            continue
        for baseline_id in BASELINE_POLICIES:
            baseline = full.get(baseline_id) if boundary is None else source.get((baseline_id, boundary))
            if not baseline:
                continue
            rows.append(
                {
                    "version": VERSION,
                    "comparison_scope": scope,
                    "source_boundary": boundary,
                    "method_policy_id": M58_POLICY,
                    "baseline_policy_id": baseline_id,
                    "method_success_rows": h001.get("primary_success_rows"),
                    "baseline_success_rows": baseline.get("primary_success_rows"),
                    "scan_policy_rows": h001.get("scan_policy_rows"),
                    "method_primary_proxy_sr": h001.get("primary_proxy_sr"),
                    "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
                    "delta_primary_proxy_sr": delta(h001.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")),
                    "method_primary_spl_proxy_mean": h001.get("primary_spl_proxy_mean"),
                    "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
                    "delta_primary_spl_proxy_mean": delta(
                        h001.get("primary_spl_proxy_mean"), baseline.get("primary_spl_proxy_mean")
                    ),
                    "method_mean_hit_rank_over_success": h001.get("primary_first_hit_rank_mean_over_success"),
                    "baseline_mean_hit_rank_over_success": baseline.get("primary_first_hit_rank_mean_over_success"),
                    "delta_mean_hit_rank_over_success": delta(
                        h001.get("primary_first_hit_rank_mean_over_success"),
                        baseline.get("primary_first_hit_rank_mean_over_success"),
                    ),
                    "method_best_any_viewpoint_xz_m_mean": h001.get("best_any_viewpoint_xz_m_mean"),
                    "baseline_best_any_viewpoint_xz_m_mean": baseline.get("best_any_viewpoint_xz_m_mean"),
                    "claim_boundary": "Pairwise rows are leakage-safe goal-evaluation proxy comparisons, not executed navigation SR/SPL.",
                }
            )
    return rows


def build_source_gap_goal_recovery_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id")), str(row.get("task_context_id"))): row
        for row in scan_rows
    }
    rows: list[dict[str, Any]] = []
    for key, method in sorted(index.items()):
        policy_id, episode_id, task_context_id = key
        if policy_id != M58_POLICY:
            continue
        base = index.get((BASE_H001_POLICY, episode_id, task_context_id), {})
        task = index.get((TASK_AGNOSTIC_POLICY, episode_id, task_context_id), {})
        detector = index.get((DETECTOR_POLICY, episode_id, task_context_id), {})
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "task_context_id": task_context_id,
                "object_category": method.get("object_category"),
                "source_boundary": method.get("source_boundary"),
                "diagnostic_source_gap_boundary_for_reporting": bool(
                    method.get("diagnostic_source_gap_boundary_for_reporting")
                ),
                "method_policy_id": M58_POLICY,
                "base_h001_policy_id": BASE_H001_POLICY,
                "method_primary_hit": bool(method.get("primary_hit")),
                "base_h001_primary_hit": bool(base.get("primary_hit")),
                "task_agnostic_primary_hit": bool(task.get("primary_hit")),
                "detector_primary_hit": bool(detector.get("primary_hit")),
                "method_first_hit_rank": method.get("primary_first_hit_rank"),
                "base_h001_first_hit_rank": base.get("primary_first_hit_rank"),
                "task_agnostic_first_hit_rank": task.get("primary_first_hit_rank"),
                "detector_first_hit_rank": detector.get("primary_first_hit_rank"),
                "recovered_vs_base_h001": (not bool(base.get("primary_hit"))) and bool(method.get("primary_hit")),
                "lost_vs_base_h001": bool(base.get("primary_hit")) and not bool(method.get("primary_hit")),
                "improves_rank_vs_base_h001": finite_float(method.get("primary_first_hit_rank")) is not None
                and finite_float(base.get("primary_first_hit_rank")) is not None
                and float(method["primary_first_hit_rank"]) < float(base["primary_first_hit_rank"]),
                "ties_task_agnostic_success": bool(method.get("primary_hit")) == bool(task.get("primary_hit")),
                "claim_boundary": "Recovery rows use ObjectNav labels only after policy order materialization.",
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_goal_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_policy_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        by_policy_id[str(row.get("policy_id"))].append(row)
    rows = []
    for policy_id, policy_rows in sorted(by_policy_id.items()):
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "candidate_goal_eval_rows": len(policy_rows),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "eval_goal_rows_joined": len(
                    {row.get("adapter_episode_id") for row in policy_rows if row.get("eval_goal_position")}
                ),
                "loaded_all_viewpoint_episode_rows": sum(
                    1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
                ),
                "policy_order_fixed_before_eval_join": True,
                "leakage_audit_pass": not any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows
                ),
            }
        )
    return rows


def metric_lookup(rows: list[dict[str, Any]], policy_id: str, boundary: str | None = None) -> dict[str, Any]:
    if boundary is None:
        for row in rows:
            if row.get("policy_id") == policy_id and row.get("metric_scope") == "aggregate_policy":
                return row
        return {}
    for row in rows:
        if (
            row.get("policy_id") == policy_id
            and row.get("metric_scope") == "aggregate_policy_source_boundary"
            and row.get("source_boundary") == boundary
        ):
            return row
    return {}


def build_readiness_gate_rows(
    m58_coverage: dict[str, Any],
    candidate_goal_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    method_full = metric_lookup(aggregate_rows, M58_POLICY)
    base_full = metric_lookup(aggregate_rows, BASE_H001_POLICY)
    method_gap = metric_lookup(source_rows, M58_POLICY, "source_gap")
    base_gap = metric_lookup(source_rows, BASE_H001_POLICY, "source_gap")
    unrecovered_gap_rows = [row for row in recovery_rows if row.get("source_boundary") == "source_gap"]
    return [
        {
            "version": VERSION,
            "gate_id": "m58_materialization_ready",
            "status": "pass"
            if m58_coverage.get("status") == "e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready"
            else "fail",
            "evidence": f"M58 status `{m58_coverage.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_goal_rows_evaluated",
            "status": "pass" if len(candidate_goal_rows) == int(m58_coverage.get("candidate_rows") or -1) else "fail",
            "evidence": f"candidate-goal rows={len(candidate_goal_rows)}; M58 candidate rows={m58_coverage.get('candidate_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "new_policy_full_denominator_present",
            "status": "pass" if int(method_full.get("scan_policy_rows") or 0) == 18 else "fail",
            "evidence": f"M58 policy scan-task rows={method_full.get('scan_policy_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if leakage_rows and all(row.get("leakage_audit_pass") for row in leakage_rows) else "fail",
            "evidence": f"leakage-pass policies={sum(1 for row in leakage_rows if row.get('leakage_audit_pass'))}/{len(leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_sr_improves_over_h001_v2",
            "status": "pass"
            if finite_float(method_gap.get("primary_proxy_sr")) is not None
            and finite_float(base_gap.get("primary_proxy_sr")) is not None
            and float(method_gap["primary_proxy_sr"]) > float(base_gap["primary_proxy_sr"])
            else "fail",
            "evidence": f"M58 source-gap SR={fmt(method_gap.get('primary_proxy_sr'))}; base H001 v2 source-gap SR={fmt(base_gap.get('primary_proxy_sr'))}.",
        },
        {
            "version": VERSION,
            "gate_id": "full_denominator_sr_not_worse_than_h001_v2",
            "status": "pass"
            if finite_float(method_full.get("primary_proxy_sr")) is not None
            and finite_float(base_full.get("primary_proxy_sr")) is not None
            and float(method_full["primary_proxy_sr"]) >= float(base_full["primary_proxy_sr"])
            else "fail",
            "evidence": f"M58 full SR={fmt(method_full.get('primary_proxy_sr'))}; base H001 v2 full SR={fmt(base_full.get('primary_proxy_sr'))}.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_context_recovery_without_loss",
            "status": "pass"
            if unrecovered_gap_rows
            and sum(1 for row in unrecovered_gap_rows if row.get("recovered_vs_base_h001")) > 0
            and sum(1 for row in unrecovered_gap_rows if row.get("lost_vs_base_h001")) == 0
            else "fail",
            "evidence": (
                f"source-gap recovered={sum(1 for row in unrecovered_gap_rows if row.get('recovered_vs_base_h001'))}; "
                f"lost={sum(1 for row in unrecovered_gap_rows if row.get('lost_vs_base_h001'))}."
            ),
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_claim_still_blocked",
            "status": "pass",
            "evidence": "M59 is leakage-safe goal evaluation only; Docker trajectory execution is still required.",
        },
    ]


def build_claim_boundary_rows(ready_for_m60: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_leakage_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M59 evaluates M58 rows against ObjectNav goal/viewpoint labels after policy order materialization.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_source_gap_proxy_recovery",
            "supported": ready_for_m60,
            "claim_boundary": "Supported only as goal-evaluation proxy and only if source-gap SR improves without full-denominator SR loss.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M59 does not execute Habitat trajectories; real navigation SR/SPL requires M60/M61-style Docker execution.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "M59 uses fixed JSONL policies and eval-only labels; deployment requires simulator execution, scale, and allowed-input policy packaging.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context remains a secondary condition; M59 does not test natural-language human intent.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M59 reuses existing detector/current-observation candidates and does not prove final real RGB-D/open-vocabulary robustness.",
        },
    ]


def build_route_decision_rows(ready_for_m60: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "promote_to_trajectory_contract" if ready_for_m60 else "repair_goal_eval_or_policy_before_trajectory",
            "selected_next_unit": "E008-M60 high-path tail-slot trajectory contract and Docker preflight"
            if ready_for_m60
            else "repair E008-M59 high-path tail-slot goal evaluation or policy materialization",
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "requires_docker_next": ready_for_m60,
            "real_navigation_sr_spl_ready": False,
            "deployable_search_policy_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_m60_command_rows(ready_for_m60: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "command_id": "m60_contract_next",
            "ready": ready_for_m60,
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/plan_m60_high_path_tail_slot_trajectory_contract.py",
            "expected_outputs": [
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/coverage.json",
                "experiments/E008_real_navigation_benchmark/artifacts/E008-M60_high_path_tail_slot_trajectory_contract_v0/report.md",
            ],
            "claim_boundary": "M60 should create a Docker trajectory contract only after M59 passes leakage-safe goal-evaluation gates.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    aggregate_table = markdown_table(
        aggregate_rows,
        [
            "policy_id",
            "primary_success_rows",
            "scan_policy_rows",
            "primary_proxy_sr",
            "primary_spl_proxy_mean",
            "primary_first_hit_rank_mean_over_success",
            "best_any_viewpoint_xz_m_mean",
        ],
    )
    source_table = markdown_table(
        source_rows,
        [
            "policy_id",
            "source_boundary",
            "primary_success_rows",
            "scan_policy_rows",
            "primary_proxy_sr",
            "primary_spl_proxy_mean",
            "primary_first_hit_rank_mean_over_success",
        ],
    )
    key_pairwise = [
        row
        for row in pairwise_rows
        if row.get("baseline_policy_id") in {BASE_H001_POLICY, TASK_AGNOSTIC_POLICY, DETECTOR_POLICY, STATIC_POLICY}
    ]
    pairwise_table = markdown_table(
        key_pairwise,
        [
            "comparison_scope",
            "baseline_policy_id",
            "delta_primary_proxy_sr",
            "delta_primary_spl_proxy_mean",
            "delta_mean_hit_rank_over_success",
        ],
    )
    gate_table = markdown_table(gate_rows, ["gate_id", "status", "evidence"])
    return f"""# E008-M59 High-Path Tail-Slot Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M58 status: `{coverage['m58_status']}`.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Source-boundary aggregate rows: {coverage['source_boundary_aggregate_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- M58 policy full `GoalEvalProxySR`: {fmt(coverage['m58_full_primary_proxy_sr'])}.
- M58 policy source-gap `GoalEvalProxySR`: {fmt(coverage['m58_source_gap_primary_proxy_sr'])}.
- Base H001 v2 source-gap `GoalEvalProxySR`: {fmt(coverage['base_h001_source_gap_primary_proxy_sr'])}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

{aggregate_table}

## Source Boundary Aggregate

{source_table}

## Key Pairwise Deltas

{pairwise_table}

## Readiness Gates

{gate_table}

## Claim Boundary

- M59 uses `ObjectNav` goal/viewpoint fields only as evaluation labels after M58 fixed policy rows.
- M59 reports `GoalEvalProxySR` / proxy `SPL`; it is not final real navigation `SR` / `SPL`.
- The next positive route, if gates pass, is a Docker trajectory contract/execution path.
- Human intent remains a secondary structured condition, not a main natural-language intent claim.
"""


def main() -> None:
    m27 = load_module(M27_TOOL, "e008_m27_goal_eval")
    m27.VERSION = VERSION
    m27.PRIMARY_METRIC = PRIMARY_METRIC
    m12 = m27.load_m12_module()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m58_coverage = read_json(M58_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_DIR / "oracle_path_rows.jsonl")
    visit_rows = read_jsonl(M58_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M58_DIR / "trajectory_execution_plan_rows.jsonl")
    if not goal_rows:
        raise SystemExit("missing M03 episode_goal_eval_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M58 dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    if not plan_rows:
        raise SystemExit("missing M58 trajectory_execution_plan_rows.jsonl")

    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in oracle_rows}
    candidate_goal_rows = m27.build_candidate_goal_eval_rows(visit_rows, eval_index, oracle_index)
    candidate_goal_rows = enrich_candidate_goal_rows(candidate_goal_rows, visit_rows)
    scan_metric_rows, context_rows, aggregate_rows = m27.build_metric_rows(candidate_goal_rows)
    scan_metric_rows = attach_plan_metadata(scan_metric_rows, plan_rows)
    source_rows = aggregate_scan_rows(m27, scan_metric_rows)
    policy_goal_metric_rows = scan_metric_rows + context_rows + aggregate_rows + source_rows
    failure_rows = m27.build_failure_rows(scan_metric_rows)
    pairwise_rows = build_pairwise_rows(aggregate_rows, source_rows)
    source_gap_recovery_rows = build_source_gap_goal_recovery_rows(scan_metric_rows)
    leakage_audit_rows = build_leakage_audit_rows(candidate_goal_rows, eval_index)
    gate_rows = build_readiness_gate_rows(
        m58_coverage,
        candidate_goal_rows,
        aggregate_rows,
        source_rows,
        source_gap_recovery_rows,
        leakage_audit_rows,
    )
    ready_for_m60 = bool(gate_rows) and all(row.get("status") == "pass" for row in gate_rows)
    claim_boundary_rows = build_claim_boundary_rows(ready_for_m60)
    route_decision_rows = build_route_decision_rows(ready_for_m60)
    m60_command_rows = build_m60_command_rows(ready_for_m60)

    method_full = metric_lookup(aggregate_rows, M58_POLICY)
    base_full = metric_lookup(aggregate_rows, BASE_H001_POLICY)
    task_full = metric_lookup(aggregate_rows, TASK_AGNOSTIC_POLICY)
    detector_full = metric_lookup(aggregate_rows, DETECTOR_POLICY)
    method_gap = metric_lookup(source_rows, M58_POLICY, "source_gap")
    base_gap = metric_lookup(source_rows, BASE_H001_POLICY, "source_gap")
    task_gap = metric_lookup(source_rows, TASK_AGNOSTIC_POLICY, "source_gap")
    detector_gap = metric_lookup(source_rows, DETECTOR_POLICY, "source_gap")
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    source_gap_rows = [row for row in source_gap_recovery_rows if row.get("source_boundary") == "source_gap"]
    recovery_counts = Counter(
        "recovered"
        if row.get("recovered_vs_base_h001")
        else "lost"
        if row.get("lost_vs_base_h001")
        else "same"
        for row in source_gap_rows
    )

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready_for_m60 else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m58_status": m58_coverage.get("status"),
        "eval_episode_rows": len(goal_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_task_context_rows": len(context_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "source_boundary_aggregate_rows": len(source_rows),
        "policy_goal_metric_rows": len(policy_goal_metric_rows),
        "primary_failure_rows": len(failure_rows),
        "primary_metric": PRIMARY_METRIC,
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "m58_policy_id": M58_POLICY,
        "base_h001_policy_id": BASE_H001_POLICY,
        "m58_full_primary_proxy_sr": method_full.get("primary_proxy_sr"),
        "base_h001_full_primary_proxy_sr": base_full.get("primary_proxy_sr"),
        "task_agnostic_full_primary_proxy_sr": task_full.get("primary_proxy_sr"),
        "detector_full_primary_proxy_sr": detector_full.get("primary_proxy_sr"),
        "m58_source_gap_primary_proxy_sr": method_gap.get("primary_proxy_sr"),
        "base_h001_source_gap_primary_proxy_sr": base_gap.get("primary_proxy_sr"),
        "task_agnostic_source_gap_primary_proxy_sr": task_gap.get("primary_proxy_sr"),
        "detector_source_gap_primary_proxy_sr": detector_gap.get("primary_proxy_sr"),
        "m58_minus_base_h001_full_sr_delta": delta(
            method_full.get("primary_proxy_sr"), base_full.get("primary_proxy_sr")
        ),
        "m58_minus_base_h001_source_gap_sr_delta": delta(
            method_gap.get("primary_proxy_sr"), base_gap.get("primary_proxy_sr")
        ),
        "m58_minus_task_agnostic_source_gap_sr_delta": delta(
            method_gap.get("primary_proxy_sr"), task_gap.get("primary_proxy_sr")
        ),
        "source_gap_recovery_rows": len(source_gap_recovery_rows),
        "source_gap_recovered_vs_base_context_rows": recovery_counts.get("recovered", 0),
        "source_gap_lost_vs_base_context_rows": recovery_counts.get("lost", 0),
        "source_gap_same_vs_base_context_rows": recovery_counts.get("same", 0),
        "ready_for_m60_trajectory_contract": ready_for_m60,
        "requires_docker_now": False,
        "requires_docker_next": ready_for_m60,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "human_intent_main_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "high_path_tail_candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "high_path_tail_policy_goal_metric_rows.jsonl", policy_goal_metric_rows)
        write_jsonl(output_dir / "high_path_tail_goal_failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "pairwise_policy_delta_rows.jsonl", pairwise_rows)
        write_jsonl(output_dir / "source_gap_goal_recovery_rows.jsonl", source_gap_recovery_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_jsonl(output_dir / "m60_command_rows.jsonl", m60_command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, aggregate_rows, source_rows, pairwise_rows, gate_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
