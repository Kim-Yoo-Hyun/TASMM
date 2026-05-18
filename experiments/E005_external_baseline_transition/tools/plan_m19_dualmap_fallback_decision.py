#!/usr/bin/env python3
"""Decide whether to keep repairing DualMap or switch to ConceptGraphs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M19_dualmap_fallback_decision_v0"
M16 = EXPERIMENT_ROOT / "artifacts" / "E005-M16_dualmap_object_output_diagnosis_v0" / "coverage.json"
M17_VERIFY = EXPERIMENT_ROOT / "artifacts" / "E005-M17_dualmap_denser_stride_retry_v0" / "verification" / "coverage.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route": "conceptgraphs_fallback_source_interface_audit",
            "selected": True,
            "why": "DualMap has now passed Docker/runtime/cache execution but still does not produce object-map pkl outputs under default stability settings or denser stride.",
            "claim_value": "Keeps external baseline pressure while avoiding a non-faithful DualMap configuration change.",
            "cost": "Requires a new source/interface audit and adapter plan for ConceptGraphs.",
        },
        {
            "rank": 2,
            "route": "dualmap_lower_stable_num_diagnostic",
            "selected": False,
            "why": "Could test runtime object serialization, but lowering stable_num changes DualMap behavior and cannot be reported as faithful baseline performance.",
            "claim_value": "Schema-only diagnostic evidence.",
            "cost": "Adds another DualMap variant without solving the fair external-baseline comparison.",
        },
        {
            "rank": 3,
            "route": "open3dsg_or_hovsg_next",
            "selected": False,
            "why": "Relevant broader mapping/scene-graph baselines, but ConceptGraphs is a closer posed RGB-D open-vocabulary graph mapping fallback.",
            "claim_value": "Later expansion route.",
            "cost": "Higher adapter and evaluation mismatch risk as immediate next step.",
        },
    ]


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M19 DualMap Fallback Decision",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- M16 selected route was `denser_stride_default_stability_retry` after M14 processed {coverage['m16_processed_keyframes']} keyframes and produced object `*.pkl` count {coverage['m16_pkl_count']}.",
        f"- M18 verifier status: `{coverage['m18_status']}`.",
        f"- M18 processed keyframes: {coverage['m18_processed_keyframes']}.",
        f"- M18 local object count: {coverage['m18_first_local_object_count']} -> {coverage['m18_final_local_object_count']}.",
        f"- M18 object `*.pkl` count: {coverage['m18_pkl_count']}.",
        f"- M18 `layout.pcd` / `system_time.csv` / `detector_time.csv`: {coverage['m18_layout_pcd_count']} / {coverage['m18_system_time_count']} / {coverage['m18_detector_time_count']}.",
        "",
        "## Decision",
        "",
        "- Selected route: `conceptgraphs_fallback_source_interface_audit`.",
        "- Do not use lower-`stable_num` `DualMap` as a baseline result.",
        "- Keep lower-`stable_num` only as a later schema-only diagnostic if `ConceptGraphs` is blocked.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['route']}`: rank {row['rank']}, selected {str(row['selected']).lower()}; {row['why']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- `DualMap` currently supports only a bounded feasibility/negative integration note, not a performance baseline.",
            "- `ConceptGraphs` source/interface audit is required before any external mapping baseline comparison.",
            "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain unsupported.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    m16 = read_json(M16)
    m18 = read_json(M17_VERIFY)
    inventory = m18.get("output_inventory", {})
    rows = route_rows()
    coverage = {
        "status": "e005_m19_dualmap_fallback_decision_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m16_processed_keyframes": m16.get("processed_keyframes", 0),
        "m16_pkl_count": m16.get("pkl_count", 0),
        "m18_status": m18.get("status", "missing"),
        "m18_processed_keyframes": m18.get("processed_keyframes", 0),
        "m18_first_local_object_count": m18.get("first_local_object_count", 0),
        "m18_final_local_object_count": m18.get("final_local_object_count", 0),
        "m18_pkl_count": inventory.get("pkl_count", 0),
        "m18_layout_pcd_count": inventory.get("layout_pcd_count", 0),
        "m18_system_time_count": inventory.get("system_time_count", 0),
        "m18_detector_time_count": inventory.get("detector_time_count", 0),
        "selected_route": "conceptgraphs_fallback_source_interface_audit",
        "lower_stable_num_retry_selected": False,
        "next_recommended_unit": "E005-M20 ConceptGraphs source/interface audit",
    }
    decision = {
        "status": coverage["status"],
        "decision": coverage["selected_route"],
        "route_order": [row["route"] for row in rows],
        "next_action": coverage["next_recommended_unit"],
        "claim_boundary": [
            "DualMap does not yet provide object-map baseline evidence.",
            "Do not report lower-stable-num DualMap as faithful baseline performance.",
            "ConceptGraphs fallback must still pass source/interface and adapter feasibility checks.",
        ],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_jsonl(OUT_DIR / "route_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
