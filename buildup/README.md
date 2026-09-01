# Research Buildup

Updated: 2026-09-01

## Role

이 폴더는 research topic을 찾고 research lead로 성장시키는 buildup 작업의
유일한 저장 위치다.

- Stable workflow와 gate 정의: `docs/buildup.md`
- Active home base, seed registry, reading, comparison, probe와 decision:
  `buildup/`
- Buildup을 통과한 research lead의 hypothesis 검증: `hypothesis/`
- 충분히 검증된 hypothesis의 paper-level experiment: `experiments/`

`docs/buildup.md`에는 절차만 기록한다. Live seed, 조사 결과, probe 결과와
판단은 이 폴더 밖에 중복하지 않는다.

## Current State

- Home base: `pending_user_proposal`
- Active seed: 없음
- Promoted lead: 없음

사용자가 home base와 resource boundary를 제안하기 전에는 하위 topic
folder를 만들거나 특정 연구 분야를 active scope로 정하지 않는다.

## Stage Flow

```text
buildup/
  topic discovery, seed portfolio, targeted reading, risk-reduction probe
    ↓ buildup gate 통과
hypothesis/
  falsifiable hypothesis, focused validation, disconfirmation
    ↓ experiment-ready gate 통과
experiments/
  paper-level scale, baselines, ablation, robustness, reproducibility
```

Stage를 건너뛰지 않는다. Buildup이 완료되지 않은 seed를 `hypothesis/`에
만들지 않고, 충분히 검증되지 않은 hypothesis를 `experiments/`로 넘기지
않는다.

## Folder Convention

Home base가 정해진 뒤 필요한 항목만 만든다.

```text
buildup/
  README.md
  <short-home-base>/
    README.md
    seeds/
      <short-seed>.md
    reading/
    probes/
```

- Home-base `README.md`가 scope, resource boundary, seed registry와 current
  gate의 authoritative owner다.
- `seeds/`에는 problem card를 둔다.
- `reading/`에는 seed 선택과 nearest-prior 판단에 직접 필요한 문헌 기록만
  둔다.
- `probes/`에는 risk-reduction contract와 결과를 둔다.
- 빈 하위 folder는 미리 만들지 않는다.

## Buildup Handoff Gate

`docs/buildup.md`의 `Handoff To Hypothesis` 조건을 모두 만족한 research
lead만 `hypothesis/`로 승격한다. 이 README에는 gate 결과, source card,
handoff destination과 promotion date만 registry로 남긴다.

승격할 때 `hypothesis/CAND-<number>/`를 만들고 source buildup path와 handoff
evidence를 기록한다. 이후 active hypothesis 판단과 결과는 `hypothesis/`만
갱신하며, buildup record는 provenance로 동결한다.

## Status Values

- `seed`: 초기 question
- `shortlisted`: 비교 후 상위 seed
- `probing`: risk-reduction probe 진행 중
- `promoted`: buildup gate 통과 후 hypothesis로 이관
- `killed`: 핵심 가정 반증 또는 observable target 부재
- `deferred`: resource나 user decision을 기다림

현재 상태와 바로 다음 action은 이 README와 `TODO.md`에 짧게 반영한다.
