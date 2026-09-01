# Experiments

Updated: 2026-09-01

## Role

이 폴더는 `hypothesis/`에서 충분히 검증돼 `Experiment-ready`가 된
hypothesis의 paper-level 작업만 수행한다.

- Research scoping, topic development와 feasibility studies는 `buildup/`에서 수행한다.
- Focused hypothesis validation은 `hypothesis/`에서 수행한다.
- Scaled benchmark, strong baselines, ablation, robustness, generalization,
  failure analysis와 paper artifacts는 `experiments/`에서 수행한다.

## Active Experiment

없음. 현재 `Experiment-ready` hypothesis가 없다.

새 experiment는 source hypothesis, completed validation evidence와 frozen
pre-outcome contract가 생긴 뒤 Docker-only로 연다. 세부 gate는
`docs/hypothesis.md`와 `docs/experiments.md`를 따른다.

## Experiment Registry

없음.

## Required Handoff

- source hypothesis path와 status
- frozen question, claim/non-claim과 disconfirmation rule
- dataset/split/evaluator, baselines와 metrics
- main experiment contract와 Docker execution path
- unresolved risks와 resource estimate
