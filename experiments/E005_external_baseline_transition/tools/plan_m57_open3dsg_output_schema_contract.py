#!/usr/bin/env python3
"""Inspect Open3DSG staged output schemas and define query-conversion contract."""

from __future__ import annotations

import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M57_output_schema_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M57_open3dsg_output_schema_contract_v0"
M56_DIR = EXP_ROOT / "artifacts" / "E005-M56_robustness_denominator_open3dsg_audit_v0"
VERSION = "e005_m57_open3dsg_output_schema_contract_v0"


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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(STAGED_ROOT))
    except ValueError:
        return str(path)


def safe_list(path: Path, pattern: str, limit: int = 200) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.rglob(pattern))[:limit]


def summarize_value(value: Any, depth: int = 0) -> dict[str, Any]:
    summary: dict[str, Any] = {"type": type(value).__name__}
    if hasattr(value, "shape"):
        try:
            summary["shape"] = [int(x) for x in value.shape]
        except Exception:
            summary["shape"] = str(value.shape)
    if hasattr(value, "dtype"):
        summary["dtype"] = str(value.dtype)
    if isinstance(value, dict):
        summary["len"] = len(value)
        if depth < 1:
            summary["sample_keys"] = [str(k) for k in list(value.keys())[:12]]
    elif isinstance(value, (list, tuple)):
        summary["len"] = len(value)
        if value and depth < 1:
            summary["first"] = summarize_value(value[0], depth + 1)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        summary["value"] = value
    return summary


def inspect_pickle(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "exists": path.exists(), "load_ok": False}
    if not path.exists():
        return row
    try:
        with path.open("rb") as handle:
            obj = pickle.load(handle)
        row["load_ok"] = True
        row["root"] = summarize_value(obj)
        if isinstance(obj, dict):
            row["keys"] = [str(k) for k in list(obj.keys())[:40]]
            row["key_summaries"] = {str(k): summarize_value(obj[k]) for k in list(obj.keys())[:24]}
    except Exception as exc:  # noqa: BLE001 - inspection script records schema failures.
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def inspect_torch_file(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "exists": path.exists(), "load_ok": False}
    if not path.exists():
        return row
    try:
        import torch  # type: ignore

        obj = torch.load(path, map_location="cpu")
        row["load_ok"] = True
        row["root"] = summarize_value(obj)
        if isinstance(obj, dict):
            row["keys"] = [str(k) for k in list(obj.keys())[:40]]
            row["key_summaries"] = {str(k): summarize_value(obj[k]) for k in list(obj.keys())[:24]}
    except Exception as exc:  # noqa: BLE001 - optional binary inspection.
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def inspect_json(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "exists": path.exists(), "load_ok": False}
    if not path.exists():
        return row
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        row["load_ok"] = True
        row["root"] = summarize_value(payload)
        if isinstance(payload, dict):
            row["keys"] = [str(k) for k in list(payload.keys())[:40]]
            row["sample_items"] = [
                {"key": str(k), "value": payload[k]} for k in list(payload.keys())[:8]
            ]
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def source_hook_audit(source_file: Path) -> dict[str, Any]:
    text = source_file.read_text(encoding="utf-8", errors="replace") if source_file.exists() else ""
    return {
        "path": rel(source_file),
        "exists": source_file.exists(),
        "has_raw_dump_jsonl_env": "OPEN3DSG_RAW_DUMP_JSONL" in text,
        "has_stream_batch_env": "OPEN3DSG_RAW_DUMP_STREAM_BATCHES" in text,
        "has_resume_env": "OPEN3DSG_RAW_DUMP_RESUME" in text,
        "has_raw_prediction_record_type": "open3dsg_raw_prediction" in text,
        "exports_relation_predicate_scores": "predicate_scores" in text,
        "exports_object_probability_rows": "object_scores" in text or "objects_scores" in text,
        "exports_objects_probs_tensor_source": "objects_probs" in text,
        "exports_objects_predict_tensor_source": "objects_predict" in text,
    }


