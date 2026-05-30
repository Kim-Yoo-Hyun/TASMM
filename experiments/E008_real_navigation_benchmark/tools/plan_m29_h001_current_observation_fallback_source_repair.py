#!/usr/bin/env python3
"""Plan a leakage-safe H001 current-observation fallback/source repair contract."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M29_h001_current_observation_fallback_source_repair_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M29_h001_current_observation_fallback_source_repair_contract_v0"
)
M26_DIR = EXP_ROOT / "artifacts" / "E008-M26_h001_visit_order_path_smoke_v0"
M27_DIR = EXP_ROOT / "artifacts" / "E008-M27_h001_goal_evaluation_smoke_v0"
M28_DIR = EXP_ROOT / "artifacts" / "E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0"
VERSION = "e008_m29_h001_current_observation_fallback_source_repair_contract_v0"

H001_POLICY = "h001_real_task_context_memory_trust_v0"
DETECTOR_POLICY = "real_detector_confidence_expanded_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
MIN_EPISODES_FOR_NAVIGATION_CLAIM = 20


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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("adapter_episode_id")),
        str(row.get("task_context_id")),
        str(row.get("policy_id")),
    )


def episode_task_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("adapter_episode_id")), str(row.get("task_context_id"))


def visit_rank(row: dict[str, Any]) -> int:
    rank = row.get("visit_rank", row.get("visit_order_index"))
    try:
        return int(rank)
    except Exception:
        return 10**9


def row_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("proposal_uid") or ""),
        str(row.get("raw_candidate_uid") or ""),
        str(row.get("frame_id") or ""),
    )


def group_candidate_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    for rows_for_key in grouped.values():
        rows_for_key.sort(key=visit_rank)
    return grouped


def first_hit(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in sorted(rows, key=visit_rank):
        if row.get("primary_eval_hit") or row.get("hit_any_viewpoint_xz_1p0"):
            return row
    return None


def min_distance(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [finite_float(row.get(field)) for row in rows]
    values = [value for value in values if value is not None]
    return min(values) if values else None


def build_allowed_input_rows() -> list[dict[str, Any]]:
    fields = [
        ("adapter_episode_id", "episode identity"),
        ("scan_id", "bridge scan identity"),
        ("scene_key", "scene identity"),
        ("object_category", "query object category"),
        ("task_context_id", "structured task context"),
        ("policy_id", "policy identity"),
        ("policy_plan_uid", "policy plan identity"),
        ("source_role", "initial memory proxy or current observation"),
        ("candidate_order_component", "source-side ordering component"),
        ("candidate_visit_order_contract", "source-side visit-order contract"),
        ("visit_order_index", "policy visit rank before metric join"),
        ("candidate_rank", "source candidate rank"),
        ("candidate_confidence", "detector/proposal confidence"),
        ("selection_score", "policy-side score"),
        ("proposal_reliability_score", "proposal reliability score"),
        ("staleness_proxy_score", "memory staleness proxy"),
        ("path_ready", "navmesh path availability flag"),
        ("navmesh_validation_status", "navmesh validation status"),
        ("candidate_position_m", "candidate coordinate"),
        ("candidate_stop_position_m", "candidate stop coordinate"),
        ("candidate_source_position_m", "observation/source coordinate"),
        ("source_to_candidate_path_cost_m", "known source-to-candidate path cost"),
        ("cumulative_known_path_cost_m", "known cumulative visit-order cost"),
        ("snap_distance_m", "candidate-to-navmesh snap diagnostic"),
        ("proposal_uid", "proposal identity"),
        ("raw_candidate_uid", "raw detector proposal identity"),
        ("frame_id", "observation frame identity"),
        ("label_canonical", "canonical source label"),
    ]
    return [
        {
            "version": VERSION,
            "field_name": field_name,
            "allowed_for_policy": True,
            "reason": reason,
            "contract_scope": "h001_current_observation_fallback_replay",
        }
        for field_name, reason in fields
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    fields = [
        ("eval_goal_position", "ObjectNav target position"),
        ("eval_goal_object_id", "ObjectNav target object id"),
        ("eval_first_viewpoint_position", "ObjectNav eval viewpoint"),
        ("eval_all_viewpoint_positions", "ObjectNav eval viewpoints"),
        ("eval_viewpoint_count", "ObjectNav eval viewpoint count"),
        ("candidate_to_eval_goal_xz_m", "post-hoc target distance"),
        ("candidate_to_eval_goal_3d_m", "post-hoc target distance"),
        ("candidate_to_eval_first_viewpoint_xz_m", "post-hoc viewpoint distance"),
        ("candidate_to_eval_first_viewpoint_3d_m", "post-hoc viewpoint distance"),
        ("candidate_to_nearest_eval_viewpoint_xz_m", "post-hoc viewpoint distance"),
        ("candidate_to_nearest_eval_viewpoint_3d_m", "post-hoc viewpoint distance"),
        ("hit_goal_xz_1p0", "post-hoc hit label"),
        ("hit_any_viewpoint_xz_1p0", "post-hoc hit label"),
        ("primary_eval_hit", "post-hoc hit label"),
        ("primary_first_hit_rank", "post-hoc success rank"),
        ("primary_spl_proxy", "post-hoc metric"),
        ("best_any_viewpoint_xz_m", "post-hoc best distance"),
        ("failure_type", "post-hoc failure taxonomy"),
        ("h001_vs_detector_outcome", "post-hoc baseline comparison"),
        ("detector_best_any_viewpoint_xz_m", "post-hoc baseline metric"),
        ("ObjectNav_SR", "executed navigation metric"),
        ("ObjectNav_SPL", "executed navigation metric"),
    ]
    return [
        {
            "version": VERSION,
            "field_name": field_name,
            "allowed_for_policy": False,
            "reason": reason,
            "contract_scope": "h001_current_observation_fallback_replay",
        }
        for field_name, reason in fields
    ]


def build_repair_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "repair_policy_id": "h001_current_observation_backstop_top5_v0",
            "policy_family": "h001_repair_candidate_source_ordering",
            "status": "ready_for_replay",
            "trigger_rule": "apply_to_all_h001_policy_plan_rows_without_using_eval_failure_labels",
            "method_form": (
                "preserve H001 visit order first, then append path-ready current-observation "
                "detector-confidence top5 candidates not already selected by H001"
            ),
            "allowed_source_policy": DETECTOR_POLICY,
            "duplicate_key": "proposal_uid/raw_candidate_uid/frame_id",
            "expected_effect": (
                "diagnostically targets detector-only M28 rows while exposing extra visit cost in M30"
            ),
            "not_a_final_claim": True,
        },
        {
            "version": VERSION,
            "repair_policy_id": "h001_source_expansion_required_v0",
            "policy_family": "h001_repair_candidate_source_expansion",
            "status": "not_implemented_in_m29",
            "trigger_rule": "all-policy-miss rows are diagnosed after evaluation only, not used as policy input",
            "method_form": (
                "requires additional non-oracle observation coverage, external map candidates, or true stale-memory "
                "state injection before trajectory execution"
            ),
            "allowed_source_policy": None,
            "duplicate_key": None,
            "expected_effect": "handles rows where H001 and detector-confidence both miss the target region",
            "not_a_final_claim": True,
        },
    ]


def build_backstop_plan_rows(
    visit_rows: list[dict[str, Any]],
    episode_task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = group_candidate_rows(visit_rows)
    rows = []
    for comparison in sorted(episode_task_rows, key=lambda row: (row.get("adapter_episode_id"), row.get("task_context_id"))):
        episode_id, task_context_id = episode_task_key(comparison)
        h001_rows = grouped.get((episode_id, task_context_id, H001_POLICY), [])
        detector_rows = grouped.get((episode_id, task_context_id, DETECTOR_POLICY), [])
        h001_ids = {row_identity(row) for row in h001_rows}
        append_rows = [row for row in detector_rows if row_identity(row) not in h001_ids and row.get("path_ready")]
        append_rows = append_rows[:5]
        rows.append(
            {
                "version": VERSION,
                "repair_plan_uid": f"m29::{episode_id}::{task_context_id}::h001_current_observation_backstop_top5_v0",
                "adapter_episode_id": episode_id,
                "scan_id": comparison.get("scan_id"),
                "scene_key": comparison.get("scene_key"),
                "object_category": comparison.get("object_category"),
                "task_context_id": task_context_id,
                "base_policy_id": H001_POLICY,
                "repair_policy_id": "h001_current_observation_backstop_top5_v0",
                "h001_original_candidate_rows": len(h001_rows),
                "detector_current_observation_rows": len(detector_rows),
                "detector_append_candidate_rows": len(append_rows),
                "estimated_repaired_candidate_rows": len(h001_rows) + len(append_rows),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_failure_label": False,
                "replay_needed": True,
                "claim_boundary": "M29 defines the allowed replay contract only; M30 must recompute ordering and metrics.",
            }
        )
    return rows


def build_repair_opportunity_rows(
    episode_task_rows: list[dict[str, Any]],
    candidate_eval_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped_eval = group_candidate_rows(candidate_eval_rows)
    rows = []
    for comparison in sorted(episode_task_rows, key=lambda row: (row.get("adapter_episode_id"), row.get("task_context_id"))):
        if comparison.get("h001_primary_hit"):
            continue
        episode_id, task_context_id = episode_task_key(comparison)
        h001_eval_rows = grouped_eval.get((episode_id, task_context_id, H001_POLICY), [])
        detector_eval_rows = grouped_eval.get((episode_id, task_context_id, DETECTOR_POLICY), [])
        detector_hit = first_hit(detector_eval_rows)
        h001_ids = {row_identity(row) for row in h001_eval_rows}
        detector_hit_available_for_backstop = bool(detector_hit) and row_identity(detector_hit) not in h001_ids
        failure_type = str(comparison.get("failure_type"))
        if comparison.get("detector_primary_hit"):
            opportunity_type = (
                "detector_only_recoverable_by_backstop"
                if detector_hit_available_for_backstop
                else "detector_only_requires_reordering_or_budget_repair"
            )
            repair_policy_id = "h001_current_observation_backstop_top5_v0"
            replay_recommended = True
        elif failure_type == "all_policy_miss_candidate_source_gap":
            opportunity_type = "not_recoverable_by_backstop_candidate_source_gap"
            repair_policy_id = "h001_source_expansion_required_v0"
            replay_recommended = False
        else:
            opportunity_type = "inspect_unclassified_h001_failure"
            repair_policy_id = "manual_failure_audit_required"
            replay_recommended = False
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": comparison.get("scan_id"),
                "scene_key": comparison.get("scene_key"),
                "object_category": comparison.get("object_category"),
                "task_context_id": task_context_id,
                "m28_failure_type": failure_type,
                "m28_h001_vs_detector_outcome": comparison.get("h001_vs_detector_outcome"),
                "repair_opportunity_type": opportunity_type,
                "repair_policy_id": repair_policy_id,
                "h001_best_any_viewpoint_xz_m_posthoc": comparison.get("h001_best_any_viewpoint_xz_m"),
                "detector_best_any_viewpoint_xz_m_posthoc": comparison.get("detector_best_any_viewpoint_xz_m"),
                "detector_primary_hit_candidate_visit_rank_posthoc": detector_hit.get("visit_rank") if detector_hit else None,
                "detector_primary_hit_candidate_in_h001_by_identity": bool(detector_hit) and row_identity(detector_hit) in h001_ids,
                "detector_primary_hit_candidate_available_for_backstop": detector_hit_available_for_backstop,
                "h001_min_any_viewpoint_xz_m_posthoc": min_distance(
                    h001_eval_rows, "candidate_to_nearest_eval_viewpoint_xz_m"
                ),
                "detector_min_any_viewpoint_xz_m_posthoc": min_distance(
                    detector_eval_rows, "candidate_to_nearest_eval_viewpoint_xz_m"
                ),
                "diagnostic_uses_eval_goal_or_viewpoint": True,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_failure_label": False,
                "replay_recommended": replay_recommended,
            }
        )
    return rows


def build_gate_rows(
    m26_coverage: dict[str, Any],
    m27_coverage: dict[str, Any],
    m28_coverage: dict[str, Any],
    opportunity_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts = Counter(row["repair_opportunity_type"] for row in opportunity_rows)
    episode_count = int(m28_coverage.get("episode_count") or 0)
    return [
        {
            "version": VERSION,
            "gate_id": "source_input_leakage_guard",
            "status": "pass"
            if m26_coverage.get("source_input_leakage_pass") and m27_coverage.get("leakage_audit_pass")
            else "fail",
            "evidence": (
                f"m26_source_input_leakage_pass={m26_coverage.get('source_input_leakage_pass')}; "
                f"m27_leakage_audit_pass={m27_coverage.get('leakage_audit_pass')}"
            ),
            "decision_effect": "required_before_replay",
        },
        {
            "version": VERSION,
            "gate_id": "fixed_policy_not_failure_conditioned",
            "status": "pass" if all(not row["policy_input_uses_failure_label"] for row in plan_rows) else "fail",
            "evidence": "backstop plan is generated for all H001 episode-task rows, not only M28 failures",
            "decision_effect": "prevents post-hoc failure-label leakage",
        },
        {
            "version": VERSION,
            "gate_id": "detector_only_repair_opportunity",
            "status": "pass" if counts.get("detector_only_recoverable_by_backstop", 0) else "warning",
            "evidence": f"detector_only_recoverable_rows={counts.get('detector_only_recoverable_by_backstop', 0)}",
            "decision_effect": "enables_M30_backstop_replay",
        },
        {
            "version": VERSION,
            "gate_id": "remaining_candidate_source_gap",
            "status": "fail" if counts.get("not_recoverable_by_backstop_candidate_source_gap", 0) else "pass",
            "evidence": f"all_policy_source_gap_rows={counts.get('not_recoverable_by_backstop_candidate_source_gap', 0)}",
            "decision_effect": "blocks_positive_navigation_claim_even_if_backstop_recovers_detector_only_rows",
        },
        {
            "version": VERSION,
            "gate_id": "true_dynamic_stale_memory_source",
            "status": "fail" if m27_coverage.get("h001_initial_memory_proxy_not_true_dynamic_stale_memory") else "pass",
            "evidence": (
                "h001_initial_memory_proxy_not_true_dynamic_stale_memory="
                f"{m27_coverage.get('h001_initial_memory_proxy_not_true_dynamic_stale_memory')}"
            ),
            "decision_effect": "blocks_dynamic_stale_memory_claim_on_hm3d",
        },
        {
            "version": VERSION,
            "gate_id": "navigation_scale",
            "status": "pass" if episode_count >= MIN_EPISODES_FOR_NAVIGATION_CLAIM else "fail",
            "evidence": f"episode_count={episode_count}; required>={MIN_EPISODES_FOR_NAVIGATION_CLAIM}",
            "decision_effect": "blocks_paper_navigation_claim_if_fail",
        },
        {
            "version": VERSION,
            "gate_id": "h001_trajectory_execution_ready_now",
            "status": "fail",
            "evidence": "M29 is a repair contract; replay and then trajectory execution are still pending.",
            "decision_effect": "select_M30_replay_before_Docker_trajectory_execution",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "run_leakage_safe_backstop_replay_before_trajectory_execution",
            "selected_next_unit": "E008-M30 H001 current-observation fallback replay smoke",
            "reason": (
                "M28 has 3 detector-only H001 misses that a fixed current-observation backstop can test cheaply; "
                "9 all-policy misses remain source-gap blockers and require later source expansion."
            ),
            "launch_long_job_now": False,
            "fallback_replay_recommended": True,
            "trajectory_execution_recommended_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_repair_contract_is_leakage_safe",
            "supported": True,
            "claim_boundary": (
                "M29 fixes allowed and blocked policy inputs for H001 current-observation fallback replay."
            ),
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_positive_h001_repair_result",
            "supported": False,
            "claim_boundary": "M29 does not replay the repaired policy and therefore reports no repaired SR/SPL or proxy gain.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "H001 repair replay, Docker trajectory execution, scale, and baselines are still pending.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Task context remains a structured memory-trust condition, not a natural-language intent result.",
        },
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    opportunity_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    opportunity_counts = Counter(row["repair_opportunity_type"] for row in opportunity_rows)
    lines = [
        "# E008-M29 H001 Current-Observation Fallback / Source Repair Contract",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Backstop plan rows: {coverage['backstop_plan_rows']}.",
        f"- Repair opportunity rows: {coverage['repair_opportunity_rows']}.",
        f"- Detector-only recoverable rows: {coverage['detector_only_recoverable_rows']}.",
        f"- All-policy source-gap rows: {coverage['all_policy_source_gap_rows']}.",
        f"- Allowed input rows: {coverage['allowed_input_rows']}.",
        f"- Blocked input rows: {coverage['blocked_input_rows']}.",
        f"- Uses `ObjectNav` eval goal/viewpoint for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.",
        "",
        "## Opportunity Taxonomy",
        "",
        "| Opportunity type | Rows |",
        "| --- | ---: |",
    ]
    for opportunity_type, count in opportunity_counts.most_common():
        lines.append(f"| `{opportunity_type}` | {count} |")
    lines.extend(
        [
            "",
            "## Repair Gates",
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
            "- M29 is a contract and diagnostic-opportunity artifact, not a repaired-policy result.",
            "- The proposed backstop is leakage-safe only if M30 uses the allowed-input contract and applies it to all H001 rows.",
            "- Detector-only misses are testable by M30; all-policy misses remain a candidate-source expansion problem.",
            "- Final real navigation `SR` / `SPL` and final real RGB-D/open-vocabulary robustness remain unsupported.",
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

    m26_coverage = read_json(M26_DIR / "coverage.json")
    m27_coverage = read_json(M27_DIR / "coverage.json")
    m28_coverage = read_json(M28_DIR / "coverage.json")
    visit_rows = read_jsonl(M26_DIR / "h001_candidate_visit_order_rows.jsonl")
    candidate_eval_rows = read_jsonl(M27_DIR / "h001_candidate_goal_eval_rows.jsonl")
    episode_task_rows = read_jsonl(M28_DIR / "episode_task_comparison_rows.jsonl")

    allowed_input_rows = build_allowed_input_rows()
    blocked_input_rows = build_blocked_input_rows()
    repair_contract_rows = build_repair_contract_rows()
    backstop_plan_rows = build_backstop_plan_rows(visit_rows, episode_task_rows)
    repair_opportunity_rows = build_repair_opportunity_rows(episode_task_rows, candidate_eval_rows)
    gate_rows = build_gate_rows(m26_coverage, m27_coverage, m28_coverage, repair_opportunity_rows, backstop_plan_rows)
    route_decision_rows = build_route_decision_rows()
    claim_boundary_rows = build_claim_boundary_rows()

    opportunity_counts = Counter(row["repair_opportunity_type"] for row in repair_opportunity_rows)
    gate_counts = Counter(row["status"] for row in gate_rows)
    coverage = {
        "version": VERSION,
        "status": "e008_m29_h001_current_observation_fallback_source_repair_contract_ready_replay_next",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m26_status": m26_coverage.get("status"),
        "m27_status": m27_coverage.get("status"),
        "m28_status": m28_coverage.get("status"),
        "episode_count": m28_coverage.get("episode_count"),
        "episode_task_rows": len(episode_task_rows),
        "repair_contract_rows": len(repair_contract_rows),
        "allowed_input_rows": len(allowed_input_rows),
        "blocked_input_rows": len(blocked_input_rows),
        "backstop_plan_rows": len(backstop_plan_rows),
        "repair_opportunity_rows": len(repair_opportunity_rows),
        "detector_only_recoverable_rows": opportunity_counts.get("detector_only_recoverable_by_backstop", 0),
        "detector_only_requires_reordering_or_budget_repair_rows": opportunity_counts.get(
            "detector_only_requires_reordering_or_budget_repair", 0
        ),
        "all_policy_source_gap_rows": opportunity_counts.get("not_recoverable_by_backstop_candidate_source_gap", 0),
        "gate_rows": len(gate_rows),
        "gate_pass": gate_counts.get("pass", 0),
        "gate_warning": gate_counts.get("warning", 0),
        "gate_fail": gate_counts.get("fail", 0),
        "source_input_leakage_pass": m26_coverage.get("source_input_leakage_pass"),
        "goal_eval_leakage_audit_pass": m27_coverage.get("leakage_audit_pass"),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "policy_input_uses_failure_label": False,
        "fallback_replay_recommended": True,
        "trajectory_execution_recommended_now": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M30 H001 current-observation fallback replay smoke",
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "allowed_input_rows.jsonl", allowed_input_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_input_rows)
    write_jsonl(ARTIFACT_DIR / "repair_contract_rows.jsonl", repair_contract_rows)
    write_jsonl(ARTIFACT_DIR / "backstop_plan_rows.jsonl", backstop_plan_rows)
    write_jsonl(ARTIFACT_DIR / "repair_opportunity_rows.jsonl", repair_opportunity_rows)
    write_jsonl(ARTIFACT_DIR / "repair_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_report(ARTIFACT_DIR / "report.md", coverage, repair_opportunity_rows, gate_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "repair_contract_rows.jsonl", repair_contract_rows)
    write_jsonl(DATA_OUT_DIR / "backstop_plan_rows.jsonl", backstop_plan_rows)
    write_jsonl(DATA_OUT_DIR / "repair_opportunity_rows.jsonl", repair_opportunity_rows)
    write_jsonl(DATA_OUT_DIR / "repair_gate_rows.jsonl", gate_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
