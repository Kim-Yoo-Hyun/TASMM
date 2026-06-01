#!/usr/bin/env python3
"""Interpret M77 repair goal-evaluation results and choose the next route."""

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
M75_DIR = EXP_ROOT / "artifacts" / "E008-M75_source_gap_spl_repair_contract_v0"
M76_DIR = EXP_ROOT / "artifacts" / "E008-M76_source_gap_spl_repair_row_materialization_smoke_v0"
M77_DIR = EXP_ROOT / "artifacts" / "E008-M77_source_gap_spl_repair_goal_evaluation_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M78_source_gap_spl_repair_result_interpretation_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M78_source_gap_spl_repair_result_interpretation_v0"
)

VERSION = "e008_m78_source_gap_spl_repair_result_interpretation_v0"
READY_STATUS = "e008_m78_source_gap_spl_repair_result_interpretation_ready"
BLOCKED_STATUS = "e008_m78_source_gap_spl_repair_result_interpretation_blocked"
NEXT_UNIT = "E008-M79 full-val-mini source-gap candidate-source expansion and loss-safe policy contract"

BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
GUARDED_POLICY = "spl_guarded_confidence_path_tail_budget5_v0"
SOURCE_PROBE_POLICY = "candidate_source_expansion_probe_v0"


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
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def metric_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("eval_budget_scope")), str(row.get("policy_id"))): row
        for row in rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def build_interpretation_rows(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    idx = metric_index(aggregate_rows)
    rows: list[dict[str, Any]] = []
    for scope in ("full_rank", "budget5"):
        base = idx.get((scope, BASELINE_POLICY), {})
        guarded = idx.get((scope, GUARDED_POLICY), {})
        base_sr = finite_float(base.get("primary_proxy_sr"))
        guarded_sr = finite_float(guarded.get("primary_proxy_sr"))
        base_spl = finite_float(base.get("primary_spl_proxy_mean"))
        guarded_spl = finite_float(guarded.get("primary_spl_proxy_mean"))
        delta = next((row for row in delta_rows if row.get("eval_budget_scope") == scope), {})
        if scope == "full_rank":
            interpretation = "guarded_order_is_full_rank_equivalent_but_not_better"
        elif (guarded_sr or 0.0) < (base_sr or 0.0):
            interpretation = "guarded_tail_breaks_budget5_detector_confidence_baseline"
        else:
            interpretation = "requires_manual_review"
        rows.append(
            {
                "version": VERSION,
                "row_type": "result_interpretation",
                "eval_budget_scope": scope,
                "baseline_policy_id": BASELINE_POLICY,
                "method_policy_id": GUARDED_POLICY,
                "baseline_proxy_sr": base_sr,
                "method_proxy_sr": guarded_sr,
                "delta_proxy_sr": guarded_sr - base_sr
                if guarded_sr is not None and base_sr is not None
                else None,
                "baseline_proxy_spl": base_spl,
                "method_proxy_spl": guarded_spl,
                "delta_proxy_spl": guarded_spl - base_spl
                if guarded_spl is not None and base_spl is not None
                else None,
                "guarded_gain_rows": delta.get("guarded_gain_rows"),
                "guarded_loss_rows": delta.get("guarded_loss_rows"),
                "both_hit_rows": delta.get("both_hit_rows"),
                "both_fail_rows": delta.get("both_fail_rows"),
                "source_gap_guarded_gain_rows": delta.get("source_gap_guarded_gain_rows"),
                "source_gap_guarded_loss_rows": delta.get("source_gap_guarded_loss_rows"),
                "interpretation": interpretation,
                "supports_trajectory_contract": False,
                "claim_boundary": "M78 interprets M77 proxy metrics only; no trajectory is executed.",
            }
        )
    rows.append(
        {
            "version": VERSION,
            "row_type": "result_interpretation",
            "eval_budget_scope": "overall",
            "baseline_policy_id": BASELINE_POLICY,
            "method_policy_id": GUARDED_POLICY,
            "interpretation": "reranking_existing_candidates_is_not_sufficient_for_full_val_mini_repair",
            "m77_status": coverage.get("status"),
            "m77_trajectory_contract_ready": coverage.get("trajectory_contract_ready"),
            "supports_positive_repaired_policy_claim": False,
            "supports_deployable_budget5_claim": False,
            "supports_final_navigation_claim": False,
            "claim_boundary": "The next defensible action is source/candidate generation repair, not Docker trajectory launch.",
        }
    )
    return rows


def by_episode_policy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("adapter_episode_id")),
                str(row.get("eval_budget_scope")),
                str(row.get("policy_id")),
            )
        ].append(row)
    return grouped


