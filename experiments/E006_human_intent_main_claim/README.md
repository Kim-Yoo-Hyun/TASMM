# E006 Human Intent Main Claim

Updated: 2026-06-06

This experiment folder defines the contract for promoting human intent from a secondary conditioning variable to a main paper claim. E006-M01 through E006-M04 are non-data claim-design gates, not execution results. E006-M05 is a schema and paired-context row materialization smoke. E006-M06 is a baseline policy row materialization smoke, not a utility or transfer result.

## Question

Can structured human intent make stale semantic memory decisions better than strong context-agnostic alternatives?

The required effect is not "the robot parses natural language." The required effect is that the same semantic memory, current evidence, candidate set, and path/search-cost fields lead to different memory trust, re-observation, and visit-order decisions when the human task utility changes.

## Current Evidence Boundary

사실:

- E004-M03 reports `task_context_memory_trust_reobserve_v0` 68 / 96 success rows, compared with `context_agnostic_memory_trust_reobserve_v0` 66 / 96.
- E004-M04 reports `all_high_value_memory_trust_counterfactual_v0` 72 / 96, which is stronger than the current task-context policy on that denominator.
- E004-M05 marks memory-trust claim strength as `split_supported`, but task-context-specific claim strength as `limited_positive_not_label_broad`.
- E005-M66 reports only 1 human task-context-specific gain row on the 195-row external-baseline denominator.
- E008-M53 demotes task context to a secondary condition because task-context distinct gain is 0 / 3 in that navigation repair setting.
- E006-M06 materializes 10,400 frozen baseline/policy output rows over 520 paired-context rows and 20 policy ids, with leakage fail rows 0.

논문 주장:

- Current evidence does not support human intent as a main contribution.
- Current evidence supports using structured task context as a conditioning signal inside memory trust and re-observation policies.
- E006-M06 does not support utility improvement or human intent as a main contribution because it does not compute `ContextUtility`, `IntentRegret`, transfer metrics, or success outcomes.

에이전트 추론:

- Human intent can become a main claim only if E006 constructs a utility-sensitive benchmark where context changes the correct decision under the same evidence.
- A natural-language or LLM parser should be treated as an input adapter until structured intent has a strong independent decision effect.

## Hypothesis

논문 주장 후보:

Structured human intent improves dynamic object search/navigation because it changes the utility of false trust, missed targets, unnecessary re-observation, and old-location dead-end visits. Therefore, stale semantic memory should expose memory trust, re-observation, and candidate visit order as task-utility-conditioned decisions.

## Method Contract

Allowed inputs:

- `query_label`, query category, old/current scan ids, and candidate source id
- stale memory features: old location, current location if observed, motion/staleness score, memory source reliability
- current evidence features: detector/map confidence, proposal source, candidate coordinate, source-ready flag
- search/navigation fields: candidate rank, path cost, reachability, old-location dead-end cost, re-observation cost
- structured task context fields fixed before evaluation

Blocked inputs:

- target uid or target object instance id
- eval goal coordinate or oracle viewpoint
- success/failure label from the evaluated row
- future observations not available at decision time
- post-hoc human label edits derived from the result

Structured task context schema:

| Field | Role |
| --- | --- |
| `task_type` | e.g. `routine_fetch`, `urgent_fetch`, `high_value_fetch`, `avoid_false_alarm`, `inspection` |
| `target_value` | utility of finding the target |
| `miss_penalty` | cost of not finding a high-value target |
| `false_trust_penalty` | cost of trusting stale old memory incorrectly |
| `reobserve_cost` | cost of checking current observation or extra candidates |
| `search_budget` | candidate visit or action budget |
| `old_location_dead_end_penalty` | task-specific penalty for visiting stale old locations |
| `latency_weight` | penalty for long search/path cost |

Natural-language adapter boundary:

- A later LLM adapter may map a user instruction to the structured fields above.
- The adapter should be evaluated with slot accuracy, consistency, and ambiguity handling.
- It is not method novelty unless the downstream structured-intent decision effect passes E006.

