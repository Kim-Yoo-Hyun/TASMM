#!/usr/bin/env python3
"""Launch the E005-M08 DualMap one-scan runtime smoke in tmux."""

from __future__ import annotations

import argparse
import errno
import getpass
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M08_dualmap_one_scan_runtime_smoke_v0"
M06_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M06_dualmap_bootstrap_launch_v0"
LOCAL_DATASET = REPO_ROOT / "local_dataset"
STAGED_ROOT = LOCAL_DATASET / "DualMap_staged" / "3rscan_scannet_exported"
STAGED_DATASET_PATH = STAGED_ROOT / "scannet"
STAGED_CONFIG = STAGED_ROOT / "config" / "dualmap_3rscan_scannet.yaml"
SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
STAGED_SCENE_DIR = STAGED_DATASET_PATH / "exported" / SCAN_ID
OUTPUT_PATH = LOCAL_DATASET / "DualMap_outputs" / SCAN_ID
HYDRA_RUN_DIR = LOCAL_DATASET / "DualMap_outputs" / "hydra" / "E005-M08" / SCAN_ID
RUNTIME_HOME = LOCAL_DATASET / "DualMap_runtime_home"
MODEL_CACHE = LOCAL_DATASET / "DualMap_model_cache"
MODEL_MOUNT = MODEL_CACHE / "model"
HF_HOME = MODEL_CACHE / "huggingface"
TORCH_HOME = MODEL_CACHE / "torch"
XDG_CACHE_HOME = MODEL_CACHE / "xdg"
ULTRALYTICS_CONFIG_DIR = MODEL_CACHE / "ultralytics"
YOLO_CONFIG_DIR = MODEL_CACHE / "yolo"
MPLCONFIGDIR = MODEL_CACHE / "matplotlib"
IMAGE_NAME = "research2/dualmap-smoke:latest"
TMUX_SESSION = "e005_m08_dualmap_runtime"
M08_VERSION = "e005_m08_dualmap_one_scan_runtime_smoke_v0"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(command: list[str], cwd: Path | None = None, input_text: str | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
    }


def tmux_has_session(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session])["ok"]


def read_sudo_password(*, env_name: str, use_stdin: bool) -> str | None:
    value = os.environ.get(env_name)
    if value:
        return value if value.endswith("\n") else value + "\n"
    if not use_stdin:
        return None
    if sys.stdin.isatty():
        value = getpass.getpass("")
    else:
        value = sys.stdin.readline()
    if not value:
        return None
    return value if value.endswith("\n") else value + "\n"


def write_fifo_once(path: Path, payload: str, timeout_s: float = 10.0) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as exc:
            last_error = str(exc)
            if exc.errno == errno.ENXIO:
                time.sleep(0.1)
                continue
            return {"ok": False, "error": last_error}
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
        return {"ok": True, "error": ""}
    return {"ok": False, "error": last_error or "fifo_writer_timeout"}


