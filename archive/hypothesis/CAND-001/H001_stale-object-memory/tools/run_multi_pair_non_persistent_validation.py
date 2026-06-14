#!/usr/bin/env python3
"""Run H001 multi-pair non-persistent validation.

This is a hypothesis-stage gate. It evaluates locally available 3RScan
reference-rescan semantic pairs and reuses the non-persistent ranking features
without using persistent cross-scan object-id anchors for ranking.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import run_non_persistent_anchor_smoke as single


H001_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(__file__).resolve().parents[4] / "local_dataset"
DEFAULT_OUT_DIR = H001_ROOT / "artifacts" / "multi_pair_non_persistent_validation"
DEFAULT_STAGING_TARGETS = H001_ROOT / "artifacts" / "rescan_staging_targets" / "targets.jsonl"
POLICIES = [
    "scene_aligned_static_map",
    "staleness_only",
    "label_nearest_current_observation",
    "label_top3_current_observation",
    "non_persistent_anchor_v0",
    "oracle_current_pose",
]


def row_uid(row: dict) -> str:
    return "{ref}->{rescan}:{obj}".format(
        ref=row["reference_scan_id"],
        rescan=row["rescan_id"],
        obj=row["object_instance_id_ref"],
    )


def pair_uid(reference_scan_id: str, rescan_id: str) -> str:
    return f"{reference_scan_id}->{rescan_id}"


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def semseg_path(dataset_root: Path, scan_id: str) -> Path:
    return dataset_root / "3RScan" / "scans" / scan_id / "semseg.v2.json"


def load_local_ready_pairs(dataset_root: Path) -> tuple[list[dict], dict]:
    metadata = single.load_json(dataset_root / "3RScan" / "files" / "3RScan.json")
    pairs = []
    scanned = 0
    reference_semseg = 0
    for group in metadata:
        reference_scan_id = group.get("reference")
        if not reference_scan_id:
            continue
        ref_has_semseg = semseg_path(dataset_root, reference_scan_id).is_file()
        for pair_metadata in group.get("scans", []):
            scanned += 1
            rescan_id = pair_metadata.get("reference")
            if ref_has_semseg:
                reference_semseg += 1
            if not ref_has_semseg or not semseg_path(dataset_root, rescan_id).is_file():
                continue
            pairs.append(
                {
                    "reference_scan_id": reference_scan_id,
                    "rescan_id": rescan_id,
                    "pair_metadata": pair_metadata,
                }
            )
    coverage = {
        "metadata_pairs_scanned": scanned,
        "pairs_with_reference_semseg": reference_semseg,
        "local_ready_pair_candidates": len(pairs),
    }
    return pairs, coverage


def transform_errors(ref_centroid: list[float], target_centroid: list[float], pair_metadata: dict, item: dict) -> dict:
    scene_transform = pair_metadata["transform"]
    scene_inverse = single.invert_rigid_row_transform(scene_transform)
    object_transform = item["transform"]
    object_inverse = single.invert_rigid_row_transform(object_transform)
    transformed = {
        "object_direct_error_m": single.transform_point_row(ref_centroid, object_transform),
        "object_inverse_error_m": single.transform_point_row(ref_centroid, object_inverse),
        "scene_direct_error_m": single.transform_point_row(ref_centroid, scene_transform),
        "scene_inverse_error_m": single.transform_point_row(ref_centroid, scene_inverse),
    }
    return {
        key: single.point_distance(value, target_centroid)
        for key, value in transformed.items()
    }


def row_band(planar_displacement_m: float, significant_threshold_m: float, low_motion_threshold_m: float) -> str:
    if planar_displacement_m >= significant_threshold_m:
        return "significant_moved"
    if planar_displacement_m <= low_motion_threshold_m:
        return "low_motion_control"
    return "mid_motion_review"


def build_pair_rows(
    dataset_root: Path,
    reference_scan_id: str,
    rescan_id: str,
    pair_metadata: dict,
    geometry_threshold_m: float,
    significant_threshold_m: float,
    low_motion_threshold_m: float,
) -> tuple[list[dict], list[dict], dict]:
    ref_objects = single.load_semseg_objects(semseg_path(dataset_root, reference_scan_id))
    rescan_objects = single.load_semseg_objects(semseg_path(dataset_root, rescan_id))
    scene_inverse = single.invert_rigid_row_transform(pair_metadata["transform"])
    pair_rows = []
    query_rows = []
    for item in pair_metadata.get("rigid", []):
        ref_id = str(item["instance_reference"])
        rescan_obj_id = str(item["instance_rescan"])
        ref_obj = ref_objects.get(ref_id)
        rescan_obj = rescan_objects.get(rescan_obj_id)
        label_match = bool(ref_obj and rescan_obj and ref_obj["label"] == rescan_obj["label"])
        errors = {}
        best_candidate = None
        best_error = None
        old_scene_aligned = None
        scene_planar = None
        scene_error = None
        if ref_obj and rescan_obj:
            errors = transform_errors(ref_obj["centroid"], rescan_obj["centroid"], pair_metadata, item)
            best_candidate = min(errors, key=lambda key: errors[key])
            best_error = errors[best_candidate]
            old_scene_aligned = single.transform_point_row(ref_obj["centroid"], scene_inverse)
            scene_error = single.point_distance(old_scene_aligned, rescan_obj["centroid"])
            scene_planar = single.planar_distance(old_scene_aligned, rescan_obj["centroid"])
        row_geometry_valid = bool(label_match and best_error is not None and best_error <= geometry_threshold_m)
        base = {
            "pair_uid": pair_uid(reference_scan_id, rescan_id),
            "reference_scan_id": reference_scan_id,
            "rescan_id": rescan_id,
            "instance_reference": ref_id,
            "instance_rescan": rescan_obj_id,
            "ref_label": ref_obj.get("label") if ref_obj else None,
            "rescan_label": rescan_obj.get("label") if rescan_obj else None,
            "ref_geometry_join": ref_obj is not None,
            "rescan_geometry_join": rescan_obj is not None,
            "label_match": label_match,
            "row_geometry_valid": row_geometry_valid,
            "row_best_candidate": best_candidate,
            "row_geometry_error_m": single.round_or_none(best_error),
            "scene_aligned_static_error_m": single.round_or_none(scene_error),
            "scene_aligned_static_planar_error_m": single.round_or_none(scene_planar),
            **{key: single.round_or_none(value) for key, value in errors.items()},
        }
        pair_rows.append(base)
        if not row_geometry_valid:
            continue
        band = row_band(scene_planar, significant_threshold_m, low_motion_threshold_m)
        query_row = {
            "row_uid": f"{pair_uid(reference_scan_id, rescan_id)}:{ref_id}",
            "pair_uid": pair_uid(reference_scan_id, rescan_id),
            "episode_id": "h001_multi_pair_{ref}_{rescan}".format(
                ref=reference_scan_id[:8],
                rescan=rescan_id[:8],
            ),
            "reference_scan_id": reference_scan_id,
            "rescan_id": rescan_id,
            "object_instance_id_ref": ref_id,
            "object_instance_id_rescan": rescan_obj_id,
            "object_label": ref_obj["label"],
            "query": f"find the {ref_obj['label']}",
            "change_type": "rigid_moved",
            "row_geometry_valid": True,
            "row_geometry_error_m": best_error,
            "row_best_candidate": best_candidate,
            "old_scene_aligned_centroid": old_scene_aligned,
            "pair_current_centroid": rescan_obj["centroid"],
            "scene_aligned_static_error_m": scene_error,
            "scene_aligned_static_planar_error_m": scene_planar,
            "significant_moved": band == "significant_moved",
            "row_band": band,
            "expected_memory_state": "needs_reobservation"
            if band == "significant_moved"
            else "trusted_or_low_motion",
            "evaluation_scope": "moved_recovery_only",
            "old_memory_is_stale": band == "significant_moved",
        }
        query_rows.append(query_row)
    pair_summary = {
        "pair_uid": pair_uid(reference_scan_id, rescan_id),
        "reference_scan_id": reference_scan_id,
        "rescan_id": rescan_id,
        "metadata_rigid": len(pair_metadata.get("rigid", [])),
        "row_geometry_valid": sum(1 for row in pair_rows if row["row_geometry_valid"]),
        "query_rows": len(query_rows),
        "significant_moved_rows": sum(1 for row in query_rows if row["row_band"] == "significant_moved"),
        "low_motion_control_rows": sum(1 for row in query_rows if row["row_band"] == "low_motion_control"),
        "mid_motion_review_rows": sum(1 for row in query_rows if row["row_band"] == "mid_motion_review"),
    }
    return pair_rows, query_rows, pair_summary


def ranked_label_candidates(row: dict, object_rows: list[dict], rescan_objects: dict[str, dict]) -> list[dict]:
    ranked = []
    for rank, item in enumerate(
        sorted(
            object_rows,
            key=lambda candidate: (
                candidate["distance_to_old_scene_aligned_m"],
                int(candidate["candidate_instance_id"]),
            ),
        ),
        start=1,
    ):
        ranked.append(
            {
                **item,
                "label_rank": rank,
                "centroid": rescan_objects[item["candidate_instance_id"]]["centroid"],
            }
        )
    return ranked


def attach_pair_fields(rows: list[dict], query_row: dict) -> list[dict]:
    output = []
    for row in rows:
        output.append(
            {
                **row,
                "row_uid": query_row["row_uid"],
                "pair_uid": query_row["pair_uid"],
                "reference_scan_id": query_row["reference_scan_id"],
                "rescan_id": query_row["rescan_id"],
                "episode_id": query_row["episode_id"],
            }
        )
    return output


def predict_policy(
    policy: str,
    row: dict,
    label_ranked: list[dict],
    np_ranked: list[dict],
    success_threshold_m: float,
) -> dict:
    pred = single.predict(policy, row, label_ranked, np_ranked, success_threshold_m)
    if policy == "staleness_only" and not row["old_memory_is_stale"]:
        error = single.point_distance(row["old_scene_aligned_centroid"], row["pair_current_centroid"])
        exact = error <= success_threshold_m
        pred.update(
            {
                "memory_state": "trusted_or_low_motion",
                "action": "return_scene_aligned_old_location",
                "returns_old_location": True,
                "suppresses_old_location": False,
                "candidate_count": 1,
                "exact_recovery": exact,
                "candidate_recall_at_1": exact,
                "candidate_recall_at_3": exact,
                "candidate_recall_all": exact,
                "target_error_m": single.round_or_none(error),
            }
        )
    return pred


def summarize_policy(policy: str, predictions: list[dict], subset_name: str, subset_rows: list[dict]) -> dict:
    ids = {row["row_uid"] for row in subset_rows}
    items = [row for row in predictions if row["row_uid"] in ids and row["policy"] == policy]
    den = len(items)
    stale_items = [row for row in items if row["old_memory_is_stale"]]
    low_motion_items = [row for row in items if row.get("row_band") == "low_motion_control"]
    entropy_items = [row for row in items if row.get("candidate_entropy") is not None]
    search_items = [row for row in items if row.get("expected_search_cost_proxy") is not None]
    return {
        "policy": policy,
        "subset": subset_name,
        "rows": den,
        "stale_rows": len(stale_items),
        "low_motion_rows": len(low_motion_items),
        "suppresses_old_location_rate": single.safe_rate(
            sum(1 for row in items if row["suppresses_old_location"]), den
        ),
        "stale_old_location_false_positive_rate": single.safe_rate(
            sum(1 for row in stale_items if row["returns_old_location"] and not row["exact_recovery"]),
            len(stale_items),
        ),
        "exact_recovery_rate": single.safe_rate(sum(1 for row in items if row["exact_recovery"]), den),
        "candidate_recall_at_1": single.safe_rate(sum(1 for row in items if row["candidate_recall_at_1"]), den),
        "candidate_recall_at_3": single.safe_rate(sum(1 for row in items if row["candidate_recall_at_3"]), den),
        "candidate_recall_all": single.safe_rate(sum(1 for row in items if row["candidate_recall_all"]), den),
        "mean_candidate_count": single.round_or_none(
            sum(row["candidate_count"] for row in items) / den if den else None
        ),
        "uses_rescan_semseg_observation": any(row["uses_rescan_semseg_observation"] for row in items),
        "uses_exact_current_pose": any(row["uses_exact_current_pose"] for row in items),
        "low_motion_static_preserved_rate": single.safe_rate(
            sum(1 for row in low_motion_items if row["returns_old_location"] and row["exact_recovery"]),
            len(low_motion_items),
        ),
        "control_forced_reobservation_rate": single.safe_rate(
            sum(1 for row in low_motion_items if row["uses_rescan_semseg_observation"]),
            len(low_motion_items),
        ),
        "mean_candidate_entropy": single.round_or_none(
            sum(row["candidate_entropy"] for row in entropy_items) / len(entropy_items)
            if entropy_items
            else None
        ),
        "mean_expected_search_cost_proxy": single.round_or_none(
            sum(row["expected_search_cost_proxy"] for row in search_items) / len(search_items)
            if search_items
            else None
        ),
    }


def policy_metrics(predictions: list[dict], subset_name: str, subset_rows: list[dict]) -> dict:
    return {
        policy: summarize_policy(policy, predictions, subset_name, subset_rows)
        for policy in POLICIES
    }


def summarize_ablations(query_rows: list[dict], feature_rows_by_uid: dict[str, list[dict]]) -> dict:
    summary = {}
    significant_rows = [row for row in query_rows if row["row_band"] == "significant_moved"]
    for ablation in single.ABLATIONS:
        records = []
        for row in significant_rows:
            ranked = single.rank_candidates(feature_rows_by_uid.get(row["row_uid"], []), ablation)
            chosen = ranked[0] if ranked else None
            target = next((item for item in ranked if item["eval_is_target_instance"]), None)
            records.append(
                {
                    "row_uid": row["row_uid"],
                    "object_label": row["object_label"],
                    "candidate_count": row.get("same_label_candidate_count"),
                    "chosen_instance_id": chosen["candidate_instance_id"] if chosen else None,
                    "target_rank": target["ranks"][ablation] if target else None,
                    "exact_top1": bool(chosen and chosen["eval_is_target_instance"]),
                    "recall_at_3": bool(target and target["ranks"][ablation] <= 3),
                }
            )
        summary[ablation] = {
            "significant_rows": len(records),
            "significant_exact_top1_rate": single.safe_rate(
                sum(1 for row in records if row["exact_top1"]), len(records)
            ),
            "significant_recall_at_3": single.safe_rate(
                sum(1 for row in records if row["recall_at_3"]), len(records)
            ),
            "mean_target_rank": single.round_or_none(
                sum(row["target_rank"] for row in records if row["target_rank"] is not None)
                / sum(1 for row in records if row["target_rank"] is not None)
                if any(row["target_rank"] is not None for row in records)
                else None
            ),
        }
    return summary


def breakdown(
    predictions: list[dict],
    query_rows: list[dict],
    field: str,
    subset_name: str,
    subset_filter,
) -> dict:
    rows = [row for row in query_rows if subset_filter(row)]
    output = {}
    for value in sorted({row[field] for row in rows}):
        value_rows = [row for row in rows if row[field] == value]
        output[str(value)] = {
            "rows": len(value_rows),
            "non_persistent_anchor_v0": summarize_policy(
                "non_persistent_anchor_v0",
                predictions,
                f"{subset_name}_{value}",
                value_rows,
            ),
            "label_nearest_current_observation": summarize_policy(
                "label_nearest_current_observation",
                predictions,
                f"{subset_name}_{value}",
                value_rows,
            ),
        }
    return output


def hard_failures(predictions: list[dict]) -> list[dict]:
    rows = []
    for row in predictions:
        if row["policy"] != "non_persistent_anchor_v0":
            continue
        significant_failure = row["row_band"] == "significant_moved" and not row["exact_recovery"]
        low_motion_failure = (
            row["row_band"] == "low_motion_control"
            and (not row["returns_old_location"] or not row["exact_recovery"])
        )
        if significant_failure or low_motion_failure:
            rows.append(
                {
                    "row_uid": row["row_uid"],
                    "reference_scan_id": row["reference_scan_id"],
                    "rescan_id": row["rescan_id"],
                    "object_instance_id_ref": row["object_instance_id_ref"],
                    "object_label": row["object_label"],
                    "row_band": row["row_band"],
                    "target_rank": row["target_rank"],
                    "chosen_instance_id": row.get("chosen_instance_id"),
                    "candidate_entropy": row.get("candidate_entropy"),
                    "exact_recovery": row["exact_recovery"],
                    "returns_old_location": row["returns_old_location"],
                }
            )
    return rows


def choose_next_staging_target(path: Path) -> dict | None:
    if not path.is_file():
        return None
    candidates = [
        row
        for row in single.load_jsonl(path)
        if not row.get("rescan_payload", {}).get("semseg", False)
    ]
    if not candidates:
        return None
    row = max(
        candidates,
        key=lambda item: (
            item.get("proxy_moved_gt_1_0m") or 0,
            item.get("proxy_moved_gt_0_5m") or 0,
            item.get("score") or 0,
            item.get("proxy_rows") or 0,
        ),
    )
    return {
        "reference_scan_id": row["reference_scan_id"],
        "rescan_id": row["rescan_id"],
        "proxy_moved_gt_1_0m": row.get("proxy_moved_gt_1_0m"),
        "proxy_moved_gt_0_5m": row.get("proxy_moved_gt_0_5m"),
        "proxy_rows": row.get("proxy_rows"),
        "score": row.get("score"),
    }


def decide_status(coverage: dict, metrics: dict) -> str:
    sig_np = metrics["significant_moved"]["non_persistent_anchor_v0"]
    sig_label = metrics["significant_moved"]["label_nearest_current_observation"]
    sig_top3 = metrics["significant_moved"]["label_top3_current_observation"]
    low_np = metrics["low_motion_control"]["non_persistent_anchor_v0"]
    improves = (
        sig_np["exact_recovery_rate"] is not None
        and sig_label["exact_recovery_rate"] is not None
        and sig_np["exact_recovery_rate"] > sig_label["exact_recovery_rate"]
    )
    preserves_recall = (
        sig_np["candidate_recall_at_3"] is not None
        and sig_top3["candidate_recall_at_3"] is not None
        and sig_np["candidate_recall_at_3"] >= sig_top3["candidate_recall_at_3"]
    )
    stale_ok = sig_np["stale_old_location_false_positive_rate"] == 0.0
    low_motion_rate = low_np["low_motion_static_preserved_rate"]
    low_ok = low_motion_rate is None or low_motion_rate >= 0.95
    metric_gate_pass = improves and preserves_recall and stale_ok and low_ok
    data_limited = coverage["validated_pair_count"] < 3 or coverage["significant_moved_rows"] < 10
    if not metric_gate_pass:
        return "fail"
    if data_limited:
        return "data_limited_pass"
    return "strict_pass"


def write_report(out_dir: Path, coverage: dict, metrics: dict) -> None:
    sig = metrics["significant_moved"]
    low = metrics["low_motion_control"]
    lines = [
        "# Multi-Pair Non-Persistent Validation Report",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## Facts",
        "",
        f"- Metadata pairs scanned: {coverage['metadata_pairs_scanned']}",
        f"- Pairs with local reference semantic payload: {coverage['pairs_with_reference_semseg']}",
        f"- Local ready semantic pairs: {coverage['local_ready_pair_candidates']}",
        f"- Validated pairs run: {coverage['validated_pair_count']}",
        f"- Query rows: {coverage['query_rows']}",
        f"- Significant moved rows: {coverage['significant_moved_rows']}",
        f"- Low-motion controls: {coverage['low_motion_control_rows']}",
        f"- Mid-motion review rows: {coverage['mid_motion_review_rows']}",
        f"- Ranking uses persistent cross-scan ids: {coverage['ranking_uses_persistent_cross_scan_ids']}",
        f"- Uses exact current pose for ranking: {coverage['uses_exact_current_pose_for_ranking']}",
        f"- Uses navigation: {coverage['uses_navigation']}",
        f"- Uses RGB-D perception: {coverage['uses_rgbd_perception']}",
        f"- Uses open-vocabulary perception: {coverage['uses_open_vocabulary_perception']}",
        "",
        "## Significant Moved Metrics",
        "",
        "| Policy | Exact recovery | Recall@1 | Recall@3 | Stale FP | Mean candidates |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in POLICIES:
        item = sig[policy]
        lines.append(
            "| {policy} | {exact} | {r1} | {r3} | {fp} | {cands} |".format(
                policy=policy,
                exact=item["exact_recovery_rate"],
                r1=item["candidate_recall_at_1"],
                r3=item["candidate_recall_at_3"],
                fp=item["stale_old_location_false_positive_rate"],
                cands=item["mean_candidate_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Low-Motion Control Metrics",
            "",
            "| Policy | Static preserved | Forced re-observation | Exact recovery |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for policy in POLICIES:
        item = low[policy]
        lines.append(
            "| {policy} | {preserved} | {forced} | {exact} |".format(
                policy=policy,
                preserved=item["low_motion_static_preserved_rate"],
                forced=item["control_forced_reobservation_rate"],
                exact=item["exact_recovery_rate"],
            )
        )
    lines.extend(
        [
            "",
            "## Pair Breakdown",
            "",
            "| Pair | Rows | Significant | Low-motion | NP exact significant | NP stale FP |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in metrics["per_pair"]:
        np_sig = item["significant_moved"]["non_persistent_anchor_v0"]
        lines.append(
            "| {pair} | {rows} | {sig_rows} | {low_rows} | {exact} | {fp} |".format(
                pair=item["pair_uid"],
                rows=item["query_rows"],
                sig_rows=item["significant_moved_rows"],
                low_rows=item["low_motion_control_rows"],
                exact=np_sig["exact_recovery_rate"],
                fp=np_sig["stale_old_location_false_positive_rate"],
            )
        )
    if coverage["status"] == "strict_pass":
        claim_line = "- This run supports a strict hypothesis-stage multi-pair semantic map-update validation result."
        threshold_line = "- A strict pass means the local hypothesis-stage gate is satisfied, but experiment-stage promotion still requires claim-boundary interpretation and broader method planning."
        decision_line = "- No immediate decision is required unless the next step is experiment-stage promotion or additional staging."
    else:
        claim_line = "- If status is `data_limited_pass`, no multi-pair claim is supported yet."
        threshold_line = "- A data-limited pass means the method remains promising but the evidence is still too small for experiment-stage promotion."
        decision_line = "- No immediate decision is required unless additional rescan payload staging needs manual download choices."
    lines.extend(
        [
            "",
            "## Gate Decision",
            "",
            f"- Result status: `{coverage['status']}`",
            f"- Strict pair threshold met: {coverage['strict_pair_threshold_met']}",
            f"- Strict significant-row threshold met: {coverage['strict_significant_row_threshold_met']}",
            f"- Next staging target: `{coverage.get('next_staging_target')}`",
            "",
            "## 논문 주장",
            "",
            "- This run supports only a hypothesis-stage validation result.",
            "- No final moved-object recovery, navigation, RGB-D perception, open-vocabulary perception, or deployable search policy claim is supported.",
            claim_line,
            "",
            "## 에이전트 추론",
            "",
            "- The core ranking signal should be judged by whether `non_persistent_anchor_v0` improves rank-sensitive significant moved rows without damaging low-motion controls.",
            threshold_line,
            "",
            "## 사용자 판단 필요",
            "",
            decision_line,
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--staging-targets", type=Path, default=DEFAULT_STAGING_TARGETS)
    parser.add_argument("--geometry-threshold-m", type=float, default=1.0)
    parser.add_argument("--significant-threshold-m", type=float, default=1.0)
    parser.add_argument("--low-motion-threshold-m", type=float, default=0.25)
    parser.add_argument("--success-threshold-m", type=float, default=0.5)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    local_ready_pairs, coverage_base = load_local_ready_pairs(args.dataset_root)
    relationships = single.load_relationships(args.dataset_root / "3DSSG" / "relationships.json")

    all_pair_rows = []
    all_query_rows = []
    all_feature_rows = []
    all_predictions = []
    pair_summaries = []
    feature_rows_by_uid: dict[str, list[dict]] = {}

    for pair in local_ready_pairs:
        reference_scan_id = pair["reference_scan_id"]
        rescan_id = pair["rescan_id"]
        pair_metadata = pair["pair_metadata"]
        pair_rows, query_rows, pair_summary = build_pair_rows(
            args.dataset_root,
            reference_scan_id,
            rescan_id,
            pair_metadata,
            args.geometry_threshold_m,
            args.significant_threshold_m,
            args.low_motion_threshold_m,
        )
        all_pair_rows.extend(pair_rows)
        if not query_rows:
            pair_summaries.append(pair_summary)
            continue

        ref_objects = single.load_semseg_objects(semseg_path(args.dataset_root, reference_scan_id))
        rescan_objects = single.load_semseg_objects(semseg_path(args.dataset_root, rescan_id))
        relationships.setdefault(reference_scan_id, [])
        relationships.setdefault(rescan_id, [])
        scene_inverse = single.invert_rigid_row_transform(pair_metadata["transform"])

        single.REFERENCE_SCAN_ID = reference_scan_id
        single.RESCAN_ID = rescan_id
        feature_rows, rows_by_object = single.build_feature_rows(
            query_rows,
            ref_objects,
            rescan_objects,
            relationships,
            scene_inverse,
        )

        for row in query_rows:
            object_rows = rows_by_object[row["object_instance_id_ref"]]
            candidate_count = len(object_rows)
            row["same_label_candidate_count"] = candidate_count
            row["ambiguity_band"] = (
                "trivial_candidate"
                if candidate_count == 1
                else "high_ambiguity"
                if candidate_count >= 5
                else "rank_sensitive"
            )
            label_ranked = ranked_label_candidates(row, object_rows, rescan_objects)
            np_ranked = [
                {
                    **item,
                    "centroid": rescan_objects[item["candidate_instance_id"]]["centroid"],
                }
                for item in single.sorted_feature_rows_for_object(
                    rows_by_object,
                    row["object_instance_id_ref"],
                    "full_non_persistent",
                )
            ]
            for policy in POLICIES:
                pred = predict_policy(
                    policy,
                    row,
                    label_ranked,
                    np_ranked,
                    args.success_threshold_m,
                )
                all_predictions.append({**row, **pred})

        for feature_row in feature_rows:
            matching_query = next(
                row
                for row in query_rows
                if row["object_instance_id_ref"] == feature_row["object_instance_id_ref"]
            )
            augmented = {
                **feature_row,
                "row_uid": matching_query["row_uid"],
                "pair_uid": matching_query["pair_uid"],
                "reference_scan_id": reference_scan_id,
                "rescan_id": rescan_id,
                "episode_id": matching_query["episode_id"],
                "same_label_candidate_count": matching_query["same_label_candidate_count"],
                "ambiguity_band": matching_query["ambiguity_band"],
            }
            all_feature_rows.append(augmented)
            feature_rows_by_uid.setdefault(matching_query["row_uid"], []).append(augmented)

        all_query_rows.extend(query_rows)
        pair_summary["query_rows"] = len(query_rows)
        pair_summary["significant_moved_rows"] = sum(
            1 for row in query_rows if row["row_band"] == "significant_moved"
        )
        pair_summary["low_motion_control_rows"] = sum(
            1 for row in query_rows if row["row_band"] == "low_motion_control"
        )
        pair_summary["mid_motion_review_rows"] = sum(
            1 for row in query_rows if row["row_band"] == "mid_motion_review"
        )
        pair_summaries.append(pair_summary)

    significant_rows = [row for row in all_query_rows if row["row_band"] == "significant_moved"]
    low_motion_rows = [row for row in all_query_rows if row["row_band"] == "low_motion_control"]
    mid_motion_rows = [row for row in all_query_rows if row["row_band"] == "mid_motion_review"]
    rank_sensitive_rows = [
        row for row in all_query_rows if row.get("same_label_candidate_count", 0) >= 2
    ]
    high_ambiguity_rows = [
        row for row in all_query_rows if row.get("same_label_candidate_count", 0) >= 5
    ]

    metrics = {
        "all_row_valid": policy_metrics(all_predictions, "all_row_valid", all_query_rows),
        "significant_moved": policy_metrics(all_predictions, "significant_moved", significant_rows),
        "low_motion_control": policy_metrics(all_predictions, "low_motion_control", low_motion_rows),
        "mid_motion_review": policy_metrics(all_predictions, "mid_motion_review", mid_motion_rows),
        "rank_sensitive": policy_metrics(all_predictions, "rank_sensitive", rank_sensitive_rows),
        "high_ambiguity": policy_metrics(all_predictions, "high_ambiguity", high_ambiguity_rows),
        "ablations": summarize_ablations(all_query_rows, feature_rows_by_uid),
        "label_breakdown_significant": breakdown(
            all_predictions,
            all_query_rows,
            "object_label",
            "significant_label",
            lambda row: row["row_band"] == "significant_moved",
        ),
        "ambiguity_breakdown": breakdown(
            all_predictions,
            all_query_rows,
            "ambiguity_band",
            "ambiguity",
            lambda row: True,
        ),
        "hard_failures": hard_failures(all_predictions),
    }
    per_pair = []
    for summary in pair_summaries:
        rows = [row for row in all_query_rows if row["pair_uid"] == summary["pair_uid"]]
        sig_rows = [row for row in rows if row["row_band"] == "significant_moved"]
        per_pair.append(
            {
                **summary,
                "all_row_valid": policy_metrics(all_predictions, f"{summary['pair_uid']}_all", rows),
                "significant_moved": policy_metrics(
                    all_predictions,
                    f"{summary['pair_uid']}_significant",
                    sig_rows,
                ),
            }
        )
    metrics["per_pair"] = per_pair

    next_target = choose_next_staging_target(args.staging_targets)
    coverage = {
        **coverage_base,
        "dataset_root": str(args.dataset_root),
        "validated_pair_count": sum(1 for item in pair_summaries if item["query_rows"] > 0),
        "pair_rows": len(all_pair_rows),
        "query_rows": len(all_query_rows),
        "significant_moved_rows": len(significant_rows),
        "low_motion_control_rows": len(low_motion_rows),
        "mid_motion_review_rows": len(mid_motion_rows),
        "rank_sensitive_rows": len(rank_sensitive_rows),
        "high_ambiguity_rows": len(high_ambiguity_rows),
        "strict_pair_threshold_met": sum(1 for item in pair_summaries if item["query_rows"] > 0) >= 3,
        "strict_significant_row_threshold_met": len(significant_rows) >= 10,
        "uses_annotation_level_current_observation": True,
        "ranking_uses_persistent_cross_scan_ids": False,
        "uses_exact_current_pose_for_ranking": False,
        "uses_navigation": False,
        "uses_rgbd_perception": False,
        "uses_open_vocabulary_perception": False,
        "geometry_threshold_m": args.geometry_threshold_m,
        "significant_threshold_m": args.significant_threshold_m,
        "low_motion_threshold_m": args.low_motion_threshold_m,
        "success_threshold_m": args.success_threshold_m,
        "next_staging_target": pair_uid(next_target["reference_scan_id"], next_target["rescan_id"])
        if next_target
        else None,
        "next_staging_target_detail": next_target,
    }
    coverage["status"] = decide_status(coverage, metrics)

    write_json(args.out_dir / "coverage.json", coverage)
    write_json(args.out_dir / "metrics.json", metrics)
    write_jsonl(args.out_dir / "pair_rows.jsonl", all_pair_rows)
    write_jsonl(args.out_dir / "query_rows.jsonl", all_query_rows)
    write_jsonl(args.out_dir / "candidate_rows.jsonl", all_feature_rows)
    write_jsonl(args.out_dir / "predictions.jsonl", all_predictions)
    write_report(args.out_dir, coverage, metrics)

    print(
        json.dumps(
            {
                "coverage": coverage,
                "significant_moved": metrics["significant_moved"],
                "low_motion_control": metrics["low_motion_control"],
                "hard_failures": metrics["hard_failures"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
