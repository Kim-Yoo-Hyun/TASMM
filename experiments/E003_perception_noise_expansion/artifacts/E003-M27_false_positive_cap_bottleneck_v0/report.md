# E003-M27 False Positive Cap Bottleneck

## Status

false_positive_cap_bottleneck_ready

## 사실

- Input unit: `E003-M26_prompt_expanded_multiscan_docker_rerun_v0`
- Evaluated scans / frames: 2 / 24
- Raw / written predictions: 9768 / 1440
- Skipped no-depth predictions: 56
- Lower-bound cap/post-depth rejected rows: 8272
- Frames saturated by per-frame cap: 24 / 24
- Baseline proposal precision: 0.027083
- Selected match-preserving precision: 0.028932
- Baseline / selected matched target rows: 39 / 39
- Baseline / selected false-positive rows: 1401 / 1309
- Calibration false-positive reduction: 92
- Same-label over-threshold false-positive rows after selected calibration: 1302
- No-same-label false-positive rows after selected calibration: 7
- No-target labels with detector predictions: 2
- Top selected false-positive labels: box=188, chair=185, table=118, plant=117, light=63, sofa=56, picture=53, cabinet=53
- Visibility bottleneck counts: {'depth_inconsistent_or_occluded_centroid_proxy': 5, 'detector_or_threshold_missed_visible_target': 13, 'not_centroid_projected_in_sampled_frames': 38, 'projection_has_no_depth_support': 4, 'retained_match_after_calibration': 39}
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M27 supports a diagnostic claim that the current real-detector pilot is blocked by cap pressure and false-positive domination, not by prompt coverage.
- E003-M27 does not support real RGB-D/open-vocabulary robustness or a paper-table detector benchmark result.

## 에이전트 추론

- Wider scaling should wait because every sampled frame saturates the per-frame cap and selected precision remains near 0.03.
- Threshold/depth/NMS calibration alone is insufficient because it preserves recall but barely changes precision.
- Next detector policy should be `cap_aware_label_balanced_ranking_v0`: label mapping cleanup, pre-cap ranking, label-balanced caps, and same-label spatial consolidation.

## 사용자 판단 필요

- None for E003-M27. Next recommended unit: `E003-M28 cap-aware label-balanced detector policy smoke`.
