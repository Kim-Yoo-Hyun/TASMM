#!/usr/bin/env python3
"""Fix the E008-M21 detector-policy trajectory execution contract and Docker preflight."""

from __future__ import annotations

import json
import math
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M21_expanded_detector_policy_trajectory_execution_contract_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M21_expanded_detector_policy_trajectory_execution_contract_v0"
VERSION = "e008_m21_expanded_detector_policy_trajectory_execution_contract_v0"

M02_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M02_hm3d_objectnav_adapter_smoke_v0"
M03_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M04_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M04_objectnav_oracle_path_smoke_v0"
M17_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M17_expanded_detector_candidate_navmesh_validation_v0"
M18_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M18_expanded_detector_candidate_visit_order_path_smoke_v0"
M19_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
M20_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M20_expanded_detector_goal_failure_comparison_navigation_decision_v0"

RESEARCH3_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
M22_RUNNER = EXP_ROOT / "tools" / "run_m22_expanded_detector_policy_trajectory_execution_smoke.py"
M22_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"
M22_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"


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


def metric_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("policy_id")), str(row.get("scan_id"))): row
        for row in rows
        if row.get("metric_scope") == "scan_policy"
    }


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def build_execution_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join non-oracle candidates to execution state"),
        ("scene_key", "scene identity and navmesh lookup"),
        ("object_category", "query category used for detector prompt and label compatibility"),
        ("start_position", "episode start state from ObjectNav metadata"),
        ("start_rotation", "episode start orientation from ObjectNav metadata"),
        ("scene_docker_path", "Habitat scene path inside the read-only data mount"),
        ("navmesh_docker_path", "Habitat navmesh path inside the read-only data mount"),
        ("proposal_uid", "detector candidate identity"),
        ("label_canonical", "detector label after canonicalization"),
        ("confidence", "detector confidence for baseline ranking"),
        ("selection_score", "detector selection score for baseline ranking"),
        ("snapped_position_m", "candidate stop position snapped to navmesh"),
        ("source_to_snapped_geodesic_m", "source-to-candidate path cost computed by Habitat pathfinder"),
        ("navmesh_validation_status", "candidate path-ready or blocked accounting status"),
        ("visit_rank", "policy visit order from E008-M18"),
    ]
    blocked = [
        ("eval_goal_position", "ObjectNav target object center is an evaluation label"),
        ("eval_goal_object_id", "ObjectNav target object id is an evaluation label"),
        ("eval_first_viewpoint_position", "ObjectNav target viewpoint is an evaluation label"),
        ("eval_all_viewpoint_positions", "ObjectNav all viewpoints are evaluation labels"),
        ("candidate_to_eval_goal_distance", "distance-to-target leaks the answer"),
        ("candidate_to_eval_viewpoint_distance", "distance-to-viewpoint leaks the answer"),
        ("primary_hit", "success label from E008-M19 cannot be used by a policy"),
        ("best_any_viewpoint_xz_m", "evaluation-only proximity diagnostic"),
        ("goal_xz_1p0_hit", "evaluation-only success diagnostic"),
    ]
    rows = []
    for name, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "field": name,
                "contract_group": "allowed_policy_input",
                "allowed_for_policy": True,
                "allowed_for_metric": True,
                "reason": reason,
            }
        )
    for name, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "field": name,
                "contract_group": "blocked_policy_input",
                "allowed_for_policy": False,
                "allowed_for_metric": True,
                "reason": reason,
            }
        )
    return rows


