# E003-M32 Scaled Pre Cap Rerun Gate

## Status

scaled_pre_cap_rerun_gate_ready

## 사실

- Selected route: `staged_8scan_24frame_pre_cap_scaled_pilot`
- Staged scans: 8
- Selected scans: 8
- Selected frame budget: 192 / 459
- Evaluation target rows in selected scope: 344
- Max labels: 32
- Max predictions: 10000
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Per-scan-label cap: 24
- Spatial consolidation radius m: 0.5
- Estimated raw predictions: 78144
- Estimated final prediction rows: 6640
- M31 blockers tracked: 7
- Docker command ready: True
- Docker run executed: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M32 supports fixing a scaled rerun contract for the pre-cap policy.
- E003-M32 does not support a detector-result claim because it does not execute Docker inference.

## 에이전트 추론

- The next Docker run should scale across all 8 staged scans but keep a 24-frame-per-scan budget to control CPU cost before full-frame evaluation.
- M31 blockers should be treated as required post-rerun diagnostics, especially `plant` recall loss and table/chair/box/light/plant false positives.
- A paper-table claim remains blocked until the scaled rerun and its failure analysis are complete.

## 사용자 판단 필요

- None for E003-M32. Next recommended unit: `E003-M33 scaled pre-cap policy Docker rerun`.
