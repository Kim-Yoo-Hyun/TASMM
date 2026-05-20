#!/usr/bin/env python3
"""Launch E005-M59 Open3DSG object-candidate export one-batch smoke."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
M58_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M59_object_candidate_export_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M59_object_candidate_export_smoke_v0"
LOG_DIR = ROOT / "logs"
IMAGE = "h001-open3dsg-repro:cu128"
SESSION = "e005_m59_open3dsg_object_export"


def run_cmd(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def image_ready() -> bool:
    result = run_cmd(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)
    return result.returncode == 0 and bool(result.stdout.strip())


def gpu_free_mib() -> int | None:
    result = run_cmd(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        timeout=20,
    )
    if result.returncode != 0:
        return None
    values = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            values.append(int(line))
        except ValueError:
            pass
    return max(values) if values else None


def tmux_session_exists() -> bool:
    result = run_cmd(["tmux", "has-session", "-t", SESSION], timeout=10)
    return result.returncode == 0


def copy_contract_files() -> None:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in [
        "object_candidate_schema.json",
        "query_candidate_schema.json",
        "export_hook_contract.json",
        "verification_contract.json",
    ]:
        src = M58_DATA_DIR / name
        if src.exists():
            shutil.copy2(src, LOCAL_DATA_DIR / name)


def build_docker_command() -> list[str]:
    source_container = "/workspace/local_dataset/Open3DSG_staged"
    out_container = "/out"
    tools_container = "/workspace/research2/tools"
    checkpoint = (
        f"{source_container}/training_repro/mlops/opensg/mlflow/"
        "363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/last.ckpt"
    )
    features = f"{source_container}/training_repro/output/features/clip_features_h001_official_blip_top5_scales3"
    runtime_base = f"{out_container}/open3dsg_runtime_base"
    python_command = " ".join(
        [
            "python",
            "open3dsg/scripts/run.py",
            "--test",
            "--dataset 3rscan",
            f"--checkpoint {checkpoint}",
            "--n_beams 5",
            "--weight_2d 0.5",
            "--clip_model OpenSeg",
            "--node_model ViT-L/14@336px",
            "--blip",
            "--avg_blip_emb",
            "--use_rgb",
            f"--load_features {features}",
            "--top_k_frames 5",
            "--scales 3",
            "--gpus 1",
            "--workers 0",
            "--quick_eval",
            "--run_name tmp_open3dsg_object_dump_smoke",
        ]
    )
    shell = (
        "mkdir -p "
        f"{runtime_base}/mlops/opensg/tensorboards "
        f"{runtime_base}/mlops/opensg/mlflow "
        f"{runtime_base}/classwise_eval && "
        f"cd {source_container}/h001_runtime/source/open3dsg_source && "
        f"python {tools_container}/m59_open3dsg_object_dump_runtime_patch.py "
        f"--source-root . -- {python_command}"
    )
    return [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "-v",
        f"{STAGED_ROOT}:{source_container}:ro",
        "-v",
        f"{LOCAL_DATA_DIR}:{out_container}",
        "-v",
        f"{EXP_ROOT / 'tools'}:{tools_container}:ro",
        "-e",
        f"OPEN3DSG_BASE={runtime_base}",
        "-e",
        f"OPEN3DSG_DATA={source_container}/training_repro/data",
        "-e",
        f"OPEN3DSG_DATA_OUT={source_container}/training_repro/output",
        "-e",
        "OPEN3DSG_HOME=/tmp",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_JSONL={out_container}/open3dsg_object_candidates.jsonl",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_COMPLETED_JSONL={out_container}/open3dsg_object_candidates.completed.jsonl",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_MANIFEST_JSON={out_container}/open3dsg_object_candidates.manifest.json",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_RESUME=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_TOPK=20",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_MAX_BATCHES=1",
        "-e",
        "OPEN3DSG_BASELINE_RUN_ID=open3dsg_h001_last_ckpt_object_candidate_smoke",
        "-e",
        f"OPEN3DSG_CHECKPOINT={checkpoint}",
        "-e",
        "OPEN3DSG_MODEL_SOURCE_STAGE=open3dsg_staged_read_only_runtime_patch",
        IMAGE,
        "bash",
        "-lc",
        shell,
    ]


def shell_quote(args: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(arg) for arg in args)


def launch_tmux(command: list[str], log_path: Path) -> subprocess.CompletedProcess[str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    shell = f"cd {ROOT} && {shell_quote(command)} > {log_path} 2>&1"
    return run_cmd(["tmux", "new", "-d", "-s", SESSION, shell], timeout=20)


def run(launch: bool, ignore_gpu_memory: bool, min_gpu_free_mib: int) -> dict[str, Any]:
    copy_contract_files()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e005_m59_open3dsg_object_export.log"
    command = build_docker_command()
    free_mib = gpu_free_mib()
    blockers = []
    if not image_ready():
        blockers.append(f"missing_image:{IMAGE}")
    if not STAGED_ROOT.exists():
        blockers.append(f"missing_staged_root:{STAGED_ROOT}")
    if tmux_session_exists():
        blockers.append(f"tmux_session_exists:{SESSION}")
    if free_mib is None:
        blockers.append("gpu_free_unknown")
    elif free_mib < min_gpu_free_mib and not ignore_gpu_memory:
        blockers.append(f"gpu_free_below_threshold:{free_mib}<{min_gpu_free_mib}")

    launch_executed = False
    launch_result = None
    if launch and not blockers:
        result = launch_tmux(command, log_path)
        launch_executed = result.returncode == 0
        launch_result = {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        if result.returncode != 0:
            blockers.append("tmux_launch_failed")

    status = "e005_m59_open3dsg_object_export_smoke_launched" if launch_executed else "e005_m59_open3dsg_object_export_smoke_not_launched"
    if blockers:
        status = "e005_m59_open3dsg_object_export_smoke_blocked_preflight"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "launch_requested": launch,
        "launch_executed": launch_executed,
        "session": SESSION,
        "log_path": str(log_path),
        "image": IMAGE,
        "gpu_free_mib": free_mib,
        "min_gpu_free_mib": min_gpu_free_mib,
        "ignore_gpu_memory": ignore_gpu_memory,
        "blockers": blockers,
        "local_output_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "source_mount_host": str(STAGED_ROOT),
        "source_mount_mode": "read_only",
        "source_modified": False,
        "command": command,
        "launch_result": launch_result,
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m59_open3dsg_object_export_smoke.py",
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(LOCAL_DATA_DIR / "launch_contract.json", coverage)
    write_text(LOCAL_DATA_DIR / "run_m59_open3dsg_object_export_smoke.sh", "#!/usr/bin/env bash\nset -euo pipefail\n" + shell_quote(command) + "\n")
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--ignore-gpu-memory", action="store_true")
    parser.add_argument("--min-gpu-free-mib", type=int, default=12000)
    args = parser.parse_args()
    coverage = run(
        launch=args.launch,
        ignore_gpu_memory=args.ignore_gpu_memory,
        min_gpu_free_mib=args.min_gpu_free_mib,
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if not coverage["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