def collect_inventory() -> dict[str, Any]:
    h001 = STAGED_ROOT / "h001_runtime"
    train = STAGED_ROOT / "training_repro"
    output = h001 / "output"
    opensg = output / "datasets" / "OpenSG_3RScan"
    features = output / "features" / "clip_features_h001_eval_blip_top5_scales3"
    classwise = h001 / "classwise_eval" / "_2026-05-18-08-44"
    source_file = h001 / "source" / "open3dsg_source" / "open3dsg" / "scripts" / "trainer.py"
    preprocessed = safe_list(opensg / "preprocessed", "data_dict_*.pkl", limit=100000)
    views = safe_list(opensg / "views", "*_object2image.pkl", limit=100000)
    feature_pts = safe_list(features, "*.pt", limit=100000)
    checkpoints = safe_list(train / "mlops" / "opensg" / "mlflow", "*.ckpt", limit=100000)
    classwise_jsons = sorted(classwise.glob("*.json")) if classwise.exists() else []
    return {
        "staged_root": str(STAGED_ROOT),
        "local_output_dir": str(LOCAL_DATA_DIR),
        "read_only_source_policy": {
            "source_modified": False,
            "write_target_for_derived_data": str(LOCAL_DATA_DIR),
            "docker_mount_rule": f"-v {STAGED_ROOT}:/data/Open3DSG_staged:ro",
        },
        "counts": {
            "preprocessed_data_dict_pkls": len(preprocessed),
            "object2image_pkls": len(views),
            "feature_pt_files": len(feature_pts),
            "classwise_eval_jsons": len(classwise_jsons),
            "mlflow_checkpoints": len(checkpoints),
        },
        "sample_paths": {
            "preprocessed": [rel(path) for path in preprocessed[:5]],
            "object2image": [rel(path) for path in views[:5]],
            "feature_pt": [rel(path) for path in feature_pts[:5]],
            "classwise_eval_json": [rel(path) for path in classwise_jsons[:5]],
            "checkpoint": [rel(path) for path in checkpoints[:5]],
        },
        "source_hook_audit": source_hook_audit(source_file),
    }


def collect_schema_samples() -> dict[str, Any]:
    h001 = STAGED_ROOT / "h001_runtime"
    opensg = h001 / "output" / "datasets" / "OpenSG_3RScan"
    features = h001 / "output" / "features" / "clip_features_h001_eval_blip_top5_scales3"
    classwise = h001 / "classwise_eval" / "_2026-05-18-08-44"
    preprocessed = safe_list(opensg / "preprocessed", "data_dict_*.pkl", limit=3)
    views = safe_list(opensg / "views", "*_object2image.pkl", limit=2)
    feature_pts = safe_list(features, "*.pt", limit=2)
    classwise_jsons = sorted(classwise.glob("*.json"))[:4] if classwise.exists() else []
    samples = {
        "preprocessed_samples": [inspect_pickle(path) for path in preprocessed],
        "object2image_samples": [inspect_pickle(path) for path in views],
        "feature_pt_samples": [inspect_torch_file(path) for path in feature_pts],
        "classwise_eval_samples": [inspect_json(path) for path in classwise_jsons],
    }
    binary_samples = read_json(LOCAL_DATA_DIR / "binary_schema_samples.json")
    if binary_samples:
        samples["dependency_runtime_binary_samples"] = binary_samples
    return samples


