#!/usr/bin/env python3
"""Evaluate E008-M69 full-val-mini detector visit-order rows against ObjectNav targets."""

from __future__ import annotations

import gzip
import importlib.util
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
M64_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M68_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M69_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M12_TOOL = EXP_ROOT / "tools" / "run_m12_detector_candidate_goal_evaluation_smoke.py"
VERSION = "e008_m70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    return str(value)


def load_objectnav_payloads() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payloads[path.name] = json.load(handle)
    return payloads


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(isinstance(value, (int, float)) for value in vec)


def build_full_val_mini_eval_goal_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads = load_objectnav_payloads()
    rows: list[dict[str, Any]] = []
    for row in episode_rows:
        content_file = str(row.get("content_file"))
        source_episode_id = str(row.get("source_episode_id"))
        payload = payloads.get(content_file)
        if not payload:
            continue
        episode = None
        for candidate in payload.get("episodes", []):
            if str(candidate.get("episode_id")) == source_episode_id:
                episode = candidate
                break
        if episode is None:
            continue
        scene_file = Path(str(episode.get("scene_id", ""))).name
        object_category = str(episode.get("object_category"))
        goal_key = f"{scene_file}_{object_category}"
        goals = payload.get("goals_by_category", {}).get(goal_key, [])
        closest_id = episode.get("info", {}).get("closest_goal_object_id")
        selected_goal = None
        for goal in goals:
            if goal.get("object_id") == closest_id:
                selected_goal = goal
                break
        if selected_goal is None and goals:
            selected_goal = goals[0]
        first_viewpoint_position = None
        first_viewpoint_rotation = None
        if isinstance(selected_goal, dict):
            for viewpoint in selected_goal.get("view_points", []):
                agent_state = viewpoint.get("agent_state", {}) if isinstance(viewpoint, dict) else {}
                position = agent_state.get("position")
                if valid_vec3(position):
                    first_viewpoint_position = [float(value) for value in position]
                    rotation = agent_state.get("rotation")
                    first_viewpoint_rotation = rotation if isinstance(rotation, list) else None
                    break
        rows.append(
            {
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scene_key": row.get("scene_key"),
                "scene_id_raw": episode.get("scene_id") or row.get("scene_id_raw"),
                "source_episode_id": source_episode_id,
                "object_category": object_category,
                "start_position": episode.get("start_position") or row.get("start_position"),
                "start_rotation": episode.get("start_rotation") or row.get("start_rotation"),
                "eval_goal_fields_ready": selected_goal is not None,
                "eval_goal_object_id": closest_id,
                "eval_goal_object_name": selected_goal.get("object_name") if isinstance(selected_goal, dict) else None,
                "eval_goal_position": selected_goal.get("position") if isinstance(selected_goal, dict) else None,
                "eval_first_viewpoint_position": first_viewpoint_position,
                "eval_first_viewpoint_rotation": first_viewpoint_rotation,
                "eval_viewpoint_count": len(selected_goal.get("view_points", [])) if isinstance(selected_goal, dict) else 0,
                "eval_euclidean_distance": episode.get("info", {}).get("euclidean_distance"),
                "eval_geodesic_distance": episode.get("info", {}).get("geodesic_distance"),
                "policy_input_allowed": False,
                "reason": "ObjectNav goal position, object id, view points, and shortest-path distances are evaluation-only fields.",
            }
        )
    return rows


