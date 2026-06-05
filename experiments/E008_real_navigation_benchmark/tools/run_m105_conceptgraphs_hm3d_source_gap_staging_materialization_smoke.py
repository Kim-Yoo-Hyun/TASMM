#!/usr/bin/env python3
"""Materialize ConceptGraphs-compatible HM3D source-gap staging inputs."""

from __future__ import annotations

import filecmp
import json
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M104_DIR = EXP_ROOT / "artifacts" / "E008-M104_conceptgraphs_hm3d_source_gap_adapter_preflight_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
)
STAGED_ROOT = DATA_OUT_DIR / "conceptgraphs_hm3d_source_gap_staged"
CONFIG_PATH = STAGED_ROOT / "config" / "conceptgraphs_hm3d_source_gap.yaml"

VERSION = "e008_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
READY_STATUS = "e008_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_ready"
BLOCKED_STATUS = "e008_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_blocked"
NEXT_UNIT = "E008-M106 ConceptGraphs HM3D source-gap runtime launch/verification contract"
CONCEPTGRAPHS_IMAGE = "research2/conceptgraphs-smoke:latest"
CONTAINER_DATASET_ROOT = "/data/ConceptGraphs_hm3d_source_gap"
CONTAINER_CONFIG_PATH = f"{CONTAINER_DATASET_ROOT}/config/conceptgraphs_hm3d_source_gap.yaml"


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


def write_json(path: Path, payload: Any) -> None:
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


def parse_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "parse_ready": False}
    out: dict[str, Any] = {"exists": True}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, raw = [part.strip() for part in line.split("=", 1)]
        if key in {"m_colorWidth", "m_colorHeight", "m_depthWidth", "m_depthHeight", "m_frames.size"}:
            out[key] = int(float(raw))
        elif key == "m_depthShift":
            out[key] = float(raw)
        elif key in {"m_calibrationColorIntrinsic", "m_calibrationDepthIntrinsic"}:
            out[key] = [float(token) for token in raw.split()]
    matrix = out.get("m_calibrationDepthIntrinsic") or out.get("m_calibrationColorIntrinsic")
    out["parse_ready"] = isinstance(matrix, list) and len(matrix) == 16
    if out["parse_ready"]:
        out["fx"] = matrix[0]
        out["fy"] = matrix[5]
        out["cx"] = matrix[2]
        out["cy"] = matrix[6]
    return out


def write_intrinsics(target_intrinsic: Path, info: dict[str, Any]) -> bool:
    if not info.get("parse_ready"):
        return False
    matrix = "\n".join(
        [
            f"{float(info['fx']):.9f} 0 {float(info['cx']):.9f} 0",
            f"0 {float(info['fy']):.9f} {float(info['cy']):.9f} 0",
            "0 0 1 0",
            "0 0 0 1",
            "",
        ]
    )
    target_intrinsic.mkdir(parents=True, exist_ok=True)
    for name in ["intrinsic_color.txt", "intrinsic_depth.txt"]:
        path = target_intrinsic / name
        if not path.exists() or path.read_text(encoding="utf-8", errors="replace") != matrix:
            path.write_text(matrix, encoding="utf-8")
    return True


def write_dataset_config(info: dict[str, Any]) -> None:
    width = int(info.get("m_colorWidth") or info.get("m_depthWidth") or 640)
    height = int(info.get("m_colorHeight") or info.get("m_depthHeight") or 480)
    fx = float(info.get("fx", 320.0))
    fy = float(info.get("fy", 320.0))
    cx = float(info.get("cx", width / 2.0))
    cy = float(info.get("cy", height / 2.0))
    depth_scale = float(info.get("m_depthShift", 1000.0))
    write_text(
        CONFIG_PATH,
        "\n".join(
            [
                "dataset_name: 'scannet'",
                "camera_params:",
                f"  image_height: {height}",
                f"  image_width: {width}",
                f"  fx: {fx:.9f}",
                f"  fy: {fy:.9f}",
                f"  cx: {cx:.9f}",
                f"  cy: {cy:.9f}",
                f"  png_depth_scale: {depth_scale:.1f}",
                "",
            ]
        ),
    )


