# E003-M44 Pre-Cap Candidate-Pool Export Smoke

## Status

pre_cap_candidate_pool_export_smoke_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 4
- Max frames per scan: 24
- Max predictions per frame: 60
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Selection score mode: `confidence`
- Support evidence policy: `none`
- Scanned frames: 93
- Frames with written predictions: 82
- Raw predictions: 2015
- Written predictions: 96
- Support evidence ready: True
- Rows with support policy: 0
- Support row field errors: 0
- Candidate pool export ready: True
- Candidate pool rows: 1970
- Candidate pool field errors: 0
- Skipped no-depth predictions: 27
- Validator errors/warnings: 0 / 0
- Matched proposal rows: 21
- False-positive proposal rows: 75
- Proposal precision smoke: 0.21875
- Scan target recall smoke: 0.7241379310344828
- Label-overlap target recall smoke: 0.7241379310344828
- Mean matched centroid error m: 0.49758619047619046
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
