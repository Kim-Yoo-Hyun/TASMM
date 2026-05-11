# E003-M33 Scaled Pre Cap Policy Docker Rerun

## Status

scaled_pre_cap_policy_docker_rerun_ready

## 사실

- Selected route: `staged_8scan_24frame_pre_cap_scaled_pilot`
- Docker build executed: True
- Docker run executed: True
- Estimated detector wall time seconds: 3333
- Evaluated scans / frames: 8 / 192
- Evaluation target rows: 344
- Raw predictions: 67639
- Projected candidates: 65812
- Policy input candidates: 60435
- Spatial consolidated candidates: 4284
- Final prediction rows: 3414
- Raw candidate cap reached: False
- Max predictions reached after policy: False
- Validator errors/warnings: 0 / 0
- Matched target rows: 204
- False-positive proposal rows: 3210
- Proposal precision: 0.05975395430579965
- Scan target recall: 0.5930232558139535
- Depth-consistent visible-proxy target rows: 154
- Recall over depth-consistent visible-proxy denominator: 0.9155844155844156
- Detector/threshold missed visible-proxy target rows: 13
- Calibration changed selected proposals: False
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M33 supports that the Dockerized `cap_aware_label_balanced_ranking_v0` route can scale from the two-scan pilot to 8 staged `3RScan` scans under a fixed output schema.
- E003-M33 supports a scaled diagnostic result, not a final real RGB-D/open-vocabulary robustness claim.
- E003-M33 does not support a deployable perception/search claim because false-positive load remains high and visibility is still a centroid/depth proxy.

## 에이전트 추론

- The scaled run improves the denominator size enough for label-level failure analysis, but proposal precision remains low.
- Match-preserving calibration selected the baseline-like config, so simple confidence/depth/NMS filtering did not reduce false positives without risking matched target loss.
- The next unit should analyze M33 false-positive labels, visible-proxy misses, and M31 blocker resolution before any paper-table claim.

## 사용자 판단 필요

- None for E003-M33. Next recommended unit: `E003-M34 scaled pre-cap failure and label analysis`.
