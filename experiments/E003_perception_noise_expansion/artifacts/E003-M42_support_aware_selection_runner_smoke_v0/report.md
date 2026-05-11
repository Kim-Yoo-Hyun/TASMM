# E003-M42 Support-Aware Selection Runner Smoke

## Status

support_aware_selection_runner_smoke_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 1
- Max frames per scan: 2
- Max predictions per frame: 20
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Selection score mode: `confidence_sqrt_depth_support_temporal_v0`
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

- E003-M42 supports a short runner smoke for the selected support-aware score mode.
- E003-M42 does not support final real RGB-D/open-vocabulary robustness because it is not a scaled heldout evaluation.

## 에이전트 추론

- The next decision should compare this smoke against E003-M40 before committing to a longer rerun.
- A scaled claim still requires recall-preserving false-positive reduction beyond this short smoke.

## 사용자 판단 필요

- None for E003-M42 smoke.
