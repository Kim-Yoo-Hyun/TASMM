# E003-M03 Noisy Policy Evaluation

## Status

noisy_policy_eval_ready

## 사실

- Input directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M02_annotation_proxy_noise_v0`
- Noisy query rows: 588
- Noisy candidate rows: 2496
- Prediction rows: 5292
- Failure rows: 466
- Profiles: `clean_annotation_oracle_v0`, `annotation_score_jitter_v0`
- Candidate grid signal rows: 2496
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M03_noisy_policy_eval_v0`

## Significant Moved `routine_fetch`

### `clean_annotation_oracle_v0`

| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 2.0 | 0.0 | -0.3 | 1.0 |
| `always_top1` | 0.636364 | 1.363636 | 0.636364 | 0.431818 | 0.0 |
| `always_top3` | 0.727273 | 1.909091 | 0.681818 | 0.440909 | 0.0 |
| `always_top5` | 0.909091 | 2.181818 | 0.722727 | 0.581818 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.727273 | 1.909091 | 0.681818 | 0.440909 | 0.0 |
| `task_conditioned_budget_v0` | 0.727273 | 1.636364 | 0.681818 | 0.481818 | 0.0 |
| `reachable_first_task_conditioned_budget_v0` | 0.727273 | 1.636364 | 0.681818 | 0.481818 | 0.0 |
| `oracle_current_target` | 1.0 | 1.0 | 1.0 | 0.85 | 0.0 |

### `annotation_score_jitter_v0`

| Policy | proxy `SR` | `ExpectedSearchCost` | `AttemptSPL` | Utility | Stale FP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 2.0 | 0.0 | -0.3 | 1.0 |
| `always_top1` | 0.545455 | 1.454545 | 0.545455 | 0.327273 | 0.0 |
| `always_top3` | 0.636364 | 2.181818 | 0.590909 | 0.309091 | 0.0 |
| `always_top5` | 1.0 | 2.272727 | 0.677273 | 0.659091 | 0.0 |
| `fixed_uncertainty_topk_v0` | 0.636364 | 2.181818 | 0.590909 | 0.309091 | 0.0 |
| `task_conditioned_budget_v0` | 0.636364 | 1.818182 | 0.590909 | 0.363636 | 0.0 |
| `reachable_first_task_conditioned_budget_v0` | 0.636364 | 1.818182 | 0.590909 | 0.363636 | 0.0 |
| `oracle_current_target` | 1.0 | 1.0 | 1.0 | 0.85 | 0.0 |

## Robustness Delta

`annotation_score_jitter_v0` minus `clean_annotation_oracle_v0` for significant moved `routine_fetch`:

| Policy | Delta proxy `SR` | Delta cost | Delta `AttemptSPL` | Delta utility |
| --- | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.0 | 0.0 | 0.0 | 0.0 |
| `always_top1` | -0.090909 | 0.090909 | -0.090909 | -0.104545 |
| `always_top3` | -0.090909 | 0.272727 | -0.090909 | -0.131818 |
| `always_top5` | 0.090909 | 0.090909 | -0.045454 | 0.077273 |
| `fixed_uncertainty_topk_v0` | -0.090909 | 0.272727 | -0.090909 | -0.131818 |
| `task_conditioned_budget_v0` | -0.090909 | 0.181818 | -0.090909 | -0.118182 |
| `reachable_first_task_conditioned_budget_v0` | -0.090909 | 0.181818 | -0.090909 | -0.118182 |
| `oracle_current_target` | 0.0 | 0.0 | 0.0 | 0.0 |

## 논문 주장

- E003-M03 supports evaluating controlled annotation-proxy ranking-noise robustness.
- E003-M03 does not support real RGB-D or open-vocabulary perception robustness.
- E003-M03 does not support real navigation `SR` / `SPL`.

## 에이전트 추론

- Since target presence is preserved, metric changes isolate rank/candidate-order robustness rather than proposal recall.
- `reachable_first_task_conditioned_budget_v0` uses E002 grid reachability only as an auxiliary candidate-order signal, not as real navigation execution.
- E003-M04 should summarize robustness boundaries before adding target dropout or false-positive profiles.

## 사용자 판단 필요

- None for E003-M03. Continue to E003-M04 robustness/failure analysis.

## Outputs

- `predictions.jsonl`
- `failure_rows.jsonl`
- `metrics.json`
- `coverage.json`
- `report.md`
