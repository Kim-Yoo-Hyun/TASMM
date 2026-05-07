# Research Direction

## Working Title

Semantic Mapping for Human-Friendly Robot Intelligence

## Long-Term Aim

사람 친화적인 로봇 지능을 위해 semantic map을 단순한 3D label 저장소가 아니라, 사람의 의도, 지식, 공간 관계, affordance, 시간 변화, 불확실성을 함께 담는 task-oriented memory로 만든다.

## Current Scope

사실:

- 석사 연구 제약은 6개월~1년으로 둔다.
- 현재 연구 계획의 실질 제약은 6개월~1년 규모의 top-tier submission target이다.
- 중간 과정에서 독립적인 contribution이 성립하면 workshop, short paper, 또는 관련 venue에 먼저 투고할 수 있다.
- 현재 leading direction은 H001 / E001에서 출발한 `Task-Conditioned Semantic Memory Trust for Dynamic Object Search and Navigation`이다.

논문 주장:

- 목표 claim은 stale semantic memory update가 dynamic object search/navigation에서 `ExpectedSearchCost`, `SR`, `SPL`을 개선하고, RGB-D / open-vocabulary perception noise 아래에서도 유지되며, human task context가 memory trust와 re-observation decision을 바꾼다는 것이다.

에이전트 추론:

- 6개월~1년 scope에서는 proxy semantic-pair benchmark만으로는 부족하다. Semantic mapping contribution이 top-tier로 보이려면 map state가 embodied search/navigation behavior, perception robustness, task-conditioned decision으로 이어져야 한다.
- 단, 모든 요소를 full real-robot deployment로 만들 필요는 없다. 우선순위는 scalable benchmark, embodied search-cost bridge, perception robustness subset, task-context ablation 순서다.

사용자 판단 필요:

- 최종 thesis direction은 E001 scale-up과 embodied / perception bridge 결과를 본 뒤 확정한다.

## Core Hypothesis

로봇이 사람의 자연어 지시를 안정적으로 수행하려면, mapping은 geometry reconstruction 이후에 붙는 후처리가 아니라 instruction grounding, object state tracking, action planning과 함께 설계되어야 한다.

## 연구 렌즈

### Map Representation

semantic map은 다음 정보를 분리해서 저장해야 한다.

- metric geometry: occupancy, free space, traversability, camera pose uncertainty
- object instances: object mask, 3D extent, category, open-vocabulary feature, confidence
- relations: on, in, near, between, left/right of, visible from, reachable from
- affordances: graspable, placeable, openable, support surface, obstacle, landmark
- temporal state: moved, disappeared, newly observed, stale, dynamic
- human-facing semantics: user names, preferences, task-relevant aliases, room-level concepts

### Human Intention

사람의 의도는 명령 문장 자체보다 넓다. 다음 신호를 map과 연결할 수 있어야 한다.

- explicit command: "bring the mug next to the laptop"
- underspecified command: "clean this area", "put it where it belongs"
- correction: "not that one", "the cup I used earlier"
- preference: fragile objects, private areas, frequently used objects
- common sense: dishes near sink, chargers near outlets, medicine in cabinet

### Task Grounding

좋은 map은 query에 답하는 것에서 끝나지 않고 action으로 이어져야 한다.

- semantic navigation: open-vocabulary object/room/landmark search
- mobile manipulation: find, approach, pick, place, rearrange
- human-aware assistance: ask clarification, remember user-specific object names, avoid unsafe assumptions
- interactive recovery: update map after a failed grounding or a human correction

## Contribution Candidate Requirements

각 후보는 다음을 명확히 해야 한다.

- 어떤 기존 한계에서 출발하는가
- 왜 이것이 semantic mapping 문제인가
- 어떤 dataset, benchmark, metric으로 확인할 수 있는가
- 실패했을 때 무엇을 배울 수 있는가

현재 후보 목록과 세부 판단은 [Contribution Candidates.md](<Contribution Candidates.md>)와 [CAND-001.md](CAND-001.md), [CAND-002.md](CAND-002.md), [CAND-003.md](CAND-003.md)에서 관리한다. 이 파일은 연구 방향의 상위 관점만 유지한다.

## Current Leading Candidate

에이전트 추론:

- 현재 leading candidate는 [CAND-001: Intent- And Staleness-Aware Semantic Mapping](CAND-001.md)이다.
- 이유는 Clio의 task-driven granularity, DualMap/OpenIN의 dynamic memory, OGScene3D/OVI-MAP의 incremental instance-semantic mapping 흐름을 하나의 semantic mapping 문제로 연결할 수 있기 때문이다.

사용자 판단 필요:

- 첫 실험을 moved-object stale memory로 좁힐지, instruction-conditioned re-observation으로 좁힐지 결정해야 한다.

## Initial Contribution Candidates

### 1. Intent-Conditioned Semantic Map Update

사람의 지시가 들어왔을 때 모든 semantic feature를 균일하게 갱신하지 않고, task-relevant objects, relations, and affordances를 우선적으로 갱신하는 online semantic mapping 방법.

기존 한계:

- 많은 open-vocabulary semantic map은 RGB-D stream에서 얻은 VLM feature를 task-agnostic하게 누적한다.
- navigation이나 manipulation에서 실제로 필요한 것은 전체 장면의 평균적인 semantic coverage가 아니라 현재 지시와 관련된 object, relation, affordance의 정확한 grounding이다.
- task-agnostic fusion은 compute/memory를 많이 쓰면서도 ambiguous instruction이나 correction 이후에 어떤 map evidence를 갱신해야 하는지 명확하지 않다.

왜 semantic mapping 문제인가:

- 핵심은 language parser 자체가 아니라 observation을 어떤 semantic memory로 저장하고, 지시가 들어왔을 때 어떤 map cell/object/relation을 갱신하거나 재조회할지 결정하는 문제다.
- map representation이 task relevance, uncertainty, relation evidence를 담지 못하면 downstream planner는 같은 instruction에서도 불필요한 search나 잘못된 goal selection을 하게 된다.

검증 후보:

- Datasets/benchmarks: Habitat-Matterport 3D, HM3D ObjectNav, Replica, AI2-THOR, RoboTHOR, 실내 RGB-D replay log
- Metrics: text-to-object Recall@k, task success, SPL, false-positive goal rate, map memory, update latency, query latency
- Baselines: 2D VLM retrieval, VLMaps-style dense map, object-level static map, oracle object map

실패했을 때 배우는 것:

- intent-conditioned update가 성능을 올리지 못하면 current bottleneck은 map update가 아니라 perception quality, query parsing, or planner interface일 가능성이 크다.
- memory/latency만 줄고 success가 오르지 않으면 efficiency contribution으로 방향을 좁혀야 한다.
- ambiguous instruction에서만 효과가 있으면 benchmark를 ambiguity/correction 중심으로 재설계해야 한다.

논문 claim 후보:

- instruction-conditioned map update reduces unnecessary memory/compute while improving task success under ambiguous natural language commands.

필요한 증거:

- 동일한 RGB-D stream에서 task-agnostic map과 비교
- object grounding accuracy, task success, map memory, latency 측정
- ambiguous instruction과 correction scenario 포함

### 2. Common-Ground Semantic Mapping

사람 시점과 로봇 시점의 semantic mismatch를 줄이는 map representation. 예를 들어 사람은 "the box under the desk"라고 말하지만 로봇은 낮은 시점에서 desk underside만 보거나 object가 occluded되어 있을 수 있다.

기존 한계:

- 기존 semantic mapping은 주로 robot observation 기준으로 map을 만든다.
- 사람의 명령은 human viewpoint, prior knowledge, room-level common sense, occluded object expectation을 포함하는 경우가 많다.
- 낮은 카메라 높이, 제한된 field of view, occlusion 때문에 robot-view semantic confidence와 human-facing object description이 불일치한다.

왜 semantic mapping 문제인가:

- 문제의 중심은 human phrase를 2D image에 matching하는 것이 아니라, 서로 다른 관찰 가능성과 시점에서 생긴 semantic evidence를 하나의 shared spatial memory로 정렬하는 것이다.
- map이 viewpoint provenance, visibility, occlusion, relation evidence를 저장해야 "사람은 보았지만 로봇은 못 본 물체"와 "로봇이 다른 이름으로 본 물체"를 구분할 수 있다.

검증 후보:

