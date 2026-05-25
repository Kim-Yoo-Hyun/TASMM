# Schedule

Last updated: 2026-05-25

이 문서는 H001 main experiment implementation을 top-tier submission path로 확장하기 위한 실행 순서를 관리한다. 세부 실험 결과는 `experiments/`에 기록하고, 이 문서는 단계, gate, baseline 확장 방향만 관리한다.

## Current Direction

사실:

- Active direction: `CAND-001` / `Intent- and Staleness-Aware Semantic Mapping`.
- Active hypothesis: `H001_stale-object-memory`.
- Current stage: main experiment implementation.
- Final paper target: Direction B `Task-Aware Dynamic Semantic Mapping for Open-Vocabulary Search and Navigation`.
- Current path: use Direction A `Task-Conditioned Stale Semantic Memory` as the core method/backbone, then expand through real proposal/search bridge, external baselines, and search/navigation metrics.
- Current E003 status: E003-M75 direct current-rescan bridge is ready over 96 query rows; real RGB-D/open-vocabulary claim readiness remains false.
- Current E004 status: E004-M05 supports memory-trust claim strength `split_supported`; task-context-specific claim strength remains `limited_positive_not_label_broad`.
- Current E005 status: `ConceptGraphs` is the active converted positive external mapping baseline route. All 9 heldout scans have runtime output and query-level conversion, and H001 has been replayed on the same M38 heldout query contract. E005-M56-M71 completed the two-table robustness denominator contract, read-only `Open3DSG` source/interface audit, output schema contract, object-candidate export, denominator-aligned query conversion, target-geometry loader repair, route decision, leakage-safe predicted-vocabulary policy evaluation, paper-table integration boundary, external-baseline failure-boundary rows, real RGB-D/open-vocabulary robustness route decision, full-denominator real proposal bridge planning, and `heldout_b01` detector query-level conversion. M64 predicted-vocabulary policy reaches strict 144 / 195 and relaxed 147 / 195 with leakage audit pass. M65 includes this row as a bounded external scene-graph baseline, excludes primary-label adapter from the main table, and keeps human intent as structured task-context secondary evidence. M71 converts `heldout_b01`: target detected 54 / 66, real detector task-budget 8 / 66, real detector top5 21 / 66, static memory 45 / 66, context-agnostic memory trust 48 / 66, H001 real memory-trust 48 / 66, and `ConceptGraphs` b01 45 / 66. Real RGB-D/open-vocabulary robustness remains blocked until remaining heldout batches are run and converted.

에이전트 추론:

- Current core direction is aligned with recent work on open-vocabulary semantic mapping, 3D scene memory, task-driven mapping, and embodied navigation.
- Direction B is the correct final top-tier target, but the immediate implementation should remain focused on Direction A's memory-decision core to avoid an unfocused system paper.
- Human intent should remain a controlled task-context condition unless a dedicated context-sensitive utility benchmark shows broad gains over context-agnostic memory trust.
- Top-tier competitiveness requires moving beyond `3RScan` / `3DSSG` proxy evidence into stronger external baselines and downstream search/navigation evaluation.

## Top-Tier Target Claim

논문 주장 후보:

- `Task-Conditioned Stale Semantic Memory Update` improves dynamic object search/navigation by modulating memory trust, re-observation priority, and candidate visit order under object movement and perception noise.
- The method should improve `ExpectedSearchCost`, `SR`, `SPL` or `AttemptSPL`, stale old-location false positives, and proposal-aware search robustness.

논문 주장:

- Final claim should include real RGB-D / open-vocabulary proposal robustness and a search/navigation bridge, not only annotation-proxy stale memory behavior.
- Direction B is the final target claim family; Direction A is the core method claim that must survive ablation and bridge tests.
- Human task context is not yet a main contribution claim. The current defensible phrasing is that structured task context is a conditioning signal for memory trust and re-observation, not that the system understands human intent.

## Schedule

