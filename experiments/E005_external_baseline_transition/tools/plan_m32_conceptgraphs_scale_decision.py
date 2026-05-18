#!/usr/bin/env python3
"""Decide whether to scale ConceptGraphs from one scan to the 4 staged scans."""

from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M21_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M21_conceptgraphs_staging_materialization_v0"
M27_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
M31_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M31_conceptgraphs_query_metric_v0"
M60_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
M73_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M32_conceptgraphs_scale_decision_v0"

VERSION = "e005_m32_conceptgraphs_scale_decision_v0"
IMAGE = "research2/conceptgraphs-smoke:latest"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def run(cmd: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def image_ready() -> bool:
    return run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)["ok"]


def gpu_probe() -> dict[str, Any]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        timeout=10,
    )
    if not result["ok"]:
        return {"ready": False, "raw": result}
    parts = [part.strip() for part in result["stdout"].split(",")]
    return {
        "ready": True,
        "name": parts[0] if len(parts) > 0 else "",
        "memory_total_mib": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
        "memory_used_mib": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
        "memory_free_mib": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None,
    }


def expected_outputs(scan_dir: Path) -> dict[str, Any]:
    gsa = scan_dir / "gsa_detections_none"
    pcd = scan_dir / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"
    post = scan_dir / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"
    return {
        "gsa_detection_count": len(list(gsa.glob("*.pkl.gz"))) if gsa.exists() else 0,
        "full_pcd_exists": pcd.exists(),
        "full_pcd_post_exists": post.exists(),
        "full_pcd": str(pcd),
        "full_pcd_post": str(post),
    }


def query_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_scan = Counter(str(row["current_rescan_id"]) for row in rows)
    by_label = Counter(str(row["label_canonical"]) for row in rows)
    scan_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        scan_label[str(row["current_rescan_id"])][str(row["label_canonical"])] += 1
    return {
        "rows": len(rows),
        "by_scan": dict(sorted(by_scan.items())),
        "by_label": dict(sorted(by_label.items())),
        "by_scan_label": {scan: dict(sorted(counter.items())) for scan, counter in sorted(scan_label.items())},
    }


