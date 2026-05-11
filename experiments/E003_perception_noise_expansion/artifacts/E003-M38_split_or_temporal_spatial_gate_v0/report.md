# E003-M38 Split Or Temporal-Spatial Gate

## Status

split_or_temporal_spatial_gate_ready

## 사실

- Split feasibility rows: 210
- Best split uncovered heldout target label count: 7
- Best split uncovered heldout target rows: 7
- Stronger split feasible with current 8 scans: False
- Support policy rows: 244
- Selected dev support policy: `spatial_support_or_rank_guard_r1p5m_min3_rank_guard_le_12`
- Selected heldout matched targets: 89
- Selected heldout false-positive rows: 1406
- Selected heldout retention: 0.9175257731958762
- Selected heldout precision: 0.05953177257525084
- Heldout oracle support policy: `temporal_support_or_rank_guard_r0p75m_min3_rank_guard_le_20`
- Heldout oracle matched targets: 95
- Heldout oracle false-positive rows: 1336
- Heldout oracle precision: 0.06638714185883997
- Selected route: `temporal_spatial_evidence_instrumentation_required`
- Runner integration recommended: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M38 can support a route decision after M37 heldout transfer failure.
- E003-M38 does not support a final real RGB-D/open-vocabulary robustness claim.
- E003-M38 does not support Docker runner integration unless heldout support-policy retention and false-positive reduction both pass.

## 에이전트 추론

- If no split covers heldout target labels with dev matched examples, stronger split design is not enough with the current 8-scan artifact.
- If support-policy oracle is better than dev-selected transfer, the next route should instrument richer temporal/spatial evidence rather than deploy the current post-hoc filter.

## 사용자 판단 필요

- None for E003-M38. Next recommended unit: `E003-M39 temporal-spatial support instrumentation gate`.
