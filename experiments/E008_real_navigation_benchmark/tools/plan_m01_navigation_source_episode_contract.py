#!/usr/bin/env python3
"""Plan E008-M01 real navigation source and episode contract."""

from __future__ import annotations

import gzip
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
OUT_DIR = EXP_ROOT / "artifacts" / "E008-M01_navigation_source_episode_contract_v0"
VERSION = "e008_m01_navigation_source_episode_contract_v0"

E007_M07_DIR = ROOT / "experiments" / "E007_navigation_path_cost_bridge" / "artifacts" / "E007-M07_bridge_table_package_navigation_decision_v0"
RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HM3D_ROOT = RESEARCH2_DATA_ROOT / "versioned_data" / "hm3d-0.2"
HM3D_SCENE_ROOT = HM3D_ROOT / "hm3d"
OBJECTNAV_ROOT = RESEARCH2_DATA_ROOT / "datasets" / "objectnav" / "hm3d" / "v2" / "objectnav_hm3d_v2"
DERIVED_NAV_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge"

HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
VLMAPS_IMAGE = "research2/vlmaps-hm3d:20260508-timmfix"


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


def run_command(cmd: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # pragma: no cover - preflight should keep moving.
        return {"returncode": None, "stdout": "", "stderr": str(exc), "ok": False}


def docker_image_ready(image: str) -> bool:
    return run_command(["docker", "image", "inspect", image], timeout_s=10)["ok"]


def habitat_import_ready() -> dict[str, Any]:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        (
            "micromamba run -n base python - <<'PY'\n"
            "import importlib.util\n"
            "mods = ['habitat_sim', 'habitat', 'magnum', 'numpy']\n"
            "missing = [m for m in mods if importlib.util.find_spec(m) is None]\n"
            "print('missing=' + ','.join(missing))\n"
            "raise SystemExit(1 if missing else 0)\n"
            "PY"
        ),
    ]
    result = run_command(cmd, timeout_s=30)
    return {
        "image": HABITAT_IMAGE,
        "image_ready": docker_image_ready(HABITAT_IMAGE),
        "import_ready": result["ok"],
        "import_stdout": result["stdout"],
        "import_stderr_tail": result["stderr"][-500:],
    }


def count_files(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob(pattern))


def split_scene_counts() -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for split in ["train", "val", "minival"]:
        split_root = HM3D_SCENE_ROOT / split
        counts[split] = {
            "scene_dirs": sum(1 for p in split_root.iterdir() if p.is_dir()) if split_root.exists() else 0,
            "glb_files": count_files(split_root, "*.glb"),
            "navmesh_files": count_files(split_root, "*.navmesh"),
            "semantic_config_files": count_files(split_root, "*semantic*"),
        }
    return counts


def count_objectnav_episodes(split: str) -> dict[str, Any]:
    split_root = OBJECTNAV_ROOT / split
    content_root = split_root / "content"
    gz_files = sorted(content_root.glob("*.json.gz")) if content_root.exists() else []
    aggregate = split_root / f"{split}.json.gz"
    total_episodes = 0
    sample_files = gz_files[:5]
    parse_errors: list[str] = []
    for path in gz_files:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
            total_episodes += len(payload.get("episodes", [])) if isinstance(payload, dict) else 0
        except Exception as exc:  # pragma: no cover - corrupted file accounting.
            parse_errors.append(f"{path.name}: {exc}")
    return {
        "split": split,
        "aggregate_file_ready": aggregate.exists(),
        "content_json_gz_files": len(gz_files),
        "episode_rows": total_episodes,
        "sample_files": [p.name for p in sample_files],
        "parse_error_count": len(parse_errors),
        "parse_error_samples": parse_errors[:3],
    }


