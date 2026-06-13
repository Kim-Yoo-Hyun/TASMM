# Literature Survey: Semantic Mapping For Human-Friendly Robot Intelligence

Updated: 2026-06-09

검색/확인 범위: 2024-2026 primary sources 중심. 사용한 우선순위는 논문 PDF, arXiv, CVF Open Access, OpenReview, 공식 project page, 공식 code repository 순서다.

## Current Targeted Refresh

사실:

- E008-M137 설계를 위해 [CAND-001_top-tier-refresh-2026.md](CAND-001_top-tier-refresh-2026.md)를 추가했다.
- 이 문서는 100-paper metadata scan, 25-paper deep-read shortlist, 9-codebase audit, 7개 H001 integration proposal, 3-persona orthogonal review를 관리한다.

에이전트 추론:

- 현재 추가 문헌 조사의 목적은 broad survey 확장이 아니라 `confidence-preserving trajectory-aware repair`, source-gap/source-coverage decision, external map/navigation baseline 방어를 E008-M137에 연결하는 것이다.

## Field Map

### 1. Open-Vocabulary Spatial Feature Maps

사실:

- 이 축은 VLM/CLIP-style semantics를 3D map, voxel field, Gaussian field, 또는 frontier map으로 lift해서 text query나 ObjectNav에 연결한다.
- 대표 폴더: [2024_icra_vlfm](2024_icra_vlfm/README.md), [2024_eccv_o2v-mapping](2024_eccv_o2v-mapping/README.md), [2024_cvpr_langsplat](2024_cvpr_langsplat/README.md), [2024_arxiv_ovo-slam](2024_arxiv_ovo-slam/README.md), [2026_arxiv_ovi-map](2026_arxiv_ovi-map/README.md).

논문 주장:

- VLFM은 vision-language frontier value가 zero-shot ObjectNav를 돕는다고 주장한다.
- O2V-Mapping은 online open-vocabulary mapping에서 local update, hierarchical segmentation, multi-view consistency 문제를 다룬다.
- OVI-MAP은 class-agnostic instance reconstruction과 semantic inference를 분리하면 online instance-semantic consistency를 높일 수 있다고 주장한다.

에이전트 추론:

- 이 축은 map이 "어디에 무엇이 있는가"를 답하는 데 강하지만, 사람 의도, dynamic staleness, affordance를 직접 모델링하지 않으면 human-friendly robot intelligence로는 약하다.

### 2. Object-Centric / Scene-Graph Semantic Maps

사실:

- dense feature map의 memory, scalability, relation reasoning 문제를 object graph, hierarchical graph, octree graph, scene graph backend로 해결하려는 흐름이다.
- 대표 폴더: [2024_icra_conceptgraphs](2024_icra_conceptgraphs/README.md), [2024_cvpr_open3dsg](2024_cvpr_open3dsg/README.md), [2024_rss_hov-sg](2024_rss_hov-sg/README.md), [2024_arxiv_clio](2024_arxiv_clio/README.md), [2025_iccv_octree-graph](2025_iccv_octree-graph/README.md), [2026_arxiv_ogscene3d](2026_arxiv_ogscene3d/README.md).

논문 주장:

- ConceptGraphs는 open-vocabulary 3D scene graph가 perception과 planning 사이의 interface가 될 수 있다고 주장한다.
- HOV-SG는 floor-room-object hierarchy가 large-scale language-grounded navigation에 필요하다고 주장한다.
- Clio는 task list가 주어졌을 때 map granularity 자체가 task-dependent라고 주장한다.

에이전트 추론:

- 이 축은 "semantic mapping이 왜 단순 perception이 아닌가"를 가장 잘 보여준다. map representation이 downstream reasoning의 search space와 failure mode를 직접 결정한다.

### 3. Dynamic / Lifelong Object Memory

사실:

- 2025 이후 논문들은 moved object, repeated query, dynamic scene, stale memory 문제를 더 직접적으로 다룬다.
- 대표 폴더: [2024_cvpr_goat-bench](2024_cvpr_goat-bench/README.md), [2024_arxiv_one-map](2024_arxiv_one-map/README.md), [2025_ral_dualmap](2025_ral_dualmap/README.md), [2025_arxiv_openin](2025_arxiv_openin/README.md), [2025_arxiv_findanything](2025_arxiv_findanything/README.md), [2025_cvpr_3d-mem](2025_cvpr_3d-mem/README.md).

