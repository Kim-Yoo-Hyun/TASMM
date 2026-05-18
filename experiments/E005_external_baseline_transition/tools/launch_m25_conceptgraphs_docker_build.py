#!/usr/bin/env python3
"""Launch E005-M25 ConceptGraphs Docker build in a background tmux job."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M25_conceptgraphs_docker_build_preflight_v0"
DOCKER_DIR = EXPERIMENT_ROOT / "docker" / "conceptgraphs_smoke"
IMAGE = "research2/conceptgraphs-smoke:latest"
SESSION = "e005_m25_conceptgraphs_docker_build"
CONCEPTGRAPHS_COMMIT = "93277a02bd89171f8121e84203121cf7af9ebb5d"
GSA_COMMIT = "a4d76a2b55e348943cba4cd57d7553c354296223"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001 - launch diagnostics should record failures.
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def tmux_has_session(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session], timeout=10)["ok"]


def build_run_script(path: Path, status_path: Path, manifest_path: Path, docker_build_command: str) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"ROOT={shlex.quote(str(ROOT))}",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"MANIFEST_PATH={shlex.quote(str(manifest_path))}",
        f"IMAGE={shlex.quote(IMAGE)}",
        f"DOCKER_BUILD_COMMAND={shlex.quote(docker_build_command)}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "mkdir -p \"$(dirname \"$STATUS_PATH\")\"",
        "write_status running docker_build \"E005-M25 ConceptGraphs Docker build started\" 0",
        "cd \"$ROOT\"",
        "bash -lc \"$DOCKER_BUILD_COMMAND\"",
        "rc=$?",
        "if [ \"$rc\" -ne 0 ]; then",
        "  write_status failed docker_build \"Docker build failed\" \"$rc\"",
        "  exit \"$rc\"",
        "fi",
        "IMAGE_ID=$(docker image inspect \"$IMAGE\" --format '{{.Id}}' 2>/dev/null || true)",
        "IMAGE_SIZE=$(docker image inspect \"$IMAGE\" --format '{{.Size}}' 2>/dev/null || echo 0)",
        "STATUS_PATH=\"$STATUS_PATH\" MANIFEST_PATH=\"$MANIFEST_PATH\" IMAGE=\"$IMAGE\" IMAGE_ID=\"$IMAGE_ID\" IMAGE_SIZE=\"$IMAGE_SIZE\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': 'completed',",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "    'image': os.environ['IMAGE'],",
        "    'image_id': os.environ['IMAGE_ID'],",
        "    'image_size_bytes': int(os.environ.get('IMAGE_SIZE') or 0),",
        "}",
        "Path(os.environ['MANIFEST_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps({'status': 'completed', 'step': 'completed', 'message': 'E005-M25 Docker build completed', 'returncode': 0, 'updated_at': payload['updated_at']}, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "write_status completed completed \"E005-M25 Docker build completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M25 ConceptGraphs Docker Build Preflight",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- launch executed: {str(coverage['launch_executed']).lower()}.",
        f"- Docker image: `{coverage['docker_image']}`.",
        f"- Dockerfile: `{coverage['dockerfile']}`.",
        f"- build context: `{coverage['build_context']}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- working directory: `{coverage['working_directory']}`.",
        f"- status path: `{coverage['background_status_path']}`.",
        f"- manifest path: `{coverage['output_manifest_path']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        "",
        "## Claim Boundary",
        "",
        "- E005-M25 only launches and tracks the `ConceptGraphs` container build.",
        "- It does not support a `ConceptGraphs` runtime, object-map, or performance comparison claim.",
        "- The smoke image follows the official Python 3.10 / PyTorch 2.0.1 / CUDA 11.8 setup; RTX 5090 runtime compatibility remains a separate verification risk.",
        "",
        "## Compatibility Notes",
        "",
        "- The Dockerfile applies a headless `matplotlib` backend patch.",
        "- The Dockerfile adds a minimal `ram` import alias for the pinned `Grounded-Segment-Anything` commit because the ConceptGraphs script imports `ram.*` even in `class_set none` mode.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m25_conceptgraphs_docker_build.log"
    run_script = OUT_DIR / "run_m25_conceptgraphs_docker_build.sh"
    status_path = OUT_DIR / "background_status.json"
    manifest_path = OUT_DIR / "docker_build_manifest.json"
    dockerfile = DOCKER_DIR / "Dockerfile"
    docker_build_command = (
        "docker build --progress=plain "
        f"-t {shlex.quote(IMAGE)} "
        f"--build-arg CONCEPTGRAPHS_COMMIT={shlex.quote(CONCEPTGRAPHS_COMMIT)} "
        f"--build-arg GSA_COMMIT={shlex.quote(GSA_COMMIT)} "
        f"-f {shlex.quote(str(dockerfile))} "
        f"{shlex.quote(str(DOCKER_DIR))}"
    )
    build_run_script(run_script, status_path, manifest_path, docker_build_command)

    launch_command = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1"
    already_running = tmux_has_session(SESSION)
    launch_result = {"ok": False, "stdout": "", "stderr": "session_already_running", "cmd": []}
    if not already_running:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        launch_result = run(["tmux", "new", "-d", "-s", SESSION, launch_command], timeout=20)

    running_after = tmux_has_session(SESSION)
    if already_running or running_after:
        status = "e005_m25_conceptgraphs_docker_build_job_launched"
    else:
        status = "e005_m25_conceptgraphs_docker_build_launch_failed"

    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_session": SESSION,
        "tmux_was_running_before_launch": already_running,
        "tmux_running_after_launch": running_after,
        "launch_executed": not already_running and launch_result["ok"],
        "launch_result": launch_result,
        "docker_image": IMAGE,
        "dockerfile": str(dockerfile),
        "build_context": str(DOCKER_DIR),
        "docker_build_command": docker_build_command,
        "launch_command": launch_command,
        "run_script": str(run_script),
        "log_path": str(log_path),
        "background_status_path": str(status_path),
        "output_manifest_path": str(manifest_path),
        "working_directory": str(ROOT),
        "expected_files": {
            "image": IMAGE,
            "dockerfile": str(dockerfile),
            "import_smoke": str(DOCKER_DIR / "import_smoke.py"),
        },
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m25_conceptgraphs_docker_build.py",
        "next_recommended_unit": "E005-M26 ConceptGraphs Docker build completion verification",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", {"status": status, "next": coverage["next_recommended_unit"]})
    write_text(OUT_DIR / "launch_command.txt", launch_command + "\n")
    write_text(OUT_DIR / "docker_build_command.txt", docker_build_command + "\n")
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if status == "e005_m25_conceptgraphs_docker_build_job_launched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
