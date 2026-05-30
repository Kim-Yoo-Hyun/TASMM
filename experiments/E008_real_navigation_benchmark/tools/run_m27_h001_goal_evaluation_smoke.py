#!/usr/bin/env python3
"""Evaluate H001 visit-order rows against ObjectNav targets as eval-only labels."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M27_h001_goal_evaluation_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M27_h001_goal_evaluation_smoke_v0"
M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M26_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M26_h001_visit_order_path_smoke_v0"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
VERSION = "e008_m27_h001_goal_evaluation_smoke_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"


def load_m12_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m12_goal_eval", M12_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M12_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    return module


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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def safe_ratio(num: int, den: int) -> float | None:
    return round(float(num) / float(den), 6) if den else None


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def valid_vec3(vec: object) -> bool:
    if not isinstance(vec, list) or len(vec) != 3:
        return False
    return all(finite_float(value) is not None for value in vec)


def dist3(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def dist_xz(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[2]) - float(b[2])) ** 2))


def nearest_viewpoint_distances(candidate_pos: list[float] | None, viewpoints: list[list[float]]) -> tuple[float | None, float | None]:
    if not valid_vec3(candidate_pos) or not viewpoints:
        return None, None
    xz = [dist_xz(candidate_pos, viewpoint) for viewpoint in viewpoints]
    xyz = [dist3(candidate_pos, viewpoint) for viewpoint in viewpoints]
    return min(value for value in xz if value is not None), min(value for value in xyz if value is not None)


def hit(distance: float | None, threshold: float) -> bool:
    return distance is not None and distance <= threshold


def oracle_path(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    for key in (
        "oracle_viewpoint_path_m",
        "episode_eval_geodesic_distance_m",
        "oracle_goal_snapped_path_m",
        "viewpoint_path_geodesic_distance",
        "eval_geodesic_distance",
        "goal_snapped_path_geodesic_distance",
    ):
        value = finite_float(row.get(key))
        if value is not None:
            return value
    return None


def build_candidate_goal_eval_rows(
    visit_rows: list[dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in visit_rows:
        eval_goal = eval_index.get(str(row.get("adapter_episode_id")), {})
        oracle = oracle_index.get(str(row.get("adapter_episode_id")), {})
        candidate_pos = row.get("candidate_stop_position_m") if row.get("path_ready") else None
        goal_pos = eval_goal.get("eval_goal_position")
        first_viewpoint = eval_goal.get("eval_first_viewpoint_position")
        all_viewpoints = eval_goal.get("eval_all_viewpoint_positions", [])
        any_viewpoint_xz, any_viewpoint_3d = nearest_viewpoint_distances(candidate_pos, all_viewpoints)
        goal_xz = dist_xz(candidate_pos, goal_pos)
        goal_3d = dist3(candidate_pos, goal_pos)
        first_viewpoint_xz = dist_xz(candidate_pos, first_viewpoint)
        first_viewpoint_3d = dist3(candidate_pos, first_viewpoint)
        primary_hit = hit(any_viewpoint_xz, 1.0)
        rows.append(
            {
                "version": VERSION,
                "candidate_goal_eval_uid": f"m27::{row.get('candidate_visit_uid')}",
                "candidate_visit_uid": row.get("candidate_visit_uid"),
                "policy_plan_uid": row.get("policy_plan_uid"),
                "policy_id": row.get("policy_id"),
                "policy_family": row.get("policy_family"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "source_role": row.get("source_role"),
                "candidate_order_component": row.get("candidate_order_component"),
                "candidate_visit_order_contract": row.get("candidate_visit_order_contract"),
                "visit_rank": row.get("visit_order_index"),
                "proposal_uid": row.get("proposal_uid"),
                "raw_candidate_uid": row.get("raw_candidate_uid"),
                "frame_id": row.get("frame_id"),
                "label_canonical": row.get("label_canonical"),
                "path_ready": bool(row.get("path_ready")),
                "candidate_stop_position_m": candidate_pos,
                "candidate_position_m": row.get("candidate_position_m"),
                "candidate_source_position_m": row.get("candidate_source_position_m"),
                "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
                "cumulative_known_path_cost_m": row.get("cumulative_known_path_cost_m"),
                "eval_goal_position": goal_pos,
                "eval_goal_object_id": eval_goal.get("eval_goal_object_id"),
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
                "uses_objectnav_eval_goal_for_policy": bool(row.get("uses_objectnav_eval_goal")),
                "uses_objectnav_eval_viewpoint_for_policy": bool(row.get("uses_objectnav_eval_viewpoint")),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(row.get("uses_objectnav_eval_goal"))
                or bool(row.get("uses_objectnav_eval_viewpoint")),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "primary_eval_metric": PRIMARY_METRIC,
                "primary_eval_hit": primary_hit,
                "real_navigation_sr_spl_ready": False,
            }
        )
    return rows


def first_hit_row(rows: list[dict[str, Any]], hit_key: str) -> dict[str, Any] | None:
    for row in sorted(rows, key=lambda item: int(item.get("visit_rank") or 10**9)):
        if row.get(hit_key):
            return row
    return None


def best_distance(rows: list[dict[str, Any]], distance_key: str) -> tuple[float | None, int | None]:
    valid = [(finite_float(row.get(distance_key)), int(row.get("visit_rank") or 10**9)) for row in rows]
    valid = [(distance, rank) for distance, rank in valid if distance is not None]
    if not valid:
        return None, None
    return min(valid, key=lambda item: item[0])


def spl_proxy(hit_row: dict[str, Any] | None) -> float:
    if not hit_row:
        return 0.0
    oracle = oracle_path(hit_row)
    cost = finite_float(hit_row.get("cumulative_known_path_cost_m"))
    if oracle is None or cost is None or cost <= 0:
        return 0.0
    return float(oracle / max(oracle, cost))


def summarize_policy_plan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("empty policy-plan rows")
    first_primary = first_hit_row(rows, "hit_any_viewpoint_xz_1p0")
    first_vp05 = first_hit_row(rows, "hit_any_viewpoint_xz_0p5")
    first_vp15 = first_hit_row(rows, "hit_any_viewpoint_xz_1p5")
    first_goal10 = first_hit_row(rows, "hit_goal_xz_1p0")
    first_goal15 = first_hit_row(rows, "hit_goal_xz_1p5")
    best_goal_xz, best_goal_rank = best_distance(rows, "candidate_to_eval_goal_xz_m")
    best_vp_xz, best_vp_rank = best_distance(rows, "candidate_to_nearest_eval_viewpoint_xz_m")
    first_row = rows[0]
    return {
        "version": VERSION,
        "metric_scope": "scan_policy",
        "policy_plan_uid": first_row.get("policy_plan_uid"),
        "policy_id": first_row.get("policy_id"),
        "policy_family": first_row.get("policy_family"),
        "adapter_episode_id": first_row.get("adapter_episode_id"),
        "scan_id": first_row.get("scan_id"),
        "scene_key": first_row.get("scene_key"),
        "object_category": first_row.get("object_category"),
        "task_context_id": first_row.get("task_context_id"),
        "candidate_rows": len(rows),
        "path_ready_rows": sum(1 for row in rows if row.get("path_ready")),
        "primary_metric": PRIMARY_METRIC,
        "primary_hit": first_primary is not None,
        "primary_first_hit_rank": first_primary.get("visit_rank") if first_primary else None,
        "primary_first_hit_cost_m": first_primary.get("cumulative_known_path_cost_m") if first_primary else None,
        "primary_spl_proxy": spl_proxy(first_primary),
        "any_viewpoint_xz_0p5_hit": first_vp05 is not None,
        "any_viewpoint_xz_0p5_first_rank": first_vp05.get("visit_rank") if first_vp05 else None,
        "any_viewpoint_xz_1p0_hit": first_primary is not None,
        "any_viewpoint_xz_1p0_first_rank": first_primary.get("visit_rank") if first_primary else None,
        "any_viewpoint_xz_1p5_hit": first_vp15 is not None,
        "any_viewpoint_xz_1p5_first_rank": first_vp15.get("visit_rank") if first_vp15 else None,
        "goal_xz_1p0_hit": first_goal10 is not None,
        "goal_xz_1p0_first_rank": first_goal10.get("visit_rank") if first_goal10 else None,
        "goal_xz_1p5_hit": first_goal15 is not None,
        "goal_xz_1p5_first_rank": first_goal15.get("visit_rank") if first_goal15 else None,
        "best_goal_xz_m": best_goal_xz,
        "best_goal_xz_rank": best_goal_rank,
        "best_any_viewpoint_xz_m": best_vp_xz,
        "best_any_viewpoint_xz_rank": best_vp_rank,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "real_navigation_sr_spl_ready": False,
    }


def summarize_aggregate(rows: list[dict[str, Any]], scope: str, keys: dict[str, Any]) -> dict[str, Any]:
    primary_hits = [row for row in rows if row.get("primary_hit")]
    vp05_hits = [row for row in rows if row.get("any_viewpoint_xz_0p5_hit")]
    vp15_hits = [row for row in rows if row.get("any_viewpoint_xz_1p5_hit")]
    goal10_hits = [row for row in rows if row.get("goal_xz_1p0_hit")]
    goal15_hits = [row for row in rows if row.get("goal_xz_1p5_hit")]
    primary_ranks = [
        finite_float(row.get("primary_first_hit_rank")) for row in primary_hits if row.get("primary_first_hit_rank") is not None
    ]
    primary_costs = [
        finite_float(row.get("primary_first_hit_cost_m")) for row in primary_hits if row.get("primary_first_hit_cost_m") is not None
    ]
    best_goal = [finite_float(row.get("best_goal_xz_m")) for row in rows if row.get("best_goal_xz_m") is not None]
    best_vp = [finite_float(row.get("best_any_viewpoint_xz_m")) for row in rows if row.get("best_any_viewpoint_xz_m") is not None]
    primary_ranks_f = [value for value in primary_ranks if value is not None]
    primary_costs_f = [value for value in primary_costs if value is not None]
    best_goal_f = [value for value in best_goal if value is not None]
    best_vp_f = [value for value in best_vp if value is not None]
    denominator = len(rows)
    return {
        "version": VERSION,
        "metric_scope": scope,
        **keys,
        "scan_policy_rows": denominator,
        "primary_metric": PRIMARY_METRIC,
        "primary_proxy_sr": safe_ratio(len(primary_hits), denominator),
        "primary_success_rows": len(primary_hits),
        "primary_spl_proxy_mean": mean([float(row.get("primary_spl_proxy") or 0.0) for row in rows]),
        "primary_first_hit_rank_mean_over_success": mean(primary_ranks_f),
        "primary_first_hit_cost_m_mean_over_success": mean(primary_costs_f),
        "any_viewpoint_xz_0p5_proxy_sr": safe_ratio(len(vp05_hits), denominator),
        "any_viewpoint_xz_1p0_proxy_sr": safe_ratio(len(primary_hits), denominator),
        "any_viewpoint_xz_1p5_proxy_sr": safe_ratio(len(vp15_hits), denominator),
        "goal_xz_1p0_proxy_sr": safe_ratio(len(goal10_hits), denominator),
        "goal_xz_1p5_proxy_sr": safe_ratio(len(goal15_hits), denominator),
        "best_goal_xz_m_mean": mean(best_goal_f),
        "best_any_viewpoint_xz_m_mean": mean(best_vp_f),
        "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
        "path_ready_rows": sum(int(row.get("path_ready_rows") or 0) for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "real_navigation_sr_spl_ready": False,
    }


def build_metric_rows(candidate_goal_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_plan: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        by_plan[(str(row["policy_id"]), str(row["adapter_episode_id"]), str(row["task_context_id"]))].append(row)
    scan_rows = [summarize_policy_plan(rows) for _, rows in sorted(by_plan.items())]

    by_policy_context: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        by_policy_context[(str(row["policy_id"]), str(row["task_context_id"]))].append(row)
        by_policy[str(row["policy_id"])].append(row)

    policy_context_rows = [
        summarize_aggregate(
            rows,
            "aggregate_policy_task_context",
            {
                "policy_id": policy_id,
                "policy_family": rows[0].get("policy_family"),
                "task_context_id": task_context_id,
            },
        )
        for (policy_id, task_context_id), rows in sorted(by_policy_context.items())
    ]
    aggregate_rows = [
        summarize_aggregate(
            rows,
            "aggregate_policy",
            {
                "policy_id": policy_id,
                "policy_family": rows[0].get("policy_family"),
                "task_context_id": "all",
            },
        )
        for policy_id, rows in sorted(by_policy.items())
    ]
    return scan_rows, policy_context_rows, aggregate_rows


def build_failure_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in scan_metric_rows:
        if row.get("primary_hit"):
            continue
        rows.append(
            {
                "version": VERSION,
                "policy_plan_uid": row.get("policy_plan_uid"),
                "policy_id": row.get("policy_id"),
                "policy_family": row.get("policy_family"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "failure_type": "no_h001_candidate_within_any_gt_viewpoint_xz_1p0",
                "best_any_viewpoint_xz_m": row.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": row.get("best_any_viewpoint_xz_rank"),
                "best_goal_xz_m": row.get("best_goal_xz_m"),
                "best_goal_xz_rank": row.get("best_goal_xz_rank"),
                "suspected_cause": "h001_visit_order_candidates_do_not_cover_target_stop_region_or_localize_other_same-category_instances",
                "next_test": "compare policy failures and decide H001 trajectory-execution contract before claiming real SR/SPL",
            }
        )
    return rows


def build_leakage_audit_rows(candidate_goal_rows: list[dict[str, Any]], eval_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_policy = defaultdict(list)
    for row in candidate_goal_rows:
        by_policy[str(row["policy_id"])].append(row)
    for policy_id, policy_rows in sorted(by_policy.items()):
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "candidate_goal_eval_rows": len(policy_rows),
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


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_h001_leakage_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M27 joins H001 visit rows to ObjectNav targets only for evaluation labels.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M27 is not a Habitat policy execution and does not compute final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_true_dynamic_stale_memory_on_hm3d",
            "supported": False,
            "claim_boundary": "M27 still uses an HM3D static-memory proxy as initial memory, not a real dynamic stale-memory event stream.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_deployable_search_policy",
            "supported": False,
            "claim_boundary": "M27 reports goal-evaluation proxy metrics only; deployable policy requires trajectory execution, scale, and navigation/search baselines.",
        },
    ]


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | "
            "{primary_first_hit_rank_mean_over_success} | {any_viewpoint_xz_1p5_proxy_sr} | {goal_xz_1p0_proxy_sr} | {best_any_viewpoint_xz_m_mean} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    context_lines = []
    for row in context_rows:
        context_lines.append(
            "| {policy_id} | {task_context_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} |".format(
                **{key: format_value(row.get(key)) for key in row}
            )
        )
    failure_counts = Counter(str(row["policy_id"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M27 H001 Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M26 status: `{coverage['m26_status']}`.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy-task rows: {coverage['aggregate_policy_task_context_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Task Context Aggregate

| policy_id | task_context_id | primary hits | primary proxy SR | primary proxy SPL |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(context_lines)}

## Claim Boundary

- E008-M27 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- E008-M27 reports `GoalEvalProxySR` / `GoalEvalProxySPL` style diagnostics, not final real navigation `SR` / `SPL`.
- `initial_memory_proxy` is still an `HM3D` static-memory proxy, not true dynamic stale memory.
- Structured `task_context_id` controls H001 memory trust/re-observation budget, but natural-language human intent is not tested here.
"""


