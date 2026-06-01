#!/usr/bin/env python3
"""Build the E008-M60 high-path tail-slot trajectory contract and Docker preflight."""

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
VERSION = "e008_m60_high_path_tail_slot_trajectory_contract_v0"
READY_STATUS = "e008_m60_high_path_tail_slot_trajectory_contract_ready_runner_next"
BLOCKED_STATUS = "e008_m60_high_path_tail_slot_trajectory_contract_blocked"

M58_DIR = EXP_ROOT / "artifacts" / "E008-M58_source_gap_high_path_tail_slot_policy_materialization_v0"
M59_DIR = EXP_ROOT / "artifacts" / "E008-M59_high_path_tail_slot_goal_evaluation_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M60_high_path_tail_slot_trajectory_contract_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M60_high_path_tail_slot_trajectory_contract_v0"
)

HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
OBJECTNAV_CONTENT_ROOT = (
    RESEARCH3_DATA_ROOT
    / "datasets"
    / "objectnav"
    / "hm3d"
    / "v2"
    / "objectnav_hm3d_v2"
    / "val_mini"
    / "content"
)
M37_RUNNER = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M61_RUNNER = EXP_ROOT / "tools" / "run_m61_high_path_tail_slot_trajectory_execution_smoke.py"
M61_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0"
M61_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0"
)
NEXT_UNIT = "E008-M61 high-path tail-slot trajectory execution smoke"

M60_POLICY = "h001_task_conditioned_high_path_tail_slot_budget5_v3"
BASE_H001_POLICY = "h001_task_conditioned_safe_source_diverse_budget5_v2"
BASELINE_POLICIES = [
    "static_stale_memory_top1_v0",
    "detector_confidence_budget5_v0",
    "fixed_topk_current_observation_budget5_v0",
    "source_diverse_current_observation_budget5_v1",
    "task_agnostic_source_diverse_budget5_v1",
    BASE_H001_POLICY,
    "h001_task_conditioned_source_diverse_budget5_v1",
]
EXPECTED_CANDIDATE_ROWS = 648
EXPECTED_PLAN_ROWS = 144
EXPECTED_NEW_POLICY_PLAN_ROWS = 18

REQUIRED_M58_FILES = [
    "coverage.json",
    "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
    "trajectory_execution_plan_rows.jsonl",
    "input_contract_rows.jsonl",
    "leakage_audit_rows.jsonl",
    "policy_materialization_summary_rows.jsonl",
    "m49_order_preservation_audit_rows.jsonl",
    "tail_slot_policy_audit_rows.jsonl",
    "source_gap_episode_recovery_rows.jsonl",
]
REQUIRED_M59_FILES = [
    "coverage.json",
    "high_path_tail_policy_goal_metric_rows.jsonl",
    "pairwise_policy_delta_rows.jsonl",
    "source_gap_goal_recovery_rows.jsonl",
    "readiness_gate_rows.jsonl",
    "leakage_audit_rows.jsonl",
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


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return round(sum(clean) / len(clean), 6) if clean else None


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
    return RESEARCH3_DATA_ROOT / rel


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


def metric_lookup(rows: list[dict[str, Any]], policy_id: str, source_boundary: str | None = None) -> dict[str, Any]:
    for row in rows:
        if row.get("policy_id") != policy_id:
            continue
        if source_boundary is None and row.get("metric_scope") == "aggregate_policy":
            return row
        if (
            source_boundary is not None
            and row.get("metric_scope") == "aggregate_policy_source_boundary"
            and row.get("source_boundary") == source_boundary
        ):
            return row
    return {}


def build_policy_contract_rows(
    summary_rows: list[dict[str, Any]],
    m59_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary in sorted(summary_rows, key=lambda row: str(row.get("policy_id"))):
        policy_id = str(summary.get("policy_id"))
        full_metric = metric_lookup(m59_metric_rows, policy_id)
        source_gap_metric = metric_lookup(m59_metric_rows, policy_id, "source_gap")
        if policy_id == M60_POLICY:
            role = "method"
        elif policy_id == BASE_H001_POLICY:
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
                "source_ready_plan_rows": int(summary.get("policy_plan_rows") or 0)
                - int(summary.get("source_gap_plan_rows") or 0),
                "source_gap_plan_rows": summary.get("source_gap_plan_rows"),
                "stale_first_plan_rows": summary.get("stale_first_plan_rows"),
                "current_first_plan_rows": summary.get("current_first_plan_rows"),
                "runner_required": True,
                "pairwise_baseline_for_method": policy_id in BASELINE_POLICIES,
                "m59_full_GoalEvalProxySR": full_metric.get("primary_proxy_sr"),
                "m59_source_gap_GoalEvalProxySR": source_gap_metric.get("primary_proxy_sr"),
                "m59_full_GoalEvalProxySPL": full_metric.get("primary_spl_proxy_mean"),
                "m59_source_gap_GoalEvalProxySPL": source_gap_metric.get("primary_spl_proxy_mean"),
                "claim_boundary": "M60 fixes execution contract only; trajectory SR/SPL is not computed until M61.",
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
            "claim_status": "blocked_until_M61_execution",
        },
        {
            "version": VERSION,
            "metric": "SPL",
            "row_scope": "policy_aggregate",
            "definition": "success * oracle shortest path / max(executed path, oracle shortest path)",
            "eval_only_fields": "ObjectNav oracle viewpoint shortest path",
            "claim_status": "blocked_until_M61_execution",
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
            "metric": "source_gap_aggregate",
            "row_scope": "aggregate",
            "definition": "post-execution split using diagnostic_source_gap_boundary_for_reporting from M58",
            "eval_only_fields": "none for split; ObjectNav fields only for metric computation",
            "claim_status": "reporting_split_only_not_policy_input",
        },
        {
            "version": VERSION,
            "metric": "M59_GoalEvalProxySR",
            "row_scope": "pre_execution_proxy",
            "definition": "leakage-safe proxy gate already computed in M59; used only as a precondition for M60",
            "eval_only_fields": "ObjectNav goal/viewpoint fields joined after policy order was fixed",
            "claim_status": "not_a_final_navigation_metric",
        },
    ]


