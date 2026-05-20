# Semantic Mapping Research Workspace

업데이트: 2026-05-21

이 워크스페이스는 semantic mapping을 중심으로, human-friendly robot intelligence 연구를 작게 시작하기 위한 문서 기반 작업 공간이다. 목표는 로봇이 사람의 의도와 지식을 이해하고, 그 이해를 공간적 기억과 행동으로 연결하여 사람이 요구하는 복잡한 작업을 수행하게 하는 것이다.

현재 연구 제약은 6개월~1년 규모로 둔다. 최종 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`으로, AI, ML, CV, Robotics top-tier journal/conference를 겨냥한다. 중간에 독립적인 contribution이 성립하면 workshop, short paper, 또는 관련 venue에 먼저 투고할 수 있다.

## 현재 원칙

- 작업을 시작할 때 [TODO.md](TODO.md)를 먼저 확인한다.
- 작업 중 새 task가 생기면 [TODO.md](TODO.md)에 추가한다.
- 빈 `paper/` 폴더를 미리 만들지 않는다. 논문 폴더는 연구 질문, 핵심 그림, 실험 테이블이 최소 1개씩 생긴 뒤 만든다.
- 먼저 Markdown으로 연구 주장, 실험 하네스, 재현성 기준, 관련 논문 읽기 방식을 고정한다.
- 코드는 첫 번째 실험이 명확해졌을 때 만든다. 그 전에는 폴더 구조보다 문제 정의와 평가 축을 우선한다.
- AI, ML, CV, Robotics top-tier journal/conference 제출을 목표로 하되, venue별 양식보다 먼저 "강한 주장 + 재현 가능한 증거 + 명확한 한계"를 만든다.

## 문서

- [TODO.md](TODO.md): 계획, 상태, 다음 행동
- [AGENTS.md](AGENTS.md): 작업자가 따라야 할 운영 규칙
- [docs/index.md](docs/index.md): workflow 문서 인덱스
- [docs/literature.md](docs/literature.md): 문헌조사 workflow와 작성 규칙
- [docs/hypothesis.md](docs/hypothesis.md): hypothesis workflow와 작성 규칙
- [docs/experiments.md](docs/experiments.md): experiment workflow와 작성 규칙
- [experiments/README.md](experiments/README.md): main experiment index
- [docs/paper.md](docs/paper.md): 논문 작성 프로토콜 초안. 논문 작성 단계에서 다시 정리한다.
- [docs/reproducibility.md](docs/reproducibility.md): 데이터, checkpoint, Docker, 재현 명령, artifact/evaluation 요약
- [literature/README.md](literature/README.md): field map, trend synthesis, cross-paper insights, open questions
- [literature/PAPER.md](literature/PAPER.md): paper registry와 reading queue
- [literature/Contribution Candidates.md](<literature/Contribution Candidates.md>): contribution candidate 목록
- [literature/research_direction.md](literature/research_direction.md): semantic mapping 연구 방향과 초기 문제 후보
- [hypothesis/README.md](hypothesis/README.md): hypothesis index

## 현재 진행 상황

- Active candidate: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`
- Active hypothesis: `H001_stale-object-memory`
- Final paper target: Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`
- Current implementation path: Direction A `Task-Conditioned Stale Semantic Memory`를 core method로 만들고, real RGB-D/open-vocabulary proposal bridge, external baselines, search/navigation metrics를 붙여 Direction B로 확장
- Current experiment: [E005_external_baseline_transition](experiments/E005_external_baseline_transition/README.md)
- Current E004 status: E004-M01 transition gate is `ready_with_constraints`; E004-M02 metric contract is `ready`; E004-M03 memory trust policy is `ready_with_constraints`; E004-M04 claim-boundary ablation is `ready`; E004-M05 scale/split stress is `ready_limited_task_context`. E004-M05 supports a split-supported memory-trust decision claim, but task-context-specific claim strength remains limited and not label-broad. The next unit is E005 external baseline transition.
- Current E005 status: E005-M01 through E005-M58 are complete/verified with constraints, and E005-M59 `Open3DSG` object-candidate export smoke has failed on GPU memory during `InstructBLIP` checkpoint loading. `DualMap` staging and runtime execute on the staged `3RScan` adapter, but M14/M17 produce no object `*.pkl` outputs. `ConceptGraphs` is the active external mapping baseline route; all 9 heldout scans have runtime output and query-level conversion. Full heldout `ConceptGraphs` strict bbox top5 is 114/195 = 0.584615, relaxed bbox 1m top3 is 144/195 = 0.738462. H001 heldout policy replay on the same `M38` contract gives H001 172/195 = 0.882051, static memory 141/195 = 0.723077, and context-agnostic memory trust 171/195 = 0.876923. E005-M56 fixes a two-table robustness denominator: Table A proxy-search external map rows 195 and Table B real RGB-D proposal bridge rows 96. `/home/yoohyun/research/local_dataset/Open3DSG_staged` is readable and is used only as a read-only source; derived `Open3DSG` bridge data is stored under `/home/yoohyun/research2/local_dataset/Open3DSG_bridge/`. E005-M57 confirms relation raw dump readiness and feature/checkpoint route feasibility. E005-M58 fixes the `Open3DSG` object-candidate schema, read-only Docker command contract, and verifier. E005-M59 launched with tmux session `e005_m59_open3dsg_object_export`, log `logs/20260521_044206_e005_m59_open3dsg_object_export.log`, and output path `local_dataset/Open3DSG_bridge/E005-M59_object_candidate_export_smoke_v0/`; as of 2026-05-21 04:54 KST, tmux is stopped, candidate rows are not written, source modified is false, and `Open3DSG` query-level performance claim remains false. `OpenMask3D` remains a later proposal baseline because its Docker/`MinkowskiEngine` blocker remains. Real RGB-D/open-vocabulary robustness and real navigation `SR` / `SPL` remain blocked.
- Current boundary: main experiment implementation 단계이며, paper 폴더는 아직 만들지 않는다.
- Current top-tier path: E001 benchmark/proxy -> E002 search/navigation bridge -> E003 controlled perception/proposal noise -> Dockerized RGB-D/open-vocabulary proposal route -> E003-M75 expanded query-level evaluation -> E004 task-context memory trust / re-observation decision with split stress -> E005 external baselines and dataset-format staging -> Direction B mapping-navigation system evidence.

## 작업 루프

1. `TODO.md`에서 현재 next action을 확인한다.
2. 문헌조사는 `docs/literature.md`의 workflow를 따른다.
3. `literature/PAPER.md`의 `Reading Queue`에서 논문을 고르고 각 paper folder에 기록한다.
4. `literature/Contribution Candidates.md`에서 후보를 고르고 `literature/CAND-*.md`로 구체화한다.
5. Hypothesis 작업은 `docs/hypothesis.md`의 entry context와 workflow를 따른다.
6. `hypothesis/` 아래에서 후보 문제를 한 문장 hypothesis로 좁힌다.
7. 실제 구현 단계에서는 `docs/experiments.md`의 규칙을 따르고 `experiments/` 아래에 experiment 내용을 기록한다.
8. 논문 작성 단계가 오면 `docs/paper.md`를 다시 정리하고 claim-evidence ledger를 채운다.
9. claim-evidence ledger가 채워진 뒤에만 실제 paper draft 폴더를 만든다.

## 연구 기준

좋은 semantic mapping 논문은 단순히 "VLM feature를 3D map에 넣었다"에서 끝나지 않는다. top-tier를 노리려면 다음 중 적어도 하나가 선명해야 한다.

- 새로운 map representation이 기존 방식보다 명확히 더 쓸모 있다.
- 사람의 언어, 의도, 상식, 선호가 map update나 task execution에 실제로 영향을 준다.
- navigation, manipulation, search, instruction following 같은 downstream task에서 성능 차이가 난다.
- 실험이 simulation에만 갇히지 않고 real-world noise, dynamic changes, embodiment gap 중 하나를 정면으로 다룬다.
- 실패 사례와 한계가 논문 안에서 정직하게 다뤄지고, 재현 가능한 코드/데이터/명령으로 뒷받침된다.
