# E003-M37 Suppression Split Validation Gate

## Status

suppression_split_validation_gate_ready

## 사실

- Split protocol: `balanced_scan_4_4_v0`
- Dev scans: 4
- Heldout scans: 4
- Heldout baseline matched targets: 97
- Heldout baseline false-positive rows: 1523
- Heldout target labels without dev matched example: 24
- Selected candidate policy: `dev_selected_visible_miss_guarded_labelwise_rank_cap_v0`
- Selected candidate heldout matched targets: 81
- Selected candidate heldout false-positive rows: 1154
- Selected candidate heldout precision: 0.06558704453441296
- Selected candidate heldout retention: 0.8350515463917526
- Selected fixed policy: `global_rank_cap_le_22_selected_on_train`
- Heldout oracle policy: `heldout_oracle_visible_miss_guarded_labelwise_rank_cap_v0`
- Heldout oracle false-positive rows: 979
- Runner integration recommended: False
- Paper-table command ready: False
- Real RGB-D/open-vocabulary claim ready: False

## 논문 주장

- E003-M37 supports a split-validation gate for suppression policies over M33 real-proposal artifacts.
- E003-M37 does not support Docker runner integration if heldout recall-preserving false-positive reduction is weak.
- E003-M37 does not support a final real RGB-D/open-vocabulary robustness claim.

## 에이전트 추론

- The diagnostic labelwise ceiling should not be promoted unless dev-selected caps transfer to heldout scans.
- If heldout gains are weak, the next step should be stronger split design or temporal/spatial evidence rather than runner integration.

## 사용자 판단 필요

- None for E003-M37. Next recommended unit: `E003-M38 stronger split or temporal-spatial suppression gate`.
