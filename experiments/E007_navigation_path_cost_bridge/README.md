# E007 Navigation Path-Cost Bridge

Updated: 2026-05-27

## Status

E007 starts after E005-M101 selected `paper_table_integration_and_navigation_bridge_next`. E007-M01 defines the contract for connecting the M100 query-level candidate visit order to path-aware search/navigation proxy metrics. E007-M02 materializes policy candidate routes and audits path-source compatibility. E007-M03 projects external candidate coordinates onto the E002 occupancy-grid profile and computes route-level path-cost fields with source-limited accounting. E007-M04 evaluates policy-level path-cost metrics while preserving the full denominator and source-ready subset. E007-M05 interprets the result for paper-table use and fixes reviewer-facing claim boundaries. E007-M06 audits source-limit, stop-rank, and old-memory path-start sensitivity. E007-M07 packages the final bridge table, claim-evidence ledger, reviewer-defense rows, and navigation-expansion decision. These units do not report real navigation `SR` / `SPL`.

Next unit: E008-M01 real navigation benchmark/source preflight and episode contract.

## Source

- Workflow rule: `docs/experiments.md`
- Query-level selected policy: `experiments/E005_external_baseline_transition/artifacts/E005-M100_conceptgraphs_assisted_fallback_policy_v0/selected_policy_rows.jsonl`
- Paper-table decision: `experiments/E005_external_baseline_transition/artifacts/E005-M101_map_assisted_claim_boundary_navigation_decision_v0/`
- First path-cost source: `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/`
- `ConceptGraphs` candidate source: `experiments/E005_external_baseline_transition/artifacts/E005-M45_conceptgraphs_heldout_query_metric_v0/`
- Real detector candidate source: `experiments/E005_external_baseline_transition/artifacts/E005-M69_full_denominator_real_proposal_detector_run_v0/`

## E007 Contract

| Field | Required content |
| --- | --- |
| question | Can the M100 policy order be converted from query-level candidate count to path-aware search cost without denominator drift? |
| hypothesis | H001 + `ConceptGraphs` fallback should remain useful when candidate visits are charged by an explicit path-cost proxy instead of raw candidate count. |
| dataset | The 195-row M100 heldout denominator with E002 `occupancy_grid_astar_v0` source coverage. |
| method | Materialize policy candidate visit sequences, attach path cost, preserve source-limited rows, and compare baselines under the same denominator. |
| comparison | Static stale memory, detector-confidence ranking, `ConceptGraphs`-only map, task-agnostic re-observation, H001, and H001 + `ConceptGraphs` fallback. |
| metrics | `PathExpectedSearchCost`, `PathAttemptSPLProxy`, `OldLocationDeadEndCostM`, `PathSourceLimitedRate`, and failure reduction by `row_band` / `task_context_id`. |
| command | `python experiments/E007_navigation_path_cost_bridge/tools/plan_m01_navigation_path_cost_bridge_contract.py`; `python experiments/E007_navigation_path_cost_bridge/tools/audit_m02_path_source_compatibility.py`; `python experiments/E007_navigation_path_cost_bridge/tools/project_m03_external_candidate_grid_paths.py`; `python experiments/E007_navigation_path_cost_bridge/tools/evaluate_m04_path_cost_policy_metrics.py`; `python experiments/E007_navigation_path_cost_bridge/tools/plan_m05_path_cost_result_interpretation.py`; `python experiments/E007_navigation_path_cost_bridge/tools/audit_m06_path_start_source_limit_sensitivity.py`; `python experiments/E007_navigation_path_cost_bridge/tools/plan_m07_bridge_table_navigation_decision.py` |
| output | Contract, source readiness rows, metric contract rows, candidate route rows, query materialization rows, projected route rows, target path rows, policy path summary rows, source-limited rows, baseline rows, claim boundary rows, and reports. |
| conclusion | E007-M01 supports a path-cost bridge contract only. E007-M02 supports route materialization. E007-M03 supports route-level path-cost field readiness. E007-M04 supports occupancy-grid proxy path-cost policy metrics with source limits. E007-M05 supports a paper-facing bridge table with explicit proxy boundaries. E007-M06 shows the table is reviewer-defensible under source-limit/direct-only sensitivity. E007-M07 packages the bridge table as paper-facing proxy evidence and selects E008-M01 as the next preflight/contract step, but not real navigation `SR` / `SPL`. |

## E007-M01

Implementation unit: `E007-M01_navigation_path_cost_bridge_contract_v0`.

Facts:

- Status: `e007_m01_navigation_path_cost_bridge_contract_ready`.
- M100/E002 row overlap: 195 / 195.
- E002 target-grid reachable overlap: 186 / 195.
- `ConceptGraphs` candidate eval rows / query overlap: 7,470 / 195.
- Real detector proposal rows: 925.
- Selected path-cost source: `e002_occupancy_grid_astar_v0`.
- Selected next unit: E007-M02 path-source compatibility and candidate-route materialization audit.

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/plan_m01_navigation_path_cost_bridge_contract.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/contract.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/source_readiness_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/metric_contract_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/baseline_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/command_plan_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M01_navigation_path_cost_bridge_contract_v0/report.md`

## Claim Boundary

- E007-M01 does not claim real navigation `SR` / `SPL`.
- E007-M01 does not claim final real RGB-D/open-vocabulary robustness.
- E007-M01 does not make human intent a main contribution.
- E007-M02 does not claim path-cost metric improvement because 3,097 external route rows still need grid projection.
- E007-M03 does not claim path-cost policy improvement because policy-level metrics have not yet been computed.
- E007-M04 does not claim real navigation `SR` / `SPL`; it reports `PathAttemptSPLProxy`.
- E007-M05 does not claim real navigation `SR` / `SPL`; it fixes E007-M04 as paper-facing occupancy-grid path-cost bridge evidence.
- E007-M06 does not claim real navigation `SR` / `SPL`; it verifies source-limit/direct-only sensitivity for the proxy bridge table.
- E007-M07 does not claim real navigation `SR` / `SPL`; it packages the final E007 proxy table and selects E008-M01.
- `OldLocationDeadEndCostM` is not a primary metric yet because the current path source starts from the old-memory centroid.
- The next defensible step is E008-M01 real navigation benchmark/source preflight and episode contract.

## E007-M02

Implementation unit: `E007-M02_path_source_compatibility_v0`.

Facts:

- Status: `e007_m02_path_source_compatibility_ready_projection_pending`.
- Query rows: 195.
- Query-policy rows: 1,170.
- Route rows: 3,814.
- Queries with all six policies materialized at least once: 177 / 195.
- Candidate grid projection-ready route rows: 705.
- External projection pending route rows: 3,097.
- Source gap rows: 36.
- Selected next unit: E007-M03 external candidate grid projection and path-cost route computation.

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/audit_m02_path_source_compatibility.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/policy_route_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/query_materialization_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/policy_summary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/source_gap_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M02_path_source_compatibility_v0/report.md`

## E007-M03

Implementation unit: `E007-M03_external_candidate_grid_projection_v0`.

Facts:

- Status: `e007_m03_external_candidate_grid_projection_ready`.
- Query rows: 195.
- Query-policy rows: 1,170.
- Route rows: 3,814.
- Route projection-ready rows: 3,785.
- Route path-ready rows: 3,331.
- Query-policy eval-ready rows: 928.
- Source-limited query-policy rows: 216.
- No-route query-policy rows: 36.
- Target path-ready rows: 183.
- Selected next unit: E007-M04 path-cost policy metric evaluation with source-limited accounting.

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/project_m03_external_candidate_grid_paths.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/projected_route_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/query_path_readiness_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/target_path_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/policy_path_summary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/source_limited_route_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/scan_grid_summaries.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M03_external_candidate_grid_projection_v0/report.md`

Agent inference:

- E007-M03 removes the main external-coordinate blocker from E007-M02.
- E007-M04 should report full-denominator and source-ready subset metrics separately because 216 / 1,170 query-policy rows remain source-limited.

## E007-M04

Implementation unit: `E007-M04_path_cost_policy_metrics_v0`.

Facts:

- Status: `e007_m04_path_cost_policy_metrics_ready_with_source_limits`.
- Query rows: 195.
- Query-policy rows: 1,170.
- Path source-ready query-policy rows: 972.
- Source-limited query-policy rows: 198.
- Method policy: `h001_then_conceptgraphs_top5_on_observed_miss_v0`.
- Method full-denominator success: 181 / 195 = 0.928205.
- Method source-ready path success: 163 / 174 = 0.936782.
- Method mean path cost: 2.996131m.
- Method mean `PathAttemptSPLProxy`: 0.824554.
- Paired source-ready delta vs `real_static_memory_only_v0`: success +0.178161, `PathAttemptSPLProxy` +0.065933, path cost +2.996131m.
- Paired source-ready delta vs `conceptgraphs_only_strict_top5_v0`: success +0.312925, `PathAttemptSPLProxy` +0.564378, path cost -5.576065m.
- Paired source-ready delta vs `h001_real_task_context_memory_trust_v0`: success +0.054545, `PathAttemptSPLProxy` +0.004390, path cost +0.941948m.
- Selected next unit: E007-M05 path-cost result interpretation and paper-table boundary decision.

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/evaluate_m04_path_cost_policy_metrics.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/query_policy_metric_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/policy_metric_summary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/paired_policy_delta_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/context_metric_summary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M04_path_cost_policy_metrics_v0/report.md`

