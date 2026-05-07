# E001-M03 Baseline Evaluation

## Status

baseline_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0`
- Query rows: 294
- Base query rows: 98
- Candidate rows: 1248
- Predictions: 2352
- Failure rows: 184
- Policies: `scene_aligned_static_map`, `label_nearest_current_observation`, `always_top1`, `always_top3`, `always_top5`, `fixed_uncertainty_topk_v0`, `task_conditioned_budget_v0`, `oracle_current_target`
- Output directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0`

## Significant Moved Rows

### `routine_fetch`

| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 2.0 | 0.0 | -0.3 | 1.0 |
| `label_nearest_current_observation` | 0.636364 | 1.363636 | 0.636364 | 0.431818 | 0.0 |
| `always_top1` | 0.636364 | 1.363636 | 0.636364 | 0.431818 | 0.0 |
| `always_top3` | 0.727273 | 1.909091 | 0.681818 | 0.440909 | 0.0 |
| `always_top5` | 0.909091 | 2.181818 | 0.722727 | 0.581818 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 1.909091 | 0.681818 | 0.440909 | 0.0 |
| `task_conditioned_budget_v0` | 0.727273 | 1.636364 | 0.681818 | 0.481818 | 0.0 |
| `oracle_current_target` | 1.0 | 1.0 | 1.0 | 0.85 | 0.0 |

### `high_value_fetch`

| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 2.0 | 0.0 | -0.55 | 1.0 |
| `label_nearest_current_observation` | 0.636364 | 1.363636 | 0.636364 | 1.613636 | 0.0 |
| `always_top1` | 0.636364 | 1.363636 | 0.636364 | 1.613636 | 0.0 |
| `always_top3` | 0.727273 | 1.909091 | 0.681818 | 1.827273 | 0.0 |
| `always_top5` | 0.909091 | 2.181818 | 0.722727 | 2.377273 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 1.909091 | 0.681818 | 1.827273 | 0.0 |
| `task_conditioned_budget_v0` | 0.909091 | 2.181818 | 0.722727 | 2.377273 | 0.0 |
| `oracle_current_target` | 1.0 | 1.0 | 1.0 | 2.85 | 0.0 |

### `noisy_high_value_fetch`

| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 2.0 | 0.0 | -0.55 | 1.0 |
| `label_nearest_current_observation` | 0.636364 | 1.363636 | 0.636364 | 1.613636 | 0.0 |
| `always_top1` | 0.636364 | 1.363636 | 0.636364 | 1.613636 | 0.0 |
| `always_top3` | 0.727273 | 1.909091 | 0.681818 | 1.827273 | 0.0 |
| `always_top5` | 0.909091 | 2.181818 | 0.722727 | 2.377273 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 1.909091 | 0.681818 | 1.827273 | 0.0 |
| `task_conditioned_budget_v0` | 0.909091 | 2.181818 | 0.722727 | 2.377273 | 0.0 |
| `oracle_current_target` | 1.0 | 1.0 | 1.0 | 2.85 | 0.0 |

## 논문 주장

- This artifact supports clean annotation-level E001 baseline comparison for semantic-pair dynamic object search proxy tasks.
- This artifact does not support real navigation `SR` / `SPL`, RGB-D perception robustness, open-vocabulary perception robustness, learned policy, or natural-language intention understanding.

## 에이전트 추론

- `task_conditioned_budget_v0` should be judged against both fixed top-k and oracle upper bound, not only against the static map.
- Structured task context is used as a controlled variable so E004 can later test whether memory trust changes are useful before adding LLM parsing.
- E002 should reuse `expected_search_cost` and replace candidate-count cost with path/search cost.

## 사용자 판단 필요

- None for E001-M03. Continue to E001 failure analysis or E002 path-cost bridge after reviewing baseline table.

## Outputs

- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
