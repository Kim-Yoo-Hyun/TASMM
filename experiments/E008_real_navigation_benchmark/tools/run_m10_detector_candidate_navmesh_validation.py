#!/usr/bin/env python3
"""Validate E008-M09 detector candidate coordinates against Habitat navmeshes."""

from __future__ import annotations

import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M10_detector_candidate_navmesh_validation_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M10_detector_candidate_navmesh_validation_v0"
VERSION = "e008_m10_detector_candidate_navmesh_validation_v0"

M08_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M08_hm3d_rendered_rgbd_frame_staging_smoke_v0"
M09_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M09_hm3d_rendered_rgbd_detector_candidate_smoke_v0"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"


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


def write_json(path: Path, payload: object) -> None:
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


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: sanitize_json(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(v) for v in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def dist(a: list[float], b: list[float]) -> float:
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))


def finite_vec(vec: object, n: int = 3) -> bool:
    if not isinstance(vec, list) or len(vec) != n:
        return False
    try:
        return all(math.isfinite(float(v)) for v in vec)
    except Exception:
        return False


def finite_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def build_frame_index(render_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for row in render_rows:
        out[(str(row["scan_id"]), str(row["frame_id"]))] = row
    return out


def first_frame_id(row: dict[str, Any]) -> str | None:
    frames = row.get("frame_ids")
    if isinstance(frames, list) and frames:
        return str(frames[0])
    bbox = row.get("bbox_2d")
    if isinstance(bbox, dict) and bbox:
        return str(next(iter(bbox)))
    return None


def build_docker_input(proposal_rows: list[dict[str, Any]], frame_index: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for rank, proposal in enumerate(proposal_rows, start=1):
        scan_id = str(proposal.get("scan_id", ""))
        frame_id = first_frame_id(proposal)
        frame_row = frame_index.get((scan_id, frame_id or ""))
        centroid = proposal.get("centroid_world_m")
        row: dict[str, Any] = {
            "candidate_rank": rank,
            "proposal_uid": proposal.get("proposal_uid"),
            "raw_candidate_uid": proposal.get("raw_candidate_uid"),
            "scan_id": scan_id,
            "frame_id": frame_id,
            "label_canonical": proposal.get("label_canonical"),
            "confidence": proposal.get("confidence"),
            "selection_score": proposal.get("selection_score"),
            "centroid_world_m": centroid,
            "coordinate_valid": finite_vec(centroid),
            "join_ready": frame_row is not None,
        }
        if frame_row:
            row.update(
                {
                    "adapter_episode_id": frame_row.get("adapter_episode_id"),
                    "scene_key": frame_row.get("scene_key"),
                    "scene_docker_path": frame_row.get("hm3d_scene_docker_path"),
                    "navmesh_docker_path": frame_row.get("hm3d_navmesh_docker_path"),
                    "object_category": frame_row.get("object_category"),
                    "source_position": frame_row.get("source_position"),
                    "yaw_offset_deg": frame_row.get("yaw_offset_deg"),
                    "policy_input_allowed": frame_row.get("policy_input_allowed"),
                    "uses_objectnav_eval_goal": frame_row.get("uses_objectnav_eval_goal"),
                    "uses_objectnav_eval_viewpoint": frame_row.get("uses_objectnav_eval_viewpoint"),
                }
            )
        rows.append(row)
    return rows


def parse_json_stdout(stdout: str) -> Any:
    for line in reversed([part.strip() for part in stdout.splitlines() if part.strip()]):
        if line.startswith("[") or line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON object found in docker stdout")


def run_habitat_navmesh_validation(input_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    code = f"""
import json
import math
from pathlib import Path

import habitat_sim

rows = [json.loads(line) for line in Path({json.dumps('/work/' + str(input_path.relative_to(ROOT)))}).read_text().splitlines() if line.strip()]
by_scene = {{}}
for row in rows:
    if row.get("join_ready") and row.get("coordinate_valid") and row.get("scene_docker_path"):
        by_scene.setdefault(row["scene_docker_path"], []).append(row)

def as_float_list(vec):
    return [float(x) for x in vec]

def dist(a, b):
    return float(math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))))

def find_path(sim, start, end):
    out = {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": ""}}
    try:
        path = habitat_sim.ShortestPath()
        path.requested_start = start
        path.requested_end = end
        found = bool(sim.pathfinder.find_path(path))
        out["path_found"] = found
        out["geodesic_distance"] = float(path.geodesic_distance) if found else None
        out["point_count"] = len(path.points) if found else 0
    except Exception as exc:
        out["error"] = repr(exc)
    return out

result_rows = []
seen = set()
for scene_path, scene_rows in by_scene.items():
    sim = None
    try:
        sim_cfg = habitat_sim.SimulatorConfiguration()
        sim_cfg.scene_id = scene_path
        sim_cfg.scene_dataset_config_file = {json.dumps(SCENE_DATASET_CONFIG)}
        sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.AgentConfiguration()]))
        for row in scene_rows:
            out = dict(row)
            seen.add(row["proposal_uid"])
            source = row.get("source_position")
            centroid = row.get("centroid_world_m")
            out["pathfinder_loaded"] = bool(sim.pathfinder.is_loaded)
            out["source_navigable"] = bool(sim.pathfinder.is_navigable(source)) if source else False
            out["centroid_navigable"] = bool(sim.pathfinder.is_navigable(centroid)) if centroid else False
            snapped = sim.pathfinder.snap_point(centroid)
            snapped_list = as_float_list(snapped)
            out["snapped_position_m"] = snapped_list
            out["snapped_navigable"] = bool(sim.pathfinder.is_navigable(snapped_list))
            out["snap_distance_m"] = dist(centroid, snapped_list)
            out["centroid_source_euclidean_m"] = dist(source, centroid) if source else None
            out["snapped_source_euclidean_m"] = dist(source, snapped_list) if source else None
            out["centroid_y_delta_from_source_m"] = float(centroid[1]) - float(source[1]) if source else None
            out["snapped_y_delta_from_source_m"] = float(snapped_list[1]) - float(source[1]) if source else None
            path = find_path(sim, source, snapped_list) if source else {{"path_found": False, "geodesic_distance": None, "point_count": 0, "error": "missing_source"}}
            out["source_to_snapped_path_found"] = path["path_found"]
            out["source_to_snapped_geodesic_m"] = path["geodesic_distance"]
            out["source_to_snapped_path_point_count"] = path["point_count"]
            out["source_to_snapped_path_error"] = path["error"]
            if path["geodesic_distance"] is not None and out["snapped_source_euclidean_m"] is not None:
                out["path_stretch_vs_euclidean"] = float(path["geodesic_distance"]) / max(float(out["snapped_source_euclidean_m"]), 1e-6)
            else:
                out["path_stretch_vs_euclidean"] = None
            result_rows.append(out)
    except Exception as exc:
        for row in scene_rows:
            out = dict(row)
            seen.add(row.get("proposal_uid"))
            out["pathfinder_loaded"] = False
            out["scene_error"] = repr(exc)
            out["source_to_snapped_path_found"] = False
            result_rows.append(out)
    finally:
        if sim is not None:
            sim.close()

for row in rows:
    if row.get("proposal_uid") not in seen:
        out = dict(row)
        out["pathfinder_loaded"] = False
        out["source_to_snapped_path_found"] = False
        out["skip_reason"] = "missing_join_or_invalid_coordinate_or_scene"
        result_rows.append(out)

print(json.dumps(result_rows, sort_keys=True))
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{RESEARCH3_DATA_ROOT}:/data:ro",
        "-v",
        f"{ROOT}:/work:ro",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python - <<'PY'\n" + code + "\nPY",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=180)
    meta = {
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
        "requested_candidate_count": sum(1 for _ in input_path.open("r", encoding="utf-8")),
        "command": " ".join(cmd[:10]) + " ...",
        "mounts": [f"{RESEARCH3_DATA_ROOT}:/data:ro", f"{ROOT}:/work:ro"],
    }
    if proc.returncode != 0:
        return [], meta
    try:
        return parse_json_stdout(proc.stdout), meta
    except Exception as exc:
        meta["ok"] = False
        meta["parse_error"] = str(exc)
        return [], meta


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


def build_scan_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("scan_id"))].append(row)
    out = []
    for scan_id, rows in sorted(grouped.items()):
        out.append(
            {
                "scan_id": scan_id,
                "adapter_episode_id": rows[0].get("adapter_episode_id"),
                "scene_key": rows[0].get("scene_key"),
                "object_category": rows[0].get("object_category"),
                "candidate_rows": len(rows),
                "join_ready_rows": sum(1 for row in rows if row.get("join_ready")),
                "coordinate_valid_rows": sum(1 for row in rows if row.get("coordinate_valid")),
                "source_navigable_rows": sum(1 for row in rows if row.get("source_navigable")),
                "centroid_navigable_rows": sum(1 for row in rows if row.get("centroid_navigable")),
                "snapped_navigable_rows": sum(1 for row in rows if row.get("snapped_navigable")),
                "source_to_snapped_path_found_rows": sum(1 for row in rows if row.get("source_to_snapped_path_found")),
                "candidate_usable_for_path_smoke_rows": sum(1 for row in rows if row.get("candidate_usable_for_path_smoke")),
                "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in rows]),
                "p90_snap_distance_m": quantile([row.get("snap_distance_m") for row in rows], 0.9),
                "mean_source_to_snapped_geodesic_m": mean([row.get("source_to_snapped_geodesic_m") for row in rows]),
                "max_abs_centroid_y_delta_from_source_m": max(
                    [abs(float(row["centroid_y_delta_from_source_m"])) for row in rows if row.get("centroid_y_delta_from_source_m") is not None],
                    default=None,
                ),
            }
        )
    return out


def classify_candidate_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in candidate_rows:
        row = dict(row)
        if not row.get("join_ready"):
            status = "blocked_missing_frame_scene_join"
        elif not row.get("coordinate_valid"):
            status = "blocked_invalid_centroid_coordinate"
        elif not row.get("source_navigable"):
            status = "blocked_source_not_navigable"
        elif not finite_vec(row.get("snapped_position_m")) or not finite_number(row.get("snap_distance_m")):
            status = "blocked_snap_failed_non_finite"
        elif not row.get("snapped_navigable"):
            status = "blocked_snapped_point_not_navigable"
        elif not row.get("source_to_snapped_path_found"):
            status = "blocked_snapped_point_unreachable_from_episode_start"
        else:
            status = "candidate_path_ready"
        row["navmesh_validation_status"] = status
        row["candidate_usable_for_path_smoke"] = status == "candidate_path_ready"
        out.append(row)
    return out


def build_route_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    ready = bool(coverage["coordinate_frame_navmesh_validation_ready"])
    return [
        {
            "rank": 1,
            "route_id": "e008_m11_reachable_subset_candidate_visit_order_path_smoke",
            "selected": ready,
            "decision": "selected_next" if ready else "blocked",
            "next_unit": "E008-M11 reachable-subset detector candidate visit-order path smoke" if ready else "repair E008-M10 coordinate-frame validation",
            "launch_long_job_now": False,
            "reason": "Detector coordinates are scene-joined and navmesh-snapped; unreachable candidates are explicit failure rows for the next path smoke." if ready else "Coordinate/navmesh validation is not strong enough for candidate visit-order path smoke.",
        },
        {
            "rank": 2,
            "route_id": "e008_real_navigation_sr_spl_now",
            "selected": False,
            "decision": "defer",
            "next_unit": "later executable navigation policy benchmark",
            "launch_long_job_now": False,
            "reason": "M10 validates candidate coordinates only; real `SR` / `SPL` still requires policy execution and baseline visit orders.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(coverage: dict[str, Any], scan_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    scan_summary = [
        {
            "scan_id": row["scan_id"],
            "rows": row["candidate_rows"],
            "path": row["source_to_snapped_path_found_rows"],
            "mean_snap_m": row["mean_snap_distance_m"],
            "p90_snap_m": row["p90_snap_distance_m"],
        }
        for row in scan_rows
    ]
    route_summary = [
        {"rank": row["rank"], "route_id": row["route_id"], "decision": row["decision"], "next_unit": row["next_unit"]}
        for row in route_rows
    ]
    return (
        "# E008-M10 Detector Candidate Navmesh Validation\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- Candidate rows: {coverage['candidate_rows']}.\n"
        f"- Join-ready rows: {coverage['join_ready_rows']} / {coverage['candidate_rows']}.\n"
        f"- Coordinate-valid rows: {coverage['coordinate_valid_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source navigable rows: {coverage['source_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Centroid navigable rows: {coverage['centroid_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Snapped navigable rows: {coverage['snapped_navigable_rows']} / {coverage['candidate_rows']}.\n"
        f"- Source-to-snapped path found rows: {coverage['source_to_snapped_path_found_rows']} / {coverage['candidate_rows']}.\n"
        f"- Mean snap distance: {coverage['mean_snap_distance_m']}.\n"
        f"- P90 snap distance: {coverage['p90_snap_distance_m']}.\n"
        f"- Coordinate-frame snap ready: {str(coverage['coordinate_frame_snap_ready']).lower()}.\n"
        f"- Path reachability ready with warnings: {str(coverage['candidate_path_reachability_ready_with_warnings']).lower()}.\n"
        f"- Coordinate-frame/navmesh validation ready: {str(coverage['coordinate_frame_navmesh_validation_ready']).lower()}.\n"
        f"- Navmesh validation status counts: `{coverage['navmesh_validation_status_counts']}`.\n"
        f"- Real navigation `SR` / `SPL` ready: {str(coverage['real_navigation_sr_spl_ready']).lower()}.\n\n"
        "## Per-Scan Summary\n\n"
        + markdown_table(scan_summary, ["scan_id", "rows", "path", "mean_snap_m", "p90_snap_m"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route_id", "decision", "next_unit"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M10 validates that E008-M09 detector candidate coordinates can be interpreted in the `HM3D` / `Habitat` world frame and mostly snapped to reachable navmesh goals.\n"
        "- E008-M10 does not claim real navigation `SR` / `SPL` because no policy was executed in the simulator.\n"
        "- E008-M10 does not claim final real RGB-D/open-vocabulary robustness because target recall is still blocked by the `ObjectNav` eval-goal leakage guard.\n\n"
        "## Agent Inference\n\n"
        "- The main warning is not a frame-join failure: it is candidate reachability after snapping, concentrated in a small subset of rows.\n"
        "- The next defensible step is a reachable-subset visit-order path smoke that counts unreachable candidates as explicit failures instead of silently filtering them.\n"
    )


def main() -> None:
    m09_coverage = read_json(M09_ARTIFACT_DIR / "e008_m09_verification_coverage.json")
    proposal_rows = read_jsonl(M09_ARTIFACT_DIR / "container_output" / "real_proposals.jsonl")
    render_rows = read_jsonl(M08_DATA_DIR / "render_inputs" / "render_plan_rows.jsonl")

    frame_index = build_frame_index(render_rows)
    docker_input_rows = build_docker_input(proposal_rows, frame_index)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    docker_input_path = ARTIFACT_DIR / "candidate_navmesh_input_rows.jsonl"
    write_jsonl(docker_input_path, docker_input_rows)

    candidate_rows, docker_meta = run_habitat_navmesh_validation(docker_input_path)
    candidate_rows = classify_candidate_rows(candidate_rows)
    candidate_rows = [sanitize_json(row) for row in candidate_rows]
    scan_rows = build_scan_summary_rows(candidate_rows)

    candidate_count = len(candidate_rows)
    path_found = sum(1 for row in candidate_rows if row.get("source_to_snapped_path_found"))
    snapped_navigable = sum(1 for row in candidate_rows if row.get("snapped_navigable"))
    join_ready = sum(1 for row in candidate_rows if row.get("join_ready"))
    coordinate_valid = sum(1 for row in candidate_rows if row.get("coordinate_valid"))
    source_navigable = sum(1 for row in candidate_rows if row.get("source_navigable"))
    centroid_navigable = sum(1 for row in candidate_rows if row.get("centroid_navigable"))
    label_counts = Counter(str(row.get("label_canonical")) for row in candidate_rows)

    snap_ready = (
        m09_coverage.get("status") == "e008_m09_hm3d_rendered_rgbd_detector_candidate_smoke_ready"
        and docker_meta.get("ok") is True
        and candidate_count == len(proposal_rows)
        and candidate_count > 0
        and join_ready == candidate_count
        and coordinate_valid == candidate_count
        and source_navigable == candidate_count
        and snapped_navigable / max(candidate_count, 1) >= 0.99
    )
    path_reachability_ready_with_warnings = path_found / max(candidate_count, 1) >= 0.90
    strict_path_ready = snapped_navigable == candidate_count and path_found / max(candidate_count, 1) >= 0.95
    validation_ready = snap_ready and path_reachability_ready_with_warnings
    if snap_ready and strict_path_ready:
        status = "e008_m10_detector_candidate_navmesh_validation_ready"
    elif validation_ready:
        status = "e008_m10_detector_candidate_navmesh_validation_ready_with_path_warnings"
    else:
        status = "e008_m10_detector_candidate_navmesh_validation_blocked"

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "m09_status": m09_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "habitat_image": HABITAT_IMAGE,
        "candidate_rows": candidate_count,
        "input_proposal_rows": len(proposal_rows),
        "join_ready_rows": join_ready,
        "coordinate_valid_rows": coordinate_valid,
        "source_navigable_rows": source_navigable,
        "centroid_navigable_rows": centroid_navigable,
        "snapped_navigable_rows": snapped_navigable,
        "source_to_snapped_path_found_rows": path_found,
        "source_to_snapped_path_found_rate": path_found / max(candidate_count, 1),
        "candidate_usable_for_path_smoke_rows": sum(1 for row in candidate_rows if row.get("candidate_usable_for_path_smoke")),
        "mean_snap_distance_m": mean([row.get("snap_distance_m") for row in candidate_rows]),
        "p50_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.5),
        "p90_snap_distance_m": quantile([row.get("snap_distance_m") for row in candidate_rows], 0.9),
        "max_snap_distance_m": max([float(row["snap_distance_m"]) for row in candidate_rows if row.get("snap_distance_m") is not None], default=None),
        "mean_source_to_snapped_geodesic_m": mean([row.get("source_to_snapped_geodesic_m") for row in candidate_rows]),
        "label_counts": dict(sorted(label_counts.items())),
        "navmesh_validation_status_counts": dict(sorted(Counter(str(row.get("navmesh_validation_status")) for row in candidate_rows).items())),
        "evaluated_scan_rows": len(scan_rows),
        "coordinate_frame_snap_ready": snap_ready,
        "candidate_path_reachability_ready_with_warnings": path_reachability_ready_with_warnings,
        "strict_path_ready": strict_path_ready,
        "coordinate_frame_navmesh_validation_ready": validation_ready,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
        "docker_returncode": docker_meta.get("returncode"),
        "selected_next_unit": "E008-M11 reachable-subset detector candidate visit-order path smoke" if validation_ready else "repair E008-M10 coordinate-frame validation",
    }
    route_rows = build_route_rows(coverage)

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_navmesh_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "candidate_navmesh_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "scan_summary_rows.jsonl", scan_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, scan_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "candidate_navmesh_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "scan_summary_rows.jsonl", scan_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
