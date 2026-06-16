# E002 Path Cost Bridge

Updated: 2026-06-16

## Status

`E002-M01_path_cost_inputs_v0`, `E002-M02_path_policy_evaluation_v0`, E002 claim/source planning, `E002-M05_occupancy_grid_astar_v0`, `E002-M06_grid_path_policy_evaluation_v0`, `E002-M07_grid_failure_source_analysis_v0`, `E002-M08_source_quality_filtered_grid_eval_v0`, and `E002-M09_reachable_first_scoring_v0` are complete. Next unit is E003 perception-noise expansion.

## Source

- Source experiment: `experiments/E001_semantic_pair_dynamic_search_proxy/`
- Workflow rule: `docs/experiments.md`
- Input query artifact: `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/query_rows.jsonl`
- Input candidate artifact: `experiments/E001_semantic_pair_dynamic_search_proxy/artifacts/E001-M02_query_construction_v0/candidate_rows.jsonl`

## 사실

- E001 currently provides annotation-level semantic-pair dynamic object search proxy rows.
- E001 has no real navigation mesh, occupancy map, or robot trajectory.
- E001 candidate rows already preserve `candidate_path_cost_m` as nullable placeholder.
- E002 starts by attaching a controlled path-cost proxy and path-aware visit order to the E001 query/candidate rows.
- Local `3RScan` payloads include annotated PLY, `semseg.v2.json`, and segment JSON for staged scans.
- Local payload inspection did not find a ready navmesh or robot trajectory source for E002.

## 논문 주장

E002-M01 can support:

- path-cost bridge input construction.
- old-location dead-end cost modeling as a controlled proxy.
- path-aware candidate visit order construction.

E002-M02 can support:

- path-cost proxy policy comparison using the E001 denominator.
- comparison among static old-location, fixed top-k, task-conditioned, path-aware, and oracle policies.
- old-location dead-end failure accounting under `euclidean_polyline_proxy_v0`.

E002-M05 can support:

- free-space path-cost smoke construction from local `3RScan` geometry.
- explicit reachable/unreachable accounting under `occupancy_grid_astar_v0`.

E002-M06 can support:

- policy comparison under `occupancy_grid_astar_v0`.
- grid-path upper-bound comparison against `oracle_current_target`.
- failure accounting for target-unreachable and returned-unreachable candidate rows.

E002-M07 can support:

- separating occupancy-grid source limits from policy failures.
- blocking a positive claim for naive `grid_path_aware_task_conditioned_budget_v0`.
- motivating a source-quality mask before method revision.

E002-M08 can support:

- source-quality-filtered grid-path proxy metric reporting.
- using `target_reachable_eval` as the primary grid-path proxy denominator.
- treating `all_candidates_reachable_eval` as a strict sensitivity diagnostic.

E002-M09 can support:

- reachable-first semantic grid scoring under the source-filtered grid-path proxy.
- reducing returned-unreachable attempts without recall loss against `task_conditioned_budget_v0`.
- treating reachable-first scoring as a method cleanup, not a standalone navigation policy claim.

E002-M01/M02/M05/M06/M07/M08/M09 cannot support:

- real navigation `SR` / `SPL`.
- deployable search policy.
- collision-aware path planning.
- RGB-D or open-vocabulary perception robustness.

## E002 Contract

