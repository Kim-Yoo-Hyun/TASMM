# E003-M06 Annotation Proposal Dropout

## Status

proposal_dropout_eval_ready

## 사실

- Input query rows: 294
- Input candidate rows: 1248
- Dropout seeds: 11, 17, 23
- Target drop rate: 0.15
- Non-target candidate drop rate: 0.25
- Noisy query rows: 1176
- Noisy candidate rows: 4208
- Prediction rows: 10584
- Failure rows: 1191
- Dropout target dropped rows: 77
- Dropout target dropped rate: 0.087302
- Dropout forced target-retained rows: 51
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M06_annotation_proposal_dropout_v0`

## Significant Moved `routine_fetch`

| Denominator | Policy | proxy `SR` | proposal recall | target dropped rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean all | `task_conditioned_budget_v0` | 0.727273 | 1.0 | 0.0 | 1.636364 | 0.681818 | 0.481818 |
| dropout target-retained | `task_conditioned_budget_v0` | 0.8 | 1.0 | 0.0 | 1.533333 | 0.733333 | 0.57 |
| dropout target-dropped | `task_conditioned_budget_v0` | 0.0 | 0.0 | 1.0 | 3.0 | 0.0 | -0.45 |
| dropout target-retained | `reachable_first_task_conditioned_budget_v0` | 0.766667 | 1.0 | 0.0 | 1.566667 | 0.716667 | 0.531667 |
| dropout target-dropped | `reachable_first_task_conditioned_budget_v0` | 0.0 | 0.0 | 1.0 | 3.0 | 0.0 | -0.45 |

## 논문 주장

- E003-M06 supports controlled annotation-proxy proposal-recall stress evaluation.
- E003-M06 supports separating target-retained and target-dropped denominators.
- E003-M06 does not support real RGB-D or open-vocabulary detector robustness.

## 에이전트 추론

- Target-dropped rows approximate detector proposal recall failure more directly than score/rank jitter.
- A positive retained-denominator result should not be mixed with target-dropped failures; both denominators are required.
- Since the selected route is repository-local artifact transformation, Docker is not required here; future detector/open-vocabulary implementation must be Dockerized.

## 사용자 판단 필요

- None for E003-M06. Next step should analyze dropout failure boundary or add a false-positive/centroid-jitter profile.

## Outputs

- `noise_manifest.jsonl`
- `noisy_query_rows.jsonl`
- `noisy_candidate_rows.jsonl`
- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
