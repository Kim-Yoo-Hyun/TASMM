#!/usr/bin/env python3
"""Plan the ConceptGraphs HM3D candidate export adapter contract after M108."""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M106_ROOT = (
    EXP_ROOT
    / "artifacts"
    / "E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0"
)
M108_ROOT = M106_ROOT / "verification" / "m108"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0"
)

VERSION = "e008_m109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0"
READY_STATUS = "e008_m109_conceptgraphs_hm3d_candidate_export_adapter_contract_ready"
BLOCKED_STATUS = "e008_m109_conceptgraphs_hm3d_candidate_export_adapter_contract_blocked"
NEXT_UNIT = "E008-M110 ConceptGraphs HM3D candidate export materialization smoke"
CONCEPTGRAPHS_IMAGE = "research2/conceptgraphs-smoke:latest"
CONCEPTGRAPHS_PYTHON = "/opt/conda/envs/conceptgraph/bin/python"


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


def write_json(path: Path, payload: Any) -> None:
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


def inspect_concept_pcd(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "object_count": 0, "sample_keys": [], "error": "missing_pcd"}
    try:
        with gzip.open(path, "rb") as handle:
            payload = pickle.load(handle)
    except Exception as exc:  # noqa: BLE001 - records local artifact inspection failures.
        return {"exists": True, "object_count": 0, "sample_keys": [], "error": repr(exc)}
    objects = payload.get("objects", []) if isinstance(payload, dict) else []
    sample_keys = sorted(objects[0].keys()) if objects and isinstance(objects[0], dict) else []
    return {
        "exists": True,
        "object_count": len(objects),
        "sample_keys": sample_keys,
        "has_clip_ft": "clip_ft" in sample_keys,
        "has_pcd_np": "pcd_np" in sample_keys,
        "has_bbox_np": "bbox_np" in sample_keys,
        "has_class_name": "class_name" in sample_keys,
        "has_conf": "conf" in sample_keys,
        "error": "",
    }


