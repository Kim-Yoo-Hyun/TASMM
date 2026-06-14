# archive

This folder preserves material that is no longer part of the active, share-facing execution path.

Contents:

- `hypothesis/`: historical hypothesis-stage workspace after promotion into `experiments/`.
- `blocked_routes/`: blocked or deprioritized route code such as `DualMap` and `OpenMask3D` scaffolds.
- `legacy/`: miscellaneous legacy scratch directories.
- `generated_artifacts/`: local archive of generated experiment artifacts moved out of active experiment code. This directory is ignored by Git to keep the shared repository lightweight.

Rules:

- Do not import active code from `archive/`.
- Do not use archived artifacts as paper evidence without copying the relevant lightweight summary into `results/` or regenerating the artifact from `experiments/*/tools/`.
- If a route is reactivated, move only the needed code back into the active structure and update README/reproducibility paths in the same change.

