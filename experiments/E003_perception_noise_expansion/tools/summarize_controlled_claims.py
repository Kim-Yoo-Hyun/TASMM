#!/usr/bin/env python3
"""Summarize E003 controlled perception-robustness claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = EXPERIMENT_ROOT / "artifacts"
DEFAULT_OUT_DIR = ARTIFACT_ROOT / "E003-M15_controlled_perception_claim_summary_v0"
SUMMARY_VERSION = "e003_controlled_perception_claim_summary_v0"


SOURCE_UNITS = {
    "M03_score_jitter_eval": "E003-M03_noisy_policy_eval_v0",
    "M04_score_jitter_boundary": "E003-M04_robustness_failure_analysis_v0",
    "M06_dropout_eval": "E003-M06_annotation_proposal_dropout_v0",
    "M07_dropout_boundary": "E003-M07_dropout_failure_boundary_v0",
    "M08_false_positive_eval": "E003-M08_annotation_false_positive_v0",
    "M09_false_positive_boundary": "E003-M09_false_positive_failure_boundary_v0",
    "M10_centroid_jitter_eval": "E003-M10_annotation_centroid_jitter_v0",
    "M11_centroid_jitter_boundary": "E003-M11_centroid_jitter_failure_boundary_v0",
    "M12_combined_route": "E003-M12_combined_noise_route_decision_v0",
    "M13_combined_eval": "E003-M13_annotation_combined_moderate_v0",
    "M14_combined_boundary": "E003-M14_combined_noise_failure_boundary_v0",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def source_dir(unit_key: str) -> Path:
    return ARTIFACT_ROOT / SOURCE_UNITS[unit_key]


def maybe_json(unit_key: str, filename: str) -> dict[str, Any]:
    path = source_dir(unit_key) / filename
    if not path.exists():
        return {}
    return load_json(path)


def nested(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def collect_sources() -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for unit_key, dirname in SOURCE_UNITS.items():
        unit_dir = ARTIFACT_ROOT / dirname
        sources[unit_key] = {
            "unit_key": unit_key,
            "artifact_dir": str(unit_dir),
            "coverage": maybe_json(unit_key, "coverage.json"),
            "claim_boundary": maybe_json(unit_key, "claim_boundary.json"),
            "summary": maybe_json(unit_key, "summary.json"),
            "metrics": maybe_json(unit_key, "metrics.json"),
            "real_proposal_requirements": maybe_json(unit_key, "real_proposal_route_requirements.json"),
        }
    return sources


def build_profile_summary_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    m04_claim = sources["M04_score_jitter_boundary"]["claim_boundary"]
    m04_cov = sources["M04_score_jitter_boundary"]["coverage"]
    m07_claim = sources["M07_dropout_boundary"]["claim_boundary"]
    m09_claim = sources["M09_false_positive_boundary"]["claim_boundary"]
    m11_claim = sources["M11_centroid_jitter_boundary"]["claim_boundary"]
    m14_claim = sources["M14_combined_boundary"]["claim_boundary"]
    rows = [
        {
            "summary_version": SUMMARY_VERSION,
            "profile": "annotation_score_jitter_v0",
            "boundary_unit": "E003-M04_robustness_failure_analysis_v0",
            "status": m04_claim["status"],
            "stress_type": "score/rank perturbation",
            "stress_query_rows": None,
            "prediction_rows": m04_claim["key_evidence"]["prediction_rows"],
            "boundary_rows": None,
            "hard_boundary_rows": m04_claim["key_evidence"]["primary_hard_failure_rows"],
            "task_context": "routine_fetch",
            "row_band": "significant_moved",
            "task_conditioned_metric": {
                "proxy_sr_delta": m04_claim["key_evidence"]["task_significant_routine_proxy_sr_delta"],
                "expected_search_cost_delta": m04_claim["key_evidence"][
                    "task_significant_routine_cost_delta"
                ],
            },
            "reachable_first_metric": {
                "vs_task_stress_sr_delta": m04_claim["key_evidence"][
                    "reachable_vs_task_significant_routine_stress_sr_delta"
                ],
                "vs_task_unreachable_event_delta": m04_claim["key_evidence"][
                    "reachable_vs_task_significant_routine_unreachable_event_delta"
                ],
            },
            "safe_scope": "controlled annotation-proxy ranking-noise robustness boundary",
            "main_limitation": "target-drop and real detector proposal recall are absent",
            "uses_real_rgbd_perception": m04_cov.get("uses_real_rgbd_perception"),
            "uses_open_vocab_perception": m04_cov.get("uses_open_vocab_perception"),
            "uses_real_navigation": m04_cov.get("uses_real_navigation"),
        },
        {
            "summary_version": SUMMARY_VERSION,
            "profile": "annotation_proposal_dropout_v0",
            "boundary_unit": "E003-M07_dropout_failure_boundary_v0",
            "status": m07_claim["status"],
            "stress_type": "proposal recall / target dropout",
            "stress_query_rows": m07_claim["key_evidence"]["dropout_query_rows"],
            "prediction_rows": sources["M07_dropout_boundary"]["coverage"].get("prediction_rows"),
            "boundary_rows": m07_claim["key_evidence"]["boundary_rows"],
            "hard_boundary_rows": sources["M07_dropout_boundary"]["coverage"].get("hard_boundary_rows"),
            "target_dropped_rate": m07_claim["key_evidence"]["target_dropped_rate"],
            "strict_target_retained_rate_excluding_forced": m07_claim["key_evidence"][
                "strict_target_retained_rate_excluding_forced"
            ],
            "task_context": "routine_fetch",
            "row_band": "significant_moved",
            "task_conditioned_metric": {
                "target_dropped_sr": m07_claim["key_evidence"]["target_dropped_significant_routine_task_sr"],
                "natural_retained_sr": m07_claim["key_evidence"][
                    "natural_retained_significant_routine_task_sr"
                ],
            },
            "reachable_first_metric": {
                "natural_retained_sr": m07_claim["key_evidence"][
                    "natural_retained_significant_routine_reachable_sr"
                ],
            },
            "safe_scope": "controlled annotation-proxy proposal-recall boundary",
            "main_limitation": "target-dropped rows are proposal-recall ceiling cases",
            "uses_real_rgbd_perception": m07_claim["key_evidence"]["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": m07_claim["key_evidence"]["uses_open_vocab_perception"],
            "uses_real_navigation": m07_claim["key_evidence"]["uses_real_navigation"],
        },
        {
            "summary_version": SUMMARY_VERSION,
            "profile": "annotation_false_positive_v0",
            "boundary_unit": "E003-M09_false_positive_failure_boundary_v0",
            "status": m09_claim["status"],
            "stress_type": "annotation-derived false-positive contamination",
            "stress_query_rows": m09_claim["key_evidence"]["stress_query_rows"],
            "prediction_rows": sources["M09_false_positive_boundary"]["coverage"].get("prediction_rows"),
            "boundary_rows": m09_claim["key_evidence"]["boundary_rows"],
            "hard_boundary_rows": m09_claim["key_evidence"]["hard_boundary_rows"],
            "false_positive_added_rows": m09_claim["key_evidence"]["false_positive_added_rows"],
            "target_pushed_down_rows": m09_claim["key_evidence"]["target_pushed_down_rows"],
            "task_context": "routine_fetch",
            "row_band": "significant_moved",
            "task_conditioned_metric": {
                "target_push_sr": m09_claim["key_evidence"]["target_push_significant_routine_task_sr"],
            },
            "reachable_first_metric": {
                "target_push_sr": m09_claim["key_evidence"][
                    "target_push_significant_routine_reachable_sr"
                ],
                "vs_task_sr_delta": m09_claim["key_evidence"][
                    "significant_routine_reachable_minus_task_sr_delta"
                ],
                "success_gain_rows": m09_claim["key_evidence"][
                    "significant_routine_reachable_success_gain_rows"
                ],
            },
            "safe_scope": "controlled annotation-derived false-positive boundary",
            "main_limitation": "no real detector hallucinations or same-label detector false positives",
            "uses_real_rgbd_perception": m09_claim["key_evidence"]["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": m09_claim["key_evidence"]["uses_open_vocab_perception"],
            "uses_real_navigation": m09_claim["key_evidence"]["uses_real_navigation"],
        },
        {
            "summary_version": SUMMARY_VERSION,
            "profile": "annotation_centroid_jitter_v0",
            "boundary_unit": "E003-M11_centroid_jitter_failure_boundary_v0",
            "status": m11_claim["status"],
            "stress_type": "centroid localization jitter",
            "stress_query_rows": m11_claim["key_evidence"]["stress_query_rows"],
            "prediction_rows": sources["M11_centroid_jitter_boundary"]["coverage"].get("prediction_rows"),
            "boundary_rows": m11_claim["key_evidence"]["boundary_rows"],
            "hard_boundary_rows": m11_claim["key_evidence"]["hard_boundary_rows"],
            "target_jitter_exceeds_threshold_rows": m11_claim["key_evidence"][
                "target_jitter_exceeds_threshold_rows"
            ],
            "target_rank_changed_rows": m11_claim["key_evidence"]["target_rank_changed_rows"],
            "task_context": "routine_fetch",
            "row_band": "significant_moved",
            "task_conditioned_metric": {
                "identity_sr": m11_claim["key_evidence"]["significant_routine_task_identity_sr"],
                "localization_sr": m11_claim["key_evidence"]["significant_routine_task_localization_sr"],
                "threshold_identity_sr": m11_claim["key_evidence"][
                    "significant_routine_threshold_task_identity_sr"
                ],
                "threshold_localization_sr": m11_claim["key_evidence"][
                    "significant_routine_threshold_task_localization_sr"
                ],
            },
            "reachable_first_metric": {
                "identity_sr": m11_claim["key_evidence"]["significant_routine_reachable_identity_sr"],
                "localization_sr": m11_claim["key_evidence"][
                    "significant_routine_reachable_localization_sr"
                ],
                "vs_task_identity_delta": m11_claim["key_evidence"][
                    "significant_routine_reachable_minus_task_identity_delta"
                ],
                "vs_task_localization_delta": m11_claim["key_evidence"][
                    "significant_routine_reachable_minus_task_localization_delta"
                ],
            },
            "safe_scope": "controlled annotation-proxy localization-noise boundary",
            "main_limitation": "grid/path costs are not recomputed after centroid perturbation",
            "uses_real_rgbd_perception": m11_claim["key_evidence"]["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": m11_claim["key_evidence"]["uses_open_vocab_perception"],
            "uses_real_navigation": m11_claim["key_evidence"]["uses_real_navigation"],
        },
        {
            "summary_version": SUMMARY_VERSION,
            "profile": "annotation_combined_moderate_v0",
            "boundary_unit": "E003-M14_combined_noise_failure_boundary_v0",
            "status": m14_claim["status"],
            "stress_type": "combined score/rank, proposal dropout, false positives, centroid jitter",
            "stress_query_rows": m14_claim["key_evidence"]["stress_query_rows"],
            "prediction_rows": sources["M14_combined_boundary"]["coverage"].get("prediction_rows"),
            "boundary_rows": m14_claim["key_evidence"]["boundary_rows"],
            "hard_boundary_rows": m14_claim["key_evidence"]["hard_boundary_rows"],
            "target_dropped_rows": m14_claim["key_evidence"]["target_dropped_rows"],
            "false_positive_added_rows": m14_claim["key_evidence"]["false_positive_added_rows"],
            "target_pushed_down_rows": m14_claim["key_evidence"]["target_pushed_down_rows"],
            "target_rank_changed_rows": m14_claim["key_evidence"]["target_rank_changed_rows"],
            "target_jitter_exceeds_threshold_rows": m14_claim["key_evidence"][
                "target_jitter_exceeds_threshold_rows"
            ],
            "task_context": "routine_fetch",
            "row_band": "significant_moved",
            "task_conditioned_metric": {
                "identity_sr": m14_claim["key_evidence"]["significant_routine_task_identity_sr"],
                "localization_sr": m14_claim["key_evidence"]["significant_routine_task_localization_sr"],
                "target_dropped_identity_sr": m14_claim["key_evidence"][
                    "significant_routine_task_target_dropped_identity_sr"
                ],
            },
            "reachable_first_metric": {
                "identity_sr": m14_claim["key_evidence"]["significant_routine_reachable_identity_sr"],
                "localization_sr": m14_claim["key_evidence"][
                    "significant_routine_reachable_localization_sr"
                ],
                "vs_task_identity_delta": m14_claim["key_evidence"][
                    "significant_routine_reachable_minus_task_identity_delta"
                ],
                "vs_task_localization_delta": m14_claim["key_evidence"][
                    "significant_routine_reachable_minus_task_localization_delta"
                ],
                "identity_success_gain_rows": m14_claim["key_evidence"][
                    "significant_routine_reachable_identity_success_gain_rows"
                ],
                "identity_success_loss_rows": m14_claim["key_evidence"][
                    "significant_routine_reachable_identity_success_loss_rows"
                ],
            },
            "safe_scope": "controlled annotation-proxy combined-noise boundary",
            "main_limitation": "not real RGB-D/open-vocabulary detector output and not real navigation",
            "uses_real_rgbd_perception": m14_claim["key_evidence"]["uses_real_rgbd_perception"],
            "uses_open_vocab_perception": m14_claim["key_evidence"]["uses_open_vocab_perception"],
            "uses_real_navigation": m14_claim["key_evidence"]["uses_real_navigation"],
        },
    ]
    return rows


def build_claim_evidence_rows(profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined = next(row for row in profile_rows if row["profile"] == "annotation_combined_moderate_v0")
    fp = next(row for row in profile_rows if row["profile"] == "annotation_false_positive_v0")
    centroid = next(row for row in profile_rows if row["profile"] == "annotation_centroid_jitter_v0")
    dropout = next(row for row in profile_rows if row["profile"] == "annotation_proposal_dropout_v0")
    return [
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-001",
            "status": "supported_controlled_annotation_proxy",
            "claim": "E003 provides a controlled annotation-proxy perception/proposal-noise suite for H001 stale semantic-memory search.",
            "evidence_units": [
                "E003-M03",
                "E003-M07",
                "E003-M09",
                "E003-M11",
                "E003-M14",
            ],
            "key_numbers": {
                "profiles_with_boundary": 5,
                "combined_boundary_rows": combined["boundary_rows"],
                "combined_hard_boundary_rows": combined["hard_boundary_rows"],
            },
            "paper_use": "Can be used as a controlled stress-test table or ablation suite, with annotation-proxy wording.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-002",
            "status": "supported_with_boundary",
            "claim": "Target-dropped rows should be reported as proposal-recall ceilings rather than recoverable memory-policy failures.",
            "evidence_units": ["E003-M07", "E003-M14"],
            "key_numbers": {
                "dropout_target_dropped_rate": dropout["target_dropped_rate"],
                "combined_target_dropped_rows": combined["target_dropped_rows"],
                "combined_target_dropped_identity_sr": combined["task_conditioned_metric"][
                    "target_dropped_identity_sr"
                ],
            },
            "paper_use": "Use as denominator rule and failure-analysis boundary.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-003",
            "status": "supported_subset",
            "claim": "`reachable_first_task_conditioned_budget_v0` mitigates distractor/rank-budget failures in significant moved `routine_fetch` under false-positive and combined stress.",
            "evidence_units": ["E003-M09", "E003-M14"],
            "key_numbers": {
                "false_positive_target_push_task_sr": fp["task_conditioned_metric"]["target_push_sr"],
                "false_positive_target_push_reachable_sr": fp["reachable_first_metric"][
                    "target_push_sr"
                ],
                "false_positive_reachable_gain_rows": fp["reachable_first_metric"][
                    "success_gain_rows"
                ],
                "combined_task_identity_sr": combined["task_conditioned_metric"]["identity_sr"],
                "combined_reachable_identity_sr": combined["reachable_first_metric"]["identity_sr"],
                "combined_reachable_minus_task_identity_delta": combined["reachable_first_metric"][
                    "vs_task_identity_delta"
                ],
                "combined_reachable_gain_rows": combined["reachable_first_metric"][
                    "identity_success_gain_rows"
                ],
                "combined_reachable_loss_rows": combined["reachable_first_metric"][
                    "identity_success_loss_rows"
                ],
            },
            "paper_use": "Use as method-signal evidence, but keep subset and proxy metric labels explicit.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-004",
            "status": "supported_controlled_annotation_proxy",
            "claim": "Identity retrieval and spatial localization must be reported separately under centroid noise.",
            "evidence_units": ["E003-M11"],
            "key_numbers": {
                "target_jitter_exceeds_threshold_rows": centroid[
                    "target_jitter_exceeds_threshold_rows"
                ],
                "threshold_identity_sr": centroid["task_conditioned_metric"][
                    "threshold_identity_sr"
                ],
                "threshold_localization_sr": centroid["task_conditioned_metric"][
                    "threshold_localization_sr"
                ],
            },
            "paper_use": "Use as metric design and failure-analysis justification.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-005",
            "status": "weakened_not_main_claim",
            "claim": "`task_conditioned_budget_v0` alone is robust under all perception-like noise.",
            "evidence_units": ["E003-M14"],
            "key_numbers": {
                "combined_task_identity_sr": combined["task_conditioned_metric"]["identity_sr"],
                "combined_task_localization_sr": combined["task_conditioned_metric"][
                    "localization_sr"
                ],
                "combined_reachable_identity_sr": combined["reachable_first_metric"]["identity_sr"],
                "combined_reachable_localization_sr": combined["reachable_first_metric"][
                    "localization_sr"
                ],
            },
            "paper_use": "Do not use as main claim; use it to motivate reachable-first and failure-boundary design.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-006",
            "status": "unsupported_blocked",
            "claim": "H001 is robust to real RGB-D or open-vocabulary detector outputs.",
            "evidence_units": ["E003-M01", "E003-M05", "E003-M12"],
            "key_numbers": {
                "real_rgbd_proposal_ready_rows": 0,
                "real_open_vocab_proposal_ready_rows": 0,
                "proposal_output_files": 0,
            },
            "paper_use": "Blocked until Dockerized detector/proposal generation and proposal-to-3DSSG matching are staged.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-007",
            "status": "unsupported_blocked",
            "claim": "E003 reports real navigation `SR` / `SPL` or deployable search-policy performance.",
            "evidence_units": ["E002", "E003-M14"],
            "key_numbers": {
                "uses_real_navigation": False,
                "grid_path_recomputed_for_centroid_jitter": False,
            },
            "paper_use": "Blocked until simulator, navmesh, or trajectory execution source is available.",
        },
        {
            "summary_version": SUMMARY_VERSION,
            "claim_id": "C-E003-008",
            "status": "unsupported_blocked",
            "claim": "E003 evaluates natural-language intention understanding.",
            "evidence_units": ["E001", "E003"],
            "key_numbers": {
                "intent_condition_source": "structured_task_context",
            },
            "paper_use": "Keep human intent as structured task context / memory-trust condition unless an LLM/NLU route is added later.",
        },
    ]


def build_promotion_gate(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    m12_requirements = sources["M12_combined_route"]["real_proposal_requirements"]
    m14_claim = sources["M14_combined_boundary"]["claim_boundary"]
    return {
        "summary_version": SUMMARY_VERSION,
        "status": "controlled_claim_ready_real_proposal_blocked",
        "controlled_claim_ready": True,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "real_navigation_claim_ready": False,
        "paper_table_readiness": {
            "controlled_annotation_proxy_table": "ready_as_controlled_stress_table",
            "real_perception_table": "blocked",
            "real_navigation_table": "blocked",
        },
        "current_blockers": m12_requirements.get("current_blockers", []),
        "minimum_unblock_requirements": m12_requirements.get("minimum_unblock_requirements", []),
        "next_recommended_unit": "E003-M16 Dockerized real-proposal route decision",
        "next_recommended_unit_reason": (
            "E003 controlled profiles and boundaries are consolidated; top-tier perception claim "
            "now needs a real proposal source, scan alignment, Docker command, and proposal matching schema."
        ),
        "carry_forward_boundaries": m14_claim["partial_or_weakened_claims"]
        + m14_claim["unsupported_claims"],
    }


def build_claim_summary(
    sources: dict[str, dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    promotion_gate: dict[str, Any],
) -> dict[str, Any]:
    completed_statuses = {
        unit_key: sources[unit_key]["coverage"].get("status")
        or sources[unit_key]["claim_boundary"].get("status")
        for unit_key in SOURCE_UNITS
    }
    all_real_rgbd_flags = [
        row.get("uses_real_rgbd_perception")
        for row in profile_rows
        if row.get("uses_real_rgbd_perception") is not None
    ]
    all_open_vocab_flags = [
        row.get("uses_open_vocab_perception")
        for row in profile_rows
        if row.get("uses_open_vocab_perception") is not None
    ]
    all_navigation_flags = [
        row.get("uses_real_navigation")
        for row in profile_rows
        if row.get("uses_real_navigation") is not None
    ]
    combined = next(row for row in profile_rows if row["profile"] == "annotation_combined_moderate_v0")
    return {
        "summary_version": SUMMARY_VERSION,
        "status": "controlled_perception_claim_summary_ready",
        "source_units": SOURCE_UNITS,
        "completed_statuses": completed_statuses,
        "controlled_profiles_summarized": [row["profile"] for row in profile_rows],
        "claim_rows": len(claim_rows),
        "supported_claim_count": sum(1 for row in claim_rows if row["status"].startswith("supported")),
        "unsupported_claim_count": sum(1 for row in claim_rows if row["status"] == "unsupported_blocked"),
        "core_supported_claim": (
            "Under controlled annotation-proxy perception/proposal noise, H001 can separate proposal-recall, "
            "distractor rank/budget, and centroid-localization failures, and reachable-first ordering mitigates "
            "combined distractor/rank-budget damage in significant moved routine-fetch rows."
        ),
        "main_method_signal": {
            "profile": "annotation_combined_moderate_v0",
            "subset": "significant_moved|routine_fetch",
            "task_conditioned_identity_sr": combined["task_conditioned_metric"]["identity_sr"],
            "reachable_first_identity_sr": combined["reachable_first_metric"]["identity_sr"],
            "reachable_minus_task_identity_delta": combined["reachable_first_metric"][
                "vs_task_identity_delta"
            ],
            "reachable_gain_rows": combined["reachable_first_metric"]["identity_success_gain_rows"],
            "reachable_loss_rows": combined["reachable_first_metric"]["identity_success_loss_rows"],
        },
        "global_flags": {
            "uses_real_rgbd_perception_any": any(all_real_rgbd_flags),
            "uses_open_vocab_perception_any": any(all_open_vocab_flags),
            "uses_real_navigation_any": any(all_navigation_flags),
            "all_profiles_annotation_proxy": not any(all_real_rgbd_flags)
            and not any(all_open_vocab_flags)
            and not any(all_navigation_flags),
        },
        "promotion_gate_status": promotion_gate["status"],
        "next_recommended_unit": promotion_gate["next_recommended_unit"],
    }


def build_coverage(
    out_dir: Path,
    sources: dict[str, dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    promotion_gate: dict[str, Any],
    claim_summary: dict[str, Any],
) -> dict[str, Any]:
    missing_coverage = [
        unit_key for unit_key, source in sources.items() if not source["coverage"]
    ]
    missing_claim_boundaries = [
        unit_key
        for unit_key in [
            "M04_score_jitter_boundary",
            "M07_dropout_boundary",
            "M09_false_positive_boundary",
            "M11_centroid_jitter_boundary",
            "M14_combined_boundary",
        ]
        if not sources[unit_key]["claim_boundary"]
    ]
    status = "controlled_perception_claim_summary_ready"
    if missing_coverage or missing_claim_boundaries:
        status = "review_needed"
    return {
        "summary_version": SUMMARY_VERSION,
        "status": status,
        "source_units": SOURCE_UNITS,
        "profile_rows": len(profile_rows),
        "claim_evidence_rows": len(claim_rows),
        "controlled_claim_ready": promotion_gate["controlled_claim_ready"],
        "real_rgbd_or_open_vocab_claim_ready": promotion_gate[
            "real_rgbd_or_open_vocab_claim_ready"
        ],
        "real_navigation_claim_ready": promotion_gate["real_navigation_claim_ready"],
        "missing_coverage": missing_coverage,
        "missing_claim_boundaries": missing_claim_boundaries,
        "docker_required": False,
        "docker_reason": "E003-M15 is repository-local aggregation over E003 JSON/JSONL artifacts; future real detector/open-vocabulary proposal generation remains Docker-required.",
        "next_recommended_unit": claim_summary["next_recommended_unit"],
        "outputs": {
            "profile_summary_rows": str(out_dir / "profile_summary_rows.jsonl"),
            "claim_evidence_rows": str(out_dir / "claim_evidence_rows.jsonl"),
            "promotion_gate": str(out_dir / "promotion_gate.json"),
            "claim_summary": str(out_dir / "claim_summary.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    coverage: dict[str, Any],
    profile_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    promotion_gate: dict[str, Any],
    claim_summary: dict[str, Any],
    out_dir: Path,
) -> str:
    combined = next(row for row in profile_rows if row["profile"] == "annotation_combined_moderate_v0")
    fp = next(row for row in profile_rows if row["profile"] == "annotation_false_positive_v0")
    centroid = next(row for row in profile_rows if row["profile"] == "annotation_centroid_jitter_v0")
    lines = [
        "# E003-M15 Controlled Perception Claim Summary",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Profile summary rows: {coverage['profile_rows']}",
        f"- Claim evidence rows: {coverage['claim_evidence_rows']}",
        f"- Controlled claim ready: {coverage['controlled_claim_ready']}",
        f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
        f"- Real navigation claim ready: {coverage['real_navigation_claim_ready']}",
        f"- Main method-signal subset: `{claim_summary['main_method_signal']['subset']}`",
        f"- Combined `task_conditioned_budget_v0` identity `SR`: {claim_summary['main_method_signal']['task_conditioned_identity_sr']}",
        f"- Combined `reachable_first_task_conditioned_budget_v0` identity `SR`: {claim_summary['main_method_signal']['reachable_first_identity_sr']}",
        f"- Reachable-first minus task identity `SR` delta: {claim_summary['main_method_signal']['reachable_minus_task_identity_delta']}",
        f"- Reachable-first gain/loss rows: {claim_summary['main_method_signal']['reachable_gain_rows']} / {claim_summary['main_method_signal']['reachable_loss_rows']}",
        f"- Docker required: {coverage['docker_required']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Profile Evidence",
        "",
        "| Profile | Boundary | rows | hard rows | main signal | limitation |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in profile_rows:
        if row["profile"] == "annotation_score_jitter_v0":
            signal = (
                "`task_conditioned_budget_v0` significant routine proxy `SR` delta "
                f"{row['task_conditioned_metric']['proxy_sr_delta']}"
            )
        elif row["profile"] == "annotation_proposal_dropout_v0":
            signal = (
                "target-dropped significant routine `SR` "
                f"{row['task_conditioned_metric']['target_dropped_sr']}"
            )
        elif row["profile"] == "annotation_false_positive_v0":
            signal = (
                "target-pushed task/reachable `SR` "
                f"{row['task_conditioned_metric']['target_push_sr']} / "
                f"{row['reachable_first_metric']['target_push_sr']}"
            )
        elif row["profile"] == "annotation_centroid_jitter_v0":
            signal = (
                "threshold identity/localization `SR` "
                f"{row['task_conditioned_metric']['threshold_identity_sr']} / "
                f"{row['task_conditioned_metric']['threshold_localization_sr']}"
            )
        else:
            signal = (
                "combined task/reachable identity `SR` "
                f"{row['task_conditioned_metric']['identity_sr']} / "
                f"{row['reachable_first_metric']['identity_sr']}"
            )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['profile']}`",
                    f"`{row['boundary_unit']}`",
                    str(row.get("boundary_rows")),
                    str(row.get("hard_boundary_rows")),
                    signal,
                    row["main_limitation"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            f"- {claim_summary['core_supported_claim']}",
            "- E003 can be written as a controlled annotation-proxy robustness suite, not as a real RGB-D/open-vocabulary perception result.",
            "- Target-dropped, false-positive rank/budget, and centroid-localization failures should remain separate denominators in paper tables.",
            "- `reachable_first_task_conditioned_budget_v0` is the current strongest method signal under false-positive and combined stress.",
            "",
            "## Claim Ledger",
            "",
        ]
    )
    for row in claim_rows:
        lines.append(f"- `{row['claim_id']}` [{row['status']}]: {row['claim']}")
    lines.extend(
        [
            "",
            "## 에이전트 추론",
            "",
            f"- Combined stress is the most informative current evidence: `task_conditioned_budget_v0` drops to {combined['task_conditioned_metric']['identity_sr']} identity `SR`, while `reachable_first_task_conditioned_budget_v0` reaches {combined['reachable_first_metric']['identity_sr']}.",
            f"- False-positive target-pushed rows show the same pattern: task-conditioned `SR` {fp['task_conditioned_metric']['target_push_sr']} vs reachable-first `SR` {fp['reachable_first_metric']['target_push_sr']}.",
            f"- Centroid jitter requires a separate localization metric because threshold-exceeded rows have identity `SR` {centroid['task_conditioned_metric']['threshold_identity_sr']} and localization `SR` {centroid['task_conditioned_metric']['threshold_localization_sr']}.",
            "- For top-tier positioning, this summary is necessary but not sufficient: a real proposal route is still needed before claiming real perception robustness.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- Next recommended unit: `{promotion_gate['next_recommended_unit']}`.",
            "- 사용자 판단이 필요한 지점은 real RGB-D/open-vocabulary proposal route를 바로 시작할지, 또는 E004 task-context memory trust로 이동하기 전에 E003 real-proposal gate를 먼저 여는지다.",
            "",
            "## Real Proposal Promotion Gate",
            "",
            f"- Status: `{promotion_gate['status']}`",
            f"- Paper controlled table readiness: `{promotion_gate['paper_table_readiness']['controlled_annotation_proxy_table']}`",
            f"- Real perception table readiness: `{promotion_gate['paper_table_readiness']['real_perception_table']}`",
            f"- Real navigation table readiness: `{promotion_gate['paper_table_readiness']['real_navigation_table']}`",
            "",
            "Minimum unblock requirements:",
        ]
    )
    for item in promotion_gate["minimum_unblock_requirements"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `profile_summary_rows.jsonl`",
            "- `claim_evidence_rows.jsonl`",
            "- `promotion_gate.json`",
            "- `claim_summary.json`",
            "- `coverage.json`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    sources = collect_sources()
    profile_rows = build_profile_summary_rows(sources)
    claim_rows = build_claim_evidence_rows(profile_rows)
    promotion_gate = build_promotion_gate(sources)
    claim_summary = build_claim_summary(sources, profile_rows, claim_rows, promotion_gate)
    coverage = build_coverage(
        args.out_dir,
        sources,
        profile_rows,
        claim_rows,
        promotion_gate,
        claim_summary,
    )
    report = build_report(coverage, profile_rows, claim_rows, promotion_gate, claim_summary, args.out_dir)

    write_jsonl(args.out_dir / "profile_summary_rows.jsonl", profile_rows)
    write_jsonl(args.out_dir / "claim_evidence_rows.jsonl", claim_rows)
    write_json(args.out_dir / "promotion_gate.json", promotion_gate)
    write_json(args.out_dir / "claim_summary.json", claim_summary)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": coverage["status"], "out_dir": str(args.out_dir)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