| Phase | Goal | Main output | Gate |
| --- | --- | --- | --- |
| E003-M39 | Temporal/spatial support instrumentation | Complete: support fields, runner insertion point, and verification plan fixed | No long rerun until schema and verification command are fixed |
| E003-M40 | Proposal-quality runner smoke | Complete: support fields implemented and short Docker smoke passed | Support fields must appear in validated proposal output |
| E003-M41 | Support-aware selection policy gate | Complete: selected `confidence_sqrt_depth_support_temporal_v0` | No long rerun until policy contract and success checks are fixed |
| E003-M42 | Support-aware selection runner smoke | Complete: selected score mode implemented and short Docker smoke passed | Validator must pass and support-aware score mode must be recorded |
| E003-M43 | Support-aware scaled rerun route gate | Complete: selected `pre_cap_candidate_pool_export_then_offline_replay_v0` | No immediate long rerun because existing artifacts cannot support score ablation |
| E003-M44 | Pre-cap candidate-pool export and offline replay harness | Complete: exported 629 support-instrumented candidates and reproduced runner selection offline | Replay reproduced runner selected stable-candidate set |
| E003-M45 | Scaled candidate-pool export and support-aware replay | Complete: 60,435 candidate pool rows, replay ready, frozen verdict `fail_redesign` | Support-aware score lost targets, added false positives, and failed hard/weak criteria |
| E003-M46 | Support-aware redesign or external proposal baseline gate | Complete: 12 local score policies swept, hard pass 0, weak positive 0 | Selected `external_proposal_baseline_gate_first` |
| E003-M47 | External proposal/mapping baseline feasibility gate | Complete: selected `Grounded-SAM` over `OpenMask3D`, `ConceptGraphs`, `OVIR-3D`, `HOV-SG` | First route must diagnose whether box-depth projection is the current proposal bottleneck |
| E003-M48 | `Grounded-SAM` mask-backprojection contract | Complete: `grounded_sam_mask_backproject_v0` input/output contract, blocked inputs, optional mask fields, and long-running job policy fixed | No result claim; implementation smoke remains next |
| E003-M49 | `Grounded-SAM` Docker/model smoke | Complete: mask-depth rows emitted, validator passed, M21 matcher passed | Implementation smoke only |
| E003-M50 | Same-subset bbox-depth vs mask-depth comparison gate | Complete: bbox-depth beat mask-depth on matched targets, precision, recall, and centroid error | Do not scale `Grounded-SAM` yet |
| E003-M51 | Post-M50 route decision | Complete: selected artifact-local `Grounded-SAM` mask failure analysis | Must avoid spending compute on a route with negative same-subset evidence |
| E003-M52 | `Grounded-SAM` mask failure analysis | Complete: target loss is mask projection dropout and centroid worsening is match-set composition | Do not scale current `Grounded-SAM` route as-is |
| E003-M53 | Bbox-depth continuation and failure-boundary repair gate | Complete: selected search-critical bbox-depth failure-boundary audit | Must preserve the stronger current route while keeping external baseline expansion open |
| E003-M54 | Search-critical bbox-depth failure-boundary audit | Complete: exact current query-instance joins 0, label-level bridge risk identified | Current detector failures cannot yet be used as direct search-decision evidence |
| E003-M55 | Dynamic-pair-aligned real-proposal bridge gate | Complete: selected search-failure current-rescan staging first | Must stage current-rescan sequence payloads before detector output can be evaluated against E001/E002 rows |
| E003-M56 | Current-rescan sequence payload staging plan | Complete: fixed target scan list, command, output paths, logs, and verification for 4 current rescans | Use long-running/background task rule for download/decompression |
| E003-M57 | Current-rescan sequence staging background job | Complete: launched M56 command in `tmux`, recorded job status/log path, and verified 4 / 4 payloads ready | Direct detector bridge design can start |
| E003-M58 | Direct current-rescan detector/evaluation bridge design | Complete: 7 query rows, 5 unique bridge targets, 4 scans, `chair`/`pillow` prompt set, M59 command plan | No real RGB-D search claim until detector bridge output is evaluated |
| E003-M59 | Direct current-rescan detector bridge Docker run | Complete: 93 frames, 96 proposals, validator errors/warnings 0 / 0, matched 21, false positives 75 | Query-level bridge evaluation required before search claim |
| E003-M60 | Direct current-rescan query-level bridge evaluation | Complete: 3 / 7 query targets detected, `detector_task_budget_v0` success 0 / 7 | Budget/rank gap blocks real RGB-D search claim |
| E003-M61 | Direct bridge rank/failure analysis gate | Complete: detector recall miss 4, task-budget mismatch 2, false-positive rank failure 1 | Selected `proposal_rerank_then_openmask3d_feasibility` |
| E003-M62 | Offline proposal rerank/budget repair sweep | Complete: best deployable unbounded repair 3 / 7, bounded top-5/adaptive repair 2 / 7 | Selected bounded repair integration before `OpenMask3D` |
| E003-M63 | Bounded rerank/budget repair integration gate | Complete: bounded repair ablation ready, unique rerank gain false, unbounded upper-bound only | Selected `openmask3d_feasibility_gate_next` |
| E003-M64 | `OpenMask3D` feasibility decision gate | Complete: target-undetected rows 4, minimal-input-ready scans 4 / 4 | Selected `openmask3d_scene_format_model_smoke_plan_next` |
| E003-M65 | `OpenMask3D` scene-format/model smoke plan | Fix scene-format manifest, command plan, adapter contract, and verification command | No Docker/model run until background/log/output/verification contract is fixed |
| E004-M01 | Task-context memory trust contract | Fix task context fields for memory trust / re-observation decision | Natural language parser remains adapter, not main claim |
| E004-M02 | Task-conditioned re-observation/search policy | Evaluate task-conditioned policy under stale memory + proposal noise | Must beat static memory, fixed top-k, and detector-confidence-first |
| E005-M49 | Full heldout metric aggregation | Complete: all 9 heldout `ConceptGraphs` scans aggregated, strict bbox top5 114 / 195 | External baseline still needs H001 comparison on the same query contract |
| E005-M50 | H001-vs-`ConceptGraphs` comparison gate | Complete: direct common query rows 0, paired superiority not ready from original universes | Replay H001 on the `M38` heldout query contract |
| E005-M51 | H001 heldout replay contract | Complete: 195 / 195 heldout query rows adapter-ready, issues 0 | No result claim until H001 replay is run |
| E005-M52 | H001 heldout policy replay | Complete: H001 172 / 195, `ConceptGraphs` 114 / 195, static memory 141 / 195, context-agnostic 171 / 195 | Paired failure/table decision required before paper claim |
| E005-M53 | Paired failure analysis / paper-table decision | Complete: H001-vs-`ConceptGraphs` and H001-vs-static proxy-search claims ready; task-context main claim not ready | Do not claim human intent as the main contribution |
| E005-M54 | Paper-table claim ledger / method claim rewrite | Complete: paper-facing table, allowed claims, blocked claims, and method framing fixed | Main claim centers memory trust, staleness handling, and bounded re-observation |
| E005-M55 | Real RGB-D/open-vocabulary robustness expansion gate | Complete: selected `robustness_denominator_contract_then_open3dsg_audit` | Real RGB-D robustness remains blocked |
| E005-M56 | Robustness denominator + `Open3DSG` audit | Complete: Table A proxy-search denominator 195 rows, Table B real RGB-D proposal bridge denominator 96 rows, `Open3DSG_staged` read-only audit passed | No `Open3DSG` performance claim before query-level conversion |
| E005-M57 | `Open3DSG` output schema inspection / query-conversion contract | Complete: relation raw dump ready, feature/checkpoint route feasible, object candidate export needed | No `Open3DSG` object-search claim before candidate rows exist |
| E005-M58 | `Open3DSG` object-candidate dump/export smoke plan | Complete: read-only Docker command, object-candidate schema, local output path, export contract, and verifier fixed | No `Open3DSG` object-search claim before one-batch candidate rows exist |
| E005-M59 | `Open3DSG` object-candidate export hook / one-batch Docker smoke | Complete: lower-memory relaunch ready, 180 object-candidate rows, completed batches 1 | Input to M60/M61 coverage diagnosis |
| E005-M60 | `Open3DSG` query-level conversion | Complete after M61 rerun and target-geometry loader fix: 195-row denominator, 7,600 object candidates, 759 query/eval candidate rows, 585 policy rows, strict 81 / 195 | Primary-label adapter below `ConceptGraphs` |
| E005-M61 | Targeted `Open3DSG` denominator-aligned batch export | Complete: all 9 query scans, 51 target subgraphs, 7,600 object-candidate rows, source modified false | Input to M60 rerun |
| E005-M62 | `Open3DSG` result interpretation | Complete after corrected M60: bridge feasibility true, main-table performance baseline false, H001 strict margin +91 | Input to M63 |
| E005-M63 | `Open3DSG` route decision | Complete: diagnostic predicted-term strict 144 / 195, selected bounded repair next | M64 completed the policy verification |
| E005-M64 | `Open3DSG` leakage-safe vocabulary policy | Complete: strict 144 / 195, relaxed 147 / 195, leakage audit pass | Input to M65 paper-table boundary decision |
| E005-M65 | `Open3DSG` paper-table integration boundary | Complete: include predicted-vocabulary adapter row, exclude primary-label adapter from main table, human intent secondary | Input to E005-M66 failure-boundary rows |
| E005-M66 | External-baseline failure-boundary rows | Complete: H001-only 60 vs `ConceptGraphs`, H001-only 39 vs `Open3DSG` vocab, task-context gain 1 | Input to E005-M67 robustness route decision |
| E005-M67 | Real RGB-D/open-vocabulary robustness route decision | Complete: selected `scale_real_proposal_bridge_to_m38_heldout_denominator`, denominator gap 195 vs 96 rows | Input to E005-M68 full-denominator bridge plan |
| E005-M68 | Full-denominator real proposal bridge plan | Complete: 195 rows, 9 ready scans, 65 object targets, 22 prompt labels, 214 sampled frames, 3 heldout batches | Input to E005-M69 detector batch launch |
| E005-M69 | Full-denominator real proposal detector batch launch | Complete: `heldout_b01` launched in tmux `e005_m69_real_proposal_heldout_b01` | Input to E005-M70 completion verification |
| E005-M70 | `heldout_b01` detector completion verification | Complete: expected files 12/12, prediction rows 261, matched targets 18/22, recall 0.8182, precision 0.0690, false-positive rate 0.9310 | Input to E005-M71 query-level metric conversion |
| E005-M71 | `heldout_b01` real proposal query-level conversion | Complete: target detected 54/66, H001 48/66, context-agnostic 48/66, `ConceptGraphs` b01 45/66 | Input to E005-M72 remaining batch launch |
| E006-M01 optional | Context-sensitive utility benchmark design | Define task-context-sensitive query rows and utility metrics | Start only if human task context is promoted beyond secondary ablation |
| E006-M02 optional | Strong context-agnostic baseline suite | Compare against fixed trust, all-high-value, all-reobserve, risk-only, path-cost-only, detector-confidence-only | Human task context must beat these baselines beyond a 1-row gain |
| E006-M03 optional | Context generalization stress | Test heldout scan / label / task-group transfer | Human task context main claim requires broad transfer, not one label group |
| E007 optional | Navigation `SR` / `SPL` bridge | Add simulator/navmesh/trajectory execution and navigation baselines | Do not start before proxy table and real RGB-D robustness are stable |

