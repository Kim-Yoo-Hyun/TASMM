#!/usr/bin/env python3
"""Decide the evaluation route after M93 two-branch repair materialization."""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
M91_DIR = EXP_ROOT / "artifacts" / "E008-M91_source_gap_target_coverage_candidate_source_failure_diagnosis_v0"
M93_DIR = EXP_ROOT / "artifacts" / "E008-M93_source_gap_two_branch_repair_row_materialization_smoke_v0"
ARTIFACT_DIR = (
    EXP_ROOT
    / "artifacts"
    / "E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0"
)
DATA_OUT_DIR = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M94_source_gap_two_branch_repair_evaluation_route_decision_v0"
)

VERSION = "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_v0"
READY_STATUS = "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_ready"
BLOCKED_STATUS = "e008_m94_source_gap_two_branch_repair_evaluation_route_decision_blocked"
COVERAGE_NEXT_UNIT = "E008-M95 coverage-expansion render/detector launcher adaptation contract"
CAP_NEXT_UNIT = "E008-M95 cap-threshold probe loss-safe goal-evaluation contract"
STOP_NEXT_UNIT = "record source-gap repair boundary and pause E008 expansion"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finite_float(value: object) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def first_rank(rows: list[dict[str, Any]], key: str) -> int | None:
    ranks = [int(row["probe_rank"]) for row in rows if row.get(key) is True and row.get("probe_rank") is not None]
    return min(ranks) if ranks else None


