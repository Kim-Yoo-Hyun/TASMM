#!/usr/bin/env python3
"""Plan the E005 external baseline transition after E004."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M01_external_baseline_transition_v0"
)
E004_DECISION = (
    ROOT
    / "experiments"
    / "E004_task_context_memory_trust"
    / "artifacts"
    / "E004-M05_scale_split_stress_v0"
    / "decision.json"
)
E003_OPENMASK_BLOCKER = (
    ROOT
    / "experiments"
    / "E003_perception_noise_expansion"
    / "artifacts"
    / "E003-M72_openmask3d_blocker_fallback_gate_v0"
    / "coverage.json"
)


WEIGHTS = {
    "e004_claim_alignment": 3,
    "artifact_fit": 2,
    "implementation_feasibility": 2,
    "top_tier_reviewer_value": 2,
    "direction_b_value": 2,
    "immediate_executable_value": 1,
}


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_rows(openmask_blocked: bool) -> list[dict]:
    rows = [
        {
            "baseline": "DualMap",
            "family": "dynamic_semantic_mapping",
            "role": "Primary dynamic semantic mapping baseline",
            "source": "https://eku127.github.io/DualMap/",
            "why_relevant": (
                "Closest external baseline to task/staleness-aware semantic memory: "
                "online open-vocabulary mapping, dynamic changes, natural-language navigation, "
                "global abstract map plus local concrete map."
            ),
            "first_use_in_this_project": (
                "Audit code/data interface and define an adapter from DualMap-style "
                "global/local map outputs to the E004 candidate-visit and memory-trust schema."
            ),
            "known_blocker": "No local adapter yet; likely needs a stream/log interface rather than current JSONL rows.",
            "fallback_if_blocked": "ConceptGraphs object/graph export adapter",
            "e004_claim_alignment": 5,
            "artifact_fit": 2,
            "implementation_feasibility": 3,
            "top_tier_reviewer_value": 4,
            "direction_b_value": 5,
            "immediate_executable_value": 2,
        },
        {
            "baseline": "ConceptGraphs",
            "family": "open_vocabulary_mapping",
            "role": "Strong open-vocabulary graph mapping baseline",
            "source": "https://concept-graphs.github.io/",
            "why_relevant": (
                "Builds open-vocabulary object/relationship graphs from posed RGB-D observations; "
                "well aligned with semantic map representation and planner-facing map utility."
            ),
            "first_use_in_this_project": (
                "If DualMap adapter blocks, build a ConceptGraphs-style object graph export "
                "for the same staged RGB-D scans and convert graph nodes to E004 candidates."
            ),
            "known_blocker": "Heavy dependencies: Grounded-SAM, checkpoints, LLaVA/OpenAI-style captioning path.",
            "fallback_if_blocked": "Open3DSG relation/object prediction audit",
            "e004_claim_alignment": 3,
            "artifact_fit": 4,
            "implementation_feasibility": 3,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 4,
            "immediate_executable_value": 3,
        },
        {
            "baseline": "Open3DSG",
            "family": "open_vocabulary_3d_scene_graph",
            "role": "Open-vocabulary 3D scene graph baseline",
            "source": "https://github.com/boschresearch/Open3DSG",
            "why_relevant": (
                "Uses 3RScan in its evaluation path and targets open-vocabulary object/relation prediction, "
                "which is useful for relation-aware semantic memory comparisons."
            ),
            "first_use_in_this_project": (
                "Audit checkpoint/feature requirements and whether predicted nodes/relations can be "
                "joined to E004 query rows without full retraining."
            ),
            "known_blocker": "Potentially heavy 2D feature precompute and checkpoint dependency; relation output is not a search policy.",
            "fallback_if_blocked": "ConceptGraphs/HOV-SG representation comparison only",
            "e004_claim_alignment": 3,
            "artifact_fit": 3,
            "implementation_feasibility": 2,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 4,
            "immediate_executable_value": 2,
        },
        {
            "baseline": "OpenMask3D",
            "family": "external_3d_instance_proposal",
            "role": "External 3D instance proposal baseline",
            "source": "https://github.com/OpenMask3D/openmask3d",
            "why_relevant": (
                "Directly tests whether class-agnostic 3D instance masks and CLIP mask features "
                "reduce the detector recall/false-positive bottleneck seen in E003."
            ),
            "first_use_in_this_project": (
                "Resume only after deciding whether to repair the Docker/MinkowskiEngine blocker "
                "or run an alternative container route."
            ),
            "known_blocker": (
                "Local E003-M71/M72 Docker build failed on MinkowskiEngine dependency setup."
                if openmask_blocked
                else "No current blocker recorded, but environment is still high risk."
            ),
            "fallback_if_blocked": "DualMap or ConceptGraphs transition first; keep OpenMask3D as later proposal baseline",
            "e004_claim_alignment": 2,
            "artifact_fit": 5,
            "implementation_feasibility": 1 if openmask_blocked else 2,
            "top_tier_reviewer_value": 4,
            "direction_b_value": 3,
            "immediate_executable_value": 1 if openmask_blocked else 2,
        },
        {
            "baseline": "HOV-SG",
            "family": "hierarchical_open_vocabulary_scene_graph",
            "role": "Hierarchy/navigation-oriented mapping baseline",
            "source": "https://github.com/hovsg/HOV-SG",
            "why_relevant": (
                "Represents floors, rooms, and objects in a hierarchy and targets language-grounded robot navigation."
            ),
            "first_use_in_this_project": (
                "Use after E005 if the paper expands from object-level memory trust to room/floor-level search decisions."
            ),
            "known_blocker": "Requires Habitat/HM3D-style pipeline and hierarchy construction; less direct for current 3RScan query rows.",
            "fallback_if_blocked": "ConceptGraphs object-level graph baseline",
            "e004_claim_alignment": 3,
            "artifact_fit": 2,
            "implementation_feasibility": 2,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 5,
            "immediate_executable_value": 1,
        },
        {
            "baseline": "DualMap-light ablation",
            "family": "internalized_dynamic_mapping_baseline",
            "role": "Paper-safe fallback if full DualMap code integration blocks",
            "source": "derived_adapter_from_DualMap_problem_contract",
            "why_relevant": (
                "Implements only the comparable global/local memory decision interface using current E004 rows, "
                "without claiming to reproduce DualMap."
            ),
            "first_use_in_this_project": (
                "Define as a fallback ablation only after attempting official DualMap interface audit."
            ),
            "known_blocker": "Not an external baseline; must be labeled as an internal ablation, not DualMap reproduction.",
            "fallback_if_blocked": "N/A",
            "e004_claim_alignment": 4,
            "artifact_fit": 5,
            "implementation_feasibility": 5,
            "top_tier_reviewer_value": 1,
            "direction_b_value": 2,
            "immediate_executable_value": 4,
        },
        {
            "baseline": "VLFM",
            "family": "navigation_search_policy",
            "role": "Navigation/search baseline for later SR/SPL claims",
            "source": "https://github.com/rai-opensource/vlfm",
            "why_relevant": (
                "Connects vision-language maps to frontier-based semantic navigation and real ObjectNav metrics."
            ),
            "first_use_in_this_project": (
                "Defer until simulator/navmesh/episode definitions exist; use as navigation baseline for Direction B."
            ),
            "known_blocker": "Current project has query-level search rows, not Habitat navigation episodes.",
            "fallback_if_blocked": "HM3D-OVON modular baseline",
            "e004_claim_alignment": 2,
            "artifact_fit": 1,
            "implementation_feasibility": 3,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 4,
            "immediate_executable_value": 2,
        },
        {
            "baseline": "HM3D-OVON",
            "family": "open_vocabulary_navigation_benchmark",
            "role": "Benchmark route for later real navigation/open-vocabulary ObjectNav claims",
            "source": "https://github.com/naokiyokoyama/ovon",
            "why_relevant": "Large open-vocabulary ObjectNav benchmark with free-form language goals.",
            "first_use_in_this_project": "Defer until navigation episodes and simulator-backed evaluation are in scope.",
            "known_blocker": "Not compatible with current 3RScan dynamic-pair rows without a separate Habitat route.",
            "fallback_if_blocked": "GOAT-Bench or VLFM-only comparison",
            "e004_claim_alignment": 1,
            "artifact_fit": 1,
            "implementation_feasibility": 3,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 4,
            "immediate_executable_value": 1,
        },
        {
            "baseline": "GOAT-Bench",
            "family": "lifelong_navigation_benchmark",
            "role": "Benchmark route for multi-goal memory/navigation claims",
            "source": "https://github.com/Ram81/goat-bench",
            "why_relevant": (
                "Tests sequential open-vocabulary goals and memory reuse, which matches the long-term Direction B story."
            ),
            "first_use_in_this_project": "Defer until the method has a simulator navigation interface.",
            "known_blocker": "Requires Habitat-style lifelong navigation episodes rather than current query rows.",
            "fallback_if_blocked": "HM3D-OVON single-goal ObjectNav",
            "e004_claim_alignment": 2,
            "artifact_fit": 1,
            "implementation_feasibility": 2,
            "top_tier_reviewer_value": 5,
            "direction_b_value": 5,
            "immediate_executable_value": 1,
        },
        {
            "baseline": "3D-Mem",
            "family": "scene_memory",
            "role": "Scene memory/reasoning baseline",
            "source": "https://openaccess.thecvf.com/content/CVPR2025/papers/Yang_3D-Mem_3D_Scene_Memory_for_Embodied_Exploration_and_Reasoning_CVPR_2025_paper.pdf",
            "why_relevant": (
                "Relevant to embodied scene memory and reasoning, useful for positioning the memory representation."
            ),
            "first_use_in_this_project": (
                "Use as a literature/representation baseline unless code and evaluation interface are confirmed."
            ),
            "known_blocker": "Local intake is currently README-only; executable interface not audited.",
            "fallback_if_blocked": "Literature comparison only",
            "e004_claim_alignment": 3,
            "artifact_fit": 2,
            "implementation_feasibility": 2,
            "top_tier_reviewer_value": 4,
            "direction_b_value": 4,
            "immediate_executable_value": 1,
        },
    ]
    for row in rows:
        row["weighted_score"] = sum(row[key] * weight for key, weight in WEIGHTS.items())
    return sorted(rows, key=lambda row: (-row["weighted_score"], row["baseline"]))


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def write_report(path: Path, coverage: dict, decision: dict, rows: list[dict]) -> None:
    table_lines = [
        "| Rank | Baseline | Family | Score | First use | Known blocker |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        table_lines.append(
            "| {rank} | `{baseline}` | `{family}` | {score} | {first_use} | {blocker} |".format(
                rank=index,
                baseline=row["baseline"],
                family=row["family"],
                score=row["weighted_score"],
                first_use=row["first_use_in_this_project"].replace("|", "/"),
                blocker=row["known_blocker"].replace("|", "/"),
            )
        )

    report = "\n".join(
        [
            "# E005-M01 External Baseline Transition",
            "",
            "## Status",
            "",
            decision["status"],
            "",
            "## 사실",
            "",
            f"- Candidate baselines scored: {coverage['candidate_count']}.",
            f"- Selected first route: `{decision['selected_first_route']}`.",
            f"- Backup route: `{decision['backup_route']}`.",
            f"- E004 memory-trust claim strength: `{coverage['e004_memory_trust_claim_strength']}`.",
            f"- E004 task-context-specific claim strength: `{coverage['e004_task_context_claim_strength']}`.",
            f"- `OpenMask3D` local blocker present: {coverage['openmask3d_blocker_present']}.",
            "",
            "## Candidate Table",
            "",
            *table_lines,
            "",
            "## 논문 주장",
            "",
            "- E005-M01 does not add a new performance claim.",
            "- It fixes the first external-baseline route needed to defend E004 against dynamic semantic mapping and open-vocabulary mapping baselines.",
            "- E004 remains bounded as split-supported memory trust with limited, not label-broad task-context specificity.",
            "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
            "",
            "## 에이전트 추론",
            "",
            "- `DualMap` is selected first because it is the closest external baseline to the current claim: online open-vocabulary dynamic semantic mapping with global/local map roles and dynamic object status.",
            "- `ConceptGraphs` is the most practical fallback because it is a strong open-vocabulary graph mapping baseline over posed RGB-D observations.",
            "- `OpenMask3D` remains important for 3D instance proposals, but the current Docker/MinkowskiEngine blocker makes it a bad immediate blocker for E005.",
            "- `VLFM`, `HM3D-OVON`, and `GOAT-Bench` should wait until simulator-backed navigation episodes are defined.",
            "",
            "## Next",
            "",
            "- E005-M02 DualMap source/interface audit and adapter contract.",
        ]
    )
    path.write_text(report + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    e004_decision = read_json(E004_DECISION)
    openmask_coverage = read_json(E003_OPENMASK_BLOCKER)
    openmask_blocked = openmask_coverage.get("status") == "openmask3d_blocked_direct_denominator_fallback_selected"
    rows = candidate_rows(openmask_blocked=openmask_blocked)
    selected = next(row for row in rows if row["baseline"] == "DualMap")
    backup = next(row for row in rows if row["baseline"] == "ConceptGraphs")
    coverage = {
        "e005_version": "e005_m01_external_baseline_transition_v0",
        "candidate_count": len(rows),
        "e004_decision_path": str(E004_DECISION),
        "e004_memory_trust_claim_strength": e004_decision.get("claim_boundary", {}).get(
            "memory_trust_decision_claim_strength"
        ),
        "e004_task_context_claim_strength": e004_decision.get("claim_boundary", {}).get(
            "task_context_specific_claim_strength"
        ),
        "openmask3d_blocker_path": str(E003_OPENMASK_BLOCKER),
        "openmask3d_blocker_present": openmask_blocked,
        "score_weights": WEIGHTS,
        "selected_first_route": selected["baseline"],
        "backup_route": backup["baseline"],
        "status": "e005_m01_external_baseline_transition_ready",
        "next_recommended_unit": "E005-M02 DualMap source/interface audit and adapter contract",
    }
    decision = {
        "status": coverage["status"],
        "selected_first_route": selected["baseline"],
        "selected_route_family": selected["family"],
        "selected_route_score": selected["weighted_score"],
        "selected_route_first_use": selected["first_use_in_this_project"],
        "selected_route_rationale": selected["why_relevant"],
        "selected_route_known_blocker": selected["known_blocker"],
        "backup_route": backup["baseline"],
        "backup_route_family": backup["family"],
        "backup_route_score": backup["weighted_score"],
        "claim_boundary": {
            "memory_trust_decision_claim_strength": coverage["e004_memory_trust_claim_strength"],
            "task_context_specific_claim_strength": coverage["e004_task_context_claim_strength"],
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "next_recommended_unit": coverage["next_recommended_unit"],
    }
    write_jsonl(OUT_DIR / "candidate_rows.jsonl", rows)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "decision.json", decision)
    write_report(OUT_DIR / "report.md", coverage, decision, rows)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
