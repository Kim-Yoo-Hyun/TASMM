# Paper Workflow

Status: active protocol, no paper folder yet.

이 문서는 paper 작성 규칙과 claim 검증 기준만 관리한다. 논문 본문 산출물은 아직 만들지 않는다. 실제 paper folder는 thesis, main result table, method figure, target venue, claim-evidence ledger가 구체화된 뒤에 만든다.

Source note: this workflow reflects the "Motivation is Not Novelty" guide: https://gisbi-kim.github.io/motivation-is-not-novelty/

## Core Rule

Motivation is not novelty.

For this project, the following is only motivation:

- dynamic objects make semantic memory stale
- RGB-D / open-vocabulary perception creates missed targets, false positives, and localization errors
- human task context should affect robot behavior
- existing mapping systems do not directly solve our dynamic search setting

Novelty starts only when the paper can explain why the naive solution fails, what principle follows from that diagnosis, and why the method must have its specific form.

Paper development must be principle-driven, not conclusion-fitting. If a result is negative, do not preserve the desired claim by changing thresholds, denominators, or posthoc filters. First record the failure mechanism, disconfirmation rule, and next validation requirement; only then design the next method form or scale-up gate from that diagnosis.

## Paper Claim Ladder

Use this ladder before writing any abstract, introduction, method, or contribution list.

| Stage | Required Output | Current H001 Direction |
| --- | --- | --- |
| Motivation | What existing methods fail to handle | Stale semantic memory under dynamic object search and noisy RGB-D/open-vocabulary proposals |
| Naive baseline | Simplest implementation implied by the motivation | static old memory, fixed top-k, detector-confidence ranking, context-agnostic memory trust |
| Failure diagnosis | Why the naive baseline fails | stale old-location FP, detector recall miss, false-positive pushdown, centroid/localization error, path/reachability mismatch, task-budget mismatch |
| Principle | One sentence that explains the required method form | Candidate: memory trust should be conditioned on staleness, task value, current-evidence reliability, and search/re-observation cost |
| Method form | Components derived from the principle | task context conditioner, memory trust gate, re-observation budget, path/search-cost ranking, proposal reliability bridge |
| Evidence | Experiments that test the principle, not just performance | E001/E002 proxy search, E003 noise and real proposal bridge, E004 memory trust policy, E005 external baselines |
| Boundary | What the paper cannot claim yet | real navigation `SR` / `SPL`, final real RGB-D/open-vocabulary robustness, deployable search policy, human intent as a main claim under current E006-M08 decision |

## Current One-Liner

Working one-liner:

> In dynamic indoor search, stale semantic memory fails not because old memory is always wrong, but because its reliability is task- and observation-cost dependent; therefore a semantic map should expose memory trust and re-observation as first-class decisions conditioned on task value, current proposal reliability, and search cost.

This is still a working hypothesis. It becomes a paper-ready novelty sentence only if ablations show that each condition is necessary and simpler alternatives fail for predictable reasons.

## Novelty Gate

Before calling anything a contribution, answer these questions.

- What is the closest naive baseline, in one sentence?
- Why does it fail, in a mechanism-level sentence?
- Which method component is forced by that failure diagnosis?
- What breaks when that component is removed?
- Why not static memory, detector-confidence ranking, fixed top-k, or context-agnostic memory trust?
- Which result tests the insight rather than merely showing a better score?
- Does the claim hold beyond one scan, one label group, or one artifact route?
- Can the novelty be explained in 30 seconds without saying "we propose"?

If four or more answers are weak, the work is still motivation-stage and the method section should not be drafted.

## Claim-Evidence Ledger

