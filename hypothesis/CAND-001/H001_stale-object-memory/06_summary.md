# Summary

## 사실

- H001 strict-pass value summary is complete.
- H001 search-cost bridge gate is complete with status `bridge_pass`.
- H001 perception-noise gate is complete with status `robustness_pass`.
- H001 task-context conditioning gate is complete with status `conditioning_pass`.
- H001 budget baseline gate is complete with status `budget_baseline_pass`.
- Safe current claim: `Task-Conditioned Stale Semantic Memory Update`.
- Current artifact supports stale suppression, low-motion preservation, bounded top-k candidate uncertainty, candidate-inspection proxy search improvement, moderate controlled proposal-noise robustness, structured task-context budget conditioning, and budget-efficiency boundary against fixed top-k baselines.
- Current artifact does not support real navigation, real RGB-D perception, open-vocabulary perception, learned task policy superiority, or rich human-intention understanding.

## 논문 주장

Safe wording:

- "Task-conditioned stale semantic memory update can suppress stale object-location memories and expose bounded current-candidate uncertainty under dynamic indoor semantic map changes."

Top-tier target wording after further gates:

- "Task-conditioned stale semantic memory update improves dynamic object search/navigation by reducing stale-target failures and search burden, while remaining robust to perception noise."

Not safe yet:

- "The robot solves moved-object recovery."
- "The method improves `SR` / `SPL`."
- "The method is robust to RGB-D or open-vocabulary perception noise."
- "The robot understands human intentions."
- "The task-conditioned policy is learned from language."
- "The method dominates `always_top5` in high-value contexts."

## 에이전트 추론

`Task-Conditioned Stale Semantic Memory Update` alone is too narrow for top-tier positioning. The expansion status is:

1. Search-cost bridge: complete as proxy search success / `AttemptSPL`, not real navigation `SR` / `SPL`.
2. Perception-noise bridge: complete as controlled annotation-level proposal noise, not real RGB-D / open-vocabulary perception.
3. Task-context bridge: complete as structured context-conditioned budget adjustment, not natural-language intention understanding.
4. Budget baseline bridge: complete. `task_conditioned_budget_v0` is more budget-efficient than `always_top5` in `routine_fetch`, but matches `always_top5` in high-value contexts.

## 다음 Gate

Recommended next decision:

`main_experiment_readiness_gate`

Completed top-tier expansion sub-gate:

- `search_cost_bridge_gate`
- `perception_noise_gate`
- `task_context_condition_gate`
- `budget_baseline_gate`

Remaining hypothesis sub-gates:

- None.

Do not edit `docs/experiments.md` until the main experiment transition is explicitly accepted.

## Experiment Promotion Contract

사실:

- Target claim: `Task-Conditioned Stale Semantic Memory Update` improves dynamic object search proxy behavior by suppressing stale old-location returns, exposing bounded current-candidate uncertainty, and conditioning candidate budget on structured task context.
- Dataset unit: `3RScan` / `3DSSG` reference-rescan semantic pair.
- Current hypothesis evidence: 12 validated pairs, 94 query rows, 10 significant moved rows, 48 low-motion controls.
- Required baselines: `scene_aligned_static_map`, `label_nearest_current_observation`, `always_top1`, `always_top3`, `always_top5`, fixed `uncertainty_topk_v0`, and oracle upper bound.
- Primary metrics: stale old-location FP, low-motion preservation, Recall@returned K, `ExpectedSearchCost`, proxy `SR`, `AttemptSPL`, task utility, and success / returned-location efficiency.
- Non-claims at promotion: real navigation `SR` / `SPL`, real RGB-D perception robustness, open-vocabulary perception robustness, learned task policy, and natural-language intention understanding.

에이전트 추론:

- Promotion is reasonable only if `docs/experiments.md` preserves the proxy-search boundary and includes fixed top-k baselines.
- First experiment after promotion should scale semantic-pair dynamic object search proxy before real navigation or real RGB-D perception.
- Failure after promotion would mean either context-conditioned budget is not better than fixed top-k at scale, or current annotation-level signals do not survive broader pair diversity.

## Main Experiment Readiness Gate

사실:

- Gate status: `ready_with_constraints`.
- H001 has problem framing, hypothesis, method contract, evaluation protocol, baseline family, metric set, failure mode, and claim boundary fixed inside this hypothesis folder.
- Main experiment unit: `3RScan` / `3DSSG` reference-rescan semantic pair.
- Main experiment target: scale the semantic-pair dynamic object search proxy benchmark beyond the current 12 validated pairs.
- Required baselines remain `scene_aligned_static_map`, `label_nearest_current_observation`, `always_top1`, `always_top3`, `always_top5`, fixed `uncertainty_topk_v0`, and oracle upper bound.
- Required first-stage metrics remain stale old-location FP, low-motion preservation, Recall@returned K, `ExpectedSearchCost`, proxy `SR`, `AttemptSPL`, task utility, and success / returned-location efficiency.
- Readiness does not mean final thesis direction confirmation.

논문 주장:

- H001 is ready to enter a main experiment only as a proxy semantic-map memory update benchmark.
- H001 is not ready to enter a main experiment as a real navigation, real RGB-D perception, open-vocabulary perception, learned policy, or natural-language intention-understanding benchmark.

에이전트 추론:

- Additional small hypothesis smoke tests are unlikely to add more decision value than scaling the current protocol.
- The main remaining uncertainty is whether the `ready_with_constraints` signal survives broader pair diversity and fixed top-k baselines.
- A negative main experiment would still be informative: it would show that task-conditioned memory trust is not consistently better than fixed budget search under current annotation-level dynamic-object signals.

## 사용자 판단 필요

`ready_with_constraints` has been accepted as the working transition state. Next workflow is `experiments/E001_semantic_pair_dynamic_search_proxy/`.
