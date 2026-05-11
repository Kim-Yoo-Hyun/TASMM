#!/usr/bin/env python3
"""Run E003-M45 scaled offline replay and proposal matching."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import mean
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M45_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M45_scaled_candidate_pool_export_replay_v0"
MATCHER = EXPERIMENT_ROOT / "tools" / "evaluate_m21_detector_matching.py"
M45_VERSION = "e003_m45_scaled_candidate_pool_export_replay_v0"
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


def safe_rate(num: int | float, denom: int | float) -> float | None:
    if not denom:
        return None
    return float(num) / float(denom)


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
        frame_id = str((row.get("frame_ids") or ["frame-unknown"])[0])
        scan_id = str(row.get("scan_id"))
        row["proposal_uid"] = f"m45-{score_mode}:{scan_id}:{frame_id}:{rank:05d}"
    return selected


def selected_keys(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["raw_candidate_uid"]) for row in rows]


def run_matcher(*, m17_dir: Path, proposal_dir: Path, out_dir: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(MATCHER),
        "--m17-dir",
        str(m17_dir),
        "--m20-dir",
        str(proposal_dir),
        "--out-dir",
        str(out_dir),
    ]
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    coverage = load_json(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else {}
    return {
        "command": cmd,
        "coverage": coverage,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
        "stdout": result.stdout.strip(),
    }


def summarize_mode(
    *,
    mode: str,
    replay_rows: list[dict[str, Any]],
    runner_rows: list[dict[str, Any]],
    matching_result: dict[str, Any],
    m33_baseline: dict[str, Any],
) -> dict[str, Any]:
    runner_set = set(selected_keys(runner_rows))
    replay_set = set(selected_keys(replay_rows))
    matching = matching_result.get("coverage") or {}
    matched = int(matching.get("matched_target_rows", 0) or 0)
    fp = int(matching.get("false_positive_proposal_rows", 0) or 0)
    precision = matching.get("proposal_precision_smoke")
    return {
        "common_with_runner_selected_rows": len(runner_set & replay_set),
        "false_positive_delta_vs_m33": fp - int(m33_baseline.get("false_positive_proposal_rows", 0) or 0),
        "false_positive_proposal_rows": fp,
        "matched_target_delta_vs_m33": matched - int(m33_baseline.get("matched_target_rows", 0) or 0),
        "matched_target_rows": matched,
        "matched_target_retention_vs_m33": safe_rate(matched, int(m33_baseline.get("matched_target_rows", 0) or 0)),
        "ordered_reproduction_match": selected_keys(replay_rows) == selected_keys(runner_rows),
        "proposal_precision": precision,
        "proposal_precision_delta_vs_m33": (
            float(precision) - float(m33_baseline.get("proposal_precision", 0.0) or 0.0)
            if precision is not None
            else None
        ),
        "replay_only_rows": len(replay_set - runner_set),
        "runner_only_rows": len(runner_set - replay_set),
        "scan_target_recall": matching.get("scan_target_recall_smoke"),
        "score_mode": mode,
        "selected_rows": len(replay_rows),
        "set_reproduction_match": replay_set == runner_set,
    }


def choose_support_result(mode_summaries: list[dict[str, Any]], m33_baseline: dict[str, Any]) -> dict[str, Any]:
    by_mode = {row["score_mode"]: row for row in mode_summaries}
    support = by_mode.get(SUPPORT_AWARE_SCORE_MODE, {})
    sqrt_depth = by_mode.get("confidence_sqrt_depth", {})
    confidence = by_mode.get("confidence", {})
    m33_matched = int(m33_baseline.get("matched_target_rows", 0) or 0)
    support_matched = int(support.get("matched_target_rows", 0) or 0)
    support_fp = int(support.get("false_positive_proposal_rows", 0) or 0)
    m33_fp = int(m33_baseline.get("false_positive_proposal_rows", 0) or 0)
    support_precision = support.get("proposal_precision")
    m33_precision = m33_baseline.get("proposal_precision")
    return {
        "support_aware_beats_confidence": (
            support.get("matched_target_rows", -1),
            -support.get("false_positive_proposal_rows", 10**9),
        )
        > (
            confidence.get("matched_target_rows", -1),
            -confidence.get("false_positive_proposal_rows", 10**9),
        ),
        "support_aware_beats_sqrt_depth": (
            support.get("matched_target_rows", -1),
            -support.get("false_positive_proposal_rows", 10**9),
        )
        > (
            sqrt_depth.get("matched_target_rows", -1),
            -sqrt_depth.get("false_positive_proposal_rows", 10**9),
        ),
        "support_aware_false_positive_delta_vs_m33": support_fp - m33_fp,
        "support_aware_matched_target_delta_vs_m33": support_matched - m33_matched,
        "support_aware_precision_delta_vs_m33": (
            float(support_precision) - float(m33_precision)
            if support_precision is not None and m33_precision is not None
            else None
        ),
        "support_aware_quality_positive_vs_m33": (
            support_matched >= m33_matched
            and support_fp < m33_fp
            and support_precision is not None
            and m33_precision is not None
            and float(support_precision) > float(m33_precision)
        ),
    }


def judge_frozen_contract(
    *,
    status: str,
    validator_errors: int,
    validator_warnings: int,
    mode_summaries: list[dict[str, Any]],
    m33_baseline: dict[str, Any],
) -> dict[str, Any]:
    by_mode = {row["score_mode"]: row for row in mode_summaries}
    support = by_mode.get(SUPPORT_AWARE_SCORE_MODE, {})
    sqrt_depth = by_mode.get("confidence_sqrt_depth", {})
    m33_matched = int(m33_baseline.get("matched_target_rows", 0) or 0)
    m33_fp = int(m33_baseline.get("false_positive_proposal_rows", 0) or 0)
    m33_precision = float(m33_baseline.get("proposal_precision", 0.0) or 0.0)
    support_matched = int(support.get("matched_target_rows", 0) or 0)
    support_fp = int(support.get("false_positive_proposal_rows", 0) or 0)
    support_precision = float(support.get("proposal_precision", 0.0) or 0.0)
    sqrt_tuple = (
        int(sqrt_depth.get("matched_target_rows", 0) or 0),
        -int(sqrt_depth.get("false_positive_proposal_rows", 0) or 0),
        float(sqrt_depth.get("proposal_precision", 0.0) or 0.0),
    )
    support_tuple = (support_matched, -support_fp, support_precision)
    ready = status == "scaled_candidate_pool_replay_ready" and validator_errors == 0 and validator_warnings == 0
    not_worse_than_sqrt_depth = support_tuple >= sqrt_tuple
    hard_pass = (
        ready
        and support_matched >= m33_matched
        and support_fp < m33_fp
        and support_precision > m33_precision
        and not_worse_than_sqrt_depth
    )
    weak_positive = ready and support_matched >= 194 and support_fp <= 3049 and support_precision > m33_precision
    reasons = []
    if not ready:
        reasons.append("replay_or_validator_not_ready")
    if support_matched < m33_matched:
        reasons.append("support_aware_matched_targets_below_m33")
    if support_matched < 194:
        reasons.append("support_aware_matched_targets_below_weak_retention_floor")
    if support_fp >= m33_fp:
        reasons.append("support_aware_false_positives_not_reduced_vs_m33")
    if support_fp > 3049:
        reasons.append("support_aware_false_positives_above_weak_positive_floor")
    if support_precision <= m33_precision:
        reasons.append("support_aware_precision_not_improved_vs_m33")
    if not not_worse_than_sqrt_depth:
        reasons.append("support_aware_strictly_worse_than_confidence_sqrt_depth")
    verdict = "hard_pass" if hard_pass else "weak_positive" if weak_positive else "fail_redesign"
    return {
        "contract_version": "e003_m45_result_interpretation_contract_v0",
        "fail_redesign": verdict == "fail_redesign",
        "hard_pass": hard_pass,
        "not_worse_than_confidence_sqrt_depth": not_worse_than_sqrt_depth,
        "reasons": reasons,
        "verdict": verdict,
        "weak_positive": weak_positive,
    }


def build_report(coverage: dict[str, Any]) -> str:
    mode_rows = coverage.get("mode_summaries", [])
    mode_lines = [
        (
            f"- `{row['score_mode']}`: matched {row['matched_target_rows']}, "
            f"FP {row['false_positive_proposal_rows']}, precision {row['proposal_precision']}."
        )
        for row in mode_rows
    ]
    return "\n".join(
        [
            "# E003-M45 Scaled Candidate-Pool Export And Support-Aware Replay",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## Facts",
            "",
            f"- Docker export status: `{coverage['docker_export_status']}`.",
            f"- Candidate pool rows: {coverage['candidate_pool_rows']}.",
            f"- Runner selected rows: {coverage['runner_selected_rows']}.",
            f"- M33 matched / FP / precision: {coverage['m33_matched_target_rows']} / {coverage['m33_false_positive_proposal_rows']} / {coverage['m33_proposal_precision']}.",
            *mode_lines,
            f"- Support-aware quality positive vs M33: {coverage['support_result']['support_aware_quality_positive_vs_m33']}.",
            f"- Frozen contract verdict: `{coverage['frozen_interpretation_contract_verdict']['verdict']}`.",
            f"- Validator errors/warnings: {coverage['validator_error_rows']} / {coverage['validator_warning_rows']}.",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}.",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}.",
            "",
            "## Paper Claim",
            "",
            "- E003-M45 supports a scaled offline comparison over one shared detector candidate pool.",
            "- It does not by itself support final real RGB-D/open-vocabulary robustness until heldout transfer and external baselines are added.",
            "",
            "## Agent Inference",
            "",
            "- The key result is whether support-aware scoring improves false-positive load without losing matched targets compared with the M33 confidence baseline.",
            "- If support-aware scoring is not positive, the next step should be score redesign or external proposal baseline integration rather than a paper-table claim.",
            "",
            "## User Decision Needed",
            "",
            "- None for E003-M45 execution.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m45-dir", default=DEFAULT_M45_DIR, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.m17_dir = args.m17_dir.resolve()
    args.m33_dir = args.m33_dir.resolve()
    args.m45_dir = args.m45_dir.resolve()
    output_dir = args.m45_dir / "offline_replay"
    output_dir.mkdir(parents=True, exist_ok=True)

    coverage_path = args.m45_dir / "coverage.json"
    docker_coverage_path = args.m45_dir / "docker_coverage.json"
    report_path = args.m45_dir / "report.md"
    docker_report_path = args.m45_dir / "docker_report.md"
    if docker_coverage_path.exists():
        docker_coverage = load_json(docker_coverage_path)
    else:
        docker_coverage = load_json(coverage_path)
        write_json(docker_coverage_path, docker_coverage)
    if report_path.exists() and not docker_report_path.exists():
        shutil.copyfile(report_path, docker_report_path)

    m33_coverage = load_json(args.m33_dir / "coverage.json")
    candidate_pool_rows = load_jsonl(args.m45_dir / "container_output" / "pre_cap_candidate_pool.jsonl")
    runner_rows = load_jsonl(args.m45_dir / "container_output" / "real_proposals.jsonl")
    run_config = docker_coverage.get("run_config") or {}
    max_predictions = int(run_config.get("max_predictions", 0) or 0)
    per_scan_label_cap = int(run_config.get("pre_cap_per_scan_label_cap", 0) or 0)
    spatial_radius_m = float(run_config.get("pre_cap_spatial_consolidation_radius_m", 0.0) or 0.0)

    mode_summaries = []
    matcher_results = {}
    for mode in REPLAY_SCORE_MODES:
        replay_rows = select_from_candidate_pool(
            candidate_pool_rows,
            max_predictions=max_predictions,
            per_scan_label_cap=per_scan_label_cap,
            score_mode=mode,
            spatial_consolidation_radius_m=spatial_radius_m,
        )
        proposal_dir = output_dir / mode
        container_dir = proposal_dir / "container_output"
        matching_dir = proposal_dir / "matching"
        write_jsonl(container_dir / "real_proposals.jsonl", replay_rows)
        matcher_result = run_matcher(m17_dir=args.m17_dir, proposal_dir=proposal_dir, out_dir=matching_dir)
        matcher_results[mode] = matcher_result
        mode_summaries.append(
            summarize_mode(
                mode=mode,
                replay_rows=replay_rows,
                runner_rows=runner_rows,
                matching_result=matcher_result,
                m33_baseline=m33_coverage,
            )
        )

    support_result = choose_support_result(mode_summaries, m33_coverage)
    matcher_ok = all(result["returncode"] == 0 for result in matcher_results.values())
    candidate_pool_ready = bool((docker_coverage.get("candidate_pool_export") or {}).get("ready"))
    validator_errors = int(docker_coverage.get("validator_error_rows", 0) or 0)
    validator_warnings = int(docker_coverage.get("validator_warning_rows", 0) or 0)
    status = (
        "scaled_candidate_pool_replay_ready"
        if candidate_pool_ready and matcher_ok and validator_errors == 0 and validator_warnings == 0
        else "scaled_candidate_pool_replay_failed"
    )
    frozen_contract_verdict = judge_frozen_contract(
        status=status,
        validator_errors=validator_errors,
        validator_warnings=validator_warnings,
        mode_summaries=mode_summaries,
        m33_baseline=m33_coverage,
    )
    coverage = {
        "candidate_pool_rows": len(candidate_pool_rows),
        "docker_export_status": docker_coverage.get("status"),
        "frozen_interpretation_contract_path": str(args.m45_dir / "interpretation_contract.json"),
        "frozen_interpretation_contract_verdict": frozen_contract_verdict,
        "m33_false_positive_proposal_rows": int(m33_coverage.get("false_positive_proposal_rows", 0) or 0),
        "m33_matched_target_rows": int(m33_coverage.get("matched_target_rows", 0) or 0),
        "m33_proposal_precision": m33_coverage.get("proposal_precision"),
        "m45_version": M45_VERSION,
        "matcher_results": matcher_results,
        "mode_summaries": mode_summaries,
        "next_recommended_unit": (
            "E003-M46 real proposal to stale-memory bridge"
            if support_result["support_aware_quality_positive_vs_m33"]
            else "E003-M46 support-aware score redesign or external proposal baseline gate"
        ),
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_config": run_config,
        "runner_selected_rows": len(runner_rows),
        "status": status,
        "support_result": support_result,
        "validator_error_rows": validator_errors,
        "validator_warning_rows": validator_warnings,
    }
    write_json(output_dir / "coverage.json", coverage)
    write_json(coverage_path, coverage)
    write_text(report_path, build_report(coverage))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "scaled_candidate_pool_replay_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
