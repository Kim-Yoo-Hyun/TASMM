#!/usr/bin/env python3
"""Plan E008-M03 H001 candidate-to-navigation adapter contract."""

from __future__ import annotations

import gzip
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
VERSION = "e008_m03_h001_candidate_navigation_adapter_contract_v0"

M02_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M02_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M100_DIR = ROOT / "experiments" / "E005_external_baseline_transition" / "artifacts" / "E005-M100_conceptgraphs_assisted_fallback_policy_v0"
E007_M04_DIR = ROOT / "experiments" / "E007_navigation_path_cost_bridge" / "artifacts" / "E007-M04_path_cost_policy_metrics_v0"

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

SELECTED_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_goal_index() -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for content_file in sorted(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        goals_by_category = payload.get("goals_by_category", {})
        for key, goals in goals_by_category.items():
            if "_" not in key:
                continue
            scene_file, category = key.split("_", 1)
            if isinstance(goals, list):
                index[(scene_file, category)] = goals
    return index


def build_episode_goal_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    goal_index = load_goal_index()
    out: list[dict[str, Any]] = []
    for row in episode_rows:
        scene_file = Path(str(row["scene_id_raw"])).name
        category = str(row["object_category"])
        goals = goal_index.get((scene_file, category), [])
        closest_id = row.get("closest_goal_object_id")
        selected_goal = None
        for goal in goals:
            if goal.get("object_id") == closest_id:
                selected_goal = goal
                break
        if selected_goal is None and goals:
            selected_goal = goals[0]
        viewpoints = selected_goal.get("view_points", []) if isinstance(selected_goal, dict) else []
        first_view = viewpoints[0].get("agent_state", {}) if viewpoints else {}
        out.append(
            {
                "adapter_episode_id": row["adapter_episode_id"],
                "source_episode_id": row["source_episode_id"],
                "scene_key": row["scene_key"],
                "scene_id_raw": row["scene_id_raw"],
                "object_category": category,
                "start_position": row["start_position"],
                "start_rotation": row["start_rotation"],
                "eval_goal_object_id": closest_id,
                "eval_goal_position": selected_goal.get("position") if isinstance(selected_goal, dict) else None,
                "eval_goal_object_name": selected_goal.get("object_name") if isinstance(selected_goal, dict) else None,
                "eval_viewpoint_count": len(viewpoints),
                "eval_first_viewpoint_position": first_view.get("position"),
                "eval_first_viewpoint_rotation": first_view.get("rotation"),
                "eval_geodesic_distance": row.get("geodesic_distance"),
                "eval_euclidean_distance": row.get("euclidean_distance"),
                "eval_goal_fields_ready": selected_goal is not None and bool(viewpoints),
                "policy_input_allowed": False,
                "reason": "ObjectNav goal position, object id, view points, and shortest-path distances are evaluation-only fields.",
            }
        )
    return out


def build_candidate_schema_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_uid", "string", "Unique candidate id before execution.", True, True),
        ("candidate_source", "enum", "old memory / current detector / external map / oracle eval source.", True, True),
        ("candidate_rank", "int", "Policy visit rank starting from 1.", True, True),
        ("candidate_label", "string", "Query/category label for the candidate.", True, True),
        ("candidate_xyz", "float[3]", "3D candidate point in simulator scene coordinates.", True, True),
        ("candidate_viewpoint_position", "float[3]", "Optional navigable viewpoint for visiting the candidate.", True, True),
        ("candidate_viewpoint_rotation", "float[4]", "Optional orientation at the candidate viewpoint.", False, True),
        ("candidate_confidence", "float", "Detector/map confidence available before execution.", False, True),
        ("memory_trust_score", "float", "H001 memory-trust score available before execution.", False, True),
        ("staleness_score", "float", "Estimated staleness/motion risk available before execution.", False, True),
        ("path_cost_estimate_m", "float", "Pre-execution path-cost estimate from available map/navmesh.", False, True),
        ("fallback_trigger", "string", "Runtime-observable miss/exhaustion event; not evaluation label.", False, True),
        ("target_match_distance", "float", "Distance to ground-truth target after evaluation.", False, False),
        ("success_label", "bool", "Post-execution success label.", False, False),
        ("eval_goal_object_id", "int", "ObjectNav target object id.", False, False),
        ("eval_goal_position", "float[3]", "ObjectNav target goal position.", False, False),
        ("eval_viewpoint_position", "float[3]", "ObjectNav target viewpoint.", False, False),
        ("shortest_path_to_goal", "float", "Metric-only shortest path distance.", False, False),
    ]
    return [
        {
            "field": field,
            "type": typ,
            "description": desc,
            "required_for_candidate_adapter": required,
            "policy_input_allowed": allowed,
        }
        for field, typ, desc, required, allowed in fields
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    allowed = [
        ("object_category", "The query category is the task."),
        ("scene_id_raw", "Required to load the simulator scene."),
        ("start_position", "Required for navigation execution."),
        ("start_rotation", "Required for navigation execution."),
        ("task_context_id", "Structured context can condition memory trust and search budget."),
        ("candidate_xyz", "Candidate location generated before execution."),
        ("candidate_source", "Needed for policy comparison and ablation."),
        ("candidate_confidence", "Allowed only if produced before action by detector/map."),
        ("memory_trust_score", "Allowed only if computed from stale-memory/current-observation features."),
        ("path_cost_estimate_m", "Allowed only if computed before execution from map/navmesh."),
        ("fallback_trigger_observed_miss", "Allowed only as a runtime event after visiting returned candidates."),
    ]
    blocked = [
        ("closest_goal_object_id", "ObjectNav evaluation target id."),
        ("eval_goal_position", "Ground-truth target position."),
        ("eval_viewpoint_position", "Ground-truth ObjectNav viewpoint."),
        ("goals_by_category", "Contains target object positions and viewpoints."),
        ("geodesic_distance", "Shortest-path metric field."),
        ("euclidean_distance", "Evaluation diagnostic field."),
        ("target_match_distance", "Post-hoc matching result."),
        ("success_label", "Post-execution metric."),
        ("query_bridge_success", "Post-hoc success label from proxy tables."),
        ("old_location_dead_end_expected", "Evaluation-only dead-end label."),
    ]
    rows = [
        {"field": field, "policy_input": "allowed", "reason": reason}
        for field, reason in allowed
    ]
    rows.extend({"field": field, "policy_input": "blocked", "reason": reason} for field, reason in blocked)
    return rows


def unique_policy_metrics() -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(E007_M04_DIR / "policy_metric_summary_rows.jsonl"):
        if row.get("subset") != "full_denominator":
            continue
        metrics[str(row["policy"])] = {
            "e007_query_policy_rows": row.get("query_policy_rows"),
            "e007_query_bridge_success_rows": row.get("query_bridge_success_rows_full_denominator"),
            "e007_mean_path_attempt_spl_proxy": row.get("mean_path_attempt_spl_proxy_source_ready"),
            "e007_mean_path_expected_search_cost_m": row.get("mean_path_expected_search_cost_m_source_ready"),
        }
    return metrics


def policy_input_fields_from_m100() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(M100_DIR / "policy_rows.jsonl"):
        policy = str(row["policy"])
        out.setdefault(
            policy,
            {
                "candidate_visit_order": row.get("candidate_visit_order"),
                "policy_input_fields_used": row.get("policy_input_fields_used", []),
                "count": 0,
            },
        )
        out[policy]["count"] += 1
    return out


def build_policy_adapter_rows() -> list[dict[str, Any]]:
    e007_metrics = unique_policy_metrics()
    m100_fields = policy_input_fields_from_m100()
    policy_specs = [
        {
            "policy": "real_static_memory_only_v0",
            "policy_family": "static_stale_memory",
            "required_candidate_sources": ["stale_memory_candidates"],
            "hm3d_required_source_status": "missing_stale_memory_injection",
            "candidate_visit_order_contract": "visit stale-memory candidates in memory order",
        },
        {
            "policy": "real_detector_confidence_top5_v0",
            "policy_family": "detector_confidence_ranking",
            "required_candidate_sources": ["hm3d_rgbd_detector_candidates"],
            "hm3d_required_source_status": "missing_hm3d_rgbd_detector_or_map_candidates",
            "candidate_visit_order_contract": "visit detector candidates by confidence top5",
        },
        {
            "policy": "conceptgraphs_only_strict_top5_v0",
            "policy_family": "external_open_vocab_map",
            "required_candidate_sources": ["hm3d_conceptgraphs_map_candidates"],
            "hm3d_required_source_status": "missing_hm3d_conceptgraphs_or_equivalent_map_candidates",
            "candidate_visit_order_contract": "visit external map candidates by CLIP/text rank top5",
        },
        {
            "policy": "real_context_agnostic_memory_trust_reobserve_v0",
            "policy_family": "context_agnostic_memory_trust",
            "required_candidate_sources": ["stale_memory_candidates", "current_observation_candidates"],
            "hm3d_required_source_status": "missing_stale_memory_and_current_observation_candidate_sources",
            "candidate_visit_order_contract": "use memory trust without task-context-specific utility",
        },
        {
            "policy": "h001_real_task_context_memory_trust_v0",
            "policy_family": "h001_memory_trust",
            "required_candidate_sources": ["stale_memory_candidates", "current_observation_candidates", "task_context_id"],
            "hm3d_required_source_status": "missing_stale_memory_and_current_observation_candidate_sources",
            "candidate_visit_order_contract": "H001 memory-trust queue conditioned by structured task context",
        },
        {
            "policy": SELECTED_POLICY,
            "policy_family": "h001_plus_external_map_fallback",
            "required_candidate_sources": ["stale_memory_candidates", "current_observation_candidates", "hm3d_external_map_candidates", "observed_miss_runtime_event"],
            "hm3d_required_source_status": "missing_h001_candidate_sources_and_external_map_candidates",
            "candidate_visit_order_contract": "H001 queue first; after observed miss/exhaustion, visit external map top5",
        },
        {
            "policy": "oracle_goal_shortest_path_v0",
            "policy_family": "evaluation_upper_bound",
            "required_candidate_sources": ["ObjectNav eval goals"],
            "hm3d_required_source_status": "ready_eval_only",
            "candidate_visit_order_contract": "use ObjectNav ground-truth goal/viewpoint only as upper-bound metric smoke",
        },
    ]
    rows = []
    for spec in policy_specs:
        policy = spec["policy"]
        metrics = e007_metrics.get(policy, {})
        m100 = m100_fields.get(policy, {})
        executable = spec["hm3d_required_source_status"] == "ready_eval_only"
        rows.append(
            {
                **spec,
                "e007_proxy_policy_ready": policy in e007_metrics or policy == "oracle_goal_shortest_path_v0",
                "m100_policy_rows": m100.get("count", 0),
                "m100_candidate_visit_order": m100.get("candidate_visit_order", spec["candidate_visit_order_contract"]),
                "m100_policy_input_fields_used": m100.get("policy_input_fields_used", []),
                "hm3d_candidate_adapter_contract_ready": True,
                "hm3d_policy_execution_ready": False,
                "hm3d_oracle_upper_bound_smoke_ready": executable,
                "policy_input_leakage_guard_ready": True,
                "real_navigation_sr_spl_ready": False,
                **metrics,
            }
        )
    return rows


def build_candidate_source_rows(policy_rows: list[dict[str, Any]], episode_goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    needed = Counter()
    for row in policy_rows:
        if row["policy"] == "oracle_goal_shortest_path_v0":
            continue
        needed.update(row["required_candidate_sources"])
    return [
        {
            "candidate_source": "ObjectNav eval goals",
            "status": "ready_eval_only",
            "rows_ready": sum(1 for row in episode_goal_rows if row["eval_goal_fields_ready"]),
            "policy_input_allowed": False,
            "used_for": "oracle upper-bound metric smoke only",
        },
        {
            "candidate_source": "stale_memory_candidates",
            "status": "missing_for_hm3d",
            "rows_ready": 0,
            "policy_input_allowed": True,
            "used_for": "static stale memory, H001 memory trust, context-agnostic memory trust",
            "required_by_policy_count": needed["stale_memory_candidates"],
        },
        {
            "candidate_source": "current_observation_candidates",
            "status": "missing_for_hm3d",
            "rows_ready": 0,
            "policy_input_allowed": True,
            "used_for": "detector/current-observation re-observation and H001 memory trust",
            "required_by_policy_count": needed["current_observation_candidates"],
        },
        {
            "candidate_source": "hm3d_rgbd_detector_candidates",
            "status": "missing_for_hm3d",
            "rows_ready": 0,
            "policy_input_allowed": True,
            "used_for": "detector-confidence ranking baseline",
            "required_by_policy_count": needed["hm3d_rgbd_detector_candidates"],
        },
        {
            "candidate_source": "hm3d_external_map_candidates",
            "status": "missing_for_hm3d",
            "rows_ready": 0,
            "policy_input_allowed": True,
            "used_for": "ConceptGraphs/HOV-SG/Open3DSG-like external map fallback",
            "required_by_policy_count": needed["hm3d_external_map_candidates"] + needed["hm3d_conceptgraphs_map_candidates"],
        },
        {
            "candidate_source": "observed_miss_runtime_event",
            "status": "contract_ready_execution_missing",
            "rows_ready": 0,
            "policy_input_allowed": True,
            "used_for": "H001 fallback trigger after runtime candidate exhaustion",
            "required_by_policy_count": needed["observed_miss_runtime_event"],
        },
    ]


def build_route_rows(contract_ready: bool, oracle_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e008_m04_objectnav_goal_oracle_path_smoke",
            "selected": contract_ready and oracle_ready,
            "decision": "selected_next" if contract_ready and oracle_ready else "blocked",
            "next_unit": "E008-M04 ObjectNav goal/viewpoint oracle path smoke",
            "launch_long_job_now": False,
            "reason": "Before H001 execution, verify that ObjectNav eval goals/viewpoints and Habitat path metrics can produce a bounded oracle upper-bound row without leaking it into policy inputs.",
        },
        {
            "rank": 2,
            "route_id": "e008_h001_policy_execution_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "E008-M05 or later H001 candidate-source staging",
            "launch_long_job_now": False,
            "reason": "H001 real navigation execution needs stale-memory/current-observation/external-map candidate sources in HM3D coordinates.",
        },
        {
            "rank": 3,
            "route_id": "e008_full_navigation_benchmark_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "later bounded execution batch",
            "launch_long_job_now": False,
            "reason": "Full `SR` / `SPL` benchmark should wait until oracle smoke and policy candidate-source rows are ready.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    policy_summary = [
        {
            "policy": row["policy"],
            "source_status": row["hm3d_required_source_status"],
            "contract": row["hm3d_candidate_adapter_contract_ready"],
            "execution": row["hm3d_policy_execution_ready"],
        }
        for row in policy_rows
    ]
    source_summary = [
        {
            "candidate_source": row["candidate_source"],
            "status": row["status"],
            "rows_ready": row["rows_ready"],
            "policy_input": row["policy_input_allowed"],
        }
        for row in source_rows
    ]
    route_summary = [
        {
            "rank": row["rank"],
            "route_id": row["route_id"],
            "decision": row["decision"],
            "next_unit": row["next_unit"],
        }
        for row in route_rows
    ]
    return (
        "# E008-M03 H001 Candidate Navigation Adapter Contract\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- M02 episode rows: {coverage['m02_episode_rows']}.\n"
        f"- Eval goal rows ready: {coverage['eval_goal_rows_ready']} / {coverage['m02_episode_rows']}.\n"
        f"- Policy adapter rows: {coverage['policy_adapter_rows']}.\n"
        f"- Candidate source rows ready for H001 execution: {coverage['h001_candidate_source_rows_ready']}.\n"
        f"- Oracle upper-bound smoke ready: {str(coverage['oracle_upper_bound_smoke_ready']).lower()}.\n"
        f"- H001 navigation policy execution ready: {str(coverage['h001_navigation_policy_execution_ready']).lower()}.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        "## Policy Adapter Boundary\n\n"
        + markdown_table(policy_summary, ["policy", "source_status", "contract", "execution"])
        + "\n\n"
        "## Candidate Sources\n\n"
        + markdown_table(source_summary, ["candidate_source", "status", "rows_ready", "policy_input"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M03 fixes the H001-to-navigation candidate schema and leakage guard only.\n"
        "- ObjectNav goal positions and viewpoints are ready, but they are evaluation-only and cannot be used by H001 or baselines.\n"
        "- H001 real navigation execution is still blocked because HM3D stale-memory, current-observation, and external-map candidate sources are not staged.\n"
        "- Real navigation `SR` / `SPL` remains false until candidate visit orders are executed in Habitat and trajectory metrics are computed.\n\n"
        "## Agent Inference\n\n"
        "- The most defensible next step is a bounded ObjectNav oracle path smoke to validate metric plumbing without claiming H001 navigation performance.\n"
        "- After the oracle smoke, H001 needs HM3D candidate-source staging before a real policy execution table can be launched.\n"
    )


def main() -> None:
    m02_coverage = read_json(M02_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M02_DATA_DIR / "episode_adapter_rows.jsonl")
    episode_goal_rows = build_episode_goal_rows(episode_rows)
    schema_rows = build_candidate_schema_rows()
    input_guard_rows = build_input_guard_rows()
    policy_rows = build_policy_adapter_rows()
    source_rows = build_candidate_source_rows(policy_rows, episode_goal_rows)

    eval_goal_ready = sum(1 for row in episode_goal_rows if row["eval_goal_fields_ready"])
    h001_ready_sources = [
        row for row in source_rows
        if row["policy_input_allowed"] and row["rows_ready"] > 0 and row["candidate_source"] != "observed_miss_runtime_event"
    ]
    oracle_ready = eval_goal_ready == len(episode_rows) and len(episode_rows) > 0
    contract_ready = (
        m02_coverage.get("status") == "e008_m02_hm3d_objectnav_adapter_smoke_ready"
        and bool(policy_rows)
        and all(row["policy_input_leakage_guard_ready"] for row in policy_rows)
        and bool(schema_rows)
    )
    h001_execution_ready = False
    route_rows = build_route_rows(contract_ready, oracle_ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m03_h001_candidate_navigation_adapter_contract_ready" if contract_ready else "e008_m03_h001_candidate_navigation_adapter_contract_blocked",
        "m02_status": m02_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m02_episode_rows": len(episode_rows),
        "eval_goal_rows_ready": eval_goal_ready,
        "candidate_schema_rows": len(schema_rows),
        "input_guard_rows": len(input_guard_rows),
        "policy_adapter_rows": len(policy_rows),
        "candidate_source_rows": len(source_rows),
        "h001_candidate_source_rows_ready": len(h001_ready_sources),
        "oracle_upper_bound_smoke_ready": oracle_ready,
        "h001_navigation_policy_execution_ready": h001_execution_ready,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M04 ObjectNav goal/viewpoint oracle path smoke" if contract_ready and oracle_ready else "repair E008-M03 candidate adapter contract",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "candidate_schema_rows.jsonl", schema_rows)
    write_jsonl(ARTIFACT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(ARTIFACT_DIR / "policy_adapter_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_source_rows.jsonl", source_rows)
    write_jsonl(ARTIFACT_DIR / "episode_goal_eval_rows.jsonl", episode_goal_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, policy_rows, source_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_schema_rows.jsonl", schema_rows)
    write_jsonl(DATA_OUT_DIR / "input_guard_rows.jsonl", input_guard_rows)
    write_jsonl(DATA_OUT_DIR / "policy_adapter_rows.jsonl", policy_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_source_rows.jsonl", source_rows)
    write_jsonl(DATA_OUT_DIR / "episode_goal_eval_rows.jsonl", episode_goal_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
