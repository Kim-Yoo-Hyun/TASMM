#!/usr/bin/env python3
"""Fix the E008-M31 H001 fallback trajectory contract and source-gap boundary."""

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
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0"
VERSION = "e008_m31_h001_fallback_trajectory_contract_source_gap_boundary_v0"

M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M21_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M21_expanded_detector_policy_trajectory_execution_contract_v0"
M22_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M30_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M30_h001_current_observation_fallback_replay_smoke_v0"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
M32_RUNNER = EXP_ROOT / "tools" / "run_m32_h001_fallback_trajectory_execution_smoke.py"
M32_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"
M32_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M32_h001_fallback_trajectory_execution_smoke_v0"

POLICY_ID = "h001_current_observation_backstop_top5_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"

BLOCKED_POLICY_FIELDS = {
    "eval_goal_object_id": "ObjectNav target object id is evaluation-only.",
    "eval_goal_position": "ObjectNav target position is evaluation-only.",
    "eval_all_viewpoint_count_loaded": "ObjectNav target viewpoints are evaluation-only.",
    "eval_viewpoint_count": "ObjectNav target viewpoint count is evaluation-only.",
    "candidate_to_eval_first_viewpoint_3d_m": "Distance to eval viewpoint leaks the answer.",
    "candidate_to_eval_first_viewpoint_xz_m": "Distance to eval viewpoint leaks the answer.",
    "candidate_to_eval_goal_3d_m": "Distance to eval goal leaks the answer.",
    "candidate_to_eval_goal_xz_m": "Distance to eval goal leaks the answer.",
    "candidate_to_nearest_eval_viewpoint_3d_m": "Distance to eval viewpoint leaks the answer.",
    "candidate_to_nearest_eval_viewpoint_xz_m": "Distance to eval viewpoint leaks the answer.",
    "episode_eval_geodesic_distance_m": "Oracle distance is metric-only.",
    "oracle_goal_snapped_path_m": "Oracle goal path is metric-only.",
    "oracle_viewpoint_path_m": "Oracle viewpoint path is metric-only.",
    "primary_eval_hit": "Success label is metric-only.",
    "primary_eval_metric": "Evaluation metric name is not needed by the policy.",
    "hit_any_viewpoint_xz_0p5": "Success label is metric-only.",
    "hit_any_viewpoint_xz_1p0": "Success label is metric-only.",
    "hit_any_viewpoint_xz_1p5": "Success label is metric-only.",
    "hit_first_viewpoint_xz_1p0": "Success label is metric-only.",
    "hit_goal_xz_1p0": "Success label is metric-only.",
    "hit_goal_xz_1p5": "Success label is metric-only.",
    "hit_goal_xz_2p0": "Success label is metric-only.",
    "m28_failure_type": "Failure diagnosis is post-hoc.",
    "transition_type": "Repair transition label is post-hoc.",
}


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


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def hm3d_scene_docker_path(scene_key: str) -> str:
    scene_hash = scene_key.split("-", 1)[1] if "-" in scene_key else scene_key
    return f"/data/versioned_data/hm3d-0.2/hm3d/minival/{scene_key}/{scene_hash}.basis.glb"


def hm3d_navmesh_docker_path(scene_key: str) -> str:
    scene_hash = scene_key.split("-", 1)[1] if "-" in scene_key else scene_key
    return f"/data/versioned_data/hm3d-0.2/hm3d/minival/{scene_key}/{scene_hash}.basis.navmesh"


def metric_scan_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_policy"]


def metric_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") in {"aggregate_policy", "aggregate_policy_task_context"}]


def build_navmesh_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("proposal_uid")): row for row in rows if row.get("proposal_uid")}


