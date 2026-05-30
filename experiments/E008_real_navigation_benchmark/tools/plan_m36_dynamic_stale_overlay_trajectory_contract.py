#!/usr/bin/env python3
"""Build the E008-M36 dynamic-stale overlay trajectory contract."""

from __future__ import annotations

import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M36_dynamic_stale_overlay_trajectory_contract_v0"
VERSION = "e008_m36_dynamic_stale_overlay_trajectory_contract_v0"

M35_DIR = EXP_ROOT / "artifacts" / "E008-M35_dynamic_stale_overlay_materialization_smoke_v0"
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
M37_RUNNER = EXP_ROOT / "tools" / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M37_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
M37_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0"
NEXT_UNIT = "E008-M37 dynamic-stale overlay trajectory execution smoke"

BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id",
    "eval_goal_position",
    "eval_first_viewpoint_position",
    "eval_all_viewpoint_positions",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "primary_eval_hit",
    "trajectory_success",
    "success_proposal_uid",
    "success_source_role",
    "m32_trajectory_success",
    "m33_source_gap_label",
    "detector_success_delta",
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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def valid_vec3(vec: object) -> bool:
    return isinstance(vec, list) and len(vec) == 3 and all(finite_float(value) is not None for value in vec)


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


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


def normalize_candidate(row: dict[str, Any]) -> dict[str, Any]:
    policy_plan_uid = str(row.get("overlay_policy_plan_uid"))
    candidate_visit_uid = str(row.get("overlay_candidate_uid"))
    stop = row.get("execution_stop_position_m") or row.get("candidate_stop_position_m") or row.get("snapped_position_m")
    path_ready = bool(row.get("path_ready")) and valid_vec3(stop) and row.get("policy_input_allowed", True) is not False
    return {
        "version": VERSION,
        "source_version": row.get("version"),
        "selected_route": row.get("selected_route"),
        "benchmark_row_uid": row.get("benchmark_row_uid"),
        "m34_source_policy_plan_uid": row.get("m34_source_policy_plan_uid"),
        "policy_plan_uid": policy_plan_uid,
        "candidate_visit_uid": candidate_visit_uid,
        "overlay_policy_plan_uid": policy_plan_uid,
        "overlay_candidate_uid": candidate_visit_uid,
        "policy_id": row.get("policy_id"),
        "policy_role": row.get("policy_role"),
        "adapter_episode_id": row.get("adapter_episode_id"),
        "scan_id": row.get("scan_id"),
        "scene_key": row.get("scene_key"),
        "object_category": row.get("object_category"),
        "task_context_id": row.get("task_context_id"),
        "visit_rank": row.get("visit_rank"),
        "proposal_uid": row.get("proposal_uid"),
        "raw_candidate_uid": row.get("raw_candidate_uid"),
        "frame_id": row.get("frame_id"),
        "label_canonical": row.get("label_canonical"),
        "candidate_source_role": row.get("candidate_source_role"),
        "source_role": row.get("candidate_source_role"),
        "dynamic_stale_overlay_role": row.get("dynamic_stale_overlay_role"),
        "candidate_order_component": row.get("candidate_order_component"),
        "candidate_position_m": row.get("candidate_position_m"),
        "candidate_stop_position_m": stop,
        "execution_stop_position_m": stop,
        "snapped_position_m": row.get("snapped_position_m") or stop,
        "source_position_m": row.get("source_position_m"),
        "scene_docker_path": row.get("scene_docker_path"),
        "navmesh_docker_path": row.get("navmesh_docker_path"),
        "path_ready": path_ready,
        "candidate_usable_for_path_smoke": bool(row.get("candidate_usable_for_path_smoke", path_ready)),
        "policy_input_allowed": True,
        "navmesh_validation_status": row.get("navmesh_validation_status"),
        "ranking_score": finite_float(row.get("ranking_score")),
        "confidence": finite_float(row.get("confidence")),
        "source_to_candidate_path_cost_m": finite_float(row.get("source_to_candidate_path_cost_m")),
        "cumulative_known_path_cost_m": finite_float(row.get("cumulative_known_path_cost_m")),
        "diagnostic_source_gap_boundary": bool(row.get("diagnostic_source_gap_boundary")),
        "diagnostic_not_policy_input": True,
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_success_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "claim_boundary": "M36 trajectory runner input row normalized from M35; eval goals and success labels are excluded.",
    }


