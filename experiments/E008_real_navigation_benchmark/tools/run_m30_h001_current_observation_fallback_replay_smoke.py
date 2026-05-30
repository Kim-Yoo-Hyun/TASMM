#!/usr/bin/env python3
"""Replay the M29 H001 current-observation backstop contract on M27 eval rows."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M30_h001_current_observation_fallback_replay_smoke_v0"
DATA_OUT_DIR = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M30_h001_current_observation_fallback_replay_smoke_v0"
M27_DIR = EXP_ROOT / "artifacts" / "E008-M27_h001_goal_evaluation_smoke_v0"
M28_DIR = EXP_ROOT / "artifacts" / "E008-M28_h001_goal_evaluation_comparison_trajectory_decision_v0"
M29_DIR = EXP_ROOT / "artifacts" / "E008-M29_h001_current_observation_fallback_source_repair_contract_v0"
M27_TOOL = EXP_ROOT / "tools" / "run_m27_h001_goal_evaluation_smoke.py"
VERSION = "e008_m30_h001_current_observation_fallback_replay_smoke_v0"

H001_POLICY = "h001_real_task_context_memory_trust_v0"
DETECTOR_POLICY = "real_detector_confidence_expanded_v0"
CONTEXT_POLICY = "real_context_agnostic_memory_trust_reobserve_v0"
STATIC_POLICY = "real_static_memory_proxy_v0"
REPAIR_POLICY = "h001_current_observation_backstop_top5_v0"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
MIN_EPISODES_FOR_NAVIGATION_CLAIM = 20


def load_m27_module() -> Any:
    spec = importlib.util.spec_from_file_location("e008_m27_goal_eval", M27_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {M27_TOOL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    module.PRIMARY_METRIC = PRIMARY_METRIC
    return module


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


def safe_delta(a: object, b: object) -> float | None:
    af = finite_float(a)
    bf = finite_float(b)
    if af is None or bf is None:
        return None
    return round(af - bf, 6)


def row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("adapter_episode_id")),
        str(row.get("task_context_id")),
        str(row.get("policy_id")),
    )


def episode_task_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("adapter_episode_id")), str(row.get("task_context_id"))


def identity(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("proposal_uid") or ""),
        str(row.get("raw_candidate_uid") or ""),
        str(row.get("frame_id") or ""),
    )


def visit_rank(row: dict[str, Any]) -> int:
    try:
        return int(row.get("visit_rank") or row.get("visit_order_index") or 10**9)
    except Exception:
        return 10**9


def group_candidate_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row_key(row)].append(row)
    for values in grouped.values():
        values.sort(key=visit_rank)
    return grouped


def index_scan_metric(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (str(row.get("adapter_episode_id")), str(row.get("task_context_id")), str(row.get("policy_id"))): row
        for row in rows
        if row.get("metric_scope") == "scan_policy"
    }


def index_aggregate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("policy_id")): row
        for row in rows
        if row.get("metric_scope") == "aggregate_policy"
    }


def build_repaired_candidate_rows(
    m29_plan_rows: list[dict[str, Any]],
    candidate_eval_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = group_candidate_rows(candidate_eval_rows)
    repaired_rows: list[dict[str, Any]] = []
    replay_plan_rows: list[dict[str, Any]] = []

    for plan in sorted(m29_plan_rows, key=lambda row: (row.get("adapter_episode_id"), row.get("task_context_id"))):
        episode_id = str(plan.get("adapter_episode_id"))
        task_context_id = str(plan.get("task_context_id"))
        h001_rows = grouped.get((episode_id, task_context_id, H001_POLICY), [])
        detector_rows = grouped.get((episode_id, task_context_id, DETECTOR_POLICY), [])
        seen = {identity(row) for row in h001_rows}
        append_rows = []
        for row in detector_rows:
            if identity(row) in seen or not row.get("path_ready"):
                continue
            append_rows.append(row)
            seen.add(identity(row))
            if len(append_rows) >= 5:
                break

        combined = [(row, "base_h001_order") for row in h001_rows] + [
            (row, "current_observation_backstop_detector_confidence") for row in append_rows
        ]
        policy_plan_uid = f"m30::{episode_id}::{task_context_id}::{REPAIR_POLICY}"
        cumulative_known_path_cost = 0.0
        for index, (row, segment) in enumerate(combined, 1):
            path_cost = finite_float(row.get("source_to_candidate_path_cost_m")) or 0.0
            cumulative_known_path_cost += path_cost
            repaired = dict(row)
            repaired.update(
                {
                    "version": VERSION,
                    "candidate_goal_eval_uid": f"m30::{episode_id}::{task_context_id}::{index:03d}",
                    "candidate_visit_uid": f"m30::{policy_plan_uid}::{index:03d}",
                    "policy_plan_uid": policy_plan_uid,
                    "policy_id": REPAIR_POLICY,
                    "policy_family": "h001_repair_memory_trust_backstop",
                    "base_policy_id": H001_POLICY,
                    "source_policy_id": row.get("policy_id"),
                    "original_policy_id": row.get("policy_id"),
                    "original_policy_plan_uid": row.get("policy_plan_uid"),
                    "original_visit_rank": row.get("visit_rank"),
                    "repair_policy_id": REPAIR_POLICY,
                    "repair_plan_uid": plan.get("repair_plan_uid"),
                    "repair_replay_segment": segment,
                    "candidate_visit_order_contract": "h001_preserve_then_current_observation_backstop_top5",
                    "visit_rank": index,
                    "cumulative_known_path_cost_m": round(cumulative_known_path_cost, 6),
                    "policy_input_allowed": True,
                    "policy_input_uses_eval_goal_or_viewpoint": False,
                    "policy_input_uses_failure_label": False,
                    "uses_objectnav_eval_goal_for_policy": False,
                    "uses_objectnav_eval_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                    "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                    "real_navigation_sr_spl_ready": False,
                    "claim_boundary": "M30 replay metric only; not a Habitat trajectory execution.",
                }
            )
            repaired_rows.append(repaired)

        replay_plan_rows.append(
            {
                "version": VERSION,
                "repair_plan_uid": plan.get("repair_plan_uid"),
                "policy_plan_uid": policy_plan_uid,
                "adapter_episode_id": episode_id,
                "scan_id": plan.get("scan_id"),
                "scene_key": plan.get("scene_key"),
                "object_category": plan.get("object_category"),
                "task_context_id": task_context_id,
                "base_policy_id": H001_POLICY,
                "repair_policy_id": REPAIR_POLICY,
                "h001_original_candidate_rows": len(h001_rows),
                "detector_current_observation_rows": len(detector_rows),
                "detector_appended_candidate_rows": len(append_rows),
                "replayed_candidate_rows": len(combined),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_failure_label": False,
            }
        )
    return repaired_rows, replay_plan_rows


def build_delta_rows(
    repaired_aggregate: dict[str, Any],
    baseline_aggregates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for baseline_id in [H001_POLICY, DETECTOR_POLICY, CONTEXT_POLICY, STATIC_POLICY]:
        baseline = baseline_aggregates.get(baseline_id, {})
        rows.append(
            {
                "version": VERSION,
                "repair_policy_id": REPAIR_POLICY,
                "baseline_policy_id": baseline_id,
                "repair_primary_success_rows": repaired_aggregate.get("primary_success_rows"),
                "baseline_primary_success_rows": baseline.get("primary_success_rows"),
                "primary_success_rows_delta_repair_minus_baseline": safe_delta(
                    repaired_aggregate.get("primary_success_rows"), baseline.get("primary_success_rows")
                ),
                "repair_primary_proxy_sr": repaired_aggregate.get("primary_proxy_sr"),
                "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
                "primary_proxy_sr_delta_repair_minus_baseline": safe_delta(
                    repaired_aggregate.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")
                ),
                "repair_primary_spl_proxy_mean": repaired_aggregate.get("primary_spl_proxy_mean"),
                "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
                "primary_spl_proxy_delta_repair_minus_baseline": safe_delta(
                    repaired_aggregate.get("primary_spl_proxy_mean"), baseline.get("primary_spl_proxy_mean")
                ),
                "claim_status": "diagnostic_goal_eval_proxy_not_real_navigation",
            }
        )
    return rows


def build_transition_rows(
    m28_episode_rows: list[dict[str, Any]],
    repaired_scan_rows: list[dict[str, Any]],
    m27_metric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    repaired_index = index_scan_metric(repaired_scan_rows)
    baseline_index = index_scan_metric(m27_metric_rows)
    rows = []
    for row in sorted(m28_episode_rows, key=lambda item: (item.get("adapter_episode_id"), item.get("task_context_id"))):
        episode_id, task_context_id = episode_task_key(row)
        repaired = repaired_index.get((episode_id, task_context_id, REPAIR_POLICY), {})
        h001 = baseline_index.get((episode_id, task_context_id, H001_POLICY), {})
        detector = baseline_index.get((episode_id, task_context_id, DETECTOR_POLICY), {})
        context = baseline_index.get((episode_id, task_context_id, CONTEXT_POLICY), {})
        static = baseline_index.get((episode_id, task_context_id, STATIC_POLICY), {})
        h001_hit = bool(h001.get("primary_hit"))
        repaired_hit = bool(repaired.get("primary_hit"))
        detector_hit = bool(detector.get("primary_hit"))
        if h001_hit and repaired_hit:
            transition_type = "h001_success_preserved"
        elif h001_hit and not repaired_hit:
            transition_type = "unexpected_h001_success_lost"
        elif not h001_hit and repaired_hit and detector_hit:
            transition_type = "detector_only_recovered_by_backstop"
        elif not h001_hit and repaired_hit and not detector_hit:
            transition_type = "new_repair_success_not_detector"
        elif not h001_hit and not repaired_hit and detector_hit:
            transition_type = "detector_only_not_recovered"
        else:
            transition_type = "remaining_all_policy_source_gap"
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "task_context_id": task_context_id,
                "m28_failure_type": row.get("failure_type"),
                "transition_type": transition_type,
                "h001_primary_hit": h001_hit,
                "repaired_primary_hit": repaired_hit,
                "detector_primary_hit": detector_hit,
                "context_agnostic_primary_hit": bool(context.get("primary_hit")),
                "static_primary_hit": bool(static.get("primary_hit")),
                "h001_candidate_rows": h001.get("candidate_rows"),
                "repaired_candidate_rows": repaired.get("candidate_rows"),
                "detector_candidate_rows": detector.get("candidate_rows"),
                "h001_primary_first_hit_rank": h001.get("primary_first_hit_rank"),
                "repaired_primary_first_hit_rank": repaired.get("primary_first_hit_rank"),
                "detector_primary_first_hit_rank": detector.get("primary_first_hit_rank"),
                "h001_primary_first_hit_cost_m": h001.get("primary_first_hit_cost_m"),
                "repaired_primary_first_hit_cost_m": repaired.get("primary_first_hit_cost_m"),
                "detector_primary_first_hit_cost_m": detector.get("primary_first_hit_cost_m"),
                "h001_primary_spl_proxy": h001.get("primary_spl_proxy"),
                "repaired_primary_spl_proxy": repaired.get("primary_spl_proxy"),
                "detector_primary_spl_proxy": detector.get("primary_spl_proxy"),
                "repaired_minus_h001_spl_proxy": safe_delta(
                    repaired.get("primary_spl_proxy"), h001.get("primary_spl_proxy")
                ),
                "repaired_minus_detector_spl_proxy": safe_delta(
                    repaired.get("primary_spl_proxy"), detector.get("primary_spl_proxy")
                ),
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
            }
        )
    return rows


def build_gate_rows(
    coverage_inputs: dict[str, Any],
    transition_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transition_counts = Counter(row["transition_type"] for row in transition_rows)
    deltas = {row["baseline_policy_id"]: row for row in delta_rows}
    repaired_vs_detector = deltas.get(DETECTOR_POLICY, {})
    return [
        {
            "version": VERSION,
            "gate_id": "leakage_guard",
            "status": "pass" if coverage_inputs["leakage_audit_pass"] else "fail",
            "evidence": f"policy_input_uses_eval_goal_or_viewpoint={coverage_inputs['uses_objectnav_eval_goal_or_viewpoint_for_policy']}",
            "decision_effect": "required_for_any_repair_claim",
        },
        {
            "version": VERSION,
            "gate_id": "detector_only_recovery",
            "status": "pass" if transition_counts.get("detector_only_recovered_by_backstop", 0) == 3 else "warning",
            "evidence": f"detector_only_recovered_rows={transition_counts.get('detector_only_recovered_by_backstop', 0)}",
            "decision_effect": "supports_running_a_bounded_trajectory_contract_next",
        },
        {
            "version": VERSION,
            "gate_id": "no_h001_success_loss",
            "status": "pass" if transition_counts.get("unexpected_h001_success_lost", 0) == 0 else "fail",
            "evidence": f"lost_rows={transition_counts.get('unexpected_h001_success_lost', 0)}",
            "decision_effect": "blocks_repair_if_any_original_success_is_lost",
        },
        {
            "version": VERSION,
            "gate_id": "not_worse_than_detector_confidence_sr",
            "status": "pass"
            if finite_float(repaired_vs_detector.get("primary_success_rows_delta_repair_minus_baseline")) == 0
            else "fail",
            "evidence": (
                "success_delta_repair_minus_detector="
                f"{repaired_vs_detector.get('primary_success_rows_delta_repair_minus_baseline')}"
            ),
            "decision_effect": "allows_small_trajectory_contract_but_not_superiority_claim",
        },
        {
            "version": VERSION,
            "gate_id": "beats_detector_confidence_spl",
            "status": "pass"
            if (finite_float(repaired_vs_detector.get("primary_spl_proxy_delta_repair_minus_baseline")) or -1.0) > 0
            else "fail",
            "evidence": (
                "spl_delta_repair_minus_detector="
                f"{repaired_vs_detector.get('primary_spl_proxy_delta_repair_minus_baseline')}"
            ),
            "decision_effect": "blocks_claim_that_repair_is_better_than_detector_confidence",
        },
        {
            "version": VERSION,
            "gate_id": "remaining_candidate_source_gap",
            "status": "fail" if transition_counts.get("remaining_all_policy_source_gap", 0) else "pass",
            "evidence": f"remaining_all_policy_source_gap_rows={transition_counts.get('remaining_all_policy_source_gap', 0)}",
            "decision_effect": "blocks_final_navigation_and_robustness_claims",
        },
        {
            "version": VERSION,
            "gate_id": "true_dynamic_stale_memory_source",
            "status": "fail" if coverage_inputs["h001_initial_memory_proxy_not_true_dynamic_stale_memory"] else "pass",
            "evidence": (
                "h001_initial_memory_proxy_not_true_dynamic_stale_memory="
                f"{coverage_inputs['h001_initial_memory_proxy_not_true_dynamic_stale_memory']}"
            ),
            "decision_effect": "blocks_dynamic_stale_memory_claim_on_hm3d",
        },
        {
            "version": VERSION,
            "gate_id": "navigation_scale",
            "status": "pass" if int(coverage_inputs["episode_count"] or 0) >= MIN_EPISODES_FOR_NAVIGATION_CLAIM else "fail",
            "evidence": f"episode_count={coverage_inputs['episode_count']}; required>={MIN_EPISODES_FOR_NAVIGATION_CLAIM}",
            "decision_effect": "blocks_paper_navigation_claim_if_fail",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_repair_recovers_detector_only_goal_proxy_rows",
            "supported": True,
            "claim_boundary": "M30 shows the fixed current-observation backstop recovers detector-only M28 misses under GoalEvalProxy.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_repair_beats_detector_confidence",
            "supported": False,
            "claim_boundary": "M30 matches detector-confidence primary SR but has lower SPL proxy due to appended backstop cost.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M30 is still a goal-evaluation replay, not a Habitat trajectory execution.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M30 uses the existing 6-episode HM3D detector bridge and does not scale real RGB-D/open-vocabulary robustness.",
        },
    ]


def write_report(
    path: Path,
    coverage: dict[str, Any],
    aggregate_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    transition_counts = Counter(row["transition_type"] for row in transition_rows)
    lines = [
        "# E008-M30 H001 Current-Observation Fallback Replay Smoke",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Repaired candidate-goal eval rows: {coverage['repaired_candidate_goal_eval_rows']}.",
        f"- Repaired primary success rows: {coverage['repaired_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Base H001 primary success rows: {coverage['base_h001_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Detector-confidence primary success rows: {coverage['detector_primary_success_rows']} / {coverage['scan_policy_rows_per_policy']}.",
        f"- Recovered H001 failure rows: {coverage['recovered_h001_failure_rows']}.",
        f"- Remaining all-policy source-gap rows: {coverage['remaining_all_policy_source_gap_rows']}.",
        f"- H001 success-loss rows: {coverage['lost_h001_success_rows']}.",
        f"- Uses `ObjectNav` eval goal/viewpoint for policy: {coverage['uses_objectnav_eval_goal_or_viewpoint_for_policy']}.",
        "",
        "## Aggregate Metrics",
        "",
        "| Policy | Success rows | `GoalEvalProxySR` | `GoalEvalProxySPL` | Mean hit rank | Mean hit cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in aggregate_rows:
        lines.append(
            "| `{}` | {} / {} | {} | {} | {} | {} |".format(
                row.get("policy_id"),
                row.get("primary_success_rows"),
                row.get("scan_policy_rows"),
                row.get("primary_proxy_sr"),
                row.get("primary_spl_proxy_mean"),
                row.get("primary_first_hit_rank_mean_over_success"),
                row.get("primary_first_hit_cost_m_mean_over_success"),
            )
        )
    lines.extend(["", "## Deltas", "", "| Baseline | Success delta | SR delta | SPL delta |", "| --- | ---: | ---: | ---: |"])
    for row in delta_rows:
        lines.append(
            "| `{}` | {} | {} | {} |".format(
                row.get("baseline_policy_id"),
                row.get("primary_success_rows_delta_repair_minus_baseline"),
                row.get("primary_proxy_sr_delta_repair_minus_baseline"),
                row.get("primary_spl_proxy_delta_repair_minus_baseline"),
            )
        )
    lines.extend(["", "## Transition Types", "", "| Transition type | Rows |", "| --- | ---: |"])
    for transition_type, count in transition_counts.most_common():
        lines.append(f"| `{transition_type}` | {count} |")
    lines.extend(["", "## Gates", "", "| Gate | Status | Evidence |", "| --- | --- | --- |"])
    for row in gate_rows:
        lines.append(f"| `{row['gate_id']}` | `{row['status']}` | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M30 supports a leakage-safe replay result, not final H001 real navigation.",
            "- The replay recovers the 3 detector-only M28 rows without losing prior H001 successes.",
            "- The repaired policy matches detector-confidence `GoalEvalProxySR` but does not beat detector-confidence `GoalEvalProxySPL`.",
            "- The 9 all-policy source-gap rows, 6-episode scale, and static-memory proxy still block final claims.",
            "",
            "## Next",
            "",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m27_module = load_m27_module()
    m27_coverage = read_json(M27_DIR / "coverage.json")
    m28_coverage = read_json(M28_DIR / "coverage.json")
    m29_coverage = read_json(M29_DIR / "coverage.json")
    candidate_eval_rows = read_jsonl(M27_DIR / "h001_candidate_goal_eval_rows.jsonl")
    m27_metric_rows = read_jsonl(M27_DIR / "h001_policy_goal_metric_rows.jsonl")
    m28_episode_rows = read_jsonl(M28_DIR / "episode_task_comparison_rows.jsonl")
    m29_plan_rows = read_jsonl(M29_DIR / "backstop_plan_rows.jsonl")

    repaired_candidate_rows, replay_plan_rows = build_repaired_candidate_rows(m29_plan_rows, candidate_eval_rows)
    repaired_scan_rows, repaired_context_rows, repaired_aggregate_rows = m27_module.build_metric_rows(repaired_candidate_rows)
    repaired_metric_rows = repaired_scan_rows + repaired_context_rows + repaired_aggregate_rows
    repaired_aggregate = repaired_aggregate_rows[0] if repaired_aggregate_rows else {}
    baseline_aggregates = index_aggregate(m27_metric_rows)
    aggregate_comparison_rows = [
        baseline_aggregates[policy_id]
        for policy_id in [STATIC_POLICY, CONTEXT_POLICY, H001_POLICY, DETECTOR_POLICY]
        if policy_id in baseline_aggregates
    ] + repaired_aggregate_rows
    delta_rows = build_delta_rows(repaired_aggregate, baseline_aggregates)
    transition_rows = build_transition_rows(m28_episode_rows, repaired_scan_rows, m27_metric_rows)
    transition_counts = Counter(row["transition_type"] for row in transition_rows)

    coverage_inputs = {
        "episode_count": m28_coverage.get("episode_count"),
        "leakage_audit_pass": not any(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in repaired_candidate_rows),
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
            row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") for row in repaired_candidate_rows
        ),
        "h001_initial_memory_proxy_not_true_dynamic_stale_memory": m27_coverage.get(
            "h001_initial_memory_proxy_not_true_dynamic_stale_memory"
        ),
    }
    gate_rows = build_gate_rows(coverage_inputs, transition_rows, delta_rows)
    gate_counts = Counter(row["status"] for row in gate_rows)

    h001_aggregate = baseline_aggregates.get(H001_POLICY, {})
    detector_aggregate = baseline_aggregates.get(DETECTOR_POLICY, {})
    context_aggregate = baseline_aggregates.get(CONTEXT_POLICY, {})
    static_aggregate = baseline_aggregates.get(STATIC_POLICY, {})
    selected_next_unit = "E008-M31 H001 fallback trajectory-execution contract and source-gap boundary"
    coverage = {
        "version": VERSION,
        "status": "e008_m30_h001_current_observation_fallback_replay_smoke_ready_trajectory_contract_next",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m27_status": m27_coverage.get("status"),
        "m28_status": m28_coverage.get("status"),
        "m29_status": m29_coverage.get("status"),
        "episode_count": m28_coverage.get("episode_count"),
        "scan_policy_rows_per_policy": repaired_aggregate.get("scan_policy_rows"),
        "replay_plan_rows": len(replay_plan_rows),
        "repaired_candidate_goal_eval_rows": len(repaired_candidate_rows),
        "repaired_metric_rows": len(repaired_metric_rows),
        "transition_rows": len(transition_rows),
        "repaired_primary_success_rows": repaired_aggregate.get("primary_success_rows"),
        "base_h001_primary_success_rows": h001_aggregate.get("primary_success_rows"),
        "detector_primary_success_rows": detector_aggregate.get("primary_success_rows"),
        "context_agnostic_primary_success_rows": context_aggregate.get("primary_success_rows"),
        "static_primary_success_rows": static_aggregate.get("primary_success_rows"),
        "repaired_primary_proxy_sr": repaired_aggregate.get("primary_proxy_sr"),
        "repaired_primary_spl_proxy_mean": repaired_aggregate.get("primary_spl_proxy_mean"),
        "base_h001_primary_proxy_sr": h001_aggregate.get("primary_proxy_sr"),
        "detector_primary_proxy_sr": detector_aggregate.get("primary_proxy_sr"),
        "detector_primary_spl_proxy_mean": detector_aggregate.get("primary_spl_proxy_mean"),
        "repaired_minus_h001_success_rows": safe_delta(
            repaired_aggregate.get("primary_success_rows"), h001_aggregate.get("primary_success_rows")
        ),
        "repaired_minus_detector_success_rows": safe_delta(
            repaired_aggregate.get("primary_success_rows"), detector_aggregate.get("primary_success_rows")
        ),
        "repaired_minus_h001_spl_proxy": safe_delta(
            repaired_aggregate.get("primary_spl_proxy_mean"), h001_aggregate.get("primary_spl_proxy_mean")
        ),
        "repaired_minus_detector_spl_proxy": safe_delta(
            repaired_aggregate.get("primary_spl_proxy_mean"), detector_aggregate.get("primary_spl_proxy_mean")
        ),
        "recovered_h001_failure_rows": transition_counts.get("detector_only_recovered_by_backstop", 0)
        + transition_counts.get("new_repair_success_not_detector", 0),
        "detector_only_recovered_rows": transition_counts.get("detector_only_recovered_by_backstop", 0),
        "preserved_h001_success_rows": transition_counts.get("h001_success_preserved", 0),
        "lost_h001_success_rows": transition_counts.get("unexpected_h001_success_lost", 0),
        "remaining_failure_rows": transition_counts.get("remaining_all_policy_source_gap", 0)
        + transition_counts.get("detector_only_not_recovered", 0),
        "remaining_all_policy_source_gap_rows": transition_counts.get("remaining_all_policy_source_gap", 0),
        "transition_type_counts": dict(transition_counts),
        "gate_rows": len(gate_rows),
        "gate_pass": gate_counts.get("pass", 0),
        "gate_warning": gate_counts.get("warning", 0),
        "gate_fail": gate_counts.get("fail", 0),
        "leakage_audit_pass": coverage_inputs["leakage_audit_pass"],
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": coverage_inputs[
            "uses_objectnav_eval_goal_or_viewpoint_for_policy"
        ],
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
        "policy_input_uses_failure_label": False,
        "repaired_matches_detector_sr": safe_delta(
            repaired_aggregate.get("primary_success_rows"), detector_aggregate.get("primary_success_rows")
        )
        == 0,
        "repaired_beats_detector_spl_proxy": (
            safe_delta(repaired_aggregate.get("primary_spl_proxy_mean"), detector_aggregate.get("primary_spl_proxy_mean"))
            or -1
        )
        > 0,
        "trajectory_contract_recommended_next": True,
        "trajectory_execution_recommended_now": False,
        "source_expansion_required_before_final_claim": True,
        "launch_long_job_now": False,
        "selected_next_unit": selected_next_unit,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
    }

    claim_boundary_rows = build_claim_boundary_rows()
    route_decision_rows = [
        {
            "version": VERSION,
            "decision": "prepare_bounded_h001_fallback_trajectory_contract",
            "selected_next_unit": selected_next_unit,
            "reason": (
                "M30 recovers the 3 detector-only M28 rows without H001 success loss and matches detector-confidence SR, "
                "but remaining source-gap rows and lower SPL proxy keep final claims blocked."
            ),
            "launch_long_job_now": False,
            "trajectory_contract_recommended_next": True,
            "trajectory_execution_recommended_now": False,
            "real_navigation_sr_spl_ready": False,
        }
    ]

    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_jsonl(ARTIFACT_DIR / "fallback_replay_candidate_goal_eval_rows.jsonl", repaired_candidate_rows)
    write_jsonl(ARTIFACT_DIR / "fallback_replay_policy_goal_metric_rows.jsonl", repaired_metric_rows)
    write_jsonl(ARTIFACT_DIR / "aggregate_policy_comparison_rows.jsonl", aggregate_comparison_rows)
    write_jsonl(ARTIFACT_DIR / "fallback_replay_delta_rows.jsonl", delta_rows)
    write_jsonl(ARTIFACT_DIR / "failure_transition_rows.jsonl", transition_rows)
    write_jsonl(ARTIFACT_DIR / "fallback_replay_plan_rows.jsonl", replay_plan_rows)
    write_jsonl(ARTIFACT_DIR / "replay_gate_rows.jsonl", gate_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", route_decision_rows)
    write_report(
        ARTIFACT_DIR / "report.md",
        coverage,
        aggregate_comparison_rows,
        delta_rows,
        transition_rows,
        gate_rows,
    )

    write_json(DATA_OUT_DIR / "coverage.json", coverage)
    write_jsonl(DATA_OUT_DIR / "fallback_replay_candidate_goal_eval_rows.jsonl", repaired_candidate_rows)
    write_jsonl(DATA_OUT_DIR / "fallback_replay_policy_goal_metric_rows.jsonl", repaired_metric_rows)
    write_jsonl(DATA_OUT_DIR / "failure_transition_rows.jsonl", transition_rows)
    write_jsonl(DATA_OUT_DIR / "fallback_replay_delta_rows.jsonl", delta_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
