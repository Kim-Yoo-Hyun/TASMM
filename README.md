# Research Workspace

업데이트: 2026-09-01

## Current State

현재 active candidate, hypothesis, experiment, paper claim은 없다.

[N28 admission-bottleneck synthesis](literature/admission-bottleneck-synthesis-search-stop-n28-2026-09.md)는 N20--N27을 다섯 independent route로 집계했다. Strict admission은 `0/5`였고, final evidence에서 exact novelty, simple-baseline-resistant residual, failure-forced method의 demonstrated pass는 각각 `0/5`였다.

Current outcome:

`stop_open_ended_direction_search_under_current_admission_contract`

이는 Robotics나 3D Vision에 연구 문제가 없다는 뜻이 아니다. 현재의 public-artifact/resource contract 안에서 top-tier candidate로 승격할 evidence chain이 없다는 판단이다.

## Active Workspace

| Path | Role |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 작업 규칙, novelty discipline, Docker-only 원칙 |
| [TODO.md](TODO.md) | 현재 상태와 다음 승인 경계 |
| [summary.md](summary.md) | 종료된 연구들의 핵심 결과와 재진입 조건 |
| [docs/](docs/) | literature, hypothesis, experiment, paper, reproducibility workflow |
| [literature/](literature/) | N20/N22--N28의 final decision reports만 보존 |
| [hypothesis/](hypothesis/) | active hypothesis 상태 |
| [experiments/](experiments/) | active experiment 상태 |

`local_dataset/`, `logs/`, in-repo `archive/`는 active workload가 없어 workspace에서 제거했다. 새 gate가 실제로 요구할 때만 다시 만든다.

## Retired Workspace

종료된 연구별 paper folders, E001--E009 source/artifacts, killed probes, datasets와 logs는 삭제하지 않고 다음 sibling archive로 이동했다.

- Archive: `/home/yoohyun/research2_retired_20260901/`
- Manifest: `/home/yoohyun/research2_retired_20260901/MANIFEST.md`
- Pre-move size: 약 8.8 GiB, non-Git files 34,873개

Archive는 historical evidence다. 새 hypothesis가 특정 자산을 요구하기 전에는 전체를 active workspace로 복원하지 않는다.

## Re-entry

Open-ended topic search는 다음 trigger 전까지 pause한다.

1. policy-visible row, privileged mechanism oracle, task outcome과 fixed evaluator를 함께 제공하는 new public denominator
2. group-disjoint split에서 최소 세 simple controls 뒤에도 남는 pre-existing residual
3. exact-prior audit 뒤 남고 특정 representation/inference/control form을 강제하는 principle
4. 사용자가 original benchmark/data/hardware instrumentation 또는 연구 scope 변경을 명시적으로 승인

세부 기준은 [N28](literature/admission-bottleneck-synthesis-search-stop-n28-2026-09.md)과 [TODO.md](TODO.md)를 따른다.
