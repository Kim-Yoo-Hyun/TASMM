# Research Agent Harness
이 저장소는 AI/ML/CV/Robotics 분야의 석사 연구를 위해 문헌 조사, 동향 파악, 기여 가능성 탐색을 누적하는 작업 공간이다.

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
- `docs/*.md`도 progress dump로 사용하지 않는다. `docs/buildup.md`는
  topic-incubation rulebook, `docs/paper.md`는
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
3. Research scoping and topic-development tasks: `docs/buildup.md`, then `buildup/README.md` and the relevant research-scope README
4. Hypothesis tasks: `docs/hypothesis.md`, `hypothesis/README.md`, then the selected source research-question record and target hypothesis README
5. Paper-level experiment tasks: `docs/experiments.md`, `docs/paper.md`, `docs/reproducibility.md`, `experiments/README.md`, then relevant experiment/config/report files
6. Literature tasks: `docs/literature.md`; store the output in the currently active stage folder

## Repository File Role Map

- `AGENTS.md`: agent-facing operating contract. Owns stable rules, file-role map, documentation ownership, experiment safety, novelty/claim guardrails, and update protocol.
- `README.md`: human-facing project overview and current high-level phase. It should summarize where the work stands, not duplicate runbooks.
- `TODO.md`: mutable task board. Owns `Now`, `Next`, and recently completed items. It should not contain long literature notes, full metrics, or large command logs.
- `summary.md`: consolidated research summary. Owns problem definition, hypothesis, contribution, metric/baseline plan, current evidence, and top-level paper direction.
- `docs/index.md`: documentation index. Owns navigation pointers and file-role links only; current status, active questions, metrics, and artifact inventories belong to the smallest authoritative owner such as `TODO.md`, `summary.md`, folder `README.md`, or reports.
- `docs/buildup.md`: research-scoping and topic-development workflow. Owns scope entry requirements, candidate research questions, comparative assessment, feasibility/pilot studies, selection decisions, and entry to hypothesis formulation.
- `docs/literature.md`: literature workflow rulebook. Owns preliminary literature review, related-work records, trend synthesis, and contribution scans.
- `docs/hypothesis.md`: hypothesis workflow rulebook. Owns candidate/hypothesis stages, gate criteria, and hypothesis artifact conventions.
- `docs/experiments.md`: Docker experiment workflow rulebook. Owns experiment promotion criteria, root-creation checklist, source adapter expectations, metric-freeze gates, and paper-result boundary rules.
- `docs/paper.md`: paper-framing rulebook. Owns top-tier novelty standard, claim boundary, reviewer-process interpretation, reviewer-risk checklist, and table/ablation/failure-analysis requirements. It should not become a manuscript changelog or PDF build log.
- `docs/reproducibility.md`: recovery and reproducibility runbook. Owns dataset/checkpoint/model locations, artifact bundles, Docker commands, verification commands, transfer guidance, and cleanup implications.
- `buildup/`: the only active storage root for research scope, candidate research questions, preliminary literature review, feasibility/pilot studies, and question-selection decisions.
- `hypothesis/`: the only active storage root for selected research questions, formal hypotheses, focused validation, and experiment handoff evidence.
- `experiments/`: the only active storage root for sufficiently validated hypotheses promoted to paper-level scaled work.
- `literature/README.md`: the sole compact summary of retired research. Do not duplicate that history in active stage indexes or workflow documents.
- Keep hypothesis-stage smoke tests and paper-body experiment artifacts explicitly separate.
- Paper-body experiments use Docker as the default execution environment.
- `docs/hypothesis.md`는 hypothesis workflow와 작성 규칙을 관리한다.
- `docs/literature.md`는 literature workflow와 작성 규칙을 관리한다.
- `docs/experiments.md`는 Docker experiment workflow와 promotion 규칙을 관리한다.
- `docs/paper.md`는 top-tier paper framing, novelty standard, reviewer-defense rule을 관리한다.
- `docs/literature.md`와 `docs/hypothesis.md`는 workflow rulebook으로 유지한다.

## Documentation Ownership Rules

