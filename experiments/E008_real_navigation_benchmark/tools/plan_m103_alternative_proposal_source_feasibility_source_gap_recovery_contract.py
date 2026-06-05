#!/usr/bin/env python3
"""Plan an alternative proposal-source feasibility contract after E008-M102."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
E005_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"

M06_DIR = EXP_ROOT / "artifacts" / "E008-M06_hm3d_semantic_candidate_source_smoke_v0"
M102_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M102_coverage_expansion_failure_audit_source_gap_repair_closure_v0"
)
E003_M72_DIR = E003_ROOT / "artifacts" / "E003-M72_openmask3d_blocker_fallback_gate_v0"
E005_M97_DIR = E005_ROOT / "artifacts" / "E005-M97_external_proposal_mapping_feasibility_v0"
E005_M98_DIR = E005_ROOT / "artifacts" / "E005-M98_conceptgraphs_reliability_boundary_v0"
E005_M100_DIR = E005_ROOT / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"
E005_M101_DIR = E005_ROOT / "artifacts" / "E005-M101_map_assisted_claim_boundary_navigation_decision_v0"

OPENMASK_CHECKPOINT_DIR = ROOT / "local_dataset" / "checkpoints" / "openmask3d"
HM3D_BRIDGE_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
)
DATA_OUT_DIR = (
    HM3D_BRIDGE_DIR
    / "E008-M103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
)

VERSION = "e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_v0"
READY_STATUS = "e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_ready"
BLOCKED_STATUS = "e008_m103_alternative_proposal_source_feasibility_source_gap_recovery_contract_blocked"
NEXT_UNIT = "E008-M104 ConceptGraphs HM3D source-gap adapter/preflight contract"


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
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def docker_image_ready(image: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", image],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0


def checkpoint_ready(path: Path, min_size: int) -> bool:
    return path.exists() and path.stat().st_size >= min_size


def build_source_gap_requirement_rows(source_gap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_gap_rows:
        failure_type = str(row.get("m91_dominant_failure_type"))
        if failure_type == "observation_or_detector_target_coverage_gap":
            source_requirement = (
                "generate at least one target-category 3D/map candidate from non-oracle observations "
                "before any path ranking or budget repair"
            )
            recovery_test = "primary target-near candidate must appear under leakage-safe goal evaluation"
            why_current_failed = "same detector coverage expansion made 853 pre-cap candidates but the closest post-repair candidate stayed 5.484739m from any target viewpoint"
        else:
            source_requirement = (
                "preserve low-confidence or ambiguous target-category 3D/map candidates with valid coordinates "
                "before top-k cap suppression"
            )
            recovery_test = "pre-cap near-miss must become a valid source-ready primary candidate without eval-goal leakage"
            why_current_failed = "cap/threshold probe could not promote the earlier 1.082507m near-miss into a primary or relaxed fixed-order recovery"
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_gap_requirement",
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "m102_assigned_repair_branch": row.get("assigned_repair_branch"),
                "m102_closure_status": row.get("repair_branch_status"),
                "m102_best_post_repair_any_viewpoint_xz_m": row.get("post_repair_best_any_viewpoint_xz_m"),
                "why_current_route_failed": why_current_failed,
                "alternative_source_minimum_requirement": source_requirement,
                "recovery_test_after_candidate_generation": recovery_test,
                "blocked_inputs": [
                    "ObjectNav eval_goal_position",
                    "ObjectNav target viewpoint coordinates",
                    "success labels or target object id",
                    "distance-to-target fields used for policy ordering",
                ],
                "claim_boundary": "This row defines the source-gap requirement; it is not a recovery result.",
            }
        )
    return rows


def build_route_rows(
    m06_coverage: dict[str, Any],
    e003_m72_coverage: dict[str, Any],
    e005_m97_coverage: dict[str, Any],
    e005_m98_coverage: dict[str, Any],
    e005_m100_coverage: dict[str, Any],
    e005_m101_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    conceptgraphs_image_ready = docker_image_ready("research2/conceptgraphs-smoke:latest")
    real_smoke_image_ready = docker_image_ready("research2/real-smoke:latest")
    habitat_image_ready = docker_image_ready("research3/habitat-h001:20260508-calib-artifacts")
    openmask3d_image_ready = docker_image_ready("research2/openmask3d-smoke:latest")
    openmask3d_ckpt_ready = checkpoint_ready(
        OPENMASK_CHECKPOINT_DIR / "openmask3d_arbitrary_scene_model.ckpt", 50_000_000
    )
    sam_ckpt_ready = checkpoint_ready(OPENMASK_CHECKPOINT_DIR / "sam_vit_h_4b8939.pth", 2_000_000_000)
    hm3d_semantic_coordinate_ready = bool(m06_coverage.get("candidate_rows_ready"))
    conceptgraphs_e005_ready = bool(
        e005_m97_coverage.get("selected_first_route") == "conceptgraphs_derived_map_candidate_route"
        and e005_m98_coverage.get("status") == "e005_m98_conceptgraphs_reliability_boundary_ready"
        and e005_m100_coverage.get("status") == "e005_m100_conceptgraphs_assisted_fallback_policy_ready"
        and e005_m101_coverage.get("status") == "e005_m101_map_assisted_claim_boundary_navigation_decision_ready"
    )
    return [
        {
            "version": VERSION,
            "route_id": "same_groundingdino_bbox_depth_more_render_or_lower_cap",
            "candidate_source_principle": "2D open-vocabulary bbox plus depth back-projection",
            "decision": "reject",
            "rank": 99,
            "hm3d_runtime_ready": real_smoke_image_ready and habitat_image_ready,
            "directly_addresses_m102_failure": False,
            "engineering_burden": "low",
            "expected_claim_value": "negative reviewer-defense only",
            "reason": "M102 already closed the same detector/source principle after cap-threshold and coverage-expansion repairs failed.",
            "next_unit": None,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "hm3d_semantic_object_upper_bound",
            "candidate_source_principle": "dataset semantic labels / ObjectNav semantic source",
            "decision": "diagnostic_ceiling_only",
            "rank": 4,
            "hm3d_semantic_label_support_rows_ready": m06_coverage.get("semantic_label_support_rows_ready"),
            "hm3d_candidate_coordinate_rows_ready": m06_coverage.get("candidate_rows_ready"),
            "hm3d_coordinate_extraction_ready": hm3d_semantic_coordinate_ready,
            "directly_addresses_m102_failure": "ceiling_only",
            "engineering_burden": "medium",
            "expected_claim_value": "upper-bound sanity check, not deployable proposal source",
            "reason": "M06 found semantic labels but no reliable non-oracle coordinate extraction; ObjectNav goal/viewpoint leakage must stay metric-only.",
            "next_unit": "optional diagnostic upper-bound only after non-oracle source route is staged",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "conceptgraphs_hm3d_map_candidate_adapter",
            "candidate_source_principle": "posed RGB-D open-vocabulary 3D map candidates with instance-level spatial memory",
            "decision": "select_preflight_first",
            "rank": 1,
            "conceptgraphs_image_ready": conceptgraphs_image_ready,
            "habitat_image_ready": habitat_image_ready,
            "e005_conceptgraphs_route_ready": conceptgraphs_e005_ready,
            "e005_query_rows": e005_m98_coverage.get("query_rows"),
            "e005_conceptgraphs_success_rows": e005_m98_coverage.get("conceptgraphs_success_rows"),
            "e005_selected_map_assisted_success_rows": e005_m100_coverage.get("selected_success_rows"),
            "directly_addresses_m102_failure": "medium_high",
            "engineering_burden": "medium",
            "expected_claim_value": "best immediate route to test whether a map-level candidate source repairs HM3D source-gap cases",
            "reason": "It changes the failed bbox-depth proposal principle, has a working Docker image and positive E005 map-candidate evidence, and avoids the current OpenMask3D build blocker.",
            "next_unit": NEXT_UNIT,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "openmask3d_hm3d_3d_instance_proposal",
            "candidate_source_principle": "open-vocabulary 3D instance proposals from RGB-D/masks",
            "decision": "defer_blocked_fallback",
            "rank": 2,
            "checkpoint_ready": openmask3d_ckpt_ready,
            "sam_checkpoint_ready": sam_ckpt_ready,
            "image_ready": openmask3d_image_ready,
            "e003_m72_status": e003_m72_coverage.get("status"),
            "e003_m72_blockers": e003_m72_coverage.get("blockers"),
            "directly_addresses_m102_failure": "high",
            "engineering_burden": "high",
            "expected_claim_value": "strong proposal baseline if environment blocker is resolved",
            "reason": "The route is methodologically relevant, but current local evidence marks Docker/MinkowskiEngine setup as a hard blocker and no image is ready.",
            "next_unit": "revisit only if ConceptGraphs HM3D preflight fails or reviewer baseline pressure dominates",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "hov_sg_hierarchical_map_navigation_baseline",
            "candidate_source_principle": "hierarchical open-vocabulary semantic graph for map-navigation",
            "decision": "defer_source_runtime_audit",
            "rank": 3,
            "hm3d_runtime_ready": False,
            "directly_addresses_m102_failure": "medium_high",
            "engineering_burden": "high",
            "expected_claim_value": "broader map-navigation baseline for Direction B",
            "reason": "Useful for a broader system paper, but source/runtime compatibility is not yet audited and it is too heavy for the immediate source-gap gate.",
            "next_unit": "HOV-SG source/runtime audit after ConceptGraphs or OpenMask3D gate",
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "route_id": "open3dsg_denominator_aligned_3rscan_supporting_row",
            "candidate_source_principle": "3D scene graph prediction baseline on 3RScan/Open3DSG source",
            "decision": "supporting_external_baseline_not_hm3d_navigation_source",
            "rank": 5,
            "hm3d_runtime_ready": False,
            "directly_addresses_m102_failure": False,
            "engineering_burden": "medium",
            "expected_claim_value": "external scene-graph baseline support, not HM3D source-gap recovery",
            "reason": "The read-only Open3DSG bridge is valuable for external baseline rigor but does not provide the HM3D ObjectNav candidate source needed by M102.",
            "next_unit": None,
            "launch_long_job_now": False,
        },
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("rgb", "rendered or staged RGB observations from non-oracle agent/coverage poses"),
        ("depth", "depth aligned to the RGB frame or map-construction input"),
        ("pose", "camera/agent pose for map fusion and coordinate projection"),
        ("intrinsics", "camera intrinsics needed by the candidate-source route"),
        ("query_label", "object category string such as sofa or toilet"),
        ("start_pose", "episode start pose for source-readiness/path-cost validation"),
        ("navmesh", "Habitat navmesh for snap/path validation after candidate generation"),
        ("policy_context", "structured task context only for memory-trust or re-observation decision, not for target leakage"),
    ]
    blocked = [
        ("eval_goal_position", "ObjectNav target goal coordinate"),
        ("target_viewpoints", "ObjectNav success/viewpoint coordinates used as policy input"),
        ("target_object_id", "oracle instance id of the target object"),
        ("success_label", "episode success/failure labels"),
        ("distance_to_eval_target", "any distance-to-target field used before evaluation"),
        ("m100_or_m102_case_success", "prior failure/success tags used to order candidates"),
    ]
    rows = [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "rule": rule,
            "policy_use_allowed": True,
        }
        for field, rule in allowed
    ]
    rows.extend(
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "rule": rule,
            "policy_use_allowed": False,
        }
        for field, rule in blocked
    )
    return rows


def build_m104_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": (
                "M104 can stage ConceptGraphs-compatible HM3D source-gap inputs for both M102 cases, "
                "produce non-oracle target-category map candidates, and export coordinates without blocked fields."
            ),
            "next_action": "E008-M105 navmesh/source-readiness validation for ConceptGraphs-derived HM3D candidates",
            "claim_status_after_gate": "proposal-source feasibility only; no source-gap recovery claim yet",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": (
                "M104 stages input layout but produces candidates for only one source-gap case, or produces map objects "
                "without reliable category/coordinate binding."
            ),
            "next_action": "record source-specific limitation and decide ConceptGraphs repair vs OpenMask3D fallback",
            "claim_status_after_gate": "diagnostic source-route evidence only",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": (
                "M104 cannot stage RGB-D/pose/intrinsics without oracle leakage, cannot run in existing Docker, "
                "or produces zero non-oracle candidate rows for the source-gap cases."
            ),
            "next_action": "revisit OpenMask3D environment repair or HOV-SG source/runtime audit; do not run navigation trajectories",
            "claim_status_after_gate": "alternative proposal-source route not supported",
        },
    ]


def build_candidate_output_contract_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_id", "stable id for each generated map/proposal candidate"),
        ("source_route", "conceptgraphs_hm3d_map_candidate_adapter or later external route id"),
        ("scan_id", "E008 scan id"),
        ("adapter_episode_id", "ObjectNav adapter episode id for evaluation join only"),
        ("scene_key", "HM3D scene key"),
        ("object_category", "query category"),
        ("candidate_xyz", "world coordinate of candidate center before navmesh snap"),
        ("confidence", "source confidence or normalized score, if provided"),
        ("semantic_label", "source label or matched text label"),
        ("map_instance_id", "map/proposal instance id if available"),
        ("evidence_frame_ids", "non-oracle frame ids used by the source route"),
        ("source_input_trace", "short trace proving no blocked input was used"),
        ("coordinate_frame", "world/habitat coordinate frame tag"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "m104_candidate_output_field",
            "field": field,
            "required": field
            in {
                "candidate_id",
                "source_route",
                "scan_id",
                "adapter_episode_id",
                "scene_key",
                "object_category",
                "candidate_xyz",
                "source_input_trace",
                "coordinate_frame",
            },
            "definition": definition,
        }
        for field, definition in fields
    ]


def build_claim_boundary_rows(selected_route: str) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "current_detector_source_gap_repair_route_failed",
            "status": "supported_by_M102",
            "boundary": "negative reviewer-defense claim only",
        },
        {
            "version": VERSION,
            "claim": "alternative_proposal_source_feasibility",
            "status": "contract_ready_not_yet_tested",
            "boundary": f"M103 selects {selected_route}; M104 must materialize/check candidates before any positive source-gap statement.",
        },
        {
            "version": VERSION,
            "claim": "source_gap_recovery",
            "status": "blocked",
            "boundary": "requires leakage-safe goal evaluation after an alternative candidate source produces source-ready rows.",
        },
        {
            "version": VERSION,
            "claim": "real_navigation_SR_SPL",
            "status": "blocked",
            "boundary": "requires positive source-gap proxy recovery and Docker/Habitat trajectory execution against baselines.",
        },
        {
            "version": VERSION,
            "claim": "final_real_RGBD_open_vocabulary_robustness",
            "status": "blocked",
            "boundary": "requires external proposal/map route evidence beyond the current GroundingDINO bbox-depth diagnostic chain.",
        },
        {
            "version": VERSION,
            "claim": "human_intent_main_contribution",
            "status": "blocked",
            "boundary": "M103 is about proposal source; human intent remains a conditioning variable unless a separate E006/E008 gate shows task-context-specific gains.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Why not keep tuning the current detector?",
            "answer": "M102 closed both cap-threshold and coverage-expansion branches; the failure is candidate-source generation, not just ranking.",
        },
        {
            "version": VERSION,
            "question": "Why not use HM3D semantic annotations as the source?",
            "answer": "M06 supports semantic labels but not reliable non-oracle coordinate extraction; ObjectNav goal/viewpoint data must remain evaluation-only.",
        },
        {
            "version": VERSION,
            "question": "Why choose ConceptGraphs before OpenMask3D?",
            "answer": "ConceptGraphs has a ready Docker image and positive E005 map-candidate evidence; OpenMask3D is more direct as a 3D proposal baseline but remains Docker/MinkowskiEngine-blocked.",
        },
        {
            "version": VERSION,
            "question": "Does M103 improve navigation?",
            "answer": "No. It fixes the next evidence contract. Navigation claims remain blocked until M104+ generate source-ready candidates and subsequent proxy/trajectory evaluations pass.",
        },
    ]


def build_next_action_rows(selected_route: str) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "selected_next_unit": NEXT_UNIT,
            "selected_route": selected_route,
            "launch_long_job_now": False,
            "why_next": "M104 should first verify HM3D-to-ConceptGraphs input compatibility and non-oracle candidate export before any long map-construction run.",
            "expected_output_root": str(HM3D_BRIDGE_DIR / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"),
        }
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    source_gap_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    selected = next(row for row in route_rows if row["decision"] == "select_preflight_first")
    lines = [
        "# E008-M103 Alternative Proposal-Source Feasibility / Source-Gap Recovery Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M102 source-gap cases: {coverage['source_gap_case_rows']}.",
        f"- Current detector route closed: {coverage['current_detector_source_gap_repair_route_closed']}.",
        f"- Selected route: `{coverage['selected_route']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        f"- Launch long job now: {coverage['launch_long_job_now']}.",
        f"- `ConceptGraphs` image ready: {coverage['conceptgraphs_image_ready']}.",
        f"- `OpenMask3D` image ready: {coverage['openmask3d_image_ready']}.",
        f"- `OpenMask3D` checkpoints ready: {coverage['openmask3d_checkpoints_ready']}.",
        "",
        "## Source-Gap Requirements",
        "",
        "| scan_id | category | M102 branch | post-repair best m | requirement |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in source_gap_rows:
        lines.append(
            "| {scan_id} | {cat} | {branch} | {dist} | {req} |".format(
                scan_id=row.get("scan_id"),
                cat=row.get("object_category"),
                branch=row.get("m102_assigned_repair_branch"),
                dist=f"{float(row.get('m102_best_post_repair_any_viewpoint_xz_m')):.6f}",
                req=row.get("alternative_source_minimum_requirement"),
            )
        )
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| route | decision | rank | directness | burden | reason |",
            "| --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in sorted(route_rows, key=lambda item: int(item["rank"])):
        lines.append(
            "| {route} | {decision} | {rank} | {direct} | {burden} | {reason} |".format(
                route=row.get("route_id"),
                decision=row.get("decision"),
                rank=row.get("rank"),
                direct=row.get("directly_addresses_m102_failure"),
                burden=row.get("engineering_burden"),
                reason=row.get("reason"),
            )
        )
    lines.extend(
        [
            "",
            "## M104 Gate",
            "",
            "| gate | condition | next action |",
            "| --- | --- | --- |",
        ]
    )
    for row in gate_rows:
        lines.append(f"| {row['gate']} | {row['condition']} | {row['next_action']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- M103 supports selecting `{selected['route_id']}` as the next preflight route.",
            "- M103 does not support source-gap recovery, deployable policy, final real navigation `SR` / `SPL`, final RGB-D/open-vocabulary robustness, or human-intent contribution.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    m102_coverage = read_json(M102_DIR / "coverage.json")
    m102_source_gap_rows = read_jsonl(M102_DIR / "source_gap_case_closure_rows.jsonl")
    m06_coverage = read_json(M06_DIR / "coverage.json")
    e003_m72_coverage = read_json(E003_M72_DIR / "coverage.json")
    e005_m97_coverage = read_json(E005_M97_DIR / "coverage.json")
    e005_m98_coverage = read_json(E005_M98_DIR / "coverage.json")
    e005_m100_coverage = read_json(E005_M100_DIR / "coverage.json")
    e005_m101_coverage = read_json(E005_M101_DIR / "coverage.json")

    required_inputs_ready = bool(
        m102_coverage.get("status")
        == "e008_m102_coverage_expansion_failure_audit_source_gap_repair_closure_ready"
        and m102_source_gap_rows
    )

    if ARTIFACT_DIR.exists():
        shutil.rmtree(ARTIFACT_DIR)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_gap_requirement_rows = build_source_gap_requirement_rows(m102_source_gap_rows)
    route_rows = build_route_rows(
        m06_coverage,
        e003_m72_coverage,
        e005_m97_coverage,
        e005_m98_coverage,
        e005_m100_coverage,
        e005_m101_coverage,
    )
    selected_route_row = next(row for row in route_rows if row["decision"] == "select_preflight_first")
    selected_route = str(selected_route_row["route_id"])
    input_contract_rows = build_input_contract_rows()
    m104_gate_rows = build_m104_gate_rows()
    candidate_output_contract_rows = build_candidate_output_contract_rows()
    claim_boundary_rows = build_claim_boundary_rows(selected_route)
    reviewer_defense_rows = build_reviewer_defense_rows()
    next_action_rows = build_next_action_rows(selected_route)

    openmask3d_ckpt_ready = checkpoint_ready(
        OPENMASK_CHECKPOINT_DIR / "openmask3d_arbitrary_scene_model.ckpt", 50_000_000
    )
    sam_ckpt_ready = checkpoint_ready(OPENMASK_CHECKPOINT_DIR / "sam_vit_h_4b8939.pth", 2_000_000_000)
    conceptgraphs_image_ready = bool(selected_route_row.get("conceptgraphs_image_ready"))
    openmask3d_image_ready = docker_image_ready("research2/openmask3d-smoke:latest")

    coverage = {
        "version": VERSION,
        "status": READY_STATUS if required_inputs_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m102_status": m102_coverage.get("status"),
        "source_gap_case_rows": len(m102_source_gap_rows),
        "current_detector_source_gap_repair_route_closed": bool(
            m102_coverage.get("current_detector_source_gap_repair_route_closed")
        ),
        "same_detector_rerun_selected": False,
        "hm3d_semantic_candidate_coordinate_ready": bool(m06_coverage.get("candidate_rows_ready")),
        "conceptgraphs_image_ready": conceptgraphs_image_ready,
        "conceptgraphs_e005_route_ready": bool(selected_route_row.get("e005_conceptgraphs_route_ready")),
        "openmask3d_image_ready": openmask3d_image_ready,
        "openmask3d_checkpoints_ready": openmask3d_ckpt_ready and sam_ckpt_ready,
        "openmask3d_e003_m72_status": e003_m72_coverage.get("status"),
        "selected_route": selected_route,
        "selected_next_unit": NEXT_UNIT,
        "launch_long_job_now": False,
        "additional_long_job_recommended_now": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_requirement_rows.jsonl", source_gap_requirement_rows)
    write_jsonl(ARTIFACT_DIR / "route_feasibility_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_contract_rows)
    write_jsonl(ARTIFACT_DIR / "m104_gate_rows.jsonl", m104_gate_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_output_contract_rows.jsonl", candidate_output_contract_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "reviewer_defense_rows.jsonl", reviewer_defense_rows)
    write_jsonl(ARTIFACT_DIR / "next_action_rows.jsonl", next_action_rows)
    write_report(
        ARTIFACT_DIR / "report.md",
        coverage,
        source_gap_requirement_rows,
        route_rows,
        m104_gate_rows,
    )

    for path in ARTIFACT_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, DATA_OUT_DIR / path.name)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
