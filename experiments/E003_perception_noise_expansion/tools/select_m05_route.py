#!/usr/bin/env python3
"""Select the E003-M05 route after auditing real proposal-source readiness."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_E001_M02_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_M04_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M04_robustness_failure_analysis_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M05_route_v0"
ANALYSIS_VERSION = "e003_m05_route_v0"
SELECTED_CONTROLLED_PROFILE = "annotation_proposal_dropout_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def scan_sequence_status(scan_dir: Path) -> dict[str, Any]:
    sequence_dir = scan_dir / "sequence"
    sequence_zip = scan_dir / "sequence.zip"
    color_frames = set()
    depth_frames = set()
    pose_frames = set()
    if sequence_dir.exists():
        for path in sequence_dir.iterdir():
            name = path.name
            if name.endswith(".color.jpg"):
                color_frames.add(name.replace(".color.jpg", ""))
            elif name.endswith(".depth.pgm"):
                depth_frames.add(name.replace(".depth.pgm", ""))
            elif name.endswith(".pose.txt"):
                pose_frames.add(name.replace(".pose.txt", ""))
    triplet_count = len(color_frames & depth_frames & pose_frames)
    return {
        "scan_id": scan_dir.name,
        "sequence_zip": sequence_zip.exists(),
        "sequence_dir": sequence_dir.exists(),
        "color_frame_count": len(color_frames),
        "depth_frame_count": len(depth_frames),
        "pose_frame_count": len(pose_frames),
        "rgbd_pose_triplet_count": triplet_count,
        "rgbd_sequence_available": sequence_zip.exists() or sequence_dir.exists(),
        "rgbd_triplet_ready": triplet_count > 0,
    }


def discover_sequences(dataset_root: Path) -> dict[str, dict[str, Any]]:
    scans_dir = dataset_root / "3RScan" / "scans"
    if not scans_dir.exists():
        return {}
    return {
        path.name: scan_sequence_status(path)
        for path in sorted(scans_dir.iterdir())
        if path.is_dir()
    }


def discover_proposal_outputs(dataset_root: Path) -> list[str]:
    tokens = ["proposal", "detect", "detection", "open_vocab", "open-vocab", "clip", "sam", "mask"]
    allowed_suffixes = {".json", ".jsonl", ".pkl", ".pickle", ".pt", ".pth", ".npz", ".npy", ".csv"}
    rows = []
    if not dataset_root.exists():
        return rows
    for path in dataset_root.rglob("*"):
        if not path.is_file():
            continue
        lowered = path.name.lower()
        if path.suffix.lower() not in allowed_suffixes:
            continue
        if any(token in lowered for token in tokens):
            rows.append(str(path))
    return sorted(rows)


def build_source_rows(
    query_rows: list[dict[str, Any]],
    sequences: dict[str, dict[str, Any]],
    proposal_outputs: list[str],
) -> list[dict[str, Any]]:
    detector_output_available = len(proposal_outputs) > 0
    rows = []
    for row in query_rows:
        ref_status = sequences.get(row["reference_scan_id"], {})
        rescan_status = sequences.get(row["rescan_id"], {})
        rescan_rgbd_ready = bool(rescan_status.get("rgbd_triplet_ready"))
        rows.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "metadata_split": row["metadata_split"],
                "reference_scan_id": row["reference_scan_id"],
                "rescan_id": row["rescan_id"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "reference_rgbd_sequence_available": bool(ref_status.get("rgbd_sequence_available")),
                "reference_rgbd_triplet_count": ref_status.get("rgbd_pose_triplet_count", 0),
                "rescan_rgbd_sequence_available": bool(rescan_status.get("rgbd_sequence_available")),
                "rescan_rgbd_triplet_count": rescan_status.get("rgbd_pose_triplet_count", 0),
                "rescan_rgbd_ready_for_detector": rescan_rgbd_ready,
                "detector_or_proposal_output_available": detector_output_available,
                "e001_rgbd_ready_flag": bool(row.get("e003_rgbd_ready")),
                "e001_open_vocab_ready_flag": bool(row.get("e003_open_vocab_ready")),
                "real_rgbd_proposal_ready": rescan_rgbd_ready and detector_output_available,
                "real_open_vocab_proposal_ready": bool(row.get("e003_open_vocab_ready")) and detector_output_available,
                "open_vocab_proposal_source": row.get("open_vocab_proposal_source"),
                "route_status": "real_proposal_ready"
                if rescan_rgbd_ready and detector_output_available
                else "blocked_real_proposal_source",
            }
        )
    return rows


def build_profile_contract(query_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "selected_profile": SELECTED_CONTROLLED_PROFILE,
        "selection_reason": "Real RGB-D/open-vocabulary proposal source is blocked; target-drop tests detector proposal-recall sensitivity next.",
        "profile_role": "controlled_proposal_recall_stress",
        "source": "annotation candidates from E001-M02",
        "docker_required": False,
        "docker_reason": "This profile is a repository-local artifact transform; Docker becomes required when a detector/open-vocabulary model is implemented for paper-body experiments.",
        "reference_profile": "clean_annotation_oracle_v0",
        "recommended_seed_set": [11, 17, 23],
        "dropout_policy": {
            "non_target_candidate_drop_rate": 0.25,
            "target_drop_rate": 0.15,
            "preserve_at_least_one_candidate": True,
            "drop_target_rows_reported_separately": True,
        },
        "required_denominators": [
            "all_rows",
            "target_retained_eval",
            "target_dropped_eval",
        ],
        "required_metrics": [
            "proposal_recall",
            "target_dropped_rate",
            "target_retained_eval_SR",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "task utility",
            "stale old-location FP",
        ],
        "primary_rows": len(query_rows),
        "next_executable_unit": "E003-M06_annotation_proposal_dropout_v0",
        "next_expected_outputs": [
            "noise_manifest.jsonl",
            "noisy_query_rows.jsonl",
            "noisy_candidate_rows.jsonl",
            "metrics.json",
            "failure_rows.jsonl",
            "coverage.json",
            "report.md",
        ],
    }


def build_route_decision(
    source_rows: list[dict[str, Any]],
    sequences: dict[str, dict[str, Any]],
    proposal_outputs: list[str],
    m04_claim_boundary: dict[str, Any],
    profile_contract: dict[str, Any],
) -> dict[str, Any]:
    real_rgbd_ready_rows = [row for row in source_rows if row["real_rgbd_proposal_ready"]]
    rescan_rgbd_ready_rows = [row for row in source_rows if row["rescan_rgbd_ready_for_detector"]]
    status = "controlled_stress_selected" if not real_rgbd_ready_rows else "real_proposal_route_ready"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "selected_route": "controlled_annotation_proxy_stress"
        if status == "controlled_stress_selected"
        else "real_rgbd_or_open_vocab_proposal",
        "selected_profile": profile_contract["selected_profile"] if status == "controlled_stress_selected" else None,
        "query_rows": len(source_rows),
        "local_scan_count": len(sequences),
        "local_sequence_scan_count": sum(1 for row in sequences.values() if row["rgbd_sequence_available"]),
        "local_rgbd_triplet_scan_count": sum(1 for row in sequences.values() if row["rgbd_triplet_ready"]),
        "query_rows_with_rescan_rgbd_ready": len(rescan_rgbd_ready_rows),
        "query_rows_with_real_rgbd_proposal_ready": len(real_rgbd_ready_rows),
        "query_rows_with_real_open_vocab_proposal_ready": sum(
            1 for row in source_rows if row["real_open_vocab_proposal_ready"]
        ),
        "proposal_output_files_found": len(proposal_outputs),
        "proposal_output_examples": proposal_outputs[:20],
        "route_status_counts": counter_dict(Counter(row["route_status"] for row in source_rows)),
        "rescan_sequence_status_counts": counter_dict(
            Counter(row["rescan_rgbd_ready_for_detector"] for row in source_rows)
        ),
        "reference_sequence_status_counts": counter_dict(
            Counter(row["reference_rgbd_sequence_available"] for row in source_rows)
        ),
        "blockers": [
            "No detector/proposal output files found under local_dataset.",
            "No current E001 query row has a detector/open-vocabulary proposal source.",
            "No current E001 query row has rescan RGB-D triplets ready for detector execution.",
            "Real detector/open-vocabulary implementation must use Docker under docs/experiments.md.",
        ]
        if status == "controlled_stress_selected"
        else [],
        "m04_boundary_used": {
            "task_significant_routine_proxy_sr_delta": m04_claim_boundary["key_evidence"].get(
                "task_significant_routine_proxy_sr_delta"
            ),
            "target_drop_profiles_included": m04_claim_boundary["key_evidence"].get(
                "target_drop_profiles_included"
            ),
        },
        "next_action": profile_contract["next_executable_unit"]
        if status == "controlled_stress_selected"
        else "dockerized_real_proposal_pipeline_contract",
    }


def build_coverage(
    route_decision: dict[str, Any],
    source_rows: list[dict[str, Any]],
    out_dir: Path,
) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": route_decision["status"],
        "query_rows": len(source_rows),
        "selected_route": route_decision["selected_route"],
        "selected_profile": route_decision["selected_profile"],
        "docker_rule_active_for_real_implementation": True,
        "docker_required_for_selected_route": False
        if route_decision["selected_route"] == "controlled_annotation_proxy_stress"
        else True,
        "outputs": {
            "proposal_source_rows": str(out_dir / "proposal_source_rows.jsonl"),
            "route_decision": str(out_dir / "route_decision.json"),
            "controlled_profile_contract": str(out_dir / "controlled_profile_contract.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    route_decision: dict[str, Any],
    profile_contract: dict[str, Any],
    coverage: dict[str, Any],
    out_dir: Path,
) -> str:
    lines = [
        "# E003-M05 Route Selection",
        "",
        "## Status",
        "",
        route_decision["status"],
        "",
        "## 사실",
        "",
        f"- Query rows: {route_decision['query_rows']}",
        f"- Local sequence scan count: {route_decision['local_sequence_scan_count']}",
        f"- Local RGB-D triplet scan count: {route_decision['local_rgbd_triplet_scan_count']}",
        f"- Query rows with rescan RGB-D ready: {route_decision['query_rows_with_rescan_rgbd_ready']}",
        f"- Query rows with real RGB-D proposal ready: {route_decision['query_rows_with_real_rgbd_proposal_ready']}",
        f"- Query rows with real open-vocabulary proposal ready: {route_decision['query_rows_with_real_open_vocab_proposal_ready']}",
        f"- Proposal output files found: {route_decision['proposal_output_files_found']}",
        f"- Selected route: `{route_decision['selected_route']}`",
        f"- Selected profile: `{route_decision['selected_profile']}`",
        f"- Docker rule active for real implementation: {coverage['docker_rule_active_for_real_implementation']}",
        f"- Docker required for selected route: {coverage['docker_required_for_selected_route']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Blockers",
        "",
    ]
    for item in route_decision["blockers"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Selected Controlled Profile",
            "",
            f"- Profile: `{profile_contract['selected_profile']}`",
            f"- Role: `{profile_contract['profile_role']}`",
            f"- Target drop rate: {profile_contract['dropout_policy']['target_drop_rate']}",
            f"- Non-target candidate drop rate: {profile_contract['dropout_policy']['non_target_candidate_drop_rate']}",
            f"- Required denominators: {', '.join(f'`{item}`' for item in profile_contract['required_denominators'])}",
            f"- Next executable unit: `{profile_contract['next_executable_unit']}`",
            "",
            "## 논문 주장",
            "",
            "- E003-M05 supports choosing the next controlled proposal-recall stress route after real proposal-source audit.",
            "- E003-M05 does not support real RGB-D or open-vocabulary robustness because no detector/proposal source is ready.",
            "",
            "## 에이전트 추론",
            "",
            "- `annotation_proposal_dropout_v0` is the next profile because M04 already tested rank-only noise and explicitly found no target-drop condition.",
            "- Target-drop stress is closer to detector proposal recall failure than false-positive or centroid-only noise.",
            "- Real detector/open-vocabulary implementation should be a Dockerized paper-body experiment, not an ad hoc local script.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for M05 route selection. Continue to E003-M06 controlled proposal-dropout implementation unless real proposal data is staged first.",
            "",
            "## Outputs",
            "",
            "- `proposal_source_rows.jsonl`",
            "- `route_decision.json`",
            "- `controlled_profile_contract.json`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--e001-m02-dir", type=Path, default=DEFAULT_E001_M02_DIR)
    parser.add_argument("--m04-dir", type=Path, default=DEFAULT_M04_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    query_rows = load_jsonl(args.e001_m02_dir / "query_rows.jsonl")
    sequences = discover_sequences(args.dataset_root)
    proposal_outputs = discover_proposal_outputs(args.dataset_root)
    m04_claim_boundary = load_json(args.m04_dir / "claim_boundary.json")
    source_rows = build_source_rows(query_rows, sequences, proposal_outputs)
    profile_contract = build_profile_contract(query_rows)
    route_decision = build_route_decision(
        source_rows,
        sequences,
        proposal_outputs,
        m04_claim_boundary,
        profile_contract,
    )
    coverage = build_coverage(route_decision, source_rows, args.out_dir)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "proposal_source_rows.jsonl", source_rows)
    write_json(args.out_dir / "route_decision.json", route_decision)
    write_json(args.out_dir / "controlled_profile_contract.json", profile_contract)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(
        build_report(route_decision, profile_contract, coverage, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": route_decision["status"],
                "selected_route": route_decision["selected_route"],
                "selected_profile": route_decision["selected_profile"],
                "query_rows_with_rescan_rgbd_ready": route_decision[
                    "query_rows_with_rescan_rgbd_ready"
                ],
                "proposal_output_files_found": route_decision["proposal_output_files_found"],
                "next_action": route_decision["next_action"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
