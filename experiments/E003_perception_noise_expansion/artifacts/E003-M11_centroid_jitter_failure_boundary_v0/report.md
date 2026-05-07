# E003-M11 Centroid Jitter Failure Boundary

## Status

centroid_jitter_boundary_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M10_annotation_centroid_jitter_v0`
- Boundary rows: 7938
- Hard boundary rows: 173
- Stress query rows: 882
- Target jitter exceeds threshold rows: 123
- Target jitter exceeds threshold rate: 0.139456
- Target rank changed rows: 139
- Target rank changed rate: 0.157596
- Mean target centroid jitter m: 0.313896
- Mean target planar jitter m: 0.308592
- Grid path recomputed for centroid jitter: False
- Uses real RGB-D perception: False
- Uses open-vocabulary perception: False
- Uses real navigation: False
- Docker required: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M11_centroid_jitter_failure_boundary_v0`

## Significant Moved `routine_fetch` Boundary

| Group | Policy | rows | identity `SR` | localization `SR` | localization delta | identity-localization gap | identity regressions | localization regressions | mean jitter m |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| target_jitter_exceeds_threshold | `task_conditioned_budget_v0` | 3 | 1.0 | 0.0 | -1.0 | 1.0 | 0 | 3 | 0.697119 |
| target_jitter_exceeds_threshold | `reachable_first_task_conditioned_budget_v0` | 3 | 1.0 | 0.0 | -1.0 | 1.0 | 0 | 3 | 0.697119 |
| target_jitter_exceeds_threshold | `always_top5` | 3 | 1.0 | 0.0 | -1.0 | 1.0 | 0 | 3 | 0.697119 |
| target_jitter_exceeds_threshold | `oracle_current_target` | 3 | 1.0 | 0.0 | -1.0 | 1.0 | 0 | 3 | 0.697119 |
| target_rank_changed_within_threshold | `task_conditioned_budget_v0` | 10 | 0.3 | 0.3 | -0.1 | 0.0 | 1 | 1 | 0.284108 |
| target_rank_changed_within_threshold | `reachable_first_task_conditioned_budget_v0` | 10 | 0.3 | 0.3 | -0.1 | 0.0 | 1 | 1 | 0.284108 |
| target_rank_changed_within_threshold | `always_top5` | 10 | 0.8 | 0.8 | -0.1 | 0.0 | 2 | 2 | 0.284108 |
| target_rank_changed_within_threshold | `oracle_current_target` | 10 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.284108 |
| candidate_rank_changed_only | `task_conditioned_budget_v0` | 8 | 0.625 | 0.625 | 0.0 | 0.0 | 0 | 0 | 0.174045 |
| candidate_rank_changed_only | `reachable_first_task_conditioned_budget_v0` | 8 | 0.625 | 0.625 | 0.0 | 0.0 | 0 | 0 | 0.174045 |
| candidate_rank_changed_only | `always_top5` | 8 | 0.75 | 0.75 | 0.0 | 0.0 | 0 | 0 | 0.174045 |
| candidate_rank_changed_only | `oracle_current_target` | 8 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.174045 |
| within_threshold_rank_stable | `task_conditioned_budget_v0` | 12 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.232741 |
| within_threshold_rank_stable | `reachable_first_task_conditioned_budget_v0` | 12 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.232741 |
| within_threshold_rank_stable | `always_top5` | 12 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.232741 |
| within_threshold_rank_stable | `oracle_current_target` | 12 | 1.0 | 1.0 | 0.0 | 0.0 | 0 | 0 | 0.232741 |

## Reachable-First vs Task-Conditioned

- Significant moved `routine_fetch` paired rows: 33
- Identity `SR` delta reachable-first minus task: 0.0
- Localization `SR` delta reachable-first minus task: 0.0
- Returned-unreachable event delta reachable-first minus task: -0.151515
- Reachable-first localization gain rows: 0
- Reachable-first localization loss rows: 0

## 논문 주장
- E003-M11 supports controlled annotation-proxy centroid-jitter failure-boundary analysis.
- Identity retrieval and spatial localization should be reported as separate success metrics under centroid noise.
- Correct-target identity success can still become localization failure when target centroid jitter exceeds the success threshold.

## 에이전트 추론

- Centroid jitter creates a measurable gap between correct-target identity retrieval and spatial localization.
- The current reachable-first policy mainly changes unreachable-return behavior; it does not improve identity or localization success under this centroid-jitter profile.
- Because grid path costs are not recomputed after centroid perturbation, this result should stay a controlled localization-noise proxy rather than a navigation claim.

## 사용자 판단 필요

- None for E003-M11. Continue to E003-M12 combined-noise route decision unless redirected to Dockerized real proposal generation.

## Outputs

- `boundary_rows.jsonl`
- `hard_boundary_rows.jsonl`
- `policy_delta_rows.jsonl`
- `summary.json`
- `claim_boundary.json`
- `coverage.json`
- `report.md`
