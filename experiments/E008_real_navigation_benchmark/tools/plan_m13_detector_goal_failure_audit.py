#!/usr/bin/env python3
"""Audit E008-M12 detector-goal failures and select the next coverage route."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M13_detector_goal_failure_audit_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M13_detector_goal_failure_audit_v0"
VERSION = "e008_m13_detector_goal_failure_audit_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M07_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M07_hm3d_rendered_rgbd_detector_candidate_source_plan_v0"
M09_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0"
M12_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M12_detector_candidate_goal_evaluation_smoke_v0"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH3_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)


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


def valid_vec3(vec: object) -> bool:
    if not isinstance(vec, list) or len(vec) != 3:
        return False
    return all(finite_float(v) is not None for v in vec)


def as_vec3(vec: object) -> list[float] | None:
    if not valid_vec3(vec):
        return None
    return [float(v) for v in vec]  # type: ignore[arg-type]


def dist_xz(a: object, b: object) -> float | None:
    av = as_vec3(a)
    bv = as_vec3(b)
    if av is None or bv is None:
        return None
    return float(math.sqrt((av[0] - bv[0]) ** 2 + (av[2] - bv[2]) ** 2))


def mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def min_or_none(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    return min(valid) if valid else None


def hit(distance: float | None, threshold: float) -> bool:
    return distance is not None and distance <= threshold


def query_label_compatible(object_category: object, label: object) -> bool:
    query = str(object_category or "").lower().replace("-", "_")
    candidate = str(label or "").lower().replace("-", "_")
    if not query or not candidate:
        return False
    aliases = {
        "tv_monitor": {"tv", "television", "monitor", "tv_monitor"},
        "television": {"tv", "television", "monitor", "tv_monitor"},
        "tv": {"tv", "television", "monitor", "tv_monitor"},
    }
    if query in aliases:
        return candidate in aliases[query]
    return query == candidate


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

        viewpoints = []
        if isinstance(selected_goal, dict):
            for viewpoint in selected_goal.get("view_points", []):
                agent_state = viewpoint.get("agent_state", {}) if isinstance(viewpoint, dict) else {}
                position = agent_state.get("position")
                if valid_vec3(position):
                    viewpoints.append([float(v) for v in position])

        staged_scene_key = str(row.get("scene_key", "")).replace("-", "_", 1)
        scan_id = f"hm3dnav_{staged_scene_key}_ep{row.get('source_episode_id')}"
        out[scan_id] = {
            **row,
            "scan_id": scan_id,
            "eval_all_viewpoint_positions": viewpoints,
            "eval_all_viewpoint_count_loaded": len(viewpoints),
            "eval_goals_by_category_loaded": bool(goals),
            "eval_selected_goal_loaded": selected_goal is not None,
        }
    return out


def candidate_distance_summary(rows: list[dict[str, Any]], eval_goal: dict[str, Any], position_key: str) -> dict[str, Any]:
    viewpoints = eval_goal.get("eval_all_viewpoint_positions", [])
    goal_position = eval_goal.get("eval_goal_position")
    distances_any_vp = [min_or_none([dist_xz(row.get(position_key), viewpoint) for viewpoint in viewpoints]) for row in rows]
    distances_goal = [dist_xz(row.get(position_key), goal_position) for row in rows]
    return {
        "candidate_rows": len(rows),
        "best_any_viewpoint_xz_m": min_or_none(distances_any_vp),
        "best_goal_xz_m": min_or_none(distances_goal),
        "any_viewpoint_xz_1p0_hits": sum(1 for distance in distances_any_vp if hit(distance, 1.0)),
        "any_viewpoint_xz_1p5_hits": sum(1 for distance in distances_any_vp if hit(distance, 1.5)),
        "goal_xz_1p0_hits": sum(1 for distance in distances_goal if hit(distance, 1.0)),
        "goal_xz_1p5_hits": sum(1 for distance in distances_goal if hit(distance, 1.5)),
    }


def classify_episode_failure(
    failed_all_policies: bool,
    pre_cap_summary: dict[str, Any],
    final_summary: dict[str, Any],
    m12_summary: dict[str, Any],
) -> tuple[str, str]:
    if not failed_all_policies:
        return "not_primary_failure", "eligible_for_execution_smoke_after_scale_check"

    pre_best = finite_float(pre_cap_summary.get("best_any_viewpoint_xz_m"))
    pre_hits_15 = int(pre_cap_summary.get("any_viewpoint_xz_1p5_hits") or 0)
    final_hits_15 = int(final_summary.get("any_viewpoint_xz_1p5_hits") or 0)
    m12_best = finite_float(m12_summary.get("best_any_viewpoint_xz_m"))

    if pre_hits_15 == 0 and pre_best is not None and pre_best > 2.5:
        return "target_region_missing_in_precap_detector_pool", "expand_non_oracle_observation_coverage"
    if pre_hits_15 == 0 and pre_best is not None and pre_best <= 2.0:
        return "near_miss_localization_threshold", "audit_localization_snap_threshold_before_execution"
    if pre_hits_15 > 0 and final_hits_15 == 0:
        return "post_cap_or_snap_suppression", "ranking_or_cap_repair_before_coverage_expansion"
    if m12_best is not None and m12_best > 2.5:
        return "snapped_candidate_far_from_target_stop_region", "expand_non_oracle_observation_coverage"
    return "other_candidate_goal_gap", "inspect_candidate_geometry_and_render_coverage"


def build_episode_rows(
    eval_index: dict[str, dict[str, Any]],
    render_rows: list[dict[str, Any]],
    pre_cap_rows: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
    policy_goal_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    render_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in render_rows:
        render_by_scan[str(row.get("scan_id"))].append(row)

    pre_cap_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pre_cap_rows:
        pre_cap_by_scan[str(row.get("scan_id"))].append(row)

    final_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in final_rows:
        final_by_scan[str(row.get("scan_id"))].append(row)

    policy_scan_rows = [
        row
        for row in policy_goal_rows
        if row.get("metric_scope") == "scan_policy" and row.get("primary_metric") == "any_viewpoint_xz_1p0"
    ]
    policy_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policy_scan_rows:
        policy_by_scan[str(row.get("scan_id"))].append(row)

    failure_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in failure_rows:
        failure_by_scan[str(row.get("scan_id"))].append(row)

    episode_rows = []
    prefinal_rows = []
    policy_failure_audit_rows = []

    for scan_id, eval_goal in sorted(eval_index.items()):
        object_category = eval_goal.get("object_category")
        pre_compatible = [
            row for row in pre_cap_by_scan.get(scan_id, []) if query_label_compatible(object_category, row.get("label_canonical"))
        ]
        final_compatible = [
            row for row in final_by_scan.get(scan_id, []) if query_label_compatible(object_category, row.get("label_canonical"))
        ]
        pre_summary = candidate_distance_summary(pre_compatible, eval_goal, "centroid_world_m")
        final_summary = candidate_distance_summary(final_compatible, eval_goal, "centroid_world_m")
        scan_policy = policy_by_scan.get(scan_id, [])
        m12_best_any = min_or_none([finite_float(row.get("best_any_viewpoint_xz_m")) for row in scan_policy])
        m12_best_goal = min_or_none([finite_float(row.get("best_goal_xz_m")) for row in scan_policy])
        m12_summary = {
            "best_any_viewpoint_xz_m": m12_best_any,
            "best_goal_xz_m": m12_best_goal,
            "primary_success_policy_count": sum(1 for row in scan_policy if row.get("primary_hit")),
            "goal_xz_1p0_success_policy_count": sum(1 for row in scan_policy if row.get("goal_xz_1p0_hit")),
            "policy_rows": len(scan_policy),
        }
        failed_all_policies = bool(scan_policy) and int(m12_summary["primary_success_policy_count"]) == 0
        failure_class, next_action = classify_episode_failure(failed_all_policies, pre_summary, final_summary, m12_summary)

        yaw_offsets = sorted(
            {
                int(row["yaw_offset_deg"])
                for row in render_by_scan.get(scan_id, [])
                if finite_float(row.get("yaw_offset_deg")) is not None
            }
        )
        row = {
            "version": VERSION,
            "scan_id": scan_id,
            "adapter_episode_id": eval_goal.get("adapter_episode_id"),
            "scene_key": eval_goal.get("scene_key"),
            "object_category": object_category,
            "render_frame_count": len(render_by_scan.get(scan_id, [])),
            "render_yaw_offsets_deg": yaw_offsets,
            "eval_all_viewpoint_count_loaded": eval_goal.get("eval_all_viewpoint_count_loaded"),
            "pre_cap_candidate_rows": pre_summary["candidate_rows"],
            "final_candidate_rows": final_summary["candidate_rows"],
            "pre_cap_best_any_viewpoint_xz_m": pre_summary["best_any_viewpoint_xz_m"],
            "pre_cap_best_goal_xz_m": pre_summary["best_goal_xz_m"],
            "pre_cap_any_viewpoint_xz_1p0_hits": pre_summary["any_viewpoint_xz_1p0_hits"],
            "pre_cap_any_viewpoint_xz_1p5_hits": pre_summary["any_viewpoint_xz_1p5_hits"],
            "pre_cap_goal_xz_1p0_hits": pre_summary["goal_xz_1p0_hits"],
            "final_centroid_best_any_viewpoint_xz_m": final_summary["best_any_viewpoint_xz_m"],
            "final_centroid_best_goal_xz_m": final_summary["best_goal_xz_m"],
            "final_centroid_any_viewpoint_xz_1p0_hits": final_summary["any_viewpoint_xz_1p0_hits"],
            "final_centroid_any_viewpoint_xz_1p5_hits": final_summary["any_viewpoint_xz_1p5_hits"],
            "m12_snapped_best_any_viewpoint_xz_m": m12_summary["best_any_viewpoint_xz_m"],
            "m12_snapped_best_goal_xz_m": m12_summary["best_goal_xz_m"],
            "m12_primary_success_policy_count": m12_summary["primary_success_policy_count"],
            "m12_goal_xz_1p0_success_policy_count": m12_summary["goal_xz_1p0_success_policy_count"],
            "m12_policy_rows": m12_summary["policy_rows"],
            "failed_all_policies": failed_all_policies,
            "primary_failure_class": failure_class,
            "recommended_next_action": next_action,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_audit": True,
            "claim_boundary": "audit_only_not_real_navigation_sr_spl",
        }
        episode_rows.append(row)
        prefinal_rows.append(
            {
                "version": VERSION,
                "scan_id": scan_id,
                "adapter_episode_id": eval_goal.get("adapter_episode_id"),
                "object_category": object_category,
                "pre_cap_candidate_rows": pre_summary["candidate_rows"],
                "final_candidate_rows": final_summary["candidate_rows"],
                "pre_cap_best_any_viewpoint_xz_m": pre_summary["best_any_viewpoint_xz_m"],
                "final_centroid_best_any_viewpoint_xz_m": final_summary["best_any_viewpoint_xz_m"],
                "m12_snapped_best_any_viewpoint_xz_m": m12_summary["best_any_viewpoint_xz_m"],
                "pre_cap_any_viewpoint_xz_1p0_hits": pre_summary["any_viewpoint_xz_1p0_hits"],
                "pre_cap_any_viewpoint_xz_1p5_hits": pre_summary["any_viewpoint_xz_1p5_hits"],
                "final_centroid_any_viewpoint_xz_1p0_hits": final_summary["any_viewpoint_xz_1p0_hits"],
                "final_centroid_any_viewpoint_xz_1p5_hits": final_summary["any_viewpoint_xz_1p5_hits"],
                "primary_failure_class": failure_class,
            }
        )

        for failure in failure_by_scan.get(scan_id, []):
            policy_failure_audit_rows.append(
                {
                    "version": VERSION,
                    "scan_id": scan_id,
                    "adapter_episode_id": eval_goal.get("adapter_episode_id"),
                    "policy_id": failure.get("policy_id"),
                    "object_category": object_category,
                    "m12_failure_type": failure.get("failure_type"),
                    "m12_best_any_viewpoint_xz_m": failure.get("best_any_viewpoint_xz_m"),
                    "m12_best_goal_xz_m": failure.get("best_goal_xz_m"),
                    "primary_failure_class": failure_class,
                    "recommended_next_action": next_action,
                }
            )

    return episode_rows, prefinal_rows, policy_failure_audit_rows


def build_expansion_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "bounded_start_neighborhood_multiview_v0",
            "route_status": "selected_next_plan",
            "purpose": "Increase non-oracle observation coverage before simulator SR/SPL execution.",
            "allowed_inputs": [
                "scene_file",
                "navmesh_file",
                "episode_start_position",
                "episode_start_rotation",
                "object_category",
                "current_detector_candidate_rows",
                "reachable_navmesh_samples",
                "fixed_render_budget",
            ],
            "blocked_inputs": [
                "eval_goal_position",
                "eval_viewpoints",
                "closest_goal_object_id",
                "success_label",
                "candidate_to_goal_distance",
            ],
            "verification_command": "rerun M08-M12 equivalent checks on expanded observations and repeat leakage audit",
            "paper_claim_boundary": "coverage_expansion_plan_only_not_final_rgbd_robustness_or_real_navigation_sr_spl",
        }
    ]


def build_route_decision_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "observation_coverage_expansion_before_simulator_execution",
            "selected_next_unit": "E008-M14 non-oracle observation-coverage expansion plan",
            "reason": "All primary M12 failures are shared across policies, and pre-cap detector candidates already miss the target stop region for most failed episodes; ranking repair is therefore not the first bottleneck.",
            "failed_all_policies_episode_rows": coverage["failed_all_policies_episode_rows"],
            "precap_target_region_missing_episode_rows": coverage["precap_target_region_missing_episode_rows"],
            "near_miss_localization_episode_rows": coverage["near_miss_localization_episode_rows"],
            "post_cap_or_snap_suppression_episode_rows": coverage["post_cap_or_snap_suppression_episode_rows"],
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "launch_long_job_now": False,
        }
    ]


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def build_report(coverage: dict[str, Any], episode_rows: list[dict[str, Any]], route_decision_rows: list[dict[str, Any]]) -> str:
    table_lines = []
    for row in episode_rows:
        table_lines.append(
            "| {scan_id} | {object_category} | {m12_primary_success_policy_count}/{m12_policy_rows} | "
            "{pre_cap_candidate_rows} | {pre_cap_best_any_viewpoint_xz_m} | {final_candidate_rows} | "
            "{m12_snapped_best_any_viewpoint_xz_m} | `{primary_failure_class}` | `{recommended_next_action}` |".format(
                **{key: format_value(value) for key, value in row.items()}
            )
        )
    class_counts = Counter(str(row["primary_failure_class"]) for row in episode_rows)
    class_line = ", ".join(f"`{key}` {value}" for key, value in sorted(class_counts.items()))
    return f"""# E008-M13 Detector-Goal Failure Audit

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M12 status: `{coverage['m12_status']}`.
- Episode rows audited: {coverage['episode_rows']}.
- M12 policy failure rows audited: {coverage['policy_failure_rows']}.
- Episodes failing all policies under `any_viewpoint_xz_1p0`: {coverage['failed_all_policies_episode_rows']}.
- Failure classes: {class_line}.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Selected next unit: `{coverage['selected_next_unit']}`.

