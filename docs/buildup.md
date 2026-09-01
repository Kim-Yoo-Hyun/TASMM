# Research Scoping and Topic Development Workflow

Updated: 2026-09-01

## Purpose

이 문서는 broad research interest를 명시적인 research scope로 정리하고,
여러 candidate research questions를 preliminary evidence로 비교해 formal
hypothesis로 발전시킬 질문을 선택하는 workflow를 정의한다.

`buildup/`은 repository 경로명이다. 연구 단계와 산출물에는 다음 academic
terminology를 사용한다.

```text
research scope and constraints
  -> candidate research questions
  -> preliminary literature review
  -> feasibility or pilot study
  -> question selected for hypothesis formulation
  -> formal hypothesis and focused validation
```

이 단계에서는 exact novelty, final method, full benchmark 또는 paper claim을
확정하지 않는다. Observable research question, empirical accessibility,
resource feasibility와 informational value를 먼저 판단한다.

## Scope Boundary

- 사용자가 research scope를 정하기 전에는 특정 task, method family,
  dataset, application 또는 venue를 active scope로 추정하지 않는다.
- Public artifact만 사용할지, limited annotation, derived benchmark, original
  data 또는 hardware instrumentation까지 허용할지는 resource constraints에
  명시한다.
- Method나 dataset 하나를 research scope 자체로 간주하지 않는다. 해당
  method/data가 어떤 research problem family를 조사하게 하는지 설명한다.

## Storage Rule

- Stable workflow와 template: `docs/buildup.md`
- Current state와 question registry: `buildup/README.md`
- Scope, candidate questions, related work와 feasibility evidence:
  `buildup/<short-scope>/`
- Plan, status와 next action: `TODO.md`

Research Scoping and Topic Development의 live payload는 `buildup/` 안에서만
관리한다. `literature/`, `hypothesis/`, `experiments/` 또는 `summary.md`에
중복하지 않는다. Research scope가 정해지기 전에는 빈 scope folder를 만들지
않는다.

## Entry Requirements

이 stage를 시작하려면 사용자가 최소한 다음을 정한다.

1. `research area or problem family`
2. `motivation and expected significance`
3. `relevant experience, resources, and access`
4. `data, compute, annotation, and hardware constraints`
5. `explicitly excluded scope`
6. `available research time`

Exact research question, method, dataset와 venue를 모두 고정할 필요는 없다.
Research scope는 preliminary evidence와 feasibility 결과에 따라 수정할 수
있다.

## Stage 1: Research Context

Research scope가 정해진 뒤 다음을 한 페이지 이내로 정리한다.

- research area와 expected significance
- active research communities와 plausible target venues
- representative recent work와 relevant research groups
- available code, data, evaluator, compute와 expertise
- 반복해서 보고되는 limitation, anomaly, disagreement와 missing evaluation
- unavailable resources와 explicit constraints

목표는 exhaustive survey가 아니라 candidate question을 만들 수 있는 research
context와 empirical access를 파악하는 것이다. Literature review는
`docs/literature.md`의 `Scoping Literature Review`를 따른다.

## Stage 2: Candidate Research Questions

첫 질문 하나에 즉시 commit하지 않고, 기본적으로 서로 다른 candidate
research questions 3--5개를 작성한다. 질문은 다음 관찰에서 시작할 수 있다.

- known method의 unexplained failure 또는 stress condition
- papers 사이의 conflicting result 또는 evaluation gap
- 새로운 data, measurement, simulator 또는 tool이 가능하게 한 question
- 기존 method를 새로운 task/domain에 적용했을 때의 mismatch
- reimplementation에서 관찰된 competence 또는 reproducibility gap
- current research program의 well-defined subproblem
- simple baseline이 예상보다 강하거나 약한 empirical result

Motivation만 있는 항목은 candidate research question이 아니다. 최소한
observed or suspected phenomenon과 evaluation target이 있어야 한다.

## Candidate Research Question Record

