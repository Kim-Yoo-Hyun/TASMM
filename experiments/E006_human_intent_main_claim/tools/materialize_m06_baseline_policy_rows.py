#!/usr/bin/env python3
"""Materialize E006-M06 baseline policy rows without target-aware leakage."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
M05_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M05_schema_pair_materialization_smoke_v0"
)
DEFAULT_OUT_ROOT = (
    REPO_ROOT
    / "experiments/E006_human_intent_main_claim/artifacts/"
    / "E006-M06_baseline_policy_materialization_smoke_v0"
)
VERSION = "e006_m06_baseline_policy_materialization_smoke_v0"

BLOCKED_TERMS = [
    "target_uid",
    "target_object_instance_id",
    "eval_goal_coordinate",
    "oracle_viewpoint",
    "success_label",
    "target_rank",
    "target_distance",
]

TASK_CONTEXT_POLICY_IDS = {
    "no_staleness_memory_trust_v0",
    "no_reobserve_budget_v0",
    "no_path_search_cost_v0",
    "task_context_only_v0",
    "h001_task_conditioned_memory_trust_v0",
    "oracle_target_available_v0",
    "oracle_context_utility_v0",
}

POLICY_DEFS = {
    "static_stale_memory_v0": {
        "family": "memory_only",
        "allowed": ["old_memory_candidate"],
        "action": "trust_old",
        "budget": 1,
        "old": True,
        "reobserve": False,
        "source": "old_memory",
    },
    "detector_confidence_topk_v0": {
        "family": "detector_only",
        "allowed": ["current_proposal_confidence", "candidate_rank"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "current_detector",
    },
    "fixed_topk_always5_v0": {
        "family": "fixed_topk",
        "allowed": ["candidate_rank"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "current_candidates",
    },
    "context_agnostic_memory_trust_reobserve_v0": {
        "family": "context_agnostic",
        "allowed": ["staleness", "memory_reliability", "proposal_reliability", "source_ready_flag"],
        "action": "reobserve_current",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "mixed_memory_current",
    },
    "all_high_value_memory_trust_counterfactual_v0": {
        "family": "constant_context",
        "allowed": ["staleness", "memory_reliability", "proposal_reliability", "frozen_high_value_profile"],
        "action": "reobserve_current",
        "budget": 8,
        "old": False,
        "reobserve": True,
        "source": "mixed_memory_current",
    },
    "all_reobserve_budget5_v0": {
        "family": "context_agnostic",
        "allowed": ["current_proposal_availability", "fixed_budget"],
        "action": "reobserve_current",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "current_candidates",
    },
    "risk_threshold_only_v0": {
        "family": "risk_only",
        "allowed": ["staleness", "motion_risk", "source_ready_flag"],
        "action": "trust_old",
        "budget": 1,
        "old": True,
        "reobserve": False,
        "source": "old_memory",
    },
    "path_cost_only_reachable_first_v0": {
        "family": "cost_only",
        "allowed": ["reachability", "path_cost", "source_ready_flag"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "path_ready_candidates",
    },
    "proposal_reliability_only_v0": {
        "family": "proposal_reliability",
        "allowed": ["proposal_source", "proposal_confidence", "depth_support"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "current_detector",
    },
    "dev_best_global_mixture_v0": {
        "family": "context_agnostic",
        "allowed": ["dev_frozen_global_weights", "staleness", "proposal_confidence", "path_cost"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "global_mixture",
    },
    "conceptgraphs_only_open_vocab_map_v0": {
        "family": "external_map",
        "allowed": ["conceptgraphs_rank", "conceptgraphs_score", "candidate_coordinate"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": False,
        "source": "conceptgraphs",
    },
    "open3dsg_vocab_only_scene_graph_v0": {
        "family": "external_scene_graph",
        "allowed": ["open3dsg_vocab_score", "candidate_coordinate"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": False,
        "source": "open3dsg",
    },
    "no_task_context_v0": {
        "family": "ablation",
        "allowed": ["staleness", "proposal_reliability", "path_cost"],
        "action": "visit_candidates",
        "budget": 5,
        "old": False,
        "reobserve": True,
        "source": "mixed_memory_current",
    },
    "no_staleness_memory_trust_v0": {
        "family": "ablation",
        "allowed": ["task_context", "proposal_reliability", "path_cost"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "current_candidates",
    },
    "no_reobserve_budget_v0": {
        "family": "ablation",
        "allowed": ["task_context", "staleness", "proposal_reliability", "path_cost"],
        "action": "trust_old",
        "budget": 1,
        "old": True,
        "reobserve": False,
        "source": "old_memory",
    },
    "no_path_search_cost_v0": {
        "family": "ablation",
        "allowed": ["task_context", "staleness", "proposal_reliability"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "mixed_memory_current",
    },
    "task_context_only_v0": {
        "family": "ablation",
        "allowed": ["task_context"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "task_context_prior",
    },
    "h001_task_conditioned_memory_trust_v0": {
        "family": "task_conditioned",
        "allowed": ["task_context", "staleness", "proposal_reliability", "path_cost", "source_ready_flag"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "h001_policy",
    },
    "oracle_target_available_v0": {
        "family": "oracle_diagnostic",
        "allowed": ["oracle_placeholder_after_policy_freeze"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "oracle_placeholder",
    },
    "oracle_context_utility_v0": {
        "family": "oracle_diagnostic",
        "allowed": ["oracle_placeholder_after_policy_freeze", "task_context"],
        "action": "visit_candidates",
        "budget": "context",
        "old": False,
        "reobserve": True,
        "source": "oracle_placeholder",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stable_hash(raw: str, length: int = 12) -> str:
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]


def budget_for(policy: dict[str, Any], paired_row: dict[str, Any]) -> int:
    raw = policy["budget"]
    if raw == "context":
        return int(paired_row["search_budget"])
    return int(raw)


def decision_for(policy_id: str, policy: dict[str, Any], paired_row: dict[str, Any]) -> tuple[str, bool, bool]:
    if policy_id == "risk_threshold_only_v0":
        low_motion = paired_row.get("source_row_band") == "low_motion_control"
        return ("trust_old" if low_motion else "reobserve_current", low_motion, not low_motion)
    if policy_id == "context_agnostic_memory_trust_reobserve_v0" and paired_row.get("source_ready_group") == "source_gap":
        return "trust_old", True, False
    if policy_id == "h001_task_conditioned_memory_trust_v0":
        if paired_row.get("task_type") in {"avoid_false_alarm", "low_value_fast"}:
            return "trust_old", True, False
        return "visit_candidates", False, True
    return str(policy["action"]), bool(policy["old"]), bool(policy["reobserve"])


def candidate_ids(policy: dict[str, Any], paired_row: dict[str, Any], budget: int) -> list[str]:
    source = str(policy["source"])
    seed = f"{paired_row['evidence_group_id']}|{paired_row['context_id']}|{source}"
    if source == "old_memory":
        return [f"old_memory_candidate_{paired_row['source_reference_hash']}"]
    return [
        f"{source}_candidate_{stable_hash(seed + '|' + str(index), 10)}"
        for index in range(1, max(1, budget) + 1)
    ]


def expected_cost(policy_id: str, paired_row: dict[str, Any], budget: int, reobserve: bool) -> float:
    reobserve_cost = float(paired_row.get("old_location_dead_end_penalty", 0)) * 0.05 if reobserve else 0.0
    source_penalty = 1.0 if paired_row.get("source_ready_group") == "source_gap" else 0.0
    if policy_id in {"static_stale_memory_v0", "risk_threshold_only_v0", "no_reobserve_budget_v0"}:
        return 1.0 + source_penalty
    return float(budget) + reobserve_cost + source_penalty


def materialize(out_root: Path) -> dict[str, Any]:
    paired_rows = read_jsonl(M05_ROOT / "paired_context_queries.jsonl")
    manifest = read_json(M05_ROOT / "implementation_manifest.json")
    policy_ids = list(manifest.get("policy_ids", []))
    missing_policy_defs = sorted(set(policy_ids) - set(POLICY_DEFS))
    if missing_policy_defs:
        raise RuntimeError(f"Missing policy definitions: {missing_policy_defs}")

    out_rows: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    for paired in paired_rows:
        for policy_id in policy_ids:
            policy = POLICY_DEFS[policy_id]
            budget = budget_for(policy, paired)
            action, old_trusted, reobserve = decision_for(policy_id, policy, paired)
            ranked = candidate_ids(policy, paired, budget)
            uses_task_context = policy_id in TASK_CONTEXT_POLICY_IDS
            row = {
                "allowed_input_groups": policy["allowed"],
                "context_id": paired["context_id"],
                "decision_action": action,
                "e006_policy_row_version": VERSION,
                "expected_search_cost": expected_cost(policy_id, paired, budget, reobserve),
                "old_memory_trusted": old_trusted,
                "pair_id": paired["pair_id"],
                "path_cost_m": None,
                "policy_family": policy["family"],
                "policy_id": policy_id,
                "query_id": paired["query_id"],
                "ranked_candidate_ids": ranked,
                "reobserve_selected": reobserve,
                "selected_budget": budget,
                "source_ready_flag": paired["source_ready_group"] == "source_ready",
                "uses_task_context": uses_task_context,
            }
            out_rows.append(row)
            serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
            hits = [term for term in BLOCKED_TERMS if term in serialized]
            leakage_rows.append(
                {
                    "context_id": paired["context_id"],
                    "pair_id": paired["pair_id"],
                    "policy_id": policy_id,
                    "query_id": paired["query_id"],
                    "blocked_term_hits": hits,
                    "leakage_audit_status": "pass" if not hits else "fail",
                    "uses_task_context": uses_task_context,
                }
            )

    fail_rows = [row for row in leakage_rows if row["leakage_audit_status"] != "pass"]
    family_counts = Counter(row["policy_family"] for row in out_rows)
    task_context_counts = Counter(str(row["uses_task_context"]).lower() for row in out_rows)
    action_counts = Counter(row["decision_action"] for row in out_rows)
    summary = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ready" if not fail_rows else "failed",
        "paired_context_rows": len(paired_rows),
        "policy_count": len(policy_ids),
        "baseline_policy_rows": len(out_rows),
        "leakage_audit_rows": len(leakage_rows),
        "leakage_fail_rows": len(fail_rows),
        "policy_family_counts": dict(sorted(family_counts.items())),
        "uses_task_context_counts": dict(sorted(task_context_counts.items())),
        "decision_action_counts": dict(sorted(action_counts.items())),
        "output_root": str(out_root),
        "selected_next_unit": "E006-M07 utility metric row materialization smoke"
        if not fail_rows
        else "repair E006-M06 baseline policy row leakage",
        "human_intent_main_claim_ready": False,
        "utility_improvement_ready": False,
        "real_navigation_sr_spl_ready": False,
        "final_real_rgbd_open_vocab_robustness_ready": False,
    }

    report = "\n".join(
        [
            "# E006-M06 Baseline Policy Row Materialization Smoke",
            "",
            "## Facts",
            "",
            f"- Status: `{summary['status']}`.",
            f"- Paired context rows: {summary['paired_context_rows']}.",
            f"- Policy count: {summary['policy_count']}.",
            f"- Baseline policy rows: {summary['baseline_policy_rows']}.",
            f"- Leakage fail rows: {summary['leakage_fail_rows']}.",
            f"- Selected next unit: {summary['selected_next_unit']}.",
            "",
            "## Claim Boundary",
            "",
            "- M06 materializes frozen policy outputs only.",
            "- M06 does not compute utility metrics, success labels, transfer results, real navigation `SR` / `SPL`, or human-intent main-claim evidence.",
            "",
        ]
    )

    write_jsonl(out_root / "baseline_policy_rows.jsonl", out_rows)
    write_jsonl(out_root / "leakage_audit_rows.jsonl", leakage_rows)
    write_json(out_root / "summary.json", summary)
    write_text(out_root / "report.md", report)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args()
    args.out_root.mkdir(parents=True, exist_ok=True)
    summary = materialize(args.out_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
