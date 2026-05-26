# Research Summary

Updated: 2026-05-26

이 문서는 `research2/`의 연구 방향, 배경, 가설, 현재 진행 상태, 남은 쟁점, 실험 계획을 간단히 정리한 working research report다. 세부 진행 로그는 `TODO.md`, `hypothesis/`, `experiments/`에 둔다.

## Research Direction

사실:

- 연구 축은 semantic mapping 기반 human-friendly robot intelligence다.
- Active candidate는 `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`이다.
- Active hypothesis는 `H001_stale-object-memory`다.
- 최종 목표는 AI, ML, CV, Robotics top-tier journal/conference를 겨냥한 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`이다.
- 현재 경로는 Direction A `Task-Conditioned Stale Semantic Memory`를 core method로 고정하고, real RGB-D/open-vocabulary proposal bridge, external mapping baselines, search/navigation metrics를 붙여 Direction B로 확장하는 방식이다.

에이전트 추론:

- 논문 중심은 "semantic map에 더 많은 정보를 저장했다"가 아니라 "stale semantic memory를 언제 믿고, 언제 재관측하고, 어떤 후보를 먼저 방문할지 결정한다"에 두는 편이 강하다.
- human intent는 현재 natural-language understanding claim이 아니라 memory trust, re-observation, search budget, candidate visit order를 바꾸는 structured task context로 다루는 것이 방어 가능하다.

## Research Background

사실:

- 최근 semantic mapping, 3D scene graph, open-vocabulary mapping 연구는 RGB-D sequence, `3RScan`, `3DSSG`, VLM/LLM reasoning, open-vocabulary perception과 결합되고 있다.
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
- stale memory와 noisy current observation을 함께 다루는 semantic mapping decision layer는 dynamic object search에서 `ExpectedSearchCost`, `AttemptSPL`, stale old-location FP를 개선할 수 있다.

## Limitation Of Existing Work

사실:

- 많은 semantic mapping 연구는 map construction, open-vocabulary retrieval, object grounding 성능에 집중한다.
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

- `Task-Conditioned Stale Semantic Memory Update` should improve dynamic object search behavior over static memory, fixed top-k, detector-only, external open-vocabulary map baselines, and context-agnostic memory trust.
- real navigation `SR` / `SPL`은 simulator/navmesh/trajectory execution이 붙기 전까지 claim하지 않는다.

## Core Hypothesis

논문 주장 후보:

- Task context can modulate memory trust and re-observation decisions so that robots avoid stale old-location failures while preserving useful stable-location memory.
- A task-conditioned stale semantic memory layer can improve dynamic object search under perception noise by combining old memory, current proposals, and search-cost-aware candidate ranking.
- The same framework can scale toward open-vocabulary search/navigation if external mapping baselines and heldout real RGB-D evaluation support the claim.

에이전트 추론:

- 현재 가장 방어 가능한 핵심 claim은 "task/staleness-aware semantic memory decision"이다.
- broader Direction B claim은 `ConceptGraphs`, `Open3DSG`, `HOV-SG` 같은 external mapping baselines, heldout transfer, navigation/search-cost evidence가 더 붙어야 한다.

## Proposed Framework

에이전트 추론:

Working name은 `TASMM`로 둔다: `Task- and Staleness-aware Semantic Memory Mapping`.

구성:

- Semantic Memory Store: object/category memory, old/current location, staleness/motion signal, source quality.
- Task Context Conditioner: structured task context를 memory trust, re-observation priority, search budget에 반영.
- Candidate Proposal Layer: annotation-proxy candidates와 real RGB-D/open-vocabulary proposals를 공통 schema로 정리.
- Search Decision Layer: static memory, detector-confidence ranking, fixed top-k, task-conditioned budget, reachable-first policy, oracle upper bound를 비교.
- Evaluation Layer: dynamic object search proxy, path/search-cost bridge, perception-noise robustness, external mapping baseline, failure analysis.

## Current Progress

사실:

- Hypothesis 단계는 `ready_with_constraints`로 main experiment 단계에 진입했다.
- E001은 `3RScan` / `3DSSG` 기반 semantic-pair dynamic object search proxy를 구성했다.
- E002는 path/search-cost bridge와 `occupancy_grid_astar_v0` proxy를 추가했다.
- E003은 controlled perception/proposal noise와 Dockerized RGB-D/open-vocabulary proposal route를 구축했다. E003-M75는 96 query rows에서 target detected 87/96, bounded repair success 33/96을 보였지만 final real RGB-D/open-vocabulary robustness claim은 false다.
- E004는 `task_context_memory_trust_reobserve_v0`를 평가했다. Memory-trust decision claim은 split stress에서 지지되지만 task-context-specific claim은 `limited_positive_not_label_broad`다.
- E005는 external baseline transition 단계다. `DualMap`은 실행/staging은 됐지만 object `*.pkl` output을 만들지 못해 performance baseline으로는 부적합하다.
- `ConceptGraphs`는 full 9-scan heldout query-level conversion을 통과했다. Strict bbox top5는 114/195 = 0.584615, relaxed bbox 1m top3는 144/195 = 0.738462이다.
- H001 replay on the same `M38` query contract gives H001 172/195 = 0.882051, static memory 141/195 = 0.723077, and context-agnostic memory trust 171/195 = 0.876923.
- E005-M56은 two-table robustness denominator를 고정했다. Table A는 proxy-search external map denominator 195 rows, Table B는 real RGB-D proposal bridge denominator 96 rows다.
- `/home/yoohyun/research/local_dataset/Open3DSG_staged`는 read-only source로만 사용하고, 파생 결과는 `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`에 저장한다.
- E005-M57-M71은 `Open3DSG` read-only source를 이용한 schema/export/query-conversion/interpretation/route decision, leakage-safe predicted-vocabulary policy evaluation, paper-table integration boundary, external-baseline failure-boundary rows, real RGB-D/open-vocabulary robustness route decision, full-denominator real proposal bridge plan, `heldout_b01` detector batch launch/completion/query-level conversion을 완료했다.
- E005-M72/M73/M74는 b01/b02/b03 detector launch, completion verification, query-level conversion을 완료했다.
- E005-M75는 full real-proposal aggregate route decision을 완료했다. Full aggregate는 query rows 195, target detected 144/195, H001 157/195, context-agnostic 156/195, `ConceptGraphs` same-batch 114/195, detector task-budget 24/195, detector top5 51/195이다.
- E005-M76은 M75를 diagnostic real-proposal search table로는 포함 가능하다고 판단했지만, detector precision 0.051892, target detection 0.738462, mean false positives before target 8.104167 때문에 final real RGB-D/open-vocabulary robustness는 blocked로 고정했다.
- E005-M77은 기존 M69 pre-cap candidate pool 23,742 rows를 분석했다. Pre-cap detected targets는 54/65, current selected detected targets는 48/65이며, best offline policy `offline_confidence_log_depth_radius0p5_cap24`는 top5 success를 current 51/195에서 60/195로 올릴 가능성을 보였다.
- E005-M78은 fixed policy `offline_confidence_log_depth_radius0p5_cap24_fixed_replay_v0`를 구현/검증했다. M77 best policy를 top5/rank mismatch 0으로 재현했고, selected proposals 926, matched proposal rows 98, proposal precision 0.105832, target detected 147/195, top5 success 60/195를 얻었다.
- E005-M79는 M78 fixed policy가 runner source edit 없이 `confidence_log_depth` score mode로 표현 가능함을 확인했다. First rerun batch는 expected top5 gain이 가장 큰 `heldout_b02`로 정했다.
- E005-M80은 `heldout_b02` confidence-log-depth targeted detector rerun을 background로 launch했다. tmux session은 `e005_m80_confidence_log_depth_heldout_b02`, log는 `logs/20260526_020840_e005_m80_confidence_log_depth_heldout_b02.log`, output은 `experiments/E005_external_baseline_transition/artifacts/E005-M80_confidence_log_depth_detector_run_v0/heldout_b02/`다.
- E005-M81은 M80 completion을 검증했다. Expected files 14/14, prediction rows 264, matched targets 14/17, proposal precision 0.053030, scan target recall 0.823529다.
- E005-M82는 M80/M81 output을 query-level metric으로 변환했다. `heldout_b02` detector top5는 기존 9/69에서 15/69로, task-budget은 5/69에서 7/69로 개선됐지만, target detected는 42/69로 유지됐다.
- E005-M61은 9개 query scan, 195 query rows, 51 target subgraphs에 대해 denominator-aligned `Open3DSG` object-candidate rows 7,600개를 생성했다.
- Corrected E005-M60은 query candidate/eval rows 759개와 policy rows 585개를 생성했다. 현재 `Open3DSG` strict bbox top5는 81/195 = 0.415385, relaxed bbox 1m top3는 90/195 = 0.461538이다.
- E005-M64는 predicted-vocabulary adapter를 leakage-safe policy로 구현/검증했다. Strict bbox top5는 144/195 = 0.738462, relaxed bbox 1m top3는 147/195 = 0.753846이다.
- E005-M65는 `Open3DSG` predicted-vocabulary adapter를 main table의 bounded external scene-graph baseline row로 포함하고, primary-label adapter는 diagnostic/supplement row로 분리했다.
- E005-M66은 external-baseline failure boundary를 row-level로 정리했다. H001 vs `ConceptGraphs`는 both_success 112, H001-only 60, `ConceptGraphs`-only 2, both_fail 21이고, H001 vs `Open3DSG` vocab은 both_success 133, H001-only 39, `Open3DSG` vocab-only 11, both_fail 12다.
- E005-M67은 real RGB-D/open-vocabulary robustness route로 `scale_real_proposal_bridge_to_m38_heldout_denominator`를 선택했다. M38/M45 heldout denominator는 195 query rows / 9 scans / 65 target rows이고, 현재 E003-M75 real-proposal bridge는 96 rows라 denominator mismatch가 99 rows다.
- E005-M68은 M38/M45 195-row denominator 전체를 real-proposal bridge input으로 materialize했다. 9/9 scans ready, 65 object targets, 22 prompt labels, 214 sampled frames, 3 heldout batches이며 E003-M75와 row-level overlap은 0이다.
- E005-M70은 `heldout_b01` detector completion을 검증했다. Expected files 12/12, prediction rows 261, pre-cap candidate rows 5,310, matched targets 18/22, scan target recall 0.8182, proposal precision 0.0690, false-positive rate 0.9310이다.
- E005-M71은 `heldout_b01` 66 query rows를 real proposal query-level metric으로 변환했다. Target detected 54/66, real detector task-budget 8/66, real detector top5 21/66, static memory 45/66, context-agnostic memory trust 48/66, H001 real memory-trust 48/66, `ConceptGraphs` same-batch 45/66이다.
- E005-M73/M74는 `heldout_b02`를 검증/변환했다. Detector expected files 12/12, prediction rows 264, pre-cap candidate rows 6,799, matched targets 14/17, scan target recall 0.8235, proposal precision 0.0530, false-positive rate 0.9470이고, query-level target detected 42/69, H001 54/69, context-agnostic 54/69, `ConceptGraphs` same-batch 45/69이다.
- E005에서 human intent는 structured `task_context_id`로 H001 memory trust / re-observation policy에 반영됐다. 그러나 H001과 context-agnostic memory trust의 차이는 1 success row라 human intent main claim은 false다.
- `docs/reproducibility.md`에는 데이터 위치, checkpoint/Docker 보존 후보, Drive backup/restore checklist, 재현 명령, artifact/evaluation 요약을 정리했다.
- `experiments/report.md`와 `docs/paper.md`에는 `ConceptGraphs` / `Open3DSG` 기준 reviewer defense와 claim-evidence ledger를 반영했다.

논문 주장:

- 현재 방어 가능한 claim은 controlled/proxy setting에서의 task/staleness-aware memory decision과 `ConceptGraphs` 대비 proxy-search comparison이다.
- `DualMap` performance claim, human intent main claim, final real RGB-D/open-vocabulary robustness claim, deployable search policy claim, real navigation `SR` / `SPL` claim은 아직 하지 않는다. `Open3DSG`는 bounded predicted-vocabulary adapter baseline으로만 제한해 claim한다.

## Remaining Issues

사실:

- H001은 `ConceptGraphs`와 static memory 대비 개선을 보였지만, context-agnostic memory trust 대비 gain은 1 row로 좁다. 따라서 human task context는 현재 main contribution이 아니라 secondary ablation이다.
- `Open3DSG`는 primary-label adapter 성능은 `ConceptGraphs`보다 낮지만, predicted-vocabulary adapter에서는 strict bbox top5 144/195로 `ConceptGraphs` strict 114/195를 넘는다.
- `OpenMask3D`는 checkpoint는 준비됐지만 local Docker/`MinkowskiEngine` build blocker가 있다.
- real RGB-D/open-vocabulary proposal route는 full M38/M45 denominator까지 확장됐다. 그러나 final robustness claim은 아직 불가하다. 이유는 detector target detection이 144/195로 완전하지 않고, false positives before target 평균이 8.104167이며, real navigation / deployable policy evidence가 아직 없기 때문이다.
- real navigation `SR` / `SPL`은 simulator, navmesh, trajectory execution source가 아직 없다.

에이전트 추론:

- 다음 방어 포인트는 "detector repair"와 "semantic memory decision contribution"을 분리하는 것이다.
- Top-tier 가능성을 높이려면 M83에서 `heldout_b02` ranking gain이 b01/b03 rerun을 정당화하는지 판단하고, 이후에도 남는 target detection 한계는 prompt/label repair 또는 external 3D proposal baseline으로 넘겨야 한다.

## Experiment Plan

사실:

- Immediate next unit: E005-M83에서 `heldout_b02` rerun 결과를 해석하고 b01/b03 rerun 여부를 결정한다.
- Strict 0.5m, relaxed 1.0m, center-localization metrics는 external baseline table에서 분리해 유지한다.
- Docker는 논문 본문용 실제 구현 실험의 기본 실행 환경이다.

논문 주장 후보:

- Main experiment는 `Task-Conditioned Stale Semantic Memory Update`가 dynamic object search에서 stale old-location failure와 search cost를 줄이는지 검증한다.
- Robustness experiment는 controlled perception noise와 real RGB-D/open-vocabulary proposals에서 memory decision layer가 유지되는지 확인한다.
- External baseline experiment는 `ConceptGraphs`, 가능하면 `Open3DSG` / `HOV-SG`, 그리고 feasible한 dynamic mapping baseline과 비교해 novelty boundary를 방어한다.
- Navigation/search-cost extension은 real navigation `SR` / `SPL`이 아니라 먼저 `ExpectedSearchCost`, `AttemptSPL`, candidate visit order로 bridge를 만든다.

사용자 판단 필요:

- 중간 투고는 focused semantic memory decision paper로 먼저 고정할지, broader mapping-navigation system paper까지 확장할지 evidence가 더 쌓인 뒤 결정한다.
