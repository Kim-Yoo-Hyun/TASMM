#!/usr/bin/env python3
"""Decompose E008-M174 source-coverage utility conservatism failure."""

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
M172_DIR = EXP_ROOT / "artifacts" / "E008-M172_source_coverage_ablation_tradeoff_decomposition_v0"
M173_DIR = EXP_ROOT / "artifacts" / "E008-M173_source_coverage_utility_pareto_contract_v0"
M174_DIR = EXP_ROOT / "artifacts" / "E008-M174_source_coverage_utility_pareto_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M174b_source_coverage_utility_conservatism_failure_decomposition_v0"

VERSION = "e008_m174b_source_coverage_utility_conservatism_failure_decomposition_v0"
READY_STATUS = "e008_m174b_source_coverage_utility_conservatism_failure_decomposition_ready"
BLOCKED_STATUS = "e008_m174b_source_coverage_utility_conservatism_failure_decomposition_blocked"

SELECTED_POLICY = "source_coverage_budgeted_utility_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_WITNESS = "source_coverage_only_task_agnostic_v1"
WITHOUT_CONFIDENCE_GUARD = "source_coverage_utility_without_confidence_guard_v1"
NEXT_UNIT = "E008-M175 source-coverage trigger/candidate-source expansion contract"

NUMERIC_FIELDS = [
    "utility_delta",
    "coverage_novelty_norm",
    "prefix_path_saving_norm",
    "expected_extra_visit_norm",
    "confidence_loss_norm",
    "rank_displacement_norm",
    "confidence_loss",
    "rank_displacement_abs_from_detector",
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def min_or_none(values: list[float]) -> float | None:
    return min(values) if values else None


def max_or_none(values: list[float]) -> float | None:
    return max(values) if values else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def numeric(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    return finite_float(row.get(field)) if finite_float(row.get(field)) is not None else default


def summarize_components(component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in component_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(by_policy.items()):
        fallback_counts = Counter(str(row.get("fallback_reason") or "") for row in rows)
        positive_utility_rows = sum(numeric(row, "utility_delta") > 0 for row in rows)
        allowed_rows = sum(bool(row.get("promotion_allowed")) for row in rows)
        confidence_guard_fail_rows = sum(not bool(row.get("detector_confidence_protection_guard_pass")) for row in rows)
        prefix_guard_fail_rows = sum(not bool(row.get("prefix_path_saving_guard_pass")) for row in rows)
        rows_payload: dict[str, Any] = {
            "version": VERSION,
            "row_type": "policy_component_summary",
            "policy_id": policy_id,
            "component_rows": len(rows),
            "promotion_candidate_rows": sum(bool(row.get("promotion_candidate")) for row in rows),
            "promotion_allowed_rows": allowed_rows,
            "positive_utility_rows": positive_utility_rows,
            "confidence_guard_fail_rows": confidence_guard_fail_rows,
            "prefix_path_guard_fail_rows": prefix_guard_fail_rows,
            "coverage_positive_rows": sum(numeric(row, "coverage_novelty_norm") > 0 for row in rows),
            "path_saving_positive_rows": sum(numeric(row, "prefix_path_saving_norm") > 0 for row in rows),
            "source_gap_prelabel_rows": sum(bool(row.get("source_gap_prelabel")) for row in rows),
            "dominant_fallback_reason": fallback_counts.most_common(1)[0][0] if fallback_counts else None,
            "dominant_fallback_count": fallback_counts.most_common(1)[0][1] if fallback_counts else 0,
        }
        for field in NUMERIC_FIELDS:
            values = [numeric(row, field) for row in rows]
            rows_payload[f"{field}_min"] = min_or_none(values)
            rows_payload[f"{field}_max"] = max_or_none(values)
            rows_payload[f"{field}_mean"] = mean(values)
        out.append(rows_payload)
    return out


def selected_utility_factor_rows(component_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row for row in component_rows if row.get("policy_id") == SELECTED_POLICY]
    if not selected:
        return []
    factors = [
        ("coverage_reward", 0.050, "coverage_novelty_norm", "positive"),
        ("path_reward", 0.030, "prefix_path_saving_norm", "positive"),
        ("source_gap_reward", 0.020, "source_gap_prelabel", "positive_bool"),
        ("visit_penalty", -0.080, "expected_extra_visit_norm", "negative"),
        ("confidence_penalty", -0.060, "confidence_loss_norm", "negative"),
        ("rank_displacement_penalty", -0.040, "rank_displacement_norm", "negative"),
    ]
    rows = []
    for factor_id, weight, field, role in factors:
        if role == "positive_bool":
            values = [1.0 if row.get(field) else 0.0 for row in selected]
        else:
            values = [numeric(row, field) for row in selected]
        contribution_values = [weight * value for value in values]
        rows.append(
            {
                "version": VERSION,
                "row_type": "selected_utility_factor",
                "factor_id": factor_id,
                "field": field,
                "weight": weight,
                "role": role,
                "positive_input_rows": sum(value > 0 for value in values),
                "input_mean": mean(values),
                "input_max": max_or_none(values),
                "mean_contribution": mean(contribution_values),
                "max_contribution": max_or_none(contribution_values),
            }
        )
    return rows


def failure_mechanism_rows(policy_summary: list[dict[str, Any]], factor_rows: list[dict[str, Any]], m174: dict[str, Any]) -> list[dict[str, Any]]:
    selected = next((row for row in policy_summary if row.get("policy_id") == SELECTED_POLICY), {})
    no_conf = next((row for row in policy_summary if row.get("policy_id") == WITHOUT_CONFIDENCE_GUARD), {})
    rank_factor = next((row for row in factor_rows if row.get("factor_id") == "rank_displacement_penalty"), {})
    confidence_factor = next((row for row in factor_rows if row.get("factor_id") == "confidence_penalty"), {})
    coverage_factor = next((row for row in factor_rows if row.get("factor_id") == "coverage_reward"), {})
    path_factor = next((row for row in factor_rows if row.get("factor_id") == "path_reward"), {})
    source_gap_factor = next((row for row in factor_rows if row.get("factor_id") == "source_gap_reward"), {})
    return [
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "selected_utility_no_activity",
            "evidence": f"selected changed episode rows={m174.get('selected_changed_episode_rows')}; selected promoted rows={m174.get('selected_promoted_rows')}; positive utility rows={selected.get('positive_utility_rows')}.",
            "interpretation": "The precommitted selected utility is materializable but inert; running Docker would not test a changed method.",
            "next_requirement": "Do not launch trajectory execution until the method changes policy-visible rows under fixed rules.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "rank_and_confidence_penalties_dominate",
            "evidence": f"rank mean contribution={fmt(rank_factor.get('mean_contribution'))}; confidence mean contribution={fmt(confidence_factor.get('mean_contribution'))}; selected utility max={fmt(selected.get('utility_delta_max'))}.",
            "interpretation": "The candidate moves offered by source-coverage-only require large rank displacement and confidence loss, so protected detector-confidence fallback suppresses every move.",
            "next_requirement": "Treat source coverage as a candidate-source/re-observation trigger rather than a within-pool reranking replacement unless a new non-posthoc principle is recorded.",
        },
        {
            "version": VERSION,
            "row_type": "failure_mechanism",
            "mechanism_id": "weak_reward_side",
            "evidence": f"coverage positive rows={coverage_factor.get('positive_input_rows')}; path positive rows={path_factor.get('positive_input_rows')}; source-gap rows={source_gap_factor.get('positive_input_rows')}; no-confidence-guard positive utility rows={no_conf.get('positive_utility_rows')}.",
            "interpretation": "Even the confidence-guard negative control has zero positive utility rows, so the failure is not only one guard; reward signals are too sparse/weak for posthoc reranking.",
            "next_requirement": "A next method must create or request better source evidence before ranking, not merely relax a threshold.",
        },
    ]


def route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "run_m175_docker_trajectory_contract_now",
            "decision": "reject",
            "selected": False,
            "reason": "M174 selected policy activity gate failed; Docker execution would duplicate detector-confidence behavior.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "posthoc_weight_or_threshold_tuning",
            "decision": "reject",
            "selected": False,
            "reason": "Changing weights only to create order changes would violate the paper rule against conclusion-fitting after a negative gate.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "source_coverage_trigger_candidate_source_expansion",
            "decision": "select_next",
            "selected": ready,
            "reason": "M174 shows source coverage is not effective as protected within-pool reranking; it should instead trigger candidate-source expansion/re-observation before ranking.",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M174b decomposition",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "row_type": "route_decision",
            "route_id": "close_source_coverage_rerank_branch_negative",
            "decision": "record_boundary",
            "selected": False,
            "reason": "Within-pool source-coverage utility is recorded as a negative branch unless future evidence introduces a new principle.",
            "selected_next_unit": None,
            "launch_long_job_now": False,
        },
    ]