def build_policy_execution_contract_rows(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    descriptions = {
        "detector_confidence_all_candidates_v0": {
            "candidate_failure_semantics": "blocked_candidates_count_as_failed_attempts",
            "purpose": "naive detector-confidence baseline including unreachable candidates",
        },
        "detector_confidence_reachable_subset_v0": {
            "candidate_failure_semantics": "skip_non_path_ready_candidates_after_accounting",
            "purpose": "reachable detector-confidence baseline",
        },
        "path_cost_ascending_reachable_subset_v0": {
            "candidate_failure_semantics": "skip_non_path_ready_candidates_after_accounting",
            "purpose": "path-cost baseline",
        },
        "confidence_path_cost_tradeoff_reachable_subset_v0": {
            "candidate_failure_semantics": "skip_non_path_ready_candidates_after_accounting",
            "purpose": "detector-confidence/path-cost tradeoff baseline",
        },
    }
    rows = []
    for row in aggregate_rows:
        policy_id = str(row.get("policy_id"))
        desc = descriptions.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "candidate_scope": row.get("candidate_scope"),
                "purpose": desc.get("purpose", "policy under contract"),
                "candidate_failure_semantics": desc.get("candidate_failure_semantics", "explicit_failure_accounting_required"),
                "execution_state": "start_at_ObjectNav_episode_start_then_visit_candidate_snapped_positions_in_policy_order",
                "termination_rule": "terminate_on_first_eval_success_or_when_candidate_budget_exhausted",
                "candidate_budget_default": "all_ranked_candidates_for_smoke; later paper table should report fixed budgets",
                "allowed_eval_use": "ObjectNav goal/viewpoints only after each stop for metric computation",
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "ranked_candidate_rows": row.get("ranked_candidate_rows"),
                "path_ready_ranked_rows": row.get("path_ready_ranked_rows"),
                "blocked_ranked_rows": row.get("blocked_ranked_rows"),
                "mean_first_path_ready_cost_m": row.get("mean_first_path_ready_cost_m"),
                "runner_required": True,
            }
        )
    return rows


def build_policy_execution_plan_rows(
    m18_policy_rows: list[dict[str, Any]],
    m19_policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m18_index = metric_index(m18_policy_rows)
    m19_index = metric_index(m19_policy_rows)
    rows = []
    for key in sorted(set(m18_index) | set(m19_index)):
        policy_id, scan_id = key
        m18 = m18_index.get(key, {})
        m19 = m19_index.get(key, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_id": scan_id,
                "adapter_episode_id": m19.get("adapter_episode_id") or m18.get("adapter_episode_id"),
                "scene_key": m19.get("scene_key") or m18.get("scene_key"),
                "object_category": m19.get("object_category") or m18.get("object_category"),
                "ranked_candidate_rows": m18.get("ranked_candidate_rows"),
                "path_ready_ranked_rows": m18.get("path_ready_ranked_rows"),
                "blocked_ranked_rows": m18.get("blocked_ranked_rows"),
                "top1_path_ready": m18.get("top1_path_ready"),
                "first_path_ready_rank": m18.get("first_path_ready_rank"),
                "first_path_ready_cost_m": m18.get("first_path_ready_cost_m"),
                "m19_primary_hit": m19.get("primary_hit"),
                "m19_primary_first_hit_rank": m19.get("primary_first_hit_rank"),
                "m19_primary_first_hit_cost_m": m19.get("primary_first_hit_cost_m"),
                "m19_primary_spl_proxy": m19.get("primary_spl_proxy"),
                "m19_goal_xz_1p0_hit": m19.get("goal_xz_1p0_hit"),
                "expected_runner_input_file": "candidate_visit_order_rows.jsonl",
                "expected_runner_output_scope": "one trajectory row per policy/scan plus per-candidate attempt rows",
                "claim_boundary": "pre_execution_proxy_row_not_sr_spl",
            }
        )
    return rows


