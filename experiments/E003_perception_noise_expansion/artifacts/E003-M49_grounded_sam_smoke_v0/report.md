# E003-M49 Grounded-SAM Docker/Model Smoke

## Status

grounded_sam_model_smoke_ready

## 사실

- Backend id: `grounded_sam_mask_backproject_v0`.
- GroundingDINO model id: `IDEA-Research/grounding-dino-tiny`.
- SAM model id: `facebook/sam-vit-base`.
- Docker build executed: True.
- Docker run executed: True.
- Prediction rows: 24.
- Mask geometry rows: 24.
- Rows with mask RLE: 24.
- Validator errors/warnings: 0 / 0.
- M21 matcher returncode: 0.
- Matched proposal rows: 1.
- False-positive proposal rows: 23.
- Proposal precision smoke: 0.041666666666666664.
- Paper-table command ready: False.
- Real RGB-D/open-vocabulary claim ready: False.

## 논문 주장

- E003-M49 supports only a short implementation smoke for `Grounded-SAM` mask-depth proposal rows.
- E003-M49 does not support final real RGB-D/open-vocabulary robustness or search/navigation claims.

## 에이전트 추론

- If this smoke is ready, the next defensible step is a same-subset comparison against the current bbox-depth `GroundingDINO` route.
- A positive same-subset result would still require heldout transfer and external baseline scaling before a paper-table claim.

## 사용자 판단 필요

- None for the smoke implementation if validator and M21 matcher pass.
