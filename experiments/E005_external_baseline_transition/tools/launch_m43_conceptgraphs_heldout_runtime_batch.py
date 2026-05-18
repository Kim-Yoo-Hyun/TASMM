#!/usr/bin/env python3
"""Launch one bounded ConceptGraphs heldout runtime batch."""

from __future__ import annotations

import argparse
import glob
import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "E005_external_baseline_transition"
M41_DIR = EXP_DIR / "artifacts" / "E005-M41_conceptgraphs_heldout_runtime_preflight_v0"
M42_DIR = EXP_DIR / "artifacts" / "E005-M42_conceptgraphs_heldout_staging_materialization_v0"
OUT_DIR = EXP_DIR / "artifacts" / "E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0"
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=timeout)
        return {
            "cmd": cmd,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "ok": False, "returncode": None, "stderr": repr(exc), "stdout": ""}


def image_ready() -> bool:
    return run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)["ok"]


def tmux_running(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session], timeout=10)["ok"]


def gpu_snapshot() -> dict[str, Any]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        timeout=10,
    )
    if not result["ok"] or not result["stdout"]:
        return {"available": False, "raw": result}
    first = result["stdout"].splitlines()[0]
    parts = [part.strip() for part in first.split(",")]
    if len(parts) < 4:
        return {"available": False, "raw": result}
    return {
        "available": True,
        "name": parts[0],
        "memory_total_mib": int(parts[1]),
        "memory_used_mib": int(parts[2]),
        "memory_free_mib": int(parts[3]),
        "raw": result,
    }


def expected_for_scan(scan_id: str) -> dict[str, Any]:
    scan_root = STAGED_ROOT / scan_id
    return {
        "full_pcd": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"),
        "full_pcd_post": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"),
        "gsa_detection_pattern": str(scan_root / "gsa_detections_none" / "*.pkl.gz"),
        "scan_id": scan_id,
    }


def output_ready(scan_id: str) -> bool:
    expected = expected_for_scan(scan_id)
    return (
        len(glob.glob(expected["gsa_detection_pattern"])) > 0
        and Path(expected["full_pcd"]).exists()
        and Path(expected["full_pcd_post"]).exists()
    )


def container_script(scan_ids: list[str], batch_id: str) -> str:
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
                f"echo '[E005-M43:{batch_id}] start scan {scan_id}'",
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
                f"echo '[E005-M43:{batch_id}] completed scan {scan_id}'",
            ]
        )
    return "; ".join(lines)


def docker_command(scan_ids: list[str], batch_id: str) -> list[str]:
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
        container_script(scan_ids, batch_id),
    ]


def scan_preflight(scan_ids: list[str]) -> list[dict[str, Any]]:
    rows = []
    for scan_id in scan_ids:
        root = STAGED_ROOT / scan_id
        color_count = len(list((root / "color").glob("*.jpg"))) if root.exists() else 0
        depth_count = len(list((root / "depth").glob("*.png"))) if root.exists() else 0
        pose_count = len(list((root / "pose").glob("*.txt"))) if root.exists() else 0
        rows.append(
            {
                "color_count": color_count,
                "depth_count": depth_count,
                "output_ready_before_launch": output_ready(scan_id),
                "pose_count": pose_count,
                "scan_id": scan_id,
                "scan_root": str(root),
                "scan_root_exists": root.exists(),
                "staged_payload_ready": root.exists() and color_count > 0 and color_count == depth_count == pose_count,
            }
        )
    return rows


def choose_batch(batch_rows: list[dict[str, Any]], requested: str | None) -> dict[str, Any]:
    if requested:
        for row in batch_rows:
            if row["batch_id"] == requested:
                return row
        raise SystemExit(f"unknown batch id: {requested}")
    for row in batch_rows:
        if not all(output_ready(scan_id) for scan_id in row["scan_ids"]):
            return row
    raise SystemExit("all batches already have runtime outputs")


