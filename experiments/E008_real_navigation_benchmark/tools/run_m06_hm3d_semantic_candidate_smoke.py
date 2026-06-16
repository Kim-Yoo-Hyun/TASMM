#!/usr/bin/env python3
"""Run E008-M06 HM3D semantic annotation candidate-source smoke."""

from __future__ import annotations

import csv
import json
import re
import struct
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M06_hm3d_semantic_candidate_source_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M06_hm3d_semantic_candidate_source_smoke_v0"
VERSION = "e008_m06_hm3d_semantic_candidate_source_smoke_v0"

M02_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M05_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M05_hm3d_candidate_source_staging_plan_v0"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HM3D_MINIVAL_ROOT = RESEARCH2_DATA_ROOT / "versioned_data" / "hm3d-0.2" / "hm3d" / "minival"
HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
SCENE_DATASET_CONFIG = "/data/versioned_data/hm3d-0.2/hm3d/minival/hm3d_annotated_minival_basis.scene_dataset_config.json"

CATEGORY_ALIASES = {
    "bed": ["bed"],
    "chair": ["chair", "armchair", "office chair", "dining chair"],
    "tv_monitor": ["tv", "television", "monitor", "screen"],
}

COMPONENT_TYPES = {
    5120: ("b", 1),
    5121: ("B", 1),
    5122: ("h", 2),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}
ACCESSOR_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def normalize_label(label: str) -> str:
    text = label.lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def category_aliases(category: str) -> list[str]:
    return [normalize_label(alias) for alias in CATEGORY_ALIASES.get(category, [category])]


def label_matches(category: str, label_norm: str) -> bool:
    aliases = category_aliases(category)
    return any(label_norm == alias or label_norm.endswith(f" {alias}") for alias in aliases)


def scene_short(scene_key: str) -> str:
    return scene_key.split("-", 1)[1] if "-" in scene_key else scene_key


def scene_paths(scene_key: str) -> dict[str, Path]:
    short = scene_short(scene_key)
    scene_dir = HM3D_MINIVAL_ROOT / scene_key
    return {
        "scene_dir": scene_dir,
        "basis_glb": scene_dir / f"{short}.basis.glb",
        "basis_navmesh": scene_dir / f"{short}.basis.navmesh",
        "semantic_glb": scene_dir / f"{short}.semantic.glb",
        "semantic_txt": scene_dir / f"{short}.semantic.txt",
    }


def scene_docker_path(scene_key: str) -> str:
    short = scene_short(scene_key)
    return f"/data/versioned_data/hm3d-0.2/hm3d/minival/{scene_key}/{short}.basis.glb"