def main() -> None:
    m12 = load_m12_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m26_coverage = read_json(M26_ARTIFACT_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    visit_rows = read_jsonl(M26_ARTIFACT_DIR / "h001_candidate_visit_order_rows.jsonl")
    blocked_policy_rows = read_jsonl(M26_ARTIFACT_DIR / "blocked_policy_plan_rows.jsonl")
    if not goal_rows:
        raise SystemExit("missing M03 episode_goal_eval_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M26 h001_candidate_visit_order_rows.jsonl")

    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in oracle_rows}

    candidate_goal_rows = build_candidate_goal_eval_rows(visit_rows, eval_index, oracle_index)
    scan_metric_rows, context_rows, aggregate_rows = build_metric_rows(candidate_goal_rows)
    policy_goal_metric_rows = scan_metric_rows + context_rows + aggregate_rows
    failure_rows = build_failure_rows(scan_metric_rows)
    leakage_audit_rows = build_leakage_audit_rows(candidate_goal_rows, eval_index)
    claim_boundary_rows = build_claim_boundary_rows()

    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in aggregate_rows]
    ready = bool(aggregate_rows) and leakage_pass and not uses_eval_policy
    selected_next = (
        "E008-M28 H001 goal-evaluation comparison and trajectory-execution decision"
        if ready
        else "repair E008-M27 H001 leakage-safe goal-evaluation smoke"
    )
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "h001_goal_eval_smoke_ready_but_navigation_claim_blocked" if ready else "blocked",
            "selected_next_unit": selected_next,
            "reason": "H001 visit-order rows can be evaluated against ObjectNav targets without policy leakage; compare policy failures before trajectory execution."
            if ready
            else "H001 goal-evaluation rows are missing or use blocked eval-only fields.",
            "h001_goal_eval_proxy_ready": ready,
            "h001_navigation_policy_execution_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "launch_long_job_now": False,
        }
    ]

    coverage = {
        "version": VERSION,
        "status": "e008_m27_h001_goal_evaluation_smoke_ready"
        if ready
        else "e008_m27_h001_goal_evaluation_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m26_status": m26_coverage.get("status"),
        "eval_episode_rows": len(goal_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_task_context_rows": len(context_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_goal_metric_rows": len(policy_goal_metric_rows),
        "blocked_policy_plan_rows": len(blocked_policy_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_failure_rows": len(failure_rows),
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "policy_primary_metrics": {
            str(row["policy_id"]): {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
            }
            for row in aggregate_rows
        },
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "h001_goal_eval_proxy_ready": ready,
        "h001_navigation_policy_execution_ready": False,
        "h001_initial_memory_proxy_not_true_dynamic_stale_memory": True,
        "structured_task_context_not_natural_language_intent": True,
        "dynamic_stale_memory_claim_ready_on_hm3d": False,
        "real_navigation_sr_spl_ready": False,
        "real_navigation_sr_spl_smoke_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "h001_candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "h001_policy_goal_metric_rows.jsonl", policy_goal_metric_rows)
        write_jsonl(output_dir / "h001_goal_failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "blocked_policy_plan_rows.jsonl", blocked_policy_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, aggregate_rows, context_rows, failure_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
