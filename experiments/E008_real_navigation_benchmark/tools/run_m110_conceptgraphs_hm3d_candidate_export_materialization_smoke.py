#!/usr/bin/env python3
"""Materialize ConceptGraphs HM3D source-gap object and candidate rows."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M104_ROOT = EXP_ROOT / "artifacts" / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
M106_ROOT = EXP_ROOT / "artifacts" / "E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0"
M109_ROOT = EXP_ROOT / "artifacts" / "E008-M109_conceptgraphs_hm3d_candidate_export_adapter_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
)

VERSION = "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
READY_STATUS = "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_ready"
FAILED_STATUS = "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_failed"
BLOCKED_STATUS = "e008_m110_conceptgraphs_hm3d_candidate_export_materialization_smoke_blocked"
NEXT_UNIT = "E008-M111 ConceptGraphs HM3D candidate navmesh/source-readiness validation"
IMAGE = "research2/conceptgraphs-smoke:latest"
CONTAINER_NAME = "e008_m110_conceptgraphs_candidate_export"
CONCEPTGRAPHS_PYTHON = "/opt/conda/envs/conceptgraph/bin/python"
LOCAL_CLIP_CHECKPOINT = (
    "/opt/conceptgraphs_cache/huggingface/hub/"
    "models--laion--CLIP-ViT-H-14-laion2B-s32B-b79K/"
    "snapshots/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_model.safetensors"
)
BLOCKED_TERMS = ["eval_goal", "eval_viewpoint", "oracle", "success_label", "distance_to_goal"]


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


def build_query_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_rows: list[dict[str, Any]] = []
    for row in case_rows:
        label = str(row.get("object_category") or "").strip()
        scan_id = str(row.get("scan_id") or "")
        if not label or not scan_id:
            continue
        query_rows.append(
            {
                "version": VERSION,
                "query_uid": f"e008_m110:{scan_id}:{label}",
                "scan_id": scan_id,
                "scene_key": row.get("scene_key"),
                "episode_id": row.get("adapter_episode_id"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "query_label": label,
                "label_canonical": label,
                "task_context_id": "source_gap_recovery_probe_v0",
                "m102_branch": row.get("m102_branch"),
                "minimum_requirement": row.get("minimum_requirement"),
                "policy_allowed_input": True,
            }
        )
    return query_rows


def expected_pcd_by_scan() -> dict[str, str]:
    rows = read_jsonl(M106_ROOT / "expected_output_rows.jsonl")
    return {str(row.get("scan_id")): str(row.get("full_pcd_post")) for row in rows if row.get("scan_id")}


def docker_export(query_rows: list[dict[str, Any]], pcd_by_scan: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {
        "version": VERSION,
        "query_rows": query_rows,
        "pcd_by_scan": pcd_by_scan,
    }
    inner = r"""
import gzip
import json
import math
import pickle
import sys

import numpy as np
import open_clip
import torch

payload = json.loads(sys.stdin.read())
version = payload["version"]
query_rows = payload["query_rows"]
pcd_by_scan = payload["pcd_by_scan"]
labels = sorted({row["label_canonical"] for row in query_rows})

device = "cpu"
model, _, _ = open_clip.create_model_and_transforms("ViT-H-14", pretrained="__LOCAL_CLIP_CHECKPOINT__")
model = model.to(device)
model.eval()
tokenizer = open_clip.get_tokenizer("ViT-H-14")
with torch.no_grad():
    tokens = tokenizer(labels).to(device)
    text_features = model.encode_text(tokens).float()
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
label_to_feature = {label: text_features[idx].detach().cpu().numpy() for idx, label in enumerate(labels)}

def finite_list(values):
    out = []
    for value in values:
        try:
            fval = float(value)
        except Exception:
            out.append(None)
            continue
        out.append(round(fval, 6) if math.isfinite(fval) else None)
    return out

def as_array(value):
    if value is None:
        return np.asarray([], dtype=float)
    try:
        return np.asarray(value, dtype=float)
    except Exception:
        return np.asarray([], dtype=float)

query_by_scan = {}
for row in query_rows:
    query_by_scan.setdefault(row["scan_id"], []).append(row)

