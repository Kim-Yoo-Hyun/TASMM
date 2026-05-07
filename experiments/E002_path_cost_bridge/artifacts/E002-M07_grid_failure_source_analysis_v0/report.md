# E002-M07 Grid Failure Source Analysis

## Status

grid_failure_source_analysis_ready

## 사실

- Grid query rows: 294
- Target-unreachable query rows: 27
- Target-unreachable base rows: 9
- Target-unreachable rate: 0.091837
- Returned-unreachable prediction rows: 331
- Returned-unreachable rows with reachable target: 144
- Returned-unreachable rows dominated by source limitation: 187
- Candidate grid reachable rows from M05: 1029
- Candidate grid unreachable rows from M05: 219
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0`

## Target Source Failures

| Source failure | Rows |
| --- | ---: |
| `candidate_unprojectable` | 6 |
| `disconnected_free_space` | 15 |
| `start_unprojectable` | 6 |

## Grid-Aware Comparison

| Scope | Rows | Success gain | Success loss | Cost improvement | Cost regression | Mean utility delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `all` | 294 | 0 | 2 | 7 | 13 | -0.012863 |
| `significant_moved` | 33 | 0 | 1 | 2 | 5 | -0.057127 |

## 논문 주장

- E002-M07 supports separating occupancy-grid source limits from policy failures.
- E002-M07 supports keeping `target_grid_unreachable` rows explicit instead of dropping them.
- E002-M07 does not support a positive claim for `grid_path_aware_task_conditioned_budget_v0`.
- E002-M07 does not support real navigation `SR` / `SPL`, deployable search policy, or RGB-D/open-vocabulary robustness claims.

## 에이전트 추론

- Target-unreachable rows are mostly source/grid-construction limits, so they should be reported separately from method misses.
- Grid-aware ordering reduces some returned-unreachable attempts, but it also loses target recall under fixed budgets.
- The next method step should improve reachable-candidate scoring or add a source-quality mask before claiming navigation-style value.

## 사용자 판단 필요

- None for E002-M07. Next action should be either a source-quality mask or a grid-aware scoring revision.

## Outputs

- `target_source_rows.jsonl`
- `returned_unreachable_rows.jsonl`
- `grid_aware_comparison_rows.jsonl`
- `summary.json`
- `report.md`
