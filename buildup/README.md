# Research Scoping and Topic Development

Updated: 2026-09-01

## Purpose

이 폴더는 research scope를 정하고 candidate research questions를 비교해
formal hypothesis로 발전시킬 질문을 선택하는 작업의 유일한 저장 위치다.
`buildup/`은 repository 경로명이며, 연구 문서에서는 `Research Scoping and
Topic Development`를 stage 명칭으로 사용한다.

- Stable workflow와 entry criteria: `docs/buildup.md`
- Research scope, candidate questions, preliminary literature review,
  feasibility/pilot studies와 selection decision: `buildup/`
- 선택된 research question의 hypothesis formulation과 focused validation:
  `hypothesis/`
- 충분히 검증된 hypothesis의 paper-level evaluation: `experiments/`

`docs/buildup.md`에는 절차만 기록한다. 현재 scope, 조사 결과, feasibility
evidence와 selection decision은 이 폴더 밖에 중복하지 않는다.

## Basis In Official Research Guidance

공식 지침마다 형식은 다르지만 다음 요소가 반복된다.

- Research problem, significance, prior work, preliminary work와 remaining
  timeline:
  [Stanford CS Thesis Proposal](https://www.cs.stanford.edu/phd-program-requirements-thesis-proposal)
- Objective, current practice and limitations, expected impact, risks, cost,
  duration과 success criteria:
  [DARPA Heilmeier Catechism](https://www.darpa.mil/about/heilmeier-catechism)
- Project role, motivation, goals, expectations와 realistic planning:
  [MIT UROP Project Planning](https://urop.mit.edu/mentors/resources/project-planning/),
  [MIT UROP Students](https://urop.mit.edu/students/)
- Scope, deliverables, related work와 progress milestones:
  [MIT Underactuated Robotics Project](https://underactuated.csail.mit.edu/Spring2024/project.html)
- Research question, related work, methodology와 evaluation plan:
  [Stanford CS197C Project Proposal](https://web.stanford.edu/class/cs197c/assignments/project.html)

따라서 이 workspace는 `home base`, `seed`, `probe`, `promotion` 같은 내부
표현 대신 `research scope`, `candidate research question`,
`feasibility/pilot study`, `selection for hypothesis formulation`을 사용한다.

## Current State

- Research scope: `pending_user_decision`
- Candidate research questions: 없음
- Question selected for hypothesis formulation: 없음

사용자가 research scope와 resource constraints를 정하기 전에는 하위 scope
folder를 만들거나 특정 연구 분야를 active scope로 간주하지 않는다.

## Stage Flow

```text
buildup/
  research scope and constraints
  -> candidate research questions
  -> preliminary literature review
  -> feasibility or pilot study
  -> question selection
    ↓ Hypothesis Formulation Entry Criteria 통과
hypothesis/
  formal hypothesis and focused validation
    ↓ Experiment Handoff Gate 통과
experiments/
  paper-level evaluation and reproducible evidence
```

Stage를 건너뛰지 않는다. Entry criteria를 충족하지 않은 candidate question을
`hypothesis/`에 만들지 않고, 충분히 검증되지 않은 hypothesis를
`experiments/`로 넘기지 않는다.

## Folder Convention

Research scope가 정해진 뒤 필요한 항목만 만든다.

```text
buildup/
  README.md
  <short-scope>/
    README.md
    questions/
      <short-question>.md
    related_work/
    pilot_studies/
```

- Scope `README.md`가 research area, significance, resource constraints,
  available time, expected research output, candidate-question registry와
  current decision의 authoritative owner다.
- `questions/`에는 candidate research question record를 둔다.
- `related_work/`에는 question selection과 prior-work overlap 판단에 직접
  필요한 preliminary literature review를 둔다.
- `pilot_studies/`에는 feasibility/pilot study의 protocol, success criteria,
  milestones와 result를 둔다.
- 빈 하위 folder는 미리 만들지 않는다.

## Hypothesis Formulation Entry Criteria

`docs/buildup.md`의 `Entry To Hypothesis Formulation` 조건을 모두 만족한
research question만 `hypothesis/`로 넘긴다. 이 README에는 selection result,
source question record, target hypothesis directory와 selection date만 registry로
남긴다.

선택할 때 `hypothesis/CAND-<number>/`를 만들고 source scope, candidate
question과 feasibility evidence를 기록한다. 이후 hypothesis와 validation
result는 `hypothesis/`에서만 갱신하며, source record는 provenance로 동결한다.

## Status Values

- `exploratory`: preliminary research question
- `under_review`: comparative review와 preliminary literature review 진행 중
- `feasibility_study`: feasibility 또는 pilot study 진행 중
- `ready_for_hypothesis`: hypothesis formulation entry criteria 통과
- `discontinued`: question 또는 observed phenomenon을 더 진행하지 않음
- `deferred`: resource, evidence 또는 user decision을 기다림

현재 research scope, question registry와 바로 다음 action은 이 README와
`TODO.md`에 짧게 반영한다.
