# E003-M24 Visibility Prompt Projection Gate

## Status

visibility_prompt_projection_gate_ready

## 사실

- Evaluated scans: 2
- Evaluated frames: 24
- Scan-level evaluation target rows: 99
- Active M22 prompt target rows: 99
- Prompt-not-active target rows: 0
- Centroid frustum-visible target rows: 48
- Depth-valid projected target rows: 41
- Depth-consistent visible-proxy target rows: 35
- M22 matched target rows: 39
- M23 selected matched target rows: 39
- M22 matched outside centroid frustum proxy rows: 13
- Detector/threshold missed depth-consistent visible target rows: 13
- M22 recall over scan denominator: 0.3939393939393939
- M22 recall over active prompt denominator: 0.3939393939393939
- M22 recall over depth-consistent visible proxy denominator: 0.6285714285714286
- M23 recall over depth-consistent visible proxy denominator: 0.6285714285714286
- Dominant bottleneck: retained_match_after_calibration
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
