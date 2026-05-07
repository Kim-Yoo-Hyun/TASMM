# E003-M04 Robustness Failure Analysis

## Status

robustness_boundary_ready

## 사실

- Transition rows: 2646
- Hard failure rows: 29
- Reference profile: `clean_annotation_oracle_v0`
- Stress profile: `annotation_score_jitter_v0`
- Target-drop profiles included: False
- Uses real RGB-D perception: False
- Uses open-vocabulary perception: False
- Uses real navigation: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M04_robustness_failure_analysis_v0`

## Significant Moved `routine_fetch` Delta

| Policy | clean `SR` | stress `SR` | delta `SR` | noise regressions | cost delta | `AttemptSPL` delta | utility delta | unreachable event delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `always_top1` | 0.636364 | 0.545455 | -0.090909 | 1 | 0.090909 | -0.090909 | -0.104545 | 0 |
| `always_top3` | 0.727273 | 0.636364 | -0.090909 | 1 | 0.272727 | -0.090909 | -0.131818 | 0 |
| `always_top5` | 0.909091 | 1.0 | 0.090909 | 0 | 0.090909 | -0.045455 | 0.077273 | 1 |
| `task_conditioned_budget_v0` | 0.727273 | 0.636364 | -0.090909 | 1 | 0.181818 | -0.090909 | -0.118182 | 0 |
| `reachable_first_task_conditioned_budget_v0` | 0.727273 | 0.636364 | -0.090909 | 1 | 0.181818 | -0.090909 | -0.118182 | 0 |

## Hard Boundary

- `task_conditioned_budget_v0` significant moved `routine_fetch` delta `SR`: -0.090909
- `task_conditioned_budget_v0` significant moved `routine_fetch` noise regression rows: 1
- `reachable_first_task_conditioned_budget_v0` significant moved `routine_fetch` delta `SR`: -0.090909
- `reachable_first_task_conditioned_budget_v0` stress-vs-clean returned-unreachable event delta: 0
- Noisy `reachable_first_task_conditioned_budget_v0` vs noisy `task_conditioned_budget_v0` returned-unreachable event delta: -0.181818
- Noisy `reachable_first_task_conditioned_budget_v0` vs noisy `task_conditioned_budget_v0` proxy `SR` delta: 0.0
- Primary hard label counts: 29 rows total; see `hard_failure_rows.jsonl`.

## 논문 주장

- E003 currently supports controlled annotation-proxy ranking-noise evaluation.
- `task_conditioned_budget_v0` and `reachable_first_task_conditioned_budget_v0` keep target-retained denominators explicit under score/rank perturbation.
- `reachable_first_task_conditioned_budget_v0` can reduce returned-unreachable attempts, but this is an occupancy-grid proxy effect.

## 에이전트 추론

- Ranking noise causes measurable proxy SR and utility degradation for `task_conditioned_budget_v0` on significant moved `routine_fetch` rows.
- The reachable-first variant lowers unreachable returns but does not recover the observed ranking-noise success drop.
- `always_top5` can be more robust to target-preserving ranking noise at the cost of larger candidate budgets.

## Unsupported Claims

- real RGB-D perception robustness
- open-vocabulary perception robustness
- real navigation `SR` / `SPL`
- detector proposal recall robustness
- natural-language intention understanding

## 사용자 판단 필요

- None for M04. The next implementation choice is whether E003-M05 stages real proposal sources or adds another controlled annotation-proxy stress profile.

## Outputs

- `transition_rows.jsonl`
- `hard_failure_rows.jsonl`
- `policy_delta_rows.jsonl`
- `summary.json`
- `claim_boundary.json`
- `coverage.json`
- `report.md`