## Benchmark Contract

E006 rows must be paired by evidence:

```text
same query + same memory + same current proposals + same path/search costs
different structured task context
```

Required pair types:

| Pair type | Expected decision difference |
| --- | --- |
| `routine_fetch` vs `high_value_fetch` | high-value context can justify more re-observation or larger budget |
| `urgent_fetch` vs `inspection` | urgent context should reduce costly detours; inspection can tolerate broader search |
| `avoid_false_alarm` vs `high_value_fetch` | false-alarm-sensitive context should suppress weak stale memory more aggressively |
| `low_value_fast` vs `high_value_slow` | same target evidence should trade off cost and recall differently |

Minimum denominator before a main claim:

- at least two heldout scan groups
- at least two object label groups with positive context-specific effects
- at least two task-context groups with positive context-specific effects
- no claim from a single `chair` / `pillow`-only effect

## Baseline Suite

E006-M02 fixes the strong context-agnostic baseline suite. These baselines are designed to answer: if the task-conditioned policy wins, did it win because human intent is useful, or because a simpler global rule would have worked?

Baseline fairness rules:

- Primary comparison must use the same query rows, candidate rows, old memory, current proposal fields, and path/search-cost fields.
- Non-oracle baselines must not read `task_type`, `target_value`, `miss_penalty`, `false_trust_penalty`, `reobserve_cost`, `old_location_dead_end_penalty`, or `latency_weight`.
- Constant-context baselines may use one frozen context profile for every row, such as "always high value", but they must not switch by row.
- Any threshold, budget, or mixture weight must be selected on a dev split and frozen before heldout evaluation.
- If the task-conditioned policy wins only because it uses a larger candidate budget, the claim is warning/fail unless the utility metric explicitly justifies that cost.

Strong baseline families:

| Baseline | Allowed inputs | Decision rule | Expected failure if human intent matters |
| --- | --- | --- | --- |
| `static_stale_memory_v0` | old memory only | trust old candidate first, no current re-observation unless old memory unavailable | stale old-location dead-end under moved objects |
| `detector_confidence_topk_v0` | current proposal confidence and candidate rank | visit current candidates by detector/map confidence | missed target or false-positive pushdown when detector is noisy |
| `fixed_topk_always5_v0` | candidate list only | return or visit top 5 candidates with no memory trust decision | unnecessary cost in low-value or false-alarm-sensitive contexts |
| `context_agnostic_memory_trust_reobserve_v0` | staleness, memory reliability, current evidence reliability | trust/reobserve from one global threshold | cannot change false-trust vs miss tradeoff across task contexts |
| `all_high_value_memory_trust_counterfactual_v0` | same as context-agnostic plus one frozen high-value profile | behave as if every task has high target value | unnecessary re-observation and high search cost on routine or low-value tasks |
| `all_reobserve_budget5_v0` | current proposal availability and fixed budget | always reobserve and visit up to fixed budget 5 | high cost; weak when old memory is reliable and cheap |
| `risk_threshold_only_v0` | staleness or motion risk score | trust old memory only below one global risk threshold | fails when the same risk should be tolerated differently by task utility |
| `path_cost_only_reachable_first_v0` | reachability and path cost | visit reachable/low-cost candidates first | ignores high-value target miss penalty and stale-memory risk |
| `proposal_reliability_only_v0` | source id, detector/map confidence, proposal depth/support if present | choose the most reliable proposal source first | ignores old-memory value and task-dependent re-observation utility |
| `dev_best_global_mixture_v0` | dev-selected fixed weights over staleness, proposal confidence, path cost | one global score for every task context | if it matches task-conditioned policy, human-intent claim is weak |
| `conceptgraphs_only_open_vocab_map_v0` | `ConceptGraphs` candidate rank/score and coordinates | use external map candidates without H001 task-conditioned memory trust | tests whether a stronger map alone solves the decision |
| `open3dsg_vocab_only_scene_graph_v0` | bounded `Open3DSG` predicted-vocabulary candidate score/rank | use external scene-graph object candidates without H001 task-conditioned memory trust | tests whether graph/vocabulary expansion replaces the task-conditioned decision |

