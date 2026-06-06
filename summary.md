# Research Summary

Updated: 2026-06-06

이 문서는 `research2/`의 연구 방향, 배경, 가설, 현재 상태, 남은 쟁점, 실험 계획을 간단히 정리한 working research report다. 세부 진행 로그는 `TODO.md`, `hypothesis/`, `experiments/`, `docs/reproducibility.md`에 둔다.

## Research Direction

사실:

- 연구 축은 semantic mapping 기반 human-friendly robot intelligence다.
- Active candidate는 `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`이다.
- Active hypothesis는 `H001_stale-object-memory`다.
- 최종 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이며, AI, ML, CV, Robotics top-tier journal/conference를 겨냥한다.

에이전트 추론:

- 중심 novelty는 "semantic map에 정보를 더 넣는 것"이 아니라 stale semantic memory를 언제 믿고, 언제 재관측하고, 어떤 후보를 먼저 방문할지 결정하는 데 있다.
- human intent는 현재 natural-language understanding claim이 아니라 memory trust, re-observation, search budget, candidate visit order를 바꾸는 structured task context로 다루는 것이 방어 가능하다.

## Research Background

사실:

- 최근 semantic mapping, 3D scene graph, open-vocabulary mapping 연구는 RGB-D sequence, VLM/LLM reasoning, embodied search/navigation과 결합되고 있다.
- Robotics 관점에서는 semantic map이 search, navigation, manipulation, instruction following 같은 downstream task의 행동 품질을 개선하는지가 중요하다.

에이전트 추론:

- dynamic object search/navigation에서는 stale memory, perception noise, path/search cost, task context가 동시에 작동한다.
- top-tier를 목표로 하려면 map quality만이 아니라 decision quality, external baseline, heldout split, failure boundary를 함께 보여야 한다.

## Motivation

사실:

- 실내 물체는 이동하고, old semantic memory는 stale해질 수 있다.
- old memory를 그대로 믿으면 stale old-location failure가 발생한다.
- old memory를 완전히 버리면 반복적으로 유용한 location prior와 stable object memory를 잃는다.
- RGB-D / open-vocabulary perception은 missed target, false positive, localization error를 만든다.

논문 주장 후보:

- task context는 stale semantic memory를 얼마나 신뢰할지, 언제 재관측할지, 어떤 후보 위치를 먼저 방문할지를 조절하는 condition이 될 수 있다.
- stale memory와 noisy current observation을 함께 다루는 semantic mapping decision layer는 dynamic object search에서 `ExpectedSearchCost`, `AttemptSPL`, stale old-location false positive를 줄일 수 있다.

## Limitation Of Existing Work

사실:

- 많은 semantic mapping 연구는 map construction, open-vocabulary retrieval, object grounding 성능에 집중한다.
- open-vocabulary mapping은 query flexibility를 제공하지만, 물체 이동 이후 old memory를 얼마나 신뢰해야 하는지까지 직접 평가하지 않는 경우가 많다.
- 3D scene graph 기반 reasoning은 object/relation 구조를 제공하지만, task-conditioned memory update와 search-cost decision을 평가하는 benchmark는 약하다.

에이전트 추론:

- 기존 한계는 "map이 틀린다"가 아니라 "map의 uncertainty, staleness, task relevance를 행동 의사결정으로 연결하는 기준이 약하다"로 잡는 것이 좋다.
- 이 문제는 과거 semantic memory, 현재 RGB-D observation, object identity, task context, spatial cost가 하나의 map-based decision으로 결합되므로 semantic mapping 문제다.

## Problem Definition

사실:

