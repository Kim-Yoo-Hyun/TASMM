# Agent Rules

## Start Of Work

- Treat `AGENTS.md` as the top-level project instruction, not as an experiment log.
- Read startup context in this order: `AGENTS.md` -> `README.md` -> `TODO.md` -> `docs/index.md`.
- After startup context, use `TODO.md` Now/Next as the active work queue.
- Before editing or running a task, read the relevant workflow document under `docs/` and the nearest folder `README.md`.
- Update `TODO.md` when starting, finishing, or discovering a task.
- Keep `TODO.md` limited to plan, status, and next action.
- `docs/hypothesis.md`는 hypothesis workflow와 작성 규칙을 관리한다.
- `docs/literature.md`는 literature workflow와 작성 규칙을 관리한다.
- `docs/experiments.md`는 Docker experiment workflow와 promotion 규칙을 관리한다.
- `docs/paper.md`는 top-tier paper framing, novelty standard, reviewer-defense rule을 관리한다.
- `docs/literature.md`와 `docs/hypothesis.md`는 workflow rulebook으로 유지한다.

## Instruction Strategy

`AGENTS.md`는 작업 전에 읽히는 project instruction이며, 세부 연구 로그가 아니라 에이전트용 상위 운영 규칙이다. OpenAI Codex guidance처럼 repo-level instruction에는 setup/rules/expectations, file responsibilities, verification expectations만 두고, 상세 지침은 가까운 하위 문서나 nested instruction으로 분리한다.

- 이 repo의 기본 구조는 `AGENTS.md = 상위 규칙과 파일 책임`,
  `docs/*.md = repository-wide workflow rulebook / navigation / recovery
  runbook`, 각 폴더 `README.md`와 가까운 report = folder-local state/runbook
  이다.
- 이 파일에는 변하지 않는 rule, document ownership, claim boundary, experiment safety rule만 둔다.
- 최신 실험 상태, 긴 artifact 목록, 실행 명령, row count, completion log는
  `summary.md`, `TODO.md`, folder `README.md`, closest report artifact, 또는
  recovery 성격일 때만 `docs/reproducibility.md`에 둔다. `docs/index.md`는
  색인과 문서 위치 안내만 소유한다.
- 특정 폴더의 세부 규칙은 그 폴더의 `README.md` 또는 필요 시 nested `AGENTS.md`로 분리한다.
- `AGENTS.md`를 run log, paper draft, artifact inventory, download checklist, or metric table로 사용하지 않는다.
- `docs/*.md`도 progress dump로 사용하지 않는다. `docs/paper.md`는
  reviewer-facing writing rulebook, `docs/experiments.md`는 Docker promotion
  rulebook, `docs/hypothesis.md`와 `docs/literature.md`는 workflow rulebook,
  `docs/reproducibility.md`는 recovery/runbook 예외로 유지한다.
- Codex의 project instruction size limit을 고려해 이 파일은 간결하게 유지한다. 긴 목록은 owning document로 이동한다.

## Reading Protocol

작업 시작 시에는 `AGENTS.md`를 최상위 project instruction으로 먼저 읽고,
이어서 현재 상태와 우선순위를 재구성한다. 이후 작업 유형에 맞는 대표
문서를 읽고 필요한 폴더의 `README.md`로 내려간다.

1. Global instruction: `AGENTS.md`
2. Orientation: `README.md`, `TODO.md`, `docs/index.md`
3. Global rules: `docs/paper.md`, `docs/experiments.md`, `docs/reproducibility.md`
4. Research state: `summary.md`, `experiments/RelCompat3D_geom_reliability/README.md`, and compact `results/`
5. Literature tasks: `docs/literature.md`; restore the local archive only when explicitly reactivating the workflow
6. Hypothesis tasks: `docs/hypothesis.md`; restore the local archive only when explicitly reactivating the workflow
7. Experiment tasks: `docs/experiments.md`, relevant `experiments/**/README.md`, `commands.md`, `configs/**/compose*.yaml`, and reports

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Research Target

- 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference 제출 가능성을 기준으로 판단한다.
- 후보, hypothesis, experiment, claim boundary를 정할 때 `NeurIPS`, `ICLR`, `ICML`, `CVPR`, `ICCV`, `ECCV`, `CoRL`, `ICRA`, `IROS`, `RA-L`, `T-RO`급 venue의 reviewer가 볼 novelty, contribution, benchmark rigor, reproducibility를 우선한다.
- 단기 smoke test는 허용하지만, 최종 claim은 top-tier paper로 확장 가능한 dataset scale, baseline, metric, ablation, robustness, failure analysis 경로를 가져야 한다.