각 질문은 다음 형식으로
`buildup/<short-scope>/questions/<short-question>.md`에 기록한다.

```md
# <Short Research Question>

## Status
Exploratory / Under Review / Feasibility Study / Ready for Hypothesis / Discontinued / Deferred

## Facts

## Source Claims

## Agent Inference

## Research Question Or Suspected Phenomenon

## Significance

## Current State Of The Art And Limitation

## Evaluation Target

## Available Data / Code / Evaluator

## Simplest Baseline Or Counterexample

## Critical Assumptions

## Feasibility Or Pilot Study

## Preliminary Success Criteria

## Expected Deliverable

## Timeline And Milestones

## Interpretation Of A Negative Result

## Resource Requirements

## Related-Work Overlap

## User Decision Needed
```

`Facts`, `Source Claims`, `Agent Inference`, `User Decision Needed`를 서로
섞지 않는다.

## Stage 3: Comparative Assessment

Candidate questions를 독립적인 pass/fail로 처리하지 않고 같은 set 안에서
비교한다. 각 기준을 `low / medium / high`와 한 줄 evidence로 기록한다.

| Criterion | Assessment question |
| --- | --- |
| significance | 성공하면 어떤 scientific understanding 또는 capability가 달라지는가? |
| empirical accessibility | 현재 constraints 안에서 phenomenon을 관찰하고 측정할 수 있는가? |
| feasibility | 사용 가능한 기간 안에 중요한 uncertainty를 줄일 수 있는가? |
| informational value | 결과가 어느 쪽이어도 다음 research decision에 정보를 주는가? |
| resource fit | available data, code, compute, expertise와 access에 맞는가? |
| scientific depth | 단발성 engineering fix를 넘어 generalizable question으로 발전할 수 있는가? |
| related-work overlap | nearest prior가 question과 expected insight를 이미 다뤘을 가능성은 어떤가? |
| rigorous evaluation path | preliminary study 뒤 controlled evaluation으로 확장할 수 있는가? |

상위 1--2개 question만 preliminary literature review와 feasibility study로
보낸다. 이 단계의 related-work overlap은 review priority이며 exact novelty의
최종 판정이 아니다.

## Stage 4: Preliminary Literature Review

선택된 candidate question마다 다음을 확인한다.

1. nearest primary papers 1--3개
2. 각 paper의 exact research question, claimed contribution과 boundary
3. official code, data와 evaluator의 실제 접근 가능성
4. simplest baseline과 strongest adjacent baseline
5. candidate question과 prior work의 최소 차이
6. novelty 주장 전에 확인해야 할 empirical uncertainty

Broad survey 완료를 feasibility study의 선행조건으로 삼지 않는다. 반대로
search snippet이나 secondary survey만으로 prior-work overlap을 확정하지
않는다.

## Stage 5: Assumptions And Research Risks

각 candidate question에 critical assumptions와 decision branches를 기록한다.

```text
critical assumption
  ├─ supported -> next unresolved research risk
  ├─ contradicted -> discontinue or reformulate the question
  └─ ambiguous -> cheaper measurement or narrower scope
```

각 assumption에는 다음을 포함한다.

- scientific or operational necessity
- current supporting evidence
- disconfirming observation
- expected cost and duration
- cheaper proxy measurement, if available

## Stage 6: Feasibility Or Pilot Study

Feasibility/pilot study의 목적은 method 성능을 과시하는 것이 아니라 가장
중요한 uncertainty 하나를 줄이고 본 연구의 실행 가능성을 판단하는 것이다.

가능한 study 형태:

- official baseline의 minimal reproduction
- dataset, schema 또는 evaluator audit
- small subset 또는 synthetic perturbation
- simple-baseline competence check
- one-case counterexample 또는 preliminary failure classification
- expected paper plot/table의 minimal version

External method의 reproduction, adapter, smoke test와 evaluation은
`AGENTS.md`의 Docker-only rule을 따른다. 실행 전 research question, input,
output, metric, success criteria, milestone과 disconfirmation rule을 고정한다.

