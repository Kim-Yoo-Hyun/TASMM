#!/usr/bin/env python3
"""Plan a loss-safe candidate-source expansion contract after M78."""

from __future__ import annotations

import json
import math
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M68_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M69_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E008-M75_source_gap_spl_repair_contract_v0"
M78_DIR = EXP_ROOT / "artifacts" / "E008-M78_source_gap_spl_repair_result_interpretation_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0"
)

VERSION = "e008_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract_v0"
READY_STATUS = "e008_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract_ready"
BLOCKED_STATUS = "e008_m79_source_gap_candidate_source_expansion_loss_safe_policy_contract_blocked"
NEXT_UNIT = "E008-M80 full-val-mini loss-safe candidate-source expansion row materialization smoke"

BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
PRIMARY_BUDGET = 5
EXPANDED_BUDGET = 8


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


def finite_int(value: object, default: int = 10**9) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def group_rows(rows: list[dict[str, Any]], *keys: str) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key)) for key in keys)].append(row)
    return grouped


def build_navmesh_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("proposal_uid")): row for row in rows if row.get("proposal_uid")}


def top_budget_summary(
    visit_rows: list[dict[str, Any]],
    navmesh_index: dict[str, dict[str, Any]],
    *,
    budget: int = PRIMARY_BUDGET,
) -> dict[str, Any]:
    top_rows = sorted(visit_rows, key=lambda row: finite_int(row.get("visit_rank")))[:budget]
    joined_rows = []
    for row in top_rows:
        joined = dict(row)
        joined.update(navmesh_index.get(str(row.get("proposal_uid")), {}))
        joined_rows.append(joined)
    return {
        "top_budget_rows": len(joined_rows),
        "top_budget_unique_observation_pose_ids": len(
            {row.get("observation_pose_id") for row in joined_rows if row.get("observation_pose_id")}
        ),
        "top_budget_unique_frame_pose_roles": len(
            {row.get("frame_pose_role") for row in joined_rows if row.get("frame_pose_role")}
        ),
        "top_budget_mean_source_to_candidate_path_cost_m": mean(
            [finite_float(row.get("source_to_candidate_path_cost_m")) for row in joined_rows]
        ),
        "top_budget_max_source_to_candidate_path_cost_m": max(
            [
                value
                for value in [finite_float(row.get("source_to_candidate_path_cost_m")) for row in joined_rows]
                if value is not None
            ],
            default=None,
        ),
        "top_budget_proposal_uids": [row.get("proposal_uid") for row in joined_rows],
    }


