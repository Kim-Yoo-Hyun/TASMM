#!/usr/bin/env python3
"""Interpret M32 H001 trajectory results against M22 detector trajectories."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M33_h001_trajectory_result_interpretation_baseline_alignment_v0"
)
VERSION = "e008_m33_h001_trajectory_result_interpretation_baseline_alignment_v0"

M22_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M30_DIR = EXP_ROOT / "artifacts" / "E008-M30_h001_current_observation_fallback_replay_smoke_v0"
M32_DIR = EXP_ROOT / "artifacts" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"

H001_POLICY = "h001_current_observation_backstop_top5_v0"
PRIMARY_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
DETECTOR_POLICIES = [
    "detector_confidence_all_candidates_v0",
    "detector_confidence_reachable_subset_v0",
    "confidence_path_cost_tradeoff_reachable_subset_v0",
    "path_cost_ascending_reachable_subset_v0",
]


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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def delta(a: object, b: object) -> float | None:
    af = finite_float(a)
    bf = finite_float(b)
    if af is None or bf is None:
        return None
    return float(af - bf)


def scan_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") in {"scan_policy", "scan_task_policy"}]


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("metric_scope") in {"policy_aggregate", "task_context_aggregate", "source_gap_aggregate"}
    ]


def index_detector_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for row in scan_policy_rows(rows):
        policy_id = str(row.get("policy_id"))
        if policy_id in DETECTOR_POLICIES:
            out[(str(row.get("adapter_episode_id")), policy_id)] = row
    return out


def index_h001_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for row in scan_policy_rows(rows):
        if row.get("policy_id") == H001_POLICY:
            out[(str(row.get("adapter_episode_id")), str(row.get("task_context_id")))] = row
    return out


def build_denominator_alignment_rows(
    detector_rows: list[dict[str, Any]],
    h001_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    detector_index = index_detector_rows(detector_rows)
    h001_index = index_h001_rows(h001_rows)
    episode_ids = sorted({episode_id for episode_id, _ in h001_index})
    task_context_ids = sorted({task_id for _, task_id in h001_index})
    rows: list[dict[str, Any]] = []

    rows.append(
        {
            "version": VERSION,
            "alignment_scope": "native_detector_policy",
            "method_id": "detector_policies_native_m22",
            "episode_rows": len({row.get("adapter_episode_id") for row in scan_policy_rows(detector_rows)}),
            "task_context_rows": 0,
            "policy_rows": len(scan_policy_rows(detector_rows)),
            "directly_comparable_to_h001_task_context_rows": False,
            "reason": "M22 detector policies are evaluated once per episode; M32 H001 is evaluated once per episode-task-context.",
        }
    )
    rows.append(
        {
            "version": VERSION,
            "alignment_scope": "native_h001_task_context",
            "method_id": H001_POLICY,
            "episode_rows": len(episode_ids),
            "task_context_rows": len(task_context_ids),
            "policy_rows": len(scan_policy_rows(h001_rows)),
            "directly_comparable_to_h001_task_context_rows": True,
            "reason": "M32 H001 has 3 structured task contexts per ObjectNav episode.",
        }
    )
    for policy_id in DETECTOR_POLICIES:
        available = sum(1 for episode_id in episode_ids if (episode_id, policy_id) in detector_index)
        rows.append(
            {
                "version": VERSION,
                "alignment_scope": "detector_replicated_to_task_context",
                "method_id": policy_id,
                "episode_rows": available,
                "task_context_rows": len(task_context_ids),
                "policy_rows": available * len(task_context_ids),
                "directly_comparable_to_h001_task_context_rows": available == len(episode_ids),
                "reason": "Detector has no task-context branch; replicate each detector episode result over H001 task contexts only for denominator-aligned diagnostic comparison.",
            }
        )
    return rows


def aggregate_method(rows: list[dict[str, Any]], method_id: str, scope: str) -> dict[str, Any]:
    success_rows = sum(1 for row in rows if bool(row.get("trajectory_success") or row.get("SR") == 1.0))
    total_rows = len(rows)
    return {
        "version": VERSION,
        "metric_scope": scope,
        "method_id": method_id,
        "rows": total_rows,
        "success_rows": success_rows,
        "SR": safe_ratio(success_rows, total_rows),
        "SPL": mean([finite_float(row.get("SPL")) for row in rows]),
        "PathLengthM_mean": mean([finite_float(row.get("PathLengthM")) for row in rows]),
        "CandidateVisits_mean": mean([finite_float(row.get("CandidateVisits")) for row in rows]),
        "StopRank_mean_over_success": mean(
            [finite_float(row.get("StopRank")) for row in rows if bool(row.get("trajectory_success"))]
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) for row in rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": any(
            bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_metric")) for row in rows
        ),
    }


def build_aligned_metric_rows(
    detector_rows: list[dict[str, Any]],
    h001_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    detector_index = index_detector_rows(detector_rows)
    h001_index = index_h001_rows(h001_rows)
    episode_task_keys = sorted(h001_index)
    aligned: list[dict[str, Any]] = []

    h001_task_rows = [h001_index[key] for key in episode_task_keys]
    h001_source_ready_rows = [
        row for row in h001_task_rows if not bool(row.get("m31_source_gap_boundary"))
    ]
    h001_source_gap_rows = [
        row for row in h001_task_rows if bool(row.get("m31_source_gap_boundary"))
    ]
    aligned.append(aggregate_method(h001_task_rows, H001_POLICY, "h001_task_context_aligned"))
    aligned.append(aggregate_method(h001_source_ready_rows, H001_POLICY, "h001_source_ready_subset"))
    aligned.append(aggregate_method(h001_source_gap_rows, H001_POLICY, "h001_source_gap_subset"))

    for policy_id in DETECTOR_POLICIES:
        replicated = []
        source_ready_replicated = []
        source_gap_replicated = []
        for episode_id, task_context_id in episode_task_keys:
            row = detector_index.get((episode_id, policy_id))
            h001 = h001_index[(episode_id, task_context_id)]
            if not row:
                continue
            diagnostic_row = dict(row)
            diagnostic_row["task_context_id"] = task_context_id
            replicated.append(diagnostic_row)
            if bool(h001.get("m31_source_gap_boundary")):
                source_gap_replicated.append(diagnostic_row)
            else:
                source_ready_replicated.append(diagnostic_row)
        aligned.append(aggregate_method(replicated, policy_id, "detector_task_context_replicated"))
        aligned.append(aggregate_method(source_ready_replicated, policy_id, "detector_on_h001_source_ready_subset"))
        aligned.append(aggregate_method(source_gap_replicated, policy_id, "detector_on_h001_source_gap_subset"))
    return aligned


def build_pairwise_delta_rows(aligned_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["metric_scope"], row["method_id"]): row for row in aligned_rows}
    h001_all = by_key.get(("h001_task_context_aligned", H001_POLICY), {})
    h001_ready = by_key.get(("h001_source_ready_subset", H001_POLICY), {})
    h001_gap = by_key.get(("h001_source_gap_subset", H001_POLICY), {})
    rows = []
    for policy_id in DETECTOR_POLICIES:
        comparisons = [
            ("all_task_context_rows", h001_all, by_key.get(("detector_task_context_replicated", policy_id), {})),
            ("h001_source_ready_subset", h001_ready, by_key.get(("detector_on_h001_source_ready_subset", policy_id), {})),
            ("h001_source_gap_subset", h001_gap, by_key.get(("detector_on_h001_source_gap_subset", policy_id), {})),
        ]
        for scope, h001, detector in comparisons:
            rows.append(
                {
                    "version": VERSION,
                    "comparison_scope": scope,
                    "h001_method_id": H001_POLICY,
                    "baseline_method_id": policy_id,
                    "h001_rows": h001.get("rows"),
                    "baseline_rows": detector.get("rows"),
                    "h001_SR": h001.get("SR"),
                    "baseline_SR": detector.get("SR"),
                    "h001_minus_baseline_SR": delta(h001.get("SR"), detector.get("SR")),
                    "h001_SPL": h001.get("SPL"),
                    "baseline_SPL": detector.get("SPL"),
                    "h001_minus_baseline_SPL": delta(h001.get("SPL"), detector.get("SPL")),
                    "h001_PathLengthM_mean": h001.get("PathLengthM_mean"),
                    "baseline_PathLengthM_mean": detector.get("PathLengthM_mean"),
                    "h001_minus_baseline_PathLengthM_mean": delta(
                        h001.get("PathLengthM_mean"), detector.get("PathLengthM_mean")
                    ),
                    "interpretation": classify_pairwise_result(scope, h001, detector, policy_id),
                }
            )
    return rows


def classify_pairwise_result(scope: str, h001: dict[str, Any], detector: dict[str, Any], policy_id: str) -> str:
    h001_sr = finite_float(h001.get("SR"))
    det_sr = finite_float(detector.get("SR"))
    h001_spl = finite_float(h001.get("SPL"))
    det_spl = finite_float(detector.get("SPL"))
    if h001_sr is None or det_sr is None:
        return "missing_alignment_row"
    if scope == "h001_source_gap_subset" and h001_sr == 0.0 and det_sr > 0.0:
        return "source_gap_is_h001_candidate_source_failure_not_navigation_difficulty"
    if h001_sr < det_sr:
        return "h001_underperforms_detector_on_success"
    if h001_sr == det_sr and h001_spl is not None and det_spl is not None and h001_spl < det_spl:
        return "h001_matches_success_but_loses_efficiency"
    if h001_sr == det_sr and h001_spl is not None and det_spl is not None and h001_spl >= det_spl:
        return "h001_matches_or_beats_detector_on_aligned_subset"
    return f"requires_manual_review_against_{policy_id}"


def build_proxy_execution_rows(
    proxy_delta_rows: list[dict[str, Any]],
    h001_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = list(proxy_delta_rows)
    source_ready = [row for row in proxy_delta_rows if not bool(row.get("m31_source_gap_boundary"))]
    source_gap = [row for row in proxy_delta_rows if bool(row.get("m31_source_gap_boundary"))]
    h001_metric_rows = scan_policy_rows(h001_rows)
    return [
        {
            "version": VERSION,
            "scope": "all_h001_task_context_rows",
            "rows": len(all_rows),
            "success_agreement_rows": sum(1 for row in all_rows if row.get("success_agreement")),
            "success_agreement_rate": safe_ratio(sum(1 for row in all_rows if row.get("success_agreement")), len(all_rows)),
            "proxy_SPL_mean": mean([finite_float(row.get("m30_proxy_spl")) for row in all_rows]),
            "trajectory_SPL_mean": mean([finite_float(row.get("trajectory_spl")) for row in all_rows]),
            "trajectory_minus_proxy_SPL_mean": mean(
                [finite_float(row.get("trajectory_minus_proxy_spl")) for row in all_rows]
            ),
            "interpretation": "proxy success transfers, but proxy SPL overestimates executed efficiency",
        },
        {
            "version": VERSION,
            "scope": "source_ready_subset",
            "rows": len(source_ready),
            "success_agreement_rows": sum(1 for row in source_ready if row.get("success_agreement")),
            "success_agreement_rate": safe_ratio(
                sum(1 for row in source_ready if row.get("success_agreement")), len(source_ready)
            ),
            "proxy_SPL_mean": mean([finite_float(row.get("m30_proxy_spl")) for row in source_ready]),
            "trajectory_SPL_mean": mean([finite_float(row.get("trajectory_spl")) for row in source_ready]),
            "trajectory_minus_proxy_SPL_mean": mean(
                [finite_float(row.get("trajectory_minus_proxy_spl")) for row in source_ready]
            ),
            "interpretation": "H001 can execute when candidate source contains a target-region proposal, but trajectory efficiency is lower than proxy",
        },
        {
            "version": VERSION,
            "scope": "source_gap_subset",
            "rows": len(source_gap),
            "success_agreement_rows": sum(1 for row in source_gap if row.get("success_agreement")),
            "success_agreement_rate": safe_ratio(
                sum(1 for row in source_gap if row.get("success_agreement")), len(source_gap)
            ),
            "proxy_SPL_mean": mean([finite_float(row.get("m30_proxy_spl")) for row in source_gap]),
            "trajectory_SPL_mean": mean([finite_float(row.get("trajectory_spl")) for row in source_gap]),
            "trajectory_minus_proxy_SPL_mean": mean(
                [finite_float(row.get("trajectory_minus_proxy_spl")) for row in source_gap]
            ),
            "interpretation": "source-gap failures remain failures under execution",
        },
        {
            "version": VERSION,
            "scope": "h001_failure_type_counts",
            "rows": len(h001_metric_rows),
            "failure_type_counts": dict(sorted(Counter(str(row.get("FailureType")) for row in h001_metric_rows).items())),
            "interpretation": "all M32 failures are exhausted-stop source-gap failures",
        },
    ]


def build_claim_boundary_rows(pairwise_rows: list[dict[str, Any]], proxy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_pair = next(
        (
            row
            for row in pairwise_rows
            if row["comparison_scope"] == "all_task_context_rows"
            and row["baseline_method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    source_gap_pair = next(
        (
            row
            for row in pairwise_rows
            if row["comparison_scope"] == "h001_source_gap_subset"
            and row["baseline_method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    proxy_all = next((row for row in proxy_rows if row["scope"] == "all_h001_task_context_rows"), {})
    return [
        {
            "version": VERSION,
            "claim_id": "h001_fallback_trajectory_execution_smoke",
            "status": "supported_bounded",
            "safe_claim": "H001 fallback rows can be executed in Docker Habitat without policy leakage and proxy/trajectory success agrees on the 18-row smoke set.",
            "evidence": f"success agreement {proxy_all.get('success_agreement_rows')}/{proxy_all.get('rows')}; leakage pass recorded in M32.",
        },
        {
            "version": VERSION,
            "claim_id": "h001_improves_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Do not claim H001 improves real navigation SR/SPL in the current HM3D ObjectNav smoke.",
            "evidence": f"H001 vs {PRIMARY_DETECTOR_POLICY}: SR delta {primary_pair.get('h001_minus_baseline_SR')}, SPL delta {primary_pair.get('h001_minus_baseline_SPL')}.",
        },
        {
            "version": VERSION,
            "claim_id": "source_gap_boundary",
            "status": "blocked_for_current_h001_source",
            "safe_claim": "The current source-gap rows diagnose candidate-source failure rather than navigation execution failure.",
            "evidence": f"On source-gap subset, H001 SR {source_gap_pair.get('h001_SR')} vs detector SR {source_gap_pair.get('baseline_SR')}.",
        },
        {
            "version": VERSION,
            "claim_id": "stale_semantic_memory_navigation_novelty",
            "status": "not_tested_by_current_hm3d_objectnav_setup",
            "safe_claim": "Current HM3D ObjectNav smoke tests navigation plumbing, not the full stale-memory semantic mapping thesis.",
            "evidence": "HM3D ObjectNav has no explicit old-location/new-location stale-memory intervention; detector current-observation route dominates the smoke denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_rgbd_open_vocab_robustness",
            "status": "blocked",
            "safe_claim": "Do not claim final RGB-D/open-vocabulary robustness from E008-M33.",
            "evidence": "M33 reuses prior rendered detector candidates and does not add heldout detector/model/source variation.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m33_next_unit",
            "selected_next_unit": "E008-M34 dynamic-stale navigation benchmark contract and source-intervention design",
            "decision": "do_not_scale_current_h001_fallback_as_main_navigation_result",
            "reason": "The current H001 fallback trajectory underperforms detector trajectories and the current HM3D ObjectNav setup does not inject stale semantic memory changes.",
            "next_action": "Design the next navigation unit around stale-memory intervention or source construction before larger-scale SR/SPL claims.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m33_baseline_alignment",
            "selected_next_unit": "E008-M34 dynamic-stale navigation benchmark contract and source-intervention design",
            "decision": "keep_m22_detector_as_required_navigation_baseline",
            "reason": "Detector trajectory rows dominate current H001 rows on SR/SPL; any future H001 navigation claim must beat or explain this baseline under a stale-memory task setting.",
            "next_action": "Carry detector-confidence and path-cost detector policies forward as baseline rows.",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision_id": "m33_claim_boundary",
            "selected_next_unit": "E008-M34 dynamic-stale navigation benchmark contract and source-intervention design",
            "decision": "treat_m32_as_plumbing_smoke_not_paper_main_result",
            "reason": "M32 validates execution plumbing and leakage guard, but not the top-tier novelty mechanism.",
            "next_action": "Record M32 in reviewer-defense evidence and move to a dynamic-stale navigation contract.",
            "launch_long_job_now": False,
        },
    ]


def build_report(
    coverage: dict[str, Any],
    aligned_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    proxy_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    primary_pair = next(
        (
            row
            for row in pairwise_rows
            if row["comparison_scope"] == "all_task_context_rows"
            and row["baseline_method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    h001_all = next(
        (row for row in aligned_rows if row["metric_scope"] == "h001_task_context_aligned"),
        {},
    )
    detector_primary = next(
        (
            row
            for row in aligned_rows
            if row["metric_scope"] == "detector_task_context_replicated"
            and row["method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    source_ready = next((row for row in aligned_rows if row["metric_scope"] == "h001_source_ready_subset"), {})
    source_gap = next((row for row in aligned_rows if row["metric_scope"] == "h001_source_gap_subset"), {})
    proxy_all = next((row for row in proxy_rows if row["scope"] == "all_h001_task_context_rows"), {})
    lines = [
        "# E008-M33 H001 Trajectory Result Interpretation / Baseline Alignment",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M32 H001 task-context rows: {coverage['m32_scan_task_metric_rows']}.",
        f"- M22 detector scan-policy rows: {coverage['m22_scan_policy_metric_rows']}.",
        f"- H001 trajectory `SR`: {h001_all.get('SR'):.6f}.",
        f"- H001 trajectory `SPL`: {h001_all.get('SPL'):.6f}.",
        f"- Primary detector baseline: `{PRIMARY_DETECTOR_POLICY}`.",
        f"- Primary detector replicated `SR`: {detector_primary.get('SR'):.6f}.",
        f"- Primary detector replicated `SPL`: {detector_primary.get('SPL'):.6f}.",
        f"- H001 minus primary detector `SR`: {primary_pair.get('h001_minus_baseline_SR'):.6f}.",
        f"- H001 minus primary detector `SPL`: {primary_pair.get('h001_minus_baseline_SPL'):.6f}.",
        f"- Proxy/trajectory success agreement: {proxy_all.get('success_agreement_rows')} / {proxy_all.get('rows')}.",
        f"- Source-ready H001 subset `SR` / `SPL`: {source_ready.get('SR'):.6f} / {source_ready.get('SPL'):.6f}.",
        f"- Source-gap H001 subset `SR` / `SPL`: {source_gap.get('SR'):.6f} / {source_gap.get('SPL'):.6f}.",
        "",
        "## Aligned Metrics",
        "",
        "| metric_scope | method_id | rows | success_rows | SR | SPL | PathLengthM_mean | CandidateVisits_mean |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in aligned_rows:
        if row["metric_scope"] in {
            "h001_task_context_aligned",
            "h001_source_ready_subset",
            "h001_source_gap_subset",
            "detector_task_context_replicated",
        }:
            lines.append(
                "| {metric_scope} | {method_id} | {rows} | {success_rows} | {SR:.6f} | {SPL:.6f} | {PathLengthM_mean:.6f} | {CandidateVisits_mean:.6f} |".format(
                    **row
                )
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- M32 supports execution plumbing and leakage-safe metric use, but not an H001 navigation improvement claim.",
            "- The current H001 fallback matches proxy success exactly, but trajectory `SPL` is substantially lower than the proxy `SPL`.",
            "- The 9 source-gap rows fail under H001 execution while detector trajectories succeed on the same episode denominator; this is a candidate-source / stale-task construction issue.",
            "- The current `HM3D ObjectNav` setup is useful for navigation execution plumbing, but it does not yet encode dynamic stale semantic memory as a controlled intervention.",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}`: {row['status']} - {row['safe_claim']}")
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            f"- Selected next unit: {route_rows[0]['selected_next_unit']}.",
            f"- Decision: `{route_rows[0]['decision']}`.",
            f"- Reason: {route_rows[0]['reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m22_cov = read_json(M22_DIR / "coverage.json")
    m32_cov = read_json(M32_DIR / "coverage.json")
    m22_rows = read_jsonl(M22_DIR / "trajectory_policy_metric_rows.jsonl")
    m32_rows = read_jsonl(M32_DIR / "trajectory_policy_metric_rows.jsonl")
    m32_proxy_delta_rows = read_jsonl(M32_DIR / "proxy_trajectory_delta_rows.jsonl")
    m30_cov = read_json(M30_DIR / "coverage.json")

    denominator_rows = build_denominator_alignment_rows(m22_rows, m32_rows)
    aligned_rows = build_aligned_metric_rows(m22_rows, m32_rows)
    pairwise_rows = build_pairwise_delta_rows(aligned_rows)
    proxy_rows = build_proxy_execution_rows(m32_proxy_delta_rows, m32_rows)
    claim_rows = build_claim_boundary_rows(pairwise_rows, proxy_rows)
    route_rows = build_route_decision_rows()

    primary_pair = next(
        (
            row
            for row in pairwise_rows
            if row["comparison_scope"] == "all_task_context_rows"
            and row["baseline_method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    source_gap_primary = next(
        (
            row
            for row in pairwise_rows
            if row["comparison_scope"] == "h001_source_gap_subset"
            and row["baseline_method_id"] == PRIMARY_DETECTOR_POLICY
        ),
        {},
    )
    coverage = {
        "version": VERSION,
        "status": "e008_m33_h001_trajectory_result_interpretation_baseline_alignment_ready",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "m22_status": m22_cov.get("status"),
        "m30_status": m30_cov.get("status"),
        "m32_status": m32_cov.get("status"),
        "m22_scan_policy_metric_rows": m22_cov.get("scan_policy_metric_rows"),
        "m32_scan_task_metric_rows": m32_cov.get("scan_task_metric_rows"),
        "denominator_alignment_rows": len(denominator_rows),
        "aligned_metric_rows": len(aligned_rows),
        "pairwise_delta_rows": len(pairwise_rows),
        "proxy_execution_interpretation_rows": len(proxy_rows),
        "claim_boundary_rows": len(claim_rows),
        "route_decision_rows": len(route_rows),
        "primary_detector_policy": PRIMARY_DETECTOR_POLICY,
        "h001_minus_primary_detector_SR": primary_pair.get("h001_minus_baseline_SR"),
        "h001_minus_primary_detector_SPL": primary_pair.get("h001_minus_baseline_SPL"),
        "source_gap_h001_SR": source_gap_primary.get("h001_SR"),
        "source_gap_detector_SR": source_gap_primary.get("baseline_SR"),
        "m32_proxy_trajectory_success_agreement_rows": m32_cov.get("proxy_trajectory_success_agreement_rows"),
        "m32_proxy_success_trajectory_failure_rows": m32_cov.get("proxy_success_trajectory_failure_rows"),
        "m32_proxy_failure_trajectory_success_rows": m32_cov.get("proxy_failure_trajectory_success_rows"),
        "baseline_alignment_ready": True,
        "h001_navigation_improvement_claim_ready": False,
        "dynamic_stale_navigation_benchmark_needed": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "denominator_alignment_rows.jsonl", denominator_rows)
    write_jsonl(ARTIFACT_DIR / "aligned_navigation_metric_rows.jsonl", aligned_rows)
    write_jsonl(ARTIFACT_DIR / "pairwise_baseline_delta_rows.jsonl", pairwise_rows)
    write_jsonl(ARTIFACT_DIR / "proxy_execution_interpretation_rows.jsonl", proxy_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "aligned_navigation_metric_rows.jsonl", aligned_rows)
    write_jsonl(DATA_OUT_DIR / "pairwise_baseline_delta_rows.jsonl", pairwise_rows)
    write_jsonl(DATA_OUT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, aligned_rows, pairwise_rows, proxy_rows, claim_rows, route_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
