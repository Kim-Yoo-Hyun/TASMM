# E002-M02 Path Policy Evaluation

## Status

path_policy_eval_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0`
- Query rows: 294
- Prediction rows: 2646
- Failure rows: 191
- Path-cost profile: `euclidean_polyline_proxy_v0`
- Real navigation path-cost rows: 0
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0`

## Significant Moved Rows

### `routine_fetch`

| Policy | proxy `SR` | Path cost | Path `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.15 | 1.0 |
| `always_top1` | 0.636364 | 1.27675 | 0.636364 | 0.444851 | 0.0 |
| `always_top3` | 0.727273 | 2.026084 | 0.688026 | 0.42336 | 0.0 |
| `always_top5` | 0.909091 | 2.649124 | 0.763075 | 0.511722 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 2.026084 | 0.688026 | 0.42336 | 0.0 |
| `task_conditioned_budget_v0` | 0.727273 | 1.718859 | 0.688026 | 0.469444 | 0.0 |
| `path_aware_task_conditioned_budget_v0` | 0.727273 | 1.718859 | 0.688026 | 0.469444 | 0.0 |
| `oracle_current_target` | 1.0 | 1.753063 | 1.0 | 0.737041 | 0.0 |

### `high_value_fetch`

| Policy | proxy `SR` | Path cost | Path `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.4 | 1.0 |
| `always_top1` | 0.636364 | 1.27675 | 0.636364 | 1.626669 | 0.0 |
| `always_top3` | 0.727273 | 2.026084 | 0.688026 | 1.809724 | 0.0 |
| `always_top5` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 2.026084 | 0.688026 | 1.809724 | 0.0 |
| `task_conditioned_budget_v0` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `path_aware_task_conditioned_budget_v0` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `oracle_current_target` | 1.0 | 1.753063 | 1.0 | 2.737041 | 0.0 |

### `noisy_high_value_fetch`

| Policy | proxy `SR` | Path cost | Path `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.4 | 1.0 |
| `always_top1` | 0.636364 | 1.27675 | 0.636364 | 1.626669 | 0.0 |
| `always_top3` | 0.727273 | 2.026084 | 0.688026 | 1.809724 | 0.0 |
| `always_top5` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 2.026084 | 0.688026 | 1.809724 | 0.0 |
| `task_conditioned_budget_v0` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `path_aware_task_conditioned_budget_v0` | 0.909091 | 2.649124 | 0.763075 | 2.307177 | 0.0 |
| `oracle_current_target` | 1.0 | 1.753063 | 1.0 | 2.737041 | 0.0 |

## 논문 주장

- E002-M02 supports path-cost proxy policy comparison using the E001 denominator.
- E002-M02 does not support real navigation `SR` / `SPL`, collision-aware planning, or deployable search policy claims.

## 에이전트 추론

- Path-aware ordering is now directly comparable with semantic/non-persistent ordering under the same task-conditioned budget.
- If path-aware ordering lowers path cost but loses recall, that is a useful failure mode rather than a bug.
- Real navigation claims require replacing `euclidean_polyline_proxy_v0` with navmesh, occupancy, simulator, or robot trajectory cost.

## 사용자 판단 필요

- None for E002-M02. Continue to E002 claim-boundary summary or real path-cost source planning.

## Outputs

- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
