# E003-M10 Annotation Centroid Jitter

## Status

centroid_jitter_eval_ready

## 사실

- Input query rows: 294
- Input candidate rows: 1248
- Centroid jitter seeds: 43, 47, 53
- Planar sigma m: 0.25
- Max planar jitter m: 0.75
- Noisy query rows: 1176
- Noisy candidate rows: 4992
- Prediction rows: 10584
- Failure rows: 1654
- Target rank changed rows: 139 / 882
- Target jitter exceeds threshold rows: 123 / 882
- Mean target centroid jitter m: 0.313896
- Mean target planar jitter m: 0.308592
- Grid path recomputed for centroid jitter: False
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0`

## Significant Moved `routine_fetch`

| Profile | Policy | rows | identity `SR` | localization `SR` | target jitter exceed rate | rank changed rate | `ExpectedSearchCost` | `AttemptSPL` | Utility |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | `task_conditioned_budget_v0` | 11 | 0.727273 | 0.727273 | 0.0 | 0.0 | 1.636364 | 0.681818 | 0.481818 |
| centroid-jitter | `task_conditioned_budget_v0` | 33 | 0.69697 | 0.606061 | 0.090909 | 0.30303 | 1.757576 | 0.621212 | 0.433333 |
| centroid-jitter | `reachable_first_task_conditioned_budget_v0` | 33 | 0.69697 | 0.606061 | 0.090909 | 0.30303 | 1.757576 | 0.621212 | 0.433333 |
| centroid-jitter | `always_top5` | 33 | 0.878788 | 0.787879 | 0.090909 | 0.30303 | 2.363636 | 0.663636 | 0.524242 |
| centroid-jitter | `oracle_current_target` | 33 | 1.0 | 0.909091 | 0.090909 | 0.30303 | 1.0 | 1.0 | 0.85 |

## Threshold-Exceeded Subset

- Significant moved `routine_fetch` `task_conditioned_budget_v0` threshold-exceeded rows: 3
- Threshold-exceeded identity `SR`: 1.0
- Threshold-exceeded localization `SR`: 0.0

## 논문 주장

- E003-M10 supports controlled annotation-proxy centroid localization jitter stress evaluation.
- E003-M10 separates identity/rank success from localization success under jittered candidate centroids.
- E003-M10 does not support real RGB-D localization noise or real navigation `SR` / `SPL`.

## 에이전트 추론

- Centroid jitter is the missing individual controlled perception-like profile after rank jitter, proposal dropout, and false-positive contamination.
- `localization_proxy_sr` is stricter than identity `SR` because returning the correct target with an over-jittered centroid is not counted as localized success.
- Occupancy-grid path costs are not recomputed after jitter; this run should be followed by a boundary analysis before any combined-noise profile.

## 사용자 판단 필요

- None for E003-M10. Continue to E003-M11 centroid-jitter failure-boundary analysis unless redirected to Dockerized real proposal generation.

## Outputs

- `noise_manifest.jsonl`
- `noisy_query_rows.jsonl`
- `noisy_candidate_rows.jsonl`
- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
