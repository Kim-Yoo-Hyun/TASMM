#!/usr/bin/env python3
"""Build the M183 source-pool detector-policy trajectory contract and Docker preflight."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M129_TOOL = EXP_ROOT / "tools" / "plan_m129_target_free_detector_policy_trajectory_contract.py"

VERSION = "e008_m183_docker_trajectory_execution_contract_preflight_v0"
READY_STATUS = "e008_m183_docker_trajectory_execution_contract_preflight_ready_runner_next"
READY_RUNNER_MISSING_STATUS = "e008_m183_docker_trajectory_execution_contract_preflight_ready_runner_missing"
BLOCKED_STATUS = "e008_m183_docker_trajectory_execution_contract_preflight_blocked"

ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M183_docker_trajectory_execution_contract_preflight_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M183_docker_trajectory_execution_contract_preflight_v0"
M180_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"
M181_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M181_expanded_candidate_visit_order_path_materialization_v0"
M182_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M182_leakage_safe_goal_evaluation_proxy_v0"
M184_RUNNER = EXP_ROOT / "tools" / "run_m184_docker_trajectory_execution_sr_spl.py"
M184_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"
M184_DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M184_docker_trajectory_execution_sr_spl_v0"


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
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_m128_compat() -> Path:
    compat_dir = ARTIFACT_DIR / "_compat_inputs" / "m128_promotion_gate"
    m182_cov = read_json(M182_ARTIFACT_DIR / "coverage.json")
    promotion_ready = (
        m182_cov.get("status") == "e008_m182_leakage_safe_goal_evaluation_proxy_ready"
        and bool(m182_cov.get("leakage_audit_pass"))
        and bool(m182_cov.get("target_free_proxy_recovery_observed"))
    )
    write_json(
        compat_dir / "coverage.json",
        {
            "version": VERSION,
            "status": "e008_m183_proxy_promotion_compat_ready" if promotion_ready else "e008_m183_proxy_promotion_compat_blocked",
            "trajectory_contract_promotion_ready": promotion_ready,
            "m182_status": m182_cov.get("status"),
            "target_free_proxy_recovery_observed": m182_cov.get("target_free_proxy_recovery_observed"),
            "leakage_audit_pass": m182_cov.get("leakage_audit_pass"),
        },
    )
    return compat_dir


def build_m183_readiness_gate_rows(
    m129: Any,
    m180_cov: dict[str, Any],
    m181_cov: dict[str, Any],
    m182_cov: dict[str, Any],
    compat_promotion_cov: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    goal_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    docker_rows: list[dict[str, Any]],
    budget_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    policies = Counter(str(row.get("policy_id")) for row in plan_rows)
    full_rows = [
        row
        for row in budget_summary_rows
        if row.get("metric_scope") == "policy_budget_aggregate" and row.get("budget") == "full"
    ]
    min_full_proxy_sr = min([float(row.get("GoalEvalProxySR") or 0.0) for row in full_rows], default=0.0)
    return [
        {
            "version": VERSION,
            "gate_id": "m180_navmesh_source_readiness_ready",
            "status": "pass"
            if m180_cov.get("status") == "e008_m180_candidate_navmesh_source_readiness_validation_ready"
            else "fail",
            "evidence": f"M180 status={m180_cov.get('status')}; path_ready={m180_cov.get('source_to_snapped_path_found_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m181_visit_order_ready",
            "status": "pass" if m181_cov.get("candidate_visit_order_path_smoke_ready") else "fail",
            "evidence": f"M181 status={m181_cov.get('status')}; visit_order_rows={m181_cov.get('visit_order_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m182_leakage_safe_goal_eval_ready",
            "status": "pass" if m182_cov.get("leakage_audit_pass") else "fail",
            "evidence": f"M182 status={m182_cov.get('status')}; leakage={m182_cov.get('leakage_audit_pass')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m182_proxy_recovery_observed",
            "status": "pass" if m182_cov.get("target_free_proxy_recovery_observed") else "fail",
            "evidence": f"target_free_proxy_recovery_observed={m182_cov.get('target_free_proxy_recovery_observed')}.",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_contract_promotion_ready",
            "status": "pass" if compat_promotion_cov.get("trajectory_contract_promotion_ready") else "fail",
            "evidence": f"compat promotion={compat_promotion_cov.get('trajectory_contract_promotion_ready')}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_candidate_rows_materialized",
            "status": "pass" if len(candidate_rows) == int(m181_cov.get("visit_order_rows") or -1) else "fail",
            "evidence": f"candidate rows={len(candidate_rows)}; M181 visit_order_rows={m181_cov.get('visit_order_rows')}.",
        },
        {
            "version": VERSION,
            "gate_id": "runner_plan_rows_materialized",
            "status": "pass"
            if len(plan_rows) == m129.EXPECTED_PLAN_ROWS and len(policies) == m129.EXPECTED_POLICY_COUNT
            else "fail",
            "evidence": f"plan rows={len(plan_rows)}; expected={m129.EXPECTED_PLAN_ROWS}; policies={dict(sorted(policies.items()))}.",
        },
        {
            "version": VERSION,
            "gate_id": "goal_and_oracle_rows_ready",
            "status": "pass" if len(goal_rows) == m129.EXPECTED_SCAN_ROWS and len(oracle_rows) == m129.EXPECTED_SCAN_ROWS else "fail",
            "evidence": f"goal rows={len(goal_rows)}; oracle rows={len(oracle_rows)}; expected={m129.EXPECTED_SCAN_ROWS}.",
        },
        {
            "version": VERSION,
            "gate_id": "policy_input_leakage",
            "status": "pass" if all(row.get("leakage_audit_pass") for row in leakage_rows) else "fail",
            "evidence": f"blocked hits={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}.",
        },
        {
            "version": VERSION,
            "gate_id": "full_ranked_proxy_success_floor",
            "status": "pass" if min_full_proxy_sr >= 1.0 else "warning",
            "evidence": f"full-budget min proxy SR={min_full_proxy_sr:.6f}; warning still allows M184 execution for protected-baseline interpretation.",
        },
        {
            "version": VERSION,
            "gate_id": "docker_preflight",
            "status": "pass"
            if all(row.get("status") in {"pass", "warning"} for row in docker_rows)
            and not any(row.get("status") == "fail" for row in docker_rows)
            else "fail",
            "evidence": f"fail={sum(1 for row in docker_rows if row.get('status') == 'fail')}; warning={sum(1 for row in docker_rows if row.get('status') == 'warning')}.",
        },
        {
            "version": VERSION,
            "gate_id": "m184_runner_wrapper",
            "status": "pass" if M184_RUNNER.exists() else "warning",
            "evidence": f"M184 runner exists={M184_RUNNER.exists()}.",
        },
    ]


def build_m184_command_rows(m129: Any) -> list[dict[str, Any]]:
    command = (
        "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp "
        "-v /home/yoohyun/research2/local_dataset/data:/data:ro "
        "-v /home/yoohyun/research2:/work -w /work "
        f"{m129.HABITAT_IMAGE} bash -lc "
        "\"micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/run_m184_docker_trajectory_execution_sr_spl.py "
        "--m129-contract experiments/E008_real_navigation_benchmark/artifacts/E008-M183_docker_trajectory_execution_contract_preflight_v0 "
        "--out-root experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0 "
        "--derived-out-root local_dataset/HM3D_navigation_bridge/E008-M184_docker_trajectory_execution_sr_spl_v0\""
    )
    return [
        {
            "version": VERSION,
            "command_id": "e008_m184_docker_trajectory_execution_sr_spl",
            "working_directory": str(ROOT),
            "docker_image": m129.HABITAT_IMAGE,
            "source_mount": "/home/yoohyun/research2/local_dataset/data:/data:ro",
            "repo_mount": "/home/yoohyun/research2:/work",
            "contract_path": str(ARTIFACT_DIR.relative_to(ROOT)),
            "runner_path": str(M184_RUNNER.relative_to(ROOT)),
            "runner_implemented": M184_RUNNER.exists(),
            "output_path": str(M184_ARTIFACT_DIR.relative_to(ROOT)),
            "derived_output_path": str(M184_DATA_OUT_DIR.relative_to(ROOT)),
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
                "p=Path('experiments/E008_real_navigation_benchmark/artifacts/E008-M184_docker_trajectory_execution_sr_spl_v0/coverage.json')\n"
                "c=json.loads(p.read_text())\n"
                "assert c['status']=='e008_m184_docker_trajectory_execution_sr_spl_ready'\n"
                "print('m184 ready')\n"
                "PY"
            ),
        }
    ]


def main() -> None:
    m129 = load_module(M129_TOOL, "e008_m129_contract_wrapper")
    compat_m128_dir = build_m128_compat()
    scan_rows = read_jsonl(M180_ARTIFACT_DIR / "scan_source_boundary_rows.jsonl")

    m129.VERSION = VERSION
    m129.READY_STATUS = READY_STATUS
    m129.READY_RUNNER_MISSING_STATUS = READY_RUNNER_MISSING_STATUS
    m129.BLOCKED_STATUS = BLOCKED_STATUS
    m129.ARTIFACT_DIR = ARTIFACT_DIR
    m129.DATA_OUT_DIR = DATA_OUT_DIR
    m129.M125_DIR = M180_ARTIFACT_DIR
    m129.M126_DIR = M181_ARTIFACT_DIR
    m129.M127_DIR = M182_ARTIFACT_DIR
    m129.M128_DIR = compat_m128_dir
    m129.M130_RUNNER = M184_RUNNER
    m129.M130_ARTIFACT_DIR = M184_ARTIFACT_DIR
    m129.M130_DATA_OUT_DIR = M184_DATA_OUT_DIR
    m129.NEXT_UNIT = "E008-M184 Docker trajectory execution with SR, SPL, path length, visits"
    m129.EXPECTED_SCAN_ROWS = len(scan_rows)
    m129.EXPECTED_PLAN_ROWS = len(scan_rows) * m129.EXPECTED_POLICY_COUNT

    def gate_wrapper(
        m180_cov: dict[str, Any],
        m181_cov: dict[str, Any],
        m182_cov: dict[str, Any],
        compat_promotion_cov: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
        plan_rows: list[dict[str, Any]],
        goal_rows: list[dict[str, Any]],
        oracle_rows: list[dict[str, Any]],
        leakage_rows: list[dict[str, Any]],
        docker_rows: list[dict[str, Any]],
        budget_summary_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return build_m183_readiness_gate_rows(
            m129,
            m180_cov,
            m181_cov,
            m182_cov,
            compat_promotion_cov,
            candidate_rows,
            plan_rows,
            goal_rows,
            oracle_rows,
            leakage_rows,
            docker_rows,
            budget_summary_rows,
        )

    m129.build_readiness_gate_rows = gate_wrapper
    m129.build_m130_command_rows = lambda: build_m184_command_rows(m129)
    m129.main()

    report_path = ARTIFACT_DIR / "report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        report = report.replace(
            "# E008-M129 Target-Free Detector-Policy Trajectory Contract",
            "# E008-M183 Docker Trajectory Execution Contract Preflight",
        )
        report = report.replace("M129", "M183")
        report = report.replace("M130", "M184")
        report_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
