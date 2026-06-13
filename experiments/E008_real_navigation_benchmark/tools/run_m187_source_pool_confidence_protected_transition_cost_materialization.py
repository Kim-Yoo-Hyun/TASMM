#!/usr/bin/env python3
"""Materialize M187 confidence-protected transition-cost repair rows."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E008_real_navigation_benchmark"
TOOLS_ROOT = EXP_ROOT / "tools"

M37_TOOL = TOOLS_ROOT / "run_m37_dynamic_stale_overlay_trajectory_execution_smoke.py"
M143_TOOL = TOOLS_ROOT / "run_m143_full_val_mini_confidence_preserving_trajectory_cost_materialization.py"

VERSION = "e008_m187_source_pool_confidence_protected_transition_cost_materialization_v0"
READY_STATUS = "e008_m187_source_pool_confidence_protected_transition_cost_materialization_ready"
BLOCKED_STATUS = "e008_m187_source_pool_confidence_protected_transition_cost_materialization_blocked"
NEXT_UNIT = "E008-M188 source-pool repaired policy leakage-safe goal-evaluation proxy"

DEFAULT_M183_ROOT = EXP_ROOT / "artifacts" / "E008-M183_docker_trajectory_execution_contract_preflight_v0"
DEFAULT_M186_ROOT = EXP_ROOT / "artifacts" / "E008-M186_source_pool_protected_baseline_failure_decomposition_v0"
DEFAULT_OUT_ROOT = (
    EXP_ROOT
    / "artifacts"
    / "E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0"
)
DEFAULT_DERIVED_OUT_ROOT = (
    ROOT
    / "local_dataset"
    / "HM3D_navigation_bridge"
    / "E008-M187_source_pool_confidence_protected_transition_cost_materialization_v0"
)

HABITAT_IMAGE = "research3/habitat-h001:20260508-calib-artifacts"
HOST_RESEARCH2_ROOT = Path("/home/yoohyun/research2")
HOST_DATA_ROOT = Path("/home/yoohyun/research3/local_dataset/data")
DOCKER_RESEARCH2_ROOT = Path("/work")
DOCKER_DATA_ROOT = Path("/data")

MATRIX_ID = "m187_source_pool_candidate_transition_geodesic_matrix_v0"
SELECTED_POLICY = "confidence_protected_transition_cost_policy_v1"
PROTECTED_BASELINE = "detector_confidence_reachable_subset_v0"
TRANSITION_ONLY_ABLATION = "transition_cost_only_reachable_subset_v0"
SOURCE_PROXY_FAILED = "path_cost_ascending_reachable_subset_v0"
PRIOR_TRADEOFF = "confidence_path_cost_tradeoff_reachable_subset_v0"
POLICY_ORDER = [
    SELECTED_POLICY,
    PROTECTED_BASELINE,
    TRANSITION_ONLY_ABLATION,
    PRIOR_TRADEOFF,
    SOURCE_PROXY_FAILED,
]
POLICY_ROLES = {
    SELECTED_POLICY: "selected_confidence_protected_transition_cost_repair",
    PROTECTED_BASELINE: "protected_detector_confidence_baseline",
    TRANSITION_ONLY_ABLATION: "transition_cost_without_confidence_protection_ablation",
    PRIOR_TRADEOFF: "negative_prior_confidence_path_tradeoff_baseline",
    SOURCE_PROXY_FAILED: "negative_source_proxy_path_cost_baseline",
}
CONFIDENCE_BIN_WIDTH = 0.05

BLOCKED_POLICY_FIELDS = {
    "eval_goal_position",
    "eval_goal_object_id",
    "eval_goal_object_name",
    "eval_first_viewpoint_position",
    "eval_first_viewpoint_rotation",
    "eval_all_viewpoint_positions",
    "eval_viewpoint_count",
    "eval_all_viewpoint_count_loaded",
    "eval_geodesic_distance",
    "eval_euclidean_distance",
    "candidate_to_eval_goal_xz_m",
    "candidate_to_eval_goal_3d_m",
    "candidate_to_eval_first_viewpoint_xz_m",
    "candidate_to_eval_first_viewpoint_3d_m",
    "candidate_to_nearest_eval_viewpoint_xz_m",
    "candidate_to_nearest_eval_viewpoint_3d_m",
    "primary_eval_hit",
    "hit_any_viewpoint_xz_1p0",
    "hit_goal_xz_1p0",
    "eval_success",
    "success_label",
    "oracle_viewpoint_path_m",
    "oracle_goal_snapped_path_m",
    "episode_eval_geodesic_distance_m",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m183-root", default=str(DEFAULT_M183_ROOT))
    parser.add_argument("--m186-root", default=str(DEFAULT_M186_ROOT))
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--derived-out-root", default=str(DEFAULT_DERIVED_OUT_ROOT))
    parser.add_argument("--limit-episodes", type=int, default=None)
    parser.add_argument("--inside-docker", action="store_true")
    return parser.parse_args()


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def host_to_container_path(path: Path) -> str:
    path = path.resolve()
    try:
        return str(DOCKER_RESEARCH2_ROOT / path.relative_to(HOST_RESEARCH2_ROOT))
    except ValueError:
        return str(path)


def habitat_import_ready() -> bool:
    return importlib.util.find_spec("habitat_sim") is not None


def run_self_in_docker(args: argparse.Namespace) -> int:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        "1001:1001",
        "-e",
        "HOME=/tmp",
        "-v",
        f"{HOST_DATA_ROOT}:{DOCKER_DATA_ROOT}:ro",
        "-v",
        f"{HOST_RESEARCH2_ROOT}:{DOCKER_RESEARCH2_ROOT}",
        "-w",
        str(DOCKER_RESEARCH2_ROOT),
        HABITAT_IMAGE,
        "bash",
        "-lc",
        "micromamba run -n base python "
        "experiments/E008_real_navigation_benchmark/tools/"
        "run_m187_source_pool_confidence_protected_transition_cost_materialization.py "
        "--inside-docker "
        f"--m183-root {host_to_container_path(resolve_path(args.m183_root))} "
        f"--m186-root {host_to_container_path(resolve_path(args.m186_root))} "
        f"--out-root {host_to_container_path(resolve_path(args.out_root))} "
        f"--derived-out-root {host_to_container_path(resolve_path(args.derived_out_root))}"
        + (f" --limit-episodes {args.limit_episodes}" if args.limit_episodes is not None else ""),
    ]
    result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return int(result.returncode)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def as_vec3(value: object) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    out = [finite_float(part) for part in value]
    if any(part is None for part in out):
        return None
    return [float(part) for part in out]


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
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
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


def adapter_token(adapter_episode_id: str) -> str:
    return adapter_episode_id.replace("::", "__")


def build_benchmark_uid(adapter_episode_id: str) -> str:
    return f"m187::{adapter_token(adapter_episode_id)}"


def build_policy_plan_uid(adapter_episode_id: str, policy_id: str) -> str:
    return f"m187::{adapter_token(adapter_episode_id)}::{policy_id}"


def start_node_uid(adapter_episode_id: str) -> str:
    return f"episode_start::{adapter_episode_id}"


def candidate_node_uid(row: dict[str, Any]) -> str:
    return f"candidate::{row.get('proposal_uid')}"


def confidence_sort_key(row: dict[str, Any]) -> tuple[float, int, str]:
    return (
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or row.get("candidate_rank") or 10**9),
        str(row.get("proposal_uid")),
    )


def source_cost_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    return (
        finite_float(row.get("source_to_candidate_path_cost_m")) or math.inf,
        -(finite_float(row.get("confidence")) or -math.inf),
        int(row.get("candidate_rank_m09") or row.get("candidate_rank") or 10**9),
        str(row.get("proposal_uid")),
    )


def confidence_bin(row: dict[str, Any]) -> int:
    confidence = finite_float(row.get("confidence")) or 0.0
    return int(math.floor((confidence + 1e-12) / CONFIDENCE_BIN_WIDTH))


def mean(values: list[object]) -> float | None:
    clean = [float(value) for value in values if finite_float(value) is not None]
    return float(sum(clean) / len(clean)) if clean else None


def matrix_cost(
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    from_uid: str,
    to_uid: str,
) -> tuple[bool, float | None, int, str]:
    row = cost_lookup.get((from_uid, to_uid), {})
    return (
        bool(row.get("path_found")),
        finite_float(row.get("geodesic_distance_m")),
        int(row.get("point_count") or 0),
        str(row.get("path_error") or ""),
    )


def patch_m143_module(m143: Any) -> None:
    m143.VERSION = VERSION
    m143.MATRIX_ID = MATRIX_ID
    m143.SELECTED_POLICY = SELECTED_POLICY
    m143.PRIMARY_BASELINE = PROTECTED_BASELINE
    m143.HARD_VETO_POLICY = TRANSITION_ONLY_ABLATION
    m143.CONFIDENCE_ONLY = PROTECTED_BASELINE
    m143.FAILED_REPAIR = PRIOR_TRADEOFF
    m143.PATH_COST_BASELINE = SOURCE_PROXY_FAILED
    m143.POLICY_ORDER = POLICY_ORDER
    m143.POLICY_ROLES = POLICY_ROLES
    m143.CONFIDENCE_BAND_ABS = CONFIDENCE_BIN_WIDTH
    m143.BLOCKED_POLICY_FIELDS = BLOCKED_POLICY_FIELDS


def base_candidates_from_m183(
    m183_rows: list[dict[str, Any]],
    limit_episodes: int | None,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[str]]]:
    policy_order: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in sorted(m183_rows, key=lambda item: (str(item.get("adapter_episode_id")), str(item.get("policy_id")), int(item.get("visit_rank") or 10**9))):
        policy_order[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(str(row.get("proposal_uid")))

    protected = [
        row
        for row in m183_rows
        if row.get("policy_id") == PROTECTED_BASELINE
        and bool(row.get("path_ready"))
        and bool(row.get("candidate_usable_for_path_smoke", True))
    ]
    selected_episode_ids = sorted({str(row.get("adapter_episode_id")) for row in protected})
    if limit_episodes is not None:
        selected_episode_ids = selected_episode_ids[:limit_episodes]
    selected_episode_set = set(selected_episode_ids)

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(protected, key=lambda item: (str(item.get("adapter_episode_id")), confidence_sort_key(item))):
        adapter_episode_id = str(row.get("adapter_episode_id"))
        proposal_uid = str(row.get("proposal_uid"))
        if adapter_episode_id not in selected_episode_set or proposal_uid in seen:
            continue
        clean = dict(row)
        for field in BLOCKED_POLICY_FIELDS:
            clean.pop(field, None)
        stop = (
            as_vec3(clean.get("execution_stop_position_m"))
            or as_vec3(clean.get("candidate_stop_position_m"))
            or as_vec3(clean.get("snapped_position_m"))
        )
        clean.update(
            {
                "version": VERSION,
                "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
                "candidate_stop_position_m": stop,
                "execution_stop_position_m": stop,
                "snapped_position_m": stop,
                "path_ready": True,
                "candidate_usable_for_path_smoke": True,
                "blocked_candidate_for_path_policy": False,
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "primary_budget_cap": "full_ranked",
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M187 base candidate row from M183 protected source-pool denominator; ObjectNav goal/viewpoint fields are excluded from policy input.",
            }
        )
        out.append(clean)
        seen.add(proposal_uid)
    return out, policy_order


def order_from_existing_policy(
    candidates: list[dict[str, Any]],
    proposal_order: list[str],
    fallback_key: Any,
) -> list[dict[str, Any]]:
    by_uid = {str(row.get("proposal_uid")): row for row in candidates}
    ordered: list[dict[str, Any]] = []
    for proposal_uid in proposal_order:
        if proposal_uid in by_uid:
            ordered.append(by_uid[proposal_uid])
    missing = [row for row in candidates if str(row.get("proposal_uid")) not in set(proposal_order)]
    ordered.extend(sorted(missing, key=fallback_key))
    return ordered


def confidence_protected_transition_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(sorted(candidates, key=confidence_sort_key))
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    while remaining:
        detector_top = sorted(remaining, key=confidence_sort_key)[0]
        top_bin = max(confidence_bin(row) for row in remaining)
        bin_rows = [row for row in remaining if confidence_bin(row) == top_bin]
        scored: list[tuple[bool, float, float, int, str, dict[str, Any]]] = []
        for row in bin_rows:
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            scored.append(
                (
                    not found,
                    cost if cost is not None else math.inf,
                    -(finite_float(row.get("confidence")) or -math.inf),
                    int(row.get("candidate_rank_m09") or 10**9),
                    str(row.get("proposal_uid")),
                    row,
                )
            )
        selected = sorted(scored)[0][-1] if scored else detector_top
        found, cost, _, path_error = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        reason = (
            "detector_confidence_bin_preserved"
            if selected.get("proposal_uid") == detector_top.get("proposal_uid")
            else "within_confidence_bin_transition_tiebreak"
        )
        events.append(
            {
                "reason": reason,
                "detector_top_proposal_uid": detector_top.get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence_bin": top_bin,
                "selected_confidence_bin": confidence_bin(selected),
                "top_confidence": finite_float(detector_top.get("confidence")),
                "selected_confidence": finite_float(selected.get("confidence")),
                "confidence_delta_from_top": (finite_float(detector_top.get("confidence")) or 0.0)
                - (finite_float(selected.get("confidence")) or 0.0),
                "selected_current_path_found": found,
                "selected_current_path_cost_m": cost,
                "selected_current_path_error": path_error,
                "confidence_bin_width": CONFIDENCE_BIN_WIDTH,
                "hard_feasibility_veto_applied": False,
                "confidence_bin_transition_override": selected.get("proposal_uid") != detector_top.get("proposal_uid"),
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if found:
            current_uid = candidate_node_uid(selected)
    return ordered, events


def transition_only_order(
    candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining = list(candidates)
    current_uid = start_node_uid(adapter_episode_id)
    ordered: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    while remaining:
        scored: list[tuple[bool, float, float, int, str, dict[str, Any]]] = []
        for row in remaining:
            found, cost, _, _ = matrix_cost(cost_lookup, current_uid, candidate_node_uid(row))
            scored.append(
                (
                    not found,
                    cost if cost is not None else math.inf,
                    -(finite_float(row.get("confidence")) or -math.inf),
                    int(row.get("candidate_rank_m09") or 10**9),
                    str(row.get("proposal_uid")),
                    row,
                )
            )
        selected = sorted(scored)[0][-1]
        found, cost, _, path_error = matrix_cost(cost_lookup, current_uid, candidate_node_uid(selected))
        events.append(
            {
                "reason": "transition_cost_only_greedy",
                "detector_top_proposal_uid": sorted(remaining, key=confidence_sort_key)[0].get("proposal_uid"),
                "selected_proposal_uid": selected.get("proposal_uid"),
                "current_node_uid": current_uid,
                "top_confidence_bin": max(confidence_bin(row) for row in remaining),
                "selected_confidence_bin": confidence_bin(selected),
                "selected_current_path_found": found,
                "selected_current_path_cost_m": cost,
                "selected_current_path_error": path_error,
                "confidence_bin_transition_override": True,
                "hard_feasibility_veto_applied": False,
            }
        )
        ordered.append(selected)
        remaining = [row for row in remaining if row.get("proposal_uid") != selected.get("proposal_uid")]
        if found:
            current_uid = candidate_node_uid(selected)
    return ordered, events


def materialize_policy_rows(
    policy_id: str,
    ordered_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    adapter_episode_id: str,
    events: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    plan_uid = build_policy_plan_uid(adapter_episode_id, policy_id)
    current_uid = start_node_uid(adapter_episode_id)
    cumulative = 0.0
    out: list[dict[str, Any]] = []
    event_by_rank = {idx + 1: event for idx, event in enumerate(events or [])}
    for rank, source in enumerate(ordered_candidates, start=1):
        to_uid = candidate_node_uid(source)
        found, cost, point_count, path_error = matrix_cost(cost_lookup, current_uid, to_uid)
        if found and cost is not None:
            cumulative += cost
        event = event_by_rank.get(rank, {})
        row = dict(source)
        for field in BLOCKED_POLICY_FIELDS:
            row.pop(field, None)
        if policy_id == SOURCE_PROXY_FAILED:
            ranking_score = -1.0 * (finite_float(source.get("source_to_candidate_path_cost_m")) or math.inf)
        elif policy_id == TRANSITION_ONLY_ABLATION:
            ranking_score = -1.0 * (cost if cost is not None else math.inf)
        elif policy_id == SELECTED_POLICY and event.get("reason") == "within_confidence_bin_transition_tiebreak":
            ranking_score = (finite_float(source.get("confidence")) or 0.0) + 0.0001
        else:
            ranking_score = finite_float(source.get("confidence")) or 0.0
        row.update(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": build_benchmark_uid(adapter_episode_id),
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES[policy_id],
                "method_policy": policy_id == SELECTED_POLICY,
                "primary_baseline_policy": policy_id == PROTECTED_BASELINE,
                "candidate_visit_uid": f"{plan_uid}::{rank:04d}",
                "visit_rank": rank,
                "ranking_score": ranking_score,
                "candidate_order_component": policy_id,
                "task_context_id": "open_vocabulary_object_search_target_free_source",
                "candidate_source_role": "current_observation",
                "dynamic_stale_overlay_role": "target_free_detector_candidate",
                "primary_budget_cap": "full_ranked",
                "trajectory_cost_matrix_id": MATRIX_ID,
                "confidence_bin_width": CONFIDENCE_BIN_WIDTH,
                "confidence_bin": confidence_bin(source),
                "current_pose_to_candidate_geodesic_m": cost,
                "current_pose_to_candidate_path_found": found,
                "current_pose_to_candidate_path_point_count": point_count,
                "current_pose_to_candidate_path_error": path_error,
                "planned_segment_path_found": found,
                "planned_cumulative_path_cost_m": cumulative,
                "selected_from_remaining_rows": len(ordered_candidates) - rank + 1,
                "path_ready": bool(source.get("path_ready")),
                "candidate_usable_for_path_smoke": bool(source.get("candidate_usable_for_path_smoke", True)),
                "blocked_candidate_for_path_policy": bool(source.get("blocked_candidate_for_path_policy")),
                "confidence_bin_reason": event.get("reason") if event else None,
                "confidence_bin_transition_override": bool(event.get("confidence_bin_transition_override")) if event else False,
                "selected_confidence_bin": event.get("selected_confidence_bin") if event else confidence_bin(source),
                "top_confidence_bin": event.get("top_confidence_bin") if event else confidence_bin(source),
                "confidence_delta_from_top": event.get("confidence_delta_from_top") if event else 0.0,
                "uses_transition_cost_for_policy": policy_id in {SELECTED_POLICY, TRANSITION_ONLY_ABLATION},
                "uses_source_proxy_cost_for_policy": policy_id in {SOURCE_PROXY_FAILED, PRIOR_TRADEOFF},
                "uses_task_context_for_decision": False,
                "policy_input_allowed": True,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "claim_boundary": "M187 materializes repaired source-pool policy rows only; SR/SPL requires M188+M189 trajectory evaluation.",
            }
        )
        out.append(row)
        if found:
            current_uid = to_uid
    return out


def build_all_policy_rows(
    base_candidates: list[dict[str, Any]],
    cost_lookup: dict[tuple[str, str], dict[str, Any]],
    existing_policy_order: dict[tuple[str, str], list[str]],
) -> list[dict[str, Any]]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in base_candidates:
        by_episode[str(row.get("adapter_episode_id"))].append(row)

    out: list[dict[str, Any]] = []
    for adapter_episode_id, candidates in sorted(by_episode.items()):
        candidates = sorted(candidates, key=confidence_sort_key)
        for policy_id in POLICY_ORDER:
            events: list[dict[str, Any]] | None = None
            if policy_id == SELECTED_POLICY:
                ordered, events = confidence_protected_transition_order(candidates, cost_lookup, adapter_episode_id)
            elif policy_id == TRANSITION_ONLY_ABLATION:
                ordered, events = transition_only_order(candidates, cost_lookup, adapter_episode_id)
            elif policy_id == PROTECTED_BASELINE:
                ordered = order_from_existing_policy(
                    candidates,
                    existing_policy_order.get((adapter_episode_id, policy_id), []),
                    confidence_sort_key,
                )
            elif policy_id == PRIOR_TRADEOFF:
                ordered = order_from_existing_policy(
                    candidates,
                    existing_policy_order.get((adapter_episode_id, policy_id), []),
                    confidence_sort_key,
                )
            elif policy_id == SOURCE_PROXY_FAILED:
                ordered = order_from_existing_policy(
                    candidates,
                    existing_policy_order.get((adapter_episode_id, policy_id), []),
                    source_cost_sort_key,
                )
            else:
                raise ValueError(f"unknown policy_id: {policy_id}")
            out.extend(materialize_policy_rows(policy_id, ordered, cost_lookup, adapter_episode_id, events))
    return out


def build_plan_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[str(row.get("policy_plan_uid"))].append(row)
    out: list[dict[str, Any]] = []
    for plan_uid, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row.get("visit_rank") or 10**9))
        first = rows[0]
        out.append(
            {
                "version": VERSION,
                "policy_plan_uid": plan_uid,
                "benchmark_row_uid": first.get("benchmark_row_uid"),
                "policy_id": first.get("policy_id"),
                "policy_role": first.get("policy_role"),
                "method_policy": first.get("policy_id") == SELECTED_POLICY,
                "primary_baseline_policy": first.get("policy_id") == PROTECTED_BASELINE,
                "scan_id": first.get("scan_id"),
                "adapter_episode_id": first.get("adapter_episode_id"),
                "scene_key": first.get("scene_key"),
                "object_category": first.get("object_category"),
                "task_context_id": first.get("task_context_id"),
                "candidate_budget": len(rows),
                "primary_budget_cap": "full_ranked",
                "candidate_rows": len(rows),
                "path_ready_candidate_rows": sum(1 for row in rows if row.get("path_ready")),
                "blocked_candidate_rows": sum(1 for row in rows if not row.get("path_ready")),
                "planned_cumulative_path_cost_m": rows[-1].get("planned_cumulative_path_cost_m"),
                "first_proposal_uid": first.get("proposal_uid"),
                "first_confidence": first.get("confidence"),
                "first_current_pose_to_candidate_geodesic_m": first.get("current_pose_to_candidate_geodesic_m"),
                "execution_candidate_file": "dynamic_stale_overlay_trajectory_candidate_rows.jsonl",
                "trajectory_cost_matrix_file": "trajectory_cost_matrix_rows.jsonl",
                "execution_semantics": "start at ObjectNav episode start and visit execution_stop_position_m in visit_rank order",
                "termination_rule": "terminate on first eval-only success after a stop or after the full ranked list is exhausted",
                "requires_docker": True,
                "runner_script": "experiments/E008_real_navigation_benchmark/tools/run_m184_docker_trajectory_execution_sr_spl.py",
                "runner_input_ready": bool(rows) and all(row.get("scene_docker_path") for row in rows),
                "execute_in_next_runner": False,
                "next_runner_after_proxy_gate": True,
                "start_state_source": "ObjectNav episode start state from M183 episode_goal_eval_rows; goal/viewpoints are metric-only",
                "uses_transition_cost_for_policy": first.get("policy_id") in {SELECTED_POLICY, TRANSITION_ONLY_ABLATION},
                "uses_task_context_for_decision": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
                "policy_input_uses_eval_goal_or_viewpoint": False,
                "policy_input_uses_success_label": False,
                "stale_visit_first": False,
                "current_observation_first": True,
                "stale_before_current_rows": 0,
                "old_location_dead_end_cost_proxy_m": 0.0,
                "claim_boundary": "M187 fixes runner-compatible repaired policy inputs only; M188 proxy and later Docker trajectory execution are required.",
            }
        )
    return out


def build_input_contract_rows() -> list[dict[str, Any]]:
    allowed = [
        ("adapter_episode_id", "episode identity used to join start state"),
        ("scene_key", "scene identity"),
        ("object_category", "query category and label compatibility"),
        ("scene_docker_path", "Habitat scene path"),
        ("navmesh_docker_path", "Habitat navmesh path"),
        ("candidate_position_m", "detector-derived candidate centroid"),
        ("candidate_stop_position_m", "candidate stop on navmesh"),
        ("execution_stop_position_m", "candidate execution stop"),
        ("snapped_position_m", "navmesh-snapped candidate point"),
        ("confidence", "detector confidence score"),
        ("confidence_bin", "precommitted 0.05 confidence bin for protected transition rerank"),
        ("source_to_candidate_path_cost_m", "source-to-candidate diagnostic prior"),
        ("current_pose_to_candidate_geodesic_m", "current-state transition cost from the materialized geodesic matrix"),
        ("trajectory_cost_matrix_id", "cost matrix identifier"),
        ("candidate_rank_m09", "detector rank tie-breaker"),
        ("path_ready", "candidate path usability flag"),
        ("candidate_usable_for_path_smoke", "runner usability flag"),
    ]
    rows = [
        {
            "version": VERSION,
            "contract_group": "allowed_policy_input",
            "field": field,
            "allowed_for_policy": True,
            "allowed_for_metric": True,
            "reason": reason,
        }
        for field, reason in allowed
    ]
    rows.extend(
        {
            "version": VERSION,
            "contract_group": "blocked_policy_input",
            "field": field,
            "allowed_for_policy": False,
            "allowed_for_metric": True,
            "reason": "ObjectNav goal/viewpoint, success label, or posthoc metric-only field.",
        }
        for field in sorted(BLOCKED_POLICY_FIELDS)
    )
    return rows


def build_policy_order_audit_rows(
    candidate_rows: list[dict[str, Any]],
    base_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in base_candidates:
        base_by_episode[str(row.get("adapter_episode_id"))].append(row)
    for row in candidate_rows:
        rows_by_key[(str(row.get("adapter_episode_id")), str(row.get("policy_id")))].append(row)

    out: list[dict[str, Any]] = []
    for adapter_episode_id, base_rows in sorted(base_by_episode.items()):
        detector_order = [str(row.get("proposal_uid")) for row in sorted(base_rows, key=confidence_sort_key)]
        detector_rank = {proposal_uid: idx + 1 for idx, proposal_uid in enumerate(detector_order)}
        detector_bin = {str(row.get("proposal_uid")): confidence_bin(row) for row in base_rows}
        for policy_id in POLICY_ORDER:
            policy_rows = sorted(
                rows_by_key.get((adapter_episode_id, policy_id), []),
                key=lambda row: int(row.get("visit_rank") or 10**9),
            )
            bin_violations = 0
            first_rank_flip = None
            for idx, row in enumerate(policy_rows, start=1):
                proposal_uid = str(row.get("proposal_uid"))
                expected_uid = detector_order[idx - 1] if idx <= len(detector_order) else None
                if expected_uid != proposal_uid and first_rank_flip is None:
                    first_rank_flip = {
                        "visit_rank": idx,
                        "expected_detector_proposal_uid": expected_uid,
                        "selected_proposal_uid": proposal_uid,
                    }
                selected_bin = detector_bin.get(proposal_uid, -1)
                skipped_higher_bin = [
                    other_uid
                    for other_uid in detector_order
                    if other_uid not in {str(prev.get("proposal_uid")) for prev in policy_rows[: idx - 1]}
                    and detector_bin.get(other_uid, -1) > selected_bin
                ]
                if policy_id == SELECTED_POLICY and skipped_higher_bin:
                    bin_violations += 1
            out.append(
                {
                    "version": VERSION,
                    "row_type": "policy_order_audit",
                    "adapter_episode_id": adapter_episode_id,
                    "policy_id": policy_id,
                    "policy_role": POLICY_ROLES.get(policy_id),
                    "candidate_rows": len(policy_rows),
                    "detector_order_identical": [str(row.get("proposal_uid")) for row in policy_rows] == detector_order,
                    "first_rank_flip": first_rank_flip,
                    "confidence_bin_violation_count": bin_violations,
                    "confidence_bin_width": CONFIDENCE_BIN_WIDTH,
                    "confidence_bin_guard_pass": policy_id != SELECTED_POLICY or bin_violations == 0,
                    "audit_pass": policy_id != SELECTED_POLICY or bin_violations == 0,
                }
            )
    return out


def summarize_audit_rows(audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(by_policy.items()):
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "episode_rows": len(rows),
                "detector_order_identical_rows": sum(1 for row in rows if row.get("detector_order_identical")),
                "confidence_bin_violation_count": sum(int(row.get("confidence_bin_violation_count") or 0) for row in rows),
                "audit_pass": all(row.get("audit_pass") for row in rows),
            }
        )
    return out


def build_leakage_audit_rows(
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads = [
        ("repaired_candidate_rows", candidate_rows),
        ("trajectory_execution_plan_rows", plan_rows),
        ("trajectory_cost_matrix_rows", matrix_rows),
    ]
    out: list[dict[str, Any]] = []
    for payload, rows in payloads:
        field_hits = Counter()
        flag_hits = 0
        for row in rows:
            for field in BLOCKED_POLICY_FIELDS:
                if field in row:
                    field_hits[field] += 1
            if (
                row.get("uses_objectnav_eval_goal_or_viewpoint_for_policy")
                or row.get("policy_input_uses_eval_goal_or_viewpoint")
                or row.get("policy_input_uses_success_label")
            ):
                flag_hits += 1
        out.append(
            {
                "version": VERSION,
                "payload": payload,
                "row_count": len(rows),
                "blocked_field_hits": dict(sorted(field_hits.items())),
                "blocked_field_hit_count": sum(field_hits.values()),
                "blocked_flag_hit_count": flag_hits,
                "leakage_audit_pass": sum(field_hits.values()) == 0 and flag_hits == 0,
            }
        )
    return out


def build_policy_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_policy[str(row.get("policy_id"))].append(row)
    out: list[dict[str, Any]] = []
    for policy_id, rows in sorted(by_policy.items()):
        plan_last_rows = []
        by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_plan[str(row.get("policy_plan_uid"))].append(row)
        for plan_rows in by_plan.values():
            ordered = sorted(plan_rows, key=lambda row: int(row.get("visit_rank") or 10**9))
            if ordered:
                plan_last_rows.append(ordered[-1])
        out.append(
            {
                "version": VERSION,
                "policy_id": policy_id,
                "policy_role": POLICY_ROLES.get(policy_id),
                "episode_rows": len(by_plan),
                "candidate_rows": len(rows),
                "path_ready_rows": sum(1 for row in rows if row.get("path_ready")),
                "planned_cumulative_path_cost_m_mean": mean(
                    [row.get("planned_cumulative_path_cost_m") for row in plan_last_rows]
                ),
                "transition_override_rows": sum(1 for row in rows if row.get("confidence_bin_transition_override")),
                "confidence_bin_violation_count": sum(
                    int(row.get("selected_confidence_bin") or 0) > int(row.get("top_confidence_bin") or 0)
                    for row in rows
                    if policy_id == SELECTED_POLICY
                ),
                "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
                "claim_boundary": "M187 policy summary over materialized rows; not executed trajectory evidence.",
            }
        )
    return out


def build_readiness_gate_rows(
    missing_inputs: list[str],
    m186_cov: dict[str, Any],
    base_candidates: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    plan_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    leakage_rows: list[dict[str, Any]],
    scene_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode = Counter(str(row.get("adapter_episode_id")) for row in base_candidates)
    expected_matrix_rows = sum(count * count for count in by_episode.values())
    expected_candidate_rows = len(base_candidates) * len(POLICY_ORDER)
    expected_plan_rows = len(by_episode) * len(POLICY_ORDER)
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    selected_audit = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_changed_episode_count = sum(1 for row in selected_audit if not row.get("detector_order_identical"))
    gates = [
        (
            "required_inputs_present",
            not missing_inputs,
            f"missing={missing_inputs}",
            True,
        ),
        (
            "m186_repair_contract_ready",
            m186_cov.get("status") == "e008_m186_source_pool_protected_baseline_failure_decomposition_ready",
            f"M186 status={m186_cov.get('status')}.",
            True,
        ),
        (
            "source_pool_denominator_preserved",
            len(by_episode) == 8 and len(base_candidates) == 180,
            f"episodes={len(by_episode)}; base_candidates={len(base_candidates)}; expected=8/180",
            True,
        ),
        (
            "transition_cost_matrix_materialized",
            len(matrix_rows) == expected_matrix_rows,
            f"matrix rows={len(matrix_rows)}; expected={expected_matrix_rows}",
            True,
        ),
        (
            "candidate_policy_rows_materialized",
            len(candidate_rows) == expected_candidate_rows,
            f"candidate rows={len(candidate_rows)}; expected={expected_candidate_rows}",
            True,
        ),
        (
            "same_candidate_count_per_policy",
            set(candidate_counts.values()) == {len(base_candidates)} and len(candidate_counts) == len(POLICY_ORDER),
            f"counts={dict(sorted(candidate_counts.items()))}",
            True,
        ),
        (
            "execution_plans_materialized",
            len(plan_rows) == expected_plan_rows,
            f"plan rows={len(plan_rows)}; expected={expected_plan_rows}",
            True,
        ),
        (
            "selected_policy_activity",
            selected_changed_episode_count > 0,
            f"selected changed episode orders={selected_changed_episode_count}/{len(by_episode)}",
            True,
        ),
        (
            "confidence_bin_guard",
            all(row.get("confidence_bin_guard_pass") for row in selected_audit),
            f"selected bin violations={sum(int(row.get('confidence_bin_violation_count') or 0) for row in selected_audit)}",
            True,
        ),
        (
            "leakage_audit_pass",
            all(row.get("leakage_audit_pass") for row in leakage_rows),
            f"failed={sum(1 for row in leakage_rows if not row.get('leakage_audit_pass'))}",
            True,
        ),
        (
            "scene_runtime_errors_absent",
            not scene_errors,
            f"scene_errors={len(scene_errors)}",
            True,
        ),
        (
            "execute_trajectories_now",
            False,
            "M187 materializes repaired rows only; M188 leakage-safe proxy should run before Docker trajectory execution.",
            False,
        ),
    ]
    return [
        {
            "version": VERSION,
            "row_type": "readiness_gate",
            "gate_id": gate_id,
            "gate_status": "pass" if passed else "fail",
            "passed": passed,
            "blocks_m188": blocks and not passed,
            "evidence": evidence,
        }
        for gate_id, passed, evidence, blocks in gates
    ]


def build_claim_boundary_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "claim_id": "repaired_policy_rows_materialized",
            "supported": ready,
            "claim_boundary": "M187 materializes a confidence-bin protected transition-cost repair over the fixed M183 source-pool denominator.",
        },
        {
            "version": VERSION,
            "claim_id": "principle_driven_repair",
            "supported": ready,
            "claim_boundary": "The repair follows M186: source-to-candidate proxy cost is replaced with current-state transition cost, but detector confidence remains protected across 0.05 bins.",
        },
        {
            "version": VERSION,
            "claim_id": "executed_navigation_improvement",
            "supported": False,
            "claim_boundary": "M187 does not execute Habitat trajectories; M188 proxy and later Docker execution are required for SR/SPL.",
        },
        {
            "version": VERSION,
            "claim_id": "final_real_navigation_sr_spl",
            "supported": False,
            "claim_boundary": "Final navigation claim still needs repaired policy proxy, trajectory execution, heldout transfer, external navigation/search baselines, and failure analysis.",
        },
    ]


def build_route_decision_rows(ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "version": VERSION,
            "row_type": "route_decision",
            "decision_id": "m187_selected_next",
            "decision": "run_m188_leakage_safe_proxy" if ready else "repair_m187_materialization",
            "selected_next_unit": NEXT_UNIT if ready else "repair E008-M187 materialization",
            "launch_long_job_now": False,
            "reason": "M187 has repaired runner-compatible rows; M188 should evaluate leakage-safe proxy before Docker trajectory execution."
            if ready
            else "One or more materialization gates failed.",
        }
    ]


def copy_metric_only_rows(m183_root: Path, out_root: Path, derived_out_root: Path) -> tuple[int, int]:
    episode_rows = read_jsonl(m183_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m183_root / "oracle_path_rows.jsonl")
    for output_dir in (out_root, derived_out_root):
        write_jsonl(output_dir / "episode_goal_eval_rows.jsonl", episode_rows)
        write_jsonl(output_dir / "oracle_path_rows.jsonl", oracle_rows)
    return len(episode_rows), len(oracle_rows)


def build_report(
    coverage: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    audit_summary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# E008-M187 Source-Pool Confidence-Protected Transition-Cost Materialization",
            "",
            f"Generated: {coverage['generated_at']}",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Base source-pool candidate rows: {coverage['base_source_pool_candidate_rows']}.",
            f"- Episode rows: {coverage['episode_rows']}.",
            f"- Cost matrix rows: {coverage['transition_cost_matrix_rows']} "
            f"(expected {coverage['expected_transition_cost_matrix_rows']}).",
            f"- Candidate-policy rows: {coverage['repaired_candidate_rows']}.",
            f"- Execution plan rows: {coverage['trajectory_execution_plan_rows']}.",
            f"- Selected policy: `{coverage['selected_policy_id']}`.",
            f"- Confidence bin width: {coverage['confidence_bin_width']}.",
            f"- Selected changed episode orders: {coverage['selected_policy_changed_episode_orders']} / {coverage['episode_rows']}.",
            f"- Selected confidence-bin violations: {coverage['selected_policy_confidence_bin_violations']}.",
            f"- Leakage audit pass: {coverage['leakage_audit_pass']}.",
            f"- Selected next unit: {coverage['selected_next_unit']}.",
            "",
            "## Policy Summary",
            "",
            markdown_table(
                summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "candidate_rows",
                    "planned_cumulative_path_cost_m_mean",
                    "transition_override_rows",
                ],
            ),
            "",
            "## Order Audit Summary",
            "",
            markdown_table(
                audit_summary_rows,
                [
                    "policy_id",
                    "episode_rows",
                    "detector_order_identical_rows",
                    "confidence_bin_violation_count",
                    "audit_pass",
                ],
            ),
            "",
            "## Gates",
            "",
            markdown_table(gate_rows, ["gate_id", "gate_status", "blocks_m188", "evidence"]),
            "",
            "## Claim Boundary",
            "",
            "- M187 is row materialization, not a positive navigation result.",
            "- The selected policy may reorder candidates only inside a fixed 0.05 confidence bin.",
            "- ObjectNav goal/viewpoint and success labels remain metric-only and are not policy inputs.",
            "- M188 must check leakage-safe proxy before any Docker trajectory execution.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    if not args.inside_docker and not habitat_import_ready():
        raise SystemExit(run_self_in_docker(args))

    m183_root = resolve_path(args.m183_root)
    m186_root = resolve_path(args.m186_root)
    out_root = resolve_path(args.out_root)
    derived_out_root = resolve_path(args.derived_out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    derived_out_root.mkdir(parents=True, exist_ok=True)

    m143 = load_module(M143_TOOL, "e008_m143_materialization")
    m37 = load_module(M37_TOOL, "e008_m37_runner")
    patch_m143_module(m143)

    m183_cov = read_json(m183_root / "coverage.json")
    m186_cov = read_json(m186_root / "coverage.json")
    m183_rows = read_jsonl(m183_root / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl")
    goal_rows = read_jsonl(m183_root / "episode_goal_eval_rows.jsonl")
    oracle_rows = read_jsonl(m183_root / "oracle_path_rows.jsonl")
    missing_inputs = [
        str(path.relative_to(ROOT))
        for path, rows in [
            (m183_root / "coverage.json", [m183_cov] if m183_cov else []),
            (m186_root / "coverage.json", [m186_cov] if m186_cov else []),
            (m183_root / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", m183_rows),
            (m183_root / "episode_goal_eval_rows.jsonl", goal_rows),
            (m183_root / "oracle_path_rows.jsonl", oracle_rows),
        ]
        if not rows
    ]
    if missing_inputs:
        raise SystemExit(f"missing required inputs: {missing_inputs}")

    base_candidates, existing_policy_order = base_candidates_from_m183(m183_rows, args.limit_episodes)
    matrix_rows, cost_lookup, scene_errors = m143.build_cost_matrix_rows(m37, goal_rows, base_candidates)
    candidate_rows = build_all_policy_rows(base_candidates, cost_lookup, existing_policy_order)
    plan_rows = build_plan_rows(candidate_rows)
    input_contract_rows = build_input_contract_rows()
    audit_rows = build_policy_order_audit_rows(candidate_rows, base_candidates)
    audit_summary_rows = summarize_audit_rows(audit_rows)
    leakage_rows = build_leakage_audit_rows(candidate_rows, plan_rows, matrix_rows)
    gate_rows = build_readiness_gate_rows(
        missing_inputs,
        m186_cov,
        base_candidates,
        matrix_rows,
        candidate_rows,
        plan_rows,
        audit_rows,
        leakage_rows,
        scene_errors,
    )
    ready = not any(row.get("blocks_m188") for row in gate_rows)
    claim_rows = build_claim_boundary_rows(ready)
    route_rows = build_route_decision_rows(ready)
    summary_rows = build_policy_summary_rows(candidate_rows)

    by_episode = Counter(str(row.get("adapter_episode_id")) for row in base_candidates)
    expected_matrix_rows = sum(count * count for count in by_episode.values())
    selected_audit = [row for row in audit_rows if row.get("policy_id") == SELECTED_POLICY]
    selected_changed_episode_orders = sum(1 for row in selected_audit if not row.get("detector_order_identical"))
    candidate_counts = Counter(str(row.get("policy_id")) for row in candidate_rows)
    path_found_count = sum(1 for row in matrix_rows if row.get("path_found"))
    coverage = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": READY_STATUS if ready else BLOCKED_STATUS,
        "artifact_output_root": str(out_root),
        "derived_output_root": str(derived_out_root),
        "inside_docker": args.inside_docker,
        "habitat_image": HABITAT_IMAGE,
        "m183_status": m183_cov.get("status"),
        "m186_status": m186_cov.get("status"),
        "episode_rows": len(by_episode),
        "scene_count": len({str(row.get("scene_key")) for row in base_candidates}),
        "category_count": len({str(row.get("object_category")) for row in base_candidates}),
        "base_source_pool_candidate_rows": len(base_candidates),
        "transition_cost_matrix_rows": len(matrix_rows),
        "expected_transition_cost_matrix_rows": expected_matrix_rows,
        "transition_cost_matrix_path_found_rows": path_found_count,
        "transition_cost_matrix_path_missing_rows": len(matrix_rows) - path_found_count,
        "repaired_candidate_rows": len(candidate_rows),
        "trajectory_execution_plan_rows": len(plan_rows),
        "candidate_rows_by_policy": dict(sorted(candidate_counts.items())),
        "policy_ids": POLICY_ORDER,
        "selected_policy_id": SELECTED_POLICY,
        "primary_baseline_policy_id": PROTECTED_BASELINE,
        "confidence_bin_width": CONFIDENCE_BIN_WIDTH,
        "selected_policy_changed_episode_orders": selected_changed_episode_orders,
        "selected_policy_confidence_bin_violations": sum(
            int(row.get("confidence_bin_violation_count") or 0) for row in selected_audit
        ),
        "policy_order_audit_rows": len(audit_rows),
        "policy_order_audit_pass": all(row.get("audit_pass") for row in audit_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_audit_pass": all(row.get("leakage_audit_pass") for row in leakage_rows),
        "readiness_gate_rows": len(gate_rows),
        "scene_error_rows": len(scene_errors),
        "episode_goal_eval_rows_copied_for_metric": len(goal_rows),
        "oracle_path_rows_copied_for_metric": len(oracle_rows),
        "runner_alias_candidate_file_ready": True,
        "runner_alias_plan_file_ready": True,
        "materialization_ready": ready,
        "trajectory_execution_result_ready": False,
        "real_navigation_sr_spl_ready": False,
        "deployable_search_policy_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
        "human_intent_main_claim_ready": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_policy": False,
        "uses_objectnav_eval_goal_or_viewpoint_for_metric": False,
        "limit_episodes": args.limit_episodes,
        "launch_long_job_now": False,
        "selected_next_unit": route_rows[0]["selected_next_unit"],
    }

    for output_dir in (out_root, derived_out_root):
        write_json(output_dir / "coverage.json", coverage)
        write_jsonl(output_dir / "base_candidate_rows.jsonl", base_candidates)
        write_jsonl(output_dir / "transition_cost_matrix_rows.jsonl", matrix_rows)
        write_jsonl(output_dir / "trajectory_cost_matrix_rows.jsonl", matrix_rows)
        write_jsonl(output_dir / "confidence_protected_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "dynamic_stale_overlay_trajectory_candidate_rows.jsonl", candidate_rows)
        write_jsonl(output_dir / "trajectory_execution_plan_rows.jsonl", plan_rows)
        write_jsonl(output_dir / "input_contract_rows.jsonl", input_contract_rows)
        write_jsonl(output_dir / "policy_order_audit_rows.jsonl", audit_rows)
        write_jsonl(output_dir / "policy_order_audit_summary_rows.jsonl", audit_summary_rows)
        write_jsonl(output_dir / "leakage_audit_rows.jsonl", leakage_rows)
        write_jsonl(output_dir / "readiness_gate_rows.jsonl", gate_rows)
        write_jsonl(output_dir / "claim_boundary_rows.jsonl", claim_rows)
        write_jsonl(output_dir / "route_decision_rows.jsonl", route_rows)
        write_jsonl(output_dir / "policy_summary_rows.jsonl", summary_rows)
        write_json(output_dir / "scene_materialization_meta.json", {"scene_errors": scene_errors})
    copy_metric_only_rows(m183_root, out_root, derived_out_root)
    (out_root / "report.md").write_text(
        build_report(coverage, summary_rows, audit_summary_rows, gate_rows),
        encoding="utf-8",
    )
    shutil.copy2(out_root / "report.md", derived_out_root / "report.md")

    print(json.dumps(sanitize_json(coverage), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
