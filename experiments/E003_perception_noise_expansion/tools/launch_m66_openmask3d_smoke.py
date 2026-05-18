#!/usr/bin/env python3
"""Launch the E003-M66 OpenMask3D preflight/model-smoke job in tmux."""

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
DEFAULT_M65_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M65_openmask3d_scene_format_model_smoke_plan_v0"
DEFAULT_M66_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M66_openmask3d_model_smoke_v0"
LAUNCH_VERSION = "e003_m66_openmask3d_smoke_launch_v0"
TMUX_SESSION = "e003_m66_openmask3d_smoke"


def load_json(path: Path) -> dict[str, Any]:
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
    proc = subprocess.run(["tmux", "has-session", "-t", session], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode == 0


def build_run_script(path: Path, m66_dir: Path, openmask3d_repo_dir: Path, run_docker_build: bool) -> None:
    status_path = m66_dir / "background_status.json"
    stage_manifest = m66_dir / "stage" / "stage_manifest.json"
    raw_output_dir = m66_dir / "openmask3d_raw"
    dockerfile = EXPERIMENT_ROOT / "docker" / "openmask3d_smoke" / "Dockerfile"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shlex.quote(str(REPO_ROOT))}",
        f"mkdir -p {shlex.quote(str(openmask3d_repo_dir.parent))} {shlex.quote(str(raw_output_dir))}",
        f"echo '{{\"status\":\"running\",\"step\":\"start\",\"updated_at\":\"'$(date -Iseconds)'\"}}' > {shlex.quote(str(status_path))}",
        f"python experiments/E003_perception_noise_expansion/tools/stage_m66_openmask3d_scene_format.py --out-dir {shlex.quote(str(m66_dir))}",
        f"if [ ! -d {shlex.quote(str(openmask3d_repo_dir / '.git'))} ]; then git clone --depth 1 https://github.com/OpenMask3D/openmask3d.git {shlex.quote(str(openmask3d_repo_dir))}; fi",
        f"OPENMASK_COMMIT=$(git -C {shlex.quote(str(openmask3d_repo_dir))} rev-parse HEAD)",
        f"MASK_CKPT={shlex.quote(str(openmask3d_repo_dir / 'resources' / 'openmask3d_arbitrary_scene_model.ckpt'))}",
        f"SAM_CKPT={shlex.quote(str(openmask3d_repo_dir / 'resources' / 'sam_vit_h_4b8939.pth'))}",
        "mkdir -p \"$(dirname \"$MASK_CKPT\")\"",
        "if [ ! -s \"$MASK_CKPT\" ] || [ ! -s \"$SAM_CKPT\" ]; then",
        f"  python - <<'PY'\nimport json\nfrom pathlib import Path\nstatus_path = Path({str(status_path)!r})\nstatus_path.write_text(json.dumps({{'status': 'needs_checkpoints', 'step': 'checkpoint_preflight', 'openmask3d_commit': 'PLACEHOLDER', 'mask_checkpoint': {str(openmask3d_repo_dir / 'resources' / 'openmask3d_arbitrary_scene_model.ckpt')!r}, 'sam_checkpoint': {str(openmask3d_repo_dir / 'resources' / 'sam_vit_h_4b8939.pth')!r}, 'message': 'OpenMask3D/SAM checkpoints are not present; model inference was not launched.'}}, indent=2) + '\\n', encoding='utf-8')\nPY",
        "  python - <<PY\nfrom pathlib import Path\np = Path(" + repr(str(status_path)) + ")\ns = p.read_text()\ns = s.replace('PLACEHOLDER', '${OPENMASK_COMMIT}')\np.write_text(s)\nPY",
        "  exit 0",
        "fi",
    ]
    if run_docker_build:
        lines.extend(
            [
                f"printf 'a\\n' | sudo -S docker build -t research2/openmask3d-smoke:latest -f {shlex.quote(str(dockerfile))} {shlex.quote(str(dockerfile.parent))}",
                "echo '{\"status\":\"docker_build_completed\",\"step\":\"docker_build\",\"updated_at\":\"'$(date -Iseconds)'\"}' > "
                + shlex.quote(str(status_path)),
                "# Model inference wrapper is intentionally kept explicit per scene; adapter execution follows after raw outputs are produced.",
            ]
        )
    else:
        lines.extend(
            [
                f"echo '{{\"status\":\"needs_docker_build\",\"step\":\"docker_preflight\",\"openmask3d_commit\":\"'${{OPENMASK_COMMIT}}'\",\"dockerfile\":\"{str(dockerfile)}\",\"message\":\"Checkpoints are present, but Docker build was not requested for this launch.\"}}' > {shlex.quote(str(status_path))}",
            ]
        )
    lines.append("")
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M66 OpenMask3D Launch",
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
            f"- log path: `{coverage['log_path']}`.",
            f"- run script: `{coverage['run_script']}`.",
            f"- OpenMask3D repo dir: `{coverage['openmask3d_repo_dir']}`.",
            f"- run Docker build requested: {coverage['run_docker_build_requested']}.",
            f"- verification command: `{coverage['verification_command']}`.",
            "",
            "## 논문 주장",
            "",
            "- E003-M66 launch does not create a paper result claim.",
            "- It only launches the background preflight/model-smoke route required before `OpenMask3D` can be evaluated.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not monitor the job continuously.",
            "- If it exits at checkpoint preflight, acquire checkpoints or choose the fallback route before trying model inference.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None while the background job is running or waiting for checkpoint acquisition.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m65-dir", default=DEFAULT_M65_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_M66_DIR, type=Path)
    parser.add_argument("--run-docker-build", action="store_true")
    args = parser.parse_args()

    command_plan = load_json(args.m65_dir / "openmask3d_command_plan.json")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    launch_dir = args.out_dir / "launch"
    openmask3d_repo_dir = EXPERIMENT_ROOT / "external" / "openmask3d"
    run_script = launch_dir / "run_m66_openmask3d_smoke.sh"
    build_run_script(run_script, args.out_dir, openmask3d_repo_dir, args.run_docker_build)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO_ROOT / "logs" / f"{timestamp}_e003_m66_openmask3d_smoke.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""

    if not tmux_path:
        status = "openmask3d_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "openmask3d_background_job_already_running"
        background_status = "running"
    else:
        command = [
            "tmux",
            "new-session",
            "-d",
            "-s",
            TMUX_SESSION,
            "bash",
            "-lc",
            f"cd {shlex.quote(str(REPO_ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1",
        ]
        write_text(launch_dir / "launch_command.txt", shlex.join(command) + "\n")
        proc = subprocess.run(command, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout
        launch_stderr = proc.stderr
        after_running = tmux_has_session(TMUX_SESSION)
        if proc.returncode == 0 and after_running:
            status = "openmask3d_background_job_launched"
            background_status = "running"
        elif proc.returncode == 0:
            status = "openmask3d_background_job_exited_needs_verification"
            background_status = "needs_verification"
        else:
            status = "openmask3d_launch_failed"
            background_status = "failed"

    coverage = {
        "background_job_status": background_status,
        "command_plan": str(args.m65_dir / "openmask3d_command_plan.json"),
        "expected_files": command_plan.get("expected_files_after_success"),
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stderr": launch_stderr,
        "launch_stdout": launch_stdout,
        "launch_time": datetime.now().isoformat(timespec="seconds"),
        "launch_version": LAUNCH_VERSION,
        "log_path": str(log_path),
        "openmask3d_repo_dir": str(openmask3d_repo_dir),
        "run_docker_build_requested": args.run_docker_build,
        "run_script": str(run_script),
        "status": status,
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "verification_command": f"python experiments/E003_perception_noise_expansion/tools/verify_m66_openmask3d_smoke.py --m66-dir {args.out_dir}",
        "working_directory": str(REPO_ROOT),
    }
    write_json(launch_dir / "coverage.json", coverage)
    (launch_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if background_status in {"running", "needs_verification"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
