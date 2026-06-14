# Results

## 사실

Latest strict artifact:

- Validated pairs: 12.
- Query rows: 94.
- Significant moved rows: 10.
- Low-motion controls: 48.
- Mid-motion review rows: 36.
- Rank-sensitive rows: 58.
- High-ambiguity rows: 37.
- Status: `strict_pass`.

Significant moved metrics:

| Policy | Top-1 / exact | Recall@3 | Stale FP | Mean search cost |
| --- | ---: | ---: | ---: | ---: |
| `label_nearest_current_observation` | 0.600000 | 0.700000 | 0.000000 | n/a |
| `label_top3_current_observation` | 0.000000 | 0.700000 | 0.000000 | n/a |
| `non_persistent_anchor_v0` | 0.800000 | 1.000000 | 0.000000 | 1.300000 |
| `uncertainty_topk_v0` | 0.800000 | 1.000000 | 0.000000 | 1.300000 |

Low-motion controls under `uncertainty_topk_v0`:

- static preserved: 1.000000.
- forced re-observation: 0.000000.

Search-cost bridge on significant moved rows:

| Policy | Proxy search success | `AttemptSPL` proxy | Mean checked locations | Stale dead-end |
| --- | ---: | ---: | ---: | ---: |
| `scene_aligned_static_map` | 0.000000 | 0.000000 | 2.000000 | 1.000000 |
| `label_nearest_current_observation` | 0.600000 | 0.600000 | 1.400000 | 0.000000 |
| `label_top3_current_observation` | 0.700000 | 0.650000 | 2.000000 | 0.000000 |
| `non_persistent_anchor_v0` | 0.800000 | 0.800000 | 1.200000 | 0.000000 |
| `uncertainty_topk_v0` | 1.000000 | 0.883333 | 1.300000 | 0.000000 |

Search-cost bridge on high-ambiguity significant rows:

- `uncertainty_topk_v0` proxy search success: 1.000000.
- `non_persistent_anchor_v0` proxy search success: 0.666667.
- `label_top3_current_observation` proxy search success: 0.500000.
- `scene_aligned_static_map` stale dead-end: 1.000000.

Perception-noise gate on significant moved rows:

| Scenario | Policy | Observable-target success | `AttemptSPL` proxy | Mean checked locations | Overall success |
| --- | --- | ---: | ---: | ---: | ---: |
| `ranking_noise_moderate` | `label_top3_current_observation` | 0.718000 | 0.561000 | 2.212000 | 0.718000 |
| `ranking_noise_moderate` | `non_persistent_anchor_v0` | 0.422000 | 0.422000 | 1.578000 | 0.422000 |
| `ranking_noise_moderate` | `uncertainty_topk_v0` | 0.904000 | 0.644833 | 1.857000 | 0.904000 |
| `target_dropout_stress` | `uncertainty_topk_v0` | 0.904938 | 0.641770 | 2.072589 | 0.733000 |
| `heavy_noise_stress` | `uncertainty_topk_v0` | 0.618785 | 0.367956 | 2.499482 | 0.560000 |

Low-motion controls under `ranking_noise_moderate`:

- `uncertainty_topk_v0` static preserved: 1.000000.

Task-context conditioning on `ranking_noise_moderate` significant moved rows:

| Context | Policy | Observable-target success | Mean utility | Mean checked locations |
| --- | --- | ---: | ---: | ---: |
| `routine_fetch` | fixed `uncertainty_topk_v0` | 0.904000 | 0.625450 | 1.857000 |
| `routine_fetch` | `task_conditioned_budget_v0` | 0.912000 | 0.633000 | 1.860000 |
| `high_value_fetch` | fixed `uncertainty_topk_v0` | 0.904000 | 2.409450 | 1.857000 |
| `high_value_fetch` | `task_conditioned_budget_v0` | 0.988000 | 2.674800 | 1.908000 |

Task-context conditioning on `heavy_noise_stress` significant moved rows:

| Context | Policy | Observable-target success | Mean utility when target observable | Mean checked locations |
| --- | --- | ---: | ---: | ---: |
| `noisy_high_value_fetch` | fixed `uncertainty_topk_v0` | 0.618785 | 1.400718 | 2.517000 |
| `noisy_high_value_fetch` | `task_conditioned_budget_v0` | 0.930387 | 2.364696 | 2.932000 |

