#!/usr/bin/env python3
"""Build the E008-M134 trajectory-aware repair trajectory contract and Docker preflight."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m134_target_free_trajectory_aware_repair_trajectory_contract_v0"
READY_STATUS = "e008_m134_target_free_trajectory_aware_repair_trajectory_contract_ready_runner_next"
READY_RUNNER_MISSING_STATUS = "e008_m134_target_free_trajectory_aware_repair_trajectory_contract_ready_runner_missing"
BLOCKED_STATUS = "e008_m134_target_free_trajectory_aware_repair_trajectory_contract_blocked"

M133_DIR = EXP_ROOT / "artifacts" / "E008-M133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0"
DATA_OUT_DIR = (
    ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0"
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
M135_RUNNER = EXP_ROOT / "tools" / "run_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke.py"
M135_ARTIFACT_DIR = (
    EXP_ROOT / "artifacts" / "E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0"
)
M135_DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0"
)
NEXT_UNIT = "E008-M135 target-free trajectory-aware repair trajectory execution smoke"

METHOD_POLICY = "trajectory_greedy_confidence_path_repair_v0"
PRIMARY_BASELINE_POLICY = "detector_confidence_reachable_subset_v0"
EXPECTED_POLICY_COUNT = 5
EXPECTED_SCAN_ROWS = 1
EXPECTED_PLAN_ROWS = EXPECTED_SCAN_ROWS * EXPECTED_POLICY_COUNT
EXPECTED_CANDIDATE_ROWS = 75
EXPECTED_MATRIX_ROWS = 225

CORE_INPUT_FILES = [
    "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
    "trajectory_execution_plan_rows.jsonl",
    "episode_goal_eval_rows.jsonl",
    "oracle_path_rows.jsonl",
]
M133_AUX_FILES = [
    "trajectory_cost_matrix_rows.jsonl",
    "trajectory_repair_candidate_rows.jsonl",
    "trajectory_repair_execution_plan_rows.jsonl",
    "input_contract_rows.jsonl",
    "leakage_audit_rows.jsonl",
    "readiness_gate_rows.jsonl",
    "policy_summary_rows.jsonl",
]

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "eval_all_viewpoint_count_loaded",
    "eval_geodesic_distance",
    "eval_euclidean_distance",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_first_viewpoint_3d_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
}


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


def build_execution_contract_rows(
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    policy_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_index = {str(row.get("policy_id")): row for row in plan_rows}
    summary_index = {str(row.get("policy_id")): row for row in policy_summary_rows}
    counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    path_counts = Counter(str(row.get("policy_id")) for row in candidate_rows if row.get("path_ready"))
    rows: list[dict[str, Any]] = []
    for policy_id in sorted(plan_index):
        plan = plan_index[policy_id]
        summary = summary_index.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "row_type": "trajectory_execution_contract",
                "policy_id": policy_id,
                "policy_role": plan.get("policy_role"),
                "method_policy": policy_id == METHOD_POLICY,
                "primary_baseline_policy": policy_id == PRIMARY_BASELINE_POLICY,
                "scan_id": plan.get("scan_id"),
                "adapter_episode_id": plan.get("adapter_episode_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "candidate_rows": counts.get(policy_id, 0),
                "path_ready_candidate_rows": path_counts.get(policy_id, 0),
                "planned_cumulative_path_cost_m": summary.get("planned_cumulative_path_cost_m"),
                "first_proposal_uid": summary.get("first_proposal_uid"),
                "first_current_pose_to_candidate_geodesic_m": summary.get(
                    "first_current_pose_to_candidate_geodesic_m"
                ),
                "runner_script": str(M135_RUNNER.relative_to(ROOT)),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "execution_plan_file": "trajectory_execution_plan_rows.jsonl",
                "execute_in_m135": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "claim_boundary": "M134 fixes the execution contract only; M135 is required for executed SR/SPL.",
            }
        )
    return rows


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads = [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
        ("trajectory_cost_matrix_rows", matrix_rows),
    ]
    out: list[dict[str, Any]] = []
    for payload, rows in payloads:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
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
    m135_compile: dict[str, Any] | None,
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
        {
            "version": VERSION,
            "check_id": "m37_generalized_runner_available",
            "status": "pass" if M37_RUNNER.exists() and m37_compile.get("ok") else "fail",
            "evidence": f"runner={M37_RUNNER.relative_to(ROOT)}; py_compile={bool(m37_compile.get('ok'))}.",
        },
        {
            "version": VERSION,
            "check_id": "m135_repair_runner_available",
            "status": "pass" if M135_RUNNER.exists() and m135_compile and m135_compile.get("ok") else "fail",
            "evidence": f"runner={M135_RUNNER.relative_to(ROOT)}; exists={M135_RUNNER.exists()}; py_compile={bool(m135_compile and m135_compile.get('ok'))}.",
        },
    ]


def build_m135_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke.py "
        "--m134-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M134_target_free_trajectory_aware_repair_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M135_RUNNER.relative_to(ROOT)),
            "runner_implemented": M135_RUNNER.exists(),
            "output_path": str(M135_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M135_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M135_target_free_trajectory_aware_repair_trajectory_execution_smoke_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m135_target_free_trajectory_aware_repair_trajectory_execution_smoke_ready'\n"
                "assert c['scan_task_policy_rows'] == 5\n"
                "print('m135 ready')\n"
                "PY"
            ),
        }
    ]


def build_readiness_gate_rows(
    m133_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    gates = [
        (
            "m133_materialization_ready",
            m133_cov.get("status") == "e008_m133_target_free_trajectory_aware_visit_order_repair_materialization_smoke_ready",
            f"M133 status={m133_cov.get('status')}.",
            True,
        ),
        (
            "runner_candidate_rows_copied",
            len(candidate_rows) == EXPECTED_CANDIDATE_ROWS and set(candidate_counts.values()) == {15},
            f"candidate rows={len(candidate_rows)}; counts={dict(sorted(candidate_counts.items()))}.",
            True,
        ),
        (
            "runner_plan_rows_copied",
            len(plan_rows) == EXPECTED_PLAN_ROWS and len(policy_counts) == EXPECTED_POLICY_COUNT,
            f"plan rows={len(plan_rows)}; policies={dict(sorted(policy_counts.items()))}.",
            True,
        ),
        (
            "goal_and_oracle_rows_ready",
            len(goal_rows) == EXPECTED_SCAN_ROWS and len(oracle_rows) == EXPECTED_SCAN_ROWS,
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
            "M134 is a contract/preflight unit; M135 should execute.",
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
            "blocks_m135": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "trajectory_repair_execution_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M134 provides a Docker-preflighted, runner-compatible one-case target-free trajectory-aware repair execution contract.",
        },
        {
            "version": VERSION,
            "claim_id": "trajectory_aware_repair_execution",
            "status": "not_executed",
            "safe_claim": "M134 does not execute Habitat trajectories; M135 is required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M135 execution, result interpretation, larger scale, and external navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "M134 target-free repair contract does not use human intent; E006-M08 remains the active human-intent boundary.",
        },
    ]


def build_route_decision_rows(contract_ready: bool, runner_ready: bool) -> list[dict[str, Any]]:
    if contract_ready and runner_ready:
        selected_next = NEXT_UNIT
        decision = "run_m135_target_free_trajectory_aware_repair_trajectory_smoke"
    elif contract_ready:
        selected_next = "E008-M135 target-free trajectory-aware repair trajectory execution runner scaffold"
        decision = "scaffold_m135_runner_before_docker_execution"
    else:
        selected_next = "repair E008-M134 target-free trajectory-aware repair trajectory contract"
        decision = "repair_m134_contract_or_preflight"
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m134_selected_next",
            "decision": decision,
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "reason": "M134 fixes the trajectory-aware repair execution input contract and Docker/data preflight; M135 should execute the bounded one-case trajectory smoke."
            if contract_ready
            else "One or more M134 contract/preflight gates failed.",
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
            "# E008-M134 Target-Free Trajectory-Aware Repair Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Eval goal rows: {coverage['target_free_eval_goal_rows']}.",
            f"- Oracle path rows: {coverage['oracle_path_rows']}.",
            f"- Docker preflight pass: {coverage['docker_preflight_pass']}.",
            f"- Runner implemented: {coverage['runner_implemented']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            markdown_table(
                contract_rows,
                [
                    "policy_id",
                    "policy_role",
                    "candidate_rows",
                    "path_ready_candidate_rows",
                    "planned_cumulative_path_cost_m",
                    "first_current_pose_to_candidate_geodesic_m",
                    "method_policy",
                    "primary_baseline_policy",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "blocks_m135", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            markdown_table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Paper Claim Boundary",
            "",
            "- M134 supports only the trajectory-aware repair execution contract and Docker/data preflight.",
            "- M134 intentionally does not claim final real navigation `SR` / `SPL`, deployable search policy, or final real RGB-D/open-vocabulary robustness.",
            "- The full-ranked execution mode tests one target-free repair case before any scale-up.",
            "",
        ]
    )


def copy_input_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in CORE_INPUT_FILES + M133_AUX_FILES:
        src = M133_DIR / filename
        if src.exists():
            shutil.copy2(src, output_dir / filename)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m133_cov = read_json(M133_DIR / "coverage.json")
    candidate_rows = read_jsonl(M133_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    plan_rows = read_jsonl(M133_DIR / "trajectory_execution_plan_rows.jsonl")
    goal_rows = read_jsonl(M133_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M133_DIR / "oracle_path_rows.jsonl")
    matrix_rows = read_jsonl(M133_DIR / "trajectory_cost_matrix_rows.jsonl")
    policy_summary_rows = read_jsonl(M133_DIR / "policy_summary_rows.jsonl")

    if not m133_cov:
        raise SystemExit("missing M133 coverage.json")
    if not all([candidate_rows, plan_rows, goal_rows, oracle_rows, matrix_rows, policy_summary_rows]):
        raise SystemExit("missing one or more required M133 rows for M134")

    contract_rows = build_execution_contract_rows(plan_rows, candidate_rows, policy_summary_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, matrix_rows)

    docker_version_status = command_status(["docker", "--version"], timeout_s=10)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    nvidia_status = command_status(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout_s=10)
    m37_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    m135_compile = command_status(["python", "-m", "py_compile", str(M135_RUNNER)], timeout_s=30) if M135_RUNNER.exists() else None
    docker_rows = build_docker_preflight_rows(
        candidate_rows,
        docker_version_status,
        docker_image_status,
        nvidia_status,
        m37_compile,
        m135_compile,
    )
    gate_rows = build_readiness_gate_rows(
        m133_cov,
        candidate_rows,
        plan_rows,
        goal_rows,
        oracle_rows,
        matrix_rows,
        leakage_rows,
        docker_rows,
    )
    contract_ready = not any(row.get("blocks_m135") for row in gate_rows)
    runner_ready = M135_RUNNER.exists() and bool(m135_compile and m135_compile.get("ok"))
    route_rows = build_route_decision_rows(contract_ready, runner_ready)
    command_rows = build_m135_command_rows()
    claim_rows = build_claim_boundary_rows()

    policy_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
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
        "m133_status": m133_cov.get("status"),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "policy_count": len(policy_counts),
        "policy_ids": sorted(policy_counts),
        "policy_plan_counts": dict(sorted(policy_counts.items())),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "target_free_eval_goal_rows": len(goal_rows),
        "oracle_path_rows": len(oracle_rows),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "method_policy_id": METHOD_POLICY,
        "primary_baseline_policy_id": PRIMARY_BASELINE_POLICY,
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "docker_preflight_pass": docker_preflight_pass,
        "docker_cli_ok": bool(docker_version_status.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "nvidia_smi_ok": bool(nvidia_status.get("ok")),
        "m37_runner_py_compile_pass": bool(m37_compile.get("ok")),
        "runner_script": str(M135_RUNNER.relative_to(ROOT)),
        "runner_implemented": M135_RUNNER.exists(),
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
        write_jsonl(output_dir / "m135_command_rows.jsonl", command_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, contract_rows, gate_rows, docker_rows),
        encoding="utf-8",
    )
    shutil.copy2(ARTIFACT_DIR / "report.md", DATA_OUT_DIR / "report.md")

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
