# scripts

This folder contains lightweight command wrappers for reproducible runs.

Rules:

- Keep wrappers thin; core logic stays in `experiments/*/tools/` or future `src/`.
- Do not store data, checkpoints, logs, or generated JSONL outputs here.
- Long-running jobs must write logs under `logs/` and follow `AGENTS.md`.

Current wrapper:

- `run_e008_source_pool_scale.sh`: verifies/runs the current E008 M194-M198 source-pool scale chain.

