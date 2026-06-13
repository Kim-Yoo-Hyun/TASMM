#!/usr/bin/env python3
"""Package E008 navigation failure boundary and select the next method pivot."""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M165_DIR = EXP_ROOT / "artifacts" / "E008-M165_confidence_first_repair_failure_decomposition_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M166_navigation_failure_boundary_method_pivot_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M166_navigation_failure_boundary_method_pivot_contract_v0"

VERSION = "e008_m166_navigation_failure_boundary_method_pivot_contract_v0"
READY_STATUS = "e008_m166_navigation_failure_boundary_method_pivot_contract_ready"
BLOCKED_STATUS = "e008_m166_navigation_failure_boundary_method_pivot_contract_blocked"
NEXT_UNIT = "E008-M167 source-coverage memory-interface method contract"

SELECTED_METHOD_FAMILY = "source_coverage_memory_interface"
SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"


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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    try:
        out = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{out:.6f}" if math.isfinite(out) else "NA"


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def boundary_rows(m165: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "failure_boundary",
            "boundary_id": "local_path_tiebreak_not_main_method",
            "status": "closed_negative",
            "fact": f"M165 changed {m165.get('changed_episode_rows')} / 30 episode orders but changed {m165.get('selected_success_proposal_changed_rows')} successful proposals vs detector-confidence.",
            "paper_decision": "exclude local path tie-break from the main method family",
            "next_requirement": "future policy must change source coverage, recovered target, or pre-success route cost at episode level",
        },
        {
            "version": VERSION,
            "row_type": "failure_boundary",
            "boundary_id": "confidence_floor_guard_required",
            "status": "keep_as_guard",
            "fact": "`confidence_floor_guard` is the only diagnostic-supported component from M165.",
            "paper_decision": "retain as a necessary reliability guard, not as a standalone contribution",
            "next_requirement": "all future policies must preserve detector-confidence as protected baseline and confidence floor as a guard",
        },
        {
            "version": VERSION,
            "row_type": "failure_boundary",
            "boundary_id": "source_gap_not_validated_on_current_denominator",
            "status": "defer_to_source_gap_or_external_route",
            "fact": f"source_gap_prelabel_rows={m165.get('source_gap_prelabel_rows')}; source-gap trigger is absent/inert.",
            "paper_decision": "do not claim source-gap trigger on the current full-val-mini denominator",
            "next_requirement": "evaluate source-gap only on source-gap/source-coverage rows or external proposal-source routes",
        },
        {
            "version": VERSION,
            "row_type": "failure_boundary",
            "boundary_id": "ranking_only_navigation_repair_exhausted",
            "status": "method_pivot_required",
            "fact": "ranking-only repair changes order around the same candidate set and does not change successful target recovery.",
            "paper_decision": "pivot from local reranking to source-coverage / memory-interface policy",
            "next_requirement": "M167 must freeze an input/ablation contract before any new rows are materialized",
        },
    ]


def method_pivot_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "method_pivot",
            "method_family": SELECTED_METHOD_FAMILY,
            "policy_id": SELECTED_POLICY,
            "decision": "selected_next",
            "principle": "semantic memory/search policy must expose source coverage and memory-interface decisions, not only local path-cost reranking",
            "kept_component": "confidence_floor_guard",
            "excluded_component": "local_path_tiebreak_as_main_method",
            "protected_baseline": PROTECTED_BASELINE,
            "materialization_ready_next": True,
        },
        {
            "version": VERSION,
            "row_type": "method_pivot",
            "method_family": "external_map_assisted_proposal_route",
            "policy_id": "conceptgraphs_only_or_assisted_route",
            "decision": "baseline_pressure_after_internal_contract",
            "principle": "external map proposals remain required for reviewer pressure, but need a shared candidate interface before direct navigation comparison",
            "kept_component": "external proposal source",
            "excluded_component": "unmatched denominator comparison",
            "protected_baseline": PROTECTED_BASELINE,
            "materialization_ready_next": False,
        },
        {
            "version": VERSION,
            "row_type": "method_pivot",
            "method_family": "memory_interface_repair",
            "policy_id": "memory_trust_state_reobservation_route",
            "decision": "secondary_candidate",
            "principle": "memory trust and re-observation should become explicit state if source coverage alone does not improve execution",
            "kept_component": "task/staleness memory trust",
            "excluded_component": "human intent as current main claim",
            "protected_baseline": PROTECTED_BASELINE,
            "materialization_ready_next": False,
        },
    ]


