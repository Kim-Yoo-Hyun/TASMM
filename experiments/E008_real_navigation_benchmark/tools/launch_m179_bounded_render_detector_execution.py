#!/usr/bin/env python3
"""Launch E008-M179 bounded source-pool render or detector jobs."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M178_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M179_bounded_render_detector_execution_verification_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M178_navmesh_snap_render_detector_launcher_contract_v0"
)
RENDER_SESSION = "e008_m179_source_pool_render"
DETECTOR_SESSION = "e008_m179_source_pool_detector"
VERSION = "e008_m179_bounded_render_detector_launch_v0"


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


def tmux_running(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def command_status(command: str) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True, shell=True)
    except Exception as exc:  # noqa: BLE001 - launch artifact should record failures.
        return {"available": False, "returncode": None, "stdout": "", "stderr": repr(exc)}
    return {
        "available": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def command_row(job_id: str) -> dict[str, Any]:
    for row in read_jsonl(M178_ARTIFACT_DIR / "long_job_command_rows.jsonl"):
        if row.get("job_id") == job_id:
            return row
    return {}


def render_ready() -> bool:
    coverage = read_json(ARTIFACT_DIR / "render_verification_coverage.json")
    return str(coverage.get("status")) in {
        "e008_m179_render_ready",
        "e008_m179_render_ready_with_depth_filtered_frames",
    }


def detector_ready() -> bool:
    coverage = read_json(ARTIFACT_DIR / "detector_verification_coverage.json")
    return str(coverage.get("status")) == "e008_m179_detector_candidate_source_ready"


def select_stage(stage: str) -> str:
    if stage != "auto":
        return stage
    if detector_ready():
        return "none"
    if render_ready():
        return "detector"
    return "render"


def build_report(coverage: dict[str, Any], preflight_rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M179 Bounded Render/Detector Launch",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Stage: `{coverage['stage']}`.",
            f"- tmux session: `{coverage.get('tmux_session')}`.",
            f"- Log path: `{coverage.get('log_path')}`.",
            f"- Output path: `{coverage.get('output_path')}`.",
            f"- Launch executed: {str(coverage['launch_executed']).lower()}.",
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
            "- M179 launch only starts bounded render/detector jobs.",
            "- Detector, goal-evaluation, trajectory, and protected-baseline claims require downstream verification.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["auto", "render", "detector"], default="auto")
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    stage = select_stage(args.stage)
    m178 = read_json(M178_ARTIFACT_DIR / "coverage.json")
    render_plan_rows = read_jsonl(DATA_OUT_DIR / "render_inputs" / "render_plan_rows.jsonl")
    detector_manifest_rows = read_jsonl(DATA_OUT_DIR / "detector_inputs" / "real_proposal_query_manifest.jsonl")
    render_row = command_row("E008-M179-render")
    detector_row = command_row("E008-M179-detector")
    if stage == "render":
        job_row = render_row
        session = RENDER_SESSION
        preflight_rows = [
            {
                "gate_id": "m178_ready",
                "gate_status": "pass" if m178.get("m179_gate_ready") else "fail",
                "details": m178.get("status"),
            },
            {
                "gate_id": "render_plan_rows_ready",
                "gate_status": "pass" if render_plan_rows else "fail",
                "details": len(render_plan_rows),
            },
            {
                "gate_id": "tmux_session_free",
                "gate_status": "pass" if not tmux_running(RENDER_SESSION) else "fail",
                "details": RENDER_SESSION,
            },
        ]
    elif stage == "detector":
        job_row = detector_row
        session = DETECTOR_SESSION
        preflight_rows = [
            {
                "gate_id": "render_ready",
                "gate_status": "pass" if render_ready() else "fail",
                "details": read_json(ARTIFACT_DIR / "render_verification_coverage.json").get("status"),
            },
            {
                "gate_id": "detector_manifest_rows_ready",
                "gate_status": "pass" if detector_manifest_rows else "fail",
                "details": len(detector_manifest_rows),
            },
            {
                "gate_id": "tmux_session_free",
                "gate_status": "pass" if not tmux_running(DETECTOR_SESSION) else "fail",
                "details": DETECTOR_SESSION,
            },
        ]
    else:
        job_row = {}
        session = None
        preflight_rows = [
            {
                "gate_id": "m179_already_ready",
                "gate_status": "pass" if detector_ready() else "fail",
                "details": read_json(ARTIFACT_DIR / "detector_verification_coverage.json").get("status"),
            }
        ]

    blockers = [row["gate_id"] for row in preflight_rows if row["gate_status"] == "fail"]
    launch_result: dict[str, Any] | None = None
    launch_executed = False
    if stage in {"render", "detector"} and not blockers:
        launch_result = command_status(str(job_row.get("command")))
        launch_executed = bool(launch_result.get("available"))
    status = (
        f"e008_m179_{stage}_launched"
        if launch_executed
        else "e008_m179_already_ready"
        if stage == "none"
        else f"e008_m179_{stage}_launch_blocked_or_failed"
    )
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "stage": stage,
        "blockers": blockers,
        "launch_executed": launch_executed,
        "launch_result": launch_result,
        "tmux_session": session,
        "tmux_running_after_launch": tmux_running(session) if session else False,
        "log_path": job_row.get("log_path") if job_row else None,
        "output_path": job_row.get("output_path") if job_row else None,
        "working_directory": str(ROOT),
        "command": job_row.get("command") if job_row else None,
        "render_plan_rows": len(render_plan_rows),
        "detector_manifest_rows": len(detector_manifest_rows),
        "selected_next_unit": "E008-M179 completion verification",
        "real_navigation_sr_spl_ready": False,
    }
    write_json(ARTIFACT_DIR / f"{stage}_launch_coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / f"{stage}_launch_preflight_rows.jsonl", preflight_rows)
    write_text(ARTIFACT_DIR / f"{stage}_launch_report.md", build_report(coverage, preflight_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_executed or stage == "none" else 2


if __name__ == "__main__":
    raise SystemExit(main())