Required ablation policies:

| Ablation | Difference from task-conditioned method | Reviewer question |
| --- | --- | --- |
| `no_task_context_v0` | remove structured task context; keep staleness, proposal reliability, and path cost | Is task context necessary? |
| `no_staleness_memory_trust_v0` | remove staleness/memory-trust term | Is this more than task-conditioned top-k? |
| `no_reobserve_budget_v0` | keep ranking but disable re-observation budget decision | Is budget/re-observation part of the insight? |
| `no_path_search_cost_v0` | keep memory trust but remove path/search-cost term | Is the result sensitive to embodied search cost? |
| `task_context_only_v0` | use task context without staleness/proposal reliability | Does task context alone overfit a utility prior? |

Baseline promotion rule:

- A human-intent main claim needs improvement over the best non-oracle row among `context_agnostic_memory_trust_reobserve_v0`, `all_high_value_memory_trust_counterfactual_v0`, `all_reobserve_budget5_v0`, `path_cost_only_reachable_first_v0`, `detector_confidence_topk_v0`, and `dev_best_global_mixture_v0`.
- External baselines such as `ConceptGraphs` and bounded `Open3DSG` are required as pressure rows, but they do not replace the context-agnostic ablation suite because they test map quality rather than task utility.

Upper bounds:

- `oracle_target_available_v0`
- `oracle_context_utility_v0`

Upper bounds are diagnostics, not baselines.

## Row Schema

E006-M02 also fixes the schema needed before implementation.

`paired_context_queries.jsonl` required fields:

| Field | Meaning |
| --- | --- |
| `pair_id` | stable id for same-evidence context pair |
| `query_id` | original query row id |
| `evidence_group_id` | same memory/proposal/path-cost group id shared across contexts |
| `scan_group_id` | split/scene group for transfer accounting |
| `label_group` | object category group |
| `source_ready_group` | `source_ready`, `source_gap`, or `mixed` |
| `context_id` | structured context row id |
| `task_type` | fixed task type label |
| `utility_profile_id` | id of numeric utility profile |
| `search_budget` | candidate/action budget available to task-conditioned policy |
| `old_location_dead_end_penalty` | context-specific penalty |
| `blocked_field_audit` | must be empty or pass |

`baseline_policy_rows.jsonl` required fields:

| Field | Meaning |
| --- | --- |
| `pair_id`, `query_id`, `context_id` | join keys |
| `policy_id` | policy/baseline id |
| `policy_family` | memory-only, detector-only, cost-only, context-agnostic, task-conditioned, external-map, oracle |
| `uses_task_context` | true only for task-conditioned policies and oracle diagnostics |
| `allowed_input_groups` | recorded input groups used by policy |
| `decision_action` | `trust_old`, `reobserve_current`, `visit_candidates`, or `stop` |
| `selected_budget` | number of candidates/actions allowed by policy |
| `old_memory_trusted` | boolean |
| `reobserve_selected` | boolean |
| `ranked_candidate_ids` | ordered candidate ids, with no target uid |
| `expected_search_cost` | expected candidate/path cost |
| `path_cost_m` | optional path cost if available |
| `source_ready_flag` | source-ready accounting |

`utility_metric_rows.jsonl` required fields:

| Field | Meaning |
| --- | --- |
| `policy_id`, `pair_id`, `context_id` | join keys |
| `ContextUtility` | utility score under the context profile |
| `IntentRegret` | regret against `oracle_context_utility_v0` |
| `ContextSpecificGain` | delta against best frozen context-agnostic baseline |
| `ContextPairDecisionDivergence` | whether paired contexts changed decisions under same evidence |
| `ExpectedSearchCost` | search/candidate/path cost |
| `OldLocationDeadEndCostM` | stale old-location dead-end cost |
| `UnnecessaryReobserveCost` | cost of re-observation not justified by utility |
| `MissedHighValuePenalty` | penalty for missing high-value target |
| `FalseTrustPenalty` | penalty for trusting stale memory incorrectly |

