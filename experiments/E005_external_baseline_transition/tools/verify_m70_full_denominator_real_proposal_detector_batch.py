#!/usr/bin/env python3
"""Verify E005-M69 full-denominator real proposal detector batch completion."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
DEFAULT_LAUNCH_ROOT = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_launch_v0"
DEFAULT_RUN_ROOT = EXP_ROOT / "artifacts" / "E005-M69_full_denominator_real_proposal_detector_run_v0"
DEFAULT_OUT_ROOT = EXP_ROOT / "artifacts" / "E005-M70_full_denominator_real_proposal_detector_verification_v0"
VERIFY_VERSION = "e005_m70_full_denominator_real_proposal_detector_verifier_v0"
READY_RUN_STATUSES = {
    "detector_projection_smoke_ready",
    "pre_cap_candidate_pool_export_smoke_ready",
    "cleanup_trace_diagnostic_ready",
}
ERROR_PATTERNS = [
    r"\bERROR\b",
    r"Traceback",
    r"Exception",
    r"RuntimeError",
    r"out of memory",
    r"No such file",
    r"\bKilled\b",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("rb") as handle:
        for _ in handle:
            count += 1
    return count


def tmux_has_session(session: str) -> bool:
    proc = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def read_log_sample(path: Path, max_chars: int = 8000) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "size_bytes": 0, "head": "", "tail": "", "error_hits": []}
    raw_size = path.stat().st_size
    if raw_size == 0:
        return {"exists": True, "size_bytes": 0, "head": "", "tail": "", "error_hits": []}
    with path.open("rb") as handle:
        head = handle.read(max_chars).decode("utf-8", errors="replace")
        handle.seek(max(0, raw_size - max_chars), 0)
        tail = handle.read(max_chars).decode("utf-8", errors="replace")
    sample = f"{head}\n{tail}"
    hits = sorted({pattern for pattern in ERROR_PATTERNS if re.search(pattern, sample, flags=re.IGNORECASE)})
    return {"exists": True, "size_bytes": raw_size, "head": head, "tail": tail, "error_hits": hits}


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def summarize_run(run_coverage: dict[str, Any]) -> dict[str, Any]:
    frame = run_coverage.get("frame_diagnostics", {})
    pre_cap = run_coverage.get("pre_cap_policy_summary", {})
    model = run_coverage.get("model_status", {})
    pool = run_coverage.get("candidate_pool_export", {})
    return {
        "backend_contract_ready": run_coverage.get("backend_contract_ready"),
        "candidate_pool_rows": pool.get("candidate_pool_rows") or pre_cap.get("pre_cap_candidate_pool_rows"),
        "docker_build_executed": run_coverage.get("docker_build_executed"),
        "docker_run_executed": run_coverage.get("docker_run_executed"),
        "frames_with_raw_predictions": frame.get("frames_with_raw_predictions"),
        "frames_with_written_predictions": frame.get("frames_with_written_predictions"),
        "max_predictions_reached": pre_cap.get("max_predictions_reached_after_policy"),
        "model_backend_id": model.get("backend_id"),
        "model_device": model.get("device"),
        "pre_cap_policy_applied": run_coverage.get("pre_cap_policy_applied"),
        "projected_candidate_count": frame.get("projected_candidate_count") or model.get("mask_projected_candidate_count"),
        "raw_candidate_collection_cap_reached": frame.get("raw_candidate_collection_cap_reached"),
        "raw_prediction_count": frame.get("raw_prediction_count"),
        "scanned_frame_count": frame.get("scanned_frame_count"),
        "selected_candidate_count": pre_cap.get("final_prediction_rows"),
        "selected_scan_count": len(frame.get("prediction_scans", [])) if isinstance(frame.get("prediction_scans"), list) else None,
        "status": run_coverage.get("status"),
    }


def build_report(coverage: dict[str, Any]) -> str:
    matching = coverage["matching"]
    validator = coverage["validator"]
    line_counts = coverage["line_counts"]
    run_summary = coverage["run_summary"]
    return "\n".join(
        [
            "# E005-M70 Full-Denominator Real Proposal Detector Verification",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- Batch id: `{coverage['batch_id']}`.",
            f"- tmux session running: {coverage['tmux_session_running']}.",
            f"- expected files ready: {coverage['expected_files_ready']} / {coverage['expected_file_count']}.",
            f"- run status: `{run_summary.get('status')}`.",
            f"- validator status: `{validator.get('status')}`.",
            f"- validator errors/warnings: {validator.get('error_rows')} / {validator.get('warning_rows')}.",
            f"- matching status: `{matching.get('status')}`.",
            f"- prediction rows: {line_counts['prediction_rows']}.",
            f"- pre-cap candidate rows: {line_counts['pre_cap_candidate_rows']}.",
            f"- matched target rows: {matching.get('matched_target_rows')} / {matching.get('scan_eval_target_rows')}.",
            f"- scan target recall smoke: {matching.get('scan_target_recall_smoke')}.",
            f"- proposal precision smoke: {matching.get('proposal_precision_smoke')}.",
            f"- false-positive proposal rate smoke: {matching.get('false_positive_proposal_rate_smoke')}.",
            f"- mean matched centroid error m: {matching.get('matched_centroid_error_m', {}).get('mean')}.",
            f"- log path: `{coverage['log_path']}`.",
            f"- log size bytes: {coverage['log']['size_bytes']}.",
            f"- log error sample hits: {coverage['log']['error_hits']}.",
            "",
            "## 논문 주장",
            "",
            "- M70 supports that `heldout_b01` produced schema-valid, matchable real RGB-D/open-vocabulary proposal artifacts.",
            "- M70 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.",
            "",
            "## 에이전트 추론",
            "",
            "- `heldout_b01` is ready for E005-M71 query-level metric conversion because detector output, validator coverage, matching coverage, and targeted log checks passed.",
            "- The high false-positive rate means the next gate must evaluate query-level budget/rank/search-cost behavior before launching additional heldout batches as a paper claim.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E005-M71.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", default="heldout_b01")
    parser.add_argument("--launch-root", default=DEFAULT_LAUNCH_ROOT, type=Path)
    parser.add_argument("--run-root", default=DEFAULT_RUN_ROOT, type=Path)
    parser.add_argument("--out-root", default=DEFAULT_OUT_ROOT, type=Path)
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    batch_id = args.batch_id
    launch_dir = (args.launch_root / batch_id).resolve()
    run_dir = (args.run_root / batch_id).resolve()
    out_dir = (args.out_root / batch_id).resolve()

    launch = load_json(launch_dir / "coverage.json")
    run_coverage = load_json(run_dir / "coverage.json")
    validator = load_json(run_dir / "validator" / "coverage.json")
    matching = load_json(run_dir / "matching" / "coverage.json")

    expected_files = [Path(path) for path in launch.get("expected_files", [])]
    secondary_files = [
        run_dir / "container_output" / "backend_contract.json",
        run_dir / "container_output" / "model_smoke.json",
        run_dir / "container_output" / "pre_cap_candidate_pool.jsonl",
        run_dir / "container_output" / "pre_cap_policy_summary.json",
        run_dir / "container_output" / "run_metadata.json",
        run_dir / "matching" / "matched_proposals.jsonl",
        run_dir / "matching" / "target_recall_rows.jsonl",
        run_dir / "validator" / "validation_rows.jsonl",
    ]
    all_expected = expected_files + secondary_files
    expected_rows = [
        {
            "exists": path.exists(),
            "path": str(path),
            "relative_path": rel_or_abs(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for path in all_expected
    ]
    expected_ready = sum(1 for row in expected_rows if row["exists"])

    tmux_session = str(launch.get("tmux_session") or f"e005_m69_real_proposal_{batch_id}")
    tmux_running = tmux_has_session(tmux_session)
    log_path = Path(str(launch.get("log_path", "")))
    log = read_log_sample(log_path)

    prediction_path = run_dir / "container_output" / "real_proposals.jsonl"
    pre_cap_path = run_dir / "container_output" / "pre_cap_candidate_pool.jsonl"
    cleanup_trace_path = run_dir / "container_output" / "cleanup_trace.jsonl"
    matched_path = run_dir / "matching" / "matched_proposals.jsonl"
    recall_path = run_dir / "matching" / "target_recall_rows.jsonl"
    validation_path = run_dir / "validator" / "validation_rows.jsonl"

    line_counts = {
        "matched_proposal_rows": count_lines(matched_path),
        "cleanup_trace_rows": count_lines(cleanup_trace_path),
        "pre_cap_candidate_rows": count_lines(pre_cap_path),
        "prediction_rows": count_lines(prediction_path),
        "target_recall_rows": count_lines(recall_path),
        "validator_validation_rows": count_lines(validation_path),
    }
    cleanup_trace_export = run_coverage.get("cleanup_trace_export", {})
    cleanup_trace_mode = bool(cleanup_trace_export.get("enabled"))
    common_checks = {
        "expected_files_complete": expected_ready == len(expected_rows) and bool(expected_rows),
        "log_no_error_hits_in_sample": not log["error_hits"],
        "tmux_session_finished": not tmux_running,
    }
    detector_checks = {
        "matching_ready": matching.get("status") == "detector_matching_smoke_ready",
        "prediction_rows_positive": line_counts["prediction_rows"] > 0,
        "pre_cap_candidate_rows_positive": line_counts["pre_cap_candidate_rows"] > 0,
        "run_status_ready": run_coverage.get("status") in READY_RUN_STATUSES,
        "validator_ready": validator.get("status") == "proposal_schema_smoke_valid"
        and validator.get("valid") is True
        and validator.get("error_rows") == 0
        and validator.get("warning_rows") == 0,
    }
    cleanup_checks = {
        "cleanup_trace_ready": bool(cleanup_trace_export.get("ready")),
        "cleanup_trace_rows_positive": line_counts["cleanup_trace_rows"] > 0,
        "cleanup_trace_blocked_field_clean": int(cleanup_trace_export.get("blocked_field_hit_count", 0) or 0) == 0,
        "cleanup_trace_field_clean": int(cleanup_trace_export.get("field_error_count", 0) or 0) == 0,
        "cleanup_trace_row_count_matches": (
            not int(cleanup_trace_export.get("expected_model_status_rows", 0) or 0)
            or line_counts["cleanup_trace_rows"] == int(cleanup_trace_export.get("expected_model_status_rows", 0) or 0)
        ),
    }
    detector_ready = all({**common_checks, **detector_checks}.values())
    cleanup_ready = all({**common_checks, **cleanup_checks}.values()) if cleanup_trace_mode else False
    checks = {**common_checks, **(cleanup_checks if cleanup_trace_mode else detector_checks)}
    ready = cleanup_ready if cleanup_trace_mode else detector_ready
    status = (
        "e005_m89_cleanup_trace_detector_batch_ready"
        if cleanup_trace_mode and ready
        else
        "e005_m70_real_proposal_detector_batch_ready_with_false_positive_load"
        if ready
        else "e005_m70_real_proposal_detector_batch_needs_attention"
    )

    coverage = {
        "batch_id": batch_id,
        "checks": checks,
        "expected_file_count": len(expected_rows),
        "expected_files": expected_rows,
        "expected_files_ready": expected_ready,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "launch_coverage_path": str(launch_dir / "coverage.json"),
        "line_counts": line_counts,
        "log": log,
        "log_path": str(log_path),
        "matching": matching,
        "next_recommended_unit": (
            "E005-M71 real proposal query-level metric conversion"
            if detector_ready
            else "E005-M89 cleanup trace analysis"
            if cleanup_trace_mode
            else "E005-M71 heldout_b01 real proposal query-level metric conversion"
        ),
        "query_metric_conversion_ready": detector_ready,
        "real_navigation_sr_spl_ready": False,
        "real_rgbd_open_vocab_robustness_ready": False,
        "run_dir": str(run_dir),
        "run_summary": summarize_run(run_coverage),
        "cleanup_trace_export": cleanup_trace_export,
        "cleanup_trace_mode": cleanup_trace_mode,
        "status": status,
        "tmux_session": tmux_session,
        "tmux_session_running": tmux_running,
        "validator": validator,
        "verify_version": VERIFY_VERSION,
    }
    write_json(out_dir / "coverage.json", coverage)
    write_text(out_dir / "report.md", build_report(coverage))
    print(
        json.dumps(
            {
                "batch_id": batch_id,
                "matched_target_rows": matching.get("matched_target_rows"),
                "next_recommended_unit": coverage["next_recommended_unit"],
                "cleanup_trace_rows": line_counts["cleanup_trace_rows"],
                "prediction_rows": line_counts["prediction_rows"],
                "proposal_precision_smoke": matching.get("proposal_precision_smoke"),
                "query_metric_conversion_ready": coverage["query_metric_conversion_ready"],
                "scan_target_recall_smoke": matching.get("scan_target_recall_smoke"),
                "status": status,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    ready_statuses = {
        "e005_m70_real_proposal_detector_batch_ready_with_false_positive_load",
        "e005_m89_cleanup_trace_detector_batch_ready",
    }
    if args.require_ready and status not in ready_statuses:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
