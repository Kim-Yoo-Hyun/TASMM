#!/usr/bin/env python3
"""Build the E008-M191 scale-up contract for source-pool acquisition."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"

VERSION = "e008_m191_source_pool_protected_confidence_scaleup_contract_v0"
READY_STATUS = "e008_m191_source_pool_protected_confidence_scaleup_contract_ready"
BLOCKED_STATUS = "e008_m191_source_pool_protected_confidence_scaleup_contract_blocked"
NEXT_UNIT = "E008-M192 source-pool protected-confidence scale denominator materialization"

M176_ROOT = EXP_ROOT / "artifacts" / "E008-M176_source_coverage_trigger_row_materialization_smoke_v0"
M177_ROOT = EXP_ROOT / "artifacts" / "E008-M177_source_pool_pose_render_plan_materialization_contract_v0"
M180_ROOT = EXP_ROOT / "artifacts" / "E008-M180_candidate_navmesh_source_readiness_validation_v0"
M184_ROOT = EXP_ROOT / "artifacts" / "E008-M184_docker_trajectory_execution_sr_spl_v0"
M188_ROOT = EXP_ROOT / "artifacts" / "E008-M188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_v0"
M190_ROOT = EXP_ROOT / "artifacts" / "E008-M190_source_pool_protected_confidence_method_boundary_scale_decision_v0"

OUT_ROOT = EXP_ROOT / "artifacts" / "E008-M191_source_pool_protected_confidence_scaleup_contract_v0"
DATA_OUT_ROOT = ROOT / "local_dataset" / "HM3D_navigation_bridge" / "E008-M191_source_pool_protected_confidence_scaleup_contract_v0"

SOURCE_POOL_COMPONENT = "fixed_budget_source_pool_candidate_generation"
SELECTED_METHOD = "source_pool_plus_detector_confidence_reachable_subset_v1"
PROTECTED_DEFAULT = "detector_confidence_reachable_subset_v0"
NO_SOURCE_POOL_BASELINE = "no_source_pool_detector_confidence_reachable_subset_v0"
NEGATIVE_PATH_ABLATION = "source_pool_path_cost_ascending_reachable_subset_v0"
NEGATIVE_TRANSITION_ABLATION = "source_pool_confidence_protected_transition_cost_policy_v1"
TASK_AGNOSTIC_CONTEXT_BASELINE = "task_agnostic_reobservation_source_pool_v0"

MAX_SOURCE_POSES_PER_REQUEST = 8
YAW_SAMPLES_PER_POSE = 4
BATCH_SIZE_EPISODES = 10


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


def sanitize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize(value) for value in payload]
    if isinstance(payload, float) and not math.isfinite(payload):
        return None
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(sanitize(row), sort_keys=True, allow_nan=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    value_f = finite_float(value)
    if value_f is not None:
        return f"{value_f:.6f}"
    return "null" if value is None else str(value)


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def unique_count(rows: list[dict[str, Any]], key: str) -> int:
    return len({str(row.get(key)) for row in rows if row.get(key) is not None})


def request_rows(trigger_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in trigger_rows if row.get("request_candidate_source_expansion") is True]
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("scene_key")),
            str(row.get("object_category")),
            str(row.get("adapter_episode_id")),
        ),
    )


def build_m192_seed_rows(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(requests):
        planned_source_pose_rows = MAX_SOURCE_POSES_PER_REQUEST
        planned_render_plan_rows = planned_source_pose_rows * YAW_SAMPLES_PER_POSE
        out.append(
            {
                "version": VERSION,
                "row_type": "m192_source_pool_scale_seed",
                "scale_denominator_id": "hm3d_val_mini_all_triggered_source_pool_scale_v1",
                "scale_request_uid": f"m191::{row.get('benchmark_row_uid')}",
                "source_trigger_row_uid": row.get("trigger_row_uid"),
                "benchmark_row_uid": row.get("benchmark_row_uid"),
                "adapter_episode_id": row.get("adapter_episode_id"),
                "scan_id": row.get("scan_id"),
                "scene_key": row.get("scene_key"),
                "object_category": row.get("object_category"),
                "trigger_count": row.get("trigger_count"),
                "trigger_ids": row.get("trigger_ids"),
                "top1_confidence": row.get("top1_confidence"),
                "mean_top5_confidence": row.get("mean_top5_confidence"),
                "top10_unique_coverage_keys": row.get("top10_unique_coverage_keys"),
                "candidate_rows_before_source_pool": row.get("candidate_rows"),
                "path_ready_candidate_rows_before_source_pool": row.get("path_ready_candidate_rows"),
                "source_ready_candidate_rows_before_source_pool": row.get("source_ready_candidate_rows"),
                "planned_source_pose_rows": planned_source_pose_rows,
                "planned_yaw_samples_per_pose": YAW_SAMPLES_PER_POSE,
                "planned_render_plan_rows": planned_render_plan_rows,
                "scale_batch_id": f"m192_batch_{index // BATCH_SIZE_EPISODES:02d}",
                "source_pose_budget_rule": "fixed_8_source_poses_per_triggered_episode",
                "protected_default_policy_id": PROTECTED_DEFAULT,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_source_placement": False,
                "uses_success_label_for_policy": False,
                "claim_boundary": "M191 seed row only; it does not render frames, run detectors, evaluate goals, or execute trajectories.",
            }
        )
    return out


def build_scale_denominator_rows(requests: list[dict[str, Any]], m177_cov: dict[str, Any], m180_cov: dict[str, Any]) -> list[dict[str, Any]]:
    categories = sorted({str(row.get("object_category")) for row in requests})
    scenes = sorted({str(row.get("scene_key")) for row in requests})
    return [
        {
            "version": VERSION,
            "denominator_id": "m177_m184_bounded_source_pool_smoke_8_episode_v0",
            "role": "completed_reference_smoke",
            "episode_rows": m177_cov.get("selected_request_rows"),
            "scene_count": len(m177_cov.get("selected_scenes") or []),
            "category_count": len(m177_cov.get("selected_categories") or []),
            "source_pose_rows": m177_cov.get("source_pose_rows"),
            "render_plan_rows": m177_cov.get("render_plan_rows"),
            "path_ready_candidate_rows": m180_cov.get("candidate_usable_for_path_smoke_rows"),
            "current_status": "executed_through_m184_and_interpreted_through_m190",
            "claim_use": "diagnostic_seed_only",
        },
        {
            "version": VERSION,
            "denominator_id": "hm3d_val_mini_all_triggered_source_pool_scale_v1",
            "role": "selected_first_scale_denominator",
            "episode_rows": len(requests),
            "scene_count": len(scenes),
            "category_count": len(categories),
            "scene_keys": scenes,
            "object_categories": categories,
            "source_pose_budget_per_episode": MAX_SOURCE_POSES_PER_REQUEST,
            "planned_source_pose_rows": len(requests) * MAX_SOURCE_POSES_PER_REQUEST,
            "planned_render_plan_rows": len(requests) * MAX_SOURCE_POSES_PER_REQUEST * YAW_SAMPLES_PER_POSE,
            "scale_batch_size_episodes": BATCH_SIZE_EPISODES,
            "scale_batch_count": math.ceil(len(requests) / BATCH_SIZE_EPISODES) if requests else 0,
            "current_status": "ready_for_m192_materialization",
            "claim_use": "first_scale_candidate_source_acquisition_eval",
        },
        {
            "version": VERSION,
            "denominator_id": "heldout_scene_or_external_navigation_transfer_v1",
            "role": "future_top_tier_requirement",
            "episode_rows": None,
            "scene_count": None,
            "category_count": None,
            "current_status": "not_materialized",
            "claim_use": "required_before_final_real_navigation_or_generality_claim",
        },
    ]


def build_source_pool_budget_rows(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scene_counts = Counter(str(row.get("scene_key")) for row in requests)
    category_counts = Counter(str(row.get("object_category")) for row in requests)
    rows: list[dict[str, Any]] = [
        {
            "version": VERSION,
            "budget_id": "global_fixed_budget_v1",
            "scope": "global",
            "triggered_episode_rows": len(requests),
            "source_pose_budget_per_episode": MAX_SOURCE_POSES_PER_REQUEST,
            "yaw_samples_per_pose": YAW_SAMPLES_PER_POSE,
            "planned_source_pose_rows": len(requests) * MAX_SOURCE_POSES_PER_REQUEST,
            "planned_render_plan_rows": len(requests) * MAX_SOURCE_POSES_PER_REQUEST * YAW_SAMPLES_PER_POSE,
            "reason": "Use the same per-request cap as M177 while removing the M177 top-8 priority selection for scale.",
        }
    ]
    for scene_key, count in sorted(scene_counts.items()):
        rows.append(
            {
                "version": VERSION,
                "budget_id": f"scene::{scene_key}",
                "scope": "scene",
                "scene_key": scene_key,
                "triggered_episode_rows": count,
                "planned_source_pose_rows": count * MAX_SOURCE_POSES_PER_REQUEST,
                "planned_render_plan_rows": count * MAX_SOURCE_POSES_PER_REQUEST * YAW_SAMPLES_PER_POSE,
            }
        )
    for category, count in sorted(category_counts.items()):
        rows.append(
            {
                "version": VERSION,
                "budget_id": f"category::{category}",
                "scope": "category",
                "object_category": category,
                "triggered_episode_rows": count,
                "planned_source_pose_rows": count * MAX_SOURCE_POSES_PER_REQUEST,
                "planned_render_plan_rows": count * MAX_SOURCE_POSES_PER_REQUEST * YAW_SAMPLES_PER_POSE,
            }
        )
    return rows


def build_baseline_ablation_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "policy_or_baseline_id": SELECTED_METHOD,
            "role": "selected_method_for_scale",
            "candidate_pool": "current_candidates_plus_m192_source_pool_candidates",
            "ranking_rule": "detector_confidence_reachable_subset",
            "required": True,
            "positive_claim_allowed_now": False,
            "expected_test": "Does source-pool acquisition improve recovery under the same protected confidence order?",
        },
        {
            "version": VERSION,
            "policy_or_baseline_id": NO_SOURCE_POOL_BASELINE,
            "role": "primary_ablation",
            "candidate_pool": "current_candidates_only",
            "ranking_rule": "detector_confidence_reachable_subset",
            "required": True,
            "positive_claim_allowed_now": False,
            "expected_test": "Separates candidate-source acquisition gains from ranking gains.",
        },
        {
            "version": VERSION,
            "policy_or_baseline_id": PROTECTED_DEFAULT,
            "role": "safe_execution_default",
            "candidate_pool": "source_pool_candidates_when_available",
            "ranking_rule": "detector_confidence_reachable_subset",
            "required": True,
            "positive_claim_allowed_now": False,
            "expected_test": "Preserves detector-confidence as the protected naive baseline.",
        },
        {
            "version": VERSION,
            "policy_or_baseline_id": NEGATIVE_PATH_ABLATION,
            "role": "negative_ablation_optional",
            "candidate_pool": "current_candidates_plus_m192_source_pool_candidates",
            "ranking_rule": "path_cost_ascending",
            "required": False,
            "positive_claim_allowed_now": False,
            "expected_test": "Confirms that path-cost-only ranking remains a negative ablation unless it beats protected confidence.",
        },
        {
            "version": VERSION,
            "policy_or_baseline_id": NEGATIVE_TRANSITION_ABLATION,
            "role": "negative_ablation_optional",
            "candidate_pool": "current_candidates_plus_m192_source_pool_candidates",
            "ranking_rule": "confidence_bin_then_transition_cost",
            "required": False,
            "positive_claim_allowed_now": False,
            "expected_test": "Tracks M188/M189 transition repair failure on the scale denominator if needed.",
        },
        {
            "version": VERSION,
            "policy_or_baseline_id": TASK_AGNOSTIC_CONTEXT_BASELINE,
            "role": "future_human_intent_ablation",
            "candidate_pool": "current_candidates_plus_m192_source_pool_candidates",
            "ranking_rule": "context_agnostic_source_pool_trigger",
            "required": False,
            "positive_claim_allowed_now": False,
            "expected_test": "Required only if human intent is re-promoted as a main claim.",
        },
    ]


def build_metric_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "m195_proxy_gate_before_docker_trajectory",
            "metric_scope": "leakage_safe_proxy",
            "primary_metrics": ["primary_proxy_SR", "primary_proxy_SPL", "CandidateVisits", "first_hit_rank"],
            "pass_condition": "selected source-pool protected-confidence has higher proxy SR than no-source-pool baseline, or equal SR with higher proxy SPL and no new shared leakage failures",
            "fail_condition": "no SR gain and proxy SPL lower than no-source-pool baseline",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
        {
            "version": VERSION,
            "gate_id": "m197_docker_trajectory_gate",
            "metric_scope": "executed_navigation",
            "primary_metrics": ["SR", "SPL", "PathLengthM", "CandidateVisits", "failure_type"],
            "pass_condition": "selected source-pool protected-confidence has SR >= no-source-pool baseline and SPL not worse; positive claim requires SR or SPL improvement with failure reduction",
            "fail_condition": "source-pool adds candidates but lowers SPL without SR/failure-reduction gain",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
        {
            "version": VERSION,
            "gate_id": "top_tier_claim_gate",
            "metric_scope": "paper_claim",
            "primary_metrics": ["heldout_SR", "heldout_SPL", "external_baseline_delta", "failure_taxonomy"],
            "pass_condition": "scale denominator plus heldout/external baseline route support the same mechanism-level claim",
            "fail_condition": "gain is only on the current 30-episode val_mini source or disappears against stronger baselines",
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
    ]


def build_leakage_audit_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("episode_start_pose", "ObjectNav episode start pose for route execution"),
        ("scene_and_navmesh", "scene geometry and navigation mesh"),
        ("policy_visible_current_candidates", "current detector/map candidates already available before source-pool expansion"),
        ("m176_trigger_features", "confidence/source-coverage/path-ready trigger features"),
        ("source_pool_rgbd_frames", "RGB-D frames rendered from target-free source-pool poses"),
        ("detector_confidence_and_coordinates", "open-vocabulary detector outputs and snapped coordinates"),
    ]
    blocked = [
        ("objectnav_goal_position", "not allowed for source placement, ranking, or candidate filtering"),
        ("objectnav_viewpoint_positions", "not allowed for source placement, ranking, or candidate filtering"),
        ("success_label_or_eval_hit", "not allowed before metric computation"),
        ("posthoc_threshold_from_eval", "no threshold may be selected using eval success"),
        ("m188_or_m189_eval_label_for_policy", "diagnostic-only labels cannot alter M191/M192 policy inputs"),
    ]
    rows: list[dict[str, Any]] = []
    for input_id, reason in allowed:
        rows.append(
            {
                "version": VERSION,
                "input_id": input_id,
                "input_status": "allowed",
                "reason": reason,
                "must_audit": True,
            }
        )
    for input_id, reason in blocked:
        rows.append(
            {
                "version": VERSION,
                "input_id": input_id,
                "input_status": "blocked",
                "reason": reason,
                "must_audit": True,
            }
        )
    return rows


def build_command_ledger_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "command_id": "m191_reproduce_contract",
            "stage": "contract",
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/plan_m191_source_pool_protected_confidence_scaleup_contract.py",
            "output_path": str(OUT_ROOT),
            "expected_files": ["coverage.json", "m192_materialization_seed_rows.jsonl", "scale_denominator_rows.jsonl"],
            "long_job": False,
            "status": "ready",
        },
        {
            "version": VERSION,
            "command_id": "m192_materialize_scale_denominator",
            "stage": "next_unit",
            "working_directory": str(ROOT),
            "command": "python experiments/E008_real_navigation_benchmark/tools/run_m192_source_pool_protected_confidence_scale_denominator_materialization.py",
            "output_path": "experiments/E008_real_navigation_benchmark/artifacts/E008-M192_source_pool_protected_confidence_scale_denominator_materialization_v0/",
            "expected_files": ["coverage.json", "source_pool_scale_request_rows.jsonl", "source_pool_observation_pose_rows.jsonl", "source_pool_render_plan_rows.jsonl"],
            "long_job": False,
            "status": "planned_next",
        },
        {
            "version": VERSION,
            "command_id": "future_render_tmux_template",
            "stage": "future_long_job_template",
            "working_directory": str(ROOT),
            "command": "tmux new -d -s e008_m19x_source_pool_scale_render 'cd /home/yoohyun/research2 && <render-command> > logs/<timestamp>_e008_m19x_source_pool_scale_render.log 2>&1'",
            "output_path": "local_dataset/HM3D_navigation_bridge/<future_source_pool_scale_render>/",
            "expected_files": ["rendered RGB-D frames", "verification coverage"],
            "long_job": True,
            "status": "template_only",
        },
        {
            "version": VERSION,
            "command_id": "future_detector_tmux_template",
            "stage": "future_long_job_template",
            "working_directory": str(ROOT),
            "command": "tmux new -d -s e008_m19x_source_pool_scale_detector 'cd /home/yoohyun/research2 && <detector-command> > logs/<timestamp>_e008_m19x_source_pool_scale_detector.log 2>&1'",
            "output_path": "local_dataset/HM3D_navigation_bridge/<future_source_pool_scale_detector>/",
            "expected_files": ["detector prediction rows", "coordinate candidate rows", "verification coverage"],
            "long_job": True,
            "status": "template_only",
        },
        {
            "version": VERSION,
            "command_id": "future_docker_trajectory_template",
            "stage": "future_docker_execution_template",
            "working_directory": str(ROOT),
            "command": "docker run --rm --gpus all --user 1001:1001 -e HOME=/tmp -v /home/yoohyun/research3/local_dataset/data:/data:ro -v /home/yoohyun/research2:/work -w /work research3/habitat-h001:20260508-calib-artifacts bash -lc \"micromamba run -n base python experiments/E008_real_navigation_benchmark/tools/run_m19x_source_pool_scale_trajectory_execution.py --contract <contract> --out-root <out-root> --derived-out-root <derived-out-root>\"",
            "output_path": "experiments/E008_real_navigation_benchmark/artifacts/<future_source_pool_scale_trajectory>/",
            "expected_files": ["coverage.json", "trajectory metric rows", "leakage audit rows"],
            "long_job": True,
            "status": "template_only",
        },
    ]


def build_readiness_gate_rows(input_ready: bool, requests: list[dict[str, Any]], m190_cov: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "gate_id": "input_artifacts_ready",
            "status": "pass" if input_ready else "fail",
            "reason": "M176/M177/M180/M184/M188/M190 inputs are ready." if input_ready else "One or more required inputs are missing or not ready.",
        },
        {
            "version": VERSION,
            "gate_id": "scale_denominator_nonempty",
            "status": "pass" if len(requests) >= 30 else "warning",
            "reason": f"{len(requests)} triggered source-pool request rows selected for M192.",
        },
        {
            "version": VERSION,
            "gate_id": "method_boundary_respected",
            "status": "pass" if m190_cov.get("protected_detector_confidence_execution_default") and not m190_cov.get("trajectory_execution_now") else "fail",
            "reason": "M190 requires protected detector confidence and blocks immediate trajectory execution.",
        },
        {
            "version": VERSION,
            "gate_id": "m192_materialization_ready",
            "status": "pass" if input_ready and bool(requests) else "fail",
            "reason": "M191 seed rows are ready for source pose/render-plan materialization.",
        },
        {
            "version": VERSION,
            "gate_id": "long_job_launch_now",
            "status": "fail",
            "reason": "M191 is a contract-only unit; render, detector, and trajectory execution must wait for M192/M193+.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim": "source-pool protected-confidence scale-up is ready to materialize",
            "allowed": True,
            "boundary": "Allowed as a contract/materialization-readiness statement only.",
        },
        {
            "version": VERSION,
            "claim": "source-pool acquisition improves real navigation",
            "allowed": False,
            "boundary": "Requires M192+ materialization, proxy gate, Docker trajectory execution, and no-source-pool ablation.",
        },
        {
            "version": VERSION,
            "claim": "transition-cost repair improves search/navigation",
            "allowed": False,
            "boundary": "M188-M190 reject this as a positive claim; keep only as a negative ablation.",
        },
        {
            "version": VERSION,
            "claim": "final real RGB-D/open-vocabulary robustness",
            "allowed": False,
            "boundary": "Requires scale, heldout transfer, and external proposal/map baselines.",
        },
        {
            "version": VERSION,
            "claim": "human intent as a main contribution",
            "allowed": False,
            "boundary": "E006-M08 remains negative; task context stays secondary unless redesigned and revalidated.",
        },
    ]


def build_reviewer_defense_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "question": "How will M191 avoid turning into detector-confidence ranking only?",
            "answer": "The primary comparison is same ranking rule with and without source-pool candidate acquisition.",
            "evidence_required": "M192+ must materialize `no_source_pool_detector_confidence_reachable_subset_v0` and `source_pool_plus_detector_confidence_reachable_subset_v1` on the same denominator.",
        },
        {
            "version": VERSION,
            "question": "Why not continue transition-cost repair?",
            "answer": "M188/M189 already show it ties recovery and loses proxy SPL; M191 treats it only as optional negative ablation.",
            "evidence_required": "Do not launch transition repair trajectories unless a precommitted proxy gate reverses the failure.",
        },
        {
            "version": VERSION,
            "question": "Why is this semantic mapping?",
            "answer": "The defended component is a map-level source-coverage/re-observation decision that changes what evidence enters the semantic memory, not merely how a fixed list is sorted.",
            "evidence_required": "Show source-pool acquisition changes candidate availability and failure taxonomy under blocked eval-goal inputs.",
        },
        {
            "version": VERSION,
            "question": "What would still block top-tier claims?",
            "answer": "A single local `HM3D val_mini` source is not enough; heldout scene/category transfer and external navigation/map baselines are still required.",
            "evidence_required": "M191 records this as a future denominator and baseline requirement, not current evidence.",
        },
    ]


def build_route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "decision_id": "selected_next_unit",
            "selected_next_unit": NEXT_UNIT,
            "trajectory_execution_now": False,
            "long_job_launch_now": False,
            "reason": "Scale-up must first materialize source-pool request/source-pose/render-plan rows under the M191 contract.",
        },
        {
            "version": VERSION,
            "decision_id": "method_family_for_scale",
            "selected_method_family": "source_pool_acquisition_plus_protected_confidence_execution",
            "selected_method_id": SELECTED_METHOD,
            "primary_ablation_id": NO_SOURCE_POOL_BASELINE,
            "safe_execution_default": PROTECTED_DEFAULT,
            "reason": "The next scale test should isolate acquisition gain from ranking changes.",
        },
    ]


def write_report(
    coverage: dict[str, Any],
    denominator_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> None:
    report = f"""# E008-M191 Source-Pool Protected-Confidence Scale-Up Contract

