#!/usr/bin/env python3
"""Validate E008-M16 expanded detector candidates against Habitat navmeshes."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M15_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M15_non_oracle_observation_expansion_frame_staging_v0"
M16_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M16_non_oracle_observation_expansion_detector_candidate_smoke_v0"
M10_TOOL = EXP_ROOT / "tools" / "run_m10_detector_candidate_navmesh_validation.py"
VERSION = "e008_m17_expanded_detector_candidate_navmesh_validation_v0"


def load_m10_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m10_navmesh", M10_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M10_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def mean(values: list[Any]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def quantile(values: list[Any], q: float) -> float | None:
    clean = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not clean:
        return None
    idx = min(len(clean) - 1, max(0, int(round((len(clean) - 1) * q))))
    return clean[idx]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_route_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    ready = bool(coverage["coordinate_frame_navmesh_validation_ready"])
    return [
        {
            "decision": "selected_next" if ready else "blocked",
            "launch_long_job_now": False,
            "next_unit": "E008-M18 expanded detector candidate visit-order path smoke"
            if ready
            else "repair E008-M17 expanded coordinate-frame validation",
            "rank": 1,
            "reason": "Expanded detector candidates are scene-joined and navmesh validated."
            if ready
            else "Expanded detector candidate coordinates are not ready for path-order evaluation.",
            "route_id": "e008_m18_expanded_candidate_visit_order_path_smoke",
            "selected": ready,
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later executable navigation policy benchmark",
            "rank": 2,
            "reason": "M17 validates candidate coordinates only; real `SR` / `SPL` still requires policy execution.",
            "route_id": "e008_real_navigation_sr_spl_now",
            "selected": False,
        },
    ]


def merge_render_rows_with_snap_source(render_rows: list[dict[str, Any]], snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snap_by_frame = {
        (str(row.get("scan_id")), str(row.get("frame_id"))): row
        for row in snap_rows
    }
    merged = []
    for row in render_rows:
        out = dict(row)
        snap = snap_by_frame.get((str(row.get("scan_id")), str(row.get("frame_id"))), {})
        render_position = snap.get("render_position_m") or snap.get("snapped_position_m")
        if render_position:
            out["planned_source_position"] = row.get("source_position")
            out["source_position"] = render_position
            out["source_position_source"] = "E008-M15 snap_validation render_position_m"
            out["source_snap_distance_m"] = snap.get("snap_distance_m")
            out["source_snap_warning_large_move"] = snap.get("snap_warning_large_move")
            out["source_snap_validation_ready"] = snap.get("snap_validation_ready")
        merged.append(out)
    return merged


def build_report(coverage: dict[str, Any], scan_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    scan_summary = [
        {
            "mean_snap_m": row["mean_snap_distance_m"],
            "p90_snap_m": row["p90_snap_distance_m"],
            "path": row["source_to_snapped_path_found_rows"],
            "rows": row["candidate_rows"],
            "scan_id": row["scan_id"],
        }
        for row in scan_rows
    ]
    route_summary = [
        {"decision": row["decision"], "next_unit": row["next_unit"], "rank": row["rank"], "route_id": row["route_id"]}
        for row in route_rows
    ]
    return (
        "# E008-M17 Expanded Detector Candidate Navmesh Validation\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Candidate rows: {coverage['candidate_rows']}.\n"
        f"- Join-ready rows: {coverage['join_ready_rows']} / {coverage['candidate_rows']}.\n"
        f"- Coordinate-valid rows: {coverage['coordinate_valid_rows']} / {coverage['candidate_rows']}.\n"
        f"- Snapped navigable rows: {coverage['snapped_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source-to-snapped path found rows: {coverage['source_to_snapped_path_found_rows']} / {coverage['candidate_rows']}.\n"
        f"- Every scan has a path-ready candidate: {str(coverage['every_scan_has_path_ready_candidate']).lower()}.\n"
        f"- Mean snap distance: {coverage['mean_snap_distance_m']}.\n"
        f"- P90 snap distance: {coverage['p90_snap_distance_m']}.\n"
        f"- Navmesh validation status counts: `{coverage['navmesh_validation_status_counts']}`.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        f"- Source position basis: `{coverage['source_position_basis']}`.\n"
        f"- Large source snap warning rows inherited from M15: {coverage['m15_large_snap_warning_rows']}.\n\n"
        "## Per-Scan Summary\n\n"
        + markdown_table(scan_summary, ["scan_id", "rows", "path", "mean_snap_m", "p90_snap_m"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M17 validates expanded detector candidate coordinates against `HM3D` / `Habitat` navmeshes.\n"
        "- E008-M17 does not claim real navigation `SR` / `SPL` because no policy trajectory is executed.\n"
        "- E008-M17 does not claim final real RGB-D/open-vocabulary robustness because goal evaluation and policy comparisons remain separate gates.\n\n"
    )


def main() -> None:
    m10 = load_m10_module()
    m16_coverage = read_json(M16_ARTIFACT_DIR / "e008_m16_verification_coverage.json")
    proposal_rows = read_jsonl(M16_ARTIFACT_DIR / "container_output" / "real_proposals.jsonl")
    render_rows = read_jsonl(M15_DATA_DIR / "render_inputs" / "render_plan_rows.jsonl")
    snap_rows = read_jsonl(M15_DATA_DIR / "snap_validation_rows.jsonl")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    merged_render_rows = merge_render_rows_with_snap_source(render_rows, snap_rows)
    frame_index = m10.build_frame_index(merged_render_rows)
    docker_input_rows = m10.build_docker_input(proposal_rows, frame_index)
    docker_input_path = ARTIFACT_DIR / "candidate_navmesh_input_rows.jsonl"
    write_jsonl(docker_input_path, docker_input_rows)

    candidate_rows, docker_meta = m10.run_habitat_navmesh_validation(docker_input_path)
    candidate_rows = m10.classify_candidate_rows(candidate_rows)
    candidate_rows = [sanitize_json(row) for row in candidate_rows]
    scan_rows = m10.build_scan_summary_rows(candidate_rows)

    candidate_count = len(candidate_rows)
    path_found = sum(1 for row in candidate_rows if row.get("source_to_snapped_path_found"))
    snapped_navigable = sum(1 for row in candidate_rows if row.get("snapped_navigable"))
    join_ready = sum(1 for row in candidate_rows if row.get("join_ready"))
    coordinate_valid = sum(1 for row in candidate_rows if row.get("coordinate_valid"))
    source_navigable = sum(1 for row in candidate_rows if row.get("source_navigable"))
    centroid_navigable = sum(1 for row in candidate_rows if row.get("centroid_navigable"))
    label_counts = Counter(str(row.get("label_canonical")) for row in candidate_rows)

    snap_ready = (
        m16_coverage.get("status") == "e008_m16_non_oracle_observation_expansion_detector_candidate_smoke_ready"
        and docker_meta.get("ok") is True
        and candidate_count == len(proposal_rows)
        and candidate_count > 0
        and join_ready == candidate_count
        and coordinate_valid == candidate_count
        and source_navigable == candidate_count
        and snapped_navigable / max(candidate_count, 1) >= 0.99
    )
    every_scan_has_path_ready = bool(scan_rows) and all(
        int(row.get("source_to_snapped_path_found_rows", 0) or 0) > 0 for row in scan_rows
    )
    path_reachability_ready_with_warnings = (
        path_found / max(candidate_count, 1) >= 0.85 and every_scan_has_path_ready
    )
    strict_path_ready = snapped_navigable == candidate_count and path_found / max(candidate_count, 1) >= 0.95
    validation_ready = snap_ready and path_reachability_ready_with_warnings
    if snap_ready and strict_path_ready:
        status = "e008_m17_expanded_detector_candidate_navmesh_validation_ready"
    elif validation_ready:
        status = "e008_m17_expanded_detector_candidate_navmesh_validation_ready_with_path_warnings"
    else:
        status = "e008_m17_expanded_detector_candidate_navmesh_validation_blocked"

    coverage = {
        "artifact_output_root": str(ARTIFACT_DIR),
        "candidate_path_reachability_ready_with_warnings": path_reachability_ready_with_warnings,
        "candidate_rows": candidate_count,
        "candidate_usable_for_path_smoke_rows": sum(1 for row in candidate_rows if row.get("candidate_usable_for_path_smoke")),
        "centroid_navigable_rows": centroid_navigable,
        "coordinate_frame_navmesh_validation_ready": validation_ready,
        "coordinate_frame_snap_ready": snap_ready,
        "coordinate_valid_rows": coordinate_valid,
        "derived_output_root": str(DATA_OUT_DIR),
        "docker_returncode": docker_meta.get("returncode"),
        "evaluated_scan_rows": len(scan_rows),
        "every_scan_has_path_ready_candidate": every_scan_has_path_ready,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "input_proposal_rows": len(proposal_rows),
        "join_ready_rows": join_ready,
        "label_counts": dict(sorted(label_counts.items())),
        "launch_long_job_now": False,
        "m15_large_snap_warning_rows": sum(1 for row in snap_rows if row.get("snap_warning_large_move")),
        "m16_status": m16_coverage.get("status"),
        "max_snap_distance_m": max([float(row["snap_distance_m"]) for row in candidate_rows if row.get("snap_distance_m") is not None], default=None),
        "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in candidate_rows]),
        "mean_source_to_snapped_geodesic_m": mean([row.get("source_to_snapped_geodesic_m") for row in candidate_rows]),
        "navmesh_validation_status_counts": dict(sorted(Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows).items())),
        "p50_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.5),
        "p90_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.9),
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": "E008-M18 expanded detector candidate visit-order path smoke" if validation_ready else "repair E008-M17 coordinate-frame validation",
        "snapped_navigable_rows": snapped_navigable,
        "source_navigable_rows": source_navigable,
        "source_to_snapped_path_found_rate": path_found / max(candidate_count, 1),
        "source_to_snapped_path_found_rows": path_found,
        "status": status,
        "strict_path_ready": strict_path_ready,
        "source_position_basis": "E008-M15 snap_validation render_position_m",
        "version": VERSION,
    }
    route_rows = build_route_rows(coverage)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_navmesh_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "candidate_navmesh_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "scan_summary_rows.jsonl", scan_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(build_report(coverage, scan_rows, route_rows), encoding="utf-8")

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_navmesh_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "scan_summary_rows.jsonl", scan_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
