# CAND-001

Updated: 2026-05-06

## Candidate Summary

`Intent- and Staleness-Aware Semantic Mapping`

사람 지시를 수행하는 robot이 semantic map 안의 object memory를 모두 동일하게 신뢰하지 않고, task relevance와 staleness에 따라 어떤 object/relation을 믿고 다시 확인할지 결정하는 방향이다.

## Source Literature

- `Clio`
- `DualMap`
- `OpenIN`
- `OpenMap`
- `HOV-SG`
- `LangMap`
- `OVI-MAP`
- `OGScene3D`

## Hypothesis Queue

| ID | Status | Short title | Next action |
| --- | --- | --- | --- |
| H001 | Main experiment transition accepted | [stale-object-memory](H001_stale-object-memory/README.md) | Continue E001 in `experiments/` |

## Current Gate

- Consolidated H001 docs:
  - [Setup](H001_stale-object-memory/01_setup.md)
  - [Data](H001_stale-object-memory/02_data.md)
  - [Gates](H001_stale-object-memory/03_gates.md)
  - [Method](H001_stale-object-memory/04_method.md)
  - [Results](H001_stale-object-memory/05_results.md)
  - [Summary](H001_stale-object-memory/06_summary.md)
- Current strict artifact: 12 validated pairs, 94 query rows, 10 significant moved rows, 48 low-motion controls.
- `uncertainty_topk_v0`: Recall@returned K 1.0000, mean `ExpectedSearchCost` 1.3000, stale FP 0.0000.
- `search_cost_bridge_gate`: proxy search success 1.0000, `AttemptSPL` proxy 0.883333, mean checked locations 1.3000.
- `perception_noise_gate`: `robustness_pass`, `ranking_noise_moderate` observable-target success 0.9040, `AttemptSPL` proxy 0.6448.
- `task_context_gate`: `conditioning_pass`, `high_value_fetch` observable-target success 0.9880, `heavy_noise_stress` / `noisy_high_value_fetch` observable-target success 0.9304.
- `budget_baseline_gate`: `budget_baseline_pass`, `routine_fetch` success/returned-location 0.3811 vs `always_top5` 0.2754, `high_value_fetch` matches `always_top5`.
- Safe claim: `Task-Conditioned Stale Semantic Memory Update`.
- Main experiment readiness gate: `ready_with_constraints`.
- Main experiment transition: accepted for `E001_semantic_pair_dynamic_search_proxy`.
