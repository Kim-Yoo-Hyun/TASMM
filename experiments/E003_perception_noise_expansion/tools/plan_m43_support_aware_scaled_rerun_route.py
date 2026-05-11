#!/usr/bin/env python3
"""Plan E003-M43 support-aware scaled rerun route gate."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M40_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M40_temporal_spatial_support_runner_smoke_v0"
DEFAULT_M42_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M42_support_aware_selection_runner_smoke_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M43_support_aware_scaled_rerun_route_gate_v0"
M43_VERSION = "e003_m43_support_aware_scaled_rerun_route_gate_v0"
SUPPORT_AWARE_SCORE_MODE = "confidence_sqrt_depth_support_temporal_v0"
SUPPORT_BASELINE_SCORE_MODE = "confidence_sqrt_depth"
SUPPORT_EVIDENCE_POLICY = "temporal_spatial_support_evidence_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command_payload(argv: list[str]) -> dict[str, Any]:
    return {
        "argv": argv,
        "shell": shlex.join(argv),
    }


def stable_candidate_key(row: dict[str, Any]) -> str:
    centroid = row.get("centroid_world_m") or []
    centroid_key = ",".join(f"{float(value):.6f}" for value in centroid[:3])
    frame_ids = ",".join(str(value) for value in row.get("frame_ids", []))
    bbox_items = []
    bbox_by_frame = row.get("bbox_2d") or {}
    for frame_id in sorted(bbox_by_frame):
        bbox = bbox_by_frame.get(frame_id) or []
        bbox_items.append(f"{frame_id}:{','.join(f'{float(value):.3f}' for value in bbox)}")
    return "::".join(
        [
            str(row.get("scan_id")),
            frame_ids,
            str(row.get("raw_frame_local_index")),
            str(row.get("label_canonical")),
            centroid_key,
            "|".join(bbox_items),
        ]
    )


def metric_value(coverage: dict[str, Any], key: str, default: Any = None) -> Any:
    matching = coverage.get("matching_coverage") or {}
    if key in matching:
        return matching.get(key)
    return coverage.get(key, default)


def compare_metrics(m40: dict[str, Any], m42: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "prediction_rows",
        "matched_proposal_rows",
        "matched_target_rows",
        "false_positive_proposal_rows",
        "proposal_precision_smoke",
        "scan_target_recall_smoke",
        "label_overlap_target_recall_smoke",
    ]
    rows = []
    for key in keys:
        base = metric_value(m40, key)
        target = metric_value(m42, key)
        delta = None
        if isinstance(base, (int, float)) and isinstance(target, (int, float)):
            delta = target - base
        rows.append(
            {
                "metric": key,
                "m40": base,
                "m42": target,
                "delta_m42_minus_m40": delta,
            }
        )
    return {
        "rows": rows,
        "matched_proposal_delta": metric_value(m42, "matched_proposal_rows", 0)
        - metric_value(m40, "matched_proposal_rows", 0),
        "false_positive_delta": metric_value(m42, "false_positive_proposal_rows", 0)
        - metric_value(m40, "false_positive_proposal_rows", 0),
        "precision_delta": metric_value(m42, "proposal_precision_smoke", 0.0)
        - metric_value(m40, "proposal_precision_smoke", 0.0),
    }


def compare_selected_rows(m40_rows: list[dict[str, Any]], m42_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m40_by_key = {stable_candidate_key(row): row for row in m40_rows}
    m42_by_key = {stable_candidate_key(row): row for row in m42_rows}
    common_keys = set(m40_by_key) & set(m42_by_key)
    union_keys = set(m40_by_key) | set(m42_by_key)

    score_deltas = []
    pre_cap_rank_changed = 0
    group_rank_changed = 0
    changed_examples = []
    for key in sorted(common_keys):
        m40_row = m40_by_key[key]
        m42_row = m42_by_key[key]
        m40_score = float(m40_row.get("selection_score", 0.0) or 0.0)
        m42_score = float(m42_row.get("selection_score", 0.0) or 0.0)
        delta = m42_score - m40_score
        if abs(delta) > 1e-10:
            score_deltas.append(delta)
        if m40_row.get("pre_cap_rank") != m42_row.get("pre_cap_rank"):
            pre_cap_rank_changed += 1
        if m40_row.get("pre_cap_group_rank") != m42_row.get("pre_cap_group_rank"):
            group_rank_changed += 1
        if len(changed_examples) < 8 and (
            abs(delta) > 1e-10
            or m40_row.get("pre_cap_rank") != m42_row.get("pre_cap_rank")
            or m40_row.get("pre_cap_group_rank") != m42_row.get("pre_cap_group_rank")
        ):
            changed_examples.append(
                {
                    "label_canonical": m42_row.get("label_canonical"),
                    "m40_pre_cap_rank": m40_row.get("pre_cap_rank"),
                    "m42_pre_cap_rank": m42_row.get("pre_cap_rank"),
                    "m40_selection_score": m40_score,
                    "m42_selection_score": m42_score,
                    "selection_score_delta": delta,
                    "support_spatial_neighbor_count_r1p0m": m42_row.get(
                        "support_spatial_neighbor_count_r1p0m"
                    ),
                    "support_temporal_neighbor_frame_count_r2p0m": m42_row.get(
                        "support_temporal_neighbor_frame_count_r2p0m"
                    ),
                }
            )

    only_m40 = [m40_by_key[key] for key in sorted(set(m40_by_key) - set(m42_by_key))]
    only_m42 = [m42_by_key[key] for key in sorted(set(m42_by_key) - set(m40_by_key))]
    return {
        "m40_selected_rows": len(m40_rows),
        "m42_selected_rows": len(m42_rows),
        "common_selected_rows": len(common_keys),
        "m40_only_selected_rows": len(only_m40),
        "m42_only_selected_rows": len(only_m42),
        "selected_set_jaccard": (len(common_keys) / len(union_keys)) if union_keys else None,
        "selection_symmetric_difference_rows": len(only_m40) + len(only_m42),
        "selection_score_changed_common_rows": len(score_deltas),
        "selection_score_delta_mean": mean(score_deltas) if score_deltas else 0.0,
        "selection_score_delta_max": max(score_deltas) if score_deltas else 0.0,
        "selection_score_delta_min": min(score_deltas) if score_deltas else 0.0,
        "pre_cap_rank_changed_common_rows": pre_cap_rank_changed,
        "pre_cap_group_rank_changed_common_rows": group_rank_changed,
        "m40_only_examples": [
            {
                "label_canonical": row.get("label_canonical"),
                "pre_cap_rank": row.get("pre_cap_rank"),
                "selection_score": row.get("selection_score"),
            }
            for row in only_m40[:5]
        ],
        "m42_only_examples": [
            {
                "label_canonical": row.get("label_canonical"),
                "pre_cap_rank": row.get("pre_cap_rank"),
                "selection_score": row.get("selection_score"),
                "support_spatial_neighbor_count_r1p0m": row.get("support_spatial_neighbor_count_r1p0m"),
                "support_temporal_neighbor_frame_count_r2p0m": row.get(
                    "support_temporal_neighbor_frame_count_r2p0m"
                ),
            }
            for row in only_m42[:5]
        ],
        "changed_examples": changed_examples,
    }


def support_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return {
        "rows_with_support_policy": sum(
            1 for row in rows if row.get("support_evidence_policy") == SUPPORT_EVIDENCE_POLICY
        ),
        "rows_with_spatial_support_r1p0m": sum(
            1 for row in rows if int(row.get("support_spatial_neighbor_count_r1p0m", 0) or 0) > 0
        ),
        "rows_with_temporal_support_r2p0m": sum(
            1 for row in rows if int(row.get("support_temporal_neighbor_frame_count_r2p0m", 0) or 0) > 0
        ),
        "max_spatial_support_r1p0m": max(
            int(row.get("support_spatial_neighbor_count_r1p0m", 0) or 0) for row in rows
        ),
        "max_temporal_support_r2p0m": max(
            int(row.get("support_temporal_neighbor_frame_count_r2p0m", 0) or 0) for row in rows
        ),
    }


def existing_replay_available(*artifact_dirs: Path) -> bool:
    candidate_names = [
        "pre_cap_candidate_pool.jsonl",
        "pre_cap_candidates.jsonl",
        "candidate_pool.jsonl",
        "container_output/pre_cap_candidate_pool.jsonl",
        "container_output/pre_cap_candidates.jsonl",
    ]
    return any((artifact_dir / name).exists() for artifact_dir in artifact_dirs for name in candidate_names)


def build_route_decision(
    *,
    m33: dict[str, Any],
    m40: dict[str, Any],
    m42: dict[str, Any],
    metric_comparison: dict[str, Any],
    row_comparison: dict[str, Any],
    replay_available: bool,
) -> dict[str, Any]:
    short_smoke_valid = (
        m40.get("status") == "temporal_spatial_support_runner_smoke_ready"
        and m42.get("status") == "support_aware_selection_runner_smoke_ready"
        and int(m42.get("validator_error_rows", 0) or 0) == 0
        and int(m42.get("validator_warning_rows", 0) or 0) == 0
        and bool((m42.get("support_evidence") or {}).get("ready"))
    )
    ranking_sensitive = (
        int(row_comparison["selection_symmetric_difference_rows"]) > 0
        or int(row_comparison["pre_cap_rank_changed_common_rows"]) > 0
        or int(row_comparison["selection_score_changed_common_rows"]) > 0
    )
    quality_positive = (
        int(metric_comparison["matched_proposal_delta"]) > 0
        or int(metric_comparison["false_positive_delta"]) < 0
        or float(metric_comparison["precision_delta"]) > 0.0
    )
    m33_scaled_ready = m33.get("status") == "scaled_pre_cap_policy_docker_rerun_ready"

    selected_route = "pre_cap_candidate_pool_export_then_offline_replay_v0"
    immediate_long_rerun_recommended = False
    full_scaled_run_after_export_recommended = True
    if not short_smoke_valid:
        selected_route = "fix_support_aware_smoke_before_scaled_route"
        full_scaled_run_after_export_recommended = False
    elif replay_available and ranking_sensitive:
        selected_route = "offline_replay_existing_candidate_pool_v0"
        full_scaled_run_after_export_recommended = False

    return {
        "m43_version": M43_VERSION,
        "selected_route": selected_route,
        "short_smoke_valid": short_smoke_valid,
        "ranking_sensitive": ranking_sensitive,
        "quality_positive_in_short_smoke": quality_positive,
        "existing_candidate_pool_replay_available": replay_available,
        "m33_scaled_baseline_ready": m33_scaled_ready,
        "immediate_support_aware_long_rerun_recommended": immediate_long_rerun_recommended,
        "full_scaled_run_after_candidate_pool_export_recommended": full_scaled_run_after_export_recommended,
        "runner_edit_required_before_next_scaled_run": selected_route
        == "pre_cap_candidate_pool_export_then_offline_replay_v0",
        "route_options": [
            {
                "route": "immediate_scaled_support_aware_docker_rerun_v0",
                "status": "not_selected",
                "reason": (
                    "M42 has neutral quality delta vs M40, and a support-aware-only scaled rerun would not "
                    "preserve a replayable candidate pool for ablations."
                ),
            },
            {
                "route": "offline_replay_existing_candidate_pool_v0",
                "status": "blocked" if not replay_available else "available",
                "reason": (
                    "Existing M40/M42 artifacts store final selected proposals and summaries, not the cleaned "
                    "pre-consolidation candidate pool needed to compare score modes without rerunning the detector."
                ),
            },
            {
                "route": "pre_cap_candidate_pool_export_then_offline_replay_v0",
                "status": "selected" if selected_route == "pre_cap_candidate_pool_export_then_offline_replay_v0" else "not_selected",
                "reason": (
                    "One small runner edit can export the support-instrumented candidate pool, then offline replay can "
                    "compare confidence, sqrt-depth, support-aware, and redesigned scores using the same detector output."
                ),
            },
            {
                "route": "score_redesign_before_any_scaled_evidence_v0",
                "status": "deferred",
                "reason": (
                    "Score redesign should be tested by replaying a candidate pool; redesigning from final selected rows "
                    "would overfit to a tiny smoke artifact."
                ),
            },
        ],
        "next_recommended_unit": (
            "E003-M44 pre-cap candidate-pool export and offline replay harness smoke"
            if selected_route == "pre_cap_candidate_pool_export_then_offline_replay_v0"
            else "E003-M44 offline replay or smoke fix"
        ),
    }


def build_candidate_pool_contract() -> dict[str, Any]:
    return {
        "contract_id": "pre_cap_candidate_pool_export_for_offline_replay_v0",
        "purpose": "Make support-aware scoring ablations replayable without repeated detector inference.",
        "runner_new_args": [
            {
                "arg": "--export-pre-cap-candidate-pool",
                "type": "flag",
                "default": False,
            },
            {
                "arg": "--pre-cap-candidate-pool-output",
                "default": "/outputs/pre_cap_candidate_pool.jsonl",
            },
        ],
        "export_stage": "after_prompt_label_cleanup_and_support_evidence_before_spatial_consolidation_and_caps",
        "required_fields": [
            "scan_id",
            "frame_ids",
            "label_canonical",
            "centroid_world_m",
            "confidence",
            "depth_valid_pixel_count",
            "raw_candidate_uid",
            "support_evidence_policy",
            "support_spatial_neighbor_count_r1p0m",
            "support_temporal_neighbor_frame_count_r2p0m",
        ],
        "offline_replay_score_modes": [
            "confidence",
            SUPPORT_BASELINE_SCORE_MODE,
            SUPPORT_AWARE_SCORE_MODE,
        ],
        "reproduction_check": (
            "Offline replay with the runner score mode must reproduce the runner selected stable-candidate set "
            "on the M44 short smoke before any scaled export run."
        ),
        "scaled_use": (
            "After M44 smoke passes, run one 8-scan detector job that exports the candidate pool; compare score "
            "modes offline and use the same rows for support score redesign if needed."
        ),
    }


def build_verification_plan(out_dir: Path) -> dict[str, Any]:
    script_rel = Path(__file__).resolve().relative_to(REPO_ROOT)
    py_compile = [
        "python",
        "-m",
        "py_compile",
        str(script_rel),
    ]
    run_gate = [
        "python",
        str(script_rel),
        "--out-dir",
        str(out_dir.relative_to(REPO_ROOT)),
    ]
    m44_smoke_placeholder = [
        "python",
        "experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py",
        "--build",
        "--out-dir",
        "experiments/E003_perception_noise_expansion/artifacts/E003-M44_pre_cap_candidate_pool_export_smoke_v0",
        "--max-scans",
        "1",
        "--max-frames-per-scan",
        "2",
        "--max-labels",
        "32",
        "--max-predictions",
        "400",
        "--max-predictions-per-frame",
        "20",
        "--candidate-selection-policy",
        "cap_aware_label_balanced_ranking_v0",
        "--selection-score-mode",
        SUPPORT_AWARE_SCORE_MODE,
        "--pre-cap-per-scan-label-cap",
        "40",
        "--pre-cap-spatial-consolidation-radius-m",
        "0.5",
        "--raw-candidate-collection-cap",
        "20000",
        "--support-evidence-policy",
        SUPPORT_EVIDENCE_POLICY,
        "--support-evidence-radii-m",
        "0.75,1.0,1.5,2.0",
        "--export-pre-cap-candidate-pool",
    ]
    return {
        "commands_executed_for_m43": [
            command_payload(py_compile),
            command_payload(run_gate),
        ],
        "commands_reserved_for_m44_after_runner_edit": [
            command_payload(m44_smoke_placeholder),
        ],
        "m44_smoke_success_checks": [
            "pre_cap_candidate_pool.jsonl exists and row count equals policy input candidate count",
            "candidate pool rows include support evidence fields when support policy is enabled",
            "offline replay reproduces runner selected stable-candidate set for confidence_sqrt_depth_support_temporal_v0",
            "validator errors/warnings remain 0/0",
        ],
        "long_running_rule": "Run any 8-scan detector export in tmux/nohup with timestamped logs under logs/.",
    }


def build_coverage(
    *,
    m33: dict[str, Any],
    m40: dict[str, Any],
    m42: dict[str, Any],
    metric_comparison: dict[str, Any],
    row_comparison: dict[str, Any],
    route_decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "support_aware_scaled_rerun_route_gate_ready",
        "m43_version": M43_VERSION,
        "selected_route": route_decision["selected_route"],
        "short_smoke_valid": route_decision["short_smoke_valid"],
        "ranking_sensitive": route_decision["ranking_sensitive"],
        "quality_positive_in_short_smoke": route_decision["quality_positive_in_short_smoke"],
        "existing_candidate_pool_replay_available": route_decision["existing_candidate_pool_replay_available"],
        "immediate_support_aware_long_rerun_recommended": route_decision[
            "immediate_support_aware_long_rerun_recommended"
        ],
        "runner_edit_required_before_next_scaled_run": route_decision[
            "runner_edit_required_before_next_scaled_run"
        ],
        "m33_scaled_baseline_ready": route_decision["m33_scaled_baseline_ready"],
        "m33_final_prediction_rows": m33.get("final_prediction_rows"),
        "m33_matched_target_rows": m33.get("matched_target_rows"),
        "m33_false_positive_proposal_rows": m33.get("false_positive_proposal_rows"),
        "m33_proposal_precision": m33.get("proposal_precision"),
        "m40_status": m40.get("status"),
        "m42_status": m42.get("status"),
        "m40_score_mode": (m40.get("run_config") or {}).get("selection_score_mode"),
        "m42_score_mode": (m42.get("run_config") or {}).get("selection_score_mode"),
        "m42_support_ready": bool((m42.get("support_evidence") or {}).get("ready")),
        "m42_validator_error_rows": m42.get("validator_error_rows"),
        "m42_validator_warning_rows": m42.get("validator_warning_rows"),
        "m42_vs_m40_matched_proposal_delta": metric_comparison["matched_proposal_delta"],
        "m42_vs_m40_false_positive_delta": metric_comparison["false_positive_delta"],
        "m42_vs_m40_precision_delta": metric_comparison["precision_delta"],
        "m42_vs_m40_common_selected_rows": row_comparison["common_selected_rows"],
        "m42_vs_m40_selection_symmetric_difference_rows": row_comparison[
            "selection_symmetric_difference_rows"
        ],
        "m42_vs_m40_pre_cap_rank_changed_common_rows": row_comparison[
            "pre_cap_rank_changed_common_rows"
        ],
        "m42_vs_m40_selection_score_changed_common_rows": row_comparison[
            "selection_score_changed_common_rows"
        ],
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "next_recommended_unit": route_decision["next_recommended_unit"],
    }


def build_report(coverage: dict[str, Any], route_decision: dict[str, Any], candidate_contract: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# E003-M43 Support-Aware Scaled Rerun Route Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## Facts",
            "",
            f"- M40 score mode: `{coverage['m40_score_mode']}`.",
            f"- M42 score mode: `{coverage['m42_score_mode']}`.",
            f"- M42 support ready: {coverage['m42_support_ready']}.",
            f"- M42 validator errors/warnings: {coverage['m42_validator_error_rows']} / {coverage['m42_validator_warning_rows']}.",
            f"- M42 vs M40 matched proposal delta: {coverage['m42_vs_m40_matched_proposal_delta']}.",
            f"- M42 vs M40 false-positive delta: {coverage['m42_vs_m40_false_positive_delta']}.",
            f"- M42 vs M40 precision delta: {coverage['m42_vs_m40_precision_delta']}.",
            f"- M42 vs M40 common selected rows: {coverage['m42_vs_m40_common_selected_rows']}.",
            f"- M42 vs M40 selected symmetric difference rows: {coverage['m42_vs_m40_selection_symmetric_difference_rows']}.",
            f"- M42 vs M40 pre-cap rank changed common rows: {coverage['m42_vs_m40_pre_cap_rank_changed_common_rows']}.",
            f"- M42 vs M40 selection-score changed common rows: {coverage['m42_vs_m40_selection_score_changed_common_rows']}.",
            f"- Existing candidate-pool replay available: {coverage['existing_candidate_pool_replay_available']}.",
            f"- Selected route: `{coverage['selected_route']}`.",
            f"- Immediate support-aware long rerun recommended: {coverage['immediate_support_aware_long_rerun_recommended']}.",
            f"- Runner edit required before next scaled run: {coverage['runner_edit_required_before_next_scaled_run']}.",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}.",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}.",
            "",
            "## Paper Claim",
            "",
            "- E003-M43 supports only a route decision for support-aware proposal evaluation.",
            "- It does not support final real RGB-D/open-vocabulary robustness or a paper-table result.",
            "",
            "## Agent Inference",
            "",
            "- M42 is a valid runner smoke but does not improve proposal quality over M40 on the short artifact.",
            "- The score is not entirely inert: selected rows and ranks change, so a scaled test is still meaningful.",
            "- Existing artifacts cannot isolate support scoring because they do not preserve the pre-cap candidate pool.",
            "- The next route should export the support-instrumented candidate pool and replay score modes offline before any long scaled claim.",
            "",
            "## User Decision Needed",
            "",
            "- None for the route gate.",
            "",
            "## Next Unit",
            "",
            f"- {coverage['next_recommended_unit']}.",
            f"- Candidate-pool contract: `{candidate_contract['contract_id']}`.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m33-dir", type=Path, default=DEFAULT_M33_DIR)
    parser.add_argument("--m40-dir", type=Path, default=DEFAULT_M40_DIR)
    parser.add_argument("--m42-dir", type=Path, default=DEFAULT_M42_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m33 = load_json(args.m33_dir / "coverage.json")
    m40 = load_json(args.m40_dir / "coverage.json")
    m42 = load_json(args.m42_dir / "coverage.json")
    m40_rows = load_jsonl(args.m40_dir / "container_output" / "real_proposals.jsonl")
    m42_rows = load_jsonl(args.m42_dir / "container_output" / "real_proposals.jsonl")

    metric_comparison = compare_metrics(m40, m42)
    row_comparison = compare_selected_rows(m40_rows, m42_rows)
    m42_support_summary = support_summary(m42_rows)
    replay_available = existing_replay_available(args.m40_dir, args.m42_dir, args.m33_dir)
    route_decision = build_route_decision(
        m33=m33,
        m40=m40,
        m42=m42,
        metric_comparison=metric_comparison,
        row_comparison=row_comparison,
        replay_available=replay_available,
    )
    candidate_contract = build_candidate_pool_contract()
    coverage = build_coverage(
        m33=m33,
        m40=m40,
        m42=m42,
        metric_comparison=metric_comparison,
        row_comparison=row_comparison,
        route_decision=route_decision,
    )
    verification_plan = build_verification_plan(args.out_dir)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(
        args.out_dir / "m40_m42_comparison.json",
        {
            "metric_comparison": metric_comparison,
            "row_comparison": row_comparison,
            "m42_support_summary": m42_support_summary,
        },
    )
    write_json(args.out_dir / "route_decision.json", route_decision)
    write_json(args.out_dir / "candidate_pool_contract.json", candidate_contract)
    write_json(args.out_dir / "verification_plan.json", verification_plan)
    write_text(args.out_dir / "report.md", build_report(coverage, route_decision, candidate_contract))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
