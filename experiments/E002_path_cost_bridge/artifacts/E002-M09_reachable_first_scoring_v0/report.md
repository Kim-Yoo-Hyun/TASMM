# E002-M09 Reachable-First Semantic Grid Scoring

## Status

reachable_first_scoring_gate_pass

## 사실

- Target-reachable eval rows: 267
- Strict all-candidates-reachable rows: 198
- Reachable-first prediction rows: 267
- Target-reachable success loss rows: 0
- Target-reachable success gain rows: 0
- Target-reachable returned-unreachable delta total: -6
- Output directory: `/home/yoohyun/research2/experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0`

## Target-Reachable Significant Moved Rows

### `routine_fetch`

| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate | Returned-unreachable count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `task_conditioned_budget_v0` | 9 | 0.777778 | 1.415195 | 0.760261 | 0.565498 | 0.111111 | 1 |
| `reachable_first_task_conditioned_budget_v0` | 9 | 0.777778 | 1.304084 | 0.760261 | 0.582165 | 0.0 | 0 |

### `high_value_fetch`

| Policy | Rows | grid proxy `SR` | Grid cost | Grid `AttemptSPL` | Utility | Returned-unreachable rate | Returned-unreachable count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `task_conditioned_budget_v0` | 9 | 0.888889 | 2.88009 | 0.804277 | 2.206875 | 0.111111 | 1 |
| `reachable_first_task_conditioned_budget_v0` | 9 | 0.888889 | 2.768979 | 0.815817 | 2.223542 | 0.111111 | 1 |

## Gate Summary

| Scope | Rows | Success loss | Success gain | Returned-unreachable delta | Mean cost delta | Mean utility delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `target_reachable_eval` | 267 | 0 | 0 | -6 | -0.018727 | 0.002809 | True |

## 논문 주장

- E002-M09 supports reachable-first semantic grid scoring only as a source-filtered grid-path proxy revision.
- E002-M09 can support a returned-unreachable reduction claim if the gate passes with zero success loss.
- E002-M09 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.

## 에이전트 추론

- This revision is safer than naive grid-path ordering because it preserves semantic rank among reachable candidates and only demotes grid-unreachable candidates.
- A positive M09 result should be treated as method cleanup for E002, not as the main paper contribution by itself.

## 사용자 판단 필요

- None for E002-M09. If accepted, the next experiment can move to E003 perception-noise expansion.

## Outputs

- `reachable_first_predictions.jsonl`
- `comparison_rows.jsonl`
- `strict_comparison_rows.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
