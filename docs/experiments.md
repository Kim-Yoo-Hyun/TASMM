# Experiments Workflow

Updated: 2026-06-14

이 문서는 main experiment 구현과 기록을 위한 workflow / 작성 규칙만 관리한다. 실험별 내용, contract, manifest, 결과, failure analysis는 루트의 `experiments/` 폴더에 둔다.

## Storage Rule

- workflow와 작성 규칙: `docs/experiments.md`
- experiment index: `experiments/README.md`
- 개별 experiment: `experiments/E<number>_<short-title>/`
- 작업 계획과 진행 상태: `TODO.md`
- 논문 작성 protocol: `docs/paper.md`

`docs/experiments.md`는 절차와 기준만 관리한다. 특정 experiment의 question, hypothesis, dataset, baselines, metrics, commands, results, failure analysis는 `experiments/` 아래에 기록한다.

## Entry Context

Experiment 작업을 시작하는 에이전트는 아래 순서로 읽는다.

1. `AGENTS.md`
2. `README.md`
3. `TODO.md`
4. `docs/index.md`
5. `docs/experiments.md`
6. `docs/paper.md`
7. `docs/reproducibility.md`
8. `hypothesis/README.md`
9. 대상 hypothesis folder의 `README.md`
10. `experiments/README.md`
11. 대상 experiment folder의 `README.md`

## Working Rule

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, dataset, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 않고 구분한다.
- 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference 제출 가능성을 기준으로 판단한다.
- `TODO.md`는 계획, 상태, 다음 행동만 관리한다.
- `experiments/`에는 실제 experiment 내용과 산출물 계약을 둔다.
- `docs/experiments.md`에는 특정 experiment 숫자, 결과, claim ledger를 길게 넣지 않는다.

## Docker Rule

- 논문 본문용 experiment 구현은 Docker를 기본 실행 환경으로 둔다.
- 외부 repo, detector, simulator, GPU dependency, system package, compiled extension이 필요한 실험은 Dockerfile 또는 Docker 실행 명령이 있어야 paper-table command로 인정한다.
- 단순 artifact audit, JSONL 변환, 기존 산출물 재집계처럼 repository-local 표준 Python만 쓰는 보조 분석은 Docker 전 단계에서 실행할 수 있다.
- 최종 논문 표에 들어가는 command는 Docker image tag, mounted dataset path, exact command, seed, output path를 함께 기록한다.

## Main Experiment Gate

Experiment folder를 만들 수 있는 조건:

- 연결된 hypothesis가 `ready_with_constraints` 이상이다.
- target claim과 non-claims가 분리되어 있다.
- dataset unit, baseline family, metric family가 정해져 있다.
- failure case에서 무엇을 배울지 적을 수 있다.
- 빈 폴더가 아니라 최소 `README.md`를 함께 만든다.

Main experiment 구현 시작은 최종 thesis 확정을 뜻하지 않는다. 첫 scaled result와 failure analysis 이후에 thesis direction 확정 여부를 판단한다.

## Minimal Experiment Contract

각 experiment `README.md`에는 최소한 아래 항목을 둔다.

| Field | Required content |
| --- | --- |
| question | 실험이 답하는 연구 질문 |
| hypothesis | 결과가 어떻게 나올 것이라는 예상 |
| dataset | dataset root, split, manifest, preprocessing |
| method | test method, allowed inputs, blocked inputs |
| comparison | baseline, ablation, upper/lower bound |
| metrics | primary metrics, secondary diagnostics |
| command | 같은 결과를 재실행하는 정확한 명령 |
| output | metrics, predictions, logs, tables, figures |
| conclusion | claim을 지지/반박/보류하는 이유 |

No command, no paper table.

Paper-body implementation command는 위 Docker Rule을 만족해야 한다.

## Artifact Rule

- Manifest는 가능한 한 JSONL로 기록한다.
- Coverage와 aggregate metrics는 JSON으로 기록한다.
- 사람이 읽는 요약은 `README.md`나 짧은 report markdown에 둔다.
- 결과 표는 dataset split, method version, seed count, excluded cases, exact command를 함께 기록한다.
- 실패 사례는 `failure_type`, `suspected_cause`, `next_test`를 포함한다.

## Claim Boundary Rule

Experiment 결과를 기록할 때는 항상 네 구획을 유지한다.

- 사실: 실행한 데이터, 명령, 수치, 파일 경로
- 논문 주장: 결과로 안전하게 말할 수 있는 claim과 아직 말할 수 없는 claim
- 에이전트 추론: 왜 그렇게 해석하는지
- 사용자 판단 필요: thesis direction, claim expansion, 추가 구현 여부처럼 사용자가 결정해야 할 부분

## Code Layout Rule

초기에는 experiment folder 내부에서 작게 시작한다. 재사용 코드가 늘어나면 그때 루트 공용 구조로 승격한다.

```text
experiments/
  E<number>_<short-title>/
    README.md
    tools/
    artifacts/
```

공용 구조 생성 조건:

- `configs/`: 같은 실험을 seed나 dataset만 바꿔 반복할 때 필요해지면 만든다.
- `src/`: 재사용 함수가 experiment 2개 이상에서 공유될 때 만든다.
- `scripts/`: paper table을 재현하는 top-level CLI가 필요해지면 만든다.
- `outputs/`: 여러 experiment의 최종 table / figure를 모을 때 만든다.