def build_metric_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "metric": "SR",
            "row_scope": "policy_aggregate",
            "definition": "mean over episodes of success after executing policy stops",
            "required_input": "trajectory_policy_metric_rows.jsonl",
            "eval_only_fields": "ObjectNav goal/viewpoints",
            "claim_status": "blocked_until_E008-M22_or_later_execution",
        },
        {
            "version": VERSION,
            "metric": "SPL",
            "row_scope": "policy_aggregate",
            "definition": "success * oracle_shortest_path_length / max(executed_path_length, oracle_shortest_path_length)",
            "required_input": "trajectory_policy_metric_rows.jsonl plus E008-M04 oracle path rows",
            "eval_only_fields": "ObjectNav oracle viewpoint shortest path",
            "claim_status": "blocked_until_E008-M22_or_later_execution",
        },
        {
            "version": VERSION,
            "metric": "PathLengthM",
            "row_scope": "scan_policy",
            "definition": "sum of executed geodesic segments before success or budget exhaustion",
            "required_input": "trajectory_attempt_rows.jsonl",
            "eval_only_fields": "none",
            "claim_status": "runner_metric",
        },
        {
            "version": VERSION,
            "metric": "CandidateVisits",
            "row_scope": "scan_policy",
            "definition": "number of candidate stops attempted before success or budget exhaustion",
            "required_input": "trajectory_attempt_rows.jsonl",
            "eval_only_fields": "none",
            "claim_status": "runner_metric",
        },
        {
            "version": VERSION,
            "metric": "StopRank",
            "row_scope": "scan_policy",
            "definition": "first candidate rank where eval-only success is observed",
            "required_input": "trajectory_attempt_rows.jsonl",
            "eval_only_fields": "ObjectNav goal/viewpoints after stop only",
            "claim_status": "runner_metric",
        },
        {
            "version": VERSION,
            "metric": "FailureType",
            "row_scope": "attempt_or_scan_policy",
            "definition": "blocked_candidate, path_not_found, budget_exhausted, no_eval_success, simulator_error, or success",
            "required_input": "trajectory_attempt_rows.jsonl",
            "eval_only_fields": "ObjectNav eval success labels for final scan-policy outcome",
            "claim_status": "failure_analysis_metric",
        },
        {
            "version": VERSION,
            "metric": "GoalEvalProxySR",
            "row_scope": "policy_aggregate",
            "definition": "E008-M19 leakage-safe candidate-goal proxy retained only for comparison with pre-execution rows",
            "required_input": "E008-M19 policy_goal_metric_rows.jsonl",
            "eval_only_fields": "ObjectNav goal/viewpoints",
            "claim_status": "proxy_not_final_navigation_metric",
        },
    ]


def build_runner_output_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "file": "trajectory_attempt_rows.jsonl",
            "row_scope": "candidate_attempt",
            "required_keys": [
                "policy_id",
                "scan_id",
                "visit_rank",
                "proposal_uid",
                "attempt_status",
                "path_found",
                "segment_geodesic_m",
                "cumulative_path_length_m",
                "stop_position_m",
                "eval_success",
            ],
        },
        {
            "version": VERSION,
            "file": "trajectory_policy_metric_rows.jsonl",
            "row_scope": "scan_policy_and_policy_aggregate",
            "required_keys": ["policy_id", "scan_id", "SR", "SPL", "PathLengthM", "CandidateVisits", "StopRank", "FailureType"],
        },
        {
            "version": VERSION,
            "file": "trajectory_failure_rows.jsonl",
            "row_scope": "failure_case",
            "required_keys": ["policy_id", "scan_id", "failure_type", "proposal_uid", "reason"],
        },
        {
            "version": VERSION,
            "file": "leakage_audit_rows.jsonl",
            "row_scope": "field_guard",
            "required_keys": ["field", "allowed_for_policy", "observed_in_policy_input", "leakage_audit_pass"],
        },
        {
            "version": VERSION,
            "file": "coverage.json",
            "row_scope": "artifact_summary",
            "required_keys": ["status", "trajectory_execution_rows", "real_navigation_sr_spl_ready", "uses_objectnav_eval_goal_or_viewpoint_for_policy"],
        },
    ]