| Claim Candidate | Evidence Needed | Current Status | Risk |
| --- | --- | --- | --- |
| Task/staleness-aware memory decision improves dynamic object search proxy behavior | E001/E002/E004 tables vs static memory, fixed top-k, context-agnostic trust, path-aware variants | partially supported | task-context effect is narrow |
| The decision layer remains useful under real RGB-D/open-vocabulary proposal noise | E003 direct current-rescan bridge, heldout split, detector/proposal baseline comparison | diagnostic supported, final robustness not ready | M75 full aggregate over b01/b02/b03 has target detected 144 / 195, H001 157 / 195, context-agnostic 156 / 195, `ConceptGraphs` 114 / 195, detector task-budget 24 / 195, and detector top5 51 / 195. M76 marks this diagnostic-table ready but blocks final robustness due to detector precision 0.051892, target detection 0.738462, and false-positive load. M78 fixed replay reproduces M77 best policy with 0 mismatches and reaches top5 60 / 195, target detected 147 / 195, precision 0.105832. M80-M82 reproduces the expected `heldout_b02` runner gain: detector top5 9 / 69 -> 15 / 69 and task-budget 5 / 69 -> 7 / 69, but target detected stays 42 / 69. M83 stops immediate b01/b03 reruns. M84-M91 show prompt repair is not ready as a paper claim: strict pre-cap suppressed target count is 0, 1.5m threshold recovery is diagnostic only, same-label instance ambiguity remains, and the largest zero-written exposure is a label-resolution / scan-prompt scope mismatch. M91 validates `active_scan_exact_label_precedence_v0` on the audited scan: M89 pre-cap/final 0 / 0 becomes M91 479 / 24, with matched target rows 5 / 5. M93 validates the repair at b02 batch level: target detected 42 / 69 -> 57 / 69 and detector top5 15 / 69 -> 18 / 69, with no observed side-effect loss, but detector task-budget stays 7 / 69 and H001 stays 54 / 69. M94 records it as batch-level repair diagnostic, projects b02-replaced aggregate target detected 159 / 195 and detector top5 60 / 195, and selects stop-and-record rather than b01/b03 expansion. M95 fixes the paper-facing boundary: 7 full real-proposal diagnostic rows, 4 repair diagnostic rows, 2 allowed diagnostic claims, and 4 blocked claims. M96 selects external proposal/mapping baseline feasibility before navigation. M97 selects `ConceptGraphs`-derived route. M98 shows H001 recovers 54 rows where both `ConceptGraphs` strict top5 and real detector top5 fail, but `ConceptGraphs` succeeds on 24 H001-failure rows that must be inspected before a broad superiority claim |
| The framework is stronger than external dynamic/open-vocabulary mapping baselines | E005 `ConceptGraphs` and at least one additional fair query-level route such as `Open3DSG` / `HOV-SG` | partially supported for proxy-search only | `ConceptGraphs` full 195-row heldout comparison is ready; corrected `Open3DSG` bridge is denominator-aligned; M65 includes the M64 predicted-vocabulary adapter as a bounded external scene-graph baseline row; M66 fixes row-level failure boundaries |
| Structured human intent improves semantic memory decisions | E006 same-evidence paired task-context benchmark, strong context-agnostic baselines, utility/regret metrics, heldout scan/label/task transfer | current evidence negative for main claim | E006-M01-M06 fix the paired-context, baseline, transfer, utility, schema, and frozen policy-row contracts. E006-M07 materializes 20,800 utility metric rows with policy-row mutation audit `pass`, but the primary policy has mean `ContextSpecificGain` -4.253654 against the strongest context-agnostic baselines. E006-M08 therefore keeps human intent as secondary conditioning / ablation evidence unless a future policy redesign passes utility, strong-baseline, and transfer gates |
| The system supports deployable search policy | bounded budget improvement, allowed-input contract, failure separation | not ready | current policy is diagnostic, not deployable |
| The system improves real navigation `SR` / `SPL` | simulator/navmesh/trajectory execution and navigation baselines | diagnostic smoke supported, final H001 claim unsupported | E008-M22 provides Docker-executed detector-policy trajectory smoke over 6 `HM3D ObjectNav` rows. E008-M37 executes 90 dynamic-stale overlay scan-task-policy rows in Docker `Habitat`: detector confidence `SR` 1.0 / `SPL` 0.407894, fixed current top-k `SR` 0.5 / `SPL` 0.373373, H001 task-conditioned memory trust `SR` 0.5 / `SPL` 0.141996, static stale memory `SR` 0.0, task-agnostic memory trust `SR` 0.5 / `SPL` 0.167627. E008-M38 interprets this as repair-before-scale. E008-M39-M62 iterate through budget-matched repair, source-diverse redesign, task-context demotion, and high-path tail-slot diagnostic navigation evidence. E008-M63-M92 scale to `val_mini_full_episode_scale`, run/render detector candidates, validate navmesh/source readiness, execute detector-policy trajectory smoke, reject a source-gap/SPL rerank repair, test loss-safe source expansion, materialize source-gap source/observation expansion, verify 192/192 rendered frames, verify 48 source-gap detector candidates, validate 2/2 source-gap cases as source-ready with 30/48 path-ready candidates, materialize 138 source-gap visit-order/path rows, run leakage-safe source-gap goal-evaluation, interpret the negative result, diagnose target-coverage failure modes, and fix a two-branch repair contract. M93-M101 materialize and verify coverage-expansion rows for one remaining source-gap case, run detector inference, validate 11/24 candidates as path-ready, materialize 57 visit-order/path rows, run leakage-safe goal evaluation, and reject trajectory promotion. M102 closes the current detector source-gap repair route: 2/2 source-gap cases closed negative, M97 proposals/pre-cap 24/853, M98 path-ready 11/24, M100 primary success max 0. M103 selects `conceptgraphs_hm3d_map_candidate_adapter` as the next alternative proposal-source preflight because `ConceptGraphs` image/E005 route are ready, while `OpenMask3D` checkpoints are ready but the Docker image remains blocked. M104 confirms both selected source-gap cases are adapter materialization-ready for `ConceptGraphs`. M105 materializes 2/2 staged scans with 192 RGB-D/pose frames, 576/576 regular input files, container readability true, and leakage rows 0. M106 fixes the bounded runtime launch/verification contract. M107 completes the runtime, M108 verifies runtime outputs ready for 2/2 scans, M109 fixes the candidate export adapter with post-PCD object counts 29/42, M110 materializes 71 leakage-safe candidate rows with 71/71 semantic-scored rows and leakage audit pass, M111 validates those candidates against `Habitat` navmesh: coordinate/snapped navigable 71/71, path-ready 48/71, source-ready queries 2/2, M112 materializes 215 visit-order/path rows with leakage audit pass, and M113 runs leakage-safe goal evaluation with primary proxy success 0/2 for all policies. Path-cost-aware `ConceptGraphs` ordering reduces first-ready path cost, but M113 shows those path-ready candidates are not close enough to eval target viewpoints: mean best any-viewpoint XZ distance 3.468193m. M114 interprets this as a negative gate, rejects trajectory promotion, and splits failures into one severe source coverage gap and one stop-region/viewpoint alignment gap. M115 fixes the repair-route contract, M116 materializes the two audit families, M117 selects M118 stop-region transform smoke while deferring source-coverage repair to external/visibility preflight, and M118 materializes 50 non-oracle radial stop-region candidates for the selected toilet case with 50/50 path-ready rows and leakage audit pass. M118 observes budget-5 proxy recovery for `stop_region_cardinal_first_budgeted_v0` but not for path-cost-only policies, which supports a local viewpoint-alignment interface diagnosis rather than a navigation claim. M119 then verifies the remaining `sofa` case as a source-coverage failure: current M84/M93 source poses are far from the target view region, same-source rerank/rerun is rejected, and target-free source-coverage expansion is selected before any trajectory or external-map claim. M120 fixes that target-free source-coverage expansion contract with two selected M121 materialization routes and blocks ObjectNav target/viewpoint source-placement leakage. M121 materializes 40 target-free source poses, 320 render-plan rows, and 2 detector manifests with leakage false. M122 fixes render/detector launcher inputs and M123/M124 long-job command ledgers. M123 verifies 295 depth-filtered detector-sampled frames, M124 verifies 24 detector prediction rows with 2,910 pre-cap candidates, M125 passes navmesh/source-readiness validation with 15 / 24 path-smoke usable candidates, M126 materializes 69 visit-order/path rows with leakage audit pass, M127 observes leakage-safe `any_viewpoint_xz_1p0` proxy recovery 1/1 for all four policies with proxy SPL 0.357073-0.779043, M128 selects a bounded trajectory-contract/preflight gate, M129 materializes 69 runner-compatible trajectory candidate rows plus 4 execution plans with Docker/data/runner preflight pass, and M130 executes the one-case target-free detector-policy trajectory smoke. M130 reaches `SR` 1.0 for all four policies, but the path-cost method has `SPL` 0.092750 versus detector-confidence `SPL` 0.701267, so it is diagnostic-negative for a navigation-improvement claim. Later E008-M191-M198 scale source-pool acquisition to 30 triggered episodes and reject immediate trajectory promotion because source-pool proxy `SR` / `SPL` 0.5667 / 0.3235 is below the M70 no-source detector baseline 0.8000 / 0.3506. Final navigation claims remain blocked until M199 failure decomposition, candidate-generation repair, heldout transfer, and external navigation/search baselines pass. |