def build_loss_diagnosis_rows(
    pairwise_rows: list[dict[str, Any]],
    candidate_goal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = by_episode_policy(candidate_goal_rows)
    out: list[dict[str, Any]] = []
    losses = [row for row in pairwise_rows if row.get("comparison") == "guarded_loss"]
    for loss in losses:
        episode = str(loss.get("adapter_episode_id"))
        scope = str(loss.get("eval_budget_scope"))
        base_rows = sorted(
            grouped.get((episode, scope, BASELINE_POLICY), []),
            key=lambda row: int(row.get("visit_rank") or 10**9),
        )
        guarded_rows = sorted(
            grouped.get((episode, scope, GUARDED_POLICY), []),
            key=lambda row: int(row.get("visit_rank") or 10**9),
        )
        base_hit = next((row for row in base_rows if row.get("primary_eval_hit")), {})
        guarded_tail = next(
            (row for row in guarded_rows if row.get("repair_component") == "m76_guarded_path_cost_tail_slot"),
            {},
        )
        out.append(
            {
                "version": VERSION,
                "row_type": "budget5_loss_diagnosis",
                "adapter_episode_id": episode,
                "eval_budget_scope": scope,
                "object_category": loss.get("object_category"),
                "baseline_hit_rank": loss.get("baseline_primary_first_hit_rank"),
                "baseline_hit_proposal_uid": base_hit.get("proposal_uid"),
                "baseline_hit_source_visit_rank": base_hit.get("source_visit_rank"),
                "baseline_hit_source_to_candidate_path_cost_m": base_hit.get("source_to_candidate_path_cost_m"),
                "baseline_hit_candidate_to_nearest_eval_viewpoint_xz_m": base_hit.get(
                    "candidate_to_nearest_eval_viewpoint_xz_m"
                ),
                "guarded_tail_rank": guarded_tail.get("visit_rank"),
                "guarded_tail_proposal_uid": guarded_tail.get("proposal_uid"),
                "guarded_tail_source_policy_id": guarded_tail.get("source_policy_id"),
                "guarded_tail_source_visit_rank": guarded_tail.get("source_visit_rank"),
                "guarded_tail_source_to_candidate_path_cost_m": guarded_tail.get("source_to_candidate_path_cost_m"),
                "guarded_tail_candidate_to_nearest_eval_viewpoint_xz_m": guarded_tail.get(
                    "candidate_to_nearest_eval_viewpoint_xz_m"
                ),
                "failure_mechanism": "path_cost_tail_replaced_detector_confidence_rank5_hit_with_near_source_false_candidate",
                "policy_visible_lesson": "Do not let path-cost tail evict detector-confidence top-5 unless a separate candidate-source reliability gate is proven.",
                "claim_boundary": "Eval hit labels are used only for post-hoc diagnosis, not for policy ranking.",
            }
        )
    return out


def build_source_gap_rows(
    failure_targets: list[dict[str, Any]],
    source_boundary_rows: list[dict[str, Any]],
    scan_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_by_ep = {
        str(row.get("adapter_episode_id")): row
        for row in failure_targets
        if bool(row.get("diagnostic_source_gap_boundary"))
    }
    by_episode_policy_scope = {
        (str(row.get("adapter_episode_id")), str(row.get("eval_budget_scope")), str(row.get("policy_id"))): row
        for row in scan_metric_rows
        if row.get("metric_scope") == "scan_policy"
    }
    out: list[dict[str, Any]] = []
    for episode, target in sorted(target_by_ep.items()):
        base_budget = by_episode_policy_scope.get((episode, "budget5", BASELINE_POLICY), {})
        guarded_budget = by_episode_policy_scope.get((episode, "budget5", GUARDED_POLICY), {})
        base_full = by_episode_policy_scope.get((episode, "full_rank", BASELINE_POLICY), {})
        guarded_full = by_episode_policy_scope.get((episode, "full_rank", GUARDED_POLICY), {})
        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_interpretation",
                "adapter_episode_id": episode,
                "object_category": target.get("object_category"),
                "m75_repair_target": target.get("repair_target"),
                "baseline_budget5_hit": bool(base_budget.get("primary_hit")),
                "guarded_budget5_hit": bool(guarded_budget.get("primary_hit")),
                "baseline_full_rank_hit": bool(base_full.get("primary_hit")),
                "guarded_full_rank_hit": bool(guarded_full.get("primary_hit")),
                "best_budget5_any_viewpoint_xz_m": min(
                    [
                        value
                        for value in [
                            finite_float(base_budget.get("best_any_viewpoint_xz_m")),
                            finite_float(guarded_budget.get("best_any_viewpoint_xz_m")),
                        ]
                        if value is not None
                    ],
                    default=None,
                ),
                "best_full_rank_any_viewpoint_xz_m": min(
                    [
                        value
                        for value in [
                            finite_float(base_full.get("best_any_viewpoint_xz_m")),
                            finite_float(guarded_full.get("best_any_viewpoint_xz_m")),
                        ]
                        if value is not None
                    ],
                    default=None,
                ),
                "source_gap_resolved_by_m76_m77": False,
                "next_validation_requirement": "candidate_source_expansion_or_observation_coverage_before_reranking",
                "claim_boundary": "Source-gap rows are diagnostic; M77 does not create new candidates.",
            }
        )
    return out


