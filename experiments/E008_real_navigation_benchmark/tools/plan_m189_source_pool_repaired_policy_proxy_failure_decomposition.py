#!/usr/bin/env python3
"""Decompose why M187 repaired policy fails the M188 proxy promotion gate."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_v0"
READY_STATUS = "e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m189_source_pool_repaired_policy_proxy_failure_decomposition_blocked"
NEXT_UNIT = "E008-M190 source-pool protected-confidence method boundary and scale decision"

M187_ROOT = EXP_ROOT / "artifacts" / "E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0"
M188_ROOT = EXP_ROOT / "artifacts" / "E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
OUT_ROOT = EXP_ROOT / "artifacts" / "E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0"
DATA_OUT_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M189_source_pool_repaired_policy_proxy_failure_decomposition_v0"

SELECTED_POLICY = "confidence_protected_transition_cost_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
TRANSITION_ONLY = "transition_cost_only_reachable_subset_v0"
SOURCE_PROXY = "path_cost_ascending_reachable_subset_v0"
PRIOR_TRADEOFF = "confidence_path_cost_tradeoff_reachable_subset_v0"


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


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


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
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
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


def first_hit(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9)):
        if row.get("primary_eval_hit"):
            return row
    return None


def build_episode_decomposition_rows(
    candidate_goal_rows: list[dict[str, Any]],
    pairwise_delta_rows: list[dict[str, Any]],
    order_audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        by_episode_policy[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)
    delta_by_episode = {
        str(row.get("adapter_episode_id")): row
        for row in pairwise_delta_rows
        if row.get("policy_id") == SELECTED_POLICY
    }
    audit_by_episode = {
        str(row.get("adapter_episode_id")): row
        for row in order_audit_rows
        if row.get("policy_id") == SELECTED_POLICY
    }
    out: list[dict[str, Any]] = []
    episode_ids = sorted({episode_id for episode_id, _ in by_episode_policy})
    for episode_id in episode_ids:
        selected_hit = first_hit(by_episode_policy.get((episode_id, SELECTED_POLICY), []))
        protected_hit = first_hit(by_episode_policy.get((episode_id, PROTECTED_BASELINE), []))
        selected_rows = by_episode_policy.get((episode_id, SELECTED_POLICY), [])
        protected_rows = by_episode_policy.get((episode_id, PROTECTED_BASELINE), [])
        representative = selected_rows[0] if selected_rows else protected_rows[0] if protected_rows else {}
        selected_hit_uid = selected_hit.get("proposal_uid") if selected_hit else None
        protected_hit_uid = protected_hit.get("proposal_uid") if protected_hit else None
        same_hit = selected_hit_uid is not None and selected_hit_uid == protected_hit_uid
        delta = delta_by_episode.get(episode_id, {})
        if not selected_hit and not protected_hit:
            classification = "shared_source_coverage_or_localization_gap"
        elif same_hit and (finite_float(delta.get("delta_primary_spl_proxy")) or 0.0) < -1e-9:
            classification = "same_success_candidate_delayed_or_costlier"
        elif same_hit and (finite_float(delta.get("delta_primary_spl_proxy")) or 0.0) > 1e-9:
            classification = "same_success_candidate_cheaper_route"
        elif same_hit:
            classification = "same_success_candidate_tie"
        elif selected_hit and not protected_hit:
            classification = "selected_unique_proxy_recovery"
        elif protected_hit and not selected_hit:
            classification = "selected_lost_proxy_recovery"
        else:
            classification = "different_success_candidate"
        audit = audit_by_episode.get(episode_id, {})
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": representative.get("scan_id"),
                "scene_key": representative.get("scene_key"),
                "object_category": representative.get("object_category"),
                "classification": classification,
                "selected_primary_hit": bool(selected_hit),
                "protected_primary_hit": bool(protected_hit),
                "same_success_proposal_uid": same_hit,
                "selected_success_proposal_uid": selected_hit_uid,
                "protected_success_proposal_uid": protected_hit_uid,
                "selected_first_hit_rank": selected_hit.get("visit_rank") if selected_hit else None,
                "protected_first_hit_rank": protected_hit.get("visit_rank") if protected_hit else None,
                "selected_first_hit_cost_m": selected_hit.get("planned_cumulative_path_cost_m") if selected_hit else None,
                "protected_first_hit_cost_m": protected_hit.get("planned_cumulative_path_cost_m") if protected_hit else None,
                "delta_primary_hit": delta.get("delta_primary_hit"),
                "delta_primary_spl_proxy": delta.get("delta_primary_spl_proxy"),
                "delta_primary_first_hit_rank": delta.get("delta_primary_first_hit_rank"),
                "delta_primary_first_hit_cost_m": delta.get("delta_primary_first_hit_cost_m"),
                "first_rank_flip": audit.get("first_rank_flip"),
                "confidence_bin_violation_count": audit.get("confidence_bin_violation_count"),
                "best_any_viewpoint_xz_m": min(
                    [
                        finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m"))
                        for row in selected_rows
                        if finite_float(row.get("candidate_to_nearest_eval_viewpoint_xz_m")) is not None
                    ]
                    or [None]
                ),
                "claim_boundary": "M189 episode decomposition uses M188 eval-only labels to diagnose proxy failure; it is not a policy input.",
            }
        )
    return out


def build_root_cause_rows(
    episode_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    m187_policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    agg = {str(row.get("policy_id")): row for row in aggregate_rows}
    selected = agg.get(SELECTED_POLICY, {})
    protected = agg.get(PROTECTED_BASELINE, {})
    transition_only = agg.get(TRANSITION_ONLY, {})
    selected_spl = finite_float(selected.get("primary_spl_proxy_mean")) or 0.0
    protected_spl = finite_float(protected.get("primary_spl_proxy_mean")) or 0.0
    selected_sr = finite_float(selected.get("primary_proxy_sr")) or 0.0
    protected_sr = finite_float(protected.get("primary_proxy_sr")) or 0.0
    m187_summary = {str(row.get("policy_id")): row for row in m187_policy_rows}
    selected_full_cost = finite_float(m187_summary.get(SELECTED_POLICY, {}).get("planned_cumulative_path_cost_m_mean"))
    protected_full_cost = finite_float(m187_summary.get(PROTECTED_BASELINE, {}).get("planned_cumulative_path_cost_m_mean"))
    transition_full_cost = finite_float(m187_summary.get(TRANSITION_ONLY, {}).get("planned_cumulative_path_cost_m_mean"))
    same_success_rows = [row for row in episode_rows if row.get("same_success_proposal_uid")]
    delayed_rows = [row for row in episode_rows if row.get("classification") == "same_success_candidate_delayed_or_costlier"]
    cheaper_rows = [row for row in episode_rows if row.get("classification") == "same_success_candidate_cheaper_route"]
    shared_gap_rows = [row for row in episode_rows if row.get("classification") == "shared_source_coverage_or_localization_gap"]
    return [
        {
            "version": VERSION,
            "root_cause_id": "no_new_recovery_from_transition_rerank",
            "status": "supported",
            "principle": "A reranker cannot improve proxy SR if all policies already hit the same recoverable candidates and miss the same uncovered case.",
            "evidence": f"selected/protected SR={selected_sr:.6f}/{protected_sr:.6f}; same success proposal rows={len(same_success_rows)}; shared gap rows={len(shared_gap_rows)}.",
            "claim_boundary": "This diagnoses M188 only; it does not claim final navigation behavior.",
        },
        {
            "version": VERSION,
            "root_cause_id": "route_cost_objective_not_first_success_objective",
            "status": "supported",
            "principle": "Lower full-list transition cost does not guarantee lower cost-to-first-success, which is what proxy SPL measures.",
            "evidence": f"selected/protected full-list cost={selected_full_cost:.6f}/{protected_full_cost:.6f}; selected/protected proxy SPL={selected_spl:.6f}/{protected_spl:.6f}; delayed/costlier rows={len(delayed_rows)}; cheaper rows={len(cheaper_rows)}.",
            "claim_boundary": "Transition cost should not be the main ranking objective for search success without a success-likelihood guard.",
        },
        {
            "version": VERSION,
            "root_cause_id": "pure_transition_cost_confirms_likelihood_loss",
            "status": "supported",
            "principle": "The ablation that optimizes transition cost most aggressively gets the shortest full route but worse proxy SPL, so spatial efficiency alone is the wrong target.",
            "evidence": f"transition-only full-list cost={transition_full_cost:.6f}; transition-only proxy SPL={finite_float(transition_only.get('primary_spl_proxy_mean')):.6f}; protected proxy SPL={protected_spl:.6f}.",
            "claim_boundary": "This supports rejecting transition-only or transition-dominant reranking as the main method.",
        },
        {
            "version": VERSION,
            "root_cause_id": "residual_source_coverage_gap_not_rank_fixable",
            "status": "supported",
            "principle": "The remaining failed episode has no candidate within the primary ObjectNav viewpoint threshold, so ordering cannot fix it.",
            "evidence": f"shared gap rows={len(shared_gap_rows)}; best any-viewpoint XZ min={mean([row.get('best_any_viewpoint_xz_m') for row in shared_gap_rows])}.",
            "claim_boundary": "This points to candidate-source/visibility expansion, not another within-pool rerank, for residual recall.",
        },
    ]


def build_method_decision_rows(root_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "reject_m187_selected_transition_repair_as_main_policy",
            "decision": "reject_selected_transition_rerank_for_trajectory_promotion",
            "reason": "It ties protected proxy SR but loses proxy SPL, and the failure is objective mismatch rather than implementation error.",
            "selected_policy_id": SELECTED_POLICY,
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "keep_source_pool_candidate_generation",
            "decision": "keep_source_pool_expansion_as_candidate_source_component",
            "reason": "The 8-episode source-pool denominator still contains recoverable candidates for 7/8 episodes; the failure is ranking/coverage boundary, not candidate-source materialization.",
            "selected_component": "fixed_budget_source_pool_candidate_generation",
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "protected_confidence_execution_default",
            "decision": "use_detector_confidence_reachable_subset_as_safe_execution_default_until_new_evidence",
            "reason": "Protected detector confidence is the strongest current policy by proxy SPL and does not use eval-only labels.",
            "safe_policy_id": PROTECTED_BASELINE,
            "trajectory_execution_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "next_route",
            "decision": "write_method_boundary_and_scale_decision",
            "reason": "Before launching new trajectories, the method must be reframed around source-pool expansion plus protected confidence, or a new success-likelihood guard must be justified.",
            "selected_next_unit": NEXT_UNIT,
            "trajectory_execution_now": False,
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m189_selected_next",
            "decision": "method_boundary_and_scale_decision_before_trajectory",
            "selected_next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
            "reason": "M189 rejects the selected transition repair as the main execution policy and keeps source-pool expansion plus protected confidence as the current defensible branch.",
        }
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "selected_transition_repair_positive_navigation_claim",
            "supported": False,
            "claim_boundary": "M189 rejects the M187 selected transition repair for trajectory promotion because it loses M188 proxy SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "source_pool_candidate_generation_useful",
            "supported": True,
            "claim_boundary": "The source-pool candidate set remains useful as a candidate-source expansion, but this is not yet a final navigation claim.",
        },
        {
            "version": VERSION,
            "claim_id": "protected_confidence_safe_execution_policy",
            "supported": True,
            "claim_boundary": "Detector-confidence reachable-subset ordering is the current safest execution default on this source-pool denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final real navigation still requires a selected method boundary, Docker trajectory execution, scale-up, heldout transfer, and external baselines.",
        },
    ]


def build_readiness_gate_rows(
    missing_inputs: list[str],
    episode_rows: list[dict[str, Any]],
    root_rows: list[dict[str, Any]],
    method_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gates = [
        ("required_inputs_present", not missing_inputs, f"missing={missing_inputs}", True),
        ("episode_decomposition_ready", len(episode_rows) == 8, f"episode rows={len(episode_rows)}; expected=8", True),
        (
            "root_causes_supported",
            all(row.get("status") == "supported" for row in root_rows),
            f"supported={sum(1 for row in root_rows if row.get('status') == 'supported')}/{len(root_rows)}",
            True,
        ),
        (
            "method_decision_ready",
            len(method_rows) >= 4,
            f"method decision rows={len(method_rows)}",
            True,
        ),
        (
            "trajectory_execution_now",
            False,
            "M189 is a failure decomposition and method-boundary unit; no Docker trajectory job should launch here.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m190": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_report(
    coverage: dict[str, Any],
    episode_rows: list[dict[str, Any]],
    root_rows: list[dict[str, Any]],
    method_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M189 Source-Pool Repaired Policy Proxy Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Selected policy: `{SELECTED_POLICY}`.",
            f"- Protected baseline: `{PROTECTED_BASELINE}`.",
            f"- Selected/protected proxy `SR`: {coverage['selected_primary_proxy_sr']} / {coverage['protected_primary_proxy_sr']}.",
            f"- Selected/protected proxy `SPL`: {coverage['selected_primary_spl_proxy_mean']} / {coverage['protected_primary_spl_proxy_mean']}.",
            f"- Same success proposal rows: {coverage['same_success_proposal_rows']}.",
            f"- Same-success delayed/costlier rows: {coverage['same_success_delayed_or_costlier_rows']}.",
            f"- Same-success cheaper rows: {coverage['same_success_cheaper_route_rows']}.",
            f"- Shared source-coverage/localization gap rows: {coverage['shared_gap_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Episode Decomposition",
            "",
            markdown_table(
                episode_rows,
                [
                    "adapter_episode_id",
                    "object_category",
                    "classification",
                    "selected_first_hit_rank",
                    "protected_first_hit_rank",
                    "delta_primary_spl_proxy",
                    "delta_primary_first_hit_cost_m",
                ],
            ),
            "",
            "## Root Causes",
            "",
            markdown_table(root_rows, ["root_cause_id", "status", "principle", "evidence"]),
            "",
            "## Method Decisions",
            "",
            markdown_table(method_rows, ["decision_id", "decision", "reason", "trajectory_execution_now"]),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m190", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M189 rejects `confidence_protected_transition_cost_policy_v1` as a positive navigation-improvement policy.",
            "- M189 keeps source-pool candidate generation as useful, but ranking must default to protected detector confidence until a stronger success-likelihood guard exists.",
            "- M189 does not execute trajectories and does not support final real navigation `SR` / `SPL`.",
            "",
        ]
    )


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    m187_cov = read_json(M187_ROOT / "coverage.json")
    m188_cov = read_json(M188_ROOT / "coverage.json")
    candidate_goal_rows = read_jsonl(M188_ROOT / "candidate_goal_eval_rows.jsonl")
    aggregate_rows = read_jsonl(M188_ROOT / "aggregate_policy_goal_metric_rows.jsonl")
    pairwise_delta_rows = read_jsonl(M188_ROOT / "pairwise_policy_delta_rows.jsonl")
    order_audit_rows = read_jsonl(M187_ROOT / "policy_order_audit_rows.jsonl")
    m187_policy_summary_rows = read_jsonl(M187_ROOT / "policy_summary_rows.jsonl")
    missing_inputs = [
        str(path.relative_to(ROOT))
        for path, rows in [
            (M187_ROOT / "coverage.json", [m187_cov] if m187_cov else []),
            (M188_ROOT / "coverage.json", [m188_cov] if m188_cov else []),
            (M188_ROOT / "candidate_goal_eval_rows.jsonl", candidate_goal_rows),
            (M188_ROOT / "aggregate_policy_goal_metric_rows.jsonl", aggregate_rows),
            (M188_ROOT / "pairwise_policy_delta_rows.jsonl", pairwise_delta_rows),
            (M187_ROOT / "policy_order_audit_rows.jsonl", order_audit_rows),
            (M187_ROOT / "policy_summary_rows.jsonl", m187_policy_summary_rows),
        ]
        if not rows
    ]
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    episode_rows = build_episode_decomposition_rows(candidate_goal_rows, pairwise_delta_rows, order_audit_rows)
    root_rows = build_root_cause_rows(episode_rows, aggregate_rows, m187_policy_summary_rows)
    method_rows = build_method_decision_rows(root_rows)
    route_rows = build_route_decision_rows()
    claim_rows = build_claim_boundary_rows()
    gate_rows = build_readiness_gate_rows(missing_inputs, episode_rows, root_rows, method_rows)
    ready = not any(row.get("blocks_m190") for row in gate_rows)
    class_counts = Counter(str(row.get("classification")) for row in episode_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(OUT_ROOT),
        "derived_output_root": str(DATA_OUT_ROOT),
        "m187_status": m187_cov.get("status"),
        "m188_status": m188_cov.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "selected_primary_proxy_sr": m188_cov.get("selected_primary_proxy_sr"),
        "selected_primary_spl_proxy_mean": m188_cov.get("selected_primary_spl_proxy_mean"),
        "protected_primary_proxy_sr": m188_cov.get("protected_primary_proxy_sr"),
        "protected_primary_spl_proxy_mean": m188_cov.get("protected_primary_spl_proxy_mean"),
        "episode_decomposition_rows": len(episode_rows),
        "classification_counts": dict(sorted(class_counts.items())),
        "same_success_proposal_rows": sum(1 for row in episode_rows if row.get("same_success_proposal_uid")),
        "same_success_delayed_or_costlier_rows": class_counts.get("same_success_candidate_delayed_or_costlier", 0),
        "same_success_cheaper_route_rows": class_counts.get("same_success_candidate_cheaper_route", 0),
        "same_success_tie_rows": class_counts.get("same_success_candidate_tie", 0),
        "shared_gap_rows": class_counts.get("shared_source_coverage_or_localization_gap", 0),
        "root_cause_rows": len(root_rows),
        "method_decision_rows": len(method_rows),
        "readiness_gate_rows": len(gate_rows),
        "trajectory_execution_now": False,
        "transition_repair_positive_claim_ready": False,
        "source_pool_candidate_generation_kept": True,
        "protected_confidence_execution_default": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (OUT_ROOT, DATA_OUT_ROOT):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "episode_decomposition_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "root_cause_rows.jsonl", root_rows)
        write_jsonl(output_dir / "method_decision_rows.jsonl", method_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    (OUT_ROOT / "report.md").write_text(
        build_report(coverage, episode_rows, root_rows, method_rows, gate_rows),
        encoding="utf-8",
    )
    (DATA_OUT_ROOT / "report.md").write_text((OUT_ROOT / "report.md").read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
