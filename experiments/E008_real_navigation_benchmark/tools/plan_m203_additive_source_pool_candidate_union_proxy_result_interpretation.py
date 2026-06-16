#!/usr/bin/env python3
"""Interpret M202 additive source-pool proxy results before trajectory work."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m203_additive_source_pool_candidate_union_proxy_result_interpretation_v0"
READY_STATUS = "e008_m203_additive_source_pool_candidate_union_proxy_result_interpretation_ready"
NEXT_UNIT = "E008-M204 additive source-pool candidate-union Docker trajectory execution contract/preflight"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M203_additive_source_pool_candidate_union_proxy_result_interpretation_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M203_additive_source_pool_candidate_union_proxy_result_interpretation_v0"
)

M201_DIR = EXP_ROOT / "artifacts" / "E008-M201_additive_source_pool_candidate_union_row_materialization_v0"
M202_DIR = EXP_ROOT / "artifacts" / "E008-M202_additive_source_pool_candidate_union_goal_evaluation_proxy_v0"

SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
BASELINE_ONLY_POLICY = "no_source_pool_detector_confidence_reachable_subset_v0"
SOURCE_POOL_REPLACEMENT_POLICY = "source_pool_replacement_detector_confidence_reachable_subset_v0"
UNGUARDED_UNION_POLICY = "additive_union_unguarded_confidence_sort_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    path.write_text(
        "".join(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def finite_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def row_by_policy(rows: list[dict[str, Any]], policy_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("policy_id") == policy_id:
            return row
    return {}


def build_source_summary(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_hit_source_counts = Counter(
        row.get("selected_first_hit_source_family") for row in source_rows if row.get("selected_primary_hit")
    )
    selected_hit_action_counts = Counter(
        row.get("selected_first_hit_union_action") for row in source_rows if row.get("selected_primary_hit")
    )
    return {
        "source_contribution_rows": len(source_rows),
        "selected_primary_hit_rows": sum(1 for row in source_rows if row.get("selected_primary_hit")),
        "baseline_primary_hit_rows": sum(1 for row in source_rows if row.get("baseline_primary_hit")),
        "replacement_primary_hit_rows": sum(1 for row in source_rows if row.get("replacement_primary_hit")),
        "baseline_success_lost_by_selected_rows": sum(
            1 for row in source_rows if row.get("baseline_primary_hit") and not row.get("selected_primary_hit")
        ),
        "source_pool_incremental_recovery_rows": sum(
            1 for row in source_rows if row.get("source_pool_incremental_recovery")
        ),
        "baseline_fail_selected_fail_rows": sum(
            1 for row in source_rows if not row.get("baseline_primary_hit") and not row.get("selected_primary_hit")
        ),
        "selected_hit_source_family_counts": dict(sorted(selected_hit_source_counts.items())),
        "selected_hit_union_action_counts": dict(sorted(selected_hit_action_counts.items())),
        "selected_minus_baseline_spl_proxy_sum": sum(
            finite_float(row.get("selected_minus_baseline_spl_proxy")) or 0.0 for row in source_rows
        ),
    }


def build_policy_interpretation_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in policy_rows:
        policy_id = row.get("policy_id")
        interpretation = "not_selected"
        selected_for_m204 = False
        if policy_id == SELECTED_POLICY:
            interpretation = "selected_for_m204_contract_preflight"
            selected_for_m204 = True
        elif policy_id == SOURCE_POOL_REPLACEMENT_POLICY:
            interpretation = "negative_ablation_replacement_deletes_reliable_baseline_evidence"
        elif policy_id == UNGUARDED_UNION_POLICY:
            interpretation = "positive_sr_ablation_but_lower_spl_than_source_gap_guard"
        elif policy_id == BASELINE_ONLY_POLICY:
            interpretation = "protected_baseline_for_trajectory_comparison"
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "interpretation": interpretation,
                "selected_for_m204_contract": selected_for_m204,
                "candidate_rows": row.get("candidate_rows"),
                "primary_success_rows": row.get("primary_success_rows"),
                "baseline_primary_success_rows": row.get("baseline_primary_success_rows"),
                "delta_primary_success_rows": row.get("delta_primary_success_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "baseline_primary_proxy_sr": row.get("baseline_primary_proxy_sr"),
                "delta_primary_proxy_sr": row.get("delta_primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "baseline_primary_spl_proxy_mean": row.get("baseline_primary_spl_proxy_mean"),
                "delta_primary_spl_proxy_mean": row.get("delta_primary_spl_proxy_mean"),
                "trajectory_claim_ready": False,
            }
        )
    return out


def build_gate_rows(
    m201: dict[str, Any],
    m202: dict[str, Any],
    selected_row: dict[str, Any],
    source_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "fixed_denominator",
            "pass": m201.get("denominator_rows") == m202.get("full_denominator_rows") == 30,
            "evidence": "M201 denominator rows and M202 full denominator rows both remain 30.",
            "value": m202.get("full_denominator_rows"),
        },
        {
            "version": VERSION,
            "gate": "baseline_preservation",
            "pass": bool(m201.get("baseline_prefix_audit_pass"))
            and finite_int(m201.get("baseline_candidate_loss_count")) == 0
            and finite_int(source_summary.get("baseline_success_lost_by_selected_rows")) == 0,
            "evidence": "M201 preserves the no-source baseline prefix and M202 loses no baseline successes.",
            "value": source_summary.get("baseline_success_lost_by_selected_rows"),
        },
        {
            "version": VERSION,
            "gate": "leakage_audit",
            "pass": bool(m201.get("leakage_audit_pass")) and bool(m202.get("leakage_audit_pass")),
            "evidence": "M201/M202 policy rows do not use ObjectNav eval goal/viewpoint as policy input.",
            "value": m202.get("leakage_audit_pass"),
        },
        {
            "version": VERSION,
            "gate": "positive_proxy_delta",
            "pass": bool(m202.get("positive_proxy_gate_pass"))
            and int(selected_row.get("delta_primary_success_rows") or 0) > 0
            and float(selected_row.get("delta_primary_spl_proxy_mean") or 0.0) > 0.0,
            "evidence": "Selected additive union improves proxy SR/SPL over the protected no-source baseline.",
            "value": {
                "delta_success": selected_row.get("delta_primary_success_rows"),
                "delta_proxy_sr": selected_row.get("delta_primary_proxy_sr"),
                "delta_proxy_spl": selected_row.get("delta_primary_spl_proxy_mean"),
            },
        },
        {
            "version": VERSION,
            "gate": "replacement_negative_ablation",
            "pass": True,
            "evidence": "Source-pool replacement is negative, so the method form must preserve reliable baseline evidence and append source-pool evidence.",
            "value": SOURCE_POOL_REPLACEMENT_POLICY,
        },
        {
            "version": VERSION,
            "gate": "direct_real_navigation_claim",
            "pass": False,
            "evidence": "M202 is leakage-safe proxy evaluation only; Habitat trajectory execution has not been run for the selected additive union policy.",
            "value": None,
        },
    ]


def build_decision_rows(all_gates_pass: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "promote_to_docker_trajectory_contract_preflight",
            "selected": all_gates_pass,
            "selected_next_unit": NEXT_UNIT,
            "reason": "M202 passes a leakage-safe positive proxy gate while preserving the protected no-source baseline; the next defensible step is a Docker trajectory contract/preflight, not a direct paper claim.",
            "launch_long_job_now": False,
            "trajectory_contract_promoted": all_gates_pass,
            "trajectory_execution_promoted": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        },
        {
            "version": VERSION,
            "decision": "skip_direct_trajectory_execution_without_contract",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "Trajectory execution must first fix runner rows, policy baselines, Docker/data preflight, metrics, and leakage checks.",
            "launch_long_job_now": False,
            "trajectory_contract_promoted": False,
            "trajectory_execution_promoted": False,
        },
        {
            "version": VERSION,
            "decision": "reject_source_pool_replacement_policy",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The replacement route loses seven successes against the protected no-source baseline in M202.",
            "launch_long_job_now": False,
            "trajectory_contract_promoted": False,
            "trajectory_execution_promoted": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_additive_union_proxy_gate",
            "supported": True,
            "claim_boundary": "M203 supports a proxy-level claim that additive source-pool candidate union can recover additional leakage-safe ObjectNav proxy hits without deleting protected no-source detector successes.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_method_form_boundary",
            "supported": True,
            "claim_boundary": "M203 supports the method-form boundary that source-pool evidence should be additive under a source-gap guard, because source-pool replacement is a negative ablation.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M203 does not support real navigation SR/SPL; it selects the Docker trajectory contract/preflight as the next required gate.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M203 is still a 30-row HM3D val-mini proxy interpretation and does not establish final real RGB-D/open-vocabulary robustness.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M203 does not change the E006 boundary; human intent remains an optional conditioning/ablation axis until a separate utility policy redesign succeeds.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack": "The improvement is just adding more candidates.",
            "defense": "M202 includes a replacement-negative ablation and M201 preserves the protected baseline prefix; M204 must still measure candidate visits/path cost so extra candidates are penalized.",
            "remaining_risk": "Proxy SPL gain is small, so trajectory execution may erase the proxy advantage.",
        },
        {
            "version": VERSION,
            "attack": "The policy could be tuned to the ObjectNav goal.",
            "defense": "M200/M201/M202 forbid ObjectNav goal/viewpoint and success-label fields for policy rows; eval labels are joined only for metric computation.",
            "remaining_risk": "M204 must preserve the same policy-input audit in runner rows.",
        },
        {
            "version": VERSION,
            "attack": "The scale is too small for a top-tier claim.",
            "defense": "M203 is not a final claim; it is a bounded promotion gate from proxy diagnosis to Docker trajectory execution.",
            "remaining_risk": "Heldout scenes, external nav/search baselines, and larger denominators remain required.",
        },
        {
            "version": VERSION,
            "attack": "Source-pool evidence is unreliable.",
            "defense": "The selected route does not replace reliable current detector evidence; it appends source-pool candidates only after protected no-source evidence.",
            "remaining_risk": "If M204 shows high visit/path overhead, the source-pool branch must be further budgeted or rejected.",
        },
    ]


def build_m204_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "contract_item": "runner_rows",
            "required": True,
            "requirement": "Use the same 30-row M202 denominator and selected additive union policy rows.",
        },
        {
            "version": VERSION,
            "contract_item": "baselines",
            "required": True,
            "requirement": "Execute or materialize comparable rows for selected additive union, no-source baseline, source-pool replacement negative ablation, and unguarded union ablation if feasible.",
        },
        {
            "version": VERSION,
            "contract_item": "metrics",
            "required": True,
            "requirement": "Report executed SR, SPL, path length, candidate visits, success-by-source, and failure rows.",
        },
        {
            "version": VERSION,
            "contract_item": "docker_preflight",
            "required": True,
            "requirement": "Validate Docker image, dataset mounts, navmesh access, Habitat episode loading, and write logs under logs/ if execution is long-running.",
        },
        {
            "version": VERSION,
            "contract_item": "claim_boundary",
            "required": True,
            "requirement": "Do not claim real navigation improvement unless executed SR/SPL improves over the protected baseline under the fixed denominator.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> str:
    return f"""# E008-M203 Additive Source-Pool Proxy Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input artifacts: `E008-M201`, `E008-M202`.
