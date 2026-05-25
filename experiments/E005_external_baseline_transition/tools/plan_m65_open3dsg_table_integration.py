#!/usr/bin/env python3
"""Build E005-M65 Open3DSG table-integration and claim-boundary decision."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = ROOT / "experiments" / "E005_external_baseline_transition"
OUT_DIR = EXP_ROOT / "artifacts" / "E005-M65_open3dsg_table_integration_v0"
VERSION = "e005_m65_open3dsg_table_integration_v0"

M49_METRICS = EXP_ROOT / "artifacts" / "E005-M49_conceptgraphs_full_heldout_aggregation_v0" / "metrics.json"
M52_METRICS = EXP_ROOT / "artifacts" / "E005-M52_h001_heldout_policy_replay_v0" / "metrics.json"
M54_COVERAGE = EXP_ROOT / "artifacts" / "E005-M54_paper_table_claim_ledger_v0" / "coverage.json"
M60_METRICS = EXP_ROOT / "artifacts" / "E005-M60_open3dsg_query_conversion_m61_v0" / "metrics.json"
M64_METRICS = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0" / "metrics.json"
M64_COVERAGE = EXP_ROOT / "artifacts" / "E005-M64_open3dsg_vocab_expansion_policy_v0" / "coverage.json"

H001 = "task_context_memory_trust_reobserve_v0"
STATIC = "static_memory_only_v0"
CONTEXT_AGNOSTIC = "context_agnostic_memory_trust_reobserve_v0"
DETECTOR_TOP5 = "detector_top5_v0"
CONCEPTGRAPHS = "conceptgraphs_clip_rank_bbox_strict_top5_v0"
OPEN3DSG_PRIMARY = "open3dsg_objects_probs_bbox_strict_top5_v0"
OPEN3DSG_VOCAB = "open3dsg_predicted_terms_bbox_strict_top5_v0"
OPEN3DSG_VOCAB_RELAXED = "open3dsg_predicted_terms_bbox_relaxed_1m_top3_v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def metric(source: str, policy: str, payload: dict[str, Any]) -> dict[str, Any]:
    return payload["policy_metrics"][policy]


def table_row(
    *,
    source: str,
    policy: str,
    label: str,
    role: str,
    metric_payload: dict[str, Any],
    note: str,
    include_in_main_table: bool,
) -> dict[str, Any]:
    m = metric(source, policy, metric_payload)
    return {
        "source": source,
        "policy": policy,
        "paper_label": label,
        "paper_table_role": role,
        "rows": m["rows"],
        "success_rows": m["query_bridge_success_rows"],
        "success_rate": m["query_bridge_success_rate"],
        "target_detected_rows": m.get("target_detected_rows"),
        "target_detected_rate": m.get("target_detected_rate"),
        "mean_expected_search_cost": m["mean_expected_search_cost"],
        "mean_attempt_spl_proxy": m["mean_attempt_spl_proxy"],
        "old_location_dead_end_avoided_rows": m.get("old_location_dead_end_avoided_rows"),
        "include_in_main_table": include_in_main_table,
        "note": note,
    }


def add_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy = {row["policy"]: row for row in rows}
    h001 = by_policy[H001]
    concept = by_policy[CONCEPTGRAPHS]
    open3dsg_vocab = by_policy[OPEN3DSG_VOCAB]
    for row in rows:
        row["success_rows_delta_vs_h001"] = int(row["success_rows"]) - int(h001["success_rows"])
        row["success_rows_delta_vs_conceptgraphs"] = int(row["success_rows"]) - int(concept["success_rows"])
        row["success_rows_delta_vs_open3dsg_vocab"] = int(row["success_rows"]) - int(open3dsg_vocab["success_rows"])
        row["success_rate_delta_vs_h001"] = round(float(row["success_rate"]) - float(h001["success_rate"]), 6)
        row["success_rate_delta_vs_conceptgraphs"] = round(float(row["success_rate"]) - float(concept["success_rate"]), 6)
        row["success_rate_delta_vs_open3dsg_vocab"] = round(float(row["success_rate"]) - float(open3dsg_vocab["success_rate"]), 6)
    return rows


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Row | Source | Role | Success | Rate | ExpectedSearchCost | AttemptSPL | Delta vs H001 | Include |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["paper_label"],
                    row["source"],
                    row["paper_table_role"],
                    f"{row['success_rows']} / {row['rows']}",
                    f"{float(row['success_rate']):.6f}",
                    f"{float(row['mean_expected_search_cost']):.6f}",
                    f"{float(row['mean_attempt_spl_proxy']):.6f}",
                    f"{int(row['success_rows_delta_vs_h001']):+d}",
                    str(row["include_in_main_table"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def claim_rows(rows: list[dict[str, Any]], coverage: dict[str, Any]) -> list[dict[str, Any]]:
    by_policy = {row["policy"]: row for row in rows}
    h001 = by_policy[H001]
    context = by_policy[CONTEXT_AGNOSTIC]
    open3dsg_primary = by_policy[OPEN3DSG_PRIMARY]
    open3dsg_vocab = by_policy[OPEN3DSG_VOCAB]
    concept = by_policy[CONCEPTGRAPHS]
    return [
        {
            "claim_id": "C-M65-001",
            "claim_type": "allowed_main_table_row",
            "claim": "`Open3DSG` predicted-vocabulary adapter can be included as a bounded external scene-graph baseline row.",
            "status": "ready_with_adapter_boundary",
            "evidence": {
                "open3dsg_vocab_success": open3dsg_vocab["success_rows"],
                "open3dsg_primary_success": open3dsg_primary["success_rows"],
                "conceptgraphs_success": concept["success_rows"],
                "query_rows": coverage["query_rows"],
            },
            "allowed_wording": "`Open3DSG` with a leakage-safe predicted-vocabulary adapter reaches 144/195 strict bbox top5 on the shared proxy-search denominator.",
            "forbidden_wording": "`Open3DSG` itself solves the open-vocabulary robustness setting, or the adapter is our core method contribution.",
            "paper_table_action": "include_main_table_with_adapter_label",
        },
        {
            "claim_id": "C-M65-002",
            "claim_type": "allowed_main",
            "claim": "H001 remains stronger than the adapted `Open3DSG` row on the M38 heldout proxy-search denominator.",
            "status": "ready_with_proxy_boundary",
            "evidence": {
                "h001_success": h001["success_rows"],
                "open3dsg_vocab_success": open3dsg_vocab["success_rows"],
                "h001_minus_open3dsg_vocab_success_rows": int(h001["success_rows"]) - int(open3dsg_vocab["success_rows"]),
                "query_rows": coverage["query_rows"],
            },
            "allowed_wording": "H001 improves proxy-search success over both `ConceptGraphs` and the bounded `Open3DSG` vocabulary-adapter row.",
            "forbidden_wording": "H001 is a better general open-vocabulary mapper than `Open3DSG`.",
            "paper_table_action": "use_as_external_baseline_pressure",
        },
        {
            "claim_id": "C-M65-003",
            "claim_type": "allowed_secondary",
            "claim": "Human intent is reflected as structured task context, but remains a secondary ablation in E005.",
            "status": "secondary_ablation_only",
            "evidence": {
                "task_context_policy": H001,
                "h001_success": h001["success_rows"],
                "context_agnostic_success": context["success_rows"],
                "h001_minus_context_agnostic_success_rows": int(h001["success_rows"]) - int(context["success_rows"]),
                "human_task_context_main_claim_ready": coverage["human_task_context_main_claim_ready"],
            },
            "allowed_wording": "Structured task context is used as a condition for memory trust and re-observation decisions.",
            "forbidden_wording": "The paper's main contribution is human intent understanding or natural-language intent parsing.",
            "paper_table_action": "keep_context_agnostic_ablation_in_main_or_supplement",
        },
        {
            "claim_id": "C-M65-004",
            "claim_type": "blocked",
            "claim": "Final real RGB-D/open-vocabulary robustness.",
            "status": "blocked",
            "evidence": {
                "open3dsg_vocab_ready": True,
                "conceptgraphs_ready": True,
                "real_rgbd_open_vocab_robustness_ready": coverage["real_rgbd_open_vocab_robustness_ready"],
            },
            "allowed_wording": "M64 improves the external scene-graph baseline table under a proxy-search denominator.",
            "forbidden_wording": "M64 proves final real RGB-D/open-vocabulary robustness.",
            "paper_table_action": "do_not_promote_to_final_robustness_claim",
        },
        {
            "claim_id": "C-M65-005",
            "claim_type": "blocked",
            "claim": "Real navigation `SR` / `SPL` improvement.",
            "status": "blocked",
            "evidence": {
                "real_navigation_sr_spl_ready": coverage["real_navigation_sr_spl_ready"],
                "current_metrics": ["ExpectedSearchCost", "AttemptSPL"],
            },
            "allowed_wording": "Current navigation evidence is a proxy bridge.",
            "forbidden_wording": "The method improves real navigation `SR` / `SPL`.",
            "paper_table_action": "keep_navigation_claim_out",
        },
    ]


def build_report(coverage: dict[str, Any], rows: list[dict[str, Any]], claims: list[dict[str, Any]]) -> str:
    human_claim = next(row for row in claims if row["claim_id"] == "C-M65-003")
    lines = [
        "# E005-M65 Open3DSG Table Integration",
        "",
        "## Facts",
        "",
        f"- Status: `{coverage['status']}`.",
        f"- Query denominator rows: {coverage['query_rows']}.",
        f"- `Open3DSG` primary-label strict: {coverage['open3dsg_primary_success_rows']} / {coverage['query_rows']}.",
        f"- `Open3DSG` predicted-vocabulary strict: {coverage['open3dsg_vocab_success_rows']} / {coverage['query_rows']}.",
        f"- `ConceptGraphs` strict: {coverage['conceptgraphs_success_rows']} / {coverage['query_rows']}.",
        f"- H001 strict proxy success: {coverage['h001_success_rows']} / {coverage['query_rows']}.",
        "",
        "## Proposed Paper Table",
        "",
        markdown_table(rows),
        "## Paper Claims",
        "",
        "- Include `Open3DSG` predicted-vocabulary adapter as a bounded external scene-graph baseline row.",
        "- Do not present the `Open3DSG` vocabulary adapter as the method contribution.",
        "- Keep final real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` blocked.",
        "",
        "## Human Intent",
        "",
        "- E005 reflects human intent only through structured `task_context_id` in H001 memory-trust / re-observation policies.",
        f"- H001 vs context-agnostic gain is {human_claim['evidence']['h001_minus_context_agnostic_success_rows']} success row on this denominator.",
        "- Therefore human intent remains a secondary ablation, not the main E005 contribution.",
        "",
        "## Agent Inference",
        "",
        "- M64 strengthens external baseline rigor because H001 is compared against both `ConceptGraphs` and a stronger `Open3DSG` adapter row.",
        "- The paper should frame this as semantic memory decision evidence, not as an open-vocabulary mapping architecture claim.",
        "",
        "## Next",
        "",
        f"- {coverage['next_recommended_unit']}.",
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m49 = read_json(M49_METRICS)
    m52 = read_json(M52_METRICS)
    m54 = read_json(M54_COVERAGE)
    m60 = read_json(M60_METRICS)
    m64 = read_json(M64_METRICS)
    m64_coverage = read_json(M64_COVERAGE)

    rows = [
        table_row(
            source="H001",
            policy=STATIC,
            label="Static stale memory",
            role="memory_ablation",
            metric_payload=m52,
            note="naive old-memory baseline",
            include_in_main_table=True,
        ),
        table_row(
            source="H001",
            policy=DETECTOR_TOP5,
            label="Detector confidence top-5",
            role="detector_baseline",
            metric_payload=m52,
            note="detector-only candidate ranking baseline",
            include_in_main_table=True,
        ),
        table_row(
            source="ConceptGraphs",
            policy=CONCEPTGRAPHS,
            label="ConceptGraphs-only map retrieval",
            role="external_map_baseline",
            metric_payload=m49,
            note="converted positive external mapping baseline",
            include_in_main_table=True,
        ),
        table_row(
            source="Open3DSG",
            policy=OPEN3DSG_PRIMARY,
            label="Open3DSG primary-label adapter",
            role="external_scene_graph_diagnostic",
            metric_payload=m60,
            note="valid but weak primary-label adapter; include in supplement/failure row",
            include_in_main_table=False,
        ),
        table_row(
            source="Open3DSG",
            policy=OPEN3DSG_VOCAB,
            label="Open3DSG predicted-vocabulary adapter",
            role="external_scene_graph_baseline_bounded_adapter",
            metric_payload=m64,
            note="leakage-safe bounded adapter row",
            include_in_main_table=True,
        ),
        table_row(
            source="H001",
            policy=CONTEXT_AGNOSTIC,
            label="Context-agnostic memory trust + re-observation",
            role="memory_ablation",
            metric_payload=m52,
            note="tests whether task context is the main driver",
            include_in_main_table=True,
        ),
        table_row(
            source="H001",
            policy=H001,
            label="H001 task-conditioned memory trust + bounded re-observation",
            role="main_method",
            metric_payload=m52,
            note="main method row",
            include_in_main_table=True,
        ),
    ]
    rows = add_deltas(rows)

    by_policy = {row["policy"]: row for row in rows}
    coverage = {
        "status": "e005_m65_open3dsg_table_integration_ready",
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_dir": str(OUT_DIR),
        "query_rows": int(by_policy[H001]["rows"]),
        "h001_success_rows": int(by_policy[H001]["success_rows"]),
        "context_agnostic_success_rows": int(by_policy[CONTEXT_AGNOSTIC]["success_rows"]),
        "conceptgraphs_success_rows": int(by_policy[CONCEPTGRAPHS]["success_rows"]),
        "open3dsg_primary_success_rows": int(by_policy[OPEN3DSG_PRIMARY]["success_rows"]),
        "open3dsg_vocab_success_rows": int(by_policy[OPEN3DSG_VOCAB]["success_rows"]),
        "open3dsg_vocab_relaxed_success_rows": int(metric("Open3DSG", OPEN3DSG_VOCAB_RELAXED, m64)["query_bridge_success_rows"]),
        "h001_minus_open3dsg_vocab_success_rows": int(by_policy[H001]["success_rows"]) - int(by_policy[OPEN3DSG_VOCAB]["success_rows"]),
        "open3dsg_vocab_minus_conceptgraphs_success_rows": int(by_policy[OPEN3DSG_VOCAB]["success_rows"]) - int(by_policy[CONCEPTGRAPHS]["success_rows"]),
        "h001_minus_context_agnostic_success_rows": int(by_policy[H001]["success_rows"]) - int(by_policy[CONTEXT_AGNOSTIC]["success_rows"]),
        "open3dsg_vocab_main_table_include": True,
        "open3dsg_primary_main_table_include": False,
        "human_intent_reflected_as_structured_task_context": True,
        "human_intent_main_claim_ready": False,
        "human_task_context_main_claim_ready": bool(m54.get("human_task_context_main_claim_ready", False)),
        "real_rgbd_open_vocab_robustness_ready": False,
        "real_navigation_sr_spl_ready": False,
        "m64_leakage_audit_pass": bool(
            m64_coverage.get("uses_gt_object_label") is False
            and m64_coverage.get("uses_id2name_label") is False
            and m64_coverage.get("uses_target_uid_before_ranking") is False
            and m64_coverage.get("uses_target_geometry_before_ranking") is False
        ),
        "next_recommended_unit": "E005-M66 external-baseline table failure-boundary rows or E006 human-context upgrade decision",
    }
    claims = claim_rows(rows, coverage)
    write_json(OUT_DIR / "coverage.json", coverage)
    write_jsonl(OUT_DIR / "paper_table_rows.jsonl", rows)
    write_csv(OUT_DIR / "paper_table_rows.csv", rows)
    write_text(OUT_DIR / "paper_table.md", markdown_table(rows))
    write_jsonl(OUT_DIR / "claim_boundary_rows.jsonl", claims)
    write_text(OUT_DIR / "report.md", build_report(coverage, rows, claims))
    return coverage


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
