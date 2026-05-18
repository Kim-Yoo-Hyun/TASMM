#!/usr/bin/env python3
"""Launch E005-M39 heldout sequence acquisition/staging for ConceptGraphs."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M38_DIR = EXP_ROOT / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M39_conceptgraphs_heldout_sequence_launch_v0"
SCAN_ROOT = ROOT / "local_dataset" / "3RScan" / "scans"
LOG_ROOT = ROOT / "logs"
BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"
VERSION = "e005_m39_conceptgraphs_heldout_sequence_launch_v0"
TMUX_SESSION = "e005_m39_conceptgraphs_heldout_sequence"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def shell_quote(value: str | Path) -> str:
    text = str(value)
    return "'" + text.replace("'", "'\"'\"'") + "'"


def count_sequence_files(sequence_dir: Path) -> dict[str, int]:
    if not sequence_dir.exists():
        return {
            "color_frames": 0,
            "depth_frames": 0,
            "pose_frames": 0,
            "frame_triplet_lower_bound": 0,
        }
    color_frames = len(list(sequence_dir.glob("*.color.jpg")))
    depth_frames = len(list(sequence_dir.glob("*.depth.pgm")))
    pose_frames = len(list(sequence_dir.glob("*.pose.txt")))
    return {
        "color_frames": color_frames,
        "depth_frames": depth_frames,
        "pose_frames": pose_frames,
        "frame_triplet_lower_bound": min(color_frames, depth_frames, pose_frames),
    }


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def build_manifest(scan_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scan_id in scan_ids:
        scan_dir = SCAN_ROOT / scan_id
        zip_path = scan_dir / "sequence.zip"
        sequence_dir = scan_dir / "sequence"
        counts = count_sequence_files(sequence_dir)
        url = f"{BASE_URL}/{scan_id}/sequence.zip"
        rows.append(
            {
                "scan_id": scan_id,
                "scan_dir": str(scan_dir),
                "sequence_zip_path": str(zip_path),
                "sequence_dir": str(sequence_dir),
                "url": url,
                "sequence_zip_ready": zip_path.exists(),
                "sequence_dir_ready": sequence_dir.exists(),
                "frame_triplet_lower_bound": counts["frame_triplet_lower_bound"],
                "needs_download": not zip_path.exists(),
                "needs_decompression": bool(zip_path.exists() and counts["frame_triplet_lower_bound"] == 0),
                "download_command": f"wget -c -O {shell_quote(zip_path)} {shell_quote(url)}",
                "unzip_command": f"unzip -n {shell_quote(zip_path)} -d {shell_quote(sequence_dir)}",
                "fallback_official_script_command": (
                    "python local_dataset/3RScan/download_3rscan.py "
                    f"-o {shell_quote(SCAN_ROOT)} --id {scan_id} --type sequence.zip"
                ),
            }
        )
    return rows


def build_run_script(manifest_rows: list[dict[str, Any]], out_dir: Path) -> str:
    verification_command = (
        "python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py "
        f"--manifest {shell_quote(out_dir / 'download_manifest.jsonl')} "
        f"--out-dir {shell_quote(out_dir / 'verification')} --require-ready"
    )
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shell_quote(ROOT)}",
        "mkdir -p logs",
        "",
    ]
    for row in manifest_rows:
        lines.extend(
            [
                f"# {row['scan_id']}",
                f"mkdir -p {shell_quote(row['scan_dir'])}",
                row["download_command"],
                row["unzip_command"],
                "",
            ]
        )
    lines.extend([verification_command, ""])
    return "\n".join(lines)


def build_report(coverage: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E005-M39 ConceptGraphs Heldout Sequence Launch",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux session: `{coverage['tmux_session']}`.",
        f"- background job status: `{coverage['background_job_status']}`.",
        f"- target scan count: {coverage['target_scan_count']}.",
        f"- prelaunch ready scan count: {coverage['prelaunch_sequence_ready_scan_count']}.",
        f"- download required scan count: {coverage['download_required_scan_count']}.",
        f"- decompression required scan count: {coverage['decompression_required_scan_count']}.",
        f"- log path: `{coverage['log_path']}`.",
        f"- run script: `{coverage['run_script']}`.",
        f"- verification command: `{coverage['verification_command']}`.",
        "",
        "## Target Scans",
        "",
    ]
    for row in manifest_rows:
        lines.append(
            f"- `{row['scan_id']}`: zip ready {str(row['sequence_zip_ready']).lower()}, "
            f"frame triplets {row['frame_triplet_lower_bound']}, needs download {str(row['needs_download']).lower()}."
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- E005-M39 is a data acquisition/staging launch, not a `ConceptGraphs` performance result.",
            "- Heldout runtime performance and final paper-table claims remain blocked until completion verification and metric conversion.",
            "",
            "## Agent Inference",
            "",
            "- The long-running acquisition job should stay in background.",
            "- Check progress only when explicitly requested or when E005-M40 depends on the result.",
            "- Verify completion with file counts and zip integrity rather than scanning the full log.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    contract = read_json(M38_DIR / "heldout_contract.json")
    missing_scan_ids = contract.get("next_execution_requirements", {}).get("missing_sequence_scan_ids", [])
    if not missing_scan_ids:
        scan_rows = read_jsonl(M38_DIR / "scan_rows.jsonl")
        missing_scan_ids = [
            row["scan_id"]
            for row in scan_rows
            if row.get("split") == "heldout_sequence_required" and row.get("download_required_for_scale")
        ]
    scan_ids = [str(scan_id) for scan_id in missing_scan_ids]
    manifest_rows = build_manifest(scan_ids)
    run_script_path = OUT_DIR / "run_heldout_sequence_staging.sh"
    write_text(run_script_path, build_run_script(manifest_rows, OUT_DIR))
    write_jsonl(OUT_DIR / "download_manifest.jsonl", manifest_rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_ROOT / f"{timestamp}_e005_m39_conceptgraphs_heldout_sequence.log"
    verification_command = (
        "python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py "
        f"--manifest {shell_quote(OUT_DIR / 'download_manifest.jsonl')} "
        f"--out-dir {shell_quote(OUT_DIR / 'verification')} --require-ready"
    )
    launch_command = (
        f"tmux new -d -s {TMUX_SESSION} "
        f"{shell_quote(f'cd {ROOT} && bash {run_script_path} > {log_path} 2>&1')}"
    )

    tmux_path = shutil.which("tmux")
    before_running = bool(tmux_path and tmux_has_session(TMUX_SESSION))
    launch_executed = False
    launch_returncode: int | None = None
    launch_stdout = ""
    launch_stderr = ""
    if not tmux_path:
        status = "e005_m39_heldout_sequence_launch_failed"
        background_status = "failed"
        launch_stderr = "tmux_not_found"
    elif before_running:
        status = "e005_m39_heldout_sequence_already_running"
        background_status = "running"
    else:
        proc = subprocess.run(
            launch_command,
            shell=True,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        launch_executed = True
        launch_returncode = proc.returncode
        launch_stdout = proc.stdout.strip()
        launch_stderr = proc.stderr.strip()
        if proc.returncode == 0 and tmux_has_session(TMUX_SESSION):
            status = "e005_m39_heldout_sequence_job_launched"
            background_status = "running"
        else:
            status = "e005_m39_heldout_sequence_launch_failed"
            background_status = "failed"

    prelaunch_ready = sum(1 for row in manifest_rows if row["frame_triplet_lower_bound"] > 0)
    download_required = sum(1 for row in manifest_rows if row["needs_download"])
    decompression_required = sum(1 for row in manifest_rows if row["needs_download"] or row["needs_decompression"])
    coverage = {
        "m39_version": VERSION,
        "status": status,
        "background_job_status": background_status,
        "target_scan_count": len(manifest_rows),
        "target_scan_ids": [row["scan_id"] for row in manifest_rows],
        "prelaunch_sequence_ready_scan_count": prelaunch_ready,
        "download_required_scan_count": download_required,
        "decompression_required_scan_count": decompression_required,
        "tmux_available": bool(tmux_path),
        "tmux_session": TMUX_SESSION,
        "tmux_session_running_before_launch": before_running,
        "launch_executed": launch_executed,
        "launch_returncode": launch_returncode,
        "launch_stdout": launch_stdout,
        "launch_stderr": launch_stderr,
        "launch_command": launch_command,
        "run_script": str(run_script_path),
        "log_path": str(log_path),
        "log_exists_at_launch": log_path.exists(),
        "verification_command": verification_command,
        "working_directory": str(ROOT),
        "expected_files": [
            "sequence.zip",
            "sequence/_info.txt",
            "sequence/*.color.jpg",
            "sequence/*.depth.pgm",
            "sequence/*.pose.txt",
        ],
        "next_recommended_unit": "E005-M40 heldout sequence staging completion verification",
        "paper_table_claim_ready": False,
        "heldout_runtime_claim_ready": False,
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(
        OUT_DIR / "command_plan.json",
        {
            "launch_command": launch_command,
            "run_script": str(run_script_path),
            "log_path": str(log_path),
            "verification_command": verification_command,
            "working_directory": str(ROOT),
        },
    )
    write_text(OUT_DIR / "report.md", build_report(coverage, manifest_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if background_status == "running" else 1


if __name__ == "__main__":
    raise SystemExit(main())