def build_plan_rows(m35_plans: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_plan[str(row.get("policy_plan_uid"))].append(row)

    rows: list[dict[str, Any]] = []
    for plan in sorted(m35_plans, key=lambda row: str(row.get("overlay_policy_plan_uid"))):
        policy_plan_uid = str(plan.get("overlay_policy_plan_uid"))
        plan_candidates = sorted(by_plan.get(policy_plan_uid, []), key=lambda row: int(row.get("visit_rank") or 10**9))
        source_role_counts = Counter(str(row.get("candidate_source_role")) for row in plan_candidates)
        rows.append(
            {
                "version": VERSION,
                "source_version": plan.get("version"),
                "selected_route": plan.get("selected_route"),
                "benchmark_row_uid": plan.get("benchmark_row_uid"),
                "m34_source_policy_plan_uid": plan.get("m34_source_policy_plan_uid"),
                "policy_plan_uid": policy_plan_uid,
                "overlay_policy_plan_uid": policy_plan_uid,
                "policy_id": plan.get("policy_id"),
                "policy_role": plan.get("policy_role"),
                "adapter_episode_id": plan.get("adapter_episode_id"),
                "scan_id": plan.get("scan_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "task_context_id": plan.get("task_context_id"),
                "candidate_visit_order_contract": "dynamic_stale_overlay_v0",
                "candidate_rows": len(plan_candidates),
                "path_ready_candidate_rows": sum(1 for row in plan_candidates if row.get("path_ready")),
                "source_role_counts": dict(sorted(source_role_counts.items())),
                "stale_old_memory_candidate_rows": source_role_counts.get("stale_old_memory", 0),
                "current_observation_candidate_rows": source_role_counts.get("current_observation", 0),
                "first_candidate_source_role": plan_candidates[0].get("candidate_source_role") if plan_candidates else None,
                "stale_visit_first": bool(plan.get("stale_visit_first")),
                "current_observation_first": bool(plan.get("current_observation_first")),
                "stale_before_current_rows": plan.get("stale_before_current_rows"),
                "old_location_dead_end_cost_proxy_m": finite_float(plan.get("old_location_dead_end_cost_proxy_m")),
                "stale_visit_rate_proxy": finite_float(plan.get("stale_visit_rate_proxy")),
                "reobservation_rate_proxy": finite_float(plan.get("reobservation_rate_proxy")),
                "diagnostic_source_gap_boundary": bool(plan.get("diagnostic_source_gap_boundary")),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "start_state_source": "ObjectNav episode start state from E008-M03/E008-M22 runner input",
                "execution_semantics": "start at episode start and visit execution_stop_position_m in visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after candidate budget is exhausted",
                "candidate_budget": "all materialized ranked candidates for smoke; paper tables must also report fixed-budget variants",
                "execute_in_next_runner": bool(plan_candidates) and all(valid_vec3(row.get("execution_stop_position_m")) for row in plan_candidates),
                "requires_docker": True,
                "runner_script": str(M37_RUNNER.relative_to(ROOT)),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_m35_proxy_success_for_filtering": False,
                "claim_boundary": "M36 execution plan is a trajectory contract; no trajectory metric has been computed yet.",
            }
        )
    return rows


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("policy_plan_uid", "plan identity used to group policy candidates"),
        ("policy_id", "policy label for baseline/method comparison"),
        ("adapter_episode_id", "episode identity used to join to start state and eval-only metric rows"),
        ("scene_key", "scene identity used to load Habitat scene/navmesh"),
        ("object_category", "query category for reporting and grouped metrics"),
        ("task_context_id", "structured task context for task-conditioned policy comparison"),
        ("visit_rank", "materialized visit order fixed before metric computation"),
        ("candidate_source_role", "stale old memory vs current observation source role"),
        ("dynamic_stale_overlay_role", "counterfactual overlay role used for failure analysis"),
        ("execution_stop_position_m", "candidate stop point for trajectory execution"),
        ("scene_docker_path", "Habitat scene path inside read-only Docker data mount"),
        ("navmesh_docker_path", "Habitat navmesh path inside read-only Docker data mount"),
        ("path_ready", "pre-execution reachability/accounting flag"),
        ("confidence", "detector score for detector baseline ranking already materialized"),
        ("ranking_score", "ranking score already used before M36"),
        ("source_to_candidate_path_cost_m", "non-eval path-cost input/diagnostic"),
    ]
    blocked = [
        ("eval_goal_position", "ObjectNav target position is evaluation-only"),
        ("eval_goal_object_id", "ObjectNav target object id is evaluation-only"),
        ("eval_first_viewpoint_position", "ObjectNav target viewpoint is evaluation-only"),
        ("eval_all_viewpoint_positions", "ObjectNav target viewpoints are evaluation-only"),
        ("candidate_to_eval_goal_xz_m", "distance to target leaks the answer"),
        ("candidate_to_nearest_eval_viewpoint_xz_m", "distance to target viewpoint leaks the answer"),
        ("primary_eval_hit", "success label is metric-only"),
        ("trajectory_success", "execution outcome cannot be a policy input"),
        ("m32_trajectory_success", "previous trajectory outcome is diagnostic only"),
    ]
    rows = []
    for field, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "contract_group": "allowed_policy_input",
                "allowed_for_policy": True,
                "allowed_for_metric": True,
                "reason": reason,
            }
        )
    for field, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "contract_group": "blocked_policy_input",
                "allowed_for_policy": False,
                "allowed_for_metric": True,
                "reason": reason,
            }
        )
    return rows


