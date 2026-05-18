#!/usr/bin/env python3
"""Launch the E005-M14 DualMap cache-fixed detector retry in tmux."""

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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M14_dualmap_cache_fixed_detector_retry_v0"
M13_PLAN = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M13_dualmap_cache_permission_repair_plan_v0"
    / "cache_fixed_detector_retry_command_plan.json"
)
LOCAL_DATASET = REPO_ROOT / "local_dataset"
MODEL_CACHE = LOCAL_DATASET / "DualMap_model_cache"
MODEL_MOUNT = MODEL_CACHE / "model"
STAGED_ROOT = LOCAL_DATASET / "DualMap_staged" / "3rscan_scannet_exported"
STAGED_DATASET_PATH = STAGED_ROOT / "scannet"
STAGED_CONFIG = STAGED_ROOT / "config" / "dualmap_3rscan_scannet.yaml"
SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
STAGED_SCENE_DIR = STAGED_DATASET_PATH / "exported" / SCAN_ID
IMAGE_NAME = "research2/dualmap-smoke:latest"
TMUX_SESSION = "e005_m14_dualmap_cache_retry"
M14_VERSION = "e005_m14_dualmap_cache_fixed_detector_retry_v0"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(command: list[str], input_text: str | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
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


def gpu_snapshot() -> dict[str, Any]:
    query = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ]
    )
    return {"gpu_query": query}


def build_container_command(plan: dict[str, Any]) -> str:
    return shlex.join([str(part) for part in plan.get("container_command", [])])


def build_docker_command(plan: dict[str, Any]) -> list[str]:
    uid = os.getuid()
    gid = os.getgid()
    command = [
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
    ]
    for key, value in sorted(plan.get("required_env", {}).items()):
        command.extend(["-e", f"{key}={value}"])
    command.extend(["-v", f"{LOCAL_DATASET}:{LOCAL_DATASET}"])
    command.extend(["-v", f"{MODEL_MOUNT}:/workspace/DualMap/model"])
    for mount in plan.get("extra_mounts", []):
        Path(mount["host"]).mkdir(parents=True, exist_ok=True)
        command.extend(["-v", f"{mount['host']}:{mount['container']}"])
    command.extend(
        [
            "-w",
            "/workspace/DualMap",
            plan.get("image_name", IMAGE_NAME),
            "bash",
            "-lc",
            f"set -euo pipefail; {build_container_command(plan)}",
        ]
    )
    return command


def ensure_runtime_dirs(plan: dict[str, Any]) -> None:
    MODEL_MOUNT.mkdir(parents=True, exist_ok=True)
    for value in plan.get("required_env", {}).values():
        if str(value).startswith(str(LOCAL_DATASET)):
            Path(value).mkdir(parents=True, exist_ok=True)
    for mount in plan.get("extra_mounts", []):
        Path(mount["host"]).mkdir(parents=True, exist_ok=True)
    Path(plan["output_path"]).mkdir(parents=True, exist_ok=True)
    Path(plan["hydra_run_dir"]).mkdir(parents=True, exist_ok=True)


