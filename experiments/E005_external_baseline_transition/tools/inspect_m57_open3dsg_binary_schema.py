#!/usr/bin/env python3
"""Inspect binary Open3DSG schema samples inside a dependency-ready runtime."""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path
from typing import Any


STAGED_ROOT = Path("/data/Open3DSG_staged")
OUT_DIR = Path("/out")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(STAGED_ROOT))
    except ValueError:
        return str(path)


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
            summary["sample_keys"] = [str(k) for k in list(value.keys())[:20]]
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
            row["keys"] = [str(k) for k in list(obj.keys())[:50]]
            row["key_summaries"] = {str(k): summarize_value(obj[k]) for k in list(obj.keys())[:30]}
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
        try:
            blob = path.read_bytes()
            tokens = sorted(set(token.decode("utf-8", errors="ignore") for token in re.findall(rb"[A-Za-z_][A-Za-z0-9_]{2,}", blob)))
            likely = [
                token
                for token in tokens
                if token
                in {
                    "scan_id",
                    "objects_id",
                    "objects_cat",
                    "objects_count",
                    "objects_center",
                    "objects_bbox",
                    "edges",
                    "pairs",
                    "triples",
                    "predicate_count",
                    "predicate_edges",
                    "predicate_dist",
                    "predicate_min_dist",
                    "id2name",
                }
            ]
            row["byte_scan_key_hints"] = likely
        except Exception as byte_exc:  # noqa: BLE001
            row["byte_scan_error"] = f"{type(byte_exc).__name__}: {byte_exc}"
    return row


def inspect_torch_file(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "exists": path.exists(), "load_ok": False}
    if not path.exists():
        return row
    try:
        import torch

        obj = torch.load(path, map_location="cpu")
        row["load_ok"] = True
        row["root"] = summarize_value(obj)
        if isinstance(obj, dict):
            row["keys"] = [str(k) for k in list(obj.keys())[:50]]
            row["key_summaries"] = {str(k): summarize_value(obj[k]) for k in list(obj.keys())[:30]}
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def main() -> int:
    opensg = STAGED_ROOT / "h001_runtime" / "output" / "datasets" / "OpenSG_3RScan"
    features = STAGED_ROOT / "h001_runtime" / "output" / "features" / "clip_features_h001_eval_blip_top5_scales3"
    preprocessed = sorted((opensg / "preprocessed").rglob("data_dict_*.pkl"))[:3]
    views = sorted((opensg / "views").glob("*_object2image.pkl"))[:2]
    feature_pts = sorted(features.rglob("*.pt"))[:2]
    payload = {
        "status": "binary_schema_samples_ready",
        "staged_root": str(STAGED_ROOT),
        "output_dir": str(OUT_DIR),
        "preprocessed_samples": [inspect_pickle(path) for path in preprocessed],
        "object2image_samples": [inspect_pickle(path) for path in views],
        "feature_pt_samples": [inspect_torch_file(path) for path in feature_pts],
    }
    write_json(OUT_DIR / "binary_schema_samples.json", payload)
    print(json.dumps({"status": payload["status"], "output": str(OUT_DIR / "binary_schema_samples.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
