# E003-M43 Support-Aware Scaled Rerun Route Gate

## Status

support_aware_scaled_rerun_route_gate_ready

## Facts

- M40 score mode: `confidence_sqrt_depth`.
- M42 score mode: `confidence_sqrt_depth_support_temporal_v0`.
- M42 support ready: True.
- M42 validator errors/warnings: 0 / 0.
- M42 vs M40 matched proposal delta: 0.
- M42 vs M40 false-positive delta: 0.
- M42 vs M40 precision delta: 0.0.
- M42 vs M40 common selected rows: 94.
- M42 vs M40 selected symmetric difference rows: 2.
- M42 vs M40 pre-cap rank changed common rows: 68.
- M42 vs M40 selection-score changed common rows: 89.
- Existing candidate-pool replay available: False.
- Selected route: `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- Immediate support-aware long rerun recommended: False.
- Runner edit required before next scaled run: True.
- Paper-table command ready: False.
- Real RGB-D/open-vocabulary claim ready: False.

## Paper Claim

- E003-M43 supports only a route decision for support-aware proposal evaluation.
- It does not support final real RGB-D/open-vocabulary robustness or a paper-table result.

## Agent Inference

- M42 is a valid runner smoke but does not improve proposal quality over M40 on the short artifact.
- The score is not entirely inert: selected rows and ranks change, so a scaled test is still meaningful.
- Existing artifacts cannot isolate support scoring because they do not preserve the pre-cap candidate pool.
- The next route should export the support-instrumented candidate pool and replay score modes offline before any long scaled claim.

## User Decision Needed

- None for the route gate.

## Next Unit

- E003-M44 pre-cap candidate-pool export and offline replay harness smoke.
- Candidate-pool contract: `pre_cap_candidate_pool_export_for_offline_replay_v0`.
