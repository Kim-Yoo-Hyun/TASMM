# E002-M08 Source-Quality Filtered Grid Evaluation

## Status

source_quality_filtered_grid_eval_ready

## 사실

- Query rows: 294
- Target-reachable eval rows: 267
- Source-limited target-unreachable rows: 27
- All-candidates-reachable sensitivity rows: 198
- Target-reachable eval prediction rows: 2403
- Target-reachable eval failure rows: 144
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0`

## Source Limit Summary

| Source failure | Rows |
| --- | ---: |
| `candidate_unprojectable` | 6 |
| `disconnected_free_space` | 15 |
| `start_unprojectable` | 6 |

## Target-Reachable Significant Moved Rows

### `routine_fetch`

| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 9 | 0.0 | 1.0 | 0.0 | -0.15 | 0.0 |
| `always_top1` | 9 | 0.666667 | 0.940767 | 0.666667 | 0.525552 | 0.0 |
| `always_top3` | 9 | 0.777778 | 1.676142 | 0.760261 | 0.526356 | 0.111111 |
| `always_top5` | 9 | 0.888889 | 2.88009 | 0.804277 | 0.456875 | 0.111111 |
| `fixed_uncertainty_topk_v0` | 9 | 0.777778 | 1.676142 | 0.760261 | 0.526356 | 0.111111 |
| `task_conditioned_budget_v0` | 9 | 0.777778 | 1.415195 | 0.760261 | 0.565498 | 0.111111 |
| `grid_path_aware_task_conditioned_budget_v0` | 9 | 0.666667 | 1.390276 | 0.612722 | 0.458125 | 0.0 |
| `oracle_current_target` | 9 | 1.0 | 1.719008 | 1.0 | 0.742149 | 0.0 |

### `high_value_fetch`

| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 9 | 0.0 | 1.0 | 0.0 | -0.4 | 0.0 |
| `always_top1` | 9 | 0.666667 | 0.940767 | 0.666667 | 1.775552 | 0.0 |
| `always_top3` | 9 | 0.777778 | 1.676142 | 0.760261 | 2.026356 | 0.111111 |
| `always_top5` | 9 | 0.888889 | 2.88009 | 0.804277 | 2.206875 | 0.111111 |
| `fixed_uncertainty_topk_v0` | 9 | 0.777778 | 1.676142 | 0.760261 | 2.026356 | 0.111111 |
| `task_conditioned_budget_v0` | 9 | 0.888889 | 2.88009 | 0.804277 | 2.206875 | 0.111111 |
| `grid_path_aware_task_conditioned_budget_v0` | 9 | 0.888889 | 2.9985 | 0.725676 | 2.189114 | 0.111111 |
| `oracle_current_target` | 9 | 1.0 | 1.719008 | 1.0 | 2.742149 | 0.0 |

## Key Comparisons

- `routine_fetch` target-reachable significant moved `task_conditioned_budget_v0` `SR`: 0.777778 vs `always_top5` 0.888889 vs oracle 1.0.
- `high_value_fetch` target-reachable significant moved `task_conditioned_budget_v0` `SR`: 0.888889 vs `always_top5` 0.888889 vs oracle 1.0.
- `grid_path_aware_task_conditioned_budget_v0` remains unsupported as an improvement claim: routine significant moved `SR` delta vs task-conditioned is -0.111111.

## Strict Sensitivity

- `all_candidates_reachable_eval` rows: 198.
- Significant moved `routine_fetch` rows under strict sensitivity: 4.
- This strict view is a diagnostic, not the primary denominator, because it removes many hard candidate-set rows.

## 논문 주장

- E002-M08 supports reporting source-quality-filtered grid-path proxy metrics separately from source-limited rows.
- E002-M08 supports using `target_reachable_eval` as the primary grid-path proxy denominator.
- E002-M08 does not support a positive claim for naive `grid_path_aware_task_conditioned_budget_v0`.
- E002-M08 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.

## 에이전트 추론

- The filtered denominator makes the oracle upper bound interpretable: target-reachable oracle `SR` becomes 1.0.
- The core method signal is still task-conditioned stale-memory suppression, not path-aware ordering.
- Candidate-unreachable rows should remain a diagnostic because removing all of them leaves too few significant moved rows for the main claim.

## 사용자 판단 필요

- None for E002-M08. Next action should decide whether to revise grid-aware scoring or move to E003 perception-noise expansion.

## Outputs

- `source_quality_rows.jsonl`
- `source_limit_rows.jsonl`
- `filtered_predictions.jsonl`
- `target_reachable_failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
