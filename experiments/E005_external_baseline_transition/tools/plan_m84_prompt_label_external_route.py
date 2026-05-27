#!/usr/bin/env python3
"""Decide the next route after limited confidence-log-depth repair."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
E003_ROOT = ROOT / "experiments" / "E003_perception_noise_expansion"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M84_prompt_label_external_route_decision_v0"
M75_DIR = EXP_ROOT / "artifacts" / "E005-M75_real_proposal_aggregate_route_v0"
M77_DIR = EXP_ROOT / "artifacts" / "E005-M77_offline_detector_prompt_repair_v0"
M83_DIR = EXP_ROOT / "artifacts" / "E005-M83_confidence_log_depth_rerun_decision_v0"
M50_DIR = E003_ROOT / "artifacts" / "E003-M50_same_subset_bbox_vs_mask_v0"
M72_DIR = E003_ROOT / "artifacts" / "E003-M72_openmask3d_blocker_fallback_gate_v0"
VERSION = "e005_m84_prompt_label_external_route_decision_v0"


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


def summarize_miss_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    miss_rows = [row for row in rows if row.get("repair_class") == "prompt_or_detector_recall_miss"]
    label_counts = Counter(str(row.get("label_canonical")) for row in miss_rows)
    batch_counts = Counter(str(row.get("batch_id")) for row in miss_rows)
    scan_counts = Counter(str(row.get("scan_id")) for row in miss_rows)
    ambiguous_labels = {"object", "furniture", "item", "thing"}
    broad_or_ambiguous = sum(count for label, count in label_counts.items() if label in ambiguous_labels)
    chair_like = sum(count for label, count in label_counts.items() if label in {"chair", "stool"})
    return {
        "batch_counts": dict(sorted(batch_counts.items())),
        "broad_or_ambiguous_label_miss_targets": broad_or_ambiguous,
        "chair_or_stool_miss_targets": chair_like,
        "label_counts": dict(label_counts.most_common()),
        "miss_target_rows": len(miss_rows),
        "miss_unique_scans": len(scan_counts),
        "rows": miss_rows,
    }


def build_route_options(
    m75: dict[str, Any],
    m77: dict[str, Any],
    m83: dict[str, Any],
    m50: dict[str, Any],
    m72: dict[str, Any],
    miss_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    target_rows = int(m77.get("target_rows", 0))
    query_rows = int(m75.get("query_rows", 0))
    queries_per_target = round(query_rows / target_rows, 6) if target_rows else None
    miss_targets = int(miss_summary["miss_target_rows"])
    max_query_detection_gain = int(round(miss_targets * (query_rows / target_rows))) if target_rows else 0
    b01_b03_remaining_gain = int(m83.get("expected_all_batch_top5_delta_vs_m75", 0)) - int(
        m83.get("b02_actual_top5_delta_vs_original", 0)
    )
    openmask_blockers = m72.get("blockers", [])
    grounded_sam_weak_positive = bool(m50.get("comparison", {}).get("weak_positive"))

    options = [
        {
            "blocked_by": [],
            "decision": "reject_now",
            "evidence": "M83 shows b01 expected top5 gain 0 and b03 expected top5 gain 3 rows.",
            "expected_claim_value": "low",
            "option_id": "continue_b01_b03_confidence_log_depth_reruns",
            "risk": "spends detector compute for a complete diagnostic row without addressing target detection",
            "score": 15,
        },
        {
            "blocked_by": [],
            "decision": "select_next",
            "evidence": (
                f"M77 has {miss_targets} prompt/detector recall-miss target rows; "
                f"maximum query detection exposure is about {max_query_detection_gain} rows "
                f"under {queries_per_target} queries per target."
            ),
            "expected_claim_value": "medium",
            "option_id": "prompt_label_recall_audit_and_repair_plan",
            "risk": "chair/stool misses suggest not all failures are synonym-only; audit must separate prompt alias, visibility, and detector miss",
            "score": 82,
        },
        {
            "blocked_by": ["grounded_sam_same_subset_negative"] if not grounded_sam_weak_positive else [],
            "decision": "reject_now",
            "evidence": "M50 mask-depth is not weak-positive against bbox-depth on the same subset.",
            "expected_claim_value": "low",
            "option_id": "scale_grounded_sam_mask_depth",
            "risk": "scaling a negative same-subset route would weaken reviewer defense",
            "score": 20,
        },
        {
            "blocked_by": [str(row.get("blocker")) for row in openmask_blockers],
            "decision": "later_after_blocker_or_if_external_pressure_required",
            "evidence": "OpenMask3D is a relevant 3D proposal baseline, but M72 records hard Docker/MinkowskiEngine/image blockers.",
            "expected_claim_value": "high_if_unblocked",
            "option_id": "openmask3d_external_proposal_baseline",
            "risk": "high engineering burden and blocked local environment",
            "score": 54 if openmask_blockers else 76,
        },
        {
            "blocked_by": ["not_a_direct_real_proposal_recall_repair"],
            "decision": "keep_as_mapping_baseline_not_next_recall_repair",
            "evidence": "ConceptGraphs/Open3DSG already provide external map/scene-graph pressure on the 195-row proxy denominator.",
            "expected_claim_value": "medium",
            "option_id": "additional_map_baseline_hovsg_or_conceptgraphs_variant",
            "risk": "does not directly fix detector target-detection misses in the real proposal bridge",
            "score": 45,
        },
    ]
    return options


def build_report(coverage: dict[str, Any], options: list[dict[str, Any]], miss_rows: list[dict[str, Any]]) -> str:
    option_lines = [
        "| Option | Decision | Score | Claim value | Main blocker/risk |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for option in options:
        blockers = ", ".join(option["blocked_by"]) if option["blocked_by"] else option["risk"]
        option_lines.append(
            f"| `{option['option_id']}` | `{option['decision']}` | {option['score']} | "
            f"{option['expected_claim_value']} | {blockers} |"
        )
    miss_lines = [
        "| Batch | Label | Scan | Target UID | Boundary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in miss_rows:
        miss_lines.append(
            "| `{batch}` | `{label}` | `{scan}` | `{target}` | `{boundary}` |".format(
                batch=row.get("batch_id"),
                label=row.get("label_canonical"),
                scan=row.get("scan_id"),
                target=row.get("target_uid"),
                boundary=row.get("repair_class"),
            )
        )
    return "\n".join(
        [
            "# E005-M84 Prompt/Label vs External Proposal Route Decision",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Selected route: `{coverage['selected_next_route']}`.",
            f"- Prompt/detector recall-miss targets: {coverage['prompt_or_detector_recall_miss_targets']} / {coverage['target_rows']}.",
            f"- Max query-detection exposure if those targets are recovered: {coverage['max_query_detection_gain_from_recall_repair']} / {coverage['query_rows']}.",
            f"- Remaining confidence-log-depth rerun expected top5 gain after b02: {coverage['remaining_confidence_log_depth_expected_gain_rows']} rows.",
            f"- OpenMask3D hard blockers: {coverage['openmask3d_hard_blocker_count']}.",
            f"- Grounded-SAM same-subset weak positive: {str(coverage['grounded_sam_same_subset_weak_positive']).lower()}.",
            "",
            "## Route Options",
            "",
            *option_lines,
            "",
            "## Prompt/Detector Recall-Miss Rows",
            "",
            *miss_lines,
            "",
            "## Claim Boundary",
            "",
            "- E005-M84 is a route decision, not a new detector result.",
            "- It does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL`.",
            "- The next step should stay lightweight: audit prompt aliases, broad labels, visibility, and detector miss classes before launching another long run.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m75 = read_json(M75_DIR / "coverage.json")
    m77 = read_json(M77_DIR / "coverage.json")
    m83 = read_json(M83_DIR / "coverage.json")
    m50 = read_json(M50_DIR / "coverage.json")
    m72 = read_json(M72_DIR / "coverage.json")
    target_rows = read_jsonl(M77_DIR / "target_repair_boundary_rows.jsonl")
    miss_summary = summarize_miss_rows(target_rows)
    route_options = build_route_options(m75, m77, m83, m50, m72, miss_summary)

    target_count = int(m77.get("target_rows", 0))
    query_rows = int(m75.get("query_rows", 0))
    miss_targets = int(miss_summary["miss_target_rows"])
    query_per_target = query_rows / target_count if target_count else 0
    max_query_detection_gain = int(round(miss_targets * query_per_target)) if target_count else 0
    remaining_gain = int(m83.get("expected_all_batch_top5_delta_vs_m75", 0)) - int(
        m83.get("b02_actual_top5_delta_vs_original", 0)
    )
    openmask_blockers = m72.get("blockers", [])
    hard_openmask_blockers = [row for row in openmask_blockers if row.get("severity") == "hard"]
    selected_route = "prompt_label_recall_audit_first_then_external_proposal_baseline_gate"
    coverage = {
        "deployable_search_policy_claim_ready": False,
        "final_real_rgbd_open_vocab_robustness_claim_ready": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "grounded_sam_same_subset_weak_positive": bool(m50.get("comparison", {}).get("weak_positive")),
        "h001_success_rows": int(m75.get("h001_success_rows", 0)),
        "max_query_detection_gain_from_recall_repair": max_query_detection_gain,
        "next_recommended_unit": "E005-M85 prompt/label recall miss audit and repair contract",
        "openmask3d_hard_blocker_count": len(hard_openmask_blockers),
        "prompt_or_detector_recall_miss_batch_counts": miss_summary["batch_counts"],
        "prompt_or_detector_recall_miss_label_counts": miss_summary["label_counts"],
        "prompt_or_detector_recall_miss_targets": miss_targets,
        "query_rows": query_rows,
        "queries_per_target": round(query_per_target, 6) if target_count else None,
        "real_navigation_sr_spl_claim_ready": False,
        "remaining_confidence_log_depth_expected_gain_rows": remaining_gain,
        "selected_next_route": selected_route,
        "status": "e005_m84_prompt_label_external_route_decision_ready",
        "target_rows": target_count,
        "version": VERSION,
    }

    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "route_options.jsonl", route_options)
    write_jsonl(OUT_DIR / "prompt_detector_recall_miss_rows.jsonl", miss_summary["rows"])
    write_text(OUT_DIR / "report.md", build_report(coverage, route_options, miss_summary["rows"]))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
