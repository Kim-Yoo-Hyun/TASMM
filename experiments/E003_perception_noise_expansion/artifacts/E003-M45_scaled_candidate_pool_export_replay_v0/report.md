# E003-M45 Scaled Candidate-Pool Export And Support-Aware Replay

## Status

scaled_candidate_pool_replay_ready

## Facts

- Docker export status: `pre_cap_candidate_pool_export_smoke_ready`.
- Candidate pool rows: 60435.
- Runner selected rows: 3407.
- M33 matched / FP / precision: 204 / 3210 / 0.05975395430579965.
- `confidence`: matched 204, FP 3210, precision 0.05975395430579965.
- `confidence_sqrt_depth`: matched 198, FP 3209, precision 0.05811564426181391.
- `confidence_sqrt_depth_support_temporal_v0`: matched 196, FP 3211, precision 0.05752861755209862.
- Support-aware quality positive vs M33: False.
- Frozen contract verdict: `fail_redesign`.
- Validator errors/warnings: 0 / 0.
- Paper-table command ready: False.
- Real RGB-D/open-vocabulary claim ready: False.

## Paper Claim

- E003-M45 supports a scaled offline comparison over one shared detector candidate pool.
- It does not by itself support final real RGB-D/open-vocabulary robustness until heldout transfer and external baselines are added.

## Agent Inference

- The key result is whether support-aware scoring improves false-positive load without losing matched targets compared with the M33 confidence baseline.
- If support-aware scoring is not positive, the next step should be score redesign or external proposal baseline integration rather than a paper-table claim.

## User Decision Needed

- None for E003-M45 execution.
