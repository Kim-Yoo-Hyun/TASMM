#!/usr/bin/env python3
"""Build E008-M156 budget-aware utility trajectory execution contract."""

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

VERSION = "e008_m156_budget_aware_utility_trajectory_contract_v0"
READY_STATUS = "e008_m156_budget_aware_utility_trajectory_contract_ready_runner_next"
READY_RUNNER_MISSING_STATUS = "e008_m156_budget_aware_utility_trajectory_contract_ready_runner_missing"
BLOCKED_STATUS = "e008_m156_budget_aware_utility_trajectory_contract_blocked"

M149_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
)
M155_DIR = (
    EXP_ROOT / "artifacts" / "E008-M155_budget_aware_utility_policy_materialization_smoke_v0"
)
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
)

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
M157_RUNNER = EXP_ROOT / "tools" / "run_m157_budget_aware_utility_trajectory_execution.py"
M157_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M157_budget_aware_utility_trajectory_execution_v0"
M157_DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M157_budget_aware_utility_trajectory_execution_v0"
)

NEXT_UNIT = "E008-M157 budget-aware utility trajectory execution"
METHOD_POLICY = "budget_aware_confidence_path_utility_v0"
PRIMARY_BASELINE_POLICY = "detector_confidence_reachable_subset_v0"

EXPECTED_POLICY_COUNT = 7
EXPECTED_EPISODE_ROWS = 30
EXPECTED_PLAN_ROWS = EXPECTED_POLICY_COUNT * EXPECTED_EPISODE_ROWS
EXPECTED_CANDIDATE_ROWS = 6300
EXPECTED_CANDIDATE_ROWS_PER_POLICY = 900
EXPECTED_BASE_CANDIDATE_ROWS = 900
EXPECTED_MATRIX_ROWS = 33354