## Stage 7: Selection Decision

Preliminary evidence를 검토한 뒤 다음 중 하나를 선택하고 근거를 기록한다.

- `discontinue`: phenomenon이 없거나 authorized scope에서 관찰할 수 없다.
- `refine`: 더 좁은 population, condition 또는 formulation이 필요하다.
- `reformulate`: initial assumption은 틀렸지만 새로운 explanation이나
  research question이 드러났다.
- `repeat feasibility study`: measurement validity가 불충분하며 더 적절한
  low-cost study가 남아 있다.
- `select for hypothesis formulation`: formal falsifiable hypothesis를 작성할
  evidence가 생겼다. Status를 `ready_for_hypothesis`로 바꾼다.

Outcome에 맞춰 threshold, denominator 또는 metric을 사후 변경해 question을
유지하지 않는다. 변경이 필요하면 explicit revision 또는 새로운 candidate
question으로 기록한다.

## Entry To Hypothesis Formulation

Candidate research question은 다음 조건을 모두 만족할 때만
`hypothesis/CAND-<number>/`로 넘긴다.

1. Research problem 또는 phenomenon을 한 문장으로 설명할 수 있다.
2. Facts와 source claims가 proposed explanation과 분리돼 있다.
3. Accessible data, benchmark, evaluator 또는 study design이 하나 이상 있다.
4. Simplest relevant baseline 또는 counterexample이 정의돼 있다.
5. Critical assumption과 disconfirming observation이 정의돼 있다.
6. Feasibility/pilot evidence 또는 documented feasibility assessment가 있다.
7. Negative result가 의미하는 다음 research decision이 명확하다.
8. Intervention, expected measurable effect와 evaluation target을 포함하는
   draft hypothesis를 작성할 수 있다.

다음은 이 entry의 필수조건이 아니다.

- final method architecture
- complete exact-prior survey
- publication-ready novelty statement
- full-scale benchmark result
- multi-domain generalization
- failure-derived method principle
- paper folder 또는 target deadline

이 항목들은 `hypothesis/`의 focused validation과, 그 criteria를 통과한 뒤
`experiments/`의 paper-level work에서 점진적으로 요구한다.

## Discontinuation Criteria

- Authorized constraints 안에 observable evaluation target이 없다.
- Critical assumption이 반증되고 meaningful reformulation도 없다.
- Simplest baseline이 suspected phenomenon을 충분히 설명한다.
- Exact prior가 동일한 question과 insight를 이미 소유하고 남는 question이
  없다.
- Feasibility가 석사 연구 범위를 넘고 informative proxy study가 없다.

Discontinuation은 해당 candidate question에 적용한다. Research scope 전체를
중단하려면 여러 independent questions의 evidence와 별도 synthesis가 필요하다.

## Hypothesis And Paper-Level Boundary

Selected research question 또는 encouraging preliminary result가 곧 paper
contribution은 아니다. 먼저 `hypothesis/`에서 formal hypothesis formulation과
focused validation을 수행한다. Hypothesis가 `docs/hypothesis.md`의 Experiment
Handoff Gate를 통과한 뒤에만 `experiments/`에서 다음 evidence를 만든다.

- exact novelty와 nearest-prior residue
- simple-baseline-resistant phenomenon
- failure analysis에서 도출되는 principle과 method necessity
- benchmark rigor, ablation, robustness와 failure analysis
- generalization과 reproducibility

## Update Rules

- Current research scope와 candidate-question registry:
  `buildup/README.md`, `buildup/<short-scope>/README.md`
- Stable process와 template: 이 문서
- Preliminary literature review: `buildup/<short-scope>/related_work/`
- Feasibility/pilot evidence: `buildup/<short-scope>/pilot_studies/`
- Selected question과 formal hypothesis: `hypothesis/`
- Paper-level evaluation: `experiments/`
- Plan과 next action: `TODO.md`

Live result, literature payload와 study log는 이 문서에 누적하지 않는다.