def build_run_script(path: Path, status_path: Path, plan: dict[str, Any]) -> None:
    docker_command = shlex.join(build_docker_command(plan))
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"SCAN_ID={shlex.quote(SCAN_ID)}",
        f"OUTPUT_PATH={shlex.quote(plan['output_path'])}",
        f"IMAGE_NAME={shlex.quote(plan.get('image_name', IMAGE_NAME))}",
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
        "write_status running docker_auth \"Authenticating sudo for Docker runtime\" 0",
        "sudo -S -v",
        "sudo_rc=$?",
        "if [ \"$sudo_rc\" -ne 0 ]; then",
        "  write_status failed docker_auth \"sudo authentication failed\" \"$sudo_rc\"",
        "  exit \"$sudo_rc\"",
        "fi",
        "write_status running docker_runtime \"Running DualMap cache-fixed detector retry\" 0",
        docker_command,
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed docker_runtime \"DualMap cache-fixed detector retry failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed runtime_completed \"DualMap cache-fixed detector retry completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--sudo-password-env", default="E005_M14_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plan = read_json(M13_PLAN)
    sudo_password = read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e005_m14_dualmap_cache_fixed_retry.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    status_path = args.out_dir / "background_status.json"
    run_script = args.out_dir / "run_m14_dualmap_cache_fixed_retry.sh"
    if plan:
        ensure_runtime_dirs(plan)
        build_run_script(run_script, status_path, plan)

    image_probe = run(["sudo", "-S", "docker", "image", "inspect", plan.get("image_name", IMAGE_NAME)], input_text=sudo_password) if sudo_password and plan else {"ok": False}
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

    if not plan:
        status = "e005_m14_dualmap_cache_fixed_retry_launch_failed"
        background_status = "failed"
        launch_stderr = f"missing_m13_command_plan: {M13_PLAN}"
    elif not tmux_path:
        status = "e005_m14_dualmap_cache_fixed_retry_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m14_dualmap_cache_fixed_retry_already_running"
        background_status = "running"
        password_delivery = {"ok": True, "error": ""}
    elif not image_probe.get("ok"):
        status = "e005_m14_dualmap_cache_fixed_retry_launch_failed"
        background_status = "failed"
        launch_stderr = "docker_image_not_ready_or_sudo_auth_failed"
    elif sudo_password is None:
        status = "e005_m14_dualmap_cache_fixed_retry_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e005_m14_sudo_{os.getpid()}_{timestamp}.fifo"
        os.mkfifo(fifo_path, 0o600)
        command_inner = (
            f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; "
            f"cd {shlex.quote(str(REPO_ROOT))}; "
            f"{shlex.quote(str(run_script))} < {shlex.quote(str(fifo_path))} "
            f"> {shlex.quote(str(log_path))} 2>&1"
        )
        launch_command = ["tmux", "new-session", "-d", "-s", TMUX_SESSION, "bash", "-lc", command_inner]
        write_text(args.out_dir / "launch_command.txt", shlex.join(launch_command) + "\n")
        proc = subprocess.run(launch_command, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout
        launch_stderr = proc.stderr
        password_delivery = write_fifo_once(fifo_path, sudo_password) if proc.returncode == 0 else {"ok": False, "error": "tmux_launch_failed"}
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and password_delivery["ok"] and after_running:
            status = "e005_m14_dualmap_cache_fixed_retry_job_launched"
            background_status = "running"
        elif proc.returncode == 0:
            status = "e005_m14_dualmap_cache_fixed_retry_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "e005_m14_dualmap_cache_fixed_retry_launch_failed"
            background_status = "failed"

    verification_command = "python experiments/E005_external_baseline_transition/tools/verify_m14_dualmap_cache_fixed_retry.py"
    coverage = {
        "background_job_status": background_status,
        "background_status_path": str(status_path),
        "container_command": build_container_command(plan) if plan else "",
        "docker_command": shlex.join(build_docker_command(plan)) if plan else "",
        "expected_outputs": plan.get("expected_outputs", []) if plan else [],
        "extra_mounts": plan.get("extra_mounts", []) if plan else [],
        "gpu_before_launch": gpu_snapshot(),
        "hydra_run_dir": plan.get("hydra_run_dir", "") if plan else "",
        "image_name": plan.get("image_name", IMAGE_NAME) if plan else IMAGE_NAME,
        "image_probe_ok": bool(image_probe.get("ok")),
        "launch_command": shlex.join(launch_command) if launch_command else "",
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": M14_VERSION,
        "log_path": str(log_path),
        "next_recommended_unit": "E005-M15 DualMap cache-fixed detector retry completion verification",
        "output_path": plan.get("output_path", "") if plan else "",
        "password_delivery": password_delivery,
        "run_script": str(run_script),
        "scan_id": SCAN_ID,
        "staged_counts": staged_counts,
        "status": status,
        "sudo_password_recorded": False,
        "tmux_session": TMUX_SESSION,
        "verification_command": verification_command,
    }
    decision = {
        "status": status,
        "background_job_status": background_status,
        "runtime_launched": background_status in {"running", "needs_verification"},
        "external_baseline_comparison_ready": False,
        "next_recommended_unit": coverage["next_recommended_unit"],
        "needs_verification": background_status in {"running", "needs_verification"},
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "decision.json", decision)
    write_text(args.out_dir / "runtime_command.txt", coverage["docker_command"] + "\n")
    print(json.dumps(decision | {"artifact_dir": str(args.out_dir)}, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
