# E001 Semantic Pair Dynamic Search Proxy

Updated: 2026-05-07

## Status

Implementation started. `E001-M01_pair_manifest_v0` through `E001-M05_additional_pair_staging_v0` artifacts are generated. Next unit is E002 path-cost preparation.

## Source

- Source hypothesis: `hypothesis/CAND-001/H001_stale-object-memory/`
- Workflow rule: `docs/experiments.md`
- Dataset root: `local_dataset/`

## 사실

- H001 readiness state `ready_with_constraints` is accepted as the working transition state.
- Dataset unit: `3RScan` / `3DSSG` reference-rescan semantic pair.
- Current local dataset contains `3RScan`, `3DSSG`, and `3DSSG_subset`.
- First main experiment target is scaling the semantic-pair dynamic object search proxy benchmark beyond the initial 12 validated pairs.
- First-stage evidence remains annotation-level `semseg.v2.json` and `3DSSG/relationships.json`.

## 논문 주장

Testable claim:

- `Task-Conditioned Stale Semantic Memory Update` improves dynamic object search proxy behavior by suppressing stale old-location returns, exposing bounded current-candidate uncertainty, and conditioning candidate budget on structured task context.

E001-only non-claims:

- real navigation `SR` / `SPL`.
- real RGB-D perception robustness.
- open-vocabulary perception robustness.
- learned task policy.
- natural-language intention understanding.

Target full-paper claim after E001-E004:

- `Task-Conditioned Semantic Memory Trust` improves dynamic object search/navigation under stale semantic maps and perception noise by changing memory trust, re-observation, and candidate-budget decisions according to task context.

## E001 Contract

| Field | Required content |
| --- | --- |
| question | Does task-conditioned stale semantic memory update reduce stale old-location failures and search burden on `3RScan` / `3DSSG` semantic-pair dynamic object search proxy tasks? |
| hypothesis | `task_conditioned_budget_v0` should preserve low-motion memories, suppress stale old locations, recover significant moved targets inside bounded candidate sets, and improve task utility or success / returned-location efficiency against fixed baselines. |
| config | Dataset root, eligible pair manifest, query construction thresholds, policy versions, random seed, controlled noise scenario, and metric set. |
| command | TBD at implementation time. No result table is paper-eligible without an exact command. |
| input manifest | Reference-rescan pair IDs, payload availability, selected split, query rows, significant moved rows, low-motion controls, excluded cases and reasons. |
| output manifest | Metrics JSON, predictions JSONL, failure table, pair coverage report, and paper-table candidate summary. |
| comparison | `scene_aligned_static_map`, `label_nearest_current_observation`, `always_top1`, `always_top3`, `always_top5`, fixed `uncertainty_topk_v0`, `task_conditioned_budget_v0`, and oracle upper bound. |
| conclusion | Claim supported, weakened, or rejected based on metric direction, baseline comparison, and failure concentration. |

## Metric Contract

Primary metrics:

- stale old-location FP.
- low-motion preservation.
- Recall@returned K.
- `ExpectedSearchCost`.
- proxy `SR`.
- `AttemptSPL`.
- task utility.
- success / returned-location efficiency.

Secondary diagnostics:

- significant moved row count.
- low-motion control count.
- high-ambiguity row count.
- same-label candidate count.
- target rank distribution.
- excluded pair reasons.

## Implementation Order

1. Pair manifest: enumerate eligible `3RScan` / `3DSSG` reference-rescan semantic pairs and record payload availability. Done for `E001-M01_pair_manifest_v0`.
2. Query construction: generate significant moved rows, low-motion controls, and mid-motion review rows with fixed thresholds and expansion-ready fields for E002/E003/E004. Done for `E001-M02_query_construction_v0`.
3. Baseline evaluation: run static, current-observation, fixed top-k, task-conditioned, and oracle policies. Done for `E001-M03_baseline_evaluation_v0`.
4. Failure analysis: summarize hard labels, ambiguous candidates, missing payloads, and cases where fixed top-k matches or beats the method. Done for `E001-M04_failure_analysis_v0`.
5. Noise scenario: rerun controlled annotation-level proposal noise after clean semantic-pair results are stable.

## Top-Tier Expansion Ladder

사실:

- Research scope is 6 months to 1 year.
- E001 is the first main experiment, not the complete top-tier package.
- Intermediate submissions are allowed when a standalone contribution is ready.

Planned ladder:

