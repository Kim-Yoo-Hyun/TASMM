# E003-M36 Recall Preserving Suppression Sweep

## Status

recall_preserving_suppression_sweep_ready

## 사실

- Input proposal rows: 3414
- Evaluation target rows: 344
- Sweep policy rows: 56
- Baseline matched targets: 204
- Baseline false-positive rows: 3210
- Baseline precision: 0.05975395430579965
- Baseline visible-proxy recall: 0.9155844155844156
- Selected deployable 95pct policy: `global_rank_cap_le_20`
- Selected deployable 95pct matched targets: 195
- Selected deployable 95pct false-positive rows: 2819
- Selected deployable 95pct precision: 0.06469807564698075
- Selected diagnostic policy: `labelwise_rank_cap_oracle_retain_0p95`
- Selected diagnostic matched targets: 204
- Selected diagnostic false-positive rows: 1585
- Selected diagnostic precision: 0.11403018446059252
- M35 selected probe after rematching: `visible_miss_guarded_labelwise_rank_cap_v0`
- M35 selected probe matched targets / false positives: 204 / 1782
- Split validation required: True
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M36 supports an offline suppression sweep over the M33 real-proposal artifacts.
- E003-M36 supports a diagnostic ceiling for labelwise rank-cap suppression, not a final method claim.
- E003-M36 does not support a paper-table real RGB-D/open-vocabulary robustness claim because policy selection still needs split validation.

## 에이전트 추론

- Deployable fixed hyperparameters give a modest recall-preserving gain, while labelwise diagnostic caps show a much larger ceiling.
- The next step should validate cap selection on a dev/held-out split before adding the policy to the Docker runner.

## 사용자 판단 필요

- None for E003-M36. Next recommended unit: `E003-M37 suppression split validation gate`.
