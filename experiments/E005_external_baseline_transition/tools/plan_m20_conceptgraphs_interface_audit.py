#!/usr/bin/env python3
"""Audit ConceptGraphs as the E005 fallback external mapping baseline."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M20_conceptgraphs_interface_audit_v0"
DUALMAP_STAGE_ROOT = ROOT / "local_dataset" / "DualMap_staged" / "3rscan_scannet_exported" / "scannet" / "exported"
CONCEPTGRAPHS_STAGE_ROOT = ROOT / "local_dataset" / "ConceptGraphs_staged" / "3rscan_depth_aligned_scannet"

GITHUB_API = "https://api.github.com/repos/concept-graphs/concept-graphs"
RAW = "https://raw.githubusercontent.com/concept-graphs/concept-graphs/main"
OFFICIAL_REPO = "https://github.com/concept-graphs/concept-graphs"
PROJECT_PAGE = "https://concept-graphs.github.io/"
PAPER_URL = "https://concept-graphs.github.io/assets/pdf/2023-ConceptGraphs.pdf"
ARXIV_URL = "https://arxiv.org/abs/2309.16650"


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


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def fetch_text(url: str, timeout: int = 30, max_bytes: int = 300_000) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read(max_bytes).decode("utf-8", errors="replace")


def safe_fetch_text(url: str) -> tuple[str, str]:
    try:
        return fetch_text(url), ""
    except Exception as exc:  # noqa: BLE001 - audit should record network/source failures.
        return "", str(exc)


def image_size(path: Path) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            return {"width": image.size[0], "height": image.size[1], "mode": image.mode}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def count_files(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


def local_scan_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scan_dir in sorted(p for p in DUALMAP_STAGE_ROOT.iterdir() if p.is_dir()) if DUALMAP_STAGE_ROOT.exists() else []:
        color_files = sorted((scan_dir / "color").glob("*.jpg"))
        depth_files = sorted((scan_dir / "depth").glob("*.png"))
        pose_files = sorted((scan_dir / "pose").glob("*.txt"))
        intrinsic_depth = scan_dir / "intrinsic" / "intrinsic_depth.txt"
        rows.append(
            {
                "scan_id": scan_dir.name,
                "color_jpg_count": len(color_files),
                "depth_png_count": len(depth_files),
                "pose_txt_count": len(pose_files),
                "intrinsic_depth_exists": intrinsic_depth.exists(),
                "intrinsic_color_exists": (scan_dir / "intrinsic" / "intrinsic_color.txt").exists(),
                "sample_color_size": image_size(color_files[0]) if color_files else {},
                "sample_depth_size": image_size(depth_files[0]) if depth_files else {},
                "conceptgraphs_direct_scannet_ready": bool(
                    color_files and depth_files and pose_files and (scan_dir / "intrinsic" / "intrinsic_color.txt").exists()
                ),
            }
        )
    return rows


def source_audit() -> dict[str, Any]:
    repo = fetch_json(GITHUB_API)
    branch = repo.get("default_branch", "main")
    ref = fetch_json(f"https://api.github.com/repos/concept-graphs/concept-graphs/git/ref/heads/{branch}")
    readme, readme_error = safe_fetch_text(f"{RAW}/README.md")
    license_text, license_error = safe_fetch_text(f"{RAW}/LICENSE")
    environment_text, environment_error = safe_fetch_text(f"{RAW}/environment.yml")
    scannet_config, scannet_error = safe_fetch_text(f"{RAW}/conceptgraph/dataset/dataconfigs/scannet/base.yaml")
    datasets_common, dataset_error = safe_fetch_text(f"{RAW}/conceptgraph/dataset/datasets_common.py")
    mapping_cfg, mapping_cfg_error = safe_fetch_text(f"{RAW}/conceptgraph/configs/slam_pipeline/base.yaml")
    mapping_script, mapping_script_error = safe_fetch_text(f"{RAW}/conceptgraph/slam/cfslam_pipeline_batch.py")
    detection_script, detection_script_error = safe_fetch_text(f"{RAW}/conceptgraph/scripts/generate_gsa_results.py")
    scenegraph_script, scenegraph_error = safe_fetch_text(f"{RAW}/conceptgraph/scenegraph/build_scenegraph_cfslam.py")

    output_patterns = {
        "detections": sorted(set(re.findall(r"gsa_detections_[A-Za-z0-9_${}_\\-]+", detection_script))),
        "mapping": sorted(set(re.findall(r"pcd_saves[^\\n\"']*|full_pcd_[^\\n\"']+", mapping_script + readme))),
        "scenegraph": sorted(set(re.findall(r"scene_map_cfslam_pruned\\.pkl\\.gz|cfslam_object_relations\\.json", scenegraph_script + readme))),
    }
    return {
        "official_repo": OFFICIAL_REPO,
        "project_page": PROJECT_PAGE,
        "paper_url": PAPER_URL,
        "arxiv_url": ARXIV_URL,
        "api_default_branch": repo.get("default_branch"),
        "api_license": repo.get("license", {}),
        "api_pushed_at": repo.get("pushed_at"),
        "api_updated_at": repo.get("updated_at"),
        "api_size": repo.get("size"),
        "api_stargazers_count": repo.get("stargazers_count"),
        "head_commit": ref.get("object", {}).get("sha"),
        "source_errors": {
            "readme": readme_error,
            "license": license_error,
            "environment": environment_error,
            "scannet_config": scannet_error,
            "datasets_common": dataset_error,
            "mapping_cfg": mapping_cfg_error,
            "mapping_script": mapping_script_error,
            "detection_script": detection_script_error,
            "scenegraph_script": scenegraph_error,
        },
        "readme_signals": {
            "takes_posed_rgbd": "posed RGB-D images" in readme,
            "replica_example": "Replica" in readme,
            "other_dataset_loader_note": "write your own dataloader" in readme,
            "outputs_pkl_gz": "pkl.gz" in readme,
            "scenegraph_generation": "build-scenegraph" in readme,
            "python_310": "Python 3.10" in readme or "python=3.10" in readme,
            "gsa_required": "Grounded-Segment-Anything" in readme or "GSA_PATH" in readme,
        },
        "license_text_first_line": license_text.splitlines()[0] if license_text else "",
        "environment_signals": {
            "pytorch_2_0_1": "pytorch==2.0.1" in readme or "pytorch=2.0.1" in environment_text,
            "cuda_11_8": "CUDA 11.8" in readme or "11.8" in environment_text,
            "pytorch3d": "pytorch3d" in readme.lower() or "pytorch3d" in environment_text.lower(),
            "faiss": "faiss" in readme.lower() or "faiss" in environment_text.lower(),
            "gradslam": "gradslam" in readme.lower(),
            "open_clip": "open_clip_torch" in readme,
            "ultralytics": "ultralytics" in readme or "YOLO" in detection_script,
            "llava": "LLaVA" in readme or "llava" in scenegraph_script.lower(),
        },
        "interface_signals": {
            "scannet_dataset_class": "class ScannetDataset" in datasets_common,
            "scannet_color_glob": 'color/*.jpg' in datasets_common,
            "scannet_depth_glob": 'depth/*.png' in datasets_common,
            "scannet_pose_glob": 'pose/*.txt' in datasets_common,
            "scannet_intrinsic_color": "intrinsic_color.txt" in datasets_common,
            "base_mapping_dataset_root": "dataset_root" in mapping_cfg,
            "base_mapping_scene_id": "scene_id" in mapping_cfg,
            "base_mapping_obj_min_detections": "obj_min_detections" in mapping_cfg,
            "generate_gsa_dataset_root_arg": "--dataset_root" in detection_script,
            "generate_gsa_scene_id_arg": "--scene_id" in detection_script,
            "cfslam_loads_detection_pkl_gz": ".pkl.gz" in mapping_script and "gsa_detections" in mapping_script,
            "scenegraph_loads_mapfile": "--mapfile" in scenegraph_script,
        },
        "scannet_base_config": scannet_config,
        "output_patterns": output_patterns,
        "raw_source_urls": {
            "README": f"{RAW}/README.md",
            "LICENSE": f"{RAW}/LICENSE",
            "scannet_config": f"{RAW}/conceptgraph/dataset/dataconfigs/scannet/base.yaml",
            "datasets_common": f"{RAW}/conceptgraph/dataset/datasets_common.py",
            "mapping_config": f"{RAW}/conceptgraph/configs/slam_pipeline/base.yaml",
            "detection_script": f"{RAW}/conceptgraph/scripts/generate_gsa_results.py",
            "mapping_script": f"{RAW}/conceptgraph/slam/cfslam_pipeline_batch.py",
            "scenegraph_script": f"{RAW}/conceptgraph/scenegraph/build_scenegraph_cfslam.py",
        },
    }


def adapter_contract(scan_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready_counts = {
        "selected_scans": len(scan_rows),
        "color_ready": sum(row["color_jpg_count"] > 0 for row in scan_rows),
        "depth_ready": sum(row["depth_png_count"] > 0 for row in scan_rows),
        "pose_ready": sum(row["pose_txt_count"] > 0 for row in scan_rows),
        "intrinsic_depth_ready": sum(row["intrinsic_depth_exists"] for row in scan_rows),
        "direct_intrinsic_color_ready": sum(row["intrinsic_color_exists"] for row in scan_rows),
    }
    return {
        "adapter_id": "conceptgraphs_3rscan_depth_aligned_scannet_v0",
        "status": "adapter_materialization_required",
        "source_stage_root": str(DUALMAP_STAGE_ROOT),
        "target_stage_root": str(CONCEPTGRAPHS_STAGE_ROOT),
        "selected_scan_count": len(scan_rows),
        "ready_counts": ready_counts,
        "recommended_dataset_root": str(CONCEPTGRAPHS_STAGE_ROOT),
        "recommended_dataset_config": str(CONCEPTGRAPHS_STAGE_ROOT / "config" / "conceptgraphs_3rscan_depth_aligned_scannet.yaml"),
        "required_layout_per_scan": [
            "color/*.jpg",
            "depth/*.png",
            "pose/*.txt",
            "intrinsic/intrinsic_color.txt",
        ],
        "materialization_policy": [
            "Create a separate ConceptGraphs staging root; do not mutate DualMap staging outputs.",
            "Resize or generate depth-aligned color JPGs at 224x172 for the initial smoke so GSA masks and mapping tensors share resolution.",
            "Copy intrinsic_depth.txt to intrinsic/intrinsic_color.txt only for the depth-aligned smoke layout.",
            "Use dataset_root=<ConceptGraphs_stage_root> and scene_id=<scan_id> with the ConceptGraphs ScannetDataset route.",
        ],
        "blocked_claims": [
            "No ConceptGraphs performance claim before object pkl.gz output exists.",
            "No full-resolution open-vocabulary robustness claim from depth-aligned smoke.",
            "No real navigation SR/SPL claim.",
        ],
        "next_smoke_expected_outputs": [
            "<stage_root>/<scan_id>/gsa_detections_<variant>/*.pkl.gz",
            "<stage_root>/<scan_id>/pcd_saves/full_pcd_<variant>_<suffix>.pkl.gz",
            "<stage_root>/<scan_id>/pcd_saves/full_pcd_<variant>_<suffix>_post.pkl.gz",
        ],
    }


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route": "conceptgraphs_depth_aligned_scannet_smoke",
            "selected": True,
            "why": "Current 3RScan staged scans already have color/depth/pose; ConceptGraphs ScannetDataset only needs a compatible root, intrinsic_color.txt, and resolution alignment.",
            "risk": "Depth-aligned color smoke is not final full-resolution performance evidence.",
        },
        {
            "rank": 2,
            "route": "conceptgraphs_custom_3rscan_dataset_class",
            "selected": False,
            "why": "Cleaner handling of different color/depth resolutions, but requires source patching before proving baseline feasibility.",
            "risk": "More implementation burden and harder to call faithful official baseline.",
        },
        {
            "rank": 3,
            "route": "dualmap_lower_stable_num_schema_smoke",
            "selected": False,
            "why": "Can test DualMap object serialization, but is not faithful baseline performance.",
            "risk": "Distracts from external baseline comparison.",
        },
    ]


def build_report(coverage: dict[str, Any], source: dict[str, Any], contract: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M20 ConceptGraphs Source/Interface Audit",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Official repo: `{source['official_repo']}`.",
        f"- Default branch: `{source['api_default_branch']}`.",
        f"- License: `{source['api_license'].get('spdx_id', 'unknown')}`.",
        f"- Repository pushed at: `{source['api_pushed_at']}`.",
        f"- Local staged scans audited: {coverage['selected_scan_count']}.",
        f"- Local direct ConceptGraphs-ready scans: {coverage['direct_conceptgraphs_ready_count']} / {coverage['selected_scan_count']}.",
        f"- Adapter status: `{contract['status']}`.",
        "",
        "## Interface Summary",
        "",
        "- Input: posed RGB-D image sequence with dataset root, scene id, dataset config, color/depth/pose/intrinsic files.",
        "- Detection output: `gsa_detections_<variant>/*.pkl.gz` under each scene folder.",
        "- Mapping output: `pcd_saves/full_pcd_<variant>_<suffix>.pkl.gz` and postprocessed `_post.pkl.gz` object maps.",
        "- Scene graph output: `sg_cache/map/scene_map_cfslam_pruned.pkl.gz` and `cfslam_object_relations.json` after scenegraph construction.",
        "",
        "## Decision",
        "",
        "- Selected route: `conceptgraphs_depth_aligned_scannet_smoke`.",
        "- Next unit: `E005-M21 ConceptGraphs 3RScan staging materialization smoke`.",
        "- Do not mutate the existing `DualMap` staging root.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['route']}`: rank {row['rank']}, selected {str(row['selected']).lower()}; {row['why']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M20 is source/interface audit only, not a baseline result.",
            "- `ConceptGraphs` can become the external mapping baseline only after staging, runtime smoke, object-map schema inspection, and E004-compatible query adapter evaluation.",
            "- Full-resolution open-vocabulary robustness remains blocked by detector/runtime validation and heldout split requirements.",
            "",
            "## Sources",
            "",
            f"- {source['official_repo']}",
            f"- {source['project_page']}",
            f"- {source['arxiv_url']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    source = source_audit()
    scan_rows = local_scan_rows()
    contract = adapter_contract(scan_rows)
    rows = route_rows()
    direct_ready = sum(row["conceptgraphs_direct_scannet_ready"] for row in scan_rows)
    source_errors = {key: value for key, value in source["source_errors"].items() if value}
    status = "e005_m20_conceptgraphs_interface_audit_ready_with_adapter_required"
    if source_errors:
        status = "e005_m20_conceptgraphs_interface_audit_ready_with_source_warnings"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "official_repo": source["official_repo"],
        "default_branch": source["api_default_branch"],
        "license_spdx": source["api_license"].get("spdx_id"),
        "selected_scan_count": len(scan_rows),
        "direct_conceptgraphs_ready_count": direct_ready,
        "adapter_id": contract["adapter_id"],
        "adapter_status": contract["status"],
        "selected_route": "conceptgraphs_depth_aligned_scannet_smoke",
        "source_warning_count": len(source_errors),
        "next_recommended_unit": "E005-M21 ConceptGraphs 3RScan staging materialization smoke",
    }
    decision = {
        "status": coverage["status"],
        "decision": coverage["selected_route"],
        "next_action": coverage["next_recommended_unit"],
        "claim_boundary": [
            "No ConceptGraphs performance claim from E005-M20.",
            "Adapter materialization and runtime smoke are required before object-map comparison.",
            "Depth-aligned smoke is feasibility evidence, not final full-resolution robustness evidence.",
        ],
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "source_audit.json", source)
    write_json(OUT_DIR / "adapter_contract.json", contract)
    write_json(OUT_DIR / "decision.json", decision)
    write_jsonl(OUT_DIR / "local_scan_rows.jsonl", scan_rows)
    write_jsonl(OUT_DIR / "route_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", build_report(coverage, source, contract, rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
