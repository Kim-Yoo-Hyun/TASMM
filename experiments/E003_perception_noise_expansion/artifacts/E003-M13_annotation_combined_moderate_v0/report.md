# E003-M13 Annotation Combined Moderate

## Status

combined_moderate_eval_ready

## 사실

- Input query rows: 294
- Input candidate rows: 1248
- Combined seeds: 61, 67, 71
- Score jitter sigma: 0.08
- Target drop rate: 0.1
- Non-target drop rate: 0.2
- False-positive candidates per row: 1 to 2
- Centroid planar sigma m: 0.18
- Max planar jitter m: 0.5
- Noisy query rows: 1176
- Noisy candidate rows: 5419
- Prediction rows: 10584
- Failure rows: 1621
- Target dropped rows: 49 / 882
- False-positive added rows: 837 / 882
- Target pushed-down rows: 120 / 882
- Target rank changed rows: 185 / 882
- Target jitter exceeds threshold rows: 23 / 882
- Mean target centroid jitter m: 0.233738
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M13_annotation_combined_moderate_v0`

## Significant Moved `routine_fetch`

| Profile | Policy | rows | identity `SR` | localization `SR` | proposal recall | target dropped | false positive | jitter exceeded | `ExpectedSearchCost` | `AttemptSPL` | Utility |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | `task_conditioned_budget_v0` | 11 | 0.727273 | 0.727273 | 1.0 | 0.0 | 0.0 | 0.0 | 1.636364 | 0.681818 | 0.481818 |
| combined | `task_conditioned_budget_v0` | 33 | 0.212121 | 0.212121 | 0.969697 | 0.030303 | 0.727273 | 0.0 | 2.181818 | 0.19697 | -0.115152 |
| combined | `reachable_first_task_conditioned_budget_v0` | 33 | 0.606061 | 0.606061 | 0.969697 | 0.030303 | 0.727273 | 0.0 | 1.757576 | 0.575758 | 0.342424 |
| combined | `always_top5` | 33 | 0.787879 | 0.787879 | 0.969697 | 0.030303 | 0.727273 | 0.0 | 2.909091 | 0.45202 | 0.351515 |
| combined | `oracle_current_target` | 33 | 0.969697 | 0.969697 | 0.969697 | 0.030303 | 0.727273 | 0.0 | 1.0 | 0.969697 | 0.819697 |

## Required Boundaries

- Significant moved `routine_fetch` target-dropped `task_conditioned_budget_v0` rows: 1
- Target-dropped identity/localization `SR`: 0.0 / 0.0
- Significant moved `routine_fetch` jitter-exceeded `task_conditioned_budget_v0` rows: 0
- Jitter-exceeded identity/localization `SR`: None / None

## 논문 주장

- E003-M13 supports controlled annotation-proxy combined perception-like stress evaluation.
- E003-M13 combines proposal dropout, annotation-derived false positives, score/rank jitter, and centroid jitter.
- E003-M13 does not support real RGB-D perception robustness, open-vocabulary detector robustness, or real navigation `SR` / `SPL`.

## 에이전트 추론

- This is the first E003 profile where proposal recall, distractor contamination, rank noise, and localization noise interact in one denominator.
- Target-dropped and jitter-exceeded denominators must stay separate from the all-row aggregate.
- A boundary analysis should follow before using this result as a paper claim.

## 사용자 판단 필요

- None for E003-M13. Continue to E003-M14 combined-noise failure-boundary analysis unless redirected to Dockerized real proposal staging.

## Outputs

- `noise_manifest.jsonl`
- `noisy_query_rows.jsonl`
- `noisy_candidate_rows.jsonl`
- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