## Human Task Context Claim Upgrade

사실:

- E005-M53 shows H001 improves over `ConceptGraphs` and static memory on the heldout proxy-search table.
- E005-M53 also shows that H001 improves over context-agnostic memory trust by only 1 row.
- Current evidence supports task context as a secondary ablation, not as the main contribution.

논문 주장:

- Do not write the current paper as a human-intent understanding paper.
- The current paper can say structured task context conditions memory trust and re-observation decisions, but it should not claim that human task context is the main source of improvement.
- Natural language or LLM parsing should remain an adapter until structured context has a strong independent effect.

에이전트 추론:

- Human intent is worth keeping in the research direction, but not worth expanding before the real RGB-D/open-vocabulary robustness gate is planned.
- Promote human task context only if a dedicated context-sensitive utility benchmark shows clear gains over strong context-agnostic policies.
- The right upgrade target is not generic natural-language understanding; it is context-dependent utility: different task contexts should rationally change memory trust, re-observation budget, candidate visit order, and old-location dead-end cost.

Upgrade requirements:

- Build `task-context-sensitive` query rows where the same object/location evidence should lead to different decisions under different task contexts.
- Add strong context-agnostic baselines: fixed trust, all-high-value trust, all-reobserve, risk-threshold only, path-cost only, and detector-confidence only.
- Add context-dependent utility metrics: `ExpectedSearchCost`, old-location dead-end cost, unnecessary re-observation cost, missed-high-value penalty, false trust penalty, and candidate visit order.
- Require heldout scan / label / task-group transfer before writing a general human-context claim.
- Treat LLM-based natural-language intent parsing as a later input adapter, not as a source of method novelty.

