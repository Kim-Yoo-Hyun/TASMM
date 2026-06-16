#!/usr/bin/env python3
"""Freeze the M200 additive source-pool candidate-union repair contract."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m200_additive_source_pool_candidate_union_repair_contract_v0"
READY_STATUS = "e008_m200_additive_source_pool_candidate_union_repair_contract_ready"
NEXT_UNIT = "E008-M201 additive source-pool candidate-union row materialization"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M200_additive_source_pool_candidate_union_repair_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M200_additive_source_pool_candidate_union_repair_contract_v0"
)

M70_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
)
M196_DIR = EXP_ROOT / "artifacts" / "E008-M196_source_pool_scale_candidate_visit_order_path_materialization_v0"
M197_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
M199_DIR = EXP_ROOT / "artifacts" / "E008-M199_source_pool_scale_failure_decomposition_repair_decision_v0"

PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SELECTED_POLICY = "additive_union_candidate_pool_with_source_gap_guard_v0"
SOURCE_POOL_REPLACEMENT_NEGATIVE = "source_pool_replacement_detector_confidence_reachable_subset_v0"
BASELINE_ONLY_ABLATION = "no_source_pool_detector_confidence_reachable_subset_v0"
UNGUARDED_UNION_ABLATION = "additive_union_unguarded_confidence_sort_v0"
BAND_INTERLEAVE_ABLATION = "additive_union_confidence_band_interleave_v0"


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


def policy_rows_from_scan_metrics(path: Path, metric_scope: str, policy_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in read_jsonl(path)
        if row.get("metric_scope") == metric_scope and row.get("policy_id") == policy_id
    ]


def build_method_contract_rows(m199_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": SELECTED_POLICY,
            "policy_role": "selected_repair_policy",
            "method_form": "preserve no-source detector-confidence candidate order, then append source-pool candidates as additive evidence under fixed source-gap and duplicate guards",
            "protected_base_policy_id": PROTECTED_BASELINE,
            "negative_replacement_policy_id": SOURCE_POOL_REPLACEMENT_NEGATIVE,
            "failure_diagnosis_used": "M199: source-pool adds 2 unique recoveries but loses 9 no-source baseline successes, including 7 source-gap/no-detector rows",
            "why_this_form_is_forced": "If source-pool replaces the no-source candidate pool, it deletes reliable baseline evidence; if it is additive, it can preserve baseline successes while exposing unique source-pool recoveries.",
            "baseline_prefix_preserved": True,
            "source_pool_can_replace_baseline_candidate": False,
            "source_gap_no_detector_policy": "fallback_to_no_source_baseline",
            "deduplicate_policy": "same episode, category, rounded snapped xz coordinate, and raw candidate uid if available",
            "ranking_rule": "baseline candidates keep original protected order; source-pool candidates are appended by detector confidence then path-ready cost",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "m199_lost_baseline_success_rows": m199_coverage.get("source_pool_lost_baseline_success_rows"),
            "m199_unique_recovery_rows": m199_coverage.get("source_pool_unique_recovery_rows"),
        },
        {
            "version": VERSION,
            "row_type": "method_contract",
            "policy_id": PROTECTED_BASELINE,
            "policy_role": "protected_baseline",
            "method_form": "no-source detector-confidence reachable subset",
            "protected_base_policy_id": PROTECTED_BASELINE,
            "negative_replacement_policy_id": None,
            "failure_diagnosis_used": "M70 remains stronger than M197 replacement source-pool on proxy SR/SPL",
            "why_this_form_is_forced": "M200 must prove any candidate-generation change does not erase this baseline.",
            "baseline_prefix_preserved": True,
            "source_pool_can_replace_baseline_candidate": False,
            "source_gap_no_detector_policy": "not_applicable",
            "deduplicate_policy": "none",
            "ranking_rule": "detector-confidence order",
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
        },
    ]


def build_candidate_union_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "field": "candidate_source_family",
            "required": True,
            "allowed_values": ["no_source_detector", "source_pool_detector"],
            "policy_use": "select baseline preservation and additive source-pool rows",
        },
        {
            "version": VERSION,
            "field": "base_candidate_rank",
            "required": True,
            "allowed_values": ["integer for no_source_detector, null for source_pool_detector"],
            "policy_use": "audit that no-source baseline prefix is preserved",
        },
        {
            "version": VERSION,
            "field": "union_rank",
            "required": True,
            "allowed_values": ["integer"],
            "policy_use": "M201 materialized visit order",
        },
        {
            "version": VERSION,
            "field": "source_gap_after_m195",
            "required": True,
            "allowed_values": ["boolean"],
            "policy_use": "ensure source-gap/no-detector rows fall back to baseline rather than replacement",
        },
        {
            "version": VERSION,
            "field": "union_action",
            "required": True,
            "allowed_values": ["keep_baseline", "append_source_pool", "drop_duplicate_source_pool"],
            "policy_use": "explain how each candidate enters or does not enter the additive pool",
        },
        {
            "version": VERSION,
            "field": "uses_objectnav_eval_goal_or_viewpoint_for_policy",
            "required": True,
            "allowed_values": [False],
            "policy_use": "leakage audit",
        },
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    allowed = [
        ("proposal_uid", "candidate identity"),
        ("raw_candidate_uid", "dedup candidate identity"),
        ("adapter_episode_id", "episode grouping"),
        ("object_category", "query category"),
        ("label_canonical", "candidate label compatibility"),
        ("confidence", "current evidence reliability"),
        ("candidate_snapped_position_m", "dedup and path location"),
        ("source_to_candidate_path_cost_m", "append-order tie-break"),
        ("path_ready", "hard feasibility guard"),
        ("candidate_source_family", "baseline vs source-pool provenance"),
        ("source_gap_after_m195", "fallback guard"),
    ]
    blocked = [
        ("eval_goal_position", "ObjectNav goal is metric-only"),
        ("eval_first_viewpoint_position", "ObjectNav viewpoint is metric-only"),
        ("candidate_to_nearest_eval_viewpoint_xz_m", "metric-only distance"),
        ("primary_eval_hit", "success label leakage"),
        ("primary_spl_proxy", "metric output"),
        ("best_any_viewpoint_xz_m", "metric-only diagnostic"),
    ]
    rows: list[dict[str, Any]] = []
    for field, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": True,
                "blocked_for_policy": False,
                "reason": reason,
            }
        )
    for field, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "allowed_for_policy": False,
                "blocked_for_policy": True,
                "reason": reason,
            }
        )
    return rows


def build_baseline_protection_rows(m70_rows: list[dict[str, Any]], m197_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    episode_ids = sorted({str(row.get("adapter_episode_id")) for row in m70_rows} | {str(row.get("adapter_episode_id")) for row in m197_rows})
    m70_by_episode = {str(row.get("adapter_episode_id")): row for row in m70_rows}
    m197_by_episode = {str(row.get("adapter_episode_id")): row for row in m197_rows}
    out: list[dict[str, Any]] = []
    for episode_id in episode_ids:
        baseline = m70_by_episode.get(episode_id, {})
        source_pool = m197_by_episode.get(episode_id, {})
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": baseline.get("scan_id") or source_pool.get("scan_id"),
                "scene_key": baseline.get("scene_key") or source_pool.get("scene_key"),
                "object_category": baseline.get("object_category") or source_pool.get("object_category"),
                "baseline_candidate_rows": baseline.get("candidate_rows", 0),
                "source_pool_candidate_rows": source_pool.get("candidate_rows", 0),
                "baseline_primary_hit": bool(baseline.get("primary_hit")),
                "source_pool_replacement_primary_hit": bool(source_pool.get("primary_hit")),
                "m201_required_union_candidate_rows_min": int(baseline.get("candidate_rows") or 0),
                "m201_required_baseline_prefix_mutation_count": 0,
                "m201_required_baseline_candidate_loss_count": 0,
                "source_gap_fallback_required": not bool(source_pool.get("candidate_rows")),
                "reason": "M201 must not lose no-source detector candidates when adding source-pool evidence.",
            }
        )
    return out


def build_policy_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_id": SELECTED_POLICY,
            "role": "selected_repair",
            "candidate_pool": "no_source_detector candidates union source_pool_detector candidates",
            "ranking": "baseline protected prefix, then appended source-pool detector confidence with path-ready tie-break",
            "positive_claim_gate": "must improve or at least preserve protected SR and improve SPL or recovery count in M202 before trajectory execution",
        },
        {
            "version": VERSION,
            "policy_id": BASELINE_ONLY_ABLATION,
            "role": "required_baseline",
            "candidate_pool": "no_source_detector candidates only",
            "ranking": "detector confidence reachable subset",
            "positive_claim_gate": "reference row; not a method claim",
        },
        {
            "version": VERSION,
            "policy_id": SOURCE_POOL_REPLACEMENT_NEGATIVE,
            "role": "closed_negative_baseline",
            "candidate_pool": "source_pool_detector candidates only",
            "ranking": "detector confidence reachable subset",
            "positive_claim_gate": "closed by M199 negative evidence",
        },
        {
            "version": VERSION,
            "policy_id": UNGUARDED_UNION_ABLATION,
            "role": "ablation",
            "candidate_pool": "union candidates",
            "ranking": "global confidence sort without baseline prefix guard",
            "positive_claim_gate": "expected to expose why baseline protection is needed",
        },
        {
            "version": VERSION,
            "policy_id": BAND_INTERLEAVE_ABLATION,
            "role": "optional_tradeoff_ablation",
            "candidate_pool": "union candidates",
            "ranking": "interleave source-pool rows only within a fixed confidence band",
            "positive_claim_gate": "may improve SPL but cannot be selected unless it preserves baseline SR",
        },
    ]


def build_m201_gate_rows(m199_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m201_materialization_required",
            "ready_for_m201": True,
            "required_input_artifacts": [
                "M70 no-source detector policy rows",
                "M196 source-pool visit-order rows",
                "M197 source-pool goal metric rows",
                "M199 failure decomposition rows",
            ],
            "required_output_rows": [
                "union_candidate_rows.jsonl",
                "union_policy_rows.jsonl",
                "baseline_prefix_audit_rows.jsonl",
                "dedup_audit_rows.jsonl",
                "leakage_audit_rows.jsonl",
            ],
            "minimum_denominator_rows": m199_coverage.get("denominator_rows"),
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "trajectory_execution_allowed_after_m201": False,
        },
        {
            "version": VERSION,
            "gate_id": "m202_proxy_eval_required_before_trajectory",
            "ready_for_m201": False,
            "required_condition": "M201 materializes union rows with leakage/pass and no baseline candidate loss",
            "required_metric_gate": "M202 must compare selected repair to no-source detector baseline on the same 30 rows before Docker trajectory execution",
            "trajectory_execution_allowed_after_m201": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_additive_union_contract",
            "supported": True,
            "claim_boundary": "M200 supports a repair contract: source-pool candidates may be added to, but not replace, the protected no-source detector candidate pool.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repaired_policy_performance",
            "supported": False,
            "claim_boundary": "M200 does not materialize repaired rows or evaluate proxy SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M200 does not execute Habitat trajectories.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_m201_additive_candidate_union_row_materialization",
            "selected": True,
            "selected_next_unit": NEXT_UNIT,
            "reason": "The M199 negative replacement failure is now converted into a leakage-safe additive candidate-union contract.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "attack": "Why not simply use source-pool candidates instead of the detector baseline?",
            "defense": "M199 shows replacement loses 9 no-source baseline successes, so replacement is empirically weaker and conceptually wrong.",
        },
        {
            "version": VERSION,
            "attack": "Is additive union a posthoc fix after seeing targets?",
            "defense": "M200 fixes allowed inputs, baseline prefix audits, fixed denominator, and no threshold changes before M201/M202 evaluation.",
        },
        {
            "version": VERSION,
            "attack": "Does M200 prove navigation improvement?",
            "defense": "No. M200 is a contract only; repaired performance must pass M202 proxy and later Docker trajectory gates.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    method_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return f"""# E008-M200 Additive Source-Pool Candidate-Union Repair Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Selected policy: `{coverage['selected_policy_id']}`.