def build_source_rows(habitat_runtime: dict[str, Any], scene_counts: dict[str, dict[str, int]], objectnav_counts: dict[str, Any]) -> list[dict[str, Any]]:
    hm3d_data_ready = HM3D_ROOT.exists() and scene_counts["minival"]["navmesh_files"] > 0 and objectnav_counts["content_json_gz_files"] > 0
    hm3d_runtime_ready = habitat_runtime["image_ready"] and habitat_runtime["import_ready"]
    return [
        {
            "source_id": "hm3d_objectnav_habitat_local_research2",
            "source_type": "real_navigation_simulator_source",
            "dataset": "HM3D ObjectNav v2",
            "simulator": "Habitat",
            "source_root": str(RESEARCH2_DATA_ROOT),
            "source_access": "external_read_only",
            "derived_output_root": str(DERIVED_NAV_ROOT),
            "scene_counts": scene_counts,
            "objectnav_val_mini": objectnav_counts,
            "docker_image": HABITAT_IMAGE,
            "docker_import_ready": hm3d_runtime_ready,
            "data_ready": hm3d_data_ready,
            "selected_first_source": hm3d_data_ready and hm3d_runtime_ready,
            "claim_boundary": (
                "Supports real navigation source preflight, but not stale-memory dynamics until H001 state "
                "injection and candidate adapter are implemented."
            ),
        },
        {
            "source_id": "3rscan_occupancy_grid_astar_proxy",
            "source_type": "proxy_navigation_source",
            "dataset": "3RScan / 3DSSG",
            "simulator": "none",
            "source_root": str(ROOT / "local_dataset" / "3RScan"),
            "source_access": "local_research2",
            "derived_output_root": str(ROOT / "experiments" / "E007_navigation_path_cost_bridge" / "artifacts"),
            "data_ready": E007_M07_DIR.exists(),
            "docker_import_ready": False,
            "selected_first_source": False,
            "claim_boundary": "Already used as E007 occupancy-grid path-cost proxy; not real navigation `SR` / `SPL`.",
        },
        {
            "source_id": "hm3d_ovon_goat_vlfm_later_route",
            "source_type": "standard_open_vocab_navigation_baseline_route",
            "dataset": "HM3D-OVON / GOAT-Bench",
            "simulator": "Habitat",
            "source_root": "",
            "source_access": "not_staged_in_research2",
            "derived_output_root": str(DERIVED_NAV_ROOT),
            "data_ready": False,
            "docker_import_ready": docker_image_ready(VLMAPS_IMAGE),
            "selected_first_source": False,
            "claim_boundary": "Important later baseline route, but E008-M01 selects the already staged HM3D ObjectNav preflight first.",
        },
        {
            "source_id": "isaac_lab_navigation_later_route",
            "source_type": "robotics_simulator_route",
            "dataset": "custom",
            "simulator": "Isaac Lab / Isaac Sim",
            "source_root": "",
            "source_access": "docker_image_only",
            "derived_output_root": str(DERIVED_NAV_ROOT),
            "data_ready": False,
            "docker_import_ready": docker_image_ready("isaac-lab-ros2-nav:latest"),
            "selected_first_source": False,
            "claim_boundary": "Useful for robotics deployment later, but no E008 benchmark/episode adapter exists yet.",
        },
    ]


def build_episode_schema_rows() -> list[dict[str, Any]]:
    fields = [
        ("episode_id", "string", "Unique navigation episode id.", True),
        ("scene_id", "string", "`HM3D` scene id or dynamic-memory source id.", True),
        ("split", "string", "train/val/minival/heldout split id.", True),
        ("start_position", "float[3]", "Agent start position from simulator episode.", True),
        ("start_rotation", "float[4]", "Agent start orientation from simulator episode.", True),
        ("goal_object_category", "string", "Target object/category query.", True),
        ("goal_object_id_or_region", "string", "Simulator target object id or goal region id when available.", False),
        ("task_context_id", "string", "Structured task context used by H001 memory trust and budget policy.", True),
        ("stale_memory_candidates", "list", "Old-memory candidate locations and confidence/trust features.", True),
        ("current_observation_candidates", "list", "Detector/mapper/current observation candidates.", True),
        ("policy_visit_order", "list", "Ordered candidate visits emitted by baseline or H001 policy.", True),
        ("success_distance_m", "float", "Navigation success threshold, fixed before execution.", True),
        ("max_steps_or_time", "int", "Execution budget, fixed before execution.", True),
    ]
    return [
        {
            "field": field,
            "type": typ,
            "description": desc,
            "required_for_e008_m02": required,
            "blocked_from_policy_input": False,
        }
        for field, typ, desc, required in fields
    ]


