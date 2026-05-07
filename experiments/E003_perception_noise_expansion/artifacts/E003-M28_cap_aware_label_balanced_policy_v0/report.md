# E003-M28 Cap Aware Label Balanced Policy

## Status

cap_aware_label_balanced_policy_smoke_ready

## 사실

- Input proposal rows: 1440
- Enabled prompt labels: 85
- Label-cleaned proposal rows: 1433
- Dropped non-prompt label rows: 7
- Dropped not-scan-prompt label rows: 0
- Baseline proposal rows: 1440
- Baseline matched target rows: 39
- Baseline false-positive rows: 1401
- Baseline precision: 0.027083333333333334
- Selected score mode: `confidence`
- Selected per-scan-label cap: 24
- Selected spatial consolidation radius m: 0.5
- Selected proposal rows: 407
- Selected matched target rows: 32
- Selected false-positive rows: 375
- Selected precision: 0.07862407862407862
- Selected scan target recall: 0.32323232323232326
- Precision delta vs baseline: 0.05154074529074529
- False-positive reduction vs baseline: 1026
- Matched target delta vs baseline: -7
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M28 supports an artifact-replay diagnostic that label-balanced cap-aware ranking can reduce written-proposal false positives under the M26 denominator.
- E003-M28 does not support a final real RGB-D/open-vocabulary robustness claim because the policy is replayed after M26's detector cap, not inside the detector before cap.

## 에이전트 추론

- The selected replay policy should be treated as a pre-cap Docker integration candidate only if the recall loss is explicitly reported.
- The next Docker run should apply this policy before the per-frame/global cap so raw detector candidates are ranked before truncation.

## 사용자 판단 필요

- None for E003-M28. Next recommended unit: `E003-M29 Docker pre-cap policy integration rerun gate`.