- If a change adds or changes a rule, update `AGENTS.md`.
- If a change updates current status, active work, or completion history, update `TODO.md` and the smallest authoritative owner. Update `docs/index.md` only when document locations, role maps, or durable workflow roots change.
- If a change affects research framing, contribution, novelty, or reviewer defense, update `docs/paper.md`, `summary.md`, and the relevant `paper/` planning file.
- If a change affects commands, datasets, checkpoints, model caches, artifact transfer, or cleanup safety, update `docs/reproducibility.md`, the relevant config README/compose file, and the relevant experiment README.
- If a change affects a folder-local workflow, update that folder's `README.md`; do not expand `AGENTS.md` with folder-local details.
- Report files: 새 `report_*.md` 파일은 사용자가 명시적으로 요청한 경우에만 만든다. 사용자가 새 report 작성을 요청하지 않은 진행 사항은 현재 작업 범위의 기존 authoritative report 파일에 계속 반영한다. 중복된 stage report를 늘리지 말고 기존 report에 누적하거나 병합한다.
- When a new durable root-level research/workflow folder is created or activated, add it to `docs/index.md` and the relevant README role map before substantive work in that folder. Create a matching `docs/<folder>.md` only if the folder needs workflow rules beyond its local README. This applies to durable workflow roots such as `src/`, `configs/`, `experiments/`, `results/`, `paper/`, `literature/`, or reactivated hypothesis work, not transient/ignored roots such as `logs/`, `local_dataset/`, or `release/`.
- If a detailed list appears in more than one place, keep the authoritative copy in the owning document and replace other copies with a pointer.
- Documentation-system convention: `docs/index.md` and `docs/README.md` are
  entry points, similar to MkDocs/Docusaurus/Sphinx index pages. They should
  point to owning documents, not reproduce the content. When a `docs/*.md` file
  starts accumulating live progress, move that progress to `TODO.md`,
  `summary.md`, folder `README.md`, or the closest report and leave a pointer.

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Research Target

- 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference 제출 가능성을 기준으로 판단한다.
- 후보, hypothesis, experiment, claim boundary를 정할 때 `NeurIPS`, `ICLR`, `ICML`, `CVPR`, `ICCV`, `ECCV`, `CoRL`, `ICRA`, `IROS`, `RA-L`, `T-RO`급 venue의 reviewer가 볼 novelty, contribution, benchmark rigor, reproducibility를 우선한다.
- 단기 smoke test는 허용하지만, 최종 claim은 top-tier paper로 확장 가능한 dataset scale, baseline, metric, ablation, robustness, failure analysis 경로를 가져야 한다.

## Research Scoping And Topic Development

- 새 연구주제는 `AI`, `ML`, `CV`, `Robotics` 전체에서 탐색할 수 있으며 특정 분야를 기본 scope로 가정하지 않는다.
- Research scoping과 topic development는 `docs/buildup.md`를 먼저 따른다. Question selection, hypothesis validation, paper-level admission을 서로 다른 stage로 유지한다.
- `research scope`는 사용자가 명시적으로 선택한다. 선택 전에는 특정 task, method, dataset, application 또는 venue를 active scope로 추정하지 않는다.
- Candidate research question에는 exact novelty, final method, full benchmark, multi-domain evidence, failure-derived principle을 동시에 요구하지 않는다. 먼저 observable question, simplest baseline, critical assumption, feasibility/pilot study와 informational value를 확인한다.
- Research scoping과 topic-development payload는 `buildup/`에서만 관리한다. Hypothesis Formulation Entry Criteria를 통과한 question만 `hypothesis/`로 넘긴다.
- Hypothesis의 focused validation은 `hypothesis/`에서만 관리한다. 충분히 검증돼 Experiment Handoff Gate를 통과한 hypothesis만 `experiments/`로 넘긴다.
- `experiments/`는 scaled benchmark, strong baseline, ablation, robustness, reproducibility와 paper claim을 다루는 paper-level stage다.

## Novelty Discipline

- Motivation을 novelty로 쓰지 않는다. 기존 방법이 noise, distribution shift,
  long-horizon setting 또는 resource constraint에서 실패한다는 사실은 문제
  제기일 뿐이다.
- 새 module, LLM/VLM adapter, detector, reranker 또는 memory layer를
  붙였다는 사실만으로 contribution이라고 쓰지 않는다.
- 각 paper claim은 `motivation -> naive baseline -> failure diagnosis -> principle -> method form -> ablation/evidence` 순서로 방어되어야 한다.
- Hypothesis와 experiment는 증명하고 싶은 결론에 맞춰 끼워 맞추지 않는다. 실패 진단에서 나온 원리가 다음 method form, ablation, scale-up gate를 자연스럽게 요구해야 한다.
- 가장 단순한 naive baseline을 먼저 정의하고, 왜 실패하는지 case-level failure taxonomy로 기록한다.
- Method component는 failure diagnosis에서 도출되어야 한다. component를 다른 module로 쉽게 바꿔도 설명이 유지되면 novelty가 약한 것이다.
- 결과가 기대와 다르면 claim을 유지한 채 threshold나 denominator를 조정하지 않는다. 먼저 failure mode, disconfirmation rule, 다음 validation requirement를 기록하고, 그 기록에서 다음 실험을 도출한다.
- "왜 더 단순한 X로는 안 되는가?"에 대해 선택된 candidate와 failure
  diagnosis에 맞는 domain-relevant X를 최소 3개 준비한다.
