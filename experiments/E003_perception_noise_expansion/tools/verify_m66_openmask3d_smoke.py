#!/usr/bin/env python3
"""Verify E003-M66 OpenMask3D staging and smoke-output readiness."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M66_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M66_openmask3d_model_smoke_v0"
VERIFY_VERSION = "e003_m66_openmask3d_smoke_verifier_v0"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def run_optional(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return {"command": command, "returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:], "stdout_tail": proc.stdout[-2000:]}


def build_report(coverage: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M66 OpenMask3D Verifier",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Stage ready: {coverage['stage_ready']}",
            f"- Background status: `{coverage['background_job_status']}`",
            f"- Repo ready: {coverage['openmask3d_repo_ready']}",
            f"- Mask checkpoint ready: {coverage['mask_checkpoint_ready']}",
            f"- SAM checkpoint ready: {coverage['sam_checkpoint_ready']}",
            f"- Raw output files: {coverage['raw_output_file_count']}",
            f"- Prediction file exists: {coverage['prediction_file_exists']}",
            f"- Validator executed: {coverage['validator_executed']}",
            f"- Real RGB-D/open-vocabulary search claim ready: {coverage['real_rgbd_open_vocab_search_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- This verifier can only promote a later claim after model outputs exist and pass schema/matching checks.",
            "- A stage-only pass does not support `OpenMask3D` proposal or search improvement claims.",
            "",
            "## 에이전트 추론",
            "",
            "- If checkpoints are missing, the next action is checkpoint acquisition or an environment-route decision, not claim interpretation.",
            "- If raw `OpenMask3D` outputs exist but no proposal JSONL exists, the next action is adapter implementation.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for verifier execution.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m66-dir", default=DEFAULT_M66_DIR, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[3], type=Path)
    args = parser.parse_args()

    stage_coverage = load_json(args.m66_dir / "stage" / "coverage.json")
    launch_coverage = load_json(args.m66_dir / "launch" / "coverage.json")
    background_status = load_json(args.m66_dir / "background_status.json")
    default_repo_dir = EXPERIMENT_ROOT / "external" / "openmask3d"
    repo_dir = Path(launch_coverage.get("openmask3d_repo_dir", default_repo_dir))
    resources_dir = repo_dir / "resources"
    mask_checkpoint = resources_dir / "openmask3d_arbitrary_scene_model.ckpt"
    sam_checkpoint = resources_dir / "sam_vit_h_4b8939.pth"
    raw_root = args.m66_dir / "openmask3d_raw"
    raw_files = list(raw_root.rglob("*_masks.pt")) + list(raw_root.rglob("*_openmask3d_features.npy"))
    prediction_file = args.m66_dir / "container_output" / "real_proposals.jsonl"

    validator_result: dict[str, Any] | None = None
    validator_executed = False
    if prediction_file.exists():
        validator_executed = True
        validator_result = run_optional(
            [
                "python",
                "experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py",
                "--predictions",
                str(prediction_file),
                "--out-dir",
                str(args.m66_dir / "validator"),
                "--schema-only-smoke",
            ],
            cwd=args.repo_root,
        )

    stage_ready = bool(stage_coverage.get("stage_ready"))
    repo_ready = (repo_dir / "run_openmask3d_single_scene.sh").exists()
    checkpoints_ready = mask_checkpoint.exists() and sam_checkpoint.exists()
    prediction_ready = prediction_file.exists() and (validator_result or {}).get("returncode") == 0
    status = "openmask3d_stage_ready_model_not_run"
    if not stage_ready:
        status = "openmask3d_stage_not_ready"
    elif not repo_ready:
        status = "openmask3d_repo_not_ready"
    elif not checkpoints_ready:
        status = "openmask3d_checkpoints_missing"
    elif raw_files and not prediction_file.exists():
        status = "openmask3d_raw_outputs_ready_adapter_missing"
    elif prediction_ready:
        status = "openmask3d_prediction_schema_ready"

    coverage = {
        "background_job_status": background_status.get("status", launch_coverage.get("background_job_status", "unknown")),
        "launch_coverage": str(args.m66_dir / "launch" / "coverage.json"),
        "mask_checkpoint": str(mask_checkpoint),
        "mask_checkpoint_ready": mask_checkpoint.exists(),
        "openmask3d_repo_dir": str(repo_dir),
        "openmask3d_repo_ready": repo_ready,
        "prediction_file": str(prediction_file),
        "prediction_file_exists": prediction_file.exists(),
        "raw_output_file_count": len(raw_files),
        "raw_output_files": [str(path) for path in raw_files[:20]],
        "real_rgbd_open_vocab_search_claim_ready": prediction_ready,
        "sam_checkpoint": str(sam_checkpoint),
        "sam_checkpoint_ready": sam_checkpoint.exists(),
        "stage_coverage": str(args.m66_dir / "stage" / "coverage.json"),
        "stage_ready": stage_ready,
        "status": status,
        "validator_executed": validator_executed,
        "validator_result": validator_result,
        "verify_version": VERIFY_VERSION,
    }
    out_dir = args.m66_dir / "verification"
    write_json(out_dir / "coverage.json", coverage)
    (out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if stage_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