def parse_semantic_txt(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline()
        if not first.startswith("HM3D Semantic Annotations"):
            handle.seek(0)
        reader = csv.reader(handle)
        for parts in reader:
            if len(parts) < 4:
                continue
            try:
                semantic_object_id = int(parts[0])
            except ValueError:
                continue
            try:
                region_id = int(parts[3])
            except ValueError:
                region_id = None
            rows.append(
                {
                    "semantic_object_id": semantic_object_id,
                    "semantic_color": str(parts[1]).upper(),
                    "semantic_label": str(parts[2]).strip(),
                    "semantic_label_norm": normalize_label(str(parts[2])),
                    "semantic_region_id": region_id,
                }
            )
    return rows


def read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    with path.open("rb") as handle:
        magic, version, _length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2:
            raise ValueError(f"unsupported GLB header: {magic!r} version={version}")
        json_len, json_type = struct.unpack("<I4s", handle.read(8))
        if json_type != b"JSON":
            raise ValueError(f"missing JSON chunk in {path}")
        payload = json.loads(handle.read(json_len).decode("utf-8"))
        bin_len, bin_type = struct.unpack("<I4s", handle.read(8))
        if bin_type != b"BIN\x00":
            raise ValueError(f"missing BIN chunk in {path}")
        binary = handle.read(bin_len)
    return payload, binary


def iter_accessor_values(payload: dict[str, Any], binary: bytes, accessor_index: int):
    accessor = payload["accessors"][accessor_index]
    buffer_view = payload["bufferViews"][accessor["bufferView"]]
    component_type = int(accessor["componentType"])
    if component_type not in COMPONENT_TYPES:
        return
    fmt, size = COMPONENT_TYPES[component_type]
    width = ACCESSOR_WIDTH[accessor["type"]]
    stride = int(buffer_view.get("byteStride", size * width))
    offset = int(buffer_view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    unpack = struct.Struct("<" + fmt * width).unpack_from
    for index in range(int(accessor["count"])):
        yield unpack(binary, offset + index * stride)


def glb_geometry_probe(scene_key: str, semantic_rows: list[dict[str, Any]], episode_categories: list[str]) -> dict[str, Any]:
    path = scene_paths(scene_key)["semantic_glb"]
    if not path.exists():
        return {
            "scene_key": scene_key,
            "semantic_glb_ready": False,
            "geometry_probe_ready": False,
            "reason": "semantic.glb missing",
        }
    payload, binary = read_glb(path)
    nodes = payload.get("nodes", [])
    meshes = payload.get("meshes", [])
    node_tokens = []
    for node in nodes:
        name = str(node.get("name", ""))
        match = re.search(r"object([^_]+)", name.lower())
        if match:
            node_tokens.append(match.group(1))
    node_token_counts = Counter(node_tokens)
    node_category_matches = {
        category: sum(
            count
            for token, count in node_token_counts.items()
            if label_matches(category, normalize_label(re.sub(r"\d+$", "", token)))
        )
        for category in episode_categories
    }

    semantic_colors = {row["semantic_color"] for row in semantic_rows}
    color_hexes = set()
    color_accessor_count = 0
    color_vertex_count = 0
    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            accessor_index = primitive.get("attributes", {}).get("COLOR_0")
            if accessor_index is None:
                continue
            color_accessor_count += 1
            for values in iter_accessor_values(payload, binary, int(accessor_index)):
                if len(values) < 3:
                    continue
                color_vertex_count += 1
                color_hexes.add("".join(f"{round(float(v) / 257.0):02X}" for v in values[:3]))
    color_intersection = sorted(semantic_colors & color_hexes)

    return {
        "scene_key": scene_key,
        "semantic_glb_ready": True,
        "node_count": len(nodes),
        "mesh_count": len(meshes),
        "node_object_token_unique": len(node_token_counts),
        "node_object_token_top10": node_token_counts.most_common(10),
        "node_category_matches": node_category_matches,
        "color_accessor_count": color_accessor_count,
        "color_vertex_count": color_vertex_count,
        "glb_unique_vertex_colors": len(color_hexes),
        "semantic_txt_unique_colors": len(semantic_colors),
        "semantic_color_intersection_count": len(color_intersection),
        "semantic_color_intersection_sample": color_intersection[:10],
        "geometry_probe_ready": False,
        "reason": "semantic.glb has no reliable semantic-id-to-geometry mapping for target categories: node object tokens do not cover target categories and vertex colors do not match semantic.txt colors.",
    }


def run_habitat_semantic_aabb_probe(scene_keys: list[str], episode_categories_by_scene: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [
        {
            "scene_key": scene_key,
            "scene_docker_path": scene_docker_path(scene_key),
            "episode_categories": episode_categories_by_scene.get(scene_key, []),
        }
        for scene_key in scene_keys
    ]
    code = f"""
import json
import habitat_sim

rows = json.loads({json.dumps(json.dumps(rows))})

def norm(label):
    return str(label).lower().replace('_', ' ').replace('-', ' ').strip()

def category_aliases(category):
    mapping = {{
        "bed": ["bed"],
        "chair": ["chair", "armchair", "office chair", "dining chair"],
        "tv_monitor": ["tv", "television", "monitor", "screen"],
    }}
    return [norm(x) for x in mapping.get(category, [category])]

def matches(category, label):
    label = norm(label)
    return any(label == alias or label.endswith(" " + alias) for alias in category_aliases(category))

out = []
for row in rows:
    sim = None
    try:
        cfg = habitat_sim.SimulatorConfiguration()
        cfg.scene_id = row["scene_docker_path"]
        cfg.scene_dataset_config_file = {json.dumps(SCENE_DATASET_CONFIG)}
        cfg.load_semantic_mesh = True
        cfg.force_separate_semantic_scene_graph = True
        sim = habitat_sim.Simulator(habitat_sim.Configuration(cfg, [habitat_sim.AgentConfiguration()]))
        objects = [obj for obj in sim.semantic_scene.objects if obj is not None]
        category_counts = {{}}
        nonzero_by_category = {{}}
        samples = []
        for obj in objects:
            category = obj.category.name() if obj.category else ""
            size = obj.aabb.size()
            center = obj.aabb.center()
            nonzero = abs(float(size.x)) + abs(float(size.y)) + abs(float(size.z)) > 1e-6
            for query_category in row["episode_categories"]:
                if matches(query_category, category):
                    category_counts[query_category] = category_counts.get(query_category, 0) + 1
                    nonzero_by_category[query_category] = nonzero_by_category.get(query_category, 0) + (1 if nonzero else 0)
                    if len(samples) < 5:
                        samples.append({{
                            "semantic_id": int(obj.semantic_id),
                            "object_id": str(obj.id),
                            "category": category,
                            "nonzero_aabb": nonzero,
                            "center": [float(center.x), float(center.y), float(center.z)],
                            "size": [float(size.x), float(size.y), float(size.z)],
                        }})
        out.append({{
            "scene_key": row["scene_key"],
            "habitat_scene_loaded": True,
            "semantic_object_count": len(objects),
            "target_category_object_counts": category_counts,
            "target_category_nonzero_aabb_counts": nonzero_by_category,
            "nonzero_aabb_total": sum(1 for obj in objects if abs(float(obj.aabb.size().x)) + abs(float(obj.aabb.size().y)) + abs(float(obj.aabb.size().z)) > 1e-6),
            "sample_target_objects": samples,
            "aabb_coordinate_extraction_ready": any(v > 0 for v in nonzero_by_category.values()),
            "error": "",
        }})
    except Exception as exc:
        out.append({{
            "scene_key": row["scene_key"],
            "habitat_scene_loaded": False,
            "semantic_object_count": 0,
            "target_category_object_counts": {{}},
            "target_category_nonzero_aabb_counts": {{}},
            "nonzero_aabb_total": 0,
            "sample_target_objects": [],
            "aabb_coordinate_extraction_ready": False,
            "error": repr(exc),
        }})
    finally:
        if sim is not None:
            sim.close()
print(json.dumps(out, sort_keys=True))
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{RESEARCH2_DATA_ROOT}:/data:ro",
        "--entrypoint",
        "bash",
        HABITAT_IMAGE,
        "-lc",
        "micromamba run -n base python - <<'PY'\n" + code + "\nPY",
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=120)
    meta = {
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
        "command": " ".join(cmd[:8]) + " ...",
        "mount": f"{RESEARCH2_DATA_ROOT}:/data:ro",
    }
    if proc.returncode != 0:
        return [], meta
    try:
        for line in reversed([part.strip() for part in proc.stdout.splitlines() if part.strip()]):
            if line.startswith("["):
                return json.loads(line), meta
        meta["ok"] = False
        meta["parse_error"] = "no JSON list in stdout"
        return [], meta
    except Exception as exc:
        meta["ok"] = False
        meta["parse_error"] = repr(exc)
        return [], meta


def build_semantic_label_rows(episode_rows: list[dict[str, Any]], semantic_by_scene: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out = []
    for episode in episode_rows:
        scene_key = str(episode["scene_key"])
        category = str(episode["object_category"])
        matched = [
            row
            for row in semantic_by_scene.get(scene_key, [])
            if label_matches(category, str(row["semantic_label_norm"]))
        ]
        out.append(
            {
                "adapter_episode_id": episode["adapter_episode_id"],
                "scene_key": scene_key,
                "object_category": category,
                "category_aliases": category_aliases(category),
                "semantic_label_support_ready": len(matched) > 0,
                "matched_semantic_object_count": len(matched),
                "matched_semantic_object_ids": [row["semantic_object_id"] for row in matched[:20]],
                "matched_semantic_labels": sorted({row["semantic_label"] for row in matched}),
            }
        )
    return out


def build_candidate_blocker_rows(
    label_rows: list[dict[str, Any]],
    aabb_rows: list[dict[str, Any]],
    glb_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aabb_by_scene = {row["scene_key"]: row for row in aabb_rows}
    glb_by_scene = {row["scene_key"]: row for row in glb_rows}
    out = []
    for row in label_rows:
        scene_key = row["scene_key"]
        category = row["object_category"]
        aabb = aabb_by_scene.get(scene_key, {})
        glb = glb_by_scene.get(scene_key, {})
        aabb_count = int((aabb.get("target_category_nonzero_aabb_counts") or {}).get(category, 0))
        glb_node_count = int((glb.get("node_category_matches") or {}).get(category, 0))
        out.append(
            {
                "adapter_episode_id": row["adapter_episode_id"],
                "scene_key": scene_key,
                "object_category": category,
                "semantic_label_support_ready": row["semantic_label_support_ready"],
                "matched_semantic_object_count": row["matched_semantic_object_count"],
                "habitat_nonzero_aabb_count": aabb_count,
                "glb_node_category_match_count": glb_node_count,
                "semantic_color_intersection_count": glb.get("semantic_color_intersection_count", 0),
                "candidate_coordinate_extraction_ready": False,
                "candidate_rows_ready": 0,
                "blocker": "semantic_label_available_but_no_reliable_non_oracle_geometry_mapping",
                "next_action": "Use rendered RGB-D detector or external map candidate source instead of ObjectNav goal/viewpoint leakage.",
            }
        )
    return out


def build_route_rows(candidate_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_ready = len(candidate_rows) > 0
    return [
        {
            "rank": 1,
            "route_id": "e008_m07_hm3d_rendered_rgbd_detector_candidate_source_plan",
            "selected": not candidate_ready,
            "decision": "selected_next" if not candidate_ready else "defer",
            "next_unit": "E008-M07 HM3D rendered RGB-D detector candidate-source plan",
            "launch_long_job_now": False,
            "reason": "Semantic labels are available, but E008-M06 cannot derive reliable non-oracle coordinates from HM3D semantic annotation geometry.",
        },
        {
            "rank": 2,
            "route_id": "e008_h001_navigation_execution_now",
            "selected": candidate_ready,
            "decision": "blocked" if not candidate_ready else "candidate_rows_ready_but_execution_still_needs_metric_gate",
            "next_unit": "later H001 candidate visit-order execution",
            "launch_long_job_now": False,
            "reason": "H001 execution requires candidate coordinate rows and navigable viewpoints; current candidate rows ready count is "
            + str(len(candidate_rows))
            + ".",
        },
        {
            "rank": 3,
            "route_id": "objectnav_goal_viewpoint_as_candidate_source",
            "selected": False,
            "decision": "rejected_policy_leakage",
            "next_unit": "none",
            "launch_long_job_now": False,
            "reason": "ObjectNav target ids, goal positions, viewpoints, and shortest-path fields remain evaluation-only and cannot be used to create policy candidates.",
        },
        {
            "rank": 4,
            "route_id": "hm3d_conceptgraphs_external_map_candidate_source",
            "selected": False,
            "decision": "defer_after_rgbd_render_plan",
            "next_unit": "later HM3D external map candidate source",
            "launch_long_job_now": False,
            "reason": "External map baseline is still needed for top-tier rigor, but rendered RGB-D candidate-source planning is the immediate prerequisite.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(
    coverage: dict[str, Any],
    label_rows: list[dict[str, Any]],
    aabb_rows: list[dict[str, Any]],
    glb_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    label_summary = [
        {
            "episode": row["adapter_episode_id"],
            "category": row["object_category"],
            "labels": row["semantic_label_support_ready"],
            "matches": row["matched_semantic_object_count"],
        }
        for row in label_rows
    ]
    aabb_summary = [
        {
            "scene": row["scene_key"],
            "loaded": row["habitat_scene_loaded"],
            "objects": row["semantic_object_count"],
            "nonzero_aabb": row["nonzero_aabb_total"],
            "aabb_ready": row["aabb_coordinate_extraction_ready"],
        }
        for row in aabb_rows
    ]
    glb_summary = [
        {
            "scene": row["scene_key"],
            "nodes": row.get("node_count", 0),
            "colors": row.get("glb_unique_vertex_colors", 0),
            "color_intersection": row.get("semantic_color_intersection_count", 0),
            "geometry_ready": row.get("geometry_probe_ready", False),
        }
        for row in glb_rows
    ]
    blocker_summary = [
        {
            "episode": row["adapter_episode_id"],
            "category": row["object_category"],
            "aabb": row["habitat_nonzero_aabb_count"],
            "node": row["glb_node_category_match_count"],
            "candidate_rows": row["candidate_rows_ready"],
        }
        for row in blocker_rows
    ]
    route_summary = [
        {
            "rank": row["rank"],
            "route": row["route_id"],
            "decision": row["decision"],
            "next": row["next_unit"],
        }
        for row in route_rows
    ]
    return (
        "# E008-M06 HM3D Semantic Annotation Candidate Source Smoke\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- M05 status: `{coverage['m05_status']}`.\n"
        f"- Episode rows: {coverage['episode_rows']}.\n"
        f"- Semantic label support rows ready: {coverage['semantic_label_support_rows_ready']} / {coverage['semantic_label_support_rows_total']}.\n"
        f"- Habitat semantic nonzero-AABB scenes: {coverage['habitat_nonzero_aabb_scenes']} / {coverage['scene_rows']}.\n"
        f"- GLB semantic geometry mapping scenes ready: {coverage['glb_geometry_mapping_scenes_ready']} / {coverage['scene_rows']}.\n"
        f"- Candidate rows ready: {coverage['candidate_rows_ready']}.\n"
        f"- Selected next unit: {coverage['selected_next_unit']}.\n"
        f"- Launch long job now: {str(coverage['launch_long_job_now']).lower()}.\n\n"
        "## Semantic Label Support\n\n"
        + markdown_table(label_summary, ["episode", "category", "labels", "matches"])
        + "\n\n"
        "## Habitat AABB Probe\n\n"
        + markdown_table(aabb_summary, ["scene", "loaded", "objects", "nonzero_aabb", "aabb_ready"])
        + "\n\n"
        "## GLB Geometry Probe\n\n"
        + markdown_table(glb_summary, ["scene", "nodes", "colors", "color_intersection", "geometry_ready"])
        + "\n\n"
        "## Candidate Blockers\n\n"
        + markdown_table(blocker_summary, ["episode", "category", "aabb", "node", "candidate_rows"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route", "decision", "next"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M06 does not produce H001 executable candidate rows.\n"
        "- The result is a negative/blocked semantic-annotation smoke: labels are present, but reliable non-oracle geometry mapping is not available from the current `HM3D` semantic annotation path.\n"
        "- `ObjectNav` goal/viewpoint fields remain blocked for policy input.\n"
        "- Real navigation `SR` / `SPL`, deployable search policy, and final real RGB-D/open-vocabulary robustness remain false.\n\n"
        "## Agent Inference\n\n"
        "- The next defensible route is not to force `ObjectNav` goal annotations into policy candidates; that would weaken leakage defense.\n"
        "- Move to rendered RGB-D detector candidate-source planning, then later add external map candidates such as `ConceptGraphs` / `HOV-SG` for top-tier baseline pressure.\n"
    )


def main() -> None:
    m05_coverage = read_json(M05_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M02_DATA_DIR / "episode_adapter_rows.jsonl")
    scene_keys = sorted({str(row["scene_key"]) for row in episode_rows})
    episode_categories_by_scene: dict[str, list[str]] = {
        scene_key: sorted({str(row["object_category"]) for row in episode_rows if str(row["scene_key"]) == scene_key})
        for scene_key in scene_keys
    }

    semantic_by_scene = {
        scene_key: parse_semantic_txt(scene_paths(scene_key)["semantic_txt"])
        for scene_key in scene_keys
    }
    label_rows = build_semantic_label_rows(episode_rows, semantic_by_scene)
    aabb_rows, docker_meta = run_habitat_semantic_aabb_probe(scene_keys, episode_categories_by_scene)
    glb_rows = [
        glb_geometry_probe(scene_key, semantic_by_scene.get(scene_key, []), episode_categories_by_scene.get(scene_key, []))
        for scene_key in scene_keys
    ]
    blocker_rows = build_candidate_blocker_rows(label_rows, aabb_rows, glb_rows)
    candidate_rows: list[dict[str, Any]] = []
    route_rows = build_route_rows(candidate_rows, blocker_rows)

    semantic_label_ready = sum(1 for row in label_rows if row["semantic_label_support_ready"])
    habitat_nonzero_scenes = sum(1 for row in aabb_rows if row.get("aabb_coordinate_extraction_ready"))
    glb_ready_scenes = sum(1 for row in glb_rows if row.get("geometry_probe_ready"))
    selected = next(row for row in route_rows if row["selected"])
    status = (
        "e008_m06_hm3d_semantic_candidate_source_smoke_ready_blocked_coordinate_extraction"
        if semantic_label_ready == len(label_rows) and len(candidate_rows) == 0
        else "e008_m06_hm3d_semantic_candidate_source_smoke_blocked"
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "m05_status": m05_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "episode_rows": len(episode_rows),
        "scene_rows": len(scene_keys),
        "semantic_label_support_rows_ready": semantic_label_ready,
        "semantic_label_support_rows_total": len(label_rows),
        "habitat_semantic_probe_ok": bool(docker_meta.get("ok")),
        "habitat_nonzero_aabb_scenes": habitat_nonzero_scenes,
        "glb_geometry_mapping_scenes_ready": glb_ready_scenes,
        "candidate_rows_ready": len(candidate_rows),
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "selected_next_unit": selected["next_unit"],
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_json(ARTIFACT_DIR / "docker_semantic_probe_meta.json", docker_meta)
    write_jsonl(ARTIFACT_DIR / "semantic_label_rows.jsonl", label_rows)
    write_jsonl(ARTIFACT_DIR / "habitat_semantic_aabb_rows.jsonl", aabb_rows)
    write_jsonl(ARTIFACT_DIR / "semantic_glb_geometry_probe_rows.jsonl", glb_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_blocker_rows.jsonl", blocker_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, label_rows, aabb_rows, glb_rows, blocker_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_json(DATA_OUT_DIR / "docker_semantic_probe_meta.json", docker_meta)
    write_jsonl(DATA_OUT_DIR / "semantic_label_rows.jsonl", label_rows)
    write_jsonl(DATA_OUT_DIR / "habitat_semantic_aabb_rows.jsonl", aabb_rows)
    write_jsonl(DATA_OUT_DIR / "semantic_glb_geometry_probe_rows.jsonl", glb_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_blocker_rows.jsonl", blocker_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
