#!/usr/bin/env python3
"""Verify OpenMask3D checkpoint cache/resource readiness for E003-M67."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M67_openmask3d_checkpoint_env_route_v0"
DEFAULT_CACHE_DIR = REPO_ROOT / "local_dataset" / "checkpoints" / "openmask3d"
DEFAULT_OPENMASK3D_REPO = EXPERIMENT_ROOT / "external" / "openmask3d"
VERIFY_VERSION = "e003_m67_openmask3d_checkpoint_verifier_v0"


CHECKPOINTS = [
    {
        "cache_filename": "openmask3d_arbitrary_scene_model.ckpt",
        "key": "openmask3d_mask_arbitrary_scene",
        "min_size_bytes": 50_000_000,
        "resource_filename": "openmask3d_arbitrary_scene_model.ckpt",
    },
    {
        "cache_filename": "sam_vit_h_4b8939.pth",
        "key": "sam_vit_h",
        "min_size_bytes": 2_000_000_000,
        "resource_filename": "sam_vit_h_4b8939.pth",
    },
]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def file_status(path: Path, min_size_bytes: int) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "exists": exists,
        "min_size_bytes": min_size_bytes,
        "path": str(path),
        "ready": exists and size >= min_size_bytes,
        "size_bytes": size,
    }


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M67 OpenMask3D Checkpoint Verifier",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Cache dir: `{coverage['cache_dir']}`",
            f"- OpenMask3D repo dir: `{coverage['openmask3d_repo_dir']}`",
            f"- Cache ready: {coverage['cache_ready_count']} / {coverage['checkpoint_count']}",
            f"- Resource ready: {coverage['resource_ready_count']} / {coverage['checkpoint_count']}",
            f"- Checkpoints ready: {coverage['checkpoints_ready']}",
            "",
            "## 논문 주장",
            "",
            "- This verifier only checks checkpoint availability.",
            "- It does not support model-output or search-improvement claims.",
            "",
            "## 에이전트 추론",
            "",
            "- If cache is ready but resource links are missing, the next action is symlink/copy repair.",
            "- If cache is missing, launch the recorded checkpoint download job in the next unit.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for verifier execution.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, type=Path)
    parser.add_argument("--openmask3d-repo", default=DEFAULT_OPENMASK3D_REPO, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    args = parser.parse_args()

    resources_dir = args.openmask3d_repo / "resources"
    rows = []
    cache_ready_count = 0
    resource_ready_count = 0
    for checkpoint in CHECKPOINTS:
        cache_path = args.cache_dir / checkpoint["cache_filename"]
        resource_path = resources_dir / checkpoint["resource_filename"]
        cache = file_status(cache_path, int(checkpoint["min_size_bytes"]))
        resource = file_status(resource_path, int(checkpoint["min_size_bytes"]))
        cache_ready_count += int(cache["ready"])
        resource_ready_count += int(resource["ready"])
        rows.append(
            {
                "cache": cache,
                "key": checkpoint["key"],
                "resource": resource,
            }
        )

    checkpoints_ready = cache_ready_count == len(CHECKPOINTS) and resource_ready_count == len(CHECKPOINTS)
    coverage = {
        "cache_dir": str(args.cache_dir),
        "cache_ready_count": cache_ready_count,
        "checkpoint_count": len(CHECKPOINTS),
        "checkpoint_rows": rows,
        "checkpoints_ready": checkpoints_ready,
        "openmask3d_repo_dir": str(args.openmask3d_repo),
        "resource_ready_count": resource_ready_count,
        "status": "openmask3d_checkpoints_ready" if checkpoints_ready else "openmask3d_checkpoints_missing",
        "verify_version": VERIFY_VERSION,
    }
    write_json(args.out_dir / "checkpoint_verification.json", coverage)
    (args.out_dir / "checkpoint_verification.md").write_text(build_report(coverage), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if checkpoints_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
