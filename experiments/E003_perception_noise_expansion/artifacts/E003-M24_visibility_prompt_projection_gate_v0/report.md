# E003-M24 Visibility Prompt Projection Gate

## Status

visibility_prompt_projection_gate_ready

## 사실

- Evaluated scans: 1
- Evaluated frames: 6
- Scan-level evaluation target rows: 51
- Active M22 prompt target rows: 32
- Prompt-not-active target rows: 19
- Centroid frustum-visible target rows: 8
- Depth-valid projected target rows: 7
- Depth-consistent visible-proxy target rows: 5
- M22 matched target rows: 7
- M23 selected matched target rows: 4
- M22 matched outside centroid frustum proxy rows: 2
- Detector/threshold missed depth-consistent visible target rows: 0
- M22 recall over scan denominator: 0.13725490196078433
- M22 recall over active prompt denominator: 0.21875
- M22 recall over depth-consistent visible proxy denominator: 1.0
- M23 recall over depth-consistent visible proxy denominator: 0.6
- Dominant bottleneck: not_centroid_projected_in_sampled_frames
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M24 supports a diagnostic separation between active-prompt coverage, visibility-proxy denominator, depth/projection support, and detector matching.
- E003-M24 does not support real RGB-D/open-vocabulary robustness because the visibility proxy uses target centroids and one scan's sampled frames.

## 에이전트 추론

- If many scan-level targets are not active prompts or not visible in sampled frames, scan-level recall is not an appropriate detector denominator.
- M22 recall should be judged against active-prompt and visibility-aware denominators before interpreting low scan-level recall as detector failure.
- M23 improves precision but drops matched targets, so the next detector step should use match-preserving calibration with a visibility-aware denominator.

## 사용자 판단 필요

- None for E003-M24 diagnostic.
