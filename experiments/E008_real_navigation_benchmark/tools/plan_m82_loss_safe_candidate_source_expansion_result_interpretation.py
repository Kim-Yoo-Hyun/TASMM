#!/usr/bin/env python3
"""Interpret M81 loss-safe expansion results and choose the next E008 route."""

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
M80_DIR = EXP_ROOT / "artifacts" / "E008-M80_loss_safe_candidate_source_expansion_row_materialization_smoke_v0"
M81_DIR = EXP_ROOT / "artifacts" / "E008-M81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M82_loss_safe_candidate_source_expansion_result_interpretation_v0"
)

VERSION = "e008_m82_loss_safe_candidate_source_expansion_result_interpretation_v0"
READY_STATUS = "e008_m82_loss_safe_candidate_source_expansion_result_interpretation_ready"
BLOCKED_STATUS = "e008_m82_loss_safe_candidate_source_expansion_result_interpretation_blocked"
NEXT_UNIT = "E008-M83 full-val-mini source-gap non-oracle source/observation expansion contract"

CORE_POLICY = "detector_confidence_budget5_core_v0"
APPEND_POLICY = "loss_safe_append_source_probe_budget8_v0"
SOURCE_EXPAND_POLICY = "loss_safe_observation_source_expansion_probe_v0"


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


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def aggregate_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row.get("metric_scope") == "policy_aggregate":
            out[(str(row.get("eval_budget_scope")), str(row.get("policy_id")))] = row
    return out