M149_SUPPORT_FILES = [
    "base_candidate_rows.jsonl",
    "trajectory_cost_matrix_rows.jsonl",
    "episode_goal_eval_rows.jsonl",
    "oracle_path_rows.jsonl",
    "input_contract_rows.jsonl",
]
M155_AUX_FILES = [
    "budget_aware_candidate_rows.jsonl",
    "policy_plan_rows.jsonl",
    "utility_component_rows.jsonl",
    "policy_order_audit_rows.jsonl",
    "materialization_gate_rows.jsonl",
    "reviewer_defense_rows.jsonl",
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
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
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


def normalize_candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        policy_id = str(row.get("policy_id"))
        payload = dict(row)
        payload.update(
            {
                "version": VERSION,
                "m155_materialization_version": row.get("version"),
                "execution_contract_version": VERSION,
                "claim_boundary": "M156 fixes runner-compatible budget-aware utility trajectory inputs only; no Habitat trajectory is executed.",
                "method_policy": policy_id == METHOD_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE_POLICY,
                "runner_input_ready": True,
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_success_label_for_policy": False,
            }
        )
        out.append(payload)
    return out


def build_plan_rows(
    m155_plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    audit_index = {
        (str(row.get("benchmark_row_uid")), str(row.get("policy_id"))): row
        for row in audit_rows
    }
    out: list[dict[str, Any]] = []
    for plan in m155_plan_rows:
        uid = str(plan.get("benchmark_row_uid"))
        policy_id = str(plan.get("policy_id"))
        rows = sorted(grouped[(uid, policy_id)], key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0] if rows else {}
        last = rows[-1] if rows else {}
        audit = audit_index.get((uid, policy_id), {})
        path_ready_count = sum(1 for row in rows if row.get("path_ready"))
        current_first = str(first.get("candidate_source_role")) == "current_observation"
        source_gap = any(bool(row.get("source_gap_recovery_branch_active")) for row in rows)
        payload = {
            **plan,
            "version": VERSION,
            "m155_materialization_version": plan.get("version"),
            "execution_contract_version": VERSION,
            "row_type": "trajectory_execution_plan",
            "policy_role": first.get("policy_role"),
            "method_policy": policy_id == METHOD_POLICY,
            "primary_baseline_policy": policy_id == PRIMARY_BASELINE_POLICY,
            "execute_in_next_runner": True,
            "requires_docker": True,
            "runner_script": str(M157_RUNNER.relative_to(ROOT)),
            "runner_input_ready": bool(rows),
            "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
            "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
            "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
            "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
            "start_state_source": "ObjectNav episode start state from episode_goal_eval_rows; goal/viewpoints are metric-only",
            "candidate_budget": len(rows),
            "candidate_rows": len(rows),
            "path_ready_candidate_rows": path_ready_count,
            "blocked_candidate_rows": len(rows) - path_ready_count,
            "planned_cumulative_path_cost_m": last.get("planned_cumulative_path_cost_m"),
            "first_confidence": first.get("confidence"),
            "first_current_pose_to_candidate_geodesic_m": first.get("current_pose_to_candidate_geodesic_m"),
            "current_observation_first": current_first,
            "stale_visit_first": False,
            "stale_before_current_rows": 0,
            "old_location_dead_end_cost_proxy_m": 0.0,
            "diagnostic_source_gap_boundary_for_reporting": source_gap,
            "order_changed_vs_detector": bool(audit.get("order_changed_vs_detector")),
            "utility_promotion_allowed_rows": audit.get("utility_promotion_allowed_rows"),
            "promotion_candidate_rows": audit.get("promotion_candidate_rows"),
            "max_rank_displacement_abs_from_detector": audit.get("max_rank_displacement_abs_from_detector"),
            "m155_requires_cumulative_path_recompute_for_execution": plan.get(
                "requires_cumulative_path_recompute_for_execution"
            ),
            "uses_m127_proxy_success_for_filtering": False,
            "uses_task_context_for_decision": False,
            "uses_trajectory_cost_matrix_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
            "policy_input_uses_eval_goal_or_viewpoint": False,
            "policy_input_uses_success_label": False,
            "claim_boundary": "M156 is a Docker trajectory contract/preflight unit; M157 is required for executed SR/SPL.",
        }
        out.append(payload)
    return out


def build_execution_contract_rows(
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    path_counts = Counter(str(row.get("policy_id")) for row in candidate_rows if row.get("path_ready"))
    changed_counts = Counter(
        str(row.get("policy_id")) for row in audit_rows if row.get("order_changed_vs_detector")
    )
    promotion_sums: dict[str, int] = defaultdict(int)
    max_rank_disp: dict[str, int] = defaultdict(int)
    audit_pass: dict[str, bool] = defaultdict(lambda: True)
    for row in audit_rows:
        policy_id = str(row.get("policy_id"))
        promotion_sums[policy_id] += int(row.get("utility_promotion_allowed_rows") or 0)
        max_rank_disp[policy_id] = max(max_rank_disp[policy_id], int(row.get("max_rank_displacement_abs_from_detector") or 0))
        audit_pass[policy_id] = audit_pass[policy_id] and bool(row.get("audit_pass"))
    role_index = {str(row.get("policy_id")): row.get("policy_role") for row in plan_rows if row.get("policy_role")}
    rows: list[dict[str, Any]] = []
    for policy_id in sorted(plan_counts):
        rows.append(
            {
                "version": VERSION,
                "row_type": "trajectory_execution_contract",
                "policy_id": policy_id,
                "policy_role": role_index.get(policy_id),
                "method_policy": policy_id == METHOD_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE_POLICY,
                "episode_rows": plan_counts[policy_id],
                "candidate_rows": candidate_counts[policy_id],
                "path_ready_candidate_rows": path_counts[policy_id],
                "order_changed_episode_rows": changed_counts[policy_id],
                "utility_promotion_allowed_rows": promotion_sums[policy_id] if policy_id.startswith("budget_aware") else None,
                "max_rank_displacement_abs_from_detector": max_rank_disp[policy_id],
                "policy_order_audit_pass": audit_pass[policy_id],
                "runner_script": str(M157_RUNNER.relative_to(ROOT)),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_plan_file": "trajectory_execution_plan_rows.jsonl",
                "execute_in_m157": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M156 fixes the budget-aware utility execution contract only; M157 is required for executed SR/SPL.",
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    input_contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked_fields = {str(row.get("field")) for row in input_contract_rows if row.get("allowed_for_policy") is False}
    out: list[dict[str, Any]] = []
    for payload, rows in [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in blocked_fields:
                if field in row:
                    field_hits[field] += 1
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get(
                "policy_input_uses_eval_goal_or_viewpoint"
            ) or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def build_docker_preflight_rows(
    candidate_rows: list[dict[str, Any]],
    docker_version_status: dict[str, Any],
    docker_image_status: dict[str, Any],
    nvidia_status: dict[str, Any],
    m37_compile: dict[str, Any],
    m157_compile: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    scene_paths = sorted({str(row.get("scene_docker_path")) for row in candidate_rows if row.get("scene_docker_path")})
    navmesh_paths = sorted(
        {str(row.get("navmesh_docker_path")) for row in candidate_rows if row.get("navmesh_docker_path")}
    )
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
        {
            "version": VERSION,
            "check_id": "m37_generalized_runner_available",
            "status": "pass" if M37_RUNNER.exists() and m37_compile.get("ok") else "fail",
            "evidence": f"runner={M37_RUNNER.relative_to(ROOT)}; py_compile={bool(m37_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "m157_budget_aware_runner_available",
            "status": "pass" if M157_RUNNER.exists() and m157_compile and m157_compile.get("ok") else "fail",
            "evidence": f"runner={M157_RUNNER.relative_to(ROOT)}; exists={M157_RUNNER.exists()}; py_compile={bool(m157_compile and m157_compile.get('ok'))}.",
        },
    ]


def build_m157_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m157_budget_aware_utility_trajectory_execution.py "
        "--m156-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M156_budget_aware_utility_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M157_budget_aware_utility_trajectory_execution_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m157_budget_aware_utility_trajectory_execution",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M157_RUNNER.relative_to(ROOT)),
            "runner_implemented": M157_RUNNER.exists(),
            "output_path": str(M157_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M157_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M157_budget_aware_utility_trajectory_execution_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m157_budget_aware_utility_trajectory_execution_ready'\n"
                "assert c['scan_task_policy_rows'] == 210\n"
                "print('m157 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    *,
    m155_cov: dict[str, Any],
    base_candidate_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    m155_leakage_rows: list[dict[str, Any]],
    m155_audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    episode_count = len({str(row.get("adapter_episode_id")) for row in plan_rows})
    selected_audits = [row for row in m155_audit_rows if row.get("policy_id") == METHOD_POLICY]
    gates = [
        (
            "m155_materialization_ready",
            m155_cov.get("status") == "e008_m155_budget_aware_utility_policy_materialization_smoke_ready"
            and m155_cov.get("trajectory_execution_ready") is True,
            f"M155 status={m155_cov.get('status')}; trajectory_execution_ready={m155_cov.get('trajectory_execution_ready')}.",
            True,
        ),
        (
            "base_candidate_denominator_available",
            len(base_candidate_rows) == EXPECTED_BASE_CANDIDATE_ROWS,
            f"base candidates={len(base_candidate_rows)}; expected={EXPECTED_BASE_CANDIDATE_ROWS}.",
            True,
        ),
        (
            "runner_candidate_rows_written",
            len(candidate_rows) == EXPECTED_CANDIDATE_ROWS
            and len(candidate_counts) == EXPECTED_POLICY_COUNT
            and set(candidate_counts.values()) == {EXPECTED_CANDIDATE_ROWS_PER_POLICY},
            f"candidate rows={len(candidate_rows)}; counts={dict(sorted(candidate_counts.items()))}.",
            True,
        ),
        (
            "runner_plan_rows_written",
            len(plan_rows) == EXPECTED_PLAN_ROWS
            and len(plan_counts) == EXPECTED_POLICY_COUNT
            and episode_count == EXPECTED_EPISODE_ROWS
            and sum(1 for row in plan_rows if row.get("execute_in_next_runner")) == EXPECTED_PLAN_ROWS,
            f"plan rows={len(plan_rows)}; episode rows={episode_count}; policies={dict(sorted(plan_counts.items()))}.",
            True,
        ),
        (
            "goal_and_oracle_rows_ready",
            len(goal_rows) == EXPECTED_EPISODE_ROWS and len(oracle_rows) == EXPECTED_EPISODE_ROWS,
            f"goal rows={len(goal_rows)}; oracle rows={len(oracle_rows)}.",
            True,
        ),
        (
            "trajectory_cost_matrix_available",
            len(matrix_rows) == EXPECTED_MATRIX_ROWS,
            f"matrix rows={len(matrix_rows)}; expected={EXPECTED_MATRIX_ROWS}.",
            False,
        ),
        (
            "method_and_primary_baseline_present",
            METHOD_POLICY in candidate_counts and PRIMARY_BASELINE_POLICY in candidate_counts,
            f"method={METHOD_POLICY in candidate_counts}; primary_baseline={PRIMARY_BASELINE_POLICY in candidate_counts}.",
            True,
        ),
        (
            "selected_policy_order_change_preserved",
            len(selected_audits) == EXPECTED_EPISODE_ROWS
            and sum(1 for row in selected_audits if row.get("order_changed_vs_detector")) == int(
                m155_cov.get("selected_changed_episode_rows") or 0
            ),
            f"selected_changed={sum(1 for row in selected_audits if row.get('order_changed_vs_detector'))}; coverage={m155_cov.get('selected_changed_episode_rows')}.",
            True,
        ),
        (
            "m155_leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in m155_leakage_rows),
            f"failed={sum(1 for row in m155_leakage_rows if not row.get('leakage_audit_pass'))}.",
            True,
        ),
        (
            "m156_leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in leakage_rows),
            f"failed={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}.",
            True,
        ),
        (
            "docker_preflight",
            all(row.get("status") in {"pass", "warning"} for row in docker_rows)
            and not any(row.get("status") == "fail" for row in docker_rows),
            f"fail={sum(1 for row in docker_rows if row.get('status') == 'fail')}; warning={sum(1 for row in docker_rows if row.get('status') == 'warning')}.",
            True,
        ),
        (
            "execute_trajectories_now",
            False,
            "M156 is a contract/preflight unit; M157 should execute.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m157": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "budget_aware_utility_execution_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M156 provides a Docker-preflighted, runner-compatible budget-aware utility trajectory execution contract.",
        },
        {
            "version": VERSION,
            "claim_id": "budget_aware_utility_trajectory_execution",
            "status": "not_executed",
            "safe_claim": "M156 does not execute Habitat trajectories; M157 is required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M157 execution, M158 interpretation, heldout transfer, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "M156 target-free execution contract does not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(contract_ready: bool, runner_ready: bool) -> list[dict[str, Any]]:
    if contract_ready and runner_ready:
        selected_next = NEXT_UNIT
        decision = "run_m157_budget_aware_utility_trajectory_execution"
    elif contract_ready:
        selected_next = "E008-M157 budget-aware utility trajectory execution runner scaffold"
        decision = "scaffold_m157_runner_before_docker_execution"
    else:
        selected_next = "repair E008-M156 budget-aware utility trajectory contract"
        decision = "repair_m156_contract_or_preflight"
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m156_selected_next",
            "decision": decision,
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "reason": "M156 fixes the budget-aware utility execution input contract and Docker/data preflight; M157 should execute trajectories."
            if contract_ready
            else "One or more M156 contract/preflight gates failed.",
        }
    ]


def build_report(
    coverage: dict[str, Any],
    contract_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M156 Budget-Aware Utility Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Eval goal rows: {coverage['full_val_mini_eval_goal_rows']}.",
            f"- Oracle path rows: {coverage['oracle_path_rows']}.",
            f"- Docker preflight pass: {coverage['docker_preflight_pass']}.",
            f"- Runner implemented: {coverage['runner_implemented']}.",
            f"- Method policy: `{coverage['method_policy_id']}`.",
            f"- Primary baseline: `{coverage['primary_baseline_policy_id']}`.",
            f"- Selected changed episode rows: {coverage['selected_policy_changed_episode_rows']}.",
            f"- Selected utility-promoted rows: {coverage['selected_policy_utility_promoted_rows']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            markdown_table(
                contract_rows,
                [
                    "policy_id",
                    "policy_role",
                    "episode_rows",
                    "candidate_rows",
                    "order_changed_episode_rows",
                    "utility_promotion_allowed_rows",
                    "method_policy",
                    "primary_baseline_policy",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "blocks_m157", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            markdown_table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Paper Claim Boundary",
            "",
            "- M156 supports only the budget-aware utility execution contract and Docker/data preflight.",
            "- M156 intentionally does not claim final real navigation `SR` / `SPL`, deployable search policy, or final real RGB-D/open-vocabulary robustness.",
            "- M157 must test whether the materialized utility policy beats the protected detector-confidence baseline without increasing visit cost.",
            "",
        ]
    )


def copy_support_files(output_dir: Path, candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in M149_SUPPORT_FILES:
        src = M149_DIR / filename
        if src.exists():
            shutil.copy2(src, output_dir / filename)
    for filename in M155_AUX_FILES:
        src = M155_DIR / filename
        if src.exists():
            shutil.copy2(src, output_dir / filename)
    write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(output_dir / "budget_aware_execution_plan_rows.jsonl", plan_rows)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m155_cov = read_json(M155_DIR / "coverage.json")
    base_candidate_rows = read_jsonl(M149_DIR / "base_candidate_rows.jsonl")
    raw_candidate_rows = read_jsonl(M155_DIR / "budget_aware_candidate_rows.jsonl")
    raw_plan_rows = read_jsonl(M155_DIR / "policy_plan_rows.jsonl")
    goal_rows = read_jsonl(M149_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M149_DIR / "oracle_path_rows.jsonl")
    matrix_rows = read_jsonl(M149_DIR / "trajectory_cost_matrix_rows.jsonl")
    input_contract_rows = read_jsonl(M149_DIR / "input_contract_rows.jsonl")
    m155_audit_rows = read_jsonl(M155_DIR / "policy_order_audit_rows.jsonl")
    m155_leakage_rows = read_jsonl(M155_DIR / "leakage_audit_rows.jsonl")

    if not m155_cov:
        raise SystemExit("missing M155 coverage.json")
    if not all([base_candidate_rows, raw_candidate_rows, raw_plan_rows, goal_rows, oracle_rows, input_contract_rows]):
        raise SystemExit("missing one or more required M149/M155 rows for M156")

    candidate_rows = normalize_candidate_rows(raw_candidate_rows)
    plan_rows = build_plan_rows(raw_plan_rows, candidate_rows, m155_audit_rows)
    contract_rows = build_execution_contract_rows(plan_rows, candidate_rows, m155_audit_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, input_contract_rows)

    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)
    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m157_compile = command_status(["python", "-m", "py_compile", str(M157_RUNNER)], timeout_s=30) if M157_RUNNER.exists() else None
    docker_rows = build_docker_preflight_rows(
        candidate_rows,
        docker_version_status,
        docker_image_status,
        nvidia_status,
        m37_compile,
        m157_compile,
    )
    gate_rows = build_readiness_gate_rows(
        m155_cov=m155_cov,
        base_candidate_rows=base_candidate_rows,
        candidate_rows=candidate_rows,
        plan_rows=plan_rows,
        goal_rows=goal_rows,
        oracle_rows=oracle_rows,
        matrix_rows=matrix_rows,
        m155_leakage_rows=m155_leakage_rows,
        m155_audit_rows=m155_audit_rows,
        leakage_rows=leakage_rows,
        docker_rows=docker_rows,
    )
    contract_ready = not any(row.get("blocks_m157") for row in gate_rows)
    runner_ready = M157_RUNNER.exists() and bool(m157_compile and m157_compile.get("ok"))
    route_rows = build_route_decision_rows(contract_ready, runner_ready)
    command_rows = build_m157_command_rows()
    claim_rows = build_claim_boundary_rows()

    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    selected_audits = [row for row in m155_audit_rows if row.get("policy_id") == METHOD_POLICY]
    docker_preflight_pass = all(row.get("status") in {"pass", "warning"} for row in docker_rows) and not any(
        row.get("status") == "fail" for row in docker_rows
    )
    if not contract_ready:
        status = BLOCKED_STATUS
    elif runner_ready:
        status = READY_STATUS
    else:
        status = READY_RUNNER_MISSING_STATUS

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m155_status": m155_cov.get("status"),
        "base_candidate_rows": len(base_candidate_rows),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "episode_rows": len({str(row.get("adapter_episode_id")) for row in plan_rows}),
        "scene_count": len({str(row.get("scene_key")) for row in plan_rows}),
        "policy_count": len(plan_counts),
        "policy_ids": sorted(plan_counts),
        "policy_plan_counts": dict(sorted(plan_counts.items())),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "full_val_mini_eval_goal_rows": len(goal_rows),
        "oracle_path_rows": len(oracle_rows),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "method_policy_id": METHOD_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE_POLICY,
        "selected_policy_changed_episode_rows": sum(1 for row in selected_audits if row.get("order_changed_vs_detector")),
        "selected_policy_utility_promoted_rows": sum(int(row.get("utility_promotion_allowed_rows") or 0) for row in selected_audits),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "docker_preflight_pass": docker_preflight_pass,
        "docker_cli_ok": bool(docker_version_status.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "nvidia_smi_ok": bool(nvidia_status.get("ok")),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "runner_script": str(M157_RUNNER.relative_to(ROOT)),
        "runner_implemented": M157_RUNNER.exists(),
        "runner_py_compile_pass": runner_ready,
        "trajectory_execution_contract_ready": contract_ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        copy_support_files(output_dir, candidate_rows, plan_rows)
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "trajectory_execution_contract_rows.jsonl", contract_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "m157_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, contract_rows, gate_rows, docker_rows),
        encoding="utf-8",
    )
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