def build_episode_task_goal_metric_rows(
    scan_metric_rows: list[dict[str, Any]],
    episode_task_policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metric_by_policy_scan = {
        (str(row.get("policy_id")), str(row.get("scan_id"))): row
        for row in scan_metric_rows
    }
    rows: list[dict[str, Any]] = []
    for task in episode_task_policy_rows:
        metric = metric_by_policy_scan.get((str(task.get("policy_id")), str(task.get("scan_id"))))
        if not metric:
            continue
        rows.append(
            {
                "version": VERSION,
                "metric_scope": "episode_task_policy_goal_eval",
                "policy_id": task.get("policy_id"),
                "candidate_scope": task.get("candidate_scope"),
                "scan_id": task.get("scan_id"),
                "adapter_episode_id": task.get("adapter_episode_id"),
                "scene_key": task.get("scene_key"),
                "object_category": task.get("object_category"),
                "split_id": task.get("split_id"),
                "scan_task_context_uid": task.get("scan_task_context_uid"),
                "task_context_id": task.get("task_context_id"),
                "source_ready": task.get("source_ready"),
                "source_gap": task.get("source_gap"),
                "candidate_rows": metric.get("candidate_rows"),
                "path_ready_rows": metric.get("path_ready_rows"),
                "blocked_rows": metric.get("blocked_rows"),
                "primary_metric": metric.get("primary_metric"),
                "primary_hit": metric.get("primary_hit"),
                "primary_first_hit_rank": metric.get("primary_first_hit_rank"),
                "primary_first_hit_cost_m": metric.get("primary_first_hit_cost_m"),
                "primary_spl_proxy": metric.get("primary_spl_proxy"),
                "any_viewpoint_xz_1p5_hit": metric.get("any_viewpoint_xz_1p5_hit"),
                "goal_xz_1p0_hit": metric.get("goal_xz_1p0_hit"),
                "best_any_viewpoint_xz_m": metric.get("best_any_viewpoint_xz_m"),
                "best_any_viewpoint_xz_rank": metric.get("best_any_viewpoint_xz_rank"),
                "best_goal_xz_m": metric.get("best_goal_xz_m"),
                "best_goal_xz_rank": metric.get("best_goal_xz_rank"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": metric.get(
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy"
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "real_navigation_sr_spl_ready": False,
                "claim_boundary": "M70 repeats detector goal-evaluation metrics over structured task contexts for denominator accounting only; detector order itself is task-agnostic.",
            }
        )
    return rows


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "full_val_mini_goal_eval_smoke_ready_but_navigation_claim_blocked" if ready else "blocked",
            "selected_next_unit": "E008-M71 full-val-mini detector-goal failure comparison and trajectory-execution decision"
            if ready
            else "repair E008-M70 leakage-safe goal-evaluation smoke",
            "reason": "Full-val-mini visit-order rows can be evaluated against ObjectNav targets without policy leakage; compare policy failures before trajectory execution."
            if ready
            else "Full-val-mini goal-evaluation rows are missing or use blocked eval-only fields.",
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_full_val_mini_leakage_safe_goal_eval_proxy",
            "supported": True,
            "claim_boundary": "M70 joins detector visit rows to ObjectNav targets only as evaluation labels.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M70 is not a Habitat policy execution and does not compute final real navigation SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_detector_target_recall",
            "supported": False,
            "claim_boundary": "M70 scores candidate proximity to ObjectNav goal viewpoints; it does not solve the M67 matching-target-row gap.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "Detector policies in M70 are task-agnostic; task context rows are denominator accounting only.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
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
    failure_counts = Counter(str(row["policy_id"]) for row in failure_rows)
    failure_line = ", ".join(f"`{key}` {value}" for key, value in sorted(failure_counts.items())) or "none"
    return f"""# E008-M70 Full-Val-Mini Detector Candidate Goal-Evaluation Smoke

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M69 status: `{coverage['m69_status']}`.
- Eval episode rows: {coverage['eval_episode_rows']}.
- Candidate-goal eval rows: {coverage['candidate_goal_eval_rows']}.
- Scan-policy rows: {coverage['scan_policy_metric_rows']}.
- Episode-task goal metric rows: {coverage['episode_task_goal_metric_rows']}.
- Aggregate policy rows: {coverage['aggregate_policy_rows']}.
- Primary eval metric: `{coverage['primary_metric']}`.
- Eval-only goal/viewpoint policy leakage: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.
- Failure rows under primary metric: {coverage['primary_failure_rows']} ({failure_line}).
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Aggregate

| policy_id | primary hits | primary proxy SR | primary proxy SPL | mean hit rank | any-vp 1.5m proxy SR | goal 1.0m proxy SR | mean best any-vp XZ m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(aggregate_lines)}

## Claim Boundary

- E008-M70 uses `ObjectNav` goal/viewpoint fields only as evaluation labels.
- E008-M70 reports `GoalEvalProxySR` / `GoalEvalProxySPL` style diagnostics, not final real navigation `SR` / `SPL`.
- E008-M70 does not resolve detector target-recall matching because M67 matching target rows remain zero.
- Task contexts are included only for denominator accounting; detector visit order is task-agnostic in this unit.
"""


def main() -> None:
    m12 = load_m12_module()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m69_coverage = read_json(M69_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M64_ARTIFACT_DIR / "val_mini_episode_rows.jsonl")
    nav_rows = read_jsonl(M68_ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl")
    visit_rows = read_jsonl(M69_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")
    episode_task_policy_rows = read_jsonl(M69_ARTIFACT_DIR / "episode_task_policy_metric_rows.jsonl")
    if not episode_rows:
        raise SystemExit("missing M64 val_mini_episode_rows.jsonl")
    if not nav_rows:
        raise SystemExit("missing M68 candidate_navmesh_validation_rows.jsonl")
    if not visit_rows:
        raise SystemExit("missing M69 candidate_visit_order_rows.jsonl")

    goal_rows = build_full_val_mini_eval_goal_rows(episode_rows)
    eval_index = m12.build_eval_goal_index(goal_rows)
    oracle_index = {str(row["adapter_episode_id"]): row for row in goal_rows}
    candidate_index = {str(row["proposal_uid"]): row for row in nav_rows}
    candidate_goal_rows = m12.build_candidate_goal_eval_rows(visit_rows, candidate_index, eval_index, oracle_index)
    scan_metric_rows, aggregate_rows = m12.build_metric_rows(candidate_goal_rows)
    policy_metric_rows = scan_metric_rows + aggregate_rows
    episode_task_goal_metric_rows = build_episode_task_goal_metric_rows(scan_metric_rows, episode_task_policy_rows)
    failure_rows = m12.build_failure_rows(scan_metric_rows)
    leakage_audit_rows = m12.build_leakage_audit_rows(candidate_goal_rows, eval_index)
    uses_eval_policy = any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in leakage_audit_rows)
    leakage_pass = all(row.get("leakage_audit_pass") for row in leakage_audit_rows)
    primary_metrics = {str(row["policy_id"]): row for row in aggregate_rows}
    ready = bool(aggregate_rows) and len(goal_rows) == len(episode_rows) and leakage_pass and not uses_eval_policy
    route_decision_rows = build_route_decision_rows(ready)
    claim_boundary_rows = build_claim_boundary_rows()
    primary_success_counts = [int(row.get("primary_success_rows") or 0) for row in aggregate_rows]

    coverage = {
        "version": VERSION,
        "status": "e008_m70_full_val_mini_detector_candidate_goal_evaluation_smoke_ready"
        if ready
        else "e008_m70_full_val_mini_detector_candidate_goal_evaluation_smoke_blocked",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m69_status": m69_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "eval_episode_rows": len(goal_rows),
        "expected_eval_episode_rows": len(episode_rows),
        "loaded_all_viewpoint_episode_rows": sum(
            1 for row in eval_index.values() if int(row.get("eval_all_viewpoint_count_loaded") or 0) > 0
        ),
        "candidate_navmesh_rows": len(nav_rows),
        "visit_order_rows": len(visit_rows),
        "candidate_goal_eval_rows": len(candidate_goal_rows),
        "scan_policy_metric_rows": len(scan_metric_rows),
        "episode_task_goal_metric_rows": len(episode_task_goal_metric_rows),
        "aggregate_policy_rows": len(aggregate_rows),
        "policy_goal_metric_rows": len(policy_metric_rows),
        "primary_metric": PRIMARY_METRIC,
        "primary_failure_rows": len(failure_rows),
        "primary_success_count_min": min(primary_success_counts) if primary_success_counts else 0,
        "primary_success_count_max": max(primary_success_counts) if primary_success_counts else 0,
        "policy_primary_metrics": {
            policy_id: {
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get("primary_first_hit_rank_mean_over_success"),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "best_any_viewpoint_xz_m_mean": row.get("best_any_viewpoint_xz_m_mean"),
            }
            for policy_id, row in primary_metrics.items()
        },
        "leakage_audit_rows": len(leakage_audit_rows),
        "leakage_audit_pass": leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": uses_eval_policy,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "real_navigation_sr_spl_ready": False,
        "real_navigation_sr_spl_smoke_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "detector_target_recall_claim_ready": False,
        "h001_navigation_policy_execution_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "full_val_mini_eval_goal_rows.jsonl", goal_rows)
        write_jsonl(output_dir / "candidate_goal_eval_rows.jsonl", candidate_goal_rows)
        write_jsonl(output_dir / "policy_goal_metric_rows.jsonl", policy_metric_rows)
        write_jsonl(output_dir / "episode_task_goal_metric_rows.jsonl", episode_task_goal_metric_rows)
        write_jsonl(output_dir / "failure_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_audit_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, aggregate_rows, failure_rows), encoding="utf-8")
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
