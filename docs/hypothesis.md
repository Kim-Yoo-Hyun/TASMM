# Hypothesis Workflow

Updated: 2026-09-01

이 문서는 `docs/buildup.md`에서 선택된 research question을 formal,
falsifiable hypothesis로 바꾸는 에이전트 workflow와 작성 규칙을 정의한다. 실제
hypothesis 내용은 루트의 `hypothesis/` 폴더에 저장한다.

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
5. `docs/buildup.md`
6. `buildup/README.md`
7. selected research question의 research-scope README, question record와
   feasibility/pilot evidence
8. `docs/hypothesis.md`
9. `hypothesis/README.md`
10. 대상 hypothesis 폴더의 `README.md`

## Research Scoping Handoff

Hypothesis workflow는 주제를 처음 생성하는 단계가 아니다. 다음 조건을
만족해 `buildup/README.md`와 source question record에서
`ready_for_hypothesis`로 확정된 research question만 받는다.

- `docs/buildup.md`의 `Entry To Hypothesis Formulation` criteria가 모두
  충족돼 있다.
- Source research-scope README, question record와 feasibility/pilot evidence
  path가 기록돼 있다.
- Selection decision, unresolved research risk와 draft hypothesis가 handoff record에
  포함돼 있다.

Handoff 시 exact novelty, final method, full benchmark, second-domain evidence,
failure-forced method principle은 필수조건이 아니다. 이들은 hypothesis
evidence가 쌓이면서 검토한다. 충분히 검증된 뒤에만 `experiments/`로
승격하고 paper-level evidence에는 `docs/paper.md`를 적용한다.

## Phase Gate

Hypothesis 단계로 넘어간다는 뜻은 thesis direction을 확정한다는 뜻이 아니다. 다음 조건을 만족하는지 검증 가능한 문장으로 압축하는 단계다.

- 기존 한계가 primary source로 뒷받침된다.
- 선택된 research area에서 왜 중요한 문제인지 설명된다.
- dataset, benchmark, evaluator 또는 small study와 metric/baseline 후보가 있다.
- 실패했을 때 배울 수 있는 것이 명확하다.
- 첫 실험이 석사 연구 범위에서 실행 가능하다.

## Scope Rule

Hypothesis 단계는 full reproduction이나 full dataset 검증 단계가 아니다. 이 단계의 목표는 논문으로 발전할 가능성이 있는지 빠르게 확인하는 것이다.

- full dataset 사용을 요구하지 않는다.
- 기존 논문 전체 재현을 요구하지 않는다.
- 작은 subset, one-case replay, before/after study, synthetic perturbation을 허용한다.
- Research area에 따라 simulation, analytical test, controlled data slice,
  human evaluation 또는 hardware study를 사용할 수 있다. 단, 사용자 승인
  resource boundary를 넘지 않는다.
- 단, metric, baseline, failure interpretation은 반드시 있어야 한다.
- Hypothesis가 충분히 검증되기 전에는 `experiments/`로 넘어가지 않는다.
- Hypothesis 단계의 study design, dataset/replay 접근성 판단, baseline 후보, metric 정의는 모두 `hypothesis/` 아래에 기록한다.
- 좋은 결과 하나만으로 승격하지 않는다. 핵심 assumption, baseline threat,
  leakage/competence risk와 disconfirmation branch를 함께 검증한다.
- Experiment-ready gate를 통과하면 `docs/experiments.md`에 따라
  `experiments/`에서 paper-level work를 시작한다.
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

## Experiment Handoff Criteria

## Deferred Candidates
```

### `hypothesis/CAND-<number>/README.md`

candidate별 hypothesis 후보 묶음을 관리한다.

```md
# CAND-<number>

## Candidate Summary

## Research Scoping Handoff

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

Draft / Validating / Experiment-ready / Deferred / Discontinued

## Facts

## Paper Claims

## Inferences

## Research Scoping Handoff

## Hypothesis

If <intervention>, then <expected measurable effect> on <task/benchmark>, compared with <baseline>.

## Research Relevance

## Dataset / Benchmark / Evaluator / Study Design

## Metrics

## Baselines

## First Experiment Shape

## What Failure Teaches

## User Decision Needed
```

## Experiment Handoff Gate

Hypothesis를 `Experiment-ready`로 올려 `experiments/`에 넘기려면 다음을 모두
만족해야 한다.

- Source research-question path와 scoping handoff evidence가 기록돼 있다.
- 최소 6개 primary source와 연결된다.
- Nearest prior와 남는 problem/claim boundary가 구분돼 있다.
- 접근 가능한 benchmark 또는 study에서 최소 하나의 completed falsification
  result가 있다.
- metric 2개 이상이 있다. 하나는 primary quality/performance를 측정하고,
  다른 하나는 behavior, robustness, efficiency, cost 또는 failure severity처럼
  claim의 실제 consequence를 측정한다.
- baseline 2개 이상이 있다.
- Simplest baseline이 현상을 전부 설명하는지 검사했고, competence와
  leakage/evaluator validity를 확인했다.
- 실패 시 해석이 최소 2갈래 이상으로 나뉜다.
- 결과가 hypothesis를 지지하는 범위와 non-claim이 분리돼 있다.
- Dataset unit, split/evaluator, baseline family, primary metric과
  disconfirmation rule을 paper-level scale-up 전에 고정할 수 있다.
- Experiment resource estimate와 Docker execution path가 현실적이다.

승격할 때 `experiments/E<number>_<short-title>/README.md`를 만들고 source
hypothesis path, frozen evidence, unresolved risk와 main experiment contract를
기록한다. 이후 paper-level 실행과 결과는 `experiments/`에서만 갱신한다.
