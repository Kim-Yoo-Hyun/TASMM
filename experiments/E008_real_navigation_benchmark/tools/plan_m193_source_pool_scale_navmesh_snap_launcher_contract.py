#!/usr/bin/env python3
"""Validate M192 source-pool scale poses and write the M194 launcher contract."""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M178_TOOL = EXP_ROOT / "tools" / "plan_m178_navmesh_snap_render_detector_launcher_contract.py"
M192_ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0"
)
M192_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M193_source_pool_scale_navmesh_snap_launcher_contract_v0"
)
M194_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M194_source_pool_scale_render_detector_execution_v0"

VERSION = "e008_m193_source_pool_scale_navmesh_snap_launcher_contract_v0"
READY_STATUS = "e008_m193_source_pool_scale_navmesh_snap_launcher_contract_ready"
READY_WARNING_STATUS = "e008_m193_source_pool_scale_navmesh_snap_launcher_contract_ready_with_snap_warnings"
BLOCKED_STATUS = "e008_m193_source_pool_scale_navmesh_snap_launcher_contract_blocked"
NEXT_UNIT = "E008-M194 source-pool scale render/detector execution launch and verification"

SELECTED_DENOMINATOR = "hm3d_val_mini_all_triggered_source_pool_scale_v1"
SELECTED_METHOD = "source_pool_plus_detector_confidence_reachable_subset_v1"
PRIMARY_ABLATION = "no_source_pool_detector_confidence_reachable_subset_v0"
PROTECTED_DEFAULT = "detector_confidence_reachable_subset_v0"
ROUTE_ID = "source_pool_scale_full_triggered_expansion_v1"
EXPECTED_SOURCE_POSE_ROWS = 240
EXPECTED_RENDER_PLAN_ROWS = 960
PROMPT_SET_ID = "e008_m193_source_pool_scale_detector_prompts_v0"
BATCH_ID = "e008_m193_source_pool_scale"


def load_m178() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m178_reused_contract", M178_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M178_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.M177_ARTIFACT_DIR = M192_ARTIFACT_DIR
    module.M177_DATA_DIR = M192_DATA_DIR
    module.ARTIFACT_DIR = ARTIFACT_DIR
    module.DATA_OUT_DIR = DATA_OUT_DIR
    module.M179_ARTIFACT_DIR = M194_ARTIFACT_DIR
    module.VERSION = VERSION
    module.READY_STATUS = READY_STATUS
    module.READY_WARNING_STATUS = READY_WARNING_STATUS
    module.BLOCKED_STATUS = BLOCKED_STATUS
    module.NEXT_UNIT = NEXT_UNIT
    module.RENDER_TMUX_SESSION = "e008_m194_source_pool_scale_render"
    module.DETECTOR_TMUX_SESSION = "e008_m194_source_pool_scale_detector"
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


def sanitize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def patch_text(value: Any) -> Any:
    if isinstance(value, str):
        return (
            value.replace("E008-M179", "E008-M194")
            .replace("E008-M178", "E008-M193")
            .replace("E008-M177", "E008-M192")
            .replace("e008_m179", "e008_m194")
            .replace("e008_m178", "e008_m193")
            .replace("e008_m177", "e008_m192")
            .replace("m179", "m194")
            .replace("m178", "m193")
            .replace("m177", "m192")
        )
    if isinstance(value, dict):
        return {key: patch_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [patch_text(item) for item in value]
    return value


def source_by_pose_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("observation_pose_id")): row for row in rows}


