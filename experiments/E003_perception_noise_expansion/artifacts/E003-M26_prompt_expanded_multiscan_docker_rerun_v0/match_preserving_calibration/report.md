# E003-M23 Proposal Consolidation Calibration

## Status

proposal_calibration_diagnostic_ready

## 사실

- Input proposal rows: 1440
- Sweep rows: 1188
- Baseline retained proposal rows: 1440
- Baseline matched target rows: 39
- Baseline proposal precision: 0.027083333333333334
- Baseline fixed label-overlap target recall: 0.4148936170212766
- Best full-match-preserving proposal precision: 0.028931750741839762
- Best full-match-preserving false-positive rows: 1309
- Selected confidence threshold: 0.0
- Selected min depth pixels: 100
- Selected NMS radius m: 0.0
- Selected score mode: `confidence`
- Selected retained proposal rows: 1348
- Selected matched target rows: 39
- Selected false-positive proposal rows: 1309
- Selected proposal precision: 0.028931750741839762
- Selected scan target recall: 0.3939393939393939
- Selected fixed label-overlap target recall: 0.4148936170212766
- Selected calibration F1: 0.054091539528432736
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