Leakage audit:

- `ranked_candidate_ids` must be source-local candidate ids, not target object ids.
- Utility rows may use ground-truth success only after policy output is frozen.
- Split assignment and dev-selected baseline hyperparameters must be recorded before heldout metrics.

## Context Generalization Stress

E006-M03 fixes the generalization stress gate. Its purpose is to prevent a human-intent claim from being supported by one scan group, one label group, one utility profile, or one source route.

Generalization principle:

```text
same policy family + frozen utility formula + frozen baseline thresholds
must produce positive context-specific utility on heldout scans, heldout labels, and heldout task groups
```

Split axes:

| Axis | Required split | What it tests |
| --- | --- | --- |
| `scan_group_holdout` | no scan or rescan-family overlap between dev and heldout groups | avoids scan-specific threshold fitting |
| `label_group_holdout` | at least one positive-effect label group is unseen during policy/threshold selection | avoids `chair` / `pillow`-only effects |
| `task_group_holdout` | at least one task type or utility profile is unseen during policy/threshold selection | tests whether task utility transfers beyond memorized contexts |
| `source_condition_split` | report `source_ready` and `source_gap` separately | separates intent effect from candidate-source availability |
| `external_route_split` | report internal H001-only, `ConceptGraphs`-assisted, and bounded `Open3DSG` pressure rows separately when available | avoids claiming task context when a stronger map route explains the gain |

Minimum split manifest fields:

| Field | Meaning |
| --- | --- |
| `split_id` | stable split id |
| `split_role` | `dev`, `heldout_scan`, `heldout_label`, `heldout_task`, or `stress` |
| `heldout_axis` | scan, label, task, source, or external route |
| `query_id` | query row id |
| `pair_id` | paired-context id |
| `scan_group_id` | scan or rescan-family group |
| `label_group` | object/category group |
| `task_group` | task-family group |
| `source_ready_group` | source-ready accounting group |
| `allowed_for_threshold_selection` | boolean |
| `allowed_for_final_claim` | boolean |

Threshold and tuning rule:

- Tune thresholds, budgets, and global mixture weights only on rows with `allowed_for_threshold_selection=true`.
- Freeze `task_context_schema.json`, utility weights, baseline thresholds, and policy ids before heldout evaluation.
- Do not rebalance heldout splits after seeing `ContextUtility`, `IntentRegret`, or success outcomes.
- If a split has insufficient label or task coverage, mark it `warning` or `fail`; do not silently drop it.

Primary transfer gates:

| Gate | Pass condition | Warning condition | Fail condition |
| --- | --- | --- | --- |
| `scan_transfer` | positive `ContextSpecificGain` and lower `IntentRegret` than best non-oracle context-agnostic baseline in at least two heldout scan groups | positive aggregate but one scan group dominates | no heldout scan group positive |
| `label_transfer` | positive context-specific effect in at least two label groups, with no single label group contributing more than 60% of positive gain | two labels positive but one contributes 60-80% | one-label-only effect or only `chair` / `pillow` positive |
| `task_transfer` | at least two task groups positive, including one group not used for threshold selection | positive only on dev-seen task groups | no heldout task group positive |
| `source_transfer` | source-ready result remains positive and source-gap is separately reported without overclaim | source-ready positive but source-gap unresolved | source-gap mixed into aggregate to hide failure |
| `external_route_pressure` | task-conditioned policy remains useful after `ConceptGraphs` / bounded `Open3DSG` pressure rows are included or separated | external rows explain part of the gain | external-map-only route dominates task-conditioned policy |

Claim permission:

- Full human-intent main claim requires `scan_transfer`, `label_transfer`, and `task_transfer` pass.
- If only `scan_transfer` passes, claim only scan-level robustness of a structured task-context policy.
- If only `label_transfer` fails, claim boundary must say the result is label-narrow.
- If only `task_transfer` fails, human intent must remain a secondary conditioning variable.
- If `external_route_pressure` fails, contribution must be narrowed to map-source integration rather than human intent.