def build_runner_adaptation_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "adaptation_id": "generalize_policy_id",
            "m32_limitation": "M32 hard-codes one H001 fallback policy id.",
            "m37_requirement": "Read policy_id and policy_role from each plan/candidate row.",
            "status": "implemented_in_runner_scaffold",
        },
        {
            "version": VERSION,
            "adaptation_id": "generalize_input_files",
            "m32_limitation": "M32 reads M31-specific h001_fallback_candidate_visit_order_rows.jsonl.",
            "m37_requirement": "Read M36 dynamic_stale_overlay_trajectory_candidate_rows.jsonl and trajectory_execution_plan_rows.jsonl.",
            "status": "implemented_in_runner_scaffold",
        },
        {
            "version": VERSION,
            "adaptation_id": "multi_policy_aggregation",
            "m32_limitation": "M32 aggregates only one policy.",
            "m37_requirement": "Aggregate by policy, task context, and source-gap boundary over five materialized policies.",
            "status": "implemented_in_runner_scaffold",
        },
        {
            "version": VERSION,
            "adaptation_id": "dynamic_stale_metrics",
            "m32_limitation": "M32 compares to M30 proxy rows, not stale-overlay rows.",
            "m37_requirement": "Report stale-first/current-first, old-location dead-end proxy, source role of success, and H001-vs-baseline deltas.",
            "status": "implemented_in_runner_scaffold",
        },
    ]


def build_docker_command_rows() -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research3/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py "
        "--m36-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M36_dynamic_stale_overlay_trajectory_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m37_dynamic_stale_overlay_trajectory_execution_smoke",
            "working_directory": str(ROOT),
            "docker_image": HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research3/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "output_path": str(M37_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M37_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M37_dynamic_stale_overlay_trajectory_execution_smoke_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['dynamic_stale_overlay_trajectory_smoke_ready'] is True\n"
                "assert c['scan_task_policy_rows'] == 90\n"
                "print('m37 ready')\n"
                "PY"
            ),
        }
    ]


