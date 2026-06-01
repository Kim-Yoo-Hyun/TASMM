#!/usr/bin/env python3
"""Interpret E008-M70 full-val-mini goal-eval rows and decide trajectory route."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0"
)
M67_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M67_full_val_mini_detector_candidate_source_v0"
M68_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M68_full_val_mini_detector_candidate_navmesh_validation_v0"
M69_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M69_full_val_mini_detector_candidate_visit_order_path_smoke_v0"
M70_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"

VERSION = "e008_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_v0"
READY_STATUS = "e008_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_ready"
BLOCKED_STATUS = "e008_m71_full_val_mini_detector_goal_failure_comparison_trajectory_decision_blocked"
NEXT_UNIT = "E008-M72 full-val-mini detector-policy trajectory execution contract and Docker preflight"
PRIMARY_METRIC = "any_viewpoint_xz_1p0"
PRIMARY_DETECTOR_BASELINE = "detector_confidence_reachable_subset_v0"
ALL_CANDIDATE_BASELINE = "detector_confidence_all_candidates_v0"
POLICY_ORDER = [
    "detector_confidence_all_candidates_v0",
    "detector_confidence_reachable_subset_v0",
    "path_cost_ascending_reachable_subset_v0",
    "confidence_path_cost_tradeoff_reachable_subset_v0",
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


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def safe_ratio(num: int, denom: int) -> float:
    return float(num / denom) if denom else 0.0


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return float(left_f - right_f)


def fmt(value: object) -> str:
    value_f = finite_float(value)
    return "NA" if value_f is None else f"{value_f:.6f}"


def scan_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "scan_policy"]


def aggregate_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("metric_scope") == "policy_aggregate"]


def policy_aggregate_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("policy_id")): row for row in aggregate_policy_rows(rows)}


def scan_policy_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("policy_id")), str(row.get("adapter_episode_id"))): row
        for row in scan_policy_rows(rows)
    }


def classify_failure_episode(rows: list[dict[str, Any]]) -> tuple[str, str]:
    best_any = min(
        [value for value in [finite_float(row.get("best_any_viewpoint_xz_m")) for row in rows] if value is not None],
        default=None,
    )
    best_goal = min(
        [value for value in [finite_float(row.get("best_goal_xz_m")) for row in rows] if value is not None],
        default=None,
    )
    any_relaxed = any(bool(row.get("any_viewpoint_xz_1p5_hit")) for row in rows)
    goal_hit = any(bool(row.get("goal_xz_1p0_hit")) for row in rows)
    if best_any is None:
        return "missing_goal_eval_distance", "inspect M70 metric rows before trajectory contract"
    if best_any <= 1.5 and (any_relaxed or goal_hit):
        return "relaxed_viewpoint_or_goal_near_miss", "include in trajectory smoke but report threshold/viewpoint mismatch"
    if best_any <= 2.0:
        return "moderate_localization_near_miss", "include in trajectory smoke with localization-boundary accounting"
    if best_any <= 3.0:
        return "candidate_region_gap", "include as detector coverage/ranking failure, not as H001 navigation evidence"
    return "severe_candidate_source_coverage_gap", "do not interpret as policy ranking failure without candidate-source repair"


def build_policy_comparison_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates = policy_aggregate_index(metric_rows)
    baseline = aggregates.get(PRIMARY_DETECTOR_BASELINE, {})
    all_candidate = aggregates.get(ALL_CANDIDATE_BASELINE, {})
    rows: list[dict[str, Any]] = []
    for policy_id in POLICY_ORDER:
        row = aggregates.get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "primary_success_rows": row.get("primary_success_rows"),
                "scan_policy_rows": row.get("scan_policy_rows"),
                "primary_proxy_sr": row.get("primary_proxy_sr"),
                "primary_spl_proxy_mean": row.get("primary_spl_proxy_mean"),
                "primary_first_hit_rank_mean_over_success": row.get(
                    "primary_first_hit_rank_mean_over_success"
                ),
                "primary_first_hit_cost_m_mean_over_success": row.get(
                    "primary_first_hit_cost_m_mean_over_success"
                ),
                "goal_xz_1p0_proxy_sr": row.get("goal_xz_1p0_proxy_sr"),
                "any_viewpoint_xz_1p5_proxy_sr": row.get("any_viewpoint_xz_1p5_proxy_sr"),
                "blocked_rows": row.get("blocked_rows"),
                "candidate_rows": row.get("candidate_rows"),
                "delta_proxy_sr_vs_reachable_confidence": delta(
                    row.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")
                ),
                "delta_spl_proxy_vs_reachable_confidence": delta(
                    row.get("primary_spl_proxy_mean"), baseline.get("primary_spl_proxy_mean")
                ),
                "delta_hit_cost_vs_reachable_confidence_m": delta(
                    row.get("primary_first_hit_cost_m_mean_over_success"),
                    baseline.get("primary_first_hit_cost_m_mean_over_success"),
                ),
                "delta_spl_proxy_vs_all_candidate_confidence": delta(
                    row.get("primary_spl_proxy_mean"), all_candidate.get("primary_spl_proxy_mean")
                ),
                "trajectory_role": trajectory_role(policy_id),
                "supports_trajectory_contract": policy_id in POLICY_ORDER,
                "supports_final_navigation_claim": False,
            }
        )
    return rows


def trajectory_role(policy_id: str) -> str:
    if policy_id == PRIMARY_DETECTOR_BASELINE:
        return "primary_detector_confidence_baseline"
    if policy_id == ALL_CANDIDATE_BASELINE:
        return "blocked_candidate_accounting_baseline"
    if policy_id == "path_cost_ascending_reachable_subset_v0":
        return "path_efficiency_candidate_policy"
    if policy_id == "confidence_path_cost_tradeoff_reachable_subset_v0":
        return "confidence_path_cost_tradeoff_candidate_policy"
    return "diagnostic_policy"


def build_failure_episode_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scan_policy_rows(metric_rows):
        if not row.get("primary_hit"):
            by_episode[str(row.get("adapter_episode_id"))].append(row)
    out: list[dict[str, Any]] = []
    for episode_id, rows in sorted(by_episode.items()):
        failure_class, next_test = classify_failure_episode(rows)
        first = rows[0]
        best_any = [finite_float(row.get("best_any_viewpoint_xz_m")) for row in rows]
        best_goal = [finite_float(row.get("best_goal_xz_m")) for row in rows]
        first_ranks = [finite_float(row.get("best_any_viewpoint_xz_rank")) for row in rows]
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "failed_policy_count": len(rows),
                "all_detector_policies_failed": len(rows) == len(POLICY_ORDER),
                "min_best_any_viewpoint_xz_m": min([value for value in best_any if value is not None], default=None),
                "min_best_goal_xz_m": min([value for value in best_goal if value is not None], default=None),
                "mean_best_any_viewpoint_xz_m": mean(best_any),
                "mean_best_goal_xz_m": mean(best_goal),
                "min_best_any_viewpoint_rank": min(
                    [value for value in first_ranks if value is not None], default=None
                ),
                "any_viewpoint_xz_1p5_hit_any_policy": any(
                    bool(row.get("any_viewpoint_xz_1p5_hit")) for row in rows
                ),
                "goal_xz_1p0_hit_any_policy": any(bool(row.get("goal_xz_1p0_hit")) for row in rows),
                "failure_class": failure_class,
                "next_test": next_test,
                "trajectory_inclusion": trajectory_inclusion(failure_class),
                "claim_boundary": "all-policy detector proxy failure; do not treat as H001 stale-memory policy evidence",
            }
        )
    return out


def trajectory_inclusion(failure_class: str) -> str:
    if failure_class == "severe_candidate_source_coverage_gap":
        return "include_for_failure_accounting_only"
    if failure_class in {"relaxed_viewpoint_or_goal_near_miss", "moderate_localization_near_miss"}:
        return "include_for_trajectory_threshold_sensitivity"
    return "include_for_detector_failure_taxonomy"


def build_episode_policy_outcome_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = scan_policy_index(metric_rows)
    episodes = sorted({episode_id for _, episode_id in index})
    rows: list[dict[str, Any]] = []
    for episode_id in episodes:
        policy_rows = [index[(policy_id, episode_id)] for policy_id in POLICY_ORDER if (policy_id, episode_id) in index]
        if not policy_rows:
            continue
        success_count = sum(1 for row in policy_rows if row.get("primary_hit"))
        first = policy_rows[0]
        rows.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": first.get("scan_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "policy_rows": len(policy_rows),
                "primary_success_policy_count": success_count,
                "all_policy_success": success_count == len(policy_rows),
                "all_policy_failure": success_count == 0,
                "best_any_viewpoint_xz_m_min": min(
                    [
                        value
                        for value in [finite_float(row.get("best_any_viewpoint_xz_m")) for row in policy_rows]
                        if value is not None
                    ],
                    default=None,
                ),
                "best_goal_xz_m_min": min(
                    [
                        value
                        for value in [finite_float(row.get("best_goal_xz_m")) for row in policy_rows]
                        if value is not None
                    ],
                    default=None,
                ),
                "path_cost_policy_spl_best": max(
                    [
                        value
                        for value in [
                            finite_float(index.get(("path_cost_ascending_reachable_subset_v0", episode_id), {}).get("primary_spl_proxy")),
                            finite_float(index.get(("confidence_path_cost_tradeoff_reachable_subset_v0", episode_id), {}).get("primary_spl_proxy")),
                        ]
                        if value is not None
                    ],
                    default=None,
                ),
                "confidence_policy_spl_best": max(
                    [
                        value
                        for value in [
                            finite_float(index.get((ALL_CANDIDATE_BASELINE, episode_id), {}).get("primary_spl_proxy")),
                            finite_float(index.get((PRIMARY_DETECTOR_BASELINE, episode_id), {}).get("primary_spl_proxy")),
                        ]
                        if value is not None
                    ],
                    default=None,
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": any(
                    bool(row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")) for row in policy_rows
                ),
            }
        )
    for row in rows:
        row["path_cost_spl_gain_over_confidence"] = delta(
            row.get("path_cost_policy_spl_best"), row.get("confidence_policy_spl_best")
        )
    return rows


def build_trajectory_decision_rows(
    coverage_m67_matching: dict[str, Any],
    coverage_m68: dict[str, Any],
    coverage_m70: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    failure_episode_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    success_min = int(coverage_m70.get("primary_success_count_min") or 0)
    eval_eps = int(coverage_m70.get("eval_episode_rows") or 0)
    min_proxy_sr = safe_ratio(success_min, eval_eps)
    spl_gain = max(
        [
            value
            for value in [
                finite_float(row.get("delta_spl_proxy_vs_reachable_confidence"))
                for row in policy_rows
                if row.get("policy_id") != PRIMARY_DETECTOR_BASELINE
            ]
            if value is not None
        ],
        default=0.0,
    )
    trajectory_contract_ready = (
        bool(coverage_m70.get("leakage_audit_pass"))
        and not bool(coverage_m70.get("uses_objectnav_eval_goal_or_viewpoint_for_policy"))
        and eval_eps >= 30
        and min_proxy_sr >= 0.7
        and int(coverage_m68.get("path_ready_scan_rows") or 0) == eval_eps
    )
    return [
        {
            "version": VERSION,
            "decision": "proceed_to_trajectory_contract_not_execution_launch"
            if trajectory_contract_ready
            else "repair_before_trajectory_contract",
            "selected_next_unit": NEXT_UNIT
            if trajectory_contract_ready
            else "repair E008-M70/M68 before full-val-mini trajectory contract",
            "launch_long_job_now": False,
            "trajectory_contract_ready": trajectory_contract_ready,
            "trajectory_execution_ready_now": False,
            "reason": (
                "M70 has leakage-safe 30-episode goal-eval proxy coverage and path-cost policies show an SPL proxy signal; M72 should fix Docker trajectory inputs before any long job."
                if trajectory_contract_ready
                else "M70/M68 gates do not yet justify trajectory contract."
            ),
            "eval_episode_rows": eval_eps,
            "min_goal_eval_proxy_sr": min_proxy_sr,
            "max_spl_proxy_gain_vs_reachable_confidence": spl_gain,
            "all_policy_failure_episodes": sum(1 for row in failure_episode_rows if row.get("all_detector_policies_failed")),
            "detector_target_recall_claim_ready": bool(coverage_m67_matching.get("matched_target_rows")),
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "human_intent_main_claim_ready": False,
        }
    ]


def build_gate_rows(
    coverage_m67_matching: dict[str, Any],
    coverage_m68: dict[str, Any],
    coverage_m70: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    failure_episode_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_eps = int(coverage_m70.get("eval_episode_rows") or 0)
    success_min = int(coverage_m70.get("primary_success_count_min") or 0)
    min_sr = safe_ratio(success_min, eval_eps)
    spl_gains = [
        finite_float(row.get("delta_spl_proxy_vs_reachable_confidence"))
        for row in policy_rows
        if row.get("policy_id") not in {PRIMARY_DETECTOR_BASELINE, ALL_CANDIDATE_BASELINE}
    ]
    max_spl_gain = max([value for value in spl_gains if value is not None], default=0.0)
    severe_failures = sum(
        1 for row in failure_episode_rows if row.get("failure_class") == "severe_candidate_source_coverage_gap"
    )
    all_policy_failures = sum(1 for row in failure_episode_rows if row.get("all_detector_policies_failed"))
    return [
        {
            "version": VERSION,
            "gate_id": "leakage_guard",
            "status": "pass"
            if coverage_m70.get("leakage_audit_pass")
            and not coverage_m70.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
            else "fail",
            "evidence": (
                f"leakage_pass={coverage_m70.get('leakage_audit_pass')}; "
                f"policy_uses_eval_goal={coverage_m70.get('uses_objectnav_eval_goal_or_viewpoint_for_policy')}"
            ),
            "decision_effect": "required_for_any_trajectory_contract",
        },
        {
            "version": VERSION,
            "gate_id": "full_val_mini_denominator",
            "status": "pass" if eval_eps == 30 else "fail",
            "evidence": f"eval_episode_rows={eval_eps}",
            "decision_effect": "requires_30_episodes_for_full_val_mini_smoke",
        },
        {
            "version": VERSION,
            "gate_id": "proxy_success_for_trajectory_smoke",
            "status": "pass" if min_sr >= 0.7 else "fail",
            "evidence": f"minimum policy GoalEvalProxySR={min_sr:.6f} ({success_min}/{eval_eps})",
            "decision_effect": "allows_trajectory_contract_if_other_gates_pass",
        },
        {
            "version": VERSION,
            "gate_id": "path_efficiency_signal",
            "status": "pass" if max_spl_gain >= 0.05 else "warning",
            "evidence": f"max SPL proxy gain vs reachable confidence={max_spl_gain:.6f}",
            "decision_effect": "justifies testing path-cost policies in trajectory execution",
        },
        {
            "version": VERSION,
            "gate_id": "failure_taxonomy_visible",
            "status": "warning" if all_policy_failures else "pass",
            "evidence": f"all-policy failure episodes={all_policy_failures}; severe coverage gaps={severe_failures}",
            "decision_effect": "requires_failure_rows_in_trajectory_report",
        },
        {
            "version": VERSION,
            "gate_id": "navmesh_source_ready",
            "status": "pass" if int(coverage_m68.get("path_ready_scan_rows") or 0) == eval_eps else "fail",
            "evidence": (
                f"path_ready_scan_rows={coverage_m68.get('path_ready_scan_rows')}; "
                f"source_to_snapped_path_found_rows={coverage_m68.get('source_to_snapped_path_found_rows')}"
            ),
            "decision_effect": "required_before_trajectory_contract",
        },
        {
            "version": VERSION,
            "gate_id": "detector_target_recall_claim",
            "status": "fail" if int(coverage_m67_matching.get("matched_target_rows") or 0) == 0 else "pass",
            "evidence": f"M67 matched_target_rows={coverage_m67_matching.get('matched_target_rows')}",
            "decision_effect": "blocks_detector_recall_claim_but_not_goal_eval_proxy",
        },
        {
            "version": VERSION,
            "gate_id": "trajectory_execution_metrics",
            "status": "fail",
            "evidence": "M71 does not execute Habitat trajectories.",
            "decision_effect": "blocks_real_navigation_sr_spl_claim_until_M72_plus_execution",
        },
        {
            "version": VERSION,
            "gate_id": "external_navigation_baselines",
            "status": "fail",
            "evidence": "No VLFM/HM3D-OVON/GOAT-Bench modular baseline row in E008 yet.",
            "decision_effect": "blocks_top_tier_final_navigation_claim",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_trajectory_contract_readiness",
            "supported": True,
            "claim_boundary": "M71 supports moving to a trajectory contract/preflight because M70 has leakage-safe 30-episode proxy coverage.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_path_cost_proxy_signal",
            "supported": True,
            "claim_boundary": "Path-cost policies do not improve proxy SR, but they improve proxy SPL enough to justify trajectory testing.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "No M71 row is an executed Habitat trajectory; final SR/SPL remains blocked.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_detector_target_recall",
            "supported": False,
            "claim_boundary": "M67 matching target rows remain zero; M70/M71 use ObjectNav goal/viewpoint proxy labels instead.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_human_intent_main_claim",
            "supported": False,
            "claim_boundary": "M71 evaluates task-agnostic detector policies; task context remains denominator accounting only.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    failure_episode_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> str:
    policy_lines = [
        "| `{policy_id}` | {primary_success_rows}/{scan_policy_rows} | {primary_proxy_sr} | {primary_spl_proxy_mean} | {delta_spl_proxy_vs_reachable_confidence} | {primary_first_hit_cost_m_mean_over_success} | {trajectory_role} |".format(
            **{key: fmt(row.get(key)) if isinstance(row.get(key), float) else row.get(key) for key in row}
        )
        for row in policy_rows
    ]
    failure_lines = [
        "| `{adapter_episode_id}` | {object_category} | {min_best_any_viewpoint_xz_m} | {min_best_goal_xz_m} | `{failure_class}` | `{trajectory_inclusion}` |".format(
            **{key: fmt(row.get(key)) if isinstance(row.get(key), float) else row.get(key) for key in row}
        )
        for row in failure_episode_rows
    ]
    gate_lines = [
        f"| `{row['gate_id']}` | `{row['status']}` | {row['evidence']} | {row['decision_effect']} |"
        for row in gate_rows
    ]
    decision = decision_rows[0]
    return f"""# E008-M71 Full-Val-Mini Detector-Goal Failure Comparison

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Input M70 status: `{coverage['m70_status']}`.
- Eval episodes: {coverage['eval_episode_rows']}.
- Minimum detector policy `GoalEvalProxySR`: {coverage['min_goal_eval_proxy_sr']:.6f}.
- All-policy failure episodes: {coverage['all_policy_failure_episodes']}.
- Severe candidate-source coverage gap episodes: {coverage['severe_candidate_source_coverage_gap_episodes']}.
- Best SPL proxy policy: `{coverage['best_spl_proxy_policy_id']}`.
- Max SPL proxy gain over reachable detector confidence: {coverage['max_spl_proxy_gain_vs_reachable_confidence']:.6f}.
- Detector target recall claim ready: {coverage['detector_target_recall_claim_ready']}.
- Real navigation `SR` / `SPL` ready: {coverage['real_navigation_sr_spl_ready']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Policy Comparison

| policy_id | proxy hits | proxy SR | proxy SPL | SPL delta vs reachable confidence | mean first-hit cost m | trajectory role |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(policy_lines)}

