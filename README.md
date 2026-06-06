# Semantic Mapping Research Workspace

업데이트: 2026-06-06

이 워크스페이스는 semantic mapping을 중심으로 human-friendly robot intelligence를 연구하는 작업 공간이다. 목표는 로봇이 사람의 의도와 지식을 공간적 기억과 행동으로 연결하여, 사람이 요구하는 복잡한 search/navigation task를 수행하게 하는 것이다.

현재 연구 제약은 6개월~1년 규모로 둔다. 최종 목표는 Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`으로, AI, ML, CV, Robotics top-tier journal/conference를 겨냥한다. 중간에 독립적인 contribution이 성립하면 workshop, short paper, 또는 관련 venue에 먼저 투고할 수 있다.

## 현재 원칙

- 작업을 시작할 때 [AGENTS.md](AGENTS.md) -> [README.md](README.md) -> [TODO.md](TODO.md) -> [docs/index.md](docs/index.md) 순서로 확인한다.
- 실제 작업 우선순위는 [TODO.md](TODO.md)의 Now/Next를 따른다.
- 작업 중 새 task가 생기면 [TODO.md](TODO.md)에 추가하고, 완료 후에는 가까운 책임 문서와 함께 갱신한다.
- [AGENTS.md](AGENTS.md)는 repo-level 규칙, 작업 기대치, 파일 책임, novelty 기준, Docker/reproducibility 원칙만 관리한다.
- 빈 `paper/` 폴더를 미리 만들지 않는다. 논문 폴더는 thesis, main result table, method figure, target venue, claim-evidence ledger가 구체화된 뒤 만든다.
- 세부 결과나 긴 실험 기록은 루트 README에 반복하지 않고 해당 workflow 문서, 가까운 폴더 `README.md`, `report.md`, artifact note에 기록한다.
- AI, ML, CV, Robotics top-tier journal/conference 제출을 목표로 하되, venue별 양식보다 먼저 "강한 주장 + 재현 가능한 증거 + 명확한 한계"를 만든다.

## 문서 지도

- [AGENTS.md](AGENTS.md): repo-level 작업 규칙과 판단 기준
- [TODO.md](TODO.md): Now/Next/Completed 중심의 작업판
- [summary.md](summary.md): 연구 방향, 배경, 가설, 진행 상태, 남은 쟁점, 실험 계획 요약
- [docs/index.md](docs/index.md): 전체 문서 지도와 읽는 순서
- [docs/literature.md](docs/literature.md): 문헌조사 workflow와 작성 규칙
- [docs/hypothesis.md](docs/hypothesis.md): hypothesis workflow와 작성 규칙
- [docs/experiments.md](docs/experiments.md): experiment workflow와 작성 규칙
- [docs/paper.md](docs/paper.md): paper framing, novelty, reviewer-defense 기준
- [docs/reproducibility.md](docs/reproducibility.md): 데이터, checkpoint, Docker, artifact, 재현 명령 기준
- [literature/README.md](literature/README.md): 문헌 조사 결과의 cross-paper synthesis
- [hypothesis/README.md](hypothesis/README.md): hypothesis index와 active gate
- [experiments/README.md](experiments/README.md): main experiment index
- [experiments/report.md](experiments/report.md): 기여점, reviewer defense, 최종 논문 방향성

각 폴더의 `README.md`는 해당 폴더의 local entry point다. 세부 결과는 가장 가까운 local README, report, 또는 artifact note에 기록한다.

## 현재 진행 상황

- Active candidate: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`
- Active hypothesis: `H001_stale-object-memory`
- Final paper target: Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`
- Current implementation path: Direction A `Task-Conditioned Stale Semantic Memory`를 core method로 만들고, real RGB-D/open-vocabulary proposal bridge, external baselines, search/navigation metrics를 붙여 Direction B로 확장
- Current experiment: [E008_real_navigation_benchmark](experiments/E008_real_navigation_benchmark/README.md)
- Current status: E001-E007 have built proxy search, perception-noise, external-baseline, path-cost bridge, and E006 human-intent claim/strong-baseline/transfer-stress/utility-formula/schema/policy/metric materialization with constraints; E006-M08 keeps human intent as secondary conditioning / ablation evidence because the main-claim gate fails against the strongest context-agnostic baselines. E008 is validating whether `HM3D ObjectNav` + `Habitat` can support paper-facing navigation evidence. E008-M123 verified a 295-frame depth-filtered detector-usable subset, E008-M124 verified target-free detector candidate-source generation, E008-M125 passed navmesh/source-readiness validation with 15 / 24 candidates usable for path-smoke, E008-M126 materialized 69 visit-order/path rows with leakage audit pass, E008-M127 observed leakage-safe target-free proxy recovery on 1 case, E008-M128 selected bounded trajectory contract/preflight, E008-M129 generated the runner-compatible trajectory contract with Docker/data/runner preflight pass, E008-M130 executed the one-case target-free detector-policy trajectory smoke, E008-M131 interpreted it, E008-M132 fixed the trajectory-aware repair contract, E008-M133 materialized 225 cost-matrix rows, 75 repair candidate rows, and 5 execution plan rows with leakage audit pass, E008-M134 fixed the repair trajectory runner contract / Docker preflight, E008-M135 executed the one-case repair trajectory smoke, and E008-M136 interpreted the result. M136 rejects scaling the current repair because selected repair `SPL` 0.329622 remains below detector-confidence / confidence-only `SPL` 0.701267, while preserving it as a trajectory-cost diagnostic.
- Current next action: run E008-M137 target-free confidence-preserving trajectory-aware repair contract.
- Current blocked claims: real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, `OldLocationDeadEndCostM` as a primary metric, and human intent as a main claim.
- Current boundary: main experiment implementation 단계이며, paper 폴더는 아직 만들지 않는다.

Detailed experiment state lives in [TODO.md](TODO.md), [experiments/README.md](experiments/README.md), [experiments/E008_real_navigation_benchmark/README.md](experiments/E008_real_navigation_benchmark/README.md), and [docs/reproducibility.md](docs/reproducibility.md).

## 작업 루프

1. `AGENTS.md` -> `README.md` -> `TODO.md` -> `docs/index.md` 순서로 현재 상태를 확인한다.
2. `TODO.md`의 Now/Next에서 실제 다음 행동을 고른다.
3. 작업 유형에 맞는 `docs/` workflow와 가까운 폴더 `README.md`를 읽는다.
4. 문헌조사는 `docs/literature.md`, hypothesis는 `docs/hypothesis.md`, experiment는 `docs/experiments.md`를 따른다.
5. 논문 관련 판단은 `docs/paper.md`, 재현성과 artifact 판단은 `docs/reproducibility.md`를 우선 적용한다.
6. 논문 본문용 experiment는 Docker 기반으로 확정하고, hypothesis-stage smoke test와 paper experiment artifact를 구분한다.
7. 작업 후 가장 가까운 책임 문서에만 세부 내용을 기록하고, 필요한 경우 `TODO.md`의 Now/Next/Completed를 갱신한다.
8. claim-evidence ledger가 채워진 뒤에만 실제 paper draft 폴더를 만든다.

## 연구 기준

좋은 semantic mapping 논문은 단순히 "VLM feature를 3D map에 넣었다"에서 끝나지 않는다. top-tier를 노리려면 다음 중 적어도 하나가 선명해야 한다.

- 새로운 map representation이 기존 방식보다 명확히 더 쓸모 있다.
- 사람의 언어, 의도, 상식, 선호가 map update나 task execution에 실제로 영향을 준다.
- navigation, manipulation, search, instruction following 같은 downstream task에서 성능 차이가 난다.
- 실험이 simulation에만 갇히지 않고 real-world noise, dynamic changes, embodiment gap 중 하나를 정면으로 다룬다.
- 실패 사례와 한계가 논문 안에서 정직하게 다뤄지고, 재현 가능한 코드/데이터/명령으로 뒷받침된다.
