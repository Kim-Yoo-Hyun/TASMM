#!/usr/bin/env python3
"""Plan E003-M67 OpenMask3D checkpoint acquisition and Docker env route."""

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
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M67_openmask3d_checkpoint_env_route_v0"
DEFAULT_CACHE_DIR = REPO_ROOT / "local_dataset" / "checkpoints" / "openmask3d"
DEFAULT_OPENMASK3D_REPO = EXPERIMENT_ROOT / "external" / "openmask3d"
M67_VERSION = "e003_m67_openmask3d_checkpoint_env_route_v0"


CHECKPOINTS = [
    {
        "cache_filename": "openmask3d_arbitrary_scene_model.ckpt",
        "download_method": "gdown_continue_google_drive_id",
        "file_id": "1rD2Uvbsi89X4lSkont_jUTT7X9iaox9y",
        "key": "openmask3d_mask_arbitrary_scene",
        "min_size_bytes": 50_000_000,
        "official_source": "https://github.com/OpenMask3D/openmask3d",
        "official_url": "https://drive.google.com/file/d/1rD2Uvbsi89X4lSkont_jUTT7X9iaox9y/view?usp=share_link",
        "resource_filename": "openmask3d_arbitrary_scene_model.ckpt",
    },
    {
        "cache_filename": "sam_vit_h_4b8939.pth",
        "download_method": "wget_continue_direct_url",
        "key": "sam_vit_h",
        "min_size_bytes": 2_000_000_000,
        "official_source": "https://github.com/facebookresearch/segment-anything#model-checkpoints",
        "official_url": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
        "resource_filename": "sam_vit_h_4b8939.pth",
    },
]


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


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
        "stdout_tail": proc.stdout[-2000:],
    }


def file_ready(path: Path, min_size_bytes: int) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {"exists": exists, "path": str(path), "ready": exists and size >= min_size_bytes, "size_bytes": size}


