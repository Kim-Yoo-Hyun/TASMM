#!/usr/bin/env python3
"""Plan E003-M51 route after M50 same-subset comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M47_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M47_external_baseline_feasibility_gate_v0"
DEFAULT_M50_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M50_same_subset_bbox_vs_mask_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M51_post_m50_route_decision_v0"
M51_VERSION = "e003_m51_post_m50_route_decision_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def score_route(row: dict[str, Any]) -> int:
    return (
        3 * int(row["current_harness_fit"])
        + 3 * int(row["diagnostic_value"])
        + 2 * int(row["reviewer_defense_value"])
        + 2 * int(row["top_tier_path_value"])
        - 2 * int(row["implementation_burden"])
        - int(row["dependency_risk"])
        - int(row["compute_cost"])
    )


def build_routes(m50: dict[str, Any], m47: dict[str, Any], m33: dict[str, Any]) -> list[dict[str, Any]]:
    comparison = m50.get("comparison") or {}
    mask_lost_target = (comparison.get("delta_mask_minus_bbox") or {}).get("matched_target_rows", 0) < 0
    mask_worse_centroid = (comparison.get("delta_mask_minus_bbox") or {}).get("matched_centroid_error_mean_m", 0) > 0
    m47_candidates = {row["external_route"]: row for row in m47.get("candidate_routes", [])}
    openmask_m47 = m47_candidates.get("OpenMask3D", {})

    routes = [
        {
            "compute_cost": 1,
            "current_harness_fit": 5,
            "dependency_risk": 0,
            "diagnostic_value": 5,
            "evidence_basis": [
                "E003-M50 mask-depth lost one matched target versus bbox-depth on the same subset",
                "E003-M50 mask-depth worsened mean matched centroid error",
                "Failure can be diagnosed from existing M49/M50 artifacts without another Docker run",
            ],
            "implementation_burden": 1,
            "main_risk": "may only confirm that the current Grounded-SAM route should be abandoned",
            "next_unit": "E003-M52 Grounded-SAM mask failure analysis",
            "route_id": "targeted_mask_failure_analysis_first",
            "route_type": "artifact_local_diagnostic",
            "selected_if": "M50 is negative but could still hide a mask projection/filtering implementation issue",
            "top_tier_path_value": 3,
            "reviewer_defense_value": 5,
        },
        {
            "compute_cost": 2,
            "current_harness_fit": 5,
            "dependency_risk": 1,
            "diagnostic_value": 4,
            "evidence_basis": [
                "E003-M33 already has an 8-scan scaled bbox-depth artifact",
                f"E003-M33 matched targets {m33.get('matched_target_rows')} and false positives {m33.get('false_positive_proposal_rows')}",
                "E003-M50 same-subset bbox-depth beat mask-depth on matched targets, precision, recall, and centroid error",
            ],
            "implementation_burden": 2,
            "main_risk": "continuing only bbox-depth may weaken external-baseline novelty unless paired with a later stronger baseline",
            "next_unit": "E003-M52 bbox-depth continuation and failure-boundary repair gate",
            "route_id": "bbox_depth_continuation_after_mask_check",
            "route_type": "current_best_route_continuation",
            "selected_if": "mask failure analysis finds no simple implementation fix",
            "top_tier_path_value": 3,
            "reviewer_defense_value": 4,
        },
        {
            "compute_cost": 5,
            "current_harness_fit": int(openmask_m47.get("current_harness_fit", 3) or 3),
            "dependency_risk": int(openmask_m47.get("dependency_risk", 4) or 4),
            "diagnostic_value": 4,
            "evidence_basis": [
                "M47 ranked OpenMask3D second after Grounded-SAM",
                "OpenMask3D has stronger 3D instance baseline value than 2D mask backprojection",
                "It may better separate detector proposal quality from stale-memory logic",
            ],
            "implementation_burden": int(openmask_m47.get("implementation_burden", 4) or 4),
            "main_risk": "scene-format conversion, checkpoints, and MinkowskiEngine-style dependencies may dominate before a small result",
            "next_unit": "E003-M52 OpenMask3D scene-format feasibility gate",
            "route_id": "openmask3d_feasibility_after_mask_failure",
            "route_type": "external_3d_instance_baseline",
            "selected_if": "mask failure analysis confirms 2D mask-depth projection is not worth repairing and external baseline value becomes urgent",
            "top_tier_path_value": 5,
            "reviewer_defense_value": 5,
        },
    ]
    for row in routes:
        row["feasibility_score"] = score_route(row)
    routes = sorted(routes, key=lambda row: row["feasibility_score"], reverse=True)
    for row in routes:
        row["m50_mask_lost_target"] = bool(mask_lost_target)
        row["m50_mask_worse_centroid"] = bool(mask_worse_centroid)
    return routes


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage["selected_route"]
    m50 = coverage["m50_summary"]
    lines = [
        "# E003-M51 Post-M50 Route Decision",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- M50 selected route: `{m50['selected_next_route']}`.",
        f"- M50 weak/hard positive: {m50['weak_positive']} / {m50['hard_positive']}.",
        f"- M50 bbox-depth matched / FP / precision: {m50['bbox_matched_target_rows']} / {m50['bbox_false_positive_rows']} / {m50['bbox_precision']}.",
        f"- M50 mask-depth matched / FP / precision: {m50['mask_matched_target_rows']} / {m50['mask_false_positive_rows']} / {m50['mask_precision']}.",
        f"- Selected immediate route: `{selected['route_id']}`.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Route Ranking",
        "",
    ]
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
            "- E003-M51 does not create a paper result claim.",
            "- It fixes the next route after a negative `Grounded-SAM` same-subset comparison.",
            "- Real RGB-D/open-vocabulary robustness remains unsupported.",
            "",
            "## 에이전트 추론",
            "",
            "- Do not scale `Grounded-SAM` now because M50 is negative.",
            "- Do not jump straight to `OpenMask3D` before checking whether M50 exposed a simple mask projection/filtering bug.",
            "- A short artifact-local mask failure analysis is the cheapest way to defend abandoning or repairing the `Grounded-SAM` route.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if the immediate diagnostic route is accepted.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m47-dir", default=DEFAULT_M47_DIR, type=Path)
    parser.add_argument("--m50-dir", default=DEFAULT_M50_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m33 = load_json(args.m33_dir / "coverage.json")
    m47 = load_json(args.m47_dir / "coverage.json")
    m50 = load_json(args.m50_dir / "coverage.json")
    routes = build_routes(m50=m50, m47=m47, m33=m33)
    selected = routes[0]

    bbox = m50["bbox_depth_metrics"]
    mask = m50["mask_depth_metrics"]
    comparison = m50["comparison"]
    coverage = {
        "candidate_routes": routes,
        "m50_summary": {
            "bbox_false_positive_rows": bbox.get("false_positive_proposal_rows"),
            "bbox_matched_target_rows": bbox.get("matched_target_rows"),
            "bbox_precision": bbox.get("proposal_precision_smoke"),
            "hard_positive": comparison.get("hard_positive"),
            "mask_false_positive_rows": mask.get("false_positive_proposal_rows"),
            "mask_matched_target_rows": mask.get("matched_target_rows"),
            "mask_precision": mask.get("proposal_precision_smoke"),
            "selected_next_route": (m50.get("route_decision") or {}).get("selected_next_route"),
            "weak_positive": comparison.get("weak_positive"),
        },
        "m51_version": M51_VERSION,
        "next_recommended_unit": selected["next_unit"],
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "selected_route": selected,
        "status": "post_m50_route_decision_ready",
    }

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", selected)
    write_jsonl(args.out_dir / "candidate_routes.jsonl", routes)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