Generated: {datetime.now().isoformat(timespec="seconds")}

## Status

- Status: `{coverage["status"]}`
- Selected scale denominator: `hm3d_val_mini_all_triggered_source_pool_scale_v1`
- Triggered episode rows: {coverage["scale_triggered_episode_rows"]}
- Planned source poses / render rows: {coverage["planned_source_pose_rows"]} / {coverage["planned_render_plan_rows"]}
- Selected method: `{SELECTED_METHOD}`
- Primary ablation: `{NO_SOURCE_POOL_BASELINE}`
- Safe execution default: `{PROTECTED_DEFAULT}`
- Selected next unit: {coverage["selected_next_unit"]}

## 사실

M191 is a contract-only unit. It reads M176-M190 artifacts, writes M192 seed rows, fixes scale denominator and comparison rules, and launches no render, detector, or Docker trajectory job.

## Scale Denominators

{table(denominator_rows, ["denominator_id", "role", "episode_rows", "scene_count", "category_count", "planned_source_pose_rows", "planned_render_plan_rows", "current_status"])}

## Baselines And Ablations

{table(baseline_rows, ["policy_or_baseline_id", "role", "candidate_pool", "ranking_rule", "required"])}

## Metric Gates

{table(metric_rows, ["gate_id", "metric_scope", "pass_condition", "fail_condition"])}

