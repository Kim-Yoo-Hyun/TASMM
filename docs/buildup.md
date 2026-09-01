# Research Buildup Workflow

Updated: 2026-09-01

## Purpose

이 문서는 연구 분야를 정한 뒤 완성된 paper idea를 즉시 요구하지 않고,
여러 problem seed를 관찰 가능한 research lead로 성장시키는 pre-hypothesis
workflow를 정의한다.

Buildup은 다음 사이의 독립된 단계다.

```text
user-selected home base
  -> problem seed portfolio
  -> targeted reading and risk-reduction probe
  -> research lead
  -> falsifiable hypothesis
  -> paper-oriented admission
```

- Buildup의 입력은 사용자가 선택한 `home base`다.
- Buildup의 작업 산출물은 모두 루트 `buildup/`에 저장한다.
- Buildup의 출력은 `docs/hypothesis.md`의 entry gate를 만족하는 research lead다.
- Buildup은 exact novelty, final method, full benchmark, paper claim을 확정하는
  단계가 아니다.
- 이 workflow는 `AI`, `ML`, `CV`, `Robotics` 전반에 적용하며
  특정 과거 연구 방향을 기본 연구주제로 가정하지 않는다.

## Scope Boundary

- 사용자가 home base를 제안하기 전에는 특정 task, method family, dataset,
  application, venue 또는 과거 연구 방향을 active scope로 추정하지 않는다.
- public artifact만 허용할지, limited annotation, derived benchmark, original
  data 또는 hardware instrumentation까지 허용할지도 home base와 함께
  별도로 정한다.

## Storage Rule

- Workflow와 template: `docs/buildup.md`
- Active state와 registry: `buildup/README.md`
- Home-base scope, problem cards, reading, probes와 decisions:
  `buildup/<short-home-base>/`
- 작업 계획과 다음 action: `TODO.md`

Buildup 과정은 `buildup/` 안에서만 진행한다. `literature/`, `hypothesis/`,
`experiments/` 또는 `summary.md`에 live buildup payload를 복제하지 않는다.
Home base가 정해지기 전에는 빈 topic folder를 만들지 않는다.

## Evidence Basis

### Source-backed observations

