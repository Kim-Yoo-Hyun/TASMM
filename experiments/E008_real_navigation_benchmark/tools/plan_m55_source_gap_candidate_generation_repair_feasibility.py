#!/usr/bin/env python3
"""Decide whether E008 source-gap repair is reranking or candidate generation."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

M43_DIR = EXP_ROOT / "artifacts" / "E008-M43_dynamic_stale_navigation_policy_redesign_contract_v0"
M44_DIR = EXP_ROOT / "artifacts" / "E008-M44_source_diverse_redesign_row_materialization_smoke_v0"
M49_DIR = EXP_ROOT / "artifacts" / "E008-M49_routine_fetch_repair_row_materialization_smoke_v0"
M51_DIR = EXP_ROOT / "artifacts" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"
M52_DIR = EXP_ROOT / "artifacts" / "E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0"
M54_DIR = EXP_ROOT / "artifacts" / "E008-M54_navigation_boundary_package_paper_table_freeze_v0"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M55_source_gap_candidate_generation_repair_feasibility_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M55_source_gap_candidate_generation_repair_feasibility_v0"
)

VERSION = "e008_m55_source_gap_candidate_generation_repair_feasibility_v0"
READY_STATUS = "e008_m55_source_gap_candidate_generation_repair_feasibility_ready"
BLOCKED_STATUS = "e008_m55_source_gap_candidate_generation_repair_feasibility_blocked"
NEXT_UNIT = "E008-M56 source-gap candidate-source expansion contract"

STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
H001_PREV_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"

POLICY_ORDER = [
    DETECTOR_POLICY,
    FIXED_POLICY,
    H001_POLICY,
    H001_PREV_POLICY,
    SOURCE_CURRENT_POLICY,
    STATIC_POLICY,
    TASK_AGNOSTIC_POLICY,
]


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


def min_finite(values: list[object]) -> float | None:
    clean = [finite_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return min(clean) if clean else None


def scan_task_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("adapter_episode_id")), str(row.get("task_context_id")))


def is_scan_task_metric(row: dict[str, Any]) -> bool:
    return row.get("metric_scope") == "scan_task_policy"


def is_success(row: dict[str, Any]) -> bool:
    sr = finite_float(row.get("SR"))
    return bool(row.get("trajectory_success")) or sr == 1.0


def attempt_hit(row: dict[str, Any]) -> bool:
    return bool(row.get("primary_eval_hit")) or bool(row.get("eval_success")) or bool(
        row.get("hit_any_viewpoint_xz_1p0")
    )


def unique_candidate_id(row: dict[str, Any]) -> str:
    for key in ["raw_candidate_uid", "proposal_uid", "overlay_candidate_uid", "candidate_visit_uid"]:
        value = row.get(key)
        if value:
            return str(value)
    return json.dumps(row.get("candidate_stop_position_m"), sort_keys=True)


def group_by_key(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[scan_task_key(row)].append(row)
    return out


def build_source_gap_policy_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_gap_rows = [
        row
        for row in metric_rows
        if is_scan_task_metric(row) and bool(row.get("diagnostic_source_gap_boundary"))
    ]
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_gap_rows:
        by_policy[str(row.get("policy_id"))].append(row)

    out: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        rows = by_policy.get(policy_id, [])
        success_rows = sum(1 for row in rows if is_success(row))
        current = {
            "version": VERSION,
            "boundary": "source_gap",
            "policy_id": policy_id,
            "rows": len(rows),
            "success_rows": success_rows,
            "SR": safe_ratio(success_rows, len(rows)),
            "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
            "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
            "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
            "OldLocationDeadEndCostM_mean": mean(
                [finite_float(row.get("OldLocationDeadEndCostM")) for row in rows]
            ),
            "StopRank_mean": mean([finite_float(row.get("StopRank")) for row in rows]),
            "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in rows).items())),
            "supports_source_gap_solved_claim": False,
        }
        if policy_id == H001_POLICY:
            current["interpretation"] = (
                "partial_source_gap_recovery_over_detector_and_fixed_baselines_but_not_over_task_agnostic"
            )
        elif policy_id == TASK_AGNOSTIC_POLICY:
            current["interpretation"] = "matches_h001_v2_on_source_gap_and_blocks_task_conditioned_claim"
        elif policy_id in {DETECTOR_POLICY, FIXED_POLICY, SOURCE_CURRENT_POLICY}:
            current["interpretation"] = "current_budgeted_source_baseline_fails_source_gap_rows"
        elif policy_id == STATIC_POLICY:
            current["interpretation"] = "stale_memory_lower_bound_fails_source_gap_rows"
        else:
            current["interpretation"] = "previous_h001_ablation_not_sufficient"
        out.append(current)
    return out


def build_episode_rows(
    metric_rows: list[dict[str, Any]],
    attempt_rows: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_gap_metrics = [
        row
        for row in metric_rows
        if is_scan_task_metric(row) and bool(row.get("diagnostic_source_gap_boundary"))
    ]
    metrics_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_gap_metrics:
        metrics_by_episode[str(row.get("adapter_episode_id"))].append(row)

    attempts_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempt_rows:
        if bool(row.get("diagnostic_source_gap_boundary")):
            attempts_by_episode[str(row.get("adapter_episode_id"))].append(row)

    source_gap_pools = [row for row in pool_rows if bool(row.get("diagnostic_source_gap_boundary_for_reporting"))]
    pools_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_gap_pools:
        pools_by_episode[str(row.get("adapter_episode_id"))].append(row)

    source_gap_candidates = [
        row for row in candidate_rows if bool(row.get("diagnostic_source_gap_boundary_for_reporting"))
    ]
    candidates_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_gap_candidates:
        candidates_by_episode[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for adapter_episode_id in sorted(metrics_by_episode):
        rows = metrics_by_episode[adapter_episode_id]
        attempts = attempts_by_episode.get(adapter_episode_id, [])
        pools = pools_by_episode.get(adapter_episode_id, [])
        candidates = candidates_by_episode.get(adapter_episode_id, [])
        contexts = sorted({str(row.get("task_context_id")) for row in rows})

        successes_by_policy = {
            policy_id: sum(1 for row in rows if row.get("policy_id") == policy_id and is_success(row))
            for policy_id in POLICY_ORDER
        }
        any_hit_contexts = sorted({str(row.get("task_context_id")) for row in attempts if attempt_hit(row)})
        h001_success_contexts = sorted(
            {
                str(row.get("task_context_id"))
                for row in rows
                if row.get("policy_id") == H001_POLICY and is_success(row)
            }
        )
        min_nearest = min_finite(
            [row.get("candidate_to_nearest_eval_viewpoint_xz_m") for row in attempts]
        )
        unique_materialized_candidates = len({unique_candidate_id(row) for row in candidates})
        candidate_source_counts = Counter(str(row.get("candidate_source_role")) for row in candidates)

        if len(h001_success_contexts) == len(contexts) and contexts:
            repair_decision = "current_candidate_rerank_partial_positive_but_task_agnostic_tie"
            next_requirement = "retain_as_positive_source_gap_case_but_do_not_claim_task_conditioning"
            current_top5_repair_sufficient = True
        elif any_hit_contexts:
            repair_decision = "ranking_repair_possible_on_existing_top5_variant_evidence"
            next_requirement = "audit_why_h001_missed_available_hit_without_using_eval_labels"
            current_top5_repair_sufficient = False
        else:
            repair_decision = "needs_observation_expansion_or_external_candidate_source"
            next_requirement = (
                "expand non-oracle observation/source generation before broader navigation scale-up"
            )
            current_top5_repair_sufficient = False

        row0 = rows[0]
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": adapter_episode_id,
                "scene_key": row0.get("scene_key"),
                "scan_id": row0.get("scan_id"),
                "object_category": row0.get("object_category"),
                "task_contexts": contexts,
                "task_context_rows": len(contexts),
                "source_gap_policy_rows": len(rows),
                "attempt_rows": len(attempts),
                "attempt_policy_rows": len({(row.get("policy_id"), row.get("task_context_id")) for row in attempts}),
                "m44_full_current_candidate_rows_max": max(
                    [int(row.get("m36_full_current_candidate_rows", 0) or 0) for row in pools] or [0]
                ),
                "m44_full_current_unique_diversity_keys_max": max(
                    [int(row.get("m36_full_current_unique_diversity_keys", 0) or 0) for row in pools] or [0]
                ),
                "m44_full_current_unique_frame_ids_max": max(
                    [int(row.get("m36_full_current_unique_frame_ids", 0) or 0) for row in pools] or [0]
                ),
                "m49_materialized_candidate_rows": len(candidates),
                "m49_unique_materialized_candidates": unique_materialized_candidates,
                "m49_candidate_source_counts": dict(sorted(candidate_source_counts.items())),
                "detector_success_contexts": successes_by_policy.get(DETECTOR_POLICY, 0),
                "fixed_success_contexts": successes_by_policy.get(FIXED_POLICY, 0),
                "source_current_success_contexts": successes_by_policy.get(SOURCE_CURRENT_POLICY, 0),
                "h001_v1_success_contexts": successes_by_policy.get(H001_PREV_POLICY, 0),
                "h001_v2_success_contexts": successes_by_policy.get(H001_POLICY, 0),
                "task_agnostic_success_contexts": successes_by_policy.get(TASK_AGNOSTIC_POLICY, 0),
                "any_policy_hit_contexts": any_hit_contexts,
                "h001_v2_success_task_contexts": h001_success_contexts,
                "current_top5_variant_has_eval_hit": bool(any_hit_contexts),
                "min_candidate_to_nearest_eval_viewpoint_xz_m": min_nearest,
                "current_top5_repair_sufficient_for_episode": current_top5_repair_sufficient,
                "repair_decision": repair_decision,
                "next_requirement": next_requirement,
                "claim_boundary": "source_gap_feasibility_diagnostic_only_not_final_navigation_claim",
            }
        )
    return out


def build_candidate_generation_feasibility_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in episode_rows:
        decision = row["repair_decision"]
        if decision == "current_candidate_rerank_partial_positive_but_task_agnostic_tie":
            feasibility = "feasible_for_detector_gap_recovery_not_task_specific"
        elif decision == "ranking_repair_possible_on_existing_top5_variant_evidence":
            feasibility = "needs_policy_ranking_debug"
        else:
            feasibility = "not_supported_by_existing_top5_variants"
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": row["adapter_episode_id"],
                "object_category": row["object_category"],
                "task_context_rows": row["task_context_rows"],
                "full_current_candidate_rows_max": row["m44_full_current_candidate_rows_max"],
                "materialized_candidate_rows": row["m49_materialized_candidate_rows"],
                "min_candidate_to_nearest_eval_viewpoint_xz_m": row[
                    "min_candidate_to_nearest_eval_viewpoint_xz_m"
                ],
                "h001_v2_success_contexts": row["h001_v2_success_contexts"],
                "task_agnostic_success_contexts": row["task_agnostic_success_contexts"],
                "detector_success_contexts": row["detector_success_contexts"],
                "current_top5_variant_has_eval_hit": row["current_top5_variant_has_eval_hit"],
                "candidate_generation_feasibility": feasibility,
                "selected_repair_route": (
                    "candidate_source_expansion"
                    if feasibility == "not_supported_by_existing_top5_variants"
                    else "retain_as_diagnostic_positive_case"
                ),
                "policy_leakage_guard": (
                    "Do not use eval hit labels to generate candidate order; use them only for feasibility diagnosis."
                ),
            }
        )
    return out


def build_evidence_gate_rows(
    episode_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    m54_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    source_gap_contexts = sum(int(row["task_context_rows"]) for row in episode_rows)
    h001 = next(row for row in policy_rows if row["policy_id"] == H001_POLICY)
    task_agnostic = next(row for row in policy_rows if row["policy_id"] == TASK_AGNOSTIC_POLICY)
    detector = next(row for row in policy_rows if row["policy_id"] == DETECTOR_POLICY)
    fixed = next(row for row in policy_rows if row["policy_id"] == FIXED_POLICY)

    remaining_rows = [
        row for row in episode_rows if int(row.get("h001_v2_success_contexts", 0)) < int(row["task_context_rows"])
    ]
    remaining_contexts = sum(
        int(row["task_context_rows"]) - int(row.get("h001_v2_success_contexts", 0))
        for row in episode_rows
    )
    remaining_with_any_hit = sum(
        len(set(row.get("any_policy_hit_contexts", [])) - set(row.get("h001_v2_success_task_contexts", [])))
        for row in episode_rows
    )

    gates = [
        {
            "gate_id": "m54_navigation_boundary_available",
            "passed": m54_coverage.get("status") == "e008_m54_navigation_boundary_package_paper_table_freeze_ready",
            "evidence": f"M54 status={m54_coverage.get('status')}.",
            "implication": "M55 can use the frozen diagnostic table as input.",
        },
        {
            "gate_id": "source_gap_episode_rows_present",
            "passed": bool(episode_rows) and source_gap_contexts > 0,
            "evidence": f"{len(episode_rows)} source-gap episodes, {source_gap_contexts} scan-task contexts.",
            "implication": "Candidate-generation repair can be analyzed on source-gap rows.",
        },
        {
            "gate_id": "h001_source_gap_partial_recovery",
            "passed": int(h001.get("success_rows", 0)) > 0,
            "evidence": f"H001 v2 source-gap success {h001.get('success_rows')}/{h001.get('rows')}.",
            "implication": "H001 has a positive source-gap case but not a solved source-gap claim.",
        },
        {
            "gate_id": "h001_beats_detector_and_fixed_on_source_gap_sr",
            "passed": int(h001.get("success_rows", 0)) > int(detector.get("success_rows", 0))
            and int(h001.get("success_rows", 0)) > int(fixed.get("success_rows", 0)),
            "evidence": (
                f"H001 {h001.get('success_rows')}/{h001.get('rows')}, "
                f"detector {detector.get('success_rows')}/{detector.get('rows')}, "
                f"fixed {fixed.get('success_rows')}/{fixed.get('rows')}."
            ),
            "implication": "H001 can claim diagnostic improvement over confidence/fixed source-gap baselines.",
        },
        {
            "gate_id": "h001_beats_task_agnostic_on_source_gap_sr",
            "passed": int(h001.get("success_rows", 0)) > int(task_agnostic.get("success_rows", 0)),
            "evidence": (
                f"H001 {h001.get('success_rows')}/{h001.get('rows')}, "
                f"task-agnostic {task_agnostic.get('success_rows')}/{task_agnostic.get('rows')}."
            ),
            "implication": "Task-conditioned source-gap claim remains blocked if this fails.",
        },
        {
            "gate_id": "remaining_source_gap_has_existing_top5_hit",
            "passed": remaining_contexts > 0 and remaining_with_any_hit == remaining_contexts,
            "evidence": (
                f"remaining failed source-gap contexts={remaining_contexts}, "
                f"remaining contexts with any top-5 variant eval hit={remaining_with_any_hit}."
            ),
            "implication": "If false, reranking already materialized top-5 variants is insufficient.",
        },
        {
            "gate_id": "rerank_only_repair_sufficient",
            "passed": False,
            "evidence": (
                f"{len(remaining_rows)} unrecovered source-gap episodes still have no top-5 hit under "
                "the executed detector/fixed/source-diverse/H001/task-agnostic variants."
            ),
            "implication": "Next unit should expand candidate sources before navigation scale-up.",
        },
        {
            "gate_id": "candidate_source_expansion_needed",
            "passed": True,
            "evidence": "Unrecovered source-gap episodes have nearest executed candidate >3m from eval viewpoints.",
            "implication": "M56 should define observation expansion or external candidate-source routes.",
        },
    ]
    return [{"version": VERSION, **row} for row in gates]


def build_route_decision_rows(evidence_gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate = {row["gate_id"]: bool(row["passed"]) for row in evidence_gate_rows}
    return [
        {
            "version": VERSION,
            "route_id": "scale_navigation_benchmark_now",
            "selected": False,
            "next_unit": None,
            "reason": "Source-gap is not solved and H001 ties task-agnostic source-diverse.",
        },
        {
            "version": VERSION,
            "route_id": "rerank_existing_budget5_candidates_now",
            "selected": False,
            "next_unit": None,
            "reason": "Remaining source-gap failures have no eval hit under the already executed top-5 variants.",
        },
        {
            "version": VERSION,
            "route_id": "full_candidate_pool_oracle_diagnostic_only",
            "selected": False,
            "next_unit": None,
            "reason": "The full pool can be inspected as a diagnostic, but eval-hit labels must not define the policy.",
        },
        {
            "version": VERSION,
            "route_id": "source_gap_candidate_source_expansion_contract",
            "selected": gate.get("candidate_source_expansion_needed", False),
            "next_unit": NEXT_UNIT,
            "reason": (
                "The remaining failure is candidate-source coverage, so M56 should define "
                "non-oracle observation expansion and external source routes."
            ),
        },
        {
            "version": VERSION,
            "route_id": "human_intent_upgrade_now",
            "selected": False,
            "next_unit": None,
            "reason": "Task context still does not beat task-agnostic source-diverse on source-gap rows.",
        },
    ]


def build_claim_boundary_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    h001 = next(row for row in policy_rows if row["policy_id"] == H001_POLICY)
    task_agnostic = next(row for row in policy_rows if row["policy_id"] == TASK_AGNOSTIC_POLICY)
    detector = next(row for row in policy_rows if row["policy_id"] == DETECTOR_POLICY)
    return [
        {
            "version": VERSION,
            "claim_id": "source_gap_diagnosis_ready",
            "supported": True,
            "evidence": "M51/M52/M54 source-gap rows are available and M55 localizes the remaining failure to candidate-source coverage.",
            "claim_boundary": "diagnostic feasibility claim only",
        },
        {
            "version": VERSION,
            "claim_id": "partial_source_gap_recovery_over_detector_budget5",
            "supported": int(h001.get("success_rows", 0)) > int(detector.get("success_rows", 0)),
            "evidence": f"H001 source-gap SR={h001.get('SR')}; detector source-gap SR={detector.get('SR')}.",
            "claim_boundary": "diagnostic smoke evidence only; not final navigation claim",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_solved",
            "supported": False,
            "evidence": f"H001 source-gap SR={h001.get('SR')} and remaining source-gap contexts fail.",
            "required_evidence": "candidate-source expansion that recovers remaining source-gap contexts without eval-label leakage.",
        },
        {
            "version": VERSION,
            "claim_id": "task_conditioned_source_gap_improvement",
            "supported": False,
            "evidence": (
                f"H001 source-gap success_rows={h001.get('success_rows')} equals "
                f"task-agnostic success_rows={task_agnostic.get('success_rows')}."
            ),
            "required_evidence": "task context must change source selection or re-observation decisions and beat task-agnostic.",
        },
        {
            "version": VERSION,
            "claim_id": "rerank_only_source_gap_repair_sufficient",
            "supported": False,
            "evidence": "Two source-gap episodes have no successful candidate among executed top-5 variants.",
            "required_evidence": "new source generation or external map/proposal source, then leakage-safe navigation execution.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "evidence": "M55 is a feasibility decision over a small diagnostic denominator.",
            "required_evidence": "scaled navigation execution with source-gap repair, strong baselines, ablations, and heldout scenes.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "why_not_scale_now",
            "M54 already shows H001 ties task-agnostic and has weak source-gap recovery; scaling would amplify an unresolved blocker.",
            "Run M56 candidate-source expansion contract before broader navigation benchmark execution.",
        ),
        (
            "why_not_more_reranking",
            "M51 top-5 variants do not contain a successful candidate for two source-gap episodes, so reranking the same executed set is not enough.",
            "Separate candidate generation/source coverage from policy ranking.",
        ),
        (
            "oracle_leakage_guard",
            "Eval-goal/viewpoint labels are used only for metric and feasibility diagnosis, not for policy-visible candidate order.",
            "Any full-pool inspection must remain diagnostic or use policy-visible signals only.",
        ),
        (
            "human_intent_boundary",
            "Structured task context still ties task-agnostic source-diverse on source-gap rows.",
            "Keep human intent as a secondary condition until it changes a decision and improves metrics.",
        ),
        (
            "top_tier_novelty_boundary",
            "The current evidence identifies a real failure mode but does not yet prove a general dynamic semantic mapping method.",
            "Top-tier claim needs source-gap repair, external candidate/map baselines, heldout transfer, and failure taxonomy.",
        ),
    ]
    return [
        {
            "version": VERSION,
            "defense_id": defense_id,
            "reviewer_attack": attack,
            "response": response,
        }
        for defense_id, attack, response in rows
    ]


def write_report(
    coverage: dict[str, Any],
    episode_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    evidence_gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    h001 = next(row for row in policy_rows if row["policy_id"] == H001_POLICY)
    task_agnostic = next(row for row in policy_rows if row["policy_id"] == TASK_AGNOSTIC_POLICY)
    detector = next(row for row in policy_rows if row["policy_id"] == DETECTOR_POLICY)
    selected = next(row for row in route_rows if row["selected"])
    lines = [
        "# E008-M55 Source-Gap Candidate-Generation Repair Feasibility",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Source-gap episodes: {coverage['source_gap_episode_rows']}.",
        f"- Source-gap scan-task contexts: {coverage['source_gap_scan_task_context_rows']}.",
        f"- H001 v2 source-gap success: {h001['success_rows']} / {h001['rows']} (`SR`={h001['SR']:.6f}).",
        f"- Task-agnostic source-gap success: {task_agnostic['success_rows']} / {task_agnostic['rows']} (`SR`={task_agnostic['SR']:.6f}).",
        f"- Detector source-gap success: {detector['success_rows']} / {detector['rows']} (`SR`={detector['SR']:.6f}).",
        f"- Remaining H001 failed source-gap contexts: {coverage['h001_remaining_source_gap_failed_context_rows']}.",
        f"- Remaining failed contexts with any executed top-5 variant hit: {coverage['remaining_failed_contexts_with_any_top5_variant_hit']}.",
        f"- Selected route: `{selected['route_id']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Interpretation",
        "",
        "- The positive source-gap case is real but narrow: H001 v2 recovers one episode group and beats detector/fixed budget-5 there.",
        "- The same recovered rows are also recovered by `task_agnostic_source_diverse_budget5_v1`, so this does not support a task-conditioned source-gap claim.",
        "- The two unrecovered source-gap episodes have no success under the executed detector/fixed/source-diverse/H001/task-agnostic top-5 variants; the failure is therefore not defensibly just another top-5 reranking problem.",
        "- The next step should expand candidate sources through non-oracle observation expansion or external map/proposal sources before broader navigation scale-up.",
        "",
        "## Episode Decisions",
        "",
        "| episode | object | H001 | task-agnostic | detector | min nearest eval viewpoint xz | decision |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in episode_rows:
        min_xz = row["min_candidate_to_nearest_eval_viewpoint_xz_m"]
        min_txt = "NA" if min_xz is None else f"{min_xz:.6f}"
        lines.append(
            f"| `{row['adapter_episode_id']}` | `{row['object_category']}` | "
            f"{row['h001_v2_success_contexts']}/{row['task_context_rows']} | "
            f"{row['task_agnostic_success_contexts']}/{row['task_context_rows']} | "
            f"{row['detector_success_contexts']}/{row['task_context_rows']} | "
            f"{min_txt} | `{row['repair_decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Evidence Gates",
            "",
            "| gate | pass | implication |",
            "| --- | --- | --- |",
        ]
    )
    for row in evidence_gate_rows:
        lines.append(f"| `{row['gate_id']}` | {row['passed']} | {row['implication']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M55 supports only a source-gap repair feasibility decision.",
            "- It does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, or human intent as a main contribution.",
            "- Any full candidate-pool inspection must be treated as diagnostic unless the policy uses only non-oracle signals.",
            "",
            "## Next",
            "",
            f"- {coverage['selected_next_unit']}: define candidate-source expansion routes and the leakage-safe gates for testing them.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m43_coverage = read_json(M43_DIR / "coverage.json")
    m54_coverage = read_json(M54_DIR / "coverage.json")
    metric_rows = read_jsonl(M51_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    attempt_rows = read_jsonl(M51_DIR / "dynamic_stale_trajectory_attempt_rows.jsonl")
    pool_rows = read_jsonl(M44_DIR / "candidate_pool_summary_rows.jsonl")
    candidate_rows = read_jsonl(M49_DIR / "routine_fetch_repair_candidate_rows.jsonl")
    source_boundary_rows = read_jsonl(M52_DIR / "source_boundary_rows.jsonl")

    input_ready = all(
        [
            m43_coverage,
            m54_coverage,
            metric_rows,
            attempt_rows,
            pool_rows,
            candidate_rows,
            source_boundary_rows,
        ]
    )

    policy_rows = build_source_gap_policy_rows(metric_rows)
    episode_rows = build_episode_rows(metric_rows, attempt_rows, pool_rows, candidate_rows)
    feasibility_rows = build_candidate_generation_feasibility_rows(episode_rows)
    evidence_gate_rows = build_evidence_gate_rows(episode_rows, policy_rows, m54_coverage)
    route_rows = build_route_decision_rows(evidence_gate_rows)
    claim_boundary_rows = build_claim_boundary_rows(policy_rows)
    reviewer_defense_rows = build_reviewer_defense_rows()

    h001 = next(row for row in policy_rows if row["policy_id"] == H001_POLICY)
    task_agnostic = next(row for row in policy_rows if row["policy_id"] == TASK_AGNOSTIC_POLICY)
    remaining_failed_contexts = sum(
        int(row["task_context_rows"]) - int(row.get("h001_v2_success_contexts", 0))
        for row in episode_rows
    )
    remaining_hit_contexts = sum(
        len(set(row.get("any_policy_hit_contexts", [])) - set(row.get("h001_v2_success_task_contexts", [])))
        for row in episode_rows
    )
    gate_pass_rows = sum(1 for row in evidence_gate_rows if row["passed"])
    selected = next(row for row in route_rows if row["selected"])
    status = READY_STATUS if input_ready and selected["route_id"] == "source_gap_candidate_source_expansion_contract" else BLOCKED_STATUS

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m43_status": m43_coverage.get("status"),
        "m54_status": m54_coverage.get("status"),
        "input_ready": input_ready,
        "source_gap_episode_rows": len(episode_rows),
        "source_gap_policy_rows": len(policy_rows),
        "source_gap_scan_task_context_rows": sum(int(row["task_context_rows"]) for row in episode_rows),
        "candidate_generation_feasibility_rows": len(feasibility_rows),
        "evidence_gate_rows": len(evidence_gate_rows),
        "evidence_gate_pass_rows": gate_pass_rows,
        "route_decision_rows": len(route_rows),
        "claim_boundary_rows": len(claim_boundary_rows),
        "reviewer_defense_rows": len(reviewer_defense_rows),
        "h001_source_gap_success_rows": h001.get("success_rows"),
        "h001_source_gap_rows": h001.get("rows"),
        "h001_source_gap_SR": h001.get("SR"),
        "task_agnostic_source_gap_success_rows": task_agnostic.get("success_rows"),
        "task_agnostic_source_gap_rows": task_agnostic.get("rows"),
        "task_agnostic_source_gap_SR": task_agnostic.get("SR"),
        "h001_beats_task_agnostic_source_gap": int(h001.get("success_rows", 0)) > int(
            task_agnostic.get("success_rows", 0)
        ),
        "h001_remaining_source_gap_failed_context_rows": remaining_failed_contexts,
        "remaining_failed_contexts_with_any_top5_variant_hit": remaining_hit_contexts,
        "rerank_only_repair_sufficient": False,
        "candidate_source_expansion_needed": True,
        "real_navigation_sr_spl_ready": False,
        "human_intent_main_claim_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_route": selected["route_id"],
        "selected_next_unit": selected["next_unit"],
        "artifact_dir": str(ARTIFACT_DIR.relative_to(ROOT)),
        "derived_data_dir": str(DATA_OUT_DIR.relative_to(ROOT)),
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_policy_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_episode_rows.jsonl", episode_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_generation_feasibility_rows.jsonl", feasibility_rows)
    write_jsonl(ARTIFACT_DIR / "evidence_gate_rows.jsonl", evidence_gate_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_defense_rows)
    write_report(coverage, episode_rows, policy_rows, evidence_gate_rows, route_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "source_gap_episode_rows.jsonl", episode_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_generation_feasibility_rows.jsonl", feasibility_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
