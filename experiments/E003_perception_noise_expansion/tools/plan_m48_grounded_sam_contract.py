#!/usr/bin/env python3
"""Plan E003-M48 Grounded-SAM mask-backprojection contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M45_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M45_scaled_candidate_pool_export_replay_v0"
DEFAULT_M47_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M47_external_baseline_feasibility_gate_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M48_grounded_sam_contract_v0"
M48_VERSION = "e003_m48_grounded_sam_contract_v0"
CONTRACT_ID = "grounded_sam_mask_backprojection_contract_v0"
BACKEND_ID = "grounded_sam_mask_backproject_v0"
BASE_BACKEND_ID = "groundingdino_rgbd_backproject_v0"


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


def shell_join(command: list[str]) -> str:
    return " ".join(command)


def baseline_summary(m45: dict[str, Any]) -> dict[str, Any]:
    confidence = ((m45.get("matcher_results") or {}).get("confidence") or {}).get("coverage") or {}
    sqrt_depth = ((m45.get("matcher_results") or {}).get("confidence_sqrt_depth") or {}).get("coverage") or {}
    support = (
        ((m45.get("matcher_results") or {}).get("confidence_sqrt_depth_support_temporal_v0") or {}).get("coverage")
        or {}
    )
    return {
        "baseline_artifact": str(DEFAULT_M45_DIR),
        "box_depth_confidence": {
            "false_positive_proposal_rows": confidence.get("false_positive_proposal_rows"),
            "matched_target_rows": confidence.get("matched_target_rows"),
            "mean_matched_centroid_error_m": (confidence.get("matched_centroid_error_m") or {}).get("mean"),
            "proposal_precision": confidence.get("proposal_precision_smoke"),
            "scan_target_recall": confidence.get("scan_target_recall_smoke"),
        },
        "box_depth_confidence_sqrt_depth": {
            "false_positive_proposal_rows": sqrt_depth.get("false_positive_proposal_rows"),
            "matched_target_rows": sqrt_depth.get("matched_target_rows"),
            "mean_matched_centroid_error_m": (sqrt_depth.get("matched_centroid_error_m") or {}).get("mean"),
            "proposal_precision": sqrt_depth.get("proposal_precision_smoke"),
            "scan_target_recall": sqrt_depth.get("scan_target_recall_smoke"),
        },
        "box_depth_support_aware_failed": {
            "false_positive_proposal_rows": support.get("false_positive_proposal_rows"),
            "matched_target_rows": support.get("matched_target_rows"),
            "proposal_precision": support.get("proposal_precision_smoke"),
        },
        "frozen_m45_verdict": (m45.get("frozen_interpretation_contract_verdict") or {}).get("verdict"),
    }


def build_optional_fields() -> list[dict[str, Any]]:
    return [
        {
            "field": "geometry_source",
            "type": "string",
            "value": "mask_depth_backprojection_v0",
            "purpose": "separate mask-depth geometry from previous box-depth geometry",
        },
        {
            "field": "mask_backend_id",
            "type": "string",
            "value": "sam_box_prompt_v0",
            "purpose": "record the segmentation backend used after GroundingDINO boxes",
        },
        {
            "field": "mask_area_px",
            "type": "integer",
            "purpose": "2D mask area before depth filtering",
        },
        {
            "field": "mask_depth_valid_pixel_count",
            "type": "integer",
            "purpose": "valid positive depth pixels inside the mask",
        },
        {
            "field": "mask_depth_valid_ratio",
            "type": "number",
            "purpose": "valid depth pixels divided by mask area",
        },
        {
            "field": "mask_backprojection_policy",
            "type": "string",
            "value": "median_mad_trimmed_mask_depth_v0",
            "purpose": "freeze robust depth filtering and centroid estimation policy",
        },
        {
            "field": "mask_centroid_world_m",
            "type": "array[number]",
            "purpose": "mask-depth centroid in scan/world coordinates",
        },
        {
            "field": "bbox_centroid_world_m",
            "type": "array[number]",
            "purpose": "paired diagnostic centroid from previous bbox-depth route",
        },
        {
            "field": "mask_support_point_sample_path",
            "type": "string|null",
            "purpose": "optional path to sampled world points for later debugging without bloating JSONL",
        },
    ]


def build_contract(schema: dict[str, Any], m47: dict[str, Any], m45: dict[str, Any]) -> dict[str, Any]:
    required_fields = sorted((schema.get("required_fields") or {}).keys())
    optional_fields = build_optional_fields()
    log_template = (
        "ts=$(date +%Y%m%d_%H%M%S); "
        "tmux new-session -d -s e003_m49_grounded_sam "
        "\"cd {repo} && "
        "mkdir -p logs && "
        "python experiments/E003_perception_noise_expansion/tools/run_m49_grounded_sam_smoke.py "
        "--out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0 "
        "--max-scans 1 --max-frames-per-scan 2 --max-labels 12 "
        "> logs/${{ts}}_e003_m49_grounded_sam_smoke.log 2>&1\""
    ).format(repo=REPO_ROOT)
    return {
        "allowed_inputs": [
            "posed RGB frames from 3RScan sequence payload",
            "registered depth frames from the same sequence payload",
            "camera pose and intrinsics from the sequence payload",
            "M17 prompt labels and prompt set id",
            "GroundingDINO boxes, labels, and confidence scores",
            "SAM masks produced from the same RGB frame and detector boxes",
        ],
        "baseline_to_compare": baseline_summary(m45),
        "blocked_inputs": [
            "3DSSG object instance ids during proposal generation",
            "M17 evaluation target ids during proposal generation",
            "candidate_is_target",
            "matched_3dssg_instance_id before M21 matching",
            "future frames outside the selected scan/frame budget",
            "heldout matching labels or target locations as detector prompts beyond the fixed M17 prompt set",
        ],
        "comparison_policy": {
            "primary_comparison": "same scan/frame subset versus current bbox-depth GroundingDINO route",
            "success_signal": [
                "validator errors == 0",
                "M21 matcher completes",
                "non-empty proposal rows",
                "matched targets are not lower than the same-subset bbox-depth route or mean matched centroid error decreases",
                "false-positive rows do not increase on the same subset",
            ],
            "unsupported_after_pass": [
                "final real RGB-D/open-vocabulary robustness",
                "real navigation SR/SPL",
                "deployable search policy",
                "claim that SAM solves detector label false positives",
            ],
        },
        "contract_id": CONTRACT_ID,
        "detector_backend": {
            "base_detector_backend_id": BASE_BACKEND_ID,
            "new_backend_id": BACKEND_ID,
            "segmentation_backend": "SAM",
            "selected_by_m47": m47.get("selected_route"),
        },
        "implementation_route": {
            "preferred_edit_points": [
                "experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py",
                "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py or a thin M49 wrapper",
            ],
            "runner_args_to_add": [
                "--detector grounded_sam_mask_backproject_v0",
                "--segmentation-backend sam_vit_b",
                "--mask-depth-filter median_mad_trimmed_mask_depth_v0",
                "--mask-min-depth-valid-pixels 200",
                "--mask-point-sample-cap 2048",
            ],
            "do_not_start_with": [
                "OpenMask3D scene conversion",
                "ConceptGraphs full map build",
                "HOV-SG navigation/hierarchy pipeline",
            ],
        },
        "long_running_policy": {
            "background_required_for": [
                "SAM checkpoint download",
                "Docker build with segmentation dependencies",
                "multi-scan mask generation",
            ],
            "log_dir": "logs/",
            "tmux_template": log_template,
            "verification_command": (
                "python -m json.tool "
                "experiments/E003_perception_noise_expansion/artifacts/E003-M49_grounded_sam_smoke_v0/coverage.json"
            ),
        },
        "mask_backprojection_steps": [
            "run GroundingDINO as the current backend does",
            "run SAM with each detector box as a box prompt",
            "resize mask to depth frame coordinates",
            "keep finite positive depth pixels inside the mask",
            "apply robust median/MAD or percentile depth trimming",
            "backproject valid mask pixels with intrinsics and pose",
            "write mask centroid and optional sampled support points",
            "preserve the existing real_proposal_prediction_jsonl_v0 required fields",
            "run the existing validator and M21 matcher",
        ],
        "output_contract": {
            "optional_fields_added": optional_fields,
            "required_fields_preserved": required_fields,
            "schema_id": schema.get("schema_id"),
        },
        "smoke_scope": {
            "max_frames_per_scan": 2,
            "max_labels": 12,
            "max_predictions": 400,
            "max_scans": 1,
            "reason": "verify schema, depth/mask geometry, and matcher compatibility before any long multi-scan run",
        },
    }


def build_coverage(contract: dict[str, Any], schema: dict[str, Any], m47: dict[str, Any]) -> dict[str, Any]:
    selected_grounded_sam = m47.get("selected_route") == "Grounded-SAM"
    required_fields = set((schema.get("required_fields") or {}).keys())
    required_ready = {
        field: field in required_fields
        for field in [
            "bbox_2d",
            "centroid_world_m",
            "confidence",
            "depth_valid_pixel_count",
            "detector_id",
            "frame_ids",
            "label_canonical",
            "mask_rle",
            "proposal_uid",
            "scan_id",
        ]
    }
    contract_ready = selected_grounded_sam and all(required_ready.values())
    return {
        "backend_id": BACKEND_ID,
        "contract_id": CONTRACT_ID,
        "contract_ready": contract_ready,
        "docker_run_executed": False,
        "m47_selected_route": m47.get("selected_route"),
        "m48_version": M48_VERSION,
        "next_recommended_unit": "E003-M49 Grounded-SAM Docker/model smoke implementation",
        "optional_field_count": len(contract["output_contract"]["optional_fields_added"]),
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "required_schema_fields_ready": required_ready,
        "smoke_run_ready": False,
        "status": "grounded_sam_contract_ready" if contract_ready else "grounded_sam_contract_blocked",
    }


def build_report(coverage: dict[str, Any], contract: dict[str, Any]) -> str:
    baseline = contract["baseline_to_compare"]["box_depth_confidence"]
    return "\n".join(
        [
            "# E003-M48 Grounded-SAM Contract",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Selected backend id: `{coverage['backend_id']}`.",
            f"- Contract id: `{coverage['contract_id']}`.",
            f"- M47 selected route: `{coverage['m47_selected_route']}`.",
            f"- Existing schema id: `{contract['output_contract']['schema_id']}`.",
            f"- Existing required fields preserved: {all(coverage['required_schema_fields_ready'].values())}.",
            f"- Optional mask diagnostic fields added: {coverage['optional_field_count']}.",
            f"- M45 bbox-depth confidence baseline: matched {baseline['matched_target_rows']}, false positives {baseline['false_positive_proposal_rows']}, precision {baseline['proposal_precision']}.",
            f"- Docker/model smoke executed: {coverage['docker_run_executed']}.",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M48 does not create a new result claim.",
            "- It fixes the contract needed to test whether mask-depth backprojection is better than box-depth backprojection for proposal geometry.",
            "",
            "## 에이전트 추론",
            "",
            "- `Grounded-SAM` is the correct first external implementation route because it minimally changes the current `GroundingDINO` runner while directly isolating the box-depth projection bottleneck.",
            "- `OpenMask3D`, `ConceptGraphs`, and `HOV-SG` should remain later baselines after this proposal-quality bottleneck is understood.",
            "- A successful M49 smoke would justify a same-subset comparison against the current M45/M33 box-depth baseline, but not a final robustness claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E003-M49. The next unit should implement a short Docker/model smoke from this contract.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m45-dir", default=DEFAULT_M45_DIR, type=Path)
    parser.add_argument("--m47-dir", default=DEFAULT_M47_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = load_json(args.m17_dir / "proposal_output_schema.json")
    m45 = load_json(args.m45_dir / "coverage.json")
    m47 = load_json(args.m47_dir / "coverage.json")

    contract = build_contract(schema=schema, m47=m47, m45=m45)
    coverage = build_coverage(contract=contract, schema=schema, m47=m47)

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "contract.json", contract)
    write_jsonl(args.out_dir / "optional_fields.jsonl", contract["output_contract"]["optional_fields_added"])
    write_text(args.out_dir / "report.md", build_report(coverage, contract))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if coverage["contract_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