## Episode Audit

| scan_id | category | M12 primary policies hit | pre-cap rows | pre-cap best any-vp XZ m | final rows | M12 snapped best any-vp XZ m | class | next action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(table_lines)}

## Claim Boundary

- This artifact is a detector-goal failure audit, not executed navigation.
- It uses `ObjectNav` goal/viewpoint fields only as audit labels, not policy inputs.
- It does not claim real navigation `SR` / `SPL`.
- It does not claim final real RGB-D/open-vocabulary robustness.

## Agent Inference

The three primary failures are shared by all four visit-order policies. Two failed episodes are clear target-region misses already in the pre-cap detector pool, and one is a near-miss around the localization/evaluation threshold. The next defensible step is non-oracle observation coverage expansion before simulator execution, not more visit-order ranking.

## Route Decision

- Decision: `{route_decision_rows[0]['decision']}`.
- Reason: {route_decision_rows[0]['reason']}
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m12_coverage = read_json(M12_ARTIFACT_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_ARTIFACT_DIR / "episode_goal_eval_rows.jsonl")
    render_rows = read_jsonl(M07_ARTIFACT_DIR / "render_plan_rows.jsonl")
    pre_cap_rows = read_jsonl(M09_ARTIFACT_DIR / "container_output" / "pre_cap_candidate_pool.jsonl")
    final_rows = read_jsonl(M09_ARTIFACT_DIR / "container_output" / "real_proposals.jsonl")
    policy_goal_rows = read_jsonl(M12_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")
    failure_rows = read_jsonl(M12_ARTIFACT_DIR / "failure_rows.jsonl")

    required = {
        "M03 episode_goal_eval_rows": goal_rows,
        "M07 render_plan_rows": render_rows,
        "M09 pre_cap_candidate_pool": pre_cap_rows,
        "M09 real_proposals": final_rows,
        "M12 policy_goal_metric_rows": policy_goal_rows,
        "M12 failure_rows": failure_rows,
    }
    missing = [name for name, rows in required.items() if not rows]
    if missing:
        raise SystemExit(f"missing required rows: {', '.join(missing)}")

    eval_index = build_eval_goal_index(goal_rows)
    episode_rows, prefinal_rows, policy_failure_audit_rows = build_episode_rows(
        eval_index,
        render_rows,
        pre_cap_rows,
        final_rows,
        policy_goal_rows,
        failure_rows,
    )

    class_counts = Counter(str(row["primary_failure_class"]) for row in episode_rows)
    failed_rows = [row for row in episode_rows if row.get("failed_all_policies")]
    coverage = {
        "version": VERSION,
        "status": "e008_m13_detector_goal_failure_audit_ready_observation_expansion_selected",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m12_status": m12_coverage.get("status"),
        "episode_rows": len(episode_rows),
        "policy_failure_rows": len(policy_failure_audit_rows),
        "m12_policy_failure_rows_input": len(failure_rows),
        "failed_all_policies_episode_rows": len(failed_rows),
        "precap_target_region_missing_episode_rows": class_counts.get("target_region_missing_in_precap_detector_pool", 0),
        "near_miss_localization_episode_rows": class_counts.get("near_miss_localization_threshold", 0),
        "post_cap_or_snap_suppression_episode_rows": class_counts.get("post_cap_or_snap_suppression", 0),
        "not_primary_failure_episode_rows": class_counts.get("not_primary_failure", 0),
        "mean_failed_pre_cap_best_any_viewpoint_xz_m": mean(
            [
                float(row["pre_cap_best_any_viewpoint_xz_m"])
                for row in failed_rows
                if finite_float(row.get("pre_cap_best_any_viewpoint_xz_m")) is not None
            ]
        ),
        "mean_failed_m12_snapped_best_any_viewpoint_xz_m": mean(
            [
                float(row["m12_snapped_best_any_viewpoint_xz_m"])
                for row in failed_rows
                if finite_float(row.get("m12_snapped_best_any_viewpoint_xz_m")) is not None
            ]
        ),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_audit": True,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "selected_next_unit": "E008-M14 non-oracle observation-coverage expansion plan",
        "launch_long_job_now": False,
    }
    expansion_contract_rows = build_expansion_contract_rows()
    route_decision_rows = build_route_decision_rows(coverage)

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "episode_failure_audit_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "precap_final_coverage_rows.jsonl", prefinal_rows)
        write_jsonl(output_dir / "policy_failure_audit_rows.jsonl", policy_failure_audit_rows)
        write_jsonl(output_dir / "coverage_expansion_contract_rows.jsonl", expansion_contract_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, episode_rows, route_decision_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
