#!/usr/bin/env python3
"""Launch ConceptGraphs runtime for M32-approved pending staged scans."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M32_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M32_conceptgraphs_scale_decision_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M33_conceptgraphs_pending_scan_runtime_v0"
SESSION = "e005_m33_conceptgraphs_pending_scans"
IMAGE = "research2/conceptgraphs-smoke:latest"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
MODEL_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache"
GSA_CACHE = MODEL_CACHE / "gsa"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"
PYTHON_BIN = "/opt/conda/envs/conceptgraph/bin/python"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def tmux_running() -> bool:
    return run(["tmux", "has-session", "-t", SESSION], timeout=10)["ok"]


def image_ready() -> bool:
    return run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)["ok"]


def expected_for_scan(scan_id: str) -> dict[str, Any]:
    scan_root = STAGED_ROOT / scan_id
    return {
        "scan_id": scan_id,
        "gsa_detection_pattern": str(scan_root / "gsa_detections_none" / "*.pkl.gz"),
        "full_pcd": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"),
        "full_pcd_post": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"),
    }


def container_script(scan_ids: list[str]) -> str:
    dataset_root = "/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet"
    dataset_config = f"{dataset_root}/config/conceptgraphs_3rscan_depth_aligned_scannet.yaml"
    lines = [
        "set -euo pipefail",
        "cd /workspace/concept-graphs/conceptgraph",
    ]
    for scan_id in scan_ids:
        quoted_scan = shlex.quote(scan_id)
        lines.extend(
            [
                f"echo '[E005-M33] start scan {scan_id}'",
                (
                    f"{PYTHON_BIN} scripts/generate_gsa_results.py "
                    f"--dataset_root {shlex.quote(dataset_root)} "
                    f"--dataset_config {shlex.quote(dataset_config)} "
                    f"--scene_id {quoted_scan} --class_set none --stride 5 --device cuda"
                ),
                (
                    f"{PYTHON_BIN} slam/cfslam_pipeline_batch.py "
                    f"dataset_root={shlex.quote(dataset_root)} "
                    f"dataset_config={shlex.quote(dataset_config)} "
                    f"scene_id={quoted_scan} "
                    "stride=5 spatial_sim_type=overlap mask_conf_threshold=0.95 "
                    "match_method=sim_sum sim_threshold=1.2 dbscan_eps=0.1 "
                    "gsa_variant=none class_agnostic=True skip_bg=True max_bbox_area_ratio=0.5 "
                    f"save_suffix={shlex.quote(SAVE_SUFFIX)} "
                    "merge_interval=20 merge_visual_sim_thresh=0.8 merge_text_sim_thresh=0.8"
                ),
                f"echo '[E005-M33] completed scan {scan_id}'",
            ]
        )
    return "; ".join(lines)


def docker_command(scan_ids: list[str]) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--network=host",
        "-e",
        "GSA_PATH=/workspace/Grounded-Segment-Anything",
        "-e",
        "HF_HOME=/opt/conceptgraphs_cache/huggingface",
        "-e",
        "TORCH_HOME=/opt/conceptgraphs_cache/torch",
        "-e",
        "XDG_CACHE_HOME=/opt/conceptgraphs_cache/xdg",
        "-e",
        "MPLCONFIGDIR=/tmp/matplotlib",
        "-e",
        "PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128",
        "-v",
        f"{STAGED_ROOT}:/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet:rw",
        "-v",
        f"{MODEL_CACHE}:/opt/conceptgraphs_cache:rw",
        "-v",
        f"{GSA_CACHE / 'sam_vit_h_4b8939.pth'}:/workspace/Grounded-Segment-Anything/sam_vit_h_4b8939.pth:ro",
        "-v",
        f"{GSA_CACHE / 'groundingdino_swint_ogc.pth'}:/workspace/Grounded-Segment-Anything/groundingdino_swint_ogc.pth:ro",
        "-w",
        "/workspace/concept-graphs/conceptgraph",
        IMAGE,
        "bash",
        "-lc",
        container_script(scan_ids),
    ]


def preflight(scan_ids: list[str]) -> dict[str, Any]:
    rows = []
    for scan_id in scan_ids:
        root = STAGED_ROOT / scan_id
        rows.append(
            {
                "scan_id": scan_id,
                "scan_root_exists": root.exists(),
                "color_count": len(list((root / "color").glob("*.jpg"))) if root.exists() else 0,
                "depth_count": len(list((root / "depth").glob("*.png"))) if root.exists() else 0,
                "pose_count": len(list((root / "pose").glob("*.txt"))) if root.exists() else 0,
            }
        )
    return {
        "image_ready": image_ready(),
        "staged_root_exists": STAGED_ROOT.exists(),
        "dataset_config_exists": (STAGED_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml").exists(),
        "sam_checkpoint_exists": (GSA_CACHE / "sam_vit_h_4b8939.pth").exists(),
        "groundingdino_checkpoint_exists": (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(),
        "scan_rows": rows,
    }


def write_run_script(path: Path, status_path: Path, command: list[str], scan_ids: list[str]) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"SCAN_IDS={shlex.quote(','.join(scan_ids))}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" SCAN_IDS=\"$SCAN_IDS\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'scan_ids': [x for x in os.environ['SCAN_IDS'].split(',') if x],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running conceptgraphs_pending_scan_runtime \"E005-M33 ConceptGraphs pending scan runtime started\" 0",
        shlex.join(command),
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed conceptgraphs_pending_scan_runtime \"E005-M33 ConceptGraphs pending scan runtime failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed completed \"E005-M33 ConceptGraphs pending scan runtime completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m32 = read_json(M32_DIR / "coverage.json")
    scan_rows = read_jsonl(M32_DIR / "scan_rows.jsonl")
    pending_scan_ids = [row["scan_id"] for row in scan_rows if row.get("launch_required")]
    expected_rows = [expected_for_scan(scan_id) for scan_id in pending_scan_ids]
    preflight_state = preflight(pending_scan_ids)
    blockers: list[str] = []
    if m32.get("status") != "e005_m32_conceptgraphs_scale_decision_approved":
        blockers.append("m32_not_approved")
    if not pending_scan_ids:
        blockers.append("no_pending_scan_ids")
    for key in ["image_ready", "staged_root_exists", "dataset_config_exists", "sam_checkpoint_exists", "groundingdino_checkpoint_exists"]:
        if not preflight_state.get(key):
            blockers.append(key)
    for row in preflight_state["scan_rows"]:
        if not row["scan_root_exists"] or row["color_count"] <= 0 or row["depth_count"] <= 0 or row["pose_count"] <= 0:
            blockers.append(f"scan_payload_missing:{row['scan_id']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m33_conceptgraphs_pending_scans.log"
    status_path = OUT_DIR / "background_status.json"
    run_script = OUT_DIR / "run_m33_conceptgraphs_pending_scans.sh"
    command = docker_command(pending_scan_ids)
    write_run_script(run_script, status_path, command, pending_scan_ids)
    write_text(OUT_DIR / "docker_command.txt", shlex.join(command) + "\n")
    write_jsonl(OUT_DIR / "expected_outputs.jsonl", expected_rows)

    launch_executed = False
    launch_result = {"ok": False, "stdout": "", "stderr": "not_launched", "cmd": []}
    if blockers:
        status = "e005_m33_conceptgraphs_pending_scan_runtime_blocked_preflight"
    elif tmux_running():
        status = "e005_m33_conceptgraphs_pending_scan_runtime_already_running"
    else:
        launch_cmd = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1"
        launch_result = run(["tmux", "new", "-d", "-s", SESSION, launch_cmd], timeout=20)
        launch_executed = launch_result["ok"]
        status = (
            "e005_m33_conceptgraphs_pending_scan_runtime_job_launched"
            if launch_result["ok"]
            else "e005_m33_conceptgraphs_pending_scan_runtime_launch_failed"
        )

    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_session": SESSION,
        "tmux_running_after_launch": tmux_running(),
        "launch_executed": launch_executed,
        "launch_result": launch_result,
        "blockers": blockers,
        "pending_scan_ids": pending_scan_ids,
        "pending_scan_count": len(pending_scan_ids),
        "preflight": preflight_state,
        "log_path": str(log_path),
        "run_script": str(run_script),
        "background_status_path": str(status_path),
        "expected_outputs": expected_rows,
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m33_conceptgraphs_pending_scans.py",
        "next_recommended_unit": "E005-M34 ConceptGraphs pending-scan runtime completion verification",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
