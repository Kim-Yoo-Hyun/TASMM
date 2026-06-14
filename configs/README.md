# configs

This folder stores lightweight, versionable configuration files.

Rules:

- Keep dataset roots, checkpoint roots, Docker image names, and selected experiment IDs here when they are useful across scripts.
- Do not store credentials, local passwords, raw data, checkpoints, model caches, or generated artifacts.
- Local machine-specific overrides should stay untracked.

Current config:

- `e008_source_pool_scale.json`: active E008 M194-M198 source-pool scale reproduction chain.

