# E003-M47 External Baseline Feasibility Gate

## Status

external_baseline_feasibility_gate_ready

## Facts

- Selected first route: `Grounded-SAM`.
- Next recommended unit: `E003-M48 Grounded-SAM mask-backprojection proposal smoke`.
- M46 selected route: `external_proposal_baseline_gate_first`.

## Route Ranking

- `Grounded-SAM`: score 39, harness fit 5, diagnostic fit 5, burden 2.
- `OpenMask3D`: score 24, harness fit 3, diagnostic fit 4, burden 4.
- `ConceptGraphs`: score 16, harness fit 3, diagnostic fit 3, burden 5.
- `OVIR-3D`: score 14, harness fit 2, diagnostic fit 3, burden 4.
- `HOV-SG`: score 6, harness fit 2, diagnostic fit 2, burden 5.

## Paper Claim

- E003-M47 does not support a new paper claim.
- It selects the first external route needed to separate proposal/backend failure from stale-memory logic.

## Agent Inference

- `Grounded-SAM` is the best first route because it is the smallest controlled change from the current `GroundingDINO` RGB-D backprojection backend.
- `OpenMask3D` has stronger top-tier baseline value but should follow after mask-backprojection smoke because its setup and data conversion burden are higher.
- `ConceptGraphs` and `HOV-SG` are better mapping/navigation baselines, not first proposal-failure diagnosis tools.

## User Decision Needed

- None for the first feasibility route. The next implementation unit should smoke-test `Grounded-SAM` mask-backprojection.
