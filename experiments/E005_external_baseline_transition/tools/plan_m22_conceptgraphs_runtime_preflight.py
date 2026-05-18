#!/usr/bin/env python3
"""Plan the ConceptGraphs Docker/runtime preflight after staging materialization."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M20_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M20_conceptgraphs_interface_audit_v0"
M21_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M21_conceptgraphs_staging_materialization_v0"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M22_conceptgraphs_runtime_preflight_v0"

CONCEPTGRAPHS_REPO = ROOT / "local_dataset" / "external_repos" / "concept-graphs"
GSA_REPO = ROOT / "local_dataset" / "external_repos" / "Grounded-Segment-Anything"
MODEL_CACHE = ROOT / "local_dataset" / "ConceptGraphs_model_cache"
GSA_CACHE = MODEL_CACHE / "gsa"
STAGED_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"
STAGED_CONFIG = STAGED_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml"
SAM_SOURCE = ROOT / "local_dataset" / "checkpoints" / "openmask3d" / "sam_vit_h_4b8939.pth"
SMOKE_SCAN_ID = "ddc73795-765b-241a-9c5d-b97744afe077"

CONCEPTGRAPHS_COMMIT = "93277a02bd89171f8121e84203121cf7af9ebb5d"
GSA_COMMIT = "a4d76a2b55e348943cba4cd57d7553c354296223"
LLAVA_COMMIT = "8fc54a09a6be74b2abd913c468fb3d42ae826194"
IMAGE_NAME = "research2/conceptgraphs-smoke:latest"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
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


def run(cmd: list[str], timeout: int = 20, cwd: Path | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
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
    except Exception as exc:  # noqa: BLE001 - preflight should record local probe failures.
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def git_head(repo: Path) -> dict[str, Any]:
    if not (repo / ".git").exists():
        return {"path": str(repo), "exists": False, "head": None}
    result = run(["git", "rev-parse", "HEAD"], cwd=repo)
    return {"path": str(repo), "exists": True, "head": result["stdout"] if result["ok"] else None}


def docker_probe() -> dict[str, Any]:
    version = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=10)
    runtimes = run(["docker", "info", "--format", "{{json .Runtimes}}"], timeout=10)
    images = run(["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}"], timeout=10)
    matching_images = []
    if images["ok"]:
        for line in images["stdout"].splitlines():
            if any(token in line for token in ["concept", "cuda", "dualmap", "real-smoke", "openmask"]):
                matching_images.append(line)
    return {
        "docker_ready": version["ok"],
        "server_version": version["stdout"] if version["ok"] else None,
        "nvidia_runtime_detected": "nvidia" in runtimes.get("stdout", ""),
        "runtime_probe_ok": runtimes["ok"],
        "conceptgraphs_image_exists": any(line.startswith("research2/conceptgraphs-smoke:") for line in matching_images),
        "relevant_local_images": matching_images,
    }


def gpu_probe() -> dict[str, Any]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits",
        ],
        timeout=10,
    )
    if not result["ok"]:
        return {"nvidia_smi_ready": False, "raw": result}
    parts = [part.strip() for part in result["stdout"].split(",")]
    return {
        "nvidia_smi_ready": True,
        "name": parts[0] if len(parts) > 0 else "",
        "memory_total_mib": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
        "memory_free_mib": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
        "driver_version": parts[3] if len(parts) > 3 else "",
    }


def staged_probe() -> dict[str, Any]:
    rows = read_jsonl(M21_DIR / "materialization_rows.jsonl")
    smoke = STAGED_ROOT / SMOKE_SCAN_ID
    return {
        "m21_status": read_json(M21_DIR / "coverage.json").get("status"),
        "staged_root": str(STAGED_ROOT),
        "staged_config": str(STAGED_CONFIG),
        "staged_root_exists": STAGED_ROOT.exists(),
        "staged_config_exists": STAGED_CONFIG.exists(),
        "ready_scan_count": sum(row.get("conceptgraphs_scannet_ready", False) for row in rows),
        "selected_scan_count": len(rows),
        "smoke_scan_id": SMOKE_SCAN_ID,
        "smoke_color_count": len(list((smoke / "color").glob("*.jpg"))),
        "smoke_depth_count": len(list((smoke / "depth").glob("*.png"))),
        "smoke_pose_count": len(list((smoke / "pose").glob("*.txt"))),
        "smoke_intrinsic_color_exists": (smoke / "intrinsic" / "intrinsic_color.txt").exists(),
    }


def checkpoint_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "id": "sam_vit_h_4b8939",
            "required_for": "class_set_none_sam_dense_smoke",
            "path": str(SAM_SOURCE),
            "ready": SAM_SOURCE.exists(),
            "source": "reused_from_openmask3d_checkpoint_cache",
            "acquisition_needed": not SAM_SOURCE.exists(),
        },
        {
            "id": "groundingdino_swint_ogc",
            "required_for": "generate_gsa_results_import_and_unconditional_model_init",
            "path": str(GSA_CACHE / "groundingdino_swint_ogc.pth"),
            "ready": (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(),
            "source": "Grounded-Segment-Anything checkpoint",
            "acquisition_needed": not (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(),
        },
        {
            "id": "ram_swin_large_14m",
            "required_for": "ram_withbg_allclasses_full_detect_variant",
            "path": str(GSA_CACHE / "ram_swin_large_14m.pth"),
            "ready": (GSA_CACHE / "ram_swin_large_14m.pth").exists(),
            "source": "Grounded-Segment-Anything checkpoint",
            "acquisition_needed": "defer_for_first_class_set_none_smoke",
        },
        {
            "id": "llava_7b_v0",
            "required_for": "scenegraph_caption_and_relation_generation",
            "path": str(MODEL_CACHE / "llava" / "LLaVA-7B-v0"),
            "ready": (MODEL_CACHE / "llava" / "LLaVA-7B-v0").exists(),
            "source": "LLaVA",
            "acquisition_needed": "defer_until_object_map_pkl_exists",
        },
    ]
    return rows


def dependency_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    env = source.get("environment_signals", {})
    return [
        {"dependency": "Python 3.10", "needed_for": "ConceptGraphs official env", "ready_now": False, "route": "Docker/conda env"},
        {"dependency": "PyTorch 2.0.1 + CUDA 11.8", "needed_for": "official tested setup", "ready_now": False, "route": "Docker/conda env", "source_signal": env.get("pytorch_2_0_1") and env.get("cuda_11_8")},
        {"dependency": "pytorch3d 0.7.4", "needed_for": "3D ops", "ready_now": False, "route": "Docker/conda env", "source_signal": env.get("pytorch3d")},
        {"dependency": "gradslam conceptfusion branch", "needed_for": "dataset/SLAM utilities", "ready_now": False, "route": "Docker build from source", "source_signal": env.get("gradslam")},
        {"dependency": "Grounded-Segment-Anything", "needed_for": "GSA detection extraction", "ready_now": GSA_REPO.exists(), "route": f"clone at {GSA_COMMIT}"},
        {"dependency": "SAM checkpoint", "needed_for": "dense segmentation", "ready_now": SAM_SOURCE.exists(), "route": "reuse OpenMask3D checkpoint cache"},
        {"dependency": "GroundingDINO checkpoint", "needed_for": "unconditional GSA model init", "ready_now": (GSA_CACHE / "groundingdino_swint_ogc.pth").exists(), "route": "resumable checkpoint download"},
        {"dependency": "RAM checkpoint", "needed_for": "class-aware ConceptGraphs-Detect", "ready_now": (GSA_CACHE / "ram_swin_large_14m.pth").exists(), "route": "defer for first smoke"},
        {"dependency": "LLaVA", "needed_for": "scene graph captions/relations", "ready_now": False, "route": "defer until object map pkl exists"},
    ]


def acquisition_plan() -> dict[str, Any]:
    log_path = ROOT / "logs" / "<YYYYMMDD_HHMMSS>_e005_m23_conceptgraphs_acquisition.log"
    return {
        "status": "planned_not_launched",
        "next_unit": "E005-M23 ConceptGraphs repo/checkpoint acquisition background launch",
        "repo_policy": {
            "conceptgraphs_repo": str(CONCEPTGRAPHS_REPO),
            "conceptgraphs_clone": f"git clone https://github.com/concept-graphs/concept-graphs.git {CONCEPTGRAPHS_REPO}",
            "conceptgraphs_checkout": f"git checkout {CONCEPTGRAPHS_COMMIT}",
            "gsa_repo": str(GSA_REPO),
            "gsa_clone": f"git clone https://github.com/IDEA-Research/Grounded-Segment-Anything.git {GSA_REPO}",
            "gsa_checkout": f"git checkout {GSA_COMMIT}",
            "llava_checkout_deferred": LLAVA_COMMIT,
        },
        "checkpoint_policy": {
            "cache_root": str(GSA_CACHE),
            "reuse_existing_sam": str(SAM_SOURCE),
            "required_first_smoke": ["sam_vit_h_4b8939.pth", "groundingdino_swint_ogc.pth"],
            "deferred": ["ram_swin_large_14m.pth", "tag2text_swin_14m.pth", "LLaVA-7B-v0"],
            "resumable_download_rule": "use aria2c or wget -c; write logs under logs/; verify by file size/checksum if available",
        },
        "docker_policy": {
            "image": IMAGE_NAME,
            "build_required": True,
            "preferred_base": "nvidia/cuda:11.8.0-devel-ubuntu22.04",
            "local_cuda_base_available": "nvidia/cuda:11.8.0-base-ubuntu22.04",
            "run_long_build_in_tmux": True,
            "log_path_template": str(log_path),
        },
        "tmux_template": (
            "mkdir -p logs && tmux new -d -s e005_m23_conceptgraphs_acquisition "
            "'cd /home/yoohyun/research2 && <repo_checkpoint_or_docker_command> "
            "> logs/<YYYYMMDD_HHMMSS>_e005_m23_conceptgraphs_acquisition.log 2>&1'"
        ),
    }


def runtime_contract() -> dict[str, Any]:
    dataset_root_container = "/data/ConceptGraphs_staged/3rscan_depth_aligned_scannet"
    dataset_config_container = f"{dataset_root_container}/config/conceptgraphs_3rscan_depth_aligned_scannet.yaml"
    return {
        "status": "planned_not_launched",
        "smoke_scan_id": SMOKE_SCAN_ID,
        "docker_image": IMAGE_NAME,
        "host_mounts": [
            {"host": str(STAGED_ROOT), "container": dataset_root_container, "mode": "rw"},
            {"host": str(MODEL_CACHE), "container": "/opt/conceptgraphs_cache", "mode": "rw"},
        ],
        "first_smoke_variant": {
            "id": "class_set_none_sam_dense_smoke",
            "why": "uses SAM dense masks and avoids RAM/LLaVA for the first object-map feasibility smoke",
            "known_caveat": "ConceptGraphs generate_gsa_results.py still initializes GroundingDINO before class_set branching, so the GroundingDINO checkpoint is still required unless source is patched.",
        },
        "commands_inside_container": [
            "cd /workspace/concept-graphs/conceptgraph",
            (
                "python scripts/generate_gsa_results.py "
                f"--dataset_root {dataset_root_container} "
                f"--dataset_config {dataset_config_container} "
                f"--scene_id {SMOKE_SCAN_ID} "
                "--class_set none --stride 5 --sam_variant sam --device cuda"
            ),
            (
                "python slam/cfslam_pipeline_batch.py "
                f"dataset_root={dataset_root_container} "
                f"dataset_config={dataset_config_container} "
                f"scene_id={SMOKE_SCAN_ID} "
                "stride=5 spatial_sim_type=overlap mask_conf_threshold=0.95 "
                "match_method=sim_sum sim_threshold=1.2 dbscan_eps=0.1 "
                "gsa_variant=none class_agnostic=True skip_bg=True max_bbox_area_ratio=0.5 "
                "save_suffix=overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub "
                "merge_interval=20 merge_visual_sim_thresh=0.8 merge_text_sim_thresh=0.8"
            ),
        ],
        "expected_outputs": [
            f"{STAGED_ROOT}/{SMOKE_SCAN_ID}/gsa_detections_none/*.pkl.gz",
            f"{STAGED_ROOT}/{SMOKE_SCAN_ID}/pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub.pkl.gz",
            f"{STAGED_ROOT}/{SMOKE_SCAN_ID}/pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub_post.pkl.gz",
        ],
        "verification_command": (
            "find local_dataset/ConceptGraphs_staged/3rscan_depth_aligned_scannet/"
            f"{SMOKE_SCAN_ID} -path '*/gsa_detections_none/*.pkl.gz' -o -path '*/pcd_saves/*.pkl.gz'"
        ),
        "runtime_launched_in_m22": False,
    }


def build_report(
    coverage: dict[str, Any],
    deps: list[dict[str, Any]],
    checkpoints: list[dict[str, Any]],
    acquisition: dict[str, Any],
    runtime: dict[str, Any],
) -> str:
    blocker_deps = [row for row in deps if not row.get("ready_now")]
    missing_checkpoints = [row for row in checkpoints if row.get("ready") is False and row.get("acquisition_needed") is not False]
    lines = [
        "# E005-M22 ConceptGraphs Docker/Runtime Preflight",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Docker ready: {str(coverage['docker_ready']).lower()}.",
        f"- NVIDIA runtime detected: {str(coverage['nvidia_runtime_detected']).lower()}.",
        f"- GPU: `{coverage['gpu_name']}` with free memory {coverage['gpu_free_mib']} MiB.",
        f"- Staged scans ready: {coverage['ready_scan_count']} / {coverage['selected_scan_count']}.",
        f"- ConceptGraphs repo present: {str(coverage['conceptgraphs_repo_present']).lower()}.",
        f"- GSA repo present: {str(coverage['gsa_repo_present']).lower()}.",
        f"- ConceptGraphs Docker image present: {str(coverage['conceptgraphs_image_exists']).lower()}.",
        f"- SAM checkpoint ready: {str(coverage['sam_checkpoint_ready']).lower()}.",
        f"- GroundingDINO checkpoint ready: {str(coverage['groundingdino_checkpoint_ready']).lower()}.",
        "",
        "## Dependency Blockers",
        "",
    ]
    for row in blocker_deps:
        lines.append(f"- `{row['dependency']}`: route `{row['route']}`.")
    lines.extend(["", "## Checkpoint State", ""])
    for row in checkpoints:
        lines.append(f"- `{row['id']}`: ready {str(row['ready']).lower()}, acquisition `{row['acquisition_needed']}`.")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Next unit: `{acquisition['next_unit']}`.",
            f"- First smoke variant: `{runtime['first_smoke_variant']['id']}`.",
            "- Runtime launched in E005-M22: false.",
            "",
            "## Claim Boundary",
            "",
            "- E005-M22 is runtime planning/preflight evidence only.",
            "- No `ConceptGraphs` performance claim is supported yet.",
            "- `ConceptGraphs` object-map baseline comparison requires repo/checkpoint acquisition, Docker build, one-scan runtime smoke, and object-map schema inspection.",
            "- No final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claim is supported yet.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    source = read_json(M20_DIR / "source_audit.json")
    staged = staged_probe()
    docker = docker_probe()
    gpu = gpu_probe()
    conceptgraphs_git = git_head(CONCEPTGRAPHS_REPO)
    gsa_git = git_head(GSA_REPO)
    checkpoints = checkpoint_rows()
    deps = dependency_rows(source)
    acquisition = acquisition_plan()
    runtime = runtime_contract()
    sam_ready = next(row for row in checkpoints if row["id"] == "sam_vit_h_4b8939")["ready"]
    grounding_ready = next(row for row in checkpoints if row["id"] == "groundingdino_swint_ogc")["ready"]
    status = "e005_m22_conceptgraphs_runtime_preflight_ready_with_acquisition_required"
    if not staged["staged_root_exists"] or staged["ready_scan_count"] != staged["selected_scan_count"]:
        status = "e005_m22_conceptgraphs_runtime_preflight_blocked_by_staging"
    elif not docker["docker_ready"] or not docker["nvidia_runtime_detected"] or not gpu["nvidia_smi_ready"]:
        status = "e005_m22_conceptgraphs_runtime_preflight_blocked_by_runtime_host"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "conceptgraphs_expected_commit": CONCEPTGRAPHS_COMMIT,
        "conceptgraphs_repo_present": conceptgraphs_git["exists"],
        "conceptgraphs_repo_head": conceptgraphs_git["head"],
        "gsa_expected_commit": GSA_COMMIT,
        "gsa_repo_present": gsa_git["exists"],
        "gsa_repo_head": gsa_git["head"],
        "docker_ready": docker["docker_ready"],
        "docker_server_version": docker["server_version"],
        "nvidia_runtime_detected": docker["nvidia_runtime_detected"],
        "conceptgraphs_image_exists": docker["conceptgraphs_image_exists"],
        "gpu_ready": gpu["nvidia_smi_ready"],
        "gpu_name": gpu.get("name", ""),
        "gpu_total_mib": gpu.get("memory_total_mib"),
        "gpu_free_mib": gpu.get("memory_free_mib"),
        "staged_root": staged["staged_root"],
        "staged_config": staged["staged_config"],
        "selected_scan_count": staged["selected_scan_count"],
        "ready_scan_count": staged["ready_scan_count"],
        "smoke_scan_id": SMOKE_SCAN_ID,
        "sam_checkpoint_ready": sam_ready,
        "groundingdino_checkpoint_ready": grounding_ready,
        "runtime_launched": False,
        "next_recommended_unit": acquisition["next_unit"],
    }
    decision = {
        "status": status,
        "decision": "launch_repo_checkpoint_acquisition_before_docker_build",
        "selected_smoke_variant": runtime["first_smoke_variant"]["id"],
        "next_action": acquisition["next_unit"],
        "claim_boundary": [
            "No ConceptGraphs performance claim from E005-M22.",
            "No object-map comparison until runtime pkl.gz exists and schema is inspected.",
            "No full-resolution open-vocabulary robustness claim from depth-aligned smoke.",
        ],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "host_preflight.json", {"docker": docker, "gpu": gpu, "staged": staged})
    write_json(OUT_DIR / "acquisition_plan.json", acquisition)
    write_json(OUT_DIR / "runtime_contract.json", runtime)
    write_json(OUT_DIR / "decision.json", decision)
    write_jsonl(OUT_DIR / "dependency_rows.jsonl", deps)
    write_jsonl(OUT_DIR / "checkpoint_rows.jsonl", checkpoints)
    write_text(OUT_DIR / "report.md", build_report(coverage, deps, checkpoints, acquisition, runtime))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
