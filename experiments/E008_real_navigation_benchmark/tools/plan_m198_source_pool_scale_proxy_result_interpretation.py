#!/usr/bin/env python3
"""Interpret M197 source-pool scale proxy results before trajectory promotion."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
VERSION = "e008_m198_source_pool_scale_proxy_result_interpretation_v0"
ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M198_source_pool_scale_proxy_result_interpretation_v0"
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M198_source_pool_scale_proxy_result_interpretation_v0"
)
M70_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
M70_DATA_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
)
ARCHIVED_M70_ARTIFACT_DIR = (
    ROOT
    / "archive"
    / "generated_artifacts"
    / "experiments"
    / "E008_real_navigation_benchmark"
    / "artifacts"
    / "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0"
)
M197_ARTIFACT_DIR = EXP_ROOT / "artifacts" / "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0"

PROTECTED_POLICY = "detector_confidence_reachable_subset_v0"
PATH_POLICY = "path_cost_ascending_reachable_subset_v0"
SELECTED_NEXT_UNIT = "E008-M199 source-pool scale failure decomposition and candidate-generation repair decision"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("missing all candidate inputs: " + ", ".join(str(path) for path in paths))


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


def f(value: object) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def delta(a: object, b: object) -> float | None:
    aa = f(a)
    bb = f(b)
    if aa is None or bb is None:
        return None
    return aa - bb


def metric(coverage: dict[str, Any], policy_id: str, key: str) -> Any:
    return (coverage.get("policy_primary_metrics") or {}).get(policy_id, {}).get(key)


def build_policy_comparison_rows(m70: dict[str, Any], m197: dict[str, Any]) -> list[dict[str, Any]]:
    policy_ids = sorted(set((m70.get("policy_primary_metrics") or {})) | set((m197.get("policy_primary_metrics") or {})))
    rows: list[dict[str, Any]] = []
    for policy_id in policy_ids:
        baseline = (m70.get("policy_primary_metrics") or {}).get(policy_id, {})
        source_pool = (m197.get("policy_primary_metrics") or {}).get(policy_id, {})
        rows.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "baseline_artifact": "E008-M70_full_val_mini_detector_candidate_goal_evaluation_smoke_v0",
                "source_pool_artifact": "E008-M197_source_pool_scale_leakage_safe_goal_evaluation_proxy_v0",
                "baseline_primary_success_rows": baseline.get("primary_success_rows"),
                "source_pool_primary_success_rows": source_pool.get("primary_success_rows"),
                "baseline_scan_policy_rows": baseline.get("scan_policy_rows"),
                "source_pool_scan_policy_rows": source_pool.get("scan_policy_rows"),
                "baseline_primary_proxy_sr": baseline.get("primary_proxy_sr"),
                "source_pool_primary_proxy_sr": source_pool.get("primary_proxy_sr"),
                "delta_primary_proxy_sr": delta(source_pool.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")),
                "baseline_primary_spl_proxy_mean": baseline.get("primary_spl_proxy_mean"),
                "source_pool_primary_spl_proxy_mean": source_pool.get("primary_spl_proxy_mean"),
                "delta_primary_spl_proxy_mean": delta(
                    source_pool.get("primary_spl_proxy_mean"),
                    baseline.get("primary_spl_proxy_mean"),
                ),
                "baseline_hit_rank_mean": baseline.get("primary_first_hit_rank_mean_over_success"),
                "source_pool_hit_rank_mean": source_pool.get("primary_first_hit_rank_mean_over_success"),
                "delta_hit_rank_mean": delta(
                    source_pool.get("primary_first_hit_rank_mean_over_success"),
                    baseline.get("primary_first_hit_rank_mean_over_success"),
                ),
                "trajectory_promotion_support": False,
                "reason": "source_pool_proxy_sr_below_no_source_baseline"
                if delta(source_pool.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")) is not None
                and float(delta(source_pool.get("primary_proxy_sr"), baseline.get("primary_proxy_sr")) or 0.0) < 0.0
                else "source_pool_does_not_establish_strict_sr_spl_improvement",
            }
        )
    return rows


def build_decision_rows(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision": "reject_immediate_docker_trajectory_execution",
            "selected": True,
            "selected_next_unit": SELECTED_NEXT_UNIT,
            "reason": "M197 source-pool scale proxy SR is below the no-source full-val-mini detector baseline; trajectory execution would test a degraded candidate-generation route rather than a supported method.",
            "launch_long_job_now": False,
            "trajectory_execution_promoted": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "key_delta_primary_proxy_sr": coverage.get("protected_delta_primary_proxy_sr"),
            "key_delta_primary_spl_proxy_mean": coverage.get("protected_delta_primary_spl_proxy_mean"),
        },
        {
            "version": VERSION,
            "decision": "defer_path_cost_trajectory_even_if_proxy_spl_higher",
            "selected": False,
            "selected_next_unit": "later trajectory only after source-pool SR recovers against protected baseline",
            "reason": "Path-cost source-pool proxy SPL is higher than detector confidence but primary proxy SR remains 0.5667 vs the no-source baseline 0.8.",
            "launch_long_job_now": False,
            "trajectory_execution_promoted": False,
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "supported_negative_scale_proxy_boundary",
            "supported": True,
            "claim_boundary": "M198 supports a negative boundary: source-pool scale candidate generation is not ready for trajectory promotion because it loses proxy SR to the no-source detector baseline.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_source_pool_navigation_improvement",
            "supported": False,
            "claim_boundary": "M198 does not support claiming source-pool navigation improvement, even though path-cost sorting improves proxy SPL among recovered rows.",
        },
        {
            "version": VERSION,
            "claim_id": "unsupported_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "M198 does not execute Habitat trajectories and blocks immediate Docker trajectory launch.",
        },
    ]


def build_report(coverage: dict[str, Any], comparison_rows: list[dict[str, Any]]) -> str:
    lines = []
    for row in comparison_rows:
        lines.append(
            "| {policy_id} | {baseline_primary_success_rows}/{baseline_scan_policy_rows} | "
            "{source_pool_primary_success_rows}/{source_pool_scan_policy_rows} | "
            "{baseline_primary_proxy_sr} | {source_pool_primary_proxy_sr} | {delta_primary_proxy_sr} | "
            "{baseline_primary_spl_proxy_mean} | {source_pool_primary_spl_proxy_mean} | {delta_primary_spl_proxy_mean} |".format(
                **{key: row.get(key) for key in row}
            )
        )
    return f"""# E008-M198 Source-Pool Scale Proxy Result Interpretation

