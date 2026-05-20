#!/usr/bin/env python3
"""Plan the real RGB-D / open-vocabulary robustness expansion after M54."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
M54_DIR = EXP_ROOT / "artifacts" / "E005-M54_paper_table_claim_ledger_v0"
M75_DIR = E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
OPENMASK_BLOCKER_DIR = E003_ROOT / "artifacts" / "E003-M72_openmask3d_blocker_fallback_gate_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M55_real_rgbd_ov_robustness_gate_v0"
VERSION = "e005_m55_real_rgbd_ov_robustness_gate_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def score_routes(openmask: dict[str, Any]) -> list[dict[str, Any]]:
    openmask_blocked = openmask.get("status") == "openmask3d_blocked_direct_denominator_fallback_selected"
    routes = [
        {
            "route_id": "robustness_denominator_contract_then_open3dsg_audit",
            "score": 52,
            "selected": True,
            "route_type": "denominator_and_external_map_baseline",
            "rationale": [
                "M54 provides a proxy-search table, but robustness needs a separate denominator contract.",
                "E003-M75 provides a real RGB-D proposal bridge over 96 rows, but it is diagnostic and not a final robustness table.",
                "`Open3DSG` is closer to semantic mapping / 3D scene graph baselines than another detector-only tweak.",
                "This route avoids the current `OpenMask3D` Docker blocker while preparing a second map/scene-graph baseline.",
            ],
            "next_unit": "E005-M56 robustness denominator contract + Open3DSG source/interface audit",
            "risk": "moderate",
        },
        {
            "route_id": "openmask3d_environment_repair_and_model_smoke",
            "score": 34 if openmask_blocked else 44,
            "selected": False,
            "route_type": "external_3d_instance_proposal_baseline",
            "rationale": [
                "`OpenMask3D` is a strong proposal-quality baseline for detector-recall-miss rows.",
                "The current blocker is environment/dependency, not negative proposal-quality evidence.",
                "M72 records hard blockers: Docker build failure, `MinkowskiEngine` build requirement error, and missing image.",
                "It should be retried after the robustness denominator is fixed, not before.",
            ],
            "next_unit": "Later OpenMask3D Docker repair/model smoke if proposal-baseline evidence becomes the bottleneck",
            "risk": "high",
        },
        {
            "route_id": "hov_sg_mapping_navigation_audit",
            "score": 29,
            "selected": False,
            "route_type": "broader_mapping_navigation_baseline",
            "rationale": [
                "`HOV-SG` is useful for broader Direction B mapping-navigation positioning.",
                "It is heavier than a source/interface audit and may pull the work toward system integration too early.",
                "Use it after the second baseline/denominator contract clarifies the real RGB-D robustness claim.",
            ],
            "next_unit": "Later HOV-SG source/interface audit after Open3DSG or OpenMask3D route decision",
            "risk": "high",
        },
        {
            "route_id": "grounded_sam_scale",
            "score": 18,
            "selected": False,
            "route_type": "mask_depth_proposal_baseline",
            "rationale": [
                "E003-M50 showed `Grounded-SAM` mask-depth did not beat bbox-depth on the same subset.",
                "Scaling this route now risks spending compute on a known weaker geometry projection path.",
            ],
            "next_unit": "Do not scale unless a new mask projection repair is introduced",
            "risk": "moderate",
        },
        {
            "route_id": "real_navigation_sr_spl_bridge",
            "score": 12,
            "selected": False,
            "route_type": "navigation_claim_expansion",
            "rationale": [
                "Real navigation `SR` / `SPL` requires simulator/navmesh/trajectory execution.",
                "Starting navigation now would mix unready robustness and navigation claims.",
            ],
            "next_unit": "E007 after real RGB-D/open-vocabulary robustness becomes stable",
            "risk": "high",
        },
    ]
    return sorted(routes, key=lambda row: (-int(row["score"]), row["route_id"]))


def build_requirements(m54: dict[str, Any], m75: dict[str, Any], m75_metrics: dict[str, Any]) -> dict[str, Any]:
    bounded_metric = m75_metrics.get("policy_metrics", {}).get("bounded_old_memory_distance_guard_adaptive_top5_v0", {})
    return {
        "claim_to_upgrade": "final_real_rgbd_open_vocab_robustness",
        "current_status": "blocked",
        "ready_evidence": {
            "m54_proxy_search_table_ready": bool(m54.get("main_proxy_search_table_ready")),
            "conceptgraphs_heldout_proxy_rows": int(m54.get("query_rows", 0)),
            "h001_success_rows": int(m54.get("h001_success_rows", 0)),
            "conceptgraphs_success_rows": int(m54.get("conceptgraphs_success_rows", 0)),
            "e003_m75_real_proposal_rows": int(m75.get("direct_bridge_query_rows", 0)),
            "e003_m75_target_detected_rows": int(m75.get("query_target_detected_rows", 0)),
            "e003_m75_bounded_repair_success_rows": int(bounded_metric.get("query_bridge_success_rows", 0)),
        },
        "blocking_gaps": [
            "M54 proxy-search table and E003-M75 real-proposal bridge use different denominators.",
            "Only one mature external map baseline is ready: `ConceptGraphs`.",
            "Current real proposal bridge has low deployable policy success: bounded repair is 33 / 96 in E003-M75 metrics.",
            "The visibility denominator is still proxy-based, not true object visibility.",
            "`OpenMask3D` remains blocked by Docker / `MinkowskiEngine` environment compatibility.",
            "Real navigation `SR` / `SPL` has no simulator/navmesh/trajectory execution source yet.",
        ],
        "minimum_upgrade_requirements": [
            "Define a two-table robustness denominator: proxy-search external map table and real RGB-D proposal bridge table.",
            "Keep strict bbox, relaxed bbox, center localization, target detection, rank, false-positive-before-target, `ExpectedSearchCost`, and `AttemptSPL` separate.",
            "Add at least one additional external route beyond `ConceptGraphs` before writing final robustness language.",
            "Separate detector recall miss, rank/budget failure, false positive pushdown, localization error, and stale old-location failure.",
            "State that task context is secondary unless E006 is launched and passes context-sensitive utility gates.",
        ],
        "e003_m75_key_metrics": {
            "query_rows": m75_metrics.get("query_rows"),
            "query_target_detected_rows": m75_metrics.get("query_target_detected_rows"),
            "query_target_detected_rate": m75_metrics.get("query_target_detected_rate"),
            "bounded_repair_success_rows": bounded_metric.get("query_bridge_success_rows"),
            "bounded_repair_success_rate": bounded_metric.get("query_bridge_success_rate"),
            "mean_false_positive_before_target_when_detected": m75_metrics.get("mean_false_positive_before_target_when_detected"),
        },
    }


def build_report(coverage: dict[str, Any], routes: list[dict[str, Any]], requirements: dict[str, Any]) -> str:
    selected = next(row for row in routes if row["selected"])
    return "\n".join(
        [
            "# E005-M55 Real RGB-D / Open-Vocabulary Robustness Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- M54 proxy-search query rows: {coverage['m54_query_rows']}.",
            f"- H001 success rows: {coverage['h001_success_rows']}.",
            f"- `ConceptGraphs` success rows: {coverage['conceptgraphs_success_rows']}.",
            f"- E003-M75 real proposal bridge rows: {coverage['e003_m75_query_rows']}.",
            f"- E003-M75 target detected rows: {coverage['e003_m75_target_detected_rows']}.",
            f"- `OpenMask3D` currently blocked: {coverage['openmask3d_blocked']}.",
            "",
            "## Decision",
            "",
            f"- Selected route: `{selected['route_id']}`.",
            f"- Next unit: {selected['next_unit']}.",
            "- Do not claim final real RGB-D/open-vocabulary robustness yet.",
            "- Do not start real navigation `SR` / `SPL` before this robustness route is stable.",
            "",
            "## Route Ranking",
            "",
            "| Route | Score | Selected | Risk |",
            "| --- | ---: | --- | --- |",
            *[
                f"| `{row['route_id']}` | {row['score']} | {str(row['selected']).lower()} | {row['risk']} |"
                for row in routes
            ],
            "",
            "## Blocking Gaps",
            "",
            *[f"- {gap}" for gap in requirements["blocking_gaps"]],
            "",
            "## Minimum Upgrade Requirements",
            "",
            *[f"- {req}" for req in requirements["minimum_upgrade_requirements"]],
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m54 = read_json(M54_DIR / "coverage.json")
    m75 = read_json(M75_DIR / "coverage.json")
    m75_metrics = read_json(M75_DIR / "metrics.json")
    openmask = read_json(OPENMASK_BLOCKER_DIR / "coverage.json")

    if m54.get("status") != "e005_m54_paper_table_claim_ledger_ready":
        raise RuntimeError(f"M54 is not ready: {m54.get('status')}")
    if m75.get("status") != "expanded_direct_query_bridge_ready":
        raise RuntimeError(f"E003-M75 is not ready: {m75.get('status')}")

    routes = score_routes(openmask)
    selected = next(row for row in routes if row["selected"])
    requirements = build_requirements(m54, m75, m75_metrics)
    coverage = {
        "status": "e005_m55_real_rgbd_ov_robustness_gate_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m54_status": m54.get("status"),
        "e003_m75_status": m75.get("status"),
        "m54_query_rows": m54.get("query_rows"),
        "h001_success_rows": m54.get("h001_success_rows"),
        "conceptgraphs_success_rows": m54.get("conceptgraphs_success_rows"),
        "e003_m75_query_rows": m75.get("direct_bridge_query_rows"),
        "e003_m75_target_detected_rows": m75.get("query_target_detected_rows"),
        "openmask3d_blocked": openmask.get("status") == "openmask3d_blocked_direct_denominator_fallback_selected",
        "selected_route": selected["route_id"],
        "selected_next_unit": selected["next_unit"],
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "human_task_context_main_claim_ready": False,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "route_decision.json", selected)
    write_json(OUT_DIR / "robustness_requirements.json", requirements)
    write_jsonl(OUT_DIR / "candidate_routes.jsonl", routes)
    write_text(OUT_DIR / "report.md", build_report(coverage, routes, requirements))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