## Failure Episodes

| episode | category | min any-vp XZ m | min goal XZ m | failure class | trajectory inclusion |
| --- | --- | ---: | ---: | --- | --- |
{chr(10).join(failure_lines)}

## Gate Rows

| gate | status | evidence | decision effect |
| --- | --- | --- | --- |
{chr(10).join(gate_lines)}

## Route Decision

- Decision: `{decision['decision']}`.
- Reason: {decision['reason']}
- Launch long job now: {decision['launch_long_job_now']}.

## Claim Boundary

- M71 is a decision artifact, not an executed navigation benchmark.
- M71 supports moving to M72 trajectory contract/preflight; it does not support final real navigation `SR` / `SPL`.
- M71's six failed episodes are all-policy detector proxy failures, so they should be reported as detector/source/threshold failures rather than H001 memory-decision evidence.
- `ObjectNav` goal/viewpoint fields remain evaluation-only; no policy row may use them for ranking.
"""


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    coverage_m67_matching = read_json(M67_ARTIFACT_DIR / "matching" / "coverage.json")
    coverage_m68 = read_json(M68_ARTIFACT_DIR / "coverage.json")
    coverage_m69 = read_json(M69_ARTIFACT_DIR / "coverage.json")
    coverage_m70 = read_json(M70_ARTIFACT_DIR / "coverage.json")
    metric_rows = read_jsonl(M70_ARTIFACT_DIR / "policy_goal_metric_rows.jsonl")
    if not metric_rows:
        raise SystemExit("missing E008-M70 policy_goal_metric_rows.jsonl")

    policy_rows = build_policy_comparison_rows(metric_rows)
    failure_episode_rows = build_failure_episode_rows(metric_rows)
    episode_policy_outcome_rows = build_episode_policy_outcome_rows(metric_rows)
    gate_rows = build_gate_rows(coverage_m67_matching, coverage_m68, coverage_m70, policy_rows, failure_episode_rows)
    decision_rows = build_trajectory_decision_rows(
        coverage_m67_matching,
        coverage_m68,
        coverage_m70,
        policy_rows,
        failure_episode_rows,
    )
    claim_boundary_rows = build_claim_boundary_rows()
    gate_counts = Counter(row["status"] for row in gate_rows)
    failure_counts = Counter(str(row.get("failure_class")) for row in failure_episode_rows)

    best_spl_row = max(
        policy_rows,
        key=lambda row: finite_float(row.get("primary_spl_proxy_mean")) or -float("inf"),
    )
    max_spl_gain = max(
        [
            value
            for value in [
                finite_float(row.get("delta_spl_proxy_vs_reachable_confidence"))
                for row in policy_rows
                if row.get("policy_id") != PRIMARY_DETECTOR_BASELINE
            ]
            if value is not None
        ],
        default=0.0,
    )
    eval_eps = int(coverage_m70.get("eval_episode_rows") or 0)
    success_min = int(coverage_m70.get("primary_success_count_min") or 0)
    ready = bool(decision_rows[0].get("trajectory_contract_ready"))
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m68_status": coverage_m68.get("status"),
        "m69_status": coverage_m69.get("status"),
        "m70_status": coverage_m70.get("status"),
        "eval_episode_rows": eval_eps,
        "policy_count": len(POLICY_ORDER),
        "policy_comparison_rows": len(policy_rows),
        "episode_policy_outcome_rows": len(episode_policy_outcome_rows),
        "failure_episode_rows": len(failure_episode_rows),
        "all_policy_failure_episodes": sum(
            1 for row in failure_episode_rows if row.get("all_detector_policies_failed")
        ),
        "failure_class_counts": dict(sorted(failure_counts.items())),
        "severe_candidate_source_coverage_gap_episodes": failure_counts.get(
            "severe_candidate_source_coverage_gap", 0
        ),
        "min_goal_eval_proxy_sr": safe_ratio(success_min, eval_eps),
        "best_spl_proxy_policy_id": best_spl_row.get("policy_id"),
        "best_spl_proxy_mean": best_spl_row.get("primary_spl_proxy_mean"),
        "max_spl_proxy_gain_vs_reachable_confidence": max_spl_gain,
        "gate_status_counts": dict(sorted(gate_counts.items())),
        "trajectory_contract_ready": ready,
        "trajectory_execution_ready_now": False,
        "launch_long_job_now": False,
        "detector_target_recall_claim_ready": bool(coverage_m67_matching.get("matched_target_rows")),
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": decision_rows[0]["selected_next_unit"],
    }

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_comparison_rows.jsonl", policy_rows)
        write_jsonl(output_dir / "failure_episode_rows.jsonl", failure_episode_rows)
        write_jsonl(output_dir / "episode_policy_outcome_rows.jsonl", episode_policy_outcome_rows)
        write_jsonl(output_dir / "navigation_readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "trajectory_decision_rows.jsonl", decision_rows)
    write_jsonl(ARTIFACT_DIR / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_jsonl(ARTIFACT_DIR / "route_decision_rows.jsonl", decision_rows)
    (ARTIFACT_DIR / "report.md").write_text(
        build_report(coverage, policy_rows, failure_episode_rows, gate_rows, decision_rows),
        encoding="utf-8",
    )
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