def sanitize_candidate_row(row: dict[str, Any], navmesh_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    proposal_uid = str(row.get("proposal_uid"))
    nav = navmesh_index.get(proposal_uid, {})
    scene_key = str(row.get("scene_key"))
    stop_position = row.get("candidate_stop_position_m") or nav.get("snapped_position_m")
    source_position = row.get("candidate_source_position_m") or nav.get("source_position")
    path_ready = bool(row.get("path_ready")) and row.get("policy_input_allowed", True) is not False
    return {
        "version": VERSION,
        "policy_id": POLICY_ID,
        "policy_family": "h001_repair_memory_trust_backstop",
        "policy_plan_uid": row.get("policy_plan_uid"),
        "candidate_visit_uid": row.get("candidate_visit_uid"),
        "adapter_episode_id": row.get("adapter_episode_id"),
        "scan_id": row.get("scan_id"),
        "scene_key": scene_key,
        "object_category": row.get("object_category"),
        "task_context_id": row.get("task_context_id"),
        "visit_rank": row.get("visit_rank"),
        "proposal_uid": proposal_uid,
        "raw_candidate_uid": row.get("raw_candidate_uid"),
        "frame_id": row.get("frame_id"),
        "label_canonical": row.get("label_canonical"),
        "candidate_order_component": row.get("candidate_order_component"),
        "candidate_visit_order_contract": "h001_preserve_then_current_observation_backstop_top5",
        "source_role": row.get("source_role"),
        "repair_replay_segment": row.get("repair_replay_segment"),
        "base_policy_id": row.get("base_policy_id"),
        "source_policy_id": row.get("source_policy_id"),
        "original_policy_id": row.get("original_policy_id"),
        "original_visit_rank": row.get("original_visit_rank"),
        "candidate_position_m": row.get("candidate_position_m"),
        "candidate_source_position_m": source_position,
        "candidate_stop_position_m": stop_position,
        "execution_stop_position_m": stop_position,
        "source_to_candidate_path_cost_m": finite_float(row.get("source_to_candidate_path_cost_m")),
        "cumulative_known_path_cost_m": finite_float(row.get("cumulative_known_path_cost_m")),
        "ranking_cost_m": finite_float(row.get("source_to_candidate_path_cost_m")),
        "path_ready": path_ready,
        "policy_input_allowed": True,
        "scene_docker_path": nav.get("scene_docker_path") or hm3d_scene_docker_path(scene_key),
        "navmesh_docker_path": nav.get("navmesh_docker_path") or hm3d_navmesh_docker_path(scene_key),
        "navmesh_validation_status": nav.get("navmesh_validation_status") or ("candidate_path_ready" if path_ready else "unknown"),
        "candidate_usable_for_path_smoke": bool(nav.get("candidate_usable_for_path_smoke", path_ready)),
        "snapped_position_m": nav.get("snapped_position_m") or stop_position,
        "source_position": nav.get("source_position") or source_position,
        "source_to_snapped_geodesic_m": finite_float(nav.get("source_to_snapped_geodesic_m")),
        "source_to_snapped_path_found": bool(nav.get("source_to_snapped_path_found", path_ready)),
        "confidence": finite_float(nav.get("confidence")),
        "selection_score": finite_float(nav.get("selection_score")),
        "policy_input_uses_eval_goal_or_viewpoint": False,
        "policy_input_uses_failure_label": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "claim_boundary": "M31 policy input row; ObjectNav eval goal/viewpoint and M30 hit labels are excluded.",
    }


def build_execution_plan_rows(
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_plan[str(row.get("policy_plan_uid"))].append(row)
    out = []
    for plan in sorted(plan_rows, key=lambda row: (str(row.get("scan_id")), str(row.get("task_context_id")))):
        policy_plan_uid = str(plan.get("policy_plan_uid"))
        candidates = sorted(by_plan.get(policy_plan_uid, []), key=lambda row: int(row.get("visit_rank") or 10**9))
        out.append(
            {
                "version": VERSION,
                "policy_id": POLICY_ID,
                "policy_plan_uid": policy_plan_uid,
                "adapter_episode_id": plan.get("adapter_episode_id"),
                "scan_id": plan.get("scan_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "task_context_id": plan.get("task_context_id"),
                "candidate_visit_order_contract": "h001_preserve_then_current_observation_backstop_top5",
                "candidate_rows": len(candidates),
                "path_ready_candidate_rows": sum(1 for row in candidates if row.get("path_ready")),
                "source_role_counts": dict(sorted(Counter(str(row.get("source_role")) for row in candidates).items())),
                "execution_candidate_file": "h001_fallback_candidate_visit_order_rows.jsonl",
                "start_state_source": "ObjectNav episode start state from E008-M03/E008-M22 runner input",
                "execution_semantics": "start at episode start and visit execution_stop_position_m in visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after candidate budget is exhausted",
                "candidate_budget": "all ranked H001 fallback candidates for smoke; paper tables must also report fixed-budget variants",
                "uses_m30_proxy_success_for_filtering": False,
                "execute_in_next_runner": True,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_failure_label": False,
                "claim_boundary": "Execution plan includes all 18 episode-task rows; source-gap labels are diagnostic-only.",
            }
        )
    return out


def build_source_gap_boundary_rows(transition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in transition_rows:
        if row.get("transition_type") != "remaining_all_policy_source_gap":
            continue
        out.append(
            {
                "version": VERSION,
                "boundary_id": f"m31_source_gap::{row.get('adapter_episode_id')}::{row.get('task_context_id')}",
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": row.get("task_context_id"),
                "transition_type": row.get("transition_type"),
                "m28_failure_type": row.get("m28_failure_type"),
                "detector_primary_hit": row.get("detector_primary_hit"),
                "h001_primary_hit": row.get("h001_primary_hit"),
                "repaired_primary_hit": row.get("repaired_primary_hit"),
                "repaired_candidate_rows": row.get("repaired_candidate_rows"),
                "detector_candidate_rows": row.get("detector_candidate_rows"),
                "h001_candidate_rows": row.get("h001_candidate_rows"),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "diagnostic_uses_eval_goal_or_viewpoint": True,
                "policy_execution_should_include_row": True,
                "reason": "All compared policy sources miss the eval target region under M30 GoalEvalProxy; this is source coverage boundary, not a policy-input filter.",
            }
        )
    return out


def build_blocked_input_rows(
    raw_candidate_rows: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    sanitized_candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_keys = Counter()
    for row in raw_candidate_rows + transition_rows:
        raw_keys.update(row.keys())
    sanitized_keys = set()
    for row in sanitized_candidate_rows + plan_rows:
        sanitized_keys.update(row.keys())
    rows = []
    for field, reason in sorted(BLOCKED_POLICY_FIELDS.items()):
        rows.append(
            {
                "version": VERSION,
                "field": field,
                "observed_in_m30_raw_rows": int(raw_keys.get(field, 0)),
                "observed_in_m31_policy_input_rows": field in sanitized_keys,
                "allowed_for_policy": False,
                "allowed_for_metric_or_diagnostic": True,
                "leakage_audit_pass": field not in sanitized_keys,
                "reason": reason,
            }
        )
    return rows


def build_metric_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "metric": "SR",
            "row_scope": "policy_aggregate",
            "definition": "mean over episode-task rows after Habitat executes H001 fallback stops",
            "required_next_output": "E008-M32 trajectory_policy_metric_rows.jsonl",
            "claim_status": "blocked_until_E008-M32_execution",
        },
        {
            "version": VERSION,
            "metric": "SPL",
            "row_scope": "policy_aggregate",
            "definition": "success * oracle shortest path / max(executed path length, oracle shortest path)",
            "required_next_output": "E008-M32 trajectory_policy_metric_rows.jsonl plus E008-M04 oracle path rows",
            "claim_status": "blocked_until_E008-M32_execution",
        },
        {
            "version": VERSION,
            "metric": "PathLengthM",
            "row_scope": "scan_task_policy",
            "definition": "sum of executed geodesic segments before success or budget exhaustion",
            "required_next_output": "E008-M32 trajectory_attempt_rows.jsonl",
            "claim_status": "runner_metric",
        },
        {
            "version": VERSION,
            "metric": "CandidateVisits",
            "row_scope": "scan_task_policy",
            "definition": "number of fallback candidate stops attempted before success or budget exhaustion",
            "required_next_output": "E008-M32 trajectory_attempt_rows.jsonl",
            "claim_status": "runner_metric",
        },
        {
            "version": VERSION,
            "metric": "GoalEvalProxySR",
            "row_scope": "policy_aggregate",
            "definition": "M30 leakage-safe goal-evaluation proxy retained only as pre-execution diagnostic",
            "required_next_output": "E008-M30 fallback_replay_policy_goal_metric_rows.jsonl",
            "claim_status": "proxy_not_final_navigation_metric",
        },
        {
            "version": VERSION,
            "metric": "SourceGapBoundaryRate",
            "row_scope": "posthoc_diagnostic",
            "definition": "fraction of episode-task rows where detector/base/repaired sources all miss target region",
            "required_next_output": "source_gap_boundary_rows.jsonl",
            "claim_status": "failure_boundary_not_policy_metric",
        },
    ]


def build_baseline_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "baseline_id": "detector_confidence_reachable_subset_v0",
            "current_source": "E008-M22 Docker trajectory smoke",
            "required_for_paper_table": True,
            "status": "trajectory_smoke_available",
            "comparison_role": "naive current-observation detector ranking baseline",
        },
        {
            "version": VERSION,
            "baseline_id": "h001_real_task_context_memory_trust_v0",
            "current_source": "E008-M27 goal-evaluation proxy only",
            "required_for_paper_table": True,
            "status": "trajectory_execution_missing",
            "comparison_role": "base H001 without current-observation backstop",
        },
        {
            "version": VERSION,
            "baseline_id": "h001_current_observation_backstop_top5_v0",
            "current_source": "E008-M30 goal-evaluation proxy; E008-M31 execution contract",
            "required_for_paper_table": True,
            "status": "trajectory_runner_next",
            "comparison_role": "H001 fallback policy under test",
        },
        {
            "version": VERSION,
            "baseline_id": "task_agnostic_memory_trust_v0",
            "current_source": "E008-M27 goal-evaluation proxy only",
            "required_for_paper_table": True,
            "status": "trajectory_execution_missing",
            "comparison_role": "ablation of structured task context",
        },
    ]


def build_docker_preflight_rows(m21_coverage: dict[str, Any], m22_coverage: dict[str, Any]) -> list[dict[str, Any]]:
    docker_info = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE, "--format", "{{.Id}} {{.Size}}"])
    return [
        {
            "version": VERSION,
            "check": "m21_docker_preflight_ready",
            "status": "pass" if m21_coverage.get("docker_preflight_ready") else "fail",
            "evidence": f"M21 status={m21_coverage.get('status')}",
            "required_before": "E008-M32 runner execution",
        },
        {
            "version": VERSION,
            "check": "m22_detector_trajectory_smoke_ready",
            "status": "pass" if m22_coverage.get("real_navigation_sr_spl_smoke_ready") else "fail",
            "evidence": f"M22 status={m22_coverage.get('status')}; rows={m22_coverage.get('trajectory_execution_rows')}",
            "required_before": "H001 runner adaptation",
        },
        {
            "version": VERSION,
            "check": "docker_cli_current_access",
            "status": "pass" if docker_info["ok"] else "warning",
            "evidence": docker_info["stdout_tail"].strip() or docker_info["stderr_tail"].strip(),
            "required_before": "E008-M32 runner execution",
        },
        {
            "version": VERSION,
            "check": "habitat_image_current_access",
            "status": "pass" if image_status["ok"] else "warning",
            "evidence": image_status["stdout_tail"].strip() or image_status["stderr_tail"].strip(),
            "required_before": "E008-M32 runner execution",
        },
        {
            "version": VERSION,
            "check": "research3_data_root_readable",
            "status": "pass" if RESEARCH3_DATA_ROOT.exists() and RESEARCH3_DATA_ROOT.is_dir() else "fail",
            "evidence": str(RESEARCH3_DATA_ROOT),
            "required_before": "E008-M32 runner execution",
        },
        {
            "version": VERSION,
            "check": "m32_runner_script",
            "status": "warning" if not M32_RUNNER.exists() else "pass",
            "evidence": str(M32_RUNNER),
            "required_before": "E008-M32 runner execution",
        },
    ]