Latest navigation ledger update: E008-M198 is complete. M165 decomposes the M163/M164 negative gate: the selected repair changes 24 / 30 episode orders but changes 0 successful target proposals versus detector-confidence, with mean delta `SPL` -0.003213 and mean candidate visits +0.200000. M166-M176 convert that failure into a method pivot and source-acquisition contract: local path tie-break is excluded as the main method, `confidence_floor_guard` remains a necessary guard, within-pool source-coverage reranking is closed as a negative branch, and `source_coverage_triggered_candidate_source_expansion_v1` becomes the next method family. M177-M184 validate a fixed-budget source-pool branch on 8 episodes, but M185-M190 reject direct path-cost and transition-cost reranking because they tie protected `SR` and lose `SPL`. M191-M198 scale the source-pool acquisition route to 30 triggered `HM3D ObjectNav val_mini` episodes: M194 produces 552 detector candidate rows from 960 frames, M195 validates 523 path-ready candidates with 23 / 30 source-ready scans, M196 materializes 2,121 visit-order rows, and M197 records leakage-safe proxy recovery 17 / 30. M198 compares the source-pool protected detector-confidence policy against the M70 no-source detector baseline and rejects immediate trajectory promotion: source-pool proxy `SR` / `SPL` 0.5667 / 0.3235 vs baseline 0.8000 / 0.3506. This is a negative scale boundary, not a positive navigation-improvement result.

