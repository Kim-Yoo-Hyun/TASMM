# E003-M46 Score Redesign Or External Baseline Gate

## Status

score_redesign_or_external_gate_ready

## Facts

- Candidate pool rows: 60435.
- Swept policy rows: 12.
- Hard pass policy count: 0.
- Weak positive policy count: 0.
- Selected route: `external_proposal_baseline_gate_first`.
- Next recommended unit: `E003-M47 external proposal/mapping baseline feasibility gate`.

## Top Policies

- `confidence`: matched 204, FP 3210, precision 0.05975395430579965, hard False, weak False.
- `confidence_sqrt_depth`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `support_tiebreak_eps`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `rank_guard_12_weak_support`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `rank_guard_24_weak_support`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `density_penalty_0p01`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `density_penalty_0p03`: matched 198, FP 3209, precision 0.05811564426181391, hard False, weak False.
- `spatial_penalty_temporal_boost`: matched 198, FP 3210, precision 0.058098591549295774, hard False, weak False.

## Paper Claim

- E003-M46 does not create a new paper claim.
- It decides whether M45 failure is repairable by a local score redesign before moving to external baselines.

## Agent Inference

- If no hard/weak positive policy appears in this bounded sweep, the current support evidence is not discriminative enough as a main score signal.
- In that case, top-tier progress should shift toward external proposal/mapping baselines or richer support evidence, not a stale-memory bridge claim.

## User Decision Needed

- None for this gate; the next unit follows the selected route.