def build_docker_preflight_rows(
    m02_coverage: dict[str, Any],
    m04_coverage: dict[str, Any],
    m17_coverage: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    docker_info = command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    image_status = command_status(["docker", "image", "inspect", HABITAT_IMAGE, "--format", "{{.Id}} {{.Size}}"])
    data_ready = RESEARCH3_DATA_ROOT.exists() and RESEARCH3_DATA_ROOT.is_dir()
    rows = [
        {
            "version": VERSION,
            "check": "docker_cli",
            "status": "pass" if docker_info["ok"] else "fail",
            "evidence": docker_info["stdout_tail"].strip() or docker_info["stderr_tail"].strip(),
            "required_before": "E008-M22 runner execution",
        },
        {
            "version": VERSION,
            "check": "habitat_image",
            "status": "pass" if image_status["ok"] else "fail",
            "evidence": image_status["stdout_tail"].strip() or image_status["stderr_tail"].strip(),
            "required_before": "E008-M22 runner execution",
        },
        {
            "version": VERSION,
            "check": "research3_data_root_readable",
            "status": "pass" if data_ready else "fail",
            "evidence": str(RESEARCH3_DATA_ROOT),
            "required_before": "E008-M22 runner execution",
        },
        {
            "version": VERSION,
            "check": "m02_docker_scene_smoke",
            "status": "pass" if m02_coverage.get("docker_scene_smoke_success") else "fail",
            "evidence": f"returncode={m02_coverage.get('docker_returncode')}; sampled={m02_coverage.get('sampled_episode_rows')}",
            "required_before": "trajectory execution",
        },
        {
            "version": VERSION,
            "check": "m04_oracle_path_metric_smoke",
            "status": "pass" if m04_coverage.get("oracle_metric_plumbing_ready") else "fail",
            "evidence": f"viewpoint_paths={m04_coverage.get('viewpoint_paths_found')}/{m04_coverage.get('episode_rows')}",
            "required_before": "SPL metric",
        },
        {
            "version": VERSION,
            "check": "m17_candidate_navmesh_validation",
            "status": "pass" if m17_coverage.get("coordinate_frame_navmesh_validation_ready") else "fail",
            "evidence": f"path_ready={m17_coverage.get('candidate_usable_for_path_smoke_rows')}/{m17_coverage.get('candidate_rows')}",
            "required_before": "candidate trajectory execution",
        },
        {
            "version": VERSION,
            "check": "m22_runner_script",
            "status": "warning" if not M22_RUNNER.exists() else "pass",
            "evidence": str(M22_RUNNER),
            "required_before": "E008-M22 execution",
        },
    ]
    detail = {
        "docker_info": docker_info,
        "habitat_image_status": image_status,
        "research3_data_root_ready": data_ready,
        "runner_script_exists": M22_RUNNER.exists(),
    }
    return rows, detail


def build_docker_command_rows() -> list[dict[str, Any]]:
    runner_cmd = (
        "docker run --rm --gpus all "
        f"-v {RESEARCH3_DATA_ROOT}:/data:ro "
        f"-v {ROOT}:/work "
        "-w /work "
        f"{HABITAT_IMAGE} "
        "bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m22_expanded_detector_policy_trajectory_execution_smoke.py "
        "--m21-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M21_expanded_detector_policy_trajectory_execution_contract_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0\""
    )
    verify_cmd = (
        "python - <<'PY'\n"
        "import json\n"
        "from pathlib import Path\n"
        "p = Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0/coverage.json')\n"
        "data = json.loads(p.read_text())\n"
        "assert data['uses_objectnav_eval_goal_or_viewpoint_for_policy'] is False\n"
        "assert data['trajectory_execution_rows'] > 0\n"
        "print(data['status'])\n"
        "PY"
    )
    return [
        {
            "version": VERSION,
            "command_id": "m22_trajectory_execution_runner_template",
            "working_directory": str(ROOT),
            "command": runner_cmd,
            "output_path": str(M22_ARTIFACT_DIR),
            "derived_output_path": str(M22_DATA_OUT_DIR),
            "expected_files": [
                "coverage.json",
                "trajectory_attempt_rows.jsonl",
                "trajectory_policy_metric_rows.jsonl",
                "trajectory_failure_rows.jsonl",
                "leakage_audit_rows.jsonl",
            ],
            "verification_command": verify_cmd,
            "status": "template_runner_missing" if not M22_RUNNER.exists() else "ready_to_run",
            "long_job_policy": "launch in tmux only if runtime exceeds smoke scale",
        }
    ]


def gate_status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("status")) for row in rows).items()))


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(format_value(row.get(col)) for col in columns) + " |")
    return "\n".join([header, sep] + body)