| ID | Role | Required evidence |
| --- | --- | --- |
| E001 | semantic-pair dynamic object search proxy benchmark | scaled pair/query manifest, fixed baselines, `ExpectedSearchCost`, proxy `SR`, `AttemptSPL`, task utility, failure taxonomy |
| E002 | dynamic object search/navigation bridge | path/search cost, candidate visit order, old-location dead-end cost, `SR`, `SPL` or defensible proxy `SPL` |
| E003 | RGB-D / open-vocabulary perception robustness | RGB-D replay or open-vocabulary proposal subset, detector/proposal noise, stale-memory update stability |
| E004 | task-context memory trust / re-observation decision | task context changes memory trust, re-observation threshold, candidate budget; ablations against fixed top-k and fixed uncertainty |

논문 주장:

- E001 can support a benchmark/proxy claim.
- E001-E004 together can support a top-tier full-paper claim about task-conditioned semantic memory trust for dynamic search/navigation under stale maps and perception noise.

에이전트 추론:

- E001 must remain reproducible and auditable because it becomes the denominator for later embodied and perception claims.
- E002/E003 are the main upgrades that move the paper beyond a small semantic-memory heuristic.
- E004 is needed to keep human task context central without overclaiming natural-language understanding.

## E001-M01 Pair Manifest Unit

Implementation unit: `E001-M01_pair_manifest_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E001_semantic_pair_dynamic_search_proxy/tools/build_pair_manifest.py
```

Artifacts:

- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0/manifest.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0/coverage.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M01_pair_manifest_v0/report.md`

사실:

- `3RScan/files/3RScan.json` contains 1004 reference-rescan metadata pairs.
- Local `3RScan/scans/` currently contains 53 scan directories.
- 54 local scan directories have the semantic payload triplet: `semseg.v2.json`, `labels.instances.annotated.v2.ply`, and `mesh.refined.0.010000.segs.v2.json`.
- 8 local scan directories have `sequence.zip` or `sequence/`; this is optional for E001-M01.
- `3DSSG/relationships.json` contains 1335 unique scan entries.
- `3DSSG/objects.json` contains 1482 unique scan entries.
- 13 metadata pairs currently have both reference and rescan semantic payloads locally available.
- 13 metadata pairs satisfy the minimum E001-M01 ready condition under the current local dataset.
- Generated manifest rows: 1004.
- Generated `ready_minimal` rows: 13.
- Generated blocked rows: 991.

Manifest input:

- `local_dataset/3RScan/files/3RScan.json`.
- `local_dataset/3RScan/scans/<scan_id>/semseg.v2.json`.
- `local_dataset/3RScan/scans/<scan_id>/labels.instances.annotated.v2.ply`.
- `local_dataset/3RScan/scans/<scan_id>/mesh.refined.0.010000.segs.v2.json`.
- `local_dataset/3DSSG/objects.json`.
- `local_dataset/3DSSG/relationships.json`.

Manifest row schema:

- `manifest_version`: fixed string `e001_pair_manifest_v0`.
- `pair_uid`: `<reference_scan_id>-><rescan_id>`.
- `reference_scan_id`.
- `rescan_id`.
- `metadata_split`: value from the `3RScan` metadata group.
- `metadata_rigid_count`.
- `metadata_removed_count`.
- `reference_payload`: booleans for `scan_dir`, `semseg`, `ply`, `segs`, `sequence`.
- `rescan_payload`: booleans for `scan_dir`, `semseg`, `ply`, `segs`, `sequence`.
- `reference_3dssg`: booleans for `objects`, `relationships`.
- `rescan_3dssg`: booleans for `objects`, `relationships`.
- `eligibility_status`: one of `ready_minimal`, `blocked`.
- `exclusion_reasons`: list of blocker strings.
- `next_stage`: one of `query_construction_v0`, `needs_staging`, `exclude`.

Eligibility rule:

- `ready_minimal` requires both reference and rescan scan directories.
- `ready_minimal` requires both reference and rescan `semseg.v2.json`.
- `ready_minimal` requires both reference and rescan `labels.instances.annotated.v2.ply`.
- `ready_minimal` requires both reference and rescan `mesh.refined.0.010000.segs.v2.json`.
- `ready_minimal` requires `metadata_rigid_count > 0`.
- `ready_minimal` requires reference-side `3DSSG` objects and relationships.
- Rescan-side `3DSSG` relationships are recorded but not required for E001-M01 because first-stage current observations come from `semseg.v2.json`.
- `sequence.zip` / `sequence/` is recorded but not required; missing sequence cannot block proxy semantic-pair evaluation.

Exclusion reasons:

- `missing_reference_scan_dir`.
- `missing_rescan_scan_dir`.
- `missing_reference_semseg`.
- `missing_rescan_semseg`.
- `missing_reference_ply`.
- `missing_rescan_ply`.
- `missing_reference_segs`.
- `missing_rescan_segs`.
- `missing_rigid_metadata`.
- `missing_reference_3dssg_objects`.
- `missing_reference_3dssg_relationships`.

## 에이전트 추론

- E001-M01 should not yet filter by significant displacement. That belongs to E001-M02 query construction.
- E001-M01 should keep blocked rows with explicit exclusion reasons so the denominator is auditable.
- Existing H001 candidate-selection logic can be reused, but E001-M01 needs a cleaner manifest schema and paper-table coverage report.

## 사용자 판단 필요

None for this unit.

## E001-M02 Query Construction Unit

Implementation unit: `E001-M02_query_construction_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E001_semantic_pair_dynamic_search_proxy/tools/build_queries.py
```

Artifacts:

- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/pair_rows.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/base_query_rows.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/query_rows.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/candidate_rows.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/coverage.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/report.md`

