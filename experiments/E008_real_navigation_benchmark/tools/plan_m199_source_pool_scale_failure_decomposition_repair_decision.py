#!/usr/bin/env python3
"""Decompose M198 source-pool scale failure and fix the next repair decision."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m199_source_pool_scale_failure_decomposition_repair_decision_v0"
READY_STATUS = "e008_m199_source_pool_scale_failure_decomposition_repair_decision_ready"

ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M199_source_pool_scale_failure_decomposition_repair_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M199_source_pool_scale_failure_decomposition_repair_decision_v0"
)

M70_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
)
M195_DIR = EXP_ROOT / "artifacts" / "E008-M195_source_pool_scale_candidate_navmesh_source_readiness_validation_v0"
M197_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"
M198_DIR = EXP_ROOT / "artifacts" / "E008-M198_source_pool_scale_proxy_result_interpretation_v0"

PROTECTED_POLICY = "detector_confidence_reachable_subset_v0"
NEXT_UNIT = "E008-M200 additive source-pool candidate-union repair contract"
SELECTED_REPAIR = "additive_union_candidate_pool_with_source_gap_guard_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    path.write_text(
        "".join(json.dumps(sanitize_json(row), sort_keys=True, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def delta(left: object, right: object) -> float | None:
    left_f = finite_float(left)
    right_f = finite_float(right)
    if left_f is None or right_f is None:
        return None
    return left_f - right_f


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    if value is None:
        return "null"
    return str(value)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def index_scan_policy(rows: list[dict[str, Any]], metric_scope: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("policy_id") != PROTECTED_POLICY:
            continue
        if row.get("metric_scope") != metric_scope:
            continue
        out[str(row.get("adapter_episode_id"))] = row
    return out


def classify_episode(baseline: dict[str, Any], source_pool: dict[str, Any], boundary: dict[str, Any]) -> tuple[str, str]:
    baseline_hit = bool(baseline.get("primary_hit"))
    source_pool_hit = bool(source_pool.get("primary_hit"))
    source_gap = bool(boundary.get("source_gap"))
    source_best = finite_float(source_pool.get("best_any_viewpoint_xz_m"))
    source_candidate_rows = int(source_pool.get("candidate_rows") or 0)
    baseline_best = finite_float(baseline.get("best_any_viewpoint_xz_m"))

    if baseline_hit and source_pool_hit:
        comparison_class = "shared_success"
        spl_delta = delta(source_pool.get("primary_spl_proxy"), baseline.get("primary_spl_proxy")) or 0.0
        if spl_delta < -1e-9:
            failure_type = "shared_success_source_pool_cost_regression"
        elif spl_delta > 1e-9:
            failure_type = "shared_success_source_pool_cost_gain"
        else:
            failure_type = "shared_success_tie"
        return comparison_class, failure_type

    if baseline_hit and not source_pool_hit:
        comparison_class = "source_pool_lost_baseline_success"
        if source_gap or source_candidate_rows == 0:
            failure_type = "lost_success_source_gap_no_detector_candidate"
        elif source_best is not None and source_best <= 1.5:
            failure_type = "lost_success_near_threshold_or_localization_margin"
        else:
            failure_type = "lost_success_candidate_coverage_regression"
        return comparison_class, failure_type

    if source_pool_hit and not baseline_hit:
        return "source_pool_unique_recovery", "source_pool_adds_useful_candidate"

    if source_gap or source_candidate_rows == 0:
        return "shared_failure", "shared_failure_source_gap_no_detector_candidate"
    if source_best is not None and source_best <= 1.5:
        return "shared_failure", "shared_failure_near_threshold_or_stop_region_margin"
    if baseline_best is not None and source_best is not None and source_best > baseline_best:
        return "shared_failure", "shared_failure_candidate_coverage_not_improved"
    return "shared_failure", "shared_failure_detector_or_target_coverage_gap"


def build_episode_comparison_rows(
    baseline_rows: dict[str, dict[str, Any]],
    source_pool_rows: dict[str, dict[str, Any]],
    boundary_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    episode_ids = sorted(set(baseline_rows) | set(source_pool_rows) | set(boundary_rows))
    for episode_id in episode_ids:
        baseline = baseline_rows.get(episode_id, {})
        source_pool = source_pool_rows.get(episode_id, {})
        boundary = boundary_rows.get(episode_id, {})
        comparison_class, failure_type = classify_episode(baseline, source_pool, boundary)
        out.append(
            {
                "version": VERSION,
                "adapter_episode_id": episode_id,
                "scan_id": source_pool.get("scan_id") or baseline.get("scan_id") or boundary.get("scan_id"),
                "scene_key": source_pool.get("scene_key") or baseline.get("scene_key") or boundary.get("scene_key"),
                "object_category": source_pool.get("object_category")
                or baseline.get("object_category")
                or boundary.get("object_category"),
                "policy_id": PROTECTED_POLICY,
                "comparison_class": comparison_class,
                "failure_type": failure_type,
                "baseline_primary_hit": bool(baseline.get("primary_hit")),
                "source_pool_primary_hit": bool(source_pool.get("primary_hit")),
                "baseline_primary_first_hit_rank": baseline.get("primary_first_hit_rank"),
                "source_pool_primary_first_hit_rank": source_pool.get("primary_first_hit_rank"),
                "baseline_primary_spl_proxy": baseline.get("primary_spl_proxy"),
                "source_pool_primary_spl_proxy": source_pool.get("primary_spl_proxy"),
                "delta_primary_spl_proxy": delta(source_pool.get("primary_spl_proxy"), baseline.get("primary_spl_proxy")),
                "baseline_best_any_viewpoint_xz_m": baseline.get("best_any_viewpoint_xz_m"),
                "source_pool_best_any_viewpoint_xz_m": source_pool.get("best_any_viewpoint_xz_m"),
                "delta_best_any_viewpoint_xz_m": delta(
                    source_pool.get("best_any_viewpoint_xz_m"),
                    baseline.get("best_any_viewpoint_xz_m"),
                ),
                "baseline_candidate_rows": baseline.get("candidate_rows"),
                "source_pool_candidate_rows": source_pool.get("candidate_rows"),
                "source_boundary_status": boundary.get("source_boundary_status"),
                "source_ready_after_m195": bool(boundary.get("source_ready")),
                "source_gap_after_m195": bool(boundary.get("source_gap")),
                "policy_input_allowed": source_pool.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") is False
                and baseline.get("uses_objectnav_eval_goal_or_viewpoint_for_policy") is False,
                "claim_boundary": "M199 compares M70 and M197 only after both visit orders are frozen; ObjectNav targets remain evaluation-only labels.",
            }
        )
    return out


def build_failure_decomposition_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(episode_rows)
    rows: list[dict[str, Any]] = []
    for (comparison_class, failure_type), count in sorted(
        Counter((row["comparison_class"], row["failure_type"]) for row in episode_rows).items()
    ):
        subset = [row for row in episode_rows if row["comparison_class"] == comparison_class and row["failure_type"] == failure_type]
        source_gap_count = sum(1 for row in subset if row.get("source_gap_after_m195"))
        source_ready_count = sum(1 for row in subset if row.get("source_ready_after_m195"))
        object_counts = Counter(str(row.get("object_category")) for row in subset)
        rows.append(
            {
                "version": VERSION,
                "comparison_class": comparison_class,
                "failure_type": failure_type,
                "row_count": count,
                "row_fraction": count / total if total else None,
                "source_gap_rows": source_gap_count,
                "source_ready_rows": source_ready_count,
                "object_category_counts": dict(sorted(object_counts.items())),
                "repair_implication": repair_implication(failure_type),
            }
        )
    return rows


def repair_implication(failure_type: str) -> str:
    if failure_type == "lost_success_source_gap_no_detector_candidate":
        return "do_not_replace_no_source_candidate_pool; add source-pool candidates only when source evidence exists"
    if failure_type == "lost_success_near_threshold_or_localization_margin":
        return "preserve baseline candidates and add localization-margin/stop-region validation before trajectory promotion"
    if failure_type == "source_pool_adds_useful_candidate":
        return "keep source-pool expansion as additive evidence, not as a replacement policy"
    if failure_type == "shared_failure_near_threshold_or_stop_region_margin":
        return "inspect stop-region tolerance and viewpoint coverage before claiming detector-source robustness"
    if failure_type == "shared_success_source_pool_cost_regression":
        return "protect detector-confidence order unless source-pool candidate has strict recovery or cost evidence"
    return "record as diagnostic boundary before any trajectory execution"


def build_repair_decision_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "select_additive_union_candidate_pool_with_source_gap_guard",
            "selected": True,
            "selected_repair": SELECTED_REPAIR,
            "selected_next_unit": NEXT_UNIT,
            "reason": "Source-pool scale adds 2 unique recoveries but loses 9 no-source baseline successes; 7 losses are source-gap/no-detector-candidate rows, so source-pool must be additive rather than replacement.",
            "required_baseline_protection": PROTECTED_POLICY,
            "posthoc_threshold_change_allowed": False,
            "denominator_change_allowed": False,
            "trajectory_execution_promoted": False,
            "launch_long_job_now": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "key_lost_baseline_success_rows": coverage["source_pool_lost_baseline_success_rows"],
            "key_unique_recovery_rows": coverage["source_pool_unique_recovery_rows"],
        },
        {
            "version": VERSION,
            "decision": "reject_source_pool_replacement_policy",
            "selected": False,
            "reason": "Replacement-style source-pool candidate generation is less reliable than the no-source detector baseline on the same 30-row denominator.",
            "trajectory_execution_promoted": False,
            "launch_long_job_now": False,
        },
        {
            "version": VERSION,
            "decision": "reject_immediate_threshold_relaxation",
            "selected": False,
            "reason": "Near-threshold rows are useful diagnostics, but relaxing the primary 1.0m viewpoint metric after observing failures would weaken the leakage-safe benchmark contract.",
            "posthoc_threshold_change_allowed": False,
            "launch_long_job_now": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_source_pool_failure_diagnosis",
            "supported": True,
            "claim_boundary": "M199 supports the diagnosis that source-pool scale candidate generation is useful only as additive evidence; as a replacement it loses too many no-source detector successes.",
        },
        {
            "version": VERSION,
            "claim_id": "supported_next_repair_contract",
            "supported": True,
            "claim_boundary": "M199 supports moving to an additive union candidate-pool contract with source-gap guard and protected detector-confidence baseline.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_pool_navigation_improvement",
            "supported": False,
            "claim_boundary": "M199 does not support a positive source-pool navigation-improvement claim or Docker trajectory execution.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_final_rgbd_open_vocab_robustness",
            "supported": False,
            "claim_boundary": "M199 is a failure decomposition and repair-decision gate; final RGB-D/open-vocabulary robustness remains blocked until the additive repair improves against protected baselines and trajectory execution passes.",
        },
    ]


def build_report(
    coverage: dict[str, Any],
    failure_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> str:
    failure_columns = [
        "comparison_class",
        "failure_type",
        "row_count",
        "source_gap_rows",
        "source_ready_rows",
        "repair_implication",
    ]
    repair_columns = [
        "decision",
        "selected",
        "selected_repair",
        "selected_next_unit",
        "trajectory_execution_promoted",
        "reason",
    ]
    return f"""# E008-M199 Source-Pool Scale Failure Decomposition

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- Denominator rows: {coverage['denominator_rows']}.
- Protected policy: `{coverage['protected_policy_id']}`.
- No-source baseline primary success rows: {coverage['baseline_primary_success_rows']}.
- Source-pool primary success rows: {coverage['source_pool_primary_success_rows']}.
- Shared success rows: {coverage['shared_success_rows']}.
- Source-pool unique recovery rows: {coverage['source_pool_unique_recovery_rows']}.
- Source-pool lost baseline success rows: {coverage['source_pool_lost_baseline_success_rows']}.
- Lost baseline success rows caused by source-gap/no-detector-candidate: {coverage['lost_baseline_source_gap_no_detector_candidate_rows']}.
- Shared failure rows: {coverage['shared_failure_rows']}.
- Selected repair: `{coverage['selected_repair']}`.
- Selected next unit: {coverage['selected_next_unit']}.
- Trajectory execution promoted: {coverage['trajectory_execution_promoted']}.

