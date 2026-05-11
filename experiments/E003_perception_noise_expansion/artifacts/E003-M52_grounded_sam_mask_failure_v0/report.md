# E003-M52 Grounded-SAM Mask Failure Analysis

## Status

grounded_sam_mask_failure_analysis_ready

## 사실

- Bbox-depth proposal rows: 31.
- Mask-depth proposal rows: 24.
- Common candidate rows by scan/frame/raw index: 24.
- Bbox-only candidate rows: 7.
- Mask-only candidate rows: 0.
- `Grounded-SAM` skipped mask projection rows: 16.
- Bbox matched targets: 2.
- Mask matched targets: 1.
- Lost-by-mask targets: 1, labels {'plant': 1}.
- Matched-by-both targets: 1.
- Common same-target match-distance delta mask minus bbox: {'max': -0.018907, 'mean': -0.018907, 'median': -0.018907, 'min': -0.018907}.
- Aggregate M50 mean centroid error delta mask minus bbox: 0.3249025.
- Exact per-skipped mask reason observable from current artifacts: False.

## 논문 주장

- E003-M52 does not create a final paper claim.
- E003-M52 supports a route decision: the current `Grounded-SAM` mask-depth path should not be scaled as-is.
- Real RGB-D/open-vocabulary robustness remains unsupported.

## 에이전트 추론

- Target loss primary cause: `mask_projection_candidate_dropout_before_matching`.
- Centroid worsening primary cause: `match_set_composition_after_easy_target_dropout`.
- False-positive interpretation: `fewer_rows_without_precision_gain`.
- The M50 centroid degradation is not evidence that the common matched target became worse under mask-depth; the common matched target is slightly better under mask-depth, but the easy bbox-depth `plant` match was dropped before matching.
- Because the exact skipped-mask reason is not recorded, the current artifact can defend stopping the scaled `Grounded-SAM` route but cannot prove whether the failure is SAM mask absence, low valid mask depth, or another per-candidate projection condition.
- Next recommended unit: `E003-M53 bbox-depth continuation and failure-boundary repair gate`.

## 사용자 판단 필요

- None if bbox-depth continuation is accepted as the next immediate route. `OpenMask3D` remains the next external 3D instance baseline candidate after the current bbox-depth route is stabilized.
