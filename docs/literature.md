# Literature Workflow

Updated: 2026-09-01

## Purpose

문헌 조사는 motivation을 수집하는 작업이 아니라 problem ownership, executable denominator, simple-baseline pressure와 forced method boundary를 판정하는 작업이다.

## Start Condition

N28의 re-entry trigger 또는 사용자가 승인한 새 scope가 없으면 broad survey를 열지 않는다.

Search를 열 때는 먼저 다음을 한 문장씩 고정한다.

1. existing limitation
2. 왜 robotics/3D vision problem인가
3. public artifact와 evaluator
4. 가장 단순한 세 controls
5. 실패하면 무엇을 배우는가

## Search Order

1. Official benchmark/data/code로 executable denominator를 확인한다.
2. 2024--2026 exact problem/principle prior를 확인한다.
3. Task/scene prior, geometry/trajectory/history, threshold/state-conditioned control을 먼저 정의한다.
4. 같은 label/metric을 가진 second-domain path를 확인한다.
5. Residual이 특정 representation/inference/control form을 강제하는지 판정한다.
6. 위 조건이 남을 때만 one-week no-outcome contract를 쓴다.

## Evidence Labels

문서에서 다음을 분리한다.

- 사실: source, schema, released artifact, measured result
- 논문 주장: 저자가 paper에서 주장한 범위
- 에이전트 추론: source를 바탕으로 한 novelty/feasibility 판단
- 사용자 판단 필요: scope, resource 또는 irreversible choice

## Source Rules

- PaperReview나 survey는 discovery source로만 사용한다.
- Novelty와 artifact readiness는 primary paper, appendix, official code/data에서 재검증한다.
- Latest result가 중요한 경우 web search로 current source를 확인한다.
- Paper title, method, dataset, metric, benchmark 이름은 English original을 유지한다.

## Output

- Cross-paper synthesis와 current boundary: `literature/README.md`
- Candidate-specific audit: `literature/<short-topic>-<gate>-<YYYY-MM>.md`
- Paper folders와 registry는 active search가 실제로 필요할 때만 만든다.
- Killed route의 source/artifact는 active surface에 누적하지 않고 retired archive로 이동한다.

## Admission Rule

모두 통과해야 candidate를 만든다.

1. public executable denominator
2. unoccupied exact problem/principle
3. residual after at least three simple controls
4. one-week decisive kill path
5. credible second-domain route
6. failure-derived, non-substitutable method principle

Threshold나 denominator를 outcome 뒤에 바꿔 claim을 구제하지 않는다.
