#!/usr/bin/env python3
"""Select the E003-M12 route after individual controlled-noise boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M01_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M01_source_audit_v0"
DEFAULT_M05_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M05_route_v0"
DEFAULT_M07_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M07_dropout_failure_boundary_v0"
DEFAULT_M09_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M09_false_positive_failure_boundary_v0"
DEFAULT_M11_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M11_centroid_jitter_failure_boundary_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M12_combined_noise_route_decision_v0"
ANALYSIS_VERSION = "e003_m12_combined_noise_route_decision_v0"
SELECTED_PROFILE = "annotation_combined_moderate_v0"
NEXT_UNIT = "E003-M13_annotation_combined_moderate_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def build_evidence_summary(
    noise_plan: dict[str, Any],
    route_m05: dict[str, Any],
    dropout_claim: dict[str, Any],
    false_positive_claim: dict[str, Any],
    centroid_claim: dict[str, Any],
    centroid_coverage: dict[str, Any],
) -> dict[str, Any]:
    dropout = dropout_claim["key_evidence"]
    false_positive = false_positive_claim["key_evidence"]
    centroid = centroid_claim["key_evidence"]
    return {
        "analysis_version": ANALYSIS_VERSION,
        "ready_rows": noise_plan["ready_rows"],
        "individual_controlled_profiles_complete": {
            "annotation_score_jitter_v0": True,
            "annotation_proposal_dropout_v0": dropout_claim["status"] == "dropout_boundary_ready",
            "annotation_false_positive_v0": false_positive_claim["status"] == "false_positive_boundary_ready",
            "annotation_centroid_jitter_v0": centroid_claim["status"] == "centroid_jitter_boundary_ready",
        },
        "real_proposal_readiness": {
            "m05_status": route_m05["status"],
            "query_rows": route_m05["query_rows"],
            "query_rows_with_rescan_rgbd_ready": route_m05["query_rows_with_rescan_rgbd_ready"],
            "query_rows_with_real_rgbd_proposal_ready": route_m05[
                "query_rows_with_real_rgbd_proposal_ready"
            ],
            "query_rows_with_real_open_vocab_proposal_ready": route_m05[
                "query_rows_with_real_open_vocab_proposal_ready"
            ],
            "proposal_output_files_found": route_m05["proposal_output_files_found"],
            "blockers": route_m05["blockers"],
        },
        "profile_boundary_evidence": {
            "dropout": {
                "boundary_rows": dropout["boundary_rows"],
                "target_drop_attempt_rate": dropout["target_drop_attempt_rate"],
                "target_dropped_rate": dropout["target_dropped_rate"],
                "strict_target_retained_rate_excluding_forced": dropout[
                    "strict_target_retained_rate_excluding_forced"
                ],
                "significant_routine_target_dropped_task_sr": dropout[
                    "target_dropped_significant_routine_task_sr"
                ],
            },
            "false_positive": {
                "boundary_rows": false_positive["boundary_rows"],
                "hard_boundary_rows": false_positive["hard_boundary_rows"],
                "false_positive_added_rows": false_positive["false_positive_added_rows"],
                "target_pushed_down_rows": false_positive["target_pushed_down_rows"],
                "target_pushed_down_rate": false_positive["target_pushed_down_rate"],
                "significant_routine_reachable_minus_task_sr_delta": false_positive[
                    "significant_routine_reachable_minus_task_sr_delta"
                ],
            },
            "centroid_jitter": {
                "boundary_rows": centroid["boundary_rows"],
                "hard_boundary_rows": centroid["hard_boundary_rows"],
                "target_jitter_exceeds_threshold_rows": centroid[
                    "target_jitter_exceeds_threshold_rows"
                ],
                "target_jitter_exceeds_threshold_rate": centroid[
                    "target_jitter_exceeds_threshold_rate"
                ],
                "target_rank_changed_rows": centroid["target_rank_changed_rows"],
                "significant_routine_task_identity_sr": centroid[
                    "significant_routine_task_identity_sr"
                ],
                "significant_routine_task_localization_sr": centroid[
                    "significant_routine_task_localization_sr"
                ],
                "grid_path_recomputed_for_centroid_jitter": centroid[
                    "grid_path_recomputed_for_centroid_jitter"
                ],
            },
        },
        "shared_non_claims": sorted(
            set(dropout_claim["unsupported_claims"])
            | set(false_positive_claim["unsupported_claims"])
            | set(centroid_claim["unsupported_claims"])
        ),
        "centroid_coverage_status": centroid_coverage["status"],
    }


def build_combined_profile_contract(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "profile_id": SELECTED_PROFILE,
        "role": "controlled_annotation_proxy_combined_stress",
        "reference_profile": "clean_annotation_oracle_v0",
        "next_executable_unit": NEXT_UNIT,
        "source": "E001-M02 annotation candidates with E002 grid reachability attached when available",
        "docker_required": False,
        "docker_reason": "This is a repository-local JSONL artifact transform and policy evaluation; Docker remains required for real detector/open-vocabulary implementations.",
        "seed_set": [61, 67, 71],
        "operation_order": [
            "candidate dropout with target-dropped rows retained as a separate denominator",
            "annotation-derived false-positive insertion",
            "score jitter and rank recomputation",
            "centroid jitter and localization metric recomputation",
            "policy evaluation with identity and localization metrics separated",
        ],
        "moderate_noise_parameters": {
            "score_jitter_sigma": 0.08,
            "target_drop_rate": 0.10,
            "non_target_candidate_drop_rate": 0.20,
            "min_false_positive_candidates": 1,
            "max_false_positive_candidates": 2,
            "centroid_planar_sigma_m": 0.18,
            "centroid_z_sigma_m": 0.04,
            "max_planar_jitter_m": 0.50,
            "max_z_jitter_m": 0.12,
            "preserve_at_least_one_candidate": True,
        },
        "required_denominators": [
            "all_rows",
            "target_retained_eval",
            "target_dropped_eval",
            "false_positive_added_eval",
            "target_rank_changed_eval",
            "target_jitter_within_threshold_eval",
            "target_jitter_exceeds_threshold_eval",
            "significant_moved|routine_fetch",
            "significant_moved|high_value_fetch",
            "low_motion_control",
        ],
        "primary_metrics": [
            "proposal_recall",
            "target_dropped_rate",
            "identity_proxy_SR",
            "localization_proxy_SR",
            "identity_localization_gap",
            "ExpectedSearchCost",
            "AttemptSPL proxy",
            "task utility",
            "stale old-location FP",
            "returned-unreachable event rate",
            "robustness delta against clean_annotation_oracle_v0",
        ],
        "must_report_boundaries": [
            "target-dropped rows are proposal-recall ceiling rows",
            "false positives that push target outside task budget",
            "identity-success/localization-failure rows caused by over-threshold centroid jitter",
            "grid/path costs are not recomputed after centroid jitter unless a later path-cost source is added",
        ],
        "claim_if_successful": "Controlled perception-like annotation noise robustness under combined dropout, false-positive, score/rank, and centroid perturbations.",
        "non_claims_even_if_successful": [
            "real RGB-D perception robustness",
            "open-vocabulary detector robustness",
            "real navigation SR/SPL",
            "deployable search policy",
            "natural-language intention understanding",
        ],
        "readiness_basis": {
            "individual_profiles_complete": evidence["individual_controlled_profiles_complete"],
            "real_proposal_ready_rows": evidence["real_proposal_readiness"][
                "query_rows_with_real_rgbd_proposal_ready"
            ],
            "real_open_vocab_ready_rows": evidence["real_proposal_readiness"][
                "query_rows_with_real_open_vocab_proposal_ready"
            ],
        },
    }


def build_real_proposal_requirements(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "route_id": "dockerized_real_proposal_route",
        "status": "blocked_not_selected_as_immediate_next",
        "docker_required": True,
        "current_blockers": evidence["real_proposal_readiness"]["blockers"],
        "minimum_unblock_requirements": [
            "Dockerfile or Docker image tag for detector/open-vocabulary proposal generation",
            "exact mounted dataset path and output path",
            "RGB-D frame, depth, pose, and scan-alignment route for the selected query denominator",
            "proposal output schema with label, confidence, mask or point support, centroid, and source frame ids",
            "matching/evaluation schema from proposals to 3DSSG object ids",
            "proposal recall, false-positive, localization-error, and stale-memory policy metrics",
            "seed/config record for detector thresholds and text prompts",
        ],
        "suggested_after": [
            NEXT_UNIT,
            "combined-noise claim-boundary analysis",
        ],
        "reason_for_deferral": "Current E001 query denominator has 0 real RGB-D proposal-ready rows, 0 real open-vocabulary proposal-ready rows, and 0 proposal output files; switching immediately would stop the E003 controlled-noise progression before the combined profile is measured.",
    }


def build_route_decision(
    evidence: dict[str, Any],
    combined_contract: dict[str, Any],
    real_requirements: dict[str, Any],
) -> dict[str, Any]:
    individual_ready = all(evidence["individual_controlled_profiles_complete"].values())
    real_ready = (
        evidence["real_proposal_readiness"]["query_rows_with_real_rgbd_proposal_ready"] > 0
        or evidence["real_proposal_readiness"]["query_rows_with_real_open_vocab_proposal_ready"] > 0
    )
    if individual_ready and not real_ready:
        status = "combined_controlled_route_selected"
        selected_route = "controlled_annotation_proxy_combined_stress"
        selected_profile = SELECTED_PROFILE
        next_action = NEXT_UNIT
    elif real_ready:
        status = "real_proposal_route_ready"
        selected_route = "dockerized_real_proposal_route"
        selected_profile = None
        next_action = "dockerized_real_proposal_pipeline_contract"
    else:
        status = "review_needed"
        selected_route = "blocked"
        selected_profile = None
        next_action = "repair_missing_individual_profile_boundaries"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": status,
        "selected_route": selected_route,
        "selected_profile": selected_profile,
        "next_action": next_action,
        "decision": {
            "immediate_next": selected_route,
            "deferred_route": real_requirements["route_id"],
            "deferred_route_status": real_requirements["status"],
        },
        "why_not_real_route_now": real_requirements["reason_for_deferral"] if not real_ready else None,
        "why_combined_now": [
            "Score/rank jitter, proposal dropout, false-positive contamination, and centroid jitter have separate executable boundaries.",
            "The combined profile is the smallest next step that tests interaction between proposal recall, distractors, rank noise, and localization noise.",
            "It preserves the current E001/E002 denominator and can be run as a repository-local artifact transform.",
            "Real detector/open-vocabulary claims remain blocked until Dockerized proposal generation and alignment are staged.",
        ],
        "claim_boundary": {
            "safe_if_next_unit_succeeds": combined_contract["claim_if_successful"],
            "non_claims_even_if_next_unit_succeeds": combined_contract[
                "non_claims_even_if_successful"
            ],
        },
        "evidence_snapshot": {
            "ready_rows": evidence["ready_rows"],
            "real_rgbd_proposal_ready_rows": evidence["real_proposal_readiness"][
                "query_rows_with_real_rgbd_proposal_ready"
            ],
            "real_open_vocab_proposal_ready_rows": evidence["real_proposal_readiness"][
                "query_rows_with_real_open_vocab_proposal_ready"
            ],
            "proposal_output_files_found": evidence["real_proposal_readiness"][
                "proposal_output_files_found"
            ],
            "individual_controlled_profiles_complete": evidence[
                "individual_controlled_profiles_complete"
            ],
        },
    }


def build_coverage(
    evidence: dict[str, Any],
    route_decision: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "status": route_decision["status"],
        "selected_route": route_decision["selected_route"],
        "selected_profile": route_decision["selected_profile"],
        "next_action": route_decision["next_action"],
        "ready_rows": evidence["ready_rows"],
        "individual_controlled_profiles_complete": evidence[
            "individual_controlled_profiles_complete"
        ],
        "query_rows_with_real_rgbd_proposal_ready": evidence["real_proposal_readiness"][
            "query_rows_with_real_rgbd_proposal_ready"
        ],
        "query_rows_with_real_open_vocab_proposal_ready": evidence["real_proposal_readiness"][
            "query_rows_with_real_open_vocab_proposal_ready"
        ],
        "proposal_output_files_found": evidence["real_proposal_readiness"][
            "proposal_output_files_found"
        ],
        "docker_required_for_selected_route": route_decision["selected_route"]
        == "dockerized_real_proposal_route",
        "docker_required_for_real_route": True,
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "uses_real_navigation": False,
        "outputs": {
            "input_evidence_summary": str(out_dir / "input_evidence_summary.json"),
            "route_decision": str(out_dir / "route_decision.json"),
            "combined_profile_contract": str(out_dir / "combined_profile_contract.json"),
            "real_proposal_route_requirements": str(out_dir / "real_proposal_route_requirements.json"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(
    evidence: dict[str, Any],
    route_decision: dict[str, Any],
    combined_contract: dict[str, Any],
    real_requirements: dict[str, Any],
    coverage: dict[str, Any],
    out_dir: Path,
) -> str:
    dropout = evidence["profile_boundary_evidence"]["dropout"]
    false_positive = evidence["profile_boundary_evidence"]["false_positive"]
    centroid = evidence["profile_boundary_evidence"]["centroid_jitter"]
    lines = [
        "# E003-M12 Combined-Noise Route Decision",
        "",
        "## Status",
        "",
        route_decision["status"],
        "",
        "## 사실",
        "",
        f"- Ready annotation-proxy query rows: {evidence['ready_rows']}",
        f"- Real RGB-D proposal-ready rows: {coverage['query_rows_with_real_rgbd_proposal_ready']}",
        f"- Real open-vocabulary proposal-ready rows: {coverage['query_rows_with_real_open_vocab_proposal_ready']}",
        f"- Proposal output files found: {coverage['proposal_output_files_found']}",
        f"- Selected route: `{route_decision['selected_route']}`",
        f"- Selected profile: `{route_decision['selected_profile']}`",
        f"- Next action: `{route_decision['next_action']}`",
        f"- Docker required for selected route: {coverage['docker_required_for_selected_route']}",
        f"- Docker required for real proposal route: {coverage['docker_required_for_real_route']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Input Evidence",
        "",
        f"- Dropout boundary rows: {dropout['boundary_rows']}",
        f"- Dropout target dropped rate: {dropout['target_dropped_rate']}",
        f"- False-positive boundary rows: {false_positive['boundary_rows']}",
        f"- False-positive target pushed-down rows: {false_positive['target_pushed_down_rows']}",
        f"- Centroid-jitter boundary rows: {centroid['boundary_rows']}",
        f"- Centroid-jitter target exceeds threshold rows: {centroid['target_jitter_exceeds_threshold_rows']}",
        f"- Centroid-jitter significant `routine_fetch` identity/localization `SR`: {centroid['significant_routine_task_identity_sr']} / {centroid['significant_routine_task_localization_sr']}",
        "",
        "## Selected Combined Profile",
        "",
        f"- Profile: `{combined_contract['profile_id']}`",
        f"- Seed set: {', '.join(str(seed) for seed in combined_contract['seed_set'])}",
        f"- Score jitter sigma: {combined_contract['moderate_noise_parameters']['score_jitter_sigma']}",
        f"- Target drop rate: {combined_contract['moderate_noise_parameters']['target_drop_rate']}",
        f"- Non-target drop rate: {combined_contract['moderate_noise_parameters']['non_target_candidate_drop_rate']}",
        f"- False-positive candidates per row: {combined_contract['moderate_noise_parameters']['min_false_positive_candidates']} to {combined_contract['moderate_noise_parameters']['max_false_positive_candidates']}",
        f"- Centroid planar sigma m: {combined_contract['moderate_noise_parameters']['centroid_planar_sigma_m']}",
        f"- Max planar jitter m: {combined_contract['moderate_noise_parameters']['max_planar_jitter_m']}",
        "",
        "## Real Proposal Route",
        "",
        f"- Status: `{real_requirements['status']}`",
        f"- Reason for deferral: {real_requirements['reason_for_deferral']}",
        "",
        "## 논문 주장",
        "",
        "- E003-M12 supports selecting `annotation_combined_moderate_v0` as the next controlled perception-like stress route.",
        "- E003-M12 supports keeping real RGB-D/open-vocabulary claims blocked until Dockerized proposal generation and alignment are staged.",
        "- E003-M12 does not itself support new metric results; it fixes the next implementation contract.",
        "",
        "## 에이전트 추론",
        "",
        "- The combined profile is the correct immediate next step because all individual controlled profiles now have separate boundaries.",
        "- Switching immediately to real proposals would require Dockerized detector generation and a new proposal-to-3DSSG matching contract, while current ready rows remain 0.",
        "- The combined profile should still be framed as annotation-proxy robustness, not real perception robustness.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M12. Continue to E003-M13 `annotation_combined_moderate_v0` implementation unless redirected to Dockerized real proposal staging.",
        "",
        "## Outputs",
        "",
        "- `input_evidence_summary.json`",
        "- `route_decision.json`",
        "- `combined_profile_contract.json`",
        "- `real_proposal_route_requirements.json`",
        "- `coverage.json`",
        "- `report.md`",
        "",
    ]
    return "\n".join(lines)


def run(
    m01_dir: Path,
    m05_dir: Path,
    m07_dir: Path,
    m09_dir: Path,
    m11_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    noise_plan = load_json(m01_dir / "noise_plan.json")
    route_m05 = load_json(m05_dir / "route_decision.json")
    dropout_claim = load_json(m07_dir / "claim_boundary.json")
    false_positive_claim = load_json(m09_dir / "claim_boundary.json")
    centroid_claim = load_json(m11_dir / "claim_boundary.json")
    centroid_coverage = load_json(m11_dir / "coverage.json")

    evidence = build_evidence_summary(
        noise_plan,
        route_m05,
        dropout_claim,
        false_positive_claim,
        centroid_claim,
        centroid_coverage,
    )
    combined_contract = build_combined_profile_contract(evidence)
    real_requirements = build_real_proposal_requirements(evidence)
    route_decision = build_route_decision(evidence, combined_contract, real_requirements)
    coverage = build_coverage(evidence, route_decision, out_dir)
    report = build_report(
        evidence,
        route_decision,
        combined_contract,
        real_requirements,
        coverage,
        out_dir,
    )

    write_json(out_dir / "input_evidence_summary.json", evidence)
    write_json(out_dir / "route_decision.json", route_decision)
    write_json(out_dir / "combined_profile_contract.json", combined_contract)
    write_json(out_dir / "real_proposal_route_requirements.json", real_requirements)
    write_json(out_dir / "coverage.json", coverage)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    return coverage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m01-dir", type=Path, default=DEFAULT_M01_DIR)
    parser.add_argument("--m05-dir", type=Path, default=DEFAULT_M05_DIR)
    parser.add_argument("--m07-dir", type=Path, default=DEFAULT_M07_DIR)
    parser.add_argument("--m09-dir", type=Path, default=DEFAULT_M09_DIR)
    parser.add_argument("--m11-dir", type=Path, default=DEFAULT_M11_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    coverage = run(args.m01_dir, args.m05_dir, args.m07_dir, args.m09_dir, args.m11_dir, args.out_dir)
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
