# E003-M21 Detector Proposal Matching

## Status

detector_matching_smoke_ready

## 사실

- Input prediction rows: 3414
- Evaluated scans: 8 / 8
- Scan-level evaluation target rows: 344
- Label-overlap target rows: 343
- Matched proposal rows: 204
- Matched target rows: 204
- Proposal precision smoke: 0.05975395430579965
- Scan target recall smoke: 0.5930232558139535
- Label-overlap target recall smoke: 0.5947521865889213
- False-positive proposal rows: 3210
- Mean matched centroid error m: 0.5345816127450981
- Matching threshold m: 1.0
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M21 supports a first detector-to-denominator matching gate for M20 proposal rows.
- E003-M21 does not support real RGB-D/open-vocabulary robustness because M20 only covers one sampled frame from one scan.
- E003-M21 can identify whether the current RGB-D backprojection and label mapping are plausible enough to scale.

## 에이전트 추론

- Low scan-level recall is expected at this stage because the M20 denominator is not visibility-filtered and only one frame was evaluated.
- The current useful signal is whether same-label proposals can be matched with reasonable centroid error and whether false positives dominate.
- The next unit should scale the detector run over more frames/scans or fix RGB-D projection before using this path in paper tables.

## 사용자 판단 필요

- None for E003-M21 smoke. The next step should be selected from scaling M20 inference or improving projection/matching quality.
