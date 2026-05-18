#!/usr/bin/env python3
"""Audit DualMap source/interface fit and define the E004 adapter contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M02_dualmap_interface_audit_v0"
)
M01_DECISION = (
    ROOT
    / "experiments"
    / "E005_external_baseline_transition"
    / "artifacts"
    / "E005-M01_external_baseline_transition_v0"
    / "decision.json"
)
E004_DECISION = (
    ROOT
    / "experiments"
    / "E004_task_context_memory_trust"
    / "artifacts"
    / "E004-M05_scale_split_stress_v0"
    / "decision.json"
)


DUALMAP_MAIN_COMMIT = "157235ec49e6a1f439babbc571c4c02ad1f06aa9"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_audit() -> dict:
    return {
        "official_repo": "https://github.com/Eku127/DualMap",
        "project_page": "https://eku127.github.io/DualMap/",
        "paper": "https://arxiv.org/abs/2506.01950",
        "main_commit_checked": DUALMAP_MAIN_COMMIT,
        "license": "Apache-2.0",
        "clone_command": (
            "git clone --branch main --single-branch --recurse-submodules "
            "git@github.com:Eku127/DualMap.git"
        ),
        "tested_environment_from_readme": {
            "os": "Ubuntu 22.04",
            "ros": "ROS 2 Humble",
            "python": "3.10",
        },
        "input_modes": [
            "Dataset Mode",
            "ROS streams / rosbag files",
            "Record3D iPhone stream",
            "Online simulation via Habitat Data Collector",
        ],
        "dataset_mode_supported_sources": [
            "Replica",
            "ScanNet",
            "TUM RGB-D",
            "self-collected data using Habitat Data Collector",
        ],
        "dataset_mode_required_layouts": [
            "RGB-D frame directory",
            "trajectory or pose files",
            "intrinsic files for ScanNet-style export",
            "optional semantic mesh / ground truth for evaluation",
        ],
        "runner_commands": {
            "dataset": "python -m applications.runner_dataset",
            "offline_query": "python -m applications.offline_local_map_query",
            "semseg_eval": "python -m evaluation.sem_seg_eval",
            "ros": "python -m applications.runner_ros",
        },
        "documented_outputs": [
            "output/map_results/<scene>/map/*.pkl",
            "output/map_results/<scene>/map/layout.pcd",
            "output/map_results/<scene>/detections/",
            "output/map_results/<scene>/detector_time.csv",
            "output/map_results/<scene>/system_time.csv",
            "output/map_results/eval/results.json",
            "offline query example map/viewpoint.json",
        ],
        "major_dependencies": [
            "MobileCLIP submodule",
            "open_clip_torch",
            "YOLO / ultralytics",
            "FastSAM or segmentation frontend",
            "Open3D",
            "Rerun",
            "FAISS CPU",
            "ROS 1/2 for ROS route",
            "Habitat Data Collector for simulation navigation route",
            "Hugging Face model access for CLIP weights unless cached locally",
        ],
        "official_facts_used": [
            {
                "fact": "DualMap supports dataset, ROS/rosbag, and Record3D input modes.",
                "source": "https://github.com/Eku127/DualMap",
            },
            {
                "fact": "Dataset mode supports Replica, ScanNet, TUM RGB-D, and self-collected Habitat Data Collector data.",
                "source": "https://github.com/Eku127/DualMap/blob/main/resources/doc/app_runner_dataset.md",
            },
            {
                "fact": "Dataset output contains object representation PKLs, layout point cloud, detection outputs, and timing CSVs.",
                "source": "https://github.com/Eku127/DualMap/blob/main/resources/doc/app_runner_dataset.md",
            },
            {
                "fact": "Offline query consumes a map directory containing object PKLs, layout.pcd, and viewpoint.json.",
                "source": "https://github.com/Eku127/DualMap/blob/main/resources/doc/app_offline_query.md",
            },
            {
                "fact": "Simulation navigation depends on Habitat Data Collector and ROS2.",
                "source": "https://github.com/Eku127/DualMap/blob/main/resources/doc/app_simulation.md",
            },
        ],
    }


def adapter_contract() -> dict:
    return {
        "contract_version": "dualmap_to_e004_candidate_adapter_v0",
        "purpose": (
            "Convert DualMap map/query outputs into E004-compatible candidate rows so the "
            "E004 memory-trust decision layer can be compared against a dynamic semantic "
            "mapping baseline without leaking target identity or success labels."
        ),
        "source_options": {
            "preferred": "DualMap dataset-mode map output from 3RScan-style RGB-D sequence staging",
            "fallback": "DualMap offline-query example output schema inspection without performance claim",
            "not_allowed_as_external_baseline": "DualMap-light ablation unless clearly labeled as internal ablation",
        },
        "minimum_required_dualmap_fields": [
            "object/map element id",
            "text label or queryable semantic descriptor",
            "world-frame centroid or representative location",
            "similarity / confidence / retrieval score",
            "map source scene id",
            "observation/frame support or last-seen metadata if available",
        ],
        "e004_candidate_fields_to_emit": [
            "query_row_uid",
            "base_row_uid",
            "current_rescan_id",
            "task_context_id",
            "query_text",
            "target_label_canonical",
            "candidate_source",
            "candidate_object_id",
            "candidate_label",
            "candidate_centroid_m",
            "candidate_score",
            "candidate_rank",
            "candidate_visit_order",
            "candidate_expected_search_cost",
            "candidate_path_cost_m",
            "old_memory_distance_m",
            "source_quality",
            "memory_trust_feature_bundle",
        ],
        "allowed_policy_inputs": [
            "query text / label",
            "structured task context",
            "DualMap retrieval score",
            "candidate centroid",
            "candidate visit order",
            "candidate path/search cost if available before evaluation",
            "staleness and old-memory distance features from E004",
            "source quality and observation support available before success evaluation",
        ],
        "blocked_leakage_inputs": [
            "target_uid",
            "target detected flag",
            "target rank",
            "target match distance",
            "success labels",
            "false positives before target",
            "evaluation-only dead-end labels",
            "ground-truth current object identity not available to the policy",
        ],
        "primary_comparison": [
            "E004 task_context_memory_trust_reobserve_v0 on current detector proposals",
            "DualMap-derived candidate visit order",
            "context-agnostic memory trust baseline",
            "static old-memory baseline",
        ],
        "metrics": [
            "proxy SR",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "stale old-location return rate",
            "target detected / candidate available rate",
            "failure class: source unavailable vs rank/cost failure vs policy failure",
        ],
        "claim_boundary": {
            "performance_claim_ready": False,
            "external_baseline_comparison_ready": False,
            "adapter_contract_ready": True,
            "real_navigation_sr_spl_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        },
    }


def decision(source: dict, contract: dict, m01: dict, e004: dict) -> dict:
    direct_drop_in = False
    dataset_route_feasible = True
    external_baseline_ready = False
    selected_next = "E005-M03 DualMap 3RScan dataset-format staging feasibility"
    blockers = [
        "DualMap output object PKL schema must be inspected before candidate conversion.",
        "3RScan RGB-D sequences must be staged into a DualMap-supported Dataset Mode layout.",
        "DualMap official baseline cannot be run directly on E004 JSONL rows.",
        "Navigation claims require ROS2/Habitat Data Collector or a separate simulator route.",
        "Hugging Face / MobileCLIP / YOLO / FastSAM weights may require cached downloads.",
    ]
    return {
        "status": "e005_m02_dualmap_interface_audit_ready_with_staging_required",
        "selected_route": m01.get("selected_first_route", "DualMap"),
        "backup_route": m01.get("backup_route", "ConceptGraphs"),
        "source_commit": source["main_commit_checked"],
        "official_license": source["license"],
        "direct_drop_in_to_e004_jsonl": direct_drop_in,
        "dataset_mode_staging_route_feasible": dataset_route_feasible,
        "external_baseline_comparison_ready": external_baseline_ready,
        "adapter_contract_ready": contract["claim_boundary"]["adapter_contract_ready"],
        "blockers": blockers,
        "claim_boundary": {
            "memory_trust_decision_claim_strength": e004.get("claim_boundary", {}).get(
                "memory_trust_decision_claim_strength"
            ),
            "task_context_specific_claim_strength": e004.get("claim_boundary", {}).get(
                "task_context_specific_claim_strength"
            ),
            "dualmap_performance_claim_ready": False,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
        },
        "next_recommended_unit": selected_next,
    }


def write_report(path: Path, source: dict, contract: dict, decision_data: dict) -> None:
    lines = [
        "# E005-M02 DualMap Interface Audit",
        "",
        "## Status",
        "",
        decision_data["status"],
        "",
        "## 사실",
        "",
        f"- Official repo: `{source['official_repo']}`.",
        f"- Checked main commit: `{source['main_commit_checked']}`.",
        f"- License: `{source['license']}`.",
        "- Official input modes: Dataset Mode, ROS streams / rosbags, Record3D, and online simulation via Habitat Data Collector.",
        "- Dataset Mode supports Replica, ScanNet, TUM RGB-D, and self-collected Habitat Data Collector data.",
        "- Documented Dataset Mode output includes object `*.pkl`, `layout.pcd`, optional detections, `detector_time.csv`, and `system_time.csv`.",
        "- Offline query consumes a map directory with object PKLs, `layout.pcd`, and `viewpoint.json`.",
        f"- Direct drop-in to current E004 JSONL rows: {decision_data['direct_drop_in_to_e004_jsonl']}.",
        f"- Dataset-mode staging route feasible: {decision_data['dataset_mode_staging_route_feasible']}.",
        f"- Adapter contract ready: {decision_data['adapter_contract_ready']}.",
        f"- External baseline comparison ready: {decision_data['external_baseline_comparison_ready']}.",
        "",
        "## Adapter Contract",
        "",
        f"- Contract version: `{contract['contract_version']}`.",
        f"- Preferred source: {contract['source_options']['preferred']}.",
        f"- Fallback source: {contract['source_options']['fallback']}.",
        "- Required DualMap fields: "
        + ", ".join(f"`{field}`" for field in contract["minimum_required_dualmap_fields"])
        + ".",
        "- Emitted E004 fields: "
        + ", ".join(f"`{field}`" for field in contract["e004_candidate_fields_to_emit"])
        + ".",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in decision_data["blockers"]],
        "",
        "## 논문 주장",
        "",
        "- E005-M02 does not support a `DualMap` performance claim.",
        "- E005-M02 supports an adapter contract and confirms that a fair official `DualMap` comparison requires dataset-format staging.",
        "- E004 claim boundary remains fixed: split-supported memory trust and limited, not label-broad task-context specificity.",
        "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
        "## 에이전트 추론",
        "",
        "- `DualMap` is not a drop-in baseline for E004 JSONL rows because it expects RGB-D streams or dataset layouts and emits map artifacts.",
        "- The most defensible route is to stage selected 3RScan current-rescan sequences into a DualMap-compatible Dataset Mode layout, then convert DualMap map/query outputs into E004 candidate rows.",
        "- If object PKL schema or model dependencies block this route, `ConceptGraphs` remains the fallback external mapping baseline.",
        "- A `DualMap-light ablation` can be useful for debugging but must not be presented as an external baseline.",
        "",
        "## Next",
        "",
        f"- {decision_data['next_recommended_unit']}.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m01 = read_json(M01_DECISION)
    e004 = read_json(E004_DECISION)
    source = source_audit()
    contract = adapter_contract()
    decision_data = decision(source=source, contract=contract, m01=m01, e004=e004)
    coverage = {
        "e005_version": "e005_m02_dualmap_interface_audit_v0",
        "m01_decision_path": str(M01_DECISION),
        "e004_decision_path": str(E004_DECISION),
        "official_repo": source["official_repo"],
        "main_commit_checked": source["main_commit_checked"],
        "license": source["license"],
        "adapter_contract_ready": decision_data["adapter_contract_ready"],
        "dataset_mode_staging_route_feasible": decision_data["dataset_mode_staging_route_feasible"],
        "direct_drop_in_to_e004_jsonl": decision_data["direct_drop_in_to_e004_jsonl"],
        "external_baseline_comparison_ready": decision_data["external_baseline_comparison_ready"],
        "status": decision_data["status"],
        "next_recommended_unit": decision_data["next_recommended_unit"],
    }
    write_json(OUT_DIR / "source_audit.json", source)
    write_json(OUT_DIR / "adapter_contract.json", contract)
    write_json(OUT_DIR / "decision.json", decision_data)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_report(OUT_DIR / "report.md", source, contract, decision_data)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
