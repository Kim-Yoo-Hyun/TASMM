# E003-M26 Prompt Expanded Multiscan Docker Rerun

## Status

prompt_expanded_multiscan_docker_rerun_pilot_ready

## 사실

- Docker build executed: True
- Docker run executed: True
- Image/server route: `research2/real-smoke`, Docker server 29.4.0
- Evaluated scans / frames: 2 / 24
- Run config: max scans 2, max frames per scan 12, max labels 32, max predictions 1440
- Raw / written predictions: 9768 / 1440
- Raw-to-written rate: 0.147420
- Not projected or capped predictions: 8272
- Max predictions reached: True
- Validator error / warning rows: 0 / 7
- Scan eval target rows: 99
- Active prompt target rows: 99
- Prompt-not-active target rows: 0
- Matched target rows: 39
- Scan target recall smoke: 0.393939
- Label-overlap target recall smoke: 0.414894
- Proposal precision smoke: 0.027083
- False-positive proposal rows: 1401
- Selected calibration retained / matched / false-positive rows: 1348 / 39 / 1309
- Selected calibration precision: 0.028932
- Depth-consistent visible-proxy target rows: 35
- Recall over depth-consistent visible-proxy denominator: 0.628571
- Detector/threshold missed visible-proxy target rows: 13
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M26 supports saying that the prompt-expanded Docker route can produce non-empty multi-scan RGB-D/open-vocabulary proposal artifacts under the fixed schema.
- E003-M26 supports saying that prompt coverage is no longer the immediate blocker for the two-scan pilot because prompt-not-active target rows are 0.
- E003-M26 does not support a paper-table real RGB-D/open-vocabulary robustness claim.

## 에이전트 추론

- The bottleneck shifted from prompt budget to proposal quality: recall improved over the earlier one-scan smoke, but proposal precision remains very low.
- The detector output is cap-limited, so the next unit should separate detector scoring, frame/label caps, projection loss, and false-positive consolidation before wider scaling.
- The match-preserving calibration preserves matched targets, but it does not solve the false-positive domination problem.

## 사용자 판단 필요

- None for E003-M26. Next recommended unit: `E003-M27 false-positive / cap bottleneck analysis gate`.
