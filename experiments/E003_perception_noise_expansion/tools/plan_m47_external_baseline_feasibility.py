#!/usr/bin/env python3
"""Plan E003-M47 external proposal/mapping baseline feasibility gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M46_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M46_score_redesign_or_external_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M47_external_baseline_feasibility_gate_v0"
M47_VERSION = "e003_m47_external_baseline_feasibility_gate_v0"


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
        + 3 * int(row["direct_m45_failure_diagnostic"])
        + 2 * int(row["schema_bridge_fit"])
        + 2 * int(row["top_tier_reviewer_value"])
        - 2 * int(row["implementation_burden"])
        - int(row["dependency_risk"])
        - int(row["dataset_conversion_burden"])
    )


def build_candidates() -> list[dict[str, Any]]:
    rows = [
        {
            "dataset_conversion_burden": 1,
            "dependency_risk": 2,
            "direct_m45_failure_diagnostic": 5,
            "external_route": "Grounded-SAM",
            "implementation_burden": 2,
            "input_fit": "current posed RGB-D frames, prompt labels, and GroundingDINO text boxes are already in the runner; add SAM mask refinement before depth backprojection",
            "main_risk": "it may improve mask geometry while preserving GroundingDINO label false positives",
            "next_unit": "E003-M48 Grounded-SAM mask-backprojection proposal smoke",
            "output_fit": "2D masks plus existing depth/pose can be converted to the current real_proposal_prediction_jsonl_v0 schema",
            "primary_question": "Are M45 false positives and target losses partly caused by box-based depth projection rather than stale-memory logic?",
            "schema_bridge_fit": 5,
            "source_url": "https://github.com/IDEA-Research/Grounded-Segment-Anything",
            "top_tier_reviewer_value": 3,
            "current_harness_fit": 5,
        },
        {
            "dataset_conversion_burden": 3,
            "dependency_risk": 4,
            "direct_m45_failure_diagnostic": 4,
            "external_route": "OpenMask3D",
            "implementation_burden": 4,
            "input_fit": "needs point cloud plus posed RGB-D frames; current data likely has enough ingredients but requires ScanNet-like scene packaging and checkpoints",
            "main_risk": "MinkowskiEngine/checkpoint/data-format burden can dominate before a small feasibility result",
            "next_unit": "OpenMask3D scene-format staging after Grounded-SAM smoke or if mask-backprojection fails",
            "output_fit": "3D instance masks can map to proposal centroids and open-vocabulary labels, but adapter work is nontrivial",
            "primary_question": "Does a 3D open-vocabulary instance segmentation baseline reduce proposal false positives better than 2D detector projection?",
            "schema_bridge_fit": 4,
            "source_url": "https://github.com/OpenMask3D/openmask3d",
            "top_tier_reviewer_value": 5,
            "current_harness_fit": 3,
        },
        {
            "dataset_conversion_burden": 4,
            "dependency_risk": 3,
            "direct_m45_failure_diagnostic": 3,
            "external_route": "OVIR-3D",
            "implementation_burden": 4,
            "input_fit": "expects custom RGB-D video folders, poses, config, and reconstructed point cloud; current 3RScan can be converted but not directly",
            "main_risk": "retrieval-oriented output is less direct for proposal precision/recall tables",
            "next_unit": "defer unless OpenMask3D is blocked",
            "output_fit": "ranked 3D instance retrieval can be compared for query success, but proposal-row matching needs a custom adapter",
            "primary_question": "Can retrieval-style 3D instance grounding serve as an alternative to proposal generation?",
            "schema_bridge_fit": 3,
            "source_url": "https://github.com/shiyoung77/OVIR-3D",
            "top_tier_reviewer_value": 4,
            "current_harness_fit": 2,
        },
        {
            "dataset_conversion_burden": 3,
            "dependency_risk": 5,
            "direct_m45_failure_diagnostic": 3,
            "external_route": "ConceptGraphs",
            "implementation_burden": 5,
            "input_fit": "takes posed RGB-D images and builds object-centric open-vocabulary maps, but requires its own mapping stack and foundation-model dependencies",
            "main_risk": "heavy dependency chain, including Grounded-SAM/LLaVA style components, makes it a poor first debugging gate",
            "next_unit": "mapping-baseline track after a proposal backend smoke is stable",
            "output_fit": "object-centric map/graph is highly relevant to semantic mapping, but less direct for M45 proposal-quality diagnosis",
            "primary_question": "Does an object-centric open-vocabulary map baseline outperform the current proposal-memory stack?",
            "schema_bridge_fit": 3,
            "source_url": "https://github.com/concept-graphs/concept-graphs",
            "top_tier_reviewer_value": 5,
            "current_harness_fit": 3,
        },
        {
            "dataset_conversion_burden": 5,
            "dependency_risk": 5,
            "direct_m45_failure_diagnostic": 2,
            "external_route": "HOV-SG",
            "implementation_burden": 5,
            "input_fit": "supports posed RGB-D and hierarchical scene graph construction, but its strongest path is HM3DSem/ScanNet/Replica style navigation/hierarchy evaluation",
            "main_risk": "too broad for immediate M45 proposal failure; better suited once navigation/hierarchy claims are active",
            "next_unit": "defer to navigation/search benchmark expansion",
            "output_fit": "hierarchical graph is valuable for language navigation, but not a direct proposal-quality replacement",
            "primary_question": "Does hierarchical open-vocabulary mapping improve language-grounded navigation/search?",
            "schema_bridge_fit": 2,
            "source_url": "https://github.com/hovsg/HOV-SG",
            "top_tier_reviewer_value": 5,
            "current_harness_fit": 2,
        },
    ]
    for row in rows:
        row["feasibility_score"] = score_route(row)
    return sorted(rows, key=lambda row: row["feasibility_score"], reverse=True)


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E003-M47 External Baseline Feasibility Gate",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Selected first route: `{coverage['selected_route']}`.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        f"- M46 selected route: `{coverage['m46_selected_route']}`.",
        "",
        "## Route Ranking",
        "",
    ]
    for row in coverage["candidate_routes"]:
        lines.append(
            f"- `{row['external_route']}`: score {row['feasibility_score']}, "
            f"harness fit {row['current_harness_fit']}, diagnostic fit {row['direct_m45_failure_diagnostic']}, "
            f"burden {row['implementation_burden']}."
        )
    lines.extend(
        [
            "",
            "## Paper Claim",
            "",
            "- E003-M47 does not support a new paper claim.",
            "- It selects the first external route needed to separate proposal/backend failure from stale-memory logic.",
            "",
            "## Agent Inference",
            "",
            "- `Grounded-SAM` is the best first route because it is the smallest controlled change from the current `GroundingDINO` RGB-D backprojection backend.",
            "- `OpenMask3D` has stronger top-tier baseline value but should follow after mask-backprojection smoke because its setup and data conversion burden are higher.",
            "- `ConceptGraphs` and `HOV-SG` are better mapping/navigation baselines, not first proposal-failure diagnosis tools.",
            "",
            "## User Decision Needed",
            "",
            "- None for the first feasibility route. The next implementation unit should smoke-test `Grounded-SAM` mask-backprojection.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m46-dir", default=DEFAULT_M46_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m46 = load_json(args.m46_dir / "coverage.json")
    candidates = build_candidates()
    selected = candidates[0]
    coverage = {
        "candidate_routes": candidates,
        "m46_selected_route": (m46.get("route_decision") or {}).get("selected_route"),
        "m47_version": M47_VERSION,
        "next_recommended_unit": selected["next_unit"],
        "selected_route": selected["external_route"],
        "status": "external_baseline_feasibility_gate_ready",
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_decision.json", selected)
    write_jsonl(args.out_dir / "candidate_routes.jsonl", candidates)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
