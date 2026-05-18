#!/usr/bin/env python3
"""Diagnose E005-M14 DualMap missing object outputs and plan a bounded retry."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M16_dualmap_object_output_diagnosis_v0"
M13_PLAN = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M13_dualmap_cache_permission_repair_plan_v0"
    / "cache_fixed_detector_retry_command_plan.json"
)
M14_VERIFY = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M14_dualmap_cache_fixed_detector_retry_v0"
    / "verification"
    / "coverage.json"
)
LOCAL_DATASET = ROOT / "local_dataset"
SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
M17_ROUTE_ID = "E005-M17_denser_stride_object_retry_v0"


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def int_from_regex(text: str, pattern: str, default: int = 0) -> int:
    match = re.search(pattern, text)
    if not match:
        return default
    return int(match.group(1))


def list_ints_from_regex(text: str, pattern: str) -> list[int]:
    return [int(match) for match in re.findall(pattern, text)]


def replace_command_parts(command: list[str], *, route_id: str, stride: int) -> list[str]:
    output_path = LOCAL_DATASET / "DualMap_outputs" / route_id / SCAN_ID
    hydra_run_dir = LOCAL_DATASET / "DualMap_outputs" / "hydra" / route_id / SCAN_ID
    new_command: list[str] = []
    for part in command:
        if part.startswith("output_path="):
            new_command.append(f"output_path={output_path}")
        elif part.startswith("hydra.run.dir="):
            new_command.append(f"hydra.run.dir={hydra_run_dir}")
        elif part.startswith("stride="):
            new_command.append(f"stride={stride}")
        else:
            new_command.append(part)
    return new_command


def build_denser_stride_plan(base_plan: dict[str, Any]) -> dict[str, Any]:
    output_path = LOCAL_DATASET / "DualMap_outputs" / M17_ROUTE_ID / SCAN_ID
    hydra_run_dir = LOCAL_DATASET / "DualMap_outputs" / "hydra" / M17_ROUTE_ID / SCAN_ID
    return {
        "route_id": M17_ROUTE_ID,
        "image_name": base_plan.get("image_name", "research2/dualmap-smoke:latest"),
        "scan_id": SCAN_ID,
        "output_path": str(output_path),
        "hydra_run_dir": str(hydra_run_dir),
        "container_command": replace_command_parts(
            [str(part) for part in base_plan.get("container_command", [])],
            route_id=M17_ROUTE_ID,
            stride=5,
        ),
        "required_env": base_plan.get("required_env", {}),
        "extra_mounts": base_plan.get("extra_mounts", []),
        "expected_outputs": ["*/map/*.pkl", "*/map/layout.pcd", "*/system_time.csv", "*/detector_time.csv"],
        "repair_principle": "Keep the official stability threshold but process denser RGB-D keyframes so local objects can survive end_process.",
        "configuration_delta_from_m14": {
            "stride": {"from": 20, "to": 5},
            "stable_num": {"from": 8, "to": 8},
            "run_detection": True,
            "use_fastsam": True,
            "run_local_mapping_only": True,
        },
    }


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route": "denser_stride_default_stability_retry",
            "selected": True,
            "why": "M14 processed only 5 keyframes while DualMap requires stable_num=8 before objects can persist through end_process.",
            "claim_boundary": "Faithful runtime repair; still only one-scan smoke until object schema and adapter evaluation pass.",
        },
        {
            "rank": 2,
            "route": "diagnostic_lower_stable_num_retry",
            "selected": False,
            "why": "Use only if denser stride still produces no object pkl; lowering stable_num changes DualMap behavior more strongly.",
            "claim_boundary": "Diagnostic configuration, not a faithful external baseline result.",
        },
        {
            "rank": 3,
            "route": "conceptgraphs_fallback",
            "selected": False,
            "why": "Use if bounded DualMap output repairs cannot produce inspectable object-map outputs.",
            "claim_boundary": "Fallback open-vocabulary mapping baseline, not DualMap evidence.",
        },
    ]


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M16 DualMap Object Output Diagnosis",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- M14 verifier status: `{coverage['m14_status']}`.",
        f"- M14 background status: `{coverage['m14_background_status']}`.",
        f"- M14 processed keyframes: {coverage['processed_keyframes']}.",
        f"- M14 configured `stride`: {coverage['configured_stride']}.",
        f"- M14 configured `stable_num`: {coverage['configured_stable_num']}.",
        f"- M14 initial/end local object counts: {coverage['first_local_object_count']} -> {coverage['final_local_object_count']}.",
        f"- M14 object `*.pkl` count: {coverage['pkl_count']}.",
        f"- M14 `layout.pcd` count: {coverage['layout_pcd_count']}.",
        f"- M14 timing files ready: system {coverage['system_time_count']}, detector {coverage['detector_time_count']}.",
        "",
        "## Diagnosis",
        "",
        "- Cache permission and detector initialization are no longer the blocker.",
        "- The missing object-map output is consistent with an object-retention/configuration issue: too few keyframes were processed for the default stability gate, then `end_process` eliminated the local objects before `save_map` wrote object `*.pkl` files.",
        "",
        "## Decision",
        "",
        "- Selected next route: `denser_stride_default_stability_retry`.",
        "- Keep `stable_num=8` and change only `stride=20` -> `stride=5` for the first repair.",
        "- If this still misses `*.pkl`, run a diagnostic lower-`stable_num` retry before switching to `ConceptGraphs`.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['route']}`: rank {row['rank']}, selected {str(row['selected']).lower()}; {row['why']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M16 is a diagnosis/repair plan, not a performance result.",
            "- M17 can support only a `DualMap` one-scan runtime-output smoke unless object schema inspection and adapter evaluation follow.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    base_plan = read_json(M13_PLAN)
    m14_verify = read_json(M14_VERIFY)
    inventory = m14_verify.get("output_inventory", {})
    dualmap_log = Path(inventory.get("sample_dualmap_log", ""))
    log_text = read_text(dualmap_log)
    local_counts = list_ints_from_regex(log_text, r"Local Objects num: (\d+)")
    processed_keyframes = len(re.findall(r"\[Main\] Keyframe idx:", log_text))
    configured_stride = int_from_regex(log_text, r"stride: (\d+)", default=0)
    configured_stable_num = int_from_regex(log_text, r"stable_num: (\d+)", default=0)
    rows = route_rows()
    plan = build_denser_stride_plan(base_plan)
    coverage = {
        "status": "e005_m16_dualmap_object_output_diagnosis_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m14_status": m14_verify.get("status", "missing"),
        "m14_background_status": m14_verify.get("background_status", {}).get("status", "missing"),
        "processed_keyframes": processed_keyframes,
        "configured_stride": configured_stride,
        "configured_stable_num": configured_stable_num,
        "first_local_object_count": local_counts[0] if local_counts else 0,
        "max_local_object_count": max(local_counts) if local_counts else 0,
        "final_local_object_count": local_counts[-1] if local_counts else 0,
        "pkl_count": inventory.get("pkl_count", 0),
        "layout_pcd_count": inventory.get("layout_pcd_count", 0),
        "system_time_count": inventory.get("system_time_count", 0),
        "detector_time_count": inventory.get("detector_time_count", 0),
        "selected_route": "denser_stride_default_stability_retry",
        "next_recommended_unit": "E005-M17 DualMap denser-stride object retry launch",
        "command_plan": str(OUT_DIR / "denser_stride_retry_command_plan.json"),
    }
    decision = {
        "status": coverage["status"],
        "decision": coverage["selected_route"],
        "route_order": [row["route"] for row in rows],
        "next_action": coverage["next_recommended_unit"],
        "claim_boundary": [
            "No DualMap performance claim from E005-M16.",
            "M17 must produce inspectable object *.pkl files before adapter evaluation.",
        ],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_json(OUT_DIR / "denser_stride_retry_command_plan.json", plan)
    write_jsonl(OUT_DIR / "route_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