## Failure Decomposition

{markdown_table(failure_rows, failure_columns)}

## Repair Decision

{markdown_table(repair_rows, repair_columns)}

## Interpretation

M199 confirms that the source-pool branch should not replace the no-source detector candidate pool. The branch adds useful candidates in 2 rows, but it loses 9 baseline successes, including 7 `tv_monitor` source-gap rows where the source-pool detector path produced no usable candidate. The principled next method form is therefore an additive union: preserve the protected detector-confidence baseline, add source-pool candidates only as extra evidence, keep the 30-row denominator and primary metric fixed, and block trajectory execution until the repaired candidate pool beats the protected no-source baseline in leakage-safe proxy evaluation.
"""


def main() -> None:
    m70_coverage = read_json(M70_DATA_DIR / "coverage.json")
    m195_coverage = read_json(M195_DIR / "coverage.json")
    m197_coverage = read_json(M197_DIR / "coverage.json")
    m198_coverage = read_json(M198_DIR / "coverage.json")
    if not m70_coverage:
        raise SystemExit(f"missing {M70_DATA_DIR / 'coverage.json'}")
    if not m195_coverage:
        raise SystemExit(f"missing {M195_DIR / 'coverage.json'}")
    if not m197_coverage:
        raise SystemExit(f"missing {M197_DIR / 'coverage.json'}")
    if not m198_coverage:
        raise SystemExit(f"missing {M198_DIR / 'coverage.json'}")

    baseline_rows = index_scan_policy(
        read_jsonl(M70_DATA_DIR / "policy_goal_metric_rows.jsonl"),
        "scan_policy",
    )
    source_pool_rows = index_scan_policy(
        read_jsonl(M197_DIR / "source_pool_scale_scan_goal_metric_rows.jsonl"),
        "source_pool_scale_scan_policy_goal_eval",
    )
    boundary_rows = {
        str(row.get("adapter_episode_id")): row
        for row in read_jsonl(M195_DIR / "scan_source_boundary_rows.jsonl")
    }
    if not baseline_rows:
        raise SystemExit("missing M70 protected baseline scan-policy rows")
    if not source_pool_rows:
        raise SystemExit("missing M197 protected source-pool scan-policy rows")
    if not boundary_rows:
        raise SystemExit("missing M195 scan source boundary rows")

    episode_rows = build_episode_comparison_rows(baseline_rows, source_pool_rows, boundary_rows)
    failure_rows = build_failure_decomposition_rows(episode_rows)
    class_counts = Counter(row["comparison_class"] for row in episode_rows)
    failure_counts = Counter(row["failure_type"] for row in episode_rows)

    coverage = {
        "version": VERSION,
        "status": READY_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m70_status": m70_coverage.get("status"),
        "m195_status": m195_coverage.get("status"),
        "m197_status": m197_coverage.get("status"),
        "m198_status": m198_coverage.get("status"),
        "protected_policy_id": PROTECTED_POLICY,
        "denominator_rows": len(episode_rows),
        "baseline_primary_success_rows": class_counts["shared_success"] + class_counts["source_pool_lost_baseline_success"],
        "source_pool_primary_success_rows": class_counts["shared_success"] + class_counts["source_pool_unique_recovery"],
        "shared_success_rows": class_counts["shared_success"],
        "source_pool_unique_recovery_rows": class_counts["source_pool_unique_recovery"],
        "source_pool_lost_baseline_success_rows": class_counts["source_pool_lost_baseline_success"],
        "shared_failure_rows": class_counts["shared_failure"],
        "lost_baseline_source_gap_no_detector_candidate_rows": failure_counts[
            "lost_success_source_gap_no_detector_candidate"
        ],
        "lost_baseline_near_threshold_or_localization_margin_rows": failure_counts[
            "lost_success_near_threshold_or_localization_margin"
        ],
        "source_ready_lost_baseline_success_rows": sum(
            1
            for row in episode_rows
            if row["comparison_class"] == "source_pool_lost_baseline_success"
            and row.get("source_ready_after_m195")
        ),
        "source_gap_lost_baseline_success_rows": sum(
            1
            for row in episode_rows
            if row["comparison_class"] == "source_pool_lost_baseline_success"
            and row.get("source_gap_after_m195")
        ),
        "selected_repair": SELECTED_REPAIR,
        "selected_next_unit": NEXT_UNIT,
        "method_claim_ready": False,
        "trajectory_execution_promoted": False,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "posthoc_threshold_change_allowed": False,
        "denominator_change_allowed": False,
    }
    repair_rows = build_repair_decision_rows(coverage)
    claim_rows = build_claim_boundary_rows()

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "episode_comparison_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "failure_decomposition_rows.jsonl", failure_rows)
        write_jsonl(output_dir / "repair_decision_rows.jsonl", repair_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, failure_rows, repair_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
