#!/usr/bin/env python3
"""Plan sequence payload staging for E003-M55 current-rescan bridge targets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M55_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M55_dynamic_pair_bridge_gate_v0"
DEFAULT_DATASET_ROOT = RESEARCH_ROOT / "local_dataset" / "3RScan" / "scans"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M56_current_rescan_sequence_staging_plan_v0"
M56_VERSION = "e003_m56_current_rescan_sequence_staging_plan_v0"
BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


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


def build_manifest_rows(target_rows: list[dict[str, Any]], dataset_root: Path, out_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in target_rows:
        if int(row.get("search_failure_rows", 0) or 0) <= 0:
            continue
        scan_id = str(row["scan_id"])
        scan_dir = dataset_root / scan_id
        sequence_dir = scan_dir / "sequence"
        zip_path = scan_dir / "sequence.zip"
        url = f"{BASE_URL}/{scan_id}/sequence.zip"
        counts = count_sequence_files(sequence_dir)
        needs_download = not zip_path.exists()
        needs_decompression = bool(zip_path.exists() and counts["frame_triplet_lower_bound"] == 0)
        rows.append(
            {
                "download_command": f"wget -c -O {shell_quote(zip_path)} {shell_quote(url)}",
                "fallback_official_script_command": (
                    "python local_dataset/3RScan/download_3rscan.py "
                    f"-o {shell_quote(dataset_root)} --id {scan_id} --type sequence.zip"
                ),
                "failure_labels": row.get("failure_labels", {}),
                "frame_triplet_lower_bound": counts["frame_triplet_lower_bound"],
                "needs_decompression": needs_decompression,
                "needs_download": needs_download,
                "output_path": str(zip_path),
                "scan_dir": str(scan_dir),
                "scan_id": scan_id,
                "search_failure_rows": int(row.get("search_failure_rows", 0) or 0),
                "sequence_dir": str(sequence_dir),
                "sequence_dir_ready": sequence_dir.exists(),
                "sequence_zip_path": str(zip_path),
                "sequence_zip_ready": zip_path.exists(),
                "unzip_command": f"unzip -n {shell_quote(zip_path)} -d {shell_quote(sequence_dir)}",
                "url": url,
                "verification_command": (
                    "python experiments/E003_perception_noise_expansion/tools/"
                    "verify_m56_sequence_payloads.py "
                    f"--manifest {shell_quote(out_dir / 'download_manifest.jsonl')} "
                    f"--out-dir {shell_quote(out_dir / 'verification')} --require-ready"
                ),
            }
        )
    return rows


def build_run_script(manifest_rows: list[dict[str, Any]], out_dir: Path) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "cd /home/yoohyun/research2",
        "mkdir -p logs",
        "",
    ]
    for row in manifest_rows:
        lines.extend(
            [
                f"# {row['scan_id']}",
                f"mkdir -p {shell_quote(Path(row['scan_dir']))}",
                row["download_command"],
                row["unzip_command"],
                "",
            ]
        )
    lines.extend(
        [
            (
                "python experiments/E003_perception_noise_expansion/tools/"
                "verify_m56_sequence_payloads.py "
                f"--manifest {shell_quote(out_dir / 'download_manifest.jsonl')} "
                f"--out-dir {shell_quote(out_dir / 'verification')} --require-ready"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_report(coverage: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# E003-M56 Current-Rescan Sequence Staging Plan",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Target scan count: {coverage['target_scan_count']}.",
        f"- Sequence-ready target scan count before launch: {coverage['prelaunch_sequence_ready_scan_count']}.",
        f"- Scans needing download: {coverage['download_required_scan_count']}.",
        f"- Scans needing decompression after zip appears: {coverage['decompression_required_scan_count']}.",
        f"- Background job status: `{coverage['background_job_status']}`.",
        f"- Launch command: `{coverage['launch_command']}`.",
        f"- Verification command: `{coverage['verification_command']}`.",
        f"- Next recommended unit: `{coverage['next_recommended_unit']}`.",
        "",
        "## Target Scans",
        "",
    ]
    for row in manifest_rows:
        lines.append(
            f"- `{row['scan_id']}`: failure labels {row['failure_labels']}, "
            f"download required {row['needs_download']}, sequence ready {row['sequence_dir_ready']}."
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M56 does not create a paper result claim.",
            "- It fixes the reproducible staging plan needed before current-rescan detector outputs can be evaluated against E001/E002 rows.",
            "- Real RGB-D/open-vocabulary search robustness remains blocked until the staging job completes and detector inference/evaluation runs.",
            "",
            "## 에이전트 추론",
            "",
            "- The smallest direct bridge is to stage only the 4 current rescans that already have E001/E002 search failures.",
            "- `wget -c` is preferred over the official script because it is resumable; the official script remains a fallback command.",
            "- The next step should launch this as a background job rather than block the main agent.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None if E003-M57 launches the background staging job with the recorded command.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m55-dir", default=DEFAULT_M55_DIR, type=Path)
    parser.add_argument("--dataset-root", default=DEFAULT_DATASET_ROOT, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m55 = load_json(args.m55_dir / "coverage.json")
    bridge_rows = load_jsonl(args.m55_dir / "bridge_target_scan_rows.jsonl")
    manifest_rows = build_manifest_rows(bridge_rows, args.dataset_root, args.out_dir)
    run_script = build_run_script(manifest_rows, args.out_dir)
    run_script_path = args.out_dir / "run_sequence_staging.sh"
    write_text(run_script_path, run_script)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = RESEARCH_ROOT / "logs" / f"{timestamp}_e003_m56_sequence_staging.log"
    launch_command = (
        "mkdir -p logs && tmux new -d -s e003_m56_sequence_stage "
        f"{shell_quote(f'cd {RESEARCH_ROOT} && bash {run_script_path} > {log_path} 2>&1')}"
    )
    verification_command = (
        "python experiments/E003_perception_noise_expansion/tools/verify_m56_sequence_payloads.py "
        f"--manifest {shell_quote(args.out_dir / 'download_manifest.jsonl')} "
        f"--out-dir {shell_quote(args.out_dir / 'verification')} --require-ready"
    )
    prelaunch_ready = sum(1 for row in manifest_rows if not row["needs_download"] and row["frame_triplet_lower_bound"] > 0)
    download_required = sum(1 for row in manifest_rows if row["needs_download"])
    decompression_required = sum(1 for row in manifest_rows if row["needs_decompression"] or row["needs_download"])
    coverage = {
        "background_job_status": "not_launched",
        "decompression_required_scan_count": decompression_required,
        "download_required_scan_count": download_required,
        "expected_files": [
            "sequence.zip",
            "sequence/_info.txt",
            "sequence/*.color.jpg",
            "sequence/*.depth.pgm",
            "sequence/*.pose.txt",
        ],
        "launch_command": launch_command,
        "log_path": str(log_path),
        "m55_selected_route": (m55.get("selected_route") or {}).get("route_id"),
        "m56_version": M56_VERSION,
        "next_recommended_unit": "E003-M57 launch current-rescan sequence staging background job",
        "output_path": str(args.out_dir),
        "paper_table_command_ready": False,
        "prelaunch_sequence_ready_scan_count": prelaunch_ready,
        "real_rgbd_or_open_vocab_search_claim_ready": False,
        "run_script": str(run_script_path),
        "status": "current_rescan_sequence_staging_plan_ready",
        "target_scan_count": len(manifest_rows),
        "target_scan_ids": [row["scan_id"] for row in manifest_rows],
        "verification_command": verification_command,
        "working_directory": str(RESEARCH_ROOT),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "command_plan.json", {
        "launch_command": launch_command,
        "log_path": str(log_path),
        "run_script": str(run_script_path),
        "verification_command": verification_command,
        "working_directory": str(RESEARCH_ROOT),
    })
    write_jsonl(args.out_dir / "download_manifest.jsonl", manifest_rows)
    write_text(args.out_dir / "report.md", build_report(coverage, manifest_rows))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
