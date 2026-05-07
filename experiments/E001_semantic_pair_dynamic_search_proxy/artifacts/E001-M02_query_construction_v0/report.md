# E001-M02 Query Construction

## Status

ready

## 사실

- Dataset root: `/home/yoohyun/research2/local_dataset`
- Manifest path: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0/manifest.jsonl`
- Ready manifest pairs: 13
- Validated pair count: 13
- Pair rigid rows: 101
- Base query rows: 98
- Context-expanded query rows: 294
- Candidate rows: 1248
- Significant moved base rows: 11
- Low-motion control base rows: 51
- Mid-motion review base rows: 36
- Rows with `rgbd_sequence_available`: 0
- Output directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0`

## Context Expansion

| `task_context_id` | Query rows |
| --- | ---: |
| `high_value_fetch` | 98 |
| `noisy_high_value_fetch` | 98 |
| `routine_fetch` | 98 |

## 논문 주장

- E001-M02 supports proxy query construction for semantic-pair dynamic object search.
- Human intent is represented only as structured task context that changes memory trust, re-observation threshold, and candidate budget.
- E001-M02 still does not support real navigation `SR` / `SPL`, RGB-D perception robustness, open-vocabulary perception robustness, learned policy, or natural-language intention understanding.

## 에이전트 추론

- `row_uid` is context-expanded, while `base_row_uid` preserves the object-level denominator.
- E002 can attach `candidate_path_cost_m`, `path_cost_profile_id`, and path-aware `candidate_visit_order_policy` without rebuilding the query set.
- E003 can replace `annotation_semseg` candidates with RGB-D or open-vocabulary proposals while preserving the same target rows.
- E004 can compare task contexts directly because every base row is expanded over the same structured context profiles.

## 사용자 판단 필요

- None for E001-M02. Continue to E001 baseline evaluation.

## Outputs

- `pair_rows.jsonl`
- `base_query_rows.jsonl`
- `query_rows.jsonl`
- `candidate_rows.jsonl`
- `coverage.json`
- `report.md`
