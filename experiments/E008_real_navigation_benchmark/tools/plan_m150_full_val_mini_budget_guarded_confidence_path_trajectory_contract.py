#!/usr/bin/env python3
"""Build E008-M150 budget-guarded confidence/path trajectory execution contract."""

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

VERSION = "e008_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0"
READY_STATUS = "e008_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_ready_runner_next"
READY_RUNNER_MISSING_STATUS = "e008_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_ready_runner_missing"
BLOCKED_STATUS = "e008_m150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_blocked"

M149_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M149_full_val_mini_budget_guarded_confidence_path_materialization_smoke_v0"
)
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0"
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
M151_RUNNER = EXP_ROOT / "tools" / "run_m151_full_val_mini_budget_guarded_confidence_path_execution.py"
M151_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
)
M151_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0"
)
NEXT_UNIT = "E008-M151 full-val-mini budget-guarded confidence/path trajectory execution"

METHOD_POLICY = "budget_guarded_confidence_path_repair_v1"
PRIMARY_BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
EXPECTED_POLICY_COUNT = 6
EXPECTED_EPISODE_ROWS = 30
EXPECTED_PLAN_ROWS = EXPECTED_EPISODE_ROWS * EXPECTED_POLICY_COUNT
EXPECTED_CANDIDATE_ROWS = 5400
EXPECTED_BASE_CANDIDATE_ROWS = 900
EXPECTED_MATRIX_ROWS = 33354