def build_result_interpretation_rows(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    delta_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    idx = aggregate_index(aggregate_rows)
    delta_by_scope = {str(row.get("eval_budget_scope")): row for row in delta_summary_rows}
    rows: list[dict[str, Any]] = []
    for scope in ("detector_budget5", "policy_budget"):
        core = idx.get((scope, CORE_POLICY), {})
        append = idx.get((scope, APPEND_POLICY), {})
        delta = delta_by_scope.get(scope, {})
        core_sr = finite_float(core.get("primary_proxy_sr"))
        append_sr = finite_float(append.get("primary_proxy_sr"))
        core_spl = finite_float(core.get("primary_spl_proxy_mean"))
        append_spl = finite_float(append.get("primary_spl_proxy_mean"))
        if scope == "detector_budget5":
            interpretation = "budget5_preserved_append_does_not_change_primary_budget"
            supports = bool(coverage.get("detector_budget5_eval_loss_safe"))
        else:
            interpretation = "policy_budget_append_has_diagnostic_gain_without_loss_but_not_budget5_deployable"
            supports = int(delta.get("append_gain_rows") or 0) > 0 and int(delta.get("append_loss_rows") or 0) == 0
        rows.append(
            {
                "version": VERSION,
                "row_type": "result_interpretation",
                "eval_budget_scope": scope,
                "baseline_policy_id": CORE_POLICY,
                "method_policy_id": APPEND_POLICY,
                "baseline_proxy_sr": core_sr,
                "method_proxy_sr": append_sr,
                "delta_proxy_sr": append_sr - core_sr
                if append_sr is not None and core_sr is not None
                else None,
                "baseline_proxy_spl": core_spl,
                "method_proxy_spl": append_spl,
                "delta_proxy_spl": append_spl - core_spl
                if append_spl is not None and core_spl is not None
                else None,
                "append_gain_rows": delta.get("append_gain_rows"),
                "append_loss_rows": delta.get("append_loss_rows"),
                "source_gap_append_gain_rows": delta.get("source_gap_append_gain_rows"),
                "source_gap_append_loss_rows": delta.get("source_gap_append_loss_rows"),
                "supports_diagnostic_append_gain": supports,
                "supports_deployable_budget5_policy": False,
                "supports_source_gap_recovery": False,
                "interpretation": interpretation,
                "claim_boundary": "M82 interprets M81 proxy metrics only; no Habitat trajectory is executed.",
            }
        )
    return rows


def build_append_gain_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in pairwise_rows:
        if row.get("eval_budget_scope") != "policy_budget" or row.get("comparison") != "append_gain":
            continue
        out.append(
            {
                "version": VERSION,
                "row_type": "append_gain_interpretation",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "method_primary_first_hit_rank": row.get("method_primary_first_hit_rank"),
                "delta_primary_spl_proxy": row.get("delta_primary_spl_proxy"),
                "baseline_best_any_viewpoint_xz_m": row.get("baseline_best_any_viewpoint_xz_m"),
                "method_best_any_viewpoint_xz_m": row.get("method_best_any_viewpoint_xz_m"),
                "source_gap_expansion_case": bool(row.get("source_gap_expansion_case")),
                "interpretation": "append candidate helps only after detector budget-5, so this is budget-extension evidence",
                "trajectory_priority": "low_until_source_gap_expansion_is_addressed",
                "claim_boundary": "Append gain is proxy evidence at ranks beyond primary budget; it is not deployable budget-5 evidence.",
            }
        )
    return out


def build_source_gap_decision_rows(
    source_plan_rows: list[dict[str, Any]],
    source_eval_plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_by_plan = {str(row.get("plan_uid")): row for row in source_eval_plan_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_plan_rows:
        if row.get("case_type") == "source_gap_unresolved":
            grouped[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for episode, plans in sorted(grouped.items()):
        recovered = any(
            bool(eval_by_plan.get(str(plan.get("plan_uid")), {}).get("existing_append_recovered_primary_proxy"))
            for plan in plans
        )
        action_counts = Counter(str(plan.get("action_id")) for plan in plans)
        long_job_actions = [
            str(plan.get("action_id"))
            for plan in plans
            if bool(plan.get("requires_long_job_later"))
        ]
        first = plans[0] if plans else {}
        out.append(
            {
                "version": VERSION,
                "row_type": "source_gap_decision",
                "adapter_episode_id": episode,
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "source_plan_rows": len(plans),
                "action_counts": dict(action_counts),
                "long_job_action_ids": sorted(set(long_job_actions)),
                "existing_append_recovered_primary_proxy": recovered,
                "selected_next_action": "non_oracle_source_observation_expansion_contract",
                "source_gap_resolved": False,
                "requires_contract_before_long_job": True,
                "claim_boundary": "Source-gap case selection is diagnostic; M83 must define non-oracle allowed inputs before rendering or detection.",
            }
        )
    return out


def build_trajectory_decision_rows(
    interpretation_rows: list[dict[str, Any]],
    append_gain_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_scope = {str(row.get("eval_budget_scope")): row for row in interpretation_rows}
    detector = by_scope.get("detector_budget5", {})
    policy = by_scope.get("policy_budget", {})
    rows = [
        {
            "version": VERSION,
            "route_id": "promote_append_budget8_policy_to_trajectory",
            "decision": "reject_now",
            "reason": "Append gain is outside the detector budget-5 scope and does not recover source-gap rows.",
            "evidence": f"append_gain_rows={len(append_gain_rows)}, source_gap_unresolved_rows={len(source_gap_rows)}",
            "required_before_reconsideration": "source-gap recovery or a paper-facing reason to evaluate budget-8 trajectories",
        },
        {
            "version": VERSION,
            "route_id": "source_observation_expansion_contract_first",
            "decision": "select",
            "reason": "M81 proves existing append rows are loss-safe but insufficient for source-gap; M80 already contains non-oracle expansion plans.",
            "evidence": f"detector_budget5_delta_sr={fmt(detector.get('delta_proxy_sr'))}, policy_budget_delta_sr={fmt(policy.get('delta_proxy_sr'))}",
            "required_before_reconsideration": "M83 must fix allowed inputs, output paths, long-job policy, and verification gates before any render/detector run.",
        },
        {
            "version": VERSION,
            "route_id": "package_m81_as_diagnostic_table",
            "decision": "defer",
            "reason": "M81 is useful boundary evidence, but top-tier navigation path still needs source-gap repair and trajectory evidence.",
            "evidence": "detector budget-5 preservation true; source-gap gain 0",
            "required_before_reconsideration": "Use if source/observation expansion also fails.",
        },
        {
            "version": VERSION,
            "route_id": "external_navigation_search_baselines_now",
            "decision": "defer",
            "reason": "External navigation/search baselines are necessary for final claims, but current internal source-gap blocker should be resolved first.",
            "evidence": "final real navigation SR/SPL ready false",
            "required_before_reconsideration": "Resume after source-gap expansion or after declaring E008 diagnostic-only.",
        },
    ]
    for row in rows:
        row["trajectory_execution_ready_now"] = False
        row["launch_long_job_now"] = False
        row["claim_boundary"] = "M82 is a route decision unit, not a trajectory result."
    return rows


def build_gate_rows(
    coverage: dict[str, Any],
    append_gain_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m81_ready",
            "gate_status": "pass"
            if coverage.get("status") == "e008_m81_loss_safe_candidate_source_expansion_goal_evaluation_smoke_ready"
            else "fail",
            "blocks_next": False,
            "rationale": "M82 requires M81 goal-evaluation metrics.",
        },
        {
            "version": VERSION,
            "gate_id": "detector_budget5_preservation",
            "gate_status": "pass" if coverage.get("detector_budget5_eval_loss_safe") else "fail",
            "blocks_next": False,
            "rationale": "Append policy must preserve detector budget-5 before any expansion is considered.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_budget_append_gain",
            "gate_status": "pass" if append_gain_rows else "warning",
            "blocks_next": False,
            "rationale": "Append-only policy-budget gain is diagnostic evidence, not primary budget evidence.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_recovery",
            "gate_status": "fail" if source_gap_rows else "pass",
            "blocks_next": False,
            "rationale": "Existing append rows do not recover source-gap episodes.",
        },
        {
            "version": VERSION,
            "gate_id": "direct_trajectory_promotion",
            "gate_status": "fail",
            "blocks_next": False,
            "rationale": "No source-gap recovery and no deployable budget-5 improvement; source expansion contract comes first.",
        },
        {
            "version": VERSION,
            "gate_id": "m83_contract_route",
            "gate_status": "pass" if source_gap_rows else "warning",
            "blocks_next": False,
            "rationale": "M83 should precommit allowed source/observation expansion inputs and verification before any long job.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_loss_safe_append_diagnostic",
            "supported": True,
            "claim_boundary": "M81/M82 support loss-safe append diagnostics under policy-budget scope.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_detector_budget5_preservation",
            "supported": True,
            "claim_boundary": "Detector budget-5 behavior is preserved, but not improved.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_gap_recovery",
            "supported": False,
            "claim_boundary": "Existing append rows recover 0 source-gap cases.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_budget5_policy",
            "supported": False,
            "claim_boundary": "Policy-budget gain occurs at ranks beyond the primary budget-5 scope.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M82 does not execute Habitat trajectories and does not compare external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M82 does not add task-context-specific or natural-language intent evidence.",
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
            "rationale": "Precommit source/observation expansion contract before rendering, detection, or trajectory execution.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    interpretation_rows: list[dict[str, Any]],
    append_gain_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    interp_lines = [
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
        for row in interpretation_rows
    ]
    append_lines = [
        f"| `{row['adapter_episode_id']}` | {row['object_category']} | {row['method_primary_first_hit_rank']} | {fmt(row['delta_primary_spl_proxy'])} | {fmt(row['method_best_any_viewpoint_xz_m'])} |"
        for row in append_gain_rows
    ]
    source_lines = [
        f"| `{row['adapter_episode_id']}` | {row['object_category']} | {row['existing_append_recovered_primary_proxy']} | {', '.join(row['long_job_action_ids'])} |"
        for row in source_gap_rows
    ]
    route_lines = [
        f"| `{row['route_id']}` | {row['decision']} | {row['reason']} |"
        for row in route_rows
    ]
    return f"""# E008-M82 Loss-Safe Expansion Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M81 status: `{coverage['m81_status']}`.
- Append gain/loss rows: {coverage['append_gain_rows']} / {coverage['append_loss_rows']}.
- Source-gap append gain/loss rows: {coverage['source_gap_append_gain_rows']} / {coverage['source_gap_append_loss_rows']}.
- Direct trajectory promotion ready: {coverage['direct_trajectory_promotion_ready']}.
- Source/observation expansion contract required: {coverage['source_observation_expansion_contract_required']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Result Interpretation

| scope | baseline SR | method SR | delta SR | baseline SPL | method SPL | delta SPL | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(interp_lines)}

## Append Gains

| episode | object | hit rank | delta SPL proxy | best xz distance |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(append_lines) if append_lines else '| none | none | NA | NA | NA |'}

## Source-Gap Decision

| episode | object | existing append recovered | long-job action ids |
| --- | --- | --- | --- |
{chr(10).join(source_lines) if source_lines else '| none | none | NA | NA |'}

## Route Decision

| route_id | decision | reason |
| --- | --- | --- |
{chr(10).join(route_lines)}

## Claim Boundary

- M82 supports loss-safe append diagnostics, not final navigation.
- M82 blocks direct trajectory promotion because source-gap recovery is 0 and append gain is outside budget-5.
- M83 should define a non-oracle source/observation expansion contract before any long-running render/detector job.
"""


def sync_derived() -> None:
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)


def main() -> int:
    generated_at = datetime.now().replace(microsecond=0).isoformat()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    m81_coverage = read_json(M81_DIR / "coverage.json")
    aggregate_rows = read_jsonl(M81_DIR / "aggregate_policy_goal_metric_rows.jsonl")
    delta_summary_rows = read_jsonl(M81_DIR / "policy_delta_summary_rows.jsonl")
    pairwise_rows = read_jsonl(M81_DIR / "policy_pairwise_delta_rows.jsonl")
    source_eval_plan_rows = read_jsonl(M81_DIR / "source_observation_expansion_eval_plan_rows.jsonl")
    source_plan_rows = read_jsonl(M80_DIR / "source_observation_expansion_plan_rows.jsonl")

    missing_inputs = []
    required = [
        (M81_DIR / "coverage.json", [m81_coverage] if m81_coverage else []),
        (M81_DIR / "aggregate_policy_goal_metric_rows.jsonl", aggregate_rows),
        (M81_DIR / "policy_delta_summary_rows.jsonl", delta_summary_rows),
        (M81_DIR / "policy_pairwise_delta_rows.jsonl", pairwise_rows),
        (M81_DIR / "source_observation_expansion_eval_plan_rows.jsonl", source_eval_plan_rows),
        (M80_DIR / "source_observation_expansion_plan_rows.jsonl", source_plan_rows),
    ]
    for path, rows in required:
        if not rows:
            missing_inputs.append(str(path))

    interpretation_rows = build_result_interpretation_rows(
        m81_coverage,
        aggregate_rows,
        delta_summary_rows,
    )
    append_gain_rows = build_append_gain_rows(pairwise_rows)
    source_gap_rows = build_source_gap_decision_rows(source_plan_rows, source_eval_plan_rows)
    trajectory_decision_rows = build_trajectory_decision_rows(
        interpretation_rows,
        append_gain_rows,
        source_gap_rows,
    )
    gate_rows = build_gate_rows(m81_coverage, append_gain_rows, source_gap_rows)
    claim_boundary_rows = build_claim_boundary_rows()
    next_action_rows = build_next_action_rows()

    status = READY_STATUS if not missing_inputs else BLOCKED_STATUS
    append_loss_rows = int(m81_coverage.get("policy_budget_append_loss_rows") or 0)
    source_gap_append_gain_rows = int(m81_coverage.get("policy_budget_source_gap_append_gain_rows") or 0)
    source_gap_append_loss_rows = int(m81_coverage.get("policy_budget_source_gap_append_loss_rows") or 0)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": generated_at,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m81_status": m81_coverage.get("status"),
        "missing_inputs": missing_inputs,
        "result_interpretation_rows": len(interpretation_rows),
        "append_gain_rows": len(append_gain_rows),
        "append_loss_rows": append_loss_rows,
        "source_gap_decision_rows": len(source_gap_rows),
        "source_gap_append_gain_rows": source_gap_append_gain_rows,
        "source_gap_append_loss_rows": source_gap_append_loss_rows,
        "trajectory_decision_rows": len(trajectory_decision_rows),
        "gate_rows": len(gate_rows),
        "gate_fail_rows": sum(1 for row in gate_rows if row.get("gate_status") == "fail"),
        "gate_warning_rows": sum(1 for row in gate_rows if row.get("gate_status") == "warning"),
        "claim_boundary_rows": len(claim_boundary_rows),
        "detector_budget5_eval_loss_safe": bool(m81_coverage.get("detector_budget5_eval_loss_safe")),
        "policy_budget_append_diagnostic_ready": bool(append_gain_rows and append_loss_rows == 0),
        "source_gap_recovered_by_existing_append": source_gap_append_gain_rows > 0,
        "direct_trajectory_promotion_ready": False,
        "trajectory_execution_ready_now": False,
        "source_observation_expansion_contract_required": True,
        "deployable_search_policy_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_route": "source_observation_expansion_contract_first",
        "selected_next_unit": NEXT_UNIT,
    }

    write_jsonl(ARTIFACT_DIR / "result_interpretation_rows.jsonl", interpretation_rows)
    write_jsonl(ARTIFACT_DIR / "append_gain_interpretation_rows.jsonl", append_gain_rows)
    write_jsonl(ARTIFACT_DIR / "source_gap_decision_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_source_expansion_decision_rows.jsonl", trajectory_decision_rows)
    write_jsonl(ARTIFACT_DIR / "gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, interpretation_rows, append_gain_rows, source_gap_rows, trajectory_decision_rows),
        encoding="utf-8",
    )

    sync_derived()
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