def build_docker_command_rows() -> list[dict[str, Any]]:
    runner_cmd = (
        "docker run --rm --gpus all "
        f"-v {RESEARCH3_DATA_ROOT}:/data:ro "
        f"-v {ROOT}:/work "
        "-w /work "
        f"{HABITAT_IMAGE} "
        "bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m32_h001_fallback_trajectory_execution_smoke.py "
        "--m31-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M31_h001_fallback_trajectory_contract_source_gap_boundary_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M32_h001_fallback_trajectory_execution_smoke_v0\""
    )
    verify_cmd = (
        "python - <<'PY'\n"
        "import json\n"
        "from pathlib import Path\n"
        "p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M32_h001_fallback_trajectory_execution_smoke_v0/coverage.json')\n"
        "data = json.loads(p.read_text())\n"
        "assert data['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False\n"
        "assert data['h001_fallback_trajectory_smoke_ready'] is True\n"
        "print(data['status'])\n"
        "PY"
    )
    return [
        {
            "version": VERSION,
            "command_id": "m32_h001_fallback_trajectory_execution_runner_template",
            "working_directory": str(ROOT),
            "command": runner_cmd,
            "output_path": str(M32_ARTIFACT_DIR),
            "derived_output_path": str(M32_DATA_OUT_DIR),
            "expected_files": [
                "coverage.json",
                "trajectory_attempt_rows.jsonl",
                "trajectory_policy_metric_rows.jsonl",
                "trajectory_failure_rows.jsonl",
                "leakage_audit_rows.jsonl",
            ],
            "verification_command": verify_cmd,
            "status": "runner_missing_next" if not M32_RUNNER.exists() else "ready_to_run",
            "long_job_policy": "launch in Docker; use tmux if execution is expanded beyond smoke scale",
        }
    ]