def build_contract(inventory: dict[str, Any], samples: dict[str, Any]) -> dict[str, Any]:
    hook = inventory["source_hook_audit"]
    binary_samples = samples.get("dependency_runtime_binary_samples", {})
    sample_preprocessed = binary_samples.get("preprocessed_samples") or samples.get("preprocessed_samples", [])
    first_preprocessed_keys = sample_preprocessed[0].get("keys", []) if sample_preprocessed else []
    binary_ready = binary_samples.get("status") == "binary_schema_samples_ready"
    feature_pt_ready = any(row.get("load_ok") for row in binary_samples.get("feature_pt_samples", []))
    pkl_ready = any(row.get("load_ok") for row in binary_samples.get("preprocessed_samples", []))
    pkl_key_hints = sorted(
        {
            key
            for row in binary_samples.get("preprocessed_samples", [])
            for key in row.get("byte_scan_key_hints", [])
        }
    )
    object_candidate_ready_from_existing_dump = bool(hook["exports_object_probability_rows"])
    relation_dump_ready = bool(hook["has_raw_prediction_record_type"] and hook["exports_relation_predicate_scores"])
    return {
        "contract_id": "open3dsg_query_conversion_contract_v0",
        "source_policy": inventory["read_only_source_policy"],
        "available_sources": [
            {
                "source_id": "classwise_eval_metrics",
                "status": "aggregate_only_not_query_convertible",
                "why": "Contains classwise recall/mRecall summaries, not per-query object candidates.",
            },
            {
                "source_id": "preprocessed_subgraph_pkls",
                "status": "geometry_and_gt_join_source_binary_env_mismatch",
                "sample_keys": first_preprocessed_keys,
                "byte_scan_key_hints": pkl_key_hints,
                "why": "Provides object ids, graph edges, object centers/bboxes, and GT subgraph structure needed for joins.",
            },
            {
                "source_id": "existing_h001_raw_dump_hook",
                "status": "relation_score_dump_ready_object_score_extension_needed",
                "why": "The source can stream relation predicate scores, but object-search requires per-object class scores or candidate rows.",
            },
            {
                "source_id": "trained_checkpoints_and_features",
                "status": "runtime_export_feasible_needs_docker_command",
                "why": "Checkpoints and BLIP/OpenSeg feature artifacts exist, so a read-only runtime export can write derived rows under research2/local_dataset.",
            },
        ],
        "required_output_schemas": [
            {
                "schema_id": "open3dsg_object_candidate_jsonl_v0",
                "required_fields": [
                    "scan_id",
                    "subset_split_id",
                    "subgraph_id",
                    "object_id",
                    "object_label_query",
                    "open3dsg_object_label_prediction",
                    "object_score",
                    "bbox_or_center",
                    "score_type",
                    "source_checkpoint",
                ],
                "purpose": "Convert Open3DSG object predictions into H001 object-search candidate rows.",
            },
            {
                "schema_id": "open3dsg_relation_prediction_jsonl_v0",
                "required_fields": [
                    "scan_id",
                    "subset_split_id",
                    "subgraph_id",
                    "subject_id",
                    "object_id",
                    "predicate_scores",
                    "source_checkpoint",
                ],
                "purpose": "Optional relation-aware diagnostic table; not sufficient alone for object search.",
            },
        ],
        "conversion_steps": [
            "Run Open3DSG inference/export in Docker with Open3DSG_staged mounted read-only.",
            "Write raw dump/object candidate rows to /home/yoohyun/research2/local_dataset/Open3DSG_bridge/.",
            "Join object candidate rows to H001 query rows by scan_id/subset_split_id/object_id and target label.",
            "Evaluate strict bbox/center and relaxed bbox metrics under the same M38 or direct-bridge denominator.",
            "Keep relation-only metrics separate from object-search metrics.",
        ],
        "readiness": {
            "schema_inspection_ready": True,
            "dependency_runtime_binary_schema_ready": binary_ready,
            "dependency_runtime_feature_pt_schema_ready": feature_pt_ready,
            "dependency_runtime_preprocessed_pkl_unpickle_ready": pkl_ready,
            "existing_data_modified": False,
            "relation_raw_dump_ready": relation_dump_ready,
            "object_candidate_dump_ready": object_candidate_ready_from_existing_dump,
            "query_level_conversion_ready_without_new_export": False,
            "m58_recommended": True,
        },
        "blocked_claims": [
            "Open3DSG query-level object-search performance",
            "final real RGB-D/open-vocabulary robustness",
            "real navigation SR/SPL",
        ],
    }


def build_next_actions(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_next_unit": "E005-M58 Open3DSG object-candidate dump/export smoke plan",
        "reason": [
            "Existing staged aggregate eval is not query-convertible.",
            "The H001 raw dump hook can export relation scores, but object-search needs object candidate scores.",
            "A Docker read-only run should write all derived rows under /home/yoohyun/research2/local_dataset/Open3DSG_bridge/.",
        ],
        "m58_required_outputs": [
            "Docker command contract with Open3DSG_staged mounted read-only",
            "object candidate JSONL schema",
            "raw dump output path under research2/local_dataset/Open3DSG_bridge/",
            "lightweight verifier for row counts, required fields, and no writes under source staged path",
        ],
        "do_not_do_yet": [
            "Do not modify Open3DSG_staged.",
            "Do not claim Open3DSG baseline performance before object-candidate rows exist.",
            "Do not merge relation-only recall with object-search success metrics.",
        ],
        "contract_readiness": contract["readiness"],
    }


