#!/usr/bin/env python3
"""Audit E003 perception source readiness and fix the first noise plan."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_E001_M01_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M01_pair_manifest_v0"
)
DEFAULT_E001_M02_DIR = (
    REPO_ROOT
    / "experiments"
    / "E001_semantic_pair_dynamic_search_proxy"
    / "artifacts"
    / "E001-M02_query_construction_v0"
)
DEFAULT_E002_M09_DIR = (
    REPO_ROOT
    / "experiments"
    / "E002_path_cost_bridge"
    / "artifacts"
    / "E002-M09_reachable_first_scoring_v0"
)
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M01_source_audit_v0"
AUDIT_VERSION = "e003_source_audit_v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return dict(grouped)


def target_counts(candidate_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in candidate_rows:
        if row.get("candidate_is_target"):
            counts[row["row_uid"]] += 1
    return dict(counts)


def candidate_counts(candidate_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in candidate_rows:
        counts[row["row_uid"]] += 1
    return dict(counts)


def discover_sequence_scans(dataset_root: Path) -> dict[str, dict[str, Any]]:
    scans_dir = dataset_root / "3RScan" / "scans"
    output: dict[str, dict[str, Any]] = {}
    if not scans_dir.exists():
        return output
    for scan_dir in sorted(path for path in scans_dir.iterdir() if path.is_dir()):
        sequence_zip = scan_dir / "sequence.zip"
        sequence_dir = scan_dir / "sequence"
        has_sequence_zip = sequence_zip.exists()
        has_sequence_dir = sequence_dir.exists()
        output[scan_dir.name] = {
            "scan_id": scan_dir.name,
            "sequence_zip": has_sequence_zip,
            "sequence_dir": has_sequence_dir,
            "sequence_available": has_sequence_zip or has_sequence_dir,
        }
    return output


def discover_open_vocab_hints(dataset_root: Path, experiment_root: Path) -> list[str]:
    hints = []
    tokens = ["open", "vocab", "clip", "proposal", "detect", "ground", "concept", "ov"]
    for root in [dataset_root, experiment_root]:
        if not root.exists():
            continue
        for path in sorted(root.iterdir()):
            lowered = path.name.lower()
            if any(token in lowered for token in tokens):
                hints.append(str(path))
    return hints


def build_pair_rows(
    manifest_rows: list[dict[str, Any]],
    query_rows: list[dict[str, Any]],
    sequence_scans: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    ready_rows = [row for row in manifest_rows if row["eligibility_status"] == "ready_minimal"]
    query_by_pair = group_by(query_rows, "pair_uid")
    rows = []
    for row in ready_rows:
        ref_seq = sequence_scans.get(row["reference_scan_id"], {})
        rescan_seq = sequence_scans.get(row["rescan_id"], {})
        pair_queries = query_by_pair.get(row["pair_uid"], [])
        rows.append(
            {
                "audit_version": AUDIT_VERSION,
                "pair_uid": row["pair_uid"],
                "metadata_split": row["metadata_split"],
                "reference_scan_id": row["reference_scan_id"],
                "rescan_id": row["rescan_id"],
                "query_rows": len(pair_queries),
                "reference_sequence_available": bool(ref_seq.get("sequence_available")),
                "rescan_sequence_available": bool(rescan_seq.get("sequence_available")),
                "pair_sequence_ready": bool(ref_seq.get("sequence_available"))
                and bool(rescan_seq.get("sequence_available")),
                "manifest_reference_sequence": bool(row["reference_payload"].get("sequence")),
                "manifest_rescan_sequence": bool(row["rescan_payload"].get("sequence")),
                "annotation_proxy_ready": len(pair_queries) > 0,
                "real_rgbd_ready": False,
                "open_vocab_ready": False,
                "next_source": "annotation_proxy_noise",
            }
        )
    return rows


def build_source_rows(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_uid = candidate_counts(candidate_rows)
    targets_by_uid = target_counts(candidate_rows)
    rows = []
    for row in query_rows:
        candidate_count = candidates_by_uid.get(row["row_uid"], 0)
        target_count = targets_by_uid.get(row["row_uid"], 0)
        annotation_ready = candidate_count > 0 and target_count == 1
        rows.append(
            {
                "audit_version": AUDIT_VERSION,
                "row_uid": row["row_uid"],
                "base_row_uid": row["base_row_uid"],
                "pair_uid": row["pair_uid"],
                "metadata_split": row["metadata_split"],
                "reference_scan_id": row["reference_scan_id"],
                "rescan_id": row["rescan_id"],
                "task_context_id": row["task_context_id"],
                "row_band": row["row_band"],
                "object_label": row["object_label"],
                "candidate_rows": candidate_count,
                "target_candidate_rows": target_count,
                "annotation_proxy_noise_ready": annotation_ready,
                "rgbd_sequence_available": bool(row.get("rgbd_sequence_available")),
                "e003_rgbd_ready": bool(row.get("e003_rgbd_ready")),
                "e003_open_vocab_ready": bool(row.get("e003_open_vocab_ready")),
                "open_vocab_proposal_source": row.get("open_vocab_proposal_source"),
                "perception_profile_id": row.get("perception_profile_id"),
                "proposal_noise_profile_id": row.get("proposal_noise_profile_id"),
                "first_executable_profile": "annotation_score_jitter_v0"
                if annotation_ready
                else "blocked_missing_annotation_target",
                "real_perception_status": "blocked_no_rgbd_or_open_vocab_source",
            }
        )
    return rows


def build_noise_plan(
    source_rows: list[dict[str, Any]],
    out_dir: Path,
) -> dict[str, Any]:
    ready_rows = [row for row in source_rows if row["annotation_proxy_noise_ready"]]
    return {
        "audit_version": AUDIT_VERSION,
        "plan_version": "e003_noise_plan_v0",
        "first_executable_unit": "E003-M02_annotation_proxy_noise_generator_v0",
        "first_command": "python experiments/E003_perception_noise_expansion/tools/build_noise_inputs.py",
        "input_query_artifact": str(DEFAULT_E001_M02_DIR / "query_rows.jsonl"),
        "input_candidate_artifact": str(DEFAULT_E001_M02_DIR / "candidate_rows.jsonl"),
        "output_directory": str(
            EXPERIMENT_ROOT / "artifacts" / "E003-M02_annotation_proxy_noise_v0"
        ),
        "primary_profiles": [
            {
                "proposal_noise_profile_id": "clean_annotation_oracle_v0",
                "role": "clean_reference",
                "target_policy": "preserve_target",
                "seed_required": False,
            },
            {
                "proposal_noise_profile_id": "annotation_score_jitter_v0",
                "role": "first_stress_profile",
                "target_policy": "preserve_target",
                "seed_required": True,
                "seed": 7,
                "score_jitter_sigma": 0.10,
                "rank_recompute": True,
            },
        ],
        "deferred_profiles": [
            "annotation_proposal_dropout_v0",
            "annotation_false_positive_v0",
            "annotation_centroid_jitter_v0",
            "annotation_combined_moderate_v0",
        ],
        "m02_outputs": [
            "noise_manifest.jsonl",
            "noisy_query_rows.jsonl",
            "noisy_candidate_rows.jsonl",
            "coverage.json",
            "report.md",
        ],
        "required_row_fields": [
            "row_uid",
            "base_row_uid",
            "pair_uid",
            "task_context_id",
            "row_band",
            "object_label",
            "success_threshold_m",
            "task_context_id",
        ],
        "required_candidate_fields": [
            "row_uid",
            "candidate_instance_id",
            "candidate_is_target",
            "candidate_rank_non_persistent",
            "candidate_score_non_persistent",
            "candidate_centroid",
        ],
        "denominator_policy": {
            "primary": "all annotation_proxy_noise_ready rows",
            "target_dropped_rows": "not applicable for first profile because target is preserved",
            "future_dropout_policy": "target-retained and target-dropped denominators must be reported separately",
        },
        "ready_rows": len(ready_rows),
        "audit_output_directory": str(out_dir),
    }


def build_summary(
    source_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    sequence_scans: dict[str, dict[str, Any]],
    open_vocab_hints: list[str],
    e001_m01_coverage: dict[str, Any],
    e001_m02_coverage: dict[str, Any],
    e002_m09_coverage: dict[str, Any] | None,
) -> dict[str, Any]:
    annotation_ready = [row for row in source_rows if row["annotation_proxy_noise_ready"]]
    sequence_ready_pairs = [row for row in pair_rows if row["pair_sequence_ready"]]
    return {
        "audit_version": AUDIT_VERSION,
        "status": "source_audit_ready"
        if len(annotation_ready) == len(source_rows) and len(source_rows) > 0
        else "review_needed",
        "query_rows": len(source_rows),
        "candidate_rows": e001_m02_coverage["candidate_rows"],
        "ready_manifest_pairs": e001_m02_coverage["ready_manifest_pairs"],
        "annotation_proxy_noise_ready_rows": len(annotation_ready),
        "annotation_proxy_noise_ready_rate": round(len(annotation_ready) / len(source_rows), 6)
        if source_rows
        else None,
        "rgbd_sequence_available_query_rows": sum(
            1 for row in source_rows if row["rgbd_sequence_available"]
        ),
        "e003_rgbd_ready_rows": sum(1 for row in source_rows if row["e003_rgbd_ready"]),
        "e003_open_vocab_ready_rows": sum(1 for row in source_rows if row["e003_open_vocab_ready"]),
        "local_sequence_scan_count": sum(
            1 for row in sequence_scans.values() if row["sequence_available"]
        ),
        "ready_pair_sequence_ready_count": len(sequence_ready_pairs),
        "open_vocab_hint_count": len(open_vocab_hints),
        "open_vocab_hints": open_vocab_hints[:20],
        "row_band_counts": counter_dict(Counter(row["row_band"] for row in source_rows)),
        "task_context_counts": counter_dict(Counter(row["task_context_id"] for row in source_rows)),
        "candidate_count_distribution": counter_dict(Counter(row["candidate_rows"] for row in source_rows)),
        "target_candidate_count_distribution": counter_dict(
            Counter(row["target_candidate_rows"] for row in source_rows)
        ),
        "e001_m01_local_sequence_available": e001_m01_coverage["local_scan_payloads"][
            "sequence_available"
        ],
        "e002_m09_target_reachable_eval_rows": e002_m09_coverage.get("target_reachable_eval_rows")
        if e002_m09_coverage
        else None,
        "real_perception_blockers": [
            "no E001 query rows with rgbd_sequence_available",
            "no E001 query rows with e003_open_vocab_ready",
            "no configured detector/proposal output schema",
        ],
        "first_executable_profile": "annotation_score_jitter_v0",
        "first_reference_profile": "clean_annotation_oracle_v0",
        "next_unit": "E003-M02_annotation_proxy_noise_generator_v0",
    }


def build_report(summary: dict[str, Any], noise_plan: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# E003-M01 Source Audit",
        "",
        "## Status",
        "",
        summary["status"],
        "",
        "## 사실",
        "",
        f"- Query rows: {summary['query_rows']}",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Annotation-proxy noise ready rows: {summary['annotation_proxy_noise_ready_rows']}",
        f"- RGB-D sequence available query rows: {summary['rgbd_sequence_available_query_rows']}",
        f"- E003 RGB-D ready rows: {summary['e003_rgbd_ready_rows']}",
        f"- E003 open-vocabulary ready rows: {summary['e003_open_vocab_ready_rows']}",
        f"- Local sequence scan count: {summary['local_sequence_scan_count']}",
        f"- Ready pair sequence-ready count: {summary['ready_pair_sequence_ready_count']}",
        f"- Open-vocabulary hint count: {summary['open_vocab_hint_count']}",
        f"- E002-M09 target-reachable eval rows: {summary['e002_m09_target_reachable_eval_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## First Executable Plan",
        "",
        f"- First unit: `{noise_plan['first_executable_unit']}`",
        f"- Command: `{noise_plan['first_command']}`",
        f"- Reference profile: `{summary['first_reference_profile']}`",
        f"- First stress profile: `{summary['first_executable_profile']}`",
        f"- Ready rows: {noise_plan['ready_rows']}",
        "",
        "## 논문 주장",
        "",
        "- E003-M01 supports starting with controlled annotation-proxy proposal noise.",
        "- E003-M01 does not support real RGB-D or open-vocabulary perception robustness.",
        "- Real perception claims remain blocked until aligned detector/proposal outputs are generated.",
        "",
        "## 에이전트 추론",
        "",
        "- The first executable profile should preserve target presence and perturb ranking first, because this isolates memory-update robustness from detector recall failure.",
        "- Proposal dropout, false positives, centroid jitter, and combined noise should follow after the clean and score-jitter path is executable.",
        "- Local sequence payloads exist in the dataset, but they are not connected to the current E001 query denominator.",
        "",
        "## 사용자 판단 필요",
        "",
        "- None for E003-M01. Continue to E003-M02 annotation-proxy noise generator.",
        "",
        "## Outputs",
        "",
        "- `source_audit_rows.jsonl`",
        "- `pair_readiness_rows.jsonl`",
        "- `noise_plan.json`",
        "- `coverage.json`",
        "- `report.md`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e001-m01-dir", type=Path, default=DEFAULT_E001_M01_DIR)
    parser.add_argument("--e001-m02-dir", type=Path, default=DEFAULT_E001_M02_DIR)
    parser.add_argument("--e002-m09-dir", type=Path, default=DEFAULT_E002_M09_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    e001_m01_coverage = load_json(args.e001_m01_dir / "coverage.json")
    e001_m02_coverage = load_json(args.e001_m02_dir / "coverage.json")
    e002_m09_coverage = (
        load_json(args.e002_m09_dir / "coverage.json")
        if (args.e002_m09_dir / "coverage.json").exists()
        else None
    )
    manifest_rows = load_jsonl(args.e001_m01_dir / "manifest.jsonl")
    query_rows = load_jsonl(args.e001_m02_dir / "query_rows.jsonl")
    candidate_rows = load_jsonl(args.e001_m02_dir / "candidate_rows.jsonl")
    dataset_root = Path(e001_m02_coverage["dataset_root"])

    sequence_scans = discover_sequence_scans(dataset_root)
    open_vocab_hints = discover_open_vocab_hints(dataset_root, EXPERIMENT_ROOT)
    pair_rows = build_pair_rows(manifest_rows, query_rows, sequence_scans)
    source_rows = build_source_rows(query_rows, candidate_rows)
    noise_plan = build_noise_plan(source_rows, args.out_dir)
    summary = build_summary(
        source_rows,
        pair_rows,
        sequence_scans,
        open_vocab_hints,
        e001_m01_coverage,
        e001_m02_coverage,
        e002_m09_coverage,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "source_audit_rows.jsonl", source_rows)
    write_jsonl(args.out_dir / "pair_readiness_rows.jsonl", pair_rows)
    write_json(args.out_dir / "noise_plan.json", noise_plan)
    write_json(args.out_dir / "coverage.json", summary)
    (args.out_dir / "report.md").write_text(
        build_report(summary, noise_plan, args.out_dir),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": summary["status"],
                "query_rows": summary["query_rows"],
                "annotation_proxy_noise_ready_rows": summary[
                    "annotation_proxy_noise_ready_rows"
                ],
                "rgbd_sequence_available_query_rows": summary[
                    "rgbd_sequence_available_query_rows"
                ],
                "e003_open_vocab_ready_rows": summary["e003_open_vocab_ready_rows"],
                "first_executable_profile": summary["first_executable_profile"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