def build_scan_rows(staged_rows: list[dict[str, Any]], m60_rows: list[dict[str, Any]], m73_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m60_by_scan = Counter(str(row["current_rescan_id"]) for row in m60_rows)
    m73_by_scan = Counter(str(row["current_rescan_id"]) for row in m73_rows)
    rows: list[dict[str, Any]] = []
    for row in staged_rows:
        scan_id = str(row["scan_id"])
        scan_dir = Path(row["target_scan_dir"])
        outputs = expected_outputs(scan_dir)
        completed = bool(outputs["full_pcd_exists"] and outputs["full_pcd_post_exists"] and outputs["gsa_detection_count"] > 0)
        frames = int(row.get("common_frame_count") or 0)
        expected_runtime_minutes = round(max(5.0, frames / 93.0 * 5.0), 2)
        rows.append(
            {
                "scan_id": scan_id,
                "frames": frames,
                "conceptgraphs_scannet_ready": bool(row.get("conceptgraphs_scannet_ready")),
                "resolution_aligned": bool(row.get("resolution_aligned")),
                "m60_query_rows": int(m60_by_scan[scan_id]),
                "m73_query_rows": int(m73_by_scan[scan_id]),
                "runtime_output_completed": completed,
                "launch_required": not completed,
                "expected_runtime_minutes_rough": expected_runtime_minutes,
                **outputs,
            }
        )
    return rows


def metric_boundary() -> dict[str, Any]:
    return {
        "primary_reporting": [
            {
                "name": "strict_bbox_0p5m",
                "threshold_m": 0.5,
                "claim_use": "main strict localization/search success",
            },
            {
                "name": "strict_center_0p5m",
                "threshold_m": 0.5,
                "claim_use": "centroid alignment sanity check",
            },
            {
                "name": "relaxed_bbox_1p0m",
                "threshold_m": 1.0,
                "claim_use": "near-miss / map-object coverage diagnostic only",
            },
        ],
        "blocked_claims": [
            "Do not call relaxed 1.0m near-hit a strict search success.",
            "Do not claim final ConceptGraphs baseline performance until all staged scans are converted to query-level metrics.",
            "Do not claim real navigation SR/SPL from this scale pass.",
        ],
        "scale_success_gate": {
            "minimum": "all staged scans produce full_pcd_post and candidate exports",
            "diagnostic": "report strict and relaxed metrics separately",
            "next_after_runtime": "E005-M34 4-scan candidate export/query metrics",
        },
    }


def decision(scan_rows: list[dict[str, Any]], m31: dict[str, Any], gpu: dict[str, Any]) -> dict[str, Any]:
    ready_scans = [row for row in scan_rows if row["conceptgraphs_scannet_ready"] and row["resolution_aligned"]]
    pending = [row for row in ready_scans if row["launch_required"]]
    blockers: list[str] = []
    if len(ready_scans) < 4:
        blockers.append("not_all_staged_scans_ready")
    if not image_ready():
        blockers.append("conceptgraphs_image_missing")
    if m31.get("status") != "e005_m31_conceptgraphs_query_metric_strict_near_miss_ready":
        blockers.append("m31_boundary_not_ready")
    if gpu.get("ready") and gpu.get("memory_free_mib") is not None and int(gpu["memory_free_mib"]) < 12000:
        blockers.append("low_gpu_free_memory_for_runtime_launch")

    approve = not blockers and bool(pending)
    if approve:
        selected = "approve_background_scale_runtime_for_pending_scans"
        rationale = (
            "M31 gives a measurable near-hit instead of a dead route, all staged scans are ready, "
            "and scale is needed to decide whether the strict miss is systematic or scan-specific."
        )
    elif not pending and not blockers:
        selected = "runtime_outputs_already_complete_move_to_4scan_conversion"
        rationale = "All staged scans already have ConceptGraphs outputs; skip runtime launch and move to conversion."
    else:
        selected = "block_scale_until_preflight_repaired"
        rationale = "Scale should not launch until blockers are cleared."
    return {
        "approved": approve,
        "blockers": blockers,
        "pending_scan_count": len(pending),
        "ready_scan_count": len(ready_scans),
        "rationale": rationale,
        "selected_next_route": selected,
        "pending_scan_ids": [row["scan_id"] for row in pending],
    }


def build_report(coverage: dict[str, Any], route: dict[str, Any], boundary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M32 ConceptGraphs Scale Decision",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Ready staged scans: {coverage['ready_scan_count']} / {coverage['selected_scan_count']}.",
            f"- Pending runtime scans: {coverage['pending_scan_count']}.",
            f"- Completed runtime scans: {coverage['completed_runtime_scan_count']}.",
            f"- M60 query rows over staged scans: {coverage['m60_query_rows']}.",
            f"- M73 expanded query rows over staged scans: {coverage['m73_query_rows']}.",
            f"- M31 failure class: `{coverage['m31_failure_class']}`.",
            f"- GPU free MiB at decision: {coverage['gpu_free_mib']}.",
            f"- Selected route: `{route['selected_next_route']}`.",
            "",
            "## Claim Boundary",
            "",
            f"- Strict metric: `{boundary['primary_reporting'][0]['name']}`.",
            f"- Relaxed diagnostic: `{boundary['primary_reporting'][2]['name']}`.",
            "- The relaxed metric is a near-hit diagnostic, not the main success claim.",
            "",
            "## Agent Inference",
            "",
            f"- {route['rationale']}",
            "",
            "## Next",
            "",
            "- If approved, launch pending scans as a logged background job and verify output inventory before any 4-scan metric claim.",
            "",
        ]
    )


def main() -> int:
    staged_rows = read_jsonl(M21_DIR / "materialization_rows.jsonl")
    m60_rows = read_jsonl(M60_DIR / "query_bridge_rows.jsonl")
    m73_rows = read_jsonl(M73_DIR / "direct_bridge_query_rows.jsonl")
    m31 = read_json(M31_DIR / "coverage.json")
    gpu = gpu_probe()
    scan_rows = build_scan_rows(staged_rows, m60_rows, m73_rows)
    boundary = metric_boundary()
    route = decision(scan_rows, m31, gpu)
    completed = sum(1 for row in scan_rows if row["runtime_output_completed"])
    coverage = {
        "status": "e005_m32_conceptgraphs_scale_decision_approved"
        if route["approved"]
        else "e005_m32_conceptgraphs_scale_decision_blocked"
        if route["blockers"]
        else "e005_m32_conceptgraphs_scale_decision_ready_no_runtime_needed",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "selected_scan_count": len(scan_rows),
        "ready_scan_count": route["ready_scan_count"],
        "pending_scan_count": route["pending_scan_count"],
        "completed_runtime_scan_count": completed,
        "pending_scan_ids": route["pending_scan_ids"],
        "m60_query_rows": len(m60_rows),
        "m60_query_summary": query_summary(m60_rows),
        "m73_query_rows": len(m73_rows),
        "m73_query_summary": query_summary(m73_rows),
        "m31_status": m31.get("status"),
        "m31_failure_class": m31.get("failure_class"),
        "gpu_free_mib": gpu.get("memory_free_mib"),
        "blockers": route["blockers"],
        "selected_next_route": route["selected_next_route"],
        "next_recommended_unit": "E005-M33 ConceptGraphs pending-scan background runtime launch"
        if route["approved"]
        else "Repair M32 blockers before launch",
    }
    write_jsonl(OUT_DIR / "scan_rows.jsonl", scan_rows)
    write_json(OUT_DIR / "metric_boundary.json", boundary)
    write_json(OUT_DIR / "route_decision.json", route)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, route, boundary))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