def format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def build_report(
    coverage: dict[str, Any],
    policy_contract_rows: list[dict[str, Any]],
    docker_preflight_rows: list[dict[str, Any]],
    metric_schema_rows: list[dict[str, Any]],
) -> str:
    policy_table = markdown_table(
        policy_contract_rows,
        [
            "policy_id",
            "candidate_failure_semantics",
            "ranked_candidate_rows",
            "path_ready_ranked_rows",
            "blocked_ranked_rows",
            "mean_first_path_ready_cost_m",
        ],
    )
    docker_table = markdown_table(docker_preflight_rows, ["check", "status", "evidence", "required_before"])
    metric_table = markdown_table(metric_schema_rows, ["metric", "row_scope", "claim_status"])
    return f"""# E008-M21 Expanded Detector-Policy Trajectory Execution Contract

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Contract ready: {coverage['trajectory_execution_contract_ready']}.
- Docker preflight ready: {coverage['docker_preflight_ready']}.
- M22 runner implemented: {coverage['runner_implemented']}.
- Policy execution plan rows: {coverage['policy_execution_plan_rows']}.
- Real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.
- H001 navigation policy execution ready: {coverage['h001_navigation_policy_execution_ready']}.

## Policy Contract

{policy_table}

## Docker Preflight

{docker_table}

## Metric Contract

{metric_table}

## Execution Semantics

- Start each episode at the `ObjectNav` episode start state.
- Visit detector candidate `snapped_position_m` in the selected policy order.
- Evaluate `ObjectNav` goal/viewpoint success only after a stop; those fields remain blocked policy inputs.
- Stop on first eval-only success or after the candidate budget is exhausted.
- Count non-path-ready candidates explicitly as blocked attempts or skipped rows according to the policy contract.

## Claim Boundary

- E008-M21 is a contract/preflight artifact, not a simulator trajectory result.
- E008-M19 `GoalEvalProxy` success does not become real navigation `SR` / `SPL` until E008-M22 or later executes trajectories.
- H001 real navigation remains blocked until H001 stale-memory/current-observation candidate-source rows are instantiated for `HM3D ObjectNav`.

## Agent Inference

The detector-policy route is ready for an M22 runner scaffold. The strongest immediate next step is to implement a minimal trajectory runner that produces leakage-audited `SR`, `SPL`, path length, candidate-visit, and failure rows over the current 6-episode smoke set.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m02_coverage = read_json(M02_ARTIFACT_DIR / "coverage.json")
    m03_coverage = read_json(M03_ARTIFACT_DIR / "coverage.json")
    m04_coverage = read_json(M04_ARTIFACT_DIR / "coverage.json")
    m17_coverage = read_json(M17_ARTIFACT_DIR / "coverage.json")
    m18_coverage = read_json(M18_ARTIFACT_DIR / "coverage.json")
    m19_coverage = read_json(M19_ARTIFACT_DIR / "coverage.json")
    m20_coverage = read_json(M20_ARTIFACT_DIR / "coverage.json")
    m18_policy_rows = read_jsonl(M18_ARTIFACT_DIR / "policy_metric_rows.jsonl")
    m19_policy_rows = read_jsonl(M19_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")
    m18_visit_rows = read_jsonl(M18_ARTIFACT_DIR / "candidate_visit_order_rows.jsonl")
    m17_candidate_rows = read_jsonl(M17_ARTIFACT_DIR / "candidate_navmesh_rows.jsonl")

    if not m18_policy_rows:
        raise SystemExit("missing E008-M18 policy_metric_rows.jsonl")
    if not m19_policy_rows:
        raise SystemExit("missing E008-M19 policy_goal_metric_rows.jsonl")
    if not m18_visit_rows:
        raise SystemExit("missing E008-M18 candidate_visit_order_rows.jsonl")
    if not m17_candidate_rows:
        raise SystemExit("missing E008-M17 candidate_navmesh_rows.jsonl")

    input_contract_rows = build_execution_input_contract_rows()
    aggregate_rows = aggregate_metric_rows(m18_policy_rows)
    policy_contract_rows = build_policy_execution_contract_rows(aggregate_rows)
    policy_execution_plan_rows = build_policy_execution_plan_rows(m18_policy_rows, m19_policy_rows)
    metric_schema_rows = build_metric_schema_rows()
    runner_output_contract_rows = build_runner_output_contract_rows()
    docker_preflight_rows, docker_detail = build_docker_preflight_rows(m02_coverage, m04_coverage, m17_coverage)
    docker_command_rows = build_docker_command_rows()

    docker_preflight_ready = all(row["status"] == "pass" for row in docker_preflight_rows if row["check"] != "m22_runner_script")
    contract_ready = (
        bool(policy_contract_rows)
        and bool(policy_execution_plan_rows)
        and not any(row.get("allowed_for_policy") for row in input_contract_rows if row["contract_group"] == "blocked_policy_input")
        and not bool(m19_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
        and bool(m20_coverage.get("selected_next_unit") == "E008-M21 expanded detector-policy trajectory execution contract and Docker preflight")
    )
    runner_implemented = M22_RUNNER.exists()
    selected_next = (
        "E008-M22 expanded detector-policy trajectory execution runner scaffold"
        if contract_ready and docker_preflight_ready and not runner_implemented
        else "E008-M22 expanded detector-policy trajectory execution smoke"
        if contract_ready and docker_preflight_ready
        else "repair E008-M21 trajectory execution preflight"
    )
    status = (
        "e008_m21_expanded_detector_policy_trajectory_execution_contract_ready_runner_missing"
        if contract_ready and docker_preflight_ready and not runner_implemented
        else "e008_m21_expanded_detector_policy_trajectory_execution_contract_ready"
        if contract_ready and docker_preflight_ready
        else "e008_m21_expanded_detector_policy_trajectory_execution_contract_blocked"
    )

    blocked_eval_fields = [row for row in input_contract_rows if row["contract_group"] == "blocked_policy_input"]
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "proceed_to_m22_runner_scaffold" if "ready" in status else "blocked",
            "reason": "Contract and Docker/data preflight are ready; the M22 runner script is the missing implementation unit."
            if "ready" in status and not runner_implemented
            else "Contract and Docker/data preflight are ready for execution."
            if "ready" in status
            else "Contract or Docker/data preflight failed.",
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "h001_navigation_policy_execution_ready": bool(m03_coverage.get("h001_navigation_policy_execution_ready")),
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]

    first_hit_costs = [finite_float(row.get("m19_primary_first_hit_cost_m")) for row in policy_execution_plan_rows]
    coverage = {
        "artifact_output_root": str(ARTIFACT_DIR),
        "blocked_eval_policy_field_rows": len(blocked_eval_fields),
        "candidate_navmesh_rows": len(m17_candidate_rows),
        "candidate_visit_order_rows": len(m18_visit_rows),
        "derived_output_root": str(DATA_OUT_DIR),
        "docker_image": HABITAT_IMAGE,
        "docker_preflight_ready": docker_preflight_ready,
        "docker_preflight_status_counts": gate_status_counts(docker_preflight_rows),
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "h001_candidate_source_rows_ready": m03_coverage.get("h001_candidate_source_rows_ready"),
        "h001_navigation_policy_execution_ready": bool(m03_coverage.get("h001_navigation_policy_execution_ready")),
        "input_contract_rows": len(input_contract_rows),
        "launch_long_job_now": False,
        "m17_status": m17_coverage.get("status"),
        "m18_status": m18_coverage.get("status"),
        "m19_status": m19_coverage.get("status"),
        "m20_status": m20_coverage.get("status"),
        "mean_m19_primary_first_hit_cost_m": mean(first_hit_costs),
        "metric_schema_rows": len(metric_schema_rows),
        "policy_execution_plan_rows": len(policy_execution_plan_rows),
        "policy_execution_rows": len(policy_contract_rows),
        "real_navigation_sr_spl_ready": False,
        "research3_data_root": str(RESEARCH3_DATA_ROOT),
        "runner_implemented": runner_implemented,
        "runner_output_contract_rows": len(runner_output_contract_rows),
        "selected_next_unit": selected_next,
        "status": status,
        "trajectory_execution_contract_ready": contract_ready,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(m19_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
        "version": VERSION,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "execution_input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "blocked_eval_field_rows.jsonl", blocked_eval_fields)
        write_jsonl(output_dir / "policy_execution_contract_rows.jsonl", policy_contract_rows)
        write_jsonl(output_dir / "trajectory_policy_execution_plan_rows.jsonl", policy_execution_plan_rows)
        write_jsonl(output_dir / "trajectory_metric_schema_rows.jsonl", metric_schema_rows)
        write_jsonl(output_dir / "runner_output_contract_rows.jsonl", runner_output_contract_rows)
        write_jsonl(output_dir / "docker_preflight_rows.jsonl", docker_preflight_rows)
        write_jsonl(output_dir / "docker_command_rows.jsonl", docker_command_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
        write_json(output_dir / "docker_preflight_detail.json", docker_detail)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_contract_rows, docker_preflight_rows, metric_schema_rows),
        encoding="utf-8",
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
