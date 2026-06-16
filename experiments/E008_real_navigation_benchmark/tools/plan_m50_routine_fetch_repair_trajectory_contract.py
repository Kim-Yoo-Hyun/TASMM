#!/usr/bin/env python3
"""Build the E008-M50 routine-fetch repair trajectory contract and Docker preflight."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m50_routine_fetch_repair_trajectory_contract_v0"
READY_STATUS = "e008_m50_routine_fetch_repair_trajectory_contract_ready_runner_next"
BLOCKED_STATUS = "e008_m50_routine_fetch_repair_trajectory_contract_blocked"

M49_DIR = EXP_ROOT / "artifacts" / "E008-M49_routine_fetch_repair_row_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M50_routine_fetch_repair_trajectory_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M50_routine_fetch_repair_trajectory_contract_v0"

HABITAT_IMAGE = "research2/habitat-h001:20260508-calib-artifacts"
RESEARCH2_DATA_ROOT = Path("/home/yoohyun/research2/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH2_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)
M37_RUNNER = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M51_RUNNER = EXP_ROOT / "tools" / "run_m51_routine_fetch_repair_trajectory_execution_smoke.py"
M51_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"
M51_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0"
NEXT_UNIT = "E008-M51 routine-fetch repair trajectory execution smoke"

REPAIR_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
H001_V1_POLICY = "h001_task_conditioned_source_diverse_budget5_v1"
BASELINE_POLICIES = [
    "static_stale_memory_top1_v0",
    "detector_confidence_budget5_v0",
    "fixed_topk_current_observation_budget5_v0",
    "source_diverse_current_observation_budget5_v1",
    "task_agnostic_source_diverse_budget5_v1",
    H001_V1_POLICY,
]
EXPECTED_CANDIDATE_ROWS = 558
EXPECTED_PLAN_ROWS = 126
EXPECTED_BASELINE_PRESERVATION_ROWS = 108
EXPECTED_REGRESSION_TARGET_ROWS = 2

REQUIRED_M49_FILES = [
    "coverage.json",
    "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
    "trajectory_execution_plan_rows.jsonl",
    "input_contract_rows.jsonl",
    "leakage_audit_rows.jsonl",
    "policy_materialization_summary_rows.jsonl",
    "baseline_preservation_audit_rows.jsonl",
    "repair_policy_audit_rows.jsonl",
    "regression_repair_target_audit_rows.jsonl",
]


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


def sanitize_json(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_json(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(clean) / len(clean)) if clean else None


def command_status(cmd: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s, check=False)
    except FileNotFoundError as exc:
        return {"available": False, "ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "available": True,
            "ok": False,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "",
            "timeout_s": timeout_s,
        }
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-500:],
    }


def host_path_from_docker(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        rel = path.relative_to(DOCKER_DATA_ROOT)
    except ValueError:
        return None
    return RESEARCH2_DATA_ROOT / rel


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def build_policy_contract_rows(summary_rows: list[dict[str, Any]], repair_audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repair_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repair_audit_rows:
        repair_by_task[str(row.get("task_context_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for summary in summary_rows:
        policy_id = str(summary.get("policy_id"))
        if policy_id == REPAIR_POLICY:
            role = "method"
        elif policy_id == H001_V1_POLICY:
            role = "previous_method_baseline"
        else:
            role = "baseline_or_ablation"
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": role,
                "candidate_budget": 1 if policy_id == "static_stale_memory_top1_v0" else 5,
                "policy_plan_rows": summary.get("policy_plan_rows"),
                "candidate_rows": summary.get("candidate_rows"),
                "source_ready_plan_rows": summary.get("source_ready_plan_rows"),
                "source_gap_plan_rows": summary.get("source_gap_plan_rows"),
                "stale_first_plan_rows": summary.get("stale_first_plan_rows"),
                "current_first_plan_rows": summary.get("current_first_plan_rows"),
                "runner_required": True,
                "pairwise_baseline_for_repair_policy": policy_id in BASELINE_POLICIES,
                "routine_fetch_repair_source_kind": "task_agnostic_source_diverse_current_guard"
                if policy_id == REPAIR_POLICY
                else None,
                "routine_fetch_repair_rows": len(repair_by_task.get("routine_fetch", [])) if policy_id == REPAIR_POLICY else None,
                "claim_boundary": "M50 fixes execution contract only; performance is not computed until M51.",
            }
        )
    return rows


def build_metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "metric": "SR",
            "row_scope": "policy_aggregate",
            "definition": "mean over scan-task-policy rows of trajectory success after executing materialized stops",
            "eval_only_fields": "ObjectNav goal/viewpoints loaded inside runner after each stop",
            "claim_status": "blocked_until_M51_execution",
        },
        {
            "version": VERSION,
            "metric": "SPL",
            "row_scope": "policy_aggregate",
            "definition": "success * oracle shortest path / max(executed path, oracle shortest path)",
            "eval_only_fields": "ObjectNav oracle viewpoint shortest path",
            "claim_status": "blocked_until_M51_execution",
        },
        {
            "version": VERSION,
            "metric": "OldLocationDeadEndCostM",
            "row_scope": "scan_task_policy",
            "definition": "executed stale-old-memory path length before reaching current observation candidates",
            "eval_only_fields": "none",
            "claim_status": "diagnostic_not_primary_metric",
        },
        {
            "version": VERSION,
            "metric": "routine_fetch_no_regression",
            "row_scope": "task_context_aggregate",
            "definition": "M51 must compare repaired H001 v2 against task-agnostic source-diverse and previous H001 v1 on routine_fetch rows",
            "eval_only_fields": "ObjectNav success and trajectory path length",
            "claim_status": "blocked_until_M51_execution_and_M52_interpretation",
        },
        {
            "version": VERSION,
            "metric": "source_gap_aggregate",
            "row_scope": "aggregate",
            "definition": "post-execution split using diagnostic_source_gap_boundary_for_reporting from M49",
            "eval_only_fields": "none for split; ObjectNav fields only for metric computation",
            "claim_status": "reporting_split_only_not_policy_input",
        },
    ]


def build_runner_compatibility_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    m37_compile: dict[str, Any],
    m51_compile: dict[str, Any],
) -> list[dict[str, Any]]:
    m37_text = M37_RUNNER.read_text(encoding="utf-8") if M37_RUNNER.exists() else ""
    return [
        {
            "version": VERSION,
            "check_id": "m37_generalized_runner_available",
            "status": "pass" if M37_RUNNER.exists() and m37_compile.get("ok") else "fail",
            "evidence": f"runner={M37_RUNNER.relative_to(ROOT)}; py_compile={bool(m37_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "m51_policy_wrapper_available",
            "status": "pass" if M51_RUNNER.exists() and m51_compile.get("ok") else "fail",
            "evidence": f"runner={M51_RUNNER.relative_to(ROOT)}; py_compile={bool(m51_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "source_gap_reporting_fallback",
            "status": "pass" if "source_gap_for_reporting" in m37_text else "fail",
            "evidence": "M37 must read diagnostic_source_gap_boundary_for_reporting when policy-input diagnostic_source_gap_boundary is absent.",
        },
        {
            "version": VERSION,
            "check_id": "candidate_file_contract",
            "status": "pass" if len(candidate_rows) == EXPECTED_CANDIDATE_ROWS else "fail",
            "evidence": f"dynamic_stale_overlay_trajectory_candidate_rows.jsonl rows={len(candidate_rows)}.",
        },
        {
            "version": VERSION,
            "check_id": "plan_file_contract",
            "status": "pass" if len(plan_rows) == EXPECTED_PLAN_ROWS else "fail",
            "evidence": f"trajectory_execution_plan_rows.jsonl rows={len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "check_id": "h001_pairwise_policy_constants",
            "status": "pass",
            "evidence": f"H001={REPAIR_POLICY}; baselines={','.join(BASELINE_POLICIES)}.",
        },
    ]


def build_docker_preflight_rows(
    candidate_rows: list[dict[str, Any]],
    docker_image_status: dict[str, Any],
    docker_version_status: dict[str, Any],
    nvidia_status: dict[str, Any],
) -> list[dict[str, Any]]:
    scene_paths = sorted({str(row.get("scene_docker_path")) for row in candidate_rows if row.get("scene_docker_path")})
    navmesh_paths = sorted({str(row.get("navmesh_docker_path")) for row in candidate_rows if row.get("navmesh_docker_path")})
    scene_host_paths = [host_path_from_docker(path) for path in scene_paths]
    navmesh_host_paths = [host_path_from_docker(path) for path in navmesh_paths]
    scene_ready = sum(1 for path in scene_host_paths if path is not None and path.exists())
    navmesh_ready = sum(1 for path in navmesh_host_paths if path is not None and path.exists())
    content_files = list(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")) if OBJECTNAV_CONTENT_ROOT.exists() else []
    return [
        {
            "version": VERSION,
            "check_id": "docker_cli",
            "status": "pass" if docker_version_status.get("ok") else "fail",
            "evidence": f"returncode={docker_version_status.get('returncode')}; stderr_tail={docker_version_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "habitat_docker_image",
            "status": "pass" if docker_image_status.get("ok") else "fail",
            "evidence": f"image={HABITAT_IMAGE}; returncode={docker_image_status.get('returncode')}; stderr_tail={docker_image_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "nvidia_smi",
            "status": "pass" if nvidia_status.get("ok") else "warning",
            "evidence": f"returncode={nvidia_status.get('returncode')}; stdout_tail={nvidia_status.get('stdout_tail')!r}; stderr_tail={nvidia_status.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "check_id": "read_only_hm3d_data_root",
            "status": "pass" if RESEARCH2_DATA_ROOT.exists() else "fail",
            "evidence": f"path={RESEARCH2_DATA_ROOT}; exists={RESEARCH2_DATA_ROOT.exists()}.",
        },
        {
            "version": VERSION,
            "check_id": "scene_files",
            "status": "pass" if scene_ready == len(scene_paths) and bool(scene_paths) else "fail",
            "evidence": f"ready={scene_ready}/{len(scene_paths)}.",
        },
        {
            "version": VERSION,
            "check_id": "navmesh_files",
            "status": "pass" if navmesh_ready == len(navmesh_paths) and bool(navmesh_paths) else "fail",
            "evidence": f"ready={navmesh_ready}/{len(navmesh_paths)}.",
        },
        {
            "version": VERSION,
            "check_id": "objectnav_content_files",
            "status": "pass" if content_files else "fail",
            "evidence": f"path={OBJECTNAV_CONTENT_ROOT}; json_gz_files={len(content_files)}.",
        },
    ]


def build_m51_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m51_routine_fetch_repair_trajectory_execution_smoke.py\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m51_routine_fetch_repair_trajectory_execution_smoke",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "output_path": str(M51_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M51_DATA_OUT_DIR.relative_to(ROOT)),
            "command": command,
            "launch_now": False,
            "expected_files": [
                "coverage.json",
                "dynamic_stale_trajectory_attempt_rows.jsonl",
                "dynamic_stale_trajectory_policy_metric_rows.jsonl",
                "pairwise_policy_delta_rows.jsonl",
                "claim_boundary_rows.jsonl",
                "report.md",
            ],
            "verification_command": (
                "python - <<'PY'\n"
                "import json\n"
                "from pathlib import Path\n"
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M51_routine_fetch_repair_trajectory_execution_smoke_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m51_routine_fetch_repair_trajectory_execution_smoke_ready'\n"
                "assert c['scan_task_policy_rows'] == 126\n"
                "print('m51 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    m49_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    m49_leakage_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    required_present = [name for name in REQUIRED_M49_FILES if (M49_DIR / name).exists()]
    policies = {str(row.get("policy_id")) for row in plan_rows}
    return [
        {
            "version": VERSION,
            "gate_id": "m49_artifact_files_present",
            "status": "pass" if len(required_present) == len(REQUIRED_M49_FILES) else "fail",
            "evidence": f"present={len(required_present)}/{len(REQUIRED_M49_FILES)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_ready",
            "status": "pass" if m49_cov.get("status") == "e008_m49_routine_fetch_repair_row_materialization_smoke_ready" else "fail",
            "evidence": f"M49 status={m49_cov.get('status')}.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_rows_preserved",
            "status": "pass" if len(candidate_rows) == EXPECTED_CANDIDATE_ROWS else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; expected={EXPECTED_CANDIDATE_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "execution_plan_rows_preserved",
            "status": "pass" if len(plan_rows) == EXPECTED_PLAN_ROWS else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected={EXPECTED_PLAN_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "repair_policy_and_baselines_present",
            "status": "pass" if REPAIR_POLICY in policies and set(BASELINE_POLICIES).issubset(policies) else "fail",
            "evidence": f"policies={sorted(policies)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_policy_input_leakage",
            "status": "pass" if all(row.get("leakage_pass") for row in m49_leakage_rows) else "fail",
            "evidence": f"leakage rows={len(m49_leakage_rows)}; blocked hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in m49_leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_budget_cap_compliance",
            "status": "pass" if all(row.get("budget_cap_compliance_pass") for row in m49_leakage_rows) else "fail",
            "evidence": f"over-budget hits={sum(int(row.get('over_budget_candidate_hits') or 0) for row in m49_leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_baseline_preservation",
            "status": "pass"
            if len(baseline_rows) == EXPECTED_BASELINE_PRESERVATION_ROWS
            and all(row.get("preservation_pass") for row in baseline_rows)
            else "fail",
            "evidence": f"baseline preservation pass={sum(1 for row in baseline_rows if row.get('preservation_pass'))}/{len(baseline_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m49_regression_targets",
            "status": "pass"
            if len(target_rows) == EXPECTED_REGRESSION_TARGET_ROWS and all(row.get("audit_pass") for row in target_rows)
            else "fail",
            "evidence": f"target audit pass={sum(1 for row in target_rows if row.get('audit_pass'))}/{len(target_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_compatibility",
            "status": "pass" if all(row.get("status") == "pass" for row in runner_rows) else "fail",
            "evidence": f"runner checks pass={sum(1 for row in runner_rows if row.get('status') == 'pass')}/{len(runner_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "docker_preflight",
            "status": "pass"
            if all(row.get("status") in {"pass", "warning"} for row in docker_rows)
            and not any(row.get("status") == "fail" for row in docker_rows)
            else "fail",
            "evidence": f"docker/data checks fail={sum(1 for row in docker_rows if row.get('status') == 'fail')}; warning={sum(1 for row in docker_rows if row.get('status') == 'warning')}.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "trajectory_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M50 provides a Docker-ready trajectory execution contract for M49 repaired routine-fetch rows.",
        },
        {
            "version": VERSION,
            "claim_id": "routine_fetch_repair_navigation_result",
            "status": "not_ready",
            "safe_claim": "No M50 output contains executed trajectories or SR/SPL results.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M51 execution, interpretation, larger scale, and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "Structured task context remains a condition; M50 does not support natural-language human-intent understanding.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m50_selected_next",
            "decision": "run_routine_fetch_repair_trajectory_smoke" if ready else "repair_m50_contract_or_preflight",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M50 routine-fetch repair trajectory contract",
            "reason": "M50 verifies M49 rows, M51 runner wrapper, Docker image, read-only HM3D data, and source-gap reporting compatibility."
            if ready
            else "One or more M50 contract/preflight gates did not pass.",
            "launch_long_job_now": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M50 Routine-Fetch Repair Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## 사실",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M49 status: `{coverage['m49_status']}`.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Runner py_compile pass: {coverage['runner_py_compile_pass']}.",
            f"- Docker preflight pass: {coverage['docker_preflight_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            markdown_table(
                policy_rows,
                [
                    "policy_id",
                    "policy_role",
                    "policy_plan_rows",
                    "candidate_rows",
                    "source_ready_plan_rows",
                    "source_gap_plan_rows",
                    "stale_first_plan_rows",
                    "current_first_plan_rows",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            markdown_table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Runner Compatibility",
            "",
            markdown_table(runner_rows, ["check_id", "status", "evidence"]),
            "",
            "## 논문 주장",
            "",
            "- M50 supports only a Docker-ready execution contract.",
            "- M50 does not support repaired navigation improvement, final real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.",
            "",
            "## 에이전트 추론",
            "",
            "- M49 already fixed candidate order; M50 prevents a reproducibility gap by pinning the exact Docker command, runner wrapper, input files, and source-gap reporting semantics before trajectory execution.",
            "",
            "## 사용자 판단 필요",
            "",
            "- If M51 trajectory execution is positive, decide whether to scale the same benchmark or first broaden navigation/search baselines.",
            "",
        ]
    )


def copy_input_artifacts(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]], input_rows: list[dict[str, Any]], leakage_rows: list[dict[str, Any]]) -> None:
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_rows)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leakage_rows)
    write_jsonl(DATA_OUT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(DATA_OUT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(DATA_OUT_DIR / "input_contract_rows.jsonl", input_rows)


def copy_core_outputs(filenames: list[str]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        src = ARTIFACT_DIR / name
        if src.exists():
            shutil.copy2(src, DATA_OUT_DIR / name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m49_cov = read_json(M49_DIR / "coverage.json")
    candidate_rows = read_jsonl(M49_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M49_DIR / "trajectory_execution_plan_rows.jsonl")
    input_contract_rows = read_jsonl(M49_DIR / "input_contract_rows.jsonl")
    m49_leakage_rows = read_jsonl(M49_DIR / "leakage_audit_rows.jsonl")
    summary_rows = read_jsonl(M49_DIR / "policy_materialization_summary_rows.jsonl")
    baseline_rows = read_jsonl(M49_DIR / "baseline_preservation_audit_rows.jsonl")
    repair_audit_rows = read_jsonl(M49_DIR / "repair_policy_audit_rows.jsonl")
    target_rows = read_jsonl(M49_DIR / "regression_repair_target_audit_rows.jsonl")

    if not m49_cov or not candidate_rows or not plan_rows:
        raise SystemExit("missing required E008-M49 inputs")

    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m51_compile = command_status(["python", "-m", "py_compile", str(M51_RUNNER)], timeout_s=30)
    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)

    policy_rows = build_policy_contract_rows(summary_rows, repair_audit_rows)
    metric_rows = build_metric_contract_rows()
    runner_rows = build_runner_compatibility_rows(candidate_rows, plan_rows, m37_compile, m51_compile)
    docker_rows = build_docker_preflight_rows(candidate_rows, docker_image_status, docker_version_status, nvidia_status)
    command_rows = build_m51_command_rows()
    gate_rows = build_readiness_gate_rows(
        m49_cov,
        candidate_rows,
        plan_rows,
        m49_leakage_rows,
        baseline_rows,
        target_rows,
        runner_rows,
        docker_rows,
    )
    contract_ready = all(row.get("status") == "pass" for row in gate_rows)
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(contract_ready)

    source_gap_reporting_rows = sum(1 for row in plan_rows if row.get("diagnostic_source_gap_boundary_for_reporting"))
    policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if contract_ready else BLOCKED_STATUS,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m49_status": m49_cov.get("status"),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "policy_count": len(policy_counts),
        "policy_ids": sorted(policy_counts),
        "h001_policy_id": REPAIR_POLICY,
        "baseline_policy_ids": BASELINE_POLICIES,
        "source_gap_reporting_plan_rows": source_gap_reporting_rows,
        "source_ready_reporting_plan_rows": len(plan_rows) - source_gap_reporting_rows,
        "m49_policy_input_leakage_pass": all(row.get("leakage_pass") for row in m49_leakage_rows),
        "m49_budget_cap_compliance_pass": all(row.get("budget_cap_compliance_pass") for row in m49_leakage_rows),
        "m49_baseline_preservation_pass_rows": sum(1 for row in baseline_rows if row.get("preservation_pass")),
        "m49_baseline_preservation_rows": len(baseline_rows),
        "m49_regression_target_pass_rows": sum(1 for row in target_rows if row.get("audit_pass")),
        "m49_regression_target_rows": len(target_rows),
        "runner_script": str(M51_RUNNER.relative_to(ROOT)),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "m51_runner_py_compile_pass": bool(m51_compile.get("ok")),
        "runner_py_compile_pass": bool(m37_compile.get("ok")) and bool(m51_compile.get("ok")),
        "m37_source_gap_reporting_fallback_ready": any(
            row.get("check_id") == "source_gap_reporting_fallback" and row.get("status") == "pass"
            for row in runner_rows
        ),
        "docker_cli_ok": bool(docker_version_status.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "docker_preflight_pass": all(row.get("status") in {"pass", "warning"} for row in docker_rows)
        and not any(row.get("status") == "fail" for row in docker_rows),
        "nvidia_smi_ok": bool(nvidia_status.get("ok")),
        "trajectory_execution_contract_ready": contract_ready,
        "trajectory_execution_result_ready": False,
        "dynamic_stale_navigation_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    copy_input_artifacts(candidate_rows, plan_rows, input_contract_rows, m49_leakage_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "runner_compatibility_rows.jsonl", runner_rows)
    write_jsonl(ARTIFACT_DIR / "docker_preflight_rows.jsonl", docker_rows)
    write_jsonl(ARTIFACT_DIR / "m51_command_rows.jsonl", command_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, gate_rows, docker_rows, runner_rows),
        encoding="utf-8",
    )

    copy_core_outputs(
        [
            "coverage.json",
            "trajectory_execution_contract_rows.jsonl",
            "metric_contract_rows.jsonl",
            "runner_compatibility_rows.jsonl",
            "docker_preflight_rows.jsonl",
            "m51_command_rows.jsonl",
            "readiness_gate_rows.jsonl",
        ],
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
