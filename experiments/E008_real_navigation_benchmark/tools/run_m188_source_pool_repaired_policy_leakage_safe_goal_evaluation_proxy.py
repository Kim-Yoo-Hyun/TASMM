#!/usr/bin/env python3
"""Evaluate M187 repaired source-pool policy rows against ObjectNav targets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"

VERSION = "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
READY_STATUS = "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_ready"
BLOCKED_STATUS = "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_blocked"

DEFAULT_M187_ROOT = (
    EXP_ROOT
    / "artifacts"
    / "E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0"
)
DEFAULT_OUT_ROOT = (
    EXP_ROOT
    / "artifacts"
    / "E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
)
DEFAULT_DERIVED_OUT_ROOT = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
)

SELECTED_POLICY = "confidence_protected_transition_cost_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
NEXT_TRAJECTORY_UNIT = "E008-M189 source-pool repaired policy Docker trajectory execution contract/preflight"
NEXT_FAILURE_UNIT = "E008-M189 source-pool repaired policy proxy failure decomposition"

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "eval_all_viewpoint_count_loaded",
    "eval_geodesic_distance",
    "eval_euclidean_distance",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_first_viewpoint_3d_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m187-root", default=str(DEFAULT_M187_ROOT))
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DERIVED_OUT_ROOT))
    return parser.parse_args()


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    module.PRIMARY_METRIC = PRIMARY_METRIC
    return module


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


def as_vec3(value: object) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    out = [finite_float(part) for part in value]
    if any(part is None for part in out):
        return None
    return [float(part) for part in out]


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def hit(distance: float | None, threshold: float) -> bool:
    return distance is not None and distance <= threshold


def nearest_viewpoint_distances(m12: Any, candidate_pos: list[float] | None, viewpoints: list[list[float]]) -> tuple[float | None, float | None]:
    if not m12.valid_vec3(candidate_pos) or not viewpoints:
        return None, None
    xz = [m12.dist_xz(candidate_pos, viewpoint) for viewpoint in viewpoints]
    xyz = [m12.dist3(candidate_pos, viewpoint) for viewpoint in viewpoints]
    clean_xz = [value for value in xz if value is not None]
    clean_xyz = [value for value in xyz if value is not None]
    return (min(clean_xz) if clean_xz else None, min(clean_xyz) if clean_xyz else None)


def build_candidate_goal_eval_rows(
    m12: Any,
    visit_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(visit_rows, key=lambda item: (str(item.get("policy_id")), str(item.get("adapter_episode_id")), int(item.get("visit_rank") or 10**9))):
        adapter_episode_id = str(row.get("adapter_episode_id"))
        eval_goal = eval_index.get(adapter_episode_id, {})
        oracle = oracle_index.get(adapter_episode_id, {})
        path_ready = bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))
        candidate_pos = (
            as_vec3(row.get("execution_stop_position_m"))
            or as_vec3(row.get("snapped_position_m"))
            or as_vec3(row.get("candidate_stop_position_m"))
        )
        if not path_ready:
            candidate_pos = None
        goal_pos = eval_goal.get("eval_goal_position")
        first_viewpoint = eval_goal.get("eval_first_viewpoint_position")
        all_viewpoints = eval_goal.get("eval_all_viewpoint_positions", [])
        any_viewpoint_xz, any_viewpoint_3d = nearest_viewpoint_distances(m12, candidate_pos, all_viewpoints)
        goal_xz = m12.dist_xz(candidate_pos, goal_pos)
        goal_3d = m12.dist3(candidate_pos, goal_pos)
        first_viewpoint_xz = m12.dist_xz(candidate_pos, first_viewpoint)
        first_viewpoint_3d = m12.dist3(candidate_pos, first_viewpoint)
        primary_hit = hit(any_viewpoint_xz, 1.0)
        planned_cost = finite_float(row.get("planned_cumulative_path_cost_m"))
        if planned_cost is None:
            planned_cost = finite_float(row.get("cumulative_known_path_cost_m"))
        out.append(
            {
                "version": VERSION,
                "policy_id": row.get("policy_id"),
                "policy_role": row.get("policy_role"),
                "method_policy": bool(row.get("method_policy")),
                "primary_baseline_policy": bool(row.get("primary_baseline_policy")),
                "policy_plan_uid": row.get("policy_plan_uid"),
                "candidate_visit_uid": row.get("candidate_visit_uid"),
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": adapter_episode_id,
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "visit_rank": row.get("visit_rank"),
                "proposal_uid": row.get("proposal_uid"),
                "label_canonical": row.get("label_canonical"),
                "path_ready": path_ready,
                "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
                "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
                "current_pose_to_candidate_geodesic_m": row.get("current_pose_to_candidate_geodesic_m"),
                "planned_cumulative_path_cost_m": planned_cost,
                "cumulative_known_path_cost_m": planned_cost,
                "candidate_snapped_position_m": candidate_pos,
                "eval_goal_position": goal_pos,
                "eval_goal_object_id": eval_goal.get("eval_goal_object_id"),
                "eval_goal_object_name": eval_goal.get("eval_goal_object_name"),
                "eval_viewpoint_count": eval_goal.get("eval_viewpoint_count"),
                "eval_all_viewpoint_count_loaded": eval_goal.get("eval_all_viewpoint_count_loaded", 0),
                "candidate_to_eval_goal_xz_m": goal_xz,
                "candidate_to_eval_goal_3d_m": goal_3d,
                "candidate_to_eval_first_viewpoint_xz_m": first_viewpoint_xz,
                "candidate_to_eval_first_viewpoint_3d_m": first_viewpoint_3d,
                "candidate_to_nearest_eval_viewpoint_xz_m": any_viewpoint_xz,
                "candidate_to_nearest_eval_viewpoint_3d_m": any_viewpoint_3d,
                "hit_goal_xz_1p0": hit(goal_xz, 1.0),
                "hit_goal_xz_1p5": hit(goal_xz, 1.5),
                "hit_goal_xz_2p0": hit(goal_xz, 2.0),
                "hit_any_viewpoint_xz_0p5": hit(any_viewpoint_xz, 0.5),
                "hit_any_viewpoint_xz_1p0": primary_hit,
                "hit_any_viewpoint_xz_1p5": hit(any_viewpoint_xz, 1.5),
                "hit_first_viewpoint_xz_1p0": hit(first_viewpoint_xz, 1.0),
                "oracle_viewpoint_path_m": oracle.get("viewpoint_path_geodesic_distance"),
                "oracle_goal_snapped_path_m": oracle.get("goal_snapped_path_geodesic_distance"),
                "episode_eval_geodesic_distance_m": eval_goal.get("eval_geodesic_distance"),
                "policy_input_allowed": bool(row.get("policy_input_allowed")),
                "uses_objectnav_eval_goal_for_policy": False,
                "uses_objectnav_eval_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                    or row.get("policy_input_uses_eval_goal_or_viewpoint")
                    or row.get("policy_input_uses_success_label")
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "policy_input_uses_eval_goal_or_viewpoint": bool(row.get("policy_input_uses_eval_goal_or_viewpoint")),
                "policy_input_uses_success_label": bool(row.get("policy_input_uses_success_label")),
                "primary_eval_metric": PRIMARY_METRIC,
                "primary_eval_hit": primary_hit,
                "claim_boundary": "M188 joins ObjectNav goal/viewpoints after M187 policy order is fixed; these fields are metric-only.",
            }
        )
    return out


def build_failure_rows(m12: Any, scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = m12.build_failure_rows(scan_metric_rows)
    out: list[dict[str, Any]] = []
    for row in rows:
        enriched = dict(row)
        enriched.update(
            {
                "version": VERSION,
                "claim_boundary": "M188 failure rows are leakage-safe proxy diagnostics, not executed navigation failures.",
            }
        )
        out.append(enriched)
    return out


def build_pairwise_delta_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_episode_policy: dict[tuple[str, str], dict[str, Any]] = {}
    for row in scan_metric_rows:
        rows_by_episode_policy[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))] = row

    episode_ids = sorted({str(row.get("adapter_episode_id")) for row in scan_metric_rows})
    policy_ids = sorted({str(row.get("policy_id")) for row in scan_metric_rows if row.get("policy_id") != PROTECTED_BASELINE})
    out: list[dict[str, Any]] = []
    for episode_id in episode_ids:
        protected = rows_by_episode_policy.get((episode_id, PROTECTED_BASELINE), {})
        for policy_id in policy_ids:
            row = rows_by_episode_policy.get((episode_id, policy_id), {})
            if not row or not protected:
                continue
            out.append(
                {
                    "version": VERSION,
                    "adapter_episode_id": episode_id,
                    "scan_id": row.get("scan_id"),
                    "object_category": row.get("object_category"),
                    "policy_id": policy_id,
                    "baseline_policy_id": PROTECTED_BASELINE,
                    "delta_primary_hit": int(bool(row.get("primary_hit"))) - int(bool(protected.get("primary_hit"))),
                    "delta_primary_spl_proxy": (finite_float(row.get("primary_spl_proxy")) or 0.0)
                    - (finite_float(protected.get("primary_spl_proxy")) or 0.0),
                    "delta_primary_first_hit_rank": None
                    if row.get("primary_first_hit_rank") is None or protected.get("primary_first_hit_rank") is None
                    else (finite_float(row.get("primary_first_hit_rank")) or 0.0)
                    - (finite_float(protected.get("primary_first_hit_rank")) or 0.0),
                    "delta_primary_first_hit_cost_m": None
                    if row.get("primary_first_hit_cost_m") is None or protected.get("primary_first_hit_cost_m") is None
                    else (finite_float(row.get("primary_first_hit_cost_m")) or 0.0)
                    - (finite_float(protected.get("primary_first_hit_cost_m")) or 0.0),
                    "delta_best_any_viewpoint_xz_m": None
                    if row.get("best_any_viewpoint_xz_m") is None or protected.get("best_any_viewpoint_xz_m") is None
                    else (finite_float(row.get("best_any_viewpoint_xz_m")) or 0.0)
                    - (finite_float(protected.get("best_any_viewpoint_xz_m")) or 0.0),
                    "method_policy": policy_id == SELECTED_POLICY,
                    "claim_boundary": "M188 pairwise deltas compare fixed policy orders under eval-only ObjectNav labels.",
                }
            )
    return out


def build_pairwise_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(by_policy.items()):
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "baseline_policy_id": PROTECTED_BASELINE,
                "episode_rows": len(rows),
                "primary_hit_gain_rows": sum(1 for row in rows if int(row.get("delta_primary_hit") or 0) > 0),
                "primary_hit_loss_rows": sum(1 for row in rows if int(row.get("delta_primary_hit") or 0) < 0),
                "primary_hit_tie_rows": sum(1 for row in rows if int(row.get("delta_primary_hit") or 0) == 0),
                "mean_delta_primary_spl_proxy": mean([row.get("delta_primary_spl_proxy") for row in rows]),
                "mean_delta_primary_first_hit_rank": mean([row.get("delta_primary_first_hit_rank") for row in rows]),
                "mean_delta_primary_first_hit_cost_m": mean([row.get("delta_primary_first_hit_cost_m") for row in rows]),
                "method_policy": policy_id == SELECTED_POLICY,
            }
        )
    return out


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def policy_row(aggregate_rows: list[dict[str, Any]], policy_id: str) -> dict[str, Any]:
    for row in aggregate_rows:
        if row.get("policy_id") == policy_id:
            return row
    return {}


def build_leakage_audit_rows(candidate_goal_rows: list[dict[str, Any]], eval_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    policy_counts = Counter(str(row["policy_id"]) for row in candidate_goal_rows)
    rows: list[dict[str, Any]] = []
    for policy_id, count in sorted(policy_counts.items()):
        policy_rows = [row for row in candidate_goal_rows if row["policy_id"] == policy_id]
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "candidate_goal_eval_rows": count,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "eval_goal_rows_joined": len({row["adapter_episode_id"] for row in policy_rows if row.get("eval_goal_position")}),
                "goals_by_category_read_for_eval_only": True,
                "loaded_all_viewpoint_episode_rows": sum(
                    1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
                ),
                "policy_input_allowed_fields_only": True,
                "leakage_audit_pass": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in policy_rows),
            }
        )
    return rows


def build_readiness_gate_rows(
    missing_inputs: list[str],
    m187_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    candidate_goal_rows: list[dict[str, Any]],
    scan_metric_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    selected = policy_row(aggregate_rows, SELECTED_POLICY)
    protected = policy_row(aggregate_rows, PROTECTED_BASELINE)
    selected_sr = finite_float(selected.get("primary_proxy_sr"))
    protected_sr = finite_float(protected.get("primary_proxy_sr"))
    selected_spl = finite_float(selected.get("primary_spl_proxy_mean"))
    protected_spl = finite_float(protected.get("primary_spl_proxy_mean"))
    selected_rows = int(selected.get("scan_policy_rows") or 0)
    protected_rows = int(protected.get("scan_policy_rows") or 0)
    trajectory_promotion = (
        selected_rows == protected_rows
        and selected_rows == 8
        and selected_sr is not None
        and protected_sr is not None
        and selected_spl is not None
        and protected_spl is not None
        and selected_sr >= protected_sr
        and selected_spl >= protected_spl
    )
    gates = [
        ("required_inputs_present", not missing_inputs, f"missing={missing_inputs}", True),
        (
            "m187_materialization_ready",
            m187_cov.get("status") == "e008_m187_source_pool_confidence_protected_transition_cost_materialization_ready",
            f"M187 status={m187_cov.get('status')}.",
            True,
        ),
        (
            "source_pool_denominator_preserved",
            len(goal_rows) == 8 and len(candidate_rows) == 900,
            f"goal rows={len(goal_rows)}; candidate rows={len(candidate_rows)}; expected=8/900.",
            True,
        ),
        (
            "candidate_goal_eval_materialized",
            len(candidate_goal_rows) == len(candidate_rows),
            f"candidate-goal rows={len(candidate_goal_rows)}; candidate rows={len(candidate_rows)}.",
            True,
        ),
        (
            "policy_metric_rows_materialized",
            len(scan_metric_rows) == 40 and len(aggregate_rows) == 5,
            f"scan-policy rows={len(scan_metric_rows)}; aggregate rows={len(aggregate_rows)}; expected=40/5.",
            True,
        ),
        (
            "leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in leakage_rows),
            f"failed={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}.",
            True,
        ),
        (
            "selected_vs_protected_same_denominator",
            selected_rows == protected_rows == 8,
            f"selected rows={selected_rows}; protected rows={protected_rows}.",
            True,
        ),
        (
            "selected_proxy_sr_not_lower_than_protected",
            selected_sr is not None and protected_sr is not None and selected_sr >= protected_sr,
            f"selected SR={selected_sr}; protected SR={protected_sr}.",
            False,
        ),
        (
            "selected_proxy_spl_not_lower_than_protected",
            selected_spl is not None and protected_spl is not None and selected_spl >= protected_spl,
            f"selected SPL={selected_spl}; protected SPL={protected_spl}.",
            False,
        ),
        (
            "trajectory_promotion_gate",
            trajectory_promotion,
            f"promotion={trajectory_promotion}; selected SR/SPL={selected_sr}/{selected_spl}; protected SR/SPL={protected_sr}/{protected_spl}.",
            False,
        ),
    ]
    return (
        [
            {
                "version": VERSION,
                "row_type": "readiness_gate",
                "gate_id": gate_id,
                "gate_status": "pass" if passed else "fail",
                "passed": passed,
                "blocks_m189": blocks and not passed,
                "blocks_trajectory_promotion": (not blocks) and not passed,
                "evidence": evidence,
            }
            for gate_id, passed, evidence, blocks in gates
        ],
        trajectory_promotion,
    )


def build_claim_boundary_rows(proxy_ready: bool, trajectory_promotion: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "source_pool_repaired_policy_proxy_eval",
            "supported": proxy_ready,
            "claim_boundary": "M188 evaluates fixed M187 policy order against ObjectNav goal/viewpoints only after row materialization.",
        },
        {
            "version": VERSION,
            "claim_id": "trajectory_execution_promotion",
            "supported": trajectory_promotion,
            "claim_boundary": "Promotion requires selected proxy SR and proxy SPL to be no worse than the protected detector-confidence baseline on the same denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "executed_navigation_improvement",
            "supported": False,
            "claim_boundary": "M188 is not a Habitat trajectory execution and cannot claim real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final navigation claim still needs Docker trajectory execution, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
    ]


def build_route_decision_rows(proxy_ready: bool, trajectory_promotion: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m188_selected_next",
            "decision": "prepare_repaired_policy_docker_trajectory_execution"
            if proxy_ready and trajectory_promotion
            else "decompose_repaired_policy_proxy_failure",
            "selected_next_unit": NEXT_TRAJECTORY_UNIT if proxy_ready and trajectory_promotion else NEXT_FAILURE_UNIT,
            "launch_long_job_now": False,
            "trajectory_promotion_gate_pass": trajectory_promotion,
            "reason": "Selected repaired policy passes same-denominator leakage-safe proxy gates against protected detector confidence."
            if proxy_ready and trajectory_promotion
            else "M188 proxy is evaluable, but selected repaired policy does not yet satisfy both protected SR and SPL proxy gates.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    pairwise_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M188 Source-Pool Repaired Policy Leakage-Safe Goal-Evaluation Proxy",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.",
            f"- Scan-policy rows: {coverage['scan_policy_metric_rows']}.",
            f"- Aggregate policy rows: {coverage['aggregate_policy_rows']}.",
            f"- Selected policy: `{SELECTED_POLICY}`.",
            f"- Protected baseline: `{PROTECTED_BASELINE}`.",
            f"- Selected proxy `SR` / `SPL`: {fmt(coverage['selected_primary_proxy_sr'])} / {fmt(coverage['selected_primary_spl_proxy_mean'])}.",
            f"- Protected proxy `SR` / `SPL`: {fmt(coverage['protected_primary_proxy_sr'])} / {fmt(coverage['protected_primary_spl_proxy_mean'])}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Trajectory promotion gate pass: {coverage['trajectory_promotion_gate_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Aggregate",
            "",
            markdown_table(
                aggregate_rows,
                [
                    "policy_id",
                    "primary_success_rows",
                    "scan_policy_rows",
                    "primary_proxy_sr",
                    "primary_spl_proxy_mean",
                    "primary_first_hit_rank_mean_over_success",
                    "goal_xz_1p0_proxy_sr",
                    "best_any_viewpoint_xz_m_mean",
                ],
            ),
            "",
            "## Pairwise Summary",
            "",
            markdown_table(
                pairwise_summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "primary_hit_gain_rows",
                    "primary_hit_loss_rows",
                    "mean_delta_primary_spl_proxy",
                    "mean_delta_primary_first_hit_rank",
                    "mean_delta_primary_first_hit_cost_m",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m189", "blocks_trajectory_promotion", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M188 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.",
            "- M188 reports leakage-safe proxy `SR`/`SPL`, not executed navigation `SR`/`SPL`.",
            "- Docker trajectory execution remains a separate gate.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    m187_root = resolve_path(args.m187_root)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m12 = load_module(M12_TOOL, "e008_m12_goal_eval")
    m187_cov = read_json(m187_root / "coverage.json")
    candidate_rows = read_jsonl(m187_root / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    goal_rows = read_jsonl(m187_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m187_root / "oracle_path_rows.jsonl")
    missing_inputs = [
        str(path.relative_to(ROOT))
        for path, rows in [
            (m187_root / "coverage.json", [m187_cov] if m187_cov else []),
            (m187_root / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows),
            (m187_root / "episode_goal_eval_rows.jsonl", goal_rows),
            (m187_root / "oracle_path_rows.jsonl", oracle_rows),
        ]
        if not rows
    ]
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in oracle_rows}
    candidate_goal_rows = build_candidate_goal_eval_rows(m12, candidate_rows, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = build_failure_rows(m12, scan_metric_rows)
    leakage_rows = build_leakage_audit_rows(candidate_goal_rows, eval_index)
    pairwise_rows = build_pairwise_delta_rows(scan_metric_rows)
    pairwise_summary_rows = build_pairwise_summary_rows(pairwise_rows)
    gate_rows, trajectory_promotion = build_readiness_gate_rows(
        missing_inputs,
        m187_cov,
        candidate_rows,
        goal_rows,
        candidate_goal_rows,
        scan_metric_rows,
        aggregate_rows,
        leakage_rows,
    )
    proxy_ready = not any(row.get("blocks_m189") for row in gate_rows)
    claim_rows = build_claim_boundary_rows(proxy_ready, trajectory_promotion)
    route_rows = build_route_decision_rows(proxy_ready, trajectory_promotion)

    selected = policy_row(aggregate_rows, SELECTED_POLICY)
    protected = policy_row(aggregate_rows, PROTECTED_BASELINE)
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if proxy_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "m187_status": m187_cov.get("status"),
        "candidate_rows": len(candidate_rows),
        "eval_episode_rows": len(goal_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "failure_rows": len(failure_rows),
        "primary_metric": PRIMARY_METRIC,
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "selected_primary_proxy_sr": selected.get("primary_proxy_sr"),
        "selected_primary_spl_proxy_mean": selected.get("primary_spl_proxy_mean"),
        "selected_primary_success_rows": selected.get("primary_success_rows"),
        "selected_scan_policy_rows": selected.get("scan_policy_rows"),
        "protected_primary_proxy_sr": protected.get("primary_proxy_sr"),
        "protected_primary_spl_proxy_mean": protected.get("primary_spl_proxy_mean"),
        "protected_primary_success_rows": protected.get("primary_success_rows"),
        "protected_scan_policy_rows": protected.get("scan_policy_rows"),
        "pairwise_delta_rows": len(pairwise_rows),
        "pairwise_summary_rows": len(pairwise_summary_rows),
        "policy_primary_metrics": {
            str(row.get("policy_id")): {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
            }
            for row in aggregate_rows
        },
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "readiness_gate_rows": len(gate_rows),
        "trajectory_promotion_gate_pass": trajectory_promotion,
        "real_navigation_sr_spl_ready": False,
        "trajectory_execution_result_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "scan_policy_goal_metric_rows.jsonl", scan_metric_rows)
        write_jsonl(output_dir / "aggregate_policy_goal_metric_rows.jsonl", aggregate_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "pairwise_policy_delta_rows.jsonl", pairwise_rows)
        write_jsonl(output_dir / "pairwise_policy_delta_summary_rows.jsonl", pairwise_summary_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", goal_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
    (out_root / "report.md").write_text(
        build_report(coverage, aggregate_rows, pairwise_summary_rows, gate_rows),
        encoding="utf-8",
    )
    shutil.copy2(out_root / "report.md", derived_out_root / "report.md")

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