## Novelty Discipline

- Motivation을 novelty로 쓰지 않는다. "기존 방법이 dynamic object, RGB-D noise, open-vocabulary query, stale memory에서 실패한다"는 문제 제기일 뿐이다.
- 새 module, LLM/VLM adapter, detector, reranker, map layer를 붙였다는 사실만으로 contribution이라고 쓰지 않는다.
- 각 paper claim은 `motivation -> naive baseline -> failure diagnosis -> principle -> method form -> ablation/evidence` 순서로 방어되어야 한다.
- Hypothesis와 experiment는 증명하고 싶은 결론에 맞춰 끼워 맞추지 않는다. 실패 진단에서 나온 원리가 다음 method form, ablation, scale-up gate를 자연스럽게 요구해야 한다.
- 가장 단순한 naive baseline을 먼저 정의하고, 왜 실패하는지 case-level failure taxonomy로 기록한다.
- Method component는 failure diagnosis에서 도출되어야 한다. component를 다른 module로 쉽게 바꿔도 설명이 유지되면 novelty가 약한 것이다.
- 결과가 기대와 다르면 claim을 유지한 채 threshold나 denominator를 조정하지 않는다. 먼저 failure mode, disconfirmation rule, 다음 validation requirement를 기록하고, 그 기록에서 다음 실험을 도출한다.
- "왜 더 단순한 X로는 안 되는가?"에 대해 최소 3개의 X를 준비한다. 예: static memory, detector-confidence ranking, fixed top-k, context-agnostic memory trust.
- Contribution sentence에서 "we propose"를 지워도 남는 insight가 있어야 한다.
- Ablation은 전체 system vs baseline만으로 끝내지 않는다. task context, staleness/memory trust, re-observation budget, path/search cost, proposal reliability, external map baseline 연결이 각각 무엇을 깨뜨리는지 보여야 한다.
- Generality claim은 2개 이상의 split, scene group, label group, task/domain, 또는 external baseline route에서 지지될 때만 쓴다.
- Failure mode는 future work로 숨기지 않는다. 실패 조건, 원인, 다음 validation requirement를 claim boundary에 명시한다.
- 우리 연구에서 금지되는 약한 claim: "semantic map에 human intent/VLM/open-vocabulary perception을 붙였다." 더 강한 claim은 stale semantic memory의 실패 원인과 memory trust/re-observation/search-cost decision의 필연성을 한 문장으로 설명해야 한다.

## Workflow And Judgment Sources

- `docs/index.md` is the document map and read-order hub.
- `docs/literature.md` defines literature survey workflow.
- `docs/hypothesis.md` defines hypothesis validation workflow.
- `docs/paper.md` defines paper framing, top-tier novelty, claim-evidence, and reviewer-defense standards.
- `docs/reproducibility.md` defines experiment reproduction, artifact, Docker, checkpoint, and backup/restore standards.
- For paper-related judgments, apply `docs/paper.md` before local preference.
- For reproducibility or artifact judgments, apply `docs/reproducibility.md` before local preference.
- Keep hypothesis-stage smoke tests and paper-body experiment artifacts explicitly separate.
- Paper-body experiments use Docker as the default execution environment.

## Docker-Only Reproduction

