# Agent Rules

## Start Of Work

- Read `TODO.md` first.
- Update `TODO.md` when starting, finishing, or discovering a task.
- Keep `TODO.md` limited to plan, status, and next action.

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Workspace Shape

- Root files stay limited to `README.md`, `TODO.md`, and `AGENTS.md`.
- Research notes live under `literature/`.
- Do not create an empty `paper/` folder.
- Create a paper folder only after the thesis, main result table, method figure, target venue, and claim-evidence ledger are concrete.

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