- 신규 연구자는 faculty 또는 senior researcher의 현재 프로젝트에서
  subproblem을 맡고, reading과 group interaction을 거쳐 범위를 구체화할 수
  있다. Stanford CURIS와 KTH Robotics Research Project는 이런
  apprenticeship 경로를 공식적인 연구 시작 방식으로 사용한다.
  [Stanford CURIS](https://curis.stanford.edu/about/),
  [KTH Robotics Research Project](https://www.kth.se/student/kurser/kurs/DD2411/?l=en)
- 독립적인 problem choice에서도 첫 아이디어에 바로 commit하기보다 여러
  아이디어를 비교하고, impact, 성공 가능성, competition/edge, critical
  assumption과 earliest go/no-go test를 검토하는 것이 권장된다.
  [Michael A. Fischbach, *Problem choice and decision trees in science and engineering*](https://doi.org/10.1016/j.cell.2024.03.012)
- 문제 선택에는 feasibility뿐 아니라 연구자가 지속적으로 중요하다고 느낄
  수 있는지가 포함된다. 초기 가정이 무너지는 불확실한 구간과 예상 밖의
  branch는 연구 과정의 일부다.
  [Uri Alon, *How To Choose a Good Scientific Problem*](https://www.weizmann.ac.il/mcb/alon/sites/mcb.UriAlon/files/uploads/nurturing/howtochoosegoodproblem.pdf)
- 초기 proposal은 수정 가능한 범위 합의로 운영할 수 있고, nearest-neighbor
  paper, baseline, critical project risk를 먼저 다룬 뒤 결과에 따라 범위를
  바꿀 수 있다.
  [Stanford CS197C Project Proposal](https://web.stanford.edu/class/cs197c/assignments/project.html)
- 연구 시작 형태는 new method에 한정되지 않는다. 기존 method 개선,
  새로운 문제에 적용, stress test, reimplementation, faculty project의
  subproblem도 연구 seed가 될 수 있다.
  [UT Austin Robot Manipulation and Learning Project](https://www.cs.utexas.edu/~robertom/cs395t_spring2025/project.html),
  [MIT Underactuated Robotics Project](https://underactuated.csail.mit.edu/Spring2024/project.html)

### Agent inference adopted by this workspace

- Topic discovery와 top-tier paper admission을 같은 gate로 처리하면
  preliminary evidence가 생기기 전에 유망한 seed를 제거할 위험이 있다.
- 따라서 buildup에서는 `time-to-information`과 `learning value`를 우선하고,
  exact novelty와 failure-forced method는 evidence가 생긴 뒤 별도 gate에서
  판단한다.
- 한 seed의 실패는 원칙적으로 그 problem card의 kill, narrow 또는 pivot
  근거다. 별도 evidence 없이 home base 전체의 search-stop으로 확대하지
  않는다.

### User decision required

- home base와 그 선택 이유
- 사용할 수 있는 시간, compute, data, annotation, hardware, mentor/contact
- public-only인지 original denominator/data construction도 허용하는지
- 선호하는 problem type과 피하고 싶은 problem type

## Entry Contract

Buildup을 시작하려면 사용자가 최소한 다음을 제안한다.

1. `home base`: problem family, empirical setting, capability, method family,
   application domain 또는 research lineage 중 하나 이상
2. 관심을 유지할 수 있는 이유
3. 명시적으로 제외할 범위
4. resource boundary: 기간, compute, data/annotation/hardware 허용 범위

처음부터 exact question, method, dataset 또는 venue를 모두 고정할 필요는
없다. 한 축을 고정했으면 나머지는 evidence에 따라 움직일 수 있다.

## Stage 1: Build a Research Context Map

Home base가 정해진 뒤 다음을 한 페이지 이내로 정리한다.

- active research communities와 plausible target venues
- 최근 representative work와 현재 lab/project lineage
- 재사용 가능한 code, data, evaluator, compute, expertise
- 반복해서 보고되는 limitation, anomaly, disagreement, missing evaluation
- 접근할 수 없는 자산과 명시적 resource boundary

이 단계의 목표는 exhaustive survey가 아니라 seed가 자랄 환경과 관찰
가능성을 파악하는 것이다. Literature 작업은 `docs/literature.md`의
`Buildup Search`를 따른다.

## Stage 2: Generate a Seed Portfolio

하나의 아이디어에 즉시 commit하지 않고 기본적으로 서로 다른 3--5개
problem seed를 만든다. 다음 출발 형태를 모두 허용한다.

- known method의 unexplained failure 또는 stress condition
- 두 paper의 conflicting result나 evaluation gap
- 새로운 data, measurement, simulator, tool이 열어주는 질문
- 기존 method를 새로운 task/domain에 적용했을 때 생기는 mismatch
- reimplementation에서 관찰된 competence 또는 reproducibility gap
- 현재 연구 프로젝트의 좁은 subproblem
- simple baseline이 예상보다 강하거나 약한 현상

Motivation 문장만 있는 항목은 seed가 아니다. 최소한 관찰할 현상이나
질문이 있어야 한다.

## Problem Card

각 seed는 다음 compact card로 관리한다. 실제 card는
`buildup/<short-home-base>/seeds/<short-seed>.md`에 둔다.

```md
# <Short Seed Title>

## Status
Seed / Shortlisted / Probing / Promoted / Killed / Deferred

## Facts

## Source Claims

## Inference

## Question Or Suspected Phenomenon

## Why It Matters

## Current Practice And Suspected Limitation

## Observable Target

## Accessible Data / Code / Evaluator

## Simplest Baseline Or Counterexample

## Critical Assumptions

## Smallest Risk-Reduction Test

## What Failure Teaches

## Resource Estimate

## Prior-Ownership Risk

## User Decision Needed
```

`Facts`, `Source Claims`, `Inference`, `User Decision Needed`를 서로 섞지
않는다.

## Stage 3: Compare Before Committing

각 card를 절대적인 pass/fail이 아니라 같은 portfolio 안에서 비교한다.
각 축은 `low / medium / high`와 한 줄 근거로 기록한다.

| Axis | Question |
| --- | --- |
| importance | 성공하면 누가 무엇을 다르게 이해하거나 할 수 있는가? |
| observability | 핵심 현상을 현재 resource boundary에서 측정할 수 있는가? |
| time-to-information | 1--2주 안에 중요한 가정 하나를 줄일 수 있는가? |
| learning value | 결과가 어느 쪽이어도 다음 branch를 결정할 수 있는가? |
| edge | 보유한 data, code, expertise, access 또는 viewpoint가 있는가? |
| research depth | 단발성 engineering fix를 넘어 원리 질문으로 발전할 여지가 있는가? |
| prior risk | nearest prior가 질문과 예상 insight를 이미 소유할 가능성은 어떤가? |
| scale path | 초기 probe 뒤 rigorous evaluation으로 확장할 현실적인 경로가 있는가? |

상위 1--2개만 targeted reading과 probe로 보낸다. 이 시점의 `prior risk`는
조사 우선순위이며 exact novelty의 최종 판정이 아니다.

## Stage 4: Targeted Nearest-Neighbor Reading

Shortlisted seed마다 다음을 확인한다.

1. 가장 가까운 primary paper 1--3개
2. 그 paper가 해결한 정확한 question과 남긴 boundary
3. official code/data/evaluator의 실제 접근 가능성
4. 가장 단순한 baseline과 strongest adjacent baseline
5. seed가 prior와 달라지는 최소 단위
6. novelty가 아니라 먼저 확인해야 할 empirical uncertainty

Broad survey를 완성할 때까지 probe를 미루지 않는다. 반대로 search
snippet이나 survey만으로 prior ownership을 확정하지 않는다.

## Stage 5: Assumption And Decision Tree

각 shortlisted seed에 대해 다음 decision tree를 작성한다.

```text
critical assumption
  ├─ supported -> 다음으로 줄여야 할 risk
  ├─ contradicted -> kill 또는 problem reformulation
  └─ ambiguous -> 더 싼 measurement 또는 scope reduction
```

Assumption마다 다음을 기록한다.

- 왜 필요한가
- 현재 evidence
- 틀렸음을 보여주는 결과
- 확인 비용과 예상 시간
- 먼저 검사할 수 있는 더 싼 proxy

## Stage 6: Risk-Reduction Probe

Probe의 목적은 method 성능을 과시하는 것이 아니라 가장 위험한 가정
하나를 빠르게 줄이는 것이다. 허용되는 예시는 다음과 같다.

- official baseline의 최소 재현
- dataset/schema/evaluator audit
- small subset 또는 synthetic perturbation
- simple baseline과의 competence check
- one-case counterexample 또는 failure taxonomy
- expected plot/table의 최소 버전

External method의 실행, reproduction, adapter, smoke test와 evaluation은
`AGENTS.md`의 Docker-only rule을 따른다. 실행 전 command, input, output,
metric, disconfirmation rule을 고정한다.

## Stage 7: Review And Branch

Probe 뒤에는 다음 중 하나만 선택하고 근거를 기록한다.

- `kill`: 핵심 현상이 없거나 authorized scope에서 관찰할 수 없다.
- `narrow`: 현상은 있으나 더 작은 population/condition이 필요하다.
- `pivot`: 가정은 틀렸지만 다른 explanation이나 question이 드러났다.
- `repeat`: measurement가 불충분하며 더 싼 확인 방법이 남아 있다.
- `promote`: falsifiable hypothesis로 압축할 evidence가 생겼다. Card status를
  `promoted`로 바꾸고 hypothesis handoff를 기록한다.

Outcome에 맞춰 threshold, denominator 또는 metric을 사후 변경해 seed를
구제하지 않는다. 변경이 필요하면 새 card 또는 명시적인 card revision으로
기록한다.

## Handoff To Hypothesis

Research lead는 다음 조건을 모두 만족할 때만
`hypothesis/CAND-<number>/`로 넘긴다.

1. problem 또는 phenomenon을 한 문장으로 설명할 수 있다.
2. facts와 source claims가 suspected explanation과 분리돼 있다.
3. accessible probe, dataset, benchmark 또는 evaluator가 하나 이상 있다.
4. simplest relevant baseline 또는 counterexample이 정의돼 있다.
5. critical assumption과 disconfirmation result가 정의돼 있다.
6. 작은 probe의 결과 또는 probe 가능성 audit가 기록돼 있다.
7. 실패가 가르치는 다음 branch가 명확하다.
8. intervention, expected measurable effect, evaluation target을 가진 draft
   hypothesis를 만들 수 있다.

다음은 handoff 필수조건이 아니다.

- final method architecture
- complete exact-prior survey
- publication-ready novelty sentence
- full-scale benchmark result
- second-domain generalization
- failure-forced method principle
- paper folder 또는 target deadline

이 항목들은 `hypothesis/`의 focused validation과, 그 gate를 통과한 뒤
`experiments/`의 paper-level 작업에서 점진적으로 요구한다.

## Stop Rules

- authorized resource boundary 안에 observable target이 없다.
- critical assumption이 반증되고 유의미한 pivot branch도 없다.
- simplest baseline이 suspected phenomenon을 충분히 설명한다.
- exact prior가 동일한 question과 insight를 이미 소유하고 남는 branch가 없다.
- time-to-information이 석사 연구 범위를 넘고 더 작은 proxy가 없다.

Stop은 해당 card에 적용한다. Home base 전체를 중단하려면 서로 독립적인
여러 route의 evidence와 별도의 synthesis가 필요하다.

## Hypothesis And Paper-Level Boundary

Research lead 또는 좋은 preliminary result가 곧 contribution은 아니다.
먼저 `hypothesis/`에서 falsification과 focused validation을 수행한다. 그
hypothesis가 `docs/hypothesis.md`의 experiment-ready gate를 통과한 뒤에만
`experiments/`에서 다음 paper-level evidence를 만든다.

- exact novelty와 nearest-prior residue
- simple-baseline-resistant phenomenon
- failure diagnosis에서 도출되는 principle과 method necessity
- benchmark rigor, ablation, robustness, failure analysis
- generality와 reproducibility

Project selection을 위한 질문 정리에는
[DARPA Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism)을
참고할 수 있지만, 그 질문을 모든 early seed의 admission gate로 사용하지
않는다.

## Update Rules

- 현재 home base와 active seed queue: `buildup/README.md`와
  `buildup/<short-home-base>/README.md`
- durable process와 template: 이 문서
- buildup reading, problem card와 probe: `buildup/`
- promoted candidate와 focused validation: `hypothesis/`
- paper-level scale-up과 experiment evidence: `experiments/`
- 계획과 다음 action: `TODO.md`

Live result, literature payload와 probe log는 이 문서에 누적하지 않는다.
