#!/usr/bin/env python3
"""Validate E008-M110 ConceptGraphs HM3D candidates against Habitat navmeshes."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"
M10_TOOL = EXP_ROOT / "tools" / "run_m10_detector_candidate_navmesh_validation.py"
M64_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M64_full_val_mini_high_path_scale_materialization_v0"
M104_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
M110_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
M110_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M110_conceptgraphs_hm3d_candidate_export_materialization_smoke_v0"
VERSION = "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_v0"


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
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
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


def finite_vec(vec: object, n: int = 3) -> bool:
    if not isinstance(vec, list) or len(vec) != n:
        return False
    try:
        return all(math.isfinite(float(value)) for value in vec)
    except Exception:
        return False


def mean(values: list[Any]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def quantile(values: list[Any], q: float) -> float | None:
    clean = sorted(float(value) for value in values if value is not None and math.isfinite(float(value)))
    if not clean:
        return None
    idx = min(len(clean) - 1, max(0, int(round((len(clean) - 1) * q))))
    return clean[idx]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(out)


def build_episode_index(episode_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in episode_rows:
        adapter_episode_id = str(row.get("adapter_episode_id"))
        if adapter_episode_id not in out:
            out[adapter_episode_id] = row
    return out


def build_case_index(case_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("scan_id")): row for row in case_rows}


def build_docker_input_rows(
    candidate_rows: list[dict[str, Any]],
    episode_index: dict[str, dict[str, Any]],
    case_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        adapter_episode_id = str(row.get("adapter_episode_id") or row.get("episode_id"))
        episode = episode_index.get(adapter_episode_id, {})
        case = case_index.get(str(row.get("scan_id")), {})
        centroid = row.get("candidate_center_xyz")
        out: dict[str, Any] = {
            "adapter_episode_id": adapter_episode_id,
            "candidate_center_xyz": centroid,
            "candidate_confidence_mean": row.get("candidate_confidence_mean"),
            "candidate_id": row.get("candidate_id"),
            "candidate_num_detections": row.get("candidate_num_detections"),
            "candidate_point_count": row.get("candidate_point_count"),
            "candidate_rank": row.get("rank"),
            "candidate_source": row.get("candidate_source"),
            "candidate_uid": row.get("candidate_uid"),
            "centroid_world_m": centroid,
            "coordinate_frame": row.get("coordinate_frame"),
            "coordinate_valid": finite_vec(centroid),
            "frame_id": "conceptgraphs_post_pcd",
            "join_ready": bool(episode),
            "label_canonical": row.get("query_label"),
            "m102_branch": row.get("m102_branch") or case.get("m102_branch"),
            "minimum_requirement": case.get("minimum_requirement"),
            "navmesh_docker_path": episode.get("navmesh_docker_path"),
            "object_category": episode.get("object_category") or row.get("query_label"),
            "policy_input_allowed": bool(row.get("policy_allowed_input")) and bool(episode.get("policy_input_allowed", True)),
            "proposal_uid": row.get("candidate_uid"),
            "query_label": row.get("query_label"),
            "query_uid": row.get("query_uid"),
            "rank": row.get("rank"),
            "raw_candidate_uid": row.get("candidate_id"),
            "scan_id": row.get("scan_id"),
            "scene_docker_path": episode.get("scene_docker_path"),
            "scene_key": row.get("scene_key") or episode.get("scene_key"),
            "selection_score": row.get("semantic_score"),
            "semantic_score": row.get("semantic_score"),
            "source_class_names": row.get("source_class_names"),
            "source_position": episode.get("start_position"),
            "source_route": row.get("source_route"),
            "source_scene_id_raw": episode.get("scene_id_raw"),
            "source_episode_id": episode.get("source_episode_id"),
            "task_context_id": row.get("task_context_id"),
            "uses_objectnav_eval_goal": False,
            "uses_objectnav_eval_viewpoint": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "version": VERSION,
        }
        rows.append(out)
    return rows


def build_query_source_boundary_rows(candidate_rows: list[dict[str, Any]], query_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("query_uid"))].append(row)
    query_by_uid = {str(row.get("query_uid")): row for row in query_rows}
    out: list[dict[str, Any]] = []
    for query_uid in sorted(set(grouped) | set(query_by_uid)):
        rows = grouped.get(query_uid, [])
        query = query_by_uid.get(query_uid, {})
        path_ready = sum(1 for row in rows if row.get("candidate_usable_for_path_smoke"))
        coordinate_valid = sum(1 for row in rows if row.get("coordinate_valid"))
        if not rows:
            status = "source_gap_no_conceptgraphs_candidate"
        elif path_ready > 0:
            status = "source_ready_path_candidate_available"
        elif coordinate_valid > 0:
            status = "source_gap_no_path_ready_candidate"
        else:
            status = "source_gap_invalid_coordinates"
        out.append(
            {
                "adapter_episode_id": query.get("adapter_episode_id") or (rows[0].get("adapter_episode_id") if rows else None),
                "candidate_rows": len(rows),
                "coordinate_valid_rows": coordinate_valid,
                "label_canonical": query.get("label_canonical") or query.get("query_label") or (rows[0].get("query_label") if rows else None),
                "m102_branch": query.get("m102_branch") or (rows[0].get("m102_branch") if rows else None),
                "path_ready_candidate_rows": path_ready,
                "query_uid": query_uid,
                "scan_id": query.get("scan_id") or (rows[0].get("scan_id") if rows else None),
                "scene_key": query.get("scene_key") or (rows[0].get("scene_key") if rows else None),
                "source_boundary_status": status,
                "source_gap": path_ready == 0,
                "source_ready": path_ready > 0,
                "top_rank_path_ready": any(row.get("candidate_usable_for_path_smoke") and int(row.get("rank") or 10**9) == 1 for row in rows),
            }
        )
    return out


def build_scan_source_boundary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("scan_id"))].append(row)
    out: list[dict[str, Any]] = []
    for scan_id, rows in sorted(grouped.items()):
        path_ready = sum(1 for row in rows if row.get("candidate_usable_for_path_smoke"))
        status = "source_ready_path_candidate_available" if path_ready else "source_gap_no_path_ready_candidate"
        out.append(
            {
                "candidate_rows": len(rows),
                "coordinate_valid_rows": sum(1 for row in rows if row.get("coordinate_valid")),
                "label_canonical": rows[0].get("label_canonical"),
                "path_ready_candidate_rows": path_ready,
                "scan_id": scan_id,
                "scene_key": rows[0].get("scene_key"),
                "source_boundary_status": status,
                "source_gap": path_ready == 0,
                "source_ready": path_ready > 0,
                "top_semantic_rank": min(int(row.get("rank") or 10**9) for row in rows),
                "top_path_ready_rank": min(
                    [int(row.get("rank") or 10**9) for row in rows if row.get("candidate_usable_for_path_smoke")],
                    default=None,
                ),
            }
        )
    return out


def build_failure_taxonomy_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows)
    total = max(len(candidate_rows), 1)
    return [
        {
            "failure_type": status,
            "is_ready_status": status == "candidate_path_ready",
            "row_count": count,
            "row_fraction": count / total,
        }
        for status, count in sorted(counts.items())
    ]


def decide_gate(coverage: dict[str, Any]) -> tuple[str, str]:
    candidate_rows = int(coverage["candidate_rows"])
    query_rows = int(coverage["query_rows"])
    source_ready_queries = int(coverage["source_ready_query_rows"])
    coordinate_rate = float(coverage["coordinate_valid_rate"])
    snap_rate = float(coverage["snapped_navigable_rate"])
    path_rate = float(coverage["source_to_snapped_path_found_rate"])
    if candidate_rows == 0:
        return "fail", "no_conceptgraphs_candidates"
    if coordinate_rate < 0.90:
        return "fail", "coordinate_valid_rate_below_0p90"
    if source_ready_queries == 0:
        return "fail", "no_query_has_path_ready_conceptgraphs_candidate"
    if source_ready_queries == query_rows and snap_rate >= 0.90 and path_rate >= 0.25:
        return "pass", "all_queries_have_path_ready_conceptgraphs_candidate"
    return "warning", "partial_queries_have_path_ready_conceptgraphs_candidate"


def build_route_rows(verdict: str, coverage: dict[str, Any]) -> list[dict[str, Any]]:
    ready = verdict in {"pass", "warning"}
    return [
        {
            "decision": "selected_next" if ready else "blocked",
            "launch_long_job_now": False,
            "next_unit": "E008-M112 ConceptGraphs HM3D candidate visit-order/path smoke"
            if ready
            else "repair E008-M111 ConceptGraphs HM3D candidate navmesh/source-readiness validation",
            "rank": 1,
            "reason": coverage.get("gate_reason"),
            "route_id": "e008_m112_conceptgraphs_hm3d_candidate_visit_order_path_smoke",
            "selected": ready,
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later leakage-safe source-gap recovery evaluation",
            "rank": 2,
            "reason": "M111 validates coordinate/navmesh/source-readiness only; source-gap recovery needs leakage-safe goal-evaluation rows.",
            "route_id": "e008_source_gap_recovery_eval_now",
            "selected": False,
        },
        {
            "decision": "defer",
            "launch_long_job_now": False,
            "next_unit": "later real navigation trajectory execution",
            "rank": 3,
            "reason": "M111 does not execute trajectories and cannot support real navigation `SR` / `SPL`.",
            "route_id": "e008_real_navigation_sr_spl_now",
            "selected": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "M110 `ConceptGraphs` HM3D candidate rows are navmesh/source-readiness validated for later path smoke.",
            "status": "allowed_if_gate_passes",
        },
        {
            "claim": "M111 proves source-gap recovery.",
            "status": "blocked",
            "reason": "M111 does not compare candidates against leakage-safe goal-evaluation targets.",
        },
        {
            "claim": "M111 proves real navigation `SR` / `SPL`.",
            "status": "blocked",
            "reason": "M111 does not execute policy trajectories.",
        },
        {
            "claim": "M111 proves final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "reason": "M111 covers two source-gap scans only and lacks downstream source-gap evaluation, heldout transfer, and external navigation/search baselines.",
        },
        {
            "claim": "M111 proves `ConceptGraphs` class-name recognition.",
            "status": "blocked",
            "reason": "M110 source class names are generic `item`; the usable ranking signal is CLIP feature/text scoring.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    query_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
    taxonomy_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    query_summary = [
        {
            "query_uid": row["query_uid"],
            "label": row.get("label_canonical"),
            "candidates": row["candidate_rows"],
            "path_ready": row["path_ready_candidate_rows"],
            "status": row["source_boundary_status"],
        }
        for row in query_rows
    ]
    scan_summary = [
        {
            "scan_id": row["scan_id"],
            "label": row.get("label_canonical"),
            "candidates": row["candidate_rows"],
            "path_ready": row["path_ready_candidate_rows"],
            "top_path_ready_rank": row["top_path_ready_rank"],
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
        "# E008-M111 ConceptGraphs HM3D Candidate Navmesh/Source-Readiness Validation\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Gate verdict: `{coverage['gate_verdict']}` / `{coverage['gate_reason']}`.\n"
        f"- Candidate rows: {coverage['candidate_rows']}.\n"
        f"- Join-ready rows: {coverage['join_ready_rows']} / {coverage['candidate_rows']}.\n"
        f"- Coordinate-valid rows: {coverage['coordinate_valid_rows']} / {coverage['candidate_rows']}.\n"
        f"- Snapped navigable rows: {coverage['snapped_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source-to-snapped path rows: {coverage['source_to_snapped_path_found_rows']} / {coverage['candidate_rows']}.\n"
        f"- Path-ready candidate rows: {coverage['candidate_usable_for_path_smoke_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source-ready query rows: {coverage['source_ready_query_rows']} / {coverage['query_rows']}.\n"
        f"- Source-ready scan rows: {coverage['source_ready_scan_rows']} / {coverage['scan_rows']}.\n"
        f"- Mean source-to-snapped geodesic: {coverage['mean_source_to_snapped_geodesic_m']}.\n"
        f"- Final real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        "## Query Boundary\n\n"
        + markdown_table(query_summary, ["query_uid", "label", "candidates", "path_ready", "status"])
        + "\n\n"
        "## Scan Boundary\n\n"
        + markdown_table(scan_summary, ["scan_id", "label", "candidates", "path_ready", "top_path_ready_rank", "status"])
        + "\n\n"
        "## Failure Taxonomy\n\n"
        + markdown_table(taxonomy_summary, ["failure_type", "rows", "fraction"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- M111 validates `ConceptGraphs` HM3D candidate coordinates against `HM3D` / `Habitat` navmesh reachability.\n"
        "- M111 does not claim source-gap recovery, because leakage-safe goal-evaluation is not run here.\n"
        "- M111 does not claim real navigation `SR` / `SPL`, because no trajectory is executed.\n"
        "- M111 does not claim final RGB-D/open-vocabulary robustness.\n"
        "- M111 does not claim `ConceptGraphs` class-name recognition because M110 exports generic `item` source classes.\n"
    )


def main() -> None:
    m10 = load_m10_module()
    m110_coverage = read_json(M110_ARTIFACT_DIR / "coverage.json")
    m110_candidate_rows = read_jsonl(M110_ARTIFACT_DIR / "candidate_rows.jsonl")
    if not m110_candidate_rows:
        m110_candidate_rows = read_jsonl(M110_DATA_DIR / "candidate_rows.jsonl")
    m110_query_rows = read_jsonl(M110_ARTIFACT_DIR / "query_join_rows.jsonl")
    episode_rows = read_jsonl(M64_ARTIFACT_DIR / "val_mini_episode_rows.jsonl")
    case_rows = read_jsonl(M104_ARTIFACT_DIR / "case_staging_selection_rows.jsonl")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    episode_index = build_episode_index(episode_rows)
    case_index = build_case_index(case_rows)
    docker_input_rows = build_docker_input_rows(m110_candidate_rows, episode_index, case_index)
    docker_input_path = ARTIFACT_DIR / "candidate_navmesh_input_rows.jsonl"
    write_jsonl(docker_input_path, docker_input_rows)

    candidate_rows, docker_meta = m10.run_habitat_navmesh_validation(docker_input_path)
    candidate_rows = m10.classify_candidate_rows(candidate_rows)
    candidate_rows = [sanitize_json(row) for row in candidate_rows]

    query_boundary_rows = build_query_source_boundary_rows(candidate_rows, m110_query_rows)
    scan_boundary_rows = build_scan_source_boundary_rows(candidate_rows)
    failure_rows = [row for row in candidate_rows if row.get("navmesh_validation_status") != "candidate_path_ready"]
    taxonomy_rows = build_failure_taxonomy_rows(candidate_rows)

    candidate_count = len(candidate_rows)
    join_ready = sum(1 for row in candidate_rows if row.get("join_ready"))
    coordinate_valid = sum(1 for row in candidate_rows if row.get("coordinate_valid"))
    source_navigable = sum(1 for row in candidate_rows if row.get("source_navigable"))
    centroid_navigable = sum(1 for row in candidate_rows if row.get("centroid_navigable"))
    snapped_navigable = sum(1 for row in candidate_rows if row.get("snapped_navigable"))
    path_found = sum(1 for row in candidate_rows if row.get("source_to_snapped_path_found"))
    path_ready = sum(1 for row in candidate_rows if row.get("candidate_usable_for_path_smoke"))
    source_ready_queries = sum(1 for row in query_boundary_rows if row.get("source_ready"))
    source_ready_scans = sum(1 for row in scan_boundary_rows if row.get("source_ready"))
    status_counts = dict(sorted(Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows).items()))
    label_counts = Counter(str(row.get("label_canonical")) for row in candidate_rows)

    coverage: dict[str, Any] = {
        "artifact_output_root": str(ARTIFACT_DIR),
        "candidate_rows": candidate_count,
        "candidate_usable_for_path_smoke_rows": path_ready,
        "coordinate_valid_rate": coordinate_valid / max(candidate_count, 1),
        "coordinate_valid_rows": coordinate_valid,
        "derived_output_root": str(DATA_OUT_DIR),
        "docker_returncode": docker_meta.get("returncode"),
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_navigation_policy_execution_ready": False,
        "input_candidate_rows": len(m110_candidate_rows),
        "join_ready_rows": join_ready,
        "label_counts": dict(sorted(label_counts.items())),
        "m110_status": m110_coverage.get("status"),
        "max_snap_distance_m": max([float(row["snap_distance_m"]) for row in candidate_rows if row.get("snap_distance_m") is not None], default=None),
        "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in candidate_rows]),
        "mean_source_to_snapped_geodesic_m": mean([row.get("source_to_snapped_geodesic_m") for row in candidate_rows]),
        "navmesh_validation_status_counts": status_counts,
        "p50_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.5),
        "p90_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.9),
        "query_rows": len(query_boundary_rows),
        "real_navigation_sr_spl_ready": False,
        "scan_rows": len(scan_boundary_rows),
        "selected_next_unit": None,
        "snapped_navigable_rate": snapped_navigable / max(candidate_count, 1),
        "snapped_navigable_rows": snapped_navigable,
        "source_gap_recovery_evaluated": False,
        "source_navigable_rows": source_navigable,
        "source_ready_query_rows": source_ready_queries,
        "source_ready_scan_rows": source_ready_scans,
        "source_to_snapped_path_found_rate": path_found / max(candidate_count, 1),
        "source_to_snapped_path_found_rows": path_found,
        "source_class_name_boundary": "generic_item_class_names_clip_text_score_only",
        "trajectory_execution_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) for row in candidate_rows
        ),
        "version": VERSION,
    }
    coverage["centroid_navigable_rows"] = centroid_navigable
    verdict, reason = decide_gate(coverage)
    coverage["gate_verdict"] = verdict
    coverage["gate_reason"] = reason
    if verdict == "pass":
        coverage["status"] = "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready"
        coverage["selected_next_unit"] = "E008-M112 ConceptGraphs HM3D candidate visit-order/path smoke"
    elif verdict == "warning":
        coverage["status"] = "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_ready_with_source_warnings"
        coverage["selected_next_unit"] = "E008-M112 diagnostic ConceptGraphs HM3D candidate visit-order/path smoke"
    else:
        coverage["status"] = "e008_m111_conceptgraphs_hm3d_candidate_navmesh_source_readiness_validation_blocked"
        coverage["selected_next_unit"] = "repair E008-M111 ConceptGraphs HM3D candidate navmesh/source-readiness validation"

    route_rows = build_route_rows(verdict, coverage)
    claim_rows = build_claim_boundary_rows()

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_navmesh_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "candidate_navmesh_input_rows.jsonl", docker_input_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_navmesh_validation_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_failure_rows.jsonl", failure_rows)
    write_jsonl(ARTIFACT_DIR / "query_source_boundary_rows.jsonl", query_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "scan_source_boundary_rows.jsonl", scan_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "failure_taxonomy_rows.jsonl", taxonomy_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, query_boundary_rows, scan_boundary_rows, taxonomy_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_navmesh_validation_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_failure_rows.jsonl", failure_rows)
    write_jsonl(DATA_OUT_DIR / "query_source_boundary_rows.jsonl", query_boundary_rows)
    write_jsonl(DATA_OUT_DIR / "scan_source_boundary_rows.jsonl", scan_boundary_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
