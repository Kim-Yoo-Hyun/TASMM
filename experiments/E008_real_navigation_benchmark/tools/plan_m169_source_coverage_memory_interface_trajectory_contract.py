#!/usr/bin/env python3
"""Build E008-M169 source-coverage memory-interface trajectory contract."""

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
M156_DIR = EXP_ROOT / "artifacts" / "E008-M156_budget_aware_utility_trajectory_contract_v0"
M168_DIR = EXP_ROOT / "artifacts" / "E008-M168_source_coverage_memory_interface_materialization_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M169_source_coverage_memory_interface_trajectory_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M169_source_coverage_memory_interface_trajectory_contract_v0"

VERSION = "e008_m169_source_coverage_memory_interface_trajectory_contract_v0"
READY_STATUS = "e008_m169_source_coverage_memory_interface_trajectory_contract_ready_runner_next"
BLOCKED_STATUS = "e008_m169_source_coverage_memory_interface_trajectory_contract_blocked"
NEXT_UNIT = "E008-M170 source-coverage memory-interface trajectory execution"

HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
DOCKER_DATA_ROOT = Path("/data")
OBJECTNAV_CONTENT_ROOT = RESEARCH3_DATA_ROOT / "datasets" / "objectnav" / "hm3d" / "v2" / "objectnav_hm3d_v2" / "val_mini" / "content"

SELECTED_POLICY = "source_coverage_memory_interface_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
RUNNER = EXP_ROOT / "tools" / "run_m170_source_coverage_memory_interface_trajectory_execution.py"
M170_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"
M170_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M170_source_coverage_memory_interface_trajectory_execution_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
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
    path.write_text(json.dumps(sanitize_json(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


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


def int_value(value: object, default: int = 10**9) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in cols) + " |")
    return "\n".join(lines)


def command_status(cmd: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s, check=False)
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "",
        }
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_tail": proc.stdout[-500:], "stderr_tail": proc.stderr[-500:]}


