#!/usr/bin/env python3
"""Decide the next real RGB-D / open-vocabulary robustness route."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M67_real_rgbd_ov_robustness_route_v0"
VERSION = "e005_m67_real_rgbd_ov_robustness_route_v0"

M45_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M55_COVERAGE = EXP_ROOT / "artifacts" / "E005-M55_real_rgbd_ov_robustness_gate_v0" / "coverage.json"
M66_COVERAGE = EXP_ROOT / "artifacts" / "E005-M66_external_baseline_failure_boundary_v0" / "coverage.json"
M75_COVERAGE = E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0" / "coverage.json"
M75_METRICS = E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0" / "metrics.json"

M45_TARGET_FILES = [
    M45_DIR / "target_rows.jsonl",
    M45_DIR / "target_rows_heldout_b02.jsonl",
    M45_DIR / "target_rows_heldout_b03.jsonl",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def m45_denominator_summary() -> dict[str, Any]:
    target_rows: list[dict[str, Any]] = []
    for path in M45_TARGET_FILES:
        target_rows.extend(read_jsonl(path))
    query_uids = {
        query_uid
        for row in target_rows
        for query_uid in row.get("bridge_query_row_uids", [])
    }
    scan_ids = {str(row.get("scan_id")) for row in target_rows if row.get("scan_id")}
    labels = {str(row.get("label_canonical")) for row in target_rows if row.get("label_canonical")}
    target_uids = {str(row.get("target_uid")) for row in target_rows if row.get("target_uid")}
    return {
        "target_rows": len(target_rows),
        "query_rows": len(query_uids),
        "scan_count": len(scan_ids),
        "label_count": len(labels),
        "target_uid_count": len(target_uids),
        "scan_ids": sorted(scan_ids),
        "labels": sorted(labels),
    }


def score_routes(m45: dict[str, Any], m75_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    bounded = m75_metrics.get("policy_metrics", {}).get("bounded_old_memory_distance_guard_adaptive_top5_v0", {})
    detector_top5 = m75_metrics.get("policy_metrics", {}).get("detector_top5_v0", {})
    return [
        {
            "route_id": "scale_real_proposal_bridge_to_m38_heldout_denominator",
            "score": 64,
            "selected": True,
            "route_type": "real_rgbd_open_vocab_robustness_table",
            "next_unit": "E005-M68 full-denominator real RGB-D proposal bridge plan",
            "why": [
                "M66 makes the proxy-search external-baseline boundary defensible.",
                "The current weakness is denominator mismatch: proxy-search table has 195 rows, while E003-M75 real-proposal bridge has 96 rows.",
                "Scaling the real proposal bridge to the M38/M45 heldout denominator is the shortest path to a real RGB-D/open-vocabulary robustness table.",
                "The route preserves the current H001 claim focus: memory trust, stale-memory recovery, re-observation budget, and search cost.",
            ],
            "risk": "moderate_high",
            "requires_background_job": True,
            "expected_denominator_rows": m45["query_rows"],
        },
        {
            "route_id": "openmask3d_proposal_baseline_repair",
            "score": 43,
            "selected": False,
            "route_type": "external_3d_instance_proposal_baseline",
            "next_unit": "Later OpenMask3D Docker/MinkowskiEngine repair if detector proposal quality becomes the main reviewer blocker",
            "why": [
                "`OpenMask3D` is useful for proposal-quality pressure.",
                "It is still blocked by Docker / `MinkowskiEngine`, so it should not precede a denominator-alignment route.",
                "A repaired `OpenMask3D` row should be added after the M38/M45 real-proposal denominator is fixed.",
            ],
            "risk": "high",
            "requires_background_job": True,
            "expected_denominator_rows": None,
        },
        {
            "route_id": "hov_sg_or_conceptgraphs_navigation_audit",
            "score": 35,
            "selected": False,
            "route_type": "broader_mapping_navigation_baseline",
            "next_unit": "Later map-navigation baseline audit after real proposal robustness table is stable",
            "why": [
                "`HOV-SG` / `ConceptGraphs` navigation routes support the broader Direction B story.",
                "They are heavier system baselines and should not be used to hide current real-proposal denominator gaps.",
            ],
            "risk": "high",
            "requires_background_job": False,
            "expected_denominator_rows": None,
        },
        {
            "route_id": "real_navigation_sr_spl_now",
            "score": 22,
            "selected": False,
            "route_type": "navigation_execution",
            "next_unit": "E007 after real RGB-D/open-vocabulary robustness table and simulator/navmesh contract are ready",
            "why": [
                "Real navigation `SR` / `SPL` needs simulator/navmesh/trajectory execution.",
                "Starting it before robustness denominator alignment would mix two unsupported claims.",
            ],
            "risk": "high",
            "requires_background_job": True,
            "expected_denominator_rows": None,
        },
        {
            "route_id": "human_intent_main_claim_upgrade",
            "score": 16,
            "selected": False,
            "route_type": "context_sensitive_utility_benchmark",
            "next_unit": "Optional E006 only if human intent is promoted beyond secondary ablation",
            "why": [
                "M66 shows only 1 task-context-specific success gain over context-agnostic memory trust.",
                "Human intent should remain structured task context unless a new context-sensitive utility benchmark is created.",
            ],
            "risk": "moderate",
            "requires_background_job": False,
            "expected_denominator_rows": None,
        },
    ]


def build_requirements(
    m45: dict[str, Any],
    m55: dict[str, Any],
    m66: dict[str, Any],
    m75: dict[str, Any],
    m75_metrics: dict[str, Any],
) -> dict[str, Any]:
    bounded = m75_metrics.get("policy_metrics", {}).get("bounded_old_memory_distance_guard_adaptive_top5_v0", {})
    detector_top5 = m75_metrics.get("policy_metrics", {}).get("detector_top5_v0", {})
    unbounded = m75_metrics.get("policy_metrics", {}).get("unbounded_old_memory_distance_guard_until_target_v0", {})
    return {
        "m67_goal": "turn the proxy-search external-baseline boundary into a real RGB-D/open-vocabulary robustness route",
        "inputs": {
            "m55_status": m55.get("status"),
            "m66_status": m66.get("status"),
            "m75_status": m75.get("status"),
            "m45_query_rows": m45["query_rows"],
            "m45_scan_count": m45["scan_count"],
            "m45_target_rows": m45["target_rows"],
            "m75_query_rows": m75.get("direct_bridge_query_rows"),
            "m75_target_detected_rows": m75.get("query_target_detected_rows"),
        },
        "current_gap": {
            "denominator_mismatch_rows": int(m45["query_rows"]) - int(m75.get("direct_bridge_query_rows", 0)),
            "m75_bounded_repair_success_rows": bounded.get("query_bridge_success_rows"),
            "m75_detector_top5_success_rows": detector_top5.get("query_bridge_success_rows"),
            "m75_unbounded_upper_bound_success_rows": unbounded.get("query_bridge_success_rows"),
            "m66_h001_only_vs_conceptgraphs": m66.get("pair_outcome_counts", {})
            .get("h001_vs_conceptgraphs", {})
            .get("task_context_memory_trust_reobserve_v0_only"),
            "m66_h001_only_vs_open3dsg_vocab": m66.get("pair_outcome_counts", {})
            .get("h001_vs_open3dsg_vocab", {})
            .get("task_context_memory_trust_reobserve_v0_only"),
            "m66_task_context_gain_rows": m66.get("human_intent_boundary_counts", {}).get("task_context_specific_gain"),
        },
        "m68_minimum_contract": [
            "Use the M38/M45 heldout query denominator or explicitly mark any missing rows.",
            "Reuse E003-M75 policy schema so `detector_top1/top3/top5`, bounded memory repair, unbounded upper bound, and oracle upper bound stay comparable.",
            "Record per-query target detection, target rank, false-positive-before-target, `ExpectedSearchCost`, `AttemptSPL`, and old-location dead-end cost.",
            "Keep query labels, target geometry, and success labels blocked from policy ranking except in oracle/analysis rows.",
            "Launch detector/proposal extraction as a background job with timestamped logs if runtime is required.",
            "Do not claim real navigation `SR` / `SPL`; this is still a search/proposal robustness bridge.",
        ],
        "claim_boundary_after_m67": {
            "proxy_search_external_baseline_claim": "ready_with_proxy_boundary",
            "final_real_rgbd_open_vocab_robustness": "not_ready_until_m68_or_later",
            "real_navigation_sr_spl": "blocked",
            "human_intent_main_claim": "blocked_secondary_ablation_only",
        },
    }


def build_report(coverage: dict[str, Any], routes: list[dict[str, Any]], requirements: dict[str, Any]) -> str:
    selected = next(row for row in routes if row["selected"])
    return "\n".join(
        [
            "# E005-M67 Real RGB-D / Open-Vocabulary Robustness Route",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M38/M45 heldout denominator: {coverage['m45_query_rows']} query rows, {coverage['m45_scan_count']} scans, {coverage['m45_target_rows']} target rows.",
            f"- Current E003-M75 real-proposal denominator: {coverage['m75_query_rows']} query rows.",
            f"- Denominator mismatch: {coverage['denominator_mismatch_rows']} query rows.",
            f"- M75 bounded repair success: {coverage['m75_bounded_repair_success_rows']} / {coverage['m75_query_rows']}.",
            f"- M66 H001-only rows vs `ConceptGraphs`: {coverage['m66_h001_only_vs_conceptgraphs']}.",
            f"- M66 H001-only rows vs `Open3DSG` vocab: {coverage['m66_h001_only_vs_open3dsg_vocab']}.",
            f"- M66 task-context-specific gain rows: {coverage['m66_task_context_gain_rows']}.",
            "",
            "## Decision",
            "",
            f"- Selected route: `{selected['route_id']}`.",
            f"- Next unit: {selected['next_unit']}.",
            "- Keep final real RGB-D/open-vocabulary robustness blocked until the scaled real-proposal denominator is executed and evaluated.",
            "- Keep real navigation `SR` / `SPL` blocked until a simulator/navmesh/trajectory protocol exists.",
            "",
            "## Route Ranking",
            "",
            "| Route | Score | Selected | Risk | Next |",
            "| --- | ---: | --- | --- | --- |",
            *[
                f"| `{row['route_id']}` | {row['score']} | {str(row['selected']).lower()} | {row['risk']} | {row['next_unit']} |"
                for row in routes
            ],
            "",
            "## M68 Minimum Contract",
            "",
            *[f"- {item}" for item in requirements["m68_minimum_contract"]],
            "",
            "## Claim Boundary",
            "",
            "- M67 is a route decision, not a new performance result.",
            "- The paper can continue using M66 for proxy-search external-baseline boundary.",
            "- The next result that can upgrade the paper is a scaled real RGB-D/open-vocabulary robustness table on the M38/M45 denominator.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m45 = m45_denominator_summary()
    m55 = read_json(M55_COVERAGE)
    m66 = read_json(M66_COVERAGE)
    m75 = read_json(M75_COVERAGE)
    m75_metrics = read_json(M75_METRICS)
    if m55.get("status") != "e005_m55_real_rgbd_ov_robustness_gate_ready":
        raise RuntimeError(f"M55 is not ready: {m55.get('status')}")
    if m66.get("status") != "e005_m66_external_baseline_failure_boundary_ready":
        raise RuntimeError(f"M66 is not ready: {m66.get('status')}")
    if m75.get("status") != "expanded_direct_query_bridge_ready":
        raise RuntimeError(f"E003-M75 is not ready: {m75.get('status')}")
    if m45["query_rows"] != 195:
        raise RuntimeError(f"unexpected M45 denominator rows: {m45['query_rows']}")

    routes = score_routes(m45, m75_metrics)
    selected = next(row for row in routes if row["selected"])
    requirements = build_requirements(m45, m55, m66, m75, m75_metrics)
    gap = requirements["current_gap"]
    coverage = {
        "status": "e005_m67_real_rgbd_ov_robustness_route_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_dir": str(OUT_DIR),
        "selected_route": selected["route_id"],
        "next_recommended_unit": selected["next_unit"],
        "m45_query_rows": m45["query_rows"],
        "m45_scan_count": m45["scan_count"],
        "m45_target_rows": m45["target_rows"],
        "m75_query_rows": m75.get("direct_bridge_query_rows"),
        "m75_target_detected_rows": m75.get("query_target_detected_rows"),
        "denominator_mismatch_rows": gap["denominator_mismatch_rows"],
        "m75_bounded_repair_success_rows": gap["m75_bounded_repair_success_rows"],
        "m75_detector_top5_success_rows": gap["m75_detector_top5_success_rows"],
        "m75_unbounded_upper_bound_success_rows": gap["m75_unbounded_upper_bound_success_rows"],
        "m66_h001_only_vs_conceptgraphs": gap["m66_h001_only_vs_conceptgraphs"],
        "m66_h001_only_vs_open3dsg_vocab": gap["m66_h001_only_vs_open3dsg_vocab"],
        "m66_task_context_gain_rows": gap["m66_task_context_gain_rows"],
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "human_intent_main_claim_ready": False,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "m45_denominator_summary.json", m45)
    write_json(OUT_DIR / "requirements.json", requirements)
    write_json(OUT_DIR / "selected_route.json", selected)
    write_jsonl(OUT_DIR / "route_rows.jsonl", routes)
    write_text(OUT_DIR / "report.md", build_report(coverage, routes, requirements))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
