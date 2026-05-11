#!/usr/bin/env python3
"""Plan a dynamic-pair-aligned real-proposal bridge after E003-M54."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_QUERY_DIR = (
    RESEARCH_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_M16_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M16_real_proposal_route_decision_v0"
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M54_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M54_search_critical_bbox_failure_boundary_v0"
DEFAULT_DATASET_ROOT = RESEARCH_ROOT / "local_dataset" / "3RScan" / "scans"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M55_dynamic_pair_bridge_gate_v0"
M55_VERSION = "e003_m55_dynamic_pair_bridge_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


def scan_state(scan_id: str, dataset_root: Path) -> dict[str, Any]:
    scan_dir = dataset_root / scan_id
    sequence_dir = scan_dir / "sequence"
    color_frames = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.exists() else 0
    depth_frames = len(list(sequence_dir.glob("*.depth.pgm"))) if sequence_dir.exists() else 0
    pose_frames = len(list(sequence_dir.glob("*.pose.txt"))) if sequence_dir.exists() else 0
    frame_triplets = min(color_frames, depth_frames, pose_frames)
    state = {
        "color_frames": color_frames,
        "depth_frames": depth_frames,
        "frame_triplet_lower_bound": frame_triplets,
        "has_info": (sequence_dir / "_info.txt").exists(),
        "ply_ready": (scan_dir / "labels.instances.annotated.v2.ply").exists(),
        "scan_dir": str(scan_dir),
        "scan_dir_ready": scan_dir.exists(),
        "scan_id": scan_id,
        "segs_ready": (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists(),
        "semantic_triplet_ready": False,
        "semseg_ready": (scan_dir / "semseg.v2.json").exists(),
        "sequence_dir_ready": sequence_dir.exists(),
        "sequence_ready": False,
        "sequence_zip_ready": (scan_dir / "sequence.zip").exists(),
    }
    state["semantic_triplet_ready"] = bool(
        state["scan_dir_ready"] and state["ply_ready"] and state["segs_ready"] and state["semseg_ready"]
    )
    state["sequence_ready"] = bool(state["has_info"] and frame_triplets > 0)
    state["proposal_alignment_ready"] = bool(state["semantic_triplet_ready"] and state["sequence_ready"])
    return state


def build_label_priority(label_rows: list[dict[str, Any]]) -> dict[str, int]:
    priorities = {}
    for row in label_rows:
        priorities[str(row.get("label_canonical"))] = int(row.get("search_bridge_priority", 0) or 0)
    return priorities


def build_bridge_target_rows(
    query_boundary_rows: list[dict[str, Any]],
    label_priorities: dict[str, int],
    dataset_root: Path,
) -> list[dict[str, Any]]:
    by_scan: dict[str, dict[str, Any]] = {}
    for row in query_boundary_rows:
        scan_id = str(row.get("rescan_id"))
        label = str(row.get("label_canonical"))
        e001_fail = row.get("e001_primary_success") is False
        e002_fail = row.get("e002_primary_success") is False
        item = by_scan.setdefault(
            scan_id,
            {
                "base_row_uids": set(),
                "bridge_priority_score": 0,
                "e001_failure_rows": 0,
                "e002_failure_rows": 0,
                "failure_labels": Counter(),
                "label_priority_sum": 0,
                "labels": Counter(),
                "query_rows": 0,
                "row_bands": Counter(),
                "scan_id": scan_id,
                "search_failure_rows": 0,
                "task_contexts": Counter(),
            },
        )
        priority = int(label_priorities.get(label, 0))
        item["query_rows"] += 1
        item["label_priority_sum"] += priority
        item["labels"][label] += 1
        item["row_bands"][str(row.get("row_band"))] += 1
        item["task_contexts"][str(row.get("task_context_id"))] += 1
        item["base_row_uids"].add(str(row.get("base_row_uid")))
        if e001_fail:
            item["e001_failure_rows"] += 1
        if e002_fail:
            item["e002_failure_rows"] += 1
        if e001_fail or e002_fail:
            item["search_failure_rows"] += 1
            item["failure_labels"][label] += 1
            item["bridge_priority_score"] += 10 + priority
        elif priority > 0:
            item["bridge_priority_score"] += priority

    rows = []
    for scan_id, item in by_scan.items():
        state = scan_state(scan_id, dataset_root)
        needs_sequence = bool(state["semantic_triplet_ready"] and not state["sequence_ready"])
        if item["search_failure_rows"]:
            recommended_action = "stage_current_rescan_sequence_for_direct_bridge"
        elif needs_sequence and item["label_priority_sum"] > 0:
            recommended_action = "stage_if_expanding_label_level_bridge"
        elif state["proposal_alignment_ready"]:
            recommended_action = "ready_for_detector_bridge"
        else:
            recommended_action = "not_priority_for_m56"
        rows.append(
            {
                "base_row_uid_count": len(item["base_row_uids"]),
                "bridge_priority_score": int(item["bridge_priority_score"]),
                "e001_failure_rows": int(item["e001_failure_rows"]),
                "e002_failure_rows": int(item["e002_failure_rows"]),
                "failure_labels": dict(item["failure_labels"].most_common()),
                "label_priority_sum": int(item["label_priority_sum"]),
                "labels": dict(item["labels"].most_common()),
                "query_rows": int(item["query_rows"]),
                "recommended_action": recommended_action,
                "row_bands": dict(item["row_bands"].most_common()),
                "scan_id": scan_id,
                "search_failure_rows": int(item["search_failure_rows"]),
                "task_contexts": dict(item["task_contexts"].most_common()),
                **state,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -int(row["search_failure_rows"]),
            -int(row["bridge_priority_score"]),
            str(row["scan_id"]),
        ),
    )


def score_route(row: dict[str, Any]) -> int:
    return (
        4 * int(row["direct_search_causality"])
        + 3 * int(row["top_tier_value"])
        + 3 * int(row["claim_relevance"])
        + 2 * int(row["current_artifact_fit"])
        - 2 * int(row["implementation_burden"])
        - int(row["dependency_risk"])
        - int(row["claim_weakness"])
    )


def build_routes(
    m16: dict[str, Any],
    m17: dict[str, Any],
    m33: dict[str, Any],
    m54: dict[str, Any],
    bridge_targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    search_failure_target_scans = [row for row in bridge_targets if int(row["search_failure_rows"]) > 0]
    sequence_ready_failure_scans = [row for row in search_failure_target_scans if bool(row["sequence_ready"])]
    semantic_ready_failure_scans = [row for row in search_failure_target_scans if bool(row["semantic_triplet_ready"])]
    routes = [
        {
            "claim_relevance": 5,
            "claim_weakness": 1,
            "current_artifact_fit": 3,
            "dependency_risk": 3,
            "direct_search_causality": 5,
            "evidence_basis": [
                f"M54 exact current query-instance joins are {m54.get('exact_current_query_join_rows')}.",
                f"M16 current real RGB-D proposal-ready query rows are {m16.get('query_rows_current_real_rgbd_proposal_ready')}.",
                f"Search-failure current rescans to stage first: {len(search_failure_target_scans)}.",
                f"Those scans with semantic triplets ready: {len(semantic_ready_failure_scans)}.",
                f"Those scans already sequence-ready: {len(sequence_ready_failure_scans)}.",
            ],
            "implementation_burden": 3,
            "main_risk": "requires sequence payload staging/download before detector rerun; must use background job policy if download or decompression is needed",
            "next_unit": "E003-M56 current-rescan sequence payload staging plan",
            "route_id": "stage_search_failure_current_rescans_first",
            "route_type": "direct_dynamic_pair_bridge",
            "top_tier_value": 5,
        },
        {
            "claim_relevance": 3,
            "claim_weakness": 3,
            "current_artifact_fit": 5,
            "dependency_risk": 0,
            "direct_search_causality": 2,
            "evidence_basis": [
                f"M17 staged ready scan rows: {m17.get('ready_scan_rows')}.",
                f"M33 detector result covers {m33.get('evaluated_scan_count')} scans and {m33.get('evaluated_frame_count')} frames.",
                "Can reuse existing M33/M45 detector outputs without another long detector run.",
                "Does not preserve E001/E002 dynamic-pair current-rescan identity.",
            ],
            "implementation_burden": 1,
            "main_risk": "would become a detector-aligned search proxy rather than direct stale-memory dynamic-pair evidence",
            "next_unit": "E003-M56 detector-aligned search proxy design",
            "route_id": "detector_aligned_search_proxy_on_m17_scans",
            "route_type": "proxy_bridge",
            "top_tier_value": 3,
        },
        {
            "claim_relevance": 2,
            "claim_weakness": 4,
            "current_artifact_fit": 4,
            "dependency_risk": 0,
            "direct_search_causality": 1,
            "evidence_basis": [
                f"M54 reference-memory-only joins: {m54.get('reference_memory_only_join_rows')}.",
                f"M16 reference-sequence-ready query rows: {m16.get('query_rows_reference_sequence_ready')}.",
                "This can probe perception of old-memory/reference locations, not current target re-observation.",
            ],
            "implementation_burden": 1,
            "main_risk": "tests memory-side perception but not dynamic current-target search success",
            "next_unit": "E003-M56 reference-memory-side diagnostic only",
            "route_id": "reference_memory_side_bridge_only",
            "route_type": "weak_diagnostic_bridge",
            "top_tier_value": 2,
        },
        {
            "claim_relevance": 3,
            "claim_weakness": 4,
            "current_artifact_fit": 4,
            "dependency_risk": 4,
            "direct_search_causality": 1,
            "evidence_basis": [
                "`OpenMask3D` is a stronger external 3D instance proposal baseline candidate.",
                "M54 shows another detector cannot fix the missing E001/E002 current-rescan join by itself.",
                "It is better after the bridge denominator is fixed.",
            ],
            "implementation_burden": 5,
            "main_risk": "heavy dependency before downstream search bridge is fixed",
            "next_unit": "E003-M56 OpenMask3D feasibility after bridge denominator",
            "route_id": "openmask3d_before_bridge",
            "route_type": "external_proposal_baseline",
            "top_tier_value": 4,
        },
        {
            "claim_relevance": 2,
            "claim_weakness": 5,
            "current_artifact_fit": 5,
            "dependency_risk": 0,
            "direct_search_causality": 0,
            "evidence_basis": [
                "Controlled annotation-proxy stress is already complete.",
                "It does not provide real RGB-D/open-vocabulary evidence.",
            ],
            "implementation_burden": 0,
            "main_risk": "insufficient for top-tier real perception/search claim",
            "next_unit": "No new E003 real-proposal unit",
            "route_id": "stay_with_label_level_stress_only",
            "route_type": "no_direct_bridge",
            "top_tier_value": 1,
        },
    ]
    for row in routes:
        row["feasibility_score"] = score_route(row)
        row["paper_table_command_ready"] = False
        row["real_rgbd_or_open_vocab_search_claim_ready"] = False
    return sorted(routes, key=lambda row: row["feasibility_score"], reverse=True)


def build_report(coverage: dict[str, Any], bridge_targets: list[dict[str, Any]]) -> str:
    selected = coverage["selected_route"]
    lines = [
        "# E003-M55 Dynamic-Pair Bridge Gate",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- M54 exact current query-instance joins: {coverage['m54_exact_current_query_join_rows']}.",
        f"- M16 current real RGB-D proposal-ready query rows: {coverage['m16_current_real_rgbd_proposal_ready_query_rows']}.",
        f"- Search-failure current rescans: {coverage['search_failure_current_rescan_count']}.",
        f"- Search-failure current rescans with semantic triplet ready: {coverage['search_failure_semantic_triplet_ready_scan_count']}.",
        f"- Search-failure current rescans already sequence-ready: {coverage['search_failure_sequence_ready_scan_count']}.",
        f"- Selected route: `{selected['route_id']}`.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Priority Current Rescans",
        "",
    ]
    for row in bridge_targets[:8]:
        if not row["search_failure_rows"]:
            continue
        lines.append(
            f"- `{row['scan_id']}`: failure rows {row['search_failure_rows']}, "
            f"labels {row['failure_labels']}, semantic triplet {row['semantic_triplet_ready']}, "
            f"sequence ready {row['sequence_ready']}, action `{row['recommended_action']}`."
        )
    lines.extend(["", "## Route Ranking", ""])
    for row in coverage["candidate_routes"]:
        lines.append(
            f"- `{row['route_id']}`: score {row['feasibility_score']}, "
            f"type `{row['route_type']}`, next `{row['next_unit']}`."
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M55 does not create a paper result claim.",
            "- E003-M55 fixes the next bridge route needed before real RGB-D/open-vocabulary proposal evidence can support a downstream search claim.",
            "- Real RGB-D/open-vocabulary search robustness remains blocked until current-rescan detector outputs are available and evaluated against E001/E002 rows.",
            "",
            "## 에이전트 추론",
            "",
            "- The direct route should stage the current rescans that already produce `chair`/`pillow` search failures, because this is the smallest bridge that can turn detector failures into downstream search evidence.",
            "- A detector-aligned proxy on M17 scans is cheaper, but it weakens the main stale-memory dynamic-pair claim.",
            "- `OpenMask3D` should wait until the bridge denominator is fixed; otherwise it only improves proposal-quality evidence without solving the search-causality gap.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if E003-M56 current-rescan sequence payload staging plan is accepted as the next unit.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e001-query-dir", default=DEFAULT_E001_QUERY_DIR, type=Path)
    parser.add_argument("--m16-dir", default=DEFAULT_M16_DIR, type=Path)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m54-dir", default=DEFAULT_M54_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m16 = load_json(args.m16_dir / "coverage.json")
    m17 = load_json(args.m17_dir / "coverage.json")
    m33 = load_json(args.m33_dir / "coverage.json")
    m54 = load_json(args.m54_dir / "coverage.json")
    query_boundary_rows = load_jsonl(args.m54_dir / "query_search_boundary_rows.jsonl")
    label_rows = load_jsonl(args.m54_dir / "label_search_risk_rows.jsonl")
    label_priorities = build_label_priority(label_rows)
    bridge_targets = build_bridge_target_rows(
        query_boundary_rows=query_boundary_rows,
        label_priorities=label_priorities,
        dataset_root=args.dataset_root,
    )
    routes = build_routes(m16=m16, m17=m17, m33=m33, m54=m54, bridge_targets=bridge_targets)
    selected = routes[0]
    search_failure_targets = [row for row in bridge_targets if int(row["search_failure_rows"]) > 0]
    semantic_ready_failure_targets = [row for row in search_failure_targets if bool(row["semantic_triplet_ready"])]
    sequence_ready_failure_targets = [row for row in search_failure_targets if bool(row["sequence_ready"])]
    coverage = {
        "bridge_target_scan_rows": len(bridge_targets),
        "candidate_routes": routes,
        "dataset_root": str(args.dataset_root),
        "m16_current_real_rgbd_proposal_ready_query_rows": m16.get("query_rows_current_real_rgbd_proposal_ready"),
        "m16_current_rescan_sequence_ready_query_rows": m16.get("query_rows_current_rescan_sequence_ready"),
        "m16_reference_sequence_ready_query_rows": m16.get("query_rows_reference_sequence_ready"),
        "m17_ready_scan_rows": m17.get("ready_scan_rows"),
        "m33_evaluated_frame_count": m33.get("evaluated_frame_count"),
        "m33_evaluated_scan_count": m33.get("evaluated_scan_count"),
        "m54_exact_current_query_join_rows": m54.get("exact_current_query_join_rows"),
        "m54_existing_search_failure_with_label_level_detector_risk_rows": m54.get(
            "existing_search_failure_with_label_level_detector_risk_rows"
        ),
        "m54_label_overlap_count": m54.get("label_overlap_count"),
        "m54_reference_memory_only_join_rows": m54.get("reference_memory_only_join_rows"),
        "m55_version": M55_VERSION,
        "next_recommended_unit": selected["next_unit"],
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_search_claim_ready": False,
        "search_failure_current_rescan_count": len(search_failure_targets),
        "search_failure_current_rescans": [row["scan_id"] for row in search_failure_targets],
        "search_failure_semantic_triplet_ready_scan_count": len(semantic_ready_failure_targets),
        "search_failure_sequence_ready_scan_count": len(sequence_ready_failure_targets),
        "selected_route": selected,
        "status": "dynamic_pair_bridge_gate_ready",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", selected)
    write_jsonl(args.out_dir / "candidate_routes.jsonl", routes)
    write_jsonl(args.out_dir / "bridge_target_scan_rows.jsonl", bridge_targets)
    write_text(args.out_dir / "report.md", build_report(coverage, bridge_targets))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
