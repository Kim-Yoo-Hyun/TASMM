#!/usr/bin/env python3
"""Plan E005-M79 runner insertion and targeted detector rerun contract."""

from __future__ import annotations

import json
import shlex
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
RUNNER_SOURCE = E003_ROOT / "docker" / "real_proposals" / "run_rgbd_ov_proposals.py"
DEFAULT_M68_ROOT = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0"
DEFAULT_M71_ROOT = EXP_ROOT / "artifacts" / "E005-M71_real_proposal_query_metric_v0"
DEFAULT_M78_ROOT = EXP_ROOT / "artifacts" / "E005-M78_offline_repair_replay_v0"
DEFAULT_OUT_DIR = EXP_ROOT / "artifacts" / "E005-M79_runner_insertion_targeted_rerun_plan_v0"
M80_LAUNCH_ROOT = EXP_ROOT / "artifacts" / "E005-M80_confidence_log_depth_detector_launch_v0"
M80_RUN_ROOT = EXP_ROOT / "artifacts" / "E005-M80_confidence_log_depth_detector_run_v0"
M81_VERIFY_ROOT = EXP_ROOT / "artifacts" / "E005-M81_confidence_log_depth_detector_verification_v0"
M82_QUERY_ROOT = EXP_ROOT / "artifacts" / "E005-M82_confidence_log_depth_query_metric_v0"
VERSION = "e005_m79_runner_insertion_targeted_rerun_plan_v0"
BATCHES = ("heldout_b01", "heldout_b02", "heldout_b03")
FIXED_SCORE_MODE = "confidence_log_depth"
FIXED_POLICY_ID = "offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_rate(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 6)


def safe_mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(float(mean(values)), 6)


def find_line(source_lines: list[str], pattern: str) -> int | None:
    for index, line in enumerate(source_lines, start=1):
        if pattern in line:
            return index
    return None


def replace_arg(command: list[str], flag: str, value: str) -> list[str]:
    result = list(command)
    if flag not in result:
        result.extend([flag, value])
        return result
    index = result.index(flag)
    if index + 1 >= len(result):
        raise RuntimeError(f"missing value for {flag}")
    result[index + 1] = value
    return result


