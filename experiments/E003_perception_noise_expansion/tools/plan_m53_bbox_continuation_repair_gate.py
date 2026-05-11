#!/usr/bin/env python3
"""Plan the E003-M53 bbox-depth continuation and repair route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M36_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M36_recall_preserving_suppression_sweep_v0"
DEFAULT_M37_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M37_suppression_split_validation_v0"
DEFAULT_M38_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M38_split_or_temporal_spatial_gate_v0"
DEFAULT_M46_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M46_score_redesign_or_external_gate_v0"
DEFAULT_M47_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M47_external_baseline_feasibility_gate_v0"
DEFAULT_M52_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M52_grounded_sam_mask_failure_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M53_bbox_continuation_repair_gate_v0"
M53_VERSION = "e003_m53_bbox_continuation_repair_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def score_route(row: dict[str, Any]) -> int:
    return (
        3 * int(row["current_artifact_fit"])
        + 3 * int(row["claim_relevance"])
        + 2 * int(row["reviewer_defense_value"])
        + 2 * int(row["top_tier_path_value"])
        - 2 * int(row["implementation_burden"])
        - int(row["dependency_risk"])
        - int(row["scope_drift_risk"])
    )


def get_m47_route(m47: dict[str, Any], name: str) -> dict[str, Any]:
    for row in m47.get("candidate_routes", []):
        if row.get("external_route") == name:
            return row
    return {}


def build_external_reason_rows(m47: dict[str, Any]) -> list[dict[str, Any]]:
    openmask = get_m47_route(m47, "OpenMask3D")
    conceptgraphs = get_m47_route(m47, "ConceptGraphs")
    hovsg = get_m47_route(m47, "HOV-SG")
    ovir = get_m47_route(m47, "OVIR-3D")
    return [
        {
            "baseline": "OpenMask3D",
            "immediate_role": "later_external_3d_instance_proposal_baseline",
            "reason_to_keep": "It directly tests whether 3D open-vocabulary instance masks reduce proposal false positives better than 2D bbox/mask-depth projection.",
            "reason_not_immediate": "M52 only showed the current Grounded-SAM route should not scale; the current best bbox-depth route still needs a defensible failure-boundary bridge before another heavy external dependency.",
            "m47_score": openmask.get("feasibility_score"),
            "output_fit": openmask.get("output_fit"),
        },
        {
            "baseline": "Open3DSG",
            "immediate_role": "later_scene_graph_mapping_baseline",
            "reason_to_keep": "It is relevant when the paper compares semantic map or scene-graph representation quality.",
            "reason_not_immediate": "The current blocker is proposal-row false positives and target dropout under real RGB-D/open-vocabulary output, not 3D scene graph construction quality.",
            "m47_score": None,
            "output_fit": "Scene graph/map representation baseline; needs a separate adapter to the current proposal-row and dynamic search schema.",
        },
        {
            "baseline": "ConceptGraphs",
            "immediate_role": "later_open_vocabulary_mapping_baseline",
            "reason_to_keep": "It is a strong object-centric open-vocabulary mapping baseline for semantic map comparison.",
            "reason_not_immediate": "It is a mapping stack, not the smallest test for the current bbox-depth proposal failure boundary.",
            "m47_score": conceptgraphs.get("feasibility_score"),
            "output_fit": conceptgraphs.get("output_fit"),
        },
        {
            "baseline": "HOV-SG",
            "immediate_role": "later_hierarchical_mapping_navigation_baseline",
            "reason_to_keep": "It is relevant for hierarchical open-vocabulary scene graph and navigation/search claims.",
            "reason_not_immediate": "Navigation/hierarchy claims are still blocked by real navigation source and downstream benchmark integration.",
            "m47_score": hovsg.get("feasibility_score"),
            "output_fit": hovsg.get("output_fit"),
        },
        {
            "baseline": "OVIR-3D",
            "immediate_role": "fallback_3d_retrieval_baseline",
            "reason_to_keep": "It may provide a 3D instance retrieval route if OpenMask3D is blocked.",
            "reason_not_immediate": "Its retrieval-oriented output is less direct for proposal precision/recall and stale-memory search rows.",
            "m47_score": ovir.get("feasibility_score"),
            "output_fit": ovir.get("output_fit"),
        },
    ]


def build_routes(
    m33: dict[str, Any],
    m36: dict[str, Any],
    m37: dict[str, Any],
    m38: dict[str, Any],
    m46: dict[str, Any],
    m47: dict[str, Any],
    m52: dict[str, Any],
) -> list[dict[str, Any]]:
    openmask = get_m47_route(m47, "OpenMask3D")
    conceptgraphs = get_m47_route(m47, "ConceptGraphs")
    hovsg = get_m47_route(m47, "HOV-SG")
    routes = [
        {
            "claim_relevance": 5,
            "current_artifact_fit": 5,
            "dependency_risk": 0,
            "evidence_basis": [
                f"M33 scaled bbox-depth artifact covers {m33.get('evaluated_scan_count')} scans and {m33.get('evaluated_frame_count')} frames.",
                f"M33 has {m33.get('matched_target_rows')} matched targets and {m33.get('false_positive_proposal_rows')} false-positive rows.",
                "M52 shows Grounded-SAM should not scale as-is, so the current best route is still bbox-depth.",
                "M36/M37/M38 show generic suppression, split selection, and simple support-aware fixes are not claim-ready.",
            ],
            "implementation_burden": 1,
            "main_risk": "may only produce a tighter claim boundary unless it identifies a search-critical subset where detector failures matter",
            "next_unit": "E003-M54 search-critical bbox-depth failure-boundary audit",
            "reviewer_defense_value": 5,
            "route_id": "search_critical_bbox_failure_boundary_first",
            "route_type": "current_best_route_defense_and_repair",
            "scope_drift_risk": 0,
            "top_tier_path_value": 4,
        },
        {
            "claim_relevance": 4,
            "current_artifact_fit": 4,
            "dependency_risk": 1,
            "evidence_basis": [
                f"M36 diagnostic policy keeps {m36.get('selected_diagnostic_policy', {}).get('matched_target_rows')} matched targets and reduces false positives to {m36.get('selected_diagnostic_policy', {}).get('false_positive_proposal_rows')}.",
                f"M37 dev-selected policy transfers poorly: heldout matched targets {m37.get('selected_candidate_policy', {}).get('matched_target_rows')} / {m37.get('heldout_baseline_policy', {}).get('matched_target_rows')}.",
                "A deployable repair must avoid labelwise overfitting and preserve visible-proxy recall.",
            ],
            "implementation_burden": 3,
            "main_risk": "more proposal filtering may repeat M36/M37 overfit and M45/M46 support-score failure",
            "next_unit": "E003-M54 deployable bbox-depth suppression repair smoke",
            "reviewer_defense_value": 4,
            "route_id": "deployable_bbox_suppression_repair_now",
            "route_type": "proposal_filter_repair",
            "scope_drift_risk": 1,
            "top_tier_path_value": 3,
        },
        {
            "claim_relevance": 4,
            "current_artifact_fit": int(openmask.get("current_harness_fit", 3) or 3),
            "dependency_risk": int(openmask.get("dependency_risk", 4) or 4),
            "evidence_basis": [
                "OpenMask3D is the strongest later 3D instance proposal baseline candidate in M47.",
                "It is more directly comparable to proposal precision/recall than map-level baselines.",
                "M52 says Grounded-SAM should not scale, but it does not prove all external 3D instance baselines should be skipped.",
            ],
            "implementation_burden": int(openmask.get("implementation_burden", 4) or 4),
            "main_risk": openmask.get("main_risk", "external dependency and scene-format burden"),
            "next_unit": "E003-M54 OpenMask3D scene-format feasibility gate",
            "reviewer_defense_value": 5,
            "route_id": "openmask3d_feasibility_now",
            "route_type": "external_3d_instance_baseline",
            "scope_drift_risk": 2,
            "top_tier_path_value": 5,
        },
        {
            "claim_relevance": 3,
            "current_artifact_fit": 2,
            "dependency_risk": 3,
            "evidence_basis": [
                "Open3DSG is relevant to scene-graph/map representation comparison.",
                "The current E003 blocker is detector proposal false positives and target dropout, not scene graph construction.",
                "It needs a separate adapter from scene graph outputs to dynamic object search rows.",
            ],
            "implementation_burden": 4,
            "main_risk": "high chance of shifting from current E003 proposal failure into a separate representation benchmark",
            "next_unit": "E005 scene-graph mapping baseline planning",
            "reviewer_defense_value": 4,
            "route_id": "open3dsg_mapping_baseline_now",
            "route_type": "scene_graph_mapping_baseline",
            "scope_drift_risk": 4,
            "top_tier_path_value": 4,
        },
        {
            "claim_relevance": 3,
            "current_artifact_fit": int(conceptgraphs.get("current_harness_fit", 3) or 3),
            "dependency_risk": int(conceptgraphs.get("dependency_risk", 5) or 5),
            "evidence_basis": [
                "ConceptGraphs is relevant for object-centric open-vocabulary mapping comparison.",
                "Its strongest role is a map baseline after the stale-memory/search evaluation bridge is stable.",
                "It is not the smallest repair for the current proposal-row false-positive boundary.",
            ],
            "implementation_burden": int(conceptgraphs.get("implementation_burden", 5) or 5),
            "main_risk": conceptgraphs.get("main_risk", "heavy mapping stack before proposal failure is stabilized"),
            "next_unit": "E005 ConceptGraphs mapping baseline adapter planning",
            "reviewer_defense_value": 5,
            "route_id": "conceptgraphs_mapping_baseline_now",
            "route_type": "open_vocabulary_mapping_baseline",
            "scope_drift_risk": 4,
            "top_tier_path_value": 5,
        },
        {
            "claim_relevance": 2,
            "current_artifact_fit": int(hovsg.get("current_harness_fit", 2) or 2),
            "dependency_risk": int(hovsg.get("dependency_risk", 5) or 5),
            "evidence_basis": [
                "HOV-SG is relevant for hierarchical open-vocabulary scene graph and navigation/search claims.",
                "Real navigation SR/SPL remains unsupported in the current workspace.",
                "It is better suited after E004/E005 task and navigation benchmark integration.",
            ],
            "implementation_burden": int(hovsg.get("implementation_burden", 5) or 5),
            "main_risk": hovsg.get("main_risk", "too broad before navigation/hierarchy claims are active"),
            "next_unit": "E005 HOV-SG navigation/mapping baseline planning",
            "reviewer_defense_value": 4,
            "route_id": "hovsg_navigation_mapping_baseline_now",
            "route_type": "hierarchical_mapping_navigation_baseline",
            "scope_drift_risk": 5,
            "top_tier_path_value": 5,
        },
    ]
    for row in routes:
        row["feasibility_score"] = score_route(row)
        row["m52_scaled_grounded_sam_recommended"] = bool(
            m52.get("diagnosis", {}).get("scaled_grounded_sam_recommended")
        )
        row["m46_best_policy"] = (m46.get("route_decision") or {}).get("best_policy_by_matched_fp_precision", {}).get(
            "policy_id"
        )
        row["m38_support_transfer_pass"] = bool(m38.get("support_transfer_pass"))
    return sorted(routes, key=lambda row: row["feasibility_score"], reverse=True)


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_route"]
    m33 = coverage["evidence_summary"]["m33"]
    m52 = coverage["evidence_summary"]["m52"]
    lines = [
        "# E003-M53 Bbox-Depth Continuation Repair Gate",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- M33 scaled bbox-depth: {m33['evaluated_scan_count']} scans / {m33['evaluated_frame_count']} frames.",
        f"- M33 matched / FP / precision: {m33['matched_target_rows']} / {m33['false_positive_proposal_rows']} / {m33['proposal_precision']}.",
        f"- M52 scaled `Grounded-SAM` recommended: {m52['scaled_grounded_sam_recommended']}.",
        f"- M52 target loss cause: `{m52['target_loss_primary_cause']}`.",
        f"- Selected immediate route: `{selected['route_id']}`.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in coverage["candidate_routes"]:
        lines.append(
            f"- `{row['route_id']}`: score {row['feasibility_score']}, "
            f"type `{row['route_type']}`, next `{row['next_unit']}`."
        )
    lines.extend(
        [
            "",
            "## External Baseline Boundary",
            "",
        ]
    )
    for row in coverage["external_baseline_boundary"]:
        lines.append(
            f"- `{row['baseline']}`: role `{row['immediate_role']}`; "
            f"not immediate: {row['reason_not_immediate']}"
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M53 does not create a paper result claim.",
            "- It fixes the immediate route after negative `Grounded-SAM` evidence.",
            "- Real RGB-D/open-vocabulary robustness remains unsupported.",
            "",
            "## 에이전트 추론",
            "",
            "- The next step should not be another heavy external baseline before the current best bbox-depth route has a search-critical failure boundary.",
            "- `OpenMask3D` is a better external proposal-quality baseline than `Open3DSG`, `ConceptGraphs`, or `HOV-SG` for this specific E003 failure, but it is still not the immediate next unit.",
            "- `Open3DSG`, `ConceptGraphs`, and `HOV-SG` are more appropriate for later map/scene-graph/navigation baseline expansion.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if E003-M54 search-critical bbox-depth failure-boundary audit is accepted as the next immediate unit.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m36-dir", default=DEFAULT_M36_DIR, type=Path)
    parser.add_argument("--m37-dir", default=DEFAULT_M37_DIR, type=Path)
    parser.add_argument("--m38-dir", default=DEFAULT_M38_DIR, type=Path)
    parser.add_argument("--m46-dir", default=DEFAULT_M46_DIR, type=Path)
    parser.add_argument("--m47-dir", default=DEFAULT_M47_DIR, type=Path)
    parser.add_argument("--m52-dir", default=DEFAULT_M52_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m33 = load_json(args.m33_dir / "coverage.json")
    m36 = load_json(args.m36_dir / "coverage.json")
    m37 = load_json(args.m37_dir / "coverage.json")
    m38 = load_json(args.m38_dir / "coverage.json")
    m46 = load_json(args.m46_dir / "coverage.json")
    m47 = load_json(args.m47_dir / "coverage.json")
    m52 = load_json(args.m52_dir / "coverage.json")
    routes = build_routes(m33=m33, m36=m36, m37=m37, m38=m38, m46=m46, m47=m47, m52=m52)
    selected = routes[0]
    external_boundary = build_external_reason_rows(m47)
    coverage = {
        "candidate_routes": routes,
        "evidence_summary": {
            "m33": {
                "evaluated_frame_count": m33.get("evaluated_frame_count"),
                "evaluated_scan_count": m33.get("evaluated_scan_count"),
                "false_positive_proposal_rows": m33.get("false_positive_proposal_rows"),
                "matched_target_rows": m33.get("matched_target_rows"),
                "proposal_precision": m33.get("proposal_precision"),
                "real_rgbd_or_open_vocab_claim_ready": m33.get("real_rgbd_or_open_vocab_claim_ready"),
                "visibility_proxy_is_true_visibility": m33.get("visibility_proxy_is_true_visibility"),
            },
            "m36": {
                "diagnostic_policy": (m36.get("selected_diagnostic_policy") or {}).get("policy_id"),
                "selected_deployable_policy": (m36.get("selected_deployable_95pct_policy") or {}).get("policy_id"),
                "split_validation_required": m36.get("split_validation_required"),
            },
            "m37": {
                "label_stratified_validation_feasible": m37.get("label_stratified_validation_feasible"),
                "runner_integration_recommended": m37.get("runner_integration_recommended"),
                "selected_candidate_retention": (m37.get("selected_candidate_policy") or {}).get(
                    "matched_target_retention_vs_m33"
                ),
            },
            "m38": {
                "stronger_split_feasible_with_current_scans": m38.get("stronger_split_feasible_with_current_scans"),
                "support_transfer_pass": m38.get("support_transfer_pass"),
            },
            "m46": {
                "hard_pass_policy_count": (m46.get("route_decision") or {}).get("hard_pass_policy_count"),
                "weak_positive_policy_count": (m46.get("route_decision") or {}).get("weak_positive_policy_count"),
            },
            "m52": {
                "scaled_grounded_sam_recommended": (m52.get("diagnosis") or {}).get(
                    "scaled_grounded_sam_recommended"
                ),
                "target_loss_primary_cause": (m52.get("diagnosis") or {}).get("target_loss_primary_cause"),
            },
        },
        "external_baseline_boundary": external_boundary,
        "m53_version": M53_VERSION,
        "next_recommended_unit": selected["next_unit"],
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "selected_route": selected,
        "status": "bbox_continuation_repair_gate_ready",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", selected)
    write_jsonl(args.out_dir / "candidate_routes.jsonl", routes)
    write_jsonl(args.out_dir / "external_baseline_boundary.jsonl", external_boundary)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