Decision:

- Immediate paper path: keep human task context as secondary evidence.
- Optional expansion path: launch E006 only after E005-M54 if the paper needs a stronger human-intent claim.

## Claim Expansion Order

사실:

- Real RGB-D/open-vocabulary robustness is not ready.
- Real navigation `SR` / `SPL` is not ready.
- E005-M53 makes the proxy-search claim boundary explicit.

에이전트 추론:

- The next claim to mature is proxy-search with external map baseline comparison.
- The next expansion after that should be real RGB-D/open-vocabulary robustness.
- Real navigation `SR` / `SPL` should come last because it requires simulator/navmesh/trajectory execution and navigation baselines.

Order:

1. E005-M54: paper-table claim ledger / method claim rewrite. Complete.
2. E005-M55: real RGB-D/open-vocabulary robustness expansion gate. Complete.
3. E005-M56: two-table robustness denominator and `Open3DSG` source/interface audit. Complete.
4. E005-M57: `Open3DSG` output schema inspection / query-conversion contract. Complete.
5. E005-M58: `Open3DSG` object-candidate dump/export smoke plan. Complete.
6. E005-M59: `Open3DSG` object-candidate export hook implementation / one-batch Docker smoke. Complete.
7. E005-M60: `Open3DSG` query-level conversion. Complete after M61 rerun and target-geometry loader fix.
8. E005-M61: targeted denominator-aligned `Open3DSG` export. Complete.
9. E005-M62: `Open3DSG` result interpretation. Complete with corrected metrics.
10. E005-M63: `Open3DSG` route decision. Complete; bounded predicted-vocabulary repair selected.
11. E005-M64: leakage-safe `Open3DSG` predicted-vocabulary policy. Complete.
12. E005-M65: `Open3DSG` vocabulary-policy claim-boundary / paper-table integration decision. Complete.
13. E005-M66: external-baseline table failure-boundary rows. Complete.
14. E005-M67: real RGB-D/open-vocabulary robustness expansion route decision. Complete.
15. E005-M68: full-denominator real RGB-D proposal bridge plan. Complete.
16. E005-M69: full-denominator real proposal detector batch launch. Complete for `heldout_b01`.
17. E005-M70: `heldout_b01` detector completion verification. Complete.
18. E005-M71: `heldout_b01` real proposal query-level metric conversion. Complete.
19. E005-M72: `heldout_b02` / `heldout_b03` real proposal detector batch launch.
20. Optional E006 human task-context upgrade: context-sensitive utility benchmark and strong context-agnostic baselines.
21. E007 navigation bridge: simulator/navmesh/trajectory execution, `SR`, `SPL`, `ExpectedSearchCost`, candidate visit order, stale old-location dead-end cost.