def build_report(coverage: dict[str, Any], contract: dict[str, Any], next_actions: dict[str, Any]) -> str:
    counts = coverage["counts"]
    readiness = contract["readiness"]
    return "\n".join(
        [
            "# E005-M57 Open3DSG Output Schema Contract",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- Read-only source: `{coverage['staged_root']}`.",
            f"- Derived data output: `{coverage['local_output_dir']}`.",
            f"- Existing source data modified: {coverage['existing_open3dsg_data_modified']}.",
            f"- Preprocessed `data_dict_*.pkl`: {counts['preprocessed_data_dict_pkls']}.",
            f"- `object2image` `.pkl`: {counts['object2image_pkls']}.",
            f"- Feature `.pt` files: {counts['feature_pt_files']}.",
            f"- MLflow checkpoints: {counts['mlflow_checkpoints']}.",
            f"- Dependency-runtime binary schema ready: {contract['readiness']['dependency_runtime_binary_schema_ready']}.",
            f"- Feature `.pt` load ready in dependency runtime: {contract['readiness']['dependency_runtime_feature_pt_schema_ready']}.",
            f"- Preprocessed `.pkl` unpickle ready in dependency runtime: {contract['readiness']['dependency_runtime_preprocessed_pkl_unpickle_ready']}.",
            "",
            "## Contract Decision",
            "",
            f"- Schema inspection ready: {readiness['schema_inspection_ready']}.",
            f"- Relation raw dump ready: {readiness['relation_raw_dump_ready']}.",
            f"- Object candidate dump ready: {readiness['object_candidate_dump_ready']}.",
            f"- Query-level conversion ready without new export: {readiness['query_level_conversion_ready_without_new_export']}.",
            "- Current aggregate eval metrics are not query-convertible.",
            "- Existing H001 raw dump hook is relation-score oriented; object-search baseline needs object candidate rows.",
            "",
            "## Next Action",
            "",
            f"- {next_actions['selected_next_unit']}.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    m56 = read_json(M56_DIR / "coverage.json")
    if m56.get("status") != "e005_m56_robustness_denominator_open3dsg_audit_ready":
        raise RuntimeError(f"M56 is not ready: {m56.get('status')}")
    if not STAGED_ROOT.exists():
        raise RuntimeError(f"Missing read-only source: {STAGED_ROOT}")

    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    inventory = collect_inventory()
    samples = collect_schema_samples()
    contract = build_contract(inventory, samples)
    next_actions = build_next_actions(contract)
    coverage = {
        "status": "e005_m57_open3dsg_output_schema_contract_ready_object_candidate_export_needed",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "staged_root": str(STAGED_ROOT),
        "local_output_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "existing_open3dsg_data_modified": False,
        "data_outputs_written_under_research2_local_dataset": True,
        "counts": inventory["counts"],
        "source_hook_audit": inventory["source_hook_audit"],
        "dependency_runtime_binary_schema_ready": contract["readiness"]["dependency_runtime_binary_schema_ready"],
        "query_level_conversion_ready": contract["readiness"]["query_level_conversion_ready_without_new_export"],
        "object_candidate_export_needed": not contract["readiness"]["object_candidate_dump_ready"],
        "selected_next_unit": next_actions["selected_next_unit"],
    }

    write_json(LOCAL_DATA_DIR / "schema_inventory.json", inventory)
    write_json(LOCAL_DATA_DIR / "schema_samples.json", samples)
    write_json(LOCAL_DATA_DIR / "conversion_contract.json", contract)
    write_json(LOCAL_DATA_DIR / "next_actions.json", next_actions)
    write_jsonl(
        LOCAL_DATA_DIR / "source_schema_rows.jsonl",
        [
            {"row_type": "inventory", "payload": inventory["counts"]},
            {"row_type": "source_hook_audit", "payload": inventory["source_hook_audit"]},
            {"row_type": "readiness", "payload": contract["readiness"]},
        ],
    )

    pointer = {
        "status": coverage["status"],
        "local_data_dir": str(LOCAL_DATA_DIR),
        "files": [
            "schema_inventory.json",
            "schema_samples.json",
            "conversion_contract.json",
            "next_actions.json",
            "source_schema_rows.jsonl",
        ],
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "artifact_pointer.json", pointer)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, contract, next_actions))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
