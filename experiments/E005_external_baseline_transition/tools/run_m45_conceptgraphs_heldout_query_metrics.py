#!/usr/bin/env python3
"""Convert heldout ConceptGraphs outputs into query-level metrics."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
TOOLS_ROOT = EXP_ROOT / "tools"
DEFAULT_CONTRACT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_query_metric_v0"
M43_VERIFY_DIR = EXP_ROOT / "artifacts" / "E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0" / "verification"
SCANS_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
OBJECTS_PATH = ROOT / "local_dataset" / "3DSSG" / "objects.json"
VERSION = "e005_m45_conceptgraphs_heldout_query_metric_v0"


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


def load_m35_module() -> Any:
    path = TOOLS_ROOT / "run_m35_conceptgraphs_4scan_query_metrics.py"
    spec = importlib.util.spec_from_file_location("e005_m35_reuse", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load M35 helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["e005_m35_reuse"] = module
    spec.loader.exec_module(module)
    return module


def object_scan_index(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    return {str(row["scan"]): row for row in payload.get("scans", [])}


def semseg_index(scan_dir: Path) -> dict[str, dict[str, Any]]:
    path = scan_dir / "semseg.v2.json"
    if not path.exists():
        return {}
    payload = read_json(path)
    return {str(row.get("objectId", row.get("id"))): row for row in payload.get("segGroups", [])}


def object_extent(semseg_group: dict[str, Any] | None) -> dict[str, Any]:
    if not semseg_group:
        return {
            "centroid_world_m": None,
            "obb_axes_lengths_m": None,
            "segments_count": 0,
            "semseg_present": False,
        }
    obb = semseg_group.get("obb", {})
    return {
        "centroid_world_m": obb.get("centroid"),
        "obb_axes_lengths_m": obb.get("axesLengths"),
        "segments_count": len(semseg_group.get("segments", [])),
        "semseg_present": True,
    }


def build_target_rows(query_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    objects_by_scan = object_scan_index(OBJECTS_PATH)
    wanted_by_scan: dict[str, set[str]] = {}
    linked_by_target: dict[str, list[dict[str, Any]]] = {}
    for row in query_rows:
        scan_id = str(row["current_rescan_id"])
        object_id = str(row["object_instance_id_rescan"])
        target_uid = str(row["target_uid"])
        wanted_by_scan.setdefault(scan_id, set()).add(object_id)
        linked_by_target.setdefault(target_uid, []).append(row)

    rows: list[dict[str, Any]] = []
    for scan_id, wanted_object_ids in sorted(wanted_by_scan.items()):
        scan_dir = SCANS_ROOT / scan_id
        semseg_by_id = semseg_index(scan_dir)
        object_rows = {
            str(obj.get("id")): obj
            for obj in objects_by_scan.get(scan_id, {}).get("objects", [])
            if str(obj.get("id")) in wanted_object_ids
        }
        for object_id in sorted(wanted_object_ids, key=lambda value: int(value) if value.isdigit() else value):
            target_uid = f"{scan_id}:{object_id}"
            obj = object_rows.get(object_id, {})
            linked_queries = linked_by_target.get(target_uid, [])
            extent = object_extent(semseg_by_id.get(object_id))
            rows.append(
                {
                    "target_uid": target_uid,
                    "scan_id": scan_id,
                    "object_instance_id": object_id,
                    "label_canonical": str(obj.get("label") or (linked_queries[0]["label_canonical"] if linked_queries else "")),
                    "source_objects_json": str(OBJECTS_PATH),
                    "source_semseg_json": str(scan_dir / "semseg.v2.json"),
                    "m45_version": VERSION,
                    "bridge_query_row_uids": [row["row_uid"] for row in linked_queries],
                    "bridge_query_task_contexts": sorted({str(row["task_context_id"]) for row in linked_queries}),
                    "is_bridge_query_target": bool(linked_queries),
                    **extent,
                }
            )
    return rows


def remap_candidate_suite(candidate_rows: list[dict[str, Any]], suite_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row.get("query_suite") != "expanded_m73":
            continue
        rows.append({**row, "query_suite": suite_name})
    return rows


def normalize_version_key(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        current = dict(row)
        current.pop("m35_version", None)
        current["m45_version"] = VERSION
        normalized.append(current)
    return normalized


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def failure_class(metrics: dict[str, Any]) -> str:
    if metrics["strict_bbox_hit_rows"] > 0:
        return "strict_bbox_hit_available"
    if metrics["relaxed_bbox_1m_hit_rows"] > 0:
        return "strict_threshold_miss_relaxed_bbox_hit"
    if metrics["candidate_rows"] > 0:
        return "map_candidate_target_miss"
    return "no_map_candidates"


def build_report(coverage: dict[str, Any], metrics: dict[str, Any]) -> str:
    suite_name = coverage["query_suite"]
    suite = metrics["suites"][suite_name]
    strict_bbox = suite["policy_metrics"]["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    relaxed_bbox = suite["policy_metrics"]["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]
    centroid = suite["policy_metrics"]["conceptgraphs_clip_rank_centroid_strict_top5_v0"]
    return "\n".join(
        [
            f"# E005-M45 ConceptGraphs Heldout Query Metric: {coverage['batch_id']}",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Batch id: `{coverage['batch_id']}`.",
            f"- Query suite: `{suite_name}`.",
            f"- Scans: {coverage['scan_count']}.",
            f"- Query rows: {suite['query_rows']}.",
            f"- Target uids: {suite['target_uid_count']}.",
            f"- Object rows: {coverage['object_rows']}.",
            f"- Candidate rows: {suite['candidate_rows']}.",
            f"- Strict center top5 success rows/rate: {centroid['query_bridge_success_rows']} / {centroid['query_bridge_success_rate']}.",
            f"- Strict bbox top5 success rows/rate: {strict_bbox['query_bridge_success_rows']} / {strict_bbox['query_bridge_success_rate']}.",
            f"- Relaxed bbox 1m top3 success rows/rate: {relaxed_bbox['query_bridge_success_rows']} / {relaxed_bbox['query_bridge_success_rate']}.",
            f"- Failure class: `{coverage['failure_class']}`.",
            "",
            "## Claim Boundary",
            "",
            "- M45 is a 3-scan heldout batch diagnostic, not the final 9-scan heldout result.",
            "- Strict 0.5m bbox, strict 0.5m centroid, and relaxed 1.0m bbox results must stay separate.",
            "- This does not support final real RGB-D/open-vocabulary robustness or real navigation `SR` / `SPL`.",
            "",
            "## Agent Inference",
            "",
            "- This batch is useful for transfer diagnostics because its target labels include labels outside the 4-scan dev metric path.",
            "- The next defensible step is either finish the remaining heldout batches or compare this batch against the method-side policy under the same query schema.",
            "",
        ]
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    suite_name = f"heldout_m38_{args.batch_id.replace('heldout_', '')}"
    query_rows = read_jsonl(args.contract_dir / f"{args.batch_id}_query_rows.jsonl")
    m43_verify = read_json(M43_VERIFY_DIR / args.batch_id / "coverage.json")
    scan_ids = [str(row["scan_id"]) for row in m43_verify.get("inventory", []) if row.get("full_pcd_post_exists")]
    target_rows = build_target_rows(query_rows)
    target_by_uid = {str(row["target_uid"]): row for row in target_rows}
    m35 = load_m35_module()
    m35.OUT_DIR = out_dir
    m35.VERSION = VERSION
    m35.CONTAINER_NAME = f"e005_m45_conceptgraphs_heldout_query_metrics_{args.batch_id}"

    errors: list[str] = []
    if m43_verify.get("status") != "e005_m43_conceptgraphs_heldout_runtime_batch_outputs_ready":
        errors.append(f"m43_outputs_not_ready:{m43_verify.get('status')}")
    if not query_rows:
        errors.append("missing_query_rows")
    missing_targets = sorted({str(row["target_uid"]) for row in query_rows if str(row["target_uid"]) not in target_by_uid})
    if missing_targets:
        errors.append(f"missing_targets:{missing_targets[:5]}")
    missing_centroids = sorted(row["target_uid"] for row in target_rows if not row.get("centroid_world_m"))
    if missing_centroids:
        errors.append(f"missing_target_centroids:{missing_centroids[:5]}")
    if not scan_ids:
        errors.append("missing_ready_scan_ids")

    if errors:
        coverage = {
            "status": "e005_m45_conceptgraphs_heldout_query_metric_blocked",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "batch_id": args.batch_id,
            "query_suite": suite_name,
            "errors": errors,
            "next_recommended_unit": "Repair M43/M45 query target inputs",
        }
        write_json(out_dir / f"coverage_{args.batch_id}.json", coverage)
        write_json(out_dir / "coverage.json", coverage)
        write_jsonl(out_dir / f"target_rows_{args.batch_id}.jsonl", target_rows)
        write_text(out_dir / f"report_{args.batch_id}.md", f"# E005-M45 ConceptGraphs Heldout Query Metric: {args.batch_id}\n\nBlocked.\n")
        write_text(out_dir / "report.md", f"# E005-M45 ConceptGraphs Heldout Query Metric: {args.batch_id}\n\nBlocked.\n")
        return coverage

    docker_meta, result = m35.docker_export(scan_ids, [], query_rows)
    write_json(out_dir / "docker_meta.json", docker_meta)
    if not result:
        coverage = {
            "status": "e005_m45_conceptgraphs_heldout_query_metric_failed",
            "version": VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "batch_id": args.batch_id,
            "query_suite": suite_name,
            "docker_returncode": docker_meta.get("returncode"),
            "next_recommended_unit": "Inspect E005-M45 docker_meta stderr/stdout tail",
        }
        write_json(out_dir / f"coverage_{args.batch_id}.json", coverage)
        write_json(out_dir / "coverage.json", coverage)
        write_text(out_dir / f"report_{args.batch_id}.md", f"# E005-M45 ConceptGraphs Heldout Query Metric: {args.batch_id}\n\nFailed.\n")
        write_text(out_dir / "report.md", f"# E005-M45 ConceptGraphs Heldout Query Metric: {args.batch_id}\n\nFailed.\n")
        return coverage

    object_rows = result["object_rows"]
    candidate_rows = remap_candidate_suite(result["candidate_rows"], suite_name)
    eval_rows = normalize_version_key(m35.build_candidate_eval_rows(candidate_rows, target_by_uid))
    policy_rows = normalize_version_key(m35.build_policy_rows(eval_rows))
    suite_metrics = m35.build_suite_metrics(eval_rows, policy_rows, suite_name)
    metrics = {"suites": {suite_name: suite_metrics}}
    failure = failure_class(suite_metrics)
    strict = suite_metrics["policy_metrics"]["conceptgraphs_clip_rank_bbox_strict_top5_v0"]
    relaxed = suite_metrics["policy_metrics"]["conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0"]
    status = (
        "e005_m45_conceptgraphs_heldout_query_metric_ready_with_strict_hits"
        if failure == "strict_bbox_hit_available"
        else "e005_m45_conceptgraphs_heldout_query_metric_ready_near_hit_only"
        if failure == "strict_threshold_miss_relaxed_bbox_hit"
        else "e005_m45_conceptgraphs_heldout_query_metric_ready_target_miss"
    )
    label_counts = dict(sorted(Counter(str(row["label_canonical"]) for row in query_rows).items()))
    coverage = {
        "status": status,
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_id": args.batch_id,
        "query_suite": suite_name,
        "m43_status": m43_verify.get("status"),
        "scan_count": len(scan_ids),
        "scan_ids": scan_ids,
        "query_rows": len(query_rows),
        "target_uid_count": len({row["target_uid"] for row in query_rows}),
        "label_counts": label_counts,
        "object_rows": len(object_rows),
        "candidate_rows": len(candidate_rows),
        "failure_class": failure,
        "strict_bbox_top5_success_rows": strict["query_bridge_success_rows"],
        "strict_bbox_top5_success_rate": strict["query_bridge_success_rate"],
        "relaxed_bbox_1m_top3_success_rows": relaxed["query_bridge_success_rows"],
        "relaxed_bbox_1m_top3_success_rate": relaxed["query_bridge_success_rate"],
        "heldout_batch_only": True,
        "heldout_all_query_rows": read_json(args.contract_dir / "coverage.json").get("heldout_all_query_rows"),
        "paper_table_claim_ready": False,
        "final_baseline_claim_ready": False,
        "real_navigation_sr_spl_ready": False,
        "next_recommended_unit": "E005-M46 ConceptGraphs heldout metric interpretation / remaining batch decision",
    }

    write_jsonl(out_dir / f"target_rows_{args.batch_id}.jsonl", target_rows)
    write_jsonl(out_dir / f"object_rows_{args.batch_id}.jsonl", object_rows)
    write_jsonl(out_dir / f"candidate_rows_{args.batch_id}.jsonl", candidate_rows)
    write_jsonl(out_dir / f"candidate_eval_rows_{args.batch_id}.jsonl", eval_rows)
    write_jsonl(out_dir / f"policy_rows_{args.batch_id}.jsonl", policy_rows)
    write_json(out_dir / f"metrics_{args.batch_id}.json", metrics)
    write_json(out_dir / f"coverage_{args.batch_id}.json", coverage)
    write_text(out_dir / f"report_{args.batch_id}.md", build_report(coverage, metrics))
    write_json(out_dir / "coverage.json", coverage)
    write_text(out_dir / "report.md", build_report(coverage, metrics))
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="heldout_b01")
    parser.add_argument("--contract-dir", type=Path, default=DEFAULT_CONTRACT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    coverage = run(args)
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