def build_metric_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "SR",
            "role": "primary_after_execution",
            "definition": "Episode success under fixed success distance and execution budget.",
            "ready_now": False,
            "blocked_until": "Habitat episode adapter and policy execution exist.",
        },
        {
            "metric": "SPL",
            "role": "primary_after_execution",
            "definition": "Success weighted by shortest-path distance over executed path length.",
            "ready_now": False,
            "blocked_until": "Shortest path and executed trajectory are available from Habitat.",
        },
        {
            "metric": "ExpectedSearchCost",
            "role": "bridge_consistency",
            "definition": "Candidate visit cost before execution; used to compare with E007 proxy.",
            "ready_now": True,
            "blocked_until": "",
        },
        {
            "metric": "PathAttemptSPLProxy",
            "role": "proxy_only",
            "definition": "E007 occupancy-grid path proxy; must not be reported as real `SPL`.",
            "ready_now": True,
            "blocked_until": "",
        },
        {
            "metric": "OldLocationDeadEndCostM",
            "role": "secondary_after_execution",
            "definition": "Executed path cost spent visiting stale old-memory locations that are not the target.",
            "ready_now": False,
            "blocked_until": "Start pose and executed candidate-visit trajectories are fixed.",
        },
        {
            "metric": "FailureType",
            "role": "failure_analysis",
            "definition": "Separate no-path, collision/timeout, wrong candidate, detector miss, stale-memory dead end, and source-adapter mismatch.",
            "ready_now": False,
            "blocked_until": "E008-M02 adapter smoke defines executable episode rows.",
        },
    ]


def build_baseline_rows() -> list[dict[str, Any]]:
    return [
        ("real_static_memory_only_v0", "old-memory only candidate visit order", "E007 comparable baseline"),
        ("real_detector_confidence_top5_v0", "detector-confidence current candidates first", "E007 comparable baseline"),
        ("conceptgraphs_only_strict_top5_v0", "`ConceptGraphs` map retrieval candidates only", "E007 comparable baseline"),
        ("real_context_agnostic_memory_trust_reobserve_v0", "memory trust without structured task context", "task-context ablation"),
        ("h001_real_task_context_memory_trust_v0", "H001 task-conditioned memory trust and re-observation", "core method row"),
        ("h001_then_conceptgraphs_top5_on_observed_miss_v0", "H001 plus `ConceptGraphs` fallback on observed miss", "map-assisted repair tradeoff row"),
        ("oracle_goal_shortest_path_v0", "shortest-path upper bound to known goal", "execution sanity upper bound only; not a policy baseline"),
    ]
    return [
        {
            "baseline_id": baseline_id,
            "description": description,
            "role": role,
            "allowed_inputs": "Same pre-execution candidate rows and task context contract as H001, except oracle upper bound.",
            "blocked_inputs": "Ground-truth goal position, success label, target rank, and shortest path before policy ranking.",
        }
        for baseline_id, description, role in [
            ("real_static_memory_only_v0", "old-memory only candidate visit order", "E007 comparable baseline"),
            ("real_detector_confidence_top5_v0", "detector-confidence current candidates first", "E007 comparable baseline"),
            ("conceptgraphs_only_strict_top5_v0", "`ConceptGraphs` map retrieval candidates only", "E007 comparable baseline"),
            ("real_context_agnostic_memory_trust_reobserve_v0", "memory trust without structured task context", "task-context ablation"),
            ("h001_real_task_context_memory_trust_v0", "H001 task-conditioned memory trust and re-observation", "core method row"),
            ("h001_then_conceptgraphs_top5_on_observed_miss_v0", "H001 plus `ConceptGraphs` fallback on observed miss", "map-assisted repair tradeoff row"),
            ("oracle_goal_shortest_path_v0", "shortest-path upper bound to known goal", "execution sanity upper bound only; not a policy baseline"),
        ]
    ]


