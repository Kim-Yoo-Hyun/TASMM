# E003-M30 Pre Cap Policy Docker Rerun

## Status

pre_cap_policy_docker_rerun_pilot_ready

## 사실

- Docker build executed: True
- Docker run executed: True
- Candidate selection policy: `cap_aware_label_balanced_ranking_v0`
- Pre-cap policy applied: True
- Raw predictions: 9768
- Projected candidates: 9496
- Policy input candidates: 8969
- Spatial consolidated candidates: 848
- Final written predictions: 830
- Max predictions reached after policy: False
- Validator error / warning rows: 0 / 0
- M26 matched target rows: 39
- M30 matched target rows: 48
- Matched target delta vs M26: 9
- M26 false-positive rows: 1401
- M30 false-positive rows: 782
- False-positive delta vs M26: -619
- M26 proposal precision: 0.027083
- M30 proposal precision: 0.057831
- Precision delta vs M26: 0.030748
- Selected calibration retained / matched / false-positive rows: 830 / 48 / 782
- Selected calibration precision: 0.057831
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M30 supports saying the pre-cap policy can be executed inside the Docker detector runner under the fixed M26 pilot conditions.
- E003-M30 does not support a final real RGB-D/open-vocabulary robustness claim because this is still a two-scan pilot and needs failure/recall tradeoff analysis.

## 에이전트 추론

- The key comparison is M30 vs M26, not M30 alone, because M26 fixed prompt coverage but was cap/false-positive dominated.
- If M30 reduces false positives while preserving most M26 matches, the next unit should analyze which labels/frames/targets account for the remaining recall loss.

## 사용자 판단 필요

- None for E003-M30. Next recommended unit: `E003-M31 pre-cap policy failure/recall tradeoff analysis`.