def build_expansion_case_rows(
    source_gap_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    scan_source_rows: list[dict[str, Any]],
    visit_rows: list[dict[str, Any]],
    navmesh_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_by_episode = {str(row.get("adapter_episode_id")): row for row in scan_source_rows}
    visits_by_episode_policy = group_rows(visit_rows, "adapter_episode_id", "policy_id")
    navmesh_index = build_navmesh_index(navmesh_rows)

    rows: list[dict[str, Any]] = []
    for row in source_gap_rows:
        episode = str(row.get("adapter_episode_id"))
        source = source_by_episode.get(episode, {})
        summary = top_budget_summary(
            visits_by_episode_policy.get((episode, BASELINE_POLICY), []),
            navmesh_index,
            budget=PRIMARY_BUDGET,
        )
        rows.append(
            {
                "version": VERSION,
                "row_type": "expansion_case",
                "case_type": "source_gap_unresolved",
                "adapter_episode_id": episode,
                "scene_key": source.get("scene_key"),
                "scan_id": source.get("scan_id"),
                "object_category": row.get("object_category"),
                "selected_for_m80": True,
                "candidate_rows": source.get("candidate_rows"),
                "path_ready_candidate_rows": source.get("path_ready_candidate_rows"),
                "source_boundary_status": source.get("source_boundary_status"),
                "baseline_budget5_hit": row.get("baseline_budget5_hit"),
                "baseline_full_rank_hit": row.get("baseline_full_rank_hit"),
                "best_full_rank_any_viewpoint_xz_m": row.get("best_full_rank_any_viewpoint_xz_m"),
                "expansion_requirement": "new_or_exposed_candidate_source_evidence",
                "selected_expansion_route": "loss_safe_observation_source_expansion_probe_v0",
                "m80_expected_action": "materialize detector top5 core plus append-only source/observation expansion rows",
                **summary,
                "policy_input_boundary": "diagnostic source-gap labels and eval distances are not policy inputs.",
            }
        )

    for row in loss_rows:
        rows.append(
            {
                "version": VERSION,
                "row_type": "expansion_case",
                "case_type": "budget5_loss_sentinel",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "object_category": row.get("object_category"),
                "selected_for_m80": True,
                "baseline_hit_rank": row.get("baseline_hit_rank"),
                "baseline_hit_proposal_uid": row.get("baseline_hit_proposal_uid"),
                "guarded_tail_proposal_uid": row.get("guarded_tail_proposal_uid"),
                "failure_mechanism": row.get("failure_mechanism"),
                "expansion_requirement": "preserve_detector_confidence_budget5_before_any_append_or_path_cost_stage",
                "selected_expansion_route": "loss_sentinel_top5_preservation_check_v0",
                "m80_expected_action": "assert detector-confidence top5 proposal order is unchanged for every materialized policy.",
                "policy_input_boundary": "loss identity is post-hoc reporting only; M80 policy cannot branch on this episode id.",
            }
        )

    for row in failure_rows:
        if bool(row.get("diagnostic_source_gap_boundary")):
            continue
        rows.append(
            {
                "version": VERSION,
                "row_type": "expansion_case",
                "case_type": "localization_boundary_control",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "scan_id": row.get("scan_id"),
                "object_category": row.get("object_category"),
                "selected_for_m80": False,
                "m75_repair_target": row.get("repair_target"),
                "m71_failure_class": row.get("m71_failure_class"),
                "expansion_requirement": "report_separately_from_source_gap_gain",
                "selected_expansion_route": "claim_boundary_control_only",
                "m80_expected_action": "do not count localization/threshold controls as source-gap recovery.",
                "policy_input_boundary": "M71 failure class is post-hoc reporting only.",
            }
        )
    return rows


def build_policy_contract_rows() -> list[dict[str, Any]]:
    blocked_inputs = [
        "ObjectNav goal position",
        "ObjectNav viewpoint position",
        "candidate_to_eval_goal_*",
        "candidate_to_nearest_eval_viewpoint_*",
        "primary_eval_hit",
        "trajectory_success",
        "SR",
        "SPL",
        "success_proposal_uid",
        "M71 failure class",
        "M78 guarded_loss identity",
    ]
    return [
        {
            "version": VERSION,
            "policy_id": "detector_confidence_budget5_core_v0",
            "policy_role": "loss_safe_core_baseline",
            "materialize_in_m80": True,
            "primary_budget_cap": PRIMARY_BUDGET,
            "ranking_principle": "copy detector-confidence reachable top-5 exactly before any source expansion.",
            "allowed_inputs": ["label_canonical", "confidence", "path_ready", "navmesh_validation_status"],
            "blocked_inputs": blocked_inputs,
            "required_invariant": "top5_proposal_uid_order_matches_detector_confidence_reachable_subset_v0",
            "expected_effect": "preserve the strongest budget-5 baseline and prevent M78-style path-cost eviction.",
        },
        {
            "version": VERSION,
            "policy_id": "loss_safe_append_source_probe_budget8_v0",
            "policy_role": "append_only_candidate_source_probe",
            "materialize_in_m80": True,
            "primary_budget_cap": EXPANDED_BUDGET,
            "ranking_principle": "keep detector-confidence top-5, then append up to three policy-visible source-diverse/path-ready candidates.",
            "allowed_inputs": [
                "label_canonical",
                "confidence",
                "source_to_candidate_path_cost_m",
                "candidate_source_role",
                "frame_pose_role",
                "observation_pose_id",
                "path_ready",
                "navmesh_validation_status",
                "candidate_rank_m09",
            ],
            "blocked_inputs": blocked_inputs,
            "required_invariant": "first_5_rows_match_detector_confidence_budget5_core_v0",
            "expected_effect": "measure whether source evidence can improve coverage without sacrificing budget-5 safety.",
        },
        {
            "version": VERSION,
            "policy_id": "loss_safe_observation_source_expansion_probe_v0",
            "policy_role": "new_source_plan_for_full_rank_source_gap_miss",
            "materialize_in_m80": True,
            "primary_budget_cap": None,
            "ranking_principle": "create a non-oracle observation/source expansion plan when existing full-rank candidates miss the target region.",
            "allowed_inputs": [
                "episode_start_pose",
                "navmesh",
                "rendered_source_pose_inventory",
                "candidate_count",
                "path_ready_candidate_count",
                "source_role_counts",
                "frame_pose_role",
                "observation_pose_id",
                "label_canonical",
                "confidence",
                "source_to_candidate_path_cost_m",
            ],
            "blocked_inputs": blocked_inputs,
            "required_invariant": "source_plan_uses_no_eval_goal_or_viewpoint",
            "expected_effect": "prepare candidate-source expansion that can later run rendering/detection without policy leakage.",
        },
        {
            "version": VERSION,
            "policy_id": "path_cost_secondary_tiebreak_only_v0",
            "policy_role": "guard_rule_not_standalone_policy",
            "materialize_in_m80": False,
            "primary_budget_cap": PRIMARY_BUDGET,
            "ranking_principle": "path cost may break ties or order appended probes, but cannot replace detector-confidence top-5.",
            "allowed_inputs": ["source_to_candidate_path_cost_m", "path_ready", "navmesh_validation_status"],
            "blocked_inputs": blocked_inputs,
            "required_invariant": "path_cost_never_evicts_detector_top5_under_budget5",
            "expected_effect": "prevents the M78 regression mechanism from recurring.",
        },
        {
            "version": VERSION,
            "policy_id": "localization_threshold_reporting_v0",
            "policy_role": "claim_boundary_not_policy",
            "materialize_in_m80": False,
            "primary_budget_cap": None,
            "ranking_principle": "keep near-miss and relaxed-threshold rows as reporting boundaries only.",
            "allowed_inputs": [],
            "blocked_inputs": blocked_inputs,
            "required_invariant": "no_threshold_boundary_row_is_counted_as_source_gap_recovery",
            "expected_effect": "prevents threshold sensitivity from becoming an inflated H001 policy claim.",
        },
    ]


def build_source_expansion_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "existing_candidate_append_probe",
            "route_status": "diagnostic_only",
            "m80_action": "append rows after preserved detector top-5 using existing path-ready candidates.",
            "why_needed": "quantifies budget cost of extra source probes without creating new detector outputs.",
            "claim_boundary": "Cannot solve full-rank source-gap misses if the existing candidate pool contains no strict hit.",
        },
        {
            "version": VERSION,
            "route_id": "non_oracle_observation_source_expansion",
            "route_status": "selected_for_plan",
            "m80_action": "materialize source/observation expansion plan rows for unresolved source-gap cases.",
            "why_needed": "M78 shows strict full-rank candidate rows still miss source-gap cases, so new observation/source evidence is required.",
            "claim_boundary": "M80 should materialize plans only; later rendering/detector jobs must follow long-task logging rules.",
        },
        {
            "version": VERSION,
            "route_id": "external_map_candidate_source_bridge",
            "route_status": "defer",
            "m80_action": "none",
            "why_needed": "Useful for final Direction B baseline pressure but should not replace the immediate source-gap repair contract.",
            "claim_boundary": "External map use needs separate baseline fairness and allowed-input accounting.",
        },
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "input_group": "candidate_label_score_path",
            "input_status": "allowed_for_policy",
            "fields": ["label_canonical", "confidence", "selection_score", "source_to_candidate_path_cost_m", "path_ready"],
            "rationale": "Available before evaluation and needed for loss-safe append ordering.",
        },
        {
            "version": VERSION,
            "input_group": "source_observation_inventory",
            "input_status": "allowed_for_policy",
            "fields": ["frame_pose_role", "observation_pose_id", "candidate_source_role", "source_role_counts"],
            "rationale": "Available source provenance needed to plan candidate-source expansion.",
        },
        {
            "version": VERSION,
            "input_group": "navmesh_source_geometry",
            "input_status": "allowed_for_policy",
            "fields": ["episode_start_pose", "navmesh", "source_position", "planned_observation_pose"],
            "rationale": "Allowed for non-oracle source expansion as long as eval goal/viewpoint is not used.",
        },
        {
            "version": VERSION,
            "input_group": "objectnav_eval_geometry",
            "input_status": "blocked_for_policy",
            "fields": ["ObjectNav goal position", "ObjectNav viewpoint position", "candidate_to_eval_goal_*"],
            "rationale": "Evaluation-only geometry may be used only after fixed policy rows are materialized.",
        },
        {
            "version": VERSION,
            "input_group": "success_or_failure_labels",
            "input_status": "blocked_for_policy",
            "fields": ["primary_eval_hit", "trajectory_success", "SR", "SPL", "M71 failure class", "M78 guarded_loss identity"],
            "rationale": "These are post-hoc diagnostics and cannot rank candidates or trigger policy branches.",
        },
    ]