## External Baseline Expansion

Top-tier submission needs external baselines beyond current internal policies.

### Open-Vocabulary Mapping Baseline

Candidate baselines:

- `ConceptGraphs`
- `HOV-SG`
- `Open3DSG` if implementation/data compatibility is practical

Purpose:

- Compare against map construction and open-vocabulary object/relationship representation baselines.
- Show whether stale-memory decision logic adds value beyond stronger open-vocabulary map representations.

### Dynamic Semantic Mapping Baseline

Candidate baselines:

- `DualMap` or a compatible DualMap-style dynamic mapping baseline

Purpose:

- Compare against online open-vocabulary mapping for dynamically changing scenes.
- Clarify whether the contribution is dynamic map update, stale-memory trust, or downstream search decision.

### Navigation/Search Baseline

Candidate baselines:

- `VLFM`
- `HM3D-OVON` baseline
- `GOAT-Bench` modular baseline

Purpose:

- Connect semantic memory to downstream `SR`, `SPL`, `ExpectedSearchCost`, and lifelong/multimodal navigation metrics.
- Avoid limiting the paper to proxy object retrieval.

### Scene Memory Baseline

Candidate baseline:

- `3D-Mem`

Purpose:

- Compare against recent 3D scene memory and memory-management approaches for embodied exploration/reasoning.
- Position H001 as task-conditioned stale semantic memory rather than generic scene memory.

### Detector/Proposal Baseline

Candidate baselines:

- `Grounded-SAM`
- `OpenMask3D`
- `OVIR-3D`
- `ConceptGraphs` proposal path