def build_input_contract_rows() -> list[dict[str, Any]]:
    return [
        {"field": "task_context_id", "policy_input": "allowed", "reason": "Structured task context conditions memory trust and budget."},
        {"field": "stale_memory_candidate_features", "policy_input": "allowed", "reason": "Core semantic memory evidence."},
        {"field": "current_observation_candidate_features", "policy_input": "allowed", "reason": "Real proposal/map evidence available before action."},
        {"field": "candidate_path_cost_estimate", "policy_input": "allowed", "reason": "Allowed if computed before execution from known map/source."},
        {"field": "goal_object_category", "policy_input": "allowed", "reason": "The query is the task."},
        {"field": "ground_truth_goal_position", "policy_input": "blocked", "reason": "Evaluation-only field."},
        {"field": "shortest_path_to_goal", "policy_input": "blocked", "reason": "Metric-only field before oracle upper bound."},
        {"field": "success_label", "policy_input": "blocked", "reason": "Evaluation leakage."},
        {"field": "target_rank_or_match_distance", "policy_input": "blocked", "reason": "Post-hoc matching leakage."},
    ]


def build_route_rows(selected_source_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "e008_m02_hm3d_objectnav_episode_adapter_smoke",
            "selected": selected_source_ready,
            "decision": "selected_next" if selected_source_ready else "blocked_until_source_ready",
            "next_unit": "E008-M02 HM3D ObjectNav episode/source adapter smoke",
            "launch_long_job_now": False,
            "reason": "Local read-only HM3D ObjectNav data and Habitat Docker runtime are enough for a bounded adapter smoke, not a full benchmark run.",
        },
        {
            "rank": 2,
            "route_id": "e008_full_navigation_execution_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "E008-M03 or later policy execution",
            "launch_long_job_now": False,
            "reason": "Need E008-M02 adapter rows before simulator execution can be a paper-table command.",
        },
        {
            "rank": 3,
            "route_id": "3rscan_real_navigation_adapter_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "3RScan simulator/navmesh adapter",
            "launch_long_job_now": False,
            "reason": "Current 3RScan route has PLY/occupancy grids but no simulator/navmesh source for real `SR` / `SPL`.",
        },
    ]


