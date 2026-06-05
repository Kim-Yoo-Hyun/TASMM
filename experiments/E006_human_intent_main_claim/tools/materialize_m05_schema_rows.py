#!/usr/bin/env python3
"""Materialize E006-M05 schema and paired-context smoke rows.

This script intentionally creates only schema / manifest / paired-context rows.
It does not generate policy outputs or utility metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M05_schema_pair_materialization_smoke_v0"
)
E007_M04_ROWS = (
    REPO_ROOT
    / "experiments/E007_navigation_path_cost_bridge/artifacts/"
    / "E007-M04_path_cost_policy_metrics_v0/query_policy_metric_rows.jsonl"
)
E005_M100_ROWS = (
    REPO_ROOT
    / "experiments/E005_external_baseline_transition/artifacts/"
    / "E005-M100_conceptgraphs_assisted_fallback_policy_v0/selected_policy_rows.jsonl"
)

METHOD_POLICY = "h001_then_conceptgraphs_top5_on_observed_miss_v0"
CONTRACT_VERSION = "e006_m05_schema_pair_materialization_smoke_v0"


TASK_PROFILES = [
    {
        "utility_profile_id": "routine_fetch_v0",
        "task_type": "routine_fetch",
        "task_group": "fetch_value",
        "target_value": 10,
        "miss_penalty": 6,
        "false_trust_penalty": 4,
        "reobserve_cost": 1.0,
        "search_budget": 5,
        "old_location_dead_end_penalty": 2,
        "latency_weight": 0.50,
    },
    {
        "utility_profile_id": "high_value_fetch_v0",
        "task_type": "high_value_fetch",
        "task_group": "fetch_value",
        "target_value": 25,
        "miss_penalty": 25,
        "false_trust_penalty": 8,
        "reobserve_cost": 1.5,
        "search_budget": 8,
        "old_location_dead_end_penalty": 4,
        "latency_weight": 0.40,
    },
    {
        "utility_profile_id": "urgent_fetch_v0",
        "task_type": "urgent_fetch",
        "task_group": "urgency",
        "target_value": 16,
        "miss_penalty": 12,
        "false_trust_penalty": 5,
        "reobserve_cost": 2.0,
        "search_budget": 3,
        "old_location_dead_end_penalty": 5,
        "latency_weight": 1.00,
    },
    {
        "utility_profile_id": "inspection_v0",
        "task_type": "inspection",
        "task_group": "inspection",
        "target_value": 12,
        "miss_penalty": 8,
        "false_trust_penalty": 2,
        "reobserve_cost": 0.5,
        "search_budget": 10,
        "old_location_dead_end_penalty": 1,
        "latency_weight": 0.20,
    },
    {
        "utility_profile_id": "avoid_false_alarm_v0",
        "task_type": "avoid_false_alarm",
        "task_group": "false_alarm",
        "target_value": 10,
        "miss_penalty": 4,
        "false_trust_penalty": 16,
        "reobserve_cost": 1.0,
        "search_budget": 4,
        "old_location_dead_end_penalty": 10,
        "latency_weight": 0.60,
    },
    {
        "utility_profile_id": "low_value_fast_v0",
        "task_type": "low_value_fast",
        "task_group": "speed_value",
        "target_value": 6,
        "miss_penalty": 3,
        "false_trust_penalty": 6,
        "reobserve_cost": 1.5,
        "search_budget": 3,
        "old_location_dead_end_penalty": 6,
        "latency_weight": 1.00,
    },
    {
        "utility_profile_id": "high_value_slow_v0",
        "task_type": "high_value_slow",
        "task_group": "speed_value",
        "target_value": 24,
        "miss_penalty": 24,
        "false_trust_penalty": 6,
        "reobserve_cost": 0.8,
        "search_budget": 10,
        "old_location_dead_end_penalty": 3,
        "latency_weight": 0.25,
    },
]

PROFILE_BY_ID = {row["utility_profile_id"]: row for row in TASK_PROFILES}
PROFILE_PAIRS = [
    {
        "profile_pair_id": "pair_routine_high_value_v0",
        "context_a": "routine_fetch_v0",
        "context_b": "high_value_fetch_v0",
    },
    {
        "profile_pair_id": "pair_urgent_inspection_v0",
        "context_a": "urgent_fetch_v0",
        "context_b": "inspection_v0",
    },
    {
        "profile_pair_id": "pair_false_alarm_high_value_v0",
        "context_a": "avoid_false_alarm_v0",
        "context_b": "high_value_fetch_v0",
    },
    {
        "profile_pair_id": "pair_fast_slow_v0",
        "context_a": "low_value_fast_v0",
        "context_b": "high_value_slow_v0",
    },
]

POLICY_IDS = [
    "static_stale_memory_v0",
    "detector_confidence_topk_v0",
    "fixed_topk_always5_v0",
    "context_agnostic_memory_trust_reobserve_v0",
    "all_high_value_memory_trust_counterfactual_v0",
    "all_reobserve_budget5_v0",
    "risk_threshold_only_v0",
    "path_cost_only_reachable_first_v0",
    "proposal_reliability_only_v0",
    "dev_best_global_mixture_v0",
    "conceptgraphs_only_open_vocab_map_v0",
    "open3dsg_vocab_only_scene_graph_v0",
    "no_task_context_v0",
    "no_staleness_memory_trust_v0",
    "no_reobserve_budget_v0",
    "no_path_search_cost_v0",
    "task_context_only_v0",
    "h001_task_conditioned_memory_trust_v0",
    "oracle_target_available_v0",
    "oracle_context_utility_v0",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stable_hash(raw: str, length: int = 12) -> str:
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]


def parse_scan_pair(base_row_uid: str) -> tuple[str, str]:
    old_scan, rest = base_row_uid.split("->", 1)
    current_scan, _target_part = rest.rsplit(":", 1)
    return old_scan, current_scan


def profile_hash() -> str:
    payload = json.dumps(TASK_PROFILES, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_ready_group(method_rows: list[dict[str, Any]]) -> str:
    ready_values = [bool(row.get("path_source_ready")) for row in method_rows]
    if all(ready_values):
        return "source_ready"
    if not any(ready_values):
        return "source_gap"
    return "mixed"


def split_row(
    *,
    paired_row: dict[str, Any],
    split_index: int,
    heldout_axis: str,
    split_role: str,
    allow_threshold: bool,
    allow_final: bool,
) -> dict[str, Any]:
    return {
        "allowed_for_final_claim": allow_final,
        "allowed_for_threshold_selection": allow_threshold,
        "heldout_axis": heldout_axis,
        "label_group": paired_row["label_group"],
        "pair_id": paired_row["pair_id"],
        "query_id": paired_row["query_id"],
        "scan_group_id": paired_row["scan_group_id"],
        "source_ready_group": paired_row["source_ready_group"],
        "split_id": f"e006_m05_{heldout_axis}_{split_role}_{split_index:06d}",
        "split_role": split_role,
        "task_group": paired_row["task_group"],
    }


def materialize(out_root: Path) -> dict[str, Any]:
    out_root.mkdir(parents=True, exist_ok=True)

    e007_rows = read_jsonl(E007_M04_ROWS)
    m100_rows = read_jsonl(E005_M100_ROWS)

    method_by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in e007_rows:
        if row.get("policy") == METHOD_POLICY:
            method_by_base[row["base_row_uid"]].append(row)

    meta_by_base: dict[str, dict[str, Any]] = {}
    for row in m100_rows:
        base = row["base_row_uid"]
        if base not in meta_by_base:
            meta_by_base[base] = {
                "batch_id": row.get("batch_id", "unknown_batch"),
                "current_rescan_id": row.get("current_rescan_id"),
                "label_group": row.get("label_canonical", "unknown_label"),
                "row_band": row.get("row_band", "unknown_row_band"),
            }

    missing_meta = sorted(set(method_by_base) - set(meta_by_base))
    if missing_meta:
        raise RuntimeError(f"Missing M100 metadata for {len(missing_meta)} base rows")

    paired_rows: list[dict[str, Any]] = []
    transfer_rows: list[dict[str, Any]] = []

    dev_labels = {
        meta["label_group"]
        for base, meta in meta_by_base.items()
        if meta["batch_id"] == "heldout_b01" and base in method_by_base
    }
    dev_task_groups = {"fetch_value", "false_alarm"}

    for base_index, base in enumerate(sorted(method_by_base)):
        old_scan, current_scan = parse_scan_pair(base)
        method_rows = method_by_base[base]
        meta = meta_by_base[base]
        evidence_group_id = f"e006_ev_{stable_hash(base)}"
        scan_group_id = f"{old_scan}__{current_scan}"
        group = source_ready_group(method_rows)
        source_limited_reasons = sorted(
            {
                row.get("path_source_limited_reason")
                for row in method_rows
                if row.get("path_source_limited_reason")
            }
        )

        for pair in PROFILE_PAIRS:
            pair_key = f"{base}|{pair['profile_pair_id']}"
            pair_id = f"e006_pair_{stable_hash(pair_key)}"
            for profile_id in (pair["context_a"], pair["context_b"]):
                profile = PROFILE_BY_ID[profile_id]
                query_key = f"{pair_key}|{profile_id}"
                row = {
                    "blocked_field_audit": "pass",
                    "context_id": f"ctx_{profile_id}",
                    "cost_source_groups": ["candidate_rank_only", "candidate_plus_path"],
                    "evidence_group_id": evidence_group_id,
                    "label_group": meta["label_group"],
                    "old_location_dead_end_penalty": profile[
                        "old_location_dead_end_penalty"
                    ],
                    "pair_id": pair_id,
                    "profile_pair_id": pair["profile_pair_id"],
                    "query_id": f"e006_q_{stable_hash(query_key)}",
                    "scan_group_id": scan_group_id,
                    "search_budget": profile["search_budget"],
                    "source_batch_id": meta["batch_id"],
                    "source_ready_group": group,
                    "source_reference_hash": stable_hash(base, 16),
                    "source_row_band": meta["row_band"],
                    "source_limited_reasons": source_limited_reasons,
                    "task_group": profile["task_group"],
                    "task_type": profile["task_type"],
                    "utility_profile_id": profile_id,
                }
                paired_rows.append(row)

                if meta["batch_id"] == "heldout_b01":
                    scan_role = "dev"
                    scan_threshold = True
                    scan_final = False
                else:
                    scan_role = "heldout_scan"
                    scan_threshold = False
                    scan_final = True
                transfer_rows.append(
                    split_row(
                        paired_row=row,
                        split_index=len(transfer_rows),
                        heldout_axis="scan",
                        split_role=scan_role,
                        allow_threshold=scan_threshold,
                        allow_final=scan_final,
                    )
                )

                if row["label_group"] in dev_labels:
                    label_role = "dev"
                    label_threshold = True
                    label_final = False
                else:
                    label_role = "heldout_label"
                    label_threshold = False
                    label_final = True
                transfer_rows.append(
                    split_row(
                        paired_row=row,
                        split_index=len(transfer_rows),
                        heldout_axis="label",
                        split_role=label_role,
                        allow_threshold=label_threshold,
                        allow_final=label_final,
                    )
                )

                if row["task_group"] in dev_task_groups:
                    task_role = "dev"
                    task_threshold = True
                    task_final = False
                else:
                    task_role = "heldout_task"
                    task_threshold = False
                    task_final = True
                transfer_rows.append(
                    split_row(
                        paired_row=row,
                        split_index=len(transfer_rows),
                        heldout_axis="task",
                        split_role=task_role,
                        allow_threshold=task_threshold,
                        allow_final=task_final,
                    )
                )

                transfer_rows.append(
                    split_row(
                        paired_row=row,
                        split_index=len(transfer_rows),
                        heldout_axis="source",
                        split_role="stress",
                        allow_threshold=False,
                        allow_final=row["source_ready_group"] != "mixed",
                    )
                )
                transfer_rows.append(
                    split_row(
                        paired_row=row,
                        split_index=len(transfer_rows),
                        heldout_axis="external_route",
                        split_role="stress",
                        allow_threshold=False,
                        allow_final=True,
                    )
                )

    schema = {
        "blocked_inputs": [
            "target_uid",
            "target_object_instance_id",
            "eval_goal_coordinate",
            "oracle_viewpoint",
            "success_label",
            "target_rank",
            "target_distance",
            "future_observation",
        ],
        "constants": {
            "budget_overrun_penalty": 10.0,
            "path_unit_m": 5.0,
            "primary_cost_source_rule": "group-separated",
        },
        "fields": {
            "false_trust_penalty": "cost of trusting stale memory incorrectly",
            "latency_weight": "penalty weight for expected search/path cost",
            "miss_penalty": "cost of missing target under task context",
            "old_location_dead_end_penalty": "task-specific stale old-location penalty",
            "reobserve_cost": "cost of current re-observation or extra checks",
            "search_budget": "candidate/action budget",
            "target_value": "utility of finding target",
            "task_type": "structured task type",
        },
        "profile_pairs": PROFILE_PAIRS,
        "profiles": TASK_PROFILES,
        "schema_version": "task_context_schema_v0",
        "utility_formula_id": "context_utility_v0",
        "version": CONTRACT_VERSION,
    }

    blocked_output_terms = [
        "target_uid",
        "target_object_instance_id",
        "eval_goal_coordinate",
        "oracle_viewpoint",
        "success_label",
        "target_rank",
        "target_distance",
    ]
    serialized_outputs = "\n".join(
        [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in paired_rows]
    )
    blocked_hits = [
        term for term in blocked_output_terms if term in serialized_outputs
    ]
    blocked_status = "pass" if not blocked_hits else "fail"

    manifest = {
        "blocked_input_audit": {
            "blocked_output_term_hits": blocked_hits,
            "omitted_fields": blocked_output_terms,
            "status": blocked_status,
        },
        "cost_source_groups": ["candidate_rank_only", "candidate_plus_path"],
        "dev_selection_fields": [
            "context_agnostic_thresholds",
            "global_mixture_weights",
            "candidate_budget",
            "source_ready_threshold",
        ],
        "docker_image": "not_required_for_schema_materialization_smoke",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "implementation_manifest_version": "implementation_manifest_v0",
        "m04_contract_version": "e006_m04_utility_formula_v0",
        "m05_contract_version": CONTRACT_VERSION,
        "outputs": {
            "implementation_manifest": str(out_root / "implementation_manifest.json"),
            "paired_context_queries": str(out_root / "paired_context_queries.jsonl"),
            "summary": str(out_root / "summary.json"),
            "task_context_schema": str(out_root / "task_context_schema.json"),
            "transfer_split_manifest": str(out_root / "transfer_split_manifest.jsonl"),
        },
        "policy_ids": POLICY_IDS,
        "profile_table_hash": profile_hash(),
        "reproduction_commands": [
            "python experiments/E006_human_intent_main_claim/tools/materialize_m05_schema_rows.py",
            "python -m py_compile experiments/E006_human_intent_main_claim/tools/materialize_m05_schema_rows.py",
        ],
        "search_cost_contract_id": "search_cost_contract_v0",
        "source_artifact_roots": {
            "e005_m100_selected_policy_rows": str(E005_M100_ROWS),
            "e007_m04_query_policy_metric_rows": str(E007_M04_ROWS),
        },
        "task_context_schema_version": "task_context_schema_v0",
        "utility_formula_id": "context_utility_v0",
    }

    summary = {
        "blocked_input_audit_status": blocked_status,
        "contract_status": "ready" if blocked_status == "pass" else "failed",
        "cost_source_groups": ["candidate_rank_only", "candidate_plus_path"],
        "evidence_group_count": len(method_by_base),
        "generated_at": manifest["generated_at"],
        "label_group_count": len({row["label_group"] for row in paired_rows}),
        "m05_contract_version": CONTRACT_VERSION,
        "paired_context_rows": len(paired_rows),
        "profile_pair_count": len(PROFILE_PAIRS),
        "source_ready_group_counts": dict(
            Counter(row["source_ready_group"] for row in paired_rows)
        ),
        "split_role_counts": dict(Counter(row["split_role"] for row in transfer_rows)),
        "task_group_count": len({row["task_group"] for row in paired_rows}),
        "transfer_manifest_rows": len(transfer_rows),
    }

    write_json(out_root / "task_context_schema.json", schema)
    write_json(out_root / "implementation_manifest.json", manifest)
    write_jsonl(out_root / "paired_context_queries.jsonl", paired_rows)
    write_jsonl(out_root / "transfer_split_manifest.jsonl", transfer_rows)
    write_json(out_root / "summary.json", summary)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args()
    summary = materialize(args.out_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["contract_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
