#!/usr/bin/env python3
"""Export 4-scan ConceptGraphs candidates and query-level metrics."""

from __future__ import annotations

import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M21_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M21_conceptgraphs_staging_materialization_v0"
M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M33_conceptgraphs_pending_scan_runtime_v0"
M60_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
M73_DIR = ROOT / "experiments" / "E003_perception_noise_expansion" / "artifacts" / "E003-M73_direct_bridge_denominator_expansion_plan_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M35_conceptgraphs_4scan_query_metric_v0"

VERSION = "e005_m35_conceptgraphs_4scan_query_metric_v0"
IMAGE = "research2/conceptgraphs-smoke:latest"
CONTAINER_NAME = "e005_m35_conceptgraphs_4scan_query_metrics"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"
LOCAL_CLIP_CHECKPOINT = (
    "/opt/conceptgraphs_cache/huggingface/hub/"
    "models--laion--CLIP-ViT-H-14-laion2B-s32B-b79K/"
    "snapshots/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_model.safetensors"
)

POLICIES = [
    {
        "policy": "conceptgraphs_clip_rank_centroid_strict_top5_v0",
        "distance_field": "eval_center_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 3,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 5,
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_unbounded_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": "all",
    },
]


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


def expected_post_path(scan_id: str) -> Path:
    return (
        ROOT
        / "local_dataset"
        / "ConceptGraphs_staged"
        / "3rscan_depth_aligned_scannet"
        / scan_id
        / "pcd_saves"
        / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"
    )


def scan_ids_from_m21() -> list[str]:
    rows = read_jsonl(M21_DIR / "materialization_rows.jsonl")
    return [str(row["scan_id"]) for row in rows if row.get("conceptgraphs_scannet_ready")]


def docker_export(scan_ids: list[str], primary_queries: list[dict[str, Any]], expanded_queries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    post_paths = {scan_id: str(expected_post_path(scan_id)) for scan_id in scan_ids}
    payload = {
        "version": VERSION,
        "scan_ids": scan_ids,
        "post_paths": post_paths,
        "query_suites": {
            "primary_m60": primary_queries,
            "expanded_m73": expanded_queries,
        },
    }
    payload_path = OUT_DIR / "docker_payload.json"
    docker_script_path = OUT_DIR / "docker_export_m35.py"
    write_json(payload_path, payload)
    inner = r"""
import gzip
import json
import pickle
import sys

import numpy as np
import open_clip
import torch

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
scan_ids = payload["scan_ids"]
post_paths = payload["post_paths"]
query_suites = payload["query_suites"]

labels = sorted({row["label_canonical"] for rows in query_suites.values() for row in rows})
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

queries_by_suite_scan = {}
for suite, rows in query_suites.items():
    by_scan = {}
    for row in rows:
        by_scan.setdefault(row["current_rescan_id"], []).append(row)
    queries_by_suite_scan[suite] = by_scan

object_rows = []
candidate_rows = []
scan_object_counts = {}
for scan_id in scan_ids:
    with gzip.open(post_paths[scan_id], "rb") as handle:
        concept_payload = pickle.load(handle)
    objects = concept_payload.get("objects", [])
    scan_object_counts[scan_id] = len(objects)
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

        for suite, by_scan in queries_by_suite_scan.items():
            for query in by_scan.get(scan_id, []):
                label = query["label_canonical"]
                semantic_score = None
                if clip_ft.size and label in label_to_feature:
                    semantic_score = float(np.dot(clip_ft, label_to_feature[label]))
                candidate_rows.append(
                    {
                        **object_row,
                        "query_suite": suite,
                        "query_uid": query["bridge_query_uid"],
                        "query_label": label,
                        "target_uid": query["target_uid"],
                        "task_context_id": query.get("task_context_id"),
                        "row_band": query.get("row_band"),
                        "expected_memory_state": query.get("expected_memory_state"),
                        "old_memory_is_stale": query.get("old_memory_is_stale"),
                        "old_location_dead_end_expected": query.get("old_location_dead_end_expected"),
                        "semantic_score": round(semantic_score, 6) if semantic_score is not None else None,
                        "policy_allowed_input": True,
                    }
                )

for suite in query_suites:
    qids = sorted({row["query_uid"] for row in candidate_rows if row["query_suite"] == suite})
    for query_uid in qids:
        ranked = [
            row
            for row in candidate_rows
            if row["query_suite"] == suite and row["query_uid"] == query_uid and row["semantic_score"] is not None
        ]
        ranked.sort(key=lambda row: row["semantic_score"], reverse=True)
        for rank, row in enumerate(ranked, start=1):
            row["rank"] = rank

coverage = {
    "status": "docker_export_ready",
    "device": device,
    "scan_ids": scan_ids,
    "scan_object_counts": scan_object_counts,
    "object_rows": len(object_rows),
    "candidate_rows": len(candidate_rows),
    "query_rows_by_suite": {suite: len(rows) for suite, rows in query_suites.items()},
    "labels": labels,
    "clip_text_scoring_ready": bool(labels) and all(row.get("semantic_score") is not None for row in candidate_rows),
}
print("BEGIN_E005_M35_JSON")
print(json.dumps({"coverage": coverage, "object_rows": object_rows, "candidate_rows": candidate_rows}, sort_keys=True))
print("END_E005_M35_JSON")
"""
    script = inner.replace("__LOCAL_CLIP_CHECKPOINT__", LOCAL_CLIP_CHECKPOINT)
    write_text(docker_script_path, script)
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
        "/opt/conda/envs/conceptgraph/bin/python",
        str(docker_script_path),
        str(payload_path),
    ]
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=900)
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return {
            "cmd": cmd,
            "returncode": None,
            "timeout_seconds": 900,
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
    start = proc.stdout.find("BEGIN_E005_M35_JSON")
    end = proc.stdout.find("END_E005_M35_JSON")
    if start < 0 or end < 0:
        return meta, {}
    json_text = proc.stdout[start + len("BEGIN_E005_M35_JSON") : end].strip()
    return meta, json.loads(json_text)


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(a, b)))