## Readiness Gates

{table(readiness_rows, ["gate_id", "status", "reason"])}

## Route Decision

{table(route_rows, ["decision_id", "selected_next_unit", "trajectory_execution_now", "long_job_launch_now", "reason"])}

## 논문 주장

M191 supports only a readiness/contract claim: the next valid experiment should compare source-pool acquisition plus protected detector confidence against the no-source-pool detector-confidence ablation on the same scale denominator. It does not support final real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, or a human-intent main claim.

## 에이전트 추론

The principle-driven scale-up is acquisition-first. M190 rejected local reranking as the main method, so M191 fixes a comparison that can show whether semantic-map source acquisition changes candidate availability and downstream failures under the same protected ranking rule.
"""
    write_text(OUT_ROOT / "report.md", report)


def main() -> None:
    m176_cov = read_json(M176_ROOT / "coverage.json")
    m177_cov = read_json(M177_ROOT / "coverage.json")
    m180_cov = read_json(M180_ROOT / "coverage.json")
    m184_cov = read_json(M184_ROOT / "coverage.json")
    m188_cov = read_json(M188_ROOT / "coverage.json")
    m190_cov = read_json(M190_ROOT / "coverage.json")
    trigger_rows = read_jsonl(M176_ROOT / "source_coverage_trigger_rows.jsonl")
    requests = request_rows(trigger_rows)

    input_ready = all(
        [
            m176_cov.get("status") == "e008_m176_source_coverage_trigger_row_materialization_smoke_ready",
            m177_cov.get("status") == "e008_m177_source_pool_pose_render_plan_materialization_contract_ready",
            m180_cov.get("status") == "e008_m180_candidate_navmesh_source_readiness_validation_ready",
            m184_cov.get("status") == "e008_m184_docker_trajectory_execution_sr_spl_ready",
            m188_cov.get("status") == "e008_m188_source_pool_repaired_policy_leakage_safe_goal_evaluation_proxy_ready",
            m190_cov.get("status") == "e008_m190_source_pool_protected_confidence_method_boundary_scale_decision_ready",
            bool(requests),
        ]
    )

    seed_rows = build_m192_seed_rows(requests)
    denominator_rows = build_scale_denominator_rows(requests, m177_cov, m180_cov)
    budget_rows = build_source_pool_budget_rows(requests)
    baseline_rows = build_baseline_ablation_rows()
    metric_rows = build_metric_gate_rows()
    leakage_rows = build_leakage_audit_contract_rows()
    command_rows = build_command_ledger_rows()
    readiness_rows = build_readiness_gate_rows(input_ready, requests, m190_cov)
    claim_rows = build_claim_boundary_rows()
    reviewer_rows = build_reviewer_defense_rows()
    route_rows = build_route_decision_rows()

    planned_source_pose_rows = len(requests) * MAX_SOURCE_POSES_PER_REQUEST
    planned_render_plan_rows = planned_source_pose_rows * YAW_SAMPLES_PER_POSE
    coverage = {
        "version": VERSION,
        "status": READY_STATUS if input_ready else BLOCKED_STATUS,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_m176_status": m176_cov.get("status"),
        "input_m177_status": m177_cov.get("status"),
        "input_m180_status": m180_cov.get("status"),
        "input_m184_status": m184_cov.get("status"),
        "input_m188_status": m188_cov.get("status"),
        "input_m190_status": m190_cov.get("status"),
        "input_artifacts_ready": input_ready,
        "selected_scale_denominator_id": "hm3d_val_mini_all_triggered_source_pool_scale_v1",
        "scale_triggered_episode_rows": len(requests),
        "scale_scene_count": unique_count(requests, "scene_key"),
        "scale_category_count": unique_count(requests, "object_category"),
        "scale_batch_size_episodes": BATCH_SIZE_EPISODES,
        "scale_batch_count": math.ceil(len(requests) / BATCH_SIZE_EPISODES) if requests else 0,
        "source_pose_budget_per_episode": MAX_SOURCE_POSES_PER_REQUEST,
        "yaw_samples_per_pose": YAW_SAMPLES_PER_POSE,
        "planned_source_pose_rows": planned_source_pose_rows,
        "planned_render_plan_rows": planned_render_plan_rows,
        "selected_method_id": SELECTED_METHOD,
        "kept_method_component": SOURCE_POOL_COMPONENT,
        "primary_ablation_id": NO_SOURCE_POOL_BASELINE,
        "safe_execution_default_policy_id": PROTECTED_DEFAULT,
        "protected_m184_docker_sr": m190_cov.get("protected_docker_sr"),
        "protected_m184_docker_spl": m190_cov.get("protected_docker_spl"),
        "source_pool_smoke_proxy_sr": m188_cov.get("protected_primary_proxy_sr"),
        "source_pool_smoke_proxy_spl": m188_cov.get("protected_primary_spl_proxy_mean"),
        "m192_materialization_ready_next": input_ready,
        "render_or_detector_long_job_launch_now": False,
        "docker_trajectory_execution_now": False,
        "real_navigation_sr_spl_ready": False,
        "final_rgbd_open_vocabulary_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "selected_next_unit": NEXT_UNIT,
    }

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    write_json(OUT_ROOT / "coverage.json", coverage)
    write_json(DATA_OUT_ROOT / "coverage.json", coverage)
    write_jsonl(OUT_ROOT / "scale_denominator_rows.jsonl", denominator_rows)
    write_jsonl(OUT_ROOT / "m192_materialization_seed_rows.jsonl", seed_rows)
    write_jsonl(DATA_OUT_ROOT / "m192_materialization_seed_rows.jsonl", seed_rows)
    write_jsonl(OUT_ROOT / "source_pool_budget_rows.jsonl", budget_rows)
    write_jsonl(OUT_ROOT / "baseline_ablation_rows.jsonl", baseline_rows)
    write_jsonl(OUT_ROOT / "metric_gate_rows.jsonl", metric_rows)
    write_jsonl(OUT_ROOT / "leakage_audit_contract_rows.jsonl", leakage_rows)
    write_jsonl(OUT_ROOT / "command_ledger_rows.jsonl", command_rows)
    write_jsonl(OUT_ROOT / "readiness_gate_rows.jsonl", readiness_rows)
    write_jsonl(OUT_ROOT / "claim_boundary_rows.jsonl", claim_rows)
    write_jsonl(OUT_ROOT / "reviewer_defense_rows.jsonl", reviewer_rows)
    write_jsonl(OUT_ROOT / "route_decision_rows.jsonl", route_rows)
    write_report(coverage, denominator_rows, baseline_rows, metric_rows, readiness_rows, route_rows)

    print(json.dumps(coverage, indent=2, sort_keys=True, allow_nan=False))
    if not input_ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
