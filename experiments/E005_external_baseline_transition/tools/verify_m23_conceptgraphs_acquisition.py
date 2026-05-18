#!/usr/bin/env python3
"""Verify the E005-M23 ConceptGraphs acquisition background job."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
LAUNCH_DIR = EXPERIMENT_ROOT / "artifacts" / "E005-M23_conceptgraphs_acquisition_launch_v0"
OUT_DIR = LAUNCH_DIR / "verification"
SESSION = "e005_m23_conceptgraphs_acquisition"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # noqa: BLE001 - verifier should record failures.
        return {"cmd": cmd, "returncode": None, "stdout": "", "stderr": repr(exc), "ok": False}


def tmux_running() -> bool:
    return run(["tmux", "has-session", "-t", SESSION], timeout=10)["ok"]


def git_head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    result = run(["git", "rev-parse", "HEAD"], cwd=path, timeout=10)
    return result["stdout"] if result["ok"] else None


def file_state(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists() or path.is_symlink(),
        "is_symlink": path.is_symlink(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def build_report(coverage: dict[str, Any]) -> str:
    lines = [
        "# E005-M23 ConceptGraphs Acquisition Verification",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- tmux running: {str(coverage['tmux_running']).lower()}.",
        f"- background status: `{coverage['background_status'].get('status', 'missing')}`.",
        f"- ConceptGraphs head: `{coverage['conceptgraphs_head']}`.",
        f"- GSA head: `{coverage['gsa_head']}`.",
        f"- ConceptGraphs commit match: {str(coverage['conceptgraphs_commit_match']).lower()}.",
        f"- GSA commit match: {str(coverage['gsa_commit_match']).lower()}.",
        f"- SAM cache ready: {str(coverage['sam_cache_ready']).lower()}.",
        f"- GroundingDINO checkpoint ready: {str(coverage['groundingdino_ready']).lower()}.",
        f"- log path: `{coverage['log_path']}`.",
        "",
        "## Claim Boundary",
        "",
        "- This verification only checks acquisition state.",
        "- No `ConceptGraphs` runtime or performance claim is supported.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    launch = read_json(LAUNCH_DIR / "coverage.json")
    expected = launch.get("expected_files", {})
    background_status = read_json(Path(launch.get("background_status_path", "")))
    conceptgraphs_repo = Path(expected.get("conceptgraphs_repo", ""))
    gsa_repo = Path(expected.get("gsa_repo", ""))
    conceptgraphs_head = git_head(conceptgraphs_repo)
    gsa_head = git_head(gsa_repo)
    conceptgraphs_match = conceptgraphs_head == expected.get("conceptgraphs_expected_commit")
    gsa_match = gsa_head == expected.get("gsa_expected_commit")
    sam_cache = file_state(Path(expected.get("sam_symlink_cache", "")))
    sam_repo = file_state(Path(expected.get("sam_symlink_gsa_repo", "")))
    grounding = file_state(Path(expected.get("groundingdino_checkpoint", "")))
    grounding_repo = file_state(Path(expected.get("groundingdino_symlink_gsa_repo", "")))
    running = tmux_running()
    all_ready = (
        conceptgraphs_match
        and gsa_match
        and sam_cache["exists"]
        and sam_repo["exists"]
        and grounding["exists"]
        and grounding["size_bytes"] > 0
        and grounding_repo["exists"]
    )
    if all_ready and background_status.get("status") == "completed":
        status = "e005_m23_conceptgraphs_acquisition_completed_ready"
    elif running:
        status = "e005_m23_conceptgraphs_acquisition_running"
    elif background_status.get("status") == "failed":
        status = "e005_m23_conceptgraphs_acquisition_failed"
    else:
        status = "e005_m23_conceptgraphs_acquisition_needs_verification"
    coverage = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tmux_running": running,
        "background_status": background_status,
        "conceptgraphs_head": conceptgraphs_head,
        "gsa_head": gsa_head,
        "conceptgraphs_commit_match": conceptgraphs_match,
        "gsa_commit_match": gsa_match,
        "sam_cache": sam_cache,
        "sam_repo": sam_repo,
        "sam_cache_ready": sam_cache["exists"],
        "sam_repo_ready": sam_repo["exists"],
        "groundingdino_checkpoint": grounding,
        "groundingdino_repo": grounding_repo,
        "groundingdino_ready": grounding["exists"] and grounding["size_bytes"] > 0,
        "log_path": launch.get("log_path"),
        "next_recommended_unit": "E005-M24 ConceptGraphs acquisition completion verification"
        if status == "e005_m23_conceptgraphs_acquisition_running"
        else "E005-M25 ConceptGraphs Docker build preflight"
        if status == "e005_m23_conceptgraphs_acquisition_completed_ready"
        else "Inspect E005-M23 acquisition log tail",
    }
    write_json(OUT_DIR / "coverage.json", coverage)
    write_text(OUT_DIR / "report.md", build_report(coverage))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
