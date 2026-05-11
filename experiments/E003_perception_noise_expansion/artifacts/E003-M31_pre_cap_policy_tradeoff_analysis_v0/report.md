# E003-M31 Pre Cap Policy Tradeoff Analysis

## Status

pre_cap_policy_tradeoff_analysis_ready

## 사실

- Evaluated scans: 2
- Scan eval target rows: 99
- M26 / M28 / M30 matched target rows: 39 / 32 / 48
- M30 gains/losses vs M26: 15 / 6
- Stable matched / stable missed: 33 / 45
- M26 / M28 / M30 false-positive rows: 1401 / 375 / 782
- M26 / M28 / M30 proposal precision: 0.027083333333333334 / 0.07862407862407862 / 0.05783132530120482
- M30 written proposals: 830
- M30 depth-consistent visible-proxy target rows: 35
- M30 missed visible-proxy target rows: 5
- Top gain labels: clothes:+2, kitchen cabinet:+2, backpack:+1, bag:+1, blanket:+1
- Top loss labels: plant:-6
- Top false-positive labels: table:47, chair:42, box:41, light:41, plant:38
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M31 supports a two-scan diagnostic claim that the pre-cap policy improves the M26 detector pilot's recall/precision tradeoff.
- E003-M31 does not support a final real RGB-D/open-vocabulary robustness claim because scale, true visibility, and remaining false positives are unresolved.

## 에이전트 추론

- M30 is better than M26 on matched targets and false positives, while M28 remains a high-precision post-hoc replay with lower matched-target count.
- The next scaling step is reasonable only after visible-proxy misses and top false-positive labels are reviewed, because the remaining error is label- and visibility-structured.

## 사용자 판단 필요

- None for E003-M31. Next recommended unit: `E003-M32 scaled pre-cap policy rerun gate`.
