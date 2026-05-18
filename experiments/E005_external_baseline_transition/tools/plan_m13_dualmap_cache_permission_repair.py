#!/usr/bin/env python3
"""Plan the E005-M13 DualMap cache-permission repair route after E005-M11."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M13_dualmap_cache_permission_repair_plan_v0"
M10_PLAN = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M10_dualmap_runtime_repair_decision_v0"
    / "detector_enabled_retry_command_plan.json"
)
M11_VERIFY = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M11_dualmap_detector_enabled_free_gpu_retry_v0"
    / "verification"
    / "coverage.json"
)
LOCAL_DATASET = ROOT / "local_dataset"
MODEL_CACHE = LOCAL_DATASET / "DualMap_model_cache"
SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
IMAGE_NAME = "research2/dualmap-smoke:latest"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def build_cache_fixed_command_plan(m10_plan: dict[str, Any]) -> dict[str, Any]:
    route_id = "E005-M14_cache_fixed_detector_retry_v0"
    output_path = LOCAL_DATASET / "DualMap_outputs" / route_id / SCAN_ID
    hydra_run_dir = LOCAL_DATASET / "DualMap_outputs" / "hydra" / route_id / SCAN_ID
    cache_mount_host = MODEL_CACHE / "mambauser_cache"
    cache_mount_container = "/home/mambauser/.cache"
    env = dict(m10_plan.get("required_env", {}))
    env.update(
        {
            "CLIP_CACHE_DIR": f"{cache_mount_container}/clip",
            "HF_HOME": str(MODEL_CACHE / "huggingface"),
            "HF_HUB_CACHE": str(MODEL_CACHE / "huggingface" / "hub"),
            "MPLCONFIGDIR": str(MODEL_CACHE / "matplotlib"),
            "TORCH_HOME": str(MODEL_CACHE / "torch"),
            "TRANSFORMERS_CACHE": str(MODEL_CACHE / "huggingface" / "transformers"),
            "ULTRALYTICS_CONFIG_DIR": str(MODEL_CACHE / "ultralytics"),
            "XDG_CACHE_HOME": str(MODEL_CACHE / "xdg"),
            "YOLO_CONFIG_DIR": str(MODEL_CACHE / "yolo"),
        }
    )
    command = list(m10_plan.get("container_command", []))
    replacements = {
        str(m10_plan.get("output_path", "")): str(output_path),
        str(m10_plan.get("hydra_run_dir", "")): str(hydra_run_dir),
    }
    command = [replacements.get(str(part), str(part)) for part in command]
    command = [
        f"output_path={output_path}" if str(part).startswith("output_path=") else str(part)
        for part in command
    ]
    command = [
        f"hydra.run.dir={hydra_run_dir}" if str(part).startswith("hydra.run.dir=") else str(part)
        for part in command
    ]
    return {
        "route_id": route_id,
        "image_name": m10_plan.get("image_name", IMAGE_NAME),
        "scan_id": SCAN_ID,
        "run_detection": True,
        "use_fastsam": True,
        "output_path": str(output_path),
        "hydra_run_dir": str(hydra_run_dir),
        "container_command": command,
        "required_env": env,
        "extra_mounts": [
            {
                "host": str(cache_mount_host),
                "container": cache_mount_container,
                "purpose": "Make the hardcoded /home/mambauser/.cache/clip path writable for YOLO-World/CLIP class embeddings.",
            }
        ],
        "expected_outputs": ["*/map/*.pkl", "*/map/layout.pcd", "*/system_time.csv"],
        "verification_hint": "If this succeeds, inspect runtime object *.pkl schema before adapter evaluation.",
    }


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route": "cache_fixed_detector_retry",
            "selected": True,
            "why": "E005-M11 failed at /home/mambauser/.cache/clip permission during detector initialization.",
            "claim_boundary": "Runtime smoke only; no performance claim before output verification and schema inspection.",
        },
        {
            "rank": 2,
            "route": "cache_fixed_fastsam_disabled_retry",
            "selected": False,
            "why": "Use if cache-fixed default detector retry reaches SAM/YOLO but FastSAM remains a resource or model blocker.",
            "claim_boundary": "Configuration variant, not faithful default DualMap.",
        },
        {
            "rank": 3,
            "route": "loader_only_layout_smoke",
            "selected": False,
            "why": "Use if detector initialization remains blocked; tests dataset/layout compatibility only.",
            "claim_boundary": "No object map or open-vocabulary baseline evidence.",
        },
        {
            "rank": 4,
            "route": "conceptgraphs_fallback",
            "selected": False,
            "why": "Use only after bounded DualMap runtime repairs fail.",
            "claim_boundary": "Fallback external mapping baseline, not DualMap evidence.",
        },
    ]


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M13 DualMap Cache Permission Repair Plan",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- E005-M11 verifier status: `{coverage['m11_status']}`.",
        f"- E005-M11 failure signals: {', '.join(coverage['m11_failure_signals'])}.",
        f"- YOLO-World model cache exists: {str(coverage['yolo_model_exists']).lower()}.",
        f"- YOLO-World model size bytes: {coverage['yolo_model_size_bytes']}.",
        f"- Repair host cache mount: `{coverage['cache_mount_host']}`.",
        f"- Repair container cache mount: `{coverage['cache_mount_container']}`.",
        "",
        "## Decision",
        "",
        "- Selected next route: `cache_fixed_detector_retry`.",
        "- Repair principle: mount a writable host cache at `/home/mambauser/.cache` and set explicit CLIP/HF/Ultralytics cache env vars.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['route']}`: rank {row['rank']}, selected {str(row['selected']).lower()}; {row['why']}")
    lines.extend(
        [
            "",
            "## Paper Claim Boundary",
            "",
            "- E005-M13 is a repair plan, not a baseline result.",
            "- `DualMap` external baseline evidence remains blocked until runtime object `*.pkl`, `layout.pcd`, and `system_time.csv` are produced and inspected.",
            "- If this route fails, use loader-only layout smoke or lower-memory detector configuration before switching to `ConceptGraphs`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    m10_plan = read_json(M10_PLAN)
    m11_verify = read_json(M11_VERIFY)
    yolo_model = MODEL_CACHE / "model" / "yolov8l-world.pt"
    cache_mount_host = MODEL_CACHE / "mambauser_cache"
    cache_mount_host.mkdir(parents=True, exist_ok=True)
    (cache_mount_host / "clip").mkdir(parents=True, exist_ok=True)
    plan = build_cache_fixed_command_plan(m10_plan)
    rows = route_rows()
    coverage = {
        "status": "e005_m13_dualmap_cache_permission_repair_plan_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m11_status": m11_verify.get("status", "missing"),
        "m11_failure_signals": m11_verify.get("failure_signals", []),
        "m11_output_inventory": m11_verify.get("output_inventory", {}),
        "yolo_model_exists": yolo_model.exists(),
        "yolo_model_size_bytes": yolo_model.stat().st_size if yolo_model.exists() else 0,
        "cache_mount_host": plan["extra_mounts"][0]["host"],
        "cache_mount_container": plan["extra_mounts"][0]["container"],
        "selected_route": "cache_fixed_detector_retry",
        "next_recommended_unit": "E005-M14 DualMap cache-fixed detector retry launch",
        "command_plan": str(OUT_DIR / "cache_fixed_detector_retry_command_plan.json"),
    }
    decision = {
        "status": coverage["status"],
        "decision": "cache_fixed_detector_retry",
        "route_order": [row["route"] for row in rows],
        "next_action": coverage["next_recommended_unit"],
        "claim_boundary": [
            "No DualMap performance claim from E005-M13.",
            "Cache-fixed retry must still produce runtime outputs and pass schema inspection.",
        ],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_json(OUT_DIR / "cache_fixed_detector_retry_command_plan.json", plan)
    write_jsonl(OUT_DIR / "route_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
