#!/usr/bin/env python3
"""Launch ConceptGraphs repo/checkpoint acquisition in a background tmux job."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M22_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M22_conceptgraphs_runtime_preflight_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M23_conceptgraphs_acquisition_launch_v0"

CONCEPTGRAPHS_REPO = ROOT / "local_dataset" / "external_repos" / "concept-graphs"
GSA_REPO = ROOT / "local_dataset" / "external_repos" / "Grounded-Segment-Anything"
GSA_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache" / "gsa"
SAM_SOURCE = ROOT / "local_dataset" / "checkpoints" / "openmask3d" / "sam_vit_h_4b8939.pth"

CONCEPTGRAPHS_COMMIT = "93277a02bd89171f8121e84203121cf7af9ebb5d"
GSA_COMMIT = "a4d76a2b55e348943cba4cd57d7553c354296223"
GROUNDINGDINO_URL = (
    "https://github.com/IDEA-Research/GroundingDINO/releases/download/"
    "v0.1.0-alpha/groundingdino_swint_ogc.pth"
)
SESSION = "e005_m23_conceptgraphs_acquisition"


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


def build_run_script(path: Path, status_path: Path, manifest_path: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"ROOT={shlex.quote(str(ROOT))}",
        f"CONCEPTGRAPHS_REPO={shlex.quote(str(CONCEPTGRAPHS_REPO))}",
        f"GSA_REPO={shlex.quote(str(GSA_REPO))}",
        f"GSA_CACHE={shlex.quote(str(GSA_CACHE))}",
        f"SAM_SOURCE={shlex.quote(str(SAM_SOURCE))}",
        f"CONCEPTGRAPHS_COMMIT={shlex.quote(CONCEPTGRAPHS_COMMIT)}",
        f"GSA_COMMIT={shlex.quote(GSA_COMMIT)}",
        f"GROUNDINGDINO_URL={shlex.quote(GROUNDINGDINO_URL)}",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"MANIFEST_PATH={shlex.quote(str(manifest_path))}",
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
        "clone_or_update() {",
        "  local repo_url=\"$1\"",
        "  local repo_dir=\"$2\"",
        "  local commit=\"$3\"",
        "  local name=\"$4\"",
        "  if [ -d \"$repo_dir/.git\" ]; then",
        "    write_status running \"fetch_${name}\" \"Fetching ${name}\" 0",
        "    git -C \"$repo_dir\" fetch --all --tags",
        "  else",
        "    write_status running \"clone_${name}\" \"Cloning ${name}\" 0",
        "    rm -rf \"$repo_dir\"",
        "    git clone \"$repo_url\" \"$repo_dir\"",
        "  fi",
        "  local rc=$?",
        "  if [ \"$rc\" -ne 0 ]; then",
        "    write_status failed \"repo_${name}\" \"Repo acquisition failed for ${name}\" \"$rc\"",
        "    exit \"$rc\"",
        "  fi",
        "  write_status running \"checkout_${name}\" \"Checking out ${name} commit\" 0",
        "  git -C \"$repo_dir\" checkout \"$commit\"",
        "  rc=$?",
        "  if [ \"$rc\" -ne 0 ]; then",
        "    write_status failed \"checkout_${name}\" \"Checkout failed for ${name}\" \"$rc\"",
        "    exit \"$rc\"",
        "  fi",
        "  git -C \"$repo_dir\" submodule update --init --recursive || true",
        "}",
        "mkdir -p \"$ROOT/local_dataset/external_repos\" \"$GSA_CACHE\" \"$(dirname \"$STATUS_PATH\")\"",
        "write_status running start \"E005-M23 acquisition started\" 0",
        "clone_or_update https://github.com/concept-graphs/concept-graphs.git \"$CONCEPTGRAPHS_REPO\" \"$CONCEPTGRAPHS_COMMIT\" conceptgraphs",
        "clone_or_update https://github.com/IDEA-Research/Grounded-Segment-Anything.git \"$GSA_REPO\" \"$GSA_COMMIT\" gsa",
        "write_status running checkpoint_sam \"Linking SAM checkpoint\" 0",
        "if [ ! -f \"$SAM_SOURCE\" ]; then",
        "  write_status failed checkpoint_sam \"SAM checkpoint source missing\" 20",
        "  exit 20",
        "fi",
        "ln -sf \"$SAM_SOURCE\" \"$GSA_CACHE/sam_vit_h_4b8939.pth\"",
        "ln -sf \"$SAM_SOURCE\" \"$GSA_REPO/sam_vit_h_4b8939.pth\"",
        "write_status running checkpoint_groundingdino \"Downloading GroundingDINO checkpoint\" 0",
        "wget -c -O \"$GSA_CACHE/groundingdino_swint_ogc.pth\" \"$GROUNDINGDINO_URL\"",
        "rc=$?",
        "if [ \"$rc\" -ne 0 ]; then",
        "  write_status failed checkpoint_groundingdino \"GroundingDINO checkpoint download failed\" \"$rc\"",
        "  exit \"$rc\"",
        "fi",
        "ln -sf \"$GSA_CACHE/groundingdino_swint_ogc.pth\" \"$GSA_REPO/groundingdino_swint_ogc.pth\"",
        "CONCEPT_HEAD=$(git -C \"$CONCEPTGRAPHS_REPO\" rev-parse HEAD 2>/dev/null || true)",
        "GSA_HEAD=$(git -C \"$GSA_REPO\" rev-parse HEAD 2>/dev/null || true)",
        "GROUNDING_SIZE=$(stat -c%s \"$GSA_CACHE/groundingdino_swint_ogc.pth\" 2>/dev/null || echo 0)",
        "STATUS_PATH=\"$STATUS_PATH\" MANIFEST_PATH=\"$MANIFEST_PATH\" CONCEPT_HEAD=\"$CONCEPT_HEAD\" GSA_HEAD=\"$GSA_HEAD\" GROUNDING_SIZE=\"$GROUNDING_SIZE\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': 'completed',",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "    'conceptgraphs_head': os.environ['CONCEPT_HEAD'],",
        "    'gsa_head': os.environ['GSA_HEAD'],",
        "    'groundingdino_size_bytes': int(os.environ['GROUNDING_SIZE']),",
        "    'conceptgraphs_repo': os.environ.get('CONCEPTGRAPHS_REPO', ''),",
        "    'gsa_repo': os.environ.get('GSA_REPO', ''),",
        "}",
        "Path(os.environ['MANIFEST_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps({'status': 'completed', 'step': 'completed', 'message': 'E005-M23 acquisition completed', 'returncode': 0, 'updated_at': payload['updated_at']}, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "write_status completed completed \"E005-M23 acquisition completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M23 ConceptGraphs Acquisition Launch",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- launch executed: {str(coverage['launch_executed']).lower()}.",
        f"- log path: `{coverage['log_path']}`.",
        f"- run script: `{coverage['run_script']}`.",
        f"- status path: `{coverage['background_status_path']}`.",
        f"- output manifest: `{coverage['output_manifest_path']}`.",
        f"- working directory: `{coverage['working_directory']}`.",
        f"- `ConceptGraphs` repo: `{coverage['expected_files']['conceptgraphs_repo']}`.",
        f"- `Grounded-Segment-Anything` repo: `{coverage['expected_files']['gsa_repo']}`.",
        f"- `GroundingDINO` checkpoint: `{coverage['expected_files']['groundingdino_checkpoint']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        "",
        "## Claim Boundary",
        "",
        "- E005-M23 only launches acquisition; it is not a runtime result.",
        "- No `ConceptGraphs` baseline comparison is supported before completion verification and runtime smoke.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m23_conceptgraphs_acquisition.log"
    run_script = OUT_DIR / "run_m23_conceptgraphs_acquisition.sh"
    status_path = OUT_DIR / "background_status.json"
    manifest_path = OUT_DIR / "acquisition_manifest.json"
    build_run_script(run_script, status_path, manifest_path)
    launch_command = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1"

    already_running = tmux_has_session(SESSION)
    launch_result = {"ok": False, "stdout": "", "stderr": "session_already_running", "cmd": []}
    if not already_running:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        launch_result = run(["tmux", "new", "-d", "-s", SESSION, launch_command], timeout=20)

    running_after = tmux_has_session(SESSION)
    status = "e005_m23_conceptgraphs_acquisition_job_launched" if running_after else "e005_m23_conceptgraphs_acquisition_launch_failed"
    if already_running:
        status = "e005_m23_conceptgraphs_acquisition_already_running"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_session": SESSION,
        "tmux_running_after_launch": running_after,
        "launch_executed": bool(launch_result["ok"]),
        "launch_command": launch_command,
        "launch_result": launch_result,
        "working_directory": str(ROOT),
        "log_path": str(log_path),
        "run_script": str(run_script),
        "background_status_path": str(status_path),
        "output_manifest_path": str(manifest_path),
        "expected_files": {
            "conceptgraphs_repo": str(CONCEPTGRAPHS_REPO),
            "conceptgraphs_expected_commit": CONCEPTGRAPHS_COMMIT,
            "gsa_repo": str(GSA_REPO),
            "gsa_expected_commit": GSA_COMMIT,
            "sam_symlink_cache": str(GSA_CACHE / "sam_vit_h_4b8939.pth"),
            "sam_symlink_gsa_repo": str(GSA_REPO / "sam_vit_h_4b8939.pth"),
            "groundingdino_checkpoint": str(GSA_CACHE / "groundingdino_swint_ogc.pth"),
            "groundingdino_symlink_gsa_repo": str(GSA_REPO / "groundingdino_swint_ogc.pth"),
        },
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m23_conceptgraphs_acquisition.py",
        "runtime_launched": False,
        "docker_build_launched": False,
        "claim_boundary": [
            "No ConceptGraphs performance claim from E005-M23.",
            "No runtime or Docker build is launched in E005-M23.",
            "Completion must be verified before runtime smoke.",
        ],
    }
    decision = {
        "status": status,
        "decision": "background_acquisition_launched" if running_after else "launch_failed",
        "next_action": "E005-M24 ConceptGraphs acquisition completion verification",
        "log_path": str(log_path),
        "verification_command": coverage["verification_command"],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if running_after else 1


if __name__ == "__main__":
    raise SystemExit(main())