Stress rows to include before paper claim:

| Stress row | Purpose |
| --- | --- |
| `low_value_fast` vs `high_value_slow` | tests cost/recall tradeoff under same evidence |
| `avoid_false_alarm` vs `high_value_fetch` | tests false trust vs miss penalty |
| `urgent_fetch` vs `inspection` | tests latency-sensitive vs broad-search behavior |
| `routine_fetch` vs `high_value_fetch` | maintains continuity with E004 while checking it is not the only positive pair |

Required reporting:

- group-level `ContextUtility`, `IntentRegret`, `ContextSpecificGain`, and proxy `SR`
- bootstrap or repeated-split uncertainty for the primary utility/regret deltas
- top contributing scan group, label group, and task group
- failure rows with `failure_type`, `dominant_axis`, `suspected_cause`, and `next_validation`
- explicit non-claim if the positive effect is from budget expansion only

## Utility Formula And Implementation Readiness

E006-M04 fixes the utility formula and implementation-readiness contract. Its purpose is to prevent later E006 execution from tuning the metric after seeing policy outcomes.

Utility convention:

- All task profiles use unitless utility points.
- Benefits are positive and costs are subtracted.
- Policy outputs are generated before success labels, oracle target availability, or goal coordinates are read.
- Utility metrics may use ground-truth success only after `baseline_policy_rows.jsonl` is frozen.
- Primary tables must not mix incompatible cost sources without a separate group report.

Outcome variables:

| Variable | Meaning | Computed after policy output? |
| --- | --- | --- |
| `HitWithinBudget` | selected candidate sequence reaches the target within the allowed budget | yes |
| `MissedTarget` | target is not reached within budget while a target exists in the evaluation denominator | yes |
| `FalseTrust` | policy trusts stale old memory and the old-memory candidate is not the target under current evidence | yes |
| `OldLocationDeadEnd` | policy visits old stale location before target and the target is elsewhere | yes |
| `ReobserveCount` | number of current-observation or extra-candidate checks selected by policy | no, from policy row |
| `CandidateVisitCount` | number of non-oracle candidates the policy attempts | no, from policy row |
| `PathCostM` | path cost in meters when E002/E007/E008 path fields are available | no, from path artifact |
| `BudgetOverrun` | selected budget exceeds the context budget | no, from policy row |

Primary formula:

```text
ContextUtility =
  target_value * HitWithinBudget
  - miss_penalty * MissedTarget
  - false_trust_penalty * FalseTrust
  - old_location_dead_end_penalty * OldLocationDeadEnd
  - reobserve_cost * ReobserveCount
  - latency_weight * ExpectedSearchCost
  - budget_overrun_penalty * BudgetOverrun

IntentRegret =
  OracleContextUtility - ContextUtility

ContextSpecificGain =
  ContextUtility(policy)
  - max(ContextUtility(non_oracle_context_agnostic_baseline))
```

`ExpectedSearchCost` is computed with `search_cost_contract_v0`:

| Cost source | Formula | Reporting rule |
| --- | --- | --- |
| `candidate_rank_only` | `CandidateVisitCount` | allowed for proxy-search tables |
| `candidate_plus_path` | `CandidateVisitCount + PathCostM / 5.0` | required for path-backed search/navigation bridge rows |

Global constants:

| Constant | Value | Purpose |
| --- | --- | --- |
| `path_unit_m` | 5.0 | converts meters into candidate-attempt units |
| `budget_overrun_penalty` | 10.0 | prevents a policy from winning only by ignoring context budget |
| `primary_cost_source_rule` | group-separated | tables report `candidate_rank_only` and `candidate_plus_path` separately |

Frozen task profiles:

| `utility_profile_id` | `task_type` | `target_value` | `miss_penalty` | `false_trust_penalty` | `reobserve_cost` | `search_budget` | `old_location_dead_end_penalty` | `latency_weight` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `routine_fetch_v0` | `routine_fetch` | 10 | 6 | 4 | 1.0 | 5 | 2 | 0.50 |
| `high_value_fetch_v0` | `high_value_fetch` | 25 | 25 | 8 | 1.5 | 8 | 4 | 0.40 |
| `urgent_fetch_v0` | `urgent_fetch` | 16 | 12 | 5 | 2.0 | 3 | 5 | 1.00 |
| `inspection_v0` | `inspection` | 12 | 8 | 2 | 0.5 | 10 | 1 | 0.20 |
| `avoid_false_alarm_v0` | `avoid_false_alarm` | 10 | 4 | 16 | 1.0 | 4 | 10 | 0.60 |
| `low_value_fast_v0` | `low_value_fast` | 6 | 3 | 6 | 1.5 | 3 | 6 | 1.00 |
| `high_value_slow_v0` | `high_value_slow` | 24 | 24 | 6 | 0.8 | 10 | 3 | 0.25 |

Profile-pair requirements:

| Pair id | Context A | Context B | Required policy pressure |
| --- | --- | --- | --- |
| `pair_routine_high_value_v0` | `routine_fetch_v0` | `high_value_fetch_v0` | higher value should justify more re-observation or larger budget only when utility supports it |
| `pair_urgent_inspection_v0` | `urgent_fetch_v0` | `inspection_v0` | latency-sensitive task should reject broad search more often |
| `pair_false_alarm_high_value_v0` | `avoid_false_alarm_v0` | `high_value_fetch_v0` | false-trust penalty and miss penalty should pull decisions in opposite directions |
| `pair_fast_slow_v0` | `low_value_fast_v0` | `high_value_slow_v0` | same evidence should trade off cost and recall differently |

Implementation row-generation order:

1. Load fixed query/candidate/path rows from existing E001/E002/E005/E007/E008 artifacts.
2. Assign `evidence_group_id` before adding task context.
3. Duplicate each eligible evidence row into the frozen profile pairs above.
4. Assign `transfer_split_manifest.jsonl` before computing metrics.
5. Generate non-oracle policy rows without target uid, goal coordinate, success label, target rank, or target distance.
6. Freeze `baseline_policy_rows.jsonl`.
7. Compute `utility_metric_rows.jsonl` from frozen policy rows and evaluation labels.
8. Aggregate `group_transfer_metrics.jsonl` and `summary.json`.
9. Export `failure_rows.jsonl` for rows where task-conditioned policy loses to the best context-agnostic baseline.

Implementation manifest fields:

| Field | Required content |
| --- | --- |
| `m04_contract_version` | `e006_m04_utility_formula_v0` |
| `task_context_schema_version` | `task_context_schema_v0` |
| `utility_formula_id` | `context_utility_v0` |
| `search_cost_contract_id` | `search_cost_contract_v0` |
| `profile_table_hash` | hash or exact copy of frozen task profile table |
| `source_artifact_roots` | E001/E002/E005/E007/E008 roots used for rows |
| `policy_ids` | all non-oracle, task-conditioned, ablation, external-map, and oracle diagnostic ids |
| `dev_selection_fields` | thresholds and budgets allowed to be selected on dev |
| `blocked_input_audit` | pass/fail and any row-level leakage errors |
| `cost_source_groups` | `candidate_rank_only` and/or `candidate_plus_path` |
| `docker_image` | required for final paper-body execution, optional for local schema dry run |
| `reproduction_commands` | exact commands once implementation exists |

M04 pass/warning/fail:

| Gate | Pass | Warning | Fail |
| --- | --- | --- | --- |
| `formula_freeze` | formula, constants, and profiles fixed before row metrics | sensitivity profiles planned but not primary | utility weights edited after seeing outcomes |
| `row_order` | policy rows freeze before utility rows | partial dry run only | metrics computed from target-aware policy inputs |
| `cost_source` | cost sources separated in reports | one group too small for claim | cost sources mixed in one headline score |
| `baseline_readiness` | all M02 strong baselines included in manifest | external pressure row missing but marked | context-agnostic baselines omitted |
| `transfer_readiness` | M03 split fields generated before metrics | insufficient group coverage marked warning | heldout groups selected after outcomes |

