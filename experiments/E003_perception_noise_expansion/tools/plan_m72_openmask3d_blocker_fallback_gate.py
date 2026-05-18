#!/usr/bin/env python3
"""Decide the E003 route after the OpenMask3D Docker build blocker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M70_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M70_openmask3d_docker_env_build_preflight_v0"
DEFAULT_M60_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M60_direct_current_rescan_query_bridge_v0"
DEFAULT_M63_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M63_bounded_repair_integration_gate_v0"
DEFAULT_M64_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M64_openmask3d_feasibility_decision_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M72_openmask3d_blocker_fallback_gate_v0"
M72_VERSION = "e003_m72_openmask3d_blocker_fallback_gate_v0"


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


def extract_blockers(verification: dict[str, Any]) -> list[dict[str, Any]]:
    log_tail = str(verification.get("log_tail") or "")
    background = verification.get("background_status", {})
    blockers: list[dict[str, Any]] = []
    if verification.get("status") == "openmask3d_docker_build_failed":
        blockers.append(
            {
                "blocker": "docker_build_failed",
                "evidence": f"background status `{background.get('status')}`, returncode `{background.get('returncode')}`",
                "severity": "hard",
            }
        )
    if "MinkowskiEngine" in log_tail and "Getting requirements to build wheel: finished with status 'error'" in log_tail:
        blockers.append(
            {
                "blocker": "minkowskiengine_build_requirement_error",
                "evidence": "OpenMask3D dependency install failed while collecting NVIDIA/MinkowskiEngine before wheel build.",
                "severity": "hard",
            }
        )
    if not verification.get("image_ready"):
        blockers.append(
            {
                "blocker": "image_not_ready",
                "evidence": f"Docker image `{verification.get('image_name')}` is absent after build exit.",
                "severity": "hard",
            }
        )
    return blockers


def build_route_rows(
    verification: dict[str, Any],
    m60: dict[str, Any],
    m63: dict[str, Any],
    m64: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    has_hard_blocker = any(row["severity"] == "hard" for row in blockers)
    direct_rows = int(m60.get("direct_bridge_query_rows", 0) or 0)
    target_detected = int(m60.get("query_target_detected_rows", 0) or 0)
    bounded_failures = int(m64.get("bounded_failure_rows", 0) or 0)
    recall_misses = int(m64.get("gap_class_counts_after_bounded", {}).get("detector_recall_miss_after_bounded_repair", 0) or 0)

    return [
        {
            "route": "repair_openmask3d_env_now",
            "decision": "defer",
            "score": 2 if has_hard_blocker else 5,
            "rationale": "OpenMask3D remains valuable as an external 3D proposal baseline, but current blocker is legacy MinkowskiEngine/CUDA dependency setup rather than a semantic-memory research result.",
            "expected_benefit": "Could test whether 3D instance proposals recover target-undetected rows.",
            "cost_or_risk": "High build/debug cost; likely more CUDA/torch/RTX 5090 compatibility risk after this blocker.",
        },
        {
            "route": "direct_bridge_denominator_expansion",
            "decision": "select",
            "score": 8,
            "rationale": "The current direct bridge has only 7 query rows; expanding exact current-rescan bridge coverage improves claim defensibility without depending on OpenMask3D environment success.",
            "expected_benefit": f"Increase denominator beyond {direct_rows} direct query rows while preserving the existing Dockerized RGB-D/open-vocabulary proposal path.",
            "cost_or_risk": "Still uses the current proposal backend, so it strengthens search-bridge evidence but does not replace the need for later external baselines.",
            "current_signal": {
                "m60_query_target_detected_rows": target_detected,
                "m64_bounded_failure_rows": bounded_failures,
                "m64_detector_recall_miss_rows": recall_misses,
                "m63_selected_next_route": m63.get("selected_next_route"),
            },
        },
        {
            "route": "external_3d_baseline_later",
            "decision": "defer_to_e005",
            "score": 6,
            "rationale": "OpenMask3D, ConceptGraphs, HOV-SG, and Open3DSG are better handled as external baseline expansion after the bridge denominator and evaluation contract are stable.",
            "expected_benefit": "Top-tier reviewer defense for broader mapping-navigation system paper.",
            "cost_or_risk": "Requires additional Docker/runtime integration and fair adapter contracts.",
        },
    ]


def build_report(coverage: dict[str, Any], route_rows: list[dict[str, Any]]) -> str:
    selected = next(row for row in route_rows if row["decision"] == "select")
    blockers = coverage["blockers"]
    return "\n".join(
        [
            "# E003-M72 OpenMask3D Blocker Fallback Gate",
            "",
            "## Status",
            "",
            coverage["status"],
            "",
            "## 사실",
            "",
            f"- E003-M70 verification status: `{coverage['m70_verification_status']}`.",
            f"- tmux session running: {coverage['tmux_session_running']}.",
            f"- image ready: {coverage['image_ready']}.",
            f"- hard blockers: {sum(1 for row in blockers if row['severity'] == 'hard')}.",
            f"- selected next route: `{coverage['selected_next_route']}`.",
            "",
            "## 논문 주장",
            "",
            "- This gate does not support an `OpenMask3D` proposal-quality claim.",
            "- This gate only supports an engineering route decision after Docker environment failure.",
            "",
            "## 에이전트 추론",
            "",
            f"- `{selected['route']}` is preferred because the current direct bridge denominator is still small and can be expanded without spending more time on legacy dependency repair.",
            "- `OpenMask3D` remains useful later as an external baseline, but it should not block E003 search-bridge evidence.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for proceeding to direct bridge denominator expansion.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m70-dir", type=Path, default=DEFAULT_M70_DIR)
    parser.add_argument("--m60-dir", type=Path, default=DEFAULT_M60_DIR)
    parser.add_argument("--m63-dir", type=Path, default=DEFAULT_M63_DIR)
    parser.add_argument("--m64-dir", type=Path, default=DEFAULT_M64_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir = args.out_dir.resolve()
    verification = load_json(args.m70_dir / "verification" / "coverage.json")
    m60 = load_json(args.m60_dir / "coverage.json")
    m63 = load_json(args.m63_dir / "coverage.json")
    m64 = load_json(args.m64_dir / "coverage.json")
    blockers = extract_blockers(verification)
    route_rows = build_route_rows(verification, m60, m63, m64, blockers)
    selected_route = next(row["route"] for row in route_rows if row["decision"] == "select")
    coverage = {
        "blockers": blockers,
        "e003_m72_version": M72_VERSION,
        "image_ready": bool(verification.get("image_ready")),
        "m60_direct_bridge_query_rows": m60.get("direct_bridge_query_rows"),
        "m60_query_target_detected_rows": m60.get("query_target_detected_rows"),
        "m64_bounded_failure_rows": m64.get("bounded_failure_rows"),
        "m64_gap_class_counts_after_bounded": m64.get("gap_class_counts_after_bounded", {}),
        "m70_verification_status": verification.get("status"),
        "next_recommended_unit": "E003-M73 direct bridge denominator expansion plan",
        "openmask3d_proposal_quality_claim_ready": False,
        "paper_table_command_ready": False,
        "real_rgbd_open_vocab_search_claim_ready": False,
        "selected_next_route": selected_route,
        "status": "openmask3d_blocked_direct_denominator_fallback_selected",
        "tmux_session_running": bool(verification.get("tmux_session_running")),
    }
    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "route_options.json", {"routes": route_rows})
    write_text(args.out_dir / "report.md", build_report(coverage, route_rows))
    print(json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