def build_readiness_gate_rows(
    coverage: dict[str, Any],
    docker_preflight_rows: list[dict[str, Any]],
    blocked_input_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate": "m30_replay_ready",
            "status": "pass" if coverage["m30_replay_ready"] else "fail",
            "evidence": coverage["m30_status"],
            "next_action_if_fail": "repair E008-M30 replay artifact",
        },
        {
            "version": VERSION,
            "gate": "execute_all_rows_without_proxy_success_filter",
            "status": "pass" if coverage["execute_all_episode_task_rows_next"] and not coverage["filtering_to_proxy_success_for_execution_allowed"] else "fail",
            "evidence": f"plan_rows={coverage['trajectory_execution_plan_rows']}",
            "next_action_if_fail": "remove success-conditioned filtering from M31 plan",
        },
        {
            "version": VERSION,
            "gate": "policy_input_leakage",
            "status": "pass" if coverage["policy_input_leakage_pass"] else "fail",
            "evidence": f"blocked_field_hits={coverage['sanitized_policy_eval_field_hits']}",
            "next_action_if_fail": "strip eval/hit/failure fields from policy input rows",
        },
        {
            "version": VERSION,
            "gate": "source_gap_boundary_recorded",
            "status": "warning" if coverage["source_gap_boundary_rows"] else "fail",
            "evidence": f"source_gap_rows={coverage['source_gap_boundary_rows']}",
            "next_action_if_fail": "add post-hoc source-gap boundary rows before trajectory runner",
        },
        {
            "version": VERSION,
            "gate": "docker_preflight_no_fail",
            "status": "pass" if not any(row["status"] == "fail" for row in docker_preflight_rows) else "fail",
            "evidence": json.dumps(dict(sorted(Counter(row["status"] for row in docker_preflight_rows).items()))),
            "next_action_if_fail": "repair Docker/data preflight before M32",
        },
        {
            "version": VERSION,
            "gate": "m32_runner_implemented",
            "status": "warning" if not M32_RUNNER.exists() else "pass",
            "evidence": str(M32_RUNNER),
            "next_action_if_fail": "implement E008-M32 runner scaffold",
        },
        {
            "version": VERSION,
            "gate": "final_real_navigation_claim",
            "status": "fail",
            "evidence": "M31 is a contract/boundary artifact, not executed H001 trajectory evidence.",
            "next_action_if_fail": "run E008-M32 and then scale/baseline before final claim",
        },
    ]


