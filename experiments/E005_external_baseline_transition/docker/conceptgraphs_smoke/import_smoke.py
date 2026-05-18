"""Import smoke for the ConceptGraphs external-baseline container."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


MODULES = [
    "torch",
    "torchvision",
    "faiss",
    "open3d",
    "open_clip",
    "pytorch3d",
    "gradslam",
    "conceptgraph",
    "conceptgraph.dataset.datasets_common",
    "conceptgraph.slam.slam_classes",
    "conceptgraph.slam.utils",
    "groundingdino.util.inference",
    "segment_anything",
    "ram.models",
]


def main() -> int:
    imported = {}
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        imported[module_name] = getattr(module, "__file__", "built-in")

    payload = {
        "status": "conceptgraphs_import_smoke_ok",
        "gsa_path": os.environ.get("GSA_PATH"),
        "cuda_home": os.environ.get("CUDA_HOME"),
        "modules": imported,
        "conceptgraphs_exists": Path("/workspace/concept-graphs").exists(),
        "gsa_exists": Path("/workspace/Grounded-Segment-Anything").exists(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