| Field | Required content |
| --- | --- |
| question | Can E001 dynamic object search proxy rows be converted into path/search-cost rows without changing the query denominator? |
| hypothesis | A controlled path-cost proxy can expose whether stale-memory suppression and task-conditioned candidate budgets remain useful when candidate visits are costed by spatial travel rather than candidate count. |
| dataset | E001 M02 query/candidate artifacts generated from locally ready `3RScan` / `3DSSG` pairs. |
| method | Attach `candidate_path_cost_m`, old-location dead-end cost, and path-aware candidate visit order using a declared proxy profile. |
| comparison | M02 compares static old-location, fixed top-k, task-conditioned, path-aware, and oracle policies. M06 repeats the comparison under `occupancy_grid_astar_v0`. M08 recomputes metrics after source-quality masking. M09 compares `task_conditioned_budget_v0` with `reachable_first_task_conditioned_budget_v0`. |
| metrics | M01 records coverage and path-cost proxy availability. M02 records proxy `SR`, path cost, `AttemptSPL` proxy, utility, stale FP, and low-motion preservation. M05 records grid reachability and A* path cost coverage. M06 records grid proxy `SR`, grid cost, grid `AttemptSPL` proxy, utility, stale FP, target-unreachable rate, and returned-unreachable rate. M07 separates source limits, returned-unreachable policy cases, and grid-aware ordering regressions. M08 records `target_reachable_eval`, `source_limited_target_grid_unreachable`, and `all_candidates_reachable_eval` metrics. M09 records success loss/gain and returned-unreachable deltas. |
| command | `python experiments/E002_path_cost_bridge/tools/build_path_cost_inputs.py`; `python experiments/E002_path_cost_bridge/tools/evaluate_path_policies.py`; `python experiments/E002_path_cost_bridge/tools/build_occupancy_grid_paths.py`; `python experiments/E002_path_cost_bridge/tools/evaluate_grid_path_policies.py`; `python experiments/E002_path_cost_bridge/tools/analyze_grid_failures.py`; `python experiments/E002_path_cost_bridge/tools/evaluate_source_quality_filtered_grid.py`; `python experiments/E002_path_cost_bridge/tools/evaluate_reachable_first_scoring.py` |
| output | path rows, grid rows, predictions, failure rows, metrics, coverage, reports. |
| conclusion | Claim supported only if every E001 query row receives path-cost bridge fields without denominator drift and policy evaluation keeps real-navigation claims unsupported. |

## E002-M01 Path Cost Input Unit

Implementation unit: `E002-M01_path_cost_inputs_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/build_path_cost_inputs.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0/path_query_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0/path_candidate_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M01_path_cost_inputs_v0/report.md`

사실:

- Path-cost source is initially `euclidean_polyline_proxy`, not navmesh geodesic distance.
- Candidate visit starts from the old scene-aligned memory location.
- `candidate_path_cost_m` is direct Euclidean distance from old memory location to candidate centroid.
- `candidate_path_cumulative_cost_m` is cumulative Euclidean travel under path-aware candidate order.
- `old_location_dead_end_cost_m` is a fixed distance-equivalent inspection penalty for stale significant moved rows.
- Query rows: 294.
- Candidate rows: 1248.
- Rows with path-cost proxy: 294.
- Rows with real navigation path cost: 0.
- Old-location dead-end rows: 33.
- Denominator preserved: true.

논문 주장:

- E002-M01 supports bridge preparation only.
- E002-M01 does not convert E001 into a real navigation benchmark.

에이전트 추론:

- This is the smallest defensible bridge from candidate-count `ExpectedSearchCost` to path/search-cost evaluation.
- Real `SPL` should remain unsupported until path cost comes from a navigation mesh, occupancy grid, simulator, or robot trajectory.

사용자 판단 필요:

- None for M01/M02. Claim boundary and source planning are recorded in E002-M03/M04 below.

## E002-M02 Path Policy Evaluation Unit

Implementation unit: `E002-M02_path_policy_evaluation_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/evaluate_path_policies.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0/predictions.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0/failure_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0/metrics.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M02_path_policy_evaluation_v0/report.md`

사실:

