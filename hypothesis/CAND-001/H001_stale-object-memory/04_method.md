# Method

## 사실

현재 구현된 policy family:

- `scene_aligned_static_map`
- `staleness_only`
- `label_nearest_current_observation`
- `label_top3_current_observation`
- `instance_evidence_v0`
- `non_persistent_anchor_v0`
- `uncertainty_topk_v0`
- `oracle_current_pose`

Allowed ranking inputs:

- query object label.
- old scene-aligned object memory.
- current same-label candidate geometry from `semseg.v2.json`.
- local relation predicate names and neighbor labels from `3DSSG`.
- label-binned local context.
- candidate entropy, score margin, bounded top-k rules.

Not allowed for ranking:

- persistent cross-scan object-id matching.
- exact current target pose.
- navigation trajectory.
- RGB-D or open-vocabulary perception outputs.

Search-cost bridge contract:

- Artifact: `artifacts/search_cost_bridge_gate/`.
- Primary subset: significant moved rows.
- Proxy `SR`: target found within the returned candidate-location budget.
- Proxy `SPL`: `1 / checked_locations` for successful rows, `0` for failures.
- This is a candidate-inspection proxy, not real `SPL`.
- Current gate uses no navmesh, obstacle map, robot start pose, RGB-D perception, or open-vocabulary detections.

Perception-noise gate contract:

- Artifact: `artifacts/perception_noise_gate/`.
- Primary scenario: `ranking_noise_moderate`.
- Perturbations: 0.20 m localization jitter, feature-score noise std 0.08, non-target candidate dropout 0.10, false-positive proposal probability 0.50.
- Primary scenario keeps target proposals observable to test ranking robustness separately from perception recall.
- Stress scenarios: `target_dropout_stress` and `heavy_noise_stress`.
- This is controlled annotation-level proposal noise, not real RGB-D or open-vocabulary perception.

Task-context conditioning gate contract:

- Artifact: `artifacts/task_context_gate/`.
- Contexts: `routine_fetch`, `high_value_fetch`, `noisy_high_value_fetch`.
- Context inputs are structured cost profiles: success reward, check cost, failure cost, and max candidate budget.
- Context changes returned candidate budget and memory trust behavior; it does not parse natural language.
- Baseline: fixed `uncertainty_topk_v0` budget.
- Policy under test: `task_conditioned_budget_v0`.

Budget baseline gate contract:

- Artifact: `artifacts/budget_baseline_gate/`.
- Baselines: `always_top1`, `always_top3`, `always_top5`, fixed `uncertainty_topk_v0`.
- Test policy: `task_conditioned_budget_v0`.
- The gate separates utility from budget efficiency.
- Passing this gate does not mean `task_conditioned_budget_v0` dominates `always_top5`; it means context determines when top-5 behavior is worth the extra budget.

Experiment promotion method contract:

- Promoted method name: `task_conditioned_budget_v0`.
- Method role: semantic map memory trust and candidate-budget policy for dynamic object search proxy.
- Required baseline family: static map, label-nearest current observation, fixed top-k budgets, fixed uncertainty budget, and oracle upper bound.
- Required fixed top-k baselines: `always_top1`, `always_top3`, `always_top5`.
- Required claim boundary: all promoted metrics remain proxy search metrics until real navigation or real perception is implemented.

## 논문 주장

지원되는 주장:

- H001 can frame semantic memory update as a map-state decision: trust old memory, suppress stale memory, update from current observation, or expose top-k uncertainty.
- `non_persistent_anchor_v0` improves significant moved exact recovery over label-nearest current observation on the current artifact.
- `uncertainty_topk_v0` preserves all significant moved targets inside a bounded returned set.
- `uncertainty_topk_v0` improves candidate-inspection proxy search success and `AttemptSPL` over direct top-1 memory update on the current artifact.
- `uncertainty_topk_v0` remains useful under moderate controlled proposal noise when the target proposal is observable.
- `task_conditioned_budget_v0` improves context-weighted utility for high-value and noisy high-value search contexts.
- `task_conditioned_budget_v0` is more budget-efficient than `always_top5` for `routine_fetch` and matches `always_top5` behavior for high-value contexts.

아직 지원되지 않는 주장:

- Learned policy superiority.
- Calibrated confidence under held-out split.
- Real navigation `SR` / `SPL`.
- Perception-robust deployment.
- Real RGB-D / open-vocabulary detector robustness.
- Natural-language intention understanding.
- Learned task policy superiority.
- Superiority over all fixed top-k baselines in every context.

## 에이전트 추론

`uncertainty_topk_v0` is the most defensible current method shape. It admits that exact instance recovery is uncertain and turns ambiguity into a bounded search interface. The search-cost bridge confirms this is not just a bookkeeping metric: on significant moved rows, returning a bounded set raises proxy search success from 0.800000 under direct top-1 `non_persistent_anchor_v0` to 1.000000 while keeping mean checked locations at 1.300000.

For top-tier positioning, the method should become a task-conditioned memory trust layer:

1. task context selects relevant object memories.
2. stale evidence changes trust strictness.
3. current candidates are ranked with semantic geometry and relation context.
4. uncertainty determines whether the robot trusts, searches, or re-observes.
5. task context changes trust threshold and returned candidate budget when perception is noisy or task cost is high.

## 사용자 판단 필요

Top-tier expansion gates와 budget baseline gate는 hypothesis 수준에서 통과했다. 다음은 이 claim boundary와 fixed top-k baseline requirement를 유지한 채 `docs/experiments.md` planning으로 승격할지 판단하는 것이다.
