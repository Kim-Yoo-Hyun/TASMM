#!/usr/bin/env python3
"""Evaluate E008-M11 detector visit-order rows against ObjectNav targets as eval-only labels."""

from __future__ import annotations

import gzip
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M12_detector_candidate_goal_evaluation_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M12_detector_candidate_goal_evaluation_smoke_v0"
VERSION = "e008_m12_detector_candidate_goal_evaluation_smoke_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M10_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M10_detector_candidate_navmesh_validation_v0"
M11_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M11_detector_candidate_visit_order_path_smoke_v0"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH2_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)

PRIMARY_METRIC = "any_viewpoint_xz_1p0"


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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def dist3(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def dist_xz(a: list[float] | None, b: list[float] | None) -> float | None:
    if not valid_vec3(a) or not valid_vec3(b):
        return None
    return float(math.sqrt((float(a[0]) - float(b[0])) ** 2 + (float(a[2]) - float(b[2])) ** 2))


def valid_vec3(vec: object) -> bool:
    if not isinstance(vec, list) or len(vec) != 3:
        return False
    return all(finite_float(v) is not None for v in vec)


def load_goal_index() -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for content_file in sorted(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        goals_by_category = payload.get("goals_by_category", {})
        for key, goals in goals_by_category.items():
            if "_" not in key or not isinstance(goals, list):
                continue
            scene_file, category = key.split("_", 1)
            index[(scene_file, category)] = goals
    return index


def build_eval_goal_index(goal_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    goal_index = load_goal_index()
    out: dict[str, dict[str, Any]] = {}
    for row in goal_rows:
        scene_file = Path(str(row.get("scene_id_raw", ""))).name
        category = str(row.get("object_category", ""))
        goals = goal_index.get((scene_file, category), [])
        selected_goal = None
        closest_id = row.get("eval_goal_object_id")
        for goal in goals:
            if goal.get("object_id") == closest_id:
                selected_goal = goal
                break
        if selected_goal is None and goals:
            selected_goal = goals[0]
        all_viewpoint_positions = []
        if isinstance(selected_goal, dict):
            for viewpoint in selected_goal.get("view_points", []):
                agent_state = viewpoint.get("agent_state", {}) if isinstance(viewpoint, dict) else {}
                position = agent_state.get("position")
                if valid_vec3(position):
                    all_viewpoint_positions.append([float(v) for v in position])
        out[str(row["adapter_episode_id"])] = {
            **row,
            "eval_all_viewpoint_positions": all_viewpoint_positions,
            "eval_all_viewpoint_count_loaded": len(all_viewpoint_positions),
            "eval_goals_by_category_loaded": bool(goals),
            "eval_selected_goal_loaded": selected_goal is not None,
        }
    return out


def nearest_viewpoint_distances(candidate_pos: list[float] | None, viewpoints: list[list[float]]) -> tuple[float | None, float | None]:
    if not valid_vec3(candidate_pos) or not viewpoints:
        return None, None
    xz = [dist_xz(candidate_pos, viewpoint) for viewpoint in viewpoints]
    xyz = [dist3(candidate_pos, viewpoint) for viewpoint in viewpoints]
    return min(v for v in xz if v is not None), min(v for v in xyz if v is not None)


def build_candidate_goal_eval_rows(
    visit_rows: list[dict[str, Any]],
    candidate_index: dict[str, dict[str, Any]],
    eval_index: dict[str, dict[str, Any]],
    oracle_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out = []
    for row in visit_rows:
        candidate = candidate_index.get(str(row.get("proposal_uid")), {})
        eval_goal = eval_index.get(str(row.get("adapter_episode_id")), {})
        oracle = oracle_index.get(str(row.get("adapter_episode_id")), {})
        candidate_pos = candidate.get("snapped_position_m") if row.get("path_ready") else None
        goal_pos = eval_goal.get("eval_goal_position")
        first_viewpoint = eval_goal.get("eval_first_viewpoint_position")
        all_viewpoints = eval_goal.get("eval_all_viewpoint_positions", [])
        any_viewpoint_xz, any_viewpoint_3d = nearest_viewpoint_distances(candidate_pos, all_viewpoints)
        goal_xz = dist_xz(candidate_pos, goal_pos)
        goal_3d = dist3(candidate_pos, goal_pos)
        first_viewpoint_xz = dist_xz(candidate_pos, first_viewpoint)
        first_viewpoint_3d = dist3(candidate_pos, first_viewpoint)
        primary_hit = hit(any_viewpoint_xz, 1.0)
        out.append(
            {
                "version": VERSION,
                "policy_id": row.get("policy_id"),
                "scan_id": row.get("scan_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "visit_rank": row.get("visit_rank"),
                "proposal_uid": row.get("proposal_uid"),
                "label_canonical": row.get("label_canonical"),
                "path_ready": bool(row.get("path_ready")),
                "blocked_candidate_for_path_policy": bool(row.get("blocked_candidate_for_path_policy")),
                "source_to_candidate_path_cost_m": row.get("source_to_candidate_path_cost_m"),
                "cumulative_known_path_cost_m": row.get("cumulative_known_path_cost_m"),
                "candidate_snapped_position_m": candidate_pos,
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
            }
        )
    return out


def hit(distance: float | None, threshold: float) -> bool:
    return distance is not None and distance <= threshold


def first_hit_row(rows: list[dict[str, Any]], hit_key: str) -> dict[str, Any] | None:
    for row in sorted(rows, key=lambda r: int(r.get("visit_rank") or 10**9)):
        if row.get(hit_key):
            return row
    return None


def best_distance(rows: list[dict[str, Any]], distance_key: str) -> tuple[float | None, int | None]:
    valid = [(finite_float(row.get(distance_key)), int(row.get("visit_rank") or 10**9)) for row in rows]
    valid = [(distance, rank) for distance, rank in valid if distance is not None]
    if not valid:
        return None, None
    distance, rank = min(valid, key=lambda item: item[0])
    return distance, rank


def oracle_path(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    for key in ("oracle_viewpoint_path_m", "episode_eval_geodesic_distance_m", "oracle_goal_snapped_path_m"):
        value = finite_float(row.get(key))
        if value is not None:
            return value
    return None


def spl_proxy(hit_row: dict[str, Any] | None) -> float:
    if not hit_row:
        return 0.0
    oracle = oracle_path(hit_row)
    cost = finite_float(hit_row.get("cumulative_known_path_cost_m"))
    if oracle is None or cost is None or cost <= 0:
        return 0.0
    return float(oracle / max(oracle, cost))


def summarize_policy_scan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("empty policy scan rows")
    first_primary = first_hit_row(rows, "hit_any_viewpoint_xz_1p0")
    first_vp_05 = first_hit_row(rows, "hit_any_viewpoint_xz_0p5")
    first_vp_15 = first_hit_row(rows, "hit_any_viewpoint_xz_1p5")
    first_goal_10 = first_hit_row(rows, "hit_goal_xz_1p0")
    first_goal_15 = first_hit_row(rows, "hit_goal_xz_1p5")
    best_goal_xz, best_goal_rank = best_distance(rows, "candidate_to_eval_goal_xz_m")
    best_vp_xz, best_vp_rank = best_distance(rows, "candidate_to_nearest_eval_viewpoint_xz_m")
    return {
        "version": VERSION,
        "metric_scope": "scan_policy",
        "policy_id": rows[0]["policy_id"],
        "scan_id": rows[0]["scan_id"],
        "adapter_episode_id": rows[0]["adapter_episode_id"],
        "scene_key": rows[0]["scene_key"],
        "object_category": rows[0]["object_category"],
        "candidate_rows": len(rows),
        "path_ready_rows": sum(1 for row in rows if row.get("path_ready")),
        "blocked_rows": sum(1 for row in rows if row.get("blocked_candidate_for_path_policy")),
        "primary_metric": PRIMARY_METRIC,
        "primary_hit": first_primary is not None,
        "primary_first_hit_rank": first_primary.get("visit_rank") if first_primary else None,
        "primary_first_hit_cost_m": first_primary.get("cumulative_known_path_cost_m") if first_primary else None,
        "primary_spl_proxy": spl_proxy(first_primary),
        "any_viewpoint_xz_0p5_hit": first_vp_05 is not None,
        "any_viewpoint_xz_0p5_first_rank": first_vp_05.get("visit_rank") if first_vp_05 else None,
        "any_viewpoint_xz_1p0_hit": first_primary is not None,
        "any_viewpoint_xz_1p0_first_rank": first_primary.get("visit_rank") if first_primary else None,
        "any_viewpoint_xz_1p5_hit": first_vp_15 is not None,
        "any_viewpoint_xz_1p5_first_rank": first_vp_15.get("visit_rank") if first_vp_15 else None,
        "goal_xz_1p0_hit": first_goal_10 is not None,
        "goal_xz_1p0_first_rank": first_goal_10.get("visit_rank") if first_goal_10 else None,
        "goal_xz_1p5_hit": first_goal_15 is not None,
        "goal_xz_1p5_first_rank": first_goal_15.get("visit_rank") if first_goal_15 else None,
        "best_goal_xz_m": best_goal_xz,
        "best_goal_xz_rank": best_goal_rank,
        "best_any_viewpoint_xz_m": best_vp_xz,
        "best_any_viewpoint_xz_rank": best_vp_rank,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
    }


def summarize_policy_aggregate(policy_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary_hits = [row for row in rows if row.get("primary_hit")]
    vp05_hits = [row for row in rows if row.get("any_viewpoint_xz_0p5_hit")]
    vp15_hits = [row for row in rows if row.get("any_viewpoint_xz_1p5_hit")]
    goal10_hits = [row for row in rows if row.get("goal_xz_1p0_hit")]
    goal15_hits = [row for row in rows if row.get("goal_xz_1p5_hit")]
    primary_ranks = [finite_float(row.get("primary_first_hit_rank")) for row in primary_hits if row.get("primary_first_hit_rank") is not None]
    primary_costs = [finite_float(row.get("primary_first_hit_cost_m")) for row in primary_hits if row.get("primary_first_hit_cost_m") is not None]
    best_goal = [finite_float(row.get("best_goal_xz_m")) for row in rows if row.get("best_goal_xz_m") is not None]
    best_vp = [finite_float(row.get("best_any_viewpoint_xz_m")) for row in rows if row.get("best_any_viewpoint_xz_m") is not None]
    primary_ranks_f = [v for v in primary_ranks if v is not None]
    primary_costs_f = [v for v in primary_costs if v is not None]
    best_goal_f = [v for v in best_goal if v is not None]
    best_vp_f = [v for v in best_vp if v is not None]
    denominator = len(rows)
    return {
        "version": VERSION,
        "metric_scope": "policy_aggregate",
        "policy_id": policy_id,
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
        "blocked_rows": sum(int(row.get("blocked_rows") or 0) for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
    }


def safe_ratio(num: int, den: int) -> float | None:
    return float(num / den) if den else None


def build_metric_rows(candidate_goal_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_policy_scan: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_goal_rows:
        by_policy_scan[(str(row["policy_id"]), str(row["scan_id"]))].append(row)
    scan_rows = [summarize_policy_scan(rows) for _, rows in sorted(by_policy_scan.items())]
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_rows:
        by_policy[str(row["policy_id"])].append(row)
    aggregate_rows = [summarize_policy_aggregate(policy_id, rows) for policy_id, rows in sorted(by_policy.items())]
    return scan_rows, aggregate_rows


def build_failure_rows(scan_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in scan_metric_rows:
        if row.get("primary_hit"):
            continue
        rows.append(
            {
                "version": VERSION,
                "policy_id": row["policy_id"],
                "scan_id": row["scan_id"],
                "adapter_episode_id": row["adapter_episode_id"],
                "object_category": row["object_category"],
                "failure_type": "no_candidate_within_any_gt_viewpoint_xz_1p0",
                "best_any_viewpoint_xz_m": row.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": row.get("best_any_viewpoint_xz_rank"),
                "best_goal_xz_m": row.get("best_goal_xz_m"),
                "best_goal_xz_rank": row.get("best_goal_xz_rank"),
                "suspected_cause": "rendered_start_pose_detector_candidates_do_not_cover_target_stop_region_or_localize_other_same-category_instances",
                "next_test": "inspect target visibility/candidate rows and decide render-coverage expansion before simulator SR/SPL execution",
            }
        )
    return rows


def build_leakage_audit_rows(candidate_goal_rows: list[dict[str, Any]], eval_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    policy_counts = Counter(str(row["policy_id"]) for row in candidate_goal_rows)
    rows = []
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


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(coverage: dict[str, Any], aggregate_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]]) -> str:
    aggregate_lines = []
    for row in aggregate_rows:
        aggregate_lines.append(
            "| {policy_id} | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | "
            "{primary_first_hit_rank_mean_over_success} | {any_viewpoint_xz_1p5_proxy_sr} | {goal_xz_1p0_proxy_sr} | {best_any_viewpoint_xz_m_mean} |".format(
                **{k: format_value(row.get(k)) for k in row}
            )
        )
    failure_counts = Counter(str(row["policy_id"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M12 Detector Candidate Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M11 status: `{coverage['m11_status']}`.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- This artifact uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- This artifact is a leakage-safe target-evaluation smoke, not executed navigation.
- It reports `GoalEvalProxySR` / `GoalEvalProxySPL` style diagnostics, not real navigation `SR` / `SPL`.
- The current 6-episode subset is too small for final real RGB-D/open-vocabulary robustness or deployable search-policy claims.

## Agent Inference

The detector candidate route can be evaluated against `ObjectNav` targets without policy leakage, but the primary proxy success is still limited. The next step should inspect failures and decide whether to expand observation coverage/candidate generation before simulator trajectory execution.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m11_coverage = read_json(M11_ARTIFACT_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl")
    nav_rows = read_jsonl(M10_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    visit_rows = read_jsonl(M11_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")

    if not goal_rows:
        raise SystemExit("missing M03 episode_goal_eval_rows.jsonl")
    if not nav_rows:
        raise SystemExit("missing M10 candidate_navmesh_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M11 candidate_visit_order_rows.jsonl")

    eval_index = build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in oracle_rows}
    candidate_index = {str(row["proposal_uid"]): row for row in nav_rows}

    candidate_goal_rows = build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = build_metric_rows(candidate_goal_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    failure_rows = build_failure_rows(scan_metric_rows)
    leakage_audit_rows = build_leakage_audit_rows(candidate_goal_rows, eval_index)

    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "goal_eval_smoke_ready_but_navigation_claim_blocked",
            "selected_next_unit": "E008-M13 detector-goal failure audit and observation-coverage expansion decision",
            "reason": "M12 can evaluate visit-order rows against ObjectNav target labels without policy leakage, but proxy success is limited and should be diagnosed before simulator SR/SPL execution.",
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "launch_long_job_now": False,
        }
    ]

    primary_success = {
        row["policy_id"]: row
        for row in aggregate_rows
    }
    coverage = {
        "version": VERSION,
        "status": "e008_m12_detector_candidate_goal_evaluation_smoke_ready_with_limited_proxy_success",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m11_status": m11_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "eval_episode_rows": len(goal_rows),
        "candidate_navmesh_rows": len(nav_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_metric_rows": len(policy_metric_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_failure_rows": len(failure_rows),
        "policy_primary_metrics": {
            policy_id: {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
            }
            for policy_id, row in primary_success.items()
        },
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_audit_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, aggregate_rows, failure_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
