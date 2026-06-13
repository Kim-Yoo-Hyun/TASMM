#!/usr/bin/env python3
"""Interpret M184 against the protected detector-confidence baseline and decide scale-up status."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m185_protected_detector_confidence_interpretation_scale_decision_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M185_protected_detector_confidence_interpretation_scale_decision_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M185_protected_detector_confidence_interpretation_scale_decision_v0"
M184_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"

METHOD_POLICY = "path_cost_ascending_reachable_subset_v0"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def policy_aggregate(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id") or row.get("group_id")): row
        for row in metric_rows
        if row.get("metric_scope") == "policy_aggregate"
    }


def build_pairwise_summary(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        grouped[str(row.get("baseline_policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for baseline_id, rows in sorted(grouped.items()):
        out.append(
            {
                "version": VERSION,
                "baseline_policy_id": baseline_id,
                "rows": len(rows),
                "delta_SR_mean": mean([finite_float(row.get("delta_SR")) for row in rows]),
                "delta_SPL_mean": mean([finite_float(row.get("delta_SPL")) for row in rows]),
                "delta_PathLengthM_mean": mean([finite_float(row.get("delta_PathLengthM")) for row in rows]),
                "method_success_rows": sum(1 for row in rows if finite_float(row.get("method_SR")) == 1.0),
                "baseline_success_rows": sum(1 for row in rows if finite_float(row.get("baseline_SR")) == 1.0),
            }
        )
    return out


def build_policy_summary(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggs = policy_aggregate(metric_rows)
    rows: list[dict[str, Any]] = []
    for policy_id, row in sorted(aggs.items()):
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_task_policy_rows": row.get("scan_task_policy_rows"),
                "success_rows": row.get("success_rows"),
                "SR": row.get("SR"),
                "SPL": row.get("SPL"),
                "PathLengthM_mean": row.get("PathLengthM_mean"),
                "CandidateVisits_mean": row.get("CandidateVisits_mean"),
                "StopRank_mean_over_success": row.get("StopRank_mean_over_success"),
            }
        )
    return rows


def decide(coverage: dict[str, Any], policy_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]]) -> dict[str, Any]:
    policy = {str(row["policy_id"]): row for row in policy_rows}
    method = policy.get(METHOD_POLICY, {})
    protected = policy.get(PROTECTED_BASELINE, {})
    protected_pairwise = [row for row in pairwise_rows if row.get("baseline_policy_id") == PROTECTED_BASELINE]
    method_sr = finite_float(method.get("SR")) or 0.0
    protected_sr = finite_float(protected.get("SR")) or 0.0
    method_spl = finite_float(method.get("SPL")) or 0.0
    protected_spl = finite_float(protected.get("SPL")) or 0.0
    ready = coverage.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready"
    if not ready:
        decision = "blocked_repair_m184_execution"
        scale_ready = False
        reason = f"M184 status={coverage.get('status')}"
    elif method_sr > protected_sr or (method_sr == protected_sr and method_spl > protected_spl):
        decision = "scale_up_source_pool_policy_with_protected_baseline"
        scale_ready = True
        reason = "method matches or improves protected baseline SR and improves either SR or SPL."
    elif method_sr == protected_sr and method_spl == protected_spl and protected_pairwise:
        decision = "scale_up_as_tie_boundary_with_case_level_failure_analysis"
        scale_ready = True
        reason = "method ties protected baseline; larger scale can test whether path-cost ordering improves cost without losing SR."
    else:
        decision = "method_not_yet_better_than_protected_baseline"
        scale_ready = False
        reason = "protected detector-confidence baseline remains stronger on bounded trajectory smoke."
    return {
        "version": VERSION,
        "decision": decision,
        "scale_up_recommended": scale_ready,
        "reason": reason,
        "method_policy_id": METHOD_POLICY,
        "protected_baseline_id": PROTECTED_BASELINE,
        "method_SR": method_sr,
        "protected_baseline_SR": protected_sr,
        "method_SPL": method_spl,
        "protected_baseline_SPL": protected_spl,
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(coverage: dict[str, Any], policy_rows: list[dict[str, Any]], pairwise_rows: list[dict[str, Any]], decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M185 Protected Detector-Confidence Interpretation Scale Decision",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M184 status: `{coverage['m184_status']}`.",
            f"- Protected baseline: `{PROTECTED_BASELINE}`.",
            f"- Method policy: `{METHOD_POLICY}`.",
            f"- Scale-up recommended: {str(coverage['scale_up_recommended']).lower()}.",
            f"- Decision: `{decision['decision']}`.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "scan_task_policy_rows",
                    "success_rows",
                    "SR",
                    "SPL",
                    "PathLengthM_mean",
                    "CandidateVisits_mean",
                ],
            ),
            "",
            "## Pairwise Delta Summary",
            "",
            markdown_table(pairwise_rows, ["baseline_policy_id", "rows", "delta_SR_mean", "delta_SPL_mean", "delta_PathLengthM_mean"]),
            "",
            "## Claim Boundary",
            "",
            "- M185 interprets a bounded source-pool trajectory smoke, not a final real navigation benchmark.",
            "- `SR` / `SPL` are executed `Habitat` diagnostics over the current bounded denominator.",
            "- Final top-tier navigation claim still requires larger heldout scale, external navigation/search baselines, and robustness analysis.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    m184_cov = read_json(M184_ARTIFACT_DIR / "coverage.json")
    metric_rows = read_jsonl(M184_ARTIFACT_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    pairwise_delta_rows = read_jsonl(M184_ARTIFACT_DIR / "pairwise_policy_delta_rows.jsonl")
    policy_rows = build_policy_summary(metric_rows)
    pairwise_rows = build_pairwise_summary(pairwise_delta_rows)
    decision = decide(m184_cov, policy_rows, pairwise_rows)
    ready = m184_cov.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready"
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m185_protected_detector_confidence_interpretation_scale_decision_ready"
        if ready
        else "e008_m185_protected_detector_confidence_interpretation_scale_decision_blocked",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m184_status": m184_cov.get("status"),
        "m184_scan_task_policy_rows": m184_cov.get("scan_task_policy_rows"),
        "m184_trajectory_success_rows": m184_cov.get("trajectory_success_rows"),
        "policy_summary_rows": len(policy_rows),
        "pairwise_summary_rows": len(pairwise_rows),
        "scale_up_recommended": decision["scale_up_recommended"],
        "selected_next_unit": "scale source-pool real navigation denominator"
        if decision["scale_up_recommended"]
        else "repair source-pool policy before scale-up",
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        **{f"decision_{key}": value for key, value in decision.items() if key != "version"},
    }
    claim_rows = [
        {
            "version": VERSION,
            "claim_id": "bounded_source_pool_trajectory_interpretation",
            "supported": ready,
            "claim_boundary": "M185 supports bounded trajectory interpretation only.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final SR/SPL claim requires larger heldout denominator and external navigation/search baselines.",
        },
    ]
    route_rows = [
        {
            "version": VERSION,
            "decision": decision["decision"],
            "selected_next_unit": coverage["selected_next_unit"],
            "scale_up_recommended": decision["scale_up_recommended"],
            "reason": decision["reason"],
        }
    ]
    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "pairwise_delta_summary_rows.jsonl", pairwise_rows)
        write_jsonl(output_dir / "scale_decision_rows.jsonl", [decision])
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_rows, pairwise_rows, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