Agent inference:

- E007-M04 gives a stronger path-cost bridge than M100's raw visit-count metric, but the correct framing is cost-aware repair tradeoff.
- H001 + `ConceptGraphs` fallback improves success over H001-only on paired source-ready rows, but it also increases path cost, so it should not be written as unconditional dominance.

## E007-M05

Implementation unit: `E007-M05_path_cost_result_interpretation_v0`.

Facts:

- Status: `e007_m05_path_cost_result_interpretation_ready`.
- Selected table role: `paper_facing_occupancy_grid_path_cost_bridge_table`.
- Method policy: `h001_then_conceptgraphs_top5_on_observed_miss_v0`.
- E007-M04 bridge table ready: true.
- Main navigation table ready: false.
- Real navigation `SR` / `SPL` ready: false.
- `OldLocationDeadEndCostM` primary metric ready: false.
- Source-limited query-policy rows: 198 / 1,170.
- Upstream expected-search-cost stop rows: 47 / 1,170.
- Selected next unit: E007-M06 path-start/source-limit sensitivity and reviewer-defense audit.

Bridge-table rows:

| Policy | Full success | Source ready | Path success | Path cost | `PathAttemptSPLProxy` | Source-limited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `real_static_memory_only_v0` | 141 / 195 | 183 / 195 | 132 / 183 | 0.000000 | 0.721311 | 12 / 195 |
| `real_detector_confidence_top5_v0` | 51 / 195 | 126 / 195 | 42 / 126 | 15.109528 | 0.101173 | 69 / 195 |
| `conceptgraphs_only_strict_top5_v0` | 114 / 195 | 153 / 195 | 96 / 153 | 9.304745 | 0.222307 | 42 / 195 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 156 / 195 | 168 / 195 | 144 / 168 | 1.570337 | 0.841430 | 27 / 195 |
| `h001_real_task_context_memory_trust_v0` | 157 / 195 | 168 / 195 | 145 / 168 | 1.837889 | 0.841561 | 27 / 195 |
| `h001_then_conceptgraphs_top5_on_observed_miss_v0` | 181 / 195 | 174 / 195 | 163 / 174 | 2.996131 | 0.824554 | 21 / 195 |

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/plan_m05_path_cost_result_interpretation.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/bridge_table_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/paper_boundary_decision_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/reviewer_defense_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/route_decision_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M05_path_cost_result_interpretation_v0/report.md`

Agent inference:

- E007-M04 should be used as a paper-facing occupancy-grid path-cost bridge table, not as final navigation evidence.
- The method is clearly better than static memory, detector-confidence ranking, and `ConceptGraphs`-only under paired source-ready path metrics.
- Against H001-only, the result is a repair tradeoff: success and `PathAttemptSPLProxy` improve slightly while path cost increases.
- E007-M06 should quantify sensitivity to source-limited rows, stop-rank fallback, and the old-memory path-start assumption before any real navigation expansion.

## E007-M06

Implementation unit: `E007-M06_path_start_source_limit_sensitivity_v0`.

Facts:

- Status: `e007_m06_path_start_source_limit_sensitivity_ready`.
- Query-policy rows: 1,170.
- Source-limited query-policy rows: 198.
- Stop-rank query-policy rows: 47.
- Old-first non-target zero-step route rows: 153.
- Bridge table defensible with proxy boundary: true.
- Real navigation `SR` / `SPL` ready: false.
- `OldLocationDeadEndCostM` primary metric ready: false.
- Selected next unit: E007-M07 bridge-table package and navigation-expansion decision.

Sensitivity table:

| Policy | Full success | Source-ready lower bound | Direct/failure lower bound | Stop-rank rows | Source-limited | Old-start non-target zero |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `real_static_memory_only_v0` | 141 / 195 | 132 / 195 | 132 / 195 | 0 | 12 | 54 |
| `real_detector_confidence_top5_v0` | 51 / 195 | 42 / 195 | 42 / 195 | 0 | 69 | 0 |
| `conceptgraphs_only_strict_top5_v0` | 114 / 195 | 96 / 195 | 96 / 195 | 0 | 42 | 0 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 156 / 195 | 144 / 195 | 132 / 195 | 15 | 27 | 33 |
| `h001_real_task_context_memory_trust_v0` | 157 / 195 | 145 / 195 | 132 / 195 | 16 | 27 | 33 |
| `h001_then_conceptgraphs_top5_on_observed_miss_v0` | 181 / 195 | 163 / 195 | 150 / 195 | 16 | 21 | 33 |

Stricter direct/failure source-ready paired deltas for method:

| Baseline | Paired rows | Success delta | Path cost delta | `PathAttemptSPLProxy` delta |
| --- | ---: | ---: | ---: | ---: |
| `real_static_memory_only_v0` | 161 | +0.111801 | +2.851324m | +0.012982 |
| `real_detector_confidence_top5_v0` | 110 | +0.636364 | -13.038231m | +0.794171 |
| `conceptgraphs_only_strict_top5_v0` | 134 | +0.291045 | -5.322252m | +0.559209 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 152 | +0.059211 | +1.246704m | +0.004766 |
| `h001_real_task_context_memory_trust_v0` | 152 | +0.059211 | +1.022509m | +0.004766 |

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/audit_m06_path_start_source_limit_sensitivity.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/policy_sensitivity_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/paired_delta_sensitivity_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/reviewer_defense_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/claim_boundary_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/route_decision_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M06_path_start_source_limit_sensitivity_v0/report.md`