- 모든 paper, baseline, external method의 reproduction, reimplementation, adapter 실행, smoke test, evaluation은 Docker container 안에서만 수행한다.
- Host 환경에 baseline code나 그 dependency를 설치하지 않는다. Host에서 `pip`/`conda`/`apt` install, editable install, ROS/`colcon` build, CUDA/native extension compile, baseline entry-point 실행을 하지 않는다.
- External source는 read-only audit 또는 Docker build context 용도로만 checkout할 수 있다. Source와 repository code를 container에 copy하거나 mount할 수 있지만 install/import/compile/runtime은 container 내부에서만 수행한다.
- Docker build/run이 실패하거나 image가 없을 때 host 실행으로 우회하지 않는다. Docker recipe/image를 복구할 때까지 해당 reproduction을 `blocked` 또는 `unavailable`로 기록한다.
- Host에서 허용되는 작업은 Markdown/source/Dockerfile 작성, Docker build/run orchestration, dataset/checkpoint download, checksum/manifest/log inspection, 그리고 method dependency를 import하거나 실행하지 않는 lightweight repository validation으로 제한한다.
- Dataset/source mount는 가능한 한 read-only로 두고, derived cache, prediction, checkpoint, evaluation output은 명시된 workspace artifact 경로에 쓴다.
- 각 reproduction은 Dockerfile 또는 immutable image reference, image digest/tag, source commit, dependency lock, build command, run command, mount, CPU/GPU mode, seed, output path, verification command를 기록한다.
- GPU가 필요한 workload는 NVIDIA Container Toolkit과 explicit `--gpus` option으로 실행한다. CPU-capable workload도 Docker 안에서 실행하며, GPU 필요 여부와 사용 device를 config/artifact에 기록한다.

## Workspace Shape

- Root operational files stay limited to `README.md`, `TODO.md`, and `AGENTS.md`.
- User-requested root-level reports such as `summary.md` are allowed, but do not add more root files unless explicitly needed.
- `AGENTS.md` defines repo-level rules, work expectations, file responsibility, novelty standards, and Docker/reproducibility principles only.
- Root `README.md` gives the repo-level current status and key file guide; do not duplicate long experiment records there.
- Each folder `README.md` is the local entry point for that folder.
- Research notes live under `literature/`.
- `literature/README.md` maintains cross-paper synthesis.
- `hypothesis/README.md` maintains the hypothesis index and active gate.
- If `paper/` exists, `paper/README.md` maintains paper workspace file roles, read order, and update rules.
- Do not create an empty `paper/` folder.
- Create a paper folder only after the thesis, main result table, method figure, target venue, and claim-evidence ledger are concrete.
- Put detailed results, long experiment records, and artifact interpretation in the closest responsible workflow document, folder `README.md`, `report.md`, or artifact note; do not copy them into `AGENTS.md` or root `README.md`.
- Retired 2026-09-01 source, artifacts, datasets, logs, paper folders, and long records live outside the active workspace at `/home/yoohyun/research2_retired_20260901/`; treat that tree as read-only historical evidence and restore only a named asset required by an active gate.
- Do not restore the retired tree wholesale. Recreate active `local_dataset/`, `logs/`, candidate, or experiment directories only when `TODO.md` opens a concrete task.

## Long-running and Background Tasks

- Do not keep Codex blocked while waiting for dataset downloads, model checkpoints, Docker pulls/builds, decompression, indexing, preprocessing, or other long-running I/O-heavy jobs.
- Launch long jobs in a separate `tmux` session, `nohup` process, or background job, then return to the main research task.
- Prefer resumable commands: `aria2c`, `wget -c`, `rsync --partial`, or `huggingface-cli download` with a fixed cache or `--local-dir`.
- Always write logs under `logs/` with a timestamped filename.
- Record the exact command, working directory, output path, expected files, and verification command in `TODO.md` or the relevant hypothesis/experiment `README.md`.
- Track job status as `launched`, `running`, `completed`, `failed`, or `needs verification`.
- Check progress only when explicitly requested or when a dependent task needs the result.
- Never scan or print huge logs; inspect only `tail`, `head`, or targeted `grep` / `rg` errors.
- Verify completion with file counts, expected directory layout, checksum if available, or a lightweight sanity script.
- Template:

```bash
mkdir -p logs
tmux new -d -s <job_name> 'cd /home/yoohyun/research2 && <command> > logs/<YYYYMMDD_HHMMSS>_<job_name>.log 2>&1'
```

## External Read-Only Dataset Reuse
- Experiment reports may live under `experiments/`, but data-bearing outputs from this source should point to the `research2/local_dataset` location.

## Contribution Candidate Standard

Each candidate must state:

- existing limitation it starts from
- why it is a semantic mapping problem
- dataset, benchmark, or metric that can test it
- what we learn if the idea fails

## Working Style

- Prefer small Markdown updates before code.
- If a new task appears during work, add it to `TODO.md`.
- Do not add long explanations to `TODO.md`; put research detail in `literature/`.
- For literature work, follow `docs/literature.md`.
- For hypothesis work, follow `docs/hypothesis.md`.
- For paper-body experiment implementation, use Docker as the default execution environment.
