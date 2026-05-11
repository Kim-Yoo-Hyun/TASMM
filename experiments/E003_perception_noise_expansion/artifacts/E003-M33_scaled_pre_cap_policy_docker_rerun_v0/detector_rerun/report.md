# E003-M22 Frame Scaling Projection Diagnostic

## Status

frame_scaling_projection_diagnostic_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 8
- Max frames per scan: 24
- Max predictions per frame: 60
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Scanned frames: 192
- Frames with written predictions: 192
- Raw predictions: 67639
- Written predictions: 3414
- Skipped no-depth predictions: 1827
- Validator errors/warnings: 0 / 0
- Matched proposal rows: 204
- False-positive proposal rows: 3210
- Proposal precision smoke: 0.05975395430579965
- Scan target recall smoke: 0.5930232558139535
- Label-overlap target recall smoke: 0.5947521865889213
- Mean matched centroid error m: 0.5345816127450981
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M22 supports separating frame coverage, projection loss, and matching failure after removing the M20 early stop.
- E003-M22 does not support real RGB-D/open-vocabulary robustness because it is still a small diagnostic run, not a visibility-aware detector benchmark.

## 에이전트 추론

- If multi-frame recall remains low while raw predictions are abundant, the bottleneck is likely projection/matching quality or prompt/threshold calibration rather than frame coverage alone.
- The next unit should choose between projection calibration and scaling to more scans based on this diagnostic.

## 사용자 판단 필요

- None for E003-M22 diagnostic.