Generated: {coverage['generated_at']}

## Facts

- Status: `{coverage['status']}`.
- M197 status: `{coverage['m197_status']}`.
- No-source baseline: `E008-M70` full-val-mini detector candidate goal-evaluation proxy.
- Protected policy: `{coverage['protected_policy_id']}`.
- Protected baseline proxy `SR`: {coverage['protected_baseline_primary_proxy_sr']}.
- Source-pool protected proxy `SR`: {coverage['protected_source_pool_primary_proxy_sr']}.
- Delta proxy `SR`: {coverage['protected_delta_primary_proxy_sr']}.
- Protected baseline proxy `SPL`: {coverage['protected_baseline_primary_spl_proxy_mean']}.
- Source-pool protected proxy `SPL`: {coverage['protected_source_pool_primary_spl_proxy_mean']}.
- Delta proxy `SPL`: {coverage['protected_delta_primary_spl_proxy_mean']}.
- Path-cost source-pool proxy `SPL`: {coverage['path_policy_source_pool_primary_spl_proxy_mean']}.
- Trajectory execution promoted: {coverage['trajectory_execution_promoted']}.
- Selected next unit: {coverage['selected_next_unit']}.

## Comparison

| policy_id | baseline hits | source-pool hits | baseline SR | source-pool SR | delta SR | baseline SPL | source-pool SPL | delta SPL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(lines)}

## Interpretation

M197 is leakage-safe and informative, but it is a negative scale gate. Source-pool acquisition produced useful candidates for 17 / 30 rows, while the existing no-source detector baseline recovers 24 / 30 rows on the same `HM3D ObjectNav val_mini` denominator. The path-cost policy improves proxy `SPL` among recovered rows, but the `SR` deficit is too large for trajectory promotion.
"""


def main() -> None:
    m70 = read_json(
        first_existing(
            [
                M70_ARTIFACT_DIR / "coverage.json",
                M70_DATA_DIR / "coverage.json",
                ARCHIVED_M70_ARTIFACT_DIR / "coverage.json",
            ]
        )
    )
    m197 = read_json(M197_ARTIFACT_DIR / "coverage.json")
    if not m70:
        raise SystemExit("missing M70 coverage.json")
    if not m197:
        raise SystemExit("missing M197 coverage.json")

    comparison_rows = build_policy_comparison_rows(m70, m197)
    protected_delta_sr = delta(
        metric(m197, PROTECTED_POLICY, "primary_proxy_sr"),
        metric(m70, PROTECTED_POLICY, "primary_proxy_sr"),
    )
    protected_delta_spl = delta(
        metric(m197, PROTECTED_POLICY, "primary_spl_proxy_mean"),
        metric(m70, PROTECTED_POLICY, "primary_spl_proxy_mean"),
    )
    trajectory_promoted = bool(
        protected_delta_sr is not None
        and protected_delta_spl is not None
        and protected_delta_sr >= 0.0
        and protected_delta_spl > 0.0
    )

    coverage = {
        "version": VERSION,
        "status": "e008_m198_source_pool_scale_proxy_result_interpretation_ready",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m70_status": m70.get("status"),
        "m197_status": m197.get("status"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "protected_policy_id": PROTECTED_POLICY,
        "path_policy_id": PATH_POLICY,
        "protected_baseline_primary_proxy_sr": metric(m70, PROTECTED_POLICY, "primary_proxy_sr"),
        "protected_source_pool_primary_proxy_sr": metric(m197, PROTECTED_POLICY, "primary_proxy_sr"),
        "protected_delta_primary_proxy_sr": protected_delta_sr,
        "protected_baseline_primary_spl_proxy_mean": metric(m70, PROTECTED_POLICY, "primary_spl_proxy_mean"),
        "protected_source_pool_primary_spl_proxy_mean": metric(m197, PROTECTED_POLICY, "primary_spl_proxy_mean"),
        "protected_delta_primary_spl_proxy_mean": protected_delta_spl,
        "path_policy_source_pool_primary_proxy_sr": metric(m197, PATH_POLICY, "primary_proxy_sr"),
        "path_policy_source_pool_primary_spl_proxy_mean": metric(m197, PATH_POLICY, "primary_spl_proxy_mean"),
        "trajectory_execution_promoted": trajectory_promoted,
        "launch_long_job_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "method_claim_ready": False,
        "selected_next_unit": SELECTED_NEXT_UNIT if not trajectory_promoted else "E008-M199 Docker trajectory execution contract",
    }
    decision_rows = build_decision_rows(coverage)
    claim_boundary_rows = build_claim_boundary_rows()

    for output_dir in (ARTIFACT_DIR, DATA_OUT_DIR):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "policy_comparison_rows.jsonl", comparison_rows)
        write_jsonl(output_dir / "decision_rows.jsonl", decision_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_boundary_rows)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, comparison_rows))
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
