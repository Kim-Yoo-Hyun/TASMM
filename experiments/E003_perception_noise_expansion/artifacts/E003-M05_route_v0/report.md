# E003-M05 Route Selection

## Status

controlled_stress_selected

## 사실

- Query rows: 294
- Local sequence scan count: 8
- Local RGB-D triplet scan count: 8
- Query rows with rescan RGB-D ready: 0
- Query rows with real RGB-D proposal ready: 0
- Query rows with real open-vocabulary proposal ready: 0
- Proposal output files found: 0
- Selected route: `controlled_annotation_proxy_stress`
- Selected profile: `annotation_proposal_dropout_v0`
- Docker rule active for real implementation: True
- Docker required for selected route: False
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M05_route_v0`

## Blockers

- No detector/proposal output files found under local_dataset.
- No current E001 query row has a detector/open-vocabulary proposal source.
- No current E001 query row has rescan RGB-D triplets ready for detector execution.
- Real detector/open-vocabulary implementation must use Docker under docs/experiments.md.

## Selected Controlled Profile

- Profile: `annotation_proposal_dropout_v0`
- Role: `controlled_proposal_recall_stress`
- Target drop rate: 0.15
- Non-target candidate drop rate: 0.25
- Required denominators: `all_rows`, `target_retained_eval`, `target_dropped_eval`
- Next executable unit: `E003-M06_annotation_proposal_dropout_v0`

## 논문 주장

- E003-M05 supports choosing the next controlled proposal-recall stress route after real proposal-source audit.
- E003-M05 does not support real RGB-D or open-vocabulary robustness because no detector/proposal source is ready.

## 에이전트 추론

- `annotation_proposal_dropout_v0` is the next profile because M04 already tested rank-only noise and explicitly found no target-drop condition.
- Target-drop stress is closer to detector proposal recall failure than false-positive or centroid-only noise.
- Real detector/open-vocabulary implementation should be a Dockerized paper-body experiment, not an ad hoc local script.

## 사용자 판단 필요

- None for M05 route selection. Continue to E003-M06 controlled proposal-dropout implementation unless real proposal data is staged first.

## Outputs

- `proposal_source_rows.jsonl`
- `route_decision.json`
- `controlled_profile_contract.json`
- `coverage.json`
- `report.md`
