# E003-M14 Combined Noise Failure Boundary

## Status

combined_noise_boundary_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0`
- Boundary rows: 7938
- Hard boundary rows: 521
- Stress query rows: 882
- Target dropped rows: 49
- False-positive added rows: 837
- Target pushed-down rows: 120
- Target rank changed rows: 185
- Target jitter exceeds threshold rows: 23
- Mean target centroid jitter m: 0.233738
- Combined group counts: {'candidate_dropout_or_score_shift': 27, 'centroid_localization_exceeded': 23, 'false_positive_added_no_push': 604, 'false_positive_target_pushed_down': 117, 'rank_budget_shift_no_push': 62, 'target_dropped': 49}
- Uses real RGB-D perception: False
- Uses open-vocabulary perception: False
- Uses real navigation: False
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M14_combined_noise_failure_boundary_v0`

## Significant Moved `routine_fetch` Boundary

| Group | Policy | rows | identity `SR` | localization `SR` | identity delta | localization delta | target drop | target push | rank changed | jitter exceeded | cost delta | utility delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| target_dropped | `task_conditioned_budget_v0` | 1 | 0.0 | 0.0 | -1.0 | -1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 2.0 | -1.3 |
| target_dropped | `reachable_first_task_conditioned_budget_v0` | 1 | 0.0 | 0.0 | -1.0 | -1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 2.0 | -1.3 |
| target_dropped | `always_top5` | 1 | 0.0 | 0.0 | -1.0 | -1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 5.0 | -1.75 |
| target_dropped | `oracle_current_target` | 1 | 0.0 | 0.0 | -1.0 | -1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | -1.0 |
| false_positive_target_pushed_down | `task_conditioned_budget_v0` | 17 | 0.0 | 0.0 | -0.823529 | -0.823529 | 0.0 | 1.0 | 1.0 | 0.0 | 0.823529 | -0.947059 |
| false_positive_target_pushed_down | `reachable_first_task_conditioned_budget_v0` | 17 | 0.647059 | 0.647059 | -0.176471 | -0.176471 | 0.0 | 1.0 | 1.0 | 0.0 | 0.176471 | -0.202941 |
| false_positive_target_pushed_down | `always_top5` | 17 | 0.823529 | 0.823529 | -0.117647 | -0.117647 | 0.0 | 1.0 | 1.0 | 0.0 | 1.0 | -0.267647 |
| false_positive_target_pushed_down | `oracle_current_target` | 17 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| rank_budget_shift_no_push | `task_conditioned_budget_v0` | 5 | 0.0 | 0.0 | -0.4 | -0.4 | 0.0 | 0.0 | 1.0 | 0.0 | 0.4 | -0.46 |
| rank_budget_shift_no_push | `reachable_first_task_conditioned_budget_v0` | 5 | 0.4 | 0.4 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | -0.2 | 0.03 |
| rank_budget_shift_no_push | `always_top5` | 5 | 0.6 | 0.6 | -0.2 | -0.2 | 0.0 | 0.0 | 1.0 | 0.0 | 0.4 | -0.26 |
| rank_budget_shift_no_push | `oracle_current_target` | 5 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| false_positive_added_no_push | `task_conditioned_budget_v0` | 4 | 0.25 | 0.25 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| false_positive_added_no_push | `reachable_first_task_conditioned_budget_v0` | 4 | 0.25 | 0.25 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| false_positive_added_no_push | `always_top5` | 4 | 0.75 | 0.75 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| false_positive_added_no_push | `oracle_current_target` | 4 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| candidate_dropout_or_score_shift | `task_conditioned_budget_v0` | 6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| candidate_dropout_or_score_shift | `reachable_first_task_conditioned_budget_v0` | 6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| candidate_dropout_or_score_shift | `always_top5` | 6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| candidate_dropout_or_score_shift | `oracle_current_target` | 6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Reachable-First vs Task-Conditioned

- Significant moved `routine_fetch` paired rows: 33
- `task_conditioned_budget_v0` combined identity `SR`: 0.212121
- `reachable_first_task_conditioned_budget_v0` combined identity `SR`: 0.606061
- Identity `SR` delta reachable-first minus task: 0.393939
- Localization `SR` delta reachable-first minus task: 0.393939
- Reachable-first identity gain rows: 13
- Reachable-first identity loss rows: 0
- Returned-unreachable event delta reachable-first minus task: -0.151515

## Boundary Counts

- Primary policy boundary counts: {'budget_identity_regression': 8, 'candidate_dropout_or_score_shift_survived': 54, 'combined_identity_improvement': 1, 'false_positive_added_survived': 1189, 'false_positive_push_budget_identity_regression': 84, 'false_positive_push_survived': 129, 'false_positive_push_unexpected_identity_improvement': 2, 'identity_success_over_jitter_localization_failure': 22, 'persistent_budget_localization_boundary': 20, 'persistent_false_positive_push_budget_boundary': 19, 'rank_shift_budget_identity_regression': 11, 'rank_shift_identity_improvement': 6, 'rank_shift_survived': 99, 'stable_combined_success': 22, 'target_dropped_proposal_recall_ceiling': 50, 'target_dropped_static_memory_or_control_success': 48}
- Primary policy hard label counts: {'box': 2, 'chair': 85, 'couch table': 11, 'desk': 5, 'gymnastic ball': 13, 'item': 13, 'pillow': 57, 'rocking chair': 2, 'stool': 20, 'table': 4, 'trash can': 2, 'vacuum': 9}

## 논문 주장

- E003-M14 supports controlled annotation-proxy combined-noise failure-boundary analysis.
- Combined stress exposes separable proposal-recall, distractor rank/budget, and centroid-localization boundaries.
- `reachable_first_task_conditioned_budget_v0` improves significant moved `routine_fetch` identity/localization success relative to `task_conditioned_budget_v0` under the combined annotation-proxy stress profile.

## 에이전트 추론

- The current combined profile uses annotation-derived proxy perturbations, not real RGB-D or open-vocabulary detector proposals.
- Target-dropped rows are proposal-recall ceiling cases and should not be counted as recoverable stale-memory policy failures.
- False positives are annotation-derived semantic-group or fallback distractors; same-label detector hallucinations are not covered.
- Occupancy-grid reachability is reused by instance id and is not recomputed after centroid perturbation.
- Current `ExpectedSearchCost`, `AttemptSPL`, and `SR` are proxy metrics, not real navigation `SPL` or execution `SR`.

## Unsupported Claims

- real RGB-D perception robustness
- open-vocabulary detector robustness
- real navigation `SR` / `SPL`
- deployable search policy
- natural-language intention understanding

## 사용자 판단 필요

- None for E003-M14. Next unit should consolidate the controlled perception-robustness claim before any Dockerized real proposal route.

## Outputs

- `boundary_rows.jsonl`
- `hard_boundary_rows.jsonl`
- `policy_delta_rows.jsonl`
- `summary.json`
- `claim_boundary.json`
- `coverage.json`
- `report.md`
