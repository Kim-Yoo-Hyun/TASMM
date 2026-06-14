# Research Summary

Updated: 2026-06-14

## Research Direction

사실:

- 연구 축은 semantic mapping 기반 human-friendly robot intelligence다.
- Active candidate는 `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`이다.
- Active hypothesis는 `H001_stale-object-memory`다.
- 최종 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이며, AI, ML, CV, Robotics top-tier journal/conference를 겨냥한다.
- 현재 main experiment는 `E008_real_navigation_benchmark`의 source-pool scale branch를 M198까지 완료했고, M199 failure decomposition / candidate-generation repair decision이 다음 gate다.

논문 주장 후보:

- Semantic map은 물체 위치를 저장하는 구조를 넘어, stale memory를 언제 믿고, 언제 재관측하며, 어떤 후보를 먼저 방문할지 결정하는 action-facing memory interface여야 한다.

## Research Background

사실:

- 최근 semantic mapping, 3D scene graph, open-vocabulary mapping 연구는 RGB-D sequence, VLM/LLM reasoning, embodied search/navigation과 결합되고 있다.
- Robotics 관점에서는 map construction 자체보다 search, navigation, manipulation, instruction following 같은 downstream behavior가 실제로 좋아지는지가 중요하다.
- `ConceptGraphs`, `Open3DSG`, `HOV-SG`, `3D-Mem`, `VLFM`, `HM3D-OVON` 같은 계열은 open-vocabulary map, scene memory, navigation baseline으로 reviewer pressure를 제공한다.

에이전트 추론:

- Dynamic object search/navigation에서는 stale memory, RGB-D/open-vocabulary proposal noise, path/search cost, task context가 동시에 충돌한다.
- Top-tier claim은 "기존 map이 dynamic object에 약하다"가 아니라, 왜 naive memory/retrieval/ranking이 실패하고 그 실패 때문에 어떤 decision layer가 필요한지를 보여야 한다.

## Motivation

사실:

- 실내 물체는 이동하고, old semantic memory는 stale해질 수 있다.
- Old memory를 그대로 믿으면 stale old-location failure가 발생한다.
- Old memory를 완전히 버리면 반복적으로 유용한 location prior와 stable object memory를 잃는다.
- RGB-D / open-vocabulary perception은 missed target, false positive, localization error를 만든다.
- Path/search cost를 무시하면 reachable하지 않거나 비효율적인 후보를 방문할 수 있고, path cost만 앞세우면 detector-confidence보다 낮은 `SPL`이 나올 수 있다.
- 최근 E008-M198 scale gate에서는 source-pool candidate generation이 proxy recovery를 17 / 30으로 만들었지만, M70 no-source detector baseline 24 / 30보다 낮아 immediate Docker trajectory promotion이 거부됐다.

논문 주장 후보:

- Dynamic object search에서 stale semantic memory의 실패는 old memory 자체가 항상 틀려서가 아니라, current evidence confidence, stale-memory trust, source coverage, path feasibility, search budget이 서로 충돌하기 때문에 발생한다.

## Limitation of Existing Work

사실:

- 많은 semantic mapping 연구는 map construction, object retrieval, open-vocabulary grounding 성능에 집중한다.
- Open-vocabulary mapping은 flexible query를 제공하지만, 물체 이동 이후 old memory를 얼마나 신뢰해야 하는지와 re-observation/search decision을 함께 평가하지 않는 경우가 많다.
- 3D scene graph 기반 reasoning은 object/relation 구조를 제공하지만, task-conditioned memory update와 path/search-cost decision을 downstream benchmark로 평가하는 기준은 약하다.

에이전트 추론:

- 기존 한계는 "map이 틀린다"가 아니라 "map의 uncertainty, staleness, task relevance, path feasibility를 행동 의사결정으로 연결하는 기준이 약하다"로 잡는 것이 방어 가능하다.
- 이 문제는 stale semantic memory, current RGB-D observation, object identity, task context, spatial cost가 하나의 map-based decision으로 결합되므로 semantic mapping 문제다.

## Problem Definition

사실:

