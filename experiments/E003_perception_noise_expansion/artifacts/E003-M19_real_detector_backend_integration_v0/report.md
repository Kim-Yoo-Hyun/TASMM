# E003-M19 Real Detector Backend Integration

## Status

real_detector_backend_contract_ready

## 사실

- Selected backend: `groundingdino_rgbd_backproject_v0`
- Docker image tag: `research2/real-smoke`
- Docker build executed: True
- Docker backend contract smoke executed: True
- Backend contract ready: True
- RGB-D frame triplets ready: 459
- RGB-D frame triplets missing: 0
- Manifest rows: 8
- Prompt labels: 98
- Detector backend integrated: False
- Detector predictions ready: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M19 supports selecting a concrete real-detector backend contract and connecting it to the Docker runner.
- E003-M19 supports saying that E003-M17 RGB-D frames, depth, poses, and prompts are consumable by the selected backend route.
- E003-M19 does not support detector performance or real perception robustness because model inference is not integrated yet.

## 에이전트 추론

- `groundingdino_rgbd_backproject_v0` is a practical first backend contract because it separates open-vocabulary 2D detection from RGB-D 3D projection.
- The contract explicitly blocks evaluation-only 3DSSG instance ids from detector inference.
- The next unit should add model dependencies and run a small non-empty detector prediction smoke.

## 사용자 판단 필요

- None for E003-M19. Next is detector dependency/model smoke.