- Status: `path_policy_eval_ready`.
- Query rows: 294.
- Candidate rows: 1248.
- Prediction rows: 2646.
- Failure rows: 191.
- Path-cost profile: `euclidean_polyline_proxy_v0`.
- Real navigation path-cost rows: 0.
- Significant moved `routine_fetch` static old-location proxy `SR`: 0.000000.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` proxy `SR`: 0.727273, path cost 1.718859, `AttemptSPL` proxy 0.688026.
- Significant moved `routine_fetch` `path_aware_task_conditioned_budget_v0` proxy `SR`: 0.727273, path cost 1.718859, `AttemptSPL` proxy 0.688026.
- Significant moved `high_value_fetch` `task_conditioned_budget_v0` proxy `SR`: 0.909091, path cost 2.649124, `AttemptSPL` proxy 0.763075.
- Low-motion preservation for `task_conditioned_budget_v0` and `path_aware_task_conditioned_budget_v0`: 1.000000.

논문 주장:

- E002-M02 supports path-cost proxy comparison, not real navigation evaluation.
- E002-M02 supports the claim that stale old-location memory is harmful on significant moved rows under the proxy setup.
- E002-M02 supports the claim that task-conditioned budget changes the search-cost/recall trade-off under proxy path cost.

에이전트 추론:

- Current path-aware ordering is not yet a separate contribution because it ties `task_conditioned_budget_v0` on the key significant moved summaries.
- The strongest E002 result is the bridge from candidate-count search to path-cost proxy evaluation while preserving denominator and low-motion behavior.
- A real top-tier navigation/search claim still needs a path-cost source beyond `euclidean_polyline_proxy_v0`.

사용자 판단 필요:

- None for M02. Claim boundary and source planning are recorded in E002-M03/M04 below.

## E002-M03 Claim Boundary

Stage: summary added to this README.

사실:

- E002-M02 preserves the E001 query denominator: 294 query rows.
- E002-M02 uses 1248 candidate rows and emits 2646 policy prediction rows.
- E002-M02 uses `euclidean_polyline_proxy_v0`.
- Real navigation path-cost rows: 0.
- Significant moved `routine_fetch` static old-location proxy `SR`: 0.000000, stale FP 1.000000.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` proxy `SR`: 0.727273, path cost 1.718859, `AttemptSPL` proxy 0.688026.
- Significant moved `routine_fetch` `always_top5` proxy `SR`: 0.909091, path cost 2.649124, `AttemptSPL` proxy 0.763075.
- Significant moved `high_value_fetch` `task_conditioned_budget_v0` proxy `SR`: 0.909091, path cost 2.649124, `AttemptSPL` proxy 0.763075.
- Low-motion preservation for `task_conditioned_budget_v0`: 1.000000.

논문 주장:

- Supported: E002 converts stale semantic-memory search rows into a denominator-preserving path-cost proxy evaluation.
- Supported: stale old-location memory is harmful on significant moved rows under this proxy.
- Supported: task context changes the recall/cost trade-off under proxy path cost.
- Supported with caution: `high_value_fetch` expands budget and matches `always_top5` behavior on significant moved rows.
- Not supported: real navigation `SR` / `SPL`, collision-aware path planning, deployable search policy, real RGB-D robustness, open-vocabulary perception robustness.

에이전트 추론:

- The safe paper phrasing is search-cost proxy, not navigation performance.
- The useful contribution signal is not simply higher `SR`; it is task-conditioned memory trust and candidate budget under stale semantic memory.
- `path_aware_task_conditioned_budget_v0` is not yet a separate method contribution because its key significant moved summaries tie `task_conditioned_budget_v0`.
- The next top-tier-relevant gap is replacing straight-line proxy cost with free-space constrained path cost.

사용자 판단 필요:

- None. The next implementation should target a real path-cost source before claiming navigation-style metrics.

## E002-M04 Path Source Plan

Stage: plan added to this README.

사실:

- Available local source: `local_dataset/3RScan/scans/<scan_id>/labels.instances.annotated.v2.ply`.
- Available local source: `local_dataset/3RScan/scans/<scan_id>/semseg.v2.json`.
- Available local source: `local_dataset/3RScan/scans/<scan_id>/mesh.refined.0.010000.segs.v2.json`.
- Partial source: `sequence.zip` exists for some scans but not all staged ready pairs.
- Missing source: ready navmesh.
- Missing source: robot trajectory log.

논문 주장:

- The next step can upgrade E002 from `euclidean_polyline_proxy_v0` to a free-space path-cost benchmark proxy.
- This still will not be a deployable navigation policy unless it is later connected to simulator execution, robot execution, or trajectory replay.

에이전트 추론:

- Primary route should be `occupancy_grid_astar_v0`.
- Reason: it uses the locally available PLY/semantic payloads, can be applied to the existing E001/E002 denominator, and directly tests whether obstacle-constrained travel changes the stale-memory search conclusions.
- Secondary route is `camera_trajectory_graph_v0` from `sequence.zip`; it is useful for RGB-D/perception replay but weak as a complete path-cost source because sequence availability is partial.
- Heavier route is simulator/navmesh integration; it is more publishable for navigation `SR` / `SPL`, but has higher setup risk and should come after the occupancy-grid smoke.