def build_next_action_rows(selected_source_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "task": "E008-M02 HM3D ObjectNav episode/source adapter smoke",
            "status": "ready_to_start" if selected_source_ready else "blocked",
            "action": "Load a tiny `val_mini` episode subset in Docker, verify scene/navmesh resolution, and write executable episode rows without launching a full benchmark.",
        },
        {
            "order": 2,
            "task": "E008-M03 H001 candidate-to-navigation adapter contract",
            "status": "pending",
            "action": "Map E007 policy visit orders to Habitat candidate goals and preserve blocked-input rules.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(coverage: dict[str, Any], source_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    source_summary = [
        {
            "source_id": row["source_id"],
            "data_ready": row["data_ready"],
            "docker_import_ready": row["docker_import_ready"],
            "selected": row["selected_first_source"],
            "boundary": row["claim_boundary"],
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
        "# E008-M01 Navigation Source And Episode Contract\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Selected source: `{coverage['selected_source']}`.\n"
        f"- Habitat import ready: {str(coverage['habitat_import_ready']).lower()}.\n"
        f"- HM3D minival navmesh files: {coverage['hm3d_minival_navmesh_files']}.\n"
        f"- ObjectNav `val_mini` content files: {coverage['objectnav_val_mini_content_files']}.\n"
        f"- ObjectNav `val_mini` parsed episode rows: {coverage['objectnav_val_mini_episode_rows']}.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n"
        f"- Launch long job now: {str(coverage['launch_long_job_now']).lower()}.\n\n"
        "## Source Preflight\n\n"
        + markdown_table(source_summary, ["source_id", "data_ready", "docker_import_ready", "selected", "boundary"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M01 selects a real navigation source and episode contract only.\n"
        "- E008-M01 does not claim real navigation `SR` / `SPL`.\n"
        "- `3RScan` / `3DSSG` remains the dynamic stale-memory source; `HM3D ObjectNav` is the first executable navigation-source route.\n"
        "- Any future `HM3D ObjectNav` result must be written as navigation-source transfer/adapter evidence unless stale-memory state injection is explicitly implemented.\n\n"
        "## Agent Inference\n\n"
        "- The local environment is sufficient for an E008-M02 adapter smoke because HM3D scene/navmesh data and Habitat Docker import are ready.\n"
        "- A full navigation run should not be launched until adapter rows, allowed inputs, metrics, and baselines are frozen.\n"
        "- The most defensible next step is a tiny `val_mini` adapter smoke, not another proxy metric table.\n"
    )


def main() -> None:
    e007_coverage = read_json(E007_M07_DIR / "coverage.json")
    scene_counts = split_scene_counts()
    objectnav_val_mini = count_objectnav_episodes("val_mini")
    habitat_runtime = habitat_import_ready()
    source_rows = build_source_rows(habitat_runtime, scene_counts, objectnav_val_mini)
    selected = next((row for row in source_rows if row["selected_first_source"]), None)
    selected_source = selected["source_id"] if selected else "none"
    selected_source_ready = selected is not None

    episode_rows = build_episode_schema_rows()
    metric_rows = build_metric_rows()
    baseline_rows = build_baseline_rows()
    input_rows = build_input_contract_rows()
    route_rows = build_route_rows(selected_source_ready)
    next_rows = build_next_action_rows(selected_source_ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m01_navigation_source_episode_contract_ready" if selected_source_ready else "e008_m01_navigation_source_episode_contract_blocked",
        "e007_status": e007_coverage.get("status"),
        "selected_source": selected_source,
        "hm3d_root": str(HM3D_ROOT),
        "objectnav_root": str(OBJECTNAV_ROOT),
        "derived_navigation_root": str(DERIVED_NAV_ROOT),
        "habitat_image": HABITAT_IMAGE,
        "habitat_image_ready": habitat_runtime["image_ready"],
        "habitat_import_ready": habitat_runtime["import_ready"],
        "hm3d_minival_navmesh_files": scene_counts["minival"]["navmesh_files"],
        "hm3d_total_navmesh_files": sum(split["navmesh_files"] for split in scene_counts.values()),
        "hm3d_total_glb_files": sum(split["glb_files"] for split in scene_counts.values()),
        "objectnav_val_mini_content_files": objectnav_val_mini["content_json_gz_files"],
        "objectnav_val_mini_episode_rows": objectnav_val_mini["episode_rows"],
        "real_navigation_sr_spl_ready": False,
        "old_location_dead_end_cost_primary_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": "E008-M02 HM3D ObjectNav episode/source adapter smoke" if selected_source_ready else "source repair before E008-M02",
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "summary.json", {"coverage": coverage, "habitat_runtime": habitat_runtime})
    write_jsonl(OUT_DIR / "source_preflight_rows.jsonl", source_rows)
    write_jsonl(OUT_DIR / "episode_schema_rows.jsonl", episode_rows)
    write_jsonl(OUT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(OUT_DIR / "baseline_contract_rows.jsonl", baseline_rows)
    write_jsonl(OUT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(OUT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(OUT_DIR / "next_action_rows.jsonl", next_rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, source_rows, route_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