Latest literature refresh update: 2026-06-09 targeted refresh [CAND-001_top-tier-refresh-2026.md](../literature/CAND-001_top-tier-refresh-2026.md) supports the E008-M137 paper rule that detector-confidence must remain the protected naive baseline. A trajectory-aware method is paper-facing only if it uses path/search cost as confidence-band tie-break, hard feasibility veto, or source-gap/source-coverage trigger, and shows why that guarded form avoids the M130/M135 `SPL` regression.

Latest method-pivot update: E008-M166-M198 are complete. E008-M166-M176 freeze the local-rerank failure boundary and define source coverage as a semantic-map trigger for candidate-source expansion / re-observation before detector-confidence ranking. E008-M177-M184 validate that fixed-budget source-pool acquisition can surface recoverable candidates and execute bounded Docker trajectories on a small branch. E008-M185-M190 show that ranking must remain protected by detector confidence because path/transition-cost orders do not improve `SPL`. E008-M191-M198 scale the source-pool acquisition route and reject immediate trajectory promotion because source-pool acquisition lowers full-denominator proxy `SR` against the no-source detector baseline. Next paper-facing work must explain whether the failure comes from detector target coverage, source-pool viewpoint quality, candidate cap/label filtering, or source-gap category distribution before proposing another method component.

## External Baseline Contract

사실:

- `ConceptGraphs` and bounded `Open3DSG` are the current converted external map/scene-graph baselines.
- `HOV-SG`, `VLFM`, `HM3D-OVON`, `GOAT-Bench`, and `3D-Mem` have not been run or converted in this workspace.

에이전트 추론:

- `HOV-SG` should be the next map-navigation baseline contract because it tests whether hierarchical open-vocabulary semantic mapping can produce better source-gap candidates than H001's memory-trust/search-cost policy.
- `VLFM` and `HM3D-OVON` should be used only for executable navigation pressure: same episodes, same start states, same goal categories, same blocked-input rules, and `SR` / `SPL` metrics.
- `3D-Mem` should be used to pressure the scene-memory claim, not as a direct navigation baseline unless it is adapted to the same candidate ranking interface.
- `GOAT-Bench` should wait unless human intent is explicitly re-promoted, because E006-M08 currently rejects it as a main claim.

Baseline evidence required before claims:

| Baseline | Claim pressure | Required evidence before paper claim |
| --- | --- | --- |
| `HOV-SG` | map-to-navigation source-gap candidate generation | source/runtime audit, candidate coordinate export, navmesh/path-ready validation, leakage-safe goal evaluation |
| `VLFM` | navigation policy strength | same `HM3D` split, `SR` / `SPL`, path length, failure taxonomy, no eval-goal leakage |
| `HM3D-OVON` baseline | open-vocabulary navigation benchmark rigor | official/reproducible split contract, category mapping, allowed-input audit, `SR` / `SPL` |
| `3D-Mem` | scene-memory retrieval and memory management | query/candidate adapter, stale-location suppression metrics, comparison to H001 memory trust |
| `GOAT-Bench` | broader human-facing task execution | E006 task context contract, utility metric, instruction/structured-context boundary |

논문 주장:

- Until these baselines are executed or converted, they are reviewer-defense requirements, not evidence.
- The paper should not say H001 beats open-vocabulary navigation systems; it can only say which stronger baselines are required and what shared interface will make the comparison fair.

## Experiment-To-Paper Mapping

- E001: defines the semantic-pair dynamic object search problem and naive baselines.
- E002: adds path/search-cost bridge and separates source-limited failures from policy failures.
- E003: tests controlled perception noise and real RGB-D/open-vocabulary proposal failure modes.
- E004: tests memory trust and task-context conditioning, with claim boundaries.
- E005/E006: E005 adds external baseline pressure; `DualMap` runs without object-map outputs, `ConceptGraphs` now has full 195-row heldout query-level aggregation, and `Open3DSG` is source/schema/export/query-conversion ready on the same denominator. Corrected `Open3DSG` primary-label strict bbox top5 is 81/195 and relaxed bbox 1m top3 is 90/195. M64 leakage-safe predicted-vocabulary adapter reaches strict 144/195 and relaxed 147/195. E006-M08 keeps human intent as secondary structured task-context evidence rather than a main claim. M66 records H001-only 60 rows vs `ConceptGraphs`, H001-only 39 rows vs `Open3DSG` vocab, and only 1 task-context-specific gain row. M68 materializes the robustness route: 195-row full-denominator real proposal bridge inputs split into 3 heldout batches. M71/M74/M75 convert and aggregate all b01/b02/b03 detector batches. M76 makes M75 a diagnostic real-proposal search table. M77 separates pre-cap recoverable targets from prompt/detector recall misses. M78 implements fixed offline repair replay. M79 confirms runner insertion without source edit and selects `heldout_b02` as the first targeted rerun. M80-M82 launch, verify, and convert that rerun. M83 keeps the result as diagnostic detector-ranking repair evidence and skips immediate b01/b03 reruns. M84-M92 audit prompt/label recall, visibility/matcher, candidate survival, match threshold, zero-written scan causes, raw-label trace availability, target-independent cleanup decisions, leakage-safe repair scope, one-scan cleanup repair, and query/rerun route. M93 validates the selected active-label precedence repair at b02 batch level. M94 records the result as diagnostic repair evidence and keeps final robustness, deployable policy, and navigation claims blocked. M95 fixes the paper-facing real-proposal table and final E005 blocked-claim ledger. M96 selects external proposal/mapping baseline feasibility before navigation. M97 selects `ConceptGraphs`-derived route as the first smoke. M98 produces row-level reliability groups and keeps final robustness blocked until M99 decides row inspection vs heavier external route.

