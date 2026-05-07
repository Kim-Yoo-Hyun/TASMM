# E002-M06 Grid Path Policy Evaluation

## Status

grid_path_policy_eval_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0`
- Query rows: 294
- Prediction rows: 2646
- Failure rows: 387
- Grid path-cost profile: `occupancy_grid_astar_v0`
- Target grid reachable rows: 267
- Real navigation path-cost rows: 0
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0`

## Significant Moved Rows

### `routine_fetch`

| Policy | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Stale FP | Target unreachable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.15 | 1.0 | 0.181818 |
| `always_top1` | 0.545455 | 0.860628 | 0.545455 | 0.41636 | 0.0 | 0.181818 |
| `always_top3` | 0.636364 | 1.644116 | 0.622032 | 0.389746 | 0.0 | 0.181818 |
| `always_top5` | 0.727273 | 2.810983 | 0.658045 | 0.305625 | 0.0 | 0.181818 |
| `fixed_uncertainty_topk_v0` | 0.636364 | 1.644116 | 0.622032 | 0.389746 | 0.0 | 0.181818 |
| `task_conditioned_budget_v0` | 0.636364 | 1.339705 | 0.622032 | 0.435408 | 0.0 | 0.181818 |
| `grid_path_aware_task_conditioned_budget_v0` | 0.545455 | 1.370743 | 0.501318 | 0.339843 | 0.0 | 0.181818 |
| `oracle_current_target` | 0.818182 | 1.588279 | 0.818182 | 0.57994 | 0.0 | 0.181818 |

### `high_value_fetch`

| Policy | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Stale FP | Target unreachable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.4 | 1.0 | 0.181818 |
| `always_top1` | 0.545455 | 0.860628 | 0.545455 | 1.393633 | 0.0 | 0.181818 |
| `always_top3` | 0.636364 | 1.644116 | 0.622032 | 1.571564 | 0.0 | 0.181818 |
| `always_top5` | 0.727273 | 2.810983 | 0.658045 | 1.691989 | 0.0 | 0.181818 |
| `fixed_uncertainty_topk_v0` | 0.636364 | 1.644116 | 0.622032 | 1.571564 | 0.0 | 0.181818 |
| `task_conditioned_budget_v0` | 0.727273 | 2.810983 | 0.658045 | 1.691989 | 0.0 | 0.181818 |
| `grid_path_aware_task_conditioned_budget_v0` | 0.727273 | 3.063701 | 0.593735 | 1.654081 | 0.0 | 0.181818 |
| `oracle_current_target` | 0.818182 | 1.588279 | 0.818182 | 2.170849 | 0.0 | 0.181818 |

### `noisy_high_value_fetch`

| Policy | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Stale FP | Target unreachable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 1.0 | 0.0 | -0.4 | 1.0 | 0.181818 |
| `always_top1` | 0.545455 | 0.860628 | 0.545455 | 1.393633 | 0.0 | 0.181818 |
| `always_top3` | 0.636364 | 1.644116 | 0.622032 | 1.571564 | 0.0 | 0.181818 |
| `always_top5` | 0.727273 | 2.810983 | 0.658045 | 1.691989 | 0.0 | 0.181818 |
| `fixed_uncertainty_topk_v0` | 0.636364 | 1.644116 | 0.622032 | 1.571564 | 0.0 | 0.181818 |
| `task_conditioned_budget_v0` | 0.727273 | 2.810983 | 0.658045 | 1.691989 | 0.0 | 0.181818 |
| `grid_path_aware_task_conditioned_budget_v0` | 0.727273 | 3.063701 | 0.593735 | 1.654081 | 0.0 | 0.181818 |
| `oracle_current_target` | 0.818182 | 1.588279 | 0.818182 | 2.170849 | 0.0 | 0.181818 |

## 논문 주장

- E002-M06 supports policy comparison under `occupancy_grid_astar_v0` free-space path-cost proxy.
- E002-M06 does not support real navigation `SR` / `SPL`, simulator execution, collision-aware robot planning, or deployable search policy claims.

## 에이전트 추론

- The useful comparison is against `oracle_current_target`, because target-unreachable rows lower the grid upper bound.
- Grid-aware ordering is now directly testable against semantic ranking under the same task-conditioned budget.
- Rows with unreachable targets should be analyzed as grid/source limitations before using them as method failures.

## 사용자 판단 필요

- None for E002-M06. Continue to failure/source analysis or E003 perception-noise expansion.

## Outputs

- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
