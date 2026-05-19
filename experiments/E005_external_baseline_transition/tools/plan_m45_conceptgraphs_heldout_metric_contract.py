#!/usr/bin/env python3
"""Plan the heldout ConceptGraphs metric conversion contract.

This is intentionally non-runtime work. It does not read ConceptGraphs heldout
object maps and does not compute metrics. It freezes the schema, split, policy,
and table contract that M45 should use after M44 verifies runtime outputs.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M45_conceptgraphs_heldout_metric_contract_v0"

VERSION = "e005_m45_conceptgraphs_heldout_metric_contract_v0"
M35_DIR = EXP_ROOT / "artifacts" / "E005-M35_conceptgraphs_4scan_query_metric_v0"
M38_DIR = EXP_ROOT / "artifacts" / "E005-M38_conceptgraphs_heldout_scale_v0"
M43_DIR = EXP_ROOT / "artifacts" / "E005-M43_conceptgraphs_heldout_runtime_batch_launch_v0"
M41_DIR = EXP_ROOT / "artifacts" / "E005-M41_conceptgraphs_heldout_runtime_preflight_v0"

SAVE_SUFFIX = "overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub"

POLICIES = [
    {
        "policy": "conceptgraphs_clip_rank_centroid_strict_top5_v0",
        "distance_field": "eval_center_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
        "table_role": "diagnostic_centroid_strict",
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": 5,
        "table_role": "primary_strict_bbox",
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top3_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 3,
        "table_role": "diagnostic_relaxed_bbox_top3",
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_relaxed_1m_top5_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 1.0,
        "budget": 5,
        "table_role": "diagnostic_relaxed_bbox_top5",
    },
    {
        "policy": "conceptgraphs_clip_rank_bbox_strict_unbounded_v0",
        "distance_field": "eval_bbox_distance_m",
        "threshold_m": 0.5,
        "budget": "all",
        "table_role": "upper_bound_strict_bbox",
    },
]


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


def field_list(row: dict[str, Any]) -> list[str]:
    return sorted(row.keys()) if row else []


def expected_post_path(scan_id: str) -> str:
    return str(
        ROOT
        / "local_dataset"
        / "ConceptGraphs_staged"
        / "3rscan_depth_aligned_scannet"
        / scan_id
        / "pcd_saves"
        / f"full_pcd_none_{SAVE_SUFFIX}_post.pkl.gz"
    )


def expected_full_path(scan_id: str) -> str:
    return str(
        ROOT
        / "local_dataset"
        / "ConceptGraphs_staged"
        / "3rscan_depth_aligned_scannet"
        / scan_id
        / "pcd_saves"
        / f"full_pcd_none_{SAVE_SUFFIX}.pkl.gz"
    )


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(str(row["label_canonical"]) for row in rows)
    bands = Counter(str(row["row_band"]) for row in rows)
    contexts = Counter(str(row["task_context_id"]) for row in rows)
    scans = sorted({str(row["current_rescan_id"]) for row in rows})
    targets = sorted({str(row["target_uid"]) for row in rows})
    return {
        "query_rows": len(rows),
        "scan_count": len(scans),
        "target_uid_count": len(targets),
        "label_count": len(labels),
        "label_counts": dict(sorted(labels.items())),
        "row_band_counts": dict(sorted(bands.items())),
        "task_context_counts": dict(sorted(contexts.items())),
        "scan_ids": scans,
    }


def build_expected_output_rows(scan_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "scan_id": scan_id,
            "expected_gsa_dir": str(
                ROOT
                / "local_dataset"
                / "ConceptGraphs_staged"
                / "3rscan_depth_aligned_scannet"
                / scan_id
                / "gsa_detections_none"
            ),
            "expected_full_pcd": expected_full_path(scan_id),
            "expected_full_pcd_post": expected_post_path(scan_id),
            "required_for_m45": True,
        }
        for scan_id in scan_ids
    ]


def build_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, list[dict[str, Any]]], str]:
    m35_coverage = read_json(M35_DIR / "coverage.json")
    m35_metrics = read_json(M35_DIR / "metrics.json")
    m38_coverage = read_json(M38_DIR / "coverage.json")
    m43_coverage = read_json(M43_DIR / "coverage.json")
    m43_verify = read_json(M43_DIR / "verification" / "heldout_b01" / "coverage.json")
    runtime_batch_rows = read_jsonl(M41_DIR / "runtime_batch_rows.jsonl")
    scale_rows = read_jsonl(M38_DIR / "scale_query_rows.jsonl")
    object_sample = read_jsonl(M35_DIR / "object_rows.jsonl")[:1]
    candidate_sample = read_jsonl(M35_DIR / "candidate_rows.jsonl")[:1]
    candidate_eval_sample = read_jsonl(M35_DIR / "candidate_eval_rows.jsonl")[:1]
    policy_sample = read_jsonl(M35_DIR / "policy_rows.jsonl")[:1]

    batch_query_rows: dict[str, list[dict[str, Any]]] = {}
    batch_summaries: list[dict[str, Any]] = []
    for batch in runtime_batch_rows:
        batch_id = str(batch["batch_id"])
        batch_scan_ids = [str(scan_id) for scan_id in batch.get("scan_ids", [])]
        rows = [row for row in scale_rows if str(row.get("current_rescan_id")) in set(batch_scan_ids)]
        batch_query_rows[batch_id] = rows
        batch_summaries.append(
            {
                "batch_id": batch_id,
                "scan_ids": batch_scan_ids,
                "query_rows_path": str(OUT_DIR / f"{batch_id}_query_rows.jsonl"),
                "summary": summarize_rows(rows),
                "expected_outputs": build_expected_output_rows(batch_scan_ids),
            }
        )

    selected_batch_id = "heldout_b01"
    selected_batch = next((row for row in batch_summaries if row["batch_id"] == selected_batch_id), None)
    scan_ids = [str(scan_id) for scan_id in (selected_batch or {}).get("scan_ids", [])]
    selected_rows = batch_query_rows.get(selected_batch_id, [])
    heldout_all_rows = [row for row in scale_rows if row.get("split") == "heldout_sequence_required"]
    dev_rows = [row for row in scale_rows if row.get("split") == "dev_existing_4scan_metric_ready"]

    expected_rows = build_expected_output_rows(scan_ids)

    table_schema = {
        "object_rows": {
            "source": str(M35_DIR / "object_rows.jsonl"),
            "required_fields": field_list(object_sample[0] if object_sample else {}),
            "heldout_output": "object_rows_heldout_b01.jsonl",
        },
        "candidate_rows": {
            "source": str(M35_DIR / "candidate_rows.jsonl"),
            "required_fields": field_list(candidate_sample[0] if candidate_sample else {}),
            "heldout_output": "candidate_rows_heldout_b01.jsonl",
        },
        "candidate_eval_rows": {
            "source": str(M35_DIR / "candidate_eval_rows.jsonl"),
            "required_fields": field_list(candidate_eval_sample[0] if candidate_eval_sample else {}),
            "heldout_output": "candidate_eval_rows_heldout_b01.jsonl",
        },
        "policy_rows": {
            "source": str(M35_DIR / "policy_rows.jsonl"),
            "required_fields": field_list(policy_sample[0] if policy_sample else {}),
            "heldout_output": "policy_rows_heldout_b01.jsonl",
        },
        "metrics": {
            "source": str(M35_DIR / "metrics.json"),
            "required_top_level": ["suites"],
            "heldout_output": "metrics_heldout_b01.json",
        },
    }

    contract = {
        "version": VERSION,
        "status": "e005_m45_conceptgraphs_heldout_metric_contract_ready_waiting_m44",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_dependency": {
            "required_previous_unit": "E005-M44 ConceptGraphs heldout runtime batch completion verification",
            "m43_launch_status": m43_coverage.get("status"),
            "m43_verify_status": m43_verify.get("status"),
            "m43_tmux_running": m43_verify.get("tmux_running"),
            "ready_scan_count_now": m43_verify.get("ready_scan_count"),
            "expected_scan_count": m43_verify.get("expected_scan_count"),
        },
        "input_artifacts": {
            "m35_4scan_schema": str(M35_DIR),
            "m38_scale_queries": str(M38_DIR / "scale_query_rows.jsonl"),
            "m41_runtime_batches": str(M41_DIR / "runtime_batch_rows.jsonl"),
            "m43_expected_runtime_outputs_pattern": str(M43_DIR / "expected_outputs_<batch_id>.jsonl"),
        },
        "selected_batch": {
            "batch_id": "heldout_b01",
            "scan_ids": scan_ids,
            "query_rows_path": str(OUT_DIR / "heldout_b01_query_rows.jsonl"),
            "summary": summarize_rows(selected_rows),
            "expected_outputs": expected_rows,
        },
        "all_batches": batch_summaries,
        "scale_context": {
            "m38_status": m38_coverage.get("status"),
            "target_scale": m38_coverage.get("target_scale"),
            "dev_existing_4scan": summarize_rows(dev_rows),
            "heldout_all": summarize_rows(heldout_all_rows),
            "current_batch_fraction_of_heldout_queries": round(len(selected_rows) / len(heldout_all_rows), 6)
            if heldout_all_rows
            else None,
        },
        "schema": table_schema,
        "policies": POLICIES,
        "primary_table_rows": [
            {
                "table": "external_baseline_scale",
                "row_id": "ConceptGraphs_dev_existing_4scan",
                "source": "E005-M35",
                "query_suite": "expanded_m73",
                "split": "dev_existing_4scan_metric_ready",
                "required_metrics": [
                    "query_bridge_success_rate",
                    "target_detected_rate",
                    "mean_expected_search_cost",
                    "mean_attempt_spl_proxy",
                ],
            },
            {
                "table": "external_baseline_scale",
                "row_id": "ConceptGraphs_heldout_b01",
                "source": "E005-M45",
                "query_suite": "heldout_m38_b01",
                "split": "heldout_sequence_required",
                "required_metrics": [
                    "query_bridge_success_rate",
                    "target_detected_rate",
                    "mean_expected_search_cost",
                    "mean_attempt_spl_proxy",
                ],
            },
        ],
        "claim_boundary": {
            "allowed_after_m45_b01": [
                "heldout_b01 query-level external mapping baseline diagnostic",
                "strict vs relaxed geometry boundary on one heldout runtime batch",
            ],
            "not_allowed_after_m45_b01": [
                "final ConceptGraphs heldout baseline",
                "all 9 heldout scan transfer claim",
                "final real RGB-D/open-vocabulary robustness claim",
                "real navigation SR/SPL claim",
            ],
        },
        "future_command_contract": {
            "planned_converter": "experiments/E005_external_baseline_transition/tools/run_m45_conceptgraphs_heldout_query_metrics.py --batch-id <heldout_bXX>",
            "docker_required": True,
            "reason": "CLIP text scoring uses the ConceptGraphs Docker image and the same M35 object-map schema.",
        },
        "reference_m35_metrics": {
            "status": m35_coverage.get("status"),
            "scan_count": m35_coverage.get("scan_count"),
            "expanded_m73": m35_metrics.get("suites", {}).get("expanded_m73", {}),
            "primary_m60": m35_metrics.get("suites", {}).get("primary_m60", {}),
        },
        "next_recommended_unit": "E005-M44 completion verification, then implement/run E005-M45 heldout metric conversion",
        "paper_table_claim_ready": False,
    }

    coverage = {
        "version": VERSION,
        "status": contract["status"],
        "generated_at": contract["generated_at"],
        "batch_id": "heldout_b01",
        "selected_scan_count": len(scan_ids),
        "selected_query_rows": len(selected_rows),
        "selected_target_uid_count": contract["selected_batch"]["summary"]["target_uid_count"],
        "selected_label_count": contract["selected_batch"]["summary"]["label_count"],
        "heldout_all_query_rows": len(heldout_all_rows),
        "dev_existing_query_rows": len(dev_rows),
        "m43_launch_status": m43_coverage.get("status"),
        "m43_verify_status": m43_verify.get("status"),
        "m43_tmux_running": m43_verify.get("tmux_running"),
        "m44_required_before_m45": True,
        "future_converter_ready": False,
        "paper_table_claim_ready": False,
        "next_recommended_unit": "E005-M44 completion verification",
    }

    report = "\n".join(
        [
            "# E005-M45 ConceptGraphs Heldout Metric Contract",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## Facts",
            "",
            f"- Batch id: `heldout_b01`.",
            f"- Selected scans: {coverage['selected_scan_count']}.",
            f"- Selected query rows: {coverage['selected_query_rows']}.",
            f"- Selected target uids: {coverage['selected_target_uid_count']}.",
            f"- Selected labels: {coverage['selected_label_count']}.",
            f"- Heldout-all query rows: {coverage['heldout_all_query_rows']}.",
            f"- M43 launch status: `{coverage['m43_launch_status']}`.",
            f"- Current verifier status: `{coverage['m43_verify_status']}`.",
            f"- M43 tmux running: {coverage['m43_tmux_running']}.",
            "",
            "## Metric Contract",
            "",
            "- Reuse M35 object / candidate / candidate-eval / policy row schemas.",
            "- Keep strict 0.5m bbox, relaxed 1.0m bbox, and centroid strict metrics separate.",
            "- Primary paper-facing metric is `conceptgraphs_clip_rank_bbox_strict_top5_v0`.",
            "- Relaxed metrics are diagnostics, not replacements for strict success.",
            "- `heldout_b01` is a batch diagnostic and must not be reported as the final 9-scan heldout result.",
            "",
            "## Claim Boundary",
            "",
            "- This contract does not compute heldout metrics.",
            "- M45 is blocked until M44 verifies runtime outputs for the selected scans.",
            "- No final external baseline, real RGB-D/open-vocabulary robustness, or real navigation `SR` / `SPL` claim follows from this contract alone.",
            "",
            "## Next",
            "",
            "- Run M44 completion verification after the background job finishes.",
            "- Then implement/run M45 heldout query metric conversion using this contract.",
            "",
        ]
    )
    return contract, coverage, batch_query_rows, report


def main() -> None:
    contract, coverage, batch_query_rows, report = build_contract()
    write_json(OUT_DIR / "contract.json", contract)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_json(OUT_DIR / "table_schema.json", contract["schema"])
    write_jsonl(OUT_DIR / "policy_contract_rows.jsonl", contract["policies"])
    for batch_id, rows in sorted(batch_query_rows.items()):
        write_jsonl(OUT_DIR / f"{batch_id}_query_rows.jsonl", rows)
    write_text(OUT_DIR / "report.md", report)
    print(json.dumps(coverage, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
