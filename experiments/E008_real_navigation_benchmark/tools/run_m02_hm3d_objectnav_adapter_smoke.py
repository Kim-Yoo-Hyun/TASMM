#!/usr/bin/env python3
"""Run E008-M02 HM3D ObjectNav episode/source adapter smoke."""

from __future__ import annotations

import gzip
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
VERSION = "e008_m02_hm3d_objectnav_adapter_smoke_v0"

M01_DIR = EXP_ROOT / "artifacts" / "E008-M01_navigation_source_episode_contract_v0"
RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HM3D_SCENE_ROOT = RESEARCH2_DATA_ROOT / "versioned_data" / "hm3d-0.2" / "hm3d"
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
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
SCENE_DATASET_CONFIG = HM3D_SCENE_ROOT / "minival" / "hm3d_annotated_minival_basis.scene_dataset_config.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def to_docker_path(path: Path) -> str:
    return "/data/" + str(path.resolve().relative_to(RESEARCH2_DATA_ROOT.resolve()))


def resolve_scene(scene_id: str) -> dict[str, Any]:
    parts = Path(scene_id).parts
    if len(parts) >= 4 and parts[0] == "hm3d_v0.2":
        split = parts[1]
        scene_dir = parts[2]
        scene_file = parts[3]
        scene_path = HM3D_SCENE_ROOT / split / scene_dir / scene_file
    else:
        split = "unknown"
        scene_dir = Path(scene_id).parent.name
        scene_file = Path(scene_id).name
        scene_path = HM3D_SCENE_ROOT / scene_id

    navmesh_path = scene_path.with_suffix(".navmesh")
    return {
        "scene_id_raw": scene_id,
        "split": split,
        "scene_key": scene_dir,
        "scene_path": str(scene_path),
        "navmesh_path": str(navmesh_path),
        "scene_docker_path": to_docker_path(scene_path) if scene_path.exists() else "",
        "navmesh_docker_path": to_docker_path(navmesh_path) if navmesh_path.exists() else "",
        "scene_ready": scene_path.exists(),
        "navmesh_ready": navmesh_path.exists(),
        "scene_file": scene_file,
    }