논문 주장:

- DualMap은 global abstract map과 local concrete map을 나누면 dynamic changing scenes에서 online language navigation을 더 효율적으로 처리할 수 있다고 주장한다.
- OpenIN은 Carrier-Relationship Scene Graph가 moved target navigation에 유리하다고 주장한다.
- GOAT-Bench는 multimodal lifelong navigation 평가를 통해 reusable memory의 필요성을 드러낸다.

에이전트 추론:

- "stale semantics"는 좋은 석사 주제다. 실패해도 perception, re-identification, memory decay, exploration policy 중 어느 병목인지 분리해서 배울 수 있다.

### 4. Human-Facing Benchmarks / Functional Semantics

사실:

- 최근 benchmark는 object category만 묻지 않고 embodied QA, instruction grounding, multi-granularity goal, functional relationship을 평가한다.
- 대표 폴더: [2024_cvpr_embodiedscan](2024_cvpr_embodiedscan/README.md), [2024_cvpr_openeqa](2024_cvpr_openeqa/README.md), [2024_arxiv_hm3d-ovon](2024_arxiv_hm3d-ovon/README.md), [2025_acmmm_openmap](2025_acmmm_openmap/README.md), [2025_cvpr_openfungraph](2025_cvpr_openfungraph/README.md), [2026_arxiv_langmap](2026_arxiv_langmap/README.md).

논문 주장:

- OpenEQA는 embodied agents가 environment memory를 이용해 natural-language questions에 답해야 한다고 문제를 재정의한다.
- OpenMap은 instruction grounding을 위해 instance-level visual-language map의 structural-semantic consistency가 중요하다고 주장한다.
- Open-Vocabulary Functional 3D Scene Graphs는 spatial relation만으로는 부족하고 functional relation이 필요하다고 주장한다.
- LangMap은 scene, room, region, instance level을 나누는 hierarchical goal navigation benchmark를 제안한다.

에이전트 추론:

- "open-vocabulary" 자체는 human-friendly가 아니다. 사람을 위한 robot intelligence를 주장하려면 ambiguity, correction, functional relation, user-facing task success 중 하나를 평가에 넣어야 한다.

## Trend Synthesis

### 2024

사실:

- 2024년에는 open-vocabulary map을 embodied navigation, 3D scene graph, embodied QA benchmark로 연결하는 작업이 많다.
- VLFM, O2V-Mapping, ConceptGraphs, Open3DSG, HOV-SG, Clio, OpenEQA, GOAT-Bench, EmbodiedScan이 이 흐름을 대표한다.

에이전트 추론:

- 2024년의 중심 질문은 "foundation model semantics를 3D 공간에 어떻게 저장하고 query할 것인가"였다.

### 2025

사실:

- 2025년에는 dynamic scene, instruction grounding, functional scene graph, memory-efficient representation, instance-oriented navigation이 강해졌다.
- DualMap, OpenIN, OpenMap, Open-Vocabulary Functional 3D Scene Graphs, 3D-Mem, FindAnything이 이 축에 있다.

에이전트 추론:

- 2025년의 중심 질문은 "이 map이 실제 robot task에서 오래 쓸 수 있는가"로 이동했다.

### 2026

사실:

- 2026년 초 preprint들은 incremental mapping, hierarchical benchmark, instance-semantic separation, Gaussian scene graph update를 강조한다.
- LangMap, OVI-MAP, OGScene3D가 여기에 해당한다.

에이전트 추론:

- 2026년의 초기 흐름은 "online/incremental + hierarchy + temporal confidence"다. 새 논문은 이 흐름을 따라가되, 단순 incremental 구현보다 새로운 insight를 줘야 한다.

## Cross-Paper Insights

### Insight 1. Map Granularity Is Becoming A Research Question

사실:

- Clio는 task-driven granularity를 명시적으로 다룬다.
- HOV-SG와 LangMap은 floor/room/region/object처럼 abstraction level을 나눈다.
- OpenMap과 OVI-MAP은 instance-level consistency를 강조한다.

에이전트 추론:

- semantic mapping 논문은 "우리 map은 무엇을 저장하는가"보다 "현재 human task에 어떤 granularity가 필요한가"를 물어야 더 최신 흐름에 맞다.

