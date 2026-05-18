#!/usr/bin/env python3
"""Plan the E005-M10 DualMap runtime blocker repair/relaunch route."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M10_dualmap_runtime_repair_decision_v0"
M08_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M08_dualmap_one_scan_runtime_smoke_v0"
M08_VERIFY = M08_OUT_DIR / "verification" / "coverage.json"

LOCAL_DATASET = ROOT / "local_dataset"
SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
STAGED_ROOT = LOCAL_DATASET / "DualMap_staged" / "3rscan_scannet_exported"
STAGED_DATASET_PATH = STAGED_ROOT / "scannet"
STAGED_CONFIG = STAGED_ROOT / "config" / "dualmap_3rscan_scannet.yaml"
IMAGE_NAME = "research2/dualmap-smoke:latest"
FREE_GPU_RETRY_MIN_MIB = 24_000


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def gpu_snapshot() -> dict[str, Any]:
    query = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ]
    )
    processes = run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ]
    )
    gpus: list[dict[str, Any]] = []
    if query["ok"]:
        for row in query["stdout"].splitlines():
            parts = [part.strip() for part in row.split(",")]
            if len(parts) != 4:
                continue
            name, total, used, free = parts
            gpus.append(
                {
                    "name": name,
                    "memory_total_mib": int(total),
                    "memory_used_mib": int(used),
                    "memory_free_mib": int(free),
                }
            )
    return {
        "gpu_query": query,
        "gpus": gpus,
        "compute_process_query": processes,
        "compute_process_stdout": processes["stdout"],
    }


def staged_counts() -> dict[str, Any]:
    scene_dir = STAGED_DATASET_PATH / "exported" / SCAN_ID
    return {
        "scene_dir": str(scene_dir),
        "config_exists": STAGED_CONFIG.exists(),
        "color": len(list((scene_dir / "color").glob("*.jpg"))) if scene_dir.exists() else 0,
        "depth": len(list((scene_dir / "depth").glob("*.png"))) if scene_dir.exists() else 0,
        "pose": len(list((scene_dir / "pose").glob("*.txt"))) if scene_dir.exists() else 0,
        "intrinsic_depth_exists": (scene_dir / "intrinsic" / "intrinsic_depth.txt").exists(),
    }


def build_runtime_overrides(output_path: Path, hydra_run_dir: Path, *, run_detection: bool) -> list[str]:
    overrides = [
        "dataset_name=scannet",
        f"scene_id={SCAN_ID}",
        f"dataset_path={STAGED_DATASET_PATH}",
        f"dataset_conf_path={STAGED_CONFIG}",
        f"output_path={output_path}",
        "use_rerun=false",
        "run_local_mapping_only=true",
        "use_parallel=false",
        "stride=20",
        "save_layout=true",
        "save_global_map=false",
        "hydra.job.chdir=false",
        f"hydra.run.dir={hydra_run_dir}",
    ]
    if run_detection:
        overrides.extend(["run_detection=true", "save_local_map=true", "use_fastsam=true"])
    else:
        overrides.extend(["run_detection=false", "save_local_map=false", "use_fastsam=false"])
    return overrides


def command_plan(*, route_id: str, run_detection: bool) -> dict[str, Any]:
    output_path = LOCAL_DATASET / "DualMap_outputs" / route_id / SCAN_ID
    hydra_run_dir = LOCAL_DATASET / "DualMap_outputs" / "hydra" / route_id / SCAN_ID
    overrides = build_runtime_overrides(output_path, hydra_run_dir, run_detection=run_detection)
    container_command = [
        "/opt/conda/envs/dualmap/bin/python",
        "-m",
        "applications.runner_dataset",
        *overrides,
    ]
    return {
        "route_id": route_id,
        "run_detection": run_detection,
        "image_name": IMAGE_NAME,
        "scan_id": SCAN_ID,
        "output_path": str(output_path),
        "hydra_run_dir": str(hydra_run_dir),
        "container_command": container_command,
        "required_env": {
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
            "HOME": str(LOCAL_DATASET / "DualMap_runtime_home"),
            "HF_HOME": str(LOCAL_DATASET / "DualMap_model_cache" / "huggingface"),
            "TORCH_HOME": str(LOCAL_DATASET / "DualMap_model_cache" / "torch"),
            "XDG_CACHE_HOME": str(LOCAL_DATASET / "DualMap_model_cache" / "xdg"),
            "ULTRALYTICS_CONFIG_DIR": str(LOCAL_DATASET / "DualMap_model_cache" / "ultralytics"),
            "YOLO_CONFIG_DIR": str(LOCAL_DATASET / "DualMap_model_cache" / "yolo"),
            "MPLCONFIGDIR": str(LOCAL_DATASET / "DualMap_model_cache" / "matplotlib"),
        },
        "expected_outputs": (
            ["*/map/*.pkl", "*/map/layout.pcd", "*/system_time.csv"]
            if run_detection
            else ["*/map/layout.pcd", "*/system_time.csv"]
        ),
        "verification_hint": (
            "Detector-enabled retry must inspect object *.pkl schema before adapter evaluation."
            if run_detection
            else "Loader-only layout smoke cannot support object-map baseline claims."
        ),
    }


def build_routes(m08: dict[str, Any], gpu: dict[str, Any]) -> list[dict[str, Any]]:
    signals = set(m08.get("failure_signals", []))
    free_mib = max((gpu_info["memory_free_mib"] for gpu_info in gpu.get("gpus", [])), default=0)
    oom_failure = "cuda_out_of_memory" in signals or "clip_model_init_failed" in signals
    enough_gpu_now = free_mib >= FREE_GPU_RETRY_MIN_MIB

    rows = [
        {
            "route": "detector_enabled_free_gpu_retry",
            "rank": 1 if oom_failure and enough_gpu_now else 2,
            "score": 50 if oom_failure and enough_gpu_now else 38,
            "selected": bool(oom_failure and enough_gpu_now),
            "what_it_tests": "Official-ish DualMap one-scan runtime with CLIP, YOLO, SAM/FastSAM and map serialization.",
            "why": (
                "Previous failure was GPU contention during detector initialization, and the current GPU snapshot "
                f"has {free_mib} MiB free, above the {FREE_GPU_RETRY_MIN_MIB} MiB retry threshold."
                if oom_failure and enough_gpu_now
                else "Use after GPU memory is available; this is the route needed for object-map baseline evidence."
            ),
            "expected_output": "object *.pkl, layout.pcd, system_time.csv",
            "claim_boundary": "Still a one-scan smoke; no performance claim until schema inspection and E004 adapter evaluation.",
        },
        {
            "route": "loader_only_layout_smoke",
            "rank": 2 if oom_failure and enough_gpu_now else 1,
            "score": 41 if oom_failure and enough_gpu_now else 45,
            "selected": bool(oom_failure and not enough_gpu_now),
            "what_it_tests": "Dataset loader, RGB-D/depth/pose/intrinsic compatibility, layout point-cloud save path.",
            "why": (
                "Use as fallback if detector-enabled retry blocks again, or if GPU memory becomes unavailable."
            ),
            "expected_output": "layout.pcd and timing files only",
            "claim_boundary": "No object map, no open-vocabulary baseline, no search-policy comparison.",
        },
        {
            "route": "lower_memory_detector_retry",
            "rank": 3,
            "score": 34,
            "selected": False,
            "what_it_tests": "Detector-enabled DualMap with reduced memory pressure after default free-GPU retry fails.",
            "why": "Potential knobs include lower frame stride, smaller detector options, disabling FastSAM, and explicit CUDA allocator settings.",
            "expected_output": "object *.pkl if detector modules initialize",
            "claim_boundary": "Must be labeled as a configuration variant, not a faithful default DualMap run.",
        },
        {
            "route": "conceptgraphs_fallback",
            "rank": 4,
            "score": 31,
            "selected": False,
            "what_it_tests": "Alternative open-vocabulary graph mapping baseline over posed RGB-D scans.",
            "why": "Use only if DualMap remains blocked after bounded detector retry and loader/layout compatibility checks.",
            "expected_output": "ConceptGraphs object/graph artifacts after a separate interface audit.",
            "claim_boundary": "Fallback baseline route; cannot be described as DualMap evidence.",
        },
    ]
    return sorted(rows, key=lambda row: (row["rank"], -row["score"]))


def build_report(coverage: dict[str, Any], routes: list[dict[str, Any]]) -> str:
    selected = next((route for route in routes if route["selected"]), routes[0])
    gpu_infos = coverage["gpu_snapshot"].get("gpus", [])
    free_text = ", ".join(
        f"{gpu['name']}: {gpu['memory_free_mib']} / {gpu['memory_total_mib']} MiB free"
        for gpu in gpu_infos
    ) or "unavailable"
    lines = [
        "# E005-M10 DualMap Runtime Repair Decision",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Previous runtime verifier status: `{coverage['m08_status']}`.",
        f"- Previous failure signals: {', '.join(coverage['m08_failure_signals'])}.",
        f"- Current GPU snapshot: {free_text}.",
        f"- Staged scan counts: color {coverage['staged_counts']['color']}, depth {coverage['staged_counts']['depth']}, pose {coverage['staged_counts']['pose']}.",
        f"- Docker image: `{IMAGE_NAME}`.",
        "",
        "## Decision",
        "",
        f"- Selected next route: `{selected['route']}`.",
        f"- Reason: {selected['why']}",
        "- Do not stop unrelated GPU processes without explicit user approval.",
        "",
        "## Route Ranking",
        "",
    ]
    for route in routes:
        lines.append(
            f"- `{route['route']}`: rank {route['rank']}, score {route['score']}, selected {str(route['selected']).lower()}; {route['what_it_tests']}"
        )
    lines.extend(
        [
            "",
            "## Paper Claim Boundary",
            "",
            "- E005-M10 is a repair/relaunch decision artifact, not a method result.",
            "- A detector-enabled retry can only become baseline evidence after object `*.pkl` schema inspection and E004-compatible adapter evaluation.",
            "- A loader-only layout smoke only supports dataset/runtime compatibility, not object search or open-vocabulary mapping performance.",
            "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
            "",
            "## User Decision Needed",
            "",
            "- None before the next bounded relaunch unit.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    m08_verify = read_json(M08_VERIFY)
    launch = read_json(M08_OUT_DIR / "coverage.json")
    gpu = gpu_snapshot()
    counts = staged_counts()
    routes = build_routes(m08_verify, gpu)
    selected = next((route for route in routes if route["selected"]), routes[0])

    detector_plan = command_plan(route_id="E005-M11_detector_enabled_free_gpu_retry_v0", run_detection=True)
    loader_plan = command_plan(route_id="E005-M11_loader_only_layout_smoke_v0", run_detection=False)

    coverage = {
        "status": "e005_m10_dualmap_runtime_repair_decision_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m08_status": m08_verify.get("status", "missing"),
        "m08_background_status": m08_verify.get("background_status", {}),
        "m08_failure_signals": m08_verify.get("failure_signals", []),
        "m08_output_inventory": m08_verify.get("output_inventory", {}),
        "m08_launch_output_path": launch.get("output_path", ""),
        "gpu_snapshot": gpu,
        "staged_counts": counts,
        "free_gpu_retry_min_mib": FREE_GPU_RETRY_MIN_MIB,
        "selected_route": selected["route"],
        "next_recommended_unit": (
            "E005-M11 DualMap detector-enabled free-GPU retry launch"
            if selected["route"] == "detector_enabled_free_gpu_retry"
            else "E005-M11 DualMap detection-disabled loader/layout smoke launch"
        ),
        "dualmap_image": IMAGE_NAME,
        "detector_enabled_retry_plan": str(OUT_DIR / "detector_enabled_retry_command_plan.json"),
        "loader_only_layout_plan": str(OUT_DIR / "loader_only_layout_command_plan.json"),
    }

    decision = {
        "decision": selected["route"],
        "status": coverage["status"],
        "selected_route": selected,
        "route_order": [route["route"] for route in routes],
        "claim_boundary": [
            "No DualMap performance claim from E005-M10.",
            "Detector-enabled rerun is required before object-map baseline adapter work.",
            "Loader-only layout smoke is compatibility evidence only.",
            "ConceptGraphs remains fallback, not immediate replacement.",
        ],
        "next_action": coverage["next_recommended_unit"],
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_jsonl(OUT_DIR / "route_rows.jsonl", routes)
    write_json(OUT_DIR / "detector_enabled_retry_command_plan.json", detector_plan)
    write_json(OUT_DIR / "loader_only_layout_command_plan.json", loader_plan)
    write_text(OUT_DIR / "report.md", build_report(coverage, routes))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
