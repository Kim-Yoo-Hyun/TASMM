#!/usr/bin/env python3
"""Decide whether E003 should move to an OpenMask3D feasibility route."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset" / "3RScan" / "scans"
DEFAULT_M47_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M47_external_baseline_feasibility_gate_v0"
DEFAULT_M58_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M58_direct_current_rescan_bridge_design_v0"
DEFAULT_M61_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M61_direct_bridge_rank_failure_gate_v0"
DEFAULT_M63_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M63_bounded_repair_integration_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M64_openmask3d_feasibility_decision_v0"
M64_VERSION = "e003_m64_openmask3d_feasibility_decision_v0"
SELECTED_BOUNDED_ROLE = "selected_bounded"
UNBOUNDED_ROLE = "best_unbounded"
ORACLE_ROLE = "oracle_task_budget"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


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


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def get_candidate(candidates: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for row in candidates:
        if row.get("external_route") == name:
            return row
    return {}


def group_by_role(row_outcomes: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in row_outcomes:
        grouped[str(row["paper_role"])][str(row["row_uid"])] = row
    return grouped


def build_gap_rows(
    row_outcomes: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_role = group_by_role(row_outcomes)
    selected = by_role[SELECTED_BOUNDED_ROLE]
    unbounded = by_role[UNBOUNDED_ROLE]
    oracle = by_role[ORACLE_ROLE]
    failure_by_row_uid = {str(row["row_uid"]): row for row in failure_rows}
    rows = []
    for row_uid, selected_row in sorted(selected.items()):
        unbounded_row = unbounded.get(row_uid, {})
        oracle_row = oracle.get(row_uid, {})
        failure = failure_by_row_uid.get(row_uid, {})
        if bool(selected_row["query_bridge_success"]):
            gap_class = "bounded_repair_success"
            openmask3d_relevance = "not_needed_for_this_row"
        elif not bool(selected_row["target_detected"]):
            gap_class = "detector_recall_miss_after_bounded_repair"
            openmask3d_relevance = "direct"
        elif bool(unbounded_row.get("query_bridge_success")) or bool(oracle_row.get("query_bridge_success")):
            gap_class = "rank_or_budget_gap_after_bounded_repair"
            openmask3d_relevance = "indirect"
        else:
            gap_class = "unresolved_after_bounded_repair"
            openmask3d_relevance = "uncertain"
        rows.append(
            {
                "m64_version": M64_VERSION,
                "row_uid": row_uid,
                "target_uid": selected_row["target_uid"],
                "current_rescan_id": selected_row["current_rescan_id"],
                "label_canonical": selected_row["label_canonical"],
                "task_budget": selected_row["task_budget"],
                "selected_bounded_success": selected_row["query_bridge_success"],
                "selected_bounded_target_detected": selected_row["target_detected"],
                "selected_bounded_target_rank": selected_row["target_rank"],
                "selected_bounded_returned_locations": selected_row["returned_location_count"],
                "unbounded_success": unbounded_row.get("query_bridge_success"),
                "oracle_task_budget_success": oracle_row.get("query_bridge_success"),
                "failure_class_m61": failure.get("failure_class"),
                "repair_hint_m61": failure.get("repair_hint"),
                "gap_class_m64": gap_class,
                "openmask3d_relevance": openmask3d_relevance,
                "old_location_dead_end_expected": selected_row["old_location_dead_end_expected"],
            }
        )
    return rows


def scan_file_status(dataset_root: Path, scan_id: str) -> dict[str, Any]:
    scan_dir = dataset_root / scan_id
    sequence_dir = scan_dir / "sequence"
    color_count = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.exists() else 0
    depth_count = len(list(sequence_dir.glob("*.depth.pgm"))) if sequence_dir.exists() else 0
    pose_count = len(list(sequence_dir.glob("*.pose.txt"))) if sequence_dir.exists() else 0
    triplet_lower_bound = min(color_count, depth_count, pose_count)
    return {
        "m64_version": M64_VERSION,
        "scan_id": scan_id,
        "scan_dir": str(scan_dir),
        "scan_dir_exists": scan_dir.exists(),
        "sequence_dir_exists": sequence_dir.exists(),
        "sequence_zip_exists": (scan_dir / "sequence.zip").exists(),
        "point_cloud_exists": (scan_dir / "labels.instances.annotated.v2.ply").exists(),
        "semseg_exists": (scan_dir / "semseg.v2.json").exists(),
        "segments_exists": (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists(),
        "color_frames": color_count,
        "depth_frames": depth_count,
        "pose_frames": pose_count,
        "frame_triplet_lower_bound": triplet_lower_bound,
        "openmask3d_minimal_input_ready": (
            scan_dir.exists()
            and sequence_dir.exists()
            and (scan_dir / "labels.instances.annotated.v2.ply").exists()
            and triplet_lower_bound > 0
        ),
    }


def build_scan_rows(m58_coverage: dict[str, Any], dataset_root: Path) -> list[dict[str, Any]]:
    rows = []
    for row in m58_coverage.get("scan_summary", []):
        status = scan_file_status(dataset_root, row["scan_id"])
        status.update(
            {
                "bridge_query_rows": row["bridge_query_rows"],
                "bridge_target_objects": row["bridge_target_objects"],
                "same_label_distractor_objects": row["same_label_distractor_objects"],
                "target_labels": row["target_labels"],
            }
        )
        rows.append(status)
    return rows


def build_feasibility_matrix(openmask: dict[str, Any], gap_rows: list[dict[str, Any]], scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recall_miss_rows = [row for row in gap_rows if row["gap_class_m64"] == "detector_recall_miss_after_bounded_repair"]
    indirect_rows = [row for row in gap_rows if row["gap_class_m64"] == "rank_or_budget_gap_after_bounded_repair"]
    scan_ready_rows = [row for row in scan_rows if row["openmask3d_minimal_input_ready"]]
    return [
        {
            "criterion": "proposal_recall_need",
            "status": "pass" if recall_miss_rows else "fail",
            "score": len(recall_miss_rows),
            "evidence": f"{len(recall_miss_rows)} bounded-failure query rows remain target-undetected.",
            "risk": "OpenMask3D may still miss small/occluded objects or unsupported classes.",
        },
        {
            "criterion": "direct_bridge_denominator_ready",
            "status": "pass" if len(scan_rows) and len(scan_ready_rows) == len(scan_rows) else "fail",
            "score": len(scan_ready_rows),
            "evidence": f"{len(scan_ready_rows)} / {len(scan_rows)} bridge scans have point cloud plus RGB-D sequence payloads.",
            "risk": "This is still a 4-scan / 7-query direct bridge, not a final heldout benchmark.",
        },
        {
            "criterion": "external_baseline_value",
            "status": "pass" if int(openmask.get("top_tier_reviewer_value", 0) or 0) >= 5 else "weak",
            "score": openmask.get("top_tier_reviewer_value"),
            "evidence": openmask.get("primary_question", "OpenMask3D tests 3D instance proposal quality."),
            "risk": openmask.get("main_risk", "dependency and scene-format burden"),
        },
        {
            "criterion": "schema_bridge_fit",
            "status": "conditional" if int(openmask.get("schema_bridge_fit", 0) or 0) >= 4 else "weak",
            "score": openmask.get("schema_bridge_fit"),
            "evidence": openmask.get("output_fit", "3D instance masks can be adapted to proposal rows."),
            "risk": "Adapter must produce current proposal schema without using target instance ids at inference.",
        },
        {
            "criterion": "remaining_rank_gap",
            "status": "warn" if indirect_rows else "pass",
            "score": len(indirect_rows),
            "evidence": f"{len(indirect_rows)} bounded-failure rows are still rank/budget rather than recall.",
            "risk": "OpenMask3D alone may not fix ranking/cost if it only changes proposal source.",
        },
    ]


def build_route(
    matrix_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    openmask: dict[str, Any],
) -> dict[str, Any]:
    recall_miss_rows = [row for row in gap_rows if row["gap_class_m64"] == "detector_recall_miss_after_bounded_repair"]
    unique_recall_targets = sorted({row["target_uid"] for row in recall_miss_rows})
    scan_ready = all(row["openmask3d_minimal_input_ready"] for row in scan_rows) and bool(scan_rows)
    dependency_burden = int(openmask.get("dependency_risk", 4) or 4) + int(openmask.get("implementation_burden", 4) or 4)
    if recall_miss_rows and scan_ready:
        selected = "openmask3d_scene_format_model_smoke_plan_next"
        next_unit = "E003-M65 OpenMask3D scene-format/model smoke plan"
        rationale = (
            "M63 leaves target-undetected rows that current proposals cannot recover, and the direct bridge scans "
            "have the minimal point-cloud/RGB-D payloads needed for a scene-format feasibility plan. Because "
            "OpenMask3D has high dependency burden, the next step should be a smoke plan, not an immediate long run."
        )
    elif recall_miss_rows:
        selected = "bridge_payload_repair_before_openmask3d"
        next_unit = "E003-M65 bridge payload repair or denominator expansion"
        rationale = (
            "Recall miss justifies a stronger proposal source, but the local payload is not ready enough for "
            "OpenMask3D scene-format staging."
        )
    else:
        selected = "expand_direct_bridge_denominator_before_openmask3d"
        next_unit = "E003-M65 direct bridge denominator expansion"
        rationale = "M63 no longer leaves a proposal-recall-dominated failure, so expand the denominator before OpenMask3D."
    return {
        "m64_version": M64_VERSION,
        "selected_next_route": selected,
        "next_recommended_unit": next_unit,
        "rationale": rationale,
        "recall_miss_query_rows_after_bounded": len(recall_miss_rows),
        "recall_miss_unique_targets_after_bounded": len(unique_recall_targets),
        "recall_miss_target_uids_after_bounded": unique_recall_targets,
        "scan_payload_ready_for_openmask3d_plan": scan_ready,
        "dependency_burden_score": dependency_burden,
        "openmask3d_source_url": openmask.get("source_url"),
        "route_options": {
            "openmask3d_scene_format_model_smoke_plan_next": {
                "benefit": "directly tests whether 3D instance proposal quality can recover target-undetected rows",
                "risk": "dependency and scene-format conversion can dominate before method evidence",
            },
            "bridge_payload_repair_before_openmask3d": {
                "benefit": "prevents launching a heavy baseline without valid local inputs",
                "risk": "delays external baseline evidence",
            },
            "expand_direct_bridge_denominator_before_openmask3d": {
                "benefit": "reduces small-denominator risk",
                "risk": "does not address proposal recall by itself",
            },
        },
    }


def build_smoke_contract(route: dict[str, Any], scan_rows: list[dict[str, Any]], gap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_gap_rows = [row for row in gap_rows if row["gap_class_m64"] == "detector_recall_miss_after_bounded_repair"]
    selected_scans = sorted({row["current_rescan_id"] for row in selected_gap_rows})
    selected_labels = sorted({row["label_canonical"] for row in selected_gap_rows})
    return {
        "m64_version": M64_VERSION,
        "contract_id": "openmask3d_scene_format_model_smoke_plan_v0",
        "status": "plan_required_not_launched",
        "selected_scans_for_first_smoke": selected_scans,
        "selected_prompt_labels": selected_labels,
        "minimum_expected_outputs": [
            "scene_format_manifest.json",
            "openmask3d_command_plan.json",
            "proposal_adapter_contract.json",
            "verification_command.json",
        ],
        "allowed_inputs": [
            "3RScan point cloud",
            "posed RGB-D sequence",
            "prompt labels",
            "OpenMask3D model outputs",
        ],
        "forbidden_inputs": [
            "target_uid at inference time",
            "3DSSG target instance id at inference time",
            "query_bridge_success",
            "matched_target_uid before evaluation",
        ],
        "verification_requirements": [
            "scene payload file counts",
            "adapter output schema validation",
            "same query-level bridge evaluator as M60/M63",
            "explicit comparison against `bounded_budget_repair_v0`",
        ],
        "long_running_policy": "Any Docker build, model download, or OpenMask3D inference must run in tmux/nohup/background with timestamped logs.",
        "paper_claim_boundary": "No real RGB-D/open-vocabulary search claim until OpenMask3D output is evaluated on the direct bridge and compared against current proposals.",
        "route_selected": route["selected_next_route"],
        "scan_rows_available": len(scan_rows),
    }


def build_coverage(
    gap_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    route: dict[str, Any],
    m63_coverage: dict[str, Any],
) -> dict[str, Any]:
    gap_counts = Counter(row["gap_class_m64"] for row in gap_rows)
    label_counts = Counter(row["label_canonical"] for row in gap_rows if row["gap_class_m64"] != "bounded_repair_success")
    return {
        "m64_version": M64_VERSION,
        "status": "openmask3d_feasibility_decision_ready",
        "source_m63_status": m63_coverage["status"],
        "query_rows": m63_coverage["query_rows"],
        "selected_bounded_success_rows": m63_coverage["selected_bounded_success_rows"],
        "bounded_failure_rows": int(m63_coverage["query_rows"]) - int(m63_coverage["selected_bounded_success_rows"]),
        "gap_class_counts_after_bounded": dict(sorted(gap_counts.items())),
        "gap_label_counts_after_bounded": dict(sorted(label_counts.items())),
        "bridge_scans": len(scan_rows),
        "openmask3d_minimal_input_ready_scans": sum(1 for row in scan_rows if row["openmask3d_minimal_input_ready"]),
        "feasibility_matrix_status_counts": dict(sorted(Counter(row["status"] for row in matrix_rows).items())),
        "selected_next_route": route["selected_next_route"],
        "next_recommended_unit": route["next_recommended_unit"],
        "openmask3d_feasibility_pass_with_constraints": route["selected_next_route"] == "openmask3d_scene_format_model_smoke_plan_next",
        "docker_or_model_run_launched": False,
        "paper_table_command_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
    }


def build_report(coverage: dict[str, Any], route: dict[str, Any], smoke_contract: dict[str, Any]) -> str:
    gap_counts = coverage["gap_class_counts_after_bounded"]
    return "\n".join(
        [
            "# E003-M64 OpenMask3D Feasibility Decision",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Query rows: {coverage['query_rows']}",
            f"- Selected bounded success rows: {coverage['selected_bounded_success_rows']}",
            f"- Bounded failure rows: {coverage['bounded_failure_rows']}",
            f"- Gap class counts after bounded repair: {gap_counts}",
            f"- Bridge scans: {coverage['bridge_scans']}",
            f"- `OpenMask3D` minimal-input-ready scans: {coverage['openmask3d_minimal_input_ready_scans']} / {coverage['bridge_scans']}",
            f"- Selected next route: `{route['selected_next_route']}`",
            f"- Next recommended unit: `{route['next_recommended_unit']}`",
            f"- Docker/model run launched: {coverage['docker_or_model_run_launched']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M64 supports moving to an `OpenMask3D` scene-format/model smoke plan as a feasibility step.",
            "- E003-M64 does not support claiming `OpenMask3D` improves search, proposal recall, or false positives yet.",
            "- E003-M64 keeps `Open3DSG`, `ConceptGraphs`, and `HOV-SG` as later map/scene-graph/navigation baselines.",
            "",
            "## 에이전트 추론",
            "",
            "- The direct bridge denominator is now strong enough to justify a constrained external 3D instance proposal baseline check.",
            "- The next step should prepare scene-format, model/checkpoint, adapter, and verification contracts before any long Docker/model job.",
            "- If scene-format conversion is blocked, expand the direct bridge denominator instead of spending compute on an unverified baseline path.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None. Continue to the next unit unless the scope changes.",
            "",
            "## Next Smoke Contract",
            "",
            f"- Contract id: `{smoke_contract['contract_id']}`",
            f"- Selected scans: {smoke_contract['selected_scans_for_first_smoke']}",
            f"- Selected labels: {smoke_contract['selected_prompt_labels']}",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--m47-dir", type=Path, default=DEFAULT_M47_DIR)
    parser.add_argument("--m58-dir", type=Path, default=DEFAULT_M58_DIR)
    parser.add_argument("--m61-dir", type=Path, default=DEFAULT_M61_DIR)
    parser.add_argument("--m63-dir", type=Path, default=DEFAULT_M63_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    m47 = load_json(args.m47_dir / "coverage.json")
    openmask = get_candidate(m47["candidate_routes"], "OpenMask3D")
    m58_coverage = load_json(args.m58_dir / "coverage.json")
    m61_failure_rows = load_jsonl(args.m61_dir / "failure_rows.jsonl")
    m63_coverage = load_json(args.m63_dir / "coverage.json")
    m63_row_outcomes = load_jsonl(args.m63_dir / "row_outcomes.jsonl")

    gap_rows = build_gap_rows(m63_row_outcomes, m61_failure_rows)
    scan_rows = build_scan_rows(m58_coverage, args.dataset_root)
    matrix_rows = build_feasibility_matrix(openmask, gap_rows, scan_rows)
    route = build_route(matrix_rows, gap_rows, scan_rows, openmask)
    smoke_contract = build_smoke_contract(route, scan_rows, gap_rows)
    coverage = build_coverage(gap_rows, scan_rows, matrix_rows, route, m63_coverage)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", route)
    write_json(args.out_dir / "smoke_contract.json", smoke_contract)
    write_jsonl(args.out_dir / "gap_rows.jsonl", gap_rows)
    write_jsonl(args.out_dir / "scan_input_status.jsonl", scan_rows)
    write_jsonl(args.out_dir / "feasibility_matrix.jsonl", matrix_rows)
    write_text(args.out_dir / "report.md", build_report(coverage, route, smoke_contract))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
