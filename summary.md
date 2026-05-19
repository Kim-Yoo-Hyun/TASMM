# Research Summary

Updated: 2026-05-18

이 문서는 `research2/`의 연구 방향, 배경, 가설, 현재 진행 상태, 남은 쟁점, 실험 계획을 간단히 정리한 working research report다. 세부 진행 로그는 `TODO.md`, `hypothesis/`, `experiments/`에 둔다.

## Research Direction

사실:

- 연구 축은 semantic mapping 기반 human-friendly robot intelligence다.
- Active candidate는 `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`이다.
- Active hypothesis는 `H001_stale-object-memory`다.
- 최종 목표는 AI, ML, CV, Robotics top-tier journal/conference를 겨냥한 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이다.
- 현재 경로는 Direction A `Task-Conditioned Stale Semantic Memory`를 core method로 고정하고, real RGB-D/open-vocabulary proposal bridge, external mapping baselines, search/navigation metrics를 붙여 Direction B로 확장하는 방식이다.

에이전트 추론:

- 논문 중심은 "더 많은 semantic map 정보를 저장했다"가 아니라 "stale semantic memory를 task/search decision에서 언제 믿고, 언제 재관측하고, 어떤 후보를 먼저 방문할지 결정한다"에 두는 편이 강하다.
- human intent는 당장 natural-language understanding claim이 아니라 memory trust, re-observation, search budget, candidate visit order를 바꾸는 structured task context로 다루는 것이 방어 가능하다.

## Research Background

사실:

- 최근 semantic mapping, 3D scene graph, open-vocabulary mapping 연구는 RGB-D sequence, `3RScan`, `3DSSG`, VLM/LLM reasoning, open-vocabulary perception과 결합되고 있다.
- 기존 연구는 map construction, object grounding, retrieval, 3D scene representation을 강화해 왔다.
- Robotics 관점에서는 semantic map이 search, navigation, manipulation, instruction following 같은 downstream task의 행동 품질을 개선하는지가 중요하다.

에이전트 추론:

- dynamic object search/navigation에서는 stale memory, perception noise, path/search cost, task context가 동시에 작동한다.
- top-tier를 목표로 하려면 map quality만이 아니라 decision quality, external baseline, failure boundary를 함께 보여야 한다.

## Motivation

사실:

- 실내 물체는 이동하고, old semantic memory는 stale해질 수 있다.
- old memory를 그대로 믿으면 stale old-location failure가 발생한다.
- old memory를 완전히 버리면 반복적으로 유용한 location prior와 stable object memory를 잃는다.
- RGB-D / open-vocabulary perception은 missed target, false positive, localization error를 만든다.

논문 주장 후보:

- task context는 stale semantic memory를 얼마나 신뢰할지, 언제 재관측할지, 어떤 후보 위치를 먼저 방문할지를 조절하는 condition이 될 수 있다.
- stale memory와 noisy current observation을 함께 다루는 semantic mapping decision layer는 dynamic object search에서 `SR`, `ExpectedSearchCost`, `AttemptSPL`, stale old-location FP를 개선할 수 있다.

## Limitation of Existing Work

사실:

- 많은 semantic mapping 연구는 map construction 또는 open-vocabulary retrieval 성능에 집중한다.
- open-vocabulary mapping은 query flexibility를 제공하지만, 물체 이동 이후 old memory를 얼마나 신뢰해야 하는지까지 명확히 평가하지 않는 경우가 많다.
- 3D scene graph 기반 reasoning은 object/relation 구조를 제공하지만, task-conditioned memory update와 search-cost decision을 직접 평가하는 benchmark는 약하다.

에이전트 추론:

- 기존 한계는 "map이 틀린다"가 아니라 "map의 uncertainty, staleness, task relevance를 행동 의사결정으로 연결하는 기준이 약하다"로 잡는 것이 좋다.
- 이 문제는 semantic mapping 문제다. 과거 semantic memory, 현재 RGB-D observation, object identity, task context, spatial cost가 하나의 map-based decision으로 결합되기 때문이다.

## Problem Definition

사실:

- Input: stale semantic memory from `3RScan` / `3DSSG`, current or rescan observation, object/category query, structured task context, candidate locations, optional path/search cost, RGB-D/open-vocabulary proposal rows.
- Output: candidate visit order, memory trust decision, stale-location suppression, re-observation/search budget decision, predicted target location, failure boundary.
- Evaluation: proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, stale old-location FP, proposal recall, false-positive proposal rows, proposal precision, scan target recall, depth-consistent visible-proxy recall.

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` should improve dynamic object search behavior over static memory, fixed top-k, detector-only, and naive path-aware policies.
- real navigation `SR` / `SPL`은 simulator/navmesh/trajectory execution이 붙기 전까지 claim하지 않는다.

## Core Hypothesis

논문 주장 후보:

- Task context can modulate memory trust and re-observation decisions so that robots avoid stale old-location failures while preserving useful stable-location memory.
- A task-conditioned stale semantic memory layer can improve dynamic object search under perception noise by combining old memory, current proposals, and search-cost-aware candidate ranking.
- The same framework can scale toward open-vocabulary search/navigation if external mapping baselines and heldout real RGB-D evaluation support the claim.

에이전트 추론:

- 현재 가장 방어 가능한 핵심 claim은 "task/staleness-aware semantic memory decision"이다.
- broader Direction B claim은 `ConceptGraphs` / `Open3DSG` / `HOV-SG` 같은 external mapping baselines, heldout transfer, and navigation/search-cost evidence가 더 붙어야 한다.

## Proposed Framework

에이전트 추론:

Working name은 `TASMM`로 둔다: `Task- and Staleness-aware Semantic Memory Mapping`.

구성:

- Semantic Memory Store: object/category memory, old/current location, staleness/motion signal, source quality.
- Task Context Conditioner: structured task context를 memory trust, re-observation priority, search budget에 반영.
- Candidate Proposal Layer: annotation-proxy candidates와 real RGB-D/open-vocabulary proposals를 공통 schema로 정리.
- Search Decision Layer: static memory, fixed top-k, task-conditioned budget, reachable-first policy, oracle upper bound를 비교.
- Evaluation Layer: dynamic object search proxy, path/search-cost bridge, perception-noise robustness, external mapping baseline, failure analysis.

## Current Progress

사실:

- Hypothesis 단계는 `ready_with_constraints`로 main experiment 단계에 진입했다.
- E001은 `3RScan` / `3DSSG` 기반 semantic-pair dynamic object search proxy를 구성했다.
- E002는 path/search-cost bridge와 `occupancy_grid_astar_v0` proxy를 추가했다.
- E003은 controlled perception/proposal noise와 Dockerized RGB-D/open-vocabulary proposal route를 구축했다.
- E004는 `task_context_memory_trust_reobserve_v0`를 평가했고, memory-trust decision claim은 split stress에서 지지되지만 task-context-specific claim은 `limited_positive_not_label_broad`다.
- E005는 external baseline transition 단계다. `DualMap`은 실행/staging은 됐지만 object `*.pkl` output을 만들지 못해 performance baseline으로는 아직 부적합하다.
- `ConceptGraphs`는 source/interface audit, `3RScan` depth-aligned staging, repo/checkpoint acquisition, Docker image build, import smoke, one-scan runtime output verification, 4-scan metric conversion, heldout staging, and heldout batch runtime/metric conversion을 통과했다.
- E005-M35는 4개 staged scan의 `ConceptGraphs` object map을 query-level candidate/metric으로 변환했다. Primary `M60` 기준 strict bbox top5는 3/7, relaxed bbox 1m top3는 6/7이고, expanded `M73` 기준 strict bbox top5는 57/96이다.
- E005-M38은 `ConceptGraphs` heldout/scale contract를 고정했다. Target scale은 13 scans / 291 eligible query rows이고, heldout split은 9 scans / 195 query rows다.
- E005-M40은 9/9 heldout scans의 sequence staging을 검증했고, E005-M42는 9/9 heldout scans를 `ConceptGraphs` depth-aligned Scannet-style layout으로 materialize했다.
- E005-M45/M49는 `heldout_b01/b02`를 query-level metrics로 변환했다. `heldout_b01` strict bbox top5는 45/66 = 0.681818이고, `heldout_b02` strict bbox top5는 45/69 = 0.652174이다.
- `heldout_b03`는 아직 runtime/metric conversion이 남아 있으며, launch gate는 GPU free memory >= 24GB다.

논문 주장:

- 현재까지는 `DualMap` performance claim, final real RGB-D/open-vocabulary robustness claim, deployable search policy claim, real navigation `SR` / `SPL` claim을 하지 않는다.
- 현재 방어 가능한 claim은 controlled/proxy setting에서의 task/staleness-aware memory decision과 그 failure boundary다.

## Remaining Issues

사실:

- `ConceptGraphs`는 4-scan query-level conversion과 failure analysis, 13-scan heldout/scale contract, heldout sequence staging verification, staged-layout materialization, `heldout_b01/b02` runtime/metric conversion까지 통과했지만 아직 final baseline result는 아니다. `heldout_b03` runtime/metric conversion, full 9-scan aggregation, strict/relaxed metric separation, label-transfer analysis가 남아 있다.
- `DualMap`은 object-map output 부재 때문에 아직 external baseline result로 사용 불가하다.
- `OpenMask3D`는 checkpoint는 준비됐지만 local Docker/MinkowskiEngine build blocker가 있다.
- real RGB-D/open-vocabulary proposal route는 false-positive load와 heldout label/scan transfer 문제가 남아 있다.
- real navigation `SR` / `SPL`은 아직 simulator, navmesh, trajectory execution source가 없다.
- task-context-specific effect는 좁고 label-broad하지 않다.

에이전트 추론:

- 다음 방어 포인트는 "왜 detector 성능이 아니라 semantic memory decision contribution인가"를 명확히 분리하는 것이다.
- top-tier 가능성을 높이려면 external baseline, heldout split, real proposal robustness, search/navigation bridge를 체계적으로 보강해야 한다.

## Experiment Plan

사실:

- Immediate next unit: `E005-M47 ConceptGraphs heldout_b03 runtime launch` when GPU free memory is >= 24GB.
- Keep strict 0.5m, relaxed 1.0m, and center-localization metrics separate when scaling the external baseline table.
- After `ConceptGraphs` scale, audit `Open3DSG` as the next external map/scene-graph route if a second external baseline is needed.

논문 주장 후보:

- Main experiment는 `Task-Conditioned Stale Semantic Memory Update`가 dynamic object search에서 stale old-location failure와 search cost를 줄이는지 검증한다.
- Robustness experiment는 controlled perception noise와 real RGB-D/open-vocabulary proposals에서 memory decision layer가 유지되는지 확인한다.
- External baseline experiment는 `ConceptGraphs`, 가능하면 `Open3DSG` / `HOV-SG`, 그리고 feasible한 dynamic mapping baseline과 비교해 novelty boundary를 방어한다.
- Navigation/search-cost extension은 real navigation `SR` / `SPL`이 아니라 먼저 `ExpectedSearchCost`, `AttemptSPL`, candidate visit order로 bridge를 만든다.

사용자 판단 필요:

- 중간 투고는 focused semantic memory decision paper로 먼저 고정할지, broader mapping-navigation system paper까지 확장할지 evidence가 쌓인 뒤 결정한다.