def batch_query_map(m68_root: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for batch in BATCHES:
        for row in read_jsonl(m68_root / "batches" / batch / "direct_bridge_query_rows.jsonl"):
            out[str(row["bridge_query_uid"])] = row
    return out


def summarize_m78_by_batch(m68_root: Path, m78_root: Path) -> list[dict[str, Any]]:
    query_by_uid = batch_query_map(m68_root)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(m78_root / "query_policy_rows.jsonl"):
        query = query_by_uid.get(str(row["query_uid"]))
        if not query:
            continue
        merged = dict(row)
        merged["batch_id"] = query["m68_batch_id"]
        grouped[str(query["m68_batch_id"])].append(merged)

    rows: list[dict[str, Any]] = []
    for batch in BATCHES:
        items = grouped.get(batch, [])
        successes = [row for row in items if row["query_bridge_success"]]
        detected = [row for row in items if row["target_detected"]]
        rows.append(
            {
                "batch_id": batch,
                "expected_policy_id": FIXED_POLICY_ID,
                "query_rows": len(items),
                "target_detected_rows": len(detected),
                "target_detected_rate": safe_rate(len(detected), len(items)),
                "top5_success_rows": len(successes),
                "top5_success_rate": safe_rate(len(successes), len(items)),
                "mean_expected_search_cost": safe_mean([int(row["expected_search_cost"]) for row in items]),
                "mean_attempt_spl_proxy": safe_mean([float(row["attempt_spl_proxy"]) for row in items]),
            }
        )
    return rows


def summarize_m71_detector_by_batch(m71_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in BATCHES:
        metrics = read_json(m71_root / batch / "metrics.json")
        detector = metrics.get("policy_metrics", {}).get("real_detector_confidence_top5_v0", {})
        rows.append(
            {
                "batch_id": batch,
                "policy_id": "real_detector_confidence_top5_v0",
                "query_rows": detector.get("rows"),
                "target_detected_rows": detector.get("target_detected_rows"),
                "top5_success_rows": detector.get("query_bridge_success_rows"),
                "mean_expected_search_cost": detector.get("mean_expected_search_cost"),
                "mean_attempt_spl_proxy": detector.get("mean_attempt_spl_proxy"),
            }
        )
    return rows


def build_m80_command_plan(m68_root: Path) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for batch in BATCHES:
        source = read_json(m68_root / "batches" / batch / "detector_run_command_plan.json")
        command = [str(part) for part in source["exact_command"]]
        run_out_dir = M80_RUN_ROOT / batch
        command = replace_arg(command, "--out-dir", str(run_out_dir))
        command = replace_arg(command, "--selection-score-mode", FIXED_SCORE_MODE)
        command = replace_arg(command, "--candidate-selection-policy", "cap_aware_label_balanced_ranking_v0")
        command = replace_arg(command, "--pre-cap-per-scan-label-cap", "24")
        command = replace_arg(command, "--pre-cap-spatial-consolidation-radius-m", "0.5")
        if "--export-pre-cap-candidate-pool" not in command:
            command.append("--export-pre-cap-candidate-pool")

        verify_command = [
            "python",
            "experiments/E005_external_baseline_transition/tools/verify_m70_full_denominator_real_proposal_detector_batch.py",
            "--batch-id",
            batch,
            "--launch-root",
            str(M80_LAUNCH_ROOT),
            "--run-root",
            str(M80_RUN_ROOT),
            "--out-root",
            str(M81_VERIFY_ROOT),
            "--require-ready",
        ]
        metric_command = [
            "python",
            "experiments/E005_external_baseline_transition/tools/run_m71_real_proposal_query_metrics.py",
            "--batch-id",
            batch,
            "--m69-root",
            str(M80_RUN_ROOT),
            "--m70-root",
            str(M81_VERIFY_ROOT),
            "--out-root",
            str(M82_QUERY_ROOT),
        ]
        tmux_session = f"e005_m80_confidence_log_depth_{batch}"
        log_template = f"logs/<YYYYMMDD_HHMMSS>_e005_m80_confidence_log_depth_{batch}.log"
        plans.append(
            {
                "batch_id": batch,
                "source_command_plan": str(m68_root / "batches" / batch / "detector_run_command_plan.json"),
                "exact_command": command,
                "shell_command": shlex.join(command),
                "output_dir": str(run_out_dir),
                "launch_record_dir": str(M80_LAUNCH_ROOT / batch),
                "verification_command": verify_command,
                "query_metric_command": metric_command,
                "tmux_session": tmux_session,
                "tmux_template": (
                    f"tmux new-session -d -s {tmux_session} "
                    f"'cd {ROOT} && <sudo-password-provider> {shlex.join(command)} > {log_template} 2>&1'"
                ),
                "expected_files": [
                    str(run_out_dir / "coverage.json"),
                    str(run_out_dir / "container_output" / "real_proposals.jsonl"),
                    str(run_out_dir / "container_output" / "pre_cap_candidate_pool.jsonl"),
                    str(run_out_dir / "container_output" / "pre_cap_policy_summary.json"),
                    str(run_out_dir / "matching" / "coverage.json"),
                    str(run_out_dir / "validator" / "coverage.json"),
                ],
            }
        )
    return plans


def inspect_runner() -> dict[str, Any]:
    lines = RUNNER_SOURCE.read_text(encoding="utf-8").splitlines()
    line_map = {
        "score_candidate_function": find_line(lines, "def score_candidate("),
        "confidence_log_depth_branch": find_line(lines, 'if score_mode == "confidence_log_depth"'),
        "selection_function": find_line(lines, "def select_cap_aware_label_balanced_candidates("),
        "spatial_consolidation": find_line(lines, "distance_m(row[\"centroid_world_m\"], kept[\"centroid_world_m\"])"),
        "group_cap_rank": find_line(lines, "row[\"pre_cap_group_rank\"] = rank"),
        "selection_score_write": find_line(lines, "row[\"selection_score\"] = round(score_candidate(row, score_mode), 8)"),
        "argparse_selection_score_mode": find_line(lines, '"--selection-score-mode"'),
        "pre_cap_policy_summary_write": find_line(lines, "write_json(pre_cap_policy_output, pre_cap_policy_summary)"),
        "pre_cap_candidate_pool_export": find_line(lines, "write_jsonl(pre_cap_candidate_pool_output, pre_cap_candidate_pool_rows)"),
    }
    supported = all(
        line_map[key] is not None
        for key in [
            "score_candidate_function",
            "confidence_log_depth_branch",
            "selection_function",
            "argparse_selection_score_mode",
            "pre_cap_policy_summary_write",
            "pre_cap_candidate_pool_export",
        ]
    )
    return {
        "runner_source": str(RUNNER_SOURCE),
        "line_map": line_map,
        "fixed_policy_score_mode": FIXED_SCORE_MODE,
        "runner_source_edit_required": not supported,
        "fixed_policy_runner_supported": supported,
        "insertion_point_id": "select_cap_aware_label_balanced_candidates.score_candidate_before_spatial_consolidation_and_caps",
        "allowed_policy_inputs": [
            "scan_id",
            "label_canonical",
            "confidence",
            "depth_valid_pixel_count",
            "centroid_world_m",
            "frame_ids",
            "fixed per-scan-label cap",
            "fixed spatial consolidation radius",
        ],
        "blocked_policy_inputs": [
            "target_uid",
            "object_instance_id_rescan",
            "matched_3dssg_instance_id",
            "match_distance_m",
            "success labels",
            "M77/M78 evaluation outcome",
        ],
    }


def build_decision(
    runner: dict[str, Any],
    m78_coverage: dict[str, Any],
    expected_rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    m78_ready = m78_coverage.get("status") == "e005_m78_offline_repair_replay_ready"
    all_expected_rows = sum(int(row["top5_success_rows"]) for row in expected_rows)
    runner_supported = bool(runner["fixed_policy_runner_supported"])
    detector_by_batch = {row["batch_id"]: row for row in detector_rows}
    gain_rows = []
    for row in expected_rows:
        detector = detector_by_batch.get(row["batch_id"], {})
        detector_success = int(detector.get("top5_success_rows") or 0)
        gain_rows.append(
            {
                "batch_id": row["batch_id"],
                "detector_top5_rows": detector_success,
                "m78_top5_rows": int(row["top5_success_rows"]),
                "delta_rows": int(row["top5_success_rows"]) - detector_success,
            }
        )
    first_batch = max(gain_rows, key=lambda row: (row["delta_rows"], row["m78_top5_rows"]))["batch_id"]
    if runner_supported and m78_ready and all_expected_rows == int(m78_coverage.get("fixed_top5_success_rows", -1)):
        selected_route = "gain_batch_first_targeted_rerun_then_remaining_batches_if_reproduction_holds"
        next_unit = f"E005-M80 confidence-log-depth targeted detector rerun launch for {first_batch}"
        rationale = "The fixed policy is already expressible by runner args; rerun the largest-gain batch first to test the repair claim directly."
    else:
        selected_route = "repair_runner_or_m78_contract_before_rerun"
        next_unit = "E005-M80 runner contract repair"
        rationale = "Runner support or M78 consistency checks failed; do not launch detector rerun yet."
    return {
        "selected_next_route": selected_route,
        "next_recommended_unit": next_unit,
        "rationale": rationale,
        "fixed_policy_id": FIXED_POLICY_ID,
        "fixed_policy_runner_supported": runner_supported,
        "runner_source_edit_required": not runner_supported,
        "first_rerun_batch": first_batch,
        "batch_gain_rows": gain_rows,
        "gain_batch_first_then_scale": selected_route.startswith("gain_batch_first"),
        "expected_all_batch_top5_success_rows": all_expected_rows,
        "m78_fixed_top5_success_rows": m78_coverage.get("fixed_top5_success_rows"),
        "claim_boundary": {
            "m79_is_plan_not_detector_result": True,
            "final_real_rgbd_open_vocab_robustness_claim_ready": False,
            "deployable_search_policy_claim_ready": False,
            "real_navigation_sr_spl_claim_ready": False,
            "human_intent_main_claim_ready": False,
        },
    }


def build_report(
    coverage: dict[str, Any],
    runner: dict[str, Any],
    expected_rows: list[dict[str, Any]],
    detector_rows: list[dict[str, Any]],
    decision: dict[str, Any],
) -> str:
    detector_by_batch = {row["batch_id"]: row for row in detector_rows}
    lines = [
        "# E005-M79 Runner Insertion / Targeted Rerun Plan",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Runner source: `{runner['runner_source']}`.",
        f"- Source edit required: {runner['runner_source_edit_required']}.",
        f"- Fixed score mode: `{runner['fixed_policy_score_mode']}`.",
        f"- Insertion point: `{runner['insertion_point_id']}`.",
        f"- M78 fixed top5: {coverage['m78_fixed_top5_success_rows']} / {coverage['query_rows']}.",
        f"- M78 proposal precision: {coverage['m78_fixed_proposal_precision']}.",
        "",
        "## Expected Rerun Targets",
        "",
        "| Batch | M75 Detector Top5 | M78 Fixed Top5 | M78 Target Detected |",
        "| --- | ---: | ---: | ---: |",
        *[
            f"| `{row['batch_id']}` | {detector_by_batch[row['batch_id']].get('top5_success_rows')} / {detector_by_batch[row['batch_id']].get('query_rows')} | {row['top5_success_rows']} / {row['query_rows']} | {row['target_detected_rows']} / {row['query_rows']} |"
            for row in expected_rows
        ],
        "",
        "## Decision",
        "",
        f"- Selected route: `{decision['selected_next_route']}`.",
        f"- Next unit: {decision['next_recommended_unit']}.",
        f"- First rerun batch: `{decision['first_rerun_batch']}`.",
        f"- Rationale: {decision['rationale']}",
        "",
        "## Claim Boundary",
        "",
        "- M79 is a plan/contract artifact, not a detector result.",
        "- The next detector run must write to a new output root and must not overwrite M69/M75 artifacts.",
        "- Final real RGB-D/open-vocabulary robustness, deployable search policy, and real navigation `SR` / `SPL` remain blocked.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    m78_coverage = read_json(DEFAULT_M78_ROOT / "coverage.json")
    runner = inspect_runner()
    expected_rows = summarize_m78_by_batch(DEFAULT_M68_ROOT, DEFAULT_M78_ROOT)
    detector_rows = summarize_m71_detector_by_batch(DEFAULT_M71_ROOT)
    command_plans = build_m80_command_plan(DEFAULT_M68_ROOT)
    decision = build_decision(runner, m78_coverage, expected_rows, detector_rows)
    coverage = {
        "status": "e005_m79_runner_insertion_targeted_rerun_plan_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runner_source_edit_required": runner["runner_source_edit_required"],
        "fixed_policy_runner_supported": runner["fixed_policy_runner_supported"],
        "fixed_policy_id": FIXED_POLICY_ID,
        "fixed_score_mode": FIXED_SCORE_MODE,
        "m78_fixed_top5_success_rows": m78_coverage.get("fixed_top5_success_rows"),
        "m78_fixed_proposal_precision": m78_coverage.get("fixed_proposal_precision"),
        "query_rows": m78_coverage.get("query_rows"),
        "expected_all_batch_top5_success_rows": decision["expected_all_batch_top5_success_rows"],
        "command_plan_rows": len(command_plans),
        "selected_next_route": decision["selected_next_route"],
        "next_recommended_unit": decision["next_recommended_unit"],
        "first_rerun_batch": decision["first_rerun_batch"],
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "deployable_search_policy_claim_ready": False,
        "real_navigation_sr_spl_claim_ready": False,
        "human_intent_main_claim_ready": False,
    }

    write_json(out_dir / "coverage.json", coverage)
    write_json(out_dir / "runner_insertion_contract.json", runner)
    write_json(out_dir / "targeted_rerun_command_plan.json", {"batches": command_plans})
    write_json(out_dir / "route_decision.json", decision)
    write_jsonl(out_dir / "expected_m78_batch_rows.jsonl", expected_rows)
    write_jsonl(out_dir / "m75_detector_batch_rows.jsonl", detector_rows)
    write_text(out_dir / "report.md", build_report(coverage, runner, expected_rows, detector_rows, decision))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
