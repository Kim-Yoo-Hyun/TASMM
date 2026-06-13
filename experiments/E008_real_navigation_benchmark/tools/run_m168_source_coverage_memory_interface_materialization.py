#!/usr/bin/env python3
"""Materialize E008-M168 source-coverage memory-interface policy rows."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M156_DIR = EXP_ROOT / "artifacts" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
M167_DIR = EXP_ROOT / "artifacts" / "E008-M167_source_coverage_memory_interface_method_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M168_source_coverage_memory_interface_materialization_v0"

VERSION = "e008_m168_source_coverage_memory_interface_materialization_v0"
READY_STATUS = "e008_m168_source_coverage_memory_interface_materialization_ready"
BLOCKED_STATUS = "e008_m168_source_coverage_memory_interface_materialization_blocked"
NEXT_UNIT = "E008-M169 source-coverage memory-interface Docker trajectory execution contract / preflight"

SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
SOURCE_COVERAGE_ABLATION = "source_coverage_only_task_agnostic_v1"
CONFIDENCE_ONLY_ABLATION = "confidence_floor_only_v1"
PATH_ONLY_ABLATION = "path_cost_only_reachable_subset_v1"

POLICY_ROLES = {
    SELECTED_POLICY: "selected_source_coverage_memory_interface_policy",
    PROTECTED_BASELINE: "protected_detector_confidence_baseline",
    SOURCE_COVERAGE_ABLATION: "task_agnostic_source_coverage_ablation",
    CONFIDENCE_ONLY_ABLATION: "confidence_floor_only_ablation",
    PATH_ONLY_ABLATION: "path_cost_only_ablation",
}
POLICY_ORDER = [
    SELECTED_POLICY,
    PROTECTED_BASELINE,
    SOURCE_COVERAGE_ABLATION,
    CONFIDENCE_ONLY_ABLATION,
    PATH_ONLY_ABLATION,
]
CONFIDENCE_BAND_ABS = 0.05

FORBIDDEN_FIELDS = {
    "eval_goal_position",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "primary_eval_hit",
    "SR",
    "SPL",
    "success_proposal_uid",
    "candidate_to_nearest_eval_viewpoint_xz_m",
}


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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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


def int_value(value: object, default: int = 10**9) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def confidence(row: dict[str, Any]) -> float:
    return finite_float(row.get("confidence")) or 0.0


def path_cost(row: dict[str, Any]) -> float:
    for field in ["source_to_candidate_path_cost_m", "current_pose_to_candidate_geodesic_m", "cumulative_known_path_cost_m"]:
        value = finite_float(row.get(field))
        if value is not None:
            return value
    return 10**9


def detector_rank(row: dict[str, Any]) -> int:
    return int_value(row.get("m143_detector_visit_rank") or row.get("visit_rank"))


def shell_bucket(row: dict[str, Any]) -> str:
    value = finite_float(row.get("shell_radius_m"))
    if value is None:
        return "unknown"
    return f"{round(value, 1):.1f}"


def coverage_key(row: dict[str, Any]) -> str:
    return "::".join(
        [
            str(row.get("frame_pose_role") or "unknown"),
            str(row.get("bearing_relative_deg") or "unknown"),
            shell_bucket(row),
            str(row.get("observation_pose_id") or "unknown"),
        ]
    )


def source_gap(row: dict[str, Any]) -> bool:
    return bool(row.get("source_gap_flag") or row.get("source_coverage_gap_flag") or row.get("diagnostic_source_gap_boundary"))


def group_by_episode(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("benchmark_row_uid"))].append(row)
    return {key: sorted(value, key=detector_rank) for key, value in grouped.items()}


def source_coverage_order(detector_rows: list[dict[str, Any]], *, confidence_guarded: bool) -> list[dict[str, Any]]:
    if not detector_rows:
        return []
    if not confidence_guarded:
        return sorted(
            detector_rows,
            key=lambda row: (
                coverage_key(row),
                path_cost(row),
                -confidence(row),
                detector_rank(row),
            ),
        )
    bands: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in detector_rows:
        bands[int(math.floor(confidence(row) / CONFIDENCE_BAND_ABS))].append(row)
    ordered: list[dict[str, Any]] = []
    for band in sorted(bands, reverse=True):
        bucket_rows = sorted(bands[band], key=detector_rank)
        by_cov: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in bucket_rows:
            by_cov[coverage_key(row)].append(row)
        first_pass = []
        rest = []
        for cov_rows in by_cov.values():
            cov_sorted = sorted(cov_rows, key=lambda row: (path_cost(row), -confidence(row), detector_rank(row)))
            first_pass.append(cov_sorted[0])
            rest.extend(cov_sorted[1:])
        ordered.extend(sorted(first_pass, key=lambda row: (path_cost(row), -confidence(row), detector_rank(row))))
        ordered.extend(sorted(rest, key=detector_rank))
    return ordered


def policy_order(policy_id: str, detector_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detector_rows = sorted(detector_rows, key=detector_rank)
    if policy_id in {PROTECTED_BASELINE, CONFIDENCE_ONLY_ABLATION}:
        return detector_rows
    if policy_id == SELECTED_POLICY:
        return source_coverage_order(detector_rows, confidence_guarded=True)
    if policy_id == SOURCE_COVERAGE_ABLATION:
        return source_coverage_order(detector_rows, confidence_guarded=False)
    if policy_id == PATH_ONLY_ABLATION:
        return sorted(detector_rows, key=lambda row: (path_cost(row), -confidence(row), detector_rank(row)))
    raise ValueError(policy_id)


def blocked_hits(row: dict[str, Any]) -> list[str]:
    hits = [field for field in FORBIDDEN_FIELDS if field in row and row.get(field) not in {None, "", False, 0}]
    if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_eval_goal_or_viewpoint"):
        hits.append("uses_objectnav_eval_goal_or_viewpoint_for_policy")
    if row.get("uses_success_label_for_policy") or row.get("policy_input_uses_success_label"):
        hits.append("uses_success_label_for_policy")
    return sorted(set(hits))


def copy_policy_row(row: dict[str, Any], uid: str, policy_id: str, visit_rank: int, detector_rank_index: dict[str, int]) -> dict[str, Any]:
    proposal_uid = str(row.get("proposal_uid"))
    det_rank = detector_rank_index.get(proposal_uid, visit_rank)
    displacement = visit_rank - det_rank
    out = dict(row)
    out.update(
        {
            "version": VERSION,
            "row_type": "source_coverage_candidate",
            "claim_boundary": "M168 materializes source-coverage memory-interface rows only; no Habitat trajectory is executed.",
            "policy_id": policy_id,
            "policy_role": POLICY_ROLES[policy_id],
            "policy_plan_uid": f"m168::{uid}::{policy_id}",
            "candidate_visit_uid": f"m168::{uid}::{policy_id}::{visit_rank:04d}",
            "candidate_order_component": policy_id,
            "visit_rank": visit_rank,
            "m168_source_policy_id": PROTECTED_BASELINE,
            "m168_detector_visit_rank": det_rank,
            "m168_rank_displacement_from_detector": displacement,
            "m168_rank_displacement_abs_from_detector": abs(displacement),
            "m168_coverage_key": coverage_key(row),
            "m168_confidence_band_abs": CONFIDENCE_BAND_ABS,
            "m168_source_gap_prelabel": source_gap(row),
            "m168_policy_uses_source_coverage": policy_id in {SELECTED_POLICY, SOURCE_COVERAGE_ABLATION},
            "m168_policy_uses_memory_interface_guard": policy_id == SELECTED_POLICY,
            "m168_policy_uses_path_cost_tiebreak": policy_id in {SELECTED_POLICY, PATH_ONLY_ABLATION},
            "requires_cumulative_path_recompute_for_execution": policy_id not in {PROTECTED_BASELINE, CONFIDENCE_ONLY_ABLATION},
            "protected_baseline_policy_id": PROTECTED_BASELINE,
            "selected_policy_id": SELECTED_POLICY,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_success_label_for_policy": False,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
        }
    )
    return out


def build_audit(uid: str, policy_id: str, policy_rows: list[dict[str, Any]], detector_rows: list[dict[str, Any]]) -> dict[str, Any]:
    detector_order = [str(row.get("proposal_uid")) for row in detector_rows]
    policy_order_ids = [str(row.get("proposal_uid")) for row in policy_rows]
    blocked = sum(len(blocked_hits(row)) for row in policy_rows)
    displacements = [abs(int_value(row.get("m168_rank_displacement_from_detector"), 0)) for row in policy_rows]
    first10 = policy_rows[:10]
    detector_first10 = detector_rows[:10]
    return {
        "version": VERSION,
        "row_type": "policy_order_audit",
        "benchmark_row_uid": uid,
        "policy_id": policy_id,
        "candidate_rows": len(policy_rows),
        "detector_candidate_rows": len(detector_rows),
        "candidate_set_matches_detector": set(policy_order_ids) == set(detector_order),
        "order_changed_vs_detector": policy_order_ids != detector_order,
        "max_rank_displacement_abs_from_detector": max(displacements, default=0),
        "promoted_rows": sum(int_value(row.get("m168_rank_displacement_from_detector"), 0) < 0 for row in policy_rows),
        "demoted_rows": sum(int_value(row.get("m168_rank_displacement_from_detector"), 0) > 0 for row in policy_rows),
        "unique_coverage_keys_first10": len({row.get("m168_coverage_key") for row in first10}),
        "detector_unique_coverage_keys_first10": len({coverage_key(row) for row in detector_first10}),
        "source_gap_prelabel_rows": sum(bool(row.get("m168_source_gap_prelabel")) for row in policy_rows),
        "blocked_field_hits": blocked,
        "audit_pass": set(policy_order_ids) == set(detector_order) and len(policy_rows) == len(detector_rows) and blocked == 0,
    }


def materialize(base_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    for uid, detector_rows in sorted(group_by_episode(base_rows).items()):
        detector_rank_index = {str(row.get("proposal_uid")): idx for idx, row in enumerate(detector_rows, start=1)}
        detector_first10_cov = len({coverage_key(row) for row in detector_rows[:10]})
        for policy_id in POLICY_ORDER:
            ordered = policy_order(policy_id, detector_rows)
            policy_rows = [
                copy_policy_row(row, uid=uid, policy_id=policy_id, visit_rank=rank, detector_rank_index=detector_rank_index)
                for rank, row in enumerate(ordered, start=1)
            ]
            candidate_rows.extend(policy_rows)
            audit = build_audit(uid, policy_id, policy_rows, detector_rows)
            audit_rows.append(audit)
            if policy_id == SELECTED_POLICY:
                component_rows.append(
                    {
                        "version": VERSION,
                        "row_type": "source_coverage_component",
                        "benchmark_row_uid": uid,
                        "policy_id": policy_id,
                        "candidate_rows": len(policy_rows),
                        "detector_unique_coverage_keys_first10": detector_first10_cov,
                        "selected_unique_coverage_keys_first10": audit["unique_coverage_keys_first10"],
                        "coverage_gain_first10": audit["unique_coverage_keys_first10"] - detector_first10_cov,
                        "promoted_rows": audit["promoted_rows"],
                        "demoted_rows": audit["demoted_rows"],
                        "source_gap_prelabel_rows": audit["source_gap_prelabel_rows"],
                        "materialization_decision": "ready_for_execution_contract",
                    }
                )
    return candidate_rows, audit_rows, component_rows


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    plan_rows = []
    for (uid, policy_id), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: int_value(row.get("visit_rank")))
        first = ordered[0]
        cumulative = 0.0
        for row in ordered:
            cumulative += path_cost(row)
            row["m168_planned_cumulative_path_cost_proxy_m"] = cumulative
        plan_rows.append(
            {
                "version": VERSION,
                "row_type": "policy_plan",
                "benchmark_row_uid": uid,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "policy_plan_uid": f"m168::{uid}::{policy_id}",
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_rows": len(ordered),
                "path_ready_candidate_rows": sum(bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True)) for row in ordered),
                "first_proposal_uid": ordered[0].get("proposal_uid"),
                "last_proposal_uid": ordered[-1].get("proposal_uid"),
                "planned_cumulative_path_cost_proxy_m": cumulative,
                "requires_cumulative_path_recompute_for_execution": any(bool(row.get("requires_cumulative_path_recompute_for_execution")) for row in ordered),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
            }
        )
    return plan_rows


def leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for payload, rows in [("source_coverage_candidate_rows", candidate_rows), ("policy_plan_rows", plan_rows)]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in FORBIDDEN_FIELDS:
                if field in row and row.get(field) not in {None, "", False, 0}:
                    field_hits[field] += 1
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def split_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    rows = []
    for policy_id, group in sorted(by_policy.items()):
        rows.append(
            {
                "version": VERSION,
                "row_type": "source_ready_split",
                "policy_id": policy_id,
                "candidate_rows": len(group),
                "source_ready_rows": sum(bool(row.get("source_snap_validation_ready", True)) for row in group),
                "path_ready_rows": sum(bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True)) for row in group),
                "source_gap_prelabel_rows": sum(bool(row.get("m168_source_gap_prelabel")) for row in group),
                "unique_coverage_keys": len({row.get("m168_coverage_key") for row in group}),
            }
        )
    return rows


def claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "row_materialization_ready",
            "supported": True,
            "claim_boundary": "M168 materializes fixed policy rows and leakage audits only; no trajectory result is claimed.",
        },
        {
            "version": VERSION,
            "claim_id": "source_coverage_policy_improves_navigation",
            "supported": False,
            "claim_boundary": "Requires M169 contract, later Docker trajectory execution, and protected-baseline interpretation.",
        },
    ]


def route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_docker_trajectory_contract" if ready else "repair_m168_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M168 materialization",
            "launch_long_job_now": False,
            "docker_execution_contract_ready_next": ready,
        }
    ]


def report(coverage: dict[str, Any], audit: list[dict[str, Any]], split: list[dict[str, Any]]) -> str:
    selected_audit = [row for row in audit if row.get("policy_id") == SELECTED_POLICY]
    return "\n".join(
        [
            "# E008-M168 Source-Coverage Memory-Interface Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M167 status: `{coverage['m167_status']}`.",
            f"- Candidate rows: {coverage['source_coverage_candidate_rows']}.",
            f"- Policy plan rows: {coverage['policy_plan_rows']}.",
            f"- Selected changed episode rows: {coverage['selected_changed_episode_rows']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Selected Policy Audit",
            "",
            table(selected_audit[:10], ["benchmark_row_uid", "order_changed_vs_detector", "unique_coverage_keys_first10", "detector_unique_coverage_keys_first10", "promoted_rows", "audit_pass"]),
            "",
            "## Source Split",
            "",
            table(split, ["policy_id", "candidate_rows", "source_ready_rows", "path_ready_rows", "source_gap_prelabel_rows", "unique_coverage_keys"]),
            "",
            "## Claim Boundary",
            "",
            "- M168 does not execute `Habitat` trajectories.",
            "- Source-gap trigger remains inactive on this denominator.",
            "- Positive navigation claims require M169+ execution and interpretation.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m167 = read_json(M167_DIR / "coverage.json")
    base_rows = read_jsonl(M156_DIR / "base_candidate_rows.jsonl")
    missing = []
    if m167.get("status") != "e008_m167_source_coverage_memory_interface_method_contract_ready":
        missing.append("M167 ready coverage")
    if len(base_rows) != 900:
        missing.append("M156 base candidate rows")

    candidate_rows, audit, components = materialize(base_rows) if not missing else ([], [], [])
    plans = build_plan_rows(candidate_rows)
    leaks = leakage_rows(candidate_rows, plans)
    splits = split_rows(candidate_rows)

    counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    plan_counts = Counter(str(row.get("policy_id")) for row in plans)
    selected_audits = [row for row in audit if row.get("policy_id") == SELECTED_POLICY]
    ready = (
        not missing
        and len(candidate_rows) == 4500
        and set(counts.values()) == {900}
        and len(plans) == 150
        and set(plan_counts.values()) == {30}
        and all(row.get("audit_pass") for row in audit)
        and all(row.get("leakage_audit_pass") for row in leaks)
    )

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m167_status": m167.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "policy_ids": POLICY_ORDER,
        "policy_count": len(POLICY_ORDER),
        "source_coverage_candidate_rows": len(candidate_rows),
        "candidate_rows_by_policy": dict(sorted(counts.items())),
        "policy_plan_rows": len(plans),
        "policy_plan_counts": dict(sorted(plan_counts.items())),
        "policy_order_audit_rows": len(audit),
        "source_coverage_component_rows": len(components),
        "source_ready_split_rows": len(splits),
        "selected_changed_episode_rows": sum(bool(row.get("order_changed_vs_detector")) for row in selected_audits),
        "selected_promoted_rows": sum(int(row.get("promoted_rows") or 0) for row in selected_audits),
        "selected_mean_coverage_gain_first10": (
            sum(float(row.get("unique_coverage_keys_first10") or 0) - float(row.get("detector_unique_coverage_keys_first10") or 0) for row in selected_audits) / len(selected_audits)
            if selected_audits
            else None
        ),
        "source_gap_prelabel_rows": sum(int(row.get("source_gap_prelabel_rows") or 0) for row in audit if row.get("policy_id") == SELECTED_POLICY),
        "leakage_audit_rows": len(leaks),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leaks),
        "trajectory_contract_ready_next": ready,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M168 materialization",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_coverage_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "policy_plan_rows.jsonl", plans)
    write_jsonl(ARTIFACT_DIR / "policy_order_audit_rows.jsonl", audit)
    write_jsonl(ARTIFACT_DIR / "source_coverage_component_rows.jsonl", components)
    write_jsonl(ARTIFACT_DIR / "source_ready_split_rows.jsonl", splits)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leaks)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows())
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows(ready))
    (ARTIFACT_DIR / "report.md").write_text(report(coverage, audit, splits), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
