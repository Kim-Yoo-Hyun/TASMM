#!/usr/bin/env python3
"""Run E008-M04 ObjectNav oracle path/metric smoke."""

from __future__ import annotations

import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M04_objectnav_oracle_path_smoke_v0"
VERSION = "e008_m04_objectnav_oracle_path_smoke_v0"

M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M03_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"


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


def scene_docker_path(scene_id_raw: str) -> str:
    parts = Path(scene_id_raw).parts
    if len(parts) >= 4 and parts[0] == "hm3d_v0.2":
        split, scene_dir, scene_file = parts[1], parts[2], parts[3]
        return f"/data/versioned_data/hm3d-0.2/hm3d/{split}/{scene_dir}/{scene_file}"
    return f"/data/versioned_data/hm3d-0.2/hm3d/{scene_id_raw}"


def build_docker_input(goal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in goal_rows:
        rows.append(
            {
                "adapter_episode_id": row["adapter_episode_id"],
                "source_episode_id": row["source_episode_id"],
                "scene_key": row["scene_key"],
                "scene_docker_path": scene_docker_path(str(row["scene_id_raw"])),
                "object_category": row["object_category"],
                "start_position": row["start_position"],
                "eval_first_viewpoint_position": row["eval_first_viewpoint_position"],
                "eval_goal_position": row["eval_goal_position"],
                "eval_geodesic_distance": row["eval_geodesic_distance"],
                "eval_euclidean_distance": row["eval_euclidean_distance"],
                "eval_goal_fields_ready": row["eval_goal_fields_ready"],
            }
        )
    return rows


def parse_json_stdout(stdout: str) -> Any:
    for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
        if line.startswith("[") or line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON object found in docker stdout")


def run_docker_path_smoke(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.dumps(rows)
    code = f"""
import json
import math
import habitat_sim

rows = json.loads({json.dumps(payload)})
by_scene = {{}}
for row in rows:
    by_scene.setdefault(row["scene_docker_path"], []).append(row)

def as_float_list(vec):
    return [float(x) for x in vec]

def dist(a, b):
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))

def find_path(sim, start, end):
    out = {{
        "path_found": False,
        "geodesic_distance": None,
        "point_count": 0,
        "error": "",
    }}
    try:
        path = habitat_sim.ShortestPath()
        path.requested_start = start
        path.requested_end = end
        found = bool(sim.pathfinder.find_path(path))
        out["path_found"] = found
        out["geodesic_distance"] = float(path.geodesic_distance) if found else None
        out["point_count"] = len(path.points) if found else 0
    except Exception as exc:
        out["error"] = repr(exc)
    return out

result_rows = []
for scene_path, scene_rows in by_scene.items():
    sim = None
    try:
        sim_cfg = habitat_sim.SimulatorConfiguration()
        sim_cfg.scene_id = scene_path
        sim_cfg.scene_dataset_config_file = {json.dumps(SCENE_DATASET_CONFIG)}
        sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.AgentConfiguration()]))
        for row in scene_rows:
            out = dict(row)
            start = row.get("start_position")
            view = row.get("eval_first_viewpoint_position")
            goal = row.get("eval_goal_position")
            out["pathfinder_loaded"] = bool(sim.pathfinder.is_loaded)
            out["start_navigable"] = bool(sim.pathfinder.is_navigable(start)) if start else False
            out["viewpoint_navigable"] = bool(sim.pathfinder.is_navigable(view)) if view else False
            view_path = find_path(sim, start, view) if start and view else {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": "missing_start_or_view"}}
            out["viewpoint_path_found"] = view_path["path_found"]
            out["viewpoint_path_geodesic_distance"] = view_path["geodesic_distance"]
            out["viewpoint_path_point_count"] = view_path["point_count"]
            out["viewpoint_path_error"] = view_path["error"]
            out["viewpoint_path_vs_episode_geodesic_abs_delta"] = (
                abs(float(row["eval_geodesic_distance"]) - float(view_path["geodesic_distance"]))
                if view_path["geodesic_distance"] is not None and row.get("eval_geodesic_distance") is not None
                else None
            )
            if goal:
                out["goal_centroid_navigable"] = bool(sim.pathfinder.is_navigable(goal))
                snapped = sim.pathfinder.snap_point(goal)
                snapped_list = as_float_list(snapped)
                out["goal_snapped_position"] = snapped_list
                out["goal_snap_distance_m"] = dist(goal, snapped_list)
                goal_path = find_path(sim, start, snapped_list)
                out["goal_snapped_path_found"] = goal_path["path_found"]
                out["goal_snapped_path_geodesic_distance"] = goal_path["geodesic_distance"]
                out["goal_snapped_path_point_count"] = goal_path["point_count"]
                out["goal_snapped_path_error"] = goal_path["error"]
            else:
                out["goal_centroid_navigable"] = False
                out["goal_snapped_position"] = None
                out["goal_snap_distance_m"] = None
                out["goal_snapped_path_found"] = False
                out["goal_snapped_path_geodesic_distance"] = None
                out["goal_snapped_path_point_count"] = 0
                out["goal_snapped_path_error"] = "missing_goal"
            result_rows.append(out)
    except Exception as exc:
        for row in scene_rows:
            out = dict(row)
            out["pathfinder_loaded"] = False
            out["scene_error"] = repr(exc)
            out["viewpoint_path_found"] = False
            out["goal_snapped_path_found"] = False
            result_rows.append(out)
    finally:
        if sim is not None:
            sim.close()
print(json.dumps(result_rows, sort_keys=True))
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python - <<'PY'\n" + code + "\nPY",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=120)
    meta = {
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
        "requested_episode_count": len(rows),
        "command": " ".join(cmd[:8]) + " ...",
        "mount": f"{RESEARCH2_DATA_ROOT}:/data:ro",
    }
    if proc.returncode != 0:
        return [], meta
    try:
        return parse_json_stdout(proc.stdout), meta
    except Exception as exc:
        meta["ok"] = False
        meta["parse_error"] = str(exc)
        return [], meta


def build_metric_rows(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in path_rows:
        found = bool(row.get("viewpoint_path_found"))
        path_len = row.get("viewpoint_path_geodesic_distance")
        rows.append(
            {
                "adapter_episode_id": row["adapter_episode_id"],
                "scene_key": row["scene_key"],
                "object_category": row["object_category"],
                "metric_source": "ObjectNav eval viewpoint oracle",
                "policy_input_allowed": False,
                "oracle_success": found,
                "oracle_spl_if_executed_on_shortest_path": 1.0 if found else 0.0,
                "oracle_path_length_m": path_len,
                "episode_geodesic_distance_m": row.get("eval_geodesic_distance"),
                "viewpoint_path_vs_episode_geodesic_abs_delta": row.get("viewpoint_path_vs_episode_geodesic_abs_delta"),
                "goal_snap_distance_m": row.get("goal_snap_distance_m"),
                "real_navigation_sr_spl_ready": False,
                "reason": "Metric plumbing smoke only; oracle goal/viewpoint fields are evaluation-only and are not policy inputs.",
            }
        )
    return rows


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e008_m05_hm3d_candidate_source_staging_plan",
            "selected": ready,
            "decision": "selected_next" if ready else "blocked",
            "next_unit": "E008-M05 HM3D candidate-source staging plan",
            "launch_long_job_now": False,
            "reason": "Oracle path/metric plumbing is ready; H001 execution now needs non-oracle stale-memory/current-observation/external-map candidate sources.",
        },
        {
            "rank": 2,
            "route_id": "e008_h001_navigation_execution_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "E008-M06 or later bounded H001 navigation execution",
            "launch_long_job_now": False,
            "reason": "H001 candidate-source rows for HM3D are still missing.",
        },
        {
            "rank": 3,
            "route_id": "e008_full_sr_spl_table_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "later full navigation evaluation",
            "launch_long_job_now": False,
            "reason": "Full real `SR` / `SPL` requires policy candidate sources, execution rows, baselines, and trajectory metrics.",
        },
    ]


def mean(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(coverage: dict[str, Any], path_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    path_summary = [
        {
            "episode": row["adapter_episode_id"],
            "category": row["object_category"],
            "viewpoint_path": row.get("viewpoint_path_found"),
            "path_m": row.get("viewpoint_path_geodesic_distance"),
            "goal_snap_m": row.get("goal_snap_distance_m"),
        }
        for row in path_rows
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
        "# E008-M04 ObjectNav Oracle Path Smoke\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Episode rows: {coverage['episode_rows']}.\n"
        f"- Viewpoint paths found: {coverage['viewpoint_paths_found']} / {coverage['episode_rows']}.\n"
        f"- Goal snapped paths found: {coverage['goal_snapped_paths_found']} / {coverage['episode_rows']}.\n"
        f"- Mean oracle viewpoint path length: {coverage['mean_viewpoint_path_length_m']}.\n"
        f"- Mean goal snap distance: {coverage['mean_goal_snap_distance_m']}.\n"
        f"- Oracle metric plumbing ready: {str(coverage['oracle_metric_plumbing_ready']).lower()}.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        "## Oracle Path Rows\n\n"
        + markdown_table(path_summary, ["episode", "category", "viewpoint_path", "path_m", "goal_snap_m"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M04 validates `Habitat` path/metric plumbing with `ObjectNav` eval-only goal/viewpoint fields.\n"
        "- These oracle rows are not H001 policy evidence and cannot be used as policy inputs.\n"
        "- Real navigation `SR` / `SPL` remains false because no H001 or baseline candidate visit order has been executed.\n"
        "- The next required step is to stage non-oracle `HM3D` candidate sources for stale memory, current observation, and external map baselines.\n\n"
        "## Agent Inference\n\n"
        "- The simulator metric path is technically viable for the tiny `val_mini` subset.\n"
        "- The blocker has moved from simulator/path plumbing to candidate-source construction for deployable policies.\n"
    )


def main() -> None:
    m03_coverage = read_json(M03_ARTIFACT_DIR / "coverage.json")
    goal_rows = read_jsonl(M03_DATA_DIR / "episode_goal_eval_rows.jsonl")
    docker_input = build_docker_input(goal_rows)
    path_rows, docker_meta = run_docker_path_smoke(docker_input)
    metric_rows = build_metric_rows(path_rows)

    viewpoint_found = sum(1 for row in path_rows if row.get("viewpoint_path_found"))
    goal_found = sum(1 for row in path_rows if row.get("goal_snapped_path_found"))
    oracle_ready = (
        m03_coverage.get("status") == "e008_m03_h001_candidate_navigation_adapter_contract_ready"
        and docker_meta.get("ok") is True
        and len(path_rows) == len(goal_rows)
        and len(goal_rows) > 0
        and viewpoint_found == len(goal_rows)
    )
    route_rows = build_route_rows(oracle_ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m04_objectnav_oracle_path_smoke_ready" if oracle_ready else "e008_m04_objectnav_oracle_path_smoke_blocked",
        "m03_status": m03_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "habitat_image": HABITAT_IMAGE,
        "episode_rows": len(goal_rows),
        "path_rows": len(path_rows),
        "viewpoint_paths_found": viewpoint_found,
        "goal_snapped_paths_found": goal_found,
        "mean_viewpoint_path_length_m": mean([row.get("viewpoint_path_geodesic_distance") for row in path_rows]),
        "mean_goal_snap_distance_m": mean([row.get("goal_snap_distance_m") for row in path_rows]),
        "mean_viewpoint_path_vs_episode_geodesic_abs_delta": mean([row.get("viewpoint_path_vs_episode_geodesic_abs_delta") for row in path_rows]),
        "oracle_metric_plumbing_ready": oracle_ready,
        "h001_candidate_source_rows_ready": m03_coverage.get("h001_candidate_source_rows_ready", 0),
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "docker_returncode": docker_meta.get("returncode"),
        "selected_next_unit": "E008-M05 HM3D candidate-source staging plan" if oracle_ready else "repair E008-M04 oracle path smoke",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_smoke_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "oracle_path_rows.jsonl", path_rows)
    write_jsonl(ARTIFACT_DIR / "metric_smoke_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, path_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "oracle_path_rows.jsonl", path_rows)
    write_jsonl(DATA_OUT_DIR / "metric_smoke_rows.jsonl", metric_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