Low-motion controls under `task_conditioned_budget_v0`:

- static preserved under `ranking_noise_moderate`: 1.000000.

Budget baseline gate on `ranking_noise_moderate` significant moved rows:

| Context | Policy | Observable-target success | Mean utility | Mean returned locations | Success / returned location |
| --- | --- | ---: | ---: | ---: | ---: |
| `routine_fetch` | `always_top3` | 0.915000 | 0.636000 | 2.408000 | 0.379983 |
| `routine_fetch` | `always_top5` | 0.988000 | 0.701800 | 3.588000 | 0.275362 |
| `routine_fetch` | `fixed_uncertainty_topk_v0` | 0.904000 | 0.625450 | 2.378000 | 0.380151 |
| `routine_fetch` | `task_conditioned_budget_v0` | 0.912000 | 0.633000 | 2.393000 | 0.381112 |
| `high_value_fetch` | `always_top5` | 0.988000 | 2.674800 | 3.588000 | 0.275362 |
| `high_value_fetch` | `task_conditioned_budget_v0` | 0.988000 | 2.674800 | 3.588000 | 0.275362 |

Budget baseline gate on `heavy_noise_stress` / `noisy_high_value_fetch`:

| Policy | Observable-target success | Mean utility | Mean returned locations |
| --- | ---: | ---: | ---: |
| `fixed_uncertainty_topk_v0` | 0.618785 | 1.192450 | 2.380000 |
| `always_top5` | 0.930387 | 2.046700 | 3.897000 |
| `task_conditioned_budget_v0` | 0.930387 | 2.046700 | 3.897000 |

Hard failures:

| Pair | Object | Failure | Top-k result |
| --- | --- | --- | --- |
| `0cac7578` -> `ddc73795` | `pillow` object `43` | top-1 chooses `41` | target rank 3 |
| `280d8ebb` -> `4731976c` | `pillow` object `43` | top-1 chooses `46` | target rank 2 |

## 논문 주장

지원되는 주장:

- H001 passes a strict hypothesis-stage multi-pair semantic map-update gate.
- The policy can keep stale FP at 0 on significant moved rows in the current artifact.
- The policy can preserve low-motion memories.
- The policy can expose hard `pillow` ambiguity through bounded top-k output.
- The policy improves candidate-inspection search proxy metrics on the current strict artifact.
- The policy remains useful under moderate controlled annotation-level proposal noise when the target proposal is observable.
- Structured task context can improve task-weighted utility by changing candidate budget.
- Fixed top-k baselines are necessary: `task_conditioned_budget_v0` matches `always_top5` in high-value contexts and is more budget-efficient in routine contexts.

아직 지원되지 않는 주장:

- final exact moved-object recovery.
- `SR` / `SPL` navigation improvement.
- real RGB-D / open-vocabulary perception robustness.
- open-vocabulary generalization.
- natural-language intention understanding.
- learned task policy superiority.
- dominance over `always_top5` in high-value contexts.

## 에이전트 추론

The result is promising but not top-tier-ready as a final claim. The search-cost bridge supports a proxy search claim, but not a real navigation claim. The perception-noise gate supports controlled proposal-noise robustness, but not real RGB-D or open-vocabulary perception robustness.

The heavy noise stress was the important limitation: fixed `uncertainty_topk_v0` fell to 0.618785 observable-target success. `task_conditioned_budget_v0` recovers this to 0.930387 for `noisy_high_value_fetch` by spending more candidate checks. Budget baseline shows this recovery is equivalent to `always_top5`, so the defensible claim is context-conditioned budget selection, not universal superiority over fixed top-k.

The newest `gymnastic ball`, `stool`, and `couch table` rows help denominator coverage but are trivial same-label cases. The most important evidence is the two high-ambiguity `pillow` rows and the chair-heavy high-displacement pair.

## 사용자 판단 필요

Top-tier expansion proxies, budget baseline smoke, and main experiment readiness judgment are complete. 다음은 `ready_with_constraints`를 받아들이고 main experiment design으로 넘어갈지 판단하는 것이다.
