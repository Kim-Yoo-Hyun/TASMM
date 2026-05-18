#!/usr/bin/env python3
"""Inspect ConceptGraphs one-scan runtime output schema after E005-M27."""

from __future__ import annotations

import gzip
import glob
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M27_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M28_conceptgraphs_output_schema_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_pickle(path: Path) -> Any:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as handle:
            return pickle.load(handle)
    with path.open("rb") as handle:
        return pickle.load(handle)


def value_summary(value: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"type": type(value).__name__}
    shape = getattr(value, "shape", None)
    if shape is not None:
        summary["shape"] = list(shape)
    if isinstance(value, (list, tuple)):
        summary["length"] = len(value)
        if value:
            summary["first_type"] = type(value[0]).__name__
            if isinstance(value[0], dict):
                summary["first_item_fields"] = {
                    str(key): value_summary(item_value) for key, item_value in list(value[0].items())[:40]
                }
    elif isinstance(value, dict):
        summary["key_count"] = len(value)
        summary["sample_keys"] = [str(key) for key in list(value.keys())[:20]]
    elif hasattr(value, "dtype"):
        summary["dtype"] = str(getattr(value, "dtype"))
    return summary


def object_summary(payload: Any) -> dict[str, Any]:
    summary = value_summary(payload)
    if isinstance(payload, dict):
        summary["fields"] = {str(key): value_summary(value) for key, value in list(payload.items())[:40]}
    elif isinstance(payload, (list, tuple)):
        summary["length"] = len(payload)
        if payload and isinstance(payload[0], dict):
            summary["first_item_fields"] = {
                str(key): value_summary(value) for key, value in list(payload[0].items())[:40]
            }
        elif payload:
            summary["first_item"] = value_summary(payload[0])
    return summary


def inventory(expected: dict[str, str]) -> dict[str, Any]:
    gsa_files = sorted(glob.glob(expected.get("gsa_detection_pattern", "")))
    full_pcd = Path(expected.get("full_pcd", ""))
    full_pcd_post = Path(expected.get("full_pcd_post", ""))
    return {
        "gsa_detection_count": len(gsa_files),
        "sample_gsa_detection": gsa_files[0] if gsa_files else "",
        "full_pcd": str(full_pcd),
        "full_pcd_exists": full_pcd.exists(),
        "full_pcd_post": str(full_pcd_post),
        "full_pcd_post_exists": full_pcd_post.exists(),
    }


def build_report(coverage: dict[str, Any], schema: dict[str, Any]) -> str:
    lines = [
        "# E005-M28 ConceptGraphs Output Schema Inspection",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- GSA detection files: {coverage['inventory']['gsa_detection_count']}.",
        f"- Full PCD exists: {str(coverage['inventory']['full_pcd_exists']).lower()}.",
        f"- Full PCD post exists: {str(coverage['inventory']['full_pcd_post_exists']).lower()}.",
        f"- Schema inspected: {str(coverage['schema_inspected']).lower()}.",
        "",
        "## Claim Boundary",
        "",
        "- Schema inspection only prepares conversion into query-level metrics.",
        "- It does not support a baseline performance claim by itself.",
        "",
    ]
    if schema:
        lines.extend(
            [
                "## Schema Heads",
                "",
                f"- GSA sample type: `{schema.get('gsa_detection_sample', {}).get('type', 'missing')}`.",
                f"- Full PCD type: `{schema.get('full_pcd', {}).get('type', 'missing')}`.",
                f"- Full PCD post type: `{schema.get('full_pcd_post', {}).get('type', 'missing')}`.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    launch = read_json(M27_DIR / "coverage.json")
    inv = inventory(launch.get("expected_outputs", {}))
    schema: dict[str, Any] = {}
    errors: list[str] = []
    schema_inspected = False
    if inv["gsa_detection_count"] > 0:
        try:
            schema["gsa_detection_sample"] = object_summary(load_pickle(Path(inv["sample_gsa_detection"])))
        except Exception as exc:  # noqa: BLE001 - diagnostics should keep going.
            errors.append(f"gsa_detection_sample_load_failed:{exc!r}")
    if inv["full_pcd_exists"]:
        try:
            schema["full_pcd"] = object_summary(load_pickle(Path(inv["full_pcd"])))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"full_pcd_load_failed:{exc!r}")
    if inv["full_pcd_post_exists"]:
        try:
            schema["full_pcd_post"] = object_summary(load_pickle(Path(inv["full_pcd_post"])))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"full_pcd_post_load_failed:{exc!r}")
    schema_inspected = bool(schema) and not errors
    if schema_inspected and inv["full_pcd_exists"]:
        status = "e005_m28_conceptgraphs_output_schema_ready"
    elif errors:
        status = "e005_m28_conceptgraphs_output_schema_inspection_failed"
    else:
        status = "e005_m28_conceptgraphs_output_schema_blocked_outputs_missing"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m27_launch_status": launch.get("status"),
        "inventory": inv,
        "schema_inspected": schema_inspected,
        "errors": errors,
        "next_recommended_unit": "E005-M29 ConceptGraphs output-to-query conversion plan"
        if status == "e005_m28_conceptgraphs_output_schema_ready"
        else "E005-M27 runtime smoke launch/completion",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "schema_summary.json", schema)
    write_text(OUT_DIR / "report.md", build_report(coverage, schema))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