def host_path_from_docker(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        rel = path.relative_to(DOCKER_DATA_ROOT)
    except ValueError:
        return None
    return RESEARCH3_DATA_ROOT / rel


def normalize_candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        policy_id = str(row.get("policy_id"))
        payload = dict(row)
        payload.update(
            {
                "version": VERSION,
                "m168_materialization_version": row.get("version"),
                "execution_contract_version": VERSION,
                "row_type": "dynamic_stale_overlay_trajectory_candidate",
                "claim_boundary": "M169 fixes runner-compatible source-coverage memory-interface trajectory inputs only; no Habitat trajectory is executed.",
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
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


def build_plan_rows(m168_plans: list[dict[str, Any]], candidate_rows: list[dict[str, Any]], audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row.get("benchmark_row_uid")), str(row.get("policy_id")))].append(row)
    audit_index = {(str(row.get("benchmark_row_uid")), str(row.get("policy_id"))): row for row in audit_rows}
    out = []
    for plan in m168_plans:
        uid = str(plan.get("benchmark_row_uid"))
        policy_id = str(plan.get("policy_id"))
        rows = sorted(grouped[(uid, policy_id)], key=lambda row: int_value(row.get("visit_rank")))
        first = rows[0] if rows else {}
        last = rows[-1] if rows else {}
        audit = audit_index.get((uid, policy_id), {})
        out.append(
            {
                **plan,
                "version": VERSION,
                "m168_materialization_version": plan.get("version"),
                "execution_contract_version": VERSION,
                "row_type": "trajectory_execution_plan",
                "policy_role": first.get("policy_role") or plan.get("policy_role"),
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
                "execute_in_next_runner": True,
                "requires_docker": True,
                "runner_script": str(RUNNER.relative_to(ROOT)),
                "runner_input_ready": bool(rows),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in materialized visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "start_state_source": "ObjectNav episode start state from episode_goal_eval_rows; goal/viewpoints are metric-only",
                "candidate_budget": len(rows),
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": sum(bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True)) for row in rows),
                "blocked_candidate_rows": sum(not (bool(row.get("path_ready")) and bool(row.get("candidate_usable_for_path_smoke", True))) for row in rows),
                "planned_cumulative_path_cost_m": last.get("m168_planned_cumulative_path_cost_proxy_m"),
                "first_confidence": first.get("confidence"),
                "first_current_pose_to_candidate_geodesic_m": first.get("source_to_candidate_path_cost_m"),
                "current_observation_first": str(first.get("candidate_source_role")) == "current_observation",
                "stale_visit_first": False,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "diagnostic_source_gap_boundary_for_reporting": any(bool(row.get("m168_source_gap_prelabel")) for row in rows),
                "order_changed_vs_detector": bool(audit.get("order_changed_vs_detector")),
                "promoted_rows": audit.get("promoted_rows"),
                "demoted_rows": audit.get("demoted_rows"),
                "max_rank_displacement_abs_from_detector": audit.get("max_rank_displacement_abs_from_detector"),
                "uses_task_context_for_decision": False,
                "uses_trajectory_cost_matrix_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M169 is a Docker trajectory contract/preflight unit; M170 is required for executed SR/SPL.",
            }
        )
    return out


def leakage_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for payload, rows in [("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows), ("trajectory_execution_plan_rows", plan_rows)]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            if row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") or row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
            for field in ["eval_goal_position", "eval_first_viewpoint_position", "eval_all_viewpoint_positions", "primary_eval_hit", "SR", "SPL", "success_proposal_uid"]:
                if field in row and row.get(field) not in {None, "", False, 0}:
                    field_hits[field] += 1
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


def docker_preflight_rows(candidate_rows: list[dict[str, Any]], runner_compile: dict[str, Any]) -> list[dict[str, Any]]:
    docker_version = command_status(["docker", "--version"])
    image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE])
    nvidia_status = command_status(["nvidia-smi"])
    scene_paths = sorted({str(row.get("scene_docker_path")) for row in candidate_rows if row.get("scene_docker_path")})
    navmesh_paths = sorted({str(row.get("navmesh_docker_path")) for row in candidate_rows if row.get("navmesh_docker_path")})
    scene_ready = sum(1 for path in scene_paths if (host_path_from_docker(path) or Path("__missing__")).exists())
    navmesh_ready = sum(1 for path in navmesh_paths if (host_path_from_docker(path) or Path("__missing__")).exists())
    content_files = list(OBJECTNAV_CONTENT_ROOT.glob("*.json.gz")) if OBJECTNAV_CONTENT_ROOT.exists() else []
    return [
        {"version": VERSION, "check_id": "docker_cli", "status": "pass" if docker_version.get("ok") else "fail", "evidence": f"returncode={docker_version.get('returncode')}; stderr_tail={docker_version.get('stderr_tail')!r}."},
        {"version": VERSION, "check_id": "habitat_docker_image", "status": "pass" if image_status.get("ok") else "fail", "evidence": f"image={HABITAT_IMAGE}; returncode={image_status.get('returncode')}; stderr_tail={image_status.get('stderr_tail')!r}."},
        {"version": VERSION, "check_id": "nvidia_smi", "status": "pass" if nvidia_status.get("ok") else "warning", "evidence": f"returncode={nvidia_status.get('returncode')}; stdout_tail={nvidia_status.get('stdout_tail')!r}; stderr_tail={nvidia_status.get('stderr_tail')!r}."},
        {"version": VERSION, "check_id": "read_only_hm3d_data_root", "status": "pass" if RESEARCH3_DATA_ROOT.exists() else "fail", "evidence": f"path={RESEARCH3_DATA_ROOT}; exists={RESEARCH3_DATA_ROOT.exists()}."},
        {"version": VERSION, "check_id": "scene_files", "status": "pass" if scene_ready == len(scene_paths) and bool(scene_paths) else "fail", "evidence": f"ready={scene_ready}/{len(scene_paths)}."},
        {"version": VERSION, "check_id": "navmesh_files", "status": "pass" if navmesh_ready == len(navmesh_paths) and bool(navmesh_paths) else "fail", "evidence": f"ready={navmesh_ready}/{len(navmesh_paths)}."},
        {"version": VERSION, "check_id": "objectnav_content_files", "status": "pass" if content_files else "fail", "evidence": f"path={OBJECTNAV_CONTENT_ROOT}; json_gz_files={len(content_files)}."},
        {"version": VERSION, "check_id": "m170_runner_available", "status": "pass" if RUNNER.exists() and runner_compile.get("ok") else "fail", "evidence": f"runner={RUNNER.relative_to(ROOT)}; exists={RUNNER.exists()}; py_compile={bool(runner_compile.get('ok'))}."},
    ]


def execution_contract_rows(plan_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]], audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    changed_counts = Counter(str(row.get("policy_id")) for row in audit_rows if row.get("order_changed_vs_detector"))
    promoted = defaultdict(int)
    for row in audit_rows:
        promoted[str(row.get("policy_id"))] += int(row.get("promoted_rows") or 0)
    role_index = {str(row.get("policy_id")): row.get("policy_role") for row in plan_rows}
    return [
        {
            "version": VERSION,
            "row_type": "trajectory_execution_contract",
            "policy_id": policy_id,
            "policy_role": role_index.get(policy_id),
            "method_policy": policy_id == SELECTED_POLICY,
            "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
            "episode_rows": plan_counts[policy_id],
            "candidate_rows": candidate_counts[policy_id],
            "order_changed_episode_rows": changed_counts[policy_id],
            "promoted_rows": promoted[policy_id],
            "runner_script": str(RUNNER.relative_to(ROOT)),
            "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
            "execution_plan_file": "trajectory_execution_plan_rows.jsonl",
            "execute_in_m170": True,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
            "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            "claim_boundary": "M169 fixes execution contract only; M170 is required for executed SR/SPL.",
        }
        for policy_id in sorted(plan_counts)
    ]


