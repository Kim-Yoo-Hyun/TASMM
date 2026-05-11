# E003-M29 Pre Cap Policy Integration Gate

## Status

pre_cap_policy_integration_gate_ready

## 사실

- Runner: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/docker/real_proposals/run_rgbd_ov_proposals.py`
- Detector result loop line: 351
- Current global cap check line: 355
- Current per-frame cap check line: 358
- Final row append line: 375
- Final JSONL write line: 422
- Selected policy id: `cap_aware_label_balanced_ranking_v0`
- Selected score mode: `confidence`
- Selected per-scan-label cap: 24
- Selected spatial consolidation radius m: 0.5
- Runner args contract ready: True
- Output contract ready: True
- Docker rerun plan ready: True
- Runner code updated in M29: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M29 supports a reproducible implementation contract for moving `cap_aware_label_balanced_ranking_v0` before detector output caps.
- E003-M29 does not support a detector-result claim because it does not rerun Docker detector inference.

## 에이전트 추론

- The current cap site is inside the detector result loop, so post-hoc replay can miss candidates that were truncated before M28 saw them.
- M30 should implement candidate collection first and apply `max_predictions` only after label cleanup, scoring, spatial consolidation, and per-scan-label capping.

## 사용자 판단 필요

- None for M29. Next is implementing the runner and host-wrapper pass-through, then rerunning the fixed M26 pilot under the pre-cap policy.