- Protected baseline: `{coverage['protected_baseline_policy_id']}`.
- Negative replacement policy: `{coverage['negative_replacement_policy_id']}`.
- Denominator rows: {coverage['denominator_rows']}.
- M199 source-pool unique recovery rows: {coverage['m199_source_pool_unique_recovery_rows']}.
- M199 lost baseline success rows: {coverage['m199_source_pool_lost_baseline_success_rows']}.
- M199 source-gap/no-detector loss rows: {coverage['m199_lost_baseline_source_gap_no_detector_candidate_rows']}.
- M201 materialization ready: {coverage['m201_materialization_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Method Contract

{markdown_table(method_rows, ['policy_id', 'policy_role', 'method_form', 'baseline_prefix_preserved', 'source_pool_can_replace_baseline_candidate', 'source_gap_no_detector_policy'])}

## Policy/Ablation Contract

{markdown_table(policy_rows, ['policy_id', 'role', 'candidate_pool', 'ranking'])}

## Next Gate

{markdown_table(gate_rows, ['gate_id', 'ready_for_m201', 'trajectory_execution_allowed_after_m201'])}

## Interpretation

M200 converts the M199 failure diagnosis into a stricter method contract. Source-pool evidence is allowed only as additive candidate evidence. The no-source detector-confidence candidate pool remains the protected base, the 30-row denominator and primary metric stay fixed, and M201 must prove that materialization does not drop or reorder protected baseline candidates before any proxy or trajectory claim is attempted.
"""


def main() -> None:
    m70_coverage = read_json(M70_DATA_DIR / "coverage.json")
    m196_coverage = read_json(M196_DIR / "coverage.json")
    m197_coverage = read_json(M197_DIR / "coverage.json")
    m199_coverage = read_json(M199_DIR / "coverage.json")
    if not m70_coverage:
        raise SystemExit(f"missing {M70_DATA_DIR / 'coverage.json'}")
    if not m196_coverage:
        raise SystemExit(f"missing {M196_DIR / 'coverage.json'}")
    if not m197_coverage:
        raise SystemExit(f"missing {M197_DIR / 'coverage.json'}")
    if not m199_coverage:
        raise SystemExit(f"missing {M199_DIR / 'coverage.json'}")

    m70_policy_rows = policy_rows_from_scan_metrics(
        M70_DATA_DIR / "policy_goal_metric_rows.jsonl",
        "scan_policy",
        PROTECTED_BASELINE,
    )
    m197_policy_rows = policy_rows_from_scan_metrics(
        M197_DIR / "source_pool_scale_scan_goal_metric_rows.jsonl",
        "source_pool_scale_scan_policy_goal_eval",
        PROTECTED_BASELINE,
    )
    if not m70_policy_rows:
        raise SystemExit("missing M70 protected baseline rows")
    if not m197_policy_rows:
        raise SystemExit("missing M197 source-pool protected rows")

    method_rows = build_method_contract_rows(m199_coverage)
    schema_rows = build_candidate_union_schema_rows()
    input_rows = build_input_guard_rows()
    baseline_rows = build_baseline_protection_rows(m70_policy_rows, m197_policy_rows)
    policy_rows = build_policy_contract_rows()
    gate_rows = build_m201_gate_rows(m199_coverage)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows()
    reviewer_rows = build_reviewer_defense_rows()

    baseline_loss_required_zero = all(row["m201_required_baseline_candidate_loss_count"] == 0 for row in baseline_rows)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m70_status": m70_coverage.get("status"),
        "m196_status": m196_coverage.get("status"),
        "m197_status": m197_coverage.get("status"),
        "m199_status": m199_coverage.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "negative_replacement_policy_id": SOURCE_POOL_REPLACEMENT_NEGATIVE,
        "denominator_rows": m199_coverage.get("denominator_rows"),
        "m70_policy_rows": len(m70_policy_rows),
        "m197_policy_rows": len(m197_policy_rows),
        "m199_source_pool_unique_recovery_rows": m199_coverage.get("source_pool_unique_recovery_rows"),
        "m199_source_pool_lost_baseline_success_rows": m199_coverage.get("source_pool_lost_baseline_success_rows"),
        "m199_lost_baseline_source_gap_no_detector_candidate_rows": m199_coverage.get(
            "lost_baseline_source_gap_no_detector_candidate_rows"
        ),
        "m201_materialization_ready": True,
        "baseline_prefix_audit_required": True,
        "baseline_candidate_loss_required_zero": baseline_loss_required_zero,
        "dedup_audit_required": True,
        "leakage_audit_required": True,
        "posthoc_threshold_change_allowed": False,
        "denominator_change_allowed": False,
        "trajectory_execution_promoted": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "method_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "method_contract_rows.jsonl", method_rows)
        write_jsonl(output_dir / "candidate_union_schema_rows.jsonl", schema_rows)
        write_jsonl(output_dir / "input_guard_rows.jsonl", input_rows)
        write_jsonl(output_dir / "baseline_protection_rows.jsonl", baseline_rows)
        write_jsonl(output_dir / "policy_contract_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "m201_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, method_rows, policy_rows, gate_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