- Input: stale semantic memory from `3RScan` / `3DSSG`, current or rescan observation, object/category query, structured task context, candidate locations, optional path/search cost, RGB-D/open-vocabulary proposal rows.
- Output: candidate visit order, memory trust decision, stale-location suppression, re-observation/search budget decision, predicted target location, failure boundary.
- Evaluation: proxy `SR`, `ExpectedSearchCost`, `AttemptSPL`, stale old-location false positive, proposal recall, false-positive proposal rows, proposal precision, scan target recall, depth-consistent visible-proxy recall.

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` should improve dynamic object search behavior over static memory, fixed top-k, detector-only, external open-vocabulary map baselines, and context-agnostic memory trust.
- real navigation `SR` / `SPL`은 simulator/navmesh/trajectory execution이 붙기 전까지 claim하지 않는다.

## Core Hypothesis

논문 주장 후보:

- Task context can modulate memory trust and re-observation decisions so that robots avoid stale old-location failures while preserving useful stable-location memory.
- A task-conditioned stale semantic memory layer can improve dynamic object search under perception noise by combining old memory, current proposals, and search-cost-aware candidate ranking.
- The same framework can scale toward open-vocabulary search/navigation if external mapping baselines and heldout real RGB-D evaluation support the claim.

에이전트 추론:

- 현재 가장 방어 가능한 핵심 claim은 task/staleness-aware semantic memory decision이다.
- broader Direction B claim은 `ConceptGraphs`, `Open3DSG`, `HOV-SG` 같은 external mapping baselines, heldout transfer, navigation/search-cost evidence가 더 붙어야 한다.

## Proposed Framework

에이전트 추론:

Working name은 `TASMM`로 둔다: `Task- and Staleness-aware Semantic Memory Mapping`.

- Semantic Memory Store: object/category memory, old/current location, staleness/motion signal, source quality.
- Task Context Conditioner: structured task context를 memory trust, re-observation priority, search budget에 반영.
- Candidate Proposal Layer: annotation-proxy candidates와 real RGB-D/open-vocabulary proposals를 공통 schema로 정리.
- Search Decision Layer: static memory, detector-confidence ranking, fixed top-k, task-conditioned budget, reachable-first policy, oracle upper bound를 비교.
- Evaluation Layer: dynamic object search proxy, path/search-cost bridge, perception-noise robustness, external mapping baseline, failure analysis.

## Current Progress

사실:

- Hypothesis 단계는 `ready_with_constraints`로 main experiment 단계에 진입했다.
- E001/E002는 `3RScan` / `3DSSG` 기반 dynamic object search proxy와 path/search-cost bridge를 구성했다.
- E003는 controlled perception/proposal noise와 Dockerized RGB-D/open-vocabulary proposal route를 구축했다.
- E004는 `task_context_memory_trust_reobserve_v0`를 평가했다. Memory-trust decision claim은 split stress에서 지지되지만 task-context-specific claim은 `limited_positive_not_label_broad`다.
- E005는 external baseline transition 단계다. `DualMap`은 object `*.pkl` output이 없어 performance baseline으로는 부적합하고, `ConceptGraphs`와 bounded `Open3DSG` predicted-vocabulary adapter가 현재 external baseline route다.
- E006-M01/M02/M03/M04/M05/M06/M07/M08은 human intent를 main claim으로 승격하기 위한 contract, schema materialization, baseline policy row materialization, utility metric materialization, and claim decision을 고정했다. E006-M08 결론은 current evidence에서 human intent main claim을 지지하지 않고, structured task context를 secondary conditioning / ablation axis로 유지하는 것이다.
- `ConceptGraphs` full heldout strict bbox top5는 114/195이고, H001 replay는 172/195다. `Open3DSG` bounded predicted-vocabulary adapter strict bbox top5는 144/195다.
- Full real-proposal aggregate는 target detected 144/195, H001 157/195, context-agnostic 156/195, `ConceptGraphs` same-batch 114/195, detector top5 51/195다.
- E005-M89는 `569d8f0f` zero-written cluster를 target-independent cleanup trace로 검증했다. 483 rows가 모두 drop됐고, dominant pattern은 `a chair` / `chair`가 canonical `stool`로 정규화된 뒤 active scan label `chair`와 맞지 않아 `drop_not_scan_prompt_label`로 제거되는 것이다.
- E005-M90은 leakage-safe repair route로 `active_scan_exact_label_precedence_v0`를 선택했다. Active-exact replay는 479/483 rows를 keep하고, blocked-field hits는 0이며, worst-case selected proposal upper bound는 24다.
- E005-M91은 active-label precedence runner patch와 one-scan cleanup smoke를 완료했다. M89 pre-cap/final rows 0/0은 M91에서 479/24로 회복됐고, matching smoke는 matched target rows 5/5, proposal precision 0.208333을 보였다.
- E005-M92는 M91 결과를 query/rerun decision으로 연결했다. Affected 15 query rows에서 target detection은 0->15로 회복 가능하지만, H001 success delta는 0이고 `chair`/`stool` side-effect risk가 있어 bounded `heldout_b02` rerun을 다음 단계로 선택했다.
- E005-M93은 bounded `heldout_b02` rerun을 완료했다. Target detected는 42/69 -> 57/69, detector top5는 15/69 -> 18/69로 개선됐지만, detector task-budget은 7/69, H001은 54/69로 유지됐고 side-effect loss는 0이었다.
- E005-M94는 M93을 batch-level repair diagnostic으로 고정했다. b02를 M93으로 교체한 diagnostic aggregate projection은 target detected 159/195, detector top5 60/195, detector task-budget 26/195, H001 157/195이며, 선택 route는 `stop_and_record_m93_as_batch_level_repair_diagnostic`이다.
- E005-M95는 paper-facing real-proposal diagnostic table과 final E005 boundary를 갱신했다. Main diagnostic rows 7개, repair diagnostic rows 4개, allowed diagnostic claims 2개, blocked claims 4개로 정리했다.
- E005-M96은 다음 확장 route로 `external_proposal_mapping_baseline_first`를 선택했다. Navigation/search bridge는 Direction B에 필요하지만, 현재는 proposal/mapping robustness blocker를 먼저 줄여야 한다.
- E005-M97은 first smoke route로 `conceptgraphs_derived_map_candidate_route`를 선택했다. `Open3DSG` bounded vocab adapter는 supporting row로 유지하고, `OpenMask3D`는 environment blocker, `HOV-SG`는 source/runtime audit 부재로 보류했다.
- E005-M98은 `ConceptGraphs`, real detector, H001을 같은 195-row denominator에서 비교했다. H001은 `ConceptGraphs` strict top5와 real detector top5가 모두 실패한 54 rows를 회복하지만, `ConceptGraphs`가 성공하고 H001이 실패한 24 rows도 있다.
- E005-M99는 M98 row groups를 target-level로 재검토했다. 195 rows / 65 targets 중 H001 failure는 38 rows / 13 targets이고, `ConceptGraphs` map-assisted repair candidate는 24 rows / 8 targets다. H001-or-`ConceptGraphs` upper bound는 181/195이며, selected next unit은 E005-M100 `ConceptGraphs`-assisted H001 fallback policy smoke다.
- E005-M100은 `ConceptGraphs`-assisted H001 fallback policy를 smoke-test했다. Selected policy `h001_then_conceptgraphs_top5_on_observed_miss_v0`는 H001 success 157/195를 181/195로 높이고, `AttemptSPL` proxy도 0.773932에서 0.798675로 개선한다. Mean `ExpectedSearchCost`는 1.758974에서 2.435897로 증가한다.
- E005-M101은 M100 selected policy를 paper-facing query-level table row로 ready-with-boundary 처리하고, E007-M01 navigation/path-cost bridge contract를 선택했다.
- E007-M01은 M100 195 rows와 E002 `occupancy_grid_astar_v0`의 row overlap 195/195를 확인했다. E002 target-grid reachable overlap은 186/195이고, `ConceptGraphs` candidate eval query overlap은 195/195다.
- E007-M02는 1,170 query-policy rows와 3,814 route rows를 materialize했다. E007-M03은 external candidate coordinates를 E002 grid로 project하고 route-level path-cost fields를 계산했다. E007-M04는 path-cost policy metrics를 full denominator와 source-ready subset으로 분리 평가했다. E007-M05는 이 결과를 paper-facing occupancy-grid path-cost bridge table로 고정했다. E007-M06은 source-limit/direct-only/path-start sensitivity를 검증했다. E007-M07은 final bridge table, claim-evidence ledger, reviewer defense package, navigation-expansion decision을 묶었다. Method `h001_then_conceptgraphs_top5_on_observed_miss_v0`는 full success 181/195, source-ready path success 163/174, mean path cost 2.996131m, mean `PathAttemptSPLProxy` 0.824554다. E007-M07 package는 table rows 6, allowed claims 3, blocked claims 3이다.
- E008-M01은 real navigation source/episode preflight를 완료했다. 선택 source는 local read-only `HM3D ObjectNav` + `Habitat`이며, `/home/yoohyun/research3/local_dataset/data` 아래에 `HM3D` `.glb` 1,095개, `.navmesh` 910개, `ObjectNav val_mini` parsed episodes 30개가 있고, Docker image `research3/habitat-h001:20260508-calib-artifacts`에서 `habitat_sim` import가 통과했다.
- E008-M02는 `HM3D ObjectNav` episode/source adapter smoke를 완료했다. 6개 `ObjectNav val_mini` episode row, 2개 `HM3D` scene, 6/6 scene/navmesh ready row를 만들었고, Docker `Habitat`에서 2개 scene 모두 pathfinder load가 통과했다.
- E008-M03은 `H001` candidate-to-navigation adapter contract를 완료했다. 6/6 `ObjectNav` eval goal/viewpoint rows와 7개 policy adapter rows를 만들었고, H001 실행에 필요한 `HM3D` stale-memory/current-observation/external-map candidate-source rows는 0으로 확인했다.
- E008-M04는 `ObjectNav` goal/viewpoint oracle path smoke를 완료했다. 6/6 eval-only viewpoint shortest paths와 4/6 goal-snapped paths를 계산했고, mean oracle viewpoint path length는 5.738806m다.
- E008-M05는 `HM3D` candidate-source staging plan을 완료했다. `HM3D` semantic files는 2/2 scenes에서 준비됐고, `bed` / `chair` / `tv_monitor` category label support는 6/6 episode rows에서 확인됐다.
- E008-M06은 annotation-derived `HM3D` semantic candidate-source smoke를 완료했다. Semantic label support는 6/6이지만 Habitat semantic nonzero-AABB scenes는 0/2, GLB semantic geometry mapping scenes도 0/2라 candidate rows는 0이다.
- E008-M07은 rendered RGB-D detector candidate-source plan을 완료했다. 6 episode rows에서 24 start-pose yaw-sweep render rows, 6 detector manifest rows, 5 detector labels(`bed`, `chair`, `monitor`, `television`, `tv`)를 고정했고, `Habitat` image와 `real-smoke` detector image readiness를 확인했다.
- E008-M08은 Docker `Habitat` render smoke로 24/24 rendered RGB-D/pose rows, 6/6 detector-compatible sequence dirs, 6 detector manifest rows, detector input files ready를 검증했다.
- E008-M09-M103는 `HM3D ObjectNav` rendered RGB-D detector candidate route와 non-oracle observation expansion path를 trajectory execution smoke, H001 source materialization, dynamic-stale overlay trajectory execution, budget-matched repair, source-diverse redesign, full-val-mini detector route, source-gap repair chain, coverage-expansion repair closure, alternative proposal-source feasibility contract까지 검증했다.
- E008-M78은 direct trajectory promotion과 rerank-only repair를 reject했다. E008-M79는 source-gap expansion cases 2, budget-5 loss sentinel 1, localization controls 4를 고정했고, E008-M80은 detector-confidence budget-5 core 150 rows와 append policy 240 rows를 materialize해 30/30 top-5 preservation invariant와 leakage audit를 통과했다. E008-M81은 detector budget-5 core와 append policy가 같은 13/30 `GoalEvalProxySR`을 유지하고, policy-budget append scope에서는 15/30으로 2 rows gain / 0 loss를 보였지만 source-gap append gain은 0이다. E008-M82는 direct trajectory promotion을 막고 E008-M83 source/observation expansion contract를 선택했다. E008-M85는 2 source-gap cases에 대해 192/192 rendered frames, 2/2 scans, 192/192 snap-ready rows, detector input files ready를 검증했다.

논문 주장:

- 현재 방어 가능한 claim은 controlled/proxy setting에서의 task/staleness-aware memory decision과 `ConceptGraphs` / bounded `Open3DSG` 대비 proxy-search comparison이다.
- `DualMap` performance claim, human intent main claim, final real RGB-D/open-vocabulary robustness claim, deployable search policy claim, real navigation `SR` / `SPL` claim은 아직 하지 않는다.

## Remaining Issues

사실:

- H001은 `ConceptGraphs`와 static memory 대비 개선을 보였지만, context-agnostic memory trust 대비 gain은 1 row로 좁다.
- human intent main claim은 E006-M08 기준으로 current paper path에서는 사용하지 않는다. 후속 판단은 explicit policy redesign 또는 E008 evidence 이후 재평가할 때만 진행한다.
- real RGB-D/open-vocabulary proposal route는 full denominator까지 확장됐지만 final robustness claim은 아직 불가하다. Detector target detection, false-positive load, cleanup/label scope, real navigation evidence가 남아 있다.
- `OpenMask3D`는 checkpoint는 준비됐지만 local Docker/`MinkowskiEngine` build blocker가 있다.
- real navigation `SR` / `SPL`은 simulator/navmesh trajectory smoke와 diagnostic table까지 생겼지만 final claim은 아직 불가하다. E008-M136은 E008-M135 trajectory-aware repair 결과를 해석해 current repair scale-up을 거절하고, confidence-preserving trajectory repair를 다음 단계로 선택했다.

에이전트 추론:

- 다음 방어 포인트는 detector/prompt repair와 semantic memory decision contribution을 분리하는 것이다.
- M93/M94/M95 결과상 active-label precedence repair는 b02 target-detection recovery에 타당하다. 하지만 H001 success와 detector task-budget을 개선하지 못했으므로 full heldout robustness가 아니라 failure-specific repair와 diagnostic boundary evidence로만 써야 한다.
- E008-M136 기준으로도 바로 final navigation claim을 하면 안 된다. 현재는 one-case repair trajectory diagnostic 단계이며, confidence-preserving repair evidence, heldout transfer, external navigation/search baseline이 아직 필요하다.

## Experiment Plan

사실:

- Immediate next unit: E008-M137 target-free confidence-preserving trajectory-aware repair contract.
- Strict 0.5m, relaxed 1.0m, center-localization metrics는 external baseline table에서 분리해 유지한다.
- Docker는 논문 본문용 실제 구현 실험의 기본 실행 환경이다.

논문 주장 후보:

- Main experiment는 `Task-Conditioned Stale Semantic Memory Update`가 dynamic object search에서 stale old-location failure와 search cost를 줄이는지 검증한다.
- Robustness experiment는 controlled perception noise와 real RGB-D/open-vocabulary proposals에서 memory decision layer가 유지되는지 확인한다.
- External baseline experiment는 `ConceptGraphs`, bounded `Open3DSG`, 가능하면 `HOV-SG` 또는 추가 proposal baseline과 비교해 novelty boundary를 방어한다.
- Navigation/search-cost extension은 E007에서 `ExpectedSearchCost`, `AttemptSPL`, candidate visit order bridge를 만들었고, E008-M136까지 target-free trajectory execution, result interpretation, repair contract, repair row materialization, repair trajectory smoke, scale decision을 완료했다. 현재 결과는 실행 가능성 및 failure-diagnosis evidence이지만 positive navigation-improvement evidence는 아니다. Human-intent extension은 E006-M08까지 current evidence에서 main claim false로 결정됐다.

사용자 판단 필요:

- 중간 투고는 focused semantic memory decision paper로 먼저 고정할지, broader mapping-navigation system paper까지 확장할지 evidence가 더 쌓인 뒤 결정한다.