M04 non-claims:

- M04 does not support a human-intent main claim.
- M04 does not show utility improvement, transfer, or navigation performance.
- M04 only makes the later implementation auditable by freezing the formula and row-generation contract.

## Schema And Pair Materialization Smoke

E006-M05 materializes the first executable schema and paired-context rows from the E007 195-row path-cost denominator.

사실:

- Status: `ready`.
- Command: `python experiments/E006_human_intent_main_claim/tools/materialize_m05_schema_rows.py`.
- Syntax check: `python -m py_compile experiments/E006_human_intent_main_claim/tools/materialize_m05_schema_rows.py`.
- Output root: `experiments/E006_human_intent_main_claim/artifacts/E006-M05_schema_pair_materialization_smoke_v0/`.
- Source rows: E007-M04 `query_policy_metric_rows.jsonl` and E005-M100 `selected_policy_rows.jsonl`.
- Evidence groups: 65.
- Paired context rows: 520.
- Transfer manifest rows: 2,600.
- Label groups: 23.
- Task groups: 5.
- Source-ready groups: `source_ready` 464 rows, `source_gap` 56 rows.
- Required-field validation: paired rows missing required fields 0; transfer rows missing required fields 0.
- Blocked output term hits: 0 for `target_uid`, `target_object_instance_id`, `eval_goal_coordinate`, `oracle_viewpoint`, `success_label`, `target_rank`, and `target_distance`.

Artifacts:

| Artifact | Path |
| --- | --- |
| `task_context_schema.json` | `artifacts/E006-M05_schema_pair_materialization_smoke_v0/task_context_schema.json` |
| `implementation_manifest.json` | `artifacts/E006-M05_schema_pair_materialization_smoke_v0/implementation_manifest.json` |
| `paired_context_queries.jsonl` | `artifacts/E006-M05_schema_pair_materialization_smoke_v0/paired_context_queries.jsonl` |
| `transfer_split_manifest.jsonl` | `artifacts/E006-M05_schema_pair_materialization_smoke_v0/transfer_split_manifest.jsonl` |
| `summary.json` | `artifacts/E006-M05_schema_pair_materialization_smoke_v0/summary.json` |

논문 주장:

- E006-M05 supports implementation readiness for a human-intent benchmark schema only.
- E006-M05 does not support human intent as a main contribution, utility improvement, `SR` / `SPL`, or final navigation claims.

에이전트 추론:

- The smoke is useful because it proves the M04 formula/profile contract can be instantiated without exposing target/evaluation fields in the paired-context rows.
- The next implementation risk is policy-row generation: baselines must consume these rows without reading task context when they are context-agnostic and without using evaluation-only labels.

## Metrics

Primary metrics:

- `ContextUtility`
- `IntentRegret`
- `ExpectedSearchCost`
- `ContextSpecificGain`
- `ContextPairDecisionDivergence`
- `OldLocationDeadEndCostM`
- `UnnecessaryReobserveCost`
- `MissedHighValuePenalty`
- `FalseTrustPenalty`

Secondary metrics:

- proxy `SR`
- `AttemptSPL`
- `PathAttemptSPLProxy`
- candidate top-k hit
- source-ready / source-gap split
- label-group and task-group transfer pass rate

Metric rule:

- A human-intent claim cannot be based only on raw success improvement.
- The claim must show lower utility regret under changed task context while preserving or improving success against the strongest non-oracle context-agnostic baseline.

## Pass / Warning / Fail

Pass:

- task-conditioned policy beats the best non-oracle context-agnostic baseline on `ContextUtility` or `IntentRegret`
- proxy `SR` has no material regression
- gains appear in at least two task groups, two label groups, and heldout scan groups
- ablation without task context loses the context-specific metric
- `all_high_value` and `all_reobserve` do not dominate the selected policy

Warning:

- gains are positive but concentrated in one task group or one label group
- utility improves only by adding large search cost
- task context changes the decision but not the outcome
- natural-language parser performance becomes the main positive result

Fail:

- context-agnostic memory trust ties or beats the task-conditioned policy
- `all_high_value` or `all_reobserve` is stronger under the same budget
- gains are only one or two rows on the 195-row denominator
- the policy requires blocked target/evaluation information
- the only positive evidence is prompt/LLM parsing rather than map-decision utility

## Output Contract

Planned E006 artifacts after implementation:

| Artifact | Purpose |
| --- | --- |
| `task_context_schema.json` | fixed structured intent fields and allowed values |
| `implementation_manifest.json` | M04 formula, profile, cost-source, policy-id, blocked-input, and command contract |
| `paired_context_queries.jsonl` | same-evidence, different-context query pairs |
| `transfer_split_manifest.jsonl` | dev/heldout/stress split roles across scan, label, task, source, and external-route axes |
| `baseline_policy_rows.jsonl` | policy outputs for all context-agnostic, task-conditioned, external-map, and oracle diagnostic rows |
| `utility_metric_rows.jsonl` | row-level utility and regret metrics |
| `group_transfer_metrics.jsonl` | group-level transfer metrics and uncertainty rows |
| `failure_rows.jsonl` | context-specific failure taxonomy |
| `summary.json` | pass/warning/fail gates |

## Baseline Policy Row Materialization Smoke

E006-M06 materializes frozen baseline/policy output rows from the E006-M05 paired-context rows.

사실:

- Status: `ready`.
- Command: `python experiments/E006_human_intent_main_claim/tools/materialize_m06_baseline_policy_rows.py`.
- Syntax check: `python -m py_compile experiments/E006_human_intent_main_claim/tools/materialize_m06_baseline_policy_rows.py`.
- Output root: `experiments/E006_human_intent_main_claim/artifacts/E006-M06_baseline_policy_materialization_smoke_v0/`.
- Paired context rows: 520.
- Policy count: 20.
- Baseline policy rows: 10,400.
- Leakage audit rows: 10,400.
- Leakage fail rows: 0.
- Rows with `uses_task_context=false`: 6,760.
- Rows with `uses_task_context=true`: 3,640.
- Decision action counts: `visit_candidates` 7,150, `reobserve_current` 1,728, `trust_old` 1,522.
- Selected next unit: E006-M07 `utility_metric_rows.jsonl` materialization smoke.

Artifacts:

| Artifact | Path |
| --- | --- |
| `baseline_policy_rows.jsonl` | `artifacts/E006-M06_baseline_policy_materialization_smoke_v0/baseline_policy_rows.jsonl` |
| `leakage_audit_rows.jsonl` | `artifacts/E006-M06_baseline_policy_materialization_smoke_v0/leakage_audit_rows.jsonl` |
| `summary.json` | `artifacts/E006-M06_baseline_policy_materialization_smoke_v0/summary.json` |
| `report.md` | `artifacts/E006-M06_baseline_policy_materialization_smoke_v0/report.md` |

논문 주장:

- E006-M06 supports policy-output freeze readiness only.
- E006-M06 does not support human intent as a main contribution, utility improvement, transfer robustness, `SR` / `SPL`, or final navigation claims.

에이전트 추론:

- The key value of M06 is leakage control: context-agnostic baselines do not use task context, and task-conditioned rows still avoid target uid, target rank, target distance, success label, eval goal, and oracle viewpoint fields.
- The next risk is whether utility metrics computed after policy freeze show context-specific gain over the strongest non-oracle context-agnostic baseline.

Paper-table command is not fixed yet. E006-M01/M02/M03/M04 are design contracts only. E006-M05 is a schema materialization smoke only. E006-M06 is a policy-row materialization smoke only.

## Next Unit

E006-M07: implement `utility_metric_rows.jsonl` materialization smoke from frozen `baseline_policy_rows.jsonl`, then report `ContextUtility`, `IntentRegret`, `ContextSpecificGain`, and strongest context-agnostic baseline comparison without changing policy rows.