Planned `occupancy_grid_astar_v0` contract:

- Input: E002 path query/candidate rows, scan PLY, `semseg.v2.json`, segment JSON.
- Free-space source: floor-plane points from semantic labels when available; otherwise robust floor-height estimate.
- Obstacle source: non-floor points above floor within robot-height band, inflated by a fixed robot radius.
- Start: old scene-aligned memory centroid projected to nearest free cell.
- Goals: candidate centroids projected to nearest free cells.
- Cost: 2D grid shortest path length via `A*` or Dijkstra.
- Output fields: `candidate_grid_path_cost_m`, `candidate_grid_reachable`, `grid_path_cost_profile_id`, `nearest_free_cell_distance_m`.
- Failure rows: missing payload, no floor support, start unreachable, candidate unreachable, disconnected component.
- Minimum smoke gate: preserve the 294 query denominator and produce reachable path cost for a reportable subset; disconnected rows must remain explicit rather than dropped.

사용자 판단 필요:

- None for route selection. Use `occupancy_grid_astar_v0` as the next E002 implementation unit.

## E002-M05 Occupancy Grid A*

Implementation unit: `E002-M05_occupancy_grid_astar_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/build_occupancy_grid_paths.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/grid_query_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/grid_candidate_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/scan_grid_summaries.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/failure_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M05_occupancy_grid_astar_v0/report.md`

사실:

- Status: `grid_path_cost_smoke_ready`.
- Query rows: 294.
- Candidate rows: 1248.
- Denominator preserved: true.
- Scan grids ready: 13 / 13.
- Query rows with free-space path source: 288.
- Candidate rows reachable: 1029.
- Candidate rows unreachable: 219.
- Target rows reachable: 267.
- Target rows unreachable: 27.
- Target grid path cost mean over reachable rows: 0.663882m.
- Significant moved target rows reachable: 27 / 33; mean target grid path cost 1.719008m.
- Mid-motion target rows reachable: 90 / 108; mean target grid path cost 1.017303m.
- Low-motion target rows reachable: 150 / 153; mean target grid path cost 0.261907m.
- Failure types: `disconnected_free_space` 168, `start_unprojectable` 30, `candidate_unprojectable` 21.
- Real navigation path-cost rows: 0.

논문 주장:

- E002-M05 supports free-space path-cost smoke construction from local `3RScan` PLY/semseg geometry.
- E002-M05 supports using `occupancy_grid_astar_v0` as a stronger path-cost proxy than `euclidean_polyline_proxy_v0` for reachable rows.
- E002-M05 does not support real navigation `SR` / `SPL`, simulator execution, collision-aware robot planning, or deployable search policy claims.

에이전트 추론:

- This is a useful top-tier path step because it tests whether stale-memory conclusions survive obstacle-constrained free-space cost, not just straight-line distance.
- The main limitation is that unreachable rows reflect both real layout constraints and grid-construction artifacts; they should be analyzed rather than dropped.
- Next evaluation should reuse the existing static/top-k/task-conditioned/oracle policies with grid path cost fields.

사용자 판단 필요:

- None for E002-M05. Continue to grid-path policy evaluation.

## E002-M06 Grid Path Policy Evaluation

Implementation unit: `E002-M06_grid_path_policy_evaluation_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/evaluate_grid_path_policies.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0/predictions.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0/failure_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0/metrics.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M06_grid_path_policy_evaluation_v0/report.md`

사실:

