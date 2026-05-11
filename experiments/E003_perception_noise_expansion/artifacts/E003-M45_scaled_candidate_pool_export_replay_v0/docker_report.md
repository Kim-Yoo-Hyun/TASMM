# E003-M44 Pre-Cap Candidate-Pool Export Smoke

## Status

pre_cap_candidate_pool_export_smoke_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 8
- Max frames per scan: 24
- Max predictions per frame: 60
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Selection score mode: `confidence_sqrt_depth_support_temporal_v0`
- Support evidence policy: `temporal_spatial_support_evidence_v0`
- Scanned frames: 192
- Frames with written predictions: 191
- Raw predictions: 67639
- Written predictions: 3407
- Support evidence ready: True
- Rows with support policy: 3407
- Support row field errors: 0
- Candidate pool export ready: True
- Candidate pool rows: 60435
- Candidate pool field errors: 0
- Skipped no-depth predictions: 1827
- Validator errors/warnings: 0 / 0
- Matched proposal rows: 196
- False-positive proposal rows: 3211
- Proposal precision smoke: 0.05752861755209862
- Scan target recall smoke: 0.5697674418604651
- Label-overlap target recall smoke: 0.5714285714285714
- Mean matched centroid error m: 0.5436999795918367
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M44 supports runner-side export of the cleaned pre-cap candidate pool for offline replay.
- E003-M44 does not support final real RGB-D/open-vocabulary robustness because it is a short export/replay smoke.

## 에이전트 추론

- The candidate pool should allow score-mode ablations without repeating detector inference.
- The next check is whether offline replay reproduces the runner-selected stable candidates.

## 사용자 판단 필요

- None for E003-M44 smoke.
