#!/usr/bin/env python3
"""Plan the bounded ConceptGraphs HM3D source-gap runtime launch and verification contract."""

from __future__ import annotations

import glob
import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M105_DIR = EXP_ROOT / "artifacts" / "E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0"
DATA_ROOT = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_v0"
    / "conceptgraphs_hm3d_source_gap_staged"
)
MODEL_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache"
GSA_CACHE = MODEL_CACHE / "gsa"
LOG_DIR = ROOT / "logs"

VERSION = "e008_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_v0"
READY_STATUS = "e008_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_ready"
BLOCKED_STATUS = "e008_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_blocked"
NEXT_UNIT = "E008-M107 ConceptGraphs HM3D source-gap runtime background launch"
VERIFY_UNIT = "E008-M108 ConceptGraphs HM3D source-gap runtime completion verification"
IMAGE = "research2/conceptgraphs-smoke:latest"
SESSION = "e008_m107_conceptgraphs_hm3d_source_gap_runtime"
CONTAINER_DATASET_ROOT = "/data/ConceptGraphs_hm3d_source_gap"
CONTAINER_CONFIG = f"{CONTAINER_DATASET_ROOT}/config/conceptgraphs_hm3d_source_gap.yaml"
PYTHON_BIN = "/opt/conda/envs/conceptgraph/bin/python"
SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"
MIN_GPU_FREE_MIB = 24000


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


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
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    except Exception as exc:  # noqa: BLE001 - contract records local preflight failures.
        return {"cmd": cmd, "ok": False, "returncode": None, "stderr": repr(exc), "stdout": ""}


def image_ready() -> bool:
    return run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], timeout=20)["ok"]


def tmux_running(session: str) -> bool:
    return run(["tmux", "has-session", "-t", session], timeout=10)["ok"]


def gpu_snapshot() -> dict[str, Any]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        timeout=10,
    )
    if not result["ok"] or not result["stdout"]:
        return {"available": False, "raw": result}
    first = result["stdout"].splitlines()[0]
    parts = [part.strip() for part in first.split(",")]
    if len(parts) < 4:
        return {"available": False, "raw": result}
    return {
        "available": True,
        "name": parts[0],
        "memory_total_mib": int(parts[1]),
        "memory_used_mib": int(parts[2]),
        "memory_free_mib": int(parts[3]),
        "raw": result,
    }


def expected_outputs(scan_id: str) -> dict[str, Any]:
    scan_root = DATA_ROOT / scan_id
    return {
        "version": VERSION,
        "scan_id": scan_id,
        "gsa_detection_pattern": str(scan_root / "gsa_detections_none" / "*.pkl.gz"),
        "full_pcd": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"),
        "full_pcd_post": str(scan_root / "pcd_saves" / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"),
    }


def output_ready(row: dict[str, Any]) -> bool:
    return (
        len(glob.glob(row["gsa_detection_pattern"])) > 0
        and Path(row["full_pcd"]).exists()
        and Path(row["full_pcd_post"]).exists()
    )


def scan_preflight(scan_id: str) -> dict[str, Any]:
    scan_root = DATA_ROOT / scan_id
    color_count = len(list((scan_root / "color").glob("*.jpg"))) if scan_root.exists() else 0
    depth_count = len(list((scan_root / "depth").glob("*.png"))) if scan_root.exists() else 0
    pose_count = len(list((scan_root / "pose").glob("*.txt"))) if scan_root.exists() else 0
    intrinsic_color = scan_root / "intrinsic" / "intrinsic_color.txt"
    expected = expected_outputs(scan_id)
    return {
        "version": VERSION,
        "scan_id": scan_id,
        "scan_root": str(scan_root),
        "scan_root_exists": scan_root.exists(),
        "color_count": color_count,
        "depth_count": depth_count,
        "pose_count": pose_count,
        "intrinsic_color_exists": intrinsic_color.exists(),
        "staged_payload_ready": scan_root.exists()
        and color_count > 0
        and color_count == depth_count == pose_count
        and intrinsic_color.exists(),
        "output_ready_before_launch": output_ready(expected),
    }


def container_script(scan_ids: list[str]) -> str:
    lines = [
        "set -euo pipefail",
        "cd /workspace/concept-graphs/conceptgraph",
    ]
    for scan_id in scan_ids:
        quoted_scan = shlex.quote(scan_id)
        lines.extend(
            [
                f"echo '[E008-M107] start scan {scan_id}'",
                (
                    f"{PYTHON_BIN} scripts/generate_gsa_results.py "
                    f"--dataset_root {shlex.quote(CONTAINER_DATASET_ROOT)} "
                    f"--dataset_config {shlex.quote(CONTAINER_CONFIG)} "
                    f"--scene_id {quoted_scan} --class_set none --stride 5 --device cuda"
                ),
                (
                    f"{PYTHON_BIN} slam/cfslam_pipeline_batch.py "
                    f"dataset_root={shlex.quote(CONTAINER_DATASET_ROOT)} "
                    f"dataset_config={shlex.quote(CONTAINER_CONFIG)} "
                    f"scene_id={quoted_scan} "
                    "stride=5 spatial_sim_type=overlap mask_conf_threshold=0.95 "
                    "match_method=sim_sum sim_threshold=1.2 dbscan_eps=0.1 "
                    "gsa_variant=none class_agnostic=True skip_bg=True max_bbox_area_ratio=0.5 "
                    f"save_suffix={shlex.quote(SAVE_SUFFIX)} "
                    "merge_interval=20 merge_visual_sim_thresh=0.8 merge_text_sim_thresh=0.8"
                ),
                f"echo '[E008-M107] completed scan {scan_id}'",
            ]
        )
    return "; ".join(lines)


def docker_command(scan_ids: list[str]) -> list[str]:
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
        f"{DATA_ROOT}:{CONTAINER_DATASET_ROOT}:rw",
        "-v",
        f"{MODEL_CACHE}:/opt/conceptgraphs_cache:rw",
        "-v",
        f"{GSA_CACHE / 'sam_vit_h_4b8939.pth'}:/workspace/Grounded-Segment-Anything/sam_vit_h_4b8939.pth:ro",
        "-v",
        f"{GSA_CACHE / 'groundingdino_swint_ogc.pth'}:/workspace/Grounded-Segment-Anything/groundingdino_swint_ogc.pth:ro",
        "-w",
        "/workspace/concept-graphs/conceptgraph",
        IMAGE,
        "bash",
        "-lc",
        container_script(scan_ids),
    ]


