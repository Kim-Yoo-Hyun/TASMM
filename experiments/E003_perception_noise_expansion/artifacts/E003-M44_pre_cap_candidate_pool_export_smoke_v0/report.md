# E003-M44 Pre-Cap Candidate-Pool Export And Replay Smoke

## Status

pre_cap_candidate_pool_replay_smoke_ready

## Facts

- Docker smoke status: `pre_cap_candidate_pool_export_smoke_ready`.
- Candidate pool export ready: True.
- Candidate pool rows: 629.
- Runner score mode: `confidence_sqrt_depth_support_temporal_v0`.
- Runner selected rows: 95.
- Offline replay selected rows: 95.
- Ordered reproduction match: True.
- Set reproduction match: True.
- Validator errors/warnings: 0 / 0.
- Paper-table command ready: False.
- Real RGB-D/open-vocabulary claim ready: False.

## Paper Claim

- E003-M44 supports a short reproducibility smoke for replayable pre-cap proposal candidates.
- E003-M44 does not support final real RGB-D/open-vocabulary robustness because it is not scaled heldout evidence.

## Agent Inference

- The candidate-pool export gives a stable substrate for score-mode ablations without repeating detector inference.
- The next scaled unit can export one 8-scan candidate pool, then compare support-aware scoring offline.

## User Decision Needed

- None for E003-M44.
