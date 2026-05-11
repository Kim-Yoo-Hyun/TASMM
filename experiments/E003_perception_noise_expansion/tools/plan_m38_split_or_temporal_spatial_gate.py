#!/usr/bin/env python3
"""Plan E003-M38 stronger split or temporal-spatial suppression gate."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from run_m36_recall_preserving_suppression_sweep import (
    clean_proposal,
    evaluate_policy,
    rank,
    safe_rate,
    select_best,
    slim_policy,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_M17_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M17_real_proposal_denominator_staging_v0"
DEFAULT_M33_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M33_scaled_pre_cap_policy_docker_rerun_v0"
DEFAULT_M37_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M37_suppression_split_validation_v0"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M38_split_or_temporal_spatial_gate_v0"
M38_VERSION = "e003_m38_split_or_temporal_spatial_gate_v0"
RADII_M = [0.75, 1.0, 1.5, 2.0]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def policy_id_float(value: float) -> str:
    return str(value).replace(".", "p")


def rows_for_scans(rows: list[dict[str, Any]], scans: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("scan_id")) in scans]


def centroid(row: dict[str, Any]) -> tuple[float, float, float]:
    values = row.get("centroid_world_m") or [0.0, 0.0, 0.0]
    return float(values[0]), float(values[1]), float(values[2])


def distance_m(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax, ay, az = centroid(a)
    bx, by, bz = centroid(b)
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)


def frame_ids(row: dict[str, Any]) -> set[str]:
    values = row.get("frame_ids") or []
    return {str(value) for value in values}


def add_support_features(rows: list[dict[str, Any]], radii_m: list[float]) -> list[dict[str, Any]]:
    enriched = [dict(row) for row in rows]
    max_radius = max(radii_m)
    spatial_counts = [{radius: 0 for radius in radii_m} for _ in enriched]
    temporal_frame_sets = [{radius: set() for radius in radii_m} for _ in enriched]

    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, row in enumerate(enriched):
        grouped[(str(row["scan_id"]), str(row["label_canonical"]))].append(idx)

    for indices in grouped.values():
        for pos, i in enumerate(indices):
            for j in indices[pos + 1 :]:
                d_m = distance_m(enriched[i], enriched[j])
                if d_m > max_radius:
                    continue
                frames_i = frame_ids(enriched[i])
                frames_j = frame_ids(enriched[j])
                for radius in radii_m:
                    if d_m <= radius:
                        spatial_counts[i][radius] += 1
                        spatial_counts[j][radius] += 1
                        temporal_frame_sets[i][radius].update(frames_j - frames_i)
                        temporal_frame_sets[j][radius].update(frames_i - frames_j)

    for idx, row in enumerate(enriched):
        for radius in radii_m:
            suffix = policy_id_float(radius)
            row[f"spatial_neighbor_count_r{suffix}m"] = spatial_counts[idx][radius]
            row[f"temporal_neighbor_frame_count_r{suffix}m"] = len(temporal_frame_sets[idx][radius])
    return enriched


def split_balance_score(dev_scans: set[str], scan_rows: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    stats = {str(row["scan_id"]): row for row in scan_rows}
    keys = ["evaluation_target_rows", "matched_proposal_rows", "proposal_rows", "visible_proxy_target_rows"]
    totals = {key: sum(int(row[key]) for row in scan_rows) for key in keys}
    dev_totals = {key: sum(int(stats[scan][key]) for scan in dev_scans) for key in keys}
    score = sum(abs((safe_rate(dev_totals[key], totals[key]) or 0.0) - 0.5) for key in keys)
    return score, {
        "dev_totals": dev_totals,
        "heldout_totals": {key: totals[key] - dev_totals[key] for key in keys},
        "totals": totals,
    }


def build_scan_rows(
    clean_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scans = sorted({str(row["scan_id"]) for row in clean_rows})
    proposal_count = Counter(str(row["scan_id"]) for row in clean_rows)
    matched_count = Counter(str(row["scan_id"]) for row in matched_rows if row.get("match_status") == "matched")
    target_count = Counter(
        str(row["scan_id"])
        for row in eval_targets
        if row.get("evaluation_target_enabled")
    )
    visible_count = Counter(
        str(row["scan_id"])
        for row in visibility_rows
        if row.get("depth_consistent_visible_proxy")
    )
    matched_labels: dict[str, set[str]] = defaultdict(set)
    for row in matched_rows:
        if row.get("match_status") == "matched":
            matched_labels[str(row["scan_id"])].add(str(row["label_canonical"]))
    return [
        {
            "evaluation_target_rows": int(target_count[scan]),
            "matched_label_count": len(matched_labels[scan]),
            "matched_proposal_rows": int(matched_count[scan]),
            "proposal_rows": int(proposal_count[scan]),
            "scan_id": scan,
            "visible_proxy_target_rows": int(visible_count[scan]),
        }
        for scan in scans
    ]


def enumerate_split_feasibility(
    *,
    scan_rows: list[dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    eval_targets: list[dict[str, Any]],
    min_dev_scans: int,
    min_heldout_scans: int,
) -> list[dict[str, Any]]:
    scans = sorted(str(row["scan_id"]) for row in scan_rows)
    rows: list[dict[str, Any]] = []
    for dev_count in range(min_dev_scans, len(scans) - min_heldout_scans + 1):
        for combo in itertools.combinations(scans, dev_count):
            dev_scans = set(combo)
            heldout_scans = set(scans) - dev_scans
            dev_matched_labels = {
                str(row["label_canonical"])
                for row in matched_rows
                if str(row.get("scan_id")) in dev_scans and row.get("match_status") == "matched"
            }
            heldout_target_by_label = Counter(
                str(row["label_canonical"])
                for row in eval_targets
                if str(row.get("scan_id")) in heldout_scans and row.get("evaluation_target_enabled")
            )
            uncovered_labels = sorted(label for label in heldout_target_by_label if label not in dev_matched_labels)
            balance_score, balance = split_balance_score(dev_scans, scan_rows)
            rows.append(
                {
                    "balance_score": balance_score,
                    "dev_scan_count": len(dev_scans),
                    "dev_scans": sorted(dev_scans),
                    "heldout_scan_count": len(heldout_scans),
                    "heldout_scans": sorted(heldout_scans),
                    "heldout_target_rows": sum(heldout_target_by_label.values()),
                    "uncovered_heldout_target_label_count": len(uncovered_labels),
                    "uncovered_heldout_target_labels": uncovered_labels,
                    "uncovered_heldout_target_rows": sum(heldout_target_by_label[label] for label in uncovered_labels),
                    **balance,
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            int(row["uncovered_heldout_target_label_count"]),
            int(row["uncovered_heldout_target_rows"]),
            abs(int(row["dev_scan_count"]) - int(row["heldout_scan_count"])),
            float(row["balance_score"]),
            str(row["dev_scans"]),
        ),
    )


def build_support_policy_specs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for family, feature_prefix in [
        ("spatial_support_or_rank_guard", "spatial_neighbor_count"),
        ("temporal_support_or_rank_guard", "temporal_neighbor_frame_count"),
    ]:
        for radius in RADII_M:
            suffix = policy_id_float(radius)
            feature_key = f"{feature_prefix}_r{suffix}m"
            for rank_guard in [0, 1, 2, 4, 6, 8, 10, 12, 16, 20]:
                for min_support in [1, 2, 3]:
                    policy_id = (
                        f"{family}_r{suffix}m_min{min_support}_rank_guard_le_{rank_guard}"
                    )
                    filtered = [
                        row
                        for row in rows
                        if rank(row) <= rank_guard or int(row.get(feature_key, 0) or 0) >= min_support
                    ]
                    specs.append(
                        {
                            "clean_rows": filtered,
                            "description": (
                                f"Keep if rank <= {rank_guard} or {feature_key} >= {min_support}."
                            ),
                            "family": family,
                            "id": policy_id,
                            "params": {
                                "feature_key": feature_key,
                                "min_support": min_support,
                                "radius_m": radius,
                                "rank_guard": rank_guard,
                            },
                        }
                    )
    return specs


def apply_support_policy(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    feature_key = str(params["feature_key"])
    rank_guard = int(params["rank_guard"])
    min_support = int(params["min_support"])
    return [
        row
        for row in rows
        if rank(row) <= rank_guard or int(row.get(feature_key, 0) or 0) >= min_support
    ]


def evaluate_support_sweep(
    *,
    train_rows: list[dict[str, Any]],
    heldout_rows: list[dict[str, Any]],
    train_targets: list[dict[str, Any]],
    heldout_targets: list[dict[str, Any]],
    train_visibility: list[dict[str, Any]],
    heldout_visibility: list[dict[str, Any]],
    threshold_m: float,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    train_baseline, _, _, _ = evaluate_policy(
        clean_rows=train_rows,
        eval_targets=train_targets,
        visibility_rows=train_visibility,
        threshold_m=threshold_m,
        policy_id="m37_dev_baseline",
        policy_family="baseline",
        deployability="baseline",
        description="M37 dev split baseline without additional support suppression.",
        baseline_metrics=None,
    )
    train_baseline.update(
        {
            "false_positive_reduction_vs_m33": 0,
            "matched_target_delta_vs_m33": 0,
            "matched_target_retention_vs_m33": 1.0,
            "phase": "dev",
            "precision_delta_vs_m33": 0.0,
            "visible_proxy_recall_delta_vs_m33": 0.0,
        }
    )
    heldout_baseline, _, _, _ = evaluate_policy(
        clean_rows=heldout_rows,
        eval_targets=heldout_targets,
        visibility_rows=heldout_visibility,
        threshold_m=threshold_m,
        policy_id="m37_heldout_baseline",
        policy_family="baseline",
        deployability="baseline",
        description="M37 heldout baseline without additional support suppression.",
        baseline_metrics=None,
    )
    heldout_baseline.update(
        {
            "false_positive_reduction_vs_m33": 0,
            "matched_target_delta_vs_m33": 0,
            "matched_target_retention_vs_m33": 1.0,
            "phase": "heldout",
            "precision_delta_vs_m33": 0.0,
            "visible_proxy_recall_delta_vs_m33": 0.0,
        }
    )

    policy_rows = [train_baseline, heldout_baseline]
    train_candidates: list[dict[str, Any]] = []
    for spec in build_support_policy_specs(train_rows):
        row, _, _, _ = evaluate_policy(
            clean_rows=spec["clean_rows"],
            eval_targets=train_targets,
            visibility_rows=train_visibility,
            threshold_m=threshold_m,
            policy_id=str(spec["id"]),
            policy_family=str(spec["family"]),
            deployability="candidate_policy_selected_on_dev",
            description=str(spec["description"]),
            baseline_metrics=train_baseline,
            policy_params=spec["params"],
        )
        row["phase"] = "dev"
        train_candidates.append(row)
    policy_rows.extend(train_candidates)
    selected_dev = select_best(train_candidates, min_retention=0.95)

    heldout_selected = None
    if selected_dev:
        heldout_selected, _, _, _ = evaluate_policy(
            clean_rows=apply_support_policy(heldout_rows, selected_dev["policy_params"]),
            eval_targets=heldout_targets,
            visibility_rows=heldout_visibility,
            threshold_m=threshold_m,
            policy_id=f"{selected_dev['policy_id']}_selected_on_dev",
            policy_family=str(selected_dev["policy_family"]),
            deployability="candidate_policy_selected_on_dev_applied_to_heldout",
            description="Best support policy selected on dev and applied to heldout.",
            baseline_metrics=heldout_baseline,
            policy_params=selected_dev["policy_params"],
        )
        heldout_selected["phase"] = "heldout"
        policy_rows.append(heldout_selected)

    heldout_candidates: list[dict[str, Any]] = []
    for spec in build_support_policy_specs(heldout_rows):
        row, _, _, _ = evaluate_policy(
            clean_rows=spec["clean_rows"],
            eval_targets=heldout_targets,
            visibility_rows=heldout_visibility,
            threshold_m=threshold_m,
            policy_id=str(spec["id"]),
            policy_family=str(spec["family"]),
            deployability="diagnostic_heldout_oracle_not_deployable",
            description=str(spec["description"]),
            baseline_metrics=heldout_baseline,
            policy_params=spec["params"],
        )
        row["phase"] = "heldout_oracle"
        heldout_candidates.append(row)
    heldout_oracle = select_best(heldout_candidates, min_retention=0.95)
    if heldout_oracle:
        policy_rows.append(heldout_oracle)

    return policy_rows, train_baseline, heldout_baseline, selected_dev, heldout_selected, heldout_oracle


def support_feature_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for radius in RADII_M:
        suffix = policy_id_float(radius)
        for feature_key in [
            f"spatial_neighbor_count_r{suffix}m",
            f"temporal_neighbor_frame_count_r{suffix}m",
        ]:
            buckets: dict[str, Counter] = defaultdict(Counter)
            for row in rows:
                value = int(row.get(feature_key, 0) or 0)
                bucket = "0" if value == 0 else "1" if value == 1 else "2plus"
                status = "matched" if row.get("match_status") == "matched" else "false_positive"
                buckets[bucket][status] += 1
            for bucket, counts in sorted(buckets.items()):
                total = counts["matched"] + counts["false_positive"]
                output.append(
                    {
                        "bucket": bucket,
                        "false_positive_rows": int(counts["false_positive"]),
                        "feature_key": feature_key,
                        "matched_rows": int(counts["matched"]),
                        "matched_rate": safe_rate(counts["matched"], total),
                        "proposal_rows": int(total),
                    }
                )
    return output


def build_report(coverage: dict[str, Any]) -> str:
    selected = coverage.get("selected_support_policy_heldout")
    oracle = coverage.get("heldout_oracle_support_policy")
    best_split = coverage.get("best_split_feasibility")
    return "\n".join(
        [
            "# E003-M38 Split Or Temporal-Spatial Gate",
            "",
            "## Status",
            "",
            str(coverage["status"]),
            "",
            "## 사실",
            "",
            f"- Split feasibility rows: {coverage['split_feasibility_rows']}",
            f"- Best split uncovered heldout target label count: {best_split['uncovered_heldout_target_label_count']}",
            f"- Best split uncovered heldout target rows: {best_split['uncovered_heldout_target_rows']}",
            f"- Stronger split feasible with current 8 scans: {coverage['stronger_split_feasible_with_current_scans']}",
            f"- Support policy rows: {coverage['support_policy_rows']}",
            f"- Selected dev support policy: `{coverage['selected_support_policy_dev']['policy_id'] if coverage.get('selected_support_policy_dev') else None}`",
            f"- Selected heldout matched targets: {selected['matched_target_rows'] if selected else None}",
            f"- Selected heldout false-positive rows: {selected['false_positive_proposal_rows'] if selected else None}",
            f"- Selected heldout retention: {selected['matched_target_retention_vs_m33'] if selected else None}",
            f"- Selected heldout precision: {selected['proposal_precision'] if selected else None}",
            f"- Heldout oracle support policy: `{oracle['policy_id'] if oracle else None}`",
            f"- Heldout oracle matched targets: {oracle['matched_target_rows'] if oracle else None}",
            f"- Heldout oracle false-positive rows: {oracle['false_positive_proposal_rows'] if oracle else None}",
            f"- Heldout oracle precision: {oracle['proposal_precision'] if oracle else None}",
            f"- Selected route: `{coverage['selected_route']}`",
            f"- Runner integration recommended: {coverage['runner_integration_recommended']}",
            f"- Paper-table command ready: {coverage['paper_table_command_ready']}",
            f"- Real RGB-D/open-vocabulary claim ready: {coverage['real_rgbd_or_open_vocab_claim_ready']}",
            "",
            "## 논문 주장",
            "",
            "- E003-M38 can support a route decision after M37 heldout transfer failure.",
            "- E003-M38 does not support a final real RGB-D/open-vocabulary robustness claim.",
            "- E003-M38 does not support Docker runner integration unless heldout support-policy retention and false-positive reduction both pass.",
            "",
            "## 에이전트 추론",
            "",
            "- If no split covers heldout target labels with dev matched examples, stronger split design is not enough with the current 8-scan artifact.",
            "- If support-policy oracle is better than dev-selected transfer, the next route should instrument richer temporal/spatial evidence rather than deploy the current post-hoc filter.",
            "",
            "## 사용자 판단 필요",
            "",
            f"- None for E003-M38. Next recommended unit: `{coverage['next_recommended_unit']}`.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m17-dir", default=DEFAULT_M17_DIR, type=Path)
    parser.add_argument("--m33-dir", default=DEFAULT_M33_DIR, type=Path)
    parser.add_argument("--m37-dir", default=DEFAULT_M37_DIR, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, type=Path)
    parser.add_argument("--match-distance-threshold-m", default=1.0, type=float)
    args = parser.parse_args()

    matched_rows = load_jsonl(args.m33_dir / "match_preserving_calibration" / "selected_matched_proposals.jsonl")
    enriched_matched_rows = add_support_features([dict(row) for row in matched_rows], RADII_M)
    clean_rows = [clean_proposal(row) for row in enriched_matched_rows]
    all_targets = load_jsonl(args.m17_dir / "real_proposal_object_targets.jsonl")
    visibility_rows = load_jsonl(args.m33_dir / "visibility_denominator" / "target_denominator_rows.jsonl")
    split_plan = load_json(args.m37_dir / "split_plan.json")

    evaluated_scans = sorted({str(row["scan_id"]) for row in clean_rows})
    eval_targets = [
        row
        for row in all_targets
        if row.get("evaluation_target_enabled") and str(row["scan_id"]) in evaluated_scans
    ]
    scan_rows = build_scan_rows(clean_rows, matched_rows, eval_targets, visibility_rows)
    split_rows = enumerate_split_feasibility(
        scan_rows=scan_rows,
        matched_rows=matched_rows,
        eval_targets=eval_targets,
        min_dev_scans=3,
        min_heldout_scans=2,
    )
    best_split = split_rows[0]

    dev_scans = set(split_plan["split_summary"]["dev_scans"])
    heldout_scans = set(split_plan["split_summary"]["heldout_scans"])
    support_rows, train_baseline, heldout_baseline, selected_dev, heldout_selected, heldout_oracle = evaluate_support_sweep(
        train_rows=rows_for_scans(clean_rows, dev_scans),
        heldout_rows=rows_for_scans(clean_rows, heldout_scans),
        train_targets=rows_for_scans(eval_targets, dev_scans),
        heldout_targets=rows_for_scans(eval_targets, heldout_scans),
        train_visibility=rows_for_scans(visibility_rows, dev_scans),
        heldout_visibility=rows_for_scans(visibility_rows, heldout_scans),
        threshold_m=args.match_distance_threshold_m,
    )

    selected_fp_reduction_rate = (
        safe_rate(heldout_selected["false_positive_reduction_vs_m33"], heldout_baseline["false_positive_proposal_rows"])
        if heldout_selected
        else None
    )
    support_transfer_pass = bool(
        heldout_selected
        and (heldout_selected.get("matched_target_retention_vs_m33") or 0.0) >= 0.95
        and (selected_fp_reduction_rate or 0.0) >= 0.10
    )
    stronger_split_feasible = int(best_split["uncovered_heldout_target_label_count"]) == 0

    if support_transfer_pass:
        selected_route = "temporal_spatial_support_runner_integration_candidate"
        next_unit = "E003-M39 temporal-spatial support runner integration gate"
        runner_integration = True
    elif not stronger_split_feasible:
        selected_route = "temporal_spatial_evidence_instrumentation_required"
        next_unit = "E003-M39 temporal-spatial support instrumentation gate"
        runner_integration = False
    else:
        selected_route = "stronger_split_validation_required"
        next_unit = "E003-M39 stronger split validation"
        runner_integration = False

    coverage = {
        "best_split_feasibility": {
            key: value
            for key, value in best_split.items()
            if key
            in {
                "balance_score",
                "dev_scan_count",
                "dev_scans",
                "heldout_scan_count",
                "heldout_scans",
                "heldout_target_rows",
                "uncovered_heldout_target_label_count",
                "uncovered_heldout_target_labels",
                "uncovered_heldout_target_rows",
            }
        },
        "current_m37_dev_scans": sorted(dev_scans),
        "current_m37_heldout_scans": sorted(heldout_scans),
        "heldout_baseline_policy": slim_policy(heldout_baseline),
        "heldout_oracle_support_policy": slim_policy(heldout_oracle),
        "m38_version": M38_VERSION,
        "match_distance_threshold_m": args.match_distance_threshold_m,
        "next_recommended_unit": next_unit,
        "paper_table_command_ready": False,
        "real_rgbd_or_open_vocab_claim_ready": False,
        "runner_integration_recommended": runner_integration,
        "selected_route": selected_route,
        "selected_support_fp_reduction_rate": selected_fp_reduction_rate,
        "selected_support_policy_dev": slim_policy(selected_dev),
        "selected_support_policy_heldout": slim_policy(heldout_selected),
        "split_feasibility_rows": len(split_rows),
        "status": "split_or_temporal_spatial_gate_ready",
        "stronger_split_feasible_with_current_scans": stronger_split_feasible,
        "support_feature_rows": len(support_feature_summary(enriched_matched_rows)),
        "support_policy_rows": len(support_rows),
        "support_transfer_pass": support_transfer_pass,
        "train_baseline_policy": slim_policy(train_baseline),
    }

    write_jsonl(args.out_dir / "split_feasibility_rows.jsonl", split_rows)
    write_jsonl(args.out_dir / "support_policy_rows.jsonl", support_rows)
    write_jsonl(args.out_dir / "support_feature_rows.jsonl", support_feature_summary(enriched_matched_rows))
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
