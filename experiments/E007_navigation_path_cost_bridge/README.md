# E007 Navigation Path-Cost Bridge

Updated: 2026-05-27

## Status

E007 starts after E005-M101 selected `paper_table_integration_and_navigation_bridge_next`. E007-M01 defines the contract for connecting the M100 query-level candidate visit order to path-aware search/navigation proxy metrics. It does not report real navigation `SR` / `SPL`.

Next unit: E007-M02 path-source compatibility and candidate-route materialization audit.

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
| command | `python experiments/E007_navigation_path_cost_bridge/tools/plan_m01_navigation_path_cost_bridge_contract.py` |
| output | Contract, source readiness rows, metric contract rows, baseline rows, claim boundary rows, and command plan rows. |
| conclusion | E007-M01 supports a path-cost bridge contract only. E007-M02 must audit candidate route materialization before path metrics are reported. |

## E007-M01

Implementation unit: `E007-M01_navigation_path_cost_bridge_contract_v0`.

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
- The next defensible step is E007-M02 candidate route materialization and source-compatibility audit.