def bbox_distance(point: list[float], bbox_min: list[float], bbox_max: list[float]) -> float:
    sq = 0.0
    for value, low, high in zip(point, bbox_min, bbox_max):
        if value < low:
            sq += (low - value) ** 2
        elif value > high:
            sq += (value - high) ** 2
    return math.sqrt(sq)


def safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def attempt_spl(success: bool, expected_cost: int) -> float:
    if not success or expected_cost <= 0:
        return 0.0
    return round(1.0 / float(expected_cost), 6)


def build_candidate_eval_rows(
    candidate_rows: list[dict[str, Any]],
    target_by_uid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        target = target_by_uid[str(candidate["target_uid"])]
        target_centroid = [float(x) for x in target["centroid_world_m"]]
        center = [float(x) for x in candidate["candidate_center_xyz"]]
        bbox_min = [float(x) for x in candidate["candidate_bbox_min_xyz"]]
        bbox_max = [float(x) for x in candidate["candidate_bbox_max_xyz"]]
        center_distance = distance(center, target_centroid)
        box_distance = bbox_distance(target_centroid, bbox_min, bbox_max)
        success_threshold = 0.5
        eval_rows.append(
            {
                **candidate,
                "m35_version": VERSION,
                "target_centroid_world_m": [round(x, 6) for x in target_centroid],
                "target_label_canonical": target["label_canonical"],
                "target_object_instance_id": target["object_instance_id"],
                "eval_center_distance_m": round(center_distance, 6),
                "eval_bbox_distance_m": round(box_distance, 6),
                "eval_center_success_strict": center_distance <= success_threshold,
                "eval_bbox_success_strict": box_distance <= success_threshold,
                "eval_bbox_success_relaxed_1m": box_distance <= 1.0,
                "eval_success_threshold_m": success_threshold,
                "eval_relaxed_threshold_m": 1.0,
            }
        )
    return sorted(eval_rows, key=lambda row: (str(row["query_suite"]), str(row["query_uid"]), int(row["rank"])))


def first_rank(rows: list[dict[str, Any]], distance_field: str, threshold_m: float) -> tuple[int | None, str | None, float | None]:
    for row in sorted(rows, key=lambda item: int(item["rank"])):
        distance_value = float(row[distance_field])
        if distance_value <= threshold_m:
            return int(row["rank"]), str(row["candidate_uid"]), round(distance_value, 6)
    return None, None, None


def build_policy_rows(eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_query: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        rows_by_query[(str(row["query_suite"]), str(row["query_uid"]))].append(row)

    policy_rows: list[dict[str, Any]] = []
    for (suite, query_uid), query_candidates in sorted(rows_by_query.items()):
        ordered = sorted(query_candidates, key=lambda item: int(item["rank"]))
        first = ordered[0]
        for policy in POLICIES:
            target_rank, target_candidate_uid, match_distance = first_rank(
                ordered,
                str(policy["distance_field"]),
                float(policy["threshold_m"]),
            )
            candidate_count = len(ordered)
            returned = candidate_count if policy["budget"] == "all" else min(candidate_count, int(policy["budget"]))
            success = target_rank is not None and target_rank <= returned
            expected_cost = int(target_rank) if success and target_rank is not None else returned + 1
            policy_rows.append(
                {
                    "m35_version": VERSION,
                    "query_suite": suite,
                    "query_uid": query_uid,
                    "target_uid": first["target_uid"],
                    "scan_id": first["scan_id"],
                    "label_canonical": first["query_label"],
                    "task_context_id": first["task_context_id"],
                    "row_band": first.get("row_band"),
                    "policy": policy["policy"],
                    "distance_field": policy["distance_field"],
                    "threshold_m": policy["threshold_m"],
                    "candidate_count": candidate_count,
                    "returned_location_count": returned,
                    "target_detected": target_rank is not None,
                    "target_rank": target_rank,
                    "target_candidate_uid": target_candidate_uid,
                    "target_match_distance_m": match_distance,
                    "false_positive_before_target_count": target_rank - 1 if target_rank is not None else None,
                    "query_bridge_success": success,
                    "expected_search_cost": expected_cost,
                    "attempt_spl_proxy": attempt_spl(success, expected_cost),
                    "old_memory_is_stale": first.get("old_memory_is_stale"),
                    "old_location_dead_end_expected": first.get("old_location_dead_end_expected"),
                    "query_level_baseline_result_ready": suite == "primary_m60",
                    "real_navigation_sr_spl_ready": False,
                }
            )
    return policy_rows


def summarize_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["query_bridge_success"]]
    detected = [row for row in rows if row["target_detected"]]
    return {
        "rows": len(rows),
        "target_detected_rows": len(detected),
        "target_detected_rate": safe_rate(len(detected), len(rows)),
        "query_bridge_success_rows": len(successes),
        "query_bridge_success_rate": safe_rate(len(successes), len(rows)),
        "mean_target_rank_if_detected": safe_mean([float(row["target_rank"]) for row in detected]),
        "mean_expected_search_cost": safe_mean([float(row["expected_search_cost"]) for row in rows]),
        "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in rows]),
    }


def build_suite_metrics(eval_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]], suite: str) -> dict[str, Any]:
    suite_eval = [row for row in eval_rows if row["query_suite"] == suite]
    suite_policy = [row for row in policy_rows if row["query_suite"] == suite]
    by_policy = defaultdict(list)
    for row in suite_policy:
        by_policy[row["policy"]].append(row)
    return {
        "candidate_rows": len(suite_eval),
        "query_rows": len({row["query_uid"] for row in suite_eval}),
        "scan_count": len({row["scan_id"] for row in suite_eval}),
        "target_uid_count": len({row["target_uid"] for row in suite_eval}),
        "min_center_distance_m": min((float(row["eval_center_distance_m"]) for row in suite_eval), default=None),
        "min_bbox_distance_m": min((float(row["eval_bbox_distance_m"]) for row in suite_eval), default=None),
        "strict_center_hit_rows": sum(1 for row in suite_eval if row["eval_center_success_strict"]),
        "strict_bbox_hit_rows": sum(1 for row in suite_eval if row["eval_bbox_success_strict"]),
        "relaxed_bbox_1m_hit_rows": sum(1 for row in suite_eval if row["eval_bbox_success_relaxed_1m"]),
        "policy_metrics": {policy: summarize_policy(rows) for policy, rows in sorted(by_policy.items())},
    }