def build_leakage_audit_rows(candidate_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for payload, rows in [
        ("dynamic_stale_overlay_trajectory_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
    ]:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_success_label"):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def build_gate_rows(
    m35_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    runner_compile: dict[str, Any],
    docker_image_status: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m35_materialization_ready",
            "status": "pass" if m35_cov.get("dynamic_stale_overlay_materialized") else "fail",
            "evidence": f"M35 status={m35_cov.get('status')}.",
        },
        {
            "version": VERSION,
            "gate_id": "candidate_rows_preserved",
            "status": "pass" if len(candidate_rows) == 924 else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; expected=924.",
        },
        {
            "version": VERSION,
            "gate_id": "plan_rows_preserved",
            "status": "pass" if len(plan_rows) == 90 else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected=90.",
        },
        {
            "version": VERSION,
            "gate_id": "all_plans_runner_ready",
            "status": "pass" if all(row.get("execute_in_next_runner") for row in plan_rows) else "fail",
            "evidence": f"runner-ready plan rows={sum(1 for row in plan_rows if row.get('execute_in_next_runner'))}/{len(plan_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked field hits={sum(int(row.get('blocked_field_hit_count') or 0) for row in leakage_rows)}.",
        },
        {
            "version": VERSION,
            "gate_id": "m37_runner_py_compile",
            "status": "pass" if runner_compile.get("ok") else "fail",
            "evidence": f"returncode={runner_compile.get('returncode')}; stderr_tail={runner_compile.get('stderr_tail')!r}.",
        },
        {
            "version": VERSION,
            "gate_id": "habitat_docker_image_present",
            "status": "pass" if docker_image_status.get("ok") else "warning",
            "evidence": f"docker image inspect returncode={docker_image_status.get('returncode')}; stderr_tail={docker_image_status.get('stderr_tail')!r}.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "trajectory_contract_ready",
            "status": "supported_contract_only",
            "safe_claim": "M36 provides a leakage-safe trajectory execution contract and generalized runner scaffold for M35 rows.",
        },
        {
            "version": VERSION,
            "claim_id": "dynamic_stale_navigation_result",
            "status": "not_ready",
            "safe_claim": "No M36 output contains executed trajectories or SR/SPL results.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "status": "blocked",
            "safe_claim": "Final real navigation claim needs M37 execution, larger scale, and navigation/search baselines.",
        },
        {
            "version": VERSION,
            "claim_id": "human_intent_main_claim",
            "status": "blocked",
            "safe_claim": "Structured task context remains an ablation/condition, not a main human-intent claim.",
        },
    ]


def build_route_decision_rows(contract_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "m36_selected_next",
            "decision": "run_dynamic_stale_overlay_trajectory_smoke" if contract_ready else "repair_m36_contract",
            "selected_next_unit": NEXT_UNIT if contract_ready else "repair E008-M36 contract",
            "reason": "M36 normalized all M35 policy plans and added a generalized runner scaffold; next step is Docker trajectory execution."
            if contract_ready
            else "M36 contract gates did not pass.",
            "launch_long_job_now": False,
        }
    ]


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col)) for col in columns) + " |")
    return "\n".join(lines)


