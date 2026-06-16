#!/usr/bin/env python3
"""Verify whether the restored runtime is ready for E008-M205 execution."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M204_TOOL = EXP_ROOT / "tools" / "plan_m204_additive_source_pool_candidate_union_docker_trajectory_contract.py"

VERSION = "e008_m205_runtime_restore_preflight_v0"
READY_STATUS = "e008_m205_runtime_restore_preflight_ready"
BLOCKED_STATUS = "e008_m205_runtime_restore_preflight_blocked"

M204_DIR = EXP_ROOT / "artifacts" / "E008-M204_additive_source_pool_candidate_union_docker_trajectory_contract_v0"
OUT_DIR = EXP_ROOT / "artifacts" / "E008-M205_runtime_restore_preflight_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M205_runtime_restore_preflight_v0"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        out[status] = out.get(status, 0) + 1
    return out


def build_restore_requirements(m204: Any, command_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    command = command_rows[0].get("command") if command_rows else ""
    verification = command_rows[0].get("verification_command") if command_rows else ""
    return [
        {
            "requirement_id": "hm3d_objectnav_data_root",
            "required_path": str(m204.RESEARCH2_DATA_ROOT),
            "required_mode": "read_only_mount_source",
            "current_ready": m204.RESEARCH2_DATA_ROOT.exists(),
            "verification": f"test -d {m204.RESEARCH2_DATA_ROOT}",
        },
        {
            "requirement_id": "habitat_docker_image",
            "required_image": m204.HABITAT_IMAGE,
            "required_mode": "docker_image_restore_or_rebuild",
            "current_ready": any(
                row.get("check_id") == "habitat_docker_image" and row.get("status") == "pass"
                for row in m204.build_docker_preflight_rows([])
            ),
            "verification": f"docker image inspect {m204.HABITAT_IMAGE} >/dev/null",
        },
        {
            "requirement_id": "m205_execution_command",
            "command": command,
            "verification": verification,
            "current_ready": bool(command and verification),
        },
    ]


def build_report(coverage: dict[str, Any], docker_rows: list[dict[str, Any]], command_rows: list[dict[str, Any]]) -> str:
    command = command_rows[0].get("command") if command_rows else ""
    verification = command_rows[0].get("verification_command") if command_rows else ""
    lines = [
        "# E008-M205 Runtime Restore Preflight",
        "",
        f"Generated: {coverage['generated_at']}",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- M204 contract rows ready: {coverage['m204_contract_rows_ready']}.",
        f"- Runtime preflight pass: {coverage['runtime_preflight_pass']}.",
        f"- Docker preflight fail rows: {coverage['docker_preflight_fail_rows']} / {coverage['docker_preflight_rows']}.",
        f"- M205 command ledger ready: {coverage['m205_command_ledger_ready']}.",
        f"- M205 execution launch allowed now: {coverage['m205_launch_allowed_now']}.",
        "",
        "## Docker / Data Checks",
        "",
        "| check_id | status | evidence |",
        "| --- | --- | --- |",
    ]
    for row in docker_rows:
        evidence = str(row.get("evidence", "")).replace("\n", " ")
        lines.append(f"| {row.get('check_id')} | {row.get('status')} | {evidence} |")
    lines.extend(
        [
            "",
            "## Command",
            "",
            "Run only after all runtime checks pass:",
            "",
            "```bash",
            command,
            "```",
            "",
            "Verification command:",
            "",
            "```bash",
            verification,
            "```",
            "",
            "## Claim Boundary",
            "",
            "- This preflight does not execute trajectories.",
            "- It only decides whether E008-M205 can be launched.",
            "- Final real navigation `SR` / `SPL` remains blocked until E008-M205 execution and interpretation pass.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    m204 = load_module(M204_TOOL, "e008_m204_for_m205_restore_preflight")
    candidate_rows = read_jsonl(M204_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M204_DIR / "trajectory_execution_plan_rows.jsonl")
    command_rows = read_jsonl(M204_DIR / "m205_command_rows.jsonl")
    m204_coverage = read_json(M204_DIR / "coverage.json")

    docker_rows = m204.build_docker_preflight_rows(candidate_rows)
    for row in docker_rows:
        row["version"] = VERSION

    fail_rows = [row for row in docker_rows if row.get("status") == "fail"]
    m204_contract_rows_ready = bool(candidate_rows) and len(plan_rows) == 120
    runtime_preflight_pass = not fail_rows
    command_ready = bool(command_rows and command_rows[0].get("command") and command_rows[0].get("verification_command"))
    launch_ready = m204_contract_rows_ready and runtime_preflight_pass and command_ready
    status = READY_STATUS if launch_ready else BLOCKED_STATUS

    coverage = {
        "candidate_rows": len(candidate_rows),
        "command_rows": len(command_rows),
        "data_out_dir": str(DATA_OUT_DIR.relative_to(ROOT)),
        "docker_preflight_fail_rows": len(fail_rows),
        "docker_preflight_rows": len(docker_rows),
        "docker_preflight_status_counts": status_counts(docker_rows),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m204_contract": str(M204_DIR.relative_to(ROOT)),
        "m204_contract_rows_ready": m204_contract_rows_ready,
        "m204_status": m204_coverage.get("status"),
        "m205_command_ledger_ready": command_ready,
        "m205_launch_allowed_now": launch_ready,
        "plan_rows": len(plan_rows),
        "runtime_preflight_pass": runtime_preflight_pass,
        "selected_next_unit": "run E008-M205" if launch_ready else "restore HM3D/ObjectNav data root and Habitat Docker image",
        "status": status,
        "version": VERSION,
    }
    restore_rows = build_restore_requirements(m204, command_rows)

    for out_dir in [OUT_DIR, DATA_OUT_DIR]:
        write_json(out_dir / "coverage.json", coverage)
        write_jsonl(out_dir / "docker_preflight_rows.jsonl", docker_rows)
        write_jsonl(out_dir / "restore_requirement_rows.jsonl", restore_rows)
        write_jsonl(out_dir / "m205_command_rows.jsonl", command_rows)
        write_text(out_dir / "report.md", build_report(coverage, docker_rows, command_rows))

    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if launch_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