사실:

- Query construction uses only `ready_minimal` pairs from `E001-M01_pair_manifest_v0`.
- Current query construction remains annotation-level and uses `semseg.v2.json` plus `3RScan` rigid metadata.
- E001-M02 must preserve fields needed by E002 path/search-cost, E003 RGB-D / open-vocabulary perception robustness, and E004 task-context memory-trust ablation.
- Generated pair rigid rows: 101.
- Generated object-level base query rows: 98.
- Generated context-expanded query rows: 294.
- Generated candidate rows: 1248.
- Generated significant moved base rows: 11.
- Generated low-motion control base rows: 51.
- Generated mid-motion review base rows: 36.
- Generated rows with `rgbd_sequence_available`: 0.

Thresholds:

| Field | Value | Role |
| --- | ---: | --- |
| `geometry_valid_threshold_m` | 1.0 | Maximum row geometry error allowed for query construction |
| `significant_moved_threshold_m` | 1.0 | `scene_aligned_static_planar_error_m >= 1.0` becomes `significant_moved` |
| `low_motion_threshold_m` | 0.25 | `scene_aligned_static_planar_error_m <= 0.25` becomes `low_motion_control` |
| `mid_motion_range_m` | `(0.25, 1.0)` | Rows between low-motion and significant thresholds become `mid_motion_review` |
| `success_threshold_m` | 0.5 | Current-target success threshold for top-1 / candidate localization diagnostics |

Query row schema:

- `query_version`: fixed string `e001_query_v0`.
- `base_row_uid`: `<reference_scan_id>-><rescan_id>:<object_instance_id_ref>`.
- `row_uid`: `<base_row_uid>:<task_context_id>`.
- `pair_uid`.
- `reference_scan_id`.
- `rescan_id`.
- `metadata_split`.
- `object_instance_id_ref`.
- `object_instance_id_rescan`.
- `object_label`.
- `query_text_template`: e.g. `find the <object_label>`.
- `change_type`: initially `rigid_moved`.
- `row_band`: one of `significant_moved`, `low_motion_control`, `mid_motion_review`.
- `old_memory_is_stale`: true only for `significant_moved`.
- `expected_memory_state`: one of `needs_reobservation`, `trusted_or_low_motion`, `review`.
- `old_scene_aligned_centroid`.
- `current_target_centroid`.
- `scene_aligned_static_error_m`.
- `scene_aligned_static_planar_error_m`.
- `row_geometry_error_m`.
- `same_label_candidate_count`.
- `ambiguity_band`: one of `trivial_candidate`, `rank_sensitive`, `high_ambiguity`.
- `evaluation_scope`: initially `dynamic_object_search_proxy`.

E002-ready fields:

- `search_start_policy`: initially `not_set`; later values may include `old_location`, `room_entry`, `random_free_space`, `oracle_start`.
- `old_location_dead_end_expected`: true for stale significant moved rows under static-map baseline.
- `old_location_dead_end_cost_unit`: initially `candidate_visit`.
- `candidate_visit_order_policy`: initially `ranked_candidates_then_old_location_check`; E002 may replace with path-aware order.
- `expected_search_cost_unit`: initially `candidate_count`.
- `expected_search_cost_proxy_ready`: true.
- `path_cost_ready`: false until E002.
- `path_cost_profile_id`: nullable placeholder.
- `navmesh_or_free_space_source`: nullable placeholder.
- `proxy_sr_ready`: true.
- `proxy_spl_ready`: true via `AttemptSPL`; real `SPL` remains false until E002.

E003-ready fields:

