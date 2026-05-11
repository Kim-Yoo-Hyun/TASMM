# E003-M48 Grounded-SAM Contract

## Status

grounded_sam_contract_ready

## 사실

- Selected backend id: `grounded_sam_mask_backproject_v0`.
- Contract id: `grounded_sam_mask_backprojection_contract_v0`.
- M47 selected route: `Grounded-SAM`.
- Existing schema id: `real_proposal_prediction_jsonl_v0`.
- Existing required fields preserved: True.
- Optional mask diagnostic fields added: 9.
- M45 bbox-depth confidence baseline: matched 204, false positives 3210, precision 0.05975395430579965.
- Docker/model smoke executed: False.
- Real RGB-D/open-vocabulary claim ready: False.

## 논문 주장

- E003-M48 does not create a new result claim.
- It fixes the contract needed to test whether mask-depth backprojection is better than box-depth backprojection for proposal geometry.

## 에이전트 추론

- `Grounded-SAM` is the correct first external implementation route because it minimally changes the current `GroundingDINO` runner while directly isolating the box-depth projection bottleneck.
- `OpenMask3D`, `ConceptGraphs`, and `HOV-SG` should remain later baselines after this proposal-quality bottleneck is understood.
- A successful M49 smoke would justify a same-subset comparison against the current M45/M33 box-depth baseline, but not a final robustness claim.

## 사용자 판단 필요

- None before E003-M49. The next unit should implement a short Docker/model smoke from this contract.
