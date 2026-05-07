# E003-M22 Frame Scaling Projection Diagnostic

## Status

frame_scaling_projection_diagnostic_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 1
- Max frames per scan: 6
- Max predictions per frame: 20
- Scanned frames: 6
- Frames with written predictions: 6
- Raw predictions: 1664
- Written predictions: 120
- Skipped no-depth predictions: 15
- Validator errors/warnings: 0 / 0
- Matched proposal rows: 7
- False-positive proposal rows: 113
- Proposal precision smoke: 0.058333333333333334
- Scan target recall smoke: 0.13725490196078433
- Label-overlap target recall smoke: 0.21875
- Mean matched centroid error m: 0.40222285714285716
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