def build_download_script(path: Path, cache_dir: Path, openmask3d_repo: Path, out_dir: Path) -> None:
    resources_dir = openmask3d_repo / "resources"
    gdown_venv = REPO_ROOT / ".venv_tools" / "gdown"
    gdown_python = gdown_venv / "bin" / "python"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shlex.quote(str(REPO_ROOT))}",
        f"mkdir -p {shlex.quote(str(cache_dir))} {shlex.quote(str(resources_dir))}",
        f"GDOWN_VENV={shlex.quote(str(gdown_venv))}",
        f"GDOWN_PY={shlex.quote(str(gdown_python))}",
        'if [ ! -x "$GDOWN_PY" ]; then',
        '  python -m venv "$GDOWN_VENV"',
        "fi",
        'if ! "$GDOWN_PY" -c "import gdown" >/dev/null 2>&1; then',
        '  "$GDOWN_PY" -m pip install --upgrade pip gdown',
        "fi",
    ]
    for checkpoint in CHECKPOINTS:
        cache_path = cache_dir / checkpoint["cache_filename"]
        resource_path = resources_dir / checkpoint["resource_filename"]
        if checkpoint["download_method"] == "gdown_continue_google_drive_id":
            lines.append(
                '"$GDOWN_PY" -m gdown '
                f"--continue -O {shlex.quote(str(cache_path))} {checkpoint['file_id']}"
            )
        elif checkpoint["download_method"] == "wget_continue_direct_url":
            lines.append(f"wget -c -O {shlex.quote(str(cache_path))} {checkpoint['official_url']}")
        lines.append(f"ln -sfn {shlex.quote(str(cache_path))} {shlex.quote(str(resource_path))}")
    lines.append(
        "python experiments/E003_perception_noise_expansion/tools/verify_m67_openmask3d_checkpoints.py "
        f"--cache-dir {shlex.quote(str(cache_dir))} "
        f"--openmask3d-repo {shlex.quote(str(openmask3d_repo))} "
        f"--out-dir {shlex.quote(str(out_dir))}"
    )
    lines.append("")
    write_text(path, "\n".join(str(line) for line in lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M67 OpenMask3D Checkpoint / Env Route",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Stage ready: {coverage['m66_stage_ready']}",
            f"- OpenMask3D repo ready: {coverage['openmask3d_repo_ready']}",
            f"- Checkpoints ready: {coverage['checkpoints_ready']}",
            f"- Cache dir: `{coverage['cache_dir']}`",
            f"- Download script: `{coverage['download_script']}`",
            f"- tmux launch command: `{coverage['tmux_launch_command']}`",
            f"- Verification command: `{coverage['verification_command']}`",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Fallback route: `{coverage['fallback_route']}`",
            "",
            "## 논문 주장",
            "",
            "- E003-M67 only fixes how checkpoint acquisition and env preflight should proceed.",
            "- It does not support `OpenMask3D` proposal-quality or search-improvement claims.",
            "",
            "## 에이전트 추론",
            "",
            "- Because M66 scene staging and repo preflight passed, checkpoint acquisition is the next cheapest blocker to resolve.",
            "- Docker build remains high-risk because official `OpenMask3D` depends on older `torch` / CUDA / `MinkowskiEngine`, while the host GPU is RTX 5090.",
            "- If checkpoint download or Docker build blocks, direct bridge denominator expansion is the safer fallback than spending more time on environment repair.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before launching M68 checkpoint download. The launch should be a background job.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m66-dir", default=DEFAULT_M66_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, type=Path)
    parser.add_argument("--openmask3d-repo", default=DEFAULT_OPENMASK3D_REPO, type=Path)
    args = parser.parse_args()

    m66_stage = load_json(args.m66_dir / "stage" / "coverage.json")
    m66_verification = load_json(args.m66_dir / "verification" / "coverage.json")
    background_status = load_json(args.m66_dir / "background_status.json")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_rows = []
    ready_count = 0
    for checkpoint in CHECKPOINTS:
        cache_path = args.cache_dir / checkpoint["cache_filename"]
        resource_path = args.openmask3d_repo / "resources" / checkpoint["resource_filename"]
        cache = file_ready(cache_path, int(checkpoint["min_size_bytes"]))
        resource = file_ready(resource_path, int(checkpoint["min_size_bytes"]))
        ready_count += int(cache["ready"] and resource["ready"])
        checkpoint_rows.append(
            {
                **checkpoint,
                "cache": cache,
                "resource": resource,
            }
        )

    download_script = args.out_dir / "run_m68_checkpoint_download.sh"
    build_download_script(download_script, args.cache_dir, args.openmask3d_repo, args.out_dir)
    log_template = REPO_ROOT / "logs" / "$(date +%Y%m%d_%H%M%S)_e003_m68_openmask3d_checkpoints.log"
    tmux_launch_command = (
        "tmux new-session -d -s e003_m68_openmask3d_checkpoints "
        f"'cd {REPO_ROOT} && bash {download_script} > {log_template} 2>&1'"
    )
    verification_command = (
        "python experiments/E003_perception_noise_expansion/tools/verify_m67_openmask3d_checkpoints.py "
        f"--cache-dir {args.cache_dir} --openmask3d-repo {args.openmask3d_repo} --out-dir {args.out_dir}"
    )
    verifier_precheck = run_command(verification_command.split(), REPO_ROOT)
    gpu_probe = run_command(
        ["bash", "-lc", "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null || true"],
        REPO_ROOT,
    )
    docker_probe = run_command(
        ["bash", "-lc", "printf 'a\\n' | sudo -S docker info --format '{{.ServerVersion}}' 2>/dev/null || true"],
        REPO_ROOT,
    )

    checkpoints_ready = ready_count == len(CHECKPOINTS)
    selected_route = "checkpoint_download_background_launch_next"
    if checkpoints_ready:
        selected_route = "docker_env_build_preflight_next"
    if not m66_stage.get("stage_ready"):
        selected_route = "repair_scene_staging_first"

    coverage = {
        "background_status_m66": background_status,
        "cache_dir": str(args.cache_dir),
        "checkpoint_count": len(CHECKPOINTS),
        "checkpoint_rows": checkpoint_rows,
        "checkpoints_ready": checkpoints_ready,
        "docker_probe": docker_probe,
        "download_script": str(download_script),
        "fallback_route": "direct_bridge_denominator_expansion_if_checkpoint_or_docker_env_blocks",
        "gpu_probe": gpu_probe,
        "m66_stage_ready": bool(m66_stage.get("stage_ready")),
        "m66_verification_status": m66_verification.get("status"),
        "m67_version": M67_VERSION,
        "next_recommended_unit": "E003-M68 OpenMask3D checkpoint download background launch",
        "openmask3d_repo": str(args.openmask3d_repo),
        "openmask3d_repo_ready": (args.openmask3d_repo / "run_openmask3d_single_scene.sh").exists(),
        "route_rationale": [
            "M66 scene staging is ready, so the next blocker is checkpoint availability.",
            "Use `local_dataset/checkpoints/openmask3d/` as the cache and symlink into the ignored OpenMask3D repo resources directory.",
            "Run downloads in tmux with timestamped logs; do not block Codex on large downloads.",
            "Build the heavy Docker env only after checkpoint verification passes.",
        ],
        "selected_route": selected_route,
        "status": "openmask3d_checkpoint_env_route_ready",
        "tmux_launch_command": tmux_launch_command,
        "verification_command": verification_command,
        "verifier_precheck": verifier_precheck,
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "checkpoint_manifest.json", {"checkpoints": checkpoint_rows})
    write_json(
        args.out_dir / "download_command_plan.json",
        {
            "download_script": str(download_script),
            "log_template": str(log_template),
            "tmux_launch_command": tmux_launch_command,
            "working_directory": str(REPO_ROOT),
        },
    )
    write_json(
        args.out_dir / "env_route_decision.json",
        {
            "docker_image": "research2/openmask3d-smoke:latest",
            "dockerfile": str(EXPERIMENT_ROOT / "docker" / "openmask3d_smoke" / "Dockerfile"),
            "environment_risk": "high_due_to_old_torch_cuda_minkowskiengine_and_rtx5090_host",
            "fallback_route": coverage["fallback_route"],
            "selected_route": selected_route,
        },
    )
    write_json(args.out_dir / "verification_command.json", {"verification_command": verification_command})
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
