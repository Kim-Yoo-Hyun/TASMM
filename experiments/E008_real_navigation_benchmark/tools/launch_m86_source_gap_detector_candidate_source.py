#!/usr/bin/env python3
"""Launch E008-M86 source-gap detector candidate-source generation in tmux."""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M84_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
M84_DATA_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M84_source_gap_non_oracle_source_observation_expansion_materialization_smoke_v0"
M86_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_v0"
LAUNCH_DIR = EXP_ROOT / "artifacts" / "E008-M86_source_gap_detector_candidate_source_launch_v0"
LOG_DIR = ROOT / "logs"
DETECTOR_TOOL = ROOT / "experiments" / "E003_perception_noise_expansion" / "tools" / "run_m22_frame_scaling_diagnostics.py"
REAL_SMOKE_IMAGE = "research2/real-smoke:latest"
TMUX_SESSION = "e008_m86_source_gap_detector"
VERSION = "e008_m86_source_gap_detector_candidate_source_launch_v0"
VERIFY_COMMAND = (
    "python experiments/E008_real_navigation_benchmark/tools/verify_m16_non_oracle_observation_expansion_detector_candidate_smoke.py "
    f"--m15-artifact-dir {M84_ARTIFACT_DIR} --m15-data-dir {M84_DATA_DIR} --m16-dir {M86_DIR} "
    f"--tmux-session {TMUX_SESSION} --require-ready"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command_status(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return {
            "available": False,
            "command": command,
            "returncode": None,
            "stderr": str(exc),
            "stdout": "",
        }
    return {
        "available": result.returncode == 0,
        "command": command,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "stdout": result.stdout.strip(),
    }


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in command)


def build_detector_command(log_path: Path) -> tuple[list[str], str, str]:
    inner = [
        "python",
        str(DETECTOR_TOOL),
        "--dataset-root",
        str(M84_DATA_DIR),
        "--m17-dir",
        str(M84_DATA_DIR / "detector_inputs"),
        "--out-dir",
        str(M86_DIR),
        "--max-scans",
        "2",
        "--max-frames-per-scan",
        "96",
        "--max-labels",
        "8",
        "--max-predictions",
        "20000",
        "--max-predictions-per-frame",
        "100",
        "--threshold",
        "0.08",
        "--text-threshold",
        "0.08",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        "confidence_log_depth",
        "--pre-cap-per-scan-label-cap",
        "24",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "100000",
        "--export-pre-cap-candidate-pool",
    ]
    shell_command = f"cd {shlex.quote(str(ROOT))} && {shell_join(inner)} > {shlex.quote(str(log_path))} 2>&1"
    tmux_command = ["tmux", "new-session", "-d", "-s", TMUX_SESSION, shell_command]
    return tmux_command, shell_command, shell_join(inner)


def build_preflight_rows() -> list[dict[str, Any]]:
    m85 = read_json(M84_ARTIFACT_DIR / "m85_verification_coverage.json")
    manifest_rows = read_jsonl(M84_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    object_target_rows = read_jsonl(M84_DATA_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl")
    docker_info = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    image = command_status(["docker", "image", "inspect", REAL_SMOKE_IMAGE, "--format", "{{.Id}}"])
    return [
        {
            "gate_id": "m85_render_verified",
            "gate_status": "pass" if m85.get("status") == "e008_m85_source_gap_render_frame_staging_verified" else "fail",
            "details": m85.get("status"),
        },
        {
            "gate_id": "detector_input_files_ready",
            "gate_status": "pass" if m85.get("detector_input_files_ready") is True else "fail",
            "details": m85.get("detector_input_files_ready"),
        },
        {
            "gate_id": "manifest_rows_ready",
            "gate_status": "pass" if len(manifest_rows) == 2 else "fail",
            "details": len(manifest_rows),
        },
        {
            "gate_id": "object_target_rows_ready",
            "gate_status": "pass" if len(object_target_rows) == 2 else "fail",
            "details": len(object_target_rows),
        },
        {
            "gate_id": "docker_available",
            "gate_status": "pass" if docker_info["available"] else "fail",
            "details": docker_info.get("stdout") or docker_info.get("stderr"),
        },
        {
            "gate_id": "real_smoke_image_available",
            "gate_status": "pass" if image["available"] else "fail",
            "details": REAL_SMOKE_IMAGE,
        },
        {
            "gate_id": "tmux_session_free",
            "gate_status": "pass" if not tmux_running(TMUX_SESSION) else "fail",
            "details": TMUX_SESSION,
        },
    ]


def build_report(coverage: dict[str, Any], preflight_rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M86 Source-Gap Detector Candidate-Source Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- tmux session: `{coverage['tmux_session']}`.",
            f"- Log path: `{coverage['log_path']}`.",
            f"- Output path: `{coverage['output_path']}`.",
            f"- Manifest rows: {coverage['manifest_rows']}.",
            f"- Object target rows: {coverage['object_target_rows']}.",
            f"- Launch executed: {str(coverage['launch_executed']).lower()}.",
            f"- Verification command: `{coverage['verification_command']}`.",
            "",
            "## Preflight",
            "",
            "| gate_id | gate_status | details |",
            "| --- | --- | --- |",
            *[
                f"| {row['gate_id']} | {row['gate_status']} | {row.get('details', '')} |"
                for row in preflight_rows
            ],
            "",
            "## Claim Boundary",
            "",
            "- M86 is a detector candidate-source background launch only.",
            "- M86 launch alone does not support source-gap recovery, real navigation `SR` / `SPL`, deployable search policy, or final RGB-D/open-vocabulary robustness.",
            "",
            "## Next",
            "",
            "- Verify E008-M86 completion before candidate navmesh/source-readiness validation.",
            "",
        ]
    )


def main() -> int:
    LAUNCH_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    M86_DIR.mkdir(parents=True, exist_ok=True)
    preflight_rows = build_preflight_rows()
    blockers = [row["gate_id"] for row in preflight_rows if row["gate_status"] == "fail"]
    manifest_rows = read_jsonl(M84_DATA_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    object_target_rows = read_jsonl(M84_DATA_DIR / "detector_inputs" / "real_proposal_object_targets.jsonl")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}_e008_m86_source_gap_detector.log"
    tmux_command, shell_command, inner_command = build_detector_command(log_path)
    launch_result: dict[str, Any] = {"available": False, "returncode": None, "stdout": "", "stderr": ""}
    launch_executed = False
    status = "e008_m86_source_gap_detector_candidate_source_launch_blocked"
    if not blockers:
        launch_result = command_status(tmux_command)
        launch_executed = bool(launch_result["available"])
        status = (
            "e008_m86_source_gap_detector_candidate_source_launched"
            if launch_executed
            else "e008_m86_source_gap_detector_candidate_source_launch_failed"
        )
    elif tmux_running(TMUX_SESSION) and blockers == ["tmux_session_free"]:
        status = "e008_m86_source_gap_detector_candidate_source_already_running"

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "launch_executed": launch_executed,
        "tmux_session": TMUX_SESSION,
        "tmux_running_after_launch": tmux_running(TMUX_SESSION),
        "working_directory": str(ROOT),
        "output_path": str(M86_DIR),
        "log_path": str(log_path),
        "manifest_rows": len(manifest_rows),
        "object_target_rows": len(object_target_rows),
        "verification_command": VERIFY_COMMAND,
        "tmux_command": tmux_command,
        "shell_command": shell_command,
        "inner_command": inner_command,
        "launch_result": launch_result,
        "detector_candidate_rows_ready": False,
        "source_gap_recovery_evaluated": False,
        "trajectory_execution_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": "E008-M86 completion verification",
    }
    command_rows = [
        {
            "job_id": "E008-M86",
            "job_status": "launched" if launch_executed else status,
            "command": shell_command,
            "tmux_command": shell_join(tmux_command),
            "working_directory": str(ROOT),
            "output_path": str(M86_DIR),
            "log_path": str(log_path),
            "expected_files": [
                "coverage.json",
                "container_output/real_proposals.jsonl",
                "container_output/pre_cap_candidate_pool.jsonl",
                "validator/coverage.json",
                "matching/coverage.json",
            ],
            "verification_command": VERIFY_COMMAND,
        }
    ]
    write_json(LAUNCH_DIR / "launch_coverage.json", coverage)
    write_jsonl(LAUNCH_DIR / "preflight_rows.jsonl", preflight_rows)
    write_jsonl(LAUNCH_DIR / "long_job_command_rows.jsonl", command_rows)
    write_text(LAUNCH_DIR / "report.md", build_report(coverage, preflight_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed or status.endswith("already_running") else 2


if __name__ == "__main__":
    raise SystemExit(main())
