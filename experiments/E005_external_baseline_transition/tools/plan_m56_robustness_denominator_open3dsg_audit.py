#!/usr/bin/env python3
"""Build E005-M56 robustness denominator contract and Open3DSG audit."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
M52_DIR = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0"
M54_DIR = EXP_ROOT / "artifacts" / "E005-M54_paper_table_claim_ledger_v0"
M55_DIR = EXP_ROOT / "artifacts" / "E005-M55_real_rgbd_ov_robustness_gate_v0"
M75_DIR = E003_ROOT / "artifacts" / "E003-M75_expanded_direct_query_bridge_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M56_robustness_denominator_open3dsg_audit_v0"
OPEN3DSG_STAGED = Path("/home/yoohyun/research/local_dataset/Open3DSG_staged")
VERSION = "e005_m56_robustness_denominator_open3dsg_audit_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def count_files(path: Path, suffix: str | None = None) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    count = 0
    for item in path.rglob("*"):
        if item.is_file() and (suffix is None or item.name.endswith(suffix)):
            count += 1
    return count


def count_children(path: Path) -> dict[str, int]:
    if not path.exists() or not path.is_dir():
        return {"entries": 0, "dirs": 0, "files": 0, "symlinks": 0, "broken_symlinks": 0}
    rows = list(path.iterdir())
    symlinks = [row for row in rows if row.is_symlink()]
    return {
        "entries": len(rows),
        "dirs": sum(1 for row in rows if row.is_dir()),
        "files": sum(1 for row in rows if row.is_file()),
        "symlinks": len(symlinks),
        "broken_symlinks": sum(1 for row in symlinks if not row.exists()),
    }


def file_status(path: Path, root: Path) -> dict[str, Any]:
    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = str(path)
    return {
        "relative_path": rel,
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "is_symlink": path.is_symlink(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "readable": os.access(path, os.R_OK),
    }


def safe_head(path: Path, max_lines: int = 32) -> list[str]:
    if not path.exists() or not path.is_file() or not os.access(path, os.R_OK):
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[:max_lines]


def audit_open3dsg() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    staged = OPEN3DSG_STAGED
    h001 = staged / "h001_runtime"
    train = staged / "training_repro"
    source = h001 / "source" / "open3dsg_source"
    runtime_data = h001 / "data" / "3RScan"
    train_data = train / "data" / "3RScan"
    checkpoints = h001 / "output" / "checkpoints"
    features = h001 / "output" / "features"
    datasets = h001 / "output" / "datasets"
    classwise = h001 / "classwise_eval" / "_2026-05-18-08-44"
    eval_metrics = classwise / "eval_metrics.txt"

    required_paths = {
        "staged_root": staged,
        "h001_runtime": h001,
        "training_repro": train,
        "source": source,
        "source_readme": source / "README.md",
        "source_license": source / "LICENSE.md",
        "source_pyproject": source / "pyproject.toml",
        "source_requirements": source / "requirements.txt",
        "runtime_3rscan_data": runtime_data,
        "runtime_3dssg_subset": runtime_data / "3DSSG_subset",
        "runtime_classes": runtime_data / "classes.txt",
        "runtime_relationships": runtime_data / "relationships.txt",
        "runtime_train_boxes": runtime_data / "obj_boxes_train_refined.json",
        "runtime_val_boxes": runtime_data / "obj_boxes_val_refined.json",
        "checkpoints": checkpoints,
        "checkpoint_blip2_positional_embedding": checkpoints / "blip2_positional_embedding.pt",
        "checkpoint_pointnet2_ulip": checkpoints / "pointnet2_ulip.pt",
        "checkpoint_pointnet": checkpoints / "pointnet.pth",
        "output_datasets": datasets,
        "output_opensg_3rscan": datasets / "OpenSG_3RScan",
        "output_opensg_scannet": datasets / "OpenSG_ScanNet",
        "output_features": features,
        "classwise_eval": classwise,
        "classwise_eval_metrics": eval_metrics,
        "training_repro_open3dsg_symlink": train / "open3dsg",
        "training_repro_source_symlink": train / "source" / "open3dsg_source",
    }
    audit_rows = [
        {"check_id": check_id, **file_status(path, staged)}
        for check_id, path in required_paths.items()
    ]

    feature_dirs = []
    if features.exists():
        feature_dirs = sorted(row.name for row in features.iterdir() if row.is_dir())

    source_modules = []
    module_root = source / "open3dsg"
    if module_root.exists():
        source_modules = sorted(row.name for row in module_root.iterdir() if row.is_dir() and not row.name.startswith("__"))

    inventory = {
        "open3dsg_staged_root": str(staged),
        "read_only_policy": {
            "existing_data_modified": False,
            "allowed_use": "read_only_source_interface_audit_and_later_baseline_conversion",
            "artifact_output_root": str(OUT_DIR),
        },
        "access": {
            "root_exists": staged.exists(),
            "root_readable": os.access(staged, os.R_OK),
            "root_writable": os.access(staged, os.W_OK),
            "h001_runtime_exists": h001.exists(),
            "training_repro_exists": train.exists(),
        },
        "layout_counts": {
            "runtime_3rscan_children": count_children(runtime_data),
            "training_3rscan_children": count_children(train_data),
            "checkpoint_files": count_files(checkpoints),
            "feature_files": count_files(features),
            "feature_pt_files": count_files(features, ".pt"),
            "opensg_3rscan_view_pkls": count_files(datasets / "OpenSG_3RScan" / "views", ".pkl"),
            "classwise_eval_files": count_files(classwise),
        },
        "source": {
            "modules": source_modules,
            "has_eval_script": (source / "open3dsg" / "scripts" / "eval.py").exists(),
            "has_run_script": (source / "open3dsg" / "scripts" / "run.py").exists(),
            "has_3rscan_preprocess": (source / "open3dsg" / "data" / "preprocess_3rscan.py").exists(),
            "requirements_head": safe_head(source / "requirements.txt", max_lines=20),
            "readme_head": safe_head(source / "README.md", max_lines=20),
        },
        "feature_dirs": feature_dirs,
        "existing_eval_metrics_head": safe_head(eval_metrics, max_lines=30),
        "baseline_readiness": {
            "source_interface_audit_ready": staged.exists() and source.exists(),
            "existing_eval_artifacts_present": eval_metrics.exists(),
            "checkpoint_artifacts_present": all(
                [
                    (checkpoints / "blip2_positional_embedding.pt").exists(),
                    (checkpoints / "pointnet2_ulip.pt").exists(),
                    (checkpoints / "pointnet.pth").exists(),
                ]
            ),
            "feature_artifacts_present": count_files(features, ".pt") > 0,
            "paper_performance_claim_ready": False,
            "output_to_query_contract_required": True,
        },
    }
    return inventory, audit_rows


def build_denominator_contract(
    m52_metrics: dict[str, Any], m54: dict[str, Any], m75: dict[str, Any], m75_metrics: dict[str, Any]
) -> dict[str, Any]:
    m52_policy = m52_metrics.get("policy_metrics", {})
    m75_policy = m75_metrics.get("policy_metrics", {})
    return {
        "contract_id": "robustness_denominator_contract_v0",
        "principle": "Do not merge proxy-search and real RGB-D proposal denominators into one final robustness table.",
        "tables": [
            {
                "table_id": "A_proxy_search_external_map_v0",
                "status": "ready_with_proxy_boundary",
                "source_artifacts": [
                    "E005-M52_h001_heldout_policy_replay_v0",
                    "E005-M54_paper_table_claim_ledger_v0",
                ],
                "denominator_rows": int(m54.get("query_rows", 0)),
                "methods": [
                    "static_memory_only_v0",
                    "detector_confidence_ranking",
                    "ConceptGraphs-only open-vocabulary map",
                    "context_agnostic_memory_trust_reobserve_v0",
                    "H001 task-conditioned memory trust / re-observation / search-cost policy",
                ],
                "primary_metrics": [
                    "proxy_success_rate",
                    "ExpectedSearchCost",
                    "AttemptSPL",
                    "old_location_dead_end_avoided",
                    "paired H001-only / baseline-only outcomes",
                ],
                "ready_evidence": {
                    "h001_success_rows": m54.get("h001_success_rows"),
                    "conceptgraphs_success_rows": m54.get("conceptgraphs_success_rows"),
                    "static_memory_success_rows": m52_policy.get("static_memory_only_v0", {}).get("query_bridge_success_rows"),
                    "context_agnostic_success_rows": m52_policy.get(
                        "context_agnostic_memory_trust_reobserve_v0", {}
                    ).get("query_bridge_success_rows"),
                },
                "allowed_claim": "H001 improves heldout proxy object-search decisions over static stale memory and ConceptGraphs-only retrieval on the M38 query contract.",
                "forbidden_claim": "H001 is finally robust to real RGB-D/open-vocabulary perception.",
            },
            {
                "table_id": "B_real_rgbd_proposal_bridge_v0",
                "status": "diagnostic_ready_not_final",
                "source_artifacts": [
                    "E003-M75_expanded_direct_query_bridge_v0",
                ],
                "denominator_rows": int(m75.get("direct_bridge_query_rows", 0)),
                "methods": [
                    "detector_confidence_topk",
                    "bounded_old_memory_distance_guard_adaptive_top5_v0",
                    "unbounded_old_memory_distance_guard_until_target_v0",
                ],
                "primary_metrics": [
                    "target_detected_rate",
                    "mean_target_rank_when_detected",
                    "mean_false_positive_before_target_when_detected",
                    "ExpectedSearchCost",
                    "AttemptSPL",
                    "bounded_repair_success_rate",
                ],
                "ready_evidence": {
                    "target_detected_rows": m75.get("query_target_detected_rows"),
                    "target_detected_rate": m75_metrics.get("query_target_detected_rate"),
                    "bounded_repair_success_rows": m75_policy.get(
                        "bounded_old_memory_distance_guard_adaptive_top5_v0", {}
                    ).get("query_bridge_success_rows"),
                    "mean_target_rank_when_detected": m75_metrics.get("mean_target_rank_when_detected"),
                    "mean_false_positive_before_target_when_detected": m75_metrics.get(
                        "mean_false_positive_before_target_when_detected"
                    ),
                },
                "allowed_claim": "The current RGB-D/open-vocabulary proposal bridge diagnoses detector recall, rank, and false-positive pressure.",
                "forbidden_claim": "The current detector bridge proves final open-vocabulary semantic map robustness.",
            },
            {
                "table_id": "C_open3dsg_scene_graph_route_v0",
                "status": "source_interface_audit_only",
                "source_artifacts": [
                    "/home/yoohyun/research/local_dataset/Open3DSG_staged",
                    "E005-M56_robustness_denominator_open3dsg_audit_v0",
                ],
                "denominator_rows": None,
                "methods": [
                    "Open3DSG",
                ],
                "primary_metrics": [
                    "output schema coverage",
                    "query conversion feasibility",
                    "object/relation retrieval joinability",
                    "later proxy-search metrics if conversion succeeds",
                ],
                "ready_evidence": {},
                "allowed_claim": "Open3DSG has a readable staged source/data/eval route that can be audited as a candidate scene-graph baseline.",
                "forbidden_claim": "Open3DSG has already been compared against H001 on H001 query-level metrics.",
            },
        ],
        "minimum_before_final_robustness_claim": [
            "Run at least one additional external baseline route beyond ConceptGraphs through query-level conversion.",
            "Keep detector/proposal failures separate from map-memory decision failures.",
            "Report heldout split, label-group coverage, and failure taxonomy for each table.",
            "Use real RGB-D proposal bridge as diagnostic evidence until its denominator and external baseline conversion are aligned.",
        ],
    }


def build_next_actions(inventory: dict[str, Any]) -> dict[str, Any]:
    route_ready = inventory["baseline_readiness"]["source_interface_audit_ready"]
    return {
        "selected_next_unit": "E005-M57 Open3DSG output schema inspection / query-conversion contract",
        "selected": route_ready,
        "why": [
            "`Open3DSG_staged` is readable and contains source, checkpoints, prepared 3RScan/OpenSG artifacts, and existing eval outputs.",
            "The current audit does not establish H001 query-level comparability.",
            "The next useful step is to inspect output/eval schemas and define how Open3DSG object/relation predictions can be converted to H001 search queries.",
        ],
        "do_not_do_yet": [
            "Do not write into /home/yoohyun/research/local_dataset/Open3DSG_staged.",
            "Do not claim Open3DSG performance against H001 before query-level conversion.",
            "Do not start real navigation SR/SPL before robustness tables are stable.",
        ],
    }


def build_report(
    coverage: dict[str, Any],
    contract: dict[str, Any],
    inventory: dict[str, Any],
    next_actions: dict[str, Any],
) -> str:
    table_a = contract["tables"][0]
    table_b = contract["tables"][1]
    counts = inventory["layout_counts"]
    baseline = inventory["baseline_readiness"]
    return "\n".join(
        [
            "# E005-M56 Robustness Denominator + Open3DSG Audit",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## Facts",
            "",
            f"- `Open3DSG_staged` path: `{inventory['open3dsg_staged_root']}`.",
            f"- Root exists/readable: {inventory['access']['root_exists']} / {inventory['access']['root_readable']}.",
            f"- Existing staged data modified by this step: {inventory['read_only_policy']['existing_data_modified']}.",
            f"- Runtime `3RScan` entries/symlinks/broken symlinks: {counts['runtime_3rscan_children']['entries']} / {counts['runtime_3rscan_children']['symlinks']} / {counts['runtime_3rscan_children']['broken_symlinks']}.",
            f"- Checkpoint files: {counts['checkpoint_files']}; feature `.pt` files: {counts['feature_pt_files']}; `OpenSG_3RScan` view `.pkl` files: {counts['opensg_3rscan_view_pkls']}.",
            f"- Existing `Open3DSG` eval metrics present: {baseline['existing_eval_artifacts_present']}.",
            "",
            "## Denominator Contract",
            "",
            f"- Table A `{table_a['table_id']}`: {table_a['status']}, denominator rows {table_a['denominator_rows']}.",
            f"- Table B `{table_b['table_id']}`: {table_b['status']}, denominator rows {table_b['denominator_rows']}.",
            "- Table C `C_open3dsg_scene_graph_route_v0`: source/interface audit only; no H001 query-level performance claim yet.",
            "",
            "## Open3DSG Baseline Boundary",
            "",
            f"- Source/interface audit ready: {baseline['source_interface_audit_ready']}.",
            f"- Checkpoints present: {baseline['checkpoint_artifacts_present']}.",
            f"- Feature artifacts present: {baseline['feature_artifacts_present']}.",
            f"- Paper performance claim ready: {baseline['paper_performance_claim_ready']}.",
            f"- Output-to-query contract required: {baseline['output_to_query_contract_required']}.",
            "",
            "## Next Action",
            "",
            f"- {next_actions['selected_next_unit']}.",
            "",
        ]
    )


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m52_metrics = read_json(M52_DIR / "metrics.json")
    m54 = read_json(M54_DIR / "coverage.json")
    m55 = read_json(M55_DIR / "coverage.json")
    m75 = read_json(M75_DIR / "coverage.json")
    m75_metrics = read_json(M75_DIR / "metrics.json")

    if m55.get("status") != "e005_m55_real_rgbd_ov_robustness_gate_ready":
        raise RuntimeError(f"M55 is not ready: {m55.get('status')}")
    if not OPEN3DSG_STAGED.exists():
        raise RuntimeError(f"Open3DSG staged root does not exist: {OPEN3DSG_STAGED}")

    inventory, audit_rows = audit_open3dsg()
    contract = build_denominator_contract(m52_metrics, m54, m75, m75_metrics)
    next_actions = build_next_actions(inventory)
    coverage = {
        "status": "e005_m56_robustness_denominator_open3dsg_audit_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m55_status": m55.get("status"),
        "open3dsg_staged_root": str(OPEN3DSG_STAGED),
        "open3dsg_staged_root_exists": inventory["access"]["root_exists"],
        "open3dsg_staged_root_readable": inventory["access"]["root_readable"],
        "existing_open3dsg_data_modified": False,
        "proxy_search_denominator_rows": contract["tables"][0]["denominator_rows"],
        "real_rgbd_proposal_bridge_rows": contract["tables"][1]["denominator_rows"],
        "open3dsg_source_interface_audit_ready": inventory["baseline_readiness"]["source_interface_audit_ready"],
        "open3dsg_query_level_performance_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "selected_next_unit": next_actions["selected_next_unit"],
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "robustness_denominator_contract.json", contract)
    write_json(OUT_DIR / "open3dsg_inventory.json", inventory)
    write_jsonl(OUT_DIR / "open3dsg_audit_rows.jsonl", audit_rows)
    write_json(OUT_DIR / "next_actions.json", next_actions)
    write_text(OUT_DIR / "report.md", build_report(coverage, contract, inventory, next_actions))
    return coverage


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