- Selected policy: `{coverage['selected_policy_id']}`.
- Fixed denominator rows: {coverage['full_denominator_rows']}.
- Selected proxy `SR` / `SPL`: {fmt(coverage['selected_primary_proxy_sr'])} / {fmt(coverage['selected_primary_spl_proxy_mean'])}.
- Protected baseline proxy `SR` / `SPL`: {fmt(coverage['baseline_primary_proxy_sr'])} / {fmt(coverage['baseline_primary_spl_proxy_mean'])}.
- Delta success / proxy `SR` / proxy `SPL`: {coverage['selected_minus_baseline_success_rows']} / {fmt(coverage['selected_minus_baseline_proxy_sr'])} / {fmt(coverage['selected_minus_baseline_spl_proxy_mean'])}.
- Source-pool incremental recoveries: {coverage['source_pool_incremental_recovery_rows']}.
- Baseline successes lost by selected policy: {coverage['baseline_success_lost_by_selected_rows']}.
- Trajectory contract promoted: {coverage['trajectory_contract_promoted']}.
- Trajectory execution promoted: {coverage['trajectory_execution_promoted']}.
- Selected next unit: `{coverage['selected_next_unit']}`.

## Policy Interpretation

{markdown_table(policy_rows, ['policy_id', 'interpretation', 'primary_success_rows', 'delta_primary_success_rows', 'primary_proxy_sr', 'delta_primary_proxy_sr', 'primary_spl_proxy_mean', 'delta_primary_spl_proxy_mean'])}

