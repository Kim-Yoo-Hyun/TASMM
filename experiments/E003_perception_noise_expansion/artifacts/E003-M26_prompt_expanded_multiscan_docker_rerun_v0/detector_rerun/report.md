# E003-M22 Frame Scaling Projection Diagnostic

## Status

frame_scaling_projection_diagnostic_ready

## 사실

- Docker build executed: True
- Docker frame-scaling run executed: True
- Max scans: 2
- Max frames per scan: 12
- Max predictions per frame: 60
- Scanned frames: 24
- Frames with written predictions: 24
- Raw predictions: 9768
- Written predictions: 1440
- Skipped no-depth predictions: 56
- Validator errors/warnings: 0 / 7
- Matched proposal rows: 39
- False-positive proposal rows: 1401
- Proposal precision smoke: 0.027083333333333334
- Scan target recall smoke: 0.3939393939393939
- Label-overlap target recall smoke: 0.4148936170212766
- Mean matched centroid error m: 0.4966466923076923
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
