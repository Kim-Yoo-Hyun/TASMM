# E003-M35 False Positive Suppression Route

## Status

false_positive_suppression_route_ready

## 사실

- Baseline proposal rows: 3414
- Baseline matched targets: 204
- Baseline false-positive rows: 3210
- Baseline precision: 0.05975395430579965
- Top false-positive labels: plant 176, shelf 133, chair 129, sofa 117, table 116, box 111, cabinet 110, lamp 106
- Suppression priority labels: chair priority_for_rank_cap_suppression, table priority_for_rank_cap_suppression, box priority_for_rank_cap_suppression, cabinet priority_for_rank_cap_suppression, lamp priority_for_rank_cap_suppression, plant guard_recall_before_suppressing
- Selected route: `recall_preserving_rank_cap_sweep_v0`
- Selected probe policy: `visible_miss_guarded_labelwise_rank_cap_v0`
- Selected probe proposal rows: 1986
- Selected probe matched targets: 204
- Selected probe false-positive rows: 1782
- Selected probe precision: 0.1027190332326284
- Selected probe false-positive reduction vs M33: 1428
- Selected probe matched target retention: 1.0
- Docker run executed: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M35 supports selecting a recall-preserving suppression sweep route for the M33 real-proposal artifacts.
- E003-M35 does not support a final suppression method claim because it does not execute the selected M36 sweep or a held-out validation.
- E003-M35 does not support a paper-table real RGB-D/open-vocabulary robustness claim.

## 에이전트 추론

- Rank-cap suppression is the first route because it uses fields already present in M33 outputs and can be tested without another long Docker run.
- The selected probe is promising as a ceiling, but any cap selected using M33 match labels is diagnostic until validated on a split that did not choose the caps.
- Confidence/depth-only filtering should stay as a baseline arm, not the primary route.

## 사용자 판단 필요

- None for E003-M35. Next recommended unit: `E003-M36 recall-preserving suppression sweep smoke`.