def load_episode_sample(per_file: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for content_file in sorted(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")):
        with gzip.open(content_file, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        for episode in payload.get("episodes", [])[:per_file]:
            resolved = resolve_scene(str(episode.get("scene_id", "")))
            info = episode.get("info", {}) if isinstance(episode.get("info"), dict) else {}
            adapter_episode_id = f"{resolved['scene_key']}::{episode.get('episode_id')}"
            rows.append(
                {
                    "adapter_episode_id": adapter_episode_id,
                    "source_episode_id": str(episode.get("episode_id", "")),
                    "content_file": content_file.name,
                    "dataset": "HM3D ObjectNav v2",
                    "split": "val_mini",
                    "scene_id_raw": resolved["scene_id_raw"],
                    "scene_key": resolved["scene_key"],
                    "resolved_scene_path": resolved["scene_path"],
                    "resolved_navmesh_path": resolved["navmesh_path"],
                    "scene_docker_path": resolved["scene_docker_path"],
                    "navmesh_docker_path": resolved["navmesh_docker_path"],
                    "scene_ready": resolved["scene_ready"],
                    "navmesh_ready": resolved["navmesh_ready"],
                    "object_category": episode.get("object_category"),
                    "start_position": episode.get("start_position"),
                    "start_rotation": episode.get("start_rotation"),
                    "geodesic_distance": info.get("geodesic_distance"),
                    "euclidean_distance": info.get("euclidean_distance"),
                    "closest_goal_object_id": info.get("closest_goal_object_id"),
                    "task_context_id": "objectnav_search_default_v0",
                    "policy_visit_order_ready": False,
                    "candidate_goal_adapter_ready": False,
                    "executable_episode_source_ready": resolved["scene_ready"] and resolved["navmesh_ready"],
                }
            )
    return rows


def build_scene_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in episode_rows:
        key = str(row["scene_key"])
        by_key.setdefault(
            key,
            {
                "scene_key": key,
                "scene_id_raw": row["scene_id_raw"],
                "resolved_scene_path": row["resolved_scene_path"],
                "resolved_navmesh_path": row["resolved_navmesh_path"],
                "scene_docker_path": row["scene_docker_path"],
                "navmesh_docker_path": row["navmesh_docker_path"],
                "scene_ready": row["scene_ready"],
                "navmesh_ready": row["navmesh_ready"],
                "episode_rows": 0,
            },
        )
        by_key[key]["episode_rows"] += 1
    return list(by_key.values())


def parse_json_stdout(stdout: str) -> Any:
    for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
        if line.startswith("[") or line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON object found in docker stdout")


def run_docker_scene_smoke(scene_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested = [
        {
            "scene_key": row["scene_key"],
            "scene": row["scene_docker_path"],
            "navmesh": row["navmesh_docker_path"],
            "scene_dataset_config": to_docker_path(SCENE_DATASET_CONFIG) if SCENE_DATASET_CONFIG.exists() else "",
        }
        for row in scene_rows
        if row["scene_ready"] and row["navmesh_ready"]
    ]
    if not requested:
        return [], {"returncode": None, "ok": False, "stdout_tail": "", "stderr_tail": "no requested scenes"}

    code = f"""
import json
import habitat_sim

scenes = json.loads({json.dumps(json.dumps(requested))})
rows = []
for item in scenes:
    row = {{
        "scene_key": item["scene_key"],
        "scene_docker_path": item["scene"],
        "navmesh_docker_path": item["navmesh"],
        "sim_loaded": False,
        "pathfinder_loaded_initial": False,
        "pathfinder_loaded_final": False,
        "navigable_area": None,
        "error": "",
    }}
    sim = None
    try:
        sim_cfg = habitat_sim.SimulatorConfiguration()
        sim_cfg.scene_id = item["scene"]
        if item.get("scene_dataset_config"):
            sim_cfg.scene_dataset_config_file = item["scene_dataset_config"]
        agent_cfg = habitat_sim.AgentConfiguration()
        sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))
        row["sim_loaded"] = True
        row["pathfinder_loaded_initial"] = bool(sim.pathfinder.is_loaded)
        if not sim.pathfinder.is_loaded:
            row["load_nav_mesh_return"] = bool(sim.pathfinder.load_nav_mesh(item["navmesh"]))
        else:
            row["load_nav_mesh_return"] = True
        row["pathfinder_loaded_final"] = bool(sim.pathfinder.is_loaded)
        row["navigable_area"] = float(sim.pathfinder.navigable_area) if sim.pathfinder.is_loaded else None
    except Exception as exc:
        row["error"] = repr(exc)
    finally:
        if sim is not None:
            sim.close()
    rows.append(row)
print(json.dumps(rows, sort_keys=True))
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
        "requested_scene_count": len(requested),
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


def build_metric_placeholder_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "SR",
            "ready_in_m02": False,
            "reason": "M02 verifies executable episode/source rows only; no policy execution is run.",
        },
        {
            "metric": "SPL",
            "ready_in_m02": False,
            "reason": "M02 verifies scene/navmesh loading only; executed trajectory rows do not exist yet.",
        },
        {
            "metric": "ExpectedSearchCost",
            "ready_in_m02": False,
            "reason": "Candidate visit order will be attached in E008-M03.",
        },
        {
            "metric": "E007 proxy-to-execution consistency",
            "ready_in_m02": False,
            "reason": "Requires E008-M03 candidate adapter and later executed or oracle navigation rows.",
        },
    ]


def build_route_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e008_m03_h001_candidate_to_navigation_adapter_contract",
            "selected": ready,
            "decision": "selected_next" if ready else "blocked_until_m02_ready",
            "next_unit": "E008-M03 H001 candidate-to-navigation adapter contract",
            "launch_long_job_now": False,
            "reason": "Episode/source rows and Habitat scene/navmesh smoke must be ready before attaching H001 visit-order policies.",
        },
        {
            "rank": 2,
            "route_id": "e008_full_habitat_execution_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "E008-M04 or later bounded navigation execution",
            "launch_long_job_now": False,
            "reason": "Full execution is premature until candidate goals, blocked inputs, and baseline policy rows are fixed.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(
    coverage: dict[str, Any],
    scene_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    scene_summary = [
        {
            "scene_key": row["scene_key"],
            "episodes": row["episode_rows"],
            "scene_ready": row["scene_ready"],
            "navmesh_ready": row["navmesh_ready"],
        }
        for row in scene_rows
    ]
    docker_summary = [
        {
            "scene_key": row.get("scene_key"),
            "sim_loaded": row.get("sim_loaded"),
            "pathfinder": row.get("pathfinder_loaded_final"),
            "navigable_area": row.get("navigable_area"),
            "error": row.get("error", ""),
        }
        for row in docker_rows
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
        "# E008-M02 HM3D ObjectNav Adapter Smoke\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Sampled episode rows: {coverage['sampled_episode_rows']}.\n"
        f"- Unique scenes: {coverage['unique_scene_rows']}.\n"
        f"- Scene/navmesh rows ready: {coverage['episode_rows_scene_navmesh_ready']} / {coverage['sampled_episode_rows']}.\n"
        f"- Docker Habitat scene smoke success: {str(coverage['docker_scene_smoke_success']).lower()}.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n"
        f"- Launch long job now: {str(coverage['launch_long_job_now']).lower()}.\n\n"
        "## Scene Resolution\n\n"
        + markdown_table(scene_summary, ["scene_key", "episodes", "scene_ready", "navmesh_ready"])
        + "\n\n"
        "## Docker Smoke\n\n"
        + markdown_table(docker_summary, ["scene_key", "sim_loaded", "pathfinder", "navigable_area", "error"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M02 verifies episode/source adaptation and simulator scene/navmesh loading only.\n"
        "- E008-M02 does not claim real navigation `SR` / `SPL` because no candidate visit order has been executed.\n"
        "- E008-M02 does not yet prove stale-memory transfer into `HM3D ObjectNav`; that requires E008-M03 candidate-to-navigation adapter rows.\n"
        "- `HM3D ObjectNav` remains the first real navigation source route, while `3RScan` / `3DSSG` remains the dynamic stale-memory source.\n\n"
        "## Agent Inference\n\n"
        "- The real-navigation source bridge is technically viable at the episode/source layer.\n"
        "- The next defensible step is to attach H001 and baseline candidate visit orders to these executable episodes before launching navigation execution.\n"
    )


def main() -> None:
    m01_coverage = read_json(M01_DIR / "coverage.json")
    episode_rows = load_episode_sample(per_file=3)
    scene_rows = build_scene_rows(episode_rows)
    docker_rows, docker_meta = run_docker_scene_smoke(scene_rows)
    docker_scene_smoke_success = (
        docker_meta.get("ok") is True
        and len(docker_rows) == len(scene_rows)
        and all(row.get("sim_loaded") and row.get("pathfinder_loaded_final") for row in docker_rows)
    )
    all_episode_sources_ready = bool(episode_rows) and all(row["executable_episode_source_ready"] for row in episode_rows)
    m01_ready = m01_coverage.get("status") == "e008_m01_navigation_source_episode_contract_ready"
    adapter_ready = m01_ready and all_episode_sources_ready and docker_scene_smoke_success
    route_rows = build_route_rows(adapter_ready)
    metric_rows = build_metric_placeholder_rows()

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m02_hm3d_objectnav_adapter_smoke_ready" if adapter_ready else "e008_m02_hm3d_objectnav_adapter_smoke_blocked",
        "m01_status": m01_coverage.get("status"),
        "source_root": str(RESEARCH2_DATA_ROOT),
        "source_access": "external_read_only",
        "derived_output_root": str(DATA_OUT_DIR),
        "artifact_output_root": str(ARTIFACT_DIR),
        "habitat_image": HABITAT_IMAGE,
        "sampled_episode_rows": len(episode_rows),
        "unique_scene_rows": len(scene_rows),
        "episode_rows_scene_navmesh_ready": sum(1 for row in episode_rows if row["executable_episode_source_ready"]),
        "docker_requested_scene_count": docker_meta.get("requested_scene_count", 0),
        "docker_scene_smoke_success": docker_scene_smoke_success,
        "docker_returncode": docker_meta.get("returncode"),
        "scene_dataset_config_ready": SCENE_DATASET_CONFIG.exists(),
        "episode_source_adapter_ready": adapter_ready,
        "policy_visit_order_ready": False,
        "candidate_goal_adapter_ready": False,
        "real_navigation_sr_spl_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M03 H001 candidate-to-navigation adapter contract" if adapter_ready else "repair E008-M02 source adapter smoke",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_smoke_meta.json", docker_meta)
    write_json(ARTIFACT_DIR / "bridge_manifest.json", {"data_output_root": str(DATA_OUT_DIR), "artifact_output_root": str(ARTIFACT_DIR)})
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "metric_placeholder_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "docker_smoke_rows.jsonl", docker_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, scene_rows, docker_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "episode_adapter_rows.jsonl", episode_rows)
    write_jsonl(DATA_OUT_DIR / "scene_resolution_rows.jsonl", scene_rows)
    write_jsonl(DATA_OUT_DIR / "docker_smoke_rows.jsonl", docker_rows)
    write_jsonl(DATA_OUT_DIR / "metric_placeholder_rows.jsonl", metric_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
