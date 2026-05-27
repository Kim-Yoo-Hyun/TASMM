#!/usr/bin/env python3
"""Decide the E005-M90 label-normalization / scan-prompt scope repair route."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
M68_BATCH_DIR = EXP_ROOT / "artifacts" / "E005-M68_full_denominator_real_proposal_bridge_plan_v0" / "batches" / "heldout_b02"
M87_DIR = EXP_ROOT / "artifacts" / "E005-M87_candidate_survival_threshold_zero_written_v0"
M89_ANALYSIS_DIR = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_analysis_v0"
M89_RUN_DIR = EXP_ROOT / "artifacts" / "E005-M89_cleanup_trace_detector_run_v0" / "heldout_b02"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M90_label_normalization_prompt_scope_repair_v0"
VERSION = "e005_m90_label_normalization_prompt_scope_repair_v0"
SCAN_ID = "569d8f0f-72aa-2f24-89a6-77f8b8779ae9"
BLOCKED_FIELDS = {
    "target_uid",
    "candidate_is_target",
    "matched_3dssg_instance_id",
    "nearest_target_distance",
    "query_success_label",
}


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


def normalize_label_text(label: Any) -> str:
    text = str(label).strip().lower().replace(".", " ")
    for prefix in ("a ", "an ", "the "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return " ".join(text.split())


def current_prompt_lookup(prompt_payload: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in prompt_payload.get("labels", []):
        canonical = str(row.get("label_canonical", "")).strip()
        if not canonical:
            continue
        lookup[canonical.lower()] = canonical
        for prompt in row.get("prompts", []):
            lookup[str(prompt).strip().lower()] = canonical
    return lookup


def resolve_current(label: Any, prompt_payload: dict[str, Any], active_labels: list[str]) -> str:
    prompt_map = current_prompt_lookup(prompt_payload)
    normalized = normalize_label_text(label)
    direct = prompt_map.get(normalized)
    if direct:
        return direct

    matches = []
    for candidate in active_labels:
        candidate_norm = normalize_label_text(candidate)
        index = normalized.find(candidate_norm)
        if index >= 0:
            matches.append((index, -len(candidate_norm), candidate))
    if matches:
        return sorted(matches)[0][2]

    for prompt, canonical in prompt_map.items():
        prompt_norm = normalize_label_text(prompt)
        if prompt_norm and prompt_norm in normalized:
            return canonical
    return normalized


def resolve_active_exact_first(label: Any, prompt_payload: dict[str, Any], active_labels: list[str]) -> str:
    normalized = normalize_label_text(label)
    active_by_norm = {normalize_label_text(label): label for label in active_labels}
    if normalized in active_by_norm:
        return active_by_norm[normalized]
    return resolve_current(label, prompt_payload, active_labels)


def detector_prompt_labels(prompt_payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("label_canonical"))
        for row in prompt_payload.get("labels", [])
        if row.get("detector_prompt_enabled", True)
    }


def prompt_conflict_rows(prompt_payload: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in prompt_payload.get("labels", []):
        canonical = str(row.get("label_canonical"))
        prompts = [canonical, *[str(prompt) for prompt in row.get("prompts", [])]]
        for prompt in prompts:
            normalized = normalize_label_text(prompt)
            if not normalized:
                continue
            grouped[normalized].append(
                {
                    "canonical": canonical,
                    "detector_prompt_enabled": bool(row.get("detector_prompt_enabled", True)),
                    "prompt_text": prompt,
                    "scan_ids": row.get("scan_ids", []),
                }
            )
    rows = []
    for normalized, entries in sorted(grouped.items()):
        canonical_labels = sorted({entry["canonical"] for entry in entries})
        if len(canonical_labels) <= 1:
            continue
        rows.append(
            {
                "canonical_labels": canonical_labels,
                "entry_count": len(entries),
                "entries": entries,
                "normalized_prompt": normalized,
            }
        )
    return rows


def replay_cleanup_decisions(
    trace_rows: list[dict[str, Any]],
    prompt_payload: dict[str, Any],
    active_labels: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    enabled_labels = detector_prompt_labels(prompt_payload)
    rows = []
    current_decisions = Counter()
    active_exact_decisions = Counter()
    current_labels = Counter()
    active_exact_labels = Counter()
    for row in trace_rows:
        blocked = sorted(field for field in BLOCKED_FIELDS if field in row)
        label_text = row.get("label_text")
        current_label = resolve_current(label_text, prompt_payload, active_labels)
        active_exact_label = resolve_active_exact_first(label_text, prompt_payload, active_labels)

        def decision(label: str) -> tuple[str, str | None]:
            if label not in enabled_labels:
                return "drop", "drop_non_prompt_label"
            if label not in set(active_labels):
                return "drop", "drop_not_scan_prompt_label"
            return "keep", None

        current_decision, current_reason = decision(current_label)
        active_exact_decision, active_exact_reason = decision(active_exact_label)
        current_decisions[current_decision] += 1
        active_exact_decisions[active_exact_decision] += 1
        current_labels[current_label] += 1
        active_exact_labels[active_exact_label] += 1
        rows.append(
            {
                "active_exact_decision": active_exact_decision,
                "active_exact_drop_reason": active_exact_reason,
                "active_exact_label": active_exact_label,
                "blocked_fields": blocked,
                "current_decision": current_decision,
                "current_drop_reason": current_reason,
                "current_label": current_label,
                "label_text": label_text,
                "raw_candidate_uid": row.get("raw_candidate_uid"),
                "scan_id": row.get("scan_id"),
            }
        )
    summary = {
        "active_exact_decisions": dict(sorted(active_exact_decisions.items())),
        "active_exact_labels": dict(sorted(active_exact_labels.items())),
        "blocked_field_hit_count": sum(1 for row in rows if row["blocked_fields"]),
        "current_decisions": dict(sorted(current_decisions.items())),
        "current_labels": dict(sorted(current_labels.items())),
    }
    return rows, summary


def build_repair_options(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "decision": "selected",
            "false_positive_risk": "bounded_by_existing_per_scan_label_cap_but_requires_rerun_match_check",
            "leakage_status": "allowed_inputs_only",
            "option_id": "active_scan_exact_label_precedence_v0",
            "reason": "Exact normalized detector text `chair` should resolve to active scan label `chair` before global duplicate prompt aliases can map it to `stool`.",
            "runner_source_edit_required": True,
            "uses": ["label_text", "active_scan_labels", "prompt_set labels/prompts"],
        },
        {
            "decision": "rejected",
            "false_positive_risk": "high",
            "leakage_status": "allowed_inputs_only_but_semantically_unsafe",
            "option_id": "scan_prompt_scope_expand_stool_for_chair_scan_v0",
            "reason": "Allowing canonical `stool` in a `chair`-only active scan preserves the wrong semantic label and is unlikely to match `chair` targets under label-aware evaluation.",
            "runner_source_edit_required": False,
            "uses": ["active_scan_labels", "enabled_prompt_labels"],
        },
        {
            "decision": "defer",
            "false_positive_risk": "medium",
            "leakage_status": "allowed_inputs_only_if_global_and_precommitted",
            "option_id": "global_prompt_alias_deduplication_v0",
            "reason": "Removing duplicate prompt aliases globally may be valid, but it changes every scan/label and should follow a smaller active-label precedence smoke.",
            "runner_source_edit_required": True,
            "uses": ["prompt_set labels/prompts"],
        },
    ]


def build_contract(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocked_inputs": sorted(BLOCKED_FIELDS),
        "decision": coverage["selected_route"],
        "next_unit": coverage["next_recommended_unit"],
        "policy_contract": {
            "rule": "When normalized detector label text exactly matches a scan-active canonical label, return that active label before using global prompt alias lookup.",
            "stage": "label_text_to_label_canonical_resolution_before_cleanup",
        },
        "required_checks_before_detector_rerun": [
            "runner source patch uses only target-independent fields",
            "one-scan cleanup smoke shows dropped `chair` rows become post-cleanup candidates",
            "selected proposal count remains bounded by per-scan-label cap",
            "matching/query conversion is run before any robustness claim",
        ],
        "version": VERSION,
    }


def build_report(
    coverage: dict[str, Any],
    conflict_rows: list[dict[str, Any]],
    replay_summary: dict[str, Any],
    repair_options: list[dict[str, Any]],
) -> str:
    conflict_lines = ["| Normalized prompt | Canonical labels | Entries |", "| --- | --- | ---: |"]
    for row in conflict_rows[:20]:
        conflict_lines.append(
            f"| `{row['normalized_prompt']}` | `{', '.join(row['canonical_labels'])}` | {row['entry_count']} |"
        )
    option_lines = ["| Option | Decision | Reason |", "| --- | --- | --- |"]
    for row in repair_options:
        option_lines.append(f"| `{row['option_id']}` | `{row['decision']}` | {row['reason']} |")
    return "\n".join(
        [
            "# E005-M90 Label Normalization / Prompt Scope Repair Decision",
            "",
            "## Facts",
            "",
            f"- Status: `{coverage['status']}`.",
            f"- Scan: `{coverage['scan_id']}`.",
            f"- M89 trace rows: {coverage['trace_rows']}.",
            f"- M89 drop reasons: `{coverage['m89_drop_reason_counts']}`.",
            f"- Active scan labels: `{coverage['active_scan_labels']}`.",
            f"- Current replay decisions: `{replay_summary['current_decisions']}`.",
            f"- Active-exact replay decisions: `{replay_summary['active_exact_decisions']}`.",
            f"- Blocked-field hits: {coverage['blocked_field_hit_count']}.",
            f"- Worst-case new selected proposal upper bound before matching: {coverage['worst_case_new_selected_proposal_upper_bound']}.",
            "",
            "## Prompt Conflicts",
            "",
            *conflict_lines,
            "",
            "## Options",
            "",
            *option_lines,
            "",
            "## Agent Inference",
            "",
            "- The dominant failure is not a threshold, ranking, or cap issue.",
            "- The safest repair is scan-active exact label precedence because it changes `a chair` / `chair` back to the active `chair` label before cleanup.",
            "- Scan-prompt expansion that simply allows `stool` in a `chair` scan is rejected because it preserves the wrong semantic label and can inflate false positives.",
            "- This decision still does not support final real RGB-D/open-vocabulary robustness. A patched one-scan smoke and matching/query conversion are required first.",
            "",
            "## Next",
            "",
            f"- {coverage['next_recommended_unit']}.",
            "",
        ]
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_payload = read_json(M68_BATCH_DIR / "prompt_set.json")
    trace_rows = read_jsonl(M89_RUN_DIR / "container_output" / "cleanup_trace.jsonl")
    m89_coverage = read_json(M89_ANALYSIS_DIR / "coverage.json")
    active_labels = [str(label) for label in m89_coverage.get("active_scan_labels", [])]
    conflict_rows = prompt_conflict_rows(prompt_payload)
    replay_rows, replay_summary = replay_cleanup_decisions(trace_rows, prompt_payload, active_labels)
    repair_options = build_repair_options({})
    zero_written_rows = read_jsonl(M87_DIR / "zero_written_rows.jsonl")
    per_scan_label_cap = int(read_json(M89_RUN_DIR / "container_output" / "pre_cap_policy_summary.json").get("per_scan_label_cap") or 24)
    keep_count = int(replay_summary["active_exact_decisions"].get("keep", 0))
    coverage = {
        "active_scan_labels": active_labels,
        "active_exact_replay_keep_rows": keep_count,
        "blocked_field_hit_count": int(replay_summary["blocked_field_hit_count"]),
        "candidate_rerun_now": False,
        "detector_rerun_now": False,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "m89_drop_reason_counts": m89_coverage.get("drop_reason_counts", {}),
        "m89_status": m89_coverage.get("status"),
        "next_recommended_unit": "E005-M91 active-label precedence runner patch / one-scan cleanup smoke",
        "prompt_conflict_count": len(conflict_rows),
        "prompt_repair_now": False,
        "repair_contract_ready": True,
        "scan_id": SCAN_ID,
        "selected_route": "active_scan_exact_label_precedence_then_one_scan_cleanup_smoke",
        "status": "e005_m90_label_normalization_prompt_scope_repair_decision_ready",
        "threshold_relaxation_now": False,
        "trace_rows": len(trace_rows),
        "version": VERSION,
        "worst_case_new_selected_proposal_upper_bound": min(keep_count, per_scan_label_cap),
        "zero_written_query_rows": sum(int(row.get("query_exposure_rows") or 0) for row in zero_written_rows),
        "zero_written_targets": len(zero_written_rows),
    }
    repair_options = build_repair_options(coverage)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "prompt_conflict_rows.jsonl", conflict_rows)
    write_jsonl(OUT_DIR / "cleanup_replay_rows.jsonl", replay_rows)
    write_jsonl(OUT_DIR / "repair_options.jsonl", repair_options)
    write_json(OUT_DIR / "repair_contract.json", build_contract(coverage))
    write_text(OUT_DIR / "report.md", build_report(coverage, conflict_rows, replay_summary, repair_options))
    print(json.dumps(coverage, indent=2, sort_keys=True))
    return 0 if coverage["status"].endswith("_ready") and not coverage["blocked_field_hit_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
