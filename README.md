# Research Workspace

업데이트: 2026-09-01

## Current State

현재 phase는 `research scoping pending`이다. Active research scope,
candidate research question, hypothesis, experiment와 paper claim은 없다.
Research scope는 사용자가 제안하기 전까지 정하지 않는다.

## Research Pipeline

```text
buildup/     research scoping, candidate questions, feasibility studies
    ↓ Hypothesis Formulation Entry Criteria
hypothesis/  formal hypothesis와 focused validation
    ↓ experiment-ready gate
experiments/ paper-level scale, baselines, ablation, robustness, artifacts
```

- Research scoping과 topic development는 `buildup/`에서만 진행한다.
- Entry criteria를 충족해 선택된 research question만 `hypothesis/`로 넘긴다.
- 충분히 검증된 hypothesis만 `experiments/`로 넘겨 paper-level 작업을 한다.
- 각 단계의 live 내용과 결과는 다음 단계나 다른 index에 중복하지 않는다.

## Active Workspace

| Path | Role |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 작업 규칙, novelty discipline, Docker-only 원칙 |
| [TODO.md](TODO.md) | 현재 상태와 다음 승인 경계 |
| [summary.md](summary.md) | 현재 active research의 top-level summary |
| [docs/](docs/) | buildup, literature, hypothesis, experiment, paper, reproducibility workflow |
| [buildup/](buildup/) | research scope, candidate questions, related work, feasibility studies와 selection decision |
| [hypothesis/](hypothesis/) | selected question의 formal hypothesis와 focused validation |
| [experiments/](experiments/) | validated hypothesis의 paper-level work |
| [literature/](literature/) | 종료된 연구의 유일한 compact summary |

## Next

1. 사용자가 research scope와 resource constraints를 제안한다.
2. `buildup/README.md`와 `docs/buildup.md`에 따라 scope folder와 서로 다른
   candidate research questions 3--5개를 만든다.
3. 상위 1--2개에 preliminary literature review와 feasibility/pilot study를
   적용한다.
4. Hypothesis Formulation Entry Criteria를 통과한 question만 `hypothesis/`로
   넘긴다.