Requirement:

- Add at least 1-2 proposal baselines beyond `GroundingDINO`.

Purpose:

- Prevent the real RGB-D/open-vocabulary claim from depending on one detector backend.
- Separate detector/proposal quality from stale-memory update behavior.

## Dataset Plan

사실:

- `3RScan` / `3DSSG` remains the core dataset for object movement, rescan alignment, and stale semantic memory.
- Current 8-scan real-proposal artifact is too small for reliable label-stratified split learning.

에이전트 추론:

- Keep `3RScan` / `3DSSG` as the primary dynamic-memory benchmark.
- Add `HM3D-OVON` or `GOAT-Bench` when the claim shifts to navigation/search metrics.
- Consider `OpenLex3D` only if open-vocabulary representation quality itself becomes a central claim.

## Immediate Next Actions

- Run E005-M72 `heldout_b02` / `heldout_b03` real proposal detector batches using the same M68/M71 metric contract.
- Do not continuously monitor the log; inspect only targeted tail/head/error snippets when verification is needed.
- Keep the main paper claim centered on memory trust, staleness handling, bounded re-observation, and proxy-search improvement over `ConceptGraphs` / static memory.
- Keep human task context as a secondary ablation unless E006 is explicitly launched and passes context-sensitive utility gates.
- Expand real RGB-D/open-vocabulary robustness before real navigation `SR` / `SPL`.
- Keep `OpenMask3D` as the later 3D instance proposal baseline candidate.
- Keep `Open3DSG`, `ConceptGraphs`, and `HOV-SG` for map/scene-graph/navigation baseline expansion.

## Claim Boundary

사실:

