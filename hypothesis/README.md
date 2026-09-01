# Hypotheses

Updated: 2026-09-01

## Role

이 폴더는 `buildup/`의 Hypothesis Formulation Entry Criteria를 충족해 선택된
research question을 formal, falsifiable hypothesis로 만들고 focused
validation을 수행하는 유일한 저장 위치다.

- Entry criteria를 충족하지 않은 candidate research question을 이 폴더에
  만들지 않는다.
- Hypothesis의 problem, evidence, studies, baselines, metrics,
  disconfirmation과 decision은 이 폴더에서만 갱신한다.
- 충분히 검증돼 `Experiment-ready`가 된 hypothesis만 `experiments/`로
  넘긴다.

## Active Candidate

없음.

## Active Gate

없음. 현재 research scope가 정해지지 않았으며 `buildup/`에
`ready_for_hypothesis` research question이 없다.

새 candidate를 열 때 source research-question path와 scoping handoff evidence를 반드시
기록한다. 세부 entry와 experiment handoff 기준은 `docs/hypothesis.md`를
따른다.

## Hypothesis Registry

없음.

## Experiments Handoff

Completed falsification evidence, baseline/metric validity, claim/non-claim,
frozen scale-up contract와 Docker path가 준비된 hypothesis만
`experiments/E<number>_<short-title>/`로 승격한다.