Main tables should not merely report that our method is better. They should show which failure mode is addressed by which component.

## Required Ablations

Minimum ablation set for a serious paper draft:

- no task context
- no staleness / memory-trust term
- no current-proposal reliability term
- no re-observation budget
- no path/search-cost term
- fixed top-k replacement
- detector-confidence-only replacement
- context-agnostic trust replacement
- external mapping baseline replacement when available

Each ablation must have an expected failure mode before running it.

## Reviewer Defense

Expected reviewer questions:

- Why is this semantic mapping, not just ranking?
- Why is structured task context enough, and what is not claimed about natural language?
- Why not use a stronger detector or open-vocabulary mapper directly?
- Why does stale memory require task-conditioned trust instead of a fixed decay score?
- Why does the method generalize beyond `chair` / `pillow` and the current 4 rescans?
- What does `DualMap` / `ConceptGraphs` / `Open3DSG` fail or solve compared with our method?
- What would `HOV-SG`, `VLFM`, `HM3D-OVON`, `GOAT-Bench`, or `3D-Mem` test that current tables do not?
- Does `Open3DSG` remain weak after a leakage-safe predicted-vocabulary adapter, or was the gap mostly an adapter mismatch?
- Where are real navigation `SR` / `SPL` and what is the bridge until then?

Answers must refer to artifacts, tables, ablations, or explicit limitations.

## Paper Shape

### Abstract

Four sentences only:

1. problem and mechanism-level failure of existing semantic memory
2. principle and method form in one concrete sentence
3. dataset / benchmark / baseline setting
4. strongest quantitative result and boundary

### Introduction

Use this order:

1. Human-facing robot tasks need semantic maps that support action under stale and noisy observations.
2. Existing semantic maps or open-vocabulary mappers do not directly decide when old memory should be trusted for a task.
3. Diagnose the naive baseline failure, not just the application pain point.
4. State the principle that forces the method design.
5. State contributions as tested claims with evidence pointers.

### Method

Do not write a system-diagram-only method section. Each component must be introduced by the failure mode that requires it.

### Experiments

Every experiment answers a reviewer question:

| Reviewer Question | Experiment |
| --- | --- |
| Does stale memory require a decision layer? | static memory vs trust/re-observation policies |
| Does task context matter beyond a global threshold? | task-conditioned vs context-agnostic trust |
| Does path/search cost change the decision? | E002/E004 cost-aware metrics |
| Does the result survive proposal noise? | E003 controlled and real proposal diagnostics |
| Is this competitive with external mappers? | E005 `ConceptGraphs` comparison is positive; corrected `Open3DSG` is weaker under primary labels, while M65 accepts the M64 bounded predicted-vocabulary adapter as a main-table external baseline row; M101 marks `ConceptGraphs`-assisted H001 fallback as paper-facing query-level table ready with boundary |
| What breaks? | failure taxonomy and claim boundary table |

## Reproducibility Checklist

- exact dataset version and split are recorded
- preprocessing is described
- all policy inputs and forbidden inputs are fixed
- all baselines are sourced or implemented
- exact commands reproduce main tables
- Docker image and hardware are recorded for paper-body experiments
- external code, models, checkpoints, datasets, and assets are cited with version/license
- failure cases are not filtered out silently
- limitations are linked to actual experiments

Current reproducibility entry point: `docs/reproducibility.md`.

## When To Create A Paper Folder

Create a paper folder only when all are true:

- one-sentence thesis is stable
- method components are derived from diagnosed failures
- at least one main result table exists
- one system diagram or method figure is sketched
- target venue and deadline are selected
- related work map has at least 20 closely read papers
- claim-evidence ledger has no empty evidence for main claims

Until then, keep paper work in this protocol and result logs.