def build_route_candidate_rows(
    interpretation_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    budget_interpretation = next(
        row for row in interpretation_rows if row.get("eval_budget_scope") == "budget5"
    )
    route_rows = [
        {
            "version": VERSION,
            "route_id": "promote_guarded_repair_to_trajectory",
            "decision": "reject",
            "reason": "M77 budget-5 proxy success and SPL regress against detector-confidence baseline.",
            "required_before_reconsideration": "no_success_loss_and_no_spl_regression_under_budget5",
        },
        {
            "version": VERSION,
            "route_id": "continue_tail_slot_reranking_only",
            "decision": "reject",
            "reason": "The only guarded loss is caused by evicting detector-confidence rank-5; source-gap rows also remain unresolved.",
            "required_before_reconsideration": "policy_visible_reliability_gate_that_does_not_evict_detector_top5_hits",
        },
        {
            "version": VERSION,
            "route_id": "freeze_detector_confidence_budget5_as_baseline",
            "decision": "keep_as_baseline",
            "reason": "Detector confidence is stronger than the guarded repair under budget-5 in M77.",
            "required_before_reconsideration": "new policy must beat this baseline without using eval labels",
        },
        {
            "version": VERSION,
            "route_id": "candidate_source_expansion_loss_safe_policy_contract",
            "decision": "select",
            "reason": "M75/M77 show source-gap is not fixed by reranking, and M77 shows path-cost tail can evict a detector top-5 hit.",
            "required_before_reconsideration": "materialize policy-visible candidate-source expansion rows while preserving detector-confidence budget safety, then re-evaluate leakage-safe proxy metrics",
        },
        {
            "version": VERSION,
            "route_id": "stop_and_package_diagnostic_boundary",
            "decision": "defer",
            "reason": "Useful for reporting, but top-tier path still needs a stronger candidate-source repair or external baseline comparison.",
            "required_before_reconsideration": "use if candidate-source expansion also fails",
        },
    ]
    for row in route_rows:
        row["budget5_delta_proxy_sr"] = budget_interpretation.get("delta_proxy_sr")
        row["budget5_delta_proxy_spl"] = budget_interpretation.get("delta_proxy_spl")
        row["budget5_loss_rows"] = len(loss_rows)
        row["source_gap_rows"] = len(source_gap_rows)
        row["claim_boundary"] = "Route decision is based on M77 proxy diagnostics, not final navigation SR/SPL."
    return route_rows


def build_gate_rows(
    m77_coverage: dict[str, Any],
    loss_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trajectory_ready = bool(m77_coverage.get("trajectory_contract_ready"))
    return [
        {
            "version": VERSION,
            "gate_id": "m77_ready",
            "gate_status": "pass"
            if m77_coverage.get("status") == "e008_m77_source_gap_spl_repair_goal_evaluation_smoke_ready"
            else "fail",
            "blocks_next_route": False,
            "rationale": "M78 requires M77 proxy evaluation.",
        },
        {
            "version": VERSION,
            "gate_id": "direct_trajectory_promotion",
            "gate_status": "fail" if not trajectory_ready else "pass",
            "blocks_next_route": False,
            "rationale": "Direct trajectory promotion is blocked by M77 budget-5 regression.",
        },
        {
            "version": VERSION,
            "gate_id": "budget5_loss_diagnosed",
            "gate_status": "pass" if loss_rows else "warning",
            "blocks_next_route": False,
            "rationale": "M78 should record whether the guarded budget-5 loss has a concrete case-level mechanism.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_unresolved",
            "gate_status": "pass" if source_gap_rows else "warning",
            "blocks_next_route": False,
            "rationale": "Source-gap unresolved rows justify candidate-source expansion as the next route.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_source_expansion_next",
            "gate_status": "pass",
            "blocks_next_route": False,
            "rationale": "Next unit should create a contract before materializing or running any long job.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_m77_failure_interpretation",
            "supported": True,
            "claim_boundary": "M78 supports the statement that M76/M77 guarded tail-slot repair is not ready for trajectory promotion.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_positive_repaired_policy",
            "supported": False,
            "claim_boundary": "Budget-5 proxy success and SPL regress, so positive repaired-policy claim is blocked.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "Source-gap rows require candidate-source expansion or observation coverage, not just reranking.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_loss_safe_repair_policy",
            "supported": False,
            "claim_boundary": "A future policy must prove it does not evict detector-confidence budget-5 hits before it can be called deployable.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_navigation",
            "supported": False,
            "claim_boundary": "M78 does not execute Habitat trajectories and does not add external navigation/search baselines.",
        },
    ]


def build_next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_action",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "rationale": "A contract is needed before any candidate-source expansion materialization or trajectory rerun.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    interpretation_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    interp_lines = []
    for row in interpretation_rows:
        if row.get("eval_budget_scope") == "overall":
            continue
        interp_lines.append(
            "| {scope} | {base_sr} | {method_sr} | {delta_sr} | {base_spl} | {method_spl} | {delta_spl} | {interpretation} |".format(
                scope=row.get("eval_budget_scope"),
                base_sr=fmt(row.get("baseline_proxy_sr")),
                method_sr=fmt(row.get("method_proxy_sr")),
                delta_sr=fmt(row.get("delta_proxy_sr")),
                base_spl=fmt(row.get("baseline_proxy_spl")),
                method_spl=fmt(row.get("method_proxy_spl")),
                delta_spl=fmt(row.get("delta_proxy_spl")),
                interpretation=row.get("interpretation"),
            )
        )
    route_lines = [
        f"| `{row['route_id']}` | {row['decision']} | {row['reason']} |"
        for row in route_rows
    ]
    loss_line = (
        f"{loss_rows[0]['adapter_episode_id']} rank-{loss_rows[0]['baseline_hit_rank']} detector hit was evicted"
        if loss_rows
        else "none"
    )
    return f"""# E008-M78 Source-Gap/SPL Repair Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M77 status: `{coverage['m77_status']}`.
- Budget-5 loss rows: {coverage['budget5_loss_rows']} ({loss_line}).
- Source-gap unresolved rows: {coverage['source_gap_unresolved_rows']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Result Interpretation

| scope | baseline SR | method SR | delta SR | baseline SPL | method SPL | delta SPL | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(interp_lines)}

## Route Decision

| route_id | decision | reason |
| --- | --- | --- |
{chr(10).join(route_lines)}

## Claim Boundary

- M78 supports a negative repair interpretation: guarded path-cost tail-slot is not ready for trajectory promotion.
- M78 does not support final real navigation `SR` / `SPL`.
- The next defensible route is candidate-source expansion before further reranking or Docker trajectory execution.
"""


def sync_derived() -> None:
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m77_coverage = read_json(M77_DIR / "coverage.json")
    m77_aggregate_rows = read_jsonl(M77_DIR / "aggregate_policy_goal_metric_rows.jsonl")
    m77_delta_rows = read_jsonl(M77_DIR / "policy_delta_summary_rows.jsonl")
    m77_pairwise_rows = read_jsonl(M77_DIR / "policy_pairwise_delta_rows.jsonl")
    m77_candidate_goal_rows = read_jsonl(M77_DIR / "repair_candidate_goal_eval_rows.jsonl")
    m77_scan_rows = read_jsonl(M77_DIR / "scan_policy_goal_metric_rows.jsonl")
    m77_source_boundary_rows = read_jsonl(M77_DIR / "source_boundary_goal_metric_rows.jsonl")
    m75_failure_targets = read_jsonl(M75_DIR / "failure_episode_repair_rows.jsonl")
    m76_budget_rows = read_jsonl(M76_DIR / "budget_accounting_rows.jsonl")

    missing_inputs = []
    for path, rows in [
        (M77_DIR / "coverage.json", [m77_coverage] if m77_coverage else []),
        (M77_DIR / "aggregate_policy_goal_metric_rows.jsonl", m77_aggregate_rows),
        (M77_DIR / "policy_delta_summary_rows.jsonl", m77_delta_rows),
        (M77_DIR / "policy_pairwise_delta_rows.jsonl", m77_pairwise_rows),
        (M77_DIR / "repair_candidate_goal_eval_rows.jsonl", m77_candidate_goal_rows),
        (M75_DIR / "failure_episode_repair_rows.jsonl", m75_failure_targets),
    ]:
        if not rows:
            missing_inputs.append(str(path))

    interpretation_rows = build_interpretation_rows(m77_coverage, m77_aggregate_rows, m77_delta_rows)
    loss_rows = build_loss_diagnosis_rows(m77_pairwise_rows, m77_candidate_goal_rows)
    source_gap_rows = build_source_gap_rows(m75_failure_targets, m77_source_boundary_rows, m77_scan_rows)
    route_candidate_rows = build_route_candidate_rows(interpretation_rows, loss_rows, source_gap_rows)
    gate_rows = build_gate_rows(m77_coverage, loss_rows, source_gap_rows)
    claim_boundary_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    status = READY_STATUS
    if missing_inputs:
        status = BLOCKED_STATUS

    budget_interp = next(row for row in interpretation_rows if row.get("eval_budget_scope") == "budget5")
    full_interp = next(row for row in interpretation_rows if row.get("eval_budget_scope") == "full_rank")
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m77_status": m77_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "result_interpretation_rows": len(interpretation_rows),
        "budget5_loss_rows": len(loss_rows),
        "source_gap_unresolved_rows": len(source_gap_rows),
        "route_candidate_rows": len(route_candidate_rows),
        "gate_rows": len(gate_rows),
        "claim_boundary_rows": len(claim_boundary_rows),
        "m76_budget_accounting_rows": len(m76_budget_rows),
        "full_rank_delta_proxy_sr": full_interp.get("delta_proxy_sr"),
        "full_rank_delta_proxy_spl": full_interp.get("delta_proxy_spl"),
        "budget5_delta_proxy_sr": budget_interp.get("delta_proxy_sr"),
        "budget5_delta_proxy_spl": budget_interp.get("delta_proxy_spl"),
        "direct_trajectory_promotion_ready": False,
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

    write_jsonl(ARTIFACT_DIR / "result_interpretation_rows.jsonl", interpretation_rows)
    write_jsonl(ARTIFACT_DIR / "budget5_loss_diagnosis_rows.jsonl", loss_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_interpretation_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "route_candidate_rows.jsonl", route_candidate_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, interpretation_rows, loss_rows, route_candidate_rows),
        encoding="utf-8",
    )

    sync_derived()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