CORE_INPUT_FILES = [
    "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
    "trajectory_execution_plan_rows.jsonl",
    "episode_goal_eval_rows.jsonl",
    "oracle_path_rows.jsonl",
    "input_contract_rows.jsonl",
]
M149_AUX_FILES = [
    "base_candidate_rows.jsonl",
    "trajectory_cost_matrix_rows.jsonl",
    "budget_guarded_candidate_rows.jsonl",
    "budget_guarded_execution_plan_rows.jsonl",
    "policy_summary_rows.jsonl",
    "policy_order_audit_rows.jsonl",
    "budget_guard_audit_rows.jsonl",
    "budget_guard_audit_summary_rows.jsonl",
    "leakage_audit_rows.jsonl",
    "readiness_gate_rows.jsonl",
    "m148_policy_contract_rows.jsonl",
    "m148_trigger_contract_rows.jsonl",
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


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


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


def build_policy_order_summary(order_audit_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in order_audit_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    return {
        policy_id: {
            "episode_rows": len(rows),
            "detector_order_identical_rows": sum(1 for row in rows if row.get("detector_order_identical")),
            "hard_feasibility_veto_count": sum(int(row.get("hard_feasibility_veto_count") or 0) for row in rows),
            "confidence_band_violation_count": sum(
                int(row.get("confidence_band_violation_count") or 0) for row in rows
            ),
            "rank_displacement_violation_count": sum(
                int(row.get("rank_displacement_violation_count") or 0) for row in rows
            ),
            "budget_repair_trigger_rows": sum(int(row.get("budget_repair_trigger_rows") or 0) for row in rows),
            "audit_pass": all(row.get("audit_pass") for row in rows),
        }
        for policy_id, rows in by_policy.items()
    }


def build_execution_contract_rows(
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    policy_summary_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
    order_audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    path_counts = Counter(str(row.get("policy_id")) for row in candidate_rows if row.get("path_ready"))
    summary_index = {str(row.get("policy_id")): row for row in policy_summary_rows}
    budget_index = {str(row.get("policy_id")): row for row in budget_summary_rows}
    order_index = build_policy_order_summary(order_audit_rows)
    rows: list[dict[str, Any]] = []
    for policy_id in sorted(plan_counts):
        summary = summary_index.get(policy_id, {})
        budget = budget_index.get(policy_id, {})
        order = order_index.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "row_type": "trajectory_execution_contract",
                "policy_id": policy_id,
                "policy_role": summary.get("policy_role") or next(
                    (row.get("policy_role") for row in plan_rows if row.get("policy_id") == policy_id),
                    None,
                ),
                "method_policy": policy_id == METHOD_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE_POLICY,
                "episode_rows": plan_counts.get(policy_id, 0),
                "candidate_rows": candidate_counts.get(policy_id, 0),
                "path_ready_candidate_rows": path_counts.get(policy_id, 0),
                "planned_cumulative_path_cost_m_mean": summary.get("planned_cumulative_path_cost_m_mean"),
                "detector_order_identical_episode_rows": summary.get("detector_order_identical_rows"),
                "path_repair_trigger_rows": summary.get("path_repair_trigger_rows"),
                "hard_feasibility_veto_rows": summary.get("hard_feasibility_veto_rows"),
                "max_rank_displacement_abs_from_detector": summary.get("max_rank_displacement_abs_from_detector"),
                "budget_guard_pass_rows": budget.get("guard_pass_rows"),
                "planned_candidate_row_delta_vs_detector_sum": budget.get(
                    "planned_candidate_row_delta_vs_detector_sum"
                ),
                "confidence_band_violation_count": order.get("confidence_band_violation_count"),
                "rank_displacement_violation_count": order.get("rank_displacement_violation_count"),
                "policy_order_audit_pass": order.get("audit_pass"),
                "runner_script": str(M151_RUNNER.relative_to(ROOT)),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_plan_file": "trajectory_execution_plan_rows.jsonl",
                "execute_in_m151": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M150 fixes the budget-guarded full-val-mini execution contract only; M151 is required for executed SR/SPL.",
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    input_contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked_fields = {
        str(row.get("field"))
        for row in input_contract_rows
        if row.get("contract_group") == "blocked_policy_input"
    }
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
    m151_compile: dict[str, Any] | None,
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
            "check_id": "m151_budget_guarded_runner_available",
            "status": "pass" if M151_RUNNER.exists() and m151_compile and m151_compile.get("ok") else "fail",
            "evidence": f"runner={M151_RUNNER.relative_to(ROOT)}; exists={M151_RUNNER.exists()}; py_compile={bool(m151_compile and m151_compile.get('ok'))}.",
        },
    ]


def build_m151_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m151_full_val_mini_budget_guarded_confidence_path_execution.py "
        "--m150-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M150_full_val_mini_budget_guarded_confidence_path_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m151_full_val_mini_budget_guarded_confidence_path_execution",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M151_RUNNER.relative_to(ROOT)),
            "runner_implemented": M151_RUNNER.exists(),
            "output_path": str(M151_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M151_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M151_full_val_mini_budget_guarded_confidence_path_execution_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m151_full_val_mini_budget_guarded_confidence_path_execution_ready'\n"
                "assert c['scan_task_policy_rows'] == 180\n"
                "print('m151 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    m149_cov: dict[str, Any],
    base_candidate_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
    order_audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    episode_count = len({str(row.get("adapter_episode_id")) for row in plan_rows})
    selected_budget = next((row for row in budget_summary_rows if row.get("policy_id") == METHOD_POLICY), {})
    selected_order = [
        row for row in order_audit_rows if row.get("policy_id") == METHOD_POLICY
    ]
    gates = [
        (
            "m149_materialization_ready",
            m149_cov.get("status") == "e008_m149_full_val_mini_budget_guarded_confidence_path_materialization_ready",
            f"M149 status={m149_cov.get('status')}.",
            True,
        ),
        (
            "base_candidate_denominator_preserved",
            len(base_candidate_rows) == EXPECTED_BASE_CANDIDATE_ROWS,
            f"base candidates={len(base_candidate_rows)}; expected={EXPECTED_BASE_CANDIDATE_ROWS}.",
            True,
        ),
        (
            "runner_candidate_rows_copied",
            len(candidate_rows) == EXPECTED_CANDIDATE_ROWS
            and set(candidate_counts.values()) == {EXPECTED_BASE_CANDIDATE_ROWS},
            f"candidate rows={len(candidate_rows)}; counts={dict(sorted(candidate_counts.items()))}.",
            True,
        ),
        (
            "runner_plan_rows_copied",
            len(plan_rows) == EXPECTED_PLAN_ROWS
            and len(plan_counts) == EXPECTED_POLICY_COUNT
            and episode_count == EXPECTED_EPISODE_ROWS,
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
            "trajectory_cost_matrix_ready",
            len(matrix_rows) == EXPECTED_MATRIX_ROWS,
            f"matrix rows={len(matrix_rows)}; expected={EXPECTED_MATRIX_ROWS}.",
            True,
        ),
        (
            "method_and_primary_baseline_present",
            METHOD_POLICY in candidate_counts and PRIMARY_BASELINE_POLICY in candidate_counts,
            f"method={METHOD_POLICY in candidate_counts}; primary_baseline={PRIMARY_BASELINE_POLICY in candidate_counts}.",
            True,
        ),
        (
            "selected_budget_guard_pass",
            bool(selected_budget)
            and selected_budget.get("guard_pass_rows") == EXPECTED_EPISODE_ROWS
            and selected_budget.get("max_rank_displacement_abs_from_detector") == 1,
            f"selected_budget={selected_budget}.",
            True,
        ),
        (
            "selected_order_audit_pass",
            len(selected_order) == EXPECTED_EPISODE_ROWS
            and all(row.get("audit_pass") for row in selected_order)
            and sum(int(row.get("confidence_band_violation_count") or 0) for row in selected_order) == 0
            and sum(int(row.get("rank_displacement_violation_count") or 0) for row in selected_order) == 0,
            f"selected_order_rows={len(selected_order)}.",
            True,
        ),
        (
            "policy_input_leakage",
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
            "M150 is a contract/preflight unit; M151 should execute.",
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
            "blocks_m151": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "full_val_mini_budget_guarded_execution_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M150 provides a Docker-preflighted, runner-compatible full-val-mini budget-guarded trajectory execution contract.",
        },
        {
            "version": VERSION,
            "claim_id": "full_val_mini_budget_guarded_execution",
            "status": "not_executed",
            "safe_claim": "M150 does not execute Habitat trajectories; M151 is required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M151 execution, M152 interpretation, heldout transfer, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "M150 target-free execution contract does not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(contract_ready: bool, runner_ready: bool) -> list[dict[str, Any]]:
    if contract_ready and runner_ready:
        selected_next = NEXT_UNIT
        decision = "run_m151_full_val_mini_budget_guarded_confidence_path_execution"
    elif contract_ready:
        selected_next = "E008-M151 full-val-mini budget-guarded confidence/path execution runner scaffold"
        decision = "scaffold_m151_runner_before_docker_execution"
    else:
        selected_next = "repair E008-M150 full-val-mini budget-guarded confidence/path trajectory contract"
        decision = "repair_m150_contract_or_preflight"
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m150_selected_next",
            "decision": decision,
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "reason": "M150 fixes the full-val-mini budget-guarded execution input contract and Docker/data preflight; M151 should execute trajectories."
            if contract_ready
            else "One or more M150 contract/preflight gates failed.",
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
            "# E008-M150 Full-Val-Mini Budget-Guarded Confidence/Path Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Base candidate rows: {coverage['base_candidate_rows']}.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Eval goal rows: {coverage['full_val_mini_eval_goal_rows']}.",
            f"- Oracle path rows: {coverage['oracle_path_rows']}.",
            f"- Docker preflight pass: {coverage['docker_preflight_pass']}.",
            f"- Runner implemented: {coverage['runner_implemented']}.",
            f"- Method policy: `{coverage['method_policy_id']}`.",
            f"- Primary baseline: `{coverage['primary_baseline_policy_id']}`.",
            f"- Selected repair-trigger rows: {coverage['selected_policy_path_repair_trigger_rows']}.",
            f"- Selected hard-veto rows: {coverage['selected_policy_hard_veto_rows']}.",
            f"- Selected max rank displacement: {coverage['selected_policy_max_rank_displacement_abs']}.",
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
                    "planned_cumulative_path_cost_m_mean",
                    "path_repair_trigger_rows",
                    "max_rank_displacement_abs_from_detector",
                    "method_policy",
                    "primary_baseline_policy",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "blocks_m151", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            markdown_table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Paper Claim Boundary",
            "",
            "- M150 supports only the full-val-mini budget-guarded execution contract and Docker/data preflight.",
            "- M150 intentionally does not claim final real navigation `SR` / `SPL`, deployable search policy, or final real RGB-D/open-vocabulary robustness.",
            "- M151 must test whether budget-guarded local path repair can beat the protected detector-confidence baseline without increasing visit cost.",
            "",
        ]
    )


def copy_input_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in CORE_INPUT_FILES + M149_AUX_FILES:
        src = M149_DIR / filename
        if src.exists():
            shutil.copy2(src, output_dir / filename)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m149_cov = read_json(M149_DIR / "coverage.json")
    base_candidate_rows = read_jsonl(M149_DIR / "base_candidate_rows.jsonl")
    candidate_rows = read_jsonl(M149_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M149_DIR / "trajectory_execution_plan_rows.jsonl")
    goal_rows = read_jsonl(M149_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M149_DIR / "oracle_path_rows.jsonl")
    matrix_rows = read_jsonl(M149_DIR / "trajectory_cost_matrix_rows.jsonl")
    policy_summary_rows = read_jsonl(M149_DIR / "policy_summary_rows.jsonl")
    budget_summary_rows = read_jsonl(M149_DIR / "budget_guard_audit_summary_rows.jsonl")
    order_audit_rows = read_jsonl(M149_DIR / "policy_order_audit_rows.jsonl")
    input_contract_rows = read_jsonl(M149_DIR / "input_contract_rows.jsonl")

    if not m149_cov:
        raise SystemExit("missing M149 coverage.json")
    if not all(
        [
            base_candidate_rows,
            candidate_rows,
            plan_rows,
            goal_rows,
            oracle_rows,
            matrix_rows,
            policy_summary_rows,
            budget_summary_rows,
            order_audit_rows,
            input_contract_rows,
        ]
    ):
        raise SystemExit("missing one or more required M149 rows for M150")

    contract_rows = build_execution_contract_rows(
        plan_rows,
        candidate_rows,
        policy_summary_rows,
        budget_summary_rows,
        order_audit_rows,
    )
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, input_contract_rows)
    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)
    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m151_compile = command_status(["python", "-m", "py_compile", str(M151_RUNNER)], timeout_s=30) if M151_RUNNER.exists() else None
    docker_rows = build_docker_preflight_rows(
        candidate_rows,
        docker_version_status,
        docker_image_status,
        nvidia_status,
        m37_compile,
        m151_compile,
    )
    gate_rows = build_readiness_gate_rows(
        m149_cov,
        base_candidate_rows,
        candidate_rows,
        plan_rows,
        goal_rows,
        oracle_rows,
        matrix_rows,
        leakage_rows,
        docker_rows,
        budget_summary_rows,
        order_audit_rows,
    )
    contract_ready = not any(row.get("blocks_m151") for row in gate_rows)
    runner_ready = M151_RUNNER.exists() and bool(m151_compile and m151_compile.get("ok"))
    route_rows = build_route_decision_rows(contract_ready, runner_ready)
    command_rows = build_m151_command_rows()
    claim_rows = build_claim_boundary_rows()

    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    selected_summary = next((row for row in policy_summary_rows if row.get("policy_id") == METHOD_POLICY), {})
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
        "m149_status": m149_cov.get("status"),
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
        "selected_policy_path_repair_trigger_rows": selected_summary.get("path_repair_trigger_rows", 0),
        "selected_policy_hard_veto_rows": selected_summary.get("hard_feasibility_veto_rows", 0),
        "selected_policy_max_rank_displacement_abs": selected_summary.get(
            "max_rank_displacement_abs_from_detector", 0
        ),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "docker_preflight_pass": docker_preflight_pass,
        "docker_cli_ok": bool(docker_version_status.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "nvidia_smi_ok": bool(nvidia_status.get("ok")),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "runner_script": str(M151_RUNNER.relative_to(ROOT)),
        "runner_implemented": M151_RUNNER.exists(),
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
        copy_input_files(output_dir)
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "trajectory_execution_contract_rows.jsonl", contract_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "m151_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, contract_rows, gate_rows, docker_rows),
        encoding="utf-8",
    )
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