def count_files(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


def build_runtime_overrides() -> list[str]:
    return [
        "dataset_name=scannet",
        f"scene_id={SCAN_ID}",
        f"dataset_path={STAGED_DATASET_PATH}",
        f"dataset_conf_path={STAGED_CONFIG}",
        f"output_path={OUTPUT_PATH}",
        "use_rerun=false",
        "run_local_mapping_only=true",
        "save_local_map=true",
        "use_parallel=false",
        "stride=20",
        "hydra.job.chdir=false",
        f"hydra.run.dir={HYDRA_RUN_DIR}",
    ]


def build_container_command() -> str:
    python_cmd = [
        "/opt/conda/envs/dualmap/bin/python",
        "-m",
        "applications.runner_dataset",
        *build_runtime_overrides(),
    ]
    return shlex.join(python_cmd)


def build_docker_command() -> list[str]:
    uid = os.getuid()
    gid = os.getgid()
    return [
        "sudo",
        "-n",
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--network=host",
        "--user",
        f"{uid}:{gid}",
        "-e",
        f"HOME={RUNTIME_HOME}",
        "-e",
        f"HF_HOME={HF_HOME}",
        "-e",
        f"TORCH_HOME={TORCH_HOME}",
        "-e",
        f"XDG_CACHE_HOME={XDG_CACHE_HOME}",
        "-e",
        f"ULTRALYTICS_CONFIG_DIR={ULTRALYTICS_CONFIG_DIR}",
        "-e",
        f"YOLO_CONFIG_DIR={YOLO_CONFIG_DIR}",
        "-e",
        f"MPLCONFIGDIR={MPLCONFIGDIR}",
        "-v",
        f"{LOCAL_DATASET}:{LOCAL_DATASET}",
        "-v",
        f"{MODEL_MOUNT}:/workspace/DualMap/model",
        "-w",
        "/workspace/DualMap",
        IMAGE_NAME,
        "bash",
        "-lc",
        f"set -euo pipefail; {build_container_command()}",
    ]


def build_run_script(path: Path, status_path: Path) -> None:
    docker_command = shlex.join(build_docker_command())
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"SCAN_ID={shlex.quote(SCAN_ID)}",
        f"OUTPUT_PATH={shlex.quote(str(OUTPUT_PATH))}",
        f"IMAGE_NAME={shlex.quote(IMAGE_NAME)}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" SCAN_ID=\"$SCAN_ID\" OUTPUT_PATH=\"$OUTPUT_PATH\" IMAGE_NAME=\"$IMAGE_NAME\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'scan_id': os.environ['SCAN_ID'],",
        "    'output_path': os.environ['OUTPUT_PATH'],",
        "    'image_name': os.environ['IMAGE_NAME'],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running preflight \"E005-M08 DualMap one-scan runtime smoke started\" 0",
        f"mkdir -p {shlex.quote(str(OUTPUT_PATH))} {shlex.quote(str(HYDRA_RUN_DIR))} {shlex.quote(str(RUNTIME_HOME))} {shlex.quote(str(MODEL_MOUNT))} {shlex.quote(str(HF_HOME))} {shlex.quote(str(TORCH_HOME))} {shlex.quote(str(XDG_CACHE_HOME))} {shlex.quote(str(ULTRALYTICS_CONFIG_DIR))} {shlex.quote(str(YOLO_CONFIG_DIR))} {shlex.quote(str(MPLCONFIGDIR))}",
        "write_status running docker_auth \"Authenticating sudo for Docker runtime\" 0",
        "sudo -S -v",
        "sudo_rc=$?",
        "if [ \"$sudo_rc\" -ne 0 ]; then",
        "  write_status failed docker_auth \"sudo authentication failed\" \"$sudo_rc\"",
        "  exit \"$sudo_rc\"",
        "fi",
        "write_status running docker_runtime \"Running DualMap one-scan runtime smoke\" 0",
        docker_command,
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed docker_runtime \"DualMap one-scan runtime failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed runtime_completed \"DualMap one-scan runtime completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M08 DualMap One-Scan Runtime Smoke Launch",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- background job status: `{coverage['background_job_status']}`.",
        f"- launch executed: {str(coverage['launch_executed']).lower()}.",
        f"- Docker image: `{coverage['image_name']}`.",
        f"- smoke scan id: `{coverage['scan_id']}`.",
        f"- staged scene dir: `{coverage['staged_scene_dir']}`.",
        f"- output path: `{coverage['output_path']}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- run script: `{coverage['run_script']}`.",
        f"- status path: `{coverage['background_status_path']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        f"- sudo password recorded: {str(coverage['sudo_password_recorded']).lower()}.",
        "",
        "## Paper Claim Boundary",
        "",
        "- E005-M08 launch does not support a `DualMap` performance claim.",
        "- It only starts one-scan runtime smoke needed before runtime object `*.pkl` schema inspection and adapter design.",
        "- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
        "## Agent Inference",
        "",
        "- Do not monitor the job continuously.",
        "- Verify completion with the M08 verifier, output file counts, targeted log tail, and runtime output layout.",
        "- If runtime fails on model download or code/data mismatch, record the blocker before deciding repair or `ConceptGraphs` fallback.",
        "",
        "## User Decision Needed",
        "",
        "- None while the background job is running.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--sudo-password-env", default="E005_M08_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    sudo_password = read_sudo_password(
        env_name=args.sudo_password_env,
        use_stdin=args.sudo_password_stdin,
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e005_m08_dualmap_one_scan_runtime.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    status_path = args.out_dir / "background_status.json"
    run_script = args.out_dir / "run_m08_dualmap_one_scan_runtime.sh"
    build_run_script(run_script, status_path)

    image_probe = run(["sudo", "-S", "docker", "image", "inspect", IMAGE_NAME], input_text=sudo_password) if sudo_password else {"ok": False}
    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    staged_counts = {
        "color": count_files(STAGED_SCENE_DIR / "color", "*.jpg"),
        "depth": count_files(STAGED_SCENE_DIR / "depth", "*.png"),
        "pose": count_files(STAGED_SCENE_DIR / "pose", "*.txt"),
        "intrinsic_depth_exists": (STAGED_SCENE_DIR / "intrinsic" / "intrinsic_depth.txt").exists(),
        "config_exists": STAGED_CONFIG.exists(),
    }

    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    password_delivery = {"ok": False, "error": "not_attempted"}
    launch_command: list[str] = []
    fifo_path: Path | None = None

    if not tmux_path:
        status = "e005_m08_dualmap_runtime_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m08_dualmap_runtime_already_running"
        background_status = "running"
        password_delivery = {"ok": True, "error": ""}
    elif not image_probe.get("ok"):
        status = "e005_m08_dualmap_runtime_launch_failed"
        background_status = "failed"
        launch_stderr = "docker_image_not_ready"
    elif not STAGED_SCENE_DIR.exists() or min(staged_counts["color"], staged_counts["depth"], staged_counts["pose"]) == 0:
        status = "e005_m08_dualmap_runtime_launch_failed"
        background_status = "failed"
        launch_stderr = f"staged_scene_not_ready: {STAGED_SCENE_DIR}"
    elif not staged_counts["intrinsic_depth_exists"] or not staged_counts["config_exists"]:
        status = "e005_m08_dualmap_runtime_launch_failed"
        background_status = "failed"
        launch_stderr = "staged_config_or_intrinsic_missing"
    elif sudo_password is None:
        status = "e005_m08_dualmap_runtime_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e005_m08_sudo_{os.getpid()}_{timestamp}.fifo"
        os.mkfifo(fifo_path, 0o600)
        command_inner = (
            f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; "
            f"cd {shlex.quote(str(REPO_ROOT))}; "
            f"{shlex.quote(str(run_script))} < {shlex.quote(str(fifo_path))} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        launch_command = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            TMUX_SESSION,
            "bash",
            "-lc",
            command_inner,
        ]
        write_text(args.out_dir / "launch_command.txt", shlex.join(launch_command) + "\n")
        proc = subprocess.run(
            launch_command,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout
        launch_stderr = proc.stderr
        if proc.returncode == 0:
            password_delivery = write_fifo_once(fifo_path, sudo_password)
        else:
            password_delivery = {"ok": False, "error": "tmux_launch_failed"}
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and password_delivery["ok"] and after_running:
            status = "e005_m08_dualmap_runtime_job_launched"
            background_status = "running"
        elif proc.returncode == 0 and after_running:
            status = "e005_m08_dualmap_runtime_password_delivery_failed"
            background_status = "failed"
        elif proc.returncode == 0:
            status = "e005_m08_dualmap_runtime_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "e005_m08_dualmap_runtime_launch_failed"
            background_status = "failed"

    verification_command = (
        "python experiments/E005_external_baseline_transition/tools/verify_m08_dualmap_runtime_smoke.py"
    )
    coverage = {
        "background_job_status": background_status,
        "background_status_path": str(status_path),
        "container_command": build_container_command(),
        "docker_command": shlex.join(build_docker_command()),
        "hydra_run_dir": str(HYDRA_RUN_DIR),
        "image_name": IMAGE_NAME,
        "image_probe_ok": bool(image_probe.get("ok")),
        "launch_command": shlex.join(launch_command) if launch_command else "",
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": M08_VERSION,
        "log_path": str(log_path),
        "model_cache": str(MODEL_CACHE),
        "next_recommended_unit": "E005-M09 DualMap one-scan runtime completion verification",
        "output_path": str(OUTPUT_PATH),
        "password_delivery": password_delivery,
        "run_script": str(run_script),
        "scan_id": SCAN_ID,
        "staged_config": str(STAGED_CONFIG),
        "staged_counts": staged_counts,
        "staged_dataset_path": str(STAGED_DATASET_PATH),
        "staged_scene_dir": str(STAGED_SCENE_DIR),
        "status": status,
        "sudo_password_recorded": False,
        "tmux_session": TMUX_SESSION,
        "verification_command": verification_command,
    }
    decision = {
        "status": status,
        "background_job_status": background_status,
        "selected_route": "DualMap",
        "image_name": IMAGE_NAME,
        "runtime_launched": background_status in {"running", "needs_verification"},
        "external_baseline_comparison_ready": False,
        "next_recommended_unit": coverage["next_recommended_unit"],
        "needs_verification": background_status in {"running", "needs_verification"},
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "decision.json", decision)
    write_text(args.out_dir / "runtime_command.txt", coverage["docker_command"] + "\n")
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(decision | {"artifact_dir": str(args.out_dir)}, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
