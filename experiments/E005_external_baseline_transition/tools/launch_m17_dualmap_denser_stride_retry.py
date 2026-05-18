#!/usr/bin/env python3
"""Launch the E005-M17 DualMap denser-stride object-output retry in tmux."""

from __future__ import annotations

import argparse
import errno
import getpass
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M17_dualmap_denser_stride_retry_v0"
M16_PLAN = (
    EXPERIMENT_ROOT
    / "artifacts"
    / "E005-M16_dualmap_object_output_diagnosis_v0"
    / "denser_stride_retry_command_plan.json"
)
LOCAL_DATASET = REPO_ROOT / "local_dataset"
MODEL_CACHE = LOCAL_DATASET / "DualMap_model_cache"
MODEL_MOUNT = MODEL_CACHE / "model"
TMUX_SESSION = "e005_m17_dualmap_denser_stride_retry"
M17_VERSION = "e005_m17_dualmap_denser_stride_retry_v0"


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
            plan.get("image_name", "research2/dualmap-smoke:latest"),
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
        f"SCAN_ID={shlex.quote(str(plan['scan_id']))}",
        f"OUTPUT_PATH={shlex.quote(str(plan['output_path']))}",
        f"IMAGE_NAME={shlex.quote(str(plan.get('image_name', 'research2/dualmap-smoke:latest')))}",
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
        "write_status running docker_runtime \"Running DualMap denser-stride object retry\" 0",
        docker_command,
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed docker_runtime \"DualMap denser-stride object retry failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed runtime_completed \"DualMap denser-stride object retry completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--sudo-password-env", default="E005_M17_SUDO_PASSWORD")
    parser.add_argument("--sudo-password-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    plan = read_json(M16_PLAN)
    if not plan:
        raise SystemExit(f"Missing command plan: {M16_PLAN}")
    if tmux_has_session(TMUX_SESSION):
        raise SystemExit(f"tmux session already running: {TMUX_SESSION}")
    ensure_runtime_dirs(plan)
    logs_dir = REPO_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"{stamp}_e005_m17_dualmap_denser_stride_retry.log"
    status_path = args.out_dir / "background_status.json"
    run_script = args.out_dir / "run_m17_dualmap_denser_stride_retry.sh"
    build_run_script(run_script, status_path, plan)
    password = read_sudo_password(env_name=args.sudo_password_env, use_stdin=args.sudo_password_stdin)
    if password is None:
        raise SystemExit("sudo password required via env or stdin")
    fifo_path = Path(f"/tmp/e005_m17_sudo_{os.getpid()}_{stamp}.fifo")
    if fifo_path.exists():
        fifo_path.unlink()
    os.mkfifo(fifo_path, 0o600)
    launch_command = [
        "tmux",
        "new-session",
        "-d",
        "-s",
        TMUX_SESSION,
        "bash",
        "-lc",
        f"trap 'rm -f {shlex.quote(str(fifo_path))}' EXIT; cd {shlex.quote(str(REPO_ROOT))}; {shlex.quote(str(run_script))} < {shlex.quote(str(fifo_path))} > {shlex.quote(str(log_path))} 2>&1",
    ]
    launch = run(launch_command)
    password_delivery = {"ok": False, "error": "launch_failed"}
    if launch["ok"]:
        password_delivery = write_fifo_once(fifo_path, password)
    coverage = {
        "status": "e005_m17_dualmap_denser_stride_retry_job_launched" if launch["ok"] and password_delivery["ok"] else "e005_m17_dualmap_denser_stride_retry_launch_failed",
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": M17_VERSION,
        "tmux_session": TMUX_SESSION,
        "background_job_status": "running" if tmux_has_session(TMUX_SESSION) else "not_running",
        "background_status_path": str(status_path),
        "log_path": str(log_path),
        "output_path": plan["output_path"],
        "hydra_run_dir": plan["hydra_run_dir"],
        "scan_id": plan["scan_id"],
        "image_name": plan.get("image_name", "research2/dualmap-smoke:latest"),
        "container_command": build_container_command(plan),
        "docker_command": shlex.join(build_docker_command(plan)),
        "run_script": str(run_script),
        "launch_command": shlex.join(launch_command),
        "launch_executed": launch["ok"],
        "launch_returncode": launch["returncode"],
        "launch_stdout": launch["stdout"],
        "launch_stderr": launch["stderr"],
        "password_delivery": password_delivery,
        "sudo_password_recorded": False,
        "gpu_before_launch": gpu_snapshot(),
        "configuration_delta_from_m14": plan.get("configuration_delta_from_m14", {}),
        "expected_outputs": plan.get("expected_outputs", []),
        "output_counts_at_launch": {
            "pkl": count_files(Path(plan["output_path"]), "*/map/*.pkl"),
            "layout_pcd": count_files(Path(plan["output_path"]), "*/map/layout.pcd"),
            "system_time": count_files(Path(plan["output_path"]), "*/system_time.csv"),
            "detector_time": count_files(Path(plan["output_path"]), "*/detector_time.csv"),
        },
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m17_dualmap_denser_stride_retry.py",
        "next_recommended_unit": "E005-M18 DualMap denser-stride retry completion verification",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "runtime_command.txt", shlex.join(build_docker_command(plan)) + "\n")
    write_text(args.out_dir / "launch_command.txt", shlex.join(launch_command) + "\n")
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"].endswith("_job_launched") else 1


if __name__ == "__main__":
    raise SystemExit(main())
