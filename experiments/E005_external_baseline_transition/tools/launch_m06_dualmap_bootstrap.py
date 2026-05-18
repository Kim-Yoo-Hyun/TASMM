#!/usr/bin/env python3
"""Launch the E005-M06 DualMap submodule and Docker bootstrap in tmux."""

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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M06_dualmap_bootstrap_launch_v0"
DUALMAP_REPO = REPO_ROOT / "local_dataset" / "external_repos" / "DualMap"
DOCKERFILE = EXPERIMENT_ROOT / "docker" / "dualmap_smoke" / "Dockerfile"
DOCKER_CONTEXT = DOCKERFILE.parent
IMAGE_NAME = "research2/dualmap-smoke:latest"
EXPECTED_COMMIT = "157235ec49e6a1f439babbc571c4c02ad1f06aa9"
M06_VERSION = "e005_m06_dualmap_bootstrap_launch_v0"
TMUX_SESSION = "e005_m06_dualmap_bootstrap"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
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
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


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


def build_run_script(path: Path, status_path: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"REPO_ROOT={shlex.quote(str(REPO_ROOT))}",
        f"DUALMAP_REPO={shlex.quote(str(DUALMAP_REPO))}",
        f"DOCKERFILE={shlex.quote(str(DOCKERFILE))}",
        f"DOCKER_CONTEXT={shlex.quote(str(DOCKER_CONTEXT))}",
        f"IMAGE_NAME={shlex.quote(IMAGE_NAME)}",
        f"EXPECTED_COMMIT={shlex.quote(EXPECTED_COMMIT)}",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        "KEEPALIVE_PID=\"\"",
        "cleanup() {",
        "  if [ -n \"$KEEPALIVE_PID\" ]; then kill \"$KEEPALIVE_PID\" >/dev/null 2>&1 || true; fi",
        "}",
        "trap cleanup EXIT",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" IMAGE_NAME=\"$IMAGE_NAME\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'image_name': os.environ['IMAGE_NAME'],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running preflight \"E005-M06 bootstrap started\" 0",
        "cd \"$DUALMAP_REPO\" || { write_status failed repo_missing \"DualMap repo not found\" 2; exit 2; }",
        "head_commit=$(git rev-parse HEAD)",
        "if [ \"$head_commit\" != \"$EXPECTED_COMMIT\" ]; then",
        "  write_status failed repo_commit_mismatch \"DualMap repo commit mismatch: ${head_commit}\" 3",
        "  exit 3",
        "fi",
        "write_status running submodule_update \"Updating local mobileclip submodule\" 0",
        "git submodule set-url 3rdparty/mobileclip https://github.com/apple/ml-mobileclip.git",
        "git submodule sync --recursive",
        "git submodule update --init --recursive",
        "submodule_rc=$?",
        "if [ \"$submodule_rc\" -ne 0 ]; then",
        "  write_status failed submodule_update \"mobileclip submodule update failed\" \"$submodule_rc\"",
        "  exit \"$submodule_rc\"",
        "fi",
        "test -f 3rdparty/mobileclip/setup.py || { write_status failed submodule_missing \"mobileclip setup.py missing\" 4; exit 4; }",
        "write_status running docker_auth \"Authenticating sudo for Docker build\" 0",
        "sudo -S -v",
        "sudo_rc=$?",
        "if [ \"$sudo_rc\" -ne 0 ]; then",
        "  write_status failed docker_auth \"sudo authentication failed\" \"$sudo_rc\"",
        "  exit \"$sudo_rc\"",
        "fi",
        "(while true; do sudo -n true >/dev/null 2>&1 || exit 0; sleep 60; done) &",
        "KEEPALIVE_PID=$!",
        "cd \"$REPO_ROOT\"",
        "write_status running docker_build \"Building DualMap Docker smoke image\" 0",
        "sudo -n docker build --progress=plain --build-arg DUALMAP_COMMIT=\"$EXPECTED_COMMIT\" -t \"$IMAGE_NAME\" -f \"$DOCKERFILE\" \"$DOCKER_CONTEXT\"",
        "build_rc=$?",
        "if [ \"$build_rc\" -ne 0 ]; then",
        "  write_status failed docker_build \"DualMap Docker build failed\" \"$build_rc\"",
        "  exit \"$build_rc\"",
        "fi",
        "write_status running docker_import_smoke \"Running DualMap dependency import smoke\" 0",
        "sudo -n docker run --rm --gpus all \"$IMAGE_NAME\" bash -lc \"micromamba run -n dualmap python - <<'PY'",
        "import importlib",
        "mods = ['hydra','omegaconf','torch','cv2','imageio','numpy','open3d','open_clip','ultralytics','rerun','faiss','kornia','natsort','scipy','tyro','supervision']",
        "for mod in mods:",
        "    importlib.import_module(mod)",
        "print('dualmap_import_smoke_ok')",
        "PY\"",
        "smoke_rc=$?",
        "if [ \"$smoke_rc\" -ne 0 ]; then",
        "  write_status failed docker_import_smoke \"DualMap Docker import smoke failed\" \"$smoke_rc\"",
        "  exit \"$smoke_rc\"",
        "fi",
        "image_id=$(sudo -n docker image inspect \"$IMAGE_NAME\" --format '{{.Id}}' 2>/dev/null || true)",
        "write_status completed bootstrap_ready \"DualMap bootstrap ready: ${image_id}\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M06 DualMap Bootstrap Launch",
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
        f"- repo path: `{coverage['dualmap_repo']}`.",
        f"- Docker image: `{coverage['image_name']}`.",
        f"- Dockerfile: `{coverage['dockerfile']}`.",
        f"- Docker context: `{coverage['docker_context']}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- run script: `{coverage['run_script']}`.",
        f"- status path: `{coverage['background_status_path']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        f"- sudo password recorded: {str(coverage['sudo_password_recorded']).lower()}.",
        "",
        "## Paper Claim Boundary",
        "",
        "- E005-M06 launch does not support a `DualMap` performance claim.",
        "- It only launches the environment/bootstrap job required before one-scan runtime smoke and runtime `*.pkl` schema inspection.",
        "- External baseline comparison, final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
        "## Agent Inference",
        "",
        "- Do not monitor the job continuously.",
        "- Verify completion with the M06 verifier, image inspection, submodule layout, and targeted log tail.",
        "- If Docker build fails on dependency resolution, decide whether to repair `DualMap` image or switch to the `ConceptGraphs` backup route.",
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
    parser.add_argument("--sudo-password-env", default="E005_M06_SUDO_PASSWORD")
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
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e005_m06_dualmap_bootstrap.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    status_path = args.out_dir / "background_status.json"
    run_script = args.out_dir / "run_m06_dualmap_bootstrap.sh"
    build_run_script(run_script, status_path)

    repo_probe = run(["git", "rev-parse", "HEAD"], cwd=DUALMAP_REPO) if DUALMAP_REPO.exists() else {}
    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    password_delivery = {"ok": False, "error": "not_attempted"}
    launch_command: list[str] = []
    fifo_path: Path | None = None

    if not tmux_path:
        status = "e005_m06_dualmap_bootstrap_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m06_dualmap_bootstrap_already_running"
        background_status = "running"
        password_delivery = {"ok": True, "error": ""}
    elif not DUALMAP_REPO.exists():
        status = "e005_m06_dualmap_bootstrap_launch_failed"
        background_status = "failed"
        launch_stderr = f"dualmap_repo_missing: {DUALMAP_REPO}"
    elif repo_probe.get("stdout") != EXPECTED_COMMIT:
        status = "e005_m06_dualmap_bootstrap_launch_failed"
        background_status = "failed"
        launch_stderr = f"dualmap_repo_commit_mismatch: {repo_probe.get('stdout')}"
    elif not DOCKERFILE.exists():
        status = "e005_m06_dualmap_bootstrap_launch_failed"
        background_status = "failed"
        launch_stderr = f"dockerfile_missing: {DOCKERFILE}"
    elif sudo_password is None:
        status = "e005_m06_dualmap_bootstrap_launch_failed"
        background_status = "failed"
        launch_stderr = "sudo_password_missing"
    else:
        fifo_path = Path("/tmp") / f"e005_m06_sudo_{os.getpid()}_{timestamp}.fifo"
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
            status = "e005_m06_dualmap_bootstrap_job_launched"
            background_status = "running"
        elif proc.returncode == 0 and after_running:
            status = "e005_m06_dualmap_bootstrap_password_delivery_failed"
            background_status = "failed"
        elif proc.returncode == 0:
            status = "e005_m06_dualmap_bootstrap_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "e005_m06_dualmap_bootstrap_launch_failed"
            background_status = "failed"

    verification_command = (
        "printf '<sudo-password>\\n' | "
        "python experiments/E005_external_baseline_transition/tools/verify_m06_dualmap_bootstrap.py "
        "--sudo-password-stdin"
    )
    coverage = {
        "background_job_status": background_status,
        "background_status_path": str(status_path),
        "docker_context": str(DOCKER_CONTEXT),
        "dockerfile": str(DOCKERFILE),
        "dualmap_repo": str(DUALMAP_REPO),
        "expected_commit": EXPECTED_COMMIT,
        "image_name": IMAGE_NAME,
        "launch_command": shlex.join(launch_command) if launch_command else "",
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": M06_VERSION,
        "log_path": str(log_path),
        "next_recommended_unit": "E005-M07 DualMap bootstrap completion verification",
        "password_delivery": password_delivery,
        "run_script": str(run_script),
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
        "runtime_launched": False,
        "external_baseline_comparison_ready": False,
        "next_recommended_unit": coverage["next_recommended_unit"],
        "needs_verification": background_status in {"running", "needs_verification"},
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "decision.json", decision)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(decision | {"artifact_dir": str(args.out_dir)}, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