object_rows = []
candidate_rows = []
pcd_summary_rows = []
for scan_id, pcd_path in pcd_by_scan.items():
    with gzip.open(pcd_path, "rb") as handle:
        concept_payload = pickle.load(handle)
    objects = concept_payload.get("objects", []) if isinstance(concept_payload, dict) else []
    pcd_summary_rows.append({"scan_id": scan_id, "full_pcd_post": pcd_path, "object_count": len(objects)})
    for object_index, obj in enumerate(objects):
        pcd = as_array(obj.get("pcd_np"))
        bbox = as_array(obj.get("bbox_np"))
        if pcd.size:
            pcd = pcd.reshape((-1, 3))
        if bbox.size:
            bbox = bbox.reshape((-1, 3))
        if pcd.size:
            center = pcd.mean(axis=0)
            bbox_min = pcd.min(axis=0)
            bbox_max = pcd.max(axis=0)
        elif bbox.size:
            center = bbox.mean(axis=0)
            bbox_min = bbox.min(axis=0)
            bbox_max = bbox.max(axis=0)
        else:
            center = np.asarray([np.nan, np.nan, np.nan])
            bbox_min = np.asarray([np.nan, np.nan, np.nan])
            bbox_max = np.asarray([np.nan, np.nan, np.nan])
        if bbox.size:
            bbox_min = bbox.min(axis=0)
            bbox_max = bbox.max(axis=0)
        extent = bbox_max - bbox_min
        conf = [float(x) for x in obj.get("conf", [])]
        class_names = [str(x) for x in obj.get("class_name", [])]
        clip_ft = as_array(obj.get("clip_ft"))
        if clip_ft.size:
            clip_ft = clip_ft.reshape((-1,))
            norm = float(np.linalg.norm(clip_ft))
            if norm > 1e-12:
                clip_ft = clip_ft / norm
        candidate_uid = f"conceptgraphs:{scan_id}:post_object:{object_index:04d}"
        object_row = {
            "version": version,
            "candidate_uid": candidate_uid,
            "candidate_id": candidate_uid,
            "scan_id": scan_id,
            "source_route": "conceptgraphs_hm3d_map_candidate_adapter",
            "candidate_source": "conceptgraphs_hm3d_runtime_post_pcd",
            "source_object_index": object_index,
            "source_pcd_path": pcd_path,
            "coordinate_frame": "hm3d_world_from_staged_rgbd_pose",
            "candidate_center_xyz": finite_list(center),
            "candidate_bbox_min_xyz": finite_list(bbox_min),
            "candidate_bbox_max_xyz": finite_list(bbox_max),
            "candidate_extent_xyz": finite_list(extent),
            "candidate_point_count": int(pcd.shape[0]) if pcd.size else 0,
            "candidate_num_detections": int(obj.get("num_detections", 0)),
            "candidate_confidence_mean": round(float(np.mean(conf)), 6) if conf else None,
            "candidate_confidence_max": round(float(np.max(conf)), 6) if conf else None,
            "source_class_names": class_names,
            "source_image_idx": [int(x) for x in obj.get("image_idx", [])],
            "source_mask_idx": [int(x) for x in obj.get("mask_idx", [])],
            "has_clip_ft": bool(clip_ft.size),
            "policy_allowed_input": True,
        }
        object_rows.append(object_row)
        for query in query_by_scan.get(scan_id, []):
            label = query["label_canonical"]
            semantic_score = None
            if clip_ft.size and label in label_to_feature and clip_ft.shape[0] == label_to_feature[label].shape[0]:
                semantic_score = float(np.dot(clip_ft, label_to_feature[label]))
            candidate_rows.append(
                {
                    **object_row,
                    "query_uid": query["query_uid"],
                    "episode_id": query.get("episode_id"),
                    "adapter_episode_id": query.get("adapter_episode_id"),
                    "scene_key": query.get("scene_key"),
                    "query_label": label,
                    "task_context_id": query.get("task_context_id"),
                    "m102_branch": query.get("m102_branch"),
                    "semantic_score": round(semantic_score, 6) if semantic_score is not None else None,
                    "rank": None,
                    "navmesh_validation_status": None,
                    "path_cost_m": None,
                    "eval_success": None,
                }
            )