def image_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        with Image.open(path) as image:
            return {
                "exists": True,
                "format": image.format,
                "height": image.size[1],
                "mode": image.mode,
                "width": image.size[0],
            }
    except Exception as exc:  # noqa: BLE001 - smoke records corrupt files.
        return {"exists": True, "error": str(exc)}


def raw_frame_ids(sequence_dir: Path) -> list[str]:
    color_ids = {path.name.removeprefix("frame-").removesuffix(".color.jpg") for path in sequence_dir.glob("frame-*.color.jpg")}
    depth_ids = {path.name.removeprefix("frame-").removesuffix(".depth.pgm") for path in sequence_dir.glob("frame-*.depth.pgm")}
    pose_ids = {path.name.removeprefix("frame-").removesuffix(".pose.txt") for path in sequence_dir.glob("frame-*.pose.txt")}
    return sorted(color_ids & depth_ids & pose_ids)


def copy_regular(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.is_file() and filecmp.cmp(src, dst, shallow=False):
        return False
    shutil.copyfile(src, dst)
    return True


def convert_depth_png(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        existing = image_info(dst)
        source = image_info(src)
        if existing.get("width") == source.get("width") and existing.get("height") == source.get("height"):
            return False
    with Image.open(src) as image:
        depth = image.convert("I;16")
        depth.save(dst, format="PNG")
    return True


def pose_matrix_valid(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        rows = [[float(value) for value in line.split()] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except ValueError:
        return False
    return len(rows) == 4 and all(len(row) == 4 for row in rows)


def chmod_for_container(root: Path) -> dict[str, int]:
    changed_dirs = 0
    changed_files = 0
    for path in [root, *root.rglob("*")]:
        try:
            desired = 0o777 if path.is_dir() else 0o666
            current = stat.S_IMODE(path.stat().st_mode)
            if current != desired:
                path.chmod(desired)
                if path.is_dir():
                    changed_dirs += 1
                else:
                    changed_files += 1
        except FileNotFoundError:
            continue
    return {"permission_changed_dirs": changed_dirs, "permission_changed_files": changed_files}


def docker_image_ready(image: str) -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except Exception:
        return False
    return proc.returncode == 0


def run_container_readability_smoke(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [f"test -f {CONTAINER_CONFIG_PATH}"]
    for row in scan_rows:
        scan_id = row["scan_id"]
        checks.extend(
            [
                f"test -f {CONTAINER_DATASET_ROOT}/{scan_id}/color/000000.jpg",
                f"test -f {CONTAINER_DATASET_ROOT}/{scan_id}/depth/000000.png",
                f"test -f {CONTAINER_DATASET_ROOT}/{scan_id}/pose/000000.txt",
                f"test -f {CONTAINER_DATASET_ROOT}/{scan_id}/intrinsic/intrinsic_color.txt",
            ]
        )
    command = " && ".join(checks) + " && echo container_read_ok"
    row: dict[str, Any] = {
        "version": VERSION,
        "row_type": "container_readability_smoke",
        "image": CONCEPTGRAPHS_IMAGE,
        "host_dataset_root": str(STAGED_ROOT),
        "container_dataset_root": CONTAINER_DATASET_ROOT,
        "command": command,
        "image_ready": docker_image_ready(CONCEPTGRAPHS_IMAGE),
        "container_readable": False,
        "stdout_tail": "",
        "stderr_tail": "",
        "returncode": None,
    }
    if not row["image_ready"]:
        row["stderr_tail"] = "docker_image_not_ready"
        return [row]
    try:
        proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{STAGED_ROOT}:{CONTAINER_DATASET_ROOT}:ro",
                CONCEPTGRAPHS_IMAGE,
                "bash",
                "-lc",
                command,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )
        row["returncode"] = proc.returncode
        row["stdout_tail"] = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        row["stderr_tail"] = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""
        row["container_readable"] = proc.returncode == 0 and row["stdout_tail"] == "container_read_ok"
    except Exception as exc:  # noqa: BLE001 - smoke records Docker failures.
        row["stderr_tail"] = repr(exc)
    return [row]


def selected_source_layout(case_row: dict[str, Any], layout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scan_id = str(case_row["scan_id"])
    bundle = str(case_row["selected_source_bundle"])
    for row in layout_rows:
        if str(row.get("scan_id")) == scan_id and str(row.get("bundle_id")) == bundle:
            return row
    return {}


def materialize_case(case_row: dict[str, Any], layout_row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scan_id = str(case_row["scan_id"])
    sequence_dir = Path(str(layout_row.get("sequence_dir", "")))
    target_scan = Path(str(case_row["target_staging_dir"]))
    target_color = target_scan / "color"
    target_depth = target_scan / "depth"
    target_pose = target_scan / "pose"
    target_intrinsic = target_scan / "intrinsic"
    for directory in [target_color, target_depth, target_pose, target_intrinsic]:
        directory.mkdir(parents=True, exist_ok=True)

    info = parse_info(sequence_dir / "_info.txt")
    frame_ids = raw_frame_ids(sequence_dir)
    frame_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    color_written = 0
    depth_written = 0
    pose_written = 0
    for frame_id in frame_ids:
        src_color = sequence_dir / f"frame-{frame_id}.color.jpg"
        src_depth = sequence_dir / f"frame-{frame_id}.depth.pgm"
        src_pose = sequence_dir / f"frame-{frame_id}.pose.txt"
        dst_color = target_color / f"{frame_id}.jpg"
        dst_depth = target_depth / f"{frame_id}.png"
        dst_pose = target_pose / f"{frame_id}.txt"
        try:
            color_changed = copy_regular(src_color, dst_color)
            depth_changed = convert_depth_png(src_depth, dst_depth)
            pose_changed = copy_regular(src_pose, dst_pose)
            color_written += int(color_changed)
            depth_written += int(depth_changed)
            pose_written += int(pose_changed)
            frame_rows.append(
                {
                    "version": VERSION,
                    "scan_id": scan_id,
                    "frame_id": frame_id,
                    "source_bundle": case_row["selected_source_bundle"],
                    "color_path": str(dst_color),
                    "depth_path": str(dst_depth),
                    "pose_path": str(dst_pose),
                    "color_regular_file": dst_color.is_file() and not dst_color.is_symlink(),
                    "depth_regular_file": dst_depth.is_file() and not dst_depth.is_symlink(),
                    "pose_regular_file": dst_pose.is_file() and not dst_pose.is_symlink(),
                    "pose_matrix_valid": pose_matrix_valid(dst_pose),
                }
            )
        except Exception as exc:  # noqa: BLE001 - materialization smoke records frame failures.
            errors.append({"frame_id": frame_id, "error": repr(exc)})

    intrinsic_written = write_intrinsics(target_intrinsic, info)
    permission_result = chmod_for_container(target_scan)
    color_files = sorted(target_color.glob("*.jpg"))
    depth_files = sorted(target_depth.glob("*.png"))
    pose_files = sorted(target_pose.glob("*.txt"))
    sample_color = image_info(color_files[0]) if color_files else {"exists": False}
    sample_depth = image_info(depth_files[0]) if depth_files else {"exists": False}
    sample_pose_valid = pose_matrix_valid(pose_files[0]) if pose_files else False
    expected_width = int(info.get("m_colorWidth", 0))
    expected_height = int(info.get("m_colorHeight", 0))
    frame_count_ok = len(frame_ids) > 0 and len(color_files) == len(depth_files) == len(pose_files) == len(frame_ids)
    resolution_ok = (
        sample_color.get("width") == sample_depth.get("width") == expected_width
        and sample_color.get("height") == sample_depth.get("height") == expected_height
    )
    regular_file_count = sum(
        1
        for directory, suffix in [(target_color, "*.jpg"), (target_depth, "*.png"), (target_pose, "*.txt")]
        for path in directory.glob(suffix)
        if path.is_file() and not path.is_symlink()
    )
    ready = (
        frame_count_ok
        and resolution_ok
        and bool(intrinsic_written)
        and (target_intrinsic / "intrinsic_color.txt").exists()
        and (target_intrinsic / "intrinsic_depth.txt").exists()
        and all(row["pose_matrix_valid"] for row in frame_rows)
        and not errors
    )
    row = {
        "version": VERSION,
        "row_type": "materialization",
        "scan_id": scan_id,
        "adapter_episode_id": case_row.get("adapter_episode_id"),
        "object_category": case_row.get("object_category"),
        "source_bundle": case_row.get("selected_source_bundle"),
        "source_sequence_dir": str(sequence_dir),
        "target_scan_dir": str(target_scan),
        "frame_count": len(frame_ids),
        "color_jpg_count": len(color_files),
        "depth_png_count": len(depth_files),
        "pose_txt_count": len(pose_files),
        "color_written_this_run": color_written,
        "depth_written_this_run": depth_written,
        "pose_written_this_run": pose_written,
        "regular_file_count": regular_file_count,
        "expected_regular_file_count": len(frame_ids) * 3,
        "frame_count_ok": frame_count_ok,
        "resolution_ok": resolution_ok,
        "intrinsic_color_exists": (target_intrinsic / "intrinsic_color.txt").exists(),
        "intrinsic_depth_exists": (target_intrinsic / "intrinsic_depth.txt").exists(),
        "intrinsic_written_or_ready": bool(intrinsic_written),
        "sample_color": sample_color,
        "sample_depth": sample_depth,
        "sample_pose_valid": sample_pose_valid,
        "info_parse_ready": bool(info.get("parse_ready")),
        "camera_width": expected_width,
        "camera_height": expected_height,
        "png_depth_scale": float(info.get("m_depthShift", 1000.0)),
        "error_count": len(errors),
        "errors": errors[:20],
        "uses_objectnav_eval_goal": False,
        "uses_objectnav_eval_viewpoint": False,
        "uses_target_object_id": False,
        "conceptgraphs_staging_ready": ready,
        **permission_result,
    }
    return row, frame_rows


def build_runtime_contract_rows(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in scan_rows:
        scan_id = row["scan_id"]
        rows.append(
            {
                "version": VERSION,
                "row_type": "future_runtime_contract",
                "scan_id": scan_id,
                "launch_now": False,
                "image": CONCEPTGRAPHS_IMAGE,
                "working_directory": "/workspace/concept-graphs/conceptgraph",
                "dataset_root": CONTAINER_DATASET_ROOT,
                "dataset_config": CONTAINER_CONFIG_PATH,
                "host_dataset_root": str(STAGED_ROOT),
                "container_mount": f"{STAGED_ROOT}:{CONTAINER_DATASET_ROOT}:rw",
                "expected_inputs": [
                    f"{CONTAINER_DATASET_ROOT}/{scan_id}/color/*.jpg",
                    f"{CONTAINER_DATASET_ROOT}/{scan_id}/depth/*.png",
                    f"{CONTAINER_DATASET_ROOT}/{scan_id}/pose/*.txt",
                    f"{CONTAINER_DATASET_ROOT}/{scan_id}/intrinsic/intrinsic_color.txt",
                ],
                "expected_outputs": [
                    f"{scan_id}/gsa_detections_none/*.pkl.gz",
                    f"{scan_id}/pcd_saves/full_pcd_none_<suffix>.pkl.gz",
                    f"{scan_id}/pcd_saves/full_pcd_none_<suffix>_post.pkl.gz",
                ],
                "verification_after_launch": "file counts plus object-map schema inspection; inspect only tail/head or targeted errors in logs",
                "claim_boundary": "Runtime output is required before candidate-generation, source-gap recovery, or navigation claims.",
            }
        )
    return rows


def build_m106_gate_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    ready = int(coverage["ready_scan_count"])
    total = int(coverage["scan_count"])
    return [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M105 materializes both selected source-gap cases with color/depth/pose/intrinsics/config ready and no leakage rows.",
            "current_ready_count": ready,
            "required_ready_count": total,
            "next_action": "Prepare a bounded ConceptGraphs runtime launch/verification contract.",
            "claim_status_after_gate": "input staging ready only; no source-gap recovery claim yet",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "Only one selected source-gap case is staging-ready, or regular-file/container-readiness checks are incomplete.",
            "current_ready_count": ready,
            "required_ready_count": total,
            "next_action": "repair M105 staging before runtime launch, or narrow to diagnostic one-case runtime only",
            "claim_status_after_gate": "diagnostic layout evidence only",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "No selected source-gap case is staging-ready, or intrinsic/depth conversion/leakage audit fails.",
            "current_ready_count": ready,
            "required_ready_count": total,
            "next_action": "do not launch ConceptGraphs; revisit adapter or alternative source route",
            "claim_status_after_gate": "ConceptGraphs HM3D route unsupported",
        },
    ]


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E008-M105 ConceptGraphs HM3D Source-Gap Staging Materialization Smoke",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Staged root: `{coverage['staged_root']}`.",
        f"- Dataset config: `{coverage['dataset_config']}`.",
        f"- Selected source-gap cases: {coverage['scan_count']}.",
        f"- Ready staged scans: {coverage['ready_scan_count']} / {coverage['scan_count']}.",
        f"- Total frames: {coverage['total_frame_count']}.",
        f"- Color/depth/pose files: {coverage['total_color_jpg_count']} / {coverage['total_depth_png_count']} / {coverage['total_pose_txt_count']}.",
        f"- Regular input files: {coverage['regular_file_count']} / {coverage['expected_regular_file_count']}.",
        f"- Container readability smoke: {str(coverage['container_readability_ready']).lower()}.",
        f"- Leakage rows: {coverage['leakage_row_count']}.",
        f"- Runtime launched: {str(coverage['runtime_launched']).lower()}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Scan Rows",
        "",
    ]
    for row in rows:
        lines.append(
            "- `{scan_id}` ({category}, {bundle}): ready {ready}, frames {frames}, "
            "color/depth/pose {color}/{depth}/{pose}, regular files {regular}/{expected_regular}.".format(
                scan_id=row["scan_id"],
                category=row["object_category"],
                bundle=row["source_bundle"],
                ready=str(row["conceptgraphs_staging_ready"]).lower(),
                frames=row["frame_count"],
                color=row["color_jpg_count"],
                depth=row["depth_png_count"],
                pose=row["pose_txt_count"],
                regular=row["regular_file_count"],
                expected_regular=row["expected_regular_file_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- M105 materializes `ConceptGraphs` input layout only; it does not run `ConceptGraphs`.",
            "- The staged files are regular host files rather than host-absolute symlinks, avoiding the previous container-readability failure mode.",
            "- Runtime launch, candidate export, source-gap recovery, trajectory execution, and final navigation claims remain future work.",
            "",
        ]
    )
    return "\n".join(lines)


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copyfile(path, DATA_OUT_DIR / path.name)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    m104 = read_json(M104_DIR / "coverage.json")
    case_rows = read_jsonl(M104_DIR / "case_staging_selection_rows.jsonl")
    layout_rows = read_jsonl(M104_DIR / "scan_layout_preflight_rows.jsonl")
    if not m104.get("adapter_preflight_ready"):
        raise SystemExit("M104 adapter preflight is not ready")

    scan_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []
    first_info: dict[str, Any] | None = None
    for case_row in case_rows:
        layout_row = selected_source_layout(case_row, layout_rows)
        if not layout_row:
            scan_rows.append(
                {
                    "version": VERSION,
                    "row_type": "materialization",
                    "scan_id": case_row.get("scan_id"),
                    "source_bundle": case_row.get("selected_source_bundle"),
                    "conceptgraphs_staging_ready": False,
                    "error_count": 1,
                    "errors": [{"error": "selected_source_layout_missing"}],
                }
            )
            continue
        row, frames = materialize_case(case_row, layout_row)
        if first_info is None:
            first_info = parse_info(Path(str(layout_row["sequence_dir"])) / "_info.txt")
        scan_rows.append(row)
        frame_rows.extend(frames)

    if first_info is None:
        first_info = {"parse_ready": False}
    write_dataset_config(first_info)
    chmod_for_container(STAGED_ROOT)

    leakage_rows = [
        row
        for row in scan_rows
        if bool(row.get("uses_objectnav_eval_goal"))
        or bool(row.get("uses_objectnav_eval_viewpoint"))
        or bool(row.get("uses_target_object_id"))
    ]
    ready_count = sum(1 for row in scan_rows if row.get("conceptgraphs_staging_ready"))
    error_count = sum(int(row.get("error_count", 0)) for row in scan_rows)
    status = READY_STATUS if scan_rows and ready_count == len(scan_rows) and error_count == 0 and not leakage_rows else BLOCKED_STATUS
    container_rows = run_container_readability_smoke(scan_rows)
    container_readability_ready = all(bool(row.get("container_readable")) for row in container_rows)
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m104_status": m104.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "staged_root": str(STAGED_ROOT),
        "dataset_config": str(CONFIG_PATH),
        "config_exists": CONFIG_PATH.exists(),
        "scan_count": len(scan_rows),
        "ready_scan_count": ready_count,
        "total_frame_count": sum(int(row.get("frame_count", 0)) for row in scan_rows),
        "total_color_jpg_count": sum(int(row.get("color_jpg_count", 0)) for row in scan_rows),
        "total_depth_png_count": sum(int(row.get("depth_png_count", 0)) for row in scan_rows),
        "total_pose_txt_count": sum(int(row.get("pose_txt_count", 0)) for row in scan_rows),
        "regular_file_count": sum(int(row.get("regular_file_count", 0)) for row in scan_rows),
        "expected_regular_file_count": sum(int(row.get("expected_regular_file_count", 0)) for row in scan_rows),
        "container_readability_ready": container_readability_ready,
        "leakage_row_count": len(leakage_rows),
        "error_count": error_count,
        "runtime_launched": False,
        "candidate_rows_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }
    runtime_rows = build_runtime_contract_rows(scan_rows)
    m106_gate_rows = build_m106_gate_rows(coverage)
    leakage_audit_rows = [
        {
            "version": VERSION,
            "scan_id": row.get("scan_id"),
            "uses_objectnav_eval_goal": bool(row.get("uses_objectnav_eval_goal")),
            "uses_objectnav_eval_viewpoint": bool(row.get("uses_objectnav_eval_viewpoint")),
            "uses_target_object_id": bool(row.get("uses_target_object_id")),
            "leakage_safe": not (
                bool(row.get("uses_objectnav_eval_goal"))
                or bool(row.get("uses_objectnav_eval_viewpoint"))
                or bool(row.get("uses_target_object_id"))
            ),
        }
        for row in scan_rows
    ]

    output_paths = [
        ARTIFACT_DIR / "coverage.json",
        ARTIFACT_DIR / "materialization_rows.jsonl",
        ARTIFACT_DIR / "frame_materialization_rows.jsonl",
        ARTIFACT_DIR / "runtime_contract_rows.jsonl",
        ARTIFACT_DIR / "container_readability_rows.jsonl",
        ARTIFACT_DIR / "m106_gate_rows.jsonl",
        ARTIFACT_DIR / "leakage_audit_rows.jsonl",
        ARTIFACT_DIR / "report.md",
    ]
    write_json(output_paths[0], coverage)
    write_jsonl(output_paths[1], scan_rows)
    write_jsonl(output_paths[2], frame_rows)
    write_jsonl(output_paths[3], runtime_rows)
    write_jsonl(output_paths[4], container_rows)
    write_jsonl(output_paths[5], m106_gate_rows)
    write_jsonl(output_paths[6], leakage_audit_rows)
    write_text(output_paths[7], build_report(coverage, scan_rows))
    mirror_outputs(output_paths)
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