def failure_class(metrics: dict[str, Any]) -> str:
    if metrics["strict_bbox_hit_rows"] > 0:
        return "strict_bbox_hit_available"
    if metrics["relaxed_bbox_1m_hit_rows"] > 0:
        return "strict_threshold_miss_relaxed_bbox_hit"
    if metrics["candidate_rows"] > 0:
        return "map_candidate_target_miss"
    return "no_map_candidates"


def build_report(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    primary = metrics["suites"]["primary_m60"]
    expanded = metrics["suites"]["expanded_m73"]
    primary_strict = primary["policy_metrics"]["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    primary_relaxed = primary["policy_metrics"]["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]
    expanded_strict = expanded["policy_metrics"]["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    expanded_relaxed = expanded["policy_metrics"]["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]
    return "\n".join(
        [
            "# E005-M35 ConceptGraphs 4-Scan Query Metric",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Scans: {coverage['scan_count']}.",
            f"- Object rows: {coverage['object_rows']}.",
            f"- Primary M60 query rows: {primary['query_rows']}.",
            f"- Expanded M73 query rows: {expanded['query_rows']}.",
            f"- Primary candidate rows: {primary['candidate_rows']}.",
            f"- Expanded candidate rows: {expanded['candidate_rows']}.",
            f"- Primary strict bbox top5 success rows/rate: {primary_strict['query_bridge_success_rows']} / {primary_strict['query_bridge_success_rate']}.",
            f"- Primary relaxed bbox 1m top3 success rows/rate: {primary_relaxed['query_bridge_success_rows']} / {primary_relaxed['query_bridge_success_rate']}.",
            f"- Expanded strict bbox top5 success rows/rate: {expanded_strict['query_bridge_success_rows']} / {expanded_strict['query_bridge_success_rate']}.",
            f"- Expanded relaxed bbox 1m top3 success rows/rate: {expanded_relaxed['query_bridge_success_rows']} / {expanded_relaxed['query_bridge_success_rate']}.",
            f"- Primary failure class: `{coverage['primary_failure_class']}`.",
            f"- Expanded failure class: `{coverage['expanded_failure_class']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M35 is a 4-scan external baseline conversion result, but still a small staged subset.",
            "- Primary `M60` metrics and expanded `M73` coverage diagnostics must be reported separately.",
            "- Strict 0.5m bbox/center success and relaxed 1.0m bbox near-hit must be reported separately.",
            "- This does not support final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL`.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scan_ids = scan_ids_from_m21()
    m33 = read_json(M33_DIR / "verification" / "coverage.json")
    primary_queries = read_jsonl(M60_DIR / "query_bridge_rows.jsonl")
    expanded_queries = read_jsonl(M73_DIR / "direct_bridge_query_rows.jsonl")
    target_by_uid = {str(row["target_uid"]): row for row in read_jsonl(M73_DIR / "real_proposal_object_targets.jsonl")}
    errors: list[str] = []

    if m33.get("status") != "e005_m33_conceptgraphs_pending_scan_runtime_outputs_ready":
        errors.append("m33_outputs_not_ready")
    for scan_id in scan_ids:
        if not expected_post_path(scan_id).exists():
            errors.append(f"missing_full_pcd_post:{scan_id}")
    for query in primary_queries + expanded_queries:
        if str(query["target_uid"]) not in target_by_uid:
            errors.append(f"missing_target:{query['target_uid']}")
            break

    if errors:
        coverage = {
            "status": "e005_m35_conceptgraphs_4scan_query_metric_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "errors": errors,
            "next_recommended_unit": "Repair M33/M60/M73 inputs",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", "# E005-M35 ConceptGraphs 4-Scan Query Metric\n\nBlocked.\n")
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    docker_meta, result = docker_export(scan_ids, primary_queries, expanded_queries)
    write_json(OUT_DIR / "docker_meta.json", docker_meta)
    if not result:
        coverage = {
            "status": "e005_m35_conceptgraphs_4scan_query_metric_failed",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "docker_returncode": docker_meta.get("returncode"),
            "next_recommended_unit": "Inspect E005-M35 docker_meta stderr/stdout tail",
        }
        write_json(OUT_DIR / "coverage.json", coverage)
        write_text(OUT_DIR / "report.md", "# E005-M35 ConceptGraphs 4-Scan Query Metric\n\nFailed.\n")
        print(json.dumps(coverage, indent=2, sort_keys=True))
        return 0

    object_rows = result["object_rows"]
    candidate_rows = result["candidate_rows"]
    eval_rows = build_candidate_eval_rows(candidate_rows, target_by_uid)
    policy_rows = build_policy_rows(eval_rows)
    metrics = {
        "suites": {
            "primary_m60": build_suite_metrics(eval_rows, policy_rows, "primary_m60"),
            "expanded_m73": build_suite_metrics(eval_rows, policy_rows, "expanded_m73"),
        }
    }
    primary_failure = failure_class(metrics["suites"]["primary_m60"])
    expanded_failure = failure_class(metrics["suites"]["expanded_m73"])
    status = (
        "e005_m35_conceptgraphs_4scan_query_metric_ready_with_strict_hits"
        if primary_failure == "strict_bbox_hit_available"
        else "e005_m35_conceptgraphs_4scan_query_metric_ready_near_hit_only"
        if primary_failure == "strict_threshold_miss_relaxed_bbox_hit"
        else "e005_m35_conceptgraphs_4scan_query_metric_ready_target_miss"
    )
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m33_status": m33.get("status"),
        "scan_count": len(scan_ids),
        "scan_ids": scan_ids,
        "object_rows": len(object_rows),
        "candidate_rows": len(candidate_rows),
        "primary_failure_class": primary_failure,
        "expanded_failure_class": expanded_failure,
        "query_level_baseline_result_ready": True,
        "small_subset_only": True,
        "final_baseline_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M36 ConceptGraphs 4-scan failure analysis / claim boundary",
    }

    write_jsonl(OUT_DIR / "object_rows.jsonl", object_rows)
    write_jsonl(OUT_DIR / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(OUT_DIR / "candidate_eval_rows.jsonl", eval_rows)
    write_jsonl(OUT_DIR / "policy_rows.jsonl", policy_rows)
    write_json(OUT_DIR / "metrics.json", metrics)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage, metrics))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