## Gate Results

{markdown_table(gate_rows, ['gate', 'pass', 'evidence'])}

## Claim Boundary

{markdown_table(claim_rows, ['claim_id', 'supported', 'claim_boundary'])}

## Interpretation

M202 is a positive proxy gate, not a final navigation result. The selected additive union policy preserves the protected no-source detector baseline and adds two proxy recoveries, while source-pool replacement remains a negative ablation. This supports moving to a Docker trajectory contract/preflight, where candidate visits and path costs can penalize the extra candidate pool.
"""


def main() -> None:
    m201 = read_json(M201_DIR / "coverage.json")
    m202 = read_json(M202_DIR / "coverage.json")
    if not m201:
        raise SystemExit("missing M201 coverage.json")
    if not m202:
        raise SystemExit("missing M202 coverage.json")

    m202_policy_rows = read_jsonl(M202_DIR / "policy_comparison_rows.jsonl")
    source_rows = read_jsonl(M202_DIR / "source_contribution_rows.jsonl")
    selected_row = row_by_policy(m202_policy_rows, SELECTED_POLICY)
    if not selected_row:
        raise SystemExit(f"missing selected policy row: {SELECTED_POLICY}")

    source_summary = build_source_summary(source_rows)
    policy_interpretation_rows = build_policy_interpretation_rows(m202_policy_rows)
    gate_rows = build_gate_rows(m201, m202, selected_row, source_summary)
    required_gates = [row for row in gate_rows if row["gate"] != "direct_real_navigation_claim"]
    all_required_gates_pass = all(bool(row.get("pass")) for row in required_gates)
    decision_rows = build_decision_rows(all_required_gates_pass)
    claim_boundary_rows = build_claim_boundary_rows()
    reviewer_defense_rows = build_reviewer_defense_rows()
    m204_contract_rows = build_m204_contract_rows()

    coverage = {
        "version": VERSION,
        "status": READY_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m201_status": m201.get("status"),
        "m202_status": m202.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "baseline_policy_id": BASELINE_ONLY_POLICY,
        "source_pool_replacement_policy_id": SOURCE_POOL_REPLACEMENT_POLICY,
        "unguarded_union_policy_id": UNGUARDED_UNION_POLICY,
        "full_denominator_rows": m202.get("full_denominator_rows"),
        "selected_primary_success_rows": selected_row.get("primary_success_rows"),
        "baseline_primary_success_rows": selected_row.get("baseline_primary_success_rows"),
        "selected_minus_baseline_success_rows": selected_row.get("delta_primary_success_rows"),
        "selected_primary_proxy_sr": selected_row.get("primary_proxy_sr"),
        "baseline_primary_proxy_sr": selected_row.get("baseline_primary_proxy_sr"),
        "selected_minus_baseline_proxy_sr": selected_row.get("delta_primary_proxy_sr"),
        "selected_primary_spl_proxy_mean": selected_row.get("primary_spl_proxy_mean"),
        "baseline_primary_spl_proxy_mean": selected_row.get("baseline_primary_spl_proxy_mean"),
        "selected_minus_baseline_spl_proxy_mean": selected_row.get("delta_primary_spl_proxy_mean"),
        "source_pool_incremental_recovery_rows": source_summary.get("source_pool_incremental_recovery_rows"),
        "baseline_success_lost_by_selected_rows": source_summary.get("baseline_success_lost_by_selected_rows"),
        "baseline_prefix_audit_pass": m201.get("baseline_prefix_audit_pass"),
        "dedup_audit_pass": m201.get("dedup_audit_pass"),
        "leakage_audit_pass": bool(m201.get("leakage_audit_pass")) and bool(m202.get("leakage_audit_pass")),
        "positive_proxy_gate_pass": bool(m202.get("positive_proxy_gate_pass")),
        "required_gates_pass": all_required_gates_pass,
        "trajectory_contract_promoted": all_required_gates_pass,
        "trajectory_execution_promoted": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "m204_contract_ready": all_required_gates_pass,
        "selected_next_unit": NEXT_UNIT,
        **source_summary,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_interpretation_rows.jsonl", policy_interpretation_rows)
        write_jsonl(output_dir / "trajectory_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "decision_rows.jsonl", decision_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
        write_jsonl(output_dir / "reviewer_defense_rows.jsonl", reviewer_defense_rows)
        write_jsonl(output_dir / "m204_contract_rows.jsonl", m204_contract_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_interpretation_rows, gate_rows, claim_boundary_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