Agent inference:

- E007 bridge table is defensible as an occupancy-grid path-cost proxy table if full denominator, source-ready lower bound, and direct/failure-only sensitivity are reported together.
- The result remains strongest against static memory, detector-confidence ranking, and `ConceptGraphs`-only.
- Method-vs-H001 remains a repair tradeoff rather than path-cost optimality.
- `OldLocationDeadEndCostM` should stay blocked until a robot/start-pose or executed navigation source exists.

## E007-M07

Implementation unit: `E007-M07_bridge_table_package_navigation_decision_v0`.

Facts:

- Status: `e007_m07_bridge_table_package_navigation_decision_ready`.
- Paper table package ready: true.
- Bridge table role: `paper_facing_occupancy_grid_path_cost_proxy_table`.
- Table rows: 6.
- Allowed claim rows: 3.
- Blocked claim rows: 3.
- Real navigation `SR` / `SPL` ready: false.
- `OldLocationDeadEndCostM` primary metric ready: false.
- Final real RGB-D/open-vocabulary robustness ready: false.
- Selected next unit: E008-M01 real navigation benchmark/source preflight and episode contract.
- Launch long job now: false.

Final E007 table:

| Policy | Full success | Source-ready lower bound | Direct/failure lower bound | Path cost | `PathAttemptSPLProxy` | Source-limited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `real_static_memory_only_v0` | 141 / 195 | 132 / 195 | 132 / 195 | 0.000000 | 0.721311 | 12 / 195 |
| `real_detector_confidence_top5_v0` | 51 / 195 | 42 / 195 | 42 / 195 | 15.109528 | 0.101173 | 69 / 195 |
| `conceptgraphs_only_strict_top5_v0` | 114 / 195 | 96 / 195 | 96 / 195 | 9.304745 | 0.222307 | 42 / 195 |
| `real_context_agnostic_memory_trust_reobserve_v0` | 156 / 195 | 144 / 195 | 132 / 195 | 1.570337 | 0.841430 | 27 / 195 |
| `h001_real_task_context_memory_trust_v0` | 157 / 195 | 145 / 195 | 132 / 195 | 1.837889 | 0.841561 | 27 / 195 |
| `h001_then_conceptgraphs_top5_on_observed_miss_v0` | 181 / 195 | 163 / 195 | 150 / 195 | 2.996131 | 0.824554 | 21 / 195 |

Command:

```bash
python experiments/E007_navigation_path_cost_bridge/tools/plan_m07_bridge_table_navigation_decision.py
```

Artifacts:

- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/coverage.json`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/paper_table_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/claim_evidence_ledger_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/reviewer_defense_package_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/navigation_expansion_decision_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/next_action_rows.jsonl`
- `experiments/E007_navigation_path_cost_bridge/artifacts/E007-M07_bridge_table_package_navigation_decision_v0/report.md`

Agent inference:

- E007 is complete as an occupancy-grid path-cost proxy bridge table.
- The defensible claim is that H001 + `ConceptGraphs` fallback improves proxy path-cost search over static memory, detector-confidence ranking, and `ConceptGraphs`-only.
- Against H001-only, the correct phrasing is map-assisted repair tradeoff: higher success with extra path cost, not path-cost optimality.
- The next top-tier bottleneck is not another proxy table; it is E008-M01 benchmark/source preflight for real navigation episodes.
