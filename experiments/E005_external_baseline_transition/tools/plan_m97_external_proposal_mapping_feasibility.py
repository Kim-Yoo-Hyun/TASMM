#!/usr/bin/env python3
"""Build the E005-M97 external proposal/mapping baseline feasibility matrix."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M97_external_proposal_mapping_feasibility_v0"
VERSION = "e005_m97_external_proposal_mapping_feasibility_v0"

M96_DIR = EXP_ROOT / "artifacts" / "E005-M96_next_expansion_route_decision_v0"
M95_DIR = EXP_ROOT / "artifacts" / "E005-M95_real_proposal_paper_boundary_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M49_DIR = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0"
M64_DIR = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0"
M72_OPENMASK_DIR = E003_ROOT / "artifacts" / "E003-M72_openmask3d_blocker_fallback_gate_v0"


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


def docker_image_ready(image: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def path_ready(path: str | Path) -> bool:
    return Path(path).exists()


def build_matrix() -> list[dict[str, Any]]:
    m49 = read_json(M49_DIR / "coverage.json")
    m64 = read_json(M64_DIR / "coverage.json")
    m72_openmask = read_json(M72_OPENMASK_DIR / "coverage.json")

    conceptgraphs_repo = ROOT / "local_dataset" / "external_repos" / "concept-graphs"
    conceptgraphs_staged = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
    open3dsg_source = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
    open3dsg_bridge = ROOT / "local_dataset" / "Open3DSG_bridge"
    openmask_repo = E003_ROOT / "external" / "openmask3d"
    openmask_checkpoint = ROOT / "local_dataset" / "checkpoints" / "openmask3d" / "openmask3d_arbitrary_scene_model.ckpt"
    openmask_sam = ROOT / "local_dataset" / "checkpoints" / "openmask3d" / "sam_vit_h_4b8939.pth"
    hovsg_repo_candidates = [
        ROOT / "local_dataset" / "external_repos" / "HOV-SG",
        ROOT / "local_dataset" / "external_repos" / "hovsg",
        ROOT / "local_dataset" / "external_repos" / "hov-sg",
    ]
    hovsg_repo_ready = any(path.exists() for path in hovsg_repo_candidates)

    return [
        {
            "route_id": "conceptgraphs_derived_map_candidate_route",
            "rank": 1,
            "selected_for_first_smoke": True,
            "role": "external_open_vocabulary_mapping_baseline",
            "top_tier_value": "high",
            "engineering_burden": "low_to_medium",
            "denominator_alignment": "ready_195_rows",
            "local_data_ready": bool(m49.get("query_rows") == 195 and m49.get("scan_count") == 9),
            "source_repo_ready": path_ready(conceptgraphs_repo),
            "docker_ready": docker_image_ready("research2/conceptgraphs-smoke:latest"),
            "existing_metric_ready": bool(m49.get("paper_table_claim_ready")),
            "current_evidence": {
                "query_rows": m49.get("query_rows"),
                "strict_bbox_top5": m49.get("primary_strict_bbox_top5_success_rows"),
                "relaxed_bbox_1m_top3": m49.get("relaxed_bbox_1m_top3_success_rows"),
                "candidate_rows": m49.get("candidate_rows"),
                "object_rows": m49.get("object_rows"),
            },
            "blockers": [
                "Already used as map baseline, so M98 must add a distinct proposal/mapping robustness analysis rather than repeat M49.",
                "Must tie failures to H001 memory-decision rows, not only report retrieval scores.",
            ],
            "first_smoke": "E005-M98 ConceptGraphs-derived proposal/map reliability and failure-boundary smoke over the 195-row denominator",
            "decision": "selected_first",
            "rationale": [
                "It is the only candidate with full heldout 195-row query conversion, source/runtime history, and low additional setup burden.",
                "It directly addresses reviewer pressure for a stronger external open-vocabulary mapping baseline before navigation.",
                "It can be executed without a new heavy Docker run by reusing existing `ConceptGraphs` artifacts.",
            ],
        },
        {
            "route_id": "open3dsg_bounded_vocab_adapter_route",
            "rank": 2,
            "selected_for_first_smoke": False,
            "role": "external_scene_graph_baseline_supporting_row",
            "top_tier_value": "medium",
            "engineering_burden": "low",
            "denominator_alignment": "ready_195_rows",
            "local_data_ready": bool(m64.get("query_rows") == 195 and m64.get("open3dsg_vocab_policy_ready")),
            "source_repo_ready": path_ready(open3dsg_source),
            "docker_ready": docker_image_ready("h001-open3dsg-repro:cu128"),
            "existing_metric_ready": bool(m64.get("open3dsg_main_table_candidate_ready")),
            "current_evidence": {
                "query_rows": m64.get("query_rows"),
                "strict_bbox_top5": 144,
                "relaxed_bbox_1m_top3": 147,
                "object_candidate_rows": m64.get("object_candidate_rows"),
                "source_modified": m64.get("source_modified"),
                "bridge_dir_ready": path_ready(open3dsg_bridge),
            },
            "blockers": [
                "This is a bounded predicted-vocabulary adapter row, not a real RGB-D proposal robustness route.",
                "The primary-label adapter is weaker, so the paper must label the stronger row precisely.",
            ],
            "first_smoke": "No immediate heavy smoke; keep as supporting table row and use M66 failure-boundary rows.",
            "decision": "supporting_not_first",
            "rationale": [
                "It is useful as a second external scene-graph baseline row.",
                "It does not directly solve the current real-proposal robustness blocker because it is adapter-based and not a fresh proposal source.",
            ],
        },
        {
            "route_id": "openmask3d_instance_proposal_route",
            "rank": 3,
            "selected_for_first_smoke": False,
            "role": "external_3d_instance_proposal_baseline",
            "top_tier_value": "high_if_unblocked",
            "engineering_burden": "high",
            "denominator_alignment": "not_ready_currently_two_scan_plan_only",
            "local_data_ready": path_ready(openmask_repo) and path_ready(openmask_checkpoint),
            "source_repo_ready": path_ready(openmask_repo),
            "docker_ready": docker_image_ready("research2/openmask3d-smoke:latest"),
            "existing_metric_ready": False,
            "current_evidence": {
                "e003_m72_status": m72_openmask.get("status"),
                "image_ready": m72_openmask.get("image_ready"),
                "blockers": m72_openmask.get("blockers"),
                "checkpoint_ready_partial": path_ready(openmask_checkpoint),
                "sam_checkpoint_ready": path_ready(openmask_sam),
            },
            "blockers": [
                "Docker image is not ready after `MinkowskiEngine` dependency failure.",
                "Current local cache has partial checkpoint readiness; SAM checkpoint is not confirmed in the OpenMask3D cache path.",
                "Needs denominator scaling after environment repair.",
            ],
            "first_smoke": "Later E005-M99 or E003 continuation: repair Docker/MinkowskiEngine route or use a prebuilt image before denominator conversion.",
            "decision": "defer_until_env_unblocked",
            "rationale": [
                "It would be a strong reviewer-facing proposal baseline if executable.",
                "It is not the first route because environment repair is high-risk and would delay the current claim-boundary work.",
            ],
        },
        {
            "route_id": "hovsg_hierarchical_open_vocab_scene_graph_route",
            "rank": 4,
            "selected_for_first_smoke": False,
            "role": "external_hierarchical_open_vocabulary_mapping_baseline",
            "top_tier_value": "high_if_acquired",
            "engineering_burden": "high_unknown",
            "denominator_alignment": "not_ready",
            "local_data_ready": False,
            "source_repo_ready": hovsg_repo_ready,
            "docker_ready": False,
            "existing_metric_ready": False,
            "current_evidence": {
                "local_repo_candidates": [str(path) for path in hovsg_repo_candidates],
                "local_repo_ready": hovsg_repo_ready,
            },
            "blockers": [
                "Source/runtime not acquired in this workspace.",
                "Input/output schema, checkpoint burden, and 3RScan compatibility are unknown.",
                "Needs source/interface audit before any claim-facing run.",
            ],
            "first_smoke": "Later source/interface audit if `ConceptGraphs` route is insufficient for top-tier baseline pressure.",
            "decision": "defer_source_audit",
            "rationale": [
                "It is conceptually aligned with Direction B, but no local feasibility evidence exists yet.",
                "A source/runtime audit is appropriate after the low-burden `ConceptGraphs` derived route is exhausted.",
            ],
        },
    ]


def build_first_smoke_contract(selected_route: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_unit": "E005-M98 ConceptGraphs-derived proposal/map reliability and failure-boundary smoke",
        "selected_route": selected_route["route_id"],
        "purpose": "Use existing ConceptGraphs heldout map candidates to test whether external map/proposal coverage explains the remaining real RGB-D/open-vocabulary robustness boundary.",
        "input_artifacts": [
            "experiments/E005_external_baseline_transition/artifacts/E005-M49_conceptgraphs_full_heldout_aggregation_v0/",
            "experiments/E005_external_baseline_transition/artifacts/E005-M66_external_baseline_failure_boundary_v0/",
            "experiments/E005_external_baseline_transition/artifacts/E005-M75_real_proposal_aggregate_route_v0/",
            "experiments/E005_external_baseline_transition/artifacts/E005-M95_real_proposal_paper_boundary_v0/",
        ],
        "output_contract": [
            "route coverage summary",
            "ConceptGraphs-vs-real-proposal row groups",
            "H001-only / ConceptGraphs-only / detector-only / shared-failure counts",
            "claim boundary rows for real RGB-D/open-vocabulary robustness",
            "next decision: run a heavier external route or proceed to navigation bridge design",
        ],
        "blocked_claims_remain_blocked": [
            "final real RGB-D/open-vocabulary robustness",
            "deployable search policy",
            "real navigation SR/SPL",
            "human intent as a main contribution",
        ],
        "long_running_job_required": False,
    }


def build_decision_criteria() -> list[dict[str, Any]]:
    return [
        {
            "criterion": "denominator_aligned_now",
            "weight": "high",
            "preferred_route": "conceptgraphs_derived_map_candidate_route",
            "reason": "M97 should avoid launching a heavy route before using already aligned 195-row external map evidence.",
        },
        {
            "criterion": "directly_addresses_m95_blocker",
            "weight": "high",
            "preferred_route": "conceptgraphs_derived_map_candidate_route",
            "reason": "The current blocker is proposal/mapping robustness, not navigation execution.",
        },
        {
            "criterion": "reviewer_baseline_strength",
            "weight": "high",
            "preferred_route": "openmask3d_instance_proposal_route_or_hovsg_if_unblocked",
            "reason": "`OpenMask3D` or `HOV-SG` would be stronger if executable, but both are currently blocked or unaudited.",
        },
        {
            "criterion": "claim_specificity",
            "weight": "medium",
            "preferred_route": "conceptgraphs_derived_map_candidate_route",
            "reason": "The next result must separate map candidate coverage from detector ranking and from H001 memory trust.",
        },
        {
            "criterion": "engineering_risk",
            "weight": "medium",
            "preferred_route": "conceptgraphs_derived_map_candidate_route",
            "reason": "This route can be run from existing artifacts; `OpenMask3D` and `HOV-SG` require environment/source work.",
        },
    ]


def build_claim_boundary() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "C-M97-001",
            "claim": "The next external route should first reuse denominator-aligned `ConceptGraphs` map candidates for proposal/mapping reliability analysis.",
            "claim_type": "route_decision",
            "status": "selected",
            "evidence": "Full 195-row `ConceptGraphs` heldout conversion and M96 route decision are ready.",
            "next_validation_requirement": "E005-M98 must produce row-level reliability/failure groups, not a repeated retrieval table.",
        },
        {
            "claim_id": "C-M97-002",
            "claim": "`OpenMask3D` is a strong proposal-baseline candidate.",
            "claim_type": "future_baseline",
            "status": "blocked_by_environment",
            "evidence": "M72 records Docker/MinkowskiEngine build failure and missing image.",
            "next_validation_requirement": "Repair or replace the Docker route before claim-facing runs.",
        },
        {
            "claim_id": "C-M97-003",
            "claim": "`HOV-SG` is directionally aligned with Direction B.",
            "claim_type": "future_baseline",
            "status": "source_audit_required",
            "evidence": "No local source/runtime artifact exists in this workspace.",
            "next_validation_requirement": "Run a source/interface audit before acquisition or Docker work.",
        },
        {
            "claim_id": "C-M97-004",
            "claim": "`Open3DSG` bounded vocab adapter remains a supporting external scene-graph row.",
            "claim_type": "baseline_boundary",
            "status": "supporting_not_primary_next_route",
            "evidence": "M64 is denominator-aligned, but it is a bounded predicted-vocabulary adapter rather than a fresh proposal source.",
            "next_validation_requirement": "Keep exact adapter label in tables and do not use it as final real RGB-D proposal robustness evidence.",
        },
    ]


def report(
    coverage: dict[str, Any],
    matrix: list[dict[str, Any]],
    criteria: list[dict[str, Any]],
    first_smoke: dict[str, Any],
) -> str:
    matrix_lines = [
        "| Rank | Route | Decision | Data Ready | Docker Ready | Burden | First Smoke |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix:
        matrix_lines.append(
            f"| {row['rank']} | `{row['route_id']}` | {row['decision']} | "
            f"{str(row['local_data_ready']).lower()} | {str(row['docker_ready']).lower()} | "
            f"{row['engineering_burden']} | {row['first_smoke']} |"
        )

    criteria_lines = [
        "| Criterion | Weight | Preferred Route | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in criteria:
        criteria_lines.append(
            f"| `{row['criterion']}` | {row['weight']} | `{row['preferred_route']}` | {row['reason']} |"
        )

    return f"""# E005-M97 External Proposal/Mapping Feasibility Matrix