for query in query_rows:
    qid = query["query_uid"]
    ranked = [row for row in candidate_rows if row["query_uid"] == qid]
    ranked.sort(
        key=lambda row: (
            row["semantic_score"] is not None,
            row["semantic_score"] if row["semantic_score"] is not None else -999.0,
            row["candidate_confidence_max"] if row["candidate_confidence_max"] is not None else -999.0,
        ),
        reverse=True,
    )
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
        row["candidate_visit_order_key"] = f"{qid}:rank{rank:04d}"

coverage = {
    "status": "docker_export_ready",
    "device": device,
    "labels": labels,
    "query_rows": len(query_rows),
    "object_rows": len(object_rows),
    "candidate_rows": len(candidate_rows),
    "semantic_scored_rows": sum(1 for row in candidate_rows if row.get("semantic_score") is not None),
    "pcd_summary_rows": pcd_summary_rows,
}
print("BEGIN_E008_M110_JSON")
print(json.dumps({
    "coverage": coverage,
    "query_rows": query_rows,
    "object_rows": object_rows,
    "candidate_rows": candidate_rows,
    "pcd_summary_rows": pcd_summary_rows,
}, sort_keys=True))
print("END_E008_M110_JSON")
"""
    script = inner.replace("__LOCAL_CLIP_CHECKPOINT__", LOCAL_CLIP_CHECKPOINT)
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        CONTAINER_NAME,
        "-i",
        "-e",
        "HF_HOME=/opt/conceptgraphs_cache/huggingface",
        "-e",
        "TORCH_HOME=/opt/conceptgraphs_cache/torch",
        "-e",
        "XDG_CACHE_HOME=/opt/conceptgraphs_cache/xdg",
        "-v",
        f"{ROOT}:{ROOT}:ro",
        "-v",
        f"{ROOT / 'local_dataset' / 'ConceptGraphs_model_cache'}:/opt/conceptgraphs_cache:rw",
        "-w",
        str(ROOT),
        IMAGE,
        CONCEPTGRAPHS_PYTHON,
        "-c",
        script,
    ]
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return {
            "cmd": cmd,
            "returncode": None,
            "timeout_seconds": 300,
            "stdout_tail": "\n".join((exc.stdout or "").splitlines()[-40:]) if isinstance(exc.stdout, str) else "",
            "stderr_tail": "\n".join((exc.stderr or "").splitlines()[-80:]) if isinstance(exc.stderr, str) else "",
        }, {}
    meta = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-40:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-80:]),
    }
    if proc.returncode != 0:
        return meta, {}
    start = proc.stdout.find("BEGIN_E008_M110_JSON")
    end = proc.stdout.find("END_E008_M110_JSON")
    if start < 0 or end < 0:
        return meta, {}
    return meta, json.loads(proc.stdout[start + len("BEGIN_E008_M110_JSON") : end].strip())


def blocked_term_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        row_text = json.dumps(row, sort_keys=True)
        for term in BLOCKED_TERMS:
            if term in row_text:
                hits.append({"row_index": idx, "term": term})
    return hits


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E008-M110 ConceptGraphs HM3D Candidate Export Materialization Smoke",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Query rows: {coverage.get('query_rows')}.",
            f"- Object rows: {coverage.get('object_rows')}.",
            f"- Candidate rows: {coverage.get('candidate_rows')}.",
            f"- Semantic scored rows: {coverage.get('semantic_scored_rows')} / {coverage.get('candidate_rows')}.",
            f"- Candidate rows ready: {str(coverage.get('candidate_rows_ready')).lower()}.",
            f"- Source-gap recovery supported: {str(coverage.get('source_gap_recovery_supported')).lower()}.",
            f"- Selected next unit: {coverage.get('selected_next_unit')}.",
            "",
            "## Claim Boundary",
            "",
            "- M110 materializes candidate rows only.",
            "- M110 does not validate navmesh reachability, evaluate source-gap recovery, execute trajectories, or support final navigation claims.",
            "",
        ]
    )


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    m109 = read_json(M109_ROOT / "coverage.json")
    case_rows = read_jsonl(M104_ROOT / "case_staging_selection_rows.jsonl")
    query_rows = build_query_rows(case_rows)
    pcd_by_scan = expected_pcd_by_scan()
    pcd_by_scan = {row["scan_id"]: pcd_by_scan.get(row["scan_id"], "") for row in query_rows}
    blockers: list[str] = []
    if m109.get("status") != "e008_m109_conceptgraphs_hm3d_candidate_export_adapter_contract_ready":
        blockers.append("m109_not_ready")
    if not query_rows:
        blockers.append("missing_query_rows")
    missing_pcd = [scan_id for scan_id, path in pcd_by_scan.items() if not path or not Path(path).exists()]
    if missing_pcd:
        blockers.append("missing_post_pcd")
    if blockers:
        coverage = {
            "version": VERSION,
            "status": BLOCKED_STATUS,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "blockers": blockers,
            "missing_pcd_scan_ids": missing_pcd,
            "selected_next_unit": "Repair M109/M108 inputs",
        }
        write_json(ARTIFACT_DIR / "coverage.json", coverage)
        write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    docker_meta, result = docker_export(query_rows, pcd_by_scan)
    write_json(ARTIFACT_DIR / "docker_meta.json", docker_meta)
    if not result:
        coverage = {
            "version": VERSION,
            "status": FAILED_STATUS,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "docker_returncode": docker_meta.get("returncode"),
            "candidate_rows_ready": False,
            "source_gap_recovery_supported": False,
            "selected_next_unit": "Inspect E008-M110 docker_meta stderr/stdout tail",
        }
        write_json(ARTIFACT_DIR / "coverage.json", coverage)
        write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    object_rows = result["object_rows"]
    candidate_rows = result["candidate_rows"]
    query_join_rows = result["query_rows"]
    pcd_summary_rows = result["pcd_summary_rows"]
    leakage_rows = [
        {
            "version": VERSION,
            "artifact": "candidate_rows.jsonl",
            "blocked_terms": BLOCKED_TERMS,
            "blocked_term_hits": blocked_term_hits(candidate_rows),
        },
        {
            "version": VERSION,
            "artifact": "object_rows.jsonl",
            "blocked_terms": BLOCKED_TERMS,
            "blocked_term_hits": blocked_term_hits(object_rows),
        },
    ]
    for row in leakage_rows:
        row["pass"] = len(row["blocked_term_hits"]) == 0
    coords_ready = all(
        isinstance(row.get("candidate_center_xyz"), list)
        and len(row["candidate_center_xyz"]) == 3
        and all(value is not None for value in row["candidate_center_xyz"])
        for row in object_rows
    )
    semantic_ready = len(candidate_rows) > 0 and all(row.get("semantic_score") is not None for row in candidate_rows)
    leakage_pass = all(row["pass"] for row in leakage_rows)
    candidate_rows_ready = bool(candidate_rows) and coords_ready and leakage_pass
    coverage = {
        **result["coverage"],
        "version": VERSION,
        "status": READY_STATUS if candidate_rows_ready else FAILED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "data_output_root": str(DATA_OUT_DIR),
        "m109_status": m109.get("status"),
        "query_labels": sorted({row["query_label"] for row in query_join_rows}),
        "scan_count": len({row["scan_id"] for row in object_rows}),
        "coords_ready": coords_ready,
        "semantic_scoring_ready": semantic_ready,
        "leakage_audit_pass": leakage_pass,
        "candidate_rows_ready": candidate_rows_ready,
        "candidate_generation_supported": candidate_rows_ready,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if candidate_rows_ready else "Repair E008-M110 candidate export",
    }
    write_jsonl(DATA_OUT_DIR / "query_join_rows.jsonl", query_join_rows)
    write_jsonl(DATA_OUT_DIR / "object_rows.jsonl", object_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "pcd_summary_rows.jsonl", pcd_summary_rows)
    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "query_join_rows.jsonl", query_join_rows)
    write_jsonl(ARTIFACT_DIR / "object_rows.jsonl", object_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "pcd_summary_rows.jsonl", pcd_summary_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