- Input: stale semantic memory from `3RScan` / `3DSSG`, current or rescan observation, `HM3D ObjectNav` episode state, object/category query, structured task context, candidate locations, RGB-D/open-vocabulary proposal rows, source-coverage rows, optional path/search cost.
- Output: candidate visit order, memory trust decision, stale-location suppression, re-observation/search-budget decision, predicted target location, failure boundary.
- Evaluation sources: `3RScan`, `3DSSG`, `3DSSG_subset`, `ConceptGraphs` staged RGB-D route, bounded `Open3DSG` adapter, `HM3D ObjectNav` + `Habitat`.

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` should improve dynamic object search behavior over static memory, fixed top-k, detector-only, external open-vocabulary map baselines, and context-agnostic memory trust.
- Real navigation `SR` / `SPL`은 simulator/navmesh/trajectory execution과 protected baseline comparison이 통과되기 전까지 final claim으로 쓰지 않는다. M198 기준 source-pool scale route는 protected baseline보다 proxy `SR`이 낮아 trajectory promotion이 막혀 있다.

## Core Hypothesis

논문 주장 후보:

- A semantic map should expose memory trust and re-observation/search decisions as first-class outputs, not only object locations.
- Task/staleness-aware memory trust can reduce stale old-location failures while preserving useful stable-location memory.
- Under RGB-D/open-vocabulary noise, a confidence-first memory decision layer can remain useful if current proposal reliability, stale-memory trust, source coverage, and search cost are explicitly separated.
- For navigation-facing evidence, path/search cost should not replace proposal reliability globally; it should act as a confidence-preserving veto, tie-break, or bounded local repair.
- Source-coverage / re-observation expansion should be treated as a candidate-generation interface, not as a positive navigation claim, until it beats the no-source detector baseline on full-denominator proxy and executed trajectory metrics.

에이전트 추론:

- 현재 가장 방어 가능한 핵심은 task/staleness-aware semantic memory decision이다.
- Broader Direction B claim은 real RGB-D/open-vocabulary robustness, heldout transfer, `ConceptGraphs` / bounded `Open3DSG` / future `HOV-SG` or `VLFM`-style baselines, and real navigation `SR` / `SPL` evidence가 더 붙어야 한다. M198은 source-pool scale route의 negative boundary로 해석해야 한다.

## Proposed Framework

에이전트 추론:

Working name은 `TASMM`: `Task- and Staleness-aware Semantic Memory Mapping`이다.

TASMM은 semantic map을 object store가 아니라 decision-producing memory interface로 정의한다.

1. `Semantic Memory Store`
   - 각 object/category에 대해 old location, current observation location, object/category label, source scan, timestamp/rescan relation, motion/staleness signal, relation/geometry cue를 저장한다.
   - Output은 단순 nearest object가 아니라 candidate object set과 memory state다.

2. `Proposal Reliability Layer`
   - Annotation-proxy candidate, real RGB-D/open-vocabulary proposal, `ConceptGraphs` candidate, bounded `Open3DSG` candidate를 공통 row schema로 변환한다.
   - Candidate row는 `confidence`, `source_role`, `candidate_position`, `path_ready`, `source_gap_flag`, `label_match`, `proposal_source`, `policy_allowed_inputs`를 가진다.
   - Current evidence confidence는 protected base signal로 유지한다. M159/M160 이후 M198까지의 결과 기준으로 `detector_confidence_reachable_subset_v0`를 protected baseline으로 둔다.

3. `Staleness And Memory Trust Gate`
   - Old memory candidate가 current observation보다 먼저 방문될 수 있는 조건을 task value, staleness/motion signal, current proposal availability, expected search cost로 제한한다.
   - Static stale memory, fixed top-k, context-agnostic memory trust를 naive baselines로 둔다.

4. `Re-observation / Source-Coverage Trigger`
   - Source-gap evidence가 있는 경우에만 re-observation or source expansion을 trigger한다.
   - Source-gap bonus를 모든 target-free row에 global score로 더하지 않는다. M159에서 source-gap bonus는 current denominator에서 inert로 판정됐고, M160은 source-gap을 trigger-only signal로 고정했다.
   - M191-M198 scale branch에서는 source-pool acquisition이 960 rendered frames와 552 detector candidates를 만들었지만, full-denominator proxy `SR`이 baseline보다 낮아 candidate-generation repair가 필요하다.

5. `Confidence-First Constrained Search Policy`
   - Current safe execution default는 `detector_confidence_reachable_subset_v0`다.
   - Base order는 `detector_confidence_reachable_subset_v0` 또는 equivalent current-evidence confidence ranking이다.
   - Confidence floor 아래 candidate는 confidence floor 위 candidate를 넘지 못한다.
   - Path/search cost는 global additive score가 아니라 다음 중 하나로만 사용한다.
   - `hard_feasibility_veto`: non-navigable or no-path candidate를 demote/remove.
   - `confidence_band_tie_break`: confidence 차이가 작은 후보들 안에서만 shorter path / lower candidate visit cost를 사용.
   - `bounded_local_repair`: protected order에서 크게 벗어나지 않는 rank displacement 안에서만 source-gap or path-feasible repair를 허용.
   - Budget은 weak scalar penalty가 아니라 hard visit cap, no-extra-visit gate, or precommitted utility/Pareto target으로 기록한다.
   - M198 기준 path-cost source-pool policy는 proxy `SPL` 일부를 높였지만 proxy `SR` 손실을 복구하지 못했으므로, real trajectory 실행으로 승격하지 않는다.

6. `Task Context Conditioner`
   - Human intent는 현재 natural-language understanding claim이 아니라 structured task context로 둔다.
   - Task context는 memory trust, re-observation priority, search budget, utility weighting을 바꾸는 conditioning signal이다.
   - E006-M08 기준 human intent main claim은 아직 지원되지 않으므로, main method에서는 secondary conditioning / ablation axis로 유지한다.

7. `Failure And Claim Boundary Layer`
   - 각 policy output에는 allowed input, blocked input, leakage audit, failure type, claim boundary를 붙인다.
   - Negative result는 threshold 조정으로 숨기지 않고, failure diagnosis -> method form revision -> ablation requirement로 연결한다.

## Experiment Plan (Metric, Baseline)

Metric:

- Dynamic search proxy: proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, stale old-location false positive, candidate visits, first-success rank.
- Proposal robustness: target detection, proposal precision, false-positive proposal rows, scan target recall, visible-proxy recall, label cleanup side effect.
- External mapping comparison: strict bbox top-k, relaxed bbox 1m top-k, center-localization metric, H001-only / baseline-only / both-fail row groups.
- Path/search bridge: path-ready ratio, source-ready subset metric, mean path cost, `PathAttemptSPLProxy`, source-limit sensitivity.
- Real navigation: `SR`, `SPL`, path length, candidate visits, stop rank, failure type, protected-baseline delta.
- Claim-boundary metrics: leakage audit pass/fail, heldout split transfer, label/scan/task-group breadth, component ablation pass/fail.
- Current E008 scale gate: M70 no-source detector proxy `SR` / `SPL` 0.8000 / 0.3506; M197 source-pool protected proxy `SR` / `SPL` 0.5667 / 0.3235; M198 trajectory promotion false.

Baseline:

- Naive memory/search: static stale memory, fixed top-k, detector-confidence ranking, context-agnostic memory trust, oracle upper bound.
- H001 ablations: no task context, no staleness/memory trust, no current-proposal reliability, no re-observation budget, no path/search-cost term, no confidence floor, no source-gap trigger, no budget guard.
- External semantic mapping / scene graph: `ConceptGraphs`, bounded `Open3DSG` predicted-vocabulary adapter, future `HOV-SG` if runtime/source contract is ready.
- Navigation/search baselines: detector-confidence reachable subset, path-cost-only rerank, confidence-first constrained repair, future `VLFM` / `HM3D-OVON` style executable navigation baseline if integrated on the same episodes.
- Human intent baseline: structured task context vs strongest context-agnostic policy; human intent is not main claim unless E006 redesign passes strong-baseline and transfer gates.