def write_run_script(path: Path, status_path: Path, command: list[str], scan_ids: list[str]) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"STATUS_PATH={shlex.quote(str(status_path))}",
        f"SCAN_IDS={shlex.quote(','.join(scan_ids))}",
        "write_status() {",
        "  local status=\"$1\"",
        "  local step=\"$2\"",
        "  local message=\"$3\"",
        "  local returncode=\"${4:-0}\"",
        "  STATUS_PATH=\"$STATUS_PATH\" STATUS=\"$status\" STEP=\"$step\" MESSAGE=\"$message\" RETURNCODE=\"$returncode\" SCAN_IDS=\"$SCAN_IDS\" python - <<'PY'",
        "import json, os",
        "from datetime import datetime",
        "from pathlib import Path",
        "payload = {",
        "    'message': os.environ['MESSAGE'],",
        "    'returncode': int(os.environ.get('RETURNCODE', '0')),",
        "    'scan_ids': [x for x in os.environ['SCAN_IDS'].split(',') if x],",
        "    'status': os.environ['STATUS'],",
        "    'step': os.environ['STEP'],",
        "    'updated_at': datetime.now().isoformat(timespec='seconds'),",
        "}",
        "Path(os.environ['STATUS_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\\n', encoding='utf-8')",
        "PY",
        "}",
        "write_status running conceptgraphs_hm3d_source_gap_runtime \"E008-M107 ConceptGraphs HM3D source-gap runtime started\" 0",
        shlex.join(command),
        "runtime_rc=$?",
        "if [ \"$runtime_rc\" -ne 0 ]; then",
        "  write_status failed conceptgraphs_hm3d_source_gap_runtime \"E008-M107 ConceptGraphs HM3D source-gap runtime failed\" \"$runtime_rc\"",
        "  exit \"$runtime_rc\"",
        "fi",
        "write_status completed completed \"E008-M107 ConceptGraphs HM3D source-gap runtime completed\" 0",
        "",
    ]
    write_text(path, "\n".join(lines))
    path.chmod(0o755)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E008-M106 ConceptGraphs HM3D Source-Gap Runtime Launch/Verification Contract",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Scan count: {coverage['scan_count']}.",
        f"- Staged root: `{coverage['staged_root']}`.",
        f"- Docker image ready: {str(coverage['image_ready']).lower()}.",
        f"- Checkpoints ready: {str(coverage['checkpoints_ready']).lower()}.",
        f"- GPU free MiB: {coverage['gpu_snapshot'].get('memory_free_mib')}.",
        f"- Launch now: {str(coverage['launch_now']).lower()}.",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- log path: `{coverage['log_path']}`.",
        f"- run script: `{coverage['run_script']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        f"- Blockers: {coverage['blockers']}.",
        f"- Selected next unit: {coverage['selected_next_unit']}.",
        "",
        "## Interpretation",
        "",
        "- M106 fixes the bounded runtime launch and verification contract only.",
        "- M106 does not launch the runtime job and does not produce candidates.",
        "- Source-gap recovery, candidate coordinate validation, trajectory execution, and final navigation claims remain future work.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    m105 = read_json(M105_DIR / "coverage.json")
    materialization_rows = read_jsonl(M105_DIR / "materialization_rows.jsonl")
    scan_ids = [str(row["scan_id"]) for row in materialization_rows if row.get("conceptgraphs_staging_ready")]
    gpu = gpu_snapshot()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e008_m107_conceptgraphs_hm3d_source_gap_runtime.log"
    run_script = ARTIFACT_DIR / "run_m107_conceptgraphs_hm3d_source_gap_runtime.sh"
    status_path = ARTIFACT_DIR / "background_status.json"
    command = docker_command(scan_ids)
    write_run_script(run_script, status_path, command, scan_ids)

    scan_rows = [scan_preflight(scan_id) for scan_id in scan_ids]
    expected_rows = [expected_outputs(scan_id) for scan_id in scan_ids]
    checkpoint_rows = [
        {
            "version": VERSION,
            "checkpoint_id": "sam_vit_h_4b8939",
            "path": str(GSA_CACHE / "sam_vit_h_4b8939.pth"),
            "exists": (GSA_CACHE / "sam_vit_h_4b8939.pth").exists(),
        },
        {
            "version": VERSION,
            "checkpoint_id": "groundingdino_swint_ogc",
            "path": str(GSA_CACHE / "groundingdino_swint_ogc.pth"),
            "exists": (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(),
        },
    ]
    checkpoints_ready = all(row["exists"] for row in checkpoint_rows)
    image_is_ready = image_ready()
    gpu_memory_ready = bool(gpu.get("available")) and int(gpu.get("memory_free_mib", 0)) >= MIN_GPU_FREE_MIB
    staged_ready = (
        m105.get("status") == "e008_m105_conceptgraphs_hm3d_source_gap_staging_materialization_smoke_ready"
        and bool(scan_rows)
        and all(row["staged_payload_ready"] for row in scan_rows)
    )
    blockers: list[str] = []
    if not staged_ready:
        blockers.append("m105_staging_not_ready")
    if not image_is_ready:
        blockers.append("conceptgraphs_image_not_ready")
    if not checkpoints_ready:
        blockers.append("checkpoint_missing")
    if not gpu_memory_ready:
        blockers.append("gpu_memory_below_contract_threshold")
    if tmux_running(SESSION):
        blockers.append("tmux_session_already_running")

    launch_command = (
        f"mkdir -p logs && tmux new -d -s {shlex.quote(SESSION)} "
        f"{shlex.quote('cd ' + str(ROOT) + ' && ' + str(run_script) + ' > ' + str(log_path) + ' 2>&1')}"
    )
    verification_command = (
        "python experiments/E008_real_navigation_benchmark/tools/verify_m108_conceptgraphs_hm3d_source_gap_runtime_outputs.py "
        f"--m106-root {ARTIFACT_DIR}"
    )
    launch_contract_rows = [
        {
            "version": VERSION,
            "row_type": "launch_contract",
            "launch_now": False,
            "long_job_required": True,
            "session": SESSION,
            "working_directory": str(ROOT),
            "log_path": str(log_path),
            "run_script": str(run_script),
            "background_status_path": str(status_path),
            "exact_launch_command": launch_command,
            "docker_command": shlex.join(command),
            "min_gpu_free_mib": MIN_GPU_FREE_MIB,
            "claim_boundary": "Launch produces runtime outputs only after completion verification; no source-gap recovery claim yet.",
        }
    ]
    verification_rows = [
        {
            "version": VERSION,
            "row_type": "verification_contract",
            "verification_command": verification_command,
            "required_checks": [
                "tmux session stopped or background_status completed",
                "gsa_detections_none/*.pkl.gz count > 0 per scan",
                "full_pcd_none_<suffix>.pkl.gz exists per scan",
                "full_pcd_none_<suffix>_post.pkl.gz exists per scan",
                "inspect only log tail/head or targeted errors",
            ],
            "claim_boundary": "Verification supports runtime output availability only; candidate export and navigation remain separate gates.",
        }
    ]
    long_job_rows = [
        {
            "version": VERSION,
            "row_type": "long_job_policy",
            "job": "E008-M107 ConceptGraphs HM3D source-gap runtime",
            "run_in_background": True,
            "log_path": str(log_path),
            "do_not_block_codex": True,
            "progress_check_policy": "check only when explicitly requested or when M108 depends on results",
            "log_inspection_policy": "tail/head or targeted grep only",
        }
    ]
    claim_boundary_rows = [
        {
            "version": VERSION,
            "claim": "ConceptGraphs_HM3D_runtime_launch_contract",
            "status": "supported" if not blockers else "blocked",
            "boundary": "M106 supports only launch/verification contract readiness.",
        },
        {
            "version": VERSION,
            "claim": "ConceptGraphs_source_gap_candidate_generation",
            "status": "blocked",
            "boundary": "requires M107 runtime outputs plus a candidate export adapter.",
        },
        {
            "version": VERSION,
            "claim": "source_gap_recovery",
            "status": "blocked",
            "boundary": "requires leakage-safe goal evaluation after alternative candidates exist.",
        },
        {
            "version": VERSION,
            "claim": "real_navigation_SR_SPL",
            "status": "blocked",
            "boundary": "requires candidate navmesh validation and Docker Habitat trajectory execution.",
        },
    ]
    m107_gate_rows = [
        {
            "version": VERSION,
            "gate": "pass",
            "condition": "M106 launch contract has no blockers and GPU memory is above threshold.",
            "current_blockers": blockers,
            "next_action": "Launch M107 in tmux using the exact launch command.",
            "claim_status_after_gate": "runtime launched/running only; no source-gap recovery claim yet",
        },
        {
            "version": VERSION,
            "gate": "warning",
            "condition": "Only GPU memory is below threshold while all data/image/checkpoint contracts pass.",
            "current_blockers": blockers,
            "next_action": "wait for GPU memory, then launch M107 without changing data or command",
            "claim_status_after_gate": "launch deferred",
        },
        {
            "version": VERSION,
            "gate": "fail",
            "condition": "staged data, Docker image, or checkpoints are not ready.",
            "current_blockers": blockers,
            "next_action": "repair the blocker before any runtime launch",
            "claim_status_after_gate": "runtime route unsupported until repaired",
        },
    ]
    status = READY_STATUS if not blockers else BLOCKED_STATUS
    if blockers == ["gpu_memory_below_contract_threshold"]:
        status = "e008_m106_conceptgraphs_hm3d_source_gap_runtime_launch_verification_contract_ready_waiting_gpu"
    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m105_status": m105.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "staged_root": str(DATA_ROOT),
        "scan_count": len(scan_ids),
        "scan_ids": scan_ids,
        "image": IMAGE,
        "image_ready": image_is_ready,
        "checkpoints_ready": checkpoints_ready,
        "gpu_snapshot": gpu,
        "gpu_memory_ready": gpu_memory_ready,
        "min_gpu_free_mib": MIN_GPU_FREE_MIB,
        "blockers": blockers,
        "launch_now": False,
        "long_job_required": True,
        "tmux_session": SESSION,
        "tmux_running_before_launch": tmux_running(SESSION),
        "log_path": str(log_path),
        "run_script": str(run_script),
        "background_status_path": str(status_path),
        "launch_command": launch_command,
        "verification_command": verification_command,
        "runtime_output_ready_before_launch": all(output_ready(row) for row in expected_rows),
        "candidate_rows_ready": False,
        "source_gap_recovery_supported": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
        "selected_verification_unit": VERIFY_UNIT,
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "runtime_scan_preflight_rows.jsonl", scan_rows)
    write_jsonl(ARTIFACT_DIR / "checkpoint_preflight_rows.jsonl", checkpoint_rows)
    write_jsonl(ARTIFACT_DIR / "expected_output_rows.jsonl", expected_rows)
    write_jsonl(ARTIFACT_DIR / "launch_contract_rows.jsonl", launch_contract_rows)
    write_jsonl(ARTIFACT_DIR / "verification_contract_rows.jsonl", verification_rows)
    write_jsonl(ARTIFACT_DIR / "long_job_policy_rows.jsonl", long_job_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "m107_gate_rows.jsonl", m107_gate_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
