# E003-M07 Dropout Failure Boundary

## Status

dropout_boundary_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0`
- Boundary rows: 7938
- Hard boundary rows: 294
- Dropout query rows: 882
- Natural target-retained rows: 754
- Forced-retained rows: 51
- Target-dropped rows: 77
- Reported target-retained rate: 0.912698
- Strict target-retained rate excluding forced rows: 0.854875
- Target-drop attempt rate including forced rows: 0.145125
- Uses real RGB-D perception: False
- Uses open-vocabulary perception: False
- Uses real navigation: False
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M07_dropout_failure_boundary_v0`

## Significant Moved `routine_fetch` Boundary

| Denominator | Policy | rows | clean `SR` | dropout `SR` | delta `SR` | regressions | improvements | mean rank delta | cost delta | utility delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `natural_target_retained` | `always_top5` | 28 | 0.892857 | 0.964286 | 0.071429 | 0 | 2 | -0.25 | -0.178571 | 0.098214 |
| `natural_target_retained` | `task_conditioned_budget_v0` | 28 | 0.75 | 0.785714 | 0.035714 | 0 | 1 | -0.25 | -0.035714 | 0.041071 |
| `natural_target_retained` | `reachable_first_task_conditioned_budget_v0` | 28 | 0.75 | 0.75 | 0.0 | 0 | 0 | -0.285714 | 0.0 | 0.0 |
| `natural_target_retained` | `oracle_current_target` | 28 | 1.0 | 1.0 | 0.0 | 0 | 0 | -0.25 | 0.0 | 0.0 |
| `forced_retained` | `always_top5` | 2 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `forced_retained` | `task_conditioned_budget_v0` | 2 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `forced_retained` | `reachable_first_task_conditioned_budget_v0` | 2 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `forced_retained` | `oracle_current_target` | 2 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `target_dropped` | `always_top5` | 3 | 1.0 | 0.0 | -1.0 | 3 | 0 | None | 1.666667 | -1.25 |
| `target_dropped` | `task_conditioned_budget_v0` | 3 | 0.333333 | 0.0 | -0.333333 | 1 | 0 | None | 0.666667 | -0.433333 |
| `target_dropped` | `reachable_first_task_conditioned_budget_v0` | 3 | 0.333333 | 0.0 | -0.333333 | 1 | 0 | None | 0.666667 | -0.433333 |
| `target_dropped` | `oracle_current_target` | 3 | 1.0 | 0.0 | -1.0 | 3 | 0 | None | 0.0 | -1.0 |

## Boundary Counts

- Primary policy boundary counts: {'forced_retained_artificial_recall_floor': 102, 'target_dropped_low_motion_static_memory_success': 62, 'target_dropped_proposal_recall_ceiling': 92, 'target_retained_distractor_dropout_improvement': 12, 'target_retained_persistent_budget_boundary': 26, 'target_retained_stable_success': 1470}
- Primary policy hard label counts: {'box': 4, 'chair': 78, 'pillow': 34, 'stool': 2}

## 논문 주장

- E003-M07 supports controlled annotation-proxy proposal-recall boundary analysis.
- Target-dropped rows should be treated as a proposal-recall ceiling, not as a recoverable memory-update failure.
- Forced-retained rows should be separated from strict target-retained robustness because they create an artificial recall floor.
- Target-retained dropout rows can test candidate-pruning sensitivity, but not false-positive contamination.

## 에이전트 추론

- Target-retained dropout can improve proxy SR by removing distractors, so positive retained-denominator results are not sufficient for perception robustness.
- The observed target-dropped failures motivate proposal recall accounting before claiming real RGB-D/open-vocabulary robustness.
- The current route remains annotation-proxy and should be described as a bridge experiment.
- Next stress profile should be `annotation_false_positive_v0`.
- Reason: Dropout removes candidates and can make ranking easier; false-positive contamination tests the opposite and is closer to open-vocabulary proposal hallucination.

## Unsupported Claims

- real RGB-D perception robustness
- open-vocabulary detector robustness
- deployable search policy
- real navigation `SR` / `SPL`
- recovery when the true target is absent from all current proposals

## 사용자 판단 필요

- None for E003-M07. Next implementation unit should start `annotation_false_positive_v0` unless the route is redirected to Dockerized real proposal generation.

## Outputs

- `boundary_rows.jsonl`
- `hard_boundary_rows.jsonl`
- `policy_delta_rows.jsonl`
- `summary.json`
- `claim_boundary.json`
- `coverage.json`
- `report.md`