def build_report(
    coverage: dict[str, Any],
    gate_rows: list[dict[str, Any]],
    adaptation_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> str:
    policy_rows = []
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    for policy_id, rows in sorted(by_policy.items()):
        policy_rows.append(
            {
                "policy_id": policy_id,
                "plans": len(rows),
                "candidates": sum(int(row.get("candidate_rows") or 0) for row in rows),
                "stale_first": sum(1 for row in rows if row.get("stale_visit_first")),
                "current_first": sum(1 for row in rows if row.get("current_observation_first")),
            }
        )
    return "\n".join(
        [
            "# E008-M36 Dynamic-Stale Overlay Trajectory Contract",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- M35 status: `{coverage['m35_status']}`.",
            f"- Candidate rows: {coverage['trajectory_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Runner script: `{coverage['runner_script']}`.",
            f"- Runner py_compile pass: {coverage['runner_py_compile_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Rows",
            "",
            markdown_table(policy_rows, ["policy_id", "plans", "candidates", "stale_first", "current_first"]),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "status", "evidence"]),
            "",
            "## Runner Adaptation",
            "",
            markdown_table(adaptation_rows, ["adaptation_id", "status", "m37_requirement"]),
            "",
            "## Claim Boundary",
            "",
            "- M36 is a contract and runner-adaptation unit only.",
            "- M36 does not execute `Habitat` trajectories and does not produce `SR` / `SPL`.",
            "- Dynamic-stale navigation claims require M37 trajectory execution and interpretation.",
            "",
        ]
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m35_cov = read_json(M35_DIR / "coverage.json")
    m35_candidates = read_jsonl(M35_DIR / "dynamic_stale_overlay_policy_candidate_rows.jsonl")
    m35_plans = read_jsonl(M35_DIR / "dynamic_stale_overlay_policy_execution_plan_rows.jsonl")

    if not m35_cov or not m35_candidates or not m35_plans:
        raise SystemExit("missing E008-M35 inputs")

    candidate_rows = [normalize_candidate(row) for row in m35_candidates]
    plan_rows = build_plan_rows(m35_plans, candidate_rows)
    input_contract_rows = build_input_contract_rows()
    adaptation_rows = build_runner_adaptation_rows()
    docker_command_rows = build_docker_command_rows()
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows)
    runner_compile = command_status(["python", "-m", "py_compile", str(M37_RUNNER)], timeout_s=30)
    docker_image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE], timeout_s=20)
    gate_rows = build_gate_rows(m35_cov, candidate_rows, plan_rows, leakage_rows, runner_compile, docker_image_status)
    contract_ready = (
        m35_cov.get("dynamic_stale_overlay_materialized") is True
        and len(candidate_rows) == 924
        and len(plan_rows) == 90
        and all(row.get("execute_in_next_runner") for row in plan_rows)
        and all(row.get("leakage_pass") for row in leakage_rows)
        and bool(runner_compile.get("ok"))
    )
    claim_rows = build_claim_boundary_rows()
    route_rows = build_route_decision_rows(contract_ready)

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m36_dynamic_stale_overlay_trajectory_contract_ready_runner_next"
        if contract_ready
        else "e008_m36_dynamic_stale_overlay_trajectory_contract_blocked",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m35_status": m35_cov.get("status"),
        "m35_candidate_rows": m35_cov.get("policy_candidate_rows"),
        "m35_plan_rows": m35_cov.get("policy_execution_plan_rows"),
        "trajectory_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "execute_in_next_runner_rows": sum(1 for row in plan_rows if row.get("execute_in_next_runner")),
        "policy_ids": sorted({str(row.get("policy_id")) for row in plan_rows}),
        "policy_count": len({str(row.get("policy_id")) for row in plan_rows}),
        "intervention_rows": len({str(row.get("benchmark_row_uid")) for row in plan_rows}),
        "source_gap_plan_rows": sum(1 for row in plan_rows if row.get("diagnostic_source_gap_boundary")),
        "leakage_audit_pass": all(row.get("leakage_pass") for row in leakage_rows),
        "blocked_field_hit_count": sum(int(row.get("blocked_field_hit_count") or 0) for row in leakage_rows),
        "blocked_flag_hit_count": sum(int(row.get("blocked_flag_hit_count") or 0) for row in leakage_rows),
        "runner_script": str(M37_RUNNER.relative_to(ROOT)),
        "runner_exists": M37_RUNNER.exists(),
        "runner_py_compile_pass": bool(runner_compile.get("ok")),
        "habitat_docker_image_inspect_ok": bool(docker_image_status.get("ok")),
        "trajectory_execution_contract_ready": contract_ready,
        "runner_adaptation_ready": contract_ready,
        "trajectory_execution_result_ready": False,
        "dynamic_stale_navigation_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for out_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(out_dir / "coverage.json", coverage)
        write_jsonl(out_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(out_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(out_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(out_dir / "runner_adaptation_rows.jsonl", adaptation_rows)
        write_jsonl(out_dir / "docker_command_rows.jsonl", docker_command_rows)
        write_jsonl(out_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(out_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(out_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(out_dir / "route_decision_rows.jsonl", route_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, gate_rows, adaptation_rows, plan_rows),
        encoding="utf-8",
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