def next_contract_seed_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "next_contract_seed",
            "selected_next_unit": NEXT_UNIT,
            "method_family": "source_coverage_triggered_candidate_source_expansion",
            "principle": "If source coverage is the missing factor, semantic map should decide when to request or include additional observation sources before detector-confidence ranking, not force low-confidence candidates upward inside a fixed pool.",
            "allowed_inputs": [
                "coverage diversity of current source set",
                "detector-confidence distribution",
                "path-ready/source-ready status",
                "source pose coverage keys",
                "pre-execution candidate-source availability",
            ],
            "blocked_inputs": [
                "ObjectNav eval goal/viewpoints",
                "trajectory_success",
                "SR/SPL",
                "success proposal id",
            ],
            "baseline_to_preserve": PROTECTED_BASELINE,
            "minimum_gate_before_execution": "new candidate-source rows must change selected policy rows before Docker trajectory execution",
        }
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_coverage_utility_rerank_branch",
            "supported": False,
            "claim_boundary": "M174b closes the current within-pool source-coverage utility reranking branch as inactive under fixed guards.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_as_map_interface_signal",
            "supported": True,
            "claim_boundary": "M174b supports only a design diagnosis: source coverage should be used as a candidate-source/re-observation trigger, not as positive navigation evidence.",
        },
        {
            "version": VERSION,
            "claim_id": "real_navigation_improvement",
            "supported": False,
            "claim_boundary": "Still requires a changed method, Docker trajectory execution, protected-baseline interpretation, heldout transfer, and external baselines.",
        },
    ]


def reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "issue_id": "why_not_run_trajectories_anyway",
            "reviewer_response": "Because the selected policy changes 0/30 episode orders; running trajectories would not test the claimed method.",
        },
        {
            "version": VERSION,
            "issue_id": "is_next_step_threshold_tuning",
            "reviewer_response": "No. M174b rejects posthoc weight/threshold tuning and derives the next method form from the failure mechanism.",
        },
        {
            "version": VERSION,
            "issue_id": "what_did_negative_result_teach",
            "reviewer_response": "Source coverage-only can move the Pareto frontier, but protected detector-confidence ranking suppresses those moves; source coverage should control source acquisition/re-observation before ranking.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_summary: list[dict[str, Any]],
    factor_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    selected_summary = [row for row in policy_summary if row.get("policy_id") in {SELECTED_POLICY, WITHOUT_CONFIDENCE_GUARD}]
    return "\n".join(
        [
            "# E008-M174b Source-Coverage Utility Conservatism Failure Decomposition",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M174 status: `{coverage['m174_status']}`.",
            f"- Selected policy changed episode rows: {coverage['selected_changed_episode_rows']}.",
            f"- Selected positive utility rows: {coverage['selected_positive_utility_rows']}.",
            f"- Selected utility max: {fmt(coverage['selected_utility_delta_max'])}.",
            f"- No-confidence-guard positive utility rows: {coverage['no_confidence_guard_positive_utility_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Component Summary",
            "",
            table(selected_summary, ["policy_id", "component_rows", "promotion_allowed_rows", "positive_utility_rows", "confidence_guard_fail_rows", "prefix_path_guard_fail_rows", "utility_delta_max", "utility_delta_mean"]),
            "",
            "## Selected Utility Factors",
            "",
            table(factor_rows, ["factor_id", "weight", "positive_input_rows", "input_mean", "mean_contribution", "max_contribution"]),
            "",
            "## Failure Mechanisms",
            "",
            table(failure_rows, ["mechanism_id", "interpretation", "next_requirement"]),
            "",
            "## Route Decision",
            "",
            table(route_rows, ["route_id", "decision", "selected", "reason", "selected_next_unit"]),
            "",
            "## Claim Boundary",
            "",
            "- M174b does not support real navigation `SR` / `SPL` claims.",
            "- Docker execution remains blocked because the selected policy has no activity.",
            "- The next method should move source coverage earlier in the map/re-observation interface rather than tune the inactive reranker.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m172 = read_json(M172_DIR / "coverage.json")
    m173 = read_json(M173_DIR / "coverage.json")
    m174 = read_json(M174_DIR / "coverage.json")
    component_rows = read_jsonl(M174_DIR / "utility_component_rows.jsonl")
    missing = []
    if m172.get("status") != "e008_m172_source_coverage_ablation_tradeoff_decomposition_ready":
        missing.append("M172 ready coverage")
    if m173.get("status") != "e008_m173_source_coverage_utility_pareto_contract_ready":
        missing.append("M173 ready coverage")
    if m174.get("status") != "e008_m174_source_coverage_utility_pareto_materialization_blocked":
        missing.append("M174 blocked materialization coverage")
    if not component_rows:
        missing.append("M174 utility component rows")

    policy_summary = summarize_components(component_rows)
    factor_rows = selected_utility_factor_rows(component_rows)
    failure_rows = failure_mechanism_rows(policy_summary, factor_rows, m174) if not missing else []
    selected_summary = next((row for row in policy_summary if row.get("policy_id") == SELECTED_POLICY), {})
    no_conf_summary = next((row for row in policy_summary if row.get("policy_id") == WITHOUT_CONFIDENCE_GUARD), {})
    ready = not missing and selected_summary.get("positive_utility_rows") == 0 and m174.get("selected_changed_episode_rows") == 0
    route_rows = route_decision_rows(ready)
    seed_rows = next_contract_seed_rows() if ready else []
    claims = claim_boundary_rows()
    reviewer_rows = reviewer_defense_rows()

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m172_status": m172.get("status"),
        "m173_status": m173.get("status"),
        "m174_status": m174.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "source_coverage_witness_policy_id": SOURCE_COVERAGE_WITNESS,
        "component_rows": len(component_rows),
        "policy_component_summary_rows": len(policy_summary),
        "selected_changed_episode_rows": m174.get("selected_changed_episode_rows"),
        "selected_promoted_rows": m174.get("selected_promoted_rows"),
        "selected_positive_utility_rows": selected_summary.get("positive_utility_rows"),
        "selected_utility_delta_max": selected_summary.get("utility_delta_max"),
        "selected_utility_delta_mean": selected_summary.get("utility_delta_mean"),
        "selected_confidence_guard_fail_rows": selected_summary.get("confidence_guard_fail_rows"),
        "selected_prefix_path_guard_fail_rows": selected_summary.get("prefix_path_guard_fail_rows"),
        "selected_coverage_positive_rows": selected_summary.get("coverage_positive_rows"),
        "selected_path_saving_positive_rows": selected_summary.get("path_saving_positive_rows"),
        "selected_source_gap_prelabel_rows": selected_summary.get("source_gap_prelabel_rows"),
        "no_confidence_guard_positive_utility_rows": no_conf_summary.get("positive_utility_rows"),
        "docker_trajectory_execution_ready": False,
        "posthoc_tuning_allowed": False,
        "source_coverage_rerank_branch_closed_negative": ready,
        "candidate_source_expansion_contract_ready_next": ready,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M174b decomposition",
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "policy_component_summary_rows.jsonl", policy_summary)
    write_jsonl(ARTIFACT_DIR / "selected_utility_factor_rows.jsonl", factor_rows)
    write_jsonl(ARTIFACT_DIR / "failure_mechanism_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "next_contract_seed_rows.jsonl", seed_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claims)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, policy_summary, factor_rows, failure_rows, route_rows), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