- Contribution sentence에서 "we propose"를 지워도 남는 insight가 있어야 한다.
- Ablation은 전체 system vs baseline만으로 끝내지 않는다. 해당 candidate의 failure diagnosis에서 나온 핵심 요인, resource/cost, reliability와 strongest external baseline이 각각 무엇을 깨뜨리는지 보여야 한다.
- Generality claim은 2개 이상의 split, scene group, label group, task/domain, 또는 external baseline route에서 지지될 때만 쓴다.
- Failure mode는 future work로 숨기지 않는다. 실패 조건, 원인, 다음 validation requirement를 claim boundary에 명시한다.
- 기존 system에 LLM/VLM, adapter, reranker, detector 또는 새 module을 붙였다는 사실만으로 contribution을 주장하지 않는다. 선택된 domain의 failure 원인과 새 principle의 필연성을 한 문장으로 설명해야 한다.

## Docker-Only Reproduction

- 모든 paper, baseline, external method의 reproduction, reimplementation, adapter 실행, smoke test, evaluation은 Docker container 안에서만 수행한다.
- Host 환경에 baseline code나 그 dependency를 설치하지 않는다. Host에서 `pip`/`conda`/`apt` install, editable install, ROS/`colcon` build, CUDA/native extension compile, baseline entry-point 실행을 하지 않는다.
- External source는 read-only audit 또는 Docker build context 용도로만 checkout할 수 있다. Source와 repository code를 container에 copy하거나 mount할 수 있지만 install/import/compile/runtime은 container 내부에서만 수행한다.
- Docker build/run이 실패하거나 image가 없을 때 host 실행으로 우회하지 않는다. Docker recipe/image를 복구할 때까지 해당 reproduction을 `blocked` 또는 `unavailable`로 기록한다.
- Host에서 허용되는 작업은 Markdown/source/Dockerfile 작성, Docker build/run orchestration, dataset/checkpoint download, checksum/manifest/log inspection, 그리고 method dependency를 import하거나 실행하지 않는 lightweight repository validation으로 제한한다.
- Dataset/source mount는 가능한 한 read-only로 두고, derived cache, prediction, checkpoint, evaluation output은 명시된 workspace artifact 경로에 쓴다.
- 각 reproduction은 Dockerfile 또는 immutable image reference, image digest/tag, source commit, dependency lock, build command, run command, mount, CPU/GPU mode, seed, output path, verification command를 기록한다.
- GPU가 필요한 workload는 NVIDIA Container Toolkit과 explicit `--gpus` option으로 실행한다. CPU-capable workload도 Docker 안에서 실행하며, GPU 필요 여부와 사용 device를 config/artifact에 기록한다.

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

## Artifact Handoff And Cleanup Rules

- Always distinguish three goals before advising uploads or deletion: paper-result preservation, current experiment resume, and full reproduction. Each goal requires a different artifact set.
- GitHub should carry `src/`, `configs/`, `scripts/`, runbooks, paper source, compact manifests, reports, table summaries, and metric summaries. Large `local_dataset/` payloads, model caches, feature caches, and row-level JSONL outputs stay ignored and must be transferred separately or regenerated.
- Before deleting any local dataset, checkpoint, feature cache, model cache, or row-level JSONL, verify the external copy with checksums, file counts, expected directory layout, or a lightweight sanity script. Record the verification and deletion rationale in `TODO.md` or `docs/reproducibility.md`.

## Contribution Candidate Standard

Each candidate must state:

- existing limitation it starts from
- why it is a substantive problem in the selected research area
- dataset, benchmark, metric, evaluator, or study design that can test it
- what we learn if the idea fails

## Working Style

- Prefer small Markdown updates before code.
- If a new task appears during work, add it to `TODO.md`.
- Do not add long explanations to `TODO.md`; put research detail in the active stage's closest README, research-question record, study, or experiment report.
- For research scoping and topic development, follow `docs/buildup.md` before opening a hypothesis.
- For literature work, follow `docs/literature.md`.
- For hypothesis work, follow `docs/hypothesis.md`.
- For paper-body experiment implementation, use Docker as the default execution environment.