def min_finite(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [finite_float(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return min(values) if values else None


def build_cap_probe_eval_rows(
    cap_probe_rows: list[dict[str, Any]],
    pre_cap_eval_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_by_uid = {str(row.get("raw_candidate_uid")): row for row in pre_cap_eval_rows}
    output: list[dict[str, Any]] = []
    for probe in sorted(
        cap_probe_rows,
        key=lambda row: (
            str(row.get("adapter_episode_id")),
            str(row.get("probe_policy_id")),
            int(row.get("probe_rank") or 10**9),
        ),
    ):
        eval_row = eval_by_uid.get(str(probe.get("raw_candidate_uid")), {})
        output.append(
            {
                "version": VERSION,
                "row_type": "cap_probe_eval",
                "adapter_episode_id": probe.get("adapter_episode_id"),
                "scan_id": probe.get("scan_id"),
                "scene_key": probe.get("scene_key"),
                "object_category": probe.get("object_category"),
                "branch_id": probe.get("branch_id"),
                "probe_policy_id": probe.get("probe_policy_id"),
                "probe_role": probe.get("probe_role"),
                "candidate_budget": probe.get("candidate_budget"),
                "probe_rank": probe.get("probe_rank"),
                "pre_cap_confidence_rank": probe.get("pre_cap_confidence_rank"),
                "raw_candidate_uid": probe.get("raw_candidate_uid"),
                "frame_id": probe.get("frame_id"),
                "confidence": probe.get("confidence"),
                "selection_score": probe.get("selection_score"),
                "path_metadata_available": probe.get("path_metadata_available"),
                "path_ready": probe.get("path_ready"),
                "source_to_candidate_path_cost_m": probe.get("source_to_candidate_path_cost_m"),
                "eval_join_ready": bool(eval_row),
                "hit_any_viewpoint_xz_1p0": eval_row.get("hit_any_viewpoint_xz_1p0"),
                "hit_any_viewpoint_xz_1p5": eval_row.get("hit_any_viewpoint_xz_1p5"),
                "hit_goal_xz_1p0": eval_row.get("hit_goal_xz_1p0"),
                "candidate_to_nearest_eval_viewpoint_xz_m": eval_row.get("candidate_to_nearest_eval_viewpoint_xz_m"),
                "candidate_to_eval_goal_xz_m": eval_row.get("candidate_to_eval_goal_xz_m"),
                "inside_final_label_cap_by_confidence": eval_row.get("inside_final_label_cap_by_confidence"),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": bool(eval_row),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "policy_input_allowed": False,
                "rank_uses_eval_distance": False,
                "fixed_order_from_m93": True,
                "claim_boundary": (
                    "M94 joins M93 fixed probe rows to M91 eval-only distances after ranking; "
                    "these fields are metrics, not policy inputs."
                ),
            }
        )
    return output


def build_cap_policy_metric_rows(eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eval_rows:
        grouped[(str(row.get("adapter_episode_id")), str(row.get("probe_policy_id")))].append(row)

    output: list[dict[str, Any]] = []
    for (episode, policy_id), rows in sorted(grouped.items()):
        rows_sorted = sorted(rows, key=lambda row: int(row.get("probe_rank") or 10**9))
        output.append(
            {
                "version": VERSION,
                "row_type": "cap_probe_policy_metric",
                "adapter_episode_id": episode,
                "scan_id": rows_sorted[0].get("scan_id"),
                "scene_key": rows_sorted[0].get("scene_key"),
                "object_category": rows_sorted[0].get("object_category"),
                "branch_id": rows_sorted[0].get("branch_id"),
                "probe_policy_id": policy_id,
                "candidate_budget": rows_sorted[0].get("candidate_budget"),
                "candidate_rows": len(rows_sorted),
                "eval_joined_rows": sum(1 for row in rows_sorted if row.get("eval_join_ready")),
                "primary_any_viewpoint_xz_1p0_hit": any(row.get("hit_any_viewpoint_xz_1p0") is True for row in rows_sorted),
                "relaxed_any_viewpoint_xz_1p5_hit": any(row.get("hit_any_viewpoint_xz_1p5") is True for row in rows_sorted),
                "goal_xz_1p0_hit": any(row.get("hit_goal_xz_1p0") is True for row in rows_sorted),
                "primary_any_viewpoint_xz_1p0_first_rank": first_rank(rows_sorted, "hit_any_viewpoint_xz_1p0"),
                "relaxed_any_viewpoint_xz_1p5_first_rank": first_rank(rows_sorted, "hit_any_viewpoint_xz_1p5"),
                "goal_xz_1p0_first_rank": first_rank(rows_sorted, "hit_goal_xz_1p0"),
                "best_any_viewpoint_xz_m": min_finite(rows_sorted, "candidate_to_nearest_eval_viewpoint_xz_m"),
                "best_goal_xz_m": min_finite(rows_sorted, "candidate_to_eval_goal_xz_m"),
                "path_ready_rows": sum(1 for row in rows_sorted if row.get("path_ready") is True),
                "replacement_allowed_now": False,
                "requires_budget_loss_eval": True,
                "supports_source_gap_recovery_primary": any(row.get("hit_any_viewpoint_xz_1p0") is True for row in rows_sorted),
                "supports_relaxed_threshold_diagnostic": any(row.get("hit_any_viewpoint_xz_1p5") is True for row in rows_sorted),
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "Cap probe metrics are post-hoc diagnostics; they do not authorize top-k replacement or trajectory promotion.",
            }
        )
    return output


def build_branch_route_decision_rows(
    m93_coverage: dict[str, Any],
    assignment_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    render_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    cap_metric_rows: list[dict[str, Any]],
    long_job_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str, str]:
    cap_primary = any(row.get("primary_any_viewpoint_xz_1p0_hit") is True for row in cap_metric_rows)
    cap_relaxed = any(row.get("relaxed_any_viewpoint_xz_1p5_hit") is True for row in cap_metric_rows)
    coverage_ready = (
        m93_coverage.get("status") == "e008_m93_source_gap_two_branch_repair_row_materialization_smoke_ready"
        and len(coverage_rows) >= 12
        and len(render_rows) >= 96
        and len(manifest_rows) >= 1
    )
    long_job_exact_command_ready = all(bool(row.get("exact_command")) for row in long_job_rows) if long_job_rows else False

    if cap_primary:
        selected_route = "cap_threshold_probe_eval_first"
        selected_next = CAP_NEXT_UNIT
    elif coverage_ready:
        selected_route = "coverage_expansion_launcher_adaptation_first"
        selected_next = COVERAGE_NEXT_UNIT
    else:
        selected_route = "stop_and_record_boundary"
        selected_next = STOP_NEXT_UNIT

    rows = [
        {
            "version": VERSION,
            "row_type": "branch_route_decision",
            "branch_id": "cap_threshold_rescue_branch",
            "route_id": "cap_threshold_probe_eval_first",
            "selected": selected_route == "cap_threshold_probe_eval_first",
            "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in cap_metric_rows),
            "primary_supported": cap_primary,
            "relaxed_supported": cap_relaxed,
            "replacement_allowed_now": False,
            "reason": (
                "Cap probe contains a primary 1.0m target-near hit; evaluate loss-safe replacement next."
                if cap_primary
                else "Cap probe does not produce a primary 1.0m source-gap recovery; keep as diagnostic."
            ),
            "next_unit_if_selected": CAP_NEXT_UNIT,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
        {
            "version": VERSION,
            "row_type": "branch_route_decision",
            "branch_id": "coverage_expansion_branch",
            "route_id": "coverage_expansion_launcher_adaptation_first",
            "selected": selected_route == "coverage_expansion_launcher_adaptation_first",
            "coverage_observation_rows": len(coverage_rows),
            "coverage_render_rows": len(render_rows),
            "coverage_detector_manifest_rows": len(manifest_rows),
            "long_job_rows": len(long_job_rows),
            "long_job_exact_command_ready": long_job_exact_command_ready,
            "reason": (
                "Coverage branch is the only branch with a remaining absent-target-coverage case; "
                "M93 rows are ready, but launcher commands must be adapted from the M84/M85 hardcoded path before background execution."
            )
            if coverage_ready
            else "Coverage branch rows are not ready enough for launcher adaptation.",
            "next_unit_if_selected": COVERAGE_NEXT_UNIT,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
        {
            "version": VERSION,
            "row_type": "branch_route_decision",
            "branch_id": "global",
            "route_id": "stop_and_record_boundary",
            "selected": selected_route == "stop_and_record_boundary",
            "reason": "Use only if neither cap probe nor coverage branch rows support a useful next evaluation route.",
            "next_unit_if_selected": STOP_NEXT_UNIT,
            "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        },
    ]
    return rows, selected_route, selected_next


def build_readiness_gate_rows(
    m93_coverage: dict[str, Any],
    cap_eval_rows: list[dict[str, Any]],
    cap_metric_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "m93_ready",
            "gate_pass": m93_coverage.get("status") == "e008_m93_source_gap_two_branch_repair_row_materialization_smoke_ready",
            "observed": m93_coverage.get("status"),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "cap_probe_eval_join_ready",
            "gate_pass": len(cap_eval_rows) >= 24 and all(row.get("eval_join_ready") for row in cap_eval_rows),
            "observed": {
                "cap_eval_rows": len(cap_eval_rows),
                "eval_joined_rows": sum(1 for row in cap_eval_rows if row.get("eval_join_ready")),
            },
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "cap_metric_rows_ready",
            "gate_pass": len(cap_metric_rows) >= 1,
            "observed": len(cap_metric_rows),
        },
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": "exactly_one_next_route_selected",
            "gate_pass": sum(1 for row in branch_rows if row.get("selected")) == 1,
            "observed": Counter(str(row.get("selected")) for row in branch_rows),
        },
    ]


def build_claim_boundary_rows(selected_route: str) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "cap_threshold_probe_recovery",
            "support_status": "supported_for_primary_metric" if selected_route == "cap_threshold_probe_eval_first" else "not_supported_for_primary_metric",
            "allowed_claim": "M94 can say whether fixed M93 cap probes contain a target-near candidate under eval-only metrics.",
            "blocked_claims": [
                "cap branch is a deployable replacement policy",
                "cap branch improves trajectory SR/SPL",
                "cap branch generalizes beyond one source-gap case",
            ],
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "coverage_expansion_recovery",
            "support_status": "input_ready_only",
            "allowed_claim": "M93/M94 can say coverage-expansion rows are ready for a future render/detector launcher.",
            "blocked_claims": [
                "coverage branch recovers target candidates",
                "coverage branch improves source-gap success",
                "final real RGB-D/open-vocabulary robustness is solved",
            ],
        },
        {
            "version": VERSION,
            "row_type": "claim_boundary",
            "claim": "real_navigation_sr_spl",
            "support_status": "blocked",
            "allowed_claim": "None at M94.",
            "blocked_claims": [
                "real navigation SR/SPL improves",
                "deployable search policy is validated",
                "human intent is a main contribution",
            ],
        },
    ]


def build_report(coverage: dict[str, Any], cap_metric_rows: list[dict[str, Any]], branch_rows: list[dict[str, Any]]) -> str:
    selected = [row for row in branch_rows if row.get("selected")]
    selected_route = selected[0].get("route_id") if selected else "none"
    lines = [
        "# E008-M94 Source-Gap Two-Branch Repair Evaluation Route Decision",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Cap probe eval rows: {coverage['cap_probe_eval_rows']}.",
        f"- Cap probe policy metric rows: {coverage['cap_probe_policy_metric_rows']}.",
        f"- Cap primary-supported policies: {coverage['cap_primary_supported_policy_rows']}.",
        f"- Cap relaxed-supported policies: {coverage['cap_relaxed_supported_policy_rows']}.",
        f"- Selected route: `{selected_route}`.",
        f"- Selected next unit: `{coverage['selected_next_unit']}`.",
        "",
        "## Cap Probe Metrics",
        "",
        "| policy | primary 1.0m | relaxed 1.5m | first primary rank | first relaxed rank | best any-vp XZ |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in cap_metric_rows:
        lines.append(
            "| {policy} | {primary} | {relaxed} | {primary_rank} | {relaxed_rank} | {best} |".format(
                policy=row.get("probe_policy_id"),
                primary=row.get("primary_any_viewpoint_xz_1p0_hit"),
                relaxed=row.get("relaxed_any_viewpoint_xz_1p5_hit"),
                primary_rank=row.get("primary_any_viewpoint_xz_1p0_first_rank"),
                relaxed_rank=row.get("relaxed_any_viewpoint_xz_1p5_first_rank"),
                best=row.get("best_any_viewpoint_xz_m"),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- M94 uses eval-only distances after M93 fixed candidate order; those fields are not policy inputs.",
            "- M94 does not run render, detector, or trajectory jobs.",
            "- Final real navigation `SR` / `SPL`, deployable search policy, and final RGB-D/open-vocabulary robustness remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def mirror_outputs(paths: list[Path]) -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, DATA_OUT_DIR / path.name)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)

    m93_coverage = read_json(M93_DIR / "coverage.json")
    assignment_rows = read_jsonl(M93_DIR / "case_repair_assignment_rows.jsonl")
    coverage_rows = read_jsonl(M93_DIR / "coverage_expansion_observation_plan_rows.jsonl")
    render_rows = read_jsonl(M93_DIR / "coverage_expansion_render_plan_rows.jsonl")
    manifest_rows = read_jsonl(M93_DIR / "coverage_expansion_detector_manifest_rows.jsonl")
    cap_probe_rows = read_jsonl(M93_DIR / "cap_threshold_candidate_probe_rows.jsonl")
    long_job_rows = read_jsonl(M93_DIR / "long_job_command_rows.jsonl")
    pre_cap_eval_rows = read_jsonl(M91_DIR / "pre_cap_candidate_eval_rows.jsonl")

    cap_eval_rows = build_cap_probe_eval_rows(cap_probe_rows, pre_cap_eval_rows)
    cap_metric_rows = build_cap_policy_metric_rows(cap_eval_rows)
    branch_rows, selected_route, selected_next = build_branch_route_decision_rows(
        m93_coverage,
        assignment_rows,
        coverage_rows,
        render_rows,
        manifest_rows,
        cap_metric_rows,
        long_job_rows,
    )
    readiness_rows = build_readiness_gate_rows(m93_coverage, cap_eval_rows, cap_metric_rows, branch_rows)
    claim_rows = build_claim_boundary_rows(selected_route)
    status = READY_STATUS if all(row.get("gate_pass") for row in readiness_rows) else BLOCKED_STATUS
    route_rows = [
        {
            "version": VERSION,
            "decision": "m94_select_next_route" if status == READY_STATUS else "m94_route_decision_blocked",
            "selected_route": selected_route if status == READY_STATUS else None,
            "selected_next_unit": selected_next if status == READY_STATUS else None,
            "launch_long_job_now": False,
            "requires_docker_now": False,
            "coverage_launcher_adaptation_required": selected_route == "coverage_expansion_launcher_adaptation_first",
            "trajectory_promotion_ready": False,
            "real_navigation_sr_spl_ready": False,
            "final_real_rgbd_open_vocab_robustness_ready": False,
            "source_gap_recovery_supported": selected_route == "cap_threshold_probe_eval_first",
            "reason": "M94 fixes the next route without launching long jobs.",
        }
    ]
    next_action_rows = [
        {
            "version": VERSION,
            "row_type": "next_action",
            "next_unit": selected_next if status == READY_STATUS else "repair M94 route decision inputs",
            "action": (
                "Adapt M84/M85 render-detector launcher paths to M93 coverage rows before launching background render."
                if selected_route == "coverage_expansion_launcher_adaptation_first"
                else "Write cap-branch loss-safe evaluation contract before any trajectory promotion."
                if selected_route == "cap_threshold_probe_eval_first"
                else "Stop E008 source-gap repair expansion and record boundary."
            ),
            "launch_long_job_now": False,
        }
    ]

    outputs = {
        "cap_probe_eval_rows.jsonl": cap_eval_rows,
        "cap_probe_policy_metric_rows.jsonl": cap_metric_rows,
        "branch_route_decision_rows.jsonl": branch_rows,
        "readiness_gate_rows.jsonl": readiness_rows,
        "claim_boundary_rows.jsonl": claim_rows,
        "route_decision_rows.jsonl": route_rows,
        "next_action_rows.jsonl": next_action_rows,
    }
    output_paths: list[Path] = []
    for name, rows in outputs.items():
        path = ARTIFACT_DIR / name
        write_jsonl(path, rows)
        output_paths.append(path)

    coverage = {
        "version": VERSION,
        "status": status,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "artifact_output_root": str(ARTIFACT_DIR),
        "derived_output_root": str(DATA_OUT_DIR),
        "m93_status": m93_coverage.get("status"),
        "case_repair_assignment_rows": len(assignment_rows),
        "coverage_expansion_observation_rows": len(coverage_rows),
        "coverage_expansion_render_rows": len(render_rows),
        "coverage_expansion_detector_manifest_rows": len(manifest_rows),
        "cap_probe_eval_rows": len(cap_eval_rows),
        "cap_probe_policy_metric_rows": len(cap_metric_rows),
        "cap_primary_supported_policy_rows": sum(1 for row in cap_metric_rows if row.get("primary_any_viewpoint_xz_1p0_hit") is True),
        "cap_relaxed_supported_policy_rows": sum(1 for row in cap_metric_rows if row.get("relaxed_any_viewpoint_xz_1p5_hit") is True),
        "readiness_gate_rows": len(readiness_rows),
        "readiness_gate_fail_rows": sum(1 for row in readiness_rows if not row.get("gate_pass")),
        "selected_route": selected_route if status == READY_STATUS else None,
        "selected_next_unit": selected_next if status == READY_STATUS else None,
        "launch_long_job_now": False,
        "coverage_launcher_adaptation_required": selected_route == "coverage_expansion_launcher_adaptation_first",
        "source_gap_recovery_supported": selected_route == "cap_threshold_probe_eval_first",
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }
    write_json(ARTIFACT_DIR / "coverage.json", coverage)
    write_text(ARTIFACT_DIR / "report.md", build_report(coverage, cap_metric_rows, branch_rows))
    output_paths.extend([ARTIFACT_DIR / "coverage.json", ARTIFACT_DIR / "report.md"])
    mirror_outputs(output_paths)

    if status != READY_STATUS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
