# E003-M12 Combined-Noise Route Decision

## Status

combined_controlled_route_selected

## 사실

- Ready annotation-proxy query rows: 294
- Real RGB-D proposal-ready rows: 0
- Real open-vocabulary proposal-ready rows: 0
- Proposal output files found: 0
- Selected route: `controlled_annotation_proxy_combined_stress`
- Selected profile: `annotation_combined_moderate_v0`
- Next action: `E003-M13_annotation_combined_moderate_v0`
- Docker required for selected route: False
- Docker required for real proposal route: True
- Output directory: `/home/yoohyun/research2/experiments/E003_perception_noise_expansion/artifacts/E003-M12_combined_noise_route_decision_v0`

## Input Evidence

- Dropout boundary rows: 7938
- Dropout target dropped rate: 0.087302
- False-positive boundary rows: 7938
- False-positive target pushed-down rows: 96
- Centroid-jitter boundary rows: 7938
- Centroid-jitter target exceeds threshold rows: 123
- Centroid-jitter significant `routine_fetch` identity/localization `SR`: 0.69697 / 0.606061

## Selected Combined Profile

- Profile: `annotation_combined_moderate_v0`
- Seed set: 61, 67, 71
- Score jitter sigma: 0.08
- Target drop rate: 0.1
- Non-target drop rate: 0.2
- False-positive candidates per row: 1 to 2
- Centroid planar sigma m: 0.18
- Max planar jitter m: 0.5

## Real Proposal Route

- Status: `blocked_not_selected_as_immediate_next`
- Reason for deferral: Current E001 query denominator has 0 real RGB-D proposal-ready rows, 0 real open-vocabulary proposal-ready rows, and 0 proposal output files; switching immediately would stop the E003 controlled-noise progression before the combined profile is measured.

## 논문 주장

- E003-M12 supports selecting `annotation_combined_moderate_v0` as the next controlled perception-like stress route.
- E003-M12 supports keeping real RGB-D/open-vocabulary claims blocked until Dockerized proposal generation and alignment are staged.
- E003-M12 does not itself support new metric results; it fixes the next implementation contract.

## 에이전트 추론

- The combined profile is the correct immediate next step because all individual controlled profiles now have separate boundaries.
- Switching immediately to real proposals would require Dockerized detector generation and a new proposal-to-3DSSG matching contract, while current ready rows remain 0.
- The combined profile should still be framed as annotation-proxy robustness, not real perception robustness.

## 사용자 판단 필요

- None for E003-M12. Continue to E003-M13 `annotation_combined_moderate_v0` implementation unless redirected to Dockerized real proposal staging.

## Outputs

- `input_evidence_summary.json`
- `route_decision.json`
- `combined_profile_contract.json`
- `real_proposal_route_requirements.json`
- `coverage.json`
- `report.md`