- Current real RGB-D/open-vocabulary claim readiness is false.
- Current real navigation `SR` / `SPL` claim readiness is false.
- Current human task context main-claim readiness is false.
- Current H001-vs-`ConceptGraphs` proxy-search claim readiness is true with proxy boundary.
- Current internal evidence supports controlled/proxy behavior, not final top-tier paper evidence.
- E003-M39 selects `docker_runner_pre_consolidation_support_evidence_v0` and rejects final-artifact post-processing as insufficient.
- E003-M39 fixes insertion point `select_cap_aware_label_balanced_candidates.after_cleaned_before_grouped`.
- E003-M40 status is `temporal_spatial_support_runner_smoke_ready`.
- E003-M40 attaches support evidence to 95 / 95 selected rows with validator errors/warnings 0 / 0.
- E003-M40 keeps real RGB-D/open-vocabulary claim readiness false because it is a short smoke, not heldout policy evidence.
- E003-M41 status is `support_aware_selection_policy_gate_ready`.
- E003-M41 selects `confidence_sqrt_depth_support_temporal_v0`.
- E003-M41 keeps hard support filter false, support cap changes false, and long rerun readiness false.
- E003-M42 status is `support_aware_selection_runner_smoke_ready`.
- E003-M42 validator errors/warnings are 0 / 0.
- E003-M42 matched/false-positive/precision delta vs E003-M40 is 0 / 0 / 0.0.
- E003-M43 status is `support_aware_scaled_rerun_route_gate_ready`.
- E003-M43 selected route is `pre_cap_candidate_pool_export_then_offline_replay_v0`.
- E003-M43 M42 vs M40 common selected rows are 94 / 95, selected symmetric difference is 2 rows, pre-cap rank changed common rows are 68, and selection-score changed common rows are 89.
- E003-M43 marks existing candidate-pool replay available false and immediate support-aware long rerun recommended false.
- E003-M44 status is `pre_cap_candidate_pool_replay_smoke_ready`.
- E003-M44 exported 629 pre-cap candidate rows with support policy on 629 / 629 rows.
- E003-M44 reproduced runner selection for `confidence_sqrt_depth_support_temporal_v0`: runner selected rows 95, offline replay rows 95, ordered/set reproduction true / true.
- E003-M45 tmux session `e003_m45_scaled_pool` completed with log `logs/20260508_155219_e003_m45_scaled_candidate_pool_export_replay_tmux.log`.
- E003-M45 verification status is `scaled_candidate_pool_replay_ready`, but frozen contract verdict is `fail_redesign`.
- E003-M45 support-aware score result is 196 matched targets, 3211 false positives, and proposal precision 0.057529, worse than the M33 confidence baseline 204 / 3210 / 0.059754.
- E003-M46 status is `score_redesign_or_external_gate_ready`.
- E003-M46 swept 12 bounded score policies and found hard pass 0, weak positive 0.
- E003-M46 selected `external_proposal_baseline_gate_first` because simple support-aware score redesign did not improve the M45 failure.
- E003-M47 status is `external_baseline_feasibility_gate_ready`.
- E003-M47 selected `Grounded-SAM` because it is the smallest controlled change from the current `GroundingDINO` RGB-D backprojection backend.
- `OpenMask3D` remains the stronger 3D instance segmentation baseline candidate, but its scene-format/checkpoint/MinkowskiEngine burden makes it a second route.
- `ConceptGraphs` and `HOV-SG` remain mapping/navigation baselines, not first proposal-failure diagnosis routes.
- E003-M48 status is `grounded_sam_contract_ready`.
- E003-M48 preserves the existing `real_proposal_prediction_jsonl_v0` required fields and adds 9 optional mask diagnostic fields.
- E003-M48 did not execute Docker/model inference and does not make a new result claim.
- E003-M49 `Grounded-SAM` Docker/model smoke emitted 24 mask-depth proposal rows and passed schema/matching smoke.
- E003-M50 same-subset comparison found bbox-depth 31 proposals / 2 matched targets / 29 false positives / precision 0.064516, while mask-depth had 24 / 1 / 23 / 0.041667.
- E003-M51 selected artifact-local mask failure analysis before any scaled `Grounded-SAM` rerun or `OpenMask3D` feasibility.
- E003-M52 found common candidate rows 24, bbox-only candidate rows 7, mask-only candidate rows 0, and skipped mask projection rows 16.
- E003-M52 lost-by-mask target count is 1, label `plant`; common same-target match-distance delta mask minus bbox is -0.018907m.
- E003-M52 diagnoses the aggregate centroid worsening as match-set composition after an easy bbox-depth target dropout, not common-target centroid degradation.
- E003-M52 keeps scaled `Grounded-SAM` recommended false and selects `E003-M53 bbox-depth continuation and failure-boundary repair gate`.
- E003-M53 status is `bbox_continuation_repair_gate_ready`.
- E003-M53 selected route is `search_critical_bbox_failure_boundary_first`.
- E003-M53 route scores: search-critical bbox boundary 46, deployable bbox suppression repair 30, `OpenMask3D` feasibility 27, `ConceptGraphs` mapping 19, `Open3DSG` mapping 16, `HOV-SG` navigation/mapping 10.
- E003-M53 keeps `OpenMask3D` as a later external 3D instance proposal baseline and keeps `Open3DSG` / `ConceptGraphs` / `HOV-SG` for later map/scene-graph/navigation baseline expansion.
- E003-M54 status is `search_critical_bbox_failure_boundary_ready`.
- E003-M54 exact current query-instance joins are 0 because M33/M45 detector-ready scans do not overlap with E001 current `rescan_id` rows.
- E003-M54 reference-memory-only joins are 120, label overlap count is 21, and existing E001/E002 search failures with label-level detector risk are 7.
- E003-M54 strongest bridge labels are `pillow` and `chair`; these remain label-level risks, not direct real RGB-D search-failure proof.
- E003-M55 status is `dynamic_pair_bridge_gate_ready`.
- E003-M55 selected route is `stage_search_failure_current_rescans_first`.
- E003-M55 search-failure current rescans are 4; semantic triplet ready is 4 / 4 and sequence-ready is 0 / 4.
- E003-M55 priority scans are `5555106a-36f1-29c0-8913-df1ba3c3cfd5`, `4731976c-f9f7-2a1a-95cc-31c4d1751d0b`, `ddc73795-765b-241a-9c5d-b97744afe077`, and `10b17957-3938-2467-88a5-9e9254930dad`.
- E003-M56 status is `current_rescan_sequence_staging_plan_ready`.
- E003-M56 target scan count is 4, prelaunch sequence-ready count is 0 / 4, and download-required count is 4 / 4.
- E003-M56 records a resumable `wget -c` staging script and `verify_m56_sequence_payloads.py --require-ready` verification command.
- E003-M57 status is `sequence_staging_job_launched`.
- E003-M57 background job status was `running` at launch in tmux session `e003_m56_sequence_stage`; the session later ended.
- E003-M57 log path is `logs/20260510_170443_e003_m56_sequence_staging.log`.
- E003-M57 verification status is `sequence_payloads_ready`, ready rows 4 / 4.
- E003-M57 does not create a paper result claim; it only prepares the direct current-rescan detector bridge denominator.
- E003-M58 status is `direct_current_rescan_bridge_design_ready`.
- E003-M58 links 7 search-failure query rows, 5 unique bridge targets, 4 current rescans, 29 same-label object targets, and 93 sampled frames for the next detector run.
- E003-M58 detector run executed is false and real RGB-D/open-vocabulary search claim readiness remains false.
- E003-M59 status is `pre_cap_candidate_pool_export_smoke_ready`.
- E003-M59 background job has completed.
- E003-M59 tmux session is `e003_m59_direct_bridge`.
- E003-M59 log path is `logs/20260511_114356_e003_m59_direct_current_rescan_detector_run.log`.
- E003-M59 target scans are 4 and bridge query rows are 7.
- E003-M59 scanned 93 frames, produced 2015 raw predictions, wrote 96 selected proposals, and exported 1970 pre-cap candidate rows.
- E003-M59 validator status is `proposal_schema_smoke_valid`, with errors/warnings 0 / 0.
- E003-M59 matching status is `detector_matching_smoke_ready`, with 21 matched proposals, 75 false-positive proposals, precision 0.218750, and scan target recall 0.724138.
- E003-M59 does not create a query-level paper result claim by itself; E003-M60 provides the first query-level bridge metric.
- E003-M60 status is `direct_query_bridge_budget_rank_gap`.
- E003-M60 query target detected rows are 3 / 7 and unique target detected rows are 3 / 5.
- E003-M60 mean detected target rank is 5.0 and mean false positives before detected target is 4.0.
- E003-M60 `detector_task_budget_v0` success is 0 / 7.
- E003-M60 `detector_top5_v0` success is 2 / 7.
- E003-M60 unbounded detector success is 3 / 7.
- E003-M60 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M61 status is `direct_bridge_rank_failure_gate_ready`.
- E003-M61 failure class counts are detector recall miss 4, task-budget mismatch 2, and false-positive rank failure 1.
- E003-M61 unique target failure class counts are detector recall miss 2, task-budget mismatch 2, and false-positive rank failure 1.
- E003-M61 selected next route is `proposal_rerank_then_openmask3d_feasibility`.
- E003-M61 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M62 status is `offline_rerank_budget_repair_ready`.
- E003-M62 best deployable unbounded repair succeeds on 3 / 7 rows with mean expected search cost 16.428571.
- E003-M62 bounded top-5/adaptive repair succeeds on 2 / 7 rows.
- E003-M62 selected next route is `integrate_deployable_rerank_budget_then_openmask3d`.
- E003-M62 keeps real RGB-D/open-vocabulary search claim readiness false.
- E003-M63 status is `bounded_repair_integration_gate_ready`.
- E003-M63 selected bounded policy is `old_memory_distance_guard+adaptive_uncertainty_top5`.
- E003-M63 selected bounded repair succeeds on 2 / 7 rows with mean expected search cost 5.428571.
- E003-M63 best task-budget rerank succeeds on 1 / 7 rows.
- E003-M63 unbounded upper-bound succeeds on 3 / 7 rows.
- E003-M63 bounded budget repair ablation ready is true, but bounded rerank unique gain ready is false.
- E003-M63 selected next route is `openmask3d_feasibility_gate_next`.
- E003-M64 status is `openmask3d_feasibility_decision_ready`.
- E003-M64 bounded failure rows are 5 / 7: target-undetected 4 and rank/budget gap 1.
- E003-M64 bridge scans with `OpenMask3D` minimal input readiness are 4 / 4.
- E003-M64 selected next route is `openmask3d_scene_format_model_smoke_plan_next`.
- E003-M64 launched no Docker/model run and keeps real RGB-D/open-vocabulary search claim readiness false.

논문 주장:

- Do not claim deployable real RGB-D/open-vocabulary robustness until external baselines and heldout-transfer evidence are added.
- Do not claim real navigation `SR` / `SPL` until a simulator, navmesh, or trajectory execution source is integrated.
