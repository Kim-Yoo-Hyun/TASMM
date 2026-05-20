#!/usr/bin/env python3
"""Run Open3DSG with an in-memory object-candidate dump hook.

This script is mounted into the Open3DSG Docker runtime from research2. It
patches D3SSGModule in memory and never writes to the mounted Open3DSG source.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001 - best-effort JSON conversion.
            pass
    return value


def to_int(value: Any) -> int:
    return int(json_value(value))


def to_float(value: Any) -> float | None:
    value = json_value(value)
    try:
        out = float(value)
    except Exception:  # noqa: BLE001
        return None
    return out if math.isfinite(out) else None


def to_list(value: Any) -> list[Any] | None:
    if value is None:
        return None
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    return value if isinstance(value, list) else None


def scan_parts(scan_value: Any) -> tuple[str, int | None, str]:
    if isinstance(scan_value, (list, tuple)) and scan_value:
        scan_value = scan_value[0]
    raw_scan_id = str(scan_value)
    if "-" in raw_scan_id:
        scan_id, split = raw_scan_id.rsplit("-", 1)
        if split.isdigit():
            return scan_id, int(split), raw_scan_id
    return raw_scan_id, None, raw_scan_id


def label_from_id2name(id2name: Any, object_id: int) -> str | None:
    source = id2name
    if isinstance(source, (list, tuple)) and len(source) == 1:
        source = source[0]
    if isinstance(source, dict):
        for key in (object_id, str(object_id)):
            if key not in source:
                continue
            value = source[key]
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None
            return None if value is None else str(value)
    return None


def batch_value(eval_dict: dict[str, Any], key: str, bidx: int) -> Any:
    value = eval_dict.get(key)
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return None
        if len(value) > bidx:
            return value[bidx]
        return value[0]
    if hasattr(value, "shape") and getattr(value, "ndim", 0) > 0:
        try:
            return value[bidx]
        except Exception:  # noqa: BLE001
            return value
    return value


def init_state(module: Any) -> None:
    if getattr(module, "_m59_object_dump_initialized", False):
        return
    dump_jsonl = os.environ.get("OPEN3DSG_OBJECT_DUMP_JSONL")
    completed_jsonl = os.environ.get("OPEN3DSG_OBJECT_DUMP_COMPLETED_JSONL")
    manifest_json = os.environ.get("OPEN3DSG_OBJECT_DUMP_MANIFEST_JSON")
    module._m59_object_dump_initialized = True
    module._m59_object_dump_jsonl = dump_jsonl
    module._m59_object_dump_completed_jsonl = completed_jsonl or (dump_jsonl + ".completed.jsonl" if dump_jsonl else None)
    module._m59_object_dump_manifest_json = manifest_json or (dump_jsonl + ".manifest.json" if dump_jsonl else None)
    module._m59_object_dump_rows_written = 0
    module._m59_object_dump_completed_batches = set()
    module._m59_object_dump_seen_batches = 0
    module._m59_object_dump_topk = int(os.environ.get("OPEN3DSG_OBJECT_DUMP_TOPK", "20"))
    module._m59_object_dump_max_batches = int(os.environ.get("OPEN3DSG_OBJECT_DUMP_MAX_BATCHES", "0"))
    if not dump_jsonl:
        return
    Path(dump_jsonl).parent.mkdir(parents=True, exist_ok=True)
    Path(module._m59_object_dump_completed_jsonl).parent.mkdir(parents=True, exist_ok=True)
    resume = os.environ.get("OPEN3DSG_OBJECT_DUMP_RESUME", "0") == "1"
    if resume and Path(module._m59_object_dump_completed_jsonl).exists():
        with open(module._m59_object_dump_completed_jsonl, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                raw_scan_id = record.get("raw_scan_id")
                if raw_scan_id is not None:
                    module._m59_object_dump_completed_batches.add(str(raw_scan_id))
        if Path(dump_jsonl).exists():
            with open(dump_jsonl, "r", encoding="utf-8") as handle:
                module._m59_object_dump_rows_written = sum(1 for line in handle if line.strip())
        mode = "a"
    else:
        mode = "w"
    open(dump_jsonl, mode, encoding="utf-8").close()
    open(module._m59_object_dump_completed_jsonl, mode, encoding="utf-8").close()


def object_records(module: Any, eval_dict: dict[str, Any], bidx: int, start_row: int) -> tuple[str, str, list[dict[str, Any]]]:
    scan_values = eval_dict.get("scan_id", [])
    scan_value = scan_values[bidx] if isinstance(scan_values, (list, tuple)) and len(scan_values) > bidx else scan_values
    scan_id, subset_split_id, raw_scan_id = scan_parts(scan_value)
    subgraph_id = f"{scan_id}_{subset_split_id}" if subset_split_id is not None else raw_scan_id
    object_count = to_int(batch_value(eval_dict, "objects_count", bidx))
    object_ids_raw = batch_value(eval_dict, "objects_id", bidx)
    object_ids_list = to_list(object_ids_raw) or []
    object_ids = [to_int(value) for value in object_ids_list[:object_count]]
    id2name = eval_dict.get("id2name")
    if isinstance(id2name, (list, tuple)) and len(id2name) > bidx:
        id2name = id2name[bidx]

    probs = batch_value(eval_dict, "objects_probs", bidx)
    predicts = batch_value(eval_dict, "objects_predict", bidx)
    objects_cat = batch_value(eval_dict, "objects_cat", bidx)
    centers = batch_value(eval_dict, "objects_center", bidx)
    bboxes = batch_value(eval_dict, "objects_bbox", bidx)
    valid = batch_value(eval_dict, "objects_valid", bidx)
    probs_list = to_list(probs) or []
    predicts_list = to_list(predicts) or []
    cats_list = to_list(objects_cat) or []
    centers_list = to_list(centers) or []
    bboxes_list = to_list(bboxes) or []
    valid_list = to_list(valid) or []

    baseline_run_id = os.environ.get("OPEN3DSG_BASELINE_RUN_ID", module.hparams.get("run_name", "open3dsg"))
    checkpoint_path = os.environ.get("OPEN3DSG_CHECKPOINT")
    model_source_stage = os.environ.get("OPEN3DSG_MODEL_SOURCE_STAGE", "open3dsg_runtime_patch")
    topk = max(1, int(getattr(module, "_m59_object_dump_topk", 20)))
    vocab = list(getattr(module, "obj_class_dict", []))
    rows: list[dict[str, Any]] = []

    for object_node_index, object_id in enumerate(object_ids):
        node_probs = probs_list[object_node_index] if object_node_index < len(probs_list) else []
        node_predicts = predicts_list[object_node_index] if object_node_index < len(predicts_list) else []
        if not isinstance(node_predicts, list):
            node_predicts = [node_predicts]
        gt_cat = cats_list[object_node_index] if object_node_index < len(cats_list) else None
        gt_cat_int = to_int(gt_cat) if gt_cat is not None else None
        gt_label = vocab[gt_cat_int] if gt_cat_int is not None and 0 <= gt_cat_int < len(vocab) else None
        center = centers_list[object_node_index] if object_node_index < len(centers_list) else None
        bbox = bboxes_list[object_node_index] if object_node_index < len(bboxes_list) else None
        obj_valid = valid_list[object_node_index] if object_node_index < len(valid_list) else None
        for candidate_rank, candidate_index_raw in enumerate(node_predicts[:topk]):
            candidate_index = to_int(candidate_index_raw)
            candidate_label = vocab[candidate_index] if 0 <= candidate_index < len(vocab) else str(candidate_index)
            score = None
            if isinstance(node_probs, list) and 0 <= candidate_index < len(node_probs):
                score = to_float(node_probs[candidate_index])
            if score is None:
                continue
            record_id = f"{baseline_run_id}:{raw_scan_id}:{object_id}:{candidate_rank}:{candidate_index}"
            rows.append(
                {
                    "schema_version": "open3dsg_object_candidate_jsonl_v0",
                    "record_type": "open3dsg_object_candidate",
                    "object_candidate_record_id": record_id,
                    "baseline_run_id": baseline_run_id,
                    "checkpoint_path": checkpoint_path,
                    "model_source_stage": model_source_stage,
                    "scan_id": scan_id,
                    "raw_scan_id": raw_scan_id,
                    "subset_split_id": subset_split_id,
                    "subgraph_id": subgraph_id,
                    "object_id": object_id,
                    "object_node_index": object_node_index,
                    "object_count": object_count,
                    "candidate_label": candidate_label,
                    "candidate_label_index": candidate_index,
                    "candidate_rank": candidate_rank,
                    "candidate_score": score,
                    "score_type": "open3dsg_objects_probs",
                    "candidate_vocab": "Open3DSG_R3Scan_classes",
                    "object_vocab_size": len(vocab),
                    "bbox_or_center": {
                        "center": center,
                        "bbox": bbox,
                        "geometry_source": "Open3DSG data_dict",
                    },
                    "source_tensors": {
                        "objects_probs": [object_node_index, candidate_index],
                        "objects_predict": [object_node_index, candidate_rank],
                        "objects_valid": obj_valid,
                    },
                    "gt_object_label": gt_label,
                    "gt_object_category_id": gt_cat_int,
                    "id2name_label": label_from_id2name(id2name, object_id),
                    "objects_cat_raw": gt_cat_int,
                    "row_index": start_row + len(rows),
                }
            )
    return raw_scan_id, subgraph_id, rows


def export_eval_dict(module: Any, eval_dict: dict[str, Any]) -> None:
    init_state(module)
    dump_jsonl = getattr(module, "_m59_object_dump_jsonl", None)
    if not dump_jsonl:
        return
    scan_values = eval_dict.get("scan_id", [])
    batch_size = len(scan_values) if isinstance(scan_values, (list, tuple)) else 1
    with open(dump_jsonl, "a", encoding="utf-8") as raw_handle, open(module._m59_object_dump_completed_jsonl, "a", encoding="utf-8") as completed_handle:
        for bidx in range(batch_size):
            start_row = module._m59_object_dump_rows_written
            raw_scan_id, subgraph_id, rows = object_records(module, eval_dict, bidx, start_row)
            if raw_scan_id in module._m59_object_dump_completed_batches:
                continue
            for row in rows:
                raw_handle.write(json.dumps(row, sort_keys=True))
                raw_handle.write("\n")
                module._m59_object_dump_rows_written += 1
            raw_handle.flush()
            os.fsync(raw_handle.fileno())
            completion = {
                "schema_version": "open3dsg_object_candidate_stream_completion_v0",
                "raw_scan_id": raw_scan_id,
                "subgraph_id": subgraph_id,
                "rows_start": start_row,
                "rows_end": module._m59_object_dump_rows_written,
                "rows_written": module._m59_object_dump_rows_written - start_row,
                "completed_at": utc_now(),
            }
            completed_handle.write(json.dumps(completion, sort_keys=True))
            completed_handle.write("\n")
            completed_handle.flush()
            os.fsync(completed_handle.fileno())
            module._m59_object_dump_completed_batches.add(raw_scan_id)
            module._m59_object_dump_seen_batches += 1
            print(
                "M59 object dump wrote batch "
                f"raw_scan_id={raw_scan_id} rows={completion['rows_written']} "
                f"total_rows={module._m59_object_dump_rows_written}",
                flush=True,
            )


def finalize(module: Any, status: str = "object_candidate_stream_complete") -> None:
    init_state(module)
    manifest_json = getattr(module, "_m59_object_dump_manifest_json", None)
    if not manifest_json:
        return
    manifest = {
        "schema_version": "open3dsg_object_candidate_stream_manifest_v0",
        "status": status,
        "object_dump_jsonl": getattr(module, "_m59_object_dump_jsonl", None),
        "completed_jsonl": getattr(module, "_m59_object_dump_completed_jsonl", None),
        "rows_written": getattr(module, "_m59_object_dump_rows_written", 0),
        "completed_batches": len(getattr(module, "_m59_object_dump_completed_batches", set())),
        "topk": getattr(module, "_m59_object_dump_topk", None),
        "created_at": utc_now(),
    }
    Path(manifest_json).parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_json, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"M59 object dump finalized rows={manifest['rows_written']} batches={manifest['completed_batches']}", flush=True)


def patch_trainer() -> None:
    from open3dsg.scripts import trainer as trainer_module

    original_test_step = trainer_module.D3SSGModule.test_step
    original_on_test_epoch_end = trainer_module.D3SSGModule.on_test_epoch_end

    def patched_test_step(self: Any, data_dict: dict[str, Any], batch_ixd: int) -> Any:
        before_len = len(getattr(self, "test_step_outputs", []))
        result = original_test_step(self, data_dict, batch_ixd)
        if os.environ.get("OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES", "0") != "1":
            return result
        outputs = getattr(self, "test_step_outputs", [])
        if len(outputs) <= before_len:
            return result
        eval_dict = outputs[-1]
        if "objects_center" not in eval_dict and "objects_center" in data_dict:
            eval_dict["objects_center"] = data_dict["objects_center"].detach().cpu()
        if "objects_bbox" not in eval_dict and "objects_bbox" in data_dict:
            eval_dict["objects_bbox"] = data_dict["objects_bbox"].detach().cpu()
        export_eval_dict(self, eval_dict)
        max_batches = int(os.environ.get("OPEN3DSG_OBJECT_DUMP_MAX_BATCHES", "0"))
        if max_batches > 0 and getattr(self, "_m59_object_dump_seen_batches", 0) >= max_batches:
            finalize(self, status="object_candidate_stream_complete_max_batches")
            raise SystemExit(0)
        return result

    def patched_on_test_epoch_end(self: Any) -> Any:
        if os.environ.get("OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES", "0") == "1":
            finalize(self)
            if os.environ.get("OPEN3DSG_OBJECT_DUMP_EXIT_AFTER_WRITE", "0") == "1":
                raise SystemExit(0)
        return original_on_test_epoch_end(self)

    trainer_module.D3SSGModule.test_step = patched_test_step
    trainer_module.D3SSGModule.on_test_epoch_end = patched_on_test_epoch_end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.command[0] != "--":
        raise SystemExit("Expected command after --")
    command = args.command[1:]
    if len(command) < 2 or command[0] != "python":
        raise SystemExit("Expected python command after --")
    source_root = Path(args.source_root).resolve()
    sys.path.insert(0, str(source_root))
    patch_trainer()
    script = command[1]
    sys.argv = command[1:]
    runpy.run_path(script, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
