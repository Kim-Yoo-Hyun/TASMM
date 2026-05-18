#!/usr/bin/env python3
"""Build the E005-M37 external baseline comparison and next-route decision."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M37_external_baseline_comparison_v0"
VERSION = "e005_m37_external_baseline_comparison_v0"

E003_M75_COVERAGE = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M75_expanded_direct_query_bridge_v0"
    / "coverage.json"
)
E003_M75_METRICS = E003_M75_COVERAGE.with_name("metrics.json")
E003_OPENMASK_BLOCKER = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M72_openmask3d_blocker_fallback_gate_v0"
    / "coverage.json"
)
E004_M05_DECISION = (
    ROOT
    / "experiments"
    / "E004_task_context_memory_trust"
    / "artifacts"
    / "E004-M05_scale_split_stress_v0"
    / "decision.json"
)
E004_M05_METRICS = E004_M05_DECISION.with_name("metrics.json")
E005_M19_COVERAGE = OUT_DIR.parents[0] / "E005-M19_dualmap_fallback_decision_v0" / "coverage.json"
E005_M35_METRICS = OUT_DIR.parents[0] / "E005-M35_conceptgraphs_4scan_query_metric_v0" / "metrics.json"
E005_M36_COVERAGE = OUT_DIR.parents[0] / "E005-M36_conceptgraphs_failure_boundary_v0" / "coverage.json"
E005_M36_AGGREGATE = OUT_DIR.parents[0] / "E005-M36_conceptgraphs_failure_boundary_v0" / "aggregate.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def nested_get(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def metric_line(success_rows: Any, rows: Any, rate: Any) -> str:
    if success_rows is None or rows is None or rate is None:
        return "not available"
    return f"{success_rows}/{rows} ({rate})"


def counts_line(counts: Any) -> str:
    if not isinstance(counts, dict) or not counts:
        return "not available"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def build_rows() -> list[dict[str, Any]]:
    e003_cov = read_json(E003_M75_COVERAGE)
    e003_metrics = read_json(E003_M75_METRICS)
    e004_decision = read_json(E004_M05_DECISION)
    e004_metrics = read_json(E004_M05_METRICS)
    dualmap = read_json(E005_M19_COVERAGE)
    openmask = read_json(E003_OPENMASK_BLOCKER)
    concept_m35 = read_json(E005_M35_METRICS)
    concept_m36_cov = read_json(E005_M36_COVERAGE)
    concept_m36 = read_json(E005_M36_AGGREGATE)

    e004_task = nested_get(
        e004_metrics,
        ["overall", "policy_metrics", "task_context_memory_trust_reobserve_v0"],
        {},
    )
    e004_static = nested_get(e004_metrics, ["overall", "policy_metrics", "static_memory_only_v0"], {})
    e003_bounded = nested_get(
        e003_metrics,
        ["policy_metrics", "bounded_old_memory_distance_guard_adaptive_top5_v0"],
        {},
    )
    e003_detector_budget = nested_get(e003_metrics, ["policy_metrics", "detector_task_budget_v0"], {})

    concept_primary = nested_get(concept_m36, ["suites", "primary_m60", "overall"], {})
    concept_expanded = nested_get(concept_m36, ["suites", "expanded_m73", "overall"], {})
    concept_primary_policy = nested_get(
        concept_m35,
        ["suites", "primary_m60", "policy_metrics", "conceptgraphs_clip_rank_bbox_strict_top5_v0"],
        {},
    )
    concept_expanded_policy = nested_get(
        concept_m35,
        ["suites", "expanded_m73", "policy_metrics", "conceptgraphs_clip_rank_bbox_strict_top5_v0"],
        {},
    )

    rows = [
        {
            "route": "H001 / E004 proposed route",
            "route_family": "proposed_task_aware_dynamic_semantic_memory",
            "role_in_paper": "core_method_not_external_baseline",
            "execution_state": "query_metric_ready_limited",
            "data_scale": f"{e004_metrics.get('query_rows', 96)} query rows / 4 staged scans",
            "query_level_metric_ready": True,
            "key_evidence": (
                "task_context_memory_trust_reobserve_v0 "
                f"{e004_task.get('success_rows')}/{e004_task.get('rows')} success; "
                f"static_memory_only_v0 {e004_static.get('success_rows')}/{e004_static.get('rows')} success; "
                f"E003 bounded direct bridge {e003_bounded.get('query_bridge_success_rows')}/{e003_bounded.get('rows')} success; "
                f"detector target detected {e003_cov.get('query_target_detected_rows')}/{e003_cov.get('direct_bridge_query_rows')}."
            ),
            "claim_status": "limited_positive_core_method_evidence",
            "reviewer_risk": (
                "Task-context effect is limited and detector/proposal quality is not yet a final open-vocabulary robustness claim."
            ),
            "next_action": "Keep as proposed method backbone; compare against external map baselines.",
            "paper_table_role": "main_method_row_after_scale",
        },
        {
            "route": "ConceptGraphs",
            "route_family": "open_vocabulary_mapping_baseline",
            "role_in_paper": "primary_external_mapping_baseline_candidate",
            "execution_state": "4scan_query_metric_ready_with_failure_boundary",
            "data_scale": (
                f"{concept_primary.get('rows')} primary M60 rows and "
                f"{concept_expanded.get('rows')} expanded M73 rows / 4 staged scans"
            ),
            "query_level_metric_ready": True,
            "key_evidence": (
                "primary strict bbox top5 "
                + metric_line(
                    concept_primary_policy.get("query_bridge_success_rows"),
                    concept_primary_policy.get("rows"),
                    concept_primary_policy.get("query_bridge_success_rate"),
                )
                + "; expanded strict bbox top5 "
                + metric_line(
                    concept_expanded_policy.get("query_bridge_success_rows"),
                    concept_expanded_policy.get("rows"),
                    concept_expanded_policy.get("query_bridge_success_rate"),
                )
                + f"; primary failure classes {counts_line(concept_primary.get('failure_class_counts'))}."
            ),
            "claim_status": "small_subset_external_baseline_ready_not_final",
            "reviewer_risk": (
                "Small staged subset, strict-vs-relaxed gap, label-specific success, and no heldout transfer yet."
            ),
            "next_action": "Scale/heldout ConceptGraphs first before adding a second heavy external route.",
            "paper_table_role": "first_external_mapping_baseline",
        },
        {
            "route": "DualMap",
            "route_family": "dynamic_semantic_mapping_baseline",
            "role_in_paper": "attempted_closest_dynamic_mapping_baseline",
            "execution_state": "runtime_ready_but_object_outputs_missing",
            "data_scale": f"{dualmap.get('m18_processed_keyframes')} processed keyframes in denser-stride retry",
            "query_level_metric_ready": False,
            "key_evidence": (
                f"M17/M18 pkl count {dualmap.get('m18_pkl_count')}; "
                f"layout.pcd count {dualmap.get('m18_layout_pcd_count')}; "
                f"local objects {dualmap.get('m18_first_local_object_count')} -> {dualmap.get('m18_final_local_object_count')}."
            ),
            "claim_status": "not_comparable_as_performance_baseline",
            "reviewer_risk": (
                "Reporting this as a failed performance result would be unfair; current evidence is an interface/output blocker."
            ),
            "next_action": "Do not spend another main step unless a faithful object-export path is found.",
            "paper_table_role": "implementation_attempt_or_appendix_only",
        },
        {
            "route": "OpenMask3D",
            "route_family": "external_3d_instance_proposal_baseline",
            "role_in_paper": "later_proposal_baseline_candidate",
            "execution_state": "docker_minkowskiengine_blocked",
            "data_scale": f"M60 direct bridge rows available: {openmask.get('m60_direct_bridge_query_rows')}",
            "query_level_metric_ready": False,
            "key_evidence": (
                f"image ready {openmask.get('image_ready')}; "
                f"blockers {[item.get('blocker') for item in openmask.get('blockers', [])]}."
            ),
            "claim_status": "blocked_not_a_current_external_baseline_result",
            "reviewer_risk": "Repairing this may become environment-heavy without directly fixing map-level baseline rigor.",
            "next_action": "Revisit after ConceptGraphs scale/heldout or use only as proposal-baseline branch.",
            "paper_table_role": "deferred_proposal_baseline",
        },
        {
            "route": "Open3DSG",
            "route_family": "open_vocabulary_3d_scene_graph_baseline",
            "role_in_paper": "second_external_scene_graph_baseline_candidate",
            "execution_state": "not_started_in_e005",
            "data_scale": "no local E005 result yet",
            "query_level_metric_ready": False,
            "key_evidence": "Relevant because it targets open-vocabulary 3D scene graph prediction on 3RScan-style data.",
            "claim_status": "candidate_only",
            "reviewer_risk": "Scene graph relation outputs may not directly answer search-cost or re-observation decisions.",
            "next_action": "Audit after ConceptGraphs scale if a second external map/scene-graph baseline is needed.",
            "paper_table_role": "second_external_baseline_candidate",
        },
        {
            "route": "HOV-SG / VLFM / HM3D-OVON",
            "route_family": "navigation_or_hierarchical_mapping_baseline",
            "role_in_paper": "later_navigation_system_baseline",
            "execution_state": "out_of_scope_for_current_e005_query_metric",
            "data_scale": "no local E005 result yet",
            "query_level_metric_ready": False,
            "key_evidence": "Needed for final real navigation SR/SPL claims, not for the current 3RScan query-level map baseline gate.",
            "claim_status": "future_direction_b_navigation_gate",
            "reviewer_risk": "Pulling navigation baselines in before map-level evidence may dilute the core semantic-memory claim.",
            "next_action": "Defer until map/query external baseline is stable and navigation episodes are defined.",
            "paper_table_role": "future_navigation_baseline",
        },
    ]

    # Attach source status without bloating the markdown table.
    rows[1]["m36_status"] = concept_m36_cov.get("status")
    rows[0]["e004_status"] = e004_decision.get("status")
    rows[0]["e004_claim_boundary"] = e004_decision.get("claim_boundary")
    rows[2]["dualmap_status"] = dualmap.get("status")
    rows[3]["openmask3d_status"] = openmask.get("status")
    rows[3]["openmask3d_next"] = openmask.get("selected_next_route")
    return rows


def build_decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "m37_version": VERSION,
        "status": "e005_m37_external_baseline_comparison_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "selected_next_route": "conceptgraphs_scale_heldout_first",
        "next_recommended_unit": "E005-M38 ConceptGraphs heldout/scale expansion plan",
        "external_baseline_table_ready": True,
        "paper_table_claim_ready": False,
        "go_no_go": {
            "conceptgraphs_as_first_external_mapping_baseline": True,
            "conceptgraphs_final_baseline_claim_ready": False,
            "dualmap_official_performance_baseline_ready": False,
            "openmask3d_proposal_baseline_ready": False,
            "navigation_sr_spl_baseline_ready": False,
        },
        "route_order": [
            {
                "order": 1,
                "route": "ConceptGraphs",
                "reason": "Only external map route with current 4-scan query-level metric and failure boundary.",
                "next_action": "Scale and define heldout scan/label split before using in main paper table.",
            },
            {
                "order": 2,
                "route": "Open3DSG",
                "reason": "Best second scene-graph/map baseline after ConceptGraphs scale, but not yet query-metric ready.",
                "next_action": "Audit interface after M38 if one additional external route is needed.",
            },
            {
                "order": 3,
                "route": "OpenMask3D",
                "reason": "Useful proposal baseline, but current local blocker is environment-heavy and not map-level.",
                "next_action": "Revisit only after map-level baseline rigor is no longer the bottleneck.",
            },
            {
                "order": 4,
                "route": "HOV-SG / VLFM / HM3D-OVON",
                "reason": "Relevant to final navigation SR/SPL, but requires a separate navigation episode setup.",
                "next_action": "Defer to the navigation-system stage.",
            },
            {
                "order": 5,
                "route": "DualMap",
                "reason": "Closest dynamic mapping baseline conceptually, but local faithful object-map outputs are missing.",
                "next_action": "Keep as attempted route unless official object-export recovery becomes available.",
            },
        ],
        "rows": rows,
    }


def build_report(decision: dict[str, Any]) -> str:
    rows = decision["rows"]
    lines = [
        "# E005-M37 External Baseline Comparison",
        "",
        "## Status",
        "",
        decision["status"],
        "",
        "## Comparison Table",
        "",
        "| Route | Role | Execution State | Query Metric Ready | Key Evidence | Claim Status | Next Action |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["route"],
                    row["role_in_paper"],
                    row["execution_state"],
                    str(row["query_level_metric_ready"]).lower(),
                    row["key_evidence"],
                    row["claim_status"],
                    row["next_action"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 사실",
            "",
            "- `ConceptGraphs` is the only external mapping route with current 4-scan query-level metrics.",
            "- `DualMap` reached runtime attempts but did not produce object `*.pkl` outputs for metric conversion.",
            "- `OpenMask3D` is blocked locally by Docker/MinkowskiEngine setup and has no current query-level result.",
            "- `H001 / E004 proposed route` has query-level evidence, but it is not an external baseline.",
            "",
            "## 논문 주장",
            "",
            "- Supported now: a bounded external-baseline claim that `ConceptGraphs` can be converted into the same query-level search metric interface.",
            "- Not supported now: final external baseline performance, final real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL`.",
            "",
            "## 에이전트 추론",
            "",
            "- The next highest-value step is not another heavy baseline launch; it is scaling `ConceptGraphs` with an explicit heldout scan/label contract.",
            "- `Open3DSG` is the next reasonable second external map/scene-graph route after `ConceptGraphs` scale because it is closer to 3D semantic map structure than navigation-only baselines.",
            "- `OpenMask3D` remains valuable for proposal quality, but it should not block the map-level comparison path right now.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before `E005-M38 ConceptGraphs heldout/scale expansion plan`.",
            "",
            "## Next Route Decision",
            "",
            f"- Selected next route: `{decision['selected_next_route']}`.",
            f"- Next recommended unit: `{decision['next_recommended_unit']}`.",
            "- Paper table claim ready: false.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    rows = build_rows()
    decision = build_decision(rows)
    coverage = {
        "m37_version": VERSION,
        "status": decision["status"],
        "generated_at": decision["generated_at"],
        "baseline_rows": len(rows),
        "external_baseline_table_ready": True,
        "conceptgraphs_query_metric_ready": True,
        "conceptgraphs_final_baseline_claim_ready": False,
        "dualmap_query_metric_ready": False,
        "openmask3d_query_metric_ready": False,
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "route_decision.json", decision)
    write_jsonl(OUT_DIR / "baseline_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
