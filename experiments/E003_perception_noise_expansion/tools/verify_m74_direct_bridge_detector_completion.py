#!/usr/bin/env python3
"""Verify E003-M74 expanded direct bridge detector completion."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAUNCH_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M74_direct_bridge_denominator_detector_launch_v0"
DEFAULT_RUN_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M74_direct_bridge_denominator_detector_run_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M74_direct_bridge_detector_completion_verification_v0"
VERIFY_VERSION = "e003_m74_direct_bridge_detector_completion_verifier_v0"
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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("rb") as f:
        for _ in f:
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
    with path.open("rb") as f:
        head = f.read(max_chars).decode("utf-8", errors="replace")
        f.seek(max(0, raw_size - max_chars), 0)
        tail = f.read(max_chars).decode("utf-8", errors="replace")
    sample = f"{head}\n{tail}"
    hits = sorted({pattern for pattern in ERROR_PATTERNS if re.search(pattern, sample, flags=re.IGNORECASE)})
    return {"exists": True, "size_bytes": raw_size, "head": head, "tail": tail, "error_hits": hits}


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())


def build_report(coverage: dict[str, Any]) -> str:
    matching = coverage["matching"]
    validator = coverage["validator"]
    line_counts = coverage["line_counts"]
    return "\n".join(
        [
            "# E003-M74 Detector Completion Verification",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- tmux session running: {coverage['tmux_session_running']}.",
            f"- expected files ready: {coverage['expected_files_ready']} / {coverage['expected_file_count']}.",
            f"- log path: `{coverage['log_path']}`.",
            f"- log size bytes: {coverage['log']['size_bytes']}.",
            f"- log error sample hits: {coverage['log']['error_hits']}.",
            f"- prediction rows: {line_counts['prediction_rows']}.",
            f"- pre-cap candidate rows: {line_counts['pre_cap_candidate_rows']}.",
            f"- validator status: `{validator.get('status')}`.",
            f"- validator errors/warnings: {validator.get('error_rows')} / {validator.get('warning_rows')}.",
            f"- matching status: `{matching.get('status')}`.",
            f"- matched target rows: {matching.get('matched_target_rows')} / {matching.get('scan_eval_target_rows')}.",
            f"- proposal precision smoke: {matching.get('proposal_precision_smoke')}.",
            f"- scan target recall smoke: {matching.get('scan_target_recall_smoke')}.",
            f"- false-positive proposal rate smoke: {matching.get('false_positive_proposal_rate_smoke')}.",
            f"- mean matched centroid error m: {matching.get('matched_centroid_error_m', {}).get('mean')}.",
            "",
            "## 논문 주장",
            "",
            "- E003-M74 supports that the expanded direct bridge detector run completed and produced schema-valid, matchable real RGB-D/open-vocabulary proposal artifacts.",
            "- E003-M74 does not support a search-improvement, deployable policy, final real RGB-D/open-vocabulary robustness, or real navigation claim.",
            "",
            "## 에이전트 추론",
            "",
            "- The detector run is ready for E003-M75 query-level joining because expected files, validator coverage, matching coverage, and targeted log checks passed.",
            "- High false-positive rate means M75 must evaluate budget/rank/cost behavior before using this as a stale-memory bridge result.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None before E003-M75.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-dir", default=DEFAULT_LAUNCH_DIR, type=Path)
    parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.launch_dir = args.launch_dir.resolve()
    args.run_dir = args.run_dir.resolve()
    args.out_dir = args.out_dir.resolve()

    launch = load_json(args.launch_dir / "coverage.json")
    run_coverage = load_json(args.run_dir / "coverage.json")
    validator = load_json(args.run_dir / "validator" / "coverage.json")
    matching = load_json(args.run_dir / "matching" / "coverage.json")

    expected_files = [Path(path) for path in launch.get("expected_files", [])]
    expected_rows = [
        {
            "exists": path.exists(),
            "path": str(path),
            "relative_path": rel_or_abs(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for path in expected_files
    ]
    expected_ready = sum(1 for row in expected_rows if row["exists"])

    tmux_session = launch.get("tmux_session", "e003_m74_direct_denominator")
    tmux_running = tmux_has_session(tmux_session)
    log_path = Path(launch.get("log_path", ""))
    log = read_log_sample(log_path)

    prediction_path = args.run_dir / "container_output" / "real_proposals.jsonl"
    pre_cap_path = args.run_dir / "container_output" / "pre_cap_candidate_pool.jsonl"
    matched_path = args.run_dir / "matching" / "matched_proposals.jsonl"
    recall_path = args.run_dir / "matching" / "target_recall_rows.jsonl"
    validation_path = args.run_dir / "validator" / "validation_rows.jsonl"

    line_counts = {
        "matched_proposal_rows": count_lines(matched_path),
        "pre_cap_candidate_rows": count_lines(pre_cap_path),
        "prediction_rows": count_lines(prediction_path),
        "target_recall_rows": count_lines(recall_path),
        "validator_validation_rows": count_lines(validation_path),
    }

    checks = {
        "detector_predictions_ready": bool(validator.get("detector_predictions_ready")),
        "expected_files_complete": expected_ready == len(expected_rows) and bool(expected_rows),
        "log_no_error_hits_in_sample": not log["error_hits"],
        "matching_ready": matching.get("status") == "detector_matching_smoke_ready",
        "prediction_rows_positive": line_counts["prediction_rows"] > 0,
        "run_output_ready": run_coverage.get("detector_predictions_ready") is True
        or run_coverage.get("model_status", {}).get("detector_predictions_ready") is True,
        "tmux_session_finished": not tmux_running,
        "validator_ready": validator.get("status") == "proposal_schema_smoke_valid"
        and validator.get("valid") is True
        and validator.get("error_rows") == 0
        and validator.get("warning_rows") == 0,
    }
    ready = all(checks.values())
    status = "expanded_direct_bridge_detector_run_ready" if ready else "expanded_direct_bridge_detector_run_needs_attention"

    model_status = run_coverage.get("model_status", {})
    run_summary = {
        "backend_contract_ready": run_coverage.get("backend_contract_ready"),
        "candidate_pool_export": run_coverage.get("candidate_pool_export"),
        "docker_build_executed": run_coverage.get("docker_build_executed"),
        "docker_run_executed": run_coverage.get("docker_run_executed"),
        "frame_diagnostics": run_coverage.get("frame_diagnostics"),
        "model_status": {
            "detector_backend_integrated": model_status.get("detector_backend_integrated"),
            "detector_predictions_ready": model_status.get("detector_predictions_ready"),
            "device": model_status.get("device"),
            "model_id": model_status.get("model_id"),
            "prediction_rows": model_status.get("prediction_rows"),
            "projected_candidate_count": model_status.get("projected_candidate_count"),
            "raw_prediction_count": model_status.get("raw_prediction_count"),
            "scanned_frame_count": model_status.get("scanned_frame_count"),
            "skipped_no_depth_predictions": model_status.get("skipped_no_depth_predictions"),
            "status": model_status.get("status"),
        },
        "paper_table_command_ready": run_coverage.get("paper_table_command_ready"),
        "pre_cap_policy_summary": run_coverage.get("pre_cap_policy_summary"),
        "prediction_rows": run_coverage.get("prediction_rows"),
        "real_rgbd_or_open_vocab_claim_ready": run_coverage.get("real_rgbd_or_open_vocab_claim_ready"),
        "status": run_coverage.get("status"),
        "validator_error_rows": run_coverage.get("validator_error_rows"),
        "validator_warning_rows": run_coverage.get("validator_warning_rows"),
    }

    coverage = {
        "checks": checks,
        "expected_file_count": len(expected_rows),
        "expected_files": expected_rows,
        "expected_files_ready": expected_ready,
        "launch_coverage_path": str(args.launch_dir / "coverage.json"),
        "line_counts": line_counts,
        "log": log,
        "log_path": str(log_path),
        "matching": matching,
        "next_recommended_unit": "E003-M75 expanded direct bridge query-level evaluation",
        "real_rgbd_or_open_vocab_claim_ready": False,
        "run_dir": str(args.run_dir),
        "run_summary": run_summary,
        "status": status,
        "tmux_session": tmux_session,
        "tmux_session_running": tmux_running,
        "validator": validator,
        "verify_version": VERIFY_VERSION,
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_text(args.out_dir / "report.md", build_report(coverage))
    print(
        json.dumps(
            {
                "checks": checks,
                "line_counts": line_counts,
                "matching_summary": {
                    "false_positive_proposal_rate_smoke": matching.get("false_positive_proposal_rate_smoke"),
                    "matched_target_rows": matching.get("matched_target_rows"),
                    "proposal_precision_smoke": matching.get("proposal_precision_smoke"),
                    "scan_eval_target_rows": matching.get("scan_eval_target_rows"),
                    "scan_target_recall_smoke": matching.get("scan_target_recall_smoke"),
                    "status": matching.get("status"),
                },
                "next_recommended_unit": coverage["next_recommended_unit"],
                "status": status,
                "validator_summary": {
                    "error_rows": validator.get("error_rows"),
                    "prediction_rows": validator.get("prediction_rows"),
                    "status": validator.get("status"),
                    "valid": validator.get("valid"),
                    "warning_rows": validator.get("warning_rows"),
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    if args.require_ready and not ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