- Status: `grid_path_policy_eval_ready`.
- Query rows: 294.
- Candidate rows: 1248.
- Prediction rows: 2646.
- Failure rows: 387.
- Target grid reachable rows: 267 / 294.
- Real navigation path-cost rows: 0.
- Significant moved `routine_fetch` `scene_aligned_static_map` grid proxy `SR`: 0.000000, stale FP 1.000000.
- Significant moved `routine_fetch` `task_conditioned_budget_v0` grid proxy `SR`: 0.636364, grid cost 1.339705, grid `AttemptSPL` proxy 0.622032.
- Significant moved `routine_fetch` `grid_path_aware_task_conditioned_budget_v0` grid proxy `SR`: 0.545455, grid cost 1.370743, grid `AttemptSPL` proxy 0.501318.
- Significant moved `routine_fetch` `always_top5` grid proxy `SR`: 0.727273, grid cost 2.810983, grid `AttemptSPL` proxy 0.658045.
- Significant moved `routine_fetch` `oracle_current_target` grid proxy `SR`: 0.818182.
- Significant moved `high_value_fetch` `task_conditioned_budget_v0` grid proxy `SR`: 0.727273, grid cost 2.810983, grid `AttemptSPL` proxy 0.658045.
- Low-motion `task_conditioned_budget_v0` preservation: 0.980392.
- Failure types: `target_grid_unreachable` 237, `target_outside_returned_budget` 56, `static_map_localization_error` 48, `stale_old_location_returned` 33, `returned_unreachable_candidate` 13.

논문 주장:

- E002-M06 supports policy comparison under `occupancy_grid_astar_v0` free-space path-cost proxy.
- E002-M06 supports the claim that stale old-location memory fails on significant moved rows under grid-path evaluation.
- E002-M06 supports the claim that task-conditioned budget remains useful under grid cost, but it does not dominate `always_top5` or `oracle_current_target`.
- E002-M06 does not support a claim that grid-aware candidate ordering is better than semantic task-conditioned ranking.
- E002-M06 does not support real navigation `SR` / `SPL`, simulator execution, collision-aware robot planning, or deployable search policy claims.

에이전트 추론:

- The top-tier-relevant result is now more nuanced: task-conditioned stale-memory update survives the grid-path proxy, but path-aware ordering needs a better objective than nearest-free-space ordering.
- The oracle gap is partly due to target-unreachable rows, so source/failure analysis should happen before expanding the claim.
- `always_top5` remains an important baseline because high-value task-conditioned behavior often matches or approaches broad-budget search.

사용자 판단 필요:

- None for E002-M06. Continue to grid-path failure/source analysis.

## E002-M07 Grid Failure Source Analysis

Implementation unit: `E002-M07_grid_failure_source_analysis_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/analyze_grid_failures.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0/target_source_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0/returned_unreachable_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0/grid_aware_comparison_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0/summary.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M07_grid_failure_source_analysis_v0/report.md`

사실:

- Status: `grid_failure_source_analysis_ready`.
- Grid query rows: 294.
- Target-unreachable query rows: 27.
- Target-unreachable base rows: 9.
- Target-unreachable rate: 0.091837.
- Target source failures: `disconnected_free_space` 15, `candidate_unprojectable` 6, `start_unprojectable` 6.
- Returned-unreachable prediction rows: 331.
- Returned-unreachable rows with reachable target: 144.
- Returned-unreachable rows dominated by source limitation: 187.
- Grid-aware vs task-conditioned comparison over all rows: success gain 0, success loss 2, cost improvement 7, cost regression 13, mean utility delta -0.012863.
- Grid-aware vs task-conditioned comparison over significant moved rows: success gain 0, success loss 1, cost improvement 2, cost regression 5, mean utility delta -0.057127.

논문 주장:

- E002-M07 supports separating occupancy-grid source limitations from policy failures.
- E002-M07 supports keeping `target_grid_unreachable` rows explicit rather than silently dropping them.
- E002-M07 does not support a positive claim for `grid_path_aware_task_conditioned_budget_v0`.
- E002-M07 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.

에이전트 추론:

- The source-quality issue is now a first-class evaluation contract problem, not only an implementation detail.
- Naive grid-aware ordering reduces some unreachable returns but loses recall under fixed budgets, so the next method revision should not claim path-aware ordering yet.
- The next defensible step is to define a source-quality mask that separates `target_grid_reachable` evaluation from source-limit diagnostics.

사용자 판단 필요:

- None for E002-M07. Continue to source-quality mask design and filtered grid-path evaluation.

## E002-M08 Source-Quality Filtered Grid Evaluation

Implementation unit: `E002-M08_source_quality_filtered_grid_eval_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/evaluate_source_quality_filtered_grid.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/source_quality_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/source_limit_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/filtered_predictions.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/target_reachable_failure_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/metrics.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M08_source_quality_filtered_grid_eval_v0/report.md`

사실:

- Status: `source_quality_filtered_grid_eval_ready`.
- Query rows: 294.
- Target-reachable eval rows: 267.
- Source-limited target-unreachable rows: 27.
- All-candidates-reachable sensitivity rows: 198.
- Target-reachable eval prediction rows: 2403.
- Target-reachable eval failure rows: 144.
- Source failures: `disconnected_free_space` 15, `candidate_unprojectable` 6, `start_unprojectable` 6.
- Target-reachable significant moved `routine_fetch` `task_conditioned_budget_v0` grid proxy `SR`: 0.777778, grid cost 1.415195, grid `AttemptSPL` proxy 0.760261.
- Target-reachable significant moved `routine_fetch` `always_top5` grid proxy `SR`: 0.888889.
- Target-reachable significant moved `routine_fetch` `oracle_current_target` grid proxy `SR`: 1.000000.
- Target-reachable significant moved `high_value_fetch` `task_conditioned_budget_v0` grid proxy `SR`: 0.888889, matching `always_top5`.
- Target-reachable significant moved `grid_path_aware_task_conditioned_budget_v0` remains below task-conditioned on `routine_fetch`: `SR` delta -0.111111.

논문 주장:

- E002-M08 supports reporting source-quality-filtered grid-path proxy metrics separately from source-limited rows.
- E002-M08 supports `target_reachable_eval` as the primary grid-path proxy denominator.
- E002-M08 does not support a positive claim for naive `grid_path_aware_task_conditioned_budget_v0`.
- E002-M08 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.

에이전트 추론:

- The filtered denominator makes the oracle upper bound interpretable because target-reachable oracle `SR` becomes 1.000000.
- The core method signal is still task-conditioned stale-memory suppression and budget control, not path-aware ordering.
- `all_candidates_reachable_eval` is useful as a sensitivity diagnostic, but it leaves only 4 significant moved `routine_fetch` rows and should not be the primary denominator.

사용자 판단 필요:

- None for E002-M08. Continue with reachable-first semantic grid scoring revision before E003 perception-noise expansion.

## E002-M09 Reachable-First Semantic Grid Scoring

Implementation unit: `E002-M09_reachable_first_scoring_v0`.

Stage: script and artifacts generated.

Command:

```bash
python experiments/E002_path_cost_bridge/tools/evaluate_reachable_first_scoring.py
```

Artifacts:

- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/reachable_first_predictions.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/comparison_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/strict_comparison_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/failure_rows.jsonl`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/metrics.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/coverage.json`
- `experiments/E002_path_cost_bridge/artifacts/E002-M09_reachable_first_scoring_v0/report.md`

사실:

- Status: `reachable_first_scoring_gate_pass`.
- Target-reachable eval rows: 267.
- Strict all-candidates-reachable rows: 198.
- Reachable-first prediction rows: 267.
- Target-reachable success loss rows: 0.
- Target-reachable success gain rows: 0.
- Target-reachable returned-unreachable delta total: -6.
- Target-reachable mean cost delta: -0.018727.
- Target-reachable mean utility delta: +0.002809.
- Target-reachable significant moved `routine_fetch` `task_conditioned_budget_v0` `SR`: 0.777778, returned-unreachable rate 0.111111, count 1.
- Target-reachable significant moved `routine_fetch` `reachable_first_task_conditioned_budget_v0` `SR`: 0.777778, returned-unreachable rate 0.000000, count 0.
- Target-reachable significant moved `high_value_fetch` `reachable_first_task_conditioned_budget_v0` preserves `SR`: 0.888889.

논문 주장:

- E002-M09 supports reachable-first semantic grid scoring as a source-filtered grid-path proxy revision.
- E002-M09 supports a returned-unreachable reduction claim against `task_conditioned_budget_v0` under `target_reachable_eval`.
- E002-M09 does not support real navigation `SR` / `SPL`, deployable search policy, collision-aware robot planning, or RGB-D/open-vocabulary robustness claims.

에이전트 추론:

- This revision is safer than naive grid-path ordering because it preserves semantic rank among reachable candidates and only demotes grid-unreachable candidates.
- The positive result should be treated as E002 method cleanup, not the main paper contribution by itself.

사용자 판단 필요:

- None for E002-M09. Continue to E003 perception-noise expansion.