## Facts

- Status: `{coverage["status"]}`.
- Selected first route: `{coverage["selected_first_route"]}`.
- Next recommended unit: `{coverage["next_recommended_unit"]}`.
- Candidate route count: {coverage["candidate_route_count"]}.
- Heavy/background job launched: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Real navigation `SR` / `SPL` ready: false.

## Feasibility Matrix

{chr(10).join(matrix_lines)}

## Decision Criteria

{chr(10).join(criteria_lines)}

## First Smoke Contract

- Next unit: `{first_smoke["next_unit"]}`.
- Selected route: `{first_smoke["selected_route"]}`.
- Purpose: {first_smoke["purpose"]}
- Long-running job required: {str(first_smoke["long_running_job_required"]).lower()}.

## Claim Boundary

- M97 is a feasibility decision, not a performance result.
- Do not claim final real RGB-D/open-vocabulary robustness from M97.
- Do not start navigation `SR` / `SPL` before M98 tests whether existing external map/proposal candidates explain the current robustness boundary.
- Keep `OpenMask3D` and `HOV-SG` as later high-value routes, not current first runs.

## Agent Inference

- `ConceptGraphs`-derived route is the best immediate next step because it is already denominator-aligned and low-burden.
- `OpenMask3D` is more directly a proposal baseline, but it is currently blocked by environment/build issues.
- `HOV-SG` is directionally attractive for Direction B, but it needs source/runtime audit before any claim-facing work.
- `Open3DSG` bounded vocab adapter should remain a supporting row because it is not a fresh real RGB-D proposal route.
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m96 = read_json(M96_DIR / "coverage.json")
    m95 = read_json(M95_DIR / "coverage.json")
    m75 = read_json(M75_DIR / "coverage.json")
    matrix = build_matrix()
    criteria = build_decision_criteria()
    claims = build_claim_boundary()
    selected = next(row for row in matrix if row["selected_for_first_smoke"])
    first_smoke = build_first_smoke_contract(selected)
    coverage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_route_count": len(matrix),
        "m75_h001_success_rows": m75.get("h001_success_rows"),
        "m75_query_rows": m75.get("query_rows"),
        "m95_blocked_claim_count": m95.get("blocked_claim_count"),
        "m96_selected_route": m96.get("selected_next_route"),
        "next_recommended_unit": first_smoke["next_unit"],
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "selected_first_route": selected["route_id"],
        "status": "e005_m97_external_proposal_mapping_feasibility_ready",
        "version": VERSION,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", {"coverage": coverage, "matrix": matrix, "criteria": criteria, "first_smoke": first_smoke, "claims": claims})
    write_json(OUT_DIR / "first_smoke_contract.json", first_smoke)
    write_jsonl(OUT_DIR / "feasibility_matrix.jsonl", matrix)
    write_jsonl(OUT_DIR / "decision_criteria.jsonl", criteria)
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claims)
    write_text(OUT_DIR / "report.md", report(coverage, matrix, criteria, first_smoke))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