def build_route_decision_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "prepare_m32_h001_fallback_trajectory_runner",
            "reason": "M31 converts the M30 fallback replay into leakage-safe execution inputs and records source-gap boundary rows without filtering by proxy success.",
            "selected_next_unit": coverage["selected_next_unit"],
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "human_intent_main_claim_ready": False,
        }
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_h001_fallback_trajectory_input_contract",
            "supported": True,
            "claim_boundary": "M31 supports that H001 fallback rows can be passed to a Habitat trajectory runner without eval-goal or failure-label policy inputs.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_source_gap_boundary_recorded",
            "supported": True,
            "claim_boundary": "M31 records the 9 all-policy source-gap rows as post-hoc diagnostics, not as execution filters.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M31 does not execute the H001 fallback policy in Habitat; final real navigation SR/SPL remains blocked.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M31 still uses the current 6-episode smoke bridge and does not scale real RGB-D/open-vocabulary robustness.",
        },
    ]


def format_value(value: object) -> str:
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
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join([header, sep] + body)


def build_report(
    coverage: dict[str, Any],
    baseline_contract_rows: list[dict[str, Any]],
    readiness_gate_rows: list[dict[str, Any]],
    source_gap_boundary_rows: list[dict[str, Any]],
) -> str:
    baseline_table = markdown_table(baseline_contract_rows, ["baseline_id", "status", "comparison_role"])
    gate_table = markdown_table(readiness_gate_rows, ["gate", "status", "evidence", "next_action_if_fail"])
    source_gap_table = markdown_table(source_gap_boundary_rows, ["adapter_episode_id", "task_context_id", "object_category", "transition_type", "m28_failure_type"])
    return f"""# E008-M31 H001 Fallback Trajectory Contract and Source-Gap Boundary

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M30 status: `{coverage['m30_status']}`.
- H001 fallback execution plan rows: {coverage['trajectory_execution_plan_rows']}.
- Sanitized candidate visit rows: {coverage['h001_fallback_candidate_visit_order_rows']}.
- Source-gap boundary rows: {coverage['source_gap_boundary_rows']}.
- Policy input leakage pass: {coverage['policy_input_leakage_pass']}.
- Execute all episode-task rows next: {coverage['execute_all_episode_task_rows_next']}.
- Filtering to proxy-success rows allowed: {coverage['filtering_to_proxy_success_for_execution_allowed']}.
- Real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.

## Execution Contract

- Use `h001_fallback_candidate_visit_order_rows.jsonl` as the M32 policy-input candidate order.
- Start from the `ObjectNav` episode start state, then visit `execution_stop_position_m` in `visit_rank` order.
- Evaluate `ObjectNav` goal/viewpoint success only after each stop.
- Do not filter to the 9 M30 proxy-success rows; execute all 18 episode-task rows to avoid evaluation leakage.
- Treat `source_to_candidate_path_cost_m` as ranking evidence only. M32 must recompute executed segment paths in `Habitat`.

## Baseline Contract

{baseline_table}

## Source-Gap Boundary

{source_gap_table}

## Readiness Gates

{gate_table}

## Claim Boundary

- M31 supports a leakage-safe H001 fallback trajectory-input contract.
- M31 supports a post-hoc source-gap boundary for the 9 all-policy miss rows.
- M31 does not support final real navigation `SR` / `SPL`.
- M31 does not support final real RGB-D/open-vocabulary robustness.

## Agent Inference

The next defensible unit is E008-M32: adapt the M22 Docker trajectory runner to consume the M31 H001 fallback visit-order rows, execute all 18 episode-task rows, and report `SR`, `SPL`, `PathLengthM`, `CandidateVisits`, and failure rows without using eval goals or M30 failure labels as policy input.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m17_candidate_rows = read_jsonl(M17_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")
    m21_coverage = read_json(M21_ARTIFACT_DIR / "coverage.json")
    m22_coverage = read_json(M22_ARTIFACT_DIR / "coverage.json")
    m30_coverage = read_json(M30_ARTIFACT_DIR / "coverage.json")
    m30_plan_rows = read_jsonl(M30_ARTIFACT_DIR / "fallback_replay_plan_rows.jsonl")
    m30_candidate_rows = read_jsonl(M30_ARTIFACT_DIR / "fallback_replay_candidate_goal_eval_rows.jsonl")
    m30_metric_rows = read_jsonl(M30_ARTIFACT_DIR / "fallback_replay_policy_goal_metric_rows.jsonl")
    m30_transition_rows = read_jsonl(M30_ARTIFACT_DIR / "failure_transition_rows.jsonl")

    if not m30_coverage:
        raise SystemExit("missing E008-M30 coverage.json")
    if not m30_plan_rows or not m30_candidate_rows or not m30_metric_rows or not m30_transition_rows:
        raise SystemExit("missing one or more E008-M30 input artifacts")

    navmesh_index = build_navmesh_index(m17_candidate_rows)
    sanitized_candidate_rows = [sanitize_candidate_row(row, navmesh_index) for row in m30_candidate_rows]
    execution_plan_rows = build_execution_plan_rows(m30_plan_rows, sanitized_candidate_rows)
    source_gap_boundary_rows = build_source_gap_boundary_rows(m30_transition_rows)
    blocked_input_rows = build_blocked_input_rows(m30_candidate_rows, m30_transition_rows, sanitized_candidate_rows, execution_plan_rows)
    metric_contract_rows = build_metric_contract_rows()
    baseline_contract_rows = build_baseline_contract_rows()
    docker_preflight_rows = build_docker_preflight_rows(m21_coverage, m22_coverage)
    docker_command_rows = build_docker_command_rows()
    claim_boundary_rows = build_claim_boundary_rows()

    scan_metric_rows = metric_scan_rows(m30_metric_rows)
    aggregate_rows = metric_aggregate_rows(m30_metric_rows)
    transition_counts = dict(sorted(Counter(str(row.get("transition_type")) for row in m30_transition_rows).items()))
    source_role_counts = dict(sorted(Counter(str(row.get("source_role")) for row in sanitized_candidate_rows).items()))
    sanitized_policy_eval_field_hits = sum(1 for row in blocked_input_rows if row["observed_in_m31_policy_input_rows"])
    policy_input_leakage_pass = sanitized_policy_eval_field_hits == 0 and not any(
        row.get("policy_input_uses_eval_goal_or_viewpoint") or row.get("policy_input_uses_failure_label")
        for row in sanitized_candidate_rows + execution_plan_rows
    )
    proxy_success_plan_rows = sum(1 for row in scan_metric_rows if row.get("primary_hit"))
    proxy_failure_plan_rows = len(scan_metric_rows) - proxy_success_plan_rows
    execute_all_rows_next = len(execution_plan_rows) == len(m30_plan_rows) == len(scan_metric_rows)
    contract_ready = (
        bool(sanitized_candidate_rows)
        and len(execution_plan_rows) == 18
        and policy_input_leakage_pass
        and execute_all_rows_next
        and not any(row["status"] == "fail" for row in docker_preflight_rows)
    )
    selected_next = (
        "E008-M32 H001 fallback trajectory-execution runner scaffold"
        if contract_ready
        else "repair E008-M31 H001 fallback trajectory contract"
    )

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "e008_m31_h001_fallback_trajectory_contract_source_gap_boundary_ready_runner_next"
        if contract_ready
        else "e008_m31_h001_fallback_trajectory_contract_source_gap_boundary_blocked",
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m30_status": m30_coverage.get("status"),
        "m30_replay_ready": m30_coverage.get("status")
        == "e008_m30_h001_current_observation_fallback_replay_smoke_ready_trajectory_contract_next",
        "m21_docker_preflight_ready": bool(m21_coverage.get("docker_preflight_ready")),
        "m22_detector_trajectory_smoke_ready": bool(m22_coverage.get("real_navigation_sr_spl_smoke_ready")),
        "episode_count": len({row.get("adapter_episode_id") for row in execution_plan_rows}),
        "task_context_count": len({row.get("task_context_id") for row in execution_plan_rows}),
        "trajectory_execution_plan_rows": len(execution_plan_rows),
        "h001_fallback_candidate_visit_order_rows": len(sanitized_candidate_rows),
        "source_gap_boundary_rows": len(source_gap_boundary_rows),
        "remaining_all_policy_source_gap_rows": transition_counts.get("remaining_all_policy_source_gap", 0),
        "proxy_success_plan_rows": proxy_success_plan_rows,
        "proxy_failure_plan_rows": proxy_failure_plan_rows,
        "repaired_primary_success_rows": int(m30_coverage.get("repaired_primary_success_rows") or proxy_success_plan_rows),
        "detector_primary_success_rows": int(m30_coverage.get("detector_primary_success_rows") or 0),
        "base_h001_primary_success_rows": int(m30_coverage.get("base_h001_primary_success_rows") or 0),
        "repaired_primary_proxy_sr": safe_ratio(proxy_success_plan_rows, len(scan_metric_rows)),
        "repaired_primary_spl_proxy_mean": mean([finite_float(row.get("primary_spl_proxy")) for row in scan_metric_rows]),
        "m30_aggregate_metric_rows": len(aggregate_rows),
        "source_role_counts": source_role_counts,
        "transition_type_counts": transition_counts,
        "blocked_input_rows": len(blocked_input_rows),
        "sanitized_policy_eval_field_hits": sanitized_policy_eval_field_hits,
        "policy_input_leakage_pass": policy_input_leakage_pass,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "execute_all_episode_task_rows_next": execute_all_rows_next,
        "filtering_to_proxy_success_for_execution_allowed": False,
        "trajectory_contract_ready": contract_ready,
        "trajectory_runner_recommended_next": contract_ready,
        "m32_runner_implemented": M32_RUNNER.exists(),
        "docker_preflight_status_counts": dict(sorted(Counter(row["status"] for row in docker_preflight_rows).items())),
        "docker_image": HABITAT_IMAGE,
        "research3_data_root": str(RESEARCH3_DATA_ROOT),
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": selected_next,
    }

    readiness_gate_rows = build_readiness_gate_rows(coverage, docker_preflight_rows, blocked_input_rows)
    route_decision_rows = build_route_decision_rows(coverage)

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "h001_fallback_candidate_visit_order_rows.jsonl", sanitized_candidate_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", execution_plan_rows)
        write_jsonl(output_dir / "source_gap_boundary_rows.jsonl", source_gap_boundary_rows)
        write_jsonl(output_dir / "blocked_input_rows.jsonl", blocked_input_rows)
        write_jsonl(output_dir / "metric_contract_rows.jsonl", metric_contract_rows)
        write_jsonl(output_dir / "baseline_contract_rows.jsonl", baseline_contract_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_preflight_rows)
        write_jsonl(output_dir / "docker_command_rows.jsonl", docker_command_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", readiness_gate_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, baseline_contract_rows, readiness_gate_rows, source_gap_boundary_rows),
        encoding="utf-8",
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
