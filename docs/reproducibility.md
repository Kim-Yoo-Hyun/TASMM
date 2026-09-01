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

Active dataset과 runtime artifact는 없다.

새 hypothesis 또는 experiment가 named dataset/checkpoint를 요구할 때만
`local_dataset/`을 만들고 source, checksum, mount, derived-output boundary를
기록한다.

External dataset/source를 재사용할 때는 read-only mount를 기본으로 하고,
derived cache, prediction과 evaluation output은 active workspace의 명시된
artifact 경로에 분리한다.

## Data Activation Rule

1. Active hypothesis 또는 experiment가 named asset을 요구하는지 확인한다.
2. Source license, checksum, expected layout과 read/write boundary를 기록한다.
3. 필요한 asset만 준비하고 unrelated dataset/cache를 함께 활성화하지 않는다.
4. 새 run은 current Docker record와 independent verifier를 남긴다.

## Long Jobs

필요할 때 `logs/`를 만들고 download/build/render/inference를 background `tmux`에서 실행한다. Timestamped log, exact command, cwd, output, expected files와 verification command를 `TODO.md` 또는 experiment README에 기록한다.