def readiness_rows(m168: dict[str, Any], candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]], goal_rows: list[dict[str, Any]], oracle_rows: list[dict[str, Any]], leaks: list[dict[str, Any]], docker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    plan_counts = Counter(str(row.get("policy_id")) for row in plan_rows)
    gates = [
        ("m168_materialization_ready", m168.get("status") == "e008_m168_source_coverage_memory_interface_materialization_ready", f"M168 status={m168.get('status')}.", True),
        ("runner_candidate_rows_written", len(candidate_rows) == 4500 and set(candidate_counts.values()) == {900}, f"candidate rows={len(candidate_rows)}; counts={dict(sorted(candidate_counts.items()))}.", True),
        ("runner_plan_rows_written", len(plan_rows) == 150 and set(plan_counts.values()) == {30}, f"plan rows={len(plan_rows)}; counts={dict(sorted(plan_counts.items()))}.", True),
        ("goal_and_oracle_rows_ready", len(goal_rows) == 30 and len(oracle_rows) == 30, f"goal rows={len(goal_rows)}; oracle rows={len(oracle_rows)}.", True),
        ("method_and_primary_baseline_present", SELECTED_POLICY in candidate_counts and PROTECTED_BASELINE in candidate_counts, f"method={SELECTED_POLICY in candidate_counts}; protected={PROTECTED_BASELINE in candidate_counts}.", True),
        ("leakage_audit_pass", all(row.get("leakage_audit_pass") for row in leaks), f"failed={sum(1 for row in leaks if not row.get('leakage_audit_pass'))}.", True),
        ("docker_preflight", all(row.get("status") in {"pass", "warning"} for row in docker_rows) and not any(row.get("status") == "fail" for row in docker_rows), f"fail={sum(1 for row in docker_rows if row.get('status') == 'fail')}; warning={sum(1 for row in docker_rows if row.get('status') == 'warning')}.", True),
        ("execute_trajectories_now", False, "M169 is a contract/preflight unit; M170 should execute.", False),
    ]
    return [
        {"version": VERSION, "row_type": "readiness_gate", "gate_id": gate_id, "status": "pass" if passed else "fail", "passed": passed, "blocks_m170": blocks and not passed, "evidence": evidence}
        for gate_id, passed, evidence, blocks in gates
    ]


def command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research3/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m170_source_coverage_memory_interface_trajectory_execution.py "
        "--m169-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M169_source_coverage_memory_interface_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M170_source_coverage_memory_interface_trajectory_execution_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m170_source_coverage_memory_interface_trajectory_execution",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research3/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(RUNNER.relative_to(ROOT)),
            "runner_implemented": RUNNER.exists(),
            "output_path": str(M170_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M170_DATA_OUT_DIR.relative_to(ROOT)),
            "log_template": "logs/<YYYYMMDD_HHMMSS>_e008_m170_source_coverage_memory_interface_trajectory.log",
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M170_source_coverage_memory_interface_trajectory_execution_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m170_source_coverage_memory_interface_trajectory_execution_ready'\n"
                "assert c['scan_task_policy_rows'] == 150\n"
                "print('m170 ready')\n"
                "PY"
            ),
        }
    ]


def claim_rows() -> list[dict[str, Any]]:
    return [
        {"version": VERSION, "claim_id": "docker_trajectory_contract_ready", "status": "supported_contract_only", "safe_claim": "M169 provides a Docker-preflighted, runner-compatible execution contract."},
        {"version": VERSION, "claim_id": "source_coverage_memory_interface_execution", "status": "not_executed", "safe_claim": "M169 does not execute trajectories; M170 is required."},
        {"version": VERSION, "claim_id": "positive_navigation_improvement", "status": "blocked", "safe_claim": "Requires M170 execution and M171 protected-baseline interpretation."},
    ]