## Naming Rules

- 파일명과 문서 제목은 직관적이고 핵심 단어 기반으로 짧게 작성한다.
- 부모 폴더나 workflow 이름을 파일명에 반복하지 않는다. 예: `visual_inspection/labels.jsonl`처럼 쓴다.
- 불필요한 긴 접두사, 중복된 candidate/hypothesis 이름, 설명문 형태의 파일명은 피한다.
- 번호가 필요한 workflow 문서는 기존 순서를 유지하되 제목은 짧게 둔다. 예: `01_overview.md`, `02_method.md`.
- 중복된 stage 문서는 하나의 짧은 stage log로 병합한다. 이미 병합한 오래된 번호 파일을 다시 만들지 않는다.

## Update Protocol

모든 갱신은 "가장 작은 authoritative owner"에 기록한다.

- `AGENTS.md`: stable rule이나 file-role 책임이 바뀔 때만 수정한다.
- `TODO.md`: 시작할 작업은 `Now`, 바로 다음 작업은 `Next`, 완료한 작업은 `Recently Completed`에 둔다.
- `docs/index.md`: 문서 위치, role map, durable workflow root 색인이 바뀔 때만 갱신한다. 연구 상태 dashboard나 active questions는 소유하지 않는다.
- `summary.md`: 현재 active research의 문제 정의, 가설, contribution, metric, baseline, experiment setting, claim boundary만 갱신한다.
- `docs/buildup.md`: research-scope entry requirements, candidate-question comparison, feasibility/pilot study와 hypothesis-formulation entry criteria를 관리한다. Live question status와 payload는 `buildup/`이 소유한다.
- `buildup/README.md`: research scope, candidate-question registry, current selection decision과 hypothesis-formulation handoff record를 관리한다.
- `docs/literature.md`: 문헌 조사 절차를 관리한다. 실제 payload는 현재 작업 중인 `buildup/`, `hypothesis/`, 또는 `experiments/`의 가장 작은 owner에 둔다.
- `docs/hypothesis.md`: hypothesis gate와 artifact convention을 관리한다. 실제 payload는 `hypothesis/`에 둔다.
- `docs/experiments.md` / `experiments/`: Docker experiment promotion, source adapter, metric-freeze, and paper-result boundary를 관리한다.
- `docs/paper.md` / `paper/`: paper-level novelty, reviewer defense, outline, draft, figure/table plan, venue-specific source를 관리한다.
- `docs/reproducibility.md` / `experiments/**/README.md`: dataset, checkpoint, model cache, Docker command, artifact bundle, verification, cleanup safety를 관리한다.
- `logs/`: long-running job log와 exit/status file만 둔다. 중요한 결과는 owning report/README/TODO에 요약한다.

세부 파일명, artifact directory, row-level output, run command 목록은 `AGENTS.md`에 추가하지 않는다. 그런 정보는 `docs/reproducibility.md`, `docs/hypothesis.md`, `experiments/**/README.md`, or source-specific README가 소유한다.

# Experiment implementation rule:

- 논문 본문에 들어갈 실제 experiment 구현은 Docker 기반으로만 진행한다.
- Host 환경에서 직접 패키지를 설치하거나 host-only script로 paper experiment를 확정하지 않는다.
- Experiment root를 만들 때는 Dockerfile 또는 compose file, pinned dependency record, mounted dataset/cache path, command entrypoint, and output manifest를 함께 둔다.
- `local_dataset/` 같은 큰 runtime/data root는 container에 mount하고 tracked artifact로 복사하지 않는다.
- Hypothesis-stage smoke test와 문서 검증은 기존 방식으로 가능하지만, paper experiment 결과로 승격하려면 Docker command로 재현 가능해야 한다.
- 중간 산출물이 더 구체적인 review/report artifact로 대체되면 오래된 queue 파일은 유지하지 않는다.

# Academic Terminology and Naming

- Prefer established, general academic terminology used in the relevant literature.
- Do not use project-internal names, implementation terms, variable names, or ad-hoc phrases as research terminology.
- Do not invent new terminology when an established or descriptive technical term is sufficient.
- Introduce a project-specific term only when it represents a genuinely distinct concept, and define it clearly at first use.
- Write terminology for an external researcher who has no knowledge of the repository or prior discussions.
- Use the same academic term consistently across papers, documentation, figures, tables, and experiment descriptions.
- Priority: established literature term > general technical term > descriptive formal phrase > project-specific term.
