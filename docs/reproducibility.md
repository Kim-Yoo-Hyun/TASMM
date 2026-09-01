# Reproducibility Workflow

Updated: 2026-09-01

## Non-Negotiable Rules

- Paper, baseline, adapter, simulator, detector, smoke/evaluation은 Docker-only다.
- Host에서는 Markdown/source/Dockerfile 편집, Docker orchestration, download, checksum/manifest/log audit만 한다.
- Docker 실패를 host execution으로 우회하지 않는다.
- Dataset/source는 가능하면 read-only mount하고 derived output을 분리한다.
- GPU workload는 explicit `--gpus`와 device/mode를 기록한다.

## Required Run Record

- Dockerfile 또는 immutable image tag/digest
- source commit과 dependency lock
- build/run command, mount, working directory
- CPU/GPU mode, seed, split/manifest
- allowed input, evaluation-only input, leakage boundary
- output path와 independent verification command

## Current Data State

Active dataset과 runtime artifact는 없다. 이전 `local_dataset/` 전체는 다음 위치에 원래 layout으로 보존한다.

`/home/yoohyun/research2_retired_20260901/local_dataset/`

새 gate가 특정 dataset을 요구할 때만 named source를 active `local_dataset/`로 복원한다. Derived cache나 prediction을 source와 함께 wholesale 복원하지 않는다.

External `/home/yoohyun/research/local_dataset/Open3DSG_staged`가 존재할 경우 기존 규칙대로 read-only로만 사용하며 수정·삭제하지 않는다.

## Historical Execution Assets

| Archived route | Location |
| --- | --- |
| E001--E009 | `/home/yoohyun/research2_retired_20260901/experiments/` |
| killed/negative probes | `/home/yoohyun/research2_retired_20260901/hypothesis/probes/` |
| paper/deep-read folders | `/home/yoohyun/research2_retired_20260901/literature/` |
| completed logs | `/home/yoohyun/research2_retired_20260901/logs/` |
| consolidation inventory | `/home/yoohyun/research2_retired_20260901/MANIFEST.md` |

## Restore Rule

1. Active hypothesis가 named asset을 요구하는지 확인한다.
2. Archive manifest와 source README에서 input/output boundary를 확인한다.
3. 필요한 directory만 `cp -a`로 복원한다.
4. Archived artifact를 current result로 간주하지 않는다.
5. 새 run은 current Docker record와 새로운 verifier를 남긴다.

## Long Jobs

필요할 때 `logs/`를 만들고 download/build/render/inference를 background `tmux`에서 실행한다. Timestamped log, exact command, cwd, output, expected files와 verification command를 `TODO.md` 또는 experiment README에 기록한다.
