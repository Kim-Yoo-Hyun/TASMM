#!/usr/bin/env python3
"""Launch the E003-M70 OpenMask3D Docker build preflight in tmux."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M66_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M66_openmask3d_model_smoke_v0"
DEFAULT_M67_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M67_openmask3d_checkpoint_env_route_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M70_openmask3d_docker_env_build_preflight_v0"
DOCKERFILE = EXPERIMENT_ROOT / "docker" / "openmask3d_smoke" / "Dockerfile"
DOCKER_CONTEXT = DOCKERFILE.parent
IMAGE_NAME = "research2/openmask3d-smoke:latest"
LAUNCH_VERSION = "e003_m70_openmask3d_docker_build_preflight_launch_v0"
TMUX_SESSION = "e003_m70_openmask3d_docker_build"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def build_run_script(path: Path, status_path: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"cd {shlex.quote(str(REPO_ROOT))}",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"IMAGE_NAME={shlex.quote(IMAGE_NAME)}",
        f"DOCKERFILE={shlex.quote(str(DOCKERFILE))}",
        f"DOCKER_CONTEXT={shlex.quote(str(DOCKER_CONTEXT))}",
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
        "write_status running docker_build_start \"Docker build started\" 0",
        "printf 'a\\n' | sudo -S docker build --progress=plain -t \"$IMAGE_NAME\" -f \"$DOCKERFILE\" \"$DOCKER_CONTEXT\"",
        "build_rc=$?",
        "if [ \"$build_rc\" -ne 0 ]; then",
        "  write_status failed docker_build \"Docker build failed\" \"$build_rc\"",
        "  exit \"$build_rc\"",
        "fi",
        "image_id=$(printf 'a\\n' | sudo -S docker image inspect \"$IMAGE_NAME\" --format '{{.Id}}' 2>/dev/null || true)",
        "write_status docker_build_completed docker_build \"Docker image ready: ${image_id}\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M70 OpenMask3D Docker Build Preflight Launch",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- background job status: `{coverage['background_job_status']}`.",
            f"- launch executed: {coverage['launch_executed']}.",
            f"- image name: `{coverage['image_name']}`.",
            f"- Dockerfile: `{coverage['dockerfile']}`.",
            f"- Docker context: `{coverage['docker_context']}`.",
            f"- log path: `{coverage['log_path']}`.",
            f"- run script: `{coverage['run_script']}`.",
            f"- status path: `{coverage['background_status_path']}`.",
            f"- verification command: `{coverage['verification_command']}`.",
            f"- checkpoints ready before launch: {coverage['checkpoints_ready_before_launch']}.",
            f"- stage ready before launch: {coverage['stage_ready_before_launch']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M70 launch does not create an `OpenMask3D` proposal-quality claim.",
            "- It only launches the Docker environment build preflight required before model execution can be evaluated.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not monitor the build continuously.",
            "- Verify completion with image inspection, background status, and a targeted log tail.",
            "- If the build fails on old `torch` / CUDA / `MinkowskiEngine`, use the recorded fallback route instead of unbounded environment repair.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the background build is running.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m66-dir", default=DEFAULT_M66_DIR, type=Path)
    parser.add_argument("--m67-dir", default=DEFAULT_M67_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m66_dir = args.m66_dir.resolve()
    args.m67_dir = args.m67_dir.resolve()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    stage_coverage = load_json(args.m66_dir / "stage" / "coverage.json")
    checkpoint_coverage = load_json(args.m67_dir / "checkpoint_verification.json")
    status_path = args.out_dir / "background_status.json"
    run_script = args.out_dir / "run_m70_openmask3d_docker_build.sh"
    build_run_script(run_script, status_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e003_m70_openmask3d_docker_build.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    launch_command: list[str] = []

    checkpoints_ready = bool(checkpoint_coverage.get("checkpoints_ready"))
    stage_ready = bool(stage_coverage.get("stage_ready"))
    if not tmux_path:
        status = "openmask3d_docker_build_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "openmask3d_docker_build_already_running"
        background_status = "running"
    elif not DOCKERFILE.exists():
        status = "openmask3d_docker_build_launch_failed"
        background_status = "failed"
        launch_stderr = f"dockerfile_missing: {DOCKERFILE}"
    elif not checkpoints_ready:
        status = "openmask3d_docker_build_launch_blocked"
        background_status = "blocked"
        launch_stderr = "checkpoints_not_ready"
    elif not stage_ready:
        status = "openmask3d_docker_build_launch_blocked"
        background_status = "blocked"
        launch_stderr = "stage_not_ready"
    else:
        command_inner = (
            f"cd {shlex.quote(str(REPO_ROOT))} && "
            f"bash {shlex.quote(str(run_script))} "
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
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout
        launch_stderr = proc.stderr
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and after_running:
            status = "openmask3d_docker_build_job_launched"
            background_status = "running"
        elif proc.returncode == 0:
            status = "openmask3d_docker_build_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "openmask3d_docker_build_launch_failed"
            background_status = "failed"

    verification_command = (
        "python experiments/E003_perception_noise_expansion/tools/verify_m70_openmask3d_docker_build.py "
        f"--out-dir {args.out_dir}"
    )
    coverage = {
        "background_job_status": background_status,
        "background_status_path": str(status_path),
        "checkpoint_verification": str(args.m67_dir / "checkpoint_verification.json"),
        "checkpoints_ready_before_launch": checkpoints_ready,
        "docker_context": str(DOCKER_CONTEXT),
        "dockerfile": str(DOCKERFILE),
        "fallback_route": "direct_bridge_denominator_expansion_if_docker_env_blocks",
        "image_name": IMAGE_NAME,
        "launch_command": shlex.join(launch_command) if launch_command else "",
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": LAUNCH_VERSION,
        "log_path": str(log_path),
        "next_recommended_unit": "E003-M71 OpenMask3D Docker build completion verification",
        "run_script": str(run_script),
        "stage_coverage": str(args.m66_dir / "stage" / "coverage.json"),
        "stage_ready_before_launch": stage_ready,
        "status": status,
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "verification_command": verification_command,
        "working_directory": str(REPO_ROOT),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