def write_run_script(path: Path, status_path: Path, command: list[str], batch_id: str, scan_ids: list[str]) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"BATCH_ID={shlex.quote(batch_id)}",
        f"SCAN_IDS={shlex.quote(','.join(scan_ids))}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" BATCH_ID=\"$BATCH_ID\" SCAN_IDS=\"$SCAN_IDS\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'batch_id': os.environ['BATCH_ID'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'scan_ids': [x for x in os.environ['SCAN_IDS'].split(',') if x],",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running conceptgraphs_heldout_runtime \"E005-M43 heldout runtime batch started\" 0",
        shlex.join(command),
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed conceptgraphs_heldout_runtime \"E005-M43 heldout runtime batch failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed completed \"E005-M43 heldout runtime batch completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M43 ConceptGraphs Heldout Runtime Batch Launch",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Batch id: `{coverage['batch_id']}`.",
        f"- Scan count: {coverage['scan_count']}.",
        f"- Launch executed: {str(coverage['launch_executed']).lower()}.",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- tmux running after launch: {str(coverage['tmux_running_after_launch']).lower()}.",
        f"- Log path: `{coverage['log_path']}`.",
        f"- GPU free MiB before launch: {coverage['gpu_snapshot'].get('memory_free_mib')}.",
        f"- Blockers: {coverage['blockers']}.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Claim Boundary",
        "",
        "- E005-M43 is a runtime launch gate only.",
        "- It does not support heldout performance until completion verification and metric conversion finish.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default=None)
    parser.add_argument("--min-gpu-free-mib", default=24000, type=int)
    parser.add_argument("--ignore-gpu-memory", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m42 = read_json(M42_DIR / "coverage.json")
    batch_rows = read_jsonl(M41_DIR / "runtime_batch_rows.jsonl")
    selected = choose_batch(batch_rows, args.batch_id)
    batch_id = selected["batch_id"]
    scan_ids = list(selected["scan_ids"])
    session = selected["tmux_session"]
    scan_rows = scan_preflight(scan_ids)
    gpu = gpu_snapshot()
    expected_rows = [expected_for_scan(scan_id) for scan_id in scan_ids]
    command = docker_command(scan_ids, batch_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m43_conceptgraphs_heldout_runtime_{batch_id}.log"
    run_script = OUT_DIR / f"run_m43_{batch_id}.sh"
    status_path = OUT_DIR / f"background_status_{batch_id}.json"
    write_run_script(run_script, status_path, command, batch_id, scan_ids)
    write_text(OUT_DIR / f"docker_command_{batch_id}.txt", shlex.join(command) + "\n")
    write_jsonl(OUT_DIR / f"expected_outputs_{batch_id}.jsonl", expected_rows)
    write_jsonl(OUT_DIR / "selected_batch_scan_rows.jsonl", scan_rows)

    blockers: list[str] = []
    if m42.get("status") != "e005_m42_conceptgraphs_heldout_staging_materialized_ready":
        blockers.append("m42_staging_not_ready")
    if not image_ready():
        blockers.append("docker_image_missing")
    if not (GSA_CACHE / "sam_vit_h_4b8939.pth").exists():
        blockers.append("sam_checkpoint_missing")
    if not (GSA_CACHE / "groundingdino_swint_ogc.pth").exists():
        blockers.append("groundingdino_checkpoint_missing")
    for row in scan_rows:
        if not row["staged_payload_ready"]:
            blockers.append(f"staged_payload_missing:{row['scan_id']}")
    if tmux_running(session):
        blockers.append("tmux_session_already_running")
    if gpu.get("available") and gpu.get("memory_free_mib", 0) < args.min_gpu_free_mib and not args.ignore_gpu_memory:
        blockers.append(f"gpu_free_below_threshold:{gpu.get('memory_free_mib')}<{args.min_gpu_free_mib}")
    if not gpu.get("available") and not args.ignore_gpu_memory:
        blockers.append("gpu_status_unavailable")

    launch_executed = False
    launch_result: dict[str, Any] = {"cmd": [], "ok": False, "returncode": None, "stderr": "not_launched", "stdout": ""}
    if blockers:
        status = "e005_m43_conceptgraphs_heldout_runtime_batch_blocked_preflight"
    else:
        launch_cmd = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1"
        launch_result = run(["tmux", "new", "-d", "-s", session, launch_cmd], timeout=20)
        launch_executed = launch_result["ok"]
        status = (
            "e005_m43_conceptgraphs_heldout_runtime_batch_launched"
            if launch_result["ok"]
            else "e005_m43_conceptgraphs_heldout_runtime_batch_launch_failed"
        )

    coverage = {
        "background_status_path": str(status_path),
        "batch_id": batch_id,
        "blockers": blockers,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gpu_snapshot": gpu,
        "launch_executed": launch_executed,
        "launch_result": launch_result,
        "log_path": str(log_path),
        "m43_version": "e005_m43_conceptgraphs_heldout_runtime_batch_launch_v0",
        "min_gpu_free_mib": args.min_gpu_free_mib,
        "next_recommended_unit": (
            "E005-M44 ConceptGraphs heldout runtime batch completion verification"
            if launch_executed
            else "E005-M43 relaunch when GPU memory is available"
        ),
        "paper_table_claim_ready": False,
        "run_script": str(run_script),
        "scan_count": len(scan_ids),
        "scan_ids": scan_ids,
        "scan_rows": scan_rows,
        "status": status,
        "tmux_running_after_launch": tmux_running(session),
        "tmux_session": session,
        "verification_command": (
            "python experiments/E005_external_baseline_transition/tools/"
            f"verify_m43_conceptgraphs_heldout_runtime_batch.py --batch-id {batch_id}"
        ),
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
