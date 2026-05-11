# Agent Rules

## Start Of Work

- Read `TODO.md` first.
- Update `TODO.md` when starting, finishing, or discovering a task.
- Keep `TODO.md` limited to plan, status, and next action.

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Research Target

- 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference 제출 가능성을 기준으로 판단한다.
- 후보, hypothesis, experiment, claim boundary를 정할 때 `NeurIPS`, `ICLR`, `ICML`, `CVPR`, `ICCV`, `ECCV`, `CoRL`, `ICRA`, `IROS`, `RA-L`, `T-RO`급 venue의 reviewer가 볼 novelty, contribution, benchmark rigor, reproducibility를 우선한다.
- 단기 smoke test는 허용하지만, 최종 claim은 top-tier paper로 확장 가능한 dataset scale, baseline, metric, ablation, robustness, failure analysis 경로를 가져야 한다.

## Workspace Shape

- Root operational files stay limited to `README.md`, `TODO.md`, and `AGENTS.md`.
- User-requested root-level reports such as `summary.md` are allowed, but do not add more root files unless explicitly needed.
- Research notes live under `literature/`.
- Do not create an empty `paper/` folder.
- Create a paper folder only after the thesis, main result table, method figure, target venue, and claim-evidence ledger are concrete.

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
