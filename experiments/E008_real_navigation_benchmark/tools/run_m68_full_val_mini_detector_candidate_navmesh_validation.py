#!/usr/bin/env python3
"""Validate E008-M67 full-val-mini detector candidates against Habitat navmeshes."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M10_TOOL = EXP_ROOT / "tools" / "run_m10_detector_candidate_navmesh_validation.py"
M65_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M65_full_val_mini_render_detector_contract_v0"
M65_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M65_full_val_mini_render_detector_contract_v0"
M67_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M67_full_val_mini_detector_candidate_source_v0"
M64_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
VERSION = "e008_m68_full_val_mini_detector_candidate_navmesh_validation_v0"


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


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def merge_render_rows_with_snap_source(render_rows: list[dict[str, Any]], snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snap_by_frame = {(str(row.get("scan_id")), str(row.get("frame_id"))): row for row in snap_rows}
    merged = []
    for row in render_rows:
        out = dict(row)
        snap = snap_by_frame.get((str(row.get("scan_id")), str(row.get("frame_id"))), {})
        render_position = snap.get("render_position_m") or snap.get("snapped_position_m")
        if render_position:
            out["planned_source_position"] = row.get("source_position")
            out["source_position"] = render_position
            out["source_position_source"] = "E008-M66 snap_validation render_position_m"
            out["source_snap_distance_m"] = snap.get("snap_distance_m")
            out["source_snap_warning_large_move"] = snap.get("snap_warning_large_move")
            out["source_snap_validation_ready"] = snap.get("snap_validation_ready")
            out["source_snap_shell_radius_m"] = snap.get("shell_radius_m")
            out["source_snap_observation_pose_id"] = snap.get("observation_pose_id")
        merged.append(out)
    return merged


def enrich_docker_input_rows(
    docker_input_rows: list[dict[str, Any]],
    frame_index: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    out = []
    for row in docker_input_rows:
        frame_row = frame_index.get((str(row.get("scan_id")), str(row.get("frame_id"))))
        row = dict(row)
        if frame_row:
            row["source_snap_distance_m"] = frame_row.get("source_snap_distance_m")
            row["source_snap_warning_large_move"] = frame_row.get("source_snap_warning_large_move")
            row["source_snap_validation_ready"] = frame_row.get("source_snap_validation_ready")
            row["source_snap_shell_radius_m"] = frame_row.get("source_snap_shell_radius_m")
            row["observation_pose_id"] = frame_row.get("source_snap_observation_pose_id") or frame_row.get("observation_pose_id")
            row["frame_pose_role"] = frame_row.get("pose_role")
            row["shell_radius_m"] = frame_row.get("shell_radius_m")
            row["bearing_relative_deg"] = frame_row.get("bearing_relative_deg")
        out.append(row)
    return out


def build_scan_source_boundary_rows(candidate_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_scan = {str(row.get("scan_id")): row for row in manifest_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("scan_id"))].append(row)
    out = []
    for scan_id in sorted(set(manifest_by_scan) | set(grouped)):
        rows = grouped.get(scan_id, [])
        manifest = manifest_by_scan.get(scan_id, {})
        path_ready = sum(1 for row in rows if row.get("candidate_usable_for_path_smoke"))
        snap_warning_rows = sum(1 for row in rows if row.get("source_snap_warning_large_move"))
        if not rows:
            status = "source_gap_no_detector_candidate"
        elif path_ready > 0:
            status = "source_ready_path_candidate_available"
        elif any(row.get("coordinate_valid") for row in rows):
            status = "source_gap_no_path_ready_candidate"
        else:
            status = "source_gap_invalid_coordinates"
        out.append(
            {
                "adapter_episode_id": manifest.get("adapter_episode_id") or (rows[0].get("adapter_episode_id") if rows else None),
                "candidate_rows": len(rows),
                "coordinate_valid_rows": sum(1 for row in rows if row.get("coordinate_valid")),
                "detector_target_count": manifest.get("detector_target_count"),
                "object_category": manifest.get("object_category") or (rows[0].get("object_category") if rows else None),
                "path_ready_candidate_rows": path_ready,
                "scan_id": scan_id,
                "scene_key": manifest.get("scene_key") or (rows[0].get("scene_key") if rows else None),
                "snap_warning_candidate_rows": snap_warning_rows,
                "source_boundary_status": status,
                "source_gap": path_ready == 0,
                "source_ready": path_ready > 0,
            }
        )
    return out


def build_episode_task_source_rows(
    candidate_rows: list[dict[str, Any]],
    episode_task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_scan[str(row.get("scan_id"))].append(row)
    out = []
    for task in episode_task_rows:
        scan_id = str(task.get("scan_id"))
        rows = candidates_by_scan.get(scan_id, [])
        path_ready = sum(1 for row in rows if row.get("candidate_usable_for_path_smoke"))
        out.append(
            {
                "candidate_rows": len(rows),
                "object_category": task.get("object_category"),
                "path_ready_candidate_rows": path_ready,
                "policy_input_allowed": task.get("policy_input_allowed"),
                "scan_id": scan_id,
                "scan_task_context_uid": task.get("scan_task_context_uid"),
                "source_gap": path_ready == 0,
                "source_ready": path_ready > 0,
                "split_id": task.get("split_id"),
                "task_context_id": task.get("task_context_id"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": task.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"),
            }
        )
    return out


def build_failure_taxonomy_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows)
    total = max(len(candidate_rows), 1)
    return [
        {
            "failure_type": status,
            "row_count": count,
            "row_fraction": count / total,
            "is_ready_status": status == "candidate_path_ready",
        }
        for status, count in sorted(counts.items())
    ]


def build_route_rows(verdict: str, coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "decision": "selected_next" if verdict == "pass" else "diagnostic_next" if verdict == "warning" else "blocked",
            "launch_long_job_now": False,
            "next_unit": "E008-M69 full-val-mini detector candidate visit-order path smoke"
            if verdict in {"pass", "warning"}
            else "repair E008-M68 coordinate/navmesh validation",
            "rank": 1,
            "reason": coverage.get("gate_reason"),
            "route_id": "e008_m69_full_val_mini_detector_candidate_visit_order_path_smoke",
            "selected": verdict in {"pass", "warning"},
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later full trajectory execution",
            "rank": 2,
            "reason": "M68 validates source-readiness only; `SR` / `SPL` requires policy rows and Habitat trajectory execution.",
            "route_id": "e008_real_navigation_sr_spl_now",
            "selected": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "M67 detector candidates are navmesh/source-readiness validated for later path smoke.",
            "status": "allowed_if_gate_passes",
        },
        {
            "claim": "M68 proves real navigation `SR` / `SPL`.",
            "status": "blocked",
            "reason": "No visit-order, goal-evaluation, or trajectory execution is run in M68.",
        },
        {
            "claim": "M68 proves final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "reason": "Detector target recall and external navigation/search baselines remain unresolved.",
        },
    ]


def decide_gate(coverage: dict[str, Any]) -> tuple[str, str]:
    scan_count = int(coverage["scan_rows"])
    path_ready_scans = int(coverage["path_ready_scan_rows"])
    candidate_rows = int(coverage["candidate_rows"])
    coord_rate = float(coverage["coordinate_valid_rate"])
    snap_rate = float(coverage["snapped_navigable_rate"])
    path_rate = float(coverage["source_to_snapped_path_found_rate"])
    status_counts = coverage["navmesh_validation_status_counts"]
    top_failure_count = max(
        [count for status, count in status_counts.items() if status != "candidate_path_ready"],
        default=0,
    )
    top_failure_fraction = top_failure_count / max(candidate_rows, 1)
    if path_ready_scans < 12:
        return "fail", "fewer_than_12_path_ready_scans"
    if path_rate < 0.20:
        return "fail", "path_ready_rate_below_0p20"
    if coord_rate < 0.70:
        return "fail", "coordinate_valid_rate_below_0p70"
    if top_failure_fraction >= 0.80:
        return "fail", "single_failure_mode_dominates"
    if path_ready_scans >= min(24, scan_count) and coord_rate >= 0.70 and snap_rate >= 0.60 and path_rate >= 0.50:
        return "pass", "m68_pass_source_ready_for_visit_order_path_smoke"
    return "warning", "m68_warning_diagnostic_source_ready_only"


def build_report(
    coverage: dict[str, Any],
    scan_rows: list[dict[str, Any]],
    taxonomy_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    scan_summary = [
        {
            "scan_id": row["scan_id"],
            "candidates": row["candidate_rows"],
            "path_ready": row["path_ready_candidate_rows"],
            "status": row["source_boundary_status"],
        }
        for row in scan_rows
    ]
    taxonomy_summary = [
        {"failure_type": row["failure_type"], "rows": row["row_count"], "fraction": round(float(row["row_fraction"]), 4)}
        for row in taxonomy_rows
    ]
    route_summary = [
        {"rank": row["rank"], "route_id": row["route_id"], "decision": row["decision"], "next_unit": row["next_unit"]}
        for row in route_rows
    ]
    return (
        "# E008-M68 Full-Val-Mini Detector Candidate Navmesh Validation\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Gate verdict: `{coverage['gate_verdict']}` / `{coverage['gate_reason']}`.\n"
        f"- Candidate rows: {coverage['candidate_rows']}.\n"
        f"- Coordinate-valid rows: {coverage['coordinate_valid_rows']} / {coverage['candidate_rows']}.\n"
        f"- Snapped navigable rows: {coverage['snapped_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source-to-snapped path rows: {coverage['source_to_snapped_path_found_rows']} / {coverage['candidate_rows']}.\n"
        f"- Path-ready scans: {coverage['path_ready_scan_rows']} / {coverage['scan_rows']}.\n"
        f"- Source-ready episode-task rows: {coverage['source_ready_episode_task_rows']} / {coverage['episode_task_rows']}.\n"
        f"- Snap-warning candidate rows: {coverage['snap_warning_candidate_rows']}.\n"
        f"- Final real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        "## Failure Taxonomy\n\n"
        + markdown_table(taxonomy_summary, ["failure_type", "rows", "fraction"])
        + "\n\n"
        "## Scan Boundary\n\n"
        + markdown_table(scan_summary, ["scan_id", "candidates", "path_ready", "status"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- M68 validates detector candidate source-readiness for later path/visit-order smoke.\n"
        "- M68 does not claim real navigation `SR` / `SPL`.\n"
        "- M68 does not claim final real RGB-D/open-vocabulary robustness.\n"
    )


def main() -> None:
    m10 = load_m10_module()
    m67_coverage = read_json(M67_ARTIFACT_DIR / "e008_m16_verification_coverage.json")
    proposal_rows = read_jsonl(M67_ARTIFACT_DIR / "container_output" / "real_proposals.jsonl")
    render_rows = read_jsonl(M65_DATA_DIR / "render_inputs" / "render_plan_rows.jsonl")
    snap_rows = read_jsonl(M65_DATA_DIR / "snap_validation_rows.jsonl")
    manifest_rows = read_jsonl(M65_ARTIFACT_DIR / "detector_manifest_rows.jsonl")
    episode_task_rows = read_jsonl(M64_ARTIFACT_DIR / "episode_task_context_rows.jsonl")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    merged_render_rows = merge_render_rows_with_snap_source(render_rows, snap_rows)
    frame_index = m10.build_frame_index(merged_render_rows)
    docker_input_rows = m10.build_docker_input(proposal_rows, frame_index)
    docker_input_rows = enrich_docker_input_rows(docker_input_rows, frame_index)
    docker_input_path = ARTIFACT_DIR / "candidate_navmesh_input_rows.jsonl"
    write_jsonl(docker_input_path, docker_input_rows)

    candidate_rows, docker_meta = m10.run_habitat_navmesh_validation(docker_input_path)
    candidate_rows = m10.classify_candidate_rows(candidate_rows)
    candidate_rows = [sanitize_json(row) for row in candidate_rows]

    scan_rows = build_scan_source_boundary_rows(candidate_rows, manifest_rows)
    episode_task_source_rows = build_episode_task_source_rows(candidate_rows, episode_task_rows)
    failure_rows = [row for row in candidate_rows if row.get("navmesh_validation_status") != "candidate_path_ready"]
    snap_warning_rows = [row for row in candidate_rows if row.get("source_snap_warning_large_move")]
    taxonomy_rows = build_failure_taxonomy_rows(candidate_rows)

    candidate_count = len(candidate_rows)
    coordinate_valid = sum(1 for row in candidate_rows if row.get("coordinate_valid"))
    snapped_navigable = sum(1 for row in candidate_rows if row.get("snapped_navigable"))
    path_found = sum(1 for row in candidate_rows if row.get("source_to_snapped_path_found"))
    path_ready_scans = sum(1 for row in scan_rows if row.get("source_ready"))
    source_ready_tasks = sum(1 for row in episode_task_source_rows if row.get("source_ready"))
    label_counts = Counter(str(row.get("label_canonical")) for row in candidate_rows)
    status_counts = dict(sorted(Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows).items()))

    coverage: dict[str, Any] = {
        "artifact_output_root": str(ARTIFACT_DIR),
        "candidate_rows": candidate_count,
        "coordinate_valid_rate": coordinate_valid / max(candidate_count, 1),
        "coordinate_valid_rows": coordinate_valid,
        "derived_output_root": str(DATA_OUT_DIR),
        "docker_returncode": docker_meta.get("returncode"),
        "episode_task_rows": len(episode_task_source_rows),
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "input_proposal_rows": len(proposal_rows),
        "label_counts": dict(sorted(label_counts.items())),
        "m67_status": m67_coverage.get("status"),
        "max_snap_distance_m": max([float(row["snap_distance_m"]) for row in candidate_rows if row.get("snap_distance_m") is not None], default=None),
        "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in candidate_rows]),
        "navmesh_validation_status_counts": status_counts,
        "p50_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.5),
        "p90_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.9),
        "path_ready_scan_rows": path_ready_scans,
        "real_navigation_sr_spl_ready": False,
        "scan_rows": len(scan_rows),
        "selected_next_unit": None,
        "snap_warning_candidate_rows": len(snap_warning_rows),
        "snapped_navigable_rate": snapped_navigable / max(candidate_count, 1),
        "snapped_navigable_rows": snapped_navigable,
        "source_ready_episode_task_rows": source_ready_tasks,
        "source_to_snapped_path_found_rate": path_found / max(candidate_count, 1),
        "source_to_snapped_path_found_rows": path_found,
        "version": VERSION,
    }
    verdict, reason = decide_gate(coverage)
    coverage["gate_verdict"] = verdict
    coverage["gate_reason"] = reason
    if verdict == "pass":
        coverage["status"] = "e008_m68_full_val_mini_detector_candidate_navmesh_validation_ready"
        coverage["selected_next_unit"] = "E008-M69 full-val-mini detector candidate visit-order path smoke"
    elif verdict == "warning":
        coverage["status"] = "e008_m68_full_val_mini_detector_candidate_navmesh_validation_ready_with_source_warnings"
        coverage["selected_next_unit"] = "E008-M69 diagnostic full-val-mini detector candidate visit-order path smoke"
    else:
        coverage["status"] = "e008_m68_full_val_mini_detector_candidate_navmesh_validation_blocked"
        coverage["selected_next_unit"] = "repair E008-M68 coordinate/navmesh validation"

    route_rows = build_route_rows(verdict, coverage)
    claim_rows = build_claim_boundary_rows()

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_navmesh_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "scan_source_boundary_rows.jsonl", scan_rows)
    write_jsonl(ARTIFACT_DIR / "episode_task_source_ready_rows.jsonl", episode_task_source_rows)
    write_jsonl(ARTIFACT_DIR / "snap_warning_overlap_rows.jsonl", snap_warning_rows)
    write_jsonl(ARTIFACT_DIR / "failure_taxonomy_rows.jsonl", taxonomy_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, scan_rows, taxonomy_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_navmesh_validation_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_failure_rows.jsonl", failure_rows)
    write_jsonl(DATA_OUT_DIR / "scan_source_boundary_rows.jsonl", scan_rows)
    write_jsonl(DATA_OUT_DIR / "episode_task_source_ready_rows.jsonl", episode_task_source_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