- `observation_source`: initially `annotation_semseg`.
- `current_proposal_source`: initially `semseg.v2.json`.
- `rgbd_sequence_available`: from E001-M01 payload status.
- `open_vocab_proposal_source`: nullable placeholder.
- `perception_profile_id`: initially `oracle_annotation`.
- `proposal_noise_profile_id`: initially `none`.
- `target_observable_assumption`: initially `annotation_target_present` for row-valid targets.
- `e003_rgbd_ready`: true only when `sequence.zip` or `sequence/` exists and a detector/replay route is configured.
- `e003_open_vocab_ready`: false until detector proposals are generated.

E004-ready task-context fields:

- `intent_condition_source`: initially `structured_task_context`, not natural language.
- `task_context_id`: one of `routine_fetch`, `high_value_fetch`, `noisy_high_value_fetch`.
- `success_reward`.
- `check_cost`.
- `failure_cost`.
- `max_candidate_budget`.
- `high_ambiguity_budget`.
- `memory_trust_policy`: initially `task_conditioned_budget_v0`.
- `reobservation_policy`: initially `reobserve_if_stale_or_high_uncertainty`.
- `reobservation_threshold_profile`: one of `routine`, `high_value`, `noisy_high_value`.

Task context profiles:

| `task_context_id` | `success_reward` | `check_cost` | `failure_cost` | `max_candidate_budget` | `high_ambiguity_budget` | Meaning |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `routine_fetch` | 1.0 | 0.15 | 0.0 | 3 | 2 | Ordinary request; prefer bounded search |
| `high_value_fetch` | 3.0 | 0.15 | 0.25 | 5 | 5 | Important request; spend more search budget |
| `noisy_high_value_fetch` | 3.0 | 0.15 | 0.25 | 5 | 5 | Important request under perception risk |

Candidate row companion schema:

- `row_uid`.
- `base_row_uid`.
- `candidate_instance_id`.
- `candidate_label`.
- `candidate_centroid`.
- `candidate_rank_semantic`.
- `candidate_rank_non_persistent`.
- `candidate_score_semantic`.
- `candidate_score_non_persistent`.
- `candidate_is_target`.
- `candidate_visit_order_index`.
- `candidate_visit_policy`.
- `candidate_euclidean_cost_from_old_m`.
- `candidate_path_cost_m`: nullable until E002.
- `candidate_observation_source`.
- `candidate_proposal_confidence`: nullable until E003.

논문 주장:

- E001-M02 supports proxy semantic-pair dynamic object search queries.
- E001-M02 does not claim real navigation, real RGB-D perception, open-vocabulary perception, or natural-language human intent understanding.
- Human intent is represented only as structured task context that changes memory trust, re-observation, candidate budget, and candidate visit order.

에이전트 추론:

- Adding E002/E003/E004 fields now prevents E001 from becoming a dead-end proxy benchmark.
- `base_row_uid` preserves the object-level denominator, while `row_uid` allows E004 task-context comparisons without rebuilding E001.
- Query rows should remain simple enough for E001, but every row should carry placeholders needed for path-cost, perception-source, and task-context expansion.
- E004 should remain a memory-trust / re-observation decision claim, not a language-understanding claim.

사용자 판단 필요:

- None for E001-M02. Baseline evaluation is now complete in E001-M03.

## E001-M03 Baseline Evaluation Unit

Implementation unit: `E001-M03_baseline_evaluation_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E001_semantic_pair_dynamic_search_proxy/tools/evaluate_baselines.py
```

Artifacts:

- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0/predictions.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0/failure_rows.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0/metrics.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0/coverage.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M03_baseline_evaluation_v0/report.md`

사실:

- Status: `baseline_ready`.
- Query rows: 294.
- Base query rows: 98.
- Candidate rows: 1248.
- Prediction rows: 2352.
- Failure rows: 184.
- Significant moved rows per context: 11.
- `routine_fetch` significant moved `task_conditioned_budget_v0`: proxy `SR` 0.727273, `ExpectedSearchCost` 1.636364, `AttemptSPL` 0.681818, utility 0.481818, stale FP 0.0.
- `high_value_fetch` significant moved `task_conditioned_budget_v0`: proxy `SR` 0.909091, `ExpectedSearchCost` 2.181818, `AttemptSPL` 0.722727, utility 2.377273, stale FP 0.0.
- `scene_aligned_static_map` significant moved stale FP: 1.0.
- Low-motion `task_conditioned_budget_v0` preservation rate: 1.0.
- `oracle_current_target` significant moved upper bound: proxy `SR` 1.0 and `ExpectedSearchCost` 1.0.

논문 주장:

- E001-M03 supports clean annotation-level baseline comparison for semantic-pair dynamic object search proxy tasks.
- E001-M03 does not support real navigation `SR` / `SPL`, RGB-D perception robustness, open-vocabulary perception robustness, learned policy, or natural-language intention understanding.

에이전트 추론:

- The method suppresses stale old-location returns on significant moved rows and preserves low-motion rows.
- In `routine_fetch`, the method trades success against `always_top5` for lower search cost.
- In `high_value_fetch`, the method matches `always_top5` on significant moved proxy `SR` while remaining below the oracle upper bound.
- Remaining failures are mainly candidate-budget misses and static-map localization errors, so the next useful step is failure analysis before claiming stronger E002/E003/E004 evidence.

사용자 판단 필요:

- None for E001-M03. Failure analysis is now complete in E001-M04.

## E001-M04 Failure Analysis Unit

Implementation unit: `E001-M04_failure_analysis_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E001_semantic_pair_dynamic_search_proxy/tools/analyze_failures.py
```

Artifacts:

- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0/failure_summary.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0/method_vs_baselines.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0/claim_boundary.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0/hard_cases.jsonl`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M04_failure_analysis_v0/report.md`

사실:

- Status: `claim_boundary_ready`.
- Prediction rows analyzed: 2352.
- Failure rows analyzed: 184.
- `task_conditioned_budget_v0` failure rows: 7.
- Hard case rows written: 7.
- All `task_conditioned_budget_v0` failures are `target_outside_returned_budget`.
- Overall failure types: `target_outside_returned_budget` 94, `static_map_localization_error` 57, `stale_old_location_returned` 33.

논문 주장:

- Safe E001 claim: annotation-level semantic-pair dynamic object search proxy evaluation on locally ready `3RScan` / `3DSSG` pairs.
- Safe E001 claim: `task_conditioned_budget_v0` suppresses stale old-location false positives relative to `scene_aligned_static_map` on significant moved rows.
- Safe E001 claim: structured task context changes search budget and creates a routine-vs-high-value tradeoff in proxy `SR` and `ExpectedSearchCost`.
- Unsupported claims remain real navigation `SR` / `SPL`, path-cost-aware search, RGB-D robustness, open-vocabulary robustness, natural-language intention understanding, learned task policy, and full benchmark-scale conclusion.

에이전트 추론:

- E001 is now a clean proxy benchmark result and denominator, but not yet a top-tier-complete embodied result.
- The main method weakness is bounded budget miss, not stale old-location suppression.
- Additional pair staging increased the significant moved denominator by one row; more staging may still be useful before final paper-scale claims.
- E002 should convert candidate-count `ExpectedSearchCost` into path/search cost before any navigation-style claim.

사용자 판단 필요:

- None for E001-M04. Additional pair staging is now complete in E001-M05.

## E001-M05 Additional Pair Staging Unit

Implementation unit: `E001-M05_additional_pair_staging_v0`.

Stage: target pair staged and E001 artifacts rerun.

Command:

```bash
python experiments/E001_semantic_pair_dynamic_search_proxy/tools/record_staging.py
```

Artifacts:

- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M05_additional_pair_staging_v0/staging_summary.json`
- `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M05_additional_pair_staging_v0/report.md`

사실:

- Staged target pair: `5630cfcb-12bf-2860-87ee-b4e4a5bf0cb0->d7d40d75-7a5d-2b36-9746-3e807d3e7558`.
- Downloaded rescan semantic triplet: `semseg.v2.json`, `labels.instances.annotated.v2.ply`, `mesh.refined.0.010000.segs.v2.json`.
- Target pair status after staging: `ready_minimal`.
- Target pair base query rows: 4.
- Target pair significant moved rows: 1, label `vacuum`.
- Target pair low-motion control rows: 3.
- Ready pairs after staging: 13.
- Base query rows after staging: 98.
- Significant moved base rows after staging: 11.
- Rescan `sequence` remains unavailable, so this pair currently helps E001/E002 more than E003 RGB-D replay.

논문 주장:

- E001-M05 supports payload staging and denominator expansion only.
- E001-M05 does not itself support a new method-performance claim.
- The staging result shows the current bottleneck is local payload coverage, not absence of `3RScan` / `3DSSG` metadata pairs.

에이전트 추론:

- This confirms the dataset is not intrinsically too small for the research direction; the current small denominator came from local scan payload availability.
- E002 should now use the expanded E001 query/candidate artifacts and attach path/search-cost fields.

사용자 판단 필요:

- None for E001-M05. Next implementation unit should prepare E002 path-cost bridge.
