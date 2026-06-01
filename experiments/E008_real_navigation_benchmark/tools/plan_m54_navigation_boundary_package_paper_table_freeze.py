#!/usr/bin/env python3
"""Package the E008 navigation boundary and freeze paper-facing diagnostic rows."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M52_DIR = EXP_ROOT / "artifacts" / "E008-M52_routine_fetch_repair_result_interpretation_scale_decision_v0"
M53_DIR = EXP_ROOT / "artifacts" / "E008-M53_routine_fetch_task_context_specificity_boundary_next_route_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M54_navigation_boundary_package_paper_table_freeze_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M54_navigation_boundary_package_paper_table_freeze_v0"
)

VERSION = "e008_m54_navigation_boundary_package_paper_table_freeze_v0"
READY_STATUS = "e008_m54_navigation_boundary_package_paper_table_freeze_ready"
BLOCKED_STATUS = "e008_m54_navigation_boundary_package_paper_table_freeze_blocked"
NEXT_UNIT = "E008-M55 source-gap candidate-generation repair feasibility decision"

STATIC_POLICY = "static_stale_memory_top1_v0"
DETECTOR_POLICY = "detector_confidence_budget5_v0"
FIXED_POLICY = "fixed_topk_current_observation_budget5_v0"
SOURCE_CURRENT_POLICY = "source_diverse_current_observation_budget5_v1"
H001_PREV_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
TASK_AGNOSTIC_POLICY = "task_agnostic_source_diverse_budget5_v1"

POLICY_ORDER = [
    STATIC_POLICY,
    DETECTOR_POLICY,
    FIXED_POLICY,
    SOURCE_CURRENT_POLICY,
    H001_PREV_POLICY,
    TASK_AGNOSTIC_POLICY,
    H001_POLICY,
]

POLICY_META = {
    STATIC_POLICY: {
        "paper_label": "Static stale memory top-1",
        "claim_role": "lower_bound",
        "paper_use": "diagnostic_lower_bound",
    },
    DETECTOR_POLICY: {
        "paper_label": "Detector confidence budget-5",
        "claim_role": "current_observation_baseline",
        "paper_use": "diagnostic_baseline",
    },
    FIXED_POLICY: {
        "paper_label": "Fixed top-k current observation budget-5",
        "claim_role": "simple_current_observation_baseline",
        "paper_use": "diagnostic_baseline",
    },
    SOURCE_CURRENT_POLICY: {
        "paper_label": "Source-diverse current observation budget-5",
        "claim_role": "current_observation_diversity_baseline",
        "paper_use": "diagnostic_baseline",
    },
    H001_PREV_POLICY: {
        "paper_label": "H001 source-diverse budget-5 v1",
        "claim_role": "previous_h001_ablation",
        "paper_use": "diagnostic_ablation",
    },
    TASK_AGNOSTIC_POLICY: {
        "paper_label": "Task-agnostic source-diverse budget-5",
        "claim_role": "strong_context_ablation",
        "paper_use": "required_ablation",
    },
    H001_POLICY: {
        "paper_label": "H001 safe source-diverse budget-5 v2",
        "claim_role": "repaired_h001_diagnostic_method",
        "paper_use": "diagnostic_method_row_not_final_nav_claim",
    },
}


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: sanitize_json(row.get(key)) for key in fieldnames})


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows}


def source_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row.get("policy_id")), str(row.get("boundary"))): row for row in rows}


def pairwise_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("baseline_policy_id")): row for row in rows if row.get("method_policy_id") == H001_POLICY}


def build_paper_navigation_table_rows(
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy = index_by(policy_rows, "policy_id")
    source = source_index(source_rows)
    pair = pairwise_index(pairwise_rows)
    rows: list[dict[str, Any]] = []

    for order, policy_id in enumerate(POLICY_ORDER, start=1):
        row = policy.get(policy_id, {})
        source_ready = source.get((policy_id, "source_ready"), {})
        source_gap = source.get((policy_id, "source_gap"), {})
        meta = POLICY_META[policy_id]
        current = {
            "version": VERSION,
            "table_id": "navigation_smoke_diagnostic_table_v0",
            "table_order": order,
            "policy_id": policy_id,
            "paper_label": meta["paper_label"],
            "claim_role": meta["claim_role"],
            "paper_use": meta["paper_use"],
            "include_in_diagnostic_table": True,
            "include_in_final_main_navigation_table": False,
            "rows": row.get("scan_task_policy_rows"),
            "success_rows": row.get("success_rows"),
            "SR": row.get("SR"),
            "SPL": row.get("SPL"),
            "PathLengthM_mean": row.get("PathLengthM_mean"),
            "CandidateVisits_mean": row.get("CandidateVisits_mean"),
            "OldLocationDeadEndCostM_mean": row.get("OldLocationDeadEndCostM_mean"),
            "source_ready_SR": source_ready.get("SR"),
            "source_ready_SPL": source_ready.get("SPL"),
            "source_gap_SR": source_gap.get("SR"),
            "source_gap_SPL": source_gap.get("SPL"),
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": row.get(
                "uses_objectnav_eval_goal_or_viewpoint_for_policy"
            ),
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": row.get(
                "uses_objectnav_eval_goal_or_viewpoint_for_metric"
            ),
            "supports_final_navigation_claim": False,
            "claim_boundary": "HM3D_ObjectNav_Habitat_trajectory_smoke_only",
        }
        if policy_id == H001_POLICY:
            for baseline_id in [
                STATIC_POLICY,
                DETECTOR_POLICY,
                FIXED_POLICY,
                SOURCE_CURRENT_POLICY,
                H001_PREV_POLICY,
                TASK_AGNOSTIC_POLICY,
            ]:
                pair_row = pair.get(baseline_id, {})
                suffix = baseline_id.replace("_budget5_v0", "").replace("_budget5_v1", "").replace("_top1_v0", "")
                current[f"delta_SR_vs_{suffix}"] = pair_row.get("delta_SR_mean")
                current[f"delta_SPL_vs_{suffix}"] = pair_row.get("delta_SPL_mean")
        rows.append(current)
    return rows


def build_table_freeze_rows(table_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "table_id": "navigation_smoke_diagnostic_table_v0",
            "frozen": True,
            "row_count": len(table_rows),
            "paper_use": "diagnostic_or_appendix_table",
            "reason": "Rows are leakage-safe Habitat trajectory smoke results, but they do not support final navigation improvement.",
            "required_before_main_table": "source-gap repair plus efficiency-positive result against detector/fixed and task-agnostic baselines.",
        },
        {
            "version": VERSION,
            "table_id": "main_real_navigation_sr_spl_table",
            "frozen": False,
            "row_count": 0,
            "paper_use": "blocked_main_table",
            "reason": "H001 v2 ties task-agnostic source-diverse, loses SPL to detector/fixed baselines, and has weak source-gap recovery.",
            "required_before_main_table": "scaled HM3D/OVON-style execution with strong baselines, repeated splits, and positive SR/SPL gates.",
        },
        {
            "version": VERSION,
            "table_id": "task_context_main_effect_table",
            "frozen": False,
            "row_count": 0,
            "paper_use": "blocked_main_ablation",
            "reason": "Task-context distinct gain is 0/3 contexts in M53.",
            "required_before_main_table": "a benchmark where task utility changes the optimal re-observation or visit decision beyond task-agnostic trust.",
        },
        {
            "version": VERSION,
            "table_id": "source_gap_failure_boundary_table",
            "frozen": True,
            "row_count": 7,
            "paper_use": "failure_analysis_or_boundary_table",
            "reason": "Source-gap rows identify the next repair target and prevent overclaiming.",
            "required_before_main_table": "candidate generation or source expansion that improves source-gap SR over task-agnostic source-diverse.",
        },
    ]


def build_allowed_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "e008_leakage_safe_navigation_smoke",
            "supported": True,
            "paper_sentence": "E008 provides a leakage-safe `HM3D ObjectNav` + `Habitat` trajectory smoke table for comparing stale, current-observation, task-agnostic, and H001 policies.",
            "boundary": "diagnostic trajectory smoke only, not final benchmark evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "within_h001_repair_positive",
            "supported": True,
            "paper_sentence": "The safe source-diverse H001 repair improves the previous H001 variant on the current smoke denominator.",
            "boundary": "within-H001 repair claim only.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_recovers_static_and_some_current_source_failures",
            "supported": True,
            "paper_sentence": "H001 v2 improves `SR` over static stale memory and source-diverse current observation in the current diagnostic setup.",
            "boundary": "not an overall navigation superiority claim because `SPL` and task-agnostic gates fail.",
        },
        {
            "version": VERSION,
            "claim_id": "task_context_secondary_condition",
            "supported": True,
            "paper_sentence": "Structured task context can be kept as a secondary condition in E008, but not as a main contribution.",
            "boundary": "no distinct gain over task-agnostic source-diverse in M53.",
        },
    ]


def build_blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl_improvement",
            "supported": False,
            "blocked_by": "task-agnostic equality, detector/fixed SPL loss, weak source-gap recovery, and small smoke denominator.",
            "required_evidence": "scaled Habitat navigation benchmark with H001 improving both `SR` and `SPL` over detector/fixed/current-source and task-agnostic baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "deployable_search_or_navigation_policy",
            "supported": False,
            "blocked_by": "current result is a diagnostic policy table, not a robust deployable planner.",
            "required_evidence": "budgeted policy that survives source gaps, observation noise, path-cost stress, and heldout scene/task splits.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_contribution",
            "supported": False,
            "blocked_by": "structured task context has no distinct `SR`/`SPL` gain over task-agnostic source-diverse in E008.",
            "required_evidence": "task utility or intent contexts that change the optimal memory-trust/re-observation decision with positive task-specific metrics.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_solved",
            "supported": False,
            "blocked_by": "H001 source-gap `SR` is 0.333333 and ties task-agnostic source-diverse.",
            "required_evidence": "source-gap-specific candidate generation or map expansion that beats task-agnostic source-diverse.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_rgbd_open_vocab_robustness",
            "supported": False,
            "blocked_by": "E008 uses staged detector/open-vocabulary candidates from prior diagnostics and does not prove final real RGB-D robustness.",
            "required_evidence": "full detector/proposal route with heldout splits, false-positive control, external proposal baselines, and navigation-connected metrics.",
        },
        {
            "version": VERSION,
            "claim_id": "broad_hm3d_ovon_goat_generalization",
            "supported": False,
            "blocked_by": "current E008 denominator is a small controlled `HM3D ObjectNav` smoke.",
            "required_evidence": "multiple scene groups, label groups, splits, and external navigation/search baselines.",
        },
    ]


def build_claim_boundary_rows(
    allowed_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in allowed_rows:
        out.append(
            {
                "version": VERSION,
                "claim_id": row["claim_id"],
                "supported": True,
                "claim_boundary": row["boundary"],
                "paper_sentence": row["paper_sentence"],
            }
        )
    for row in blocked_rows:
        out.append(
            {
                "version": VERSION,
                "claim_id": row["claim_id"],
                "supported": False,
                "claim_boundary": row["blocked_by"],
                "required_evidence": row["required_evidence"],
            }
        )
    return out


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack_id": "task_context_can_be_removed",
            "risk": "A reviewer can remove structured task context and obtain identical E008 `SR`/`SPL`.",
            "defense_or_fix": "Demote task context to a secondary condition in E008; require a utility-sensitive benchmark before any human intent main claim.",
        },
        {
            "version": VERSION,
            "attack_id": "spl_loss_against_detector_fixed",
            "risk": "H001 v2 has higher `SR` but lower `SPL` than detector/fixed baselines.",
            "defense_or_fix": "Report `SR` and `SPL` separately as a recovery/efficiency tradeoff; do not claim deployable navigation improvement.",
        },
        {
            "version": VERSION,
            "attack_id": "source_gap_not_solved",
            "risk": "The central dynamic-memory setting is source gap, but H001 source-gap recovery is partial and task-agnostic-equal.",
            "defense_or_fix": "Use source-gap rows as the next technical target and require candidate-generation repair before scale-up.",
        },
        {
            "version": VERSION,
            "attack_id": "small_hm3d_smoke_denominator",
            "risk": "The current denominator is too small for a top-tier navigation claim.",
            "defense_or_fix": "Freeze the table as diagnostic evidence only; scaled runs wait for stronger smoke gates.",
        },
        {
            "version": VERSION,
            "attack_id": "objectnav_goal_leakage",
            "risk": "A reviewer may suspect policy access to eval goal/viewpoint.",
            "defense_or_fix": "Keep policy and metric input fields explicit: eval goal/viewpoint is metric-only and never a policy input.",
        },
        {
            "version": VERSION,
            "attack_id": "not_real_robot_navigation",
            "risk": "`Habitat` execution is simulator navigation, not a physical robot deployment.",
            "defense_or_fix": "Call it `HM3D ObjectNav` simulator trajectory evidence; physical robot or broader embodied claims require later system experiments.",
        },
    ]


def build_freeze_gate_rows(m52: dict[str, Any], m53: dict[str, Any], table_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m52_input_ready",
            "passed": m52.get("status") == "e008_m52_routine_fetch_repair_result_interpretation_scale_decision_ready",
            "evidence": f"M52 status `{m52.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "m53_input_ready",
            "passed": m53.get("status") == "e008_m53_routine_fetch_task_context_specificity_boundary_ready",
            "evidence": f"M53 status `{m53.get('status')}`.",
        },
        {
            "version": VERSION,
            "gate_id": "diagnostic_table_rows_present",
            "passed": len(table_rows) == len(POLICY_ORDER),
            "evidence": f"Diagnostic navigation rows {len(table_rows)} / {len(POLICY_ORDER)}.",
        },
        {
            "version": VERSION,
            "gate_id": "task_context_demoted",
            "passed": bool(m53.get("task_context_demoted_to_secondary")),
            "evidence": f"Task context demoted to secondary: {m53.get('task_context_demoted_to_secondary')}.",
        },
        {
            "version": VERSION,
            "gate_id": "final_claims_blocked",
            "passed": not any(
                bool(m53.get(key))
                for key in [
                    "real_navigation_sr_spl_ready",
                    "human_intent_main_claim_ready",
                    "deployable_search_policy_ready",
                    "final_real_rgbd_open_vocab_robustness_ready",
                ]
            ),
            "evidence": "Final navigation, human intent, deployable policy, and RGB-D/open-vocabulary robustness claims remain false.",
        },
        {
            "version": VERSION,
            "gate_id": "source_gap_next_route_identified",
            "passed": True,
            "evidence": f"Selected next technical unit is `{NEXT_UNIT}`.",
        },
    ]


def build_next_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "freeze_e008_navigation_boundary",
            "selected": True,
            "reason": "The current E008 evidence is useful as a diagnostic navigation table but unsafe as a final claim.",
        },
        {
            "version": VERSION,
            "route_id": "scale_navigation_benchmark_now",
            "selected": False,
            "reason": "Scaling now would amplify task-agnostic equality, detector/fixed SPL loss, and source-gap weakness.",
        },
        {
            "version": VERSION,
            "route_id": "repair_human_intent_inside_e008_now",
            "selected": False,
            "reason": "Human/task-context specificity needs a new utility-sensitive benchmark, not another E008 trajectory tweak.",
        },
        {
            "version": VERSION,
            "route_id": "source_gap_candidate_generation_repair_next",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "After boundary packaging, source-gap candidate generation is the most direct blocker for a stronger navigation claim.",
        },
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    m52: dict[str, Any],
    m53: dict[str, Any],
    table_rows: list[dict[str, Any]],
    freeze_rows: list[dict[str, Any]],
    allowed_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    h001 = next(row for row in table_rows if row["policy_id"] == H001_POLICY)
    task_agnostic = next(row for row in table_rows if row["policy_id"] == TASK_AGNOSTIC_POLICY)
    detector = next(row for row in table_rows if row["policy_id"] == DETECTOR_POLICY)
    lines = [
        "# E008-M54 Navigation Boundary Package",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M52 input status: `{m52.get('status')}`.",
        f"- M53 input status: `{m53.get('status')}`.",
        f"- Diagnostic navigation table rows: {len(table_rows)}.",
        f"- H001 v2 `SR` / `SPL`: {fmt(h001.get('SR'))} / {fmt(h001.get('SPL'))}.",
        f"- Task-agnostic source-diverse `SR` / `SPL`: {fmt(task_agnostic.get('SR'))} / {fmt(task_agnostic.get('SPL'))}.",
        f"- Detector confidence `SR` / `SPL`: {fmt(detector.get('SR'))} / {fmt(detector.get('SPL'))}.",
        f"- H001 v2 source-gap `SR`: {fmt(h001.get('source_gap_SR'))}.",
        "",
        "## Paper Table Freeze",
        "",
    ]
    for row in freeze_rows:
        lines.append(
            f"- `{row['table_id']}`: frozen `{row['frozen']}`, use `{row['paper_use']}`. Reason: {row['reason']}"
        )
    lines.extend(
        [
            "",
            "## Allowed Claims",
            "",
        ]
    )
    for row in allowed_rows:
        lines.append(f"- `{row['claim_id']}`: {row['boundary']}")
    lines.extend(
        [
            "",
            "## Blocked Claims",
            "",
        ]
    )
    for row in blocked_rows:
        lines.append(f"- `{row['claim_id']}`: blocked by {row['blocked_by']}")
    lines.extend(
        [
            "",
            "## Next Route",
            "",
        ]
    )
    for row in route_rows:
        marker = "selected" if row["selected"] else "not selected"
        lines.append(f"- `{row['route_id']}`: {marker}. {row['reason']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "M54 freezes E008 as diagnostic navigation evidence. It does not support final real navigation `SR` / `SPL`, human intent as a main contribution, deployable search policy, or final real RGB-D/open-vocabulary robustness.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m52 = read_json(M52_DIR / "coverage.json")
    m53 = read_json(M53_DIR / "coverage.json")
    policy_rows = read_jsonl(M52_DIR / "policy_result_rows.jsonl")
    pairwise_rows = read_jsonl(M52_DIR / "pairwise_decision_rows.jsonl")
    source_rows = read_jsonl(M52_DIR / "source_boundary_rows.jsonl")
    task_context_rows = read_jsonl(M53_DIR / "task_context_specificity_rows.jsonl")

    table_rows = build_paper_navigation_table_rows(policy_rows, source_rows, pairwise_rows)
    freeze_rows = build_table_freeze_rows(table_rows)
    allowed_rows = build_allowed_claim_rows()
    blocked_rows = build_blocked_claim_rows()
    claim_rows = build_claim_boundary_rows(allowed_rows, blocked_rows)
    reviewer_rows = build_reviewer_defense_rows()
    gate_rows = build_freeze_gate_rows(m52, m53, table_rows)
    route_rows = build_next_route_rows()
    all_gates_pass = all(bool(row["passed"]) for row in gate_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if all_gates_pass else BLOCKED_STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m52_status": m52.get("status"),
        "m53_status": m53.get("status"),
        "paper_navigation_table_rows": len(table_rows),
        "paper_table_freeze_rows": len(freeze_rows),
        "allowed_claim_rows": len(allowed_rows),
        "blocked_claim_rows": len(blocked_rows),
        "reviewer_defense_rows": len(reviewer_rows),
        "freeze_gate_rows": len(gate_rows),
        "freeze_gate_pass_rows": sum(1 for row in gate_rows if row["passed"]),
        "task_context_rows": len(task_context_rows),
        "task_context_demoted_to_secondary": bool(m53.get("task_context_demoted_to_secondary")),
        "diagnostic_navigation_table_frozen": True,
        "main_navigation_table_frozen": False,
        "scale_navigation_benchmark_now": False,
        "human_intent_main_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "selected_route": "source_gap_candidate_generation_repair_next_after_boundary_freeze",
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "paper_navigation_table_rows.jsonl", table_rows)
    write_csv(ARTIFACT_DIR / "paper_navigation_table_rows.csv", table_rows)
    write_jsonl(ARTIFACT_DIR / "paper_table_freeze_rows.jsonl", freeze_rows)
    write_jsonl(ARTIFACT_DIR / "allowed_claim_rows.jsonl", allowed_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_claim_rows.jsonl", blocked_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "freeze_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "next_route_rows.jsonl", route_rows)
    write_report(
        ARTIFACT_DIR / "report.md",
        coverage,
        m52,
        m53,
        table_rows,
        freeze_rows,
        allowed_rows,
        blocked_rows,
        route_rows,
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "paper_navigation_table_rows.jsonl", table_rows)
    write_jsonl(DATA_OUT_DIR / "next_route_rows.jsonl", route_rows)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
