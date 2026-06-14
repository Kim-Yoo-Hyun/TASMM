# generated_artifacts

This is a local archive for generated experiment artifacts moved out of `experiments/`.

Policy:

- This directory is ignored by Git.
- It may contain large JSONL, detector outputs, intermediate tables, and historical reports.
- Share-facing result summaries should be copied or rewritten into `results/`.
- Active commands may regenerate outputs under `experiments/*/artifacts/`, which are also ignored by Git.

