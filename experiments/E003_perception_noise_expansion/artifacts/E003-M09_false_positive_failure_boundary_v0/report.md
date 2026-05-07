# E003-M09 False Positive Failure Boundary

## Status

false_positive_boundary_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0`
- Boundary rows: 7938
- Hard boundary rows: 231
- Stress query rows: 882
- False-positive added rows: 837
- Target pushed-down rows: 96
- Target pushed-down rate: 0.108844
- Same-label false positives: 0
- Semantic-group false positives: 648
- Fallback false positives: 1170
- Uses real RGB-D perception: False
- Uses open-vocabulary perception: False
- Uses real navigation: False
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M09_false_positive_failure_boundary_v0`

## Significant Moved `routine_fetch` Boundary

| Group | Policy | rows | clean `SR` | FP `SR` | delta `SR` | regressions | improvements | mean target-rank delta | cost delta | utility delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_pushed_down` | `always_top5` | 21 | 0.857143 | 0.571429 | -0.285714 | 6 | 0 | 2.0 | 1.571429 | -0.521429 |
| `target_pushed_down` | `task_conditioned_budget_v0` | 21 | 0.571429 | 0.0 | -0.571429 | 12 | 0 | 2.0 | 0.571429 | -0.657143 |
| `target_pushed_down` | `reachable_first_task_conditioned_budget_v0` | 21 | 0.571429 | 0.428571 | -0.142857 | 3 | 0 | 0.714286 | 0.142857 | -0.164286 |
| `target_pushed_down` | `oracle_current_target` | 21 | 1.0 | 1.0 | 0.0 | 0 | 0 | 2.0 | 0.0 | 0.0 |
| `false_positive_added_no_push` | `always_top5` | 3 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `false_positive_added_no_push` | `task_conditioned_budget_v0` | 3 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `false_positive_added_no_push` | `reachable_first_task_conditioned_budget_v0` | 3 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `false_positive_added_no_push` | `oracle_current_target` | 3 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `no_false_positive_available` | `always_top5` | 9 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `no_false_positive_available` | `task_conditioned_budget_v0` | 9 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `no_false_positive_available` | `reachable_first_task_conditioned_budget_v0` | 9 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| `no_false_positive_available` | `oracle_current_target` | 9 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | 0.0 |

## Reachable-First Comparison

- Significant moved `routine_fetch` rows: 33
- `task_conditioned_budget_v0` FP proxy `SR`: 0.363636
- `reachable_first_task_conditioned_budget_v0` FP proxy `SR`: 0.636364
- Reachable-first minus task proxy `SR` delta: 0.272727
- Reachable-first success gain rows: 9
- Reachable-first success loss rows: 0
- Reachable-first unreachable event delta: -0.181818

## Boundary Counts

- Primary policy boundary counts: {'false_positive_added_stable_success': 1443, 'false_positive_budget_regression': 27, 'false_positive_persistent_budget_boundary': 12, 'no_false_positive_available_stable_success': 90, 'target_push_budget_regression': 70, 'target_push_persistent_budget_boundary': 36, 'target_push_survived_budget': 86}
- Primary policy hard label counts: {'chair': 22, 'couch table': 9, 'desk': 6, 'gymnastic ball': 9, 'item': 9, 'pillow': 57, 'stool': 18, 'table': 6, 'vacuum': 9}

## 논문 주장

- E003-M09 supports controlled annotation-derived false-positive failure-boundary analysis.
- False-positive contamination causes recoverable and non-recoverable ranking/budget failures while preserving target presence.
- `reachable_first_task_conditioned_budget_v0` reduces the false-positive damage relative to `task_conditioned_budget_v0` in the significant moved `routine_fetch` subset.

## 에이전트 추론

- The current false positives are annotation-derived semantic-group or same-scene distractors; same-label false positives are not covered because E001 already includes same-label candidates.
- The result is a bridge toward perception-noise robustness, not a real open-vocabulary detector hallucination result.
- Target-pushed-down rows isolate budget/ranking sensitivity, but real RGB-D/open-vocabulary proposal generation is still required for detector claims.
- Next stress profile should be `annotation_centroid_jitter_v0`.
- Reason: Score/rank jitter, proposal dropout, and false-positive contamination are now covered; centroid jitter is the remaining controlled perception-like profile before combining profiles.

## Unsupported Claims

- real RGB-D perception robustness
- open-vocabulary detector hallucination robustness
- real navigation `SR` / `SPL`
- deployable search policy
- natural-language intention understanding

## 사용자 판단 필요

- None for E003-M09. Next implementation unit should start `annotation_centroid_jitter_v0` unless redirected to Dockerized real proposal generation.

## Outputs

- `boundary_rows.jsonl`
- `hard_boundary_rows.jsonl`
- `policy_delta_rows.jsonl`
- `summary.json`
- `claim_boundary.json`
- `coverage.json`
- `report.md`
