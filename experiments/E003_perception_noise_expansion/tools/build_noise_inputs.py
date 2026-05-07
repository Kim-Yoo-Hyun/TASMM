#!/usr/bin/env python3
"""Build E003 annotation-proxy noisy query and candidate rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = EXPERIMENT_ROOT / "artifacts" / "E003-M01_source_audit_v0" / "noise_plan.json"
DEFAULT_OUT_DIR = EXPERIMENT_ROOT / "artifacts" / "E003-M02_annotation_proxy_noise_v0"
NOISE_VERSION = "e003_annotation_proxy_noise_v0"


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


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def safe_rate(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return round(num / den, 6)


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def group_by_uid(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["row_uid"]].append(row)
    return dict(grouped)


def instance_key(value: Any) -> Any:
    text = str(value)
    return int(text) if text.isdigit() else text


def noisy_row_uid(row_uid: str, profile_id: str) -> str:
    return f"{row_uid}::noise={profile_id}"


def deterministic_rng(seed: int, *parts: str) -> random.Random:
    joined = "|".join([str(seed), *parts])
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def clamp_score(value: float) -> float:
    return min(1.0, max(0.0, value))


def build_noisy_query(row: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    profile_id = profile["proposal_noise_profile_id"]
    output = dict(row)
    output["original_row_uid"] = row["row_uid"]
    output["row_uid"] = noisy_row_uid(row["row_uid"], profile_id)
    output["noise_version"] = NOISE_VERSION
    output["perception_profile_id"] = "annotation_proxy_noise"
    output["proposal_noise_profile_id"] = profile_id
    output["proposal_noise_role"] = profile["role"]
    output["proposal_noise_target_policy"] = profile["target_policy"]
    output["proposal_noise_seed"] = profile.get("seed")
    output["current_proposal_source"] = "annotation_semseg_noisy_proxy"
    output["observation_source"] = "annotation_semseg_noisy_proxy"
    output["uses_real_rgbd_perception"] = False
    output["uses_open_vocab_perception"] = False
    output["target_dropped_by_noise"] = False
    return output


def build_noisy_candidates(
    original_row_uid: str,
    candidates: list[dict[str, Any]],
    profile: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile_id = profile["proposal_noise_profile_id"]
    row_uid = noisy_row_uid(original_row_uid, profile_id)
    rows = []
    for row in candidates:
        output = dict(row)
        original_score = float(row["candidate_score_non_persistent"])
        if profile_id == "clean_annotation_oracle_v0":
            noise_delta = 0.0
            noisy_score = original_score
        elif profile_id == "annotation_score_jitter_v0":
            rng = deterministic_rng(
                int(profile["seed"]),
                original_row_uid,
                str(row["candidate_instance_id"]),
                profile_id,
            )
            noise_delta = rng.gauss(0.0, float(profile["score_jitter_sigma"]))
            noisy_score = clamp_score(original_score + noise_delta)
        else:
            raise RuntimeError(f"unsupported profile in M02: {profile_id}")

        output["original_row_uid"] = original_row_uid
        output["row_uid"] = row_uid
        output["noise_version"] = NOISE_VERSION
        output["perception_profile_id"] = "annotation_proxy_noise"
        output["proposal_noise_profile_id"] = profile_id
        output["proposal_noise_role"] = profile["role"]
        output["proposal_noise_seed"] = profile.get("seed")
        output["candidate_observation_source"] = "annotation_semseg_noisy_proxy"
        output["original_candidate_rank_non_persistent"] = row["candidate_rank_non_persistent"]
        output["original_candidate_score_non_persistent"] = row["candidate_score_non_persistent"]
        output["candidate_score_noise_delta"] = round6(noise_delta)
        output["candidate_score_non_persistent"] = round6(noisy_score)
        output["candidate_retained_by_noise"] = True
        output["candidate_added_by_noise"] = False
        rows.append(output)

    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row["candidate_score_non_persistent"]),
            int(row["original_candidate_rank_non_persistent"]),
            row["candidate_euclidean_cost_from_old_m"],
            instance_key(row["candidate_instance_id"]),
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["candidate_rank_non_persistent"] = rank
        row["candidate_visit_order_index"] = rank
        row["candidate_visit_policy"] = f"{profile_id}_ranked_candidates"

    target_rows = [row for row in ranked if row["candidate_is_target"]]
    target_rank = target_rows[0]["candidate_rank_non_persistent"] if target_rows else None
    original_target_rank = (
        target_rows[0]["original_candidate_rank_non_persistent"] if target_rows else None
    )
    changed_rows = [
        row
        for row in ranked
        if row["candidate_rank_non_persistent"] != row["original_candidate_rank_non_persistent"]
    ]
    manifest = {
        "noise_version": NOISE_VERSION,
        "original_row_uid": original_row_uid,
        "row_uid": row_uid,
        "proposal_noise_profile_id": profile_id,
        "proposal_noise_role": profile["role"],
        "proposal_noise_seed": profile.get("seed"),
        "candidate_rows": len(ranked),
        "target_retained": len(target_rows) == 1,
        "target_dropped_by_noise": False,
        "target_rank_original": original_target_rank,
        "target_rank_noisy": target_rank,
        "target_rank_delta": target_rank - original_target_rank
        if target_rank is not None and original_target_rank is not None
        else None,
        "rank_changed_candidate_rows": len(changed_rows),
        "rank_changed": bool(changed_rows),
        "score_jitter_sigma": profile.get("score_jitter_sigma"),
        "rank_recompute": profile.get("rank_recompute", False),
    }
    return ranked, manifest


def summarize_profile(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not manifest_rows:
        return {"rows": 0}
    target_retained = sum(1 for row in manifest_rows if row["target_retained"])
    rank_changed = sum(1 for row in manifest_rows if row["rank_changed"])
    target_rank_changed = sum(
        1 for row in manifest_rows if row["target_rank_delta"] not in {0, None}
    )
    return {
        "rows": len(manifest_rows),
        "target_retained_rows": target_retained,
        "target_retained_rate": safe_rate(target_retained, len(manifest_rows)),
        "rank_changed_rows": rank_changed,
        "rank_changed_rate": safe_rate(rank_changed, len(manifest_rows)),
        "target_rank_changed_rows": target_rank_changed,
        "target_rank_changed_rate": safe_rate(target_rank_changed, len(manifest_rows)),
        "target_rank_delta_counts": counter_dict(
            Counter(row["target_rank_delta"] for row in manifest_rows)
        ),
    }


def build_coverage(
    query_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    noisy_query_rows: list[dict[str, Any]],
    noisy_candidate_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    out_dir: Path,
) -> dict[str, Any]:
    by_profile = {
        profile["proposal_noise_profile_id"]: summarize_profile(
            [
                row
                for row in manifest_rows
                if row["proposal_noise_profile_id"] == profile["proposal_noise_profile_id"]
            ]
        )
        for profile in profiles
    }
    status = (
        "annotation_proxy_noise_ready"
        if len(noisy_query_rows) == len(query_rows) * len(profiles)
        and len(manifest_rows) == len(query_rows) * len(profiles)
        and all(item["target_retained_rate"] == 1.0 for item in by_profile.values())
        else "review_needed"
    )
    return {
        "noise_version": NOISE_VERSION,
        "status": status,
        "input_query_rows": len(query_rows),
        "input_candidate_rows": len(candidate_rows),
        "profile_count": len(profiles),
        "profiles": [profile["proposal_noise_profile_id"] for profile in profiles],
        "noisy_query_rows": len(noisy_query_rows),
        "noisy_candidate_rows": len(noisy_candidate_rows),
        "noise_manifest_rows": len(manifest_rows),
        "profile_summaries": by_profile,
        "row_band_counts": counter_dict(Counter(row["row_band"] for row in query_rows)),
        "task_context_counts": counter_dict(Counter(row["task_context_id"] for row in query_rows)),
        "uses_real_rgbd_perception": False,
        "uses_open_vocab_perception": False,
        "target_drop_profiles_included": False,
        "unsupported_claims": [
            "real RGB-D perception robustness",
            "open-vocabulary perception robustness",
            "real navigation SR/SPL",
            "deployable search policy",
        ],
        "outputs": {
            "noise_manifest": str(out_dir / "noise_manifest.jsonl"),
            "noisy_query_rows": str(out_dir / "noisy_query_rows.jsonl"),
            "noisy_candidate_rows": str(out_dir / "noisy_candidate_rows.jsonl"),
            "coverage": str(out_dir / "coverage.json"),
            "report": str(out_dir / "report.md"),
        },
    }


def build_report(coverage: dict[str, Any], out_dir: Path) -> str:
    lines = [
        "# E003-M02 Annotation-Proxy Noise Generator",
        "",
        "## Status",
        "",
        coverage["status"],
        "",
        "## 사실",
        "",
        f"- Input query rows: {coverage['input_query_rows']}",
        f"- Input candidate rows: {coverage['input_candidate_rows']}",
        f"- Profiles: {', '.join(f'`{profile}`' for profile in coverage['profiles'])}",
        f"- Noisy query rows: {coverage['noisy_query_rows']}",
        f"- Noisy candidate rows: {coverage['noisy_candidate_rows']}",
        f"- Noise manifest rows: {coverage['noise_manifest_rows']}",
        f"- Output directory: `{out_dir}`",
        "",
        "## Profile Summary",
        "",
        "| Profile | Rows | Target retained | Rank changed | Target rank changed |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for profile, item in coverage["profile_summaries"].items():
        lines.append(
            f"| `{profile}` | {item['rows']} | {item['target_retained_rate']} | {item['rank_changed_rate']} | {item['target_rank_changed_rate']} |"
        )
    lines.extend(
        [
            "",
            "## 논문 주장",
            "",
            "- E003-M02 supports controlled annotation-proxy score/rank noise input generation.",
            "- E003-M02 preserves target presence, so it tests ranking robustness rather than proposal recall failure.",
            "- E003-M02 does not support real RGB-D or open-vocabulary perception robustness.",
            "",
            "## 에이전트 추론",
            "",
            "- `clean_annotation_oracle_v0` is the reference condition for robustness deltas.",
            "- `annotation_score_jitter_v0` is the first stress condition because it changes ranking without mixing in target dropout.",
            "- E003-M03 should evaluate policy robustness on these noisy rows before adding dropout or false-positive profiles.",
            "",
            "## 사용자 판단 필요",
            "",
            "- None for E003-M02. Continue to E003-M03 noisy policy evaluation.",
            "",
            "## Outputs",
            "",
            "- `noise_manifest.jsonl`",
            "- `noisy_query_rows.jsonl`",
            "- `noisy_candidate_rows.jsonl`",
            "- `coverage.json`",
            "- `report.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    plan = load_json(args.plan)
    query_rows = load_jsonl(Path(plan["input_query_artifact"]))
    candidate_rows = load_jsonl(Path(plan["input_candidate_artifact"]))
    candidates_by_uid = group_by_uid(candidate_rows)
    profiles = plan["primary_profiles"]

    noisy_query_rows = []
    noisy_candidate_rows = []
    manifest_rows = []

    for profile in profiles:
        for row in query_rows:
            original_row_uid = row["row_uid"]
            noisy_query_rows.append(build_noisy_query(row, profile))
            candidates, manifest = build_noisy_candidates(
                original_row_uid,
                candidates_by_uid.get(original_row_uid, []),
                profile,
            )
            noisy_candidate_rows.extend(candidates)
            manifest_rows.append(manifest)

    coverage = build_coverage(
        query_rows,
        candidate_rows,
        noisy_query_rows,
        noisy_candidate_rows,
        manifest_rows,
        profiles,
        args.out_dir,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "noise_manifest.jsonl", manifest_rows)
    write_jsonl(args.out_dir / "noisy_query_rows.jsonl", noisy_query_rows)
    write_jsonl(args.out_dir / "noisy_candidate_rows.jsonl", noisy_candidate_rows)
    write_json(args.out_dir / "coverage.json", coverage)
    (args.out_dir / "report.md").write_text(build_report(coverage, args.out_dir), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": coverage["status"],
                "noisy_query_rows": coverage["noisy_query_rows"],
                "noisy_candidate_rows": coverage["noisy_candidate_rows"],
                "profile_summaries": coverage["profile_summaries"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
