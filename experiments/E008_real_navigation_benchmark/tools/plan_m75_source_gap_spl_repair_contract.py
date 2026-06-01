#!/usr/bin/env python3
"""Build the E008-M75 source-gap/SPL repair contract after M74."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M71_DIR = EXP_ROOT / "artifacts" / "E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0"
M72_DIR = EXP_ROOT / "artifacts" / "E008-M72_full_val_mini_detector_policy_trajectory_contract_v0"
M73_DIR = EXP_ROOT / "artifacts" / "E008-M73_full_val_mini_detector_policy_trajectory_execution_smoke_v0"
M74_DIR = EXP_ROOT / "artifacts" / "E008-M74_full_val_mini_detector_policy_result_interpretation_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M75_source_gap_spl_repair_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M75_source_gap_spl_repair_contract_v0"

VERSION = "e008_m75_source_gap_spl_repair_contract_v0"
READY_STATUS = "e008_m75_source_gap_spl_repair_contract_ready"
BLOCKED_STATUS = "e008_m75_source_gap_spl_repair_contract_blocked"
NEXT_UNIT = "E008-M76 full-val-mini source-gap/SPL repair row materialization smoke"

PRIMARY_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
PATH_COST_POLICY = "path_cost_ascending_reachable_subset_v0"
TRADEOFF_POLICY = "confidence_path_cost_tradeoff_reachable_subset_v0"
ALL_CANDIDATE_POLICY = "detector_confidence_all_candidates_v0"


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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def metric_scope(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == scope]


def build_failure_episode_repair_rows(
    m71_failure_rows: list[dict[str, Any]],
    m73_scan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in m73_scan_rows:
        by_episode[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for row in sorted(m71_failure_rows, key=lambda item: str(item.get("adapter_episode_id"))):
        episode_id = str(row.get("adapter_episode_id"))
        trajectory_rows = by_episode.get(episode_id, [])
        source_gap = any(bool(item.get("diagnostic_source_gap_boundary")) for item in trajectory_rows)
        path_lengths = [finite_float(item.get("PathLengthM")) for item in trajectory_rows]
        visits = [finite_float(item.get("CandidateVisits")) for item in trajectory_rows]
        failure_class = str(row.get("failure_class"))
        repair_target, repair_route = classify_failure_repair(failure_class, source_gap)
        out.append(
            {
                "version": VERSION,
                "row_type": "failure_episode_repair_target",
                "adapter_episode_id": episode_id,
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "m71_failure_class": failure_class,
                "diagnostic_source_gap_boundary": source_gap,
                "m71_min_best_any_viewpoint_xz_m": row.get("min_best_any_viewpoint_xz_m"),
                "m71_min_best_goal_xz_m": row.get("min_best_goal_xz_m"),
                "m73_policy_rows": len(trajectory_rows),
                "m73_success_rows": sum(1 for item in trajectory_rows if bool(item.get("trajectory_success"))),
                "m73_mean_path_length_m": mean(path_lengths),
                "m73_mean_candidate_visits": mean(visits),
                "repair_target": repair_target,
                "repair_route": repair_route,
                "rerank_only_sufficient": False
                if source_gap or failure_class in {"severe_candidate_source_coverage_gap", "candidate_region_gap"}
                else None,
                "claim_boundary": "diagnostic failure target only; do not use failure class or eval distances as policy input",
            }
        )
    return out


def classify_failure_repair(failure_class: str, source_gap: bool) -> tuple[str, str]:
    if failure_class == "severe_candidate_source_coverage_gap":
        return (
            "candidate_source_expansion_required",
            "add_or_reweight policy-visible candidate-source evidence before trajectory rerun",
        )
    if source_gap or failure_class == "candidate_region_gap":
        return (
            "candidate_region_or_source_gap_repair_required",
            "materialize source-gap-aware candidate-source probes and keep source-gap reporting separate",
        )
    if failure_class in {"relaxed_viewpoint_or_goal_near_miss", "moderate_localization_near_miss"}:
        return (
            "localization_threshold_boundary",
            "report as source-ready localization/threshold boundary; do not claim H001 policy failure",
        )
    return ("manual_review_required", "inspect failure rows before materialization")


def build_path_cost_case_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in pairwise_rows if row.get("baseline_policy_id") == PRIMARY_DETECTOR_POLICY]
    out: list[dict[str, Any]] = []
    for row in rows:
        delta_spl = finite_float(row.get("delta_SPL"))
        delta_path = finite_float(row.get("delta_PathLengthM"))
        delta_visits = finite_float(row.get("method_CandidateVisits")) - finite_float(row.get("baseline_CandidateVisits")) if finite_float(row.get("method_CandidateVisits")) is not None and finite_float(row.get("baseline_CandidateVisits")) is not None else None
        if (delta_spl or 0.0) > 0:
            case_type = "path_cost_helped_spl"
        elif (delta_spl or 0.0) < 0:
            case_type = "path_cost_hurt_spl"
        else:
            case_type = "path_cost_tied_spl"
        out.append(
            {
                "version": VERSION,
                "row_type": "path_cost_case",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "diagnostic_source_gap_boundary": row.get("diagnostic_source_gap_boundary"),
                "delta_SR": row.get("delta_SR"),
                "delta_SPL": delta_spl,
                "delta_PathLengthM": delta_path,
                "delta_CandidateVisits": delta_visits,
                "case_type": case_type,
                "repair_signal": "path-cost can be a guarded tie-breaker/tail slot, not a primary ordering rule",
                "supports_final_navigation_claim": False,
            }
        )
    return out


def summarize_path_cases(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("case_type")) for row in rows)
    return {
        "path_cost_case_rows": len(rows),
        "path_cost_helped_spl_rows": counts.get("path_cost_helped_spl", 0),
        "path_cost_hurt_spl_rows": counts.get("path_cost_hurt_spl", 0),
        "path_cost_tied_spl_rows": counts.get("path_cost_tied_spl", 0),
        "mean_delta_SPL": mean([finite_float(row.get("delta_SPL")) for row in rows]),
        "mean_delta_PathLengthM": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
        "mean_delta_CandidateVisits": mean([finite_float(row.get("delta_CandidateVisits")) for row in rows]),
    }


def build_repair_problem_rows(
    m74_coverage: dict[str, Any],
    failure_rows: list[dict[str, Any]],
    path_case_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    source_gap_failures = [row for row in failure_rows if row.get("diagnostic_source_gap_boundary")]
    source_ready_failures = [row for row in failure_rows if not row.get("diagnostic_source_gap_boundary")]
    return [
        {
            "version": VERSION,
            "problem_id": "source_gap_recovery_failure",
            "evidence": "M74 source-gap trajectory SR is 0.0.",
            "affected_episode_rows": len(source_gap_failures),
            "current_value": m74_coverage.get("source_gap_SR"),
            "required_repair": "candidate-source expansion or external/current-observation fallback before reranking",
            "rerank_only_sufficient": False,
            "blocks_final_navigation_claim": True,
        },
        {
            "version": VERSION,
            "problem_id": "path_cost_spl_regression",
            "evidence": "Path-cost ordering lowers mean path length but loses SPL against detector confidence.",
            "affected_episode_rows": path_case_summary.get("path_cost_hurt_spl_rows"),
            "current_value": m74_coverage.get("path_cost_delta_SPL_vs_primary_detector"),
            "required_repair": "SPL guard: keep detector-confidence primary and use path-cost only as bounded tie-breaker/tail slot",
            "rerank_only_sufficient": True,
            "blocks_final_navigation_claim": True,
        },
        {
            "version": VERSION,
            "problem_id": "budget5_deployability_failure",
            "evidence": "M74 budget-5 minimum GoalEvalProxySR is too low.",
            "affected_episode_rows": 30,
            "current_value": m74_coverage.get("budget5_min_GoalEvalProxySR"),
            "required_repair": "materialize fixed-budget policy rows and require no success loss against detector confidence",
            "rerank_only_sufficient": None,
            "blocks_final_navigation_claim": True,
        },
        {
            "version": VERSION,
            "problem_id": "source_ready_localization_threshold_failures",
            "evidence": "Four source-ready all-policy failures remain and are mostly near-miss/localization boundaries.",
            "affected_episode_rows": len(source_ready_failures),
            "current_value": len(source_ready_failures),
            "required_repair": "report separately from source-gap recovery; do not convert threshold sensitivity into H001 policy gain",
            "rerank_only_sufficient": False,
            "blocks_final_navigation_claim": True,
        },
    ]


def build_policy_repair_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": "detector_confidence_reachable_subset_v0",
            "policy_role": "primary_baseline_to_preserve",
            "materialize_in_m76": True,
            "ranking_principle": "reachable detector-confidence ordering",
            "expected_effect": "preserve current best SPL/candidate-visit baseline",
            "allowed_inputs": [
                "label_canonical",
                "confidence",
                "selection_score",
                "path_ready",
                "navmesh_validation_status",
                "candidate_source_role",
            ],
            "blocked_inputs": blocked_policy_inputs(),
        },
        {
            "version": VERSION,
            "policy_id": "spl_guarded_confidence_path_tail_budget5_v0",
            "policy_role": "selected_repair_candidate",
            "materialize_in_m76": True,
            "ranking_principle": (
                "preserve detector-confidence top candidates, then add one bounded path-cost/source-diverse tail "
                "candidate only from policy-visible candidate fields"
            ),
            "expected_effect": "avoid path-cost SPL regression while probing budget-5 recovery",
            "allowed_inputs": [
                "label_canonical",
                "confidence",
                "selection_score",
                "source_to_candidate_path_cost_m",
                "candidate_source_role",
                "frame_pose_role",
                "observation_pose_id",
                "path_ready",
                "navmesh_validation_status",
                "candidate_rank_m09",
                "task_context_id",
            ],
            "blocked_inputs": blocked_policy_inputs(),
        },
        {
            "version": VERSION,
            "policy_id": "candidate_source_expansion_probe_v0",
            "policy_role": "source_gap_probe_not_final_policy",
            "materialize_in_m76": True,
            "ranking_principle": (
                "create source-gap probe rows from policy-visible detector/source health signals; do not use "
                "diagnostic source-gap labels to rank"
            ),
            "expected_effect": "separate candidate-source absence from ordering/SPL failure",
            "allowed_inputs": [
                "candidate_count",
                "path_ready_candidate_count",
                "source_role_counts",
                "frame_pose_role",
                "observation_pose_id",
                "label_canonical",
                "confidence",
                "source_to_candidate_path_cost_m",
            ],
            "blocked_inputs": blocked_policy_inputs()
            + ["diagnostic_source_gap_boundary", "m71_failure_class"],
        },
        {
            "version": VERSION,
            "policy_id": "localization_threshold_reporting_v0",
            "policy_role": "evaluation_boundary_not_policy",
            "materialize_in_m76": False,
            "ranking_principle": "report near-miss/localization rows as boundary evidence only",
            "expected_effect": "prevents threshold sensitivity from being misreported as navigation policy gain",
            "allowed_inputs": [],
            "blocked_inputs": blocked_policy_inputs(),
        },
    ]


def blocked_policy_inputs() -> list[str]:
    return [
        "ObjectNav goal position",
        "ObjectNav viewpoint position",
        "candidate_to_eval_goal_*",
        "candidate_to_nearest_eval_viewpoint_*",
        "primary_eval_hit",
        "trajectory_success",
        "SR",
        "SPL",
        "success_proposal_uid",
        "success_source_role",
        "m70_primary_first_hit_rank",
        "m70_primary_first_hit_cost_m",
        "m70_primary_spl_proxy",
        "M71 failure class",
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    allowed = [
        ("candidate_label_and_category", ["label_canonical", "object_category"]),
        ("detector_score", ["confidence", "selection_score", "ranking_score"]),
        ("path_and_navmesh_source", ["source_to_candidate_path_cost_m", "path_ready", "navmesh_validation_status"]),
        ("source_health", ["candidate_count", "path_ready_candidate_count", "source_role_counts"]),
        ("observation_source", ["frame_pose_role", "observation_pose_id", "candidate_source_role"]),
        ("task_context_condition", ["task_context_id"]),
    ]
    blocked = [
        ("objectnav_eval_geometry", ["candidate_to_eval_goal_*", "candidate_to_nearest_eval_viewpoint_*"]),
        ("success_labels", ["primary_eval_hit", "trajectory_success", "SR", "SPL"]),
        ("diagnostic_failure_labels", ["diagnostic_source_gap_boundary", "m71_failure_class"]),
        ("posthoc_success_identity", ["success_proposal_uid", "success_source_role"]),
        ("m70_proxy_oracle_fields", ["m70_primary_first_hit_rank", "m70_primary_first_hit_cost_m", "m70_primary_spl_proxy"]),
    ]
    rows: list[dict[str, Any]] = []
    for group, fields in allowed:
        rows.append(
            {
                "version": VERSION,
                "input_group": group,
                "input_status": "allowed_for_policy",
                "fields": fields,
                "rationale": "Available before evaluation and needed for repair materialization.",
            }
        )
    for group, fields in blocked:
        rows.append(
            {
                "version": VERSION,
                "input_group": group,
                "input_status": "blocked_for_policy",
                "fields": fields,
                "rationale": "Evaluation-only or posthoc diagnostic information; may be used only for reporting.",
            }
        )
    return rows


def build_gate_rows(
    missing_inputs: list[str],
    m74_coverage: dict[str, Any],
    path_case_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        gate("m74_input_ready", "pass" if not missing_inputs else "fail", "M74 interpretation artifact is required."),
        gate("leakage_guard_ready", "pass", "Allowed/blocked input groups are fixed before materialization."),
        gate(
            "source_gap_requires_candidate_source_repair",
            "pass" if finite_float(m74_coverage.get("source_gap_SR")) == 0.0 else "warning",
            "Source-gap SR is zero; reranking alone should not be treated as sufficient.",
        ),
        gate(
            "spl_guard_required",
            "pass" if (path_case_summary.get("path_cost_hurt_spl_rows") or 0) > 0 else "warning",
            "Path-cost ordering hurts SPL on multiple episodes and must be guarded.",
        ),
        gate(
            "budget5_deployability_blocked",
            "fail",
            "Budget-5 proxy SR remains below deployable search requirements.",
            blocks_final=True,
        ),
        gate(
            "trajectory_launch_ready",
            "fail",
            "M75 is a contract only; M76 must materialize repair rows before any Docker trajectory rerun.",
            blocks_final=True,
        ),
        gate(
            "external_navigation_baseline_ready",
            "fail",
            "VLFM / HM3D-OVON / GOAT-Bench-style baselines are still not integrated.",
            blocks_final=True,
        ),
    ]


def gate(gate_id: str, status: str, rationale: str, blocks_final: bool | None = None) -> dict[str, Any]:
    if blocks_final is None:
        blocks_final = status in {"fail", "warning"}
    return {
        "version": VERSION,
        "gate_id": gate_id,
        "gate_status": status,
        "blocks_final_real_navigation_claim": blocks_final,
        "rationale": rationale,
    }


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_gap_repair_contract",
            "claim_status": "contract_only",
            "allowed_statement": "M75 identifies source-gap candidate-source repair as required before navigation claims.",
            "blocked_statement": "M75 proves source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "spl_guard_contract",
            "claim_status": "contract_only",
            "allowed_statement": "M75 fixes an SPL guard principle for the next materialization step.",
            "blocked_statement": "M75 proves improved SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "deployable_search_policy",
            "claim_status": "blocked",
            "allowed_statement": "Budget-5 weakness is explicitly tracked.",
            "blocked_statement": "The current policy is deployable under fixed budget.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "claim_status": "blocked",
            "allowed_statement": "M75 prepares repair rows for later simulator execution.",
            "blocked_statement": "Final real navigation SR/SPL is ready.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "selected_next_unit": NEXT_UNIT,
            "selected_route": "repair_row_materialization_before_trajectory",
            "launch_long_job_now": False,
            "next_action": (
                "Materialize detector-confidence-preserving, SPL-guarded, and candidate-source probe rows; "
                "do not launch Docker trajectories until row materialization and leakage checks pass."
            ),
        }
    ]


def write_report(
    generated_at: str,
    coverage: dict[str, Any],
    repair_problem_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    path_case_summary: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M75 Source-Gap/SPL Repair Contract",
        "",
        f"Generated: {generated_at}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M74 status: `{coverage.get('m74_status')}`.",
        f"- Source-gap SR from M74: {fmt(coverage.get('source_gap_SR'))}.",
        f"- Budget-5 minimum proxy SR from M74: {fmt(coverage.get('budget5_min_GoalEvalProxySR'))}.",
        f"- Path-cost delta SPL vs detector confidence: {fmt(coverage.get('path_cost_delta_SPL_vs_primary_detector'))}.",
        f"- Path-cost helped / hurt / tied SPL rows: {path_case_summary['path_cost_helped_spl_rows']} / {path_case_summary['path_cost_hurt_spl_rows']} / {path_case_summary['path_cost_tied_spl_rows']}.",
        f"- Failure episode repair targets: {len(failure_rows)}.",
        "",
        "## Repair Problems",
        "",
        "| problem_id | affected_episode_rows | current_value | required_repair |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in repair_problem_rows:
        lines.append(
            "| {problem_id} | {affected_episode_rows} | {current_value} | {required_repair} |".format(
                problem_id=row["problem_id"],
                affected_episode_rows=row["affected_episode_rows"],
                current_value=fmt(row["current_value"]),
                required_repair=row["required_repair"],
            )
        )
    lines += [
        "",
        "## Failure Episode Targets",
        "",
        "| episode | object | M71 class | source_gap | repair_target |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in failure_rows:
        lines.append(
            "| {episode} | {obj} | {failure} | {source_gap} | {target} |".format(
                episode=row["adapter_episode_id"],
                obj=row["object_category"],
                failure=row["m71_failure_class"],
                source_gap=str(row["diagnostic_source_gap_boundary"]).lower(),
                target=row["repair_target"],
            )
        )
    lines += [
        "",
        "## Policy Contracts",
        "",
        "| policy_id | role | materialize_in_m76 | expected_effect |",
        "| --- | --- | --- | --- |",
    ]
    for row in policy_rows:
        lines.append(
            "| {policy_id} | {role} | {materialize} | {effect} |".format(
                policy_id=row["policy_id"],
                role=row["policy_role"],
                materialize=str(row["materialize_in_m76"]).lower(),
                effect=row["expected_effect"],
            )
        )
    lines += [
        "",
        "## Gates",
        "",
        "| gate_id | gate_status | blocks_final_real_navigation_claim | rationale |",
        "| --- | --- | --- | --- |",
    ]
    for row in gate_rows:
        lines.append(
            "| {gate_id} | {gate_status} | {blocks} | {rationale} |".format(
                gate_id=row["gate_id"],
                gate_status=row["gate_status"],
                blocks=str(row["blocks_final_real_navigation_claim"]),
                rationale=row["rationale"],
            )
        )
    lines += [
        "",
        "## Decision",
        "",
        f"- Selected next unit: {NEXT_UNIT}.",
        "- M75 is a contract artifact, not a trajectory execution result.",
        "- Source-gap repair must be candidate-source aware; reranking existing failed candidates is not sufficient.",
        "- SPL repair must preserve detector-confidence behavior and use path cost only as a guarded signal.",
    ]
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    required = {
        "m71_failure_rows": M71_DIR / "failure_episode_rows.jsonl",
        "m72_coverage": M72_DIR / "coverage.json",
        "m73_coverage": M73_DIR / "coverage.json",
        "m73_policy_rows": M73_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl",
        "m73_pairwise_rows": M73_DIR / "pairwise_policy_delta_rows.jsonl",
        "m74_coverage": M74_DIR / "coverage.json",
        "m74_source_boundary_rows": M74_DIR / "source_boundary_rows.jsonl",
        "m74_budget_boundary_rows": M74_DIR / "budget_boundary_rows.jsonl",
    }
    missing_inputs = [name for name, path in required.items() if not path.exists()]
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m74_coverage = read_json(required["m74_coverage"])
    m73_rows = read_jsonl(required["m73_policy_rows"])
    m73_scan_rows = metric_scope(m73_rows, "scan_task_policy")
    pairwise_rows = read_jsonl(required["m73_pairwise_rows"])
    m71_failure_rows = read_jsonl(required["m71_failure_rows"])

    path_case_rows = build_path_cost_case_rows(pairwise_rows)
    path_case_summary = summarize_path_cases(path_case_rows)
    failure_rows = build_failure_episode_repair_rows(m71_failure_rows, m73_scan_rows)
    repair_problem_rows = build_repair_problem_rows(m74_coverage, failure_rows, path_case_summary)
    policy_rows = build_policy_repair_contract_rows()
    input_guard_rows = build_input_guard_rows()
    gate_rows = build_gate_rows(missing_inputs, m74_coverage, path_case_summary)
    claim_boundary_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    ready = not missing_inputs and m74_coverage.get("status") == "e008_m74_full_val_mini_detector_policy_result_interpretation_ready"
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": generated_at,
        "missing_inputs": missing_inputs,
        "m74_status": m74_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "source_gap_SR": m74_coverage.get("source_gap_SR"),
        "source_gap_failure_episode_rows": sum(1 for row in failure_rows if row.get("diagnostic_source_gap_boundary")),
        "source_ready_failure_episode_rows": sum(1 for row in failure_rows if not row.get("diagnostic_source_gap_boundary")),
        "budget5_min_GoalEvalProxySR": m74_coverage.get("budget5_min_GoalEvalProxySR"),
        "path_cost_delta_SPL_vs_primary_detector": m74_coverage.get("path_cost_delta_SPL_vs_primary_detector"),
        "path_cost_helped_spl_rows": path_case_summary.get("path_cost_helped_spl_rows"),
        "path_cost_hurt_spl_rows": path_case_summary.get("path_cost_hurt_spl_rows"),
        "path_cost_tied_spl_rows": path_case_summary.get("path_cost_tied_spl_rows"),
        "repair_problem_rows": len(repair_problem_rows),
        "failure_episode_repair_rows": len(failure_rows),
        "path_cost_case_rows": len(path_case_rows),
        "policy_repair_contract_rows": len(policy_rows),
        "input_guard_rows": len(input_guard_rows),
        "gate_rows": len(gate_rows),
        "gate_pass_rows": sum(1 for row in gate_rows if row["gate_status"] == "pass"),
        "gate_fail_rows": sum(1 for row in gate_rows if row["gate_status"] == "fail"),
        "claim_boundary_rows": len(claim_boundary_rows),
        "repair_contract_ready": ready,
        "repair_row_materialization_ready_now": False,
        "trajectory_execution_ready_now": False,
        "launch_long_job_now": False,
        "source_gap_requires_candidate_source_repair": True,
        "spl_guard_required": True,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "repair_problem_rows.jsonl", repair_problem_rows)
    write_jsonl(ARTIFACT_DIR / "failure_episode_repair_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "path_cost_case_rows.jsonl", path_case_rows)
    write_json(ARTIFACT_DIR / "path_cost_case_summary.json", path_case_summary)
    write_jsonl(ARTIFACT_DIR / "policy_repair_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(ARTIFACT_DIR / "evaluation_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_report(generated_at, coverage, repair_problem_rows, failure_rows, path_case_summary, policy_rows, gate_rows)

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)

    print(json.dumps({"status": coverage["status"], "selected_next_unit": NEXT_UNIT}, sort_keys=True))


if __name__ == "__main__":
    main()
