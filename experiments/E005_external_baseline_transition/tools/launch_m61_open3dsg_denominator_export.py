#!/usr/bin/env python3
"""Launch E005-M61 denominator-aligned Open3DSG object-candidate export."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
STAGED_ROOT = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
M58_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0"
M61_PLAN_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M61_denominator_aligned_export_plan_v0"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M61_denominator_aligned_export_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M61_denominator_aligned_export_v0"
LOG_DIR = ROOT / "logs"
IMAGE = "h001-open3dsg-repro:cu128"
SESSION = "e005_m61_open3dsg_denominator_export"
TARGET_RUNTIME_JSONL = LOCAL_DATA_DIR / "target_relationships_runtime.jsonl"


def run_cmd(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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
    values: list[int] = []
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
    return run_cmd(["tmux", "has-session", "-t", SESSION], timeout=10).returncode == 0


def shell_quote(args: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(arg) for arg in args)


def normalize_targets() -> list[dict[str, Any]]:
    plan_targets = read_jsonl(M61_PLAN_DIR / "target_relationship_rows.jsonl")
    rows: list[dict[str, Any]] = []
    for row in plan_targets:
        rows.append(
            {
                "scan": str(row["scan_id"]),
                "split": int(row["subset_split_id"]),
                "source_split": row.get("source_split"),
                "raw_scan_id": row.get("raw_scan_id"),
            }
        )
    rows.sort(key=lambda row: (str(row["scan"]), int(row["split"])))
    return rows


def prepare_output() -> dict[str, Any]:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for name in [
        "object_candidate_schema.json",
        "query_candidate_schema.json",
        "export_hook_contract.json",
        "verification_contract.json",
    ]:
        src = M58_DATA_DIR / name
        if src.exists():
            shutil.copy2(src, LOCAL_DATA_DIR / name)
    targets = normalize_targets()
    write_jsonl(TARGET_RUNTIME_JSONL, targets)
    plan_coverage = read_json(M61_PLAN_DIR / "coverage.json")
    return {
        "target_relationship_rows": len(targets),
        "target_scan_count": len({row["scan"] for row in targets}),
        "target_runtime_jsonl": str(TARGET_RUNTIME_JSONL),
        "plan_status": plan_coverage.get("status"),
        "plan_query_rows": plan_coverage.get("query_rows"),
        "plan_query_scan_count": plan_coverage.get("query_scan_count"),
    }


def build_docker_command(max_batches: int) -> list[str]:
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
            "--run_name tmp_open3dsg_m61_denominator_export",
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
        f"OPEN3DSG_OBJECT_DUMP_TARGET_RELATIONSHIPS_JSONL={out_container}/target_relationships_runtime.jsonl",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_STREAM_BATCHES=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_RESUME=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_TOPK=20",
        "-e",
        f"OPEN3DSG_OBJECT_DUMP_MAX_BATCHES={max_batches}",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_SKIP_BLIP_LOAD=1",
        "-e",
        "OPEN3DSG_OBJECT_DUMP_OBJECT_ONLY=1",
        "-e",
        "OPEN3DSG_BASELINE_RUN_ID=open3dsg_h001_last_ckpt_denominator_aligned",
        "-e",
        f"OPEN3DSG_CHECKPOINT={checkpoint}",
        "-e",
        "OPEN3DSG_MODEL_SOURCE_STAGE=open3dsg_staged_read_only_targeted_runtime_patch",
        IMAGE,
        "bash",
        "-lc",
        shell,
    ]


def launch_tmux(command: list[str], log_path: Path) -> subprocess.CompletedProcess[str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    shell = f"cd {ROOT} && {shell_quote(command)} > {log_path} 2>&1"
    return run_cmd(["tmux", "new", "-d", "-s", SESSION, shell], timeout=20)


def run(launch: bool, ignore_gpu_memory: bool, min_gpu_free_mib: int) -> dict[str, Any]:
    prep = prepare_output()
    max_batches = int(prep["target_relationship_rows"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e005_m61_open3dsg_denominator_export.log"
    command = build_docker_command(max_batches=max_batches)
    free_mib = gpu_free_mib()
    blockers: list[str] = []
    if not image_ready():
        blockers.append(f"missing_image:{IMAGE}")
    if not STAGED_ROOT.exists():
        blockers.append(f"missing_staged_root:{STAGED_ROOT}")
    if prep["target_relationship_rows"] <= 0:
        blockers.append("missing_target_relationship_rows")
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

    status = "e005_m61_open3dsg_denominator_export_launched" if launch_executed else "e005_m61_open3dsg_denominator_export_not_launched"
    if blockers:
        status = "e005_m61_open3dsg_denominator_export_blocked_preflight"
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
        "target_context": prep,
        "expected_completed_batches": max_batches,
        "command": command,
        "launch_result": launch_result,
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m61_open3dsg_denominator_export.py",
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(LOCAL_DATA_DIR / "launch_contract.json", coverage)
    write_text(LOCAL_DATA_DIR / "run_m61_open3dsg_denominator_export.sh", "#!/usr/bin/env bash\nset -euo pipefail\n" + shell_quote(command) + "\n")
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--ignore-gpu-memory", action="store_true")
    parser.add_argument("--min-gpu-free-mib", type=int, default=24000)
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
