# Hypotheses

Updated: 2026-09-01

## Role

이 폴더는 `buildup/` gate를 통과한 research lead를 falsifiable hypothesis로
만들고 focused validation을 수행하는 유일한 저장 위치다.

- 완료되지 않은 buildup seed를 이 폴더에 만들지 않는다.
- Hypothesis의 problem, evidence, probes, baselines, metrics,
  disconfirmation과 decision은 이 폴더에서만 갱신한다.
- 충분히 검증돼 `Experiment-ready`가 된 hypothesis만 `experiments/`로
  넘긴다.

## Active Candidate

없음.

## Active Gate

없음. 현재는 `pre-buildup`이며 `buildup/`에 promoted research lead가 없다.

새 candidate를 열 때 source buildup path와 handoff evidence를 반드시
기록한다. 세부 entry와 experiment handoff 기준은 `docs/hypothesis.md`를
따른다.

## Hypothesis Registry

없음.

## Experiments Handoff

Completed falsification evidence, baseline/metric validity, claim/non-claim,
frozen scale-up contract와 Docker path가 준비된 hypothesis만
`experiments/E<number>_<short-title>/`로 승격한다.
