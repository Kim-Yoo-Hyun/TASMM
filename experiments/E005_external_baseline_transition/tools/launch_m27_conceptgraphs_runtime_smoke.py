#!/usr/bin/env python3
"""Launch E005-M27 ConceptGraphs one-scan runtime smoke when the image is ready."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M27_conceptgraphs_runtime_smoke_v0"
M22_CONTRACT = EXPERIMENT_ROOT / "artifacts" / "E005-M22_conceptgraphs_runtime_preflight_v0" / "runtime_contract.json"
SESSION = "e005_m27_conceptgraphs_runtime_smoke"
IMAGE = "research2/conceptgraphs-smoke:latest"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
MODEL_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache"
GSA_CACHE = MODEL_CACHE / "gsa"
SMOKE_SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def image_ready(image: str) -> bool:
    return run(["docker", "image", "inspect", image, "--format", "{{.Id}}"], timeout=20)["ok"]


def count_glob(path: Path, pattern: str) -> int:
    return sum(1 for _ in path.glob(pattern)) if path.exists() else 0


def build_container_script() -> str:
    dataset_root = "/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet"
    dataset_config = f"{dataset_root}/config/conceptgraphs_3rscan_depth_aligned_scannet.yaml"
    python_bin = "/opt/conda/envs/conceptgraph/bin/python"
    generate_cmd = (
        f"{python_bin} scripts/generate_gsa_results.py "
        f"--dataset_root {shlex.quote(dataset_root)} "
        f"--dataset_config {shlex.quote(dataset_config)} "
        f"--scene_id {shlex.quote(SMOKE_SCAN_ID)} "
        "--class_set none --stride 5 --device cuda"
    )
    slam_cmd = (
        f"{python_bin} slam/cfslam_pipeline_batch.py "
        f"dataset_root={shlex.quote(dataset_root)} "
        f"dataset_config={shlex.quote(dataset_config)} "
        f"scene_id={shlex.quote(SMOKE_SCAN_ID)} "
        "stride=5 spatial_sim_type=overlap mask_conf_threshold=0.95 "
        "match_method=sim_sum sim_threshold=1.2 dbscan_eps=0.1 "
        "gsa_variant=none class_agnostic=True skip_bg=True max_bbox_area_ratio=0.5 "
        f"save_suffix={shlex.quote(SAVE_SUFFIX)} "
        "merge_interval=20 merge_visual_sim_thresh=0.8 merge_text_sim_thresh=0.8"
    )
    return (
        "set -euo pipefail; "
        "cd /workspace/concept-graphs/conceptgraph; "
        f"{generate_cmd}; "
        f"{slam_cmd}"
    )


def docker_command() -> list[str]:
    sam_ckpt = GSA_CACHE / "sam_vit_h_4b8939.pth"
    grounding_ckpt = GSA_CACHE / "groundingdino_swint_ogc.pth"
    return [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--network=host",
        "-e",
        "GSA_PATH=/workspace/Grounded-Segment-Anything",
        "-e",
        "HF_HOME=/opt/conceptgraphs_cache/huggingface",
        "-e",
        "TORCH_HOME=/opt/conceptgraphs_cache/torch",
        "-e",
        "XDG_CACHE_HOME=/opt/conceptgraphs_cache/xdg",
        "-e",
        "MPLCONFIGDIR=/tmp/matplotlib",
        "-e",
        "PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128",
        "-v",
        f"{STAGED_ROOT}:/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet:rw",
        "-v",
        f"{MODEL_CACHE}:/opt/conceptgraphs_cache:rw",
        "-v",
        f"{sam_ckpt}:/workspace/Grounded-Segment-Anything/sam_vit_h_4b8939.pth:ro",
        "-v",
        f"{grounding_ckpt}:/workspace/Grounded-Segment-Anything/groundingdino_swint_ogc.pth:ro",
        "-w",
        "/workspace/concept-graphs/conceptgraph",
        IMAGE,
        "bash",
        "-lc",
        build_container_script(),
    ]


def expected_outputs() -> dict[str, Any]:
    scan_root = STAGED_ROOT / SMOKE_SCAN_ID
    return {
        "gsa_detection_pattern": str(scan_root / "gsa_detections_none" / "*.pkl.gz"),
        "full_pcd": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"),
        "full_pcd_post": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"),
    }


def preflight() -> dict[str, Any]:
    scan_root = STAGED_ROOT / SMOKE_SCAN_ID
    return {
        "image_ready": image_ready(IMAGE),
        "staged_root_exists": STAGED_ROOT.exists(),
        "dataset_config_exists": (STAGED_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml").exists(),
        "scan_root_exists": scan_root.exists(),
        "color_count": count_glob(scan_root / "color", "*.jpg"),
        "depth_count": count_glob(scan_root / "depth", "*.png"),
        "pose_count": count_glob(scan_root / "pose", "*.txt"),
        "sam_checkpoint_exists": (GSA_CACHE / "sam_vit_h_4b8939.pth").exists(),
        "groundingdino_checkpoint_exists": (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(),
    }


def build_run_script(path: Path, status_path: Path, command: list[str]) -> None:
    docker_cmd = shlex.join(command)
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"SCAN_ID={shlex.quote(SMOKE_SCAN_ID)}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" SCAN_ID=\"$SCAN_ID\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'scan_id': os.environ['SCAN_ID'],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running conceptgraphs_runtime \"E005-M27 ConceptGraphs runtime smoke started\" 0",
        docker_cmd,
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed conceptgraphs_runtime \"E005-M27 ConceptGraphs runtime smoke failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed completed \"E005-M27 ConceptGraphs runtime smoke completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M27 ConceptGraphs Runtime Smoke Launch",
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
        f"- smoke scan: `{coverage['smoke_scan_id']}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        "",
        "## Claim Boundary",
        "",
        "- E005-M27 only launches a one-scan runtime smoke when the image is ready.",
        "- No baseline performance claim is supported before output inventory and schema inspection.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{timestamp}_e005_m27_conceptgraphs_runtime_smoke.log"
    run_script = OUT_DIR / "run_m27_conceptgraphs_runtime_smoke.sh"
    status_path = OUT_DIR / "background_status.json"
    contract = read_json(M22_CONTRACT)
    preflight_state = preflight()
    command = docker_command()
    build_run_script(run_script, status_path, command)

    blockers = [key for key, value in preflight_state.items() if key.endswith("_exists") and not value]
    if not preflight_state["image_ready"]:
        blockers.append("image_not_ready")
    if preflight_state["color_count"] <= 0 or preflight_state["depth_count"] <= 0 or preflight_state["pose_count"] <= 0:
        blockers.append("scan_frame_payload_missing")

    already_running = tmux_has_session(SESSION)
    launch_result = {"ok": False, "stdout": "", "stderr": "not_launched", "cmd": []}
    launch_executed = False
    if blockers:
        status = "e005_m27_conceptgraphs_runtime_smoke_blocked_preflight"
    else:
        launch_cmd = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(run_script))} > {shlex.quote(str(log_path))} 2>&1"
        if already_running:
            status = "e005_m27_conceptgraphs_runtime_smoke_already_running"
        else:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            launch_result = run(["tmux", "new", "-d", "-s", SESSION, launch_cmd], timeout=20)
            launch_executed = launch_result["ok"]
            status = "e005_m27_conceptgraphs_runtime_smoke_job_launched" if launch_executed else "e005_m27_conceptgraphs_runtime_smoke_launch_failed"

    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_session": SESSION,
        "tmux_running_after_launch": tmux_has_session(SESSION),
        "launch_executed": launch_executed,
        "launch_result": launch_result,
        "preflight": preflight_state,
        "blockers": blockers,
        "docker_image": IMAGE,
        "smoke_scan_id": SMOKE_SCAN_ID,
        "runtime_contract_source": str(M22_CONTRACT),
        "runtime_contract_status": contract.get("status"),
        "docker_command": shlex.join(command),
        "run_script": str(run_script),
        "log_path": str(log_path),
        "background_status_path": str(status_path),
        "expected_outputs": expected_outputs(),
        "verification_command": "python experiments/E005_external_baseline_transition/tools/verify_m27_conceptgraphs_runtime_smoke.py",
        "next_recommended_unit": "E005-M27 runtime smoke completion verification"
        if status.endswith("job_launched")
        else "E005-M26 Docker build completion verification",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", {"status": status, "next": coverage["next_recommended_unit"], "blockers": blockers})
    write_text(OUT_DIR / "docker_command.txt", shlex.join(command) + "\n")
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