def enrich_render_rows(render_rows: list[dict[str, Any]], snap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snap_by_pose = source_by_pose_id(snap_rows)
    enriched: list[dict[str, Any]] = []
    for row in render_rows:
        pose = snap_by_pose.get(str(row.get("observation_pose_id")), {})
        out = patch_text(dict(row))
        out.update(
            {
                "version": VERSION,
                "scale_denominator_id": pose.get("scale_denominator_id", SELECTED_DENOMINATOR),
                "scale_request_uid": pose.get("scale_request_uid"),
                "scale_batch_id": pose.get("scale_batch_id"),
                "selected_method_id": pose.get("selected_method_id", SELECTED_METHOD),
                "primary_ablation_id": pose.get("primary_ablation_id", PRIMARY_ABLATION),
                "protected_default_policy_id": pose.get("protected_default_policy_id", PROTECTED_DEFAULT),
                "kept_method_component": pose.get("kept_method_component"),
                "route_id": pose.get("route_id", ROUTE_ID),
                "render_source": "e008_m193_source_pool_scale_navmesh_snap_launcher_contract",
                "source_position_source": "E008-M193 snap_validation render_position_m",
            }
        )
        enriched.append(out)
    return enriched


def enrich_object_target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        out = patch_text(dict(row))
        out.update(
            {
                "version": VERSION,
                "prompt_set_id": PROMPT_SET_ID,
                "target_uid": f"e008-m193:{row.get('scan_id')}:{row.get('label_canonical')}",
                "source": "E008-M193 HM3D ObjectNav category text only after M192 source-pool scale rows are frozen",
            }
        )
        out_rows.append(out)
    return out_rows


def enrich_prompt_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out = patch_text(dict(payload))
    out["version"] = VERSION
    out["prompt_set_id"] = PROMPT_SET_ID
    out["prompt_policy"] = (
        "M193 uses query category text only after M192 source-pool scale rows are frozen; "
        "ObjectNav goal/viewpoint fields are blocked."
    )
    return out


def enrich_detector_manifest_rows(
    rows: list[dict[str, Any]], render_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    first_by_scan: dict[str, dict[str, Any]] = {}
    for row in render_rows:
        first_by_scan.setdefault(str(row.get("scan_id")), row)
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        render = first_by_scan.get(str(row.get("scan_id")), {})
        out = patch_text(dict(row))
        out.update(
            {
                "version": VERSION,
                "batch_id": BATCH_ID,
                "prompt_set_id": PROMPT_SET_ID,
                "prompt_set_path": str(DATA_OUT_DIR / "detector_inputs" / "prompt_set.json"),
                "route_id": ROUTE_ID,
                "route_ids": [ROUTE_ID],
                "frame_sampling_strategy": "m192_source_pool_scale_multiview",
                "paper_table_role": "source_pool_scale_materialization_not_result",
                "scale_denominator_id": render.get("scale_denominator_id", SELECTED_DENOMINATOR),
                "scale_request_uid": render.get("scale_request_uid"),
                "scale_batch_id": render.get("scale_batch_id"),
                "selected_method_id": render.get("selected_method_id", SELECTED_METHOD),
                "primary_ablation_id": render.get("primary_ablation_id", PRIMARY_ABLATION),
                "protected_default_policy_id": render.get("protected_default_policy_id", PROTECTED_DEFAULT),
                "claim_boundary": (
                    "Detector prompt uses object category only after M192 source-pool source poses are frozen; "
                    "no ObjectNav target/viewpoint source-placement input is used."
                ),
            }
        )
        out_rows.append(out)
    return out_rows


def enrich_expected_rows(rows: list[dict[str, Any]], render_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_by_scan: dict[str, dict[str, Any]] = {}
    for row in render_rows:
        first_by_scan.setdefault(str(row.get("scan_id")), row)
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        render = first_by_scan.get(str(row.get("scan_id")), {})
        out = patch_text(dict(row))
        out.update(
            {
                "version": VERSION,
                "scale_denominator_id": render.get("scale_denominator_id", SELECTED_DENOMINATOR),
                "scale_request_uid": render.get("scale_request_uid"),
                "scale_batch_id": render.get("scale_batch_id"),
            }
        )
        out_rows.append(out)
    return out_rows


def patch_launcher_inputs(input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    render_inputs = DATA_OUT_DIR / "render_inputs"
    old_script = render_inputs / "render_m178_source_pool.py"
    new_script = render_inputs / "render_m193_source_pool.py"
    if old_script.exists():
        shutil.copyfile(old_script, new_script)
    out_rows: list[dict[str, Any]] = []
    for row in input_rows:
        out = patch_text(dict(row))
        if row.get("file_role") == "render_script" and new_script.exists():
            out["path"] = str(new_script)
            out["ready"] = True
        out["version"] = VERSION
        out_rows.append(out)
    return out_rows


def patch_command_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patched: list[dict[str, Any]] = []
    for row in rows:
        out = patch_text(dict(row))
        if str(row.get("job_id")).endswith("render"):
            out.update(
                {
                    "job_id": "E008-M194-render",
                    "job_type": "source_pool_scale_render_frame_staging",
                    "verification_command": (
                        "python experiments/E008_real_navigation_benchmark/tools/"
                        "verify_m194_source_pool_scale_render_detector_execution.py --require-render-ready"
                    ),
                }
            )
        elif str(row.get("job_id")).endswith("detector"):
            out.update(
                {
                    "job_id": "E008-M194-detector",
                    "job_type": "source_pool_scale_open_vocabulary_detector",
                    "verification_command": (
                        "python experiments/E008_real_navigation_benchmark/tools/"
                        "verify_m194_source_pool_scale_render_detector_execution.py --require-ready"
                    ),
                }
            )
        for key in ("command", "inner_command"):
            if isinstance(out.get(key), str):
                out[key] = out[key].replace("render_m178_source_pool.py", "render_m193_source_pool.py")
        out["version"] = VERSION
        out["launch_now"] = False
        patched.append(out)
    return patched


def request_coverage_rows(
    request_rows: list[dict[str, Any]], snap_rows: list[dict[str, Any]], render_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    snap_by_uid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    render_by_uid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in snap_rows:
        snap_by_uid[str(row.get("benchmark_row_uid"))].append(row)
    for row in render_rows:
        render_by_uid[str(row.get("benchmark_row_uid"))].append(row)
    rows: list[dict[str, Any]] = []
    for request in request_rows:
        uid = str(request.get("benchmark_row_uid"))
        snaps = snap_by_uid.get(uid, [])
        renders = render_by_uid.get(uid, [])
        rows.append(
            {
                "version": VERSION,
                "row_type": "request_snap_render_coverage",
                "scale_request_uid": request.get("scale_request_uid"),
                "benchmark_row_uid": uid,
                "adapter_episode_id": request.get("adapter_episode_id"),
                "scan_id": request.get("scan_id"),
                "scene_key": request.get("scene_key"),
                "object_category": request.get("object_category"),
                "snap_validation_rows": len(snaps),
                "snap_ready_rows": sum(1 for row in snaps if row.get("snap_validation_ready")),
                "source_ready_rows": sum(1 for row in snaps if row.get("source_ready_for_m180")),
                "render_plan_rows": len(renders),
                "request_snap_ready": any(row.get("snap_validation_ready") for row in snaps),
                "request_source_ready": any(row.get("source_ready_for_m180") for row in snaps),
                "request_render_ready": bool(renders),
            }
        )
    return rows


def build_readiness_rows(
    m192: dict[str, Any],
    request_rows: list[dict[str, Any]],
    pose_rows: list[dict[str, Any]],
    snap_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    detector_manifest_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    docker: dict[str, Any],
    m178: Any,
) -> list[dict[str, Any]]:
    prefix = docker.get("selected_prefix") or ["docker"]
    habitat_image = m178.image_status(prefix, m178.HABITAT_IMAGE) if docker.get("available") else {"available": False}
    real_image = m178.image_status(prefix, m178.REAL_SMOKE_IMAGE) if docker.get("available") else {"available": False}
    coverage_rows = request_coverage_rows(request_rows, snap_rows, render_rows)
    all_requests_snap_ready = bool(coverage_rows) and all(row["request_snap_ready"] for row in coverage_rows)
    all_requests_source_ready = bool(coverage_rows) and all(row["request_source_ready"] for row in coverage_rows)
    all_requests_render_ready = bool(coverage_rows) and all(row["request_render_ready"] for row in coverage_rows)
    render_count = len(render_rows)
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m192_ready",
            "gate_status": "pass"
            if m192.get("status") == "e008_m192_source_pool_protected_confidence_scale_denominator_materialization_ready"
            else "fail",
            "blocks_m193": True,
            "details": m192.get("status"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "source_pose_rows_match_contract",
            "gate_status": "pass" if len(pose_rows) == EXPECTED_SOURCE_POSE_ROWS else "fail",
            "blocks_m193": True,
            "details": {"source_pose_rows": len(pose_rows), "expected": EXPECTED_SOURCE_POSE_ROWS},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "snap_validation_rows_ready",
            "gate_status": "pass" if len(snap_rows) == len(pose_rows) and snap_rows else "fail",
            "blocks_m193": True,
            "details": {"snap_rows": len(snap_rows), "pose_rows": len(pose_rows)},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "all_requests_have_snap_ready_pose",
            "gate_status": "pass" if all_requests_snap_ready else "fail",
            "blocks_m193": True,
            "details": {
                "request_rows": len(coverage_rows),
                "snap_ready_requests": sum(1 for row in coverage_rows if row["request_snap_ready"]),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "all_source_poses_snap_ready",
            "gate_status": "pass"
            if sum(1 for row in snap_rows if row.get("snap_validation_ready")) == len(pose_rows) and pose_rows
            else "warning"
            if snap_rows
            else "fail",
            "blocks_m193": False,
            "details": {
                "snap_ready_rows": sum(1 for row in snap_rows if row.get("snap_validation_ready")),
                "source_pose_rows": len(pose_rows),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "all_requests_have_source_ready_pose",
            "gate_status": "pass" if all_requests_source_ready else "warning",
            "blocks_m193": False,
            "details": {
                "request_rows": len(coverage_rows),
                "source_ready_requests": sum(1 for row in coverage_rows if row["request_source_ready"]),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "scale_render_rows_ready",
            "gate_status": "pass"
            if render_count == EXPECTED_RENDER_PLAN_ROWS
            else "warning"
            if render_count > 0 and all_requests_render_ready
            else "fail",
            "blocks_m193": not (render_count > 0 and all_requests_render_ready),
            "details": {"render_rows": render_count, "expected": EXPECTED_RENDER_PLAN_ROWS},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "detector_manifest_ready",
            "gate_status": "pass" if len(detector_manifest_rows) == len(request_rows) and request_rows else "warning"
            if detector_manifest_rows
            else "fail",
            "blocks_m193": not bool(detector_manifest_rows),
            "details": {"detector_manifest_rows": len(detector_manifest_rows), "request_rows": len(request_rows)},
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "launcher_inputs_written",
            "gate_status": "pass" if input_rows and all(row.get("ready") for row in input_rows) else "fail",
            "blocks_m193": True,
            "details": Counter(str(row.get("ready")) for row in input_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "external_hm3d_data_readonly_source_ready",
            "gate_status": "pass" if m178.RESEARCH2_DATA_ROOT.exists() else "fail",
            "blocks_m193": True,
            "details": str(m178.RESEARCH2_DATA_ROOT),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "docker_available",
            "gate_status": "pass" if docker.get("available") else "fail",
            "blocks_m193": True,
            "details": docker.get("mode"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "habitat_image_available",
            "gate_status": "pass" if habitat_image.get("available") else "warning",
            "blocks_m194": True,
            "details": m178.HABITAT_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if real_image.get("available") else "warning",
            "blocks_m194": True,
            "details": m178.REAL_SMOKE_IMAGE,
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "tmux_sessions_free",
            "gate_status": "pass"
            if not m178.tmux_running(m178.RENDER_TMUX_SESSION)
            and not m178.tmux_running(m178.DETECTOR_TMUX_SESSION)
            else "warning",
            "blocks_m194": True,
            "details": [m178.RENDER_TMUX_SESSION, m178.DETECTOR_TMUX_SESSION],
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "source_pool_scale_snap_launcher_contract",
            "support_status": "supported_if_ready",
            "allowed_claim": (
                "M193 validates source-pool scale pose snap readiness and writes exact render/detector "
                "launcher inputs for M194."
            ),
            "blocked_claims": [
                "expanded source-pool candidates recover targets",
                "real RGB-D/open-vocabulary robustness is solved",
                "real navigation SR/SPL improves",
                "deployable search policy is ready",
                "human intent is a main contribution",
            ],
        }
    ]


def build_reviewer_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "Does M193 tune the source-pool denominator after seeing detector or navigation outcomes?",
            "answer": (
                "No. It consumes the M192 30-request / 240-pose denominator and performs only navmesh/snap "
                "validation plus launcher input materialization before detector inference or goal evaluation."
            ),
            "evidence": {
                "scale_request_rows": coverage["scale_request_rows"],
                "source_pose_rows": coverage["source_pose_rows"],
                "render_plan_rows": coverage["render_plan_rows"],
            },
        },
        {
            "version": VERSION,
            "question": "Why is detector prompt use allowed here?",
            "answer": (
                "The object category is a query input, but ObjectNav goal coordinates/viewpoints, success labels, "
                "and target ids remain blocked."
            ),
        },
        {
            "version": VERSION,
            "question": "Does M193 itself support real navigation claims?",
            "answer": "No. It is a snap/launcher contract. M194 render/detector, candidate validation, proxy goal evaluation, Docker trajectory execution, and protected-baseline interpretation remain required.",
        },
    ]


def build_report(coverage: dict[str, Any]) -> str:
    rows = [
        {"metric": "scale_request_rows", "value": coverage["scale_request_rows"]},
        {"metric": "source_pose_rows", "value": coverage["source_pose_rows"]},
        {"metric": "snap_ready_rows", "value": f"{coverage['snap_ready_rows']} / {coverage['snap_validation_rows']}"},
        {"metric": "source_ready_rows", "value": f"{coverage['source_ready_rows']} / {coverage['snap_validation_rows']}"},
        {"metric": "render_plan_rows", "value": coverage["render_plan_rows"]},
        {"metric": "detector_manifest_rows", "value": coverage["detector_manifest_rows"]},
        {"metric": "m194_gate_ready", "value": coverage["m194_gate_ready"]},
    ]
    return "\n".join(
        [
            "# E008-M193 Source-Pool Scale Navmesh/Snap Launcher Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M192 status: `{coverage['m192_status']}`.",
            f"- Scale request rows: {coverage['scale_request_rows']}.",
            f"- Source pose rows: {coverage['source_pose_rows']}.",
            f"- Snap-ready rows: {coverage['snap_ready_rows']} / {coverage['snap_validation_rows']}.",
            f"- Source-ready rows for downstream validation: {coverage['source_ready_rows']} / {coverage['snap_validation_rows']}.",
            f"- Render plan rows: {coverage['render_plan_rows']} / expected {EXPECTED_RENDER_PLAN_ROWS}.",
            f"- Detector manifest rows: {coverage['detector_manifest_rows']}.",
            f"- Launcher input rows: {coverage['launcher_input_materialization_rows']}.",
            f"- M194 gate ready: {str(coverage['m194_gate_ready']).lower()}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Summary Table",
            "",
            table(rows, ["metric", "value"]),
            "",
            "## Claim Boundary",
            "",
            "- M193 validates source-pool scale pose feasibility and records render/detector launcher inputs only.",
            "- It does not render frames, run detector inference, evaluate targets, or execute trajectories.",
            "- Real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, and human-intent main claim remain blocked.",
            "",
            "## Next",
            "",
            f"- {NEXT_UNIT}.",
            "",
        ]
    )


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> int:
    m178 = load_m178()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    m178.LOG_DIR.mkdir(parents=True, exist_ok=True)

    m192 = read_json(M192_ARTIFACT_DIR / "coverage.json")
    request_rows = read_jsonl(M192_ARTIFACT_DIR / "source_pool_scale_request_rows.jsonl")
    pose_rows = read_jsonl(M192_ARTIFACT_DIR / "source_pool_observation_pose_rows.jsonl")
    write_jsonl(ARTIFACT_DIR / "snap_input_rows.jsonl", pose_rows)

    docker = m178.docker_status()
    snap_rows, snap_meta = m178.run_habitat_snap_validation(ARTIFACT_DIR / "snap_input_rows.jsonl", docker)
    render_rows = enrich_render_rows(m178.build_render_plan_rows(snap_rows), snap_rows)
    object_target_rows = enrich_object_target_rows(m178.build_object_target_rows(render_rows))
    prompt_payload = enrich_prompt_payload(m178.build_prompt_set(object_target_rows))
    schema_payload = patch_text(m178.proposal_output_schema())
    schema_payload["version"] = VERSION
    detector_manifest_rows = enrich_detector_manifest_rows(
        m178.build_detector_manifest_rows(
            render_rows,
            DATA_OUT_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl",
            DATA_OUT_DIR / "detector_inputs" / "prompt_set.json",
            DATA_OUT_DIR / "detector_inputs" / "proposal_output_schema.json",
        ),
        render_rows,
    )
    expected_rows = enrich_expected_rows(m178.expected_file_summary_rows(render_rows), render_rows)
    input_rows = patch_launcher_inputs(
        m178.write_launcher_inputs(
            render_rows=render_rows,
            detector_manifest_rows=detector_manifest_rows,
            object_target_rows=object_target_rows,
            prompt_payload=prompt_payload,
            schema_payload=schema_payload,
        )
    )
    command_rows = patch_command_rows(m178.build_long_job_command_rows(docker, detector_manifest_rows))
    coverage_rows = request_coverage_rows(request_rows, snap_rows, render_rows)
    readiness_rows = build_readiness_rows(
        m192=m192,
        request_rows=request_rows,
        pose_rows=pose_rows,
        snap_rows=snap_rows,
        render_rows=render_rows,
        detector_manifest_rows=detector_manifest_rows,
        input_rows=input_rows,
        docker=docker,
        m178=m178,
    )

    blockers = [
        str(row.get("gate_id"))
        for row in readiness_rows
        if row.get("blocks_m193") and row.get("gate_status") == "fail"
    ]
    warning_rows = [row for row in readiness_rows if row.get("gate_status") == "warning"]
    status = BLOCKED_STATUS if blockers else READY_WARNING_STATUS if warning_rows else READY_STATUS
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "warnings": [str(row.get("gate_id")) for row in warning_rows],
        "m192_status": m192.get("status"),
        "scale_denominator_id": SELECTED_DENOMINATOR,
        "selected_method_id": SELECTED_METHOD,
        "primary_ablation_id": PRIMARY_ABLATION,
        "protected_default_policy_id": PROTECTED_DEFAULT,
        "scale_request_rows": len(request_rows),
        "source_pose_rows": len(pose_rows),
        "snap_validation_rows": len(snap_rows),
        "snap_ready_rows": sum(1 for row in snap_rows if row.get("snap_validation_ready")),
        "source_ready_rows": sum(1 for row in snap_rows if row.get("source_ready_for_m180")),
        "request_snap_ready_rows": sum(1 for row in coverage_rows if row.get("request_snap_ready")),
        "request_source_ready_rows": sum(1 for row in coverage_rows if row.get("request_source_ready")),
        "request_render_ready_rows": sum(1 for row in coverage_rows if row.get("request_render_ready")),
        "snap_warning_rows": sum(1 for row in snap_rows if row.get("snap_warning_large_move")),
        "render_plan_rows": len(render_rows),
        "expected_render_plan_rows": EXPECTED_RENDER_PLAN_ROWS,
        "detector_manifest_rows": len(detector_manifest_rows),
        "object_target_rows": len(object_target_rows),
        "expected_file_summary_rows": len(expected_rows),
        "launcher_input_materialization_rows": len(input_rows),
        "long_job_command_rows": len(command_rows),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if row.get("gate_status") == "fail"),
        "readiness_gate_warning_rows": len(warning_rows),
        "snap_validation_meta": snap_meta,
        "render_input_dir": str(DATA_OUT_DIR / "render_inputs"),
        "detector_input_dir": str(DATA_OUT_DIR / "detector_inputs"),
        "render_plan_output": str(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl"),
        "detector_manifest_output": str(DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl"),
        "m194_gate_ready": status in {READY_STATUS, READY_WARNING_STATUS},
        "launch_long_job_now": False,
        "render_job_launched": False,
        "detector_job_launched": False,
        "detector_candidate_rows_ready": False,
        "candidate_navmesh_validation_ready": False,
        "goal_evaluation_proxy_ready": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT if status in {READY_STATUS, READY_WARNING_STATUS} else "repair E008-M193 blockers",
    }

    route_rows = [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision": "m193_ready_select_m194" if coverage["m194_gate_ready"] else "m193_blocked",
            "selected_next_unit": coverage["selected_next_unit"],
            "requires_long_job_next": coverage["m194_gate_ready"],
            "launch_long_job_now": False,
            "reason": (
                "M193 validated source-pool scale snap readiness and wrote render/detector launcher inputs."
                if coverage["m194_gate_ready"]
                else "M193 has blocking readiness failures."
            ),
        }
    ]
    gate_rows = [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M193 readiness gates pass and M194 render/detector commands are recorded but not launched.",
            "observed": coverage["m194_gate_ready"],
            "next_action": coverage["selected_next_unit"],
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "Snap validation is partial or source-readiness warning exists.",
            "observed": bool(coverage["warnings"]),
            "next_action": "Proceed only as diagnostic and keep source-ready/source-gap split downstream.",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "M192 not ready, Docker/Habitat unavailable, no snap-ready request, no render rows, or no launcher inputs.",
            "observed": bool(coverage["blockers"]),
            "next_action": "Do not launch M194 until blockers are fixed.",
        },
    ]
    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "next_unit": coverage["selected_next_unit"],
            "action": "Launch E008-M194 render job in tmux; after render verification, launch detector job.",
            "launch_long_job_now": False,
        }
    ]

    outputs: dict[str, Any] = {
        "snap_validation_rows.jsonl": snap_rows,
        "request_snap_render_coverage_rows.jsonl": coverage_rows,
        "source_pool_render_plan_rows.jsonl": render_rows,
        "source_pool_detector_manifest_rows.jsonl": detector_manifest_rows,
        "source_pool_object_target_rows.jsonl": object_target_rows,
        "expected_file_summary_rows.jsonl": expected_rows,
        "launcher_input_materialization_rows.jsonl": input_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "long_job_command_rows.jsonl": command_rows,
        "m194_gate_rows.jsonl": gate_rows,
        "claim_boundary_rows.jsonl": build_claim_rows(),
        "reviewer_defense_rows.jsonl": build_reviewer_rows(coverage),
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_action_rows,
    }
    output_paths: list[Path] = []
    for name, payload in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, payload)
        output_paths.append(path)

    write_json(ARTIFACT_DIR / "source_pool_prompt_set.json", prompt_payload)
    write_json(ARTIFACT_DIR / "source_pool_proposal_output_schema.json", schema_payload)
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    output_paths.extend(
        [
            ARTIFACT_DIR / "source_pool_prompt_set.json",
            ARTIFACT_DIR / "source_pool_proposal_output_schema.json",
            ARTIFACT_DIR / "coverage.json",
            ARTIFACT_DIR / "report.md",
        ]
    )
    mirror_outputs(output_paths)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    return 0 if coverage["m194_gate_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
