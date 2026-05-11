# E003-M39 Temporal-Spatial Support Instrumentation Gate

Implementation unit: `E003-M39_temporal_spatial_support_instrumentation_gate_v0`.

## Decision

- Status: `temporal_spatial_support_instrumentation_gate_ready`
- Selected route: `docker_runner_pre_consolidation_support_evidence_v0`
- M38 selected route: `temporal_spatial_evidence_instrumentation_required`
- Deterministic post-processing route ready: `false`
- Next recommended unit: `E003-M40 temporal-spatial support runner implementation smoke`

## Rationale

- M38 showed that the current dev-selected post-hoc support filter does not transfer well enough to heldout scans.
- The current artifacts preserve final selected proposals, not the cleaned candidate pool before spatial consolidation and caps.
- Therefore support evidence must be instrumented in the Docker runner before candidates are removed by consolidation or final caps.

## Insertion Point

- Insertion id: `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`
- After line: `312`
- Before line: `316`
- Ready: `true`

## Field Contract

- Support policy id: `temporal_spatial_support_evidence_v0`
- Compute stage: `after_prompt_label_cleanup_before_spatial_consolidation_and_caps`
- Group key: `['scan_id', 'label_canonical']`
- Radii: `[0.75, 1.0, 1.5, 2.0]`

Required per-row fields when enabled include `support_evidence_policy`, `support_group_key`, `support_group_candidate_count`, `support_group_frame_count`, and radius-specific spatial, temporal, and neighbor-confidence fields.

## M40 Verification Commands

After the runner edit, run:

```bash
python experiments/E003_perception_noise_expansion/tools/run_m22_frame_scaling_diagnostics.py --out-dir experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0 --max-scans 1 --max-frames-per-scan 2 --max-labels 32 --max-predictions 400 --max-predictions-per-frame 20 --candidate-selection-policy cap_aware_label_balanced_ranking_v0 --selection-score-mode confidence_sqrt_depth --pre-cap-per-scan-label-cap 40 --pre-cap-spatial-consolidation-radius-m 0.5 --raw-candidate-collection-cap 20000 --support-evidence-policy temporal_spatial_support_evidence_v0 --support-evidence-radii-m 0.75,1.0,1.5,2.0
python experiments/E003_perception_noise_expansion/tools/validate_real_proposal_output.py --predictions experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/real_proposals.jsonl --summary experiments/E003_perception_noise_expansion/artifacts/E003-M40_temporal_spatial_support_runner_smoke_v0/validation_summary.json
```

## Claim Boundary

- This gate does not execute a new detector run.
- This gate does not make the real RGB-D/open-vocabulary robustness claim ready.
- It makes the runner-side instrumentation contract ready for M40.
