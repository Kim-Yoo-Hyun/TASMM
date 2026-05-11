#!/usr/bin/env python3
"""Run E003-M44 offline replay over an exported pre-cap candidate pool."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M44_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M44_pre_cap_candidate_pool_export_smoke_v0"
M44_VERSION = "e003_m44_pre_cap_candidate_pool_replay_v0"
SUPPORT_AWARE_SCORE_MODE = "confidence_sqrt_depth_support_temporal_v0"
REPLAY_SCORE_MODES = ["confidence", "confidence_sqrt_depth", SUPPORT_AWARE_SCORE_MODE]


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def distance_m(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[idx]) - float(b[idx])) ** 2 for idx in range(3)))


def score_candidate(row: dict[str, Any], score_mode: str) -> float:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    depth_pixels = float(row.get("depth_valid_pixel_count", 0.0) or 0.0)
    sqrt_depth_score = confidence * min(1.0, math.sqrt(depth_pixels) / math.sqrt(5000.0))
    if score_mode == "confidence":
        return confidence
    if score_mode == "confidence_log_depth":
        return confidence * min(1.0, math.log1p(depth_pixels) / math.log1p(5000.0))
    if score_mode == "confidence_sqrt_depth":
        return sqrt_depth_score
    if score_mode == SUPPORT_AWARE_SCORE_MODE:
        temporal = float(row.get("support_temporal_neighbor_frame_count_r2p0m", 0) or 0)
        spatial = float(row.get("support_spatial_neighbor_count_r1p0m", 0) or 0)
        temporal_factor = min(1.0, max(0.0, temporal) / 2.0)
        spatial_factor = min(1.0, max(0.0, spatial) / 8.0)
        return sqrt_depth_score * (1.0 + 0.25 * temporal_factor + 0.10 * spatial_factor)
    raise ValueError(f"unknown selection score mode: {score_mode}")


def select_from_candidate_pool(
    candidate_pool_rows: list[dict[str, Any]],
    *,
    max_predictions: int,
    per_scan_label_cap: int,
    score_mode: str,
    spatial_consolidation_radius_m: float,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in candidate_pool_rows:
        grouped.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(dict(row))

    consolidated = []
    for _, rows in sorted(grouped.items()):
        ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row["raw_candidate_uid"])))
        local_kept: list[dict[str, Any]] = []
        for row in ranked:
            if spatial_consolidation_radius_m <= 0 or all(
                distance_m(row["centroid_world_m"], kept["centroid_world_m"]) > spatial_consolidation_radius_m
                for kept in local_kept
            ):
                local_kept.append(row)
        consolidated.extend(local_kept)

    balanced = []
    balanced_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in consolidated:
        balanced_groups.setdefault((str(row["scan_id"]), str(row["label_canonical"])), []).append(row)
    for key, rows in sorted(balanced_groups.items()):
        ranked = sorted(rows, key=lambda row: (-score_candidate(row, score_mode), str(row["raw_candidate_uid"])))
        for rank, row in enumerate(ranked[:per_scan_label_cap], start=1):
            row = dict(row)
            row["candidate_selection_policy"] = "cap_aware_label_balanced_ranking_v0"
            row["offline_replay_score_mode"] = score_mode
            row["pre_cap_group_key"] = f"{key[0]}::{key[1]}"
            row["pre_cap_group_rank"] = rank
            row["selection_score"] = round(score_candidate(row, score_mode), 8)
            balanced.append(row)

    ranked_final = sorted(balanced, key=lambda row: (-float(row["selection_score"]), str(row["raw_candidate_uid"])))
    selected = ranked_final[:max_predictions]
    for rank, row in enumerate(selected, start=1):
        row["pre_cap_rank"] = rank
    return selected


def selected_keys(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["raw_candidate_uid"]) for row in rows]


def summarize_replay(
    *,
    score_mode: str,
    replay_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    replay_keys = selected_keys(replay_rows)
    runner_keys = selected_keys(runner_rows)
    replay_set = set(replay_keys)
    runner_set = set(runner_keys)
    common = replay_set & runner_set
    score_values = [float(row.get("selection_score", 0.0) or 0.0) for row in replay_rows]
    return {
        "common_with_runner_selected_rows": len(common),
        "first_10_raw_candidate_uids": replay_keys[:10],
        "mean_selection_score": mean(score_values) if score_values else None,
        "ordered_reproduction_match": replay_keys == runner_keys,
        "replay_only_rows": len(replay_set - runner_set),
        "runner_only_rows": len(runner_set - replay_set),
        "score_mode": score_mode,
        "selected_rows": len(replay_rows),
        "set_reproduction_match": replay_set == runner_set,
    }


def build_report(final_coverage: dict[str, Any]) -> str:
    replay = final_coverage.get("offline_replay", {})
    runner_replay = replay.get("runner_score_mode_replay", {})
    return "\n".join(
        [
            "# E003-M44 Pre-Cap Candidate-Pool Export And Replay Smoke",
            "",
            "## Status",
            "",
            str(final_coverage["status"]),
            "",
            "## Facts",
            "",
            f"- Docker smoke status: `{final_coverage.get('docker_smoke_status')}`.",
            f"- Candidate pool export ready: {final_coverage.get('candidate_pool_export', {}).get('ready')}.",
            f"- Candidate pool rows: {final_coverage.get('candidate_pool_export', {}).get('candidate_pool_rows')}.",
            f"- Runner score mode: `{replay.get('runner_score_mode')}`.",
            f"- Runner selected rows: {replay.get('runner_selected_rows')}.",
            f"- Offline replay selected rows: {runner_replay.get('selected_rows')}.",
            f"- Ordered reproduction match: {runner_replay.get('ordered_reproduction_match')}.",
            f"- Set reproduction match: {runner_replay.get('set_reproduction_match')}.",
            f"- Validator errors/warnings: {final_coverage.get('validator_error_rows')} / {final_coverage.get('validator_warning_rows')}.",
            f"- Paper-table command ready: {final_coverage.get('paper_table_command_ready')}.",
            f"- Real RGB-D/open-vocabulary claim ready: {final_coverage.get('real_rgbd_or_open_vocab_claim_ready')}.",
            "",
            "## Paper Claim",
            "",
            "- E003-M44 supports a short reproducibility smoke for replayable pre-cap proposal candidates.",
            "- E003-M44 does not support final real RGB-D/open-vocabulary robustness because it is not scaled heldout evidence.",
            "",
            "## Agent Inference",
            "",
            "- The candidate-pool export gives a stable substrate for score-mode ablations without repeating detector inference.",
            "- The next scaled unit can export one 8-scan candidate pool, then compare support-aware scoring offline.",
            "",
            "## User Decision Needed",
            "",
            "- None for E003-M44.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m44-dir", default=DEFAULT_M44_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m44_dir = args.m44_dir.resolve()
    output_dir = m44_dir / "offline_replay"
    output_dir.mkdir(parents=True, exist_ok=True)

    coverage_path = m44_dir / "coverage.json"
    docker_coverage_path = m44_dir / "docker_coverage.json"
    report_path = m44_dir / "report.md"
    docker_report_path = m44_dir / "docker_report.md"
    docker_coverage = load_json(coverage_path)
    if not docker_coverage_path.exists():
        write_json(docker_coverage_path, docker_coverage)
    if report_path.exists() and not docker_report_path.exists():
        shutil.copyfile(report_path, docker_report_path)

    candidate_pool_path = m44_dir / "container_output" / "pre_cap_candidate_pool.jsonl"
    runner_selected_path = m44_dir / "container_output" / "real_proposals.jsonl"
    candidate_pool_rows = load_jsonl(candidate_pool_path)
    runner_rows = load_jsonl(runner_selected_path)
    run_config = docker_coverage.get("run_config") or {}
    runner_score_mode = str(run_config.get("selection_score_mode"))
    max_predictions = int(run_config.get("max_predictions", 0) or 0)
    per_scan_label_cap = int(run_config.get("pre_cap_per_scan_label_cap", 0) or 0)
    spatial_radius_m = float(run_config.get("pre_cap_spatial_consolidation_radius_m", 0.0) or 0.0)

    replay_summaries = []
    runner_score_mode_replay = None
    for score_mode in REPLAY_SCORE_MODES:
        replay_rows = select_from_candidate_pool(
            candidate_pool_rows,
            max_predictions=max_predictions,
            per_scan_label_cap=per_scan_label_cap,
            score_mode=score_mode,
            spatial_consolidation_radius_m=spatial_radius_m,
        )
        write_jsonl(output_dir / f"replay_{score_mode}.jsonl", replay_rows)
        summary = summarize_replay(score_mode=score_mode, replay_rows=replay_rows, runner_rows=runner_rows)
        replay_summaries.append(summary)
        if score_mode == runner_score_mode:
            runner_score_mode_replay = summary

    runner_score_mode_replay = runner_score_mode_replay or {}
    replay_ready = bool(
        runner_score_mode_replay.get("ordered_reproduction_match")
        and runner_score_mode_replay.get("set_reproduction_match")
    )
    candidate_pool_ready = bool((docker_coverage.get("candidate_pool_export") or {}).get("ready"))
    validator_ok = (
        int(docker_coverage.get("validator_error_rows", 0) or 0) == 0
        and int(docker_coverage.get("validator_warning_rows", 0) or 0) == 0
    )
    final_status = (
        "pre_cap_candidate_pool_replay_smoke_ready"
        if candidate_pool_ready and replay_ready and validator_ok
        else "pre_cap_candidate_pool_replay_smoke_failed"
    )
    offline_replay = {
        "candidate_pool_rows": len(candidate_pool_rows),
        "m44_version": M44_VERSION,
        "replay_summaries": replay_summaries,
        "runner_score_mode": runner_score_mode,
        "runner_score_mode_replay": runner_score_mode_replay,
        "runner_selected_rows": len(runner_rows),
        "score_modes": REPLAY_SCORE_MODES,
    }
    final_coverage = {
        **docker_coverage,
        "docker_smoke_status": docker_coverage.get("status"),
        "m44_version": M44_VERSION,
        "next_recommended_unit": "E003-M45 scaled candidate-pool export and support-aware replay",
        "offline_replay": offline_replay,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "status": final_status,
    }
    write_json(output_dir / "coverage.json", offline_replay)
    write_json(coverage_path, final_coverage)
    write_text(report_path, build_report(final_coverage))
    print(json.dumps(final_coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if final_status == "pre_cap_candidate_pool_replay_smoke_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
