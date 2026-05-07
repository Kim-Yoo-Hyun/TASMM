# E003-M23 Proposal Consolidation Calibration

## Status

proposal_calibration_diagnostic_ready

## 사실

- Input proposal rows: 120
- Sweep rows: 1188
- Baseline retained proposal rows: 120
- Baseline matched target rows: 7
- Baseline proposal precision: 0.058333333333333334
- Baseline fixed label-overlap target recall: 0.21875
- Best full-match-preserving proposal precision: 0.07216494845360824
- Best full-match-preserving false-positive rows: 90
- Selected confidence threshold: 0.3
- Selected min depth pixels: 500
- Selected NMS radius m: 1.0
- Selected score mode: `confidence`
- Selected retained proposal rows: 12
- Selected matched target rows: 4
- Selected false-positive proposal rows: 8
- Selected proposal precision: 0.3333333333333333
- Selected scan target recall: 0.0784313725490196
- Selected fixed label-overlap target recall: 0.125
- Selected calibration F1: 0.18181818181818182
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
