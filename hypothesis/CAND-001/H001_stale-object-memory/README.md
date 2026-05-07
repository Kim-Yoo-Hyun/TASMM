# H001

## Status

Hypothesis-stage main experiment readiness gate complete and accepted.

Current workflow: `experiments/E001_semantic_pair_dynamic_search_proxy/`.

## Files

| File | Role |
| --- | --- |
| [01_setup.md](01_setup.md) | problem, hypothesis, scope |
| [02_data.md](02_data.md) | local data route and pair coverage |
| [03_gates.md](03_gates.md) | completed gate summary |
| [04_method.md](04_method.md) | map states, policies, allowed inputs |
| [05_results.md](05_results.md) | strict-pass metrics and hard failures |
| [06_summary.md](06_summary.md) | claim boundary and next gate |

Detailed generated outputs remain in `artifacts/`. Executable scripts remain in `tools/`.

## 사실

- H001 has a 12-pair strict hypothesis-stage artifact.
- Significant moved rows: 10.
- Low-motion controls: 48.
- `uncertainty_topk_v0` significant Recall@returned K: 1.000000.
- `uncertainty_topk_v0` mean `ExpectedSearchCost`: 1.300000.
- `uncertainty_topk_v0` stale FP: 0.000000.
- `uncertainty_topk_v0` low-motion static preserved: 1.000000.
- `search_cost_bridge_gate` status: `bridge_pass`.
- `uncertainty_topk_v0` proxy search success on significant moved rows: 1.000000.
- `uncertainty_topk_v0` `AttemptSPL` proxy on significant moved rows: 0.883333.
- `perception_noise_gate` status: `robustness_pass`.
- Under `ranking_noise_moderate`, `uncertainty_topk_v0` observable-target success: 0.904000.
- Under `ranking_noise_moderate`, `uncertainty_topk_v0` `AttemptSPL` proxy: 0.644833.
- `task_context_gate` status: `conditioning_pass`.
- Under `high_value_fetch`, `task_conditioned_budget_v0` observable-target success: 0.988000.
- Under `heavy_noise_stress` / `noisy_high_value_fetch`, observable-target success: 0.930387.
- `budget_baseline_gate` status: `budget_baseline_pass`.
- Under `routine_fetch`, `task_conditioned_budget_v0` is more budget-efficient than `always_top5`: success / returned location 0.381112 vs 0.275362.
- Under `high_value_fetch`, `task_conditioned_budget_v0` matches `always_top5`: observable-target success 0.988000.
- Experiment promotion contract is fixed in `04_method.md` and `06_summary.md`.
- Main experiment readiness gate status: `ready_with_constraints`.
- Main experiment transition: accepted for proxy semantic-pair benchmark design.
- Current evidence uses annotation-level `semseg.v2.json`, not real RGB-D or open-vocabulary perception.

## 논문 주장

Supported now:

- `Task-Conditioned Stale Semantic Memory Update`.
- Stale old-location suppression.
- Low-motion memory preservation.
- Bounded top-k uncertainty for hard moved-object cases.
- Candidate-inspection proxy search improvement.
- Moderate controlled annotation-level proposal-noise robustness.
- Structured task-context budget conditioning.
- Budget-efficiency boundary against fixed top-k baselines.

Not supported yet:

- Exact moved-object recovery.
- Dynamic object search/navigation `SR` / `SPL` improvement.
- Real RGB-D perception robustness.
- Open-vocabulary perception robustness.
- Rich human-intention understanding.
- Learned task policy superiority.
- Dominance over `always_top5` in high-value contexts.

## 에이전트 추론

The current result is strong enough for main experiment readiness, but only with proxy-claim boundaries preserved:

1. `search_cost_bridge_gate`: complete.
2. `perception_noise_gate`: complete.
3. `task_context_condition_gate`: complete.
4. `budget_baseline_gate`: complete.

Human task context is represented as structured cost/reward context that changes memory trust, returned candidate budget, and re-observation thresholds. It is not a natural-language understanding claim. In experiments, fixed top-k baselines must be included because high-value behavior intentionally matches `always_top5`.

## 사용자 판단 필요

Next workflow is `experiments/E001_semantic_pair_dynamic_search_proxy/`; do not broaden the claim to real navigation or real perception yet.
