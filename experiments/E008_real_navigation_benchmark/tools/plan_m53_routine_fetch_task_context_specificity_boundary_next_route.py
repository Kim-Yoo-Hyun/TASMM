#!/usr/bin/env python3
"""Decide the task-context boundary after the M52 routine-fetch repair result."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M52_DIR = EXP_ROOT / "artifacts" / "E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0"
)

VERSION = "e008_m53_routine_fetch_task_context_specificity_boundary_next_route_v0"
READY_STATUS = "e008_m53_routine_fetch_task_context_specificity_boundary_ready"
BLOCKED_STATUS = "e008_m53_routine_fetch_task_context_specificity_boundary_blocked"
NEXT_UNIT = "E008-M54 navigation boundary package and paper-table freeze"

H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_POLICY = "fixed_topk_current_observation_budget5_v0"


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


def gt(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and left_f > right_f)


def ge(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and left_f >= right_f)


def eq(left: object, right: object) -> bool:
    left_f = finite_float(left)
    right_f = finite_float(right)
    return bool(left_f is not None and right_f is not None and abs(left_f - right_f) < 1e-12)


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows}


def build_specificity_rows(task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in sorted(task_rows, key=lambda item: str(item.get("task_context_id"))):
        delta_sr = finite_float(row.get("h001_minus_task_agnostic_SR"))
        delta_spl = finite_float(row.get("h001_minus_task_agnostic_SPL"))
        delta_prev_sr = finite_float(row.get("h001_minus_previous_SR"))
        delta_prev_spl = finite_float(row.get("h001_minus_previous_SPL"))
        has_distinct_gain = bool(
            (delta_sr is not None and delta_sr > 0)
            or (delta_sr == 0 and delta_spl is not None and delta_spl > 0)
        )
        no_regression = bool(
            delta_sr is not None
            and delta_spl is not None
            and delta_sr >= 0
            and delta_spl >= 0
        )
        out.append(
            {
                "version": VERSION,
                "task_context_id": row.get("task_context_id"),
                "h001_SR": row.get("h001_SR"),
                "h001_SPL": row.get("h001_SPL"),
                "previous_h001_SR": row.get("previous_h001_SR"),
                "previous_h001_SPL": row.get("previous_h001_SPL"),
                "task_agnostic_SR": row.get("task_agnostic_SR"),
                "task_agnostic_SPL": row.get("task_agnostic_SPL"),
                "h001_minus_previous_SR": row.get("h001_minus_previous_SR"),
                "h001_minus_previous_SPL": row.get("h001_minus_previous_SPL"),
                "h001_minus_task_agnostic_SR": row.get("h001_minus_task_agnostic_SR"),
                "h001_minus_task_agnostic_SPL": row.get("h001_minus_task_agnostic_SPL"),
                "has_distinct_task_context_gain": has_distinct_gain,
                "no_regression_vs_task_agnostic": no_regression,
                "interpretation": interpret_specificity(delta_sr, delta_spl, delta_prev_sr, delta_prev_spl),
            }
        )
    return out


def interpret_specificity(
    delta_sr: float | None,
    delta_spl: float | None,
    delta_prev_sr: float | None,
    delta_prev_spl: float | None,
) -> str:
    if delta_sr == 0 and delta_spl == 0:
        if (delta_prev_sr is not None and delta_prev_sr > 0) or (delta_prev_spl is not None and delta_prev_spl > 0):
            return "repair_improves_previous_h001_but_task_context_is_indistinguishable_from_task_agnostic"
        return "task_context_is_indistinguishable_from_task_agnostic"
    if delta_sr is not None and delta_sr < 0:
        return "task_context_regresses_against_task_agnostic"
    if delta_sr is not None and delta_sr >= 0 and delta_spl is not None and delta_spl < 0:
        return "task_context_preserves_success_but_costs_efficiency"
    if (delta_sr is not None and delta_sr > 0) or (delta_spl is not None and delta_spl > 0):
        return "task_context_has_positive_specificity_signal"
    return "requires_manual_review"


def build_evidence_rows(
    coverage: dict[str, Any],
    specificity_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    scale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy = index_by(policy_rows, "policy_id")
    pair = index_by(pairwise_rows, "baseline_policy_id")
    source = {(row.get("policy_id"), row.get("boundary")): row for row in source_rows}
    scale = index_by(scale_rows, "gate_id")

    h001 = policy.get(H001_POLICY, {})
    task_agnostic = policy.get(TASK_AGNOSTIC_POLICY, {})
    detector_pair = pair.get(DETECTOR_POLICY, {})
    fixed_pair = pair.get(FIXED_POLICY, {})
    h001_source_gap = source.get((H001_POLICY, "source_gap"), {})
    task_source_gap = source.get((TASK_AGNOSTIC_POLICY, "source_gap"), {})

    all_context_distinct = all(bool(row["has_distinct_task_context_gain"]) for row in specificity_rows)
    any_context_distinct = any(bool(row["has_distinct_task_context_gain"]) for row in specificity_rows)
    all_no_regression = all(bool(row["no_regression_vs_task_agnostic"]) for row in specificity_rows)

    return [
        {
            "version": VERSION,
            "evidence_id": "m52_ready",
            "passed": coverage.get("status") == "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready",
            "evidence": f"M52 status `{coverage.get('status')}`.",
            "implication": "required_input_gate",
        },
        {
            "version": VERSION,
            "evidence_id": "within_h001_repair_positive",
            "passed": bool(scale.get("improves_previous_h001", {}).get("passed")),
            "evidence": f"H001 v2 SR/SPL {fmt(h001.get('SR'))}/{fmt(h001.get('SPL'))}; previous H001 improvement gate `{scale.get('improves_previous_h001', {}).get('passed')}`.",
            "implication": "keep_repaired_policy_as_internal_h001_variant",
        },
        {
            "version": VERSION,
            "evidence_id": "task_context_distinct_any",
            "passed": any_context_distinct,
            "evidence": "At least one task context must improve SR or SPL over task-agnostic source-diverse.",
            "implication": "minimum_signal_for_task_context_specificity",
        },
        {
            "version": VERSION,
            "evidence_id": "task_context_distinct_all",
            "passed": all_context_distinct,
            "evidence": "Every task context must improve SR or SPL over task-agnostic source-diverse for a broad task-context claim.",
            "implication": "required_for_human_intent_main_claim",
        },
        {
            "version": VERSION,
            "evidence_id": "no_task_context_regression",
            "passed": all_no_regression,
            "evidence": "H001 v2 has no SR/SPL regression against task-agnostic source-diverse in the three current task contexts.",
            "implication": "safe_to_keep_as_secondary_condition_but_not_main_claim",
        },
        {
            "version": VERSION,
            "evidence_id": "beats_task_agnostic_policy",
            "passed": gt(h001.get("SR"), task_agnostic.get("SR")) and ge(h001.get("SPL"), task_agnostic.get("SPL")),
            "evidence": f"H001 v2 SR/SPL {fmt(h001.get('SR'))}/{fmt(h001.get('SPL'))}; task-agnostic {fmt(task_agnostic.get('SR'))}/{fmt(task_agnostic.get('SPL'))}.",
            "implication": "required_before_claiming_task_conditioning_as_method_contribution",
        },
        {
            "version": VERSION,
            "evidence_id": "efficiency_not_worse_than_detector_fixed",
            "passed": ge(detector_pair.get("delta_SPL_mean"), 0.0) and ge(fixed_pair.get("delta_SPL_mean"), 0.0),
            "evidence": f"Delta SPL vs detector {fmt(detector_pair.get('delta_SPL_mean'))}; vs fixed {fmt(fixed_pair.get('delta_SPL_mean'))}.",
            "implication": "required_before_deployable_navigation_efficiency_claim",
        },
        {
            "version": VERSION,
            "evidence_id": "source_gap_task_context_gain",
            "passed": gt(h001_source_gap.get("SR"), task_source_gap.get("SR")),
            "evidence": f"H001 source-gap SR {fmt(h001_source_gap.get('SR'))}; task-agnostic source-gap SR {fmt(task_source_gap.get('SR'))}.",
            "implication": "required_before_claiming_task_context_helps_stale_source_gap",
        },
    ]


def build_boundary_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    passed = {row["evidence_id"]: bool(row["passed"]) for row in evidence_rows}
    return [
        {
            "version": VERSION,
            "claim_id": "within_h001_routine_fetch_repair",
            "supported": passed["within_h001_repair_positive"],
            "claim_boundary": "The safe source-diverse repair improves the previous H001 policy on this smoke denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_specificity",
            "supported": False,
            "claim_boundary": "No current task context improves SR or SPL over task-agnostic source-diverse; task context is indistinguishable in E008.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Structured task context is not natural-language intent and has no distinct navigation effect in E008.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_secondary_condition",
            "supported": passed["no_task_context_regression"],
            "claim_boundary": "Task context may remain as a reported condition or secondary ablation, but not as a main contribution.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_solved",
            "supported": False,
            "claim_boundary": "Source-gap recovery is partial and does not beat task-agnostic source-diverse.",
        },
        {
            "version": VERSION,
            "claim_id": "real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final real navigation SR/SPL remains blocked by task-agnostic equality, detector/fixed SPL loss, and weak source-gap recovery.",
        },
        {
            "version": VERSION,
            "claim_id": "scale_navigation_benchmark_now",
            "supported": False,
            "claim_boundary": "Do not scale E008 navigation runs until a distinct task-context/source-gap or efficiency-positive policy exists.",
        },
    ]


def build_route_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    passed = {row["evidence_id"]: bool(row["passed"]) for row in evidence_rows}
    return [
        {
            "version": VERSION,
            "route_id": "scale_navigation_benchmark_now",
            "selected": False,
            "score": -4,
            "reason": "M52 fails task-agnostic, SPL, and source-gap gates; broader scaling would amplify an unsupported claim.",
        },
        {
            "version": VERSION,
            "route_id": "repair_task_context_specificity_inside_e008",
            "selected": False,
            "score": -1,
            "reason": "The three current task contexts do not create distinct decisions; repairing specificity needs a new context-sensitive utility benchmark, not another E008 trajectory tweak.",
            "requires_new_benchmark": True,
        },
        {
            "version": VERSION,
            "route_id": "source_gap_candidate_generation_repair_next",
            "selected": False,
            "score": 1,
            "reason": "Source gap is a real blocker, but it is not task-context-specific and should be handled after the current navigation boundary is packaged.",
            "deferred_until_after_boundary_package": True,
        },
        {
            "version": VERSION,
            "route_id": "demote_task_context_and_package_boundary",
            "selected": True,
            "score": 4 if passed["no_task_context_regression"] else 2,
            "reason": "This preserves the within-H001 repair result while preventing a weak human/task-context claim.",
            "selected_next_unit": NEXT_UNIT,
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack_id": "remove_task_context",
            "risk": "A reviewer can remove task context and get identical E008 SR/SPL.",
            "defense": "Do not claim task-context specificity in E008; present it as a controlled condition or secondary ablation only.",
        },
        {
            "version": VERSION,
            "attack_id": "navigation_efficiency_loss",
            "risk": "Detector/fixed baselines have higher SPL despite lower SR.",
            "defense": "Report recovery and efficiency separately; do not claim deployable navigation improvement.",
        },
        {
            "version": VERSION,
            "attack_id": "source_gap_not_solved",
            "risk": "The central stale-memory challenge is source-gap recovery, where H001 remains weak.",
            "defense": "Keep source-gap rows as a failure boundary and require candidate-generation/source-expansion repair before scale.",
        },
        {
            "version": VERSION,
            "attack_id": "overfitting_to_small_hm3d_smoke",
            "risk": "The current E008 denominator is too small for final top-tier navigation claims.",
            "defense": "Use M53 as a stop boundary; run broader navigation only after the method beats strong baselines on smoke gates.",
        },
    ]


def write_report(
    coverage: dict[str, Any],
    specificity_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M53 Task-Context Specificity Boundary",
        "",
        "## Status",
        "",
        f"- Status: `{coverage['status']}`",
        f"- M52 status: `{coverage['m52_status']}`",
        f"- Selected route: `{coverage['selected_route']}`",
        f"- Selected next unit: `{coverage['selected_next_unit']}`",
        f"- Human intent main claim ready: `{str(coverage['human_intent_main_claim_ready']).lower()}`",
        f"- Real navigation `SR` / `SPL` ready: `{str(coverage['real_navigation_sr_spl_ready']).lower()}`",
        "",
        "## Task Context Specificity",
        "",
        "| Context | H001 SR | Task-Agnostic SR | Delta SR | H001 SPL | Task-Agnostic SPL | Delta SPL | Interpretation |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in specificity_rows:
        lines.append(
            "| "
            f"`{row['task_context_id']}` | {fmt(row.get('h001_SR'))} | {fmt(row.get('task_agnostic_SR'))} | "
            f"{fmt(row.get('h001_minus_task_agnostic_SR'))} | {fmt(row.get('h001_SPL'))} | "
            f"{fmt(row.get('task_agnostic_SPL'))} | {fmt(row.get('h001_minus_task_agnostic_SPL'))} | "
            f"{row['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Evidence Gates",
            "",
            "| Gate | Passed | Evidence | Implication |",
            "|---|---|---|---|",
        ]
    )
    for row in evidence_rows:
        lines.append(
            f"| `{row['evidence_id']}` | `{str(row['passed']).lower()}` | {row['evidence']} | {row['implication']} |"
        )

    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| Route | Selected | Score | Reason |",
            "|---|---|---:|---|",
        ]
    )
    for row in route_rows:
        lines.append(
            f"| `{row['route_id']}` | `{str(row['selected']).lower()}` | {row['score']} | {row['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "| Claim | Supported | Boundary |",
            "|---|---|---|",
        ]
    )
    for row in boundary_rows:
        lines.append(f"| `{row['claim_id']}` | `{str(row['supported']).lower()}` | {row['claim_boundary']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not continue E008 by merely tuning the current task-context rule.",
            "- Demote task context to a secondary condition for the current navigation evidence.",
            "- Preserve the within-H001 repair result, but do not use it as a human-intent or final navigation claim.",
            f"- Next unit: `{NEXT_UNIT}`.",
            "",
        ]
    )
    (ARTIFACT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m52_coverage = read_json(M52_DIR / "coverage.json")
    task_rows = read_jsonl(M52_DIR / "task_context_effect_rows.jsonl")
    policy_rows = read_jsonl(M52_DIR / "policy_result_rows.jsonl")
    pairwise_rows = read_jsonl(M52_DIR / "pairwise_decision_rows.jsonl")
    source_rows = read_jsonl(M52_DIR / "source_boundary_rows.jsonl")
    scale_rows = read_jsonl(M52_DIR / "scale_gate_rows.jsonl")

    if not m52_coverage:
        raise SystemExit("missing M52 coverage")
    if not task_rows or not policy_rows or not pairwise_rows or not source_rows or not scale_rows:
        raise SystemExit("missing M52 interpretation rows")

    specificity_rows = build_specificity_rows(task_rows)
    evidence_rows = build_evidence_rows(m52_coverage, specificity_rows, policy_rows, pairwise_rows, source_rows, scale_rows)
    boundary_rows = build_boundary_rows(evidence_rows)
    route_rows = build_route_rows(evidence_rows)
    reviewer_rows = build_reviewer_defense_rows()

    selected_route = next(row for row in route_rows if row["selected"])
    any_distinct = any(row["has_distinct_task_context_gain"] for row in specificity_rows)
    all_distinct = all(row["has_distinct_task_context_gain"] for row in specificity_rows)
    no_regression = all(row["no_regression_vs_task_agnostic"] for row in specificity_rows)

    m52_ready = m52_coverage.get("status") == "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready"
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if m52_ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m52_status": m52_coverage.get("status"),
        "task_context_rows": len(specificity_rows),
        "task_context_any_distinct_gain": any_distinct,
        "task_context_all_distinct_gain": all_distinct,
        "task_context_no_regression_vs_task_agnostic": no_regression,
        "evidence_gate_rows": len(evidence_rows),
        "evidence_gate_pass_rows": sum(1 for row in evidence_rows if row["passed"]),
        "route_rows": len(route_rows),
        "selected_route": selected_route["route_id"],
        "selected_next_unit": NEXT_UNIT,
        "scale_navigation_benchmark_now": False,
        "repair_task_context_inside_e008_now": False,
        "task_context_demoted_to_secondary": True,
        "human_intent_main_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "task_context_specificity_rows.jsonl", specificity_rows)
    write_jsonl(ARTIFACT_DIR / "specificity_evidence_gate_rows.jsonl", evidence_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_report(coverage, specificity_rows, evidence_rows, route_rows, boundary_rows)

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