def build_m59_summary_rows(
    m59_cov: dict[str, Any],
    m59_metric_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate_rows = [row for row in m59_metric_rows if row.get("metric_scope") == "aggregate_policy"]
    source_rows = [row for row in m59_metric_rows if row.get("metric_scope") == "aggregate_policy_source_boundary"]
    method_full = metric_lookup(aggregate_rows, M60_POLICY)
    base_full = metric_lookup(aggregate_rows, BASE_H001_POLICY)
    method_gap = metric_lookup(source_rows, M60_POLICY, "source_gap")
    base_gap = metric_lookup(source_rows, BASE_H001_POLICY, "source_gap")
    source_gap_recovery = [row for row in recovery_rows if row.get("source_boundary") == "source_gap"]
    return [
        {
            "version": VERSION,
            "summary_id": "m59_goal_eval_proxy_gate",
            "m59_status": m59_cov.get("status"),
            "method_policy_id": M60_POLICY,
            "base_h001_policy_id": BASE_H001_POLICY,
            "method_full_GoalEvalProxySR": method_full.get("primary_proxy_sr"),
            "base_full_GoalEvalProxySR": base_full.get("primary_proxy_sr"),
            "method_source_gap_GoalEvalProxySR": method_gap.get("primary_proxy_sr"),
            "base_source_gap_GoalEvalProxySR": base_gap.get("primary_proxy_sr"),
            "method_minus_base_full_GoalEvalProxySR": m59_cov.get("m58_minus_base_h001_full_sr_delta"),
            "method_minus_base_source_gap_GoalEvalProxySR": m59_cov.get("m58_minus_base_h001_source_gap_sr_delta"),
            "source_gap_recovered_context_rows": sum(1 for row in source_gap_recovery if row.get("recovered_vs_base_h001")),
            "source_gap_lost_context_rows": sum(1 for row in source_gap_recovery if row.get("lost_vs_base_h001")),
            "pairwise_rows": len(pairwise_rows),
            "ready_for_m60": bool(m59_cov.get("ready_for_m60_trajectory_contract")),
            "claim_boundary": "M59 is a proxy goal-evaluation gate; M60/M61 are needed for trajectory execution.",
        }
    ]


def build_runner_compatibility_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    m37_compile: dict[str, Any],
    m61_compile: dict[str, Any],
) -> list[dict[str, Any]]:
    m37_text = M37_RUNNER.read_text(encoding="utf-8") if M37_RUNNER.exists() else ""
    policies = Counter(str(row.get("policy_id")) for row in plan_rows)
    return [
        {
            "version": VERSION,
            "check_id": "m37_generalized_runner_available",
            "status": "pass" if M37_RUNNER.exists() and m37_compile.get("ok") else "fail",
            "evidence": f"runner={M37_RUNNER.relative_to(ROOT)}; py_compile={bool(m37_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "m61_policy_wrapper_available",
            "status": "pass" if M61_RUNNER.exists() and m61_compile.get("ok") else "fail",
            "evidence": f"runner={M61_RUNNER.relative_to(ROOT)}; py_compile={bool(m61_compile.get('ok'))}.",
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
            "check_id": "method_policy_plan_rows",
            "status": "pass" if policies.get(M60_POLICY) == EXPECTED_NEW_POLICY_PLAN_ROWS else "fail",
            "evidence": f"{M60_POLICY} plan rows={policies.get(M60_POLICY, 0)}.",
        },
        {
            "version": VERSION,
            "check_id": "h001_pairwise_policy_constants",
            "status": "pass" if set(BASELINE_POLICIES).issubset(set(policies)) else "fail",
            "evidence": f"H001={M60_POLICY}; baselines={','.join(BASELINE_POLICIES)}.",
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
            "status": "pass" if RESEARCH3_DATA_ROOT.exists() else "fail",
            "evidence": f"path={RESEARCH3_DATA_ROOT}; exists={RESEARCH3_DATA_ROOT.exists()}.",
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


def build_m61_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research3/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m61_high_path_tail_slot_trajectory_execution_smoke.py\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m61_high_path_tail_slot_trajectory_execution_smoke",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research3/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "output_path": str(M61_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M61_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M61_high_path_tail_slot_trajectory_execution_smoke_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m61_high_path_tail_slot_trajectory_execution_smoke_ready'\n"
                "assert c['scan_task_policy_rows'] == 144\n"
                "print('m61 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    m58_cov: dict[str, Any],
    m59_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    m58_leakage_rows: list[dict[str, Any]],
    m59_leakage_rows: list[dict[str, Any]],
    m59_gate_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m58_present = [name for name in REQUIRED_M58_FILES if (M58_DIR / name).exists()]
    m59_present = [name for name in REQUIRED_M59_FILES if (M59_DIR / name).exists()]
    policies = Counter(str(row.get("policy_id")) for row in plan_rows)
    method_plan_rows = [row for row in plan_rows if row.get("policy_id") == M60_POLICY]
    return [
        {
            "version": VERSION,
            "gate_id": "m58_artifact_files_present",
            "status": "pass" if len(m58_present) == len(REQUIRED_M58_FILES) else "fail",
            "evidence": f"present={len(m58_present)}/{len(REQUIRED_M58_FILES)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m59_artifact_files_present",
            "status": "pass" if len(m59_present) == len(REQUIRED_M59_FILES) else "fail",
            "evidence": f"present={len(m59_present)}/{len(REQUIRED_M59_FILES)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m58_ready",
            "status": "pass" if m58_cov.get("status") == "e008_m58_source_gap_high_path_tail_slot_policy_materialization_ready" else "fail",
            "evidence": f"M58 status={m58_cov.get('status')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m59_ready_for_m60",
            "status": "pass"
            if m59_cov.get("status") == "e008_m59_high_path_tail_slot_goal_evaluation_smoke_ready"
            and m59_cov.get("ready_for_m60_trajectory_contract")
            else "fail",
            "evidence": f"M59 status={m59_cov.get('status')}; ready_for_m60={m59_cov.get('ready_for_m60_trajectory_contract')}.",
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
            "gate_id": "method_policy_and_baselines_present",
            "status": "pass" if policies.get(M60_POLICY) == EXPECTED_NEW_POLICY_PLAN_ROWS and set(BASELINE_POLICIES).issubset(set(policies)) else "fail",
            "evidence": f"method rows={policies.get(M60_POLICY, 0)}; policies={sorted(policies)}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_input_ready",
            "status": "pass" if len(method_plan_rows) == EXPECTED_NEW_POLICY_PLAN_ROWS and all(row.get("runner_input_ready") for row in plan_rows) else "fail",
            "evidence": f"runner_input_ready={sum(1 for row in plan_rows if row.get('runner_input_ready'))}/{len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m58_policy_input_leakage",
            "status": "pass" if all(row.get("leakage_pass") for row in m58_leakage_rows) else "fail",
            "evidence": f"leakage rows={len(m58_leakage_rows)}; blocked hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in m58_leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m58_budget_cap_compliance",
            "status": "pass" if all(row.get("budget_cap_compliance_pass") for row in m58_leakage_rows) else "fail",
            "evidence": f"over-budget hits={sum(int(row.get('over_budget_candidate_hits') or 0) for row in m58_leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m59_leakage_safe_goal_eval",
            "status": "pass" if all(row.get("leakage_audit_pass") for row in m59_leakage_rows) else "fail",
            "evidence": f"M59 leakage pass={sum(1 for row in m59_leakage_rows if row.get('leakage_audit_pass'))}/{len(m59_leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m59_internal_gates_pass",
            "status": "pass" if m59_gate_rows and all(row.get("status") == "pass" for row in m59_gate_rows) else "fail",
            "evidence": f"M59 gates pass={sum(1 for row in m59_gate_rows if row.get('status') == 'pass')}/{len(m59_gate_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m59_source_gap_proxy_improvement",
            "status": "pass"
            if finite_float(m59_cov.get("m58_minus_base_h001_source_gap_sr_delta")) is not None
            and float(m59_cov.get("m58_minus_base_h001_source_gap_sr_delta")) > 0.0
            and int(m59_cov.get("source_gap_lost_vs_base_context_rows") or 0) == 0
            else "fail",
            "evidence": (
                f"delta={m59_cov.get('m58_minus_base_h001_source_gap_sr_delta')}; "
                f"recovered={m59_cov.get('source_gap_recovered_vs_base_context_rows')}; "
                f"lost={m59_cov.get('source_gap_lost_vs_base_context_rows')}."
            ),
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
            "safe_claim": "M60 provides a Docker-ready trajectory execution contract for M58/M59 high-path tail-slot rows.",
        },
        {
            "version": VERSION,
            "claim_id": "high_path_tail_slot_navigation_result",
            "status": "not_ready",
            "safe_claim": "No M60 output contains executed trajectories or trajectory SR/SPL results.",
        },
        {
            "version": VERSION,
            "claim_id": "m59_goal_eval_proxy_improvement",
            "status": "supported_pre_execution_proxy",
            "safe_claim": "M59 supports a leakage-safe GoalEvalProxy improvement gate; M60 only carries it forward as a precondition.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M61 execution, interpretation, larger scale, and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "Structured task context remains a memory-trust/re-observation condition; M60 does not support natural-language human-intent understanding.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m60_selected_next",
            "decision": "run_high_path_tail_slot_trajectory_smoke" if ready else "repair_m60_contract_or_preflight",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M60 high-path tail-slot trajectory contract",
            "reason": "M60 verifies M58 rows, M59 proxy gates, M61 runner wrapper, Docker image, read-only HM3D data, and source-gap reporting compatibility."
            if ready
            else "One or more M60 contract/preflight gates did not pass.",
            "launch_long_job_now": False,
        }
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    m59_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M60 High-Path Tail-Slot Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M58 status: `{coverage['m58_status']}`.",
            f"- M59 status: `{coverage['m59_status']}`.",
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
                    "m59_full_GoalEvalProxySR",
                    "m59_source_gap_GoalEvalProxySR",
                ],
            ),
            "",
            "## M59 Goal-Eval Proxy Gate",
            "",
            markdown_table(
                m59_summary_rows,
                [
                    "method_full_GoalEvalProxySR",
                    "base_full_GoalEvalProxySR",
                    "method_source_gap_GoalEvalProxySR",
                    "base_source_gap_GoalEvalProxySR",
                    "method_minus_base_source_gap_GoalEvalProxySR",
                    "source_gap_recovered_context_rows",
                    "source_gap_lost_context_rows",
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
            "## Paper Claim",
            "",
            "- M60 supports only a Docker-ready execution contract.",
            "- M60 does not support executed navigation improvement, final real navigation `SR` / `SPL`, or final RGB-D/open-vocabulary robustness.",
            "",
            "## Agent Inference",
            "",
            "- Because M59 proxy gains are positive and leakage-safe, M60 closes the reproducibility gap before running the same rows inside Habitat.",
            "",
        ]
    )


def copy_input_artifacts(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
) -> None:
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

    m58_cov = read_json(M58_DIR / "coverage.json")
    m59_cov = read_json(M59_DIR / "coverage.json")
    candidate_rows = read_jsonl(M58_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M58_DIR / "trajectory_execution_plan_rows.jsonl")
    input_contract_rows = read_jsonl(M58_DIR / "input_contract_rows.jsonl")
    m58_leakage_rows = read_jsonl(M58_DIR / "leakage_audit_rows.jsonl")
    summary_rows = read_jsonl(M58_DIR / "policy_materialization_summary_rows.jsonl")
    m59_metric_rows = read_jsonl(M59_DIR / "high_path_tail_policy_goal_metric_rows.jsonl")
    pairwise_rows = read_jsonl(M59_DIR / "pairwise_policy_delta_rows.jsonl")
    source_gap_recovery_rows = read_jsonl(M59_DIR / "source_gap_goal_recovery_rows.jsonl")
    m59_gate_rows = read_jsonl(M59_DIR / "readiness_gate_rows.jsonl")
    m59_leakage_rows = read_jsonl(M59_DIR / "leakage_audit_rows.jsonl")

    if not m58_cov or not m59_cov or not candidate_rows or not plan_rows:
        raise SystemExit("missing required E008-M58/M59 inputs")

    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m61_compile = command_status(["python", "-m", "py_compile", str(M61_RUNNER)], timeout_s=30)
    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)

    policy_rows = build_policy_contract_rows(summary_rows, m59_metric_rows)
    metric_rows = build_metric_contract_rows()
    m59_summary_rows = build_m59_summary_rows(m59_cov, m59_metric_rows, pairwise_rows, source_gap_recovery_rows)
    runner_rows = build_runner_compatibility_rows(candidate_rows, plan_rows, m37_compile, m61_compile)
    docker_rows = build_docker_preflight_rows(candidate_rows, docker_image_status, docker_version_status, nvidia_status)
    command_rows = build_m61_command_rows()
    gate_rows = build_readiness_gate_rows(
        m58_cov,
        m59_cov,
        candidate_rows,
        plan_rows,
        m58_leakage_rows,
        m59_leakage_rows,
        m59_gate_rows,
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
        "m58_status": m58_cov.get("status"),
        "m59_status": m59_cov.get("status"),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "policy_count": len(policy_counts),
        "policy_ids": sorted(policy_counts),
        "h001_policy_id": M60_POLICY,
        "baseline_policy_ids": BASELINE_POLICIES,
        "source_gap_reporting_plan_rows": source_gap_reporting_rows,
        "source_ready_reporting_plan_rows": len(plan_rows) - source_gap_reporting_rows,
        "m58_policy_input_leakage_pass": all(row.get("leakage_pass") for row in m58_leakage_rows),
        "m58_budget_cap_compliance_pass": all(row.get("budget_cap_compliance_pass") for row in m58_leakage_rows),
        "m59_leakage_audit_pass": all(row.get("leakage_audit_pass") for row in m59_leakage_rows),
        "m59_ready_for_m60_trajectory_contract": bool(m59_cov.get("ready_for_m60_trajectory_contract")),
        "m59_method_full_GoalEvalProxySR": m59_summary_rows[0].get("method_full_GoalEvalProxySR"),
        "m59_base_full_GoalEvalProxySR": m59_summary_rows[0].get("base_full_GoalEvalProxySR"),
        "m59_method_source_gap_GoalEvalProxySR": m59_summary_rows[0].get("method_source_gap_GoalEvalProxySR"),
        "m59_base_source_gap_GoalEvalProxySR": m59_summary_rows[0].get("base_source_gap_GoalEvalProxySR"),
        "m59_source_gap_recovered_context_rows": m59_summary_rows[0].get("source_gap_recovered_context_rows"),
        "m59_source_gap_lost_context_rows": m59_summary_rows[0].get("source_gap_lost_context_rows"),
        "runner_script": str(M61_RUNNER.relative_to(ROOT)),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "m61_runner_py_compile_pass": bool(m61_compile.get("ok")),
        "runner_py_compile_pass": bool(m37_compile.get("ok")) and bool(m61_compile.get("ok")),
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
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    copy_input_artifacts(candidate_rows, plan_rows, input_contract_rows, m58_leakage_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_contract_rows.jsonl", policy_rows)
    write_jsonl(ARTIFACT_DIR / "metric_contract_rows.jsonl", metric_rows)
    write_jsonl(ARTIFACT_DIR / "m59_goal_eval_summary_rows.jsonl", m59_summary_rows)
    write_jsonl(ARTIFACT_DIR / "runner_compatibility_rows.jsonl", runner_rows)
    write_jsonl(ARTIFACT_DIR / "docker_preflight_rows.jsonl", docker_rows)
    write_jsonl(ARTIFACT_DIR / "m61_command_rows.jsonl", command_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, m59_summary_rows, gate_rows, docker_rows, runner_rows),
        encoding="utf-8",
    )

    copy_core_outputs(
        [
            "coverage.json",
            "trajectory_execution_contract_rows.jsonl",
            "metric_contract_rows.jsonl",
            "m59_goal_eval_summary_rows.jsonl",
            "runner_compatibility_rows.jsonl",
            "docker_preflight_rows.jsonl",
            "m61_command_rows.jsonl",
            "readiness_gate_rows.jsonl",
        ],
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
