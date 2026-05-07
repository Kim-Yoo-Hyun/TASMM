# E001-M04 Failure Analysis

## Status

claim_boundary_ready

## 사실

- Prediction rows: 2352
- Failure rows: 184
- `task_conditioned_budget_v0` failure rows: 7
- Hard case rows written: 7
- Output directory: `/home/yoohyun/research2/experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0`

## Failure Types

| Failure type | Count |
| --- | ---: |
| `stale_old_location_returned` | 33 |
| `static_map_localization_error` | 57 |
| `target_outside_returned_budget` | 94 |

## Method Failures

| Context / band / failure | Count |
| --- | ---: |
| `high_value_fetch|significant_moved|target_outside_returned_budget` | 1 |
| `noisy_high_value_fetch|significant_moved|target_outside_returned_budget` | 1 |
| `routine_fetch|mid_motion_review|target_outside_returned_budget` | 2 |
| `routine_fetch|significant_moved|target_outside_returned_budget` | 3 |

## Method vs Baselines

| Baseline | Method success / baseline fail | Baseline success / method fail | Utility delta | Cost delta | proxy `SR` delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 83 | 0 | 0.742007 | -0.105442 | 0.282313 |
| `label_nearest_current_observation` | 23 | 0 | 0.20119 | 0.098639 | 0.078231 |
| `always_top1` | 23 | 0 | 0.20119 | 0.098639 | 0.078231 |
| `always_top3` | 6 | 1 | 0.061905 | 0.006803 | 0.017007 |
| `always_top5` | 0 | 4 | -0.010034 | -0.02381 | -0.013605 |
| `fixed_uncertainty_topk_v0` | 6 | 1 | 0.061905 | 0.006803 | 0.017007 |
| `oracle_current_target` | 0 | 7 | -0.069218 | 0.20068 | -0.02381 |

## 논문 주장

Safe claims:
- E001 supports annotation-level semantic-pair dynamic object search proxy evaluation on locally ready 3RScan/3DSSG pairs.
- On significant moved rows, task_conditioned_budget_v0 suppresses stale old-location false positives relative to scene_aligned_static_map.
- Structured task context changes the search budget and creates a routine-vs-high-value tradeoff in proxy SR and ExpectedSearchCost.
- Low-motion rows are preserved under task_conditioned_budget_v0 in the current E001 data.

Unsupported claims:
- real navigation SR/SPL
- path-cost-aware search policy
- RGB-D perception robustness
- open-vocabulary perception robustness
- natural-language intention understanding
- learned task policy
- full 3RScan/3DSSG benchmark-scale conclusion

## 에이전트 추론

- E001 is useful as a clean proxy benchmark and denominator, but it is not yet a top-tier-complete embodied result.
- The current method's main weakness is not stale old-location suppression; it is candidate-budget misses under bounded routine search.
- E002 should convert candidate-count cost into path/search cost before any navigation-style claim.
- E003 should replace `annotation_semseg` candidates before any perception robustness claim.

## 사용자 판단 필요

- No immediate decision is required. The next TODO can be additional staging or E002 path-cost preparation.

## Outputs

- `failure_summary.json`
- `claim_boundary.json`
- `hard_cases.jsonl`
- `report.md`
