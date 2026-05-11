# E003-M51 Post-M50 Route Decision

## Status

post_m50_route_decision_ready

## 사실

- M50 selected route: `do_not_scale_grounded_sam_yet`.
- M50 weak/hard positive: False / False.
- M50 bbox-depth matched / FP / precision: 2 / 29 / 0.06451612903225806.
- M50 mask-depth matched / FP / precision: 1 / 23 / 0.041666666666666664.
- Selected immediate route: `targeted_mask_failure_analysis_first`.
- Next recommended unit: `E003-M52 Grounded-SAM mask failure analysis`.

## Route Ranking

- `targeted_mask_failure_analysis_first`: score 43, type `artifact_local_diagnostic`, next `E003-M52 Grounded-SAM mask failure analysis`.
- `bbox_depth_continuation_after_mask_check`: score 34, type `current_best_route_continuation`, next `E003-M52 bbox-depth continuation and failure-boundary repair gate`.
- `openmask3d_feasibility_after_mask_failure`: score 24, type `external_3d_instance_baseline`, next `E003-M52 OpenMask3D scene-format feasibility gate`.

## 논문 주장

- E003-M51 does not create a paper result claim.
- It fixes the next route after a negative `Grounded-SAM` same-subset comparison.
- Real RGB-D/open-vocabulary robustness remains unsupported.

## 에이전트 추론

- Do not scale `Grounded-SAM` now because M50 is negative.
- Do not jump straight to `OpenMask3D` before checking whether M50 exposed a simple mask projection/filtering bug.
- A short artifact-local mask failure analysis is the cheapest way to defend abandoning or repairing the `Grounded-SAM` route.

## 사용자 판단 필요

- None if the immediate diagnostic route is accepted.
