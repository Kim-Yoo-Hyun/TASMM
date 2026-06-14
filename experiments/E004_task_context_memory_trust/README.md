# E004 Task Context Memory Trust

Updated: 2026-05-13

## Status

`E004-M01_transition_gate_v0` is complete with status `e004_transition_ready_with_constraints`. `E004-M02_metric_contract_v0` is complete with status `e004_m02_metric_contract_ready`. `E004-M03_memory_trust_policy_v0` is complete with status `e004_m03_task_context_tradeoff_ready_with_constraints`. `E004-M04_claim_boundary_ablation_v0` is complete with status `e004_m04_claim_boundary_ready`. `E004-M05_scale_split_stress_v0` is complete with status `e004_m05_split_stress_ready_limited_task_context`. E004 now serves as input to E005; E005-M01 selected `DualMap` as the first external baseline route.

## Source

- Workflow rule: `docs/experiments.md`
- Source hypothesis: `archive/hypothesis/CAND-001/H001_stale-object-memory/`
- E003 source: `experiments/E003_perception_noise_expansion/`
- Immediate input artifact: `experiments/E003_perception_noise_expansion/artifacts/E003-M75_expanded_direct_query_bridge_v0/`

## Contract

사실:

- E003-M75 target detection is 87 / 96 query rows.
- E003-M75 `detector_task_budget_v0` success is 13 / 96.
- E003-M75 `bounded_old_memory_distance_guard_adaptive_top5_v0` success is 33 / 96.
- E003-M75 bounded repair raises mean `ExpectedSearchCost` from 2.645833 to 4.937500.

논문 주장:

- E004 can only claim task-context memory trust / re-observation value if it improves budgeted search behavior using deployable inputs.
- E004 cannot claim final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` at the transition gate.

에이전트 추론:

- The useful E004 question is whether task context changes when the robot trusts stale memory, expands re-observation, or avoids old-location dead ends.
- E004 must not collapse into a task-agnostic top-k expansion.

사용자 판단 필요:

- None before E005.

## E004-M01 Transition Gate

Implementation unit: `E004-M01_transition_gate_v0`.

Command:

```bash
python experiments/E004_task_context_memory_trust/tools/plan_m01_transition_gate.py
```

Artifacts:

- `experiments/E004_task_context_memory_trust/tools/plan_m01_transition_gate.py`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M01_transition_gate_v0/coverage.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M01_transition_gate_v0/decision.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M01_transition_gate_v0/report.md`

사실:

- Status: `e004_transition_ready_with_constraints`.
- M75 query rows: 96.
- M75 target detected rows/rate: 87 / 0.906250.
- Task-budget success rows/rate: 13 / 0.135417.
- Bounded repair success rows/rate: 33 / 0.343750.
- Bounded success delta vs task budget: +20 rows.
- Task-budget mean `ExpectedSearchCost`: 2.645833.
- Bounded mean `ExpectedSearchCost`: 4.937500.
- Unbounded mean `ExpectedSearchCost`: 9.750000.
- Task-context-specific effect ready: false.

논문 주장:

- E004-M01 supports starting an E004 task-context memory trust / re-observation decision experiment.
- E004-M01 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.

에이전트 추론:

- M75 gives a useful bounded repair signal, but the current bounded repair has identical success rate across `routine_fetch`, `high_value_fetch`, and `noisy_high_value_fetch`.
- E004-M02 must design a task-context-specific memory trust / re-observation policy and prevent the method from becoming a generic top-k expansion.

사용자 판단 필요:

- None before E004-M03.

## E004-M02 Metric Contract

Implementation unit: `E004-M02_metric_contract_v0`.

Command:

```bash
python experiments/E004_task_context_memory_trust/tools/plan_m02_metric_contract.py
```

Artifacts:

- `experiments/E004_task_context_memory_trust/tools/plan_m02_metric_contract.py`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M02_metric_contract_v0/contract.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M02_metric_contract_v0/report.md`

사실:

- Status: `e004_m02_metric_contract_ready`.
- Source E003-M75 query rows: 96.
- Source E003-M75 target detected rows: 87.
- Query contract ready: true.
- Policy metric contract ready: true.

논문 주장:

- E004-M02 fixes the evaluation contract for task-context memory trust and re-observation decisions.
- E004-M02 is not a method result and does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.

에이전트 추론:

- The next method unit should implement `task_context_memory_trust_reobserve_v0`.
- E004-M03 must compare against `detector_task_budget_v0`, detector top-k, bounded repair, and oracle policies.
- E004-M03 must not use `target_uid`, target rank, target match distance, false positives before target, success labels, or evaluation-only dead-end labels as policy inputs.
- A positive E004 result must show task-context-specific tradeoffs, not merely higher top-k search.

사용자 판단 필요:

- None before E004-M03.

## E004-M03 Memory Trust Policy

Implementation unit: `E004-M03_memory_trust_policy_v0`.

Command:

```bash
python experiments/E004_task_context_memory_trust/tools/evaluate_m03_memory_trust_policy.py
```

Artifacts:

- `experiments/E004_task_context_memory_trust/tools/evaluate_m03_memory_trust_policy.py`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/coverage.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/decision.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/metrics.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/policy_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/policy_summary_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/failure_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M03_memory_trust_policy_v0/report.md`

사실:

- Status: `e004_m03_task_context_tradeoff_ready_with_constraints`.
- Query rows: 96.
- `static_memory_only_v0` success rows/rate: 63 / 0.656250.
- `context_agnostic_memory_trust_reobserve_v0` success rows/rate: 66 / 0.687500.
- `task_context_memory_trust_reobserve_v0` success rows/rate: 68 / 0.708333.
- `task_context_memory_trust_reobserve_v0` mean `ExpectedSearchCost` / `AttemptSPL` proxy: 2.354167 / 0.675347.
- `bounded_old_memory_distance_guard_adaptive_top5_v0` success rows/rate: 33 / 0.343750.
- `high_value_fetch` task-context delta vs context-agnostic: +2 success rows, +0.500000 mean `ExpectedSearchCost`.
- Leakage audit pass: true.

논문 주장:

- E004-M03 supports task-context memory trust / re-observation evidence under the current 96-row direct bridge denominator.
- E004-M03 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.

에이전트 추론:

- The main gain over detector-only policies comes from evaluating old-memory trust as part of the semantic memory decision.
- The task-context-specific gain over context-agnostic memory trust is narrow and concentrated in `high_value_fetch`.
- E004-M04 should check whether this is a real task-context contribution or just a small budget expansion effect.

사용자 판단 필요:

- None before E004-M04.

## E004-M04 Claim Boundary Ablation

Implementation unit: `E004-M04_claim_boundary_ablation_v0`.

Command:

```bash
python experiments/E004_task_context_memory_trust/tools/analyze_m04_claim_boundary.py
```

Artifacts:

- `experiments/E004_task_context_memory_trust/tools/analyze_m04_claim_boundary.py`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/coverage.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/decision.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/metrics.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/policy_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/policy_summary_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/row_ablation.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M04_claim_boundary_ablation_v0/report.md`

사실:

- Status: `e004_m04_claim_boundary_ready`.
- `context_agnostic_memory_trust_reobserve_v0`: 66 / 96, mean `ExpectedSearchCost` 2.187500.
- `task_context_memory_trust_reobserve_v0`: 68 / 96, mean `ExpectedSearchCost` 2.354167.
- `all_routine_memory_trust_counterfactual_v0`: 66 / 96, mean `ExpectedSearchCost` 2.187500.
- `all_high_value_memory_trust_counterfactual_v0`: 72 / 96, mean `ExpectedSearchCost` 2.687500.
- Task-context vs context-agnostic delta: +2 success rows, +0.166667 mean `ExpectedSearchCost`.
- All-high-value vs task-context delta: +4 success rows, +0.333333 mean `ExpectedSearchCost`.
- Ablation class counts: context-agnostic already success 66, unrecovered 24, task-context unique success 2, all-high-value budget-only success 4.

논문 주장:

- E004-M04 supports a memory-trust decision claim under the current 96-row direct bridge denominator.
- E004-M04 supports only a limited task-context-specific claim: `high_value_fetch` gives a small success gain by accepting extra search cost.
- E004-M04 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.

에이전트 추론:

- The current task-context effect is real but small.
- A pure all-high-value budget counterfactual gets more successes than the task-context policy, so the paper must not claim globally optimal task conditioning yet.
- The next useful unit is E004-M05 scale/split stress before moving to E005 external baselines.

사용자 판단 필요:

- None before E004-M05.

## E004-M05 Scale Split Stress

Implementation unit: `E004-M05_scale_split_stress_v0`.

Command:

```bash
python experiments/E004_task_context_memory_trust/tools/analyze_m05_scale_split_stress.py
```

Artifacts:

- `experiments/E004_task_context_memory_trust/tools/analyze_m05_scale_split_stress.py`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/coverage.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/decision.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/metrics.json`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/split_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/bootstrap_rows.jsonl`
- `experiments/E004_task_context_memory_trust/artifacts/E004-M05_scale_split_stress_v0/report.md`

사실:

- Status: `e004_m05_split_stress_ready_limited_task_context`.
- Query rows: 96.
- Overall task-context vs static success delta: +5 rows.
- Overall task-context vs context-agnostic success delta: +2 rows.
- Overall all-high-value counterfactual vs task-context success delta: +4 rows.
- Leave-one-scan memory-trust positive: true.
- Leave-one-scan task-context positive: true.
- Bootstrap task-context vs static positive rate: 0.952.
- Bootstrap task-context vs context-agnostic positive rate: 0.872.
- Bootstrap all-high-value vs task-context positive rate: 0.872.
- Task-context positive label groups: `chair`, `pillow`.
- Task-context label breadth sufficient: false.

논문 주장:

- E004-M05 supports a split-supported memory-trust decision claim under the current 96-row direct bridge denominator.
- E004-M05 supports only a limited task-context-specific claim: positive but not label-broad.
- E004-M05 does not support final real RGB-D/open-vocabulary robustness, deployable search policy, or real navigation `SR` / `SPL` claims.

에이전트 추론:

- The memory-trust decision signal is stable enough to lock E004 as current evidence.
- The task-context signal should be written as a controlled tradeoff concentrated in `chair` / `pillow` style cases, not as a broad task-conditioning result.
- The next top-tier-relevant move is E005 external baseline transition, not more tuning on the same 96 rows.

사용자 판단 필요:

- None before E005-M02.