def comparison_rows() -> list[dict[str, Any]]:
    comparisons = [
        ("static_stale_memory", "required_baseline", "proxy/e008 adapter if stale rows are present"),
        (PROTECTED_BASELINE, "protected_naive_baseline", "must remain primary protected baseline"),
        ("ConceptGraphs-only open-vocabulary map", "external_baseline", "use only through matched candidate interface"),
        ("task_agnostic_reobservation_or_source_coverage", "ablation_baseline", "separate source coverage from H001 memory trust"),
        (SELECTED_POLICY, "selected_h001_variant", "new method family after M165 failure boundary"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "comparison_contract",
            "comparison_id": comparison_id,
            "role": role,
            "requirement": requirement,
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
        }
        for comparison_id, role, requirement in comparisons
    ]


def claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "m166_failure_boundary_package",
            "supported": True,
            "claim_boundary": "M166 freezes why local rerank is not a paper-facing main method and selects the next pivot.",
        },
        {
            "version": VERSION,
            "claim_id": "selected_method_improves_navigation",
            "supported": False,
            "claim_boundary": "Requires M168 materialization, M169 Docker contract, later trajectory execution, and protected-baseline interpretation.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Still blocked until executed trajectory results, heldout transfer, ablations, and external navigation/search baselines.",
        },
    ]


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_method_contract",
            "selected_next_unit": NEXT_UNIT,
            "selected_method_family": SELECTED_METHOD_FAMILY,
            "selected_policy_id": SELECTED_POLICY,
            "launch_long_job_now": False,
            "method_contract_ready_next": True,
            "row_materialization_ready_now": False,
            "docker_execution_contract_ready_now": False,
        }
    ]


def report(coverage: dict[str, Any], boundaries: list[dict[str, Any]], pivots: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M166 Navigation Failure Boundary And Method Pivot Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M165 status: `{coverage['m165_status']}`.",
            f"- Selected method family: `{coverage['selected_method_family']}`.",
            f"- Selected policy id: `{coverage['selected_policy_id']}`.",
            f"- Protected baseline: `{coverage['protected_baseline_policy_id']}`.",
            f"- Local path tie-break as main method: {coverage['local_path_tiebreak_main_method_ready']}.",
            f"- Confidence floor guard retained: {coverage['confidence_floor_guard_retained']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Failure Boundaries",
            "",
            table(boundaries, ["boundary_id", "status", "paper_decision", "next_requirement"]),
            "",
            "## Method Pivot Candidates",
            "",
            table(pivots, ["method_family", "decision", "policy_id", "principle"]),
            "",
            "## Claim Boundary",
            "",
            "- M166 is a boundary/contract step, not a positive navigation result.",
            "- The next executable path must preserve detector-confidence as protected baseline and keep `confidence_floor_guard` as a guard.",
            "- `source_gap_trigger` remains unclaimed on the current denominator.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m165 = read_json(M165_DIR / "coverage.json")
    missing = []
    if m165.get("status") != "e008_m165_confidence_first_repair_failure_decomposition_ready":
        missing.append("M165 ready coverage")
    if m165.get("method_pivot_contract_required") is not True:
        missing.append("M165 method pivot requirement")

    boundaries = boundary_rows(m165)
    pivots = method_pivot_rows()
    comparisons = comparison_rows()
    claims = claim_rows()
    routes = route_rows()
    reviewer_rows = [
        {
            "version": VERSION,
            "issue_id": "why_not_continue_local_rerank",
            "reviewer_response": "M165 shows local swaps changed order without changing successful target proposals; continuing local threshold tuning would be conclusion-fitting.",
        },
        {
            "version": VERSION,
            "issue_id": "why_source_coverage_memory_interface",
            "reviewer_response": "The next method must change what source/candidate evidence is exposed to the policy, because ranking the same candidate set did not change target recovery.",
        },
        {
            "version": VERSION,
            "issue_id": "why_keep_detector_confidence",
            "reviewer_response": "Detector-confidence is the protected naive baseline and confidence floor is the only supported guard from M165.",
        },
    ]

    ready = not missing
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m165_status": m165.get("status"),
        "selected_method_family": SELECTED_METHOD_FAMILY,
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "failure_boundary_rows": len(boundaries),
        "method_pivot_rows": len(pivots),
        "comparison_contract_rows": len(comparisons),
        "local_path_tiebreak_main_method_ready": False,
        "confidence_floor_guard_retained": True,
        "source_gap_claim_ready_on_current_denominator": False,
        "method_contract_ready_next": ready,
        "row_materialization_ready_now": False,
        "docker_execution_contract_ready_now": False,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M166 inputs",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "failure_boundary_rows.jsonl", boundaries)
    write_jsonl(ARTIFACT_DIR / "method_pivot_rows.jsonl", pivots)
    write_jsonl(ARTIFACT_DIR / "comparison_contract_rows.jsonl", comparisons)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claims)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", routes)
    (ARTIFACT_DIR / "report.md").write_text(report(coverage, boundaries, pivots), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