### Insight 2. Dynamic Memory Is Not Just Time Decay

사실:

- DualMap은 global/local map role 분리를 사용한다.
- OpenIN은 moved object를 carrier relationship으로 추론한다.
- OGScene3D는 confidence와 temporal memory를 incremental graph update에 사용한다.

에이전트 추론:

- stale object 문제를 단순히 오래된 confidence를 낮추는 방식으로 풀면 contribution이 약하다. relation, task intent, re-observation policy가 함께 들어가야 한다.

### Insight 3. Evaluation Is The Real Differentiator

사실:

- benchmark 축은 ObjectNav success/SPL, instruction grounding accuracy, functional relation prediction, embodied QA, memory/repeated-goal navigation으로 나뉜다.
- mapping quality만 보고하는 논문보다 downstream task와 연결한 논문이 human-friendly robot intelligence 주장에 더 가깝다.

에이전트 추론:

- 석사 논문에서는 full robot system을 처음부터 만들기보다 RGB-D replay + language query + dynamic change episodes로 mapping bottleneck을 분리하는 편이 현실적이다.

## Open Questions

### OQ1. Intent-Aware Granularity Selection

질문:

- 사람 지시가 주어졌을 때 semantic map이 object/part/region/room 중 필요한 granularity를 online으로 선택할 수 있는가?

확인 가능성:

- Dataset/benchmark: LangMap, OpenMap/Matterport3D instruction grounding, HM3D rendered replay
- Metrics: grounding accuracy, false-positive target rate, query latency, map size

사용자 판단 필요:

- 이 주제는 Clio와 가까워서 novelty를 task intent + dynamic staleness까지 확장할지 판단해야 한다.

### OQ2. Staleness-Aware Object Memory

질문:

- moved object나 missing object에 대해 semantic map이 "현재 믿어도 되는 object memory"와 "다시 확인해야 하는 memory"를 구분할 수 있는가?

확인 가능성:

- Dataset/benchmark: OpenIN-style long-sequence Habitat tasks, AI2-THOR rearrangement, custom before/after RGB-D replay
- Metrics: stale false-positive rate, moved-object recovery time, task success after scene change, online update latency

사용자 판단 필요:

- 실로봇 없이 먼저 replay benchmark로 갈지, 작은 실내 real RGB-D log를 직접 수집할지 정해야 한다.

### OQ3. Functional Semantic Mapping For Assistance

질문:

- map이 category와 location뿐 아니라 "무엇을 올려둘 수 있는가", "어디에 보관해야 하는가", "어떤 object가 task affordance를 갖는가"를 저장하면 human instruction following이 좋아지는가?

확인 가능성:

- Dataset/benchmark: FunGraph3D, SceneFun3D, BEHAVIOR-style household tasks
- Metrics: functional relation accuracy, task completion, implausible placement rate

사용자 판단 필요:

- 이 방향은 human-friendly와 잘 맞지만 dataset annotation 부담이 커질 수 있다.

### OQ4. Common-Ground Semantic Mapping

질문:

- human viewpoint와 robot viewpoint가 다를 때 shared semantic map이 instruction grounding failure를 줄일 수 있는가?

확인 가능성:

- Dataset/benchmark: HM3D/Replica human-height vs robot-height render split, paired replay
- Metrics: viewpoint-shift grounding accuracy, correction success rate, clarification need rate

사용자 판단 필요:

- 이 방향은 original insight가 좋지만 benchmark를 직접 설계해야 할 가능성이 높다.

## Current Candidate Direction

에이전트 추론:

> Intent- and staleness-aware semantic mapping for human instruction following in dynamic indoor environments.

이 방향은 2024의 open-vocabulary mapping, 2025의 dynamic memory, 2026의 incremental/hierarchical benchmark 흐름을 잇는다. 동시에 "왜 semantic mapping 문제인가"가 분명하다: map이 무엇을 저장하고, 무엇을 오래 믿고, 무엇을 다시 확인하고, 어떤 granularity로 query해야 하는지를 결정하는 문제이기 때문이다.

사용자 판단 필요:

- 첫 실험은 `OQ2. Staleness-Aware Object Memory`로 좁히는 것이 현실적인지 판단해야 한다.
