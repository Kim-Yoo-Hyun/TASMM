#!/usr/bin/env python3
"""Plan E008-M05 HM3D candidate-source staging."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M05_hm3d_candidate_source_staging_plan_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M05_hm3d_candidate_source_staging_plan_v0"
VERSION = "e008_m05_hm3d_candidate_source_staging_plan_v0"

M02_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"

RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
HM3D_MINIVAL_ROOT = RESEARCH2_DATA_ROOT / "versioned_data" / "hm3d-0.2" / "hm3d" / "minival"

CATEGORY_ALIASES = {
    "bed": ["bed"],
    "chair": ["chair", "armchair", "office chair", "dining chair"],
    "tv_monitor": ["tv", "television", "monitor", "screen"],
}


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


def semantic_paths(scene_key: str) -> dict[str, Path]:
    scene_short = scene_key.split("-", 1)[1] if "-" in scene_key else scene_key
    scene_dir = HM3D_MINIVAL_ROOT / scene_key
    return {
        "scene_dir": scene_dir,
        "basis_glb": scene_dir / f"{scene_short}.basis.glb",
        "basis_navmesh": scene_dir / f"{scene_short}.basis.navmesh",
        "semantic_glb": scene_dir / f"{scene_short}.semantic.glb",
        "semantic_txt": scene_dir / f"{scene_short}.semantic.txt",
    }


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
                object_id = int(parts[0])
            except ValueError:
                continue
            label = str(parts[2]).strip()
            try:
                region_id = int(parts[3])
            except ValueError:
                region_id = None
            rows.append(
                {
                    "semantic_object_id": object_id,
                    "semantic_color": parts[1],
                    "semantic_label": label,
                    "semantic_label_norm": normalize_label(label),
                    "semantic_region_id": region_id,
                }
            )
    return rows


def category_aliases(category: str) -> list[str]:
    aliases = CATEGORY_ALIASES.get(category, [category])
    return [normalize_label(alias) for alias in aliases]


def label_matches(category: str, label_norm: str) -> bool:
    aliases = category_aliases(category)
    return any(label_norm == alias or label_norm.endswith(f" {alias}") for alias in aliases)


def build_semantic_scene_rows(episode_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    by_scene_category = Counter((row["scene_key"], row["object_category"]) for row in episode_rows)
    semantic_by_scene: dict[str, list[dict[str, Any]]] = {}
    rows = []
    for scene_key in sorted({str(row["scene_key"]) for row in episode_rows}):
        paths = semantic_paths(scene_key)
        semantic_rows = parse_semantic_txt(paths["semantic_txt"])
        semantic_by_scene[scene_key] = semantic_rows
        labels = sorted({row["semantic_label_norm"] for row in semantic_rows})
        scene_categories = sorted(category for (scene, category), _count in by_scene_category.items() if scene == scene_key)
        matched_by_category = {}
        for category in scene_categories:
            matched = [
                row
                for row in semantic_rows
                if label_matches(category, str(row["semantic_label_norm"]))
            ]
            matched_by_category[category] = [
                {
                    "semantic_object_id": row["semantic_object_id"],
                    "semantic_label": row["semantic_label"],
                    "semantic_region_id": row["semantic_region_id"],
                }
                for row in matched
            ]
        rows.append(
            {
                "scene_key": scene_key,
                "basis_glb_ready": paths["basis_glb"].exists(),
                "basis_navmesh_ready": paths["basis_navmesh"].exists(),
                "semantic_glb_ready": paths["semantic_glb"].exists(),
                "semantic_txt_ready": paths["semantic_txt"].exists(),
                "semantic_object_rows": len(semantic_rows),
                "semantic_unique_labels": len(labels),
                "episode_categories": scene_categories,
                "matched_by_category": matched_by_category,
                "semantic_annotation_route_ready_for_label_support": bool(semantic_rows)
                and paths["semantic_glb"].exists()
                and paths["semantic_txt"].exists(),
                "read_only_source_root": str(RESEARCH2_DATA_ROOT),
            }
        )
    return rows, semantic_by_scene


def build_episode_category_support_rows(
    episode_rows: list[dict[str, Any]],
    semantic_by_scene: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for episode in episode_rows:
        scene_key = str(episode["scene_key"])
        category = str(episode["object_category"])
        matched = [
            row
            for row in semantic_by_scene.get(scene_key, [])
            if label_matches(category, str(row["semantic_label_norm"]))
        ]
        rows.append(
            {
                "adapter_episode_id": episode["adapter_episode_id"],
                "scene_key": scene_key,
                "object_category": category,
                "category_aliases": category_aliases(category),
                "semantic_candidate_label_support_ready": len(matched) > 0,
                "matched_semantic_object_count": len(matched),
                "matched_semantic_labels": sorted({row["semantic_label"] for row in matched}),
                "coordinate_extraction_ready": False,
                "candidate_source_rows_ready": 0,
                "reason": "semantic.txt verifies non-oracle label availability; candidate coordinates still require semantic.glb/Habitat semantic scene extraction.",
            }
        )
    return rows


def build_source_gap_rows(candidate_source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in candidate_source_rows:
        source = str(row["candidate_source"])
        rows_ready = int(row.get("rows_ready") or 0)
        policy_allowed = bool(row.get("policy_input_allowed"))
        if source == "ObjectNav eval goals":
            gap = "no_gap_for_oracle_metric_only"
            next_action = "keep as evaluation-only oracle smoke; do not expose to policy."
        elif source == "observed_miss_runtime_event":
            gap = "execution_runtime_event_missing"
            next_action = "derive only after a candidate visit order is executed."
        elif rows_ready == 0 and policy_allowed:
            gap = "policy_candidate_source_missing"
            next_action = "stage HM3D candidate rows before H001 navigation execution."
        else:
            gap = "unknown"
            next_action = "inspect source contract."
        out.append(
            {
                "candidate_source": source,
                "status": row.get("status"),
                "rows_ready": rows_ready,
                "policy_input_allowed": policy_allowed,
                "required_by_policy_count": row.get("required_by_policy_count", 0),
                "gap": gap,
                "next_action": next_action,
            }
        )
    return out


def build_route_rows(label_support_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_support_ready = sum(1 for row in label_support_rows if row["semantic_candidate_label_support_ready"])
    total = len(label_support_rows)
    return [
        {
            "rank": 1,
            "route_id": "hm3d_semantic_annotation_candidate_source_smoke",
            "selected": label_support_ready == total and total > 0,
            "decision": "selected_next",
            "candidate_sources_unblocked": ["stale_memory_candidates", "current_observation_candidates"],
            "rows_ready_now": 0,
            "label_support_rows_ready": label_support_ready,
            "label_support_rows_total": total,
            "policy_input_allowed": True,
            "deployable_perception_claim": False,
            "requires_long_job": False,
            "expected_next_unit": "E008-M06 HM3D semantic annotation candidate-source smoke",
            "reason": "It can validate the H001 candidate schema and navigation adapter on HM3D without leaking ObjectNav goal/viewpoint fields, while keeping deployable RGB-D/open-vocabulary claims blocked.",
        },
        {
            "rank": 2,
            "route_id": "habitat_rendered_rgbd_detector_candidate_source",
            "selected": False,
            "decision": "defer_after_semantic_smoke",
            "candidate_sources_unblocked": ["current_observation_candidates", "hm3d_rgbd_detector_candidates"],
            "rows_ready_now": 0,
            "label_support_rows_ready": 0,
            "label_support_rows_total": total,
            "policy_input_allowed": True,
            "deployable_perception_claim": True,
            "requires_long_job": True,
            "expected_next_unit": "later HM3D rendered RGB-D detector candidate staging",
            "reason": "Needed for final real RGB-D/open-vocabulary robustness, but it requires rendering frames and detector/proposal runtime.",
        },
        {
            "rank": 3,
            "route_id": "hm3d_conceptgraphs_external_map_candidate_source",
            "selected": False,
            "decision": "defer_until_rendered_rgbd_or_external_map_batch",
            "candidate_sources_unblocked": ["hm3d_external_map_candidates", "hm3d_conceptgraphs_map_candidates"],
            "rows_ready_now": 0,
            "label_support_rows_ready": 0,
            "label_support_rows_total": total,
            "policy_input_allowed": True,
            "deployable_perception_claim": True,
            "requires_long_job": True,
            "expected_next_unit": "later HM3D ConceptGraphs/HOV-SG external map candidate staging",
            "reason": "Needed for external map baseline rigor, but heavier than the first candidate-schema smoke.",
        },
        {
            "rank": 4,
            "route_id": "objectnav_eval_goal_oracle_source",
            "selected": False,
            "decision": "blocked_as_policy_input",
            "candidate_sources_unblocked": [],
            "rows_ready_now": total,
            "label_support_rows_ready": total,
            "label_support_rows_total": total,
            "policy_input_allowed": False,
            "deployable_perception_claim": False,
            "requires_long_job": False,
            "expected_next_unit": "none",
            "reason": "ObjectNav goal/viewpoint fields are ground-truth evaluation fields and must remain oracle-only.",
        },
        {
            "rank": 5,
            "route_id": "synthetic_stale_memory_injection_from_eval_goals",
            "selected": False,
            "decision": "diagnostic_only_not_selected",
            "candidate_sources_unblocked": ["stale_memory_candidates"],
            "rows_ready_now": 0,
            "label_support_rows_ready": total,
            "label_support_rows_total": total,
            "policy_input_allowed": True,
            "deployable_perception_claim": False,
            "requires_long_job": False,
            "expected_next_unit": "only if annotation coordinate extraction fails",
            "reason": "Synthetic stale memory can test code paths, but it is too close to evaluation labels for top-tier navigation evidence.",
        },
        {
            "rank": 6,
            "route_id": "transfer_3rscan_h001_queue_to_hm3d",
            "selected": False,
            "decision": "rejected",
            "candidate_sources_unblocked": [],
            "rows_ready_now": 0,
            "label_support_rows_ready": 0,
            "label_support_rows_total": total,
            "policy_input_allowed": False,
            "deployable_perception_claim": False,
            "requires_long_job": False,
            "expected_next_unit": "none",
            "reason": "3RScan coordinates and HM3D navigation coordinates are not shared; transfer would not be executable.",
        },
    ]


def build_selected_route_contract_rows() -> list[dict[str, Any]]:
    fields = [
        ("candidate_uid", "string", True, True, "Unique candidate id for one HM3D semantic annotation candidate."),
        ("adapter_episode_id", "string", True, True, "Connects candidate rows to ObjectNav adapter rows."),
        ("scene_key", "string", True, True, "HM3D scene key."),
        ("object_category", "string", True, True, "Task query category."),
        ("candidate_label", "string", True, True, "Matched HM3D semantic label."),
        ("candidate_source", "enum", True, True, "Use hm3d_semantic_annotation."),
        ("semantic_object_id", "int", True, True, "HM3D semantic object id, not ObjectNav target id."),
        ("semantic_region_id", "int|null", False, True, "HM3D semantic region id."),
        ("candidate_rank", "int", True, True, "Pre-execution order within category."),
        ("candidate_xyz", "float[3]", True, True, "Centroid or navigable proxy extracted from semantic geometry."),
        ("candidate_viewpoint_position", "float[3]", False, True, "Nearest navigable point if available."),
        ("candidate_confidence", "float", False, True, "Set to annotation prior, not detector confidence."),
        ("annotation_derived", "bool", True, True, "Marks this as annotation-derived staging, not deployable perception."),
        ("eval_goal_object_id", "int", False, False, "ObjectNav target object id is forbidden."),
        ("eval_goal_position", "float[3]", False, False, "ObjectNav goal position is forbidden."),
        ("eval_viewpoint_position", "float[3]", False, False, "ObjectNav oracle viewpoint is forbidden."),
        ("success_label", "bool", False, False, "Post-execution label is forbidden."),
    ]
    return [
        {
            "selected_route": "hm3d_semantic_annotation_candidate_source_smoke",
            "field": field,
            "type": typ,
            "required_for_e008_m06": required,
            "policy_input_allowed": allowed,
            "description": desc,
        }
        for field, typ, required, allowed, desc in fields
    ]


def build_staging_input_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "input": "M02 episode_adapter_rows",
            "path": str(M02_DATA_DIR / "episode_adapter_rows.jsonl"),
            "read_mode": "read",
            "used_for": "episode ids, scene keys, object categories, starts",
            "allowed_for_policy": True,
        },
        {
            "input": "HM3D semantic.txt",
            "path": str(HM3D_MINIVAL_ROOT / "<scene_key>" / "<scene>.semantic.txt"),
            "read_mode": "read_only_external_source",
            "used_for": "semantic object ids and labels",
            "allowed_for_policy": True,
        },
        {
            "input": "HM3D semantic.glb",
            "path": str(HM3D_MINIVAL_ROOT / "<scene_key>" / "<scene>.semantic.glb"),
            "read_mode": "read_only_external_source",
            "used_for": "semantic geometry / centroid extraction in M06",
            "allowed_for_policy": True,
        },
        {
            "input": "HM3D navmesh",
            "path": str(HM3D_MINIVAL_ROOT / "<scene_key>" / "<scene>.basis.navmesh"),
            "read_mode": "read_only_external_source",
            "used_for": "snap candidate points to navigable viewpoints when possible",
            "allowed_for_policy": True,
        },
        {
            "input": "M03 input guard",
            "path": str(M03_ARTIFACT_DIR / "input_guard_rows.jsonl"),
            "read_mode": "read",
            "used_for": "leakage guard",
            "allowed_for_policy": True,
        },
        {
            "input": "M04 oracle path rows",
            "path": str(M04_ARTIFACT_DIR / "oracle_path_rows.jsonl"),
            "read_mode": "read_metric_only",
            "used_for": "metric plumbing sanity only",
            "allowed_for_policy": False,
        },
    ]


def build_blocked_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "field": "closest_goal_object_id",
            "source": "ObjectNav episode",
            "blocked_for_policy": True,
            "reason": "This is the evaluation target id.",
        },
        {
            "field": "eval_goal_position",
            "source": "M03/M04 ObjectNav goal extraction",
            "blocked_for_policy": True,
            "reason": "This is the ground-truth target position.",
        },
        {
            "field": "eval_first_viewpoint_position",
            "source": "ObjectNav goals_by_category",
            "blocked_for_policy": True,
            "reason": "This is an oracle successful viewpoint.",
        },
        {
            "field": "eval_geodesic_distance",
            "source": "ObjectNav episode",
            "blocked_for_policy": True,
            "reason": "This is a metric shortest-path field.",
        },
        {
            "field": "goal_snapped_position",
            "source": "M04 oracle path smoke",
            "blocked_for_policy": True,
            "reason": "This is derived from the ObjectNav target goal.",
        },
        {
            "field": "viewpoint_path_found",
            "source": "M04 oracle path smoke",
            "blocked_for_policy": True,
            "reason": "This is a post-hoc metric plumbing result.",
        },
    ]


def build_route_decision_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": row["rank"],
            "route_id": row["route_id"],
            "selected": row["selected"],
            "decision": row["decision"],
            "next_unit": row["expected_next_unit"],
            "launch_long_job_now": False,
            "reason": row["reason"],
        }
        for row in route_rows
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def build_report(
    coverage: dict[str, Any],
    source_gap_rows: list[dict[str, Any]],
    semantic_scene_rows: list[dict[str, Any]],
    support_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> str:
    source_summary = [
        {
            "candidate_source": row["candidate_source"],
            "gap": row["gap"],
            "rows_ready": row["rows_ready"],
            "next_action": row["next_action"],
        }
        for row in source_gap_rows
    ]
    scene_summary = [
        {
            "scene_key": row["scene_key"],
            "semantic_txt": row["semantic_txt_ready"],
            "semantic_glb": row["semantic_glb_ready"],
            "objects": row["semantic_object_rows"],
            "labels": row["semantic_unique_labels"],
        }
        for row in semantic_scene_rows
    ]
    support_summary = [
        {
            "episode": row["adapter_episode_id"],
            "category": row["object_category"],
            "support": row["semantic_candidate_label_support_ready"],
            "matches": row["matched_semantic_object_count"],
            "coordinates": row["coordinate_extraction_ready"],
        }
        for row in support_rows
    ]
    route_summary = [
        {
            "rank": row["rank"],
            "route": row["route_id"],
            "decision": row["decision"],
            "long_job": row["requires_long_job"],
        }
        for row in route_rows
    ]
    return (
        "# E008-M05 HM3D Candidate Source Staging Plan\n\n"
        "## Facts\n\n"
        f"- Status: `{coverage['status']}`.\n"
        f"- M04 status: `{coverage['m04_status']}`.\n"
        f"- Episode rows: {coverage['episode_rows']}.\n"
        f"- `HM3D` semantic files ready: {coverage['semantic_scene_files_ready']} / {coverage['semantic_scene_files_total']} scenes.\n"
        f"- Semantic category label support: {coverage['semantic_category_support_rows_ready']} / {coverage['semantic_category_support_rows_total']} episode rows.\n"
        f"- Policy candidate source rows ready now: {coverage['ready_policy_candidate_source_rows']}.\n"
        f"- Selected next unit: {coverage['selected_next_unit']}.\n"
        f"- Launch long job now: {str(coverage['launch_long_job_now']).lower()}.\n\n"
        "## Source Gaps\n\n"
        + markdown_table(source_summary, ["candidate_source", "gap", "rows_ready", "next_action"])
        + "\n\n"
        "## Semantic Annotation Readiness\n\n"
        + markdown_table(scene_summary, ["scene_key", "semantic_txt", "semantic_glb", "objects", "labels"])
        + "\n\n"
        "## Episode Label Support\n\n"
        + markdown_table(support_summary, ["episode", "category", "support", "matches", "coordinates"])
        + "\n\n"
        "## Route Decision\n\n"
        + markdown_table(route_summary, ["rank", "route", "decision", "long_job"])
        + "\n\n"
        "## Claim Boundary\n\n"
        "- E008-M05 is a staging plan, not a navigation run.\n"
        "- `ObjectNav` goal, target id, viewpoint, and shortest-path fields remain blocked for policy input.\n"
        "- The selected semantic annotation route can smoke-test HM3D candidate rows, but it is annotation-derived and does not support final real RGB-D/open-vocabulary robustness.\n"
        "- Real navigation `SR` / `SPL` remains false until non-oracle candidate visit orders are executed in `Habitat` and evaluated with trajectory metrics.\n\n"
        "## Agent Inference\n\n"
        "- The lowest-risk next implementation is to extract annotation-derived HM3D semantic candidates first, because it tests the candidate schema and path execution without detector/model runtime.\n"
        "- After that smoke passes, the top-tier path still needs rendered RGB-D detector candidates and an external map route such as `ConceptGraphs` or `HOV-SG`.\n"
    )


def main() -> None:
    m04_coverage = read_json(M04_ARTIFACT_DIR / "coverage.json")
    episode_rows = read_jsonl(M02_DATA_DIR / "episode_adapter_rows.jsonl")
    candidate_source_rows = read_jsonl(M03_ARTIFACT_DIR / "candidate_source_rows.jsonl")

    source_gap_rows = build_source_gap_rows(candidate_source_rows)
    semantic_scene_rows, semantic_by_scene = build_semantic_scene_rows(episode_rows)
    support_rows = build_episode_category_support_rows(episode_rows, semantic_by_scene)
    route_rows = build_route_rows(support_rows)
    selected_contract_rows = build_selected_route_contract_rows()
    staging_input_rows = build_staging_input_contract_rows()
    blocked_input_rows = build_blocked_input_rows()
    decision_rows = build_route_decision_rows(route_rows)

    semantic_scene_files_ready = sum(
        1
        for row in semantic_scene_rows
        if row["basis_glb_ready"] and row["basis_navmesh_ready"] and row["semantic_glb_ready"] and row["semantic_txt_ready"]
    )
    support_ready = sum(1 for row in support_rows if row["semantic_candidate_label_support_ready"])
    ready_policy_rows = sum(
        int(row.get("rows_ready") or 0)
        for row in candidate_source_rows
        if row.get("policy_input_allowed") and row.get("candidate_source") != "observed_miss_runtime_event"
    )
    selected_route = next((row for row in route_rows if row["selected"]), route_rows[0] if route_rows else {})
    plan_ready = (
        m04_coverage.get("status") == "e008_m04_objectnav_oracle_path_smoke_ready"
        and semantic_scene_files_ready == len(semantic_scene_rows)
        and support_ready == len(support_rows)
        and bool(selected_route)
    )

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m05_hm3d_candidate_source_staging_plan_ready" if plan_ready else "e008_m05_hm3d_candidate_source_staging_plan_blocked",
        "m04_status": m04_coverage.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "episode_rows": len(episode_rows),
        "candidate_source_gap_rows": len(source_gap_rows),
        "ready_policy_candidate_source_rows": ready_policy_rows,
        "semantic_scene_files_ready": semantic_scene_files_ready,
        "semantic_scene_files_total": len(semantic_scene_rows),
        "semantic_category_support_rows_ready": support_ready,
        "semantic_category_support_rows_total": len(support_rows),
        "selected_route": selected_route.get("route_id"),
        "selected_next_unit": selected_route.get("expected_next_unit", "repair E008-M05 route plan"),
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "launch_long_job_now": False,
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "source_gap_rows.jsonl", source_gap_rows)
    write_jsonl(ARTIFACT_DIR / "semantic_scene_rows.jsonl", semantic_scene_rows)
    write_jsonl(ARTIFACT_DIR / "episode_category_support_rows.jsonl", support_rows)
    write_jsonl(ARTIFACT_DIR / "candidate_source_route_rows.jsonl", route_rows)
    write_jsonl(ARTIFACT_DIR / "selected_route_contract_rows.jsonl", selected_contract_rows)
    write_jsonl(ARTIFACT_DIR / "staging_input_contract_rows.jsonl", staging_input_rows)
    write_jsonl(ARTIFACT_DIR / "blocked_input_rows.jsonl", blocked_input_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", decision_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, source_gap_rows, semantic_scene_rows, support_rows, route_rows))

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "source_gap_rows.jsonl", source_gap_rows)
    write_jsonl(DATA_OUT_DIR / "semantic_scene_rows.jsonl", semantic_scene_rows)
    write_jsonl(DATA_OUT_DIR / "episode_category_support_rows.jsonl", support_rows)
    write_jsonl(DATA_OUT_DIR / "candidate_source_route_rows.jsonl", route_rows)
    write_jsonl(DATA_OUT_DIR / "selected_route_contract_rows.jsonl", selected_contract_rows)
    write_jsonl(DATA_OUT_DIR / "staging_input_contract_rows.jsonl", staging_input_rows)
    write_jsonl(DATA_OUT_DIR / "blocked_input_rows.jsonl", blocked_input_rows)
    write_jsonl(DATA_OUT_DIR / "route_decision_rows.jsonl", decision_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