- Datasets/benchmarks: Matterport3D/HM3D에서 human-height vs robot-height rendered views, ScanNet/Replica multi-view RGB-D, custom paired human-robot viewpoint replay
- Metrics: grounding accuracy under viewpoint shift, hidden/partially visible object localization, relation grounding accuracy, clarification need rate, correction success rate
- Baselines: robot-view-only semantic map, human-view-only retrieval, view-agnostic 3D feature fusion, oracle visibility map

실패했을 때 배우는 것:

- viewpoint-aware mapping이 도움이 안 되면 mismatch의 주원인은 시점보다 open-vocabulary feature quality나 language relation parsing일 수 있다.
- hidden object에서는 좋아지고 visible object에서는 차이가 없으면 contribution을 occlusion-aware/common-ground memory로 좁힌다.
- clarification rate가 줄지 않으면 map은 좋아졌지만 interaction policy가 bottleneck이라는 증거다.

논문 claim 후보:

- human-robot viewpoint-aware semantic matching improves grounding of human instructions in partially observed scenes.

필요한 증거:

- human-view vs robot-view observation split
- hidden/partially visible object localization
- clarification turns or correction success rate

### 3. Dynamic Open-Vocabulary Object Memory

open-vocabulary semantic map에서 object가 이동, 사라짐, 재등장할 때 stale semantics를 줄이고 task execution을 안정화하는 object-level memory update 방식.

기존 한계:

- open-vocabulary semantic maps는 장면을 누적할수록 과거 evidence가 남아 confidently stale한 object location을 만들 수 있다.
- 동적 실내 환경에서는 컵, 의자, 가방, 도구처럼 task-relevant object가 자주 이동한다.
- 기존 static map 평가만으로는 "예전에는 맞았지만 지금은 틀린 semantic memory"가 task failure로 이어지는지 잘 드러나지 않는다.

왜 semantic mapping 문제인가:

- object가 이동했을 때 문제가 되는 것은 detector 한 번의 오류가 아니라 map memory의 update, deletion, confidence decay, re-identification policy다.
- semantic map이 object state와 staleness를 표현하지 못하면 planner는 오래된 semantic location을 신뢰한다.

검증 후보:

- Datasets/benchmarks: AI2-THOR rearrangement, Habitat rearrangement, iGibson dynamic scenes, BEHAVIOR-style household tasks, custom before/after RGB-D replay
- Metrics: stale object false-positive rate, moved-object localization accuracy, task success before/after scene change, re-observation recovery time, online update latency
- Baselines: static object map, naive overwrite map, time-decay confidence map, oracle current object poses

실패했을 때 배우는 것:

- stale modeling이 효과가 없으면 task failure가 semantic memory보다 exploration or manipulation control에서 발생하는지 분리해야 한다.
- false-positive는 줄지만 recall도 줄면 confidence decay가 너무 공격적이라는 의미다.
- simulation에서는 효과가 있고 real replay에서 실패하면 pose noise, occlusion, re-identification이 핵심 병목이다.

논문 claim 후보:

- explicitly modeling semantic staleness and object state changes improves navigation/manipulation success in dynamic indoor environments.

필요한 증거:

- before/after object move episodes
- false-positive goal selection rate
- online update latency
- real robot or high-fidelity replay experiment

## Top-Tier Contribution Bar

top-tier venue에서 강하게 보이려면 다음 중 2개 이상이 필요하다.

- algorithmic novelty: map representation, fusion, update, uncertainty, relation reasoning 중 하나가 새롭다.
- empirical novelty: 기존 benchmark 외에 사람 지시/동적 변화/실로봇 시나리오가 들어간다.
- systems value: latency, memory, robustness가 실제 로봇 배치 수준으로 측정된다.
- analysis depth: ablation, failure modes, sensitivity analysis가 논문의 핵심 주장과 직접 연결된다.
- reproducibility: code, configs, data manifest, exact commands, pretrained weights 또는 replay logs가 준비된다.

## Six-to-Twelve-Month Top-Tier Target

6개월~1년 target에서 기본적으로 포함할 요소:

- E001: `3RScan` / `3DSSG` reference-rescan semantic-pair benchmark scale-up.
- E002: dynamic object search/navigation bridge with `ExpectedSearchCost`, `SR`, `SPL`, and path/search cost.
- E003: RGB-D / open-vocabulary perception noise robustness, at least on a defensible subset.
- E004: human task context as memory trust / re-observation / candidate-budget condition, not as the main language-understanding claim.