def report(coverage: dict[str, Any], contracts: list[dict[str, Any]], gates: list[dict[str, Any]], docker_rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# E008-M169 Source-Coverage Memory-Interface Trajectory Contract",
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
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Contract",
            "",
            table(contracts, ["policy_id", "policy_role", "episode_rows", "candidate_rows", "order_changed_episode_rows", "promoted_rows", "method_policy", "primary_baseline_policy"]),
            "",
            "## Gates",
            "",
            table(gates, ["gate_id", "status", "blocks_m170", "evidence"]),
            "",
            "## Docker Preflight",
            "",
            table(docker_rows, ["check_id", "status", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M169 is a contract/preflight step and does not execute `Habitat` trajectories.",
            "- M170 should be launched as a background Docker job if execution is requested.",
            "- Positive navigation claims require M170 execution and M171 protected-baseline interpretation.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m168 = read_json(M168_DIR / "coverage.json")
    m168_candidates = read_jsonl(M168_DIR / "source_coverage_candidate_rows.jsonl")
    m168_plans = read_jsonl(M168_DIR / "policy_plan_rows.jsonl")
    m168_audit = read_jsonl(M168_DIR / "policy_order_audit_rows.jsonl")
    goal_rows = read_jsonl(M156_DIR / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(M156_DIR / "oracle_path_rows.jsonl")
    matrix_rows = read_jsonl(M156_DIR / "trajectory_cost_matrix_rows.jsonl")
    input_contract_rows = read_jsonl(M156_DIR / "input_contract_rows.jsonl")

    missing = []
    if m168.get("status") != "e008_m168_source_coverage_memory_interface_materialization_ready":
        missing.append("M168 ready coverage")
    if not m168_candidates or not m168_plans:
        missing.append("M168 materialized rows")
    if len(goal_rows) != 30 or len(oracle_rows) != 30:
        missing.append("M156 goal/oracle rows")

    candidate_rows = normalize_candidate_rows(m168_candidates)
    plan_rows = build_plan_rows(m168_plans, candidate_rows, m168_audit)
    leaks = leakage_rows(candidate_rows, plan_rows)
    runner_compile = command_status(["python", "-m", "py_compile", str(RUNNER.relative_to(ROOT))])
    docker_rows = docker_preflight_rows(candidate_rows, runner_compile)
    contracts = execution_contract_rows(plan_rows, candidate_rows, m168_audit)
    gates = readiness_rows(m168, candidate_rows, plan_rows, goal_rows, oracle_rows, leaks, docker_rows)
    blocker_count = sum(1 for row in gates if row.get("blocks_m170"))
    ready = not missing and blocker_count == 0

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "missing_inputs": missing,
        "m168_status": m168.get("status"),
        "selected_policy_id": SELECTED_POLICY,
        "protected_baseline_policy_id": PROTECTED_BASELINE,
        "policy_ids": sorted({str(row.get("policy_id")) for row in plan_rows}),
        "policy_count": len({str(row.get("policy_id")) for row in plan_rows}),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "full_val_mini_eval_goal_rows": len(goal_rows),
        "oracle_path_rows": len(oracle_rows),
        "trajectory_cost_matrix_rows": len(matrix_rows),
        "input_contract_rows": len(input_contract_rows),
        "trajectory_execution_contract_rows": len(contracts),
        "readiness_gate_rows": len(gates),
        "readiness_blocker_rows": blocker_count,
        "leakage_audit_rows": len(leaks),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leaks),
        "docker_preflight_rows": len(docker_rows),
        "docker_preflight_pass": not any(row.get("status") == "fail" for row in docker_rows),
        "runner_implemented": RUNNER.exists(),
        "runner_py_compile_pass": bool(runner_compile.get("ok")),
        "runner_script": str(RUNNER.relative_to(ROOT)),
        "trajectory_execution_contract_ready": ready,
        "trajectory_execution_result_ready": False,
        "positive_navigation_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": NEXT_UNIT if ready else "repair E008-M169 source-coverage memory-interface trajectory contract",
    }

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_plan_rows.jsonl", plan_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_execution_contract_rows.jsonl", contracts)
    write_jsonl(ARTIFACT_DIR / "docker_preflight_rows.jsonl", docker_rows)
    write_jsonl(ARTIFACT_DIR / "readiness_gate_rows.jsonl", gates)
    write_jsonl(ARTIFACT_DIR / "leakage_audit_rows.jsonl", leaks)
    write_jsonl(ARTIFACT_DIR / "m170_command_rows.jsonl", command_rows())
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_rows())
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", [{"version": VERSION, "decision": "run_m170_source_coverage_memory_interface_trajectory_execution" if ready else "repair_m169_contract", "selected_next_unit": coverage["selected_next_unit"], "launch_long_job_now": False}])
    write_jsonl(ARTIFACT_DIR / "episode_goal_eval_rows.jsonl", goal_rows)
    write_jsonl(ARTIFACT_DIR / "oracle_path_rows.jsonl", oracle_rows)
    write_jsonl(ARTIFACT_DIR / "trajectory_cost_matrix_rows.jsonl", matrix_rows)
    write_jsonl(ARTIFACT_DIR / "input_contract_rows.jsonl", input_contract_rows)
    (ARTIFACT_DIR / "report.md").write_text(report(coverage, contracts, gates, docker_rows), encoding="utf-8")

    if DATA_OUT_DIR.exists():
        shutil.rmtree(DATA_OUT_DIR)
    shutil.copytree(ARTIFACT_DIR, DATA_OUT_DIR)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
