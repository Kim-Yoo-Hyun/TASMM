#!/usr/bin/env python3
"""Fix the E008-M132 target-free trajectory-aware visit-order repair contract."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M126_DIR = EXP_ROOT / "artifacts" / "E008-M126_target_free_detector_candidate_visit_order_path_smoke_v0"
M129_DIR = EXP_ROOT / "artifacts" / "E008-M129_target_free_detector_policy_trajectory_contract_v0"
M130_DIR = EXP_ROOT / "artifacts" / "E008-M130_target_free_detector_policy_trajectory_execution_smoke_v0"
M131_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M132_target_free_trajectory_aware_visit_order_repair_contract_v0"
)

VERSION = "e008_m132_target_free_trajectory_aware_visit_order_repair_contract_v0"
READY_STATUS = "e008_m132_target_free_trajectory_aware_visit_order_repair_contract_ready"
BLOCKED_STATUS = "e008_m132_target_free_trajectory_aware_visit_order_repair_contract_blocked"
NEXT_UNIT = "E008-M133 target-free trajectory-aware visit-order repair materialization smoke"

HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
M133_SCRIPT = "experiments/E008_real_navigation_benchmark/tools/run_m133_target_free_trajectory_aware_visit_order_repair_materialization.py"

METHOD_POLICY = "path_cost_ascending_reachable_subset_v0"
PRIMARY_DETECTOR_POLICY = "detector_confidence_reachable_subset_v0"
SELECTED_REPAIR_POLICY = "trajectory_greedy_confidence_path_repair_v0"
PAIRWISE_MATRIX_ID = "candidate_to_candidate_geodesic_matrix_v0"

BLOCKED_POLICY_FIELDS = [
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
]


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def policy_rows(rows: list[dict[str, Any]], policy_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("policy_id") == policy_id]


def policy_metric(metric_rows: list[dict[str, Any]], policy_id: str) -> dict[str, Any]:
    for row in metric_rows:
        if row.get("metric_scope") == "policy_aggregate" and row.get("policy_id") == policy_id:
            return row
    return {}


def build_failure_to_repair_rows(
    failure_rows: list[dict[str, Any]],
    m130_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_by_policy = {
        str(row.get("policy_id")): row for row in m130_metric_rows if row.get("metric_scope") == "policy_aggregate"
    }
    out: list[dict[str, Any]] = []
    for row in failure_rows:
        policy_id = str(row.get("policy_id"))
        metric = metric_by_policy.get(policy_id, {})
        if policy_id in {METHOD_POLICY, "confidence_path_cost_tradeoff_reachable_subset_v0"}:
            repair_need = "replace_myopic_source_to_candidate_order_with_current_pose_to_candidate_trajectory_cost"
            repair_priority = "high"
        elif policy_id == PRIMARY_DETECTOR_POLICY:
            repair_need = "keep_as_primary_strong_baseline_and_compare_repair_against_it"
            repair_priority = "baseline"
        else:
            repair_need = "keep_as_candidate_accounting_baseline"
            repair_priority = "baseline"
        out.append(
            {
                "version": VERSION,
                "row_type": "failure_to_repair_contract",
                "policy_id": policy_id,
                "m130_SR": metric.get("SR"),
                "m130_SPL": metric.get("SPL"),
                "success_rank": row.get("success_rank"),
                "executed_no_success_before_success": row.get("executed_no_success_before_success"),
                "wasted_path_before_success_m": row.get("wasted_path_before_success_m"),
                "mean_unsuccessful_stop_to_nearest_eval_viewpoint_xz_m": row.get(
                    "mean_unsuccessful_stop_to_nearest_eval_viewpoint_xz_m"
                ),
                "failure_mechanism": row.get("failure_mechanism"),
                "repair_need": repair_need,
                "repair_priority": repair_priority,
                "claim_boundary": "M132 uses M130/M131 only to define a repair contract; it does not create repaired trajectory results.",
            }
        )
    return out


def build_allowed_input_rows() -> list[dict[str, Any]]:
    allowed = [
        ("candidate_stop_position_m", "candidate stop on navmesh from M125/M129"),
        ("candidate_position_m", "detector-derived 3D candidate centroid"),
        ("confidence", "detector confidence score"),
        ("selection_score", "detector/ranker score before eval-only labels"),
        ("candidate_rank_m09", "detector candidate rank"),
        ("label_canonical", "detector canonical label"),
        ("path_ready", "navmesh/source-readiness flag"),
        ("source_to_candidate_path_cost_m", "start/source to candidate geodesic for first-step prior only"),
        ("current_robot_pose_m", "online pose after each executed stop"),
        ("current_pose_to_candidate_geodesic_m", "runtime pathfinder cost from current pose to remaining candidate"),
        ("candidate_to_candidate_geodesic_m", "precomputed or runtime path between candidate stops"),
        ("blocked_candidate_for_path_policy", "candidate path usability flag"),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "allowed_input",
            "field": field,
            "source": source,
            "allowed_for_policy": True,
            "uses_objectnav_eval_goal_or_viewpoint": False,
            "uses_success_label": False,
        }
        for field, source in allowed
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "blocked_input",
            "field": field,
            "blocked_for_policy": True,
            "reason": "ObjectNav eval goal/viewpoint, success label, or posthoc metric-only distance cannot decide candidate order.",
        }
        for field in BLOCKED_POLICY_FIELDS
    ]


def build_trajectory_cost_contract_rows(path_ready_count: int) -> list[dict[str, Any]]:
    directed_pairs = path_ready_count * max(path_ready_count - 1, 0)
    return [
        {
            "version": VERSION,
            "row_type": "trajectory_cost_contract",
            "matrix_id": PAIRWISE_MATRIX_ID,
            "candidate_universe": "path_ready_label_compatible_candidates",
            "path_ready_candidate_rows": path_ready_count,
            "required_start_to_candidate_rows": path_ready_count,
            "required_candidate_to_candidate_directed_rows": directed_pairs,
            "cost_source": "Habitat pathfinder geodesic distance on HM3D navmesh",
            "allowed_policy_use": "current_pose_to_candidate_geodesic_m may update after each executed or planned stop",
            "blocked_policy_use": "Do not use eval goal/viewpoint coordinates, hit labels, or nearest eval-viewpoint distances.",
            "m133_output_file": "trajectory_cost_matrix_rows.jsonl",
            "m133_ready_gate": path_ready_count > 0,
        }
    ]


def build_policy_repair_contract_rows(path_ready_count: int) -> list[dict[str, Any]]:
    common = {
        "version": VERSION,
        "row_type": "policy_repair_contract",
        "candidate_universe": "path_ready_label_compatible_candidates",
        "requires_trajectory_cost_matrix": True,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_success_label_for_policy": False,
        "path_ready_candidate_rows": path_ready_count,
        "m133_materialize": True,
        "m134_execute": True,
    }
    return [
        {
            **common,
            "policy_id": SELECTED_REPAIR_POLICY,
            "policy_role": "selected_repair_policy",
            "ranking_form": (
                "online greedy: at each decision step score remaining candidate by detector confidence minus "
                "normalized current-pose geodesic cost, with source-to-candidate cost only as a first-step/tie prior"
            ),
            "primary_expected_fix": "avoid many target-far low-source-cost stops before success",
            "required_comparison": PRIMARY_DETECTOR_POLICY,
            "pass_condition_for_next_execution": "materialized rows preserve detector candidate universe and leakage audit passes",
        },
        {
            **common,
            "policy_id": "trajectory_greedy_confidence_only_reachable_v0",
            "policy_role": "trajectory_repair_ablation_confidence_only",
            "ranking_form": "online greedy confidence ordering over path-ready candidates without path-cost penalty",
            "primary_expected_fix": "tests whether repair gain is only detector confidence rather than trajectory cost",
            "required_comparison": PRIMARY_DETECTOR_POLICY,
            "pass_condition_for_next_execution": "materialized rows available for ablation execution",
        },
        {
            **common,
            "policy_id": "trajectory_greedy_path_only_reachable_v0",
            "policy_role": "trajectory_repair_ablation_path_only",
            "ranking_form": "online greedy nearest-next-candidate geodesic ordering over path-ready candidates",
            "primary_expected_fix": "tests whether path efficiency alone destroys semantic confidence",
            "required_comparison": PRIMARY_DETECTOR_POLICY,
            "pass_condition_for_next_execution": "materialized rows available for ablation execution",
        },
        {
            **common,
            "policy_id": PRIMARY_DETECTOR_POLICY,
            "policy_role": "primary_strong_baseline_to_preserve",
            "ranking_form": "detector confidence over reachable subset",
            "primary_expected_fix": "baseline preservation, not a repair",
            "required_comparison": SELECTED_REPAIR_POLICY,
            "pass_condition_for_next_execution": "same candidate universe and metric denominator retained",
        },
        {
            **common,
            "policy_id": METHOD_POLICY,
            "policy_role": "negative_historical_path_cost_baseline",
            "ranking_form": "source-to-candidate path-cost ascending",
            "primary_expected_fix": "none; retained to demonstrate M131 failure mechanism",
            "required_comparison": SELECTED_REPAIR_POLICY,
            "pass_condition_for_next_execution": "same denominator retained for before/after comparison",
        },
    ]


def build_m133_materialization_plan_rows() -> list[dict[str, Any]]:
    docker_cmd = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        f"-v {RESEARCH3_DATA_ROOT}:/data:ro -v {ROOT}:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        f"{M133_SCRIPT} "
        "--m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0\""
    )
    return [
        {
            "version": VERSION,
            "row_type": "m133_materialization_plan",
            "selected_next_unit": NEXT_UNIT,
            "requires_docker": True,
            "docker_image": HABITAT_IMAGE,
            "source_data_mount": f"{RESEARCH3_DATA_ROOT}:/data:ro",
            "workspace_mount": f"{ROOT}:/work",
            "script_to_implement": M133_SCRIPT,
            "input_artifact": "experiments/E008_real_navigation_benchmark/artifacts/E008-M129_target_free_detector_policy_trajectory_contract_v0",
            "output_artifact": "experiments/E008_real_navigation_benchmark/artifacts/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0",
            "derived_output": "local_dataset/HM3D_navigation_bridge/E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0",
            "expected_files": [
                "coverage.json",
                "trajectory_cost_matrix_rows.jsonl",
                "trajectory_repair_candidate_rows.jsonl",
                "trajectory_repair_execution_plan_rows.jsonl",
                "leakage_audit_rows.jsonl",
                "readiness_gate_rows.jsonl",
                "report.md",
            ],
            "exact_command_template": docker_cmd,
            "long_running_job": False,
            "claim_boundary": "M133 materializes repair rows and path matrix only; executed SR/SPL remains blocked until the next trajectory runner.",
        }
    ]


def build_readiness_gate_rows(
    missing_inputs: list[str],
    m131_ready: bool,
    path_ready_count: int,
    blocked_input_hits: int,
    repair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            "M126/M129/M130/M131 artifacts required for M132 are present.",
            True,
        ),
        (
            "m131_result_ready",
            m131_ready,
            "M131 interpretation artifact is ready and selects repair-before-scale.",
            True,
        ),
        (
            "path_ready_candidate_universe_nonempty",
            path_ready_count > 0,
            "M129 contains path-ready target-free candidates for trajectory repair.",
            True,
        ),
        (
            "blocked_policy_fields_absent_from_contract_inputs",
            blocked_input_hits == 0,
            "Policy input rows used for repair contract avoid eval-goal/viewpoint/success fields.",
            True,
        ),
        (
            "repair_policy_contract_ready",
            len(repair_rows) >= 5,
            "Selected repair policy, ablations, and baselines are fixed.",
            True,
        ),
        (
            "scale_current_path_cost_policy",
            False,
            "M131 rejects scale-up of source-to-candidate path-cost ordering.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m133": blocks_m133 and not passed,
            "rationale": rationale,
        }
        for gate_id, passed, rationale, blocks_m133 in gates
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_repair_contract",
            "supported": True,
            "claim_boundary": "M132 fixes a trajectory-aware repair contract and allowed/blocked inputs for M133.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repaired_navigation_improvement",
            "supported": False,
            "claim_boundary": "M132 does not materialize or execute repaired trajectories.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final SR/SPL needs repaired execution, scale, heldout transfer, and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M132 is target-free trajectory repair; it does not change the E006 human-intent claim boundary.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision": "select_m133_trajectory_aware_repair_materialization" if ready else "repair_m132_inputs_first",
            "selected_next_unit": NEXT_UNIT if ready else None,
            "reason": (
                "M132 has enough evidence to define a repair contract; next materialize pairwise/current-pose trajectory costs and repaired visit-order rows."
                if ready
                else "Required inputs or contract gates are missing."
            ),
            "launch_long_job_now": False,
            "scale_current_path_cost_policy": False,
            "final_real_navigation_sr_spl_ready": False,
            "deployable_search_policy_ready": False,
        }
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    failure_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# E008-M132 Target-Free Trajectory-Aware Visit-Order Repair Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M131 status: `{coverage.get('m131_status')}`.",
        f"- Path-ready candidate rows: {coverage['path_ready_candidate_rows']}.",
        f"- Selected repair policy: `{coverage['selected_repair_policy']}`.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Failure-To-Repair",
        "",
        markdown_table(
            failure_rows,
            [
                "policy_id",
                "m130_SPL",
                "success_rank",
                "wasted_path_before_success_m",
                "repair_need",
                "repair_priority",
            ],
        ),
        "",
        "## Repair Policies",
        "",
        markdown_table(
            repair_rows,
            ["policy_id", "policy_role", "ranking_form", "required_comparison"],
        ),
        "",
        "## Gates",
        "",
        markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m133", "rationale"]),
        "",
        "## Decision",
        "",
    ]
    for row in route_rows:
        lines.append(f"- {row['decision']}: {row['reason']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    m126_coverage = read_json(M126_DIR / "coverage.json")
    m129_coverage = read_json(M129_DIR / "coverage.json")
    m130_coverage = read_json(M130_DIR / "coverage.json")
    m131_coverage = read_json(M131_DIR / "coverage.json")
    m129_candidates = read_jsonl(M129_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    m130_metrics = read_jsonl(M130_DIR / "dynamic_stale_trajectory_policy_metric_rows.jsonl")
    m131_failures = read_jsonl(M131_DIR / "failure_diagnosis_rows.jsonl")

    required = {
        "m126_coverage": m126_coverage,
        "m129_coverage": m129_coverage,
        "m130_coverage": m130_coverage,
        "m131_coverage": m131_coverage,
        "m129_candidates": m129_candidates,
        "m130_metrics": m130_metrics,
        "m131_failures": m131_failures,
    }
    missing_inputs = [name for name, value in required.items() if not value]
    m131_ready = m131_coverage.get("status") == "e008_m131_target_free_detector_policy_trajectory_result_interpretation_scale_decision_ready"
    path_ready_candidates = [
        row
        for row in policy_rows(m129_candidates, PRIMARY_DETECTOR_POLICY)
        if row.get("path_ready") and not row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    ]
    path_ready_count = len(path_ready_candidates)
    blocked_input_hits = sum(1 for row in m129_candidates for field in BLOCKED_POLICY_FIELDS if field in row)

    failure_rows = build_failure_to_repair_rows(m131_failures, m130_metrics)
    allowed_rows = build_allowed_input_rows()
    blocked_rows = build_blocked_input_rows()
    cost_rows = build_trajectory_cost_contract_rows(path_ready_count)
    repair_rows = build_policy_repair_contract_rows(path_ready_count)
    plan_rows = build_m133_materialization_plan_rows()
    gate_rows = build_readiness_gate_rows(missing_inputs, m131_ready, path_ready_count, blocked_input_hits, repair_rows)
    ready = not any(row["blocks_m133"] for row in gate_rows)
    route_rows = build_route_decision_rows(ready)
    claim_rows = build_claim_boundary_rows()

    status = READY_STATUS if ready else BLOCKED_STATUS
    policy_counter = Counter(str(row.get("policy_id")) for row in m129_candidates)
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "missing_inputs": missing_inputs,
        "m126_status": m126_coverage.get("status"),
        "m129_status": m129_coverage.get("status"),
        "m130_status": m130_coverage.get("status"),
        "m131_status": m131_coverage.get("status"),
        "m131_proxy_to_trajectory_flip_detected": bool(m131_coverage.get("proxy_to_trajectory_flip_detected")),
        "m131_scale_current_path_cost_policy_ready": bool(m131_coverage.get("scale_current_path_cost_policy_ready")),
        "m129_candidate_rows": len(m129_candidates),
        "candidate_rows_by_policy": dict(sorted(policy_counter.items())),
        "path_ready_candidate_rows": path_ready_count,
        "blocked_policy_field_hits_in_m129_candidate_rows": blocked_input_hits,
        "failure_to_repair_rows": len(failure_rows),
        "policy_repair_contract_rows": len(repair_rows),
        "allowed_input_rows": len(allowed_rows),
        "blocked_input_rows": len(blocked_rows),
        "trajectory_cost_contract_rows": len(cost_rows),
        "readiness_gate_rows": len(gate_rows),
        "selected_repair_policy": SELECTED_REPAIR_POLICY,
        "selected_pairwise_matrix_id": PAIRWISE_MATRIX_ID,
        "selected_next_unit": NEXT_UNIT if ready else None,
        "scale_current_path_cost_policy_ready": False,
        "repaired_trajectory_rows_ready": False,
        "final_real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "failure_to_repair_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "allowed_input_rows.jsonl", allowed_rows)
        write_jsonl(output_dir / "blocked_input_rows.jsonl", blocked_rows)
        write_jsonl(output_dir / "trajectory_cost_contract_rows.jsonl", cost_rows)
        write_jsonl(output_dir / "policy_repair_contract_rows.jsonl", repair_rows)
        write_jsonl(output_dir / "m133_materialization_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_report(output_dir / "report.md", coverage, failure_rows, repair_rows, gate_rows, route_rows)

    if ARTIFACT_DIR != DATA_OUT_DIR:
        for filename in (
            "coverage.json",
            "failure_to_repair_rows.jsonl",
            "allowed_input_rows.jsonl",
            "blocked_input_rows.jsonl",
            "trajectory_cost_contract_rows.jsonl",
            "policy_repair_contract_rows.jsonl",
            "m133_materialization_plan_rows.jsonl",
            "readiness_gate_rows.jsonl",
            "claim_boundary_rows.jsonl",
            "route_decision_rows.jsonl",
            "report.md",
        ):
            src = ARTIFACT_DIR / filename
            dst = DATA_OUT_DIR / filename
            if src.exists() and src.resolve() != dst.resolve():
                shutil.copy2(src, dst)

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True, allow_nan=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
