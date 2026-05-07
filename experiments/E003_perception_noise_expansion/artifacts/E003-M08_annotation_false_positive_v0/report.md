# E003-M08 Annotation False Positive Stress

## Status

false_positive_eval_ready

## 사실

- Input query rows: 294
- Input candidate rows: 1248
- False-positive seeds: 31, 37, 41
- Max false-positive candidates per row: 3
- Noisy query rows: 1176
- Noisy candidate rows: 6810
- Prediction rows: 10584
- Failure rows: 1067
- False-positive added rows: 837 / 882
- Target pushed-down rows: 96 / 882
- Same-label false positives: 0
- Semantic-group false positives: 648
- Fallback false positives: 1170
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M08_annotation_false_positive_v0`

## Significant Moved `routine_fetch`

| Profile | Policy | rows | proxy `SR` | target retained | FP added rate | target pushed-down rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched clean | `task_conditioned_budget_v0` | 24 | 0.625 | 1.0 | 0.0 | 0.0 | 1.75 | 0.625 | 0.3625 |
| false-positive | `task_conditioned_budget_v0` | 24 | 0.125 | 1.0 | 1.0 | 0.875 | 2.25 | 0.125 | -0.2125 |
| false-positive | `reachable_first_task_conditioned_budget_v0` | 24 | 0.5 | 1.0 | 1.0 | 0.875 | 1.875 | 0.5 | 0.21875 |
| false-positive | `always_top5` | 24 | 0.625 | 1.0 | 1.0 | 0.875 | 3.875 | 0.291666 | 0.04375 |
| false-positive | `oracle_current_target` | 24 | 1.0 | 1.0 | 1.0 | 0.875 | 1.0 | 1.0 | 0.85 |

## 논문 주장

- E003-M08 supports controlled annotation-derived false-positive contamination stress evaluation.
- E003-M08 keeps target presence fixed, so failures are ranking/budget contamination failures rather than proposal-recall failures.
- E003-M08 does not support real RGB-D or open-vocabulary detector hallucination robustness.

## 에이전트 추론

- False-positive contamination complements dropout because it adds distractors instead of removing them.
- Positive or negative effects must be separated from real detector hallucination claims because all added candidates still come from annotation-derived object candidates.
- The next unit should analyze false-positive failure boundaries before combining dropout, false positives, and centroid jitter.

## 사용자 판단 필요

- None for E003-M08. Continue to E003-M09 false-positive failure-boundary analysis unless redirected to Dockerized real proposal generation.

## Outputs

- `noise_manifest.jsonl`
- `noisy_query_rows.jsonl`
- `noisy_candidate_rows.jsonl`
- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