def build_evaluation_gate_rows(expansion_cases: list[dict[str, Any]], m78_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    source_gap_cases = [row for row in expansion_cases if row.get("case_type") == "source_gap_unresolved"]
    loss_cases = [row for row in expansion_cases if row.get("case_type") == "budget5_loss_sentinel"]
    return [
        {
            "version": VERSION,
            "gate_id": "m78_ready",
            "gate_status": "pass"
            if m78_coverage.get("status") == "e008_m78_source_gap_spl_repair_result_interpretation_ready"
            else "fail",
            "rationale": "M79 starts only after M78 blocks direct trajectory promotion.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_requires_new_or_exposed_source",
            "gate_status": "pass" if source_gap_cases else "fail",
            "rationale": "M78 source-gap rows stay unresolved even under full-rank existing candidates.",
        },
        {
            "version": VERSION,
            "gate_id": "loss_safe_top5_preservation_required",
            "gate_status": "pass" if loss_cases else "warning",
            "rationale": "M78 provides a concrete budget-5 loss case caused by top-5 eviction.",
        },
        {
            "version": VERSION,
            "gate_id": "m80_materialization_before_evaluation",
            "gate_status": "pass",
            "rationale": "M79 is a contract only; M80 must materialize rows before proxy or trajectory evaluation.",
        },
        {
            "version": VERSION,
            "gate_id": "no_long_job_now",
            "gate_status": "pass",
            "rationale": "M79 creates only JSON/Markdown artifacts and does not launch rendering, detector, or Docker jobs.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_loss_safe_contract",
            "supported": True,
            "claim_boundary": "M79 supports a contract: future expansion must preserve detector-confidence budget-5 before adding source evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "M79 does not materialize or evaluate expanded candidate/source rows.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "Deployability requires M80/M81 budgeted metrics with no top-5 safety regression.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_navigation",
            "supported": False,
            "claim_boundary": "M79 does not execute Habitat trajectories or add navigation/search baselines.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "requires_docker_now": False,
            "launch_long_job_now": False,
            "rationale": "M80 should materialize loss-safe policy rows and source/observation expansion plan rows before any proxy evaluation or long job.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    expansion_case_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> str:
    case_lines = []
    for row in expansion_case_rows:
        if row.get("case_type") == "localization_boundary_control":
            continue
        case_lines.append(
            "| {case_type} | `{episode}` | {category} | {selected} | {route} |".format(
                case_type=row.get("case_type"),
                episode=row.get("adapter_episode_id"),
                category=row.get("object_category"),
                selected=row.get("selected_for_m80"),
                route=row.get("selected_expansion_route"),
            )
        )
    policy_lines = [
        f"| `{row['policy_id']}` | {row['policy_role']} | {row['materialize_in_m80']} | {row['required_invariant']} |"
        for row in policy_rows
    ]
    source_lines = [
        f"| `{row['route_id']}` | {row['route_status']} | {row['m80_action']} |"
        for row in source_rows
    ]
    return f"""# E008-M79 Source-Gap Candidate-Source Expansion And Loss-Safe Policy Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M78 status: `{coverage['m78_status']}`.
- Source-gap unresolved cases selected for expansion: {coverage['source_gap_expansion_cases']}.
- Budget-5 loss sentinel cases: {coverage['budget5_loss_sentinel_cases']}.
- Localization boundary controls: {coverage['localization_boundary_control_cases']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Expansion Cases

| case_type | adapter_episode_id | category | selected | route |
| --- | --- | --- | --- | --- |
{chr(10).join(case_lines)}

## Policy Contract

| policy_id | role | materialize in M80 | required invariant |
| --- | --- | --- | --- |
{chr(10).join(policy_lines)}

## Source Expansion Routes

| route_id | status | M80 action |
| --- | --- | --- |
{chr(10).join(source_lines)}

## Claim Boundary

- M79 is a contract artifact only.
- It supports the rule that candidate-source expansion must be loss-safe with respect to detector-confidence budget-5.
- It does not support source-gap recovery, deployable search policy, or final real navigation `SR` / `SPL`.
"""


def sync_derived() -> None:
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m78_coverage = read_json(M78_DIR / "coverage.json")
    source_gap_rows = read_jsonl(M78_DIR / "source_gap_interpretation_rows.jsonl")
    loss_rows = read_jsonl(M78_DIR / "budget5_loss_diagnosis_rows.jsonl")
    failure_rows = read_jsonl(M75_DIR / "failure_episode_repair_rows.jsonl")
    scan_source_rows = read_jsonl(M68_DIR / "scan_source_boundary_rows.jsonl")
    visit_rows = read_jsonl(M69_DIR / "candidate_visit_order_rows.jsonl")
    navmesh_rows = read_jsonl(M68_DIR / "candidate_navmesh_validation_rows.jsonl")

    missing_inputs = []
    for path, rows in [
        (M78_DIR / "coverage.json", [m78_coverage] if m78_coverage else []),
        (M78_DIR / "source_gap_interpretation_rows.jsonl", source_gap_rows),
        (M78_DIR / "budget5_loss_diagnosis_rows.jsonl", loss_rows),
        (M75_DIR / "failure_episode_repair_rows.jsonl", failure_rows),
        (M68_DIR / "scan_source_boundary_rows.jsonl", scan_source_rows),
        (M69_DIR / "candidate_visit_order_rows.jsonl", visit_rows),
        (M68_DIR / "candidate_navmesh_validation_rows.jsonl", navmesh_rows),
    ]:
        if not rows:
            missing_inputs.append(str(path))

    expansion_case_rows = build_expansion_case_rows(
        source_gap_rows,
        loss_rows,
        failure_rows,
        scan_source_rows,
        visit_rows,
        navmesh_rows,
    )
    policy_contract_rows = build_policy_contract_rows()
    source_expansion_contract_rows = build_source_expansion_contract_rows()
    input_guard_rows = build_input_guard_rows()
    evaluation_gate_rows = build_evaluation_gate_rows(expansion_case_rows, m78_coverage)
    claim_boundary_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    source_gap_case_count = sum(1 for row in expansion_case_rows if row.get("case_type") == "source_gap_unresolved")
    loss_sentinel_count = sum(1 for row in expansion_case_rows if row.get("case_type") == "budget5_loss_sentinel")
    localization_control_count = sum(
        1 for row in expansion_case_rows if row.get("case_type") == "localization_boundary_control"
    )
    materialize_policy_count = sum(1 for row in policy_contract_rows if row.get("materialize_in_m80"))

    status = READY_STATUS if not missing_inputs else BLOCKED_STATUS
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m78_status": m78_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "source_gap_expansion_cases": source_gap_case_count,
        "budget5_loss_sentinel_cases": loss_sentinel_count,
        "localization_boundary_control_cases": localization_control_count,
        "policy_contract_rows": len(policy_contract_rows),
        "m80_materialize_policy_rows": materialize_policy_count,
        "source_expansion_contract_rows": len(source_expansion_contract_rows),
        "input_guard_rows": len(input_guard_rows),
        "evaluation_gate_rows": len(evaluation_gate_rows),
        "claim_boundary_rows": len(claim_boundary_rows),
        "detector_budget5_preservation_required": True,
        "reranking_only_repair_sufficient": False,
        "candidate_source_expansion_required": True,
        "trajectory_execution_ready_now": False,
        "goal_evaluation_ready_now": False,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT,
    }

    write_jsonl(ARTIFACT_DIR / "expansion_case_rows.jsonl", expansion_case_rows)
    write_jsonl(ARTIFACT_DIR / "loss_safe_policy_contract_rows.jsonl", policy_contract_rows)
    write_jsonl(ARTIFACT_DIR / "source_expansion_contract_rows.jsonl", source_expansion_contract_rows)
    write_jsonl(ARTIFACT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(ARTIFACT_DIR / "evaluation_gate_rows.jsonl", evaluation_gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, expansion_case_rows, policy_contract_rows, source_expansion_contract_rows),
        encoding="utf-8",
    )

    sync_derived()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