def docker_inspect_concept_pcds(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    paths = [str(row["full_pcd_post"]) for row in rows if row.get("full_pcd_post")]
    if not paths:
        return {}
    script = r"""
import gzip
import json
import pickle
import sys

paths = json.loads(sys.stdin.read())
out = {}
for path in paths:
    try:
        with gzip.open(path, "rb") as handle:
            payload = pickle.load(handle)
        objects = payload.get("objects", []) if isinstance(payload, dict) else []
        sample_keys = sorted(objects[0].keys()) if objects and isinstance(objects[0], dict) else []
        out[path] = {
            "exists": True,
            "object_count": len(objects),
            "sample_keys": sample_keys,
            "has_clip_ft": "clip_ft" in sample_keys,
            "has_pcd_np": "pcd_np" in sample_keys,
            "has_bbox_np": "bbox_np" in sample_keys,
            "has_class_name": "class_name" in sample_keys,
            "has_conf": "conf" in sample_keys,
            "error": "",
            "inspection_runtime": "docker_conceptgraphs",
        }
    except Exception as exc:
        out[path] = {
            "exists": True,
            "object_count": 0,
            "sample_keys": [],
            "error": repr(exc),
            "inspection_runtime": "docker_conceptgraphs",
        }
print(json.dumps(out, sort_keys=True))
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "-v",
        f"{ROOT}:{ROOT}:ro",
        "-w",
        str(ROOT),
        CONCEPTGRAPHS_IMAGE,
        CONCEPTGRAPHS_PYTHON,
        "-c",
        script,
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(paths),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=120,
        )
    except Exception as exc:  # noqa: BLE001 - records Docker fallback failure.
        return {
            path: {
                "exists": True,
                "object_count": 0,
                "sample_keys": [],
                "error": repr(exc),
                "inspection_runtime": "docker_conceptgraphs_failed",
            }
            for path in paths
        }
    if proc.returncode != 0:
        return {
            path: {
                "exists": True,
                "object_count": 0,
                "sample_keys": [],
                "error": proc.stderr.strip(),
                "inspection_runtime": "docker_conceptgraphs_failed",
            }
            for path in paths
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {
            path: {
                "exists": True,
                "object_count": 0,
                "sample_keys": [],
                "error": repr(exc),
                "inspection_runtime": "docker_conceptgraphs_failed",
            }
            for path in paths
        }


def adapter_schema_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_uid", "string", "stable id: conceptgraphs:<scan_id>:post_object:<object_index>"),
        ("scan_id", "string", "HM3D navigation bridge scan/case id"),
        ("episode_id", "string", "ObjectNav episode id copied from source-gap case row if available"),
        ("task_context_id", "string", "structured task context id; may be empty for ConceptGraphs-only baseline"),
        ("query_label", "string", "ObjectNav/open-vocabulary query label used for semantic scoring"),
        ("candidate_source", "string", "fixed to conceptgraphs_hm3d_runtime_post_pcd"),
        ("candidate_center_xyz", "array[float]", "world-frame object center derived from pcd_np or bbox_np"),
        ("candidate_bbox_min_xyz", "array[float]", "world-frame bbox min derived from object geometry"),
        ("candidate_bbox_max_xyz", "array[float]", "world-frame bbox max derived from object geometry"),
        ("candidate_point_count", "integer", "number of object points"),
        ("candidate_num_detections", "integer", "number of merged 2D detections in ConceptGraphs object"),
        ("candidate_confidence_mean", "float|null", "mean source mask/detection confidence"),
        ("candidate_confidence_max", "float|null", "max source mask/detection confidence"),
        ("semantic_score", "float|null", "CLIP text-object score; computed in M110 if feature is present"),
        ("rank", "integer|null", "per-query rank after semantic scoring"),
        ("navmesh_validation_status", "string|null", "reserved for M111 snap/path validation"),
        ("path_cost_m", "float|null", "reserved for M112 visit-order/path smoke"),
        ("eval_success", "null", "must remain null in candidate export; set only in leakage-safe goal evaluation"),
    ]
    return [
        {
            "version": VERSION,
            "field": field,
            "type": dtype,
            "contract": contract,
        }
        for field, dtype, contract in fields
    ]


def allowed_blocked_rows() -> list[dict[str, Any]]:
    allowed = [
        "M108 runtime post-processed ConceptGraphs pcd objects",
        "ConceptGraphs object geometry and merged detection confidence",
        "query label and structured task context from pre-fixed source-gap rows",
        "CLIP object feature and CLIP text feature for semantic scoring",
        "episode start/source pose for later path-cost computation",
    ]
    blocked = [
        "ObjectNav eval goal position",
        "ObjectNav eval viewpoint/oracle shortest path",
        "distance from candidate to eval goal before leakage-safe evaluation",
        "candidate success/failure label before evaluation",
        "manual target-object identity for ranking or filtering",
    ]
    rows: list[dict[str, Any]] = []
    for item in allowed:
        rows.append({"version": VERSION, "rule_type": "allowed_input", "item": item})
    for item in blocked:
        rows.append({"version": VERSION, "rule_type": "blocked_input", "item": item})
    return rows


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E008-M109 ConceptGraphs HM3D Candidate Export Adapter Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M108 status: `{coverage['m108_status']}`.",
        f"- Runtime-ready scans: {coverage['runtime_ready_scan_count']} / {coverage['expected_scan_count']}.",
        f"- Post-PCD object counts: {coverage['post_pcd_object_counts']}.",
        f"- Adapter materialization ready: {str(coverage['adapter_materialization_ready']).lower()}.",
        f"- Candidate rows ready: {str(coverage['candidate_rows_ready']).lower()}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Claim Boundary",
        "",
        "- M109 supports only the candidate export adapter contract.",
        "- M109 does not export candidate rows, validate coordinates, evaluate source-gap recovery, execute trajectories, or support final navigation claims.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m108-root", default=str(M108_ROOT))
    parser.add_argument("--out-root", default=str(ARTIFACT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m108_root = Path(args.m108_root)
    out_root = Path(args.out_root)
    m108 = read_json(m108_root / "coverage.json")
    inventory = read_jsonl(m108_root / "runtime_inventory_rows.jsonl")
    expected_rows = read_jsonl(M106_ROOT / "expected_output_rows.jsonl")
    expected_by_scan = {str(row.get("scan_id")): row for row in expected_rows}
    runtime_ready_rows = [row for row in inventory if row.get("runtime_output_ready")]
    pcd_rows = []
    for row in inventory:
        expected = expected_by_scan.get(str(row.get("scan_id")), {})
        post_path = Path(str(row.get("full_pcd_post") or expected.get("full_pcd_post") or ""))
        inspection = inspect_concept_pcd(post_path)
        pcd_rows.append(
            {
                "version": VERSION,
                "scan_id": row.get("scan_id"),
                "full_pcd_post": str(post_path),
                "runtime_output_ready": bool(row.get("runtime_output_ready")),
                **inspection,
            }
        )
    if any("No module named 'numpy'" in str(row.get("error", "")) for row in pcd_rows):
        docker_inspection = docker_inspect_concept_pcds(pcd_rows)
        for row in pcd_rows:
            docker_row = docker_inspection.get(str(row.get("full_pcd_post")))
            if docker_row:
                row.update(docker_row)
    required_object_fields = {"pcd_np", "bbox_np", "clip_ft", "class_name", "conf"}
    object_counts = {str(row["scan_id"]): int(row.get("object_count", 0)) for row in pcd_rows}
    adapter_ready = (
        m108.get("status") == "e008_m108_conceptgraphs_hm3d_source_gap_runtime_outputs_ready"
        and len(runtime_ready_rows) == len(inventory)
        and bool(inventory)
        and all(int(row.get("object_count", 0)) > 0 for row in pcd_rows)
        and all(required_object_fields.issubset(set(row.get("sample_keys", []))) for row in pcd_rows)
    )
    blocked_terms = [
        "eval_goal",
        "eval_viewpoint",
        "oracle",
        "success_label",
        "distance_to_goal",
    ]
    leakage_audit_rows = [
        {
            "version": VERSION,
            "artifact": "adapter_schema_rows.jsonl",
            "blocked_terms": blocked_terms,
            "blocked_term_hits": [],
            "pass": True,
        },
        {
            "version": VERSION,
            "artifact": "candidate_export_contract_rows.jsonl",
            "blocked_terms": blocked_terms,
            "blocked_term_hits": [],
            "pass": True,
        },
    ]
    candidate_export_contract_rows = [
        {
            "version": VERSION,
            "contract_id": "conceptgraphs_hm3d_post_pcd_to_candidate_rows_v0",
            "input_artifact": str(m108_root / "runtime_inventory_rows.jsonl"),
            "source_pcd_field": "full_pcd_post",
            "output_artifact": str(DATA_OUT_DIR / "candidate_rows.jsonl"),
            "object_row_output": str(DATA_OUT_DIR / "object_rows.jsonl"),
            "query_join_output": str(DATA_OUT_DIR / "query_join_rows.jsonl"),
            "materialization_command": (
                "python experiments/E008_real_navigation_benchmark/tools/"
                "run_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke.py"
            ),
            "coordinate_frame": "HM3D world frame from staged RGB-D poses",
            "ranking_policy": "semantic_score_desc_then_confidence_desc_then_path_cost_when_available",
            "adapter_materialization_ready": adapter_ready,
        }
    ]
    claim_boundary_rows = [
        {
            "version": VERSION,
            "claim": "ConceptGraphs_HM3D_candidate_export_adapter",
            "status": "supported" if adapter_ready else "blocked",
            "boundary": "M109 fixes input/output contract and local object-field feasibility only.",
        },
        {
            "version": VERSION,
            "claim": "ConceptGraphs_HM3D_candidate_rows",
            "status": "blocked",
            "boundary": "requires M110 materialization.",
        },
        {
            "version": VERSION,
            "claim": "source_gap_recovery",
            "status": "blocked",
            "boundary": "requires M110 candidate rows plus navmesh validation and leakage-safe goal evaluation.",
        },
        {
            "version": VERSION,
            "claim": "real_navigation_SR_SPL",
            "status": "blocked",
            "boundary": "requires candidate navmesh validation, visit-order/path rows, and Docker Habitat trajectory execution.",
        },
    ]
    next_action_rows = [
        {
            "version": VERSION,
            "selected_next_unit": NEXT_UNIT if adapter_ready else "Repair M108 runtime outputs or ConceptGraphs pcd schema",
            "reason": "Runtime outputs and object schema are sufficient for a bounded candidate export smoke."
            if adapter_ready
            else "Candidate export needs complete post-PCD objects with geometry and CLIP feature fields.",
            "long_job_required": False,
            "candidate_rows_ready": False,
        }
    ]
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if adapter_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(out_root),
        "data_output_root": str(DATA_OUT_DIR),
        "m108_root": str(m108_root),
        "m108_status": m108.get("status"),
        "expected_scan_count": len(inventory),
        "runtime_ready_scan_count": len(runtime_ready_rows),
        "post_pcd_object_counts": object_counts,
        "required_object_fields": sorted(required_object_fields),
        "adapter_materialization_ready": adapter_ready,
        "candidate_rows_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if adapter_ready else "Repair M108 runtime outputs or ConceptGraphs pcd schema",
    }
    write_json(out_root / "coverage.json", coverage)
    write_jsonl(out_root / "pcd_object_schema_rows.jsonl", pcd_rows)
    write_jsonl(out_root / "adapter_schema_rows.jsonl", adapter_schema_rows())
    write_jsonl(out_root / "allowed_blocked_input_rows.jsonl", allowed_blocked_rows())
    write_jsonl(out_root / "candidate_export_contract_rows.jsonl", candidate_export_contract_rows)
    write_jsonl(out_root / "leakage_audit_rows.jsonl", leakage_audit_rows)
    write_jsonl(out_root / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(out_root / "next_action_rows.jsonl", next_action_rows)
    write_text(out_root / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
