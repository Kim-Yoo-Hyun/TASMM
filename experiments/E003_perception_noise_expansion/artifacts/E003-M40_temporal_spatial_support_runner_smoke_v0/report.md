# E003-M40 Temporal-Spatial Support Runner Smoke

## Status

temporal_spatial_support_runner_smoke_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 1
- Max frames per scan: 2
- Max predictions per frame: 20
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Support evidence policy: `temporal_spatial_support_evidence_v0`
- Scanned frames: 2
- Frames with written predictions: 2
- Raw predictions: 736
- Written predictions: 95
- Support evidence ready: True
- Rows with support policy: 95
- Support row field errors: 0
- Skipped no-depth predictions: 74
- Validator errors/warnings: 0 / 0
- Matched proposal rows: 5
- False-positive proposal rows: 90
- Proposal precision smoke: 0.05263157894736842
- Scan target recall smoke: 0.09803921568627451
- Label-overlap target recall smoke: 0.09803921568627451
- Mean matched centroid error m: 0.3280304
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M40 supports runner-side instrumentation of temporal/spatial proposal support evidence.
- E003-M40 does not support final real RGB-D/open-vocabulary robustness because it is a short smoke, not a heldout policy evaluation.

## 에이전트 추론

- Support evidence is now available before downstream support-aware selection or scaled reruns.
- The next unit should test whether the support fields can reduce false positives without losing matched targets.

## 사용자 판단 필요

- None for E003-M40 smoke.