에이전트 추론:

- 위 4개가 모두 들어가면 논문은 "stale memory update heuristic"이 아니라 "task-conditioned semantic memory trust improves dynamic search/navigation under stale maps and perception noise"로 주장할 수 있다.
- 이 경우 top-tier 가능성은 현재 proxy-only 상태보다 크게 올라간다. 핵심 risk는 engineering scope와 dataset coverage다.

## Intermediate Submission Ladder

중간 투고가 가능한 단계:

| 단계 | 가능한 투고 형태 | 성립 조건 | 한계 |
| --- | --- | --- | --- |
| E001 benchmark / proxy paper | workshop, short paper, dataset/protocol paper | scaled pair/query benchmark, fixed baselines, failure taxonomy, exact commands | real navigation과 real perception claim은 약함 |
| E002 embodied search bridge | robotics / embodied AI workshop 또는 conference submission seed | `ExpectedSearchCost`, proxy/embodied `SR`, proxy/embodied `SPL`, path/search cost가 static/fixed top-k보다 개선 | simulator or proxy design이 약하면 reviewer가 task realism을 공격 가능 |
| E003 perception robustness paper | CV/robot perception workshop 또는 full-paper component | RGB-D replay or open-vocabulary proposal noise에서 stale-memory update가 유지됨 | detector choice, compute, pseudo-label fairness 부담 |
| E004 full top-tier submission | CoRL / ICRA / CVPR / ICCV / ECCV / NeurIPS 계열 full paper target | E001+E002+E003에 task-context memory trust / re-observation ablation까지 연결 | engineering scope가 크고, 모든 claim boundary를 방어해야 함 |

에이전트 추론:

- 중간 투고는 최종 top-tier paper를 약화시키지 않도록 claim을 좁게 가져가야 한다.
- E001만으로 투고한다면 "method paper"보다 "benchmark/protocol + strong analysis"가 더 안전하다.
- 최종 full paper는 E001-E004를 하나의 story로 묶어야 한다.

## Beyond Added Scope

top-tier 가능성을 더 높이는 추가 요소와 부담:

| 추가 요소 | 기대 이득 | 부담 |
| --- | --- | --- |
| real robot 또는 high-fidelity embodied deployment | CoRL / ICRA reviewer에게 가장 설득력 있는 behavior evidence | 하드웨어, safety, calibration, repeated trials, failure recovery 부담이 큼 |
| public benchmark / dataset protocol release | empirical contribution이 강해지고 reproducibility가 좋아짐 | license, hosting, split design, baseline maintenance, documentation 부담 |
| learned memory trust / re-observation policy | heuristic이라는 약점을 줄이고 algorithmic novelty가 커짐 | training data, overfitting, ablation, policy interpretability 부담 |
| multi-dataset generalization | dataset-specific artifact 비판을 줄임 | `3RScan`, `AI2-THOR`, `Habitat`, `HM3D` 등 schema 통합 부담 |
| open-vocabulary detector ensemble robustness | perception robustness claim 강화 | detector setup, compute, noisy pseudo-label, fair comparison 부담 |
| human-in-the-loop task context or correction study | human-friendly robot intelligence와 직접 연결 | IRB/consent 가능성, user study design, annotation consistency 부담 |
| manipulation/rearrangement extension | search를 넘어 task execution contribution으로 확장 | simulator/hardware integration, grasp/place success confound 부담 |

## What Not To Do First

- 처음부터 거대한 foundation model을 fine-tune하려 하지 않는다.
- "semantic map + LLM"이라는 조합만으로 novelty를 주장하지 않는다.
- scene visualization demo만 만들고 quantitative evaluation을 미루지 않는다.
- dataset release를 contribution으로 쓰려면 license, consent, split, baseline, hosting 계획 없이 시작하지 않는다.

## First Small Step

첫 번째 작은 실험은 "RGB-D sequence + natural-language query + object localization"으로 제한한다.

최소 입력:

- RGB-D frames or replay log
- camera poses
- text query
- object/region ground truth or human annotation

최소 출력:

- query-relevant object or region
- confidence
- map update summary
- failure reason when grounding fails

성공 기준:

- baseline보다 grounding accuracy 또는 task success가 높다.
- latency와 memory overhead를 함께 보고한다.
- 실패 사례를 10개 이상 모아 category를 만든다.
