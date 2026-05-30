#!/usr/bin/env python3
"""Analyze M19 proxy vs M22 trajectory consistency and decide the H001 source gate."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M23_trajectory_proxy_consistency_h001_source_decision_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M23_trajectory_proxy_consistency_h001_source_decision_v0"
VERSION = "e008_m23_trajectory_proxy_consistency_h001_source_decision_v0"

M03_DIR = EXP_ROOT / "artifacts" / "E008-M03_h001_candidate_navigation_adapter_contract_v0"
M19_DIR = EXP_ROOT / "artifacts" / "E008-M19_expanded_detector_candidate_goal_evaluation_smoke_v0"
M21_DIR = EXP_ROOT / "artifacts" / "E008-M21_expanded_detector_policy_trajectory_execution_contract_v0"
M22_DIR = EXP_ROOT / "artifacts" / "E008-M22_expanded_detector_policy_trajectory_execution_smoke_v0"

SPL_CLOSE_TOL = 0.10
PATH_INFLATION_WARNING_RATIO = 2.0


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
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def scan_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("policy_id")), str(row.get("scan_id"))): row
        for row in rows
        if row.get("metric_scope") == "scan_policy"
    }


def aggregate_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in rows if row.get("metric_scope") == "policy_aggregate"}


def rank_desc(values: dict[str, float | None]) -> dict[str, int | None]:
    clean = [(key, value) for key, value in values.items() if value is not None]
    clean.sort(key=lambda item: (-float(item[1]), item[0]))
    return {key: idx + 1 for idx, (key, _) in enumerate(clean)} | {
        key: None for key, value in values.items() if value is None
    }


def consistency_class(m19_hit: bool, m22_success: bool) -> str:
    if m19_hit and m22_success:
        return "proxy_and_trajectory_success"
    if m19_hit and not m22_success:
        return "proxy_overestimates_success"
    if not m19_hit and m22_success:
        return "proxy_underestimates_success"
    return "proxy_and_trajectory_failure"


def spl_class(delta: float | None) -> str:
    if delta is None:
        return "spl_missing"
    if abs(delta) <= SPL_CLOSE_TOL:
        return "spl_close"
    if delta < 0:
        return "proxy_overestimates_spl"
    return "proxy_underestimates_spl"


def build_scan_consistency_rows(m19_rows: list[dict[str, Any]], m22_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    m19 = scan_index(m19_rows)
    m22 = scan_index(m22_rows)
    rows = []
    for key in sorted(set(m19) | set(m22)):
        policy_id, scan_id = key
        p = m19.get(key, {})
        t = m22.get(key, {})
        m19_hit = bool(p.get("primary_hit"))
        m22_success = bool(t.get("trajectory_success"))
        m19_rank = finite_float(p.get("primary_first_hit_rank"))
        m22_rank = finite_float(t.get("StopRank"))
        m19_cost = finite_float(p.get("primary_first_hit_cost_m"))
        m22_path = finite_float(t.get("PathLengthM"))
        m19_spl = finite_float(p.get("primary_spl_proxy"))
        m22_spl = finite_float(t.get("SPL"))
        rank_delta = None if m19_rank is None or m22_rank is None else float(m22_rank - m19_rank)
        path_delta = None if m19_cost is None or m22_path is None else float(m22_path - m19_cost)
        path_ratio = None if m19_cost in (None, 0.0) or m22_path is None else float(m22_path / m19_cost)
        spl_delta = None if m19_spl is None or m22_spl is None else float(m22_spl - m19_spl)
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_id": scan_id,
                "adapter_episode_id": t.get("adapter_episode_id") or p.get("adapter_episode_id"),
                "scene_key": t.get("scene_key") or p.get("scene_key"),
                "object_category": t.get("object_category") or p.get("object_category"),
                "m19_primary_hit": m19_hit,
                "m22_trajectory_success": m22_success,
                "success_agreement": m19_hit == m22_success,
                "success_consistency_class": consistency_class(m19_hit, m22_success),
                "m19_primary_first_hit_rank": m19_rank,
                "m22_stop_rank": m22_rank,
                "stop_rank_delta": rank_delta,
                "rank_consistent": rank_delta == 0.0,
                "m19_primary_first_hit_cost_m": m19_cost,
                "m22_path_length_m": m22_path,
                "path_length_minus_proxy_cost_m": path_delta,
                "path_inflation_ratio": path_ratio,
                "path_inflation_warning": path_ratio is not None and path_ratio > PATH_INFLATION_WARNING_RATIO,
                "m19_primary_spl_proxy": m19_spl,
                "m22_spl": m22_spl,
                "spl_delta": spl_delta,
                "spl_consistency_class": spl_class(spl_delta),
                "m22_candidate_visits": t.get("CandidateVisits"),
                "m22_executed_stops": t.get("ExecutedStops"),
                "m22_failure_type": t.get("FailureType"),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": bool(
                    p.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                )
                or bool(t.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")),
            }
        )
    return rows


def build_policy_consistency_rows(
    scan_rows: list[dict[str, Any]],
    m19_rows: list[dict[str, Any]],
    m22_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m19 = aggregate_index(m19_rows)
    m22 = aggregate_index(m22_rows)
    proxy_spl = {
        policy_id: finite_float(row.get("primary_spl_proxy_mean")) for policy_id, row in m19.items()
    }
    traj_spl = {policy_id: finite_float(row.get("SPL")) for policy_id, row in m22.items()}
    proxy_rank = rank_desc(proxy_spl)
    traj_rank = rank_desc(traj_spl)
    by_policy: dict[str, list[dict[str, Any]]] = {}
    for row in scan_rows:
        by_policy.setdefault(str(row.get("policy_id")), []).append(row)
    rows = []
    for policy_id in sorted(set(m19) | set(m22) | set(by_policy)):
        rows_for_policy = by_policy.get(policy_id, [])
        scan_count = len(rows_for_policy)
        success_agree = sum(1 for row in rows_for_policy if row.get("success_agreement"))
        rank_agree = sum(1 for row in rows_for_policy if row.get("rank_consistent"))
        spl_close = sum(1 for row in rows_for_policy if row.get("spl_consistency_class") == "spl_close")
        path_warn = sum(1 for row in rows_for_policy if row.get("path_inflation_warning"))
        pr = proxy_rank.get(policy_id)
        tr = traj_rank.get(policy_id)
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "scan_policy_rows": scan_count,
                "success_agreement_rows": success_agree,
                "success_agreement_rate": safe_ratio(success_agree, scan_count),
                "rank_consistent_rows": rank_agree,
                "rank_consistency_rate": safe_ratio(rank_agree, scan_count),
                "spl_close_rows": spl_close,
                "spl_close_rate": safe_ratio(spl_close, scan_count),
                "path_inflation_warning_rows": path_warn,
                "m19_primary_proxy_sr": finite_float(m19.get(policy_id, {}).get("primary_proxy_sr")),
                "m22_sr": finite_float(m22.get(policy_id, {}).get("SR")),
                "m19_primary_spl_proxy_mean": proxy_spl.get(policy_id),
                "m22_spl": traj_spl.get(policy_id),
                "spl_mean_delta": None
                if proxy_spl.get(policy_id) is None or traj_spl.get(policy_id) is None
                else float(traj_spl[policy_id] - proxy_spl[policy_id]),  # type: ignore[index]
                "m19_proxy_spl_rank": pr,
                "m22_trajectory_spl_rank": tr,
                "spl_rank_delta": None if pr is None or tr is None else int(tr - pr),
                "spl_order_consistent": pr == tr,
                "m19_mean_hit_rank_over_success": finite_float(
                    m19.get(policy_id, {}).get("primary_first_hit_rank_mean_over_success")
                ),
                "m22_stop_rank_mean_over_success": finite_float(m22.get(policy_id, {}).get("StopRank_mean_over_success")),
                "m22_candidate_visits_mean": finite_float(m22.get(policy_id, {}).get("CandidateVisits_mean")),
                "m22_path_length_mean_m": finite_float(m22.get(policy_id, {}).get("PathLengthM_mean")),
                "claim_boundary": "proxy_success_consistency_does_not_validate_proxy_spl_order_or_h001_policy",
            }
        )
    return rows


def build_gate_rows(
    m03_coverage: dict[str, Any],
    m21_coverage: dict[str, Any],
    m22_coverage: dict[str, Any],
    scan_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scan_count = len(scan_rows)
    success_agreement_rows = sum(1 for row in scan_rows if row.get("success_agreement"))
    spl_order_consistent_rows = sum(1 for row in policy_rows if row.get("spl_order_consistent"))
    h001_source_rows = int(m03_coverage.get("h001_candidate_source_rows_ready") or 0)
    episode_rows = int(m22_coverage.get("episode_rows") or 0)
    return [
        {
            "version": VERSION,
            "gate": "detector_policy_trajectory_smoke_ready",
            "status": "pass" if m22_coverage.get("real_navigation_sr_spl_smoke_ready") else "fail",
            "evidence": f"M22 trajectory rows={m22_coverage.get('trajectory_execution_rows')}, scan-policy rows={m22_coverage.get('scan_policy_metric_rows')}.",
        },
        {
            "version": VERSION,
            "gate": "proxy_success_matches_trajectory_success",
            "status": "pass" if scan_count and success_agreement_rows == scan_count else "fail",
            "evidence": f"success agreement {success_agreement_rows}/{scan_count} scan-policy rows.",
        },
        {
            "version": VERSION,
            "gate": "proxy_spl_order_matches_trajectory_spl_order",
            "status": "warning" if spl_order_consistent_rows < len(policy_rows) else "pass",
            "evidence": f"SPL rank agreement {spl_order_consistent_rows}/{len(policy_rows)} policies.",
        },
        {
            "version": VERSION,
            "gate": "h001_candidate_source_ready",
            "status": "fail" if h001_source_rows == 0 else "pass",
            "evidence": f"H001 candidate-source rows ready={h001_source_rows}.",
        },
        {
            "version": VERSION,
            "gate": "scale_ready_for_final_navigation_claim",
            "status": "warning" if episode_rows <= 6 else "pass",
            "evidence": f"Current E008 smoke scale uses {episode_rows} ObjectNav episodes.",
        },
        {
            "version": VERSION,
            "gate": "policy_leakage_guard",
            "status": "pass"
            if not bool(m21_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
            and not bool(m22_coverage.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
            else "fail",
            "evidence": "ObjectNav goal/viewpoints are metric-only fields under M21/M22.",
        },
    ]


def build_candidate_source_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "route_id": "scale_detector_policy_runner_now",
            "decision": "defer",
            "reason": "Detector-policy trajectory smoke is useful, but it does not instantiate stale memory, task context, or H001 memory trust.",
            "next_requirement": "Use only after H001 candidate-source rows exist or as a detector/navigation baseline scale-up.",
        },
        {
            "version": VERSION,
            "route_id": "use_objectnav_goal_as_stale_memory",
            "decision": "reject",
            "reason": "ObjectNav goal and viewpoint fields are evaluation labels; using them to create memory candidates would leak the answer.",
            "next_requirement": "H001 candidate sources must be generated from non-eval observations, detector/map outputs, or an explicitly allowed memory source.",
        },
        {
            "version": VERSION,
            "route_id": "3rscan_h001_to_habitat_transfer",
            "decision": "defer",
            "reason": "3RScan/3DSSG is the dynamic stale-memory source, but it has no current Habitat navmesh execution adapter in this repo.",
            "next_requirement": "Requires a simulator/navmesh bridge before real SR/SPL can be claimed on 3RScan dynamics.",
        },
        {
            "version": VERSION,
            "route_id": "hm3d_h001_candidate_source_contract",
            "decision": "select_next",
            "reason": "The next defensible step is to define non-leaking HM3D candidate-source rows that separate stale memory candidates, current detector evidence, task context, and policy outputs.",
            "next_requirement": "Write E008-M24 H001 candidate-source instantiation contract before scaling the navigation runner.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "M19 GoalEvalProxy predicts whether detector policies can eventually stop near an ObjectNav target under the current 6-episode smoke.",
            "status": "supported_as_smoke",
            "boundary": "This is success consistency, not final navigation performance.",
        },
        {
            "version": VERSION,
            "claim": "M19 proxy SPL is sufficient to rank policies for final trajectory SPL.",
            "status": "not_supported",
            "boundary": "M23 must report proxy/trajectory SPL rank mismatch before using proxy SPL as a paper-facing navigation metric.",
        },
        {
            "version": VERSION,
            "claim": "H001 improves real navigation SR/SPL.",
            "status": "not_supported",
            "boundary": "H001 candidate-source rows are still absent for HM3D ObjectNav.",
        },
        {
            "version": VERSION,
            "claim": "Detector-policy trajectory smoke is a valid bridge artifact.",
            "status": "supported_as_bridge",
            "boundary": "It can justify M24 source work, not a final Direction B result.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> str:
    policy_table = "\n".join(
        "| {policy_id} | {m19_primary_proxy_sr:.3f} | {m22_sr:.3f} | {m19_primary_spl_proxy_mean:.3f} | {m22_spl:.3f} | {spl_rank_delta} | {success_agreement_rate:.3f} |".format(
            **{
                **row,
                "m19_primary_proxy_sr": row.get("m19_primary_proxy_sr") or 0.0,
                "m22_sr": row.get("m22_sr") or 0.0,
                "m19_primary_spl_proxy_mean": row.get("m19_primary_spl_proxy_mean") or 0.0,
                "m22_spl": row.get("m22_spl") or 0.0,
                "spl_rank_delta": row.get("spl_rank_delta"),
            }
        )
        for row in policy_rows
    )
    gate_table = "\n".join(
        f"| {row['gate']} | {row['status']} | {row['evidence']} |" for row in gate_rows
    )
    decision_table = "\n".join(
        f"| {row['route_id']} | {row['decision']} | {row['reason']} |" for row in decision_rows
    )
    return f"""# E008-M23 Trajectory / Proxy Consistency

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Scan-policy consistency rows: {coverage['scan_consistency_rows']}.
- Policy consistency rows: {coverage['policy_consistency_rows']}.
- Proxy/trajectory success agreement: {coverage['success_agreement_rows']} / {coverage['scan_consistency_rows']}.
- SPL order consistent policies: {coverage['spl_order_consistent_policy_rows']} / {coverage['policy_consistency_rows']}.
- H001 candidate-source rows ready: {coverage['h001_candidate_source_rows_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Consistency

| Policy | M19 Proxy SR | M22 SR | M19 Proxy SPL | M22 SPL | SPL Rank Delta | Success Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{policy_table}

## Gates

| Gate | Status | Evidence |
| --- | --- | --- |
{gate_table}

## H001 Candidate-Source Decision

| Route | Decision | Reason |
| --- | --- | --- |
{decision_table}

## Claim Boundary

- M23 supports detector-policy trajectory bridge readiness, not final H001 navigation.
- Proxy success is consistent with executed trajectory success in this smoke, but proxy `SPL` ordering is not reliable enough as final navigation evidence.
- The next step must instantiate non-leaking H001 candidate-source rows before scaling navigation claims.
"""


def main() -> None:
    m03_coverage = read_json(M03_DIR / "coverage.json")
    m19_coverage = read_json(M19_DIR / "coverage.json")
    m21_coverage = read_json(M21_DIR / "coverage.json")
    m22_coverage = read_json(M22_DIR / "coverage.json")
    m19_rows = read_jsonl(M19_DIR / "policy_goal_metric_rows.jsonl")
    m22_rows = read_jsonl(M22_DIR / "trajectory_policy_metric_rows.jsonl")

    if not m19_coverage or not m22_coverage:
        raise SystemExit("missing M19 or M22 coverage")
    if not m19_rows or not m22_rows:
        raise SystemExit("missing M19 or M22 metric rows")

    scan_rows = build_scan_consistency_rows(m19_rows, m22_rows)
    policy_rows = build_policy_consistency_rows(scan_rows, m19_rows, m22_rows)
    gate_rows = build_gate_rows(m03_coverage, m21_coverage, m22_coverage, scan_rows, policy_rows)
    decision_rows = build_candidate_source_decision_rows()
    claim_rows = build_claim_boundary_rows()

    success_agreement_rows = sum(1 for row in scan_rows if row.get("success_agreement"))
    spl_order_consistent_rows = sum(1 for row in policy_rows if row.get("spl_order_consistent"))
    h001_source_rows = int(m03_coverage.get("h001_candidate_source_rows_ready") or 0)
    ready = bool(scan_rows) and success_agreement_rows == len(scan_rows) and bool(m22_coverage.get("real_navigation_sr_spl_smoke_ready"))
    selected_next = "E008-M24 H001 candidate-source instantiation contract" if ready else "repair E008-M23 consistency inputs"
    status = (
        "e008_m23_trajectory_proxy_consistency_ready_h001_source_missing"
        if ready and h001_source_rows == 0
        else "e008_m23_trajectory_proxy_consistency_ready"
        if ready
        else "e008_m23_trajectory_proxy_consistency_blocked"
    )
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "instantiate_h001_candidate_source_before_navigation_scale" if ready else "repair_inputs",
            "reason": "M19 proxy and M22 trajectory success agree, but SPL ordering differs and H001 source rows are absent."
            if ready
            else "M19/M22 consistency inputs are incomplete.",
            "selected_next_unit": selected_next,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "real_navigation_sr_spl_smoke_ready": bool(m22_coverage.get("real_navigation_sr_spl_smoke_ready")),
            "h001_navigation_policy_execution_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
        }
    ]

    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m19_status": m19_coverage.get("status"),
        "m22_status": m22_coverage.get("status"),
        "scan_consistency_rows": len(scan_rows),
        "policy_consistency_rows": len(policy_rows),
        "success_agreement_rows": success_agreement_rows,
        "success_agreement_rate": safe_ratio(success_agreement_rows, len(scan_rows)),
        "spl_order_consistent_policy_rows": spl_order_consistent_rows,
        "spl_order_consistency_rate": safe_ratio(spl_order_consistent_rows, len(policy_rows)),
        "mean_spl_delta": mean([finite_float(row.get("spl_delta")) for row in scan_rows]),
        "path_inflation_warning_rows": sum(1 for row in scan_rows if row.get("path_inflation_warning")),
        "h001_candidate_source_rows_ready": h001_source_rows,
        "h001_navigation_policy_execution_ready": False,
        "real_navigation_sr_spl_smoke_ready": bool(m22_coverage.get("real_navigation_sr_spl_smoke_ready")),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in scan_rows
        ),
        "launch_long_job_now": False,
        "selected_next_unit": selected_next,
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "scan_consistency_rows.jsonl", scan_rows)
        write_jsonl(output_dir / "policy_consistency_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "h001_candidate_source_decision_rows.jsonl", decision_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, gate_rows, decision_rows),
        encoding="utf-8",
    )

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
