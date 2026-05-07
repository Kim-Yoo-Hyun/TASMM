# E003-M20 Detector Model Smoke

## Status

detector_model_smoke_ready

## 사실

- Selected backend: `groundingdino_rgbd_backproject_v0`
- Model id: `IDEA-Research/grounding-dino-tiny`
- Docker image tag: `research2/real-smoke`
- Docker build executed: True
- Docker model smoke executed: True
- Backend contract ready: True
- Model loaded: True
- Inference device: `cpu`
- Scanned frames: 1
- Prediction rows: 20
- Validator error rows: 0
- Validator warning rows: 0
- Non-empty detector prediction smoke ready: True
- Detector backend integrated: True
- Detector predictions ready: True
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M20 supports a Dockerized non-empty model prediction smoke for the selected real-detector route.
- E003-M20 supports saying that the selected backend can load dependencies, consume RGB-D sequence inputs, and emit schema-valid proposal rows.
- E003-M20 does not support real perception robustness or proposal-recall claims because outputs are not yet matched/evaluated against the target denominator.

## 에이전트 추론

- The next unit should match detector proposals to the M17 target denominator and report proposal recall, false positives, and centroid-localization error.
- M20 should stay a smoke gate, not a paper-table result.

## 사용자 판단 필요

- None for M20 if the smoke is non-empty and validator-clean.
