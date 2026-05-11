# E003-M41 Support-Aware Selection Policy Gate

Implementation unit: `E003-M41_support_aware_selection_policy_gate_v0`.

## Decision

- Status: `support_aware_selection_policy_gate_ready`
- Selected score mode: `confidence_sqrt_depth_support_temporal_v0`
- Selected route: `support_aware_scoring_before_consolidation_and_final_rank`
- Next recommended unit: `E003-M42 support-aware selection runner smoke`

## Policy Contract

- Base score: `confidence * min(1, sqrt(depth_valid_pixel_count) / sqrt(5000))`
- Temporal factor: `min(1, support_temporal_neighbor_frame_count_r2p0m / 2)`
- Spatial factor: `min(1, support_spatial_neighbor_count_r1p0m / 8)`
- Selection score: `base_score * (1 + 0.25 * temporal_factor + 0.10 * spatial_factor)`

## Facts

- M40 support ready: `true`
- M40 prediction rows: 95
- M40 rows with support policy: 95
- M40 rows with spatial / temporal support: 93 / 58
- M40 matched / false-positive proposals: 5 / 90
- M40 proposal precision smoke: 0.05263157894736842

## Claim Boundary

- This gate does not execute Docker.
- This gate does not prove support-aware selection improves proposal quality.
- This gate blocks a long rerun until M42 implements the selected score mode and passes a short smoke.
