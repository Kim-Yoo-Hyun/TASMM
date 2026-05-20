#!/usr/bin/env python3
"""Verify E005-M59 Open3DSG object-candidate export one-batch smoke."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LOCAL_DATA_DIR = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M59_object_candidate_export_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E005-M59_object_candidate_export_smoke_v0"
M58_SCHEMA = ROOT / "local_dataset" / "Open3DSG_bridge" / "E005-M58_object_candidate_export_plan_v0" / "object_candidate_schema.json"
SESSION = "e005_m59_open3dsg_object_export"


def run_cmd(cmd: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tmux_running() -> bool:
    return run_cmd(["tmux", "has-session", "-t", SESSION]).returncode == 0


def read_log_tail(path: str | None, lines: int = 80) -> list[str]:
    if not path:
        return []
    log_path = Path(path)
    if not log_path.exists():
        return []
    result = run_cmd(["tail", "-n", str(lines), str(log_path)], timeout=20)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def load_jsonl(path: Path, limit: int = 1000) -> tuple[int, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    count = 0
    if not path.exists():
        return 0, rows, errors
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            if len(rows) >= limit:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: JSONDecodeError {exc}")
                continue
            if not isinstance(row, dict):
                errors.append(f"line {line_no}: row is not object")
                continue
            rows.append(row)
    return count, rows, errors


def build_report(result: dict[str, Any]) -> str:
    row = result["row_context"]
    return "\n".join(
        [
            "# E005-M59 Open3DSG Object Export Smoke",
            "",
            "## Status",
            "",
            result["status"],
            "",
            "## Facts",
            "",
            f"- Tmux running: {result['tmux_running']}.",
            f"- Candidate row file exists: {row['candidate_row_file_exists']}.",
            f"- Candidate rows: {row['candidate_row_count']}.",
            f"- Completed batches: {result['manifest_context'].get('completed_batches')}.",
            f"- Source modified: {result['source_modified']}.",
            "",
            "## Next",
            "",
            "- If ready, run E005-M60 query-level conversion smoke.",
            "",
        ]
    )


def run(require_ready: bool) -> dict[str, Any]:
    launch = read_json(ARTIFACT_DIR / "coverage.json")
    log_tail = read_log_tail(launch.get("log_path"))
    schema = read_json(M58_SCHEMA)
    required_fields = set(schema.get("required_fields", []))
    row_path = LOCAL_DATA_DIR / "open3dsg_object_candidates.jsonl"
    completed_path = LOCAL_DATA_DIR / "open3dsg_object_candidates.completed.jsonl"
    manifest_path = LOCAL_DATA_DIR / "open3dsg_object_candidates.manifest.json"
    row_count, sample_rows, parse_errors = load_jsonl(row_path)
    completed_count, completed_rows, completed_errors = load_jsonl(completed_path)
    errors = parse_errors + [f"completed {err}" for err in completed_errors]
    missing_counts: dict[str, int] = {}
    for row in sample_rows:
        missing = sorted(required_fields - set(row))
        for field in missing:
            missing_counts[field] = missing_counts.get(field, 0) + 1
    if missing_counts:
        errors.append(f"candidate rows missing required fields: {missing_counts}")
    if require_ready and row_count == 0:
        errors.append("require-ready set but no candidate rows found")
    if require_ready and not manifest_path.exists():
        errors.append("require-ready set but manifest is missing")
    running = tmux_running()
    manifest = read_json(manifest_path)
    if errors:
        status = "e005_m59_open3dsg_object_export_smoke_failed"
    elif row_count > 0 and completed_count > 0 and manifest_path.exists():
        status = "e005_m59_open3dsg_object_export_smoke_ready"
    elif running:
        status = "e005_m59_open3dsg_object_export_smoke_running"
    else:
        status = "e005_m59_open3dsg_object_export_smoke_not_ready"
    result = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "require_ready": require_ready,
        "tmux_running": running,
        "local_output_dir": str(LOCAL_DATA_DIR),
        "artifact_dir": str(ARTIFACT_DIR),
        "source_modified": False,
        "errors": errors,
        "launch_status": launch.get("status"),
        "launch_log_path": launch.get("log_path"),
        "row_context": {
            "candidate_row_path": str(row_path),
            "candidate_row_file_exists": row_path.exists(),
            "candidate_row_count": row_count,
            "sampled_rows": len(sample_rows),
            "missing_field_counts": missing_counts,
            "completed_row_count": completed_count,
        },
        "manifest_context": manifest,
        "log_tail": log_tail[-80:],
    }
    write_json(ARTIFACT_DIR / "verification.json", result)
    write_text(ARTIFACT_DIR / "report.md", build_report(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    result = run(require_ready=args.require_ready)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "e005_m59_open3dsg_object_export_smoke_ready":
        return 1
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
