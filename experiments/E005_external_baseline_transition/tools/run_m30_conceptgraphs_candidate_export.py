#!/usr/bin/env python3
"""Export one-scan ConceptGraphs object candidates and CLIP-text scores."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M27_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
M29_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M29_conceptgraphs_output_to_query_conversion_plan_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M30_conceptgraphs_candidate_export_v0"
IMAGE = "research2/conceptgraphs-smoke:latest"
VERSION = "e005_m30_conceptgraphs_candidate_export_v0"
CONTAINER_NAME = "e005_m30_conceptgraphs_candidate_export"
LOCAL_CLIP_CHECKPOINT = (
    "/opt/conceptgraphs_cache/huggingface/hub/"
    "models--laion--CLIP-ViT-H-14-laion2B-s32B-b79K/"
    "snapshots/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_model.safetensors"
)


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


def docker_python(scan_id: str, full_pcd_post: str, query_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {
        "scan_id": scan_id,
        "full_pcd_post": full_pcd_post,
        "query_rows": query_rows,
    }
    inner = r"""
import gzip
import json
import pickle

import numpy as np
import open_clip
import torch

payload = json.loads('''__PAYLOAD_JSON__''')
scan_id = payload["scan_id"]
query_rows = payload["query_rows"]
with gzip.open(payload["full_pcd_post"], "rb") as handle:
    concept_payload = pickle.load(handle)
objects = concept_payload.get("objects", [])

device = "cpu"
model, _, _ = open_clip.create_model_and_transforms("ViT-H-14", pretrained="__LOCAL_CLIP_CHECKPOINT__")
model = model.to(device)
model.eval()
tokenizer = open_clip.get_tokenizer("ViT-H-14")
labels = sorted({row["label_canonical"] for row in query_rows})
with torch.no_grad():
    tokens = tokenizer(labels).to(device)
    text_features = model.encode_text(tokens).float()
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
label_to_feature = {label: text_features[idx].detach().cpu().numpy() for idx, label in enumerate(labels)}

object_rows = []
candidate_rows = []
for object_index, obj in enumerate(objects):
    pcd = np.asarray(obj.get("pcd_np", []), dtype=float)
    bbox = np.asarray(obj.get("bbox_np", []), dtype=float)
    if pcd.size:
        center = pcd.mean(axis=0)
    elif bbox.size:
        center = bbox.mean(axis=0)
    else:
        center = np.array([None, None, None], dtype=object)
    if bbox.size:
        bbox_min = bbox.min(axis=0)
        bbox_max = bbox.max(axis=0)
        extent = bbox_max - bbox_min
    elif pcd.size:
        bbox_min = pcd.min(axis=0)
        bbox_max = pcd.max(axis=0)
        extent = bbox_max - bbox_min
    else:
        bbox_min = bbox_max = extent = np.array([None, None, None], dtype=object)
    conf = [float(x) for x in obj.get("conf", [])]
    clip_ft = np.asarray(obj.get("clip_ft", []), dtype=float)
    if clip_ft.size:
        clip_ft = clip_ft / max(float(np.linalg.norm(clip_ft)), 1e-12)
    object_uid = f"conceptgraphs:{scan_id}:post_object:{object_index:04d}"
    object_row = {
        "candidate_uid": object_uid,
        "scan_id": scan_id,
        "source_baseline": "ConceptGraphs",
        "source_object_index": object_index,
        "candidate_center_xyz": [None if x is None else round(float(x), 6) for x in center],
        "candidate_bbox_min_xyz": [None if x is None else round(float(x), 6) for x in bbox_min],
        "candidate_bbox_max_xyz": [None if x is None else round(float(x), 6) for x in bbox_max],
        "candidate_extent_xyz": [None if x is None else round(float(x), 6) for x in extent],
        "candidate_point_count": int(pcd.shape[0]) if pcd.size else 0,
        "candidate_num_detections": int(obj.get("num_detections", 0)),
        "candidate_confidence_mean": round(float(np.mean(conf)), 6) if conf else None,
        "candidate_confidence_max": round(float(np.max(conf)), 6) if conf else None,
        "candidate_clip_feature_source": "clip_ft",
        "source_class_names": [str(x) for x in obj.get("class_name", [])],
        "source_image_idx": [int(x) for x in obj.get("image_idx", [])],
        "source_mask_idx": [int(x) for x in obj.get("mask_idx", [])],
    }
    object_rows.append(object_row)
    for query in query_rows:
        label = query["label_canonical"]
        semantic_score = None
        if clip_ft.size and label in label_to_feature:
            semantic_score = float(np.dot(clip_ft, label_to_feature[label]))
        candidate_rows.append(
            {
                **object_row,
                "query_uid": query["bridge_query_uid"],
                "query_label": label,
                "task_context_id": query.get("task_context_id"),
                "expected_memory_state": query.get("expected_memory_state"),
                "old_memory_is_stale": query.get("old_memory_is_stale"),
                "old_location_dead_end_expected": query.get("old_location_dead_end_expected"),
                "semantic_score": round(semantic_score, 6) if semantic_score is not None else None,
                "policy_allowed_input": True,
                "eval_match_distance_m": None,
                "eval_success": None,
            }
        )

