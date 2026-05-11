# E003-M23 Proposal Consolidation Calibration

## Status

proposal_calibration_diagnostic_ready

## 사실

- Input proposal rows: 3414
- Sweep rows: 1188
- Baseline retained proposal rows: 3414
- Baseline matched target rows: 204
- Baseline proposal precision: 0.05975395430579965
- Baseline fixed label-overlap target recall: 0.5947521865889213
- Best full-match-preserving proposal precision: 0.05975395430579965
- Best full-match-preserving false-positive rows: 3210
- Selected confidence threshold: 0.0
- Selected min depth pixels: 0
- Selected NMS radius m: 0.0
- Selected score mode: `confidence`
- Selected retained proposal rows: 3414
- Selected matched target rows: 204
- Selected false-positive proposal rows: 3210
- Selected proposal precision: 0.05975395430579965
- Selected scan target recall: 0.5930232558139535
- Selected fixed label-overlap target recall: 0.5947521865889213
- Selected calibration F1: 0.10859728506787329
- Selection policy: `full_match_preserving`
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M23 supports a calibration/consolidation diagnostic over M22 detector proposals.
- E003-M23 does not support real perception robustness because the sweep is tuned on one scan and uses 3DSSG matching only for evaluation.

## 에이전트 추론

- A useful calibration gate should improve precision or false-positive count without collapsing matched target coverage.
- If the selected config mainly trades recall for precision, the next step should not scale to paper tables before a visibility-aware denominator or better detector prompts/NMS.

## 사용자 판단 필요

- None for E003-M23 diagnostic.
