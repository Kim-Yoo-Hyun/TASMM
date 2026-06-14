# src

This folder is reserved for reusable library code extracted from experiment scripts.

Current status:

- The active implementation is still script-first under `experiments/*/tools/`.
- Do not move experiment-local scripts here unless their import paths, Docker build context, and reproduction commands are updated together.
- Shared code promoted here should be stable enough to be imported by multiple experiment stages.

