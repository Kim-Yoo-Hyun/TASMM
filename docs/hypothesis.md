# Hypothesis Workflow

이 문서는 연구 후보를 검증 가능한 hypothesis로 바꾸는 에이전트 workflow와 작성 규칙을 정의한다. 실제 hypothesis 내용은 루트의 `hypothesis/` 폴더에 저장한다.

## Storage Rule

Hypothesis 관련 산출물은 루트의 `hypothesis/` 폴더에 저장한다.

- workflow와 작성 규칙: `docs/hypothesis.md`
- hypothesis index: `hypothesis/README.md`
- candidate별 hypothesis 묶음: `hypothesis/CAND-<number>/`
- 개별 hypothesis: `hypothesis/CAND-<number>/H<number>_<short-title>/`
- 작업 계획과 진행 상태: `TODO.md`

`docs/hypothesis.md`는 절차와 기준만 관리한다. 문제 정의, hypothesis, feasibility gate, first experiment shape는 `hypothesis/` 아래에 기록한다.

## Entry Context

Hypothesis 작업을 시작하는 에이전트는 아래 순서로 읽는다.

1. `AGENTS.md`
2. `README.md`
3. `TODO.md`
4. `docs/index.md`
5. `docs/literature.md`
6. `docs/hypothesis.md`
7. `literature/CAND-001.md`
8. `hypothesis/README.md`
9. 대상 hypothesis 폴더의 `README.md`

## Phase Gate

Hypothesis 단계로 넘어간다는 뜻은 thesis direction을 확정한다는 뜻이 아니다. 다음 조건을 만족하는지 검증 가능한 문장으로 압축하는 단계다.

- 기존 한계가 primary source로 뒷받침된다.
- 왜 semantic mapping 문제인지 설명된다.
- dataset / benchmark / metric / baseline 후보가 있다.
- 실패했을 때 배울 수 있는 것이 명확하다.
- 첫 실험이 석사 연구 범위에서 실행 가능하다.

## Scope Rule

Hypothesis 단계는 full reproduction이나 full dataset 검증 단계가 아니다. 이 단계의 목표는 논문으로 발전할 가능성이 있는지 빠르게 확인하는 것이다.

- full dataset 사용을 요구하지 않는다.
- 기존 논문 전체 재현을 요구하지 않는다.
- 작은 subset, one-scene replay, before/after probe, synthetic perturbation을 허용한다.
- 단, metric, baseline, failure interpretation은 반드시 있어야 한다.
- 논문으로서의 가치 검증이 충분히 완료되기 전에는 `docs/experiments.md`로 넘어가지 않는다.
- Hypothesis 단계의 probe 설계, dataset/replay 접근성 판단, baseline 후보, metric 정의는 모두 `hypothesis/` 아래에 기록한다.
- 좋은 결과가 나오고 논문 발전 가능성이 확인되면 그때 `docs/experiments.md`에서 full experiment contract로 승격한다.
- 나쁜 결과가 나오면 왜 안 되는지 기록하고 candidate를 수정하거나 보류한다.

## Hypothesis Folder Convention

```text
hypothesis/
  README.md
  CAND-001/
    README.md
    H001_<short-title>/
      README.md
      01_problem.md
      02_hypothesis.md
      03_feasibility.md
      04_first_experiment.md
```

폴더명 규칙:

- candidate folder는 `CAND-<number>`를 사용한다.
- hypothesis folder는 `H<number>_<short-title>`을 사용한다.
- short title은 짧고 핵심 단어 중심으로 쓴다.
- 아직 hypothesis가 확정되지 않았으면 빈 `H<number>_...` 폴더를 만들지 않는다.

## File Roles

### `hypothesis/README.md`

전체 hypothesis index를 관리한다.

```md
# Hypotheses

## Active Candidate

## Hypothesis Registry

## Promotion Criteria

## Deferred Candidates
```

### `hypothesis/CAND-<number>/README.md`

candidate별 hypothesis 후보 묶음을 관리한다.

```md
# CAND-<number>

## Candidate Summary

## Source Literature

## Hypothesis Queue

## Current Gate
```

### `H<number>_<short-title>/README.md`

개별 hypothesis의 첫 진입점이다.

```md
# H<number>: <Short Title>

## Hypothesis

## Why This Is Testable

## First Experiment

## Current Status
```

## Writing Rules

- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 구분한다.
- hypothesis는 한 문장으로 쓴다.
- hypothesis에는 intervention, expected effect, evaluation target이 들어가야 한다.
- "좋아질 것이다"처럼 막연하게 쓰지 않는다.
- metric이 없는 hypothesis는 아직 hypothesis가 아니다.
- baseline이 없는 hypothesis는 아직 experiment-ready가 아니다.
- 구현 아이디어보다 first falsification path를 먼저 쓴다.

## Hypothesis Template

```md
# H<number>: <Short Title>

## Status

Draft / Candidate / Experiment-ready / Deferred

## Facts

## Paper Claims

## Inferences

## Hypothesis

If <intervention>, then <expected measurable effect> on <task/benchmark>, compared with <baseline>.

## Why This Is Semantic Mapping

## Dataset / Benchmark

## Metrics

## Baselines

## First Experiment Shape

## What Failure Teaches

## User Decision Needed
```

## Promotion Criteria

Draft hypothesis를 experiment-ready로 올리려면 다음을 만족해야 한다.

- 최소 6개 primary source와 연결된다.
- benchmark 또는 small probe 후보가 1개 이상 있고 접근 가능성을 판단했다.
- metric 2개 이상이 있다. 하나는 map quality, 하나는 task behavior와 연결한다.
- baseline 2개 이상이 있다.
- 실패 시 해석이 최소 2갈래 이상으로 나뉜다.
- hypothesis 폴더 안에서 first probe contract와 가치 판단 기준이 작성되어 있다.
- 논문으로서의 가치 검증이 끝난 뒤 `docs/experiments.md`로 옮길 수 있다.