for query in query_rows:
    qid = query["bridge_query_uid"]
    ranked = [row for row in candidate_rows if row["query_uid"] == qid and row["semantic_score"] is not None]
    ranked.sort(key=lambda row: row["semantic_score"], reverse=True)
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank

coverage = {
    "status": "e005_m30_conceptgraphs_candidate_export_ready",
    "scan_id": scan_id,
    "device": device,
    "object_rows": len(object_rows),
    "query_rows": len(query_rows),
    "candidate_rows": len(candidate_rows),
    "labels": labels,
    "clip_text_scoring_ready": bool(labels) and all(row.get("semantic_score") is not None for row in candidate_rows),
    "top_candidates": sorted(candidate_rows, key=lambda row: row.get("semantic_score") or -999, reverse=True)[:3],
}
print("BEGIN_E005_M30_JSON")
print(json.dumps({"coverage": coverage, "object_rows": object_rows, "candidate_rows": candidate_rows}, sort_keys=True))
print("END_E005_M30_JSON")
"""
    script = inner.replace("__PAYLOAD_JSON__", json.dumps(payload).replace("\\", "\\\\").replace("'", "\\'"))
    script = script.replace("__LOCAL_CLIP_CHECKPOINT__", LOCAL_CLIP_CHECKPOINT)
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        CONTAINER_NAME,
        "--gpus",
        "all",
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
        "/opt/conda/envs/conceptgraph/bin/python",
        "-c",
        script,
    ]
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=240,
        )
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return {
            "cmd": cmd,
            "returncode": None,
            "timeout_seconds": 240,
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
    start = proc.stdout.find("BEGIN_E005_M30_JSON")
    end = proc.stdout.find("END_E005_M30_JSON")
    if start < 0 or end < 0:
        return meta, {}
    json_text = proc.stdout[start + len("BEGIN_E005_M30_JSON") : end].strip()
    return meta, json.loads(json_text)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E005-M30 ConceptGraphs Candidate Export",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Scan: `{coverage.get('scan_id')}`.",
            f"- Device: `{coverage.get('device')}`.",
            f"- Object rows: {coverage.get('object_rows')}.",
            f"- Query rows: {coverage.get('query_rows')}.",
            f"- Candidate rows: {coverage.get('candidate_rows')}.",
            f"- CLIP-text scoring ready: {str(coverage.get('clip_text_scoring_ready')).lower()}.",
            "",
            "## Claim Boundary",
            "",
            "- M30 supports one-scan candidate export and semantic scoring feasibility.",
            "- M30 does not support a `ConceptGraphs` baseline metric claim because eval matching and query-level metrics are deferred to M31.",
            "",
        ]
    )


def main() -> int:
    m27 = read_json(M27_DIR / "coverage.json")
    m29 = read_json(M29_DIR / "coverage.json")
    query_rows = read_jsonl(M29_DIR / "query_join_rows.jsonl")
    full_pcd_post = m27.get("expected_outputs", {}).get("full_pcd_post", "")
    scan_id = m29.get("smoke_scan_id", "")
    errors: list[str] = []
    if not full_pcd_post or not Path(full_pcd_post).exists():
        errors.append("missing_full_pcd_post")
    if not query_rows:
        errors.append("missing_query_join_rows")
    if errors:
        coverage = {
            "status": "e005_m30_conceptgraphs_candidate_export_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "errors": errors,
            "next_recommended_unit": "Repair E005-M27/M29 inputs",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", build_report(coverage))
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    docker_meta, result = docker_python(scan_id, full_pcd_post, query_rows)
    write_json(OUT_DIR / "docker_meta.json", docker_meta)
    if not result:
        coverage = {
            "status": "e005_m30_conceptgraphs_candidate_export_failed",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "docker_returncode": docker_meta.get("returncode"),
            "next_recommended_unit": "Inspect E005-M30 docker_meta stderr/stdout tail",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", build_report(coverage))
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    coverage = {
        **result["coverage"],
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m29_status": m29.get("status"),
        "query_level_baseline_result_ready": False,
        "next_recommended_unit": "E005-M31 one-scan ConceptGraphs query-level metric conversion / rank failure check",
    }
    write_jsonl(OUT_DIR / "object_rows.jsonl", result["object_rows"])
    write_jsonl(OUT_DIR / "candidate_rows.jsonl", result["candidate_rows"])
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
